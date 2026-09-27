"""The agent loop, its port, its guardrail and its six budgets. C32b.

Offline like the rest of this suite: no chat provider, no embedding provider, no network and no
database. Every port and every one of the three clients goes in through the constructor seam
the layer has required since C30a, and the scripted provider decides what the model asks for on
each turn — which is what lets a loop whose real behaviour is non-deterministic be tested
**deterministically**, one stop condition and one budget at a time.

The acceptance scenarios of HU-AIENG-032b are traced from here; each test that carries one
names it in its docstring so the mapping survives a rename.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import time
import uuid

import pytest

from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.api.schemas.assist import AgentAssistGroup, AssistGroup
from jbg_ai.assist.agent import (
    AgentBudgets,
    ToolCallTrace,
    _execute,
    agent_system_message,
    run_agent,
)
from jbg_ai.assist.agent_llm import AgentStep, AgentToolCall
from jbg_ai.assist.constants import (
    AGENT_BUDGET_STOP_REASONS,
    AGENT_PITCH_PROMPT_VERSION,
    AGENT_PROMPT_VERSION,
    AGENT_STOP_REASONS,
    AVAILABILITY_LABELS,
    AVAILABILITY_NO_SCOPE,
    AVAILABILITY_OUT_OF_STOCK,
    GROUP_ORIGIN_CATALOGUE,
    GROUP_ORIGIN_SUBSTITUTES,
    GROUP_ORIGINS,
    MAX_AGENT_CONCURRENT_TOOL_CALLS,
    MAX_AGENT_ITERATIONS,
    MAX_AGENT_PROVIDER_CALLS,
    MAX_AGENT_TOOL_CALLS,
    MAX_PITCH_PROVIDER_CALLS,
    MAX_ROUTER_PROVIDER_CALLS,
    PROMPT_VERSION,
    STOP_CLARIFICATION,
    STOP_CLOCK_BUDGET,
    STOP_CONTEXT_BUDGET,
    STOP_ITERATION_BUDGET,
    STOP_NO_CLIENT,
    STOP_NO_MORE_TOOLS,
    STOP_REFUSED,
    STOP_TOKEN_BUDGET,
    STOP_TOOL_BUDGET,
    TOOL_CAUSE_BUDGET_EXHAUSTED,
    TOOL_CAUSE_INVALID_ARGUMENT,
    TOOL_NAMES,
    TURN_ROLE_ASSISTANT,
    TURN_ROLE_OPERATOR,
    WARNING_QUERY_OUT_OF_DOMAIN,
)
from jbg_ai.assist.errors import AgentProviderError, TranscriptError
from jbg_ai.assist.prompt import load_prompt_file, prompt_sections
from jbg_ai.assist.routing import CLARIFICATION_TEMPLATES
from jbg_ai.assist.tools import ToolRegistry, build_registry
from jbg_ai.assist.transcript import turns_from
from jbg_ai.data.paths import AI_SERVICE_ROOT
from jbg_ai.knowledge.offline import InMemoryKnowledgeIndex
from support.assist_agent import finishes, refusing_agent, scripted_agent, wants
from support.assist_pitch import data_block, pitch, refusing_client, scripted_client
from support.assist_router import decision, refusing_router, scripted_router
from support.assist_world import FAMILY, PIECE, indexed_row, run
from support.fake_embedding_client import FakeEmbeddingClient
from support.fake_product_search import FakeProductSearch
from support.settings import TOKEN_TRACE_ID, build_settings

TALK = (
    (TURN_ROLE_OPERATOR, "busco un anillo de plata"),
    (TURN_ROLE_ASSISTANT, "te enseño lo que tenemos"),
    (TURN_ROLE_OPERATOR, "¿y en dorado?"),
)

#: A pitch with **no digit in it**, so the numeric gate has nothing to refuse and a test about
#: the loop is not accidentally a test about the gate.
CLEAN_PITCH = pitch(
    "Te encajan estas piezas de plata, con un acabado sobrio que sienta bien a diario."
)


def registry_over(
    search: FakeProductSearch,
    knowledge: InMemoryKnowledgeIndex,
    principal: ServicePrincipal,
    *,
    knowledge_threshold: float | None = None,
) -> ToolRegistry:
    """One registry over injected fakes. No port is constructed and no socket is opened.

    `knowledge_threshold` relaxes the corpus distance cut for the tests that need a fragment
    to come back at all: the fake embedding client derives its vectors from a hash, so the
    calibrated production threshold abstains on every question. It is the same knob, and the
    same reason, that `test_orchestrator.py` already uses to exercise the anchored question.
    """
    overrides = (
        {"jpv_knowledge_distance_threshold": knowledge_threshold}
        if knowledge_threshold is not None
        else {}
    )
    return build_registry(
        principal=principal,
        settings=build_settings(**overrides),
        embed=FakeEmbeddingClient(),
        search=search,
        knowledge=knowledge,
    )


def drive(
    *,
    search: FakeProductSearch,
    knowledge: InMemoryKnowledgeIndex,
    principal: ServicePrincipal,
    agent_script,
    router_script=(decision(),),
    pitch_script=(CLEAN_PITCH,),
    turns=TALK,
    budgets: AgentBudgets | None = None,
    agent_delay: float = 0.0,
    pitch_delay: float = 0.0,
    knowledge_threshold: float | None = None,
):
    """One request end to end over doubles. Returns the run and the three scripted providers."""
    registry = registry_over(
        search, knowledge, principal, knowledge_threshold=knowledge_threshold
    )
    agent_client, agent_provider = (
        scripted_agent(*agent_script, delay=agent_delay)
        if agent_script is not None
        else (None, None)
    )
    router_client, router_provider = (
        scripted_router(*router_script)
        if router_script is not None
        else (None, None)
    )
    pitch_client, pitch_provider = (
        scripted_client(*pitch_script, delay=pitch_delay)
        if pitch_script is not None
        else (None, None)
    )
    outcome = run(
        run_agent(
            turns_from(turns),
            principal,
            registry=registry,
            agent_client=agent_client,
            router_client=router_client,
            pitch_client=pitch_client,
            budgets=budgets or AgentBudgets(),
        )
    )
    return outcome, agent_provider, router_provider, pitch_provider, registry


# --- 3 · the port, and the type that cannot carry prose ------------------------------------


def test_the_agent_step_type_declares_no_field_able_to_carry_the_models_prose() -> None:
    """HU escenario 3, third clause. **The invariant is the type, not a later check.**

    A rule saying «the caller must not read this field» is a field the caller will read. This
    walks the declared fields instead of trusting the docstring, which is the same thing C32a
    did when it verified the read-only invariant by introspection rather than by a boolean.
    """
    names = {item.name for item in dataclasses.fields(AgentStep)}

    assert names == {
        "tool_calls",
        "usage",
        "finish_reason",
        "discarded_chars",
        "discarded_digest",
    }
    for forbidden in ("text", "content", "message", "prose", "reasoning"):
        assert forbidden not in names
    # The two that describe the discarded text are a length and a digest, never the text.
    assert dataclasses.fields(AgentStep)[3].type in ("int", int)


def test_the_adapter_discards_the_prose_and_records_only_its_length_and_digest() -> None:
    """HU escenario 3. The boundary is the adapter, and the text does not survive it."""
    client, _provider = scripted_agent(
        wants(("buscar_catalogo", {"consulta": "anillo"}), text="PROSA SECRETA DEL MODELO")
    )

    step = run(client.decide([{"role": "user", "content": "hola"}], []))

    assert step.discarded_chars == len("PROSA SECRETA DEL MODELO")
    assert step.discarded_digest is not None and len(step.discarded_digest) == 16
    assert "PROSA" not in json.dumps(dataclasses.asdict(step), default=str)


def test_a_provider_fault_of_one_turn_degrades_instead_of_escaping() -> None:
    """A fault costs the turn and not the request: the evidence already gathered is served."""
    client, _provider = scripted_agent(RuntimeError("the provider is down"))

    with pytest.raises(AgentProviderError) as caught:
        run(client.decide([{"role": "user", "content": "hola"}], []))

    assert caught.value.cause == "RuntimeError"


def test_an_argument_blob_that_is_not_an_object_becomes_an_invalid_argument(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """Not an exception and not empty arguments: the two are different things.

    A tool whose every field was optional would accept `{}` and run on defaults for a call the
    model meant differently, so «the blob did not parse» is carried as its own state and turned
    into an invalid-argument observation **without touching a port**.
    """
    outcome, _agent, _router, _pitch, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {}, "no soy json en absoluto")),
            finishes(),
        ),
    )

    call = outcome.trace[0].tools[0]
    assert call.cause == TOOL_CAUSE_INVALID_ARGUMENT
    assert call.arguments is None
    assert registry.evidence.candidates == []


def test_the_evidence_ledger_is_inert_to_the_read_only_check_by_construction(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The ledger is captured by five of the six tools and must not weaken the invariant.

    It passes **structurally and not by exemption**: it declares no public method, so it is
    not a collaborator at all — it is not named in the exclusion list the way configuration
    and identity are, and it does not lean on the gap in the write vocabulary that C32a
    declared. A future ledger that grew a `save()` would become a collaborator and fail the
    check, which is the correct outcome for an object that persisted anything.
    """
    from jbg_ai.assist.tools import (
        EvidenceLedger,
        _is_collaborator,
        _method_names,
        captured_collaborators,
        write_methods_of,
    )

    from jbg_ai.assist.tools import ToolRegistryError

    ledger = EvidenceLedger()

    assert _method_names(ledger) == []
    assert _is_collaborator(ledger) is False
    assert write_methods_of(ledger) == []

    registry = registry_over(search, knowledge, principal)
    captured = {
        type(item).__name__
        for spec in registry.specs()
        for item in captured_collaborators(spec)
    }
    # The set C32a's own test fixes, unchanged: the ledger is nowhere in it.
    assert "EvidenceLedger" not in captured

    # **The positive direction, which is the one that makes the negative one mean anything.**
    # Asserted above alone, «not captured» would hold just as well for a ledger the walk never
    # reached — so a ledger that grew a write method is handed to the real construction seam
    # and must be refused. The refusal proves both halves at once: the walk reaches the ledger
    # through the tools' closures, and it classifies it by what it can do rather than by name.
    # Found missing by the independent verification of C32b, which measured it by hand.
    @dataclasses.dataclass
    class SavingLedger(EvidenceLedger):
        def save(self) -> None:  # pragma: no cover — never called, only inspected
            return None

    with pytest.raises(ToolRegistryError, match="SavingLedger.*save"):
        build_registry(
            principal=principal,
            settings=build_settings(),
            embed=FakeEmbeddingClient(),
            search=search,
            knowledge=knowledge,
            ledger=SavingLedger(),
        )

    # And the limit C32a declared, pinned rather than forgotten: a verb the write vocabulary
    # never held is not caught. The inertness above does not lean on this gap — the ledger has
    # no public method at all — and this line is here so that closing the gap is a deliberate
    # edit instead of a silent change in what the check means.
    @dataclasses.dataclass
    class RecordingLedger(EvidenceLedger):
        def record(self) -> None:  # pragma: no cover — never called, only inspected
            return None

    build_registry(
        principal=principal,
        settings=build_settings(),
        embed=FakeEmbeddingClient(),
        search=search,
        knowledge=knowledge,
        ledger=RecordingLedger(),
    )


