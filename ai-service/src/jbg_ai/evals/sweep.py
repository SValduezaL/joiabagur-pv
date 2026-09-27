"""The calibration sweep, in two phases, and the rule that may move a default. C24, recast by C25.

**The rule was written before the measurement ran**, which is the only thing that makes "the
sweep was redone with the good judge" a claim rather than an impression. C25 reformulates it,
and the reformulation is itself dated and argued in `design.md` D14 **before** any sweep ran:

    a default changes if and only if
      · the improvement on the NEW queries exceeds 0.05, AND
      · no measured category degrades by more than 0.05.

    the tuning subset is reported as a DIAGNOSTIC of contamination and never vetoes.

Why the tuning subset stopped being a veto is a property of that subset, visible without
looking at any result: **6 of its 8 queries sit at the ceiling of nDCG@5** and all 8 at the
ceiling of Recall@5, P@3 and MRR — a saturated reading cannot improve, only tie or fall — and
**7 of the 8 come from the curated list C20/C21 calibrated the lexical branch with**. Requiring
its agreement vetoes raising the vector weight using the very queries chosen to make the
lexical branch win. C24 published the evidence itself: 0.942 on tuning against 0.535 on new,
which it called "the contamination of the tuning set, quantified". A contaminated partition is
evidence of the incumbent's overfitting, not a control group.

**The grid is one-dimensional**, because only the RATIO of the branch weights changes the
order — scaling both preserves it, which was measured by running `fuse` — so the sweep is over
`rho = w_vec / w_lex` and the pair is renormalised to sum to one. The useful band is narrow,
`rho in [0.9, 1.1]`, and the previous grid had exactly one point inside it: that is why its
optimum looked like a knife edge.

`k` and the branch depth move TOGETHER or neither means anything, by C21's rule that a deeper
branch keeps more of its tail voting.

**And the sweep has two phases, because the business signals do not change WHICH candidates
are retrieved, only their order.** `demote` is a stable sort that removes nothing, so a window
captured once can be re-scored over hundreds of weight combinations in seconds, with no
provider and no database. That makes reproducibility a STRUCTURAL property rather than a
promise about seeds. The order of the phases is a constraint and not a preference: the fusion
moves the window, so it is frozen first — and each captured window records the fusion it was
taken under, so a re-score against a different one is refused instead of silently wrong.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from itertools import product
from pathlib import Path
from uuid import UUID

from jbg_ai.config.settings import FUSION_DEFAULTS, Settings
from jbg_ai.evals.configs import EvalConfig
from jbg_ai.evals.errors import ConfigurationError
from jbg_ai.evals.golden import OUT_OF_DOMAIN, GoldenSet
from jbg_ai.evals.metrics import (
    Aggregate,
    CaseMetrics,
    abstention_rate,
    aggregate,
    score_case,
)
from jbg_ai.evals.pricing import PriceList
from jbg_ai.evals.provenance import Provenance
from jbg_ai.evals.runner import ConfigReport, run_config
from jbg_ai.indexing.embeddings import EmbeddingClient
from jbg_ai.retrieval.abstention import AbstentionRule, should_abstain
from jbg_ai.retrieval.filters import BusinessWeights, demote, extract_filters
from jbg_ai.retrieval.ports import ProductSearchPort
from jbg_ai.retrieval.synonyms import expand_query

#: `rho = w_vec / w_lex`. Eight points, four of them inside the useful band the exploration
#: measured. The previous grid — 0.33, 0.5, 0.75, 1.0, 1.5, 2.0 — had ONE.
#:
#: The band is narrow because the fusion has a crossover: below roughly 0.9 the vector
#: branch's best hit cannot reach the top five at all, and above roughly 1.1 it always takes
#: first place. Position of that hit against a lexical list of 60 with no consensus, predicted
#: and measured alike: 0.33 -> 61, 0.75 -> 22, 0.90 -> 8, 0.95 -> 5, 1.00 -> 2, >=1.10 -> 1.
RHO_GRID = (0.6, 0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.25)

#: `(k, depth)` pairs, always equal. C21's measured rule is that depth is of the order of k,
#: so they are swept together or not at all. Two points keeps the grid at sixteen.
K_DEPTH_GRID = ((40, 40), (60, 60))

#: Above the annotation noise a golden set of this size can resolve. With a confidence interval
#: of about ±0.13 on the real portion, anything smaller is a difference this set cannot see.
MATERIAL_DELTA = 0.05

#: No category may pay for the gain by more than this.
CATEGORY_TOLERANCE = 0.05

DECISION_METRIC = "ndcg_at_5"

#: Named rather than inlined for the same reason the readings are: the incumbent is the
#: continuous rule, and which row counts as the incumbent must not depend on a string literal
#: somebody can change inside an expression.
COVERAGE_CONTINUOUS_RULE = "continuous"

#: The reading that decides, and the one reported beside it. Named here because the rule is
#: the point of this module: putting the string inline would let somebody change which
#: partition arbitrates a default by editing an expression.
DECIDING_READING = "new"
DIAGNOSTIC_READING = "tuning"


def weights_for(rho: float) -> tuple[float, float]:
    """`(w_lex, w_vec)` for a ratio, renormalised so the pair sums to one.

    Only the ratio changes the order, so the normalisation is free and buys comparability: two
    points of the grid differ in one number and the reader can see which.
    """
    w_vec = rho / (1.0 + rho)
    return 1.0 - w_vec, w_vec


@dataclass(frozen=True)
class SweepPoint:
    """One point of the grid and what it scored."""

    rho: float
    rrf_k: int
    branch_depth: int
    report: ConfigReport
    coverage_rule: str = "continuous"

    @property
    def label(self) -> str:
        w_lex, w_vec = weights_for(self.rho)
        return (
            f"rho={self.rho} (w_lex={w_lex:.3f} w_vec={w_vec:.3f}) "
            f"k={self.rrf_k} depth={self.branch_depth} cobertura={self.coverage_rule}"
        )

    def score(self, reading: str = DECIDING_READING) -> float:
        return self.report.readings[reading].values[DECISION_METRIC]


@dataclass(frozen=True)
class Verdict:
    """What the rule says, and every figure it says it from."""

    moved: bool
    reason: str
    baseline: SweepPoint
    best: SweepPoint
    deltas: dict[str, float]
    category_deltas: dict[str, float]

    def as_lines(self) -> list[str]:
        diagnostic = self.deltas.get(DIAGNOSTIC_READING, 0.0)
        lines = [
            f"- Configuración vigente: **{self.baseline.label}** → "
            f"nDCG@5 ({DECIDING_READING}) {self.baseline.score():.3f}",
            f"- Mejor del barrido: **{self.best.label}** → "
            f"nDCG@5 ({DECIDING_READING}) {self.best.score():.3f}",
            "- Deltas por lectura: "
            + ", ".join(f"{name} {value:+.3f}" for name, value in self.deltas.items()),
            f"- Lectura que **decide**: `{DECIDING_READING}`. `{DIAGNOSTIC_READING}` se "
            f"publica como **diagnóstico de contaminación** ({diagnostic:+.3f}) y no veta.",
            "- Peor categoría: "
            + ", ".join(
                f"{name} {value:+.3f}"
                for name, value in sorted(self.category_deltas.items(), key=lambda i: i[1])[:3]
            ),
            f"- **Veredicto: {'se mueve el default' if self.moved else 'NO se mueve el default'}** "
            f"— {self.reason}",
        ]
        return lines


def _values(agg: Aggregate) -> float:
    return agg.values[DECISION_METRIC]


def decide(baseline: SweepPoint, candidates: list[SweepPoint]) -> Verdict:
    """Apply the reformulated rule of D14. Documents the outcome whether or not anything moves.

    Two conditions, and the tuning subset is in neither. It is computed and published all the
    same, because a reader has to be able to weigh the disagreement — what it may not do is
    decide.
    """
    best = max(candidates, key=lambda point: point.score(DECIDING_READING))
    deltas = {
        reading: _values(best.report.readings[reading])
        - _values(baseline.report.readings[reading])
        for reading in ("global", DIAGNOSTIC_READING, DECIDING_READING)
    }
    # Over the whole population of each category, deliberately, and not over the deciding
    # partition alone: a category that pays is a category that pays, whichever partition its
    # queries happen to sit in. It is the broader guard of the two.
    category_deltas = {
        name: _values(best.report.by_category[name]) - _values(agg)
        for name, agg in baseline.report.by_category.items()
        if name in best.report.by_category
    }

    if deltas[DECIDING_READING] <= MATERIAL_DELTA:
        return Verdict(
            moved=False,
            reason=(
                f"la mejora en `{DECIDING_READING}` es {deltas[DECIDING_READING]:+.3f}, por "
                f"debajo del margen acordado de {MATERIAL_DELTA}; con un intervalo de ±0,13 "
                "sobre la porción real, una diferencia así no se distingue del ruido de "
                "anotación"
            ),
            baseline=baseline,
            best=best,
            deltas=deltas,
            category_deltas=category_deltas,
        )
    worst = min(category_deltas.items(), key=lambda item: item[1], default=("", 0.0))
    if worst[1] < -CATEGORY_TOLERANCE:
        return Verdict(
            moved=False,
            reason=(
                f"la categoría `{worst[0]}` empeora {worst[1]:+.3f}, más de lo acordado "
                f"({CATEGORY_TOLERANCE}). La media puede subir mientras un caso de uso entero "
                "se rompe, y por eso la regla mira las categorías y no sólo el agregado"
            ),
            baseline=baseline,
            best=best,
            deltas=deltas,
            category_deltas=category_deltas,
        )
    contaminated = deltas[DIAGNOSTIC_READING] <= 0
    return Verdict(
        moved=True,
        reason=(
            f"supera el margen en `{DECIDING_READING}` y ninguna categoría paga más de lo "
            "acordado"
            + (
                f". `{DIAGNOSTIC_READING}` no acompaña ({deltas[DIAGNOSTIC_READING]:+.3f}) y "
                "**no veta**: es la partición con la que se calibró la rama léxica, con 6 de "
                "sus 8 consultas en el techo de la métrica, así que no puede registrar una "
                "mejora — sólo empatar o caer"
                if contaminated
                else ""
            )
        ),
        baseline=baseline,
        best=best,
        deltas=deltas,
        category_deltas=category_deltas,
    )


async def sweep(
    config: EvalConfig,
    golden: GoldenSet,
    *,
    settings: Settings,
    search: ProductSearchPort,
    embed: EmbeddingClient,
    prices: PriceList,
    provenance: Provenance,
    repeat: int = 1,
    coverage_rules: tuple[str, ...] = ("continuous",),
) -> tuple[SweepPoint, list[SweepPoint]]:
    """Run the grid in series and return the point in force plus every candidate.

    `coverage_rules` is how the CONTROL arm enters: sweeping `("continuous", "none")` measures
    whether the adaptive rule is worth having at all, which a sweep over two forms of the same
    idea cannot answer. That comparison is what retired the binary form and kept this one.
    """
    points: list[SweepPoint] = []
    for rho, (rrf_k, depth), rule in product(RHO_GRID, K_DEPTH_GRID, coverage_rules):
        w_lex, w_vec = weights_for(rho)
        variant = replace(
            config,
            branch_weight_lexical=w_lex,
            branch_weight_vector=w_vec,
            rrf_k=rrf_k,
            branch_depth=depth,
            coverage_rule=rule,
        )
        report = await run_config(
            variant,
            golden,
            settings=settings,
            search=search,
            embed=embed,
            prices=prices,
            provenance=provenance,
            repeat=repeat,
        )
        points.append(
            SweepPoint(
                rho=rho,
                rrf_k=rrf_k,
                branch_depth=depth,
                report=report,
                coverage_rule=rule,
            )
        )

    live = (
        FUSION_DEFAULTS["jpv_branch_weight_vector"]
        / FUSION_DEFAULTS["jpv_branch_weight_lexical"],
        FUSION_DEFAULTS["jpv_rrf_k"],
        FUSION_DEFAULTS["jpv_branch_depth"],
    )
    baseline = next(
        (
            point
            for point in points
            if (point.rho, point.rrf_k, point.branch_depth) == live
            and point.coverage_rule == COVERAGE_CONTINUOUS_RULE
        ),
        points[0],
    )
    return baseline, [point for point in points if point is not baseline]


# --------------------------------------------------------------------------------------
# Phase B and phase C: capture once, re-score many times.
# --------------------------------------------------------------------------------------

#: Bumped to 2 when the binary coverage rule was withdrawn: `coverage_alpha` left the fusion
#: fingerprint, so a file written before that carries a field this version does not know. The
#: version check turns that into a legible refusal instead of a type error.
CAPTURE_VERSION = 2


@dataclass(frozen=True)
class FusionFingerprint:
    """Every knob that decides WHICH candidates a query produces, and in what order.

    Recorded with each capture so a re-score can refuse a window taken under a different
    fusion. Inverting the two phases is otherwise a SILENT failure: the sweep runs, produces
    numbers, and they are measured against a fusion that is no longer the one being calibrated.

    The business weights are deliberately NOT here. They are what the re-score varies, and
    they reorder the window without changing its membership — which is the whole reason the
    second phase can run offline.
    """

    #: `mode` and the three per-list weights left this fingerprint with C25bis: one composition
    #: exists and no per-list weight does, so neither can differ between a capture and a
    #: re-score. A capture file written before that change no longer loads here, which is the
    #: correct outcome — its window was produced under a composition the code cannot reproduce,
    #: and re-scoring it would rank a window the live fusion no longer produces. Captures are
    #: not versioned artefacts: re-run the capture phase.
    rrf_k: int
    branch_depth: int
    branch_weight_lexical: float
    branch_weight_vector: float
    coverage_rule: str
    expand_synonyms: bool | None
    signal_pos_id: str | None
    retrieval_mode: str | None

    @classmethod
    def of(cls, config: EvalConfig, settings: Settings) -> "FusionFingerprint":
        """Resolve every knob to its EFFECTIVE value, so two equivalent configurations match."""
        return cls(
            rrf_k=config.rrf_k if config.rrf_k is not None else settings.jpv_rrf_k,
            branch_depth=(
                config.branch_depth
                if config.branch_depth is not None
                else settings.jpv_branch_depth
            ),
            branch_weight_lexical=(
                config.branch_weight_lexical
                if config.branch_weight_lexical is not None
                else settings.jpv_branch_weight_lexical
            ),
            branch_weight_vector=(
                config.branch_weight_vector
                if config.branch_weight_vector is not None
                else settings.jpv_branch_weight_vector
            ),
            coverage_rule=config.coverage_rule or COVERAGE_CONTINUOUS_RULE,
            expand_synonyms=config.expand_synonyms,
            signal_pos_id=config.signal_pos_id,
            retrieval_mode=config.mode,
        )


@dataclass(frozen=True)
class CapturedCandidate:
    """One candidate of a persisted window, with everything the re-score needs to order it.

    It carries the signals rather than looking them up again, because the re-score must not
    reach the database: a phase that quietly re-queried would be neither reproducible nor fast,
    and would reintroduce the very coupling the two phases exist to remove.
    """

    product_id: str
    sku: str
    score: float
    price: float | None = None
    size_label: str | None = None
    materials: tuple[str, ...] = ()
    qty_bucket: str | None = None
    sales_30d: int | None = None
    family_id: str | None = None
    branches: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapturedWindow:
    """One query's candidate window, in the order the frozen fusion produced it."""

    query_id: str
    query_text: str
    low_confidence: bool
    candidates: tuple[CapturedCandidate, ...]
    #: The distances the abstention rule actually read, when that is **not** the profile of
    #: the candidates above. C40's probe: a filtered request decides over the unfiltered
    #: profile, so the window persisted here is the filtered one and the decision is not
    #: recoverable from it. `None` means the rule read the served candidates, which is the
    #: case for every capture taken before C40 and for every unfiltered query — the whole
    #: golden set today. That is why `CAPTURE_VERSION` does not move: the candidate set is
    #: unchanged, so those captures stay valid and a re-score of them is not refused.
    probe_distances: tuple[float, ...] | None = None


