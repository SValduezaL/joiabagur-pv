## ADDED Requirements

### Requirement: The sale agent is exposed through a .NET route of its own, on its own client and its own budget

The backend SHALL expose the sale agent through a route of its own under the AI search tree, distinct from the assisted-search route and from the free-query route, and MUST NOT serve it as a mode flag of either, because the three differ in the operational properties that are configured per feature rather than per request: the time budget, the circuit state and the conversation shape the caller sends.

The route MUST require authentication and MUST accept the conversation so far, the page size wanted after hydration and the search episode identifier, with the point of sale either named explicitly or declared as every point of sale.

It MUST use a gateway client registered under a name of its own, with a time budget **greater than the service's own wall-clock ceiling plus network margin** and never the generative route's budget, and MUST NOT retry on a timeout or on a server error, because the service may already have spent its provider calls and a second attempt doubles both the wait at the counter and the paid calls.

#### Scenario: The agent has its own route
- **WHEN** the operator asks the agent for help with a conversation
- **THEN** the request is served by the agent route
- **AND** the assisted-search and free-query routes are unchanged in shape and behaviour

#### Scenario: The agent does not spend the generative route's budget
- **WHEN** the agent route calls the AI service
- **THEN** it uses the client registered for the agent
- **AND** its time budget exceeds the service's own wall-clock ceiling plus a margin for the network
- **AND** a slow agent response does not open the circuit of the generative route

#### Scenario: A timeout is not retried
- **WHEN** the agent call exceeds its time budget
- **THEN** the call is not retried
- **AND** the failure is reported to the caller as a failure of that request

### Requirement: The transcript caps are validated before any provider call is spent

The backend SHALL validate the three caps the contract declares — the number of turns, the length of each turn and the total length of the transcript — and MUST refuse a request that exceeds any of them **before** calling the AI service, so that a caller cannot spend a provider call to be told the request was malformed.

The total MUST be validated as the sum over **every** turn, including the turns attributed to the assistant, because the contract's total is not implied by the other two caps.

The request MUST also be refused when it carries no turn attributed to the operator, since the turn being answered is the last of those.

Refusal messages MUST be in Spanish, as every operator-facing validation message in this system is.

#### Scenario: A transcript over the total cap is refused before the call
- **WHEN** a request arrives whose turns sum to more than the declared total
- **THEN** the request is refused as invalid
- **AND** no call is made to the AI service

#### Scenario: The assistant's turns count towards the total
- **WHEN** a request arrives whose operator turns alone fit the total but whose assistant turns push the sum over it
- **THEN** the request is refused as invalid

#### Scenario: A transcript with no operator turn is refused
- **WHEN** a request arrives whose turns are all attributed to the assistant
- **THEN** the request is refused as invalid

### Requirement: The response carries the five fields the agent adds and the provenance of every group

The backend SHALL carry to the caller, in addition to everything the deterministic free-query response already carries, whether the answer was cut short by a budget, the stop reason from the service's closed vocabulary, the number of iterations, the number of tool calls used, the per-iteration trace and the version of the argument prompt the agent ran.

Every group MUST carry the provenance the service declares — a catalogue match or a substitute — and the backend MUST NOT flatten the two nor derive one from the other, because a substitute and a match are different things to say to a customer.

The stop reason MUST be carried as the service reported it and MUST NOT be inferred from the iteration or tool-call counters, because a count does not say whether the last step was the last one needed or the one that ran out.

#### Scenario: The agent's own fields reach the caller
- **WHEN** the agent route answers
- **THEN** the response carries the cut-short flag, the stop reason, the iteration count, the tool-call count, the trace and the argument prompt version

#### Scenario: Group provenance survives the hop
- **GIVEN** a service response carrying both catalogue matches and substitutes
- **WHEN** the backend maps it
- **THEN** each group carries its own provenance
- **AND** no group's provenance is inferred from its position or its contents

#### Scenario: The stop reason is carried and not computed
- **WHEN** the service reports a stop reason
- **THEN** the backend carries that value
- **AND** it does not derive a stop reason from the counters