# --- 5 · the loop and its stop conditions --------------------------------------------------


def test_the_loop_stops_when_the_model_asks_for_no_more_tools(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 1. It stops without exhausting anything, and it is not partial.

    And the argument is the generation layer's over the gathered evidence: the pitch that comes
    back is the one the scripted **pitch** provider wrote, never anything the loop produced.
    """
    outcome, agent, _router, pitch_provider, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            finishes(),
        ),
    )

    assert outcome.stop_reason == STOP_NO_MORE_TOOLS
    assert outcome.partial is False
    assert outcome.iterations == 2
    assert outcome.tool_calls_used == 1
    assert agent.call_count == 2
    assert pitch_provider.call_count == 1
    assert outcome.pitch == CLEAN_PITCH.pitch
    assert outcome.groups and outcome.groups[0].members[0].sku
    assert outcome.prompt_version == AGENT_PITCH_PROMPT_VERSION


def test_the_iteration_budget_stops_the_loop_and_the_response_declares_it(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 2. It cuts, it says so, and it still carries what it gathered."""
    outcome, agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
    )

    assert outcome.stop_reason == STOP_ITERATION_BUDGET
    assert outcome.partial is True
    assert outcome.iterations == MAX_AGENT_ITERATIONS
    assert agent.call_count == MAX_AGENT_ITERATIONS
    # The evidence survives the cut, and so does an argument written over it.
    assert outcome.groups
    assert outcome.pitch == CLEAN_PITCH.pitch
    # The trace declares what was spent, per iteration.
    assert len(outcome.trace) == MAX_AGENT_ITERATIONS
    assert outcome.tool_calls_used == MAX_AGENT_ITERATIONS


def test_tool_calls_beyond_the_budget_come_back_as_observations_and_touch_no_port(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 10. What fits runs **in the order the model emitted it**; the rest does not.

    The third call is `listar_familia`, and the proof that no port was touched for it is that
    the ledger holds no roster: the tool records what it read at the moment it reads it, so an
    empty list is a read that did not happen.
    """
    outcome, _agent, _router, _pitch, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(
                ("buscar_catalogo", {"consulta": "anillo"}),
                ("consultar_disponibilidad", {"sku": "JBG-0001"}),
                ("listar_familia", {"sku": "JBG-0001"}),
            ),
            finishes(),
        ),
        budgets=AgentBudgets(tool_calls=2),
    )

    executed = [call.tool for call in outcome.trace[0].tools if call.ok]
    refused = [call for call in outcome.trace[0].tools if not call.ok]

    assert executed == ["buscar_catalogo", "consultar_disponibilidad"]
    assert [call.tool for call in refused] == ["listar_familia"]
    assert refused[0].cause == TOOL_CAUSE_BUDGET_EXHAUSTED
    assert refused[0].content == {}
    assert registry.evidence.family_members == []
    assert outcome.stop_reason == STOP_TOOL_BUDGET
    assert outcome.partial is True
    assert outcome.iterations == 1


def test_the_token_budget_stops_the_loop_after_the_turn_that_exceeds_it(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """Post-hoc by design: enforcing it beforehand would need a tokeniser this service lacks.

    It can overshoot by **one** turn at most, and that turn is bounded by the other five.
    """
    outcome, agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
        budgets=AgentBudgets(prompt_tokens=100),
    )

    assert outcome.stop_reason == STOP_TOKEN_BUDGET
    assert outcome.partial is True
    assert agent.call_count == 1
    assert outcome.usage.prompt_tokens > 100


def test_the_context_budget_stops_the_loop_before_a_call_rather_than_after_one(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The deterministic half of the pair, and the budget that actually governs the cost.

    Every observation is re-sent on every later turn, so this is checked **in advance**: the
    second turn never happens, which is what a pre-flight budget means.
    """
    outcome, agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
        budgets=AgentBudgets(observation_chars=10),
    )

    assert outcome.stop_reason == STOP_CONTEXT_BUDGET
    assert outcome.partial is True
    assert agent.call_count == 1


