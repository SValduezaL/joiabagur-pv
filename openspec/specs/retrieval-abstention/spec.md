# retrieval-abstention Specification

## Purpose
The decision of whether to answer at all. The rule is fixed from the distribution of the best retrieval distance **per query** — the quantity that separates a query the catalogue can answer from one it cannot — and never from the distribution of distances per judged document, because the two answer different questions: a total overlap between the distances of relevant and irrelevant documents does not imply that the best hit of an answerable query cannot be separated from the best hit of an out-of-domain one. That distribution is published, the report states whether a single value separates the two populations, and the form of the rule is selected by a criterion recorded before the distribution was inspected.

An abstention is a decision about the query applied to the whole response, never candidates removed one by one: it returns no candidate and marks the response low confidence, so a deliberate abstention stays distinguishable from a dependency failure and from an empty assortment, both of which keep failing loudly instead of being served behind it. A rule is adopted only when it raises the abstention rate over the out-of-domain category **and** leaves the answerable queries answered; both sides of that trade are published for every candidate rule, and a query whose labelled relevant set is non-empty that the rule silences is reported as a cost weighed explicitly rather than absorbed into an aggregate.

The golden set carries enough out-of-domain queries for the rate to be a usable figure, and the count is recorded with the set and validated on load. Those queries are plausible within the jewellery domain and impossible for the catalogue rather than nonsense text, because a rule measured against nonsense discriminates nothing; adding one needs no per-document judgement, since every document is grade zero for it by the annotation criterion. The adopted rule declares whether it alters the candidate set or only the decision to serve it, because a calibration that re-scores persisted candidate windows is valid only while the candidate set is unchanged. The stage logs the rule in force, the best observed distance and the decision taken beside the other stages and never an embedding vector, and its tests run offline against fixtures, including the answerable query that must not be abstained on.

## Requirements

### Requirement: The abstention rule is fixed from the per-query best-hit distribution, not from the per-document one
The abstention rule MUST be chosen from the distribution of the **best retrieval distance per query**, separating queries the catalogue can answer from queries it cannot. It MUST NOT be chosen from the distribution of distances per judged document, because the two answer different questions: a total overlap between the distances of relevant and irrelevant **documents** does not imply that the best hit of an answerable **query** cannot be separated from the best hit of an out-of-domain one.

That distribution MUST be published, and the report MUST state whether a single value separates the two populations. The form of the rule MUST be selected by a criterion written **before** the distribution is inspected.

#### Scenario: The per-query distribution is published
- **WHEN** the abstention calibration completes
- **THEN** the report contains the best-hit distance distribution of the answerable queries and of the out-of-domain ones
- **AND** states whether a single value separates them

#### Scenario: The selection criterion precedes the measurement
- **WHEN** the abstention rule is adopted
- **THEN** the report cites a criterion recorded before the distribution was inspected
- **AND** names which of the declared forms that criterion selected

#### Scenario: The per-document distribution does not decide the form
- **WHEN** the report justifies the chosen form
- **THEN** the justification rests on the per-query best-hit distribution
- **AND** the per-document distribution is cited as a distinct measurement rather than as the reason

### Requirement: Abstention decides whether to answer and never silently returns an empty page
When the rule decides that the catalogue has no answer, the response MUST return no candidate **and** MUST be marked low confidence, so that a deliberate abstention is distinguishable from a dependency failure and from an empty assortment. A dependency failure MUST continue to fail loudly rather than being served behind an abstention.

An abstention MUST NOT be produced by removing candidates one by one: it is a decision about the query, applied to the whole response.

#### Scenario: A plausible but impossible query is abstained on
- **GIVEN** a query that is plausible in the domain and that the catalogue cannot satisfy
- **WHEN** the retrieval runs with the abstention rule active
- **THEN** no candidate is returned
- **AND** the response is marked low confidence

#### Scenario: A dependency failure is not disguised as an abstention
- **GIVEN** the embedding provider fails and no lexical candidate exists
- **WHEN** the request is served
- **THEN** it fails loudly
- **AND** it is not served as an abstention with an empty candidate list

#### Scenario: An empty assortment is not an abstention either
- **GIVEN** the point-of-sale projection holds no assigned product for the requesting token
- **WHEN** the request is served
- **THEN** it fails loudly as the projection capability defines
- **AND** it is not reported as an abstention

### Requirement: Raising abstention on out-of-domain queries must not cost answers on answerable ones
An abstention rule MUST NOT be adopted unless it raises the abstention rate over the out-of-domain category **and** leaves the answerable queries answered. The report MUST publish both figures for every candidate rule: the abstention rate over out-of-domain queries and the number of answerable queries that became abstentions.

A rule that abstains on any query whose labelled relevant set is non-empty MUST be reported as costing an answer, and that cost MUST be weighed explicitly rather than absorbed into an aggregate.

