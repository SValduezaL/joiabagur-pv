"""The assistance layer itself, in its three modes. Offline: no LLM, no provider, no RDS.

The fakes are the ones the rest of the suite already uses, injected through the constructor
seams that already exist. What is under test is the real grouping, the real warning rules,
the real addressing and the real abstention gate.
"""

from __future__ import annotations

import json

import pytest

from jbg_ai.api.schemas.assist import AssistRequest
from jbg_ai.assist.constants import (
    ASSIST_WARNING_CODES,
    FAMILY_ROSTER_CAP,
    INTENT_PRODUCT_PITCH,
    INTENT_UNCLASSIFIED,
    WARNING_FILTERS_TOO_NARROW,
    WARNING_KNOWLEDGE_NOT_COVERED,
    WARNING_FAMILY_HAS_VARIANTS,
    WARNING_SIZE_LABEL_MISSING,
)
from jbg_ai.assist.modes import AssistMode
from jbg_ai.assist.errors import UnusableAnchorProductError
from jbg_ai.assist.knowledge_scope import canonical_material_sheets
from jbg_ai.assist.orchestrator import assist_sale
from jbg_ai.assist.prompt import PitchTask, resolve_task, task_message
from jbg_ai.knowledge.constants import CLAIM_SCOPE_GENERAL
from jbg_ai.knowledge.offline import InMemoryKnowledgeIndex, LocalEmbeddingClient
from support.assist_world import (
    FAMILY,
    FOURTH,
    LONER,
    OTHER_FAMILY,
    PIECE,
    SIBLING,
    THIRD,
    indexed_row,
    run,
)
from support.assist_router import decision, scripted_router
from support.fake_product_search import FakeProductSearch
from support.settings import build_settings

SETTINGS = dict(stub_mode=False, jpv_retrieval_distance_threshold=0.65)

#: `LocalEmbeddingClient` and not `FakeEmbeddingClient`, because these tests drive BOTH
#: indexes from one client. The product side reads a precomputed `distance` off each fake
#: row and ignores the vector entirely; the knowledge side really does compare the query
#: vector against the corpus, and it holds `local_vector` embeddings — so a hash-based
#: stand-in would sit at a cosine distance of ~1 from every fragment and every knowledge
#: search here would abstain for a reason that has nothing to do with what is under test.
#: It counts its calls too, which is what the no-provider-call assertions read.
def serve(search, knowledge, principal, **kwargs):
    payload = AssistRequest(**kwargs.pop("payload"))
    return run(
        assist_sale(
            payload,
            principal,
            settings=kwargs.pop("settings", None) or build_settings(**SETTINGS),
            embed=kwargs.pop("embed", None) or LocalEmbeddingClient(),
            search=search,
            knowledge=knowledge,
            **kwargs,
        )
    )


# --- 6.1 / 6.2 · the three modes, and the intent that follows from them -------------------


def test_a_piece_with_no_question_is_served_as_one_group(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert len(response.groups) == 1
    assert response.intent == INTENT_PRODUCT_PITCH
    assert {member.product_id for member in response.groups[0].members} == {
        str(PIECE),
        str(SIBLING),
    }


def test_a_free_query_is_served_over_the_retrieved_candidates(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})

    assert response.groups
    assert response.intent == INTENT_UNCLASSIFIED


