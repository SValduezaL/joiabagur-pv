"""The agent loop: one guardrail, five turns, six budgets and an argument. C32b.

    clasificar el turno que se contesta            1 llamada, y sólo una
        └─ rechazo → cortocircuito, 0 tools, códigos de C31
    ┌── por vuelta, hasta cinco ──────────────────────────────────┐
    │   decide(messages, registry.schemas())                      │
    │       sin tool_calls            → parar (el modelo terminó) │
    │       pedir_aclaracion          → parar (TERMINAL)          │
    │   ejecutar en paralelo, tope de cuatro                      │
    │   las que no caben → observación con presupuesto_agotado    │
    │   acumular en el contexto y en la evidencia                 │
    └─────────────────────────────────────────────────────────────┘
    generate_pitch(evidencia, tarea de assist/v4)          ≤ dos llamadas

**The loop gathers evidence and writes nothing.** If its last turn wrote the prose it would
step around, in one move, the numeric gate that refuses a figure absent from the context, the
referential integrity of citations and the single repair — the three properties the generation
layer exists to hold. It also keeps «nothing is persisted» for free, because the intermediate
reasoning never leaves the process: the port it is handed has nowhere to put any.

**The classifier is a guardrail here and not a router.** One classification per request, over
the turn being answered. A refusal short-circuits on any turn; the insufficiency verdict is
**ignored**, because a follow-up turn is elliptical and «¿y en dorado?» judged alone reports
missing information the conversation already supplied; and the index verdict is **discarded**,
because choosing where to look is the decision this loop exists to make.

**Six budgets, and the two that matter most are not step counts.** What dominates the cost of
a loop is the accumulated context, because every observation is re-sent on every later turn —
so characters are checked before a call and tokens after one, and the wall clock is checked
against a deadline for the whole request because it is the only budget a counter feels.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from jbg_ai.api.schemas.assist import (
    AgentAssistGroup,
    AgentAssistResponse,
    AgentTraceIteration,
    AgentTraceTool,
    AgentUsage,
    AssistGroupMember,
)
from jbg_ai.api.auth import ServicePrincipal
from jbg_ai.assist.agent_llm import AgentLlm, AgentStep, AgentToolCall
from jbg_ai.assist.constants import (
    AGENT_CONTEXT_BUDGET_CHARS,
    AGENT_DEADLINE_SECONDS,
    AGENT_OBSERVATION_BUDGET_CHARS,
    AGENT_PITCH_PROMPT_VERSION,
    AGENT_PITCH_RESERVE_SECONDS,
    AGENT_PROMPT_VERSION,
    AGENT_TOKEN_BUDGET,
    GROUP_ORIGIN_CATALOGUE,
    GROUP_ORIGIN_SUBSTITUTES,
    MAX_AGENT_CONCURRENT_TOOL_CALLS,
    MAX_AGENT_ITERATIONS,
    MAX_AGENT_PIECES,
    MAX_AGENT_PROVIDER_CALLS,
    MAX_AGENT_TOOL_CALLS,
    STOP_CLARIFICATION,
    STOP_CLOCK_BUDGET,
    STOP_CONTEXT_BUDGET,
    STOP_ITERATION_BUDGET,
    STOP_NO_CLIENT,
    STOP_NO_MORE_TOOLS,
    STOP_PROVIDER_ERROR,
    STOP_REFUSED,
    STOP_TOKEN_BUDGET,
    STOP_TOOL_BUDGET,
    TOOL_CAUSE_BUDGET_EXHAUSTED,
    TOOL_CAUSE_INVALID_ARGUMENT,
)
from jbg_ai.assist.errors import AgentProviderError
from jbg_ai.assist.llm import AssistLlm, TokenUsage
from jbg_ai.assist.pitch import EMPTY_PITCH, PitchOutcome, generate_pitch
from jbg_ai.assist.prompt import (
    AgentPitchTask,
    FreeQueryCandidate,
    FreeQueryGroup,
    PitchCitation,
    free_query_payload_from,
    load_prompt_file,
    prompt_sections,
)
from jbg_ai.assist.router_llm import RouterLlm
from jbg_ai.assist.routing import RoutingOutcome, classify_query
from jbg_ai.assist.tools import ToolObservation, ToolRegistry
from jbg_ai.assist.transcript import (
    Turn,
    answered_turn,
    transcript_block,
    transcript_chars,
    transcript_plain,
    validate_transcript,
)
# Reused rather than duplicated: the projection of a corpus fragment onto the contract is the
# same on both routes, and a second copy is how two routes start reporting a citation
# differently. Made public in C32b for this import; it was module-private with one caller.
from jbg_ai.assist.orchestrator import to_citation
from jbg_ai.knowledge.search import KnowledgeCitation
from jbg_ai.retrieval.ports import FamilyMember

logger = logging.getLogger(__name__)

STAGE = "agent"

#: The heading of the loop prompt whose body is its system message. Same shape as the
#: argument's and the classifier's, deliberately: one parser, one rule about where rules live.
SYSTEM_SECTION = "Sistema"

#: The tool whose invocation ends the loop. Named from the frozen set rather than restated, so
#: a rename of the tool breaks an import instead of silently disabling the terminal rule.
CLARIFICATION_TOOL = "pedir_aclaracion"
CATALOGUE_TOOL = "buscar_catalogo"


def load_agent_prompt() -> str:
    """The loop's prompt file, by the same search order every other prompt uses."""
    return load_prompt_file(AGENT_PROMPT_VERSION)


