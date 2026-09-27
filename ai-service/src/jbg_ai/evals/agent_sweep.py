"""The two-armed provider pass of the agent loop. C32b.

**A dated measurement, not a reproducible row.** It calls a language model, so it lives beside
`assist_sweep.py` and `cag_run.py` and not inside the runner that re-executes on every
evaluation — keeping the two apart is what stops an irreproducible figure from entering a table
of reproducible ones.

What it measures, and the reading that matters is always the **distribution**:

    carga          p50/p95 de tokens, de contexto y de reloj · curva de crecimiento por vuelta
                   coste por brazo de modelo · sobrecoste contra el pipeline determinista
    calibración    herramienta muerta · causa de argumento recurrente · NOMBRE INVENTADO
                   llamadas casi idénticas · tasa de pivote POR ETIQUETA de disponibilidad

An agent has a long tail — the request that loops to its limit is the one that ruins a mean —
so no aggregate is published here without its percentiles.

**It drives the real layer.** `run_agent` is the function the route calls; a harness that
re-implemented the loop would measure the re-implementation, which is the mistake this
repository already names in `evals/configs.py`. What it changes is the model of the arm and
nothing else: the budgets, the prompts and the registry are the serving ones.

**This is the declared exception to the no-persistence rule.** The serving path writes no
transcript, no argument and no tool argument anywhere, log included. The harness writes the
**rich** trace — arguments and observations — bound to a run identifier, a commit and the
prompt versions, because the granularity question cannot be answered without it: «two nearly
identical calls to one tool» is a statement about arguments. The transcripts are synthetic and
no operator wrote them, which is what makes that exception cheap here.

    uv run python -m jbg_ai.evals.agent_sweep --dry-run          # procedencia y tamaño
    uv run python -m jbg_ai.evals.agent_sweep --limit 3 --arms openai/gpt-4o   # humo
    uv run python -m jbg_ai.evals.agent_sweep                    # la pasada entera
    uv run python -m jbg_ai.evals.agent_sweep --rescore evals/results/<artefacto>.json

**`--rescore` recomputes every aggregate from an artefact already written**, with no provider
and no database: cost priced stage by stage, pivot rates per arm, the calibration scored against
the expectations it ran with and against the current ones. It exists because the independent
verification of C32b found three figures of the published report that no committed code could
reproduce — the corrected cost, the pooled pivot table and the OK/MISS count — and a number
nobody can recompute is a number nobody can check.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import statistics
import sys
import time
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.health_report import projection_age_seconds
from jbg_ai.assist.agent import AgentBudgets, run_agent
from jbg_ai.assist.agent_llm import LiteLlmAgentClient
from jbg_ai.assist.constants import (
    AGENT_PITCH_PROMPT_VERSION,
    AGENT_PROMPT_VERSION,
    AVAILABILITY_LABEL_BY_BUCKET,
    AVAILABILITY_LABELS,
    AVAILABILITY_NO_SCOPE,
    DEFAULT_AGENT_MODEL,
    DEFAULT_ASSIST_MODEL,
    DEFAULT_ROUTER_MODEL,
    MAX_AGENT_PROVIDER_CALLS,
    MAX_PITCH_PROVIDER_CALLS,
    PRICE_PLACEHOLDER,
    PROMPT_VERSION,
    ROUTER_PROMPT_VERSION,
    STOCK_PLACEHOLDER,
    TOOL_NAMES,
)
from jbg_ai.assist.llm import LiteLlmAssistClient, TokenUsage
from jbg_ai.assist.prompt import load_prompt_file
from jbg_ai.assist.router_llm import LiteLlmRouterClient
from jbg_ai.assist.tools import build_registry
from jbg_ai.assist.transcript import Turn
from jbg_ai.data.paths import AI_SERVICE_ROOT
from jbg_ai.db.engine import dispose_engine
from jbg_ai.evals.errors import EvaluationUnavailable
from jbg_ai.evals.execute import harness_settings
from jbg_ai.evals.provenance import UNKNOWN_SHA
from jbg_ai.knowledge.search import SqlAlchemyKnowledgeIndex
from jbg_ai.retrieval.orchestrator import build_retrieval_embed_client
from jbg_ai.retrieval.search import SqlAlchemyProductSearch

AGENT_SETS = AI_SERVICE_ROOT / "evals" / "agent"
LOAD_SET = AGENT_SETS / "load-set.yaml"
CALIBRATION = AGENT_SETS / "calibration.yaml"
RESULTS_DIR = AI_SERVICE_ROOT / "evals" / "results"

#: The two arms, and the second is the whole reason the model is a variable of its own. The
#: cost arithmetic decomposes the agent's overhead against the deterministic pipeline into a
#: multiplier of TOKENS, which is structural, and a multiplier of MODEL, which is an
#: environment variable. Measuring both turns that second one into a measurement instead of a
#: preference — and it is cheap: the second arm is a fraction of the first.
DEFAULT_ARMS: tuple[str, ...] = (DEFAULT_AGENT_MODEL, "openai/gpt-4o-mini")

#: MAO-AIR, the point of sale with the most exposure to stockouts in the C10 world: 34,4 % of
#: its assortment at zero stock, 143 of 416. **Declared and not inferred**, and it is the same
#: identifier `evals/configs/v3-senales.yaml` declares for the same reason — a test asserts the
#: two agree rather than letting them drift.
MAO_AIR = UUID("43da2f6a-cb64-4067-b5c2-cd67f5a8f6b3")

#: The marker a calibration scenario carries where the harness must put a real reference. A
#: scenario that said «esta pieza» would give the model nothing to anchor the availability tool
#: on, and its pivot rate would be computed over whatever the search happened to return.
PIECE_MARKER = "{pieza}"

#: The key under which `resolve_pieces` returns a SKU whose family has several members.
#: It is **not** an availability label and is kept out of that vocabulary on purpose.
FAMILY_WITH_VARIANTS = "family:con_variantes"

#: Per million tokens, in USD. Published prices of 2026-09, recorded **in the artefact** so a
#: figure can be recomputed later against what it was actually priced at rather than against
#: whatever the price is when somebody reads the report.
PRICES: dict[str, tuple[float, float]] = {
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
}

#: The three stages of one request, in the order they run. **Each is priced by its own model**:
#: the classifier and the argument do not run the arm under measurement, and a request of the
#: `gpt-4o` arm spends ~3.300 prompt tokens on the classifier alone.
STAGES: tuple[str, ...] = ("router", "loop", "pitch")

#: The prompts whose text a run depends on. Their **digests** go in the provenance, because a
#: version label does not identify a text: the probes of C32b recorded `agent/v1` and
#: `assist/v4` over texts that were edited between one probe and the next.
MEASURED_PROMPTS: tuple[str, ...] = (
    AGENT_PROMPT_VERSION,
    AGENT_PITCH_PROMPT_VERSION,
    ROUTER_PROMPT_VERSION,
)

#: What the pass counts as a mention of availability in a served argument. **A measurement
#: vocabulary and not a gate**: the four labels, their spelling as prose, and the stems a
#: sentence about stock is made of. Nothing stops an argument from carrying them — `verify()`
#: passes «disponible» and even «sin_existencias» — so the one honest thing to do is to count
#: them. It over-counts on purpose: «disponible en talla M» is counted, because telling a
#: catalogue fact from a stock claim is a judgement this counter does not make.
AVAILABILITY_PROSE_TERMS: tuple[str, ...] = (
    "sin existencias",
    "ultimas unidades",
    "sin ambito",
    "disponibles",
    "en stock",
    "sin stock",
)
_AVAILABILITY_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(
        [re.escape(term) for term in (*AVAILABILITY_LABELS, *AVAILABILITY_PROSE_TERMS)]
        + [r"agotad\w*"]
    )
    + r")\b"
)


def _folded(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def availability_terms_in(text: str) -> int:
    """How many availability terms a served argument carries. A count and never the text.

    The harness is the declared exception to the no-persistence rule for tool arguments, not
    for prose, so what reaches the artefact is a number.
    """
    return len(_AVAILABILITY_PATTERN.findall(_folded(text or "")))


def placeholders_in(outcome, marker: str) -> int:
    """Occurrences of a placeholder in the **first** generated attempt, or 0 when none ran.

    **The first attempt and not the served one**, which is the same rule `free_query_gate`
    applies and for the same reason: what is being measured is what the prompt produced, and
    the single repair runs after it. A count of the served argument would report zero for
    every placeholder the repair removed and so would measure the repair instead of the prompt.

    A count and never the text. The agent's task runs over an **unanchored** payload — the
    argument speaks of several pieces, so there is nothing to resolve a placeholder against —
    and since C40 a placeholder there is a hard violation, so this is the figure that says
    whether the argument is being withheld for obeying its own prompt.
    """
    attempt = getattr(outcome, "initial_generated", None) if outcome else None
    if attempt is None:
        attempt = getattr(outcome, "generated", None) if outcome else None
    return attempt.pitch.count(marker) if attempt else 0


async def projection_freshness(
    search: SqlAlchemyProductSearch, settings, *, now: datetime | None = None
) -> dict[str, Any]:
    """The projection's age and the staleness verdict that applies to it, right now.

    **Read per row and not once per run, and that is the point of it.** A pass of this harness
    takes longer than the ceiling it is measured against — C32b's took 2 h 44 min against a
    ceiling of 1 h — and the two paths disagree in silence: `resolve_pieces` goes through
    `scope_buckets`, declared *read by the evaluation only* and carrying **no freshness check**,
    while the serving path consults the checkpoint and declines to apply the point-of-sale
    prefilter once it is stale. A run with no recorded age therefore cannot be told apart from
    a run that was fresh throughout, which is exactly what happened to C32b's retrieval figures
    and what could not be cleaned up afterwards.

    **The age comes from the synchronisation checkpoint** — `projection_synced_at()`, one row
    per feed — and never from `ai.pos_projection.refreshed_at`, which records when an
    assignment last changed rather than when the drain last ran. C41 found that exact confusion
    in C40's manipulation, so the port that reads the checkpoint is the only source here.
    """
    ceiling = settings.jpv_pos_projection_max_age_seconds
    synced_at = await search.projection_synced_at()
    age = projection_age_seconds(synced_at, now=now)
    return {
        "synced_at": synced_at.isoformat() if synced_at else None,
        "age_seconds": age,
        "ceiling_seconds": ceiling,
        # Never drained is stale: the prefilter does not apply then either.
        "stale": age is None or age > ceiling,
    }


def expectation_verdict(
    invoked: Iterable[str], scenario: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Score one calibration scenario by the semantics its file declares. `None` when it has none.

    `expects` is a **conjunction** — every tool, at some point; `expects_any` a **disjunction**
    — at least one; `forbids` — none of them. An empty `expects` is satisfied vacuously, which
    is how a scenario that must end in a refusal says so together with its `forbids`.

    Until the independent verification of C32b nothing in the repository read these fields: the
    OK/MISS table of the report was scored by hand. `declared_discrepancy` is carried through so
    a miss the calibration set documents as known is counted apart from one nobody expected.
    """
    fields = ("expects", "expects_any", "forbids")
    if all(scenario.get(name) is None for name in fields):
        return None
    tools = set(invoked)
    expects = list(scenario.get("expects") or [])
    any_of = list(scenario.get("expects_any") or [])
    forbids = list(scenario.get("forbids") or [])
    missing = [name for name in expects if name not in tools]
    any_met = not any_of or bool(tools & set(any_of))
    forbidden = [name for name in forbids if name in tools]
    return {
        "met": not missing and any_met and not forbidden,
        "missing": missing,
        "missing_any_of": [] if any_met else any_of,
        "forbidden_invoked": forbidden,
        "declared_discrepancy": bool(scenario.get("declared_discrepancy")),
    }


