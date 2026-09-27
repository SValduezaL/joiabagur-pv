# jbg-ai test layout

The test tree **mirrors the `src/jbg_ai/` package**. One rule decides where a test
goes: *which module owns the behaviour under test?* That answer never changes when
a change is archived, so the layout survives C01 → C40 without renaming anything.

Tests are deliberately **not** organised by OpenSpec change. A change is a unit of
work, not a unit of behaviour: `test_openapi_snapshot_is_stable` was written in C02
but guards every change after it, and C22 edits code first shipped by C14. Change
traceability lives in the module docstring (`Delivered by C02.`), where it costs
nothing and cannot rot into a wrong folder name.

## Layout

```text
tests/
├── README.md
├── conftest.py       # global fixtures only — never import from it (see Support)
├── support/          # importable helpers and injectable fakes
├── fixtures/         # test data: payloads, golden set, corpus samples
├── api/              # HTTP surface: routing, auth, contracts, stubs, OpenAPI snapshot
├── config/           # settings loading and fail-fast validation
├── db/               # engine, connection pool, lazy construction
├── migrations/       # Alembic upgrade/downgrade, schema `ai`, index definitions
├── data/             # catalog corpus and synthetic world generators
├── enrichment/       # LLM extraction, closed vocabularies, per-field confidence
├── families/         # name-root grouping, material fusion, guards, relative embedding veto
├── indexing/         # source text, hashing, embeddings, upsert, drift
├── retrieval/        # vector/lexical search, RRF, filters, ranking, substitutes
├── assist/           # sale assistance: structure (C30a) — modes, grouping, rule warnings,
│                     # deterministic grounding — generation (C30b) — versioned prompt,
│                     # the three checks, the single repair, degradation — and the tool
│                     # registry (C32a) — the frozen set of six, the read-only invariant by
│                     # introspection, failures as observations — and the agent loop (C32b)
│                     # — transcript caps and delimiting, six budgets, stop reasons, two traces
└── evals/            # harness, metrics, baselines, scenario replays
```

Folders are created **on demand**, not up front. `api/`, `config/`, `support/`, `db/`, `migrations/`, `data/`, `enrichment/`, `families/`, `indexing/`, `retrieval/`, `knowledge/` and `evals/` are populated; the rest are reserved names so nobody invents a
parallel taxonomy later.

## Which folder for which change

