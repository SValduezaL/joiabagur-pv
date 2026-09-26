# sales-assistant-agent Specification

## Purpose
The sale assistant's agent loop in `jbg-ai`, the logic behind `POST /v1/assist/agent`. It runs a manual function-calling loop over the six read-only tools of the `sales-assistant-tools` registry — call the model with the tools' schemas, execute the calls a turn requests concurrently under a ceiling below the database connection pool's capacity, return their observations and call the model again — until the model asks for no further tool, invokes the clarification tool, or a budget runs out. The loop only gathers evidence: the argument is still written by the generation layer over that evidence, so the numeric gate, the referential integrity of citations and the single repair keep holding, and the prose of a loop turn is discarded by the type of the agent port rather than by discipline. One request is bounded by six budgets — loop iterations, tool calls, chat-provider calls, accumulated tokens, accumulated context in characters and wall-clock time — and exhausting any of them serves what was gathered with `partial: true` and a `stop_reason` drawn from a closed vocabulary, never inferred from counters; calls beyond the remaining tool budget come back as observations carrying the budget-exhausted cause and touch no port. The multi-turn transcript travels in the request, capped in turns, per-turn length and total length, every turn — those attributed to the assistant included — is delimited as data, and the service stores no conversation state between calls; the intent classifier acts as an entry guardrail that classifies exactly one turn per request and whose refusal short-circuits on any turn. The response extends the deterministic assistance response with the partial flag, the stop reason, the counters, a usage object publishing the provider-call count and a bounded wire trace that names, per iteration, the tools invoked, their outcome, cost and latency, but never their arguments or observation contents. The route is separate: `POST /v1/assist/sale` is unchanged in shape, behaviour and provider-call ceiling, the published contract moves by addition only, and without an agent credential the route degrades instead of failing. The token, context and wall-clock budgets are fixed by a real-provider measurement against declared calibration instruments, never against the evaluation's golden set, and the tests run offline.

## Requirements

### Requirement: The sale assistant runs a manual function-calling loop that gathers evidence and never writes the answer
The service SHALL run a loop that calls the model with the tool registry's schemas, executes the tool calls the model requests, returns their observations and calls the model again, until the model requests no further tools, requests clarification, or a declared budget is exhausted; and the loop MUST NOT produce the response prose itself.

The argument is written by the generation layer over the evidence the loop gathered. If the last turn of the loop wrote prose it would bypass, in one step, the numeric gate that rejects a figure absent from the given context, the referential integrity of citations, and the single repair — the three properties the generation capability exists to hold. It also keeps "nothing is persisted" without effort, because the intermediate reasoning never leaves the process.

#### Scenario: The loop stops when the model asks for no more tools
- **GIVEN** a request the model can answer after one round of tools
- **WHEN** the model returns a turn carrying no tool calls
- **THEN** the loop stops without exhausting any budget
- **AND** the response is not marked partial
- **AND** the argument was produced by the generation layer over the gathered evidence

#### Scenario: The evidence reaches the generation layer and the loop's prose does not
- **WHEN** a request completes after several rounds of tools
- **THEN** the candidates, family members and corpus fragments the tools observed are what the generation layer was given
- **AND** the published citations are the ones the argument declared it used and that verified

### Requirement: The textual content of a loop turn is discarded, and the discarding is a property of the type
The agent port SHALL return only the tool calls a turn requested together with what the turn cost, and its return type MUST NOT carry a field for free text.

A rule that says "the caller must not read this field" is a field the caller will eventually read. Making the discard structural is the same choice this project already made when it verified the read-only invariant by introspecting the object graph rather than by trusting a boolean on the descriptor. The cost is accepted and declared: the model's own reasoning is not available for debugging, and the adapter records the length and a digest of what it discarded, never the text.

#### Scenario: No fragment of a loop turn's prose reaches the response
- **GIVEN** a model that returns prose alongside its tool calls
- **WHEN** the response is composed
- **THEN** no field of the response contains any fragment of that prose
- **AND** the wire trace does not contain it either

#### Scenario: The port cannot carry free text
- **WHEN** the agent port's return type is inspected
- **THEN** it declares no field able to carry the model's prose