@dataclass(frozen=True)
class Capture:
    """Every window of one run, plus the fusion they were all taken under."""

    version: int
    golden_set_version: str
    fusion: FusionFingerprint
    windows: tuple[CapturedWindow, ...] = field(default_factory=tuple)
    #: Availability bucket per product for the whole assortment of the reading scope. It is
    #: persisted rather than re-read because the OPERATIONAL metric — the objective of the
    #: re-score — needs the bucket of every JUDGED document to build its ideal, not only of
    #: the ones a configuration retrieved. Reading it in phase C would mean opening a pool,
    #: and that is exactly what phase C promises not to do.
    buckets: dict[str, str] = field(default_factory=dict)
    #: The abstention rule the windows were captured under, so a re-score that has to
    #: recompute a decision from a persisted probe can do it without reading settings — phase
    #: C opens nothing, and `Settings()` needs an environment. `None` in a capture where no
    #: window carries a probe, which is every capture taken before C40.
    abstention: AbstentionRule | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, payload: str) -> "Capture":
        data = json.loads(payload)
        if data.get("version") != CAPTURE_VERSION:
            raise ConfigurationError(
                f"capture version {data.get('version')!r} is not {CAPTURE_VERSION}: the file "
                "was written by another version of the harness and its fields may not mean "
                "the same thing"
            )
        return cls(
            version=data["version"],
            golden_set_version=data["golden_set_version"],
            fusion=FusionFingerprint(**data["fusion"]),
            windows=tuple(
                CapturedWindow(
                    query_id=item["query_id"],
                    query_text=item["query_text"],
                    low_confidence=item["low_confidence"],
                    probe_distances=(
                        None
                        if item.get("probe_distances") is None
                        else tuple(item["probe_distances"])
                    ),
                    candidates=tuple(
                        CapturedCandidate(
                            **{
                                **entry,
                                "materials": tuple(entry.get("materials") or ()),
                                "branches": tuple(entry.get("branches") or ()),
                            }
                        )
                        for entry in item["candidates"]
                    ),
                )
                for item in data["windows"]
            ),
            buckets=dict(data.get("buckets") or {}),
            abstention=(
                None
                if data.get("abstention") is None
                else AbstentionRule(**data["abstention"])
            ),
        )


