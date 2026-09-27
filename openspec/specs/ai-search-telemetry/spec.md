# ai-search-telemetry Specification

## Purpose
Recording of the query-to-selection cycle of assisted search, so the adoption and retrieval-quality KPIs can be computed from the database rather than inferred. Covers the event model and its two-write lifecycle, the split of responsibility that has the server record the search it just served and the browser report only the selection, the projection and capping of the stored result list, server-side derivation of the selected rank, the distinction between the assisted path and the degraded lexical one, the grouping of the queries of a search episode, attribution of a sale to the search that originated it, authorization by ownership of the event with no administrator exception, the guarantee that a telemetry failure never propagates to a search or a sale, confidentiality of the operator's query text in logs, and the schema assertions that hold the properties which fail without raising an error.
## Requirements
### Requirement: Assisted searches are recorded by the server

The backend SHALL persist one search event per executed assisted search. The event MUST record the query text, the effective filters sent to retrieval, the result list as displayed, the number of displayed results, the origin of those results, the correlation trace identifier, the retrieval duration, the total handling duration, the episode identifier, and the point of sale and user the search was served for.

The recording operation MUST be an internal application-layer service, not an HTTP endpoint: every field above is known only to the server, so a client reporting them would be reporting values it cannot observe.

The user identifier and point-of-sale identifier MUST come from an already validated call scope and MUST NOT be accepted as loose identifiers. The scope type MUST be the one whose single construction path requires a concrete point of sale, so a search event cannot exist for a point of sale the user has no access to.

Timestamps and durations MUST be captured while the search is being served, even when persistence is deferred, so that a delayed write does not shift the recorded instant.

#### Scenario: A served search is persisted with the server-known fields
- **WHEN** the recording service is invoked with a validated scope, a query, the effective filters, the displayed result list, the result origin, a trace identifier and both durations
- **THEN** a row is persisted carrying all of them
- **AND** the creation timestamp is the instant the search was served
- **AND** the operation returns the identifier of the persisted event

#### Scenario: The point-of-sale scope cannot be bypassed
- **WHEN** code attempts to record a search
- **THEN** the only available signature requires a validated call scope
- **AND** there is no overload accepting a bare point-of-sale identifier

### Requirement: Degraded searches are recorded and distinguishable

The system SHALL record searches that were not served by the AI service with the same completeness as assisted searches, and MUST mark their origin so every path can be separated in analysis.

Three such paths exist beside the semantic assisted one and MUST NOT share an origin value. The first is the degraded path, used when the AI service was consulted and could not answer. The second is the disabled path, used when assisted search is switched off for the point of sale and the AI service was therefore never consulted at all. Recording the second as the first would corrupt the very population the origin exists to isolate: a period with assisted search switched off would read as a period of repeated AI failures. The third is the generative path, used when the operator asked for an assisted answer to a free-text query and the AI service served it with a routing decision, a corpus consultation and prose. Recording the third as the semantic assisted one would make the comparison between a search that costs one embedding and a search that costs an embedding plus a classifier plus a corpus plus a generation impossible to draw from the table, which is the comparison this value exists to enable.

The retrieval duration MUST measure obtaining the candidate list regardless of its source, so all origins remain comparable to each other.

The origin MUST be persisted as an enumeration with explicit stable values, and its mapping MUST be documented, because the table is queried by hand. Adding a value MUST NOT change the meaning of the values already stored.

The query text of a free-text query served by the generative path MUST be persisted exactly as the semantic path persists it, inheriting and declaring the same retention limitation; the customer's question asked about one piece on the sale card MUST NOT be persisted, because it is of another nature.

#### Scenario: A degraded search is recorded with its own origin
- **WHEN** a search is served by the lexical searcher because the AI service was unavailable
- **THEN** the persisted event carries the lexical-fallback origin
- **AND** the retrieval duration measures the lexical query

#### Scenario: A search with assisted retrieval switched off is recorded as disabled
- **WHEN** a search is served without consulting the AI service because assisted search is switched off for that point of sale
- **THEN** the persisted event carries the disabled origin
- **AND** it does not carry the lexical-fallback origin
- **AND** the retrieval duration measures the query that produced the results

#### Scenario: A generative search is recorded with its own origin
- **WHEN** a free-text query is served by the assisted answer path
- **THEN** the persisted event carries the generative origin
- **AND** it does not carry the assisted origin

#### Scenario: The origins are separable in analysis
- **WHEN** events of the assisted, degraded, disabled and generative origins exist
- **THEN** grouping by origin yields the four populations separately
- **AND** the retrieval duration of all of them is expressed in the same unit and measures the same phase
- **AND** the values previously stored for the assisted, degraded and disabled origins still mean what they meant before

#### Scenario: Adding the third origin needs no schema change
- **WHEN** the persisted origin column is inspected after the third value is introduced
- **THEN** the column type is unchanged
- **AND** no migration was required to store the new value

