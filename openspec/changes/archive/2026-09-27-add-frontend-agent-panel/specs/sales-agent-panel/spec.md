## ADDED Requirements

### Requirement: The agent panel is a fourth way of starting a sale, on its own lazily loaded route

The frontend SHALL expose the sale agent as a fourth way of starting a sale, reachable from the sales landing page and living on its own lazily loaded route under the sales tree, alongside the scanning, manual entry and assisted search routes, and MUST NOT expose it as a toggle inside the assisted search panel.

That panel is one query producing one set of results while the agent is a conversation, and it already carries a toggle with a different meaning — the degraded path against the generative one. Two controls of similar name and different meaning on the same screen is the failure the free-query panel was built to remove.

The panel MUST offer a way to reach the deterministic panel, so that the same question can be asked in both and compared.

#### Scenario: The agent is reachable as an entry method
- **WHEN** the operator opens the sales landing page
- **THEN** a fourth card offers the agent
- **AND** activating it navigates to the agent's own route

#### Scenario: The assisted panel is unchanged
- **WHEN** the assisted search panel is inspected
- **THEN** it carries no agent toggle
- **AND** its existing route toggle keeps its meaning

### Requirement: The gate is read before entering and has three states, and a probe that cannot answer never closes it

The frontend SHALL read the availability probe before letting the operator into the panel and MUST render the entry card in one of three states: active when the agent is reported available; disabled **with the reason stated** when it is reported unavailable; and **active with a warning** when the probe cannot answer.

Failing the probe MUST NOT close a door that may well work, which is the rule the availability badge of the assisted panel already follows.

The reason shown when the agent is unavailable MUST be the agent's own and MUST NOT be the assisted answer's, because the agent has a credential chain of its own and the two can be off independently.

Reading the probe MUST NOT consume any request-rate quota and MUST NOT cause a model to run.

#### Scenario: The card is active when the agent is available
- **WHEN** the probe reports the agent available
- **THEN** the entry card is active

#### Scenario: The card is closed with its reason
- **WHEN** the probe reports the agent unavailable
- **THEN** the entry card is disabled
- **AND** the reason is stated on it
- **AND** the reason is not the assisted answer's

#### Scenario: A probe that cannot answer leaves the door open
- **WHEN** the probe fails or reports an unknown state
- **THEN** the entry card stays active
- **AND** a warning states that availability could not be confirmed

### Requirement: Each turn owns its answer block, and only the last one is open

The frontend SHALL render the conversation as a thread in which every answer from the agent is a block anchored to the turn that produced it, carrying that turn's prose, citations, groups, trace and stop state, and MUST NOT render a single results area that is refreshed on each turn.

A refreshed area leaves the operator reading one turn's argument while the rows beneath it already belong to the next, and **when the loop pivots to substitutes the piece being looked at disappears with no explanation** — which is the behaviour the agent exists to demonstrate.

Only the most recent block MUST be open; earlier blocks MUST collapse to a single line carrying the turn's summary and MUST reopen when activated, so that the act of selling always belongs to what is open.

Pieces MAY repeat across turns and MUST NOT be de-duplicated between them, because each turn's evidence is its own.

#### Scenario: Each answer is anchored to its turn
- **WHEN** the operator sends a second turn
- **THEN** the new answer appears as its own block
- **AND** the previous block remains in the thread

#### Scenario: Only the last block is open
- **WHEN** a new answer arrives
- **THEN** the previous block collapses to a single line
- **AND** activating that line reopens it

#### Scenario: A piece repeated across turns is not removed
- **WHEN** two turns return the same piece
- **THEN** both blocks show it

### Requirement: The composer counts the transcript that will be sent, not what the operator typed

The frontend SHALL show, beside the composer, the number of turns and the number of characters **of the transcript it is about to send**, counting the turns attributed to the assistant as well as the operator's, and MUST close the composer with its reason when any of the three contract caps is reached rather than letting a request be sent that will be refused.

Counting only what the operator typed would let the counter read well under its limit while the request was already over the total, which is precisely the refusal the counter exists to prevent.

The turn attributed to the assistant MUST carry the argument as it was served; when the argument was withheld, or when the answer was a clarification question, it MUST carry a short synthetic line naming the pieces so that a later turn referring to «that one» still has an antecedent.

