"""The harness of the agent's provider pass, checked without a provider. C32b.

**The first tests this harness ever had**, written by the independent verification of C32b.
Until then nothing imported `evals/agent_sweep.py`, and three of its defects reached the
published report: every token priced at the arm's price, a pivot rate pooled over both arms,
and a `KeyError` on the committed calibration set that would have lost a whole paid pass at the
moment of writing its artefact. Each is pinned here in the direction that would have caught it.

Offline and free: synthetic rows, the scripted doubles of the loop, and the committed artefact
of run `293fe5c6e470`, which is read and never rewritten.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.assist.agent import run_agent
from jbg_ai.assist.prompt import load_prompt_file
from jbg_ai.assist.tools import build_registry
from jbg_ai.assist.transcript import turns_from
from jbg_ai.data.paths import AI_SERVICE_ROOT
from jbg_ai.evals.agent_sweep import (
    CALIBRATION,
    FAMILY_WITH_VARIANTS,
    MEASURED_PROMPTS,
    PIECE_MARKER,
    PRICES,
    _cost,
    _row,
    append_record,
    availability_terms_in,
    expectation_verdict,
    legacy_router_usage,
    load_artefact,
    pivot_rates,
    projection_freshness,
    prompt_digests,
    rescore,
    rescore_path,
    scenario_turns,
    stage_costs,
    stage_usages,
    summarise,
)
from jbg_ai.knowledge.offline import InMemoryKnowledgeIndex
from support.assist_agent import finishes, scripted_agent, wants
from support.assist_pitch import pitch, scripted_client
from support.assist_router import decision, scripted_router
from support.assist_world import indexed_row
from support.fake_embedding_client import FakeEmbeddingClient
from support.fake_product_search import FakeProductSearch
from support.settings import TOKEN_POS_ID, build_settings

PASS = AI_SERVICE_ROOT / "evals" / "results" / "c32b-agent-sweep-293fe5c6e470.json"

GPT4O = "openai/gpt-4o"
MINI = "openai/gpt-4o-mini"


def row_like(**overrides) -> dict:
    """The keys the aggregates read, and nothing else. A test states only what it is about."""
    values = {
        "id": "X01",
        "set": "calibration",
        "arm": GPT4O,
        "stop_reason": "sin_mas_herramientas",
        "partial": False,
        "iterations": 1,
        "provider_calls": 3,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "elapsed_ms": 1.0,
        "per_iteration": [],
        "tools_invoked": [],
        "invented_tools": [],
        "pitch_ran": False,
        "pitch_withheld": False,
        "pitch_initial_violations": [],
        "fixture": None,
        "expects": None,
        "forbids": None,
    }
    values.update(overrides)
    return values


def turn_like(prompt_tokens: int, completion_tokens: int, iteration: int = 1) -> dict:
    return {
        "iteration": iteration,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "context_chars": 0,
        "elapsed_ms": 1.0,
        "provider_error": None,
        "cut_by_clock": False,
        "tools": [],
    }


def stage(model: str, prompt_tokens: int, completion_tokens: int, calls: int = 1) -> dict:
    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "calls": calls,
    }


# --- C2 · the pivot rates: per arm, and only over availability fixtures ------------------------


def test_the_pivot_rates_skip_a_fixture_that_is_not_an_availability_label() -> None:
    """The committed calibration set, run through the aggregate that writes the artefact.

    C05 declares a piece with variants, not an availability label, and the first form of this
    function read `fixture["availability"]` unconditionally: `KeyError`, raised while writing
    the artefact, after every request of the pass had been paid for.
    """
    scenarios = yaml.safe_load(CALIBRATION.read_text(encoding="utf-8"))["scenarios"]
    rows = [
        row_like(
            id=item["id"],
            arm=arm,
            fixture=item.get("fixture"),
            expects=item.get("expects"),
            forbids=item.get("forbids"),
        )
        for item in scenarios
        for arm in (GPT4O, MINI)
    ]
    assert any((row["fixture"] or {}).get("family") for row in rows), (
        "the set must still carry a non-availability fixture for this to mean anything"
    )

    rates = pivot_rates(rows)

    assert set(rates) == {GPT4O, MINI}
    for labels in rates.values():
        assert set(labels) == {
            "sin_existencias",
            "ultimas_unidades",
            "disponible",
            "sin_ambito",
        }
        assert "C05" not in {i for bucket in labels.values() for i in bucket["ids"]}


def test_the_pivot_rates_are_kept_per_arm_with_over_and_under_pivots_apart() -> None:
    """The first form pooled both arms, and the one under-pivot it published was the cheap
    arm's, presented as evidence about the arm the change chose."""
    out_of_stock = {"availability": "sin_existencias"}
    last_units = {"availability": "ultimas_unidades"}
    rows = [
        row_like(id="A", arm=GPT4O, fixture=out_of_stock, expects=["buscar_sustitutos"],
                 tools_invoked=["consultar_disponibilidad", "buscar_sustitutos"]),
        row_like(id="A", arm=MINI, fixture=out_of_stock, expects=["buscar_sustitutos"],
                 tools_invoked=["consultar_disponibilidad"]),
        row_like(id="B", arm=MINI, fixture=last_units, forbids=["buscar_sustitutos"],
                 tools_invoked=["consultar_disponibilidad", "buscar_sustitutos"]),
    ]

    rates = pivot_rates(rows)

    assert rates[GPT4O]["sin_existencias"]["failure"] == "ninguno"
    assert rates[GPT4O]["sin_existencias"]["pivot_rate"] == 1.0
    assert rates[MINI]["sin_existencias"]["infra_pivots"] == 1
    assert rates[MINI]["sin_existencias"]["failure"] == "infra-pivote"
    assert rates[MINI]["ultimas_unidades"]["over_pivots"] == 1
    assert rates[MINI]["ultimas_unidades"]["failure"] == "sobre-pivote"
    assert "ultimas_unidades" not in rates[GPT4O]