### Requirement: One request is bounded by six budgets and declares which one stopped it
The service SHALL bound one request by six budgets — loop iterations, tool calls, chat-provider calls, accumulated tokens, accumulated context measured in characters, and elapsed wall-clock time — and exhausting any of them MUST serve the evidence gathered so far, mark the response partial, and name the budget that stopped it.

The count of steps is not what dominates the cost of a loop: the accumulated context is, because every observation is re-sent on every later turn. That is why a budget of characters is evaluated before a call and a budget of tokens is enforced after one — enforcing tokens beforehand would require a tokeniser this project does not depend on, and the one turn by which the token budget can overshoot is itself bounded by the other five.

The wall-clock budget is not optional decoration. This route's worst case is several times the latency the deterministic route declares, and a loop whose only limits are step counts can spend a provider timeout on every one of them.

The stop reason SHALL be drawn from a closed vocabulary that distinguishes the model finishing from each budget cutting and from clarification ending the loop, and MUST NOT be inferred by the consumer from counter values.

#### Scenario: The iteration budget stops the loop and the response says so
- **GIVEN** a model that keeps requesting tools on every turn
- **WHEN** the iteration budget is reached
- **THEN** the loop stops
- **AND** the response is marked partial
- **AND** the stop reason names the iteration budget
- **AND** the response still carries the evidence gathered and an argument written over it

#### Scenario: The provider-call ceiling holds for one request
- **GIVEN** a request that classifies, runs the maximum number of loop turns and repairs its argument
- **WHEN** it completes
- **THEN** the total number of chat-provider calls does not exceed the declared ceiling
- **AND** that ceiling is derived from the constants of its three stages rather than written as a literal

#### Scenario: Embedding calls are counted apart from provider calls
- **WHEN** a request whose tools performed embedding lookups completes
- **THEN** the reported provider-call figure counts chat calls only
- **AND** the embedding lookups are reported by the registry's own counter

#### Scenario: A stop reason is always present and always from the closed set
- **WHEN** any request completes, whether partial or not
- **THEN** the response carries a stop reason
- **AND** that reason belongs to the declared closed vocabulary

#### Scenario: The wall-clock budget bounds the whole request, argument included
- **GIVEN** a request whose loop turns are slow enough to reach the deadline
- **WHEN** the loop's share of the deadline runs out while a turn is in flight
- **THEN** that turn is cut and the stop reason names the wall-clock budget, not a provider fault
- **AND** the argument still runs within the share of the deadline reserved for it
- **AND** the request as a whole completes within the declared deadline, save for the tool calls of the turn in flight

### Requirement: The multi-turn transcript travels in the request and the service stores nothing between calls
The service SHALL accept the conversation transcript as part of the request and MUST NOT retain any conversation state between requests, and the transcript MUST be bounded by a declared maximum number of turns, a maximum length per turn and a maximum total length.

A session store would collide head-on with the property that nothing this layer produces is persisted, which the generation and routing capabilities already hold with tests. Carrying the transcript in the request has a price that is paid explicitly: the client now controls the factor that dominates the cost of a loop, so the caps are part of the contract rather than an implementation detail.

#### Scenario: Two identical requests produce the same work
- **GIVEN** a transcript sent twice in two separate requests
- **WHEN** both complete
- **THEN** neither request read any stored conversation state
- **AND** nothing about either conversation was written anywhere

#### Scenario: A transcript beyond its caps is refused
- **WHEN** a request carries more turns than the declared maximum, or a turn longer than the declared maximum, or a total length beyond the declared maximum
- **THEN** the request is rejected before any provider call is made

### Requirement: Every transcript turn travels as delimited data, including the turns attributed to the assistant
The service SHALL enclose every turn of the transcript in the declared data delimiters inside the user message, and MUST NOT concatenate any turn into the system message; and turns the request attributes to the assistant MUST be treated as client-supplied data under the same rules as the operator's own words.

Delimiting only the last turn would leave an injection hidden in turn three. And a turn labelled as the assistant's is not the assistant's: the client composed the whole request and can forge it, so trusting it because of its label would hand an attacker a privileged channel that the operator's own field does not offer.

