using JoiabagurPV.Application.DTOs.Ai;

namespace JoiabagurPV.Application.Interfaces;

/// <summary>
/// Serves assisted catalog search: retrieval, authoritative hydration, degradation and
/// telemetry.
/// </summary>
public interface IAssistedSearchService
{
    /// <summary>
    /// Runs one assisted search on behalf of a user.
    /// </summary>
    /// <param name="request">Query, point of sale, page size and quick filters.</param>
    /// <param name="userId">Who is searching.</param>
    /// <param name="role">Their role, carried into the service token.</param>
    /// <param name="isAdmin">
    /// Whether the caller may search on a point of sale they hold no assignment for. Passed in
    /// rather than derived here, following the pattern the sales module already uses.
    /// </param>
    /// <remarks>
    /// This method does not throw on an AI failure. Every failure mode of the gateway — an open
    /// circuit, an exhausted budget, a transport error, a route with no implementation, rejected
    /// credentials — degrades to the lexical searcher and is reported through
    /// <see cref="AssistedSearchResponse.AiAvailable"/>. The system never falls over because of
    /// the AI.
    /// </remarks>
    Task<AssistedSearchResult> SearchAsync(
        AssistedSearchRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Reports which assisted paths are switched on for a scope: one point of sale, or every one
    /// of them.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Synchronous, and deliberately so: it reads configuration and touches neither the database
    /// nor the AI service. Returning a task would invite a later change to put a call behind it,
    /// and a call is the one thing this must never make — the screen asks this before every
    /// search, and paying for that would exhaust the quota of the feature it is asking about.
    /// </para>
    /// <para>
    /// The scope and not only a shop, since C40_FIX: while this answered for a named point of sale
    /// alone, a screen offering the wider scope had nothing to read, so the generative path came
    /// out disabled with no reason to show. That is the shape of failure this route was created to
    /// remove, and it was still reachable one scope along.
    /// </para>
    /// </remarks>
    /// <param name="pointOfSaleId">The shop, or <see langword="null"/> for every one of them.</param>
    AiSearchAvailabilityResponse GetAvailability(Guid? pointOfSaleId);
}

/// <summary>
/// Short-lived store of the candidates the AI service returned, so a repeated query does not pay
/// for a second embedding.
/// </summary>
public interface IAssistedSearchCandidateCache
{
    /// <summary>
    /// Builds the cache key. Always includes the point of sale, even while retrieval ignores it.
    /// </summary>
    string BuildKey(Guid pointOfSaleId, string query, AiSearchFilters filters, int window);

    /// <summary>Reads a cached candidate set.</summary>
    bool TryGet(string key, out AiSearchResponse? candidates);

    /// <summary>Stores a candidate set for the configured lifetime.</summary>
    void Set(string key, AiSearchResponse candidates);
}
