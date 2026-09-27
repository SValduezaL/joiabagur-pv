namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// The three caps the frozen contract declares on a transcript, mirrored here so the request is
/// refused <strong>before</strong> a provider call is spent. C42.
/// </summary>
/// <remarks>
/// <para>
/// Mirrored and not inferred, and the three are independent: <strong>the total is not implied by
/// the other two.</strong> Twelve turns of five hundred characters is six thousand, which the total
/// refuses, so a validator checking only per-turn length would pass a request the service rejects.
/// </para>
/// <para>
/// <strong>The total sums every turn, the assistant's included</strong>, and that is what fixes how
/// deep a conversation can go. With the argument sent back verbatim — measured at a median of 386
/// characters and a maximum of 605 — six exchanges is twelve turns, so the turn cap bites first
/// while the character count sits at roughly 2 466 of 4 000. A counter that only measured what the
/// operator typed would read half its limit with the refusal already earned.
/// </para>
/// <para>
/// These are the service's values, so they move when the contract does and never on their own.
/// </para>
/// </remarks>
public static class AgentTranscriptCaps
{
    /// <summary>Turns a transcript may carry, operator and assistant together.</summary>
    public const int MaxTurns = 12;

    /// <summary>Characters a single turn may carry.</summary>
    public const int MaxTurnChars = 500;

    /// <summary>Characters the whole transcript may carry, summed over every turn.</summary>
    public const int MaxTranscriptChars = 4000;

    /// <summary>The role of a turn the operator wrote.</summary>
    public const string OperatorRole = "operario";

    /// <summary>The role of a turn attributed to the assistant.</summary>
    public const string AssistantRole = "asistente";
}

/// <summary>
/// A turn of the conversation as the operator's panel sends it. C42.
/// </summary>
/// <remarks>
/// <strong>The assistant's turns come from the client, and that is the contract's own rule.</strong>
/// The AI service stores no conversation, so the whole transcript travels on every request. Two
/// consequences the panel depends on: a turn whose argument was withheld may carry a short
/// synthetic line naming the pieces, so a later «ése» still has an antecedent; and the total
/// character cap is a sum over <em>every</em> turn, the assistant's included.
/// </remarks>
public class AgentAssistTurnDto
{
    /// <summary>Longest a single turn may be, per the frozen contract.</summary>
    public const int MaxTextLength = 500;

    /// <summary>Who the turn is attributed to: <c>operario</c> or <c>asistente</c>.</summary>
    public string Role { get; set; } = string.Empty;

    /// <summary>What that turn said.</summary>
    public string Text { get; set; } = string.Empty;
}

/// <summary>
/// A request to the sale agent: the conversation so far and the scope to answer it in.
/// </summary>
public class AgentAssistRequest
{
    /// <summary>Turns the frozen contract accepts, oldest first.</summary>
    /// <remarks>
    /// Bounded by <see cref="AgentTranscriptCaps.MaxTurns"/>, and the bound is validated here
    /// rather than delegated: a caller must not spend a provider call to be told the request was
    /// malformed.
    /// </remarks>
    public List<AgentAssistTurnDto> Turns { get; set; } = [];

    /// <summary>
    /// The shop to answer about, or <see langword="null"/> for every shop at once.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>Null is the absence of a shop and never a wildcard</strong>, exactly as on the
    /// free-query request: it builds the every-shop scope, whose token omits the <c>pos_id</c>
    /// claim, and the service reads the absence as «do not apply the availability prefilter».
    /// </para>
    /// <para>
    /// On this route the absence costs one thing more than stock figures, and the panel says so:
    /// with no shop the availability label can never report that the shop is out of stock, so
    /// <strong>the loop cannot pivot to substitutes</strong>. A capability lost, not a display
    /// preference.
    /// </para>
    /// </remarks>
    public Guid? PointOfSaleId { get; set; }

    /// <summary>Groups wanted, bounded by the configured maximum.</summary>
    public int? PageSize { get; set; }

    /// <summary>The visit this conversation belongs to, for telemetry.</summary>
    public Guid? SearchSessionId { get; set; }
}

/// <summary>
/// One group of the agent's answer, with the members this point of sale actually carries and
/// <strong>where the group came from</strong>.
/// </summary>
public class AgentAssistGroupDto
{
    /// <summary>Family identifier, or null when the piece belongs to none.</summary>
    public string? FamilyId { get; set; }

