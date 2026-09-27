## MODIFIED Requirements

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

## ADDED Requirements

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
