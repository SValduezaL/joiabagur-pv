# ai-gateway-client Specification

## Purpose
Outbound integration between the .NET backend and the `jbg-ai` service: a typed client for catalog retrieval, enrichment, assisted family grouping and the audit of persisted families that maps the frozen contract without truncating it, a call scope that cannot exist without a real point of sale, emission of the internal HS256 service token with the claims the service requires and none it rejects, bounded degradation isolated per route family, failure modes a caller can branch on, end-to-end trace correlation across the hop, configuration validated at start-up, and a guard that breaks the build when the client drifts from the committed contract.
## Requirements

### Requirement: Typed gateway client exposes catalog retrieval

The backend SHALL provide a typed client for the `jbg-ai` service exposing exactly one operation in this change: catalog retrieval against `POST /v1/retrieval/products`. The client MUST serialize and deserialize the frozen contract using `snake_case` property names on the wire. `family_id` and `variant_label` MUST map to nullable values, because the contract guarantees an explicit null rather than an absent field. The client MUST NOT send `pos_id` in the request body, since the service ignores it and the scope comes from the token. The client MUST report `candidates_returned` as received and MUST NOT truncate the result list: `top_k` is the page size the caller wants after hydrating, and truncation belongs to the hydrating caller.

#### Scenario: Successful response is mapped in full
- **WHEN** the AI service answers HTTP 200 to a retrieval request
- **THEN** the client returns an object exposing `results`, `candidates_returned`, `low_confidence`, `trace_id` and `effective_pos_id`
- **AND** each result exposes `product_id`, `sku`, `score`, `match_reasons` and `materials` as a list

#### Scenario: Contract nulls survive mapping
- **WHEN** a returned result carries `family_id` and `variant_label` set to null
- **THEN** both properties are null on the mapped object
- **AND** mapping neither throws nor substitutes a default value

#### Scenario: Over-retrieval is reported, not truncated
- **WHEN** the service returns more candidates than the requested `top_k`
- **THEN** the client returns every candidate it received
- **AND** `candidates_returned` reports the same count the service reported

### Requirement: Typed gateway client exposes catalog enrichment

The client SHALL expose an operation for catalog enrichment against `POST /v1/enrich/products`, serializing and deserializing the frozen contract with `snake_case` property names on the wire. Every proposed value MUST map its confidence and its provenance — `rule` or `inferred` — as first-class values rather than being flattened away, because the review policy of the consuming capability is expressed entirely in terms of them. Proposed values the contract declares as nullable MUST map to nullable values. The operation MUST carry a catalog-wide call scope.

#### Scenario: Proposed profiles are mapped with confidence and provenance
- **WHEN** the AI service answers HTTP 200 to an enrichment request
- **THEN** the client returns one proposed profile per requested product
- **AND** each proposed field exposes its confidence and whether it is `rule` or `inferred`

#### Scenario: Absent proposed fields survive mapping
- **WHEN** a returned profile carries a null piece type, stone type or size label
- **THEN** those properties are null on the mapped object
- **AND** mapping neither throws nor substitutes a default value

### Requirement: Typed gateway client exposes family suggestion

The backend SHALL extend the typed `jbg-ai` client with one operation for assisted family grouping against `POST /v1/families/suggest`, added by the change that first calls it. The client MUST serialize and deserialize the frozen contract using `snake_case` property names on the wire. `variant_label` MUST map to a nullable value, because the contract guarantees an explicit null rather than an absent field for a member with no distinguishing token. The client MUST report the proposals and the rejected groups as received and MUST NOT filter, reorder or truncate either list: deciding what to accept belongs to the administrator, not to the transport.

The client MUST NOT invoke this operation on behalf of an operator: the calling scope is the administrator that the .NET controller has already authorised.

#### Scenario: Proposals are surfaced without truncation

- **WHEN** the service returns a set of proposals and a set of rejected groups
- **THEN** the client returns both lists in full and in the order received
- **AND** it does not drop members flagged for review

#### Scenario: A member with no variant maps to an explicit null