def test_the_global_context_budget_binds_when_a_sweep_raises_the_section_budget(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """Q-4's «per section and also global», with the global branch actually executed.

    With the default values it cannot bind — observations stop at their own budget and the
    transcript at its cap, below the global — and until the independent verification of C32b
    no test reached it. It binds when a sweep raises the section budget, which is the one
    configuration where nothing else would bound the context: here the section budget is out
    of reach and the stop can only come from the sum of the two sections.
    """
    from jbg_ai.assist.transcript import transcript_chars

    outcome, agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
        budgets=AgentBudgets(observation_chars=10**6, context_chars=200),
    )

    transcript = transcript_chars(turns_from(TALK))
    observations = outcome.trace[0].context_chars

    assert outcome.stop_reason == STOP_CONTEXT_BUDGET
    assert agent.call_count == 1
    # The section alone was nowhere near its own budget; the sum is what crossed.
    assert observations < 10**6
    assert transcript <= 200 < observations + transcript


def test_the_wall_clock_budget_stops_the_loop(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The only budget a counter feels, and the reason it is a deadline for the whole request.

    The reserve for the argument is set to zero here so the budget is read alone: this is the
    check between turns. The next test is the one about the request as a whole.
    """
    outcome, agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
        budgets=AgentBudgets(deadline_seconds=0.05, pitch_reserve_seconds=0.0),
        agent_delay=0.06,
    )

    assert outcome.stop_reason == STOP_CLOCK_BUDGET
    assert outcome.partial is True
    assert agent.call_count == 1


def test_the_wall_clock_budget_bounds_the_whole_request_argument_included(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """**The deadline is the request's, not only the loop's.** Found by the independent
    verification of C32b: the clock was checked only before a turn, so a turn in flight ran its
    own timeout past the deadline and the argument ran after that — a request with a 0,2 s
    deadline took 0,479 s, and the declared 15 s was 31 s by construction.

    The loop now runs against the deadline minus the argument's reserve, and the turn in flight
    is cut when that runs out. With a 1 s deadline, 0,4 s of reserve and 0,35 s per turn, the
    second turn is cut at 0,6 s and the argument still fits: the old loop would have started a
    third turn at 0,71 s and served at ~1,36 s.
    """
    outcome, agent, _router, pitch_provider, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
        budgets=AgentBudgets(deadline_seconds=1.0, pitch_reserve_seconds=0.4),
        agent_delay=0.35,
        pitch_delay=0.3,
    )

    assert outcome.stop_reason == STOP_CLOCK_BUDGET
    assert outcome.partial is True
    assert agent.call_count == 2, "the second turn started and was cut; no third"
    # Cut by the clock, and said so — not blamed on a provider that may have been answering.
    assert outcome.trace[-1].cut_by_clock is True
    assert outcome.trace[-1].provider_error is None
    # The argument ran inside its reserve, and the whole request inside the deadline.
    assert pitch_provider.call_count == 1
    assert outcome.pitch == CLEAN_PITCH.pitch
    assert outcome.elapsed_ms < 1_000.0


def test_a_provider_fault_reports_its_own_stop_reason_and_marks_the_response_partial(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """**Found by a measurement, not by reading the code.**

    C32b's first provider pass hit a rate limit on request six, and every request after it
    came back reporting `sin_mas_herramientas` with `partial: false` — «the model finished
    asking for tools» about a request whose call never arrived. Those responses were
    indistinguishable from complete ones — how many is not known, because the run left no
    artefact — and the suite had never caught it because a scripted double does not fall over
    in the middle of a batch.

    A fault costs the turn and not the request, so whatever earlier turns gathered is still
    served; but the answer is not the one an unhurried request would have produced, which is
    what `partial` means.
    """
    from jbg_ai.assist.constants import STOP_PROVIDER_ERROR

    outcome, agent, _router, pitch_provider, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(RuntimeError("429 rate limit"),),
    )

    assert outcome.stop_reason == STOP_PROVIDER_ERROR
    assert outcome.stop_reason != STOP_NO_MORE_TOOLS
    assert outcome.partial is True
    assert outcome.iterations == 1
    assert outcome.tool_calls_used == 0
    assert agent.call_count == 1, "the fault costs the turn, and the loop does not retry"
    # Nothing was gathered, so nothing is written over it.
    assert pitch_provider.call_count == 0
    assert outcome.pitch == ""
    # And the cause survives where an operator can read it.
    assert outcome.trace[0].provider_error == "RuntimeError"


def test_a_fault_on_a_later_turn_still_serves_what_the_earlier_turns_gathered(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The other half of «a fault costs the turn and not the request»."""
    from jbg_ai.assist.constants import STOP_PROVIDER_ERROR

    outcome, _agent, _router, pitch_provider, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            RuntimeError("429 rate limit"),
        ),
    )

    assert outcome.stop_reason == STOP_PROVIDER_ERROR
    assert outcome.partial is True
    # The evidence of turn one survives and is written over.
    assert registry.evidence.candidates
    assert outcome.groups
    assert pitch_provider.call_count == 1
    assert outcome.pitch == CLEAN_PITCH.pitch


