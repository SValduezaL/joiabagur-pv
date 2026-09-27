## ADDED Requirements

### Requirement: Sale assistance and substitutes are exposed through two authenticated routes anchored to a product

The backend SHALL expose exactly two operations for the sale card, both anchored to one product and both under the AI namespace without a version segment: a write-free POST that returns the sale assistance for that product, and a GET that returns its substitutes.

Both operations MUST require authentication. The sale assistance request MUST carry the point of sale in its body and MAY carry a question about the product; the question MUST travel in the request body and MUST NOT be accepted as part of the URL, because it is free text written about a customer and a URL is recorded by proxies, browsers and caches. A question, when present, MUST NOT be blank and MUST be bounded by the maximum the frozen AI contract declares for its own query field. The substitutes request MUST carry the point of sale and MAY carry a page size, bounded by a configured maximum.

Request validation MUST be invoked explicitly by the endpoint, and an invalid request MUST be rejected before any call is issued to the AI service.

A free question with no product and the multi-turn agent route MUST NOT be exposed by this capability: their generated argument speaks about several products with the same price and stock placeholders, so no single product exists to resolve them against.

#### Scenario: A sale assistance request is served
- **GIVEN** an authenticated caller who may use a point of sale that carries the product
- **WHEN** the caller posts a sale assistance request for that product, with or without a question
- **THEN** the endpoint answers with the group of the product, the warnings, the citations and the state of the argument

#### Scenario: The question never travels in the URL
- **WHEN** a sale assistance request carries a question
- **THEN** the question is read from the request body
- **AND** the route accepts no question as a query parameter

#### Scenario: An invalid request is rejected before any work is done
- **WHEN** a request carries a blank question, a question longer than the contract allows, or a page size above the configured maximum
- **THEN** the endpoint answers with a validation error
- **AND** no call is issued to the AI service

#### Scenario: An unauthenticated request is refused
- **WHEN** an unauthenticated caller requests either operation
- **THEN** the endpoint refuses it
- **AND** no call is issued to the AI service

#### Scenario: No route exists for a free question or for the agent
- **WHEN** the routes of this capability are enumerated
- **THEN** none of them forwards a question without a product
- **AND** none of them forwards a multi-turn transcript

### Requirement: Every request is scoped to one point of sale and to a product that point of sale carries, before the AI service is called

The system SHALL require a concrete point of sale on both operations, SHALL validate it with the rule of assisted search, and MUST NOT call the AI service for a request it is about to refuse.

A request without a point of sale MUST be rejected as invalid. An inactive point of sale MUST be refused for every role. An operator MUST be forbidden when the point of sale is not one they are assigned to; an administrator MAY use any active point of sale.

The anchored product MUST be refused as not found when it is unknown, inactive, or has no active inventory record at the requested point of sale, for every role, because the scope of the request is one concrete shop and the inventory assignment is what determines that a product belongs to it. The quantity of that record MAY be zero: a product the shop carries and has run out of is still the shop's product.

The point-of-sale scope sent to the AI service MUST come from the validated scope and MUST NOT be taken from the request body.

#### Scenario: An operator cannot use a point of sale they are not assigned to
- **WHEN** an operator requests either operation for a point of sale outside their assignments
- **THEN** the request is forbidden
- **AND** no call is issued to the AI service

#### Scenario: A product the shop does not carry is not found
- **GIVEN** an operator assigned to a point of sale
- **WHEN** the operator requests either operation for a product with no active inventory record at that point of sale
- **THEN** the request is answered as not found
- **AND** no call is issued to the AI service

#### Scenario: A product the shop has run out of is still served
- **GIVEN** a product whose active inventory record at the point of sale has a quantity of zero
- **WHEN** either operation is requested for it
- **THEN** the request is served

#### Scenario: An administrator may use any active point of sale
- **WHEN** an administrator requests either operation for an active point of sale that carries the product
- **THEN** the request is served for that point of sale

