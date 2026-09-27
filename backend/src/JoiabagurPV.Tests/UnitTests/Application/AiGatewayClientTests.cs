using System.IdentityModel.Tokens.Jwt;
using System.Net;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Application.Services;
using JoiabagurPV.Tests.TestHelpers;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// Exercises the gateway against the real resilience pipeline with a fake socket underneath.
/// No jbg-ai container, no network.
/// </summary>
public class AiGatewayClientTests
{
    private const string SuccessBody = """
        {
          "results": [
            {
              "product_id": "11111111-1111-1111-1111-111111111111",
              "sku": "ERIZO-M",
              "score": 0.87,
              "match_reasons": ["material", "piece_type"],
              "materials": ["plata", "baño de oro"],
              "family_id": "22222222-2222-2222-2222-222222222222",
              "variant_label": "M",
              "debug": { "vector_score": 0.9, "lexical_score": 0.4, "rerank_score": null, "notes": ["stub"] }
            },
            {
              "product_id": "33333333-3333-3333-3333-333333333333",
              "sku": "ANILLO-S",
              "score": 0.61,
              "match_reasons": ["piece_type"],
              "materials": ["plata"],
              "family_id": null,
              "variant_label": null,
              "debug": null
            }
          ],
          "candidates_returned": 2,
          "low_confidence": false,
          "trace_id": "trace-test-0001",
          "effective_pos_id": "44444444-4444-4444-4444-444444444444"
        }
        """;

    private static AiSearchRequest AnyRequest() => new()
    {
        Query = "anillo de plata para regalo",
        TopK = 5,
        Filters = new AiSearchFilters { Materials = ["plata"] }
    };

    private static AiCallScope AnyScope() =>
        AiCallScope.ForPointOfSale(Guid.NewGuid(), "Operator", Guid.NewGuid());

    [Fact]
    public async Task SearchAsync_WhenServiceReturns200_MapsResponse()
    {
        var handler = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);

        var response = await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        response.CandidatesReturned.Should().Be(2);
        response.LowConfidence.Should().BeFalse();
        response.TraceId.Should().Be("trace-test-0001");
        response.EffectivePosId.Should().Be("44444444-4444-4444-4444-444444444444");

