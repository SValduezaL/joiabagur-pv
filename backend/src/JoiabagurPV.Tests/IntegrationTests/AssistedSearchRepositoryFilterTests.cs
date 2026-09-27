using FluentAssertions;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Domain.Interfaces.Repositories;
using JoiabagurPV.Infrastructure.Data;
using JoiabagurPV.Infrastructure.Data.Repositories;
using JoiabagurPV.Tests.TestHelpers.Mothers;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace JoiabagurPV.Tests.IntegrationTests;

/// <summary>
/// The degraded searcher against a real PostgreSQL: that the filters an operator pressed actually
/// exclude, and that pressing nothing still returns everything.
/// </summary>
/// <remarks>
/// <para>
/// These run against the database rather than a mock because the thing under test <em>is</em> the
/// SQL: a <c>jsonb</c> overlap operator and a correlated existence subquery against a table with
/// no navigation property. A mocked repository would assert that the arguments were forwarded,
/// which is precisely the part that was never in doubt — the defect this fixes was that the
/// searcher had no filter parameter at all, so the chips stayed pressed over results that ignored
/// them.
/// </para>
/// <para>
/// Every test tags its products with a token unique to the run and queries for that token, so the
/// assertions hold whatever else the shared database contains. That is deliberate in place of a
/// Respawn reset: this collection is serial, and wiping it would take the fixtures of the other
/// classes in the collection with it.
/// </para>
/// </remarks>
[Collection(RepositoryTestCollection.Name)]
public class AssistedSearchRepositoryFilterTests
{
    /// <summary>
    /// Wide enough that nothing in these tests is truncated by the window rather than by a filter,
    /// which would make a passing assertion mean nothing.
    /// </summary>
    private const int Window = 50;

    private readonly TestDatabaseFixture _fixture;

