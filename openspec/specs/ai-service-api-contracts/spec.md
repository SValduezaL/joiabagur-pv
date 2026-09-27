# ai-service-api-contracts Specification

## Purpose
Frozen `/v1` endpoint surface of `jbg-ai`: explicit Pydantic request/response models for retrieval, sale assistance, inventory, enrichment, assisted family grouping, the audit of persisted families and index sync with a keyset cursor, deterministic stub responses with no external I/O, 501 for unimplemented routes when stubs are off, a development-only evaluations route, and a versioned OpenAPI snapshot that detects contract drift.
## Requirements
### Requirement: Frozen `/v1` endpoint surface
The `jbg-ai` service SHALL expose the following internal endpoints under `/v1`, each backed by explicit Pydantic request and response models: `POST /v1/retrieval/products`, `POST /v1/retrieval/substitutes`, `POST /v1/assist/sale`, `POST /v1/inventory/propose`, `POST /v1/enrich/products`, `POST /v1/families/suggest`, `POST /v1/families/audit`, `POST /v1/index/sync`, `GET /v1/index/status`, and `GET /v1/evals/runs` (development profile only). Every `/v1` endpoint MUST require a valid internal service token. `GET /health` MUST remain public and its contract MUST NOT change with respect to C01. Response bodies MUST validate against the declared response model; the service MUST NOT return undeclared shapes.

`POST /v1/families/suggest` is the ninth route and the first addition to this surface since it was frozen. `POST /v1/families/audit` is the tenth, and it is a separate route rather than an extension of the ninth: the two read disjoint populations — suggestion reads products that belong to no family, the audit reads the families that exist — and they converge differently, since suggestion empties itself as batches are approved while the audit is a standing signal. Folding the audit into the suggestion response would move the committed snapshot just the same, so nothing is saved by it.

Adding a route moves the boundary with the .NET client deliberately: the committed `ai-service/openapi.json` MUST be regenerated in the same change that adds the route, and `test_openapi_snapshot_is_stable` MUST pass against that regenerated snapshot. A route added without regenerating the snapshot MUST fail the build.

#### Scenario: Every frozen route answers with its declared model
- **WHEN** an authenticated client calls any of the ten `/v1` endpoints with a valid request body in stub mode
- **THEN** the response status is 200
- **AND** the body validates against that endpoint's declared response model

#### Scenario: Health contract is unchanged
- **WHEN** a client calls `GET /health` without a token
- **THEN** the response is HTTP 200 with an OK status indicator and the configured service version
- **AND** the shape is the same one C01 published

#### Scenario: The family suggestion route requires the service token
- **WHEN** an unauthenticated client calls `POST /v1/families/suggest`
- **THEN** the request is rejected before any work is done
- **AND** no proposal is computed

#### Scenario: The family audit route requires the service token
- **WHEN** an unauthenticated client calls `POST /v1/families/audit`
- **THEN** the request is rejected before any work is done
- **AND** no similarity is computed

#### Scenario: The regenerated snapshot matches the live schema
- **WHEN** `test_openapi_snapshot_is_stable` runs against the working tree of the change that added the route
- **THEN** the live OpenAPI schema equals the committed `ai-service/openapi.json`
- **AND** that snapshot contains the ten `/v1` paths

### Requirement: Retrieval contract carries materials, family and variant
Retrieval request models MUST accept `query`, `top_k`, `filters` (including `materials` as a list of strings) and `mode`, plus an optional `pos_id` that is accepted for client compatibility and ignored. Each retrieval result MUST expose `product_id`, `sku`, `score`, `match_reasons`, `materials` as a list, `family_id`, `variant_label`, and an optional `debug` object. `family_id` and `variant_label` MUST be nullable and MUST be null when unknown rather than omitted or defaulted to a placeholder value. The retrieval response MUST expose `results`, `candidates_returned`, `low_confidence` and `trace_id`. `POST /v1/retrieval/substitutes` MUST return the same result shape plus `similarity_signals`.

#### Scenario: Retrieval result exposes the v3 contract fields
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with a valid body in stub mode
- **THEN** the response validates against the retrieval response model
- **AND** each result exposes `materials` as a list, plus `family_id` and `variant_label`
- **AND** unknown `family_id` or `variant_label` values are null rather than absent

#### Scenario: Substitutes add similarity signals
- **WHEN** an authenticated client calls `POST /v1/retrieval/substitutes` with a valid body in stub mode
- **THEN** the response uses the retrieval result shape
- **AND** `similarity_signals` is present on the response

