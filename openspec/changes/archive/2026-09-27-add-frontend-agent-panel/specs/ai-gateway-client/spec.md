## ADDED Requirements

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
