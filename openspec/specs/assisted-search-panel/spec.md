# assisted-search-panel Specification

## Purpose
Assisted search panel of the frontend: a third sales entry method living on its own lazily loaded route that hands the chosen product to the manual sale flow instead of duplicating it, a search issued only on an explicit act and never as a side effect of typing so that its cost stays bounded, quick filters over the closed enrichment vocabulary that can be cleared in a single act, a point-of-sale scope resolved by role and carried on every search — a concrete shop, or, for an administrator only, the absence that covers every one of them and reports no stock, reachable from the selector and pinning the assisted route, results rendered in the retrieval order with the price, stock and availability the backend supplied, an explanation built per result only from what the system actually asserts together with a statement of which retriever answered the search, the four ways of showing nothing kept distinguishable together with the declared short page, a retrieval funnel reserved to administrators, one search episode per visit to the panel, a selection reported at the instant of the click that never blocks the sale, and the originating search carried per line all the way to the till.

## Requirements

### Requirement: Assisted search is an entry method of the sales flow, on its own route

The frontend SHALL expose assisted search as a third way of starting a sale, reachable from the sales landing page and living on its own lazily loaded route under the sales tree, alongside the scanning and manual entry routes.

The panel MUST hand the chosen product to the existing manual sale page through navigation state, the same mechanism the scanning and image recognition pages already use, rather than duplicating the payment method, quantity, price and stock logic that page already owns.

The panel MUST NOT replace or alter the SKU searcher of the manual sale page, which remains the fast path for an operator who already knows what they want.

#### Scenario: The panel is reachable from the sales landing page
- **WHEN** an authenticated operator opens the sales landing page
- **THEN** a third entry option for assisted search is displayed alongside scanning and manual entry
- **AND** activating it navigates to the assisted search route

#### Scenario: The chosen product is handed to the manual sale page
- **WHEN** the operator selects a result for sale
- **THEN** the application navigates to the manual sale page
- **AND** the chosen product identifier travels in navigation state
- **AND** the manual sale page pre-selects that product

#### Scenario: The pre-existing SKU searcher is untouched
- **WHEN** the manual sale page is used without passing through the panel
- **THEN** its SKU searcher behaves as it did before this capability existed

### Requirement: A search is issued only when the operator asks for one

The panel SHALL issue a search only on an explicit act — submitting the query field or activating the search control — and MUST NOT issue one as a side effect of typing, however long the pause between keystrokes.

Typing MUST NOT be debounced into requests. Every uncached search charges a query embedding and consumes the endpoint's per-user request budget, and the candidate cache is keyed on the whole query string, so no prefix of a query can ever hit it: a debounced field would spend several embeddings per query, of which at most one would be read.

The panel MUST offer a small set of example queries that fill the field and run the search in a single act, so that what the system can be asked is expressed by the interface rather than left for each operator to discover.

Quick filters MUST NOT issue a search on their own, since each change of filter produces a different cache key and would charge another embedding per toggled value.

Changing the point of sale MUST clear the displayed results and MUST NOT re-issue the search automatically, because the cache key includes the point of sale and the same query in another shop pays again.

#### Scenario: Typing costs nothing
- **WHEN** the operator types, deletes and types again without submitting
- **THEN** no search request is issued

#### Scenario: Submitting issues exactly one search
- **WHEN** the operator submits the query field or activates the search control
- **THEN** exactly one search request is issued

#### Scenario: An example query searches in one act
- **WHEN** the operator activates one of the example queries
- **THEN** the query field is filled with it
- **AND** exactly one search request is issued

#### Scenario: Toggling a filter does not search
- **WHEN** the operator toggles a quick filter
- **THEN** no search request is issued until the operator submits

#### Scenario: Changing the point of sale clears rather than re-searches
- **WHEN** the operator changes the point of sale after a search
- **THEN** the displayed results are cleared
- **AND** no search request is issued

### Requirement: Quick filters offer the closed vocabulary and can be cleared at once

The panel SHALL let the operator restrict a search by material, allowing several materials at the same time, and by piece category.

The material options MUST be the closed vocabulary the enrichment pipeline uses, and the panel MUST send the canonical term rather than the displayed label. A value outside that vocabulary matches nothing in the index and fails silently, so the list MUST be pinned by a test against its source of truth.

The panel MUST offer a single action that removes every active filter, because two hard filters — material at retrieval and point of sale at hydration — compose, and clearing them is the first remedy when a search returns nothing.

#### Scenario: Several materials at once
- **WHEN** the operator selects one material and then another
- **THEN** both remain selected
- **AND** the next search carries both

