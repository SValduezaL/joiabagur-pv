"""The routing evaluation: the manifest, the confusion matrix, and the veto. C31.

**Five of the six classes are referenced and not copied**, which is the manifest's own decision
and the reason this module resolves them rather than reading a list: the day somebody adds a
query to the golden set or an `eval_question` to a document, a copied fixture would fall behind
in silence. It is the same argument C23 used to put the evaluation question *inside* each
corpus document.

**Loading validates, and a violation is a refusal rather than a warning**, exactly as
`evals/golden.py` does it. A manifest that declares 48 `catalog` cases against a golden set
holding 47 is a manifest describing a measurement nobody can reproduce, and the cheapest moment
to find that out is before the provider is called 119 times.

    catalog           48   golden, ocho categorías juzgadas          C24 / C26
    not_in_catalogue  20   golden, categoría `fuera-de-dominio`      C24
    out_of_domain      5   data/knowledge/_eval/out-of-domain.yaml   C23
    knowledge         32   marca `eval_question`, una por documento  C23
    ambiguous          4   golden, categoría `ambigua`, sin juicios  C24
    both              10   escritos en el manifiesto                 C31
    ──────────────────────────────────────────────────────────────────────
                     119

**The veto is computed here and is not a judgement call.** A single `descripcion-sin-anclaje`
query silenced rejects the configuration however many of the twenty impossible ones it catches.
The asymmetry is the one already measured and argued in `retrieval/abstention.py`: silencing a
query the shop *can* answer is a visible failure at the counter, while failing to refuse an
impossible one shows candidates that do not fit and the operator sees that.

**The two rates are reported apart and never summed.** The router's refusal rate comes from
here; the retriever's abstention rate comes from C25 and is not recomputed, because recomputing
it would need the live index and would produce a *third* number that looks like the published
one and is not. It travels as a declared figure with its provenance beside it.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from jbg_ai.assist.constants import ROUTER_PROMPT_VERSION
from jbg_ai.evals.errors import EvalError
from jbg_ai.evals.golden import GOLDEN_DIR, load_queries
from jbg_ai.knowledge.corpus import load_corpus

#: Where the manifest lives, and the directory its relative `file:` references resolve against.
ROUTING_DIR = Path(__file__).resolve().parents[3] / "evals" / "routing"
CASES_FILE = "cases.yaml"
RESULTS_DIR = Path(__file__).resolve().parents[3] / "evals" / "results"

#: The six classes, in the order the confusion matrix prints them.
ROUTING_CLASSES: tuple[str, ...] = (
    "catalog",
    "knowledge",
    "both",
    "ambiguous",
    "not_in_catalogue",
    "out_of_domain",
)

#: The class whose false positives decide whether the router is served at all. D12.
VETO_CLASS = "catalog"

#: And, inside it, the category that carries the veto in its sharpest form: twelve queries that
#: name **no piece type at all** — `joya con forma de concha marina` — and are exactly the ones
#: the vector branch exists to serve. A lexical rule dies on them, and so would a classifier
#: that learned "names one of the twelve terms" instead of "asks for an object we sell".
VETO_CATEGORY = "descripcion-sin-anclaje"

#: The retriever's abstention rate, **published by C25 and not recomputed here**. Recomputing it
#: would need the live index and would produce a third number that looks like the published one
#: and is not. The two rates below are never summed: one reads the shape of the distance profile
#: after retrieving, the other classifies before.
C25_ABSTENTION_RATE = 0.10
C25_ABSTENTION_SOURCE = (
    "C25, `evals/results/c25-sweep-fase-a.md`; measured over the 43 answerable queries the "
    "golden set held before C26 added the five `sustituto` ones"
)


class RoutingCasesError(EvalError):
    """The manifest does not describe the tree it references. Never a warning."""


@dataclass(frozen=True)
class RoutingCase:
    """One labelled query. `category` is the golden category, when it comes from there.

    The category travels because the veto needs it: `catalog` is one class of 48 and the twelve
    `descripcion-sin-anclaje` queries inside it are the ones a single silencing rejects the
    configuration over.
    """

    id: str
    text: str
    expected: str
    source: str
    category: str | None = None


@dataclass(frozen=True)
class RoutingCases:
    """The 119 labelled cases, loaded and validated."""

    version: int
    cases: tuple[RoutingCase, ...]
    declared: dict[str, int]

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.cases)

    def __len__(self) -> int:
        return len(self.cases)

    def of(self, expected: str) -> tuple[RoutingCase, ...]:
        return tuple(case for case in self.cases if case.expected == expected)

    def counts(self) -> dict[str, int]:
        return dict(Counter(case.expected for case in self.cases))


def _golden_by_category(categories: Sequence[str], *, expected: str) -> list[RoutingCase]:
    wanted = set(categories)
    return [
        RoutingCase(
            id=query.id,
            text=query.text,
            expected=expected,
            source="golden",
            category=query.category,
        )
        # `load_queries` and not `load_golden_set`: the composition check of the golden set is
        # its own business and failing it here would report the wrong problem.
        for query in load_queries(GOLDEN_DIR)
        if query.category in wanted
    ]


def _corpus_eval_questions(*, expected: str) -> list[RoutingCase]:
    """One question per corpus document, read from the document itself. Authoring rule 7."""
    return [
        RoutingCase(
            id=f"kq-{document.slug}",
            text=document.eval_question,
            expected=expected,
            source="corpus",
        )
        for document in load_corpus().documents
    ]


def _out_of_domain(path: Path, *, expected: str) -> list[RoutingCase]:
    if not path.is_file():
        raise RoutingCasesError(f"the manifest references {path}, which does not exist")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [
        RoutingCase(
            id=f"ood-{index:02d}",
            text=str(item["text"]).strip(),
            expected=expected,
            source="corpus_eval",
        )
        for index, item in enumerate(payload.get("questions") or (), start=1)
    ]


def load_routing_cases(root: Path | None = None) -> RoutingCases:
    """Read the manifest, resolve its five references, and **refuse** a count that does not add up.

    Every declared `expected_count` is checked against what the tree actually holds, and the
    failure names the class, the declared number and the real one. A manifest that quietly
    described 47 cases as 48 would make a rate unreproducible in a way nothing later could
    detect, which is the same defect the golden set's own composition check exists to prevent.
    """
    base = root or ROUTING_DIR
    path = base / CASES_FILE
    if not path.is_file():
        raise RoutingCasesError(f"{path} does not exist")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    cases: list[RoutingCase] = []
    declared: dict[str, int] = {}

    for name, spec in (payload.get("sources") or {}).items():
        declared[name] = int(spec["expected_count"])
        origin = spec.get("from")
        if origin == "golden":
            resolved = _golden_by_category(spec["categories"], expected=name)
        elif origin == "corpus":
            resolved = _corpus_eval_questions(expected=name)
        elif origin == "corpus_eval":
            resolved = _out_of_domain((base / spec["file"]).resolve(), expected=name)
        else:
            raise RoutingCasesError(
                f"class «{name}» declares an unknown source «{origin}»"
            )
        cases.extend(resolved)

    inline = payload.get("both") or ()
    declared["both"] = len(inline)
    cases.extend(
        RoutingCase(
            id=str(item["id"]),
            text=str(item["text"]).strip(),
            expected="both",
            source="manifest",
        )
        for item in inline
    )

    real = Counter(case.expected for case in cases)
    for name, count in declared.items():
        if real[name] != count:
            raise RoutingCasesError(
                f"class «{name}» declares {count} cases and the tree holds {real[name]}; "
                "a manifest that does not describe the tree makes the measurement "
                "unreproducible, so the load refuses rather than warns"
            )
    if len(set(case.id for case in cases)) != len(cases):
        raise RoutingCasesError("two cases share an identifier")
    unknown = sorted(set(real) - set(ROUTING_CLASSES))
    if unknown:
        raise RoutingCasesError(f"the manifest declares classes this module does not know: {unknown}")

    return RoutingCases(
        version=int(payload.get("version", 0)),
        cases=tuple(cases),
        declared=declared,
    )


def predicted_class(decision) -> str:
    """The class a `RouteDecision` amounts to. **Code, and never the model's own word.**

    Ambiguity is read **before** the index: a query the classifier admits but cannot search
    with is answered by a question, whatever index it would otherwise have gone to. The two
    refusals come first of all, because `index` is null on both and reading it first would
    make every refusal look like a missing route.
    """
    if decision.served == "out_of_domain":
        return "out_of_domain"
    if decision.served == "not_in_catalogue":
        return "not_in_catalogue"
    if decision.missing_axis is not None:
        return "ambiguous"
    return decision.index or "catalog"


@dataclass
class ConfusionMatrix:
    """Expected against predicted, over the six classes, plus what could not be classified."""

    rows: dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))
    degraded: Counter = field(default_factory=Counter)

    def record(self, expected: str, predicted: str | None) -> None:
        if predicted is None:
            self.degraded[expected] += 1
            self.rows[expected]["degraded"] += 1
            return
        self.rows[expected][predicted] += 1

    def total(self, expected: str) -> int:
        return sum(self.rows[expected].values())

    def correct(self, expected: str) -> int:
        return self.rows[expected][expected]

    def accuracy(self, expected: str) -> float:
        total = self.total(expected)
        return self.correct(expected) / total if total else 0.0

    @property
    def refused(self) -> int:
        """Every case the router refused, whatever it was labelled as."""
        return sum(
            row[verdict]
            for row in self.rows.values()
            for verdict in ("out_of_domain", "not_in_catalogue")
        )

    @property
    def n(self) -> int:
        return sum(sum(row.values()) for row in self.rows.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "rows": {
                expected: dict(sorted(row.items())) for expected, row in sorted(self.rows.items())
            },
            "degraded": dict(sorted(self.degraded.items())),
        }


def false_positive_rate(matrix: ConfusionMatrix, expected: str = VETO_CLASS) -> float:
    """The rate at which an answerable query is **refused**. D12's figure, on its own.

    Not "accuracy on `catalog`": a `catalog` query the router sends to `knowledge` is a routing
    mistake and shows the operator an explanation instead of pieces, which is recoverable. One
    it *refuses* shows the operator nothing at all, which is the failure at the counter.
    """
    total = matrix.total(expected)
    if not total:
        return 0.0
    refused = matrix.rows[expected]["out_of_domain"] + matrix.rows[expected]["not_in_catalogue"]
    return refused / total


def veto_violations(
    results: Iterable[tuple[RoutingCase, str | None]]
) -> tuple[RoutingCase, ...]:
    """The answerable queries the configuration silenced. **Any one of them is the veto.**

    Declared before measuring, which is the whole point: a criterion agreed after seeing the
    numbers is a criterion that gets softened by the numbers.
    """
    return tuple(
        case
        for case, predicted in results
        if case.expected == VETO_CLASS
        and predicted in ("out_of_domain", "not_in_catalogue")
    )


def git_sha() -> str:
    """The revision this measurement ran at, or `unknown` — never a guess.

    **`GIT_SHA` wins over the subprocess, and that is not a convenience.** A measurement taken
    from inside the container has no `.git` around it, so the subprocess fails and the artifact
    records `unknown` — which is honest but useless, and it happened to the two artifacts that
    carry the figure deciding whether M1 has prose at all. Every real measurement against the
    provider runs in the container, so the path that has no sha is the normal path, not the
    exceptional one. Passing it in (`-e GIT_SHA=$(git rev-parse --short HEAD)`) is what makes
    those runs comparable; the subprocess stays for a run taken from the host.
    """
    from_env = os.environ.get("GIT_SHA", "").strip()
    if from_env:
        return from_env
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 — provenance, never a reason to fail a measurement
        return "unknown"


def provenance(*, model: str, run_id: str | None = None) -> dict[str, Any]:
    """What ties a result file to the tree that produced it. The C24 pattern, reused."""
    return {
        "run_id": run_id or uuid4().hex[:12],
        "git_sha": git_sha(),
        "prompt_version": ROUTER_PROMPT_VERSION,
        "model": model,
        "taken_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def report(
    matrix: ConfusionMatrix,
    *,
    violations: Sequence[RoutingCase],
    meta: dict[str, Any],
    per_category: dict[str, Counter] | None = None,
    results_for_coverage: Sequence[tuple[RoutingCase, str | None]] | None = None,
) -> dict[str, Any]:
    """The published object: **two rates apart, the false positive on its own, and the veto.**"""
    return {
        **meta,
        "n": matrix.n,
        "confusion_matrix": matrix.as_dict(),
        "accuracy_by_class": {
            name: round(matrix.accuracy(name), 4) for name in ROUTING_CLASSES
        },
        "rates": {
            "router_refusal_rate": round(matrix.refused / matrix.n, 4) if matrix.n else 0.0,
            "retriever_abstention_rate": C25_ABSTENTION_RATE,
            "retriever_abstention_source": C25_ABSTENTION_SOURCE,
            "summable": False,
            "note": (
                "The two rates are NOT summable and must never be presented as one figure. "
                "The retriever's abstention reads the shape of the distance profile AFTER "
                "retrieving; the router's refusal classifies BEFORE retrieving. They are "
                "measured over different sets by different mechanisms, and the whole reason "
                "this change exists is being able to publish them as two numbers."
            ),
        },
        "false_positive_on_answerable": {
            "class": VETO_CLASS,
            "rate": round(false_positive_rate(matrix), 4),
            "note": (
                "The rate at which a query the shop CAN answer is refused. Reported as a "
                "figure of its own because it is the one that decides whether the router is "
                "served at all, and because it is not the complement of any accuracy here."
            ),
        },
        "veto": {
            "criterion": (
                f"zero «{VETO_CATEGORY}» queries silenced; a single one rejects the "
                "configuration however many impossible ones it catches"
            ),
            "declared_before_measuring": True,
            "violations": [
                {"id": case.id, "text": case.text, "category": case.category}
                for case in violations
            ],
            # **A run that degraded cannot pass the veto, and the first version of this
            # report said it could.** Measured: a `gpt-4o` arm whose 89 of 119 cases died of
            # rate limits reported zero violations and PASSED — because a degraded case is
            # never a refusal. A criterion that a broken run satisfies is not a criterion, so
            # coverage over the veto class is part of the verdict and not a footnote.
            "veto_class_degraded": sum(
                1 for case, predicted in results_for_coverage if predicted is None
            )
            if results_for_coverage is not None
            else None,
            "veto_class_measured": sum(
                1 for case, predicted in results_for_coverage if predicted is not None
            )
            if results_for_coverage is not None
            else None,
            "passed": (
                not violations
                and results_for_coverage is not None
                and all(predicted is not None for _, predicted in results_for_coverage)
            ),
        },
        "degraded_total": sum(matrix.degraded.values()),
        "per_category": (
            {name: dict(sorted(row.items())) for name, row in sorted(per_category.items())}
            if per_category
            else {}
        ),
        "limitations": [
            "The ten `both` cases are CONSTRUCTED and derived from the corpus's own "
            "`eval_question` markers: they measure whether the router recognises a compound "
            "query, not how often an operator writes one.",
            "The twenty `not_in_catalogue` queries were CHOSEN to be unsatisfiable, so the "
            "precision measured over them is an UPPER BOUND on what a real counter would see.",
            "The classifier's prompt was written from `enrichment/vocabularies.yaml` and the "
            "corpus README, and NOT from the `note` fields of the golden set nor the `why` "
            "fields of this manifest, both of which state the classification rule in words.",
        ],
    }


def write_result(payload: dict[str, Any], *, name: str) -> Path:
    """Persist one run to `evals/results/`, tied to its run id."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}-{payload['run_id']}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return path


