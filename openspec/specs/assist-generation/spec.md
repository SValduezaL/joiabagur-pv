# assist-generation Specification

## Purpose
The sale-assistance layer of `jbg-ai`, the logic behind `POST /v1/assist/sale`. It serves three modes selected structurally by the anchors the request carries — a free query, a piece with no question, and a piece with a question — and the two piece-anchored modes derive both the mode and the detected intent from that shape alone, the piece-anchored intent value being unchanged; the free-query mode is classified by an intent router before any retrieval runs, which decides three axes: whether the request is served at all, as in domain, out of domain, or a kind of object this catalogue does not carry; which index answers it, the catalogue, the knowledge corpus or both; and whether the query carries enough to search. The two refusals are distinct and travel as two distinct reason codes, because a trade the shop does not practise and a piece the shop does not carry are different things to say at the counter; neither of them is expressed by reusing the abstention flag, which goes on reading the shape of the distance profile after retrieving exactly as before. A query that carries too little to search receives a clarification question selected in code from a closed catalogue of Spanish templates keyed on the missing axis, never written by the model. The detected intent is reported as unclassified when this request was not classified — because no classifier ran, or because one ran and could not be used — and an unavailable classifier is a declared fail-open: the request is then served exactly as it was before this capability routed anything. The point-of-sale scope comes from the token claim and never from the body, and the response echoes the scope actually applied. Candidates are grouped by family with the variant label of every member and the match reasons the retrieval recorded, and a candidate whose family is unknown is a group of one, because a group of several products with no family asserts a grouping the catalogue does not hold. Warnings are computed from data by deterministic rules and travel as a closed vocabulary of codes — the family holds other members, the size label is absent — with the wording for a human reader left to the presentation layer; the variants warning is read from the family roster the index holds, capped at a declared maximum, rather than inferred from how many members the retrieval happened to return, and an anchored question that yields no citation once the knowledge distance threshold has been applied is declared by a code of that same vocabulary, determined from the search result already computed and at no additional provider call. No warning depends on stock: the .NET API is the authority on it and knows it only after hydration, and the availability bucket this service holds is carried for ranking and never emitted. Grounding is citable without invoking a model: the piece-anchored mode with no question addresses its fragments deterministically over the sheets of the materials the product declares and an allow-list of sections, admitting only fragments of general claim scope so that a commitment of the establishment never enters an argument nobody asked for, while the modes carrying a question search the knowledge corpus with the sheets of the undeclared materials excluded and the rest of the corpus reachable. Citations are fragments of the commercial knowledge corpus carrying their resolvable identifier, their document and section titles, their document type and their claim scope, and the catalogue is never cited, since a candidate's grounding in it is expressed through its match reasons. The abstention decision is honoured and declared in a dedicated field rather than through the cross-branch confidence signal, whose measured meaning is a different one; a piece the index cannot serve is an error distinguishing the unknown, the inactive and the un-embedded case rather than an abstention; and no field of the response carries a price or a stock figure. The two modes anchored to a piece generate a prose sale argument through a language model, reporting the version of the prompt used and the usage accumulated across every call, while the free-query mode the router admitted now generates as well, over the route the classifier decided and from a payload of its own that excludes the internal product identifiers and the retrieval scores, and an abstained request, a refused one and a clarified one call no generation provider and emit the argument empty with the prompt version absent; the argument is grounded only in the structured payload and the fragments handed to the model, every numeral it carries belongs to that payload and none of them sits next to a currency marker, and every citation published is one the argument declared and was shown to support text actually written, with a single repair attempted for all violations at once and whatever survives it degraded — the argument withheld, or the unverifiable citation withheld — rather than turned into an error, so the structured layer it preserves remains the ablation baseline; the generated text is never persisted and never logged. One request makes at most three provider calls: one classifier call, which is never retried and never repaired, and at most two generation calls. The stub fixture stays deterministic, performs no external input or output, and includes a group with a null family identifier. Tests run offline.

## Requirements

### Requirement: Sale assistance is served in three modes, anchored by piece, by query, or by both
The service SHALL serve `POST /v1/assist/sale` in three modes, selected by which anchors the request carries: a free query with no piece, a piece with no question, or a piece with a question. The request MUST accept a product identifier and a query as independent optional fields and MUST require **at least one** of them. A request carrying neither MUST be rejected as invalid, naming both fields.

The `pos_id` scope MUST come from the token claim and never from the request body, and the response MUST echo the scope actually applied.

#### Scenario: A piece with no question is served as a piece-anchored assistance
- **WHEN** an authenticated client calls the route with a product identifier and no query
- **THEN** the response carries exactly one group, the one holding that product
- **AND** the detected intent is the piece-anchored one

#### Scenario: A free query with no piece is served
- **WHEN** an authenticated client calls the route with a query and no product identifier
- **THEN** the response is served over the candidates the retrieval produced
- **AND** the detected intent is the unclassified one

#### Scenario: A piece with a question is served as both
- **WHEN** an authenticated client calls the route with a product identifier and a query
- **THEN** the groups are anchored to that product
- **AND** the citations answer the question asked

#### Scenario: A request with neither anchor is rejected
- **WHEN** an authenticated client calls the route with neither a product identifier nor a query
- **THEN** the response is a validation error
- **AND** the error names both fields as the alternatives

#### Scenario: The scope comes from the token and never from the body
- **GIVEN** the token declares one point of sale and the body declares a different one
- **WHEN** the route is called
- **THEN** the scope applied is the one in the token
- **AND** the response echoes that same scope

### Requirement: Candidates are grouped by family, and a product without a family is a group of one
The response SHALL group candidates by their family identifier, exposing the variant label of every member when it is known. A group whose family is unknown MUST carry a null family identifier and MUST contain **exactly one** member, because a group of several products with no family asserts a grouping the catalogue does not hold.

Every member MUST expose the match reasons the retrieval recorded for it, so that the reason a candidate is present travels as data rather than as prose.

#### Scenario: Members of one family are grouped under it
- **GIVEN** a product that belongs to a family with several members
- **WHEN** the route is called anchored to that product
- **THEN** the group carries that family identifier
- **AND** the members expose their variant label when it is known

#### Scenario: A product with no family is a group of one
- **GIVEN** a product that belongs to no family
- **WHEN** the route is called anchored to that product
- **THEN** the group carries a null family identifier
- **AND** the group contains exactly one member