- **WHEN** the service returns a member whose `variant_label` is null
- **THEN** the client maps it to a nullable value rather than to an empty string
- **AND** the distinction between "no variant" and "empty variant" is preserved

#### Scenario: Wire names follow the frozen contract

- **WHEN** the client serializes a family suggestion request
- **THEN** the property names on the wire are `snake_case`
- **AND** the payload validates against the committed contract

### Requirement: Typed gateway client exposes the family audit

The backend SHALL extend the typed `jbg-ai` client with one operation for auditing persisted families against `POST /v1/families/audit`, added by the change that first calls it. The client MUST serialize and deserialize the frozen contract using `snake_case` property names on the wire.

The client MUST send the `(product, family)` pairs that already carry a human verdict, because the service holds none of its own and would otherwise report judgements the administrator has already made. Assembling that set from the backend's own store is the client's responsibility, not the service's.

The client MUST report the flagged members and the candidates as received and MUST NOT filter, reorder or truncate either list: deciding what deserves attention belongs to the administrator, not to the transport. The margin of a flagged member and the similarity, worst-sibling similarity, data origin and purity count of a candidate MUST all survive the mapping, because they are what the reviewer judges by.

The client MUST NOT invoke this operation on behalf of an operator: the calling scope is the administrator that the .NET controller has already authorised. This operation MUST NOT write to the catalogue; recording a verdict is a separate backend operation that does not pass through this client.

#### Scenario: Both lists are surfaced without truncation

- **WHEN** the service returns flagged members and candidates
- **THEN** the client returns both lists in full and in the order received
- **AND** it does not drop a candidate for its data origin or its purity count

#### Scenario: The evidence a reviewer judges by survives the mapping

- **WHEN** the service returns a candidate with its similarity, the target family's worst-sibling similarity, the margin between them, its data origin and its purity count
- **THEN** all of those values are present on the mapped result
- **AND** a flagged member keeps its margin and the identity of the product that beat its worst sibling

#### Scenario: Pairs already judged travel with the request

- **WHEN** the backend holds verdicts for a set of `(product, family)` pairs and the audit is requested
- **THEN** the client includes those pairs in the request
- **AND** the service is not expected to know them by any other means

#### Scenario: Wire names follow the frozen contract

- **WHEN** the client serializes a family audit request
- **THEN** the property names on the wire are `snake_case`
- **AND** the payload validates against the committed contract

### Requirement: Typed gateway client exposes sale assistance and substitutes

The backend SHALL extend the typed `jbg-ai` client with two operations, added by the change that first calls them: sale assistance against `POST /v1/assist/sale` and substitutes against `POST /v1/retrieval/substitutes`, both serializing and deserializing the frozen contract with `snake_case` property names on the wire.

Both operations MUST require a point-of-sale scope or the scope that covers every point of sale, and MUST reject a catalog-wide scope before any request is issued. Both MUST NOT send `pos_id` in the request body, since the service ignores it and the scope comes from the token. The sale assistance request MUST carry at least one anchor, a product or a query; a request carrying neither MUST NOT be issued. A request carrying a query and no product MUST be issued, because the free-query mode no longer writes the price or stock placeholders and therefore has nothing that needs resolving against a single piece.

The sale assistance request MAY carry catalog-side filters, which MUST be serialized with the same field names the retrieval request uses and MUST be omitted when the caller selected none.

Every value the contract declares as nullable MUST map to a nullable value: the family, its label and the variant label of a member, the clarification question, the prompt version and the product a citation supports. Every citation MUST keep its identifier, document title, section title, document type, claim scope, score and snippet. The substitutes operation MUST report the candidates and `candidates_returned` as received and MUST NOT filter, reorder or truncate them: the window is larger than the page on purpose, and excluding by stock belongs to the hydrating caller.

The completion event of a sale assistance call MUST NOT carry the argument, and the question MUST NOT be emitted above debug level.

