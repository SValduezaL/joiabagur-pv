## MODIFIED Requirements

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

## ADDED Requirements

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