# --- C1 · cost, stage by stage --------------------------------------------------------------------


def test_each_stage_is_priced_by_its_own_model_and_not_by_the_arms() -> None:
    """A request of the cheap arm still pays `gpt-4o` for its classifier.

    Priced at the arm's rate — the first form — the whole request of this row costs less than
    its classifier alone, which is how the report once found the agent cheaper than the pipeline.
    """
    row = row_like(
        arm=MINI,
        prompt_tokens=3_305 + 7_000 + 2_700,
        completion_tokens=15 + 400 + 150,
        stages={
            "router": stage(GPT4O, 3_305, 15),
            "loop": stage(MINI, 7_000, 400, calls=3),
            "pitch": stage(MINI, 2_700, 150),
        },
    )

    costs = stage_costs(row)
    router = (3_305 * PRICES[GPT4O][0] + 15 * PRICES[GPT4O][1]) / 1e6
    loop = (7_000 * PRICES[MINI][0] + 400 * PRICES[MINI][1]) / 1e6
    argument = (2_700 * PRICES[MINI][0] + 150 * PRICES[MINI][1]) / 1e6

    assert costs == pytest.approx({"router": router, "loop": loop, "pitch": argument})
    assert _cost(row) == pytest.approx(router + loop + argument)
    everything_at_the_arms_price = (
        row["prompt_tokens"] * PRICES[MINI][0] + row["completion_tokens"] * PRICES[MINI][1]
    ) / 1e6
    assert everything_at_the_arms_price < router < _cost(row)


