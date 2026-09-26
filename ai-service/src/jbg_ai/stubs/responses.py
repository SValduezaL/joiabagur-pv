"""Deterministic response builders for the frozen `/v1` contracts."""

from __future__ import annotations

from datetime import UTC, datetime

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.assist import (
    AgentAssistGroup,
    AgentAssistRequest,
    AgentAssistResponse,
    AgentUsage,
    AssistGroup,
    AssistGroupMember,
    AssistRequest,
    AssistResponse,
    Citation,
)
from jbg_ai.api.schemas.common import (
    PRICE_PLACEHOLDER,
    STOCK_PLACEHOLDER,
    DebugInfo,
    Usage,
)
from jbg_ai.api.schemas.enrich import (
    EnrichRequest,
    EnrichResponse,
    ProposedList,
    ProposedProfile,
    ProposedText,
)
from jbg_ai.api.schemas.enrich import (
    MAX_BATCH_SIZE as ENRICH_MAX_BATCH_SIZE,
)
from jbg_ai.api.schemas.families import (
    ExcludedProductModel,
    FamilyAuditRequest,
    FamilyAuditResponse,
    FamilyProposalModel,
    FamilySuggestRequest,
    FamilySuggestResponse,
    FlaggedMemberModel,
    OrphanCandidateModel,
    ProposedFamilyMember,
    RejectedGroupModel,
)
from jbg_ai.api.schemas.evals import EvalMetric, EvalRun, EvalRunsResponse
from jbg_ai.api.schemas.index import (
    IndexStatusResponse,
    IndexSyncRequest,
    IndexSyncResponse,
)
from jbg_ai.api.schemas.inventory import (
    InventoryProposal,
    InventoryProposeRequest,
    InventoryProposeResponse,
)
from jbg_ai.api.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    SimilaritySignals,
    SubstituteResult,
    SubstitutesRequest,
    SubstitutesResponse,
)
from jbg_ai.assist.constants import (
    GROUP_ORIGIN_CATALOGUE,
    INTENT_PRODUCT_PITCH,
    INTENT_UNCLASSIFIED,
    STOP_NO_CLIENT,
    WARNING_FAMILY_HAS_VARIANTS,
    WARNING_SIZE_LABEL_MISSING,
)
from jbg_ai.knowledge.constants import CLAIM_SCOPE_GENERAL

OVER_RETRIEVAL_FACTOR = 3
OVER_RETRIEVAL_CAP = 60
VARIANTS_PER_FAMILY = 3

STUB_WARNING = "stub_response: deterministic fixture, no model or index was called"

_MATERIALS_CYCLE: tuple[tuple[str, ...], ...] = (
    ("plata",),
    ("oro", "circonita"),
    ("acero",),
    ("plata", "perla"),
)
_VARIANT_CYCLE: tuple[str | None, ...] = ("18 mm", "20 mm", "22 mm", None)
_SIGNAL_CYCLE: tuple[str, ...] = ("coverage_gap", "demand_up", "slow_mover", "family_incomplete")

# Enrichment fixtures. The cycles have coprime-ish lengths on purpose so a batch
# covers combinations rather than repeating one shape.
_PIECE_TYPE_CYCLE: tuple[str, ...] = ("anillo", "collar", "pendiente", "pulsera")
_STONE_TYPE_CYCLE: tuple[str | None, ...] = (None, "circonita", None, "perla", "ninguna")
_SIZE_LABEL_CYCLE: tuple[str, ...] = ("S", "M", "L")
_COLOR_TAG_CYCLE: tuple[tuple[str, ...], ...] = (("dorado",), ("plateado",), ("dorado", "blanco"))

# Straddles any plausible auto-approval threshold, so a batch exercises both the
# auto-approved and the sent-to-review branches of the consuming policy.
_TAG_CONFIDENCE_CYCLE: tuple[float, ...] = (0.92, 0.45, 0.87, 0.63)

#: Stubs run no prompt; the contract still requires the field, and a value that
#: says so is more honest than a plausible-looking version number.
STUB_PROMPT_VERSION = "stub"