def check_fusion_matches(capture: Capture, expected: FusionFingerprint) -> None:
    """Refuse a window captured under a different fusion, naming what differs.

    The mismatch is reported rather than silently re-scored, because the failure it prevents
    produces plausible numbers: phase C would run, report a winner, and that winner would have
    been chosen over a candidate set the live fusion no longer produces.
    """
    if capture.fusion == expected:
        return
    differing = [
        f"{name}: capturado {getattr(capture.fusion, name)!r} contra "
        f"{getattr(expected, name)!r}"
        for name in capture.fusion.__dataclass_fields__
        if getattr(capture.fusion, name) != getattr(expected, name)
    ]
    raise ConfigurationError(
        "las ventanas se capturaron bajo otra fusión, así que re-puntuarlas mediría el orden "
        "de una ventana que la fusión calibrada ya no produce. Diferencias — "
        + "; ".join(differing)
        + ". Vuelve a ejecutar la fase de captura con la fusión congelada."
    )


class _Orderable:
    """The minimum `demote` reads, rebuilt from a persisted candidate."""

    __slots__ = ("product_id", "price", "size_label", "materials", "qty_bucket", "sales_30d")

    def __init__(self, item: CapturedCandidate) -> None:
        self.product_id = item.product_id
        self.price = item.price
        self.size_label = item.size_label
        self.materials = list(item.materials)
        self.qty_bucket = item.qty_bucket
        self.sales_30d = item.sales_30d


