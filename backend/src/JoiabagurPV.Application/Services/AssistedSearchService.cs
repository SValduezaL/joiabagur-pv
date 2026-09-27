using System.Diagnostics;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Domain.Interfaces.Services;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Application.Services;

/// <summary>
/// Orchestrates one assisted search: scope, feature switch, retrieval, hydration, truncation,
/// degradation and telemetry.
/// </summary>
public class AssistedSearchService : IAssistedSearchService
{
    private readonly IAiGatewayClient _gateway;
    private readonly IAssistedSearchRepository _repository;
    private readonly IAssistedSearchCandidateCache _cache;
    private readonly IUserPointOfSaleService _userPointOfSaleService;
    private readonly IProductSearchEventService _searchEventService;
    private readonly IFileStorageService _fileStorage;
    private readonly ITraceContextAccessor _traceContext;
    private readonly IOptionsMonitor<AiSearchOptions> _options;
    private readonly IAssistedSearchResultProjector _projector;
    private readonly IOptionsMonitor<AiSalesAssistOptions> _assistOptions;
    private readonly IOptionsMonitor<AiFreeQuerySearchOptions> _freeQueryOptions;
    private readonly IOptionsMonitor<AiAgentAssistOptions> _agentOptions;
    private readonly TimeProvider _timeProvider;
    private readonly ILogger<AssistedSearchService> _logger;