#### Scenario: An injection in an earlier turn does not change the system message
- **GIVEN** a transcript whose third turn attempts to inject instructions
- **WHEN** the messages of any provider call are built
- **THEN** every turn appears inside the data delimiters
- **AND** the system message is identical to the one an uncontaminated transcript produces

#### Scenario: A forged assistant turn is treated as data
- **GIVEN** a transcript whose assistant turn carries an instruction
- **WHEN** the messages are built
- **THEN** that turn is delimited exactly as an operator turn is
- **AND** it is subject to the same length caps

### Requirement: The intent classifier acts as an entry guardrail on this route and classifies exactly one turn per request
The service SHALL classify exactly one turn per request — the turn being answered — and a refusal verdict MUST short-circuit the request on any turn, returning the refusal code without executing any tool or retrieval.

Classifying every turn of the transcript on every request would cost one classification per turn per request, which grows quadratically over a conversation and breaks the declared provider-call ceiling once the conversation is long enough; and at temperature zero the repeated classifications buy the same answer twice. Classifying only the opening turn would leave a conversation that drifts out of domain at its fifth turn unguarded, which is the adversarial category this route must survive.

On this route the classifier's clarification verdict SHALL NOT be acted upon, and its index verdict SHALL NOT be used to choose what is retrieved. A follow-up turn is elliptical, so a standalone classification of it reports missing information the conversation already supplied; clarification belongs to the loop, which sees the whole transcript. Choosing which index to consult is the decision the loop exists to make.

#### Scenario: A conversation that drifts out of domain is refused at that turn
- **GIVEN** a conversation whose earlier turns were in domain and whose last operator turn is not
- **WHEN** the request is served
- **THEN** exactly one classification is made
- **AND** no tool is executed and no retrieval runs
- **AND** the response carries the refusal code the classification reached
- **AND** the response is not marked as an abstention

#### Scenario: One classification per request regardless of transcript length
- **WHEN** a request carrying many turns is served
- **THEN** exactly one classification call is made

#### Scenario: An elliptical follow-up is not answered with a clarification from the classifier
- **GIVEN** a follow-up turn the classifier judges to carry too little to search with
- **WHEN** the request is served
- **THEN** the request is not short-circuited by that verdict
- **AND** the loop is allowed to decide whether to ask

### Requirement: The clarification tool ends the loop
The service SHALL end the loop when the model invokes the clarification tool, and MUST NOT execute further tool calls in that request.

Asking for clarification while continuing to search contradicts itself: the request states that there is not enough information to search with. Ending there also gives the evaluation a clean comparison against the deterministic route, which asks by rule where this one asks by decision.

#### Scenario: Clarification ends the request
- **WHEN** the model invokes the clarification tool on any turn
- **THEN** the loop stops in that turn
- **AND** the stop reason names clarification
- **AND** the question returned is the deterministic text the closed catalogue associates with the chosen axis

### Requirement: Tool calls of one turn execute concurrently under a declared ceiling
The service SHALL execute the tool calls of a single turn concurrently and MUST bound the number running at once by a declared ceiling below the database connection pool's capacity.

Assuming one tool call per turn is a defect that appears with the first complex conversation, and running four searches in sequence spends latency for nothing. But the connection pool is small and has no overflow, and each search opens its own session: running more calls at once than the pool can serve makes the last of them wait for a pool timeout, which reads like an unavailable database rather than like self-inflicted contention.

#### Scenario: Several tool calls in one turn run concurrently
- **GIVEN** a turn requesting several tool calls
- **WHEN** the turn is dispatched
- **THEN** the calls execute concurrently rather than in sequence
- **AND** each observation is paired with the call that produced it

#### Scenario: Concurrency stays below the pool's capacity
- **WHEN** a turn requests more tool calls than the declared concurrency ceiling
- **THEN** no more than the ceiling execute at any one moment

### Requirement: Tool calls beyond the remaining budget are refused as observations and touch no port
The service SHALL execute the tool calls of a turn in the order the model emitted them until the tool-call budget is spent, and MUST return each remaining call as a failed observation carrying the budget-exhausted cause without touching any port.

Executing none of a turn's calls would waste a provider call already paid for. Dropping the unaffordable ones silently would leave the model unable to tell a spent budget from a broken tool. Emitting the order rule explicitly is what makes the truncation deterministic and therefore reproducible in an evaluation.

