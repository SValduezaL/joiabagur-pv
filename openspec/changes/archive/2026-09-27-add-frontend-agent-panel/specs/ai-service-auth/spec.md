## MODIFIED Requirements

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
