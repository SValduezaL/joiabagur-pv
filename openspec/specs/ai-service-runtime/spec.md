# ai-service-runtime Specification

## Purpose
Runnable `jbg-ai` process behavior: fail-fast settings, public health with version, structured logging with `trace_id`, in-process smoke tests without external AI or production DB, and optional `JPV_RAG_LLM_*`, `JPV_EMBEDDING_*`, `JPV_INDEX_FEED_*`, `JPV_RETRIEVAL_DISTANCE_THRESHOLD`, `JPV_QUERY_EXPANSION_ENABLED` and the hybrid fusion settings — smoothing constant, per-list weights and branch depth — that MUST NOT block boot or `GET /health`.
## Requirements
### Requirement: Service exposes public health with version

The `jbg-ai` service SHALL expose `GET /health` without authentication. The response MUST be HTTP 200 when the process is running and MUST include an OK status indicator and the configured service version (`SERVICE_VERSION`).

The response MUST additionally report database reachability, the state of the vector index, whether the embedding provider credential is configured, and the state of the point-of-sale availability projection. The endpoint MUST NOT call the embedding or LLM provider: the provider field reports **configuration presence only**, never provider reachability. A third-party outage MUST NOT be able to make this endpoint fail.

The projection section MUST report when the feed was last drained, when it was last drained in full, the elapsed time since the last drain, whether that elapsed time exceeds the configured staleness ceiling, the ceiling itself, the number of pages recorded as failed for that feed, and the number of points of sale holding no assigned row. The failed page count MUST be read from the persisted record of failed batches rather than from the outcome of the drain that happens to have run most recently in this process, because that record survives a restart and because nothing else reads it today, so a page that failed months ago is otherwise invisible for ever. The elapsed time MUST be computed from `ai.sync_checkpoint.last_incremental_sync_at` for the `pos-availability` feed and MUST NOT be derived from `ai.pos_projection.refreshed_at` in any form, because the feed is incremental by keyset, so that column records when an assignment last changed rather than when the projection was last looked at.

Reporting the elapsed time and the staleness verdict together is deliberate and is not redundancy: the elapsed time informs a reader, while the verdict states what the retrieval guard decided against the ceiling this deployment is configured with. Deriving the verdict on the consumer's side would duplicate the threshold in two places, and the ceiling travels with it so a consumer can explain the verdict without knowing the service's configuration.

The reported age MUST be described as a property of the drain and never of a point of sale, because the checkpoint holds one row per feed and every scope therefore reports the same value.

The reported state MUST be cached for a short window so that repeated probing does not consume the capped database connection pool.

The handler's return annotation MUST remain an open mapping and no new route may be introduced by this requirement, so that the versioned OpenAPI snapshot is unaffected. This is what allows the projection section to be added at no contract cost on either side of the boundary: the consumer's typed reading of this payload ignores fields it does not recognise rather than failing on them.

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

#### Scenario: Health reports a point of sale left without any assortment

- **GIVEN** a projection in which one point of sale holds no assigned row
- **WHEN** a client calls `GET /health`
- **THEN** the body reports that one point of sale carries no assortment

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

### Requirement: Settings fail fast on missing required environment
On startup, `jbg-ai` MUST load settings via pydantic-settings. `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` MUST be required. If any of them is missing or empty, the process MUST fail immediately with a clear error identifying the missing setting and MUST NOT continue serving requests. `LOG_LEVEL` MAY default to `INFO`. `JWT_TTL_SECONDS` MAY default to `300`. `STUB_MODE` MAY default to `true`. `ENABLE_DEV_ENDPOINTS` MAY default from `APP_ENV`, resolving to false under a production profile. `DATABASE_URL` MUST be optional and MUST have no default; `DB_POOL_SIZE` MUST be optional and MAY default to `5`. Their absence MUST NOT prevent the process from starting or from serving the routes that do not use the database.

#### Scenario: Missing required env aborts startup
- **WHEN** `APP_ENV`, `SERVICE_VERSION` or `JWT_SECRET` is missing
- **AND** settings are loaded (application boot or settings factory)
- **THEN** loading fails with an error identifying the missing setting
- **AND** the service does not remain listening in a half-started state