### Requirement: Over-retrieval is observable and capped
`top_k` SHALL mean the page size the caller wants **after** hydrating and filtering results on the .NET side, not the number of items the retriever returns. The retrieval stub MUST return `min(top_k × 3, 60)` results and MUST report that same count in `candidates_returned`.

#### Scenario: Over-retrieval multiplies the requested page size
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `top_k = 5` in stub mode
- **THEN** `candidates_returned` is 15
- **AND** `results` has length 15

#### Scenario: Over-retrieval respects the cap of 60
- **WHEN** an authenticated client calls `POST /v1/retrieval/products` with `top_k = 30` in stub mode
- **THEN** `candidates_returned` is 60
- **AND** `results` has length 60

### Requirement: Sale assistance groups results by family
The `POST /v1/assist/sale` request MUST accept a product identifier and a query as independent optional fields, and MUST require at least one of the two; a request carrying neither MUST be rejected as invalid. It MUST also accept the same optional catalog-side filters the retrieval request accepts, defaulting to no filter, so that a caller which omits the field receives the behaviour it received before the field existed. The response MUST expose `intent`, `groups`, `pitch`, `citations`, `warnings`, an optional `clarification_question`, `usage`, `abstained` and `prompt_version`. Each entry in `groups` MUST expose a `family_id` that MAY be null, and a group whose `family_id` is null MUST contain exactly one member. Every member of a group MUST expose `variant_label` and `match_reasons`. Every entry in `warnings` MUST belong to a closed vocabulary declared by the assistance capability. Every entry in `citations` MUST expose `citation_id`, `document_title`, `section_title`, `doc_type`, `claim_scope`, `score` and `snippet`, and MAY expose the `product_id` it supports.

#### Scenario: Assist response groups members under a family
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with a valid body in stub mode
- **THEN** the response includes `groups`
- **AND** each group exposes a `family_id`
- **AND** every group member exposes `variant_label` and `match_reasons`

#### Scenario: A group without a family carries a single member
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** every group whose `family_id` is null contains exactly one member

#### Scenario: The request requires at least one anchor
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with neither a product identifier nor a query
- **THEN** the response is a validation error
- **AND** the error names both fields as the alternatives

#### Scenario: The request accepts catalog-side filters
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with a query and catalog-side filters
- **THEN** the request is accepted
- **AND** the filters carry the same fields the retrieval request declares

#### Scenario: Omitting the filters is the previous behaviour
- **WHEN** an authenticated client calls `POST /v1/assist/sale` without the filters field
- **THEN** the request is accepted
- **AND** no filter is applied

#### Scenario: Citations carry their identifier and their claim scope
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** every returned citation exposes `citation_id`, `document_title`, `section_title`, `doc_type` and `claim_scope`

#### Scenario: The response declares abstention and prompt provenance
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** the response exposes `abstained`
- **AND** it exposes `prompt_version`, which MAY be null

### Requirement: Generated text never contains resolved price or stock
Text generated by `jbg-ai` MUST NOT contain concrete price or stock figures. Where such a figure belongs, the service MUST emit the literal placeholders `{{price}}` and `{{stock}}` unresolved, leaving substitution to the .NET caller, which is the authority on price and stock.

The prohibition MUST hold over the **whole response** and not only over the generated text: no field of any `/v1` response may carry a price or a stock quantity, including the availability bucket the index holds for ranking.

#### Scenario: Pitch keeps placeholders unresolved
- **WHEN** an authenticated client calls `POST /v1/assist/sale` in stub mode
- **THEN** the returned `pitch` contains the literal `{{price}}` and `{{stock}}` placeholders
- **AND** it contains no substituted numeric price or stock value

#### Scenario: No field of the response carries a price or a stock figure
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with stubs disabled
- **THEN** no field of the response carries a price
- **AND** no field carries a stock quantity or an availability bucket

### Requirement: Inventory, enrichment and index contracts are frozen
`POST /v1/inventory/propose` MUST return a prioritized list of proposals. `POST /v1/enrich/products` MUST accept a batch of products and return proposed profiles in which **every proposed value carries both its confidence and its provenance**, stated as `rule` when the value comes from a deterministic normalization and `inferred` when a model produced it. The proposed profile MUST carry `piece_type`, `stone_type` and `size_label` as individually proposed values, and MUST carry commercial tags split into `color_tags`, `style_tags` and `occasion_tags` rather than as a single flat list, matching the columns the vector index already declares. `materials` MUST be returned as a list. The response MUST report the prompt version that produced the batch. `POST /v1/index/sync` MUST accept a keyset cursor (`since` and optional `since_id`) and return upsert counters plus the starting and ending keyset. `GET /v1/index/status` MUST return `drift_count` and `last_full_sync_at`.

