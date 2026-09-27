## ADDED Requirements

### Requirement: Typed gateway client exposes sale assistance and substitutes

The backend SHALL extend the typed `jbg-ai` client with two operations, added by the change that first calls them: sale assistance against `POST /v1/assist/sale` and substitutes against `POST /v1/retrieval/substitutes`, both serializing and deserializing the frozen contract with `snake_case` property names on the wire.

Both operations MUST require a point-of-sale call scope and MUST reject a catalog-wide scope before any request is issued. Both MUST NOT send `pos_id` in the request body, since the service ignores it and the scope comes from the token. The sale assistance request MUST always carry the product and MAY carry the question; a sale assistance request without a product MUST NOT be issued, because this client serves only the modes whose placeholders refer to one product.

Every value the contract declares as nullable MUST map to a nullable value: the family, its label and the variant label of a member, the clarification question, the prompt version and the product a citation supports. Every citation MUST keep its identifier, document title, section title, document type, claim scope, score and snippet. The substitutes operation MUST report the candidates and `candidates_returned` as received and MUST NOT filter, reorder or truncate them: the window is larger than the page on purpose, and excluding by stock belongs to the hydrating caller.

The completion event of a sale assistance call MUST NOT carry the argument, and the question MUST NOT be emitted above debug level.

#### Scenario: A sale assistance response is mapped in full
- **WHEN** the AI service answers HTTP 200 to a sale assistance request
- **THEN** the client returns the intent, the groups with their members, the argument, the citations, the warnings, the clarification question, the usage, the abstention flag, the prompt version, the trace identifier and the effective point of sale
- **AND** each citation keeps its claim scope

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

## MODIFIED Requirements

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
