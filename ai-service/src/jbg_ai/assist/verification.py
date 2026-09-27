"""The three deterministic checks over a generated argument. Delivered by C30b.

No model judges anything here. Each check is code, each violation names a **cause** from a
closed vocabulary, and the three run in order of cost — resolution (`issubset` over at most
five elements), correspondence (a substring), the numeric gate (a walk over the text) — which
is the cheap-before-expensive funnel applied inside a single call.

**What the three do and do not buy.**

    resolución       la fuente existe y estuvo en el contexto
    correspondencia  la cita se usó PARA ALGO EFECTIVAMENTE ESCRITO
    puerta numérica  ninguna cifra de precio o de stock llega al mostrador
    ─────────────────────────────────────────────────────────────────────
    fidelidad        que el fragmento DIGA lo que la frase afirma  ← ninguna

The last row is the *alucinación con coartada* and it is declared rather than solved: no model
judge runs in the serving path — it would double the latency and the cost where a customer is
waiting, and using a model to catch another model's fabrications is circular. It is measured
with RAGAS in C38, over a representative set, where a rate means something.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from jbg_ai.assist.constants import (
    CAUSE_CLAIM_NOT_IN_PITCH,
    CAUSE_CURRENCY_ADJACENT,
    CAUSE_DANGLING_CITATION,
    CAUSE_DECIMAL_FORM,
    CAUSE_ENUMERATION_FORMAT,
    CAUSE_FIGURE_NOT_IN_CONTEXT,
    CAUSE_PLACEHOLDER_IN_FREE_QUERY,
    CAUSE_STOCK_ADJACENT,
    CURRENCY_MARKERS,
    HARD_VIOLATION_CAUSES,
    PRICE_PLACEHOLDER,
    STOCK_MARKERS,
    STOCK_PLACEHOLDER,
)
from jbg_ai.assist.prompt import (
    ENUMERATION,
    NUMERAL,
    PitchContext,
    loose_numeral,
    normalise_numeral,
)
from jbg_ai.assist.schema import AssistPitch, UsedCitation

_WHITESPACE = re.compile(r"\s+")


def _marker_alternation(markers: Sequence[str]) -> str:
    """One alternation, built **from the constant** rather than restated as a literal regex.

    A marker that starts and ends with a letter gets word boundaries; `€` cannot have them, and
    a `\\b` next to a symbol would silently never match — the kind of blacklist that looks
    present and is not.
    """
    parts = []
    for marker in markers:
        escaped = re.escape(marker)
        lead = r"\b" if marker[:1].isalpha() else ""
        tail = r"\b" if marker[-1:].isalpha() else ""
        parts.append(f"{lead}{escaped}{tail}")
    return "|".join(parts)


def _after(markers: Sequence[str]) -> re.Pattern[str]:
    return re.compile(rf"\A\s*(?:{_marker_alternation(markers)})", re.IGNORECASE)


def _before(markers: Sequence[str]) -> re.Pattern[str]:
    return re.compile(rf"(?:{_marker_alternation(markers)})\s*\Z", re.IGNORECASE)


#: Immediate adjacency and nothing wider. A window of a few words would fire on «en stock» said
#: one clause earlier and reject «talla 12» in the next, which is the false positive that costs
#: the whole argument; the marker has to be the token **touching** the numeral.
_CURRENCY_AFTER = _after(CURRENCY_MARKERS)
_CURRENCY_BEFORE = _before(CURRENCY_MARKERS)
_STOCK_AFTER = _after(STOCK_MARKERS)
_STOCK_BEFORE = _before(STOCK_MARKERS)


@dataclass(frozen=True)
class Violation:
    """One failed check. `cause` is the partition the sweep publishes its rejection rate by."""

    cause: str
    detail: str
    citation_id: str | None = None
    figure: str | None = None

    @property
    def is_hard(self) -> bool:
        """Does surviving this cost the whole argument, or only one citation?"""
        return self.cause in HARD_VIOLATION_CAUSES


def normalise_text(value: str) -> str:
    """`casefold()` and collapsed whitespace, **and nothing else**.

    Deliberately not sign folding. Softening a check without a figure in front of it is what
    this project has not done since C21: if the sweep measures that more than one failure in
    ten is punctuation, the folding is added then, with the number written down.
    """
    return _WHITESPACE.sub(" ", value.casefold()).strip()


def check_resolution(
    used: Sequence[UsedCitation], payload: PitchContext
) -> tuple[Violation, ...]:
    """Every declared identifier belongs to the set handed over. A dangling one is never
    ignored: it is repaired once and, if it survives, it takes the argument with it."""
    offered = payload.citation_ids()
    return tuple(
        Violation(
            cause=CAUSE_DANGLING_CITATION,
            detail=(
                f"el identificador «{item.citation_id}» no estaba entre los entregados"
            ),
            citation_id=item.citation_id,
        )
        for item in used
        if item.citation_id not in offered
    )


def check_correspondence(
    used: Sequence[UsedCitation], pitch: str
) -> tuple[Violation, ...]:
    """The declared span occurs literally in the argument that was produced.

    A blank span is a violation and not a pass. An empty string is a substring of every text,
    so admitting it would hand back exactly the trivial satisfaction the span exists to remove.
    """
    normalised = normalise_text(pitch)
    violations = []
    for item in used:
        claim = normalise_text(item.supported_claim)
        if not claim:
            violations.append(
                Violation(
                    cause=CAUSE_CLAIM_NOT_IN_PITCH,
                    detail=(
                        f"la cita «{item.citation_id}» no declara ningún tramo del "
                        "argumentario"
                    ),
                    citation_id=item.citation_id,
                )
            )
        elif claim not in normalised:
            violations.append(
                Violation(
                    cause=CAUSE_CLAIM_NOT_IN_PITCH,
                    detail=(
                        f"el tramo declarado para «{item.citation_id}» no aparece "
                        f"literalmente en el argumentario: «{item.supported_claim}»"
                    ),
                    citation_id=item.citation_id,
                )
            )
    return tuple(violations)


def _adjacency_cause(pitch: str, start: int, end: int) -> str | None:
    """Currency or stock touching this numeral, on either side. Independent of the whitelist."""
    before, after = pitch[:start], pitch[end:]
    if _CURRENCY_AFTER.match(after) or _CURRENCY_BEFORE.search(before):
        return CAUSE_CURRENCY_ADJACENT
    if _STOCK_AFTER.match(after) or _STOCK_BEFORE.search(before):
        return CAUSE_STOCK_ADJACENT
    return None


def check_numeric_gate(pitch: str, payload: PitchContext) -> tuple[Violation, ...]:
    """Whitelist by membership in the payload object, **plus** adjacency to money or stock.

    The adjacency rule is the whole reason a pure whitelist does not close this: measured on
    the corpus, `material-oro.md` states that eighteen carats are seven hundred and fifty
    thousandths and fourteen are five hundred and eighty-five, so with that sheet in context
    `750` **belongs to the whitelist** and «750 €» walks straight through the gate that exists
    to stop it. Adjacency therefore rejects whether or not the numeral is admitted, and it is
    the single blacklist of the design: the set of currency marks is closed and unambiguous,
    unlike "numbers in jewellery", which is what made blacklists the wrong tool for the numeral
    itself.
    """
    whitelist = payload.numerals()
    loose_whitelist = payload.loose_numerals()
    enumerations = {match.start(1) for match in ENUMERATION.finditer(pitch)}

    violations = []
    for match in NUMERAL.finditer(pitch):
        raw = match.group()
        adjacency = _adjacency_cause(pitch, match.start(), match.end())
        if adjacency is not None:
            violations.append(
                Violation(
                    cause=adjacency,
                    detail=(
                        f"la cifra «{raw}» aparece pegada a una marca de "
                        + (
                            "moneda"
                            if adjacency == CAUSE_CURRENCY_ADJACENT
                            else "existencias"
                        )
                        + "; el precio y la disponibilidad van como {{price}} y {{stock}}"
                    ),
                    figure=raw,
                )
            )
            continue
        if normalise_numeral(raw) in whitelist:
            continue
        if match.start() in enumerations:
            cause = CAUSE_ENUMERATION_FORMAT
            detail = (
                f"la cifra «{raw}» encabeza un elemento de lista; el argumentario es "
                "prosa corrida"
            )
        elif loose_numeral(raw) in loose_whitelist:
            cause = CAUSE_DECIMAL_FORM
            detail = (
                f"la cifra «{raw}» no coincide con ninguna de los datos salvo por los "
                "separadores"
            )
        else:
            cause = CAUSE_FIGURE_NOT_IN_CONTEXT
            detail = f"la cifra «{raw}» no aparece en los datos entregados"
        violations.append(Violation(cause=cause, detail=detail, figure=raw))
    return tuple(violations)


def check_free_query_placeholders(
    pitch: str, payload: PitchContext
) -> tuple[Violation, ...]:
    """A price or stock placeholder written where no piece is anchored. C40.

    **Checked only when nothing is anchored**, and the asymmetry is the whole rule. With one
    piece named, a placeholder is not a fault but exactly what the prompt asks for: the .NET side
    substitutes the real figure, which is what keeps this service from ever writing a price.

    Without an anchor there is nothing to substitute it against, and
    `PitchPlaceholderResolver` withholds the **entire** argument the moment it meets one — by
    design, and with a test on the other side fixing it. So this is not a stylistic slip that
    degrades the prose: it deletes it. `assist/v5` asks the model not to write them; this is what
    makes the asking a guarantee, and what makes the frequency readable **partitioned by cause**
    rather than surfacing as an unexplained drop in delivered arguments.

    One violation per marker present, not one per occurrence: the repair message needs to name
    which marker to remove, and naming it twice adds nothing.
    """
    if payload.is_anchored:
        return ()

    return tuple(
        Violation(
            cause=CAUSE_PLACEHOLDER_IN_FREE_QUERY,
            detail=(
                f"«{marker}» no puede aparecer en una consulta sin pieza anclada: no hay nada "
                "contra lo que resolverlo. Habla de la pieza sin nombrar precio ni existencias."
            ),
        )
        for marker in (PRICE_PLACEHOLDER, STOCK_PLACEHOLDER)
        if marker in pitch
    )


def verify(generated: AssistPitch, payload: PitchContext) -> tuple[Violation, ...]:
    """The four checks, cheapest first, with every violation collected rather than the first.

    All of them are returned because all of them travel in **one** repair: the gates fail
    for the same underlying reason — a model that invents a price is the one that hangs a
    citation — so they are not independent faults deserving separate attempts.
    """
    return (
        check_resolution(generated.used, payload)
        + check_correspondence(generated.used, generated.pitch)
        + check_numeric_gate(generated.pitch, payload)
        + check_free_query_placeholders(generated.pitch, payload)
    )


def repair_message(violations: Sequence[Violation]) -> str:
    """The single repair turn, with every violation of every check communicated together."""
    lines = [
        "El argumentario que has escrito incumple estas comprobaciones. Reescríbelo "
        "entero corrigiéndolas TODAS a la vez, respetando las reglas del mensaje de "
        "sistema y sin añadir nada nuevo:",
        "",
    ]
    lines += [f"- {item.detail}" for item in violations]
    lines += [
        "",
        "Recuerda: ninguna cifra que no esté en los datos entregados, ninguna cifra "
        "pegada a una marca de moneda o de existencias, sólo los identificadores de cita "
        "entregados, y el tramo de cada cita copiado literalmente del argumentario que "
        "escribas ahora.",
    ]
    return "\n".join(lines)