def agent_system_message(text: str | None = None) -> str:
    """The invariant rules of the loop. Identical for **every** conversation, which is the point.

    No turn of the transcript reaches this string. That is the structural mitigation C30b
    delivered for the argument and C31 reused for the classifier, applied to the call this
    change adds — and applied to **every** turn rather than to the last one, because an
    injection hides in turn three as comfortably as in turn five.
    """
    return prompt_sections(text if text is not None else load_agent_prompt())[
        SYSTEM_SECTION
    ]


@dataclass(frozen=True)
class AgentBudgets:
    """The six, by parameter so an evaluation can sweep them **inside one process**.

    The pattern C20, C23, C25 and C30b established, and here it is not a convenience: three of
    these six are values the provider pass exists to set, so the harness has to be able to move
    them without restarting anything.
    """

    iterations: int = MAX_AGENT_ITERATIONS
    tool_calls: int = MAX_AGENT_TOOL_CALLS
    concurrency: int = MAX_AGENT_CONCURRENT_TOOL_CALLS
    prompt_tokens: int = AGENT_TOKEN_BUDGET
    observation_chars: int = AGENT_OBSERVATION_BUDGET_CHARS
    context_chars: int = AGENT_CONTEXT_BUDGET_CHARS
    deadline_seconds: float = AGENT_DEADLINE_SECONDS
    pieces: int = MAX_AGENT_PIECES
    #: Of `deadline_seconds`, what the argument may still take once the loop stops. The loop
    #: runs against the deadline minus this, so the request as a whole keeps the deadline.
    #: Ignored when no generation client is handed in: there is no argument to reserve for.
    pitch_reserve_seconds: float = AGENT_PITCH_RESERVE_SECONDS


@dataclass(frozen=True)
class ToolCallTrace:
    """One tool call, as the **in-process** trace records it.

    `arguments` and `content` are here and are **removed** by `wire_trace()`. A consumer logs
    the responses it receives, and the arguments a tool was called with are the operator's
    question as the model reformulated it — which the rule this project already holds keeps out
    of durable storage. The evaluation harness reads this object directly, without HTTP, which
    is how it consumes every other part of this service.
    """

    call_id: str
    tool: str
    ok: bool
    cause: str | None
    elapsed_ms: float
    arguments: Mapping[str, object] | None = None
    content: Mapping[str, object] | None = None


@dataclass(frozen=True)
class IterationTrace:
    """One turn of the loop: what it asked for, what it cost and how long it took."""

    iteration: int
    tools: tuple[ToolCallTrace, ...]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    elapsed_ms: float
    #: Accumulated observation characters **after this turn's observations were appended** —
    #: that is, what the next turn would send, and the number the next pre-flight check reads.
    #: It is the deterministic half of the context pair. The other half is `prompt_tokens`,
    #: which *is* the context this turn sent, measured by the provider rather than estimated:
    #: the two are one turn apart by construction, so a curve read off the characters is the
    #: token curve shifted by one turn.
    context_chars: int = 0
    #: Length and digest of the prose this turn produced and the port threw away. Never the
    #: text: it makes two turns comparable and one re-derivable by nobody.
    discarded_chars: int = 0
    discarded_digest: str | None = None
    #: The cause of a provider fault on this turn, when there was one.
    provider_error: str | None = None
    #: The turn was in flight when the loop's share of the deadline ran out, and was cut. Not a
    #: provider fault: the provider may have been about to answer.
    cut_by_clock: bool = False


@dataclass(frozen=True)
class AgentRun:
    """Everything one agent request produced. **A library object, not a contract model.**

    The route projects it; the harness reads it whole. Keeping the two apart is what let the
    loop, the transcript and the port be delivered and tested before the contract moved, which
    is the order the migration plan asks for.
    """

    intent: str
    stop_reason: str
    partial: bool
    iterations: int
    tool_calls_used: int
    usage: TokenUsage
    groups: tuple[AgentAssistGroup, ...] = ()
    citations: tuple[KnowledgeCitation, ...] = ()
    warnings: tuple[str, ...] = ()
    clarification_question: str | None = None
    abstained: bool = False
    pitch: str = EMPTY_PITCH
    pitch_outcome: PitchOutcome | None = None
    trace: tuple[IterationTrace, ...] = ()
    embedding_calls: int = 0
    elapsed_ms: float = 0.0
    agent_prompt_version: str = AGENT_PROMPT_VERSION
    #: `None` when the generation layer did not run, exactly as the deterministic route's
    #: field means today: «the layer ran» and no longer «there is a pitch».
    prompt_version: str | None = None
    #: **The three stages, kept apart.** `usage` is their sum and it carries one model name —
    #: the last stage's — for tokens billed at up to three different prices: the classifier,
    #: the loop (the arm under measurement) and the argument. Pricing that sum by that name is
    #: the error the first cost figure of this change made, so whoever needs a cost prices
    #: these three, each by its own `model`. Their sum is `usage`, field by field.
    router_usage: TokenUsage = field(default_factory=TokenUsage)
    loop_usage: TokenUsage = field(default_factory=TokenUsage)
    pitch_usage: TokenUsage = field(default_factory=TokenUsage)

    def wire_trace(self) -> tuple[dict[str, object], ...]:
        """The trace as it travels on the response: **what was done, never what was asked.**

        Tool names are sufficient for the measurement the evaluation needs — tools invoked
        against tools expected — and the arguments and the observation contents are exactly
        what must not enter a consumer's log.
        """
        return tuple(
            {
                "iteration": item.iteration,
                "tools": [
                    {"tool": call.tool, "ok": call.ok, "cause": call.cause}
                    for call in item.tools
                ],
                "prompt_tokens": item.prompt_tokens,
                "completion_tokens": item.completion_tokens,
                "total_tokens": item.total_tokens,
                "elapsed_ms": round(item.elapsed_ms, 1),
            }
            for item in self.trace
        )