#### Scenario: The canonical term is what travels
- **WHEN** a material is selected
- **THEN** the search request carries its canonical vocabulary term

#### Scenario: Every filter can be removed in one act
- **WHEN** the operator activates the clear-filters action
- **THEN** no material or category filter remains active

### Requirement: The search is scoped to one point of sale, chosen according to role

The panel SHALL send, on every search, either a concrete point of sale taken from what the caller is allowed to use or no point of sale at all, which is the scope covering every one of them and is offered only to administrators.

The first clause of this requirement previously read that a concrete point of sale is sent on **every** search. That stopped being true when the free-query route gained the every-point-of-sale scope, and a live requirement stating the opposite of what the system does is worse than a missing one: structural validation passes over it, so nothing reports it.

When the operator is assigned exactly one point of sale, it MUST be pre-selected and the selector MUST NOT be shown. When several are available, or the caller is an administrator, a selector MUST be offered. Only active points of sale MUST be offered, since the endpoint refuses an inactive one for every role.

Whatever the role, the point of sale pre-selected when the panel loads MUST be a concrete active shop and MUST NOT be the every-point-of-sale scope, because that scope reports no stock and a panel that opened in it would answer the counter's first question with nothing.

#### Scenario: A single assignment needs no choice
- **WHEN** the operator is assigned exactly one point of sale
- **THEN** it is pre-selected
- **AND** no point-of-sale selector is displayed

#### Scenario: Several assignments are chosen from
- **WHEN** the caller has several points of sale available, or is an administrator
- **THEN** a selector is displayed with the active points of sale they may use

#### Scenario: A refused point of sale is reported as an access problem
- **WHEN** the endpoint refuses the search because the caller may not use that point of sale
- **THEN** the panel states that the caller has no access to that shop
- **AND** it does not present it as a failure of the search service

#### Scenario: The panel opens on a concrete shop and never on the wider scope
- **WHEN** the panel finishes loading for any role
- **THEN** the point of sale selected is the first active shop available to the caller
- **AND** it is not the scope covering every point of sale

### Requirement: The panel offers the every-point-of-sale scope to administrators, and states which route can serve it

The panel SHALL offer an administrator an explicit way to scope a search to every point of sale, distinguishable from having chosen one, and MUST NOT offer it to an operator, because that scope reports no stock and therefore cannot complete a sale: it is a way of exploring the catalogue, which is administration work rather than counter work.

This requirement exists because C40 built the scope in full — a third `AiCallScope` class, a third claims profile, authorisation open to operators and administrators, nullable quantities and a result row with three states — and no control was ever added, so the whole of it went unexecuted. The three scenarios the panel already had described what the screen does **while** in that state and none of them demanded a way in. A state with no path to it is a state nobody can use, and specifying the state without the path is what let a whole stretch of work return nothing.

The narrowing is a decision of the screen and MUST NOT be read as an authorisation boundary: the free-query route continues to serve the scope to operators and administrators alike, which is what its own capability requires, and the boundary that is actually protected is that no caller may **name** a point of sale they are not assigned to. Tightening the route to administrators would contradict that capability and is explicitly not what this requirement asks for.

Because the scope reports no stock, selecting it MUST state that consequence before the operator searches — that results cover the whole catalogue and that a point of sale must be chosen to read stock — rather than leaving it to be discovered result by result.

The value the selection control carries for this scope MUST NOT reach the request. The scope travels as the **absence** of the point of sale field, never as a blank identifier, because what makes the scope safe is that an absent point of sale leaves the availability prefilter unapplied rather than matching every shop.

Selecting the scope MUST NOT issue a search, like every other change of scope or filter in this panel.

#### Scenario: An administrator can reach the every-point-of-sale scope
- **WHEN** an administrator opens the panel and inspects the point-of-sale control
- **THEN** an explicit option to search every point of sale is offered, distinguishable from the shops listed beside it
- **AND** selecting it leaves the query field and the search control usable

#### Scenario: An operator is not offered the scope, and the route still serves it
- **WHEN** an operator opens the panel, whether assigned one point of sale or several
- **THEN** no option to search every point of sale is offered
- **AND** the free-query route continues to serve that scope to an operator that requests it, because the narrowing belongs to the screen and not to authorisation

#### Scenario: Selecting the scope costs no search
- **WHEN** the administrator changes the scope to every point of sale with results on screen
- **THEN** no search request is issued
- **AND** the displayed results are cleared

#### Scenario: The consequence of the scope is stated before searching
- **WHEN** the every-point-of-sale scope is selected
- **THEN** the panel states that results cover the whole catalogue and that a point of sale must be chosen to read stock
- **AND** it states it before any search has been issued