Provenance is not decoration: the consuming capability routes a sensitive field to human review when it is inferred and exempts it when it comes from a rule, so a contract without it makes that policy unimplementable.

#### Scenario: Inventory proposals are prioritized
- **WHEN** an authenticated client calls `POST /v1/inventory/propose` with a valid body in stub mode
- **THEN** the response validates against the inventory response model
- **AND** it contains a prioritized list of proposals

#### Scenario: Enrichment returns per-field confidence and provenance
- **WHEN** an authenticated client calls `POST /v1/enrich/products` with a batch of products in stub mode
- **THEN** the response returns one proposed profile per requested product
- **AND** each proposed field carries a confidence value
- **AND** each proposed field states whether its value is `rule` or `inferred`
- **AND** `materials` is returned as a list

#### Scenario: Enrichment returns the sensitive fields the review policy needs
- **WHEN** the same call is made
- **THEN** each proposed profile exposes `piece_type`, `stone_type` and `size_label` as proposed values, each nullable
- **AND** it exposes `color_tags`, `style_tags` and `occasion_tags` as separate lists
- **AND** it exposes no single flat `tags` list

#### Scenario: Enrichment reports the prompt version
- **WHEN** the same call is made
- **THEN** the response reports the version of the prompt that produced the batch

#### Scenario: Stub proposals exercise both provenances
- **WHEN** the enrichment stub answers a batch large enough to cover its fixture cycle
- **THEN** at least one sensitive field is returned as `inferred`
- **AND** at least one sensitive field is returned as `rule`
- **AND** the response remains deterministic for the same request

#### Scenario: Index sync and status expose counters and drift
- **WHEN** an authenticated client calls `POST /v1/index/sync` with a `since` cursor in stub mode
- **THEN** the response returns upsert counters and keyset fields `since` / `since_id` and `cursor` / `cursor_id`
- **WHEN** the same client calls `GET /v1/index/status`
- **THEN** the response returns `drift_count` and `last_full_sync_at`

### Requirement: Family suggestion contract carries members, labels and review flags
`POST /v1/families/suggest` SHALL accept an optional scoping body — a piece type and a maximum number of proposals — and MUST return, for each proposal, the normalized root, the piece type, and the ordered members. Each member MUST carry the product identifier, its SKU, its name, its variant label as a nullable value, and its position. A member the relative embedding veto flagged MUST be marked as such together with its distance, and MUST still be present in the proposal.

The response MUST carry **three** lists, not one: the proposals, the groups a guard rejected together with the reason, and the products the piece-type gate excluded with theirs. A caller must be able to surface both kinds of omission as catalogue quality incidences without inferring them from an absence. Products skipped for already belonging to a family MUST be reported as a count rather than enumerated.

Under stub mode the route MUST return a deterministic fixture that validates against the declared response model, without touching the database.

#### Scenario: A proposal carries its members in order with their labels
- **WHEN** an authenticated client requests suggestions and a family is proposed
- **THEN** the proposal reports the root, the piece type and the ordered members
- **AND** each member carries its product identifier, SKU, name, position and nullable variant label

#### Scenario: A flagged member is reported and retained
- **WHEN** a proposal contains a member the relative veto flagged
- **THEN** that member is present in the members list
- **AND** it is marked for review with its distance

#### Scenario: Rejected groups are reported explicitly
- **WHEN** a candidate group is rejected by the degenerate-root guard
- **THEN** the response lists it with the reason for the rejection
- **AND** it does not appear among the proposals

#### Scenario: Stub mode answers without a database
- **WHEN** the route is called with stub mode enabled
- **THEN** the response is a deterministic fixture that validates against the declared model
- **AND** no database connection is opened

### Requirement: Family audit contract carries flags, candidates and the judgements already made

The contract for `POST /v1/families/audit` SHALL carry, in one response, the members of persisted families that the vectors do not support and the unassigned products nominated as candidates for a family, together with the groups a guard refused and the products a gate excluded, recomputed over the current catalogue state.

Each flagged member MUST carry its product, its family, the margin by which a product of another family beat its worst sibling, and the identity of that product. Each candidate MUST carry its product, the family it is nominated for, the similarity, the family's worst-sibling similarity, the margin between them, the data origin of the product, and the neighbourhood-purity count reported as a ranking signal only.

