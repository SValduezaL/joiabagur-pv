# ai-assisted-search Specification

## Purpose
Assisted catalog search of the backend behind `POST /api/ai/search`: point-of-sale scope resolved and validated before anything else, the largest candidate window the frozen `jbg-ai` contract can produce requested in a single call and never re-requested, authoritative hydration against the transactional catalog that decides which candidate survives and reports the quantity of that shop while keeping the ones that ran out, truncation to the requested page in retrieval order, bounded degradation to a Spanish full-text searcher scoped to the same point of sale, a per-point-of-sale switch held in configuration, cost bounded by a short-lived candidate cache and a per-user request-rate policy, the three empty outcomes kept distinguishable, and a retrieval funnel observable without new storage.

## Requirements

### Requirement: Assisted search is exposed through a single authenticated endpoint

The backend SHALL expose exactly one operation for assisted catalog search: a write-free POST under the AI namespace, alongside the other AI capabilities and without a version segment in its route, since versioning is applied at the boundary with the separately deployed AI service and not between a client and an API that ship together.

The endpoint MUST require authentication. The request MUST carry the operator's natural-language query, a point of sale, and the page size the caller wants. It MAY carry a search-episode identifier and catalog-side filters. The query length MUST be bounded by the maximum the frozen AI contract declares for its own query field, rather than by an independently chosen limit.

Request validation MUST be invoked explicitly by the endpoint. Registering a validator without invoking it is worse than having none, because it looks like validation.

#### Scenario: A valid request is served
- **WHEN** an authenticated caller posts a query, a point of sale it may use, and a page size
- **THEN** the endpoint answers with a result list, the identifiers of the recorded search, and the state of the assisted path

#### Scenario: An invalid request is rejected before any work is done
- **WHEN** a request carries a blank query or a page size above the allowed maximum
- **THEN** the endpoint answers with a validation error
- **AND** no call is issued to the AI service
- **AND** no search event is recorded

#### Scenario: An unauthenticated request is refused
- **WHEN** an unauthenticated caller posts a search request
- **THEN** the endpoint refuses it
- **AND** no call is issued to the AI service

### Requirement: Every assisted search is scoped to one concrete point of sale

The system SHALL require a concrete point of sale on every assisted search and MUST NOT infer one when several are possible or substitute a wildcard when none is supplied. A request without a point of sale MUST be rejected as invalid.

An operator MUST be refused, without the search being executed, when the requested point of sale is not one they are assigned to. An administrator MAY search on any active point of sale, since administrators hold no assignments and the capability would otherwise be undemonstrable without creating artificial ones; an inactive point of sale MUST be refused for every role.

The point-of-sale scope sent to the AI service MUST come from the validated scope and MUST NOT be taken from the request body, so that the retriever's scope cannot be influenced by the caller.

#### Scenario: A request without a point of sale is invalid
- **WHEN** a request omits the point of sale
- **THEN** the endpoint answers with a validation error
- **AND** the error states that assisted search requires a point of sale

#### Scenario: An operator cannot search on a point of sale they are not assigned to
- **WHEN** an operator requests a point of sale outside their assignments
- **THEN** the request is forbidden
- **AND** no call is issued to the AI service
- **AND** no search event is recorded

#### Scenario: An administrator may search on any active point of sale
- **WHEN** an administrator requests a point of sale they hold no assignment for and which is active
- **THEN** the search is executed for that point of sale

#### Scenario: An inactive point of sale is refused for every role
- **WHEN** any caller requests an inactive point of sale
- **THEN** the request is refused
- **AND** no call is issued to the AI service

### Requirement: The candidate window is requested once and never re-requested

The system SHALL ask the AI service for the largest candidate window its over-retrieval rule can produce, in a single call per search, and MUST NOT issue a second retrieval call because too few candidates survived hydration.

The requested page size MUST come from configuration rather than being hard-coded, and MUST be capped by the maximum the frozen contract accepts.

