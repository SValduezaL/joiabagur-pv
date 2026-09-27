## ADDED Requirements

### Requirement: Catalog retrieval and sale assistance accept a token with no point-of-sale claim, and that claim is never a wildcard

The service SHALL accept, on catalog retrieval and on sale assistance only, a token that carries the base claims and no point-of-sale claim, so that a search deliberately scoped to every point of sale can be served without inventing a value for a claim that is the retriever's only hard filter.

A wildcard or placeholder point-of-sale claim MUST continue to be impossible: what this requirement admits is the **absence** of the claim, which makes the availability prefilter not apply rather than match everything.

Every other `/v1` route that operates inside one point of sale MUST continue to require the claim and MUST reject a token without it, so the omission fails closed everywhere it matters.

The service principal built from such a token MUST expose no point-of-sale identifier, and the response MUST echo the absence rather than a substituted value.

#### Scenario: Retrieval is served without a point-of-sale claim
- **WHEN** an authenticated caller presents a token carrying the base claims and no point-of-sale claim to catalog retrieval
- **THEN** the request is served
- **AND** the availability prefilter is not applied

#### Scenario: Sale assistance is served without a point-of-sale claim
- **WHEN** the same token is presented to sale assistance
- **THEN** the request is served

#### Scenario: A route that needs one shop still rejects the token
- **WHEN** the same token is presented to a route that operates inside one point of sale
- **THEN** the request is rejected
- **AND** the rejection does not reveal which claim was missing

#### Scenario: The principal exposes no point of sale
- **WHEN** a token with no point-of-sale claim is validated
- **THEN** the resulting service principal exposes no point-of-sale identifier
- **AND** no placeholder value is substituted for it

#### Scenario: A wildcard claim is still not a thing
- **WHEN** a token carries a point-of-sale claim whose value is a wildcard or a placeholder
- **THEN** it is treated as a concrete value and matches no point of sale
- **AND** no route interprets it as covering every point of sale
