# Design — add-pos-projection-soft-prefilter (C22)

## Context

C05 created `ai.pos_projection` with its `qty_bucket` `CHECK` and its reverse index. C12 built `GET /api/ai/index-feed/pos-availability` — page 200, keyset cursor, tombstones, bucketed quantities, sales aggregates — and made it normative in the `index-feed` spec. C13 built the client that reads it (`fetch_pos_page`, `parse_pos_page`, returning raw dicts) and was explicitly forbidden to consume it. The table has **zero rows**, and the point-of-sale scope is applied only by .NET, at hydration, after the retriever has already spent its window.

Everything below was measured on 2026-09-05 against the local PostgreSQL (PostgreSQL 15.19, `vector` 0.8.6, 1.168 live documents, 6.720 inventory rows). Full record in [`c22-exploration-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-exploration-measurements.md). All probes were read-only and used embeddings already persisted in the index, so they are reproducible without provider credentials.

Six measurements govern the design. Three of them contradict the ficha.

| # | Measurement | Consequence |
|---|---|---|
| 1 | Page arithmetic over 20 probes: **eight of eleven** points of sale have ≥6 of 20 searches below a page of 10. FORNELLS 12/20, worst case **1 survivor**; one MAO-AIR query leaves **zero** | The problem is systemic, not FORNELLS-specific. Motivates the whole change |
| 2 | Unassigned rows (`Inventory.IsActive = false`) are **6,9 %** at CIU-CENTRE, **8,7 %** at FORNELLS, **8,8 %** at MAO-AIR; 670 of 6.720 overall | Row existence as the hard filter would spend that share of the window on candidates `Carried()` is certain to drop. Decides D1 |
| 3 | `Carried()` does **not** filter by quantity, and zero-stock assigned rows are **34,4 %** at MAO-AIR, 12,0 % at FORNELLS, 11,7 % at HT-GALDANA | Stock is what must demote without excluding, and the signal is coarse enough to matter. Decides D3 |
| 4 | HNSW is **never chosen** on the live path: Seq Scan 8,2 ms (canonical) and 10,8 ms (live shape) against **113,7 ms** forced, which returns **40 of 60** rows. Scoped to FORNELLS: **7,3 ms**, 60 rows — *re-measured after implementation: 14,8-17,3 ms scoped against 18,0-33,1 ms unscoped, see D2* | Exact KNN over the scoped subset is not an engine change, it is what the planner already does. Decides D2 |
| 5 | `IndexFeedService.MapPosItem` hardcodes `IsAssignedHint = true` on upserts and routes inactive rows to tombstones | The field is a constant today; without a soft delete it is unreachable and the ficha's demotion test is unsatisfiable. Decides D4 |
| 6 | Against the wall clock, `sales_30d` non-zero pairs fall **16,28 % → 1,32 % (22 Sep) → 0 (26 Sep)**; `sales_90d` survives to 21 Nov | C25 would calibrate on a dead signal. Decides D7 |

## Goals / Non-Goals

**Goals:**

- Fill the operator's page with products their point of sale actually carries, without letting a stale projection hide a valid product from .NET.
- Populate `ai.pos_projection` from the existing feed, idempotently and resumably, with no migration and no new HTTP surface.
- Make availability a ranking signal and assignment a scope, each in the place the measurements justify.
- Report projection freshness truthfully and let it govern degradation instead of decorating the response.
- Stop the sales windows from drifting to zero, and make the retrieval configuration reproducible for C24.
- Leave a clean seam for C25 (weights) and C26 (substitutes) without implementing either.

**Non-Goals:**

- Reading `sales_30d` / `sales_90d` / `last_sale_at` for ranking — persisted here, consumed by **C25**.
- Substitutes (C26), complementary items (C27), knowledge corpus (C23), golden set (C24).
- Any in-process scheduler, background task, or new `/v1` route.
- Partial HNSW indexes, `hnsw.iterative_scan`, or threshold recalibration by quantile (C25).
- The interface consumer of freshness — the short-page notice — which lives in C34/C36 territory.
- The other three wall clocks in the repository (movement report, return window, dashboards) and the pre-recording date shift, which is a demo operation.
- Reverting `AiGateway:RetrievalTimeoutMs` to 800 ms.

## Decisions

### D1 — The hard filter is `is_assigned_hint`, not row existence

The ficha asks that an unassigned product *«be penalised and not removed»*. But the authority's exclusion predicate is literal — `AssistedSearchRepository.Carried()` filters `Inventory.PointOfSaleId = pos ∧ Inventory.IsActive ∧ Product.IsActive` — so a product that survives in Python only to be dropped by .NET has consumed a slot for nothing. Measurement 2 sizes it: 7-9 % of the window at the three points of sale that have an operator.

The design's promise («a valid product cannot disappear because of a stale projection») is about **staleness**, not about semantics, and staleness is answered by D6, not by keeping candidates the authority will certainly reject.

| Alternative | Verdict |
|---|---|
| Row existence is the hard filter; `is_assigned_hint` demotes | Literal reading of the ficha, but spends 7-9 % of the window and is unreachable anyway per D4 |
| **`is_assigned_hint` is the hard filter** | ✅ Excludes exactly what the authority excludes; costs nothing but staleness, which D6 bounds |
| No hard filter at all, everything demotes | The page stays short — the change would buy nothing |

**Consequence:** the ficha's `test_unassigned_product_is_penalised_not_removed` is renamed to `test_out_of_stock_product_is_penalised_not_removed`, which is the test that protects the principle that is actually in force (D3).

### D2 — Scope CTE plus exact distance, not a plain join over HNSW

S10 warns that approximate indexes do not understand `WHERE`: the index returns its neighbours and the filter discards them afterwards, silently. Measurement 4 shows both halves of that story here — the trap is real (forced HNSW returns 40 of 60 rows) and it is **not on the live path**, because since C14 the planner has chosen a sequential exact scan at 1.168 rows.

So the decision is to make explicit what the database already does: a scope CTE over `ai.pos_projection`, joined to `ai.product_document`. Correct by construction, deterministic, and no slower.

**Two corrections from the implementation measurement**, recorded here rather than left to be rediscovered. First, the exploration's figures were optimistic by roughly a factor of two: measured on the populated projection with per-node timing off, the scoped statement runs at **14,8-17,3 ms** against **18,0-33,1 ms** unscoped. The direction holds — scoped is not slower — but 7,3 ms is not a number to cite. Second, and more consequential: the planner filters `ai.product_document` by distance over all 1.168 rows and hash-joins the scope **afterwards**, so the CTE does **not** reduce the number of distance computations. The justification for this shape is therefore not compute saved; it is that the scoped subset is established before the ordering, so the branch depth is honoured by construction rather than by the planner continuing to choose well. Full record in [`c22-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-implementation-measurements.md).

