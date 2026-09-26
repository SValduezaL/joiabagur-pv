## MODIFIED Requirements

### Requirement: Substitutes reach the generation layer as a group distinguished from catalogue matches
The service SHALL mark the groups it gathered from the substitutes tool as substitutes, using a value from a closed vocabulary, so that the generation layer can tell them from candidates the catalogue search returned, and SHALL publish that same marker on every group of the response so that a consumer can label them too.

A substitute and a match are different things to say to a customer, and a payload that flattened them would let the argument present a second-best alternative as though it were what was asked for. The distinction changes the shape of the payload, so the prompt that reads it moves to a new version rather than being edited in place — the figures measured against the previous version have to stay interpretable.

Publishing the marker on the response is the same argument one layer out. Until now the distinction existed only in the payload the model reads, so the argument said «and as an alternative…» because the prompt told it to while **the screen had no way to label the rows** — which is exactly what the marker exists to prevent. The marker MUST be carried on a response model of the agent's own rather than added to the group model the deterministic route publishes, because widening the shared model would move the schema of that route.

#### Scenario: A pivot to substitutes is visible in the payload
- **GIVEN** a request during which the loop invoked the substitutes tool
- **WHEN** the payload handed to the generation layer is inspected
- **THEN** the substitute groups carry the closed-vocabulary marker that distinguishes them
- **AND** the catalogue matches do not

#### Scenario: The piece the loop pivoted away from is not offered as a match
- **GIVEN** a request whose catalogue search returned a piece for which the loop then requested substitutes
- **WHEN** the payload handed to the generation layer is inspected
- **THEN** that piece is not among the catalogue matches
- **AND** when the cap on distinct pieces binds, further catalogue matches are dropped before the substitutes, while the payload keeps the order in which the evidence arrived

#### Scenario: The previous argument prompt version is preserved intact
- **WHEN** the prompt directory is inspected after this capability ships
- **THEN** the previous argument prompt version is present and unmodified

#### Scenario: Every group of the response declares its provenance
- **GIVEN** a request whose evidence holds both catalogue matches and substitutes
- **WHEN** the response is inspected
- **THEN** every group carries the closed-vocabulary marker of its provenance
- **AND** the marker distinguishes a catalogue match from a substitute

#### Scenario: The deterministic route's group model is not widened
- **WHEN** the published contract is compared before and after
- **THEN** the group model of the deterministic route is unchanged
- **AND** the marker appears only on the agent's own group model

## ADDED Requirements

### Requirement: The agent's measurement instruments record the placeholder rate and the freshness the run actually had

The agent's measurement harness SHALL record, per generation, how many price placeholders and stock placeholders the first attempt contained, and SHALL publish those counts aggregated over the run, so that the rate at which the argument writes a placeholder over an unanchored payload is readable rather than inferred from the withholding rate.

It SHALL also record the age of the point-of-sale projection, both once in the run's provenance and **again on every row**, together with the verdict of whether that age exceeded the staleness ceiling, so that a row served without the availability prefilter is identifiable afterwards instead of being averaged in with the rest.

Recording the age per row rather than once is what the run needs, because a run lasts longer than the ceiling: the harness resolves its reference pieces through a port that reads the projection directly and applies no freshness check, while the serving path consults the synchronisation checkpoint and declines to apply the scope when it is stale. The two therefore disagree in silence, and a run with no recorded age cannot be told apart from a run that was fresh throughout.

The recorded age MUST come from the synchronisation checkpoint and never from the projection's own refresh column, which records when an assignment last changed rather than when the projection was last read.

#### Scenario: Placeholder counts are recorded and aggregated
- **WHEN** a run of the agent harness completes
- **THEN** each row carries the price-placeholder and stock-placeholder counts of its first attempt
- **AND** the run publishes those counts aggregated

#### Scenario: Freshness is recorded per row and not only per run
- **WHEN** a run of the agent harness completes
- **THEN** the provenance carries the projection's age at the start
- **AND** every row carries the age and the staleness verdict that applied to it

#### Scenario: A degraded row is identifiable rather than averaged in
- **GIVEN** a run during which the projection became stale partway through
- **WHEN** the artefact is read afterwards
- **THEN** the rows served without the availability prefilter can be told from the rest

#### Scenario: The age comes from the checkpoint
- **WHEN** the recorded age is traced to its source
- **THEN** it comes from the synchronisation checkpoint
- **AND** not from the projection's refresh column
