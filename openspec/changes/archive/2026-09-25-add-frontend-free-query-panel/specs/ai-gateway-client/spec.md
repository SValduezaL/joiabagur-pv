## MODIFIED Requirements

### Requirement: Typed gateway client exposes sale assistance and substitutes

The backend SHALL extend the typed `jbg-ai` client with two operations, added by the change that first calls them: sale assistance against `POST /v1/assist/sale` and substitutes against `POST /v1/retrieval/substitutes`, both serializing and deserializing the frozen contract with `snake_case` property names on the wire.

Both operations MUST require a point-of-sale scope or the scope that covers every point of sale, and MUST reject a catalog-wide scope before any request is issued. Both MUST NOT send `pos_id` in the request body, since the service ignores it and the scope comes from the token. The sale assistance request MUST carry at least one anchor, a product or a query; a request carrying neither MUST NOT be issued. A request carrying a query and no product MUST be issued, because the free-query mode no longer writes the price or stock placeholders and therefore has nothing that needs resolving against a single piece.

The sale assistance request MAY carry catalog-side filters, which MUST be serialized with the same field names the retrieval request uses and MUST be omitted when the caller selected none.

Every value the contract declares as nullable MUST map to a nullable value: the family, its label and the variant label of a member, the clarification question, the prompt version and the product a citation supports. Every citation MUST keep its identifier, document title, section title, document type, claim scope, score and snippet. The substitutes operation MUST report the candidates and `candidates_returned` as received and MUST NOT filter, reorder or truncate them: the window is larger than the page on purpose, and excluding by stock belongs to the hydrating caller.

The completion event of a sale assistance call MUST NOT carry the argument, and the question MUST NOT be emitted above debug level.

#### Scenario: A sale assistance response is mapped in full
- **WHEN** the AI service answers HTTP 200 to a sale assistance request
- **THEN** the client returns the intent, the groups with their members, the argument, the citations, the warnings, the clarification question, the usage, the abstention flag, the prompt version, the trace identifier and the effective point of sale
- **AND** each citation keeps its claim scope

#### Scenario: A free query with no product is issued
- **WHEN** the client is called with a query and no product identifier
- **THEN** the request is issued
- **AND** the body carries the query and no product identifier

#### Scenario: A request with neither anchor is refused
- **WHEN** the client is called with neither a product identifier nor a query
- **THEN** the call fails with an argument error
- **AND** no HTTP request is issued

#### Scenario: Selected filters travel with the request
- **WHEN** the client is called with a query and catalog-side filters
- **THEN** the body carries the filters with the field names the retrieval request uses

#### Scenario: Unselected filters are omitted
- **WHEN** the client is called with no catalog-side filters
- **THEN** the body carries no filters property

#### Scenario: Contract nulls survive mapping
- **WHEN** a returned group has a null family and a member has a null variant label
- **THEN** both properties are null on the mapped object
- **AND** mapping neither throws nor substitutes a default value

#### Scenario: The substitutes window is reported, not truncated
- **WHEN** the service returns more substitutes than the requested page size
- **THEN** the client returns every candidate it received, in the order received
- **AND** `candidates_returned` reports the same count the service reported

#### Scenario: No point of sale travels in the body
- **WHEN** the client serializes a sale assistance or a substitutes request
- **THEN** the payload contains no `pos_id` property
- **AND** the property names on the wire are `snake_case`

#### Scenario: A catalog scope is rejected before any request
- **WHEN** either operation is called with a catalog-wide scope
- **THEN** the call fails with an argument error
- **AND** no HTTP request is issued

### Requirement: Every gateway call carries a real point-of-sale scope

Every call to the gateway SHALL carry a call scope holding the user identifier, the role and, when the route has point-of-sale scope, the point-of-sale identifier. The scope type MUST expose exactly three construction paths and no more: one for point-of-sale scoped routes, which requires a concrete point of sale and MUST reject an empty point-of-sale identifier; one for catalog-wide routes, which carries no point of sale at all; and one for a search that deliberately covers every point of sale, which also carries none. All three MUST reject a blank role. No sentinel value MUST be accepted in place of a point of sale on any path, because from the change that introduces the soft prefilter onward the `pos_id` claim is the retriever's only hard filter, and a wildcard reaching it would be a cross-point-of-sale leak.

The third path is not a relaxation of the first: it is a different scope, and the guarantee it preserves is that an absent claim makes the availability prefilter not apply rather than match everything, and fails closed on any route that requires the claim.

A catalog-wide scope MUST be rejected by any point-of-sale scoped operation of the client, before any request is issued. The every-point-of-sale scope MUST be accepted only by catalog retrieval and by sale assistance, and MUST be rejected by every other point-of-sale operation — the sale card, substitutes and inventory — before any request is issued, because those operate on one shop's stock and have nothing to answer without one. The client MUST NOT perform authorization: the caller is responsible for having validated the user's assignment to that point of sale before constructing a point-of-sale scope, and for having validated that the user may search across every point of sale before constructing that scope.

#### Scenario: Scope requires a concrete point of sale
- **WHEN** code attempts to build a point-of-sale call scope with an empty point-of-sale identifier
- **THEN** construction fails with an argument error
- **AND** no construction path accepts a sentinel value in its place

#### Scenario: Blank role is rejected
- **WHEN** code attempts to build a call scope with a blank role
- **THEN** construction fails with an argument error

#### Scenario: Catalog scope carries no point of sale
- **WHEN** code builds a catalog-wide call scope
- **THEN** the resulting scope exposes no point-of-sale identifier
- **AND** construction succeeds without one

#### Scenario: Catalog scope cannot be used for retrieval
- **WHEN** a retrieval call is attempted with a catalog-wide scope
- **THEN** the call fails before any HTTP request is issued

#### Scenario: The every-point-of-sale scope carries no point of sale either
- **WHEN** code builds the scope that covers every point of sale
- **THEN** the resulting scope exposes no point-of-sale identifier
- **AND** it is distinguishable from a catalog-wide scope

#### Scenario: The every-point-of-sale scope is accepted by retrieval and assistance
- **WHEN** a catalog retrieval or a sale assistance call is made with the every-point-of-sale scope
- **THEN** the request is issued

#### Scenario: The every-point-of-sale scope is refused where one shop is mandatory
- **WHEN** a substitutes or an inventory call is attempted with the every-point-of-sale scope
- **THEN** the call fails with an argument error
- **AND** no HTTP request is issued

#### Scenario: No scope accepts a sentinel point of sale
- **WHEN** every construction path of the scope type is enumerated
- **THEN** there are exactly three
- **AND** none of them accepts a wildcard or placeholder point-of-sale identifier
