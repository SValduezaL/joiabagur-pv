"""Point-of-sale scope, availability demotion, freshness and the ablation flag. C22.

Offline throughout: an injected search port and an injected embedding client. Nothing here
opens a socket and nothing reads schema `public`.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.retrieval import RetrievalMode, RetrievalRequest
from jbg_ai.retrieval.errors import InvalidPosIdError, RetrievalDependencyError
from jbg_ai.retrieval.orchestrator import retrieve_products
from jbg_ai.retrieval.projection import (
    ProjectionFreshness,
    age_seconds,
    parse_pos_id,
    resolve_scope,
)
from support.fake_embedding_client import FakeEmbeddingClient
from pydantic import ValidationError

from jbg_ai.retrieval.filters import (
    BusinessWeights,
    StructuralFilters,
    business_score,
    demote,
    demotion_rank,
)
from jbg_ai.retrieval.ports import SearchFilters
from support.fake_product_search import (
    DEFAULT_BUCKET,
    FakeAssignment,
    FakeIndexedRow,
    FakeProductSearch,
)
from support.settings import OTHER_POS_ID, TOKEN_POS_ID, TOKEN_TRACE_ID, build_settings

MINE = UUID(TOKEN_POS_ID)
THEIRS = UUID(OTHER_POS_ID)

A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
C = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
D = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
FAMILY = UUID("11111111-1111-1111-1111-111111111111")

DOC = "Tipo: anillo de plata. Materiales: plata."

PRINCIPAL = ServicePrincipal(
    user_id="u-1", role="Operator", trace_id=TOKEN_TRACE_ID, pos_id=TOKEN_POS_ID
)


def run(coro):
    return asyncio.run(coro)


def row(product_id: UUID, sku: str, distance: float, **kwargs) -> FakeIndexedRow:
    return FakeIndexedRow(
        product_id=product_id,
        sku=sku,
        distance=distance,
        materials=kwargs.pop("materials", ["plata"]),
        family_id=kwargs.pop("family_id", FAMILY),
        piece_type=kwargs.pop("piece_type", "anillo"),
        doc_text=kwargs.pop("doc_text", DOC),
        **kwargs,
    )


def request(**overrides) -> RetrievalRequest:
    values = {"query": "anillo de plata", "top_k": 5}
    values.update(overrides)
    return RetrievalRequest(**values)


def serve(search: FakeProductSearch, payload=None, principal=PRINCIPAL, **kwargs):
    return run(
        retrieve_products(
            payload if payload is not None else request(),
            principal,
            settings=kwargs.pop("settings", build_settings()),
            embed=kwargs.pop("embed", FakeEmbeddingClient()),
            search=search,
            freshness=kwargs.pop("freshness", ProjectionFreshness(ttl_seconds=0.0)),
            **kwargs,
        )
    )


def skus(response) -> list[str]:
    return [item.sku for item in response.results]


# --------------------------------------------------------------------------- the claim


def test_a_malformed_pos_id_is_rejected() -> None:
    with pytest.raises(InvalidPosIdError):
        parse_pos_id("POS-B")


@pytest.mark.parametrize(
    "claim",
    # `*` and `all` are named by the specification, which requires that a wildcard stay
    # impossible: they are values like any other, they are not UUIDs, and they are refused. The
    # only shape that widens a search is the claim not being there at all.
    ["", "   ", "POS-B", "not-a-uuid", "42", "*", "all", "ALL", "%"],
)
def test_no_claim_shape_short_of_a_uuid_is_accepted(claim: str) -> None:
    """Every VALUE that is not a UUID is refused, and an empty string is a value.

    `None` left this list with C40 and moved to the test below. The rule it used to encode —
    anything short of a UUID is a mis-issued token — still holds for everything that *is* a
    value; what changed is that the claim can now legitimately not be there at all.
    """
    with pytest.raises(InvalidPosIdError):
        parse_pos_id(claim)


def test_an_omitted_claim_is_the_every_shop_scope_and_not_a_rejection() -> None:
    """C40: absence is a scope, and it is the only shape of it.

    The reversal is narrow on purpose. `None` means the key was not in the payload — the auth
    layer already refuses a present-but-empty one — so the only way to reach this branch is a
    token deliberately issued without a shop. Everything else on the line above still raises,
    which is what keeps a broken token from being answered with the whole estate.
    """
    assert parse_pos_id(None) is None


def test_a_malformed_claim_never_produces_an_unscoped_search() -> None:
    """The failure mode this guards is silent: a broken token answered with everything."""
    search = FakeProductSearch([row(A, "S1", 0.1)])
    broken = ServicePrincipal(
        user_id="u-1", role="Operator", trace_id=TOKEN_TRACE_ID, pos_id="POS-B"
    )

    with pytest.raises(InvalidPosIdError):
        serve(search, principal=broken)

    assert search.search_calls == [], "no branch may run before the claim is read"
    assert search.lexical_calls == []


# --------------------------------------------------------------------------- the scope


def test_candidates_come_only_from_the_assortment() -> None:
    search = FakeProductSearch(
        [row(A, "MINE-1", 0.1), row(B, "THEIRS-1", 0.05), row(C, "MINE-2", 0.2)],
        assignments=[
            FakeAssignment(MINE, A),
            FakeAssignment(MINE, C),
            FakeAssignment(THEIRS, B),
        ],
    )

    response = serve(search)

    assert sorted(skus(response)) == ["MINE-1", "MINE-2"]
    assert "THEIRS-1" not in skus(response), "a nearer product of another shop stays out"


def test_a_soft_deleted_assignment_is_out_of_scope() -> None:
    """The row survives in the projection; it just stops being a candidate."""
    search = FakeProductSearch(
        [row(A, "CARRIED", 0.2), row(B, "DROPPED", 0.1)],
        assignments=[
            FakeAssignment(MINE, A),
            FakeAssignment(MINE, B, qty_bucket="0", is_assigned_hint=False),
        ],
    )

    response = serve(search)

    assert skus(response) == ["CARRIED"]


def test_the_scope_is_applied_to_every_branch() -> None:
    search = FakeProductSearch(
        [row(A, "MINE-1", 0.1)], assignments=[FakeAssignment(MINE, A)]
    )

    serve(search)

    assert search.search_calls[0]["pos_id"] == MINE
    assert [call["pos_id"] for call in search.lexical_calls] == [MINE, MINE]


def test_the_scope_comes_from_the_token_and_never_from_the_body() -> None:
    search = FakeProductSearch(
        [row(A, "MINE-1", 0.1)], assignments=[FakeAssignment(MINE, A)]
    )

    serve(search, request(pos_id=OTHER_POS_ID))

    assert search.search_calls[0]["pos_id"] == MINE


def test_the_scoped_branch_returns_its_full_depth() -> None:
    """A small assortment must fill the window it can fill, not be truncated below it.

    The failure this pins has no error of its own: an approximate index scan asked for 60
    neighbours returns what its search list happened to hold and the filter discards the
    rest, so the branch quietly comes back short. Here the scope is established first, so
    the depth is honoured by construction.
    """
    rows = [row(UUID(int=index + 1), f"MINE-{index}", 0.1) for index in range(40)]
    search = FakeProductSearch(
        rows + [row(UUID(int=900), "THEIRS", 0.01)],
        assignments=[FakeAssignment(MINE, item.product_id) for item in rows],
    )

    serve(search, request(mode=RetrievalMode.VECTOR, top_k=50))

    assert len(search.search_calls) == 1
    assert search.search_calls[0]["depth"] == 60
    hits = run(
        search.search(
            [0.1],
            threshold=0.65,
            depth=60,
            filters=search.search_calls[0]["filters"],
            model_version_key="k",
            model_id="m",
            pos_id=MINE,
        )
    )
    assert len(hits) == 40, "every assigned candidate within the depth is returned"


# --------------------------------------------------------------------------- demotion


def test_out_of_stock_product_is_penalised_not_removed() -> None:
    search = FakeProductSearch(
        [row(A, "EMPTY", 0.10), row(B, "STOCKED", 0.11)],
        assignments=[
            FakeAssignment(MINE, A, qty_bucket="0"),
            FakeAssignment(MINE, B, qty_bucket="3+"),
        ],
    )

    response = serve(search)

    assert set(skus(response)) == {"EMPTY", "STOCKED"}, "demoted, never removed"
    assert skus(response).index("STOCKED") < skus(response).index("EMPTY")


def test_a_typed_constraint_outranks_the_stock_signal() -> None:
    """What the operator typed beats a signal they did not ask about."""
    search = FakeProductSearch(
        [
            row(A, "CHEAP-EMPTY", 0.20, price=40.0),
            row(B, "DEAR-STOCKED", 0.10, price=900.0),
        ],
        assignments=[
            FakeAssignment(MINE, A, qty_bucket="0"),
            FakeAssignment(MINE, B, qty_bucket="3+"),
        ],
    )

    response = serve(search, request(query="anillo de plata por menos de 80 euros"))

    assert skus(response)[0] == "CHEAP-EMPTY", "the ceiling block outranks availability"


def test_the_two_non_zero_buckets_are_not_ordered_against_each_other() -> None:
    search = FakeProductSearch(
        [row(A, "FEW", 0.10), row(B, "MANY", 0.11)],
        assignments=[
            FakeAssignment(MINE, A, qty_bucket="1-2"),
            FakeAssignment(MINE, B, qty_bucket="3+"),
        ],
    )

    response = serve(search)

    assert skus(response) == ["FEW", "MANY"], "the fused order survives untouched"


def test_no_bucket_reaches_the_response() -> None:
    search = FakeProductSearch(
        [row(A, "EMPTY", 0.1)], assignments=[FakeAssignment(MINE, A, qty_bucket="0")]
    )

    payload = serve(search).model_dump()

    assert "qty_bucket" not in str(payload)
    assert "3+" not in str(payload)


# --------------------------------------------------------------------------- freshness


def test_freshness_reflects_the_last_synchronisation_not_the_last_change() -> None:
    """The trap: the feed is incremental, so the rows are old by design."""
    search = FakeProductSearch(
        [row(A, "S1", 0.1)],
        assignments=[FakeAssignment(MINE, A)],
        synced_at=datetime.now(tz=UTC) - timedelta(seconds=30),
    )

    response = serve(search)

    assert response.projection_age_seconds is not None
    assert 20 < response.projection_age_seconds < 120
    assert search.synced_at_calls == 1, "one checkpoint read, not one per branch"


def test_the_age_is_read_through_a_cache() -> None:
    search = FakeProductSearch(
        [row(A, "S1", 0.1)], assignments=[FakeAssignment(MINE, A)]
    )
    shared = ProjectionFreshness(ttl_seconds=60.0, clock=lambda: 0.0)

    serve(search, freshness=shared)
    serve(search, freshness=shared)

    assert search.synced_at_calls == 1, "the pool is capped at five; do not spend it twice"


def test_the_age_is_absent_when_the_prefilter_did_not_run() -> None:
    search = FakeProductSearch(
        [row(A, "S1", 0.1)], assignments=[FakeAssignment(MINE, A)]
    )

    response = serve(search, pos_prefilter=False)

    assert response.projection_age_seconds is None


def test_a_never_synchronised_checkpoint_has_no_age() -> None:
    assert age_seconds(None) is None


def test_a_naive_timestamp_is_read_as_utc() -> None:
    """PostgreSQL hands back an aware value; a driver or a fake may not."""
    naive = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(seconds=10)

    computed = age_seconds(naive)

    assert computed is not None and 5 < computed < 60


# --------------------------------------------------------------------------- guards


def test_an_unsynchronised_projection_is_503_and_not_an_abstention() -> None:
    """A 200 with an empty list is indistinguishable from a legitimate abstention."""
    search = FakeProductSearch([row(A, "S1", 0.1)], assignments=[])

    with pytest.raises(RetrievalDependencyError, match="projection"):
        serve(search)


def test_the_empty_guard_names_the_projection_as_the_cause() -> None:
    search = FakeProductSearch([row(A, "S1", 0.1)], assignments=[])

    with pytest.raises(RetrievalDependencyError) as caught:
        serve(search)

    assert "projection" in str(caught.value)
    assert "refusing to abstain" in str(caught.value)


def test_a_point_of_sale_carrying_nothing_is_not_confused_with_a_query_that_matched_nothing() -> None:
    empty_scope = FakeProductSearch([row(A, "S1", 0.1)], assignments=[])
    matched_nothing = FakeProductSearch(
        [row(A, "S1", 0.9, doc_text="Tipo: broche.")],
        assignments=[FakeAssignment(MINE, A)],
    )

    with pytest.raises(RetrievalDependencyError):
        serve(empty_scope)

    response = serve(matched_nothing, request(mode=RetrievalMode.VECTOR))
    assert response.results == [], "an honest abstention is still a 200"
    assert response.low_confidence is True


def test_a_stale_projection_stops_filtering_instead_of_hiding_products() -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(B, "THEIRS", 0.1)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(THEIRS, B)],
        synced_at=datetime.now(tz=UTC) - timedelta(hours=5),
    )

    response = serve(search)

    assert search.search_calls[0]["pos_id"] is None, "the scope is dropped, not narrowed"
    assert set(skus(response)) == {"MINE", "THEIRS"}
    assert response.projection_age_seconds is not None
    assert response.projection_age_seconds > 3600


def test_a_stale_projection_logs_the_degradation(
    caplog: pytest.LogCaptureFixture,
) -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2)],
        assignments=[FakeAssignment(MINE, A)],
        synced_at=datetime.now(tz=UTC) - timedelta(hours=5),
    )

    with caplog.at_level(logging.WARNING, logger="jbg_ai.retrieval.orchestrator"):
        serve(search)

    degraded = [r for r in caplog.records if "degraded=unscoped" in r.getMessage()]
    assert degraded, "a silent degradation is the failure this change exists to avoid"
    assert TOKEN_TRACE_ID in degraded[0].getMessage()


def test_a_projection_that_was_never_synchronised_degrades_rather_than_scoping() -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(B, "THEIRS", 0.1)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(THEIRS, B)],
        never_synchronised=True,
    )

    response = serve(search)

    assert search.search_calls[0]["pos_id"] is None
    assert response.projection_age_seconds is None


def test_a_fresh_projection_applies_the_filter() -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(B, "THEIRS", 0.1)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(THEIRS, B)],
        synced_at=datetime.now(tz=UTC) - timedelta(seconds=5),
    )

    response = serve(search)

    assert search.search_calls[0]["pos_id"] == MINE
    assert skus(response) == ["MINE"]


def test_the_ceiling_is_configurable_per_call() -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(B, "THEIRS", 0.1)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(THEIRS, B)],
        synced_at=datetime.now(tz=UTC) - timedelta(seconds=120),
    )

    serve(search, projection_max_age_seconds=60)
    assert search.search_calls[0]["pos_id"] is None

    serve(search, projection_max_age_seconds=3600)
    assert search.search_calls[1]["pos_id"] == MINE


# --------------------------------------------------------------------------- the flag


def test_disabling_the_prefilter_restores_the_previous_behaviour() -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(B, "THEIRS", 0.1)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(THEIRS, B)],
    )

    response = serve(search, pos_prefilter=False)

    assert search.search_calls[0]["pos_id"] is None
    assert [call["pos_id"] for call in search.lexical_calls] == [None, None]
    assert set(skus(response)) == {"MINE", "THEIRS"}
    assert search.scope_calls == [], "a disabled prefilter must not even count the scope"


def test_a_sweep_overrides_the_default_without_restarting() -> None:
    settings = build_settings()
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(B, "THEIRS", 0.1)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(THEIRS, B)],
    )

    scoped = serve(search, settings=settings, pos_prefilter=True)
    unscoped = serve(search, settings=settings, pos_prefilter=False)

    assert skus(scoped) == ["MINE"]
    assert set(skus(unscoped)) == {"MINE", "THEIRS"}
    assert settings.jpv_pos_prefilter_enabled is True, "the default was not mutated"


def test_the_flag_is_not_part_of_the_request_contract() -> None:
    fields = set(RetrievalRequest.model_fields)

    assert "pos_prefilter" not in fields
    assert "projection_max_age_seconds" not in fields
    assert fields == {"query", "top_k", "filters", "mode", "pos_id"}


# --------------------------------------------------------------------------- logging


def test_the_projection_stage_reports_what_the_scope_admitted(
    caplog: pytest.LogCaptureFixture,
) -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2), row(C, "MINE-2", 0.3)],
        assignments=[FakeAssignment(MINE, A), FakeAssignment(MINE, C)],
    )

    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        serve(search)

    entries = [r.getMessage() for r in caplog.records if "stage=projection" in r.getMessage()]
    assert entries
    assert TOKEN_TRACE_ID in entries[0]
    assert "scope_size=2" in entries[0]
    assert "applied=True" in entries[0]
    assert "age_seconds=" in entries[0]


def test_the_search_stage_reports_the_scoped_cardinality(
    caplog: pytest.LogCaptureFixture,
) -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2)], assignments=[FakeAssignment(MINE, A)]
    )

    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        serve(search, request(mode=RetrievalMode.VECTOR))

    entries = [r.getMessage() for r in caplog.records if "stage=search" in r.getMessage()]
    assert entries
    assert "scoped=True" in entries[0]
    assert "candidates=1" in entries[0]
    assert "truncated=True" in entries[0], "a branch below its depth must be visible"


def test_no_vector_reaches_the_logs(caplog: pytest.LogCaptureFixture) -> None:
    search = FakeProductSearch(
        [row(A, "MINE", 0.2)], assignments=[FakeAssignment(MINE, A)]
    )

    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        serve(search)

    for record in caplog.records:
        message = record.getMessage()
        assert "[0." not in message
        assert "embedding=[" not in message


# ------------------------------------------------------------------- sales, unread


def test_the_sales_figures_are_persisted_and_read_but_never_order_anything() -> None:
    """Three figures the drain writes. One is read for diagnostics. NONE orders anything.

    This replaces C22's guard, whose promise was that no sales figure reached the pipeline at
    all. `sales_30d` now does reach it — it travels on every hit and is persisted in the
    sweep's captured windows, so the report can publish its distribution and C26 has an input
    — so the guarantee moves to where it can still be structural: **the protocol the ordering
    reads does not carry the field.** `demote` cannot consume it even by accident, because it
    cannot see it.

    Why it orders nothing is measured, not cautious. As the strict tiebreak its requirement
    described, it decided **0 pairs of the top five across all 48 queries**: exact score ties
    are common — 662 pairs, 35 % of candidates — but none inside the reported window pitted a
    seller against a non-seller. As a component of the ordering key it was no tiebreak at all,
    inverting 11.067 pairs of which 71,2 % sat more than ten positions apart, and 6 of the 22
    candidates it lifted into the top five displaced a better-graded document.

    `sales_90d` and `last_sale_at` never reach the pipeline at all. `last_sale_at` is the
    tempting one — 4.021 non-null rows against `sales_30d`'s 1.424 — as an exponential decay
    whose "today" would be a wall clock; the world of C10 ends on 2026-08-23, so wall-clock
    decay takes the signal to zero and makes the ranking irreproducible by design.
    """
    import inspect

    from jbg_ai.retrieval import filters, fusion, orchestrator
    from jbg_ai.retrieval.filters import Constrained
    from jbg_ai.retrieval.ports import LexicalHit, SearchHit

    # It travels: the hits carry it, so a diagnostic and a capture can read it.
    for hit_type in (SearchHit, LexicalHit):
        fields = set(hit_type.__dataclass_fields__)
        assert "sales_30d" in fields, f"{hit_type} must carry the signal for diagnostics"
        assert "sales_90d" not in fields, hit_type
        assert "last_sale_at" not in fields, hit_type

    # It orders nothing: the protocol the ordering reads does not have the field.
    ordering_fields = set(Constrained.__annotations__)
    assert "sales_30d" not in ordering_fields, "the ordering must not be able to see it"
    assert not any(name.startswith("sales_") for name in ordering_fields)
    assert "last_sale_at" not in ordering_fields

    # And the ordering module never names it.
    assert "sales_30d" not in inspect.getsource(filters), "filters.py must not mention it"

    for module in (orchestrator, filters, fusion):
        source = inspect.getsource(module)
        assert "sales_90d" not in source, module.__name__
        assert "last_sale_at" not in source, module.__name__
        # And no ordering rule may reach for a wall clock.
        assert "date.today" not in source, module.__name__
        assert "datetime.now" not in source, module.__name__


def test_sales_figures_do_not_change_the_order() -> None:
    """Two candidates the fusion ranks equally stay in fused order whatever they sold."""
    search = FakeProductSearch(
        [row(A, "SOLD-A-LOT", 0.10), row(B, "SOLD-NOTHING", 0.11)],
        assignments=[
            FakeAssignment(MINE, A, qty_bucket="3+"),
            FakeAssignment(MINE, B, qty_bucket="3+"),
        ],
    )

    response = serve(search)

    assert skus(response) == ["SOLD-A-LOT", "SOLD-NOTHING"], "distance decides, not rotation"


# --------------------------------------------------------------------------- unit


def test_resolve_scope_skips_every_query_when_disabled() -> None:
    search = FakeProductSearch([row(A, "S1", 0.1)], assignments=[])

    scope = run(
        resolve_scope(
            MINE,
            search=search,
            enabled=False,
            max_age_seconds=3600,
            freshness=ProjectionFreshness(ttl_seconds=0.0),
        )
    )

    assert scope.pos_id is None
    assert scope.applied is False
    assert scope.reported_age is None
    assert search.scope_calls == []
    assert search.synced_at_calls == 0


# --------------------------------------------------------------------------------------
# C25 - the reading scope is separate from the restricting one.
# --------------------------------------------------------------------------------------

def test_signal_join_never_restricts_the_candidate_set() -> None:
    """A LEFT JOIN that reads, against an INNER JOIN that restricts. C25 D4.

    This is the whole point of splitting the parameter: it lets the reordering by
    availability be measured WITHOUT paying the recall cost of the prefilter, which is the
    confusion C22 declined to introduce and declared unmeasured. If the reading scope removed
    even one candidate, the `v3` row would be measuring two changes at once.
    """
    rows = [row(A, "carried", 0.10), row(B, "not-carried", 0.11), row(C, "also-not", 0.12)]
    # The point of sale carries exactly one of the three.
    assignments = [FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="3+", sales_30d=7)]

    without_anything = serve(FakeProductSearch(list(rows)), pos_prefilter=False)
    with_signal = serve(
        FakeProductSearch(list(rows), assignments=list(assignments)),
        pos_prefilter=False,
        signal_pos_id=MINE,
    )

    assert [item.sku for item in with_signal.results] == [
        item.sku for item in without_anything.results
    ], "reading the signal must preserve every candidate, and their order"

    # And the signals really were read for the candidate the point of sale carries.
    search = FakeProductSearch(list(rows), assignments=list(assignments))
    serve(search, pos_prefilter=False, signal_pos_id=MINE)
    hits = run(
        search.search(
            [0.0],
            threshold=0.65,
            depth=60,
            filters=SearchFilters(),
            model_version_key="m:1",
            model_id="m",
            signal_pos_id=MINE,
        )
    )
    by_sku = {hit.sku: hit for hit in hits}
    assert len(by_sku) == 3, "the reading scope dropped a candidate"
    assert by_sku["carried"].qty_bucket == "3+"
    assert by_sku["carried"].sales_30d == 7


def test_absent_projection_row_reports_absent_signals_not_zero() -> None:
    """Absence is not evidence of zero stock, and it is not evidence of zero sales either.

    `None` and `0` are different world states: "this point of sale does not carry it" against
    "it is carried here and sold none". Collapsing them would make the availability demotion
    fire on every product outside the assortment, turning assortment coverage into a
    relevance penalty - exactly the conflation C22 kept apart.
    """
    rows = [row(A, "carried-sold-none", 0.10), row(B, "not-carried", 0.11)]
    assignments = [
        FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="0", sales_30d=0),
    ]
    search = FakeProductSearch(rows, assignments=assignments)

    hits = run(
        search.search(
            [0.0],
            threshold=0.65,
            depth=60,
            filters=SearchFilters(),
            model_version_key="m:1",
            model_id="m",
            signal_pos_id=MINE,
        )
    )
    by_sku = {hit.sku: hit for hit in hits}

    carried = by_sku["carried-sold-none"]
    assert carried.qty_bucket == "0", "a real zero bucket"
    assert carried.sales_30d == 0, "a real zero sales window"

    absent = by_sku["not-carried"]
    assert absent.qty_bucket is None, "absence must not be reported as a bucket"
    assert absent.sales_30d is None, "absence must not be reported as zero sales"


def test_no_reading_scope_leaves_every_signal_absent() -> None:
    """With neither scope supplied, nothing is read and nothing is invented."""
    search = FakeProductSearch([row(A, "anything", 0.10)])
    hits = run(
        search.search(
            [0.0],
            threshold=0.65,
            depth=60,
            filters=SearchFilters(),
            model_version_key="m:1",
            model_id="m",
        )
    )
    assert hits[0].qty_bucket is None
    assert hits[0].sales_30d is None


def test_scope_join_still_restricts_when_supplied() -> None:
    """C22's guarantee, intact. The new parameter must not have weakened the old one."""
    rows = [row(A, "carried", 0.10), row(B, "not-carried", 0.11)]
    assignments = [FakeAssignment(pos_id=MINE, product_id=A)]
    search = FakeProductSearch(rows, assignments=assignments)

    response = serve(search, pos_prefilter=True)

    assert [item.sku for item in response.results] == ["carried"], (
        "the restricting scope must still remove what the point of sale does not carry"
    )
    # And a restricting scope reads as well: in SQL the rows are joined already.
    hits = run(
        search.search(
            [0.0],
            threshold=0.65,
            depth=60,
            filters=SearchFilters(),
            model_version_key="m:1",
            model_id="m",
            pos_id=MINE,
        )
    )
    assert [hit.sku for hit in hits] == ["carried"]
    assert hits[0].qty_bucket == DEFAULT_BUCKET


