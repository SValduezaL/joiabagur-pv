# OpenSpec Deferred Tasks

This document tracks all tasks that have been deferred to future phases or epics, along with explanations for why they were deferred.

## Active Change: `add-sales-and-image-recognition`

### Phase 2 - Offline Capabilities (Image Recognition)

**Status:** Documented in specs but NOT implemented in MVP

**Deferred Tasks:**
1. **Offline model usage** - Cached model when no network connection
2. **Progressive Web App offline capabilities** - Full offline support for PWA
3. **Push notifications for new model versions** - Notify users when new model is available
4. **IndexedDB model caching** - Store model locally for offline inference
5. **Offline inference execution** - Run ML inference without network connectivity
6. **Background model updates** - Download new models in background during idle time
7. **Cache invalidation logic** - Manage cached model version lifecycle

**Why Deferred:**
- MVP focuses on core online functionality
- Offline scenarios add significant complexity (state management, cache invalidation, conflict resolution)
- Network connectivity is expected in retail POS environments
- Simplifies MVP UX and reduces development time
- Can be added incrementally without breaking existing functionality

**Reference:** `openspec/changes/add-sales-and-image-recognition/proposal.md` lines 63-69

---

### Phase 2 - Model Configuration & Analytics

**Deferred Tasks:**
1. **Configurable confidence threshold** - Admin UI to adjust threshold (20%-80% range)
   - Currently fixed at 40% in MVP
   - **Why:** Need real-world usage data to determine optimal threshold before making it configurable

2. **Precision metrics calculation** - Track model accuracy over time
   - Currently returns `null` in MVP
   - **Why:** Requires inference logging infrastructure and historical data collection

3. **Analytics logging** - Log inference metrics (inference time, confidence scores)
   - Optional in MVP
   - **Why:** Not critical for MVP functionality, adds storage/complexity

4. **AIInferenceLog table** - Store inference history for analytics
   - **Why:** Requires database schema changes and logging infrastructure

**Reference:** 
- `openspec/changes/add-sales-and-image-recognition/specs/image-recognition/spec.md` lines 165, 437
- `openspec/changes/add-sales-and-image-recognition/tasks.md` lines 140, 235, 260

---

### Phase 2 - Model Retraining Automation

**Deferred Tasks:**
1. **Automatic model retraining triggers** - Retrain when products added/removed or photos updated
   - Currently manual trigger via admin endpoint
   - **Why:** Adds complexity (monitoring, failure handling, cost control). Manual retraining sufficient for MVP with ~500 products

2. **Scheduled retraining** - Nightly retraining if photos changed in last 24h
   - **Why:** Unnecessary for MVP scale, adds infrastructure complexity

3. **Incremental learning** - Add new products without full retrain
   - **Why:** Advanced ML technique, not needed for MVP scale

4. **A/B testing with version pinning** - Deploy new model to subset of users
   - **Why:** Over-engineering for MVP, adds significant complexity

**Reference:** 
- `openspec/changes/add-sales-and-image-recognition/design.md` lines 81, 265-268, 658

---

### Phase 2 - Frontend Enhancements

**Deferred Tasks:**
1. **CSV export for sales history** - Download sales data as CSV
   - **Why:** Nice-to-have feature, not critical for MVP

2. **Progressive model download** - Download model in chunks/streaming
   - **Why:** Simplifies MVP UX, adds state complexity. Current approach (full download) acceptable for ~14MB model

**Reference:** 
- `openspec/changes/add-sales-and-image-recognition/tasks.md` lines 248, 623

---

## Archived Changes - EP3 Integration Tasks

### Payment Method Management - Sales Integration

**Status:** Deferred until EP3 (Sales Registration) is implemented

**Deferred Tasks:**
1. **Integrate validation into sale creation workflow** - Use payment method validation when creating sales
2. **Return appropriate error messages for invalid payment methods** - Sales-specific error handling
3. **Prevent deactivation of payment methods assigned to active sales** - Business rule enforcement
4. **Test sales validation with payment methods** - Integration tests
5. **Test sales creation with valid/invalid payment methods** - End-to-end tests
6. **Sales validation documentation** - API documentation updates

**Why Deferred:**
- These tasks require the sales system (EP3) to be implemented first
- Payment method management was built as standalone capability
- Integration will be completed when sales registration is implemented
- **Note:** Sales registration is now being implemented in `add-sales-and-image-recognition` change

**Reference:** 
- `openspec/changes/archive/2026-01-07-add-payment-method-management/tasks.md` lines 46-47, 56, 74, 78, 108, 114

---

## Archived Changes - Documentation Tasks

### Point of Sale Management - System Documentation

**Status:** Deferred to post-MVP documentation phase

**Deferred Tasks:**
1. **Update data model documentation** - Full ERD and schema documentation
2. **Update architectural diagrams** - C4 model updates, sequence diagrams

**Why Deferred:**
- Documentation tasks are non-functional requirements
- Can be completed after MVP is stable
- Focus on implementation over documentation for MVP phase

**Reference:** 
- `openspec/changes/archive/2026-01-07-add-point-of-sale-management/tasks.md` lines 76-77
- `openspec/changes/archive/2025-12-14-add-point-of-sale-management/tasks.md` lines 76-77

---

### Payment Method Management - Documentation

**Deferred Tasks:**
1. **Update data model documentation** - Full ERD updates
2. **Sales validation documentation** - Integration documentation (requires EP3)

**Why Deferred:**
- Same rationale as POS management documentation
- Sales validation docs require EP3 implementation

**Reference:** 
- `openspec/changes/archive/2026-01-07-add-payment-method-management/tasks.md` lines 106, 108

---

## Archived Changes - Testing Tasks

### Product Catalog Search - Integration Tests

**Status:** Deferred (lower priority)

**Deferred Tasks:**
1. **Integration tests for GET /api/products** - Pagination, sorting, filtering
2. **Integration tests for GET /api/products/search** - Role-based filtering
3. **Integration tests for DELETE /api/products/{id}/photos/{photoId}** - Admin-only endpoint
4. **Integration tests for PUT photo management endpoints** - Admin-only endpoints

**Why Deferred:**
- Lower priority compared to unit tests and critical path integration tests
- Functionality is covered by unit tests and manual testing
- Can be added incrementally

**Reference:** 
- `openspec/changes/archive/2026-01-08-extend-product-catalog-search/tasks.md` lines 97-100

---

## Summary by Category

### By Reason for Deferral:

1. **Requires Future Epic/Feature** (EP3 Sales System)
   - Payment method sales integration
   - Sales validation tests

2. **MVP Simplification** (Phase 2 Enhancements)
   - Offline capabilities
   - Model retraining automation
   - Advanced analytics

3. **Non-Critical Features** (Nice-to-Have)
   - CSV export
   - Progressive model download
   - Additional integration tests

4. **Post-MVP Documentation**
   - System documentation updates
   - Architectural diagrams

### By Priority:

**High Priority (Implement Next):**
- Payment method sales integration (when sales system is complete)
- Offline capabilities (if network reliability becomes issue)

**Medium Priority:**
- Model retraining automation (when catalog grows significantly)
- Configurable confidence threshold (after collecting usage data)

**Low Priority:**
- Analytics logging
- CSV export
- Additional integration tests
- Documentation updates

---

---

## Active Change: `add-frontend-assisted-search-panel` (C16)

### Restore the retrieval time budget to 800 ms

**Status:** Budget temporarily raised from **800 ms to 2500 ms** in
`backend/src/JoiabagurPV.API/appsettings.json` and in the default of
`AiGatewayOptions.RetrievalTimeoutMs`.

**Why it was raised.** Measured on 2026-08-29 against the seeded world with real retrieval
(`STUB_MODE=false`, 1.200 documents with embeddings):

| Budget | Outcome |
|---|---|
| 800 ms (design §6.4) | `ai_gateway_call_failed timeout 1956 2` → `LexicalFallback` on **every** search |
| 2500 ms | Served assisted in **0,86 s** and **0,31 s** end to end |

At 800 ms the assisted path never serves: the feature would ship looking healthy —
HTTP 200, results on screen — while silently answering from the degraded lexical searcher
every single time. That is the failure mode C15 designed the origin column to make visible,
and it would have reached production undetected.

**The actual cause, which this does not fix.**
[`ai-service/src/jbg_ai/api/routers/retrieval.py`](../ai-service/src/jbg_ai/api/routers/retrieval.py)
constructs a `LiteLlmEmbeddingClient` **per request**, so the in-memory embedding cache frozen
in C11 is born empty and dies with the response. Retrieval never gets a cache hit, and every
search pays a full cold round trip to the embedding provider. The debt was recorded when C15
was designed and assigned to **C21 or C22**, which already work inside `retrieval/`; the fix is
roughly three lines in `main.py` making that client a singleton.

**Step 1 is paid. C21 (`add-hybrid-search-rrf`) made the client a process singleton**, and it
was not the "three lines in `main.py`" this note assumed. `InMemoryEmbeddingCache` is a `dict`
with no ceiling and no TTL: harmless per request, since it was born empty and died with the
response — which is also *why* retrieval never got a hit — and a lifetime leak as a singleton
keyed by every distinct operator query (~13 KB per vector) inside a container capped at
512 MiB that already uses 232. `indexing/embeddings.py` stays frozen by C11, so the bound was
injected through its existing `cache` constructor field: `retrieval/cache.py` holds a bounded
LRU, `api/main.py` builds the client once, `api/routers/retrieval.py` resolves it from
`app.state`, and `test_embeddings_module_is_unchanged` pins the freeze by content hash.

**Steps 2 to 4 stay open, and they are a change of their own** — they need a demo deploy, a
cold and warm re-measurement and a funnel confirmation, which is a different kind of work and
a different risk from anything C21 touches.

