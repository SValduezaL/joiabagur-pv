## ADDED Requirements

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

## MODIFIED Requirements

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