#### Scenario: No group with a null family carries more than one member
- **WHEN** any response is produced
- **THEN** every group with a null family identifier contains exactly one member

#### Scenario: Each member carries the reasons it was retrieved for
- **WHEN** a group member is returned
- **THEN** it exposes the match reasons the retrieval recorded
- **AND** those reasons are the retrieval vocabulary and not a generated sentence

### Requirement: Warnings are computed from rules and travel as a closed vocabulary of codes
Warnings SHALL be computed from data by deterministic rules and MUST NOT be produced by a model. Every warning emitted MUST belong to a closed vocabulary declared by this capability, and the service MUST NOT emit a warning in natural language: the wording for a human reader belongs to the presentation layer.

This capability SHALL emit **five** codes: the two that describe the piece — the product's family holds other members, and the product declares no size label — and the three this capability adds once it routes, which are the two distinct refusal reasons and the one stating that the corpus does not cover an anchored question.

The two refusal codes MUST remain distinct from each other. A trade this shop does not practise and a piece this shop does not carry are two different things for an operator to say to a customer, and one shared code would make the two rates this capability publishes separately indistinguishable where a consumer reads them.

The service MUST NOT emit any warning that depends on real stock. Stock is the .NET API's authority and is known only after hydration, and the availability bucket this service holds is carried for ranking, is never emitted, and may be stale.

#### Scenario: A family with other members raises the variants warning
- **GIVEN** a product whose family holds more than one member
- **WHEN** the route is called anchored to that product
- **THEN** the warnings contain the code stating that the family holds other members

#### Scenario: A missing size label raises its warning
- **GIVEN** a product that declares no size label
- **WHEN** the route is called anchored to that product
- **THEN** the warnings contain the code stating that the size label is absent

#### Scenario: Every warning belongs to the closed vocabulary
- **WHEN** any response is produced
- **THEN** every warning it carries is a member of the declared closed vocabulary
- **AND** none of them is a sentence in natural language

#### Scenario: The two refusal codes are two and never one
- **WHEN** the closed vocabulary is inspected
- **THEN** the code for a query outside the domain differs from the code for a query this catalogue cannot stock
- **AND** both belong to the same declared vocabulary the rule-derived codes belong to

#### Scenario: No stock warning is emitted by this service
- **GIVEN** a product whose availability bucket at the requesting point of sale is zero
- **WHEN** the route is called anchored to that product
- **THEN** the warnings contain no code about critical stock and none about members out of stock

### Requirement: The variants warning is computed from the family roster, not from the candidates retrieved
The warning stating that a family holds other members SHALL be computed from the family's full roster as the index holds it, and MUST NOT be inferred from how many members the retrieval happened to return. Grouping operates over retrieved candidates; knowing that a member exists which was not retrieved requires reading the roster.

The roster MUST be read from the index schema only, and MUST be capped at a declared maximum so a large family cannot produce an unbounded read.

#### Scenario: The warning fires on a member the retrieval did not return
- **GIVEN** a product belonging to a family of four members, of which the retrieval returned two
- **WHEN** the route is called
- **THEN** the variants warning is raised
- **AND** the reason it is raised is the roster's count and not the candidate count

#### Scenario: A family of one raises no variants warning
- **GIVEN** a product whose family holds only that product
- **WHEN** the route is called
- **THEN** the variants warning is not raised

#### Scenario: The roster is bounded
- **GIVEN** a family whose membership exceeds the declared cap
- **WHEN** the roster is read
- **THEN** it returns at most the capped number of members
- **AND** the cap is a declared value and not an incidental limit

### Requirement: A piece with no question is grounded by deterministic addressing, never by a search
When the request anchors a piece and asks no question, the service SHALL obtain its citable fragments by addressing them directly by identity, from the material sheets of the materials the product declares, over an explicit allow-list of sections. It MUST NOT run a similarity search for this mode, because the address is exact and a search could return a fragment about another material.

The service MUST include **only** fragments whose claim scope is general. A fragment that records a commitment of the establishment MUST NOT enter an argument nobody asked for.

The number of materials considered and the allow-list of sections MUST be parameters of the call and not inlined constants, so a later change can compare configurations in one process.

#### Scenario: The citations come from the declared materials' sheets
- **GIVEN** a product declaring one canonical material
- **WHEN** the route is called anchored to that product with no question
- **THEN** the citations are fragments of that material's sheet
- **AND** they belong to the declared allow-list of sections

#### Scenario: No sheet of an undeclared material is cited
- **GIVEN** a product declaring one canonical material
- **WHEN** the route is called anchored to that product with no question
- **THEN** no citation comes from the sheet of any material the product does not declare

#### Scenario: A commitment of the establishment never enters an unrequested argument
- **GIVEN** a product whose declared material has a sheet carrying a section of establishment scope
- **WHEN** the route is called anchored to that product with no question
- **THEN** no citation carries the establishment claim scope

#### Scenario: No similarity search runs for this mode
- **WHEN** the route is called anchored to a product with no question
- **THEN** no vector search over the knowledge index is performed
- **AND** no embedding provider call is made

#### Scenario: A piece declaring two materials also receives the mixed-piece guidance
- **GIVEN** a product declaring two canonical materials
- **WHEN** the route is called anchored to that product with no question
- **THEN** the citations also include the mixed-piece section about which part governs

### Requirement: Citations are corpus fragments carrying their scope, and the catalogue is never cited
Citations SHALL be fragments of the commercial knowledge corpus and nothing else. Each citation MUST carry its resolvable citation identifier, its document title, its section title, its document type and its **claim scope**, so that a commitment of the establishment is distinguishable from a fact of the world by the consumer that renders it.

The service MUST NOT emit a citation that points at a product or at the catalogue: the product's metadata already travels in the response, so citing it would verify nothing. The grounding of a candidate in the catalogue is expressed through its match reasons.

The citations of a response are **the ones the generated argument used** when there is an argument, and the ones that grounded the response when there is none. Emitting everything retrieved is not attribution but decoration, and a citation whose use cannot be verified is withheld rather than published.

#### Scenario: A citation resolves and locates
- **WHEN** a citation is returned
- **THEN** it carries its citation identifier, its document title and its section title