def rescore_window(
    window: CapturedWindow, weights: BusinessWeights, *, depth: int | None = None
) -> tuple[str, ...]:
    """Re-order one persisted window under a weight configuration. Pure: no I/O at all.

    The structural filters are recomputed rather than persisted because reading them out of
    the query text is pure — `expand_query` opens no session and calls no provider — and a
    persisted copy would be a second source of truth that could drift from the live rule.

    **The whole window is ordered and only then truncated**, which is the order the live path
    uses: the two lexical lists and the vector one can hold up to `2 * depth` distinct
    candidates between them, and cutting before the ordering would drop candidates the
    business score was about to promote.
    """
    structural = extract_filters(expand_query(window.query_text, enabled=True))
    ordered, _ = demote(
        [_Orderable(item) for item in window.candidates], structural, weights
    )
    ids = tuple(item.product_id for item in ordered)
    return ids if depth is None else ids[:depth]


def _reading(cases: Sequence[CaseMetrics]) -> Aggregate:
    """An aggregate that also carries the abstention, which `aggregate` does not average.

    **A decision nobody can read is not a decision recomputed.** The re-score has always
    passed an `abstained` flag into `score_case` and then dropped it: `AVERAGED` does not
    include it, so nothing it produced ever surfaced. C40 needs it to surface, because the
    requirement it implements is that a re-score **recompute** the decision from a persisted
    probe rather than guess it, and that is only checkable if the result comes out.

    Additive: every existing key keeps its value, and the metric the sweep decides on is not
    this one.
    """
    base = aggregate(cases)
    return Aggregate(
        queries=base.queries,
        values={**base.values, "abstention_rate": abstention_rate(cases)},
    )