    public AssistedSearchRepositoryFilterTests(TestDatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public async Task SearchLexicalAsync_WithPieceTypeFilter_ReturnsOnlyThatCategory()
    {
        var token = Token();
        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var pointOfSale = await ShopAsync(mother);

        var earrings = await PieceAsync(mother, pointOfSale.Id, token, "pendientes", ["plata"]);
        var ring = await PieceAsync(mother, pointOfSale.Id, token, "anillo", ["plata"]);

        var rows = await SearchAsync(token, pointOfSale.Id, new AssistedSearchFilters
        {
            Category = "pendientes"
        });

        rows.Select(row => row.ProductId).Should().Contain(earrings.Id);
        rows.Select(row => row.ProductId).Should().NotContain(ring.Id,
            "a category the operator pressed is a decision, and a ring is not an earring");
    }

    [Fact]
    public async Task SearchLexicalAsync_WithMaterialFilter_ReturnsOnlyPiecesCarryingIt()
    {
        var token = Token();
        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var pointOfSale = await ShopAsync(mother);

        var silver = await PieceAsync(mother, pointOfSale.Id, token, "anillo", ["plata", "oro"]);
        var steel = await PieceAsync(mother, pointOfSale.Id, token, "anillo", ["acero"]);
        var unextracted = await PieceAsync(mother, pointOfSale.Id, token, "anillo", []);

        var rows = await SearchAsync(token, pointOfSale.Id, new AssistedSearchFilters
        {
            Materials = ["plata"]
        });

        var returned = rows.Select(row => row.ProductId).ToList();

        returned.Should().Contain(silver.Id,
            "matching is an overlap: carrying silver among other materials qualifies");
        returned.Should().NotContain(steel.Id);
        returned.Should().NotContain(unextracted.Id,
            "the 8.5% of the catalog whose materials were never extracted drops out of a material "
            + "filter, and that cost is accepted rather than hidden by showing them anyway");
    }

    [Fact]
    public async Task SearchLexicalAsync_WithNoFilterSelected_ReturnsEverythingMatchingTheTerms()
    {
        var token = Token();
        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var pointOfSale = await ShopAsync(mother);

        var earrings = await PieceAsync(mother, pointOfSale.Id, token, "pendientes", ["plata"]);
        var ring = await PieceAsync(mother, pointOfSale.Id, token, "anillo", ["acero"]);
        var unprofiled = await UnprofiledPieceAsync(mother, pointOfSale.Id, token);

        var rows = await SearchAsync(token, pointOfSale.Id, AssistedSearchFilters.None);

        rows.Select(row => row.ProductId).Should()
            .Contain([earrings.Id, ring.Id, unprofiled.Id],
                "with nothing pressed the searcher behaves exactly as it did before filters "
                + "existed, including for pieces that have no enriched profile at all");
    }

    [Fact]
    public async Task SearchLexicalAsync_WithPointOfSale_ExcludesWhatAnotherShopCarries()
    {
        var token = Token();
        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var here = await ShopAsync(mother);
        var elsewhere = await ShopAsync(mother);

        var mine = await PieceAsync(mother, here.Id, token, "anillo", ["plata"]);
        var theirs = await PieceAsync(mother, elsewhere.Id, token, "anillo", ["plata"]);

        var rows = await SearchAsync(token, here.Id, AssistedSearchFilters.None);

        rows.Select(row => row.ProductId).Should().Contain(mine.Id);
        rows.Select(row => row.ProductId).Should().NotContain(theirs.Id);
    }

    [Fact]
    public async Task SearchLexicalAsync_WithoutPointOfSale_IsNotRestrictedToAnyShop()
    {
        var token = Token();
        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var here = await ShopAsync(mother);
        var elsewhere = await ShopAsync(mother);

        var mine = await PieceAsync(mother, here.Id, token, "anillo", ["plata"]);
        var theirs = await PieceAsync(mother, elsewhere.Id, token, "anillo", ["plata"]);

        var rows = await SearchAsync(token, pointOfSaleId: null, AssistedSearchFilters.None);

        rows.Select(row => row.ProductId).Should().Contain([mine.Id, theirs.Id],
            "an absent scope removes the restriction from the query — it is not a wildcard "
            + "matched against the column, and it is not an empty answer either");
    }

    [Fact]
    public async Task SearchLexicalAsync_WithoutPointOfSale_StillHonoursTheFilters()
    {
        var token = Token();
        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var here = await ShopAsync(mother);
        var elsewhere = await ShopAsync(mother);

        var earrings = await PieceAsync(mother, here.Id, token, "pendientes", ["plata"]);
        var ringElsewhere = await PieceAsync(mother, elsewhere.Id, token, "anillo", ["plata"]);

        var rows = await SearchAsync(token, pointOfSaleId: null, new AssistedSearchFilters
        {
            Category = "pendientes"
        });

        rows.Select(row => row.ProductId).Should().Contain(earrings.Id);
        rows.Select(row => row.ProductId).Should().NotContain(ringElsewhere.Id,
            "widening the scope to every shop must not quietly drop the chips that are pressed");
    }

    // ── Arrangement ───────────────────────────────────────────────────────────────────────

    /// <summary>
    /// A token unique to this test, carried in the product name and used as the query. It is what
    /// lets these assertions be exact against a database other tests also wrote to.
    /// </summary>
    private static string Token() => "tok" + Guid.NewGuid().ToString("N")[..10];

    /// <summary>
    /// The phone is pinned rather than generated. Bogus produces numbers that do not always fit
    /// the twenty characters the column allows, and the resulting 22001 looks like an application
    /// bug for as long as it takes to find this comment.
    /// </summary>
    private static async Task<PointOfSale> ShopAsync(TestDataMother mother) =>
        await mother.PointOfSale().WithPhone("600123456").CreateAsync();

    private static async Task<Product> PieceAsync(
        TestDataMother mother,
        Guid pointOfSaleId,
        string token,
        string pieceType,
        string[] materials)
    {
        var product = await StockedAsync(mother, pointOfSaleId, token);

        mother.Context.ProductAiProfiles.Add(new ProductAiProfile
        {
            ProductId = product.Id,
            PieceType = pieceType,
            MaterialsJson = "[" + string.Join(",", materials.Select(m => $"\"{m}\"")) + "]",
            ColorTagsJson = "[]",
            StyleTagsJson = "[]",
            OccasionTagsJson = "[]",
            FieldConfidenceJson = "{}",
            FieldSourceJson = "{}",
            ProposedProfileJson = "{}",
            SourceHash = new string('a', 64),
            ReviewStatus = ProfileReviewStatus.Approved,
            ReviewOrigin = ProfileReviewOrigin.AutoBulk
        });
        await mother.Context.SaveChangesAsync();

        return product;
    }

    /// <summary>A piece the enrichment pipeline never reached: stocked, but with no profile row.</summary>
    private static async Task<Product> UnprofiledPieceAsync(
        TestDataMother mother, Guid pointOfSaleId, string token) =>
        await StockedAsync(mother, pointOfSaleId, token);

    private static async Task<Product> StockedAsync(
        TestDataMother mother, Guid pointOfSaleId, string token)
    {
        var product = await mother.Product()
            .WithSku($"SKU-{Guid.NewGuid():N}"[..20])
            .WithName($"Pieza {token}")
            .CreateAsync();

        await mother.Inventory()
            .WithProduct(product.Id)
            .WithPointOfSale(pointOfSaleId)
            .WithQuantity(3)
            .CreateAsync();

        return product;
    }

    /// <summary>
    /// Exercises the real repository over the real context, which is the point: the filters are
    /// SQL, so anything short of the database would be testing the wrong thing.
    /// </summary>
    private async Task<IReadOnlyList<AssistedSearchRow>> SearchAsync(
        string token, Guid? pointOfSaleId, AssistedSearchFilters filters)
    {
        using var scope = _fixture.ScopeFactory.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var repository = new AssistedSearchRepository(context);

        return await repository.SearchLexicalAsync(
            [token], pointOfSaleId, filters, Window, CancellationToken.None);
    }
}