def agent_response(run: AgentRun, principal: ServicePrincipal) -> AgentAssistResponse:
    """Project the library result onto the contract model. **The only place the two meet.**

    Kept apart from `run_agent` so the loop, the port and the transcript could be delivered
    and tested before the contract moved — the order the migration plan asks for — and so the
    evaluation harness can read the whole run without a response model in the way.

    The trace that travels is the **wire** one: names, success and cause, plus cost and
    latency. The arguments and the observation contents stay in process.
    """
    return AgentAssistResponse(
        intent=run.intent,
        groups=list(run.groups),
        pitch=run.pitch,
        citations=[
            to_citation(item, product_id=None) for item in run.citations
        ],
        warnings=list(run.warnings),
        clarification_question=run.clarification_question,
        usage=AgentUsage(
            prompt_tokens=run.usage.prompt_tokens,
            completion_tokens=run.usage.completion_tokens,
            total_tokens=run.usage.total_tokens,
            model=run.usage.model if run.usage.calls else None,
            # The figure the deterministic route's usage object does not publish, and the
            # reason this model exists: without it the ceiling would not be observable from
            # the same object a consumer reads.
            calls=run.usage.calls,
        ),
        abstained=run.abstained,
        prompt_version=run.prompt_version,
        partial=run.partial,
        stop_reason=run.stop_reason,
        iterations=run.iterations,
        tool_calls_used=run.tool_calls_used,
        trace=[
            AgentTraceIteration(
                iteration=int(item["iteration"]),
                tools=[
                    AgentTraceTool(**call) for call in item["tools"]  # type: ignore[arg-type]
                ],
                prompt_tokens=int(item["prompt_tokens"]),
                completion_tokens=int(item["completion_tokens"]),
                total_tokens=int(item["total_tokens"]),
                elapsed_ms=float(item["elapsed_ms"]),
            )
            for item in run.wire_trace()
        ],
        # Null when no loop ran, exactly as `prompt_version` is null when the argument did
        # not: «the stage ran» and not «there is a value».
        agent_prompt_version=run.agent_prompt_version if run.iterations else None,
        trace_id=principal.trace_id,
        effective_pos_id=principal.pos_id or "",
    )


@dataclass
class _Evidence:
    """The accumulator, filled from the registry's ledger once the loop has finished.

    Read **after** the loop rather than during it, because what the payload may carry is a
    property of the whole request — the cap on distinct pieces is a cap per request — and
    deciding it turn by turn would let the first search spend the whole allowance.
    """

    catalogue_searches: list[bool] = field(default_factory=list)
    clarification: str | None = None


