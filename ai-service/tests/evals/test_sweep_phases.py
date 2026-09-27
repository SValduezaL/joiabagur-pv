"""The two phases of the calibration sweep: capture once, re-score many times. C25.

The order of the phases is a constraint and not a preference. The fusion moves the candidate
window; the business signals only reorder it. So the fusion is frozen first, each window
records the fusion it was taken under, and a re-score against a different one is REFUSED —
because the failure it prevents is silent: phase C would run, report a winner, and that winner
would have been chosen over a candidate set the live fusion no longer produces.
"""

from __future__ import annotations

import json
import socket
from dataclasses import replace

import pytest

from jbg_ai.evals.configs import load_config
from jbg_ai.evals.errors import ConfigurationError
from jbg_ai.config.settings import Settings
from jbg_ai.evals.golden import OUT_OF_DOMAIN, load_golden_set
from jbg_ai.evals.sweep import (
    CAPTURE_VERSION,
    Capture,
    CapturedCandidate,
    CapturedWindow,
    FusionFingerprint,
    business_grid,
    check_fusion_matches,
    rescore,
    rescore_window,
)
from jbg_ai.retrieval.abstention import AbstentionRule
from jbg_ai.retrieval.filters import BusinessWeights


def _fingerprint(**overrides) -> FusionFingerprint:
    values = dict(
        rrf_k=60,
        branch_depth=60,
        branch_weight_lexical=0.5,
        branch_weight_vector=0.5,
        coverage_rule="continuous",
        expand_synonyms=True,
        signal_pos_id=None,
        retrieval_mode="hybrid",
    )
    values.update(overrides)
    return FusionFingerprint(**values)


def _candidate(product_id: str, **overrides) -> CapturedCandidate:
    values = dict(
        product_id=product_id,
        sku=product_id[:8],
        score=0.5,
        price=None,
        size_label=None,
        materials=(),
        qty_bucket=None,
        sales_30d=None,
        family_id=None,
        branches=("lexical",),
    )
    values.update(overrides)
    return CapturedCandidate(**values)


def _window(*candidates: CapturedCandidate, text: str = "anillo de plata") -> CapturedWindow:
    return CapturedWindow(
        query_id="q01", query_text=text, low_confidence=False, candidates=candidates
    )


def _capture(*windows: CapturedWindow, fusion: FusionFingerprint | None = None) -> Capture:
    return Capture(
        version=CAPTURE_VERSION,
        golden_set_version="1:test",
        fusion=fusion or _fingerprint(),
        windows=windows,
    )


# --------------------------------------------------------------------------- phase C is pure


