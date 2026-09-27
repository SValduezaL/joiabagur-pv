# T-AIENG-013: Product-document indexer from catalog feed (C13)

> Ticket técnico del change OpenSpec `add-product-document-indexer`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-013](../../../../Documentos/Historias/AI-Eng/HU-AIENG-013.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C13, §0 C06a/C12, §6.3), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §6.3, §7.2, §8.1.1), sesión de exploración 2026-08-26, código real de `ai-service/src/` y `backend/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-013 / C13** — `POST /v1/index/sync` y `GET /v1/index/status` reales: pull del feed de catálogo, upsert por hash, tombstones, procedencia, Alembic `text_provenance`, OpenAPI keyset

---

## Contexto y Problema

C11 dejó una biblioteca que `api.main` **no** importa. C12 dejó un feed HTTP que Python **aún no** consume. `/v1/index/sync` y `/v1/index/status` son el stub C02: con `STUB_MODE=false` responden **501** nombrando este change. Sin C13, C14 consulta HNSW sobre cero filas (fallo mudo de S11) o bien viola §6.3 leyendo `public`.

El contrato C02 describe el cursor de sync como un `datetime`. El feed C12 pagina con keyset `(watermark, sinceId)`. Un solo instante pierde empates. C13 es el primer consumidor real de `/v1/index/*` (`IAiGatewayClient` no tiene operación de índice): se renegocia OpenAPI ahora, mismo precedente que C08.

C12 no emite procedencia. `data_origin` es NOT NULL. El `Dockerfile` no copia `data/catalog/`. C06a adjudicó `text_provenance` a C13. El mapa SKU va en `src/`.

AutoBulk de los 1.200 **ya está corrido** (confirmado 2026-08-26). El feed de catálogo no está vacío. El smoke posterior puede exigir 1.200 documentos; los pytest no.

**Estado actual del código y de la BD (verificado 2026-08-26 en repo; AutoBulk confirmado por el equipo):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-product-document-indexer` | **Scaffold** (`.openspec.yaml`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `ai-service/src/jbg_ai/indexing/` | C11: `source_text.py`, `embeddings.py`, `constants.py`, `errors.py`. `__init__` no exporta el cliente HTTP ni SQL |
| `jbg_ai.api.main` | **No** importa `indexing` (test de C11). C13 **debe** importar desde el router |
| `api/routers/index.py` | Stub; `DELIVERED_BY = "C13 (...)"`; usa `get_service_principal` (**exige `pos_id`**, contra `ai-service-auth` y el comentario de `auth.py`) |
| `api/schemas/index.py` | `IndexSyncRequest`: `since: datetime \| None`, `full: bool`, `batch_size` default 100. **Sin** `since_id`. Response `cursor: datetime \| None` |
| `openapi.json` | Congelado. Este change **sí** lo regenera (opción B) |
| `Settings` | `JPV_EMBEDDING_*` opcionales al boot. **Sin** `JPV_INDEX_FEED_*` |
| `canonical_openapi_settings` | Debe pinnear las settings nuevas de feed a ausentes / defaults |
| `db/engine.py` | Pool 5, lazy, `session_scope`. Cero queries de producto |
| Alembic | Una revisión: `f46c55c056e2` (`product_document` **sin** `text_provenance`; `sync_failure` sin `since_id` / `product_id`; **sin** `sync_checkpoint`) |
| `ai.product_document` | `data_origin` CHECK `real\|synthetic`; `embedding` NULABLE; `tsv` generada `spanish` |
| Dockerfile | Copia `src`, `migrations`, `prompts`. **No** `data/` |
| JSONL | 436 real (`SKU01`…, `merchant`/`ai_assisted`) + 764 synthetic (`SKU440`…); 1.200 total. Hueco `SKU437`–`SKU439` |
| Feed .NET | `GET /api/ai/index-feed/catalog` pág. 50, `X-Index-Feed-Key`, tombstones `kind`+`reason`, `aggregateHash` global. POS pág. 200 **existe**; C13 no lo drena |
| `IAiGatewayClient` | Retrieval + enrich. **No** index sync |
| Compose `jbg-ai` | `STUB_MODE=true`, `DATABASE_URL` al postgres interno. Backend **no** es servicio Compose (`dotnet run` en `:5056`) |
| `"Products"` / perfiles | 1.200 / AutoBulk **ejecutado** (1.200 `Approved`) |
| `indexing/embeddings.py` | **Congelado** (C11). C13 no lo edita |
| Spec viva `embedding-management` | Visual 1280d. **No se toca** |
| HU-AIENG-013 | **Creada** y alineada con este ticket |

**Impacto en producto:** ninguno visible. El valor es habilitador: C14 deja de recuperar sobre un índice vacío.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/indexing/` | Cliente de feed, orquestador de sync, mapa `sku_provenance.json`, CLI, repositorio. **No** editar `embeddings.py` |
| `ai-service/src/jbg_ai/api/routers/index.py` | Implementación real; `get_catalog_principal`; patrón stub/real de C09 |
| `ai-service/src/jbg_ai/api/schemas/index.py` | `since_id` / `cursor_id`; documentar `batch_size` como ignorado |
| `ai-service/src/jbg_ai/api/main.py` | Importar el orquestador **desde el router**, no al boot si se puede evitar arrastrar LiteLLM; el HTTP sí usa `indexing` |
| `ai-service/src/jbg_ai/config/settings.py` | `JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY`; opcional tope de tiempo (default 180). Pin en `canonical_openapi_settings` |
| `ai-service/migrations/versions/` | **Nueva** revisión Alembic (mano; no autogen) |
| `ai-service/openapi.json` | **Regenerar** |
| `ai-service/tests/indexing/` | Sync, upsert, tombstone, drift, procedencia, aislamiento |
| `ai-service/tests/api/` | Catalog token en `/v1/index/*`; snapshot |
| `ai-service/tests/migrations/` | `text_provenance` CHECK, checkpoint, columnas de `sync_failure` |
| `backend/.env.example` · Compose | URL/key de feed (placeholder). Contenedor: `host.docker.internal:5056` |
| `openspec/changes/add-product-document-indexer/` | proposal, **design.md**, specs, tasks |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-013 (**en el apply**) |
| `Documentos/modelo-de-datos.md` | `text_provenance`, `sync_checkpoint`, drift |
| `backend/` API, `frontend/`, EF Core | **Sin cambios** |

---

## Especificaciones Técnicas

### Auth y disparo

Rutas de índice: `get_catalog_principal` (`CATALOG_CLAIMS`, sin `pos_id`). Alineado con `ai-service-auth` (ya lo exige) y con enrich C09. Añadir test gemelo de `test_catalog_token_without_pos_is_accepted_on_enrich`.

`STUB_MODE=true` → stubs C02 (contratos actuales siguen verdes **hasta** regenerar el snapshot; después el stub debe rellenar `since_id`/`cursor_id` nulos o deterministas).

`STUB_MODE=false` → pipeline real. Falta de `JPV_INDEX_FEED_API_KEY`, `JPV_INDEX_FEED_BASE_URL`, `JPV_EMBEDDING_API_KEY` o del mapa → **503** con detalle que nombra la setting, no 501. `/health` no las exige.

Token hacia estas rutas: JWT interno HS256 (`JWT_SECRET`), **no** la API Key del feed. La API Key solo viaja Python → .NET en `X-Index-Feed-Key`.

### OpenAPI — **BREAKING** aditivo (opción B)

`IndexSyncRequest`:

| Campo | Tipo | Notas |
|---|---|---|
| `since` | datetime \| null | Watermark del keyset |
| `since_id` | uuid \| null | Segunda componente. Ausente + `since` ausente = usar checkpoint o full |
| `full` | bool default false | Ignora checkpoint y body cursor; drena desde el origen del feed |
| `batch_size` | int 1–1000 default 100 | **Ignorado.** Log warning una vez. Página = 50 de C12 |

`IndexSyncResponse`: además de contadores, `since` / `since_id` (de dónde arrancó) y `cursor` / `cursor_id` (dónde quedó). `skipped` = ítems cuyo embed se omitió.

Regenerar `openapi.json` con `canonical_openapi_settings`. `test_openapi_snapshot_is_stable` verde **después**.

### Cliente de feed (reutilizable, C22 lo importa)

- Base URL + header `X-Index-Feed-Key`. Comparación no aplica en Python: se **envía**.
- Query `since` / `sinceId` según `IndexFeedCursorDto`. Primera página: omitir ambos.
- Parsear `kind` `upsert` \| `tombstone`. Mapear camelCase → `ProductSourceText` (C11) + `product_id`, `family_id`, `price`, `price_band`, `is_active`, `watermark`.
- Puerto inyectable. Tests **sin** HTTP a `:5056`.
- Método/path POS en el cliente; C13 **no** lo invoca.

### Lookup de procedencia (A3 + B4)

Generar **una vez** (script de apply o comando documentado) desde:

- `data/catalog/real/generated/catalog-real-enriched.jsonl`
- `data/catalog/synthetic/generated/catalog-synthetic.jsonl`

Escribir `ai-service/src/jbg_ai/indexing/sku_provenance.json`:

```json
{ "SKU01": { "data_origin": "real", "text_provenance": "ai_assisted" } }
```

Invariantes de test (pytest en el repo, lee `data/`): 1.200 claves; 436 `real` / 764 `synthetic`; 387 `ai_assisted` / 49 `merchant` / 764 `synthetic`; cero solapes; toda clave de JSONL presente.

Runtime: solo el JSON en `src/`. Mapa ausente o ilegible → no se escribe ninguna fila (A3). SKU del feed ∉ mapa → `sync_failure`, `failed += 1`, resto sigue (B4). **Prohibido** default `synthetic` o heurística `SKU01`–`SKU436` (el sintético empieza en `SKU440`; hay hueco).

No persistir `text_quality_tier`.

### Alembic (una revisión, a mano)

1. `ai.product_document.text_provenance text NOT NULL` + CHECK `IN ('merchant','ai_assisted','synthetic')` + índice B-tree. Tabla vacía hoy → sin backfill.
2. `ai.sync_checkpoint`: una fila por `feed` (texto, p. ej. `catalog`). Columnas: `watermark timestamptz`, `since_id uuid`, `last_full_sync_at`, `last_incremental_sync_at`, `last_aggregate_hash char(64)`, `indexed_count int`.
3. `ai.sync_failure`: `cursor_since_id uuid` nullable, `product_id uuid` nullable. No usar esta tabla como bookmark.

Downgrade: drop columnas/tablas nuevas; no tocar las seis tablas de C05 más allá de `text_provenance`. Sin ENUM (C05 decisión 6).

### Upsert y tombstone

```
tombstone → DELETE WHERE product_id = :id
            deleted += rowcount  (0 = no-op, no cuenta)

upsert    → build_source_text / hash_source_text (C11)
            lookup procedencia (B4/A3)
            si stored.hash == new.hash y embedding presente:
                 UPDATE columnas (precio, price_band, family_*, tags,
                                  is_active, data_origin, text_provenance,
                                  indexed_at, doc_text, source_hash)
                 skipped += 1
            si no:
                 embed([doc_text])  # C11, assert 1536
                 UPSERT atómico fila + vector
                 upserted += 1
```

`doc_text` se escribe siempre (columna NOT NULL; el `tsv` se genera). Un PVP nuevo no cambia el hash y **sí** actualiza `price` / `price_band`.

No dejar embedding NULL visible. Si el embed falla: no pisar fila previa; `sync_failure`; continuar.

`embedding_model` / `embedding_version` = `document_version_key` de C11 (`{model}:1536:source-text/v1`).

### Dreno, checkpoint, tope

`full=true` o checkpoint ausente: `GET` catálogo sin cursor, luego seguir `nextCursor` hasta null o hasta el tope de tiempo (`JPV_INDEX_SYNC_TIME_BUDGET_SECONDS`, default **180**).

Al cortar por tiempo: persistir checkpoint del último ítem **procesado con éxito**; response con cursor; contadores parciales; HTTP 200 (no 500). El caller (CLI o segundo POST) reanuda.

Incremental: partir del checkpoint, salvo que el body traiga `since`+`since_id` (entonces esos ganan y se ignoran para no tener dos fuentes; documentar: body override, `full` gana sobre ambos).

**Default si el apply duda:** `full=true` ignora body y checkpoint; incremental sin body usa checkpoint; body completo `(since, since_id)` sustituye checkpoint para esa tirada.

CLI: `python -m jbg_ai.indexing sync [--full]`. Misma función que el router. No cron.

### `drift_count`

`GET /status`:

1. SHA-256 de `product_id` en `ai.product_document`, mismo algoritmo que C12 (`IndexFeedAggregateHash.OfProductIds`: uuid canónico, ordenados).
2. `GET` **solo** la primera página del feed catálogo → `aggregateHash`.
3. Iguales → `drift_count = 0`. Distintos → `drift_count = max(1, abs(indexed_documents − checkpoint.indexed_count))`.

Content drift ≠ set drift. El primero lo cubre el incremental + `source_hash`. Status **no** pagina 24 veces.

### Acceso a datos

Repositorio async inyectable, SQLAlchemy Core (o mapped class **prohibida** como fuente de `alembic revision --autogenerate`). Fake en tests, como `request.app.state.enrich_llm`.

Pool existente (5, sin overflow). No abrir un segundo engine.

### Tests (nombres Python `test_<unidad>_<escenario>_<esperado>`)

Obligatorios de la ficha, reinterpretados:

| Ficha | Lectura acordada |
|---|---|
| `test_upsert_is_idempotent_for_same_source_hash` | Mismo hash → **cero** llamadas al fake de embed; columnas sí se actualizan (p. ej. precio) |
| `test_tombstone_removes_document_from_index` | DELETE; segundo tombstone no-op |
| `test_tsvector_uses_spanish_configuration` | **No** reassertar `spanish` (C05). Sustituir por `test_upsert_leaves_tsv_not_null` |
| `test_status_reports_drift_when_counts_diverge` | Hashes de conjunto distintos → `drift_count >= 1`; un solo GET de feed (fake) |
| `test_failed_batch_recorded_and_does_not_block_others` | Un ítem a `sync_failure`; los demás upserted |

Más: mapa = JSONL; SKU huérfano; mapa ausente no escribe; catalog token sin POS; `batch_size` ignorado; dimensión ≠ 1536 no se persiste. Cero sockets. Migración: CHECK de `text_provenance`, tabla checkpoint. Omitir tests de BD si Docker no responde (C05).

---

## Arquitectura

```
  CLI o POST /v1/index/sync          JWT interno (sin pos_id)
              │
              ▼
  orquestador (indexing/) ──► feed client ── X-Index-Feed-Key ──► GET .../catalog
              │                                                    pág. 50, keyset
              ├─ ProductSourceText → C11 hash/embed
              ├─ sku_provenance.json
              └─ repo Core ──► ai.product_document / sync_checkpoint / sync_failure
```

Decisiones heredadas: §6.3 pull; C05 frontera `ai`/`public`; C11 skip-embed por hash; C12 API Key y tombstones `kind`+`reason`; C09 stub vs real.

**Breaking:** snapshot OpenAPI de índice. Nadie en .NET llama estas rutas hoy. Stubs de contrato y `sample_requests.py` hay que alinear.

No hay breaking del API .NET ni de EF.

---

## Definición de Hecho (DoD)

- [ ] Código según C4 / `openspec/project.md` (Python vectorial; .NET no se toca)
- [ ] `uv run pytest` verde **sin** llamadas reales a embeddings, LLM, API .NET ni RDS
- [ ] Tests nuevos: nombres `test_<unidad>_<escenario>_<esperado>`; fakes de feed y embed
- [ ] Migración Alembic aplicable y reversible; tests de esquema en contenedor pgvector (omitir si no hay Docker)
- [ ] `openapi.json` regenerado; `test_openapi_snapshot_is_stable` verde
- [ ] Specs delta en `openspec/changes/add-product-document-indexer/specs/` y `openspec validate --all --strict` → 0 failed
- [ ] `embeddings.py` sin diff. Feed POS no drenado. Sin migración EF
- [ ] Documentación: HU, este ticket, `epicas.md` y `modelo-de-datos.md` en el apply
- [ ] Sin TODO/FIXME huérfano
- [ ] Verificación **posterior** (no merge): smoke local `indexed_documents = 1200`, `drift_count = 0`

No aplica: xUnit, Vitest, UI es-ES, cobertura frontend.

---

## Requisitos No Funcionales

- **Seguridad:** tercer secreto (`JPV_INDEX_FEED_API_KEY`) ≠ `JWT_SECRET` ≠ `JPV_EMBEDDING_API_KEY`. La key no se loguea. Producción: SSM en **C17**. Token de índice sin `pos_id` (no inventar wildcard).
- **Rendimiento / free-tier:** pool 5; página 50; batch embed 64 (C11); tope 180 s; ~1.200 vectores. No abrir conexiones de overflow.
- **Observabilidad:** `trace_id` del token; logs de página/sync (contadores, hash truncado, cache_hits). Sin dump de `doc_text` ni de keys a Information.
- **Integridad:** procedencia no se adivina; no hay fila recuperable sin vector; tombstone idempotente; Python no escribe `public`.

---

## Preguntas Abiertas

Ninguna pendiente de producto. Cerradas en exploración (2026-08-26), incluida **B4+A3**.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿OpenAPI? | **Renegociar** (`since_id` / `cursor_id`) |
| 2 | ¿Idempotencia? | Skip embed; UPSERT de columnas siempre |
| 3 | ¿Procedencia? | Mapa en `src/` + Alembic. A3 + B4 |
| 4 | ¿POS / scheduler? | **No.** Cliente sí; dreno no |
| 5 | ¿Un POST drena? | **Sí**, con tope 180 s |
| 6 | ¿Aislamiento? | Por ítem |
| 7 | ¿Fila sin embedding? | **No** visible |
| 8 | ¿Checkpoint? | Tabla propia; no `sync_failure` |
| 9 | ¿`drift_count`? | Hash de conjunto, 1 GET |
| 10 | ¿DoD 1.200 en pytest? | **No.** Smoke posterior |
| 11 | ¿CLI? | **Sí**, misma función que el HTTP |
| 12 | ¿Altas a mano? | **No.** Mapa = 1.200 |
| 13 | ¿Body vs checkpoint? | `full` > body keyset > checkpoint |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** drene el POS, **no** edite `embeddings.py` y **no** abra migración EF.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. Desbloquea C14 y C18.
- **Estimación:** **8 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C11 y C12 archivados; AutoBulk ejecutado (ops). **Bloquea** C14. C22 reutiliza el cliente. No paralelizar con C23.
- **Línea de corte:** si desborda (regla 5): (1) Alembic + mapa + cliente + upsert/tombstone con fakes, archivable; (2) router real + OpenAPI + CLI + status/drift.
- **Tags:** `HU-AIENG-013`, `C13`, `EP14`, `ai-service`, `python`, `indexing`, `pgvector`, `alembic`, `openapi`, `feed-client`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-013](../../../../Documentos/Historias/AI-Eng/HU-AIENG-013.md)
- **Change OpenSpec:** `openspec/changes/add-product-document-indexer/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C13) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.3, §7.2, §8.1.1)
- **Apuntes del Máster (guía, no dogma):** [S8 esquema](../../../../Documentos/Sesiones%20Master%20AIEng/S8_BBDD_Vectoriales/Diseño%20del%20esquema%20y%20busqueda%20semantica.md) · [S9 RAG](../../../../Documentos/Sesiones%20Master%20AIEng/S9_Fundamentos_RAG/Del%20CAG%20estatico%20al%20flujo%20RAG%20-%20Las%20cuatro%20etapas%20y%20por%20que%20el%20Retrievel%20domina.md)
- **Specs vivas:** `catalog-source-text` · `index-feed` · `ai-vector-schema` · `ai-service-api-contracts` · `ai-service-auth` · `ai-service-runtime`
- **Precedentes:** C09 (`enrich.py` stub/real) · C11 (`ProductSourceText`, `LiteLlmEmbeddingClient`) · C12 (`IndexFeedPageDto`, `X-Index-Feed-Key`) · C05 (Alembic a mano, CHECK no ENUM)
- **Contrato Python:** `ai-service/openapi.json` — **sí se modifica**
- **Runbook AutoBulk:** [c12-catalog-autobulk-runbook.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c12-catalog-autobulk-runbook.md) (ya ejecutado; no es trabajo de este ticket)
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-26 | `/enrich-us` | Creación a partir de HU-AIENG-013 y de la exploración. Recoge: OpenAPI keyset (B), skip-embed ≠ skip-fila, mapa `src/` A3+B4, cliente de feed sin dreno POS, dreno+tope 180 s+CLI, aislamiento por ítem, cero fila sin vector, `sync_checkpoint`, drift por hash, smoke 1.200 fuera del merge |
