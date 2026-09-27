## MODIFIED Requirements

### Requirement: Backend Test CI Workflow

The system SHALL provide a GitHub Actions workflow that automatically executes all backend tests (unit and integration) on code changes to branches that exist in the repository and on pull requests targeting them. The trigger MUST name the integration branch and the default branch of this repository, and MUST NOT name a branch the repository does not have.

A trigger naming a non-existent branch produces a workflow that is well formed, visible and **inert**: it never runs, reports nothing, and gives the appearance of automated checking where there is none. That state held for the whole of this project's AI work, which was built on the integration branch while the trigger named two branches that were never created, so no change was ever checked automatically before being integrated.

The workflow's result SHALL be reported and MUST NOT act as a merge gate while the suite carries known pre-existing failures. A gate over a red suite is not a gate: it blocks every change indefinitely for reasons unrelated to the change, and the pre-existing failure set is additionally known to rotate between runs of the same commit. Making the workflow a required check is a separate decision that belongs with the work of bringing the suite green, and it carries a trap of its own: a workflow skipped by a path filter never reports a status, and a required check that never reports leaves a pull request blocked permanently.

The path filter that limits the workflow to changes under the backend tree SHALL be kept. Test workflows and deployment workflows fail towards opposite sides on purpose: a test that runs unnecessarily costs minutes, while a deployment that fails to run leaves an environment serving old code in silence.

#### Scenario: Test Execution on Pull Request
- **WHEN** a pull request is opened or updated targeting the integration branch or the default branch
- **THEN** the backend test workflow is triggered automatically
- **AND** all unit tests are executed
- **AND** all integration tests are executed with PostgreSQL container
- **AND** test results are reported in the pull request

#### Scenario: Test Execution on Push
- **WHEN** code is pushed to the integration branch or the default branch
- **THEN** the backend test workflow is triggered automatically
- **AND** all tests are executed
- **AND** workflow status is visible in repository

#### Scenario: Every branch the trigger names exists
- **WHEN** the workflow trigger is inspected
- **THEN** every branch it names exists in the repository
- **AND** the workflow has at least one recorded execution

#### Scenario: A failing suite reports without blocking integration
- **GIVEN** the backend suite carries known pre-existing failures
- **WHEN** the workflow runs and reports failures
- **THEN** the result is visible on the commit and on the pull request
- **AND** the failures do not prevent the change from being integrated
- **AND** the workflow is not configured as a required check

#### Scenario: The backend path filter is preserved
- **WHEN** the workflow trigger is inspected
- **THEN** it is limited to changes under the backend tree and to the workflow file itself
