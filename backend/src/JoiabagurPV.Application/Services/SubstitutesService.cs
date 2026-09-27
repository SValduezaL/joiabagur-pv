using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Domain.Interfaces.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Application.Services;

/// <summary>
/// Orchestrates one substitutes request: scope, product check, switch, one call for the largest
/// window, hydration, exclusion of what the shop cannot sell today, the page and the funnel.
/// </summary>
/// <remarks>
/// Excluding a candidate without stock here does not contradict assisted search, which keeps it.
/// A search result the shop has run out of still informs a sale; a substitute is asked for
/// precisely to sell something now in place of a product that cannot be sold. The exclusion was
/// withdrawn from the AI service by C26 so that it would live here, with the stock.
/// </remarks>
public class SubstitutesService : ISubstitutesService
{
    /// <summary>Why a substitute is wanted, as log data for the AI service.</summary>
    public const string OutOfStockReason = "sin_stock";

    private readonly IAiGatewayClient _gateway;
    private readonly IAssistedSearchRepository _repository;
    private readonly IUserPointOfSaleService _userPointOfSaleService;
    private readonly IFileStorageService _fileStorage;
    private readonly ITraceContextAccessor _traceContext;
    private readonly IOptionsMonitor<AiSalesAssistOptions> _options;
    private readonly TimeProvider _timeProvider;
    private readonly ILogger<SubstitutesService> _logger;

