# ai-free-query-search Specification

## Purpose
Free-query assisted search of the backend behind `POST /api/ai/search/assisted`: a route of its own rather than a mode flag of semantic search, because the per-point-of-sale switch, the request-rate policy, the time budget and the circuit breaker are configured per feature and not per request; the materials and the piece category the operator selected forwarded as catalog-side filters, so the generative route never knows less about what was asked than the semantic route it can be exchanged for; a switch per point of sale and a per-user request-rate policy of its own, with an exhausted quota reported as its own outcome rather than as an outage; an authenticated availability route that states, before any search has been paid for, whether each AI path is on, without calling the AI service, running a model or consuming any quota; a response carrying the family-grouped candidates hydrated against the point of sale together with the argument and its state, the citations with their claim scope, the detected intent, the abstention flag, the warnings that describe the query and not the ones that describe a single piece, the clarification question, and the usage and the elapsed-time split reserved to administrators; a scope that may cover every point of sale, where no quantity is reported rather than a false zero; the reason a path degraded reported from a closed vocabulary and not only written to the log; and a search origin of its own, so that the semantic and the generative paths are comparable by query over the persisted events.

## Requirements

### Requirement: The free query is exposed through a route of its own, separate from assisted search

The backend SHALL expose the free-query mode of sale assistance through `POST /api/ai/search/assisted`, a route distinct from `POST /api/ai/search`, and MUST NOT serve it as a mode flag of the existing search route, because the two differ in four operational properties that are configured per feature and not per request: the per-point-of-sale switch, the request-rate policy, the time budget and the circuit breaker.

The route MUST require authentication and MUST accept the operator's query, the catalog-side filters the operator selected, the page size and the search episode identifier, with the point of sale either named explicitly or declared as every point of sale.

It MUST use the generative gateway client and its own budget and circuit, and MUST NOT spend the retrieval client's, so a slow language model cannot open the circuit of a route that is answering retrieval correctly.

#### Scenario: The free query has its own route
- **WHEN** the operator asks for an assisted answer to a free-text query
- **THEN** the request is served by `POST /api/ai/search/assisted`
- **AND** `POST /api/ai/search` behaves exactly as it did before this capability existed

#### Scenario: The generative route does not spend the retrieval budget
- **WHEN** a free-query request exceeds the generative time budget
- **THEN** the retrieval circuit remains closed
- **AND** a subsequent semantic search is still served by the assisted path

### Requirement: The free query carries the filters the operator selected

The free-query request SHALL forward the materials and the piece category the operator selected to the AI service as catalog-side filters, so that the assisted route never knows less about what the operator asked for than the semantic route it can be exchanged for.

A request carrying no filter MUST be forwarded with no filter, and the whole catalogue MUST remain reachable.

#### Scenario: A selected category reaches the AI service
- **WHEN** the operator selects a piece category and asks for an assisted answer
- **THEN** every piece in the response belongs to that category

#### Scenario: No selection means no filter
- **WHEN** the operator selects neither a material nor a category
- **THEN** no filter is forwarded
- **AND** candidates from the whole catalogue are eligible

### Requirement: The free query can be switched off per point of sale, on its own switch

The route SHALL be governed by a per-point-of-sale switch of its own, held in configuration and read so that a shop can be switched on or off without a redeploy, and MUST NOT reuse the switch of assisted search nor the switch of the sale card, because the three are different features with different cost profiles.

When the switch is off for the requested point of sale, the route MUST NOT call the AI service and MUST report that the assisted answer is unavailable together with the reason.

#### Scenario: A shop that is switched off costs nothing
- **WHEN** a free-query request names a point of sale for which the route is switched off
- **THEN** no call is made to the AI service
- **AND** the response reports the assisted answer as unavailable
- **AND** the reason states that the feature is switched off

### Requirement: The cost of the free query is bounded by its own request-rate policy

The route SHALL enforce a request-rate policy per user of its own, separate from the one that governs assisted search and from the one that governs the sale card, because the card is opened once per piece while the panel is used in bursts and a shared quota would leave one of the two unable to work.