#### Scenario: Empty signing secret aborts startup
- **WHEN** `JWT_SECRET` is present but empty or blank
- **AND** settings are loaded
- **THEN** loading fails with an error identifying `JWT_SECRET`
- **AND** no authenticated route is served

#### Scenario: Valid minimal env allows boot
- **WHEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** optional `LOG_LEVEL`, `JWT_TTL_SECONDS`, `STUB_MODE` and `ENABLE_DEV_ENDPOINTS` are omitted
- **THEN** settings load successfully with `JWT_TTL_SECONDS` at `300` and `STUB_MODE` enabled
- **AND** the service can serve `GET /health`

#### Scenario: Absent database configuration does not block startup
- **WHEN** `DATABASE_URL` and `DB_POOL_SIZE` are omitted
- **AND** the required settings are present
- **THEN** settings load successfully with `DB_POOL_SIZE` at `5`
- **AND** the service starts and serves `GET /health`
- **AND** the `/v1` routes answer without opening a database connection

#### Scenario: Database configuration is accepted when supplied
- **WHEN** `DATABASE_URL` is set to a PostgreSQL connection string
- **AND** settings are loaded
- **THEN** the value is available to the database layer
- **AND** no connection is opened as a side effect of loading settings

### Requirement: Structured logging includes trace_id
Each HTTP request MUST be associated with a `trace_id`. When a validated internal service token carries a `trace_id` claim, that value MUST be used. Otherwise, if the request includes header `X-Trace-Id`, that value MUST be used; otherwise the service MUST generate a UUID. Structured logs for that request MUST include `trace_id`. The service SHOULD return the `trace_id` on the response (e.g. `X-Trace-Id` header).

#### Scenario: Token claim takes precedence over the header
- **WHEN** an authenticated request carries a `trace_id` claim and a different `X-Trace-Id` header value
- **THEN** structured logs for that request include the claim value
- **AND** the response reports that same value

#### Scenario: Incoming trace id is preserved
- **WHEN** a client calls an endpoint with `X-Trace-Id` set to a known value and no token trace claim applies
- **THEN** structured logs for that request include the same `trace_id`
- **AND** the response includes that `trace_id` (header or documented field)

#### Scenario: Missing trace id is generated
- **WHEN** a client calls an endpoint without `X-Trace-Id` and no token trace claim applies
- **THEN** the service generates a non-empty `trace_id`
- **AND** structured logs for that request include the generated `trace_id`

### Requirement: Automated smoke tests without external AI or production DB
The `ai-service` test suite MUST verify health and settings fail-fast using FastAPI `TestClient` (or equivalent in-process client). Tests MUST NOT call real LLM providers, embedding APIs, or production RDS.

#### Scenario: Health test passes in process
- **WHEN** `test_health_returns_ok_with_version` runs with required env provided to the test process
- **THEN** the assertion on OK status and version succeeds without network calls to LLM or RDS

#### Scenario: Settings fail-fast test passes
- **WHEN** `test_settings_fail_fast_when_required_env_missing` runs without a required env var
- **THEN** the test expects and observes settings load failure

### Requirement: RAG LLM settings do not block process boot
`JPV_RAG_LLM_API_KEY`, `JPV_RAG_LLM_MODEL`, `JPV_RAG_LLM_BASE_URL` and `JPV_RAG_LLM_CONCURRENCY` MUST be optional when settings load. Their absence or a blank string MUST NOT prevent the process from starting or from serving `GET /health`. `JPV_RAG_LLM_CONCURRENCY` MUST default to 8 when omitted. These settings MUST stay distinct from `JPV_CATALOG_LLM_*`. The real enrichment pipeline MUST require `JPV_RAG_LLM_API_KEY` at call time and MUST fail explicitly if it is missing; `/health` MUST NOT perform that check.

#### Scenario: Health starts without a RAG LLM key
- **GIVEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** `JPV_RAG_LLM_API_KEY`, `JPV_RAG_LLM_MODEL`, `JPV_RAG_LLM_BASE_URL` and `JPV_RAG_LLM_CONCURRENCY` are omitted
- **WHEN** settings load and a client calls `GET /health`
- **THEN** settings load successfully
- **AND** `JPV_RAG_LLM_CONCURRENCY` is 8
- **AND** the response status is 200