    public SubstitutesService(
        IAiGatewayClient gateway,
        IAssistedSearchRepository repository,
        IUserPointOfSaleService userPointOfSaleService,
        IFileStorageService fileStorage,
        ITraceContextAccessor traceContext,
        IOptionsMonitor<AiSalesAssistOptions> options,
        TimeProvider timeProvider,
        ILogger<SubstitutesService> logger)
    {
        _gateway = gateway;
        _repository = repository;
        _userPointOfSaleService = userPointOfSaleService;
        _fileStorage = fileStorage;
        _traceContext = traceContext;
        _options = options;
        _timeProvider = timeProvider;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<SubstitutesResult> GetSubstitutesAsync(
        Guid productId,
        SubstitutesRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default)
    {
        var options = _options.CurrentValue;
        var pointOfSaleId = request.PointOfSaleId;
        var pageSize = request.PageSize ?? options.SubstitutesDefaultPageSize;

        var (access, anchor) = await SalesCardAccess.ResolveAsync(
            _repository, _userPointOfSaleService, productId, pointOfSaleId, userId, isAdmin, cancellationToken);

        if (access != SalesCardAccessOutcome.Success)
        {
            return SubstitutesResult.Refused(access);
        }

        var funnel = new Funnel();
        AiSubstitutesResponse? ai = null;
        SubstitutesOutcome? failure = null;
        string? reason = null;

        if (!options.IsEnabledFor(pointOfSaleId))
        {
            failure = SubstitutesOutcome.AiUnavailable;
            reason = "switched_off";
        }
        else
        {
            var startedAt = _timeProvider.GetTimestamp();
            (ai, failure, reason) = await CallAsync(productId, anchor!, userId, role, pointOfSaleId, options, cancellationToken);
            funnel.AiMs = (int)_timeProvider.GetElapsedTime(startedAt).TotalMilliseconds;
        }

        var results = new List<SubstituteDto>();

        if (ai is not null)
        {
            funnel.CandidatesReturned = ai.Results.Count;
            results = await HydrateAsync(ai, productId, pointOfSaleId, pageSize, funnel, cancellationToken);
        }

        var outcome = failure ?? (results.Count > 0 ? SubstitutesOutcome.Ok : SubstitutesOutcome.NoneInStock);

        _logger.LogInformation(
            "stage=substitutes trace_id={TraceId} pos_id={PointOfSaleId} product_id={ProductId} outcome={Outcome} reason={Reason} candidates_returned={CandidatesReturned} carried={Carried} in_stock={InStock} returned={Returned} ai_ms={AiMs}",
            _traceContext.CurrentTraceId,
            pointOfSaleId,
            productId,
            ToWire(outcome),
            reason,
            funnel.CandidatesReturned,
            funnel.Carried,
            funnel.InStock,
            results.Count,
            funnel.AiMs);

        return SubstitutesResult.Ok(new SubstitutesResponse
        {
            Outcome = outcome,
            Results = results,
            CandidatesReturned = funnel.CandidatesReturned,
            SurvivedHydration = funnel.Carried,
            PointOfSaleId = pointOfSaleId,
            TraceId = _traceContext.CurrentTraceId
        });
    }

    /// <summary>
    /// One call, with the largest window the contract allows, and never a second one: a short page
    /// is an answer, and the window already saturates the over-retrieval cap.
    /// </summary>
    private async Task<(AiSubstitutesResponse? Response, SubstitutesOutcome? Failure, string? Reason)> CallAsync(
        Guid productId,
        AssistedSearchRow anchor,
        Guid userId,
        string role,
        Guid pointOfSaleId,
        AiSalesAssistOptions options,
        CancellationToken cancellationToken)
    {
        var traceId = _traceContext.CurrentTraceId;

        try
        {
            var response = await _gateway.SubstitutesAsync(
                new AiSubstitutesRequest
                {
                    ProductId = productId.ToString(),
                    TopK = Math.Clamp(options.SubstitutesCandidateWindow, 1, AiSubstitutesRequest.MaxTopK),
                    // Log data for the AI service, not a filter: it ranks the same either way.
                    Reason = anchor.Quantity == 0 ? OutOfStockReason : null
                },
                AiCallScope.ForPointOfSale(userId, role, pointOfSaleId),
                cancellationToken);

            return (response, null, null);
        }
        catch (AiRequestRejectedException exception)
        {
            // A state of the catalog the next synchronisation fixes. Reported as such, never as an
            // outage: the two call for different things from whoever reads the screen.
            _logger.LogWarning(exception,
                "Substitutes: reason=product_not_indexed, the AI service cannot process product {ProductId}. TraceId={TraceId}",
                productId, traceId);
            return (null, SubstitutesOutcome.ProductNotIndexed, "product_not_indexed");
        }
        catch (AiGatewayConfigurationException exception)
        {
            _logger.LogError(exception,
                "Substitutes degraded: the AI service rejected the gateway credentials. TraceId={TraceId}", traceId);
            return (null, SubstitutesOutcome.AiUnavailable, "credential_rejected");
        }
        catch (AiNotImplementedException exception)
        {
            _logger.LogError(exception,
                "Substitutes degraded: the route is not implemented on the AI service. TraceId={TraceId}", traceId);
            return (null, SubstitutesOutcome.AiUnavailable, "not_implemented");
        }
        catch (AiUnavailableException exception)
        {
            _logger.LogWarning(exception,
                "Substitutes degraded: the AI service is unavailable. TraceId={TraceId}", traceId);
            return (null, SubstitutesOutcome.AiUnavailable, "ai_unavailable");
        }
        catch (AiGatewayException exception)
        {
            _logger.LogError(exception,
                "Substitutes degraded: unclassified gateway failure of type {FailureType}. TraceId={TraceId}",
                exception.GetType().Name, traceId);
            return (null, SubstitutesOutcome.AiUnavailable, "unclassified");
        }
    }

    /// <summary>
    /// One hydration of the whole window; only what this shop carries with at least one unit, in
    /// the AI service's order, truncated to the page after filtering.
    /// </summary>
    private async Task<List<SubstituteDto>> HydrateAsync(
        AiSubstitutesResponse ai,
        Guid productId,
        Guid pointOfSaleId,
        int pageSize,
        Funnel funnel,
        CancellationToken cancellationToken)
    {
        var ids = new List<Guid>(ai.Results.Count);
        foreach (var candidate in ai.Results)
        {
            if (!Guid.TryParse(candidate.ProductId, out var id))
            {
                _logger.LogWarning(
                    "Substitutes dropped a candidate whose product identifier is not a GUID. Sku={Sku} TraceId={TraceId}",
                    candidate.Sku, _traceContext.CurrentTraceId);
                continue;
            }

            // A product is never its own substitute.
            if (id != productId)
            {
                ids.Add(id);
            }
        }

        var rows = ids.Count == 0
            ? []
            : await _repository.HydrateAsync(ids.Distinct().ToList(), pointOfSaleId, cancellationToken);

        var byId = rows.ToDictionary(row => row.ProductId);
        funnel.Carried = rows.Count;

        var inStock = new List<(AssistedSearchRow Row, AiSubstituteResult Candidate)>();
        foreach (var candidate in ai.Results)
        {
            if (Guid.TryParse(candidate.ProductId, out var id)
                && id != productId
                && byId.TryGetValue(id, out var row)
                && row.Quantity > 0)
            {
                inStock.Add((row, candidate));
            }
        }

        funnel.InStock = inStock.Count;

        var page = new List<SubstituteDto>(Math.Min(pageSize, inStock.Count));
        foreach (var (row, candidate) in inStock.Take(pageSize))
        {
            page.Add(new SubstituteDto
            {
                ProductId = row.ProductId,
                Sku = row.Sku,
                Name = row.Name,
                VariantLabel = candidate.VariantLabel,
                Price = row.Price,
                // Substitutes are refused without a point of sale — their ranking reads that
                // shop's availability — so the hydration that produced this row named one.
                QuantityAtPointOfSale = row.Quantity
                    ?? throw new InvalidOperationException(
                        "Substitutes hydrated without a point of sale. They are refused without one."),
                PrimaryPhotoUrl = row.PrimaryPhotoFileName is null
                    ? null
                    : await _fileStorage.GetUrlAsync(row.PrimaryPhotoFileName, "products"),
                CollectionName = row.CollectionName,
                Materials = candidate.Materials,
                MatchReasons = candidate.MatchReasons,
                FamilyMatch = candidate.SimilaritySignals.FamilyMatch,
                MaterialOverlap = candidate.SimilaritySignals.MaterialOverlap,
                StyleSimilarity = candidate.SimilaritySignals.StyleSimilarity
            });
        }

        return page;
    }

    /// <summary>The wire value of an outcome, so the log counts what the frontend receives.</summary>
    internal static string ToWire(SubstitutesOutcome outcome) => outcome switch
    {
        SubstitutesOutcome.Ok => "ok",
        SubstitutesOutcome.NoneInStock => "none_in_stock",
        SubstitutesOutcome.ProductNotIndexed => "product_not_indexed",
        SubstitutesOutcome.AiUnavailable => "ai_unavailable",
        _ => outcome.ToString()
    };

    /// <summary>The funnel: returned by the AI service → carried here → with stock → returned.</summary>
    private sealed class Funnel
    {
        public int CandidatesReturned { get; set; }

        public int Carried { get; set; }

        public int InStock { get; set; }

        public int? AiMs { get; set; }
    }
}