def test_a_row_written_before_the_record_is_split_with_the_classifier_of_its_own_artefact() -> None:
    """Rows of run `293fe5c6e470` carry the sum and the loop's turns, not the stages.

    Where the argument did not run, what a row spent beyond its loop is the classifier's alone;
    that is where the classifier of every other row is read from, and never from a figure
    attributed to another change.
    """
    without_argument = [
        row_like(prompt_tokens=3_305 + 5_000, completion_tokens=15 + 300,
                 per_iteration=[turn_like(5_000, 300)]),
        row_like(prompt_tokens=3_310 + 4_000, completion_tokens=16 + 200,
                 per_iteration=[turn_like(4_000, 200)]),
        row_like(prompt_tokens=3_301 + 6_000, completion_tokens=14 + 100,
                 per_iteration=[turn_like(6_000, 100)]),
    ]
    with_argument = row_like(
        prompt_tokens=3_305 + 7_000 + 2_000,
        completion_tokens=15 + 500 + 120,
        per_iteration=[turn_like(7_000, 500)],
        pitch_ran=True,
    )

    legacy = legacy_router_usage([*without_argument, with_argument])

    assert legacy is not None
    assert (legacy["prompt_tokens"], legacy["completion_tokens"]) == (3_305, 15)
    assert legacy["n"] == 3 and legacy["prompt_tokens_range"] == [3_301, 3_310]

    split = stage_usages(with_argument, legacy=legacy)
    assert split["router"]["model"] == GPT4O
    assert (split["loop"]["prompt_tokens"], split["loop"]["model"]) == (7_000, GPT4O)
    assert (split["pitch"]["prompt_tokens"], split["pitch"]["completion_tokens"]) == (2_000, 120)

    with pytest.raises(ValueError, match="cannot be split"):
        stage_usages(with_argument, legacy=None)


# --- A6 · the calibration set is scored by code, with the semantics it declares -----------------


def test_the_expectation_verdict_reads_each_field_by_its_declared_semantics() -> None:
    """All of `expects`, one of `expects_any`, none of `forbids` — each in both directions."""
    both = {"expects": ["buscar_catalogo", "consultar_conocimiento"]}
    either = {"expects_any": ["buscar_catalogo", "pedir_aclaracion"]}
    never = {"expects": [], "forbids": ["buscar_sustitutos"]}

    assert expectation_verdict(["buscar_catalogo", "consultar_conocimiento"], both)["met"]
    assert not expectation_verdict(["buscar_catalogo"], both)["met"]
    assert expectation_verdict(["pedir_aclaracion"], either)["met"]
    assert not expectation_verdict(["listar_familia"], either)["met"]
    assert expectation_verdict([], never)["met"], "an empty `expects` is met vacuously"
    assert not expectation_verdict(["buscar_sustitutos"], never)["met"]
    # A scenario with no expectation at all is not scored, rather than counted as met.
    assert expectation_verdict(["buscar_catalogo"], {"id": "L001"}) is None
    # A known miss stays a miss, and says it is known.
    declared = expectation_verdict([], {"expects": ["buscar_catalogo"], "declared_discrepancy": "x"})
    assert declared["met"] is False and declared["declared_discrepancy"] is True


def test_every_scenario_of_the_calibration_set_can_be_scored() -> None:
    """A scenario the scorer cannot read would be green by omission."""
    for item in yaml.safe_load(CALIBRATION.read_text(encoding="utf-8"))["scenarios"]:
        assert expectation_verdict([], item) is not None, item["id"]


def test_the_marker_is_resolved_for_both_kinds_of_fixture_and_a_missing_piece_skips() -> None:
    """The rule the set pins in its own file is only as good as the code that applies it."""
    scenarios = {
        item["id"]: item
        for item in yaml.safe_load(CALIBRATION.read_text(encoding="utf-8"))["scenarios"]
    }
    pieces = {"sin_existencias": "SKU637", FAMILY_WITH_VARIANTS: "SKU100"}

    out_of_stock = " ".join(turn.text for turn in scenario_turns(scenarios["C07"], pieces))
    variants = " ".join(turn.text for turn in scenario_turns(scenarios["C05"], pieces))

    assert "SKU637" in out_of_stock and PIECE_MARKER not in out_of_stock
    assert "SKU100" in variants and PIECE_MARKER not in variants
    assert scenario_turns(scenarios["C08"], pieces) is None, "no piece, no run"


# --- A7 · a run leaves what it paid for, and says which texts it measured ---------------------------


