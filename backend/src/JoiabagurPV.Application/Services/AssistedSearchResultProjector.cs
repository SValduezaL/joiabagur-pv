using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Interfaces.Services;
using JoiabagurPV.Domain.Interfaces.Repositories;
using Microsoft.Extensions.Logging;

namespace JoiabagurPV.Application.Services;

/// <summary>
/// Turns one hydrated catalog row plus the index signals that explain its match into the result
/// the screen shows.
/// </summary>
/// <remarks>
/// <para>
/// Extracted from <see cref="AssistedSearchService"/> when C40 added a second consumer, and not
/// duplicated into it. What lives here is the rule about <strong>where each field comes from</strong>,
/// which is the one thing in this projection that is easy to get wrong and impossible to notice:
/// price, stock, SKU, name and photo are the catalog's, while score, materials, match reasons,
/// family and variant label are the index's. A second copy would drift the first time somebody
/// fixed one of the two.
/// </para>
/// <para>
/// It also carries the index-drift warning, for the same reason: a divergence between what the
/// index reports and what the catalog holds is worth knowing about and is never worth failing a
/// search over, and that judgement should be made once.
/// </para>
/// </remarks>
public interface IAssistedSearchResultProjector
{
    /// <summary>
    /// Projects one row. <paramref name="candidate"/> is null on any path where no retriever
    /// ran, and then the index signals are empty rather than invented.
    /// </summary>
    Task<AssistedSearchResultDto> ProjectAsync(AssistedSearchRow row, AiSearchResult? candidate);
}

/// <inheritdoc/>
public class AssistedSearchResultProjector : IAssistedSearchResultProjector
{
    private readonly IFileStorageService _fileStorage;
    private readonly ITraceContextAccessor _traceContext;
    private readonly ILogger<AssistedSearchResultProjector> _logger;

    public AssistedSearchResultProjector(
        IFileStorageService fileStorage,
        ITraceContextAccessor traceContext,
        ILogger<AssistedSearchResultProjector> logger)
    {
        _fileStorage = fileStorage;
        _traceContext = traceContext;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<AssistedSearchResultDto> ProjectAsync(
        AssistedSearchRow row,
        AiSearchResult? candidate)
    {
        if (candidate is not null && !string.Equals(candidate.Sku, row.Sku, StringComparison.Ordinal))
        {
            // The catalog wins. A divergence means the index is behind, which is worth knowing
            // about and is not worth failing a search over.
            _logger.LogWarning(
                "Assisted search found index drift: the index reports SKU {IndexedSku} for product {ProductId}, the catalog holds {CatalogSku}. TraceId={TraceId}",
                candidate.Sku,
                row.ProductId,
                row.Sku,
                _traceContext.CurrentTraceId);
        }

        return new AssistedSearchResultDto
        {
            ProductId = row.ProductId,
            Sku = row.Sku,
            Name = row.Name,
            Price = row.Price,
            QuantityAtPointOfSale = row.Quantity,
            // `row.Quantity > 0` would be **false** for a null, which reads as «none left»
            // rather than «nobody asked». The two have to stay apart all the way to the screen.
            HasStock = row.Quantity is { } quantity ? quantity > 0 : null,
            PrimaryPhotoUrl = row.PrimaryPhotoFileName is null
                ? null
                : await _fileStorage.GetUrlAsync(row.PrimaryPhotoFileName, "products"),
            CollectionName = row.CollectionName,
            Score = candidate?.Score,
            // From the candidate, never from hydration: these are index signals that explain the
            // match, not catalog truth. Empty wherever no retriever ran.
            Materials = candidate?.Materials ?? [],
            MatchReasons = candidate?.MatchReasons ?? [],
            FamilyId = candidate?.FamilyId,
            VariantLabel = candidate?.VariantLabel
        };
    }
}
