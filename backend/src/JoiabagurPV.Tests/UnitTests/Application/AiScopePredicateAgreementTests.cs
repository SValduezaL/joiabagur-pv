using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
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
/// The availability probe against the route it describes, <strong>both of them actually run</strong>,
/// over one shared set of options. C40_FIX, independent verification.
/// </summary>
/// <remarks>
/// <para>
/// This class exists because the guard C40_FIX shipped for its own central invariant —
/// <c>AssistedSearchServiceTests.GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate</c> —
/// computes its expected value with the same extension methods the probe uses and never invokes
/// <see cref="FreeQuerySearchService"/> at all. Measured: it stays green both when the shared
/// predicate's null branch is inverted and when the route is rewritten to apply a different rule
/// for the absence. A test that survives the divergence it is named after is not a guard.
/// </para>
/// <para>
/// So the comparison here is made the only way it can bite: build the probe and the route over the
/// <em>same</em> options objects, ask one and <em>run</em> the other, and compare the verdicts
/// rather than the call sites.
/// </para>
/// </remarks>
public class AiScopePredicateAgreementTests
{
    private static readonly Guid UserId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    private static readonly Guid PointOfSaleId = Guid.Parse("22222222-2222-2222-2222-222222222222");

    private readonly Mock<IAiGatewayClient> _gateway = new();
    private readonly Mock<IAssistedSearchRepository> _repository = new();
    private readonly Mock<IAssistedSearchCandidateCache> _cache = new();
    private readonly Mock<IUserPointOfSaleService> _userPointOfSale = new();
    private readonly Mock<IProductSearchEventService> _telemetry = new();
    private readonly Mock<IFileStorageService> _fileStorage = new();
    private readonly Mock<ITraceContextAccessor> _traceContext = new();
    private readonly FakeTimeProvider _timeProvider = new();
    private readonly RecordingLoggerProvider _logs = new();

    private readonly AiSearchOptions _semanticOptions = new() { EnabledByDefault = true };
    private readonly AiSalesAssistOptions _assistOptions = new() { EnabledByDefault = true };
    private readonly AiFreeQuerySearchOptions _freeQueryOptions = new()
    {
        EnabledByDefault = true,
        CandidateWindow = 5,
        DefaultPageSize = 5,
        MaxPageSize = 20
    };

    private readonly AiAgentAssistOptions _agentOptions = new() { EnabledByDefault = true };

    public AiScopePredicateAgreementTests()
    {
        _traceContext.SetupGet(t => t.CurrentTraceId).Returns("trace-agreement");

        _repository
            .Setup(r => r.IsPointOfSaleActiveAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        _repository
            .Setup(r => r.HydrateAsync(
                It.IsAny<IReadOnlyList<Guid>>(), It.IsAny<Guid?>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync([]);

        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, PointOfSaleId)).ReturnsAsync(true);

        _telemetry
            .Setup(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()))
            .ReturnsAsync(Guid.NewGuid());

        _gateway
            .Setup(g => g.AssistSaleAsync(
                It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AiAssistSaleResponse { Intent = "in_domain", Pitch = "prosa" });
    }

    /// <summary>
    /// The invariant D4 set out to buy: for the scope with no shop named, what the probe reports
    /// and what the route does are the same answer.
    /// </summary>
    /// <remarks>
    /// The per-shop allowlist is populated on purpose in every case. It is the trap the absence has
    /// to step over — the narrow reading says an allowlisted shop does not switch the feature on for
    /// the scope that covers them all — and a route that fell back to the allowlist instead of the
    /// default would be serving a scope the screen reports as off. That is the divergence that
    /// reproduces C40's original defect, and this asserts it against the route's own behaviour.
    /// </remarks>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ProbeAndRoute_AgreeOnTheWiderScope_WhateverTheFreeQuerySwitchSays(
        bool freeQueryEnabledByDefault)
    {
        _freeQueryOptions.EnabledByDefault = freeQueryEnabledByDefault;
        _freeQueryOptions.EnabledPointOfSaleIds = [PointOfSaleId];

        var probe = Probe().GetAvailability(null);
        var served = await RouteServesTheWiderScopeAsync();

        probe.AssistedAnswerAvailable.Should().Be(served,
            "the probe describes the route, so a verdict of its own is the defect C40_FIX was opened to remove");

        if (!served)
        {
            probe.AssistedAnswerUnavailableReason.Should().Be("switched_off",
                "a switch is the only reason the probe can know without making a call");
        }
    }