#### Scenario: The claim scope travels with every citation
- **WHEN** a citation is returned
- **THEN** it carries its claim scope
- **AND** the scope is one of the values the corpus declares

#### Scenario: The catalogue is never cited
- **WHEN** any response is produced
- **THEN** no citation refers to a product or to the catalogue as its source

#### Scenario: A response carrying an argument publishes only the citations it used
- **GIVEN** a request whose context offered more fragments than the argument used
- **WHEN** the response carries a generated argument
- **THEN** only the citations the argument declared and that were verified are published

### Requirement: Abstention is honoured and declared in a field of its own
The service SHALL return no group when the retrieval layer's abstention rule decides that the catalogue cannot answer the query, and MUST declare the abstention in a dedicated boolean field of the response. The field MUST be emitted in every mode, and in the piece-anchored mode with no question its value MUST be false, because there is no retrieval to abstain from.

The service MUST NOT express this decision by reusing the cross-branch confidence signal, whose measured meaning is a different one.

The effective value of the abstention configuration MUST travel as a parameter of the call rather than being read from the environment inside, so an evaluation can compare configurations in one process.

#### Scenario: An abstained query returns nothing and says so
- **GIVEN** a query for which the abstention rule fires
- **WHEN** the route is called with it
- **THEN** the abstention field is true
- **AND** no group is returned

#### Scenario: An answerable query is not silenced
- **GIVEN** a query the catalogue can answer
- **WHEN** the route is called with it
- **THEN** the abstention field is false
- **AND** at least one group is returned

#### Scenario: The field is always present
- **WHEN** any response is produced in any mode
- **THEN** the abstention field is present
- **AND** in the piece-anchored mode with no question its value is false

### Requirement: An unusable piece is an error and never an abstention
When the request anchors a product that the index does not hold, or holds as inactive, or holds without an embedding, the service SHALL answer with an error that distinguishes the three cases. It MUST NOT answer successfully with the abstention field set, because that would assert that the catalogue cannot answer when the problem is the piece.

#### Scenario: An unknown product is an error
- **WHEN** the route is called anchored to a product the index does not hold
- **THEN** the response is an error naming that case

#### Scenario: An inactive product is a different error
- **WHEN** the route is called anchored to a product the index holds as inactive
- **THEN** the response is an error naming that case

#### Scenario: A product without an embedding is a third error
- **WHEN** the route is called anchored to a product the index holds without an embedding
- **THEN** the response is an error naming that case

#### Scenario: None of the three is served as an abstention
- **WHEN** any of the three unusable cases occurs
- **THEN** the response is not a success with the abstention field set

### Requirement: No price and no stock figure appears anywhere in the response
The response SHALL contain no concrete price and no stock quantity in **any** field, not only in the generated argument. The index holds a copy of the price for ordering and holds an availability bucket for demotion, and neither may cross the boundary: the .NET API is the authority on both.

#### Scenario: The whole response is free of price and stock figures
- **WHEN** the route is served in any mode
- **THEN** no field of the response carries a price
- **AND** no field carries a stock quantity or an availability bucket

### Requirement: With stubs disabled the route serves the real implementation
When `STUB_MODE` is disabled, `POST /v1/assist/sale` SHALL serve the real implementation and MUST NOT answer HTTP 501: the placeholder that named a future change no longer applies. When `STUB_MODE` is enabled, the route MUST keep serving a deterministic fixture that performs no external input or output.

The fixture MUST include at least one group with a null family identifier, so that a client cannot ship without ever handling the case that is the majority of the catalogue.

#### Scenario: The route no longer answers 501 with stubs disabled
- **GIVEN** `STUB_MODE` is disabled
- **WHEN** an authenticated client calls the route with a valid body
- **THEN** the response status is not 501

#### Scenario: The fixture stays deterministic
- **GIVEN** `STUB_MODE` is enabled
- **WHEN** the route is called twice with the same body
- **THEN** both responses are identical
- **AND** no database, provider or network call is made

#### Scenario: The fixture exercises the absent family
- **GIVEN** `STUB_MODE` is enabled
- **WHEN** the route is called
- **THEN** at least one returned group carries a null family identifier

### Requirement: Assistance tests run offline
The tests of this capability SHALL run with no call to a language model, to an embedding provider or to a managed database. Fakes MUST be injected through the existing constructor seams and fixtures MUST live in the service's test tree. Tests that require a database MUST use an ephemeral container and MUST skip when it is unreachable rather than failing.

#### Scenario: No external call is made by the suite
- **WHEN** the assistance tests run
- **THEN** no language model, embedding provider or managed database is contacted

#### Scenario: Database tests skip when the container is unavailable
- **GIVEN** the container runtime is unreachable
- **WHEN** the tests that need a database run
- **THEN** they are skipped rather than reported as failures

### Requirement: The assistance layer writes a sale argument in the piece-anchored modes
The service SHALL generate a prose sale argument through a language model in the two modes anchored to a piece — the piece with no question and the piece with a question — and MUST report the version of the prompt it used and the model usage it consumed. The argument MUST be grounded only in the structured payload and the corpus fragments handed to the model, and MUST NOT introduce any product, material or property that payload does not carry.

The argument is prose and not a list: the generation MUST be instructed to write continuous prose without numbered lists, because a leading enumeration numeral is a figure the numeric gate cannot distinguish from an invented one, and removing the source of that rejection is preferable to excusing it in the gate.

#### Scenario: A piece with no question receives an argument
- **GIVEN** a product that is indexed and declares at least one material
- **WHEN** the assistance is requested with its product identifier and no question
- **THEN** the generated argument is not empty
- **AND** the prompt version is reported
- **AND** the reported usage carries a non-zero token count and the model identifier

#### Scenario: A question about the piece is answered in prose
- **GIVEN** a product that is indexed and a question about it
- **WHEN** the assistance is requested with both anchors
- **THEN** the generated argument addresses the question
- **AND** at least one citation of the corpus supports it
- **AND** no citation comes from the sheet of a material the piece does not declare

### Requirement: No figure absent from the given context reaches the generated argument
Every numeric sequence in the generated argument SHALL belong to the set of numerals present in the structured payload handed to the model, and any other numeric sequence MUST be treated as a violation. The check MUST read the payload object rather than the rendered prompt, because numerals belonging to the instructions themselves would otherwise widen the admitted set and open the gate on their own.

