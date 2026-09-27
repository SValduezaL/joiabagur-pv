# vector-retrieval Specification

## Purpose
Vector retriever behind `POST /v1/retrieval/products` when `STUB_MODE` is off: embed query with C11 client (`max_attempts=1`), pgvector cosine `<=>` with SQL distance threshold, over-retrieval after the threshold, body filters that exclude while constraints inferred from the query text only demote, `score` as the normalised fused rank with the cosine distance kept as the vector diagnostic, 200 abstention vs 503 dependency failure, `mode=vector`, `mode=lexical` and fused `mode=hybrid` degrading to the lexical branch when the provider fails, a branch depth distinct from the returned window, candidates additionally scoped in SQL to the point of sale of the token claim as defined by `pos-projection`, stage logs for embed, search, lexical, filters, projection and fuse. Stub C02 remains when `STUB_MODE` is true. Python does not read schema `public`. The OpenAPI snapshot moved once, for the optional `projection_age_seconds` response field.

## Requirements

### Requirement: Real product retrieval replaces the stub when stub mode is off
When `STUB_MODE` is disabled, `POST /v1/retrieval/products` MUST run the vector retrieval pipeline and MUST return a body that validates against the frozen `RetrievalResponse` model. It MUST NOT return HTTP 501 naming a later change and MUST NOT return the C02 fixture cycle. When `STUB_MODE` is enabled, the existing C02 stub MUST remain the handler so committed contract tests stay green. `POST /v1/retrieval/substitutes` MUST NOT return 501 when stubs are off either; its behaviour is owned by `substitutes-retrieval`. The OpenAPI snapshot MUST NOT be regenerated. The products handler MUST be asynchronous.

#### Scenario: Stub mode keeps the C02 fixtures
- **GIVEN** `STUB_MODE` is enabled
- **WHEN** an authenticated client with `pos_id` calls `POST /v1/retrieval/products` with a valid body
- **THEN** the response is produced by the existing retrieval stub
- **AND** no embedding provider is called
- **AND** no database session is opened

#### Scenario: Real mode is not 501
- **GIVEN** `STUB_MODE` is disabled and retrieval dependencies are available
- **WHEN** an authenticated client with `pos_id` calls `POST /v1/retrieval/products` with a valid body
- **THEN** the response status is 200 or 503 according to index and dependency state
- **AND** the status is not 501 claiming the implementation has not arrived
- **AND** a 200 body validates against `RetrievalResponse`

#### Scenario: No retrieval route is left answering 501
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client with `pos_id` calls `POST /v1/retrieval/substitutes`
- **THEN** the response status is not 501
- **AND** no message claims the implementation is delivered in a later change

#### Scenario: OpenAPI snapshot stays frozen
- **WHEN** `test_openapi_snapshot_is_stable` runs against this change
- **THEN** the live schema equals the committed `ai-service/openapi.json`
- **AND** the snapshot file has not been regenerated

### Requirement: Query embedding uses the C11 client with a single attempt
The real products handler MUST embed the request `query` with `LiteLlmEmbeddingClient` from `indexing/embeddings.py`, constructed with `max_attempts=1`. It MUST NOT edit `indexing/embeddings.py`. It MUST prefer an instance injected on `app.state` (distinct from the indexer client that retries three times), and in production that instance MUST be built once per process rather than once per request, so that the in-memory cache frozen in C11 can ever record a hit. Because a process-lifetime cache keyed by every distinct operator query would otherwise grow without bound inside a memory-capped container, the client MUST be constructed with a cache that has a maximum size; the bounded cache MUST be supplied through the existing constructor seam rather than by editing the frozen module. A missing `JPV_EMBEDDING_API_KEY` with no injected fake MUST produce HTTP 503 naming `JPV_EMBEDDING_API_KEY`. `/health` MUST NOT require the embedding key.

When `mode` is `lexical` the handler MUST NOT call the embedding provider at all. When `mode` is `hybrid` or absent and the provider fails, or returns a vector whose dimension is not 1536, the handler MUST serve the lexical branch alone with HTTP 200 if that branch produced candidates, and MUST respond HTTP 503 if it did not — a 200 with an empty result list would be indistinguishable from a legitimate abstention. When `mode` is `vector` a provider failure MUST produce HTTP 503.

