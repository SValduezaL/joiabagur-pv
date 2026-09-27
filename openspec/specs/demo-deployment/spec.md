# demo-deployment Specification

## Purpose
Isolated demonstration environment for the AI service, deployed in an AWS account of its own and reachable from the Internet: the network boundary that leaves only the reverse proxy exposed, the classification of configuration between encrypted secrets and versioned literals, a deployment pipeline whose verification runs inside the host because the AI service is private by design, the data path that carries the real catalog and its vector index without the shop's staff accounts, and the persistence of data and certificates across redeployments.
## Requirements
### Requirement: Demo environment is isolated from the production account

The demo environment SHALL be provisioned in an AWS account distinct from the one hosting the shop's production system, from an infrastructure module with its own directory and its own state file. The module MUST NOT declare, reference or modify any resource belonging to the production account.

#### Scenario: Infrastructure plan touches no production resource

- **GIVEN** the demo infrastructure module with its own state
- **WHEN** an infrastructure plan is produced
- **THEN** every resource listed for creation, modification or destruction belongs to the demo module
- **AND** no production instance, security group, role, image repository, parameter or database appears in the plan

#### Scenario: Deployment pipeline references no production identifier

- **WHEN** the demo deployment workflow is inspected
- **THEN** it references only the demo role, the demo instance, the demo image repositories and the demo parameter prefix
- **AND** it does not reference the production deploy role, instance, repository or parameter prefix

#### Scenario: Production deployment path is unmodified

- **WHEN** the change is compared against the base branch
- **THEN** the production bundled image definition is unchanged
- **AND** the production deployment workflow is unchanged
- **AND** the production infrastructure module is unchanged
- **AND** the only production-side edits are deprecation headers on unused files and the correction of backend documentation that described an obsolete deployment path

### Requirement: Only the reverse proxy is reachable from the Internet

The demo environment SHALL expose exactly one service to the Internet. The AI service, the business API container and the database container MUST NOT publish host ports. The security group MUST allow inbound traffic only on the ports served by the reverse proxy.

#### Scenario: AI service publishes no port

- **WHEN** the demo composition file is inspected
- **THEN** the AI service declares no published port
- **AND** the database service declares no published port
- **AND** the business API service declares no published port
- **AND** the reverse proxy is the only service declaring published ports

#### Scenario: AI service is unreachable from outside

- **GIVEN** the demo environment is running
- **WHEN** a client outside the environment attempts to reach the AI service on its service port using the public address
- **THEN** the connection is not established

#### Scenario: Security group admits only proxy traffic

- **WHEN** the demo security group is inspected
- **THEN** its inbound rules admit only the ports served by the reverse proxy
- **AND** no inbound rule admits the AI service port or the database port

### Requirement: Transport security is served under a parameterised hostname

The demo environment SHALL serve traffic over TLS with a certificate valid for the configured hostname. The hostname MUST be supplied as configuration, so the environment can be deployed before a dedicated domain exists and migrated to one later without changing any image.

#### Scenario: Public entry point serves valid TLS

- **GIVEN** the demo environment is deployed with a hostname configured
- **WHEN** a browser opens the public URL
- **THEN** the connection is served over TLS with a certificate valid for that hostname
- **AND** no certificate warning is presented

#### Scenario: Hostname changes without rebuilding images

- **GIVEN** the environment is running under an initial hostname
- **WHEN** the configured hostname is changed and the environment is redeployed
- **THEN** the environment serves the new hostname
- **AND** no application image is rebuilt

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

### Requirement: Shared credentials are derived from a single parameter

Credentials that must match literally across two services — the internal service token secret and the index feed credential — SHALL each be stored as one parameter and read twice at deploy time, rather than stored as two independently editable parameters.

#### Scenario: Internal token secret is identical on both sides

- **WHEN** the deployed environment is inspected
- **THEN** the secret used by the AI service to validate internal tokens and the secret used by the business API to sign them originate from the same stored parameter

#### Scenario: Index feed credential is identical on both sides