#### Scenario: A turn requesting more calls than the budget allows
- **GIVEN** a turn requesting more tool calls than the remaining budget permits
- **WHEN** the turn is dispatched
- **THEN** the calls that fit execute in the order the model emitted them
- **AND** each remaining call returns a failed observation carrying the budget-exhausted cause
- **AND** no port was touched for any of them
- **AND** the loop stops after that turn and the response is marked partial

### Requirement: Availability labels govern the loop's decisions and never reach the generated argument
The service SHALL NOT include any availability label in what it hands to the generation layer, and the calibration run MUST measure how often a served argument nonetheless mentions availability rather than assert that it cannot.

Authority over stock belongs to the .NET API, the projection this service reads can be minutes stale, and the placeholder the hydrating layer resolves is the only expression of availability the contract admits. The label exists so the loop can decide whether to pivot to substitutes; letting it into the prose would put a stale statement about stock in the one place no numeric gate can undo it — and one of the labels is itself a member of the stock-marker vocabulary that gate watches for.

What this layer guarantees is the input: the generation layer is never given a label. What the model writes is not guaranteed by anything — the verification of the argument passes a bare «disponible», and refusing that word would also refuse a size a family roster legitimately makes available — so the output is measured, not asserted. Refusing it in the shared verification would move the deterministic route, which this capability must not do.

#### Scenario: The generation payload carries no availability label
- **GIVEN** a request during which the loop observed the availability of one or more pieces
- **WHEN** the payload handed to the generation layer is inspected
- **THEN** it contains no availability label

#### Scenario: Availability in the argument is measured, not asserted
- **WHEN** a calibration run serves an argument
- **THEN** the run records how many availability terms that argument carries, as a count and never as its text
- **AND** the only expression of availability the contract admits remains the placeholder the hydrating layer resolves

### Requirement: Substitutes reach the generation layer as a group distinguished from catalogue matches
The service SHALL mark the groups it gathered from the substitutes tool as substitutes, using a value from a closed vocabulary, so that the generation layer can tell them from candidates the catalogue search returned, and SHALL publish that same marker on every group of the response so that a consumer can label them too.

A substitute and a match are different things to say to a customer, and a payload that flattened them would let the argument present a second-best alternative as though it were what was asked for. The distinction changes the shape of the payload, so the prompt that reads it moves to a new version rather than being edited in place — the figures measured against the previous version have to stay interpretable.

Publishing the marker on the response is the same argument one layer out. Until now the distinction existed only in the payload the model reads, so the argument said «and as an alternative…» because the prompt told it to while **the screen had no way to label the rows** — which is exactly what the marker exists to prevent. The marker MUST be carried on a response model of the agent's own rather than added to the group model the deterministic route publishes, because widening the shared model would move the schema of that route.

#### Scenario: A pivot to substitutes is visible in the payload
- **GIVEN** a request during which the loop invoked the substitutes tool
- **WHEN** the payload handed to the generation layer is inspected
- **THEN** the substitute groups carry the closed-vocabulary marker that distinguishes them
- **AND** the catalogue matches do not

#### Scenario: The piece the loop pivoted away from is not offered as a match
- **GIVEN** a request whose catalogue search returned a piece for which the loop then requested substitutes
- **WHEN** the payload handed to the generation layer is inspected
- **THEN** that piece is not among the catalogue matches
- **AND** when the cap on distinct pieces binds, further catalogue matches are dropped before the substitutes, while the payload keeps the order in which the evidence arrived

#### Scenario: The previous argument prompt version is preserved intact
- **WHEN** the prompt directory is inspected after this capability ships
- **THEN** the previous argument prompt version is present and unmodified

#### Scenario: Every group of the response declares its provenance
- **GIVEN** a request whose evidence holds both catalogue matches and substitutes
- **WHEN** the response is inspected
- **THEN** every group carries the closed-vocabulary marker of its provenance
- **AND** the marker distinguishes a catalogue match from a substitute

#### Scenario: The deterministic route's group model is not widened
- **WHEN** the published contract is compared before and after
- **THEN** the group model of the deterministic route is unchanged
- **AND** the marker appears only on the agent's own group model