def test_a_piece_with_a_question_is_anchored_and_answers_the_question(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(
        search,
        knowledge,
        principal,
        payload={"product_id": str(PIECE), "query": "Cuidados y limpieza en casa de la plata"},
        knowledge_distance_threshold=0.99,
    )

    assert response.intent == INTENT_UNCLASSIFIED
    assert len(response.groups) == 1
    assert response.groups[0].family_id == str(FAMILY)
    assert response.citations, "the question must be answered from the corpus"


def test_two_wordings_with_the_same_anchors_report_the_same_intent(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    first = serve(search, knowledge, principal, payload={"query": "un regalo para mi madre"})
    second = serve(search, knowledge, principal, payload={"query": "anillo de plata barato"})

    assert first.intent == second.intent == INTENT_UNCLASSIFIED


# --- 6.3 · grouping, and the invariant that comes with a nullable family ------------------


def test_a_piece_with_a_family_is_grouped_under_it_with_its_variants(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    group = serve(
        search, knowledge, principal, payload={"product_id": str(PIECE)}
    ).groups[0]

    assert group.family_id == str(FAMILY)
    assert group.family_label == "Aro Menorca"
    assert [member.variant_label for member in group.members] == ["18 mm", "20 mm"]


def test_a_piece_with_no_family_is_a_group_of_exactly_one(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"product_id": str(LONER)})

    assert len(response.groups) == 1
    assert response.groups[0].family_id is None
    assert len(response.groups[0].members) == 1
    assert response.groups[0].members[0].product_id == str(LONER)


def test_no_group_with_a_null_family_ever_carries_more_than_one_member(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """Three familyless products in one result set must not be bucketed together."""
    search = FakeProductSearch(
        [
            indexed_row(product_id=PIECE, family_id=None, family_name=None),
            indexed_row(
                product_id=SIBLING, sku="JBG-0002", family_id=None, family_name=None
            ),
            indexed_row(
                product_id=THIRD, sku="JBG-0003", family_id=None, family_name=None
            ),
        ]
    )

    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})

    assert len(response.groups) == 3
    for group in response.groups:
        assert group.family_id is None
        assert len(group.members) == 1


def test_candidates_of_one_family_share_a_group_on_the_query_path(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch(
        [
            indexed_row(product_id=PIECE),
            indexed_row(product_id=SIBLING, sku="JBG-0002"),
            indexed_row(
                product_id=THIRD, sku="JBG-0003", family_id=OTHER_FAMILY,
                family_name="Otra",
            ),
        ]
    )

    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})
    by_family = {group.family_id: group for group in response.groups}

    assert len(by_family[str(FAMILY)].members) == 2
    assert len(by_family[str(OTHER_FAMILY)].members) == 1


def test_every_member_carries_the_match_reasons_the_retrieval_recorded(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})
    reasons = {
        reason
        for group in response.groups
        for member in group.members
        for reason in member.match_reasons
    }

    assert reasons
    assert reasons <= {"vector", "lexical"}, "the retrieval vocabulary, not a sentence"


# --- 6.4 · the warnings, and where they come from -----------------------------------------


def test_the_variants_warning_fires_on_a_member_the_retrieval_did_not_return(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """The whole reason `family_roster` exists, as a test.

    Four members in the family and the search returns exactly one, because only one is
    close enough. Counting candidates would say "no variants"; the roster says four.
    """
    # The three siblings are out of reach of BOTH branches: past the distance threshold and
    # carrying no text the query can match. Otherwise the fake's lexical branch would return
    # them anyway and the test would prove nothing about the roster.
    unreachable = {"distance": 0.95, "doc_text": "Tipo: colgante. Materiales: resina."}
    search = FakeProductSearch(
        [
            indexed_row(product_id=PIECE, distance=0.1),
            indexed_row(product_id=SIBLING, sku="JBG-0002", **unreachable),
            indexed_row(product_id=THIRD, sku="JBG-0003", **unreachable),
            indexed_row(product_id=FOURTH, sku="JBG-0004", **unreachable),
        ]
    )

    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})

    assert sum(len(group.members) for group in response.groups) == 1
    assert WARNING_FAMILY_HAS_VARIANTS in response.warnings
    assert search.family_roster_calls == [(FAMILY, FAMILY_ROSTER_CAP)]


def test_a_family_of_one_raises_no_variants_warning(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch([indexed_row(product_id=PIECE)])

    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert WARNING_FAMILY_HAS_VARIANTS not in response.warnings


def test_a_piece_with_no_family_raises_no_variants_warning(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"product_id": str(LONER)})

    assert WARNING_FAMILY_HAS_VARIANTS not in response.warnings