#### Scenario: A sale assistance response is mapped in full
- **WHEN** the AI service answers HTTP 200 to a sale assistance request
- **THEN** the client returns the intent, the groups with their members, the argument, the citations, the warnings, the clarification question, the usage, the abstention flag, the prompt version, the trace identifier and the effective point of sale
- **AND** each citation keeps its claim scope

#### Scenario: A free query with no product is issued
- **WHEN** the client is called with a query and no product identifier
- **THEN** the request is issued
- **AND** the body carries the query and no product identifier

#### Scenario: A request with neither anchor is refused
- **WHEN** the client is called with neither a product identifier nor a query
- **THEN** the call fails with an argument error
- **AND** no HTTP request is issued

#### Scenario: Selected filters travel with the request
- **WHEN** the client is called with a query and catalog-side filters
- **THEN** the body carries the filters with the field names the retrieval request uses

#### Scenario: Unselected filters are omitted
- **WHEN** the client is called with no catalog-side filters
- **THEN** the body carries no filters property

#### Scenario: Contract nulls survive mapping
- **WHEN** a returned group has a null family and a member has a null variant label
- **THEN** both properties are null on the mapped object
- **AND** mapping neither throws nor substitutes a default value

#### Scenario: The substitutes window is reported, not truncated
- **WHEN** the service returns more substitutes than the requested page size
- **THEN** the client returns every candidate it received, in the order received
- **AND** `candidates_returned` reports the same count the service reported

#### Scenario: No point of sale travels in the body
- **WHEN** the client serializes a sale assistance or a substitutes request
- **THEN** the payload contains no `pos_id` property
- **AND** the property names on the wire are `snake_case`

#### Scenario: A catalog scope is rejected before any request
- **WHEN** either operation is called with a catalog-wide scope
- **THEN** the call fails with an argument error
- **AND** no HTTP request is issued

### Requirement: Enrichment degrades on its own budget, isolated from retrieval

Catalog enrichment SHALL use its own named client with its own circuit-breaker state and its own configured time budget, sized for an extraction call rather than for retrieval. It MUST NOT be retried automatically, because a second attempt at an extraction duplicates model cost with no reason to expect a different result. A slow or failing enrichment call MUST NOT open the retrieval circuit, so it can never push an operator's search onto its degraded lexical path for a service that is answering retrieval correctly.

#### Scenario: Enrichment failures do not open the retrieval circuit
- **WHEN** enrichment calls fail repeatedly until the enrichment circuit opens
- **THEN** retrieval calls continue to be issued normally

#### Scenario: An enrichment failure is not retried
- **WHEN** the AI service answers an enrichment request with a server error
- **THEN** exactly one HTTP request was issued

#### Scenario: Enrichment resilience is configured explicitly
- **WHEN** the enrichment client is registered
- **THEN** its time budget and circuit breaker thresholds come from configuration rather than from framework defaults

### Requirement: Every gateway call carries a real point-of-sale scope

Every call to the gateway SHALL carry a call scope holding the user identifier, the role and, when the route has point-of-sale scope, the point-of-sale identifier. The scope type MUST expose exactly three construction paths and no more: one for point-of-sale scoped routes, which requires a concrete point of sale and MUST reject an empty point-of-sale identifier; one for catalog-wide routes, which carries no point of sale at all; and one for a search that deliberately covers every point of sale, which also carries none. All three MUST reject a blank role. No sentinel value MUST be accepted in place of a point of sale on any path, because from the change that introduces the soft prefilter onward the `pos_id` claim is the retriever's only hard filter, and a wildcard reaching it would be a cross-point-of-sale leak.

The third path is not a relaxation of the first: it is a different scope, and the guarantee it preserves is that an absent claim makes the availability prefilter not apply rather than match everything, and fails closed on any route that requires the claim.

A catalog-wide scope MUST be rejected by any point-of-sale scoped operation of the client, before any request is issued. The every-point-of-sale scope MUST be accepted only by catalog retrieval and by sale assistance, and MUST be rejected by every other point-of-sale operation — the sale card, substitutes and inventory — before any request is issued, because those operate on one shop's stock and have nothing to answer without one. The client MUST NOT perform authorization: the caller is responsible for having validated the user's assignment to that point of sale before constructing a point-of-sale scope, and for having validated that the user may search across every point of sale before constructing that scope.