def test_an_interrupted_run_leaves_a_record_that_a_rescore_can_read(tmp_path: Path) -> None:
    """The aborted pass of C32b left nothing: the artefact was written only at the end."""
    record = tmp_path / "c32b-agent-sweep-abc.partial.jsonl"
    row = row_like(
        set="load",
        prompt_tokens=3_305 + 1_000,
        completion_tokens=15 + 50,
        per_iteration=[turn_like(1_000, 50)],
        stages={
            "router": stage(GPT4O, 3_305, 15),
            "loop": stage(GPT4O, 1_000, 50),
            "pitch": stage(MINI, 0, 0, calls=0),
        },
    )
    append_record(record, {"provenance": {"run_id": "abc"}})
    append_record(record, {"row": row})

    document = load_artefact(record)
    assert document["partial"] is True
    assert document["rows"] == [row]

    result = rescore(record, calibration={"scenarios": []})
    assert result["rescored_from"]["partial"] is True
    assert result["summary"][f"{GPT4O}::load"]["requests"] == 1
    assert rescore_path(record).name == "c32b-agent-sweep-abc.rescore.json"


def test_the_provenance_records_the_text_of_every_measured_prompt() -> None:
    """A version label does not identify a text: the probes of C32b recorded `agent/v1` and
    `assist/v4` over texts that changed between one probe and the next."""
    digests = prompt_digests()

    assert set(digests) == set(MEASURED_PROMPTS)
    for version, digest in digests.items():
        assert digest == hashlib.sha256(load_prompt_file(version).encode("utf-8")).hexdigest()


# --- A1d · availability in the served argument is counted, since nothing prevents it -----------------


def test_availability_terms_are_counted_in_a_served_argument() -> None:
    assert availability_terms_in("Una pieza de plata con un acabado sobrio.") == 0
    assert availability_terms_in("Está disponible en tu tienda.") == 1
    assert availability_terms_in("Quedan ÚLTIMAS UNIDADES y la otra está agotada.") == 2
    assert availability_terms_in("sin_existencias, sin ámbito y disponibles") == 3
    assert availability_terms_in("") == 0


