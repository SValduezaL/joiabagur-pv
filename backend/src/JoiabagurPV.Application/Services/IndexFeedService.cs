using System.Text.Json;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Domain.Interfaces.Repositories;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Application.Services;

/// <summary>
/// Builds catalog and POS feed pages: keyset window, upsert/tombstone mapping, and the
/// aggregate hash of the global indexable set.
/// </summary>
public class IndexFeedService : IIndexFeedService
{
    private const int AggregateHashLogPrefixLength = 12;

    private readonly IIndexFeedRepository _repository;
    private readonly TimeProvider _timeProvider;
    private readonly IOptions<IndexFeedOptions> _options;
    private readonly ITraceContextAccessor _traceContext;
    private readonly ILogger<IndexFeedService> _logger;

    public IndexFeedService(
        IIndexFeedRepository repository,
        TimeProvider timeProvider,
        IOptions<IndexFeedOptions> options,
        ITraceContextAccessor traceContext,
        ILogger<IndexFeedService> logger)
    {
        _repository = repository;
        _timeProvider = timeProvider;
        _options = options;
        _traceContext = traceContext;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<IndexFeedPageDto> GetCatalogPageAsync(
        DateTime? since,
        Guid? sinceId,
        CancellationToken cancellationToken)
    {
        var take = IndexFeedPageSizes.Catalog + 1;
        // Full sync (no cursor) is the current indexable set. Tombstones belong on an
        // incremental pull, where a previously indexable row can leave the set. A product
        // that was never approved must not appear as a tombstone on the first page.
        var includeNonIndexable = since.HasValue;

        var rows = await _repository.GetCatalogPageAsync(
            since, sinceId, take, includeNonIndexable, cancellationToken);

        var hasMore = rows.Count > IndexFeedPageSizes.Catalog;
        var page = hasMore ? rows.Take(IndexFeedPageSizes.Catalog).ToList() : rows.ToList();

        var items = page.Select(MapCatalogItem).ToList();
        var ids = await _repository.GetIndexableProductIdsAsync(cancellationToken);
        var aggregateHash = IndexFeedAggregateHash.OfProductIds(ids);

        var dto = new IndexFeedPageDto
        {
            Items = items,
            NextCursor = hasMore ? CursorFrom(page[^1].Watermark, page[^1].ProductId) : null,
            HasMore = hasMore,
            PageSize = IndexFeedPageSizes.Catalog,
            AggregateHash = aggregateHash
        };

        LogPage("catalog", dto);
        return dto;
    }

    /// <inheritdoc/>
    public async Task<PosAvailabilityPageDto> GetPosAvailabilityPageAsync(
        DateTime? since,
        Guid? sinceId,
        CancellationToken cancellationToken)
    {
        var take = IndexFeedPageSizes.PosAvailability + 1;
        var rows = await _repository.GetPosPageAsync(since, sinceId, take, cancellationToken);

        var hasMore = rows.Count > IndexFeedPageSizes.PosAvailability;
        var page = hasMore
            ? rows.Take(IndexFeedPageSizes.PosAvailability).ToList()
            : rows.ToList();

        // Resolved once per page and reported on it, so a client can tell what clock produced
        // the figures without reading this service's configuration. Computed even when the page
        // carries no upsert: the instant is a property of the reading, not of its contents.
        var computedAsOf = _options.Value.SalesAsOfUtc ?? _timeProvider.GetUtcNow().UtcDateTime;

        var upserts = page.Where(row => row.IsActive).ToList();
        var salesByPair = await LoadSalesAsync(upserts, computedAsOf, cancellationToken);

        var items = page.Select(row => MapPosItem(row, salesByPair)).ToList();
        var pairs = await _repository.GetActiveAssignmentPairsAsync(cancellationToken);
        var aggregateHash = IndexFeedAggregateHash.OfPosPairs(
            pairs.Select(pair => (pair.PointOfSaleId, pair.ProductId)));

        var dto = new PosAvailabilityPageDto
        {
            Items = items,
            NextCursor = hasMore ? CursorFrom(page[^1].Watermark, page[^1].InventoryId) : null,
            HasMore = hasMore,
            PageSize = IndexFeedPageSizes.PosAvailability,
            AggregateHash = aggregateHash,
            ComputedAsOf = computedAsOf
        };

        LogPage("pos-availability", dto);
        return dto;
    }

    /// <summary>
    /// Sales aggregates for the page, counted against <paramref name="computedAsOf"/>.
    /// </summary>
    /// <remarks>
    /// The repository has taken the reference instant as a parameter since the feed was built,
    /// so nothing here needed refactoring: the only change is where the value comes from.
    /// </remarks>
    private async Task<Dictionary<(Guid PointOfSaleId, Guid ProductId), PosSalesAggregate>> LoadSalesAsync(
        IReadOnlyList<PosFeedRow> upserts,
        DateTime computedAsOf,
        CancellationToken cancellationToken)
    {
        if (upserts.Count == 0)
        {
            return [];
        }

        var pairs = upserts
            .Select(row => new PosAssignmentPair(row.PointOfSaleId, row.ProductId))
            .ToList();

        var aggregates = await _repository.GetSalesAggregatesAsync(
            pairs, computedAsOf, cancellationToken);

        return aggregates.ToDictionary(row => (row.PointOfSaleId, row.ProductId));
    }

    private static object MapCatalogItem(CatalogFeedRow row)
    {
        var indexable = row.IsActive && row.ReviewStatus == ProfileReviewStatus.Approved;
        if (indexable)
        {
            return new CatalogUpsertItemDto
            {
                ProductId = row.ProductId,
                Sku = row.Sku,
                Name = row.Name,
                Description = row.Description,
                CollectionName = row.CollectionName,
                PieceType = row.PieceType,
                Materials = ParseStringArray(row.MaterialsJson),
                StoneType = row.StoneType,
                SizeLabel = row.SizeLabel,
                FamilyId = row.FamilyId,
                FamilyName = row.FamilyName,
                VariantLabel = row.VariantLabel,
                ColorTags = ParseStringArray(row.ColorTagsJson),
                StyleTags = ParseStringArray(row.StyleTagsJson),
                OccasionTags = ParseStringArray(row.OccasionTagsJson),
                Price = row.Price,
                PriceBand = PriceBand.From(row.Price),
                IsActive = row.IsActive,
                Watermark = row.Watermark
            };
        }

        return new CatalogTombstoneItemDto
        {
            ProductId = row.ProductId,
            Reason = row.IsActive
                ? CatalogTombstoneReasons.Unapproved
                : CatalogTombstoneReasons.Deactivated,
            At = row.Watermark
        };
    }

    private static object MapPosItem(
        PosFeedRow row,
        IReadOnlyDictionary<(Guid PointOfSaleId, Guid ProductId), PosSalesAggregate> sales)
    {
        if (!row.IsActive)
        {
            return new PosAvailabilityTombstoneItemDto
            {
                PointOfSaleId = row.PointOfSaleId,
                ProductId = row.ProductId,
                At = row.Watermark
            };
        }

        sales.TryGetValue((row.PointOfSaleId, row.ProductId), out var aggregate);

        return new PosAvailabilityUpsertItemDto
        {
            PointOfSaleId = row.PointOfSaleId,
            ProductId = row.ProductId,
            QtyBucket = QtyBucket.From(row.Quantity),
            IsAssignedHint = true,
            Sales30d = aggregate?.Sales30d ?? 0,
            Sales90d = aggregate?.Sales90d ?? 0,
            LastSaleAt = aggregate?.LastSaleAt,
            Watermark = row.Watermark
        };
    }

    private static IReadOnlyList<string> ParseStringArray(string json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return [];
        }

        return JsonSerializer.Deserialize<List<string>>(json) ?? [];
    }

