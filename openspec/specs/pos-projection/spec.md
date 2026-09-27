# pos-projection Specification

## Purpose
Point-of-sale availability projection and the soft prefilter that reads it. `python -m jbg_ai.indexing sync-pos` drains `GET /api/ai/index-feed/pos-availability` into `ai.pos_projection` under its own `pos-availability` checkpoint in `ai.sync_checkpoint`, storing quantity buckets and never exact quantities, the assignment hint, the sales aggregates and the reference instant that produced them, and soft-deleting on an `unassigned` tombstone instead of removing the row. Retrieval then scopes every candidate branch in SQL to the point of sale of the token claim as its only hard filter, demotes zero-stock candidates as a weighted score within the last block of the ordering, ranking below the constraints read from the query text and never removing them, reports `projection_age_seconds` from the checkpoint, answers 503 when the projection holds no assigned row instead of an empty 200, and drops the scope when the projection is staler than the configured ceiling. The sales aggregates this capability stores are read by nothing inside it: `sales_30d` alone may reach the retrieval path of the ranking it feeds, for diagnosis, counted against the reference instant recorded on its own row and consumed by no ordering rule, while `sales_90d` and `last_sale_at` stay persisted and unread. The prefilter and that ceiling travel as parameters of the orchestration call, so the frozen request schema of `POST /v1/retrieval/products` does not move. No route under `/v1`, no EF Core migration, and a single additive Alembic revision adding a nullable `computed_as_of` column. The drain is no longer only a command: an in-process scheduler runs it once when the process starts — started without being awaited, so `GET /health` answers throughout — and again on an interval derived from the staleness ceiling, because every recorded incident of an empty or stale projection was found by somebody bringing an environment up in order to test it, and a host-level cron does not run on a developer machine at all. Every drain takes a non-blocking advisory lock inside the drain itself rather than inside the scheduler, so a scheduled tick and a command run by hand decline instead of interleaving the keyset, and `GET /health` reports when the feed was last drained, whether that exceeds the ceiling, the pages recorded as failed and the points of sale left holding no assortment. Python does not read schema `public` by SQL.

## Requirements

### Requirement: The POS availability feed is drained into ai.pos_projection by a CLI
The indexing package SHALL expose a typed client over the existing POS feed method that parses `kind` `upsert` | `tombstone` and maps camelCase fields onto `point_of_sale_id`, `product_id`, `qty_bucket`, `is_assigned_hint`, `sales_30d`, `sales_90d`, `last_sale_at`, `computed_as_of` and `watermark`. Draining MUST be reachable as `python -m jbg_ai.indexing sync-pos`, accepting `--full` to ignore the checkpoint. The command MUST load the local environment file exactly as the catalog `sync` command does. Upserts MUST be idempotent on `(pos_id, product_id)` and MUST set `refreshed_at`. This capability MUST NOT add a route under `/v1`, MUST NOT open an EF Core migration, and Python MUST NOT read or write schema `public` by SQL. It MUST NOT add any Alembic revision: `ai.pos_projection` and `ai.sync_checkpoint` already carry every column this capability needs.

The prohibition on starting an in-process scheduler or background task is **withdrawn**, and withdrawn with its reasons answered rather than dropped in silence. The three the command's own documentation gave were: that an in-process scheduler would add a background task to a container capped at 512 MiB competing for a pool of five connections; that the frozen contract enumerates the `/v1` surface in a MUST; and that honesty about staleness comes from the reported projection age rather than from a hidden cron.

The first is answered by measurement: an incremental drain fetches nought or one page of at most two hundred items and holds one connection for seconds, once per interval, and the task keeps no state between ticks. The second does not apply to a scheduler at all, only to a route, and this capability still adds none. The third is answered by what happened: the age was reported honestly for twenty days and **reached no screen**, across three separate sessions and two distinct failure modes — a projection left empty, which answers 503 to every retrieval while the deployment looks healthy from outside, and a projection left stale, which silently widens the candidate window. The cron also stops being hidden, because the health report states when the drain last ran.

The only drain recipe that existed before this change lived in prose and was **unrunnable in the topology actually deployed**: it began by changing directory to a host path, while the service ships as a container. That is why it was never installed.

