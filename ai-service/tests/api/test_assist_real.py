"""Real POST /v1/assist/sale with stubs disabled. C30a.

Offline throughout: the search port, the knowledge index and the embedding client all go in
through `app.state`, which is the seam the retrieval suite already uses. No socket is opened.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from jbg_ai.api.main import create_app
from jbg_ai.api.schemas.assist import AssistResponse
from jbg_ai.assist.constants import (
    ASSIST_INTENTS,
    ASSIST_WARNING_CODES,
    INTENT_PRODUCT_PITCH,
    INTENT_UNCLASSIFIED,
)
from jbg_ai.knowledge.chunking import chunk_corpus
from jbg_ai.knowledge.corpus import load_corpus
from jbg_ai.knowledge.offline import InMemoryKnowledgeIndex, LocalEmbeddingClient
from support.assist_world import FAMILY, LONER, PIECE, SIBLING, indexed_row
from support.fake_product_search import FakeAssignment, FakeProductSearch
from support.settings import OTHER_POS_ID, TOKEN_POS_ID, build_settings

#: Any bare number followed by a currency mark would mean Python resolved a price.
PRICE_LIKE = re.compile(r"\d+[.,]?\d*\s*(€|eur|euros)", re.IGNORECASE)

#: A price as the index holds it, so the "no price anywhere" assertion has something to find
#: if the boundary ever leaks. 87,50 is a real-looking figure and not a round one.
INDEXED_PRICE = 87.50


def _rows() -> list:
    return [
        indexed_row(product_id=PIECE, price=INDEXED_PRICE),
        indexed_row(
            product_id=SIBLING, sku="JBG-0002", variant_label="20 mm", price=INDEXED_PRICE
        ),
        indexed_row(
            product_id=LONER,
            sku="JBG-0009",
            family_id=None,
            family_name=None,
            price=INDEXED_PRICE,
        ),
    ]


def _real_app(*, search: FakeProductSearch | None = None, **overrides):
    settings = build_settings(stub_mode=False, **overrides)
    app = create_app(settings)
    app.state.retrieval_embed = LocalEmbeddingClient()
    app.state.retrieval_search = search if search is not None else FakeProductSearch(_rows())
    app.state.knowledge_index = InMemoryKnowledgeIndex(chunks=chunk_corpus(load_corpus()))
    return app


def _client(issue_token: Callable[..., str], **kwargs) -> TestClient:
    client = TestClient(_real_app(**kwargs))
    client.headers.update({"Authorization": f"Bearer {issue_token()}"})
    return client


# --- 7.1 · the route is real with stubs off, and the fixture survives with them on ---------


def test_the_route_does_not_answer_501_with_stubs_disabled(
    issue_token: Callable[..., str],
) -> None:
    response = _client(issue_token).post(
        "/v1/assist/sale", json={"product_id": str(PIECE), "top_k": 3}
    )

    assert response.status_code == 200
    assert AssistResponse.model_validate(response.json())


def test_stub_mode_still_serves_the_fixture(issue_token: Callable[..., str]) -> None:
    app = create_app(build_settings(stub_mode=True))
    app.state.retrieval_search = FakeProductSearch(_rows())
    with TestClient(app) as client:
        response = client.post(
            "/v1/assist/sale",
            json={"query": "regalo", "top_k": 2},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 200
    # The fixture still serves prose where the real path would emit an empty pitch, which is
    # what this test is about. It no longer carries placeholders: C40 took them out of the
    # free-query branch of the double, because .NET withholds the whole argument when one
    # reaches it with no anchor to resolve against, so writing them here would have taught
    # every stub-backed client a contract the real pipeline refuses.
    assert response.json()["pitch"]
    assert "{{price}}" not in response.json()["pitch"]


def test_the_delivering_change_constant_is_gone_from_the_module() -> None:
    """It went with the 501, as `SUBSTITUTES_DELIVERED_BY` did when C26 served its route."""
    from jbg_ai.api.routers import assist

    assert not hasattr(assist, "DELIVERED_BY")


# --- 7.2 · scope and authentication ---------------------------------------------------------


def test_the_scope_comes_from_the_token_and_never_from_the_body(
    issue_token: Callable[..., str],
) -> None:
    body = (
        _client(issue_token)
        .post(
            "/v1/assist/sale",
            json={"product_id": str(PIECE), "pos_id": OTHER_POS_ID, "top_k": 2},
        )
        .json()
    )

    assert body["effective_pos_id"] == TOKEN_POS_ID
    assert body["effective_pos_id"] != OTHER_POS_ID


def test_a_call_without_a_token_is_rejected(issue_token: Callable[..., str]) -> None:
    """A fresh client: the shared one carries the cookies of every login it performed."""
    client = TestClient(_real_app())

    response = client.post("/v1/assist/sale", json={"product_id": str(PIECE)})

    assert response.status_code == 401


# --- 7.3 · with no provider credential: no prose, no prompt version, no usage ----------------


def test_without_a_provider_credential_the_route_emits_no_pitch_and_a_null_prompt_version(
    issue_token: Callable[..., str],
) -> None:
    """`build_settings` pins the optional credentials to None, so this is the deployment that
    has no generation layer — and it answers **200 with the structured response**, not 503.

    The paths that cannot work without their credential do answer 503; this one has most of
    the response already computed and correct, so refusing to serve it would turn a partial
    loss into a total one. It is also the rollback of C30b, without a schema being touched.
    """
    client = _client(issue_token)

    for payload in (
        {"product_id": str(PIECE)},
        {"query": "anillo de plata"},
        {"product_id": str(PIECE), "query": "¿se puede mojar?"},
    ):
        body = client.post("/v1/assist/sale", json=payload).json()

        assert body["pitch"] == "", payload
        assert body["prompt_version"] is None, payload
        assert body["usage"] == {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": None,
        }, payload


def test_the_intent_is_always_one_of_the_two_declared_values(
    issue_token: Callable[..., str],
) -> None:
    client = _client(issue_token)

    anchored = client.post("/v1/assist/sale", json={"product_id": str(PIECE)}).json()
    asked = client.post("/v1/assist/sale", json={"query": "anillo"}).json()

    assert anchored["intent"] == INTENT_PRODUCT_PITCH
    assert asked["intent"] == INTENT_UNCLASSIFIED
    for body in (anchored, asked):
        assert body["intent"] in ASSIST_INTENTS


# --- 7.4 · the structured log -----------------------------------------------------------------


def test_the_log_line_reports_the_decision_and_carries_no_vector(
    issue_token: Callable[..., str], caplog: pytest.LogCaptureFixture
) -> None:
    # The app is built FIRST and the handler attached after: `create_app` configures the
    # root logger, so a handler added before it is wiped by it. Same order as
    # `test_trace_id_appears_in_stage_logs`, and the order is the whole trick.
    app = _real_app()
    logging.getLogger().addHandler(caplog.handler)
    with caplog.at_level(logging.INFO, logger="jbg_ai.assist.orchestrator"):
        with TestClient(app) as client:
            client.post(
                "/v1/assist/sale",
                json={"product_id": str(PIECE), "top_k": 2},
                headers={"Authorization": f"Bearer {issue_token()}"},
            )

    lines = [
        record.getMessage()
        for record in caplog.records
        if record.name == "jbg_ai.assist.orchestrator"
    ]

    assert lines, "the layer must log its decision"
    line = lines[-1]
    for field in (
        "stage=assist",
        "trace_id=",
        "mode=",
        "intent=",
        "groups=",
        "warnings=",
        "citations=",
        "abstained=",
    ):
        assert field in line, field
    # The citations are named by identifier, which is what makes the line auditable.
    assert "material-plata#" in line
    # And no vector reaches it: a 1.536-float list in a log is not an observability choice.
    assert "[0." not in line
    assert "embedding" not in line


# --- 7.5 · no price and no stock anywhere in the response -------------------------------------


def _walk(value, path="$"):
    """Every scalar of the serialised response, with the path that reached it."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")
    else:
        yield path, value


