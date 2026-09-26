# ai-service-auth Specification

## Purpose
Internal service authentication for `jbg-ai`: HS256 bearer tokens guarding every `/v1` endpoint, opaque rejection of invalid tokens, a service principal built from frozen `snake_case` claims, and token scope taking precedence over the request body.
## Requirements

### Requirement: Internal service token protects every `/v1` endpoint
Every `/v1` endpoint SHALL require an internal service token presented as `Authorization: Bearer <token>`. The token MUST be a JWT signed with HS256 using the secret configured in `JWT_SECRET`. A request without that header MUST be rejected with HTTP 401 and MUST NOT reach the route handler. `GET /health` MUST remain exempt from this requirement.

#### Scenario: Missing token is rejected
- **WHEN** a client calls any `/v1` endpoint without an `Authorization: Bearer` header
- **THEN** the response status is 401
- **AND** the route handler is not executed

#### Scenario: Valid token is accepted
- **WHEN** a client calls a `/v1` endpoint with a JWT signed with the configured secret and carrying all required claims
- **THEN** the request reaches the route handler
- **AND** the response is not 401

#### Scenario: Health stays exempt from authentication
- **WHEN** a client calls `GET /health` without any token
- **THEN** the request is accepted and answered with HTTP 200

### Requirement: Invalid tokens are rejected without revealing the cause
A token that is malformed, signed with the wrong secret, signed with an unexpected algorithm, expired, or missing any required claim MUST be rejected with HTTP 401. The response body MUST NOT disclose the signing secret, and MUST NOT disclose which specific validation step failed.

#### Scenario: Wrong signature is rejected
- **WHEN** a client presents a JWT signed with a secret other than the configured one
- **THEN** the response status is 401
- **AND** the body does not reveal the secret or the exact failure cause

#### Scenario: Expired token is rejected
- **WHEN** a client presents a JWT whose expiry is in the past
- **THEN** the response status is 401

#### Scenario: Missing required claim is rejected
- **WHEN** a client presents a correctly signed JWT that omits one of the required claims
- **THEN** the response status is 401

### Requirement: Validated tokens produce a service principal for handlers
The service MUST validate the token in a FastAPI dependency and expose the result to handlers as a service principal built from the claims `user_id`, `role`, `pos_id` and `trace_id`. These claim names are frozen in `snake_case` on the wire; the calling .NET service is responsible for emitting them with exactly those keys.

`user_id`, `role` and `trace_id` MUST be required on every `/v1` route. `pos_id` MUST be required on routes that have point-of-sale scope — retrieval, sale assistance and inventory — and MUST NOT be required on catalog-wide routes such as enrichment and index synchronization, which operate over the whole catalog and belong to no point of sale. The service MUST expose these as two distinct dependencies, so that a route's scope is declared where the route is declared and cannot be relaxed by accident for a route that needs it. A token carrying no `pos_id` MUST be rejected with HTTP 401 on any point-of-sale scoped route.

#### Scenario: Principal carries the token claims
- **WHEN** an authenticated request reaches a point-of-sale scoped `/v1` handler
- **THEN** the handler receives a service principal exposing `user_id`, `role`, `pos_id` and `trace_id` taken from the token

#### Scenario: Claim names are frozen in snake_case
- **WHEN** a token presents point-of-sale scope under a key other than `pos_id`
- **THEN** the required claim is considered absent and the response status is 401

#### Scenario: A catalog route accepts a token without point-of-sale scope
- **WHEN** an authenticated client calls a catalog-wide `/v1` route with a token carrying `user_id`, `role` and `trace_id` but no `pos_id`
- **THEN** the request reaches the route handler
- **AND** the response is not 401

#### Scenario: A retrieval route rejects a token without point-of-sale scope
- **WHEN** the same token is presented to `POST /v1/retrieval/products`
- **THEN** the response status is 401
- **AND** the route handler is not executed

#### Scenario: A catalog route still rejects a token missing the other claims
- **WHEN** a catalog-wide `/v1` route is called with a token that omits `user_id`, `role` or `trace_id`
- **THEN** the response status is 401

