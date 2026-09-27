# retrieval-evaluation Specification

## Purpose
How retrieval quality is measured in this service, and what makes one measurement comparable to another. The yardstick is a golden set versioned in the repository under `ai-service/evals/golden/` — the queries, the graded judgements, the frozen query vectors and the written annotation criterion that predates the first judgement — and never a database table, so moving the yardstick costs a code review and every figure taken before a move stays interpretable against the version it used. Its composition is not a documented intention but an executable validation that fails the load: queries whose best document shares no term with them after synonym expansion, queries that resolve only to fields of low corpus coverage, stone-value queries the piece type does not discriminate, the three classes of synonym dictionary entry, out-of-domain queries plausible within the jewellery domain rather than nonsense every configuration abstains on, literal code and product-name queries, and anchoring to real products evaluated per category so that no category is composed entirely of synthetic ones. Queries that were used to fix the fusion weights, the branch depth or the coordination rule carry a mark, and every metric is published three times — whole set, tuning subset, new queries — because a result visible only on the first is not a confirmation but a candidate for overfitting.

Judgements are graded on three levels and published on both scales under one declared binarisation rule, with a divergence between the readings reported as a finding rather than resolved by picking one; a third, operational reading joins them whenever a configuration under evaluation reorders by a business signal, its gain function of labelled grade and availability declared before the measurement and never modifying what was recorded. They are keyed by the pair of query and document, so a later configuration appends to them instead of re-recording what exists, and each carries the content hash of the text it was made against, so labels resting on since-changed documents are counted beside the metrics and not in a separate log. The judged pool is the union of what the indexed configurations return, deepened in blocks while the previous block still contributed a relevant document and stopped at the branch depth beyond which the live retriever cannot surface anything; the depth reached is recorded per query, everything outside the pool is declared irrelevant by assumption, and the unjudged share of a configuration's top results marks that row not comparable instead of scoring it silently. Retrieval always executes over the complete indexed catalogue — restricting the corpus by data origin is not an available configuration — while the breakdown by origin counts only the relevant documents of each, and the report records how often an irrelevant synthetic product outranks the first relevant real one, so that interference is measured rather than assumed.

The comparison is against baselines that replicate what they claim to replicate: the substring-over-name plus exact-code product search that preceded this project's AI work, the degraded Spanish full-text searcher composed over the same text the .NET side indexes rather than over the richer canonical document — an equivalence an automated test breaks when the renderer drifts — and a context-only configuration that places the whole catalogue in the model context without retrieval, priced per query, carrying no product price, truncating deterministically with the omitted count recorded, and projected to the catalogue size at which it no longer fits. Every run records its provenance — golden set version, configuration, index fingerprint, embedding model version, code revision and how its ranked lists were composed, that last value read from the code rather than from any setting because it is recorded even where no configuration can select it — and two runs whose provenance differs are reported as not comparable rather than compared; query embeddings are frozen per embedding model version so that repeating a run does not depend on a provider answering identically. Latency is two figures, retrieval and end-to-end, measured warm with the first execution discarded, and cost comes from a versioned price list, recorded as zero rather than absent for a configuration that calls no paid provider and declared unverified when the source cannot be reached. Abstention is measured over the out-of-domain category with both the per-document distance distribution and the per-query best-hit distribution published, and the live distance threshold and the abstention rule may be re-fixed under a rule recorded before the measurement, justified from the per-query distribution rather than the per-document one and reported with both sides of the trade: the rate gained over out-of-domain queries and the answerable queries the rule silenced. A configured default moves only under a rule written before the measurement, in the reading that decides — the queries no calibration has seen, because the tuning subset is saturated and contaminated and is published as a diagnostic that cannot veto a change — and the outcome is documented whether or not anything moves. An evaluation reporting more than one change publishes a row isolating each of them beside the combined one and keeps the previous baseline citable, its figures, provenance and measured configuration archived as versioned artefacts and the row marked historical and not re-executable once that configuration leaves the code, neither loadable as a configuration nor restated inside the harness; deepening the golden set re-runs every row so the table carries one provenance tuple and re-confirms the decision against the incumbent; and an absolute acceptance criterion the evidence cannot reach is restated as a relative one with the gap declared, never met by relabelling or by weakening the criterion after the fact. The normative output is the versioned report and the per-query detail under `ai-service/evals/results/`, written on every run; persistence to the evaluation tables is optional and the component that produces the results does not depend on the one that stores them. The harness tests run offline against fixtures, with no provider and no production database.
## Requirements
### Requirement: The golden set is a versioned repository artefact with a written annotation criterion
The golden set, its judgements, its frozen query vectors and its annotation criterion MUST live as files under `ai-service/evals/golden/` and be versioned in the repository. They MUST NOT be stored only in the database: changing the yardstick MUST require a code review, and every measurement taken before a change MUST remain interpretable against the version it used.

