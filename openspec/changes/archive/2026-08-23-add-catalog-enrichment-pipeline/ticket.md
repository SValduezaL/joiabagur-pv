# T-AIENG-009: Catalog enrichment pipeline — closed-vocab extraction with per-field provenance (C09)

> Ticket técnico del change OpenSpec `add-catalog-enrichment-pipeline`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-009](../../../../Documentos/Historias/AI-Eng/HU-AIENG-009.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C09, §0 16–23 ago), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§7.1, §7.3, §7.8, §8.5), sesiones de exploración 2026-08-23 (incluye LiteLLM / `stone_type` / concurrencia), código real de `ai-service/src/` y `backend/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-009 / C09** — Extractor real de `POST /v1/enrich/products`: vocabularios cerrados, talla por regex (`Name` > `Description`), LiteLLM a temperatura 0, confianza por span, puertas de lote fuera del HTTP

---

## Contexto y Problema

C08 dejó listo el lado .NET: `ProductAiProfile`, enrutado híbrido, `POST /api/ai/catalog/enrich-batch` y un contrato que **ya exige** `source` (`rule` | `inferred`) y `prompt_version`. C06a y C06b dejaron 1.200 productos con texto en `public."Products"`. Lo que falta es el productor: `POST /v1/enrich/products` sigue siendo el stub de C02/C08.

Eso no es un detalle. El stub marca la talla `rule` en uno de cada cuatro productos **por índice del lote** y dice que la lee del SKU. En este catálogo la talla está en el **nombre** (`mini`, `S`/`M`/`L`/`XL`). Si C09 devolviera todo `inferred`, C08 en `Routed` mandaría el catálogo a una cola que nadie vacía; en `AutoBulk` indexaría igual, pero la huella por campo mentiría. Si inventara materiales para aprobar una puerta de cobertura, violaría §7.1.

El HTTP **no recibe** `text_provenance` ni `text_quality_tier` (viven en JSONL; C13 los materializa). Por eso las puertas de §8.5 (cobertura ≥ 70 % global y ≥ 90 % sobre `ai_assisted`) no pueden ser un 422 del POST de 50. Van a un auditor sobre fixtures.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-catalog-enrichment-pipeline` | Artefactos listos; pipeline implementado (`STUB_MODE=true` conserva el stub) |
| `ai-service/src/jbg_ai/enrichment/` | Vocabularios YAML, regex, puerto LiteLLM, pipeline, auditor |
| `ai-service/prompts/enrichment/` | `v1.md` (`prompt_version = enrichment/v1`) |
| `POST /v1/enrich/products` | Stub si `STUB_MODE=true`; pipeline si `false`. Sin clave RAG → 503 explícito, no 501 |
| Contrato `ProposedProfile` | C08: `source` + `piece_type` / `stone_type` / `size_label` + tags desglosadas + `prompt_version`. `title`/`description`/`family_id`/`variant_label` opcionales |
| Stub | `enrich_products_stub`: ciclos deterministas; talla `rule` si `index % 4 == 0`; `prompt_version = "stub"`; rellena title/description/familia |
| Tests de contrato | `test_enrich_profile_carries_source_per_field`, `test_enrich_stub_exercises_both_provenances`, `test_enrich_reports_prompt_version` — corren contra el stub |
| `tests/enrichment/` | Suite con `FakeEnrichLlm`; cero sockets a proveedores |
| `Settings` | `JPV_RAG_LLM_API_KEY` / `MODEL` / `BASE_URL` / `CONCURRENCY` (default 8) opcionales al boot |
| `jbg_ai.data.llm.OpenAICatalogLlm` | CLI de generate, temp 0,8, `JPV_CATALOG_LLM_*`. **No** se importa desde el router. C06b **no** se migra a LiteLLM |
| `pyproject.toml` | `litellm==1.98.0` y `pyyaml==6.0.3` fijadas. Sin Instructor |
| `ai-service/openapi.json` | Congelado. **Este change no lo regenera** |
| C08 `ProductAiProfileService` | Envía `product_id`, `sku`, `name`, `description`. **No** envía precio, colección ni procedencia. Ignora familia. No aplica title/description a `Product` |
| `ProfileReviewPolicy` | Sensibles (`piece_type`, `materials`, `stone_type`, `size_label`) inferidos → revisión; `rule` → no; tags ≥ 0,80 → auto |
| JSONL C06a / C06b | 436 + 764 commiteados; procedencia y tier **solo** ahí |
| HU-AIENG-009 | **Creada** y alineada con este ticket |

