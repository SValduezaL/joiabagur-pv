# index-feed Specification

## Purpose
HTTP pull surface for catalog and POS indexation: `GET /api/ai/index-feed/catalog` (page 50) and `GET /api/ai/index-feed/pos-availability` (page 200), authenticated only by `X-Index-Feed-Key`. Keyset cursor on watermark, upsert and tombstone items, `price-band/v1` as a pure function, and an aggregate SHA-256 of the global indexable set. Python does not read `public` by SQL; this feed is the only read path until C13 pulls. No EF/Alembic migration, no HTTP push to `/v1/index/sync`, no AutoBulk execution.

## Requirements

### Requirement: Catalog feed pages by keyset watermark at fifty items
The system SHALL expose `GET /api/ai/index-feed/catalog` as the only HTTP read path for catalog indexation. A page MUST contain at most 50 items. The client MUST NOT choose the page size: a `pageSize` query parameter SHALL be ignored. When `since` and `sinceId` are absent the first page of a full sync is returned. When they are present the page MUST contain only rows whose watermark is strictly after the cursor, or whose watermark equals `since` and whose product identifier is greater than `sinceId`. The watermark of a product MUST be the greatest of `Product.UpdatedAt`, the associated profile's `UpdatedAt` when a profile exists, and the current family's `UpdatedAt` when the product is a current member. `hasMore` and `nextCursor` (`since`, `sinceId`) MUST allow a caller to exhaust the feed; `nextCursor` MUST be null on the last page. `PaginationConstants.MaxPageSize` MUST NOT be used on this route.

#### Scenario: The since cursor returns only rows whose watermark changed
- **GIVEN** approved profiles and a cursor `(since, sinceId)` from a previous page
- **WHEN** `GET /api/ai/index-feed/catalog` is called with that cursor and a valid API key
- **THEN** the page contains at most 50 items
- **AND** every item has a watermark after the cursor in keyset order, so rows that share an instant are neither skipped nor duplicated
- **AND** `hasMore` and `nextCursor` allow the caller to continue until the feed is exhausted

#### Scenario: Catalog page size is server-fixed
- **GIVEN** more than 50 catalog rows whose watermark is in range
- **WHEN** the catalog feed is requested with or without a `pageSize` query parameter
- **THEN** the page contains at most 50 items
- **AND** `pageSize` in the response is 50

### Requirement: Catalog items are upserts or tombstones and never-approved products are absent
A catalog row MUST be indexable when the product is active and its profile `ReviewStatus` is `Approved`. `ReviewOrigin` MUST NOT participate in that predicate. An indexable row in the cursor window MUST be emitted as `kind = upsert`. A row in the cursor window that has a profile and is no longer indexable MUST be emitted as `kind = tombstone` with `reason` `deactivated` when the product is inactive, otherwise `unapproved`. A product that has no profile MUST NOT appear as upsert or tombstone. A tombstone body MUST be `{ kind, productId, reason, at }` and MUST NOT include source-text fields.

#### Scenario: A deactivated product emits a tombstone
- **GIVEN** an indexable product that is set to `IsActive = false`
- **WHEN** the catalog feed is queried with `since` earlier than that change
- **THEN** the item is emitted with `kind = tombstone` and `reason = deactivated`
- **AND** it is not emitted as an upsert

#### Scenario: An unapproved profile is not upserted and leaving approved is a tombstone
- **GIVEN** a product whose profile is `Pending` or `Rejected` and was never `Approved`
- **WHEN** the catalog feed is requested
- **THEN** the product does not appear as an upsert
- **AND** when a profile that was `Approved` becomes not approved, the item is a tombstone with `reason = unapproved`

#### Scenario: A product with no profile does not appear
- **GIVEN** a product that has no `ProductAiProfile` row
- **AND** its `UpdatedAt` is inside the cursor window
- **WHEN** the catalog feed is requested
- **THEN** the product is absent from both upserts and tombstones

### Requirement: Catalog upsert is a superset of source text without provenance
A catalog upsert MUST include the fields of `ProductSourceText` (`sku`, `name`, `description`, `collectionName`, `pieceType`, `materials`, `stoneType`, `sizeLabel`, `familyName`, `variantLabel`, `colorTags`, `styleTags`, `occasionTags`) plus `productId`, `familyId` (uuid or null), `price`, `priceBand`, `isActive`, `watermark` and `kind`. Materials and tags MUST be JSON arrays, not the persisted `*Json` strings. `collectionName` MUST come from `Collection.Name`. The payload MUST NOT contain `dataOrigin`, `textProvenance`, `source`, `confidence` or the profile `SourceHash`. JSON property names MUST be camelCase.

#### Scenario: Upsert maps source-text fields and identifiers
- **GIVEN** an indexable product with a collection, an approved profile and a family membership
- **WHEN** the catalog feed emits that product as an upsert
- **THEN** the item includes `sku`, `name`, `productId`, `familyId`, `price`, `priceBand`, `isActive` and `watermark`
- **AND** `materials` and tag fields are arrays
- **AND** `collectionName` equals the collection's name

