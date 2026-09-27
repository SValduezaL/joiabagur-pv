"""The three deterministic checks, one by one. C30b. No provider, no model, no I/O.

The gate is the piece of this change with the most to prove, so it is tested against the
corpus figures that motivated it rather than against invented ones: `750` and `585` really do
live in `material-oro.md`, which is why a pure whitelist admits «750 €».
"""

from __future__ import annotations

import pytest

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
    PITCH_VIOLATION_CAUSES,
    STOCK_MARKERS,
)
from jbg_ai.assist.prompt import (
    FreeQueryPayload,
    PitchCitation,
    PitchPayload,
    payload_from,
)
from jbg_ai.assist.schema import AssistPitch
from jbg_ai.assist.schema import UsedCitation
from jbg_ai.assist.verification import (
    check_correspondence,
    check_numeric_gate,
    check_resolution,
    normalise_text,
    repair_message,
    verify,
)
from support.assist_pitch import pitch

#: The real sentence of `data/knowledge/material-oro.md`, which is the whole point: the figures
#: that open a pure whitelist are the corpus's own.
GOLD_SHEET = (
    "El oro de 18 quilates son 750 milésimas de oro puro, y el de 14 quilates son 585."
)

OFFERED = "material-oro#que-significa-750-y-18k"


def _payload(**overrides):
    values = dict(
        sku="JBG-0001",
        piece_type="anillo",
        materials=["oro"],
        variant_label="18 mm",
        citations=[
            PitchCitation(
                citation_id=OFFERED,
                document_title="El oro",
                section_title="Qué significa 750 y 18k",
                claim_scope="general",
                content=GOLD_SHEET,
            )
        ],
    )
    values.update(overrides)
    return payload_from(**values)


def _causes(violations) -> list[str]:
    return [item.cause for item in violations]


# --- 6.1 · resolution ----------------------------------------------------------------------


def test_dangling_citation_is_never_published() -> None:
    """HU escenario 6, first half. An identifier that was never handed over does not resolve,
    and a violation is recorded rather than the citation quietly dropped."""
    declared = [UsedCitation(citation_id="material-plata#inventada", supported_claim="x")]

    violations = check_resolution(declared, _payload())

    assert _causes(violations) == [CAUSE_DANGLING_CITATION]
    assert violations[0].citation_id == "material-plata#inventada"


def test_an_identifier_that_was_handed_over_resolves() -> None:
    declared = [UsedCitation(citation_id=OFFERED, supported_claim="x")]

    assert check_resolution(declared, _payload()) == ()


# --- 6.2 · correspondence -----------------------------------------------------------------


def test_declared_claim_absent_from_pitch_is_recorded_as_violation() -> None:
    """The check that makes «these are the ones it used» verifiable instead of asserted."""
    declared = [UsedCitation(citation_id=OFFERED, supported_claim="resiste el cloro")]

    violations = check_correspondence(declared, "El oro de esta pieza envejece muy bien.")

    assert _causes(violations) == [CAUSE_CLAIM_NOT_IN_PITCH]
    assert violations[0].citation_id == OFFERED


def test_a_declared_claim_matches_across_case_and_runs_of_whitespace() -> None:
    """`casefold()` and collapsed whitespace, and deliberately nothing else: softening the
    comparison without a measurement in front of it is what this project stopped doing at C21."""
    declared = [UsedCitation(citation_id=OFFERED, supported_claim="EL   Oro\nde esta")]

    assert check_correspondence(declared, "El oro de esta pieza envejece bien.") == ()


def test_punctuation_is_not_folded_and_that_is_the_open_measurement() -> None:
    """Declared, not an oversight: if the sweep measures more than one failure in ten caused by
    punctuation, sign folding is added **then**, with the figure written down."""
    declared = [UsedCitation(citation_id=OFFERED, supported_claim="el oro, de esta")]

    assert _causes(check_correspondence(declared, "El oro de esta pieza.")) == [
        CAUSE_CLAIM_NOT_IN_PITCH
    ]


def test_an_empty_declared_claim_is_a_violation_and_not_a_free_pass() -> None:
    """An empty string is a substring of every text, so admitting it would hand back exactly
    the trivial satisfaction the span exists to remove."""
    declared = [UsedCitation(citation_id=OFFERED, supported_claim="   ")]

    assert _causes(check_correspondence(declared, "El oro de esta pieza.")) == [
        CAUSE_CLAIM_NOT_IN_PITCH
    ]