#### Scenario: The scope travels as an absence and never as a blank identifier
- **WHEN** the administrator searches with the every-point-of-sale scope selected
- **THEN** the request carries no point-of-sale field at all
- **AND** no request the panel issues carries a blank point-of-sale identifier

### Requirement: Results are displayed in the order received, with the truth the backend supplied

The panel SHALL render results in the exact order the backend returned them and MUST NOT sort, re-rank or filter them on the client, because the rank is the measurement of retrieval quality and re-sorting would make it measure the interface instead.

Each result MUST display its photo, SKU, name, price and the quantity at the point of sale of the search. A result with no stock MUST be displayed and marked as out of stock rather than hidden, since the shop carrying a piece it has run out of is an answer that can still save a sale.

Prices MUST be displayed in euros with Spanish locale formatting.

The result row MUST be an isolated component, so that the later change that adds the generated pitch, citations and family grouping extends it rather than rewriting the page.

#### Scenario: The order is the backend's
- **WHEN** results are rendered
- **THEN** they appear in the order the response listed them
- **AND** no client-side sorting is applied

#### Scenario: A result with no stock is shown and marked
- **WHEN** a result reports no stock at the point of sale
- **THEN** it is displayed
- **AND** it is marked as out of stock

### Requirement: A result explains itself with what the system actually knows

The panel SHALL explain a result with an origin badge together with the materials the retriever recognised.

The origin badge MUST be derived **per result** from that result's own match reasons, and MUST NOT be a single decision taken once for the whole response from whether the assisted path served the search. A result the lexical branch alone produced MUST NOT be labelled a semantic match, so that a search served after the embedding provider failed tells the operator what actually answered it instead of claiming a capability that did not run.

The panel MUST NOT render the retriever's raw match reason values, which are engineering vocabulary, and MUST NOT synthesise an explanation the system has not asserted.

The variant label MUST be displayed only when present, so that it appears on its own once the change that populates it has run, without the panel being touched.

The mapping from origin to badge MUST tolerate values it does not know without failing, falling back to a neutral label rather than throwing or leaving the badge empty.

#### Scenario: The badge and the materials explain the match
- **WHEN** a result is rendered
- **THEN** an origin badge is displayed
- **AND** the materials the retriever recognised are displayed

#### Scenario: A result served only by the lexical branch says so
- **GIVEN** a response whose results carry different match reasons
- **WHEN** a result whose match reasons do not include the vector branch is rendered
- **THEN** its badge is the text-search origin
- **AND** a result whose match reasons include the vector branch shows the assisted origin in the same list

#### Scenario: An unknown origin does not break the row
- **WHEN** a result carries a match reason the panel does not know
- **THEN** a neutral origin label is displayed
- **AND** the row renders without error

#### Scenario: The raw match reasons are not shown
- **WHEN** a result is rendered
- **THEN** the retriever's raw match reason values do not appear on screen

#### Scenario: An absent variant label leaves no gap
- **WHEN** a result carries no variant label
- **THEN** no size is displayed for it
- **AND** no placeholder value is invented

### Requirement: The panel says which retriever answered the search

The panel MUST state, for the response as a whole, which retriever produced the results it is showing, derived from the provenance the results carry rather than asserted by a field of the response. Three outcomes MUST be distinguishable:

- the assisted path served and at least one result came from the semantic branch;
- the assisted path served but **no** result came from the semantic branch, which is the retrieval service having degraded to its text branch after the embedding provider failed;
- the assisted path did not serve at all and the caller's own text search answered.

The second case MUST be stated on screen. It is the failure that looks healthiest of all — the request succeeds, results are rendered and the response reports the assisted path as available — so leaving it unsaid shows the operator a screen named after a capability that did not run. It MUST NOT be presented as the assisted search being unavailable, because it answered.

When no result is returned there is no provenance to read, so the panel MUST NOT claim a mode; that case is already covered by the empty-state messages, which stay unchanged.

The low-confidence marking MUST be read only alongside an empty result list, because the retriever computes it as branch disagreement only when more than one branch ran and as "nothing was returned" otherwise.

#### Scenario: A degraded semantic branch is stated rather than hidden
- **GIVEN** a response reporting the assisted path as available
- **AND** no result carries the semantic branch among its match reasons
- **WHEN** the panel renders it
- **THEN** it says the semantic match was not available
- **AND** it does not say the assisted search is unavailable
- **AND** the results are still rendered

#### Scenario: A fused response is not warned about
- **GIVEN** a response in which at least one result came from the semantic branch
- **WHEN** the panel renders it
- **THEN** no warning about the semantic branch is displayed

