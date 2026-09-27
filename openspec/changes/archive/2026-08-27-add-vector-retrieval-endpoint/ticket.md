# T-AIENG-014: Vector retrieval on POST /v1/retrieval/products (C14)

> Ticket técnico del change OpenSpec `add-vector-retrieval-endpoint`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-014](../../../../Documentos/Historias/AI-Eng/HU-AIENG-014.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C14, §0 `query_log`), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §7.6), sesión de exploración 2026-08-27, código real de `ai-service/src/` y `backend/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-014 / C14** — `POST /v1/retrieval/products` real: embed de query, `<=>` HNSW cosine, umbral de distancia 0,65, overfetch, filtros del body, 503 de índice vacío vs abstención 200

---

## Contexto y Problema

C13 dejó un índice consultable. C02 congeló el contrato. C03 ya llama con timeout **800 ms** y no trunca el overfetch. `/v1/retrieval/products` es el stub: `STUB_MODE=true` → fixtures; `false` → **501** (`PRODUCTS_DELIVERED_BY = "C14 (add-vector-retrieval-endpoint)"`). Sin C14, C15 hidrata aire o se queda en el circuito abierto.

El default OpenAPI de `mode` es `hybrid`. C14 **solo sabe vector**. Devolver 501 en hybrid rompería el primer encendido real. Hasta C21, hybrid y lexical ejecutan la rama vectorial y lo declaran en `debug.notes`.

El score del contrato es `[0, 1]`. pgvector cosine `<=>` es distancia `[0, 2]`. El umbral vive en SQL sobre distancia; la conversión a score es del handler. Default **0,65**, a calibrar en C24. Sin relajación.

C05 no creó `ai.query_log`. C14 no la improvisa: logs estructurados por etapa + `trace_id`. C04 (`ProductSearchEvent`) cubre el lado .NET **después** de hidratar.

Índice local verificado 2026-08-27: **1.200 / 1.200 / 1536**. Smoke posterior, no pytest.

**Estado actual del código y de la BD (verificado 2026-08-27 en repo):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-vector-retrieval-endpoint` | **Scaffold** (`.openspec.yaml`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `api/routers/retrieval.py` | Stub; `require_stub_mode` → 501 en real; handler **sync** `def retrieve_products`; `get_service_principal` (exige `pos_id`); `payload.pos_id` ignorado |
| `api/schemas/retrieval.py` | `RetrievalRequest`: `query` 1–500, `top_k` 1–50 default 10, `filters`, `mode` default **hybrid**, `pos_id` opcional ignorado. Score `ge=0, le=1`. **No se toca el schema** |
| `RetrievalFilters` | `materials[]`, `category`, `family_id` (str), `exclude_product_ids[]`. Precio/stock **no** van aquí |
| `stubs/responses.py` | `over_retrieval_count` = `min(top_k × 3, 60)`. Reutilizar en real |
| `openapi.json` | Congelado. Este change **no** lo regenera |
| `jbg_ai/retrieval/` | **No existe** |
| `indexing/embeddings.py` | **Congelado** (C11). `LiteLlmEmbeddingClient.max_attempts` default `MAX_EMBED_ATTEMPTS=3`. Comentario: *C14 compares `model_version_key`* (`{model}:1536`) |
| `indexing/repository.py` | Escritor C13 (upsert/delete/checkpoint). **No** tiene `ORDER BY embedding <=>`. C14 no lo hincha: query propia en `retrieval/` |
| `api/routers/index.py` / `enrich.py` | Patrón stub vs real + `app.state` (`index_embed`, `enrich_llm`) a copiar |
| `Settings` | `JPV_EMBEDDING_*` opcionales al boot. **Sin** umbral de retrieval. `canonical_openapi_settings` debe pinnear el default nuevo |
| `db/engine.py` | Pool 5, lazy, `session_scope`. Primera sesión sin `DATABASE_URL` falla al pedirla |
| Alembic | Head C13 (`text_provenance`, `sync_checkpoint`). C14 **no** añade revisión |
| `ai.product_document` | 1.200 filas, 1.200 embedding NOT NULL 1536-d, `tsv`, GIN `materials`, B-tree `piece_type`/`family_id`, HNSW cosine. 66 `sync_failure` residuales SSL (ruido) |
| Compose `jbg-ai` | `STUB_MODE=true`. **No** inyecta `JPV_EMBEDDING_*` |
| Carga de key | `backend/.env` tiene `JPV_EMBEDDING_API_KEY`. Settings lee `.env` del cwd. No hay `ai-service/.env`. HTTP real mode = vars de proceso |
| `IAiGatewayClient` / C03 | `RetrievalTimeoutMs = 800`. Mapea `results`, `candidates_returned`, `low_confidence`, `effective_pos_id`. **Sin cambios** |
| `/v1/retrieval/substitutes` | Sigue stub/501 (C26). **No se toca** |
| HU-AIENG-014 | **Creada** y alineada con este ticket |

**Impacto en producto:** ninguno visible. El valor es habilitador: C15 deja de hablar con un 501.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/retrieval/` | **Nuevo.** Handler, SQL de búsqueda, mapeo score/filtros, logs de etapa |
| `ai-service/src/jbg_ai/api/routers/retrieval.py` | Rama real de `/products`; async; 503; patrón C09. Substitutes intacto |
| `ai-service/src/jbg_ai/config/settings.py` | `JPV_RETRIEVAL_DISTANCE_THRESHOLD` default 0,65. Pin en `canonical_openapi_settings` |
| `ai-service/tests/retrieval/` | **Nuevo.** Fakes de embed y repo; umbral; overfetch; orden; filtros; 503; hybrid=vector |
| `ai-service/tests/api/` | Stub sigue; token con `pos_id`; 503 sin key; snapshot **sin** regenerar |
| `ai-service/tests/config/` | Default y pin del umbral |
| `openspec/changes/add-vector-retrieval-endpoint/` | proposal, **design.md**, specs, tasks (aún scaffolding) |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-014 (**en el apply**) |
| `indexing/embeddings.py` | **Sin cambios** (solo instanciar con `max_attempts=1`) |
| `openapi.json`, Alembic, `backend/`, `frontend/`, EF Core | **Sin cambios** |

---

## Especificaciones Técnicas

### Auth y disparo

`get_service_principal` (claims `user_id`, `role`, `pos_id`, `trace_id`). Token sin `pos_id` → 401, igual que hoy. `payload.pos_id` se ignora; `effective_pos_id` = claim.

`STUB_MODE=true` → `retrieval_products_stub`, cero I/O. `false` → rama real. Quitar `require_stub_mode` **solo** de `/products`.

Handler **async** (embed + SQL). Substitutes puede seguir sync.

### Embed de la query

```
LiteLlmEmbeddingClient(..., max_attempts=1)
```

Misma clase C11. Indexador no se reconfigura. Preferir instancia inyectada `request.app.state.retrieval_embed` (nombre tentativo; no reutilizar `index_embed` si ese lleva 3 intentos). Sin key y sin fake inyectado → 503 nombrando `JPV_EMBEDDING_API_KEY`.

Un texto, un vector. `require_embedding_dimension` ya vive en el cliente. Fallo de proveedor → 503 (o el error HTTP que ya use C13 para embed; no 200 vacío).

Caché RAM por texto exacto: beneficio colateral, no requisito de producto.

### SQL de búsqueda

Operador `embedding <=> :query_vec` (cosine distance). Índice HNSW `vector_cosine_ops` (C05). **No** mezclar L2.

Predicados fijos:

- `embedding IS NOT NULL`
- `is_active IS TRUE`
- compatibilidad de modelo: `embedding_version` / `embedding_model` alineados con `model_version_key` del cliente vivo (p.ej. prefijo `{model}:1536` o igualdad de `embedding_model`). Cero filas compatibles → **503**, no abstención
- `embedding <=> :q <= :threshold` (`JPV_RETRIEVAL_DISTANCE_THRESHOLD`, default **0.65**)

Predicados del body, si vienen:

| Filtro | Columna | Semántica |
|---|---|---|
| `materials` no vacío | `materials` | solape `&&` (GIN) |
| `category` no nulo | `piece_type` | igualdad |
| `family_id` no nulo | `family_id` | igualdad UUID; string que no parsea → **422** |
| `exclude_product_ids` | `product_id` | `<> ALL`; UUIDs malformados se ignoran (debug), no tumbar la query |

**No** filtrar `pos_id`. **No** precio. **No** stock.

`ORDER BY embedding <=> :q ASC` + `LIMIT :overfetch` con `overfetch = min(top_k * 3, 60)`.

Overfetch **después** del umbral: el `LIMIT` aplica al conjunto ya filtrado por distancia.

### Score, razones, debug

`score = clamp(1.0 - distance, 0.0, 1.0)`. El schema Pydantic rechaza fuera de `[0, 1]`.

`match_reasons`: al menos `["vector"]`. No inventar `"lexical"` hasta C21.

`debug` (si se rellena): `vector_score = score`; `notes` incluye `vector_only_until_c21` cuando `mode` es `hybrid` o `lexical`. `mode=vector` no necesita esa nota.

### Abstención vs 503

| Situación | HTTP | Body |
|---|---|---|
| Stub on | 200 | fixtures C02 |
| Índice con compatibles; 0 hits tras umbral/filtros | **200** | `results=[]`, `candidates_returned=0`, `low_confidence=true` |
| Hay ≥1 hit | 200 | `low_confidence=false` |
| Count compatible = 0, o sin bootstrap / sin `DATABASE_URL` / sin key / embed falla de forma no recuperable | **503** | `detail` nombra el fallo; no `low_confidence` |

Sin relajación de umbral. Sin segundo round-trip.

### Observabilidad

Logs estructurados, dos etapas como mínimo:

- `stage=embed` — `trace_id`, `latency_ms`, `model`, `cache_hits`
- `stage=search` — `trace_id`, `latency_ms`, `distance_min` (null si 0 hits), `candidates`, `low_confidence`, `mode`, `threshold`

Query del operador: **solo Debug** (precedente C03/C04). No dump del vector.

**No** `INSERT` en `ai.query_log`.

### Contrato OpenAPI

Cero cambios de schema. `test_openapi_snapshot_is_stable` verde **sin** regenerar. `canonical_openapi_settings` pinnea el umbral al default para que el entorno no se cuele si algún test construye settings canónicos.

### Tests (nombres de la ficha + los que cierran las decisiones)

| Test | Qué prueba |
|---|---|
| `test_returns_empty_with_low_confidence_when_all_above_threshold` | Todas las distancias > umbral → 200, `[]`, `low_confidence=true` |
| `test_returns_overfetched_candidate_count` | `top_k=5` → como mucho 15, y no más que los que pasaron el umbral |
| `test_results_ordered_by_ascending_distance` | `score` no creciente (equiv. distancia no decreciente) |
| `test_trace_id_appears_in_stage_logs` | Caplog: `trace_id` en embed y search |
| `test_hybrid_and_lexical_modes_run_vector_branch` | No 501; nota `vector_only_until_c21` |
| `test_body_filters_materials_category_family_and_exclusions` | Los cuatro predicados |
| `test_empty_compatible_index_is_503_not_abstention` | Count 0 → 503 |
| `test_missing_embedding_key_is_503` | Sin key y sin fake → 503 |
| `test_stub_mode_still_returns_fixtures` | `STUB_MODE=true` no llama fake de embed |
| `test_retrieval_embed_client_uses_max_attempts_one` | La instancia de retrieval no reintenta |

Fakes: `EmbeddingClient` y un puerto de búsqueda (lista de filas con distancia). **Cero sockets.** No exigir 1.200 filas. Tests de BD pgvector: opcionales y *skip* si Docker no responde (precedente C05), no bloquean el merge.

---

## Arquitectura

```
  POST /v1/retrieval/products          JWT interno (con pos_id)
              │
              ├─ STUB_MODE=true ──► fixtures C02
              │
              └─ STUB_MODE=false
                     │
                     ├─ 503 si no key / no DB / count compatible = 0
                     │
                     ▼
              retrieval/ ── embed query (C11 client, max_attempts=1)
                     │
                     ▼
              SQL  embedding <=> q  ≤ threshold
                   + is_active + filters body
                   ORDER BY distance  LIMIT overfetch
                     │
                     ▼
              score = clamp(1-d, 0, 1)
              200  results / low_confidence
                     │
                     ▼
              C15 .NET (fuera de este change): hidrata, trunca, C04
```

Decisiones heredadas: §6.2 Python=parecido / .NET=números; C02 contrato; C03 800 ms; C05 HNSW cosine + GIN materials; C11 cliente y `model_version_key`; C13 índice poblado; C09 stub vs real.

**Breaking:** ninguno de OpenAPI ni de EF. El único breaking de *comportamiento* es que `STUB_MODE=false` deja de ser 501 y pasa a 200/503 reales — eso **es** este change.

No hay breaking del API .NET. C03 ya consume el schema.

---

## Definición de Hecho (DoD)

- [ ] Código según C4 / `openspec/project.md` (Python vectorial; .NET no se toca)
- [ ] `uv run pytest` verde **sin** llamadas reales a embeddings, LLM, API .NET ni RDS
- [ ] Tests nuevos: nombres `test_<unidad>_<escenario>_<esperado>`; fakes de embed y búsqueda
- [ ] `openapi.json` **sin** regenerar; `test_openapi_snapshot_is_stable` verde
- [ ] Specs delta en `openspec/changes/add-vector-retrieval-endpoint/specs/` y `openspec validate --all --strict` → 0 failed
- [ ] `embeddings.py` sin diff. Substitutes intacto. Sin Alembic. Sin migración EF
- [ ] Documentación: HU, este ticket, `epicas.md` en el apply
- [ ] Sin TODO/FIXME huérfano
- [ ] Verificación **posterior** (no merge): query obvia contra los 1.200 locales → 200 con candidatos; query absurda → 200 + `low_confidence`

No aplica: xUnit, Vitest, UI es-ES, cobertura frontend, regenerar OpenAPI.

---

## Requisitos No Funcionales

- **Seguridad:** `JPV_EMBEDDING_API_KEY` ≠ `JWT_SECRET` ≠ `JPV_RAG_LLM_*`. La key no se loguea. Query de operador solo en Debug. Producción: SSM en **C17**. Token de retrieval **con** `pos_id`.
- **Rendimiento / free-tier:** pool 5; un embed (no batch); `max_attempts=1` para no pelear con 800 ms; `LIMIT` ≤ 60; HNSW cosine. No overflow de conexiones.
- **Observabilidad:** `trace_id` del token; logs `stage=embed|search`. Sin `query_log`. Sin dump de vectores a Information.
- **Integridad:** Python no lee `public`. Score siempre en `[0, 1]`. Cero fila recuperada sin vector. Abstención ≠ índice caído.

---

## Preguntas Abiertas

Ninguna pendiente de producto. Cerradas en exploración (2026-08-27).

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿`mode=hybrid` 501 hasta C21? | **No.** Vector + nota `vector_only_until_c21` |
| 2 | ¿Umbral sobre score o distancia? | **Distancia** en SQL. Score = `clamp(1 − d, 0, 1)`. Default **0,65** |
| 3 | ¿Filtros del body? | **Honrarlos** en C14. Extracción desde texto = C21 |
| 4 | ¿Reintentos de embed? | Retrieval `max_attempts=1`. No editar `embeddings.py` |
| 5 | ¿Índice vacío 200 o 503? | **503**. Abstención real = 200 + `low_confidence` |
| 6 | ¿`ai.query_log`? | **No.** Logs + `trace_id`. C04 cubre post-hidratación |
| 7 | ¿OpenAPI? | **No** regenerar |
| 8 | ¿`family_id` inválido? | **422**. `exclude_product_ids` malformados se ignoran |
| 9 | ¿Filtrar por POS? | **No** (C22 + C15) |
| 10 | ¿DoD 1.200 en pytest? | **No.** Smoke posterior |
| 11 | ¿`design.md`? | **Sí** (el plan v3 no lo pedía; las decisiones lo exigen) |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** edite `embeddings.py`, **no** regenere OpenAPI, **no** cree `query_log` y **no** filtre por POS.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. Desbloquea C15, C21, C22, C24.
- **Estimación:** **5 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C13 archivado; índice local 1.200 (ops). **Bloquea** C15. C20/C21/C22 se sientan encima. No paralelizar con un change que edite `embeddings.py` (C23).
- **Línea de corte:** si desborda (regla 5): (1) embed + `<=>` + umbral + 200/503 + stub intacto, archivable; (2) filtros del body + nota de `mode` + logs de etapa.
- **Tags:** `HU-AIENG-014`, `C14`, `EP14`, `ai-service`, `python`, `retrieval`, `pgvector`, `hnsw`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-014](../../../../Documentos/Historias/AI-Eng/HU-AIENG-014.md)
- **Change OpenSpec:** `openspec/changes/add-vector-retrieval-endpoint/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C14) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §7.6)
- **Apuntes del Máster (guía, no dogma):** [S9 retrieval](../../../../Documentos/Sesiones%20Master%20AIEng/S9_Fundamentos_RAG/Retrieval%20que%20no%20es%20solo%20cosine%20-%20top-K,%20threshold%20y%20filtros%20sobre%20pgvector.md)
- **Specs vivas:** `ai-service-api-contracts` · `ai-service-auth` · `ai-service-runtime` · `ai-vector-schema` · `product-document-indexer` · `catalog-source-text` · `ai-gateway-client`
- **Precedentes:** C09 (`enrich.py` stub/real) · C11 (`LiteLlmEmbeddingClient`, `model_version_key`) · C13 (`index.py` 503 + `app.state`) · C02 (contrato) · C03 (800 ms)
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-27 | `/enrich-us` | Creación a partir de HU-AIENG-014 y de la exploración. Recoge: hybrid=vector hasta C21, umbral distancia 0,65, filtros del body, `max_attempts=1`, 503 vs abstención, sin `query_log`, sin OpenAPI, `design.md` obligatorio |