def test_echoing_every_supplied_identifier_does_not_satisfy_the_requirement() -> None:
    """The hole the span exists to close, stated as the spec states it.

    A model that declares every identifier it was handed passes resolution perfectly and
    trivially. The spans are what refuse it: five citations oblige five real fragments of the
    text that was written, and an invented fragment is a substring of nothing.
    """
    payload = _payload(
        citations=[
            PitchCitation(OFFERED, "El oro", "750 y 18k", "general", GOLD_SHEET),
            PitchCitation(
                "material-oro#cuidados-y-limpieza-en-casa",
                "El oro",
                "Cuidados",
                "general",
                "Límpialo con un paño suave.",
            ),
        ]
    )
    echoed = [
        UsedCitation(citation_id=item.citation_id, supported_claim="el oro envejece bien")
        for item in payload.citations
    ]

    assert check_resolution(echoed, payload) == ()
    assert _causes(check_correspondence(echoed, "Una pieza preciosa.")) == [
        CAUSE_CLAIM_NOT_IN_PITCH,
        CAUSE_CLAIM_NOT_IN_PITCH,
    ]


# --- 6.3 · the numeric gate ----------------------------------------------------------------


def test_figure_absent_from_context_is_rejected_even_if_plausible() -> None:
    """HU escenario 4. A weight in grams nobody handed over is an invention however plausible."""
    violations = check_numeric_gate("Pesa 4 gramos y sienta muy bien.", _payload())

    assert _causes(violations) == [CAUSE_FIGURE_NOT_IN_CONTEXT]
    assert violations[0].figure == "4"


def test_a_figure_present_in_the_context_is_admitted() -> None:
    assert check_numeric_gate("Es oro de 750 milésimas.", _payload()) == ()
    assert check_numeric_gate("La talla 18 mm te irá bien.", _payload()) == ()


@pytest.mark.parametrize("marker", CURRENCY_MARKERS)
def test_price_adjacent_figure_is_rejected_even_when_whitelisted(marker: str) -> None:
    """HU escenario 5, and the measurement this whole rule comes from.

    With `material-oro` in context, `750` **belongs** to the whitelist — the sheet says
    eighteen carats are seven hundred and fifty thousandths — so a pure whitelist lets «750 €»
    through, which is precisely the hole the gate existed to close. Adjacency refuses it
    whether or not the numeral is admitted.
    """
    payload = _payload()
    assert "750" in payload.numerals(), "the premise: the corpus itself whitelists it"

    violations = check_numeric_gate(f"Te lo llevas por 750 {marker}.", payload)

    assert _causes(violations) == [CAUSE_CURRENCY_ADJACENT]
    assert violations[0].figure == "750"


def test_the_recorded_cause_tells_currency_adjacency_from_absence_from_the_context() -> None:
    """A rejection rate is only readable partitioned by cause; a single number cannot tell a
    gate that works from a gate that gets in the way."""
    whitelisted = check_numeric_gate("Son 750 €.", _payload())
    invented = check_numeric_gate("Pesa 4 gramos.", _payload())

    assert whitelisted[0].cause != invented[0].cause
    assert {whitelisted[0].cause, invented[0].cause} <= set(PITCH_VIOLATION_CAUSES)


@pytest.mark.parametrize("marker", STOCK_MARKERS)
def test_a_figure_adjacent_to_a_stock_expression_is_rejected(marker: str) -> None:
    payload = _payload()
    text = f"{marker} 18 hoy." if marker in {"quedan", "en stock"} else f"Hay 18 {marker}."

    assert _causes(check_numeric_gate(text, payload)) == [CAUSE_STOCK_ADJACENT]


def test_the_placeholders_carry_no_figure_and_pass_the_gate_untouched() -> None:
    """`{{price}}` and `{{stock}}` are not numerals: they are the tokens .NET resolves."""
    assert check_numeric_gate(
        "Cuesta {{price}} y quedan {{stock}} disponibles.", _payload()
    ) == ()


def test_an_enumeration_numeral_is_rejected_and_classified_apart() -> None:
    """Still a violation — the gate forgives nothing — but named, because the prompt is where
    that failure is removed and the classification is what says whether the prompt is working."""
    violations = check_numeric_gate("1. Es de oro\n2. Y va bien", _payload())

    assert _causes(violations) == [CAUSE_ENUMERATION_FORMAT, CAUSE_ENUMERATION_FORMAT]
    assert set(_causes(violations)) <= set(HARD_VIOLATION_CAUSES)


def test_a_separator_disagreement_is_rejected_and_classified_apart() -> None:
    """`1.500` against a context carrying `1500` is refused too, and the cause is what would
    justify a separator rule later — with the figure in front of it, not before."""
    payload = _payload(
        citations=[
            PitchCitation(
                OFFERED, "El oro", "Pureza", "general", "La pieza pesa 1500 miligramos."
            )
        ]
    )

    violations = check_numeric_gate("Pesa 1.5.00 miligramos.", payload)

    assert _causes(violations) == [CAUSE_DECIMAL_FORM]


