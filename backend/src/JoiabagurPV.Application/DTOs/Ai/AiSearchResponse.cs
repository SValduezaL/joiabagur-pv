namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Catalog retrieval response from jbg-ai.
/// </summary>
/// <remarks>
/// <see cref="Results"/> holds every candidate the service produced, which is more than
/// the requested page size by design: the service over-fetches so the caller has margin
/// after hydrating and discarding. Truncating to the requested page size is the caller's
/// job, not this client's.
/// </remarks>
public class AiSearchResponse
{
    /// <summary>Candidates ordered by relevance.</summary>
    public List<AiSearchResult> Results { get; set; } = [];

    /// <summary>How many candidates the retriever produced.</summary>
    public int CandidatesReturned { get; set; }

    /// <summary>
    /// True when nothing cleared the confidence threshold. An empty result set with this
    /// flag set is a valid answer, not a failure.
    /// </summary>
    public bool LowConfidence { get; set; }

    /// <summary>
    /// Codes of the closed vocabulary that describe the QUERY rather than a piece. Today
    /// only <c>filters_too_narrow</c>: the query is answerable and the caller's own
    /// catalog-side filters are what left almost nothing.
    /// </summary>
    /// <remarks>
    /// Decided by retrieval and not by the assistance layer, because it needs the unfiltered
    /// abstention probe and the probe lives there. Carried here rather than recomputed so the
    /// semantic route and the assisted one cannot say different things about one search.
    /// </remarks>
    public List<string> Warnings { get; set; } = [];

    /// <summary>Correlation identifier echoed by the service.</summary>
    public string TraceId { get; set; } = string.Empty;

    /// <summary>
    /// Point-of-sale scope the service actually applied — always the token claim,
    /// never a body value.
    /// </summary>
    public string EffectivePosId { get; set; } = string.Empty;
}