def test_a_stop_reason_is_always_present_and_always_from_the_closed_set(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """Whether partial or not, and never deduced by the consumer from the counters.

    Five iterations does not say whether the fifth was the last one needed or the one that ran
    out, and those are opposite statements about the answer being read.
    """
    scripts = {
        STOP_NO_MORE_TOOLS: ((finishes(),), AgentBudgets()),
        STOP_ITERATION_BUDGET: (
            (wants(("buscar_catalogo", {"consulta": "a"})),),
            AgentBudgets(),
        ),
        STOP_TOOL_BUDGET: (
            (
                wants(
                    ("buscar_catalogo", {"consulta": "a"}),
                    ("listar_familia", {"sku": "JBG-0001"}),
                ),
            ),
            AgentBudgets(tool_calls=1),
        ),
        STOP_TOKEN_BUDGET: (
            (wants(("buscar_catalogo", {"consulta": "a"})),),
            AgentBudgets(prompt_tokens=1),
        ),
    }
    for expected, (script, budgets) in scripts.items():
        outcome, *_ = drive(
            search=search,
            knowledge=knowledge,
            principal=principal,
            agent_script=script,
            budgets=budgets,
        )
        assert outcome.stop_reason == expected
        assert outcome.stop_reason in AGENT_STOP_REASONS
        assert outcome.partial is (expected in AGENT_BUDGET_STOP_REASONS)


def test_the_provider_call_ceiling_holds_for_a_request_that_loops_and_repairs(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 5. Classify, spend every turn, repair the argument: still under the ceiling.

    And the ceiling is **derived from the constants of its three stages** rather than written
    as a digit, so a change to any of them cannot leave a stale literal behind.
    """
    assert MAX_AGENT_PROVIDER_CALLS == (
        MAX_ROUTER_PROVIDER_CALLS + MAX_AGENT_ITERATIONS + MAX_PITCH_PROVIDER_CALLS
    )

    outcome, agent, router, pitch_provider, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(wants(("buscar_catalogo", {"consulta": "anillo"})),),
        # The first argument hangs a citation that resolves to nothing, which is a hard
        # violation and buys the single repair; the second is clean.
        pitch_script=(
            pitch("Una pieza sobria.", ("inventada#nada", "Una pieza sobria.")),
            CLEAN_PITCH,
        ),
    )

    assert router.call_count == MAX_ROUTER_PROVIDER_CALLS
    assert agent.call_count == MAX_AGENT_ITERATIONS
    assert pitch_provider.call_count == MAX_PITCH_PROVIDER_CALLS
    assert outcome.usage.calls == MAX_AGENT_PROVIDER_CALLS
    assert outcome.usage.calls <= MAX_AGENT_PROVIDER_CALLS
    # The embedding lookups are counted apart and are NOT part of that figure.
    assert registry.embedding_calls >= 1
    assert outcome.embedding_calls == registry.embedding_calls


def test_the_run_keeps_each_stages_usage_apart_so_each_is_priced_by_its_own_model(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """`usage` is a sum over up to three models and names only one of them.

    Found by the independent verification of C32b: the first cost figure of this change priced
    every token of a request at the loop's price, and its correction replaced the classifier's
    measured cost with a figure nobody had measured. Both errors start where a sum is priced by
    one name. The three stages are kept apart here — the three doubles report three different
    models — and they add up to the published sum, field by field.
    """
    outcome, _agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            finishes(),
        ),
    )

    stages = (outcome.router_usage, outcome.loop_usage, outcome.pitch_usage)

    assert [stage.calls for stage in stages] == [1, 2, 1]
    assert len({stage.model for stage in stages}) == 3, "three stages, three models"
    # The sum carries the last stage's name for tokens that are mostly not its own.
    assert outcome.usage.model == outcome.pitch_usage.model
    for name in ("prompt_tokens", "completion_tokens", "total_tokens", "calls"):
        assert getattr(outcome.usage, name) == sum(getattr(stage, name) for stage in stages)
    # And the loop's share is exactly what its turns report.
    assert outcome.loop_usage.prompt_tokens == sum(
        item.prompt_tokens for item in outcome.trace
    )


def test_no_fragment_of_the_loops_prose_reaches_the_response_or_the_wire_trace(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 3. Asserted over the whole serialised run, not field by field."""
    secret = "TEXTO DEL MODELO QUE NADIE DEBE LEER"
    outcome, _agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo"}), text=secret),
            finishes(text=secret),
        ),
    )

    everywhere = json.dumps(
        {
            "pitch": outcome.pitch,
            "clarification": outcome.clarification_question,
            "warnings": list(outcome.warnings),
            "wire": list(outcome.wire_trace()),
            "groups": [group.model_dump() for group in outcome.groups],
        },
        default=str,
        ensure_ascii=False,
    )

    assert secret not in everywhere
    # It is recorded as a length and a digest, which is what makes «the model wrote three
    # paragraphs nobody will read» a signal without the paragraphs.
    assert outcome.trace[0].discarded_chars == len(secret)
    assert outcome.trace[0].discarded_digest is not None


def test_a_transcript_over_its_caps_is_refused_before_any_provider_call(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 4, last clause. The cap is worth nothing enforced after the first call."""
    registry = registry_over(search, knowledge, principal)
    agent_client, agent_provider = refusing_agent()
    router_client, router_provider = refusing_router()

    with pytest.raises(TranscriptError):
        run(
            run_agent(
                [
                    __import__(
                        "jbg_ai.assist.transcript", fromlist=["Turn"]
                    ).Turn(role=TURN_ROLE_OPERATOR, text="a" * 5_000)
                ],
                principal,
                registry=registry,
                agent_client=agent_client,
                router_client=router_client,
            )
        )

    assert agent_provider.calls == 0
    assert router_provider.calls == 0


# --- 5.3 · concurrency, under a ceiling taken from the connection pool ---------------------


class _ConcurrencyProbe:
    """A stand-in registry that records how many invocations overlap.

    Duck-typed on purpose: `_execute` needs exactly one method of a registry, and driving the
    real one through a slow port would measure the port instead of the dispatcher.
    """

    def __init__(self) -> None:
        self.running = 0
        self.peak = 0
        self.order: list[str] = []

    async def invoke(self, name, arguments):  # noqa: ANN001 — a local double
        from jbg_ai.assist.tools import ToolObservation

        self.running += 1
        self.peak = max(self.peak, self.running)
        self.order.append(name)
        await asyncio.sleep(0.01)
        self.running -= 1
        return ToolObservation.success(name, {"visto": name})


def _calls(count: int) -> tuple[AgentToolCall, ...]:
    return tuple(
        AgentToolCall(call_id=f"c{index}", name=f"tool-{index}", arguments={})
        for index in range(count)
    )


def test_several_tool_calls_of_one_turn_run_concurrently_rather_than_in_sequence() -> None:
    """Assuming one call per turn is the defect that appears with the first complex
    conversation, and three searches in sequence spend latency for nothing."""
    probe = _ConcurrencyProbe()
    started = time.perf_counter()

    results = run(_execute(_calls(3), probe, limit=MAX_AGENT_CONCURRENT_TOOL_CALLS))

    assert probe.peak > 1
    assert (time.perf_counter() - started) < 0.03 * 3
    # Each observation is paired with the call that produced it.
    assert [item.call_id for item in results] == ["c0", "c1", "c2"]
    assert [item.tool for item in results] == ["tool-0", "tool-1", "tool-2"]


def test_concurrency_never_exceeds_the_ceiling_below_the_pools_capacity() -> None:
    """Six at once would queue against a pool of five with no overflow, and the last would wait
    out `pool_timeout` — which reads like an unavailable database rather than like contention
    this service inflicted on itself."""
    probe = _ConcurrencyProbe()

    run(_execute(_calls(6), probe, limit=MAX_AGENT_CONCURRENT_TOOL_CALLS))

    assert probe.peak <= MAX_AGENT_CONCURRENT_TOOL_CALLS
    assert len(probe.order) == 6


# --- 6 · the entry guardrail ----------------------------------------------------------------


def test_a_conversation_that_drifts_out_of_domain_is_refused_at_that_turn(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 6. One classification, zero tools, zero retrieval, and not an abstention."""
    registry = registry_over(search, knowledge, principal)
    agent_client, agent_provider = refusing_agent()
    router_client, router_provider = scripted_router(
        decision(served="out_of_domain", index=None)
    )

    outcome = run(
        run_agent(
            turns_from(
                (
                    (TURN_ROLE_OPERATOR, "busco un anillo de plata"),
                    (TURN_ROLE_ASSISTANT, "te enseño estos"),
                    (TURN_ROLE_OPERATOR, "¿me arreglas la moto?"),
                )
            ),
            principal,
            registry=registry,
            agent_client=agent_client,
            router_client=router_client,
            pitch_client=refusing_client()[0],
        )
    )

    assert router_provider.call_count == 1
    assert agent_provider.calls == 0
    assert outcome.stop_reason == STOP_REFUSED
    assert outcome.tool_calls_used == 0
    assert outcome.iterations == 0
    assert outcome.warnings == (WARNING_QUERY_OUT_OF_DOMAIN,)
    assert outcome.abstained is False
    assert outcome.partial is False
    assert registry.evidence.candidates == []


def test_exactly_one_classification_is_made_whatever_the_length_of_the_transcript(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 6. Classifying every turn is quadratic over a conversation and buys the
    same answer twice at temperature zero — which is what C31 refused when it refused to retry.
    """
    long_talk = tuple(
        (TURN_ROLE_OPERATOR if index % 2 == 0 else TURN_ROLE_ASSISTANT, f"turno {index}")
        for index in range(8)
    )

    _outcome, _agent, router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(finishes(),),
        turns=long_talk,
    )

    assert router.call_count == 1


def test_an_elliptical_follow_up_is_not_short_circuited_by_the_insufficiency_verdict(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 6 y 7. «¿y en dorado?» judged alone reports a missing axis the conversation
    already settled, so on this route that verdict is ignored and the loop decides."""
    outcome, agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        router_script=(decision(served="in_domain", index=None, missing_axis="material"),),
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo dorado"})),
            finishes(),
        ),
    )

    assert agent.call_count == 2
    assert outcome.stop_reason == STOP_NO_MORE_TOOLS
    # The classifier emitted no question: on this route it does not decide that.
    assert outcome.clarification_question is None


