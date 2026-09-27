## ADDED Requirements

### Requirement: Point-of-sale activity is projected into ai.pos_shop by a drain of its own

The indexing package SHALL drain `GET /api/ai/index-feed/pos-shops` into a table `ai.pos_shop` holding one row per point of sale with its identifier, whether it is active, and when the row was last refreshed. The drain MUST be complete on every run — there is no cursor and no checkpoint — and MUST apply the whole reading in a single transaction: rows present in the reading are inserted or updated, and rows absent from it are removed. This drain MUST NOT embed anything and MUST NOT require an embedding or generation credential. It MUST NOT read or write schema `public` by SQL, and it MUST add exactly one additive Alembic revision and no EF Core migration.

**The single transaction is the requirement, not an implementation habit.** The removal and the insertion are two halves of one statement about the world, and a committed removal without its insertion leaves the table empty — a state that post-deployment verification is specified to treat as a failure. An empty `ai.pos_shop` must only ever mean *nobody has drained it yet*, never *a drain was half applied*.

**Removing rows absent from the reading is what the complete feed is for.** A point of sale deleted from the business emits nothing a cursored feed could carry, so without this rule its row would outlive it and be counted for ever. That is the same defect this capability refuses to accept one table along, and it is why the activity is not carried as a column of `ai.pos_projection`: the availability feed is incremental by keyset over the inventory watermark, an activity change touches no inventory row, and such a column would be stale from the moment a shop opened or closed.

The table records activity and nothing else. It MUST NOT hold the shop's code, name or address: the count this capability serves counts and does not name, and `public` remains the authority on every descriptive attribute of a point of sale.

#### Scenario: Draining the shop feed populates the table

- **GIVEN** a shop activity feed stating twelve points of sale and `STUB_MODE` disabled
- **WHEN** the shop drain runs
- **THEN** `ai.pos_shop` holds one row per point of sale
- **AND** each row records whether that point of sale is active

#### Scenario: A point of sale that leaves the feed leaves the table

- **GIVEN** `ai.pos_shop` holds a row for a point of sale
- **WHEN** a later reading of the feed no longer states that point of sale
- **THEN** the row is removed from `ai.pos_shop`

#### Scenario: A shop that closes is recorded as inactive rather than removed

- **GIVEN** a point of sale that the feed reports as inactive
- **WHEN** the shop drain runs
- **THEN** its row is retained in `ai.pos_shop`
- **AND** the row records the point of sale as inactive

#### Scenario: A failed drain leaves the previous reading intact

- **GIVEN** a drain that fails after removing rows and before writing the new reading
- **WHEN** the table is inspected
- **THEN** it holds the reading the previous successful drain wrote
- **AND** it is not empty

#### Scenario: The shop drain reaches no provider and no business schema

- **GIVEN** the shop drain runs with no embedding or generation credential configured
- **WHEN** the statements it issues are inspected
- **THEN** the drain completes
- **AND** no request is issued to any model provider
- **AND** every statement reads or writes only schema `ai`

### Requirement: The shop drain runs on the same schedule as the availability drain and before it

The scheduled drain SHALL run the shop drain and the availability drain on each pass, at start-up and on the configured interval, under the conditions that already govern the scheduler — the enabling switch, not `STUB_MODE`, and a configured feed. The shop drain MUST run **before** the availability drain within a pass. Neither drain may block process start-up, and a failure of either MUST NOT prevent the other from being attempted nor raise out of the scheduled task.

**The order is a correctness rule and not a preference.** The count this capability reports crosses both tables. With the shops drained first, the only transient state is *shops known, assortment not yet written*, which the count correctly reports as points of sale lacking an assortment — a true statement for as long as it lasts. With the order reversed the transient state is *assortment written, no shop known*, in which the count has nothing to count against and reports an environment as complete while it is not. One order produces a truthful alarm that clears itself; the other produces a silent pass.

#### Scenario: Both drains run at start-up in order