#### Scenario: Both sides of the trade are published
- **WHEN** a candidate abstention rule is evaluated
- **THEN** the report gives its abstention rate over out-of-domain queries
- **AND** the number of answerable queries it turned into abstentions

#### Scenario: A rule that silences answerable queries is not adopted on the aggregate alone
- **GIVEN** a candidate rule that raises out-of-domain abstention
- **AND** abstains on queries whose labelled relevant set is non-empty
- **WHEN** the decision is taken
- **THEN** that cost is reported for each affected query
- **AND** the decision states it explicitly rather than citing only the aggregate

### Requirement: The out-of-domain category is large enough to calibrate against
The golden set MUST carry enough out-of-domain queries for an abstention rate to be a usable figure, and the count MUST be recorded with the set. Out-of-domain queries MUST be plausible within the domain and impossible for the catalogue, never nonsense text, because a rule measured against nonsense discriminates nothing.

Because every document is grade zero for an out-of-domain query by the annotation criterion, adding such a query MUST NOT require per-document judgements.

#### Scenario: The out-of-domain count is recorded and sufficient
- **WHEN** the golden set is loaded
- **THEN** the number of out-of-domain queries is reported
- **AND** the load fails if it falls below the declared minimum

#### Scenario: An out-of-domain query is plausible and impossible
- **GIVEN** a query in the out-of-domain category
- **WHEN** it is reviewed
- **THEN** it names something a customer could plausibly ask a jeweller for
- **AND** the catalogue contains nothing that satisfies it

#### Scenario: Adding an out-of-domain query needs no per-document labelling
- **WHEN** an out-of-domain query is added to the golden set
- **THEN** no per-document judgement is required for it
- **AND** every retrieved document counts as grade zero by the annotation criterion

### Requirement: Whether the abstention rule alters the candidate set is declared
The adopted rule MUST declare whether it changes which candidates are retrieved or only whether they are served, and MUST also declare which distance profile it reads. A rule expressed as a distance bound inside the retrieval statement changes the candidate set; a rule applied after fusion does not.

That declaration MUST be recorded with the rule, because a calibration that re-scores persisted candidate windows is only valid while the candidate set is unchanged and while the profile the rule read is recoverable from what was persisted.

When the rule reads a distance profile other than the one the served candidates came from, that profile MUST be persisted alongside the candidate window, so a re-score can recompute the decision instead of guessing it.

#### Scenario: The rule declares its effect on the candidate set
- **WHEN** the abstention rule is adopted
- **THEN** the report states whether it alters the candidate set or only the decision to serve it
- **AND** it states which distance profile the decision reads

#### Scenario: A candidate-set-altering rule invalidates persisted windows
- **GIVEN** an abstention rule that changes the retrieval statement's distance bound
- **WHEN** candidate windows captured before that change are re-scored
- **THEN** the run is refused
- **AND** the mismatch is reported

#### Scenario: The profile the decision read is recoverable
- **GIVEN** a persisted run whose abstention decision read a profile other than the served candidates
- **WHEN** the run is re-scored
- **THEN** the decision is recomputed from the persisted profile
- **AND** the re-score is not refused

### Requirement: The abstention decision is observable
The stage that decides abstention MUST log, with the request trace identifier, the rule in force, the best distance observed for the query, and the decision taken. It MUST NOT log any embedding vector.

#### Scenario: The abstention decision is logged with its inputs
- **WHEN** the abstention stage runs
- **THEN** it logs the rule in force, the best observed distance and the decision
- **AND** the entry carries the request trace identifier

#### Scenario: No vector reaches the logs
- **WHEN** the abstention stage logs
- **THEN** no embedding vector appears in the entry

### Requirement: The abstention decision reaches the sale-assistance path and is declared there
The abstention decision SHALL govern the sale-assistance path and not only the product retrieval response. When the rule decides that the catalogue has no answer for a query, the assistance response MUST return no group and MUST declare the abstention in a field dedicated to it.

The assistance response MUST NOT express this decision by reusing the cross-branch confidence signal. That signal carries a different, measured meaning — the absence of agreement between branches — and on the judged set it fires on answerable queries far more often than on out-of-domain ones, so reusing it would report the opposite of what a reader would conclude.

This requirement does not alter what the product retrieval response reports; it adds the obligation that the decision travels to the consumer that generates.

#### Scenario: An abstained query yields no group on the assistance path
- **GIVEN** a query for which the rule decides the catalogue has no answer
- **WHEN** the sale assistance is requested with it
- **THEN** no group is returned
- **AND** the dedicated abstention field is set

#### Scenario: The cross-branch signal is not repurposed
- **WHEN** the sale assistance declares an abstention
- **THEN** it does so in its own field
- **AND** it does not rely on the cross-branch confidence signal to convey it

#### Scenario: An answerable query is not silenced on the assistance path
- **GIVEN** a query the catalogue can answer
- **WHEN** the sale assistance is requested with it
- **THEN** the dedicated abstention field is clear
- **AND** at least one group is returned