# Fixed instants: a clock call would break determinism and the snapshot contract.
_LAST_FULL_SYNC_AT = datetime(2026, 8, 1, 3, 0, tzinfo=UTC)
_LAST_INCREMENTAL_SYNC_AT = datetime(2026, 8, 5, 3, 0, tzinfo=UTC)
_NEXT_CURSOR = datetime(2026, 8, 5, 3, 30, tzinfo=UTC)


def over_retrieval_count(top_k: int) -> int:
    """Candidates the retriever produces for a requested page size (design v3 §7.6)."""
    return min(top_k * OVER_RETRIEVAL_FACTOR, OVER_RETRIEVAL_CAP)


def _materials(index: int) -> list[str]:
    return list(_MATERIALS_CYCLE[index % len(_MATERIALS_CYCLE)])


def _variant_label(index: int) -> str | None:
    """Some variants are unknown on purpose so clients handle the null case."""
    return _VARIANT_CYCLE[index % len(_VARIANT_CYCLE)]


def _family_id(index: int) -> str | None:
    """Every seventh product has no family yet, mirroring an incomplete catalog."""
    if index % 7 == 0:
        return None
    return f"F-{index // VARIANTS_PER_FAMILY:03d}"


def _score(index: int) -> float:
    return round(max(0.99 - index * 0.01, 0.01), 4)


def _result(index: int, query: str) -> RetrievalResult:
    score = _score(index)
    return RetrievalResult(
        product_id=f"P-{index:04d}",
        sku=f"JBG-{index:04d}",
        score=score,
        match_reasons=[f"term_match:{query.strip()[:40]}", "material_match"],
        materials=_materials(index),
        family_id=_family_id(index),
        variant_label=_variant_label(index),
        debug=DebugInfo(
            vector_score=score,
            lexical_score=round(score * 0.8, 4),
            rerank_score=None,
            notes=["stub"],
        ),
    )


def _is_low_confidence(query: str) -> bool:
    return len(query.strip()) < 3


def retrieval_products_stub(
    request: RetrievalRequest, principal: ServicePrincipal
) -> RetrievalResponse:
    count = over_retrieval_count(request.top_k)
    results = [_result(index, request.query) for index in range(count)]
    return RetrievalResponse(
        results=results,
        candidates_returned=count,
        low_confidence=_is_low_confidence(request.query),
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )


def retrieval_substitutes_stub(
    request: SubstitutesRequest, principal: ServicePrincipal
) -> SubstitutesResponse:
    count = over_retrieval_count(request.top_k)
    results: list[SubstituteResult] = []
    for index in range(count):
        base = _result(index, request.product_id)
        results.append(
            SubstituteResult(
                **base.model_dump(),
                similarity_signals=SimilaritySignals(
                    material_overlap=round(0.9 - index * 0.01, 4),
                    style_similarity=round(0.85 - index * 0.01, 4),
                    visual_similarity=None,
                    family_match=base.family_id is not None,
                ),
            )
        )
    return SubstitutesResponse(
        results=results,
        candidates_returned=count,
        low_confidence=False,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )


#: Which fixture group has no family. **Every fourth, and the first of them is real
#: coverage and not decoration**: a fixture where every response carries a family lets a
#: client ship without ever handling the null case, and that case is ~58 % of the catalogue.
#: The same reasoning `families_suggest_stub` and `families_audit_stub` wrote into their own
#: code when they populated every list — "a stub that only returned proposals would let a
#: client ship without ever handling the two kinds of refusal".
_ASSIST_FAMILYLESS_EVERY = 4

#: Sections of the corpus the fixture cites. Real slugs of real files, so a client that
#: follows a `citation_id` from the fixture lands where it would land in production.
_ASSIST_CITATION_CYCLE: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "material-plata",
        "Plata",
        "cuidados-y-limpieza-en-casa",
        "Cuidados y limpieza en casa",
        "material",
    ),
    (
        "material-plata",
        "Plata",
        "piel-sensible-y-alergias",
        "Piel sensible y alergias",
        "material",
    ),
    (
        "tallas-anillos",
        "Tallas de anillo",
        "de-la-talla-espanola-a-los-milimetros",
        "De la talla española a los milímetros",
        "talla",
    ),
)


