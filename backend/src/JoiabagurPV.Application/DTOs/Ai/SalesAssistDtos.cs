using System.Text.Json.Serialization;

namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Body of <c>POST /api/ai/products/{productId}/sales-assist</c>.
/// </summary>
/// <remarks>
/// A POST with the question in the body, never a GET with it in the URL. The question is free
/// text written about a customer, and a URL ends up in the proxy's access log, the browser's
/// history and any intermediate cache. A GET is also safe and cacheable by definition, so a
/// prefetch could trigger a paid call.
/// </remarks>
public class SalesAssistRequest
{
    /// <summary>Point of sale the card is served for. Required.</summary>
    public Guid PointOfSaleId { get; set; }

    /// <summary>
    /// The customer's question about the piece, or null for the piece's own argument. When
    /// present it may not be blank and is bounded by the contract's own query limit.
    /// </summary>
    public string? Question { get; set; }
}

/// <summary>
/// Query of <c>GET /api/ai/products/{productId}/substitutes</c>.
/// </summary>
public class SubstitutesRequest
{
    /// <summary>Point of sale the substitutes must be sellable at. Required.</summary>
    public Guid PointOfSaleId { get; set; }

    /// <summary>How many substitutes to return. Falls back to the configured default.</summary>
    public int? PageSize { get; set; }
}

/// <summary>
/// State of the argument in a sale assistance response. Each value says something different to
/// the operator, and painting them as one absence would make the screen lie.
/// </summary>
/// <remarks>
/// Decided in declaration order below, the first that applies winning — except
/// <see cref="Generated"/>, which is what remains. Serialized as the snake_case string, which is
/// a contract with the card of C36: the Spanish copy for each value belongs there.
/// </remarks>
[JsonConverter(typeof(JsonStringEnumConverter<PitchStatus>))]
public enum PitchStatus
{
    /// <summary>The AI path degraded, or the card is switched off for the point of sale.</summary>
    [JsonStringEnumMemberName("ai_unavailable")]
    AiUnavailable,

    /// <summary>The AI service ran no generation (no prompt version): typically no credential.</summary>
    [JsonStringEnumMemberName("not_generated")]
    NotGenerated,

    /// <summary>The AI service ran the generation and withheld the argument itself.</summary>
    [JsonStringEnumMemberName("withheld_by_ai")]
    WithheldByAi,

    /// <summary>No question was asked and the anchored product has no units at the point of sale.</summary>
    [JsonStringEnumMemberName("withheld_out_of_stock")]
    WithheldOutOfStock,

    /// <summary>A placeholder remained after resolution; the raw template never ships.</summary>
    [JsonStringEnumMemberName("withheld_unresolved")]
    WithheldUnresolved,

    /// <summary>The argument is delivered, with price and stock resolved against the anchored product.</summary>
    [JsonStringEnumMemberName("generated")]
    Generated
}

/// <summary>
/// The sale card of one product at one point of sale.
/// </summary>
/// <remarks>
/// No figure in here was written by a model: price, quantity and the stock warnings come from the
/// catalog and the inventory of that point of sale. The AI contributes the grouping, the
/// argument's prose, the citations and its own rule-derived codes.
/// </remarks>
public class SalesAssistResponse
{
    /// <summary>Whether the AI service served this card. False on every degraded path.</summary>
    public bool AiAvailable { get; set; }

    /// <summary>
    /// Why the AI path degraded, from the closed vocabulary the service already computes for its
    /// own log line. Null when the path did not degrade.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Six values: <c>switched_off</c>, <c>credential_rejected</c>, <c>not_implemented</c>,
    /// <c>product_not_indexed</c>, <c>ai_unavailable</c> and <c>unclassified</c>. They were
    /// computed and thrown away before this existed, so a piece added after the last index
    /// synchronisation — a state the next synchronisation fixes by itself — reached the operator
    /// looking exactly like an outage, and only the backend log told them apart.
    /// </para>
    /// <para>
    /// The value is assigned onto this response <strong>before</strong> the log line is written,
    /// and the log line reads it from here. That is what makes "the screen and the log cannot
    /// disagree" a property of the code rather than a promise: there is one value, not two that
    /// have to be kept in step.
    /// </para>
    /// </remarks>
    public string? DegradedReason { get; set; }

