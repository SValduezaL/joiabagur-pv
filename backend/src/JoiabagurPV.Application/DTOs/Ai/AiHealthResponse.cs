namespace JoiabagurPV.Application.DTOs.Ai;

/// <summary>
/// Health report returned by the jbg-ai service, and served on to the administrator dashboard.
/// </summary>
/// <remarks>
/// <para>
/// Every field here is deliberately non-sensitive. The response describes infrastructure, and it
/// is served to a browser: it carries no connection string, no database hostname and no fragment
/// of any credential. <see cref="Provider"/> in particular reports whether the embedding
/// credential is <em>configured</em> — never its value, and never whether the provider is
/// answering, which jbg-ai does not ask either.
/// </para>
/// <para>
/// The jbg-ai side declares this payload as an open mapping, on purpose: enriching it does not
/// move the frozen OpenAPI contract, whereas a typed response model there would. This class is
/// this side's reading of that mapping, and an unrecognised field is ignored rather than fatal.
/// </para>
/// </remarks>
public class AiHealthResponse
{
    /// <summary><c>OK</c> or <c>degraded</c>.</summary>
    public string Status { get; set; } = string.Empty;

    /// <summary>Version of the jbg-ai service that answered.</summary>
    public string Version { get; set; } = string.Empty;

    /// <summary><c>ok</c>, <c>unavailable</c>, or <c>not_configured</c>.</summary>
    /// <remarks>
    /// The name of the database, its host and its credentials are not part of this: only whether
    /// the service can reach it.
    /// </remarks>
    public string Database { get; set; } = string.Empty;

    /// <summary>State of the vector index.</summary>
    public AiHealthIndex Index { get; set; } = new();

    /// <summary><c>configured</c> or <c>missing</c> — presence of the credential, never its value.</summary>
    public string Provider { get; set; } = string.Empty;

    /// <summary>
    /// State of the point-of-sale availability projection, or <see langword="null"/> when the AI
    /// service that answered predates this section.
    /// </summary>
    /// <remarks>
    /// Nullable on purpose. A deployment can run an older <c>jbg-ai</c> image than this API — that
    /// is what the open mapping on the other side is for — and a card that threw on the absence
    /// would turn a version skew into a broken dashboard. Absent means "this service does not
    /// report it"; <c>unavailable</c> inside the section means "it reports it and does not know".
    /// </remarks>
    public AiHealthProjection? Projection { get; set; }
}

/// <summary>
/// Freshness of <c>ai.pos_projection</c>, which scopes assisted search to a shop's assortment.
/// </summary>
/// <remarks>
/// <para>
/// <strong>The age is the drain's, not a shop's.</strong> The checkpoint it comes from holds one
/// row per feed, so every point of sale reports the same number. A field named as though it were
/// per-shop would be false, and the first person to read it would act on it.
/// </para>
/// <para>
/// A stale projection does <em>not</em> hide products. The .NET side still applies the truth when
/// it hydrates, so what staleness costs is a short page, never a missing piece. The card's copy
/// says so, because "results may be incomplete" is true and "results are unreliable" is not.
/// </para>
/// </remarks>
public class AiHealthProjection
{
    /// <summary><c>ok</c>, <c>stale</c>, <c>never_drained</c>, or <c>unavailable</c>.</summary>
    /// <remarks>
    /// <c>never_drained</c> is kept apart from <c>stale</c> because they need different actions:
    /// a projection nobody has ever drained answers 503 to every scoped retrieval, while a stale
    /// one serves a wider window and declares it.
    /// </remarks>
    public string Status { get; set; } = string.Empty;

    /// <summary>When the feed was last drained, or null when it never was.</summary>
    public DateTimeOffset? SyncedAt { get; set; }

    /// <summary>When the feed was last drained in full.</summary>
    public DateTimeOffset? FullSyncedAt { get; set; }

    /// <summary>Seconds since the last drain, or null when it never ran.</summary>
    public double? AgeSeconds { get; set; }

    /// <summary>The staleness ceiling the AI service is configured with.</summary>
    /// <remarks>
    /// Travels with the verdict so this side can explain it without knowing how the other side is
    /// configured. Recomputing the verdict here from the age would put the threshold in two
    /// places, and the two would drift.
    /// </remarks>
    public int? CeilingSeconds { get; set; }

    /// <summary>What the retrieval guard decided, or null when it could not be decided.</summary>
    public bool? Stale { get; set; }

    /// <summary>Pages recorded as failed for this feed. Cumulative, not "the last run's".</summary>
    public int? FailedPages { get; set; }

    /// <summary>Points of sale present in the projection.</summary>
    public int? PointsOfSale { get; set; }

    /// <summary>
    /// Of those, how many hold no assigned row — each of which answers 503 to every scoped
    /// retrieval while the deployment looks healthy from outside, because this API degrades
    /// correctly to its lexical path and answers 200.
    /// </summary>
    public int? ShopsWithoutScope { get; set; }
}

/// <summary>
/// Vector index section of the health report.
/// </summary>
public class AiHealthIndex
{
    /// <summary>Documents currently indexed. Zero means an empty environment, not a broken one.</summary>
    public int Documents { get; set; }

    /// <summary>
    /// Embedding model recorded on the index rows, or <c>null</c> when the index is empty.
    /// </summary>
    public string? Model { get; set; }

    /// <summary>Embedding model the service is configured to query with.</summary>
    public string? ConfiguredModel { get; set; }

    /// <summary><c>ok</c>, <c>model_mismatch</c>, or <c>unavailable</c>.</summary>
    /// <remarks>
    /// <c>model_mismatch</c> is the quietest failure the deployment has: queries embedded with one
    /// model against documents embedded with another compare two different vector spaces, and the
    /// result is noise returned with a 200 and no log line. It is reported explicitly here so the
    /// dashboard can show it as an error rather than leaving somebody to infer it.
    /// </remarks>
    public string Status { get; set; } = string.Empty;
}