#### Scenario: Draining the POS feed populates the projection
- **GIVEN** a POS availability feed with upsert items and `STUB_MODE` disabled
- **WHEN** `python -m jbg_ai.indexing sync-pos` is run
- **THEN** one row per `(pos_id, product_id)` exists in `ai.pos_projection`
- **AND** running the same command again produces the same rows without duplicating any
- **AND** no route was added under `/v1`

#### Scenario: The projection stores a bucket and never the exact quantity
- **GIVEN** a feed upsert whose `qtyBucket` is `0`, `1-2` or `3+`
- **WHEN** the projection row is written
- **THEN** `qty_bucket` holds that bucket
- **AND** no column of `ai.pos_projection` holds an exact quantity
- **AND** a value outside that vocabulary is rejected by the schema constraint

#### Scenario: No schema change is opened
- **GIVEN** the change is implemented
- **WHEN** the Alembic history and the .NET migrations are inspected
- **THEN** no new Alembic revision exists
- **AND** no EF Core migration exists
- **AND** no table is created, altered or dropped

### Requirement: The POS drain keeps its own keyset checkpoint
The POS drain SHALL persist its cursor in `ai.sync_checkpoint` under `feed` value `pos-availability`, recording `watermark`, `since_id`, `last_incremental_sync_at`, `last_full_sync_at`, `last_aggregate_hash` and `indexed_count`. A run without `--full` MUST resume from that cursor. The catalog checkpoint row MUST NOT be read or written by this drain. Batch failures MUST be recorded in `ai.sync_failure` without aborting the remaining pages.

#### Scenario: A second run resumes instead of restarting
- **GIVEN** a completed POS drain that stored a cursor
- **WHEN** `sync-pos` runs again without `--full`
- **THEN** the request carries the stored keyset cursor
- **AND** the `catalog` checkpoint row is unchanged

#### Scenario: A full run ignores the stored cursor
- **GIVEN** a stored POS cursor
- **WHEN** `sync-pos --full` is run
- **THEN** the first page is requested without cursor query parameters
- **AND** the catalog checkpoint row is still unchanged

### Requirement: The POS drain runs at start-up and on an interval without anyone remembering
The service SHALL drain the POS availability feed automatically, both once when the process starts and repeatedly on a configured interval, reusing the same drain the command line invokes rather than reimplementing the keyset protocol a second time. The start-up drain MUST run a full drain when no checkpoint exists for the feed and an incremental drain when one does. The scheduler MUST NOT block process start-up: it MUST be started without being awaited, so that `GET /health` answers 200 throughout the initial drain.

Draining at start-up is the part that matters, and it is not a convenience. Every recorded incident of a stale or empty projection was found by somebody bringing an environment up in order to test it, so a schedule alone leaves a window open at exactly the moment the system is being measured, and a host-level cron does not run on a developer machine at all. Making start-up imply freshness is the invariant that was missing.

Not blocking is equally load-bearing: the container health probe has a short timeout and the composition chains service start-up on it, so awaiting a full drain of tens of pages would mark the container unhealthy and fail the deployment because of the improvement.

A drain that cannot reach the feed MUST log the failure with its cause, MUST retry with bounded backoff, and MUST NOT prevent the process from starting or make `GET /health` fail. When any page of a drain fails, the failed page count MUST be reported rather than swallowed, inheriting the reading the command line already applies: a page that failed is a page nobody drained, and reporting success would let a partially synchronised projection look complete.

The scheduler SHALL be governed by settings that supply an enable switch and the interval, both defaulting to values that keep the projection inside the staleness ceiling. The default interval MUST be derived from that ceiling rather than chosen, such that several consecutive failed drains can elapse before the guard degrades. Disabling the switch MUST restore exactly the behaviour that existed before this requirement, which is both the ablation and the rollback.

#### Scenario: Starting the service drains an environment that has a checkpoint
- **GIVEN** `ai.sync_checkpoint` holds a cursor for the `pos-availability` feed
- **WHEN** the service starts
- **THEN** an incremental drain runs without anyone requesting it
- **AND** `last_incremental_sync_at` for that feed advances
- **AND** `GET /health` answers 200 throughout

#### Scenario: Starting the service drains a brand new environment in full
- **GIVEN** `ai.sync_checkpoint` holds no row for the `pos-availability` feed
- **WHEN** the service starts
- **THEN** the start-up drain runs in full rather than incrementally
- **AND** `last_full_sync_at` is recorded
- **AND** afterwards no retrieval answers 503 for an empty projection

