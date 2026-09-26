"""Sale assistance contracts: family-grouped results, rule warnings and citations.

The `pitch` never contains a resolved price or stock figure — it carries the
`{{price}}` and `{{stock}}` placeholders for the .NET API to substitute. **And the
prohibition holds over the whole response, not only over the pitch**: no model here carries
a price, a stock quantity or the availability bucket the index keeps for ranking.

**This block moved once, in C30a, and the window was the reason.** The frozen shape could
not serve its consumer — `family_id` required against a catalogue where ~58 % of products
have no family, and `query` required against a consumer anchored to a piece — and at that
moment the route had **zero** consumers: `IAiGatewayClient` had no assist method and C34 did
not exist. Regenerating the snapshot is a contract negotiation and not a chore, as the
service README says; C18a and C18b set the precedent of doing it in the same change that
moves the boundary, and doing it later would have cost what doing it then did not.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from jbg_ai.api.schemas.common import ScopedResponse, Usage
from jbg_ai.api.schemas.retrieval import RetrievalFilters
from jbg_ai.assist.constants import (
    AGENT_STOP_REASONS,
    ASSIST_INTENTS,
    ASSIST_WARNING_CODES,
    GROUP_ORIGIN_CATALOGUE,
    GROUP_ORIGIN_SUBSTITUTES,
    MAX_TRANSCRIPT_CHARS,
    MAX_TRANSCRIPT_TURNS,
    MAX_TURN_CHARS,
)


class AssistContext(BaseModel):
    """Optional hints the operator can pass along with the query."""

    occasion: str | None = None
    recipient: str | None = None
    preferred_materials: list[str] = Field(default_factory=list)
    notes: str | None = None


class AssistRequest(BaseModel):
    """One of the two anchors is required, and **at least** one rather than exactly one.

    "Exactly one" would exclude the mode that carries the most value for the least cost —
    a piece on the screen plus the question the customer just asked — which is the mode
    that finally gives the ten counter-conversation documents of the corpus a route to an
    operator's screen. `IndexSyncRequest` with `full` against `since` is the same shape.
    """

    product_id: str | None = Field(
        default=None,
        min_length=1,
        description="Anchor the assistance to one indexed piece. Null means a free query",
    )
    query: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="What the operator asked. Null means the piece itself is the request",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Families wanted after hydration")
    filters: RetrievalFilters = Field(
        default_factory=RetrievalFilters,
        description=(
            "Catalog filters for the free-query mode. Ignored when a piece is anchored: "
            "the anchor already determines what is retrieved"
        ),
    )
    context: AssistContext | None = None
    locale: str = Field(default="es-ES")
    pos_id: str | None = Field(
        default=None,
        description="Accepted for client compatibility and ignored; scope comes from the token",
    )

    @model_validator(mode="after")
    def _requires_an_anchor(self) -> AssistRequest:
        """Name **both** fields: a caller that sent neither needs to be told the alternatives."""
        if self.product_id is None and self.query is None:
            raise ValueError(
                "at least one of product_id and query is required: "
                "product_id anchors the assistance to a piece, query asks a question, "
                "and a request carrying neither anchors nothing"
            )
        return self


class AgentTurn(BaseModel):
    """One turn of the conversation the agent route answers. C32b.

    **A turn attributed to the assistant is client-supplied data.** The client composes the
    whole request and can write what it likes in `role`, so trusting that label would hand an
    attacker a channel the operator's own field does not offer. Both roles travel under the
    same length cap and both are enclosed in the same data delimiters inside the user message.
    """

    role: Literal["operario", "asistente"] = Field(
        ...,
        description=(
            "Who the turn is attributed to. `asistente` is **attributed and never trusted**: "
            "this service stores no conversation, so every turn arrives from the client"
        ),
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TURN_CHARS,
        description=(
            "What was said. The cap is the one a single query of the deterministic route "
            "already declares, so one turn of a conversation cannot be longer than one query"
        ),
    )


class AgentAssistRequest(BaseModel):
    """A conversation to answer, and the caps that bound it. C32b.

    **The transcript travels in the request because this service stores nothing between
    calls** — the property the generation and routing capabilities already hold with tests,
    which a session store would collide with head-on. The price is that the client now
    controls the factor that dominates the cost of a loop, which is why the three caps are
    part of the contract rather than an implementation detail.
    """

    turns: list[AgentTurn] = Field(
        ...,
        min_length=1,
        max_length=MAX_TRANSCRIPT_TURNS,
        description=(
            "The conversation so far, oldest first. At least one turn must be the operator's: "
            "the one being answered is the last of those, because a client that appends its "
            "own account of the reply must not move what the request is asking"
        ),
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Families wanted after hydration")
    context: AssistContext | None = None
    locale: str = Field(default="es-ES")
    pos_id: str | None = Field(
        default=None,
        description="Accepted for client compatibility and ignored; scope comes from the token",
    )

    @model_validator(mode="after")
    def _within_the_total_cap(self) -> AgentAssistRequest:
        """The total is **not implied** by the other two caps, which is why it is a third one.

        The maximum number of turns at the maximum length each is well past this bound, so a
        transcript can satisfy both of the others and still be too large to serve.
        """
        total = sum(len(turn.text) for turn in self.turns)
        if total > MAX_TRANSCRIPT_CHARS:
            raise ValueError(
                f"the transcript is {total} characters; the maximum total is "
                f"{MAX_TRANSCRIPT_CHARS}, independently of the per-turn maximum"
            )
        return self


class AssistGroupMember(BaseModel):
    product_id: str
    sku: str
    variant_label: str | None = Field(default=None, description="Null when the variant is unknown")
    materials: list[str] = Field(default_factory=list)
    score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: list[str] = Field(
        default_factory=list,
        description=(
            "Why the retrieval produced this candidate, in its own vocabulary. Reused rather "
            "than restated: these codes carry real provenance since C21 and the panel already "
            "maps them to badges"
        ),
    )


class AssistGroup(BaseModel):
    """One product family; members are the variants the operator can disambiguate.

    `family_id` is **nullable**, and the invariant that comes with it is *null implies exactly
    one member*. A synthetic identifier would have been a lie on the wire: .NET and the
    frontend would have to recognise a prefix no schema declares, and nothing in the type
    would stop the variants warning from firing on a group of one.
    """

    family_id: str | None = Field(
        default=None,
        description="Null when the product belongs to no family; such a group holds one member",
    )
    family_label: str | None = None
    members: list[AssistGroupMember]


class Citation(BaseModel):
    """A fragment of the knowledge corpus, carrying everything needed to present it honestly.

    **Citations are corpus fragments and nothing else.** Citing the catalogue would verify
    nothing — the product's metadata already travels in the response — so the anchoring of a
    candidate in the catalogue is expressed with `match_reasons` instead.

    `citation_id` is `<documento>#<sección>`: with the corpus in git it *resolves, locates and
    opens* a file and a heading. `claim_scope` is not decoration either — it separates a fact
    of the world from a commitment of the establishment, which is the failure the whole
    marking mechanism of C23 exists to prevent, and 25 of the corpus's 161 fragments carry it.
    """

    citation_id: str = Field(
        ..., description="`<document>#<section>`; resolves to a file and a heading in git"
    )
    document_title: str
    section_title: str
    doc_type: str = Field(..., description="Corpus document type: material, faq, politica, talla")
    claim_scope: str = Field(
        ...,
        description=(
            "`general` for a fact of the world, `establecimiento` for a commitment of the "
            "house, which is never read to a customer without confirming it in store"
        ),
    )
    score: float = Field(..., ge=0.0, le=1.0)
    snippet: str
    product_id: str | None = Field(
        default=None, description="The piece this claim supports, when the request anchored one"
    )


class AssistResponse(ScopedResponse):
    intent: str = Field(
        ...,
        description=(
            "Closed vocabulary of the assistance capability: "
            + ", ".join(ASSIST_INTENTS)
            + ". `product_pitch` for a piece with no question, derived from the request shape "
            "and unchanged since C30a. For a free query it is the verdict C31's classifier "
            "reached before retrieving anything: `in_domain` admitted, `out_of_domain` not "
            "this business, `not_in_catalogue` jewellery this catalogue does not stock. "
            "`unclassified` means no classification was made — no classifier ran, or one ran "
            "and could not be used — and the request was served exactly as it was before this "
            "capability routed anything"
        ),
    )
    groups: list[AssistGroup]
    pitch: str = Field(
        ...,
        description="Generated prose with unresolved {{price}} / {{stock}} placeholders",
    )
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Rule-derived codes, from the closed vocabulary of the assistance capability: "
            + ", ".join(ASSIST_WARNING_CODES)
            + ". Never a sentence: the Spanish a human reads belongs to the frontend. The two "
            "refusal codes are distinct on purpose — a trade this shop does not practise and a "
            "piece it does not carry are two different things to say to a customer — and "
            "`knowledge_not_covered` states that an anchored question produced no citation "
            "after the corpus distance threshold, so the argument describes the piece without "
            "claiming to have answered"
        ),
    )
    clarification_question: str | None = Field(
        default=None,
        description=(
            "A question back to the operator when the classifier found the query carries too "
            "little to search with, naming the axis it left out. Null in every other case, "
            "including a refusal. Selected in code from a closed catalogue of es-ES templates "
            "and never written by the model: the field is typed as prose rather than as a "
            "code, so the presentation layer cannot resolve it, and two requests carrying the "
            "same query produce exactly the same text"
        ),
    )
    usage: Usage
    abstained: bool = Field(
        ...,
        description=(
            "The retrieval's abstention rule decided the catalogue cannot answer this query, "
            "so no group is returned. Emitted in every mode — constantly false for a piece "
            "with no question, where there is no retrieval to abstain from — and deliberately "
            "**not** `low_confidence`, whose measured meaning is cross-branch consensus and "
            "fires on answerable queries far more often than on out-of-domain ones"
        ),
    )
    prompt_version: str | None = Field(
        default=None,
        description=(
            "Version of the prompt the generation layer ran with; null when it did not run"
        ),
    )


class AgentUsage(Usage):
    """The agent's usage object: everything the shared one carries, plus the call count. C32b.

    **Added here and deliberately not to `Usage`.** The shared model is what
    `POST /v1/assist/sale` publishes, and widening it would move that route's schema — which
    this change promises not to do. Without the count, though, «the ceiling is observable from
    the same object a consumer reads» would not be true of this route, and the ceiling is one
    of the four things the project evaluates about an agent.

    The figure counts **chat calls of one request**: the classification, the loop's turns and
    the argument with its repair. The embedding lookups the tools make are counted by the
    registry's own counter and are not folded in here, because `usage.calls` already means
    exactly this on the other route and a number that means two things in two places is a
    number nobody can compare.

    **`model` is redeclared here, and only here, because on this route it cannot be read as the
    shared object's field is read.** The token counts add up to three stages that may run three
    different models — the classifier, the loop and the argument — and `model` names only the
    last one that reported, so tokens priced at that model's rate misstate the cost. The first
    cost figure of C32b made exactly that mistake. The shared `Usage` keeps its description:
    `POST /v1/assist/sale` must not move.
    """

    model: str | None = Field(
        default=None,
        description=(
            "Model of the LAST stage that reported one — the argument's when it ran, otherwise "
            "the loop's or the classifier's. **Not a price key for the token counts beside "
            "it**: on this route those counts add up to as many as three stages that may run "
            "different models, so tokens multiplied by this model's price misstate the cost. "
            "Null while stubbed"
        ),
    )
    calls: int = Field(
        default=0,
        ge=0,
        description=(
            "Chat-provider calls this request made: one classification, at most one per loop "
            "turn, and the argument with its single repair. Bounded by a ceiling **derived "
            "from the constants of those three stages** rather than written as a literal. "
            "Embedding lookups are counted apart and are not included"
        ),
    )


class AgentAssistGroup(AssistGroup):
    """One group of the agent's answer, carrying **where it came from**. C42.

    **A subclass and deliberately not a field on `AssistGroup`**, by the precedent `AgentUsage`
    sets one class up: the shared model is what `POST /v1/assist/sale` publishes, and widening it
    would move that route's schema — which this change promises not to do. Adding it here is an
    addition to this route alone, so a consumer that ignores it receives exactly the response it
    received before.

    **Why it has to reach the consumer at all.** The distinction existed only in the payload the
    model reads, so the argument said «y como alternativa…» because the prompt told it to, while
    the screen had no way to label the rows — which is precisely what the marker exists to
    prevent. Offering a second best as though it were what was asked for is what a customer
    notices, and the loop asked for substitutes 125 times in the measured pass: routine, not an
    edge case.
    """

    origin: Literal[GROUP_ORIGIN_CATALOGUE, GROUP_ORIGIN_SUBSTITUTES] = Field(
        ...,
        description=(
            "Where this group came from, from a closed vocabulary of two: "
            f"`{GROUP_ORIGIN_CATALOGUE}` for a catalogue match — which a roster member also is, "
            "since nothing about it says the shop cannot sell what was asked for — and "
            f"`{GROUP_ORIGIN_SUBSTITUTES}` for an alternative to a piece that did not serve. "
            "**Never to be inferred from position or ordering**: the payload keeps the order the "
            "evidence arrived in, so position says nothing about provenance"
        ),
    )


class AgentTraceTool(BaseModel):
    """One tool call of one iteration, as the wire reports it: **what, and how it went.**

    The arguments are absent by rule and not by omission. A consumer logs the responses it
    receives, and the arguments a tool was called with are the operator's question as the
    model reformulated it — which the rule this service already holds keeps out of durable
    storage. Tool names are what the evaluation compares: tools invoked against tools expected.
    """

    tool: str = Field(..., description="Name of the tool invoked, from the frozen set of six")
    ok: bool
    cause: str | None = Field(
        default=None,
        description=(
            "Closed-vocabulary failure cause when the observation failed, null otherwise. "
            "`presupuesto_agotado` means the consumer refused the call because the request's "
            "tool budget was spent, and that **no port was touched** for it"
        ),
    )


class AgentTraceIteration(BaseModel):
    """One turn of the loop: which tools it ran, what it cost and how long it took."""

    iteration: int = Field(..., ge=1)
    tools: list[AgentTraceTool] = Field(default_factory=list)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    elapsed_ms: float = Field(default=0.0, ge=0.0)


class AgentAssistResponse(AssistResponse):
    """What `POST /v1/assist/agent` returns: the deterministic shape **plus** five fields.

    **A subclass and not an independent model, and that is the whole value of the cut.** The
    comparison this capability exists to enable runs both routes over the same set, so it has
    to be a difference of fields rather than a translation between two shapes: every field of
    the deterministic response is present here with the same meaning, and what the agent adds
    are additions.
    """

    groups: list[AgentAssistGroup] = Field(
        ...,
        description=(
            "The deterministic route's groups, each carrying **the provenance of its evidence**. "
            "Narrowed here rather than widened there, which is what keeps the contract move an "
            "addition to this route alone"
        ),
    )
    partial: bool = Field(
        ...,
        description=(
            "The answer is not the one an unhurried request would have produced: a declared "
            "budget cut the loop short, or no agent credential is configured and nothing was "
            "gathered. **False for a refusal**, which is a complete answer to a request this "
            "shop will not serve, and false when the model simply stopped asking for tools"
        ),
    )
    stop_reason: str = Field(
        ...,
        description=(
            "Why the loop stopped, from a closed vocabulary: "
            + ", ".join(AGENT_STOP_REASONS)
            + ". **Always present and never to be inferred from the counters**: five "
            "iterations does not say whether the fifth was the last one needed or the one "
            "that ran out, and those are opposite statements about the answer being read"
        ),
    )
    iterations: int = Field(
        ..., ge=0, description="Turns of the loop that ran; zero when it never started"
    )
    tool_calls_used: int = Field(
        ...,
        ge=0,
        description=(
            "Tool executions this request paid for, accumulated across turns. Calls refused "
            "for want of budget are counted in neither this figure nor the tool budget: no "
            "port was touched for them"
        ),
    )
    trace: list[AgentTraceIteration] = Field(
        default_factory=list,
        description=(
            "Per iteration: the tools invoked, whether each succeeded and with what cause if "
            "not, plus what the iteration cost and how long it took. **Always present and "
            "bounded** rather than requested by a parameter, which would create two response "
            "shapes to test. It carries no tool argument and no observation content; a richer "
            "trace is available in process to a caller that embeds this layer directly"
        ),
    )
    agent_prompt_version: str | None = Field(
        default=None,
        description=(
            "Version of the **loop's** prompt, reported apart from `prompt_version`, which "
            "keeps the meaning it already has: the version the argument was written with. Two "
            "calls with different outputs and potentially different models, so a single field "
            "would make either figure unreadable the first time one of the two moved. Null "
            "when no loop ran"
        ),
    )
    usage: AgentUsage
