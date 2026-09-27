## MODIFIED Requirements

### Requirement: Secrets reach containers through the process environment only

Values classified as secrets SHALL be read from the encrypted parameter store at deploy time and passed to containers through the deploying process environment. They MUST NOT be written to any file on the host, MUST NOT be baked into any image, and MUST NOT appear in the deployment command output. A secret MAY be declared **optional**, and for an optional secret the deployment MUST NOT fail when it resolves to an empty value: the service it belongs to degrades to its declared behaviour instead.

Three of the provider credentials are optional, one per generation stage — the sale argument, the intent classifier and the agent loop — and each one absent is a declared state with a rollback of its own rather than a fault. They are **separate parameters and never one parameter read three times**, because the three stages run different models: sharing one would make the cost of a classification of a few tokens indistinguishable from the cost of a paragraph. That is the opposite of the rule the shared internal credentials follow, and deliberately so: there the risk is drift between two copies, here the risk is confusing three costs.

The deployment MUST record, once per stage, whether that stage's credential was present or absent, and MUST NOT record what the value was.

#### Scenario: No environment file is written to the host

- **WHEN** the deployment completes
- **THEN** no environment file containing secret values exists next to the composition file
- **AND** no secret value is present in any file on the host outside container runtime state

#### Scenario: Command output carries no secret

- **WHEN** the output of the remote deployment command is inspected
- **THEN** it contains no secret value
- **AND** shell execution tracing is not enabled for the section that reads secrets

#### Scenario: A missing required value fails the deployment loudly

- **GIVEN** a required configuration value resolves to an empty string
- **WHEN** the deployment script runs
- **THEN** the deployment fails with a message naming the missing value
- **AND** no container is started with that value empty

#### Scenario: A missing optional credential does not fail the deployment

- **GIVEN** an optional provider credential has no parameter in the store
- **WHEN** the deployment script runs
- **THEN** the deployment completes
- **AND** the stage that credential belongs to degrades to its declared behaviour
- **AND** the deployment records that stage's credential as absent without naming any value

#### Scenario: Each generation stage carries its own credential

- **WHEN** the deployment reads the provider credentials
- **THEN** the sale argument, the intent classifier and the agent loop each resolve from a parameter of their own
- **AND** no stage is served by falling back to another stage's credential when its own parameter exists

### Requirement: Behaviour-affecting settings are version controlled, not stored as parameters

Settings that change what the system computes rather than where it runs — the embedding model identifier, the retrieval distance threshold, the stub response mode, and the switches that make each AI route servable by default — SHALL be declared as literals under version control. They MUST NOT be supplied from the parameter store, so that changing them requires code review.

Every AI route that the environment is meant to demonstrate MUST have its default-enabled switch declared explicitly. Omitting one is not a neutral default: the switch is a boolean with no initialiser and an empty per-point-of-sale list, so an omitted switch leaves that route unservable for every point of sale while the composition looks complete.

#### Scenario: Embedding model is a versioned literal

- **WHEN** the demo composition file is inspected
- **THEN** the embedding model identifier appears as a literal value
- **AND** it is not read from the parameter store

#### Scenario: Stub mode is disabled by a versioned literal

- **WHEN** the demo composition file is inspected
- **THEN** stub response mode is declared as a literal and is disabled
- **AND** it is not read from the parameter store

#### Scenario: Retrieval threshold is a versioned literal

- **WHEN** the demo composition file is inspected
- **THEN** the retrieval distance threshold appears as a literal value matching the value the evaluation figures were computed with

#### Scenario: Every demonstrated AI route declares its switch

- **WHEN** the demo composition file is inspected
- **THEN** each AI route the environment demonstrates carries its default-enabled switch as a literal
- **AND** none of those switches is left to its compiled default
- **AND** none of them is read from the parameter store

### Requirement: Deployment is verified from inside the host

Because the AI service is not reachable from outside the environment, post-deployment verification SHALL execute inside the host through the systems management service. The verification MUST fail the deployment when the index is empty, when the configured embedding model disagrees with the indexed one, when the database is unreachable, when the provider credential is absent, when the point-of-sale availability projection holds no assigned row for any point of sale, when the knowledge corpus holds no fragment, or when the agent route does not answer.

The fifth condition closes a gap the first four left open, and it is the same class of failure the first one exists to catch. An environment whose vector index is full but whose projection is empty **passes verification today**: every retrieval answers 503 for a scoped request, the consumer degrades correctly to its lexical path and answers 200, a valid certificate is served and the screens render — so the deployment looks like a success and finds nothing that the assortment should have narrowed. It is exactly the shape of the empty index, one table along, and it has already reached a deployed environment once.

The sixth condition is the third table of that same series. With no knowledge fragment indexed, the piece-anchored argument is withheld for want of material to anchor it to and the piece-anchored question answers that the corpus does not cover it — both of which read on screen as a defect of the sale card, not of the deployment.

The seventh condition MUST distinguish a route that does not answer from a route that answers a declared degradation. A response carrying a stop reason of provider failure or of absent client is a **successful** response at the transport layer and MUST NOT fail the verification: it is the behaviour the layer is specified to have when its credential or its provider is unavailable.

#### Scenario: Verification runs inside the host