- **GIVEN** a service starting with the scheduler enabled and a configured feed
- **WHEN** the start-up pass runs
- **THEN** the shop drain runs before the availability drain
- **AND** `GET /health` answers throughout

#### Scenario: A failing shop drain does not stop the availability drain

- **GIVEN** the shop feed is unreachable
- **WHEN** a scheduled pass runs
- **THEN** the failure is logged
- **AND** the availability drain is still attempted
- **AND** no exception escapes the scheduled task

#### Scenario: The scheduler stays off under stub mode

- **GIVEN** `STUB_MODE` is enabled
- **WHEN** the service starts
- **THEN** neither drain is scheduled

## MODIFIED Requirements

### Requirement: The projection reports how many points of sale carry no assortment

The service SHALL be able to report the number of **active** points of sale that hold no assigned row in `ai.pos_projection`, counted within schema `ai` and never by reading schema `public` by SQL, together with the number of active points of sale it knows of. The count MUST be taken with the points of sale on the left of the relation — every active row of `ai.pos_shop` for which no assigned row exists in `ai.pos_projection` — and MUST NOT be derived as the difference between two counts taken over the projection alone. When `ai.pos_shop` holds no row the count MUST be reported as unknown rather than as zero.

A point of sale with no assigned row is not a degraded scope but a refused one: the retriever answers 503 for every request carrying that scope rather than abstaining, while the consumer degrades correctly to its lexical path and answers 200, so the environment looks healthy from outside. That failure is per point of sale and is more severe than staleness.

**Counting only the active ones is a correction and it has a cost already paid.** Until this change the count was taken over whatever the projection held, with no notion of whether a point of sale was still trading, so a shop closed on purpose was indistinguishable from a shop whose assortment had never arrived. That is not hypothetical: it failed a healthy deployment of the demonstration environment on 2026-09-27, over a single point of sale declared inactive since 2025-09-30 and holding its whole assortment correctly retired. The earlier reasoning that reaching the business schema over the feed would widen this capability for a count is **withdrawn**: the count was wrong, being wrong reached both a deployment log and an administrator's screen, and the boundary this capability exists to protect is untouched by the correction — the activity enters schema `ai` through the feed, and no statement here reads `public`.

**The direction of the relation is what makes the count complete.** A filter applied over the projection can only speak of points of sale that already appear in it, so an active point of sale absent from the projection altogether — the worst of the two cases, refusing every scoped retrieval and never having been counted — stays invisible. With the points of sale on the left, absence and de-assignment fall into the same number.

**Unknown is not zero.** With no shop row drained yet, zero would assert that no active point of sale lacks an assortment, which is a claim the service is in no position to make; the count says it does not know, and the accompanying number of known active points of sale is what lets a consumer tell the two apart.

#### Scenario: An active point of sale with no assigned row is counted

- **GIVEN** a projection holding rows for several active points of sale, one of which has no row with the assignment hint set
- **WHEN** the count is taken
- **THEN** that point of sale is included in the count
- **AND** the points of sale holding assigned rows are not

#### Scenario: An inactive point of sale with no assigned row is not counted

- **GIVEN** a point of sale recorded as inactive whose projection rows all carry the assignment hint unset
- **WHEN** the count is taken
- **THEN** that point of sale is not included in the count
- **AND** it is not included in the number of active points of sale reported

#### Scenario: An active point of sale absent from the projection is counted

- **GIVEN** an active point of sale that holds no row at all in `ai.pos_projection`
- **WHEN** the count is taken
- **THEN** that point of sale is included in the count

#### Scenario: With no shop known the count is unknown rather than zero

- **GIVEN** `ai.pos_shop` holds no row
- **WHEN** the count is taken
- **THEN** the number of active points of sale is reported as zero
- **AND** the number holding no assortment is reported as unknown

#### Scenario: The count never reads the business schema

- **GIVEN** the count is computed
- **WHEN** the statements it issues are inspected
- **THEN** every one of them reads only schema `ai`