Independently of that set, a numeric sequence adjacent to a currency marker or to an expression of stock MUST be treated as a violation **even when the numeral is present in the payload**. The corpus itself carries round figures that are plausible prices — the sheets state that eighteen carats are seven hundred and fifty thousandths and that sterling silver is nine hundred and twenty-five thousandths — so membership alone admits a figure that reads as a price. Price and stock travel as placeholders, which is what makes any figure next to a currency marker wrong by construction.

#### Scenario: A figure absent from the context is rejected even when plausible
- **GIVEN** a generated argument carrying a weight in grams that the payload does not contain
- **WHEN** the numeric gate is evaluated
- **THEN** the figure is recorded as a violation

#### Scenario: A figure adjacent to a currency marker is rejected even when admitted by the payload
- **GIVEN** a material sheet in the context whose text contains the figure seven hundred and fifty
- **WHEN** the generated argument writes that figure next to a currency marker
- **THEN** it is recorded as a violation
- **AND** the recorded cause distinguishes currency adjacency from absence of the figure in the context

#### Scenario: Price and stock travel as placeholders
- **GIVEN** a piece whose price and stock are known to the index
- **WHEN** the argument mentions price or availability
- **THEN** it carries the price and stock placeholders
- **AND** no field of the whole response carries a price or a stock quantity

### Requirement: A published citation is one the argument used, and the claim it supports is verifiable
The model SHALL declare, for every citation it uses, the fragment of its own generated argument that the citation supports, and the service MUST verify in code that the declared identifier belongs to the set of fragments handed to the model and that the declared fragment occurs literally in the argument that was produced. Verifying that the identifier resolves is not sufficient on its own: a model that echoes back every identifier it was given satisfies resolution perfectly while having used none, so the claim of use MUST be made checkable rather than trusted.

The declared fragment is an internal verification artefact and MUST NOT be emitted in the response. Comparison MUST be insensitive to letter case and to runs of whitespace, and MUST NOT otherwise alter the text.

#### Scenario: The model declares which fragment each citation supports
- **WHEN** an argument is generated with citations
- **THEN** each cited identifier carries the fragment of the argument it supports
- **AND** that fragment occurs in the generated argument

#### Scenario: The declared fragment does not reach the response
- **WHEN** a response carrying an argument is produced
- **THEN** no field of the response exposes the declared supporting fragment

#### Scenario: Echoing every supplied identifier does not satisfy the requirement
- **GIVEN** a model that declares every identifier it was handed
- **WHEN** the declared fragments do not occur in the generated argument
- **THEN** those citations are not published

### Requirement: A failed check is repaired once, and persistent failure degrades the response instead of the service
The service SHALL attempt at most one repair per request, communicating every violation of every check together rather than one repair per check, and MUST evaluate the checks in order of cost: citation resolution first, then the correspondence of the declared fragment, then the numeric gate. The provider MUST NOT be called more than twice for one request.

A violation of citation resolution or of the numeric gate that survives the repair MUST result in the response being served **without** the generated argument. A failure of correspondence that survives the repair MUST result in **that citation** being withheld while the argument is still served, because the fragment exists and was in the context and what failed is the model's own account of using it. A dangling citation MUST NEVER be ignored.

#### Scenario: Two checks fail and share a single repair
- **GIVEN** a generated argument that violates citation resolution and the numeric gate at once
- **WHEN** the repair policy is applied
- **THEN** exactly one repair is attempted with both violations communicated together
- **AND** the provider is called no more than twice for that request

#### Scenario: A dangling citation survives the repair and the argument is dropped
- **GIVEN** a declared identifier that was never in the set handed to the model
- **WHEN** the repair does not resolve it
- **THEN** the response is served with an empty generated argument
- **AND** the dangling identifier is not published

#### Scenario: An unverifiable claim withdraws its citation and keeps the argument
- **GIVEN** a declared fragment that does not occur in the generated argument
- **WHEN** the repair does not resolve it
- **THEN** that citation is withheld from the response
- **AND** the generated argument is still served

### Requirement: Degradation preserves what the structured layer already produced
When the generated argument is withheld for any reason, the response SHALL still carry the citations that grounded it, so that a degraded response is never poorer than the one the structured layer produces on its own. The citations of a response are the ones the argument used when there is an argument, and the ones that grounded the response when there is none.

This is what keeps the generation layer measurable as an ablation against the structured layer: the comparison requires the same route, the same candidates and the same citations, with prose and without it.

#### Scenario: The argument is dropped and the citations remain
- **GIVEN** a request whose generated argument was withheld
- **WHEN** the response is composed
- **THEN** the citations that grounded the response are present
- **AND** no field of the response is poorer than the one the structured layer produces alone

### Requirement: The reported prompt version states whether the generation layer ran
The service SHALL report the prompt version whenever the generation layer ran, including when its argument was withheld, and MUST report it as absent when the layer did not run. An empty argument alone cannot distinguish a deployment that does not generate from a generation that was rejected, and that distinction is the only evidence a consumer has that the guard acted.

#### Scenario: A rejected argument still reports its prompt version
- **GIVEN** a request whose generated argument was withheld after the repair
- **WHEN** the response is composed
- **THEN** the generated argument is empty
- **AND** the prompt version is reported

#### Scenario: A mode that does not generate reports no prompt version
- **WHEN** the free-query mode is served
- **THEN** the generated argument is empty
- **AND** the prompt version is absent

### Requirement: The generated argument is never persisted, and that includes never being logged
The service SHALL NOT write the generated argument to any durable store, and MUST NOT write its text to any log. Serving one request MUST execute no data-manipulation statement. The log line MUST carry the correlation identifier, the prompt version, the model, the usage, the latency, the identifiers of the citations used, the warning codes, the abstention decision, the length of the argument and a hash of it — and MUST NOT carry the text itself.

A log line is durable storage outside the database and carries no point-of-sale scope, while the response does; the text is re-derivable from a versioned prompt at temperature zero, which is what makes not storing it viable. The evaluation harness is the **declared exception**: it MAY store generated arguments together with their declared supporting fragments, bound to a run identifier, a commit identifier and a prompt version, outside the serving path.

#### Scenario: Serving a request writes nothing
- **WHEN** a request producing a generated argument is served
- **THEN** no data-manipulation statement is executed against the database