#### Scenario: Retrieval embed client does not retry
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** the retrieval embedding client is constructed
- **THEN** `max_attempts` is 1
- **AND** `indexing/embeddings.py` is unchanged relative to the C11 freeze

#### Scenario: The retrieval embed client is built once per process
- **GIVEN** `STUB_MODE` is disabled and no fake is injected
- **WHEN** two retrieval requests are served
- **THEN** both use the same embedding client instance
- **AND** its cache has a maximum size

#### Scenario: Missing embedding key is 503
- **GIVEN** `STUB_MODE` is disabled
- **AND** `JPV_EMBEDDING_API_KEY` is absent
- **AND** no retrieval embed fake is injected
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** the response status is 503
- **AND** the detail names `JPV_EMBEDDING_API_KEY`
- **AND** `GET /health` remains HTTP 200

#### Scenario: A provider failure degrades to the lexical branch
- **GIVEN** `STUB_MODE` is disabled and the embedding port raises a non-recoverable error
- **AND** the lexical branch produces candidates for the query
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `mode` absent or `hybrid`
- **THEN** the response status is 200
- **AND** no returned candidate reports the vector branch among its match reasons
- **AND** `low_confidence` is false, because only one branch ran and there was no disagreement to report

#### Scenario: A provider failure with nothing lexical to serve is 503
- **GIVEN** `STUB_MODE` is disabled and the embedding port raises a non-recoverable error
- **AND** the lexical branch produces no candidates for the query
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** the response status is 503
- **AND** the body is not a `RetrievalResponse` with `low_confidence`

#### Scenario: Lexical mode never calls the provider
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `mode=lexical`
- **THEN** no embedding provider call is made
- **AND** the response status is 200 or 503 according to database state

### Requirement: Search uses cosine distance with a SQL threshold and model compatibility
The vector branch MUST use the pgvector cosine operator `<=>` aligned with the HNSW `vector_cosine_ops` index. It MUST NOT use L2. Rows MUST be excluded unless `embedding IS NOT NULL`, `is_active IS TRUE`, and the stored embedding is compatible with the live client's `model_version_key` (`{model}:1536`): `embedding_version` starts with that key or `embedding_model` equals the live `model_id`. Compatible rows whose cosine distance is greater than `JPV_RETRIEVAL_DISTANCE_THRESHOLD` MUST be excluded in SQL. The default threshold MUST be 0.65. The threshold MUST NOT be relaxed when few rows remain. Python MUST NOT read schema `public`.

The threshold is a floor and not a discriminator: measured against this corpus it admits essentially every document for an ordinary query and admits none for nonsense input, so the branch depth is what actually bounds the vector list. That MUST be declared rather than presented as an abstention mechanism, and recalibrating the threshold — which would require a per-query quantile rather than a constant — is out of scope here.

`score` MUST NOT be the mapped cosine distance when more than one branch contributed. It MUST be the fused rank score normalised so that the first result scores 1.0, staying within `[0, 1]` and monotonically decreasing with the returned order. The mapped cosine distance MUST instead be reported as the vector diagnostic of the candidates the vector branch produced. Because this changes the meaning of a value the .NET side persists as telemetry, the change MUST be declared in the service README: scores recorded before and after are not comparable.

#### Scenario: Results are ordered by fused relevance
- **GIVEN** `STUB_MODE` is disabled and both branches produce candidates
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** `results` are ordered by non-increasing `score`
- **AND** the first result has `score` 1.0
- **AND** each `score` is inside `[0, 1]`
- **AND** each item's `match_reasons` reports the branches that actually produced it

#### Scenario: The vector diagnostic keeps the distance
- **GIVEN** `STUB_MODE` is disabled and a candidate was produced by the vector branch
- **WHEN** the response is inspected
- **THEN** its `debug.vector_score` equals `clamp(1 − cosine_distance, 0, 1)`

#### Scenario: Distance above the threshold is excluded from the vector list
- **GIVEN** `STUB_MODE` is disabled and the index has compatible embeddings
- **AND** every cosine distance to the query embedding is greater than the configured threshold
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `mode=vector`
- **THEN** the response status is 200
- **AND** `results` is empty
- **AND** `candidates_returned` is 0
- **AND** `low_confidence` is true
- **AND** the threshold is not raised for a second attempt