Exceeding the policy MUST be reported as its own outcome, distinguishable from the AI service being unavailable.

#### Scenario: An exhausted quota is not an outage
- **WHEN** a user exceeds the free-query request-rate policy
- **THEN** the response reports too many requests
- **AND** it does not report the AI service as unavailable

#### Scenario: The quotas are independent
- **WHEN** a user exhausts the free-query quota
- **THEN** a request to the sale card route is still served

### Requirement: Availability of both AI paths is readable before any search is issued

The backend SHALL expose an authenticated read route that reports whether the semantic path, the assisted path and the agent path are each available for the scope asked about — one named point of sale, or every point of sale when none is named — and that route MUST NOT call the AI service, MUST NOT consume any request-rate quota and MUST NOT run any model.

The route exists because availability was previously observable only inside the response of a search that had already been paid for, which makes it impossible for a screen to state, before the operator acts, that a capability is off.

It previously reported for one point of sale only and refused its absence with a validation error. That made the every-point-of-sale scope unreadable: a screen offering it had nothing to read, so the generative path appeared switched off with no reason to show — which is the same shape of failure this route was created to remove, reintroduced one scope along.

It also previously reported two paths, which left the agent's entry card with nothing to read: the agent has a credential chain of its own, so a deployment can have the assisted answer on and the agent off, and a probe reporting only the assisted path would state that the agent is available while every agent request comes back degraded. The agent's verdict MUST therefore be reported as a value of its own and MUST NOT be derived from the assisted path's.

With no point of sale named, the route MUST report the scope's default state, resolving the absence by the very rule the search route resolves it with: a deployment that switches the feature on shop by shop has not switched it on for every shop at once. The route MUST NOT resolve the absence by a rule of its own, because a probe that disagrees with the route it describes puts the screen back to presenting a capability that is off as though it were on.

The route MUST distinguish an absent point of sale from a blank one: an absent point of sale is the wider scope, and a blank identifier MUST be refused, because absence is the field not being there and anything else is a value that has to be usable. The identifier the response carries MUST be absent or null when no point of sale was named, and MUST NOT be reported as a blank identifier.

The route MUST continue to require authentication, and reporting the wider scope's state reveals nothing further, since it describes switches rather than data.

What is knowable without making a call remains the deployment's own switches and its own credentials, never the provider's state, and this route deliberately makes no call.

#### Scenario: Availability is readable before searching
- **WHEN** an authenticated caller asks for the availability of a point of sale
- **THEN** the response states whether the semantic path is available and whether the assisted path is available
- **AND** no call is made to the AI service

#### Scenario: The agent's availability is reported as a value of its own
- **WHEN** an authenticated caller asks for availability
- **THEN** the response states whether the agent path is available
- **AND** that verdict is not derived from the assisted path's

#### Scenario: The assisted path on and the agent off is a reportable state
- **GIVEN** a deployment whose assisted answer is configured and whose agent credential is not
- **WHEN** availability is read
- **THEN** the assisted path is reported available
- **AND** the agent path is reported unavailable

#### Scenario: Availability of the wider scope is readable too
- **WHEN** an authenticated caller asks for availability without naming a point of sale
- **THEN** the request is served rather than refused
- **AND** the response reports the default state of each path, which is the state the search route would apply for that same scope
- **AND** the point-of-sale identifier it carries is absent or null

#### Scenario: A blank point of sale is refused rather than read as an absence
- **WHEN** a caller asks for availability naming a blank point-of-sale identifier
- **THEN** the request is refused as invalid
- **AND** it is not served as though no point of sale had been named

#### Scenario: Reading availability consumes no quota
- **WHEN** the availability route is called repeatedly
- **THEN** no request-rate policy is consumed
- **AND** a subsequent search is served normally

### Requirement: The free-query response carries everything the AI service produced for the query