    /// <summary>Point of sale the card was served for.</summary>
    public Guid PointOfSaleId { get; set; }

    /// <summary>The anchored product.</summary>
    public Guid ProductId { get; set; }

    /// <summary>
    /// The AI service's intent, passed through (<c>product_pitch</c> without a question). Null on
    /// the degraded path, where no AI answered.
    /// </summary>
    public string? Intent { get; set; }

    /// <summary>
    /// The anchored product's group: its family members the point of sale carries, in the order
    /// the AI service returned them, or in family order on the degraded path.
    /// </summary>
    public List<SalesAssistGroupDto> Groups { get; set; } = [];

    /// <summary>The argument, resolved. Null in every state but <see cref="PitchStatus.Generated"/>.</summary>
    public string? Pitch { get; set; }

    /// <summary>State of the argument.</summary>
    public PitchStatus PitchStatus { get; set; }

    /// <summary>Corpus fragments the argument used, each with its claim scope. Empty when degraded.</summary>
    public List<SalesAssistCitationDto> Citations { get; set; } = [];

    /// <summary>
    /// Warning codes: those of the AI service adjusted to what the point of sale carries, then the
    /// two stock warnings this side computes. Never a sentence.
    /// </summary>
    public List<string> Warnings { get; set; } = [];

    /// <summary>A question back to the operator, when the AI service asked one.</summary>
    public string? ClarificationQuestion { get; set; }

    /// <summary>Version of the prompt the argument was generated with, when one was.</summary>
    public string? PromptVersion { get; set; }

    /// <summary>Correlation identifier, to find this request in both services' logs.</summary>
    public string TraceId { get; set; } = string.Empty;
}

/// <summary>One family, or one product alone, as the card shows it.</summary>
public class SalesAssistGroupDto
{
    /// <summary>Family identifier, or null when the product belongs to none.</summary>
    public string? FamilyId { get; set; }

    /// <summary>Family label, or null.</summary>
    public string? FamilyLabel { get; set; }

    /// <summary>Members the point of sale carries.</summary>
    public List<SalesAssistMemberDto> Members { get; set; } = [];
}

/// <summary>One member of a group, hydrated against the point of sale.</summary>
public class SalesAssistMemberDto
{
    public Guid ProductId { get; set; }

    /// <summary>SKU as the catalog holds it, never as the index reported it.</summary>
    public string Sku { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    /// <summary>What tells this variant from its siblings, when known.</summary>
    public string? VariantLabel { get; set; }

    /// <summary>Current catalog price.</summary>
    public decimal Price { get; set; }

    /// <summary>Units at the point of sale of the request. May be zero.</summary>
    public int QuantityAtPointOfSale { get; set; }

    /// <summary>
    /// False when the point of sale carries the product and has run out. On the anchored member
    /// this is what the card turns into its substitutes block.
    /// </summary>
    public bool HasStock { get; set; }

    public string? PrimaryPhotoUrl { get; set; }

    public string? CollectionName { get; set; }

    /// <summary>Materials from the index, explaining the match. Empty on the degraded path.</summary>
    public List<string> Materials { get; set; } = [];

    /// <summary>Match reasons from the index. Empty on the degraded path.</summary>
    public List<string> MatchReasons { get; set; } = [];

    /// <summary>Whether this is the product the card is anchored to. Exactly one member is.</summary>
    public bool IsAnchor { get; set; }
}

/// <summary>A citation as the card shows it.</summary>
public class SalesAssistCitationDto
{
    /// <summary><c>&lt;document&gt;#&lt;section&gt;</c>.</summary>
    public string CitationId { get; set; } = string.Empty;

    public string DocumentTitle { get; set; } = string.Empty;

    public string SectionTitle { get; set; } = string.Empty;

    /// <summary>material, faq, politica, talla.</summary>
    public string DocType { get; set; } = string.Empty;

    /// <summary>
    /// <c>general</c> for a fact of the world; <c>establecimiento</c> for a commitment of the house,
    /// which is confirmed in store before being passed to a customer.
    /// </summary>
    public string ClaimScope { get; set; } = string.Empty;