| Alternative | Verdict |
|---|---|
| Plain join and trust the planner | Works today; leaves the truncation risk one statistics change away, with no visible error |
| `SET LOCAL hnsw.ef_search = 200` | Still approximate, still a number chosen by hand |
| `hnsw.iterative_scan` (available: pgvector 0.8.6) | The vendor's answer, but changes index behaviour for every consumer to solve a problem this corpus does not have |
| Partial HNSW index per point of sale | S10's structural answer for very selective filters — twelve indexes to maintain at 1.168 rows |
| **Scope CTE + exact KNN over the subset** | ✅ Exact, deterministic, faster, and no index behaviour changes |

The HNSW index stays in place and the README declares the scaling ceiling: when the corpus grows an order of magnitude, `iterative_scan` and partial indexes are the path, and the cardinality logging added here is what will show it.

### D3 — Stock demotes as one more block of `demotion_rank`

`filters.py` already implements exactly this: a stable block sort that reorders without removing, whose docstring says it is *«the seam C25 replaces with calibrated weights»*. Availability joins it as a fourth component of the **single** sort key, so priority is explicit rather than emerging from the order in which two sorts were applied.

| Alternative | Verdict |
|---|---|
| A fourth RRF list built from the projection | ❌ An RRF list is a retrieval branch's opinion. Availability retrieves nothing, would hand votes to documents no branch saw, and would corrupt `low_confidence`, defined as cross-branch consensus |
| Arithmetic penalty in the SQL `ORDER BY` | ❌ Mixes `ts_rank` and cosine scales — precisely what RRF exists to avoid, as `fusion.py` states |
| **A fourth block in `demotion_rank`** | ✅ One stable sort, explicit priority, C25's seam untouched |

