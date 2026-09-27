## ADDED Requirements

### Requirement: The sale card is a screen of its own, anchored to one piece and one point of sale, reachable from the three places the operator already is

The frontend SHALL expose the sale card on a lazily loaded route of its own under the sales tree, anchored to one product identifier, and MUST reach it from the assisted search result row, from the product chosen on the manual sale page, and from the piece resolved by scanning a code.

The point of sale MUST travel to the card through navigation state, the mechanism the scanning, image recognition and assisted search pages already use to hand a product over. Only the assisted search panel and the manual sale page hold one to pass: the scanning page has never had a point of sale of its own, so nothing travels from it. When the route is opened without one, the card MUST offer the same role-resolved point-of-sale selector the assisted search panel offers, and MUST NOT issue any request until one is chosen.

The card MUST NOT be reachable from the catalog's product detail page, which is an administration screen with no point of sale to scope the request to.

The assisted search result row MUST gain this as a secondary action that neither replaces nor blocks its existing selection for sale.

#### Scenario: The card is reached from the assisted search results
- **WHEN** the operator activates the sale card action on a result row
- **THEN** the card for that product opens for the point of sale the panel was scoped to

#### Scenario: The card is reached from a scanned piece
- **WHEN** the operator scans a code and activates the sale card action
- **THEN** the card for the resolved product opens with the role-resolved point-of-sale selector, because the scan flow has not chosen a point of sale yet

#### Scenario: The card is reached from the manual sale page
- **WHEN** a product is selected on the manual sale page and the operator activates the sale card action
- **THEN** the card for that product opens for the point of sale selected on that page

#### Scenario: Opened cold, nothing is requested until a point of sale is chosen
- **WHEN** the card route is opened with no point of sale in navigation state
- **THEN** a point-of-sale selector is displayed according to the caller's role
- **AND** no request is issued until one is chosen

### Requirement: Exactly one assist request is issued on entry to the card, a failed one is never retried automatically, and only an explicit act issues another

The card SHALL issue exactly one sale assistance request on entry to each visit, and MUST NOT issue another as a consequence of re-rendering, of the response arriving, or of any failure.

A failed request MUST offer the operator an explicit retry and MUST NOT be retried on its own, because the route costs a paid provider call, its budget is limited per user and per minute, and its responses cannot be cached.

Leaving the card and entering again MUST count as another visit and MUST issue another request. A response that is no longer the current one MUST be discarded rather than rendered.

Naming a different point of sale while the card is served MUST issue another request, scoped to the shop just named. It is an explicit act of the operator, like navigating here in the first place, and not one of the three causes above; the card it asks for is a different card, and leaving the previous shop's price, units and variants under the new shop's name would be the screen stating something false. Within one visit, the only acts that MAY issue a further request are this one, the explicit retry of a failed request, and the customer's question that the next requirement governs.

While the request is in flight the card MUST display a loading state rather than an empty screen.

#### Scenario: Entering the card issues one request
- **WHEN** the operator opens the card for a piece
- **THEN** exactly one sale assistance request is issued

#### Scenario: A failure is not retried on its own
- **WHEN** the sale assistance request fails
- **THEN** no further request is issued without an explicit act by the operator
- **AND** a retry control is offered

#### Scenario: A stale response never overwrites a newer one
- **WHEN** a response arrives for a request that is no longer the current one
- **THEN** it is discarded
- **AND** the displayed content does not change

#### Scenario: Naming a different point of sale asks again
- **WHEN** the operator names a different point of sale while the card is served
- **THEN** another sale assistance request is issued, scoped to the shop just named
- **AND** the content served for the previous shop is replaced rather than left on screen

### Requirement: The customer's question is a second explicit request, bounded, and never written into the address of the page

The card SHALL send the customer's question as a second sale assistance request, issued only on an explicit act, and MUST send it in the request body, never as part of the address of the page nor as part of the navigation state that the browser records in its history.

The question MUST be rejected before being sent when it is blank or longer than the maximum the backend declares for it, five hundred characters.

The card MUST offer a small set of suggested questions drawn from the situations the knowledge corpus covers, each of which fills the field and sends it in a single act, so that what can be asked is expressed by the interface rather than left for each operator to discover.

The question MUST NOT be preserved between visits to the card.

#### Scenario: Asking sends one further request
- **WHEN** the operator submits a question about the piece
- **THEN** exactly one further sale assistance request is issued
- **AND** the question travels in its body

#### Scenario: The question is never in the address of the page
- **WHEN** a question has been asked
- **THEN** the address of the page contains no part of it
- **AND** no entry recorded in the browser's history contains it

#### Scenario: A question over the limit is refused before being sent
- **WHEN** the operator submits a question longer than the declared maximum
- **THEN** no request is issued
- **AND** the operator is told the question is too long