### Requirement: Token scope takes precedence over the request body
The effective `pos_id` and `role` applied by any `/v1` handler MUST come from the token, never from the request body. Request models MAY accept an optional `pos_id` for client compatibility, but that value MUST be ignored. A mismatch between the body value and the token value MUST NOT cause an error and MUST NOT change behavior.

#### Scenario: Token pos_id overrides a different body value
- **WHEN** a client calls `POST /v1/retrieval/products` with a token carrying `pos_id = B` and a body carrying `pos_id = A`, with A different from B
- **THEN** the effective scope applied by the handler is B
- **AND** the request does not fail because of the value sent in the body

#### Scenario: Role cannot be escalated from the body
- **WHEN** a request body carries a role value that differs from the token claim
- **THEN** the effective role remains the one from the token

### Requirement: Authentication tests run in process without external AI or database
The authentication test suite MUST cover missing token, invalid token variants, principal extraction and token-over-body precedence with an in-process client, and MUST NOT call real LLM providers, embedding APIs, or production RDS.

#### Scenario: Auth suite passes without external calls
- **WHEN** the `ai-service` test suite runs with the required environment provided in process
- **THEN** `test_request_without_token_is_rejected`, `test_invalid_token_is_rejected` and `test_pos_id_from_token_overrides_body_value` pass
- **AND** no call is made to an LLM provider, embedding API or production database

### Requirement: Catalog retrieval and sale assistance accept a token with no point-of-sale claim, and that claim is never a wildcard

The service SHALL accept, on catalog retrieval, on sale assistance and on the sale agent only, a token that carries the base claims and no point-of-sale claim, so that a search deliberately scoped to every point of sale can be served without inventing a value for a claim that is the retriever's only hard filter.

A wildcard or placeholder point-of-sale claim MUST continue to be impossible: what this requirement admits is the **absence** of the claim, which makes the availability prefilter not apply rather than match everything.

Every other `/v1` route that operates inside one point of sale MUST continue to require the claim and MUST reject a token without it, so the omission fails closed everywhere it matters. Substitutes and inventory remain such routes and their rejection MUST be unchanged.

The agent route joins the list for the same reason the assistance route did and for one of its own: it is the only route of the assistance family that was not widened when the others were, because at the time it had no consumer, and a screen offering the wider scope on the agent's panel would otherwise be refused by the route its sibling panel is served by.

The service principal built from such a token MUST expose no point-of-sale identifier, and the response MUST echo the absence rather than a substituted value.

Accepting the absence on the agent route MUST NOT change what the absence means to the loop: with no point of sale the availability tool can only report that no scope applies, so the loop cannot pivot to substitutes — a consequence of the data and not a behaviour to be simulated.

#### Scenario: Retrieval is served without a point-of-sale claim
- **WHEN** an authenticated caller presents a token carrying the base claims and no point-of-sale claim to catalog retrieval
- **THEN** the request is served
- **AND** the availability prefilter is not applied

#### Scenario: Sale assistance is served without a point-of-sale claim
- **WHEN** the same token is presented to sale assistance
- **THEN** the request is served

#### Scenario: The sale agent is served without a point-of-sale claim
- **WHEN** the same token is presented to the sale agent
- **THEN** the request is served
- **AND** the availability prefilter is not applied

#### Scenario: A route that needs one shop still rejects the token
- **WHEN** the same token is presented to a route that operates inside one point of sale
- **THEN** the request is rejected
- **AND** the rejection does not reveal which claim was missing

#### Scenario: Substitutes and inventory still reject the omission
- **WHEN** the same token is presented to the substitutes route or to an inventory route
- **THEN** the request is rejected

#### Scenario: The principal exposes no point of sale
- **WHEN** a token with no point-of-sale claim is validated
- **THEN** the resulting service principal exposes no point-of-sale identifier
- **AND** no placeholder value is substituted for it

#### Scenario: A wildcard claim is still not a thing
- **WHEN** a token carries a point-of-sale claim whose value is a wildcard or a placeholder
- **THEN** it is treated as a concrete value and matches no point of sale
- **AND** no route interprets it as covering every point of sale

#### Scenario: With no scope the loop reports no scope rather than no stock
- **GIVEN** an agent request served from a token with no point-of-sale claim
- **WHEN** the loop consults availability for a piece
- **THEN** the label reports that no scope applies
- **AND** it does not report that the shop is out of stock