#### Scenario: The log carries the provenance and not the text
- **WHEN** a request producing a generated argument is served
- **THEN** the log records the prompt version, the model, the usage, the citation identifiers, the length and a hash
- **AND** the log does not contain the text of the generated argument

### Requirement: The prompt is versioned and pinned to the file it is loaded from
The prompt SHALL be stored as a versioned file in the service's prompt directory and its identifier MUST be a constant that a test pins to that file, so the reported version cannot drift from the text actually used. Invariant rules MUST live in the system message and the per-mode task MUST live in the user message, so that one version covers both piece-anchored modes.

#### Scenario: The declared version and the loaded file agree
- **WHEN** the generation prompt is loaded
- **THEN** it comes from the file the declared version names
- **AND** a test fails if the constant and the file cease to correspond

### Requirement: The provider is not called when there is nothing to write about
The service SHALL NOT call the language model provider when the abstention rule has decided that the catalogue cannot answer the query, when the router has refused the request, or when a clarification question has been emitted. Writing prose about an empty candidate set states something with confidence about nothing, which is the failure the abstention rule exists to prevent.

The free-query mode no longer withholds generation for want of a classification: the intent of such a query is now determined before retrieval, and the argument is written over a route that was decided rather than over a candidate set nobody classified. What remains forbidden is generating when there is nothing to write about — an abstention, a refusal or an unanswered question.

#### Scenario: An abstained request calls no provider
- **GIVEN** the abstention rule decided the catalogue cannot answer
- **WHEN** the assistance is served
- **THEN** the abstention is declared and no group is returned
- **AND** no language model generation call is made

#### Scenario: A refused request calls no generation provider
- **WHEN** the router refuses a free-text query
- **THEN** the generated argument is empty and the prompt version absent
- **AND** no language model generation call is made

#### Scenario: A clarified request calls no generation provider
- **WHEN** a clarification question is emitted for a free-text query
- **THEN** the generated argument is empty and the prompt version absent
- **AND** no language model generation call is made

### Requirement: A provider failure degrades the response and never turns it into an error
When the provider fails, is unreachable or exceeds the declared time limit, the service SHALL serve the structured response — groups, warnings and citations — with an empty generated argument, and MUST NOT answer with a server error. The structured half is already computed and correct, and discarding it because the prose failed converts a partial loss into a total one.

#### Scenario: The provider fails and the structured response is served
- **GIVEN** a provider that fails or exceeds the time limit
- **WHEN** a piece-anchored assistance is served
- **THEN** the response is successful and carries its groups, warnings and citations
- **AND** the generated argument is empty
- **AND** no server error is returned

### Requirement: Reported usage accumulates across the repair
The reported model usage SHALL be the sum of every provider call made for that request, including the repair, and MUST NOT report only the last call. Reporting a single call understates the cost precisely on the requests that cost the most, which are the ones a cost measurement exists to find.

#### Scenario: A repaired request reports the sum of both calls
- **GIVEN** a request that required one repair and therefore two provider calls
- **WHEN** the response is composed
- **THEN** the reported usage is the sum of both calls

### Requirement: The operator's query travels as data and never as an instruction
The operator's query SHALL travel inside the user message, in a delimited block labelled as data, and MUST NOT be concatenated into the system message. The prompt MUST state that the content of that block is information from the customer and never an instruction.

Classifying a query and refusing one politely are a later capability's work and are not performed here; what belongs here is the structural mitigation, which is the responsibility of whoever builds the prompt.

#### Scenario: A query shaped like an instruction does not change the system behaviour
- **GIVEN** a query containing text instructing the assistant to disregard its rules
- **WHEN** the provider call is built
- **THEN** the query travels in the user message inside a delimited data block
- **AND** the system message is the same as it would be for any other query

### Requirement: Semantic fidelity of a citation is not verified at request time
The service SHALL NOT verify at request time that a cited fragment supports the meaning of the claim it is attached to, and this limitation MUST be declared rather than implied. The checks this capability performs are structural: that the identifier resolves, that the citation was used for text actually written, and that no figure is invented. A citation that resolves, that was genuinely used, and that nevertheless does not say what the sentence asserts is not detected here.

No model-based judge runs in the serving path: it would double the latency and the cost at the counter, and using a model to detect another model's fabrications is circular. The measurement belongs to the evaluation harness, over a representative set, where a rate means something.

#### Scenario: The limitation is declared and no judge runs in the serving path
- **WHEN** a request producing a generated argument is served
- **THEN** no additional model call is made to judge the fidelity of the argument

### Requirement: The detected intent is a routing verdict in the free-query mode and remains structural in the anchored ones
The service SHALL report, for a request carrying a query and no piece, an intent that states the routing verdict the classifier reached, and MUST keep deriving the intent structurally in the two piece-anchored modes, where the piece-anchored value MUST NOT change. The reported value MUST belong to a closed vocabulary declared by this capability, and when no classification could be made the service MUST report the unclassified value rather than guessing one.

The unclassified value therefore carries a second meaning from this capability onwards: it no longer states that queries are not classified at all, it states that this particular request could not be classified. Both readings are honest and a consumer needs no new field to tell them apart, because the log records why.

#### Scenario: A piece with no question keeps its determinate intent
- **WHEN** the route is called with a product identifier and no query
- **THEN** the reported intent is the piece-anchored one, unchanged from before this capability routed anything
- **AND** no classifier call is made

#### Scenario: A free query reports the verdict the router reached
- **WHEN** the route is called with a query and no piece
- **THEN** the reported intent is the routing verdict
- **AND** the value belongs to the closed vocabulary of this capability

### Requirement: A query that is not about jewellery is refused before any retrieval runs
The service SHALL classify a free-text query that falls outside the jewellery domain and MUST refuse it without executing the product retrieval or the knowledge search, returning a successful response with no group and a refusal reason code from a closed vocabulary. The refusal MUST NOT be expressed as prose written by the model, because the Spanish a human reads belongs to the presentation layer.

#### Scenario: An out-of-domain query short-circuits before retrieval
- **WHEN** a query unrelated to the jewellery business is served
- **THEN** no product retrieval and no knowledge search are executed
- **AND** no group is returned and the response is successful
- **AND** the reported intent states that the query is out of domain
- **AND** a refusal reason code from the closed vocabulary is present

