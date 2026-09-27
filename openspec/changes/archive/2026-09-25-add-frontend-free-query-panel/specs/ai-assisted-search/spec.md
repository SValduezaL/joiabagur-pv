## MODIFIED Requirements

### Requirement: The degraded searcher matches terms and is scoped to the point of sale

The degraded searcher SHALL match any individual term of the operator's query rather than the query string as a whole, because a natural-language query never appears verbatim in a product name and a whole-string match would return an empty list on every degraded search — a silent outage wearing a successful response.

It MUST restrict its results to products with active inventory at the point of sale of the search, so that the degraded path and the assisted path answer about the same shop and remain comparable in analysis. When the search is scoped to every point of sale, it MUST NOT restrict by point of sale at all.

It MUST apply the piece category and the materials the operator selected as exclusions, exactly as the assisted path does, reading them from the enriched profile the transactional catalog holds. A filter the operator selected is a decision, not an inference, and a selected filter that does not filter is the one failure of this capability that misleads without announcing itself: the control stays visibly engaged while the results ignore it.

When a selected filter cannot be applied at all, the response MUST declare it, so that the screen can say so instead of presenting an engaged control that had no effect.

It MUST order results by lexical relevance and MUST NOT use relevance as an exclusion criterion.

It MUST NOT require a new index or a schema change, and MUST NOT modify the behaviour of the pre-existing catalog search used by other screens.

#### Scenario: A natural-language query returns results
- **WHEN** the degraded searcher is given a multi-word natural-language query whose full string matches no product
- **THEN** products matching individual terms are returned
- **AND** the result list is not empty when such products exist at that point of sale

#### Scenario: The degraded searcher is scoped to the point of sale
- **WHEN** a product matches the query but has no active inventory at the point of sale of the search
- **THEN** it does not appear in the degraded results

#### Scenario: A selected piece category excludes on the degraded path
- **WHEN** the operator selects a piece category and the search is served by the degraded searcher
- **THEN** every result belongs to that category
- **AND** no result of another category is returned

#### Scenario: A selected material excludes on the degraded path
- **WHEN** the operator selects a material and the search is served by the degraded searcher
- **THEN** every result carries that material in its enriched profile

#### Scenario: No selection leaves the degraded search unfiltered
- **WHEN** the operator selects neither a material nor a category and the search is served by the degraded searcher
- **THEN** results are drawn from everything the point of sale carries that matches the terms

#### Scenario: A filter that cannot be applied is declared
- **WHEN** a filter the operator selected cannot be applied on the degraded path
- **THEN** the response declares that the filter was not applied

#### Scenario: A degraded search across every point of sale is not restricted
- **WHEN** the search is scoped to every point of sale and is served by the degraded searcher
- **THEN** results are not restricted to the inventory of any single point of sale

#### Scenario: The pre-existing catalog search is untouched
- **WHEN** the pre-existing catalog search endpoint is called
- **THEN** it behaves as it did before this capability existed