#### Scenario: Provenance and origin stay out of the catalog JSON
- **GIVEN** an indexable product whose profile carries `source`, confidence and a profile `SourceHash`
- **WHEN** the catalog feed emits that product
- **THEN** the JSON does not contain `dataOrigin`, `textProvenance`, `source`, `confidence` or the profile `SourceHash`

### Requirement: Price band is the pure function price-band/v1
The system SHALL classify `Product.Price` with a pure function versioned as `price-band/v1`, with no HTTP or EF dependency. The bands MUST be `lt-30` for price &lt; 30, `30-80` for [30, 80), `80-150` for [80, 150), `150-300` for [150, 300), and `gte-300` for ≥ 300, in EUR. A negative price MUST throw `ArgumentOutOfRangeException`. Changing the cuts MUST require a new version string. The catalog upsert MUST set `priceBand` to the result of that function.

#### Scenario: Cuts of price-band/v1
- **WHEN** the function is applied to 29.99, 30, 80, 150, 300
- **THEN** the bands are `lt-30`, `30-80`, `80-150`, `150-300`, `gte-300` respectively

#### Scenario: A negative price fails loudly
- **WHEN** the function is applied to a negative price
- **THEN** `ArgumentOutOfRangeException` is thrown
- **AND** no band is returned

### Requirement: POS availability feed is sparse, bucketed and capped at two hundred
The system SHALL expose `GET /api/ai/index-feed/pos-availability` as a sparse assignment feed. A page MUST contain at most 200 items. The client MUST NOT choose the page size. Active `Inventory` rows in the cursor window MUST be upserts. An inactive assignment whose `greatest(LastUpdatedAt, UpdatedAt)` falls in the cursor window MUST be a tombstone with `reason = unassigned` and body `{ kind, pointOfSaleId, productId, reason, at }`. `qtyBucket` MUST be `0` when `Quantity <= 0`, `1-2` when quantity is 1 or 2, and `3+` when quantity ≥ 3. The JSON MUST NOT include `quantity`. `isAssignedHint` MUST reflect `Inventory.IsActive`.

`sales30d` and `sales90d` MUST be `SUM(Sale.Quantity)` for that `(ProductId, PointOfSaleId)` over the 30 and 90 days preceding a **reference instant**, without subtracting returns. That instant MUST be the configured `IndexFeed:SalesAsOf` when it is set, and the current time otherwise, so an unset configuration preserves the previous behaviour. It MUST be reported on the page as `computedAsOf`, because a windowed figure whose clock is not declared cannot be reproduced: the same configuration and seed must yield the same aggregates on different days. `lastSaleAt` MUST be the greatest `SaleDate` **at or before that same instant**, or null. Leaving it as an unbounded `MAX(SaleDate)` would make it the one figure on the page that still drifts — a sale recorded after the declared horizon moves it — which defeats the reproducibility the reference instant exists to provide, and it is a candidate input for a decay signal that must not move on its own. The cursor MUST be keyset on `(watermark, Inventory.Id)`. `PaginationConstants.MaxPageSize` and the operator product-list cap of 50 MUST NOT be used on this route.

#### Scenario: The feed returns a bucket not an exact quantity
- **GIVEN** an active inventory whose `Quantity` is 0, 1, 2 or ≥ 3
- **WHEN** `GET /api/ai/index-feed/pos-availability` is requested
- **THEN** `qtyBucket` is `0`, `1-2` or `3+` respectively
- **AND** the JSON does not include `quantity`
- **AND** `isAssignedHint` reflects `Inventory.IsActive`
- **AND** `sales30d` and `sales90d` sum `Sale.Quantity` in each window without subtracting returns

#### Scenario: A configured reference instant anchors the sales windows
- **GIVEN** `IndexFeed:SalesAsOf` is configured and sales exist both inside and outside the 30 days preceding it
- **WHEN** the POS feed is requested
- **THEN** `sales30d` counts only the sales inside that window
- **AND** the same request issued on a later day returns the same aggregates
- **AND** the page reports that instant as `computedAsOf`

#### Scenario: A sale after the reference instant does not move the last-sale timestamp
- **GIVEN** `IndexFeed:SalesAsOf` is configured and a sale exists after that instant
- **WHEN** the POS feed is requested
- **THEN** `lastSaleAt` reports the most recent sale at or before the instant
- **AND** it does not report the later sale
- **AND** `sales30d` and `sales90d` do not count it either

#### Scenario: Without configuration the clock is the current time
- **GIVEN** `IndexFeed:SalesAsOf` is not configured
- **WHEN** the POS feed is requested
- **THEN** the windows are counted against the current time, as before
- **AND** `computedAsOf` reports the instant actually used

#### Scenario: Unassignment emits a tombstone
- **GIVEN** an inventory row whose `IsActive` is set to false
- **WHEN** the POS feed is queried with `since` earlier than that change
- **THEN** the item is emitted with `kind = tombstone` and `reason = unassigned`
- **AND** it is not emitted as an upsert