#### Scenario: A suggested question asks in one act
- **WHEN** the operator activates one of the suggested questions
- **THEN** the field is filled with it
- **AND** exactly one request is issued

#### Scenario: A new visit starts with no question
- **WHEN** the operator leaves the card and opens it again
- **THEN** the question field is empty

### Requirement: The closed warning vocabulary is translated on this screen, and a code this screen does not know degrades the row instead of breaking it

The card SHALL render every warning code the backend emits as Spanish written here, MUST NOT render a raw code to the operator, and MUST render a code it does not know with a neutral label rather than omitting the row or failing.

The translations MUST live in a module of their own, exported and tested directly, rather than inline in the components, because the vocabulary is closed but versioned and a new value must not be able to break a row of the screen.

The card MUST NOT translate the two router refusal codes, which this capability's two routes cannot emit because the intent classifier runs only on the free-query mode: they fall to the neutral label, and that is what is verified.

The card MUST NOT add a warning the backend did not emit, and MUST NOT remove one it did.

#### Scenario: A known code is shown in Spanish
- **WHEN** the response carries a warning code this screen knows
- **THEN** its Spanish text is displayed
- **AND** the raw code is not displayed

#### Scenario: An unknown code falls back to a neutral label
- **WHEN** the response carries a warning code this screen does not know
- **THEN** it is displayed with a neutral label
- **AND** the remaining warnings are displayed normally

#### Scenario: A router refusal code falls back like any other unknown
- **WHEN** the response carries either of the two router refusal codes
- **THEN** it is displayed with the neutral label

### Requirement: A missing size label is shown as an attribute of the piece and never as a warning

The card SHALL display the missing-size-label code as a neutral line beside the piece's SKU, MUST NOT place it among the warnings, and MUST NOT suppress it.

It fires on more than half of the cards and is almost perfectly anti-correlated with belonging to a family, so it states the enrichment status of the catalog rather than a fact about the piece in front of the customer. Rendered as an alert it would crowd out the two stock warnings, which fire on a few percent of cards and are the ones that can cost a sale.

#### Scenario: The missing size label is an attribute
- **WHEN** the response carries the missing-size-label code
- **THEN** it is displayed beside the SKU as an attribute of the piece
- **AND** it does not appear among the warnings

#### Scenario: The stock warnings remain warnings
- **WHEN** the response carries a stock warning and the missing-size-label code
- **THEN** the stock warning is displayed among the warnings

### Requirement: A family of several members requires the operator to name the variant before selling

The card SHALL display one row per member when the group carries two or more of them, MUST preselect none of them, and MUST NOT offer any action that starts a sale without naming a member.

Each row MUST carry the member's variant label, its price and the units that point of sale holds, and MUST mark a member with no stock. A member whose variant label is absent MUST fall back to its SKU rather than leaving the row unidentified. The anchored member MUST be marked as such.

When the group carries exactly one member the direct sale action MUST be offered, because there is nothing to choose between.

The card MUST NOT re-sort the members: the order is the one the backend delivered.

#### Scenario: Several members are offered with no preselection
- **WHEN** the group carries three members
- **THEN** three rows are displayed, each with its own sale action
- **AND** no member is preselected
- **AND** no sale action exists that does not name a member

#### Scenario: A member with no variant label is still identifiable
- **WHEN** a member of the group carries no variant label
- **THEN** its row identifies it by its SKU

#### Scenario: A single member restores the direct action
- **WHEN** the group carries exactly one member
- **THEN** the direct sale action is offered

### Requirement: The chosen piece travels to the manual sale page through navigation state

The card SHALL hand the member the operator chose to the manual sale page through navigation state, the mechanism the scanning, image recognition and assisted search pages already use, and MUST NOT duplicate the payment method, quantity, price or stock logic that page owns.

The identifier handed over MUST be that of the member whose action was activated, and never that of the anchored piece when a different member was chosen.

#### Scenario: The chosen member reaches the till
- **WHEN** the operator activates the sale action of a member that is not the anchored piece
- **THEN** the manual sale page opens preselecting that member
- **AND** it does not preselect the anchored piece

### Requirement: The six states of the argument are told apart on screen as five messages, and the two that differ in provenance are never merged

The card SHALL render the state of the argument as one of five distinct messages over the six states the backend reports, and MUST keep all six distinguishable in the rendered document so that each can be asserted separately.

The state in which the AI path degraded and the state in which no generation ran MUST NOT share a message: in the first the group, the materials and the match reasons come from the transactional catalog and there are no citations, and in the second they come from the index, so a single message would misstate where what is displayed came from.

The two states in which an argument was withheld MAY share a message, because nothing the operator can do differs between them.

Every message for a state without an argument MUST tell the operator what to do next rather than only stating the absence. The group, the warnings and the piece MUST remain displayed in every state in which the backend answered.

