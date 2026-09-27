## ADDED Requirements

### Requirement: The reason the card degraded is reported to the caller, not only written to the log

The sale card response SHALL carry the reason the AI path degraded, drawn from the same closed vocabulary the backend already computes for its own log line, so that a piece the AI service cannot process is distinguishable from an outage, a switched-off feature and a rejected credential.

The vocabulary MUST distinguish at least the feature being switched off, the credential being rejected, the route not being implemented, the product not being indexed, the AI service being unavailable, and a failure that could not be classified.

The value MUST be the one the log line carries for the same request, so the screen and the log cannot disagree, and it MUST be absent when the path did not degrade.

This closes a declared limitation of the card: until now the body reported only that the AI was unavailable, so a product added after the last index synchronisation — a state the next synchronisation fixes — read as a fault, and only the backend log separated the two.

#### Scenario: A product that is not indexed is reported as such
- **WHEN** the AI service answers that it cannot process the anchored product
- **THEN** the response reports the reason as the product not being indexed
- **AND** it does not report the reason as the AI service being unavailable

#### Scenario: A switched-off card says so
- **WHEN** the card is switched off for the point of sale
- **THEN** the response reports the reason as the feature being switched off
- **AND** no call is made to the AI service

#### Scenario: A rejected credential is not an outage
- **WHEN** the AI service rejects the gateway credentials
- **THEN** the response reports the reason as the credential being rejected

#### Scenario: A healthy card carries no reason
- **WHEN** the AI service answers normally and the argument is delivered
- **THEN** the response carries no reason for degradation

#### Scenario: The reason matches the log line
- **WHEN** a request degrades
- **THEN** the reason in the response equals the reason recorded in the log line for the same trace identifier