def test_the_two_scopes_are_independent_parameters_not_one_flag() -> None:
    """Four combinations, and each one is a different question. C25 D4.

    The flag they replace did two things at once, so `scoped=False` meant BOTH "do not
    restrict" and "do not read" - which is why the availability demotion C22 shipped never
    fired once in the 192 rows of the published evaluation run.
    """
    from jbg_ai.retrieval.search import compile_search_sql

    neither = compile_search_sql(SearchFilters())
    reads_only = compile_search_sql(SearchFilters(), reads=True)
    restricts_only = compile_search_sql(SearchFilters(), restricts=True)

    assert "scope" not in neither and "NULL AS qty_bucket" in neither
    assert "NULL AS sales_30d" in neither

    assert "LEFT JOIN scope s" in reads_only, "reading must not restrict"
    assert "s.qty_bucket" in reads_only and "s.sales_30d" in reads_only

    assert "LEFT JOIN scope s" not in restricts_only, "restricting must restrict"
    assert "JOIN scope s" in restricts_only
    assert "s.qty_bucket" in restricts_only and "s.sales_30d" in restricts_only


class _Candidate:
    """The smallest thing the business score can read."""

    def __init__(self, *, price=None, size_label=None, materials=None,
                 qty_bucket=None, sales_30d=None):
        self.price = price
        self.size_label = size_label
        self.materials = materials or []
        self.qty_bucket = qty_bucket
        self.sales_30d = sales_30d



