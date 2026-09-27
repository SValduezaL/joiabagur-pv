namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// A free-query search: the operator's own words, with no piece on the screen. C40.
/// </summary>
public class FreeQuerySearchRequest
{
    /// <summary>Longest query the frozen contract accepts.</summary>
    public const int MaxQueryLength = 500;

    /// <summary>What the operator typed.</summary>
    public string Query { get; set; } = string.Empty;

    /// <summary>
    /// The shop to answer about, or <see langword="null"/> for every shop at once.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <strong>Null is the absence of a shop and never a wildcard.</strong> It builds
    /// `AiCallScope.ForAllPointsOfSale`, whose token omits the `pos_id` claim, and the service
    /// reads an absent claim as «do not apply the availability prefilter» rather than as «match
    /// everything». A sentinel here would reach the retriever's only hard filter.
    /// </para>
    /// <para>
    /// It costs the response its stock figures, and that is stated rather than papered over:
    /// with no shop no quantity is reported, because reporting zero would assert something
    /// false about every piece in the catalogue.
    /// </para>
    /// </remarks>
    public Guid? PointOfSaleId { get; set; }

    /// <summary>Groups wanted, bounded by the configured maximum.</summary>
    public int? PageSize { get; set; }

    /// <summary>The visit this search belongs to, for telemetry.</summary>
    public Guid? SearchSessionId { get; set; }

    /// <summary>Materials the operator selected in the quick filters.</summary>
    public List<string> Materials { get; set; } = [];

    /// <summary>Optional piece category.</summary>
    public string? Category { get; set; }
}

/// <summary>
/// One family of the assisted answer, with the members this point of sale actually carries.
/// </summary>
/// <remarks>
/// Grouped rather than flat, which is the shape this endpoint is for: the AI service deduplicates
/// by family while keeping the rank — a group takes the position of its best member — and the
/// semantic path cannot do it at all, because its list has no notion of a family.
/// </remarks>
public class FreeQueryGroupDto
{
    /// <summary>Family identifier, or null when the piece belongs to none.</summary>
    public string? FamilyId { get; set; }

    /// <summary>Family label, or null.</summary>
    public string? FamilyLabel { get; set; }

    /// <summary>
    /// Members in the order the AI service ranked them, hydrated against the catalog. Never
    /// re-sorted here: re-sorting would make the rank measure this code instead of retrieval.
    /// </summary>
    public List<AssistedSearchResultDto> Members { get; set; } = [];
}

/// <summary>
/// What one free-query search cost, for an administrator. Never sent to an operator.
/// </summary>
/// <remarks>
/// <strong>Inputs of a cost and never the cost.</strong> Tokens and model, never euros: a tariff
/// written into a screen is wrong the day the provider moves it, and `usage.model` is not a
/// pricing key. Neither the query nor the argument appears here — the funnel is about what the
/// request spent, not about what it said.
/// </remarks>
public class FreeQueryUsageDto
{
    /// <summary>Provider model that generated, when one did.</summary>
    public string? Model { get; set; }

    /// <summary>Prompt tokens reported by the service.</summary>
    public int PromptTokens { get; set; }

    /// <summary>Completion tokens reported by the service.</summary>
    public int CompletionTokens { get; set; }

    /// <summary>Total tokens reported by the service.</summary>
    public int TotalTokens { get; set; }

    /// <summary>Version of the prompt the generation ran with; null when it did not run.</summary>
    public string? PromptVersion { get; set; }

    /// <summary>Milliseconds spent inside the AI service.</summary>
    public int? AiMs { get; set; }

    /// <summary>Milliseconds the whole request took, hydration and telemetry included.</summary>
    public int TotalMs { get; set; }
}

/// <summary>
/// The answer to a free query: what the catalog holds, what the corpus says, and the argument
/// tying the two together.
/// </summary>
/// <remarks>
/// <para>
/// <strong>Sixteen states are reachable here</strong>, and they are combinations of these fields
/// rather than values of any one of them. The screen gets them wrong in the combinations, so the
/// table that enumerates them lives in
/// <c>Documentos/Proyecto Final AIEng/informes/c40-m1-panel-states.md</c> and is the thing to read
/// before changing how any of this is rendered.
/// </para>
/// <para>
/// No figure in here was written by a model: price and stock come from the catalog and the
/// inventory of the point of sale, exactly as on the sale card.
/// </para>
/// </remarks>
public class FreeQuerySearchResponse
{
    /// <summary>Families in the order the service ranked them. Empty on the knowledge route.</summary>
    public List<FreeQueryGroupDto> Groups { get; set; } = [];

