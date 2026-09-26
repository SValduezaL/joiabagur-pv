## ADDED Requirements

### Requirement: The agent's evidence task is served with a prompt version of its own that forbids the placeholders

The generation layer SHALL serve the agent's evidence task from a prompt version of its own in which the invariant ordering price and availability to be written as placeholders is replaced, for that task, by the rule the free-query tasks already carry: with no anchored piece, price and availability are not spoken of at all, while comparative language that names no figure remains allowed.

The version that serves the deterministic route MUST be left unchanged on disk and MUST keep serving that route, because it has published figures measured against it and a later change is going to measure it again. Editing it would make the statement of what each version added, and what it measured, false.

The new version's system section MUST be identical to that of the version it derives from, and that identity MUST be verified by a test rather than by review, since the two files are otherwise free to drift apart silently.

The previous version of the agent's task MUST also be preserved on disk, because the agent's published figures were measured against it.

The reported argument prompt version MUST continue to be pinned to the file actually loaded.

#### Scenario: The agent's argument carries no placeholder
- **GIVEN** the agent's evidence task served from its own prompt version
- **WHEN** an argument is generated over an unanchored payload of several pieces
- **THEN** it contains neither the price placeholder nor the stock placeholder

#### Scenario: Comparative language without figures is still allowed
- **WHEN** the same argument compares the pieces it presents
- **THEN** a comparison that names no figure is not treated as a violation

#### Scenario: The deterministic route's version is untouched
- **WHEN** the prompt directory and the reported versions are inspected after this change ships
- **THEN** the version serving the deterministic route is present and unmodified
- **AND** that route still reports it

#### Scenario: The system section of the two versions is identical
- **WHEN** the new version and the one it derives from are compared
- **THEN** their system sections are identical
- **AND** a test asserts that identity

#### Scenario: The agent's previous version is preserved
- **WHEN** the prompt directory is inspected
- **THEN** the version the agent's published figures were measured against is present and unmodified

#### Scenario: The reported version is the file that ran
- **WHEN** the agent produces an argument
- **THEN** the reported argument prompt version names the file that was loaded