async def run_agent(
    turns: Sequence[Turn],
    principal: ServicePrincipal,
    *,
    registry: ToolRegistry,
    agent_client: AgentLlm | None,
    router_client: RouterLlm | None = None,
    pitch_client: AssistLlm | None = None,
    budgets: AgentBudgets = AgentBudgets(),
) -> AgentRun:
    """Serve one agent request. **Every port and every client is handed in, never built here.**

    That is the pattern the assistance layer has followed since C30a and it is what lets the
    evaluation harness and the whole suite mount this loop against doubles without opening a
    socket. Constructing a client here would put a credential in the middle of a library.

    Never raises for a provider fault, at any of the three stages: a classifier fault is a
    fail-open, a loop fault costs the turn and leaves the evidence already gathered, and a
    generation fault serves the evidence without prose. It **does** raise `TranscriptError`,
    because a transcript over its caps is a bad request and not a degradation.

    **The prompts are the versioned files, and there is no parameter to inject another text.**
    A text handed in beside a version that stays the default is how a response gets stamped
    with a prompt that never reached the model — the failure `enrichment/` already paid for.
    The two parameters that allowed it were removed by the independent verification of C32b;
    they had no caller. A sweep that needs another text needs a new version, or a parameter
    that carries the text and its version together.
    """
    validate_transcript(turns)
    started = time.perf_counter()
    # **The loop runs against the deadline minus the argument's reserve**, so the request as a
    # whole keeps the deadline: checking the clock only before a turn let the turn in flight run
    # its own timeout past it and the argument run after that, and a request with a 0,2 s
    # deadline took 0,479 s. With no generation client there is no argument to reserve for.
    reserve = budgets.pitch_reserve_seconds if pitch_client is not None else 0.0
    loop_deadline = started + budgets.deadline_seconds - reserve

    def elapsed_ms() -> float:
        return (time.perf_counter() - started) * 1000.0

    def out_of_time() -> bool:
        return time.perf_counter() >= loop_deadline

    answered = answered_turn(turns)

    # --- the entry guardrail ---------------------------------------------------------------
    #
    # **Exactly one classification, over the turn being answered.** Classifying every turn
    # would cost one call per turn per request, which grows quadratically over a conversation
    # and breaks the declared ceiling once it is long enough — and at temperature zero the
    # repeated classifications buy the same answer twice, which is what C31 refused when it
    # refused to retry. Classifying only the opening turn would leave a conversation that
    # drifts out of domain at its fifth turn unguarded, which is the category this route has
    # to survive.
    routing: RoutingOutcome = await classify_query(
        answered, client=router_client, trace_id=principal.trace_id
    )

    if routing.refused:
        # Short-circuit on **any** turn: no tool runs, no retrieval runs, and the response
        # carries the refusal code of the two C31 distinguishes. Deliberately **not** an
        # abstention: one classifies before retrieving and the other reads the shape of the
        # distance profile after, and collapsing them would make the two rates this project
        # publishes separately indistinguishable.
        return _refused(routing, principal, elapsed_ms())

    # **The insufficiency verdict is not acted on and the index verdict is not read.** Neither
    # is an oversight, and both are written here so a later reader does not restore them: a
    # follow-up turn is elliptical, so a standalone judgement of it asks the operator about an
    # axis the conversation already settled — clarification belongs to the loop, which sees the
    # whole transcript; and choosing which index to consult is the decision the loop exists to
    # make, so taking it beforehand would be an agent told in advance where to look.
    _ = routing.route

    if agent_client is None:
        # A deployment that configures no credential is a declared state, and it is the
        # rollback and the ablation at once. Nothing is retrieved because retrieval on this
        # route is a tool the loop calls, so what is served is the shape and no evidence.
        return _no_client(routing, principal, elapsed_ms())

    usage = routing.usage
    loop_usage = TokenUsage()
    evidence = _Evidence()
    traces: list[IterationTrace] = []
    messages: list[dict[str, object]] = [
        {"role": "system", "content": agent_system_message()},
        {"role": "user", "content": transcript_block(turns)},
    ]
    schemas = registry.schemas()
    observation_chars = 0
    transcript_section = transcript_chars(turns)
    tool_calls_used = 0
    iterations = 0
    stop_reason: str | None = None

    for iteration in range(1, budgets.iterations + 1):
        # **Pre-flight and deterministic**, evaluated before the call rather than after it.
        # This is the half of the token pair that can be checked in advance without a
        # tokeniser, and it is the budget that actually governs the cost of a loop.
        if observation_chars > budgets.observation_chars or (
            observation_chars + transcript_section > budgets.context_chars
        ):
            stop_reason = STOP_CONTEXT_BUDGET
            break
        if out_of_time():
            stop_reason = STOP_CLOCK_BUDGET
            break

        iterations = iteration
        turn_started = time.perf_counter()
        try:
            # Bounded by what is left of the loop's share of the deadline, and not only by the
            # client's own per-call timeout: otherwise a turn started just before the deadline
            # spends its whole timeout after it.
            step: AgentStep = await asyncio.wait_for(
                agent_client.decide(messages, schemas),
                timeout=max(loop_deadline - time.perf_counter(), 0.0),
            )
        except TimeoutError:
            # **The clock, not the provider.** The adapter turns its own timeout into an
            # `AgentProviderError`, so a bare timeout reaching here is the deadline's: the turn
            # is lost, the evidence of the earlier ones is served, and the reason says which
            # budget ran out rather than blaming a provider that may have been about to answer.
            traces.append(
                IterationTrace(
                    iteration=iteration,
                    tools=(),
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    elapsed_ms=(time.perf_counter() - turn_started) * 1000.0,
                    context_chars=observation_chars,
                    cut_by_clock=True,
                )
            )
            stop_reason = STOP_CLOCK_BUDGET
            break
        except AgentProviderError as exc:
            # The turn is lost and the request is not: the evidence the earlier turns gathered
            # is already in the ledger and is served. A fault on the first turn therefore
            # yields a partial response with no evidence rather than a five hundred.
            traces.append(
                IterationTrace(
                    iteration=iteration,
                    tools=(),
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    elapsed_ms=(time.perf_counter() - turn_started) * 1000.0,
                    provider_error=exc.cause,
                )
            )
            # **Its own reason, and partial.** Reporting `sin_mas_herramientas` here
            # would say the model finished asking for tools about a request whose call
            # never arrived, and a consumer could not tell the two apart — which is
            # exactly what the responses of the first provider pass did after its rate
            # limit (how many is not known: that run left no artefact).
            stop_reason = STOP_PROVIDER_ERROR
            break

        usage = usage + step.usage
        loop_usage = loop_usage + step.usage

        if not step.wants_tools:
            # The model finished. The one stop reason that is not a budget and not a refusal,
            # and the only one that leaves the response whole.
            traces.append(
                _trace_of(iteration, step, (), turn_started, observation_chars)
            )
            stop_reason = STOP_NO_MORE_TOOLS
            break

        # --- D-9 · what fits runs, in the order the model emitted it ------------------------
        room = max(budgets.tool_calls - tool_calls_used, 0)
        executed = tuple(step.tool_calls[:room])
        refused = tuple(step.tool_calls[room:])

        results = await _execute(executed, registry, limit=budgets.concurrency)
        tool_calls_used += len(executed)

        calls: list[ToolCallTrace] = list(results)
        for call in refused:
            # **No port is touched for these, and the model is told why.** Dropping them
            # silently would return a turn with fewer observations than calls requested, which
            # the model cannot tell from a tool that broke.
            calls.append(
                ToolCallTrace(
                    call_id=call.call_id,
                    tool=call.name,
                    ok=False,
                    cause=TOOL_CAUSE_BUDGET_EXHAUSTED,
                    elapsed_ms=0.0,
                    arguments=call.arguments,
                    content={},
                )
            )

        observation_chars += _append_turn(messages, step.tool_calls, calls)
        traces.append(
            _trace_of(iteration, step, tuple(calls), turn_started, observation_chars)
        )

        for call in calls:
            if call.tool == CATALOGUE_TOOL and call.ok and call.content is not None:
                evidence.catalogue_searches.append(bool(call.content.get("abstenido")))
            if call.tool == CLARIFICATION_TOOL and call.ok and call.content is not None:
                evidence.clarification = str(call.content.get("pregunta") or "") or None

        if evidence.clarification is not None:
            # **Terminal.** Asking for clarification while continuing to search contradicts
            # itself: the call states there is not enough information to search with.
            stop_reason = STOP_CLARIFICATION
            break
        if refused:
            stop_reason = STOP_TOOL_BUDGET
            break
        if usage.prompt_tokens > budgets.prompt_tokens:
            # **Post-hoc**, and it can overshoot by at most this one turn — which is itself
            # bounded by the other five budgets. Enforcing it beforehand needs a tokeniser
            # this service does not depend on.
            stop_reason = STOP_TOKEN_BUDGET
            break
    else:
        # The explicit exhaustion branch the design asks for, rather than a loop that ends by
        # running out of range: «the fifth turn was the last one needed» and «the fifth turn
        # was the one that ran out» are opposite statements about the answer being read.
        stop_reason = STOP_ITERATION_BUDGET

    if stop_reason is None:  # pragma: no cover — the branches above are exhaustive
        stop_reason = STOP_ITERATION_BUDGET

    return await _compose(
        turns=turns,
        answered=answered,
        principal=principal,
        registry=registry,
        routing=routing,
        pitch_client=pitch_client,
        budgets=budgets,
        evidence=evidence,
        usage=usage,
        loop_usage=loop_usage,
        traces=tuple(traces),
        iterations=iterations,
        tool_calls_used=tool_calls_used,
        stop_reason=stop_reason,
        started=started,
    )