### Requirement: A jewellery query this catalogue cannot stock is refused, and that refusal is distinct from being out of domain
The service SHALL classify a free-text query that is plausible within jewellery but asks for a kind of object this catalogue does not stock, and MUST refuse it before retrieving, with a reason code that is distinct from the out-of-domain one. These two refusals MUST NOT share a code, because what an operator says to a customer differs between a trade the shop does not practise and a piece the shop does not carry.

#### Scenario: A neighbouring-trade request is refused with its own code
- **GIVEN** a query asking for an object a jewellery shop might sell and this catalogue does not carry
- **WHEN** the assistance is served
- **THEN** no group is returned and no retrieval is executed
- **AND** the reason code differs from the one used for an out-of-domain query

#### Scenario: An answerable query is never refused
- **GIVEN** a query belonging to any answerable category of the evaluation set, including those that name no piece type at all
- **WHEN** the assistance is served
- **THEN** the router admits it
- **AND** the retrieval is executed and groups are returned

### Requirement: A query that does not carry enough to search receives a clarification question instead of candidates
The service SHALL emit a clarification question when the classifier determines that the query lacks the information needed to search, and MUST return no group and call no generation provider in that case. The clarification question MUST name the axis the query left out rather than asking for more detail in general terms.

#### Scenario: An ambiguous query is answered with a question
- **GIVEN** a query that does not determine what is being asked for
- **WHEN** the assistance is served
- **THEN** the clarification question is present and written in Spanish
- **AND** no group is returned
- **AND** no generation provider call is made

### Requirement: The clarification question is resolved in code from a closed catalogue of templates
The service SHALL select the text of the clarification question in code, from a closed catalogue of templates keyed by the missing axis, and MUST NOT publish text the language model wrote for that field. Two requests carrying the same query MUST produce exactly the same clarification text.

The contract types this field as prose rather than as a code, so the presentation layer cannot resolve it the way it resolves warning codes. Resolving it in code preserves determinism without changing the type, and keeps model-written prose out of a field that no numeric gate inspects.

#### Scenario: The same query always yields the same question
- **GIVEN** a query the classifier reports as insufficient
- **WHEN** the assistance is served twice
- **THEN** the clarification text is identical on both occasions
- **AND** the text corresponds to the axis the classifier reported as missing

### Requirement: The router's refusal is never expressed by reusing the abstention flag
The service SHALL report false in the abstention field when the router refused the request, and MUST carry the refusal in the intent and in the reason code instead. A request that reaches the retrieval and triggers the abstention rule MUST keep declaring the abstention exactly as before.

The two decisions come from different mechanisms: the abstention rule reads the shape of the distance profile after retrieving, and the router classifies before retrieving. Collapsing them onto one field would make the two rates this capability publishes indistinguishable from each other.

#### Scenario: A refused request does not claim to have abstained
- **WHEN** the router refuses a query
- **THEN** the abstention field is false
- **AND** the refusal is stated through the intent and the reason code

#### Scenario: An abstained request still declares its abstention
- **GIVEN** a query the router admits and for which the abstention rule then fires
- **WHEN** the assistance is served
- **THEN** the abstention field is true

### Requirement: The piece-anchored question mode is routed structurally and consults both indexes
The service SHALL treat a request carrying both a piece and a question as addressed to the catalogue and the corpus at once, deriving that from the request shape, and MUST NOT call the classifier in that mode. Refusing there would refuse a piece the caller named explicitly, which is a statement about the request that this service has not established.

#### Scenario: An anchored question makes no classifier call
- **WHEN** a request carrying a product identifier and a question is served
- **THEN** both indexes are consulted
- **AND** no classifier call is made
- **AND** the total provider calls for that request do not exceed the generation ceiling

### Requirement: A question the corpus does not cover is declared by a warning code and costs no extra provider call
The service SHALL emit a warning code from the closed vocabulary when an anchored question produces no citation after the knowledge distance threshold has been applied, and MUST determine this from the search result already computed rather than by making an additional provider call. The generated argument MUST then describe the piece without asserting that the question was answered.

Zero citations after that threshold already means the corpus cannot answer the question: the separation was measured when the threshold was calibrated. What was missing was a consumer able to tell that case apart from there being nothing worth citing.

#### Scenario: An uncovered question is declared rather than silently ignored
- **GIVEN** an anchored request whose question yields no citation after the threshold
- **WHEN** the assistance is served
- **THEN** the citation list is empty and the warning code is present
- **AND** no additional provider call was made to establish it
- **AND** the generated argument does not claim to answer the question

### Requirement: The free-query mode writes a sale argument over the route the classifier decided
The service SHALL generate prose for a free-text query the router admitted, selecting the task section of the prompt according to the route the classifier decided, and MUST report the prompt version it ran with. It MUST NOT generate when the router refused the request, when a clarification question was emitted, or when the abstention rule fired.

The task sections of this mode MUST NOT instruct the model to write the price or the availability placeholders, and MUST forbid stating a price or a quantity of units at all, because the placeholders name no product and an argument that speaks about several pieces cannot be resolved against any one of them. Comparative language that carries no figure remains permitted, since the operator has the hydrated prices on the same screen.

#### Scenario: An admitted free query receives an argument
- **GIVEN** a free query the router admits and for which candidates are returned
- **WHEN** the assistance is served
- **THEN** the generated argument is not empty
- **AND** the prompt version is reported
- **AND** the task section used corresponds to the decided route

#### Scenario: The free-query argument carries no placeholder
- **GIVEN** a free query whose route returns pieces
- **WHEN** the argument is generated
- **THEN** it contains neither the price placeholder nor the stock placeholder
- **AND** it states neither a price nor a quantity of units

### Requirement: No figure absent from the free-query context reaches its generated argument
The service SHALL admit, in the argument generated for a free-text query, only figures literally present in the material handed to the model, and MUST exclude from that material the internal product identifiers and the retrieval scores. Price and availability MUST travel as placeholders in this mode exactly as they do in the piece-anchored ones.

Each candidate admitted into the material widens the set of admissible figures, which is why the identifiers and the scores are excluded explicitly: their digits are arbitrary and a counter argument never mentions them.

