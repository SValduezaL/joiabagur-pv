namespace JoiabagurPV.Application.Configuration;

/// <summary>
/// Configuration for the outbound integration with the jbg-ai service.
/// Bound from the "AiGateway" section and validated at application start.
/// </summary>
/// <remarks>
/// The base address differs by environment and neither value is the intuitive one.
/// In development the .NET API runs on the host while jbg-ai runs in Compose, so the
/// API only sees the published port (8001). In production both containers live on the
/// same host and the address is the container name, which requires the user-defined
/// Docker network that C17 must create: on the default bridge network Docker does not
/// resolve container names.
/// </remarks>
public class AiGatewayOptions
{
    /// <summary>Configuration section name.</summary>
    public const string SectionName = "AiGateway";

    /// <summary>Minimum secret length accepted for HS256 signing.</summary>
    public const int MinimumSecretLength = 32;

    /// <summary>Base address of the jbg-ai service. Must be an absolute URI.</summary>
    public string BaseUrl { get; set; } = string.Empty;

    /// <summary>
    /// HS256 secret shared with jbg-ai. Must match the service's JWT_SECRET literally:
    /// any divergence produces a 401 whose cause the service is required not to disclose.
    /// Distinct from Jwt:SecretKey, which signs user tokens.
    /// </summary>
    public string JwtSecret { get; set; } = string.Empty;

    /// <summary>Lifetime of the internal service token, in seconds.</summary>
    public int TokenTtlSeconds { get; set; } = 300;

    /// <summary>Time budget for a retrieval call, in milliseconds.</summary>
    /// <remarks>
    /// <para>
    /// The design specifies 800 ms (§6.4). Raised to 2500 ms during C16 because measurement
    /// against the seeded world with real retrieval showed the assisted path degrading on
    /// <em>every</em> search at 800 ms: the AI service builds its embedding client per request,
    /// so the in-memory cache never hits and each search pays a full cold round trip to the
    /// embedding provider.
    /// </para>
    /// <para>
    /// <strong>Temporary.</strong> When that client becomes a singleton — the change that already
    /// works inside the retrieval package — measure again and put this back to 800 ms. A budget
    /// this loose stops protecting the search from a slow provider, and with the single retry it
    /// turns the worst case into roughly five seconds of an operator waiting for a degraded
    /// answer.
    /// </para>
    /// </remarks>
    public int RetrievalTimeoutMs { get; set; } = 2500;

    /// <summary>
    /// Floor of <see cref="AssistTimeoutMs"/>, validated at start-up.
    /// </summary>
    /// <remarks>
    /// The worst case jbg-ai declares for the provider calls of one sale assistance, with its
    /// default configuration: <c>MAX_PITCH_PROVIDER_CALLS × PITCH_TIMEOUT_SECONDS = 2 × 4 s</c>
    /// (<c>ai-service/src/jbg_ai/assist/constants.py</c>). If either constant moves on the Python
    /// side, this one moves with it.
    /// </remarks>
    public const int MinimumAssistTimeoutMs = 8000;

    /// <summary>
    /// Time budget for a sale assistance call on the <c>ai-assist</c> client, in milliseconds.
    /// </summary>
    /// <remarks>
    /// <para>
    /// 10 s, raised from the 5 s C03 reserved before anything used it. The outer budget must be
    /// at least the worst case the service declares inside, or this side discards answers the
    /// service was still entitled to deliver — already degraded, still useful — and falls back to
    /// its own degradation, which carries less. Measured on the C30b pass, 7.5 % of requests at
    /// the width served spent more than 5 s in provider calls alone.
    /// </para>
    /// <para>
    /// 2 × 4 s plus the reads of the piece, its family and the corpus come to about 8.5 s; the
    /// rest is network margin. It may be lowered, never below <see cref="MinimumAssistTimeoutMs"/>,
    /// which start-up refuses.
    /// </para>
    /// <para>
    /// Measured end to end on 2026-09-22 (C34 implementation report, §4): 80 requests, M2 and M3,
    /// through Docker Compose with the real provider — p50 4.4 s, p95 7.1 s, maximum 7.9 s, none
    /// above 8 s. The maximum sits at the floor, so the budget was <em>not</em> lowered.
    /// </para>
    /// </remarks>
    public int AssistTimeoutMs { get; set; } = 10_000;

