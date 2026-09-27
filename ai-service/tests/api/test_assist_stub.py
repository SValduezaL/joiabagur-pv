"""Sale assistance stub contract tests (no LLM / embeddings / RDS).

The fixture survives C30a — `STUB_MODE` is still the switch, and with stubs on the route
still serves a deterministic body with no external input or output. What changed is the
*shape* it serves, and two properties it must now hold that it did not before: a group with
**no family**, and warnings drawn from the **closed vocabulary** instead of a sentence.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from jbg_ai.api.schemas.assist import AssistResponse
from jbg_ai.api.schemas.common import PRICE_PLACEHOLDER, STOCK_PLACEHOLDER
from jbg_ai.assist.constants import (
    ASSIST_WARNING_CODES,
    INTENT_PRODUCT_PITCH,
    INTENT_UNCLASSIFIED,
)
from jbg_ai.knowledge.constants import CLAIM_SCOPE_GENERAL

#: Any bare number followed by a currency mark would mean Python resolved a price.
PRICE_LIKE = re.compile(r"\d+[.,]?\d*\s*(€|eur|euros)", re.IGNORECASE)


def test_assist_sale_groups_by_family(
    client: TestClient, auth_headers: dict[str, str], forbid_network: None
) -> None:
    response = client.post(
        "/v1/assist/sale",
        json={"query": "regalo para mi madre", "top_k": 3},
        headers=auth_headers,
    )

    assert response.status_code == 200
    parsed = AssistResponse.model_validate(response.json())

    assert parsed.groups
    for group in parsed.groups:
        assert group.members
        for member in group.members:
            # variant_label may be null, but the field is always part of the contract.
            assert "variant_label" in member.model_dump()
            assert "match_reasons" in member.model_dump()

    # No placeholders: this is the free-query mode. See
    # `test_stub_free_query_carries_no_placeholder` for why the double must not write them.
    assert PRICE_PLACEHOLDER not in parsed.pitch
    assert STOCK_PLACEHOLDER not in parsed.pitch


def test_stub_free_query_carries_no_placeholder(
    client: TestClient, auth_headers: dict[str, str], forbid_network: None
) -> None:
    """The double must teach the contract the real pipeline enforces, not a friendlier one.

    A placeholder reaching `PitchPlaceholderResolver` without an anchor makes it withhold the
    **whole** argument — by design, and fixed by a test on the .NET side. So a stub that wrote
    `{{price}}` for a free query would hand every client running against stubs an argument that
    the real path suppresses, and the first time anyone ran against the real service the prose
    would vanish with nothing in the diff to explain it.
    """
    body = client.post(
        "/v1/assist/sale",
        json={"query": "¿la plata se puede mojar?", "top_k": 2},
        headers=auth_headers,
    ).json()

    assert body["pitch"], "the free query still gets prose; it just names no figure"
    assert PRICE_PLACEHOLDER not in body["pitch"]
    assert STOCK_PLACEHOLDER not in body["pitch"]
    # And no resolved figure either, which would be the opposite mistake: Python owns neither
    # the price nor the stock, so a number here would be invented.
    assert not PRICE_LIKE.search(body["pitch"])


def test_stub_anchored_mode_still_carries_the_placeholders(
    client: TestClient, auth_headers: dict[str, str], forbid_network: None
) -> None:
    """The anchored modes are untouched: there the resolver has a piece to resolve against."""
    body = client.post(
        "/v1/assist/sale",
        json={"product_id": "11111111-1111-1111-1111-111111111111"},
        headers=auth_headers,
    ).json()

    assert PRICE_PLACEHOLDER in body["pitch"]
    assert STOCK_PLACEHOLDER in body["pitch"]


def test_assist_stub_exercises_the_absent_family(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """A fixture where every response had a family let a client ignore ~58 % of the catalogue."""
    body = client.post(
        "/v1/assist/sale",
        json={"query": "pendientes", "top_k": 5},
        headers=auth_headers,
    ).json()

    familyless = [group for group in body["groups"] if group["family_id"] is None]

    assert familyless, "the fixture must exercise the null family"
    for group in familyless:
        assert len(group["members"]) == 1


def test_assist_stub_never_groups_several_members_under_a_null_family(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for top_k in (1, 2, 5, 20):
        body = client.post(
            "/v1/assist/sale",
            json={"query": "anillo", "top_k": top_k},
            headers=auth_headers,
        ).json()

        for group in body["groups"]:
            if group["family_id"] is None:
                assert len(group["members"]) == 1, top_k


def test_assist_stub_warnings_belong_to_the_closed_vocabulary(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = client.post(
        "/v1/assist/sale", json={"query": "anillo", "top_k": 3}, headers=auth_headers
    ).json()

    assert body["warnings"]
    for warning in body["warnings"]:
        assert warning in ASSIST_WARNING_CODES, warning
        assert " " not in warning


def test_assist_stub_citations_resolve_and_carry_their_claim_scope(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = client.post(
        "/v1/assist/sale", json={"query": "anillo", "top_k": 3}, headers=auth_headers
    ).json()

    assert body["citations"]
    for citation in body["citations"]:
        document, _, section = citation["citation_id"].partition("#")
        assert document and section, citation["citation_id"]
        assert citation["document_title"]
        assert citation["section_title"]
        assert citation["doc_type"]
        assert citation["claim_scope"] == CLAIM_SCOPE_GENERAL


def test_assist_stub_intent_is_structural_and_not_a_keyword_guess(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """The fixture obeys the same rule the real path does, so a client learns one rule."""
    anchored = client.post(
        "/v1/assist/sale", json={"product_id": "P-0001", "top_k": 2}, headers=auth_headers
    ).json()
    asked = client.post(
        "/v1/assist/sale", json={"query": "un regalo", "top_k": 2}, headers=auth_headers
    ).json()
    both = client.post(
        "/v1/assist/sale",
        json={"product_id": "P-0001", "query": "un regalo", "top_k": 2},
        headers=auth_headers,
    ).json()

    assert anchored["intent"] == INTENT_PRODUCT_PITCH
    assert asked["intent"] == INTENT_UNCLASSIFIED
    assert both["intent"] == INTENT_UNCLASSIFIED


def test_assist_stub_declares_abstention_and_a_null_prompt_version(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = client.post(
        "/v1/assist/sale", json={"query": "anillo", "top_k": 2}, headers=auth_headers
    ).json()

    assert body["abstained"] is False
    assert body["prompt_version"] is None


def test_assist_sale_rejects_a_request_with_neither_anchor(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/v1/assist/sale", json={"top_k": 2}, headers=auth_headers)

    assert response.status_code == 422
    detail = str(response.json()["detail"])
    assert "product_id" in detail
    assert "query" in detail


def test_pitch_never_resolves_price_or_stock(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/assist/sale",
        json={"query": "anillo de compromiso", "top_k": 2},
        headers=auth_headers,
    )

    pitch = response.json()["pitch"]

    assert PRICE_LIKE.search(pitch) is None


def test_assist_asks_for_clarification_when_several_families_match(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/v1/assist/sale",
        json={"query": "pendientes", "top_k": 3},
        headers=auth_headers,
    )
    body = response.json()

    assert len(body["groups"]) > 1
    assert body["clarification_question"]


def test_assist_stub_is_deterministic(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {"query": "regalo para mi madre", "top_k": 2}

    first = client.post("/v1/assist/sale", json=payload, headers=auth_headers).json()
    second = client.post("/v1/assist/sale", json=payload, headers=auth_headers).json()

    assert first == second