    public string Snippet { get; set; } = string.Empty;
}

/// <summary>
/// How a substitutes request ended. Four outcomes that mean four different things, none of them a
/// server error.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter<SubstitutesOutcome>))]
public enum SubstitutesOutcome
{
    /// <summary>At least one substitute with stock at the point of sale.</summary>
    [JsonStringEnumMemberName("ok")]
    Ok,

    /// <summary>The AI service answered and no candidate has stock at the point of sale.</summary>
    [JsonStringEnumMemberName("none_in_stock")]
    NoneInStock,

    /// <summary>
    /// The AI service cannot process the product (HTTP 422): a state of the catalog the next
    /// synchronisation fixes, not an outage.
    /// </summary>
    [JsonStringEnumMemberName("product_not_indexed")]
    ProductNotIndexed,

    /// <summary>The AI service did not answer, failed, or the card is switched off.</summary>
    [JsonStringEnumMemberName("ai_unavailable")]
    AiUnavailable
}

/// <summary>The substitutes of one product that one point of sale can sell today.</summary>
public class SubstitutesResponse
{
    public SubstitutesOutcome Outcome { get; set; }

    /// <summary>Substitutes with stock, in the order the AI service ranked them.</summary>
    public List<SubstituteDto> Results { get; set; } = [];

    /// <summary>Candidates the AI service returned. Zero when it did not answer.</summary>
    public int CandidatesReturned { get; set; }

    /// <summary>Candidates the point of sale carries, with or without stock.</summary>
    public int SurvivedHydration { get; set; }

    public Guid PointOfSaleId { get; set; }

    public string TraceId { get; set; } = string.Empty;
}

/// <summary>One substitute, hydrated against the point of sale. Always has stock.</summary>
public class SubstituteDto
{
    public Guid ProductId { get; set; }

    public string Sku { get; set; } = string.Empty;

    public string Name { get; set; } = string.Empty;

    public string? VariantLabel { get; set; }

    public decimal Price { get; set; }

    public int QuantityAtPointOfSale { get; set; }

    public string? PrimaryPhotoUrl { get; set; }

    public string? CollectionName { get; set; }

    public List<string> Materials { get; set; } = [];

    public List<string> MatchReasons { get; set; } = [];

    /// <summary>Whether the substitute belongs to the same family.</summary>
    public bool FamilyMatch { get; set; }

    /// <summary>Share of materials in common, 0 to 1.</summary>
    public double MaterialOverlap { get; set; }

    /// <summary>Style similarity, 0 to 1.</summary>
    public double StyleSimilarity { get; set; }
}

/// <summary>
/// How a sale card request ended before any AI outcome, so the endpoint can map it to a status
/// code without the service knowing about HTTP.
/// </summary>
public enum SalesCardAccessOutcome
{
    /// <summary>The request is served.</summary>
    Success = 0,

    /// <summary>The caller may not use that point of sale.</summary>
    PointOfSaleForbidden = 1,

    /// <summary>The point of sale does not exist or is not active.</summary>
    PointOfSaleUnavailable = 2,

    /// <summary>The point of sale does not carry the product: unknown, inactive or unassigned there.</summary>
    ProductNotFound = 3
}

/// <summary>Result of a sale assistance request: an outcome and, when served, a response.</summary>
public sealed record SalesAssistResult(SalesCardAccessOutcome Outcome, SalesAssistResponse? Response)
{
    public static SalesAssistResult Ok(SalesAssistResponse response) => new(SalesCardAccessOutcome.Success, response);

    public static SalesAssistResult Refused(SalesCardAccessOutcome outcome) => new(outcome, null);
}

/// <summary>Result of a substitutes request: an outcome and, when served, a response.</summary>
public sealed record SubstitutesResult(SalesCardAccessOutcome Outcome, SubstitutesResponse? Response)
{
    public static SubstitutesResult Ok(SubstitutesResponse response) => new(SalesCardAccessOutcome.Success, response);

    public static SubstitutesResult Refused(SalesCardAccessOutcome outcome) => new(outcome, null);
}