#### Scenario: The caller's own text search keeps its own message
- **GIVEN** a response reporting the assisted path as unavailable
- **WHEN** the panel renders it
- **THEN** it says the assisted search is unavailable
- **AND** the results are labelled as coming from the text search

#### Scenario: No results means no claim about the mode
- **GIVEN** a response with no results
- **WHEN** the panel renders it
- **THEN** no retriever is named
- **AND** the empty-state message is shown instead

### Requirement: The four ways of showing nothing say four different things

The panel SHALL distinguish, on screen, the four situations that produce no results, because a single empty list would state something untrue in three of them:

- the retriever answered and nothing cleared its confidence threshold — the operator is invited to rephrase;
- the retriever returned candidates and none of them is carried by this shop — the operator is invited to clear the filters first, since a hard filter is the likelier cause than the wording;
- the assisted path did not serve the search, whether degraded or switched off — the operator is told that assisted search is not available and that what is shown comes from the text searcher;
- the request budget was exceeded — the operator is told there have been too many searches in a row.

Exceeding the request budget MUST NOT be presented as the AI service being unavailable. They have different causes, different remedies and opposite operational meanings: one is a fault, the other is the system protecting itself.

None of the four MUST be presented as an application error.

While a search is in flight the panel MUST show a loading state rather than an empty list.

#### Scenario: Abstention invites rephrasing
- **WHEN** the response reports the assisted path as available and the retrieval as low confidence, with no results
- **THEN** the panel states that nothing matching was found
- **AND** it invites the operator to rephrase

#### Scenario: An empty assortment invites clearing the filters
- **WHEN** the response reports the assisted path as available, the retrieval as not low confidence, candidates returned, and no results
- **THEN** the panel states that similar pieces exist but none is in this shop
- **AND** it offers clearing the filters as the first remedy

#### Scenario: An unavailable assisted path is named as such
- **WHEN** the response reports the assisted path as unavailable
- **THEN** the panel states that assisted search is not available
- **AND** it states that the results shown come from the text searcher

#### Scenario: An exhausted request budget is not an outage
- **WHEN** the endpoint answers that too many requests were made
- **THEN** the panel states that too many searches were made in a row
- **AND** it does not state that the assisted search service is unavailable

#### Scenario: A search in flight shows progress
- **WHEN** a search request is in flight
- **THEN** the panel shows a loading state
- **AND** it does not show an empty result list

### Requirement: A page shorter than requested is declared, not disguised

The panel SHALL state, when fewer results survived than the page size asked for, how many the shop has and how many candidates were considered, using the counters the response already carries.

This is the frequent case at the points of sale with the lowest assortment coverage. Left unsaid, it reads as the system being unable to search, when what happened is that the shop does not carry the assortment.

The results MUST still be displayed: a short page is not an error state.

#### Scenario: A short page explains itself
- **WHEN** fewer results survive than the requested page size, and at least one survives
- **THEN** the panel states how many results this shop has and how many candidates were considered
- **AND** the results are displayed normally

### Requirement: The retrieval funnel is visible to administrators only

The panel SHALL expose the retrieval funnel only to callers whose role is administrator, collapsed by default, and MUST show the counters the response carries: the candidates the retriever produced, the candidates that survived hydration and the results displayed.

On the assisted route it MUST additionally show what the response carries about the cost and the timing of that request: the elapsed time of the AI call and of the whole request as two separate figures, the model, the input and output token counts, and the reason the path degraded when it degraded.

It MUST also show the identifier of the recorded search event when the response returned one, on both routes. That identifier, and not the correlation identifier of the call, is what the block can show: the response deliberately does not carry a correlation identifier — it exists only in the structured funnel log of the backend — whereas the search event identifier is the key that joins what the administrator is looking at to what telemetry persisted about it. On the assisted route its absence is itself informative, because a search spread over every point of sale is not recorded at all, and the funnel says so rather than leaving the gap to be read as a telemetry failure.

It MUST NOT show any monetary amount. Token counts and the model name are the inputs of a cost; a tariff written into the screen is wrong the day the provider moves it, and the model reported for a multi-stage route names only its last stage, so multiplying it would be false there and inviting the multiplication here would spread it.

It MUST NOT show the operator's query nor the generated argument inside the funnel.

An operator whose role is not administrator MUST NOT see the funnel at all.

#### Scenario: The funnel is collapsed and restricted
- **WHEN** an administrator receives a response
- **THEN** the funnel is available and collapsed by default

#### Scenario: An operator never sees the funnel
- **WHEN** a caller whose role is not administrator receives a response
- **THEN** no funnel is rendered