A second call is forbidden because the retriever applies its confidence threshold before its result limit: when fewer candidates come back than the over-retrieval rule allows, the threshold was the binding constraint and a larger request would return the same rows while charging a second query embedding. The system MUST therefore answer with however many results survived, even when that is fewer than the requested page size.

#### Scenario: One retrieval call per search
- **WHEN** a search is served by the assisted path
- **THEN** exactly one retrieval call is issued to the AI service

#### Scenario: A short page does not trigger a second call
- **WHEN** hydration leaves fewer results than the requested page size
- **THEN** no further retrieval call is issued
- **AND** the surviving results are returned
- **AND** the response is not an error

#### Scenario: The requested window is configured, not hard-coded
- **WHEN** the search service is constructed
- **THEN** the candidate window comes from configuration
- **AND** it does not exceed the maximum page size the frozen contract accepts

### Requirement: The backend is the authority on price, stock and availability

The system SHALL hydrate every candidate returned by the AI service against the transactional catalog before showing it, and MUST take price, quantity, name, photo and collection from that hydration rather than from the AI response, which is required never to carry them.

A candidate MUST be discarded when the product is inactive, when it has no inventory record at the point of sale of the search, or when that inventory record is inactive, since inventory assignment is what determines that a product belongs to a point of sale.

A candidate whose quantity is zero MUST be kept and marked as out of stock. Availability weights a result; it never removes it. Suppressing it would turn a sale-saving answer — the shop carries the piece and is out of it — into a silent gap.

The quantity reported MUST be the quantity at the point of sale of the search, not the sum across every point of sale the caller can access.

Hydration MUST be performed with a set-based query over the whole candidate list. Resolving inventory or photos one candidate at a time is forbidden, because the candidate window makes it two orders of magnitude of round trips inside a request that competes with the retrieval time budget.

When the identifier the index reports for a product differs from the one the catalog holds, the catalog value MUST prevail and the divergence MUST be logged.

#### Scenario: Price and stock come from the catalog
- **WHEN** results are built for a hydrated candidate
- **THEN** its price and quantity come from the transactional catalog
- **AND** they do not come from the AI response

#### Scenario: A candidate no longer available at the point of sale is dropped
- **WHEN** a candidate has no inventory record at the point of sale of the search, or its inventory record is inactive, or the product is inactive
- **THEN** it does not appear in the results

#### Scenario: A candidate with no stock is kept and marked
- **WHEN** a candidate is assigned to the point of sale with a quantity of zero
- **THEN** it appears in the results
- **AND** it is marked as having no stock

#### Scenario: The quantity is the one at that point of sale
- **WHEN** a product has stock at several points of sale the caller can access
- **THEN** the quantity reported is the one at the point of sale of the search

#### Scenario: Hydration does not query per candidate
- **WHEN** a full candidate window is hydrated
- **THEN** the number of queries issued does not grow with the number of candidates

### Requirement: Results are truncated to the requested page in retrieval order

The system SHALL return at most the requested page size and MUST preserve the relevance order in which the AI service returned the candidates. It MUST NOT re-sort the surviving results, because the rank is the measurement of retrieval quality and re-sorting would make it measure the backend instead.

#### Scenario: More survivors than the page size
- **WHEN** more candidates survive hydration than the requested page size
- **THEN** the response carries exactly the requested page size
- **AND** the results keep the order in which the AI service returned them

### Requirement: A failing AI service degrades the search, never breaks it

The system SHALL answer successfully when the AI service cannot serve the retrieval, whatever the reason: an open circuit, an exhausted time budget, a transport failure, a route with no implementation, or credentials the service rejected. Every one of these MUST fall back to the degraded searcher and MUST be reported to the caller as the assisted path being unavailable. A credential failure MUST additionally be logged at error level, since it is a configuration fault that would otherwise pass unnoticed behind a working search.

The system MUST NOT surface a failure of the AI service as a failed search.

#### Scenario: An unavailable AI service falls back
- **WHEN** the retrieval call fails because the circuit is open, the time budget is exhausted, or the transport failed
- **THEN** the response is successful
- **AND** it reports the assisted path as unavailable
- **AND** the results come from the degraded searcher