def _assist_group(index: int) -> AssistGroup:
    """Every fourth group carries no family, and then it carries exactly one member."""
    familyless = index % _ASSIST_FAMILYLESS_EVERY == 0
    size = 1 if familyless else VARIANTS_PER_FAMILY
    members = [
        AssistGroupMember(
            product_id=f"P-{index:03d}-{member:02d}",
            sku=f"JBG-{index:03d}{member:02d}",
            variant_label=_variant_label(member),
            materials=_materials(index + member),
            score=_score(index * VARIANTS_PER_FAMILY + member),
            match_reasons=["vector", "lexical"] if member % 2 == 0 else ["vector"],
        )
        for member in range(size)
    ]
    return AssistGroup(
        family_id=None if familyless else f"F-{index:03d}",
        family_label=None if familyless else f"Familia {index:03d}",
        members=members,
    )


def _assist_citation(index: int, product_id: str) -> Citation:
    document_slug, document_title, section_slug, section_title, doc_type = (
        _ASSIST_CITATION_CYCLE[index % len(_ASSIST_CITATION_CYCLE)]
    )
    return Citation(
        citation_id=f"{document_slug}#{section_slug}",
        document_title=document_title,
        section_title=section_title,
        doc_type=doc_type,
        # `general` throughout: the fixture must not model a commitment of the house as if
        # it were routine, and the mode that cites without being asked admits only `general`.
        claim_scope=CLAIM_SCOPE_GENERAL,
        score=_score(index),
        snippet=f"Fragmento de «{section_title}» en «{document_title}».",
        product_id=product_id,
    )


def assist_sale_stub(request: AssistRequest, principal: ServicePrincipal) -> AssistResponse:
    """The fixture, adjusted to the contract C30a moved. Still a pure function of its input.

    `warnings` carries **codes of the closed vocabulary** and no longer a sentence: the
    invariant is that every warning any response emits belongs to that vocabulary, and a
    fixture exempt from it would be the one response a client learns the wrong shape from.
    `intent` obeys the same structural rule the real path does, for the same reason.
    """
    groups = [_assist_group(index) for index in range(request.top_k)]
    anchored = request.product_id is not None and request.query is None
    intent = INTENT_PRODUCT_PITCH if anchored else INTENT_UNCLASSIFIED
    subject = request.query.strip() if request.query else f"la pieza {request.product_id}"

    # **The free-query mode emits no placeholders, and the double has to say so too.**
    # `PitchPlaceholderResolver` on the .NET side withholds the whole argument whenever a
    # placeholder reaches it without an anchor to resolve against — by design, and with a test
    # fixing it. So a stub that wrote them here would hand every client running against stubs an
    # argument that the real pipeline would suppress: the double would be teaching the wrong
    # contract, which is the one thing a double must never do.
    #
    # Comparative language without a figure stays allowed, and is what the free-query prompt
    # asks for; there is simply no price and no quantity to name when no piece is anchored.
    pitch = (
        f"Para «{subject}» te encajan {len(groups)} familias. "
        f"Precio {PRICE_PLACEHOLDER} y quedan {STOCK_PLACEHOLDER} unidades en tu punto de venta."
        if request.product_id is not None
        else (
            f"Para «{subject}» te encajan {len(groups)} familias. "
            "Tienes la lista con precios y existencias delante."
        )
    )
    citations = [
        _assist_citation(index, group.members[0].product_id)
        for index, group in enumerate(groups)
    ]
    warnings = [WARNING_SIZE_LABEL_MISSING]
    if any(len(group.members) > 1 for group in groups):
        warnings.insert(0, WARNING_FAMILY_HAS_VARIANTS)
    return AssistResponse(
        intent=intent,
        groups=groups,
        pitch=pitch,
        citations=citations,
        warnings=warnings,
        clarification_question=(
            "¿Prefieres alguna de estas familias en concreto?" if len(groups) > 1 else None
        ),
        usage=Usage(),
        abstained=False,
        prompt_version=None,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )


def inventory_propose_stub(
    request: InventoryProposeRequest, principal: ServicePrincipal
) -> InventoryProposeResponse:
    proposals = [
        InventoryProposal(
            product_id=f"P-{index:04d}",
            sku=f"JBG-{index:04d}",
            family_id=_family_id(index),
            variant_label=_variant_label(index),
            priority=index + 1,
            signal=_SIGNAL_CYCLE[index % len(_SIGNAL_CYCLE)],
            rationale=(
                f"Cobertura ajustada para los próximos {request.horizon_days} días; "
                f"quedan {STOCK_PLACEHOLDER} unidades."
            ),
            confidence=round(max(0.9 - index * 0.05, 0.1), 4),
        )
        for index in range(request.limit)
    ]
    return InventoryProposeResponse(
        proposals=proposals,
        horizon_days=request.horizon_days,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )


def enrich_products_stub(request: EnrichRequest, principal: ServicePrincipal) -> EnrichResponse:
    """Proposed profiles that exercise both provenances and both sides of a threshold.

    The variety is the point, not decoration. A fixture where every sensitive field
    is inferred would let a broken review policy pass its own tests: routing to
    review is what such a policy does by default, so it would never be caught
    exempting nothing. The cycles below guarantee that any batch of four products
    contains at least one `rule` field, at least one `inferred` sensitive field,
    and tags on both sides of a plausible auto-approval threshold.
    """
    profiles: list[ProposedProfile] = []
    for index, product in enumerate(request.products):
        materials = _materials(index)
        title = (product.name or f"Pieza {product.sku}").strip()

        # Every fourth piece has its size read off the SKU by a deterministic rule,
        # mirroring what the real pipeline does before calling a model at all.
        size_is_rule = index % 4 == 0
        tag_confidence = _TAG_CONFIDENCE_CYCLE[index % len(_TAG_CONFIDENCE_CYCLE)]

        profiles.append(
            ProposedProfile(
                product_id=product.product_id,
                sku=product.sku,
                title=ProposedText(value=title, confidence=0.81, source="inferred"),
                description=ProposedText(
                    value=f"{title} en {', '.join(materials)}.",
                    confidence=0.64,
                    source="inferred",
                ),
                piece_type=ProposedText(
                    value=_PIECE_TYPE_CYCLE[index % len(_PIECE_TYPE_CYCLE)],
                    confidence=0.88,
                    source="inferred",
                ),
                materials=ProposedList(value=materials, confidence=0.72, source="inferred"),
                stone_type=(
                    ProposedText(value=stone, confidence=0.61, source="inferred")
                    if (stone := _STONE_TYPE_CYCLE[index % len(_STONE_TYPE_CYCLE)]) is not None
                    else None
                ),
                size_label=(
                    ProposedText(
                        value=_SIZE_LABEL_CYCLE[index % len(_SIZE_LABEL_CYCLE)],
                        confidence=1.0 if size_is_rule else 0.57,
                        source="rule" if size_is_rule else "inferred",
                    )
                ),
                color_tags=ProposedList(
                    value=list(_COLOR_TAG_CYCLE[index % len(_COLOR_TAG_CYCLE)]),
                    confidence=tag_confidence,
                    source="inferred",
                ),
                style_tags=ProposedList(
                    value=["marino", "verano"], confidence=tag_confidence, source="inferred"
                ),
                occasion_tags=ProposedList(
                    value=["regalo"], confidence=tag_confidence, source="inferred"
                ),
                family_id=ProposedText(
                    value=f"F-{index // VARIANTS_PER_FAMILY:03d}",
                    confidence=0.55,
                    source="inferred",
                ),
                variant_label=(
                    ProposedText(value=variant, confidence=0.58, source="inferred")
                    if (variant := _variant_label(index)) is not None
                    else None
                ),
                warnings=[STUB_WARNING],
            )
        )
    return EnrichResponse(
        profiles=profiles,
        usage=Usage(),
        prompt_version=STUB_PROMPT_VERSION,
        trace_id=principal.trace_id,
    )


def index_sync_stub(request: IndexSyncRequest, principal: ServicePrincipal) -> IndexSyncResponse:
    is_full = request.full or request.since is None
    return IndexSyncResponse(
        upserted=120 if is_full else 12,
        skipped=0 if is_full else 8,
        deleted=0,
        failed=0,
        since=request.since,
        since_id=request.since_id,
        cursor=_NEXT_CURSOR,
        cursor_id=None,
        trace_id=principal.trace_id,
    )


