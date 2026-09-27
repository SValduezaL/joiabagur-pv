## ADDED Requirements

### Requirement: A result offers the sale card as a secondary action that never interferes with selecting it for sale

The panel SHALL offer, on every result row, a secondary action that opens the sale card for that product scoped to the point of sale the search was scoped to, and that action MUST NOT replace, disable or precede the existing selection for sale.

The action MUST NOT report a selection to the telemetry endpoint, because opening a card is not choosing the piece to sell and counting it as one would inflate the selection rate the search event exists to measure. The selection report stays bound to the act of choosing the product for the sale flow.

The action MUST NOT issue any search, MUST NOT alter the displayed results and MUST NOT end the search episode of the visit.

#### Scenario: Both actions are offered on a result
- **WHEN** a result is displayed
- **THEN** the selection for sale is offered
- **AND** a secondary action opening the sale card for that product is offered

#### Scenario: Opening the card reports no selection
- **WHEN** the operator opens the sale card from a result row
- **THEN** no selection report is issued to the telemetry endpoint

#### Scenario: Opening the card costs no search
- **WHEN** the operator opens the sale card from a result row
- **THEN** no search request is issued
- **AND** the displayed results are unchanged

#### Scenario: Selecting for sale behaves as it did
- **WHEN** the operator selects a result for sale
- **THEN** the selection is reported and the product is handed to the manual sale page exactly as before this capability gained the secondary action