### Requirement: The loop and the argument report their prompt versions separately
The service SHALL report the version of the loop's prompt and the version of the argument's prompt as two distinct values, and MUST NOT report one in place of the other.

They are two calls with different outputs and, potentially, different models. A single version field would make either figure unreadable the first time one of the two moved, which is the same reason the classifier's prompt is already versioned apart from the argument's.

#### Scenario: Both versions travel on a response that ran both stages
- **WHEN** a request runs the loop and produces an argument
- **THEN** the response reports the loop prompt version
- **AND** the response reports the argument prompt version
- **AND** the two are distinct fields

### Requirement: The response extends the deterministic route's shape and publishes its provider-call count
The response of the agent route SHALL carry every field the deterministic assistance response carries, with the same meaning, plus the partial flag, the stop reason, the counters, the trace and a usage object that publishes the number of provider calls made.

The evaluation this capability exists to enable compares the two routes over the same set, so the comparison must be a difference of fields rather than a translation between two shapes. The call count is published here and not added to the shared usage object, so that the deterministic route's schema is unchanged: without it, the claim that the ceiling is observable from the same object a consumer reads would not be true of this route.

#### Scenario: The agent response carries the deterministic response's fields
- **WHEN** the agent response shape is compared against the deterministic one
- **THEN** every field of the deterministic response is present with the same meaning
- **AND** the agent's additional fields are additions rather than replacements

#### Scenario: The provider-call count is readable by the consumer
- **WHEN** a request completes
- **THEN** the usage the response carries reports how many provider calls were made

### Requirement: The response publishes the identifiers and scores the model was never shown
The service SHALL publish, for every piece and every corpus fragment it returns, the identifier and the ranking score the assistance response declares, and it MUST NOT derive any of them from what the tools reported to the model nor invent one where the tool layer does not supply it.

What a tool returns to a model is bounded by rule: no internal identifier, because a model cannot say one at a counter and its digits widen the whitelist the numeric gate admits; and no retrieval score, because scores from different tools do not measure the same thing. What a consumer of this route needs is the opposite — an identifier to hydrate a piece with and a score to order it by — and the published response requires both. The two sets do not overlap, so the values a response carries cannot be rebuilt from an observation, and a document title cannot be rebuilt from a citation identifier at all.

The consequence is that the tool layer keeps what it read for the consumer alongside what it reported to the model, and the two are separate by construction rather than by discipline. A piece enumerated from a family roster was not ranked against anything, so it carries the value and the meaning the deterministic route already gives an enumeration rather than a rank invented for the occasion.

#### Scenario: A published piece carries what the model never saw
- **WHEN** a request that searched the catalogue returns candidates
- **THEN** every published piece carries its identifier and its ranking score
- **AND** neither value appeared in any observation the model was given

#### Scenario: A published citation carries its document and its type
- **WHEN** a request that consulted the corpus publishes a citation
- **THEN** it carries the document title and the document type
- **AND** neither is derived from the citation identifier

#### Scenario: An enumerated piece is not given an invented rank
- **WHEN** a family roster reaches the response
- **THEN** its members carry no match reason
- **AND** their score is the one the deterministic route gives an enumeration

### Requirement: The wire trace reports what was done and never what was asked
The response SHALL carry a trace reporting, per iteration, which tools were invoked, whether each succeeded and with what cause if not, together with what the iteration cost and how long it took; and that trace MUST NOT carry tool arguments or observation contents.

A consumer logs the responses it receives, and the arguments a tool is called with are the operator's question as the model reformulated it — which the rule this project already holds keeps out of durable storage. Tool names are sufficient for the measurement the evaluation needs, which is the tools invoked against the tools expected. A richer trace is available in process to a caller that embeds this layer directly, which is how the evaluation harness consumes every other part of this service.

#### Scenario: The trace names tools and omits arguments
- **WHEN** a request that invoked several tools completes
- **THEN** the trace reports per iteration the tool names, their success and their failure causes
- **AND** the trace reports the tokens and the elapsed time of each iteration
- **AND** the trace carries no tool arguments and no observation contents

#### Scenario: The log line carries no query either
- **WHEN** a request completes
- **THEN** the log line reports the counters, the stop reason, the cost and the latency
- **AND** it carries neither the transcript nor any tool argument