    /// <inheritdoc/>
    public async Task<PosShopsReadingDto> GetPosShopsReadingAsync(
        CancellationToken cancellationToken)
    {
        var shops = await _repository.GetPosShopsAsync(cancellationToken);

        // Resolved the same way the availability feed resolves its instant, and reported on
        // the reading rather than per item: every row of one reading was read at one moment,
        // unlike the sales windows next door, which the incremental feed spreads over several.
        var computedAsOf = _options.Value.SalesAsOfUtc ?? _timeProvider.GetUtcNow().UtcDateTime;

        var dto = new PosShopsReadingDto
        {
            Items = shops
                .Select(shop => new PosShopItemDto
                {
                    PointOfSaleId = shop.PointOfSaleId,
                    IsActive = shop.IsActive
                })
                .ToList(),
            ComputedAsOf = computedAsOf
        };

        // The active count is logged and not just the total: it is the number the consumer's
        // health report is about, so a reading that suddenly halves it is visible here.
        _logger.LogInformation(
            "index_feed_reading {Feed} {ItemCount} {ActiveCount} {TraceId}",
            "pos-shops",
            dto.Items.Count,
            dto.Items.Count(item => item.IsActive),
            _traceContext.CurrentTraceId);

        return dto;
    }

    private static IndexFeedCursorDto CursorFrom(DateTime watermark, Guid id) =>
        new() { Since = watermark, SinceId = id };

    private void LogPage(string feed, IndexFeedPageDto page)
    {
        var prefix = page.AggregateHash.Length <= AggregateHashLogPrefixLength
            ? page.AggregateHash
            : page.AggregateHash[..AggregateHashLogPrefixLength];

        _logger.LogInformation(
            "index_feed_page {Feed} {ItemCount} {HasMore} {AggregateHashPrefix} {TraceId}",
            feed,
            page.Items.Count,
            page.HasMore,
            prefix,
            _traceContext.CurrentTraceId);
    }
}
