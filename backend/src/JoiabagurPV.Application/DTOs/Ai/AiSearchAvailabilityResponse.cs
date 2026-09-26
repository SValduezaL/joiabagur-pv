namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Which assisted paths are switched on for one point of sale, answered without consulting the
/// AI service.
/// </summary>
/// <remarks>
/// <para>
/// This exists because the screen has to state availability <strong>before</strong> a search, and
/// until now there was nowhere to read it from. <c>aiAvailable</c> travels inside a search
/// response, which is to say afterwards, and the health route is an administrator's view of
/// infrastructure rather than of these switches at this shop.
/// </para>
/// <para>
/// The failure it prevents is the one that opened this change: a capability switched off and
/// presented as available. With this, an operator whose shop has the assisted answer disabled
/// sees the option disabled with its reason instead of pressing it and getting an error.
/// </para>
/// <para>
/// Two flags rather than one because the two switches are independent and each carries its own
/// rate limit, time budget and circuit. All four combinations are reachable, including the odd
/// one where semantic search is off and the assisted answer is on.
/// </para>
/// </remarks>
public class AiSearchAvailabilityResponse
{
    /// <summary>
    /// Point of sale the answer is about, or <see langword="null"/> when it is about the scope
    /// covering every one of them.
    /// </summary>
    /// <remarks>
    /// <strong>Null, and never <see cref="Guid.Empty"/>.</strong> An absent point of sale is the
    /// wider scope; a blank identifier names no shop and is refused at the door, exactly as the
    /// free-query route refuses one. Reporting the wider scope as a blank identifier would erase
    /// that distinction on the way back, which is the same wildcard-by-accident C40 spent a whole
    /// group of work closing on the way in.
    /// </remarks>
    public Guid? PointOfSaleId { get; set; }

    /// <summary>
    /// Whether the semantic path is switched on. When false the panel still searches — it
    /// degrades to the lexical searcher, with the filters applied — so this disables nothing on
    /// screen; it explains why the results are what they are.
    /// </summary>
    public bool SemanticSearchAvailable { get; set; }

    /// <summary>
    /// Whether the generative path is switched on. When false the assisted option of the route
    /// toggle is disabled with its reason, rather than failing when pressed.
    /// </summary>
    public bool AssistedAnswerAvailable { get; set; }

    /// <summary>
    /// Why the assisted answer is unavailable, from the same vocabulary the sale card reports, or
    /// null when it is available. Only <c>switched_off</c> can be known before a call: an outage
    /// or a rejected credential is discovered by making one, and this route deliberately makes
    /// none.
    /// </summary>
    public string? AssistedAnswerUnavailableReason { get; set; }

    /// <summary>
    /// Whether the sale agent is switched on. When false the agent's entry card is disabled with its
    /// reason, rather than failing when pressed. C42.
    /// </summary>
    /// <remarks>
    /// <strong>A value of its own, and never derived from <see cref="AssistedAnswerAvailable"/>.</strong>
    /// The agent has a credential chain of its own on the service side, so a deployment can have the
    /// assisted answer configured and the agent not — and a probe that reported one for the other
    /// would state that the agent is available while every agent request came back degraded. That is
    /// the shape of failure this route was created to remove, which is why the third path is reported
    /// rather than inferred.
    /// </remarks>
    public bool AgentAvailable { get; set; }

    /// <summary>
    /// Why the agent is unavailable, or null when it is available.
    /// </summary>
    /// <remarks>
    /// <strong>The agent's own reason and not the assisted answer's</strong>, which the screen needs
    /// separately: the two can be off independently, and showing the assisted answer's reason on the
    /// agent's card would explain the wrong switch. As with its sibling, only <c>switched_off</c> can
    /// be known before a call.
    /// </remarks>
    public string? AgentUnavailableReason { get; set; }
}
