namespace JoiabagurPV.Application.Configuration;

/// <summary>
/// Configuration for the free-query search endpoint (C40): the assisted answer the route toggle
/// offers over the same query the semantic path serves. Bound from the "AiFreeQuerySearch"
/// section, read through <c>IOptionsMonitor</c> and validated at start-up.
/// </summary>
/// <remarks>
/// <para>
/// **Its own section, and the reason is mechanical rather than tidy.** Four operational
/// properties already differ from the semantic search this endpoint sits beside: the switch, the
/// request allowance, the time budget and the circuit. A rate limit is an attribute of an
/// endpoint in ASP.NET, so folding the two into one route would force a single allowance —
/// 30/min lets an operator burn thirty generations, 10/min strangles the cheap path — and the
/// budget has the same problem.
/// </para>
/// <para>
/// **And its own allowance rather than the sale card's**, which is the question this section
/// exists to answer: the card is opened once per piece, and the panel is used in bursts. Sharing
/// a quota would leave whichever one an operator reached second unable to work, and the operator
/// would have no way to know why.
/// </para>
/// <para>
/// Nothing here is a secret: the gateway credentials belong to <see cref="AiGatewayOptions"/>.
/// </para>
/// </remarks>
public class AiFreeQuerySearchOptions
{
    /// <summary>Configuration section name.</summary>
    public const string SectionName = "AiFreeQuerySearch";

    /// <summary>
    /// Whether points of sale absent from <see cref="EnabledPointOfSaleIds"/> may use the
    /// assisted answer. Defaults to false, like the other two switches: enabling a shop is an
    /// explicit act.
    /// </summary>
    /// <remarks>
    /// Its absence from every <c>appsettings</c> is what left assisted search serving from its
    /// degraded path for the whole project without anybody noticing, so this one travels with a
    /// note in the start-up documentation rather than only in code.
    /// </remarks>
    public bool EnabledByDefault { get; set; }

    /// <summary>Points of sale where the assisted answer is offered, by identifier.</summary>
    public List<Guid> EnabledPointOfSaleIds { get; set; } = [];

    /// <summary>
    /// Free-query searches one user may issue inside <see cref="RateLimitWindowSeconds"/>.
    /// </summary>
    /// <remarks>
    /// Ten, matching the card's generative route rather than search's thirty, because the cost
    /// profile is the card's: a routing call, a corpus consultation and a generation. The figure
    /// is the one the screen states before the operator presses, so it is part of the interface
    /// and not only of the infrastructure.
    /// </remarks>
    public int RateLimitPermitLimit { get; set; } = 10;

    /// <summary>Length of the rate-limiting window, in seconds.</summary>
    public int RateLimitWindowSeconds { get; set; } = 60;

    /// <summary>
    /// Families requested from the AI service, which is the over-retrieval dial rather than a
    /// page size in the usual sense.
    /// </summary>
    /// <remarks>
    /// Five, which is what the frozen contract caps <c>top_k</c> at for the assist route. Asking
    /// for more is refused by the contract; asking for less leaves the hydrator without margin at
    /// the points of sale that stock a small share of the catalog.
    /// </remarks>
    public int CandidateWindow { get; set; } = 5;

    /// <summary>Groups shown when the caller does not ask for a page size.</summary>
    public int DefaultPageSize { get; set; } = 5;

    /// <summary>Largest page a caller may ask for.</summary>
    public int MaxPageSize { get; set; } = 20;

    /// <summary>Whether the assisted answer is offered for a given point of sale.</summary>
    public bool IsEnabledFor(Guid pointOfSaleId) =>
        EnabledByDefault || EnabledPointOfSaleIds.Contains(pointOfSaleId);

    /// <summary>
    /// The relationships the attributes cannot express, checked at start-up.
    /// </summary>
    /// <remarks>
    /// A default page larger than the maximum is the kind of mistake that produces no error and
    /// simply serves the wrong number of results, which is why it is refused at boot rather than
    /// clamped at request time: a clamp would make the misconfiguration permanent and invisible.
    /// </remarks>
    public IEnumerable<string> Inconsistencies()
    {
        if (DefaultPageSize > MaxPageSize)
        {
            yield return
                $"{nameof(DefaultPageSize)} ({DefaultPageSize}) must not exceed "
                + $"{nameof(MaxPageSize)} ({MaxPageSize}).";
        }

        if (CandidateWindow < DefaultPageSize)
        {
            yield return
                $"{nameof(CandidateWindow)} ({CandidateWindow}) must be at least "
                + $"{nameof(DefaultPageSize)} ({DefaultPageSize}): the window is what the "
                + "hydrator draws a page from, so a smaller one can never fill it.";
        }
    }
}