#### Scenario: The projection stays fresh without intervention
- **GIVEN** the service has been running longer than one configured interval
- **WHEN** the interval elapses
- **THEN** an incremental drain runs
- **AND** the reported projection age stays below the configured staleness ceiling while the feed answers

#### Scenario: A feed that does not answer never prevents start-up
- **GIVEN** the POS availability feed is unreachable
- **WHEN** the service starts and the start-up drain attempts it
- **THEN** the service starts and `GET /health` answers 200
- **AND** the failure is logged with its cause
- **AND** the drain is retried without intervention

#### Scenario: A failed page is reported and not swallowed
- **GIVEN** a drain in which one page fails while later pages succeed
- **WHEN** the drain completes
- **THEN** the failed page count is reported
- **AND** the drain is not presented as a complete success

#### Scenario: Disabling the scheduler restores the previous behaviour
- **GIVEN** the scheduler switch is disabled
- **WHEN** the service starts and runs
- **THEN** no drain is started by the service
- **AND** the command line remains the only way to drain
- **AND** retrieval behaves exactly as it did before this requirement existed

### Requirement: Concurrent drains are refused rather than interleaved
A drain SHALL acquire a non-blocking database-level advisory lock for the POS availability feed before writing anything, and a drain that cannot acquire it MUST decline immediately, log that the lock was held together with its correlation identifier, and write nothing. The lock MUST be taken inside the drain itself rather than inside the scheduler, so that it covers every caller — the scheduler, a second scheduler tick, and the command line run by hand.

Taking the lock inside the drain is the whole point. `ai.sync_checkpoint` holds one row per feed carrying `watermark` and `since_id`, so two drains writing at once interleave that keyset, and a corrupted keyset **does not fail: it skips rows in silence**, which is worse than the staleness this capability set out to fix. A lock that lived in the scheduler would leave the command line uncovered, and the command line run by hand is precisely how every recorded incident was repaired.

The lock MUST be non-blocking rather than queueing. A tick that waits for a slower drain builds a queue that grows without bound, so declining is the correct answer and the declined tick is recorded rather than retried immediately.

The lock key MUST be a documented constant rather than a value derived by hashing the feed name, because such a hash is not guaranteed stable across database versions and a silently changed key would disable the lock without failing — which is the exact failure mode the lock exists to prevent.

#### Scenario: A manual drain during a scheduled one declines instead of interleaving
- **GIVEN** a scheduled drain of the POS availability feed is in progress
- **WHEN** an operator runs `python -m jbg_ai.indexing sync-pos` by hand
- **THEN** the manual drain declines immediately without blocking
- **AND** it records that the lock was held, with its correlation identifier
- **AND** the keyset stored in `ai.sync_checkpoint` is not interleaved

#### Scenario: A scheduled drain during a manual one declines too
- **GIVEN** a manual drain is in progress
- **WHEN** the scheduler's interval elapses
- **THEN** the scheduled drain declines and records it
- **AND** it is not queued behind the running drain

#### Scenario: The lock is released so the next drain proceeds
- **GIVEN** a drain that has completed, whether it succeeded or recorded failed pages
- **WHEN** the next drain starts
- **THEN** it acquires the lock and proceeds

### Requirement: An unassigned tombstone soft-deletes the projection row
A POS tombstone with reason `unassigned` MUST set `is_assigned_hint` to false and `qty_bucket` to `0` on the matching row and MUST NOT delete it. When no row exists for that pair, the tombstone MUST insert one in that state. Deleting the row is forbidden because the upsert branch of the feed reports `isAssignedHint` as true for every active assignment, so a delete would make the false value unreachable and would destroy the only record distinguishing a product never carried at a point of sale from one no longer carried there.

#### Scenario: Unassignment keeps the row and flips the hint
- **GIVEN** a projection row for a pair that the feed later reports as a tombstone with reason `unassigned`
- **WHEN** the drain processes that tombstone
- **THEN** the row still exists
- **AND** `is_assigned_hint` is false and `qty_bucket` is `0`
- **AND** `refreshed_at` has advanced

#### Scenario: A tombstone for an unknown pair inserts the soft-deleted row
- **GIVEN** a tombstone for a `(pos_id, product_id)` pair absent from the projection
- **WHEN** the drain processes it
- **THEN** a row is inserted with `is_assigned_hint` false and `qty_bucket` `0`