Two sub-decisions:

- **Priority: last.** The key becomes `(price_ceiling, size, materials, out_of_stock)`. What the operator typed outranks a signal they did not ask about. The opposite is defensible at a till counter; it is not settled by argument here, it is handed to C25 with the golden set.
- **Binary, not graded.** `qty_bucket == '0'` against everything else. Ordering between `1-2` and `3+` would be a magic number without evidence — S10's warning: *«if you cannot explain in one sentence why a boost is 1,3 and not 1,5, it was not ready for production»*. The three tiers are persisted and unread until C25.

### D4 — The `unassigned` tombstone is a soft delete

Measurement 5: `IsAssignedHint = true` is hardcoded on the upsert branch and inactive rows leave as tombstones, so the feed cannot produce `false`. A `DELETE` would keep it that way forever.

The soft delete (`is_assigned_hint = false`, `qty_bucket = '0'`, `refreshed_at` bumped) makes the field reachable, makes the state observable, and preserves the history C26 needs to distinguish *«never carried here»* from *«no longer carried»*. Combined with D1, a soft-deleted row is excluded from retrieval — the same outcome a `DELETE` would give today — but the row survives for a consumer that does not exist yet.

If the tombstone names a pair with no row, it is inserted in that state rather than ignored: the feed's cursor window can start after the upsert that created it.

### D5 — Freshness comes from the checkpoint, never from `refreshed_at`

The feed is **incremental by keyset**: an assignment that does not change is never re-emitted, so its `refreshed_at` stays at the instant it last changed. `max(now − refreshed_at)` would report months on a projection synchronised thirty seconds ago — it measures *when this changed*, not *when we looked*.