#### Scenario: A single-branch mode that returns results is not low confidence
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `mode=vector` or `mode=lexical`
- **AND** at least one result is returned
- **THEN** `low_confidence` is false
- **AND** it is not true merely because a second branch did not run

#### Scenario: Incompatible embeddings do not count as abstention
- **GIVEN** `STUB_MODE` is disabled
- **AND** the count of rows compatible with the live `model_version_key` is 0
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** the response status is 503
- **AND** the status is not 200 with `low_confidence`

### Requirement: Over-retrieval applies after the distance filter
`top_k` MUST remain the page size the .NET caller wants after hydrating. The retriever MUST return at most `min(top_k × 3, 60)` hits, using the same `over_retrieval_count` helper as the stub, applied to the fused and reordered candidate list. `candidates_returned` MUST equal the length of `results`. `effective_pos_id` MUST be the token claim, not the body `pos_id`. `low_confidence` MUST be false when at least one result is returned and at least one of them was produced by more than one branch. When only one branch ran, `low_confidence` MUST NOT be derived from cross-branch consensus at all — it MUST be true only when no result is returned, which is the meaning it had before the branches existed.

Each branch MUST be truncated at the configured branch depth **before** fusing, and that depth MUST be a separate parameter from the over-retrieval window even when their defaults coincide. The vector branch's depth MUST be applied as a `LIMIT` on the set already filtered by the distance threshold.

The candidate set of every branch MUST additionally be restricted to the point of sale of the token when the soft-prefilter capability applies its scope, as defined by `pos-projection`. That restriction is the only predicate that removes a candidate on availability grounds: stock never removes one. Filtering by the point of sale MUST NOT be implemented by post-filtering an approximate index scan, because an approximate scan that returns fewer rows than requested does so without any visible error; the scoped subset MUST be established before the distance is ranked so the branch depth is honoured.

#### Scenario: Overfetch is capped after fusion
- **GIVEN** `STUB_MODE` is disabled and more than 15 candidates survive fusion
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `top_k = 5`
- **THEN** `results` has length 15
- **AND** `candidates_returned` is 15

#### Scenario: Overfetch does not refill from rows above the threshold
- **GIVEN** `STUB_MODE` is disabled, `mode=vector`, and only 2 compatible rows pass the threshold while many more exist above it
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `top_k = 5`
- **THEN** `results` has length 2
- **AND** `candidates_returned` is 2
- **AND** no row with distance greater than the threshold is present

#### Scenario: Branch depth does not follow the requested page size
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** the same query is served with `top_k = 5` and with `top_k = 20`
- **THEN** the number of candidates each branch contributes to the fusion is the same in both calls
- **AND** only the number of returned candidates differs

#### Scenario: Token pos_id is echoed and body pos_id is ignored
- **GIVEN** `STUB_MODE` is disabled and at least one hit is returned
- **WHEN** an authenticated client calls with token `pos_id = B` and body `pos_id = A`
- **THEN** `effective_pos_id` is B
- **AND** the search SQL scopes candidates to point of sale B and never to the body value

#### Scenario: The scoped branch still returns its full depth
- **GIVEN** `STUB_MODE` is disabled and a point of sale whose assortment is a small fraction of the indexed catalogue
- **WHEN** a retrieval is served with the point-of-sale scope applied
- **THEN** the vector branch returns as many candidates as its depth allows within the scoped subset
- **AND** the count is not silently capped below that depth by an approximate index scan

### Requirement: Body filters restrict the candidate set
When the request carries retrieval filters, the search MUST apply them in SQL. Non-empty `filters.materials` MUST require array overlap (`&&`) with `product_document.materials`. A non-null `filters.category` MUST equal `piece_type`. A non-null `filters.family_id` that parses as a UUID MUST equal `product_document.family_id`. A `family_id` that does not parse as a UUID MUST produce HTTP 422 without changing the frozen request schema. Malformed entries in `filters.exclude_product_ids` MUST be ignored (logged at Debug) and MUST NOT fail the request; well-formed UUIDs MUST be excluded from `results`.

The search MUST NOT **exclude** any candidate by price or by stock. A price constraint inferred from the query text MAY reorder the candidates but MUST NOT remove them, because the price held in the index is a projection of the feed and the .NET side is the authority: a stale figure must never be able to delete a valid product before that authority sees it. Body filters keep excluding because a person selected them.