**Impacto en producto:** ninguno visible hasta que un administrador ejecute `enrich-batch` (fuera de este ticket). El valor es habilitador: C11 deja de indexar el ciclo del stub.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/enrichment/` | **Nuevo** — vocabularios YAML, regex de talla, puerto `EnrichLlm` (LiteLLM), pipeline, auditor |
| `ai-service/prompts/enrichment/v1.md` | **Nuevo** — prompt de extracción, versionado |
| `ai-service/src/jbg_ai/api/routers/enrich.py` | Sustituir `require_stub_mode` + stub por el pipeline cuando `stub_mode` es falso |
| `ai-service/src/jbg_ai/config/settings.py` | Añadir `JPV_RAG_LLM_API_KEY` / `MODEL` / `BASE_URL` / `CONCURRENCY` (default 8), opcionales al boot |
| `ai-service/pyproject.toml` | Dependencia `litellm` con versión fijada |
| `ai-service/tests/enrichment/` | **Nuevo** — tests con LLM falso (nombres de la ficha + los de la exploración) |
| `backend/.env.example` | Descomentar / documentar `JPV_RAG_LLM_*` como runtime de C09 (ya esbozado) |
| `openspec/changes/add-catalog-enrichment-pipeline/` | proposal, design, specs, tasks (posteriores) |
| `Documentos/epicas.md` (EP12) | Enlazar HU-AIENG-009 |
| `backend/` API, `frontend/`, `ai-service/openapi.json`, migraciones EF/Alembic | **Sin cambios** |

---

## Especificaciones Técnicas

### Superficie HTTP (ya congelada — no se renegocia)

`POST /v1/enrich/products` · Bearer de catálogo (sin `pos_id`) · lote 1..50.

Entrada por producto: `product_id`, `sku`, `name?`, `description?`, `raw_attributes` (hoy vacío).

Salida por producto (`ProposedProfile`):

| Campo | C09 produce |
|---|---|
| `piece_type` | Hiperónimo o `null` · `inferred` |
| `materials` | Lista canónica o `[]` · `inferred` |
| `stone_type` | Tipo concreto, `piedra`, o `null` · `inferred` |
| `size_label` | Canónico o `null` · `rule` si regex, si no `inferred` o ausente |
| `color_tags` / `style_tags` / `occasion_tags` | Listas · `inferred` |
| `title`, `description`, `family_id`, `variant_label` | **`null`** |
| `warnings` | Diagnóstico por producto (p. ej. valor fuera de vocabulario descartado) |
| `prompt_version` | `enrichment/v1` (etiqueta alineada al fichero) |
| `usage.model` | id del proveedor; deja de ser `null` fuera del stub |

### Pipeline

```
name + description
  → regex talla (Name, luego Description)     → size_label source=rule
  → LiteLLM temp 0, schema Pydantic, 1 producto
  → normalizar sinónimos + rechazar fuera de vocabulario
  → stone_type: tipo ∈ YAML | piedra | null
  → piece_type: solo padres
  → confianza por span en el texto de entrada
  → ProposedProfile (title/description/family nulos)