def resolved_credential() -> tuple[str | None, str]:
    """The classifier key and which link of the chain it came from. Never the key in a log."""
    for variable, label in (
        ("JPV_ROUTER_LLM_API_KEY", "router"),
        ("JPV_ASSIST_LLM_API_KEY", "assist_fallback"),
        ("JPV_RAG_LLM_API_KEY", "rag_fallback"),
    ):
        value = os.environ.get(variable)
        if value:
            return value, label
    return None, "absent"


# --- the runner -------------------------------------------------------------------------------


#: Causes the HARNESS retries and the serving path does not. **The distinction is the whole
#: point and it is one-sided.** A rate limit is a property of how fast this sweep asks, not of
#: the classifier: 119 cases at concurrency six produced 22 of them in one run and the matrix
#: read them as classification failures, which is publishing a transport artefact as a measured
#: behaviour. A reply that does not PARSE is never retried here, because that is exactly the
#: degradation the serving path has and the figure being measured.
HARNESS_RETRY_CAUSES: frozenset[str] = frozenset({"RateLimitError", "APIConnectionError"})


async def classify_all(
    cases: Sequence[RoutingCase],
    *,
    client,
    concurrency: int = 8,
    delay: float = 0.0,
    attempts: int = 8,
    backoff: float = 4.0,
    on_result=None,
) -> list[tuple[RoutingCase, str | None, str | None]]:
    """Classify every case. Returns `(case, predicted, degraded_cause)` in the manifest's order.

    **One call per case, and the only thing retried is a rate limit.** The serving path retries
    nothing at all, and neither does this for anything the classifier itself did: a reply that
    does not parse counts as a degradation in the matrix rather than being quietly re-rolled
    until it agrees, because re-rolling would measure the best of N attempts and publish it as
    the behaviour of one. A rate limit is different in kind — it says this sweep asked too fast.
    """
    import asyncio

    from jbg_ai.assist.routing import classify_query

    gate = asyncio.Semaphore(concurrency)

    async def one(case: RoutingCase):
        outcome = None
        for attempt in range(attempts):
            async with gate:
                outcome = await classify_query(case.text, client=client)
                if delay:
                    await asyncio.sleep(delay)
            if outcome.degraded_cause not in HARNESS_RETRY_CAUSES:
                break
            await asyncio.sleep(backoff * (attempt + 1))
        predicted = (
            None if outcome.decision is None else predicted_class(outcome.decision)
        )
        if on_result is not None:
            on_result(case, predicted, outcome.degraded_cause)
        return case, predicted, outcome.degraded_cause

    return list(await asyncio.gather(*(one(case) for case in cases)))


