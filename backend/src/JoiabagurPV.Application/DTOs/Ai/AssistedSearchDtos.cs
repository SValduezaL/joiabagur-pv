namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// What the browser sends to run an assisted search.
/// </summary>
/// <remarks>
/// The point of sale is required rather than inferred. Two already-shipped capabilities force
/// it: the gateway call scope has a single construction path for point-of-sale routes and
/// refuses both a missing and a placeholder value, and the telemetry service demands that same
/// scope — a search with no point of sale could not even be recorded.
/// </remarks>
public class AssistedSearchRequest
{
    /// <summary>Natural-language query typed by the operator.</summary>
    public string Query { get; set; } = string.Empty;

    /// <summary>Point of sale the search is served for.</summary>
    public Guid PointOfSaleId { get; set; }

    /// <summary>How many results to display. Falls back to the configured default.</summary>
    public int? PageSize { get; set; }

    /// <summary>
    /// Identifier of the search episode, so the reformulations of one session group together.
    /// The server generates one when it is absent.
    /// </summary>
    public Guid? SearchSessionId { get; set; }

    /// <summary>Materials the operator selected in the quick filters.</summary>
    public List<string> Materials { get; set; } = [];

    /// <summary>Optional piece category.</summary>
    public string? Category { get; set; }
}

/// <summary>
/// One result as the operator sees it. Price, quantity, photo and collection come from the
/// catalog; identifiers, score and reasons come from the retriever.
/// </summary>
public class AssistedSearchResultDto
{
    /// <summary>Catalog identifier of the product.</summary>
    public Guid ProductId { get; set; }

    /// <summary>SKU as the catalog holds it, never as the index reported it.</summary>
    public string Sku { get; set; } = string.Empty;

    /// <summary>Product name.</summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>Current catalog price.</summary>
    public decimal Price { get; set; }

    /// <summary>Units at the point of sale of the search, not the sum across points of sale.</summary>
    /// <remarks>
    /// <strong>Null and zero are different answers and must stay so.</strong> Zero means the
    /// shop carries none; <see langword="null"/> means no shop was named, so there is nothing
    /// to count — a free query spread over every point of sale. A zero there would assert
    /// something false about a piece that may be sitting in the next shop along.
    /// </remarks>
    public int? QuantityAtPointOfSale { get; set; }

    /// <summary>
    /// False when the product is assigned to this point of sale but has run out.
    /// </summary>
    /// <remarks>
    /// Such a result is kept on purpose: "we carry it, we are out of it" is an answer that can
    /// still save a sale, and suppressing it would turn a useful fact into a silent gap.
    /// </remarks>
    /// <remarks>
    /// <see langword="null"/> with no shop named: whether a piece is in stock is a question
    /// about a shop, and answering false would read as «none left» rather than «nobody asked».
    /// </remarks>
    public bool? HasStock { get; set; }

    /// <summary>URL of the primary photo, when the product has one.</summary>
    public string? PrimaryPhotoUrl { get; set; }

    /// <summary>Collection the product belongs to, when it has one.</summary>
    public string? CollectionName { get; set; }

    /// <summary>Relevance score from the retriever, or null on the degraded path.</summary>
    public double? Score { get; set; }

    /// <summary>Signals that matched, for explaining the result to the operator.</summary>
    public List<string> MatchReasons { get; set; } = [];

    /// <summary>
    /// Materials the retriever recognised for this piece.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>Not hydrated and not authoritative.</strong> These come from the enriched index,
    /// not from the transactional catalog, and they are the same values a caller may filter on.
    /// They exist to explain a match — never to describe stock, price or availability, which
    /// remain the exclusive product of hydration.
    /// </para>
    /// <para>
    /// This is the only explanatory signal available today: <see cref="MatchReasons"/> is a
    /// single constant value for every result until the lexical branch exists, so without this
    /// a caller has nothing with which to tell an operator why a piece was proposed.
    /// </para>
    /// <para>
    /// Empty rather than absent when the retriever reported none, and empty on the degraded and
    /// disabled paths, where no retriever ran.
    /// </para>
    /// </remarks>
    public List<string> Materials { get; set; } = [];

    /// <summary>Family the product belongs to, when the index knows one.</summary>
    public string? FamilyId { get; set; }

    /// <summary>Variant label within the family, when the index knows one.</summary>
    public string? VariantLabel { get; set; }
}

