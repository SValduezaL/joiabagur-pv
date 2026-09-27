namespace JoiabagurPV.Domain.Interfaces.Repositories;

/// <summary>
/// Reads that back assisted search: authoritative hydration of retrieved candidates, and the
/// degraded lexical searcher. Implementation lives in Infrastructure.
/// </summary>
/// <remarks>
/// Both operations are set-based on purpose. Hydrating through the catalog service would resolve
/// inventory and photos one product at a time, which at a full candidate window is two orders of
/// magnitude of round trips inside a request competing with the retrieval time budget.
/// </remarks>
public interface IAssistedSearchRepository
{
    /// <summary>
    /// Hydrates the given candidates against the catalog, keeping only what the point of sale
    /// actually carries.
    /// </summary>
    /// <remarks>
    /// A row comes back only when the product is active and has an active inventory record at
    /// <paramref name="pointOfSaleId"/>. A quantity of zero is kept: availability weights a
    /// result, it never removes it.
    ///
    /// Order is not meaningful here. The caller re-orders by the relevance the retriever
    /// produced, which this query knows nothing about.
    /// </remarks>
    /// <param name="pointOfSaleId">
    /// The shop, or <see langword="null"/> for a search spread over every one of them. With a
    /// null the inventory restriction is dropped and each product comes back once, with no
    /// quantity: there is no shop whose units it would be, and reporting one shop's figure for a
    /// product carried by three would be picking an answer at random.
    /// </param>
    Task<IReadOnlyList<AssistedSearchRow>> HydrateAsync(
        IReadOnlyList<Guid> productIds,
        Guid? pointOfSaleId,
        CancellationToken cancellationToken);

    /// <summary>
    /// Degraded searcher: Spanish full-text over the catalog, scoped to one point of sale,
    /// ordered by lexical relevance and restricted by the filters the operator selected.
    /// </summary>
    /// <param name="terms">
    /// Query terms already split and sanitised. They are combined so that matching <em>any</em>
    /// of them is enough — a natural-language query never appears verbatim in a product name,
    /// and requiring all terms would return an empty list on every degraded search.
    /// </param>
    /// <param name="pointOfSaleId">
    /// The shop to answer about, or <see langword="null"/> to search every point of sale. Null is
    /// not a wildcard reaching a filter: it removes the restriction from the query, so a caller
    /// that forgets to resolve a scope gets the whole catalog rather than a silently empty one.
    /// </param>
    /// <param name="filters">
    /// What the operator selected. Applied as exclusions, exactly as the assisted path applies
    /// them — a filter someone pressed is a decision, not an inference.
    /// </param>
    Task<IReadOnlyList<AssistedSearchRow>> SearchLexicalAsync(
        IReadOnlyList<string> terms,
        Guid? pointOfSaleId,
        AssistedSearchFilters filters,
        int take,
        CancellationToken cancellationToken);

    /// <summary>Whether a point of sale exists and is active.</summary>
    Task<bool> IsPointOfSaleActiveAsync(Guid pointOfSaleId, CancellationToken cancellationToken);
}

/// <summary>
/// The catalog filters a degraded search applies, expressed in the terms the domain owns.
/// </summary>
/// <remarks>
/// <para>
/// This exists rather than reusing the application-layer filter DTO because the dependency only
/// runs one way: <c>Domain</c> references no project, and <c>Infrastructure</c> — where the query
/// that consumes this lives — references <c>Domain</c> alone. Handing the repository the DTO the
/// AI gateway serialises would invert that, and would also tie the degraded searcher to the shape
/// of a frozen external contract it has no business knowing about. The application layer maps one
/// to the other in the single place it builds them.
/// </para>
/// <para>
/// It carries only the two the transactional catalog can answer. Family and exclusion lists are
/// properties of the vector index, not of <c>ProductAiProfiles</c>, so declaring them here would
/// promise a filter this searcher cannot apply — the exact failure this whole capability is
/// being changed to stop making.
/// </para>
/// </remarks>
public sealed class AssistedSearchFilters
{
    /// <summary>Nothing selected: the degraded search behaves as it always did.</summary>
    public static readonly AssistedSearchFilters None = new();

    /// <summary>
    /// Materials the operator selected. Matching is an overlap — a result carrying <em>any</em>
    /// of them qualifies — which is what the assisted path does, so the two stay comparable.
    /// </summary>
    public IReadOnlyList<string> Materials { get; init; } = [];

    /// <summary>The piece category the operator selected, when there is one.</summary>
    public string? Category { get; init; }

    /// <summary>Whether anything at all was selected.</summary>
    public bool IsEmpty => Materials.Count == 0 && string.IsNullOrWhiteSpace(Category);
}

/// <summary>
/// One hydrated product at one point of sale, as the queries project it. Carries the file name
/// of the primary photo rather than its URL: resolving URLs is the caller's job and happens in
/// one pass over the whole page.
/// </summary>
public sealed class AssistedSearchRow
{
    public Guid ProductId { get; init; }

    public string Sku { get; init; } = string.Empty;

    public string Name { get; init; } = string.Empty;

    public decimal Price { get; init; }

    /// <summary>
    /// Units at the point of sale of the search. May be zero.
    /// </summary>
    /// <remarks>
    /// When the search was not scoped to a point of sale there is no single shop to count
    /// against, and this carries the units of whichever inventory row matched. It is therefore
    /// <strong>not</strong> a stock figure in that case and must not be presented as one: the
    /// screen says a shop has to be chosen instead of showing a number that would be true of one
    /// shop and false of the others.
    /// </remarks>
    /// <remarks>
    /// <see langword="null"/> when the hydration named no point of sale: there is no shop whose
    /// units these would be. Distinct from zero, which is a shop that carries none.
    /// </remarks>
    public int? Quantity { get; init; }

    public string? PrimaryPhotoFileName { get; init; }

    public string? CollectionName { get; init; }
}