def index_status_stub(principal: ServicePrincipal) -> IndexStatusResponse:
    return IndexStatusResponse(
        indexed_documents=1500,
        drift_count=3,
        last_full_sync_at=_LAST_FULL_SYNC_AT,
        last_incremental_sync_at=_LAST_INCREMENTAL_SYNC_AT,
        trace_id=principal.trace_id,
    )


def evals_runs_stub(principal: ServicePrincipal) -> EvalRunsResponse:
    return EvalRunsResponse(
        runs=[
            EvalRun(
                run_id="run-0001",
                suite="retrieval-golden-set",
                status="passed",
                started_at=datetime(2026, 8, 4, 10, 0, tzinfo=UTC),
                finished_at=datetime(2026, 8, 4, 10, 4, tzinfo=UTC),
                metrics=[
                    EvalMetric(name="recall_at_10", value=0.82),
                    EvalMetric(name="mrr", value=0.61),
                ],
            ),
            EvalRun(
                run_id="run-0002",
                suite="assist-generation",
                status="failed",
                started_at=datetime(2026, 8, 5, 10, 0, tzinfo=UTC),
                finished_at=datetime(2026, 8, 5, 10, 7, tzinfo=UTC),
                metrics=[EvalMetric(name="grounding_rate", value=0.74)],
            ),
        ],
        trace_id=principal.trace_id,
    )


def families_suggest_stub(
    request: FamilySuggestRequest, principal: ServicePrincipal
) -> FamilySuggestResponse:
    """One proposal, one refused group and one excluded product.

    All three lists are populated on purpose. A stub that only returned proposals
    would let a client ship without ever handling the two kinds of refusal, and
    those are where the catalogue problems surface.
    """
    piece_type = request.piece_type or "anillo"
    return FamilySuggestResponse(
        proposals=[
            FamilyProposalModel(
                root="anillo erizo de mar",
                suggested_name="Anillo erizo de mar",
                piece_type=piece_type,
                members=[
                    ProposedFamilyMember(
                        product_id="11111111-1111-1111-1111-111111111111",
                        sku="SKU-STUB-1",
                        name="Anillo erizo de mar S",
                        variant_label="S",
                        position=0,
                    ),
                    ProposedFamilyMember(
                        product_id="22222222-2222-2222-2222-222222222222",
                        sku="SKU-STUB-2",
                        name="Anillo erizo de mar M",
                        variant_label="M",
                        position=1,
                        flagged_for_review=True,
                        review_reason="closer_to_another_family",
                        margin=0.12,
                    ),
                ],
            )
        ],
        rejected_groups=[
            RejectedGroupModel(
                root="encargos",
                piece_type="collar",
                reason="root_too_short",
                product_names=["Encargos Oro", "Encargos plata"],
            )
        ],
        excluded_products=[
            ExcludedProductModel(
                product_id="33333333-3333-3333-3333-333333333333",
                sku="SKU-STUB-3",
                name="Vela Cerámica grande",
                reason="no_piece_type",
            )
        ],
        already_in_family_count=0,
        trace_id=principal.trace_id,
    )


