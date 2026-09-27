## MODIFIED Requirements

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