def test_a_row_records_each_stage_its_expectation_and_its_availability_count() -> None:
    """Driven through the real loop with the scripted doubles, so the row is what a pass writes."""
    principal = ServicePrincipal(
        user_id="u", role="Operator", trace_id="t", pos_id=TOKEN_POS_ID
    )
    registry = build_registry(
        principal=principal,
        settings=build_settings(),
        embed=FakeEmbeddingClient(),
        search=FakeProductSearch([indexed_row()]),
        knowledge=InMemoryKnowledgeIndex(chunks=[]),
    )
    agent, _ = scripted_agent(wants(("buscar_catalogo", {"consulta": "anillo"})), finishes())
    router, _ = scripted_router(decision())
    argument, _ = scripted_client(pitch("Esta pieza está disponible y es de plata."))
    item = {
        "id": "C99",
        "turns": [{"role": "operario", "text": "busco un anillo"}],
        "expects": ["buscar_catalogo"],
        "forbids": ["buscar_sustitutos"],
    }

    run = asyncio.run(
        run_agent(
            turns_from([("operario", "busco un anillo")]),
            principal,
            registry=registry,
            agent_client=agent,
            router_client=router,
            pitch_client=argument,
        )
    )
    row = _row(item=item, set_id="calibration", arm="fake/agent-model", run=run, elapsed_ms=1.0)

    assert {name: row["stages"][name]["calls"] for name in ("router", "loop", "pitch")} == {
        "router": 1,
        "loop": 2,
        "pitch": 1,
    }
    assert sum(row["stages"][name]["prompt_tokens"] for name in row["stages"]) == row[
        "prompt_tokens"
    ]
    assert row["expectation"]["met"] is True
    assert row["pitch_availability_terms"] == 1
    assert row["turns_sha256"] == hashlib.sha256(
        json.dumps(item["turns"], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


# --- the published figures, recomputed from the committed artefact --------------------------------


def test_the_rescore_of_the_committed_pass_reproduces_the_figures_the_report_publishes() -> None:
    """**The numbers of the report, reached by code and pinned.** Until the independent
    verification of C32b the corrected cost, the per-arm pivot rates and the OK/MISS table
    were computed by hand, and one of the three was wrong.

    What this pins: the classifier derived from the artefact's own rows (~3.305 prompt tokens
    on `gpt-4o`, ~0,0084 USD a request), the cost of each arm stage by stage, the pivot rates
    per arm, and the calibration scored both as it ran and against today's file.
    """
    result = rescore(PASS)

    legacy = result["legacy_router_usage"]
    assert legacy["prompt_tokens"] == 3_305 and legacy["n"] == 39
    assert legacy["prompt_tokens_range"] == [3_301, 3_312]

    per_request: dict[str, float] = {}
    for arm in (GPT4O, MINI):
        subsets = [v for k, v in result["summary"].items() if k.startswith(f"{arm}::")]
        requests = sum(item["requests"] for item in subsets)
        per_request[arm] = sum(item["cost_usd_total"] for item in subsets) / requests
        assert requests == 102
        assert all(item["unpriced_models"] == [] for item in subsets)
    assert per_request[GPT4O] == pytest.approx(0.02742, abs=5e-5)
    assert per_request[MINI] == pytest.approx(0.01008, abs=5e-5)
    total = sum(item["cost_usd_total"] for item in result["summary"].values())
    assert total == pytest.approx(3.82, abs=0.01)

    pivots = result["pivot_rates"]
    assert pivots[GPT4O]["sin_existencias"]["pivoted"] == 3
    assert pivots[GPT4O]["sin_existencias"]["failure"] == "ninguno"
    assert pivots[MINI]["sin_existencias"]["infra_pivots"] == 1
    assert pivots[MINI]["sin_existencias"]["ids"] == ["C07", "C11", "C12"]
    for arm in (GPT4O, MINI):
        for label in ("ultimas_unidades", "disponible", "sin_ambito"):
            assert (pivots[arm][label]["scenarios"], pivots[arm][label]["over_pivots"]) == (1, 0)

    as_run = result["expectations"]["as_run"]
    assert (as_run[GPT4O]["ok"], as_run[GPT4O]["miss"]) == (16, 4)
    assert (as_run[MINI]["ok"], as_run[MINI]["miss"]) == (14, 6)
    current = result["expectations"]["current"]
    assert (current[GPT4O]["ok"], current[GPT4O]["miss"]) == (18, 0)
    assert current[GPT4O]["declared"] == ["C19"]
    assert (current[MINI]["ok"], sorted(current[MINI]["missed"])) == (16, ["C03", "C11"])
    assert current[GPT4O]["not_comparable"] == ["C05"]


def test_the_embedded_summary_of_the_committed_pass_is_the_one_this_harness_no_longer_writes() -> None:
    """The artefact is a dated measurement and is not rewritten, so its embedded summary keeps
    the first cost formula. Pinned so that the two figures in circulation are told apart on
    purpose: the embedded one prices every token at the arm's rate, the rescore does not."""
    embedded = json.loads(PASS.read_text(encoding="utf-8"))["summary"]
    rescored = summarise(
        load_artefact(PASS)["rows"],
        legacy=legacy_router_usage(load_artefact(PASS)["rows"]),
    )

    assert embedded[f"{MINI}::load"]["cost_usd_per_request"] == pytest.approx(0.002301)
    assert rescored[f"{MINI}::load"]["cost_usd_per_request"] > 4 * 0.002301


# --- the instruments C42 added, before it took the pass it publishes -----------------------------


def test_agent_sweep_counts_placeholders() -> None:
    """**Counted on the FIRST attempt**, which is what the prompt produced before any repair.

    The rule is `free_query_gate`'s and the reason is the same: counting the served argument
    would report zero for every placeholder the single repair removed, and so would measure the
    repair rather than the prompt. Driven through the real loop, so the row is what a pass writes.
    """
    principal = ServicePrincipal(
        user_id="u", role="Operator", trace_id="t", pos_id=TOKEN_POS_ID
    )
    registry = build_registry(
        principal=principal,
        settings=build_settings(),
        embed=FakeEmbeddingClient(),
        search=FakeProductSearch([indexed_row()]),
        knowledge=InMemoryKnowledgeIndex(chunks=[]),
    )
    agent, _ = scripted_agent(wants(("buscar_catalogo", {"consulta": "anillo"})), finishes())
    router, _ = scripted_router(decision())
    # The exact defect C42 fixes: the agent's task runs over an UNANCHORED payload, so a
    # placeholder has nothing to resolve against and since C40 it is a hard violation.
    argument, _ = scripted_client(
        pitch("Cuesta {{price}} y su disponibilidad es {{stock}}. Otra cuesta {{price}}.")
    )
    item = {"id": "C98", "turns": [{"role": "operario", "text": "busco un anillo"}]}

    run = asyncio.run(
        run_agent(
            turns_from([("operario", "busco un anillo")]),
            principal,
            registry=registry,
            agent_client=agent,
            router_client=router,
            pitch_client=argument,
        )
    )
    row = _row(item=item, set_id="load", arm="fake/agent-model", run=run, elapsed_ms=1.0)

    assert (row["price_placeholders"], row["stock_placeholders"]) == (2, 1)

    summary = summarise([row])["fake/agent-model::load"]["pitch_placeholders"]
    assert summary == {
        "price_total": 2,
        "stock_total": 1,
        "generations_with_a_price_placeholder": 1,
        "generations_with_a_stock_placeholder": 1,
    }


def test_the_placeholder_aggregate_is_absent_and_not_zero_for_rows_that_predate_it() -> None:
    """Zero would assert that no placeholder was written; the committed pass never counted."""
    rows = load_artefact(PASS)["rows"]
    summary = summarise(rows, legacy=legacy_router_usage(rows))

    assert all("price_placeholders" not in row for row in rows)
    assert summary[f"{GPT4O}::load"]["pitch_placeholders"] is None
    # Same rule for the freshness audit: the pass that motivated recording it recorded nothing.
    assert summary[f"{GPT4O}::load"]["projection_freshness"] is None


def test_agent_sweep_records_projection_age() -> None:
    """The age comes from the **checkpoint**, and the verdict flips at the configured ceiling.

    Recorded per row because a pass lasts longer than the ceiling: C32b's took 2 h 44 min
    against 1 h, and with no recorded age its rows cannot be told from rows that were fresh.
    """
    settings = build_settings()
    ceiling = settings.jpv_pos_projection_max_age_seconds
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

    fresh = FakeProductSearch([indexed_row()], synced_at=now - timedelta(seconds=60))
    verdict = asyncio.run(projection_freshness(fresh, settings, now=now))
    assert verdict["stale"] is False
    assert verdict["age_seconds"] == pytest.approx(60.0)
    assert verdict["ceiling_seconds"] == ceiling
    # Read through the port that consults `ai.sync_checkpoint`, never `pos_projection.refreshed_at`.
    assert fresh.synced_at_calls == 1

    stale = FakeProductSearch(
        [indexed_row()], synced_at=now - timedelta(seconds=ceiling + 1)
    )
    assert asyncio.run(projection_freshness(stale, settings, now=now))["stale"] is True

    # Never drained is stale too: the prefilter does not apply then either.
    never = FakeProductSearch([indexed_row()], never_synchronised=True)
    blank = asyncio.run(projection_freshness(never, settings, now=now))
    assert (blank["age_seconds"], blank["stale"], blank["synced_at"]) == (None, True, None)


def test_a_degraded_row_is_identifiable_rather_than_averaged_in() -> None:
    """The audit a pass longer than the ceiling needs: which rows were served without scope."""
    rows = [
        {
            "arm": "a",
            "set": "load",
            "stop_reason": "fin",
            "partial": False,
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "total_tokens": 2,
            "elapsed_ms": 1.0,
            "iterations": 1,
            "provider_calls": 1,
            "per_iteration": [],
            "tools_invoked": [],
            "invented_tools": [],
            "pitch_initial_violations": [],
            "pitch_ran": False,
            "pitch_withheld": False,
            "stages": {
                name: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                       "calls": 0, "model": None}
                for name in ("router", "loop", "pitch")
            },
            "expectation": None,
            "projection_age_seconds": age,
            "projection_stale": stale,
        }
        for age, stale in ((10.0, False), (10.0, False), (7200.0, True))
    ]

    freshness = summarise(rows)["a::load"]["projection_freshness"]
    assert (freshness["rows_recorded"], freshness["rows_stale"]) == (3, 1)
    assert freshness["age_seconds"]["max"] == 7200.0
