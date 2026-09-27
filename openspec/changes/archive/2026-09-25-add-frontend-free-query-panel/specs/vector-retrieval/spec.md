## ADDED Requirements

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