def test_no_field_of_the_response_carries_a_price_or_a_stock_figure(
    issue_token: Callable[..., str],
) -> None:
    """Over the WHOLE serialised response, not over the pitch — which is empty anyway.

    An empty pitch would make a pitch-only check pass by construction, which is exactly the
    kind of test that goes green having asserted nothing.
    """
    pos = UUID(TOKEN_POS_ID)
    search = FakeProductSearch(
        _rows(),
        assignments=[
            FakeAssignment(pos_id=pos, product_id=PIECE, qty_bucket="0"),
            FakeAssignment(pos_id=pos, product_id=SIBLING, qty_bucket="1-2"),
            FakeAssignment(pos_id=pos, product_id=LONER, qty_bucket="3+"),
        ],
    )
    client = _client(issue_token, search=search)

    for payload in (
        {"product_id": str(PIECE)},
        {"query": "anillo de plata"},
        {"product_id": str(PIECE), "query": "¿se puede mojar?"},
    ):
        body = client.post("/v1/assist/sale", json=payload).json()
        blob = json.dumps(body, ensure_ascii=False)

        for forbidden in ("qty_bucket", "price", "stock", "sales_30d"):
            assert forbidden not in blob, (payload, forbidden)
        assert str(INDEXED_PRICE) not in blob, payload
        assert "87,5" not in blob and "87.5" not in blob, payload
        assert PRICE_LIKE.search(blob) is None, payload
        # The buckets the projection holds, none of which may appear as a value either.
        for path, value in _walk(body):
            assert value not in ("0", "1-2", "3+"), (payload, path)


