## MODIFIED Requirements

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

## ADDED Requirements

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

The panel SHALL state, before the operator issues any search, whether each of the two AI paths is available for the selected point of sale, reading it from a route that calls no model and consumes no request quota.

When the assisted path is unavailable, its option in the route selector MUST be disabled and the reason MUST be stated, rather than letting the operator select an option that is guaranteed to fail.

This statement MUST be independent of, and MUST NOT be replaced by, whatever notice appears with the results afterwards: one describes availability before acting, the other describes what happened during a request. In particular, a response reporting an unclassified intent means the AI answered and the classifier did not run, which no switch announces.

#### Scenario: Availability is stated before searching
- **WHEN** the panel finishes loading
- **THEN** it states whether the fast path and the assisted path are available
- **AND** it does so before any search has been issued

#### Scenario: An unavailable assisted path disables its option with a reason
- **WHEN** the assisted path is unavailable for the selected point of sale
- **THEN** its option in the route selector is disabled
- **AND** the reason is stated

#### Scenario: Reading availability costs nothing
- **WHEN** the panel reads availability
- **THEN** no model is called
- **AND** no request quota is consumed

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

When the search is scoped to every point of sale, the label MUST state that a shop must be selected to read stock, and MUST NOT show a zero, which would be a false statement.

With no point of sale selected the action that opens the sale card MUST be disabled, because the card requires one, and closing that ambiguity at the door is better than carrying it into the card.

Changing the selected point of sale MUST refresh the stock figures and MUST NOT call any model.

#### Scenario: The label names the shop
- **WHEN** a result is shown for a selected point of sale
- **THEN** the stock label states the quantity and the name of that point of sale

#### Scenario: Without a shop the label does not show a zero
- **WHEN** the search is scoped to every point of sale
- **THEN** the stock label states that a point of sale must be selected to read stock
- **AND** it does not show a quantity

#### Scenario: Without a shop the sale card is not reachable
- **WHEN** the search is scoped to every point of sale
- **THEN** the action that opens the sale card is disabled

#### Scenario: Changing shop calls no model
- **WHEN** the operator changes the selected point of sale with results on screen
- **THEN** the stock figures are refreshed
- **AND** no request is issued to the assisted answer route
