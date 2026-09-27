namespace JoiabagurPV.Application.Configuration;

/// <summary>
/// Reads the three per-point-of-sale switches for a <em>scope</em> rather than for a shop: one
/// named point of sale, or every one of them.
/// </summary>
/// <remarks>
/// <para>
/// <strong>Written once so the probe and the route cannot drift.</strong> Availability is answered
/// by <c>AssistedSearchService.GetAvailability</c> and enforced by the search services, and the two
/// have to reach the same verdict for the same scope. When they disagree the screen presents a
/// capability that is off as though it were on — or disables one that works — which is the failure
/// C40 was opened to remove and the one C40_FIX found still reachable one scope along.
/// </para>
/// <para>
/// The rule for an absent point of sale is <see cref="AiFreeQuerySearchOptions.EnabledByDefault"/>
/// and its siblings, and it was already decided in the free-query route: with no shop named there
/// is no per-shop entry to look up, so the default governs. That is the narrow reading and the safe
/// one — <strong>a deployment that enables the feature shop by shop has not enabled it for «all of
/// them»</strong>. Reading it the other way round would spend a generative budget on behalf of
/// shops whose owner deliberately switched the feature off.
/// </para>
/// <para>
/// Extension methods over one shared interface on purpose: the three options classes are
/// independent settings sections with different cost profiles, and giving them a common base type
/// would invite exactly the sharing — one rate limit, one budget, one switch — that they exist to
/// keep apart.
/// </para>
/// </remarks>
public static class AiScopeSwitchExtensions
{
    /// <summary>Whether semantic search is on for a scope: one point of sale, or every one.</summary>
    /// <param name="options">The semantic search settings.</param>
    /// <param name="pointOfSaleId">The shop, or <see langword="null"/> for every one of them.</param>
    public static bool IsEnabledForScope(this AiSearchOptions options, Guid? pointOfSaleId) =>
        pointOfSaleId is { } named ? options.IsEnabledFor(named) : options.EnabledByDefault;

    /// <summary>Whether the free-query route is on for a scope: one point of sale, or every one.</summary>
    /// <param name="options">The free-query settings.</param>
    /// <param name="pointOfSaleId">The shop, or <see langword="null"/> for every one of them.</param>
    public static bool IsEnabledForScope(this AiFreeQuerySearchOptions options, Guid? pointOfSaleId) =>
        pointOfSaleId is { } named ? options.IsEnabledFor(named) : options.EnabledByDefault;

    /// <summary>Whether the sale card's generation is on for a scope: one point of sale, or every one.</summary>
    /// <param name="options">The sale assistance settings.</param>
    /// <param name="pointOfSaleId">The shop, or <see langword="null"/> for every one of them.</param>
    public static bool IsEnabledForScope(this AiSalesAssistOptions options, Guid? pointOfSaleId) =>
        pointOfSaleId is { } named ? options.IsEnabledFor(named) : options.EnabledByDefault;

    /// <summary>Whether the sale agent is on for a scope: one point of sale, or every one.</summary>
    /// <param name="options">The sale agent settings.</param>
    /// <param name="pointOfSaleId">The shop, or <see langword="null"/> for every one of them.</param>
    /// <remarks>
    /// The fourth switch, added by C42, and read by the agent's route and by the availability probe
    /// through this one method for the reason the other three are: two readers of the same switch
    /// that compute it separately are two readers that will disagree. What the probe must
    /// <strong>not</strong> do is derive this verdict from the assisted answer's — the agent has a
    /// credential chain of its own, so the two can be off independently.
    /// </remarks>
    public static bool IsEnabledForScope(this AiAgentAssistOptions options, Guid? pointOfSaleId) =>
        pointOfSaleId is { } named ? options.IsEnabledFor(named) : options.EnabledByDefault;
}
