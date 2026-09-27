using FluentAssertions;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;
using JoiabagurPV.Application.Services;
using JoiabagurPV.Domain.Interfaces.Repositories;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Time.Testing;

namespace JoiabagurPV.Tests.UnitTests.Application;

/// <summary>
/// The POS sales windows are counted against a declared instant, not against the wall clock.
/// </summary>
/// <remarks>
/// Unit tests over a recording repository rather than integration tests against the feed
/// route: what has to be pinned is which instant reaches
/// <see cref="IIndexFeedRepository.GetSalesAggregatesAsync"/>, and asserting that through a
/// seeded database would prove it only for the dates that database happens to hold.
/// </remarks>
public class IndexFeedSalesClockTests
{
    private static readonly DateTime ConfiguredAsOf =
        new(2026, 8, 23, 23, 59, 59, DateTimeKind.Utc);

    private static readonly DateTime WallClock =
        new(2026, 9, 5, 10, 30, 0, DateTimeKind.Utc);

    [Fact]
    public async Task SalesAggregates_WithConfiguredAsOf_CountWindowsAgainstIt()
    {
        var repository = new RecordingIndexFeedRepository();
        var service = BuildService(repository, salesAsOf: ConfiguredAsOf);

        await service.GetPosAvailabilityPageAsync(null, null, CancellationToken.None);

        repository.SalesAsOfReceived.Should().ContainSingle()
            .Which.Should().Be(
                ConfiguredAsOf,
                "the configured instant, not the wall clock, anchors the windows");
    }

    [Fact]
    public async Task SalesAggregates_WithoutAsOf_FallBackToWallClock()
    {
        var repository = new RecordingIndexFeedRepository();
        var service = BuildService(repository, salesAsOf: null);

        await service.GetPosAvailabilityPageAsync(null, null, CancellationToken.None);

        repository.SalesAsOfReceived.Should().ContainSingle()
            .Which.Should().Be(
                WallClock,
                "an unset option must preserve the behaviour that predates it");
    }

    [Fact]
    public async Task PosAvailabilityPage_DeclaresComputedAsOf()
    {
        var configured = await BuildService(new RecordingIndexFeedRepository(), ConfiguredAsOf)
            .GetPosAvailabilityPageAsync(null, null, CancellationToken.None);
        var unconfigured = await BuildService(new RecordingIndexFeedRepository(), null)
            .GetPosAvailabilityPageAsync(null, null, CancellationToken.None);

        configured.ComputedAsOf.Should().Be(ConfiguredAsOf);
        unconfigured.ComputedAsOf.Should().Be(
            WallClock,
            "the page reports the instant actually used, configured or not");
    }

    [Fact]
    public async Task PosAvailabilityPage_DeclaresComputedAsOf_EvenWithNoUpserts()
    {
        var repository = new RecordingIndexFeedRepository { Rows = [] };
        var page = await BuildService(repository, ConfiguredAsOf)
            .GetPosAvailabilityPageAsync(null, null, CancellationToken.None);

        page.Items.Should().BeEmpty();
        page.ComputedAsOf.Should().Be(
            ConfiguredAsOf,
            "the instant is a property of the reading, not of what the page happened to carry");
        repository.SalesAsOfReceived.Should().BeEmpty(
            "an empty page must not spend a query on aggregates");
    }

    [Fact]
    public async Task CatalogPage_IsUntouchedByTheClock()
    {
        var repository = new RecordingIndexFeedRepository();
        var service = BuildService(repository, ConfiguredAsOf);

        var page = await service.GetCatalogPageAsync(null, null, CancellationToken.None);

        page.Should().NotBeOfType<PosAvailabilityPageDto>(
            "the catalog contract keeps its exact shape");
        repository.SalesAsOfReceived.Should().BeEmpty();
    }

    private static IndexFeedService BuildService(
        RecordingIndexFeedRepository repository,
        DateTime? salesAsOf)
    {
        var time = new FakeTimeProvider(new DateTimeOffset(WallClock));
        var options = Options.Create(new IndexFeedOptions
        {
            ApiKey = "local-dev-index-feed-key-0123456789ab",
            SalesAsOf = salesAsOf
        });

        return new IndexFeedService(
            repository,
            time,
            options,
            new StubTraceContext(),
            NullLogger<IndexFeedService>.Instance);
    }

    private sealed class StubTraceContext : ITraceContextAccessor
    {
        public string CurrentTraceId => "trace-index-feed-clock";
    }

    /// <summary>Records the reference instant every aggregate query was asked for.</summary>
    private sealed class RecordingIndexFeedRepository : IIndexFeedRepository
    {
        private static readonly Guid Pos = Guid.Parse("11111111-1111-1111-1111-111111111111");
        private static readonly Guid Product = Guid.Parse("22222222-2222-2222-2222-222222222222");

        public List<DateTime> SalesAsOfReceived { get; } = [];

        public IReadOnlyList<PosFeedRow> Rows { get; init; } =
        [
            new PosFeedRow
            {
                InventoryId = Guid.Parse("33333333-3333-3333-3333-333333333333"),
                PointOfSaleId = Pos,
                ProductId = Product,
                Watermark = new DateTime(2026, 8, 20, 0, 0, 0, DateTimeKind.Utc),
                IsActive = true,
                Quantity = 4
            }
        ];

        public Task<IReadOnlyList<CatalogFeedRow>> GetCatalogPageAsync(
            DateTime? since, Guid? sinceId, int take, bool includeNonIndexable,
            CancellationToken cancellationToken) =>
            Task.FromResult<IReadOnlyList<CatalogFeedRow>>([]);

        public Task<IReadOnlyList<Guid>> GetIndexableProductIdsAsync(
            CancellationToken cancellationToken) =>
            Task.FromResult<IReadOnlyList<Guid>>([]);

        public Task<IReadOnlyList<PosFeedRow>> GetPosPageAsync(
            DateTime? since, Guid? sinceId, int take, CancellationToken cancellationToken) =>
            Task.FromResult(Rows);

        public Task<IReadOnlyList<PosAssignmentPair>> GetActiveAssignmentPairsAsync(
            CancellationToken cancellationToken) =>
            Task.FromResult<IReadOnlyList<PosAssignmentPair>>([new(Pos, Product)]);

        public Task<IReadOnlyList<PosShopRow>> GetPosShopsAsync(
            CancellationToken cancellationToken) =>
            Task.FromResult<IReadOnlyList<PosShopRow>>([new(Pos, true)]);

        public Task<IReadOnlyList<PosSalesAggregate>> GetSalesAggregatesAsync(
            IReadOnlyList<PosAssignmentPair> pairs,
            DateTime now,
            CancellationToken cancellationToken)
        {
            SalesAsOfReceived.Add(now);
            return Task.FromResult<IReadOnlyList<PosSalesAggregate>>(
            [
                new PosSalesAggregate
                {
                    PointOfSaleId = Pos,
                    ProductId = Product,
                    Sales30d = 3,
                    Sales90d = 7,
                    LastSaleAt = new DateTime(2026, 8, 21, 0, 0, 0, DateTimeKind.Utc)
                }
            ]);
        }
    }
}
