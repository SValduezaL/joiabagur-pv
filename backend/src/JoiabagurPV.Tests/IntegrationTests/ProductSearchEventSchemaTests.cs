using FluentAssertions;
using JoiabagurPV.Domain.Entities;
using JoiabagurPV.Domain.Enums;
using JoiabagurPV.Infrastructure.Data;
using JoiabagurPV.Tests.TestHelpers;
using JoiabagurPV.Tests.TestHelpers.Mothers;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace JoiabagurPV.Tests.IntegrationTests;

/// <summary>
/// Asserts the properties of the search-event schema that fail silently when they are wrong.
/// </summary>
/// <remarks>
/// Nothing here checks that the migration applied — the fixture already proves that before
/// every integration test, so a test asserting it would discard no hypothesis. What is checked
/// is the handful of declarations whose mistakes raise no error at all and only surface once
/// there is data to lose.
/// </remarks>
[Collection(RepositoryTestCollection.Name)]
public class ProductSearchEventSchemaTests
{
    private const string Table = "ProductSearchEvents";
    private readonly TestDatabaseFixture _fixture;

    public ProductSearchEventSchemaTests(TestDatabaseFixture fixture)
    {
        _fixture = fixture;
    }

    [Theory]
    [InlineData("FiltersJson")]
    [InlineData("ResultsJson")]
    public async Task Migration_JsonColumnsAreJsonbNotText(string column)
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var type = await schema.ColumnTypeAsync(Table, column);

        type.Should().Be("jsonb",
            "the column exists to be aggregated in SQL, and jsonb also makes a byte-truncated "
            + "document impossible to store — as text, both failures would be silent");
    }

    [Fact]
    public async Task Migration_QueryTextIsBoundedToTheContractLength()
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var length = await schema.ColumnMaxLengthAsync(Table, "SearchText");

        length.Should().Be(500,
            "the bound comes from query.maxLength in the frozen ai-service/openapi.json contract");
    }

    [Fact]
    public async Task Migration_CompositeIndexOrdersPointOfSaleBeforeCreatedAt()
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var columns = await schema.IndexColumnsAsync("IX_ProductSearchEvents_PointOfSaleId_CreatedAt");

        columns.Should().Equal(["PointOfSaleId", "CreatedAt"],
            "point of sale is the equality predicate of the dominant query; reversed, the index "
            + "still exists and simply stops serving it, without any error");
    }

    [Theory]
    [InlineData("SelectedProductId")]
    [InlineData("SelectedFromRank")]
    [InlineData("SelectedAt")]
    [InlineData("TraceId")]
    [InlineData("RetrievalMs")]
    [InlineData("TotalMs")]
    public async Task Migration_OptionalColumnsAcceptNull(string column)
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var isNullable = await schema.ColumnIsNullableAsync(Table, column);

        isNullable.Should().BeTrue("a search with no selection, no trace or no timing is a valid row");
    }

    [Theory]
    [InlineData("UserId")]
    [InlineData("PointOfSaleId")]
    [InlineData("SearchSessionId")]
    [InlineData("SearchText")]
    [InlineData("ResultsCount")]
    [InlineData("SearchOrigin")]
    public async Task Migration_RequiredColumnsRejectNull(string column)
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var isNullable = await schema.ColumnIsNullableAsync(Table, column);

        isNullable.Should().BeFalse();
    }

    [Theory]
    [InlineData("FK_ProductSearchEvents_Users_UserId")]
    [InlineData("FK_ProductSearchEvents_PointOfSales_PointOfSaleId")]
    [InlineData("FK_ProductSearchEvents_Products_SelectedProductId")]
    public async Task Migration_BusinessEntitiesDoNotCascadeIntoTelemetry(string constraint)
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var rule = await schema.ForeignKeyDeleteRuleAsync(constraint);

        rule.Should().Be("RESTRICT",
            "the framework default for a required relationship is CASCADE, which here would mean "
            + "deleting an employee deletes the evidence of how the system was used");
    }

    /// <remarks>
    /// The claim being discarded is "adding a fourth origin opens a migration". It does not: the
    /// property is stored through an integer conversion, so a new member is a new value in a
    /// column that already holds integers, not a new shape.
    ///
    /// Asserted three ways because each catches a different mistake. The column type catches
    /// somebody changing the conversion to a string or a PostgreSQL enum; the pending-changes
    /// check catches a model edit that really would need a migration; and the round trip catches
    /// the value not surviving the conversion, which the first two would both miss.
    /// </remarks>
    [Fact]
    public async Task SearchOrigin_AddingTheFourthValue_RequiresNoMigration()
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var type = await schema.ColumnTypeAsync(Table, "SearchOrigin");

        type.Should().Be("integer",
            "the origin is persisted through HasConversion<int>(), so a fourth member costs "
            + "nothing at the schema level");

        _fixture.DbContext.Database.HasPendingModelChanges().Should().BeFalse(
            "introducing SearchOrigin.AssistedGenerative must not leave the model ahead of the "
            + "migrations — if this fails, the enum was not the only thing that changed");
    }

    [Fact]
    public async Task SearchOrigin_TheFourthValue_RoundTripsThroughTheExistingColumn()
    {
        using var scope = _fixture.ScopeFactory.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();

        using var mother = new TestDataMother(_fixture.ScopeFactory.CreateScope().ServiceProvider);
        var pointOfSale = await mother.PointOfSale().WithPhone("600123456").CreateAsync();
        var user = await mother.User().CreateAsync();

        var stored = new ProductSearchEvent
        {
            UserId = user.Id,
            PointOfSaleId = pointOfSale.Id,
            SearchSessionId = Guid.NewGuid(),
            SearchText = "un anillo que se pueda mojar",
            SearchOrigin = SearchOrigin.AssistedGenerative,
            FiltersJson = "{}",
            ResultsJson = "[]"
        };

        context.ProductSearchEvents.Add(stored);
        await context.SaveChangesAsync();

        using var reading = _fixture.ScopeFactory.CreateScope();
        var readBack = await reading.ServiceProvider
            .GetRequiredService<ApplicationDbContext>()
            .ProductSearchEvents
            .FindAsync(stored.Id);

        readBack!.SearchOrigin.Should().Be(SearchOrigin.AssistedGenerative);
        ((int)readBack.SearchOrigin).Should().Be(4,
            "the numeric mapping is part of the contract with whoever queries this table by hand");
    }

    [Fact]
    public async Task Migration_PurgingTelemetryNullsSaleAttributionInsteadOfBlockingIt()
    {
        await using var schema = await SchemaAssert.OpenAsync(_fixture.ConnectionString);

        var rule = await schema.ForeignKeyDeleteRuleAsync("FK_Sales_ProductSearchEvents_SearchEventId");

        rule.Should().Be("SET NULL",
            "telemetry is expendable: purging it must neither destroy a sale (CASCADE) nor be "
            + "blocked by one (RESTRICT)");
    }
}