#### Scenario: The four body predicates are applied
- **GIVEN** `STUB_MODE` is disabled and the index contains rows that both match and miss each filter
- **WHEN** an authenticated client calls with `filters.materials`, `filters.category`, a valid `filters.family_id` and `filters.exclude_product_ids`
- **THEN** every returned row overlaps the requested materials
- **AND** every returned row has `piece_type` equal to `category`
- **AND** every returned row has `family_id` equal to the requested family
- **AND** no excluded `product_id` appears in `results`

#### Scenario: Invalid family_id is 422
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client sends `filters.family_id` that is not a UUID
- **THEN** the response status is 422
- **AND** `ai-service/openapi.json` is unchanged

#### Scenario: Malformed exclusions are ignored
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client sends `filters.exclude_product_ids` containing one well-formed UUID and one malformed string
- **THEN** the well-formed id is absent from `results`
- **AND** the request is not rejected because of the malformed string

#### Scenario: A price constraint from the text never deletes a candidate
- **GIVEN** `STUB_MODE` is disabled and the query text expresses a price ceiling
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** candidates above the ceiling are still present in `results`
- **AND** they are ordered after those within it

### Requirement: Missing database configuration is 503 not abstention
When `STUB_MODE` is disabled, a missing `DATABASE_URL`, a missing `ai` schema, a missing `vector` extension, or a failure to open a session MUST cause `POST /v1/retrieval/products` to respond HTTP 503 with a detail that names the failure. `GET /health` MUST remain HTTP 200. The handler MUST NOT insert into `ai.query_log`.

#### Scenario: Absent DATABASE_URL is 503
- **GIVEN** `STUB_MODE` is disabled and `DATABASE_URL` is unset
- **AND** no search fake is injected
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** the response status is 503
- **AND** the detail names `DATABASE_URL`
- **AND** `GET /health` remains HTTP 200
- **AND** the body is not a successful empty retrieval with `low_confidence`

### Requirement: Stage logs carry trace_id and do not dump vectors
The real pipeline MUST emit structured logs for at least `stage=embed`, `stage=search`, `stage=lexical`, `stage=filters` and `stage=fuse`. All MUST include the request `trace_id` (token claim when present). Embed logs MUST include `latency_ms`, `model` and `cache_hits`. Search logs MUST include `latency_ms`, `distance_min` (null when there are zero hits), `candidates`, `mode`, `threshold` and whether the vector branch itself came back empty. That last field MUST NOT be called `low_confidence`: the search stage runs before the fusion and knows only about its own branch, so sharing the name with the response-level marking puts two opposite values under one field in a single trace — a healthy vector branch whose candidates the lexical one never saw sits inside a response that *is* low confidence. Lexical logs MUST include `latency_ms` and the candidate count of each lexical list. Filter logs MUST include which structural constraints were extracted and how many candidates were demoted. Fusion logs MUST include the size of each fused list, how many candidates appeared in more than one list, and `low_confidence`. The operator query MUST be logged only at Debug. Embedding vectors MUST NOT be logged at Information. `JPV_EMBEDDING_API_KEY` MUST NOT be logged.

#### Scenario: trace_id appears in stage logs
- **GIVEN** `STUB_MODE` is disabled and a token carries `trace_id`
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** structured logs for `stage=embed`, `stage=search`, `stage=lexical`, `stage=filters` and `stage=fuse` include that `trace_id`

#### Scenario: The search stage does not borrow the response-level confidence field
- **GIVEN** the vector branch returns no candidate while the fused response is not marked low confidence
- **WHEN** the stage logs are read
- **THEN** the search entry reports its own branch as empty under a name of its own
- **AND** it does not report `low_confidence`

#### Scenario: The fusion log records branch agreement
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client calls `POST /v1/retrieval/products`
- **THEN** the `stage=fuse` entry reports the size of each fused list
- **AND** it reports how many candidates appeared in more than one list

### Requirement: Retrieval unit tests make no provider or database calls
Tests under `ai-service/tests/retrieval/` MUST inject a fake embedding client and a fake search port (in-memory rows with distance). They MUST NOT open sockets to embedding providers, LLM providers or RDS. Optional pgvector tests MAY exist and MUST be skipped, not failed, when Docker is unreachable. A pytest MUST NOT require 1.200 indexed rows.