#### Scenario: The POS page cap is 200 and is not copied to UI lists
- **GIVEN** more than 200 availability rows
- **WHEN** the POS feed is requested without a cursor
- **THEN** the page contains at most 200 items
- **AND** `PaginationConstants.MaxPageSize` is not used
- **AND** the catalog feed remains capped at 50

### Requirement: Feeds authenticate only with the index-feed API key
Both feed routes MUST require header `X-Index-Feed-Key`. The key MUST be compared in constant time (`CryptographicOperations.FixedTimeEquals` or equivalent) against `IndexFeed:ApiKey` and, when configured and non-empty, `IndexFeed:ApiKeyPrevious`. A missing header, a distinct key, a user JWT signed with `Jwt:SecretKey`, an `access_token` cookie, or a C03 token signed with `AiGateway:JwtSecret` MUST produce **401 Unauthorized**. The controller MUST NOT use `[Authorize(Roles = ...)]`. Application start MUST fail if `ApiKey` is missing or shorter than 32 characters. The key MUST NOT be written to logs.

#### Scenario: A user JWT does not open the feed
- **GIVEN** an Administrator or Operator with a valid access token (`Jwt:SecretKey`)
- **WHEN** they call a feed without `X-Index-Feed-Key`, using a fresh HTTP client with no cookies from a prior login
- **THEN** the response is 401
- **AND** the same holds with no header, or with a key distinct from `ApiKey` / `ApiKeyPrevious`
- **AND** a C03 token (`AiGateway:JwtSecret`) does not authenticate the feed either

#### Scenario: A valid API key opens the feed
- **GIVEN** `IndexFeed:ApiKey` of at least 32 characters
- **WHEN** a feed is called with that value in `X-Index-Feed-Key` and no user token
- **THEN** the response is 200
- **AND** the same holds when the header matches `ApiKeyPrevious` and that value is configured and non-empty

### Requirement: Aggregate hash is the digest of the global indexable set
Every catalog page MUST include `aggregateHash`: the SHA-256 digest, 64 lowercase hex characters, of the UTF-8 concatenation of every currently indexable `productId` in canonical sorted order. The value MUST be computed once per request over the global set, not over the page, and MUST be identical on every page of that reading. It MUST change when a product enters or leaves the indexable set. The POS feed MUST analogously hash the sorted `(pointOfSaleId, productId)` pairs of currently assigned active inventory rows.

#### Scenario: The aggregate hash detects set drift
- **GIVEN** an indexable set I
- **WHEN** any page of the catalog feed is requested
- **THEN** `aggregateHash` is the SHA-256 hex of the sorted `productId` values of I
- **AND** it is the same on every page of that reading
- **AND** it changes when a product enters or leaves the indexable set

### Requirement: Leaving a family surfaces on the catalog cursor via the product watermark
When a product leaves a family, the catalog feed MUST be able to emit that `productId` against a `since` earlier than the replace: as an upsert without a family when the product remains indexable, or as a tombstone when it is no longer indexable. A family metadata rename MUST surface current members through `Family.UpdatedAt` without rewriting membership rows. This requirement is the feed-side counterpart of the membership watermark on `product-family`; it does not itself write `Product`.

#### Scenario: A product that left a family appears after the replace
- **GIVEN** a product that is omitted from a `PUT` of family members and the identical-list short-circuit does not apply
- **WHEN** the catalog feed is queried with `since` earlier than the replace
- **THEN** that `productId` appears (upsert without family, or tombstone if no longer indexable)
- **AND** its product watermark is after the cursor

#### Scenario: A family rename surfaces current members without rewriting them
- **GIVEN** a family whose name is updated
- **WHEN** the catalog feed is queried with `since` earlier than that update
- **THEN** current members appear via `Family.UpdatedAt`
- **AND** membership rows are not rewritten by the rename

### Requirement: The feed change does not migrate, push or index
This capability MUST NOT add an EF Core or Alembic migration, MUST NOT add `DataOrigin` on `Product`, MUST NOT open an outbox table, MUST NOT call `POST /v1/index/sync`, MUST NOT regenerate `ai-service/openapi.json`, and MUST NOT run AutoBulk over the catalog. A runbook at `Documentos/Proyecto Final AIEng/informes/c12-catalog-autobulk-runbook.md` MUST exist with conditions, commands, time and cost estimates. The runbook is not an execution record.

#### Scenario: Out of scope remains out of scope
- **GIVEN** the feeds are delivered
- **WHEN** the deliverable is inspected
- **THEN** AutoBulk has not been executed over the 1.200 products
- **AND** the AutoBulk runbook markdown exists
- **AND** there is no new EF Core migration, no `data_origin` on `Product`, and no Python client against the feed
- **AND** `POST /v1/index/sync` remains the C13 stub
- **AND** `ai-service/openapi.json` is unchanged

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