The free-query response SHALL carry the family-grouped candidates hydrated against the point of sale, the generated argument with its state, the citations with their claim scope, the detected intent, the abstention flag, the warning codes that describe the query, the clarification question when one was emitted, and the reason for degradation when the path degraded.

It MUST NOT carry the warning codes that describe a single piece, because the AI service computes those for the first member of the first group only and presenting them as a statement about the whole result set would assert something untrue.

It MUST carry the usage the AI service reported and the split of the elapsed time between the AI call and the whole request, and both MUST be restricted to callers whose role is administrator.

#### Scenario: The response carries the argument and its citations
- **WHEN** the AI service answers a free query with an argument
- **THEN** the response carries the argument, its state and the citations the argument used
- **AND** every citation keeps its claim scope

#### Scenario: Piece warnings do not travel as query warnings
- **WHEN** the AI service returns warnings that describe one piece
- **THEN** those codes are not present in the response's query warnings

#### Scenario: Usage is restricted to administrators
- **WHEN** an operator whose role is not administrator issues a free query
- **THEN** the response carries no usage figures and no elapsed-time split

### Requirement: A free query may be scoped to every point of sale, and what cannot be known is not invented

The route SHALL accept a request scoped to every point of sale, and both operators and administrators MUST be permitted to issue it, which makes the search consistent with the stock breakdown of a product, already readable across every point of sale by any authenticated caller.

With no point of sale named, the route MUST NOT report a quantity for any result and MUST state that a point of sale is needed to read stock, because reporting zero would assert something false; it MUST NOT apply the availability prefilter; and it MUST record the search with no point of sale rather than with a placeholder one.

The route MUST continue to refuse a point of sale the caller is not authorised to use when one is named.

#### Scenario: An operator may search across every point of sale
- **WHEN** an operator issues a free query scoped to every point of sale
- **THEN** the request is served
- **AND** results from the whole catalogue are eligible

#### Scenario: Without a point of sale, stock is not reported as zero
- **WHEN** a free query is scoped to every point of sale
- **THEN** no result carries a quantity
- **AND** the response states that a point of sale is required to read stock

#### Scenario: A named point of sale is still authorised
- **WHEN** an operator names a point of sale they are not assigned to
- **THEN** the request is refused
- **AND** no call is made to the AI service

### Requirement: The reason a path degraded is reported, not only logged

The backend SHALL report, on every response of the free-query route and of the sale card, the reason the AI path degraded, drawn from a closed vocabulary that distinguishes at least the switch being off, the credential being rejected, the route not being implemented, the product not being indexed, the AI service being unavailable, and an unclassified failure.

The reason MUST be the same value the backend already computes for its own log line, so that the screen and the log cannot disagree, and it MUST be absent when the path did not degrade.

#### Scenario: A product that is not indexed is not an outage
- **WHEN** the AI service reports that it cannot process the product
- **THEN** the response reports the reason as the product not being indexed
- **AND** it does not report the reason as the AI service being unavailable

#### Scenario: A healthy response carries no reason
- **WHEN** the AI service answers normally
- **THEN** the response carries no reason for degradation

### Requirement: The route is recorded with an origin of its own, so the two paths are comparable in the database

Every search served by the free-query route SHALL be recorded with a search origin distinct from the assisted, the degraded and the disabled ones, so that the comparison between the semantic and the generative path is answerable by query over the persisted events rather than only demonstrable on screen.

The query text MUST be persisted exactly as the semantic path already persists it, inheriting and declaring the retention limitation that applies to it, and the customer's question of the sale card MUST remain unpersisted.

Recording MUST NOT be able to break the search: a failure to persist MUST leave the response intact.

#### Scenario: The generative path has its own origin
- **WHEN** a free query is served by the assisted path
- **THEN** the persisted event carries the generative origin
- **AND** grouping by origin separates it from the assisted, degraded and disabled populations

#### Scenario: A telemetry failure never breaks the search
- **WHEN** persisting the event fails
- **THEN** the response is still served
- **AND** it reports no recorded event identifier
