# backend-testing Specification

## Purpose
Defines the testing infrastructure, patterns, and requirements for backend unit and integration tests. Covers CI workflows, test data generation, database isolation, and testing conventions.
## Requirements
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

### Requirement: Backend Code Coverage Reporting

The system SHALL collect and report code coverage metrics during CI test execution, enforcing a minimum coverage threshold.

#### Scenario: Coverage Collection
- **WHEN** backend tests are executed in CI
- **THEN** code coverage is collected using Coverlet
- **AND** coverage data is generated in Cobertura format

#### Scenario: Coverage Threshold Enforcement
- **WHEN** code coverage falls below 70%
- **THEN** the CI workflow fails
- **AND** coverage percentage is reported in workflow logs

#### Scenario: Coverage Report Artifact
- **WHEN** backend tests complete in CI
- **THEN** HTML coverage report is generated
- **AND** report is uploaded as workflow artifact
- **AND** report is accessible for 30 days

### Requirement: Backend Test Status Visibility

The system SHALL provide visible indicators of test and coverage status in the repository documentation.

#### Scenario: Status Badges Display
- **WHEN** viewing backend README.md
- **THEN** test workflow status badge is displayed
- **AND** current test status (passing/failing) is visible

### Requirement: Integration Test Database

The system SHALL provide isolated PostgreSQL database instances for integration tests in CI environment.

#### Scenario: PostgreSQL Service Container
- **WHEN** integration tests run in GitHub Actions
- **THEN** PostgreSQL 15 container is started
- **AND** tests connect to the container database
- **AND** container is cleaned up after tests complete

#### Scenario: Test Isolation
- **WHEN** multiple test runs execute
- **THEN** each run uses an isolated database instance
- **AND** no data persists between workflow runs

### Requirement: Test Data Generation with Bogus

The system SHALL provide Bogus-based test data generators in `TestDataGenerator` that create realistic fake entities. This class is the single source of truth for entity generation logic, used by both unit tests (directly) and integration tests (via Mother Objects). All unit tests MUST use `TestDataGenerator` methods instead of inline entity construction.

#### Scenario: Entity Faker Generation
- **WHEN** a unit test needs a fake entity (User, Product, Inventory, etc.)
- **THEN** a corresponding Faker method is available in `TestDataGenerator`
- **AND** the generated entity has realistic values (e.g., `f.Commerce.ProductName()`)
- **AND** key properties can be customized via optional parameters
- **AND** the entity is returned in-memory (not persisted)

#### Scenario: Related Entity Generation
- **WHEN** a test needs entities with relationships (e.g., Inventory with Product and PointOfSale)
- **THEN** the generator allows specifying foreign key values via parameters
- **AND** navigation properties can be populated for in-memory tests

#### Scenario: TestDataGenerator as Single Source
- **WHEN** adding a new entity type to the system
- **THEN** a new Faker and Create method MUST be added to `TestDataGenerator`
- **AND** the corresponding Mother Object MUST use `TestDataGenerator.Create*()` internally
- **AND** default values MUST NOT be duplicated between the two

#### Scenario: Prohibited Inline Entity Construction in Unit Tests
- **WHEN** writing unit tests
- **THEN** developers MUST NOT use `new Entity { Property = value }` for domain entities
- **AND** developers MUST use `TestDataGenerator.Create*()` methods instead
- **AND** code reviews SHALL reject inline entity construction patterns
- **AND** specific property overrides MAY be applied after `TestDataGenerator` call

### Requirement: Database Cleanup with Respawn

The system SHALL use Respawn for database cleanup between integration tests to ensure test isolation. Manual SQL TRUNCATE statements MUST NOT be used.

#### Scenario: Database Reset Before Test
- **WHEN** an integration test requires a clean database state
- **THEN** `ResetDatabaseAsync()` is called on `ApiWebApplicationFactory`
- **AND** Respawn removes all data from tables (except `__EFMigrationsHistory`)
- **AND** seed data is re-applied automatically
- **AND** the operation completes in under 1 second

#### Scenario: Schema Change Resilience
- **WHEN** a new table is added to the database schema
- **THEN** Respawn automatically includes the new table in cleanup
- **AND** no manual SQL TRUNCATE statements need updating
- **AND** existing integration tests continue to work without modification

#### Scenario: Prohibited Manual Truncation
- **WHEN** writing integration tests
- **THEN** developers MUST NOT use `ExecuteSqlRawAsync` with TRUNCATE commands
- **AND** developers MUST use `ResetDatabaseAsync()` exclusively
- **AND** code reviews SHALL reject manual TRUNCATE patterns

### Requirement: Integration Test Container Sharing

The system SHALL share PostgreSQL Testcontainers across integration test classes to optimize execution time.

#### Scenario: Collection Fixture Usage
- **WHEN** multiple integration test classes run
- **THEN** they share a single PostgreSQL container via xUnit collection fixture
- **AND** each test class resets the database before its tests
- **AND** tests remain isolated despite sharing the container