/// <summary>
/// The answer to an assisted search.
/// </summary>
/// <remarks>
/// <see cref="AiAvailable"/> and <see cref="LowConfidence"/> exist to separate the three ways a
/// search can return nothing, which mean different things to the operator and would otherwise be
/// indistinguishable:
/// <list type="bullet">
/// <item>the retriever answered and abstained — available, low confidence;</item>
/// <item>it returned candidates and none survived hydration — available, not low confidence;</item>
/// <item>the assisted path did not serve the search — not available.</item>
/// </list>
/// </remarks>
public class AssistedSearchResponse
{
    /// <summary>Results in the order the retriever ranked them. Never re-sorted.</summary>
    public List<AssistedSearchResultDto> Results { get; set; } = [];

    /// <summary>
    /// Identifier of the recorded search event, so the browser can report the selection against
    /// it. Null when telemetry could not persist, which never fails the search.
    /// </summary>
    public Guid? SearchEventId { get; set; }

    /// <summary>Whether the AI service served this search.</summary>
    public bool AiAvailable { get; set; }

    /// <summary>Whether the retriever abstained because nothing cleared its threshold.</summary>
    public bool LowConfidence { get; set; }

    /// <summary>Point of sale the search was served for.</summary>
    public Guid PointOfSaleId { get; set; }

    /// <summary>Candidates the retriever produced. Zero on the degraded and disabled paths.</summary>
    public int CandidatesReturned { get; set; }

    /// <summary>Candidates that survived hydration at this point of sale.</summary>
    public int SurvivedHydration { get; set; }

    /// <summary>
    /// Codes the retriever emitted about the query itself, from the closed vocabulary the
    /// assisted answer already uses. Today only <c>filters_too_narrow</c>.
    /// </summary>
    /// <remarks>
    /// <strong>A different statement from <see cref="UnappliedFilters"/>, and they must not
    /// be collapsed.</strong> That one names a filter the search could not evaluate at all;
    /// this one says every filter was applied and admitted almost nothing, over a query the
    /// catalogue can answer. The first is a gap in the searcher, the second is a fact about
    /// the operator's own selection, and they end in different actions.
    /// </remarks>
    /// <remarks>
    /// Empty on the degraded and disabled paths, which never reach the retriever.
    /// </remarks>
    public List<string> Warnings { get; set; } = [];

    /// <summary>
    /// Filters the operator selected that this search could not apply at all, so the screen can
    /// say so instead of leaving a control visibly engaged over results that ignore it.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Empty on the assisted path, which honours every filter. On the degraded and disabled paths
    /// it names the ones the lexical searcher has nothing to evaluate against. A category or
    /// material never appears here: those are applied, and a piece whose enriched profile lacks
    /// the field simply fails the filter — that is the filter working, not failing.
    /// </para>
    /// <para>
    /// <strong>It is empty in every case this endpoint can currently produce</strong>, and that is
    /// worth stating rather than leaving to be discovered. The panel's request carries exactly two
    /// filters and the degraded path now applies both, so there is nothing left to declare. The
    /// channel is kept because the requirement is a safety net rather than a feature: the failure
    /// it guards against — a pressed control over results that ignore it — is the one that opened
    /// this change, and it was invisible precisely because there was nowhere to report it. A
    /// filter added later that the catalog cannot answer has a place to say so, and the screen
    /// already knows how to render it.
    /// </para>
    /// </remarks>
    public List<string> UnappliedFilters { get; set; } = [];
}

/// <summary>
/// How an assisted search ended, so the endpoint can map it to a status code without the
/// service knowing about HTTP.
/// </summary>
public enum AssistedSearchOutcome
{
    /// <summary>The search ran.</summary>
    Success = 0,

    /// <summary>The caller may not search on that point of sale.</summary>
    PointOfSaleForbidden = 1,

    /// <summary>The point of sale does not exist or is not active.</summary>
    PointOfSaleUnavailable = 2
}

/// <summary>Result of an assisted search: an outcome and, when it succeeded, a response.</summary>
public sealed record AssistedSearchResult(AssistedSearchOutcome Outcome, AssistedSearchResponse? Response)
{
    /// <summary>The search ran and produced a response.</summary>
    public static AssistedSearchResult Ok(AssistedSearchResponse response) =>
        new(AssistedSearchOutcome.Success, response);

    /// <summary>The caller may not search on that point of sale.</summary>
    public static AssistedSearchResult Forbidden() =>
        new(AssistedSearchOutcome.PointOfSaleForbidden, null);

    /// <summary>The point of sale does not exist or is inactive.</summary>
    public static AssistedSearchResult Unavailable() =>
        new(AssistedSearchOutcome.PointOfSaleUnavailable, null);
}
