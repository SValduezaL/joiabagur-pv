## MODIFIED Requirements

### Requirement: Deployment is verified from inside the host

Because the AI service is not reachable from outside the environment, post-deployment verification SHALL execute inside the host through the systems management service. The verification MUST fail the deployment when the index is empty, when the configured embedding model disagrees with the indexed one, when the database is unreachable, when the provider credential is absent, when the service knows of no active point of sale or when any **active** point of sale holds no assigned row in the point-of-sale availability projection, when the knowledge corpus holds no fragment, or when the agent route does not answer. Before evaluating the projection conditions the verification MUST wait, up to a bounded time, until the service reports its drains as having run, so that it judges the environment rather than the instant it happened to probe.

The fifth condition closes a gap the first four left open, and it is the same class of failure the first one exists to catch. An environment whose vector index is full but whose projection is empty **passes verification today**: every retrieval answers 503 for a scoped request, the consumer degrades correctly to its lexical path and answers 200, a valid certificate is served and the screens render — so the deployment looks like a success and finds nothing that the assortment should have narrowed. It is exactly the shape of the empty index, one table along, and it has already reached a deployed environment once.

**That condition must speak of active points of sale, and until this change it did not.** Worded as *any* point of sale, it obliged a false alarm: a shop closed on purpose keeps its rows with every assignment correctly retired, which is exactly what should happen to the assortment of a shop that stopped trading, and the condition read that correctness as a fault. It failed a healthy deployment on 2026-09-27 over one such shop out of twelve, with the other six conditions passing. The same miscount reaches the administrator's screen through the health report, so the correction belongs to what is counted and not to what reads the count.

**The condition MUST fail when the service knows of no active point of sale at all, and that half is not defensive.** The schema revision that creates the shop reading is applied partway through the deployment, after the containers are up and before this verification runs, so the table is empty for a window that every redeployment passes through — and a condition that counts shops lacking an assortment returns zero over an empty table. Passing on emptiness is the defect this whole series exists to close: an empty index, an empty projection and an empty corpus each looked like success before they were made to fail, and a fourth instance introduced by the fix for the third would be worse than the fault it replaced. Absence of the reported figure altogether MUST remain tolerated as version skew of the AI image, which is a different thing from a figure present and reporting nothing known.

The sixth condition is the third table of that same series. With no knowledge fragment indexed, the piece-anchored argument is withheld for want of material to anchor it to and the piece-anchored question answers that the corpus does not cover it — both of which read on screen as a defect of the sale card, not of the deployment.

The seventh condition MUST distinguish a route that does not answer from a route that answers a declared degradation. A response carrying a stop reason of provider failure or of absent client is a **successful** response at the transport layer and MUST NOT fail the verification: it is the behaviour the layer is specified to have when its credential or its provider is unavailable.

**What the verification records MUST describe the environment at the time it is read.** The health report is cached for a short window and the start-up drain may need more than one attempt when the business API is not yet serving its feed, so a probe issued immediately can report a staleness that the drain has already cured — as it did on 2026-09-27, printing an age of a hundred and fifteen times the ceiling six seconds after the checkpoint had been written. That figure failed nothing, and it is the figure somebody reads a month later to decide whether the environment is sound.

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

#### Scenario: An active point of sale without assortment fails the deployment

- **GIVEN** the environment is deployed and one point of sale recorded as active holds no assigned row in the projection
- **WHEN** post-deployment verification runs
- **THEN** the verification fails naming that point of sale count as the cause
- **AND** the deployment is not reported as successful

#### Scenario: A point of sale closed on purpose does not fail the deployment

- **GIVEN** the environment is deployed and one point of sale is recorded as inactive with its whole assortment retired
- **WHEN** post-deployment verification runs
- **THEN** the verification does not fail on that condition
- **AND** the deployment is reported as successful when the remaining conditions pass

#### Scenario: A service that knows of no point of sale fails the deployment

- **GIVEN** the environment is deployed and the service reports that it knows of no active point of sale
- **WHEN** post-deployment verification runs
- **THEN** the verification fails
- **AND** the deployment is not reported as successful

#### Scenario: An AI image that does not report the figure is tolerated

- **GIVEN** an AI image older than this change, whose health report omits the count of active points of sale entirely
- **WHEN** post-deployment verification runs
- **THEN** the verification does not fail on that condition
- **AND** the omission is reported as version skew rather than as an empty environment

#### Scenario: Verification waits for the drains before judging the projection

- **GIVEN** the start-up drain has not yet completed when verification begins
- **WHEN** post-deployment verification runs
- **THEN** it retries the health probe up to a bounded time before evaluating the projection conditions
- **AND** the figures it records are those of the environment after the drains ran
- **AND** it does not report a staleness that the drain had already cured

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
- **AND** the service knows of at least one active point of sale
- **AND** every active point of sale holds assigned rows in the projection
- **AND** the knowledge corpus holds at least one fragment
- **AND** the agent route answers
