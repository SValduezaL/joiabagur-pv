using JoiabagurPV.Application.DTOs.Ai;

namespace JoiabagurPV.Application.Interfaces;

/// <summary>
/// Outbound integration with the jbg-ai service.
/// </summary>
/// <remarks>
/// The surface is deliberately one operation. Every other contracted endpoint is added by the
/// change that first calls it: adding a method here is a small diff, whereas the wire contract
/// it consumes is frozen and expensive to renegotiate.
/// </remarks>
public interface IAiGatewayClient
{
    /// <summary>
    /// Runs a catalog retrieval against jbg-ai.
    /// </summary>
    /// <param name="request">Query, page size and catalog-side filters.</param>
    /// <param name="scope">Caller identity and point-of-sale scope, already authorised.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>
    /// Every candidate the service produced — more than the requested page size by design.
    /// Truncating belongs to the caller, which hydrates and discards first.
    /// </returns>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    Task<AiSearchResponse> SearchAsync(
        AiSearchRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Asks jbg-ai to propose enriched profiles for a batch of products.
    /// </summary>
    /// <param name="request">Products to enrich. At most <see cref="AiEnrichRequest.MaxBatchSize"/>.</param>
    /// <param name="scope">Caller identity. Must be a catalog scope: the catalog has no point of sale.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>
    /// One proposal per requested product, each field carrying its own confidence and whether a
    /// rule or a model produced it. Nothing is persisted on either side by this call.
    /// </returns>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    /// <exception cref="ArgumentException">The scope is not a catalog scope.</exception>
    Task<AiEnrichResponse> EnrichAsync(
        AiEnrichRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Reads the jbg-ai health report: database reachability, index state, and whether the
    /// embedding provider credential is configured.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The report as the service produced it.</returns>
    /// <remarks>
    /// <para>
    /// Unauthenticated on the wire, because <c>GET /health</c> is public on the jbg-ai side. The
    /// authorisation that matters is on this side: the endpoint that calls this is restricted to
    /// administrators, since the report describes infrastructure.
    /// </para>
    /// <para>
    /// <strong>This call does not share the circuit breaker</strong> of the retrieval and
    /// enrichment clients. Its whole purpose is to diagnose the system precisely when the main
    /// path is failing, and a probe that fails whenever the circuit is open answers "broken" by
    /// refusing to look — which is the one answer it must never give.
    /// </para>
    /// </remarks>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, or a non-success status. There is no retry and no breaker.
    /// </exception>
    Task<AiHealthResponse> HealthAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Asks jbg-ai to propose product families over the indexed catalog.
    /// </summary>
    /// <param name="request">Optional narrowing by piece type and proposal cap.</param>
    /// <param name="scope">Caller identity. Must be a catalog scope.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>
    /// The proposals, plus the two kinds of omission: groups a guard refused and products the
    /// piece-type gate excluded. All three are returned as received — filtering or reordering
    /// them here would decide on the administrator's behalf what is worth looking at.
    /// </returns>
    /// <remarks>
    /// <para>
    /// The call proposes and never writes. Creating the approved families is this side's work,
    /// through <see cref="IProductFamilyService"/>, because only that path stamps
    /// <c>Product.UpdatedAt</c> on entering and leaving products — the watermark an incremental
    /// index pull reads. Writing the membership rows any other way leaves the index blind to
    /// them, and does so without raising anything.
    /// </para>
    /// <para>
    /// <strong>There is no degraded mode.</strong> Unlike search, which drops to the lexical
    /// index when the service is unreachable, a partial grouping would mean inventing catalog
    /// structure. A failure here produces no proposals at all.
    /// </para>
    /// </remarks>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    Task<AiFamilySuggestResponse> SuggestFamiliesAsync(
        AiFamilySuggestRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Audits the families that already exist, and nominates the products that look like members.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A separate route from suggestion rather than a mode of it, because the two read disjoint
    /// populations — suggestion reads products that belong to no family, this reads the families
    /// that exist — and converge differently: suggestion empties itself as batches are approved,
    /// while the audit is a standing signal.
    /// </para>
    /// <para>
    /// <strong>Judged pairs travel in the request.</strong> The service stores no verdict, so this
    /// side sends what it knows from <c>FamilyReviewVerdicts</c> on every call. Omitting them
    /// simply reports judgements the administrator has already made.
    /// </para>
    /// <para>
    /// <strong>Reads and never writes.</strong> Recording a verdict is a different operation and
    /// does not pass through this client, which is what makes "the audit changed nothing" an
    /// assertion a test can make.
    /// </para>
    /// <para>
    /// <strong>A failure is not an empty audit.</strong> There is no degraded mode: this feeds a
    /// catalog-quality screen, where an empty answer reads as "the catalog is clean". Returning
    /// one because the service did not respond would assert by accident the very conclusion the
    /// review exists to establish with evidence.
    /// </para>
    /// </remarks>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    Task<AiFamilyAuditResponse> AuditFamiliesAsync(
        AiFamilyAuditRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Asks jbg-ai for the sale assistance of one product: its group, warnings, citations and a
    /// generated argument that still carries the price and stock placeholders.
    /// </summary>
    /// <param name="request">
    /// The anchored product and, optionally, the operator's question. A request without a product
    /// is refused: this client serves only the modes whose placeholders refer to one product.
    /// </param>
    /// <param name="scope">Caller identity and point-of-sale scope, already authorised.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The response as received; nothing is hydrated, filtered or resolved here.</returns>
    /// <remarks>
    /// Runs on its own named client, <c>ai-assist</c>, with the generative time budget and its
    /// own circuit: a slow language model must not open the retrieval circuit. It is retried
    /// <strong>only</strong> when the connection never opened — any other failure may have
    /// happened after the service began generating, and a second attempt would double the wait
    /// at the counter and the paid model calls.
    /// </remarks>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiRequestRejectedException">
    /// HTTP 422: the service cannot process the product. Not an outage.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    /// <exception cref="ArgumentException">
    /// The scope is not a point-of-sale scope, or the request names no product.
    /// </exception>
    Task<AiAssistSaleResponse> AssistSaleAsync(
        AiAssistSaleRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Asks jbg-ai for the products interchangeable with one product.
    /// </summary>
    /// <param name="request">The product, the window size and an optional reason.</param>
    /// <param name="scope">Caller identity and point-of-sale scope, already authorised.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>
    /// Every candidate of the over-retrieval window, in the order received. Excluding by stock
    /// and truncating belong to the caller, which hydrates first.
    /// </returns>
    /// <remarks>
    /// Runs on the retrieval client, its budget and its circuit: the route calls no model
    /// provider and shares retrieval's failure domain.
    /// </remarks>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiRequestRejectedException">
    /// HTTP 422: the service cannot process the product. Not an outage.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    /// <exception cref="ArgumentException">The scope is not a point-of-sale scope.</exception>
    Task<AiSubstitutesResponse> SubstitutesAsync(
        AiSubstitutesRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Asks the sale agent to answer the last turn of a conversation. C42.
    /// </summary>
    /// <param name="request">The transcript so far and the page size wanted after hydration.</param>
    /// <param name="scope">Caller identity and point-of-sale scope, already authorised.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>
    /// Everything the deterministic free-query response carries, <strong>plus</strong> whether a
    /// budget cut the answer short, why the loop stopped, how many turns and tool calls it paid
    /// for, the per-iteration trace and the version of the argument prompt. Each group carries the
    /// provenance of its evidence.
    /// </returns>
    /// <remarks>
    /// <para>
    /// Runs on the <c>ai-agent</c> client, its own budget and its own circuit. Not the generative
    /// route's: the agent's median latency is of the order of the total that route declares as its
    /// ceiling, so its budget would cut a large share of these requests, and its circuit would open
    /// over a route that is answering correctly.
    /// </para>
    /// <para>
    /// <strong>A degradation the service reports inside a 200 is not a failure of this call.</strong>
    /// The loop answers successfully when its provider falls or when no credential is configured,
    /// saying so in a closed stop-reason vocabulary. Such a response comes back as a response,
    /// recorded as a metric, and the circuit stays closed.
    /// </para>
    /// <para>
    /// <strong>No point of sale is sent in the body.</strong> The contract accepts one and ignores
    /// it; scope comes from the token, and on this route the token is what decides whether the
    /// availability prefilter applies at all.
    /// </para>
    /// </remarks>
    /// <exception cref="Exceptions.AiUnavailableException">
    /// Timeout, transport failure, open circuit, or a server error other than 501.
    /// </exception>
    /// <exception cref="Exceptions.AiRequestRejectedException">
    /// HTTP 422: the service cannot process the transcript. Not an outage, and normally
    /// unreachable — the caller validates the three caps before spending the call.
    /// </exception>
    /// <exception cref="Exceptions.AiNotImplementedException">
    /// The route is contracted but has no implementation yet.
    /// </exception>
    /// <exception cref="Exceptions.AiGatewayConfigurationException">
    /// The service rejected the credentials.
    /// </exception>
    /// <exception cref="ArgumentException">
    /// The scope is neither a point-of-sale scope nor the every-point-of-sale scope, or the
    /// transcript carries no turn.
    /// </exception>
    Task<AiAssistAgentResponse> AssistAgentAsync(
        AiAssistAgentRequest request,
        AiCallScope scope,
        CancellationToken cancellationToken = default);
}