#### Scenario: Blank RAG LLM strings are treated as unset
- **GIVEN** `JPV_RAG_LLM_API_KEY` is present as an empty or whitespace string
- **WHEN** settings load
- **THEN** the key is treated as absent
- **AND** the process can serve `GET /health`

#### Scenario: Canonical OpenAPI settings pin RAG keys to absent
- **WHEN** `canonical_openapi_settings` is built
- **THEN** the RAG LLM key, model and base URL are unset
- **AND** no process environment value leaks into the committed OpenAPI snapshot

### Requirement: Embedding settings do not block process boot
`JPV_EMBEDDING_API_KEY`, `JPV_EMBEDDING_MODEL`, `JPV_EMBEDDING_BASE_URL` and `JPV_EMBEDDING_BATCH_SIZE` MUST be optional when settings load. Their absence or a blank string MUST NOT prevent the process from starting or from serving `GET /health`. `JPV_EMBEDDING_BATCH_SIZE` MUST default to 64 when omitted or blank. These settings MUST stay distinct from `JPV_RAG_LLM_*` and `JPV_CATALOG_LLM_*`. The real embedding adapter MUST require `JPV_EMBEDDING_API_KEY` at call time and MUST fail explicitly if it is missing; `/health` MUST NOT perform that check. `canonical_openapi_settings` MUST pin the embedding key, model and base URL to unset and the batch size to 64.

#### Scenario: Health starts without an embedding key
- **GIVEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** `JPV_EMBEDDING_API_KEY`, `JPV_EMBEDDING_MODEL`, `JPV_EMBEDDING_BASE_URL` and `JPV_EMBEDDING_BATCH_SIZE` are omitted
- **WHEN** settings load and a client calls `GET /health`
- **THEN** settings load successfully
- **AND** `JPV_EMBEDDING_BATCH_SIZE` is 64
- **AND** the response status is 200

#### Scenario: Blank embedding strings are treated as unset
- **GIVEN** `JPV_EMBEDDING_API_KEY` is present as an empty or whitespace string
- **WHEN** settings load
- **THEN** the key is treated as absent
- **AND** the process can serve `GET /health`

#### Scenario: Canonical OpenAPI settings pin embedding keys to absent
- **WHEN** `canonical_openapi_settings` is built
- **THEN** the embedding key, model and base URL are unset
- **AND** the embedding batch size is 64
- **AND** no process environment value leaks into the committed OpenAPI snapshot

### Requirement: Index feed settings do not block process boot
`JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY` and `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` MUST be optional when settings load. Their absence or a blank string MUST NOT prevent the process from starting or from serving `GET /health`. `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` MUST default to 180 when omitted or blank. These settings MUST stay distinct from `JWT_SECRET`, `JPV_EMBEDDING_*`, `JPV_RAG_LLM_*` and `JPV_CATALOG_LLM_*`. The real catalog sync MUST require `JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY` and `JPV_EMBEDDING_API_KEY` at call time and MUST fail with HTTP 503 naming the missing setting if any is absent; `/health` MUST NOT perform that check. The feed API key MUST NOT fall back to `JWT_SECRET`. `canonical_openapi_settings` MUST pin the feed base URL and API key to unset and the time budget to 180.

#### Scenario: Health starts without a feed key
- **GIVEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** `JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY` and `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` are omitted
- **WHEN** settings load and a client calls `GET /health`
- **THEN** settings load successfully
- **AND** `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` is 180
- **AND** the response status is 200

#### Scenario: Blank feed strings are treated as unset
- **GIVEN** `JPV_INDEX_FEED_API_KEY` is present as an empty or whitespace string
- **WHEN** settings load
- **THEN** the key is treated as absent
- **AND** the process can serve `GET /health`

#### Scenario: Canonical OpenAPI settings pin feed keys to absent
- **WHEN** `canonical_openapi_settings` is built
- **THEN** the index feed base URL and API key are unset
- **AND** the sync time budget is 180
- **AND** no process environment value leaks into the committed OpenAPI snapshot

#### Scenario: Real sync does not use JWT_SECRET as the feed key
- **GIVEN** `STUB_MODE` is false
- **AND** `JPV_INDEX_FEED_API_KEY` is absent
- **AND** `JWT_SECRET` is present
- **WHEN** `POST /v1/index/sync` is called
- **THEN** the response status is 503
- **AND** the detail names `JPV_INDEX_FEED_API_KEY`
- **AND** `JWT_SECRET` is not sent as `X-Index-Feed-Key`