def _abstained_of(window: CapturedWindow, rule: AbstentionRule | None) -> bool:
    """Recomputed from the persisted probe, or read off the window when there is none.

    **Two different things, and the file says which applies.** With no probe the rule read
    the served candidates, and `low_confidence` is what this sweep has always captured for
    the abstention rate — unchanged, so no published figure moves. With a probe the rule read
    a profile the window does not contain, and guessing from `low_confidence` would report a
    decision the run never took.
    """
    if window.probe_distances is None:
        return window.low_confidence
    if rule is None:
        raise ConfigurationError(
            f"window {window.query_id!r} persisted an abstention probe and the capture "
            "carries no rule to recompute it with: guessing the decision from "
            "low_confidence is exactly what persisting the profile exists to avoid"
        )
    return should_abstain(window.probe_distances, rule)


def rescore(
    capture: Capture,
    golden: GoldenSet,
    weights: BusinessWeights,
    *,
    buckets: dict[str, str] | None = None,
    depth: int | None = None,
    abstention: AbstentionRule | None = None,
) -> dict[str, Aggregate]:
    """Score every window under one weight configuration. No provider, no database.

    Two runs over the same windows with the same weights produce identical results, and that
    is STRUCTURAL rather than a promise about seeds: the input is a file, the ordering is a
    stable sort over it, and nothing in the path can vary.
    """
    by_query = {query.id: query for query in golden.retrieval_queries}
    rule = abstention or capture.abstention
    cases = []
    for window in capture.windows:
        if window.query_id not in by_query:
            continue
        ranked = [UUID(value) for value in rescore_window(window, weights, depth=depth)]
        cases.append(
            score_case(
                golden,
                window.query_id,
                ranked,
                abstained=_abstained_of(window, rule),
                buckets=buckets,
            )
        )

    # Averaged over the ANSWERABLE queries, for the reason `split_readings` records: an
    # out-of-domain query scores zero for every configuration, so including it compresses
    # every difference without carrying any information about ranking.
    answerable = {
        query.id
        for query in golden.retrieval_queries
        if query.category != OUT_OF_DOMAIN
    }
    scored = [case for case in cases if case.query_id in answerable]
    readings = {"global": _reading(scored)}
    for name, wanted in (
        (DIAGNOSTIC_READING, True),
        (DECIDING_READING, False),
    ):
        members = {
            query.id
            for query in golden.retrieval_queries
            if bool(query.in_tuning_set) is wanted
        }
        readings[name] = _reading(
            [case for case in scored if case.query_id in members]
        )
    for category in sorted({query.category for query in golden.retrieval_queries}):
        members = {
            query.id
            for query in golden.retrieval_queries
            if query.category == category
        }
        readings[f"category:{category}"] = _reading(
            [case for case in cases if case.query_id in members]
        )
    return readings


