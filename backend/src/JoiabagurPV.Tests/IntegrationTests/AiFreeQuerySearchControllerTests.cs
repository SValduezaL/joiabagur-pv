using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.DTOs.Auth;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Tests.TestHelpers;
using JoiabagurPV.Tests.TestHelpers.Mothers;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace JoiabagurPV.Tests.IntegrationTests;

/// <summary>
/// The free-query endpoint over HTTP: its route, its authorisation, and above all its
/// <strong>own</strong> rate-limiting policy. C40.
/// </summary>
/// <remarks>
/// Its own host, like the other two rate policies: the shared factory raises every allowance out
/// of the way, and a policy nobody can reach is a policy nobody can test. This one sets a limit
/// of two and stretches the window so the allowance cannot refill mid-test.
/// </remarks>
[Collection(IntegrationTestCollection.Name)]
public class AiFreeQuerySearchControllerTests : IAsyncLifetime
{
    private const int PermitLimit = 2;

    private readonly ApiWebApplicationFactory _sharedFactory;
    private readonly HttpClient _warmUpClient;
    private readonly CountingGateway _gateway = new();

    private WebApplicationFactory<Program> _factory = null!;
    private PointOfSale _pos = null!;
    private PointOfSale _otherPos = null!;
    private Product _product = null!;
    private HttpClient _operator = null!;
    private HttpClient _otherOperator = null!;

    public AiFreeQuerySearchControllerTests(ApiWebApplicationFactory sharedFactory)
    {
        _sharedFactory = sharedFactory;

        // Builds the shared host, which applies the migrations before the reset below.
        _warmUpClient = sharedFactory.CreateClient();
    }

    public async Task InitializeAsync()
    {
        await _sharedFactory.ResetDatabaseAsync();

        using var mother = new TestDataMother(_sharedFactory.Services);

        // Phone pinned: the generator produces numbers of varying length and the column is
        // varchar(20), so leaving it to chance fails intermittently.
        _pos = await mother.PointOfSale()
            .WithCode("FQ-POS").WithName("Free Query Shop")
            .WithAddress("Test Address").WithPhone("600123456").CreateAsync();

        _otherPos = await mother.PointOfSale()
            .WithCode("FQ-OTHER").WithName("Another Shop")
            .WithAddress("Test Address").WithPhone("600123456").CreateAsync();

        _product = await mother.Product()
            .WithSku("SKU-FQ-1").WithName("Anillo de plata").WithPrice(39.9m).CreateAsync();

        await mother.Inventory()
            .WithProduct(_product.Id).WithPointOfSale(_pos.Id).WithQuantity(4).CreateAsync();

        await mother.User().WithUsername("fqone").AsOperator().AssignedTo(_pos.Id).CreateAsync();
        await mother.User().WithUsername("fqtwo").AsOperator().AssignedTo(_pos.Id).CreateAsync();

        _gateway.AnchorProductId = _product.Id.ToString();

        _factory = _sharedFactory.WithWebHostBuilder(builder =>
        {
            builder.UseSetting("AiFreeQuerySearch:EnabledByDefault", "true");
            builder.UseSetting("AiFreeQuerySearch:RateLimitPermitLimit", PermitLimit.ToString());
            builder.UseSetting("AiFreeQuerySearch:RateLimitWindowSeconds", "300");
            builder.ConfigureServices(services => services.AddScoped<IAiGatewayClient>(_ => _gateway));
        });

        _operator = await AuthenticateAsync("fqone");
        _otherOperator = await AuthenticateAsync("fqtwo");
    }

    public Task DisposeAsync()
    {
        _factory?.Dispose();
        return Task.CompletedTask;
    }

    // ---------------------------------------------------------------- the route

    [Fact]
    public async Task FreeQuery_AnswersWithGroupsHydratedFromTheCatalog()
    {
        var response = await SearchAsync(_operator);

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = (await response.Content.ReadFromJsonAsync<FreeQuerySearchResponse>())!;

        body.AiAvailable.Should().BeTrue();
        body.Groups.Should().ContainSingle()
            .Which.Members.Should().ContainSingle()
            .Which.Price.Should().Be(39.9m, "price comes from the catalog, never from the model");
    }

