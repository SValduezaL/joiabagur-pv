## ADDED Requirements

### Requirement: Task success over the agent's calibration scenarios is a defined verdict, recomputed without a provider and published with its failures named

Task success over the agent's calibration scenarios SHALL be a verdict defined before it is published — a scenario succeeds when the tool expectation written for it is met, meaning every tool it requires was invoked, at least one of any it admits was invoked and none it forbids was, and the scenario does not itself declare a discrepancy — and that verdict MUST be recomputable from a committed run artefact with no provider call and no database, so that any reader reproduces it from the repository alone.

The published form MUST be a count over the scenario set with the failing scenarios named individually, and MUST NOT be a success rate expressed as a percentage. The reason is measured and not stylistic: scoring two runs of the same scenario set against each other puts the between-run noise at 2 of 20, so a single rate would claim a precision the evidence does not have, while the count with its names carries strictly more information.

Fields the run records but for which no per-scenario expectation was written — the terminal stop reason, the iteration and tool-call counters, the number of groups, whether an argument was generated — MUST be published beside the verdict as context and MUST NOT enter it, because admitting them after the figures are in hand would be defining the criterion from the data.

A scenario whose transcript changed after the run MUST be reported as not comparable rather than scored against the definition as it stands today, and the count of such scenarios MUST be published with the verdict.

#### Scenario: The verdict is recomputed from a committed artefact

- **WHEN** the task-success verdict is published
- **THEN** it is recomputed from a run artefact committed to the repository
- **AND** the recomputation calls no model provider and reads no database
- **AND** the artefact is identified by name and by a digest of its bytes

#### Scenario: The verdict is published as a count with its failures named

- **WHEN** the verdict over the calibration set is published
- **THEN** it is stated as a count over the set with every failing scenario named
- **AND** no success rate expressed as a percentage is published in its place
- **AND** the measured between-run noise is stated beside the count

#### Scenario: A scenario declaring its own discrepancy is counted apart

- **GIVEN** a calibration scenario that declares a discrepancy of its own
- **WHEN** the verdict is computed
- **THEN** that scenario is counted apart from both the successes and the unexplained failures

#### Scenario: A scenario that changed after the run is not scored

- **GIVEN** a calibration scenario whose transcript differs from the one the run executed
- **WHEN** the verdict is recomputed against the scenario set as it stands today
- **THEN** that scenario is reported as not comparable
- **AND** the number of scenarios in that state is published with the verdict

#### Scenario: Terminal state is context and not part of the verdict

- **GIVEN** a scenario whose tool expectation is met and whose loop stopped on a budget
- **WHEN** the verdict is computed
- **THEN** the scenario counts as a success
- **AND** its stop reason and counters are published beside the verdict rather than inside it
