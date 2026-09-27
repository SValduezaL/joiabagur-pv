## ADDED Requirements

### Requirement: The shop activity feed states every point of sale in one complete reading

The system SHALL expose `GET /api/ai/index-feed/pos-shops` as the only HTTP read path for point-of-sale activity, authenticated only by `X-Index-Feed-Key` exactly as the other two feeds are. The response MUST carry one item per point of sale the business holds, each stating its identifier and whether it is active, and MUST be a **complete reading**: it MUST NOT paginate, MUST NOT accept or emit a keyset cursor, and MUST NOT honour a `pageSize` parameter. The reading MUST declare the instant it was taken.

A complete reading is the requirement and not a simplification. A cursored feed can only ever say what changed, so a point of sale **removed** from the business emits no item at all and would survive in the consumer's projection for ever — which is the precise failure mode that forbids carrying this datum on the availability feed. Only a feed that states the whole set lets a consumer retire what is no longer in it.

It is a route of its own rather than a widening of `GET /api/ai/index-feed/pos-availability`, and the reason is mechanical rather than aesthetic. That feed is incremental by keyset over the watermark of the inventory row, computed as the greater of the row's two timestamps; **a point of sale changing its activity touches no inventory row**, so the watermark does not move, the incremental pass re-emits nothing, and any activity flag carried there would be frozen at the value it held when the row was last written. Its aggregate hash cannot see the change either, being a digest of `(pointOfSaleId, productId)` pairs. The two feeds also differ in cardinality by three orders of magnitude, so the page size that makes one correct makes the other absurd.

An inactive point of sale MUST be present in the reading and reported as inactive, never omitted. Omitting it would make *closed* and *deleted* indistinguishable on the wire, and those two require opposite treatment from the consumer: the first keeps its row and stops counting, the second loses its row.

This requirement MUST NOT alter `GET /api/ai/index-feed/pos-availability` in any respect — not its keyset cursor, not its page size of two hundred, not its aggregate hash, and not the shape of its items.

#### Scenario: The feed states every point of sale in a single reading

- **GIVEN** a business holding twelve points of sale
- **WHEN** a client calls `GET /api/ai/index-feed/pos-shops` with the feed key
- **THEN** the response carries twelve items
- **AND** each item states the point-of-sale identifier and whether it is active
- **AND** the response declares no cursor and reports no further pages

#### Scenario: An inactive point of sale is reported rather than omitted

- **GIVEN** one of the points of sale is marked inactive in the business schema
- **WHEN** the feed is read
- **THEN** that point of sale appears in the response
- **AND** it is reported as inactive

#### Scenario: A page size parameter is ignored

- **GIVEN** a caller that supplies a `pageSize` query parameter
- **WHEN** the feed is read
- **THEN** the complete set of points of sale is returned regardless of the value supplied

#### Scenario: The shop feed authenticates only with the index-feed key

- **WHEN** `GET /api/ai/index-feed/pos-shops` is called without the `X-Index-Feed-Key` header
- **THEN** the request is rejected as unauthorised
- **AND** a user bearer token does not open the route

#### Scenario: The availability feed is untouched by this addition

- **GIVEN** the shop activity feed exists
- **WHEN** `GET /api/ai/index-feed/pos-availability` is read
- **THEN** its keyset cursor behaves as it did before
- **AND** its page size is still two hundred
- **AND** its aggregate hash is computed over the same set of assignment pairs