#### Scenario: Adding the fourth origin needs no schema change either
- **WHEN** the persisted origin column is inspected after the generative value is introduced
- **THEN** the column type is unchanged
- **AND** no migration was required to store the new value

#### Scenario: The two paths of the toggle are comparable from the table
- **GIVEN** events of the assisted and the generative origins for the same query text
- **WHEN** they are grouped by origin
- **THEN** the retrieval duration, the total duration, the filters and the selected rank of each population are readable separately

### Requirement: The stored result list is the displayed one, projected and capped

The stored result list SHALL be the list shown to the operator, in display order, and MUST NOT be the raw candidate set produced by over-retrieval.

Each stored entry MUST carry the product identifier, the SKU, the 1-based rank, the relevance score and the match reasons. It MUST NOT carry attributes reconstructible from the catalog by joining on the product identifier.

The list MUST be stored in a column typed as a queryable JSON document, not as opaque text, and MUST use `camelCase` property names.

The stored list MUST be capped by number of entries and MUST NOT be truncated by byte length, since a byte-truncated JSON document is invalid and unusable for analysis. The cap MUST sit above any plausible displayed page size, so that reaching it indicates a defect rather than normal operation.

The count of results actually displayed MUST be persisted in its own integer column, independently of how many entries were stored.

#### Scenario: The displayed list is stored in rank order
- **WHEN** a search displaying ten results out of thirty retrieved candidates is recorded
- **THEN** the stored list holds the ten displayed entries in display order
- **AND** each entry carries product identifier, SKU, rank, score and match reasons
- **AND** the ranks run from 1 upwards without gaps

#### Scenario: A search with no results is still recorded
- **WHEN** retrieval produces no candidates
- **THEN** the event is persisted with a displayed-result count of zero
- **AND** the result column holds an empty list rather than a null
- **AND** the proportion of searches with no results is computable without parsing the JSON document

#### Scenario: An oversized list is capped by entries and the true count is preserved
- **WHEN** a search is recorded with more displayed results than the storage cap
- **THEN** the stored list holds exactly the cap, in rank order
- **AND** the displayed-result count records the real number displayed, not the number stored
- **AND** the stored document remains valid and queryable

### Requirement: Queries of one episode are groupable

The system SHALL record an episode identifier on every search event, supplied by the client when it opens a search session and reused across every query of that session. When the caller supplies none, the server MUST generate one so the column is never empty.

Recording one row per executed query, grouped by episode, MUST make a reformulated query distinguishable from an abandoned one without any additional column: a query with no selection that has later sibling rows in the same episode is a reformulation, and one without siblings is an abandonment.

#### Scenario: Reformulations of one episode share an identifier
- **WHEN** three queries of the same search session are recorded with the same episode identifier
- **THEN** three rows exist that can be grouped by that identifier
- **AND** at most the last one carries a selection

#### Scenario: Reformulation and abandonment are distinguishable
- **WHEN** an episode contains a query without selection followed by a later query of the same episode
- **THEN** that query is identifiable as a reformulation
- **AND** an episode whose only query carries no selection is identifiable as an abandonment

### Requirement: The operator's selection is recorded through a single endpoint

The system SHALL expose exactly one HTTP endpoint for this capability: recording the selection made on an existing search event, at `POST /api/ai/search-events/{id}/selection`. The endpoint MUST require authentication, MUST accept a body carrying only the selected product identifier, and MUST answer with no content on success.

The selection rank MUST be derived by the server from the stored result list and MUST NOT be accepted from the client, so that the rank measures retrieval quality rather than the order the interface happened to display. The selection instant MUST be stamped by the server on receipt and MUST NOT be a duration computed by the client.

The selection instant MUST be its own column and MUST NOT reuse the entity's audit update timestamp, which any later write would overwrite.

Recording a selection MUST be idempotent in the sense that the last write wins: a repeated call replaces the previous selection without returning a conflict.

#### Scenario: Rank is derived from the stored list
- **WHEN** a selection is recorded naming a product present in the stored result list
- **THEN** the selected product, its 1-based position in that list and the selection instant are persisted
- **AND** the request body carried no rank and no duration

#### Scenario: A selection naming a product absent from the list is still recorded
- **WHEN** a selection names a product that does not appear in the stored result list
- **THEN** the selected product and the selection instant are persisted
- **AND** the rank is left null
- **AND** a warning is logged, because this situation always indicates a defect
- **AND** the event does not read as abandoned

#### Scenario: A repeated selection keeps the last one
- **WHEN** a second selection is recorded on an event that already carries one
- **THEN** the event carries the second product and its corresponding rank
- **AND** the response reports success rather than a conflict

### Requirement: Only the owner of a search event may record its selection

The system SHALL reject any attempt to record a selection on a search event belonging to another user with 403 Forbidden, and MUST leave the event unchanged.

