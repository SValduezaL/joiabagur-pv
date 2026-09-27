using JoiabagurPV.Application.DTOs.Ai;

namespace JoiabagurPV.Application.Interfaces;

/// <summary>
/// Serves the free-query search: the third assistance mode, and the one an operator could not
/// reach until C40.
/// </summary>
public interface IFreeQuerySearchService
{
    /// <summary>
    /// Answers one free-text query for a point of sale.
    /// </summary>
    /// <param name="request">The query, the shop, the page size, the episode and the filters.</param>
    /// <param name="userId">Who is asking.</param>
    /// <param name="role">Their role, carried into the service token.</param>
    /// <param name="isAdmin">
    /// Whether the caller may search on a shop they hold no assignment for, and whether the
    /// response carries what the request cost. The funnel is an administrator's view.
    /// </param>
    /// <remarks>
    /// <strong>Never throws on an AI failure.</strong> Every failure mode of the gateway — an open
    /// circuit, an exhausted budget, a transport error, an unimplemented route, rejected
    /// credentials — degrades to an answer with no argument and a reason the screen can word.
    /// The panel does not break when the AI does.
    /// </remarks>
    Task<FreeQuerySearchResult> SearchAsync(
        FreeQuerySearchRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default);
}
