## MODIFIED Requirements

### Requirement: Availability of both AI paths is readable before any search is issued

The backend SHALL expose an authenticated read route that reports whether the semantic path and the assisted path are each available for the scope asked about — one named point of sale, or every point of sale when none is named — and that route MUST NOT call the AI service, MUST NOT consume any request-rate quota and MUST NOT run any model.

The route exists because availability was previously observable only inside the response of a search that had already been paid for, which makes it impossible for a screen to state, before the operator acts, that a capability is off.

It previously reported for one point of sale only and refused its absence with a validation error. That made the every-point-of-sale scope unreadable: a screen offering it had nothing to read, so the generative path appeared switched off with no reason to show — which is the same shape of failure this route was created to remove, reintroduced one scope along.

With no point of sale named, the route MUST report the scope's default state, resolving the absence by the very rule the search route resolves it with: a deployment that switches the feature on shop by shop has not switched it on for every shop at once. The route MUST NOT resolve the absence by a rule of its own, because a probe that disagrees with the route it describes puts the screen back to presenting a capability that is off as though it were on.

The route MUST distinguish an absent point of sale from a blank one: an absent point of sale is the wider scope, and a blank identifier MUST be refused, because absence is the field not being there and anything else is a value that has to be usable. The identifier the response carries MUST be absent or null when no point of sale was named, and MUST NOT be reported as a blank identifier.

The route MUST continue to require authentication, and reporting the wider scope's state reveals nothing further, since it describes switches rather than data.

#### Scenario: Availability is readable before searching
- **WHEN** an authenticated caller asks for the availability of a point of sale
- **THEN** the response states whether the semantic path is available and whether the assisted path is available
- **AND** no call is made to the AI service

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
