using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Domain.Interfaces.Repositories;
using Microsoft.EntityFrameworkCore;

namespace JoiabagurPV.Infrastructure.Data.Repositories;

/// <summary>
/// Keyset queries for the indexing feeds. Page sizes come from the caller; this type never
/// reads <c>PaginationConstants</c>.
/// </summary>
public class IndexFeedRepository : IIndexFeedRepository
{
    private readonly ApplicationDbContext _context;

    public IndexFeedRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<CatalogFeedRow>> GetCatalogPageAsync(
        DateTime? since,
        Guid? sinceId,
        int take,
        bool includeNonIndexable,
        CancellationToken cancellationToken)
    {
        var query =
            from product in _context.Products.AsNoTracking()
            join profile in _context.ProductAiProfiles.AsNoTracking()
                on product.Id equals profile.ProductId
            join member in _context.ProductFamilyMembers.AsNoTracking()
                on product.Id equals member.ProductId into memberJoin
            from member in memberJoin.DefaultIfEmpty()
            join family in _context.ProductFamilies.AsNoTracking()
                on member.ProductFamilyId equals family.Id into familyJoin
            from family in familyJoin.DefaultIfEmpty()
            join collection in _context.Collections.AsNoTracking()
                on product.CollectionId equals collection.Id into collectionJoin
            from collection in collectionJoin.DefaultIfEmpty()
            let productProfile = product.UpdatedAt > profile.UpdatedAt
                ? product.UpdatedAt
                : profile.UpdatedAt
            let familyAt = family == null ? productProfile : family.UpdatedAt
            let watermark = productProfile > familyAt ? productProfile : familyAt
            where includeNonIndexable
                  || (product.IsActive && profile.ReviewStatus == ProfileReviewStatus.Approved)
            select new { product, profile, member, family, collection, watermark };

        if (since.HasValue)
        {
            var cursorId = sinceId ?? Guid.Empty;
            var sinceValue = since.Value;
            query = query.Where(row =>
                row.watermark > sinceValue
                || (row.watermark == sinceValue && row.product.Id > cursorId));
        }

        var page = await query
            .OrderBy(row => row.watermark)
            .ThenBy(row => row.product.Id)
            .Take(take)
            .Select(row => new CatalogFeedRow
            {
                ProductId = row.product.Id,
                Watermark = row.watermark,
                IsActive = row.product.IsActive,
                ReviewStatus = row.profile.ReviewStatus,
                Sku = row.product.SKU,
                Name = row.product.Name,
                Description = row.product.Description,
                CollectionName = row.collection == null ? null : row.collection.Name,
                PieceType = row.profile.PieceType,
                MaterialsJson = row.profile.MaterialsJson,
                StoneType = row.profile.StoneType,
                SizeLabel = row.profile.SizeLabel,
                ColorTagsJson = row.profile.ColorTagsJson,
                StyleTagsJson = row.profile.StyleTagsJson,
                OccasionTagsJson = row.profile.OccasionTagsJson,
                FamilyId = row.family == null ? null : row.family.Id,
                FamilyName = row.family == null ? null : row.family.Name,
                VariantLabel = row.member == null ? null : row.member.VariantLabel,
                Price = row.product.Price
            })
            .ToListAsync(cancellationToken);

        return page;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<Guid>> GetIndexableProductIdsAsync(
        CancellationToken cancellationToken)
    {
        return await (
            from product in _context.Products.AsNoTracking()
            join profile in _context.ProductAiProfiles.AsNoTracking()
                on product.Id equals profile.ProductId
            where product.IsActive && profile.ReviewStatus == ProfileReviewStatus.Approved
            orderby product.Id
            select product.Id
        ).ToListAsync(cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<PosFeedRow>> GetPosPageAsync(
        DateTime? since,
        Guid? sinceId,
        int take,
        CancellationToken cancellationToken)
    {
        var query =
            from inventory in _context.Inventories.AsNoTracking()
            let watermark = inventory.LastUpdatedAt > inventory.UpdatedAt
                ? inventory.LastUpdatedAt
                : inventory.UpdatedAt
            select new { inventory, watermark };

        if (since.HasValue)
        {
            var cursorId = sinceId ?? Guid.Empty;
            var sinceValue = since.Value;
            query = query.Where(row =>
                row.watermark > sinceValue
                || (row.watermark == sinceValue && row.inventory.Id > cursorId));
        }

        var page = await query
            .OrderBy(row => row.watermark)
            .ThenBy(row => row.inventory.Id)
            .Take(take)
            .Select(row => new PosFeedRow
            {
                InventoryId = row.inventory.Id,
                PointOfSaleId = row.inventory.PointOfSaleId,
                ProductId = row.inventory.ProductId,
                Watermark = row.watermark,
                IsActive = row.inventory.IsActive,
                Quantity = row.inventory.Quantity
            })
            .ToListAsync(cancellationToken);

        return page;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<PosAssignmentPair>> GetActiveAssignmentPairsAsync(
        CancellationToken cancellationToken)
    {
        var pairs = await _context.Inventories
            .AsNoTracking()
            .Where(inventory => inventory.IsActive)
            .OrderBy(inventory => inventory.PointOfSaleId)
            .ThenBy(inventory => inventory.ProductId)
            .Select(inventory => new PosAssignmentPair(inventory.PointOfSaleId, inventory.ProductId))
            .ToListAsync(cancellationToken);

        return pairs;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<PosShopRow>> GetPosShopsAsync(
        CancellationToken cancellationToken)
    {
        // Every shop, active or not. Filtering to the active ones here would make "closed"
        // and "deleted" the same thing on the wire, and the consumer needs them apart: the
        // first keeps its row and stops being counted, the second loses its row.
        //
        // Ordered by identifier so two readings of an unchanged world are byte-identical,
        // which makes a diff between them mean something.
        var shops = await _context.PointOfSales
            .AsNoTracking()
            .OrderBy(pointOfSale => pointOfSale.Id)
            .Select(pointOfSale => new PosShopRow(pointOfSale.Id, pointOfSale.IsActive))
            .ToListAsync(cancellationToken);

        return shops;
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<PosSalesAggregate>> GetSalesAggregatesAsync(
        IReadOnlyList<PosAssignmentPair> pairs,
        DateTime now,
        CancellationToken cancellationToken)
    {
        if (pairs.Count == 0)
        {
            return [];
        }

        var productIds = pairs.Select(pair => pair.ProductId).Distinct().ToList();
        var posIds = pairs.Select(pair => pair.PointOfSaleId).Distinct().ToList();
        var pairSet = pairs.ToHashSet();
        var since30 = now.AddDays(-30);
        var since90 = now.AddDays(-90);

        var grouped = await _context.Sales
            .AsNoTracking()
            .Where(sale => productIds.Contains(sale.ProductId) && posIds.Contains(sale.PointOfSaleId))
            .GroupBy(sale => new { sale.ProductId, sale.PointOfSaleId })
            .Select(group => new
            {
                group.Key.ProductId,
                group.Key.PointOfSaleId,
                Sales30d = group.Sum(sale =>
                    sale.SaleDate >= since30 && sale.SaleDate <= now ? sale.Quantity : 0),
                Sales90d = group.Sum(sale =>
                    sale.SaleDate >= since90 && sale.SaleDate <= now ? sale.Quantity : 0),
                // Bounded by the reference instant, exactly like the two windows above.
                // Left unbounded it was the one figure on this page that still drifted: a
                // sale recorded after the declared horizon moved it, so the same
                // configuration and seed stopped yielding the same page on different days —
                // and it is a candidate input for the decay the ranking change may use.
                LastSaleAt = group.Max(sale =>
                    sale.SaleDate <= now ? (DateTime?)sale.SaleDate : null)
            })
            .ToListAsync(cancellationToken);

        return grouped
            .Where(row => pairSet.Contains(new PosAssignmentPair(row.PointOfSaleId, row.ProductId)))
            .Select(row => new PosSalesAggregate
            {
                PointOfSaleId = row.PointOfSaleId,
                ProductId = row.ProductId,
                Sales30d = row.Sales30d,
                Sales90d = row.Sales90d,
                LastSaleAt = row.LastSaleAt
            })
            .ToList();
    }
}
