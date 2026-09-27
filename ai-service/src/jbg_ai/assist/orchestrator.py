"""One sale-assistance request, in whichever of the three modes it is. C30a, C30b, C31.

**All three modes can now write, and one of them is classified before it retrieves anything.**
The two anchored modes hand what this module has already assembled to the generation layer. The
free query is put to a classifier *first* — one call, before `retrieve_products` — and what
comes back decides whether the request is served at all, which index answers it, and which task
section writes it. An abstained request still calls no provider: writing confidently about an
empty candidate set is the failure the abstention rule exists to prevent, and that rule remains
in place as the net it has always been, **behind** the new gate rather than instead of it.

    M1  consulta sola      → CLASIFICAR, y entonces: rechazar · repreguntar · recuperar y redactar
    M2  pieza sola         → sin clasificador: no hay consulta que clasificar
    M3  pieza con pregunta → sin clasificador: `both` por construcción, y su guardarraíl es
                             el umbral de conocimiento que ya corre — cero citas, coste cero

Both clients are **injected and never built here**, like every other port this module takes.

* With no `pitch_client` the response is exactly C30a's — empty argument, absent prompt
  version — which is what makes the generation layer measurable as an ablation.
* With no `router_client` the free query is served exactly as C30b served it: the intent
  reports unclassified, both indexes are consulted, the abstention rule applies, and nothing
  is generated. That is the **fail-open**, and it is also the ablation and the rollback. It is
  a branch in `_task_of` and in the route check above it, never a swallowed exception.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.assist import (
    AssistGroup,
    AssistGroupMember,
    AssistRequest,
    AssistResponse,
    Citation,
)
from jbg_ai.api.schemas.common import Usage
from jbg_ai.api.schemas.retrieval import RetrievalRequest, RetrievalResult
from jbg_ai.assist.constants import (
    DEFAULT_MATERIAL_CAP,
    DEFAULT_PITCH_SECTIONS,
    FAMILY_ROSTER_CAP,
    MAX_PROVIDER_CALLS,
    WARNING_FAMILY_HAS_VARIANTS,
    WARNING_KNOWLEDGE_NOT_COVERED,
    WARNING_SIZE_LABEL_MISSING,
)
from jbg_ai.assist.errors import UnusableAnchorProductError
from jbg_ai.assist.grounding import ground_piece
from jbg_ai.assist.knowledge_scope import piece_scoped_exclusions
from jbg_ai.assist.llm import AssistLlm, TokenUsage
from jbg_ai.assist.modes import AssistMode, resolve_mode
from jbg_ai.assist.pitch import EMPTY_PITCH, PitchOutcome, generate_pitch
from jbg_ai.assist.prompt import (
    FreeQueryCandidate,
    FreeQueryGroup,
    PitchCitation,
    PitchTask,
    free_query_payload_from,
    payload_from,
    resolve_task,
)
from jbg_ai.assist.router_llm import RouterLlm
from jbg_ai.assist.routing import RoutingOutcome, classify_query
from jbg_ai.config.settings import Settings
from jbg_ai.indexing.embeddings import EmbeddingClient
from jbg_ai.knowledge.search import KnowledgeCitation, KnowledgeSearchIndex, search_knowledge
from jbg_ai.retrieval.orchestrator import retrieve_products
from jbg_ai.retrieval.ports import FamilyMember, ProductSearchPort, SourceDocument

logger = logging.getLogger(__name__)

STAGE = "assist"


def _require_usable(source: SourceDocument | None, product_id: str) -> SourceDocument:
    """Three unusable cases, three sentences. The C26 pattern, reused rather than restated."""
    if source is None:
        raise UnusableAnchorProductError(
            product_id, "it is not present in the retrieval index"
        )
    if not source.is_active:
        raise UnusableAnchorProductError(
            product_id, "it is present in the retrieval index but inactive"
        )
    if not source.has_embedding:
        raise UnusableAnchorProductError(
            product_id, "it is indexed but carries no embedding, so it cannot be assisted"
        )
    return source


def _parse_product_id(raw: str) -> UUID:
    try:
        return UUID(raw)
    except (ValueError, AttributeError) as exc:
        raise UnusableAnchorProductError(
            raw, "it is not a valid product identifier"
        ) from exc


def _member_from_roster(member: FamilyMember, *, score: float) -> AssistGroupMember:
    return AssistGroupMember(
        product_id=str(member.product_id),
        sku=member.sku,
        variant_label=member.variant_label,
        materials=list(member.materials),
        score=score,
        # The roster is an enumeration and not a retrieval: nothing matched, so there is no
        # reason to report. An invented one would be the decoration C30a exists to avoid.
        match_reasons=[],
    )


def _member_from_result(result: RetrievalResult) -> AssistGroupMember:
    return AssistGroupMember(
        product_id=result.product_id,
        sku=result.sku,
        variant_label=result.variant_label,
        materials=list(result.materials),
        score=result.score,
        match_reasons=list(result.match_reasons),
    )


def _group_results(results: Sequence[RetrievalResult]) -> list[AssistGroup]:
    """Group candidates by family, preserving rank, with *null family ⇒ one member*.

    The invariant is enforced structurally rather than asserted afterwards: candidates with
    no family never share a bucket, so no code path can produce the group the contract
    forbids. Order is the retrieval's — a group takes the position of its best member — so
    grouping never reorders what the ranking decided.
    """
    groups: list[AssistGroup] = []
    by_family: dict[str, AssistGroup] = {}
    for result in results:
        member = _member_from_result(result)
        if result.family_id is None:
            groups.append(AssistGroup(family_id=None, family_label=None, members=[member]))
            continue
        existing = by_family.get(result.family_id)
        if existing is None:
            group = AssistGroup(
                family_id=result.family_id, family_label=None, members=[member]
            )
            by_family[result.family_id] = group
            groups.append(group)
        else:
            existing.members.append(member)
    return groups


def _anchored_group(
    source: SourceDocument, roster: Sequence[FamilyMember]
) -> AssistGroup:
    """The group of the anchored piece: its family when it has one, itself when it does not."""
    if source.family_id is None or not roster:
        return AssistGroup(
            family_id=None,
            family_label=None,
            members=[
                AssistGroupMember(
                    product_id=str(source.product_id),
                    sku=source.sku,
                    variant_label=None,
                    materials=list(source.materials),
                    # The piece the caller named, at full score: it was not ranked against
                    # anything, it was asked for.
                    score=1.0,
                    match_reasons=[],
                )
            ],
        )
    label = next(
        (member.family_name for member in roster if member.family_name is not None), None
    )
    return AssistGroup(
        family_id=str(source.family_id),
        family_label=label,
        members=[_member_from_roster(member, score=1.0) for member in roster],
    )


def to_citation(
    citation: KnowledgeCitation, *, product_id: str | None
) -> Citation:
    return Citation(
        citation_id=citation.citation_id,
        document_title=citation.document_title,
        section_title=citation.section_title,
        doc_type=citation.doc_type,
        claim_scope=citation.claim_scope,
        score=min(max(citation.score, 0.0), 1.0),
        snippet=citation.content,
        product_id=product_id,
    )


def _warnings(
    *, size_label: str | None, roster_size: int, has_family: bool
) -> list[str]:
    """The two codes of the closed vocabulary, from data, by rule, in a stable order.

    `family_has_variants` reads the **roster** and never the candidate count: a family of
    four whose retrieval returned one still has four, and a warning computed from what came
    back would be silent exactly when the operator most needs it.

    There is no stock warning here and there is no place to add one: this service holds an
    availability bucket for ranking that can be minutes stale, and "critical stock" said out
    loud with twelve units in the drawer is the assistant's credibility at the counter. C34
    owns those two, after hydration.
    """
    codes: list[str] = []
    if has_family and roster_size > 1:
        codes.append(WARNING_FAMILY_HAS_VARIANTS)
    if not size_label:
        codes.append(WARNING_SIZE_LABEL_MISSING)
    return codes


async def assist_sale(
    payload: AssistRequest,
    principal: ServicePrincipal,
    *,
    settings: Settings,
    embed: EmbeddingClient,
    search: ProductSearchPort,
    knowledge: KnowledgeSearchIndex,
    pitch_client: AssistLlm | None = None,
    router_client: RouterLlm | None = None,
    abstain: bool | None = None,
    knowledge_distance_threshold: float | None = None,
    pitch_sections: Sequence[str] = DEFAULT_PITCH_SECTIONS,
    material_cap: int = DEFAULT_MATERIAL_CAP,
    roster_cap: int = FAMILY_ROSTER_CAP,
    citation_top_k: int = 5,
) -> AssistResponse:
    """Serve one request. Every configuration knob is a parameter, none is read here.

    `abstain` and `knowledge_distance_threshold` travel as arguments and `Settings` supplies
    only their defaults, so an evaluation can compare configurations **inside one process**
    without restarting anything — the pattern C20, C23 and C25 established and the one the
    abstention capability now requires of every consuming path.

    `payload.pos_id` is ignored on purpose: the scope is the token's, as everywhere in `/v1`.
    """
    mode = resolve_mode(product_id=payload.product_id, query=payload.query)
    threshold = (
        settings.jpv_knowledge_distance_threshold
        if knowledge_distance_threshold is None
        else knowledge_distance_threshold
    )
    # Stripped once and used for BOTH the retrieval and the knowledge search. Measured: the
    # embedding cache is keyed on a hash of the exact text, so a trailing space is a miss and
    # M3 would pay a second embedding for a difference nobody can see.
    question = (payload.query or "").strip()

    groups: list[AssistGroup] = []
    citations: tuple[KnowledgeCitation, ...] = ()
    abstained = False
    focus_source: SourceDocument | None = None
    roster: list[FamilyMember] = []
    uncovered = False
    #: What retrieval said about the query. Empty on every path that retrieves nothing — a
    #: refusal, a clarification, the anchored modes — which is correct: with no search there is
    #: no filter to have been too narrow.
    retrieval_warnings: list[str] = []

    # --- C31 · the entry guardrail -----------------------------------------------------
    #
    # **The classifier runs in M1 and only in M1, and it cuts before `retrieve_products`.**
    # M2 has no query to classify. M3 is `both` by construction — the piece is the catalogue
    # side and the question the corpus side — and refusing there would refuse a piece the
    # caller named explicitly, which is a statement about the request this service has not
    # established. Neither reaches this line, so "M2 and M3 make no classifier call" is a
    # property of the control flow rather than of a condition somewhere inside one.
    routing = RoutingOutcome()
    if mode is AssistMode.QUERY_ONLY:
        routing = await classify_query(
            question, client=router_client, trace_id=principal.trace_id
        )

    if mode.is_anchored:
        product_id = str(payload.product_id)
        focus_source = _require_usable(
            await search.source_document(_parse_product_id(product_id)), product_id
        )
        if focus_source.family_id is not None:
            roster = list(
                await search.family_roster(focus_source.family_id, cap=roster_cap)
            )
        groups = [_anchored_group(focus_source, roster)]

        if mode is AssistMode.PIECE_ONLY:
            # No vector search of any kind: the addresses are exact.
            citations = await ground_piece(
                focus_source.materials,
                index=knowledge,
                sections=pitch_sections,
                material_cap=material_cap,
            )
        else:
            citations = await search_knowledge(
                question,
                embed=embed,
                index=knowledge,
                top_k=citation_top_k,
                exclude_documents=piece_scoped_exclusions(focus_source.materials),
                distance_threshold=threshold,
                trace_id=principal.trace_id,
            )
            # **The deterministic guardrail of M3, and it costs nothing.** Zero citations
            # after the distance threshold already *means* the corpus does not cover the
            # question: C23 calibrated `0,51` on a clean gap of eight thousandths, with the
            # 32 questions the corpus answers below it and the 5 outsiders above. This reads
            # the result that was already computed — no second search, no provider call —
            # and turns it into something a consumer can act on. Until now M3 generated
            # identically with no citations and nobody could tell the two cases apart.
            uncovered = not citations
    elif routing.short_circuits:
        # **The refusal and the clarification cut here: before any retrieval runs.** Not
        # after, and not concurrently with it — 129 ms of retrieval does not buy breaking a
        # property whose whole value is that the guardrail is visibly prior. Nothing is
        # retrieved, nothing is searched, and no provider writes anything.
        pass
    else:
        # `route` is None exactly when the classifier could not be used, and then both
        # indexes are consulted — which is what this mode did before it routed anything.
        # The fail-open is this line and the `None` branches below it, not an `except`.
        route = routing.route
        if route in (None, "catalog", "both"):
            decisions: list[bool] = []
            # The filters travel only here, in the free-query branch. The anchored branch
            # retrieves the piece's family by identity, so a catalog filter would have
            # nothing to narrow and could only contradict the anchor the caller gave.
            retrieved = await retrieve_products(
                RetrievalRequest(
                    query=question, top_k=payload.top_k, filters=payload.filters
                ),
                principal,
                settings=settings,
                embed=embed,
                search=search,
                abstain=abstain,
                on_abstention=decisions.append,
            )
            abstained = bool(decisions and decisions[-1])
            # Retrieval's own codes about the QUERY, which is where the narrow-filter
            # statement is decided: it needs the unfiltered probe, and the probe lives
            # there. Carried rather than recomputed, so the generative route and the plain
            # one cannot drift into saying different things about the same search.
            retrieval_warnings = list(retrieved.warnings)
            if not abstained:
                groups = _group_results(retrieved.results)
        if not abstained and route in (None, "knowledge", "both"):
            citations = await search_knowledge(
                question,
                embed=embed,
                index=knowledge,
                top_k=citation_top_k,
                distance_threshold=threshold,
                trace_id=principal.trace_id,
            )
            # **The guardrail M3 has had since C34, finally applied to M1.** Reads the result
            # already computed — no second search and no provider call — exactly as the
            # anchored branch does above.
            #
            # Only on the two routes that asked the corpus a question. On `catalog` an empty
            # citation list is the normal and correct state rather than a gap: that route is
            # answered from pieces, and its own task section already tells the model to return
            # no citations. Reporting "the documentation does not cover this" for a query that
            # never asked the documentation anything would be a warning about nothing.
            if route in ("knowledge", "both"):
                uncovered = not citations
        if groups:
            # The warnings describe the piece the response leads with. Reading the focus
            # piece costs one primary-key lookup and is the same read the anchored modes
            # make, which is why `size_label` never has to be smuggled out of the retrieval
            # orchestrator: the port already answers this question.
            focus_source = await _focus_of(groups, search=search)
            if focus_source is not None and focus_source.family_id is not None:
                roster = list(
                    await search.family_roster(focus_source.family_id, cap=roster_cap)
                )

    warnings = (
        _warnings(
            size_label=focus_source.size_label,
            roster_size=len(roster),
            has_family=focus_source.family_id is not None,
        )
        if focus_source is not None
        else []
    )
    # The codes the router and the coverage guardrail add, after the rule-derived ones and
    # in a stable order. Two distinct refusal codes and never one, because what an operator
    # says to a customer differs between a trade the shop does not practise and a piece the
    # shop does not carry.
    warnings += list(routing.refusal_codes)
    warnings += retrieval_warnings
    if uncovered:
        warnings.append(WARNING_KNOWLEDGE_NOT_COVERED)
    anchored_id = str(payload.product_id) if mode.is_anchored else None

    # The cuts, **before** any generation call. An abstained request: writing confidently
    # about an empty candidate set is the failure the abstention rule exists to prevent. A
    # refused one or one answered with a question: there is nothing to write about, and the
    # Spanish a human reads for either belongs to the presentation layer. And a free query
    # with **no decided route**, which is the fail-open: with no usable classification this
    # mode serves exactly the response it served before this capability routed anything.
    outcome: PitchOutcome | None = None
    task = _task_of(mode, routing, uncovered=uncovered)
    if pitch_client is not None and task is not None and not abstained:
        outcome = await generate_pitch(
            _pitch_payload(
                focus_source, roster, citations, warnings=warnings, question=question
            )
            if mode.is_anchored
            else _free_query_payload(
                groups, citations, warnings=warnings, question=question
            ),
            task,
            client=pitch_client,
        )
        if not outcome.withheld:
            # The citations of a response carrying an argument are the ones the argument
            # **used and that verified**. When it was withheld they stay the ones that
            # grounded the response: a degraded response must never be poorer than the one
            # the structured layer produces on its own, which is what keeps the ablation
            # comparable — same route, same candidates, same citations, with prose and
            # without it.
            citations = _cited(citations, outcome.used_citation_ids)

    usage = _usage(routing, outcome)
    if usage.calls > MAX_PROVIDER_CALLS:  # pragma: no cover — structurally impossible
        raise AssertionError(
            f"the provider was called {usage.calls} times for one request; "
            f"the ceiling is {MAX_PROVIDER_CALLS}"
        )
    intent = routing.intent if mode is AssistMode.QUERY_ONLY else mode.intent

    logger.info(
        "stage=%s trace_id=%s mode=%s intent=%s route=%s router_degraded=%s "
        "router_cause=%s router_ms=%.1f task=%s groups=%s members=%s warnings=%s "
        "citations=%s abstained=%s roster=%s threshold=%s prompt_version=%s model=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s provider_calls=%s "
        "pitch_ms=%.1f pitch_chars=%s pitch_sha256=%s violations=%s withdrawn=%s "
        "provider_error=%s",
        STAGE,
        principal.trace_id,
        mode.value,
        intent,
        # The route, the degradation and its cause — never the query. A log line is durable
        # storage outside the database, and the operator's text is the one thing here that a
        # customer said out loud. Nothing of the routing decision is persisted either: the
        # evaluation harness is the declared exception and it writes its own files.
        routing.route or "none",
        routing.degraded,
        routing.degraded_cause or "none",
        routing.elapsed_ms,
        task.value if task is not None else "none",
        len(groups),
        sum(len(group.members) for group in groups),
        ",".join(warnings) or "none",
        ",".join(citation.citation_id for citation in citations) or "none",
        abstained,
        len(roster),
        threshold,
        # Everything of the generation **except the argument itself**: the version, the model,
        # what it cost, how long it took, which citations it used, why anything was refused,
        # how long the text is and a hash of it. A log line is durable storage outside the
        # database and carries no point-of-sale scope, while the response does; the text is
        # re-derivable from a versioned prompt at temperature zero, which is what makes not
        # storing it viable rather than merely cautious.
        outcome.prompt_version if outcome is not None else None,
        outcome.usage.model if outcome is not None else None,
        # The totals of the WHOLE request, classifier included: `provider_calls` is the
        # observable side of the ceiling of three, and a count that left the router out
        # would say two on a request that made three.
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
        usage.calls,
        outcome.elapsed_ms if outcome is not None else 0.0,
        len(outcome.pitch) if outcome is not None else 0,
        outcome.digest if outcome is not None else "none",
        ",".join(outcome.causes()) if outcome is not None and outcome.violations else "none",
        ",".join(outcome.withdrawn_citation_ids)
        if outcome is not None and outcome.withdrawn_citation_ids
        else "none",
        outcome.provider_error if outcome is not None else None,
        extra={"trace_id": principal.trace_id},
    )

    return AssistResponse(
        intent=intent,
        groups=groups,
        pitch=outcome.pitch if outcome is not None else EMPTY_PITCH,
        citations=[to_citation(item, product_id=anchored_id) for item in citations],
        warnings=warnings,
        # Prose, and the **only** prose in this response no model wrote: the contract types
        # this field as a sentence rather than as a code, so the presentation layer cannot
        # resolve it the way it resolves warnings. Chosen in code from a closed catalogue
        # keyed on the axis the classifier reported missing, which keeps it deterministic
        # without moving the type — and keeps a figure nobody checked out of the one field
        # no numeric gate inspects.
        clarification_question=routing.clarification_question,
        usage=Usage(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            model=usage.model if usage.calls else None,
        ),
        # **False on a refusal, always.** The router's refusal is never dressed as an
        # abstention: one reads the shape of the distance profile after retrieving, the
        # other classifies before, and collapsing them onto this field would make the two
        # rates this change exists to publish separately indistinguishable from each other.
        abstained=abstained,
        # "The generation layer ran", and no longer "there is a pitch". An empty argument alone
        # cannot tell a deployment that does not generate from a generation that was rejected,
        # and that distinction is the only evidence a consumer has that the guard acted.
        prompt_version=outcome.prompt_version if outcome is not None else None,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )


def _pitch_payload(
    source: SourceDocument | None,
    roster: Sequence[FamilyMember],
    citations: Sequence[KnowledgeCitation],
    *,
    warnings: Sequence[str],
    question: str,
):
    """What the model is handed — and therefore, exactly, which figures it may write.

    Built from the objects this module already holds, never from a rendered string: the numeric
    gate reads this object, and a gate that read the prompt text would admit the numerals of
    its own instructions.
    """
    return payload_from(
        sku=source.sku if source is not None else "",
        piece_type=source.piece_type if source is not None else None,
        materials=list(source.materials) if source is not None else [],
        size_label=source.size_label if source is not None else None,
        variant_label=next(
            (
                member.variant_label
                for member in roster
                if source is not None and member.product_id == source.product_id
            ),
            None,
        ),
        family_label=next(
            (member.family_name for member in roster if member.family_name is not None),
            None,
        ),
        variants=[(member.sku, member.variant_label) for member in roster],
        warnings=list(warnings),
        citations=[
            PitchCitation(
                citation_id=item.citation_id,
                document_title=item.document_title,
                section_title=item.section_title,
                claim_scope=item.claim_scope,
                content=item.content,
            )
            for item in citations
        ],
        query=question or None,
    )


def _free_query_payload(
    groups: Sequence[AssistGroup],
    citations: Sequence[KnowledgeCitation],
    *,
    warnings: Sequence[str],
    question: str,
):
    """What the model is handed for a free query — **and therefore which figures it may write**.

    `product_id` and `score` are on the response objects this reads and are deliberately not
    copied across: their digits are arbitrary, a counter argument never mentions either, and
    every numeral handed over widens the whitelist. That exclusion is the containment for the
    declared risk of this mode — the gate measured zero violations in 120 generations against a
    payload carrying one SKU, and five candidates bring five.

    `family_id` is excluded for the same reason and is not even a near miss: it is a UUID.
    """
    return free_query_payload_from(
        groups=[
            FreeQueryGroup(
                family_label=group.family_label,
                members=tuple(
                    FreeQueryCandidate(
                        sku=member.sku,
                        piece_type=None,
                        materials=tuple(member.materials),
                        size_label=None,
                        variant_label=member.variant_label,
                    )
                    for member in group.members
                ),
            )
            for group in groups
        ],
        warnings=list(warnings),
        citations=[
            PitchCitation(
                citation_id=item.citation_id,
                document_title=item.document_title,
                section_title=item.section_title,
                claim_scope=item.claim_scope,
                content=item.content,
            )
            for item in citations
        ],
        query=question or None,
    )


def _task_of(
    mode: AssistMode, routing: RoutingOutcome, *, uncovered: bool
) -> PitchTask | None:
    """Which task section this request generates with, or `None` when it must not generate.

    One place, and it is the whole generation policy of the layer stated once:

    * the two anchored modes always generate, with the degraded task when the corpus does not
      cover an anchored question;
    * a free query generates **only over a route the classifier decided**, which is exactly
      what makes the fail-open return this mode to the behaviour it had before C31 — no route,
      no task, no call, empty argument and absent prompt version, with a test on each;
    * a refused query and one answered with a clarification never generate, because there is
      nothing to write about.
    """
    if mode.is_anchored:
        return resolve_task(mode, uncovered=uncovered)
    route = routing.route
    if route is None:
        return None
    # `uncovered` travels here too since C40. Before it did not, and a knowledge question with
    # no fragments ran the task that says "answer using those fragments" with no fragments —
    # an explicit invitation to answer from memory, in the mode C40 puts on screen.
    return resolve_task(mode, route=route, uncovered=uncovered)


def _cited(
    citations: Sequence[KnowledgeCitation], used: Sequence[str]
) -> tuple[KnowledgeCitation, ...]:
    """The grounding fragments the argument declared, in the order it declared them."""
    by_id = {item.citation_id: item for item in citations}
    return tuple(by_id[item] for item in used if item in by_id)


def _usage(routing: RoutingOutcome, outcome: PitchOutcome | None) -> TokenUsage:
    """Everything the request cost, **the classifier included**. C31.

    `TokenUsage.__add__` is what makes this a sum rather than a choice, and the same property
    that made it a type in C30b applies twice over now: a request that classified, generated and
    repaired made three calls, and a usage that reported only the generation would understate
    the cost exactly on the requests that cost the most. `calls` travels with it, so the ceiling
    of three is observable from the same object a consumer reads.

    The model is the last one a call actually reported. Two different models for one request is
    now possible — the classifier has its own setting — and the contract has one field; the
    honest reading is that the figure to compare is the **total**, which is why the two are
    published as separate rows in the report and never as one aggregate the field could carry.
    """
    total = routing.usage
    if outcome is not None:
        total = total + outcome.usage
    return total


async def _focus_of(
    groups: Sequence[AssistGroup], *, search: ProductSearchPort
) -> SourceDocument | None:
    """The piece a query-only response leads with, read from the index.

    A response with no anchor still describes **a** piece to the operator — the first member
    of the first group, which is the top-ranked candidate — and the two warnings are
    statements about a piece. Attributing them to the whole result set instead would make
    `size_label_missing` fire whenever any of fifteen candidates lacked a size, which is
    almost always and therefore informs of nothing.

    An unusable row here is **not** an error: unlike an anchored piece, this one was chosen
    by the retrieval rather than named by the caller, so the honest response is the groups
    without the warnings.
    """
    if not groups or not groups[0].members:
        return None
    try:
        product_id = UUID(groups[0].members[0].product_id)
    except ValueError:
        return None
    return await search.source_document(product_id)