#### Scenario: Scope requires a concrete point of sale
- **WHEN** code attempts to build a point-of-sale call scope with an empty point-of-sale identifier
- **THEN** construction fails with an argument error
- **AND** no construction path accepts a sentinel value in its place

#### Scenario: Blank role is rejected
- **WHEN** code attempts to build a call scope with a blank role
- **THEN** construction fails with an argument error

#### Scenario: Catalog scope carries no point of sale
- **WHEN** code builds a catalog-wide call scope
- **THEN** the resulting scope exposes no point-of-sale identifier
- **AND** construction succeeds without one

#### Scenario: Catalog scope cannot be used for retrieval
- **WHEN** a retrieval call is attempted with a catalog-wide scope
- **THEN** the call fails before any HTTP request is issued

#### Scenario: The every-point-of-sale scope carries no point of sale either
- **WHEN** code builds the scope that covers every point of sale
- **THEN** the resulting scope exposes no point-of-sale identifier
- **AND** it is distinguishable from a catalog-wide scope

#### Scenario: The every-point-of-sale scope is accepted by retrieval and assistance
- **WHEN** a catalog retrieval or a sale assistance call is made with the every-point-of-sale scope
- **THEN** the request is issued

#### Scenario: The every-point-of-sale scope is refused where one shop is mandatory
- **WHEN** a substitutes or an inventory call is attempted with the every-point-of-sale scope
- **THEN** the call fails with an argument error
- **AND** no HTTP request is issued

#### Scenario: No scope accepts a sentinel point of sale
- **WHEN** every construction path of the scope type is enumerated
- **THEN** there are exactly three
- **AND** none of them accepts a wildcard or placeholder point-of-sale identifier

### Requirement: Internal service token carries the frozen claims and nothing else

The client SHALL sign an internal service token with HS256 using a secret dedicated to this integration, separate from the user-facing signing key. The payload MUST contain the claims frozen by the AI service in `snake_case`: `user_id`, `role` and `trace_id`, each non-empty, plus `pos_id` when and only when the call scope carries a point of sale. A scope without a point of sale MUST produce a token with no `pos_id` claim at all, rather than one carrying an empty or placeholder value. It MUST contain an expiry derived from the configured time-to-live. It MUST NOT contain an audience claim, an issuer claim or a not-before claim, because the service validates tokens without expecting an audience and evaluates temporal claims with no clock tolerance. The token MUST be presented as a bearer credential on every request.

#### Scenario: Token carries the four frozen claims
- **WHEN** the client signs a token for a valid point-of-sale call scope
- **THEN** the payload contains `user_id`, `role`, `pos_id` and `trace_id` under exactly those names
- **AND** none of the four is empty

#### Scenario: Catalog token omits the point-of-sale claim
- **WHEN** the client signs a token for a catalog-wide call scope
- **THEN** the payload contains `user_id`, `role` and `trace_id`
- **AND** it contains no `pos_id` claim, empty or otherwise

#### Scenario: Token declares no audience and no issuer
- **WHEN** the client signs a token
- **THEN** the payload contains no audience claim and no issuer claim
- **AND** it contains no not-before claim

#### Scenario: Token expires after the configured lifetime
- **WHEN** the client signs a token with a configured time-to-live
- **THEN** the expiry equals the signing instant plus that lifetime

#### Scenario: Request presents the token as a bearer credential
- **WHEN** the client issues a retrieval request
- **THEN** the request carries an `Authorization` header with the signed token as a bearer credential

### Requirement: Contract failure modes are distinguishable by the caller

The client SHALL translate every documented outcome of the frozen contract into a distinguishable result, so a caller can decide whether to degrade, to surface a configuration fault or to stop. HTTP 401 MUST surface as a configuration fault, because the AI service is required to reject invalid tokens without disclosing the cause and the only actionable interpretation on this side is misconfiguration. HTTP 501 MUST surface as a not-implemented outcome, distinct from unavailability, because the contract uses it for routes whose real logic arrives in a later change. Timeouts, transport failures, HTTP 408, HTTP 5xx other than 501, and an open circuit MUST all surface as service unavailability. The client MUST NOT surface a raw transport exception to its caller.