### Requirement: The effective abstention configuration travels as a parameter on every consuming path
Every path that consumes the abstention rule SHALL receive the effective configuration as a parameter of the call. Configuration MUST supply the default only, and no consuming module may read the value from the environment internally, so an evaluation can compare configurations in a single process without restarting anything.

#### Scenario: A consuming path can be driven with a configuration of its own
- **GIVEN** two calls made in the same process with different abstention configurations
- **WHEN** both are served
- **THEN** each honours the configuration it was given
- **AND** neither reads the value from the environment

#### Scenario: Absent parameters fall back to the configured default
- **WHEN** a consuming path is called without an explicit abstention configuration
- **THEN** the configured default is applied

### Requirement: A piece that cannot be used is not reported as an abstention
When a request anchors a concrete product and the index cannot serve it — the product is unknown, inactive, or held without an embedding — the response MUST be an error that distinguishes those cases and MUST NOT be a success carrying the abstention field. An abstention is a statement about what the catalogue can answer, and using it for an unusable anchor would assert something the system has not established.

#### Scenario: An unusable anchor is an error and not an abstention
- **GIVEN** a request anchored to a product the index cannot serve
- **WHEN** it is served
- **THEN** the response is an error naming which of the unusable cases occurred
- **AND** it is not a success with the abstention field set

### Requirement: Abstention tests run offline
Tests for this capability MUST run without calling an embedding provider, a language model provider or a remote database. The rule's behaviour MUST be exercised against fixtures, including the case of an answerable query that must not be abstained on.

#### Scenario: The offline suite makes no external call
- **GIVEN** the abstention test suite
- **WHEN** it runs without credentials configured
- **THEN** it passes
- **AND** no provider call and no network call is made

#### Scenario: An answerable query is not abstained on
- **GIVEN** a fixture query whose labelled relevant set is non-empty
- **WHEN** the abstention rule is applied
- **THEN** candidates are returned
- **AND** the response is not an abstention

### Requirement: The abstention decision reads a distance profile that no selected filter has narrowed

The abstention decision SHALL be taken over the distance profile the query produces with no catalog-side filter applied, because the decision is about the query and a filter is a restriction rather than a description, and a decision taken over a filtered profile cannot fire at all when the filter is narrow: the rule needs a number of candidates inside its band that a narrow filter can never supply, so the system would serve a handful of mediocre pieces and, where a generation layer exists, write prose praising them.

The parameters of the rule were calibrated over unfiltered queries, so reading an unfiltered profile restores the regime they were fitted in rather than inventing a new one.

The unfiltered profile MUST be obtained without a second call to the embedding provider, reusing the vector already computed for the request, and MUST NOT be obtained when the request carries no filter, since in that case the served profile already is the unfiltered one.

Obtaining it MUST NOT change which candidates are served, their order or the window returned: the filters keep excluding inside the retrieval statement exactly as before.

An accepted consequence MUST be declared: a query whose description finds nothing can now abstain even when a filter would have rescued a few pieces, because the abstention judges whether the description found anything.

#### Scenario: A narrow filter no longer prevents abstention
- **GIVEN** a query whose unfiltered distance profile is flat and a filter that admits fewer candidates than the rule's minimum
- **WHEN** the retrieval runs
- **THEN** the response abstains

#### Scenario: An unfiltered request costs one statement
- **WHEN** a request carries no catalog-side filter
- **THEN** no additional retrieval statement is issued
- **AND** the decision is taken over the profile of the served candidates

#### Scenario: The unfiltered profile costs no provider call
- **WHEN** a filtered request is served
- **THEN** the number of embedding provider calls is the same as for an unfiltered request

#### Scenario: The served candidates are unchanged
- **GIVEN** a filtered request that does not abstain
- **WHEN** the response is served
- **THEN** the candidates, their order and the window are the ones the filtered retrieval produced

### Requirement: A narrow filter is declared as such and is not confused with an unanswerable query

When the unfiltered distance profile does not warrant an abstention and the filtered candidate set is smaller than the rule's minimum, the response SHALL declare that the selected filters admitted few candidates, using a code of the closed warning vocabulary, and MUST NOT abstain.

The two statements MUST stay distinguishable, because they call for different actions from the operator: one says the description found nothing, the other says the description found something the filter excluded, and asserting the second when the first is true would claim a fit that does not exist.

The declaration MUST be available on every consuming path that accepts catalog-side filters, not only on the generative one.

#### Scenario: A narrow filter over an answerable query is declared
- **GIVEN** a query whose unfiltered profile has a clear best hit and a filter that admits few candidates
- **WHEN** the retrieval runs
- **THEN** the response does not abstain
- **AND** it carries the code declaring the filters admitted few candidates

#### Scenario: An unanswerable query abstains rather than blaming the filter
- **GIVEN** a query whose unfiltered profile is flat and a narrow filter
- **WHEN** the retrieval runs
- **THEN** the response abstains
- **AND** it does not carry the code declaring the filters admitted few candidates