### Requirement: Retrieval distance threshold does not block process boot
`JPV_RETRIEVAL_DISTANCE_THRESHOLD` MUST be optional when settings load. When omitted or supplied as a blank string it MUST default to 0.65. A configured value MUST be greater than 0 and MUST NOT exceed 2 (the cosine distance domain of pgvector `<=>`). Absence of this setting MUST NOT prevent the process from starting or from serving `GET /health`. The setting MUST stay distinct from `JWT_SECRET`, `JPV_EMBEDDING_*`, `JPV_RAG_LLM_*`, `JPV_INDEX_FEED_*` and `JPV_CATALOG_LLM_*`. `/health` MUST NOT perform a retrieval query. `canonical_openapi_settings` MUST pin the threshold to 0.65 so a process environment value does not leak into the committed OpenAPI snapshot.

#### Scenario: Health starts without a retrieval threshold
- **GIVEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** `JPV_RETRIEVAL_DISTANCE_THRESHOLD` is omitted
- **WHEN** settings load and a client calls `GET /health`
- **THEN** settings load successfully
- **AND** `JPV_RETRIEVAL_DISTANCE_THRESHOLD` is 0.65
- **AND** the response status is 200

#### Scenario: Blank retrieval threshold is treated as the default
- **GIVEN** `JPV_RETRIEVAL_DISTANCE_THRESHOLD` is present as an empty or whitespace string
- **WHEN** settings load
- **THEN** the threshold is 0.65
- **AND** the process can serve `GET /health`

#### Scenario: Canonical OpenAPI settings pin the retrieval threshold
- **WHEN** `canonical_openapi_settings` is built
- **THEN** the retrieval distance threshold is 0.65
- **AND** no process environment value leaks into the committed OpenAPI snapshot

### Requirement: Query expansion flag does not block process boot
`JPV_QUERY_EXPANSION_ENABLED` MUST be optional when settings load. When omitted or supplied as a blank string it MUST default to `true`. Absence of this setting MUST NOT prevent the process from starting or from serving `GET /health`, and `GET /health` MUST NOT load the synonym dictionary. The setting MUST stay distinct from `JWT_SECRET`, `JPV_EMBEDDING_*`, `JPV_RAG_LLM_*`, `JPV_INDEX_FEED_*`, `JPV_CATALOG_LLM_*` and `JPV_RETRIEVAL_DISTANCE_THRESHOLD`. It MUST supply only the default: the effective value MUST travel as a parameter of the retrieval orchestration call, so that several configurations can be evaluated in one process without restarting it, and it MUST NOT be added to the retrieval request schema. `canonical_openapi_settings` MUST pin the flag to its default so a process environment value does not leak into the committed OpenAPI snapshot.

#### Scenario: Health starts without the expansion flag
- **GIVEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** `JPV_QUERY_EXPANSION_ENABLED` is omitted
- **WHEN** settings load and a client calls `GET /health`
- **THEN** settings load successfully
- **AND** `JPV_QUERY_EXPANSION_ENABLED` is `true`
- **AND** the response status is 200
- **AND** no synonym dictionary is loaded to answer the health request

#### Scenario: Blank expansion flag is treated as the default
- **GIVEN** `JPV_QUERY_EXPANSION_ENABLED` is present as an empty or whitespace string
- **WHEN** settings load
- **THEN** the flag is `true`
- **AND** the process can serve `GET /health`

#### Scenario: The flag can be turned off by environment
- **GIVEN** `JPV_QUERY_EXPANSION_ENABLED` is set to a false value
- **WHEN** settings load
- **THEN** the flag is `false`
- **AND** the retrieval endpoint keeps answering with the same response shape

#### Scenario: Canonical OpenAPI settings pin the expansion flag
- **WHEN** `canonical_openapi_settings` is built
- **THEN** the query expansion flag is `true`
- **AND** no process environment value leaks into the committed OpenAPI snapshot
- **AND** `ai-service/openapi.json` is unchanged by this change