# --- the turn -----------------------------------------------------------------------------


async def _execute(
    calls: Sequence[AgentToolCall], registry: ToolRegistry, *, limit: int
) -> tuple[ToolCallTrace, ...]:
    """Run a turn's calls **concurrently, under a ceiling**, pairing each result with its call.

    Assuming one call per turn is the defect that appears with the first complex conversation,
    and running four searches in sequence spends latency for nothing. The ceiling is below the
    connection pool's capacity because each search opens its own session: more at once than the
    pool can serve makes the last wait out `pool_timeout`, which reads like an unavailable
    database rather than like contention this service inflicted on itself.
    """
    gate = asyncio.Semaphore(limit)

    async def one(call: AgentToolCall) -> ToolCallTrace:
        call_started = time.perf_counter()
        if call.arguments is None:
            # The provider's argument blob did not parse as an object. **No port is touched**:
            # it is an invalid argument, which is what the model is told, and validating it
            # against the tool's schema would be validating something that is not there.
            return ToolCallTrace(
                call_id=call.call_id,
                tool=call.name,
                ok=False,
                cause=TOOL_CAUSE_INVALID_ARGUMENT,
                elapsed_ms=0.0,
                arguments=None,
                content={},
            )
        async with gate:
            observation: ToolObservation = await registry.invoke(
                call.name, call.arguments
            )
        return ToolCallTrace(
            call_id=call.call_id,
            tool=call.name,
            ok=observation.ok,
            cause=observation.cause,
            elapsed_ms=(time.perf_counter() - call_started) * 1000.0,
            arguments=call.arguments,
            content=observation.content,
        )

    if not calls:
        return ()
    return tuple(await asyncio.gather(*(one(call) for call in calls)))


def _trace_of(
    iteration: int,
    step: AgentStep,
    calls: tuple[ToolCallTrace, ...],
    turn_started: float,
    context_chars: int = 0,
) -> IterationTrace:
    return IterationTrace(
        iteration=iteration,
        tools=calls,
        prompt_tokens=step.usage.prompt_tokens,
        completion_tokens=step.usage.completion_tokens,
        total_tokens=step.usage.total_tokens,
        elapsed_ms=(time.perf_counter() - turn_started) * 1000.0,
        context_chars=context_chars,
        discarded_chars=step.discarded_chars,
        discarded_digest=step.discarded_digest,
    )