The request MUST accept the `(product, family)` pairs that already carry a human verdict, so that the service can omit them without holding any judgement of its own. The service MUST NOT persist those pairs, and MUST NOT read the transactional catalogue schema to discover them.

The request MUST accept the veto and nomination margins, falling back to configuration when they are absent, and a cap on the number of candidates returned. Flagged members, refused groups and excluded products MUST NOT be truncated by that cap.

#### Scenario: One call returns both sides of the membership line
- **WHEN** an authenticated client calls `POST /v1/families/audit` in stub mode
- **THEN** the response contains the flagged members and the candidates in the same body
- **AND** each flagged member carries its margin and the product that beat its worst sibling
- **AND** each candidate carries its similarity, the target family's worst-sibling similarity, its data origin and its purity count

#### Scenario: Judged pairs travel in the request and are not stored
- **WHEN** the caller sends a set of `(product, family)` pairs that already carry a verdict
- **THEN** none of those pairs appears among the flagged members or the candidates
- **AND** repeating the call without them reports those pairs again
- **AND** the service holds no record of them between calls

#### Scenario: The candidate cap never truncates a refusal
- **WHEN** the caller caps the number of candidates below the number the audit produced
- **THEN** the candidates are truncated to that cap
- **AND** the flagged members, the refused groups and the excluded products are returned in full

### Requirement: Index sync contract carries a keyset cursor
`POST /v1/index/sync` MUST accept `since` (datetime or null), `since_id` (uuid or null), `full` (boolean, default false) and `batch_size` (integer 1–1000, default 100). `since_id` is the second component of the catalog feed keyset; it MUST NOT be required when `since` is null. The response MUST include `upserted`, `skipped`, `deleted`, `failed`, the starting keyset `since` / `since_id`, and the ending keyset `cursor` / `cursor_id`. `skipped` MUST mean embeddings omitted, not rows ignored. `batch_size` MUST remain in the schema for compatibility and MUST NOT select the feed page size. After this change the committed `ai-service/openapi.json` MUST include these fields and `test_openapi_snapshot_is_stable` MUST pass against that regenerated snapshot. Stub-mode responses MUST populate `since_id` and `cursor_id` (null or a deterministic fixture) so the body still validates.

#### Scenario: Sync request and response expose the keyset
- **GIVEN** the regenerated OpenAPI snapshot
- **WHEN** an authenticated client calls `POST /v1/index/sync` in stub mode with `since` and `since_id`
- **THEN** the response status is 200
- **AND** the body validates against `IndexSyncResponse`
- **AND** the body exposes `since_id` and `cursor_id`

#### Scenario: Snapshot matches the live schema after regeneration
- **WHEN** `test_openapi_snapshot_is_stable` runs against the working tree of this change
- **THEN** the live OpenAPI schema equals the committed `ai-service/openapi.json`
- **AND** that schema includes `since_id` on `IndexSyncRequest` and `cursor_id` on `IndexSyncResponse`

### Requirement: Stub responses are deterministic and perform no external I/O
When `STUB_MODE` is enabled, `/v1` handlers MUST return fixture-based responses and MUST NOT call an LLM provider, an embedding API, or any database. The same request MUST produce the same response, so that the .NET client can build mapping tests against these responses.

#### Scenario: Stub mode makes no external calls
- **WHEN** `STUB_MODE` is enabled and an authenticated client calls any `/v1` endpoint
- **THEN** the response is produced from fixtures
- **AND** no LLM, embedding or database call is made

#### Scenario: Same request yields the same response
- **WHEN** the same valid request is sent twice to a `/v1` endpoint in stub mode
- **THEN** both responses are identical except for correlation values such as `trace_id`

### Requirement: Unimplemented routes return 501 when stubs are disabled
When `STUB_MODE` is disabled and a `/v1` route has no real implementation yet, the service MUST respond with HTTP 501 and a message indicating that the implementation arrives in a later change. It MUST NOT return a fixture, an empty success, or a transient-error status.

#### Scenario: Stubs off without implementation yields 501
- **WHEN** `STUB_MODE` is disabled and an authenticated client calls a `/v1` route whose real logic does not exist yet
- **THEN** the response status is 501
- **AND** the message indicates the implementation is delivered in a later change

### Requirement: The assistance route serves a real implementation with stubs disabled
When `STUB_MODE` is disabled, `POST /v1/assist/sale` MUST serve its real implementation and MUST NOT answer HTTP 501. The generic rule that an unimplemented `/v1` route answers 501 continues to govern the routes that still have no implementation, and `POST /v1/assist/sale` is no longer one of them.