def test_the_index_verdict_of_the_classifier_does_not_choose_what_is_retrieved(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """Choosing where to look is the decision the loop exists to make. The classifier says
    `knowledge` and the loop searches the catalogue anyway, because it decided to."""
    outcome, _agent, _router, _pitch, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        router_script=(decision(served="in_domain", index="knowledge"),),
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            finishes(),
        ),
    )

    assert registry.evidence.candidates
    assert outcome.groups


# --- 7 · the evidence, the pivot and what never reaches the argument -----------------------


def test_the_clarification_tool_ends_the_loop_with_the_deterministic_question(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 7. Terminal, and the sentence is the closed catalogue's, not a model's."""
    outcome, agent, _router, pitch_provider, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("pedir_aclaracion", {"eje": "material"})),
            # The script would keep going; the loop must not.
            wants(("buscar_catalogo", {"consulta": "lo que sea"})),
        ),
    )

    assert outcome.stop_reason == STOP_CLARIFICATION
    assert outcome.iterations == 1
    assert agent.call_count == 1
    assert outcome.clarification_question == CLARIFICATION_TEMPLATES["material"]
    # Nothing to write about: the layer does not generate over a question.
    assert pitch_provider.call_count == 0
    assert outcome.pitch == ""
    assert outcome.partial is False


def test_clarification_is_terminal_at_the_granularity_of_a_turn(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """A decision the artefacts left open, pinned rather than left to a reader's guess.

    «Terminal» is enforced **between** turns and not within one: the calls of a turn are
    dispatched concurrently, so a model that asked for a search alongside the clarification has
    already spent that search by the time the clarification comes back. Cancelling it
    mid-flight would buy nothing — the port has been touched — and would make the tool counter
    depend on a race. What the rule guarantees is that **no further turn happens**.
    """
    outcome, agent, _router, _pitch, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(
                ("pedir_aclaracion", {"eje": "material"}),
                ("buscar_catalogo", {"consulta": "anillo"}),
            ),
            wants(("buscar_catalogo", {"consulta": "otra cosa"})),
        ),
    )

    assert outcome.stop_reason == STOP_CLARIFICATION
    assert agent.call_count == 1, "no further turn"
    assert outcome.iterations == 1
    # The search of that same turn did run, and the response says so honestly.
    assert outcome.tool_calls_used == 2
    assert len(registry.evidence.candidates) >= 1


def test_no_availability_label_reaches_the_generation_payload(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 9. Over a request that **did** observe availability, which is the case
    that matters: the label governs the loop's decision and never the prose."""
    outcome, _agent, _router, pitch_provider, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(
                ("buscar_catalogo", {"consulta": "anillo de plata"}),
                ("consultar_disponibilidad", {"sku": "JBG-0001"}),
            ),
            finishes(),
        ),
    )

    assert registry.evidence.availability, "the request must actually have read availability"
    handed = pitch_provider.user_of(0)
    payload = json.dumps(data_block(handed), ensure_ascii=False)

    for label in AVAILABILITY_LABELS:
        assert label not in payload, label
    assert "disponibilidad" not in payload
    assert "antiguedad_proyeccion_segundos" not in payload
    # **The payload half is what this layer guarantees, and it is what this test asserts.**
    # It used to assert as well that the argument carried no label — over a scripted argument
    # that could not carry one, and with nothing in the code to stop a real one: `verify()`
    # passes «disponible» and even «sin_existencias». The independent verification of C32b
    # moved that half to where it can be true: the pass counts availability terms in every
    # served argument (`availability_terms_in` in `evals/agent_sweep.py`) and publishes it.


def test_substitute_groups_reach_the_payload_marked_apart_from_catalogue_matches(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 8, mechanical half. A substitute and a match are different things to say.

    Whether the model **pivots when it should and not when it should not** is a property of the
    model and is measured in the calibration run, not here: this pins that a pivot the model
    did make arrives distinguished.
    """
    world = FakeProductSearch(
        [
            indexed_row(),
            indexed_row(
                product_id=__import__("uuid").UUID(
                    "aaaaaaaa-aaaa-4aaa-8aaa-000000000007"
                ),
                sku="JBG-0007",
                family_id=None,
                family_name=None,
            ),
        ]
    )

    outcome, _agent, _router, pitch_provider, registry = drive(
        search=world,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_sustitutos", {"sku": "JBG-0001"})),
            finishes(),
        ),
    )

    assert registry.evidence.substitutes, "the pivot must actually have happened"
    handed = data_block(pitch_provider.user_of(0))
    origins = {group.get("procedencia") for group in handed["candidatas"]}

    assert origins == {GROUP_ORIGIN_SUBSTITUTES}
    assert GROUP_ORIGIN_CATALOGUE not in origins


def test_a_catalogue_only_payload_is_marked_as_catalogue_and_not_as_substitutes(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The other side of the same closed vocabulary, so the marker cannot be write-only."""
    _outcome, _agent, _router, pitch_provider, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            finishes(),
        ),
    )

    handed = data_block(pitch_provider.user_of(0))

    assert {group["procedencia"] for group in handed["candidatas"]} == {
        GROUP_ORIGIN_CATALOGUE
    }