For the sale assistance and substitutes operations, HTTP 422 MUST surface as a request-rejected outcome, distinct from unavailability, because the AI service answers it for a product it cannot process — absent from its index, inactive, or without an embedding — and reading it as an outage would present a product created before the last synchronisation as a failure of the service. Every other operation of the client MUST keep translating any other non-success status as unavailability; narrowing that shared translation for them is not part of this requirement.

#### Scenario: Authentication failure is reported as configuration fault
- **WHEN** the AI service answers HTTP 401
- **THEN** the client raises a configuration fault distinct from unavailability
- **AND** the failure is logged at error level

#### Scenario: Unimplemented route is reported as such
- **WHEN** the AI service answers HTTP 501
- **THEN** the client raises a not-implemented outcome distinct from unavailability

#### Scenario: Timeout is reported as unavailability
- **WHEN** the AI service does not answer within the configured time budget
- **THEN** the client raises service unavailability

#### Scenario: Transport failure is reported as unavailability
- **WHEN** the request fails at the transport level
- **THEN** the client raises service unavailability
- **AND** no raw transport exception reaches the caller

#### Scenario: A rejected product is not reported as unavailability
- **WHEN** the AI service answers HTTP 422 to a sale assistance or a substitutes request
- **THEN** the client raises a request-rejected outcome
- **AND** it is distinct from service unavailability and from a configuration fault

#### Scenario: Other operations keep their translation
- **WHEN** the AI service answers HTTP 422 to a retrieval request
- **THEN** the client raises service unavailability, as before

### Requirement: Family suggestion failures are distinguishable by the caller

The gateway client SHALL translate the failure modes of the family suggestion route onto the same typed errors the rest of the surface already uses, so that the controller can branch without inspecting transport details: a contracted-but-unimplemented route MUST surface as the not-implemented error, a timeout, transport failure, open circuit or server error MUST surface as the unavailable error, and rejected credentials MUST surface as the configuration error.

Family suggestion MUST NOT have a lexical or degraded fallback. Unlike search, which can drop to the lexical index, there is no safe degraded answer here: proposing groupings without the index would mean inventing catalogue structure.

#### Scenario: An unimplemented route is distinguishable from an unavailable one

- **WHEN** the service answers the family suggestion route with 501
- **THEN** the client raises the not-implemented error
- **AND** a timeout or a server error raises the unavailable error instead

#### Scenario: No degraded proposal is produced

- **WHEN** the family suggestion call fails for any reason
- **THEN** the client returns no proposals at all
- **AND** it does not synthesise a fallback grouping

### Requirement: Family audit failures are distinguishable by the caller

The backend SHALL let the caller of the audit tell apart a route that is not implemented, a dependency the service cannot reach, and a request the contract cannot accept. An audit that fails MUST NOT be reported as an audit that found nothing: a reviewer told "there is nothing to review" when the service never answered would conclude the catalogue is clean. An empty response body MUST be treated as a failure and never as a result, because on this route "empty" and "clean catalogue" are indistinguishable to the screen and only one of them is true.

A request the contract cannot accept MUST be refused **before it is sent**, which is a stronger guarantee than telling a refusal apart afterwards. A refusal the service itself issues surfaces as an unavailable service carrying the status code: the translation from HTTP status to exception is shared by every route on this client, and narrowing it is not this change's to make.

A failed audit MUST leave no verdict, no family and no membership modified.

#### Scenario: An unreachable dependency is not an empty audit

- **WHEN** the service cannot reach the index and the audit fails
- **THEN** the caller receives a failure distinguishable from a successful audit with no findings
- **AND** no empty list of flagged members or candidates is returned as though it were a result

#### Scenario: An invalid request is refused before it is sent

