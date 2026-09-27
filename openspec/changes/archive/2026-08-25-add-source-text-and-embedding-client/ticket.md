# T-AIENG-011: Canonical SourceText and hash-keyed embedding client (C11)

> Ticket técnico del change OpenSpec `add-source-text-and-embedding-client`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-011](../../../../Documentos/Historias/AI-Eng/HU-AIENG-011.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C11, §0 C05/C07/C08, §7), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.3, §7.1, §7.2, D3), sesión de exploración 2026-08-25, código real de `ai-service/src/` y `backend/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-011 / C11** — Biblioteca `jbg_ai.indexing`: `source-text/v1`, SHA-256 de `doc_text`, cliente LiteLLM de embeddings 1536d con caché in-memory, sin HTTP ni SQL

---

## Contexto y Problema

C05 dejó `ai.product_document` con `doc_text`, `source_hash`, `embedding vector(1536)` nulable y metadatos de modelo, **vacía**. C09 extrae perfiles reales. C08 persiste `ProductAiProfile` y ya advierte que su `SourceHash` **no** es el del índice. Lo que falta es la pieza que el plan llama *«lo que hace barato y determinista todo el reindexado»*: un texto canónico estable y un cliente que no vuelva a pagar el modelo si el hash no cambió.

Sin C11, C13 tendría que inventar el `SourceText` dentro del *upsert* (el sitio peor: mezclado con tombstones y el feed) y C14/C23 reimplementarían el cliente. El plan congela `indexing/embeddings.py` aquí precisamente para que eso no ocurra, y prohíbe C11 ‖ C13.

Esta biblioteca **no indexa el catálogo**. En Docker local (2026-08-25) hay 1.200 productos y **0** `ProductAiProfiles`; el esquema `ai` **no está** en ese volumen. El primer sync real es C13, después de C12 y de un AutoBulk que **no** es de este ticket.

**Estado actual del código y de la BD (verificado 2026-08-25):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-source-text-and-embedding-client` | **Scaffold** (`.openspec.yaml`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `ai-service/src/jbg_ai/indexing/` | **Ausente** |
| `POST /v1/index/sync` · `GET /v1/index/status` | Stub C02; `DELIVERED_BY = "C13 (...)"`. Con `STUB_MODE=false` → 501 |
| `ai-service/openapi.json` | **No debe cambiar** |
| `Settings` | `JPV_RAG_LLM_*` y `JPV_CATALOG_LLM_*` opcionales al boot. **Sin** `JPV_EMBEDDING_*` como campos (sí esbozados en `.env.example`) |
| `backend/.env.example` | Reserva `JPV_EMBEDDING_API_KEY` / `JPV_EMBEDDING_MODEL`. Falta `BASE_URL` |
| `jbg_ai.enrichment.llm.LiteLlmEnrichClient` | Runtime C09, `acompletion`, temp 0. **No** sirve para embeddings |
| `jbg_ai.data.llm.OpenAICatalogLlm` | CLI C06b. `api.main` no importa `jbg_ai.data`. **No** reutilizar |
| `pyproject.toml` | `litellm==1.98.0`, `openai>=1.68.0`. No hace falta dependencia nueva de embeddings |
| `ai.product_document` (migración C05) | `doc_text` NOT NULL, `source_hash CHAR(64)`, `embedding vector(1536)` nulable, `embedding_model`/`embedding_version` texto nullable |
| Schema `ai` en Docker local | **No existe** (bootstrap C05 no corrido en `jpv-pv-postgres-data`) |
| `"ProductAiProfiles"` | **0 filas** (migración C08 aplicada; AutoBulk no ejecutado) |
| `"ProductFamilies"` | **0** |
| `"Products"` | **1.200**. Mundo C10: 12 POS, 6.720 inventario, 22.961 ventas |
| `ProductAiProfile.SourceHash` | SHA-256 de **entradas** (SKU, name, description, collection). Distinto propósito |
| Spec viva `embedding-management` | Reconocimiento **visual** 1280d. **No se toca** |
| `tests/indexing/` | Nombre **reservado** en `tests/README.md`; carpeta aún no creada |
| HU-AIENG-011 | **Creada** y alineada con este ticket |

**Impacto en producto:** ninguno visible. El valor es habilitador: C13 deja de decidir el texto y C14/C23 dejan de copiar el cliente.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/indexing/` | **Nuevo** — `source_text.py` (constructor + hash), `embeddings.py` (puerto + adapter + caché). Congelar `embeddings.py` |
| `ai-service/src/jbg_ai/config/settings.py` | Añadir `JPV_EMBEDDING_API_KEY` / `MODEL` / `BASE_URL` / `BATCH_SIZE` (default 64), opcionales al boot; pin en `canonical_openapi_settings` |
| `ai-service/tests/indexing/` | **Nuevo** — tests de la ficha + dimensión + boot sin clave |
| `ai-service/tests/support/` | Fake inyectable del puerto de embeddings (el README ya lo nombra) |
| `ai-service/tests/config/` | Settings: embeddings ausentes no bloquean `/health`; blank → unset |
| `backend/.env.example` | Completar `JPV_EMBEDDING_*` (incluir `BASE_URL` y `BATCH_SIZE`); default de `MODEL` |
| `openspec/changes/add-source-text-and-embedding-client/` | proposal, **design.md** (el plan §7 lo exige), specs, tasks |
| `Documentos/epicas.md` (EP12) | Enlazar HU-AIENG-011 |
| Routers `/v1/index/*`, `openapi.json`, `jbg_ai.api.main`, migraciones, `backend/` API, `frontend/` | **Sin cambios** |

---

## Especificaciones Técnicas

### Forma: biblioteca, no servicio

C11 no monta rutas. No hay `STUB_MODE` que conmutar: no hay HTTP. Los tests inyectan el puerto. `create_app` sigue sin importar `indexing`.

```
C13 (fuera)                         C11 (este ticket)
───────────                         ────────────────
feed → fila candidata               build_source_text(record) → doc_text
¿hash == stored? → skip        ←──  hash_source_text(doc_text) → hex64
upsert + tombstone                  embed(texts) → vectors + model + version
```

### DTO de entrada (`ProductSourceText` o equivalente)

Campos, todos del lado Python, **sin** `source`/`confidence`:

| Campo | Obligatorio | Notas |
|---|---|---|
| `sku` | sí | Entra en `doc_text` (rama léxica / `tsv`) |
| `name` | sí | Prosa; viene de `Product.Name`, no de `ProposedProfile.title` |
| `description` | no | Omitir línea si vacío |
| `collection_name` | no | |
| `piece_type` | no | Vocabulario C09, ya canónico |
| `materials` | sí (lista, puede `[]`) | Ordenar; omitir línea si vacía |
| `stone_type` | no | |
| `size_label` | no | |
| `family_name` | no | **Nombre**, no UUID |
| `variant_label` | no | |
| `color_tags` / `style_tags` / `occasion_tags` | sí (listas, pueden `[]`) | Ordenar; omitir línea si vacía |

**Fuera del DTO:** `product_id`, `family_id`, `price`, `price_band`, `data_origin`, `text_provenance`, `ReviewStatus`.

### Plantilla `source-text/v1`

Orden y etiquetas en español (HU escenario 1–5). `\n`, UTF-8, sin `\r`. Constante `SOURCE_TEXT_VERSION = "source-text/v1"` en código (no fichero en `prompts/`). Cambiar etiquetas u orden = v2 y reembed de corpus.

`source_hash = sha256(doc_text.encode("utf-8")).hexdigest()` — minúsculas, 64 chars.

### Cliente de embeddings

```text
protocol EmbeddingClient
  model_id: str
  document_version_key: str   # "{model}:1536:source-text/v1" — se persiste en C13
  model_version_key: str      # "{model}:1536" — C14 compara modelo+dimensión; no persiste la query

  async embed(texts: list[str]) -> EmbedResult
```

`EmbedResult`: `vectors: list[list[float]]`, `embedding_model`, `embedding_version`, `cache_hits: int`.

- Adapter: `litellm.aembedding` (o equivalente estable en `1.98.0`).
- Default model: `openai/text-embedding-3-small`.
- Tras cada respuesta: `len(v) == 1536` o excepción.
- Batch: trocear `texts` en bloques de `JPV_EMBEDDING_BATCH_SIZE` (default **64**).
- Retry: backoff en 429 y 5xx; no reintentar 4xx de validación.
- Caché proceso: dict `(digest, model, version) → vector`. Sin TTL. Sin Redis. Sin tabla.
- **No** L2 extra: 3-small ya normaliza; C05 eligió coseno para no depender de esa precondición.
- Fallo sin API key al llamar: error explícito (503-equivalente de librería / excepción de dominio), no silencio.

`embed()` es **`async`** (como C09 `acompletion` y el futuro C13). El mismo método embebe la consulta de C14: la clave de caché es el texto exacto; no hay plantilla que renderizar. En `product_document.embedding_version` se persiste `document_version_key` (`{model}:1536:source-text/v1`) porque es el preproceso **del documento**. C14 no persiste la query: basta `model_version_key` (`{model}:1536`) para no mezclar modelos.

### Settings

| Variable | Boot `/health` | Al llamar `embed` |
|---|---|---|
| `JPV_EMBEDDING_API_KEY` | opcional; blank → unset | **obligatoria**; **no** fallback a `JPV_RAG_LLM_API_KEY` |
| `JPV_EMBEDDING_MODEL` | opcional | default código `openai/text-embedding-3-small` |
| `JPV_EMBEDDING_BASE_URL` | opcional | proxy / Azure |
| `JPV_EMBEDDING_BATCH_SIZE` | opcional | default 64 |

`canonical_openapi_settings` fija las tres (o cuatro) a ausentes / default de batch, como C09.

### Tests (nombres de la ficha + exploración)

Python: `test_<unidad>_<escenario>_<esperado>`.

| Test | Qué caza |
|---|---|
| `test_source_text_is_stable_for_same_profile` | Deriva de serialización |
| `test_material_order_does_not_change_hash` | Lista no canónica |
| `test_hash_changes_when_family_changes` | Deuda C07 / C18 |
| `test_embedding_not_recomputed_when_hash_unchanged` | Caché; fake cuenta llamadas |
| `test_absent_fields_are_omitted_not_sentinel` | `ninguna` contaminaría el espacio |
| `test_price_is_not_in_source_text` | Reembed por PVP |
| `test_family_id_uuid_is_not_in_source_text` | Ruido semántico |
| `test_vector_dimension_mismatch_is_rejected` | Primo del operator class mal alineado |
| `test_settings_do_not_require_embedding_key_to_boot` | `/health` |
| `test_embed_without_key_fails_without_using_rag_llm_key` | Clave separada |
| `test_unit_suite_makes_no_provider_calls` | Igual que C06b/C09 |

Sin marcador `db`. Sin Testcontainers.

---

## Arquitectura

**Frontera §6.2.** Python calcula parecidos. C11 solo produce texto y vectores; no decide stock, precio ni si un perfil está aprobado.

**Frontera §6.3.** Python no lee `public` por SQL. El DTO lo rellenará C13 desde el feed C12. Este ticket no abre el feed.

**Dos hashes.** C08 `ProductEnrichmentSourceHash` (entradas del extractor) ≠ C11 `source_hash` (`doc_text`). Documentado en la entidad .NET; no reutilizar el código C#.

**S11 (guía).** Hash de contenido + versión de proceso. Incremental = documento cambió. Migración de modelo = corpus entero, índice sombra: **no** se implementa. C11 solo escribe las etiquetas para que C13 pueda filtrar.

**S3.** Proveedor = config (LiteLLM). Fallback a otro modelo de **otra dimensión** = mezcla de espacios; prohibido.

**C05 decisión 11.** «El acceso tipado nace en C11/C13». Se lee como permiso, no como obligación de este change: **sin ORM**.

**Visual vs semántico.** `ProductPhotoEmbedding` 1280d JSON en `public`. Espacio distinto. Spec `embedding-management` intacta.

**Breaking changes.** Ninguno de contrato REST ni OpenAPI. C13 pasará de 501 a lógica real; C11 no lo hace.

**Paralelo.** C11 ‖ C12 permitido pero C12 va **después**. C11 ‖ C13 prohibido.

---

## Definición de Hecho (DoD)

- [ ] `jbg_ai.indexing` construye `doc_text` `source-text/v1` y `source_hash` SHA-256 estables
- [ ] Materiales/tags ordenados; familia en el texto por **nombre**; ausentes omitidos; precio fuera
- [ ] Cliente LiteLLM con batch, backoff, caché in-memory y assert 1536
- [ ] `JPV_EMBEDDING_*` no bloquean `/health`; embeber sin clave propia falla; no se usa la clave RAG LLM
- [ ] `jbg_ai.api.main` no importa `indexing`; `/v1/index/*` sigue siendo C13
- [ ] `uv run --system-certs pytest` en verde **sin** sockets a proveedores ni RDS
- [ ] `test_openapi_snapshot_is_stable` verde **sin** regenerar el snapshot
- [ ] Specs del change (capability nueva + delta de `ai-service-runtime` si aplica) y **`openspec validate --all --strict` con `0 failed`**
- [ ] `design.md` presente (plan §7)
- [ ] `Documentos/epicas.md` (EP12) enlaza HU-AIENG-011
- [ ] Sin TODO/FIXME sin tarea de seguimiento
- [ ] UI: **no aplica**
- [ ] Migración EF/Alembic: **no aplica**

**Verificación posterior (no DoD):** AutoBulk de C08/C09 sobre los 1.200 **después de C12**, luego primer sync C13. Sin perfiles aprobados el índice nace vacío y parece un bug del indexador.

---

## Requisitos No Funcionales

- **Seguridad:** `JPV_EMBEDDING_API_KEY` no se loguea. Distinta de generate y de chat. Producción: SSM `/jpv/prod/*` (C17). Tests sin red.
- **Rendimiento y coste:** hash local; caché intra-proceso; batch 64; ~1.200 vectores se pagan en **C13**, una vez por hash. No reembeber por reorder de `materials`.
- **Observabilidad:** log de *cache hit/miss*, modelo, versión, recuento de textos. El `doc_text` no sube de Debug (mismo criterio C03/C08/C09).
- **Integridad:** dimensión 1536 infalsificable en el adapter. No mezclar con 1280d visual. `tsv` español lo sigue generando Postgres a partir de `doc_text` (C13 escribe la columna; C11 solo la construye).

---

## Preguntas Abiertas

Ninguna pendiente. Las de la exploración (biblioteca, campos, caché RAM, clave separada, omitir ausentes, C12 después) y las cuatro del primer borrador de este ticket **están cerradas** (2026-08-25):

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿`embedding_version` de un *query embed* (C14) incluye `source-text/v1`? | **Documentos sí** (`document_version_key = {model}:1536:source-text/v1`). C14 no persiste la query; compara con `model_version_key = {model}:1536` |
| 2 | ¿Default de batch 64 o 128? | **64** |
| 3 | ¿`JPV_EMBEDDING_BATCH_SIZE` en settings o constante? | **Settings opcional**, default 64, como `JPV_RAG_LLM_CONCURRENCY` |
| 4 | ¿`embed()` síncrono o `async`? | **`async`** |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. Desbloquea C13 y C23.
- **Estimación:** **5 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C05 y C09 archivados. C06b no bloquea los tests (fixtures). **Bloquea** C13 y C23. C12 no es prerrequisito de *este* código; sí del primer sync.
- **Línea de corte** (si desborda, regla 5): primero constructor + hash + tests de estabilidad (archivable, desbloquea diseñar C13); después cliente LiteLLM + caché. Sin el cliente, C13 no puede llamar al proveedor, así que la segunda mitad sigue siendo 🔴.
- **Tags:** `HU-AIENG-011`, `C11`, `EP12`, `ai-service`, `python`, `indexing`, `embeddings`, `litellm`, `pgvector`, `idempotency`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-011](../../../../Documentos/Historias/AI-Eng/HU-AIENG-011.md)
- **Change OpenSpec:** `openspec/changes/add-source-text-and-embedding-client/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C11) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.3, §7.1, §7.2, D3) · specs v2 §4.7
- **Apuntes del Máster (guía):** [S11 Reindexación](../../../../Documentos/Sesiones%20Master%20AIEng/S11_RAG_avanzado/Reindexacion%20y%20Versionado%20Embeddings.md) · [S3 LiteLLM](../../../../Documentos/Sesiones%20Master%20AIEng/S3_Patrones_Diseños_Wrappers_Modelos/Abstracci%C3%B3n%20de%20proveedores%20y%20estrategias%20de%20fallback.md) · [S7 Embeddings](../../../../Documentos/Sesiones%20Master%20AIEng/S7_Embeddings/Embeddings.md)
- **Specs vivas:** `ai-vector-schema` · `ai-service-runtime` · `catalog-enrichment-pipeline` · `product-ai-profile` · **no** `embedding-management` (visual)
- **Precedentes:** `ProductEnrichmentSourceHash.cs` · migración `f46c55c056e2` (`EMBEDDING_DIM = 1536`) · `jbg_ai/enrichment/llm.py` (puerto, no reutilizar) · `tests/README.md` (`indexing/` reservada)
- **Contrato:** `ai-service/openapi.json` — **no se modifica**
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-25 | `/enrich-us` | Creación a partir de HU-AIENG-011 y de la exploración previa al proposal. Recoge: biblioteca pura, plantilla `source-text/v1`, hash del `doc_text`, LiteLLM 1536d, caché RAM, `JPV_EMBEDDING_*` sin fallback a chat, C12 después, 0 perfiles en Docker |
| 2026-08-25 | exploración | Preguntas 1–4 del ticket cerradas con el default: `document_version_key` vs `model_version_key`, batch 64, `JPV_EMBEDDING_BATCH_SIZE` en settings, `embed()` async |
