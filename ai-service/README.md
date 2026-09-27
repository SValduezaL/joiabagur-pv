# jbg-ai

Python FastAPI microservice for the JoiaBagur Proyecto Final RAG.

- **C01** (HU-AIENG-001) shipped the runnable skeleton: settings, public health, structured `trace_id` logging, container and Compose wiring.
- **C02** (HU-AIENG-002) freezes the HTTP contract: eight `/v1` endpoints with complete Pydantic models, an internal HS256 service token, deterministic stubs, and a versioned `openapi.json`. **C18a made it nine** — the first and so far only addition since the freeze.
- **C05** (HU-AIENG-005) adds the persistence foundation: `vector` extension, schema `ai`, a dedicated database role, Alembic migrations and six empty index tables with their indexes. No data, no queries — see [Database and migrations](#database-and-migrations).
- **C08** (HU-AIENG-008) **renegotiates the enrichment contract** and opens catalog-wide auth. `POST /v1/enrich/products` now returns `source` (`rule` | `inferred`) on every proposed value, plus `piece_type`, `stone_type`, `size_label`, tags split into `color_tags` / `style_tags` / `occasion_tags`, and `prompt_version` on the response. Without per-field provenance the .NET side cannot tell a value a rule produced from one a model inferred, which is the whole of its hybrid review policy. Catalog-wide routes (`/v1/enrich/*`) authenticate through `get_catalog_principal`, which does **not** require `pos_id`; retrieval, assistance and inventory keep requiring it, and a token without it is still rejected there with 401.
- **C06a** (HU-AIENG-006a) ships the real-catalog corpus **outside this service**: offline scripts in `scripts/catalog/`, JSONL in `data/catalog/real/generated/`. No LLM client, no Alembic `text_provenance`, no writes to `public` from `jbg-ai`.
- **C06b** (HU-AIENG-006b) adds the **CLI** `python -m jbg_ai.data` (`generate` / `ingest`) under `jbg_ai.data`. `api.main` does not import it. Generate reads `JPV_CATALOG_LLM_API_KEY` from `backend/.env` (host only; not the RAG key). `GET /health` does not need it. See [`src/jbg_ai/data/README.md`](src/jbg_ai/data/README.md).
- **C09** (HU-AIENG-009) replaces the enrichment stub when `STUB_MODE=false`: closed vocabularies, size regex on `Name` then `Description` (never SKU), LiteLLM at temperature 0 (`JPV_RAG_LLM_*`), confidence by evidence span, `prompt_version = enrichment/v2` since FIX1 (`enrichment/v1` for the 1.178 profiles C09 produced). Batch quality gates live in an auditor, not as HTTP 422. Compose and the OpenAPI snapshot stay on `STUB_MODE=true` until a RAG key exists. See [`prompts/enrichment/v2.md`](prompts/enrichment/v2.md) and the superseded [`v1.md`](prompts/enrichment/v1.md), kept unmodified.
- **C10** (HU-AIENG-010) adds nested CLI `python -m jbg_ai.data world simulate|ingest` under `jbg_ai.data.world`. Simulate is offline (YAML of 12 POS, no Postgres, no LLM). Ingest uses `JPV_PG*` against local Docker and does not touch `"Products"` / `"Collections"` / schema `ai`. Recipe: [`../data/world/pos-profiles.yaml`](../data/world/pos-profiles.yaml). See [`src/jbg_ai/data/README.md`](src/jbg_ai/data/README.md).
- **C11** (HU-AIENG-011) adds the library `jbg_ai.indexing`: canonical `source-text/v1` (`build_source_text` / `hash_source_text`) and an injectable LiteLLM embedding client (`aembedding`, 1536-d, in-memory cache, batch 64). `api.main` does not import it. `JPV_EMBEDDING_*` are optional at boot; embedding requires its own key and does not fall back to `JPV_RAG_LLM_API_KEY`.
- **C13** (HU-AIENG-013) replaces the `/v1/index/*` stub when `STUB_MODE=false`: catalog feed pull (`X-Index-Feed-Key`, keyset `since`/`since_id`), committed `src/jbg_ai/indexing/sku_provenance.json`, skip-embed upsert, tombstones, checkpoint, CLI `python -m jbg_ai.indexing sync [--full]`. Auth is `get_catalog_principal` (no `pos_id`). The POS feed method exists on the client and is **not** called. `indexing/embeddings.py` is not edited. OpenAPI adds `since_id` / `cursor_id`.
- **C14** (HU-AIENG-014) replaces the `/v1/retrieval/products` stub when `STUB_MODE=false`: query embed with the C11 `LiteLlmEmbeddingClient` (`max_attempts=1`; `indexing/embeddings.py` unchanged), cosine `<=>` over HNSW, distance threshold `JPV_RETRIEVAL_DISTANCE_THRESHOLD` (default 0.65), overfetch after the threshold. `mode=hybrid`/`lexical` run the vector branch until C21. Missing key, `DATABASE_URL` or compatible index → 503, not 501. **Substitutes are real since C26.** OpenAPI snapshot is not regenerated.

- **C18a** (HU-AIENG-018a) adds the library `jbg_ai.families` and the **ninth** `/v1` route, `POST /v1/families/suggest` — the first addition since C02 froze the surface, so `openapi.json` was regenerated in the same change. Grouping is deterministic and offline: no LLM, no embedding provider call, no SQL against schema `public`. The name root groups and the embedding **vetoes**, relative to the other proposed families rather than by any absolute cutoff (`JPV_FAMILY_VETO_MARGIN`), and a vetoed member is **marked for review, never removed**. Vocabularies are reused from `enrichment/vocabularies.yaml`, not redeclared. The route proposes and writes nothing; approving is .NET's, through `ProductFamilyService`.
- **C18b** (HU-AIENG-018b) adds `POST /v1/families/audit`, the **tenth** `/v1` route, and regenerates `openapi.json` in the same change as C18a did for the ninth. It audits the families that **already exist** rather than proposing new ones: it reports members the vectors do not support — a product of another family sits closer than the member's own worst sibling — and, in the same call, unassigned products that look like they belong to one. The two are the same comparison read from opposite sides of the membership line, which is why there is one route and not two. Orphans are nominated by **margin relative to the target family's own cohesion** (`JPV_FAMILY_ORPHAN_MARGIN`), never by an absolute cutoff: measured over the corpus, neighbourhood purity fires overwhelmingly on synthetic near-duplicates built to be distinct families, while relative margin fires almost entirely on real catalogue gaps — so purity is kept as a **ranking signal only**. The relative veto is reused from C18a with a different universe (persisted families instead of proposed ones), not reimplemented. Like every route here it reads **only `ai.product_document`** and never schema `public`, so the memberships it audits are the ones the index projection holds as of the last sync. It writes nothing: the verdict is .NET's, in `FamilyReviewVerdict`.
- **C20** (HU-AIENG-020) adds the library `jbg_ai.retrieval.synonyms`: query-side synonym expansion for the lexical branch C21 will build. Two layers — `enrichment/vocabularies.yaml` supplies the base equivalence classes and is **never modified from here**, because touching it forces a prompt bump and re-enrichment; `retrieval/query_synonyms.yaml` overlays what must not enter the extraction contract. That includes **Spanish stemmer artefacts**, which are first-class content and not a footnote: `collar` and `collares` stem to different lexemes and reach 140 documents against 1, and the stemmer folds acute accents but **not** `ñ`, so `bano de oro` reached 0 against 38. `expand_query` is a **pure function** returning **equivalence groups plus resolved terms** — never a rewritten string, because a single widened `tsquery` was measured to push the three products literally named «Sortija» out of the top ten, while RRF over the original and expanded lists puts them back at 1-2-3. Bridges between vocabularies are **directional**: the colour `dorado` reaches solid `oro`, but a query for `baño de oro` does not, because a symmetric union dragged 282 solid-gold pieces averaging 587 EUR into a query for plating averaging 420 EUR. The flag `JPV_QUERY_EXPANSION_ENABLED` supplies only the default; the value travels by parameter so C24 can sweep configurations in one process. **Observe-only**: a `stage=expand` log is emitted and the result is **not consumed** until C21, which is declared rather than disguised — the response of `POST /v1/retrieval/products` is unchanged. No migration, no new extension, no document re-indexed, `openapi.json` untouched.

- **C21** (HU-AIENG-021) connects the two cables C05 and C20 left stripped: `ai.product_document.tsv` had been populated on every live row since C05 and **nothing queried it**, and C20's expansion was computed, logged and read by nobody. `POST /v1/retrieval/products` now fuses **three ranked lists** — the operator's typed text (`websearch_to_tsquery`), C20's equivalence groups (`plainto_tsquery` per surface form, never `phraseto`: adjacency leaves `aro de dedo` at 0 documents against 6) and the vector branch — with **weighted RRF** (`retrieval/fusion.py`, pure and domain-free so C23, C25 and C26 can import it) at a **symmetric depth** coupled to `k`. Serving from the vector branch alone scored **67 of 120** over twelve operator queries; `dije de plata` scored **0/10**. Four measured decisions govern the shape. Groups are **OR-ed, not conjoined** — strict `&&` leaves 7 of the 10 real recorded queries at zero documents — and ordered by **coordination**, which contains the conjunction's result at the head of the list. Coordination counts **only fields whose absence is evidence**: `occasion_tags` (13 %), `style_tags` (11 %), `color_tags` (19 %) and `size_label` (45 %) score in `ts_rank` but may not jump the queue, which as a side effect leaves a mostly subjective query to the vector branch with no second number to calibrate. The vector list **weighs less** (0.33): branch parity is the worst fusion at 96/120 against 105/120, because the distance threshold passes essentially the whole corpus so that branch always votes at full strength. And structural constraints read from the text — a price ceiling, a size, materials — **demote and never exclude** (`retrieval/filters.py`), because `@>` reaches 60 documents where `&&` reaches 913 and 126 documents carry no extracted materials at all. `mode` stops lying (`lexical` makes no provider call, `vector` does not read `tsv`, the `vector_only_until_c21` note is gone), `match_reasons` reports **real provenance** per result, `low_confidence` becomes the absence of cross-branch consensus **but only when more than one branch ran** (with a single branch no candidate can appear twice, so the rule would mark every response and the field would inform of nothing; there it keeps C14's meaning of "nothing was returned"), a provider failure in `hybrid` degrades to the lexical branch with 200 instead of 503 — and to 503 only when there is nothing lexical to serve, since a 200 with an empty list is indistinguishable from a legitimate abstention. The retrieval embedding client becomes a **process singleton with a bounded LRU cache** injected through C11's existing constructor seam, paying half the debt in `openspec/DEFERRED_TASKS.md` without editing the frozen `indexing/embeddings.py`. `python -m jbg_ai.retrieval compare` writes the arm comparison to `evals/results/`. No migration, no `backend/` change, `openapi.json` untouched.

**Two behaviour changes C21 declares rather than hides.**

1. **`score` changes scale.** It is no longer `clamp(1 − cosine_distance)` but the fused RRF score normalised so the first result is 1.0 — still inside `[0, 1]` and still monotone with the order, which is what the frozen contract promises. The mapped cosine distance moves to `debug.vector_score`, and `debug.lexical_score` now carries `ts_rank`. C04's telemetry persists `score`, so **figures recorded before and after C21 are not comparable** and comparing them means nothing. Keeping the raw RRF score was rejected: values of 0,0001-0,03 persisted without meaning would look like a broken field.
2. **The distance threshold does not discriminate between plausible queries.** Measured on the live index, the cutoff passes **essentially the whole corpus** on an ordinary query and nothing at all on a nonsense control, so it is a floor and the branch depth is what actually bounds the vector list. C21 does not fix it: cutting for real needs a per-query quantile rather than a constant, which is what C25's ficha already claims. It is declared here so nobody reads the threshold as an abstention mechanism.

- **C23** (HU-AIENG-023) builds **the second index**. `ai.product_document` answers «enséñame anillos de plata» and cannot answer «¿este anillo se puede mojar?», because that answer lives in no product. C05 created `ai.knowledge_document` and `ai.knowledge_chunk` with their final shape and **nothing had ever written to them**; this change adds the content and the round trip to it. A corpus of **32 Markdown documents and 161 sections** in [`../data/knowledge/`](../data/knowledge/), one material sheet per canonical term of the enrichment vocabulary — a **derived, testable** invariant, so adding `titanio` to the vocabulary without its sheet fails a test. Every section declares its **`claim_scope`**, `general` (verifiable outside the jewellery) or `establecimiento` (a commitment of the house, **today illustrative**), and that mark travels with the retrieved fragment: a **minority** of the sections, the count sealed in `_corpus.meta.json` and reprinted by `python -m jbg_ai.knowledge stats`, are commitments, and the whole service block is one. **Zero `guion_venta` documents**, of the five the schema admits, and that is not a scope cut: an imperative fragment retrieved into a prompt is indistinguishable from an instruction, so the corpus would become an injection surface — the corpus keeps **facts to cite**, the prompt keeps **instructions to obey**. Chunking is one `##` section per chunk, no overlap, with both titles inside the indexed content, which is what tells nine structurally identical material sheets apart and comes free because `tsv` is a column generated over `content`. Identity is `uuid5` over the slugs and **never `(document_id, chunk_index)`**: inserting a section in the middle would shift every later index and silently repoint every later citation. The `citation_id` — `material-plata#cuidados-y-limpieza-en-casa` — resolves, **locates and opens the file and the heading in git**. Indexing is idempotent, skips embedding when the content hash and the version match, deletes what a run no longer produces, reuses the frozen `indexing/embeddings.py` untouched and writes a **version namespace of its own**, `knowledge/v1`: sharing `source-text/v1` would mean a change to the chunking rules invalidated nothing and left vectors declaring themselves current over text that no longer exists. Search is a **callable, not a route** — vector plus lexical fused by RRF through C21's module, with C20's expansion groups feeding the lexical branch — and the vector branch decides **whether there is an answer at all**: below `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` it returns **nothing**, so C30 has nothing with which to invent an attribution. Both decisions were measured, not assumed — figures of the run of **2026-09-06**, reprintable with `python -m jbg_ai.knowledge measure --compare` and recorded in the C23 implementation report: over 32 fixture questions plus 5 out-of-domain ones the fused configuration beats vector-only by **+6,2 pp of Recall@3 and +0,042 of MRR**, and the threshold is calibrated at **0,51** against the production embedder on the live index — the questions with an answer reach at worst 0,5062 and the out-of-domain ones start at 0,5145, a clean gap, so the strictest value that loses none of the former is the one that abstains on all of the latter. `python -m jbg_ai.indexing sync-knowledge`. **No migration, no route, `openapi.json` byte-identical.**

Boundary rule: *Python computes similarity and writes prose; .NET computes numbers and decides.* The service never emits a price or stock figure and never touches schema `public`.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker / Docker Compose (optional, for the full local stack)

## Required environment

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `APP_ENV` | yes | — | e.g. `local`, `dev`, `prod` |
| `SERVICE_VERSION` | yes | — | echoed by `GET /health` |
| `JWT_SECRET` | yes | — | HS256 secret shared with the .NET API; ≥ 32 bytes |
| `LOG_LEVEL` | no | `INFO` | standard Python logging level |
| `JWT_TTL_SECONDS` | no | `300` | documented TTL; the .NET API is the issuer |
| `STUB_MODE` | no | `true` | serve deterministic fixtures instead of real logic |
| `ENABLE_DEV_ENDPOINTS` | no | `true` unless `APP_ENV` is `prod`/`production` | mounts `GET /v1/evals/runs` |
| `DATABASE_URL` | no | — | `postgresql+psycopg://…`; its absence does not stop the service booting |
| `DB_POOL_SIZE` | no | `5` | hard ceiling on simultaneous connections; no overflow |
| `JPV_CATALOG_LLM_API_KEY` | no | — | C06b `generate` only (host `backend/.env`). Distinct from `JPV_RAG_LLM_API_KEY`. Absence does not block `/health` |
| `JPV_CATALOG_LLM_MODEL` | no | — | optional; CLI default `gpt-4o` |
| `JPV_CATALOG_LLM_BASE_URL` | no | — | optional OpenAI-compatible proxy; empty = api.openai.com |
| `JPV_PG*` | no | — | Host CLI ingest only (C06b catalog, C10 world). `backend/.env`, port 5433. Absence does not block `/health` |
| `JPV_RAG_LLM_API_KEY` | no | — | C09 runtime enrichment, and the **fallback** for the C30b sale argument when `JPV_ASSIST_LLM_API_KEY` is absent (LiteLLM). Distinct from `JPV_CATALOG_LLM_API_KEY`. Absence does not block `/health`; real enrich requires it, and `/v1/assist/sale` **degrades to C30a's response with 200** rather than refusing. `JPV_RAG_LLM_MODEL` is C09's model and is **not** read by the assistance layer, whose model is a constant of the module: inheriting it would move the model of a counter-side call whose cost and rejection rate were measured on another |
| `JPV_RAG_LLM_MODEL` | no | — | provider-prefixed id (e.g. `openai/gpt-4o`) |
| `JPV_RAG_LLM_BASE_URL` | no | — | optional LiteLLM `api_base`; empty = provider default |
| `JPV_RAG_LLM_CONCURRENCY` | no | `8` | in-flight enrichment calls inside a batch of ≤ 50 |
| `JPV_EMBEDDING_API_KEY` | no | — | C11 embeddings (LiteLLM). Distinct from `JPV_RAG_LLM_API_KEY`. Absence does not block `/health`; real `embed` requires it |
| `JPV_EMBEDDING_MODEL` | no | `openai/text-embedding-3-small` in code | provider-prefixed embedding model id |
| `JPV_EMBEDDING_BASE_URL` | no | — | optional LiteLLM `api_base`; empty = provider default |
| `JPV_EMBEDDING_BATCH_SIZE` | no | `64` | texts per provider embedding call |
| `JPV_INDEX_FEED_BASE_URL` | no | — | C13 catalog feed origin. Distinct from `JWT_SECRET`. Absence does not block `/health`; real sync requires it |
| `JPV_INDEX_FEED_API_KEY` | no | — | C13 `X-Index-Feed-Key`. Distinct from `JWT_SECRET` and `JPV_EMBEDDING_*`. Never falls back to `JWT_SECRET` |
| `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` | no | `180` | wall-clock budget for one catalog drain; blank → the default |
| `JPV_ASSIST_LLM_API_KEY` | no | — | C30b credential for the sale argument. **Optional, and it falls back to `JPV_RAG_LLM_API_KEY`** — requiring it would stop an existing deployment generating the day it appeared, and silently, because the route degrades to **200 without prose** rather than failing. Set it to bill, rate-limit and rotate counter-side generation apart from C09's batch enrichment: the two calls have different shapes, one with nobody waiting and one with a customer in front of it. Which credential was resolved is logged once as `stage=assist_client credential=assist\|rag_fallback`, so a deployment can check that it really separated them instead of assuming it |
| `JPV_ASSIST_LLM_MODEL` | no | `openai/gpt-4o-mini` | C30b model that writes the sale argument. Its **own** variable and never `JPV_RAG_LLM_MODEL`: that one is C09's enrichment model — `gpt-4o` here — and inheriting it would let a change to enrichment move a counter-side model whose cost, latency and rejection rate were measured on another. The default is the model **every C30b figure was measured on**. It must support structured output; one that does not degrades to the structured response and records the cause |
| `JPV_ASSIST_PITCH_TIMEOUT_SECONDS` | no | `4` | C30b seconds **one generation call** of `/v1/assist/sale` may take — per call, not per request: the ceiling is two calls. Supplies only the **default**; the value travels by parameter. Exceeding it degrades to the structured response with **200**. Opened at 3 s as a product judgement with no measurement behind it; the C30b sweep took one over 175 real calls — p50 2.216 ms, **p95 2.863 ms**, 4,6 % over three seconds and 0,6 % over four — so 3 s sat at 1,05 × p95 and cut jitter rather than slow generations. That latency is an upper bound taken on a developer machine through a TLS interceptor: measure your own and set it here |
| `JPV_ROUTER_LLM_API_KEY` | no | — | C31 credential for the **intent classifier**. Optional, and it falls back in a chain: **router → `JPV_ASSIST_LLM_API_KEY` → `JPV_RAG_LLM_API_KEY`**. With none of the three the classifier is **not constructed**, `intent` returns `unclassified` and the route serves exactly C30b's response — the *fail-open*, the ablation and the rollback in one. Which link is in force is logged once as `stage=router_client credential=router\|assist_fallback\|rag_fallback`; its absence says no client was built |
| `JPV_ROUTER_LLM_MODEL` | no | `openai/gpt-4o` | C31 model that classifies the query. Its **own** variable and never `JPV_ASSIST_LLM_MODEL` nor `JPV_RAG_LLM_MODEL`: ~30 output tokens against a paragraph is not the same call, and sharing one would make any cost comparison false. **The default was moved by the measurement, not chosen:** over the 119 cases of `evals/routing/cases.yaml`, same prompt `router/v3` and temperature zero, `gpt-4o-mini` silenced **3** answerable queries (false positive 6,25 %, `catalog` 81,3 %) and the veto of D12 **rejected** it, while `gpt-4o` silenced **0** (false positive 0,00 %, `catalog` 48/48) and **passed**. A deployment pointing this at `gpt-4o-mini` is serving a configuration the veto rejected |
| `JPV_ROUTER_TIMEOUT_SECONDS` | no | `2` | C31 seconds the **single** classifier call may take. **Declared NOT calibrated**: a product judgement with no latency measurement behind it, in the position C30b's three seconds occupied before its sweep moved it to four — and a harder cut, because this one runs **in front of everything**. Supplies only the default; the value travels by parameter. Exceeding it is a *fail-open*: the request proceeds unclassified. Deliberately left out of the deployment steps until the deployment measures its own distribution |
| `JPV_AGENT_LLM_API_KEY` | no | — | C32b credential for the **agent loop** of `POST /v1/assist/agent`. Optional, and it falls back in a chain: **agent → `JPV_ASSIST_LLM_API_KEY` → `JPV_RAG_LLM_API_KEY`**; the classifier's key is deliberately **not** a link. With none of the three the loop is **not constructed** and the route answers without running it — `stop_reason=sin_cliente`, `partial: true`, **200 and never 503**. Which link is in force is logged once as `stage=agent_client credential=agent\|assist_fallback\|rag_fallback` |
| `JPV_AGENT_LLM_MODEL` | no | `openai/gpt-4o` | C32b model that runs the loop; it must support function calling. Its **own** variable and never the argument's nor the classifier's. The provider pass measured `gpt-4o-mini` exhausting a budget on **66 %** of requests against 1,2 %: pointing it there is cheaper and **does not hold tool selection** |
| `JPV_AGENT_TIMEOUT_SECONDS` | no | `8` | C32b seconds **one turn** of the loop may take (`> 0`, `≤ 60`); per turn, never per request. **Declared NOT calibrated.** A turn is also cut by what is left of the request's 15 s deadline minus the argument's reserve |
| `JPV_RETRIEVAL_DISTANCE_THRESHOLD` | no | `0.65` | C14 cosine-distance cutoff `(0, 2]`. Absence does not block `/health`; blank → the default. Distinct from `JPV_EMBEDDING_*` |
| `JPV_QUERY_EXPANSION_ENABLED` | no | `true` | C20 query-side synonym expansion. Supplies only the **default**: the effective value travels as a parameter of the retrieval orchestration call, so C24 can sweep configurations in one process without restarting and without moving the frozen `openapi.json`. Default on because, measured on the live index, the lexical branch answers **nothing at all** without it for ordinary surface-form variants of catalogue vocabulary. Turning it off is also the rollback for C20. Absence does not block `/health`, which never loads the dictionary |
| `JPV_RRF_K` | no | `60` | C21 smoothing constant of the reciprocal rank fusion; blank → the default. **Not independent of `JPV_BRANCH_DEPTH`**: `k` governs how slowly a document's vote decays as its rank grows, so a deeper branch keeps more of its tail voting and the two are swept together, never separately. Absence does not block `/health` |
| `JPV_BRANCH_DEPTH` | no | `60` | C21 depth at which **every** fused list is truncated before fusing; blank → the default. One value shared by all three: cutting the lexical branches deeper than the vector one was measured to cost accuracy rather than buy it. Conceptually distinct from the over-retrieval window the endpoint returns, which follows `top_k`, even where the two happen to share a default |
| `JPV_POS_PREFILTER_ENABLED` | no | `true` | C22 point-of-sale prefilter. Supplies only the **default**: the effective value travels as a parameter of the orchestration call, so C24 can sweep configurations in one process. Default on because, probed against the live index, **most** points of sale were left with a very short result page on a large share of ordinary searches once .NET had dropped what they do not carry — worst case **one** surviving product, and one query with **none**. Figures in the C22 report. Turning it off is the rollback for C22: retrieval returns to pre-change behaviour with no deploy, and `ai.pos_projection` can stay populated because nothing else reads it. Absence does not block `/health` |
| `JPV_POS_PROJECTION_MAX_AGE_SECONDS` | no | `3600` | C22 staleness ceiling of the projection. Above it the scope is **not** applied for that request, the degradation is logged and `projection_age_seconds` still reports the age: a stale projection may leave the page short, but it must never hide a valid product from the .NET authority that hydrates it. Deliberately generous — the sync cadence is a cron, so an hour degrades only under sustained failure and not under ordinary lateness; degrading eagerly would surrender the whole benefit of the change on any transient. Measured from `ai.sync_checkpoint.last_incremental_sync_at`, **never** from `ai.pos_projection.refreshed_at`, which records when an assignment last changed — the feed is incremental, so that column would report months on a projection synchronised seconds ago |
| `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` | no | `0.51` | C23 cosine-distance cutoff of the knowledge corpus `(0, 2]`; blank → the default. **Separate from `JPV_RETRIEVAL_DISTANCE_THRESHOLD` on purpose**: that one was calibrated over much shorter product documents, and knowledge chunks are longer prose with another distance distribution. Below it the search returns **nothing** — for a question the corpus does not cover the correct answer is no citation, and C30 depends on that to have nothing with which to invent an attribution. **Calibrated, not chosen**, by a rule that outlives any one measurement: zero out-of-domain citations is a **constraint** and not a term to trade against recall; inside that band Recall@3 is maximised; and among the values that tie the **strictest** wins, which is the word the rule itself uses — being generous "to be safe" buys no recall at all and costs abstention. Re-run the sweep with `python -m jbg_ai.knowledge calibrate`; the figures of the last one are in the C23 implementation report. That sweep runs against the **offline stand-in embedder** the specification requires, so what it calibrates is the **rule**. The default here is what the same rule yields against the **production embedder on the live index**, and it is a different number rather than a rounding of it: the stand-in scores lexical overlap, its distances sit on another scale, and its own optimum lets through questions the corpus does not cover. Re-derive it against a populated index whenever the corpus, the chunking rules or the embedding model change. Supplies only the **default**: the effective value travels as a parameter of the call |
| `JPV_KNOWLEDGE_HYBRID_ENABLED` | no | `true` | C23 lexical branch of the knowledge search; blank → the default. Default on because it was **measured and not assumed**: over the fixture the fused configuration beats vector-only on **both** Recall@3 and MRR at no cost in abstention, and `python -m jbg_ai.knowledge measure --compare` reprints that comparison on demand. The branch exists for a reason specific to this corpus — nine material sheets are structurally identical, same skeleton, same register, same vocabulary, and the only thing telling them apart is the material's name, a short lexical token drowned in shared prose, so cosine collapses by homogeneity. The flag is what let that prediction be confirmed with a number instead of asserted, in the same pattern as `JPV_QUERY_EXPANSION_ENABLED`; turning it off degrades knowledge search to pure vector retrieval and is the rollback for the hybrid half of C23. Supplies only the **default**: the effective value travels as a parameter of the call |
| `JPV_FAMILY_VETO_MARGIN` | no | `0.05` | C18a relative-veto margin `[0, 1]`. **Never an absolute similarity cutoff**: a member is flagged for review, never removed, when a product of another proposed family beats its worst sibling by more than this. Absence does not block `/health` |
| `JPV_FAMILY_ORPHAN_MARGIN` | no | `0.0` | C18b orphan-nomination margin `[0, 1]`. An unassigned product is nominated when it beats the target family's **worst member** by more than this. Deliberately generous at `0.0`: it nominates, a person decides, and measured over the corpus it yields a queue one reviewer works through in a session. **Not a similarity cutoff** — the comparison is always against that family's own cohesion, so the same value behaves differently against a tight family and a broad one. Absence does not block `/health` |

Missing or blank `APP_ENV`, `SERVICE_VERSION` or `JWT_SECRET` aborts startup (fail-fast), so the process never serves `/v1` half-configured.

The **C20 synonym dictionary is curated against the corpus, not against observed demand**: `public."ProductSearchEvents"` holds 31 rows and 12 distinct texts, all written by the developer in canonical vocabulary, so there is no query distribution to draw on. Its reach is measured instead — `python -m jbg_ai.retrieval measure` writes `ai-service/evals/results/c20-query-expansion-reach.md` — and C24 re-measures it with graded relevance. This is a limitation of the same family as the golden set's absence of inter-annotator agreement, and is stated rather than mitigated.

`DATABASE_URL` is **optional on purpose**. The service must boot with no database — that is a requirement of `ai-service-dev-compose`, not an accident — so the engine is built on first use and never at import time. Under `STUB_MODE` nothing asks for a session, so the container starts fine against a database that has not even been provisioned. LLM keys are not required to boot `/health`; the catalog CLI reads `JPV_CATALOG_LLM_*` from `backend/.env`. **`python -m jbg_ai.indexing sync` reads that same file**, through `run_module` in `indexing/cli.py`: `backend/.env` is the single place the local credentials live and the one Compose interpolates, so no symlink and no `env_file:` are needed — the compose file rejects the latter on purpose, to keep host-only CLI keys out of the runtime process. The load happens in `run_module` and **not** in `main`, because tests call `main` directly and `support.settings.build_settings` pins the optional fields to `None` precisely so an exported credential cannot make an "absent configuration" case stop failing. That file carries credentials only: the three fail-fast settings of C02 — `APP_ENV`, `SERVICE_VERSION`, `JWT_SECRET` — still have to reach the process some other way, which is why the host invocation is a development aid and the container is the normal path. Real `POST /v1/enrich/products` (`STUB_MODE=false`) requires `JPV_RAG_LLM_API_KEY` and fails explicitly if it is missing — it does not invent profiles and does not return 501. Embedding (`jbg_ai.indexing`) requires `JPV_EMBEDDING_API_KEY` at call time and does not fall back to the RAG LLM key. Real `POST /v1/index/sync` requires `JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY` and `JPV_EMBEDDING_API_KEY` (and the committed `sku_provenance.json`) and answers **503** naming the missing setting — never 501, and never `JWT_SECRET` as the feed key. Real `POST /v1/retrieval/products` requires `JPV_EMBEDDING_API_KEY` and `DATABASE_URL` (and a compatible index) and answers **503** naming the missing dependency — never 501, and never 200 with `low_confidence` for an empty compatible index. Real `POST /v1/families/suggest` requires `DATABASE_URL` and answers **503** naming it — it needs no provider key at all, because it reads vectors the index already holds and never embeds anything. `POST /v1/families/audit` behaves identically and for the same reason.

## Frozen endpoints (C02)

| Method | Path | Auth | Notes |
|---|---|---|---|
| `GET` | `/health` | public | unchanged since C01 |
| `POST` | `/v1/retrieval/products` | Bearer | returns `min(top_k × 3, 60)` candidates, reported in `candidates_returned` |
| `POST` | `/v1/retrieval/substitutes` | Bearer | retrieval result shape plus `similarity_signals` |
| `POST` | `/v1/assist/sale` | Bearer | `groups[]` by **nullable** `family_id`, rule warnings as codes, citations that resolve. Real since C30a; **writes the argument since C30b** in the two piece-anchored modes, always keeping `{{price}}` / `{{stock}}` unresolved. With **neither** `JPV_ASSIST_LLM_API_KEY` **nor** its fallback `JPV_RAG_LLM_API_KEY` it serves C30a's response with 200, never 503 |
| `POST` | `/v1/assist/agent` | Bearer | **C32b**: the agent loop over a multi-turn transcript carried in the request (≤ 12 turns, ≤ 500 characters each, ≤ 4.000 in total). Every field of the deterministic response **plus** `partial`, `stop_reason`, `iterations`, `tool_calls_used`, a bounded `trace` and `agent_prompt_version`, with `usage.calls`. With no agent credential it answers without the loop, with 200. **C42** gave the route its first consumer (`POST /api/ai/search/agent` on the .NET side) and moved three things with it: each group carries `origin` (`catalogo` \| `sustitutos`) on `AgentAssistGroup`, a **subclass** — the shared `AssistGroup` is deliberately **not** widened, by the precedent of `AgentUsage`, so no other assist route sees a new field, and the value is read from the very same key the payload group is built from rather than re-derived; the route accepts a token with **no `pos_id`** (`get_unscoped_principal`), which is the «every shop» scope, so without a shop the quantity and stock flag travel null instead of zero; and the argument is now written with `assist/v6`, whose agent task adds the rule the anchored ones already had — with no anchored piece there is nothing for a `{{price}}`/`{{stock}}` marker to resolve against, so it must not write one, while comparative language is still allowed. Only `AGENT_PITCH_PROMPT_VERSION` moves: `PROMPT_VERSION` stays on `assist/v5` and neither `v4` nor `v5` was touched |
| `POST` | `/v1/inventory/propose` | Bearer | prioritized proposals, never quantities |
| `POST` | `/v1/enrich/products` | Bearer | proposed profiles with per-field confidence |
| `POST` | `/v1/families/suggest` | Bearer (catalog) | family proposals plus the groups a guard refused and the products the gate excluded; writes nothing |
| `POST` | `/v1/families/audit` | Bearer (catalog) | unsupported memberships and orphan candidates over the families that already exist; writes nothing |
| `POST` | `/v1/index/sync` | Bearer (catalog) | keyset `since` / `since_id`; `batch_size` ignored |
| `GET` | `/v1/index/status` | Bearer (catalog) | set-hash drift vs one catalog GET |
| `GET` | `/v1/evals/runs` | Bearer | **development profile only** |

None of these is exposed through nginx: the SPA never talks to Python.

## Internal service token

The .NET API (C03) is the only issuer. Tokens are HS256, signed with `JWT_SECRET`, and must carry all four claims — names are frozen in `snake_case` on the wire:

| Claim | Meaning |
|---|---|
| `user_id` | acting user on the .NET side |
| `role` | `Admin` or `Operator` |
| `pos_id` | point-of-sale scope |
| `trace_id` | correlation id, preferred over the `X-Trace-Id` header |

Rules that C03 must rely on:

- **The token wins.** `pos_id` and `role` always come from the token. Requests may carry `pos_id` in the body for client compatibility; it is ignored, and a mismatch is neither an error nor a behavior change. Scoped responses echo the applied scope in `effective_pos_id`.
- Any missing, malformed, wrongly signed, expired or incomplete token gets a single opaque **401** that never says which check failed.
- `GET /health` is exempt.

## Stubs and 501

With `STUB_MODE=true` (the local and test default) every `/v1` route answers from deterministic fixtures: no LLM, no embeddings, no database, no clock. The same request always returns the same body, so the .NET client can assert its mapping against them.

With `STUB_MODE=false` a route whose real logic does not exist yet answers **501** naming the change that will deliver it. **Exactly one route is still in that state: `/v1/inventory/propose` (C35).** `POST /v1/enrich/products` is C09: the real pipeline, or 503 if `JPV_RAG_LLM_API_KEY` is missing — never 501. `POST /v1/index/sync` and `GET /v1/index/status` are C13: the catalog drain, or 503 if feed/embed settings or `sku_provenance.json` are missing — never 501. `POST /v1/retrieval/products` is C14: the vector retriever, or 503 if `JPV_EMBEDDING_API_KEY`, `DATABASE_URL` or a compatible index is missing — never 501. `POST /v1/retrieval/substitutes` is C26: the substitutes engine over the stored embedding, or 503 if `DATABASE_URL` is missing — never 501, and **never a provider key**, because that route embeds nothing. `POST /v1/assist/sale` is **C30a and C30b**: the structured assistance layer, or 503 if `JPV_EMBEDDING_API_KEY` or `DATABASE_URL` is missing — never 501, and 422 when the body anchors a piece the index cannot serve. **The generation credential is the exception to that pattern and deliberately so**: with neither `JPV_ASSIST_LLM_API_KEY` nor its fallback `JPV_RAG_LLM_API_KEY` the route answers **200 with C30a's response** rather than 503, because the half that matters is already computed and correct, and a provider that is configured and then fails degrades the same way. With one of them set, `/v1/inventory/propose` is the **only** route left answering 501, and it is not pending work: its branch was cancelled on 2026-08-31 and that is declared as a limitation. Later changes replace remaining handlers one at a time; the contract frozen here is the one they must respect.

## Enrichment prompt versions

**The catalogue holds more than one.** `PROMPT_VERSION` in `enrichment/constants.py` names the
prompt in force, and `load_prompt()` derives its path from that constant — `prompts/<version>.md` —
so the two cannot drift and stamp a profile with a version that never produced it. Superseded
prompt files stay in the repository unmodified, because the profiles produced by them keep
declaring their version and that claim has to stay checkable.

Since FIX1 the corpus is mixed: **22 profiles on `enrichment/v2`** (the enumerated cohort of
`fix-enrichment-vocabulary-gaps`, whose `piece_type` the eight-term vocabulary could not name)
and **1.178 on `enrichment/v1`**.

**Consequence, and it is not optional: any aggregate metric over extracted attributes must be
reported per `PromptVersion`.** Coverage of `piece_type`, distribution of `materials`, share of
empty `style_tags` — an average across both populations is a number without a subject. This is the
same discipline C24 applies to `data_origin`, and the field exists precisely to make the difference
visible. Mixing `PromptVersion` is safe and traceable; mixing `embedding_version` is not, because
that compares two geometric spaces and returns a plausible number with no meaning.

## OpenAPI snapshot

`ai-service/openapi.json` is the published contract, and `test_openapi_snapshot_is_stable` fails whenever the live schema drifts from it. `docs_url` stays disabled: the artifact is the snapshot, not a browsable UI.

**Canonical profile.** The snapshot is generated with `canonical_openapi_settings()` — `APP_ENV=local`, `SERVICE_VERSION=0.1.0`, stubs on and development endpoints **enabled**, so `/v1/evals/runs` is part of the published contract. A production deployment would not serve that path; that asymmetry is deliberate. Pinning one profile in code is what keeps the snapshot deterministic and stops the test and the regeneration below from using different settings.

**Regenerating is a contract negotiation, not a chore.** A failing snapshot test means the frozen boundary moved — agree the change with whoever owns the .NET client before regenerating:

```bash
cd ai-service
uv run python -c "import json; from pathlib import Path; from jbg_ai.api.main import create_app; from jbg_ai.config import canonical_openapi_settings; Path('openapi.json').write_text(json.dumps(create_app(canonical_openapi_settings()).openapi(), indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')"
```

On PowerShell, wrap the same one-liner in single quotes:

```powershell
cd ai-service
uv run python -c 'import json; from pathlib import Path; from jbg_ai.api.main import create_app; from jbg_ai.config import canonical_openapi_settings; Path("openapi.json").write_text(json.dumps(create_app(canonical_openapi_settings()).openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")'
```

## Run locally with uv

```bash
cd ai-service
uv sync --system-certs   # use --system-certs only if TLS to PyPI fails
export APP_ENV=local
export SERVICE_VERSION=0.1.0
export JWT_SECRET=local-dev-jwt-secret-0123456789abcdef
uv run uvicorn jbg_ai.api.main:create_app --factory --host 127.0.0.1 --port 8000
```

On PowerShell:

```powershell
cd ai-service
uv sync --system-certs
$env:APP_ENV = "local"
$env:SERVICE_VERSION = "0.1.0"
$env:JWT_SECRET = "local-dev-jwt-secret-0123456789abcdef"
uv run uvicorn jbg_ai.api.main:create_app --factory --host 127.0.0.1 --port 8000
```

Smoke checks:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/v1/retrieval/products \
  -H "Content-Type: application/json" -d '{"query":"anillo","top_k":5}'
```

Health returns HTTP 200 with `{"status":"OK","version":"0.1.0"}`. The `/v1` call returns **401** without a token — that is the expected answer. To exercise it, sign a token with the same secret and the four claims, then send `Authorization: Bearer <token>`.

### Running against a real database on Windows: two traps

Both are development-machine problems. In production the service runs in a Linux container and neither exists — which is exactly why they are worth writing down: nothing in CI will ever reproduce them for you.

**Uvicorn installs the `ProactorEventLoop`, and psycopg cannot use it.** Every query fails with `Psycopg cannot use the 'ProactorEventLoop' to run in async mode`, and `GET /health` reports `"database": "unavailable"` with no other hint. Setting the policy before calling `uvicorn.run` does not help — uvicorn installs its own. The service has to be started with uvicorn not managing the loop:

```python
import asyncio, sys, uvicorn
from jbg_ai.api.main import create_app

async def main() -> None:
    config = uvicorn.Config(create_app(), host="127.0.0.1", port=8001, loop="none")
    await uvicorn.Server(config).serve()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
```

**LiteLLM verifies TLS against `certifi`, not the operating system store.** Behind a corporate proxy with its own root CA the embedding calls fail, and the symptom misleads: `curl` with the same key returns **200** while Python returns `CERTIFICATE_VERIFY_FAILED`. The indexer records it as `OpenAIException - Connection error` in `ai.sync_failure`, which names neither TLS nor certificates. This is the runtime sibling of the `--system-certs` flag above, and it needs its own fix — export the Windows root store, concatenate it with `certifi.where()`, and point `SSL_CERT_FILE` at the result.

## Run with Docker Compose

From `backend/`:

```bash
docker compose up --build jbg-ai
```

```bash
curl http://127.0.0.1:8001/health
```

The Compose service supplies `JWT_SECRET` and `STUB_MODE` so the container boots with no extra setup. That secret is a **local placeholder**: production takes it from SSM `/jpv/prod/*` in C17 and must never reuse it. `jbg-ai` joins `jpv-network` and opens no database connection.

### Postgres image (pgvector) — volume recreate

Compose Postgres uses `pgvector/pgvector:pg15` instead of `postgres:15`. After pulling the new image, if the existing `postgres_data` volume was created with the old image, recreate it:

```bash
cd backend
docker compose down -v
docker compose up -d postgres
```

`-v` deletes local volume data. Acceptable in O0 when there is no real catalog. Bringing Compose up does **not** create schema `ai` or run `CREATE EXTENSION vector` — that is the one-off provisioning below.

## Database and migrations

Schema `ai` belongs to `jbg-ai`; schema `public` belongs to the .NET API. **Python never writes to `public` and never reads it by SQL** — it reads the business side over HTTP through the paginated feeds. That boundary is enforced by database grants, not by convention: the `jbg_ai` role gets `permission denied` on `public`.

### 1. Provision once, with administrator privileges

`migrations/bootstrap.sql` installs the extension, creates schema `ai`, creates the dedicated role and grants it the minimum it needs. It is **not** an Alembic migration, and deliberately so: roles are cluster-level objects, so creating one from a migration would demand role-creation privilege from whoever migrates and would make a clean revert impossible.

```bash
cd ai-service
docker exec -i jpv-pv-postgres psql -U postgres -d joiabagur_pv \
  -v ai_password=local-dev-ai-password < migrations/bootstrap.sql
```

Pass the password **raw, without quoting it yourself**: psql's `:'var'` already renders it as a quoted literal, so pre-quoting creates a password that literally contains apostrophes and then fails to authenticate.

Re-running it is safe: the extension and schema are `IF NOT EXISTS`, and an existing role keeps its password — so the script can never silently rotate a production credential. Change one deliberately with `ALTER ROLE jbg_ai PASSWORD '...'`.

In production this step belongs to **C17**, run by the RDS master user. Because the migration also declares the extension idempotently, the same `DATABASE_URL` works in both worlds — locally the extension gets installed, on RDS the migration finds it already there. No second admin connection string is needed.

### 2. Migrate

```bash
cd ai-service
export DATABASE_URL="postgresql+psycopg://jbg_ai:local-dev-ai-password@localhost:5433/joiabagur_pv"
uv run alembic upgrade head
```

```powershell
cd ai-service
$env:DATABASE_URL = "postgresql+psycopg://jbg_ai:local-dev-ai-password@localhost:5433/joiabagur_pv"
uv run alembic upgrade head
```

`alembic downgrade base` reverts it. The revert drops the six tables and **keeps** schema `ai` and the extension: the extension is shared database-wide, and the schema holds Alembic's own version table.

Two details worth knowing before editing anything here:

- **The version table lives in `ai`**, not in `public`. Alembic's default would break the ownership boundary in the project's first Python migration, silently.
- **The schema is provisioned in `env.py`, not in the first revision.** Alembic materialises its version table *before* running any revision, so a `CREATE SCHEMA` inside `upgrade()` would arrive after the failure it was meant to prevent.

### One driver, two callers

`postgresql+psycopg://` is psycopg 3, which speaks sync for Alembic and async for FastAPI, so a single connection string serves both. Choosing `asyncpg` would have meant two URL forms and someone remembering to translate between them in every environment.

> **Windows caveat.** psycopg's async mode does not work with `ProactorEventLoop`, Python's default event loop on Windows; it needs `WindowsSelectorEventLoopPolicy`. This does not affect production (Linux container) or the test suite (Alembic is sync), only running the app with uvicorn directly on a Windows host once a route actually touches the database.

## Synchronising the POS availability projection

`ai.pos_projection` is what scopes retrieval to the assortment of one point of sale. It is
filled by a command, not by a route and not by a background task:

```bash
uv run --system-certs python -m jbg_ai.indexing sync-pos          # incremental
uv run --system-certs python -m jbg_ai.indexing sync-pos --full   # ignore the cursor
```

Like `sync`, it loads `backend/.env` through `run_module` and needs
`JPV_INDEX_FEED_BASE_URL` and `JPV_INDEX_FEED_API_KEY`. It needs **no** embedding key: it
embeds nothing. It prints one line of counters — `upserted`, `soft_deleted`, `pages`,
`failed_pages`, `computed_as_of` — and **exits non-zero when any page failed**, because a
partially synchronised projection that reports success is exactly the shape of lie the
freshness guard exists to prevent one layer up.

Its cursor lives in `ai.sync_checkpoint` under `feed = 'pos-availability'`, independent of
the `catalog` row. A page that fails is recorded in `ai.sync_failure` and the drain carries
on with the remaining pages; the bookmark stays before the page that failed, so a retry
starts in front of it rather than past it.

**There is still no route** — `ai-service-api-contracts` enumerates the `/v1` surface in a
MUST — **but since C41 there IS a scheduler**, and you no longer have to run this command to
keep the projection fresh.

### The scheduled drain (C41)

The service drains this feed **once when it starts** and then **every
`JPV_POS_SYNC_INTERVAL_SECONDS`**. The start-up drain runs in full when no checkpoint exists —
so a brand-new environment synchronises itself — and incrementally when one does.

| Setting | Default | What it does |
|---|---|---|
| `JPV_POS_SYNC_SCHEDULER_ENABLED` | `true` | Off restores exactly the pre-C41 behaviour, this command as the only drain. That is the ablation and the rollback |
| `JPV_POS_SYNC_INTERVAL_SECONDS` | `600` | **Derived, not chosen.** What matters is how many consecutive failed drains fit under `JPV_POS_PROJECTION_MAX_AGE_SECONDS` before the guard degrades the scope: at the 3600 s ceiling, 1800 s tolerates one, 900 s three, 600 s five. Rule: `ceiling / interval >= 4` |

It does not start under `STUB_MODE`, nor without a configured feed, and it **never blocks
start-up**: the task is created and not awaited, because the container health check probes
`/health` on a three-second timeout and the composition chains service start-up on it. A feed
that does not answer is logged and retried with bounded backoff, and never prevents the process
from starting.

**Why the paragraph this replaces was wrong, which is worth knowing.** It read *«there is no
route and no scheduler, on purpose … an in-process scheduler would add a background task to a
container capped at 512 MiB competing for a pool of five connections … honesty about staleness
comes from `projection_age_seconds`, not from a hidden cron»*, and it carried this recipe:

```cron
# DO NOT USE. Kept as the record of a recipe that could not work here.
*/10 * * * * cd /srv/jbg-ai && /usr/local/bin/uv run python -m jbg_ai.indexing sync-pos >> /var/log/jbg-ai/sync-pos.log 2>&1
```

It was never installed anywhere, and not through forgetfulness: it begins by changing into a
**host directory**, while this service ships as a container — the demo drains with
`docker exec -i jbg-demo-ai …`. It described a deployment that does not exist. The cost
argument does not survive measurement either: an incremental drain fetches nought or one page
of at most two hundred rows and holds one connection for seconds, once every ten minutes,
keeping no state between ticks. And the honesty argument is the one the evidence refuted — the
age was reported faithfully for twenty days and **reached no screen**, across three sessions and
two distinct failure modes, two of which published measurements taken over a scope that had
silently degraded. Reporting honestly was necessary and it was not sufficient. The cron is no
longer hidden either: `GET /health` reports when the drain last ran.

### Concurrency: the advisory lock

Every drain — scheduled, or this command run by hand — takes a **non-blocking** advisory lock
before writing anything, and one that cannot get it **declines** and writes nothing. Declining
is not failing: the work is being done by whoever holds the lock.

`ai.sync_checkpoint` holds one row per feed, so two drains writing at once interleave the
keyset, and an interleaved keyset **does not fail — it skips rows in silence**, which is worse
than the staleness this exists to fix.

| Exit code | Meaning |
|---|---|
| `0` | Drained, no failed pages |
| `1` | At least one page failed, or the feed is not configured |
| `75` | Another drain holds the lock; nothing was written |

### When you still run it by hand

Run `--full` whenever `IndexFeed:SalesAsOf` changes, and after failed pages — `GET /health`
reports the count. An incremental run recomputes nothing: the feed re-emits only pairs whose
inventory row moved, so a clock changed afterwards leaves every unchanged pair on the old one.
The stored `computed_as_of` is what makes such a mixture visible instead of silent.


## The knowledge corpus and its index (C23)

The second index. `ai.knowledge_document` and `ai.knowledge_chunk` had existed since C05
with their final shape and **nothing had ever written to them**; the content lives in
[`../data/knowledge/`](../data/knowledge/), versioned in git, and
[its README](../data/knowledge/README.md) carries the seven authoring rules.

> **Where the corpus is looked for, and why the image carries it (C39a).** The directory is
> resolved by searching three candidates in order — the checkout, the working directory, and
> `/app/data/knowledge` — which is the same search `load_prompt_file` performs for the prompts and
> for the same stated reason: one search, so a container layout cannot diverge from a developer
> checkout. It used to be **derived** by counting parent directories from the module file, which is
> correct in a checkout and lands inside the virtual environment once `uv sync --no-editable`
> installs the package: measured in the deployed container, the corpus was looked for at
> `/app/.venv/lib/data/knowledge`, a directory nothing writes to.
>
> The corpus now also **ships inside the image**, because `data/knowledge/` sits outside this
> image's build context. It arrives through a named additional context, so **a build that does not
> supply it fails** instead of producing an image whose `sync-knowledge` has nothing to read:
>
> ```bash
> docker build -f ai-service/Dockerfile --build-context corpus=./data/knowledge … ai-service
> ```
>
> Both consumers pass it: the demo deployment workflow and, for local development,
> `backend/docker-compose.yml` through `additional_contexts`. With the table empty the
> piece-anchored argument is withheld for want of material to anchor it to and the piece-anchored
> question answers `knowledge_not_covered` — which read on screen as a defect of the sale card and
> are not one.

Three commands need neither a database nor a provider:

```bash
uv run --system-certs python -m jbg_ai.knowledge validate   # the seven rules + coverage
uv run --system-certs python -m jbg_ai.knowledge stats      # doc_type and claim_scope counts
uv run --system-certs python -m jbg_ai.knowledge measure --compare
```

Indexing does need both, and it lives beside the other two drains:

```bash
uv run --system-certs python -m jbg_ai.indexing sync-knowledge          # idempotent
uv run --system-certs python -m jbg_ai.indexing sync-knowledge --full   # re-embed everything
```

Like `sync` and `sync-pos` it loads `backend/.env` through `run_module`. It needs
`JPV_EMBEDDING_API_KEY` and `DATABASE_URL`; it needs **no** index feed, because the corpus
in git is the whole truth. **There is no cursor**, so `--full` does not mean "ignore a
checkpoint" — it means **re-embed every chunk**, which is what a change of embedding model
calls for. The corpus is validated *before* anything is written: an invalid document fails
the command rather than landing half-indexed. It prints one line of counters —
`documents`, `chunks`, `embedded`, `skipped`, `deleted_chunks`, `deleted_documents`,
`version`.

**There is no route**, and that is a decision rather than an omission:
`ai-service-api-contracts` freezes the `/v1` surface in a MUST that enumerates ten routes,
and the only consumer of knowledge search is C30, **in this same Python process**. Adding a
route would mean regenerating the committed `openapi.json` and agreeing it with the .NET
side in order to connect two modules of one process. `search_knowledge()` is a callable,
shaped as a tool so C30 can hand it to the sales agent as `consultar_conocimiento`.

### What this corpus is, and what it is not

Stated here because a citation that is well formed and wrong is worse than no citation:

- **It is synthetic.** An assistant wrote it against the eight versioned block prompts in
  [`prompts/knowledge/v1/`](prompts/knowledge/v1/), reviewed block by block; the commercial
  texts the design listed as *«to ask the business for»* never arrived, exactly as the
  photographs never did. `_corpus.meta.json` seals the model, the prompt version and the
  instant.
- **Citation verification is structural, not semantic.** It confirms that the cited source
  existed and was retrieved, **not that it tells the truth**. An invented corpus can pass
  the check at 100 % while citing something false *with a verified stamp*.
- **The `establecimiento` sections are a minority of the corpus**: commitments of the house
  that are **today illustrative**. `_corpus.meta.json` seals the exact counts and
  `python -m jbg_ai.knowledge stats` reprints them, so no figure is copied by hand into
  prose that nothing re-measures. The whole service block is one, which is what demonstrates
  the marking mechanism from the first document. That mark travels with every retrieved
  fragment and C30 is obliged to propagate it: a commitment read aloud as if it were a fact
  of the world is the failure the mechanism exists to prevent.
- **The ring size table is a convention of the house.** Its arithmetic —
  `circunferencia = talla + 40`, and the diameter derived from it — is ordinary Spanish
  practice and is scoped `general`; that `M` is sizes 13-15 is a decision and is scoped
  `establecimiento`. Confirming those ranges with the business is a pending, non-blocking
  verification: if they differ, it changes **one section of one document**, and its mark
  already flags it.
## The evaluation harness and the golden set (C24)

The retriever was complete before anything measured whether it was any good. Expansion, fused
retrieval and the point-of-sale prefilter were all decided against a rubric that counts a hit as
«right piece type and right material» — which is the lexical branch's own objective function,
since `doc_text` carries canonical `Tipo:` and `Materiales:` lines and the expansion aims at
them. C24 builds the impartial judge those four changes each promised would re-measure them.

**48 judged queries and 56 written**, in [`evals/golden/`](evals/golden/), versioned in git with
graded relevance 0-2 and the annotation criterion written **before** any label. The composition
is validated by code and **the load fails** when the set stops being able to arbitrate what it
exists for — twelve queries whose best document the lexical branch cannot reach even after
synonym expansion, five that resolve only to a sparsely tagged field, four naming four different
stones, six covering the three classes of dictionary entry, five plausible in-domain questions
the catalogue cannot answer, four that are a literal code or name, and no category answered
entirely by synthetic products.

```bash
cd ai-service
uv run evals validate                                  # the set alone: no database, no provider
uv run evals freeze-vectors                            # once, against the real provider
uv run evals run --all --repeat 3 [--persist]          # the ablation table
uv run evals run --config v2b-fusion                   # one row
uv run evals sweep                                     # phase A: the branch-weight ratio
uv run evals capture                                   # phase B: persist one window per query
uv run evals rescore                                   # phase C: the weight grid, offline
uv run evals cag [--dry-run]                           # the context-only measurement, dated
uv run evals provider-latency                          # the provider round trip, cold and warm
```

> **Pass `GIT_SHA` when the run happens inside the container, which is the normal case.** Any
> measurement against the real provider runs in `jpv-pv-jbg-ai`, and there is no `.git` in the
> image — so `evals/routing.py:git_sha()` falls through to `unknown` and the artefact records a
> provenance nobody can use. It reads the environment first for exactly this reason:
>
> ```bash
> docker exec -e GIT_SHA="$(git rev-parse --short HEAD)" jpv-pv-jbg-ai \
>   python -m jbg_ai.evals.free_query_gate --prompt-version assist/v5
> ```
>
> **If the tree is dirty, say so**: `GIT_SHA="$(git rev-parse --short HEAD)+dirty"`. A bare sha on
> a dirty tree declares a re-run at that commit comparable when it is not — the trap
> `evals/provenance.py` documents, and the one C40's two placeholder artefacts fell into.

**The calibration runs in two phases, and their order is a constraint rather than a
preference.** The fusion decides WHICH candidates a query produces; the business signals only
reorder them — `demote` is a stable sort that removes nothing. So:

```
  phase A  ·  sweep     fix the fusion          provider + database · the window MOVES
                ↓ frozen
  phase B  ·  capture   one retrieval per query, window persisted with its signals
                ↓ window FIXED
  phase C  ·  rescore   the business-weight grid    no provider · no database · seconds
```

Inverting them is a **silent** failure: phase C would run, print numbers, and they would
describe a fusion that is no longer the one being calibrated. So each capture records the
fusion fingerprint it was taken under and `rescore` **refuses** a window that does not match,
naming what differs. `rescore` also needs no `DATABASE_URL` at all, which is the guarantee
rather than a convenience — the signals and the assortment's buckets travel inside the capture
file.

`sweep` explores `rho = w_vec / w_lex` over a **one-dimensional** grid, because only the ratio
changes the order: scaling both weights preserves it, measured by running `fuse`. `k` and the
branch depth move together, by C21's rule that a deeper branch keeps more of its tail voting.

`--persist` is the only thing that writes `ai.eval_run` / `ai.eval_case` / `ai.eval_result`; the
report and the per-query detail land in [`evals/results/`](evals/results/) either way. The
component that produces the results does not import the one that persists them.

**The harness introduces no setting of its own.** What it needs is already in the table above,
and the reason it is listed here is that it needs all three at once and fails naming the missing
one rather than measuring something else:

| what | why the harness needs it |
|---|---|
| `DATABASE_URL` | The pool cannot be built from a file: knowing what each configuration returns means running it against the real index. Read from the process environment, not from `backend/.env`, which carries credentials only |
| `JPV_EMBEDDING_API_KEY` | Only for `freeze-vectors` and `provider-latency`. A **run** never calls the provider: the query vectors are frozen once and served from `golden/query_vectors.jsonl`, and a missing vector raises instead of embedding on the fly, because a run that silently embeds is a run nobody can repeat |
| `JPV_RAG_LLM_API_KEY` | Only for `evals cag`. A different key from the embedding one, on purpose |
| `SSL_CERT_FILE` | On this machine TLS is intercepted and LiteLLM verifies against `certifi` rather than the operating system store — see the two Windows traps above. Set `REQUESTS_CA_BUNDLE` to the same file for `evals cag`, whose token counter downloads its encoding through `requests` |

The event loop policy is handled by the CLI itself: `psycopg` cannot run in async mode on the
proactor loop Windows installs by default, and the failure names neither psycopg nor the policy.

The measured answer to the question the project rests on, over graded relevance
([full report](evals/results/c24-baselines-2026-09-07.md), [implementation
report](../Documentos/Proyecto%20Final%20AIEng/informes/c24-implementation-measurements.md)):

| configuration | what it is | nDCG@5 | cost/query |
|---|---|---:|---:|
| `v0-nombre` | the product search the shop already had | 0,082 | $0 |
| `v0-fts` | the degraded Spanish full-text searcher | 0,454 | $0 |
| `v0-cag` | the whole catalogue in the context, no retrieval | — | $0,00267 |
| `v1-vectorial` | the vector branch alone | 0,548 | $0,0000002 |
| `v2-hibrido` | the single-stage fusion of C21 — **historical**, see below | **0,603** | $0,0000002 |

Read in two steps: tokenising Spanish buys **+0,372** and is free; semantic retrieval on top of
that buys **+0,149**. And the verdict of the earlier rubric is **reversed** — it gave the vector
branch 67 of 120 against the lexical 107, and against a judge that is not one of the parties the
vector branch beats the full-text baseline. On the twelve queries with no lexical anchor the
full-text baseline scores 0,035 and the vector branch 0,431.

**RAG against CAG, measured rather than argued.** The compacted catalogue is 17.583 tokens and
$0,00267 a query — four orders of magnitude more than embedding a query — and on the subset that
most favours it, it recalls 0,133 against the vector branch's 0,483, answering literally
`NINGUNO` on ten of twelve. Retrieval also has no catalogue ceiling: the same context stops
fitting a 100.000-token budget at **6.643 products** — a figure the harness computes and prints
under the scale curve, rather than leaving it as a division for the reader.

Latency is reported as **two figures**, always. `p95` of retrieval, which excludes the provider
round trip, is **128,6 ms** against the 500 ms the design fixes; end to end with a cold provider
would be ~900 ms, and applying the criterion to that column would report a red that belongs to
the provider. Measured separately, the provider costs p50 223 ms / p95 832 ms cold and **0 ms**
warm — the process-wide client does not reduce the round trip on a repeated query, it removes it.

**Four limitations, declared rather than mitigated:**

1. **There is no inter-annotator agreement.** The design promised double labelling with
   reconciliation between two people; the project is developed by one, so that mitigation **was
   not applied**. What replaces it is the criterion written before labelling, grouping the
   sessions by category and a deferred re-read of the doubtful ones. The absolute values carry
   the bias of a single judgement; **what is comparable between configurations remains valid,
   because the bias is the same in every row.**
2. **The annotator wrote part of the corpus** — the 764 synthetic products came from C06b. This
   is irreducible, and it is why every metric is broken down by data origin.
3. **The set is small.** With 41 queries in the real portion the confidence interval of the
   acceptance criterion is ±0,13: it does not tell 0,80 from 0,88.
4. **What the point-of-sale prefilter costs in recall is not measured.** The golden set is
   labelled unscoped, a decision taken in C22 so that retrieval quality and assortment coverage
   are not compressed into one number, and the scoped row was cut by declared decision.

## Ranking, business signals and abstention (C25)

C25 used that judge and found four things no argument had. The report is
[`evals/results/c25-baselines-2026-09-11.md`](evals/results/c25-baselines-2026-09-11.md) and the
measurements are in
[`c25-implementation-measurements.md`](../Documentos/Proyecto%20Final%20AIEng/informes/c25-implementation-measurements.md).

**The fusion did not fuse: it concatenated.** With C21's weights the sixty lexical documents
outscored the vector branch's best hit in **every** query, so a grade-2 document the vector
branch ranked **first** landed at **position 33**. It was an arithmetic defect, not a badly
calibrated weight. The fusion is now composed in **two stages** — the two lexical lists into one
ranked list, that list against the vector one under per-**branch** weights — so a branch's total
vote is exactly its declared weight however many of its own lists matched, and the lexical branch
stops contributing 120 candidates against the vector branch's 60.

**That single-stage fusion no longer exists (C25bis).** C25 kept it selectable so its published
baseline row could be re-measured; with the table published and the configuration frozen, what
was left was a dead path that could be switched on by accident and whose arithmetic the project
had measured as defective. It went, along with the per-list weights `JPV_RRF_WEIGHT_TYPED`,
`_EXPANDED` and `_VECTOR` — the first two were still read, as the fixed internal split of the
lexical branch, but the specification requires them to be equal and forbids sweeping them, so a
setting could only ever be moved into violation with nothing to detect it. They are now one
declared constant in the orchestrator, and the change could not move a figure because only stage
one's **order** reaches stage two.

**The baseline row `v2-hibrido` is therefore historical and not re-executable**, which is
declared rather than disguised. Three artefacts keep it citable: the published figures and
provenance in [`evals/results/c25-baselines-2026-09-11.md`](evals/results/c25-baselines-2026-09-11.md),
the per-query detail in [`evals/results/runs/d91d4864-ba84-40a0-b78f-acb0c461108f.jsonl`](evals/results/runs/),
and the configuration it was measured under in
[`evals/configs/retired/v2-hibrido.yaml`](evals/configs/retired/v2-hibrido.yaml) — which no longer
loads, by design. The harness does **not** restate the retired pipeline to keep the row runnable:
a harness that restates a pipeline measures the restatement.

Why it was retired is still demonstrable, and cannot be switched on: `test_the_flat_arithmetic_
that_was_retired_buried_the_vector_leader` proves the burial over the fusion primitive alone,
with the retired weights as literals local to the test. A number in a settings module is a
configuration somebody can set; the same number in a test is a record of what was measured.

**A deployment that still exports any of the four retired variables has no effect** and the boot
does not fail over it. The asymmetry is deliberate: an ignored retired knob produces the *right*
behaviour, so what is left is a mistaken belief rather than a mistaken result, and rejecting it
would turn a harmless leftover into an outage. Where a stale knob *would* change a result is an
evaluation configuration — it would publish a row that measured something else — and there it is
refused by name. What a run actually composed is read from its recorded provenance, never from
the environment somebody intended.

**The lexical branch now weighs less when its best candidate matched less of the query.** The
coordination tally had been computed, carried on every hit and read by nobody — the fourth
stripped cable of this subsystem. `w_lex x coverage`, with **no parameter of its own**. The
denominator counts only the groups whose `tsquery` is non-empty, which is the whole rule: a stop
word the operator typed becomes a counting group that can never match, and counting it would cut
the weight of a query that is in fact fully anchored. Measured against the same fusion with the
rule off, it buys **+0,128** on `descripcion-sin-anclaje` and **exactly zero** on the other seven
categories — and it turns the branch ratio from a cliff into a plateau, taking the sweep's range
over `rho` from **0,070 to 0,007**.

**Availability reorders, and it is read without restricting.** The scope that RESTRICTS
(`pos_id`, C22's prefilter) and the scope that only READS (`signal_pos_id`) are two independent
parameters over one CTE, so the reordering can be measured without paying the prefilter's recall
cost. A candidate the point of sale does not carry reports its signals **absent**, and absence is
never read as zero. The score only ever subtracts, which is what keeps an unread row neutral.
`JPV_BUSINESS_WEIGHT_AVAILABILITY=0` is the rollback.

**The retriever can decline to answer.** The form of the rule was chosen by a measurement under a
criterion written before the distribution was inspected: the best-hit distances of answerable and
out-of-domain queries **overlap completely**, so no scalar separates them. What discriminates is
the **shape** of the distance profile — an impossible query is flat, because nothing stands out.
`JPV_ABSTENTION_ENABLED=false` is the rollback and restores answering everything.

**The calibration runs offline after one capture.** See the two phases above under
`uv run evals capture` / `rescore`.

**Four limitations this change declares rather than mitigates:**

1. **`Recall@5` reaches 0,758 against the 0,85 the design asks for.** The gap is +0,09 and no
   lever in this change can close it: recall at five depends on **what** enters the window, and
   the business signals only reorder what already did. The criterion was restated as a relative
   one — each row beats the one it is built on — and this distance is declared.
2. **The signals row does not clear the relative criterion either.** `v3` improves the
   operational metric by **+0,030**, below the 0,05 this golden set can resolve. It is adopted
   because its own adoption rule is satisfied and because the set is **structurally blind** to
   availability — `criterion.md` never mentions stock — so what is missing is resolution, not
   evidence. Reported as a gap, not as a pass.
3. **Abstention reaches 0,150 against the 0,80 the ticket asks for.** Reaching 0,80 costs
   silencing **21 of the 43** answerable queries. The rule is fixed at the most it can catch
   while silencing **none** of them, and the rest is declared. The 0,150 is what the system
   declines, not what the rule alone catches: an abstention and a `low_confidence` land on the
   same response flag, so the figure unions the two — the rule takes it from 0,050 to 0,150,
   and its own two-sided figures are in the C25 implementation report.
4. **The out-of-domain category is unbalanced in a way that is measured but not corrected.**
   Naming a material pulls a query **0,12 closer** to the catalogue and makes it look more
   answerable; 12 of the 20 queries name one, because the five inherited from C24 all do and
   rewriting them would falsify the comparison with the published baseline.

## Out-of-stock substitutes (C26)

`POST /v1/retrieval/substitutes` was the last closeable 501 of the frozen contract. It answers
the question the retriever could not: *this piece cannot be sold — what do I show instead?*

**It calls no provider.** Substitutes are product to product, the anchor is a `product_id`, and
that product's embedding is already stored, so the whole capability is one SQL statement: no
query to embed, no lexical branch, no synonym expansion and no rank fusion. `fuse()` is not
called, because there is a single candidate list and a fusion over one list is the identity
map. A test asserts the provider is never touched.

**The candidate universe has exactly one hard filter: `piece_type`.** A ring is not a
second-best pendant, and the raw vector violates the type in 2 of the 4 measured cases. The
source product itself and anything in `filters.exclude_product_ids` are removed too. Nothing
else removes a candidate — in particular **availability never does**.

**The order is three continuous terms and no integer block:**

```
  orden(c) = sim(c)                              sim = 1 - distancia coseno
           - w_size          · [talla distinta]  sólo si AMBAS declaran talla
           - w_availability  · [qty_bucket = 0]  business_score de C25, reutilizado
```

`demotion_rank` is deliberately **not** reused. Its size component is an integer block, and a
block does not break a tie — it PARTITIONS, sending every candidate of another size behind
every candidate of the right one. That is the shape C25 measured with its rotation term
(11.067 inverted pairs, 71,2 % of them more than ten positions apart) and withdrew. Measured
here on the live `SKU13` neighbours: under a block the nearest sibling falls from position 1
to position 4 and the furthest leaves the top five; under the continuous term both stay
visible. `test_different_size_sibling_stays_inside_the_visible_window` is the guard.

**The size term is inert unless both sides declare a size.** An absent size is not a mismatch,
and it is not a corner case: **54 % of the rings carry no `size_label`**.

**The family is guaranteed, not privileged.** Every live member of the source product's family
comes back and reports `family_match`, but membership buys no position: measured over the four
reserved queries, "same family first" leads with the unsellable candidates, because a family
is by construction the set of pieces that differ in exactly the attribute that disqualifies.

**Availability demotes and never eliminates**, the §15.10 invariant: the projection can lag
minutes behind the counter, so a candidate it reports as exhausted is ranked below its
available peers and still returned. **Excluding on stock is C34's**, on the .NET side, which is
where the authority over stock lives. The projection age travels in each result's
`debug.notes`, because `SubstitutesResponse` has no field for it and the snapshot is frozen.

**An unusable source product is an explicit error, never an empty success.** Absent from the
index, inactive, or indexed without an embedding → **422 naming the cause**. A 200 with an
empty list is indistinguishable from a catalogue that holds no substitute.

**The endpoint does not abstain, and that is measured.** Over a sample of 300 documents the
distance to the nearest neighbour tops out at 0,123 with a family and 0,255 without one, and
the second range contains the first — the containment that stopped C25 re-fixing its scalar
threshold. In a catalogue of 1.168 Menorcan sea-jewellery pieces everything resembles
something, so `low_confidence` is emitted false by decision rather than by deferral.

### The setting

`JPV_SUBSTITUTE_WEIGHT_SIZE` (default **0,05**, optional at boot, blank means unset). Unlike
`JPV_BUSINESS_WEIGHT_AVAILABILITY`, **its value matters and not only its sign**: that one is a
binary term at the end of an otherwise lexicographic key, so the score took two values and any
positive weight gave the same order. Here a binary size term is mixed with a continuous cosine
similarity, so the weight fixes a real exchange rate. Zero is the rollback and restores exactly
the ordering the remaining terms produce alone.

The default comes from the sweep in
[`evals/results/c26-substitutes-slice.md`](evals/results/c26-substitutes-slice.md), not from an
argument. Eleven grid points over the five anchored queries: graded nDCG@5 peaks at `0,075`
(0,8785), but from `0,07` upward the **binary** reading falls from 1,0000 to 0,9738 and
Recall@5 from 0,4241 to 0,4135 — a grade-0 document (`SKU334 Anillo plata M`, the right size
and nothing else) enters a top five. Under C25's precedent of optimising with pure relevance as
the guardrail, the largest weight that holds every guardrail at its maximum is `0,06`, and
`0,06` beats `0,05` by **0,0051 of nDCG@5** on a single position swap in one query. That is
below noise, so the declared rule applies and **`0,05` is adopted** — measured, not assumed.

### Two limitations, both measured

1. **`style_similarity` is structurally near zero on the real catalogue.** Only **1 of 404**
   real products has any same-type candidate to share a style tag with, against **97,8 %** by
   material. The contract declares the field required and not nullable, so the Jaccard is
   emitted and **the absence is declared in `match_reasons`** — a zero over two untagged pieces
   must never be read as "different styles". It is deliberately **not** derived from the
   embedding: that would give it 100 % coverage and make it a copy of `score`, which is the
   second-definition-that-diverges mistake C19 was annulled for.
2. **The evaluation isolates the quality of the substitute GIVEN the correct source product.**
   The golden-set queries are text and the endpoint takes a `product_id`, so each query
   declares an explicit `source_product_id`. The full chain «operator's text → product →
   substitutes» is **C32's** and is not measured here; chaining it would have charged this
   capability with the first step's failures. Two further limits of the slice: it is five
   queries, and only **two of them move at all** under the weight — the other three name no
   size or have none — so the sweep is decided by a narrow base; and the annotator is the same
   agent that designed the ordering, which is declared exactly as the README already declares
   the absence of inter-annotator agreement for the golden set as a whole.

### Running the slice

```bash
cd ai-service
DATABASE_URL=... uv run --system-certs evals substitutes
DATABASE_URL=... uv run --system-certs evals substitutes --weights 0,0.05,0.08
```

It is a **subcommand of its own and never a row of `run --all`**: the endpoint takes a product
identifier, so `v0-fts` and `v0-nombre` could not execute it, and a row would move the
denominator of a table published twice. `GoldenSet.retrieval_queries` enforces that split in
code — the ablation runner and the sweep measure it, `judged_queries` stays the composition of
the set — and `test_the_published_ablation_denominator_is_the_one_c25_measured` pins it at 63.

## Structured sale assistance (C30a)

`POST /v1/assist/sale` was frozen into the contract by C02 and served a fixture until C30a.
It now serves a real response with `STUB_MODE=false` — **and still writes no prose**. The
argument in Spanish, its versioned prompt and the numeric gate that guards it are C30b, and
the split is the point: same route, same candidates, same citations, with an argument and
without, which is the one ablation the design's §11.2 asks for that no other row supplies.

**The contract moved once, in this change, while the route had zero consumers.**
`IAiGatewayClient` had no assist method and C34 did not exist, so the cost was nil; after C34
it would not have been. The frozen shape could not serve its own consumer anyway — `family_id`
was required against a catalogue where **58 % of products have no family**, and `query` was
required against two .NET routes both anchored to a piece.

```
AssistRequest    + product_id (optional) · query now optional · validator: AT LEAST ONE
AssistGroup        family_id → nullable · invariant: null ⇒ exactly one member
AssistGroupMember + match_reasons
Citation           + citation_id · document_title · section_title · claim_scope · doc_type
                   + score   ·   − source
AssistResponse   + abstained · prompt_version
```

### Three modes, chosen by the anchors and by nothing else

| | `product_id` | `query` | `intent` | citations |
|---|---|---|---|---|
| **free query** | — | ✓ | `unclassified` | `search_knowledge`, unfiltered |
| **piece alone** | ✓ | — | `product_pitch` | addressed by primary key, no search at all |
| **piece + question** | ✓ | ✓ | `unclassified` | `search_knowledge` with the piece-scoped filter |

`intent` is **derived from that table**, never from the wording. Classifying a query is C31
entire; a keyword router built here would be work C31 deletes, and the value reported for a
piece with no question stays correct after C31 because that router replaces `unclassified`,
never `product_pitch`.

### Warnings are codes, and there are exactly two

`family_has_variants` and `size_label_missing`, from `jbg_ai.assist.constants`. **The model
never sees the vocabulary and cannot add to it**, which is what makes "warnings are
rule-derived" a property a test can witness rather than a promise. The Spanish a human reads
belongs to the frontend — the same rule the assisted-search panel already follows for the
retriever's match reasons.

`stock_critical` and `family_members_out_of_stock` are **deliberately absent**: they need real
stock, and this service holds only an availability bucket for ranking that may be minutes
stale. "Critical stock" said out loud with twelve units in the drawer is the assistant's
credibility at the counter. They belong to C34, after hydration.

`family_has_variants` is computed from **`family_roster(family_id)`**, a new method of
`ProductSearchPort` reading `ai.product_document` alone in one statement, capped at 24 — three
times the largest family the live index holds (measured 2026-09-13: 156 families, 491
memberships, maximum 8). Grouping cannot know about members the retrieval never returned, and
the warning is exactly a statement about them.

### Citations resolve, and carry their scope

Citations are fragments of the **knowledge corpus and nothing else**: citing the catalogue
would verify nothing, since the product's metadata already travels in the response. The
anchoring of a candidate in the catalogue is expressed with `match_reasons`.

For a **piece with no question** the fragments are addressed by `chunk_id(document, section)`
over an explicit allow-list — `cuidados-y-limpieza-en-casa` and `piel-sensible-y-alergias`,
present and `general` in all nine canonical sheets — for at most two declared materials, plus
`material-piezas-mixtas#limpiar-una-pieza-mixta-sin-estropear-nada` when the piece declares
two or more. **Only `claim_scope: general` enters.** That is not caution: `material-bano-de-oro`
carries a seventh section, «Nuestra garantía sobre el baño», scoped `establecimiento`, whose
last paragraph says the conditions are confirmed in store before being passed to a customer.
"All the sections of the sheet" would put a workshop guarantee into an argument nobody asked
for, and only for plated pieces. The allow-list and the cap travel **by parameter** so C30b can
sweep 1/2/3 sections in one process.

### The knowledge filter is asymmetric, and the asymmetry is measured

`search_knowledge` gains an optional **per-document exclusion**, applied in **both** branches
on the document's primary key — `document_id(slug)` — with the same conditional-clause shape
as the `doc_type` filter. No migration, no new column, and its rollback is passing nothing.

With a piece anchored, the caller excludes the sheets of the canonical materials the piece does
**not** declare, and **nothing else**: `faq`, `politica`, `talla`, the stone sheets,
`material-piezas-mixtas` and `material-marcajes-y-punzones` always pass. The last two carry
`doc_type: material` without being outputs of `material_sheet_slug`, and that is correct —
*«¿qué significa el 925?»* is answerable about a steel piece.

Measured over the 72 golden queries against the **live index at the production threshold of
0,51** (report of 2026-09-13): the filter removes a mean of **36,4 foreign-sheet citations** per
anchored material while moving abstentions only from **41 to 44,3 of 72** — so it does not
silence what the corpus can answer. It also **promotes**: the 36,4 removed cost a net 24,6,
because the clause filters before the `LIMIT` and about 11,8 correct fragments per anchor rise
into the freed slots.

The same measurement settled the open question of whether the free-query mode needs a threshold
of its own. **It does not:** of 101 citations only one is unambiguously spurious, and the
threshold already abstains on 41 of the 72 queries.

### What it never does

Abstention is **honoured and declared** in `abstained`, never expressed by reusing
`low_confidence` — that signal means cross-branch consensus, and on the judged set it fires on
1 of 20 out-of-domain queries against 10 of 43 answerable ones, which is the opposite of what a
reader would conclude. A piece the index cannot serve — unknown, inactive, or held without an
embedding — is **422 naming which**, never a 200 with `abstained` set: that would claim the
catalogue has no answer when the problem is the piece.

No field of the response carries a price, a stock quantity or an availability bucket, and the
test that checks it walks the **whole serialised response**. Since C30b that check runs over a
response carrying a **real argument**: its C30a equivalent ran over an empty `pitch` and
therefore passed having asserted nothing about prose.

## The generated sale argument (C30b)

The two piece-anchored modes now call a language model and write three to five sentences of
continuous Spanish prose over the context C30a already distils. The free query does not, and
neither does an abstained request — both cut **before** the call.

```
POST /v1/assist/sale --> modo · recuperacion · roster · avisos · contexto citable
                            |
      consulta libre  <-----+  sin llamada · pitch "" · prompt_version null
      abstencion      <-----+  sin llamada · pitch "" · prompt_version null
                            |
                            v  pieza anclada
                     generar --> 1 resolucion · 2 correspondencia · 3 puerta numerica
                            |
                            +--> UNA reparacion con TODAS las violaciones juntas
                                     |
                       dura  <-------+-------> correspondencia
                  sin argumentario            argumentario, ESA cita retirada
```

**Its own credential and its own model, both optional.** `JPV_ASSIST_LLM_API_KEY` and
`JPV_ASSIST_LLM_MODEL` separate counter-side generation from C09's batch enrichment, which is
worth separating: different cost to attribute, different rate limit to hit, different rotation,
and a much smaller blast radius. Neither is required — the key falls back to
`JPV_RAG_LLM_API_KEY` and the model defaults to the one every figure here was measured on —
because making them required would have stopped an existing deployment generating the day the
fields appeared, and would have done it **invisibly**: this route degrades to 200 without prose
rather than failing. The fallback is therefore **logged**, once per process:
`stage=assist_client model=… timeout_s=… credential=assist|rag_fallback`. Nothing about a key
but which of the two it was.

**`prompt_version` changed meaning, and that is the only thing `openapi.json` moved.** It now
says *the generation layer ran* rather than *there is a pitch*, which is what distinguishes "we
do not write" from "we tried and the guard refused it" — the only evidence a consumer has that
the guard acted. One description, verified field by field: 1102 leaves before and after, one
changed leaf, same `anyOf`, same type, same title, no field added, removed or retyped.

### The three checks, and the one that is not there

| | what it buys | policy if it survives the repair |
|---|---|---|
| **resolution** | the source exists and was in the context | **hard** → served without the argument |
| **correspondence** | the citation was used *for text actually written* | **proportionate** → **that** citation withheld, the prose is served |
| **numeric gate** | no price or stock figure reaches the counter | **hard** → served without the argument |
| ~~semantic fidelity~~ | *that the fragment says what the sentence asserts* | **not checked here** — declared in the capability, measured with RAGAS in C38 |

The last row is the *alucinación con coartada* and it is declared rather than implied. No model
judge runs in the serving path: it would double the latency and the cost where a customer is
waiting, and using a model to catch another model's fabrications is circular.

**Correspondence is why the output carries a supporting span.** `{pitch, citation_ids[]}` — the
obvious shape — verifies only that an identifier resolves, so a model that echoes back the five
identifiers it was handed passes perfectly and trivially having used none. Declaring a span of
its own prose per citation makes "these are the ones it used" checkable: five citations oblige
five real fragments of the text that was written, and an invented fragment is a substring of
nothing. The span is **internal** — it never reaches the wire, so the verification costs zero
contract movement.

### The numeric gate is a whitelist plus one blacklist, and the corpus is why

Every numeral of the argument must belong to the set of numerals of the **payload object**, and
the gate reads that object rather than the rendered prompt — reading the text would admit the
numerals of the instructions themselves and open the gate on its own. `prompts/assist/v1.md` is
written **without a single digit** so that rule costs nothing, and a test pins it.

Membership alone is not enough, and the measurement is the corpus's own: `material-oro.md`
states that eighteen carats are **750** thousandths and fourteen are **585**, and
`material-plata.md` that sterling is **925**. With the gold sheet in context, `750` *belongs to
the whitelist*, so "750 €" walks through a pure whitelist — exactly the hole the gate exists to
close. Therefore **adjacency to a currency or stock marker refuses whether or not the numeral is
admitted**. It is the single blacklist of the design and it is correct here because that set is
closed and unambiguous, unlike "numbers in jewellery"; and it applies to the numeral's
**context**, never to the numeral.

The operator's query is handed to the model as **delimited data in the user message** — never
concatenated into the system one — and is deliberately **not** part of the admitted set: it is
what to answer, not what is true, and it is the one surface a person outside this code controls.

Rejections are recorded by **cause** — `figure_not_in_context`, `currency_adjacent_figure`,
`stock_adjacent_figure`, `enumeration_format`, `decimal_form` — because an aggregate rejection
rate cannot tell a gate that works from a gate that gets in the way.

### Nothing is written down, and that includes the log

Serving one request executes **no data-manipulation statement**, checked with a
`before_cursor_execute` listener on the `Engine` class that counts DML — not by asking which
modules were imported, which is what a module check cannot see. The log line carries the trace,
the prompt version, the model, the usage, the latency, the citation identifiers used, the
warning codes, the abstention, the length and a **hash** — and never the text. A log line is
durable storage outside the database and carries no point-of-sale scope, while the response
does; the text is re-derivable from a versioned prompt at temperature zero, which is what makes
not storing it viable rather than merely cautious.

**The declared exception is the evaluation harness.** `python -m jbg_ai.evals.assist_sweep`
stores the **complete generation object** — the prose plus every declared citation with its
span, and the pre-repair object too — bound to `run_id`, `git_sha` and `prompt_version`, outside
the serving path. C38 inherits it that way on purpose: with the spans, claim-citation pairs
arrive already aligned.

### Failure is a state of the contract, not an exception

| outcome | `pitch` | `prompt_version` | `citations[]` |
|---|---|---|---|
| generated and verified | prose | `assist/v1` | the ones it used |
| correspondence failed on one | prose | `assist/v1` | the ones it used, **minus that one** |
| hard violation survives | `""` | `assist/v1` | **the ones that grounded the response** |
| provider down or timed out | `""` | `assist/v1` | the ones that grounded the response |
| free query, or abstention | `""` | `null` | the ones that grounded the response |
| **neither** `JPV_ASSIST_LLM_API_KEY` **nor** `JPV_RAG_LLM_API_KEY` | `""` | `null` | the ones that grounded the response |

Degrading never leaves the response poorer than the structured layer's own — that is what keeps
the generation measurable as an **ablation** against C30a, which needs the same route, the same
candidates and the same citations with prose and without it. The last row is also the rollback:
removing the client leaves C30a's behaviour without touching a schema.

The ceiling is **two provider calls per request**: the generation and at most one repair,
carrying every violation of every check together. It is literal — there is no transient-retry
backoff underneath it, and that is a deliberate departure from C09's seam, whose two-second base
backoff would consume two thirds of the per-call budget before the retried call started.

## The sale assistant's tool registry (C32a)

C30a gave the assistance layer its structure, C30b its prose and C31 its entry guardrail. What
was missing to close the agentic branch was the layer of decision, and C32 was split on
2026-09-20 into the two halves that compose it. **This is the lower one: the tools and their
registry, and it calls no chat provider at all.** The loop, its budgets, `partial: true` and
`POST /v1/assist/agent` are C32b, and they **landed**: see the section below.

`jbg_ai/assist/tools.py` holds six read-only tools — `buscar_catalogo`, `buscar_sustitutos`,
`listar_familia`, `consultar_conocimiento`, `consultar_disponibilidad` and `pedir_aclaracion` —
each with a Spanish description written for a reader who sees no code, a typed parameter schema
and **argument validation that runs before any port is touched**. It is a library wired to **no
route**: `openapi.json` is byte for byte the file C31 left, and `POST /v1/assist/sale` behaves
exactly as it did.

Four properties are what the half is for, and each is a test rather than a sentence.

**The set of six is frozen.** `TOOL_NAMES` is a declared constant and construction refuses
anything outside it, so the two tools withdrawn before this registry existed —
`perfil_punto_venta`, whose change was cancelled, and `buscar_complementarios`, cut when its
signals measured empty — cannot come back by accident.

**Nothing writes, and the check looks at the object graph.** Not at a `writes: bool` on the
descriptor, which is set by whoever registers the tool — precisely who could be wrong. Three
axes over the constructed registry: the set of names, the methods every collaborator a tool
captured exposes, and the HTTP verbs any registered client could issue. A tool that describes
itself as read-only and captures a port with a write method **fails the build**. The published
limitation that no agent writes is one of the three this README hands over, so it is
demonstrated or it is not declared.

The write vocabulary is matched **token by token** and not as a substring, and that is a
correction the implementation forced: read literally, `sync` occurs inside
`ProductSearchPort.projection_synced_at()` and `ProjectionFreshness.synced_at()`, which read a
checkpoint, and the invariant would have been unsatisfiable with the very ports the registry
must inject. What token equality loses is not an inflection of a verb the vocabulary holds but
a verb it never had — `put_checkpoint()` writes and matches nothing, under either reading — so
the set is a floor under the object graph and not a proof that no method writes.

Two objects are excluded from the scan, **by name and not by category**: `Settings` and
`ServicePrincipal`, which are configuration and identity, perform no I/O, and trip the
vocabulary only on pydantic's deprecated v1 shim `update_forward_refs`. Excluding the *kinds*
they belong to was the first attempt and it was a bug: dropping every pydantic model and every
dataclass silently removed `InMemoryKnowledgeIndex` — a real port, captured by
`consultar_conocimiento` — from all three axes while every assertion stayed green. A port is
inspected whatever it is built from, and the exclusion list lives in the module whose only
reason to exist is to check, so no tool can opt its own dependencies out.

**A failure is data.** No exception leaves an invocation: one escaping would kill C32b's loop
instead of costing it a single turn. Every failure carries a code from a closed vocabulary —
`argumento_invalido`, `referencia_desconocida`, `referencia_no_utilizable`,
`dependencia_no_disponible` — never prose, by the rule the rule-derived warnings already follow.

**Availability is a band and never a figure.** `consultar_disponibilidad` is the one tool that
had no service behind it, and it is served from `ai.pos_projection` rather than from .NET —
which resolves the open question of the design's §6.1 by **deferring it with a reason**: the
only Python → .NET edge that exists carries `X-Index-Feed-Key`, has no `[Authorize]` on purpose
and no `pos_id`, and its `pos-availability` route is a paginated feed of 200 rows rather than a
point lookup. The endpoint is identified, bounded and **not built**, recorded in
`openspec/DEFERRED_TASKS.md`, with the tool shaped so that it is a drop-in replacement.

The projection stores availability as `QTY_BUCKETS = {"0", "1-2", "3+"}`, and **those are
numerals**: emitting one would put a stock figure into a model's context, which is what the
service boundary forbids. The tool maps them to `sin_existencias`, `ultimas_unidades` and
`disponible`, with a **fourth** value, `sin_ambito`, for a principal carrying no point of sale
or a piece with no projection row. The fourth is the point: absence of a row is not a count of
zero, and collapsing them would fire the pivot to substitutes over a piece the shop can
actually sell. The observation also declares the **age** of the projection reading, and a stale
projection degrades it rather than failing it — degrade, never remove. The authority over stock
stays .NET's.

Two reads are added to `ProductSearchPort` and none is modified: one document by **SKU**, and
the availability bucket of **one** piece at one point of sale. Tools address a piece by SKU and
never by internal identifier — a SKU is stable, real and semantic, while an internal identifier
is an arbitrary string of digits nobody says at a counter, which is why the generation layer
already excludes it from everything a model is shown. The per-piece read exists instead of
`scope_buckets()` because that one returns the point of sale's entire assortment, of the order
of a thousand rows, to answer a question about one piece.

The embedding calls two of the tools legitimately make are counted in **a counter of their
own**, because the `usage.calls` figure the assistance layer publishes means *chat calls of one
request* and has tests asserting its ceiling; widening its meaning here would make a number
that is already reported mean two different things in two places.

**What this half cannot measure, and says so.** The tool descriptions have not been iterated
against a real model, because this half calls none. They are prompts, and a prompt is iterated
with measurement — that happens in C32b. The granularity of six may equally turn out to be
wrong, and the registry is left with its ports injected precisely so that regrouping a tool
costs neither the ports nor their suite.

## The sale assistant's agent loop (C32b)

C32a delivered the instrument and nobody to decide: six read-only tools, their frozen registry
and the read-only invariant. **This is the layer of decision, and it is the half that calls a
provider.** Of the four things the Proyecto Final evaluates about an agentic layer — the loop,
the hard budget, the read-only invariant and `partial: true` — C32a delivered one and this
delivers the other three.

`POST /v1/assist/agent` is a **route of its own** and `POST /v1/assist/sale` is untouched, field
for field and ceiling for ceiling. That is not caution: the comparison this capability exists to
enable runs both over the same set, and it would disappear if the loop replaced the pipeline
behind a flag. The two also have latency budgets that differ by a factor the deterministic
route's consumer cannot absorb — **5 s against 15 s**.

**The port has nowhere to put prose.** `AgentStep` returns the tool calls a turn requested and
what it cost, and declares no field able to carry free text: «the textual content of a loop turn
is discarded» is a property of the type rather than a rule somebody must respect. It is the same
choice C32a made when it verified the read-only invariant by introspecting the object graph
instead of trusting a boolean. The adapter records the length and a digest of what it threw
away, never the text.

**Six budgets, and three of them were fixed by measurement.** Iterations (5) and tool calls (8)
bound the steps; the provider-call ceiling (8) is **derived** from the constants of its three
stages rather than written as a digit. Tokens, accumulated context in characters and a
wall-clock deadline were placeholders until run `293fe5c6e470` — 204 requests over two model
arms — set them:

| Budget | p50 | p95 | max | Shipped |
|---|---|---|---|---|
| Prompt tokens (classifier + loop, what the budget compares) | 10.622 | 16.244 | 18.260 | **40.000** |
| Context characters (observations) | 1.847 | 4.709 | 17.053 | **30.000** |
| Wall clock (whole request, 8 s of it reserved for the argument) | 5,3 s | 9,0 s | 11,9 s | **15,0 s** |

The token row was first published as 12.870 / 18.781 / 23.210 — the request's whole
`prompt_tokens`, argument included, which runs after the loop and never reaches the budget.
Corrected by the independent verification of C32b, which also made the clock hold for the whole
request: it used to be checked only before a turn, which put the worst case at 31 s by construction.

Exhausting any of them serves the evidence gathered so far, marks the response `partial` and
names the budget in a `stop_reason` drawn from a closed vocabulary. **The reason is never
inferred from the counters**: five iterations does not say whether the fifth was the last one
needed or the one that ran out.

**The classifier is a guardrail here and not a router.** One classification per request, over the
turn being answered. A refusal short-circuits on any turn; the insufficiency verdict is
**ignored**, because «¿y en dorado?» judged alone reports a missing axis the conversation already
supplied; and the index verdict is **discarded**, because choosing where to look is the decision
the loop exists to make. The matrix C31 published stays intact, since what reaches the classifier
is still a standalone query.

**The transcript travels in the request and nothing is stored between calls.** Every turn is
enclosed in the same data delimiters C30b uses, **including the ones the client attributes to the
assistant** — the client composed the whole request and can forge that label — and the delimiters
are stripped from a turn's text so a client cannot close the block and write outside it. Three
caps bound it: 12 turns, 500 characters per turn and 4.000 in total.

**No availability label reaches the generation layer.** The label governs the loop's decision to
pivot and never the prose: authority over stock is .NET's, the projection can be minutes stale,
and one of the labels is literally a member of the stock-marker vocabulary the numeric gate
watches for. What the model then writes is **measured, not guaranteed** — `verify()` passes a bare
«disponible» — so the pass counts availability terms in every served argument. Substitutes do
reach the generation layer, marked with a closed-vocabulary value that tells them from catalogue
matches — which is why the argument prompt moves to `assist/v4` while **`assist/v3` stays on disk
untouched** and keeps serving the deterministic route. A piece the loop pivoted away from is not
also handed over as a match, and when the cap of eight pieces binds, further matches are dropped
before the substitutes.

> **C40 moves the deterministic route to `assist/v5`, and that was a prerequisite rather than an
> improvement.** `v3` ordered the model to write `{{price}}` and `{{stock}}` in **every** task,
> including the three free-query ones — where there is no anchored piece for `PitchPlaceholderResolver`
> to resolve them against, so the .NET gateway withdrew the argument and M1 would have shipped with
> no prose at all. `v5` removes price and availability from the free-query tasks, adds an uncovered
> task for a knowledge question the corpus cannot answer, and the integrity gate gains the hard
> cause `placeholder_in_free_query`, so a placeholder there withholds the argument instead of
> reaching a screen.
>
> **The measurement refuted the prediction that justified it, and the change stands anyway.** C30b
> counted `{{price}}` in 147 of 213 arguments and `{{stock}}` in 188 of 213, and the ticket
> extrapolated that most of M1's arguments would be withheld. Measured over 90 free-query
> generations on `v3`: **2 of 90 and 1 of 90** — a factor of thirty. What actually blocked M1 was
> not the placeholder rate but the gateway guard, which refused it **100 %** of the time. On `v5`
> the counts are 0 and 0, and 0 again over 71 responses driven end to end through .NET. Both
> artefacts are in `evals/results/c40-placeholders-*.json`.

**The wall-clock budget bounds the whole request.** The loop runs against 15 s minus the
argument's reserve (its two calls at their timeout, 8 s by default) and the turn in flight is cut
when that runs out; the bound is 15 s plus, at most, the tool calls of that turn, which are not
cancelled mid-query.

**Two traces.** On the wire, per iteration: the tool names, whether each succeeded and with what
cause, plus tokens and elapsed time — and **no argument and no observation content**, because a
consumer logs what it receives and a tool's arguments are the operator's question as the model
reformulated it. In process, the same plus arguments and observations, which is how the
evaluation harness consumes every other part of this service.

**Without a credential the route degrades instead of failing**, which is the fail-open, the
ablation and the rollback at once. The chain is `agent → assist → rag` and the link that won is
logged once per process as `stage=agent_client`; the classifier's key is deliberately not a link.

### What the provider pass measured

Run `293fe5c6e470`, 204 requests, two arms, **3,82 USD** and 3,4 h of wall clock. Full figures in
[the implementation report](../Documentos/Proyecto%20Final%20AIEng/informes/c32b-implementation-measurements.md);
every aggregate is recomputable from the artefact with no provider and no database:

```bash
uv run --system-certs python -m jbg_ai.evals.agent_sweep --rescore evals/results/c32b-agent-sweep-293fe5c6e470.json
```

- **The overhead against the deterministic pipeline is ×3,0, not the ×19 the design estimated**:
  0,0274 USD per request against ~0,0092, **each stage priced by its own model**. The classifier
  runs `gpt-4o` over ~3.300 prompt tokens, 0,0084 USD, on both routes. (The first figure published,
  ×7,6, priced the classifier at 0,00205 USD, a figure attributed to C31 that C31 never published;
  corrected by the independent verification of C32b.)
- **The cheap arm does not sustain tool selection.** `gpt-4o-mini` costs ×1,1 instead of ×3,0 but
  exhausts a budget in **66 % of requests against 1,2 %** — it does not know when to stop. The
  model multiplier is reversible in price and **not in behaviour**, which is what the design
  assumed was separable.
- **The context does not need compacting.** Median prompt tokens go from 1.974 on turn one to
  3.470 on turn five: shallow and roughly linear.
- **The availability label is consistent with governing the pivot, on one scenario per label.**
  `gpt-4o` pivots on 3 of 3 out-of-stock scenarios and on none of the three labels where pivoting
  would be the expensive mistake; the one under-pivot is the cheap arm's.
- **No invented tool names, no dead tool and no near-identical consecutive calls**, which answers
  the granularity question C32a left open.
- **The argument is withheld on 13,1 % of requests** on `gpt-4o`, 9,5 points of them for
  `dangling_citation`, against 2,2 % on the deterministic route. Identified, measured and **not
  closed**.

## Tests

```bash
cd ai-service
uv run --system-certs pytest
```

Tests inject required env / settings in-process, sign their own tokens, and are meant never to call LLM providers, embedding APIs, or production RDS. The stub tests additionally block socket connections to prove it. **Two exceptions are known and recorded in [`openspec/DEFERRED_TASKS.md`](../openspec/DEFERRED_TASKS.md)**, both found by the independent verification of C32b under a socket and database guard: the `db`-marked tests run against a real PostgreSQL through testcontainers whenever Docker is reachable (72 of them, skipped otherwise), and 11 tests of `tests/api/test_assist_generation.py` build the real classifier or argument client with a fake key and reach `api.openai.com` before degrading.

**C30b's generation tests are no exception, and the seam is deliberately low.** They build the
**real** `LiteLlmAssistClient` over a scripted `complete`, so the parsing, the timeout, the usage
extraction and its accumulation are all under test and only the socket is replaced — a stand-in
for the whole client would have tested the stand-in. The one measurement that does call a
provider lives outside the suite, in `python -m jbg_ai.evals.assist_sweep`, and is dated.

The suite mirrors the `src/jbg_ai/` package — `tests/api/`, `tests/config/`, `tests/data/`, `tests/migrations/`, and a
`tests/support/` for shared helpers (including `fake_llm.py`). [`tests/README.md`](tests/README.md) explains where a new test
goes and which folder each upcoming change lands in.

### Migration tests need Docker

`tests/migrations/` runs against a **throwaway pgvector container**, with a fresh database per test so the reversibility test cannot leak schema state into its neighbours. They are marked `db`:

```bash
uv run --system-certs pytest -m db        # only the database tests
uv run --system-certs pytest -m "not db"  # everything else
```

**Without a reachable Docker they are skipped, not failed.** There is no CI running the Python suite yet, so permanent red on a laptop would teach everyone to ignore red — which costs more than these four tests are worth. The flip side is real and worth saying out loud: a green run does not by itself prove the migration was exercised. Check that the `db` tests ran, not just that nothing failed.

These four tests exist to catch failures that produce **no error at all**: an HNSW index built with the wrong operator class is silently never used, Alembic's version table lands in `public` without complaint, and an orphaned type survives a revert to break the *next* upgrade weeks later.

## Explicit non-goals

- Stubs are replaced route by route as each change makes a route real — the agent loop included since C32b, see below. Enrichment is real when `STUB_MODE=false` (C09). Catalog index sync is real when `STUB_MODE=false` (C13). Product retrieval is real when `STUB_MODE=false` (C14), **hybrid since C21** and **fused in two stages since C25**: the two lexical lists are fused with each other and the result with the vector list under per-branch weights, so a branch's vote is the one declared however many of its lists matched. The scalar distance threshold 0.65 remains a floor rather than a discriminator, and C25 answers that with a relative per-query rule instead of moving it. Substitutes are real when `STUB_MODE=false` (C26), over the embedding the index already holds. **Sale assistance is real when `STUB_MODE=false` (C30a), writes its argument since C30b and routes since C31** — structure, rule warnings and citations; prose in **all three** modes, guarded by three deterministic checks; and, in the free-query mode, a classifier that runs **before any retrieval** and either admits the query, refuses it with one of **two distinct** reason codes, or answers it with a clarification question chosen in code. With **neither** `JPV_ASSIST_LLM_API_KEY` **nor** its fallback `JPV_RAG_LLM_API_KEY` it serves exactly C30a's response, and with none of the three classifier credentials it serves exactly C30b's — two ablations and two rollbacks, each of them a credential away. No `query_log`, `indexing/embeddings.py` unchanged, and `openapi.json` regenerated by **three descriptions** and no field — `intent` and `warnings` rewritten to name the new intent and refusal vocabularies, and one added to `clarification_question`
- No `POST /v1/retrieval/complementary` — later OpenAPI negotiation. `POST /v1/families/suggest` **exists since C18a**, which is the change that first called it; `POST /v1/families/audit` since C18b, for the same reason
- `ai.product_document` is written by C13 from the catalog feed; `ai.pos_projection` is **written by C22** from the POS availability feed; `ai.knowledge_document` and `ai.knowledge_chunk` are **written by C23**, by `python -m jbg_ai.indexing sync-knowledge`, from the corpus in `data/knowledge/`
- No `ai.query_log` (unassigned; the pipeline logs `stage=expand|embed|search|lexical|filters|fuse` with `trace_id` instead). The `ai.eval_*` tables **exist since C24** and are written only with `--persist`
- No reranking. C24 measured the number that would make it decidable and C25 re-measured it under the two-stage fusion — **two queries of forty-three** have a maximum-grade document inside the window a reranker would reorder but outside the five that are shown — and a cross-encoder at ~250 ms would spend 10-15 % of C16's budget for a ceiling of 2 % of the queries. Adding one is a `configs/v2-rerank.yaml` plus a run, which is the protocol being executable rather than rhetorical
- No recalibration of `JPV_RETRIEVAL_DISTANCE_THRESHOLD`, and **C25 settled that it was never the right lever**. Over 3.926 judgements the relevant documents reach a distance of 0,8008 and the irrelevant ones start at 0,3268, so the two populations overlap; per QUERY — the quantity that actually decides — the answerable best hits reach 0,7118 while the out-of-domain ones start at 0,4469, which is **containment and not partial overlap**: the impossible range sits *inside* the answerable one. No scalar can separate them, so C25 ships a **relative per-query rule** (`retrieval/abstention.py`) that reads the SHAPE of the distance profile, runs after the fusion and does not alter the candidate set. The scalar stays where it is **by decision rather than by deferral**
- **The agent loop EXISTS since C32b** and this is no longer a non-goal. The six read-only tools and the loop that drives them are both real: `POST /v1/assist/agent` runs up to five turns under **six budgets** — three of them fixed by a provider pass and not by judgement — returns `partial: true` with a closed-vocabulary `stop_reason` when one is exhausted, and carries the multi-turn transcript in the request because the service stores nothing between calls. What remains a non-goal is **evaluating the agent's quality**: the multi-turn, adversarial and injection scenarios are a later change, which writes its own sets and checks they do not overlap with C32b's `calibration-only` one. The point availability endpoint on the .NET side is still **identified, bounded and not built**, and so is the **timeout and circuit policy of the new route in the .NET layer** — the route has no consumer today — both recorded in `openspec/DEFERRED_TASKS.md` with their reasons
- No SQL access to schema `public`, ever
- No production deploy, SSM or `CREATE EXTENSION` on RDS. C17 delivered the **enriched health** — `GET /health` reports database reachability, indexed document count, whether the embedding provider credential is configured, and a contrast between the configured embedding model and the one recorded on the index rows, all without ever calling the provider — and deployed it to an **isolated demo account**, not to the shop's production account. The return annotation stays an open mapping, so `openapi.json` is unchanged
- No production tuning: `halfvec`, `hnsw.iterative_scan`, `CREATE INDEX CONCURRENTLY` and the `VACUUM`/`REINDEX` cycle are deliberate omissions at ~1,500 vectors, not oversights
- No edits to `indexing/embeddings.py`, frozen since C11. The POS feed **is** drained since C22, by `python -m jbg_ai.indexing sync-pos` — a command, not a route. *(Corrected by C41: it also said «not an in-process scheduler», and since C41 there is one — the command's documented cron was never installable, because it changed into a host directory against a containerised service. There is still no route.)*
- **The rotation figures describe the world at its horizon, not "today".** The synthetic world of C10 ends on **2026-08-23**, and since C22 the sales windows are counted against a declared reference instant (`IndexFeed:SalesAsOf`) rather than the wall clock. Two consequences worth stating plainly. It is what makes the aggregates **reproducible** — the same configuration and seed give the same figures on different days, which a ranking that reads `now()` never could, dataset horizon or not. And it means `sales_30d` describes the thirty days before that instant: peak summer for a world whose seasonality is extreme, so **23,54 %** of assigned pairs are non-zero rather than the 16,28 % a wall-clock reading gave on 2026-09-05. Neither figure is "the truth about today"; the declared one is the one that can be cited twice and mean the same thing. Removing the setting restores wall-clock behaviour, and with it the drift to zero that made the setting necessary

## Layout

```
ai-service/
  src/jbg_ai/
    api/
      main.py       # app factory, /health, router mounting
      auth.py       # HS256 decode + ServicePrincipal
      deps.py       # auth dependency, settings access, 501 guard
      middleware.py # trace_id correlation
      routers/      # retrieval, assist, inventory, enrich, index, evals
      schemas/      # frozen request/response contracts
    config/         # pydantic-settings + canonical OpenAPI profile
    db/             # lazy async engine, bounded pool
    stubs/          # deterministic fixtures
    data/           # C06b generate/ingest + C10 world/; not imported by api.main
    enrichment/     # C09 extractor: vocabs, size regex, LiteLLM port, auditor
    families/       # C18a grouping + C18b audit over persisted families; offline, writes nothing
    indexing/       # C11 source-text/embeddings (frozen) + C13 feed client, repo, orchestrator, sku_provenance.json
    retrieval/      # C14 vector retriever (embed max_attempts=1, <=> HNSW, body filters)
                    # + C20 query expansion: synonyms.py, query_synonyms.yaml, measure.py CLI
    knowledge/      # C23 second index: corpus.py (seven authoring rules), chunking.py (pure),
                    # indexer.py (uuid5 identity, idempotent), search.py (callable, no route;
                    # + C30a per-document exclusion and address_fragments, neither a route),
                    # sizing.py (D16 ring table), offline.py + measure.py (fixture, no provider)
    assist/         # C30a structured sale assistance: modes.py (three modes, structural intent),
                    # grounding.py (M2 addressing, general scope only), knowledge_scope.py (the
                    # asymmetric exclusion set), orchestrator.py, constants.py (closed warning
                    # vocabulary, allow-list, caps, violation causes, currency/stock markers)
                    # + C30b generation: prompt.py (versioned prompt AND the payload object the
                    # gate reads), schema.py (AssistPitch/UsedCitation, never on the wire),
                    # llm.py (own seam, returns usage), verification.py (the three checks),
                    # pitch.py (one repair, two policies). The client is injected, never built
                    # + C31 the entry guardrail: routing.py (RouteDecision projected onto the
                    # contract, the es-ES clarification catalogue chosen IN CODE, and the
                    # fail-open as a branch with a cause, never a mute except), router_llm.py
                    # (the C30b seam REPLICATED, not reused: one call, no retry, no repair).
                    # prompt.py gains PitchTask (six task sections) and FreeQueryPayload, the
                    # second payload shape — several candidates, and internal identifiers and
                    # retrieval scores excluded, because every numeral widens the whitelist
                    # + C32a the tool registry: tools.py (six read-only tools, the FROZEN
                    # name set, argument validation before any port is touched, failures as
                    # observations with a closed cause, and the read-only invariant checked by
                    # INTROSPECTION of the object graph rather than by a `writes` flag). A
                    # library wired to NO route: openapi.json does not move, and its consumer
                    # is C32b's loop. constants.py gains the qualitative availability
                    # vocabulary — the projection's buckets are numerals, so a bucket never
                    # reaches a model — with «sin ambito» as a fourth value that is not
                    # «agotado», plus the tool failure causes and the write-method vocabulary
                    # + C32b the agent loop: agent.py (the loop, six budgets, the evidence
                    # projection and the two traces), agent_llm.py (the port whose return type
                    # has NO field for prose), transcript.py (turns, three caps, every turn
                    # delimited). tools.py gains the evidence ledger; constants.py the budgets,
                    # the closed stop reasons and a fifth failure cause, `presupuesto_agotado`
    evals/          # C24 harness: golden.py (load + the composition validation that fails the
                    # load), pooling.py (adaptive depth), metrics.py (graded and binary),
                    # + C31 routing.py / routing_run.py (the 119-case manifest, five of its six
                    # classes REFERENCED and not copied, the confusion matrix, the two rates kept
                    # apart and the veto — which a degraded run cannot pass) and
                    # free_query_gate.py (the numeric gate of the free-query mode, measured
                    # APART from the anchored one, because they are not the same gate),
                    # configs.py + baselines.py (the two v0 replicas), cag.py (context-only),
                    # sweep.py (the directional sweep and its written rule), runner.py,
                    # report.py, repository.py (opt-in sink, imported by nobody upstream),
                    # cli.py (`uv run evals`), assist_sweep.py (C30b context-width sweep:
                    # dated, calls a provider, and the declared persistence exception)
                    # + C32b agent_sets.py (generates the load set) and agent_sweep.py (the
                    # two-armed pass: each stage priced by its own model, rows written as they
                    # are produced, and `--rescore` to recompute an artefact with no provider)
  prompts/          # versioned prompts: catalog-synth/v3 (C06b generate) + enrichment/v1 and v2 (extract; v2 in force since FIX1)
                    # + knowledge/v1: eight block prompts, one per generation block of the corpus
                    # + assist/v1 (C30b sale argument; system rules + one task block per mode,
                    #   and deliberately written without a single digit)
                    # + assist/v2 and v3 (C31: v3 is what `POST /v1/assist/sale` runs; v1 and v2
                    #   stay on disk because figures were measured against them) and router/v1-v3
                    #   (C31 intent classifier; v3 in force)
                    # + agent/v1 (C32b loop) and assist/v4 (C32b agent evidence; v3 untouched)
                    # + assist/v5 (C40: the free-query tasks stop writing placeholders) and
                    #   assist/v6 (C42: the AGENT task inherits that rule; v4 and v5 untouched,
                    #   and only AGENT_PITCH_PROMPT_VERSION moves: PROMPT_VERSION stays on v5)
  evals/            # the yardstick, versioned: golden/ (queries, judgements, frozen query vectors,
                    # criterion.md, pricing.yaml), configs/ (the five baseline configurations —
                    # globbed by load_all(), so nothing else may live there), assist/ (C30b's
                    # declared sweep sample), routing/ (C31's 119-case routing manifest),
                    # agent/ (C32b load set and calibration-only set) and results/ (C20 reach
                    # report, C21 arm comparison, C24 baselines + runs/<run_id>.jsonl, C30b sweep
                    # artefacts, C31 confusion matrices, C32b pass artefacts and their
                    # `.rescore.json`)
  migrations/
    bootstrap.sql   # one-off: extension, schema, dedicated role, grants
    env.py          # version table in `ai`; provisions before revisions run
    versions/       # hand-written revisions (no autogenerate)
  tests/            # mirrors src/jbg_ai — see tests/README.md
    api/            # contract, auth, stubs, OpenAPI snapshot
    config/         # settings and fail-fast validation
    data/           # C06b catalog CLI + C10 world/ (no provider sockets)
    families/       # C18a grouping and C18b audit (fakes; no provider sockets)
    indexing/       # C11 embeddings, C13 catalog drain, C22 POS drain (marked `db` where SQL)
    assist/         # C30a three modes, grouping, rule warnings, addressing (fakes; offline)
                    # + C30b prompt, the three checks, the repair policies and the wiring
                    # (the real client over a scripted `complete`; no socket)
                    # + C32b the loop, the transcript, the six budgets and the two traces
    knowledge/      # C23 corpus rules, chunking, sizing, indexer, search, measurement
                    # + C30a exclusion filter and addressing by identity
    migrations/     # schema, indexes, reversibility (marked `db`)
    retrieval/      # C14 vector retriever + C20 expansion (fakes; no provider sockets)
    support/        # shared helpers and injectable fakes
  alembic.ini       # no connection string: read from DATABASE_URL
  openapi.json      # versioned contract snapshot
  Dockerfile
  pyproject.toml
```