`projection_age_seconds` is therefore `now − ai.sync_checkpoint.last_incremental_sync_at` for `feed = 'pos-availability'`, read with a short cache (**10 s**, the same value and the same reason as C17's `/health` report: the pool is capped at 5 with no overflow).

### D6 — The freshness field governs behaviour

A field with no consumer would repeat the pattern C21 criticised — `tsv` populated since C05 and queried by nobody. Here it is load-bearing:

```
projection EMPTY for this pos_id
  → 503, "refusing to abstain over an empty projection"
    (precedent: count_compatible == 0 in orchestrator.py)

projection STALE (age > JPV_POS_PROJECTION_MAX_AGE_SECONDS)
  → hard filter NOT applied for this request; warning logged;
    projection_age_seconds tells the truth in the response
    (page may be short; no valid product is hidden from .NET)

projection FRESH
  → hard filter applied
```

Empty is a dependency failure, so it fails loudly — a 200 with an empty list is indistinguishable from a legitimate abstention, which is the lie C14's `count_compatible` guard already exists to prevent. Stale is a degradation, so it degrades openly — the design's promise that a stale projection cannot hide a valid product is kept exactly here, and the honest cost is a possibly short page.

**Ceiling: 3600 s.** The design cadence is 5-10 minutes and the real one will be a cron; an hour degrades only under sustained failure, not under ordinary lateness. Deliberately generous: degrading too eagerly would give up the change's entire benefit over a transient.

### D7 — The sales clock is injected, with a declared constant

Measurement 6 gives the deadline. But the reason this belongs in the design and not in a patch is different: C24 requires `test_run_is_reproducible_for_same_config_and_seed` and the delivery checklist requires an ablation table *reproducible with one command*. **A ranking that reads `now()` was already irreproducible**, dataset horizon or not.

The injection point needed no refactor: `IIndexFeedRepository.GetSalesAggregatesAsync(pairs, now, ct)` has taken `now` as a parameter since C12, fed by `IndexFeedService` from `_timeProvider`. The change is to read `IndexFeedOptions.SalesAsOf` when set.

| Alternative | Verdict |
|---|---|
| Regenerate the world with a later horizon | ❌ Destroys 156 approved families, C09 profiles, C13's index and C21's calibration |
| Shift every sale date by N days | ❌ Breaks the seasonality the world models (FORNELLS is extreme summer), invalidates the C10 report, and must be repeated every few weeks |
| Swap to `sales_90d` + decay on `last_sale_at` | Structurally the most robust — a normalised decay is invariant to clock drift where a window loses information — but it redesigns C25's signal for a problem an injected clock already solves |
| **Injected clock, declared constant `2026-08-23T23:59:59Z`** | ✅ Minimal fix: `sales_30d` recovers a stable 16,28 %, C25 keeps its signal, and reproducibility is gained |

The value is a **configured constant**, not `max(SaleDate)`: the latter would be 2026-08-29 today, contaminated by the 7 manual test sales of C16, and would drift every time a sale is recorded in the demo. Absent configuration, behaviour is today's wall clock, so nothing changes for anyone who does not set it.

**And the instant is persisted per row, which costs this change its "no migration" claim.** C05 created `ai.pos_projection` with no column for it, and the ticket's inventory checked that table for *existence* — its `qty_bucket` `CHECK`, its reverse index — not for column adequacy, so five documents came to declare "no migration of any kind" over a fact that does not hold. The claim was an observation that the tables already existed, never a constraint someone accepted a cost for, and it does not survive contact with the schema.

Persisting it matters because the drain is **incremental**: the feed re-emits only pairs whose inventory row moved, so a pair that does not change keeps forever the `sales_30d` the run that wrote it computed. Configure `SalesAsOf` after a first drain and the projection holds wall-clock rows next to horizon rows with nothing to tell them apart — the artefact-recorded-as-finding this change exists to prevent, reappearing inside C25. `refreshed_at` is not a substitute: reconstructing which rows are which from it needs out-of-band knowledge of when the configuration changed, which is exactly what "declared" is supposed to replace.

| Alternative | Verdict |
|---|---|
| Do not persist it; leave it in configuration | ❌ Reading the projection cannot tell you which clock produced a figure, and a mixed projection is undetectable |
| Persist it on `ai.sync_checkpoint` instead | ❌ Same revision, different question: the checkpoint holds the **last** clock while the rows can come from several |
| Defer the column to C25 | ❌ Same migration one change later, on a projection already contaminated — the follow-up FIX this avoids |
| **One additive nullable column on the projection** | ✅ Answers the question C25 asks, per row; same hand-written shape as C13's `b8e3c1a4d7f0` |

### D8 — CLI, not a route and not a scheduler

`ai-service-api-contracts` enumerates the `/v1` endpoints in a MUST, so a new route is a normative contract change this change does not buy. An in-process scheduler adds a background task to a container capped at 512 MiB that already uses 232, competing for a pool of 5 connections. Production will need something; the demo does not.

`python -m jbg_ai.indexing sync-pos [--full]` with a documented cron, mirroring the C13 `sync` command including the `backend/.env` load. **Honesty comes from `projection_age_seconds`, not from a hidden cron**: if nobody has synchronised, the response says so and D6 acts on it.

### D9 — `pos_id` that does not parse is rejected

The auth module wrote the rule before this change existed: *«a wildcard `pos_id` is exactly what must never exist, because from the soft-prefilter change onward that claim is the retriever's only hard filter»*. A token whose `pos_id` is not a UUID is a mis-issued token, not a request for a global search. **422**, never a silent unscoping.

Consequence to pay: `ai-service/tests/support/settings.py` sets `TOKEN_POS_ID = "POS-B"`, while `AiServiceTokenFactory` signs `pointOfSaleId.ToString()` — a canonical GUID. The test constant becomes a UUID and the dependent battery moves with it. Known work, not a surprise.

### D10 — The ablation flag follows the C20/C21 pattern

Default in `Settings`, effective value as a parameter of `retrieve_products`, so C24 sweeps configurations inside one process without restarting and without moving the frozen request schema. With the prefilter off, retrieval behaves exactly as before this change.

Related decision recorded here because C22 forces it: **C24's golden set is labelled unscoped**. Scoped labelling would mix retrieval quality with assortment coverage in one nDCG number. The effect of this change is reported separately as **fill rate per point of sale**, whose "before" baseline is computable from what C04 already persists (`% of searches with ResultsCount < page`, grouped by `PointOfSaleId`).

## Risks / Trade-offs

- **Three live specs contradict this change literally** — `vector-retrieval` («the search SQL does not filter by `pos_id`»), `product-document-indexer` («MUST NOT … write `ai.pos_projection`») and `index-feed` («over the last 30 and 90 days»). → Three MODIFIED deltas are mandatory. Without them `openspec validate --all --strict` **stays green over false specs**, which is the August failure in its worse form: well-formed and lying.
- **Deleting the tombstoned row instead of soft-deleting it** looks obviously right and is the trap. → It makes `is_assigned_hint` permanently unreachable and removes C26's only way to tell "never" from "no longer". Pinned by test.
- **Reading freshness from `max(refreshed_at)`** looks obviously right and is the trap. → It reports months on a projection seconds old, because the feed is incremental. Pinned by test.
- **Trusting the planner with HNSW** → forced, it returns 40 of 60 rows *with no visible error*; S10 names this the most bewildering failure mode to debug after the fact. Mitigated by D2 and by logging the scoped cardinality on every search.
- **A too-aggressive staleness ceiling** would surrender the change's benefit on any transient. → 3600 s, plus the age declared on every response so the degradation is visible rather than guessed.
- **`TOKEN_POS_ID = "POS-B"`** breaks the retrieval battery the moment the claim is parsed. → Explicit task, done before the scope lands.
- **`openapi.json` moves for the first time since C13.** → Deliberate; the optional field is backward compatible for the .NET deserialiser, and the snapshot test exists to force the act. Regenerate with the README one-liner, never by hand.
- **Zone shared with C25** (also `retrieval/`) and **C23** (also `indexing/`) → the §1 rule of the plan holds: not opened in parallel, even by the same hand.
- **The fill-rate measurement used self-similarity probes**, not operator queries against the real provider. → Reproducible without credentials, but the closing verification must repeat it with real queries and with C04's telemetry as the "before" baseline.
- **`sales_*` columns are written and not read.** → Deliberate and declared: they are C25's input, and writing them now is what lets C25 be a ranking change rather than a sync change. The decay measurement is recorded so C25 knows what it is calibrating on.

## Migration Plan

One additive Alembic revision (`ai.pos_projection.computed_as_of`, nullable, no default), no EF Core migration. Deployment order:

1. Apply the revision. The table is empty and the column is nullable, so there is no backfill and no table rewrite.
2. Ship `IndexFeed:SalesAsOf` **already set** to `2026-08-23T23:59:59Z`.
3. Run `python -m jbg_ai.indexing sync-pos --full` once to populate `ai.pos_projection` and create its checkpoint row.
4. Enable the prefilter (`JPV_POS_PREFILTER_ENABLED`, default on). Before step 3 the guard of D6 answers 503, which is the correct answer for an unsynchronised projection.

Setting the reference instant **before** the first drain, rather than after it, is the whole point of the ordering. An incremental run recomputes nothing — the feed re-emits only pairs whose inventory row moved — so a clock changed afterwards leaves every unchanged pair on the old one, and recovering costs a full `sync-pos --full`. An earlier draft of this plan had step 4 setting the constant and "re-running the sync so the stored aggregates are recomputed"; that step does not do what it says, and `computed_as_of` is what makes its failure visible rather than silent.

**Rollback:** set `JPV_POS_PREFILTER_ENABLED=false` — retrieval returns to pre-change behaviour with no deploy. `ai.pos_projection` can stay populated; nothing else reads it.

## Open Questions

None blocking. Two values were decided by default when the exploration closed and are recorded here rather than left implicit:

| Question | Decision | Revisit when |
|---|---|---|
| Staleness ceiling | **3600 s** (D6) | A real sync cadence is established in production |
| Freshness cache window | **10 s** (D5), matching C17's `/health` | The connection pool stops being the binding constraint |

Deferred to their owners: the relative priority of stock against typed constraints inside `demotion_rank` (**C25**, with the golden set) · whether the rotation signal should become `sales_90d` plus normalised decay instead of `sales_30d` (**C25**) · the interface consumer of `projection_age_seconds` (**C34/C36**) · the other three wall clocks and the pre-recording date shift (demo operation, outside the RAG metrics).
