using JoiabagurPV.Application.DTOs.Ai;

namespace JoiabagurPV.Application.Interfaces;

/// <summary>
/// Serves the sale agent: a conversation over several turns, and the pillar of the project that had
/// no operator surface at all until C42.
/// </summary>
public interface IAgentAssistService
{
    /// <summary>
    /// Answers the last turn of one conversation for a point of sale, or for every one of them.
    /// </summary>
    /// <param name="request">The transcript, the shop, the page size and the episode.</param>
    /// <param name="userId">Who is asking.</param>
    /// <param name="role">Their role, carried into the service token.</param>
    /// <param name="isAdmin">
    /// Whether the caller may converse about a shop they hold no assignment for, and whether the
    /// response carries what the turn cost. The funnel is an administrator's view.
    /// </param>
    /// <remarks>
    /// <para>
    /// <strong>Never throws on an AI failure.</strong> Every failure mode of the gateway — an open
    /// circuit, an exhausted budget, a transport error, an unimplemented route, rejected
    /// credentials — degrades to an answer with no argument and a reason the screen can word. And
    /// the degradations this route reports <em>inside</em> a successful response, when its provider
    /// falls or no credential is configured, arrive as answers carrying their stop reason: they are
    /// not converted into failures here either.
    /// </para>
    /// <para>
    /// <strong>The three transcript caps are validated before the call.</strong> A caller must not
    /// spend a provider call to be told the request was malformed, and on this route that call
    /// competes for a quota that admits about one request per minute.
    /// </para>
    /// </remarks>
    Task<AgentAssistResult> AnswerAsync(
        AgentAssistRequest request,
        Guid userId,
        string role,
        bool isAdmin,
        CancellationToken cancellationToken = default);
}
