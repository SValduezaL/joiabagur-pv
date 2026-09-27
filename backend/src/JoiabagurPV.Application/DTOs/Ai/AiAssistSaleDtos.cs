namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Sale assistance request sent to jbg-ai (<c>POST /v1/assist/sale</c>).
/// </summary>
/// <remarks>
/// <para>
/// All three modes are sent from here since C40: a product alone (M2), a product with the
/// operator's question (M3), and a query with no product at all (M1). The client requires
/// **at least** one anchor, matching the contract, and refuses only a request carrying neither.
///
/// M1 was refused until C40, and the reason was sound while it held: the generated argument
/// carried `{{price}}` and `{{stock}}`, which name no product, so with several pieces on the
/// table there was nothing to resolve them against. `assist/v5` stops asking for placeholders
/// in the free-query tasks and a hard cause in the service's integrity gate makes that a
/// guarantee, so there is no longer anything to protect against.
/// </para>
/// <para>
/// The frozen contract accepts an optional <c>pos_id</c> in the body and ignores it, because
/// scope comes from the service token. This model omits it for the same reason
/// <see cref="AiSearchRequest"/> does: serializing a value the service discards would suggest
/// the body carries authority. <c>top_k</c>, <c>locale</c> and <c>context</c> are omitted too
/// and take the contract's defaults — they shape the free-query mode, not an anchored one.
/// </para>
/// </remarks>
public class AiAssistSaleRequest
{
    /// <summary>Longest question the frozen contract accepts in <c>query</c>.</summary>
    public const int MaxQueryLength = 500;

    /// <summary>
    /// The anchored product. Nullable because the contract declares it so; the client refuses to
    /// issue a request without one.
    /// </summary>
    public string? ProductId { get; set; }

    /// <summary>The operator's question, or null when the piece itself is the request.</summary>
    public string? Query { get; set; }

    /// <summary>
    /// Catalog filters for the free-query mode. Empty when the operator selected none.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Non-nullable with a default, which is <see cref="AiSubstitutesRequest"/>'s shape for the
    /// same contract field and for the same reason: the contract declares <c>filters</c> with a
    /// default rather than as nullable, and <c>AiContractSnapshotTests</c> holds the two in
    /// parity. An empty filter set and an absent property mean the same thing to the service,
    /// so sending one costs nothing and keeps the two sibling requests identical in shape.
    /// </para>
    /// <para>
    /// Ignored by the service when a piece is anchored: the anchor already determines what is
    /// retrieved. Sent anyway, because suppressing it here would put a second, undocumented rule
    /// in a client whose job is to carry the request faithfully.
    /// </para>
    /// </remarks>
    public AiSearchFilters Filters { get; set; } = new();
}

/// <summary>
/// Sale assistance response from jbg-ai.
/// </summary>
/// <remarks>
/// Carries identifiers, codes and generated prose — never a price or a quantity, which .NET
/// owns. <see cref="Pitch"/> still holds the <c>{{price}}</c> and <c>{{stock}}</c>
/// placeholders the backend resolves, which is why it must never be logged.
/// </remarks>
public class AiAssistSaleResponse
{
    /// <summary>Correlation identifier echoed by the service.</summary>
    public string TraceId { get; set; } = string.Empty;

    /// <summary>Point-of-sale scope the service applied: always the token claim.</summary>
    public string EffectivePosId { get; set; } = string.Empty;

    /// <summary>Closed vocabulary; <c>product_pitch</c> for a piece with no question.</summary>
    public string Intent { get; set; } = string.Empty;

    /// <summary>
    /// Family-grouped candidates. In the anchored modes, one group: the product's family, or the
    /// product alone.
    /// </summary>
    public List<AiAssistGroup> Groups { get; set; } = [];

    /// <summary>
    /// Generated prose with unresolved placeholders. Empty when no argument is delivered, which
    /// <see cref="PromptVersion"/> tells apart: null means the generation did not run.
    /// </summary>
    public string Pitch { get; set; } = string.Empty;

    /// <summary>Corpus fragments the argument used.</summary>
    public List<AiCitation> Citations { get; set; } = [];

    /// <summary>Rule-derived codes. Never a sentence.</summary>
    public List<string> Warnings { get; set; } = [];

    /// <summary>A question back to the operator, selected from a closed catalogue. Usually null.</summary>
    public string? ClarificationQuestion { get; set; }

    /// <summary>Model usage for the request. Logged for cost, never exposed to the frontend.</summary>
    public AiUsage Usage { get; set; } = new();

    /// <summary>Whether retrieval abstained. Constantly false for a piece with no question.</summary>
    public bool Abstained { get; set; }

    /// <summary>Version of the prompt the generation ran with; null when it did not run.</summary>
    public string? PromptVersion { get; set; }
}

/// <summary>
/// One product family, whose members are the variants the operator can disambiguate.
/// </summary>
public class AiAssistGroup
{
    /// <summary>
    /// Family identifier, or null when the product belongs to none. The contract's invariant is
    /// that null implies exactly one member.
    /// </summary>
    public string? FamilyId { get; set; }

    /// <summary>Family label, or null.</summary>
    public string? FamilyLabel { get; set; }

    /// <summary>Members in the order the service ranked them.</summary>
    public List<AiAssistGroupMember> Members { get; set; } = [];
}

/// <summary>
/// One member of a group. Identifiers and index signals only; price and stock come from hydration.
/// </summary>
public class AiAssistGroupMember
{
    /// <summary>Identifier of the product in the business database.</summary>
    public required string ProductId { get; set; }

    /// <summary>SKU as indexed. The catalog wins when they diverge.</summary>
    public required string Sku { get; set; }

    /// <summary>Variant label within the family, or null when unknown.</summary>
    public string? VariantLabel { get; set; }

    /// <summary>Materials of the piece, as indexed.</summary>
    public List<string> Materials { get; set; } = [];

    /// <summary>Relevance score in the range 0 to 1.</summary>
    public double Score { get; set; }

    /// <summary>Why the retrieval produced this candidate, in its own vocabulary.</summary>
    public List<string> MatchReasons { get; set; } = [];
}

/// <summary>
/// A fragment of the knowledge corpus, with everything needed to present it honestly.
/// </summary>
/// <remarks>
/// <see cref="ClaimScope"/> is not decoration: it separates a fact of the world
/// (<c>general</c>) from a commitment of the house (<c>establecimiento</c>) that is confirmed in
/// store before being passed to a customer. Dropping it anywhere between here and the screen
/// would erase the one distinction the marking mechanism exists for.
/// </remarks>
public class AiCitation
{
    /// <summary><c>&lt;document&gt;#&lt;section&gt;</c>; resolves to a file and a heading in git.</summary>
    public string CitationId { get; set; } = string.Empty;

    /// <summary>Title of the corpus document.</summary>
    public string DocumentTitle { get; set; } = string.Empty;

    /// <summary>Title of the section within it.</summary>
    public string SectionTitle { get; set; } = string.Empty;

    /// <summary>Corpus document type: material, faq, politica, talla.</summary>
    public string DocType { get; set; } = string.Empty;

    /// <summary><c>general</c> or <c>establecimiento</c>.</summary>
    public string ClaimScope { get; set; } = string.Empty;

    /// <summary>Retrieval score in the range 0 to 1.</summary>
    public double Score { get; set; }

    /// <summary>The fragment itself.</summary>
    public string Snippet { get; set; } = string.Empty;

    /// <summary>The piece this claim supports, when the request anchored one.</summary>
    public string? ProductId { get; set; }
}