def load_capture(path: Path) -> Capture:
    if not path.is_file():
        raise ConfigurationError(
            f"{path} does not exist. Run the capture phase first: the re-score phase reads a "
            "window it cannot produce, on purpose"
        )
    return Capture.from_json(path.read_text(encoding="utf-8"))


async def capture(
    config: EvalConfig,
    golden: GoldenSet,
    *,
    settings: Settings,
    search: ProductSearchPort,
    embed: EmbeddingClient,
) -> Capture:
    """Phase B: retrieve every query ONCE under the frozen fusion and persist its window.

    One provider call and one pair of statements per query, against the hundreds of weight
    combinations phase C then explores over the result in seconds. The business weights are
    pinned to zero here so that what is persisted is the fusion's own window: the re-score
    applies the whole ordering key from scratch, and a window already ordered by one weight
    configuration would silently bias every other.

    `low_confidence` is captured and not recomputed. It is the absence of cross-branch
    consensus, which the business weights do not change, and it feeds only the abstention rate
    — never the metric this sweep decides on.
    """
    from jbg_ai.api.auth import ServicePrincipal
    from jbg_ai.api.schemas.retrieval import RetrievalMode, RetrievalRequest
    from jbg_ai.evals.execute import TOP_K_FOR_FULL_WINDOW, harness_principal
    from jbg_ai.retrieval.orchestrator import retrieve_products

    fingerprint = FusionFingerprint.of(config, settings)
    windows: list[CapturedWindow] = []

    for query in golden.retrieval_queries:
        seen: list[CapturedCandidate] = []
        # Filled only when the rule read something other than the window below it, which on
        # today's golden set — every query unfiltered — is never. It is collected anyway so
        # that a filtered set captured later needs no change here.
        probe: list[tuple[float, ...]] = []

        def sink(candidates, _seen=seen) -> None:
            _seen.clear()
            _seen.extend(
                CapturedCandidate(
                    product_id=str(item.product_id),
                    sku=item.sku,
                    score=float(item.score),
                    price=item.price,
                    size_label=item.size_label,
                    materials=tuple(item.materials or ()),
                    qty_bucket=item.qty_bucket,
                    sales_30d=item.sales_30d,
                    family_id=None if item.family_id is None else str(item.family_id),
                    branches=tuple(item.reasons or ()),
                )
                for item in candidates
            )

        response = await retrieve_products(
            RetrievalRequest(
                query=query.text,
                top_k=TOP_K_FOR_FULL_WINDOW,
                mode=RetrievalMode(config.mode or "hybrid"),
            ),
            harness_principal(),
            settings=settings,
            embed=embed,
            search=search,
            expand_synonyms=config.expand_synonyms,
            rrf_k=config.rrf_k,
            branch_weight_lexical=config.branch_weight_lexical,
            branch_weight_vector=config.branch_weight_vector,
            coverage_rule=config.coverage_rule or COVERAGE_CONTINUOUS_RULE,
            branch_depth=config.branch_depth,
            pos_prefilter=config.pos_prefilter,
            signal_pos_id=UUID(config.signal_pos_id) if config.signal_pos_id else None,
            business_weight_availability=0.0,
            on_fused_candidates=sink,
            on_abstention_profile=probe.append,
        )
        windows.append(
            CapturedWindow(
                query_id=query.id,
                query_text=query.text,
                low_confidence=response.low_confidence,
                candidates=tuple(seen),
                probe_distances=probe[-1] if probe else None,
            )
        )

    return Capture(
        version=CAPTURE_VERSION,
        golden_set_version=golden.version,
        fusion=fingerprint,
        windows=tuple(windows),
        buckets=(
            await search.scope_buckets(UUID(config.signal_pos_id))
            if config.signal_pos_id
            else {}
        ),
        # Recorded whether or not any window needed it. It costs three numbers and it states
        # the regime the capture was taken in, which is the same argument that put the fusion
        # fingerprint here: a reader of the file should not have to reconstruct the rule from
        # an environment that has moved on.
        abstention=AbstentionRule(
            enabled=settings.jpv_abstention_enabled,
            band_alpha=settings.jpv_abstention_band_alpha,
            min_candidates=settings.jpv_abstention_band_min_candidates,
        ),
    )


def business_grid(availability: tuple[float, ...]) -> tuple[BusinessWeights, ...]:
    """Every weight configuration the re-score explores. One dimension, and barely that.

    **The grid has two distinct outcomes, not as many as it has points**, and saying so is
    part of the result rather than a caveat about it: with a single binary term the business
    score takes two values, so every positive weight produces the same ranking. The sweep is
    run over several values anyway — cheaply, offline — because a grid that reports the
    invariance is evidence, while asserting it would be an argument.
    """
    return tuple(BusinessWeights(availability=value) for value in availability)