- **WHEN** the deployed environment is inspected
- **THEN** the credential the AI service sends to the index feed and the credential the business API accepts originate from the same stored parameter

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

### Requirement: Data and certificates survive a redeployment

Database contents and issued certificates SHALL be held in persistent volumes. The deployment procedure MUST recreate containers in place and MUST NOT remove volumes.

#### Scenario: Corpus survives a redeployment

- **GIVEN** the environment is deployed with the corpus loaded
- **WHEN** the deployment workflow runs again with a new image
- **THEN** the containers are recreated
- **AND** the catalog and the vector index retain their contents

#### Scenario: Certificate survives a redeployment

- **GIVEN** a certificate has been issued for the configured hostname
- **WHEN** the deployment workflow runs again
- **THEN** the certificate is reused from its persistent volume
- **AND** no new certificate is requested from the certificate authority

#### Scenario: Deployment never removes volumes

- **WHEN** the deployment script is inspected
- **THEN** it does not contain any command that removes volumes while stopping the environment

### Requirement: Demo data carries the catalog but not the shop's staff accounts

The demo environment SHALL be populated by restoring the business and vector schemas from the local environment, so the published index is the one the reported figures describe. Personal accounts belonging to the shop's staff MUST be replaced by demonstration accounts before the environment is publicly reachable.

#### Scenario: Vector index is restored rather than recomputed

- **WHEN** the demo environment is populated
- **THEN** the vector index rows are restored from the dump with their existing embeddings
- **AND** the embeddings are not recomputed against the provider

#### Scenario: Reconciliation sync reports no drift

- **GIVEN** the demo environment has been populated from the dump
- **WHEN** a single index synchronisation is executed and the index status is queried
- **THEN** the reported drift count is zero

#### Scenario: Staff accounts are replaced by demonstration accounts

- **WHEN** the demo environment is publicly reachable
- **THEN** no account belonging to the shop's staff can authenticate
- **AND** an administrator demonstration account exists
- **AND** an operator demonstration account exists

### Requirement: The AI container is memory bounded so its failure is contained

The AI service container SHALL declare an explicit memory limit, so that exhausting memory terminates that container alone rather than the host, leaving the business API serving and letting assisted search degrade through the existing circuit breaker.

#### Scenario: Memory limit is declared on the AI service

- **WHEN** the demo composition file is inspected
- **THEN** the AI service declares an explicit memory limit
- **AND** the limit is expressed with a directive that takes effect outside swarm mode

#### Scenario: The environment survives the AI container being terminated

- **GIVEN** the environment is running
- **WHEN** the AI service container is terminated
- **THEN** the reverse proxy and the business API keep serving requests
- **AND** the AI container is restarted by its restart policy
- **AND** assisted search reports the AI as unavailable rather than failing the page

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

### Requirement: Host provisioning knows nothing about the application

Host provisioning SHALL be limited to preparing a container host: installing the container engine and the composition plugin, starting the required system services, retrieving the composition file and deployment script, and running the deployment. Application concerns — reverse proxy configuration, hostnames, certificates and application environment variables — MUST live in the composition file, the images and the parameter store.

#### Scenario: Provisioning contains no application configuration

- **WHEN** the host provisioning script is inspected
- **THEN** it contains no reverse proxy configuration
- **AND** it contains no hostname or certificate handling
- **AND** it contains no application environment variable
- **AND** it does not enumerate application services individually

### Requirement: The demo image serves under any hostname

The image built for the demo environment SHALL resolve its API calls relative to the serving origin, so that the same image works under any hostname without rebuilding.

#### Scenario: Interface calls the API on the serving origin

- **GIVEN** the demo image is built with a relative API base
- **WHEN** the interface is served under the demo hostname
- **THEN** its API calls are issued against the same origin
- **AND** image URLs derived from API-relative paths resolve against the same origin

#### Scenario: Production image definition is not reused or altered

- **WHEN** the change is inspected
- **THEN** the demo image is built from its own definition
- **AND** the production bundled image definition is unchanged
