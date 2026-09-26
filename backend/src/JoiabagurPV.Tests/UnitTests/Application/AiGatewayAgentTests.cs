using System.IdentityModel.Tokens.Jwt;
using System.Net;
using System.Text.Json;
using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Services;
using JoiabagurPV.Tests.TestHelpers;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Time.Testing;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// The operation C42 adds to the gateway — the sale agent — against the real resilience pipeline
/// with a fake socket underneath.
/// </summary>
/// <remarks>
/// What these assert that a mock could not: that the agent rides a client of its own with a budget
/// of its own, that its circuit is separate from the generative route's, and — the decision this
/// change turns on — that a degradation the service reports inside a 200 does not count as a
/// failure. Those are properties of the registration, and a hand-rolled stand-in would test the
/// stand-in.
/// </remarks>
public class AiGatewayAgentTests
{
    private const string FirstId = "11111111-1111-1111-1111-111111111111";
    private const string SecondId = "33333333-3333-3333-3333-333333333333";

    /// <summary>
    /// A pivot: one catalogue group and one substitutes group, which is what the provenance field
    /// exists for and what the loop did 125 times in the measured pass.
    /// </summary>
    private const string AgentBody = $$"""
        {
          "trace_id": "trace-agent-0001",
          "effective_pos_id": "44444444-4444-4444-4444-444444444444",
          "intent": "in_domain",
          "groups": [
            {
              "family_id": "22222222-2222-2222-2222-222222222222",
              "family_label": "Aro Menorca",
              "origin": "catalogo",
              "members": [
                { "product_id": "{{FirstId}}", "sku": "ARO-M", "variant_label": "18 mm",
                  "materials": ["plata"], "score": 0.91, "match_reasons": ["vector"] }
              ]
            },
            {
              "family_id": null,
              "family_label": null,
              "origin": "sustitutos",
              "members": [
                { "product_id": "{{SecondId}}", "sku": "SUB-1", "variant_label": null,
                  "materials": ["acero"], "score": 0.64, "match_reasons": [] }
              ]
            }
          ],
          "pitch": "De las dos, la de aro fino es la más sobria y la otra la más vistosa.",
          "citations": [],
          "warnings": [],
          "clarification_question": null,
          "usage": { "prompt_tokens": 12876, "completion_tokens": 240, "total_tokens": 13116,
                     "model": "openai/gpt-4o", "calls": 4 },
          "abstained": false,
          "prompt_version": "assist/v6",
          "partial": true,
          "stop_reason": "presupuesto_tools",
          "iterations": 3,
          "tool_calls_used": 6,
          "trace": [
            { "iteration": 1,
              "tools": [ { "tool": "buscar_catalogo", "ok": true, "cause": null } ],
              "prompt_tokens": 3200, "completion_tokens": 60, "total_tokens": 3260, "elapsed_ms": 1420.5 },
            { "iteration": 2,
              "tools": [ { "tool": "consultar_disponibilidad", "ok": true, "cause": null },
                         { "tool": "buscar_sustitutos", "ok": false, "cause": "presupuesto_agotado" } ],
              "prompt_tokens": 4100, "completion_tokens": 80, "total_tokens": 4180, "elapsed_ms": 1980.0 },
            { "iteration": 3, "tools": [], "prompt_tokens": 5576, "completion_tokens": 100,
              "total_tokens": 5676, "elapsed_ms": 1910.2 }
          ],
          "agent_prompt_version": "assist/v6"
        }
        """;

    /// <summary>
    /// The 200 the whole circuit decision turns on: the service answered, and reported that its
    /// provider fell.
    /// </summary>
    private const string ProviderFailureBody = """
        {
          "trace_id": "trace-agent-0002",
          "effective_pos_id": "44444444-4444-4444-4444-444444444444",
          "intent": "unclassified",
          "groups": [],
          "pitch": "",
          "citations": [],
          "warnings": [],
          "clarification_question": null,
          "usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": null, "calls": 0 },
          "abstained": false,
          "prompt_version": null,
          "partial": true,
          "stop_reason": "fallo_proveedor",
          "iterations": 1,
          "tool_calls_used": 0,
          "trace": [],
          "agent_prompt_version": "assist/v6"
        }
        """;

