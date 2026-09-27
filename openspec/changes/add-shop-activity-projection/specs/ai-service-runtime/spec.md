## MODIFIED Requirements

### Requirement: Service exposes public health with version

The `jbg-ai` service SHALL expose `GET /health` without authentication. The response MUST be HTTP 200 when the process is running and MUST include an OK status indicator and the configured service version (`SERVICE_VERSION`).

The response MUST additionally report database reachability, the state of the vector index, whether the embedding provider credential is configured, and the state of the point-of-sale availability projection. The endpoint MUST NOT call the embedding or LLM provider: the provider field reports **configuration presence only**, never provider reachability. A third-party outage MUST NOT be able to make this endpoint fail.

The projection section MUST report when the feed was last drained, when it was last drained in full, the elapsed time since the last drain, whether that elapsed time exceeds the configured staleness ceiling, the ceiling itself, the number of pages recorded as failed, the number of **active** points of sale the service knows of, and the number of those holding no assigned row. The failed page count MUST be read from the persisted record of failed batches rather than from the outcome of the drain that happens to have run most recently in this process, because that record survives a restart and because nothing else reads it today, so a page that failed months ago is otherwise invisible for ever; it MUST be reported per feed rather than for the projection feed alone, so that failures recorded against the catalog feed stop being unreachable to every reader. The elapsed time MUST be computed from `ai.sync_checkpoint.last_incremental_sync_at` for the `pos-availability` feed and MUST NOT be derived from `ai.pos_projection.refreshed_at` in any form, because the feed is incremental by keyset, so that column records when an assignment last changed rather than when the projection was last looked at.

The count of points of sale holding no assigned row MUST be taken over the points of sale recorded as active in schema `ai`, and MUST be reported as unknown when the service knows of no point of sale at all. Reporting zero in that state would assert that every active point of sale is served, which is a claim the service cannot make before its shop reading has arrived; and the number of known active points of sale travels beside the count precisely so a consumer can tell *nothing is wrong* from *nothing is known*. Counting without regard to activity is what made a deliberately closed shop indistinguishable from a broken one, and it failed a healthy deployment on 2026-09-27.

Reporting the elapsed time and the staleness verdict together is deliberate and is not redundancy: the elapsed time informs a reader, while the verdict states what the retrieval guard decided against the ceiling this deployment is configured with. Deriving the verdict on the consumer's side would duplicate the threshold in two places, and the ceiling travels with it so a consumer can explain the verdict without knowing the service's configuration.

The reported age MUST be described as a property of the drain and never of a point of sale, because the checkpoint holds one row per feed and every scope therefore reports the same value.

The reported state MUST be cached for a short window so that repeated probing does not consume the capped database connection pool.

The handler's return annotation MUST remain an open mapping and no new route may be introduced by this requirement, so that the versioned OpenAPI snapshot is unaffected. This is what allows the projection section to be added at no contract cost on either side of the boundary: the consumer's typed reading of this payload ignores fields it does not recognise rather than failing on them, and that same tolerance is what lets the count of active points of sale be published here without moving the typed consumer on the .NET side.

#### Scenario: Health returns OK with version

- **WHEN** the service is running with required configuration present
- **AND** a client calls `GET /health`
- **THEN** the response status is 200
- **AND** the body indicates OK status
- **AND** the body includes the configured service version

#### Scenario: Health does not require authentication

- **WHEN** a client calls `GET /health` without any auth token
- **THEN** the request is accepted (not rejected for missing credentials)

#### Scenario: Health reports database, index and provider configuration

- **GIVEN** the service is configured with a database and an embedding provider credential
- **WHEN** a client calls `GET /health`
- **THEN** the body reports the database as reachable
- **AND** the body reports the number of indexed documents
- **AND** the body reports the provider credential as configured

#### Scenario: Health reports a missing provider credential without failing

- **GIVEN** no embedding provider credential is configured
- **WHEN** a client calls `GET /health`
- **THEN** the response status is 200
- **AND** the body reports the provider credential as missing

#### Scenario: Health never calls the provider

- **GIVEN** the embedding provider is unreachable or returning errors
- **WHEN** a client calls `GET /health`
- **THEN** the response status is 200
- **AND** no request is issued to the embedding or LLM provider
- **AND** the provider field still reports whether the credential is configured

#### Scenario: Health degrades when the database is unreachable

- **GIVEN** the database cannot be reached
- **WHEN** a client calls `GET /health`
- **THEN** the body reports the database as unavailable
- **AND** the overall status indicates degradation
- **AND** the endpoint still responds rather than raising

#### Scenario: Health state is cached between probes

- **GIVEN** a client calls `GET /health` twice within the cache window
- **WHEN** the second call is served
- **THEN** the database is not probed a second time
- **AND** the vector index is not queried a second time

#### Scenario: Enriched health does not move the frozen contract

- **WHEN** the versioned OpenAPI snapshot is regenerated from the canonical settings profile
- **THEN** it is byte-identical to the committed snapshot
- **AND** the `/health` operation still declares an open object response

#### Scenario: Health reports projection freshness taken from the checkpoint

- **GIVEN** a projection whose rows were last written long ago and whose feed was drained moments ago
- **WHEN** a client calls `GET /health`
- **THEN** the body reports a small elapsed time since the last drain
- **AND** that value derives from the `pos-availability` checkpoint and not from the age of the rows
- **AND** the body reports the staleness verdict and the configured ceiling alongside it

#### Scenario: Health reports an active point of sale left without any assortment

- **GIVEN** a shop reading in which one active point of sale holds no assigned row in the projection
- **WHEN** a client calls `GET /health`
- **THEN** the body reports that one active point of sale carries no assortment
- **AND** the body reports how many active points of sale the service knows of

#### Scenario: A point of sale closed on purpose is not reported as lacking assortment

- **GIVEN** a point of sale recorded as inactive whose projection rows all carry the assignment hint unset
- **WHEN** a client calls `GET /health`
- **THEN** it is not counted among the points of sale carrying no assortment
- **AND** the overall status is unaffected by it

#### Scenario: Health reports the count as unknown before any shop reading has arrived

- **GIVEN** the service knows of no point of sale because the shop reading has not yet been drained
- **WHEN** a client calls `GET /health`
- **THEN** the response status is 200
- **AND** the number of active points of sale is reported as zero
- **AND** the number carrying no assortment is reported as unknown rather than as zero

#### Scenario: Failed pages are reported per feed

- **GIVEN** failures recorded against the catalog feed and none against the projection feed
- **WHEN** a client calls `GET /health`
- **THEN** the body reports the catalog failures under their own feed
- **AND** the projection feed still reports its own count unchanged

#### Scenario: The projection section does not move the frozen contract

- **GIVEN** the projection section is part of the health payload
- **WHEN** the OpenAPI snapshot test runs
- **THEN** it passes against the committed `ai-service/openapi.json` without regenerating it
- **AND** no route was added under `/v1`

#### Scenario: Health stays 200 when the projection has never been drained

- **GIVEN** no checkpoint exists for the `pos-availability` feed
- **WHEN** a client calls `GET /health`
- **THEN** the response status is 200
- **AND** the projection section reports the absence rather than an elapsed time