#### Scenario: An invented figure is refused in the free-query mode too
- **GIVEN** a free query that produced several groups of candidates
- **WHEN** the generated argument contains a figure absent from the material handed to the model
- **THEN** the argument is refused by the same gate that governs the anchored modes

#### Scenario: Internal identifiers do not widen the admissible set
- **WHEN** the material for a free-text query is composed
- **THEN** it carries no internal product identifier and no retrieval score

### Requirement: An unavailable classifier degrades to the unclassified intent and to the previous behaviour
The service SHALL serve a successful response when the classifier has no credential, fails, exceeds its time limit or returns something that does not parse, reporting the unclassified intent and proceeding with the retrieval exactly as it did before this capability routed anything, and MUST record the degradation and its cause in the log. It MUST NOT answer with a server error and MUST NOT refuse the request on the classifier's behalf.

Failing closed would turn a provider interruption into a universal polite refusal, which is a total outage of the useful path. Failing open degrades to a behaviour that is already shipped, tested and declared, and the abstention rule remains in place as the net it was.

#### Scenario: A classifier fault does not change the outcome of an answerable query
- **GIVEN** a classifier that is unavailable, times out or returns an unparseable reply
- **WHEN** a free-text query is served
- **THEN** the response is successful and the reported intent is the unclassified one
- **AND** the retrieval is executed and the abstention rule still applies
- **AND** the degradation and its cause are recorded in the log

#### Scenario: No classifier credential is a valid deployment state
- **GIVEN** a deployment that configures no credential for the classifier
- **WHEN** a free-text query is served
- **THEN** no classifier call is attempted
- **AND** the response is the one this capability served before routing existed

### Requirement: One request makes at most three provider calls
The service SHALL make at most one classifier call and at most two generation calls for a single request, and the total MUST NOT exceed three. The classifier MUST NOT be retried and MUST NOT repair its own output, because an unparseable label is a degradation and not a violation to fix.

#### Scenario: The ceiling holds for a routed, generated and repaired request
- **GIVEN** a free-text query that is classified, generates and requires one repair
- **WHEN** the request completes
- **THEN** exactly three provider calls were made and never more
- **AND** the reported usage accumulates all of them

#### Scenario: An unparseable classifier reply is not retried
- **GIVEN** a classifier reply that does not parse
- **WHEN** the request is served
- **THEN** no second classifier call is made

### Requirement: The classifier's label is validated against a closed vocabulary before it is used
The service SHALL validate the label returned by the classifier against the closed vocabulary declared by this capability before acting on it, and MUST treat a value outside that vocabulary as an unparseable reply rather than propagating it. The action taken for each label MUST be determined in code and MUST NOT be delegated to the model.

The classification may be made by a model; the enforcement may not. This is what makes the guardrail a deterministic check around a non-deterministic component rather than an instruction the model is free to disregard.

#### Scenario: A label outside the vocabulary never reaches the response
- **GIVEN** a classifier reply carrying a label the vocabulary does not contain
- **WHEN** the request is served
- **THEN** the reply is treated as unparseable and the request degrades to the unclassified intent
- **AND** the unknown label does not appear in the response

### Requirement: The operator's query travels as data into the classifier call as well
The service SHALL place the operator's query inside a delimited block labelled as data within the user message of the classifier call, and MUST NOT concatenate it into the system message. A query written as an instruction MUST NOT change the classifier's system message.

#### Scenario: An instruction-shaped query does not alter the classifier's system message
- **GIVEN** a query containing text instructing the assistant to disregard its rules
- **WHEN** the classifier call is built
- **THEN** the query travels inside the delimited data block of the user message
- **AND** the system message is identical to the one used for any other query

### Requirement: The refusal rate of the router and the abstention rate of the retrieval are reported as separate figures
The evaluation SHALL report the router's refusal rate and the retrieval's abstention rate as distinct figures and MUST NOT present their sum as a single measure, and it MUST also report, as a figure of its own, the rate at which answerable queries are refused. A configuration that refuses any query of the unanchored descriptive category MUST be rejected regardless of how many impossible queries it catches.

The two rates come from different mechanisms and mean different things. Silencing a query the shop can answer is a visible failure at the counter, while failing to refuse an impossible one shows candidates that do not fit and the operator can see that, which is why the asymmetry decides the veto.

#### Scenario: The report keeps the two rates apart
- **WHEN** the routing evaluation is reported
- **THEN** the router's refusal rate and the retrieval's abstention rate appear as separate figures
- **AND** the report states that they are not summable
- **AND** the refusal rate over answerable queries is reported as a figure of its own

### Requirement: The classifier's prompt is derived from the catalogue vocabulary and never from the evaluation sets
The classifier's prompt SHALL be written from the closed catalogue vocabularies and the corpus documentation, and MUST NOT be derived from the annotations of the evaluation sets it will be measured against. The implementation MUST declare that this was observed.

The annotations of the golden set state the classification rule in words, so a prompt written from them would confirm itself by construction and the measurement would arbitrate nothing. This is the structural risk the golden set declared of its own construction, in a sharper form.

#### Scenario: The provenance of the prompt is declared
- **WHEN** the implementation is reported
- **THEN** it states that the classifier's prompt was written from the catalogue vocabularies and the corpus documentation
- **AND** it states that the annotations of the evaluation sets were not used to write it

### Requirement: The prompt version that adds the free-query task sections does not replace the previous one
The service SHALL introduce the free-query task sections in a new prompt version and MUST keep the previous version's file unchanged, so measurements taken against it stay interpretable. The reported prompt version MUST continue to be pinned to the file actually loaded.

#### Scenario: Both prompt versions exist and neither shadows the other
- **WHEN** the prompt files are inspected
- **THEN** the previous version's file is present and unmodified
- **AND** the reported prompt version matches the file that was loaded

### Requirement: The assistance request accepts the catalog-side filters the caller selected

The sale-assistance request SHALL accept the same catalog-side filters the retrieval request accepts, and the free-query mode MUST forward them to the retrieval it performs, so that this mode never knows less about what the operator asked for than the retrieval route it can be exchanged for.

A request carrying no filter MUST behave exactly as it did before this field existed, and the field MUST be optional so that a caller that does not send it is unaffected.

The anchored modes MUST ignore the field, because their candidate set is the family of the anchored piece and not a retrieval.