def families_audit_stub(
    request: FamilyAuditRequest, principal: ServicePrincipal
) -> FamilyAuditResponse:
    """One flagged member, one orphan candidate, and both kinds of refusal.

    Every list is populated for the same reason `families_suggest_stub` populates
    all three of its own: a stub that returned only the findings would let a client
    ship without ever rendering a refusal, and those are where the catalogue problems
    surface. The orphan carries a purity of 2 against a margin that nominated it, so
    a client cannot quietly start treating purity as the criterion.

    `judged_pairs` is honoured here too. A stub that ignored it would let the
    dismissal path ship untested against the one behaviour it exists for.
    """
    judged = {(pair.product_id.lower(), pair.family_id.lower()) for pair in request.judged_pairs}
    flagged = [
        FlaggedMemberModel(
            product_id="22222222-2222-2222-2222-222222222222",
            sku="SKU-STUB-2",
            name="Anillo erizo de mar M",
            variant_label="M",
            family_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            family_name="Anillo erizo de mar",
            margin=0.12,
            stranger_family_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )
    ]
    orphans = [
        OrphanCandidateModel(
            product_id="44444444-4444-4444-4444-444444444444",
            sku="SKU-STUB-4",
            name="Anillo erizo de mar XL dorado",
            piece_type=request.piece_type or "anillo",
            data_origin="real",
            family_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            family_name="Anillo erizo de mar",
            similarity=0.941,
            worst_sibling=0.874,
            margin=0.067,
            purity=2,
        )
    ]
    return FamilyAuditResponse(
        flagged_members=[
            member
            for member in flagged
            if (member.product_id.lower(), member.family_id.lower()) not in judged
        ],
        orphan_candidates=[
            orphan
            for orphan in orphans
            if (orphan.product_id.lower(), orphan.family_id.lower()) not in judged
        ][: request.max_orphans],
        rejected_groups=[
            RejectedGroupModel(
                root="alianzas",
                piece_type="anillo",
                reason="root_too_short",
                product_names=["Alianzas Plata", "Alianzas oro"],
            )
        ],
        excluded_products=[
            ExcludedProductModel(
                product_id="33333333-3333-3333-3333-333333333333",
                sku="SKU-STUB-3",
                name="Diadema perlas",
                reason="no_piece_type",
            )
        ],
        families_reviewed_count=1,
        members_examined_count=2,
        trace_id=principal.trace_id,
    )


def assist_agent_stub(
    request: AgentAssistRequest, principal: ServicePrincipal
) -> AgentAssistResponse:
    """The agent route's fixture. Still a pure function of its input, and still no loop.

    **This route declares stub behaviour because every `/v1` route does**, and being the one
    exception would be the thing a client discovers in integration. So the body has the
    shape a client renders — groups, citations and an argument with the two placeholders —
    as the stub of `POST /v1/assist/sale` does. What it does not pretend is a loop: the stub
    runs none and calls no provider, so the trace has **zero iterations** and the stop reason
    is the one that says the loop did not run — the one a deployment with no agent credential
    reports, because it is the same fact. `partial: true` follows from that, for the reason
    the credential-less path gives: no loop gathered the evidence this body shows.

    **The warnings are the ones this route can emit, which here is none.** The route reports
    a refusal code on a refusal and nothing else; the two rule-derived warnings of C30a are
    statements about an anchored piece this route does not read. The first form of this stub
    emitted both, so a client integrating against it would have handled codes that never
    arrive — found by the independent verification of C32b.
    """
    answered = next(
        (turn.text for turn in reversed(request.turns) if turn.role == "operario"),
        request.turns[-1].text,
    )
    # **Every group is a catalogue match here, and that is not a shortcut.** The stub runs no
    # loop — `iterations: 0`, and the stop reason says so — so no tool ran, and a group marked
    # as a substitute would claim `buscar_sustitutos` was invoked. The shape a client renders
    # is the field being present and carrying a value of the closed vocabulary; pretending a
    # pivot would be the same mistake the first form of this stub made with the two warnings.
    groups = [
        AgentAssistGroup(**_assist_group(index).model_dump(), origin=GROUP_ORIGIN_CATALOGUE)
        for index in range(request.top_k)
    ]
    citations = [
        _assist_citation(index, group.members[0].product_id)
        for index, group in enumerate(groups)
    ]
    warnings: list[str] = []
    return AgentAssistResponse(
        intent=INTENT_UNCLASSIFIED,
        groups=groups,
        pitch=(
            f"Para «{answered}» te encajan {len(groups)} familias. "
            f"Precio {PRICE_PLACEHOLDER} y quedan {STOCK_PLACEHOLDER} unidades "
            "en tu punto de venta."
        ),
        citations=citations,
        warnings=warnings,
        clarification_question=None,
        usage=AgentUsage(),
        abstained=False,
        prompt_version=None,
        partial=True,
        stop_reason=STOP_NO_CLIENT,
        iterations=0,
        tool_calls_used=0,
        trace=[],
        agent_prompt_version=None,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )
