## MODIFIED Requirements

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

## ADDED Requirements

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