### Requirement: Abstention on this route means the catalogue was searched and had nothing
The response SHALL report abstention only when at least one catalogue search ran, every such search abstained, and no corpus fragment was gathered.

Abstention is a statement about the shape of the distance profile after retrieving, and it is not the same as a request that simply gathered nothing or one the guardrail refused. Reporting it for any of those would say the opposite of the truth about the catalogue on exactly the requests where a consumer would act on it.

#### Scenario: A refused request is not an abstention
- **WHEN** the guardrail refuses a request
- **THEN** the response is not marked as an abstention

#### Scenario: A request that never searched the catalogue is not an abstention
- **WHEN** a request completes having invoked no catalogue search
- **THEN** the response is not marked as an abstention

### Requirement: The agent route is separate and the deterministic route is unchanged
The service SHALL expose the agent loop on a route of its own, and the deterministic assistance route MUST be unchanged in its response shape, its behaviour and its provider-call ceiling.

The two have latency budgets that differ by a factor the deterministic route's consumer cannot absorb, and the evaluation this capability enables requires both to remain runnable over the same set. A flag on the existing route would put a long path in the route a counter calls synchronously and would force the partial flag, the stop reason and the trace into a response other consumers read.

#### Scenario: The deterministic route is untouched
- **WHEN** the deterministic assistance response is compared before and after this capability ships
- **THEN** its shape is identical field for field
- **AND** its provider-call ceiling is unchanged

#### Scenario: The contract moves by addition only
- **WHEN** the published contract is compared before and after
- **THEN** no field was retired and no field changed type
- **AND** the difference is the new route and its models

### Requirement: Without an agent credential the route degrades instead of failing
The service SHALL serve a response without running the loop when no agent provider credential is configured, and MUST NOT answer with a server error for that reason alone.

A deployment that configures no credential is a declared state, and it is also the rollback and the ablation at once: removing the credential is how a deployment returns to the behaviour that preceded this capability. The credential resolution follows a declared fallback chain and the link that won is logged once per process, so a deployment can check which credential is in force rather than assume it.

#### Scenario: No credential configured
- **WHEN** a request arrives and no agent credential is configured
- **THEN** no loop runs and the agent's provider is not called
- **AND** the entry guardrail still classifies the request when its own credential is configured, so a refusal is reported as one
- **AND** the response is served rather than failed

#### Scenario: The resolved credential is observable
- **WHEN** the service builds its agent client
- **THEN** it logs once which link of the fallback chain was resolved
- **AND** the log carries no secret

### Requirement: The budgets that cannot be fixed by judgement are fixed by measurement
The token budget, the context budget and the wall-clock budget SHALL be set from a run against a real provider, and each MUST be published with its distribution rather than with an average alone.

A budget chosen without a latency or cost distribution behind it is a product judgement, and this project has already measured one such judgement to be wrong by a third. Agent runs have a long tail — the request that loops to its limit is the one that ruins a mean — so the figure that governs is a high percentile and not the average.

The run SHALL also publish the growth of the accumulated context per turn and the cost of the agent relative to the deterministic pipeline over comparable input, because the figure that justifies autonomy is the overhead against the cheapest alternative that would serve the case, not the absolute cost.

#### Scenario: The budgets carry their measurement
- **WHEN** the delivered budget values are inspected
- **THEN** each carries the run that produced it
- **AND** each is published with at least a median and a high percentile

#### Scenario: The overhead against the pipeline is published
- **WHEN** the run's report is read
- **THEN** it states the cost of the agent relative to the deterministic pipeline
- **AND** it states the growth of the accumulated context per turn

### Requirement: The measurement instruments are declared as such and the evaluation set is not used
The runs that calibrate this capability SHALL use instruments declared for that purpose — a synthetic load set for cost and latency, and a hand-written calibration set carrying the tool expected at each turn — and MUST NOT use the evaluation harness's golden set to calibrate any value or to iterate any prompt.

The comparison this capability exists to enable is run over the golden set by a later change. A prompt tuned against that set would make its own verdict meaningless, which is the same reason the classifier's prompt is already required to derive from the catalogue's vocabulary rather than from the evaluation sets. The two instruments differ in size because they answer different questions: a percentile needs variety of transcripts, while ground truth needs few transcripts carefully annotated, and repeating a transcript at temperature zero buys neither.