#### Scenario: The funnel carries the search event identifier
- **WHEN** an administrator expands the funnel of a response that returned a search event identifier
- **THEN** that identifier is shown
- **WHEN** the response returned none because the search covered every point of sale
- **THEN** the funnel states that the search was not recorded, rather than showing nothing

#### Scenario: The assisted funnel splits the elapsed time
- **WHEN** an administrator expands the funnel of an assisted response
- **THEN** the elapsed time of the AI call and of the whole request are shown as two separate figures
- **AND** the model and the input and output token counts are shown

#### Scenario: The funnel shows no money
- **WHEN** the funnel is expanded
- **THEN** no monetary amount appears

#### Scenario: The funnel shows no content
- **WHEN** the funnel is expanded
- **THEN** neither the operator's query nor the generated argument appears in it

### Requirement: One search episode per visit to the panel

The panel SHALL generate one search-episode identifier when it is opened and send it with every search of that visit, so that the reformulations of one visit group together and are not counted as abandoned queries.

Changing the point of sale within a visit MUST NOT change it. Opening the panel again MUST produce a new one, because two visits that each end in a selection are two legitimate episodes with nothing to group between them.

#### Scenario: Reformulations share the episode
- **WHEN** the operator searches several times within one visit
- **THEN** every request carries the same search-episode identifier

#### Scenario: Changing the shop does not start a new episode
- **WHEN** the operator changes the point of sale within one visit
- **THEN** the search-episode identifier is unchanged

#### Scenario: A new visit is a new episode
- **WHEN** the operator opens the panel again
- **THEN** a different search-episode identifier is generated

### Requirement: The selection is reported at the moment of the click and never blocks

The panel SHALL report the operator's selection to the telemetry endpoint at the instant of the click, without waiting for the outcome and without deferring or batching it, because the server stamps the moment and a delayed call would measure the browser instead of the operator.

A failure of that report MUST NOT show an error, MUST NOT block navigation and MUST NOT prevent the sale.

When the response carried no search event identifier — which the search endpoint is allowed to return — the report MUST be skipped silently.

#### Scenario: The report does not delay the operator
- **WHEN** the operator selects a result
- **THEN** the selection is reported
- **AND** navigation to the sale flow happens without waiting for its outcome

#### Scenario: A failed report is invisible
- **WHEN** reporting the selection fails
- **THEN** no error is shown to the operator
- **AND** navigation completed normally

#### Scenario: No event identifier means no report
- **WHEN** the search response carried no search event identifier
- **THEN** no selection report is issued
- **AND** the selection still works

### Requirement: The originating search travels with the product to the till

The panel SHALL pass the search event identifier along with the chosen product, and the sales flow MUST carry it, per line, from the selection through to sale creation — both when the sale is completed directly and when the line goes through the cart.

A sale started by any other entry method MUST carry no attribution and MUST remain valid.

#### Scenario: A direct sale carries its search
- **WHEN** the operator completes a sale directly after selecting a result
- **THEN** the sale creation request carries the search event identifier

#### Scenario: A cart line carries its own search
- **WHEN** the operator adds the selected product to the cart and checks out
- **THEN** that line of the bulk request carries its own search event identifier

#### Scenario: Another entry method carries none
- **WHEN** a sale is started by scanning or by SKU search
- **THEN** the sale creation request carries no search event identifier
- **AND** the sale is created normally

### Requirement: A stale response never overwrites a newer one

The panel SHALL ignore the response of any search that is no longer the current one, so that submitting, changing the point of sale and submitting again cannot leave the results of the first request on screen.

#### Scenario: An out-of-order response is discarded
- **WHEN** a second search is issued before the first has resolved
- **AND** the first response arrives last
- **THEN** the displayed results are those of the second search

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

### Requirement: The operator chooses between a fast search and an assisted answer, and the panel states the difference before the choice

The panel SHALL offer two routes over the same query — a fast semantic search and an assisted answer — as an explicit, visible choice, and MUST state the difference in cost before the operator makes it, because the two are not two flavours of the same price: one is a single embedding while the other adds a classifier, a corpus consultation and a generation, with a time budget four times larger and a request quota three times smaller.

The fast route MUST be the default, and the choice MUST NOT be remembered between visits, because remembering the expensive route is how it gets spent unintentionally.

Changing the route MUST NOT issue a search by itself: the existing rule that a search happens only on an explicit act applies unchanged to both routes, and so does the rule that no search follows from typing, from changing a filter or from changing the point of sale.

#### Scenario: The fast route is the default
- **WHEN** the operator opens the panel
- **THEN** the fast route is selected
- **AND** the assisted route is not