#### Scenario: The assistance route no longer answers 501
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client calls `POST /v1/assist/sale` with a valid body
- **THEN** the response status is not 501

#### Scenario: A route that is still unimplemented keeps answering 501
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client calls a `/v1` route whose real logic still does not exist
- **THEN** the response status is 501

### Requirement: Evaluation endpoint exists only in the development profile
`GET /v1/evals/runs` MUST be mounted only when development endpoints are enabled. Under a production profile the route MUST NOT be registered at all.

Under a development profile it MUST answer HTTP 200 for an authenticated caller with the evaluation runs the harness has persisted, ordered most recent first, each carrying its identifier, its suite, its outcome, its start and end instants and its metrics. It MUST NOT answer 501 when stub mode is disabled: the route has a real implementation, and the placeholder that named a future change no longer applies.

When no run has been persisted, the route MUST answer 200 with an empty list, because "no evaluation has been run here" is a valid answer and is not an error.

The route's declared request and response models MUST NOT change, so the committed OpenAPI snapshot stays byte-for-byte identical.

#### Scenario: Evals route serves persisted runs in the development profile
- **WHEN** the application is built with development endpoints enabled and at least one evaluation run has been persisted
- **AND** an authenticated client calls `GET /v1/evals/runs`
- **THEN** the response status is 200
- **AND** the body contains the persisted runs with their metrics, most recent first

#### Scenario: An empty history is an empty list, not an error
- **WHEN** the application is built with development endpoints enabled and no evaluation run has been persisted
- **AND** an authenticated client calls `GET /v1/evals/runs`
- **THEN** the response status is 200
- **AND** the body contains an empty list of runs

#### Scenario: The route no longer answers 501 with stubs disabled
- **WHEN** `STUB_MODE` is disabled and an authenticated client calls `GET /v1/evals/runs` under a development profile
- **THEN** the response status is 200
- **AND** the response is not a placeholder naming a future change

#### Scenario: Evals route is absent in the production profile
- **WHEN** the application is built with a production profile
- **AND** an authenticated client calls `GET /v1/evals/runs`
- **THEN** the route is not mounted and the request is not served by an evals handler

#### Scenario: The contract snapshot is unchanged
- **WHEN** the OpenAPI snapshot test runs after the route gains its real implementation
- **THEN** the live schema equals the committed snapshot

### Requirement: Versioned OpenAPI snapshot detects contract drift
The repository MUST contain a versioned `ai-service/openapi.json` generated from the running application using the canonical development profile documented in the `ai-service` README. An automated test MUST compare the live schema against that committed file and MUST fail on any difference. Interactive API documentation MUST remain disabled: the published artifact is the snapshot, not a browsable UI.

#### Scenario: Committed snapshot matches the live schema
- **WHEN** `test_openapi_snapshot_is_stable` runs against an unmodified working tree
- **THEN** the live OpenAPI schema equals the committed `ai-service/openapi.json`

#### Scenario: Contract drift breaks the build
- **WHEN** a Pydantic model or a route signature changes and the snapshot is not regenerated
- **THEN** the snapshot test fails

### Requirement: Contract tests run in process without external AI or database
The contract test suite MUST exercise the `/v1` surface with FastAPI `TestClient` (or an equivalent in-process client) and MUST NOT call real LLM providers, embedding APIs, or production RDS.

#### Scenario: Contract suite passes without network access to AI or RDS
- **WHEN** the `ai-service` test suite runs with the required environment provided in process
- **THEN** the `/v1` contract tests pass
- **AND** no call is made to an LLM provider, embedding API or production database

### Requirement: The snapshot moves by pure addition, verified leaf by leaf

The regeneration of the committed OpenAPI snapshot for this change SHALL be verified to be a pure addition: no leaf of the previous snapshot MUST be removed and no leaf MUST change type, and the verification MUST be performed leaf by leaf against the previous snapshot rather than asserted.

The stub fixture of the assistance route MUST be kept consistent with the moved contract, and in particular MUST NOT emit the price or stock placeholders in the free-query mode, because a fixture exempt from a rule the real path enforces is the one response a client learns the wrong shape from.

#### Scenario: The snapshot movement is a pure addition
- **WHEN** the regenerated snapshot is compared with the previous one
- **THEN** no leaf was removed
- **AND** no leaf changed type
- **AND** the comparison is reported leaf by leaf

#### Scenario: The stub does not emit placeholders in the free-query mode
- **WHEN** the stub serves a request carrying a query and no product identifier
- **THEN** the returned argument contains neither the price placeholder nor the stock placeholder