### Requirement: Fusion settings do not block process boot
The smoothing constant, the per-list weights and the branch depth used by the hybrid fusion MUST be optional when settings load. When omitted or supplied as blank strings they MUST fall back to their documented defaults, and their absence MUST NOT prevent the process from starting or from serving `GET /health`. `GET /health` MUST NOT run a retrieval or load the synonym dictionary in order to answer.

The default weight of the vector list MUST be lower than the default weight of either lexical list, and the two lexical weights MUST sum to the weight of a single lexical list. The default branch depth MUST be of the same order as the smoothing constant. Each setting MUST stay distinct from `JWT_SECRET`, `JPV_EMBEDDING_*`, `JPV_RAG_LLM_*`, `JPV_INDEX_FEED_*`, `JPV_CATALOG_LLM_*`, `JPV_RETRIEVAL_DISTANCE_THRESHOLD` and `JPV_QUERY_EXPANSION_ENABLED`.

These settings MUST supply only the defaults: the effective values MUST travel as parameters of the retrieval orchestration call, so that several configurations can be evaluated in one process without restarting it, and they MUST NOT be added to the retrieval request schema. `canonical_openapi_settings` MUST pin every one of them to its default so that a process environment value cannot leak into the committed OpenAPI snapshot.

#### Scenario: Health starts without the fusion settings
- **GIVEN** `APP_ENV`, `SERVICE_VERSION` and `JWT_SECRET` are set
- **AND** every fusion setting is omitted
- **WHEN** settings load and a client calls `GET /health`
- **THEN** settings load successfully
- **AND** each fusion setting holds its documented default
- **AND** the response status is 200
- **AND** no retrieval is run and no synonym dictionary is loaded to answer the health request

#### Scenario: Blank fusion settings are treated as the defaults
- **GIVEN** the fusion settings are present as empty or whitespace strings
- **WHEN** settings load
- **THEN** each holds its documented default
- **AND** the process can serve `GET /health`

#### Scenario: The measured default weighting is preserved
- **WHEN** settings load with no fusion setting supplied
- **THEN** the vector list weight is lower than the typed lexical list weight
- **AND** it is lower than the expanded lexical list weight
- **AND** the two lexical weights sum to the weight of a single lexical list

#### Scenario: Branch depth is coupled to the smoothing constant
- **WHEN** settings load with no fusion setting supplied
- **THEN** the branch depth is of the same order as the smoothing constant
- **AND** it is a single value shared by every fused list

#### Scenario: The settings can be overridden by environment
- **GIVEN** the fusion settings are set to values other than their defaults
- **WHEN** settings load
- **THEN** those values are used
- **AND** the retrieval endpoint keeps answering with the same response shape

#### Scenario: Canonical OpenAPI settings pin the fusion settings
- **WHEN** `canonical_openapi_settings` is built
- **THEN** every fusion setting holds its default
- **AND** no process environment value leaks into the committed OpenAPI snapshot
- **AND** `ai-service/openapi.json` is unchanged by this change

### Requirement: Health detects a configured embedding model that disagrees with the index

The `jbg-ai` service SHALL compare the configured embedding model against the model recorded on the rows of the vector index, and report a mismatch state when they differ. Querying with a model other than the one that produced the indexed vectors compares two different vector spaces and returns meaningless results with no error, so this condition MUST be surfaced explicitly rather than inferred.

The comparison MUST use the model already persisted per row by the indexer; it MUST NOT require new schema.

#### Scenario: Matching model reports a healthy index

- **GIVEN** the vector index was populated with a given embedding model
- **AND** the service is configured with that same model
- **WHEN** a client calls `GET /health`
- **THEN** the index state is reported as consistent
- **AND** the reported index model equals the configured model

#### Scenario: Mismatched model is reported explicitly

- **GIVEN** the vector index was populated with one embedding model
- **AND** the service is configured with a different embedding model
- **WHEN** a client calls `GET /health`
- **THEN** the index state is reported as a model mismatch
- **AND** the body names both the indexed model and the configured model
- **AND** the overall status indicates degradation

#### Scenario: An empty index is not reported as a mismatch

- **GIVEN** the vector index contains no documents
- **WHEN** a client calls `GET /health`
- **THEN** the reported document count is zero
- **AND** the index state is not reported as a model mismatch