def build_matrix(
    results: Sequence[tuple[RoutingCase, str | None, str | None]]
) -> tuple[ConfusionMatrix, dict[str, Counter]]:
    """The matrix, plus the per-category breakdown the veto is read from."""
    matrix = ConfusionMatrix()
    per_category: dict[str, Counter] = defaultdict(Counter)
    for case, predicted, _ in results:
        matrix.record(case.expected, predicted)
        if case.category:
            per_category[case.category][predicted or "degraded"] += 1
    return matrix, dict(per_category)


def render_markdown(payload: dict[str, Any]) -> str:
    """The confusion matrix as a table a human reads, with the two rates kept apart."""
    matrix = payload["confusion_matrix"]["rows"]
    columns = list(ROUTING_CLASSES) + ["degraded"]
    lines = [
        f"# Matriz de confusión del enrutador de intención — {payload['run_id']}",
        "",
        f"- `git_sha`: `{payload['git_sha']}`",
        f"- `prompt_version`: `{payload['prompt_version']}`",
        f"- modelo: `{payload['model']}`",
        f"- tomada el: {payload['taken_at']}",
        f"- casos: **{payload['n']}**",
        "",
        "## Matriz",
        "",
        "Filas: clase esperada. Columnas: clase predicha.",
        "",
        "| esperada \ predicha | " + " | ".join(columns) + " | n | acierto |",
        "|---|" + "---|" * (len(columns) + 2),
    ]
    for name in ROUTING_CLASSES:
        row = matrix.get(name, {})
        total = sum(row.values())
        cells = []
        for column in columns:
            value = row.get(column, 0)
            cells.append(f"**{value}**" if column == name and value else str(value))
        accuracy = payload["accuracy_by_class"][name]
        lines.append(
            f"| `{name}` | " + " | ".join(cells) + f" | {total} | {accuracy:.0%} |"
        )

    rates = payload["rates"]
    false_positive = payload["false_positive_on_answerable"]
    veto = payload["veto"]
    lines += [
        "",
        "## Las dos cifras, que **no son sumables**",
        "",
        "| cifra | valor | mecanismo |",
        "|---|---|---|",
        f"| Rechazo del **enrutador** | {rates['router_refusal_rate']:.2%} | "
        "clasifica **antes** de recuperar |",
        f"| Abstención del **retriever** | {rates['retriever_abstention_rate']:.2%} | "
        "lee el perfil de distancias **después** de recuperar |",
        "",
        f"> {rates['note']}",
        "",
        f"Procedencia de la abstención: {rates['retriever_abstention_source']}.",
        "",
        "## El falso positivo sobre la clase contestable, como cifra propia",
        "",
        f"**{false_positive['rate']:.2%}** de las consultas de `{false_positive['class']}` "
        "quedaron silenciadas.",
        "",
        f"> {false_positive['note']}",
        "",
        "## El veto",
        "",
        f"Criterio: {veto['criterion']}.",
        f"Declarado antes de medir: **{veto['declared_before_measuring']}**.",
        "",
        f"**{'PASA' if veto['passed'] else 'NO PASA'}** — "
        f"{len(veto['violations'])} consulta(s) contestable(s) silenciada(s), "
        f"{veto.get('veto_class_measured')} medidas y "
        f"{veto.get('veto_class_degraded')} degradadas de la clase contestable.",
        "",
        f"Degradaciones en toda la pasada: **{payload.get('degraded_total', 0)}** de "
        f"{payload['n']}. Una pasada degradada **no puede pasar el veto**: un caso que no se "
        "clasificó no es un rechazo, así que cero violaciones sobre cero mediciones no es un "
        "aprobado sino una pasada rota.",
    ]
    if veto["violations"]:
        lines += ["", "| id | categoría | consulta |", "|---|---|---|"]
        lines += [
            f"| `{item['id']}` | `{item['category']}` | {item['text']} |"
            for item in veto["violations"]
        ]
    if payload.get("per_category"):
        lines += [
            "",
            "## Desglose por categoría del golden set",
            "",
            "| categoría | " + " | ".join(columns) + " |",
            "|---|" + "---|" * len(columns),
        ]
        for name, row in payload["per_category"].items():
            lines.append(
                f"| `{name}` | "
                + " | ".join(str(row.get(column, 0)) for column in columns)
                + " |"
            )
    lines += ["", "## Limitaciones declaradas", ""]
    lines += [f"{index}. {item}" for index, item in enumerate(payload["limitations"], start=1)]
    return "\n".join(lines) + "\n"
