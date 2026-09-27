using System.IdentityModel.Tokens.Jwt;
using System.Net;
using System.Text.Json;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Exceptions;
using JoiabagurPV.Tests.TestHelpers;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Time.Testing;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// The two operations C34 adds to the gateway — sale assistance and substitutes — against the
/// real resilience pipelines with a fake socket underneath.
/// </summary>
/// <remarks>
/// What these assert that a mock could not: which client each operation rides on, what the
/// generative pipeline retries and what it does not, and that its circuit is its own. Those are
/// properties of the registration, and a hand-rolled stand-in would test the stand-in.
/// </remarks>
public class AiGatewayAssistTests
{
    private const string AnchorId = "11111111-1111-1111-1111-111111111111";

    /// <summary>The pitch as the service writes it: prose with the two placeholders unresolved.</summary>
    private const string PitchTemplate =
        "Pendientes de plata de ley con cierre de presión, disponibles por {{price}} y tenemos {{stock}} en tienda.";

    private const string AssistBody = $$"""
        {
          "trace_id": "trace-test-0001",
          "effective_pos_id": "44444444-4444-4444-4444-444444444444",
          "intent": "product_pitch",
          "groups": [
            {
              "family_id": "22222222-2222-2222-2222-222222222222",
              "family_label": "Pendiente erizo",
              "members": [
                { "product_id": "{{AnchorId}}", "sku": "ERIZO-M", "variant_label": "M",
                  "materials": ["plata"], "score": 0.9, "match_reasons": ["anchor"] },
                { "product_id": "33333333-3333-3333-3333-333333333333", "sku": "ERIZO-S", "variant_label": null,
                  "materials": ["plata"], "score": 0.8, "match_reasons": ["family"] }
              ]
            },
            { "family_id": null, "family_label": null, "members": [
                { "product_id": "55555555-5555-5555-5555-555555555555", "sku": "SOLO-1", "variant_label": null,
                  "materials": [], "score": 0.5, "match_reasons": [] } ] }
          ],
          "pitch": "{{PitchTemplate}}",
          "citations": [
            { "citation_id": "garantia#devoluciones", "document_title": "Garantía", "section_title": "Devoluciones",
              "doc_type": "politica", "claim_scope": "establecimiento", "score": 0.71, "snippet": "Quince días.",
              "product_id": "{{AnchorId}}" },
            { "citation_id": "plata#cuidados", "document_title": "Plata", "section_title": "Cuidados",
              "doc_type": "material", "claim_scope": "general", "score": 0.66, "snippet": "Evitar el agua.",
              "product_id": null }
          ],
          "warnings": ["family_has_variants", "size_label_missing"],
          "clarification_question": null,
          "usage": { "prompt_tokens": 1200, "completion_tokens": 80, "total_tokens": 1280, "model": "openai/gpt-4o-mini" },
          "abstained": false,
          "prompt_version": "assist/v4"
        }
        """;

    private const string SubstitutesBody = """
        {
          "results": [
            { "product_id": "66666666-6666-6666-6666-666666666666", "sku": "SUB-1", "score": 0.8,
              "match_reasons": ["style"], "materials": ["plata"], "family_id": null, "variant_label": null,
              "similarity_signals": { "family_match": false, "material_overlap": 1.0, "style_similarity": 0.7, "visual_similarity": null },
              "debug": null },
            { "product_id": "77777777-7777-7777-7777-777777777777", "sku": "SUB-2", "score": 0.7,
              "match_reasons": [], "materials": [], "family_id": "88888888-8888-8888-8888-888888888888", "variant_label": "S",
              "similarity_signals": { "family_match": true, "material_overlap": 0.5, "style_similarity": 0.4 },
              "debug": { "vector_score": null, "lexical_score": null, "rerank_score": null, "notes": ["projection_age_s=12"] } },
            { "product_id": "99999999-9999-9999-9999-999999999999", "sku": "SUB-3", "score": 0.6,
              "match_reasons": [], "materials": [], "family_id": null, "variant_label": null,
              "similarity_signals": { "family_match": false, "material_overlap": 0.0, "style_similarity": 0.3 },
              "debug": null }
          ],
          "candidates_returned": 3,
          "low_confidence": false,
          "trace_id": "trace-test-0001",
          "effective_pos_id": "44444444-4444-4444-4444-444444444444"
        }
        """;