def test_the_deterministic_routes_payload_carries_no_origin_field_at_all(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 14, at the level of the object the two routes share.

    The agent marks its groups; the deterministic route builds the same class and must render
    **byte for byte** what it rendered before, because 120 measured generations were taken
    against that payload.
    """
    from jbg_ai.assist.prompt import FreeQueryCandidate, FreeQueryGroup, free_query_payload_from

    without = free_query_payload_from(
        groups=[FreeQueryGroup(members=(FreeQueryCandidate(sku="JBG-0001"),))]
    )
    with_origin = free_query_payload_from(
        groups=[
            FreeQueryGroup(
                members=(FreeQueryCandidate(sku="JBG-0001"),),
                origin=GROUP_ORIGIN_CATALOGUE,
            )
        ]
    )

    assert "procedencia" not in json.dumps(without.as_data(), ensure_ascii=False)
    assert "procedencia" in json.dumps(with_origin.as_data(), ensure_ascii=False)


def test_a_family_roster_reaches_the_payload_as_a_group_with_its_label_and_its_sizes(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The roster is evidence too, and it is the answer to «¿hay otra talla?».

    It is the one source that contributes a **size** to the payload, which widens the numeric
    whitelist on purpose: the size is the fact the question is about, and a fact the payload
    carries is a fact the argument may state. On the wire the members take the value and the
    meaning the deterministic route already gives a roster — enumerated, not ranked — and the
    group carries a real family identifier, without which two members would break the
    contract's *null family implies exactly one member* invariant.
    """
    outcome, _agent, _router, pitch_provider, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("listar_familia", {"sku": "JBG-0001"})),
            finishes(),
        ),
    )

    assert registry.evidence.family_members, "the roster must actually have been read"
    handed = data_block(pitch_provider.user_of(0))
    group = handed["candidatas"][0]

    assert group["procedencia"] == GROUP_ORIGIN_CATALOGUE
    assert group["familia"] == "Aro Menorca"
    assert [item["talla"] for item in group["piezas"]] == ["M", "M"]
    assert {item["sku"] for item in group["piezas"]} == {"JBG-0001", "JBG-0002"}

    # And on the wire: one group of two, with a real family and the roster's meaning.
    assert len(outcome.groups) == 1
    assert outcome.groups[0].family_id == str(FAMILY)
    assert len(outcome.groups[0].members) == 2
    assert all(member.score == 1.0 for member in outcome.groups[0].members)
    assert all(member.match_reasons == [] for member in outcome.groups[0].members)