def test_a_missing_size_label_raises_its_warning(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch([indexed_row(product_id=PIECE, size_label=None)])

    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert WARNING_SIZE_LABEL_MISSING in response.warnings


def test_a_declared_size_label_raises_no_warning(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert WARNING_SIZE_LABEL_MISSING not in response.warnings


def test_every_warning_belongs_to_the_closed_vocabulary(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    for payload in (
        {"product_id": str(PIECE)},
        {"query": "anillo de plata"},
        {"product_id": str(PIECE), "query": "¿se puede mojar?"},
        {"product_id": str(LONER)},
    ):
        response = serve(search, knowledge, principal, payload=payload)
        for warning in response.warnings:
            assert warning in ASSIST_WARNING_CODES, (payload, warning)
            assert " " not in warning


# --- 6.5 · no stock warning, and no bucket anywhere ----------------------------------------


def test_a_piece_out_of_stock_raises_no_stock_warning_and_leaks_no_bucket(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """The bucket exists on the row, is read by the ranking, and must not reach the wire."""
    from uuid import UUID

    from support.fake_product_search import FakeAssignment
    from support.settings import TOKEN_POS_ID

    pos = UUID(TOKEN_POS_ID)
    search = FakeProductSearch(
        [indexed_row(product_id=PIECE)],
        assignments=[FakeAssignment(pos_id=pos, product_id=PIECE, qty_bucket="0")],
    )

    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})
    body = json.dumps(response.model_dump(), ensure_ascii=False)

    assert "stock_critical" not in body
    assert "family_members_out_of_stock" not in body
    assert "qty_bucket" not in body


# --- 6.6 · the piece-anchored mode addresses, it does not search ---------------------------


def test_the_piece_anchored_mode_cites_the_sheets_of_its_own_materials(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert response.citations
    documents = {citation.citation_id.partition("#")[0] for citation in response.citations}
    assert documents == {"material-plata"}


def test_the_piece_anchored_mode_cites_no_establishment_claim(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch(
        [indexed_row(product_id=PIECE, materials=["baño de oro"], family_id=None)]
    )

    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert response.citations
    assert all(
        citation.claim_scope == CLAIM_SCOPE_GENERAL for citation in response.citations
    )


def test_the_piece_anchored_mode_makes_no_provider_call(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    embed = LocalEmbeddingClient()

    response = serve(
        search, knowledge, principal, payload={"product_id": str(PIECE)}, embed=embed
    )

    assert response.citations
    assert embed.calls == [], "a piece with no question must not embed anything"


def test_a_piece_of_two_materials_also_receives_the_mixed_piece_guidance(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch(
        [
            indexed_row(
                product_id=PIECE, materials=["plata", "baño de oro"], family_id=None
            )
        ]
    )

    response = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})
    documents = {citation.citation_id.partition("#")[0] for citation in response.citations}

    assert "material-piezas-mixtas" in documents


def test_the_section_list_and_the_material_cap_travel_by_parameter(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch(
        [
            indexed_row(
                product_id=PIECE, materials=["plata", "baño de oro"], family_id=None
            )
        ]
    )

    narrowed = serve(
        search,
        knowledge,
        principal,
        payload={"product_id": str(PIECE)},
        pitch_sections=("cuidados-y-limpieza-en-casa",),
        material_cap=1,
    )
    documents = {citation.citation_id.partition("#")[0] for citation in narrowed.citations}

    assert documents == {"material-plata", "material-piezas-mixtas"}
    sections = {
        citation.citation_id.partition("#")[2]
        for citation in narrowed.citations
        if citation.citation_id.startswith("material-plata")
    }
    assert sections == {"cuidados-y-limpieza-en-casa"}


def test_a_question_about_the_piece_never_cites_another_materials_sheet(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch(
        [indexed_row(product_id=PIECE, materials=["acero"], family_id=None)]
    )

    response = serve(
        search,
        knowledge,
        principal,
        payload={"product_id": str(PIECE), "query": "Cuidados y limpieza en casa"},
        knowledge_distance_threshold=0.99,
        citation_top_k=20,
    )
    documents = {citation.citation_id.partition("#")[0] for citation in response.citations}
    foreign = set(canonical_material_sheets()) - {"material-acero"}

    assert response.citations
    assert not documents & foreign


# --- 6.7 · abstention ----------------------------------------------------------------------


def _flat_family(count: int) -> FakeProductSearch:
    """`count` candidates at an identical distance: the flat profile the rule abstains on."""
    return FakeProductSearch(
        [
            indexed_row(
                product_id=__import__("uuid").UUID(f"aaaaaaaa-aaaa-4aaa-8aaa-{index:012d}"),
                sku=f"JBG-{index:04d}",
                distance=0.4,
                family_id=None,
                family_name=None,
            )
            for index in range(count)
        ]
    )


def test_an_abstained_query_returns_no_group_and_says_so(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(
        _flat_family(20), knowledge, principal, payload={"query": "anillo de plata"}
    )

    assert response.abstained is True
    assert response.groups == []


def test_an_answerable_query_is_not_silenced(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})

    assert response.abstained is False
    assert response.groups


def test_the_abstention_configuration_travels_by_parameter(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """Two calls in one process, two configurations, and neither reads the environment."""
    flat = _flat_family(20)

    on = serve(flat, knowledge, principal, payload={"query": "anillo"}, abstain=True)
    off = serve(flat, knowledge, principal, payload={"query": "anillo"}, abstain=False)

    assert on.abstained is True
    assert off.abstained is False
    assert off.groups


def test_the_abstention_field_is_present_in_every_mode_and_false_when_anchored(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    for payload in (
        {"product_id": str(PIECE)},
        {"product_id": str(PIECE), "query": "¿se puede mojar?"},
        {"query": "anillo de plata"},
    ):
        response = serve(search, knowledge, principal, payload=payload)
        assert response.abstained is False, payload

    anchored = serve(search, knowledge, principal, payload={"product_id": str(PIECE)})
    assert anchored.abstained is False


# --- 6.8 · an unusable piece is an error and never an abstention ---------------------------


def test_an_unknown_piece_is_an_error_naming_that_case(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    unknown = "aaaaaaaa-aaaa-4aaa-8aaa-000000009999"

    with pytest.raises(UnusableAnchorProductError) as error:
        serve(search, knowledge, principal, payload={"product_id": unknown})

    assert "not present in the retrieval index" in str(error.value)


def test_an_inactive_piece_is_a_different_error(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch([indexed_row(product_id=PIECE, is_active=False)])

    with pytest.raises(UnusableAnchorProductError) as error:
        serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert "inactive" in str(error.value)


def test_a_piece_without_an_embedding_is_a_third_error(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    search = FakeProductSearch([indexed_row(product_id=PIECE, has_embedding=False)])

    with pytest.raises(UnusableAnchorProductError) as error:
        serve(search, knowledge, principal, payload={"product_id": str(PIECE)})

    assert "no embedding" in str(error.value)


def test_an_unparseable_product_id_is_the_same_kind_of_error(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    with pytest.raises(UnusableAnchorProductError):
        serve(search, knowledge, principal, payload={"product_id": "P-0001"})


def test_the_three_unusable_cases_give_three_different_sentences(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    messages = set()
    for search, payload in (
        (FakeProductSearch([]), {"product_id": str(PIECE)}),
        (
            FakeProductSearch([indexed_row(product_id=PIECE, is_active=False)]),
            {"product_id": str(PIECE)},
        ),
        (
            FakeProductSearch([indexed_row(product_id=PIECE, has_embedding=False)]),
            {"product_id": str(PIECE)},
        ),
    ):
        with pytest.raises(UnusableAnchorProductError) as error:
            serve(search, knowledge, principal, payload=payload)
        messages.add(str(error.value))

    assert len(messages) == 3


# --- 7.3 · with no generation client: no prose, no prompt version, no usage -----------------


def test_without_a_generation_client_the_argument_is_empty_and_its_provenance_absent(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """C30a's shape, which C30b turned from a requirement into a **deployment state**.

    `assist_sale` takes the generation client as a parameter and builds none, so a call that
    passes nothing — like every call in this module — serves exactly the structured response.
    That is the rollback of C30b and the reason the two halves stay comparable as an ablation:
    same route, same candidates, same citations, with prose and without it.
    """
    for payload in (
        {"product_id": str(PIECE)},
        {"query": "anillo de plata"},
        {"product_id": str(PIECE), "query": "¿se puede mojar?"},
    ):
        response = serve(search, knowledge, principal, payload=payload)

        assert response.pitch == "", payload
        assert response.prompt_version is None, payload
        assert response.usage.prompt_tokens == 0
        assert response.usage.completion_tokens == 0
        assert response.usage.total_tokens == 0
        assert response.usage.model is None


# --- 7.2 · the scope is the token's --------------------------------------------------------


def test_the_scope_applied_is_the_token_claim_and_never_the_body(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    from support.settings import OTHER_POS_ID, TOKEN_POS_ID

    response = serve(
        search,
        knowledge,
        principal,
        payload={"product_id": str(PIECE), "pos_id": OTHER_POS_ID},
    )

    assert response.effective_pos_id == TOKEN_POS_ID


# --- 6.9 · the package imports no provider client -------------------------------------------


def test_the_assist_package_imports_no_provider_client() -> None:
    """Introspection over the module graph, not a promise in a docstring.

    Still true after C30b, and it is the same property rather than a weakened one: the layer
    is **handed** its clients and the adapter in `assist/llm.py` reaches for `litellm` inside
    the call it makes, exactly as `enrichment/llm.py` does. So the package imports offline, the
    suite opens no socket, and importing `jbg_ai.assist` costs no provider library.
    """
    import importlib
    import pkgutil

    import jbg_ai.assist as package

    forbidden = ("litellm", "openai", "anthropic", "httpx")
    for info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"jbg_ai.assist.{info.name}")
        source = module.__dict__
        for name in forbidden:
            assert name not in source, f"{info.name} imports {name}"
        assert not any(
            key.startswith(name) for key in source for name in forbidden
        ), info.name


# --- three scenarios the QA pass found covered only indirectly, closed here ---------------


class _RefusingIndex:
    """A knowledge index that fails loudly if either search branch is touched.

    `fetch_chunks` is the only door the piece-anchored mode may use. Asserting that the
    embedding client made no call proves no vector was COMPUTED; it does not prove no search
    RAN, and the scenario asks for the second thing.
    """

    def __init__(self, inner) -> None:
        self._inner = inner
        self.fetch_calls = 0

    async def vector_search(self, *args, **kwargs):
        raise AssertionError("the piece-anchored mode must run no vector search")

    async def lexical_search(self, *args, **kwargs):
        raise AssertionError("the piece-anchored mode must run no lexical search")

    async def fetch_chunks(self, chunk_ids):
        self.fetch_calls += 1
        return await self._inner.fetch_chunks(chunk_ids)


def test_no_similarity_search_runs_for_the_piece_anchored_mode(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    refusing = _RefusingIndex(knowledge)

    response = serve(search, refusing, principal, payload={"product_id": str(PIECE)})

    assert response.citations
    assert refusing.fetch_calls == 1, "one addressed read, and no branch of the search"


def test_no_language_model_provider_is_called_when_no_client_is_configured(
    search, knowledge: InMemoryKnowledgeIndex, principal, monkeypatch
) -> None:
    """The generation gate, asserted at the provider's own door rather than by introspection.

    After C30b this is the **deployment without a generation client**, which is the state a
    service with no provider credential serves in: no call is made, in any of the three modes.
    That two of those modes do call when a client is handed in is `tests/assist/
    test_generation.py`; the two modes that never call whatever is configured are there too.

    Patching `litellm.acompletion` to raise means any completion from any mode fails this test
    loudly. The embedding path is a different function and is deliberately left alone: the
    modes with a question are allowed the retrieval's own embedding, and forbidding that would
    test the wrong invariant.
    """
    import litellm

    def _forbidden(*args, **kwargs):
        raise AssertionError("C30a must not call a language model provider")

    monkeypatch.setattr(litellm, "acompletion", _forbidden, raising=False)
    monkeypatch.setattr(litellm, "completion", _forbidden, raising=False)

    for payload in (
        {"product_id": str(PIECE)},
        {"query": "anillo de plata"},
        {"product_id": str(PIECE), "query": "¿se puede mojar?"},
    ):
        response = serve(search, knowledge, principal, payload=payload)
        assert response.pitch == "", payload


def test_an_absent_abstention_parameter_falls_back_to_the_configured_default(
    knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """`Settings` supplies the default and nothing else; the call may always override it.

    Driven with the SAME flat candidate profile both ways, so the only thing that moves is
    where the effective value came from.
    """
    flat = _flat_family(20)

    enabled = serve(
        flat,
        knowledge,
        principal,
        payload={"query": "anillo"},
        settings=build_settings(**SETTINGS, jpv_abstention_enabled=True),
    )
    disabled = serve(
        flat,
        knowledge,
        principal,
        payload={"query": "anillo"},
        settings=build_settings(**SETTINGS, jpv_abstention_enabled=False),
    )

    assert enabled.abstained is True
    assert disabled.abstained is False
    assert disabled.groups


# --- C40 · the filters the operator pressed reach retrieval in the free-query mode --------


def test_free_query_forwards_filters_to_retrieval(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """The chips an operator pressed must narrow what M1 retrieves.

    Without this the free-query mode knew *less* about what was asked than the plain
    retrieval route did: the panel collected the filters and the assist request had nowhere
    to carry them, so they were dropped at the boundary while the controls stayed pressed.
    """
    serve(
        search,
        knowledge,
        principal,
        payload={
            "query": "anillo de plata",
            "filters": {"materials": ["plata"], "category": "anillo"},
        },
    )

    assert search.search_calls, "the free-query mode retrieves, so the port must be reached"
    # **The first statement, not the last.** Since C40 a filtered request issues two: the served
    # one, which carries the filters, and the abstention probe, which deliberately carries none.
    # Reading the last call here would assert the opposite of what this test is about.
    served = search.search_calls[0]["filters"]
    assert list(served.materials) == ["plata"]
    assert served.category == "anillo"

    probe = search.search_calls[-1]["filters"]
    assert probe.is_empty, "the probe judges the query, so no filter of the operator's may reach it"


def test_a_narrow_filter_is_declared_on_the_generative_route_too(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """The code reaches M1, because the decision belongs to retrieval and M1 retrieves.

    The requirement is that it be available on **every** consuming path that accepts
    catalog-side filters and not only on the generative one. This is the generative one; the
    plain retrieval route is covered in `tests/retrieval/test_probe.py`. It is **carried** and
    not recomputed here, so the two cannot drift into saying different things about one
    search.
    """
    response = serve(
        search,
        knowledge,
        principal,
        payload={
            "query": "anillo de plata",
            "filters": {"materials": ["oro"]},
        },
    )

    assert WARNING_FILTERS_TOO_NARROW in response.warnings
    assert not response.abstained, (
        "the unfiltered profile is not flat, so the description is not what failed"
    )


def test_a_refused_query_carries_no_narrow_filter_code(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """Nothing was retrieved, so there is no filter that could have been too narrow.

    The router cuts before retrieval. A code about the filters over a query this shop does not
    serve would send the operator to loosen a filter that never ran.
    """
    router, _ = scripted_router(decision(served="out_of_domain", index=None))

    response = serve(
        search,
        knowledge,
        principal,
        payload={
            "query": "un reloj sumergible",
            "filters": {"materials": ["oro"]},
        },
        router_client=router,
    )

    assert WARNING_FILTERS_TOO_NARROW not in response.warnings
    assert not search.search_calls, "the refusal cuts before retrieval, so no statement runs at all"


def test_free_query_without_filters_behaves_as_before(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """Pure addition: a caller that sends no filters gets exactly what it got before."""
    response = serve(search, knowledge, principal, payload={"query": "anillo de plata"})

    forwarded = search.search_calls[-1]["filters"]
    assert not forwarded.materials
    assert forwarded.category is None
    assert forwarded.family_id is None
    assert not forwarded.exclude_product_ids
    assert response.groups


def test_anchored_mode_ignores_filters(
    search, knowledge: InMemoryKnowledgeIndex, principal
) -> None:
    """An anchor already says what to retrieve, so a catalog filter can only contradict it.

    Asserted rather than assumed: the field is on the shared request model, so nothing stops
    a caller sending both. Honouring the filter here could drop the very piece the caller
    anchored to — answering about a piece by not showing it.
    """
    response = serve(
        search,
        knowledge,
        principal,
        payload={
            "product_id": str(PIECE),
            "filters": {"category": "un-tipo-que-no-existe"},
        },
    )

    assert len(response.groups) == 1
    assert {member.product_id for member in response.groups[0].members} == {
        str(PIECE),
        str(SIBLING),
    }


# --- C40 · the coverage guardrail reaches the free query ----------------------------------


def test_free_query_knowledge_without_corpus_declares_it(
    search, principal
) -> None:
    """A knowledge question the corpus cannot answer must say so, not answer from memory.

    M3 has had this guardrail since C34. M1 did not, so a knowledge question with zero
    fragments ran the task that says «responde apoyándote en esos fragmentos» **with no
    fragments** — which is not a neutral omission but an explicit invitation to invent, in the
    one mode C40 puts in front of an operator.
    """
    router, _ = scripted_router(decision(index="knowledge"))
    empty_corpus = InMemoryKnowledgeIndex(chunks=[])

    response = serve(
        search,
        empty_corpus,
        principal,
        payload={"query": "¿la plata aguanta el agua del mar?"},
        router_client=router,
    )

    assert response.citations == []
    assert WARNING_KNOWLEDGE_NOT_COVERED in response.warnings


def test_free_query_catalog_route_does_not_declare_missing_coverage(
    search, principal
) -> None:
    """On `catalog` an empty citation list is correct, not a gap.

    That route is answered from pieces and its own task section tells the model to return no
    citations at all, so reporting «la documentación no cubre esta pregunta» would be a warning
    about a question nobody asked the documentation.
    """
    router, _ = scripted_router(decision(index="catalog"))
    empty_corpus = InMemoryKnowledgeIndex(chunks=[])

    response = serve(
        search,
        empty_corpus,
        principal,
        payload={"query": "anillo de plata"},
        router_client=router,
    )

    assert WARNING_KNOWLEDGE_NOT_COVERED not in response.warnings


def test_free_query_uncovered_costs_no_extra_provider_call(
    search, principal
) -> None:
    """The guardrail reads a result already computed: no second search, no provider call."""
    router, _ = scripted_router(decision(index="knowledge"))
    empty_corpus = InMemoryKnowledgeIndex(chunks=[])
    embed = LocalEmbeddingClient()

    serve(
        search,
        empty_corpus,
        principal,
        payload={"query": "¿la plata aguanta el agua del mar?"},
        router_client=router,
        embed=embed,
    )

    # The embeddings are those the query itself needs and nothing more: deciding "uncovered"
    # is reading `not citations`, which the search above already produced. A guardrail that
    # cost a second call would be paid on every knowledge question the corpus cannot answer.
    assert len(embed.calls) <= 2


def test_free_query_without_corpus_uses_the_uncovered_task(
    search, principal
) -> None:
    """`resolve_task` picks the fourth free-query task, and the prompt carries its section."""
    assert (
        resolve_task(AssistMode.QUERY_ONLY, route="knowledge", uncovered=True)
        is PitchTask.FREE_QUERY_UNCOVERED
    )
    assert (
        resolve_task(AssistMode.QUERY_ONLY, route="both", uncovered=True)
        is PitchTask.FREE_QUERY_UNCOVERED
    )
    # And `catalog` is deliberately untouched: an empty corpus there is the normal state.
    assert (
        resolve_task(AssistMode.QUERY_ONLY, route="catalog", uncovered=True)
        is PitchTask.FREE_QUERY_CATALOG
    )

    task = task_message(PitchTask.FREE_QUERY_UNCOVERED).casefold()
    assert "no finjas haber contestado" in task
    assert "no respondas de memoria" in task