def _append_turn(
    messages: list[dict[str, object]],
    requested: Sequence[AgentToolCall],
    calls: Sequence[ToolCallTrace],
) -> int:
    """Append the turn and its observations, and report how many characters that cost.

    The assistant turn is rebuilt from the tool calls alone and carries **no content**, which
    is not a simplification: the port returned none, because the type it returns has no field
    for any. What the model sees of its own previous turn is exactly what it decided, which is
    also what makes a replay of a transcript reproducible.
    """
    by_id = {call.call_id: call for call in calls}
    messages.append(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call.call_id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(
                            call.arguments or {}, ensure_ascii=False
                        ),
                    },
                }
                for call in requested
            ],
        }
    )
    added = 0
    for call in requested:
        result = by_id.get(call.call_id)
        body = json.dumps(
            {
                "ok": bool(result and result.ok),
                "causa": result.cause if result else None,
                **(dict(result.content) if result and result.content else {}),
            },
            ensure_ascii=False,
        )
        added += len(body)
        messages.append(
            {"role": "tool", "tool_call_id": call.call_id, "content": body}
        )
    return added


# --- the evidence and the argument ------------------------------------------------------------


def _pieces(
    registry: ToolRegistry, cap: int
) -> tuple[list[FreeQueryGroup], list[AgentAssistGroup]]:
    """Project the ledger onto the payload's groups and the response's groups.

    Two shapes from one source, and neither is derived from the other: the payload carries what
    the model may write about — no identifier and no score, because every numeral handed over
    widens the whitelist — and the response carries what a consumer needs to show a piece.

    **The cap is on distinct pieces per request.** A loop that searched five times would
    otherwise hand over fifty, and the numeric gate measured zero violations over a payload
    carrying one SKU.

    **A piece the loop pivoted away from is not handed over as a catalogue match**, and the
    substitutes the pivot produced are the last to be dropped by the cap. Both were found by the
    independent verification of C32b: in the pass, 7 of the 10 pivots of `gpt-4o` followed a
    catalogue search, so the piece that did not serve was also a catalogue candidate — and the
    argument, told to say first what matches, headed its answer with it; and in 5 of those 7 the
    cap was reached with the candidates, which were read first, cutting the substitutes the
    pivot existed to find. The loop's decision is what excludes the piece, not its availability
    label: the label stays out of the payload, as D-11 requires.
    """
    ledger = registry.evidence
    substitute_skus = {result.sku for _, result in ledger.substitutes}
    # The pieces the loop asked substitutes for. `assist/v4` describes a substitute group as
    # alternatives to a piece that does not serve, so that piece is not also offered as a match.
    anchors = {anchor for anchor, _ in ledger.substitutes}

    # `sku -> (origin, object, family id)`. The family travels **beside** the object because
    # a roster member does not carry one: the port denormalises the family's *name* onto each
    # row but not its identifier, and the contract's *null family implies exactly one member*
    # invariant cannot be honoured for a roster of three without it.
    seen: dict[str, tuple[str, object, str | None]] = {}
    for result in ledger.candidates:
        if (
            result.sku not in seen
            and result.sku not in substitute_skus
            and result.sku not in anchors
        ):
            seen[result.sku] = (GROUP_ORIGIN_CATALOGUE, result, result.family_id)
    for _, result in ledger.substitutes:
        if result.sku not in seen:
            seen[result.sku] = (GROUP_ORIGIN_SUBSTITUTES, result, result.family_id)
    # **The roster of a family is evidence too**, and it is the answer to the commonest
    # follow-up at a counter: «¿hay otra talla?». A member is a catalogue piece and not a
    # substitute — nothing about it says the shop cannot sell what was asked for — so it
    # carries the catalogue marker, and it is the one source here that contributes a size,
    # which is exactly the fact the question is about.
    for family_id, member in ledger.family_members:
        if member.sku not in seen and member.sku not in anchors:
            seen[member.sku] = (GROUP_ORIGIN_CATALOGUE, member, family_id)

    # **Which pieces survive the cap is decided by priority; where they sit is not.** The
    # substitutes are chosen first, then the rest in arrival order; the payload keeps the order
    # the evidence arrived in, so the only thing this changes is what the cap drops.
    by_priority = [
        sku for sku, (origin, _item, _family) in seen.items()
        if origin == GROUP_ORIGIN_SUBSTITUTES
    ] + [
        sku for sku, (origin, _item, _family) in seen.items()
        if origin != GROUP_ORIGIN_SUBSTITUTES
    ]
    chosen = set(by_priority[:cap])
    kept = [(sku, entry) for sku, entry in seen.items() if sku in chosen]

    payload_groups: list[FreeQueryGroup] = []
    response_groups: list[AgentAssistGroup] = []
    # Grouped by family within each origin, and **null family implies exactly one member** —
    # the invariant the contract states, enforced structurally here as `_group_results`
    # enforces it for the deterministic route rather than asserted afterwards: a piece with no
    # family gets a bucket nothing else can land in.
    buckets: dict[tuple[str, str], list[object]] = {}
    families: dict[tuple[str, str], str | None] = {}
    order: list[tuple[str, str]] = []
    for index, (_sku, (origin, result, family_id)) in enumerate(kept):
        key = (origin, family_id or f"__alone__{index}")
        if key not in buckets:
            buckets[key] = []
            families[key] = family_id
            order.append(key)
        buckets[key].append(result)

    for key in order:
        origin = key[0]
        members = buckets[key]
        payload_groups.append(
            FreeQueryGroup(
                family_label=_family_label(members),
                origin=origin,
                members=tuple(_payload_candidate(item) for item in members),
            )
        )
        response_groups.append(
            # **The same `origin` the payload group carries, read from the same key and not
            # recomputed.** Deriving it a second time — from whether the group's pieces appear
            # in `ledger.substitutes`, say — would be a second rule to keep in step with the
            # first, and the two would disagree the day the priority above changes.
            AgentAssistGroup(
                family_id=families[key],
                family_label=_family_label(members),
                origin=origin,
                members=[_response_member(item) for item in members],
            )
        )
    return payload_groups, response_groups