def test_a_group_with_no_family_carries_exactly_one_member(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The contract's invariant, enforced structurally rather than asserted afterwards: a
    piece with no family gets a bucket nothing else can land in."""
    import uuid

    loners = FakeProductSearch(
        [
            indexed_row(
                product_id=uuid.UUID(f"aaaaaaaa-aaaa-4aaa-8aaa-0000000009{index:02d}"),
                sku=f"JBG-09{index:02d}",
                family_id=None,
                family_name=None,
            )
            for index in range(3)
        ]
    )

    outcome, *_ = drive(
        search=loners,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo"})),
            finishes(),
        ),
    )

    assert len(outcome.groups) == 3
    for group in outcome.groups:
        assert group.family_id is None
        assert len(group.members) == 1


def test_the_payload_caps_the_number_of_distinct_pieces_it_hands_over(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """C30b's rule applied: every field handed over widens the whitelist of admissible
    numerals, and the gate measured zero violations over a payload carrying one SKU."""
    import uuid

    many = FakeProductSearch(
        [
            indexed_row(
                product_id=uuid.UUID(f"aaaaaaaa-aaaa-4aaa-8aaa-0000000001{index:02d}"),
                sku=f"JBG-01{index:02d}",
                family_id=None,
                family_name=None,
            )
            for index in range(10)
        ]
    )

    _outcome, _agent, _router, pitch_provider, _registry = drive(
        search=many,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo", "top_k": 10})),
            finishes(),
        ),
        budgets=AgentBudgets(pieces=3),
    )

    handed = data_block(pitch_provider.user_of(0))
    pieces = [item for group in handed["candidatas"] for item in group["piezas"]]

    assert len(pieces) == 3


def _pivot_world() -> FakeProductSearch:
    """A search that finds the piece and four other matches, and a pivot with four answers.

    The piece `JBG-0300` is the closest match and a ring; the four other matches are necklaces,
    so they are never its substitutes; the four substitutes are rings too far away to be
    catalogue matches. The two sets are disjoint, which is what lets a test say which one a cut
    came out of.
    """
    import uuid

    def pid(index: int) -> uuid.UUID:
        return uuid.UUID(f"aaaaaaaa-aaaa-4aaa-8aaa-0000000003{index:02d}")

    alone = {"family_id": None, "family_name": None}
    rows = [
        indexed_row(
            product_id=pid(0), sku="JBG-0300", piece_type="anillo", distance=0.10, **alone
        )
    ]
    rows += [
        indexed_row(
            product_id=pid(index),
            sku=f"JBG-03{index:02d}",
            piece_type="collar",
            distance=0.10 + 0.01 * index,
            **alone,
        )
        for index in range(1, 5)
    ]
    rows += [
        indexed_row(
            product_id=pid(10 + index),
            sku=f"JBG-03{10 + index:02d}",
            piece_type="anillo",
            distance=0.95,
            **alone,
        )
        for index in range(1, 5)
    ]
    return FakeProductSearch(rows)


PIVOT_SCRIPT = (
    wants(("buscar_catalogo", {"consulta": "un regalo", "top_k": 5})),
    wants(("buscar_sustitutos", {"sku": "JBG-0300"})),
    finishes(),
)


def test_a_piece_the_loop_pivoted_away_from_does_not_reach_the_payload_as_a_match(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 8, the half the first review did not look at: **what the argument heads.**

    Found by the independent verification of C32b. In the pass, 7 of the 10 pivots of `gpt-4o`
    followed a catalogue search, so the piece that did not serve had arrived as a catalogue
    match — and `assist/v4` tells the argument to say first what matches. The pivot existed to
    keep that piece out of the headline and the payload put it there. The loop's decision is
    what excludes it; its availability label still never reaches the payload.
    """
    outcome, _agent, _router, pitch_provider, registry = drive(
        search=_pivot_world(),
        knowledge=knowledge,
        principal=principal,
        agent_script=PIVOT_SCRIPT,
    )

    assert "JBG-0300" in {item.sku for item in registry.evidence.candidates}, (
        "the piece must actually have come back from the search for this to mean anything"
    )
    handed = data_block(pitch_provider.user_of(0))
    offered = {
        piece["sku"]: group.get("procedencia")
        for group in handed["candidatas"]
        for piece in group["piezas"]
    }

    assert "JBG-0300" not in offered
    assert "JBG-0300" not in {
        member.sku for group in outcome.groups for member in group.members
    }
    # The other matches stay matches, and the substitutes stay distinguished.
    assert {sku for sku, origin in offered.items() if origin == GROUP_ORIGIN_CATALOGUE} == {
        "JBG-0301",
        "JBG-0302",
        "JBG-0303",
        "JBG-0304",
    }
    assert {sku for sku, origin in offered.items() if origin == GROUP_ORIGIN_SUBSTITUTES} == {
        "JBG-0311",
        "JBG-0312",
        "JBG-0313",
        "JBG-0314",
    }


def test_the_piece_cap_drops_further_matches_before_the_substitutes_of_a_pivot(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The cap decides **what** survives by priority, and never **where** it sits.

    Found by the independent verification of C32b: in 5 of the 7 pivots of `gpt-4o` that
    followed a search, the cap of eight was reached with the candidates, which were read first,
    and it cut the substitutes the pivot existed to find. With room for six, the four
    substitutes survive and two matches fill the rest — and the payload keeps the order the
    evidence arrived in, matches first, which is the order `assist/v4` reads.
    """
    _outcome, _agent, _router, pitch_provider, _registry = drive(
        search=_pivot_world(),
        knowledge=knowledge,
        principal=principal,
        agent_script=PIVOT_SCRIPT,
        budgets=AgentBudgets(pieces=6),
    )

    handed = data_block(pitch_provider.user_of(0))
    order = [
        (group.get("procedencia"), piece["sku"])
        for group in handed["candidatas"]
        for piece in group["piezas"]
    ]

    assert order == [
        (GROUP_ORIGIN_CATALOGUE, "JBG-0301"),
        (GROUP_ORIGIN_CATALOGUE, "JBG-0302"),
        (GROUP_ORIGIN_SUBSTITUTES, "JBG-0311"),
        (GROUP_ORIGIN_SUBSTITUTES, "JBG-0312"),
        (GROUP_ORIGIN_SUBSTITUTES, "JBG-0313"),
        (GROUP_ORIGIN_SUBSTITUTES, "JBG-0314"),
    ]


def test_the_loop_reports_an_abstention_when_the_catalogue_search_abstained(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """D-17, **the positive direction**, which is the one the field exists for.

    Driven for real rather than asserted over a default: a flat distance profile is the shape
    of a query the catalogue cannot answer, and C25's relative rule abstains on it. Testing
    only the negative direction would leave every assertion green over a field hardcoded to
    `False`, which is exactly the failure mode that let `low_confidence` survive its first
    review in C32a.
    """
    import uuid

    flat = FakeProductSearch(
        [
            indexed_row(
                product_id=uuid.UUID(int=index),
                sku=f"JBG-{index:04d}",
                distance=0.500 + 0.0005 * index,
            )
            for index in range(1, 21)
        ]
    )

    outcome, _agent, _router, pitch_provider, registry = drive(
        search=flat,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            finishes(),
        ),
    )

    assert registry.evidence.candidates == [], "an abstention empties the candidate list"
    assert outcome.abstained is True
    # And nothing is written over an empty candidate set, which is the failure the abstention
    # rule exists to prevent.
    assert pitch_provider.call_count == 0
    assert outcome.pitch == ""


def test_a_request_that_never_searched_the_catalogue_is_not_an_abstention(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """D-17, the other direction. Gathering nothing and abstaining are different sentences.

    Collapsing them would say the opposite of the truth about the catalogue on exactly the
    requests where a consumer would act on it — the refutation C32a measured for the
    consensus flag, one layer up.
    """
    empty = FakeProductSearch([])

    never_searched, *_ = drive(
        search=empty,
        knowledge=knowledge,
        principal=principal,
        agent_script=(finishes(),),
    )

    assert never_searched.abstained is False


def test_a_request_the_guardrail_refused_is_never_reported_as_an_abstention(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """One classifies before retrieving and the other reads the distance profile after."""
    outcome, *_ = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        router_script=(decision(served="not_in_catalogue", index=None),),
        agent_script=None,
    )

    assert outcome.abstained is False
    assert outcome.stop_reason == STOP_REFUSED


def test_without_an_agent_credential_the_route_degrades_instead_of_failing(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The fail-open, the ablation and the rollback in one: removing the credential is how a
    deployment returns to the behaviour that preceded this capability."""
    outcome, _agent, router, _pitch, registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=None,
    )

    assert outcome.stop_reason == STOP_NO_CLIENT
    assert outcome.iterations == 0
    assert outcome.tool_calls_used == 0
    assert registry.evidence.candidates == []
    assert router.call_count == 1
    assert outcome.pitch == ""


def test_the_published_citations_are_the_ones_the_argument_declared_and_that_verified(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 1, last clause. C30b's rule, reached through the loop's evidence."""
    question = "Cuidados y limpieza en casa de la plata"
    registry = registry_over(search, knowledge, principal, knowledge_threshold=1.5)
    seen = run(registry.invoke("consultar_conocimiento", {"pregunta": question}))
    offered = [item["citation_id"] for item in seen.content["fragmentos"]]
    assert offered, "the corpus must answer this question for the test to mean anything"

    outcome, _agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        knowledge_threshold=1.5,
        agent_script=(
            wants(("consultar_conocimiento", {"pregunta": question})),
            finishes(),
        ),
        pitch_script=(
            pitch(
                "La plata se limpia con un paño suave.",
                (offered[0], "La plata se limpia con un paño suave."),
            ),
        ),
    )

    assert [item.citation_id for item in outcome.citations] == [offered[0]]
    # And the citation carries the fields the observation never did, which is the whole reason
    # the ledger exists: a title and a type cannot be rebuilt from an identifier.
    assert outcome.citations[0].document_title
    assert outcome.citations[0].doc_type


# --- 8 · the two prompts --------------------------------------------------------------------


def test_every_declared_prompt_version_names_the_file_that_is_loaded() -> None:
    """Replicates `test_prompt_version_matches_the_loaded_prompt_file` for the two new ones.

    The path is derived from the constant in both cases, so half the pair cannot drift; this
    pins the other half, which is the failure `enrichment/` already paid for once.
    """
    for version in (AGENT_PROMPT_VERSION, AGENT_PITCH_PROMPT_VERSION):
        path = AI_SERVICE_ROOT / "prompts" / f"{version}.md"
        assert path.is_file(), version
        text = load_prompt_file(version)
        assert text == path.read_text(encoding="utf-8")
        assert text.splitlines()[0].strip() == f"# {version}"

    assert AGENT_PROMPT_VERSION == "agent/v1"
    # **v6 since C42, and the loop's own version did not move with it.** The two are apart for
    # the reason they were split: another call, another output, another model.
    assert AGENT_PITCH_PROMPT_VERSION == "assist/v6"
    # The deterministic route moved to v5 in C40 and stays there: the agent's pitch prompt did
    # not follow it then, and C42 moving the agent's does not drag the deterministic one along.
    assert PROMPT_VERSION == "assist/v5"
    assert AGENT_PITCH_PROMPT_VERSION != PROMPT_VERSION, (
        "the two constants are deliberately apart; merging them is the alternative D2 rejected"
    )


def test_the_argument_prompt_the_deterministic_route_runs_is_present_and_unedited() -> None:
    """HU escenario 14 and task 8.3: `assist/v3` is intact on disk.

    The 120 generations of C30b and the 89 of C31 are only interpretable while the text they
    were measured against is unchanged, and v4 exists precisely so that adding a section did
    not have to touch it. This replicates the guard that already protects v1 and v2.
    """
    v3 = load_prompt_file("assist/v3")
    v4 = load_prompt_file("assist/v4")
    sections_3 = prompt_sections(v3)
    sections_4 = prompt_sections(v4)

    assert v3.splitlines()[0].strip() == "# assist/v3"
    # The invariant rules are byte for byte the same, and so is every task v3 declared.
    assert sections_3["Sistema"] == sections_4["Sistema"]
    for name, body in sections_3.items():
        assert sections_4[name] == body, name
    # What v4 adds is exactly one section.
    assert set(sections_4) - set(sections_3) == {"Tarea · evidencia del agente"}


def test_the_loop_prompt_names_only_tools_that_exist_in_the_frozen_registry() -> None:
    """The prompt does not enumerate the tools — their descriptions travel in `tools` — but it
    does name the two the control rules are about, and a rename must break this rather than
    silently disable a rule."""
    text = load_prompt_file(AGENT_PROMPT_VERSION).casefold()
    named = [name for name in TOOL_NAMES if name in text]

    assert named, "the control rules name at least one tool"
    for name in named:
        assert name in TOOL_NAMES
    # And nothing that looks like a tool name but is not one.
    for withdrawn in ("perfil_punto_venta", "buscar_complementarios"):
        assert withdrawn not in text


def test_the_loop_prompt_states_that_its_prose_is_discarded() -> None:
    """The one instruction the type already enforces, said out loud so the model does not spend
    output tokens writing an answer that will be thrown away."""
    rules = agent_system_message().casefold()

    assert "se descarta" in rules
    assert "pedir_aclaracion" in rules or "aclaración" in rules


# --- 10 · the two traces ----------------------------------------------------------------------


def test_the_wire_trace_reports_what_was_done_and_never_what_was_asked(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 11. Tool names, success and cause, plus cost and latency — and no argument.

    A consumer logs the responses it receives, and the arguments a tool was called with are the
    operator's question as the model reformulated it.
    """
    query = "un anillo de plata para mi madre"
    outcome, _agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": query})),
            finishes(),
        ),
    )

    wire = outcome.wire_trace()
    serialised = json.dumps(wire, ensure_ascii=False)

    assert wire[0]["tools"] == [
        {"tool": "buscar_catalogo", "ok": True, "cause": None}
    ]
    assert wire[0]["prompt_tokens"] > 0 and wire[0]["elapsed_ms"] >= 0
    assert query not in serialised
    assert "consulta" not in serialised
    assert "candidatos" not in serialised
    # The rich trace, which only an in-process caller sees, does carry them.
    assert outcome.trace[0].tools[0].arguments == {"consulta": query}
    assert "candidatos" in (outcome.trace[0].tools[0].content or {})