    private static AiAssistSaleRequest AssistRequest(string? question = null) =>
        new() { ProductId = AnchorId, Query = question };

    private static AiSubstitutesRequest SubstitutesRequest(int topK = 1) =>
        new() { ProductId = AnchorId, TopK = topK };

    private static AiCallScope PosScope() =>
        AiCallScope.ForPointOfSale(Guid.NewGuid(), "Operator", Guid.NewGuid());

    private static AiCallScope CatalogScope() =>
        AiCallScope.ForCatalog(Guid.NewGuid(), "Administrator");

    // ---------------------------------------------------------------- sale assistance: mapping

    [Fact]
    public async Task AssistSaleAsync_WhenServiceReturns200_MapsResponseInFull()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var response = await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        response.Intent.Should().Be("product_pitch");
        response.TraceId.Should().Be("trace-test-0001");
        response.EffectivePosId.Should().Be("44444444-4444-4444-4444-444444444444");
        response.Pitch.Should().Be(PitchTemplate, "the client resolves nothing; that is the caller's job");
        response.PromptVersion.Should().Be("assist/v4");
        response.Abstained.Should().BeFalse();
        response.Warnings.Should().Equal("family_has_variants", "size_label_missing");
        response.Usage.TotalTokens.Should().Be(1280);
        response.Usage.Model.Should().Be("openai/gpt-4o-mini");

        response.Groups.Should().HaveCount(2);
        response.Groups[0].Members.Select(m => m.Sku).Should().Equal("ERIZO-M", "ERIZO-S");