### Requirement: Price and stock are hydrated authoritatively over every member of every group

The backend SHALL hydrate every member of every group the agent returned with the product's name, its price, the quantity held at the point of sale asked about, whether it has stock, its primary photo and its collection, and MUST remain the sole authority on price and stock, because the AI service holds only a qualitative availability band that never leaves it.

When the request was scoped to every point of sale, the quantity and the stock flag MUST be reported as unknown rather than as zero, and the caller MUST be able to tell the two apart.

The hydration MUST cover the members of substitute groups on the same terms as those of catalogue groups.

#### Scenario: Every member of every group is hydrated
- **WHEN** the agent returns several groups of candidates
- **THEN** every member of every group carries its name, price, stock and photo as the backend resolved them

#### Scenario: The wider scope reports stock as unknown
- **GIVEN** a request scoped to every point of sale
- **WHEN** the response is inspected
- **THEN** the quantity and the stock flag are unknown rather than zero

#### Scenario: The AI service's availability band is not published
- **WHEN** the response is inspected
- **THEN** it carries no qualitative availability band from the AI service
- **AND** the stock it carries is the backend's

### Requirement: A provider failure inside the loop degrades and never becomes a server error

The backend SHALL treat a response the AI service served successfully while reporting an internal degradation — no argument because the provider failed, or no loop because no credential was configured — as a **successful** response carrying that state, and MUST NOT convert it into a server error and MUST NOT count it as a failure of the circuit that protects the hop.

What the circuit protects against is the AI service not answering. A circuit that counted a degradation the service answered with would open over a route that is working exactly as designed; one that ignored a transport failure would lose the only signal that the service is down.

The degradation MUST be recorded as a metric and a log entry so that its rate stays observable without the circuit acting on it.

#### Scenario: An in-band provider failure is served, not failed
- **GIVEN** the AI service answers successfully reporting that its provider failed
- **WHEN** the backend maps the response
- **THEN** the caller receives a successful response carrying that state
- **AND** no server error is produced

#### Scenario: An in-band degradation does not open the circuit
- **WHEN** repeated responses report an internal degradation
- **THEN** the circuit protecting the hop stays closed
- **AND** each degradation is recorded as a metric

#### Scenario: A transport failure still counts
- **WHEN** the AI service does not answer at all
- **THEN** the circuit counts it

### Requirement: A sale originating in the agent is recorded with a search origin of its own

The backend SHALL record a selection made from the agent's answer under a search origin distinct from every existing one, so that a sale originating in the agent is distinguishable in the database from one originating in the deterministic panel and the comparison of the two paths is a query rather than a demonstration.

The new value MUST NOT require a schema migration, since the origin is persisted by conversion to an integer.

A query scoped to every point of sale MUST continue not to be recorded, which is a declared and inherited limitation rather than a new one.

#### Scenario: A selection from the agent carries its own origin
- **WHEN** the operator picks a piece from the agent's answer
- **THEN** the event is recorded with the agent's search origin

#### Scenario: The new origin opens no migration
- **WHEN** the change is inspected
- **THEN** no schema migration was created for the new origin value

### Requirement: The agent route is authorised exactly as its sibling route and names no unassigned shop

The backend SHALL authorise the agent route by the same rule the free-query route uses — available to operators and to administrators, with the wider scope open to both — and MUST refuse a request that names a point of sale the caller is not assigned to, which is the boundary that is actually protected.

Two sibling panels with two different authorisation rules break without any test failing, so the rule MUST be the same one rather than a stricter copy of it.

#### Scenario: An operator is served on the agent route
- **WHEN** an operator asks the agent about a point of sale assigned to them
- **THEN** the request is served

#### Scenario: Naming an unassigned shop is refused
- **WHEN** a caller names a point of sale they are not assigned to
- **THEN** the request is refused

#### Scenario: The wider scope is served to both roles
- **WHEN** a request is scoped to every point of sale
- **THEN** it is served for an operator and for an administrator alike