# --------------------------------------------------------------------------------------
# C25 - the business score orders only the tail block.
# --------------------------------------------------------------------------------------

LIVE_WEIGHTS = BusinessWeights(availability=1.0)


def test_typed_constraint_outranks_the_business_score() -> None:
    """What the operator expressed keeps strict precedence over a signal they did not ask for.

    This is the property the lexicographic shape exists to guarantee, and the reason the
    business weights live in ONE term at the end of the key rather than summed with the rest:
    a weighted sum of everything would let enough evidence of stock topple an explicit price
    ceiling, and then nobody could say why a document came third.
    """
    filters = StructuralFilters(price_ceiling=80.0)
    # The worst business score the scale allows, inside the ceiling.
    within = _Candidate(price=40.0, qty_bucket="0", sales_30d=0)
    # The best business score the scale allows, outside it.
    over = _Candidate(price=900.0, qty_bucket="3+", sales_30d=999)

    ordered, _ = demote([over, within], filters, LIVE_WEIGHTS)

    assert ordered == (within, over), "the ceiling must decide before the business score"
    assert demotion_rank(within, filters, LIVE_WEIGHTS) < demotion_rank(
        over, filters, LIVE_WEIGHTS
    )


def test_out_of_stock_product_ranks_below_equivalent_in_stock() -> None:
    """Unscoped, with the signal arriving through the reading scope. C25 D4 + D9.

    Unscoped on purpose: this is the configuration the evaluation runs in, and the whole
    reason the signal was split from the scope. Under C22's single flag this ordering could
    not be produced at all without also restricting the candidate set.
    """
    # A wins the fusion tiebreak (lower UUID), so A must be the EXHAUSTED one: otherwise
    # the fusion already orders in-stock first and the assertion passes without the signal
    # doing anything at all.
    rows = [row(A, "out-of-stock", 0.11), row(B, "in-stock", 0.10)]
    assignments = [
        FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="0"),
        FakeAssignment(pos_id=MINE, product_id=B, qty_bucket="3+"),
    ]

    # `pos_prefilter=False`: the candidate set is the whole catalogue, as in the evaluation.
    response = serve(
        FakeProductSearch(rows, assignments=assignments),
        pos_prefilter=False,
        signal_pos_id=MINE,
    )

    # The fusion on its own puts `out-of-stock` first, so this ordering is the signal's work
    # and not a coincidence of the tiebreak.
    assert skus(serve(FakeProductSearch(list(rows)), pos_prefilter=False)) == [
        "out-of-stock",
        "in-stock",
    ], "the premise: without the signal the exhausted candidate leads"
    assert skus(response) == ["in-stock", "out-of-stock"], (
        "the zero-stock candidate must be demoted below its in-stock peer"
    )
    assert len(response.results) == 2, "demoted, never removed"


