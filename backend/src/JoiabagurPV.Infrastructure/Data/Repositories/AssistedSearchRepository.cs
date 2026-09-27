using System.Linq.Expressions;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Domain.Interfaces.Repositories;
using Microsoft.EntityFrameworkCore;

namespace JoiabagurPV.Infrastructure.Data.Repositories;

/// <summary>
/// Set-based reads behind assisted search: hydration of retrieved candidates and the degraded
/// Spanish full-text searcher.
/// </summary>
/// <remarks>
/// Both queries start from <c>Inventory</c> rather than from <c>Product</c>. That is not a
/// stylistic choice: an active inventory record at a point of sale is what makes a product
/// belong to it, so starting there makes the visibility rule the shape of the query instead of
/// a condition someone can forget to add.
/// </remarks>
public class AssistedSearchRepository : IAssistedSearchRepository
{
    /// <summary>
    /// Text-search configuration. The same one the vector index uses for its own lexical column,
    /// so the assisted and degraded populations stay linguistically comparable.
    /// </summary>
    private const string SpanishConfiguration = "spanish";

    private readonly ApplicationDbContext _context;

    public AssistedSearchRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<AssistedSearchRow>> HydrateAsync(
        IReadOnlyList<Guid> productIds,
        Guid? pointOfSaleId,
        CancellationToken cancellationToken)
    {
        if (productIds.Count == 0)
        {
            return [];
        }

        var ids = productIds.Distinct().ToArray();
        var carried = Carried(pointOfSaleId)
            .Where(inventory => ids.Contains(inventory.ProductId));

        // One query for the whole candidate window. Order is not requested here: the caller
        // re-orders by the relevance the retriever produced, which this query knows nothing
        // about.
        if (pointOfSaleId is not null)
        {
            return await carried.Select(ToRow).ToListAsync(cancellationToken);
        }

        // **Grouped, because without a shop the query starts from every inventory row and a
        // product carried by three shops would come back three times** — and `ToDictionary` on
        // the caller's side would throw on the duplicate key. The quantity is dropped rather
        // than summed or picked: a total across shops is not what the label means, and one
        // shop's figure chosen arbitrarily would be worse than saying nothing.
        return await carried
            .GroupBy(inventory => inventory.ProductId)
            .Select(group => new AssistedSearchRow
            {
                ProductId = group.Key,
                Sku = group.First().Product.SKU,
                Name = group.First().Product.Name,
                Price = group.First().Product.Price,
                Quantity = null,
                PrimaryPhotoFileName = group.First().Product.Photos
                    .OrderByDescending(photo => photo.IsPrimary)
                    .ThenBy(photo => photo.DisplayOrder)
                    .Select(photo => photo.FileName)
                    .FirstOrDefault(),
                CollectionName = group.First().Product.Collection == null
                    ? null
                    : group.First().Product.Collection!.Name
            })
            .ToListAsync(cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<AssistedSearchRow>> SearchLexicalAsync(
        IReadOnlyList<string> terms,
        Guid? pointOfSaleId,
        AssistedSearchFilters filters,
        int take,
        CancellationToken cancellationToken)
    {
        if (terms.Count == 0 || take <= 0)
        {
            return [];
        }

        // Terms joined so that matching any of them is enough. Requiring all of them would
        // return an empty list on every natural-language query, which is the defect this
        // searcher exists to avoid.
        //
        // The tolerant conversion is used rather than the strict one: the strict one raises on a
        // stray reserved character, and these terms come from text an operator typed. That would
        // turn the one path still standing when the AI service is down into a server error.
        var tsQuery = string.Join(" OR ", terms);

        // Filtering and ordering happen over the entity graph and the projection comes last, so
        // the full-text expression is composed against columns rather than against an already
        // projected shape.
        // The document expression is written out in both places rather than extracted to a
        // helper: a method call inside an expression tree is not translatable, and EF would
        // refuse the query instead of composing it. The SKU is part of the document so that a
        // degraded search for a code still finds its product, which is the first thing an
        // operator types when nothing else works.
        return await Filtered(Carried(pointOfSaleId), filters)
            .Where(inventory => EF.Functions
                .ToTsVector(
                    SpanishConfiguration,
                    inventory.Product.Name + " " + inventory.Product.SKU + " " +
                    (inventory.Product.Description ?? string.Empty))
                .Matches(EF.Functions.WebSearchToTsQuery(SpanishConfiguration, tsQuery)))
            // Relevance orders; it never excludes. Matching and ranking share the same query so
            // the order is coherent with what the filter admitted.
            .OrderByDescending(inventory => EF.Functions
                .ToTsVector(
                    SpanishConfiguration,
                    inventory.Product.Name + " " + inventory.Product.SKU + " " +
                    (inventory.Product.Description ?? string.Empty))
                .Rank(EF.Functions.WebSearchToTsQuery(SpanishConfiguration, tsQuery)))
            .ThenBy(inventory => inventory.Product.Name)
            .Take(take)
            .Select(ToRow)
            .ToListAsync(cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<bool> IsPointOfSaleActiveAsync(Guid pointOfSaleId, CancellationToken cancellationToken)
    {
        return await _context.PointOfSales
            .AsNoTracking()
            .AnyAsync(pos => pos.Id == pointOfSaleId && pos.IsActive, cancellationToken);
    }

    /// <summary>
    /// What this point of sale carries: active inventory rows of active products.
    /// </summary>
    /// <remarks>
    /// The quantity is deliberately not filtered. A product on the shelf list with none left is
    /// still an answer — "we carry it, we are out of it" can save a sale, and suppressing it
    /// would turn a useful fact into a silent gap.
    /// </remarks>
    /// <param name="pointOfSaleId">
    /// The shop, or <see langword="null"/> for every one of them. A null drops the restriction
    /// from the query rather than matching a wildcard against the column: an absent scope means
    /// the filter is not applied, never that it matches everything, so a caller that failed to
    /// resolve one cannot leak across shops by accident — it just gets the whole catalog, which
    /// is a visibly different answer.
    /// </param>
    private IQueryable<Inventory> Carried(Guid? pointOfSaleId) =>
        _context.Inventories
            .AsNoTracking()
            .Where(inventory =>
                (pointOfSaleId == null || inventory.PointOfSaleId == pointOfSaleId)
                && inventory.IsActive
                && inventory.Product.IsActive);

    /// <summary>
    /// Applies the category and material the operator selected, reading them from the enriched
    /// profile the transactional catalog holds.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Written as existence subqueries rather than as a join so the query keeps starting from
    /// <c>Inventory</c> — the shape that makes the point-of-sale visibility rule structural — and
    /// so a product with no profile row drops out instead of duplicating. There is no navigation
    /// property from <c>Product</c> to its profile, by deliberate design of that entity, so the
    /// correlation is written by hand either way.
    /// </para>
    /// <para>
    /// Both are <strong>hard</strong> filters, because a person pressed them: the rule this
    /// repository serves is that what a human presses filters, and what a rule infers from text
    /// merely degrades the ranking. The cost is stated rather than hidden — piece type is present
    /// on 97.7% of the catalog and materials on 91.5%, so filtering by material removes the 8.5%
    /// whose materials were never extracted. Showing those anyway would mean a pressed control
    /// that does not exclude, which is the failure this capability exists to stop making.
    /// </para>
    /// <para>
    /// Materials match by overlap — carrying <em>any</em> of the selected ones qualifies — which
    /// is what the assisted path's <c>&amp;&amp;</c> against its text array does, so the degraded
    /// and assisted populations stay comparable. <c>?|</c> is the jsonb operator with those exact
    /// semantics over an array of strings.
    /// </para>
    /// </remarks>
    private IQueryable<Inventory> Filtered(IQueryable<Inventory> carried, AssistedSearchFilters filters)
    {
        if (filters.IsEmpty)
        {
            return carried;
        }

        if (!string.IsNullOrWhiteSpace(filters.Category))
        {
            var category = filters.Category;
            carried = carried.Where(inventory => _context.ProductAiProfiles
                .Any(profile => profile.ProductId == inventory.ProductId
                    && profile.PieceType == category));
        }

        if (filters.Materials.Count > 0)
        {
            var materials = filters.Materials.ToArray();
            carried = carried.Where(inventory => _context.ProductAiProfiles
                .Any(profile => profile.ProductId == inventory.ProductId
                    && EF.Functions.JsonExistAny(profile.MaterialsJson, materials)));
        }

        return carried;
    }

    /// <summary>
    /// Projection to the row the application layer consumes. Carries the primary photo's file
    /// name rather than its URL: resolving URLs belongs to the caller, which does it once for
    /// the whole page instead of once per result.
    /// </summary>
    private static readonly Expression<Func<Inventory, AssistedSearchRow>> ToRow =
        inventory => new AssistedSearchRow
        {
            ProductId = inventory.ProductId,
            Sku = inventory.Product.SKU,
            Name = inventory.Product.Name,
            Price = inventory.Product.Price,
            Quantity = inventory.Quantity,
            PrimaryPhotoFileName = inventory.Product.Photos
                .OrderByDescending(photo => photo.IsPrimary)
                .ThenBy(photo => photo.DisplayOrder)
                .Select(photo => photo.FileName)
                .FirstOrDefault(),
            CollectionName = inventory.Product.Collection == null
                ? null
                : inventory.Product.Collection.Name
        };
}
