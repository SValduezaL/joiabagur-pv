using JoiabagurPV.Domain.Enums;

namespace JoiabagurPV.Domain.Interfaces.Repositories;

/// <summary>Keyset reads for the indexing feeds. Implementation lives in Infrastructure.</summary>
public interface IIndexFeedRepository
{
    /// <summary>
    /// Catalog page in keyset order. <paramref name="includeNonIndexable"/> is true on an
    /// incremental pull so tombstones of deactivated or unapproved profiles can surface;
    /// a full sync (no cursor) asks for indexable rows only.
    /// </summary>
    /// <param name="take">Page size plus one, so the caller can set <c>hasMore</c>.</param>
    Task<IReadOnlyList<CatalogFeedRow>> GetCatalogPageAsync(
        DateTime? since,
        Guid? sinceId,
        int take,
        bool includeNonIndexable,
        CancellationToken cancellationToken);

    /// <summary>Every currently indexable product identifier, for the aggregate hash.</summary>
    Task<IReadOnlyList<Guid>> GetIndexableProductIdsAsync(CancellationToken cancellationToken);

    /// <summary>POS page in keyset order on <c>(watermark, Inventory.Id)</c>.</summary>
    Task<IReadOnlyList<PosFeedRow>> GetPosPageAsync(
        DateTime? since,
        Guid? sinceId,
        int take,
        CancellationToken cancellationToken);

    /// <summary>Active assignment pairs, for the POS aggregate hash.</summary>
    Task<IReadOnlyList<PosAssignmentPair>> GetActiveAssignmentPairsAsync(
        CancellationToken cancellationToken);

    /// <summary>
    /// Every point of sale with its activity, in one reading. No keyset and no page (C43).
    /// </summary>
    /// <remarks>
    /// Reads <c>PointOfSales</c>, which the POS availability query never touches — it
    /// projects from <c>Inventories</c> — and that absence is precisely why the AI side had
    /// no way to know whether a shop was still trading.
    /// </remarks>
    Task<IReadOnlyList<PosShopRow>> GetPosShopsAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Sales aggregates for the pairs on the current page. Sums <c>Sale.Quantity</c> only —
    /// no join to <c>Return</c>.
    /// </summary>
    Task<IReadOnlyList<PosSalesAggregate>> GetSalesAggregatesAsync(
        IReadOnlyList<PosAssignmentPair> pairs,
        DateTime now,
        CancellationToken cancellationToken);
}

/// <summary>One catalog row as the feed query projects it.</summary>
public sealed class CatalogFeedRow
{
    public Guid ProductId { get; init; }

    public DateTime Watermark { get; init; }

    public bool IsActive { get; init; }

    public ProfileReviewStatus ReviewStatus { get; init; }

    public string Sku { get; init; } = string.Empty;

    public string Name { get; init; } = string.Empty;

    public string? Description { get; init; }

    public string? CollectionName { get; init; }

    public string? PieceType { get; init; }

    public string MaterialsJson { get; init; } = "[]";

    public string? StoneType { get; init; }

    public string? SizeLabel { get; init; }

    public string ColorTagsJson { get; init; } = "[]";

    public string StyleTagsJson { get; init; } = "[]";

    public string OccasionTagsJson { get; init; } = "[]";

    public Guid? FamilyId { get; init; }

    public string? FamilyName { get; init; }

    public string? VariantLabel { get; init; }

    public decimal Price { get; init; }
}

/// <summary>One inventory row as the POS feed query projects it.</summary>
public sealed class PosFeedRow
{
    public Guid InventoryId { get; init; }

    public Guid PointOfSaleId { get; init; }

    public Guid ProductId { get; init; }

    public DateTime Watermark { get; init; }

    public bool IsActive { get; init; }

    public int Quantity { get; init; }
}

/// <summary>An assigned active <c>(pointOfSaleId, productId)</c> pair.</summary>
public readonly record struct PosAssignmentPair(Guid PointOfSaleId, Guid ProductId);

/// <summary>One point of sale as the shop reading projects it: identity and activity only.</summary>
public readonly record struct PosShopRow(Guid PointOfSaleId, bool IsActive);

/// <summary>Windowed sale sums and last-sale timestamp for one assignment.</summary>
public sealed class PosSalesAggregate
{
    public Guid PointOfSaleId { get; init; }

    public Guid ProductId { get; init; }

    public int Sales30d { get; init; }

    public int Sales90d { get; init; }

    public DateTime? LastSaleAt { get; init; }
}
