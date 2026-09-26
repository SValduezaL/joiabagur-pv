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
/// The sale-agent orchestrator: the consumer that did not exist until C42, though the loop behind
/// it had been delivered and measured since C32b. No AI service and no database — the gateway, the
/// repository and telemetry are doubles.
/// </summary>
public class AgentAssistServiceTests
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

    private readonly AiAgentAssistOptions _options = new()
    {
        EnabledByDefault = true,
        CandidateWindow = 5
    };

    private readonly AiFreeQuerySearchOptions _pageOptions = new()
    {
        EnabledByDefault = true,
        CandidateWindow = 5,
        DefaultPageSize = 5,
        MaxPageSize = 20
    };

    public AgentAssistServiceTests()
    {
        _traceContext.SetupGet(t => t.CurrentTraceId).Returns("trace-agent-1");

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

    /// <summary>
    /// The agent's own switch, never the assisted answer's: the two can be off independently
    /// because the agent has a credential chain of its own on the service side.
    /// </summary>
    [Fact]
    public async Task Agent_WhenSwitchedOff_MakesNoAiCall()
    {
        _options.EnabledByDefault = false;
        _options.EnabledPointOfSaleIds = [OtherPosId];

        var response = (await AnswerAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        response.DegradedReason.Should().Be("switched_off");
        _gateway.Verify(
            g => g.AssistAgentAsync(It.IsAny<AiAssistAgentRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task Agent_WhenTheAssistedAnswerIsOffButTheAgentIsOn_IsStillServed()
    {
        // The state the probe has to be able to report, exercised on the route so the two cannot
        // drift: the assisted answer's switch has no say over this path.
        _pageOptions.EnabledByDefault = false;
        _options.EnabledByDefault = true;
        GatewayReturns(Ai());

        var response = (await AnswerAsync()).Response!;

        response.AiAvailable.Should().BeTrue();
        response.DegradedReason.Should().BeNull();
    }

    // ---------------------------------------------------------------- the five new fields

    [Fact]
    public async Task Agent_CarriesTheFiveAgentFieldsWithoutComputingThem()
    {
        GatewayReturns(Ai(
            partial: true,
            stopReason: "presupuesto_tools",
            iterations: 3,
            toolCallsUsed: 6));

        var response = (await AnswerAsync()).Response!;

        response.Partial.Should().BeTrue();
        response.StopReason.Should().Be("presupuesto_tools");
        response.Iterations.Should().Be(3);
        response.ToolCallsUsed.Should().Be(6);
        response.AgentPromptVersion.Should().Be("assist/v6");
    }

    /// <summary>
    /// Two answers with the same iteration count and different stop reasons, so the statement
    /// cannot be coming from the counter.
    /// </summary>
    [Fact]
    public async Task Agent_DoesNotDeriveTheStopReasonFromTheCounters()
    {
        GatewayReturns(Ai(iterations: 5, stopReason: "sin_mas_herramientas"));
        var complete = (await AnswerAsync()).Response!;

        GatewayReturns(Ai(iterations: 5, stopReason: "presupuesto_vueltas", partial: true));
        var cut = (await AnswerAsync()).Response!;

        complete.Iterations.Should().Be(cut.Iterations);
        complete.StopReason.Should().NotBe(cut.StopReason,
            "five iterations does not say whether the fifth was the last one needed or the one "
            + "that ran out, and those are opposite claims about the answer being read");
    }

    [Fact]
    public async Task Agent_CarriesTheTraceWithoutArgumentsOrObservations()
    {
        var ai = Ai();
        ai.Trace =
        [
            new AiAgentTraceIteration
            {
                Iteration = 1,
                Tools =
                [
                    new AiAgentTraceTool { Tool = "buscar_catalogo", Ok = true },
                    new AiAgentTraceTool
                    {
                        Tool = "buscar_sustitutos", Ok = false, Cause = "presupuesto_agotado"
                    }
                ],
                PromptTokens = 3200,
                CompletionTokens = 60,
                TotalTokens = 3260,
                ElapsedMs = 1420.5
            }
        ];
        GatewayReturns(ai);

        var response = (await AnswerAsync()).Response!;

        response.Trace.Should().ContainSingle();
        response.Trace[0].Tools.Select(tool => tool.Tool)
            .Should().Equal("buscar_catalogo", "buscar_sustitutos");
        response.Trace[0].Tools[1].Cause.Should().Be("presupuesto_agotado");
        response.Trace[0].TotalTokens.Should().Be(3260);
        response.Trace[0].ElapsedMs.Should().BeApproximately(1420.5, 0.01);
    }

    // ---------------------------------------------------------------- hydration

    /// <summary>
    /// <strong>Every member of every group, substitutes on the same terms as matches.</strong>
    /// A substitute is a piece of this catalogue like any other; treating it differently is how a
    /// screen ends up showing an alternative with no price.
    /// </summary>
    [Fact]
    public async Task Agent_HydratesEveryMemberOfEveryGroupIncludingASubstitutesGroup()
    {
        var match = Guid.NewGuid();
        var substitute = Guid.NewGuid();

        var ai = Ai();
        ai.Groups =
        [
            new AiAssistAgentGroup
            {
                FamilyId = "fam-1",
                FamilyLabel = "Aro fino",
                Origin = "catalogo",
                Members = [Member(match, "ARO-M")]
            },
            new AiAssistAgentGroup
            {
                FamilyId = null,
                FamilyLabel = null,
                Origin = "sustitutos",
                Members = [Member(substitute, "SUB-1")]
            }
        ];
        HydrationReturns(
            Row(match, "ARO-M", price: 49.9m, quantity: 2),
            Row(substitute, "SUB-1", price: 19.9m, quantity: 7));
        GatewayReturns(ai);

        var response = (await AnswerAsync()).Response!;

        response.Groups.Should().HaveCount(2);
        response.Groups.Select(group => group.Origin).Should().Equal("catalogo", "sustitutos");

        var alternative = response.Groups[1].Members.Should().ContainSingle().Subject;
        alternative.Name.Should().Be("Anillo de plata");
        alternative.Price.Should().Be(19.9m);
        alternative.QuantityAtPointOfSale.Should().Be(7);
        alternative.HasStock.Should().BeTrue();
    }

    /// <summary>
    /// With no shop named, quantity and the stock flag are <strong>unknown</strong> and not zero.
    /// Zero would assert something false about a piece sitting in the next shop along.
    /// </summary>
    [Fact]
    public async Task Agent_WithTheEveryShopScope_ReportsStockAsUnknownRatherThanZero()
    {
        var productId = Guid.NewGuid();
        var ai = Ai(Member(productId));
        // The repository already reports the absence as unknown when no shop is named; what this
        // pins is that the service carries the null through instead of collapsing it to zero.
        _repository
            .Setup(r => r.HydrateAsync(
                It.IsAny<IReadOnlyList<Guid>>(), null, It.IsAny<CancellationToken>()))
            .ReturnsAsync([Row(productId, quantity: null)]);
        GatewayReturns(ai);

        var response = (await AnswerAsync(
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = null })).Response!;

        var member = response.Groups.Single().Members.Single();
        member.QuantityAtPointOfSale.Should().BeNull();
        member.HasStock.Should().BeNull();
    }

    [Fact]
    public async Task Agent_DoesNotPublishTheServicesAvailabilityBand()
    {
        GatewayReturns(Ai());

        var response = (await AnswerAsync()).Response!;

        // The loop's qualitative band governs one thing — whether it pivots — and never leaves the
        // service. The stock the response carries is this side's.
        response.Groups.Single().Members.Single().HasStock.Should().BeTrue();
        response.GetType().GetProperties().Select(property => property.Name)
            .Should().NotContain("AvailabilityBucket");
    }

    // ---------------------------------------------------------------- degradation

    /// <summary>
    /// A 200 reporting that the provider fell is a response carrying that state, never a server
    /// error and never an exception.
    /// </summary>
    [Fact]
    public async Task Agent_WhenTheLoopReportsAProviderFailure_ServesItAsAnAnswer()
    {
        var ai = Ai(partial: true, stopReason: "fallo_proveedor", pitch: "");
        ai.PromptVersion = null;
        GatewayReturns(ai);

        var result = await AnswerAsync();

        result.Outcome.Should().Be(AgentAssistOutcome.Success);
        result.Response!.AiAvailable.Should().BeTrue("the service answered");
        result.Response.StopReason.Should().Be("fallo_proveedor");
        result.Response.Partial.Should().BeTrue();
        result.Response.PitchStatus.Should().Be(PitchStatus.NotGenerated);
    }

    [Theory]
    [InlineData("credential_rejected")]
    [InlineData("not_implemented")]
    [InlineData("ai_unavailable")]
    public async Task Agent_WhenTheGatewayFails_DegradesWithAReasonAndNeverThrows(string expected)
    {
        GatewayThrows(expected switch
        {
            "credential_rejected" => new AiGatewayConfigurationException("rejected"),
            "not_implemented" => new AiNotImplementedException("absent"),
            _ => new AiUnavailableException("down")
        });

        var response = (await AnswerAsync()).Response!;

        response.AiAvailable.Should().BeFalse();
        response.DegradedReason.Should().Be(expected);
        response.PitchStatus.Should().Be(PitchStatus.AiUnavailable);
        response.Groups.Should().BeEmpty();
    }

    // ---------------------------------------------------------------- authorisation

    [Fact]
    public async Task Agent_WhenTheShopIsNotAssigned_IsForbidden()
    {
        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, OtherPosId)).ReturnsAsync(false);

        var result = await AnswerAsync(
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = OtherPosId });

        result.Outcome.Should().Be(AgentAssistOutcome.PointOfSaleForbidden);
        _gateway.Verify(
            g => g.AssistAgentAsync(It.IsAny<AiAssistAgentRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()),
            Times.Never);
    }

    [Fact]
    public async Task Agent_ForAnAdministratorOnAnUnassignedShop_IsServed()
    {
        _userPointOfSale.Setup(u => u.HasAccessAsync(UserId, OtherPosId)).ReturnsAsync(false);
        GatewayReturns(Ai());

        var result = await AnswerAsync(
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = OtherPosId }, isAdmin: true);

        result.Outcome.Should().Be(AgentAssistOutcome.Success);
    }

    [Fact]
    public async Task Agent_WithTheEveryShopScope_IsServedToAnOperatorToo()
    {
        // The rule is the free-query route's, copied and not tightened: two sibling panels with two
        // different authorisation rules break without any test failing.
        GatewayReturns(Ai());

        var result = await AnswerAsync(
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = null });

        result.Outcome.Should().Be(AgentAssistOutcome.Success);
    }

    // ---------------------------------------------------------------- telemetry

    [Fact]
    public async Task Agent_RecordsTheSelectionEventWithTheFifthOrigin()
    {
        GatewayReturns(Ai());

        await AnswerAsync();

        _recorded.Should().ContainSingle()
            .Which.Origin.Should().Be(SearchOrigin.AssistedAgent);
        SearchOrigin.AssistedAgent.Should().Be((SearchOrigin)5,
            "the value is read by hand in SQL, so it is part of the contract with whoever writes it");
    }

    [Fact]
    public async Task Agent_RecordsTheLastOperatorTurnAsTheQuery()
    {
        GatewayReturns(Ai());

        await AnswerAsync(new AgentAssistRequest
        {
            Turns =
            [
                new AgentAssistTurnDto { Role = "operario", Text = "busco un anillo" },
                new AgentAssistTurnDto { Role = "asistente", Text = "te enseño estos" },
                new AgentAssistTurnDto { Role = "operario", Text = "¿y en dorado?" }
            ],
            PointOfSaleId = PosId
        });

        // The turn being answered, not the whole conversation: the retention limitation the
        // semantic path declares covers one query and not a transcript.
        _recorded.Should().ContainSingle().Which.Query.Should().Be("¿y en dorado?");
    }

    [Fact]
    public async Task Agent_WithTheEveryShopScope_RecordsNothingAndSaysSo()
    {
        var productId = Guid.NewGuid();
        _repository
            .Setup(r => r.HydrateAsync(
                It.IsAny<IReadOnlyList<Guid>>(), null, It.IsAny<CancellationToken>()))
            .ReturnsAsync([Row(productId)]);
        GatewayReturns(Ai(Member(productId)));

        var response = (await AnswerAsync(
            new AgentAssistRequest { Turns = Turns(), PointOfSaleId = null })).Response!;

        // The inherited gap, declared rather than closed: the event's shop column is required and
        // indexed, so recording one would need a migration and a placeholder would be a lie.
        _recorded.Should().BeEmpty();
        response.SearchEventId.Should().BeNull();
    }

    [Fact]
    public async Task Agent_WhenTelemetryFails_StillServesTheTurn()
    {
        _telemetry
            .Setup(t => t.RecordSearchAsync(It.IsAny<RecordSearchRequest>()))
            .ThrowsAsync(new InvalidOperationException("the writer is down"));
        GatewayReturns(Ai());

        var response = (await AnswerAsync()).Response!;

        response.SearchEventId.Should().BeNull();
        response.Groups.Should().NotBeEmpty("telemetry is expendable and a conversation is not");
    }

    // ---------------------------------------------------------------- cost and privacy

    [Fact]
    public async Task Agent_ReportsTheCostToAnAdministratorAndNotToAnOperator()
    {
        GatewayReturns(Ai());

        (await AnswerAsync()).Response!.Usage.Should().BeNull();

        var administrator = (await AnswerAsync(isAdmin: true)).Response!;
        administrator.Usage.Should().NotBeNull();
        administrator.Usage!.TotalTokens.Should().Be(13116);
        administrator.Usage.ProviderCalls.Should().Be(4,
            "the provider-call count is what makes the loop's ceiling observable from the object a "
            + "consumer reads");
    }

    [Fact]
    public async Task Agent_NeverLogsTheTranscriptOrTheArgument()
    {
        GatewayReturns(Ai(pitch: "ARGUMENTARIO-QUE-NO-DEBE-APARECER"));

        await AnswerAsync(new AgentAssistRequest
        {
            Turns = [new AgentAssistTurnDto { Role = "operario", Text = "MARCA-SECRETA" }],
            PointOfSaleId = PosId
        });

        _logs.Entries.Should().NotContain(entry => entry.Message.Contains("MARCA-SECRETA"));
        _logs.Entries.Should().NotContain(
            entry => entry.Message.Contains("ARGUMENTARIO-QUE-NO-DEBE-APARECER"));

        // And the funnel is there, with the counters a cost review reads first.
        _logs.Entries.Should().Contain(entry => entry.Message.Contains("stage=agent_assist"));
    }

    // ---------------------------------------------------------------- helpers

    private static List<AgentAssistTurnDto> Turns() =>
        [new AgentAssistTurnDto { Role = "operario", Text = "busco un anillo de plata" }];

    private AgentAssistRequest Request() => new()
    {
        Turns = Turns(),
        PointOfSaleId = PosId
    };

    private Task<AgentAssistResult> AnswerAsync(
        AgentAssistRequest? request = null, bool isAdmin = false) =>
        CreateService().AnswerAsync(request ?? Request(), UserId, "Operator", isAdmin);

    private void GatewayReturns(AiAssistAgentResponse response) =>
        _gateway
            .Setup(g => g.AssistAgentAsync(It.IsAny<AiAssistAgentRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(response);

    private void GatewayThrows(AiGatewayException failure) =>
        _gateway
            .Setup(g => g.AssistAgentAsync(It.IsAny<AiAssistAgentRequest>(), It.IsAny<AiCallScope>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(failure);

    /// <summary>
    /// Matches <c>Guid?</c> and not <c>Guid</c>, so the every-shop scope is covered too: with
    /// <c>It.IsAny&lt;Guid&gt;()</c> a null shop matches no setup and the mock returns null, which
    /// surfaces as an <c>ArgumentNullException</c> inside the hydrator rather than as a failed
    /// assertion — a red that says nothing about the code under test.
    /// </summary>
    private void HydrationReturns(params AssistedSearchRow[] rows) =>
        _repository
            .Setup(r => r.HydrateAsync(It.IsAny<IReadOnlyList<Guid>>(), It.IsAny<Guid?>(), It.IsAny<CancellationToken>()))
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
        Guid productId, string sku = "SKU-1", decimal price = 39.9m, int? quantity = 3) => new()
    {
        ProductId = productId,
        Sku = sku,
        Name = "Anillo de plata",
        Price = price,
        Quantity = quantity
    };

    /// <summary>A served response whose members are hydrated by default.</summary>
    private AiAssistAgentResponse Ai(
        AiAssistGroupMember? member = null,
        string pitch = "De las dos, la de aro fino es la más sobria.",
        bool partial = false,
        string stopReason = "sin_mas_herramientas",
        int iterations = 2,
        int toolCallsUsed = 3)
    {
        var resolved = member ?? Member(Guid.NewGuid());

        if (member is null)
        {
            HydrationReturns(Row(Guid.Parse(resolved.ProductId), resolved.Sku));
        }

        return new AiAssistAgentResponse
        {
            TraceId = "trace-agent-1",
            EffectivePosId = PosId.ToString(),
            Intent = "in_domain",
            Groups =
            [
                new AiAssistAgentGroup
                {
                    FamilyId = "fam-1",
                    FamilyLabel = "Aro fino",
                    Origin = "catalogo",
                    Members = [resolved]
                }
            ],
            Pitch = pitch,
            Citations = [],
            Warnings = [],
            Usage = new AiAgentUsage
            {
                PromptTokens = 12876,
                CompletionTokens = 240,
                TotalTokens = 13116,
                Model = "openai/gpt-4o",
                Calls = 4
            },
            Abstained = false,
            PromptVersion = "assist/v6",
            Partial = partial,
            StopReason = stopReason,
            Iterations = iterations,
            ToolCallsUsed = toolCallsUsed,
            Trace = [],
            AgentPromptVersion = "assist/v6"
        };
    }

    private AgentAssistService CreateService()
    {
        using var factory = LoggerFactory.Create(builder => builder
            .SetMinimumLevel(LogLevel.Trace)
            .AddProvider(_logs));

        var monitor = new Mock<IOptionsMonitor<AiAgentAssistOptions>>();
        monitor.SetupGet(m => m.CurrentValue).Returns(_options);

        var pageMonitor = new Mock<IOptionsMonitor<AiFreeQuerySearchOptions>>();
        pageMonitor.SetupGet(m => m.CurrentValue).Returns(_pageOptions);

        return new AgentAssistService(
            _gateway.Object,
            _repository.Object,
            new AssistedSearchResultProjector(
                _fileStorage.Object, _traceContext.Object,
                factory.CreateLogger<AssistedSearchResultProjector>()),
            _userPointOfSale.Object,
            _telemetry.Object,
            _traceContext.Object,
            monitor.Object,
            pageMonitor.Object,
            _timeProvider,
            factory.CreateLogger<AgentAssistService>());
    }
}