#### Scenario: An inactive point of sale is refused for every role
- **WHEN** any caller requests either operation for an inactive point of sale
- **THEN** the request is refused
- **AND** no call is issued to the AI service

### Requirement: The backend is the authority on the members of the group

The system SHALL hydrate every member of the group returned by the AI service against the transactional catalog of the requested point of sale, with a single set-based query, and MUST take the name, price, quantity, photo and collection from that hydration rather than from the AI response.

A member MUST be dropped when the point of sale does not carry it, when its inventory record is inactive, or when the product is inactive. A member with a quantity of zero MUST be kept and marked as having no stock. An identifier that is not a valid product identifier MUST be dropped and logged.

The surviving members MUST keep the order in which the AI service returned them and MUST NOT be re-sorted. The anchored product MUST be marked as such. When the identifier the index reports differs from the one the catalog holds, the catalog value MUST prevail and the divergence MUST be logged.

#### Scenario: Price and quantity come from the catalog of that shop
- **WHEN** the group is built for a served sale assistance
- **THEN** the price and quantity of each member come from the catalog and from the inventory of the requested point of sale
- **AND** they do not come from the AI response

#### Scenario: A member the shop does not carry is dropped
- **GIVEN** the AI service returns a family with a member the point of sale does not carry
- **WHEN** the group is built
- **THEN** that member does not appear

#### Scenario: The order of the AI service is kept and the anchor is marked
- **WHEN** the group is built
- **THEN** the surviving members appear in the order the AI service returned them
- **AND** exactly one member is marked as the anchored product

#### Scenario: Hydration does not query per member
- **WHEN** a group with several members is hydrated
- **THEN** the number of queries issued does not grow with the number of members

### Requirement: The variants warning reflects what the point of sale carries

The system SHALL keep the warning that the family has variants only when two or more members of the group survive hydration, and MUST remove it otherwise. In the served path the system MUST NOT add that warning when the AI service did not emit it; it MAY only remove it.

The warning describes a family, and the family the index knows can contain members the shop does not carry. Keeping it on a group of one would ask the operator to choose among a single option, which is the failure the nullable family of the contract was introduced to remove.

#### Scenario: A family reduced to one member by hydration loses the variants warning
- **GIVEN** the AI service returns a family of three members with the variants warning
- **AND** the point of sale carries only the anchored product
- **WHEN** the sale assistance is served
- **THEN** the group has one member
- **AND** the variants warning is absent

#### Scenario: A family that keeps two members keeps the warning
- **GIVEN** the AI service returns a family with the variants warning
- **AND** the point of sale carries two of its members
- **WHEN** the sale assistance is served
- **THEN** the variants warning is present

### Requirement: Stock warnings are computed after hydration and never taken from the AI response

The system SHALL compute the two stock warnings from the hydrated quantities of the requested point of sale and MUST NOT derive them from any value in the AI response. The critical-stock warning MUST be emitted when the anchored product has at least one unit and no more than the configured critical threshold, two by default. The members-out-of-stock warning MUST be emitted when another member of the hydrated group has a quantity of zero.

A quantity of zero on the anchored product MUST NOT be reported as critical stock: it is a state of the member, carried as having no stock, and it governs the argument and the substitutes block rather than a warning.

The warnings MUST be ordered as the codes received from the AI service, adjusted by the variants rule, followed by the two stock warnings. A code the backend does not recognise MUST be passed through unchanged, because the vocabulary is closed but versioned.

#### Scenario: Two units raise critical stock
- **GIVEN** the anchored product has two units at the point of sale
- **WHEN** the sale assistance is served
- **THEN** the critical-stock warning is present

#### Scenario: Three units do not raise critical stock with the default threshold
- **GIVEN** the anchored product has three units at the point of sale and the threshold is the default
- **WHEN** the sale assistance is served
- **THEN** the critical-stock warning is absent

#### Scenario: Zero units are a state and not a warning
- **GIVEN** the anchored product has no units at the point of sale
- **WHEN** the sale assistance is served
- **THEN** the critical-stock warning is absent
- **AND** the anchored member is marked as having no stock