def test_rotation_does_not_order_anything() -> None:
    """The withdrawn term, kept as a test so the refutation cannot be undone by accident.

    Two candidates the availability signal ranks equally, one of which sold and one of which
    did not, keep the order the fusion gave them. The sentence that justified a tiebreak is
    still true at a counter; what the measurement established is that this retriever does not
    produce the situation the sentence describes - in the top five, across all 48 queries,
    there was not one tied pair for rotation to decide.
    """
    filters = StructuralFilters()
    sold = _Candidate(qty_bucket="3+", sales_30d=6)
    unsold = _Candidate(qty_bucket="3+", sales_30d=0)

    assert business_score(sold, LIVE_WEIGHTS) == business_score(unsold, LIVE_WEIGHTS)
    ordered, _ = demote([unsold, sold], filters, LIVE_WEIGHTS)
    assert ordered == (unsold, sold), "the fused order survives; the sales window decides nothing"


def test_availability_is_the_only_business_weight() -> None:
    """One weight, and its SIGN is what the calibration decided rather than its value.

    With a single binary term the score takes two values, so every positive weight produces
    the same ranking. The weight stays configurable because zero is the rollback, but the
    report says plainly that 1.0 is a declared unit and not a fitted figure.
    """
    from jbg_ai.config.settings import BUSINESS_DEFAULTS, Settings

    assert list(BUSINESS_DEFAULTS) == ["jpv_business_weight_availability"]
    assert not hasattr(BusinessWeights(), "rotation")
    settings = Settings(app_env="local", service_version="c25", jwt_secret="x" * 32)
    assert not any("rotation" in name for name in type(settings).model_fields)

    exhausted = _Candidate(qty_bucket="0", sales_30d=6)
    stocked = _Candidate(qty_bucket="3+", sales_30d=0)
    orders = {
        tuple(
            item.qty_bucket
            for item in demote(
                [exhausted, stocked], StructuralFilters(), BusinessWeights(availability=w)
            )[0]
        )
        for w in (0.25, 0.5, 1.0, 2.0, 100.0)
    }
    assert orders == {("3+", "0")}, "every positive weight gives the same ranking"