    [Fact]
    public async Task FreeQuery_WithoutQuery_Returns400()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "  ", PointOfSaleId = _pos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task FreeQuery_WhenUnauthenticated_Returns401()
    {
        // A fresh client: the shared one carries the cookies of every login it performed.
        var anonymous = _factory.CreateClient();

        var response = await anonymous.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "anillo", PointOfSaleId = _pos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task FreeQuery_ForAnUnassignedPointOfSale_IsForbidden()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "anillo", PointOfSaleId = _otherPos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.Forbidden);
    }

    // ------------------------------------------------- C40 · every point of sale at once

    /// <summary>
    /// **Operators, not only administrators**, and the reason is that it discloses nothing new:
    /// the stock breakdown of a product is already readable across every shop by any
    /// authenticated caller, so a search that spans them exposes no fact that was not exposed.
    /// </summary>
    [Fact]
    public async Task FreeQuery_ForOperatorWithAllPointsOfSale_IsServed()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "anillo de plata", PointOfSaleId = null });

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = (await response.Content.ReadFromJsonAsync<FreeQuerySearchResponse>())!;

        body.PointOfSaleId.Should().BeNull(
            "the response echoes the absence rather than substituting a shop for it");
    }

    /// <summary>
    /// What cannot be known is not invented: no quantity is reported, because a zero would
    /// assert something false about a piece that may be sitting in the next shop along.
    /// </summary>
    [Fact]
    public async Task FreeQuery_ForAllPointsOfSale_ReportsNoQuantity()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "anillo de plata", PointOfSaleId = null });

        var body = (await response.Content.ReadFromJsonAsync<FreeQuerySearchResponse>())!;
        var members = body.Groups.SelectMany(group => group.Members).ToList();

        members.Should().NotBeEmpty("the catalogue answers even with no shop named");
        members.Should().OnlyContain(member => member.QuantityAtPointOfSale == null);
        members.Should().OnlyContain(member => member.HasStock == null);
    }

    /// <summary>
    /// The third scope does not relax the other boundary. Naming a shop the caller is not
    /// assigned to is refused exactly as before, and refused before any call is made.
    /// </summary>
    [Fact]
    public async Task FreeQuery_WhenNamingAnUnassignedPointOfSale_IsRefused()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "anillo", PointOfSaleId = _otherPos.Id });

        response.StatusCode.Should().Be(HttpStatusCode.Forbidden);
    }

    /// <summary>
    /// An empty identifier is a malformed request and never «all of them»: reading it as the
    /// wider scope would turn a client bug into a wider search.
    /// </summary>
    [Fact]
    public async Task FreeQuery_WithAnEmptyPointOfSale_Returns400()
    {
        var response = await _operator.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest { Query = "anillo", PointOfSaleId = Guid.Empty });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    // ---------------------------------------------------------------- the quota

    [Fact]
    public async Task FreeQuery_WhenQuotaExhausted_ReportsTooManyRequests()
    {
        for (var i = 0; i < PermitLimit; i++)
        {
            (await SearchAsync(_operator)).StatusCode.Should().Be(HttpStatusCode.OK);
        }

        var rejected = await SearchAsync(_operator);

        rejected.StatusCode.Should().Be(HttpStatusCode.TooManyRequests);
        _gateway.AssistCalls.Should().Be(PermitLimit, "the rejected request never reached the AI");
    }

    /// <remarks>
    /// The two have opposite remedies — one resolves in seconds by waiting, the other does not
    /// resolve by waiting at all — so folding them together would show an outage message to an
    /// operator who only has to pause.
    /// </remarks>
    [Fact]
    public async Task FreeQuery_WhenQuotaExhausted_DoesNotReportUnavailable()
    {
        for (var i = 0; i < PermitLimit; i++)
        {
            await SearchAsync(_operator);
        }

        var rejected = await SearchAsync(_operator);
        var body = await rejected.Content.ReadAsStringAsync();

        rejected.StatusCode.Should().Be(HttpStatusCode.TooManyRequests);
        body.Should().NotContain("aiAvailable",
            "a throttle is not a degraded answer and must not arrive wearing one's clothes");
        body.Should().NotContain("degradedReason");
    }

    [Fact]
    public async Task FreeQuery_QuotaIsPartitionedByUser_NotByNetworkOrigin()
    {
        for (var i = 0; i < PermitLimit; i++)
        {
            await SearchAsync(_operator);
        }

        (await SearchAsync(_operator)).StatusCode.Should().Be(HttpStatusCode.TooManyRequests);

        // Same host, same network origin: partitioned by address this would be 429.
        (await SearchAsync(_otherOperator)).StatusCode.Should().Be(HttpStatusCode.OK);
    }

    /// <remarks>
    /// The whole reason this endpoint exists rather than a <c>mode</c> field: a rate limit is an
    /// attribute of an endpoint, so one route would have to pick a single allowance. Exhausting
    /// the generative one must leave the cheap path working.
    /// </remarks>
    [Fact]
    public async Task FreeQuery_QuotaIsIndependentOfTheCardQuota()
    {
        for (var i = 0; i <= PermitLimit; i++)
        {
            await SearchAsync(_operator);
        }

        var card = await _operator.PostAsJsonAsync(
            $"/api/ai/products/{_product.Id}/sales-assist",
            new SalesAssistRequest { PointOfSaleId = _pos.Id });

        card.StatusCode.Should().Be(HttpStatusCode.OK,
            "the sale card has its own allowance and is opened once per piece");
    }

    [Fact]
    public async Task FreeQuery_ExhaustedAllowance_DoesNotThrottleTheSemanticSearch()
    {
        for (var i = 0; i <= PermitLimit; i++)
        {
            await SearchAsync(_operator);
        }

        var semantic = await _operator.PostAsJsonAsync(
            "/api/ai/search",
            new AssistedSearchRequest { Query = "anillo", PointOfSaleId = _pos.Id });

        semantic.StatusCode.Should().Be(HttpStatusCode.OK,
            "the cheap path is what the toggle offers when the assisted one is spent");
    }

    // ---------------------------------------------------------------- arrangement

    private Task<HttpResponseMessage> SearchAsync(HttpClient client) =>
        client.PostAsJsonAsync(
            "/api/ai/search/assisted",
            new FreeQuerySearchRequest
            {
                Query = "un anillo de plata para regalar",
                PointOfSaleId = _pos.Id
            });

    private async Task<HttpClient> AuthenticateAsync(string username)
    {
        var client = _factory.CreateClient();
        var response = await client.PostAsJsonAsync(
            "/api/auth/login", new LoginRequest { Username = username, Password = "Test123!" });
        response.EnsureSuccessStatusCode();
        return client;
    }

    private sealed class CountingGateway : ThrowingAiGatewayClient
    {
        private int _assistCalls;

        public int AssistCalls => _assistCalls;

        public string AnchorProductId { get; set; } = string.Empty;

        public override Task<AiAssistSaleResponse> AssistSaleAsync(
            AiAssistSaleRequest request, AiCallScope scope, CancellationToken cancellationToken = default)
        {
            Interlocked.Increment(ref _assistCalls);

            return Task.FromResult(new AiAssistSaleResponse
            {
                Intent = "in_domain",
                Groups =
                [
                    new AiAssistGroup
                    {
                        FamilyId = "fam-fq",
                        FamilyLabel = "Aro fino",
                        Members =
                        [
                            new AiAssistGroupMember
                            {
                                ProductId = AnchorProductId,
                                Sku = "SKU-FQ-1",
                                Score = 0.82,
                                Materials = ["plata"],
                                MatchReasons = ["vector"]
                            }
                        ]
                    }
                ],
                // No placeholder: the free-query tasks of assist/v5 do not write them, and a
                // hard cause in the service's integrity gate makes that a guarantee.
                Pitch = "Las tres son sobrias y van bien a diario.",
                PromptVersion = "assist/v5"
            });
        }
    }
}