    /// <summary>Family label, or null.</summary>
    public string? FamilyLabel { get; set; }

    /// <summary>
    /// <c>catalogo</c> or <c>sustitutos</c>, carried from the service and never derived.
    /// </summary>
    /// <remarks>
    /// The one field this response adds to its free-query sibling's group, and the reason it exists
    /// is a customer rather than a schema: offering a second-best alternative as though it were
    /// what was asked for is what makes somebody stop trusting the counter. The screen labels the
    /// two groups from this value and never from their order.
    /// </remarks>
    public string Origin { get; set; } = string.Empty;

    /// <summary>
    /// Members in the order the AI service ranked them, hydrated against the catalog. Never
    /// re-sorted here: re-sorting would make the rank measure this code instead of retrieval.
    /// </summary>
    public List<AssistedSearchResultDto> Members { get; set; } = [];
}

/// <summary>One tool call of one iteration of the loop.</summary>
public class AgentTraceToolDto
{
    /// <summary>Name of the tool invoked, from the frozen set of six.</summary>
    public string Tool { get; set; } = string.Empty;

    /// <summary>Whether the observation succeeded.</summary>
    public bool Ok { get; set; }

    /// <summary>Closed-vocabulary failure cause when it did not, null otherwise.</summary>
    public string? Cause { get; set; }
}

/// <summary>
/// One turn of the loop, as the screen shows it: which tools ran, how they went, what it cost.
/// </summary>
/// <remarks>
/// <strong>No tool argument and no observation content, by rule.</strong> The contract excludes
/// them — the arguments are the operator's question as the model reformulated it — so there is
/// nothing here to forward, and the screen has nothing to render that it should not.
/// </remarks>
public class AgentTraceIterationDto
{
    /// <summary>One-based index of the iteration.</summary>
    public int Iteration { get; set; }

    /// <summary>Tools invoked in this iteration.</summary>
    public List<AgentTraceToolDto> Tools { get; set; } = [];

    /// <summary>Prompt tokens this iteration cost.</summary>
    public int PromptTokens { get; set; }

    /// <summary>Completion tokens this iteration cost.</summary>
    public int CompletionTokens { get; set; }

    /// <summary>Total tokens this iteration cost.</summary>
    public int TotalTokens { get; set; }

    /// <summary>Wall-clock milliseconds the iteration took.</summary>
    public double ElapsedMs { get; set; }
}

/// <summary>
/// What one agent turn cost, for an administrator. Never sent to an operator.
/// </summary>
/// <remarks>
/// The free-query usage object plus the provider-call count, which is the figure that makes the
/// loop's ceiling observable from the same object a consumer reads. <strong>Inputs of a cost and
/// never the cost</strong>: tokens and model, never euros, because a tariff written into a screen
/// is wrong the day the provider moves it — and on this route <c>Model</c> is not even a pricing
/// key, since the counts add up to as many as three stages that may run different models.
/// </remarks>
public class AgentAssistUsageDto : FreeQueryUsageDto
{
    /// <summary>Chat-provider calls this request made, across the three stages.</summary>
    public int ProviderCalls { get; set; }
}

/// <summary>
/// The agent's answer to one turn: everything the free query returns, plus what the loop did.
/// </summary>
/// <remarks>
/// <para>
/// <strong>Every field of the free-query response is here with the same meaning</strong>, which is
/// what keeps the comparison of the two paths a difference of fields rather than a translation. The
/// five additions describe the loop: whether a budget cut it short, why it stopped, how many turns
/// and tool calls it paid for, the step-by-step trace, and the version of the argument prompt.
/// </para>
/// <para>
/// No figure in here was written by a model: price and stock come from the catalog and the
/// inventory of the point of sale, exactly as on the sale card.
/// </para>
/// </remarks>
public class AgentAssistResponse
{
    /// <summary>Groups in the order the service ranked them, each labelled by provenance.</summary>
    public List<AgentAssistGroupDto> Groups { get; set; } = [];

    /// <summary>The argument. Null in every state but <see cref="PitchStatus.Generated"/>.</summary>
    public string? Pitch { get; set; }