def test_every_cause_the_gate_can_record_belongs_to_the_closed_vocabulary() -> None:
    payload = _payload()
    produced = set()
    for text in (
        "Pesa 4 gramos.",
        "Son 750 €.",
        "Quedan 3 unidades.",
        "1. Primero",
    ):
        produced |= set(_causes(check_numeric_gate(text, payload)))
    produced |= set(
        _causes(check_resolution([UsedCitation(citation_id="x#y", supported_claim="a")], payload))
    )
    produced |= set(_causes(check_correspondence(
        [UsedCitation(citation_id=OFFERED, supported_claim="no está")], "otra cosa"
    )))

    assert produced <= set(PITCH_VIOLATION_CAUSES)


# --- the order, and the single repair ------------------------------------------------------


def test_the_checks_run_cheapest_first_and_report_every_violation_together() -> None:
    """Resolution, then correspondence, then the gate. One repair carries all of them, because
    the two gates fail for the same underlying reason rather than independently."""
    generated = pitch(
        "Una pieza de 4 gramos.",
        ("material-plata#inventada", "no aparece"),
    )

    causes = _causes(verify(generated, _payload()))

    assert causes == [
        CAUSE_DANGLING_CITATION,
        CAUSE_CLAIM_NOT_IN_PITCH,
        CAUSE_FIGURE_NOT_IN_CONTEXT,
    ]


def test_the_repair_message_names_every_violation_in_one_turn() -> None:
    violations = verify(
        pitch("Una pieza de 4 gramos.", ("material-plata#inventada", "no aparece")),
        _payload(),
    )

    message = repair_message(violations)

    assert message.count("\n- ") == 3
    for item in violations:
        assert item.detail in message


def test_correspondence_is_the_only_check_whose_failure_is_not_hard() -> None:
    """The two policies, read off the vocabulary rather than off a branch of the code."""
    assert CAUSE_CLAIM_NOT_IN_PITCH not in HARD_VIOLATION_CAUSES
    assert set(PITCH_VIOLATION_CAUSES) - set(HARD_VIOLATION_CAUSES) == {
        CAUSE_CLAIM_NOT_IN_PITCH
    }


def test_normalisation_collapses_case_and_whitespace_and_nothing_else() -> None:
    assert normalise_text("  El   ORO\nde\tley  ") == "el oro de ley"
    assert normalise_text("el oro, de ley") != normalise_text("el oro de ley")


# --- C40 · a placeholder written where no piece is anchored ---------------------------------


def test_placeholder_in_free_query_withholds_the_argument() -> None:
    """The guardrail that makes `assist/v5` a guarantee instead of a request.

    A placeholder with no anchor is not a stylistic slip: `PitchPlaceholderResolver` on the
    .NET side withholds the **whole** argument the moment it meets one, so what the operator
    would see is an empty pitch and no explanation. Catching it here names the cause.
    """
    payload = FreeQueryPayload(query="algo de plata")
    generated = AssistPitch(
        pitch="Estas piezas son sobrias y van bien a diario, y cuestan {{price}}.",
        used=(),
    )

    violations = verify(generated, payload)

    assert [violation.cause for violation in violations] == [
        CAUSE_PLACEHOLDER_IN_FREE_QUERY
    ]
    assert violations[0].is_hard, "it deletes the argument downstream, so it is a hard cause"


def test_both_placeholders_are_reported_apart() -> None:
    payload = FreeQueryPayload(query="algo de plata")
    generated = AssistPitch(
        pitch="Cuesta {{price}} y quedan {{stock}} unidades.", used=()
    )

    causes = [violation.cause for violation in verify(generated, payload)]

    assert causes == [CAUSE_PLACEHOLDER_IN_FREE_QUERY] * 2


def test_anchored_mode_placeholder_is_not_a_violation() -> None:
    """With one piece named the placeholder is what the prompt **asks** for.

    The asymmetry is the whole rule: .NET resolves it against the anchored piece, which is what
    keeps this service from ever writing a price. Flagging it here would break the two modes
    that have worked since C30b.
    """
    payload = PitchPayload(sku="JBG-0001", query="¿se puede mojar?")
    generated = AssistPitch(
        pitch="Cuesta {{price}} y quedan {{stock}} unidades.", used=()
    )

    causes = [violation.cause for violation in verify(generated, payload)]

    assert CAUSE_PLACEHOLDER_IN_FREE_QUERY not in causes


def test_a_free_query_argument_without_placeholders_passes() -> None:
    """The shape `assist/v5` asks for: comparative language, no figure, no marker."""
    payload = FreeQueryPayload(query="algo de plata")
    generated = AssistPitch(
        pitch="De las tres, la más sobria es la de aro fino y la más vistosa la de eslabón.",
        used=(),
    )

    assert verify(generated, payload) == ()


def test_the_cause_is_in_both_vocabularies() -> None:
    """It must be partitionable in the sweep **and** hard, which are two separate tuples."""
    assert CAUSE_PLACEHOLDER_IN_FREE_QUERY in PITCH_VIOLATION_CAUSES
    assert CAUSE_PLACEHOLDER_IN_FREE_QUERY in HARD_VIOLATION_CAUSES
