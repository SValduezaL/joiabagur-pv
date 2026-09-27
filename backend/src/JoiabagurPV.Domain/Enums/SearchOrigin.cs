namespace JoiabagurPV.Domain.Enums;

/// <summary>
/// Where the results shown to the operator actually came from.
/// </summary>
/// <remarks>
/// Values are explicit and stable because this column is read by hand in SQL: the mapping
/// is part of the contract with whoever writes those queries, not an implementation detail
/// that may shift when a member is reordered.
///
/// This is NOT the same concept as the retrieval mode the gateway client requests from
/// <c>jbg-ai</c>. That one describes the strategy used inside the AI service; this one
/// describes whether the AI service answered at all. Conflating them would poison the
/// analysis: a week of open circuit breakers would read as the AI ranking worse, when the
/// AI never ran.
/// </remarks>
public enum SearchOrigin
{
    /// <summary>
    /// Results produced by the AI service.
    /// </summary>
    Assisted = 1,

    /// <summary>
    /// Results produced by the existing lexical searcher, because the AI service was
    /// unavailable and the circuit breaker degraded the request.
    /// </summary>
    LexicalFallback = 2,

    /// <summary>
    /// Results produced without consulting the AI service at all, because assisted search is
    /// switched off for that point of sale.
    /// </summary>
    /// <remarks>
    /// Deliberately not folded into <see cref="LexicalFallback"/>. That value exists to measure
    /// how often the AI service fails; recording a search that never reached it would make a
    /// period with the feature switched off read as a period of repeated failures — the exact
    /// confusion the origin column was introduced to prevent.
    ///
    /// It is also the control arm: with this value, switching the feature on for some points of
    /// sale and not others is a comparison the database can answer.
    /// </remarks>
    Disabled = 3,

    /// <summary>
    /// Results produced by the AI service for a free-text query, with a routing decision, a corpus
    /// consultation and a written argument behind them.
    /// </summary>
    /// <remarks>
    /// Deliberately not folded into <see cref="Assisted"/>, and for the same kind of reason the
    /// third value is not folded into the second. The two are different searches, not two
    /// renderings of one: the semantic path costs a query embedding, and this one costs an
    /// embedding plus a classifier plus a corpus lookup plus a generation, against a budget four
    /// times longer and a rate limit three times tighter. Sharing a value would make the one
    /// comparison this column exists to enable — what the operator gets for that extra cost —
    /// impossible to draw from the table.
    ///
    /// With it, the ablation of the two routes stops being something to demonstrate on screen and
    /// becomes a query: the event already carries the filters, the retrieval and total durations
    /// and the selected rank, so grouping by origin answers it directly.
    ///
    /// And a caution worth keeping next to the value: the operator chooses the route, so the two
    /// populations are selected by whoever chose. This measures an ablation; it is not a
    /// randomised comparison and must not be reported as one.
    /// </remarks>
    AssistedGenerative = 4,

    /// <summary>
    /// Results produced by the sale agent: a conversation over several turns in which a loop chose
    /// which of six tools to use, gathered evidence and had an argument written over it.
    /// </summary>
    /// <remarks>
    /// Deliberately not folded into <see cref="AssistedGenerative"/>, and the reason is the one
    /// that kept the fourth value out of the first. The generative route is one query producing
    /// one set of results: one classification, one retrieval, one generation. This one is a
    /// conversation, and it costs several times as much — up to five turns of a model choosing
    /// tools, each turn paying for the accumulated transcript, before the same generation runs.
    /// Measured over 204 requests against the real provider, its median latency is of the order of
    /// the total the generative route declares as its ceiling.
    ///
    /// Sharing a value would make the comparison this column exists for unanswerable, and that
    /// comparison is the whole reason the agent gets a panel of its own rather than a flag on the
    /// panel beside it: the same question asked in both, and what the operator got for the extra
    /// cost read off the table rather than demonstrated on screen.
    ///
    /// No migration. The column persists this enum by conversion to an integer, so a new member is
    /// a new admissible value and not a schema change — which is what the fourth value already
    /// established.
    ///
    /// The same caution applies twice over: the operator chooses the panel, so this is an ablation
    /// and not a randomised comparison. And the gap the fourth value declared is still here — a
    /// query scoped to every point of sale is not recorded at all, because the event requires a
    /// point of sale. An inherited limitation, declared rather than closed, since closing it does
    /// open a migration.
    /// </remarks>
    AssistedAgent = 5
}