#### Scenario: The counters include the assistant's turns
- **GIVEN** a thread with several answers already served
- **WHEN** the composer's counters are read
- **THEN** they account for the assistant's turns as well as the operator's

#### Scenario: The composer closes with a reason at the cap
- **WHEN** any of the three caps is reached
- **THEN** the composer is closed
- **AND** the reason is stated
- **AND** no request is sent

#### Scenario: A withheld argument still produces a sendable turn
- **GIVEN** a turn whose argument was withheld
- **WHEN** the next turn is sent
- **THEN** the assistant's turn carries a synthetic line naming the pieces
- **AND** the request is not refused for an empty turn

### Requirement: An answer with prose and no pieces is a normal answer and never an empty result

The frontend SHALL render an answer block that carries no pieces without using any of the empty-result statements, because a clarification question and a knowledge answer are normal outcomes of a conversation rather than a search that found nothing — and one in five answers carries no pieces at all.

A clarification question MUST return the focus to the composer.

An answer whose citations are empty MUST be rendered as normal, since an empty citation list is the common case rather than a fault.

An answer that searched the catalogue and found nothing MUST be distinguishable from the two above.

#### Scenario: A knowledge answer with no pieces
- **WHEN** the agent answers with prose and citations and no pieces
- **THEN** the block renders the prose and the citations
- **AND** no empty-result statement is shown

#### Scenario: A clarification question returns the focus
- **WHEN** the agent asks for a clarification
- **THEN** the block renders only the question
- **AND** the focus returns to the composer

#### Scenario: Having searched and found nothing is its own statement
- **WHEN** the agent searched the catalogue and no piece survived
- **THEN** the block states that, distinguishably from a clarification and from a knowledge answer

### Requirement: Groups are labelled by their provenance, and a substitute is never shown as a match

The frontend SHALL render catalogue matches and substitutes as separately labelled groups within the answer block, taking the label from the provenance the response carries and never from position or ordering, and MUST state the matches before the substitutes.

Offering a second-best alternative as though it were what was asked for is what a customer notices and what makes them stop trusting the counter.

Rows MUST be rendered with the existing assisted search result row, which already resolves an unknown shop name without asserting a quantity, states the rest of a family in a note, disables the sale when stock is unknown and offers both selling and opening the product card.

#### Scenario: A pivot shows two labelled groups
- **GIVEN** an answer carrying both catalogue matches and substitutes
- **WHEN** the block is rendered
- **THEN** the matches appear under their own label
- **AND** the substitutes appear under a label stating they are alternatives
- **AND** the matches are stated first

#### Scenario: The label comes from the provenance
- **WHEN** a group's provenance says it came from the substitutes tool
- **THEN** it is labelled as an alternative regardless of its position

#### Scenario: An unknown stock says a shop is needed rather than asserting none is left
- **WHEN** a row carries an unknown stock
- **THEN** it states that a shop has to be chosen to see stock
- **AND** it does not state that the piece has run out
- **AND** opening the sale card, which reports one shop's stock, is disabled

> **Amended during implementation, and the original scenario was wrong about the component this
> requirement says to reuse.** It read *«its sale action is disabled»*. The assisted search result row
> — which this change reuses **unmodified**, and whose own test since C40 pins the behaviour — does
> not disable selecting for sale on an unknown stock: it replaces the stock line with «Selecciona una
> tienda para ver existencias» and disables **opening the sale card**. Implementing the scenario as
> written would have required a diff to that row, which is explicitly out of scope, and the sibling
> panel has behaved this way since C40, so the two would have disagreed.
>
> It is also the correct behaviour, which is why it is not worth the diff: the every-shop scope exists
> to find out **where** a piece is, and the manual sale flow it hands over to requires a shop of its
> own and validates stock there — disabling selection would leave the scope unable to lead anywhere.
> What must not happen, presenting unknown stock as «none left», is what the row's three-state
> rendering already prevents, and that is what the scenario now states.

### Requirement: The trace is shown as the only on-screen evidence that an agent ran, and it never carries what was asked