    /// <summary>
    /// Floor of <see cref="AgentTimeoutMs"/>, validated at start-up.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>The service's own wall-clock ceiling for one agent request</strong>:
    /// <c>AGENT_DEADLINE_SECONDS = 15 s</c>
    /// (<c>ai-service/src/jbg_ai/assist/constants.py</c>). Exceeding that deadline is, on the
    /// Python side, a <em>degradation and not a failure</em> — the evidence gathered so far is
    /// served and the response says the clock stopped it — so an outer budget below it would throw
    /// away an answer the service was about to deliver, and replace something useful with nothing.
    /// </para>
    /// <para>
    /// If the constant moves on the Python side, this one moves with it.
    /// </para>
    /// </remarks>
    public const int MinimumAgentTimeoutMs = 15_000;

    /// <summary>
    /// Time budget for a sale agent call on the <c>ai-agent</c> client, in milliseconds.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>Above the service's ceiling plus network margin, and deliberately not fitted to the
    /// maximum observed.</strong> 18 s: the 15 s the service allows itself plus 3 s for the hop. The
    /// maximum measured over 204 requests against the real provider was 11 917 ms on the model that
    /// is served — so 15 s would already look generous — and that is precisely the reasoning to
    /// resist. Cutting at the observed maximum has an expensive failure mode: it aborts a request
    /// <strong>Python has already paid for in full</strong>, provider calls included, and hands the
    /// counter nothing for the money.
    /// </para>
    /// <para>
    /// <strong>Not <see cref="AssistTimeoutMs"/>, and that is the point of a client of its own.</strong>
    /// The agent's median latency, 5 311 ms, is of the order of the <em>total</em> the generative
    /// route declares as its ceiling; a client carrying the 10 s generative budget would cut a large
    /// share of agent requests. And the budgets are per feature rather than per request, so sharing
    /// one would also share a circuit: a slow conversation would open the breaker of a route that is
    /// answering correctly.
    /// </para>
    /// <para>
    /// It may be lowered, never below <see cref="MinimumAgentTimeoutMs"/>, which start-up refuses.
    /// </para>
    /// </remarks>
    public int AgentTimeoutMs { get; set; } = 18_000;

    /// <summary>
    /// Time budget for a catalog enrichment batch, in milliseconds.
    /// </summary>
    /// <remarks>
    /// Two orders of magnitude above the retrieval budget, and that is the point: a batch of up
    /// to fifty products through a structured-extraction model has nothing in common with a
    /// vector lookup. Nobody is waiting on this call the way an operator waits on a search — it
    /// is an administration action — so the budget is generous enough that a slow provider does
    /// not turn into a half-enriched catalog.
    /// </remarks>
    public int EnrichTimeoutMs { get; set; } = 120_000;

    /// <summary>
    /// Time budget for the health probe, in milliseconds.
    /// </summary>
    /// <remarks>
    /// Short on purpose, and short for a different reason than retrieval's budget. A human is
    /// waiting on this one: it backs a status card an administrator opens when something looks
    /// wrong. "The AI service did not answer in two seconds" is a useful diagnosis; thirty
    /// seconds of a spinner is not. It is enforced by the client's own timeout because the
    /// health client carries no resilience pipeline to race with.
    /// </remarks>
    public int HealthTimeoutMs { get; set; } = 2000;

    /// <summary>Whether the gateway client is registered at all.</summary>
    public bool Enabled { get; set; } = true;

    /// <summary>Failure ratio that opens the circuit breaker.</summary>
    public double BreakerFailureRatio { get; set; } = 0.5;

    /// <summary>Minimum number of calls in the sampling window before the breaker can open.</summary>
    public int BreakerMinimumThroughput { get; set; } = 4;

    /// <summary>Sampling window of the circuit breaker, in seconds.</summary>
    public int BreakerSamplingDurationSeconds { get; set; } = 30;

    /// <summary>How long the circuit stays open before probing again, in seconds.</summary>
    public int BreakerBreakDurationSeconds { get; set; } = 15;
}