def test_rescore_phase_reaches_no_provider_and_no_database(monkeypatch) -> None:
    """The property that makes hundreds of combinations affordable, enforced rather than hoped.

    Every socket is severed for the duration: if the re-score reached a provider or a pool it
    would raise here instead of quietly costing money and time.
    """

    def refuse(*args, **kwargs):  # pragma: no cover - the point is that it never runs
        raise AssertionError("the re-score phase opened a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)

    golden = load_golden_set()
    query = golden.judged_queries[0]
    judged = golden.judgements_for(query.id)
    window = CapturedWindow(
        query_id=query.id,
        query_text=query.text,
        low_confidence=False,
        candidates=tuple(
            _candidate(item.product_id, qty_bucket="3+", sales_30d=1) for item in judged[:10]
        ),
    )

    readings = rescore(_capture(window), golden, BusinessWeights(availability=1.0))

    assert readings["global"].queries == 1
    assert "ndcg_at_5" in readings["global"].values


def test_calibration_sweep_is_reproducible() -> None:
    """Structural, not a promise about seeds. The input is a file and the sort is stable.

    C24 could only assert this over runs that called a provider and a database, so its
    reproducibility rested on frozen vectors and a deterministic tiebreak. Here the whole
    input is persisted, so two re-scores CANNOT differ.
    """
    golden = load_golden_set()
    query = golden.judged_queries[0]
    judged = golden.judgements_for(query.id)
    window = CapturedWindow(
        query_id=query.id,
        query_text=query.text,
        low_confidence=False,
        candidates=tuple(
            _candidate(
                item.product_id,
                qty_bucket="0" if index % 3 else "3+",
                sales_30d=index % 2,
            )
            for index, item in enumerate(judged[:12])
        ),
    )
    captured = _capture(window)
    weights = BusinessWeights(availability=1.0)

    first = rescore(captured, golden, weights)
    second = rescore(captured, golden, weights)

    assert first["global"].values == second["global"].values
    assert rescore_window(window, weights) == rescore_window(window, weights)


def test_the_rescore_orders_by_the_weights_and_removes_nothing() -> None:
    """Phase C reorders a window; it never shortens one."""
    window = _window(
        _candidate("11111111-1111-1111-1111-111111111111", qty_bucket="0", sales_30d=0),
        _candidate("22222222-2222-2222-2222-222222222222", qty_bucket="3+", sales_30d=5),
        _candidate("33333333-3333-3333-3333-333333333333", qty_bucket=None, sales_30d=None),
    )
    # Only the exhausted candidate can move: the sales window orders nothing.

    weighted = rescore_window(window, BusinessWeights(availability=1.0))
    zeroed = rescore_window(window, BusinessWeights())

    assert len(weighted) == len(zeroed) == 3, "no candidate may be dropped"
    assert set(weighted) == set(zeroed)
    assert zeroed == tuple(item.product_id for item in window.candidates), (
        "zero weights must reproduce the captured order"
    )
    assert weighted[-1] == "11111111-1111-1111-1111-111111111111", (
        "the exhausted candidate must fall to the back"
    )


# ------------------------------------------------------------------ the fusion must match


def test_window_captured_under_a_different_fusion_is_refused() -> None:
    """The gate against inverting the phases, which is otherwise a SILENT failure."""
    captured = _capture(_window(_candidate("11111111-1111-1111-1111-111111111111")))

    # The same fusion: accepted.
    check_fusion_matches(captured, _fingerprint())

    for field, value in (
        ("rrf_k", 40),
        ("branch_depth", 40),
        ("branch_weight_vector", 0.4),
        ("coverage_rule", "none"),
        ("expand_synonyms", False),
    ):
        with pytest.raises(ConfigurationError) as excinfo:
            check_fusion_matches(captured, _fingerprint(**{field: value}))
        assert field in str(excinfo.value), "the mismatch must name what differs"
        assert "captura" in str(excinfo.value), "and say how to fix it"


def test_the_fingerprint_resolves_knobs_to_their_effective_values() -> None:
    """Two configurations that mean the same thing must fingerprint the same.

    A configuration leaving a knob unset inherits the setting, so comparing the declared
    values would refuse a window that is in fact compatible - and refusing valid work trains
    people to pass the override that silences the check.
    """
    # A plain `Settings`, not the harness profile: this test is about resolving knobs and
    # must not require a database URL to answer a question that has nothing to do with one.
    settings = Settings(app_env="local", service_version="c25", jwt_secret="x" * 32)
    explicit = replace(
        load_config("v2b-fusion"),
        rrf_k=settings.jpv_rrf_k,
        branch_depth=settings.jpv_branch_depth,
    )
    inherited = replace(load_config("v2b-fusion"), rrf_k=None, branch_depth=None)

    assert FusionFingerprint.of(explicit, settings) == FusionFingerprint.of(
        inherited, settings
    )


def test_the_fingerprint_excludes_the_business_weights() -> None:
    """They are what phase C VARIES, and they never change which candidates exist.

    Including them would refuse every re-score but the one that matched the capture, which is
    the same as having no phase C at all.
    """
    fields = set(FusionFingerprint.__dataclass_fields__)

    assert not any("business" in name for name in fields)
    assert "branch_weight_lexical" in fields, "but the fusion weights ARE part of it"
    assert "branch_weight_vector" in fields


def test_a_capture_written_by_another_version_is_refused() -> None:
    """Its fields may not mean the same thing, and reading them anyway is the silent case."""
    payload = _capture(_window(_candidate("11111111-1111-1111-1111-111111111111"))).to_json()

    assert Capture.from_json(payload).version == CAPTURE_VERSION

    with pytest.raises(ConfigurationError, match="version"):
        Capture.from_json(payload.replace(f'"version": {CAPTURE_VERSION}', '"version": 99'))


def test_a_capture_survives_a_round_trip_through_its_file() -> None:
    """Phase C reads a file, so what the file loses, phase C never had."""
    original = _capture(
        _window(
            _candidate(
                "11111111-1111-1111-1111-111111111111",
                price=42.0,
                size_label="L",
                materials=("plata", "oro"),
                qty_bucket="1-2",
                sales_30d=3,
                family_id="22222222-2222-2222-2222-222222222222",
                branches=("lexical", "vector"),
            )
        )
    )

    restored = Capture.from_json(original.to_json())

    assert restored == original
    candidate = restored.windows[0].candidates[0]
    assert candidate.materials == ("plata", "oro")
    assert candidate.qty_bucket == "1-2" and candidate.sales_30d == 3
    assert candidate.branches == ("lexical", "vector")


def test_the_business_grid_has_one_dimension_and_two_outcomes() -> None:
    """The grid explores one weight, and reports that its VALUE does not change the order.

    Saying so is part of the result rather than a caveat about it: with a single binary term
    the business score takes two values, so every positive weight produces the same ranking.
    The grid is run over several values anyway, cheaply and offline, because a grid that
    reports the invariance is evidence while asserting it would be an argument.
    """
    grid = business_grid(availability=(0.0, 0.5, 1.0, 2.0))

    assert [item.availability for item in grid] == [0.0, 0.5, 1.0, 2.0]
    assert BusinessWeights(availability=0.0) in grid, "the rollback is a point of the grid"
    assert all(not hasattr(item, "rotation") for item in grid)

    # One window, and every positive weight orders it the same way.
    window = _window(
        _candidate("11111111-1111-1111-1111-111111111111", qty_bucket="0", sales_30d=6),
        _candidate("22222222-2222-2222-2222-222222222222", qty_bucket="3+", sales_30d=0),
    )
    orders = {rescore_window(window, item) for item in grid if item.availability > 0}
    assert len(orders) == 1, "the value of the weight must not change the order"
    assert rescore_window(window, BusinessWeights()) != orders.pop(), (
        "and zero must restore the captured order"
    )


def test_the_capture_phase_runs_end_to_end_against_the_ports() -> None:
    """Exercises `capture` itself, which nothing did until it broke in production.

    It was calling `retrieve_products` with a keyword the orchestration no longer takes, and
    no test noticed because every other test in this file builds its windows by hand. A phase
    whose only exercise is running it against a real database is a phase that fails on the day
    somebody needs it.
    """
    import asyncio
    from uuid import UUID

    from jbg_ai.evals.sweep import capture

    from support.fake_embedding_client import FakeEmbeddingClient
    from support.fake_product_search import FakeAssignment, FakeIndexedRow, FakeProductSearch
    from support.settings import TOKEN_POS_ID, build_settings

    pos = UUID(TOKEN_POS_ID)
    product = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    search = FakeProductSearch(
        [
            FakeIndexedRow(
                product_id=product,
                sku="RING-1",
                distance=0.2,
                materials=["plata"],
                piece_type="anillo",
                doc_text="Tipo: anillo de plata. Materiales: plata.",
            )
        ],
        assignments=[FakeAssignment(pos_id=pos, product_id=product, qty_bucket="0", sales_30d=3)],
    )
    config = replace(load_config("v3-senales"), signal_pos_id=str(pos))

    result = asyncio.run(
        capture(
            config,
            load_golden_set(),
            settings=build_settings(),
            search=search,
            embed=FakeEmbeddingClient(),
        )
    )

    assert result.version == CAPTURE_VERSION
    # `retrieval_queries` and not `judged_queries`: C26 added five judged SUBSTITUTES
    # queries, which this sweep does not and must not run — they are answered by a route
    # that takes a product identifier, and counting them here would move the denominator
    # of the published ablation table.
    assert len(result.windows) == len(load_golden_set().retrieval_queries), (
        "one window per judged query of the product retriever"
    )
    assert result.fusion.signal_pos_id == str(pos)
    assert result.buckets, "the assortment's buckets must be persisted for the operational metric"

    # The signals really travelled, which is the whole point of persisting the window.
    carried = [
        item
        for window in result.windows
        for item in window.candidates
        if item.qty_bucket is not None
    ]
    assert carried, "no candidate carried a signal"
    assert carried[0].qty_bucket == "0"
    assert carried[0].sales_30d == 3

    # And the window is the FUSION's output: captured with the business weights pinned to zero,
    # so a re-score applies the whole ordering key from scratch.
    assert not any("business" in name for name in result.fusion.__dataclass_fields__)


# --------------------------------------------- C40 · the profile the decision actually read


#: Flat: twenty candidates inside the band, which is what the live rule reads as "the
#: catalogue has nothing for this query".
FLAT_PROBE = tuple(0.500 + 0.0005 * index for index in range(20))
#: Peaked: one candidate stands out, so the query IS answerable.
PEAKED_PROBE = (0.21,) + tuple(0.44 + 0.01 * index for index in range(19))

LIVE_RULE = AbstentionRule(enabled=True, band_alpha=0.03, min_candidates=15)


def _out_of_domain_query(golden):
    """The category `abstention_rate` is reported over."""
    return next(
        query
        for query in golden.retrieval_queries
        if query.category == OUT_OF_DOMAIN
    )


def _abstention_rate(readings) -> float:
    return readings[f"category:{OUT_OF_DOMAIN}"].values["abstention_rate"]


def test_rescore_recomputes_the_decision_from_the_persisted_probe() -> None:
    """A filtered pass decided over a profile the persisted window does not contain.

    Without the probe in the file the re-score could only read `low_confidence`, which is the
    absence of cross-branch consensus and **not** the abstention: it would report a decision
    the run never took. Both windows below carry `low_confidence=False`; only the profile
    separates them, and the re-score must separate them too.
    """
    golden = load_golden_set()
    # An out-of-domain query, because `abstention_rate` is reported over that category: it
    # is the population the rule was calibrated against, and the one where declining is the
    # right answer.
    query = _out_of_domain_query(golden)
    judged = golden.judgements_for(query.id)
    candidates = tuple(_candidate(item.product_id) for item in judged[:10])

    def _capture_with(probe):
        window = CapturedWindow(
            query_id=query.id,
            query_text=query.text,
            low_confidence=False,
            candidates=candidates,
            probe_distances=probe,
        )
        return Capture(
            version=CAPTURE_VERSION,
            golden_set_version="1:test",
            fusion=_fingerprint(),
            windows=(window,),
            abstention=LIVE_RULE,
        )

    weights = BusinessWeights(availability=0.0)
    flat = rescore(_capture_with(FLAT_PROBE), golden, weights)
    peaked = rescore(_capture_with(PEAKED_PROBE), golden, weights)

    # The rate is the reading the abstention feeds, and it moves with the profile alone.
    assert _abstention_rate(flat) == 1.0
    assert _abstention_rate(peaked) == 0.0


def test_a_window_without_a_probe_is_scored_exactly_as_before() -> None:
    """No probe means the rule read the served candidates, which is every capture until C40.

    Asserted so the change cannot move a published figure: the golden set is unfiltered from
    end to end, so no window in it carries a probe and every reading must be untouched.
    """
    golden = load_golden_set()
    query = _out_of_domain_query(golden)
    judged = golden.judgements_for(query.id)
    window = CapturedWindow(
        query_id=query.id,
        query_text=query.text,
        low_confidence=True,
        candidates=tuple(_candidate(item.product_id) for item in judged[:10]),
    )

    readings = rescore(_capture(window), golden, BusinessWeights(availability=0.0))

    assert window.probe_distances is None
    assert _abstention_rate(readings) == 1.0, (
        "with no probe the decision is read off the window, exactly as before C40"
    )


def test_a_persisted_probe_with_no_rule_is_refused_rather_than_guessed() -> None:
    """Guessing is precisely what persisting the profile exists to avoid, so it raises."""
    golden = load_golden_set()
    query = _out_of_domain_query(golden)
    judged = golden.judgements_for(query.id)
    capture = Capture(
        version=CAPTURE_VERSION,
        golden_set_version="1:test",
        fusion=_fingerprint(),
        windows=(
            CapturedWindow(
                query_id=query.id,
                query_text=query.text,
                low_confidence=False,
                candidates=tuple(_candidate(item.product_id) for item in judged[:10]),
                probe_distances=FLAT_PROBE,
            ),
        ),
    )

    with pytest.raises(ConfigurationError, match="probe"):
        rescore(capture, golden, BusinessWeights(availability=0.0))


def test_the_probe_and_its_rule_survive_a_round_trip_through_the_file() -> None:
    """Persisted means recoverable: a tuple of floats and three numbers, read back as they were."""
    capture = Capture(
        version=CAPTURE_VERSION,
        golden_set_version="1:test",
        fusion=_fingerprint(),
        windows=(
            CapturedWindow(
                query_id="q01",
                query_text="anillo de plata",
                low_confidence=False,
                candidates=(_candidate("00000000-0000-0000-0000-000000000001"),),
                probe_distances=PEAKED_PROBE,
            ),
        ),
        abstention=LIVE_RULE,
    )

    restored = Capture.from_json(capture.to_json())

    assert restored.windows[0].probe_distances == PEAKED_PROBE
    assert restored.abstention == LIVE_RULE


def test_a_capture_written_before_the_probe_still_loads() -> None:
    """The candidate set did not change, so those windows stay valid and must not be refused.

    That is why `CAPTURE_VERSION` did not move: the rule reads a different profile, it does not
    alter which candidates are retrieved, and the spec refuses a re-score only for the latter.
    """
    payload = _capture(_window(_candidate("00000000-0000-0000-0000-000000000001"))).to_json()
    stripped = json.loads(payload)
    del stripped["abstention"]
    for window in stripped["windows"]:
        del window["probe_distances"]

    restored = Capture.from_json(json.dumps(stripped))

    assert restored.windows[0].probe_distances is None
    assert restored.abstention is None