#### Scenario: Another member without stock raises the family warning
- **GIVEN** another member of the group is carried at the point of sale with a quantity of zero
- **WHEN** the sale assistance is served
- **THEN** the members-out-of-stock warning is present

#### Scenario: Stock warnings do not come from the AI response
- **GIVEN** the AI response carries no stock warning
- **AND** the hydrated quantities satisfy both stock rules
- **WHEN** the sale assistance is served
- **THEN** both stock warnings are present

#### Scenario: An unknown code is passed through
- **GIVEN** the AI response carries a warning code the backend does not recognise
- **WHEN** the sale assistance is served
- **THEN** that code is present in the response unchanged

### Requirement: Price and stock placeholders are resolved against the anchored product

The system SHALL resolve the price placeholder and the stock placeholder of the generated argument against the anchored product and nothing else: the price placeholder MUST be replaced by the catalog price of the anchored product formatted as Spanish currency, and the stock placeholder MUST be replaced by the quantity of the anchored product at the requested point of sale written as a whole number.

Only the two exact placeholder tokens MUST be replaced. Any remaining double brace after replacement, whether a variant spelling, an unknown name or a malformed token, MUST be treated as an unresolved placeholder.

A resolution attempted without an anchored product MUST withhold the argument, because a placeholder carries no reference to a product and assigning it to one of several would put the price of one piece next to the description of another.

#### Scenario: Both placeholders are replaced by the values of the anchored product
- **GIVEN** an anchored product priced at thirty-nine euros and ninety cents with three units at the point of sale
- **WHEN** the generated argument carries both placeholders
- **THEN** the argument delivered contains that price formatted as Spanish currency and the whole number three
- **AND** it contains no placeholder

#### Scenario: A variant spelling of a placeholder is not replaced
- **WHEN** the generated argument carries a placeholder spelled differently from the two exact tokens
- **THEN** that placeholder is treated as unresolved

#### Scenario: No anchored product means no resolution
- **WHEN** a resolution is attempted without an anchored product
- **THEN** the argument is withheld

### Requirement: The state of the argument is explicit, and an unresolved placeholder withholds the argument and never the response

The system SHALL report the state of the argument as one value of a closed set, decided in this order, the first that applies winning: unavailable when the AI path degraded, not generated when the AI service ran no generation, withheld by the AI service when it ran the generation and returned no argument, withheld because out of stock under the rule for an anchored product without stock, withheld because unresolved when a placeholder remains after resolution, and generated otherwise.

In every state but generated the argument MUST be absent from the response. The group, the warnings and the citations MUST be delivered in every state in which the AI service answered. The raw template MUST NOT reach any field of the response nor any log line.

When the backend withholds an argument the AI service published, the citations MUST remain the ones that argument declared having used. This set can be smaller than the one the AI service returns when it withholds the argument itself, and the backend cannot reconstruct the difference.

#### Scenario: An unresolved placeholder withholds the argument and keeps the rest
- **GIVEN** the AI service returns an argument carrying an unknown placeholder, a group, warnings and citations
- **WHEN** the sale assistance is served
- **THEN** the argument is absent and its state is withheld because unresolved
- **AND** the group, the warnings and the citations are present
- **AND** the raw template appears in no field of the response and in no log line

#### Scenario: No generation and a withheld generation are told apart
- **GIVEN** the AI service ran no generation for one request and ran it and returned no argument for another
- **WHEN** both are served
- **THEN** the first reports the state not generated
- **AND** the second reports the state withheld by the AI service

#### Scenario: A resolved argument is reported as generated
- **WHEN** every placeholder of the argument is resolved
- **THEN** the argument is present and its state is generated

### Requirement: The argument of an anchored product without stock is withheld only when no question was asked

The system SHALL withhold the generated argument when the anchored product has no units at the requested point of sale and the request carries no question, reporting the state withheld because out of stock. When the request carries a question, the argument MUST be delivered with the stock placeholder resolved to zero.

