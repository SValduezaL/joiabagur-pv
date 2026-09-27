## MODIFIED Requirements

### Requirement: Deployment is verified from inside the host

Because the AI service is not reachable from outside the environment, post-deployment verification SHALL execute inside the host through the systems management service. The verification MUST fail the deployment when the index is empty, when the configured embedding model disagrees with the indexed one, when the database is unreachable, when the provider credential is absent, or when the point-of-sale availability projection holds no assigned row for any point of sale.

The fifth condition closes a gap the first four left open, and it is the same class of failure the first one exists to catch. An environment whose vector index is full but whose projection is empty **passes verification today**: every retrieval answers 503 for a scoped request, the consumer degrades correctly to its lexical path and answers 200, a valid certificate is served and the screens render — so the deployment looks like a success and finds nothing that the assortment should have narrowed. It is exactly the shape of the empty index, one table along, and it has already reached a deployed environment once.

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

#### Scenario: A healthy deployment passes verification

- **GIVEN** the environment is deployed with the corpus loaded
- **WHEN** post-deployment verification runs
- **THEN** the database is reported reachable
- **AND** the indexed document count is greater than zero
- **AND** the configured embedding model matches the indexed one
- **AND** the provider credential is reported as configured
- **AND** the projection holds assigned rows for at least one point of sale