    /// <summary>State of the argument.</summary>
    public PitchStatus PitchStatus { get; set; }

    /// <summary>Corpus fragments the argument used, each with its claim scope.</summary>
    public List<SalesAssistCitationDto> Citations { get; set; } = [];

    /// <summary>Warning codes <strong>about the conversation</strong>, never about a piece.</summary>
    public List<string> Warnings { get; set; } = [];

    /// <summary>The question the service asked back, verbatim, when it asked one.</summary>
    public string? ClarificationQuestion { get; set; }

    /// <summary>What the router decided about the last turn, passed through.</summary>
    public string? Intent { get; set; }

    /// <summary>Whether retrieval abstained because nothing cleared its threshold.</summary>
    public bool Abstained { get; set; }

    /// <summary>Whether the AI service served this turn.</summary>
    public bool AiAvailable { get; set; }

    /// <summary>Why the AI path degraded, from the closed vocabulary. Null when it did not.</summary>
    public string? DegradedReason { get; set; }

    /// <summary>
    /// The answer is not the one an unhurried request would have produced.
    /// </summary>
    /// <remarks>
    /// Measured at <strong>2.0 %</strong> of requests on the model that is served, against 58.8 %
    /// on the cheap one — which is why the screen states it without alarm and states it last.
    /// </remarks>
    public bool Partial { get; set; }

    /// <summary>
    /// Why the loop stopped, from the service's closed vocabulary of ten.
    /// </summary>
    /// <remarks>
    /// <strong>Carried as reported and never inferred from <see cref="Iterations"/> or
    /// <see cref="ToolCallsUsed"/>.</strong> A count does not say whether the last step was the
    /// last one needed or the one that ran out, and those are opposite claims about the answer the
    /// operator is reading.
    /// </remarks>
    public string StopReason { get; set; } = string.Empty;

    /// <summary>Turns of the loop that ran; zero when it never started.</summary>
    public int Iterations { get; set; }

    /// <summary>Tool executions this turn paid for.</summary>
    public int ToolCallsUsed { get; set; }

    /// <summary>
    /// The per-iteration trace: <strong>the only thing on screen that distinguishes an agent from
    /// a single prompt.</strong>
    /// </summary>
    public List<AgentTraceIterationDto> Trace { get; set; } = [];

    /// <summary>Version of the loop's argument prompt. Null when no loop ran.</summary>
    public string? AgentPromptVersion { get; set; }

    /// <summary>What this turn cost. Null for anyone but an administrator.</summary>
    public AgentAssistUsageDto? Usage { get; set; }

    /// <summary>
    /// Identifier of the recorded search event, so a selection can be attributed. Null when
    /// telemetry could not persist, which never fails the turn.
    /// </summary>
    public Guid? SearchEventId { get; set; }

    /// <summary>Point of sale the turn was served for, or null for every one of them.</summary>
    public Guid? PointOfSaleId { get; set; }

    /// <summary>Members the AI service proposed, before hydration.</summary>
    public int CandidatesReturned { get; set; }

    /// <summary>Members that survived hydration at this point of sale.</summary>
    public int SurvivedHydration { get; set; }

    /// <summary>Correlation identifier, for an administrator reading the log beside the screen.</summary>
    public string? TraceId { get; set; }
}

/// <summary>How an agent turn ended, so the endpoint can map it without knowing HTTP.</summary>
public enum AgentAssistOutcome
{
    /// <summary>The turn was answered.</summary>
    Success = 0,

    /// <summary>The caller may not search on that point of sale.</summary>
    PointOfSaleForbidden = 1,

    /// <summary>The point of sale does not exist or is not active.</summary>
    PointOfSaleUnavailable = 2
}

/// <summary>Result of an agent turn: an outcome and, when it succeeded, a response.</summary>
public sealed record AgentAssistResult(
    AgentAssistOutcome Outcome,
    AgentAssistResponse? Response)
{
    public static AgentAssistResult Ok(AgentAssistResponse response) =>
        new(AgentAssistOutcome.Success, response);

    public static AgentAssistResult Forbidden() =>
        new(AgentAssistOutcome.PointOfSaleForbidden, null);

    public static AgentAssistResult Unavailable() =>
        new(AgentAssistOutcome.PointOfSaleUnavailable, null);
}
