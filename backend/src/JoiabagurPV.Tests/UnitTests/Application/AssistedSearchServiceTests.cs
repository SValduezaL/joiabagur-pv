using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Domain.Interfaces.Services;
using JoiabagurPV.Tests.TestHelpers;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Time.Testing;
using Moq;
using Xunit;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// Unit tests for the assisted-search orchestrator. No AI service, no database: the gateway,
/// the repository and telemetry are all doubles.
/// </summary>
public class AssistedSearchServiceTests
{
    private static readonly Guid UserId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    private static readonly Guid PointOfSaleId = Guid.Parse("22222222-2222-2222-2222-222222222222");
    private static readonly Guid OtherPointOfSaleId = Guid.Parse("33333333-3333-3333-3333-333333333333");

    private readonly Mock<IAiGatewayClient> _gateway = new();
    private readonly Mock<IAssistedSearchRepository> _repository = new();
    private readonly Mock<IUserPointOfSaleService> _userPointOfSale = new();
    private readonly Mock<IProductSearchEventService> _telemetry = new();
    private readonly Mock<IFileStorageService> _fileStorage = new();
    private readonly Mock<ITraceContextAccessor> _traceContext = new();
    private readonly FakeTimeProvider _timeProvider = new();
    private readonly RecordingLoggerProvider _logs = new();

    private readonly AiSearchOptions _options = new()
    {
        EnabledByDefault = true,
        CandidateWindow = 20,
        DefaultPageSize = 10,
        MaxPageSize = 50
    };

    /// <summary>The card's switch, which is the one the availability route reports as the generative path.</summary>
    private readonly AiSalesAssistOptions _assistOptions = new() { EnabledByDefault = true };

    /// <summary>The free-query endpoint's own switch; both must be on for the assisted route.</summary>
    private readonly AiFreeQuerySearchOptions _freeQueryOptions = new() { EnabledByDefault = true };
    private readonly AiAgentAssistOptions _agentOptions = new() { EnabledByDefault = true };

    private readonly List<RecordSearchRequest> _recorded = [];

    public AssistedSearchServiceTests()
    {
        _traceContext.SetupGet(t => t.CurrentTraceId).Returns("trace-1");

        _repository
            .Setup(r => r.IsPointOfSaleActiveAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        _userPointOfSale
            .Setup(u => u.HasAccessAsync(UserId, PointOfSaleId))
            .ReturnsAsync(true);

        _fileStorage
            .Setup(f => f.GetUrlAsync(It.IsAny<string>(), It.IsAny<string>()))
            .ReturnsAsync((string file, string? _) => "https://files.test/" + file);

        _telemetry
            .Setup(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()))
            .Callback<RecordSearchRequest>(_recorded.Add)
            .ReturnsAsync(Guid.NewGuid());
    }

    // ---------------------------------------------------------------- assisted path

    [Fact]
    public async Task Search_HydratesPriceAndStockFromDatabase_NotFromAiResponse()
    {
        var productId = Guid.NewGuid();
        GatewayReturns(Candidate(productId, "SKU-INDEXED", 0.91));
        HydrationReturns(Row(productId, "SKU-CATALOG", price: 42.50m, quantity: 7));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        var hit = result.Response!.Results.Should().ContainSingle().Subject;
        hit.Price.Should().Be(42.50m);
        hit.QuantityAtPointOfSale.Should().Be(7);
        hit.HasStock.Should().BeTrue();

        // The catalog wins over the index, and the divergence is not silent.
        hit.Sku.Should().Be("SKU-CATALOG");
        _logs.Entries.Should().Contain(entry => entry.Message.Contains("index drift"));

        // Identifiers, score and reasons are the only things the AI contributes.
        hit.Score.Should().Be(0.91);
    }

    [Fact]
    public async Task Search_RequestsTheMaximumCandidateWindowInASingleCall()
    {
        GatewayReturns();
        HydrationReturns();

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        _gateway.Verify(
            g => g.SearchAsync(
                It.Is<AiSearchRequest>(r => r.TopK == 20),
                It.IsAny<AiCallScope>(),
                It.IsAny<CancellationToken>()),
            Times.Once);

        // 20 saturates the over-retrieval cap: there is no larger window to ask for.
        AiSearchRequest.OverRetrievalCount(20).Should().Be(AiSearchRequest.OverRetrievalCap);
    }