def _is_roster_member(item: object) -> bool:
    """A roster member, as opposed to a ranked candidate. The two carry different facts."""
    return isinstance(item, FamilyMember)


def _payload_candidate(item: object) -> FreeQueryCandidate:
    """One piece as the model sees it. **What is absent is the design.**

    No identifier and no score in either case: their digits are arbitrary, a counter argument
    never mentions either, and every numeral handed over widens the whitelist the numeric gate
    admits. A roster member does contribute its **size**, and that is deliberate rather than an
    inconsistency: the question a roster answers is «¿hay otra talla?», so the size is the fact
    the answer is about, and a fact the payload carries is a fact the argument may state.
    """
    if _is_roster_member(item):
        return FreeQueryCandidate(
            sku=item.sku,
            piece_type=None,
            materials=tuple(item.materials),
            size_label=item.size_label,
            variant_label=item.variant_label,
        )
    return FreeQueryCandidate(
        sku=item.sku,
        piece_type=None,
        materials=tuple(item.materials),
        size_label=None,
        variant_label=item.variant_label,
    )


def _response_member(item: object) -> AssistGroupMember:
    """One piece as a consumer sees it, with the identifier and the score the contract needs.

    A roster member has neither a score nor a match reason, and inventing one would be the
    decoration this layer avoids. It takes the value and the meaning the deterministic route
    already gives a roster: **it was not ranked against anything, it was enumerated**, with no
    reason to report. That precedent is `_member_from_roster`, which passes exactly this.
    """
    if _is_roster_member(item):
        return AssistGroupMember(
            product_id=str(item.product_id),
            sku=item.sku,
            variant_label=item.variant_label,
            materials=list(item.materials),
            score=1.0,
            match_reasons=[],
        )
    return AssistGroupMember(
        product_id=item.product_id,
        sku=item.sku,
        variant_label=item.variant_label,
        materials=list(item.materials),
        score=item.score,
        match_reasons=list(item.match_reasons),
    )


def _family_label(members: Sequence[object]) -> str | None:
    """The label the roster denormalises onto its members, when the group came from one.

    A ranked candidate does not carry it — the deterministic route leaves it null for the same
    reason — so a group of candidates has no label rather than a made-up one.
    """
    for item in members:
        if _is_roster_member(item) and item.family_name:
            return str(item.family_name)
    return None


def _citations(registry: ToolRegistry) -> tuple[KnowledgeCitation, ...]:
    """The corpus fragments the loop gathered, deduplicated, in the order they were seen."""
    out: dict[str, KnowledgeCitation] = {}
    for citation in registry.evidence.citations:
        out.setdefault(citation.citation_id, citation)
    return tuple(out.values())


async def _compose(
    *,
    turns: Sequence[Turn],
    answered: str,
    principal: ServicePrincipal,
    registry: ToolRegistry,
    routing: RoutingOutcome,
    pitch_client: AssistLlm | None,
    budgets: AgentBudgets,
    evidence: _Evidence,
    usage: TokenUsage,
    loop_usage: TokenUsage,
    traces: tuple[IterationTrace, ...],
    iterations: int,
    tool_calls_used: int,
    stop_reason: str,
    started: float,
) -> AgentRun:
    """Turn the evidence into an answer: the payload, the argument, and the ceiling assertion."""
    payload_groups, response_groups = _pieces(registry, budgets.pieces)
    citations = _citations(registry)

    # **D-17 · abstention on this route is a statement about the catalogue, not about the
    # request.** True only when at least one catalogue search ran, every one of them abstained,
    # and no corpus fragment was gathered. Reporting it for a request that never searched, or
    # for one the guardrail refused, would say the opposite of the truth exactly where a
    # consumer would act on it.
    abstained = (
        bool(evidence.catalogue_searches)
        and all(evidence.catalogue_searches)
        and not citations
    )

    outcome: PitchOutcome | None = None
    # No argument over an abstention, none when the loop asked a question, and none without a
    # credential: the first would write confidently about an empty candidate set, and the
    # second has nothing to write about — the Spanish a human reads for it belongs to the
    # presentation layer and comes from the closed catalogue, not from a model.
    if (
        pitch_client is not None
        and not abstained
        and evidence.clarification is None
        and (payload_groups or citations)
    ):
        outcome = await generate_pitch(
            free_query_payload_from(
                groups=payload_groups,
                warnings=list(routing.refusal_codes),
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
                # The whole conversation, rendered once and delimited once by `build_messages`.
                # **No availability label is anywhere in this payload**: the label governs the
                # loop's decision to pivot and never the prose, because the authority over
                # stock is .NET's and one of the labels is a member of the stock-marker
                # vocabulary the numeric gate watches for.
                query=transcript_plain(turns),
            ),
            AgentPitchTask.AGENT_EVIDENCE,
            client=pitch_client,
            prompt_text=load_prompt_file(AGENT_PITCH_PROMPT_VERSION),
            prompt_version=AGENT_PITCH_PROMPT_VERSION,
        )
        usage = usage + outcome.usage
        if not outcome.withheld:
            # The citations of a response carrying an argument are the ones the argument used
            # and that verified; when it is withheld they stay the ones that grounded it, so a
            # degraded response is never poorer than the structured layer's own.
            published = {item: None for item in outcome.used_citation_ids}
            by_id = {item.citation_id: item for item in citations}
            citations = tuple(by_id[item] for item in published if item in by_id)

    if usage.calls > MAX_AGENT_PROVIDER_CALLS:  # pragma: no cover — structurally impossible
        raise AssertionError(
            f"the provider was called {usage.calls} times for one request; "
            f"the ceiling is {MAX_AGENT_PROVIDER_CALLS}"
        )

    run = AgentRun(
        intent=routing.intent,
        stop_reason=stop_reason,
        partial=_is_partial(stop_reason),
        iterations=iterations,
        tool_calls_used=tool_calls_used,
        usage=usage,
        groups=tuple(response_groups),
        citations=citations,
        warnings=routing.refusal_codes,
        clarification_question=evidence.clarification,
        abstained=abstained,
        pitch=outcome.pitch if outcome is not None else EMPTY_PITCH,
        pitch_outcome=outcome,
        trace=traces,
        embedding_calls=registry.embedding_calls,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
        prompt_version=outcome.prompt_version if outcome is not None else None,
        router_usage=routing.usage,
        loop_usage=loop_usage,
        pitch_usage=outcome.usage if outcome is not None else TokenUsage(),
    )
    _log(run, principal)
    return run