    /// <summary>The argument, resolved. Null in every state but <see cref="PitchStatus.Generated"/>.</summary>
    public string? Pitch { get; set; }

    /// <summary>State of the argument.</summary>
    public PitchStatus PitchStatus { get; set; }

    /// <summary>Corpus fragments the argument used, each with its claim scope.</summary>
    public List<SalesAssistCitationDto> Citations { get; set; } = [];

    /// <summary>
    /// Warning codes <strong>about the query</strong>, never about a piece.
    /// </summary>
    /// <remarks>
    /// The partition is by subject and not by list, and it matters because the AI service stacks
    /// both kinds into one array. A warning about a piece — that its family has variants, that it
    /// declares no size — describes the <em>first member of the first group</em> and not the set,
    /// so painting it above a result list would state something false about fourteen other pieces.
    /// A warning about the query — out of domain, not in catalogue, not covered by the
    /// documentation, filters too narrow — describes what was asked, and that is what this list
    /// carries. The card of C36 emits its own warnings for a piece when it is opened.
    /// </remarks>
    public List<string> Warnings { get; set; } = [];

    /// <summary>The question the service asked back, verbatim, when it asked one.</summary>
    /// <remarks>
    /// Rendered exactly as it arrives and never rewritten: the catalogue of questions is closed
    /// and written in code on the service side, precisely so that no model composes the sentence
    /// an operator reads.
    /// </remarks>
    public string? ClarificationQuestion { get; set; }

    /// <summary>
    /// What the router decided about the query, passed through.
    /// </summary>
    /// <remarks>
    /// This is the <strong>only</strong> thing that tells the two no-route states apart, and they
    /// need different copy: <c>in_domain</c> means the classifier ran and contradicted itself, so
    /// asking the operator to rephrase is fair; <c>unclassified</c> means it never ran, and asking
    /// them to rephrase would blame them for an absent credential.
    /// </remarks>
    public string? Intent { get; set; }

    /// <summary>Whether retrieval abstained because nothing cleared its threshold.</summary>
    public bool Abstained { get; set; }

    /// <summary>Whether the AI service served this search.</summary>
    public bool AiAvailable { get; set; }

    /// <summary>Why the AI path degraded, from the closed vocabulary. Null when it did not.</summary>
    public string? DegradedReason { get; set; }

    /// <summary>What the search cost. Null for anyone but an administrator.</summary>
    public FreeQueryUsageDto? Usage { get; set; }

    /// <summary>
    /// Identifier of the recorded search event, so a selection can be attributed. Null when
    /// telemetry could not persist, which never fails the search.
    /// </summary>
    public Guid? SearchEventId { get; set; }

    /// <summary>Point of sale the search was served for, or null for every one of them.</summary>
    public Guid? PointOfSaleId { get; set; }

    /// <summary>Members the AI service proposed, before hydration.</summary>
    public int CandidatesReturned { get; set; }

    /// <summary>Members that survived hydration at this point of sale.</summary>
    public int SurvivedHydration { get; set; }

    /// <summary>Correlation identifier, for an administrator reading the log beside the screen.</summary>
    public string? TraceId { get; set; }
}

/// <summary>How a free-query search ended, so the endpoint can map it without knowing HTTP.</summary>
public enum FreeQuerySearchOutcome
{
    /// <summary>The search ran.</summary>
    Success = 0,

    /// <summary>The caller may not search on that point of sale.</summary>
    PointOfSaleForbidden = 1,

    /// <summary>The point of sale does not exist or is not active.</summary>
    PointOfSaleUnavailable = 2
}

/// <summary>Result of a free-query search: an outcome and, when it succeeded, a response.</summary>
public sealed record FreeQuerySearchResult(
    FreeQuerySearchOutcome Outcome,
    FreeQuerySearchResponse? Response)
{
    public static FreeQuerySearchResult Ok(FreeQuerySearchResponse response) =>
        new(FreeQuerySearchOutcome.Success, response);

    public static FreeQuerySearchResult Forbidden() =>
        new(FreeQuerySearchOutcome.PointOfSaleForbidden, null);

    public static FreeQuerySearchResult Unavailable() =>
        new(FreeQuerySearchOutcome.PointOfSaleUnavailable, null);
}