### Requirement: The point-of-sale scope is the retriever's only hard filter
When the prefilter is enabled and the projection is usable, product retrieval MUST restrict candidates to rows of `ai.pos_projection` whose `pos_id` equals the token's point of sale and whose `is_assigned_hint` is true, applied in SQL to every branch that produces candidates. The scope MUST be taken from the token claim and never from the request body. A `pos_id` claim that does not parse as a UUID MUST cause the request to be rejected and MUST NOT be treated as an absent scope or widened to the whole catalogue. Restricting by assignment mirrors the .NET hydration predicate, which excludes the same rows; no other predicate added by this capability may exclude a candidate.

#### Scenario: Candidates come only from the point of sale's assortment
- **GIVEN** a token whose point of sale carries a strict subset of the indexed catalogue
- **WHEN** a product retrieval is served with the prefilter enabled and a fresh projection
- **THEN** every returned candidate is assigned to that point of sale in the projection
- **AND** products assigned only to other points of sale are absent
- **AND** the over-retrieval window is filled from the scoped subset rather than from the whole catalogue

#### Scenario: A soft-deleted assignment is out of scope
- **GIVEN** a projection row whose `is_assigned_hint` is false
- **WHEN** a retrieval is served for that point of sale
- **THEN** that product is not among the candidates
- **AND** the row remains in the projection

#### Scenario: A malformed point of sale claim never widens the search
- **GIVEN** a valid service token whose `pos_id` claim is not a UUID
- **WHEN** a product retrieval is requested
- **THEN** the request is rejected
- **AND** no retrieval is served over the unscoped catalogue

### Requirement: Availability demotes a candidate and never removes it
A candidate whose projection row reports `qty_bucket` of `0` MUST be ordered after otherwise comparable candidates and MUST remain inside the over-retrieval window. The demotion MUST rank below every block produced by a constraint read from the query text, so a constraint the operator expressed outranks a signal they did not ask for.

**The demotion is applied as a weighted score within the last block of the ordering, not as a component of the lexicographic key.** The weight MUST be configuration and MUST be decided against the golden set under the operational metric and the relevance guardrail that the business-signals ranking capability defines; setting it to zero MUST reproduce the order that the fusion and the typed-constraint blocks alone produce. Because the signal has two states, what that measurement decides is the weight's **sign** and not its magnitude, and the report MUST say so rather than presenting an invariant figure as a fitted one. A candidate whose projection row is absent — because the query ran without a reading scope, or because that point of sale does not carry the product — MUST NOT be demoted, since an absent signal is not evidence of zero stock.

The distinction MUST remain binary between `0` and any other bucket; `1-2` and `3+` MUST NOT be ordered against each other. **That is now a measured conclusion rather than a deferral:** under the operational metric neither non-zero bucket loses gain, so no objective function can order them, and the two business readings of the distinction point in opposite directions. The report MUST publish the distribution of the two non-zero buckets so the decision rests on a figure.

No stock value may reach the response as an exact quantity.

#### Scenario: An out-of-stock product is demoted, not removed
- **GIVEN** a point of sale holding both in-stock and zero-stock assigned products that match a query
- **WHEN** a product retrieval is served
- **THEN** the zero-stock products are still present among the results
- **AND** they are ordered after comparable in-stock products
- **AND** removing them from the response never occurs

#### Scenario: A typed constraint outranks the stock signal
- **GIVEN** a query expressing a price ceiling and results that differ in both price and stock
- **WHEN** the candidates are ordered
- **THEN** candidates within the ceiling precede candidates above it regardless of their stock
- **AND** stock decides the order only between candidates that the typed constraints rank equally

#### Scenario: The two non-zero buckets are not ordered against each other
- **GIVEN** two candidates whose buckets are `1-2` and `3+` and which the other blocks rank equally
- **WHEN** the candidates are ordered
- **THEN** their relative order is the one the fusion produced

#### Scenario: The distribution of the two non-zero buckets is published
- **WHEN** the calibration report completes
- **THEN** it states how many assigned pairs carry `1-2` and how many carry `3+`
- **AND** cites that figure as the reason the distinction stays binary

