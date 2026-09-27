using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Infrastructure.Data;
using JoiabagurPV.Tests.TestHelpers;
using JoiabagurPV.Tests.TestHelpers.Mothers;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace JoiabagurPV.Tests.IntegrationTests;

/// <summary>
/// Shop activity feed (C43): the reading that lets the AI side know a shop is closed.
/// </summary>
/// <remarks>
/// It exists because the AI service cannot ask: the <c>jbg_ai</c> role is refused
/// <c>SELECT</c> on <c>public."PointOfSales"</c>, so without this route the health report
/// counted a shop deliberately closed as a shop with a broken assortment — and failed a
/// healthy deployment of the demonstration environment on 2026-09-27.
/// </remarks>
[Collection(IntegrationTestCollection.Name)]
public class AiIndexFeedShopsTests : IAsyncLifetime
{
    private static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true };

    private const string ShopsFeed = "/api/ai/index-feed/pos-shops";
    private const string PosFeed = "/api/ai/index-feed/pos-availability";

    private readonly ApiWebApplicationFactory _factory;
    private readonly HttpClient _client;

    private PointOfSale _open = null!;
    private PointOfSale _closed = null!;

    public AiIndexFeedShopsTests(ApiWebApplicationFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
        _client.DefaultRequestHeaders.Add(IndexFeedOptions.HeaderName, IndexFeedTestKeys.ApiKey);
    }

    public async Task InitializeAsync()
    {
        await _factory.ResetDatabaseAsync();

        using var mother = new TestDataMother(_factory.Services);

        // `WithPhone` is pinned rather than generated: Bogus produces numbers that do not
        // always fit `PointOfSale.Phone`, and the failure reads as a 22001 from the database.
        _open = await mother.PointOfSale()
            .WithCode("SHOP-OPEN")
            .WithName("Tienda abierta")
            .WithAddress("Test Address")
            .WithPhone("600123456")
            .CreateAsync();

        _closed = await mother.PointOfSale()
            .WithCode("SHOP-CLOSED")
            .WithName("Hotel Cap d'Artrutx")
            .WithAddress("Test Address")
            .WithPhone("600123457")
            .CreateAsync();

        await DeactivateAsync(_closed.Id);
    }

    public Task DisposeAsync() => Task.CompletedTask;

    [Fact]
    public async Task GetPosShops_WithFeedKey_ReturnsEveryPointOfSale()
    {
        var response = await _client.GetAsync(ShopsFeed);
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var reading = await ReadAsync(response);

        reading.Items.Should().HaveCount(2);
        reading.Items.Select(item => item.PointOfSaleId)
            .Should().BeEquivalentTo(new[] { _open.Id, _closed.Id });
        reading.ComputedAsOf.Should().NotBe(default);
    }

    [Fact]
    public async Task GetPosShops_WithInactivePointOfSale_ReportsItRatherThanOmittingIt()
    {
        // The whole finding in one assertion. Omitting the closed shop would make "closed"
        // and "deleted" the same thing on the wire, and the consumer treats them oppositely:
        // a closed shop keeps its row and stops being counted, a deleted one loses its row.
        var reading = await ReadAsync(await _client.GetAsync(ShopsFeed));

        var closed = reading.Items.Single(item => item.PointOfSaleId == _closed.Id);
        closed.IsActive.Should().BeFalse();

        var open = reading.Items.Single(item => item.PointOfSaleId == _open.Id);
        open.IsActive.Should().BeTrue();
    }

    [Fact]
    public async Task GetPosShops_IsACompleteReading_WithNoCursorAndNoPaging()
    {
        var response = await _client.GetAsync(ShopsFeed);
        var body = await response.Content.ReadAsStringAsync();

        using var document = JsonDocument.Parse(body);
        var root = document.RootElement;

        root.TryGetProperty("nextCursor", out _).Should().BeFalse(
            "a cursor would let a removed point of sale survive in the consumer for ever");
        root.TryGetProperty("hasMore", out _).Should().BeFalse();
        root.TryGetProperty("pageSize", out _).Should().BeFalse();
        root.TryGetProperty("aggregateHash", out _).Should().BeFalse();
    }

    [Fact]
    public async Task GetPosShops_WithPageSizeParameter_IgnoresItAndReturnsEverything()
    {
        var reading = await ReadAsync(await _client.GetAsync($"{ShopsFeed}?pageSize=1"));

        reading.Items.Should().HaveCount(2);
    }

    [Fact]
    public async Task GetPosShops_WithoutFeedKey_ReturnsUnauthorized()
    {
        // A fresh client: the shared one carries the feed key, and reusing it would assert
        // nothing about an anonymous call.
        var anonymous = _factory.CreateClient();

        var response = await anonymous.GetAsync(ShopsFeed);

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    [Fact]
    public async Task GetPosShops_CarriesNoDescriptiveAttributeOfThePointOfSale()
    {
        // The consumer counts and does not name. A code or a name here would put a second
        // copy of a fact this schema owns inside the AI schema, going stale between drains.
        var body = await (await _client.GetAsync(ShopsFeed)).Content.ReadAsStringAsync();

        body.Should().NotContain("SHOP-OPEN");
        body.Should().NotContain("Artrutx");
        body.Should().NotContain("Test Address");
        body.Should().NotContain("600123456");
    }

    [Fact]
    public async Task PosAvailabilityFeed_IsUnchangedByTheShopsFeed()
    {
        // C43 declares the availability feed untouched. This pins the three properties that
        // a careless widening would have moved: the page size, the cursor and the hash.
        var response = await _client.GetAsync(PosFeed);
        response.StatusCode.Should().Be(HttpStatusCode.OK);

        var page = JsonSerializer.Deserialize<PosAvailabilityPageDto>(
            await response.Content.ReadAsStringAsync(), Json)!;

        page.PageSize.Should().Be(200);
        page.AggregateHash.Should().NotBeNullOrEmpty();
        page.HasMore.Should().BeFalse();
        page.NextCursor.Should().BeNull();
    }

    private async Task<PosShopsReadingDto> ReadAsync(HttpResponseMessage response)
    {
        response.EnsureSuccessStatusCode();
        return JsonSerializer.Deserialize<PosShopsReadingDto>(
            await response.Content.ReadAsStringAsync(), Json)!;
    }

    private async Task DeactivateAsync(Guid pointOfSaleId)
    {
        using var scope = _factory.Services.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var pointOfSale = await context.PointOfSales.SingleAsync(pos => pos.Id == pointOfSaleId);
        pointOfSale.IsActive = false;
        await context.SaveChangesAsync();
    }
}