The argument of a product without a question is a sales argument, and the model writes it without knowing the stock: offered for a product the shop cannot sell today, it argues for the sale the card is about to replace with substitutes. An answer to a question about the product remains valid whether or not the shop has units of it.

#### Scenario: No question and no stock withholds the argument
- **GIVEN** the anchored product has no units at the point of sale
- **WHEN** the sale assistance is requested without a question
- **THEN** the argument is absent and its state is withheld because out of stock

#### Scenario: A question about a product without stock is still answered
- **GIVEN** the anchored product has no units at the point of sale
- **WHEN** the sale assistance is requested with a question
- **THEN** the argument is present with the stock placeholder resolved to zero

### Requirement: Citations carry their scope and are passed through as the AI service declared them

The system SHALL deliver every citation with its identifier, its document title, its section title, its document type, its claim scope and its snippet, and MUST NOT drop the claim scope, because it separates a fact of the world from a commitment of the establishment that is confirmed in store before being passed to a customer.

The system MUST NOT add citations the AI service did not return and MUST NOT resolve them into links.

#### Scenario: A question returns citations that carry their scope
- **GIVEN** a question about the product that the knowledge corpus covers
- **WHEN** the sale assistance is served
- **THEN** each citation carries its claim scope, its document and its section

### Requirement: Substitutes are requested once with the largest window, and only what the shop can sell today is offered

The system SHALL request substitutes from the AI service with the page size that reaches the largest over-retrieval window the frozen contract allows, taken from configuration and capped by the contract maximum, in a single call per request, and MUST NOT issue a second call because too few candidates survived.

The system MUST hydrate the whole window against the requested point of sale with a single set-based query and MUST offer only candidates with an active inventory record at that point of sale and at least one unit, keeping the order in which the AI service returned them and truncating to the requested page.

Excluding a candidate without stock here does not contradict assisted search, which keeps it: a search result the shop has run out of still informs the sale, while a substitute is asked for precisely to sell something now in place of a product that cannot be sold.

#### Scenario: Only candidates with stock at that shop are offered
- **GIVEN** the window contains candidates with stock, candidates carried with no units and candidates the shop does not carry
- **WHEN** substitutes are requested
- **THEN** only the candidates with stock at the point of sale appear
- **AND** they keep the order in which the AI service returned them

#### Scenario: The page is truncated after filtering
- **WHEN** more candidates with stock survive than the requested page size
- **THEN** exactly the requested page size is returned

#### Scenario: One call with the largest window
- **WHEN** substitutes are requested
- **THEN** exactly one call is issued to the AI service
- **AND** it requests the configured window page size, which reaches the largest over-retrieval window

#### Scenario: A short page does not trigger a second call
- **WHEN** fewer candidates with stock survive than the requested page size
- **THEN** no further call is issued
- **AND** the survivors are returned

### Requirement: The four empty outcomes of substitutes are distinguishable

The system SHALL report the outcome of every substitutes request as one of four values and MUST NOT answer a server error for any of them: ok when at least one substitute with stock is returned; none in stock when the AI service answered and no candidate has stock at the point of sale; product not indexed when the AI service rejected the product as one it cannot process; and AI unavailable when the AI service did not answer, failed, or the card is switched off for that point of sale.

A product the AI service cannot process and a service that did not answer MUST NOT be reported as the same outcome, because the first is a state of the catalog the next synchronisation fixes and the second is an outage.

#### Scenario: No candidate with stock is reported as such
- **GIVEN** the AI service answers and no candidate of the window has stock at the point of sale
- **WHEN** substitutes are requested
- **THEN** the outcome is none in stock

#### Scenario: A product the AI service rejects is not an outage
- **GIVEN** the AI service answers that it cannot process the product
- **WHEN** substitutes are requested
- **THEN** the outcome is product not indexed
- **AND** it is not AI unavailable

#### Scenario: A service that does not answer is reported as unavailable
- **GIVEN** the AI service call times out or its circuit is open
- **WHEN** substitutes are requested
- **THEN** the outcome is AI unavailable
- **AND** the response is not a server error