def _is_partial(stop_reason: str) -> bool:
    """Partial exactly when the answer is not the one the request would have got unhurried.

    The five budget cuts, and the deployment with no client — which gathered nothing at all.
    A refusal is **not** partial: it is a complete answer to a request this shop will not
    serve. Neither is a clarification, nor a model that stopped asking.
    """
    from jbg_ai.assist.constants import AGENT_BUDGET_STOP_REASONS

    return (
        stop_reason in AGENT_BUDGET_STOP_REASONS
        or stop_reason in (STOP_NO_CLIENT, STOP_PROVIDER_ERROR)
    )


def _refused(
    routing: RoutingOutcome, principal: ServicePrincipal, elapsed: float
) -> AgentRun:
    run = AgentRun(
        intent=routing.intent,
        stop_reason=STOP_REFUSED,
        partial=False,
        iterations=0,
        tool_calls_used=0,
        usage=routing.usage,
        warnings=routing.refusal_codes,
        # **False on a refusal, always.** The guardrail's refusal is never dressed as an
        # abstention.
        abstained=False,
        elapsed_ms=elapsed,
        router_usage=routing.usage,
    )
    _log(run, principal)
    return run


def _no_client(
    routing: RoutingOutcome, principal: ServicePrincipal, elapsed: float
) -> AgentRun:
    run = AgentRun(
        intent=routing.intent,
        stop_reason=STOP_NO_CLIENT,
        # Partial, and the reason is worth stating: no budget was exhausted, but nothing was
        # gathered either, and a consumer reading `partial: false` over an empty response would
        # read it as «the catalogue had nothing», which is the opposite of what happened.
        partial=True,
        iterations=0,
        tool_calls_used=0,
        usage=routing.usage,
        warnings=routing.refusal_codes,
        abstained=False,
        elapsed_ms=elapsed,
        router_usage=routing.usage,
    )
    _log(run, principal)
    return run


def _log(run: AgentRun, principal: ServicePrincipal) -> None:
    """One line per request: the counters, the stop reason, the cost and the latency.

    **Never the transcript and never a tool argument.** A log line is durable storage outside
    the database, and the operator's text is the one thing here a customer said out loud — the
    rule C30b and C31 each left with a test, applied to the stage that has the most to leak.
    The tools are named because a name is what the evaluation compares; what they were called
    with is not.
    """
    logger.info(
        "stage=%s trace_id=%s intent=%s stop=%s partial=%s iterations=%s "
        "tool_calls=%s tools=%s groups=%s citations=%s abstained=%s "
        "clarified=%s agent_prompt_version=%s prompt_version=%s model=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s provider_calls=%s "
        "embedding_calls=%s elapsed_ms=%.1f pitch_chars=%s pitch_sha256=%s",
        STAGE,
        principal.trace_id,
        run.intent,
        run.stop_reason,
        run.partial,
        run.iterations,
        run.tool_calls_used,
        ",".join(
            call.tool for item in run.trace for call in item.tools
        )
        or "none",
        len(run.groups),
        len(run.citations),
        run.abstained,
        run.clarification_question is not None,
        run.agent_prompt_version,
        run.prompt_version,
        run.usage.model,
        run.usage.prompt_tokens,
        run.usage.completion_tokens,
        run.usage.total_tokens,
        run.usage.calls,
        run.embedding_calls,
        run.elapsed_ms,
        len(run.pitch),
        run.pitch_outcome.digest if run.pitch_outcome is not None else "none",
        extra={"trace_id": principal.trace_id},
    )