#### Scenario: The difference in cost is stated before the choice
- **WHEN** the operator inspects the route selector
- **THEN** the panel states that the assisted answer is slower and more limited in number of requests
- **AND** it does so without the operator having issued any search

#### Scenario: Changing the route issues no search
- **WHEN** the operator changes the selected route
- **THEN** no request is issued

#### Scenario: The choice is not remembered
- **WHEN** the operator selects the assisted route, leaves the panel and returns
- **THEN** the fast route is selected again

### Requirement: The availability of each AI path is stated before any search is issued

The panel SHALL state, before the operator issues any search, whether each of the two AI paths is available for the scope currently selected — a concrete point of sale or every point of sale — reading it from a route that calls no model and consumes no request quota.

Reading it for the scope and not only for a selected shop is what stops the wider scope from switching the generative path off in silence: while the panel read availability only for a concrete point of sale, selecting the wider scope left the reading unresolved, the availability statement stuck on its pending text and the assisted option disabled with no reason to show — which is the very failure this statement was introduced to remove.

When the assisted path is unavailable, its option in the route selector MUST be disabled and the reason MUST be stated, rather than letting the operator select an option that is guaranteed to fail.

This statement MUST be independent of, and MUST NOT be replaced by, whatever notice appears with the results afterwards: one describes availability before acting, the other describes what happened during a request. In particular, a response reporting an unclassified intent means the AI answered and the classifier did not run, which no switch announces.

#### Scenario: Availability is stated before searching
- **WHEN** the panel finishes loading
- **THEN** it states whether the fast path and the assisted path are available
- **AND** it does so before any search has been issued

#### Scenario: An unavailable assisted path disables its option with a reason
- **WHEN** the assisted path is unavailable for the scope currently selected
- **THEN** its option in the route selector is disabled
- **AND** the reason is stated

#### Scenario: Reading availability costs nothing
- **WHEN** the panel reads availability
- **THEN** no model is called
- **AND** no request quota is consumed

#### Scenario: The wider scope is a scope availability is read for, not a gap
- **WHEN** the scope covering every point of sale is selected
- **THEN** the panel reads availability for that scope and states a settled answer
- **AND** it does not remain on the text it shows while the reading is pending

### Requirement: With the every-point-of-sale scope the fast route is disabled with a reason of its own, and the assisted route is not

The panel SHALL disable the fast route of the route selector while the every-point-of-sale scope is selected, stating that the fast route works over one concrete point of sale, and MUST NOT state that the semantic path is switched off, which would be false; the assisted route MUST remain selectable on the terms of its own switch.

The two statements are different facts and are told apart on purpose: one is about **reachability** — the fast route does not accept this scope — and the other is about a **switch**. Reporting the first as the second is the class of false statement this capability exists to stop making.

When the assisted route is the only one that can serve the scope and its switch is off, the panel MUST state that the scope needs the assisted answer and that the assisted answer is switched off, rather than leaving both options of the route selector disabled with nothing explaining it. Any text stating why the assisted answer is unavailable MUST NOT claim it is unavailable "at this shop" while this scope is selected, because in this scope there is no shop to speak of.

#### Scenario: The fast route is disabled for a reason of scope
- **WHEN** the every-point-of-sale scope is selected
- **THEN** the fast option of the route selector is disabled with a reason stating that it works over one concrete point of sale
- **AND** that reason does not state that the semantic path is switched off
- **AND** the assisted route becomes the route the next search will take

#### Scenario: The assisted route stays available in the every-point-of-sale scope
- **WHEN** the every-point-of-sale scope is selected and the assisted answer is switched on
- **THEN** the assisted option of the route selector is enabled
- **AND** it is not disabled with an unstated reason

#### Scenario: A scope no route can serve is stated, not left silent
- **WHEN** the every-point-of-sale scope is selected and the assisted answer is switched off
- **THEN** the panel states that this scope needs the assisted answer and that the assisted answer is switched off
- **AND** the reason shown does not claim the assisted answer is unavailable at this shop

### Requirement: Selected filters that admitted almost nothing are a fifth way of showing nothing, and say so

The panel SHALL distinguish, from the four ways of showing nothing it already tells apart, a fifth: the selected filters admitted fewer candidates than the confidence rule needs, over a query whose description did find something.

It MUST state that pieces matching the description exist but none satisfies the selected filters, and MUST offer clearing them as the remedy. It MUST NOT state that nothing matching the description was found, which is what the abstention says and would be false here.

This distinction MUST be available on both routes of the selector, because the backend reports it on both.

#### Scenario: A narrow filter is told apart from an unanswerable query
- **WHEN** the response declares that the selected filters admitted few candidates
- **THEN** the panel states that pieces matching the description exist but none satisfies the selected filters
- **AND** it does not state that nothing matching the description was found
- **AND** it offers clearing the filters as the remedy

