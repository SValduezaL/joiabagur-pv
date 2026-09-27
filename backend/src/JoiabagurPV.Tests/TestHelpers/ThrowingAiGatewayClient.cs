using JoiabagurPV.Application.DTOs.Ai;
using JoiabagurPV.Application.Interfaces;

namespace JoiabagurPV.Tests.TestHelpers;

/// <summary>
/// Base for hand-written doubles of <see cref="IAiGatewayClient"/>: every operation throws
/// <see cref="NotSupportedException"/> until a derived double overrides the ones it uses.
/// </summary>
/// <remarks>
/// <para>
/// The interface grows by rule — each contracted endpoint is added by the change that first calls
/// it — and before this class every hand-written double had to be edited each time it did, seven
/// of them when C34 added two operations. Deriving from here, a double names only what its test
/// exercises, and the next operation breaks nothing.
/// </para>
/// <para>
/// Throwing rather than returning an empty response on purpose: a double answered on a path the
/// test did not expect should fail loudly, not hand back a plausible nothing.
/// </para>
/// </remarks>
public abstract class ThrowingAiGatewayClient : IAiGatewayClient
{
    public virtual Task<AiSearchResponse> SearchAsync(
        AiSearchRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(SearchAsync));

    public virtual Task<AiEnrichResponse> EnrichAsync(
        AiEnrichRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(EnrichAsync));

    public virtual Task<AiHealthResponse> HealthAsync(CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(HealthAsync));

    public virtual Task<AiFamilySuggestResponse> SuggestFamiliesAsync(
        AiFamilySuggestRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(SuggestFamiliesAsync));

    public virtual Task<AiFamilyAuditResponse> AuditFamiliesAsync(
        AiFamilyAuditRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(AuditFamiliesAsync));

    public virtual Task<AiAssistSaleResponse> AssistSaleAsync(
        AiAssistSaleRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(AssistSaleAsync));

    public virtual Task<AiSubstitutesResponse> SubstitutesAsync(
        AiSubstitutesRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(SubstitutesAsync));

    public virtual Task<AiAssistAgentResponse> AssistAgentAsync(
        AiAssistAgentRequest request, AiCallScope scope, CancellationToken cancellationToken = default) =>
        throw new NotSupportedException(nameof(AssistAgentAsync));
}