1. ~~Make the embedding client a singleton in the AI service.~~ **Done in C21.**
2. ~~**Measure again**, both cold and warm.~~ **Done on 2026-09-02**, against the local index
   of 1.168 documents and the real provider, through the full C21 pipeline (expansion, both
   lexical lists, embedding, vector branch, fusion, demoting filters), six operator queries:

   | | min | media | max |
   |---|---:|---:|---:|
   | **Cold** (first time each text is seen) | 273 ms | 475 ms | **1328 ms** |
   | **Warm** (the singleton's cache hits) | **74 ms** | **76 ms** | 78 ms |

   **The singleton works, and the figure that matters is 76 ms** — an order of magnitude inside
   the 800 ms budget, against 170-383 ms warm on the demo host before it existed. The cache
   removes the provider round trip entirely on a repeated query text.

   **What it does not remove is the first call for each distinct text**: 1328 ms on
   `criollas de oro`, still well over 800 ms and consistent with the 1707 ms measured on the
   demo host. So the budget is now comfortable for a shop that searches for similar things all
   day and still blown by a genuinely new query.

   These figures are a **laptop against a local database**, not the demo environment. They say
   the singleton was worth paying for; they do not settle the revert, which needs step 3
   measured where the operator actually is.
3. Put `RetrievalTimeoutMs` back to **800 ms** in `appsettings.json` **and** in the
   `AiGatewayOptions` default — the two must not drift apart. **Decide with the cold tail in
   hand**: at 800 ms a first-ever query text still degrades to the lexical searcher. That may
   now be the right trade — C21's own lexical branch is what answers, and it scores 219/240
   against the vector branch's 157/240 — but it is a decision to take deliberately and to
   confirm with the funnel, not a consequence of the cache working.
4. Confirm with the funnel log that `Origin=Assisted` and not `LexicalFallback`.

**Why not leave it at 2500 ms.** A budget that no longer bites stops being a budget. With the
single retry of C03 the worst case before degrading becomes roughly **five seconds** of an
operator standing at the till waiting for an answer that will arrive degraded anyway — worse
for the shop than failing fast into the lexical searcher. The 800 ms of §6.4 exists to bound
that wait, not to be comfortable.

**References:** `openspec/changes/add-frontend-assisted-search-panel/qa.md` §6 ·
[design §6.4](../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) ·
C15 `design.md`, *Risks / Trade-offs*

---

## Active Change: `add-ai-service-deployment` (C17)

### Splitting `/health` into liveness and readiness probes

**Status:** Deliberately NOT done in C17. The enriched report lives on the existing `GET /health`
with its return annotation unchanged (an open mapping), so `ai-service/openapi.json` — the
contract frozen with the .NET side — does not move and `test_openapi_snapshot_is_stable` stays
green.

**Why it is deferred rather than forgotten.** The current endpoint answers three different
questions for three different consumers: the container health check ("is this process alive?"),
post-deployment verification ("is this environment fit to show?"), and the administrator card
("what is wrong right now?"). That is one endpoint doing the job of two, and it is affordable
only while nothing acts on the answer automatically.

**The three triggers. Split when ANY ONE of them becomes true, and not before:**

1. **Something can restart the container based on the answer.** Today nothing does: Compose's
   `restart: unless-stopped` reacts to the process exiting, not to a health status. The moment an
   orchestrator is allowed to recycle the container on an unhealthy report, a degraded database
   turns into a restart loop — the probe causing the outage it reports.
2. **The expensive part stops being cheaply cacheable.** The report is reused for ten seconds,
   which is what keeps repeated probing off a connection pool capped at five for the whole
   system. If a future field cannot be cached that way, liveness must stop paying for readiness.
3. **The service is deployed to the shop's real account.** A different blast radius and a
   different operator justify a different contract.

**What splitting costs, and why that cost is correct.** A new route regenerates `openapi.json`
and breaks its drift test. That is the right outcome, not an obstacle: the boundary with the .NET
side will genuinely have moved, and the test exists to make that visible rather than silent.
Agree the change with whoever owns the .NET client, then regenerate with the README one-liner.

**References:** C17 `design.md` D12 · `openspec/specs/ai-service-runtime/spec.md` ·
S16 *Observabilidad* ("no confundáis el latido con la vigilancia")

### The retrieval budget, measured on the demo environment

**Status: measured on 2026-08-30. The conclusion is "do not revert yet", and the reason is
sharper than before.**

Four `ai_gateway_call_completed` latencies over four distinct queries, from the demo host in
`eu-west-1` against the real provider, with `aiAvailable: true` on all four:

| Query | Gateway latency | End to end |
|---|---|---|
| anillo de plata para regalar | 383 ms | 0,99 s |
| pendientes de oro para una boda | **1707 ms** | 1,98 s |
| collar con perlas elegante | 170 ms | 0,41 s |
| pulsera de plata sencilla | 184 ms | 0,40 s |

**What this changes.** The 2500 ms budget is not being consumed in the normal case: warm calls
land at **170–383 ms**, four to fourteen times inside it. Measured from a laptop during C16 the
same path degraded on *every* search at 800 ms; from an instance in the same region as nothing in
particular but with a better route to the provider, the ordinary case is comfortable.

**What this does NOT change.** One call in four cost **1707 ms** — still more than double the
800 ms of §6.4. So reverting the budget today would degrade roughly a quarter of searches to the
lexical path. The debt is the same one recorded above: the AI service builds a
`LiteLlmEmbeddingClient` per request, so the in-memory cache never hits and any request may pay a
full cold round trip. Distance to the provider changed how *often* that hurts, not whether it
happens.

**Therefore:** leave `RetrievalTimeoutMs` at 2500 ms. Make the embedding client a singleton in
the change that owns `retrieval/`, measure again, and only then consider 800 ms. These figures
are the new baseline to beat.

**References:** C17 `qa.md` · C16 `qa.md` §6 · measured with the demo corpus of 1200 documents

### Instance sizing, measured (C17 §10.3) — no action needed

`docker stats` on the four containers with the corpus loaded and searches served, 2026-08-30:

| Container | Memory | Of its limit |
|---|---|---|
| `jbg-demo-ai` | 232,5 MiB | **45 % of its 512 MiB cap** |
| `jbg-demo-api` | 108 MiB | — |
| `jbg-demo-postgres` | 93 MiB | — |
| `jbg-demo-proxy` | 11,7 MiB | — |

Host: 689 MB used of 1909, **917 MB available**, and **no swap configured**.

**`t3.small` is right-sized and the 512 MiB cap on the AI service is well chosen**: high enough
that ordinary operation never approaches it, low enough that the container dies before the host
does — which is the whole point of D18. No resizing, and the swap file the design offered as a
mitigation is not needed at these numbers. Re-measure if the corpus grows by an order of
magnitude or if a generative route lands.

> **Re-measured on 2026-09-22, with the generative route live (C34).** `docker stats --no-stream`
> before and after the ten sale assistances the rate window allowed — **6 + 4, not ten in a row**:
>
> | Container | Idle | After the ten generations | Of its limit |
> |---|---|---|---|
> | `jbg-demo-ai` | **269,9 MiB** | **269,9 MiB**, unchanged | **52,7 % of 512 MiB** |
> | `jbg-demo-api` | 235,2 MiB | 238,6 MiB | — |
> | `jbg-demo-postgres` | 96,6 MiB | 96,8 MiB | — |
>
> Host: 751 MB of 1909 used, 836 available, still **no swap**. The ~37 MiB above the 232,5 MiB of C17
> are the generative and router clients plus the corpus; **generating moves nothing**, because the
> model runs at the provider. **`t3.small` and the 512 MiB cap remain right-sized.**
>
> **And the tokens-per-minute quota is not the operative constraint here**, contrary to what the C32b
> entry suggests for the agent route: the ten generations the window allowed all came back `generated`,
> with no provider degradation. What binds first is the card's own limit — 10 per minute per user,
> answering 429 from the eleventh request of the window. **They were not ten in a row**: 6 from the
> piece-by-piece probe plus 4 of a burst of 12, the other 8 refused with 429, and both `docker stats`
> readings span the two phases. Reaching the quota would take several operators at once, and that
> remains unmeasured.

---

## **Este repositorio no tiene CI** — causa ya documentada, confirmada el 2026-08-30

**Estado: hallazgo, no tarea de C17.** Merece un change propio; se anota aquí para que no
se pierda.

> **La causa no es nueva.** [`Documentos/testing-backend.md`](../Documentos/testing-backend.md)
> ya la registraba en su sección *Estado de la suite*: `test-backend.yml` sólo dispara en
> `main` y `develop`, «y **todo el Proyecto Final de IA se está construyendo en `ai-eng`** y
> sus ramas de change». Lo que C17 aporta no es el descubrimiento sino la **confirmación
> empírica** de su consecuencia extrema, que hasta ahora se intuía: no es que se ejecute poco,
> es que **no se ha ejecutado nunca**.

`test-backend.yml` y `test-frontend.yml` **no se han ejecutado nunca**, ni una vez:

```
gh run list --workflow=test-backend.yml   -> NUNCA SE HA EJECUTADO
gh run list --workflow=test-frontend.yml  -> NUNCA SE HA EJECUTADO
```

Ambos disparan sobre `branches: [main, develop]`, y **ninguna de esas dos ramas existe**. Las
del repositorio son `master`, `ai-eng` —donde se integra de verdad: el PR #21 mergeó ahí— y
`demo`. Los workflows están bien escritos, sus filtros de ruta son razonables, y son inertes.

Es la misma firma que C17 encontró siete veces en un día: algo que aparenta funcionar y no se
ejecuta. Aquí el coste acumulado es mayor que el de cualquiera de aquéllos, porque significa
que **ningún cambio de este proyecto ha pasado por una comprobación automática antes de
integrarse**.

### Lo que hay que hacer, y en qué orden

1. **Corregir las ramas**: `pull_request: branches: [ai-eng, master]` más `push` sobre las
   mismas. Es el arreglo de una línea que enciende la CI.
2. **Sólo entonces**, decidir si la CI puede ser una puerta. Hoy **no puede**, y el motivo
   está en `CLAUDE.md`: la suite de backend arrastra **53 fallos preexistentes** y la de
   frontend **116**. Una puerta sobre una suite roja no es una puerta; es un bloqueo
   permanente que alguien terminará saltándose. Poner la CI en verde es el trabajo de verdad,
   y es un change en sí mismo.
3. Mantener la **lista blanca** (`paths:`) en los tests, al contrario que en los despliegues.
   Un test que sobra cuesta minutos; un despliegue que falta deja el entorno corriendo código
   viejo en silencio. Los dos filtros fallan hacia lados distintos a propósito.
4. Al hacer la CI obligatoria, cuidado con la trampa conocida: un workflow **omitido** por
   filtro de rutas nunca reporta su estado, y una comprobación requerida que no reporta deja
   el PR bloqueado para siempre. Se resuelve con un trabajo acompañante que siempre se ejecuta
   y publica el mismo nombre de comprobación.

### Y el despliegue de producción, que sigue sin filtro

`deploy-aws-ec2.yml` redespliega la tienda ante **cualquier** cambio, incluido uno que sólo
toque documentación. Se le aplica el mismo razonamiento que a `deploy-demo.yml`, pero **C17 no
lo toca**: su propia especificación exige que el flujo de despliegue de producción quede
inalterado, y hay un escenario que lo verifica. Corresponde a otro change.

---

## FIX1 — lo que la corrida dejó anotado y sin ficha

Archivado el 2026-09-05 como `2026-09-05-fix-enrichment-vocabulary-gaps`. Las tres cosas que su
informe deja abiertas, y por qué ninguna entró en el change:

### `filigrana` sigue siendo una laguna, y de otro eje

Es la única exclusión del overlay de C20 que queda abierta, y **ahora es el ejemplo al que apunta
el test guardián** `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap`. Alcanza 66
documentos por sí sola, repartidos por todos los tipos de pieza —es una técnica, no una pieza—, y
una de las 12 búsquedas registradas de operador es literalmente «anillo de filigrana tradicional
menorquina».

**Por qué se aplazó:** cerrarla significa añadir un canónico a **`style_tags`**, que es otro eje con
sus propias puertas de cobertura en el auditor, y no cuesta lo que cuesta una laguna de
`piece_type`. No tiene change asignado: FIX1 cerró las cuatro de `piece_type` y dejó ésta declarada
como abierta en su propio motivo, dentro de las `exclusions` del overlay.

**Referencia:** `ai-service/src/jbg_ai/retrieval/query_synonyms.yaml`, sección `exclusions`.

---

### El endpoint que agregue los tipos realmente presentes en el surtido

FIX1 midió lo que cuesta mover el vocabulario cerrado: **cinco ficheros, cuatro tests fijados, dos
lenguajes y dos specs vivas, para cuatro términos**. Nadie puede hoy responder «qué tipos de pieza
hay de verdad en el surtido» sin consultar la base a mano.

**Por qué se aplazó:** es una capacidad nueva, no la corrección de una laguna. **Sigue sin ficha
propia** en el plan de changes.

**Referencia:** `Documentos/Proyecto Final AIEng/informes/fix1-vocabulary-gaps-measurements.md` §8.

---

### `Llavero Cape Nao` Grande y pequeño podrían formar familia

Al ganar `llavero` como tipo, **comparten `piece_type` por primera vez** (SKU416 y SKU417), que es
la condición que el agrupador de C18a necesita para proponerlos como familia.

**Por qué se aplazó:** correr la sugerencia de C18a estaba explícitamente fuera del alcance de FIX1,
que no toca `families/`. Es una pasada del agrupador, no un cambio de código.

**Referencia:** `Documentos/Proyecto Final AIEng/informes/fix1-vocabulary-gaps-measurements.md` §8.

---

## C28 — lo que la revisión de perfiles destapó y no puede arreglar

Anotado el 2026-09-13, durante el apply de `add-profile-review-ui-and-metrics`. Los dos hallazgos
salieron de medir antes de revisar, no de la sesión, y ninguno cabe en ese change.

### `StoneType` guarda una piedra y hay piezas que llevan dos

Medido sobre los 1.168 perfiles `Approved`: de los **434 productos cuyo texto nombra al menos una
piedra del vocabulario, 14 nombran dos**, y en los catorce el extractor eligió una y descartó la
otra. Es el **3,2 %**, y no es un fallo del extractor: en una columna escalar no cabe la segunda
piedra por bien que la lea.

```
  SKU1140  esmeralda     <- el texto dice esmeralda y zafiro
  SKU1144  topacio       <- diamante y topacio
  SKU579-581  cuarzo     <- cuarzo y esmeralda   (tres productos)
  SKU582-584  onix       <- citrino y onix       (tres productos)
  SKU1148  onix          <- onix y turquesa
  SKU1149  amatista      <- amatista y nacar
  SKU593   topacio       <- diamante y topacio
  SKU795   amatista      <- amatista y topacio
```

La asimetría con `materials` es lo que lo hace visible: aquel es `jsonb` y admite lista —una pieza
es rutinariamente plata *y* baño de oro— mientras que `StoneType` es `character varying`. La
pantalla de revisión ofrece un solo valor porque refleja el esquema, no porque lo restrinja.

**Por qué se aplazó:** cerrarlo es **una migración** —`StoneType` → `StoneTypesJson`— y C08 reservó
el almacenamiento de esta capacidad precisamente para que C28 no necesitara ninguna. Y arrastra el
**contrato congelado**: `AiProposedProfile.StoneType` pasaría de `AiProposedText?` a
`AiProposedList`, lo que mueve `openapi.json` y obliga a acordar el cambio con el lado .NET. Son
dos invariantes del change a la vez. **Sin ficha asignada**, y probablemente fuera del alcance del
Proyecto Final.

**Referencia:** `backend/src/JoiabagurPV.Domain/Entities/ProductAiProfile.cs:50` ·
`backend/src/JoiabagurPV.Application/DTOs/Ai/AiEnrichResponse.cs:40`

---

### `vidrio` falta en `materials`, y alcanza 67 productos

**Lo encontró la sesión de revisión, no una consulta.** La exploración de C28 midió omisiones
buscando los términos que **ya estaban** en el vocabulario —`hilo`, `perla`, `plata`, `acero`,
`latón`— y por construcción no podía ver un hueco de cobertura. Una persona leyendo 204 productos sí.

| término | campo | anotados en la sesión | **en el corpus** |
|---|---|---:|---:|
| `vidrio` | `materials` | 13 | **67 (5,6 %)** |
| `naturaleza` | `style_tags` | 8 | **38** |
| `platino` | `materials` | 11 | 20 |
| `cobre` | `materials` | 9 | 15 |
| `cuarzo rosa` | `stone_type` | 1 | 7 |
| `turmalina` | `stone_type` | 1 | 5 |
| `titanio` · `bronce` · `marfil` · `hierro` · `madera` | `materials` | 7 | 1-5 cada uno |

`naturaleza` es el **segundo hueco conocido de `style_tags`**, junto al `filigrana` que FIX1 dejó
abierto más arriba en este documento y que alcanza 66 documentos. Ese eje empieza a tener un caso
propio.

Dos anotaciones **no son huecos de cobertura** y conviene no mezclarlas: `cuarzo rosa` es un
problema de **granularidad** —`cuarzo` sí está en `stone_type`, y la ficha de conocimiento ya
describe el rosa como una de sus variedades—, y `nácar` anotado bajo `materials` es una **frontera
de campo**, porque `nacar` está en el vocabulario de `stone_type`: la pregunta es si el nácar es el
material de la pieza o la piedra que lleva.

**Por qué se aplazó:** el mismo motivo que el término siguiente, y cuantificado en el informe —
añadir estos términos sacaría 21 de los 122 productos del estrato A y unos 30 de los 284 del B,
cambiando el lote que produjo la cifra publicada.

**Referencia:** [c28-implementation-measurements.md](../Documentos/Proyecto%20Final%20AIEng/informes/c28-implementation-measurements.md) §5

---

### El extractor emite `plata` cuando el texto dice `platino`

`platino` y `cobre` no están en el vocabulario cerrado de `materials`, que tiene nueve términos.
Medido sobre los productos cuyo texto dice `platino` y **nunca** dice `plata`:

| qué extrajo | productos | confianza | estrato |
|---|---:|---|---|
| `["plata"]` o `["oro","plata"]` | **11** | 0,45 | B |
| `[]` | 9 | 0,20 | A |

Los once son una alucinación: el modelo lee «platino», no lo encuentra entre los nueve canónicos y
emite el metal más parecido que conoce. **El sistema de confianza los cazó a los once** —0,45 es
literalmente *«lo afirmó sin que la frase esté en el texto»*— lo que confirma de paso la predicción
falsable del diseño de C28: las retiradas se concentran en el estrato B. `cobre` aparece en 15
productos, los 15 en el estrato A.

**Por qué se aplazó:** ampliar el vocabulario **cambiaría el lote a mitad de medición**.
`confidence.py` calcula el span contra el vocabulario, así que añadir los dos términos movería
hasta 24 productos fuera del estrato A —que solo tiene 122— y los 180 dejarían de ser los 180 que
produjeron la cifra publicada. Además obliga a re-enriquecer, y re-enriquecer reescribe
`ProposedProfileJson`, que es la columna contra la que se mide la tasa de corrección.

**Lo que costaría, completo:** los dos términos en `vocabularies.yaml`; sus fichas
`material-platino.md` y `material-cobre.md`, que **no son opcionales** —la spec viva de
`knowledge-corpus` exige exactamente una ficha por material canónico y
`test_every_canonical_material_has_exactly_one_sheet` lo hace fallar nombrando el término que
falta—; reindexar el corpus de conocimiento; y re-enriquecer con versión de prompt nueva, como
FIX1 hizo con sus 22 productos en `enrichment/v2`.

**Orden obligatorio:** la tasa de C28 tiene que estar **publicada antes**. Re-enriquecer primero
mezcla dos poblaciones y ninguna de las dos cifras significa lo que dice.

**Cautela heredada de la exploración:** igual que con `hilo`, «baño de platino» o «filigranas de
cobre» no son necesariamente una pieza *de* platino o *de* cobre. Por eso el registro de huecos de
la pantalla guarda el SKU y no solo el término: el change que amplíe la lista mira los textos
reales antes de decidir.

**Referencia:** `openspec/specs/knowledge-corpus/spec.md` §*Every canonical material has exactly
one sheet* · `ai-service/tests/knowledge/test_corpus_rules.py:257`

---

## C30b — la demo no genera argumentario, y lo que hace falta para que genere

**Estado:** **CERRADA el 2026-09-22 por C34.** Los cuatro pasos hechos, el parámetro creado y la demo
desplegada y verificada: `stage=assist_client … credential=assist` en el log y una asistencia real con
`pitchStatus: generated` y el precio y el stock resueltos en el texto («disponible por 250,00 € y
cuenta con 5»). Evidencia en el §13 del [QA de C34](changes/archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/qa.md).
· **Abierto el:** 2026-09-14 · **Zona:** `deploy/demo/`, `compose.demo.yaml`
**No es un fallo:** es el comportamiento declarado, verificado y con test.

> **Lo que C34 hizo con esta entrada** *(2026-09-21)*:
>
> | Paso | Estado |
> |---|---|
> | 1 · `/jbg-demo/ASSIST_LLM_API_KEY` como `SecureString` | **hecho el 2026-09-22**, versión 1, verificado sin descifrarlo |
> | 2 · `deploy.sh` lee el parámetro **sin `:?`** y con `\|\| true` | **hecho**, y además registra `Generation credential: present/absent` —si está, nunca qué es— |
> | 3 · `JPV_ASSIST_LLM_MODEL` y `JPV_ASSIST_LLM_API_KEY` en `jbg-demo-ai` | **hecho**. La clave se interpola como `${ASSIST_LLM_API_KEY:-}`, con valor por defecto vacío, para que `docker compose config` resuelva también sin el script de despliegue; vacía equivale a no configurada (`blank_assist_llm_key_is_unset`) |
> | 4 · El parámetro en la lista de secretos manuales del runbook, marcado como el único opcional | **hecho**, con una §5.6b de comprobación del card |
> | + `AiSalesAssist__EnabledByDefault: "true"` y `AiGateway__AssistTimeoutMs: "10000"` en la API | **hecho** — sin el interruptor el card saldría siempre degradado y sin llamar a la IA |
>
> **Dos precisiones a lo que dice la entrada de abajo.** La primera: `prompt_version` ya no pasa a
> `assist/v1` sino a la versión vigente para M2/M3, **`assist/v3`**. La segunda: con la clave
> puesta, el log mostrará **también** `stage=router_client … credential=assist_fallback`, porque el
> enrutador de C31 repliega a esta clave cuando no tiene la suya. Es esperado y no gasta nada: el
> enrutador sólo corre en M1 —consulta libre sin pieza—, que C34 no expone.

### Qué pasa hoy

`compose.demo.yaml` **no pasa ninguna credencial de proveedor generativo** al servicio
`jbg-demo-ai` — comprobado, no hay `JPV_RAG_LLM_*` ni `JPV_ASSIST_LLM_*` en el fichero. Así que
la demo sirve `POST /v1/assist/sale` con `pitch: ""`, `prompt_version: null` y `usage` a cero:
exactamente la respuesta de C30a, con **200** y no 503.

Eso es correcto por diseño y no hay que "arreglarlo" con prisa: un despliegue sin credencial
sirve la mitad estructurada, que es la que tiene grupos, avisos y citas resolubles. Es también
el *rollback* de C30b. Lo que falta es **decidir** que la demo enseñe la capa de generación, que
es media hora de trabajo y una clave.

### Lo que hay que cambiar, y lo que NO

**Corrección de una nota anterior de este mismo change:** el informe de implementación llegó a
decir que esto vivía en `terraform/`. **No es así**, y la diferencia importa:

| | ¿hace falta? | por qué |
|---|---|---|
| `terraform/demo/iam.tf` | **NO** | el rol de instancia ya lee **todo el prefijo** `/jbg-demo/`, no parámetro a parámetro |
| `terraform/demo/ssm.tf` | **NO** | los secretos **no se declaran en Terraform a propósito**: un valor pasado a Terraform se escribe **en claro en el fichero de estado**. Se crean a mano, como los otros seis |
| `/jbg-demo/ASSIST_LLM_API_KEY` | **sí**, a mano | `aws ssm put-parameter --type SecureString` |
| `deploy/demo/deploy.sh` | **sí**, una línea | leer el parámetro **sin `:?`** |
| `compose.demo.yaml` | **sí**, dos líneas | pasar la clave y fijar el modelo |
| `deploy/demo/README.md` | **sí** | el runbook enumera los secretos que se crean a mano |

**Terraform no se toca.** Ésa era la parte de la nota anterior que estaba mal.

### Los cuatro pasos

**1 · Crear el parámetro, a mano y una vez** (como los otros seis secretos de esta demo):

```bash
aws ssm put-parameter --region eu-west-1 \
  --name /jbg-demo/ASSIST_LLM_API_KEY \
  --type SecureString \
  --value "sk-..." \
  --description "C30b credential for the sale argument. Separate from EMBEDDING_API_KEY"
```

**2 · `deploy/demo/deploy.sh`**, junto a las otras lecturas de Clase A:

```bash
# C30b. A DIFERENCIA de los demás, este parámetro puede NO existir: sin él la capa
# de generación no corre y la ruta sirve la respuesta estructurada con 200. Por eso
# `|| true` — `set -e` más el error del store abortarían el despliegue entero por una
# credencial cuya ausencia es un estado válido y declarado.
export ASSIST_LLM_API_KEY="$(read_parameter ASSIST_LLM_API_KEY || true)"
```

Y **no** añadir una línea `: "${ASSIST_LLM_API_KEY:?...}"` en el bloque de validación: ese bloque
existe para que un valor **vacío** falle ruidosamente, y aquí vacío significa «no generamos»,
que es legítimo.

**3 · `compose.demo.yaml`**, en `jbg-demo-ai`:

```yaml
      # Clase C — ajuste versionado, no parámetro. Misma regla que
      # JPV_EMBEDDING_MODEL y JPV_RETRIEVAL_DISTANCE_THRESHOLD (C17 D8): el store
      # es un sitio donde un valor cambia sin revisión de código, y el modelo
      # cambia lo que cuesta y lo que se midió.
      JPV_ASSIST_LLM_MODEL: openai/gpt-4o-mini
      # Clase A — secreto. Fuente: /jbg-demo/ASSIST_LLM_API_KEY. Ausente = la capa
      # de generación no corre y la ruta sirve la respuesta de C30a con 200.
      JPV_ASSIST_LLM_API_KEY: ${ASSIST_LLM_API_KEY}
```

`JPV_ASSIST_PITCH_TIMEOUT_SECONDS` se deja **fuera** hasta tener una medición del propio
despliegue: el defecto de 4 s está medido desde una máquina de desarrollo en España a través de
un interceptor TLS, que es una **cota superior** de la latencia del proveedor. Si la demo mide
una distribución distinta, entonces se añade — con la cifra delante, como se hizo con el 3 s.

**4 · `deploy/demo/README.md`**: añadir el parámetro a la lista de secretos que se crean a mano,
marcándolo como **el único opcional** de esa lista.

### Cómo comprobar que funcionó

Sin abrir la consola de AWS y sin leer ninguna clave, en el log del contenedor:

```
stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist
```

`credential=rag_fallback` diría que está replegando a la clave de C09, y `stage=assist_client`
ausente, que no se construyó cliente: la capa no corre y la ruta sirve C30a. Y en la respuesta,
`prompt_version` pasa de `null` a `assist/v1` — que es exactamente la distinción que C30b metió
en el contrato para poder ver esto desde fuera.

### Por qué no se hizo aquí

C30b declara `terraform/`, `.github/workflows/` y `backend/` fuera de alcance, y el despliegue
de la demo es trabajo de despliegue, no de la capa. La mitad de Python está entregada, probada
con **13 tests** y **no es andamio**: en local se separa hoy poniendo `JPV_ASSIST_LLM_API_KEY`
en `backend/.env`, que es de donde el barrido de C30b lee sus credenciales.

---

## ~~C34 · el corpus de conocimiento no viaja en la imagen de `jbg-ai`~~ — **CERRADA por C39a (2026-09-27)**

**Estado:** **CERRADA el 2026-09-27 por C39a, y con dos arreglos y no uno**, porque al implementarla
apareció que el problema tenía una segunda mitad que esta entrada no había visto.

> **1 · El corpus entra en la imagen, por un contexto adicional con nombre.** No por mover el contexto
> de *build* a la raíz, que era el primer plan y habría **roto el desarrollo local**:
> `backend/docker-compose.yml` construye el mismo `Dockerfile` con `context: ../ai-service`. Se usa
> `--build-context corpus=./data/knowledge` con `COPY --from=corpus`, así que el contexto primario no se
> mueve, `ai-service/.dockerignore` sigue gobernando, y **construir sin el flag falla en voz alta** —
> `failed to resolve source metadata for docker.io/library/corpus:latest`, código 1—, que es la
> propiedad que importa: no existe una imagen sin corpus construida en silencio.
>
> **2 · Y la mitad que esta entrada no había visto: la ruta que el servicio lee estaba mal calculada.**
> `CORPUS_DIR` se derivaba con `parents[3].parent`, correcto en un *checkout* y absurdo con el paquete
> instalado por `uv sync --no-editable`: **medido dentro del contenedor desplegado, el corpus se buscaba
> en `/app/.venv/lib/data/knowledge`**, dentro del árbol de dependencias. Copiar el corpus sin arreglar
> eso habría dejado el defecto en pie con una imagen más gorda. Se resuelve ahora por la **misma búsqueda
> de tres candidatos que `load_prompt_file`**, cuyo *docstring* describe exactamente este problema — y
> por eso los prompts sí funcionaban y el corpus no.
>
> **Evidencia:** en la imagen nueva `CORPUS_DIR` = `/app/data/knowledge`, **no es enlace**, 33 documentos
> y *sidecar* presente; en la antigua no existe. Imagen **426 MB antes y después**; contexto de 388 kB a
> 2,78 MB. `tests/knowledge/test_corpus_location.py`, **5 passed**. Suite de `ai-service` completa,
> **1.664 passed**.
>
> **Y por qué esto sobrevivió cinco semanas sin que nada fallara:** los fragmentos indexados viven en
> `jbg-demo-pgdata` y un redespliegue no toca ese volumen. El entorno servía **161 fragmentos** desde la
> base mientras su imagen no podía haber producido ni uno. `verify.sh` gana la condición que lo habría
> dicho.

**Estado original:** identificado el 2026-09-22 al desplegar la demo, **sorteado a mano y no resuelto**.
**Zona:** `ai-service/Dockerfile` — fuera del alcance de C34, que declara `ai-service/` intocable.

`CORPUS_DIR` es `<raíz del repo>/data/knowledge` (`knowledge/constants.py`), y el `Dockerfile` del
servicio copia sólo `src`, `migrations` y `prompts`. **Dentro del contenedor el corpus no existe**, así
que `python -m jbg_ai.indexing sync-knowledge` no tiene qué indexar y `ai.knowledge_chunk` se queda a
cero. Con la tabla vacía, `POST /v1/assist/sale` **retira el argumentario en M2** —la puerta de C30b no
tiene material al que anclarse— y responde `knowledge_not_covered` sin citas en M3. Parece un problema
del card, y no lo es.

**Cómo se sorteó en la demo** (el corpus sí viaja en el paquete de despliegue, bajo `/opt/jbg-demo`):

```sh
DEST=$(docker exec -i jbg-demo-ai python -c "from jbg_ai.knowledge.constants import CORPUS_DIR; print(CORPUS_DIR)")
docker exec -u root -i jbg-demo-ai mkdir -p "$(dirname "$DEST")"
docker cp /opt/jbg-demo/data/knowledge "jbg-demo-ai:$(dirname "$DEST")/"
docker exec -i jbg-demo-ai python -m jbg_ai.indexing sync-knowledge --full
```

Tras eso, M2 pasó a `generated` con 2 citas. **Pero se pierde con cada imagen nueva.** El arreglo es una
línea en el `Dockerfile` —copiar `data/knowledge`— o un montaje en el compose, y lo decide quien pueda
tocar `ai-service/`. Mientras no se haga, cualquier entorno nuevo nace sin corpus y con M2 retirado.

> **Comprobado y agravado el 2026-09-25, en la tarea 14.2 de C40.** La entrada sigue abierta, y el
> arreglo **no es una línea**. Dos cosas que conviene dejar escritas porque las dos engañan:
>
> **1 · Hay ocho Markdown en la imagen que parecen el corpus y no lo son.** `/app/prompts/knowledge/v1`
> existe —lo copia `COPY prompts ./prompts`— y contiene `01-materiales-frecuentes.md` y siete más. Son
> los **encargos de producción del corpus**, no el corpus: éste son **33 documentos** en
> `data/knowledge/`. Es un falso positivo fácil de dar por bueno, y lo di por bueno en la primera
> lectura de esta comprobación.
>
> **2 · Copiar `data/knowledge` a `/app/data/knowledge` tampoco lo encontraría.** Medido desde dentro
> del contenedor:
>
> ```text
> CORPUS_DIR = /app/.venv/lib/data/knowledge     existe: False
> ```
>
> `CORPUS_DIR` es `REPO_ROOT / "data" / "knowledge"` y `REPO_ROOT` se calcula subiendo desde el módulo,
> que en el contenedor vive en `site-packages` — así que resuelve a `/app/.venv/lib`. El arreglo
> necesita **dos** cosas: copiar o montar el corpus, **y** que la ruta deje de derivarse de la posición
> del paquete (una variable de entorno, como el resto de la configuración del servicio).
>
> **Que esta máquina tenga 32 documentos y 161 fragmentos con vector en la base no lo contradice:** el
> indexado corrió **desde el host**, donde `data/knowledge` sí existe. Un contenedor recién creado no
> puede indexar nada.

> **Esta entrada pesa más desde el 2026-09-22, al implementar C36.** Hasta hoy el corpus vacío sólo
> degradaba respuestas que nadie veía: `/v1/assist/sale` se demostraba con `curl` y con el arnés. C36
> le pone **pantalla**, y con ella una **caja de pregunta con cinco sugerencias horneadas** que
> invitan explícitamente a preguntar justo lo que el corpus cubre — mojar la pieza, piel sensible,
> limpieza en casa, regalo sin saber la talla, playa o piscina.
>
> En un entorno sin corpus, **las cinco responden `knowledge_not_covered` sin citas**. La ficha lo
> dice con palabras del mostrador y no miente, pero el efecto es el peor posible para una
> demostración: la interfaz enseña cinco preguntas y el sistema contesta a las cinco que la
> documentación no las cubre. **Hay que sortear esto antes de enseñar la ficha**, con el `docker cp`
> de arriba; si no, parece un defecto de C36 y no lo es.

---

## ~~C22 · un entorno recién desplegado deja `ai.pos_projection` vacía, y la recuperación responde 503~~ — **CERRADA por C41 (2026-09-26)**

> **Cerrada, y por las dos vías a la vez en lugar de elegir una.** La pregunta abierta al final de
> esta entrada era si `deploy.sh` debía drenar cuando la tabla está vacía o si bastaba con el paso
> del runbook más una comprobación en `verify.sh`. C41 hace **las dos**, porque resultaron no ser
> alternativas sino capas distintas:
>
> - **El drenaje deja de depender de que alguien lo recuerde.** `jbg-ai` drena el feed **al arrancar**
>   —completo cuando no hay checkpoint, que es exactamente este caso— y después cada 600 s. Un
>   entorno recién desplegado se cura solo antes de que nadie lo mire, sin tocar `deploy.sh`: la
>   condición «la tabla está vacía» ya la resuelve el propio orquestador, porque
>   `resolve_start_cursor` devuelve un keyset vacío y `is_full` se calcula de ahí.
> - **Y `verify.sh` gana su quinto motivo de fallo**, que es la red de seguridad. Era la opción
>   «más barata» y sigue siéndolo, pero por sí sola sólo *detecta*: falla el despliegue y deja a una
>   persona ejecutando el `docker exec`. Con el drenaje de arranque, la comprobación pasa a ser lo
>   que debe ser — una afirmación que se verifica, no un trabajo pendiente.
>
> La frase que justificaba la entrada —*«un entorno con índice lleno y proyección vacía pasa hoy la
> verificación posterior al despliegue»*— deja de ser cierta. Y la tarjeta del administrador reporta
> ahora cuántos puntos de venta se han quedado sin surtido, que es el dato que faltaba para que este
> fallo fuera visible sin abrir un log.
>
> Change [`add-pos-projection-scheduled-drain`](changes/archive/2026-09-26-add-pos-projection-scheduled-drain/),
> historia [HU-AIENG-041](../Documentos/Historias/AI-Eng/HU-AIENG-041.md).

**Estado:** identificado el 2026-09-22 al desplegar la demo, resuelto en ese entorno sin arreglo
sistemático, y **cerrado sistemáticamente el 2026-09-26 por C41**. **Zona:** `deploy/demo/` y el
runbook. *El texto original se conserva íntegro debajo, porque es el diagnóstico y sigue siendo la
mejor descripción del fallo.*

`resolve_scope` se niega a abstenerse sobre una proyección vacía y lanza `RetrievalDependencyError`,
que la ruta traduce a **503**:

```python
size = await search.count_scope(pos_id)
if size == 0:
    raise RetrievalDependencyError(EMPTY_PROJECTION_DETAIL)
```

La llaman **las dos** rutas de recuperación —`/v1/retrieval/products` y `/v1/retrieval/substitutes`—, y
`jpv_pos_prefilter_enabled` viene activado por defecto. Un entorno que nunca haya drenado el feed de
disponibilidad responde 503 a **toda** recuperación, y el consumidor .NET degrada correctamente: la
búsqueda cae a su vía léxica y los sustitutos a `ai_unavailable`, **los dos con 200**, así que desde
fuera el entorno parece sano. Así estaba la demo, desplegada en C17, cuando C34 llegó.

Se arregla una vez por entorno, y persiste en la base:

```sh
docker exec -i jbg-demo-ai python -m jbg_ai.indexing sync-pos --full
```

**Lo que falta decidir:** si `deploy.sh` debe drenarlo cuando la tabla está vacía, o si basta con el
paso del runbook —que C34 añade— más una comprobación en `verify.sh`, que hoy mira el índice de
productos pero no la proyección. Lo segundo es más barato y caza el caso: un entorno con índice lleno y
proyección vacía **pasa hoy** la verificación posterior al despliegue.

---

## Active Change: `add-guardrails-and-intent-router` (C31)

### Desplegar el clasificador de intención en la demo

**Estado: pendiente, y la configuración que se despliega está decidida por medición.**

Mismo patrón que la entrada de C30b de arriba, con **tres** variables en lugar de una y con un
requisito que manda sobre todo lo demás: **sólo se despliega la configuración que pasó el veto.**

Medido sobre los 119 casos de `evals/routing/cases.yaml`, mismo prompt `router/v3`, temperatura
cero, cobertura completa en los dos arms:

| modelo | acierto `catalog` | falso positivo | silenciadas | veto |
|---|---|---|---|---|
| `openai/gpt-4o-mini` | 81,3 % | 6,25 % | **3** | **NO PASA** |
| `openai/gpt-4o` | 100 % | 0,00 % | **0** | **PASA** |

`DEFAULT_ROUTER_MODEL` quedó fijado en **`openai/gpt-4o`** por esa medición, y ése es el valor
que el despliegue tiene que poner. **Un despliegue que apunte `JPV_ROUTER_LLM_MODEL` a
`gpt-4o-mini` estaría sirviendo una configuración vetada**, que silencia tres consultas que la
tienda sí puede contestar.

Mientras la credencial no esté puesta, el clasificador no se construye, `intent` vuelve a
`unclassified` y la ruta se comporta exactamente como la dejó C30b. Eso es a la vez el
*fail-open*, la ablación y el rollback, y está entregado con test.

### Los cuatro pasos

**1 · Crear el parámetro, a mano y una vez** (como los otros siete secretos de esta demo):

```
aws ssm put-parameter --name /jbg-demo/ROUTER_LLM_API_KEY --type SecureString --value '…'
```

**Terraform no se toca**, por la misma razón que en C30b: el rol de instancia ya lee todo el
prefijo `/jbg-demo/`, y un valor pasado a Terraform se escribe en claro en el fichero de estado.

**2 · `deploy/demo/deploy.sh`**: leer el parámetro **sin `:?`**, para que un despliegue sin él
siga funcionando — que es precisamente el estado en el que hay que dejarlo hasta que el veto
pase.

**3 · `compose.demo.yaml`**: pasar `JPV_ROUTER_LLM_API_KEY` y fijar `JPV_ROUTER_LLM_MODEL`.

`JPV_ROUTER_TIMEOUT_SECONDS` se deja **fuera**, igual que C30b dejó fuera el suyo y por la misma
razón, sólo que más fuerte: el defecto de 2 s está **declarado no calibrado** en el docstring de
la constante, se tomó desde una máquina de desarrollo en España a través de un interceptor TLS, y
este corte va **delante de todo**, así que su efecto es más duro que el del argumentario. Se
añade cuando el despliegue mida su propia distribución, con la cifra delante.

**4 · `deploy/demo/README.md`**: añadir el parámetro a la lista de secretos que se crean a mano,
marcándolo como **opcional**, y anotando junto a él que `JPV_ROUTER_LLM_MODEL` **no puede
apuntar a `gpt-4o-mini`**, que es la configuración que el veto rechazó.

### Cómo comprobar que funcionó

Sin abrir la consola de AWS y sin leer ninguna clave, en el log del contenedor:

```
stage=router_client model=openai/gpt-4o timeout_s=2.0 credential=router
```

**Si ese `model=` dice `gpt-4o-mini`, el despliegue está sirviendo la configuración vetada** y
hay que corregirlo antes de mirar nada más.

`credential=assist_fallback` o `rag_fallback` dirían que repliega por la cadena, y
`stage=router_client` ausente, que no se construyó cliente y la ruta se comporta como C30b. Y en
la respuesta, `intent` pasa de `unclassified` a un veredicto de enrutado.

### Dos cosas más que este change dejó medidas y que el despliegue hereda

1. **El límite de tasa del proveedor decide cuánto se puede medir de golpe.** El barrido de 119
   casos a concurrencia 6 produjo **22 degradaciones por `RateLimitError`**, y sobre `gpt-4o`,
   **89 de 119**. El arnés reintenta sólo eso —nunca un fallo de parseo, que es la degradación
   que se está midiendo— y aun así hace falta concurrencia 1 y pausa. No afecta al camino de
   servicio, que hace una llamada por petición.
2. **La primera llamada de un proceso paga el `import litellm` dentro de su propio *timeout*.**
   Medido: los dos primeros casos de una pasada agotaron **20 s** por eso y por nada más. En el
   camino de servicio, con un corte de 2 s, eso significa que **la primera consulta libre tras un
   arranque en frío degrada** — cae en el *fail-open*, que es el comportamiento correcto, pero es
   una degradación evitable calentando el import en el arranque de la aplicación. No se hizo aquí
   porque tocar el arranque está fuera del alcance de este change; queda anotado.

---

## C32a · La consulta puntual de disponibilidad en .NET

**Estado:** identificada, acotada y **no hecha**. Aplazada **con motivo**, no por falta de tiempo.

El §6.1 del diseño RAG dibuja la arista `R2 -->|tool: consultar_disponibilidad| API` y deja el
esquema de la llamada de vuelta Python → .NET como *«decisión abierta del change del agente de
venta»*. C32a es ese change, y la resuelve **difiriéndola**: la tool se sirve desde
`ai.pos_projection`, que es un dato que Python ya tiene proyectado.

### Por qué no se hizo aquí

La única arista Python → .NET que existe hoy es
[`AiIndexFeedController`](../backend/src/JoiabagurPV.API/Controllers/AiIndexFeedController.cs), y
no sirve para esto por tres razones independientes:

1. Está autenticada con `X-Index-Feed-Key` y **sin `[Authorize]` a propósito** — *«a user JWT
   must not open these routes»* — así que no transporta identidad de usuario.
2. **No transporta `pos_id`**, que es justo el ámbito que una consulta puntual necesita.
3. Su ruta `pos-availability` es un **feed paginado de 200 filas con keyset**, pensado para un
   drenaje batch y no para preguntar por una pieza.

Construirlo habría significado ruta .NET nueva, filtro de autenticación con ámbito de punto de
venta y tests de integración: **zona .NET dentro de un change de zona Python**.

### Qué hace falta cuando se haga

- Ruta .NET puntual por `(pos_id, product_id)` o por `(pos_id, sku)`.
- Un esquema de autenticación de vuelta que **sí** transporte el ámbito del punto de venta, y
  que no sea la clave de feed: la clave de feed abre rutas sin usuario por diseño.
- Decidir si la respuesta sigue siendo una **banda cualitativa** o pasa a ser la cifra. La
  frontera del §6.2 dice que .NET es la autoridad sobre el stock, así que la cifra es suya; lo
  que C32a fija es que **al modelo no le llega un número**, venga de donde venga.

### Por qué el reemplazo es directo

La tool no tiene lógica de disponibilidad dentro: llama a
`ProductSearchPort.availability_bucket(product_id, pos_id=...)` y traduce con
`AVAILABILITY_LABEL_BY_BUCKET`. Sustituir el puerto por un cliente del endpoint .NET no cambia
la forma de la observación, ni el vocabulario cerrado, ni ninguno de sus tests — salvo el del
invariante de solo-lectura, que **volverá a ser el que decide**: un cliente HTTP de propósito
general expone `post`, `put`, `patch` y `delete`, y el tercer eje de la comprobación lo rechaza.
Quien construya ese cliente tendrá que envolverlo en una superficie que exponga sólo la lectura,
que es exactamente la restricción que se quería dejar puesta.


---

## Implementation Guidance

When implementing deferred tasks:

1. **Check this document** - Ensure task is still relevant and not superseded
2. **Review original spec** - Check `openspec/changes/[change-id]/specs/` for full requirements
3. **Review design decisions** - Check `openspec/changes/[change-id]/design.md` for context
4. **Create new change proposal** - If adding new capability, create new change proposal
5. **Update this document** - Mark tasks as completed or update status

---

**Last Updated:** 2026-09-20
**Maintained By:** Development Team

---

## C32b · La política de *timeout* y de circuito de `POST /v1/assist/agent` en la capa .NET

**Estado: CERRADA POR C42 el 2026-09-26 — el *timeout* hecho, el circuito CERRADO POR REFUTACIÓN.**
La mitad del *timeout* se cumple como pedía; la del circuito **no se ejecuta, porque medir la ruta
demostró que lo que esta entrada pide no es alcanzable**. El motivo, entero, abajo.

> ### Lo que C42 hace, y lo que refuta *(2026-09-26)*
>
> **El *timeout* propio por ruta: hecho.** `AiGatewayOptions.AgentTimeoutMs = 18_000` sobre el cliente
> con nombre `ai-agent`, con `HttpClient.Timeout` infinito y el presupuesto en el *pipeline*, suelo de
> **15 s validado al arranque** —el `AGENT_DEADLINE_SECONDS` del servicio— y sin reintento en *timeout*
> ni en 5xx. Deliberadamente **no ajustado al máximo observado** de 11.917 ms: apretarlo corta una
> petición que Python **ya pagó entera**.
>
> **El circuito que cuenta `stop_reason=fallo_proveedor`: NO SE HACE, y es una refutación y no una
> omisión.** Esta entrada pedía contarlo; el *pipeline* de la ruta hermana ya declaraba lo contrario
> —*«a 200 the service degraded internally … is not a failure: Python degraded, and the breaker
> protects from Python not answering»*—, y los dos documentos se contradecían. La contradicción se
> resuelve del lado de `ai-assist`, por **tres** razones y no por una:
>
> 1. **Lo que un cortafuegos protege es que el servicio no conteste.** Estas respuestas son
>    contestaciones. Uno que las contara se abriría sobre una ruta que **funciona como está diseñada**,
>    y la consecuencia sería peor que el problema: negaría el servicio a un mostrador cuyo proveedor
>    ya volvió.
> 2. **La aritmética lo hace inalcanzable.** Con ~13.000 tokens por petición contra un techo de 25.000
>    TPM —la misma cifra que esta entrada ya publicaba como restricción operativa— el sistema admite
>    **una petición por minuto**. El cortafuegos de este proyecto abre por **proporción de fallos sobre
>    un mínimo de muestras en una ventana**: con `BreakerSamplingDurationSeconds` en decenas de
>    segundos y `MinimumThroughput` en unidades, **la ventana expira antes de acumular la primera
>    muestra**. Un circuito que no puede abrirse no es una protección, es código que nadie ejecuta.
> 3. **Y hay un obstáculo mecánico encima.** El predicado del cortafuegos recibe un
>    `Outcome<HttpResponseMessage>` y **no ve el cuerpo**. Leerlo exigiría bufferizar la respuesta,
>    parsear el JSON dos veces y acoplar el transporte al vocabulario cerrado del contrato. Un circuito
>    de dominio en el servicio de aplicación sería correcto en capas y choca con el punto 2 igual.
>
> **Qué se hace en su lugar, porque la señal no se pierde.** La degradación se instrumenta: un
> `LogWarning` con plantilla `ai_gateway_agent_degraded` que nombra el motivo de parada, la latencia,
> las vueltas y las llamadas, emitido para `fallo_proveedor` y para `sin_cliente`. Así su tasa queda
> observable sin que el circuito actúe sobre ella —que era el único coste real de la decisión—. Y
> **quien avisa a la pantalla es la sonda**, `GET /api/ai/search/availability`, que gana
> `agentAvailable` como valor propio: no gasta cupo, no llama al proveedor y se lee antes de entrar.
>
> **La tercera viñeta de *Qué hace falta*, la de `partial: true`, también está hecha**: el bloque de
> respuesta lo dice sin alarma y nombrando el presupuesto agotado, y va el último porque sirve al
> **2,0 %** de las peticiones del brazo servido.
>
> **Y la restricción operativa se hereda tal cual.** Una petición por minuto basta para un mostrador y
> un evaluador, y **no** para dos mostradores simultáneos. Por eso el agente lleva su propia política
> de cupo —`AiAgentAssist:RateLimitPermitLimit`, cuatro por minuto— en vez de compartir la de la
> consulta libre: un puñado de conversaciones agotaría lo que la ruta barata necesita. Dimensionar la
> cuota sigue siendo parte de poner esto en producción.

> **Lo que C34 cambia en esta entrada** *(2026-09-21)*. La ruta determinista ya no declara 5 s: C34
> registró el cliente `ai-assist` para `/v1/assist/sale` con **10 s y un suelo de 8 s validado al
> arranque**, sin reintento en timeout y con circuito propio. El agente **no debe reutilizarlo**:
> su techo es otro (15 s más las herramientas de la vuelta en curso) y su circuito tiene que contar
> `stop_reason=fallo_proveedor`, que la ruta determinista no emite. El patrón a copiar sí está ya:
> un cliente con nombre por ruta, `HttpClient.Timeout` infinito y el presupuesto en el *pipeline*.

C32b publica `POST /v1/assist/agent` y **nadie la llama**. `IAiGatewayClient` no tiene método para
ella, no hay pantalla detrás y el change de hidratación no la consume. Escribir su política de
tiempo de espera y de cortocircuito ahora sería escribirla contra un consumidor imaginario, que es
la misma razón por la que C32a difirió el endpoint de disponibilidad.

### Por qué la política no puede ser la de `/v1/assist/sale`

Medido en la pasada `293fe5c6e470`, sobre 102 peticiones con `gpt-4o`:

| | `/v1/assist/sale` | `/v1/assist/agent` |
|---|---|---|
| Latencia declarada | **5 s** (§6.4 del diseño) | **15 s**, fijados por medición |
| p50 medido | — | **5,3 s** |
| p95 medido | — | **9,0 s** |
| Máximo medido | — | **11,9 s** |

**Un cliente .NET con el *timeout* de la ruta determinista cortaría más de la mitad de las
peticiones del agente.** El p50 del agente es del orden de la latencia total que la otra ruta
declara como techo.

### Qué hace falta cuando se haga

- **Un *timeout* propio por ruta**, no uno compartido: 15 s más el margen de red, contra los 5 s
  de la determinista.
- **Un cortocircuito que distinga degradación de fallo.** Esta ruta **no devuelve 5xx** cuando el
  proveedor cae: responde 200 con `partial: true` y un `stop_reason` del vocabulario cerrado. Un
  circuito que contase esas respuestas como fallos se abriría sobre una ruta que está funcionando
  como está diseñada; el que las ignorase perdería la única señal de que el proveedor está caído.
  Lo que hay que contar es `stop_reason=fallo_proveedor`, que existe precisamente porque la
  primera pasada de C32b demostró que sin él esas respuestas son indistinguibles de una completa.
- **Decidir qué hace el mostrador con `partial: true`.** Es una respuesta útil e incompleta, y la
  pantalla tiene que poder decirlo sin alarmar: no es un error.

### Y una restricción operativa que el consumidor heredará

La pasada midió que **la cuota de tokens por minuto de la organización**, y no el dinero, es lo que
limita el ritmo: con peticiones de ~13.000 tokens, un techo de 25.000 TPM admite **una petición por
minuto**. Un mostrador con varios operarios simultáneos choca con eso mucho antes que con el coste,
y el síntoma es un `RateLimitError` que la capa convierte en `fallo_proveedor` y sirve degradado.
Dimensionar la cuota es parte de poner esta ruta en producción, no un detalle de la medición.

> **Nota de la verificación independiente de C32b.** Los 15 s de la tabla de arriba **no acotaban
> la petición** cuando se escribió: el reloj sólo se miraba antes de cada vuelta, y el peor caso por
> construcción eran 15 + 8 + 2 × 4 = 31 s más las herramientas. Ahora el bucle corre contra 15 s
> menos la reserva del argumentario y la vuelta en curso se corta; el límite es **15 s más, como
> mucho, las herramientas de esa vuelta**, que no se cancelan a medias. Es el número que un
> *timeout* .NET debe cubrir, con su margen de red.

---

## C42 · El pivote a sustitutos es inalcanzable cuando el operario nombra la pieza por su NOMBRE

**Estado: medido con proveedor real, acotado y fuera del alcance de C42**, que declara no tocar las
seis herramientas ni añadir una séptima. Encontrado por la **comprobación manual** de C42 y por nada
más — las tres suites estaban verdes.

> **El pivote a sustitutos es lo que el panel del agente existe para demostrar**, y está medido **3 de
> 3** en `sin_existencias` con `gpt-4o`. Esta entrada dice que esa medición se tomó en **una situación
> que no existe en la pantalla**.

### El experimento que lo establece

Una pieza agotada de verdad —`SKU759`, *Anillo Luna Creciente S*, `qty_bucket = '0'` en
`ai.pos_projection` para `CIU-CENTRE`, comprobado— preguntada de las dos maneras contra el proveedor
real por HTTP:

| Cómo la nombra el operario | Herramientas que el bucle eligió | ¿Pivota? |
|---|---|---|
| **Por su referencia**, `SKU759` | `consultar_disponibilidad` → **`buscar_sustitutos`** | ✅ **Sí.** 6 grupos, **todos `sustitutos`** |
| **Por su nombre**, «Anillo Luna Creciente S» | `consultar_disponibilidad`❗`referencia_desconocida` → `buscar_catalogo` → `consultar_disponibilidad` | ❌ **No.** 8 grupos, todos `catalogo` |

### Y el mecanismo, que es estructural y no una torpeza del modelo

**`buscar_catalogo` no devuelve el nombre de la pieza.** Su observación lleva
`posicion`, `sku`, `materiales`, `variante` y `motivos` (`assist/tools.py`, `buscar_catalogo`). De modo
que la cadena es:

1. El modelo pasa el **nombre** a `consultar_disponibilidad`, que quiere un SKU → `referencia_desconocida`.
2. Se recupera con `buscar_catalogo`, que devuelve ocho candidatos **identificados sólo por SKU,
   material y variante**.
3. **No tiene con qué saber cuál de los ocho es la pieza que el cliente nombró**, así que consulta la
   disponibilidad de otra — que sí tiene stock — y, correctamente, no pivota.

**El bucle hace lo correcto en cada paso.** Lo que falta es el puente del nombre al SKU, y las seis
herramientas no lo tienen: la búsqueda semántica devuelve **vecinos**, no la pieza exacta.

**Por qué el arnés no lo vio**, que es el mismo patrón que esta implementación ya encontró dos veces
más: `scenario_turns` resuelve el marcador `{pieza}` a un **SKU** y lo escribe en el turno, así que en
las 204 peticiones de C32b y en las 102 de C42 **el modelo siempre recibió la referencia servida**. Un
operario teclea un nombre.

### Qué haría falta cuando se haga, y la decisión que arrastra

- **Lo más estrecho: que la observación de `buscar_catalogo` lleve el nombre del producto.** Un campo,
  en la observación que ve el modelo y no en el payload de generación.
- **Y el argumento de C30b contra ensanchar el payload no se le aplica tal cual**, que es lo que hace
  esta opción defendible: aquella regla es sobre **numerales** —*«every field handed over widens the
  whitelist the numeric gate admits»*— y un nombre no lleva cifras. Pero sigue siendo **una de las seis
  herramientas congeladas**, así que lo decide quien las posea, no un change de frontal.
- **Alternativa sin tocar las herramientas:** que la pantalla ofrezca la referencia. El panel del
  agente ya enseña el SKU en cada fila, así que un operario que ve la pieza en un turno anterior puede
  nombrarla por referencia en el siguiente. **Es un paliativo y no el arreglo**, porque el caso que
  falla es justo el primer turno, cuando el cliente nombra algo que el operario aún no tiene en
  pantalla.
- **Y lo que NO hay que hacer:** colapsar `referencia_desconocida` con una búsqueda por nombre dentro de
  `consultar_disponibilidad`. Esa herramienta responde sobre **una** pieza identificada; hacerla adivinar
  cuál convertiría una respuesta sobre existencias en una búsqueda, que es precisamente la confusión que
  el vocabulario cerrado de causas existe para evitar.

**Mientras no se haga, el pivote se demuestra nombrando la referencia**, que es realista en un
mostrador —la pieza lleva su etiqueta delante— y es lo que el *runbook* de la comprobación manual dice.

---

## C32b · Once tests preexistentes de `ai-service` salen a la red con una clave falsa

**Estado:** medido, **no corregido** y fuera del alcance de C32b: los tests son de C30b y C31, y
ninguno lo introdujo este change. Encontrado por su verificación independiente.

`tests/api/test_assist_generation.py` construye la app con una clave de mentira
(`jpv_rag_llm_api_key="sk-test"` y análogas) e inyecta dobles para el *embedding*, la búsqueda y el
corpus, **pero no para el clasificador ni para el argumentario**. La ruta construye entonces los
clientes reales de LiteLLM y los usa: la llamada sale hacia `api.openai.com`, muere (TLS o 401) y
el test pasa porque la capa degrada. Medido con un guardia de sockets y de `psycopg` sobre la suite
entera: **12 resoluciones de `api.openai.com` y 1 de `raw.githubusercontent.com`** (la tabla de
costes que descarga `litellm`), en estos once tests:

- `test_the_configured_timeout_reaches_the_generation_client`
- `test_the_dedicated_credential_is_preferred_over_the_enrichment_one`
- `test_the_enrichment_credential_is_the_fallback_and_not_a_requirement`
- `test_the_fallback_is_recorded_so_a_deployment_can_check_it_instead_of_assuming`
- `test_the_configured_model_reaches_the_generation_client`
- `test_the_enrichment_model_cannot_move_the_assistance_model`
- `test_the_classifier_credential_falls_back_through_the_three_links` (tres veces)
- `test_which_classifier_credential_is_in_force_is_recorded_without_the_key`
- `test_the_configured_classifier_model_and_timeout_reach_the_client`
- `test_the_argument_model_cannot_move_the_classifier_model`

Y uno más de otro fichero, `tests/api/test_retrieval_real.py::test_missing_embedding_key_is_503`,
intenta abrir una conexión de `psycopg`.

**Es el mismo defecto que el §10.4 del QA de C32b encontró en su propio test y corrigió**: *«la suite
no abre sockets» no es una propiedad que la suite compruebe sola*. Aparte, **72 tests `db`** corren
contra un PostgreSQL real a través de testcontainers cuando Docker está disponible (y se saltan si
no): eso es diseño, pero significa que «la suite corre sin base de datos» sólo es cierto en una
máquina sin Docker.

### Qué hace falta cuando se haga

- **Pilotar el resolutor directamente**, como hace `test_the_credential_chain_is_agent_then_assist_then_enrichment`
  desde C32b, o **inyectar los dobles** del clasificador y del argumentario en `app.state` antes de
  servir la petición. Lo que se prueba es la resolución y lo que se registra, que ocurre antes de
  cualquier llamada.
- **Después, un guardia de sockets automático en `tests/conftest.py`** que rechace toda conexión que
  no sea de bucle local y deje pasar la de testcontainers. Sin los once arreglados antes, ese
  guardia los pondría en rojo el primer día; con ellos arreglados, convierte la propiedad en algo
  que la suite comprueba en vez de algo que su README afirma.

---

## C32b · El desglose del uso por etapa en la respuesta de `POST /v1/assist/agent`

**Estado:** identificado y **no hecho**, a decidir cuando la ruta tenga consumidor (C34/C36).

`AgentUsage` suma los tokens de hasta tres etapas —clasificador, bucle y argumentario— que corren
modelos distintos, y publica **un solo `model`**, el de la última. Quien tarife `usage` × `model`
reproduce el error de coste que la verificación independiente encontró en el arnés. Dentro del
proceso ya está resuelto (`AgentRun.router_usage`, `loop_usage` y `pitch_usage`, que el arnés
tarifa una a una), y la descripción de `AgentUsage.model` en el contrato avisa de que no es una
clave de precio.

**Lo que falta, si un consumidor .NET necesita el coste**: añadir a `AgentUsage` un desglose por
etapa, cada una con su modelo y sus tokens. Es **adición pura** sobre un esquema que sólo publica
esta ruta —`/v1/assist/sale` no se mueve— y no se hace ahora porque, sin consumidor, agrandaría la
superficie congelada para nadie.

---

## C36 · servir la parte estructural de la ficha sin pagar una generación

**Estado:** identificado el 2026-09-22 al implementar C36, **no hecho y no decidible hoy**.
**Zona:** `backend/src/JoiabagurPV.Application/` y `API/` — fuera del alcance de C36, cuya zona es
`frontend/src/`.

**El problema, medido.** Los datos **baratos** de la ficha de venta —el grupo de la familia, los
cuatro avisos y el estado de existencias— y los **caros** —el argumentario y sus citas— llegan
**soldados en la misma respuesta**. Los primeros no necesitan ni un token y sólo se obtienen pagando
una generación completa de **p50 4,42 s / p95 7,13 s** (C34 §4), cuando el reparto real es **4 ms de
.NET contra 4,4 s de IA**.

**Y no hay camino alternativo desde el frontend.** `GET /api/product-families/{id}` existe y es
accesible a cualquier autenticado, pero está indexada por **familia**, el objeto de transferencia de
producto **no lleva `familyId`**, y la ruta no devuelve cantidad por punto de venta. Desde un
`productId` no se llega: comprobado sobre el árbol en la exploración de C36 (H4).

**Qué haría falta.** Un `generate=false` —o un `?structural=true`— en
`POST /api/ai/products/{productId}/sales-assist` que devuelva el mismo objeto con `pitchStatus:
not_generated`, `citations` vacío y el grupo, los avisos y las existencias hidratados igual que ahora.
Serviría la ficha estructural en **~10 ms**. Es **adición pura**: ningún campo se retira ni cambia de
tipo, y la ficha ya sabe pintar `not_generated` sin insinuar una caída.

**Por qué no se hizo en C36.** Rompe la zona del change —`backend/` intocable— y reabre un change
archivado el día anterior.

**Condición de reactivación, y por qué hoy no es observable.** Sería *«que el uso real de la ficha
muestre aperturas que no leen el argumentario»*. **No se puede comprobar**: la ficha no tiene
telemetría, que es la entrada siguiente. Mientras no la tenga, esto se decide por argumento o no se
decide.

---

## C36 · la ficha de venta no deja rastro

**Estado:** identificado el 2026-09-22 al implementar C36, **declarado como limitación**.
**Zona:** `backend/` (tabla y ruta) y `frontend/src/pages/sales/assist.tsx` (emisión).

A diferencia de la búsqueda asistida, que persiste `ProductSearchEvent` desde C04 y sostiene con él la
tasa de selección del §11 del diseño, **ninguna de las tres cosas que la ficha decide deja rastro**:

| Acto | ¿Se registra? |
|---|---|
| Abrir la ficha de una pieza | **No** |
| Preguntar algo del cliente | **No** |
| Elegir una variante de la familia | **No** |

No hay tabla equivalente y C36 no la crea, porque crearla era una migración de EF Core y la zona del
change es `frontend/src/`. Una consecuencia deliberada y una accidental:

- **Deliberada:** abrir la ficha **desde la fila de resultados no reporta selección** al endpoint de
  telemetría de búsqueda. Ver una ficha no es elegir la pieza, y contarlo inflaría la tasa de
  selección que el evento de búsqueda existe para medir. Hay test: `should report no selection when
  the card is opened from a result row`.
- **Accidental:** la condición de reactivación de la entrada anterior **no es observable**.

**Qué haría falta cuando se haga.** Una tabla `SalesAssistEvent` con el producto anclado, el punto de
venta, si hubo pregunta —**nunca su texto**, por la misma razón por la que no viaja en la URL— y el
miembro elegido si lo hubo; más una ruta de reporte con la forma de la de selección de C04, que se
llama sin esperarla y cuyo fallo es invisible por diseño. La retención hereda el problema que el §15.11
del diseño ya declara para `ProductSearchEvent`.

---


## Active Change: `add-frontend-free-query-panel` (C40)

### Una búsqueda en «todos los puntos de venta» no queda registrada

**Estado:** implementada la búsqueda, **no** su telemetría.

`ProductSearchEvent.PointOfSaleId` es `Guid` no nulo, `IsRequired()` en su configuración de EF Core
y forma parte del índice `(PointOfSaleId, CreatedAt)`. Registrar una búsqueda sin tienda exige
volverlo anulable, y eso es **una migración de EF Core**, que es lo único que el encargo de este
change excluye explícitamente. La spec, por su parte, prohíbe la salida fácil: *«it MUST record the
search with no point of sale rather than with a placeholder one»*.

Entre una migración y una mentira, la tercera opción es no registrar y decirlo. Es lo que se ha
hecho: con `PointOfSaleId` nulo el servicio devuelve `searchEventId = null` —exactamente como ya
hace cuando la telemetría falla—, no se atribuye ninguna venta a esa búsqueda y nada más cambia.

**Qué se pierde, concretamente.** Una consulta libre de ámbito global no aparece en el embudo, no
cuenta para la tasa de selección y no se puede comparar con las de ámbito de tienda. Como el panel
por defecto lleva una tienda seleccionada, el hueco afecta sólo a las búsquedas en que el operario
quita el ámbito a propósito, cuya frecuencia **no se puede medir precisamente porque no se
registran**. Eso es circular y hay que decirlo: la primera cifra que dará el arreglo es cuánto se
estaba perdiendo.

**Qué haría falta cuando se haga.** Volver `PointOfSaleId` anulable en `ProductSearchEvent` y en su
configuración, la migración correspondiente, y revisar el índice —un `(PointOfSaleId, CreatedAt)`
con nulos sigue sirviendo a las consultas por tienda, pero las agregaciones que hoy asumen no-nulo
tendrían que decidir si cuentan o excluyen las globales—. En `ProductSearchEventService` desaparece
el `?? throw` que hoy trata un ámbito sin tienda como error de programación. Y la retención hereda
el problema que el §15.11 del diseño ya declara para esta misma tabla.

### El rechazo del ámbito global en inventario no tiene superficie .NET donde afirmarse

**Estado:** la garantía existe, el test que la tarea 12.2 pedía **no puede escribirse donde lo pedía**.

La tarea 12.2 pide `ForAllPointsOfSale_IsRefusedByInventory`, junto a sus hermanos de la ficha y los
sustitutos. Los dos hermanos existen; éste no, porque **`IAiGatewayClient` no tiene operación de
inventario**: `/v1/inventory/propose` existe en jbg-ai y nada en .NET la llama. El requisito viene de
la spec, que enumera «the sale card, substitutes and inventory» pensando en las rutas del servicio y
no en los métodos del cliente.

No se ha inventado un test que pase por casualidad. Lo que hay en su lugar son dos cosas:

- **La garantía vive del lado de Python.** La ruta conserva la dependencia estricta del punto de
  venta y rechaza un token sin la reclamación, en `test_pos_scoped_route_still_rejects_it`
  (`ai-service/tests/api/test_auth.py`). Es la garantía que importa, porque es la que un cliente
  cualquiera —no sólo el .NET— encuentra al llamar.
- **Del lado .NET queda un centinela que afirma que la superficie no existe**, en
  `AiGatewayClientTests.cs:421`, `ForAllPointsOfSale_IsRefusedByInventory_HasNoClientSurface`. El día
  que este cliente crezca una llamada de inventario, ese test falla y pide su propio rechazo — que es
  exactamente el momento en que el test de la tarea 12.2 tendrá dónde aterrizar.

**Qué haría falta cuando se haga.** Añadir la operación de inventario a `IAiGatewayClient` con su
guarda de ámbito —`scope.Kind != AiCallScopeKind.PointOfSale` lanza antes de emitir petición, como
`SubstitutesAsync`—, sustituir el centinela por el test que la tarea nombra, y comprobar que el
rechazo ocurre **antes** de la petición y no por la respuesta del servicio.

Anotado aquí porque el informe de implementación lo declara diferido y la verificación encontró que
faltaba esta mitad: la entrada estaba en el informe y no en este fichero.

---

## Active Change: `c40-fix-all-shops-scope-unreachable` (C40_FIX)

### La ruta rápida no acepta el ámbito global — y arreglarlo exige antes agrupar en la rama léxica

**Son una sola tarea, y ése es el hallazgo.** Separadas parecen dos mejoras independientes; juntas son
una tarea con un orden obligatorio, porque hacer la primera sin la segunda entrega un **HTTP 500**.

**Qué falta.** `POST /api/ai/search` —la ruta rápida, la que el panel usa **por defecto**— rechaza el
ámbito «todas las tiendas» con un 400 de validación:
`AssistedSearchRequestValidator` lleva `RuleFor(x => x.PointOfSaleId).NotEmpty()`, y
`AssistedSearchRequest.PointOfSaleId` es `Guid` y no `Guid?`. El ámbito sólo lo sirve
`POST /api/ai/search/assisted`, cuyo request sí es anulable.

**Por qué C40_FIX no lo hizo.** Porque limitó el control al administrador, y con esa audiencia la
objeción económica a fijar la ruta generativa se cae: no son cien mostradores en ráfagas, son consultas
ocasionales de administración. Extender la ruta rápida arrastra el DTO, el validador, `AuthoriseAsync`,
la construcción del ámbito, la hidratación, `RecordAsync` y `AssistedSearchResponse` de
`AssistedSearchService`, **el servicio más transitado y más probado del árbol**, con toda su cola de
tests de integración. Se declaró fuera de alcance con su motivo en el `design.md` del change (D2).

**Y la mina que hay que desactivar antes, que es la parte no obvia.** La capa de repositorio ya es
anulable, pero **no de forma uniforme**:

| Método de `IAssistedSearchRepository` | Acepta `Guid?` | Agrupa por producto con nulo |
|---|---|---|
| `HydrateAsync` | sí | **sí**, con un comentario que explica el peligro |
| `SearchLexicalAsync` | sí | **no** — proyecta `ToRow` desde filas de `Inventory` |

`Carried(null)` suelta el filtro de tienda, así que un producto que tres tiendas llevan vuelve **tres
veces**, y `AssistedSearchService.BuildResultsAsync` hace `rows.ToDictionary(row => row.ProductId)`
**incondicionalmente, en las dos ramas**. Resultado: `ArgumentException` → **HTTP 500**.

Hoy la rama nula de `SearchLexicalAsync` es **código muerto**: su único llamante es `DegradedAsync`, que
siempre pasa una tienda concreta. Se activaría en el instante en que la ruta rápida aceptara la
ausencia — y **primero en desarrollo local**, donde `AiSearch__EnabledByDefault` no está declarado en
ningún `appsettings` y por tanto la ruta degradada es la que corre siempre.

### Qué hace falta cuando se haga

1. **Primero la agrupación**: replicar en `SearchLexicalAsync` el `GroupBy(ProductId)` de
   `HydrateAsync` para la rama nula, con `Quantity = null` — sin sumar y sin elegir la de una tienda al
   azar, por lo mismo que la hidratación ya razona—, y **un test que le pase `null` y compruebe que un
   producto de varias tiendas vuelve una sola vez**. Sin ese test la mina vuelve a quedar dormida y sin
   guarda.
2. `AssistedSearchRequest.PointOfSaleId` a `Guid?`; el validador retira `.NotEmpty()` y **rechaza
   `Guid.Empty`** con el mismo criterio y el mismo texto que ya usa el controlador de la consulta libre:
   ausencia es que la clave no esté, y cualquier otra cosa es un valor que tiene que ser usable.
3. `AuthoriseAsync` omitida con nulo; `AiCallScope.ForAllPointsOfSale` en vez de `ForPointOfSale`;
   el predicado del interruptor por el método de extensión que C40_FIX extrajo, que ya resuelve el nulo.
4. `RecordAsync` omitido sin tienda, como ya hace `FreeQuerySearchService`.
5. `AssistedSearchResponse.PointOfSaleId` a `Guid?`.
6. En el frontend, retirar la fijación de ruta de `assisted.tsx` —`effectiveRoute`— y el motivo de
   ámbito del lado semántico del toggle, más los dos tests que los fijan.

### Lo que esto ensancharía, y hay que decirlo al hacerlo

**El hueco de telemetría.** Hoy una consulta global no se registra, y con el control limitado al
administrador eso es marginal. Si la ruta rápida acepta el ámbito, las búsquedas globales **semánticas**
tampoco quedarían registradas, y ésas sí son la ruta por defecto: el agujero pasa de un puñado de
consultas de administración a algo que puede sesgar la comparación de las dos rutas sobre la telemetría.
La tarea de arriba —*«Una búsqueda en “todos los puntos de venta” no queda registrada»*— sube de
prioridad en ese momento, no antes.

Anotado al implementar C40_FIX, cuya exploración encontró las dos mitades: el 400 de la ruta rápida no
figuraba en ninguna pasada anterior del ticket, y la mina de la rama léxica no figuraba en ninguna
parte.

---

### La sonda de disponibilidad es más estricta que la ruta que describe — decisión de producto pendiente

**Hallado por la verificación independiente de C40_FIX (2026-09-26), medido por HTTP y fijado en un test.**
No se arregló aquí a propósito: **qué lado está mal es una decisión de producto**, y cambiar cualquiera de
los dos altera comportamiento entregado por C40.

**El hecho.** `AssistedSearchService.GetAvailability` responde

```csharp
AssistedAnswerAvailable = freeQueryOptions.IsEnabledForScope(pos) && assistOptions.IsEnabledForScope(pos);
```

y `FreeQuerySearchService` —la ruta que esa bandera describe— aplica **sólo el primero**. El segundo,
`AiSalesAssistOptions`, no se lee en ningún punto del camino de la consulta libre: lo lee
`SalesAssistService`, que sirve la ficha de venta, otra ruta.

**Medido contra la API en marcha**, con `AiFreeQuerySearch__EnabledByDefault=true` y
`AiSalesAssist__EnabledByDefault=false`:

| Llamada | Respuesta |
|---|---|
| `GET /api/ai/search/availability` (sin tienda) | `assistedAnswerAvailable: false`, `switched_off` |
| `POST /api/ai/search/assisted` (sin tienda) | `200` · `aiAvailable: true` · `pitchStatus: "generated"` · prosa real |

**Por qué importa, y por qué no es cosmético.** En el panel, con el ámbito «todas las tiendas»
seleccionado, esa combinación deshabilita **las dos** opciones del selector de vía y escribe *«La búsqueda
en todas las tiendas usa la respuesta asistida, y está desactivada»* — de un ámbito que el backend sirve
sin problema. Es el defecto que C40_FIX vino a cerrar —una capacidad que funciona, inalcanzable desde la
pantalla, con un motivo falso escrito al lado—, alcanzable por una combinación de interruptores en vez de
por una opción que falta. Y roza el `MUST NOT` vivo de `ai-free-query-search`:

> *«…and MUST NOT reuse the switch of assisted search nor the switch of the sale card, because the three
> are different features with different cost profiles.»*

La ruta, en rigor, no lo reutiliza; **la pantalla sí**, porque deshabilita la vía sobre esa lectura. El
efecto neto es que el interruptor de la ficha de venta gobierna si un operario puede usar la consulta
libre desde el panel, que es exactamente lo que ese requisito prohíbe.

**Las dos salidas, y lo que cuesta cada una.**

1. **Aflojar la sonda** a `freeQuery` a secas. La sonda pasaría a describir exactamente lo que la ruta
   hace, y el requisito de C40_FIX —*«resolving the absence by the very rule the search route resolves it
   with»*— se cumpliría de arriba abajo. Coste: si alguien apaga la ficha de venta esperando apagar
   también la prosa del panel, deja de ocurrir — así que hay que comprobar si esa expectativa existía en
   C34/C40 antes de tocarlo.
2. **Hacer que la ruta lo aplique**, leyendo `AiSalesAssistOptions` en `FreeQuerySearchService`. Coherente
   con el texto del comentario que había en `GetAvailability` —*«whether the AI service will write prose
   for this shop»*—, pero **contradice el `MUST NOT` citado arriba**, que existe precisamente para que los
   tres interruptores no se compartan.

La primera parece la correcta por ese `MUST NOT`. No se decide aquí.

**Qué hay puesto mientras tanto:** `AiScopePredicateAgreementTests` construye la sonda y la ruta sobre las
mismas opciones, **ejecuta la ruta** y compara veredictos;
`Probe_AlsoReportsTheSaleCardSwitch_WhichTheRouteNeverApplies` fija la respuesta de hoy, de modo que quien
la cambie tiene que pasar por ahí y leer esta nota.

---