#### Scenario: An abstention still says what it always said
- **WHEN** the response reports the retrieval as low confidence with no results and declares no narrow filter
- **THEN** the panel states that nothing matching was found
- **AND** it invites the operator to rephrase

### Requirement: Every state the assisted answer can return is told apart on screen

The panel SHALL distinguish, on screen, every state the assisted route can return, because a single empty list or a single failure notice would state something untrue in most of them. Beyond the ways of showing nothing the semantic route already distinguishes, the assisted route adds these, and each MUST carry its own wording:

- the query is not about jewellery at all — a refusal, worded as such;
- the query is about jewellery but asks for a kind of object this catalogue does not carry — a **different** refusal, worded differently, because what an operator says to a customer differs between a trade the shop does not practise and a piece the shop does not stock;
- the query did not carry enough to search — the clarification question the service returned is shown verbatim and the input regains focus, since returning to the query is the action the question asks for;
- the classifier ran, admitted the query and could not route it — the operator is invited to phrase it another way, and the results that were retrieved are shown;
- the classifier did not run at all — the operator is told that the assisted answer is unavailable and is **NOT** invited to rephrase, because the cause is not the wording and asking would blame the operator for a missing capability;
- the route consulted the knowledge corpus and returned prose with no pieces — this MUST NOT be presented as an empty result set, because the answer is what was asked for;
- the service withheld the argument, and the case where no generation ran at all, which MUST stay distinguishable from it.

When a result set is shown without prose, the citations the response carries MUST NOT be rendered, because a citation without a claim attributes nothing.

None of these states MUST be presented as an application error, and a state this screen does not recognise MUST degrade to a neutral statement rather than break the screen.

While an assisted request is in flight the panel MUST show a loading state and MUST state that the answer may take a few seconds.

#### Scenario: A query that is not about jewellery is refused in its own words
- **WHEN** the response reports the query as out of domain
- **THEN** the panel states that this is not a jewellery question
- **AND** the wording differs from the one used for a piece the catalogue does not carry

#### Scenario: A piece the catalogue does not carry is refused in different words
- **WHEN** the response reports the query as asking for something not in the catalogue
- **THEN** the panel states that this kind of piece is not carried
- **AND** the wording differs from the one used for a query that is not about jewellery

#### Scenario: A clarification question is shown verbatim and returns focus
- **WHEN** the response carries a clarification question
- **THEN** the panel shows that question as the service worded it
- **AND** the query input regains focus
- **AND** no result list is shown

#### Scenario: An unrouted query invites rephrasing with its results on screen
- **WHEN** the response reports the query as admitted, carries results and carries no argument
- **THEN** the panel invites the operator to phrase it another way
- **AND** the results are shown
- **AND** no citation is rendered

#### Scenario: A classifier that did not run is not the operator's fault
- **WHEN** the response reports the intent as unclassified, carries results and carries no argument
- **THEN** the panel states that the assisted answer is unavailable
- **AND** it does not invite the operator to rephrase
- **AND** no citation is rendered

#### Scenario: A knowledge answer with no pieces is not an empty result set
- **WHEN** the response carries an argument and no pieces because the route consulted the knowledge corpus
- **THEN** the panel shows the argument and its citations
- **AND** it does not state that there are no results

#### Scenario: A withheld argument is told apart from no generation at all
- **WHEN** the response reports that the service withheld the argument
- **THEN** the panel says so and ends in an action
- **AND** the wording differs from the one used when no generation ran

#### Scenario: The assisted route states that it may take seconds
- **WHEN** an assisted request is in flight
- **THEN** the panel shows a loading state
- **AND** it states that the answer may take a few seconds

### Requirement: Warnings that describe the query are shown, and warnings that describe one piece are not

The panel SHALL render the warning codes that describe the query — a refused query, a question the documentation does not cover, filters that admitted few candidates — and MUST NOT render the warning codes that describe a single piece, because the service computes those for the first member of the first group only and presenting them above a list of many pieces would assert something untrue about the rest.

The partition MUST be by the subject of the warning and never by which list it arrived in, since refusal codes and piece codes travel in the same list.

A code this screen does not know MUST fall back to a neutral label, and the raw code MUST NOT be shown to the operator, exactly as this capability already requires elsewhere.

Nothing is lost by not rendering a piece warning here: opening the sale card issues its own request anchored to that piece, and its warnings are computed for it.

#### Scenario: A query warning is rendered
- **WHEN** the response carries the code declaring that the documentation does not cover the question
- **THEN** the panel renders its Spanish wording