#### Scenario: Container Lifecycle
- **WHEN** the first test in the collection runs
- **THEN** the PostgreSQL container is started once
- **AND** the container is stopped after all tests in the collection complete

### Requirement: Mocking Conventions

The system SHALL follow consistent mocking conventions for unit tests using Moq.

#### Scenario: Repository Mocking
- **WHEN** a service test needs to mock repository behavior
- **THEN** `Mock<IRepository<T>>` is used
- **AND** setup methods define return values for expected calls
- **AND** verify methods confirm expected interactions

#### Scenario: Service Mocking
- **WHEN** a controller or higher-level test needs to mock a service
- **THEN** the service interface is mocked (not the concrete implementation)
- **AND** mocks are configured in Arrange section
- **AND** behavior verification happens in Assert section

### Requirement: Mother Object Pattern for Integration Tests

The system SHALL provide Mother Object classes that create and persist test entities with realistic defaults, simplifying integration test setup. Mother Objects MUST use Bogus (via TestDataGenerator) internally for default values to ensure consistency with unit test data. All core domain entities MUST have corresponding Mother Objects.

#### Scenario: Using TestDataMother Factory
- **WHEN** an integration test needs to create test data
- **THEN** `TestDataMother` is instantiated with `IServiceProvider`
- **AND** fluent builder methods are used to configure entity properties
- **AND** `CreateAsync()` persists the entity to the database
- **AND** the created entity is returned for use in assertions

#### Scenario: Creating Related Entities
- **WHEN** a test needs entities with foreign key relationships
- **THEN** parent entities are created first using their Mother Objects
- **AND** child entities reference parent IDs via fluent `With*()` methods
- **AND** all entities are persisted in the correct order

#### Scenario: Mother Object Default Values via Bogus
- **WHEN** a Mother Object creates an entity without explicit configuration
- **THEN** the Mother Object calls `TestDataGenerator.Create*()` to get a Bogus-generated entity
- **AND** the entity has realistic, randomized default values
- **AND** unique constraints are satisfied via Bogus random generation
- **AND** the entity passes domain validation

#### Scenario: Unified Test Data Architecture
- **WHEN** implementing test data generation
- **THEN** `TestDataGenerator` (Bogus Fakers) is the single source of entity generation logic
- **AND** Mother Objects wrap `TestDataGenerator` for database persistence
- **AND** unit tests use `TestDataGenerator` directly with mocked repositories
- **AND** integration tests use Mother Objects via `TestDataMother`
- **AND** no duplication of default value logic exists between the two patterns

#### Scenario: Mother Object Location and Naming
- **WHEN** creating a new Mother Object
- **THEN** the class is placed in `TestHelpers/Mothers/` directory
- **AND** the class is named `{Entity}Mother` (e.g., `ProductMother`, `SaleMother`)
- **AND** the class is registered in `TestDataMother` factory

#### Scenario: Required Mother Objects for Core Entities
- **WHEN** the test suite is fully configured
- **THEN** `UserMother` MUST exist for creating test users
- **AND** `ProductMother` MUST exist for creating test products
- **AND** `PointOfSaleMother` MUST exist for creating test points of sale
- **AND** `PaymentMethodMother` MUST exist for creating test payment methods
- **AND** `InventoryMother` MUST exist for creating test inventory records
- **AND** `SaleMother` MUST exist for creating test sales
- **AND** `ReturnMother` MUST exist for creating test returns
- **AND** all Mother Objects are accessible via `TestDataMother` factory

#### Scenario: Integration Test Prerequisite Setup
- **WHEN** an integration test requires prerequisite entities (not the system under test)
- **THEN** Mother Objects SHALL be used instead of API calls
- **AND** the test SHALL call the API only for the functionality being tested
- **AND** this reduces test brittleness when unrelated validations change

### Requirement: Integration Test Structure

The system SHALL follow a consistent structure for integration test classes.

#### Scenario: Test Class Setup
- **WHEN** creating a new integration test class
- **THEN** the class implements `IAsyncLifetime`
- **AND** the class is decorated with `[Collection(IntegrationTestCollection.Name)]`
- **AND** `InitializeAsync()` calls `_factory.ResetDatabaseAsync()` first
- **AND** test data is created using Mother Objects after reset

#### Scenario: Authenticated Client Creation
- **WHEN** a test needs an authenticated HTTP client
- **THEN** `CreateAuthenticatedClientAsync()` helper method is used
- **AND** the method posts to `/api/auth/login` and extracts cookies
- **AND** cookies are added to the client's request headers

#### Scenario: Unified Test Collection
- **WHEN** integration tests share database infrastructure
- **THEN** all tests MUST use `[Collection(IntegrationTestCollection.Name)]`
- **AND** separate collection fixtures (e.g., `RepositoryTestCollection`) MUST NOT be created
- **AND** test isolation is achieved via `ResetDatabaseAsync()` not separate containers