| Folder | Changes that will land here |
|---|---|
| `api/` | C01 (health), C02 (contracts, service auth, stubs, snapshot), C08 (enrichment provenance, catalog-scoped auth), C13 (landed: `/v1/index/*` real), C14 (landed: `/v1/retrieval/products` real), C17 (landed: enriched `/health` — database, index, provider credential, model contrast), C18b (landed: `POST /v1/families/audit` — tenth route, service token, judged pairs travelling in the request), C32b (landed: `POST /v1/assist/agent` — eleventh route, the contract moved by pure addition and verified leaf by leaf against C32a's snapshot kept as a fixture), **C40** (landed: the third claims profile — catalog retrieval and sale assistance accept a token with **no** `pos_id`, while every single-shop route still rejects the omission, and `test_a_blank_pos_claim_is_never_read_as_its_absence` fixes the hole the change opened and closed in one go: absence is the key being absent from the payload, anything else is a value and a value has to be usable; plus the frozen contract moved **twice** by pure addition, so the baseline fixture became `openapi-c40-baseline.json` and the two `description` leaves that change value are named one by one, keeping the guard's teeth against a third), **C42** (landed: the agent route gains a claims profile of its own — it now accepts a token with **no** `pos_id`, which every other single-shop route still rejects, so `test_auth.py` asserts the omission is served *here* and refused *there* rather than asserting a general relaxation; and the frozen contract moved once more by pure addition — `origin` on a **subclass**, which costs exactly one new schema — so the baseline fixture became `openapi-c42-baseline.json`) |
| `config/` | C01, C02 (settings, canonical OpenAPI profile), C13 (feed settings) |
| `db/` | C05 (engine, bounded pool, boot without a database) |
| `migrations/` | C05, C13 (landed: `text_provenance`, `sync_checkpoint`), C18b (landed: Alembic logging isolation — `fileConfig` must not disable the service loggers, which is destructive in-process and invisible under the CLI), C22 (landed: `pos_projection.computed_as_of` — one additive nullable column, and a test that the revision touches nothing else), C24 (landed: `ai.eval_run` / `ai.eval_case` / `ai.eval_result` — the provenance tuple a run is compared by, the CHECK that keeps a result unjudged exactly when it carries no grade, and a downgrade that leaves no trace) |
| `data/` | C06b (landed: generate/ingest CLI), C10 (landed: `world/`) |
| `enrichment/` | C09, FIX1 (landed: the four widened `piece_type` canonicals and their folding, the prompt whose heading must match `PROMPT_VERSION`, the prompt list pinned against the YAML, and the null that is an outcome and not a rejected extraction) |
| `families/` | C18a (landed: root grouping, material fusion, guards, relative veto, `POST /v1/families/suggest`), C18b (landed: audit over persisted families, orphan nomination by relative margin, source guards that the audit writes nothing and calls no provider) |
| `indexing/` | C11 (landed: source-text/v1 + embeddings), C13 (landed: catalog drain + `sku_provenance.json`), C22 (landed: typed POS feed items, the `ai.pos_projection` repository whose tombstone is a soft delete, and the POS drain with its own `pos-availability` checkpoint and per-page failures), C23 (landed: the `sync-knowledge` subcommand only — everything it drives is tested in `knowledge/`), C41 (landed: the non-blocking advisory lock taken **inside** the drain so it covers the command line too, and the start-up-plus-interval scheduler — `test_pos_scheduler.py`, whose doubles own no database because the property under test is mutual exclusion and not PostgreSQL) |
| `retrieval/` | C14, C20 (landed: two-layer synonym dictionary, equivalence-group expansion, directional bridges, the enable flag swept in-process, and the measurement CLI's safe `tsquery` composition), C21 (landed: safe `tsquery` composition with coordination ordering, weighted RRF over three ranked lists, structural filters that demote and never exclude, and the bounded cache of the embedding singleton), C22 (landed: the point-of-sale scope as the only hard filter, availability as the last demotion block, freshness read from the checkpoint and never from the rows, and the 503-on-empty / degrade-on-stale pair), FIX1 (landed: the four closed gaps gone from the exclusions, the guard test re-aimed at `filigrana`, and the plural canonical reached from its singular), C24 (landed: the deterministic tiebreak both statements needed — the compiled `ORDER BY` asserted key by key so removing it from the SQL breaks the test, and truncation proved stable where distance ties and where `coordination` and `ts_rank` tie together), C25, C26 (landed: `test_substitutes.py` — the hard filter, the continuous ordering key and the block it must not be, the inert size term, the declared signals and the provider that is never called), C27, **C40** (landed: `test_probe.py` — the unfiltered probe issued **only** when the request narrows anything, proved sequential by a counter of in-flight statements whose peak must be 1 rather than by a sleep, costing **no** extra provider call, and shown never to reach the response by planting necklaces closer than every ring and asserting none appears. The abstention reads the probe's profile when there is one — the defect being that over a filtered profile the rule can never fire when the filter is narrow, so the service served mediocre pieces and praised them — and `filters_too_narrow` is emitted only with the rule enabled, because both thresholds that define it are the rule's. The stage log carries **no vector and no query text**, and no entry is written when no probe runs) |
| `knowledge/` | C23 (landed: the seven authoring rules and the coverage invariant derived from the enrichment vocabulary, pure section chunking, deterministic `uuid5` identity whose citations resolve to a file and a heading of `data/knowledge/`, idempotent indexing that re-embeds nothing unchanged, the callable search with its own abstention threshold, the D16 ring-size table, and the offline fixture measurement), C39a (landed: `test_corpus_location.py`, where the corpus directory is **looked for** rather than derived — the previous derivation counted parent directories from the module file, which is right in a checkout and resolved inside the virtual environment once the package is installed, so the deployed container looked for the corpus at `/app/.venv/lib/data/knowledge`. The tests pin the candidate order, that the installed layout is covered, and that resolution **never raises at import**, because a missing corpus must not present itself as the whole service being down) |
| `assist/` | C30a (landed: three modes, family grouping, rule warnings, deterministic grounding), C30b (landed: `test_prompt.py`, `test_verification.py`, `test_pitch.py` and `test_generation.py` — the prompt pinned to its file and carrying no digit of its own, the three checks with the whitelist read from the payload object and the currency-adjacency case that rejects `750 €` with `750` **whitelisted**, the single repair and the literal two-call ceiling, the two policies, and degradation compared against what the structured layer produces **in the same run**; the provider is driven through `support/assist_pitch.py`, whose refusing double raises if it is called at all), **C31** (landed: `test_routing.py` and `test_guardrails.py` — the closed vocabulary enforced by a `Literal` so an invented label fails the PARSE and never propagates, the query travelling as data into the classifier call too, the clarification catalogue and its determinism, the fail-open as a branch with a named cause, the literal three-call ceiling, and the two refusals asserted with doubles that **fail loudly** — including `test_the_refusing_doubles_actually_refuse`, which drives each double through the very call production makes, because the first version of one of them overrode a method `search_knowledge` never calls and could not fire at all; the classifier is driven through `support/assist_router.py`), **C32a** (landed: `test_tools.py` — the frozen set of six asserted by NAME so that a tool returning and another leaving cannot cancel out, the read-only invariant over the object graph with a **writing port registered on purpose** to prove the check bites, and an anti-vacuity test that pins which ports each tool is seen to capture — a check that found nothing to inspect would pass over an empty list; the availability vocabulary compared against `QTY_BUCKETS` itself, since `assist/constants.py` imports nothing and writes its keys out; «sin ambito» asserted DISTINCT from «agotado» in both of its cases; and the whole registry driven once with the socket module refusing to connect — with the loop built BEFORE the guard goes up, because the Windows proactor loop opens a loopback `socketpair` of its own), **C32b** (landed: `test_agent.py` and `test_transcript.py` — the port's return type walked with `dataclasses.fields` to assert it declares NO field able to carry prose, which is the invariant as a TYPE rather than as a rule; one test per stop condition and one per budget, with the scripted double deciding what the model asks for on each turn so a non-deterministic loop is tested deterministically; concurrency asserted against a probe that records overlap rather than against a sleep; the abstention driven in BOTH directions over a flat distance profile, because the negative direction alone stays green over a field hardcoded to false — the failure mode C32a already paid for; a provider fault asserted to report its OWN stop reason after a real pass found responses claiming the model had finished when the call never arrived; and the evidence ledger shown to be inert to the read-only check **structurally**, by declaring no public method, rather than by being excluded by name — and, since the independent verification of C32b, **in the positive direction too**: a ledger that grows a `save()` is handed to the real construction seam and refused, which proves the walk reaches it. The same verification added the wall-clock budget asserted over the WHOLE request, argument included, the three stages' usage kept apart so each is priced by its own model, the global context branch actually executed, the piece a pivot abandoned kept out of the payload, and rewrote the injection test to compare the system messages the provider calls actually received — it had compared a function of no argument with itself), **C40** (landed: `assist/v5` pinned to its constant, whose three free-query tasks **forbid speaking of price and availability at all** — with several pieces on the table a placeholder has no piece to resolve against, and `PitchPlaceholderResolver` withholds the **whole** argument when one reaches it unanchored — plus a **fourth** free-query task, «uncovered», carrying the anchored rule: do not answer from memory, do not dodge with a generality, cite nothing. The hard cause `placeholder_in_free_query` is asserted **only** when `product_id is None`, with the anchored modes shown unaffected, and `test_the_cause_is_in_both_vocabularies` pins that it lives in the sweep tuple **and** the hard one, because a cause the sweep cannot partition by is a frequency nobody can read. The stub double stops writing placeholders in the free-query mode, which **inverted two existing tests**: a double that wrote them would teach every stub client a contract the real path suppresses), **C42** (landed: the provenance label asserted as a **difference of field sets** rather than by reading the payload — `"origin" not in AssistGroup.model_fields` and `set(AgentAssistGroup.model_fields) - set(AssistGroup.model_fields) == {"origin"}`, so widening the shared model breaks the test even if every response still looks right, which is the invariant as a TYPE and not as a convention; and `assist/v6` pinned to `AGENT_PITCH_PROMPT_VERSION` with `PROMPT_VERSION` asserted **not** to move, because the whole point of a separate version is that `v4` and `v5` keep the figures they were measured on), C33, C35 |
| `evals/` | C24 (landed: the golden set validation that **fails the load** when the composition stops being able to arbitrate what the set exists for, adaptive-depth pooling with appendable judgements, nDCG against a hand-computed fixture with the binary reading beside it, the two `v0` baselines and the guard that breaks when the canonical renderer drifts, deterministic truncation of the context-only catalogue with the omitted count recorded, provenance-gated comparability over frozen query vectors, and the default-change rule exercised in all four of its outcomes), C26 (landed: `test_substitutes_slice.py` — the anchored queries and the split that keeps the published ablation denominator from moving), C38 , **C31** (landed: `test_routing_cases.py` — the 119-case routing manifest whose load **refuses** when a declared count stops matching the tree, the projection of a decision onto exactly one of the six classes, the two rates kept apart with the note that they are not summable, the false positive over the answerable class as a figure of its own, and the veto — which a run that degraded **cannot** pass, because a case that was never classified is not a refusal), **C32b** (landed: `test_agent_sets.py` — the two measurement instruments and the wall between them, with the golden set crossed against BOTH agent sets in BOTH directions and normalised for accents and punctuation, because «the golden set was not used» is evidence and not a sentence in a report; the load set asserted to be exactly what its generator produces, so an artefact in git nobody can regenerate cannot ship; the calibration set asserted to declare itself `calibration-only` and to cover all six tools, since «this tool was never chosen» is only readable if the set gave the model a reason to reach for each one; and the availability fixtures checked to carry the placeholder the harness resolves — without it the pivot scenarios measure the availability of whatever the search happened to return, silently; and `test_agent_sweep.py`, **the first tests the pass harness ever had**, written by the independent verification of C32b: cost priced stage by stage with each stage's own model, pivot rates per arm and only over availability fixtures — the first form raised `KeyError` on the committed calibration set at the moment of writing the artefact —, the calibration scored by code with the semantics the file declares, rows written as they are produced so an interrupted run can be rescored, and `--rescore` of the committed run reproducing the figures the report publishes), **C40** (landed: the persisted probe profile and the rule it was captured under travel **in the capture file** and not read from `Settings()`, because phase C cuts every socket and `Settings()` demands an environment; `--rescore` recomputes the abstention from them, a capture written before the probe still loads, and one carrying a probe with no rule is **refused rather than guessed**. `CAPTURE_VERSION` deliberately does **not** move: the rule reads another profile and does not alter the candidate set, so earlier captures stay valid — and there is a test that fixes exactly that), **C42** (landed: the harness's two new instruments, which are what makes the pass auditable at all — `placeholders_in` counts markers on the **first** attempt and not on the repaired one, because counting the survivor measures the repair and not the prompt; and `projection_freshness` reads `projection_synced_at()` from `ai.sync_checkpoint` and **never** `ai.pos_projection.refreshed_at`, recorded **per row** because a pass lasts longer than the 3.600 s staleness ceiling and without it a fresh pass and a degraded one are indistinguishable after the fact — the contamination that already cost part of C32b's retrieval figures. Rows predating the instrument carry `None` and **not zero**, so «not measured» cannot be read as «measured at zero») |

Changes with no Python zone (C03, C04, C07, C08, C12, C15, C16, C19, C28, C29,
C34, C36, C37) are tested on the .NET or frontend side. C17 also ships a post-deploy smoke
check that belongs to the deployment pipeline rather than here — but it does have a
Python zone after all: the enriched `/health` is tested in `api/test_health_report.py`,
with its probe double in `support/fake_health_probe.py`.

Source: [`proyecto-final-plan-changes-openspec.md`](../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md).

## Where does my test go?

Ask what would have to break for the test to fail:

- **A wire contract** — status code, payload shape, auth decision, mounted route →
  `api/`, even when the endpoint belongs to another domain. `test_assist_stub.py`
  lives in `api/` because it asserts the frozen contract, not sales reasoning.
- **A computation** — ranking order, similarity, extracted fields, metrics →
  the module that computes it. **C30a did exactly this**: it replaced the assist stub
  with a real structural layer, the behavioural tests were born in `assist/`
  (`test_modes.py`, `test_grounding.py`, `test_orchestrator.py`) and the contract test
  stayed in `api/` — joined there by `test_assist_contract.py` for the moved schemas and
  `test_assist_real.py` for the route with stubs disabled.
- **Both** — split it. A contract assertion buried in a ranking test makes the
  contract regression invisible.

## Support vs fixtures

- `support/` holds **code**: request builders, token helpers, the two scripted provider seams of the assistance layer — `assist_pitch.py` for the argument and `assist_router.py` for the classifier, both wrapping the **real** client so the parse, the timeout and the usage extraction are the production ones and only the socket is replaced — and the injectable
  fakes that stand in for LLM and embedding clients. Importable from any test
  (`tests/` is on `pythonpath`).
- `fixtures/` holds **data**: request/response payloads, golden-set entries, corpus
  samples. The changes plan already fixes this path for evaluation fixtures.

`conftest.py` is pytest's fixture mechanism, **not** a module to import. Today four
test files do `from conftest import build_settings` / `from sample_requests import
V1_REQUESTS`; those imports only resolve because every test sits in one flat
directory and break the moment subfolders exist. They move to `support/`.

## Conventions

- **Naming**: `test_<unit>_<scenario>_<expected>` — the Python convention fixed in
  the changes plan, distinct from .NET (`Method_Scenario_ExpectedResult`) and the
  frontend (`should [behavior] when [condition]`).
- **Module docstring**: one line saying what the file guards, plus the delivering
  change. Example: `"""Frozen /v1 contract shapes. Delivered by C02."""`
- **Local fixtures** go in a `conftest.py` inside the folder that needs them — until a
  second folder needs the same one. The ephemeral-PostgreSQL fixtures (`postgres_container`,
  `database_url`, `alembic_config`, `migrated`) lived in `migrations/conftest.py` until C22,
  when the projection repository needed them from `indexing/`; they moved to the root
  `conftest.py` and `migrations/conftest.py` kept only what is its own (`database_name`,
  `run_bootstrap`).
- **Markers**: everything is a fast in-process unit test by default. Declare the
  exceptions — `@pytest.mark.db` for tests needing PostgreSQL with pgvector,
  `@pytest.mark.slow` for evaluation sweeps — so CI can select them.

## Hard rules

No test calls a real LLM provider, embedding API, or production RDS. Fakes are
injected from `support/`; the `forbid_network` fixture turns any socket connection
into a failure, and stub tests use it to prove they stay offline.

```bash
cd ai-service
uv run --system-certs pytest
```

## Current state

Populated after C24: `api/`, `config/`, `db/`, `migrations/` (C05 + C13 + C18b + C22 + C24), `data/` (C06b/C10), `enrichment/` (C09 + FIX1), `indexing/` (C11 + C13 + C22), `families/` (C18a + C18b), `retrieval/` (C14 + C20 + C21 + C22 + FIX1 + C24 + C26), `knowledge/` (C23 + C39a), `evals/` (C24 + C26) and `support/`. Remaining folders are reserved names. Two settings in
`pyproject.toml` hold the layout together:

- `pythonpath = ["src", "tests"]` — makes `support/` importable from any subfolder.
- `addopts = "--import-mode=importlib"` — stops same-named test modules in
  different folders from colliding.

Never anchor a path with `Path(__file__).parents[N]` in a test file: the count is
wrong as soon as the file changes depth. Import from `support/paths.py` instead,
which is where `AI_SERVICE_ROOT`, `OPENAPI_SNAPSHOT`, `ALEMBIC_INI` and
`MIGRATIONS_DIR` are resolved once.

`build_settings()` in `support/settings.py` pins `database_url` to `None`. That is
not decoration: pydantic reads unset fields from the environment, so without the
pin a developer with `DATABASE_URL` exported would see tests build engines against
their own database — and the cases that assert "no database configured" would
quietly stop failing when they should.

## C26 — out-of-stock substitutes

Two new files and one extended double.

| file | what it owns |
|---|---|
| `retrieval/test_substitutes.py` | the engine: hard filter on `piece_type`, the three exclusions, family recall without family priority, the continuous ordering key, the inert size term, availability that demotes and never removes, the four signals, `match_reasons`, the absence of abstention, the three unusable-source errors, and the provider that is never called |
| `api/test_substitutes_route.py` | the route: the C02 stub still served under `STUB_MODE`, 200 instead of 501 in real mode, 422 naming the cause for an unusable source, 503 without a database and **no provider key demanded**, and the token scope winning over the body |
| `evals/test_substitutes_slice.py` | the slice: every substitutes query anchored, one anchor with no family, and the split that stops the published ablation denominator moving |
| `support/fake_product_search.py` | extended with `source_document` and `neighbours_of`, plus `style_tags` and `price_band` on `FakeIndexedRow`. The fake mirrors the statement predicate for predicate and has **no restricting scope**, because there is none in the SQL either: a fake that dropped an unstocked candidate would make the invariant untestable |

**The fixture is measured, not invented.** `SKU13_NEIGHBOURS` in `test_substitutes.py` holds
the ten real cosine distances the live index returns for `SKU13 Anillo erizo de mar M` after
the `piece_type` filter. Round numbers would let the ordering tests pass on arithmetic the
catalogue does not produce; two of these scenarios only discriminate because the real gaps are
as narrow as they are.

**`test_different_size_sibling_stays_inside_the_visible_window` is the one that matters.**
Every other scenario here would also pass under an integer-block size term — the shortcut
`demotion_rank` invites, since it has one written already. This one does not. Re-ordering the
same fixture under a block: the nearest sibling `SKU14` falls from position 1 to position 4,
behind all three size matches, and `SKU15` leaves the top five. Both assertions fail. It is not
enough that the right size rises; the demoted sibling has to stay visible.

**Two existing tests moved rather than disappeared.** `test_stub_mode.py` had
`/v1/retrieval/substitutes` in its 501 parametrisation and asserted the string `"C26"` in the
detail. The route answers now, so the 501 property was **re-homed onto `/v1/assist/sale`**
(waiting on C30) instead of being deleted, and a new
`test_no_retrieval_route_is_left_answering_501` asserts the obligation C26 lifted, in the
negative.

**And C30a moved it a second time.** `/v1/assist/sale` now serves its real implementation, so
the 501 parametrisation carries **only `/v1/inventory/propose`**, whose branch was cancelled on
2026-08-31 and which is therefore a declared limitation rather than pending work. The property
was re-homed the same way it was the first time —
`test_the_assistance_route_is_no_longer_left_answering_501` asserts it in the negative — which
is why the pattern is worth naming: a route that starts answering does not delete the 501 test,
it hands it to the next route in line. When `/v1/inventory/propose` is the last one, the
parametrisation stops being a list and becomes a statement about one route.

**A trap this change walked into, recorded so the next route does not.** FastAPI publishes a
handler's **docstring** as the operation `description`. `retrieve_substitutes` had none in the
frozen snapshot — it was written as a two-line stub — so adding one turned
`test_openapi_snapshot_is_stable` red on a field that appeared out of nowhere. The explanation
lives in a comment above the decorator instead. `retrieve_products` keeps its docstring because
the snapshot already carries it.

## C25 — ranking, business signals and abstention

`tests/retrieval/test_abstention.py` is new and owns the rule that declines to answer: the shape
of the distance profile, what the rule must never do, and the observability. Its fixtures carry
**twenty** candidates rather than ten, because a profile cannot be flat against a rule that asks
for fifteen and a test that passed on that technicality would witness nothing.

The rest extends files that already existed:

| file | what C25 added |
|---|---|
| `test_fusion.py` | that `fuse` composes with itself without touching the formula |
| `test_orchestrator.py` | the two-stage fusion, the coverage rule and its **gate** |
| `test_pos_scope.py` | the reading scope against the restricting one, and the business score |
| `test_filters.py` | the ordering key with a continuous tail |
| `test_sweep_phases.py` | capture and re-score, and that the second reaches no provider and no database |
| `test_provenance_and_report.py` | the fusion mode as the sixth element of the provenance, the dirty-tree marker, and that the published table carries no withdrawn claim |
| `test_golden_validation.py` | the out-of-domain category at its new floor of twenty |

**What C25bis changed here.** Four tests went with the single-stage fusion and the per-list
weights they exercised — `test_flat_fusion_mode_reproduces_the_published_baseline`,
`test_vector_branch_weight_defaults_below_lexical`,
`test_the_two_lexical_weights_sum_to_one_lexical_list` and
`test_baseline_row_is_still_selectable_and_reproducible` — and seven arrived:

| test | what it pins |
|---|---|
| `test_the_flat_arithmetic_that_was_retired_buried_the_vector_leader` | **the fossil**: why the composition was retired, over `fuse()` alone, with the retired weights as literals local to the test. Reachable by no configuration |
| `test_no_flat_fusion_path_exists` | that it cannot come back through a setting or an orchestration parameter |
| `test_the_internal_lexical_weights_are_equal_and_not_settable` | that no per-list weight survives, and that the lexical branch's internal split is a declared constant |
| `test_the_default_branch_ratio_is_one_vote_each` | the pin that replaced "the vector weight is lower", whose subject no longer exists |
| `test_the_retired_baseline_config_no_longer_loads` | that the archived configuration is preserved **and** refused, by the unknown-key guard that already existed |
| `test_the_baseline_row_is_archived_rather_than_selectable` | conservation in place of reproducibility |
| `test_a_retired_fusion_knob_no_longer_exists_and_exporting_it_does_nothing` | that a stale export is inert, and why the boot is not made to fail over it |

Two tests were narrowed rather than removed, because the property they protect survived the
composition they compared against: `test_vector_top_hit_reaches_the_top_five_without_lexical_
consensus` and `test_low_confidence_means_branch_disagreement_and_not_list_disagreement`. Both
lost their second arm — serving the same corpus under the retired composition — and both are
stronger for it: what was a comparison between two compositions is now enforced by the shape of
the code.

**The gate is `test_full_coverage_leaves_the_lexical_weight_untouched`.** It covers five
categories measured at coverage 1,00, and each of its five queries is a **real** query of the
golden set chosen because the naive denominator breaks it. Verified by injecting that
denominator: all five fail. A gate that cannot fail is not a gate.

**C22's sales guard was retired and replaced.** It forbade `sales_30d`, `sales_90d` and
`last_sale_at` from reaching the pipeline at all. `sales_30d` now travels — the report publishes
its distribution and C26 needs it — so the guarantee moved to where it can still be structural:
**the protocol the ordering reads does not carry the field**, so `demote` cannot consume it even
by accident. The other two still never reach the pipeline, and no ordering module may reach for a
wall clock.

