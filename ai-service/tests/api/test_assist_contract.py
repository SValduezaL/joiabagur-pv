"""The contract block C30a moved, field by field. No LLM, no embeddings, no RDS.

These are tests of the *models*, not of the route: what they guard is that the shape the
.NET side will be handed says what the change says it says. The route's behaviour lives in
`tests/assist/` and in `tests/api/test_assist_real.py`.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from jbg_ai.api.schemas.assist import (
    AssistGroup,
    AssistGroupMember,
    AssistRequest,
    AssistResponse,
    Citation,
)
from jbg_ai.api.schemas.common import Usage
from jbg_ai.assist.constants import (
    ASSIST_INTENTS,
    ASSIST_REFUSAL_CODES,
    ASSIST_WARNING_CODES,
    WARNING_FAMILY_HAS_VARIANTS,
    WARNING_FILTERS_TOO_NARROW,
    WARNING_KNOWLEDGE_NOT_COVERED,
    WARNING_QUERY_NOT_IN_CATALOGUE,
    WARNING_QUERY_OUT_OF_DOMAIN,
    WARNING_SIZE_LABEL_MISSING,
)


def _member(**overrides) -> AssistGroupMember:
    values = {"product_id": "P-0001", "sku": "JBG-0001", "score": 0.9}
    values.update(overrides)
    return AssistGroupMember(**values)


def _citation(**overrides) -> Citation:
    values = {
        "citation_id": "material-plata#cuidados-y-limpieza-en-casa",
        "document_title": "Plata",
        "section_title": "Cuidados y limpieza en casa",
        "doc_type": "material",
        "claim_scope": "general",
        "score": 0.8,
        "snippet": "La plata se empaña con el aire.",
    }
    values.update(overrides)
    return Citation(**values)


# --- 3.1 · the request carries two independent anchors and needs at least one ------------


def test_assist_request_without_any_anchor_is_rejected_naming_both_fields() -> None:
    with pytest.raises(ValidationError) as error:
        AssistRequest()

    message = str(error.value)
    assert "product_id" in message
    assert "query" in message
    assert "at least one" in message


def test_assist_request_accepts_each_anchor_on_its_own_and_both_together() -> None:
    assert AssistRequest(query="¿se puede mojar?").product_id is None
    assert AssistRequest(product_id="P-0001").query is None

    both = AssistRequest(product_id="P-0001", query="¿se puede mojar?")

    assert both.product_id == "P-0001"
    assert both.query == "¿se puede mojar?"


def test_assist_request_keeps_query_optional_but_still_rejects_an_empty_string() -> None:
    """Optional is not the same as blank: a caller that sent `""` meant to ask something."""
    with pytest.raises(ValidationError):
        AssistRequest(query="")


# --- 3.2 · a group may have no family ---------------------------------------------------


def test_assist_group_accepts_a_null_family_id() -> None:
    group = AssistGroup(family_id=None, members=[_member()])

    assert group.family_id is None
    assert len(group.members) == 1


def test_assist_group_family_id_defaults_to_null_rather_than_being_required() -> None:
    """~58 % of the catalogue has no family; requiring the field priced that majority out."""
    assert AssistGroup(members=[_member()]).family_id is None


# --- 3.3 · members carry the reasons the retrieval recorded -----------------------------


def test_assist_group_member_defaults_match_reasons_to_an_empty_list() -> None:
    assert _member().match_reasons == []


def test_assist_group_member_carries_the_retrieval_vocabulary_verbatim() -> None:
    member = _member(match_reasons=["vector", "lexical"])

    assert member.match_reasons == ["vector", "lexical"]


# --- 3.4 · the citation is reformed -----------------------------------------------------


def test_citation_exposes_its_six_new_fields() -> None:
    citation = _citation()

    assert citation.citation_id == "material-plata#cuidados-y-limpieza-en-casa"
    assert citation.document_title == "Plata"
    assert citation.section_title == "Cuidados y limpieza en casa"
    assert citation.doc_type == "material"
    assert citation.claim_scope == "general"
    assert citation.score == 0.8


@pytest.mark.parametrize(
    "field",
    ["citation_id", "document_title", "section_title", "doc_type", "claim_scope", "score"],
)
def test_citation_requires_every_new_field(field: str) -> None:
    values = _citation().model_dump()
    del values[field]

    with pytest.raises(ValidationError):
        Citation(**values)


def test_citation_product_id_is_the_one_optional_field() -> None:
    """`MAY expose the product_id it supports` — the piece a claim is about, never its source."""
    assert _citation().product_id is None
    assert _citation(product_id="P-0001").product_id == "P-0001"


def test_citation_no_longer_carries_a_free_text_source() -> None:
    """`source` is gone: it held a slug and lost the document and section titles with it."""
    assert "source" not in Citation.model_fields


# --- 3.5 · the response declares abstention and prompt provenance ------------------------


def _response(**overrides) -> AssistResponse:
    values = {
        "intent": "unclassified",
        "groups": [],
        "pitch": "",
        "usage": Usage(),
        "abstained": False,
        "trace_id": "t",
        "effective_pos_id": "b0000000-0000-4000-8000-000000000002",
    }
    values.update(overrides)
    return AssistResponse(**values)


def test_assist_response_requires_abstained() -> None:
    values = _response().model_dump()
    del values["abstained"]

    with pytest.raises(ValidationError):
        AssistResponse(**values)


def test_assist_response_prompt_version_defaults_to_null() -> None:
    assert _response().prompt_version is None
    assert _response(prompt_version="assist/v1").prompt_version == "assist/v1"


def test_assist_response_does_not_reuse_low_confidence_for_abstention() -> None:
    """D9: that name already means cross-branch consensus, which is anti-correlated."""
    assert "low_confidence" not in AssistResponse.model_fields
    assert "abstained" in AssistResponse.model_fields


# --- 3.6 · the warning vocabulary is closed ----------------------------------------------


def test_warning_vocabulary_holds_the_two_rule_codes_and_the_three_of_the_router() -> None:
    """C30a's two are first and unchanged; C31 stacked three on top and C40 a sixth.

    The two refusal codes are **distinct from each other**, which is D1 stated as an assertion:
    what an operator says to a customer differs between a trade the shop does not practise and
    a piece the shop does not carry, and one shared `refused` code would erase the distinction
    exactly where a consumer reads it.

    `filters_too_narrow` is **appended and never inserted**: the order of this tuple is what a
    consumer reads, and every code before it keeps the position it had.
    """
    assert ASSIST_WARNING_CODES[:2] == (
        WARNING_FAMILY_HAS_VARIANTS,
        WARNING_SIZE_LABEL_MISSING,
    )
    assert ASSIST_WARNING_CODES == (
        WARNING_FAMILY_HAS_VARIANTS,
        WARNING_SIZE_LABEL_MISSING,
        WARNING_QUERY_OUT_OF_DOMAIN,
        WARNING_QUERY_NOT_IN_CATALOGUE,
        WARNING_KNOWLEDGE_NOT_COVERED,
        WARNING_FILTERS_TOO_NARROW,
    )
    assert WARNING_QUERY_OUT_OF_DOMAIN != WARNING_QUERY_NOT_IN_CATALOGUE
    assert ASSIST_REFUSAL_CODES == (
        WARNING_QUERY_OUT_OF_DOMAIN,
        WARNING_QUERY_NOT_IN_CATALOGUE,
    )
    assert set(ASSIST_REFUSAL_CODES) <= set(ASSIST_WARNING_CODES)
    assert WARNING_FILTERS_TOO_NARROW not in ASSIST_REFUSAL_CODES, (
        "a narrow filter is not a refusal: the router admitted the query and retrieval ran"
    )


def test_no_warning_code_is_a_sentence_in_natural_language() -> None:
    for code in ASSIST_WARNING_CODES:
        assert " " not in code, code
        assert code == code.lower()


def test_the_two_stock_warnings_are_not_part_of_this_vocabulary() -> None:
    """They need real stock, which is .NET's after hydration. C34 emits them, not this."""
    assert "stock_critical" not in ASSIST_WARNING_CODES
    assert "family_members_out_of_stock" not in ASSIST_WARNING_CODES