```

Una llamada LLM por producto. Semáforo `JPV_RAG_LLM_CONCURRENCY` (default **8**): tope de llamadas **en vuelo** dentro de un POST de 50. Secuencial (~75 s) rompe el presupuesto de C08; 50 a la vez rate-limita; 1 JSON de 50 ya está descartado. Retry **solo** si el parse falla (equivalente a Instructor, **sin** la librería). Sin reintento HTTP .NET↔Python (eso es C08).

### Vocabularios (cerrados, fichero en repo, `text` nunca `ENUM`)

**`piece_type`:** `anillo` · `pendientes` · `collar` · `pulsera` · `colgante` · `tobillera` · `broche` · `cadena`

Sinónimos de extracción (no se persisten): sortija/alianza → `anillo`; gargantilla → `collar`; brazalete/esclava → `pulsera`; criollas/aro → `pendientes`. `colgante` no se colapsa a `collar`.

**`materials`:** `plata` · `oro` · `baño de oro` · `hilo` · `latón` · `acero` · `resina` · `cuero` · `perla`

Sinónimos: plata de ley / 925 / sterling → `plata`; 18k / 18kl → `oro`; hilo encerado → `hilo`. **No** `piedras preciosas`. Ámbar/ónix no son material.

**`stone_type`:** lista **cerrada para el modelo**, YAML **ampliable para el mantenedor** (sin migración: el campo ya es `text`). Semilla = tipos del corpus + residual **`piedra`**. Sinónimos en el mismo fichero (`ámbar`/`amber` → `ambar`). Criterio de alta: «¿es gema/mineral reconocible?», **no** umbral ≥ N apariciones.

- Tipo concreto ∈ YAML → ese valor. No se escribe también `piedra`.
- El texto afirma gema/engaste y no concreta, o el modelo propone un tipo fuera de lista → `piedra`.
- Sin afirmación de gema («relieve», «brillo») → `null`.
- **No** strings libres: el modelo inventaría diamantes.

Ámbar/ónix van aquí, no a `materials`. `perla`: `stone_type` si es engaste o «collar de perlas»; el metal de la cadena en `materials`. No se duplica.

**`size_label`:** tokens de C06a (`xxs`…`xxl`, `mini`, `extramini`, S/M/L, mm/cm, anillo 5–48). Preferencia `Name` > `Description`.

Tags comerciales: listas cerradas cortas (color / estilo / ocasión). Estilo **no** es taxonomía de subtipo.

### Confianza

| Caso | `confidence` | `source` |
|---|---|---|
| Regex de talla | `1.0` | `rule` |
| Valor con span en name o description | `0.85` | `inferred` |
| Valor sin span | `0.45` | `inferred` |
| Lista mixta (un miembro con span, otro sin él) | `0.45` (el peor) | `inferred` |
| Ausente / `[]` | `0.20` | `inferred` |

C08 auto-aprueba tags ≥ 0,80: el «con span» pasa; el «sin span» va a revisión en `Routed`.

### Puertas de lote (auditor, no el POST)

Función pura sobre una lista de perfiles **más** el estrato (del JSONL o de la fixture):

- Unicidad de SKU (`test_batch_fails_when_sku_is_duplicated`).
- Todo valor ∈ vocabulario.
- `materials` vacío solo si el texto no nombra una sustancia (el test `test_empty_materials_flags_review_not_default_value` cubre el caso).
- Cobertura de tags = al menos una de las tres listas no vacía:
  - `original` / `short`: tres vacías **válidas**; no entran en el denominador que castiga.
  - `sparse`: ≥ 1 lista.
  - estrato `ai_assisted`: umbral 90 % (ficha).
  - global: 70 % **sin** contar `original`/`short` como fallo.

El POST de 50 **nunca** devuelve 422 por estas cifras.

### Settings y frontera

| Variable | Quién | Boot `/health` |
|---|---|---|
| `JPV_CATALOG_LLM_*` | CLI C06b (SDK OpenAI; no se migra) | no exige |
| `JPV_RAG_LLM_API_KEY` | runtime C09 (LiteLLM) | no exige; el enrich real sí |
| `JPV_RAG_LLM_MODEL` | p. ej. `openai/gpt-4o` (prefijo de proveedor) | no exige |
| `JPV_RAG_LLM_BASE_URL` | opcional (proxy / Azure / local) | no exige |
| `JPV_RAG_LLM_CONCURRENCY` | semáforo; default **8** | no exige |

`jbg_ai.api.main` no importa `jbg_ai.data`. El cliente de enrich es un puerto `EnrichLlm` sobre LiteLLM; **no** reutiliza `OpenAICatalogLlm` (otra clave, otra temperatura, otro schema).

`STUB_MODE=true` (tests de contrato, snapshot canónico, compose local hasta haber clave RAG): stub intacto. `false`: pipeline; sin clave → error explícito, no perfiles inventados.

### Tests (LLM falso; nombres de la ficha + exploración)

En `ai-service/tests/enrichment/`:

- `test_extracts_multiple_materials_from_description`
- `test_material_synonym_normalized_to_canonical_term`
- `test_rejects_value_outside_closed_vocabulary`
- `test_empty_materials_flags_review_not_default_value`
- `test_size_regex_marks_field_source_as_rule`
- `test_size_prefers_name_over_description`
- `test_size_is_never_read_from_sku`
- `test_generic_stone_when_gem_mentioned_without_type`
- `test_specific_stone_does_not_also_write_generic`
- `test_stone_outside_closed_list_becomes_residual_or_null`
- `test_piece_type_stores_hypernym_not_hyponym`
- `test_title_description_and_family_are_null`
- `test_confidence_follows_evidence_span`
- `test_mixed_list_uses_least_evidenced_member_confidence` — una sola lista con un miembro con span y otro sin él; el campo toma `0.45`
- `test_batch_fails_when_sku_is_duplicated` — **sobre el auditor**, no sobre el POST
- `test_batch_fails_when_tag_coverage_below_threshold` — **sobre el auditor**, no sobre el POST
- `test_tag_coverage_gate_is_evaluated_per_text_provenance`
- `test_original_or_short_may_have_empty_tags`
- `test_sparse_requires_at_least_one_tag_list`
- `test_unit_suite_makes_no_provider_calls`
- `test_settings_do_not_require_rag_llm_key_to_boot`
- `test_enrich_llm_uses_litellm_not_openai_catalog_client`
- `test_concurrency_setting_caps_in_flight_calls`

Los tests de `tests/api/test_contracts.py` **siguen verdes** contra el stub (`STUB_MODE=true`).

---

## Arquitectura

**Frontera §6.2.** Python extrae y propone. .NET persiste y decide (C08). C09 no abre conexión a `public`.

**Frontera §6.3.** Sin feed nuevo. El único consumidor HTTP sigue siendo `AiGatewayClient.EnrichAsync`.

**Decisiones que se heredan.**

- C02: contrato congelado + snapshot. Este change **no** lo mueve; si `test_openapi_snapshot_is_stable` se pone rojo, el change se ha salido de alcance.
- C06b: dos claves (`CATALOG` vs `RAG`); `/health` sin proveedor. El CLI de generate **sigue** en el SDK OpenAI; C09 no lo migra.
- C08: `source` es el interruptor del enrutado; title/description no se aplican; familia se ignora; talla no se duplica en .NET.

**Patrones.** Puerto `EnrichLlm` inyectable sobre **LiteLLM** (S3: el proveedor es config; hoy `openai/gpt-4o`). Instructor (S4) no entra: se apila encima de LiteLLM en C30+ si el retry de schema hace falta. Funciones puras para regex, vocabularios y auditor — testeables sin HTTP ni red. Guardrails S4: exception si el schema no parsea tras retry; filter (`[]` + warning) si no hay evidencia; nunca inventar para pasar una puerta. Versión de LiteLLM **fijada** (compromiso PyPI marzo 2026).

**Breaking changes.** Ninguno de contrato. Cambio de comportamiento: con `STUB_MODE=false` la ruta deja de ser 501/stub y llama al modelo.

---

## Definición de Hecho (DoD)

- [x] `POST /v1/enrich/products` con `STUB_MODE=false` produce perfiles reales (no el ciclo del stub)
- [x] Talla `rule` solo por regex sobre `Name`/`Description`; SKU no participa
- [x] Vocabularios cerrados respetados; `materials: []` sin evidencia; `hilo` admitido; `stone_type` solo valores del YAML o residual `piedra`; nunca string libre
- [x] `title` / `description` / `family_id` / `variant_label` nulos en el extractor real
- [x] `prompt_version` ≠ `"stub"`; `usage.model` informado
- [x] Auditor de puertas en tests, con estrato; el POST de 50 no falla por cobertura
- [x] `JPV_RAG_LLM_*` no bloquean `/health`; `CONCURRENCY` default 8; LiteLLM fijada en `pyproject.toml`
- [x] `uv run --system-certs pytest` en verde **sin** sockets a proveedores
- [x] `test_openapi_snapshot_is_stable` verde **sin** regenerar el snapshot
- [x] Tests de contrato existentes verdes con `STUB_MODE=true`
- [x] Specs del change y **`openspec validate --all --strict` con `0 failed`**
- [x] `Documentos/epicas.md` (EP12) enlaza HU-AIENG-009; README de `ai-service` actualiza el marcador C09
- [x] Sin TODO/FIXME sin tarea de seguimiento
- [x] UI: **no aplica**
- [x] Migración EF/Alembic: **no aplica**

**Verificación posterior (no DoD de este ticket):** un `enrich-batch` AutoBulk local sobre el catálogo Docker, documentado cuando se haga.

---

## Requisitos No Funcionales

- **Seguridad:** misma auth de catálogo que C08 (`get_catalog_principal`). `JPV_RAG_LLM_*` no viaja en el JSONL ni en logs a nivel info. En producción, SSM `/jpv/prod/*` (C17); no reutilizar la key de generate.
- **Rendimiento y coste:** lote ≤ 50; 1 llamada de modelo por producto; semáforo `JPV_RAG_LLM_CONCURRENCY` (default 8); temp 0; sin reintento HTTP. El presupuesto de decenas de segundos de la familia `ai-enrich` (C08) es el techo.
- **Observabilidad:** `trace_id` ya viaja. Loguear sku, `prompt_version`, `usage`, campos con `source=rule`. El texto de descripción no sube de Debug (mismo criterio que C03/C08).
- **Integridad:** C09 no escribe `Product` ni `ProductAiProfile`. Un valor fuera de vocabulario no se almacena.

---

## Preguntas Abiertas

Las 1 y 2 de la primera redacción **están cerradas** (2026-08-23): `stone_type` = YAML cerrado para el modelo / ampliable para el mantenedor (no umbral ≥ N); semáforo = `JPV_RAG_LLM_CONCURRENCY` default 8.

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 3 | ¿`perla` es material o `stone_type` cuando es el cuerpo de la pieza? | **`stone_type`** si es engaste o «collar de perlas»; el metal de la cadena sigue en `materials`. No se duplica |
| 4 | ¿El auditor se expone como CLI (`python -m jbg_ai.enrichment audit`)? | **No en C09.** Función + tests bastan. Un CLI se añade si al verificar el lote de 1.200 hace falta un informe |
| 5 | ¿`STUB_MODE=true` en compose local después de C09? | **Sí, hasta que haya clave RAG.** El compose no debe romper `/health` ni los tests de contrato |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Prerrequisito de C11.
- **Estimación:** **8 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C06a y C08 archivados. C06b no bloquea. **Bloquea** C11 (y, en cascada, C13).
- **Línea de corte** (ficha): si desborda, partir en pipeline+prompt / puertas de calidad. El HTTP real + vocabularios es la mitad que desbloquea C11; el auditor es la segunda.
- **Tags:** `HU-AIENG-009`, `C09`, `EP12`, `ai-service`, `python`, `enrichment`, `llm`, `litellm`, `structured-output`, `hitl`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-009](../../../../Documentos/Historias/AI-Eng/HU-AIENG-009.md)
- **Change OpenSpec:** `openspec/changes/add-catalog-enrichment-pipeline/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C09, §0) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§7.1, §7.3, §7.4, §7.8, §8.5)
- **Apuntes del Máster (S3 / S4):** [Abstracción de proveedores](../../../../Documentos/Sesiones%20Master%20AIEng/S3_Patrones_Diseños_Wrappers_Modelos/Abstracci%C3%B3n%20de%20proveedores%20y%20estrategias%20de%20fallback.md) (LiteLLM) · [Extracción de datos estructurados](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/Extraccion%20de%20datos%20estructurados.md) · [Guardrails y validación de outputs](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/Guardrails%20y%20validacion%20de%20outputs.md)
- **Specs vivas:** `ai-service-api-contracts` · `product-ai-profile` · `real-catalog-corpus` · `synthetic-catalog-corpus` · `ai-service-runtime`
- **Precedentes:** `jbg_ai/data/llm.py` (parse, no reutilizar el puerto) · `jbg_ai/api/schemas/enrich.py` · `jbg_ai/stubs/responses.py` · `ProductAiProfileService.cs` · `ProfileReviewPolicy.cs` · `scripts/catalog/.../grouping.py` (tokens de talla)
- **Contrato:** `ai-service/openapi.json` — **no se modifica**
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-23 | `/enrich-us` | Creación a partir de HU-AIENG-009 y de la exploración previa al proposal. Recoge: puertas fuera del HTTP, `piece_type` padres, `hilo` en materials, `stone_type=piedra` residual, confianza por span, title/description nulos, endpoint sin lote AutoBulk en el alcance |
| 2026-08-23 | exploración | LiteLLM como cliente de runtime (no SDK OpenAI directo; Instructor no entra). `stone_type` cerrado para el modelo / YAML ampliable. Semáforo `JPV_RAG_LLM_CONCURRENCY` default 8. Preguntas 1–2 cerradas |
| 2026-08-23 | verify follow-up | Tests dedicados de lista mixta (peor miembro) y de unicidad de SKU en el auditor; escenarios de spec homónimos |