#### Scenario: A generated argument is displayed
- **WHEN** the state of the argument is generated
- **THEN** the argument is displayed

#### Scenario: A degraded card and an ungenerated argument read differently
- **WHEN** one response declares the AI path unavailable and another declares that no generation ran
- **THEN** the two messages displayed are different
- **AND** the first states that what is displayed comes from the catalog

#### Scenario: A withheld argument says what to do next
- **WHEN** the argument was withheld by the AI service or because a placeholder remained
- **THEN** the message states that no argument could be supported and tells the operator what to do next
- **AND** the group and the warnings remain displayed

#### Scenario: A piece with no stock explains itself
- **WHEN** the argument was withheld because the anchored piece has no stock
- **THEN** the message says so and announces the alternatives

### Requirement: Citations carry their scope, resolve to no link, and are not displayed when the argument is not

The card SHALL display each citation with its document title, its section title and its snippet, collapsed by default, and MUST distinguish a citation whose claim is a commitment of the establishment from one that states a fact of the world, both visually and in words.

A citation of establishment scope MUST state that it is to be confirmed in store before being passed to a customer.

The card MUST NOT resolve a citation into a link and MUST NOT display its raw identifier as the only thing the operator can read, because no route serves the corpus and a citation that cannot be read verifies nothing.

The card MUST NOT display citations when the argument was not delivered, because they are the ones that argument used and presenting sources for a text the operator cannot read attributes nothing.

#### Scenario: An establishment claim is marked differently from a general one
- **WHEN** the response carries one citation of establishment scope and one of general scope
- **THEN** the two are distinguishable on screen
- **AND** the establishment one states that it is confirmed in store

#### Scenario: Citations are readable without a link
- **WHEN** a citation is expanded
- **THEN** its document title, its section title and its snippet are displayed

#### Scenario: A withheld argument shows no citations
- **WHEN** the argument was not delivered
- **THEN** no citation is displayed

### Requirement: Substitutes are requested from the anchored member's stock, never when the AI path is unavailable, and their four outcomes are told apart

The card SHALL request substitutes when and only when the anchored member carries no stock and the response declares the AI path available, and MUST NOT request them on a degraded card, where the outcome would be an unavailable AI service with certainty.

The trigger MUST be the anchored member's stock and MUST NOT be the state of the argument, because the anchored member's stock is present in every state the backend served while that state only reports the absence of stock when no question was asked.

The four outcomes MUST be rendered as four different messages. A product the AI service cannot process MUST be told apart from a service that did not answer. A page shorter than the one requested MUST be declared rather than padded, and the results MUST be displayed in the order received.

#### Scenario: An out-of-stock piece is offered alternatives
- **WHEN** the anchored member carries no stock and the AI path is available
- **THEN** substitutes are requested exactly once
- **AND** the results are displayed in the order received

#### Scenario: A piece with stock asks for nothing
- **WHEN** the anchored member carries stock
- **THEN** no substitutes request is issued

#### Scenario: A degraded card asks for nothing
- **WHEN** the anchored member carries no stock and the response declares the AI path unavailable
- **THEN** no substitutes request is issued
- **AND** the card explains why no alternatives are offered

#### Scenario: A product not yet indexed is not an outage
- **WHEN** the outcome states the product cannot be processed
- **THEN** the message says the piece is not ready yet
- **AND** it differs from the message for an unavailable service

#### Scenario: A short page is declared
- **WHEN** fewer substitutes are returned than the page requested
- **THEN** the number returned is stated
- **AND** the list is not padded

### Requirement: Every failure of the two routes becomes a sentence on screen and never an application error

The card SHALL translate every failure of the two backend routes into a typed outcome that is rendered as a true sentence, and MUST NOT let any of them surface as an application error or an empty screen.

Exceeding the request budget MUST be told apart from an unavailable AI service, because one is the system protecting itself and the operator only has to wait. A point of sale the caller may not use, and a piece that point of sale does not carry, MUST each read as themselves rather than as a generic failure.

Neither the customer's question nor the resolved argument MUST be written to the browser console at any level.

#### Scenario: Exceeding the budget is told apart from an outage
- **WHEN** the backend refuses the request for exceeding the rate limit
- **THEN** the operator is told to wait a few seconds
- **AND** the message differs from the one for an unavailable AI service

#### Scenario: A piece the shop does not carry says so
- **WHEN** the backend answers that the point of sale does not carry the piece
- **THEN** the card says so
- **AND** no application error is displayed

#### Scenario: A forbidden point of sale says so
- **WHEN** the backend refuses the point of sale for this caller
- **THEN** the card says the point of sale is not available to them

#### Scenario: Nothing sensitive reaches the console
- **WHEN** a card has been served with a question and a generated argument
- **THEN** neither the question nor the argument appears in the browser console at any level