#### Scenario: A credential failure degrades and is logged
- **WHEN** the AI service rejects the credentials
- **THEN** the response is successful and reports the assisted path as unavailable
- **AND** the failure is logged at error level

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

### Requirement: Assisted search can be switched off per point of sale

The system SHALL decide per point of sale whether the assisted path is used, from configuration that can be reloaded without redeploying, and MUST default to not enabled so that enabling is an explicit act.

When it is switched off, the system MUST serve the search without consulting the AI service at all, MUST report the assisted path as unavailable, and MUST record the search with the origin that means the AI service was never consulted, distinct from the one that means it was consulted and failed.

The results MUST come from the same non-assisted searcher the degraded path uses, and MUST NOT come from the pre-existing catalog search. The pre-existing searcher reports stock summed across every point of sale the caller can access and is not scoped to one shop, so serving it here would break this endpoint's own guarantee that the quantity shown is the quantity at the point of sale of the search — and would do so only for the points of sale where the feature happens to be switched off, which is the hardest kind of inconsistency to notice.

Storing this decision MUST NOT require a schema change.

#### Scenario: A disabled point of sale never reaches the AI service
- **WHEN** a search is requested for a point of sale where assisted search is switched off
- **THEN** no retrieval call is issued
- **AND** the response reports the assisted path as unavailable
- **AND** the results come from the non-assisted searcher, scoped to that point of sale

#### Scenario: The disabled path is distinguishable from the degraded one
- **WHEN** a search served with assisted search switched off is recorded
- **THEN** its origin is the disabled one
- **AND** it is not recorded as a degraded search

### Requirement: The three empty outcomes are distinguishable

The system SHALL let the caller tell apart the three situations that produce no results, because a single empty list would make the interface state something untrue in two of the three cases:

- the AI service answered and nothing cleared its confidence threshold;
- the AI service returned candidates and none of them survived hydration at that point of sale;
- the assisted path did not serve the search at all.

The response MUST therefore carry both whether the assisted path served the search and whether the retriever abstained.

#### Scenario: Abstention is reported as such
- **WHEN** the AI service answers with no candidates and low confidence
- **THEN** the response reports the assisted path as available and the retrieval as low confidence

#### Scenario: An empty page after hydration is not abstention
- **WHEN** the AI service returns candidates and none survives hydration
- **THEN** the response reports the assisted path as available and the retrieval as not low confidence
- **AND** the result list is empty

#### Scenario: A degraded empty page is neither
- **WHEN** the degraded searcher finds nothing
- **THEN** the response reports the assisted path as unavailable

### Requirement: Every served search is recorded, and recording it can never break it

The system SHALL record every search it serves through the assisted-search telemetry capability, and MUST do so after hydrating and truncating, so that what is stored is the list the operator was shown rather than the raw candidate window.

It MUST pass the effective filters, the origin of the results, the correlation identifier, the duration of obtaining the candidates, the total handling duration, and the search-episode identifier supplied by the caller, generating one when the caller supplies none.

The total handling duration MUST be captured before the recording call, so that the recorded duration does not include the recording itself.

The identifier of the recorded event MUST be returned to the caller so a later selection can be attributed to this search. The recording operation never throws and may report no identifier; the system MUST tolerate that and answer normally.

#### Scenario: The displayed list is what gets recorded
- **WHEN** a search returning a truncated page is recorded
- **THEN** the recorded result list is the truncated page, in display order
- **AND** it is not the full candidate window

#### Scenario: The recorded duration excludes the recording
- **WHEN** a search is recorded
- **THEN** the total handling duration was captured before the recording call was made

#### Scenario: A telemetry failure does not fail the search
- **WHEN** recording the search reports no identifier
- **THEN** the search still answers successfully
- **AND** the response carries no search event identifier

#### Scenario: An episode identifier always exists
- **WHEN** a request carries no search-episode identifier
- **THEN** the recorded event carries one generated by the server

