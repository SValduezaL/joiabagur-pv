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
/// The free-query orchestrator: the third assistance mode, and the one an operator could not
/// reach until C40. No AI service and no database — the gateway, the repository and telemetry
/// are doubles.
/// </summary>
public class FreeQuerySearchServiceTests
{
    private static readonly Guid UserId = Guid.Parse("11111111-1111-1111-1111-111111111111");
    private static readonly Guid PosId = Guid.Parse("22222222-2222-2222-2222-222222222222");
    private static readonly Guid OtherPosId = Guid.Parse("33333333-3333-3333-3333-333333333333");

    private readonly Mock<IAiGatewayClient> _gateway = new();
    private readonly Mock<IAssistedSearchRepository> _repository = new();
    private readonly Mock<IUserPointOfSaleService> _userPointOfSale = new();
    private readonly Mock<IProductSearchEventService> _telemetry = new();
    private readonly Mock<IFileStorageService> _fileStorage = new();
    private readonly Mock<ITraceContextAccessor> _traceContext = new();
    private readonly FakeTimeProvider _timeProvider = new();
    private readonly RecordingLoggerProvider _logs = new();
    private readonly List<RecordSearchRequest> _recorded = [];

    private readonly AiFreeQuerySearchOptions _options = new()
    {
        EnabledByDefault = true,
        CandidateWindow = 5,
        DefaultPageSize = 5,
        MaxPageSize = 20
    };

    public FreeQuerySearchServiceTests()
    {
        _traceContext.SetupGet(t => t.CurrentTraceId).Returns("trace-fq-1");

        _repository
            .Setup(r => r.IsPointOfSaleActiveAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, PosId)).ReturnsAsync(true);

        _fileStorage
            .Setup(f => f.GetUrlAsync(It.IsAny<string>(), It.IsAny<string>()))
            .ReturnsAsync((string file, string? _) => "https://files.test/" + file);