The annotation criterion MUST be written before any judgement is recorded, and MUST define each grade by a condition that can be checked against the query and the document, not by a subjective impression. The set MUST carry a version identifier that every evaluation run records.

#### Scenario: The criterion exists before the first judgement
- **WHEN** the golden set is loaded
- **THEN** an annotation criterion document exists alongside it
- **AND** the criterion defines the intermediate grade as a failure of one attribute the query named explicitly
- **AND** no judgement predates the criterion

#### Scenario: The golden set is not read from the database
- **WHEN** the harness loads the golden set
- **THEN** it reads the repository files
- **AND** it does not require a database connection to do so

### Requirement: The golden set composition is validated by code and its violation fails the load
Loading the golden set MUST fail when the set does not satisfy the composition that makes it able to arbitrate the disputes it exists for. The validation MUST be executable and MUST NOT be a documented intention.

The set MUST contain at least: twelve queries with at least one maximum-grade document whose canonical text contains **no term of the query after synonym expansion**; five queries that resolve only to fields of low corpus coverage; four queries that name a stone value where the piece type does not discriminate; six synonym queries covering the three classes of dictionary entry — stemmer artefact, commercial synonym and directional bridge; five out-of-domain queries that are plausible within the jewellery domain and have no relevant document; and four queries that are a literal code or product name.

Anchoring to real products MUST be evaluated per category, so that no category is composed entirely of synthetic products.

#### Scenario: A set without unanchored queries is rejected
- **WHEN** the golden set contains fewer than twelve queries whose best document shares no term with the query after expansion
- **THEN** the load fails and names the unmet requirement
- **AND** no evaluation runs

#### Scenario: Nonsense text does not satisfy the out-of-domain category
- **WHEN** an out-of-domain query is not plausible within the jewellery domain
- **THEN** the load fails
- **AND** the message states that every configuration abstains on nonsense, so the metric would not discriminate

#### Scenario: A wholly synthetic category is rejected
- **WHEN** every relevant document of a category belongs to synthetic products
- **THEN** the load fails
- **AND** the message states that the category cannot be compared across data origins

### Requirement: Relevance is graded, and both the graded and the binary readings are published
Each judgement MUST take one of three grades. The report MUST publish every ranking metric twice: once using the grades and once using the binary reading derived from them, where a document is relevant when its grade is at least the intermediate one. The binarisation rule MUST be fixed and declared, never chosen per configuration.

**A third, operational reading MUST be published whenever a configuration under evaluation reorders candidates by a business signal.** Its gain function MUST be a declared function of the labelled grade and the availability signal, MUST be declared before the measurement is executed, and MUST NOT modify the recorded judgements. It MUST be justified from the annotation criterion's own scale rather than from a new constant, because the criterion judges what a piece **is** and never what the shop **has**, so a metric computed over labelled relevance alone is at best orthogonal to availability.

When the readings order the configurations differently, the report MUST state it as a finding.

#### Scenario: Both readings appear in the report
- **WHEN** an evaluation run completes
- **THEN** the report contains the graded metrics and the binary metrics for every configuration
- **AND** the binarisation rule is stated once and applies to all of them

#### Scenario: The operational reading appears when business signals are evaluated
- **WHEN** an evaluation run includes a configuration that reorders by a business signal
- **THEN** the report contains the operational metric alongside the graded and binary ones
- **AND** the gain function is stated once and applies to every configuration

#### Scenario: The operational reading does not alter the judgements
- **GIVEN** a judged document whose availability signal lowers its effective gain
- **WHEN** the operational metric is computed
- **THEN** the judgement file is unchanged
- **AND** the labelled grade is still the one that was recorded

#### Scenario: Divergence between readings is surfaced
- **WHEN** two readings rank two configurations in opposite order
- **THEN** the report states that the comparison is not robust to the choice of scale

### Requirement: Queries used to calibrate the retriever are marked and reported separately
Queries that were used to fix the fusion weights, the branch depth or the coordination rule MUST be marked in the golden set. Every metric MUST be reported three times: over the whole set, over the marked subset only, and over the unmarked subset only.

**The reading that decides is the unmarked subset.** The marked subset MUST be reported as a diagnostic of contamination and MUST NOT veto a decision. The reason is a property of that subset and not of any result taken over it: it is the set of queries selected to calibrate one branch, so using it to arbitrate that branch's weight is validating a model on its training set; and its metrics are saturated, so it cannot register an improvement at all. Whenever the marked subset disagrees with the unmarked one, the report MUST state the disagreement and MUST state which queries are saturated.

The marked subset MUST be reported with the count of its queries that sit at the ceiling of the deciding metric, so a reader can see whether it had room to move.

#### Scenario: The three readings are published
- **WHEN** an evaluation run completes
- **THEN** each metric appears for the whole set, for the tuning subset and for the new queries
- **AND** queries carry the mark that assigns them to a subset

#### Scenario: The unmarked subset decides
- **GIVEN** a configuration that improves on the new queries and does not improve on the tuning subset
- **WHEN** the decision rule is applied
- **THEN** the decision is taken on the new queries
- **AND** the report states the disagreement and names it as contamination of the tuning subset

#### Scenario: Saturation is reported
- **WHEN** the tuning subset is reported
- **THEN** the report states how many of its queries sit at the ceiling of the deciding metric
- **AND** a reader can tell whether that subset had room to improve

#### Scenario: A result that holds on neither subset is not a confirmation
- **WHEN** a configuration fails to improve on the new queries
- **THEN** the report states that the decision is not confirmed
- **AND** the configuration is not adopted

### Requirement: Pooling deepens where relevant documents keep appearing and declares how far it judged
The set of documents to judge MUST be the union, without repetition, of what each indexed configuration returns. Documents outside that union MUST be treated as irrelevant, and that assumption MUST be declared in the report.

Pooling MUST start at a common base depth, MUST continue in blocks while the previous block contributed at least one relevant document, and MUST stop at the branch depth beyond which the live retriever cannot surface a document. The depth reached MUST be recorded per query.

#### Scenario: A query with few relevant documents stops early
- **WHEN** a block of pooled documents contributes no relevant document
- **THEN** pooling stops for that query
- **AND** the depth reached is recorded

#### Scenario: Pooling never exceeds what the retriever can show
- **WHEN** pooling would continue past the configured branch depth
- **THEN** it stops at that depth
- **AND** the report states that documents beyond it cannot be surfaced by the live pipeline

### Requirement: Judgements are appendable and unjudged results are reported
Judgements MUST be identified by the pair of query and document, so that a later change can add judgements without re-recording the existing ones. Every configuration MUST report the proportion of its top results that carry no judgement, and a configuration whose proportion is high MUST be marked as not comparable in the report.

#### Scenario: A later configuration adds judgements without invalidating the previous ones
- **WHEN** judgements are added for documents that were not previously pooled
- **THEN** the existing judgements are unchanged
- **AND** the golden set version reflects the addition

#### Scenario: A configuration promoting unjudged documents is not silently penalised
- **WHEN** a configuration returns results a large share of which carry no judgement
- **THEN** the report states the share
- **AND** marks that row as not comparable rather than presenting its score as final

### Requirement: Metrics are reported by data origin and retrieval always runs over the whole corpus
Retrieval MUST execute over the complete indexed catalogue regardless of the breakdown. Queries MUST be grouped by the origin of their relevant documents, and each group's metrics MUST count only the relevant documents of that origin. Restricting the retrieval corpus to a single origin MUST NOT be an available configuration.

The report MUST additionally record how often an irrelevant synthetic product outranks the first relevant real document, so that "the synthetic corpus is easier" can be distinguished from "the synthetic corpus interferes".

#### Scenario: The real portion is not measured over a smaller corpus
- **WHEN** metrics are computed for the real portion
- **THEN** the retrieval that produced them ran over the whole indexed catalogue
- **AND** no configuration exists that restricts the corpus by data origin

#### Scenario: Synthetic interference is measured, not assumed
- **WHEN** a query whose relevant documents are real is evaluated
- **THEN** the report records whether an irrelevant synthetic product preceded the first relevant real document

### Requirement: Baseline configurations replicate the semantics they claim to replicate
The evaluation MUST include a baseline that reproduces the product search that existed before this project's AI work — substring match over the product name plus exact code match — and a separate baseline that reproduces the degraded Spanish full-text searcher. The two MUST carry names that do not confuse one with the other.

The full-text baseline MUST be composed over the same text the .NET searcher indexes, and MUST NOT be composed over the canonical document, which carries additional extracted fields and would make the baseline stronger than the thing it replicates. An automated test MUST fail if the canonical document renderer changes in a way that breaks that equivalence.

Neither baseline calls an external provider, and both MUST record a cost of zero rather than an absent value.

#### Scenario: The legacy baseline answers a natural-language query the way the old searcher did
- **WHEN** the legacy baseline is evaluated on a multi-word natural-language query
- **THEN** it returns only products whose name contains the query as a substring
- **AND** its behaviour matches the pre-existing product search semantics

#### Scenario: The full-text baseline does not see the extracted fields
- **WHEN** the full-text baseline is composed
- **THEN** the text it searches consists of the product name, the code and the description line
- **AND** it does not include the extracted type, materials, colours, style or occasion lines

#### Scenario: A renderer change breaks the fidelity test, not the fidelity
- **WHEN** the canonical document renderer stops emitting the description line with its expected prefix
- **THEN** the fidelity test fails

### Requirement: The context-only baseline measures why retrieval exists, and declares what it did not see
The evaluation MUST include a configuration that places the whole catalogue in the model context without retrieval. It MUST record the size in tokens of that context, the cost per query, and the projection of that size for larger catalogues up to the point where it no longer fits.

The context MUST NOT contain product prices, because the authority over price is not this service. When the catalogue exceeds the configured context budget, the configuration MUST truncate deterministically and MUST record how many documents were omitted, rather than failing or truncating silently.

Its measurement MUST be recorded with the model and the date that produced it, and MUST NOT be presented as reproducible.

#### Scenario: A catalogue larger than the budget is truncated deterministically
- **WHEN** the compacted catalogue exceeds the context budget
- **THEN** the omitted documents are the same on every run
- **AND** the run records how many were omitted
- **AND** the reported recall is accompanied by that count

#### Scenario: The context carries no price
- **WHEN** the context-only configuration builds its prompt
- **THEN** no product price appears in it

#### Scenario: The scale projection is part of the result
- **WHEN** the context-only configuration is measured
- **THEN** the report states the token size for the current catalogue and for larger ones
- **AND** identifies the size at which the catalogue no longer fits

### Requirement: A run is comparable to another only when its provenance matches
Every evaluation run MUST record the golden set version, the configuration, a stable fingerprint of the indexed document set, the embedding model version, the code revision that produced it **and how its ranked lists were composed**. Two runs whose provenance differs MUST be reported as not comparable rather than compared.

**The composition MUST be recorded even when it can no longer be chosen.** Recording it and selecting it are different things: once a single composition remains, no configuration may select one, but a run archived under a retired composition MUST still be distinguishable from a current one, and a run MUST still declare what it actually composed rather than what its environment was thought to request. The recorded value MUST therefore come from the code and never from a setting, and a configuration that composes no ranked lists at all MUST record that absence rather than inherit the live value.

Query embeddings MUST be frozen as a versioned artefact keyed by the embedding model version, so that repeating a run does not depend on the provider answering identically.

#### Scenario: Repeating a run yields identical metrics
- **WHEN** the same configuration runs twice with the same provenance
- **THEN** the metrics are identical

#### Scenario: A moved index makes previous runs incomparable
- **WHEN** the indexed document set changes and a run is compared with an earlier one
- **THEN** the report states that the two are not comparable and names the differing element

#### Scenario: The composition is recorded although no configuration selects it
- **WHEN** an evaluation run is recorded
- **THEN** its provenance names how its ranked lists were composed
- **AND** that value comes from the code rather than from any setting
- **AND** a run whose configuration composes no ranked lists records that absence instead of the live value

#### Scenario: A run archived under a retired composition is not comparable with a current one
- **GIVEN** an archived run recorded under a composition that has since been retired
- **WHEN** it is compared with a run taken after the retirement
- **THEN** the two are reported as not comparable
- **AND** the composition is named as the differing element

### Requirement: Deepening the golden set re-runs every row and re-confirms the decision
When an evaluation appends judgements or adds queries, the golden set version changes and every previously published figure stops being comparable. Every row of the table MUST therefore be re-run under the new version, so that the published table carries **one** provenance tuple.

A decision taken against the previous version MUST be **re-confirmed** against the new one before it is fixed. Re-confirmation MUST compare the winning configuration against the incumbent; it MUST NOT require re-running the whole calibration grid.

A configuration whose results were substantially unjudged MUST be marked not comparable rather than presented alongside the others.

#### Scenario: Every row shares one provenance
- **GIVEN** judgements were appended and queries were added
- **WHEN** the table is published
- **THEN** every row reports the same golden set version and the same provenance tuple
- **AND** figures from the previous version are cited as historical rather than as comparable rows

#### Scenario: The winner is re-confirmed on the new version
- **GIVEN** a configuration chosen by a sweep run against the previous version
- **WHEN** the golden set version changes
- **THEN** that configuration is compared against the incumbent under the new version before the default is fixed
- **AND** the full grid is not re-run

#### Scenario: An unjudged row is marked not comparable
- **GIVEN** a configuration promoting documents that carry no judgement
- **WHEN** the table is published
- **THEN** its unjudged proportion is reported
- **AND** the row is marked not comparable when that proportion exceeds the declared threshold

### Requirement: The abstention behaviour may be re-fixed under a rule written before the measurement, justified from the per-query distribution
The evaluation MUST measure abstention over the out-of-domain category and MUST publish the distribution of retrieval distances separating relevant from irrelevant documents.

The live distance threshold and the abstention rule MAY be changed by an evaluation, under a rule recorded **before** the measurement is executed.

A change to the abstention behaviour MUST be justified from the distribution of the **best distance per query**, separating answerable queries from out-of-domain ones, and MUST NOT be justified from the per-document distribution alone, because the two answer different questions: a total overlap between the distances of relevant and irrelevant documents does not imply that the best hit of an answerable query cannot be separated from the best hit of an out-of-domain one. The report MUST publish both distributions, MUST state whether a single value separates the per-query populations, and MUST state whether the adopted rule alters the candidate set or only the decision to serve it.

The report MUST publish, for every candidate rule, the abstention rate over out-of-domain queries **and** the number of answerable queries the rule turned into abstentions.

#### Scenario: The distribution is published per grade
- **WHEN** an evaluation run completes
- **THEN** the report contains the distance distribution of relevant documents and of irrelevant ones
- **AND** states whether the two are separable by a single value

#### Scenario: The per-query distribution is published and decides
- **WHEN** an abstention rule is adopted
- **THEN** the report contains the best-distance distribution of answerable queries and of out-of-domain ones
- **AND** the justification rests on that distribution rather than on the per-document one

#### Scenario: A threshold change cites a rule written beforehand
- **WHEN** the live distance threshold or the abstention rule is changed
- **THEN** the report cites a rule recorded before the measurement was executed
- **AND** states whether the change alters the candidate set

#### Scenario: Both sides of the abstention trade are published
- **WHEN** a candidate abstention rule is reported
- **THEN** its abstention rate over out-of-domain queries appears
- **AND** the number of answerable queries it turned into abstentions appears

### Requirement: Judgements record the document text they were made against
Every judgement MUST record the content hash the document carried when it was judged. Each run MUST report how many judgements rest on a document whose text has since changed, and that figure MUST appear alongside the metrics rather than in a separate log.

#### Scenario: A re-enriched product is detected after labelling
- **WHEN** a judged document's canonical text changes after the judgement was recorded
- **THEN** the run reports that judgement as resting on stale text
- **AND** the count appears next to the metrics

### Requirement: The report is always written to the repository and database persistence is optional
Every run MUST produce a versioned report and a per-query detail file under `ai-service/evals/results/`. Writing to the evaluation tables MUST happen only when explicitly requested, and the component that produces the results MUST NOT depend on the component that persists them.

The harness MUST produce its report even when nothing is written to the database.

#### Scenario: A run without persistence still produces its report
- **WHEN** the harness runs without requesting persistence
- **THEN** the report and the per-query detail are written to the repository
- **AND** no evaluation table is written

#### Scenario: Baseline runs are persisted like any other
- **WHEN** persistence is requested
- **THEN** the runs of the zero-cost baselines are persisted as well
- **AND** the ablation table is complete rather than missing its reference rows

### Requirement: Latency is reported as two figures, measured warm and repeated
Each configuration MUST report the retrieval latency excluding the embedding provider round trip and the end-to-end latency including it. The acceptance criterion for latency applies to the first. The report MUST publish the second alongside the agreed budget.

Measurement MUST discard the first execution of each query and MUST repeat the remaining ones, so that the reported percentiles do not describe a cold start.

#### Scenario: Both latency figures appear per configuration
- **WHEN** an evaluation run completes
- **THEN** each configuration reports retrieval latency and end-to-end latency
- **AND** the acceptance criterion is applied to the retrieval figure

#### Scenario: The cold execution is excluded
- **WHEN** latency is measured for a query
- **THEN** the first execution is discarded
- **AND** the reported percentiles derive from the repeated warm executions

### Requirement: Cost per query is recorded for every configuration from a versioned price list
Provider prices MUST live in a versioned file carrying the date and the source they were taken from. Every configuration MUST record a cost per query, and a configuration that calls no paid provider MUST record zero rather than an absent value.

When the price source cannot be verified at measurement time, the file MUST record that the date is unknown and the report MUST declare the cost as unverified rather than carrying figures taken from memory.

#### Scenario: A configuration without provider calls records zero
- **WHEN** a lexical baseline is evaluated
- **THEN** its recorded cost per query is zero

#### Scenario: Unverifiable prices are declared, not invented
- **WHEN** the price source cannot be reached while measuring
- **THEN** the price file records an unknown date
- **AND** the report declares the cost figures unverified

### Requirement: An ablation table isolates each change it reports
When one evaluation reports more than one change to the retrieval pipeline, the table MUST contain a row for each change applied **on its own**, in addition to the row that applies them together. A table that reports only the combined result MUST NOT be published, because an improvement it shows cannot be attributed to a cause.

**The baseline row MUST remain citable, and citable is not the same as re-executable.** When the configuration a published baseline was measured under is retired from the code, the evaluation MUST preserve that row's figures, its full provenance tuple **and the configuration it was measured under** as versioned artefacts in the repository, and MUST mark the row as **historical and not re-executable** wherever it is cited. The report MUST state which rows can be re-run and which cannot.

The retired configuration MUST NOT remain loadable as a configuration: it is preserved as a record of what was measured, not as something that can be selected, and an attempt to load it MUST fail naming what no longer exists.

A retired baseline configuration MUST NOT be reimplemented inside the evaluation harness in order to keep it runnable: a harness that restates the pipeline measures the restatement, not the pipeline.

#### Scenario: Each change has its own row
- **GIVEN** an evaluation that reports both a fusion change and a ranking change
- **WHEN** the ablation table is published
- **THEN** it contains a row with the fusion change alone
- **AND** a row with both changes applied
- **AND** the improvement of each is attributable

#### Scenario: A retired baseline row stays citable
- **GIVEN** the configuration a published baseline was measured under has been retired from the code
- **WHEN** that baseline is cited
- **THEN** its figures, its full provenance tuple and the configuration it was measured under are present as versioned artefacts
- **AND** the row is marked historical and not re-executable

#### Scenario: The preserved configuration is a record and not a choice
- **GIVEN** the preserved configuration of a retired baseline
- **WHEN** it is loaded as a configuration
- **THEN** the load fails naming the knobs that no longer exist
- **AND** it is not listed among the configurations the table can run

#### Scenario: The report says which rows can be re-run
- **WHEN** an ablation table containing a retired row is published
- **THEN** it states for each row whether it can be re-executed
- **AND** a reader can tell which figures are reproducible and which are archived

#### Scenario: A retired configuration is not reimplemented in the harness
- **WHEN** the evaluation harness is inspected after a baseline configuration is retired
- **THEN** the harness contains no restatement of that pipeline
- **AND** the row's figures come from the archived artefact rather than from a copy of the code

### Requirement: A configured default changes only when the verdict is material
A default retrieval setting MUST NOT be changed on the basis of this evaluation unless the improvement exceeds the agreed margin **in the reading that decides**, and degrades no measured category beyond the agreed margin. The rule MUST be recorded before the measurement is executed, together with which reading decides and why.

The reading that decides MUST be the subset of queries that no calibration has seen. A saturated or contaminated reading MUST NOT block a change; it MUST be reported alongside, so that a reader can weigh it.

The outcome MUST be documented whether or not any default moves.

#### Scenario: A small improvement does not move a default
- **WHEN** a configuration improves the deciding metric by less than the agreed margin
- **THEN** the default is unchanged
- **AND** the report records the measured difference and the decision not to act on it

#### Scenario: A change of default is justified against the written rule
- **WHEN** a default is changed
- **THEN** the report shows every reading and the per-category effect
- **AND** cites the rule that was written before the measurement, including which reading decides

#### Scenario: A degraded category blocks a change
- **WHEN** a configuration improves the deciding metric beyond the margin
- **AND** degrades a measured category beyond the margin
- **THEN** the default is unchanged
- **AND** the report names the category that paid

#### Scenario: A contaminated reading does not block a change
- **GIVEN** a configuration that improves the deciding reading beyond the margin
- **AND** does not improve a reading reported as contaminated or saturated
- **WHEN** the rule is applied
- **THEN** the change is not blocked by that reading
- **AND** the report publishes it alongside the decision

### Requirement: An acceptance criterion the evidence cannot reach is restated as a relative one and its gap declared
When a measured baseline shows that an absolute acceptance threshold is beyond the reach of the changes under evaluation, the evaluation MUST NOT be reported as a failure of those changes and MUST NOT relabel data until the figure is met. The criterion MUST be restated as a **relative** one — each configuration beats the one it is built on, in the reading that decides and beyond the agreed margin — and the distance to the absolute threshold MUST be declared as a limitation.

The restatement MUST record the measured figures that justify it.

**A configuration that fails the relative criterion MAY still be adopted, and when it is, that gap MUST be declared with the same prominence as the absolute one.** Adoption in that case MUST rest on a rule of its own that the configuration does satisfy, and the report MUST state which rule admitted it, why the deciding metric cannot resolve the difference, and what evidence outside that metric supports the decision. A gap that is adopted MUST NOT be reported as a pass, and a criterion MUST NOT be weakened after the measurement so that a configuration meets it.

#### Scenario: The relative criterion is applied and the gap declared
- **GIVEN** a configuration that beats the one it is built on beyond the margin in the deciding reading
- **AND** does not reach the absolute threshold the design states
- **WHEN** the evaluation is reported
- **THEN** the configuration is accepted under the relative criterion
- **AND** the distance to the absolute threshold is declared as a limitation with its measured figures

#### Scenario: A configuration adopted without meeting the relative criterion declares that gap
- **GIVEN** a configuration that does not beat the one it is built on beyond the margin in any reading
- **AND** that satisfies the adoption rule its own capability defines
- **WHEN** it is adopted
- **THEN** the report declares that the relative criterion was not met, with its measured figures
- **AND** names the rule that admitted it and the evidence outside the deciding metric
- **AND** the outcome is not reported as having met the criterion

#### Scenario: A criterion is not weakened to fit a result
- **WHEN** a configuration fails an acceptance criterion
- **THEN** the criterion recorded before the measurement is unchanged
- **AND** the failure is declared rather than absorbed

#### Scenario: Judgements are not relabelled to meet a threshold
- **WHEN** an absolute threshold is not met
- **THEN** the recorded judgements are unchanged
- **AND** the annotation criterion is unchanged

### Requirement: Evaluation tests run offline
The test suite of the evaluation harness MUST run without calling embedding providers, language model providers or a production database. Metric computation, golden set validation, pooling and report generation MUST be exercised against fixtures.

#### Scenario: The suite passes with no provider reachable
- **WHEN** the evaluation tests run with no provider credentials available
- **THEN** they pass
- **AND** no outbound provider call is made

#### Scenario: A ranking metric is verified against a hand-computed value
- **WHEN** the ranking metric is computed over a fixed fixture
- **THEN** it equals the value computed by hand for that fixture

### Requirement: Task success over the agent's calibration scenarios is a defined verdict, recomputed without a provider and published with its failures named

Task success over the agent's calibration scenarios SHALL be a verdict defined before it is published — a scenario succeeds when the tool expectation written for it is met, meaning every tool it requires was invoked, at least one of any it admits was invoked and none it forbids was, and the scenario does not itself declare a discrepancy — and that verdict MUST be recomputable from a committed run artefact with no provider call and no database, so that any reader reproduces it from the repository alone.

The published form MUST be a count over the scenario set with the failing scenarios named individually, and MUST NOT be a success rate expressed as a percentage. The reason is measured and not stylistic: scoring two runs of the same scenario set against each other puts the between-run noise at 2 of 20, so a single rate would claim a precision the evidence does not have, while the count with its names carries strictly more information.

Fields the run records but for which no per-scenario expectation was written — the terminal stop reason, the iteration and tool-call counters, the number of groups, whether an argument was generated — MUST be published beside the verdict as context and MUST NOT enter it, because admitting them after the figures are in hand would be defining the criterion from the data.

A scenario whose transcript changed after the run MUST be reported as not comparable rather than scored against the definition as it stands today, and the count of such scenarios MUST be published with the verdict.

#### Scenario: The verdict is recomputed from a committed artefact

- **WHEN** the task-success verdict is published
- **THEN** it is recomputed from a run artefact committed to the repository
- **AND** the recomputation calls no model provider and reads no database
- **AND** the artefact is identified by name and by a digest of its bytes

#### Scenario: The verdict is published as a count with its failures named

- **WHEN** the verdict over the calibration set is published
- **THEN** it is stated as a count over the set with every failing scenario named
- **AND** no success rate expressed as a percentage is published in its place
- **AND** the measured between-run noise is stated beside the count

#### Scenario: A scenario declaring its own discrepancy is counted apart

- **GIVEN** a calibration scenario that declares a discrepancy of its own
- **WHEN** the verdict is computed
- **THEN** that scenario is counted apart from both the successes and the unexplained failures

#### Scenario: A scenario that changed after the run is not scored

- **GIVEN** a calibration scenario whose transcript differs from the one the run executed
- **WHEN** the verdict is recomputed against the scenario set as it stands today
- **THEN** that scenario is reported as not comparable
- **AND** the number of scenarios in that state is published with the verdict

#### Scenario: Terminal state is context and not part of the verdict

- **GIVEN** a scenario whose tool expectation is met and whose loop stopped on a budget
- **WHEN** the verdict is computed
- **THEN** the scenario counts as a success
- **AND** its stop reason and counters are published beside the verdict rather than inside it