        response.Citations.Should().HaveCount(2);
        response.Citations[0].ClaimScope.Should().Be("establecimiento");
        response.Citations[0].DocType.Should().Be("politica");
        response.Citations[0].SectionTitle.Should().Be("Devoluciones");
        response.Citations[1].ClaimScope.Should().Be("general");
    }

    [Fact]
    public async Task AssistSaleAsync_ContractNulls_SurviveMapping()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var response = await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        response.Groups[1].FamilyId.Should().BeNull();
        response.Groups[1].FamilyLabel.Should().BeNull();
        response.Groups[0].Members[1].VariantLabel.Should().BeNull();
        response.ClarificationQuestion.Should().BeNull();
        response.Citations[1].ProductId.Should().BeNull();
    }

    [Fact]
    public async Task AssistSaleAsync_SendsThePointOfSaleInTheTokenAndNeverInTheBody()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist, traceId: "trace-assist-1");
        var scope = PosScope();

        await provider.Client().AssistSaleAsync(AssistRequest("¿se puede mojar?"), scope);

        var request = assist.LastRequest!;
        request.RequestUri!.AbsolutePath.Should().Be("/v1/assist/sale");

        var token = new JwtSecurityTokenHandler().ReadJwtToken(request.Headers.Authorization!.Parameter).Payload;
        token["pos_id"].Should().Be(scope.PointOfSaleId.ToString());
        token["trace_id"].Should().Be("trace-assist-1");

        using var body = JsonDocument.Parse(assist.RequestBodies.Single());
        body.RootElement.TryGetProperty("pos_id", out _).Should().BeFalse();
        body.RootElement.GetProperty("product_id").GetString().Should().Be(AnchorId);
        body.RootElement.GetProperty("query").GetString().Should().Be("¿se puede mojar?");
    }

    [Fact]
    public async Task AssistSaleAsync_WithFilters_SerializesThemWithContractNames()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist);

        var request = AssistRequest();
        request.Filters = new AiSearchFilters
        {
            Materials = ["plata", "oro"],
            Category = "pendientes",
            FamilyId = "22222222-2222-2222-2222-222222222222",
            ExcludeProductIds = ["99999999-9999-9999-9999-999999999999"]
        };

        await provider.Client().AssistSaleAsync(request, PosScope());

        using var body = JsonDocument.Parse(assist.RequestBodies.Single());
        var filters = body.RootElement.GetProperty("filters");

        // snake_case, from the single naming policy rather than from per-property attributes.
        // A mistyped name here would not fail to compile: it would arrive as a field the
        // service does not know and be dropped, and the filter would silently not apply —
        // which is the exact failure mode this whole change exists to remove.
        filters.GetProperty("materials").EnumerateArray()
            .Select(material => material.GetString()).Should().Equal("plata", "oro");
        filters.GetProperty("category").GetString().Should().Be("pendientes");
        filters.GetProperty("family_id").GetString().Should()
            .Be("22222222-2222-2222-2222-222222222222");
        filters.GetProperty("exclude_product_ids").EnumerateArray()
            .Select(id => id.GetString()).Should().Equal("99999999-9999-9999-9999-999999999999");
    }

    /// <remarks>
    /// The shape follows <c>AiSubstitutesRequest</c>, which carries the same contract field the
    /// same way: the contract declares <c>filters</c> with a **default** rather than as nullable,
    /// and <c>AiContractSnapshotTests</c> holds the .NET model and the schema in nullability
    /// parity. A nullable property omitted when empty reads more frugal and breaks that parity,
    /// which is how this was caught — the guard fired on the first full run.
    ///
    /// Nothing is lost by sending it: an empty filter set and an absent property mean the same
    /// thing to the service, which defaults the field either way.
    /// </remarks>
    [Fact]
    public async Task AssistSaleAsync_WithoutFilters_SendsAnEmptyFilterSet()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist);

        await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        using var body = JsonDocument.Parse(assist.RequestBodies.Single());
        var filters = body.RootElement.GetProperty("filters");

        filters.GetProperty("materials").GetArrayLength().Should().Be(0);
        filters.GetProperty("category").ValueKind.Should().Be(JsonValueKind.Null);
        filters.GetProperty("family_id").ValueKind.Should().Be(JsonValueKind.Null);
        filters.GetProperty("exclude_product_ids").GetArrayLength().Should().Be(0);
    }

    /// <remarks>
    /// The free query is the third of the three modes and the only one an operator could not
    /// reach. This client refused it until C40, for a reason that was sound while it held: the
    /// generated argument carried placeholders naming no product, and the resolver withholds
    /// the whole argument rather than guess which piece a price belongs to.
    ///
    /// `assist/v5` stops asking for placeholders in the free-query tasks, and the hard cause
    /// `placeholder_in_free_query` makes that a guarantee instead of a request — so the refusal
    /// now protects nothing and only costs the mode.
    /// </remarks>
    [Fact]
    public async Task AssistSaleAsync_WithQueryAndNoProduct_IssuesTheRequest()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist);

        var response = await provider.Client().AssistSaleAsync(
            new AiAssistSaleRequest { Query = "¿la plata se puede mojar?" }, PosScope());

        response.Should().NotBeNull();

        using var body = JsonDocument.Parse(assist.RequestBodies.Single());
        body.RootElement.GetProperty("query").GetString().Should().Be("¿la plata se puede mojar?");
        body.RootElement.GetProperty("product_id").ValueKind.Should().Be(JsonValueKind.Null,
            "a free query anchors no piece, and the contract declares the field nullable");
    }

    [Fact]
    public async Task AssistSaleAsync_WithNeitherAnchor_ThrowsBeforeAnyRequest()
    {
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist);

        var act = async () => await provider.Client().AssistSaleAsync(
            new AiAssistSaleRequest(), PosScope());

        // Still refused, and still before the socket: the contract requires at least one anchor,
        // so a request carrying neither is a programming error rather than a paid round trip.
        await act.Should().ThrowAsync<ArgumentException>();
        assist.RequestCount.Should().Be(0);
    }

    [Fact]
    public async Task AssistSaleAsync_WithCatalogScope_IsRejected()
    {
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var act = async () => await provider.Client().AssistSaleAsync(AssistRequest(), CatalogScope());

        await act.Should().ThrowAsync<ArgumentException>().WithParameterName("scope");
        assist.Requests.Should().BeEmpty("the scope is refused before anything leaves the process");
    }

    /// <summary>
    /// The free-query mode now reaches the service through this client. **This test asserted the
    /// opposite until C40**, and the reversal is the point of that change rather than a slip.
    /// </summary>
    /// <remarks>
    /// What it used to say: "the free-query mode exists in the contract and not through this
    /// client, because its placeholders have no product to be resolved against". True, and the
    /// refusal was the right call while the argument carried placeholders — withholding is
    /// better than resolving a price against the wrong piece.
    ///
    /// What changed is the other end of the chain, not this opinion of it: `assist/v5` stops
    /// asking for placeholders in the three free-query tasks, and the hard cause
    /// `placeholder_in_free_query` turns that request into a guarantee. With nothing to resolve,
    /// the refusal stopped protecting anything and only kept the one mode of the three that an
    /// operator had no way to reach.
    /// </remarks>
    [Fact]
    public async Task AssistSaleAsync_WithoutProduct_ReachesTheServiceSinceTheArgumentCarriesNoPlaceholder()
    {
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var response = await provider.Client().AssistSaleAsync(
            new AiAssistSaleRequest { ProductId = null, Query = "anillos de plata" }, PosScope());

        response.Should().NotBeNull();
        assist.Requests.Should().ContainSingle();
    }

    // ---------------------------------------------------------------- sale assistance: failures

    /// <summary>
    /// A product created after the last synchronisation is not an outage, and must not read as one.
    /// </summary>
    [Fact]
    public async Task AssistSaleAsync_When422_ThrowsRequestRejected_NotUnavailable()
    {
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.UnprocessableEntity);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var act = async () => await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        (await act.Should().ThrowAsync<AiRequestRejectedException>()).Which.StatusCode.Should().Be(422);
        assist.RequestCount.Should().Be(1, "a request the service cannot process is not retried");
    }

    /// <summary>
    /// The budget really expires here — the handler waits until the pipeline cancels it — so the
    /// timeout strategy is what fails the attempt, and the retry predicate sees exactly what it
    /// would see in production. The clock is fake because the start-up floor forbids a budget
    /// short enough to wait out.
    /// </summary>
    [Fact]
    public async Task AssistSaleAsync_WhenTimeout_DoesNotRetry()
    {
        var logs = new RecordingLoggerProvider();
        var time = new FakeTimeProvider();
        var assist = new FakeHttpMessageHandler()
            .EnqueueHangUntilCancelled()
            .AlwaysRespond(HttpStatusCode.OK, AssistBody);

        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist, timeProvider: time, logs: logs);

        var call = provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        await assist.WaitForRequestsAsync(1);
        time.Advance(TimeSpan.FromMilliseconds(10_001));

        var act = async () => await call;

        await act.Should().ThrowAsync<AiUnavailableException>();
        assist.RequestCount.Should().Be(1,
            "a second attempt would double both the wait at the counter and the paid model calls");
        logs.Single("ai_gateway_call_failed").Property("Outcome").Should().Be("timeout");
    }

    [Fact]
    public async Task AssistSaleAsync_When503_DoesNotRetry()
    {
        var assist = new FakeHttpMessageHandler()
            .EnqueueResponse(HttpStatusCode.ServiceUnavailable)
            .AlwaysRespond(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var act = async () => await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        await act.Should().ThrowAsync<AiUnavailableException>();
        assist.RequestCount.Should().Be(1,
            "a server error may come after generation began; retrying it pays the provider twice");
    }

    [Fact]
    public async Task AssistSaleAsync_WhenConnectionNeverOpened_RetriesOnce()
    {
        var assist = new FakeHttpMessageHandler()
            .EnqueueConnectionFailure()
            .EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var response = await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        response.Intent.Should().Be("product_pitch");
        assist.RequestCount.Should().Be(2,
            "a connection that never opened is the one failure where nothing was spent");
    }

    /// <summary>
    /// The complement of the test above: a transport failure whose cause is not a connection
    /// that never opened may have happened after the request left, so it is not retried.
    /// </summary>
    [Fact]
    public async Task AssistSaleAsync_WhenTransportFailsAfterConnecting_DoesNotRetry()
    {
        var assist = new FakeHttpMessageHandler()
            .EnqueueTransportFailure()
            .AlwaysRespond(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var act = async () => await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        await act.Should().ThrowAsync<AiUnavailableException>();
        assist.RequestCount.Should().Be(1);
    }

    [Fact]
    public async Task AssistSaleAsync_WhenBodyDoesNotMatchContract_ThrowsUnavailable()
    {
        var assist = new FakeHttpMessageHandler().EnqueueResponse(
            HttpStatusCode.OK, """{ "groups": [ { "members": [ { "score": 0.5 } ] } ] }""");
        await using var provider = AiGatewayTestHost.Build(new FakeHttpMessageHandler(), assistHandler: assist);

        var act = async () => await provider.Client().AssistSaleAsync(AssistRequest(), PosScope());

        await act.Should().ThrowAsync<AiUnavailableException>(
            "a serializer exception would escape every catch the caller writes against the gateway");
    }

    /// <summary>
    /// A slow or failing language model must not push every operator's search onto the lexical
    /// fallback: the generative circuit is its own.
    /// </summary>
    [Fact]
    public async Task AssistSaleAsync_WhenItsCircuitOpens_RetrievalKeepsWorking()
    {
        var retrieval = new FakeHttpMessageHandler()
            .AlwaysRespond(HttpStatusCode.OK, AiGatewayClientTestBodies.RetrievalSuccess);
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.ServiceUnavailable);

        await using var provider = AiGatewayTestHost.Build(retrieval, assistHandler: assist);
        var client = provider.Client();

        // Minimum throughput is 2 in the test host.
        for (var attempt = 0; attempt < 4; attempt++)
        {
            try
            {
                await client.AssistSaleAsync(AssistRequest(), PosScope());
            }
            catch (AiUnavailableException)
            {
                // Expected while the circuit is closing.
            }
        }

        var issuedBeforeOpenCall = assist.RequestCount;
        await Assert.ThrowsAsync<AiUnavailableException>(
            () => client.AssistSaleAsync(AssistRequest(), PosScope()));
        assist.RequestCount.Should().Be(issuedBeforeOpenCall, "the assist circuit is open");

        var search = await client.SearchAsync(
            new AiSearchRequest { Query = "anillo de plata", TopK = 2 }, PosScope());
        search.Results.Should().NotBeEmpty("retrieval must keep answering while the assist circuit is open");

        retrieval.RequestCount.Should().Be(1);
    }

    // ---------------------------------------------------------------- sale assistance: logs

    /// <summary>
    /// The argument never reaches a log at any level: resolved, it carries the real price, which
    /// the placeholder mechanism exists to keep out of generated text. The question stays at debug.
    /// </summary>
    [Fact]
    public async Task AssistSaleAsync_CompletionEvent_CarriesNoArgumentText()
    {
        const string question = "¿Mi hija es alérgica al níquel, le vale?";
        var logs = new RecordingLoggerProvider();
        var assist = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(
            new FakeHttpMessageHandler(), assistHandler: assist, logs: logs, traceId: "trace-assist-log");

        await provider.Client().AssistSaleAsync(AssistRequest(question), PosScope());

        var completed = logs.Single("ai_gateway_assist_completed");
        completed.Level.Should().Be(LogLevel.Information);
        completed.Property("PitchLength").Should().Be(PitchTemplate.Length);
        completed.Property("PromptVersion").Should().Be("assist/v4");
        completed.Property("TotalTokens").Should().Be(1280);
        completed.ScopeValue("trace_id").Should().Be("trace-assist-log");
        completed.ScopeValue("endpoint").Should().Be("/v1/assist/sale");

        logs.Entries.Should().NotContain(e => e.Mentions("disponibles por"),
            "no event at any level may carry the argument");

        logs.At(LogLevel.Debug).Should().Contain(e => e.Mentions(question));
        logs.Entries.Where(e => e.Level > LogLevel.Debug)
            .Should().NotContain(e => e.Mentions(question), "the question never rises above debug");
    }

    // ---------------------------------------------------------------- substitutes

    [Fact]
    public async Task SubstitutesAsync_WhenServiceReturns200_ReturnsTheWholeWindowInOrder()
    {
        var retrieval = new FakeHttpMessageHandler().EnqueueResponse(HttpStatusCode.OK, SubstitutesBody);
        await using var provider = AiGatewayTestHost.Build(retrieval);

        var response = await provider.Client().SubstitutesAsync(SubstitutesRequest(topK: 1), PosScope());

        response.Results.Select(r => r.Sku).Should().Equal(["SUB-1", "SUB-2", "SUB-3"],
            "the window is larger than the page on purpose; excluding and truncating belong to the caller");
        response.CandidatesReturned.Should().Be(3);
        response.Results[0].SimilaritySignals.MaterialOverlap.Should().Be(1.0);
        response.Results[0].SimilaritySignals.VisualSimilarity.Should().BeNull();
        response.Results[1].SimilaritySignals.FamilyMatch.Should().BeTrue();
        response.Results[1].Debug!.Notes.Should().Contain("projection_age_s=12");

        retrieval.LastRequest!.RequestUri!.AbsolutePath.Should().Be("/v1/retrieval/substitutes");
        using var body = JsonDocument.Parse(retrieval.RequestBodies.Single());
        body.RootElement.TryGetProperty("pos_id", out _).Should().BeFalse();
    }

    [Fact]
    public async Task SubstitutesAsync_WithCatalogScope_IsRejected()
    {
        var retrieval = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SubstitutesBody);
        await using var provider = AiGatewayTestHost.Build(retrieval);

        var act = async () => await provider.Client().SubstitutesAsync(SubstitutesRequest(), CatalogScope());

        await act.Should().ThrowAsync<ArgumentException>().WithParameterName("scope");
        retrieval.Requests.Should().BeEmpty();
    }

    [Fact]
    public async Task SubstitutesAsync_When422_ThrowsRequestRejected_NotUnavailable()
    {
        var retrieval = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.UnprocessableEntity);
        await using var provider = AiGatewayTestHost.Build(retrieval);

        var act = async () => await provider.Client().SubstitutesAsync(SubstitutesRequest(), PosScope());

        await act.Should().ThrowAsync<AiRequestRejectedException>();
        retrieval.RequestCount.Should().Be(1, "a request the service cannot process is not retried");
    }

    /// <summary>
    /// Substitutes share retrieval's failure domain, and therefore its circuit: with it open, no
    /// substitutes request leaves the process either.
    /// </summary>
    [Fact]
    public async Task SubstitutesAsync_WhenTheRetrievalCircuitIsOpen_FailsFastWithoutCall()
    {
        var retrieval = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.ServiceUnavailable);
        var assist = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, AssistBody);
        await using var provider = AiGatewayTestHost.Build(retrieval, assistHandler: assist);
        var client = provider.Client();

        await Assert.ThrowsAsync<AiUnavailableException>(
            () => client.SearchAsync(new AiSearchRequest { Query = "anillo", TopK = 2 }, PosScope()));

        var issued = retrieval.RequestCount;

        await Assert.ThrowsAsync<AiUnavailableException>(
            () => client.SubstitutesAsync(SubstitutesRequest(), PosScope()));

        retrieval.RequestCount.Should().Be(issued, "with the retrieval circuit open no request may leave");
        assist.RequestCount.Should().Be(0, "substitutes never ride on the generative client");
    }

    [Theory]
    [InlineData(0)]
    [InlineData(51)]
    public async Task SubstitutesAsync_WithTopKOutsideTheContract_IsRejectedBeforeAnyRequest(int topK)
    {
        var retrieval = new FakeHttpMessageHandler().AlwaysRespond(HttpStatusCode.OK, SubstitutesBody);
        await using var provider = AiGatewayTestHost.Build(retrieval);

        var act = async () => await provider.Client().SubstitutesAsync(SubstitutesRequest(topK), PosScope());

        await act.Should().ThrowAsync<ArgumentException>();
        retrieval.Requests.Should().BeEmpty();
    }
}
