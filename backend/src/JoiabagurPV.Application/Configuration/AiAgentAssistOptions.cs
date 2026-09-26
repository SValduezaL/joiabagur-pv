namespace JoiabagurPV.Application.Configuration;

/// <summary>
/// Configuration for the sale agent endpoint (C42): the conversation panel, on its own switch and
/// its own allowance. Bound from the "AiAgentAssist" section, read through <c>IOptionsMonitor</c>
/// and validated at start-up.
/// </summary>
/// <remarks>
/// <para>
/// <strong>Its own section, and the reason is the one that gave the free query its own.</strong>
/// A rate limit is an attribute of an endpoint in ASP.NET, and this endpoint's cost profile is
/// unlike any other's: measured over 204 requests against the real provider, ~13 000 prompt tokens
/// per request against a quota of 25 000 tokens per minute means the system admits about
/// <strong>one request per minute</strong>. Folding it into the free query's allowance would let a
/// burst of conversations exhaust a quota the cheaper route needs, and the operator would have no
/// way to know why.
/// </para>
/// <para>
/// <strong>And its own switch, which is what the availability probe exists to report.</strong> The
/// agent has a credential chain of its own on the service side — agent, then assist, then the
/// shared key — so a deployment can have the assisted answer configured and the agent not. A probe
/// that derived the agent's verdict from the assisted one would state that the agent is available
/// while every agent request came back degraded, which is the shape of failure the probe was
/// created to remove.
/// </para>
/// <para>
/// <strong>Off by default, and here that is more than symmetry with its siblings.</strong> This
/// route is measured as costing several times the deterministic one and withholding its argument
/// six times more often, so it is a demonstration and a comparison rather than the way a counter
/// works by default. Enabling a shop is an explicit act.
/// </para>
/// <para>
/// The page ceiling is deliberately <em>not</em> repeated here: the panel draws pages the size the
/// free query draws them, and a second pair of numbers would let two sibling panels disagree after
/// a configuration change. Nothing here is a secret; the gateway credentials belong to
/// <see cref="AiGatewayOptions"/>, and the time budget to <c>AgentTimeoutMs</c> on it.
/// </para>
/// </remarks>
public class AiAgentAssistOptions
{
    /// <summary>Configuration section name.</summary>
    public const string SectionName = "AiAgentAssist";

    /// <summary>
    /// Whether points of sale absent from <see cref="EnabledPointOfSaleIds"/> may use the agent.
    /// </summary>
    public bool EnabledByDefault { get; set; }

    /// <summary>Points of sale where the agent is offered, by identifier.</summary>
    public List<Guid> EnabledPointOfSaleIds { get; set; } = [];

    /// <summary>
    /// Agent turns one user may issue inside <see cref="RateLimitWindowSeconds"/>.
    /// </summary>
    /// <remarks>
    /// Four, and the figure comes from the quota rather than from taste: at about one request per
    /// minute of token budget, an allowance the operator could actually exhaust would only move the
    /// refusal from this side to the provider's, where it arrives as an opaque failure instead of a
    /// number the screen can state beforehand.
    /// </remarks>
    public int RateLimitPermitLimit { get; set; } = 4;

    /// <summary>Length of the rate-limiting window, in seconds.</summary>
    public int RateLimitWindowSeconds { get; set; } = 60;

    /// <summary>
    /// Families requested from the AI service, the over-retrieval dial rather than a page size.
    /// </summary>
    /// <remarks>
    /// Five, as the free query asks for, which is what the frozen contract caps <c>top_k</c> at for
    /// the assist family of routes.
    /// </remarks>
    public int CandidateWindow { get; set; } = 5;

    /// <summary>Whether the agent is offered for a given point of sale.</summary>
    public bool IsEnabledFor(Guid pointOfSaleId) =>
        EnabledByDefault || EnabledPointOfSaleIds.Contains(pointOfSaleId);
}