def test_weights_load_from_config_not_hardcoded() -> None:
    """No weight value is written into the ordering module, and both travel per call."""
    import inspect

    from jbg_ai.config.settings import BUSINESS_DEFAULTS
    from jbg_ai.retrieval import filters as filters_module

    source = inspect.getsource(filters_module)
    for value in BUSINESS_DEFAULTS.values():
        assert f"= {value}" not in source, f"{value} is written into the ordering module"

    settings = build_settings()
    assert settings.jpv_business_weight_availability == BUSINESS_DEFAULTS[
        "jpv_business_weight_availability"
    ]

    # Two configurations in one process, and neither mutates the settings object.
    # A wins the fusion tiebreak (lower UUID), so A must be the EXHAUSTED one: otherwise
    # the fusion already orders in-stock first and the assertion passes without the signal
    # doing anything at all.
    rows = [row(A, "out-of-stock", 0.11), row(B, "in-stock", 0.10)]
    assignments = [
        FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="0"),
        FakeAssignment(pos_id=MINE, product_id=B, qty_bucket="3+"),
    ]
    weighted = serve(
        FakeProductSearch(rows, assignments=assignments),
        settings=settings,
        pos_prefilter=False,
        signal_pos_id=MINE,
    )
    unweighted = serve(
        FakeProductSearch(rows, assignments=assignments),
        settings=settings,
        pos_prefilter=False,
        signal_pos_id=MINE,
        business_weight_availability=0.0,
    )
    assert skus(weighted) == ["in-stock", "out-of-stock"]
    assert skus(unweighted) == ["out-of-stock", "in-stock"]
    assert settings.jpv_business_weight_availability == 1.0, "settings were mutated"


def test_zero_weights_restore_the_previous_ordering() -> None:
    """The rollback: zero weights reproduce fusion plus the typed blocks, exactly."""
    # A wins the fusion tiebreak (lower UUID), so A must be the EXHAUSTED one: otherwise
    # the fusion already orders in-stock first and the assertion passes without the signal
    # doing anything at all.
    rows = [row(A, "out-of-stock", 0.11), row(B, "in-stock", 0.10)]
    assignments = [
        FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="0"),
        FakeAssignment(pos_id=MINE, product_id=B, qty_bucket="3+"),
    ]

    zeroed = serve(
        FakeProductSearch(rows, assignments=assignments),
        pos_prefilter=False,
        signal_pos_id=MINE,
        business_weight_availability=0.0,
    )
    no_signal_at_all = serve(FakeProductSearch(list(rows)), pos_prefilter=False)

    assert skus(zeroed) == skus(no_signal_at_all)
    # And at the unit level the key collapses to the typed blocks alone.
    zero = BusinessWeights()
    assert demotion_rank(_Candidate(qty_bucket="0", sales_30d=0), StructuralFilters(), zero) == (
        demotion_rank(_Candidate(qty_bucket="3+", sales_30d=9), StructuralFilters(), zero)
    )


def test_no_stock_quantity_reaches_the_response() -> None:
    """The bucket is a bucket. .NET owns the number, and a number here would start one."""
    rows = [row(A, "carried", 0.10)]
    assignments = [FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="1-2", sales_30d=7)]

    response = serve(
        FakeProductSearch(rows, assignments=assignments),
        pos_prefilter=False,
        signal_pos_id=MINE,
    )

    payload = response.model_dump_json()
    for forbidden in ("qty_bucket", "sales_30d", "1-2", "stock", "quantity"):
        assert forbidden not in payload, f"{forbidden} reached the response"
    for item in response.results:
        fields = set(type(item).model_fields)
        assert not any("stock" in name or "qty" in name or "sales" in name for name in fields)


