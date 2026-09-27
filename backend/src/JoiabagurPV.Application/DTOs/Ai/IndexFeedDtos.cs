namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>Discriminator values for feed items.</summary>
public static class IndexFeedKinds
{
    public const string Upsert = "upsert";
    public const string Tombstone = "tombstone";
}

/// <summary>Catalog tombstone reasons.</summary>
public static class CatalogTombstoneReasons
{
    public const string Deactivated = "deactivated";
    public const string Unapproved = "unapproved";
}

/// <summary>POS tombstone reason.</summary>
public static class PosTombstoneReasons
{
    public const string Unassigned = "unassigned";
}

/// <summary>Keyset cursor. Null <c>nextCursor</c> means the caller has exhausted the feed.</summary>
public sealed class IndexFeedCursorDto
{
    public DateTime Since { get; init; }

    public Guid SinceId { get; init; }
}

/// <summary>
/// One page of an indexing feed. <see cref="AggregateHash"/> is the digest of the global
/// indexable set, identical on every page of the same reading.
/// </summary>
/// <remarks>
/// Not sealed so <see cref="PosAvailabilityPageDto"/> can add the one field only that feed
/// has. The catalog page keeps this exact shape: serialisation follows the declared type, so
/// widening the base would have added a permanently null field to a contract that has no use
/// for it.
/// </remarks>
public class IndexFeedPageDto
{
    public IReadOnlyList<object> Items { get; init; } = [];

    public IndexFeedCursorDto? NextCursor { get; init; }

    public bool HasMore { get; init; }

    public int PageSize { get; init; }

    public string AggregateHash { get; init; } = string.Empty;
}

/// <summary>
/// One page of the POS availability feed. Adds <see cref="ComputedAsOf"/>, the instant the
/// sales windows on this page were counted against.
/// </summary>
/// <remarks>
/// Always populated, whether the instant came from <c>IndexFeed:SalesAsOf</c> or from the
/// wall clock: a windowed figure whose clock is not declared cannot be reproduced, and the
/// point of declaring it is lost if the field is present only when someone remembered to
/// configure one. The consumer persists it per row, because the feed is incremental and one
/// projection can end up holding rows counted against different instants.
/// </remarks>
public sealed class PosAvailabilityPageDto : IndexFeedPageDto
{
    public DateTime ComputedAsOf { get; init; }
}

/// <summary>
/// Catalog upsert: superset of <c>ProductSourceText</c> plus identifiers, price, band and watermark.
/// Materials and tags are arrays, not the persisted <c>*Json</c> strings. No provenance fields.
/// </summary>
public sealed class CatalogUpsertItemDto
{
    public string Kind { get; init; } = IndexFeedKinds.Upsert;

    public Guid ProductId { get; init; }

    public string Sku { get; init; } = string.Empty;

    public string Name { get; init; } = string.Empty;

    public string? Description { get; init; }

    public string? CollectionName { get; init; }

    public string? PieceType { get; init; }

    public IReadOnlyList<string> Materials { get; init; } = [];

    public string? StoneType { get; init; }

    public string? SizeLabel { get; init; }

    public Guid? FamilyId { get; init; }

    public string? FamilyName { get; init; }

    public string? VariantLabel { get; init; }

    public IReadOnlyList<string> ColorTags { get; init; } = [];

    public IReadOnlyList<string> StyleTags { get; init; } = [];

    public IReadOnlyList<string> OccasionTags { get; init; } = [];

    public decimal Price { get; init; }

    public string PriceBand { get; init; } = string.Empty;

    public bool IsActive { get; init; }

    public DateTime Watermark { get; init; }
}

/// <summary>Catalog tombstone. Source-text fields stay off this body.</summary>
public sealed class CatalogTombstoneItemDto
{
    public string Kind { get; init; } = IndexFeedKinds.Tombstone;

    public Guid ProductId { get; init; }

    public string Reason { get; init; } = string.Empty;

    public DateTime At { get; init; }
}

/// <summary>
/// POS availability upsert. Has no <c>Quantity</c> property — serialising stock exact would
/// leak inventory on a public API route.
/// </summary>
public sealed class PosAvailabilityUpsertItemDto
{
    public string Kind { get; init; } = IndexFeedKinds.Upsert;

    public Guid PointOfSaleId { get; init; }

    public Guid ProductId { get; init; }

    public string QtyBucket { get; init; } = string.Empty;

    public bool IsAssignedHint { get; init; }

    public int Sales30d { get; init; }

    public int Sales90d { get; init; }

    public DateTime? LastSaleAt { get; init; }

    public DateTime Watermark { get; init; }
}

/// <summary>POS tombstone for an unassigned inventory row.</summary>
public sealed class PosAvailabilityTombstoneItemDto
{
    public string Kind { get; init; } = IndexFeedKinds.Tombstone;

    public Guid PointOfSaleId { get; init; }

    public Guid ProductId { get; init; }

    public string Reason { get; init; } = PosTombstoneReasons.Unassigned;

    public DateTime At { get; init; }
}

/// <summary>
/// The WHOLE set of points of sale and whether each one is trading, as of one instant (C43).
/// </summary>
/// <remarks>
/// <para>
/// <b>A reading, not a page, and it deliberately does not derive from
/// <see cref="IndexFeedPageDto"/>.</b> There is no cursor, no <c>hasMore</c> and no
/// <c>pageSize</c>: inheriting that shape would add three permanently meaningless fields to a
/// contract with no use for them, which is the same reasoning that kept
/// <c>computedAsOf</c> off the catalog page.
/// </para>
/// <para>
/// <b>Why complete rather than cursored.</b> A keyset feed can only say what changed, so a
/// point of sale <em>removed</em> from the business emits nothing and would survive in the
/// consumer's table for ever. Only a statement of the whole set lets the consumer retire what
/// is no longer in it. The cardinality makes that affordable — this is a handful of rows,
/// against the thousands the availability feed pages through.
/// </para>
/// <para>
/// <b>Why it is not a field on the availability feed.</b> That feed is incremental by keyset
/// over the watermark of the inventory row, and a point of sale changing its activity touches
/// no inventory row: the watermark would not move, the incremental pass would re-emit nothing,
/// and the flag would freeze at whatever it held when the assignment last changed.
/// </para>
/// </remarks>
public sealed class PosShopsReadingDto
{
    public IReadOnlyList<PosShopItemDto> Items { get; init; } = [];

    /// <summary>The instant this reading was taken, so a consumer can date what it stored.</summary>
    public DateTime ComputedAsOf { get; init; }
}

/// <summary>
/// One point of sale and whether it is trading. No code, no name, no address (C43).
/// </summary>
/// <remarks>
/// The consumer counts and does not name: it answers "how many active shops hold no
/// assortment". Sending a descriptive attribute would put a second copy of a fact this schema
/// owns inside the AI schema, where it would go stale between drains with nobody watching it —
/// and it would widen a feed that exists to carry one boolean.
/// </remarks>
public sealed class PosShopItemDto
{
    public Guid PointOfSaleId { get; init; }

    /// <summary>
    /// Reported for inactive shops too, never omitted: <em>closed</em> and <em>deleted</em>
    /// need opposite treatment from the consumer — the first keeps its row and stops counting,
    /// the second loses its row — and omission would make them indistinguishable on the wire.
    /// </summary>
    public bool IsActive { get; init; }
}