#### Scenario: The availability weight is configuration and zero restores the previous order
- **WHEN** the availability weight is set to zero
- **THEN** the order is the one the fusion and the typed-constraint blocks alone produce
- **AND** no weight value is written into the ordering module

#### Scenario: An absent projection row does not demote
- **GIVEN** a candidate for which no projection row is read, because the query ran without a reading scope
- **WHEN** the candidates are ordered
- **THEN** that candidate is not demoted on availability grounds
- **AND** the absence is not treated as a bucket of zero

### Requirement: The response reports projection freshness taken from the checkpoint
The retrieval response SHALL carry an optional `projection_age_seconds`, computed as the elapsed time since `ai.sync_checkpoint.last_incremental_sync_at` for `feed` value `pos-availability`. It MUST NOT be derived from `ai.pos_projection.refreshed_at` in any form, because the feed is incremental and an assignment that never changes is never re-emitted, so that column records when an assignment last changed rather than when the projection was last read. The value MUST be read through a short-lived cache so repeated retrievals do not consume the connection pool. Adding the field regenerates `ai-service/openapi.json`.

#### Scenario: Freshness reflects the last synchronisation, not the last change
- **GIVEN** a projection whose rows were last written long ago and whose feed was drained moments ago
- **WHEN** a product retrieval is served
- **THEN** `projection_age_seconds` reports seconds and not the age of the rows
- **AND** the value derives from the `pos-availability` checkpoint

#### Scenario: The regenerated contract is committed
- **GIVEN** the response model carries the new optional field
- **WHEN** the OpenAPI snapshot test runs
- **THEN** it passes against the committed `ai-service/openapi.json`
- **AND** that file contains `projection_age_seconds`

### Requirement: An empty projection fails loudly and a stale one degrades openly
When the prefilter is enabled and the projection holds no assigned row for the token's point of sale, product retrieval MUST respond HTTP 503 with a detail naming the cause, and MUST NOT respond 200 with an empty result list, which would be indistinguishable from a legitimate abstention. When the projection age exceeds the configured ceiling, the point-of-sale scope MUST NOT be applied for that request, the degradation MUST be logged, and the response MUST still report the projection age. `GET /health` MUST remain HTTP 200 in both cases.

#### Scenario: An unsynchronised projection is 503 and not an abstention
- **GIVEN** the prefilter is enabled and `ai.pos_projection` holds no assigned row for the token's point of sale
- **WHEN** a product retrieval is requested
- **THEN** the response status is 503
- **AND** the detail names the projection as the cause
- **AND** the body is not a successful retrieval with an empty result list
- **AND** `GET /health` remains HTTP 200

#### Scenario: A stale projection stops filtering instead of hiding products
- **GIVEN** a projection whose age exceeds the configured ceiling
- **WHEN** a product retrieval is requested
- **THEN** candidates are not restricted by the point of sale for that request
- **AND** the response reports the projection age
- **AND** the degradation is recorded in the logs
- **AND** the page may be shorter than requested rather than omitting a valid product

### Requirement: The projection reports how many points of sale carry no assortment
The service SHALL be able to report the number of points of sale present in `ai.pos_projection` that hold no assigned row, counted within schema `ai` and never by reading schema `public` by SQL.

A point of sale with no assigned row is not a degraded scope but a refused one: the retriever answers 503 for every request carrying that scope rather than abstaining, while the consumer degrades correctly to its lexical path and answers 200, so the environment looks healthy from outside. That failure is per point of sale, is more severe than staleness, and nothing reports it today.

It is counted against the points of sale the projection knows rather than against the active points of sale of the business schema, because the ownership boundary forbids reading that schema by SQL, and reaching it over the feed would widen this capability for a count.

#### Scenario: A point of sale with no assigned row is counted
- **GIVEN** a projection holding rows for several points of sale, one of which has no row with the assignment hint set
- **WHEN** the count is taken
- **THEN** that point of sale is included in the count
- **AND** the points of sale holding assigned rows are not

#### Scenario: The count never reads the business schema
- **GIVEN** the count is computed
- **WHEN** the statements it issues are inspected
- **THEN** every one of them reads only schema `ai`

### Requirement: The prefilter is switchable without moving the frozen request schema
The point-of-sale prefilter SHALL be governed by a setting that supplies only a default, with the effective value travelling as a parameter of the retrieval orchestration call, so configurations can be swept inside one process without restarting. The staleness ceiling SHALL be configurable in the same way. Neither value may be added to the retrieval request schema. With the prefilter disabled, retrieval MUST behave as it did before this capability existed.