#### Scenario: A filtered free query retrieves only what the filter admits
- **GIVEN** a free query carrying a piece category filter
- **WHEN** the assistance is served
- **THEN** every piece in every group belongs to that category

#### Scenario: An absent filter changes nothing
- **WHEN** a free query carries no filter
- **THEN** the candidates are the ones the same query produced before the field existed

#### Scenario: An anchored mode ignores the filters
- **GIVEN** a request anchored to a piece and carrying a filter
- **WHEN** the assistance is served
- **THEN** the group is the family of the anchored piece
- **AND** the filter does not remove any member

### Requirement: A placeholder in a free-query argument is a hard violation that withholds the argument

The integrity gate SHALL reject an argument of the free-query mode that contains the price placeholder or the stock placeholder, treating it as a hard violation that withholds the whole argument, and MUST report it under a cause of its own within the closed vocabulary of violation causes so that its rate is readable partitioned by cause.

The check MUST apply only when the request carries no anchored piece, because in the anchored modes the placeholders are the required form and resolving them is the caller's contract.

A prompt instruction alone MUST NOT be relied upon for this: the guarantee is code that runs whatever the model does, and the instruction exists to make the violation rare rather than to make it impossible.

#### Scenario: A placeholder withholds the free-query argument
- **GIVEN** a free query whose generated argument contains the price placeholder
- **WHEN** the integrity gate runs
- **THEN** the argument is withheld
- **AND** the violation is reported under its own cause

#### Scenario: The anchored modes are unaffected
- **GIVEN** a request anchored to a piece whose argument contains the price placeholder
- **WHEN** the integrity gate runs
- **THEN** the argument is not withheld for that reason

#### Scenario: The rate is readable by cause
- **WHEN** a sweep of free-query generations is summarised
- **THEN** the count of arguments withheld for carrying a placeholder is reported separately from every other cause

### Requirement: A free query whose corpus returned nothing does not pretend to have answered

The service SHALL determine, for a free query routed to the knowledge corpus or to both indexes, whether any citation survived the knowledge distance threshold, and when none did MUST declare it with the same warning code the anchored question mode uses and MUST select a task section that forbids answering from memory.

That task section MUST instruct the model not to answer the question, not to evade it with a generality that reads like an answer, and not to cite anything, because with no fragment in the context any identifier it writes is invented and any claim it makes is unsupported.

The determination MUST be read from the search result already computed and MUST cost no additional provider call.

#### Scenario: A knowledge query with no corpus is declared
- **GIVEN** a free query routed to the knowledge corpus for which no citation clears the threshold
- **WHEN** the assistance is served
- **THEN** the response carries the warning code that declares the corpus does not cover the question

#### Scenario: The uncovered task forbids answering from memory
- **GIVEN** a free query routed to both indexes for which no citation clears the threshold
- **WHEN** the argument is generated
- **THEN** the task section used is the one for an uncovered free query
- **AND** the citations published are empty

#### Scenario: The determination costs no provider call
- **WHEN** a free query is served and the corpus returned nothing
- **THEN** the count of provider calls is the same as for a query whose corpus returned fragments

### Requirement: A served verdict that names no index is routed to both indexes rather than served without prose

The service SHALL treat a classifier verdict that admits the query, reports no missing axis and names no index as a routing to both indexes, because the verdict is internally contradictory — the schema reserves an absent index for a request that is not served, while admitting the query is serving it — and the fail-open already consults both indexes in that situation, so the candidates and the fragments the task needs have already been retrieved and paid for.

The contradiction MUST remain observable: the service MUST record a cause of its own for it, so its rate stays readable, and MUST NOT alter the response in any other way.

Serving that situation with candidates, citations and no prose MUST NOT happen, because it delivers citations hanging from a text that does not exist.

#### Scenario: A verdict without an index still generates
- **GIVEN** a classifier verdict that admits the query, reports no missing axis and names no index
- **WHEN** the assistance is served
- **THEN** both indexes are consulted
- **AND** an argument is generated over the task section for both indexes
- **AND** the prompt version is reported

#### Scenario: The contradiction is recorded
- **WHEN** a verdict without an index is coerced
- **THEN** the log line for the request carries the cause that names the absent index

#### Scenario: Citations never hang from an absent argument
- **WHEN** a free query returns citations
- **THEN** either an argument was generated, or the response is a refusal, a clarification, an abstention or a degraded classification

### Requirement: The agent's evidence task is served with a prompt version of its own that forbids the placeholders

The generation layer SHALL serve the agent's evidence task from a prompt version of its own in which the invariant ordering price and availability to be written as placeholders is replaced, for that task, by the rule the free-query tasks already carry: with no anchored piece, price and availability are not spoken of at all, while comparative language that names no figure remains allowed.

The version that serves the deterministic route MUST be left unchanged on disk and MUST keep serving that route, because it has published figures measured against it and a later change is going to measure it again. Editing it would make the statement of what each version added, and what it measured, false.

The new version's system section MUST be identical to that of the version it derives from, and that identity MUST be verified by a test rather than by review, since the two files are otherwise free to drift apart silently.

The previous version of the agent's task MUST also be preserved on disk, because the agent's published figures were measured against it.

The reported argument prompt version MUST continue to be pinned to the file actually loaded.

#### Scenario: The agent's argument carries no placeholder
- **GIVEN** the agent's evidence task served from its own prompt version
- **WHEN** an argument is generated over an unanchored payload of several pieces
- **THEN** it contains neither the price placeholder nor the stock placeholder

#### Scenario: Comparative language without figures is still allowed
- **WHEN** the same argument compares the pieces it presents
- **THEN** a comparison that names no figure is not treated as a violation

#### Scenario: The deterministic route's version is untouched
- **WHEN** the prompt directory and the reported versions are inspected after this change ships
- **THEN** the version serving the deterministic route is present and unmodified
- **AND** that route still reports it

#### Scenario: The system section of the two versions is identical
- **WHEN** the new version and the one it derives from are compared
- **THEN** their system sections are identical
- **AND** a test asserts that identity

#### Scenario: The agent's previous version is preserved
- **WHEN** the prompt directory is inspected
- **THEN** the version the agent's published figures were measured against is present and unmodified

#### Scenario: The reported version is the file that ran
- **WHEN** the agent produces an argument
- **THEN** the reported argument prompt version names the file that was loaded