- **WHEN** the request carries a scope or a candidate cap the frozen contract cannot accept
- **THEN** the client refuses it without calling the service
- **AND** the caller can tell that refusal from an unavailable service and from a route that is not implemented

#### Scenario: An empty body is a failure, not an empty audit

- **WHEN** the service answers successfully with no body
- **THEN** the caller receives a failure
- **AND** no empty list of flagged members or candidates is returned as though it were a result

#### Scenario: A failed audit changes nothing

- **WHEN** an audit fails for any reason
- **THEN** no verdict is created or modified
- **AND** no family or membership is created, modified or removed

### Requirement: Retry policy never retries a permanent condition

The client SHALL retry at most once, and only for conditions that can plausibly succeed on a second attempt: transport failures, timeouts, HTTP 408 and HTTP 5xx other than 501. It MUST NOT retry HTTP 401, which reflects configuration rather than a transient fault. It MUST NOT retry HTTP 501, which reflects a route that has no implementation yet. It MUST NOT retry HTTP 422, which reflects a request the service cannot process. Retrying any of them would consume the request time budget with no possibility of success.

The sale assistance operation MUST retry only a failure to establish the connection, and nothing else, not even a timeout: every other failure may have happened after the service began generating, so a second attempt would double both the wait at the counter and the number of paid model calls.

#### Scenario: Transient server error is retried once
- **WHEN** the AI service answers HTTP 503 on the first attempt and HTTP 200 on the second
- **THEN** the client returns the mapped response
- **AND** exactly two HTTP requests were issued

#### Scenario: Unimplemented route is not retried
- **WHEN** the AI service answers HTTP 501
- **THEN** exactly one HTTP request was issued

#### Scenario: Authentication failure is not retried
- **WHEN** the AI service answers HTTP 401
- **THEN** exactly one HTTP request was issued

#### Scenario: A rejected request is not retried
- **WHEN** the AI service answers HTTP 422
- **THEN** exactly one HTTP request was issued

#### Scenario: A sale assistance timeout is not retried
- **WHEN** a sale assistance request does not complete within its time budget
- **THEN** exactly one HTTP request was issued
- **AND** the client raises service unavailability

#### Scenario: A sale assistance server error is not retried
- **WHEN** the AI service answers a sale assistance request with HTTP 503
- **THEN** exactly one HTTP request was issued

#### Scenario: A sale assistance connection that never opened is retried once
- **WHEN** the connection for a sale assistance request cannot be established on the first attempt and succeeds on the second
- **THEN** the client returns the mapped response
- **AND** exactly two connection attempts were made

### Requirement: Degradation is bounded per call and isolated per route family

Each gateway call SHALL be bounded by a configured time budget, at most one retry and a circuit breaker with explicitly configured thresholds. Default resilience presets MUST NOT be accepted unconfigured, because their default time budget and retry count contradict the agreed limits. Retrieval MUST use its own named client and its own circuit breaker state, isolated from any future generative route, so that a slow generative call cannot open the retrieval circuit and cannot trigger the caller's degraded path for a service that is answering correctly. While the circuit is open, the client MUST fail immediately without issuing an HTTP request.

Sale assistance is that generative route: it MUST use its own named client, its own circuit breaker state and its own configured time budget, sized for the provider calls of one request rather than for retrieval. Substitutes MUST use the retrieval client, its budget and its circuit, because they are a retrieval route that calls no model provider and shares its failure domain. A response that the service answers successfully after degrading internally MUST NOT count as a failure for any circuit.

#### Scenario: Open circuit fails fast without a request
- **WHEN** the retrieval circuit breaker is open and a retrieval call is made
- **THEN** the client raises service unavailability
- **AND** no HTTP request is issued

#### Scenario: Retrieval resilience is configured explicitly
- **WHEN** the retrieval client is registered
- **THEN** its time budget, retry count and circuit breaker thresholds come from configuration rather than from framework defaults

#### Scenario: Sale assistance failures do not open the retrieval circuit
- **WHEN** sale assistance calls fail repeatedly until the sale assistance circuit opens
- **THEN** retrieval and substitutes calls continue to be issued normally