#### Scenario: Unit suite stays offline
- **WHEN** the retrieval unit tests run
- **THEN** they use injected fakes rather than LiteLLM or PostgreSQL
- **AND** no socket is opened to an embedding provider, LLM provider or RDS

### Requirement: The vector branch truncates under a total order, so ties do not decide silently
The vector branch orders its candidates by cosine distance and truncates at the configured branch depth, and that ordering MUST be a total order. Distance alone is not one: when two documents share a distance and the truncation boundary falls between them, which one survives is undefined, and PostgreSQL is free to return either.

The ordering MUST therefore carry a final deterministic key after the distance, so that the set surviving truncation is a function of the query and the index alone. The key MUST NOT alter the relative order of candidates whose distances differ.

This is a property the evaluation harness depends on: without it, two runs of the same configuration against the same index can return different candidate sets, and a moved metric cannot be attributed to a change rather than to chance.

#### Scenario: Equal distances resolve the same way on every run
- **GIVEN** two indexed documents whose distance to a query vector is identical
- **AND** the branch depth truncates the candidate list between them
- **WHEN** the same retrieval runs twice against an unchanged index
- **THEN** the same document survives truncation in both runs

#### Scenario: The tiebreak does not reorder candidates that are not tied
- **GIVEN** two candidates with different distances
- **WHEN** the vector branch orders them
- **THEN** the closer one precedes the other, regardless of the deterministic key

#### Scenario: Repeating a retrieval yields the same candidate set
- **GIVEN** `STUB_MODE` is disabled and an unchanged index
- **WHEN** the same query is retrieved twice with the same configuration
- **THEN** the two candidate lists are identical in content and order

### Requirement: A filtered request issues a second, unfiltered vector statement for the abstention probe

The retriever SHALL issue, when and only when the request carries catalog-side filters, a second vector statement identical to the first except that it applies no body filter, and MUST hand its distances to the abstention decision while the served candidates continue to come from the filtered statement.

The two statements MUST be issued sequentially and never concurrently, so that at most one connection of the pool is held at any moment, which is the property the retrieval orchestration already maintains against a pool capped at five.

The probe MUST reuse the query vector already computed for the request and MUST NOT call the embedding provider a second time.

When the request carries no filter the second statement MUST NOT be issued, because the served profile already is the unfiltered one.

The probe MUST NOT alter the served candidates, their scores, their order or the returned window, and MUST NOT be reported as candidates.

Its cost MUST be treated as acceptable on the measured grounds that at this catalogue size a hard filter saves no time, so the extra scan is of the same order as the first and is paid only on the minority of searches that carry a filter.

#### Scenario: A filtered request issues two statements
- **WHEN** a retrieval request carries a piece category filter
- **THEN** two vector statements are issued
- **AND** the second applies no body filter

#### Scenario: An unfiltered request issues one statement
- **WHEN** a retrieval request carries no body filter
- **THEN** exactly one vector statement is issued

#### Scenario: The probe holds no extra connection
- **WHEN** a filtered request is served
- **THEN** the two statements are issued one after the other
- **AND** never at the same time

#### Scenario: The probe costs no provider call
- **WHEN** a filtered request is served
- **THEN** the embedding provider is called exactly once

#### Scenario: The probe never reaches the response
- **GIVEN** a filtered request whose unfiltered probe returns candidates the filter excludes
- **WHEN** the response is served
- **THEN** none of those excluded candidates appears in the results
- **AND** the scores and the order of the served candidates are the ones the filtered statement produced

### Requirement: Stage logs report the probe apart from the served search

The retrieval stage logs SHALL report the unfiltered probe distinguishably from the filtered search — at least whether the probe ran, how many candidates it found and its best distance — so that a reader can tell a query the catalogue cannot answer from a filter that admitted almost nothing.

No embedding vector MUST appear in those entries, and the operator's query text MUST NOT appear either, exactly as the existing stage entries already require.

#### Scenario: The probe is visible in the logs
- **WHEN** a filtered request is served
- **THEN** the stage logs state that the probe ran, its candidate count and its best distance
- **AND** those figures are reported apart from the filtered search's own

#### Scenario: The probe entry carries no vector and no query
- **WHEN** the probe entry is written
- **THEN** it contains no embedding vector
- **AND** it contains no query text
