namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Sale agent request sent to jbg-ai (<c>POST /v1/assist/agent</c>). C42.
/// </summary>
/// <remarks>
/// <para>
/// <strong>The transcript travels in the request because the service stores nothing between
/// calls.</strong> That is a property the generation and routing capabilities hold with tests, and
/// a session store would collide with it head-on. The price is that the caller controls the factor
/// that dominates the cost of a loop, which is exactly why the three caps are part of the contract
/// and validated here before a provider call is spent.
/// </para>
/// <para>
/// The frozen contract accepts an optional <c>pos_id</c> in the body and ignores it, because scope
/// comes from the service token. This model omits it for the same reason
/// <see cref="AiAssistSaleRequest"/> does: serializing a value the service discards would suggest
/// the body carries authority, and on this route the suggestion would be worse — the token is what
/// decides whether the availability prefilter applies at all.
/// </para>
/// </remarks>
public class AiAssistAgentRequest
{
    /// <summary>The conversation so far, oldest turn first.</summary>
    public List<AiAgentTurn> Turns { get; set; } = [];

    /// <summary>Groups wanted after hydration. Null takes the contract's default.</summary>
    public int? TopK { get; set; }
}

/// <summary>
/// One turn of the conversation, as the contract declares it.
/// </summary>
/// <remarks>
/// <strong>The assistant's role is attributed and never trusted.</strong> The service keeps no
/// conversation, so every turn arrives from the client — which is what authorises the frontend to
/// put a synthetic line in an assistant turn whose argument was withheld, and what makes the total
/// character cap a sum over turns the client wrote rather than over turns the service remembers.
/// </remarks>
public class AiAgentTurn
{
    /// <summary><c>operario</c> or <c>asistente</c>.</summary>
    public required string Role { get; set; }

    /// <summary>What that turn said.</summary>
    public required string Text { get; set; }
}

/// <summary>
/// Sale agent response from jbg-ai: the deterministic shape <strong>plus five fields</strong>.
/// </summary>
/// <remarks>
/// <para>
/// A subclass and not an independent model, and that is the whole value of the cut: the comparison
/// this capability exists to enable runs both routes over the same set, so it has to be a
/// difference of fields rather than a translation between two shapes.
/// </para>
/// <para>
/// Carries identifiers, codes and generated prose — never a price or a quantity, which .NET owns.
/// </para>
/// </remarks>
public class AiAssistAgentResponse : AiAssistSaleResponse
{
    /// <summary>
    /// Groups carrying <strong>the provenance of their evidence</strong>, which the deterministic
    /// route's groups do not.
    /// </summary>
    /// <remarks>
    /// Declared with <c>new</c> and not by widening <see cref="AiAssistGroup"/>, mirroring the
    /// service side exactly: the shared model is what <c>POST /v1/assist/sale</c> publishes, and
    /// the contract narrows the reference on this route rather than adding a field there.
    /// </remarks>
    public new List<AiAssistAgentGroup> Groups { get; set; } = [];

    /// <summary>
    /// The answer is not the one an unhurried request would have produced.
    /// </summary>
    /// <remarks>
    /// A declared budget cut the loop short, or no agent credential is configured and nothing was
    /// gathered. <strong>False for a refusal</strong>, which is a complete answer to a request this
    /// shop will not serve, and false when the model simply stopped asking for tools.
    /// </remarks>
    public bool Partial { get; set; }

    /// <summary>
    /// Why the loop stopped, from the service's closed vocabulary of ten.
    /// </summary>
    /// <remarks>
    /// <strong>Carried as reported and never inferred from the counters.</strong> Five iterations
    /// does not say whether the fifth was the last one needed or the one that ran out, and those
    /// are opposite statements about the answer being read.
    /// </remarks>
    public string StopReason { get; set; } = string.Empty;

    /// <summary>Turns of the loop that ran; zero when it never started.</summary>
    public int Iterations { get; set; }

    /// <summary>
    /// Tool executions this request paid for, accumulated across turns.
    /// </summary>
    /// <remarks>
    /// Calls refused for want of budget are counted neither here nor in the tool budget: no port
    /// was touched for them.
    /// </remarks>
    public int ToolCallsUsed { get; set; }

    /// <summary>Per-iteration trace. Always present and bounded, never requested by a parameter.</summary>
    public List<AiAgentTraceIteration> Trace { get; set; } = [];

    /// <summary>
    /// Version of the <strong>loop's</strong> argument prompt, reported apart from
    /// <c>PromptVersion</c>, which keeps the meaning it already has.
    /// </summary>
    public string? AgentPromptVersion { get; set; }

    /// <summary>Usage of the request, with the provider-call count the shared object lacks.</summary>
    public new AiAgentUsage Usage { get; set; } = new();
}

/// <summary>One group of the agent's answer, carrying where it came from.</summary>
public class AiAssistAgentGroup : AiAssistGroup
{
    /// <summary>
    /// <c>catalogo</c> for a catalogue match, <c>sustitutos</c> for an alternative to a piece that
    /// did not serve.
    /// </summary>
    /// <remarks>
    /// <strong>Never flattened and never derived from position.</strong> A substitute and a match
    /// are different things to say to a customer, and the payload keeps the order the evidence
    /// arrived in, so position says nothing about provenance.
    /// </remarks>
    public string Origin { get; set; } = string.Empty;
}

/// <summary>Usage of one agent request: the shared figures plus the provider-call count.</summary>
/// <remarks>
/// <c>Model</c> names only the last stage that reported — the argument's when it ran, otherwise the
/// loop's or the classifier's — so it is <strong>not a pricing key</strong> for the token counts
/// beside it: on this route those counts add up to as many as three stages that may run different
/// models. The first cost figure of C32b made exactly that mistake.
/// </remarks>
public class AiAgentUsage : AiUsage
{
    /// <summary>Chat-provider calls this request made, across the three stages.</summary>
    public int Calls { get; set; }
}

/// <summary>One turn of the loop: which tools it ran, what it cost and how long it took.</summary>
public class AiAgentTraceIteration
{
    /// <summary>One-based index of the iteration.</summary>
    public int Iteration { get; set; }

    /// <summary>Tools invoked in this iteration.</summary>
    public List<AiAgentTraceTool> Tools { get; set; } = [];

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
/// One tool call of one iteration: <strong>what, and how it went.</strong>
/// </summary>
/// <remarks>
/// The arguments are absent <strong>by rule and not by omission</strong>: they are the operator's
/// question as the model reformulated it, which the service's no-persistence rule keeps out of
/// durable storage. The contract does not carry them, so neither does this.
/// </remarks>
public class AiAgentTraceTool
{
    /// <summary>Name of the tool invoked, from the frozen set of six.</summary>
    public string Tool { get; set; } = string.Empty;

    /// <summary>Whether the observation succeeded.</summary>
    public bool Ok { get; set; }

    /// <summary>Closed-vocabulary failure cause when it did not, null otherwise.</summary>
    public string? Cause { get; set; }
}