#### Scenario: Sale assistance resilience is configured explicitly
- **WHEN** the sale assistance client is registered
- **THEN** its time budget and circuit breaker thresholds come from configuration rather than from framework defaults
- **AND** its circuit state is not shared with any other named client

#### Scenario: Substitutes use the retrieval client
- **WHEN** the retrieval circuit breaker is open and a substitutes call is made
- **THEN** the client raises service unavailability
- **AND** no HTTP request is issued

### Requirement: Gateway calls are traceable end to end

Every gateway call SHALL carry a correlation identifier obtained from the ambient request context, propagated both as the `trace_id` claim of the service token and as a request header, so the same call can be followed through the logs of both services including responses the service rejects before reaching a handler. Each call MUST emit a start event, and either a completion event or a failure event. The completion event MUST carry the endpoint, correlation identifier, status code, elapsed milliseconds, attempt count, `candidates_returned`, result count and `low_confidence`. The failure event MUST carry the endpoint, correlation identifier, elapsed milliseconds, attempt count, a classified outcome and the configured base address. The query text MUST NOT be emitted above debug level.

#### Scenario: Correlation identifier travels in claim and header
- **WHEN** the client issues a retrieval request with a known correlation identifier
- **THEN** the service token carries it as the `trace_id` claim
- **AND** the request carries it as a header

#### Scenario: Completed call is observable
- **WHEN** a retrieval call completes successfully
- **THEN** a completion event is emitted carrying the correlation identifier, elapsed milliseconds, attempt count and the returned candidate count

#### Scenario: Failed call records where it was pointing
- **WHEN** a retrieval call fails
- **THEN** a failure event is emitted carrying the classified outcome and the configured base address

#### Scenario: Query text stays out of production logs
- **WHEN** a retrieval call is logged at information level or above
- **THEN** the operator's query text does not appear in the emitted event

### Requirement: Gateway configuration is validated at application start

The gateway configuration SHALL be bound to a strongly-typed options object and validated during application startup, before the first request is served. Validation MUST require an absolute base address, a non-empty signing secret long enough for HS256, and positive time-to-live and time budgets. A failure MUST prevent the application from starting and MUST name the offending configuration key. Lazy validation is insufficient, because it would surface the fault inside a request instead of at startup, which is the failure mode this requirement exists to remove.

The sale assistance time budget MUST NOT be lower than the worst case the AI service declares for the provider calls of one request — two generation calls of four seconds each with its default configuration — and a lower value MUST prevent startup with a message that names that worst case. An outer budget shorter than the inner one discards responses the service was still entitled to produce, and would push the caller onto its degraded path for a service that is answering correctly.

#### Scenario: Missing secret prevents startup
- **WHEN** the application starts without the gateway signing secret configured
- **THEN** startup fails
- **AND** the error names the missing configuration key

#### Scenario: Non-absolute base address prevents startup
- **WHEN** the configured base address is not an absolute URI
- **THEN** startup fails
- **AND** the error names the offending configuration key

#### Scenario: A sale assistance budget below the service worst case prevents startup
- **WHEN** the application starts with a sale assistance time budget lower than the worst case the AI service declares
- **THEN** startup fails
- **AND** the error names the configuration key and the worst case it must cover

### Requirement: Client models cannot drift from the committed contract

An automated test SHALL compare the client's models against the committed `ai-service/openapi.json`, so that a renegotiated contract breaks the .NET build as well as the Python one. The test MUST cover the retrieval request, result and response models, the enrichment request, proposed-profile and response models, and the sale assistance and substitutes request, response and nested models, verifying that every property exists in the committed schema under the same name and with the same nullability. Without this guard, a contract change would leave the .NET build green and surface at runtime as a silently missing value — which is exactly what the per-field provenance of a proposed profile or the claim scope of a citation would become.

#### Scenario: Models match the committed schema
- **WHEN** the contract test runs against an unmodified working tree
- **THEN** every retrieval, enrichment, sale assistance and substitutes model property is present in the committed schema with the same name and nullability