### Requirement: A failing AI service degrades the card and never breaks it

The system SHALL answer the sale assistance successfully when the AI service cannot serve it, whatever the reason: an open circuit, an exhausted time budget, a transport failure, a server error, a route with no implementation, credentials the service rejected, a product the service rejected, or the card switched off for that point of sale. In every one of these cases the response MUST declare the AI path unavailable.

The degraded response MUST carry the anchored product and the members of its family that the point of sale carries, read from the backend's own family records and hydrated like the served group, together with the stock warnings and the variants warning computed by the backend. It MUST carry no argument and no citations. The reason for the degradation MUST be recorded in the log; a credential failure MUST additionally be logged at error level.

#### Scenario: An open circuit serves the card from the catalog
- **GIVEN** the sale assistance circuit is open
- **AND** the anchored product belongs to a family with two members carried at the point of sale
- **WHEN** the sale assistance is requested
- **THEN** the response is successful and declares the AI path unavailable
- **AND** it carries both members with their catalog price and quantity
- **AND** it carries the variants warning and the stock warnings that apply
- **AND** it carries no argument and no citations

#### Scenario: A rejected credential degrades and is logged as an error
- **GIVEN** the AI service rejects the internal token
- **WHEN** the sale assistance is requested
- **THEN** the response is successful and declares the AI path unavailable
- **AND** the failure is logged at error level

#### Scenario: A product the AI service rejects degrades the card
- **GIVEN** the AI service answers that it cannot process the product
- **WHEN** the sale assistance is requested
- **THEN** the response is successful and declares the AI path unavailable
- **AND** the log records that the product was rejected rather than that the service was unavailable

### Requirement: The sale card can be switched off per point of sale

The system SHALL decide from configuration, per point of sale and reloadable without redeployment, whether the sale card calls the AI service. The switch MUST govern both operations. When it is off for a point of sale, the sale assistance MUST answer with the degraded response and the substitutes with the AI-unavailable outcome, without calling the AI service, and the log MUST record that the switch, and not an outage, produced the answer.

#### Scenario: A switched-off point of sale does not call the AI service
- **GIVEN** the sale card is switched off for a point of sale
- **WHEN** either operation is requested for it
- **THEN** no call is issued to the AI service
- **AND** the log records the switch as the reason

### Requirement: The cost of the generative route is bounded per user

The system SHALL limit the rate of sale assistance requests per user with a policy of its own, configured separately from assisted search, and MUST answer a request over the limit with a status the caller can distinguish from an unavailable AI service. The substitutes operation, which calls no model provider, MUST use the rate policy of assisted search. The system MUST NOT cache responses of the AI service for the sale card.

#### Scenario: A user over the limit is refused distinguishably
- **GIVEN** a user who has exhausted the sale assistance rate limit
- **WHEN** the user requests another sale assistance
- **THEN** the request is refused with a too-many-requests status
- **AND** no call is issued to the AI service

### Requirement: Neither what the customer asks nor what the argument says is written to a log above debug

The system SHALL record one structured log line per sale assistance and one per substitutes request, correlated by the trace identifier, and MUST NOT write the argument to any log at any level, whether resolved or not, because the resolved argument carries the real price. The question MUST NOT be written above debug level.

The sale assistance line MUST carry the point of sale, the product, whether a question was asked, whether the AI path was available, the state of the argument, its length, the identifiers of the citations, the warning codes, the members returned and the members carried, the elapsed times, the prompt version, the model and the token counts. The substitutes line MUST carry the outcome and the funnel of candidates returned, carried, with stock and returned.

#### Scenario: A generated argument is absent from every log line
- **GIVEN** a sale assistance served with a question and a generated argument
- **WHEN** the logs of the backend are inspected at every level
- **THEN** no line contains the argument
- **AND** no line above debug level contains the question

#### Scenario: The substitutes funnel is observable
- **WHEN** a substitutes request is served
- **THEN** the log line carries the candidates returned, carried, with stock and returned, and the outcome