    /// <summary>
    /// The route's own reading of the absence, asserted through the route and not through the
    /// extension method it calls.
    /// </summary>
    /// <remarks>
    /// Without this, the only thing pinning the route's null branch to <c>EnabledByDefault</c> is
    /// the extension method asserting itself. Inverting that branch leaves the agreement test above
    /// green — both sides move together — so the rule's <em>value</em> needs an assertion of its own
    /// on each side.
    /// </remarks>
    [Fact]
    public async Task Route_ReadsTheAbsenceAsTheDeploymentDefault_AndIgnoresTheAllowlist()
    {
        _freeQueryOptions.EnabledByDefault = false;
        _freeQueryOptions.EnabledPointOfSaleIds = [PointOfSaleId];

        (await RouteServesTheWiderScopeAsync()).Should().BeFalse(
            "a deployment that enables the feature shop by shop has not enabled it for «all of them»");

        _freeQueryOptions.EnabledByDefault = true;
        _freeQueryOptions.EnabledPointOfSaleIds = [];

        (await RouteServesTheWiderScopeAsync()).Should().BeTrue(
            "and with the default on, the scope is served without any shop appearing in a list");
    }

    /// <summary>
    /// <strong>A disagreement that is real, and is pinned here so it cannot be lost.</strong>
    /// </summary>
    /// <remarks>
    /// <para>
    /// The probe reports the assisted answer as the conjunction of the free-query switch
    /// <em>and</em> the sale card's, while <see cref="FreeQuerySearchService"/> never reads the sale
    /// card's switch at all — it calls the gateway on the free-query switch alone. So with the
    /// free-query route switched on and the sale card switched off, the probe answers
    /// <c>switched_off</c> for a scope the route serves with prose. Verified over HTTP against the
    /// running API on 2026-09-26 as well as here.
    /// </para>
    /// <para>
    /// On the panel that lands exactly where C40_FIX came in: with the every-shop scope selected,
    /// both options of the route selector go disabled and the screen reads «La búsqueda en todas las
    /// tiendas usa la respuesta asistida, y está desactivada» — of a scope the backend answers
    /// normally. The behaviour predates C40_FIX; what C40_FIX added is a requirement saying the
    /// probe reports «the same predicate the search route applies», which this contradicts.
    /// </para>
    /// <para>
    /// Left as it is rather than changed here, because which side is wrong is a product decision:
    /// see <c>openspec/DEFERRED_TASKS.md</c>. This test states the present answer so that whoever
    /// settles it has to come through here.
    /// </para>
    /// </remarks>
    [Fact]
    public async Task Probe_AlsoReportsTheSaleCardSwitch_WhichTheRouteNeverApplies()
    {
        _freeQueryOptions.EnabledByDefault = true;
        _assistOptions.EnabledByDefault = false;

        var probe = Probe().GetAvailability(null);

        probe.AssistedAnswerAvailable.Should().BeFalse(
            "the probe ANDs the sale card's switch into its answer");
        probe.AssistedAnswerUnavailableReason.Should().Be("switched_off");

        (await RouteServesTheWiderScopeAsync()).Should().BeTrue(
            "while the route reads the free-query switch alone — the disagreement this test exists to record");
    }

    /// <summary>Runs the real route for the wider scope and reports whether it served or refused.</summary>
    private async Task<bool> RouteServesTheWiderScopeAsync()
    {
        var result = await Route().SearchAsync(
            new FreeQuerySearchRequest { Query = "un anillo de plata para regalar" },
            UserId,
            "Operator",
            isAdmin: false);

        return result.Response!.DegradedReason != "switched_off" && result.Response.AiAvailable;
    }

    private AssistedSearchService Probe()
    {
        var factory = LoggerFactory.Create(builder => builder
            .SetMinimumLevel(LogLevel.Trace)
            .AddProvider(_logs));

        return new AssistedSearchService(
            _gateway.Object,
            _repository.Object,
            _cache.Object,
            _userPointOfSale.Object,
            _telemetry.Object,
            _fileStorage.Object,
            _traceContext.Object,
            Monitor(_semanticOptions),
            Projector(factory),
            Monitor(_assistOptions),
            Monitor(_freeQueryOptions),
            Monitor(_agentOptions),
            _timeProvider,
            factory.CreateLogger<AssistedSearchService>());
    }

    private FreeQuerySearchService Route()
    {
        var factory = LoggerFactory.Create(builder => builder
            .SetMinimumLevel(LogLevel.Trace)
            .AddProvider(_logs));

        return new FreeQuerySearchService(
            _gateway.Object,
            _repository.Object,
            Projector(factory),
            _userPointOfSale.Object,
            _telemetry.Object,
            _traceContext.Object,
            Monitor(_freeQueryOptions),
            _timeProvider,
            factory.CreateLogger<FreeQuerySearchService>());
    }

    private AssistedSearchResultProjector Projector(ILoggerFactory factory) =>
        new(_fileStorage.Object, _traceContext.Object,
            factory.CreateLogger<AssistedSearchResultProjector>());

    private static IOptionsMonitor<T> Monitor<T>(T value) where T : class
    {
        var monitor = new Mock<IOptionsMonitor<T>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(value);
        return monitor.Object;
    }
}