#### Scenario: Contract drift breaks the build
- **WHEN** the committed schema changes a retrieval, enrichment, sale assistance or substitutes property name or nullability and the client models are not updated
- **THEN** the contract test fails

### Requirement: The gateway client exposes the sale agent on a client of its own, with its own budget and its own circuit

The typed client SHALL expose the sale agent operation against the agent route of the AI service, serialising and deserialising the frozen contract without truncating it, and MUST run it on a named HTTP client registered for the agent alone, with its own time budget and its own circuit state, so that a slow conversation cannot open the circuit of a route that is answering correctly.

The budget MUST be **greater than the service's own wall-clock ceiling plus a margin for the network**, and MUST NOT be the generative route's budget, because the agent's median latency is of the order of the total latency the generative route declares as its ceiling — a client carrying the generative budget would cut a large share of agent requests.

The budget MUST NOT be tightened to the maximum latency observed in measurement: the failure mode of doing so is cutting a request the service has **already paid for in full**.

The client MUST NOT retry on a timeout nor on a server error, and MUST retry only a connection that was never established, which is the one failure where the request is known not to have left and nothing was spent.

The client MUST NOT send a point of sale in the request body, since the service ignores it and the scope comes from the token.

#### Scenario: The agent operation is exposed and mapped in full
- **WHEN** the backend calls the sale agent through the client
- **THEN** the conversation is serialised as the frozen contract declares
- **AND** every field the response carries is mapped without truncation

#### Scenario: The agent runs on its own client and budget
- **WHEN** the client is resolved for the agent operation
- **THEN** it is the client registered for the agent
- **AND** its budget exceeds the service's wall-clock ceiling plus a network margin
- **AND** it is not the generative route's budget

#### Scenario: A slow agent does not open the generative circuit
- **WHEN** repeated agent calls exceed their budget
- **THEN** the circuit of the generative route stays closed

#### Scenario: Only a connection that never opened is retried
- **WHEN** an agent call times out or returns a server error
- **THEN** it is not retried
- **AND** a connection that was never established is retried once

### Requirement: A degradation the service reports inside a successful response is not a circuit failure

The circuit protecting the agent hop SHALL count the conditions of transport — the service not answering, answering with a server error, or the connection failing — and MUST NOT count a response the service served successfully while reporting an internal degradation, whether that is no argument because the provider failed or no loop because no credential was configured.

This route does not answer with a server error when its provider falls: it answers successfully, reporting the state in a closed vocabulary. A circuit that counted those responses would open over a route working exactly as designed; one that ignored a transport failure would lose the only signal that the service is down.

The deliberate consequence is that the reported provider failure is instrumented as a metric and a log entry rather than acted upon by the circuit. What tells a screen the agent is unavailable is the availability probe, which costs no quota and no provider call — and at the request rate the token-per-minute quota allows, a sample-threshold circuit over that condition could not reach its threshold before its sampling window expired.

#### Scenario: An in-band provider failure does not count
- **GIVEN** repeated successful responses reporting that the provider failed
- **WHEN** the circuit state is inspected
- **THEN** it is closed
- **AND** each occurrence was recorded as a metric

#### Scenario: A transport failure counts
- **GIVEN** repeated calls in which the service does not answer
- **WHEN** the circuit state is inspected
- **THEN** it has opened

#### Scenario: A cut-short answer is not a failure either
- **GIVEN** responses reporting that a budget cut the answer short
- **WHEN** the circuit state is inspected
- **THEN** it is closed

### Requirement: Gateway tests run in process without the AI service

The test suite for this integration SHALL exercise mapping, token emission, resilience and failure translation with a fake HTTP message handler, and MUST NOT require the `jbg-ai` container, network access or an AI provider. Time-dependent behavior MUST be driven by an injected time abstraction rather than by real waiting.

#### Scenario: Suite passes with the AI service stopped
- **WHEN** the backend test suite runs with `jbg-ai` not running and no network access
- **THEN** the gateway tests pass
- **AND** no real HTTP request leaves the test process
