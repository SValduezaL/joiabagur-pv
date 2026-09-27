# Design — add-hybrid-search-rrf (C21)

## Context

C05 created `ai.product_document.tsv` as a generated `to_tsvector('spanish', doc_text)` column with a GIN index. It is populated on all 1.168 live rows and **no code reads it**. C14 built the vector branch and left `mode=hybrid` and `mode=lexical` running it, saying so in `debug.notes`. C20 built the expansion dictionary; `expand_query` runs on every real retrieval, logs `stage=expand` and **nothing consumes its result**.

Everything below was measured on 2026-09-02 against the local PostgreSQL (1.168 live documents) and, for the vector figures, against `openai/text-embedding-3-small`. The full record is [`c21-hybrid-exploration-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md); the rubric is the one C20 used — a hit is a top-ten result with the right `piece_type` **and** the right material — so the numbers are comparable with C20's.

Nine measurements govern the design. Four of them contradict something already written, and two of those four contradict the exploration's own earlier recommendation.

| # | Measurement | Consequence |
|---|---|---|
| 1 | Corpus coverage by `doc_text` line: `Tipo:` 1.157/1.168 (99 %), `Materiales:` 1.042 (89 %), `Talla:` 529 (45 %), `Colores:` 224 (19 %), `Ocasiones:` 150 (**13 %**), `Estilo:` 133 (**11 %**) | Structural fields are trustworthy; subjective ones are not. Decides D4 |
| 2 | Strict `&&` between groups leaves **7 of the 10 real recorded queries at zero documents**. The *zero-drop* rescue rescues **one** | `anillo & plata & regalar` = 0 because only 7 documents of 1.168 mention `regalo` and none is a silver ring. Decides D2 |
| 3 | OR plus coordination contains the conjunction's result **at the head** of the list, and lifts the *Anillo de Filigrana* from positions 7-8 to 1-2 | It dominates the conjunction; the *zero-drop* becomes a no-op. Decides D2 |
| 4 | `materials`: 126 documents (10,8 %) with none, 951 with one, 91 with two or more. `@>` reaches **60** where `&&` reaches **913** | `@>` is a recall cliff, and a hard `&&` deletes 36 rings from every silver-ring query. Decides D5 |
| 5 | Branch parity is the worst fusion: **96/120** at `w_vector = 1,0`, **105/120** at 0,33, **67/120** vector-only, **107/120** lexical-only | The vector branch fills its quota whether or not it understands, so under RRF it always votes at full strength. Decides D3 |
| 6 | Asymmetric depth (200 lexical / 60 vector) costs **6-8 points of 120**. Symmetric: 40 → 113, 50 → 113, **60 → 111**, 100 → 107, 200 → 107 | With `k=60` the rank-200 document keeps 38 % of the leader's vote. Decides D3b |
| 7 | Distance `<= 0,65` passes **1.168 of 1.168** documents on ordinary queries and **0** on a nonsense control (`d_min` 0,700) | The threshold is above the median: the `LIMIT` is the real cut. Decides D3b and one declared limitation |
| 8 | Coordination restricted to well-covered fields: **113/120** without occasion and style, **114/120** also without colour, against 111 — **with no losses** | A field covered at 13 % must not decide the order. Decides D4 |
| 9 | `phraseto_tsquery` leaves `aro de dedo` at **0** documents against `plainto`'s 6. An exact name already heads both lexical lists; for `SKU690` the vector branch returns **0** candidates | Decides D6 and D7 |

## Goals / Non-Goals

**Goals:**

- Switch on the lexical branch and consume C20's groups, with the operator's own phrasing keeping a vote of its own.
- One fusion mechanism, pure and domain-free, reusable by C23, C25 and C26 without going through this endpoint.
- Structural intent from the query text expressed as ordering, never as exclusion, so a projected price can never delete a valid product.
- Provenance the operator can read and the harness can measure, without moving the frozen contract.
- Honest degradation when the embedding provider fails: serve what exists and say what served it.
- Pay the embedding-singleton half of the deferred debt, including the part its description did not anticipate.

**Non-Goals:**

- Business signals in the ranking, POS projection, substitutes, knowledge corpus, golden set — C22, C23, C24, C25, C26.
- Reverting `AiGateway:RetrievalTimeoutMs` from 2500 to 800 ms: it needs a demo deploy and a cold/warm re-measurement. Own change.
- Applying the price ceiling against the real price: that is .NET's, and it moves `openapi.json`.
- Recalibrating the distance threshold. Measurement 7 shows it would need a per-query quantile — C25's ficha already claims that work.
- Cross-encoder reranking, typo tolerance, `pg_trgm`, LLM query rewriting, `ai.query_log`, persisting anything.
- Editing `indexing/embeddings.py` (frozen since C11) or `enrichment/vocabularies.yaml`; regenerating `openapi.json`; any migration; any change under `backend/`.

## Decisions

### D1 — Three ranked lists, not two

The lexical branch emits **two** lists: `A` from the operator's typed text, `B` from C20's expanded groups. `C` is the vector list.

C20 measured that a single widened `tsquery` pushes the three matching «Sortija» products out of the top ten, and that RRF over the original and widened lists restores them to 1-2-3. Re-verified here: for `sortija de plata`, list A returns exactly those three and ranks them first, while list B places **none of the nine** «Sortija» products in its top six. Without A, the operator's own words have no vote.

| Option | Cost | Why not |
|---|---|---|
| **A + B + C (chosen)** | one extra SQL statement, run in the same round trip as B | — |
| B + C only | simpler | Loses the exact-term rescue that C20 measured and this change re-verified |
| A + C only | simpler | Loses the expansion entirely: `gargantilla dorada` back to 0 documents |
| One list, weighted `tsvector` with `setweight` | none at query time | **Impossible without a migration**: `tsv` is a *generated* column over flat `doc_text` with no field labels; adding weights rewrites every row and rebuilds the GIN — the migration C20 refused in its D10 |

### D2 — OR between groups with coordination ordering, not conjunction

Candidate set: `tsv @@ (g1 || g2 || … || gn)`. Order: `(number of counting groups the document matches) DESC, ts_rank DESC`.

| Option | Real recorded queries answered | Why |
|---|---:|---|
| Strict `&&` (what `measure.py` composes today) | **3 of 10** | The conjunction of individually frequent words matches nothing |
| `&&` with *zero-drop* (dropping groups that match no document) | **4 of 10** | The failing terms **do** match documents — just not together |
| **OR + coordination (chosen)** | **10 of 10** | — |
| Plain OR ordered by `ts_rank` | 10 of 10, worse order | Puts generic rings above the *Anillo de Filigrana* the query named |

Three properties make it the right shape rather than merely the recallful one:

1. **It dominates the conjunction.** Documents matching every group have maximum coordination, so the `&&` result set is literally the head of the OR list. No precision is traded away; only a tail is added.
2. **It absorbs the zero-drop.** A group matching no document adds 0 to *every* document's coordination, so it cannot change the order. The `EXISTS`-per-group machinery the exploration first proposed is unnecessary.
3. **It restores the discriminating term.** `anillo de filigrana tradicional menorquina` under plain `ts_rank` returns six generic rings first and the *Anillo de Filigrana* at 7-8; with coordination they are 1-2.

Being permissive in B is safe **because of D1**: a document matching everything still wins on consensus, since list A never dropped a term.

### D3 — Weighted RRF, and the vector branch weighs less

`score(d) = Σᵢ wᵢ / (k + rankᵢ(d))`, a pure function over lists of identifiers returning the fused order **plus provenance per candidate**.

| Configuration | /120 |
|---|---:|
| Vector only (production today) | 67 |
| `w_vector = 1,0` (branch parity) | **96** |
| `w_vector = 0,5` | 102 |
| **`w_vector = 0,33` (chosen)** | **105** at 200/60 depth, **111** at symmetric 60 |
| Lexical only | 107 |

Parity — which is what the exploration recommended before measuring — is the worst fused configuration, and the cause is structural: **measurement 7 explains measurement 5**. The threshold passes the whole corpus, so the vector branch always returns a full list whether or not it understands the query, and a branch that always fills its list always votes at full strength. `dije de plata` falls from 10 (lexical) to **2** at parity; `gargantilla dorada` from 10 to 5.

`w_A = w_B = 0,5` so the lexical side totals 1,0, and the degradation is exact: with expansion disabled A ≡ B and `0,5/(k+r) + 0,5/(k+r) = 1/(k+r)` — precisely one lexical list at weight 1.

**On S10.** The article warns against weighting **raw scores**, whose distributions shift per query. Weighting **rank reciprocals** is dimensionless and stable: the weight does not calibrate scales, it declares how many votes a branch holds. The distinction belongs in writing because the two look alike.

**Rejected:** hierarchical RRF (fuse A⊕B, then with C) gives the same parity with `k` applied twice and a harder story; score normalisation is the swamp RRF exists to avoid.

### D3b — Symmetric depth, coupled to `k`

All three lists truncate at the same depth, default **60**.

RRF with `k = 60` is very flat: rank 1 scores `1/61`, rank 200 scores `1/260` — **38 %** of the leader's vote. A long list does not amplify its head; it hands positive votes to 140 documents the other branches do not score at all, and that current displaces the documents two branches place well without placing first. Truncating all three at the same point makes membership of some top-N the entry requirement, which is where RRF's consensus premium bites.

| depth | `w_vector=0,33` | `0,5` | `1,0` |
|---:|---:|---:|---:|
| 200 lexical / 60 vector | 105 | 102 | 96 |
| 40 | **113** | 107 | 97 |
| 50 | **113** | 108 | 99 |
| **60 (chosen)** | 111 | 107 | 102 |
| 100 | 107 | 107 | 100 |
| 200 | 107 | 106 | 96 |

Rule: **depth ≈ k**. They are not independent parameters and must not be swept separately. 60 is chosen over the measured argmax of 40-50 because two points on a twelve-query sample is noise, and 60 equals the existing `OVER_RETRIEVAL_CAP` — **one fewer arbitrary constant**. It remains conceptually distinct from the returned over-retrieval window, which depends on `top_k`.

Measurement 7 also makes the vector depth a first-class ranking parameter rather than a safety cap: with the threshold passing the whole corpus, `LIMIT` *is* the cut.

### D4 — Coordination counts only groups whose absence is evidence

| Group resolved to | Corpus coverage | Counts? |
|---|---:|---|
| `piece_type` | 99 % | **yes** — a document without `anillo` is not a ring |
| `materials` | 89 % | **yes** |
| **unresolved** (a literal word the operator typed) | — | **yes** — the Stripe case, and what lifted the *Anillo de Filigrana* |
| `stone_type` | 54 % | **yes**, at the boundary; flagged for C24 |
| `size_label` | 45 % | **no** — owned by the demoting filter (D5). One field, one mechanism |
| `color_tags` | 19 % | **no** |
| `occasion_tags` | 13 % | **no** |
| `style_tags` | 11 % | **no** |

A group that does not count still scores in `ts_rank`; what it loses is the right to jump the queue. Under coordination ordering, matching one more group moves a document ahead of **every** document matching fewer, whatever its `ts_rank`. With `Ocasiones:` present in 150 of 1.168 documents and `boda` matching **5**, those five would outrank 1.163 equally suitable pieces. In a field covered at 99 % absence is evidence; at 13 % it is not. Lexical matching on a sparse field manufactures **false precision**.

Measured: **113/120** excluding occasion and style, **114/120** also excluding colour, against 111 — with **no losses** on any of the twelve.

**The emergent property is the real prize.** When the query is mostly subjective — *«algo elegante para una ceremonia»* — few or no groups count, coordination stops discriminating, the lexical list degenerates to `ts_rank` over a broad OR (a weak signal) and **the vector branch decides by default**. That is S10's dynamic weighting obtained without the magic number S10 warns someone will have to justify, recalibrate and debug. An explicit adaptive weight stays a C24 ablation (`v3-adaptativa`), not C21 scope.

No new analysis code is needed: `ExpandedQuery.matched` already carries `(typed term → vocabulary field → canonical)`, which C20 delivered for exactly this.

The field list is a **constant in code with the measured coverage in its comment**, not configuration: it is a property of the corpus, not of the deployment, and making it configurable would invite editing it without re-measuring.

### D5 — Structural filters demote; only what a human clicked excludes

One sentence: *what a human clicked filters; what a rule inferred from text demotes.*

| Origin | Treatment |
|---|---|
| Body filters (`filters.materials`, `filters.category`, `filters.family_id`, `filters.exclude_product_ids`) | **Hard SQL filter, unchanged.** The operator clicked them in the panel |
| Price ceiling from text (`menos de 80`) | **Demotes** |
| Size from text (`talla M`) | **Demotes** |
| Materials from text | **Demotes.** Never `@>`; never a hard `&&` |
| `piece_type` from text | **Not filtered at all** |

How it demotes, with no magic number: after fusion, a **stable block sort** on `(over_price_ceiling, size_mismatch, material_mismatch, −rrf_score)`. A candidate that breaks a constraint drops behind those that keep it, retains its RRF order inside its block, and **never leaves the over-retrieval window** — so .NET, the authority on real price, still sees it. When C25 arrives with weights calibrated against the golden set, this block sort is the seam it replaces with a score, undoing nothing.

**Why not the ficha's hard filters.** Design §7.6 already forbids a valid product disappearing because of a stale projection; C21 extends that from stock to price and size. The classic reason for hard filters — making everything downstream cheaper — does not apply at 1.168 rows: the filter buys no speed, only the risk S10 names of *«excluding the best candidate with total confidence, and nobody sees the hole it leaves»*. And `@>` is not an alternative semantics but a recall cliff: 60 documents against 913, because 91,6 % of the catalogue carries one material or none.

`piece_type` is not filtered because C20 measured that a lexical hit on the canonical term **equals** filtering by `piece_type` (`anillo` 268 = 268). Adding a `WHERE` would constrain only the vector branch — the one that rescues paraphrase.

### D6 — `websearch_to_tsquery` for the typed list, `plainto_tsquery` per emitted form

| | Operator between lexemes | `aro de dedo` reaches |
|---|---|---:|
| `plainto_tsquery` | `&` | **6** documents |
| `phraseto_tsquery` | `<->` / `<N>` (positional) | **0** documents |
| `websearch_to_tsquery` | `&`, plus `-negation` and `"quoted phrase"` | 6 |

`phraseto` annihilates `aro de dedo`, the overlay entry C20's reach report credits with **+262 documents**. So there is no "when is it multi-word" rule to write: **`plainto` for every emitted surface form, always**. If an emitted form ever proves too loose, the fix is the dictionary entry, not the constructor.

`websearch` for list A gives the operator `"quotes"` and `-negation` for free, and a syntax mistake cannot empty the result because **list B interprets no syntax at all** — at worst A loses a vote.

Terms travel **always as parameters**; no query syntax is ever concatenated. The safe shape is inherited from `retrieval/measure.py`; the only change is `&&` → `||` between groups plus the coordination expression.

### D7 — No exact-match anchor for SKU or name

The ficha asks for a boost. Measured, it buys nothing:

| Query | List A | List B | List C |
|---|---|---|---|
| `anillo Ses Salines plata` | the four, `ts_rank` 0,99 / 0,99 / 0,96 / 0,95 | the same four, coordination 4 | — |
| `pulsera Cala Galdana` | both, 0,92 / 0,70 | the same two, coordination 3 | — |
| **`SKU690`** | **1 document** | **1 document**, the same | **0 documents** |

An exact name already heads **both** lexical lists on its own, so an anchor would be code that never changes an outcome. The SKU case was the real worry — a one-element list contributes `0,5/61 + 0,5/61 = 0,01639` and the vector branch's rank-1 contributes `1,0/61 = 0,01639`, an exact tie — but the vector branch **abstains** on a SKU: everything sits above the threshold. There is nothing to tie against, and `w_vector = 0,33` widens the margin further.

`test_exact_sku_query_ranks_target_first` is kept and **changes nature**: it verifies an emergent property rather than a mechanism. If it ever fails — because the threshold moved, or a weight did — the anchor gets discussed then, with the failure in hand.

### D8 — `mode` becomes honest, and a provider failure degrades instead of 503

| `mode` | Behaviour |
|---|---|
| `hybrid` (what .NET sends) | All three lists. Provider fails **and** lexical has hits → 200, `match_reasons: ["lexical"]`. Provider fails **and** lexical is empty → **503** |
| `lexical` | No provider call at all |
| `vector` | `tsv` is not queried |

A 200 with an empty list would be indistinguishable from a legitimate abstention, and C16's panel paints its *abstained* state on `results.length === 0 && aiAvailable && lowConfidence`: serving a dependency failure behind the "we found nothing" screen is the lie this decision exists to prevent.

Serving lexical-only silently would be the other half of the same lie, which is why the panel's origin badge moves from a single per-response decision (`aiAvailable`) to a per-result one driven by `matchReasons`. That is what C16 wrote into `ORIGIN_LABELS` by hand: *«a lookup rather than a conditional so that a later origin — the lexical branch of C21 — is a new entry here instead of a change to the row»*. No .NET work: `MatchReasons` already travels to the DTO and to `ai-search.types.ts`.

**Rejected:** keeping 503 in hybrid mode and letting .NET's own degraded searcher answer. jbg-ai's lexical branch is strictly better — enriched `doc_text` plus the dictionary against a name/SKU `LIKE` — and §6.4's circuit breaker remains the outer fallback. This is an earlier rung, not a replacement.

### D9 — `low_confidence` becomes absence of cross-branch consensus, as a signal only

Today `low_confidence = (results == 0)`, which measurement 7 shows is nearly dead: the threshold only empties the list for nonsense input. The new meaning — **no candidate appears in more than one branch** — is the exact signature of the measured failure, where the vector says *pulsera* and the lexical says the three *sortijas* with 0/10 overlap. It costs no new constant and reuses the consensus RRF already computes.

**It does not change when results are returned.** Turning it into a real abstention would blank the screen on purely conceptual queries where the lexical branch legitimately matches nothing and the vector branch may well be right. As a signal it costs nothing and hands C24 the branch-disagreement metric with nothing to build. In C16's panel it is invisible while results exist, which is the correct blast radius for a hypothesis.

### D10 — The lexical branch races the provider, not the vector branch

```
count_compatible()
   │
   ├── gather( embed(original text) 170–1707 ms , lexical A+B  <10 ms )
   ├── vector search (only if a vector came back)
   ├── RRF → demoting filters → output over-retrieval window
   └── 200
```

S10 suggests running the branches in parallel. Here that would optimise what costs nothing — on 1.168 rows with a GIN index the lexical branch is noise — while holding **2 of the 5** pool connections per request, against a pool with `max_overflow=0` and a 2 s wait. Racing the lexical query against the *provider* hides it entirely behind the 170-1707 ms round trip and holds **one** connection at any moment.

### D11 — Singleton with a bounded cache, without unfreezing C11

`DEFERRED_TASKS.md` calls this "roughly three lines in `main.py`". It is not. `InMemoryEmbeddingCache` is a `dict` with **no ceiling and no TTL** — harmless per request, since it is born empty and dies with the response, and a lifetime leak as a process singleton keyed by every distinct operator query (~13 KB per vector) inside a container capped at **512 MiB that already uses 232**.

`indexing/embeddings.py` is frozen by C11, and the seam is already there: `LiteLlmEmbeddingClient` takes `cache` as a constructor field. A bounded LRU cache is defined in `retrieval/` and injected when the singleton is built in `main.py`. The frozen file keeps a zero diff.

`AiGateway:RetrievalTimeoutMs` stays at 2500 ms. Reverting it needs a demo deploy, a cold and warm re-measurement and a funnel confirmation — a different kind of work, and its `DEFERRED_TASKS.md` entry stays open with the new figures as the baseline.

### D12 — `score` changes meaning, and it is declared

`score` becomes the RRF score normalised to the first result: still inside `[0,1]` and still monotone with the order, which is what the frozen contract promises. `debug.vector_score` keeps the mapped distance when the vector branch saw the candidate, `debug.lexical_score` carries `ts_rank`.

C04's telemetry persists `score`, so this is stated in the spec and the README: **comparing scores from before and after C21 means nothing**. Keeping the RRF score raw was rejected — values of 0,0001-0,03 would be persisted without meaning and would look like a broken field.

### D13 — One capability, three modules

`hybrid-fusion` is a capability rather than a detail of `vector-retrieval` because C23 (knowledge corpus), C25 (business signals) and C26 (substitutes) will fuse ranked lists **without going through `POST /v1/retrieval/products`**. If the fusion lives inside the endpoint's spec, those three changes must either cite a spec about another endpoint or restate the behaviour. The cost is real and bounded: one more live capability out of 44, and `openspec validate --all --strict` must stay at `0 failed` after the sync.

Three modules and not one: `fusion.py` is pure and domain-free so C23, C25 and C26 can import it; `filters.py` is the seam C25 replaces; `lexical.py` owns the SQL. Merging them would force those changes to import from a module doing three jobs.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| **The rubric is the lexical branch's own objective function.** `doc_text` carries canonical `Tipo:` and `Materiales:` lines and the expansion aims at them; scoring "right type and right material" rewards whoever matches those lines by construction | Stated in the report, the ticket and here. The figures fix a **starting point**, not a verdict; the judge is C24's graded golden set with a paraphrase category. That no fused configuration beats lexical-only *on this rubric* is expected and is not a reason to drop the vector branch, which wins where the rubric cannot look — in `joya con forma de concha marina` the lexical branch buries at 23-24 the *Colgante Caracola Marina* the vector places 1-2 |
| **Recall rises and `ts_rank` orders a large set.** OR plus expansion can produce 200-800 candidates | Coordination puts the conjunction's result at the head, so the ordering that matters is not `ts_rank`'s alone. Depth 60 then discards the tail entirely |
| **`low_confidence` changes meaning and .NET's funnel persists it** (D9) | Signal only, no behaviour change, declared in the spec and the README. C24 decides whether it becomes a real abstention |
| **`score` changes scale and C04 persists it** (D12) | Declared in the spec and the README. Before/after comparisons are meaningless and must not be attempted |
| **The subjective-field list drifts** — someone adds a field without re-measuring coverage | Constant in code with the measured coverage in the comment, plus `test_sparse_vocabulary_fields_do_not_count_towards_coordination`. `stone_type` at 54 % is on the boundary and flagged for C24, because none of the twelve queries isolates it |
| **The singleton cache grows unbounded** — the part `DEFERRED_TASKS.md` did not anticipate (D11) | Bounded LRU injected by constructor, with `test_embedding_cache_is_bounded`, and `test_embeddings_module_is_unchanged` pinning the C11 freeze |
| **Someone raises the vector weight "for symmetry"** | Measured: it costs 9-15 points of 120 and sinks `dije de plata` from 10 to 2. Recorded in D3, in the ticket's risks and in a test that pins the default below the lexical weight |
| **Someone returns to strict `&&` "for precision"** | Measured: it leaves 7 of the 10 real queries mute. Recorded in D2 and pinned by a test |
| **The distance threshold does not discriminate** (measurement 7) and C21 does not fix it | Declared as a limitation. Cutting for real needs a per-query quantile, which C25's ficha already claims. Meanwhile the vector depth is the effective cut and it is configurable |
| **Zone shared with C22 and C25**, all three living in `retrieval/` | The surviving §1 rule: two changes touching the same files are not open at once, even for the same person |
| **Curated against the corpus, not against demand** — 31 telemetry rows, 12 texts, all developer-written | Inherited from C20 and declared in the README beside the golden set's absence of inter-annotator agreement. The default weights are a measured starting point, not a calibration |

## Migration Plan

No migration. No Alembic revision, no EF Core migration, no PostgreSQL extension, no document re-indexed: `doc_text`, `tsv` and `source_hash` are provably identical before and after, and `setweight` is refused precisely because it would require rewriting the generated column (D1).

Deployment is a code deploy plus optional environment variables, all with defaults. **Rollback is `mode`-shaped and configuration-shaped**: setting the vector weight to 0 yields a lexical-only retriever; setting the lexical weights to 0 restores C14's behaviour ordered by RRF over a single list; `JPV_QUERY_EXPANSION_ENABLED=false` still turns off the expansion, which now degrades to list A alone. No data has to be undone.

The frontend change ships in the same deploy. It is inert until the service returns a `match_reasons` other than `["vector"]`, so the two halves are not order-dependent.

## Open Questions

| # | Question | Default applied if unanswered before the apply |
|---|---|---|
| 1 | Names of the fusion settings | `JPV_RRF_K`, `JPV_RRF_WEIGHT_TYPED`, `JPV_RRF_WEIGHT_EXPANDED`, `JPV_RRF_WEIGHT_VECTOR`, `JPV_BRANCH_DEPTH` — one depth for all three lists |
| 2 | Does `stone_type` (54 % coverage) count towards coordination? | **Yes**, provisionally. It sits between the high block (89-99 %) and the sparse one (11-19 %), and none of the twelve queries isolates it. Flagged for C24 |
| 3 | Is the sparse-field list configuration or a code constant? | **Code constant**, with the measured coverage in its comment. It is a property of the corpus, not of the deployment |
| 4 | Does the frontend badge change belong to C21? | **Yes.** Without it the screen says "semantic match" over results the lexical branch alone served — the lie D8 exists to prevent. About five lines and one test |
| 5 | Extend `measure.py` or create an evaluation CLI? | **Extend it.** A new evaluation CLI is C24, and starting it here would duplicate the home of the same kind of report |

Default for any minor detail the apply uncovers: the narrowest option that does **not** regenerate `openapi.json`, touch `backend/`, edit `indexing/embeddings.py` or `enrichment/vocabularies.yaml`, open a migration, introduce a filter that excludes, or bring forward anything from C22, C24 or C25.