def test_the_log_line_carries_the_counters_and_neither_the_transcript_nor_an_argument(
    search: FakeProductSearch,
    knowledge: InMemoryKnowledgeIndex,
    principal: ServicePrincipal,
    caplog,
) -> None:
    """HU escenario 11, third clause. A log line is durable storage outside the database.

    The tools are **named**, because a name is what the evaluation compares; what they were
    called with is the operator's question as the model reformulated it, and that is the one
    thing here a customer said out loud.
    """
    import logging

    query = "un anillo de plata para mi madre"
    with caplog.at_level(logging.INFO, logger="jbg_ai.assist.agent"):
        drive(
            search=search,
            knowledge=knowledge,
            principal=principal,
            agent_script=(
                wants(("buscar_catalogo", {"consulta": query})),
                finishes(),
            ),
        )

    lines = [item for item in caplog.messages if item.startswith("stage=agent ")]
    assert len(lines) == 1, "one line per request"
    line = lines[0]

    assert "stop=sin_mas_herramientas" in line
    assert "iterations=2" in line and "tool_calls=1" in line
    assert "tools=buscar_catalogo" in line
    assert "provider_calls=" in line and "elapsed_ms=" in line
    # And none of what a customer said, nor what the model asked the tool.
    assert query not in line
    for turn in TALK:
        assert turn[1] not in line
    assert "consulta" not in line


def test_the_rich_trace_is_available_in_process_and_pairs_every_observation(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """HU escenario 11, last clause: the harness reads it without going through HTTP."""
    outcome, _agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(
                ("buscar_catalogo", {"consulta": "anillo"}),
                ("consultar_disponibilidad", {"sku": "JBG-0001"}),
            ),
            finishes(),
        ),
    )

    calls = outcome.trace[0].tools

    assert len(calls) == 2
    assert all(isinstance(call, ToolCallTrace) for call in calls)
    assert {call.call_id for call in calls} == {"call-1", "call-2"}
    assert all(call.content is not None for call in calls)


# --- C42 · the provenance reaches the consumer, and only on this route --------------------------


def test_agent_group_declares_its_origin(
    knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The marker on the **response**, not only on the payload the model reads.

    Until C42 the distinction existed one layer in: the argument said «y como alternativa…»
    because the prompt told it to, while the screen had nothing to label the rows with — which
    is the exact failure the marker exists to prevent. The loop asked for substitutes 125 times
    in the measured pass, so this is routine and not an edge case.

    **Read from the same key the payload group is built from and not recomputed.** A second rule
    — «a group whose pieces appear in the substitutes ledger» — would be a second thing to keep
    in step, and the two would disagree the day the cap's priority changes.
    """
    world = FakeProductSearch(
        [
            indexed_row(),
            indexed_row(
                product_id=uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-000000000007"),
                sku="JBG-0007",
                family_id=None,
                family_name=None,
            ),
        ]
    )

    outcome, _agent, _router, pitch_provider, registry = drive(
        search=world,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            wants(("buscar_sustitutos", {"sku": "JBG-0001"})),
            finishes(),
        ),
    )

    assert registry.evidence.substitutes, "the pivot must actually have happened"
    assert outcome.groups, "and the response must carry the groups it produced"

    origins = {group.origin for group in outcome.groups}
    assert origins <= set(GROUP_ORIGINS)
    assert GROUP_ORIGIN_SUBSTITUTES in origins

    # The two layers agree, which is what «published, not recomputed» means here.
    handed = data_block(pitch_provider.user_of(0))
    assert [group["procedencia"] for group in handed["candidatas"]] == [
        group.origin for group in outcome.groups
    ]


def test_a_catalogue_only_run_declares_the_catalogue_origin_on_its_response(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """The other side of the closed vocabulary, so the field cannot be write-only on the wire."""
    outcome, _agent, _router, _pitch, _registry = drive(
        search=search,
        knowledge=knowledge,
        principal=principal,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            finishes(),
        ),
    )

    assert outcome.groups
    assert {group.origin for group in outcome.groups} == {GROUP_ORIGIN_CATALOGUE}


def test_the_shared_group_model_did_not_grow_the_field(
    search: FakeProductSearch, knowledge: InMemoryKnowledgeIndex, principal: ServicePrincipal
) -> None:
    """**The promise this change makes about the other route, field by field.** D3.

    `AssistGroup` is what `POST /v1/assist/sale` publishes, so widening it would move that
    route's schema — which is exactly what the subclass avoids, by the precedent `AgentUsage`
    set one class up. This fails the day somebody moves `origin` onto the shared model «because
    both routes have groups».
    """
    assert set(AssistGroup.model_fields) == {"family_id", "family_label", "members"}
    assert "origin" not in AssistGroup.model_fields
    assert set(AgentAssistGroup.model_fields) - set(AssistGroup.model_fields) == {"origin"}
    assert issubclass(AgentAssistGroup, AssistGroup), (
        "a subclass and not a parallel model: the comparison the evaluation runs has to be a "
        "difference of fields rather than a translation between two shapes"
    )


def test_with_no_scope_the_loop_reports_no_scope_rather_than_no_stock(
    knowledge: InMemoryKnowledgeIndex
) -> None:
    """The consequence of C42 admitting the omission on this route, at the level of the loop.

    With no point of sale the availability tool can only report that no scope applies, so the
    label can never say the shop is out of stock and **the pivot to substitutes cannot fire**.
    That is a property of the data and not a behaviour anybody simulates — which is why the
    frontend states it as a capability lost when the every-shop scope is selected, rather than
    as a display preference.
    """
    unscoped = ServicePrincipal(
        user_id="u-1", role="Operator", trace_id=TOKEN_TRACE_ID, pos_id=None
    )

    _outcome, _agent, _router, _pitch, registry = drive(
        search=FakeProductSearch([indexed_row()]),
        knowledge=knowledge,
        principal=unscoped,
        agent_script=(
            wants(("buscar_catalogo", {"consulta": "anillo de plata"})),
            wants(("consultar_disponibilidad", {"sku": "JBG-0001"})),
            finishes(),
        ),
    )

    labels = [label for _sku, label in registry.evidence.availability]
    assert labels == [AVAILABILITY_NO_SCOPE]
    assert AVAILABILITY_OUT_OF_STOCK not in labels