    /// <summary>The route beside it, answering normally, so its circuit can be shown untouched.</summary>
    private const string SaleBody = """
        {
          "trace_id": "trace-sale-0001",
          "effective_pos_id": "44444444-4444-4444-4444-444444444444",
          "intent": "in_domain",
          "groups": [],
          "pitch": "De las tres, la más sobria es la de aro fino.",
          "citations": [],
          "warnings": [],
          "clarification_question": null,
          "usage": { "prompt_tokens": 900, "completion_tokens": 60, "total_tokens": 960,
                     "model": "openai/gpt-4o" },
          "abstained": false,
          "prompt_version": "assist/v5"
        }
        """;

    private static AiAssistAgentRequest AgentRequest(int turns = 1) =>
        new()
        {
            Turns = Enumerable.Range(0, turns)
                .Select(index => new AiAgentTurn
                {
                    Role = index % 2 == 0 ? "operario" : "asistente",
                    Text = $"turno {index}"
                })
                .ToList(),
            TopK = 5
        };

    private static AiCallScope PosScope() =>
        AiCallScope.ForPointOfSale(Guid.NewGuid(), "Operator", Guid.NewGuid());

    private static AiCallScope AllShopsScope() =>
        AiCallScope.ForAllPointsOfSale(Guid.NewGuid(), "Administrator");

    private static AiCallScope CatalogScope() =>
        AiCallScope.ForCatalog(Guid.NewGuid(), "Administrator");

    // ---------------------------------------------------------------- mapping

    [Fact]
    public async Task AssistAgentAsync_WhenServiceReturns200_MapsTheFiveNewFieldsAndTheOrigin()
    {
        var agent = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        var response = await provider.Client().AssistAgentAsync(AgentRequest(), PosScope());

        // Everything the deterministic response carries, with the same meaning.
        response.Intent.Should().Be("in_domain");
        response.TraceId.Should().Be("trace-agent-0001");
        response.PromptVersion.Should().Be("assist/v6");
        response.Pitch.Should().StartWith("De las dos");

        // And the five the agent adds.
        response.Partial.Should().BeTrue();
        response.StopReason.Should().Be("presupuesto_tools");
        response.Iterations.Should().Be(3);
        response.ToolCallsUsed.Should().Be(6);
        response.AgentPromptVersion.Should().Be("assist/v6");

        // The trace, in full and per iteration: tools, outcomes, cause, cost and duration.
        response.Trace.Should().HaveCount(3);
        response.Trace[1].Tools.Select(tool => tool.Tool)
            .Should().Equal("consultar_disponibilidad", "buscar_sustitutos");
        response.Trace[1].Tools[1].Ok.Should().BeFalse();
        response.Trace[1].Tools[1].Cause.Should().Be("presupuesto_agotado");
        response.Trace[1].TotalTokens.Should().Be(4180);
        response.Trace[1].ElapsedMs.Should().BeApproximately(1980.0, 0.01);

        // The provider-call count the shared usage object does not carry.
        response.Usage.Calls.Should().Be(4);
        response.Usage.TotalTokens.Should().Be(13116);
    }

    [Fact]
    public async Task AssistAgentAsync_CarriesTheProvenanceOfEveryGroupWithoutFlatteningIt()
    {
        var agent = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        var response = await provider.Client().AssistAgentAsync(AgentRequest(), PosScope());

        // A substitute and a match are different things to say to a customer, so neither is
        // derived from the other and neither from its position in the list.
        response.Groups.Select(group => group.Origin).Should().Equal("catalogo", "sustitutos");
        response.Groups[1].FamilyId.Should().BeNull("a null family implies exactly one member");
        response.Groups[1].Members.Should().ContainSingle().Which.Sku.Should().Be("SUB-1");
    }

