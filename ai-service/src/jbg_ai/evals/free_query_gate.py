"""The numeric gate of the FREE-QUERY mode, measured apart from the anchored one. C31.

**They are not the same gate, and publishing one rate for both would hide the thing worth
knowing.** C30b measured **0 violations in 120 generations** against a payload carrying one
SKU, one size label and one variant label. A free query hands the model up to five groups, so
every candidate widens the whitelist and the exposure grows with the result set. That is the
declared risk of this change, and a rate that averaged the two modes would be arithmetic over
two different populations.

What is measured here is the **first** generation of each query, before any repair: the rate at
which an argument arrives broken is what says whether the gate works, and the rate after a
repair confounds the gate with the repair.

Real index, real corpus, real provider. The classifier decides the route, exactly as the
serving path does, so a query routed to `knowledge` is measured with no candidates at all —
which is the point: the payload is what the route produced and not what a fixture chose.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from uuid import uuid4

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.assist import AssistRequest
from jbg_ai.assist.constants import (
    DEFAULT_ASSIST_MODEL,
    DEFAULT_ROUTER_MODEL,
    PRICE_PLACEHOLDER,
    PITCH_VIOLATION_CAUSES,
    STOCK_PLACEHOLDER,
    PROMPT_VERSION,
)
from jbg_ai.assist.llm import LiteLlmAssistClient
from jbg_ai.assist.prompt import (
    FREE_QUERY_TASKS,
    _SECTION_BY_TASK,
    load_prompt_file,
    prompt_sections,
)
from jbg_ai.assist.router_llm import LiteLlmRouterClient
from jbg_ai.evals.routing import RESULTS_DIR, git_sha, load_routing_cases, provenance
from jbg_ai.knowledge.search import SqlAlchemyKnowledgeIndex
from jbg_ai.retrieval.orchestrator import build_retrieval_embed_client
from jbg_ai.retrieval.search import SqlAlchemyProductSearch

#: Wider than the serving cut, for the reason the routing sweep gives: a sweep has nobody
#: waiting at a counter, and a serving budget would turn provider jitter into measured failures.
SWEEP_TIMEOUT_SECONDS = 30.0


def _count(outcome, marker: str) -> int:
    """Occurrences of a placeholder in the first generated attempt, or 0 when none ran."""
    attempt = getattr(outcome, "initial_generated", None) if outcome else None
    if attempt is None:
        attempt = getattr(outcome, "generated", None) if outcome else None
    return attempt.pitch.count(marker) if attempt else 0


async def _run(args) -> dict:
    # Windows installs the ProactorEventLoop by default and `psycopg` refuses it. One scenario,
    # one loop: the engine is process-wide and its connections belong to the loop that opened
    # them, so two `asyncio.run` calls in one process fail with `InterfaceError`.
    from jbg_ai.assist.orchestrator import assist_sale
    from jbg_ai.config.settings import Settings

    settings = Settings()  # type: ignore[call-arg]
    cases = [
        case
        for case in load_routing_cases()
        # Only the classes a free query can actually generate over. A refused or clarified
        # query calls no provider at all, so it has nothing to say about a numeric gate.
        if case.expected in {"catalog", "knowledge", "both"}
    ]
    if args.limit:
        cases = cases[: args.limit]

    key = (
        os.environ.get("JPV_ASSIST_LLM_API_KEY")
        or os.environ.get("JPV_RAG_LLM_API_KEY")
    )
    router_key = os.environ.get("JPV_ROUTER_LLM_API_KEY") or key
    embed = build_retrieval_embed_client(settings)
    search = SqlAlchemyProductSearch(settings)
    knowledge = SqlAlchemyKnowledgeIndex(settings)
    principal = ServicePrincipal(
        user_id="c31-sweep", role="Operator", trace_id=uuid4().hex[:12], pos_id=args.pos_id
    )

    # **The outcome is captured at the seam and the orchestrator is not modified for it.**
    # The rate that says whether the gate works is the rate at which a generation arrives
    # broken — the FIRST attempt, before any repair — and the serving path deliberately keeps
    # that object to itself. Wrapping `generate_pitch` here reads it without putting an
    # evaluation hook into the path a counter runs.
    from jbg_ai.assist import orchestrator as orchestrator_module
    from jbg_ai.assist.pitch import generate_pitch as real_generate_pitch
    from jbg_ai.assist.routing import classify_query as real_classify_query

    captured: list = []
    routed: list = []

    async def capturing_classify(query, **kwargs):
        outcome = await real_classify_query(query, **kwargs)
        routed.append(outcome)
        return outcome

    orchestrator_module.classify_query = capturing_classify

    # **The prompt version is a parameter of the run, so a before/after varies one thing.**
    # `--prompt-version` is what makes the C40 measurement a comparison rather than two
    # anecdotes: the same code, the same index, the same corpus and the same queries, with the
    # prompt as the only difference. `generate_pitch` already takes the text and the version
    # side by side, precisely so a caller cannot stamp a response with a prompt that never
    # reached the model.
    prompt_text = load_prompt_file(args.prompt_version)
    prompt_sections_present = prompt_sections(prompt_text)

    async def capturing(payload_obj, task, **kwargs):
        # A version older than C40 has no «sin cobertura» section for the free query, so a task
        # it cannot serve falls back to the one its route would have used. Without this the
        # "before" pass would die on the first uncovered knowledge query instead of measuring
        # what that version actually did, which is to run the normal task with no fragments.
        resolved = task
        section = _SECTION_BY_TASK.get(task)
        if section is not None and section not in prompt_sections_present:
            resolved = FREE_QUERY_TASKS.get(routed[-1].route if routed else "", task)
            fallbacks.append((getattr(task, "value", None), getattr(resolved, "value", None)))

        kwargs["prompt_text"] = prompt_text
        kwargs["prompt_version"] = args.prompt_version
        outcome = await real_generate_pitch(payload_obj, resolved, **kwargs)
        captured.append((payload_obj, resolved, outcome))
        return outcome

    orchestrator_module.generate_pitch = capturing

    fallbacks: list = []
    causes: Counter = Counter()
    initial_causes: Counter = Counter()
    rows: list[dict] = []
    for index, case in enumerate(cases, start=1):
        pitch_client = LiteLlmAssistClient(
            api_key=key, model=args.model, timeout=SWEEP_TIMEOUT_SECONDS
        )
        router_client = LiteLlmRouterClient(
            api_key=router_key, model=args.router_model, timeout=SWEEP_TIMEOUT_SECONDS
        )
        before = len(captured)
        try:
            response = await assist_sale(
                AssistRequest(query=case.text, top_k=5),
                principal,
                settings=settings,
                embed=embed,
                search=search,
                knowledge=knowledge,
                pitch_client=pitch_client,
                router_client=router_client,
            )
        except Exception as exc:  # noqa: BLE001 — a sweep records a failure, never dies of one
            rows.append({"id": case.id, "error": type(exc).__name__})
            continue
        # **Only this query's capture, never the previous one's.** A request that generated
        # nothing appends nothing, so reading `captured[-1]` unconditionally attributed the
        # previous query's task, whitelist and causes to it — which read as 54 `catalog`
        # generations where there had been 24. The length is compared before and after.
        payload_obj, task, outcome = (
            captured[-1] if len(captured) > before else (None, None, None)
        )
        if outcome is not None:
            causes.update(item.cause for item in outcome.violations)
            initial_causes.update(item.cause for item in outcome.initial_violations)
        rows.append(
            {
                "id": case.id,
                "expected": case.expected,
                "router_degraded_cause": (
                    routed[-1].degraded_cause if routed else None
                ),
                "route": routed[-1].route if routed else None,
                "task": getattr(task, "value", None),
                "whitelist_size": len(payload_obj.numerals()) if payload_obj else None,
                "initial_causes": sorted(
                    {item.cause for item in outcome.initial_violations}
                )
                if outcome
                else [],
                "initial_figures": sorted(
                    {item.figure for item in outcome.initial_violations if item.figure}
                )
                if outcome
                else [],
                "surviving_causes": sorted({item.cause for item in outcome.violations})
                if outcome
                else [],
                "provider_error": outcome.provider_error if outcome else None,
                "provider_calls": outcome.usage.calls if outcome else 0,
                "intent": response.intent,
                "groups": len(response.groups),
                "members": sum(len(group.members) for group in response.groups),
                "citations": len(response.citations),
                "abstained": response.abstained,
                "clarified": response.clarification_question is not None,
                # **The C40 measurement.** Counted on the FIRST attempt, which is what the
                # prompt produced before any repair, and counted rather than stored: the
                # argument is content the serving path may not persist, and a count is not.
                "price_placeholders": _count(outcome, PRICE_PLACEHOLDER),
                "stock_placeholders": _count(outcome, STOCK_PLACEHOLDER),
                "generated": bool(response.pitch),
                "prompt_version": response.prompt_version,
                "total_tokens": response.usage.total_tokens,
            }
        )
        if index % 10 == 0:
            print(f"  {index}/{len(cases)}", file=sys.stderr)
        await asyncio.sleep(args.delay)

    generated = [row for row in rows if row.get("prompt_version")]
    withheld = [row for row in generated if not row["generated"]]
    return {
        **provenance(model=args.model),
        "git_sha": git_sha(),
        "router_model": args.router_model,
        "pitch_prompt_version": args.prompt_version,
        "serving_prompt_version": PROMPT_VERSION,
        # **The figure C40 exists to publish.** Counted over the FIRST attempt of every
        # generation, which is what the prompt produced before any repair.
        "price_placeholders_total": sum(row.get("price_placeholders", 0) for row in rows),
        "stock_placeholders_total": sum(row.get("stock_placeholders", 0) for row in rows),
        "generations_with_a_price_placeholder": sum(
            1 for row in rows if row.get("price_placeholders", 0)
        ),
        "generations_with_a_stock_placeholder": sum(
            1 for row in rows if row.get("stock_placeholders", 0)
        ),
        "task_fallbacks": fallbacks,
        "n_queries": len(rows),
        "n_generated": len(generated),
        "n_withheld_by_the_gate": len(withheld),
        "free_query_rejection_rate": (
            round(len(withheld) / len(generated), 4) if generated else None
        ),
        "note": (
            "The rejection rate of the FREE-QUERY mode. Published apart from the anchored "
            "one — C30b's 0 violations in 120 generations — because they are not the same "
            "gate: every candidate a free query returns widens the numeric whitelist, and a "
            "single averaged figure would be arithmetic over two different populations."
        ),
        "causes_after_repair": dict(causes),
        "causes_on_first_attempt": dict(initial_causes),
        "mean_whitelist_size": (
            round(
                sum(row["whitelist_size"] or 0 for row in rows if row.get("whitelist_size"))
                / max(1, sum(1 for row in rows if row.get("whitelist_size"))),
                1,
            )
        ),
        "router_degradations": dict(
            Counter(
                row["router_degraded_cause"]
                for row in rows
                if row.get("router_degraded_cause")
            )
        ),
        "by_task": dict(
            Counter(row["task"] for row in rows if row.get("task"))
        ),
        "withheld_by_task": dict(
            Counter(row["task"] for row in rows if row.get("task") and not row["generated"])
        ),
        "mean_members": (
            round(
                sum(row.get("members", 0) for row in rows) / max(1, len(rows)), 1
            )
        ),
        "violation_vocabulary": list(PITCH_VIOLATION_CAUSES),
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_ASSIST_MODEL)
    parser.add_argument("--router-model", default=DEFAULT_ROUTER_MODEL)
    parser.add_argument(
        "--prompt-version",
        default=PROMPT_VERSION,
        help="Which assist prompt to generate with. The before/after of C40 varies only this",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--pos-id", default="b0000000-0000-4000-8000-000000000002")
    parser.add_argument("--name", default="c31-free-query-gate")
    args = parser.parse_args(argv)

    # Windows installs the ProactorEventLoop by default and `psycopg` refuses it. **Guarded
    # rather than unconditional**: the attribute does not exist on Linux, so running this
    # harness inside the container — which is how C40 measures against the provider without a
    # certificate bundle of its own — died on this line before reaching the first query.
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    import litellm  # noqa: F401 — warm the import outside every per-call timeout

    payload = asyncio.run(_run(args))
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{args.name}-{payload['run_id']}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
