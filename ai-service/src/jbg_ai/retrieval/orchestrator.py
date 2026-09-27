"""Fuse a vector list and two lexical lists into one answer. C14 built the vector branch; C21
connects the lexical one and makes `mode` mean what it says.

Two cables were stripped and left unconnected before this change. `ai.product_document.tsv` —
a generated `to_tsvector('spanish', doc_text)` column with its GIN index — had been populated
on every live row since C05 and nothing queried it. C20 computed the query expansion, logged it
as `stage=expand` and nobody read the result. Both are consumed here.

The order of the pipeline is a decision and not an accident (**C21** design D10 — not C25's,
whose D10 withdrew rotation from the ordering): the lexical branch
races the **embedding provider**, not the vector search. Running the two SQL statements in
parallel would optimise what costs nothing — on 1.168 rows with a GIN index the lexical query
is noise — while holding two of the five pool connections per request against a pool with
`max_overflow=0`. Racing the provider instead hides the lexical branch entirely behind a
170-1707 ms round trip and holds one connection at any moment.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from uuid import UUID

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.common import DebugInfo
from jbg_ai.api.schemas.retrieval import (
    RetrievalFilters,
    RetrievalMode,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
)
from jbg_ai.assist.constants import WARNING_FILTERS_TOO_NARROW
from jbg_ai.config.settings import Settings
from jbg_ai.indexing.constants import DEFAULT_EMBEDDING_MODEL
from jbg_ai.indexing.embeddings import EmbeddingClient, EmbedResult, LiteLlmEmbeddingClient
from jbg_ai.indexing.errors import EmbeddingError
from jbg_ai.retrieval.abstention import AbstentionRule
from jbg_ai.retrieval.abstention import log_decision as log_abstention
from jbg_ai.retrieval.abstention import should_abstain
from jbg_ai.retrieval.errors import InvalidFamilyIdError, RetrievalDependencyError
from jbg_ai.retrieval.filters import (
    OUT_OF_STOCK_BUCKET,
    BusinessWeights,
    StructuralFilters,
    demote,
    extract_filters,
)
from jbg_ai.retrieval.fusion import FusedCandidate, RankedList, fuse, normalised_scores
from jbg_ai.retrieval.lexical import EXPANDED_LIST, TYPED_LIST, expanded_request, typed_request
from jbg_ai.retrieval.ports import LexicalHit, ProductSearchPort, SearchFilters, SearchHit
from jbg_ai.retrieval.projection import (
    ProjectionFreshness,
    ProjectionScope,
    default_freshness,
    parse_pos_id,
    resolve_scope,
)
from jbg_ai.retrieval.synonyms import ExpandedQuery, expand_query
from jbg_ai.stubs.responses import over_retrieval_count

logger = logging.getLogger(__name__)

VECTOR_LIST = "vector"
#: Name the lexical branch presents to the inter-branch stage. It is a BRANCH and not a list:
#: whatever the two lexical lists did among themselves, stage 2 sees one ranked opinion holding
#: one weight. That is what makes `len(ranks) > 1` in stage 2 mean cross-branch consensus.
LEXICAL_BRANCH_LIST = "lexical"

#: The weight each of the two lexical lists carries INSIDE stage one. Declared here and not in
#: settings, and that is the whole point: the specification requires the two to be equal and
#: forbids sweeping them, so a setting could only ever be moved into violation with nothing to
#: detect it — which is worse than a dead knob, because it looks like a decision.
#:
#: **The value cannot change any result.** Both lists carry it, RRF scales linearly with the
#: weight, and stage two receives only the ORDER stage one produced — `lexical_ids` — never its
#: magnitudes. C25bis retired the three per-list weights on exactly that argument, so the
#: deletion was bit-identical by construction rather than by lucky measurement.
LEXICAL_INTERNAL_WEIGHT = 0.5

#: Two values, and neither is a strength parameter: the scaling IS the proportion, so the
#: live system carries no number governing how hard it pulls.
#:
#: `continuous` is the adopted rule. `none` switches it off and is the CONTROL — the arm that
#: measured whether the idea is worth having at all, and the rollback if it ever misbehaves.
#:
#: A third form was implemented and **withdrawn after measuring**: "did the best candidate
#: cover every expressible group? if not, keep a declared fraction alpha". It produced results
#: identical to the continuous rule at every point of the sweep, for two independent reasons —
#: the natural alpha of 0,5 coincides with the most frequent partial coverage on this set, and
#: where the two do differ both push the effective branch ratio past the point where the fused
#: order saturates. Indistinguishable in effect and carrying one parameter more, it lost on
#: cost rather than on result. The figures are in the C25 implementation report.
COVERAGE_CONTINUOUS = "continuous"
COVERAGE_NONE = "none"
COVERAGE_RULES = (COVERAGE_CONTINUOUS, COVERAGE_NONE)
LEXICAL_REASON = "lexical"
VECTOR_REASON = "vector"


def build_retrieval_embed_client(settings: Settings) -> LiteLlmEmbeddingClient:
    """Distinct from the indexer client: one attempt, so C03's 800 ms budget holds.

    Built once per process in `api/main.py` and resolved from `app.state`, with a **bounded**
    cache injected through this constructor seam — see `retrieval/cache.py`. Per request the
    unbounded cache of C11 was harmless; as a singleton it would be a lifetime leak.
    """
    from jbg_ai.retrieval.cache import BoundedEmbeddingCache

    return LiteLlmEmbeddingClient(
        api_key=settings.jpv_embedding_api_key,
        model=settings.jpv_embedding_model or DEFAULT_EMBEDDING_MODEL,
        base_url=settings.jpv_embedding_base_url,
        batch_size=settings.jpv_embedding_batch_size,
        max_attempts=1,
        cache=BoundedEmbeddingCache(),
    )


def parse_body_filters(filters: RetrievalFilters) -> SearchFilters:
    family_id: UUID | None = None
    if filters.family_id is not None:
        try:
            family_id = UUID(filters.family_id)
        except ValueError as exc:
            raise InvalidFamilyIdError(filters.family_id) from exc

    exclude: list[UUID] = []
    for raw in filters.exclude_product_ids:
        try:
            exclude.append(UUID(str(raw)))
        except (ValueError, TypeError, AttributeError):
            logger.debug("ignoring malformed exclude_product_id=%s", raw)

    materials = [item for item in filters.materials if item]
    return SearchFilters(
        materials=materials,
        category=filters.category,
        family_id=family_id,
        exclude_product_ids=exclude,
    )


def clamp_score(distance: float) -> float:
    return min(max(1.0 - distance, 0.0), 1.0)


@dataclass
class _Candidate:
    """One product, whatever produced it, plus the diagnostics of the branches that saw it."""

    product_id: UUID
    sku: str
    materials: list[str]
    family_id: UUID | None
    variant_label: str | None
    price: float | None
    size_label: str | None
    #: Read by the availability block of `demotion_rank` and never emitted. `None` means the
    #: query ran unscoped, which is not the same as a bucket of zero.
    qty_bucket: str | None = None
    #: Read by the business score of `demotion_rank` and never emitted. `None` is absence —
    #: no reading scope, or a product this point of sale does not carry — and never a zero.
    sales_30d: int | None = None
    vector_score: float | None = None
    lexical_score: float | None = None
    reasons: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass(frozen=True)
class _EmbedOutcome:
    result: EmbedResult | None
    error: Exception | None
    latency_ms: float


async def retrieve_products(
    payload: RetrievalRequest,
    principal: ServicePrincipal,
    *,
    settings: Settings,
    embed: EmbeddingClient,
    search: ProductSearchPort,
    expand_synonyms: bool | None = None,
    rrf_k: int | None = None,
    branch_weight_lexical: float | None = None,
    branch_weight_vector: float | None = None,
    coverage_rule: str = COVERAGE_CONTINUOUS,
    abstain: bool | None = None,
    branch_depth: int | None = None,
    pos_prefilter: bool | None = None,
    signal_pos_id: UUID | None = None,
    business_weight_availability: float | None = None,
    on_fused_candidates: Callable[[Sequence[object]], None] | None = None,
    on_abstention: Callable[[bool], None] | None = None,
    on_abstention_profile: Callable[[Sequence[float]], None] | None = None,
    projection_max_age_seconds: int | None = None,
    freshness: ProjectionFreshness | None = None,
) -> RetrievalResponse:
    """Every configuration knob overrides the settings default for one call.

    They are parameters and not only settings because C24 sweeps configurations inside one
    process; putting them on `RetrievalRequest` instead would move the frozen `openapi.json`.
    None of them mutates `settings`.
    """
    logger.debug(
        "operator query=%s",
        payload.query,
        extra={"trace_id": principal.trace_id},
    )

    expansion_enabled = (
        settings.jpv_query_expansion_enabled if expand_synonyms is None else expand_synonyms
    )
    k = settings.jpv_rrf_k if rrf_k is None else rrf_k
    w_lex_branch = (
        settings.jpv_branch_weight_lexical
        if branch_weight_lexical is None
        else branch_weight_lexical
    )
    w_vec_branch = (
        settings.jpv_branch_weight_vector
        if branch_weight_vector is None
        else branch_weight_vector
    )
    depth = settings.jpv_branch_depth if branch_depth is None else branch_depth
    weights = BusinessWeights(
        availability=(
            settings.jpv_business_weight_availability
            if business_weight_availability is None
            else business_weight_availability
        ),
    )
    prefilter = (
        settings.jpv_pos_prefilter_enabled if pos_prefilter is None else pos_prefilter
    )
    max_age = (
        settings.jpv_pos_projection_max_age_seconds
        if projection_max_age_seconds is None
        else projection_max_age_seconds
    )

    run_vector = payload.mode is not RetrievalMode.LEXICAL
    run_lexical = payload.mode is not RetrievalMode.VECTOR

    expand_started = time.perf_counter()
    expanded = expand_query(payload.query, enabled=expansion_enabled)
    expand_ms = (time.perf_counter() - expand_started) * 1000
    logger.info(
        "stage=expand trace_id=%s latency_ms=%.2f enabled=%s tokens=%s matched_terms=%s "
        "consumed=%s",
        principal.trace_id,
        expand_ms,
        expansion_enabled,
        len(expanded.groups),
        len(expanded.matched),
        run_lexical,
        extra={"trace_id": principal.trace_id},
    )

    # Parsed even when the prefilter is off: a token whose point of sale cannot be read is
    # broken whatever this request intends to do with it, and finding that out only when
    # somebody enables the flag is how a mis-issued token survives to production.
    pos_id = parse_pos_id(principal.pos_id)

    filters = parse_body_filters(payload.filters)
    if run_vector:
        compatible = await search.count_compatible(
            model_version_key=embed.model_version_key,
            model_id=embed.model_id,
        )
        if compatible == 0:
            raise RetrievalDependencyError(
                "no compatible embeddings for the live model_version_key; "
                "refusing to abstain over an empty or foreign index"
            )

    scope_started = time.perf_counter()
    scope = await resolve_scope(
        pos_id,
        search=search,
        enabled=prefilter,
        max_age_seconds=max_age,
        freshness=freshness or default_freshness,
    )
    logger.info(
        "stage=projection trace_id=%s latency_ms=%.2f enabled=%s applied=%s stale=%s "
        "age_seconds=%s scope_size=%s max_age_seconds=%s",
        principal.trace_id,
        (time.perf_counter() - scope_started) * 1000,
        prefilter,
        scope.applied,
        scope.stale,
        None if scope.age_seconds is None else round(scope.age_seconds, 1),
        scope.size,
        max_age,
        extra={"trace_id": principal.trace_id},
    )
    if scope.stale:
        logger.warning(
            "stage=projection trace_id=%s degraded=unscoped age_seconds=%s max_age_seconds=%s "
            "reason=%s",
            principal.trace_id,
            None if scope.age_seconds is None else round(scope.age_seconds, 1),
            max_age,
            "never_synchronised" if scope.age_seconds is None else "stale",
            extra={"trace_id": principal.trace_id},
        )

    embedded, typed_hits, expanded_hits = await _race_provider_against_text(
        payload,
        principal,
        expanded=expanded,
        embed=embed,
        search=search,
        filters=filters,
        depth=depth,
        run_vector=run_vector,
        run_lexical=run_lexical,
        pos_id=scope.pos_id,
        signal_pos_id=signal_pos_id,
    )

    vector_hits: list[SearchHit] = []
    vector_ran = False
    probe_distances: list[float] | None = None
    threshold = settings.jpv_retrieval_distance_threshold
    if embedded is not None and embedded.result is not None:
        vector_ran = True
        vector_hits = await _vector_branch(
            embedded.result,
            principal,
            embed=embed,
            search=search,
            filters=filters,
            threshold=threshold,
            depth=depth,
            mode=payload.mode,
            pos_id=scope.pos_id,
            signal_pos_id=signal_pos_id,
        )
        # Sequentially, and only when something narrows: with no filter the served profile
        # already is the unfiltered one, so a probe would ask the same question twice.
        if not filters.is_empty:
            probe_distances = await _probe_branch(
                embedded.result,
                principal,
                embed=embed,
                search=search,
                threshold=threshold,
                depth=depth,
                pos_id=scope.pos_id,
            )
    elif embedded is not None and embedded.error is not None:
        if payload.mode is RetrievalMode.VECTOR or not (typed_hits or expanded_hits):
            # A 200 with an empty list would be indistinguishable from a legitimate
            # abstention, and C16's panel paints its "we found nothing" screen on exactly
            # that shape. Serving a dependency failure behind it is the lie D8 prevents.
            raise RetrievalDependencyError(str(embedded.error)) from embedded.error
        logger.warning(
            "stage=embed trace_id=%s degraded_to=lexical error=%s",
            principal.trace_id,
            embedded.error,
            extra={"trace_id": principal.trace_id},
        )

    structural = extract_filters(expanded)

    # The fourth stripped cable of this subsystem, after `tsv`, the expansion and
    # `qty_bucket`: `coordination` has been computed, carried on every `LexicalHit` and read
    # by nobody. C21 expected an adaptive weighting to EMERGE from `ts_rank` and it does not —
    # `ts_rank` keeps ordering sixty documents that keep winning all of them.
    coverage = _lexical_coverage(expanded_hits)
    w_lex_effective = _scaled_lexical_weight(w_lex_branch, coverage, rule=coverage_rule)
    logger.info(
        "stage=coverage trace_id=%s rule=%s coverage=%s w_lex=%s w_lex_effective=%s",
        principal.trace_id,
        coverage_rule,
        "none" if coverage is None else f"{coverage:.3f}",
        w_lex_branch,
        f"{w_lex_effective:.4f}",
        extra={"trace_id": principal.trace_id},
    )

    candidates, cross_branch = _fuse_branches(
        typed_hits,
        expanded_hits,
        vector_hits,
        k=k,
        depth=depth,
        branch_weights=(w_lex_effective, w_vec_branch),
    )

    # An observability seam for the EVALUATION, and nothing else calls it. The capture phase
    # of the sweep needs the fused window with the fields the ordering reads — price, size,
    # materials, bucket, sales window — and the response carries none of them by design. The
    # alternative was a harness that rebuilt the pipeline, which would measure the copy.
    # It receives the window BEFORE `demote`, so what is persisted is the fusion's own output
    # and the re-score applies the whole ordering key from scratch.
    if on_fused_candidates is not None:
        on_fused_candidates(candidates)

    before = [item.product_id for item in candidates]
    ordered, demoted = demote(candidates, structural, weights)
    logger.info(
        "stage=filters trace_id=%s extracted=%s demoted=%s candidates=%s",
        principal.trace_id,
        structural.describe(),
        demoted,
        len(ordered),
        extra={"trace_id": principal.trace_id},
    )
    # `stage=signals` reports the business signals alone, because `stage=filters` cannot: it
    # counts everything the key demoted, and after C25 that conflates a price ceiling the
    # operator typed with a stock figure they never asked about. No exact quantity and no
    # vector appears here — the bucket is a bucket, and the sales window is reported only as
    # how many candidates carried one.
    logger.info(
        "stage=signals trace_id=%s w_availability=%s reading_scope=%s "
        "reordered=%s absent_signal=%s out_of_stock=%s with_sales_signal=%s",
        principal.trace_id,
        weights.availability,
        signal_pos_id is not None or scope.applied,
        sum(
            1
            for position, item in enumerate(ordered)
            if position >= len(before) or before[position] != item.product_id
        ),
        sum(1 for item in ordered if item.qty_bucket is None),
        sum(1 for item in ordered if item.qty_bucket == OUT_OF_STOCK_BUCKET),
        # A DIAGNOSTIC count and nothing else: `sales_30d` is persisted and read so the
        # report can publish its distribution, and no ordering rule consumes it. The
        # `Constrained` protocol `demote` reads does not even carry the field.
        sum(1 for item in ordered if item.sales_30d),
        extra={"trace_id": principal.trace_id},
    )

    window = over_retrieval_count(payload.top_k)
    shown = ordered[:window]
    fused = run_lexical and vector_ran
    low_confidence = _low_confidence(shown, fused=fused)

    # The decision about whether the catalogue can answer this query at all. It runs HERE —
    # after the fusion, over the distances the vector branch already produced — and not in the
    # retrieval statement, because the measurement that chose its form also chose its phase:
    # a relative rule does not alter the candidate set, which is what keeps the persisted
    # windows of the calibration valid.
    #
    # It is reached only when the vector branch actually ran. A provider failure degrades to
    # the lexical branch further up, or raises; serving that as an abstention would be the
    # same lie as a 200 with an empty list, and D8 of the fusion design prevents it.
    abstention = AbstentionRule(
        enabled=(
            settings.jpv_abstention_enabled if abstain is None else abstain
        ),
        band_alpha=settings.jpv_abstention_band_alpha,
        min_candidates=settings.jpv_abstention_band_min_candidates,
    )
    served_distances = [hit.distance for hit in vector_hits]
    # **The decision reads the unfiltered profile when there is one.** C40: the question is
    # whether the catalogue can answer the query, and the filter is not part of the query.
    distances = served_distances if probe_distances is None else probe_distances
    abstained = vector_ran and should_abstain(distances, abstention)
    if vector_ran:
        log_abstention(
            trace_id=principal.trace_id,
            rule=abstention,
            distances=distances,
            abstained=abstained,
        )

    # The other half of the same seam, and the reason the two must stay apart: a flat unfiltered
    # profile means the description found nothing, and a peaked one with a thin filtered set
    # means it found something the filter excluded. They end in opposite actions — describe it
    # another way, or remove a filter — and asserting the second when the first is true claims a
    # fit that does not exist.
    narrow_filters = (
        vector_ran
        and probe_distances is not None
        and abstention.enabled
        and not abstained
        and len(served_distances) < abstention.min_candidates
    )
    warnings: list[str] = [WARNING_FILTERS_TOO_NARROW] if narrow_filters else []
    if probe_distances is not None:
        logger.info(
            "stage=abstain trace_id=%s profile=unfiltered probe_candidates=%s "
            "served_candidates=%s min_candidates=%s filters_too_narrow=%s",
            principal.trace_id,
            len(probe_distances),
            len(served_distances),
            abstention.min_candidates,
            narrow_filters,
            extra={"trace_id": principal.trace_id},
        )

    # The profile the decision actually read, handed to whoever persists the candidate window.
    # Without it a re-score of a FILTERED pass could not recompute the decision, because the
    # window it persists is the filtered one and the rule did not read that.
    if on_abstention_profile is not None and probe_distances is not None:
        on_abstention_profile(tuple(probe_distances))
    # The second observability seam of this function, and it exists for the same reason as
    # `on_fused_candidates`: the decision is not recoverable from `RetrievalResponse`. An
    # empty `results` is also what a query that simply found nothing produces, and the one
    # field that does move with an abstention — `low_confidence` — carries a DIFFERENT,
    # measured meaning (cross-branch consensus: 1 of 20 out-of-domain against 10 of 43
    # answerable). A caller reading it as abstention would report the opposite of the truth
    # on the judged set, which is exactly what C30a's `abstained` field exists to avoid.
    #
    # It reports, and changes nothing: the gating below is unchanged, and a caller that
    # passes nothing sees the function it has always seen.
    if on_abstention is not None and vector_ran:
        on_abstention(abstained)

    if abstained:
        # A decision about the query, applied to the WHOLE response: no candidate is removed
        # one by one, because an abstention built by filtering is indistinguishable from a
        # retrieval that merely found little.
        shown = []
        low_confidence = True

    # `mode=` is gone from this line with C25bis: one composition exists, so a field that can
    # only ever print one value is noise, and the requirement that demanded it here is the one
    # that change removes. What the run actually composed is still RECORDED — in the
    # provenance of an evaluation run, which is where a reader can act on it.
    logger.info(
        "stage=fuse trace_id=%s typed=%s expanded=%s vector=%s fused=%s branches=%s "
        "cross_branch=%s returned=%s low_confidence=%s k=%s depth=%s weights=%s",
        principal.trace_id,
        len(typed_hits),
        len(expanded_hits),
        len(vector_hits),
        len(candidates),
        _branches_that_ran(run_lexical=run_lexical, vector_ran=vector_ran),
        cross_branch,
        len(shown),
        low_confidence,
        k,
        depth,
        f"w_lex={w_lex_branch} w_vec={w_vec_branch}",
        extra={"trace_id": principal.trace_id},
    )

    results = [_to_result(item, structural) for item in shown]
    return RetrievalResponse(
        results=results,
        candidates_returned=len(results),
        low_confidence=low_confidence,
        warnings=warnings,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
        projection_age_seconds=scope.reported_age,
    )


async def _race_provider_against_text(
    payload: RetrievalRequest,
    principal: ServicePrincipal,
    *,
    expanded: ExpandedQuery,
    embed: EmbeddingClient,
    search: ProductSearchPort,
    filters: SearchFilters,
    depth: int,
    run_vector: bool,
    run_lexical: bool,
    pos_id: UUID | None,
    signal_pos_id: UUID | None,
) -> tuple[_EmbedOutcome | None, list[LexicalHit], list[LexicalHit]]:
    """`gather(embed, lexical A then B)` — one pool connection held at any moment (D10)."""

    async def _embed_stage() -> _EmbedOutcome | None:
        if not run_vector:
            return None
        started = time.perf_counter()
        try:
            result = await embed.embed([payload.query])
        except EmbeddingError as exc:
            return _EmbedOutcome(None, exc, (time.perf_counter() - started) * 1000)
        latency = (time.perf_counter() - started) * 1000
        if not result.vectors:
            return _EmbedOutcome(
                None, RetrievalDependencyError("embedding provider returned no vector"), latency
            )
        logger.info(
            "stage=embed trace_id=%s latency_ms=%.1f model=%s cache_hits=%s",
            principal.trace_id,
            latency,
            result.embedding_model,
            result.cache_hits,
            extra={"trace_id": principal.trace_id},
        )
        return _EmbedOutcome(result, None, latency)

    async def _lexical_stage() -> tuple[list[LexicalHit], list[LexicalHit]]:
        if not run_lexical:
            return [], []
        started = time.perf_counter()
        # Sequential on purpose: two concurrent statements would hold two of the five pool
        # connections, and the pair costs single-digit milliseconds behind the provider.
        typed = await search.search_lexical(
            typed_request(payload.query),
            depth=depth,
            filters=filters,
            pos_id=pos_id,
            signal_pos_id=signal_pos_id,
        )
        widened = await search.search_lexical(
            expanded_request(expanded),
            depth=depth,
            filters=filters,
            pos_id=pos_id,
            signal_pos_id=signal_pos_id,
        )
        logger.info(
            "stage=lexical trace_id=%s latency_ms=%.1f typed=%s expanded=%s scoped=%s",
            principal.trace_id,
            (time.perf_counter() - started) * 1000,
            len(typed),
            len(widened),
            pos_id is not None,
            extra={"trace_id": principal.trace_id},
        )
        return typed, widened

    embedded, lexical = await asyncio.gather(_embed_stage(), _lexical_stage())
    typed_hits, expanded_hits = lexical
    return embedded, typed_hits, expanded_hits


async def _vector_branch(
    embedded: EmbedResult,
    principal: ServicePrincipal,
    *,
    embed: EmbeddingClient,
    search: ProductSearchPort,
    filters: SearchFilters,
    threshold: float,
    depth: int,
    mode: RetrievalMode,
    pos_id: UUID | None,
    signal_pos_id: UUID | None,
) -> list[SearchHit]:
    started = time.perf_counter()
    hits = await search.search(
        embedded.vectors[0],
        threshold=threshold,
        depth=depth,
        filters=filters,
        model_version_key=embed.model_version_key,
        model_id=embed.model_id,
        pos_id=pos_id,
        signal_pos_id=signal_pos_id,
    )
    hits = sorted(hits, key=lambda item: item.distance)[:depth]
    # `vector_empty` and not `low_confidence`: this stage knows only whether **its own**
    # branch returned anything, and the response-level marking is computed after the fusion.
    # The two really do diverge — a healthy vector branch whose candidates the lexical one
    # never saw logs `vector_empty=False` inside a response that *is* low confidence, because
    # nothing came from both branches. Sharing the name put two opposite values under one
    # field in a single trace, which is the kind of log that gets believed over the code.
    logger.info(
        "stage=search trace_id=%s latency_ms=%.1f distance_min=%s candidates=%s "
        "vector_empty=%s mode=%s threshold=%s scoped=%s depth=%s truncated=%s",
        principal.trace_id,
        (time.perf_counter() - started) * 1000,
        hits[0].distance if hits else None,
        len(hits),
        not hits,
        mode.value,
        threshold,
        pos_id is not None,
        depth,
        len(hits) < depth,
        extra={"trace_id": principal.trace_id},
    )
    return hits


async def _probe_branch(
    embedded: EmbedResult,
    principal: ServicePrincipal,
    *,
    embed: EmbeddingClient,
    search: ProductSearchPort,
    threshold: float,
    depth: int,
    pos_id: UUID | None,
) -> list[float]:
    """The same query with no body filter, for the abstention alone. C40.

    **Why it exists.** The abstention asks whether the catalogue can answer the *query*, and a
    filter is a restriction rather than a description. Read over a filtered profile the rule
    cannot fire at all when the filter is narrow — it needs `min_candidates` inside its band and
    a narrow filter can never supply them — so the system would serve a handful of mediocre
    pieces and, on the generative path, write prose praising them. The rule's parameters were
    calibrated over unfiltered queries; reading an unfiltered profile restores the regime they
    were fitted in instead of inventing a new one.

    **What it costs, and what it does not.** The vector is the one already computed for this
    request, so the embedding provider is called exactly once however many statements run. It is
    awaited *after* the filtered statement and never beside it: one connection of the pool at a
    time, which is the property this orchestration maintains against a pool capped at five. And
    it returns distances, never hits — nothing it finds can reach the response, the order or the
    window, because there is no path from here to the candidates.

    The point-of-sale scope is **kept**. It is not one of the operator's filters: it is what this
    shop carries, and a probe that ignored it would judge the query against a catalogue the
    counter cannot sell from.
    """
    started = time.perf_counter()
    hits = await search.search(
        embedded.vectors[0],
        threshold=threshold,
        depth=depth,
        filters=SearchFilters(),
        model_version_key=embed.model_version_key,
        model_id=embed.model_id,
        pos_id=pos_id,
        signal_pos_id=None,
    )
    distances = sorted(hit.distance for hit in hits)[:depth]
    # Reported apart from `stage=search` so a reader can tell a query the catalogue cannot
    # answer from a filter that admitted almost nothing. Scalars only: this stage receives
    # distances, and neither the vector nor the operator's query text can reach it.
    logger.info(
        "stage=probe trace_id=%s latency_ms=%.1f distance_min=%s candidates=%s scoped=%s "
        "depth=%s",
        principal.trace_id,
        (time.perf_counter() - started) * 1000,
        f"{distances[0]:.4f}" if distances else None,
        len(distances),
        pos_id is not None,
        depth,
        extra={"trace_id": principal.trace_id},
    )
    return distances


def _fuse_branches(
    typed_hits: list[LexicalHit],
    expanded_hits: list[LexicalHit],
    vector_hits: list[SearchHit],
    *,
    k: int,
    depth: int,
    branch_weights: tuple[float, float],
) -> tuple[list[_Candidate], int]:
    """Fuse the lists and rebuild the candidates with their real provenance.

    **One composition, and it is the two-stage one.** The two lexical lists are fused into one
    ranked list, and that list is fused against the vector list, so a branch's total vote is
    exactly its declared weight however many of its own lists happened to match.

    The single-stage fusion over all three lists that C21 shipped was retired by C25bis. It was
    not a weighting choice but an ARITY defect: with the per-list weights the sixty lexical
    documents outscored the vector branch's best hit in every query. The demonstration survives
    as pure arithmetic over `fuse()` in the test suite, where no configuration can reach it.
    """
    candidates: dict[UUID, _Candidate] = {}

    for hit in (*typed_hits, *expanded_hits):
        item = candidates.get(hit.product_id) or _from_hit(hit)
        item.lexical_score = max(item.lexical_score or 0.0, hit.ts_rank)
        candidates[hit.product_id] = item

    for hit in vector_hits:
        item = candidates.get(hit.product_id) or _from_hit(hit)
        item.vector_score = clamp_score(hit.distance)
        candidates[hit.product_id] = item

    typed_ids = [hit.product_id for hit in typed_hits]
    expanded_ids = [hit.product_id for hit in expanded_hits]
    vector_ids = [hit.product_id for hit in vector_hits]

    fused = _fuse_two_stage(
        typed_ids,
        expanded_ids,
        vector_ids,
        k=k,
        depth=depth,
        branch_weights=branch_weights,
    )
    lexical_names = (LEXICAL_BRANCH_LIST,)

    scores = normalised_scores(fused)

    ordered: list[_Candidate] = []
    cross_branch = 0
    for entry, score in zip(fused, scores, strict=True):
        item = candidates[entry.key]  # type: ignore[index]
        item.score = score
        reasons: list[str] = []
        if VECTOR_LIST in entry.ranks:
            reasons.append(VECTOR_REASON)
        if any(name in entry.ranks for name in lexical_names):
            reasons.append(LEXICAL_REASON)
        item.reasons = reasons
        # A candidate seen by both lexical lists is not cross-branch: with the expansion
        # disabled the two lists are identical, and every lexical hit would qualify. Under the
        # two-stage composition the point is moot — stage 2 has one entry per branch — so what
        # C25 had to state in prose is now STRUCTURAL, and the signal cannot drift back to
        # meaning "two lists agreed". That is why `low_confidence` needs no exception here.
        if len(reasons) > 1:
            cross_branch += 1
        # A diagnostic is absent rather than invented for a branch that did not see it.
        if VECTOR_REASON not in reasons:
            item.vector_score = None
        if LEXICAL_REASON not in reasons:
            item.lexical_score = None
        ordered.append(item)

    return ordered, cross_branch


def _lexical_coverage(expanded_hits: Sequence[LexicalHit]) -> float | None:
    """How much of what the query CAN express its best lexical candidate actually matched.

    The numerator is free: the expanded list arrives `ORDER BY coordination DESC`, so the
    first hit's tally IS the maximum. The denominator counts only the groups whose tsquery
    survives the language configuration, which is the point the whole rule turns on — a stop
    word the operator typed becomes a counting group that can never match anything, and
    counting it would lower the weight of a query that is in fact fully anchored.

    `None` means "do not scale", and it is returned for the two cases where the ratio carries
    no information rather than carrying zero:

    * the lexical branch produced nothing, so its weight decides nothing;
    * the query expressed no group the index can be asked about at all, so there is no
      denominator. Scaling to zero there would silence the branch on the strength of a
      question that was never asked.
    """
    if not expanded_hits:
        return None
    best = expanded_hits[0]
    if best.coverage_denominator <= 0:
        return None
    # Clamped because a document can match a group more than one way through the OR of its
    # surface forms; coverage is a proportion and must not exceed one.
    return min(best.coordination / best.coverage_denominator, 1.0)


def _scaled_lexical_weight(weight: float, coverage: float | None, *, rule: str) -> float:
    """`w_lex x coverage`, and nothing else. C25 D7.

    A branch whose best candidate matched everything the query can express keeps its full
    declared weight; one that matched a fraction keeps that fraction. **No parameter of its
    own**, which is the property the rule was adopted for and the one that survived the
    comparison against a form that had one.

    Measured against the control arm — the same fusion with the rule off — it buys **+0,128**
    on `descripcion-sin-anclaje` and **exactly zero** on all seven other categories, which is
    D7's falsifiable prediction confirmed against the live index. It also flattens the branch
    ratio from a cliff into a plateau: the sweep's range over `rho` falls from 0,070 without
    the rule to 0,007 with it, so the default stops sitting on a discontinuity.

    `none` is the control and the rollback. It is an on/off switch, not a strength.
    """
    if coverage is None or rule == COVERAGE_NONE:
        return weight
    if rule != COVERAGE_CONTINUOUS:
        raise ValueError(f"unknown coverage rule {rule!r}, expected one of {COVERAGE_RULES}")
    return weight * coverage


def _fuse_two_stage(
    typed_ids: Sequence[UUID],
    expanded_ids: Sequence[UUID],
    vector_ids: Sequence[UUID],
    *,
    k: int,
    depth: int,
    branch_weights: tuple[float, float],
) -> tuple[FusedCandidate, ...]:
    """Stage 1 inside the lexical branch, stage 2 between the branches. C25.

    The formula is untouched: this composes `fuse` with itself, feeding stage 1's ORDER back
    in as a ranked list. Only the order survives stage 1 — the magnitude of the intra-lexical
    consensus is flattened — which is the declared cost of the change, and the defence is that
    flattening magnitude into rank is what RRF does at every level of every one of its stages.

    **Stage 1's output is truncated at `depth` too.** Without that the lexical branch could
    present up to `2 * depth` distinct candidates to stage 2 against the vector branch's
    `depth`, which is a second and independent way of over-weighting it: twice the slots on
    top of the larger vote.
    """
    w_lex, w_vec = branch_weights

    # Equal and declared, never configured: see `LEXICAL_INTERNAL_WEIGHT`. Only the ORDER of
    # this stage reaches stage two, so the common value cannot alter any result.
    lexical = fuse(
        [
            RankedList(TYPED_LIST, LEXICAL_INTERNAL_WEIGHT, typed_ids),
            RankedList(EXPANDED_LIST, LEXICAL_INTERNAL_WEIGHT, expanded_ids),
        ],
        k=k,
        depth=depth,
    )
    lexical_ids = [item.key for item in lexical][:depth]

    return fuse(
        [
            RankedList(LEXICAL_BRANCH_LIST, w_lex, lexical_ids),
            RankedList(VECTOR_LIST, w_vec, vector_ids),
        ],
        k=k,
        depth=depth,
    )


def _from_hit(hit: LexicalHit | SearchHit) -> _Candidate:
    """One candidate from whichever branch saw it first. Every branch reports the bucket."""
    return _Candidate(
        product_id=hit.product_id,
        sku=hit.sku,
        materials=list(hit.materials),
        family_id=hit.family_id,
        variant_label=hit.variant_label,
        price=hit.price,
        size_label=hit.size_label,
        qty_bucket=hit.qty_bucket,
        sales_30d=hit.sales_30d,
    )


def _branches_that_ran(*, run_lexical: bool, vector_ran: bool) -> str:
    names = [
        name
        for name, ran in ((LEXICAL_REASON, run_lexical), (VECTOR_REASON, vector_ran))
        if ran
    ]
    return "+".join(names) if names else "none"


def _low_confidence(shown: Sequence[_Candidate], *, fused: bool) -> bool:
    """Absence of cross-branch consensus — but only where there were branches to disagree.

    With two branches running, the signal is the one D9 defines: no returned candidate was
    produced by more than one of them, which is the exact signature of the measured failure
    where the vector branch answered *pulsera* and the lexical one the three *sortijas* with
    zero overlap. It stays a signal: it never changes how many candidates are returned.

    With **one** branch — `mode=lexical`, `mode=vector`, or a `hybrid` request whose embedding
    provider failed and degraded — no candidate can ever appear twice, so that rule would mark
    every response low confidence and the field would carry no information at all. There it
    keeps the C14 meaning instead: the retriever returned nothing. Reporting a permanent true
    would be the same kind of lie as the `["vector"]` constant this change removed.
    """
    if not fused:
        return not shown
    return not any(len(item.reasons) > 1 for item in shown)


def _to_result(item: _Candidate, structural: StructuralFilters) -> RetrievalResult:
    notes: list[str] = []
    if not structural.is_empty:
        notes.append(f"structural_filters:{structural.describe()}")
    return RetrievalResult(
        product_id=str(item.product_id),
        sku=item.sku,
        score=item.score,
        match_reasons=list(item.reasons),
        materials=list(item.materials),
        family_id=str(item.family_id) if item.family_id is not None else None,
        variant_label=item.variant_label,
        debug=DebugInfo(
            vector_score=item.vector_score,
            lexical_score=item.lexical_score,
            rerank_score=None,
            notes=notes,
        ),
    )