def test_sales_window_is_read_against_the_row_reference_instant() -> None:
    """Never against the wall clock, so the same configuration orders the same on any day.

    `sales_30d` is the drain's own figure, already counted against the `computed_as_of`
    recorded on that row. The ranking reads the stored number and computes no window of its
    own, which is what makes this structural: there is no clock in the ordering path to be
    wrong. The world of C10 ends on 2026-08-23, so a wall-clock window would take every
    figure to zero and make the ranking irreproducible by design.
    """
    import inspect

    from jbg_ai.retrieval import filters as filters_module
    from jbg_ai.retrieval import orchestrator as orchestrator_module

    for module in (filters_module, orchestrator_module):
        source = inspect.getsource(module)
        for clock in ("date.today", "datetime.now", "utcnow", "time.time()"):
            assert clock not in source, f"{module.__name__} reaches for a wall clock: {clock}"

    # And the value the ordering reads is the stored one, unmodified.
    rows = [row(A, "sold", 0.10), row(B, "unsold", 0.11)]
    assignments = [
        FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="3+", sales_30d=4),
        FakeAssignment(pos_id=MINE, product_id=B, qty_bucket="3+", sales_30d=0),
    ]
    search = FakeProductSearch(rows, assignments=assignments)
    hits = run(
        search.search(
            [0.0],
            threshold=0.65,
            depth=60,
            filters=SearchFilters(),
            model_version_key="m:1",
            model_id="m",
            signal_pos_id=MINE,
        )
    )
    assert {hit.sku: hit.sales_30d for hit in hits} == {"sold": 4, "unsold": 0}