    [Fact]
    public async Task AssistAgentAsync_SendsTheScopeInTheTokenAndNeverInTheBody()
    {
        var agent = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent, traceId: "trace-agent-1");
        var scope = PosScope();

        await provider.Client().AssistAgentAsync(AgentRequest(3), scope);

        var request = agent.LastRequest!;
        request.RequestUri!.AbsolutePath.Should().Be("/v1/assist/agent");

        var token = new JwtSecurityTokenHandler().ReadJwtToken(request.Headers.Authorization!.Parameter).Payload;
        token["pos_id"].Should().Be(scope.PointOfSaleId.ToString());
        token["trace_id"].Should().Be("trace-agent-1");

        using var body = JsonDocument.Parse(agent.RequestBodies.Single());
        body.RootElement.TryGetProperty("pos_id", out _).Should().BeFalse(
            "the contract accepts one and ignores it, and on this route the token is what decides "
            + "whether the availability prefilter applies at all");
        body.RootElement.GetProperty("turns").GetArrayLength().Should().Be(3);
        body.RootElement.GetProperty("turns")[0].GetProperty("role").GetString().Should().Be("operario");
        body.RootElement.GetProperty("top_k").GetInt32().Should().Be(5);
    }

    [Fact]
    public async Task AssistAgentAsync_WithTheEveryShopScope_OmitsThePointOfSaleClaim()
    {
        var agent = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        await provider.Client().AssistAgentAsync(AgentRequest(), AllShopsScope());

        var token = new JwtSecurityTokenHandler()
            .ReadJwtToken(agent.LastRequest!.Headers.Authorization!.Parameter).Payload;

        // Absence, never a wildcard: the service reads an absent claim as «do not apply the
        // availability prefilter», and a sentinel would reach the retriever's only hard filter.
        token.ContainsKey("pos_id").Should().BeFalse();
    }

    [Fact]
    public async Task AssistAgentAsync_WithACatalogScope_IsRefusedBeforeAnyCall()
    {
        var agent = new FakeHttpMessageHandler();
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        await Assert.ThrowsAsync<ArgumentException>(
            () => provider.Client().AssistAgentAsync(AgentRequest(), CatalogScope()));

        agent.RequestCount.Should().Be(0);
    }

    [Fact]
    public async Task AssistAgentAsync_WithNoTurn_IsRefusedBeforeAnyCall()
    {
        var agent = new FakeHttpMessageHandler();
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        await Assert.ThrowsAsync<ArgumentException>(
            () => provider.Client().AssistAgentAsync(
                new AiAssistAgentRequest { Turns = [] }, PosScope()));

        agent.RequestCount.Should().Be(0);
    }

    // ------------------------------------------------- its own client and its own budget

    /// <summary>
    /// <strong>The property the whole named client exists for.</strong> The agent's median latency
    /// is of the order of the total the generative route declares as its ceiling, so a client
    /// carrying the generative budget would cut a large share of agent requests.
    /// </summary>
    [Fact]
    public async Task AgentAssist_UsesItsOwnTimeoutAndNotTheAssistOne()
    {
        var time = new FakeTimeProvider();
        var agent = new FakeHttpMessageHandler().EnqueueHangUntilCancelled();
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(),
            agentHandler: agent,
            assistTimeoutMs: 10_000,
            agentTimeoutMs: 18_000,
            timeProvider: time);

        var call = provider.Client().AssistAgentAsync(AgentRequest(), PosScope());
        await agent.WaitForRequestsAsync(1);

        // Past the generative budget and short of the agent's: still in flight. A shared client
        // would have cut here, which is the failure this separation removes.
        time.Advance(TimeSpan.FromMilliseconds(12_000));
        call.IsCompleted.Should().BeFalse(
            "the agent's budget is its own, and 12 s is inside it though outside the assist one");

        time.Advance(TimeSpan.FromMilliseconds(7_000));
        await Assert.ThrowsAsync<AiUnavailableException>(() => call);
    }

    /// <summary>
    /// The budget is above the wall-clock ceiling the service gives one request, and start-up
    /// refuses anything below it.
    /// </summary>
    [Fact]
    public void AgentTimeout_SitsAboveTheServicesOwnCeiling()
    {
        var defaults = new AiGatewayOptions();

        defaults.AgentTimeoutMs.Should().BeGreaterThan(AiGatewayOptions.MinimumAgentTimeoutMs,
            "the floor is the service's ceiling; the budget adds the network margin on top");
        AiGatewayOptions.MinimumAgentTimeoutMs.Should().Be(15_000,
            "AGENT_DEADLINE_SECONDS on the Python side; if it moves, this moves with it");

        // And deliberately NOT fitted to the maximum latency observed in measurement, 11 917 ms:
        // cutting there aborts a request Python has already paid for in full.
        defaults.AgentTimeoutMs.Should().BeGreaterThan(11_917 + 3_000);
        defaults.AgentTimeoutMs.Should().NotBe(defaults.AssistTimeoutMs);
    }

    [Fact]
    public async Task AssistAgentAsync_OnATimeout_IsNotRetried()
    {
        var time = new FakeTimeProvider();
        var agent = new FakeHttpMessageHandler()
            .EnqueueHangUntilCancelled()
            .EnqueueHangUntilCancelled();
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent, timeProvider: time);

        var call = provider.Client().AssistAgentAsync(AgentRequest(), PosScope());
        await agent.WaitForRequestsAsync(1);
        time.Advance(TimeSpan.FromMilliseconds(19_000));

        await Assert.ThrowsAsync<AiUnavailableException>(() => call);

        // The loop may already have spent five turns of provider calls plus the argument: a second
        // attempt doubles both the wait at the counter and the paid calls.
        agent.RequestCount.Should().Be(1);
    }

    [Fact]
    public async Task AssistAgentAsync_OnAServerError_IsNotRetried()
    {
        var agent = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.InternalServerError);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        await Assert.ThrowsAsync<AiUnavailableException>(
            () => provider.Client().AssistAgentAsync(AgentRequest(), PosScope()));

        agent.RequestCount.Should().Be(1);
    }

    [Fact]
    public async Task AssistAgentAsync_OnAConnectionThatNeverOpened_IsRetriedOnce()
    {
        var agent = new FakeHttpMessageHandler()
            .EnqueueConnectionFailure()
            .EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);

        var response = await provider.Client().AssistAgentAsync(AgentRequest(), PosScope());

        // The one failure where the request is known not to have left, so nothing was spent.
        agent.RequestCount.Should().Be(2);
        response.StopReason.Should().Be("presupuesto_tools");
    }

    // ------------------------------------------------- the circuit, and what it must not count

    /// <summary>
    /// <strong>The decision this change turns on, as a test.</strong> A 200 reporting
    /// <c>fallo_proveedor</c> is a successful response carrying an internal degradation. A circuit
    /// that counted it would open over a route working exactly as designed.
    /// </summary>
    [Fact]
    public async Task AgentAssist_WhenProviderFails_DoesNotOpenTheCircuitOnPartial()
    {
        var agent = new FakeHttpMessageHandler()
            .AlwaysRespond(HttpStatusCode.OK, ProviderFailureBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent);
        var client = provider.Client();

        // Well past the minimum throughput of 2 the test host configures.
        for (var attempt = 0; attempt < 6; attempt++)
        {
            var response = await client.AssistAgentAsync(AgentRequest(), PosScope());

            response.StopReason.Should().Be("fallo_proveedor");
            response.Partial.Should().BeTrue();
            response.Pitch.Should().BeEmpty();
        }

        // Still answering, so the circuit never opened — and the seventh request reaches the socket.
        var issuedBefore = agent.RequestCount;
        await client.AssistAgentAsync(AgentRequest(), PosScope());
        agent.RequestCount.Should().Be(issuedBefore + 1, "the circuit stayed closed");
    }

    /// <summary>
    /// The other half of the same decision: the degradation the circuit ignores is instrumented, so
    /// its rate stays observable. Without this line the cost of that decision would be invisible.
    /// </summary>
    [Fact]
    public async Task AgentAssist_WhenProviderFails_RecordsTheDegradationAsAMetric()
    {
        var logs = new RecordingLoggerProvider();
        var agent = new FakeHttpMessageHandler()
            .EnqueueResponse(HttpStatusCode.OK, ProviderFailureBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent, logs: logs);

        await provider.Client().AssistAgentAsync(AgentRequest(), PosScope());

        var degraded = logs.Entries
            .Where(entry => entry.Message.Contains("ai_gateway_agent_degraded"))
            .ToList();

        degraded.Should().ContainSingle("the rate has to stay readable without the circuit acting");
        degraded[0].Level.Should().Be(LogLevel.Warning);
        degraded[0].Message.Should().Contain("fallo_proveedor");
    }

    [Fact]
    public async Task AgentAssist_WhenComplete_RecordsNoDegradation()
    {
        var logs = new RecordingLoggerProvider();
        var agent = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent, logs: logs);

        await provider.Client().AssistAgentAsync(AgentRequest(), PosScope());

        // `presupuesto_tools` is a budget cutting the answer short, not a degradation of the
        // service: the evidence gathered before the cut is still useful, and 2 % of requests on the
        // model that is served report it.
        logs.Entries.Should().NotContain(entry => entry.Message.Contains("ai_gateway_agent_degraded"));
    }

    [Fact]
    public async Task AssistAgentAsync_WhenItsCircuitOpens_TheGenerativeRouteKeepsWorking()
    {
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SaleBody);
        var agent = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.ServiceUnavailable);

        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist, agentHandler: agent);
        var client = provider.Client();

        for (var attempt = 0; attempt < 4; attempt++)
        {
            try
            {
                await client.AssistAgentAsync(AgentRequest(), PosScope());
            }
            catch (AiUnavailableException)
            {
                // Expected while the circuit is closing.
            }
        }

        var issuedBeforeOpenCall = agent.RequestCount;
        await Assert.ThrowsAsync<AiUnavailableException>(
            () => client.AssistAgentAsync(AgentRequest(), PosScope()));
        agent.RequestCount.Should().Be(issuedBeforeOpenCall, "the agent circuit is open");

        // And the route beside it is untouched, which is the whole reason for a client of its own.
        var sale = await client.AssistSaleAsync(
            new AiAssistSaleRequest { Query = "un anillo de plata" }, PosScope());
        sale.Should().NotBeNull();
    }

    [Fact]
    public async Task AssistAgentAsync_NeverLogsTheTranscript()
    {
        var logs = new RecordingLoggerProvider();
        var agent = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AgentBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), agentHandler: agent, logs: logs);

        var request = new AiAssistAgentRequest
        {
            Turns =
            [
                new AiAgentTurn { Role = "operario", Text = "MARCA-SECRETA-DEL-CLIENTE" }
            ]
        };

        await provider.Client().AssistAgentAsync(request, PosScope());

        // What a customer said at a counter, and the argument that carries it back. Neither is
        // persisted anywhere, a log included: the no-persistence rule covers both.
        logs.Entries.Should().NotContain(entry => entry.Message.Contains("MARCA-SECRETA-DEL-CLIENTE"));
        logs.Entries.Should().NotContain(entry => entry.Message.Contains("De las dos"));
    }
}
