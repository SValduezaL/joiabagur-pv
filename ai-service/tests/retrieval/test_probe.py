"""The unfiltered abstention probe, and the two statements it must never confuse. C40.

Offline throughout: an injected search port and an injected embedding client, like the rest of
the retrieval tests. Nothing here opens a socket.

**Why the probe exists at all.** The abstention rule asks whether the catalogue can answer the
*query*, and a filter is a restriction rather than a description. Read over a filtered profile
the rule cannot fire when the filter is narrow — it needs `min_candidates` inside its band and a
narrow filter can never supply them — so the system would serve a handful of mediocre pieces and,
on the generative path, write prose praising them. That is the failure these tests pin down, and
the two statements it produces are what the first four of them measure.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.retrieval import RetrievalRequest
from jbg_ai.assist.constants import WARNING_FILTERS_TOO_NARROW
from jbg_ai.retrieval.orchestrator import retrieve_products
from support.fake_embedding_client import FakeEmbeddingClient
from support.fake_product_search import FakeIndexedRow, FakeProductSearch
from support.settings import TOKEN_POS_ID, TOKEN_TRACE_ID, build_settings

PRINCIPAL = ServicePrincipal(
    user_id="u-1", role="Operator", trace_id=TOKEN_TRACE_ID, pos_id=TOKEN_POS_ID
)

#: The live operating point, fixed by C25 against 20 out-of-domain and 43 answerable queries.
MIN_CANDIDATES = 15


def _run(coro):
    return asyncio.run(coro)


def _rows(distances, *, piece_type: str, material: str, start: int = 1):
    """Rows that answer the query, all of one type and one material so a filter can split them."""
    return [
        FakeIndexedRow(
            product_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
            sku=f"SKU{index:02d}",
            distance=distance,
            materials=[material],
            piece_type=piece_type,
            doc_text=f"Tipo: {piece_type} de {material}. Materiales: {material}.",
        )
        for index, distance in enumerate(distances, start=start)
    ]


#: Twenty rings of silver whose profile has a clear peak: the query IS answerable.
def _peaked_catalogue():
    return _rows(
        [0.21] + [0.44 + 0.01 * index for index in range(19)],
        piece_type="anillo",
        material="plata",
    )


#: Twenty rings of silver whose profile is flat: nothing in the catalogue stands out.
def _flat_catalogue():
    return _rows(
        [0.500 + 0.0005 * index for index in range(20)],
        piece_type="anillo",
        material="plata",
    )


def _serve(search, *, filters=None, **kwargs):
    return _run(
        retrieve_products(
            RetrievalRequest(
                query="anillo de plata",
                top_k=5,
                filters=filters or {},
            ),
            PRINCIPAL,
            settings=kwargs.pop("settings", build_settings()),
            embed=kwargs.pop("embed", FakeEmbeddingClient()),
            search=search,
            **kwargs,
        )
    )


# ------------------------------------------------------------------ how many statements run


def test_filtered_request_issues_two_statements() -> None:
    """The served one carries the filters; the probe carries none. Both, and in that order."""
    search = FakeProductSearch(_peaked_catalogue())

    _serve(search, filters={"category": "anillo"})

    assert len(search.search_calls) == 2
    assert search.search_calls[0]["filters"].category == "anillo"
    assert search.search_calls[1]["filters"].is_empty, (
        "the probe judges the query, so no filter of the operator's may narrow it"
    )


def test_unfiltered_request_issues_one_statement() -> None:
    """With nothing narrowing, the served profile already IS the unfiltered one.

    A probe here would ask the same question twice and pay a second scan for an answer the
    first statement already gave.
    """
    search = FakeProductSearch(_peaked_catalogue())

    _serve(search)

    assert len(search.search_calls) == 1


def test_probe_costs_no_provider_call() -> None:
    """The vector is the one already computed, so the provider is called exactly once.

    This is the property that makes the probe affordable: the extra cost is a scan of an index
    the filters module already measured as saving no time at this catalogue size, and never a
    second round trip to the embedding provider.
    """
    search = FakeProductSearch(_peaked_catalogue())
    embed = FakeEmbeddingClient()

    _serve(search, filters={"category": "anillo"}, embed=embed)

    assert embed.call_count == 1

    unfiltered = FakeEmbeddingClient()
    _serve(FakeProductSearch(_peaked_catalogue()), embed=unfiltered)
    assert embed.call_count == unfiltered.call_count, (
        "a filtered request must cost the provider exactly what an unfiltered one costs"
    )


def test_probe_never_reaches_the_response() -> None:
    """Candidates the filter excludes stay excluded, and the order is the filtered one's.

    The probe returns distances and not hits, so there is no path from it to the results; this
    witnesses that at the boundary rather than trusting the type.
    """
    rings = _rows([0.30, 0.32, 0.34], piece_type="anillo", material="plata")
    # Nearer than every ring, and excluded by the category filter. If the probe leaked, these
    # would lead the response.
    necklaces = _rows(
        [0.10, 0.11], piece_type="collar", material="plata", start=90
    )
    search = FakeProductSearch(rings + necklaces)

    response = _serve(search, filters={"category": "anillo"})

    returned = {result.sku for result in response.results}
    assert returned, "the filtered statement found rings, so something must be served"
    assert returned.isdisjoint({row.sku for row in necklaces})
    assert [result.sku for result in response.results] == [
        row.sku for row in rings[: len(response.results)]
    ], "the order is the one the filtered statement produced"


def test_the_two_statements_are_issued_one_after_the_other() -> None:
    """Sequentially and never at once: one connection of a pool capped at five, at any moment.

    The fake records entry, so a concurrent implementation would show the second call starting
    before the first returned.
    """
    search = FakeProductSearch(_peaked_catalogue())
    inflight = {"max": 0, "now": 0}
    original = search.search

    async def _counting(*args, **kwargs):
        inflight["now"] += 1
        inflight["max"] = max(inflight["max"], inflight["now"])
        try:
            return await original(*args, **kwargs)
        finally:
            inflight["now"] -= 1

    search.search = _counting  # type: ignore[method-assign]

    _serve(search, filters={"category": "anillo"})

    assert inflight["max"] == 1


# --------------------------------------------------------- which profile the decision reads


def test_abstention_reads_the_unfiltered_profile() -> None:
    """A flat query abstains even though the filter left too few candidates to judge.

    **This is the whole point of the change.** Before it, the rule read the filtered profile:
    with three candidates it could never reach `min_candidates`, so it answered, and the service
    served three mediocre pieces for a query the catalogue cannot answer.
    """
    flat = _flat_catalogue()
    # A material filter that admits three of the twenty: fewer than the rule's minimum, so a
    # decision taken over the filtered profile cannot fire at all.
    for row in flat[:3]:
        row.materials.append("oro")
    search = FakeProductSearch(flat)

    decisions: list[bool] = []
    response = _serve(
        search, filters={"materials": ["oro"]}, on_abstention=decisions.append
    )

    assert decisions == [True]
    assert response.results == []


def test_an_unfiltered_flat_query_still_abstains() -> None:
    """The regime the rule was calibrated in is unchanged where no filter is involved."""
    decisions: list[bool] = []
    _serve(FakeProductSearch(_flat_catalogue()), on_abstention=decisions.append)

    assert decisions == [True]


def test_the_probe_profile_is_handed_out_for_persistence() -> None:
    """The seam a capture needs: the rule read a profile the persisted window does not contain.

    Without it a re-score of a filtered pass could only guess the decision, because what gets
    persisted is the filtered window and the rule did not read that.
    """
    profiles: list[tuple[float, ...]] = []
    _serve(
        FakeProductSearch(_peaked_catalogue()),
        filters={"category": "anillo"},
        on_abstention_profile=profiles.append,
    )

    assert len(profiles) == 1
    assert len(profiles[0]) == 20, "the probe saw the whole catalogue, not the filtered slice"
    assert profiles[0] == tuple(sorted(profiles[0]))


def test_no_profile_is_handed_out_when_nothing_narrows() -> None:
    """Absence means "the rule read the served window", which is what a re-score assumes."""
    profiles: list[tuple[float, ...]] = []
    _serve(FakeProductSearch(_peaked_catalogue()), on_abstention_profile=profiles.append)

    assert profiles == []


# ------------------------------------------------------------------- the narrow filter code


def test_narrow_filter_over_answerable_query_is_declared() -> None:
    """A peak in the unfiltered profile and a thin filtered set: the FILTER is what emptied it."""
    peaked = _peaked_catalogue()
    for row in peaked[:2]:
        row.materials.append("oro")
    search = FakeProductSearch(peaked)

    response = _serve(search, filters={"materials": ["oro"]})

    assert WARNING_FILTERS_TOO_NARROW in response.warnings
    assert response.results, "it does not abstain: the description found something"


def test_unanswerable_query_abstains_instead_of_blaming_the_filter() -> None:
    """A flat unfiltered profile: the description found nothing, and saying otherwise lies.

    «Hay piezas que encajan pero ninguna pasa los filtros» presupposes the description is
    answerable. Over an unanswerable query that sentence is simply false, and it would send the
    operator to remove a filter that was never the problem.
    """
    flat = _flat_catalogue()
    for row in flat[:2]:
        row.materials.append("oro")
    search = FakeProductSearch(flat)

    response = _serve(search, filters={"materials": ["oro"]})

    assert response.results == []
    assert WARNING_FILTERS_TOO_NARROW not in response.warnings


def test_a_generous_filter_over_an_answerable_query_declares_nothing() -> None:
    """The code states a problem, so it must not fire when there is none."""
    response = _serve(
        FakeProductSearch(_peaked_catalogue()), filters={"category": "anillo"}
    )

    assert response.warnings == []


def test_an_unfiltered_request_can_never_carry_the_narrow_filter_code() -> None:
    """With no filter there is nothing to have been too narrow, whatever the result set size."""
    search = FakeProductSearch(
        _rows([0.21, 0.44], piece_type="anillo", material="plata")
    )

    response = _serve(search)

    assert len(response.results) < MIN_CANDIDATES
    assert response.warnings == []


# ------------------------------------------------------------------------------- the log


def test_probe_log_carries_no_vector_and_no_query(caplog) -> None:
    """Scalars only, by the same rule the existing stage entries already follow.

    The probe stage receives distances, which are numbers; the vector never reaches it and the
    operator's query text is not passed to it at all. This asserts the entry rather than the
    intention, because an added field is exactly how a query text gets into a log.
    """
    search = FakeProductSearch(_peaked_catalogue())

    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        _serve(search, filters={"category": "anillo"})

    entries = [
        record.getMessage()
        for record in caplog.records
        if "stage=probe" in record.getMessage()
    ]
    assert len(entries) == 1, "one probe, one entry"

    entry = entries[0]
    assert "candidates=20" in entry
    assert "distance_min=0.2100" in entry
    assert "anillo de plata" not in entry, "the operator's query text must not appear"
    assert "[0." not in entry and "vector" not in entry, "no embedding may appear"


def test_no_probe_entry_is_written_when_no_probe_runs(caplog) -> None:
    """An entry for a statement that did not run would overstate what the search cost."""
    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        _serve(FakeProductSearch(_peaked_catalogue()))

    assert not [r for r in caplog.records if "stage=probe" in r.getMessage()]