def test_the_signals_stage_logs_its_weights_without_quantities_or_vectors(caplog) -> None:
    """`stage=filters` cannot report this: it conflates a typed ceiling with a stock figure."""
    rows = [row(A, "in-stock", 0.11), row(B, "out-of-stock", 0.10)]
    assignments = [
        FakeAssignment(pos_id=MINE, product_id=A, qty_bucket="3+", sales_30d=5),
        FakeAssignment(pos_id=MINE, product_id=B, qty_bucket="0", sales_30d=0),
    ]

    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        serve(
            FakeProductSearch(rows, assignments=assignments),
            pos_prefilter=False,
            signal_pos_id=MINE,
        )

    entry = next(m for m in caplog.messages if "stage=signals" in m)
    assert "w_availability=1.0" in entry
    assert "w_rotation" not in entry, "the withdrawn weight must not be logged"
    assert "reading_scope=True" in entry
    assert "out_of_stock=1" in entry
    # A diagnostic count, not an ordering input: the report publishes the distribution.
    assert "with_sales_signal=1" in entry
    assert TOKEN_TRACE_ID in entry
    # No exact quantity and no vector.
    assert "sales_30d=5" not in entry
    assert "0.11" not in entry and "[" not in entry


def test_an_absent_signal_never_ranks_below_a_read_one() -> None:
    """The rule the first implementation broke, and the measurement caught. C25.

    A bonus for having sold ranks a candidate whose projection row was never read BELOW one
    that sold, which is exactly "treating absence as zero sales". Measured on a reading scope
    covering 416 of 1.168 products, that form cost 0,244 of pure relevance: it sorted the
    assortment above everything outside it instead of sorting the exhausted below the
    available. Both terms subtract, so absence is neutral by construction.
    """
    absent = _Candidate(qty_bucket=None, sales_30d=None)
    carried_and_sold = _Candidate(qty_bucket="3+", sales_30d=9)
    carried_unsold = _Candidate(qty_bucket="3+", sales_30d=0)
    exhausted = _Candidate(qty_bucket="0", sales_30d=9)

    # Absence is never worse than the best news a read row can carry.
    assert business_score(absent, LIVE_WEIGHTS) >= business_score(
        carried_and_sold, LIVE_WEIGHTS
    )
    # And no score is ever positive: only bad news moves a candidate.
    for item in (absent, carried_and_sold, carried_unsold, exhausted):
        assert business_score(item, LIVE_WEIGHTS) <= 0.0
    # With rotation withdrawn the surviving asymmetry is gone too: a row that was read and
    # did not sell scores exactly what an unread one scores.
    assert business_score(carried_unsold, LIVE_WEIGHTS) == business_score(
        absent, LIVE_WEIGHTS
    )

    ordered, _ = demote(
        [exhausted, carried_unsold, absent, carried_and_sold],
        StructuralFilters(),
        LIVE_WEIGHTS,
    )
    # Only the exhausted candidate moves. Absent, carried-and-sold and carried-unsold all
    # score zero and keep the order the fusion gave them.
    assert ordered[-1] is exhausted
    assert [item for item in ordered[:3]] == [carried_unsold, absent, carried_and_sold]