    public AssistedSearchService(
        IAiGatewayClient gateway,
        IAssistedSearchRepository repository,
        IAssistedSearchCandidateCache cache,
        IUserPointOfSaleService userPointOfSaleService,
        IProductSearchEventService searchEventService,
        IFileStorageService fileStorage,
        ITraceContextAccessor traceContext,
        IOptionsMonitor<AiSearchOptions> options,
        IAssistedSearchResultProjector projector,
        IOptionsMonitor<AiSalesAssistOptions> assistOptions,
        IOptionsMonitor<AiFreeQuerySearchOptions> freeQueryOptions,
        IOptionsMonitor<AiAgentAssistOptions> agentOptions,
        TimeProvider timeProvider,
        ILogger<AssistedSearchService> logger)
    {
        _projector = projector;
        _assistOptions = assistOptions;
        _freeQueryOptions = freeQueryOptions;
        _agentOptions = agentOptions;
        _gateway = gateway;
        _repository = repository;
        _cache = cache;
        _userPointOfSaleService = userPointOfSaleService;
        _searchEventService = searchEventService;
        _fileStorage = fileStorage;
        _traceContext = traceContext;
        _options = options;
        _timeProvider = timeProvider;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<AssistedSearchResult> SearchAsync(
        AssistedSearchRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default)
    {
        var startedAt = _timeProvider.GetTimestamp();
        var options = _options.CurrentValue;

        var access = await AuthoriseAsync(request.PointOfSaleId, userId, isAdmin, cancellationToken);
        if (access is not null)
        {
            return access;
        }

        // The scope is built once and never rebuilt: it is what carries the point of sale into
        // the service token, and the retriever trusts the token rather than the body.
        var scope = AiCallScope.ForPointOfSale(userId, role, request.PointOfSaleId);
        var filters = BuildFilters(request);
        var pageSize = request.PageSize ?? options.DefaultPageSize;

        var retrieval = options.IsEnabledFor(request.PointOfSaleId)
            ? await RetrieveAsync(request, filters, scope, options, cancellationToken)
            : Retrieval.Disabled();

        IReadOnlyList<AssistedSearchRow> rows;
        if (retrieval.Origin == SearchOrigin.Assisted)
        {
            rows = await HydrateAsync(retrieval.Candidates, request.PointOfSaleId, cancellationToken);
        }
        else
        {
            // The non-assisted paths are timed too, and timed over the same phase: obtaining the
            // candidate list. Leaving this null would make the assisted and degraded populations
            // incomparable, which is the one thing the origin column exists to enable.
            var lexicalStartedAt = _timeProvider.GetTimestamp();

            // Asked for the same window the assisted path uses, not for the page size. What the
            // funnel calls "survived" then means the same thing on both paths — how much of this
            // shop matched — instead of being trivially equal to the displayed count whenever the
            // AI is not answering, which would make the two origins incomparable in exactly the
            // analysis the funnel exists for. The extra rows cost nothing at this catalog size
            // and are truncated away below.
            rows = await DegradedAsync(request, filters, LexicalWindow(options), cancellationToken);
            retrieval = retrieval with { RetrievalMs = ElapsedMs(lexicalStartedAt) };
        }

        var results = await BuildResultsAsync(rows, retrieval, pageSize);

        // Captured before the telemetry call on purpose: recording is work this figure must not
        // include, or the number starts describing the writer instead of the search.
        var totalMs = ElapsedMs(startedAt);

        var searchEventId = await RecordAsync(
            request, scope, filters, results, retrieval, totalMs);

        LogFunnel(request, retrieval, rows.Count, results.Count);

        return AssistedSearchResult.Ok(new AssistedSearchResponse
        {
            Results = results,
            SearchEventId = searchEventId,
            AiAvailable = retrieval.Origin == SearchOrigin.Assisted,
            LowConfidence = retrieval.LowConfidence,
            PointOfSaleId = request.PointOfSaleId,
            CandidatesReturned = retrieval.Candidates.Count,
            SurvivedHydration = rows.Count,
            // Passed through, never recomputed: the decision behind it needed the unfiltered
            // probe of the retriever, which this side has no way of taking.
            Warnings = [.. retrieval.Warnings],
            // Only the degraded and disabled paths can leave a filter unapplied. The assisted
            // path hands every filter to the retriever, which honours all of them.
            UnappliedFilters = retrieval.Origin == SearchOrigin.Assisted
                ? []
                : UnappliedFilters(filters)
        });
    }

    /// <inheritdoc/>
    /// <remarks>
    /// Reads switches and calls nothing.
    ///
    /// The generative flag requires <strong>both</strong> the free-query endpoint's own switch and
    /// the sale card's. <strong>That is stricter than the route it describes, and knowingly so
    /// since the independent verification of C40_FIX measured it.</strong> The first switch is the
    /// one <c>FreeQuerySearchService</c> actually enforces; the second belongs to
    /// <c>SalesAssistService</c> and is <em>not</em> read anywhere on the free-query path — the
    /// gateway writes prose for a free query with the sale card switched off, verified over HTTP.
    /// So with the free query on and the card off this reports <c>switched_off</c> for a scope the
    /// route serves, which the panel turns into a disabled option and, in the every-shop scope,
    /// into a dead end with a false reason. Kept as it stands rather than loosened here, because
    /// which side is wrong is a product decision: see <c>openspec/DEFERRED_TASKS.md</c> and
    /// <c>AiScopePredicateAgreementTests</c>, which pins the present answer.
    /// </remarks>
    public AiSearchAvailabilityResponse GetAvailability(Guid? pointOfSaleId)
    {
        // The shared predicate in all three, so that what this reports and what each route
        // enforces cannot drift. With no shop named the deployment default governs — the narrow
        // reading, already decided by the free-query route: enabling the feature shop by shop has
        // not enabled it for «all of them». See AiScopeSwitchExtensions.
        var assistedAnswer =
            _freeQueryOptions.CurrentValue.IsEnabledForScope(pointOfSaleId)
            && _assistOptions.CurrentValue.IsEnabledForScope(pointOfSaleId);

        // **The agent's own switch, read through the same shared predicate and NOT derived from
        // the verdict above.** The agent has a credential chain of its own on the service side —
        // agent, then assist, then the shared key — so a deployment can have the assisted answer
        // configured and the agent not. Reporting one for the other would tell the screen the agent
        // is available while every agent request came back degraded: exactly the failure this route
        // was created to remove, and the reason the third path is reported rather than inferred.
        var agent = _agentOptions.CurrentValue.IsEnabledForScope(pointOfSaleId);

        return new AiSearchAvailabilityResponse
        {
            PointOfSaleId = pointOfSaleId,

            // Reported with its own predicate even for the wider scope, which the fast route does
            // not serve. **This describes a switch, not reachability.** Answering false here would
            // state that semantic search is switched off, which is a different fact and a false
            // one; that the fast route cannot serve this scope is the panel's to say, and it says
            // it in its own words.
            SemanticSearchAvailable = _options.CurrentValue.IsEnabledForScope(pointOfSaleId),
            AssistedAnswerAvailable = assistedAnswer,

            // Only the switch can be known without calling. An outage or a rejected credential is
            // discovered by making a call, and making one here would defeat the purpose.
            AssistedAnswerUnavailableReason = assistedAnswer ? null : "switched_off",

            AgentAvailable = agent,
            AgentUnavailableReason = agent ? null : "switched_off"
        };
    }

    /// <summary>
    /// Checks that the caller may search on this point of sale, and that it is usable at all.
    /// </summary>
    /// <remarks>
    /// The assignment check has no administrator exception of its own, so the exception is
    /// granted here, explicitly and only for active points of sale. Without it an administrator
    /// could not run the feature at all, since administrators hold no assignments.
    /// </remarks>
    private async Task<AssistedSearchResult?> AuthoriseAsync(
        Guid pointOfSaleId,
        Guid userId,
        bool isAdmin,
        CancellationToken cancellationToken)
    {
        if (!await _repository.IsPointOfSaleActiveAsync(pointOfSaleId, cancellationToken))
        {
            return AssistedSearchResult.Unavailable();
        }

        if (isAdmin)
        {
            return null;
        }

        return await _userPointOfSaleService.HasAccessAsync(userId, pointOfSaleId)
            ? null
            : AssistedSearchResult.Forbidden();
    }

    /// <summary>
    /// Asks the AI service for the largest candidate window the frozen contract can produce, in
    /// a single call, or serves it from the cache.
    /// </summary>
    /// <remarks>
    /// There is deliberately no second call when few candidates survive hydration. The retriever
    /// applies its distance threshold before its row limit, so a result set smaller than the
    /// over-retrieval count means the threshold was the binding constraint — asking again with a
    /// larger window returns the same rows and charges a second query embedding. And the window
    /// configured here already saturates the over-retrieval cap, so there is no larger window to
    /// ask for.
    /// </remarks>
    private async Task<Retrieval> RetrieveAsync(
        AssistedSearchRequest request,
        AiSearchFilters filters,
        AiCallScope scope,
        AiSearchOptions options,
        CancellationToken cancellationToken)
    {
        var window = Math.Clamp(options.CandidateWindow, 1, AiSearchRequest.MaxTopK);
        var key = _cache.BuildKey(request.PointOfSaleId, request.Query, filters, window);
        var startedAt = _timeProvider.GetTimestamp();

        if (_cache.TryGet(key, out var cached) && cached is not null)
        {
            return Retrieval.Assisted(cached, ElapsedMs(startedAt));
        }

        try
        {
            var response = await _gateway.SearchAsync(
                new AiSearchRequest
                {
                    Query = request.Query,
                    TopK = window,
                    Filters = filters,
                    Mode = AiRetrievalMode.Hybrid
                },
                scope,
                cancellationToken);

            _cache.Set(key, response);
            return Retrieval.Assisted(response, ElapsedMs(startedAt));
        }
        catch (AiGatewayConfigurationException exception)
        {
            // Error level, not warning: the search still works, which is exactly why a wrong
            // secret would otherwise sit unnoticed behind a page that looks fine.
            _logger.LogError(
                exception,
                "Assisted search degraded: the AI service rejected the gateway credentials. TraceId={TraceId}",
                _traceContext.CurrentTraceId);

            return Retrieval.Degraded();
        }
        catch (AiNotImplementedException exception)
        {
            _logger.LogError(
                exception,
                "Assisted search degraded: the retrieval route is not implemented on the AI service. TraceId={TraceId}",
                _traceContext.CurrentTraceId);

            return Retrieval.Degraded();
        }
        catch (AiUnavailableException exception)
        {
            _logger.LogWarning(
                exception,
                "Assisted search degraded: the AI service is unavailable. TraceId={TraceId}",
                _traceContext.CurrentTraceId);

            return Retrieval.Degraded();
        }
        catch (AiGatewayException exception)
        {
            // Final clause over the abstract base, so the guarantee is structural rather than
            // enumerative. The three cases above cover every subclass that exists today; this
            // one is what keeps "the search never fails because of the AI" true the day a later
            // change adds a fourth, which would otherwise escape and break the search.
            _logger.LogError(
                exception,
                "Assisted search degraded: unclassified gateway failure of type {FailureType}. TraceId={TraceId}",
                exception.GetType().Name,
                _traceContext.CurrentTraceId);

            return Retrieval.Degraded();
        }
    }

    /// <summary>
    /// Applies the truth: what this point of sale actually carries, at the price and quantity the
    /// catalog holds right now.
    /// </summary>
    private async Task<IReadOnlyList<AssistedSearchRow>> HydrateAsync(
        IReadOnlyList<AiSearchResult> candidates,
        Guid pointOfSaleId,
        CancellationToken cancellationToken)
    {
        if (candidates.Count == 0)
        {
            return [];
        }

        var ids = new List<Guid>(candidates.Count);
        foreach (var candidate in candidates)
        {
            if (Guid.TryParse(candidate.ProductId, out var id))
            {
                ids.Add(id);
            }
            else
            {
                _logger.LogWarning(
                    "Assisted search dropped a candidate whose product identifier is not a GUID. Sku={Sku} TraceId={TraceId}",
                    candidate.Sku,
                    _traceContext.CurrentTraceId);
            }
        }

        return await _repository.HydrateAsync(ids, pointOfSaleId, cancellationToken);
    }

    /// <summary>
    /// The degraded path. Splits the query into terms so that matching any of them is enough.
    /// </summary>
    private async Task<IReadOnlyList<AssistedSearchRow>> DegradedAsync(
        AssistedSearchRequest request,
        AiSearchFilters filters,
        int take,
        CancellationToken cancellationToken)
    {
        var terms = Tokenize(request.Query);
        if (terms.Count == 0)
        {
            return [];
        }

        return await _repository.SearchLexicalAsync(
            terms, request.PointOfSaleId, ToDomainFilters(filters), take, cancellationToken);
    }

    /// <summary>
    /// Maps the gateway's filter shape to the one the catalog understands.
    /// </summary>
    /// <remarks>
    /// The two are kept apart on purpose. <see cref="AiSearchFilters"/> is the body of a frozen
    /// external contract and carries fields that only the vector index can answer; the domain
    /// type carries the two the transactional catalog can. Mapping in one place is what makes
    /// <see cref="UnappliedFilters"/> computable at all — the fields that fall on the floor here
    /// are exactly the ones the response has to declare.
    /// </remarks>
    private static AssistedSearchFilters ToDomainFilters(AiSearchFilters filters) => new()
    {
        Materials = filters.Materials,
        Category = filters.Category
    };

    /// <summary>
    /// The filters the operator selected that a degraded search cannot honour.
    /// </summary>
    /// <remarks>
    /// Family and exclusion lists are properties of the vector index, so the lexical searcher has
    /// nothing to evaluate them against. Category and materials are <strong>not</strong> listed
    /// here: they are applied, and a piece missing the profile field they read simply fails the
    /// filter, which is the filter working rather than failing.
    ///
    /// This exists so the screen can say so. A control that stays visibly engaged while the
    /// results ignore it is the one failure of this capability that misleads without announcing
    /// itself, and it is the defect that opened this change.
    /// </remarks>
    private static List<string> UnappliedFilters(AiSearchFilters filters)
    {
        var unapplied = new List<string>();

        if (!string.IsNullOrWhiteSpace(filters.FamilyId))
        {
            unapplied.Add(nameof(AiSearchFilters.FamilyId));
        }

        if (filters.ExcludeProductIds.Count > 0)
        {
            unapplied.Add(nameof(AiSearchFilters.ExcludeProductIds));
        }

        return unapplied;
    }

    /// <summary>
    /// Rows the degraded searcher asks for: the same window the assisted path over-retrieves,
    /// so the funnel counts the same thing on both origins.
    /// </summary>
    private static int LexicalWindow(AiSearchOptions options) =>
        AiSearchRequest.OverRetrievalCount(
            Math.Clamp(options.CandidateWindow, 1, AiSearchRequest.MaxTopK));

    /// <summary>
    /// Builds the page: relevance order from the retriever, truth from the catalog, truncated to
    /// what the caller asked for.
    /// </summary>
    private async Task<List<AssistedSearchResultDto>> BuildResultsAsync(
        IReadOnlyList<AssistedSearchRow> rows,
        Retrieval retrieval,
        int pageSize)
    {
        var byId = rows.ToDictionary(row => row.ProductId);

        // On the assisted path the order is the retriever's, and the surviving rows are placed
        // back into it. Re-sorting would make the rank measure this code instead of retrieval
        // quality, which is the number the whole evaluation rests on.
        var ordered = new List<(AssistedSearchRow Row, AiSearchResult? Candidate)>(rows.Count);

        if (retrieval.Origin == SearchOrigin.Assisted)
        {
            foreach (var candidate in retrieval.Candidates)
            {
                if (Guid.TryParse(candidate.ProductId, out var id) && byId.TryGetValue(id, out var row))
                {
                    ordered.Add((row, candidate));
                }
            }
        }
        else
        {
            // The degraded searcher already returned its own relevance order.
            foreach (var row in rows)
            {
                ordered.Add((row, null));
            }
        }

        var page = ordered.Take(pageSize).ToList();
        var results = new List<AssistedSearchResultDto>(page.Count);

        // The projection moved to a collaborator when C40 gave it a second consumer. The rule it
        // carries — price, stock, SKU, name and photo from the catalog; score, materials, match
        // reasons, family and variant from the index — is the one thing here that is easy to get
        // wrong and impossible to notice, so it exists once.
        foreach (var (row, candidate) in page)
        {
            results.Add(await _projector.ProjectAsync(row, candidate));
        }

        return results;
    }

    /// <summary>
    /// Records the search that was just served. Never throws, and a null identifier is a normal
    /// outcome the caller has to tolerate.
    /// </summary>
    private async Task<Guid?> RecordAsync(
        AssistedSearchRequest request,
        AiCallScope scope,
        AiSearchFilters filters,
        IReadOnlyList<AssistedSearchResultDto> results,
        Retrieval retrieval,
        int totalMs)
    {
        // The displayed list, not the candidate window: the operator never saw the positions of
        // the candidates that hydration dropped.
        var displayed = results
            .Select(result => new AiSearchResult
            {
                ProductId = result.ProductId.ToString(),
                Sku = result.Sku,
                Score = result.Score ?? 0,
                MatchReasons = result.MatchReasons,
                FamilyId = result.FamilyId,
                VariantLabel = result.VariantLabel
            })
            .ToList();

        return await _searchEventService.RecordSearchAsync(new RecordSearchRequest
        {
            Scope = scope,
            Query = request.Query,
            Filters = filters,
            DisplayedResults = displayed,
            Origin = retrieval.Origin,
            SearchSessionId = request.SearchSessionId,
            TraceId = _traceContext.CurrentTraceId,
            RetrievalMs = retrieval.RetrievalMs,
            TotalMs = totalMs
        });
    }

    /// <summary>
    /// Emits the funnel, which is how the loss caused by filtering by point of sale after
    /// retrieval becomes measurable.
    /// </summary>
    /// <remarks>
    /// No new column is needed for the baseline: the proportion of searches that do not fill a
    /// page comes from the displayed count and the point of sale that telemetry already stores,
    /// and telling abstention apart from an empty page after hydration comes from joining on the
    /// trace identifier with the retrieval stage logs of the AI service.
    ///
    /// The operator's query is not in here. It is free text that may incidentally carry personal
    /// data, and it stays at debug level.
    /// </remarks>
    private void LogFunnel(
        AssistedSearchRequest request,
        Retrieval retrieval,
        int survived,
        int displayed)
    {
        _logger.LogInformation(
            "Assisted search funnel. PointOfSaleId={PointOfSaleId} Origin={Origin} Candidates={Candidates} Survived={Survived} Displayed={Displayed} LowConfidence={LowConfidence} TraceId={TraceId}",
            request.PointOfSaleId,
            retrieval.Origin,
            retrieval.Candidates.Count,
            survived,
            displayed,
            retrieval.LowConfidence,
            _traceContext.CurrentTraceId);

        _logger.LogDebug(
            "Assisted search query. PointOfSaleId={PointOfSaleId} Query={Query} TraceId={TraceId}",
            request.PointOfSaleId,
            request.Query,
            _traceContext.CurrentTraceId);
    }

    private static AiSearchFilters BuildFilters(AssistedSearchRequest request) => new()
    {
        Materials = request.Materials
            .Where(material => !string.IsNullOrWhiteSpace(material))
            .Select(material => material.Trim())
            .ToList(),
        Category = string.IsNullOrWhiteSpace(request.Category) ? null : request.Category.Trim()
    };

    /// <summary>
    /// Splits the query into search terms.
    /// </summary>
    /// <remarks>
    /// Stop words are deliberately not stripped here. The Spanish text-search configuration
    /// removes them itself when it builds the query, and a second list maintained in this
    /// language would be one more thing to keep in step with the one the database actually
    /// applies — worse than not having it, because it would look authoritative.
    ///
    /// Single characters are dropped, which is a different matter: they survive no dictionary,
    /// carry no signal, and once stemmed would widen the match for free.
    /// </remarks>
    private static List<string> Tokenize(string query)
    {
        if (string.IsNullOrWhiteSpace(query))
        {
            return [];
        }

        return query
            .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            // Single characters carry no signal and would match almost everything once stemmed.
            .Where(term => term.Length > 1)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Take(16)
            .ToList();
    }

    private int ElapsedMs(long startedAt) =>
        (int)_timeProvider.GetElapsedTime(startedAt).TotalMilliseconds;

    /// <summary>
    /// What retrieval produced, whichever path served it.
    /// </summary>
    private sealed record Retrieval(
        SearchOrigin Origin,
        IReadOnlyList<AiSearchResult> Candidates,
        bool LowConfidence,
        int? RetrievalMs,
        IReadOnlyList<string> Warnings)
    {
        public static Retrieval Assisted(AiSearchResponse response, int retrievalMs) =>
            new(
                SearchOrigin.Assisted,
                response.Results,
                response.LowConfidence,
                retrievalMs,
                response.Warnings);

        /// <summary>The AI service was consulted and could not answer.</summary>
        public static Retrieval Degraded() =>
            new(SearchOrigin.LexicalFallback, [], false, null, []);

        /// <summary>The AI service was never consulted, because the feature is switched off.</summary>
        public static Retrieval Disabled() =>
            new(SearchOrigin.Disabled, [], false, null, []);
    }
}