def test_the_warnings_field_documents_the_closed_vocabulary() -> None:
    description = AssistResponse.model_fields["warnings"].description or ""

    for code in ASSIST_WARNING_CODES:
        assert code in description


# --- C31 · the contract moved in DESCRIPTIONS and in nothing else ---------------------------


def test_the_router_added_no_field_and_changed_no_type() -> None:
    """D4 and the sixth non-negotiable, pinned so a later change cannot move the shape quietly.

    The verification that produced `openapi.json` flattened both documents to leaves and
    compared them: **one leaf added — a `description` key on a field that had none — zero
    removed, zero types changed, `required` identical.** This is the half of it a suite can keep
    checking: `intent` is still a plain string, `clarification_question` still an optional one,
    and `warnings` still a list of strings, which is why the refusal code and the question
    needed no new field at all.
    """
    schema = AssistResponse.model_json_schema()
    properties = schema["properties"]

    assert properties["intent"]["type"] == "string"
    assert set(properties["warnings"]["items"]) == {"type"}
    assert properties["warnings"]["items"]["type"] == "string"
    assert properties["warnings"]["type"] == "array"
    # Optional prose, exactly as C30a declared it.
    assert {entry.get("type") for entry in properties["clarification_question"]["anyOf"]} == {
        "string",
        "null",
    }
    assert "clarification_question" not in schema["required"]
    assert "refusal_reason" not in properties
    assert "route" not in properties
    assert "missing_axis" not in properties


def test_the_intent_field_documents_its_closed_vocabulary() -> None:
    description = AssistResponse.model_fields["intent"].description or ""

    for value in ASSIST_INTENTS:
        assert value in description, value


def test_the_clarification_question_declares_that_no_model_writes_it() -> None:
    """The field is typed as prose, so the presentation layer cannot resolve it — which is why
    the contract has to say that the prose is nonetheless deterministic and code-chosen."""
    description = AssistResponse.model_fields["clarification_question"].description or ""

    assert "never written by the model" in description
    assert "same text" in description