### Requirement: The cost of a search is bounded

The system SHALL bound what an assisted search can spend, because every one of them charges a query embedding and an operator holding a key or a mis-tuned client can issue many in seconds.

It MUST cache the candidates the AI service returned for a short, configurable lifetime, storing only their identifiers and scores. It MUST NOT cache hydrated values: hydration MUST be performed again on a cache hit, so that a cached search can never serve a stale price or a stale stock figure.

The cache key MUST include the point of sale, even while retrieval is independent of it, so that the key does not silently become a cross-point-of-sale leak when the retriever gains a point-of-sale filter.

It MUST apply a request-rate policy to the endpoint, partitioned by user rather than by network origin, because a whole shop shares one origin behind the reverse proxy. Exceeding it MUST be reported distinguishably from the AI service being unavailable.

#### Scenario: A repeated query does not pay for a second embedding
- **WHEN** the same query is issued twice from the same point of sale within the cache lifetime
- **THEN** the second search issues no retrieval call to the AI service

#### Scenario: A cache hit still hydrates
- **WHEN** a search is served from cached candidates and the stock of one of them changed in between
- **THEN** the response reports the current stock

#### Scenario: The cache key separates points of sale
- **WHEN** the same query is issued from two different points of sale
- **THEN** the cached entry of one is not served to the other

#### Scenario: The rate policy is partitioned by user
- **WHEN** two users of the same shop issue searches from the same network origin
- **THEN** their requests are counted separately

#### Scenario: Exceeding the rate policy is not reported as AI unavailability
- **WHEN** a caller exceeds the request-rate policy
- **THEN** the response reports too many requests
- **AND** it is not a successful response reporting the assisted path as unavailable

### Requirement: The retrieval funnel is observable without new storage

The system SHALL emit, for every served search, a structured event carrying the correlation identifier, the point of sale, how many candidates the AI service returned, how many survived hydration and how many were displayed, so that the loss caused by filtering by point of sale after retrieval is measurable per point of sale.

This instrumentation MUST NOT require new persisted columns. The proportion of searches that do not fill a page is derivable from the displayed-result count and the point of sale that telemetry already persists, and separating abstention from an empty page after hydration is derivable by joining on the correlation identifier with the retrieval stage logs of the AI service.

The operator's query text MUST NOT appear in any event at information level or above.

#### Scenario: The funnel is emitted per search
- **WHEN** a search is served
- **THEN** a structured event carries the correlation identifier, the point of sale, the candidate count, the survivor count and the displayed count

#### Scenario: No new columns are added
- **WHEN** the persisted schema is compared before and after this capability
- **THEN** it is unchanged
- **AND** no migration was generated

#### Scenario: The query stays out of production logs
- **WHEN** the funnel event is emitted
- **THEN** the operator's query text does not appear in it

### Requirement: Results carry the material signals the retriever recognised

Each result returned to the caller SHALL carry the materials the AI service reported for that candidate, so that the interface can explain why a result is being shown.

These materials are **not** hydrated and are **not** authoritative: they come from the enriched index, not from the transactional catalog, and they are the same values the caller may filter on. They exist to explain a match, never to describe stock, price or availability, which remain the exclusive product of hydration.

The field MUST be present and empty rather than absent when the retriever reported none, and MUST be empty on the degraded and disabled paths, where no retriever ran.

This is the only explanatory signal available today: the retriever's match reasons are a single constant value for every result until the lexical branch exists, so a caller has nothing else with which to tell an operator why a piece was proposed.

#### Scenario: A retrieved result carries its materials
- **WHEN** a result is built from a candidate the AI service returned
- **THEN** it carries the materials that candidate reported

#### Scenario: Materials never come from hydration
- **WHEN** a result carries materials
- **THEN** they are the values the AI service reported
- **AND** they are not read from the transactional catalog

#### Scenario: A degraded result carries no materials
- **WHEN** a result is produced by the degraded or the disabled path
- **THEN** its material list is empty
- **AND** it is not absent