#### Scenario: The golden set is untouched
- **WHEN** the change's artefacts and runs are reviewed
- **THEN** no prompt was iterated against the golden set
- **AND** no budget was calibrated from it

#### Scenario: The instruments declare what they are
- **WHEN** the calibration instruments are inspected
- **THEN** each declares whether it measures load or carries ground truth
- **AND** the ground-truth instrument declares that it is for calibration and not for evaluation

### Requirement: The calibration run answers whether the tool granularity and the availability vocabulary are adequate
The calibration run SHALL report, from the loop's trace, whether any tool was never chosen, whether any tool accumulated argument failures, whether the model invented tool names and which, and whether consecutive near-identical calls to one tool occurred; and it SHALL report the rate at which the loop pivoted to substitutes for each availability label.

These two questions were left open when the tool registry shipped, because that half deliberately called no model and therefore could not measure a model's choices. Both are answerable from the trace with no new instrument. An invented tool name is the most informative datum the run can produce, because the name the model reaches for states which tool is missing; and the pivot rates separate the expensive failure — pivoting away from a piece the shop can actually sell — from the cheap one.

#### Scenario: The granularity report is produced
- **WHEN** the calibration run completes
- **THEN** it reports per tool whether it was ever chosen and how often its arguments failed
- **AND** it lists any tool names the model invented

#### Scenario: The pivot rates are reported per label
- **WHEN** the calibration run completes
- **THEN** it reports the substitute-pivot rate for each availability label
- **AND** it distinguishes pivoting when the piece is sellable from failing to pivot when it is not

### Requirement: The agent's measurement instruments record the placeholder rate and the freshness the run actually had

The agent's measurement harness SHALL record, per generation, how many price placeholders and stock placeholders the first attempt contained, and SHALL publish those counts aggregated over the run, so that the rate at which the argument writes a placeholder over an unanchored payload is readable rather than inferred from the withholding rate.

It SHALL also record the age of the point-of-sale projection, both once in the run's provenance and **again on every row**, together with the verdict of whether that age exceeded the staleness ceiling, so that a row served without the availability prefilter is identifiable afterwards instead of being averaged in with the rest.

Recording the age per row rather than once is what the run needs, because a run lasts longer than the ceiling: the harness resolves its reference pieces through a port that reads the projection directly and applies no freshness check, while the serving path consults the synchronisation checkpoint and declines to apply the scope when it is stale. The two therefore disagree in silence, and a run with no recorded age cannot be told apart from a run that was fresh throughout.

The recorded age MUST come from the synchronisation checkpoint and never from the projection's own refresh column, which records when an assignment last changed rather than when the projection was last read.

#### Scenario: Placeholder counts are recorded and aggregated
- **WHEN** a run of the agent harness completes
- **THEN** each row carries the price-placeholder and stock-placeholder counts of its first attempt
- **AND** the run publishes those counts aggregated

#### Scenario: Freshness is recorded per row and not only per run
- **WHEN** a run of the agent harness completes
- **THEN** the provenance carries the projection's age at the start
- **AND** every row carries the age and the staleness verdict that applied to it

#### Scenario: A degraded row is identifiable rather than averaged in
- **GIVEN** a run during which the projection became stale partway through
- **WHEN** the artefact is read afterwards
- **THEN** the rows served without the availability prefilter can be told from the rest

#### Scenario: The age comes from the checkpoint
- **WHEN** the recorded age is traced to its source
- **THEN** it comes from the synchronisation checkpoint
- **AND** not from the projection's refresh column

### Requirement: Agent tests run offline
The test suite of this capability SHALL run with no chat provider, no embedding provider, no network and no real database, driving injected doubles for every port and for the agent provider.

This is the property every layer of this service already holds, and it is what lets a loop with non-deterministic behaviour be tested deterministically: the doubles decide what the model asks for, so each stop condition, each budget and each failure path is exercised without a provider being involved.

#### Scenario: The suite runs with nothing configured
- **WHEN** the suite runs with no provider credential and no database URL
- **THEN** every test passes
- **AND** no socket is opened
