using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.DTOs.Auth;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Infrastructure.Data;
using JoiabagurPV.Tests.TestHelpers.Mothers;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace JoiabagurPV.Tests.IntegrationTests;

/// <summary>
/// Integration tests for the assisted-search endpoint, against a real PostgreSQL.
/// </summary>
/// <remarks>
/// The AI service is never reached here: with no gateway configured the client fails and the
/// request degrades, which is precisely the path worth proving against a real database. The
/// Spanish full-text search is SQL the compiler cannot check, the hydration rules are join
/// semantics, and both are the parts that would break silently.
/// </remarks>
[Collection(IntegrationTestCollection.Name)]
public class AiSearchControllerTests : IAsyncLifetime
{
    private readonly ApiWebApplicationFactory _factory;

    private PointOfSale _pos = null!;
    private PointOfSale _otherPos = null!;
    private PointOfSale _closedPos = null!;
    private Product _ring = null!;
    private Product _necklace = null!;
    private Product _outOfStock = null!;
    private Product _unassigned = null!;
    private Product _inactiveProduct = null!;
    private Product _inactiveAssignment = null!;
    private HttpClient _operatorClient = null!;
    private HttpClient _adminClient = null!;

    public AiSearchControllerTests(ApiWebApplicationFactory factory)
    {
        _factory = factory;

        // Load-bearing, despite looking like an unused field. Creating a client builds the host,
        // and building the host is what applies the migrations. InitializeAsync resets the
        // database before issuing any request, so without this the reset runs against a schema
        // that does not exist yet and the whole class fails with "no tables found" whenever it is
        // the first one in the run.
        _anonymousClient = factory.CreateClient();
    }

    private readonly HttpClient _anonymousClient;

    public async Task InitializeAsync()
    {
        await _factory.ResetDatabaseAsync();

        using var mother = new TestDataMother(_factory.Services);

        // Phone pinned on every point of sale: the generator produces numbers of varying length
        // and the column is varchar(20), so leaving it to chance fails intermittently.
        _pos = await mother.PointOfSale()
            .WithCode("SEARCH-POS").WithName("Search Point of Sale")
            .WithAddress("Test Address").WithPhone("600123456").CreateAsync();

        _otherPos = await mother.PointOfSale()
            .WithCode("SEARCH-OTHER").WithName("Other Point of Sale")
            .WithAddress("Test Address").WithPhone("600123456").CreateAsync();

        _closedPos = await mother.PointOfSale()
            .WithCode("SEARCH-CLOSED").WithName("Closed Point of Sale")
            .WithAddress("Test Address").WithPhone("600123456").Inactive().CreateAsync();

        _ring = await mother.Product()
            .WithSku("SKU-RING-1").WithName("Anillo de plata")
            .WithDescription("Anillo artesanal de plata de ley con piedra azul")
            .WithPrice(48.00m).CreateAsync();

        _necklace = await mother.Product()
            .WithSku("SKU-NECK-1").WithName("Collar dorado")
            .WithDescription("Collar de baño de oro para regalo")
            .WithPrice(72.00m).CreateAsync();

        _outOfStock = await mother.Product()
            .WithSku("SKU-RING-2").WithName("Anillo de oro")
            .WithDescription("Anillo de oro amarillo")
            .WithPrice(180.00m).CreateAsync();

        _unassigned = await mother.Product()
            .WithSku("SKU-RING-3").WithName("Anillo de acero")
            .WithDescription("Anillo de acero quirurgico")
            .WithPrice(20.00m).CreateAsync();

        _inactiveProduct = await mother.Product()
            .WithSku("SKU-RING-4").WithName("Anillo retirado")
            .WithDescription("Anillo retirado del catalogo")
            .WithPrice(30.00m).CreateAsync();

        _inactiveAssignment = await mother.Product()
            .WithSku("SKU-RING-5").WithName("Anillo desasignado")
            .WithDescription("Anillo cuya asignacion se desactivo")
            .WithPrice(35.00m).CreateAsync();

        await mother.Inventory().WithProduct(_ring.Id).WithPointOfSale(_pos.Id).WithQuantity(5).CreateAsync();
        await mother.Inventory().WithProduct(_necklace.Id).WithPointOfSale(_pos.Id).WithQuantity(2).CreateAsync();

        // Carried here, but sold out. Must survive: availability weights, it never excludes.
        await mother.Inventory().WithProduct(_outOfStock.Id).WithPointOfSale(_pos.Id).WithQuantity(0).CreateAsync();

        // Carried by another shop only.
        await mother.Inventory().WithProduct(_unassigned.Id).WithPointOfSale(_otherPos.Id).WithQuantity(9).CreateAsync();

        // Assigned here, but the product left the catalog.
        await mother.Inventory().WithProduct(_inactiveProduct.Id).WithPointOfSale(_pos.Id).WithQuantity(4).CreateAsync();

        // Assignment itself deactivated.
        await mother.Inventory().WithProduct(_inactiveAssignment.Id).WithPointOfSale(_pos.Id)
            .WithQuantity(4).Inactive().CreateAsync();

        await mother.Product().WithSku("SKU-RING-4-DEACTIVATE").WithName("placeholder").CreateAsync();
        await DeactivateProductAsync(_inactiveProduct.Id);

        await mother.User().WithUsername("searchoperator").AsOperator()
            .AssignedTo(_pos.Id).CreateAsync();

        await mother.User().WithUsername("searchadmin").AsAdmin().CreateAsync();

        _operatorClient = await AuthenticateAsync("searchoperator", "Test123!");
        _adminClient = await AuthenticateAsync("searchadmin", "Test123!");
    }