#### Scenario: A piece warning is not rendered in the list
- **WHEN** the response carries a code that describes one piece
- **THEN** the panel does not render it above the result list

#### Scenario: An unknown code degrades to a neutral label
- **WHEN** the response carries a query warning code this screen does not know
- **THEN** it is rendered with a neutral label
- **AND** the raw code is not shown

### Requirement: A citation the integrity gate withdrew is stated, discreetly, and never as a suspicion

The panel SHALL state, when the response carries an argument whose declared citations were withdrawn by the integrity gate, that the claim has no verifiable source, and MUST do so as a single discreet line beside the argument rather than as an alert.

The wording MUST NOT suggest an invention: the fragment existed and was in the context, and what could not be verified is the model's own account of which span it supported. The measured frequency of this state in the free-query mode is about one in four knowledge answers, which makes it a normal state rather than an exception, and an alert at that frequency would train the operator to ignore it.

It MUST stay distinguishable from a route where having no citation is correct, and from the case where the whole argument was withheld.

#### Scenario: A withdrawn citation is stated discreetly
- **WHEN** the response carries an argument and no citations because the gate withdrew them
- **THEN** the panel states beside the argument that there is no verifiable source
- **AND** it does not render the statement as an alert

#### Scenario: The wording does not accuse the model of inventing
- **WHEN** the statement is rendered
- **THEN** it does not describe the citation as invented or as a possible hallucination

#### Scenario: A catalogue route with no citations is not the same state
- **WHEN** the response carries an argument for a route where the corpus is not consulted
- **THEN** the panel does not state that there is no verifiable source

### Requirement: A result row states what else its family carries

The panel SHALL state, for a result of the assisted route belonging to a group of more than one member, what other variants the family carries, using the variant label of each member and falling back to its SKU when the label is absent, so that the grouping that spared the list from being flooded stops being invisible to the operator.

A group of a single member MUST produce no such statement, and the row MUST NOT be padded with an empty one.

The statement MUST announce the family and MUST NOT offer a sale action for any member other than the one the row is about: the row announces, the sale card unfolds. It MUST NOT re-sort, re-group or otherwise alter the order the backend supplied.

#### Scenario: A row announces its family
- **WHEN** a result of the assisted route belongs to a group of several members
- **THEN** the row states what other variants the family carries

#### Scenario: A missing variant label degrades to the SKU
- **WHEN** a member of the group has no variant label
- **THEN** it is named by its SKU

#### Scenario: A single-member group says nothing
- **WHEN** a result belongs to a group of exactly one member
- **THEN** the row states nothing about a family

#### Scenario: The row does not sell
- **WHEN** a row states what its family carries
- **THEN** it offers no sale action for any member other than the one the row is about

### Requirement: The stock label names the shop, and says so plainly when there is no shop to name

The panel SHALL name the point of sale in the stock label of every result — the quantity followed by the name of that shop — because with more than one shop in play "this shop" is ambiguous and an ambiguity in a stock figure is what costs a sale.

When the search is scoped to every point of sale, the label MUST state that a shop must be selected to read stock, and MUST NOT show a zero, which would be a false statement. Each product MUST appear once in that scope, however many shops carry it, because a product listed three times is a statement about shops rather than about the catalogue.

With no point of sale selected the action that opens the sale card MUST be disabled, because the card requires one, and closing that ambiguity at the door is better than carrying it into the card.

Changing the selected point of sale MUST clear the displayed results and MUST NOT call any model. It previously read that changing it refreshes the stock figures, which was never what the panel did and which no test asserted: the results are cleared, because the candidate cache is keyed on the point of sale and re-running the search would charge an embedding the operator did not ask for. A figure that is not on screen cannot be refreshed, so the clause is withdrawn rather than reinterpreted.

#### Scenario: The label names the shop
- **WHEN** a result is shown for a selected point of sale
- **THEN** the stock label states the quantity and the name of that point of sale

#### Scenario: Without a shop the label does not show a zero
- **WHEN** the search is scoped to every point of sale
- **THEN** the stock label states that a point of sale must be selected to read stock
- **AND** it does not show a quantity

#### Scenario: Without a shop each product is listed once
- **WHEN** the search is scoped to every point of sale and a product is carried by more than one shop
- **THEN** that product appears exactly once in the results

#### Scenario: Without a shop the sale card is not reachable
- **WHEN** the search is scoped to every point of sale
- **THEN** the action that opens the sale card is disabled

#### Scenario: Changing shop clears rather than refreshes, and calls no model
- **WHEN** the operator changes the selected point of sale with results on screen
- **THEN** the displayed results are cleared
- **AND** no request is issued to the assisted answer route