    [Fact]
    public async Task Search_WhenPosCoverageIsLow_ReturnsFewerThanTopK_WithoutASecondCall()
    {
        // Sixty candidates come back; this shop carries three of them.
        var candidates = Enumerable.Range(0, 60).Select(_ => Candidate(Guid.NewGuid())).ToArray();
        GatewayReturns(candidates);
        HydrationReturns(candidates.Take(3).Select(c => Row(Guid.Parse(c.ProductId), c.Sku)).ToArray());

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Response!.Results.Should().HaveCount(3);
        result.Response.CandidatesReturned.Should().Be(60);
        result.Response.SurvivedHydration.Should().Be(3);

        // A short page is an answer, not a reason to pay for a second embedding.
        _gateway.Verify(
            g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Search_PreservesRetrievalOrder_AndTruncatesToPageSize()
    {
        var ids = Enumerable.Range(0, 5).Select(_ => Guid.NewGuid()).ToArray();
        GatewayReturns(ids.Select(id => Candidate(id)).ToArray());

        // Hydration returns them in a deliberately different order.
        HydrationReturns(ids.Reverse().Select(id => Row(id)).ToArray());

        var request = Request();
        request.PageSize = 3;

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        result.Response!.Results.Select(r => r.ProductId).Should().Equal(ids[0], ids[1], ids[2]);
    }

    [Fact]
    public async Task Search_WhenRetrieverAbstains_ReportsLowConfidenceAndStaysAvailable()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AiSearchResponse { Results = [], CandidatesReturned = 0, LowConfidence = true });

        HydrationReturns();

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Response!.Results.Should().BeEmpty();
        result.Response.AiAvailable.Should().BeTrue();
        result.Response.LowConfidence.Should().BeTrue();
    }

    [Fact]
    public async Task Search_WhenNothingSurvivesHydration_IsNotReportedAsAbstention()
    {
        GatewayReturns(Candidate(Guid.NewGuid()));
        HydrationReturns();

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Response!.Results.Should().BeEmpty();
        result.Response.AiAvailable.Should().BeTrue();

        // Empty for a different reason than abstention, and the caller can tell them apart.
        result.Response.LowConfidence.Should().BeFalse();
        result.Response.CandidatesReturned.Should().Be(1);
        result.Response.SurvivedHydration.Should().Be(0);
    }

    // ---------------------------------------------------------------- hydration rules

    [Fact]
    public async Task Search_KeepsAssignedProductWithZeroStock()
    {
        var productId = Guid.NewGuid();
        GatewayReturns(Candidate(productId));
        HydrationReturns(Row(productId, quantity: 0));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        var hit = result.Response!.Results.Should().ContainSingle().Subject;
        hit.QuantityAtPointOfSale.Should().Be(0);
        hit.HasStock.Should().BeFalse();
    }

    [Fact]
    public async Task Search_WhenCandidateNoLongerAssigned_DropsItAfterHydration()
    {
        var kept = Guid.NewGuid();
        var dropped = Guid.NewGuid();
        GatewayReturns(Candidate(kept), Candidate(dropped));

        // The repository is what enforces assignment: the dropped one simply does not come back.
        HydrationReturns(Row(kept));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Response!.Results.Select(r => r.ProductId).Should().Equal(kept);
    }

    [Fact]
    public async Task Search_HydratesInASingleQuery()
    {
        var candidates = Enumerable.Range(0, 60).Select(_ => Candidate(Guid.NewGuid())).ToArray();
        GatewayReturns(candidates);
        HydrationReturns(candidates.Select(c => Row(Guid.Parse(c.ProductId))).ToArray());

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // One call for the whole window. Per-candidate hydration at this size is two orders of
        // magnitude of round trips inside an 800 ms budget.
        _repository.Verify(
            r => r.HydrateAsync(It.IsAny<IReadOnlyList<Guid>>(), PointOfSaleId, It.IsAny<CancellationToken>()),
            Times.Once);
    }

    // ---------------------------------------------------------------- degradation

    [Theory]
    [InlineData("unavailable")]
    [InlineData("configuration")]
    [InlineData("notimplemented")]
    public async Task Search_WhenAiUnavailable_FallsBackToLexicalSearch(string failure)
    {
        Exception exception = failure switch
        {
            "configuration" => new AiGatewayConfigurationException("bad secret"),
            "notimplemented" => new AiNotImplementedException("not yet"),
            _ => new AiUnavailableException("circuit open")
        };

        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(exception);

        var productId = Guid.NewGuid();
        LexicalReturns(Row(productId));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // The search never fails because of the AI.
        result.Outcome.Should().Be(AssistedSearchOutcome.Success);
        result.Response!.AiAvailable.Should().BeFalse();
        result.Response.Results.Should().ContainSingle();
        _recorded.Should().ContainSingle().Which.Origin.Should().Be(SearchOrigin.LexicalFallback);
    }