        _telemetry
            .Setup(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()))
            .Callback<RecordSearchRequest>(_recorded.Add)
            .ReturnsAsync(Guid.NewGuid());
    }

    // ---------------------------------------------------------------- the switch

    [Fact]
    public async Task FreeQuery_WhenSwitchedOff_MakesNoAiCall()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [OtherPosId];

        var response = (await SearchAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        response.DegradedReason.Should().Be("switched_off",
            "the screen says a switch did it rather than presenting an outage that is not happening");
        _gateway.Verify(
            g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task FreeQuery_WhenSwitchedOnForOnePointOfSale_CallsTheAi()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [PosId];
        GatewayReturns(Ai());

        (await SearchAsync()).Response!.AiAvailable.Should().BeTrue();
    }

    // ---------------------------------------------------------------- the quota

    /// <remarks>
    /// The allowance is enforced by the endpoint's rate-limiting policy and not by this service,
    /// so what these two hold is the property that makes a separate policy meaningful: the
    /// service reads its own section, and that section's allowance is not the card's.
    /// </remarks>
    [Fact]
    public void FreeQuery_QuotaIsIndependentOfTheCardQuota()
    {
        var card = new AiSalesAssistOptions();
        var freeQuery = new AiFreeQuerySearchOptions();

        AiFreeQuerySearchOptions.SectionName.Should().NotBe(AiSalesAssistOptions.SectionName,
            "a shared section would make one allowance govern both, which is what having two "
            + "sections exists to prevent");

        // They happen to start at the same number, and that is a default rather than a coupling:
        // moving one must not move the other.
        freeQuery.RateLimitPermitLimit = 3;
        card.RateLimitPermitLimit.Should().Be(10);
    }

    // ---------------------------------------------------------------- degradation

    [Theory]
    [InlineData(typeof(AiUnavailableException), "ai_unavailable")]
    [InlineData(typeof(AiNotImplementedException), "not_implemented")]
    [InlineData(typeof(AiGatewayConfigurationException), "credential_rejected")]
    public async Task FreeQuery_WhenTheGatewayFails_DegradesWithItsReason(Type failure, string reason)
    {
        GatewayThrows((AiGatewayException)Activator.CreateInstance(failure, "boom")!);

        var response = (await SearchAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        response.DegradedReason.Should().Be(reason);
        response.PitchStatus.Should().Be(PitchStatus.AiUnavailable);
    }

    [Fact]
    public async Task FreeQuery_WhenTheGatewayFails_StillAnswers()
    {
        GatewayThrows(new AiUnavailableException("circuit open"));

        var result = await SearchAsync();

        // The panel does not break when the AI does: an operator with a customer in front of
        // them needs a screen that says something true, not an error.
        result.Outcome.Should().Be(FreeQuerySearchOutcome.Success);
        result.Response.Should().NotBeNull();
    }

    /// <remarks>
    /// The isolation is structural rather than a rule somebody remembers: the two rides use
    /// different named clients with different circuits, so a generative failure cannot reach the
    /// retrieval one. Asserted by the shape of the call — this service never touches the
    /// retrieval client at all.
    /// </remarks>
    [Fact]
    public async Task FreeQuery_WhenGenerativeBudgetExceeded_LeavesRetrievalCircuitClosed()
    {
        GatewayThrows(new AiUnavailableException("assist budget exceeded"));

        await SearchAsync();

        _gateway.Verify(
            g => g.SearchAsync(It.IsAny<AiSearchRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never,
            "the generative route must not spend, or trip, the retrieval client");
    }

    // ---------------------------------------------------------------- the response

    [Fact]
    public async Task FreeQuery_ForOperator_CarriesNoUsage()
    {
        GatewayReturns(Ai());

        var response = (await SearchAsync(isAdmin: false)).Response!;

        response.Usage.Should().BeNull("the funnel is an administrator's view");
    }

    [Fact]
    public async Task FreeQuery_ForAdministrator_CarriesUsageWithoutAnyAmount()
    {
        GatewayReturns(Ai());

        var response = (await SearchAsync(isAdmin: true)).Response!;

        response.Usage.Should().NotBeNull();
        response.Usage!.TotalTokens.Should().Be(1280);
        response.Usage.Model.Should().Be("fake/model");

        // Inputs of a cost and never the cost: a tariff in a screen is wrong the day the
        // provider moves it, and usage.model is not a pricing key.
        var funnel = System.Text.Json.JsonSerializer.Serialize(response.Usage);
        funnel.Should().NotContain("€").And.NotContain("eur", "no monetary amount, ever");
    }

    [Fact]
    public async Task FreeQuery_DoesNotCarryPieceWarnings()
    {
        GatewayReturns(Ai(warnings:
        [
            "family_has_variants",
            "size_label_missing",
            "knowledge_not_covered",
            "query_out_of_domain"
        ]));

        var response = (await SearchAsync()).Response!;

        // A warning about a piece describes the FIRST MEMBER OF THE FIRST GROUP, not the set, so
        // painting it above fifteen results would state something false about fourteen of them.
        response.Warnings.Should().NotContain("family_has_variants");
        response.Warnings.Should().NotContain("size_label_missing");

        // A warning about the query describes what was asked, and that is what this screen shows.
        response.Warnings.Should().Contain("knowledge_not_covered");
        response.Warnings.Should().Contain("query_out_of_domain");
    }

    [Fact]
    public async Task FreeQuery_PassesTheFiltersTheOperatorPressed()
    {
        GatewayReturns(Ai());

        var request = Request();
        request.Materials = ["plata"];
        request.Category = "pendientes";

        await SearchAsync(request);

        _gateway.Verify(
            g => g.AssistSaleAsync(
                It.Is<AiAssistSaleRequest>(r =>
                    r.Filters.Category == "pendientes" && r.Filters.Materials.Contains("plata")),
                It.IsAny<AiCallScope>(),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task FreeQuery_HydratesPriceAndStockFromTheCatalog()
    {
        var productId = Guid.NewGuid();
        GatewayReturns(Ai(Member(productId, "SKU-INDEXED")));
        HydrationReturns(Row(productId, "SKU-CATALOG", price: 42.5m, quantity: 7));

        var response = (await SearchAsync()).Response!;

        var member = response.Groups.Should().ContainSingle().Subject
            .Members.Should().ContainSingle().Subject;

        member.Price.Should().Be(42.5m);
        member.QuantityAtPointOfSale.Should().Be(7);
        member.Sku.Should().Be("SKU-CATALOG", "the catalog wins over the index");
    }

    [Fact]
    public async Task FreeQuery_DropsAGroupNoMemberOfWhichThisShopCarries()
    {
        GatewayReturns(Ai(Member(Guid.NewGuid())));
        HydrationReturns();

        var response = (await SearchAsync()).Response!;

        response.Groups.Should().BeEmpty("a family nobody can sell here is not an answer");
        response.SurvivedHydration.Should().Be(0);
        response.CandidatesReturned.Should().Be(1);
    }

    // ---------------------------------------------------------------- telemetry

    [Fact]
    public async Task FreeQuery_RecordsTheGenerativeOrigin()
    {
        GatewayReturns(Ai());

        await SearchAsync();

        var recorded = _recorded.Should().ContainSingle().Subject;
        recorded.Origin.Should().Be(SearchOrigin.AssistedGenerative,
            "recording it as the semantic origin would make the comparison this value exists "
            + "for impossible to draw from the table");
        recorded.Query.Should().Be("anillo de plata para regalar");
    }

    [Fact]
    public async Task FreeQuery_RecordsTheRowsTheOperatorSaw_InTheOrderTheyArePainted()
    {
        var first = Guid.NewGuid();
        var second = Guid.NewGuid();
        var third = Guid.NewGuid();

        // Deliberately handed back in another order: the rank must come from what retrieval
        // ranked, never from what the repository happened to return.
        HydrationReturns(Row(third, "SKU-3"), Row(first, "SKU-1"), Row(second, "SKU-2"));

        GatewayReturns(new AiAssistSaleResponse
        {
            TraceId = "trace-fq-1",
            EffectivePosId = PosId.ToString(),
            Intent = "in_domain",
            Groups =
            [
                new AiAssistGroup
                {
                    FamilyId = "fam-1",
                    FamilyLabel = "Aro fino",
                    Members = [Member(first, "SKU-1"), Member(second, "SKU-2")]
                },
                new AiAssistGroup
                {
                    FamilyId = null,
                    FamilyLabel = null,
                    Members = [Member(third, "SKU-3")]
                }
            ],
            Pitch = "Estas piezas encajan con lo que buscas.",
            Citations = [],
            Warnings = [],
            Usage = new AiUsage
            {
                PromptTokens = 1000, CompletionTokens = 280, TotalTokens = 1280, Model = "fake/model"
            },
            Abstained = false,
            PromptVersion = "assist/v5"
        });

        await SearchAsync();

        var recorded = _recorded.Should().ContainSingle().Subject;

        // An empty list here used to leave `SelectedFromRank` null for every generative search,
        // which quietly removed half of what the fourth origin exists to measure: the two routes
        // stayed comparable on duration and filters, and stopped being comparable on whether the
        // operator picked anything.
        recorded.DisplayedResults.Select(displayed => displayed.Sku)
            .Should().Equal(["SKU-1", "SKU-2", "SKU-3"],
                "the panel paints group by group and, inside each, member by member, so that walk "
                + "is the rank the operator perceived");
    }

    [Fact]
    public async Task FreeQuery_WhenTelemetryFails_StillServes()
    {
        GatewayReturns(Ai());
        _telemetry
            .Setup(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()))
            .ThrowsAsync(new InvalidOperationException("the writer is down"));

        var result = await SearchAsync();

        result.Outcome.Should().Be(FreeQuerySearchOutcome.Success);
        result.Response!.SearchEventId.Should().BeNull("a null identifier is a normal outcome");
        _logs.Entries.Should().Contain(entry => entry.Level == LogLevel.Warning);
    }

    // ---------------------------------------------------------------- authorisation

    [Fact]
    public async Task FreeQuery_ForUnassignedPointOfSale_IsForbidden()
    {
        var request = Request();
        request.PointOfSaleId = OtherPosId;

        (await SearchAsync(request)).Outcome
            .Should().Be(FreeQuerySearchOutcome.PointOfSaleForbidden);
    }

    [Fact]
    public async Task FreeQuery_ForInactivePointOfSale_IsUnavailable()
    {
        _repository
            .Setup(r => r.IsPointOfSaleActiveAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);

        (await SearchAsync()).Outcome
            .Should().Be(FreeQuerySearchOutcome.PointOfSaleUnavailable);
    }

    // ---------------------------------------------------------------- the log line

    [Fact]
    public async Task FreeQuery_LogsNeitherTheQueryNorTheArgument()
    {
        GatewayReturns(Ai(pitch: "Estas piezas son sobrias y van bien a diario."));

        await SearchAsync();

        var written = string.Join("\n", _logs.Entries.Select(entry => entry.Message));

        written.Should().NotContain("anillo de plata para regalar",
            "the query is what a customer said out loud");
        written.Should().NotContain("sobrias y van bien a diario",
            "the argument carries the query back");
    }

    // ---------------------------------------------------------------- arrangement

    private static FreeQuerySearchRequest Request() => new()
    {
        Query = "anillo de plata para regalar",
        PointOfSaleId = PosId
    };

    private Task<FreeQuerySearchResult> SearchAsync(
        FreeQuerySearchRequest? request = null, bool isAdmin = false) =>
        CreateService().SearchAsync(request ?? Request(), UserId, "Operator", isAdmin);

    private void GatewayReturns(AiAssistSaleResponse response) =>
        _gateway
            .Setup(g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(response);

    private void GatewayThrows(AiGatewayException failure) =>
        _gateway
            .Setup(g => g.AssistSaleAsync(It.IsAny<AiAssistSaleRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(failure);

    private void HydrationReturns(params AssistedSearchRow[] rows) =>
        _repository
            .Setup(r => r.HydrateAsync(It.IsAny<IReadOnlyList<Guid>>(), It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(rows);

    private static AiAssistGroupMember Member(Guid productId, string sku = "SKU-1") => new()
    {
        ProductId = productId.ToString(),
        Sku = sku,
        Score = 0.8,
        Materials = ["plata"],
        MatchReasons = ["vector"]
    };

    private static AssistedSearchRow Row(
        Guid productId, string sku = "SKU-1", decimal price = 39.9m, int quantity = 3) => new()
    {
        ProductId = productId,
        Sku = sku,
        Name = "Anillo de plata",
        Price = price,
        Quantity = quantity
    };

    /// <summary>A served response whose members are hydrated by default.</summary>
    private AiAssistSaleResponse Ai(
        AiAssistGroupMember? member = null,
        List<string>? warnings = null,
        string pitch = "Estas piezas encajan con lo que buscas.")
    {
        var resolved = member ?? Member(Guid.NewGuid());

        if (member is null)
        {
            HydrationReturns(Row(Guid.Parse(resolved.ProductId), resolved.Sku));
        }

        return new AiAssistSaleResponse
        {
            TraceId = "trace-fq-1",
            EffectivePosId = PosId.ToString(),
            Intent = "in_domain",
            Groups = [new AiAssistGroup { FamilyId = "fam-1", FamilyLabel = "Aro fino", Members = [resolved] }],
            Pitch = pitch,
            Citations = [],
            Warnings = warnings ?? [],
            Usage = new AiUsage { PromptTokens = 1000, CompletionTokens = 280, TotalTokens = 1280, Model = "fake/model" },
            Abstained = false,
            PromptVersion = "assist/v5"
        };
    }

    private FreeQuerySearchService CreateService()
    {
        using var factory = LoggerFactory.Create(builder => builder
            .SetMinimumLevel(LogLevel.Trace)
            .AddProvider(_logs));

        var monitor = new Mock<IOptionsMonitor<AiFreeQuerySearchOptions>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(_options);

        return new FreeQuerySearchService(
            _gateway.Object,
            _repository.Object,
            new AssistedSearchResultProjector(
                _fileStorage.Object, _traceContext.Object,
                factory.CreateLogger<AssistedSearchResultProjector>()),
            _userPointOfSale.Object,
            _telemetry.Object,
            _traceContext.Object,
            monitor.Object,
            _timeProvider,
            factory.CreateLogger<FreeQuerySearchService>());
    }
}