        var first = response.Results[0];
        first.ProductId.Should().Be("11111111-1111-1111-1111-111111111111");
        first.Sku.Should().Be("ERIZO-M");
        first.Score.Should().BeApproximately(0.87, 0.001);
        first.MatchReasons.Should().BeEquivalentTo(["material", "piece_type"]);
        first.Materials.Should().BeEquivalentTo(["plata", "baño de oro"]);
        first.VariantLabel.Should().Be("M");
        first.Debug!.VectorScore.Should().BeApproximately(0.9, 0.001);
    }

    [Fact]
    public async Task SearchAsync_WhenFamilyIdIsNull_MapsToNullWithoutThrowing()
    {
        var handler = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);

        var response = await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        var second = response.Results[1];
        second.FamilyId.Should().BeNull();
        second.VariantLabel.Should().BeNull();
        second.Debug.Should().BeNull();
    }

    /// <summary>
    /// The service over-fetches so the caller has margin after hydrating and discarding.
    /// Truncating here would silently starve that caller.
    /// </summary>
    [Fact]
    public async Task SearchAsync_WhenServiceOverFetches_ReturnsEveryCandidate()
    {
        var handler = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);

        var request = AnyRequest();
        request.TopK = 1;

        var response = await provider.Client().SearchAsync(request, AnyScope());

        response.Results.Should().HaveCount(2, "the client must not truncate to top_k");
    }

    [Fact]
    public async Task SearchAsync_SendsBearerTokenAndTraceHeader()
    {
        var handler = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler, traceId: "trace-xyz-999");
        var scope = AnyScope();

        await provider.Client().SearchAsync(AnyRequest(), scope);

        var request = handler.LastRequest!;
        request.RequestUri!.AbsolutePath.Should().Be("/v1/retrieval/products");
        request.Headers.Authorization!.Scheme.Should().Be("Bearer");
        request.Headers.GetValues(AiGatewayClient.TraceHeaderName).Should().ContainSingle()
            .Which.Should().Be("trace-xyz-999");

        var payload = new JwtSecurityTokenHandler()
            .ReadJwtToken(request.Headers.Authorization.Parameter).Payload;

        payload["trace_id"].Should().Be("trace-xyz-999");
        payload["pos_id"].Should().Be(scope.PointOfSaleId.ToString());
    }

    [Fact]
    public async Task SearchAsync_WhenTimeout_ThrowsAiUnavailable()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SuccessBody);
        handler.EnqueueHang().EnqueueHang();
        await using var provider = AiGatewayTestHost.Build(handler, retrievalTimeoutMs: 60);

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        await act.Should().ThrowAsync<AiUnavailableException>();
    }

    /// <summary>
    /// Two failing calls fill the sampling window and open the circuit; the third must not
    /// reach the socket at all. The thresholds are set low on purpose — with the framework
    /// defaults the circuit never opens and this test would pass without testing anything.
    /// </summary>
    [Fact]
    public async Task SearchAsync_WhenCircuitOpen_FailsFastWithoutCall()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.ServiceUnavailable);
        await using var provider = AiGatewayTestHost.Build(handler);
        var client = provider.Client();

        await Assert.ThrowsAsync<AiUnavailableException>(
            () => client.SearchAsync(AnyRequest(), AnyScope()));

        var requestsBeforeCircuitOpened = handler.RequestCount;

        await Assert.ThrowsAsync<AiUnavailableException>(
            () => client.SearchAsync(AnyRequest(), AnyScope()));

        handler.RequestCount.Should().Be(
            requestsBeforeCircuitOpened,
            "with the circuit open no request may leave the process");
    }

    /// <summary>
    /// jbg-ai answers 501 for a route whose implementation lands in a later change. Retrying it
    /// spends the budget for nothing, which is why the contract uses 501 and not 503.
    /// </summary>
    [Fact]
    public async Task SearchAsync_WhenServiceReturns501_DoesNotRetryAndThrowsNotImplemented()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.NotImplemented);
        await using var provider = AiGatewayTestHost.Build(handler);

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        await act.Should().ThrowAsync<AiNotImplementedException>();
        handler.RequestCount.Should().Be(1, "a route with no implementation must not be retried");
    }

    [Fact]
    public async Task SearchAsync_WhenServiceReturns401_DoesNotRetry()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.Unauthorized);
        await using var provider = AiGatewayTestHost.Build(handler);

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        await act.Should().ThrowAsync<AiGatewayConfigurationException>();
        handler.RequestCount.Should().Be(1, "a mismatched secret is not fixed by trying again");
    }

    /// <summary>
    /// C34 reads a 422 as a rejection on sale assistance and substitutes only. The translation is
    /// shared by the whole client, and every other operation keeps reading it as unavailability.
    /// </summary>
    [Fact]
    public async Task SearchAsync_When422_StillThrowsUnavailable()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.UnprocessableEntity);
        await using var provider = AiGatewayTestHost.Build(handler);

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        (await act.Should().ThrowAsync<AiUnavailableException>())
            .Which.Should().NotBeOfType<AiRequestRejectedException>();
        handler.RequestCount.Should().Be(1, "a 4xx other than 408 is not retried");
    }

    [Fact]
    public async Task SearchAsync_WhenServiceReturns503_RetriesOnceThenSucceeds()
    {
        var handler = new FakeHttpMessageHandler()
            .EnqueueResponse(HttpStatusCode.ServiceUnavailable)
            .EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);

        var response = await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        response.CandidatesReturned.Should().Be(2);
        handler.RequestCount.Should().Be(2, "a transient server error is worth exactly one more attempt");
    }

    [Fact]
    public async Task SearchAsync_WhenTransportFails_ThrowsAiUnavailableAfterOneRetry()
    {
        var handler = new FakeHttpMessageHandler()
            .EnqueueTransportFailure()
            .EnqueueTransportFailure();
        await using var provider = AiGatewayTestHost.Build(handler);

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        await act.Should().ThrowAsync<AiUnavailableException>();
        handler.RequestCount.Should().Be(2);
    }

    /// <summary>
    /// The completion event is what answers "how long did it take and how many attempts did it
    /// cost" when someone asks why a search felt slow. A log line that cannot answer that is
    /// close to useless.
    /// </summary>
    [Fact]
    public async Task SearchAsync_WhenCallCompletes_EmitsCompletionEventWithLatencyAndCounts()
    {
        var logs = new RecordingLoggerProvider();
        var handler = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler, traceId: "trace-log-001", logs: logs);

        await provider.Client().SearchAsync(AnyRequest(), AnyScope());

        logs.Has("ai_gateway_call_started").Should().BeTrue();

        var completed = logs.Single("ai_gateway_call_completed");
        completed.Level.Should().Be(LogLevel.Information);
        completed.Property("StatusCode").Should().Be(200);
        completed.Property("Attempts").Should().Be(1);
        completed.Property("CandidatesReturned").Should().Be(2);
        completed.Property("ResultsCount").Should().Be(2);
        completed.Property("LowConfidence").Should().Be(false);
        completed.Property("LatencyMs").Should().NotBeNull();

        // The correlation identifier and the endpoint are bound once per call, not repeated.
        completed.ScopeValue("trace_id").Should().Be("trace-log-001");
        completed.ScopeValue("endpoint").Should().Be("/v1/retrieval/products");

        logs.Has("ai_gateway_call_failed").Should().BeFalse();
    }

    /// <summary>
    /// base_url rides on the failure event alone. Start-up validation catches a key that is
    /// absent or malformed, never one that is present and stale, so when a call fails the first
    /// useful question is where it was pointing.
    /// </summary>
    [Fact]
    public async Task SearchAsync_WhenCallFails_EmitsFailureEventWithOutcomeAndBaseUrl()
    {
        var logs = new RecordingLoggerProvider();
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.Unauthorized);
        await using var provider = AiGatewayTestHost.Build(handler, traceId: "trace-log-002", logs: logs);

        await Assert.ThrowsAsync<AiGatewayConfigurationException>(
            () => provider.Client().SearchAsync(AnyRequest(), AnyScope()));

        var failed = logs.Single("ai_gateway_call_failed");
        failed.Property("Outcome").Should().Be("unauthorized");
        failed.Property("BaseUrl").Should().Be("http://localhost:8001");
        failed.Property("Attempts").Should().Be(1);
        failed.Property("LatencyMs").Should().NotBeNull();
        failed.ScopeValue("trace_id").Should().Be("trace-log-002");

        // A rejected token is configuration, and configuration faults deserve error level.
        failed.Level.Should().Be(LogLevel.Error);

        logs.Has("ai_gateway_call_completed").Should().BeFalse();
    }

    /// <summary>
    /// Privacy rule from the design: the operator's query is free text that may accidentally
    /// carry personal data, and production logs are not the place to discover that. It is
    /// recorded at debug level and must never surface above it — a constraint that survives
    /// only if something asserts it.
    /// </summary>
    [Fact]
    public async Task SearchAsync_QueryTextNeverRisesAboveDebug()
    {
        var logs = new RecordingLoggerProvider();
        var handler = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler, logs: logs);

        var request = AnyRequest();
        await provider.Client().SearchAsync(request, AnyScope());

        logs.At(LogLevel.Debug).Should().Contain(e => e.Mentions(request.Query),
            "the query is still recorded, just where it belongs");

        logs.Entries
            .Where(e => e.Level >= LogLevel.Information)
            .Should().NotContain(e => e.Mentions(request.Query),
                "no event at information level or above may carry the operator's query text");

        // What does travel upwards is its length, which is diagnostic without being personal.
        logs.Single("ai_gateway_call_started").Property("QueryLength")
            .Should().Be(request.Query.Length);
    }

    /// <summary>
    /// The first of two independent closures on the point-of-sale boundary.
    /// </summary>
    /// <remarks>
    /// The catalog scope exists so enrichment does not have to invent a point of sale. From C22
    /// onward the `pos_id` claim is the retriever's only hard filter, so letting that scope
    /// reach retrieval would be a cross-point-of-sale leak. jbg-ai refuses it as well; neither
    /// side is trusted to be the only one that remembers.
    /// </remarks>
    [Fact]
    public async Task SearchAsync_WithCatalogScope_IsRejected()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);
        var catalogScope = AiCallScope.ForCatalog(Guid.NewGuid(), "Administrator");

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), catalogScope);

        await act.Should().ThrowAsync<ArgumentException>()
            .WithParameterName("scope");

        handler.Requests.Should().BeEmpty(
            "the scope is refused before anything leaves the process");
    }

    // --- C40 · the third scope, and the two routes that take it ---------------------------

    /// <summary>
    /// Retrieval and sale assistance can answer without a shop, so they take it. The list is
    /// closed: every other point-of-sale operation refuses it below.
    /// </summary>
    [Fact]
    public async Task ForAllPointsOfSale_IsAcceptedByRetrievalAndAssistance()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);
        var everyShop = AiCallScope.ForAllPointsOfSale(Guid.NewGuid(), "Operator");

        var act = async () => await provider.Client().SearchAsync(AnyRequest(), everyShop);

        await act.Should().NotThrowAsync<ArgumentException>();
        handler.Requests.Should().NotBeEmpty(
            "the request is issued: an absent pos_id makes the prefilter not apply, and the "
            + "service reads it that way rather than as a wildcard");
    }

    /// <summary>
    /// **No exception here, and the reason is what substitutes are for.** They rank by what a
    /// shop can actually hand over, so with no shop the ranking has nothing to read and the
    /// answer would be to a different question from the one asked.
    /// </summary>
    [Fact]
    public async Task ForAllPointsOfSale_IsRefusedBySubstitutes()
    {
        var handler = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SuccessBody);
        await using var provider = AiGatewayTestHost.Build(handler);
        var everyShop = AiCallScope.ForAllPointsOfSale(Guid.NewGuid(), "Operator");

        var act = async () => await provider.Client().SubstitutesAsync(
            new AiSubstitutesRequest { ProductId = Guid.NewGuid().ToString(), TopK = 5 },
            everyShop);

        await act.Should().ThrowAsync<ArgumentException>()
            .WithParameterName("scope");

        handler.Requests.Should().BeEmpty(
            "refused before any request is issued, like the catalog scope above");
    }

    /// <summary>
    /// The inventory refusal the specification also asks for has **no .NET surface to be
    /// asserted on**, and that is recorded here rather than left as a missing test.
    /// </summary>
    /// <remarks>
    /// `/v1/inventory/propose` exists on jbg-ai and this client has no operation for it: nothing
    /// in .NET calls that route. The equivalent guarantee is enforced on the service side, where
    /// the route keeps the strict claims dependency and rejects a token with no `pos_id` —
    /// asserted by `test_pos_scoped_route_still_rejects_it` in `tests/api/test_auth.py`.
    ///
    /// What this test can assert is the property that makes the absence safe: the client's
    /// point-of-sale operations are exactly the three below, so there is no fourth one quietly
    /// taking a scope nobody checked.
    /// </remarks>
    [Fact]
    public void ForAllPointsOfSale_IsRefusedByInventory_HasNoClientSurface()
    {
        typeof(IAiGatewayClient)
            .GetMethods()
            .Select(method => method.Name)
            .Should().NotContain(name => name.Contains("Inventory", StringComparison.Ordinal),
                "if this client ever grows an inventory call, it needs its own scope refusal "
                + "and this test should become that refusal");
    }
}