def test_no_stock_warning_is_emitted_by_this_service(
    issue_token: Callable[..., str],
) -> None:
    pos = UUID(TOKEN_POS_ID)
    search = FakeProductSearch(
        _rows(),
        assignments=[FakeAssignment(pos_id=pos, product_id=PIECE, qty_bucket="0")],
    )

    body = (
        _client(issue_token, search=search)
        .post("/v1/assist/sale", json={"product_id": str(PIECE)})
        .json()
    )

    assert "stock_critical" not in body["warnings"]
    assert "family_members_out_of_stock" not in body["warnings"]
    for warning in body["warnings"]:
        assert warning in ASSIST_WARNING_CODES


# --- the three unusable anchors, over HTTP ------------------------------------------------------


def test_an_unusable_piece_is_a_422_and_never_a_200_with_abstained(
    issue_token: Callable[..., str],
) -> None:
    cases = {
        "unknown": (FakeProductSearch([]), "not present in the retrieval index"),
        "inactive": (
            FakeProductSearch([indexed_row(product_id=PIECE, is_active=False)]),
            "inactive",
        ),
        "unindexed": (
            FakeProductSearch([indexed_row(product_id=PIECE, has_embedding=False)]),
            "no embedding",
        ),
    }
    seen = set()
    for name, (search, fragment) in cases.items():
        response = _client(issue_token, search=search).post(
            "/v1/assist/sale", json={"product_id": str(PIECE)}
        )

        assert response.status_code == 422, name
        detail = str(response.json()["detail"])
        assert fragment in detail, name
        seen.add(detail)

    assert len(seen) == 3, "the three cases must be three different sentences"


def test_a_request_with_neither_anchor_is_rejected_naming_both(
    issue_token: Callable[..., str],
) -> None:
    response = _client(issue_token).post("/v1/assist/sale", json={"top_k": 2})

    assert response.status_code == 422
    detail = str(response.json()["detail"])
    assert "product_id" in detail
    assert "query" in detail


# --- the citations resolve --------------------------------------------------------------------


def test_every_citation_resolves_to_a_real_document_and_heading(
    issue_token: Callable[..., str],
) -> None:
    """The property that makes a citation verifiable rather than decorative."""
    corpus = load_corpus()
    body = (
        _client(issue_token)
        .post("/v1/assist/sale", json={"product_id": str(PIECE)})
        .json()
    )

    assert body["citations"]
    for citation in body["citations"]:
        document_slug, _, section_slug = citation["citation_id"].partition("#")
        document = corpus.document(document_slug)
        assert document is not None, citation["citation_id"]
        section = document.section(section_slug)
        assert section is not None, citation["citation_id"]
        assert citation["document_title"] == document.title
        assert citation["section_title"] == section.title
        assert citation["claim_scope"] == section.claim_scope
        assert citation["doc_type"] == document.doc_type


def test_no_citation_points_at_a_product_or_at_the_catalogue(
    issue_token: Callable[..., str],
) -> None:
    client = _client(issue_token)

    for payload in ({"product_id": str(PIECE)}, {"query": "anillo de plata"}):
        body = client.post("/v1/assist/sale", json=payload).json()
        for citation in body["citations"]:
            assert not citation["citation_id"].startswith("catalog:"), payload
            assert str(FAMILY) not in citation["citation_id"], payload
            assert str(PIECE) not in citation["citation_id"], payload