def turns_digest(turns: Sequence[Mapping[str, Any]]) -> str:
    """The scenario's turns as written — marker unresolved — so a later rescore can tell whether
    the scenario it scores against is the one that ran."""
    return hashlib.sha256(
        json.dumps(list(turns), ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def prompt_digests() -> dict[str, str]:
    return {
        version: hashlib.sha256(load_prompt_file(version).encode("utf-8")).hexdigest()
        for version in MEASURED_PROMPTS
    }


def _git_sha() -> str:
    import subprocess

    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, cwd=AI_SERVICE_ROOT,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=AI_SERVICE_ROOT,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 — a run outside a checkout still records something
        return UNKNOWN_SHA
    # A run taken on a dirty tree was NOT produced by the commit it names. C25 was bitten by
    # exactly this and `provenance.py` records the rule; it is reused rather than restated.
    return f"{sha}+dirty" if dirty else sha


#: The three chains, exactly as `api/routers/assist.py` resolves them. **Three and not one,
#: and the first pass proved why it matters.** That run resolved a single credential and handed
#: it to all three clients, which did two things at once: it measured a configuration the route
#: never serves, and it pointed every call of every stage at one key — so a rate limit was
#: reached on request six and the requests that followed degraded. How many is not known: the
#: run left no artefact, and the two counts written down from its console (46 and 64) disagree.
#:
#: The classifier's key is deliberately absent from the agent's chain and vice versa: a request
#: of this route resolves two clients, and letting one fall back to the other would make the
#: cost of the two stages impossible to tell apart.
CREDENTIAL_CHAINS: dict[str, tuple[tuple[str, str], ...]] = {
    "agent": (
        ("JPV_AGENT_LLM_API_KEY", "agent"),
        ("JPV_ASSIST_LLM_API_KEY", "assist_fallback"),
        ("JPV_RAG_LLM_API_KEY", "rag_fallback"),
    ),
    "router": (
        ("JPV_ROUTER_LLM_API_KEY", "router"),
        ("JPV_ASSIST_LLM_API_KEY", "assist_fallback"),
        ("JPV_RAG_LLM_API_KEY", "rag_fallback"),
    ),
    "pitch": (
        ("JPV_ASSIST_LLM_API_KEY", "assist"),
        ("JPV_RAG_LLM_API_KEY", "rag_fallback"),
    ),
}


def _credential(stage: str = "agent") -> tuple[str | None, str]:
    """The chain of ONE stage, so the pass measures what would actually serve."""
    for variable, link in CREDENTIAL_CHAINS[stage]:
        value = os.environ.get(variable)
        if value:
            return value, link
    return None, "absent"


def _credentials() -> dict[str, tuple[str | None, str]]:
    return {stage: _credential(stage) for stage in CREDENTIAL_CHAINS}


class TokenPacer:
    """Keeps the run under a **tokens-per-minute** ceiling, measured rather than assumed.

    **The first pass failed because the limit is not what it looked like.** It broke on request
    six, twice, with three different keys and a delay between requests — so it was neither a
    per-key limit nor a per-request one. The arithmetic says what it was: 55.649 tokens in 33
    seconds, a rate of ~100.000 tokens per minute against an organisation ceiling well below
    that. Splitting the credentials across stages did nothing because the quota is the
    organisation's, not the key's.

    A fixed delay is the wrong instrument for a token ceiling: requests here range from ~1.800
    to ~16.000 tokens, so a pause long enough for the biggest wastes most of the run and one
    tuned to the average still bursts through the limit. This sleeps only as long as the
    *tokens already spent in the last minute* require, which self-tunes to whatever the real
    ceiling turns out to be.

    It paces **between** requests and never inside one: a pause in the middle would land in the
    wall-clock budget this pass exists to measure.
    """

    def __init__(self, tokens_per_minute: int) -> None:
        self.limit = tokens_per_minute
        self._spent: list[tuple[float, int]] = []

    def record(self, tokens: int) -> None:
        self._spent.append((time.monotonic(), tokens))

    def _in_window(self, now: float) -> int:
        self._spent = [item for item in self._spent if now - item[0] < 60.0]
        return sum(tokens for _when, tokens in self._spent)

    async def wait_for(self, estimated: int) -> float:
        """Sleep until `estimated` more tokens fit under the ceiling. Returns seconds slept."""
        if self.limit <= 0:
            return 0.0
        slept = 0.0
        while True:
            now = time.monotonic()
            used = self._in_window(now)
            if used + estimated <= self.limit or not self._spent:
                return slept
            # Wait until the oldest entry leaves the window; it is the smallest sleep that can
            # change the answer, so this never over-waits.
            oldest = self._spent[0][0]
            pause = max(60.0 - (now - oldest), 0.1)
            await asyncio.sleep(pause)
            slept += pause


def load_sets() -> tuple[dict, dict]:
    return (
        yaml.safe_load(LOAD_SET.read_text(encoding="utf-8")),
        yaml.safe_load(CALIBRATION.read_text(encoding="utf-8")),
    )


# --- resolving the fixtures against the projection ------------------------------------------


async def resolve_pieces(search: SqlAlchemyProductSearch) -> dict[str, str]:
    """One real SKU per availability label, read from MAO-AIR's projection **at run time**.

    A SKU written into the set would calibrate against a label that the next sync makes
    something else, and the scenario would stop measuring what it claims with nothing failing.
    The chosen references are recorded in the artefact's provenance, so the run is auditable
    without the set having to lie about being stable.

    `sin_ambito` is the one that cannot come from a bucket: it means **no row was read**, so it
    is resolved as a piece the index holds and this point of sale does not carry — which is the
    distinction C32a made a fourth value precisely so it would not be confused with zero.
    """
    buckets = await search.scope_buckets(MAO_AIR)
    chosen: dict[str, str] = {}

    for product_id, bucket in sorted(buckets.items()):
        label = AVAILABILITY_LABEL_BY_BUCKET.get(bucket)
        if label is None or label in chosen:
            continue
        document = await search.source_document(UUID(product_id))
        if document is not None and document.is_active:
            chosen[label] = document.sku

    # A piece the point of sale does not carry: the honest source of «no scope».
    if AVAILABILITY_NO_SCOPE not in chosen:
        unscoped = await _first_unscoped(search, set(buckets))
        if unscoped is not None:
            chosen[AVAILABILITY_NO_SCOPE] = unscoped

    # Not an availability label: the reference a chaining scenario needs.
    variants = await _piece_with_variants(search)
    if variants is not None:
        chosen[FAMILY_WITH_VARIANTS] = variants
    return chosen


async def _piece_with_variants(search: SqlAlchemyProductSearch) -> str | None:
    """A SKU whose family holds more than one active member.

    Needed because a scenario about «are there other sizes of that one?» has to name a piece
    that actually has other sizes — the first version of C05 asked the model to chain onto a
    reference the conversation never contained, which made it unsatisfiable rather than hard.
    """
    from sqlalchemy import text

    from jbg_ai.db.engine import session_scope

    async with session_scope(search._settings) as session:  # noqa: SLF001 — harness only
        rows = await session.execute(
            text(
                "SELECT sku FROM ("
                "  SELECT sku, count(*) OVER (PARTITION BY family_id) AS members"
                "  FROM ai.product_document"
                "  WHERE is_active AND family_id IS NOT NULL) q"
                " WHERE members >= 2 ORDER BY sku LIMIT 1"
            )
        )
        row = rows.first()
    return str(row[0]) if row else None


async def _first_unscoped(
    search: SqlAlchemyProductSearch, carried: set[str]
) -> str | None:
    """A SKU the index holds and this point of sale does not carry."""
    from sqlalchemy import text

    from jbg_ai.db.engine import session_scope

    async with session_scope(search._settings) as session:  # noqa: SLF001 — harness only
        rows = await session.execute(
            text(
                "SELECT sku FROM ai.product_document "
                "WHERE is_active AND product_id::text <> ALL(:carried) "
                "ORDER BY sku LIMIT 1"
            ),
            {"carried": list(carried) or [""]},
        )
        row = rows.first()
    return str(row[0]) if row else None


def scenario_turns(item: dict, pieces: dict[str, str]) -> list[Turn] | None:
    """The turns of one scenario with its marker resolved, or `None` when it cannot be run.

    Returning `None` rather than raising: a projection that happens to carry no piece at one
    label costs that scenario and not the pass, and the artefact records which were skipped.
    """
    fixture = item.get("fixture") or {}
    key = (
        fixture["availability"]
        if "availability" in fixture
        else FAMILY_WITH_VARIANTS
        if fixture.get("family") == "con_variantes"
        else None
    )
    replacement = pieces.get(key) if key else None
    if fixture and replacement is None:
        return None
    turns: list[Turn] = []
    for turn in item["turns"]:
        text = turn["text"]
        if replacement is not None:
            text = text.replace(PIECE_MARKER, replacement)
        turns.append(Turn(role=turn["role"], text=text))
    return turns


# --- one request ------------------------------------------------------------------------------


def _row(
    *,
    item: dict,
    set_id: str,
    arm: str,
    run,
    elapsed_ms: float,
    projection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Everything one request produced, flattened for analysis. Distribution first."""
    per_iteration = [
        {
            "iteration": trace.iteration,
            "prompt_tokens": trace.prompt_tokens,
            "completion_tokens": trace.completion_tokens,
            # The two halves of the context pair: what the pre-flight budget counted, and what
            # the provider actually charged for the same turn.
            "context_chars": trace.context_chars,
            "elapsed_ms": round(trace.elapsed_ms, 1),
            "discarded_chars": trace.discarded_chars,
            "provider_error": trace.provider_error,
            "cut_by_clock": trace.cut_by_clock,
            "tools": [
                {
                    "tool": call.tool,
                    "ok": call.ok,
                    "cause": call.cause,
                    # The rich trace: the declared exception, and what the granularity
                    # question needs. «Two nearly identical calls» is about arguments.
                    "arguments": dict(call.arguments) if call.arguments else None,
                }
                for call in trace.tools
            ],
        }
        for trace in run.trace
    ]
    invoked = [call["tool"] for turn in per_iteration for call in turn["tools"]]
    return {
        "id": item["id"],
        "set": set_id,
        "arm": arm,
        "operator_turns": item.get(
            "operator_turns",
            sum(1 for turn in item["turns"] if turn["role"] == "operario"),
        ),
        "measures": item.get("measures"),
        "expects": item.get("expects"),
        "expects_any": item.get("expects_any"),
        "forbids": item.get("forbids"),
        "declared_discrepancy": item.get("declared_discrepancy"),
        "fixture": item.get("fixture"),
        "turns_sha256": turns_digest(item["turns"]),
        "expectation": expectation_verdict(invoked, item),
        # **The three stages, each with its own model.** Their sum is `prompt_tokens` and
        # friends below; pricing that sum by one model is the error the first cost figure of
        # C32b made, so the parts are what the cost is computed from.
        "stages": {
            "router": _usage_record(run.router_usage),
            "loop": _usage_record(run.loop_usage, model=arm),
            "pitch": _usage_record(run.pitch_usage),
        },
        # A count and never the text: see `availability_terms_in`.
        "pitch_availability_terms": availability_terms_in(run.pitch),
        # **The placeholder rate of the agent's task, counted on the first attempt.** The
        # withholding rate alone cannot tell a placeholder from a dangling citation, and those
        # call for opposite fixes: one is the prompt, the other the corpus.
        "price_placeholders": placeholders_in(run.pitch_outcome, PRICE_PLACEHOLDER),
        "stock_placeholders": placeholders_in(run.pitch_outcome, STOCK_PLACEHOLDER),
        # **The freshness this row actually ran with**, so a row served without the prefilter is
        # identifiable afterwards instead of being averaged in with the rest. `None` for rows
        # written before the record existed — not zero, which would be a claim.
        "projection_age_seconds": (
            projection.get("age_seconds") if projection else None
        ),
        "projection_stale": projection.get("stale") if projection else None,
        "stop_reason": run.stop_reason,
        "partial": run.partial,
        "iterations": run.iterations,
        "tool_calls_used": run.tool_calls_used,
        "tools_invoked": invoked,
        # A name the model reached for that is not one of the six. **The most informative
        # datum this run can produce**, because the name states which tool is missing.
        "invented_tools": sorted({name for name in invoked if name not in TOOL_NAMES}),
        "abstained": run.abstained,
        "clarified": run.clarification_question is not None,
        "warnings": list(run.warnings),
        "groups": len(run.groups),
        "citations": len(run.citations),
        "pitch_chars": len(run.pitch),
        # **Why there is no argument, when there is none.** Without this a row reading
        # `pitch_chars: 0` is unanalysable and the only way to find out costs another run —
        # which is the whole point of recording it before the expensive one. The causes are
        # the generation layer's own closed vocabulary, so they partition.
        "pitch_withheld": run.pitch_outcome is not None and run.pitch_outcome.withheld,
        "pitch_ran": run.pitch_outcome is not None,
        "pitch_violations": (
            list(run.pitch_outcome.causes()) if run.pitch_outcome else []
        ),
        "pitch_initial_violations": (
            [item.cause for item in run.pitch_outcome.initial_violations]
            if run.pitch_outcome
            else []
        ),
        "pitch_withdrawn_citations": (
            list(run.pitch_outcome.withdrawn_citation_ids) if run.pitch_outcome else []
        ),
        "pitch_provider_error": (
            run.pitch_outcome.provider_error if run.pitch_outcome else None
        ),
        "pitch_calls": run.pitch_outcome.usage.calls if run.pitch_outcome else 0,
        "prompt_tokens": run.usage.prompt_tokens,
        "completion_tokens": run.usage.completion_tokens,
        "total_tokens": run.usage.total_tokens,
        "provider_calls": run.usage.calls,
        "embedding_calls": run.embedding_calls,
        "elapsed_ms": round(elapsed_ms, 1),
        "per_iteration": per_iteration,
    }


def _usage_record(usage: TokenUsage, *, model: str | None = None) -> dict[str, Any]:
    return {
        "model": usage.model or model,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "calls": usage.calls,
    }


# --- cost, stage by stage ----------------------------------------------------------------------
#
# **Every stage is priced by its own model.** The first form of this harness priced every token
# of a request at the arm's price, which mixes three models; the report then corrected it by
# hand with a classifier figure attributed to C31 that C31 never published, while the artefact
# itself shows the classifier spending ~3.300 prompt tokens on `gpt-4o` per request. Both errors
# were found by the independent verification of C32b, and both start where a sum is priced by
# one name.


def legacy_router_usage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """The classifier's usage, **derived from the artefact itself**, for rows that predate the
    per-stage record.

    Where the argument did not run, whatever a row spent beyond its loop turns is the
    classifier's alone; its prompt barely moves with the query, so the median of those rows is
    the classifier of every row. Declared in the rescore's output with its range, never assumed.
    """
    spent: list[tuple[int, int]] = []
    for row in rows:
        if "stages" in row or row.get("pitch_ran"):
            continue
        loop_prompt = sum(turn["prompt_tokens"] for turn in row["per_iteration"])
        loop_completion = sum(turn["completion_tokens"] for turn in row["per_iteration"])
        prompt = row["prompt_tokens"] - loop_prompt
        if prompt > 0:
            spent.append((prompt, row["completion_tokens"] - loop_completion))
    if not spent:
        return None
    prompts = [item[0] for item in spent]
    return {
        "prompt_tokens": int(statistics.median(prompts)),
        "completion_tokens": int(statistics.median(item[1] for item in spent)),
        "n": len(spent),
        "prompt_tokens_range": [min(prompts), max(prompts)],
        "source": (
            "median over this artefact's requests where the argument did not run: what they "
            "spent beyond their loop turns is the classifier's alone"
        ),
    }


def stage_usages(
    row: Mapping[str, Any],
    *,
    legacy: Mapping[str, Any] | None = None,
    stage_models: Mapping[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """The three stages of one row, each with the model it ran. Recorded, or derived for rows
    written before the record existed — and then the loop is exact (its turns carry their
    tokens), the classifier comes from `legacy_router_usage` and the argument is the rest."""
    models = {
        "router": (stage_models or {}).get("router") or DEFAULT_ROUTER_MODEL,
        "pitch": (stage_models or {}).get("pitch") or DEFAULT_ASSIST_MODEL,
    }
    if "stages" in row:
        return {
            name: {
                **row["stages"][name],
                "model": row["stages"][name].get("model")
                or (row["arm"] if name == "loop" else models[name]),
            }
            for name in STAGES
        }

    loop_prompt = sum(turn["prompt_tokens"] for turn in row["per_iteration"])
    loop_completion = sum(turn["completion_tokens"] for turn in row["per_iteration"])
    rest_prompt = row["prompt_tokens"] - loop_prompt
    rest_completion = row["completion_tokens"] - loop_completion
    if row.get("pitch_ran"):
        if legacy is None:
            raise ValueError(
                "a row that ran the argument and predates the per-stage record cannot be split "
                "without the classifier's usage derived from its own artefact"
            )
        router = (legacy["prompt_tokens"], legacy["completion_tokens"])
        pitch = (max(rest_prompt - router[0], 0), max(rest_completion - router[1], 0))
    else:
        router = (rest_prompt, rest_completion)
        pitch = (0, 0)
    return {
        "router": {"model": models["router"], "prompt_tokens": router[0], "completion_tokens": router[1]},
        "loop": {"model": row["arm"], "prompt_tokens": loop_prompt, "completion_tokens": loop_completion},
        "pitch": {"model": models["pitch"], "prompt_tokens": pitch[0], "completion_tokens": pitch[1]},
    }


def _price(stage: Mapping[str, Any], unpriced: set[str] | None = None) -> float:
    prices = PRICES.get(stage["model"] or "")
    if prices is None:
        if unpriced is not None and (stage["prompt_tokens"] or stage["completion_tokens"]):
            unpriced.add(str(stage["model"]))
        return 0.0
    return (
        stage["prompt_tokens"] * prices[0] + stage["completion_tokens"] * prices[1]
    ) / 1_000_000


def stage_costs(
    row: Mapping[str, Any],
    *,
    legacy: Mapping[str, Any] | None = None,
    stage_models: Mapping[str, str] | None = None,
    unpriced: set[str] | None = None,
) -> dict[str, float]:
    stages = stage_usages(row, legacy=legacy, stage_models=stage_models)
    return {name: _price(stages[name], unpriced) for name in STAGES}


def _cost(
    row: Mapping[str, Any],
    *,
    legacy: Mapping[str, Any] | None = None,
    stage_models: Mapping[str, str] | None = None,
    unpriced: set[str] | None = None,
) -> float:
    return sum(
        stage_costs(
            row, legacy=legacy, stage_models=stage_models, unpriced=unpriced
        ).values()
    )


# --- the summary, always partitioned ---------------------------------------------------------


def _percentiles(values: list[float]) -> dict[str, float]:
    """p50 and p95, and never a mean on its own.

    An agent's cost distribution has a long tail: the request that loops to its limit is the
    one a mean hides. The mean is reported too, but beside the percentiles and never instead.
    """
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "p50": round(statistics.median(ordered), 1),
        "p95": round(ordered[max(int(0.95 * len(ordered)) - 1, 0)], 1),
        "max": round(ordered[-1], 1),
        "mean": round(statistics.fmean(ordered), 1),
    }


def summarise(
    rows: list[dict],
    *,
    legacy: Mapping[str, Any] | None = None,
    stage_models: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for arm in sorted({row["arm"] for row in rows}):
        for set_id in sorted({row["set"] for row in rows if row["arm"] == arm}):
            subset = [
                row for row in rows if row["arm"] == arm and row["set"] == set_id
            ]
            out[f"{arm}::{set_id}"] = _summarise_subset(
                subset, legacy=legacy, stage_models=stage_models
            )
    return out


def _summarise_subset(
    subset: list[dict],
    *,
    legacy: Mapping[str, Any] | None = None,
    stage_models: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    stops: dict[str, int] = {}
    for row in subset:
        stops[row["stop_reason"]] = stops.get(row["stop_reason"], 0) + 1

    tool_counts: dict[str, int] = {name: 0 for name in TOOL_NAMES}
    causes: dict[str, int] = {}
    for row in subset:
        for turn in row["per_iteration"]:
            for call in turn["tools"]:
                tool_counts[call["tool"]] = tool_counts.get(call["tool"], 0) + 1
                if call["cause"]:
                    causes[call["cause"]] = causes.get(call["cause"], 0) + 1

    unpriced: set[str] = set()
    by_stage = [
        stage_costs(row, legacy=legacy, stage_models=stage_models, unpriced=unpriced)
        for row in subset
    ]
    costs = [sum(item.values()) for item in by_stage]
    stages = [
        stage_usages(row, legacy=legacy, stage_models=stage_models) for row in subset
    ]
    measured_terms = [
        row["pitch_availability_terms"]
        for row in subset
        if row.get("pitch_ran") and "pitch_availability_terms" in row
    ]
    return {
        "requests": len(subset),
        "partial": sum(1 for row in subset if row["partial"]),
        "stop_reasons": stops,
        "tokens_prompt": _percentiles([row["prompt_tokens"] for row in subset]),
        "tokens_total": _percentiles([row["total_tokens"] for row in subset]),
        # **What `AGENT_TOKEN_BUDGET` compares**: the classifier plus the loop, which is what
        # has accumulated when the check runs. `tokens_prompt` adds the argument, which runs
        # after the loop — the budget was first calibrated on that other quantity.
        "tokens_governed": _percentiles(
            [item["router"]["prompt_tokens"] + item["loop"]["prompt_tokens"] for item in stages]
        ),
        "context_chars": _percentiles(
            [
                max((turn["context_chars"] for turn in row["per_iteration"]), default=0)
                for row in subset
            ]
        ),
        "wall_ms": _percentiles([row["elapsed_ms"] for row in subset]),
        "iterations": _percentiles([float(row["iterations"]) for row in subset]),
        "provider_calls": _percentiles([float(row["provider_calls"]) for row in subset]),
        "provider_calls_over_ceiling": sum(
            1 for row in subset if row["provider_calls"] > MAX_AGENT_PROVIDER_CALLS
        ),
        # The curve, which is what says whether the accumulated context has to be compacted.
        "growth_by_turn": _growth(subset),
        "tool_usage": tool_counts,
        "tools_never_chosen": sorted(
            name for name, count in tool_counts.items() if count == 0
        ),
        "invented_tool_names": sorted(
            {name for row in subset for name in row["invented_tools"]}
        ),
        "failure_causes": causes,
        # The generation layer's verdict, partitioned. An argument withheld is a request that
        # cost everything and served no prose, so the rate and its causes belong beside the
        # cost rather than in a footnote.
        "pitch_ran": sum(1 for row in subset if row["pitch_ran"]),
        "pitch_withheld": sum(1 for row in subset if row["pitch_withheld"]),
        "pitch_violation_causes": _tally(
            cause for row in subset for cause in row["pitch_initial_violations"]
        ),
        # **The placeholder figure this change exists to publish**, aggregated over the first
        # attempt of every generation. `None` for a subset whose rows predate the count — not
        # zero, which would assert that no placeholder was written.
        "pitch_placeholders": (
            {
                "price_total": sum(row.get("price_placeholders", 0) for row in subset),
                "stock_total": sum(row.get("stock_placeholders", 0) for row in subset),
                "generations_with_a_price_placeholder": sum(
                    1 for row in subset if row.get("price_placeholders", 0)
                ),
                "generations_with_a_stock_placeholder": sum(
                    1 for row in subset if row.get("stock_placeholders", 0)
                ),
            }
            if any("price_placeholders" in row for row in subset)
            else None
        ),
        # **The audit of the run, not a quality figure.** A subset whose rows disagree on
        # staleness was served two different ways, so its retrieval aggregates describe neither.
        "projection_freshness": (
            {
                "rows_recorded": sum(
                    1 for row in subset if row.get("projection_stale") is not None
                ),
                "rows_stale": sum(
                    1 for row in subset if row.get("projection_stale") is True
                ),
                "age_seconds": _percentiles(
                    [
                        float(row["projection_age_seconds"])
                        for row in subset
                        if row.get("projection_age_seconds") is not None
                    ]
                ),
            }
            if any(row.get("projection_stale") is not None for row in subset)
            else None
        ),
        # Availability terms in served arguments: nothing prevents them, so they are counted.
        # `None` for rows written before the count existed — not zero, which would be a claim.
        "pitch_availability_terms": (
            {
                "arguments_measured": len(measured_terms),
                "arguments_with_terms": sum(1 for count in measured_terms if count),
                "terms": sum(measured_terms),
            }
            if measured_terms or not any(row.get("pitch_ran") for row in subset)
            else None
        ),
        "expectations": _expectation_counts(subset),
        # **Each stage priced by its own model**, and the three published apart.
        "cost_usd_total": round(sum(costs), 4),
        "cost_usd_per_request": round(sum(costs) / max(len(costs), 1), 6),
        "cost_usd_per_request_by_stage": {
            name: round(sum(item[name] for item in by_stage) / max(len(by_stage), 1), 6)
            for name in STAGES
        },
        "unpriced_models": sorted(unpriced),
    }


def _expectation_counts(
    rows: Sequence[Mapping[str, Any]],
    current: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """OK / miss / declared miss over the rows that carry expectations.

    With `current`, each row is scored against the scenario **as the calibration file says it
    today** — but only when that scenario is still the one that ran: the turns' digest when the
    row carries one, and for rows written before it the fixture, which is the weaker check and
    is said so. A scenario whose transcript changed after the run is not comparable, and is
    listed rather than scored.
    """
    counts: dict[str, Any] = {
        "ok": 0,
        "miss": 0,
        "miss_declared": 0,
        "missed": [],
        "declared": [],
        "not_comparable": [],
    }
    scored = 0
    for row in rows:
        scenario: Mapping[str, Any] | None = row
        if current is not None:
            scenario = current.get(row["id"])
            comparable = scenario is not None and (
                row["turns_sha256"] == turns_digest(scenario["turns"])
                if "turns_sha256" in row
                else (row.get("fixture") or None) == (scenario.get("fixture") or None)
            )
            if not comparable:
                counts["not_comparable"].append(row["id"])
                continue
        verdict = expectation_verdict(row["tools_invoked"], scenario)
        if verdict is None:
            continue
        scored += 1
        if verdict["met"]:
            counts["ok"] += 1
        elif verdict["declared_discrepancy"]:
            counts["miss_declared"] += 1
            counts["declared"].append(row["id"])
        else:
            counts["miss"] += 1
            counts["missed"].append(row["id"])
    return counts if scored or counts["not_comparable"] else None


def _tally(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return out


def _growth(subset: list[dict]) -> dict[str, dict[str, float]]:
    """Accumulated prompt tokens and context characters **per turn index**.

    The figure that decides whether compaction is needed, and the one D-14 refused to act on
    before measuring: first the curve, then the decision.
    """
    by_turn: dict[int, list[tuple[int, int]]] = {}
    for row in subset:
        for turn in row["per_iteration"]:
            # A turn lost to the provider or cut by the clock reports zero tokens, which is not
            # a point of the curve: it would pull the median down on exactly the long requests.
            if turn.get("provider_error") or turn.get("cut_by_clock"):
                continue
            by_turn.setdefault(turn["iteration"], []).append(
                (turn["prompt_tokens"], turn["context_chars"])
            )
    return {
        str(index): {
            "requests": len(items),
            "prompt_tokens_p50": round(statistics.median([a for a, _ in items]), 1),
            "context_chars_p50": round(statistics.median([b for _, b in items]), 1),
        }
        for index, items in sorted(by_turn.items())
    }


def pivot_rates(rows: list[dict]) -> dict[str, Any]:
    """The substitute-pivot rate **per arm and per availability label**, over- and under- apart.

    The expensive failure is pivoting away from a piece the shop can sell, and an aggregate
    rate cannot tell it from the cheap one.

    **Per arm**, because the pass exists to compare two models and a rate over both describes
    neither: the first form of this function pooled them, and the one under-pivot it reported
    was the cheap arm's. **Only availability fixtures count**: since C05 declares a piece with
    variants rather than a label, the first form raised `KeyError` on the committed calibration
    set — at the moment of writing the artefact, which would have lost a whole paid pass. Both
    found by the independent verification of C32b. Whether a scenario must or must not pivot
    is read from its `expects` and its `forbids`, per row, never from the last row of a label.
    """
    out: dict[str, Any] = {}
    for row in rows:
        label = (row.get("fixture") or {}).get("availability")
        if label is None:
            continue
        bucket = out.setdefault(row["arm"], {}).setdefault(
            label,
            {
                "scenarios": 0,
                "pivoted": 0,
                "pivot_required": 0,
                "pivot_forbidden": 0,
                "infra_pivots": 0,
                "over_pivots": 0,
                "ids": [],
            },
        )
        pivoted = "buscar_sustitutos" in row["tools_invoked"]
        required = "buscar_sustitutos" in (row.get("expects") or [])
        forbidden = "buscar_sustitutos" in (row.get("forbids") or [])
        bucket["scenarios"] += 1
        bucket["pivoted"] += int(pivoted)
        bucket["pivot_required"] += int(required)
        bucket["pivot_forbidden"] += int(forbidden)
        bucket["infra_pivots"] += int(required and not pivoted)
        bucket["over_pivots"] += int(forbidden and pivoted)
        bucket["ids"].append(row["id"])
    for labels in out.values():
        for bucket in labels.values():
            bucket["pivot_rate"] = round(bucket["pivoted"] / max(bucket["scenarios"], 1), 4)
            failures = [
                name
                for name, count in (
                    ("infra-pivote", bucket["infra_pivots"]),
                    ("sobre-pivote", bucket["over_pivots"]),
                )
                if count
            ]
            bucket["failure"] = " y ".join(failures) or "ninguno"
    return out


# --- the artefact: written as it is produced, and re-read without a provider -------------------


def append_record(path: Path, record: Mapping[str, Any]) -> None:
    """One line per record, flushed as it is produced.

    **A pass that dies leaves what it paid for.** The first form wrote the artefact only at the
    end, so the aborted pass of C32b left nothing behind and its figures survive only as console
    output nobody kept; and a fault while summarising — the `KeyError` above — would have lost
    the 204 rows of a finished one. The final JSON is still written; this is what exists until
    then, and what a rescore can read if it never is.
    """
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def load_artefact(path: Path) -> dict[str, Any]:
    """A finished artefact, or the partial record a run left behind."""
    if path.name.endswith(".jsonl"):
        provenance: dict[str, Any] = {}
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "provenance" in record:
                provenance = record["provenance"]
            elif "row" in record:
                rows.append(record["row"])
        return {"provenance": provenance, "rows": rows, "partial": True}
    return json.loads(path.read_text(encoding="utf-8"))


def rescore(
    path: Path, *, calibration: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Every aggregate of an artefact, recomputed by the code of today. **No provider, no DB.**

    What it reads is what the run recorded. What it adds is declared in its own output: for
    artefacts that predate the per-stage record, the classifier's usage derived from the
    artefact itself, and the stage models taken from the defaults when the provenance did not
    record them. The calibration file is read as it is today, and a scenario that changed
    after the run is listed as not comparable instead of being scored.
    """
    document = load_artefact(path)
    rows: list[dict[str, Any]] = document["rows"]
    provenance: Mapping[str, Any] = document.get("provenance") or {}
    recorded = provenance.get("stage_models") or {}
    stage_models = {
        "router": recorded.get("router") or DEFAULT_ROUTER_MODEL,
        "pitch": recorded.get("pitch") or DEFAULT_ASSIST_MODEL,
    }
    legacy = (
        legacy_router_usage(rows) if any("stages" not in row for row in rows) else None
    )
    scenarios = (calibration or load_sets()[1])["scenarios"]
    current = {item["id"]: item for item in scenarios}
    calibration_rows = [row for row in rows if row["set"] == "calibration"]
    arms = sorted({row["arm"] for row in rows})
    # The digest of the bytes with line endings normalised, so a Windows checkout and a Linux
    # one name the same artefact with the same value.
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return {
        "rescored_from": {
            "artefact": path.name,
            "sha256_lf": hashlib.sha256(raw).hexdigest(),
            "run_id": provenance.get("run_id"),
            "partial": bool(document.get("partial")),
        },
        "rescored_with": {
            "git_sha": _git_sha(),
            "taken_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "stage_models": {**stage_models, "loop": "the arm of each row"},
        "stage_models_source": (
            "recorded in the provenance"
            if recorded
            else "defaults: the artefact predates the record of the stage models"
        ),
        "legacy_router_usage": legacy,
        "prices_usd_per_million": PRICES,
        "summary": summarise(rows, legacy=legacy, stage_models=stage_models),
        "pivot_rates": pivot_rates(rows),
        "expectations": {
            "as_run": {
                arm: _expectation_counts([row for row in calibration_rows if row["arm"] == arm])
                for arm in arms
            },
            "current": {
                arm: _expectation_counts(
                    [row for row in calibration_rows if row["arm"] == arm], current
                )
                for arm in arms
            },
        },
    }


def rescore_path(path: Path) -> Path:
    """Where the rescore of an artefact is written: beside it, and named after it."""
    stem = path.name.removesuffix(".partial.jsonl").removesuffix(".json")
    return path.with_name(f"{stem}.rescore.json")


# --- the run ------------------------------------------------------------------------------------


async def run(args: argparse.Namespace) -> int:
    load_set, calibration = load_sets()
    # The dry run must work with nothing configured: its whole job is to print what the
    # pass WOULD do before anybody pays for it, and demanding a database to do that would
    # make the cheap check the expensive one.
    settings = harness_settings(requires_database=not args.dry_run)
    credentials = _credentials()

    chosen_sets: list[tuple[str, dict, str]] = []
    if args.sets in ("both", "load"):
        chosen_sets.append(("load", load_set, "transcripts"))
    if args.sets in ("both", "calibration"):
        chosen_sets.append(("calibration", calibration, "scenarios"))

    arms = list(args.arms or DEFAULT_ARMS)
    run_id = uuid4().hex[:12]
    # The serving budgets, with the argument's reserve computed as the route computes it: from
    # the timeout the generation client is actually built with.
    budgets = AgentBudgets(
        pitch_reserve_seconds=MAX_PITCH_PROVIDER_CALLS
        * settings.jpv_assist_pitch_timeout_seconds
    )
    provenance: dict[str, Any] = {
        "run_id": run_id,
        "git_sha": _git_sha(),
        "taken_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "agent_prompt_version": AGENT_PROMPT_VERSION,
        "pitch_prompt_version": AGENT_PITCH_PROMPT_VERSION,
        "router_prompt_version": ROUTER_PROMPT_VERSION,
        "deterministic_route_prompt_version": PROMPT_VERSION,
        "arms": arms,
        "credential_links": {stage: link for stage, (_key, link) in credentials.items()},
        "delay_seconds": args.delay,
        "tokens_per_minute_ceiling": args.tpm,
        "sets": {
            name: {"id": document["id"], "size": len(document[key_name])}
            for name, document, key_name in chosen_sets
        },
        "point_of_sale": str(MAO_AIR),
        "budgets": budgets.__dict__,
        "provider_call_ceiling": MAX_AGENT_PROVIDER_CALLS,
        "prices_usd_per_million": PRICES,
        # **What the two stages that do not run the arm ran**, so their cost can be priced
        # from the artefact rather than assumed from whatever the defaults are when it is read.
        "stage_models": {
            "router": settings.jpv_router_llm_model,
            "loop": "the arm of each row",
            "pitch": settings.jpv_assist_llm_model,
        },
        # **The texts, not only their labels.** Two texts under one label are two instruments.
        "prompt_sha256": prompt_digests(),
        "limit": args.limit or None,
    }

    planned = sum(
        min(len(document[key_name]), args.limit or len(document[key_name]))
        for _name, document, key_name in chosen_sets
    ) * len(arms)
    provenance["planned_requests"] = planned

    print(json.dumps(provenance, indent=2, ensure_ascii=False, default=str))
    if args.dry_run:
        print(
            f"\ndry run: {len(arms)} arms x "
            f"{planned // max(len(arms), 1)} transcripts = {planned} requests, "
            "none executed, nothing written"
        )
        return 0

    if not settings.database_url:
        raise EvaluationUnavailable("DATABASE_URL is required for the agent sweep")
    unresolved = [stage for stage, (value, _link) in credentials.items() if value is None]
    if unresolved:
        raise EvaluationUnavailable(
            "no credential resolves for: "
            + ", ".join(unresolved)
            + ". Each stage has its own chain: "
            + "; ".join(
                stage + " -> " + " then ".join(name for name, _ in chain)
                for stage, chain in CREDENTIAL_CHAINS.items()
            )
        )

    embed = build_retrieval_embed_client(settings)
    search = SqlAlchemyProductSearch(settings)
    knowledge = SqlAlchemyKnowledgeIndex(settings)
    rows: list[dict] = []
    skipped: list[str] = []
    pacer = TokenPacer(args.tpm)
    # The running mean, so the first requests are paced on the estimate and the later ones
    # on what this run actually costs.
    estimate = 12_000
    paced_seconds = 0.0
    partial = RESULTS_DIR / f"c32b-agent-sweep-{run_id}.partial.jsonl"

    try:
        pieces = await resolve_pieces(search)
        provenance["resolved_pieces"] = pieces
        provenance["index_compatible_documents"] = await search.count_compatible(
            model_version_key=embed.model_version_key, model_id=embed.model_id
        )
        provenance["assortment_size"] = await search.count_scope(MAO_AIR)
        # **The age at the start, and the rows carry their own.** This one answers «was the
        # projection fresh when the pass began»; the per-row figure answers «was it still fresh
        # when THIS row ran», which is the question a pass longer than the ceiling makes real.
        provenance["projection_freshness_at_start"] = await projection_freshness(
            search, settings
        )
        print(json.dumps(
            {"resolved_pieces": pieces,
             "index": provenance["index_compatible_documents"],
             "assortment": provenance["assortment_size"]},
            indent=2, ensure_ascii=False,
        ))
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        append_record(partial, {"provenance": provenance})

        for arm in arms:
            for set_name, document, key_name in chosen_sets:
                items = document[key_name]
                if args.limit:
                    items = items[: args.limit]
                for item in items:
                    turns = scenario_turns(item, pieces)
                    if turns is None:
                        skipped.append(f"{set_name}:{item['id']}")
                        print(f"  skipped {item['id']}: no piece for its fixture")
                        continue
                    principal = ServicePrincipal(
                        user_id="agent-sweep",
                        role="Operator",
                        trace_id=f"sweep-{run_id}-{item['id']}",
                        pos_id=str(MAO_AIR),
                    )
                    paced_seconds += await pacer.wait_for(estimate)
                    started = time.perf_counter()
                    result = await run_agent(
                        turns,
                        principal,
                        registry=build_registry(
                            principal=principal,
                            settings=settings,
                            embed=embed,
                            search=search,
                            knowledge=knowledge,
                        ),
                        agent_client=LiteLlmAgentClient(
                            api_key=credentials["agent"][0],
                            model=arm,
                            base_url=settings.jpv_rag_llm_base_url,
                            timeout=settings.jpv_agent_timeout_seconds,
                        ),
                        router_client=LiteLlmRouterClient(
                            api_key=credentials["router"][0],
                            model=settings.jpv_router_llm_model,
                            base_url=settings.jpv_rag_llm_base_url,
                            timeout=settings.jpv_router_timeout_seconds,
                        ),
                        pitch_client=LiteLlmAssistClient(
                            api_key=credentials["pitch"][0],
                            model=settings.jpv_assist_llm_model,
                            base_url=settings.jpv_rag_llm_base_url,
                            timeout=settings.jpv_assist_pitch_timeout_seconds,
                        ),
                        budgets=budgets,
                    )
                    elapsed = (time.perf_counter() - started) * 1000.0
                    # Read **after** the request and never before: the age that matters is the
                    # one the retrieval guard would have seen, and the request is what took the
                    # time. One checkpoint read per row, outside the clock being measured.
                    freshness = await projection_freshness(search, settings)
                    row = _row(
                        item=item,
                        set_id=set_name,
                        arm=arm,
                        run=result,
                        elapsed_ms=elapsed,
                        projection=freshness,
                    )
                    rows.append(row)
                    append_record(partial, {"row": row})
                    pacer.record(row["total_tokens"])
                    estimate = max(
                        1_000,
                        int(sum(item["total_tokens"] for item in rows) / len(rows)),
                    )
                    if args.delay:
                        # Between requests and never inside one: pausing mid-request
                        # would land in the wall-clock budget being measured.
                        await asyncio.sleep(args.delay)
                    print(
                        f"  {arm:<20} {set_name:<12} {item['id']:>5} "
                        f"{row['stop_reason']:<24} it={row['iterations']} "
                        f"tools={row['tool_calls_used']} "
                        f"tok={row['total_tokens']:>6} {row['elapsed_ms']:>7.0f} ms"
                        # Visible while the pass runs, because the moment to react to a stale
                        # projection is before the remaining rows are paid for.
                        + (" RANCIA" if freshness["stale"] else ""),
                        flush=True,
                    )
    finally:
        await dispose_engine()

    provenance["skipped"] = skipped
    provenance["paced_seconds"] = round(paced_seconds, 1)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    artefact = RESULTS_DIR / f"c32b-agent-sweep-{run_id}.json"
    # The aggregates are computed **before** anything is written and the partial record is
    # removed only **after** the artefact exists: a fault in either leaves the rows on disk.
    summary = summarise(rows, stage_models=provenance["stage_models"])
    pivots = pivot_rates(rows)
    artefact.write_text(
        json.dumps(
            {
                "provenance": provenance,
                "summary": summary,
                "pivot_rates": pivots,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    partial.unlink(missing_ok=True)
    print(f"\nwrote {artefact}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def run_rescore(path: Path) -> int:
    """`--rescore`: recompute an artefact's aggregates, print them and write them beside it."""
    result = rescore(path)
    target = rescore_path(path)
    target.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"\nwrote {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m jbg_ai.evals.agent_sweep",
        description="C32b two-armed provider pass of the sale assistant's agent loop",
    )
    parser.add_argument(
        "--arms",
        nargs="*",
        default=None,
        help=f"Models under measurement. Default: {' '.join(DEFAULT_ARMS)}",
    )
    parser.add_argument(
        "--sets",
        choices=("both", "load", "calibration"),
        default="both",
        help="Which instrument to run. Default: both",
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="First N of each set, for a smoke test"
    )
    parser.add_argument(
        "--tpm",
        type=int,
        default=25_000,
        help=(
            "Tokens-per-minute ceiling to stay under. The organisation's quota, not the "
            "key's: the first pass measured ~100k/min against a lower ceiling and every "
            "request after the sixth came back empty. 0 disables the pacing"
        ),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help=(
            "Seconds to wait between requests. A request makes up to eight provider "
            "calls, so a key on a low rate tier is exhausted in a handful of them: the "
            "first pass of C32b hit its limit on request six and every one after it came "
            "back empty. Pacing turns a wasted run into a slow one"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Provenance and size only: nothing executed and nothing written",
    )
    parser.add_argument(
        "--rescore",
        type=Path,
        default=None,
        metavar="ARTEFACT",
        help=(
            "Recompute every aggregate of an artefact already written — or of the partial "
            "record an interrupted run left — with no provider and no database, and write "
            "them beside it as <artefact>.rescore.json"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rescore is not None:
        # Nothing to load and nothing to connect to: the artefact is the whole input.
        return run_rescore(args.rescore)

    # The shared local env file, exactly as `evals/cli.py` loads it, and **existing process
    # environment wins** so an explicit export still overrides. It is here so a credential
    # never has to be typed on a command line, where it would land in shell history.
    from jbg_ai.data.envload import load_local_env

    load_local_env()

    # `psycopg` refuses the ProactorEventLoop, which is what Python installs by default on
    # Windows. Every loose script that opens the async engine needs this; in the tests
    # `support/async_db.run_db` already does it.
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        return asyncio.run(run(args))
    except EvaluationUnavailable as exc:
        print(f"unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