#### Scenario: Disabling the prefilter restores the previous behaviour
- **GIVEN** the prefilter is disabled
- **WHEN** a product retrieval is served
- **THEN** candidates are drawn from the whole indexed catalogue
- **AND** no point-of-sale restriction is applied in SQL
- **AND** the request schema of `POST /v1/retrieval/products` is unchanged

#### Scenario: A sweep overrides the default without restarting
- **GIVEN** a caller that passes the prefilter value as a parameter of the orchestration call
- **WHEN** two retrievals are served with opposite values in the same process
- **THEN** each behaves according to its parameter
- **AND** the setting default is not mutated

### Requirement: The scoped pipeline is observable and its cardinality is recorded
The drain and the retrieval MUST emit structured logs carrying `trace_id`. Retrieval MUST log a projection stage reporting the projection age, the number of rows in the point-of-sale scope, and whether the hard filter was applied. The search stage MUST report the candidate count produced under the scope. Vectors MUST NOT be written to logs.

#### Scenario: Every scoped retrieval records what the scope admitted
- **GIVEN** a product retrieval served with the prefilter enabled
- **WHEN** the request completes
- **THEN** a projection stage entry carries `trace_id`, the projection age, the scope size and whether the filter was applied
- **AND** the search stage entry reports the candidates produced under that scope
- **AND** no embedding vector appears in any log entry

### Requirement: Sales aggregates are stored by this capability and read by none of it
The projection SHALL persist `sales_30d`, `sales_90d`, `last_sale_at` and the reference instant reported by the feed. The reference instant MUST be stored **on each row** so a later consumer can tell what clock produced that row's figures. Storing it once per synchronisation instead is insufficient, because the feed is incremental: a pair the feed does not re-emit keeps the figures the run that wrote it computed, so one projection can hold rows counted against different instants.

**`sales_30d` MAY now be read by the ranking that this capability feeds, for diagnosis only.** It may travel on a retrieved candidate and be persisted by an evaluation so its distribution can be published, and **no ordering rule may consume it** — a prohibition the business-signals ranking capability makes structural by keeping the field off the interface its ordering reads. When it is read, it MUST be read against the reference instant recorded on that row and never against the wall clock, so that the same configuration yields the same figure on different days. `sales_90d` and `last_sale_at` remain persisted and unread, and MUST NOT reach the retrieval path at all.

This capability itself MUST NOT use any of these figures to order, filter or score candidates.

#### Scenario: Sales figures are persisted with their reference instant
- **GIVEN** the drain writes a projection row
- **WHEN** the row is inspected
- **THEN** it carries its sales windows, its last sale instant and the reference instant the feed reported

#### Scenario: The unread figures stay unread
- **GIVEN** two assigned candidates identical except for their `sales_90d` and `last_sale_at`
- **WHEN** a product retrieval is served
- **THEN** their relative order is the one produced by fusion and the demotion blocks
- **AND** no ordering rule consumed any sales figure

#### Scenario: The drain does not order anything
- **WHEN** the drain runs
- **THEN** it writes the projection and computes no ranking
- **AND** no ordering decision is taken inside this capability

#### Scenario: The sales window is read against the row's reference instant
- **GIVEN** a projection whose rows carry a reference instant earlier than today
- **WHEN** `sales_30d` is read for diagnosis
- **THEN** the window is counted against that instant
- **AND** the figure is unchanged when the same configuration runs on a later day

#### Scenario: The sales window does not reorder anything
- **GIVEN** two assigned candidates identical except for their `sales_30d`
- **WHEN** a product retrieval is served
- **THEN** their relative order is the one the fusion produced

### Requirement: Retrieval unit tests reach no provider, no public schema and no network
Tests for this capability MUST run offline with injected fakes. They MUST NOT call an embedding provider, an LLM or a remote database, and MUST NOT read schema `public` by SQL. Database-backed tests MUST use an ephemeral PostgreSQL with pgvector and skip when it is unreachable.

#### Scenario: The offline suite makes no external call
- **GIVEN** the retrieval and indexing test suites for this capability
- **WHEN** they run without credentials configured
- **THEN** they pass
- **AND** no provider call, no network call and no query against schema `public` is made