- **WHEN** the deployment workflow verifies the result
- **THEN** the check is executed inside the host through the systems management service
- **AND** the check does not require the AI service to be reachable from the pipeline runner

#### Scenario: An empty index fails the deployment

- **GIVEN** the environment is deployed but the vector index contains no documents
- **WHEN** post-deployment verification runs
- **THEN** the verification fails
- **AND** the deployment is not reported as successful

#### Scenario: An empty projection fails the deployment

- **GIVEN** the environment is deployed with the vector index populated and the point-of-sale projection holding no assigned row
- **WHEN** post-deployment verification runs
- **THEN** the verification fails naming the projection as the cause
- **AND** the deployment is not reported as successful

#### Scenario: An empty knowledge corpus fails the deployment

- **GIVEN** the environment is deployed with the vector index populated and the knowledge corpus holding no fragment
- **WHEN** post-deployment verification runs
- **THEN** the verification fails naming the corpus as the cause
- **AND** the deployment is not reported as successful

#### Scenario: An agent route that does not answer fails the deployment

- **GIVEN** the environment is deployed and the agent route does not answer
- **WHEN** post-deployment verification runs
- **THEN** the verification fails naming the agent route as the cause
- **AND** the deployment is not reported as successful

#### Scenario: A declared degradation of the agent route does not fail the deployment

- **GIVEN** the agent route answers with a stop reason of provider failure or of absent client
- **WHEN** post-deployment verification runs
- **THEN** the verification does not fail on that condition
- **AND** the degradation is reported rather than treated as an outage

#### Scenario: A healthy deployment passes verification

- **GIVEN** the environment is deployed with the corpus loaded
- **WHEN** post-deployment verification runs
- **THEN** the database is reported reachable
- **AND** the indexed document count is greater than zero
- **AND** the configured embedding model matches the indexed one
- **AND** the provider credential is reported as configured
- **AND** the projection holds assigned rows for at least one point of sale
- **AND** the knowledge corpus holds at least one fragment
- **AND** the agent route answers

### Requirement: Images and provisioning are reproducible

Application images and host provisioning SHALL pin every external artefact to an explicit version, and every corpus the service indexes MUST travel inside the image that indexes it. Moving tags MUST NOT be used, so the same commit produces the same environment on any day and in any account.

An image whose indexing command has no corpus to read is not reproducible even when every dependency is pinned: the environment's behaviour then depends on whatever was copied onto the host by hand, so a freshly provisioned host starts with an empty table while an older one appears to work. The corpus MUST therefore be copied into the image from a build context, MUST NOT be supplied to the container by a mount from the deployment bundle, and MUST NOT be placed on the host after the fact; and a build that does not supply it MUST fail rather than produce an image without it.

The last clause is the one that carries the guarantee, and it is why a pre-build copy step outside the image definition does not satisfy this requirement: such a step leaves `docker build` able to succeed and produce a corpus-less image in silence, which is the failure this exists to remove. Declaring the corpus as an input of the image definition makes its absence a build error.

The path the corpus is copied to MUST be one the service resolves in an installed layout, and that resolution MUST NOT depend on the package being importable from a source checkout. Deriving a data path by counting parent directories from the module file is correct in a checkout and wrong once the package is installed into a virtual environment, where it resolves inside the dependency tree — measured in the deployed environment as `/app/.venv/lib/data/knowledge`, a directory nothing writes to. A copy aimed at such a path, or a symbolic link pointing at it, satisfies the letter of this requirement and leaves the defect in place.

#### Scenario: Dependency installer is version pinned

- **WHEN** the AI service image definition is inspected
- **THEN** the dependency installer is copied from an explicitly versioned source
- **AND** no moving tag is used for it

#### Scenario: Composition plugin is version pinned

- **WHEN** the host provisioning script is inspected
- **THEN** the composition plugin is installed from an explicitly versioned release

#### Scenario: Base operating system image is resolved automatically

- **WHEN** the demo infrastructure module is inspected
- **THEN** the base operating system image is resolved from the provider's published parameter
- **AND** no manual image identifier variable must be updated before applying

#### Scenario: The knowledge corpus is inside the AI service image

- **WHEN** the AI service image is inspected
- **THEN** the knowledge corpus directory exists inside it at the path the service reads
- **AND** it is a real directory and not a link to somewhere the image does not populate
- **AND** the indexing command can populate the corpus table with no file supplied by the host

#### Scenario: The corpus is not supplied by a host mount

- **WHEN** the demo composition file is inspected
- **THEN** the AI service declares no volume carrying the knowledge corpus
- **AND** a host with no deployment bundle unpacked still yields a populated corpus table after indexing

#### Scenario: A build that does not supply the corpus fails

- **GIVEN** the corpus is declared as an input of the image definition
- **WHEN** the image is built without that input supplied
- **THEN** the build fails
- **AND** no image is produced that would answer as if the corpus were present

#### Scenario: The corpus path resolves in an installed layout

- **GIVEN** the service package is installed into a virtual environment rather than imported from a source checkout
- **WHEN** the service resolves the directory it reads the corpus from
- **THEN** the resolved directory is the one the image populates
- **AND** it is not a directory inside the dependency tree