This check MUST NOT grant an exception to the administrator role. Unlike point-of-sale access, which administrators bypass by design elsewhere in the system, a search event is the record of what one specific person did, and allowing another user to complete it would allow corrupting the data without trace.

#### Scenario: Another operator cannot complete the event
- **WHEN** a user attempts to record a selection on a search event owned by a different user
- **THEN** the system answers 403 Forbidden
- **AND** the event is left unchanged

#### Scenario: The administrator role grants no exception
- **WHEN** a user holding the administrator role attempts to record a selection on a search event they do not own
- **THEN** the system answers 403 Forbidden
- **AND** the event is left unchanged

### Requirement: A telemetry failure never propagates to the caller

The search recording operation SHALL absorb any persistence failure, log it at error level, and return an absent event identifier. It MUST NOT throw, so that a caller cannot let a telemetry problem surface as a failed search.

#### Scenario: A failed write does not break the caller
- **WHEN** persisting a search event fails
- **THEN** the recording operation returns without throwing
- **AND** the returned event identifier is absent
- **AND** the failure is logged at error level

### Requirement: Sale attribution is carried by the sale, not by the event

The sales table SHALL carry an optional reference to the search event a sale originated from, and the search event MUST NOT carry a reference to the sale. Attribution belongs to the derived fact so that it can be declared in the same write that creates the sale, rather than by a follow-up call that could be lost between the selection and the till.

The reference MUST be optional, so that sales with no assisted search behind them remain valid, and the proportion of sales carrying one MUST be computable from the sales table alone, without joining the event table.

#### Scenario: A sale can carry its originating search
- **WHEN** a sale is stored with a reference to an existing search event
- **THEN** the sale carries that reference
- **AND** counting the sales that carry one requires no join against the event table

#### Scenario: A sale without an originating search remains valid
- **WHEN** a sale is stored with no search event reference
- **THEN** the sale is stored with no attribution
- **AND** no validation error is raised

### Requirement: Deletion rules are declared, not inherited

Every foreign key introduced by this capability SHALL declare its delete behaviour explicitly rather than relying on the persistence framework's default, because the default for a required relationship is cascading deletion and would make deleting a user or a point of sale destroy the record of how the system was used.

Deleting a search event MUST set the referencing sale's attribution to null, and MUST NOT delete or block the deletion of any sale. Deleting a user, a point of sale or a selected product MUST be restricted rather than cascading into search events.

#### Scenario: Purging telemetry preserves sales
- **WHEN** search events referenced by existing sales are deleted
- **THEN** those sales still exist
- **AND** their attribution is null
- **AND** the deletion is not blocked by the constraint

#### Scenario: Business entities do not cascade into telemetry
- **WHEN** the delete behaviour of the references to user, point of sale and selected product is inspected
- **THEN** none of them is cascading

### Requirement: The query text stays out of production logs

The system SHALL record the operator's query text at debug level only, and MUST NOT emit it in any log event at information level or above, because it is free text that may incidentally carry personal data.

The query text column MUST be bounded to the maximum length declared for the query field in the frozen `ai-service/openapi.json` contract, rather than to an independently chosen limit.

#### Scenario: The query does not rise above debug level
- **WHEN** a search is recorded and its log events are emitted
- **THEN** the query text appears only in debug-level events
- **AND** no event at information level or above contains it

### Requirement: The schema is verified, not assumed

The change SHALL provide schema assertions that verify the properties which fail silently when they are wrong: the JSON column types, the column order of the composite index, the bounded length of the query text column, the nullability of the selection columns, and the delete behaviour of every foreign key.

The change SHALL also provide an assertion that the persistence model and the migration snapshot do not diverge, so that changing a configuration without generating a migration breaks the build.

Both assertions MUST live in shared test helpers rather than inside a single test file, so the remaining planned migrations can reuse them.

#### Scenario: The JSON columns are the queryable type
- **WHEN** the applied schema is inspected in the database catalog
- **THEN** both document columns are of the queryable JSON type and not opaque text

#### Scenario: The composite index orders its columns as intended
- **WHEN** the applied schema is inspected in the database catalog
- **THEN** the composite index lists the point-of-sale column before the timestamp column

#### Scenario: Model and migration cannot drift apart
- **WHEN** a persistence configuration is changed without generating a migration
- **THEN** the drift assertion fails
- **AND** it does so without requiring a database

### Requirement: The capability exposes no read surface

This capability SHALL expose no endpoint that reads search events: no retrieval by identifier, no listing, no aggregation and no metrics endpoint. Analysis of the recorded events is performed with direct SQL, outside the application.

The event entity MUST NOT declare navigation properties towards user, point of sale, product or sale, so that the model offers no reading path either.

#### Scenario: No read route exists
- **WHEN** the routes exposed by this capability are enumerated
- **THEN** the only one is the selection endpoint
- **AND** no route returns search event data