    [Fact]
    public async Task Search_WhenCredentialsRejected_LogsAtErrorLevel()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiGatewayConfigurationException("bad secret"));

        LexicalReturns();

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // A working search would otherwise hide a misconfigured secret indefinitely.
        _logs.Entries.Should().Contain(entry => entry.Level == LogLevel.Error);
    }

    [Fact]
    public async Task Fallback_MatchesAnyQueryTerm_NotTheWholeString()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiUnavailableException("circuit open"));

        LexicalReturns();

        var request = Request();
        request.Query = "un anillo de plata para regalar";

        await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        // The query is split into terms and every one of them is passed. Stop words are not
        // stripped here on purpose: the Spanish text-search configuration removes them itself,
        // and a second list maintained in C# would drift from the one the database applies.
        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.Is<IReadOnlyList<string>>(terms =>
                    terms.Count > 1
                    && terms.Contains("anillo") && terms.Contains("plata") && terms.Contains("regalar")),
                PointOfSaleId,
                It.IsAny<AssistedSearchFilters>(),
                It.IsAny<int>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Fallback_DropsSingleCharacterNoise()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiUnavailableException("circuit open"));

        LexicalReturns();

        var request = Request();
        request.Query = "a anillo o plata";

        await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        // One-character tokens carry no signal and, once stemmed, would widen the match for free.
        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.Is<IReadOnlyList<string>>(terms => !terms.Contains("a") && !terms.Contains("o")),
                PointOfSaleId,
                It.IsAny<AssistedSearchFilters>(),
                It.IsAny<int>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Fallback_IsScopedToTheSearchPointOfSale()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiUnavailableException("circuit open"));

        LexicalReturns();

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.IsAny<IReadOnlyList<string>>(),
                PointOfSaleId,
                It.IsAny<AssistedSearchFilters>(),
                It.IsAny<int>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    // ---------------------------------------------------------------- filters on the degraded path

    [Fact]
    public async Task SearchAsync_WhenDegradedAndFilterSelected_AppliesTheFilter()
    {
        GatewayUnavailable();
        LexicalReturns(Row(Guid.NewGuid()));

        var request = Request();
        request.Category = "pendientes";
        request.Materials = ["plata"];

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        result.Response!.AiAvailable.Should().BeFalse("the gateway failed, so this is the degraded path");

        // The defect that opened this change: the chips stayed pressed and the degraded searcher
        // never saw them, so the results ignored a filter the operator had selected and nothing
        // on screen said so.
        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.IsAny<IReadOnlyList<string>>(),
                PointOfSaleId,
                It.Is<AssistedSearchFilters>(filters =>
                    filters.Category == "pendientes"
                    && filters.Materials.Contains("plata")),
                It.IsAny<int>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task SearchAsync_WhenDegradedAndNothingSelected_PassesNoFilter()
    {
        GatewayUnavailable();
        LexicalReturns(Row(Guid.NewGuid()));

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.IsAny<IReadOnlyList<string>>(),
                PointOfSaleId,
                It.Is<AssistedSearchFilters>(filters => filters.IsEmpty),
                It.IsAny<int>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <remarks>
    /// This is the other half of the declaration requirement, and it asserts a negative on
    /// purpose. Both filters the panel can send — category and materials — are now applied on the
    /// degraded path, so neither may be declared unapplied: a piece whose enriched profile lacks
    /// the field fails the filter, and a filter that excludes is a filter working, not failing.
    /// Declaring it would put a warning on screen under results that are in fact correctly
    /// filtered, which is the same class of lie as the silence this change removes.
    ///
    /// The declaration channel itself stays exercised by
    /// <see cref="SearchAsync_WhenAssisted_DeclaresNoUnappliedFilter"/> and is dormant by
    /// construction: see the remarks on the response property for why it is kept.
    /// </remarks>
    [Fact]
    public async Task SearchAsync_WhenDegradedAndFilterIsApplicable_DoesNotDeclareItUnapplied()
    {
        GatewayUnavailable();
        LexicalReturns(Row(Guid.NewGuid()));

        var request = Request();
        request.Category = "pendientes";
        request.Materials = ["plata"];

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        result.Response!.AiAvailable.Should().BeFalse();
        result.Response.UnappliedFilters.Should().BeEmpty();
    }

    [Fact]
    public async Task SearchAsync_WhenAssisted_DeclaresNoUnappliedFilter()
    {
        var productId = Guid.NewGuid();
        GatewayReturns(Candidate(productId));
        HydrationReturns(Row(productId));

        var request = Request();
        request.Category = "pendientes";
        request.Materials = ["plata"];

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        result.Response!.AiAvailable.Should().BeTrue();
        result.Response.UnappliedFilters.Should().BeEmpty(
            "the retriever honours every filter the request carries");
    }

    // ---------------------------------------------------------------- availability, before searching

    [Fact]
    public void Availability_WhenCalled_MakesNoAiCall()
    {
        var availability = CreateService().GetAvailability(PointOfSaleId);

        availability.PointOfSaleId.Should().Be(PointOfSaleId);
        _gateway.VerifyNoOtherCalls();
        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.IsAny<IReadOnlyList<string>>(), It.IsAny<Guid?>(),
                It.IsAny<AssistedSearchFilters>(), It.IsAny<int>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    /// <remarks>
    /// The quota is enforced by the endpoint's rate-limiting policy rather than by this service,
    /// so what is asserted here is the property that makes exemption safe: repeated calls do no
    /// work that could be rationed. If this ever starts calling the gateway, disabling the limit
    /// on the route would become a way to spend the quota without being counted.
    /// </remarks>
    [Fact]
    public void Availability_WhenCalledRepeatedly_ConsumesNoQuota()
    {
        var service = CreateService();

        for (var i = 0; i < 50; i++)
        {
            service.GetAvailability(PointOfSaleId);
        }

        _gateway.VerifyNoOtherCalls();
        _telemetry.VerifyNoOtherCalls();
    }

    [Fact]
    public void Availability_WhenAssistedAnswerIsSwitchedOff_ReportsItWithItsReason()
    {
        _assistOptions.EnabledByDefault = false;

        var availability = CreateService().GetAvailability(PointOfSaleId);

        availability.AssistedAnswerAvailable.Should().BeFalse();
        availability.AssistedAnswerUnavailableReason.Should().Be("switched_off",
            "the toggle disables the option with a reason instead of failing when pressed");
    }

    [Fact]
    public void Availability_WhenBothAreOn_ReportsNoReason()
    {
        var availability = CreateService().GetAvailability(PointOfSaleId);

        availability.SemanticSearchAvailable.Should().BeTrue();
        availability.AssistedAnswerAvailable.Should().BeTrue();
        availability.AssistedAnswerUnavailableReason.Should().BeNull();
    }

    /// <remarks>
    /// The odd quadrant of the four, and reachable: the two switches are independent, so semantic
    /// search can be off while the generative path is on. It is asserted because a screen that
    /// collapsed the two into one badge would render this state wrongly.
    /// </remarks>
    [Fact]
    public void Availability_WhenSemanticIsOffAndAssistedIsOn_ReportsThemSeparately()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [OtherPointOfSaleId];

        var availability = CreateService().GetAvailability(PointOfSaleId);

        availability.SemanticSearchAvailable.Should().BeFalse();
        availability.AssistedAnswerAvailable.Should().BeTrue();
    }

    // ---------------------------------------------------------------- feature switch

    [Fact]
    public async Task Search_WhenFeatureFlagOff_UsesLegacySearch()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [OtherPointOfSaleId];
        LexicalReturns(Row(Guid.NewGuid()));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Response!.AiAvailable.Should().BeFalse();
        result.Response.Results.Should().ContainSingle();

        _gateway.Verify(
            g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task Search_WhenFeatureFlagOff_RecordsOriginDisabled()
    {
        _options.EnabledByDefault = false;
        LexicalReturns();

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // Not LexicalFallback: that value measures how often the AI fails, and a shop with the
        // feature switched off never asked it anything.
        _recorded.Should().ContainSingle().Which.Origin.Should().Be(SearchOrigin.Disabled);
    }

    [Fact]
    public async Task Search_WhenFeatureFlagOn_ForThatPointOfSaleOnly_UsesAssistedPath()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [PointOfSaleId];
        GatewayReturns();
        HydrationReturns();

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Response!.AiAvailable.Should().BeTrue();
    }

    // ---------------------------------------------------------------- telemetry

    [Fact]
    public async Task Search_RecordsTheSearch_WithTheDisplayedListNotTheCandidateWindow()
    {
        var ids = Enumerable.Range(0, 30).Select(_ => Guid.NewGuid()).ToArray();
        GatewayReturns(ids.Select(id => Candidate(id)).ToArray());
        HydrationReturns(ids.Select(id => Row(id)).ToArray());

        var request = Request();
        request.PageSize = 10;

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        // Obligation inherited from the telemetry change: without this call the whole capability
        // is dead code that compiles, passes its tests and arrives empty.
        _telemetry.Verify(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()), Times.Once);

        var recorded = _recorded.Should().ContainSingle().Subject;
        recorded.DisplayedResults.Should().HaveCount(10);
        recorded.Scope.PointOfSaleId.Should().Be(PointOfSaleId);
        recorded.TraceId.Should().Be("trace-1");
        recorded.TotalMs.Should().NotBeNull();
        recorded.RetrievalMs.Should().NotBeNull();
        result.Response!.SearchEventId.Should().NotBeNull();
    }

    [Fact]
    public async Task Search_RecordsRetrievalDuration_OnEveryOrigin()
    {
        _options.EnabledByDefault = false;
        LexicalReturns();

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // Both origins must measure the same phase or they stop being comparable, which is the
        // one thing the origin column exists to enable.
        _recorded.Should().ContainSingle().Which.RetrievalMs.Should().NotBeNull();
    }

    [Fact]
    public async Task Search_WhenTelemetryFails_StillReturnsResults()
    {
        _telemetry
            .Setup(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()))
            .ReturnsAsync((Guid?)null);

        GatewayReturns(Candidate(Guid.NewGuid()));
        HydrationReturns(Row(Guid.NewGuid()));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Outcome.Should().Be(AssistedSearchOutcome.Success);
        result.Response!.SearchEventId.Should().BeNull();
    }

    // ---------------------------------------------------------------- cost

    [Fact]
    public async Task Search_RepeatedQueryHitsCandidateCache_WithoutSecondEmbedding()
    {
        var productId = Guid.NewGuid();
        GatewayReturns(Candidate(productId));
        HydrationReturns(Row(productId));

        var service = CreateService(realCache: true);
        await service.SearchAsync(Request(), UserId, "Operator", isAdmin: false);
        await service.SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        _gateway.Verify(
            g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Once);

        // The ranking is cached; the truth is not. Hydration runs on every request.
        _repository.Verify(
            r => r.HydrateAsync(It.IsAny<IReadOnlyList<Guid>>(), PointOfSaleId, It.IsAny<CancellationToken>()),
            Times.Exactly(2));
    }

    [Fact]
    public void Search_CandidateCacheIsBoundedByTheConfiguredSize()
    {
        _options.CandidateCacheSize = 2;
        using var cache = new AssistedSearchCandidateCache(OptionsMonitor());

        var keys = Enumerable.Range(0, 40)
            .Select(i => cache.BuildKey(PointOfSaleId, $"consulta {i}", new AiSearchFilters(), 20))
            .ToList();

        foreach (var key in keys)
        {
            cache.Set(key, new AiSearchResponse());
        }

        // The cap has to actually cap. Before this was wired, the option validated at start-up,
        // read as a bound in configuration, and did nothing — which is worse than not having it.
        var retained = keys.Count(key => cache.TryGet(key, out _));
        retained.Should().BeLessThan(keys.Count);
    }

    [Fact]
    public void Search_CacheKeyIncludesPointOfSale()
    {
        var cache = new AssistedSearchCandidateCache(OptionsMonitor());

        var filters = new AiSearchFilters();

        var one = cache.BuildKey(PointOfSaleId, "anillo de plata", filters, 20);
        var other = cache.BuildKey(OtherPointOfSaleId, "anillo de plata", filters, 20);

        // Redundant today, because retrieval ignores the point of sale. Present anyway: the day
        // the retriever gains that filter, a key without it becomes a cross-shop leak nobody
        // would think to audit from the other service.
        one.Should().NotBe(other);
    }

    [Fact]
    public void Search_CacheKeyIgnoresTriviallyDifferentSpellings()
    {
        var cache = new AssistedSearchCandidateCache(OptionsMonitor());

        var one = cache.BuildKey(PointOfSaleId, "  Anillo   de PLATA ", new AiSearchFilters(), 20);
        var other = cache.BuildKey(PointOfSaleId, "anillo de plata", new AiSearchFilters(), 20);

        one.Should().Be(other);
    }

    [Fact]
    public void Search_CacheKeyDoesNotCarryTheQueryInClear()
    {
        var cache = new AssistedSearchCandidateCache(OptionsMonitor());

        var key = cache.BuildKey(PointOfSaleId, "regalo para Marta Soler", new AiSearchFilters(), 20);

        // Free text an operator typed. A cache key is one of the places nobody remembers to redact.
        key.Should().NotContain("Marta");
        key.Should().NotContain("regalo");
    }

    [Fact]
    public async Task Search_WhenGatewayThrowsAnUnclassifiedFailure_StillDegrades()
    {
        // A subclass the service does not name. Today none exists beyond the three it catches;
        // this fixes the guarantee structurally, so a later change adding a fourth cannot make
        // the search fail on a fault the AI is responsible for.
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new UnknownGatewayFailure());

        LexicalReturns(Row(Guid.NewGuid()));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        result.Outcome.Should().Be(AssistedSearchOutcome.Success);
        result.Response!.AiAvailable.Should().BeFalse();
        result.Response.Results.Should().ContainSingle();
        _logs.Entries.Should().Contain(entry => entry.Level == LogLevel.Error);
    }

    [Fact]
    public async Task Search_DegradedFunnelCountsMatchesNotJustTheDisplayedPage()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiUnavailableException("circuit open"));

        // Twenty five products of this shop match the terms; ten are displayed.
        LexicalReturns(Enumerable.Range(0, 25).Select(_ => Row(Guid.NewGuid())).ToArray());

        var request = Request();
        request.PageSize = 10;

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        result.Response!.Results.Should().HaveCount(10);

        // Not 10. Capping the search at the page size would make "survived" trivially equal to
        // "displayed" on this path and leave the two origins incomparable in the very analysis
        // the funnel exists for.
        result.Response.SurvivedHydration.Should().Be(25);

        _repository.Verify(
            r => r.SearchLexicalAsync(
                It.IsAny<IReadOnlyList<string>>(),
                PointOfSaleId,
                It.IsAny<AssistedSearchFilters>(),
                AiSearchRequest.OverRetrievalCap,
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    // ---------------------------------------------------------------- observability

    [Fact]
    public async Task Search_EmitsTheFunnelPerSearch()
    {
        var ids = Enumerable.Range(0, 30).Select(_ => Guid.NewGuid()).ToArray();
        GatewayReturns(ids.Select(id => Candidate(id)).ToArray());
        HydrationReturns(ids.Take(12).Select(id => Row(id)).ToArray());

        var request = Request();
        request.PageSize = 10;

        await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        // This is how the loss caused by filtering by point of sale after retrieval becomes
        // measurable, and it is the baseline the point-of-sale prefilter will be compared against.
        var funnel = _logs.Single("Assisted search funnel");
        funnel.Level.Should().Be(LogLevel.Information);
        funnel.Property("PointOfSaleId").Should().Be(PointOfSaleId);
        funnel.Property("Candidates").Should().Be(30);
        funnel.Property("Survived").Should().Be(12);
        funnel.Property("Displayed").Should().Be(10);
        funnel.Property("TraceId").Should().Be("trace-1");
    }

    [Fact]
    public async Task Search_QueryStaysOutOfProductionLogs()
    {
        GatewayReturns(Candidate(Guid.NewGuid()));
        HydrationReturns();

        var request = Request();
        request.Query = "regalo para Marta Soler";

        await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        // Free text an operator typed, which in a hotel point of sale can incidentally name a
        // guest. It is confined to debug level, and a rule nothing asserts is one refactor away
        // from being gone.
        _logs.Entries
            .Where(entry => entry.Level >= LogLevel.Information)
            .Should().NotContain(entry => entry.Mentions("Marta Soler"));

        _logs.At(LogLevel.Debug).Should().Contain(entry => entry.Mentions("Marta Soler"));
    }

    // ---------------------------------------------------------------- permissions

    [Fact]
    public async Task Search_OperatorCannotChooseUnassignedPos()
    {
        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, OtherPointOfSaleId)).ReturnsAsync(false);

        var request = Request();
        request.PointOfSaleId = OtherPointOfSaleId;

        var result = await CreateService().SearchAsync(request, UserId, "Operator", isAdmin: false);

        result.Outcome.Should().Be(AssistedSearchOutcome.PointOfSaleForbidden);
        _gateway.Verify(
            g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);
        _recorded.Should().BeEmpty();
    }

    [Fact]
    public async Task Search_AdminMayChooseAnyActivePos()
    {
        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, OtherPointOfSaleId)).ReturnsAsync(false);
        GatewayReturns();
        HydrationReturns();

        var request = Request();
        request.PointOfSaleId = OtherPointOfSaleId;

        var result = await CreateService().SearchAsync(request, UserId, "Administrator", isAdmin: true);

        result.Outcome.Should().Be(AssistedSearchOutcome.Success);
    }

    [Fact]
    public async Task Search_WhenPointOfSaleInactive_IsRefused()
    {
        _repository
            .Setup(r => r.IsPointOfSaleActiveAsync(PointOfSaleId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        var result = await CreateService().SearchAsync(Request(), UserId, "Administrator", isAdmin: true);

        // Not even an administrator searches a shop that is closed.
        result.Outcome.Should().Be(AssistedSearchOutcome.PointOfSaleUnavailable);
        _gateway.Verify(
            g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task Search_SendsThePointOfSaleThroughTheScope_NotTheBody()
    {
        AiCallScope? captured = null;
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .Callback<AiSearchRequest, AiCallScope, CancellationToken>((_, scope, _) => captured = scope)
            .ReturnsAsync(new AiSearchResponse());

        HydrationReturns();

        await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        captured.Should().NotBeNull();
        captured!.PointOfSaleId.Should().Be(PointOfSaleId);
        captured.Kind.Should().Be(AiCallScopeKind.PointOfSale);
    }

    [Fact]
    public async Task Search_CarriesTheMaterialsTheRetrieverReported_NotHydratedOnes()
    {
        var id = Guid.NewGuid();
        var candidate = Candidate(id);
        candidate.Materials = ["plata", "perla"];

        GatewayReturns(candidate);
        HydrationReturns(Row(id));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // The only explanatory signal available: match reasons are a single constant value for
        // every result until the lexical branch exists, so without this the panel has nothing
        // true to tell the operator about why a piece was proposed.
        result.Response!.Results.Should().ContainSingle()
            .Which.Materials.Should().Equal("plata", "perla");
    }

    [Fact]
    public async Task Search_WhenDegraded_ReturnsAnEmptyMaterialListRatherThanNone()
    {
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiUnavailableException("circuit open"));

        LexicalReturns(Row(Guid.NewGuid()));

        var result = await CreateService().SearchAsync(Request(), UserId, "Operator", isAdmin: false);

        // Empty and present, not absent: there is no candidate on this path because no retriever
        // ran, and a caller must not have to tell "no materials" apart from "no field".
        result.Response!.AiAvailable.Should().BeFalse();
        result.Response.Results.Should().ContainSingle()
            .Which.Materials.Should().NotBeNull().And.BeEmpty();
    }

    // ---------------------------------------------------------------- helpers

    private AssistedSearchService CreateService(bool realCache = false)
    {
        var factory = LoggerFactory.Create(builder => builder
            .SetMinimumLevel(LogLevel.Trace)
            .AddProvider(_logs));

        IAssistedSearchCandidateCache cache = realCache
            ? new AssistedSearchCandidateCache(OptionsMonitor())
            : new NoCache();

        return new AssistedSearchService(
            _gateway.Object,
            _repository.Object,
            cache,
            _userPointOfSale.Object,
            _telemetry.Object,
            _fileStorage.Object,
            _traceContext.Object,
            OptionsMonitor(),
            new AssistedSearchResultProjector(
                _fileStorage.Object, _traceContext.Object,
                factory.CreateLogger<AssistedSearchResultProjector>()),
            AssistOptionsMonitor(),
            FreeQueryOptionsMonitor(),
            AgentOptionsMonitor(),
            _timeProvider,
            factory.CreateLogger<AssistedSearchService>());
    }

    private IOptionsMonitor<AiFreeQuerySearchOptions> FreeQueryOptionsMonitor()
    {
        var monitor = new Mock<IOptionsMonitor<AiFreeQuerySearchOptions>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(_freeQueryOptions);
        return monitor.Object;
    }

    private IOptionsMonitor<AiAgentAssistOptions> AgentOptionsMonitor()
    {
        var monitor = new Mock<IOptionsMonitor<AiAgentAssistOptions>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(_agentOptions);
        return monitor.Object;
    }

    private IOptionsMonitor<AiSalesAssistOptions> AssistOptionsMonitor()
    {
        var monitor = new Mock<IOptionsMonitor<AiSalesAssistOptions>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(_assistOptions);
        return monitor.Object;
    }

    private IOptionsMonitor<AiSearchOptions> OptionsMonitor()
    {
        var monitor = new Mock<IOptionsMonitor<AiSearchOptions>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(_options);
        return monitor.Object;
    }

    private static AssistedSearchRequest Request() => new()
    {
        Query = "anillo de plata",
        PointOfSaleId = PointOfSaleId
    };

    /// <summary>Makes the gateway fail, which is what puts the search on the degraded path.</summary>
    private void GatewayUnavailable() =>
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new AiUnavailableException("circuit open"));

    private void GatewayReturns(params AiSearchResult[] candidates) =>
        _gateway
            .Setup(g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AiSearchResponse
            {
                Results = [.. candidates],
                CandidatesReturned = candidates.Length,
                LowConfidence = false,
                TraceId = "trace-1",
                EffectivePosId = PointOfSaleId.ToString()
            });

    private void HydrationReturns(params AssistedSearchRow[] rows) =>
        _repository
            .Setup(r => r.HydrateAsync(It.IsAny<IReadOnlyList<Guid>>(), It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(rows);

    private void LexicalReturns(params AssistedSearchRow[] rows) =>
        _repository
            .Setup(r => r.SearchLexicalAsync(
                It.IsAny<IReadOnlyList<string>>(), It.IsAny<Guid?>(), It.IsAny<AssistedSearchFilters>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(rows);

    private static AiSearchResult Candidate(Guid productId, string sku = "SKU-1", double score = 0.8) => new()
    {
        ProductId = productId.ToString(),
        Sku = sku,
        Score = score,
        MatchReasons = ["vector"]
    };

    private static AssistedSearchRow Row(
        Guid productId,
        string sku = "SKU-1",
        decimal price = 10m,
        int quantity = 3) => new()
    {
        ProductId = productId,
        Sku = sku,
        Name = "Anillo",
        Price = price,
        Quantity = quantity,
        PrimaryPhotoFileName = "photo.jpg",
        CollectionName = "Tramontana"
    };

    /// <summary>A gateway failure the service does not name, to prove the base-class catch.</summary>
    private sealed class UnknownGatewayFailure()
        : AiGatewayException("a failure mode invented by a later change");

    /// <summary>Cache that never hits, so most tests exercise the retrieval path directly.</summary>
    private sealed class NoCache : IAssistedSearchCandidateCache
    {
        public string BuildKey(Guid pointOfSaleId, string query, AiSearchFilters filters, int window) => "none";

        public bool TryGet(string key, out AiSearchResponse? candidates)
        {
            candidates = null;
            return false;
        }

        public void Set(string key, AiSearchResponse candidates)
        {
        }
    }

    // ------------------------------------------- availability of the every-point-of-sale scope (C40_FIX)

    /// <remarks>
    /// C40 built the every-shop scope in full and left the probe answering for a named shop only,
    /// so a screen offering the scope had nothing to read: the generative path came out disabled
    /// with no reason to show, which is the shape of failure this route was created to remove.
    /// </remarks>
    [Fact]
    public void GetAvailability_WithoutPointOfSale_ReportsTheDefaultScope()
    {
        var availability = CreateService().GetAvailability(null);

        availability.PointOfSaleId.Should().BeNull(
            "an absent point of sale is the wider scope, and it must not come back as a blank one");
        availability.SemanticSearchAvailable.Should().BeTrue();
        availability.AssistedAnswerAvailable.Should().BeTrue();
        availability.AssistedAnswerUnavailableReason.Should().BeNull();
    }

    /// <remarks>
    /// The narrow reading, and the safe one: a deployment that enables the feature shop by shop has
    /// not enabled it for «all of them». Reading it the other way would spend a generative budget
    /// on behalf of shops whose owner deliberately switched the feature off.
    /// </remarks>
    [Fact]
    public void GetAvailability_WithoutPointOfSale_IgnoresThePerShopAllowlist()
    {
        _freeQueryOptions.EnabledByDefault = false;
        _freeQueryOptions.EnabledPointOfSaleIds = [PointOfSaleId];

        var availability = CreateService().GetAvailability(null);

        availability.AssistedAnswerAvailable.Should().BeFalse(
            "an allowlisted shop does not switch the feature on for the scope that covers them all");
        availability.AssistedAnswerUnavailableReason.Should().Be("switched_off");

        // And the same configuration still reports the named shop as available, so what is being
        // asserted is the scope rule and not a switch that happens to be off.
        CreateService().GetAvailability(PointOfSaleId).AssistedAnswerAvailable.Should().BeTrue();
    }

    /// <remarks>
    /// <strong>The guard against the probe and the route drifting apart.</strong> They are computed
    /// in different services, and when they disagree the screen presents a capability that is off as
    /// though it were on — which is the defect C40 was opened to remove. Both now read the same
    /// extension method, and this asserts the verdict rather than the call site.
    /// </remarks>
    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public void GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate(
        bool freeQueryDefault,
        bool assistDefault)
    {
        _freeQueryOptions.EnabledByDefault = freeQueryDefault;
        _freeQueryOptions.EnabledPointOfSaleIds = [PointOfSaleId];
        _assistOptions.EnabledByDefault = assistDefault;
        _assistOptions.EnabledPointOfSaleIds = [PointOfSaleId];

        var probe = CreateService().GetAvailability(null);

        // What the free-query route itself would enforce for the very same scope.
        var routeWouldServe = _freeQueryOptions.IsEnabledForScope(null);

        probe.AssistedAnswerAvailable.Should().Be(routeWouldServe && _assistOptions.IsEnabledForScope(null),
            "the probe must report the predicate the route applies, never one of its own");
    }

    /// <remarks>
    /// The probe describes <em>switches</em>; the panel describes <em>reachability</em>. The fast
    /// route does not accept this scope, but saying so here by answering false would state that
    /// semantic search is switched off — a different fact, and a false one.
    /// </remarks>
    [Fact]
    public void GetAvailability_WithoutPointOfSale_StillReportsTheSemanticSwitchOnItsOwnTerms()
    {
        _options.EnabledByDefault = true;

        CreateService().GetAvailability(null).SemanticSearchAvailable.Should().BeTrue();

        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [PointOfSaleId];

        CreateService().GetAvailability(null).SemanticSearchAvailable.Should().BeFalse();
    }

    [Fact]
    public void GetAvailability_WithoutPointOfSale_MakesNoAiCall()
    {
        CreateService().GetAvailability(null);

        _gateway.VerifyNoOtherCalls();
        _telemetry.VerifyNoOtherCalls();
    }
}