The frontend SHALL render, per answer block, the per-iteration trace the response carries — which tools were invoked, whether each succeeded and under what cause if not, and the tokens and milliseconds each iteration cost — presented as a sequence of steps, and MUST NOT render tool arguments nor the content of observations, which the contract excludes by rule.

The trace is the only thing on screen that distinguishes an agent from a single prompt, so it MUST be reachable from the open block; it MAY be collapsed by default, with the number of iterations visible in the block's status strip.

#### Scenario: The trace is reachable from the open block
- **WHEN** an answer block is open
- **THEN** its trace can be revealed
- **AND** it lists the iterations with their tools, outcomes, tokens and duration

#### Scenario: The trace shows no arguments and no observations
- **WHEN** the trace is rendered
- **THEN** no tool argument is shown
- **AND** no observation content is shown

### Requirement: The ten stop reasons are stated in Spanish and never inferred from the counters

The frontend SHALL carry a Spanish statement for each of the ten values of the service's stop-reason vocabulary and MUST take the statement from the reported value alone, never deriving it from the iteration or tool-call counters, because a count of iterations does not say whether the last one was the last needed or the one that ran out — and those are opposite claims about the answer being read.

A value the frontend does not recognise MUST fall back to a neutral statement rather than to a guess or to a blank.

#### Scenario: Every stop reason has a statement
- **WHEN** an answer reports any of the ten stop reasons
- **THEN** the block states it in Spanish

#### Scenario: The statement does not come from the counters
- **WHEN** two answers report the same iteration count with different stop reasons
- **THEN** their statements differ

#### Scenario: An unknown value falls back to a neutral statement
- **WHEN** an answer reports a stop reason the frontend does not recognise
- **THEN** a neutral statement is shown rather than a blank or a guess

### Requirement: The scope is fixed for the length of a conversation, and changing it restarts the thread and says so

The frontend SHALL keep the point-of-sale scope fixed while a conversation is open, and MUST warn the operator and restart the thread when the scope changes, because the evidence already gathered was gathered in another shop.

The scope MUST default to the operator's own point of sale and MUST NOT default to every point of sale for anyone.

The every-point-of-sale option MUST be offered under the same rule the sibling panel applies, and selecting it MUST state the consequence that matters: with no point of sale the availability label can never say the shop is out of stock, **so the agent stops offering alternatives** — which is a capability lost rather than a display preference.

#### Scenario: Changing the scope restarts the thread with a warning
- **GIVEN** a conversation in progress
- **WHEN** the scope is changed
- **THEN** the operator is warned before the thread is restarted
- **AND** the previous evidence is cleared

#### Scenario: The default scope is the operator's own shop
- **WHEN** the panel is opened
- **THEN** the scope is the operator's point of sale

#### Scenario: The wider scope states that alternatives stop being offered
- **WHEN** every point of sale is selected
- **THEN** a line states that the agent will not offer alternatives in that scope

### Requirement: An incomplete answer is stated without alarm and names the budget that ran out

The frontend SHALL state, on an answer the service reported as cut short by a budget, that it is incomplete and which budget ran out, and MUST NOT present it as an error nor with an alarm colour, because the evidence gathered before the cut is still useful.

The statement MUST come from the reported stop reason.

#### Scenario: A cut answer is stated as incomplete
- **WHEN** an answer reports having been cut short by a budget
- **THEN** the block states that it is incomplete
- **AND** names the budget that ran out
- **AND** does not present it as an error

#### Scenario: A complete answer carries no such statement
- **WHEN** an answer was not cut short
- **THEN** no incompleteness statement is shown

### Requirement: The cost already spent in the session is visible before the next request is sent

The frontend SHALL show, in a fixed area of the panel, the requests issued, the tokens consumed and the cost accrued over the current session, accumulating the usage each answer reports, so that the operator sees what the agent costs **before** pressing again rather than after.

This route is measured as costing several times the deterministic one, and the quota that binds it is tokens per minute rather than money, so the visible figure is what makes the trade-off legible at the counter.

#### Scenario: The accrued cost is visible
- **WHEN** several turns have been answered
- **THEN** the panel shows the requests, tokens and cost accumulated across them

#### Scenario: The figure accumulates rather than replacing
- **WHEN** a new answer arrives
- **THEN** its usage is added to the running totals