    public Task DisposeAsync() => Task.CompletedTask;

    [Fact]
    public async Task Search_WhenAiUnavailable_FallsBackToLexicalSearch()
    {
        var response = await SearchAsync(_operatorClient, "un anillo de plata para regalar", _pos.Id);

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;

        // No AI service is reachable in the test host, so this is the degraded path — and it
        // finds things, which is the whole point of replacing a whole-string match.
        body.AiAvailable.Should().BeFalse();
        body.Results.Should().NotBeEmpty();
        body.Results.Select(r => r.Sku).Should().Contain("SKU-RING-1");
    }

    [Fact]
    public async Task Fallback_MatchesAnyQueryTerm_NotTheWholeString()
    {
        // This exact string appears in no product name. A whole-string match returns nothing.
        var response = await SearchAsync(_operatorClient, "quiero un collar bonito para un regalo", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;

        body.Results.Select(r => r.Sku).Should().Contain("SKU-NECK-1");
    }

    [Fact]
    public async Task Fallback_ToleratesReservedCharactersInTheQuery()
    {
        // The strict text-search conversion raises on these. The degraded path is the one thing
        // still standing when the AI is down; it must not turn a typo into a server error.
        var response = await SearchAsync(_operatorClient, "anillo & plata | (oro", _pos.Id);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task Fallback_FindsByExactSku()
    {
        var response = await SearchAsync(_operatorClient, "SKU-NECK-1", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;

        body.Results.Select(r => r.Sku).Should().Contain("SKU-NECK-1");
    }

    [Fact]
    public async Task Search_HydratesPriceAndStockFromDatabase_NotFromAiResponse()
    {
        var response = await SearchAsync(_operatorClient, "anillo plata", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;
        var hit = body.Results.Single(r => r.Sku == "SKU-RING-1");

        hit.Price.Should().Be(48.00m);
        hit.QuantityAtPointOfSale.Should().Be(5);
        hit.HasStock.Should().BeTrue();
        hit.Name.Should().Be("Anillo de plata");
    }

    [Fact]
    public async Task Search_KeepsAssignedProductWithZeroStock()
    {
        var response = await SearchAsync(_operatorClient, "anillo oro", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;
        var hit = body.Results.Single(r => r.Sku == "SKU-RING-2");

        hit.QuantityAtPointOfSale.Should().Be(0);
        hit.HasStock.Should().BeFalse();
    }

    [Fact]
    public async Task Search_DropsWhatThisPointOfSaleDoesNotCarry()
    {
        var response = await SearchAsync(_operatorClient, "anillo", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;
        var skus = body.Results.Select(r => r.Sku).ToList();

        skus.Should().NotContain("SKU-RING-3", "it is carried by another point of sale");
        skus.Should().NotContain("SKU-RING-4", "the product is inactive");
        skus.Should().NotContain("SKU-RING-5", "the inventory assignment is inactive");
    }

    [Fact]
    public async Task Search_QuantityIsTheOneAtThatPointOfSale()
    {
        using var mother = new TestDataMother(_factory.Services);
        await mother.Inventory().WithProduct(_ring.Id).WithPointOfSale(_otherPos.Id)
            .WithQuantity(99).CreateAsync();

        var response = await SearchAsync(_operatorClient, "anillo plata", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;

        // Not 104. The catalog service sums across assigned points of sale; this endpoint does
        // not, because the operator is standing in one shop.
        body.Results.Single(r => r.Sku == "SKU-RING-1").QuantityAtPointOfSale.Should().Be(5);
    }

    [Fact]
    public async Task Search_RecordsTheSearchEvent()
    {
        var response = await SearchAsync(_operatorClient, "anillo plata", _pos.Id);

        var body = (await response.Content.ReadFromJsonAsync<AssistedSearchResponse>())!;

        // Without this the telemetry capability is dead code that compiles and passes.
        body.SearchEventId.Should().NotBeNull();
    }

    [Fact]
    public async Task Search_WithoutPointOfSale_ReturnsBadRequest()
    {
        var response = await _operatorClient.PostAsJsonAsync(
            "/api/ai/search",
            new AssistedSearchRequest { Query = "anillo", PointOfSaleId = Guid.Empty });

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task Search_WithBlankQuery_ReturnsBadRequest()
    {
        var response = await SearchAsync(_operatorClient, "   ", _pos.Id);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task Search_OperatorCannotChooseUnassignedPos()
    {
        var response = await SearchAsync(_operatorClient, "anillo", _otherPos.Id);

        response.StatusCode.Should().Be(HttpStatusCode.Forbidden);
    }

    [Fact]
    public async Task Search_AdminMayChooseAnyActivePos()
    {
        var response = await SearchAsync(_adminClient, "anillo", _otherPos.Id);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task Search_WhenPointOfSaleInactive_IsRefused()
    {
        var response = await SearchAsync(_adminClient, "anillo", _closedPos.Id);

        // Not even an administrator searches a shop that is closed.
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task Search_WhenUnauthenticated_Returns401()
    {
        // A fresh client: the shared one carries the cookies of every login it performed, so it
        // is not anonymous.
        var anonymous = _factory.CreateClient();

        var response = await SearchAsync(anonymous, "anillo", _pos.Id);

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    // ---------------------------------------------------------------- availability

    /// <remarks>
    /// Routing and authorisation are the two things a unit test of the service cannot see, and
    /// both are easy to get wrong in a way that only shows up in the browser: a mistyped route
    /// segment answers 404, and inheriting the controller's rate-limiting policy would make the
    /// availability check spend the quota of the search it is checking on.
    /// </remarks>
    [Fact]
    public async Task Availability_WhenCalled_ReportsBothSwitchesWithoutSearching()
    {
        var response = await _operatorClient.GetAsync($"/api/ai/search/availability?pointOfSaleId={_pos.Id}");

        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var body = (await response.Content.ReadFromJsonAsync<AiSearchAvailabilityResponse>())!;

        body.PointOfSaleId.Should().Be(_pos.Id);
        body.AssistedAnswerUnavailableReason.Should().Be(
            body.AssistedAnswerAvailable ? null : "switched_off");
    }

    [Fact]
    public async Task Availability_WhenCalledRepeatedly_IsNotRateLimited()
    {
        // Comfortably past the search policy's allowance. If this route inherited it, checking
        // availability would start answering 429 — and the panel asks before every search.
        for (var i = 0; i < 40; i++)
        {
            var response = await _operatorClient.GetAsync(
                $"/api/ai/search/availability?pointOfSaleId={_pos.Id}");

            response.StatusCode.Should().Be(HttpStatusCode.OK,
                "the availability check makes no AI call, so rationing it would only ration the "
                + "screen's ability to tell the truth about what is switched on");
        }
    }

    [Fact]
    public async Task Availability_WhenUnauthenticated_Returns401()
    {
        var anonymous = _factory.CreateClient();

        var response = await anonymous.GetAsync($"/api/ai/search/availability?pointOfSaleId={_pos.Id}");

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    /// <remarks>
    /// C40_FIX. This route refused an absent point of sale, so a screen offering the every-shop
    /// scope had nothing to read and showed the generative path disabled with no reason — the
    /// failure the route was created to prevent, reappearing one scope along.
    /// </remarks>
    [Fact]
    public async Task Availability_WithoutPointOfSale_ReturnsTheDefaultScope()
    {
        var response = await _operatorClient.GetAsync("/api/ai/search/availability");

        response.StatusCode.Should().Be(HttpStatusCode.OK,
            "an absent point of sale is the scope covering every one of them, not a malformed request");

        var body = (await response.Content.ReadFromJsonAsync<AiSearchAvailabilityResponse>())!;

        body.PointOfSaleId.Should().BeNull(
            "the wider scope comes back as an absence and never as a blank identifier");
        body.AssistedAnswerUnavailableReason.Should().Be(
            body.AssistedAnswerAvailable ? null : "switched_off");
    }

    /// <remarks>
    /// The distinction that makes this scope safe, asserted on the way in: an absent point of sale
    /// leaves the availability prefilter unapplied, while a blank identifier names no shop. Reading
    /// the second as the first would turn a client bug into a wider answer, which is the
    /// wildcard-by-accident C40 spent a whole group of work closing.
    /// </remarks>
    [Fact]
    public async Task Availability_WithBlankPointOfSale_Returns400()
    {
        var response = await _operatorClient.GetAsync(
            $"/api/ai/search/availability?pointOfSaleId={Guid.Empty}");

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest,
            "a blank identifier is a value that names no shop, so it has to be refused rather than "
            + "read as though the field had not been sent");
    }

    /// <remarks>
    /// <strong>Independent verification, 2026-09-26.</strong> The <c>Guid.Empty</c> form has a test;
    /// these two forms had none, and both were served as the wider scope. A <c>Guid?</c> swallows a
    /// query value it cannot parse and hands over <see langword="null"/>, and since C40_FIX
    /// <see langword="null"/> is a <em>meaning</em> — every point of sale — rather than a missing
    /// field. <c>SuppressModelStateInvalidFilter</c> is on globally, so nothing else refuses it
    /// either. Until C40_FIX the parameter was a non-nullable <c>Guid</c>, which bound to
    /// <c>Guid.Empty</c> on a failure and fell into the guard below it, so the change removed that
    /// net without replacing it.
    /// </remarks>
    [Theory]
    [InlineData("")]
    [InlineData("%20")]
    [InlineData("notaguid")]
    [InlineData("22222222-2222-2222-2222")]
    public async Task Availability_WithAnUnusablePointOfSale_Returns400(string unusable)
    {
        var response = await _operatorClient.GetAsync(
            $"/api/ai/search/availability?pointOfSaleId={unusable}");

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest,
            "the field being there with nothing usable in it is a value, not an absence, and reading "
            + "it as the wider scope turns a client bug into a wider answer");
    }

    // ---------------------------------------------------------------- helpers

    private static Task<HttpResponseMessage> SearchAsync(HttpClient client, string query, Guid pointOfSaleId) =>
        client.PostAsJsonAsync(
            "/api/ai/search",
            new AssistedSearchRequest { Query = query, PointOfSaleId = pointOfSaleId });

    private async Task<HttpClient> AuthenticateAsync(string username, string password)
    {
        var client = _factory.CreateClient();

        var response = await client.PostAsJsonAsync(
            "/api/auth/login",
            new LoginRequest { Username = username, Password = password });

        response.EnsureSuccessStatusCode();
        return client;
    }

    private async Task DeactivateProductAsync(Guid productId)
    {
        using var scope = _factory.Services.CreateScope();
        var context = scope.ServiceProvider
            .GetRequiredService<ApplicationDbContext>();

        var product = await context.Products.FindAsync(productId);
        product!.IsActive = false;
        await context.SaveChangesAsync();
    }
}
