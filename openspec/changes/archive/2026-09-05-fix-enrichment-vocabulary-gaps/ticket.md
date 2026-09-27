# T-AIENG-FIX1: Close the enrichment vocabulary gaps — four piece types, `enrichment/v2` and a 22-product cohort (FIX1)

> Ticket técnico del change OpenSpec `fix-enrichment-vocabulary-gaps`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, specs vivas de `openspec/specs/`, [HU-AIENG-FIX1](../../../../Documentos/Historias/AI-Eng/HU-AIENG-FIX1.md) y las mediciones de [fix1-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/fix1-exploration-measurements.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-FIX1 / FIX1** — Ampliar `piece_type` con `diadema`, `gemelos`, `cinturon` y `llavero`; saltar a `enrichment/v2` derivando la ruta del prompt de su versión; reenriquecer una cohorte enumerada de 22 productos con dos de ellos como grupo de control; y emitir los deltas de las dos specs vivas que el salto deja falsas

---

## Contexto y Problema

`piece_type` es un vocabulario **cerrado** de ocho hiperónimos fijado por C09. El catálogo contiene piezas que esos ocho términos no saben nombrar, y el extractor hace lo que se le pidió: deja nulo o elige el hiperónimo más plausible. C18a vio la mitad del problema —once productos sin tipo— y lo anotó como change propio.

**La exploración del 2026-09-05 midió la otra mitad.** De los 22 productos cuyo nombre lleva uno de los cuatro términos, **11 están sin tipo y 9 están mal tipados**. Y el mal tipado es peor que el nulo, porque el filtro de categoría del panel es **duro** (`AND d.piece_type = :category`): una diadema etiquetada `broche` aparece cuando el operador filtra por broche.

| Categoría | documentos | impostores | qué son |
|---|---:|---:|---|
| `broche` | 85 | **6** (7,1 %) | 3 diademas, 2 gemelos, 1 llavero |
| `collar` | 140 | **2** | 2 diademas |
| `colgante` | 161 | **1** | 1 diadema |

Reenriquecer sólo los once nulos —lo que la ficha pide— entregaría un facet «Diadema» que devuelve **5 de 11**. No dice cero: dice cinco. Sin error, sin traza y con resultados en pantalla.

Y el criterio de extremo a extremo de la ficha —*«buscar "diadema" pasa de cero a resultados»*— **ya se cumple hoy**: la rama léxica de C21 alcanza los 11 documentos porque el nombre está en `doc_text`. Un verificador que lo ejecute firmaría verde por el motivo equivocado.

**Estado actual del código (verificado en el repositorio y contra la base de datos viva):**

| Pieza | Estado |
|---|---|
| `enrichment/vocabularies.yaml` → `piece_type.terms` | **8 términos** (C09). Sin `diadema`, `gemelos`, `cinturon` ni `llavero` |
| `prompts/enrichment/v1.md` | Existe · **duplica la lista como texto plano**, sección «Vocabularios» |
| `enrichment/constants.py` → `PROMPT_VERSION` | `"enrichment/v1"` |
| `enrichment/pipeline.py` → `_PROMPT_RELATIVE` | `Path("prompts") / "enrichment" / "v1.md"` — **hardcodeado, desacoplado de la constante** |
| `frontend/src/lib/materials-vocabulary.ts` → `PIECE_TYPE_OPTIONS` | **8 opciones**, espejo manual del YAML; consumido por `pages/sales/assisted.tsx:335` |
| `retrieval/query_synonyms.yaml` → `exclusions` | Declara `llavero`, `diadema`, `gemelos` y `cinturon` como *«pertenece a `fix-enrichment-vocabulary-gaps`»* |
| `retrieval/synonyms.py` → `_base_layer()` | **Deriva** las clases de equivalencia del YAML de enriquecimiento: añadir un término crea su clase de consulta sola |
| `tests/retrieval/test_synonyms.py:103` `test_base_vocabulary_terms_are_pinned` | Fija los 8 términos · **saltará** |
| `tests/retrieval/test_synonyms.py:265` `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in` | Exige los 4 términos en `exclusions` · **saltará** |
| `tests/retrieval/test_synonyms.py:70` `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` | **Usa `diadema` como canónico desconocido** · saltará con `DID NOT RAISE` |
| `frontend/src/lib/materials-vocabulary.test.ts` | Fija los 8 tipos y los 9 materiales · **saltará** |
| `openspec/specs/catalog-enrichment-pipeline/spec.md` | Enumera los 8 términos en un **MUST** y fija `prompt_version = enrichment/v1` en un escenario |
| `openspec/specs/query-expansion/spec.md` | Escenario *«Vocabulary gaps are not smuggled in as synonyms»* → *«recorded as belonging to the vocabulary-gap change»* |
| `ProductAiProfiles` | **1.200 filas**, todas `PromptVersion = enrichment/v1`; 1.168 `Approved`, 32 `Rejected` |
| `ai.product_document` | 1.168 filas · `piece_type IS NULL` en **11** · `tsv` es columna generada de `doc_text` |
| `AiEnrichRequest` / `ProductAiProfileService` | `Force` existe (`if (!request.Force && stored.SourceHash == hash)`); `MaxBatchSize = 50`; `AutoBulk` → `Approved` |
| `indexing/source_text.py` | Renderiza la línea `Tipo:` en `doc_text` → cambiar `piece_type` cambia `source_hash` → el indexador incremental reembebe esa fila |
| Artefactos OpenSpec de este change | **A generar** (0/4, schema `spec-driven`) |

**Impacto en producto:** el desplegable «Tipo de pieza» pasa de describir un catálogo de ocho categorías a describir el que existe, y deja de devolver diademas cuando se pide broches.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/enrichment/` | **Alto** — `vocabularies.yaml` (4 términos), `constants.py` (`PROMPT_VERSION`), `pipeline.py` (`load_prompt` derivada) |
| `ai-service/prompts/enrichment/` | **Alto** — `v2.md` **nuevo**; `v1.md` **intacto** |
| `ai-service/src/jbg_ai/retrieval/` | **Medio** — `query_synonyms.yaml`: cierre de las 4 exclusiones, motivo de `filigrana`, forma de superficie `gemelo` |
| `ai-service/tests/` | **Medio** — 3 tests fijados en `retrieval/test_synonyms.py` + tests nuevos en `enrichment/` |
| `frontend/src/lib/` | **Medio** — `materials-vocabulary.ts` (+4 opciones) y su test fijado |
| `openspec/changes/<change>/specs/` | **Alto** — 2 requisitos `MODIFIED` + 1 `ADDED` en `catalog-enrichment-pipeline`; 1 `MODIFIED` en `query-expansion` |
| `Documentos/` | **Medio** — `epicas.md` (EP12), informe `fix1-vocabulary-gaps-measurements.md`, limitación del README de `ai-service` |
| `backend/` | **Ninguno de código** — sólo se **ejecuta** `POST /api/ai/catalog/enrich-batch` con `force: true` |
| `ai-service/openapi.json` · `terraform/` · `.github/workflows/` | **Ninguno** |

---

## Especificaciones Técnicas

### Servicio Python (`ai-service`)

**Vocabulario**

- `piece_type.terms` += `diadema`, `gemelos`, `cinturon`, `llavero`, en ese orden, **al final de la lista** para que el diff sea legible y el test fijado se lea como una ampliación.
- Formas canónicas acordadas: **`gemelos`** en plural (como `pendientes`) y **`cinturon`** sin tilde (precedente de `pequeno`).
- **Ningún sinónimo de extracción nuevo** en el YAML de enriquecimiento: las variantes de consulta viven en el overlay, que es la capa de C20.

**Prompt**

- Fichero nuevo `prompts/enrichment/v2.md`, encabezado `# enrichment/v2`, con la sección «Vocabularios» ampliada a doce términos.
- Línea nueva en el encargo, en el sentido de: *el catálogo puede contener servicios, consumibles y artículos de regalo que no son piezas de joyería; para ellos `piece_type` es `null`*. La salida `null` **ya existía** en el prompt de C09 — lo que faltaba era el encargo, no la opción.
- `PROMPT_VERSION = "enrichment/v2"` y `_PROMPT_RELATIVE = Path("prompts") / f"{PROMPT_VERSION}.md"`, de modo que constante y ruta no puedan divergir.
- `v1.md` **no se modifica ni se elimina**.

**Overlay de consulta (`query_synonyms.yaml`)**

- Retirar de `exclusions` los cuatro términos, que dejan de ser lagunas: la sección documenta lo que **no** debe entrar, y mantener ahí cuatro canónicos del base la volvería autocontradictoria.
- Actualizar el motivo de `filigrana` para que no siga remitiendo a este change.
- Añadir clase `piece_type / gemelos` con forma de superficie `gemelo`: la reducción de plurales de `singular_candidates` va singular←plural, así que el singular no alcanza al canónico plural. Cada entrada nueva lleva su medición, como exige la spec viva.
- **No se añade `tiara`**: alcanza 0 documentos y la regla del overlay es que una entrada sin número detrás no entra.

**Tests**

| Test | Acción |
|---|---|
| `test_base_vocabulary_terms_are_pinned` | Ampliar la tupla a 12 términos |
| `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in` | Reducir el conjunto exigido a las exclusiones que siguen vivas (`piel`, `filigrana`) |
| `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` | **Sustituir `diadema`** por un canónico que siga siendo desconocido. **No eliminar el test** |
| `test_new_piece_types_are_canonical_and_normalised` | Nuevo — resolución y normalización de los cuatro términos y de `gemelo` |
| `test_prompt_version_matches_the_loaded_prompt_file` | Nuevo — el encabezado del fichero cargado por `load_prompt()` es `# ` + `PROMPT_VERSION` |
| `test_untypeable_jewel_stays_null` | Nuevo — un producto sin evidencia de tipo conserva `piece_type` nulo |
| `test_proper_name_containing_a_piece_type_does_not_beat_the_head_noun` | Nuevo — regresión de falso amigo, en el idioma de la exclusión `piel` |

> **Sobre `test_service_and_consumable_rows_get_null_piece_type`:** con un `EnrichLlm` falso prueba el pipeline, no el enunciado del prompt. Debe nombrarse por lo que comprueba. **La evaluación del prompt es la corrida de reenriquecimiento**, y su evidencia es el informe.

### Frontend

- `PIECE_TYPE_OPTIONS` += `{ value: 'diadema', label: 'Diadema' }`, `{ value: 'gemelos', label: 'Gemelos' }`, `{ value: 'cinturon', label: 'Cinturón' }`, `{ value: 'llavero', label: 'Llavero' }`.
- El `value` viaja al recuperador y se compara por **igualdad exacta**: debe ser byte a byte el canónico del YAML. La tilde vive sólo en el `label`.
- `materials-vocabulary.test.ts`: ampliar el array fijado y su descripción («los ocho tipos canónicos» → doce).
- **Ningún componente nuevo**: `pages/sales/assisted.tsx` itera sobre la constante y se rellena solo. Sin cambios en el `<Select>` de Metronic ni en `AiSearchFilters.Category`, que es `string?` sin enum.

### Deltas de specs

```
specs/catalog-enrichment-pipeline/spec.md
  ## MODIFIED Requirements
    ### Requirement: Real enrichment replaces the stub when stub mode is off
        (el escenario «Real mode produces extracted profiles» fija enrichment/v1 → v2)
    ### Requirement: Closed vocabularies reject unknown values and invent nothing
        (la lista canónica de piece_type pasa de 8 a 12 términos)
  ## ADDED Requirements
    ### Requirement: Non-jewellery rows get a null piece type

specs/query-expansion/spec.md
  ## MODIFIED Requirements
    ### Requirement: Dictionary entries and exclusions are justified against the corpus
```

`MODIFIED` obliga a reescribir el requisito **completo con todos sus escenarios**; el de vocabularios cerrados tiene cuatro. Es la parte más voluminosa del change y no lleva una línea de algoritmo.

### Operación de datos (no es código)

- Cohorte **enumerada** de 22 SKU en `design.md`, no derivada por consulta en tiempo de ejecución.
- `POST /api/ai/catalog/enrich-batch` con los 22 `productId`, `force: true`, `reviewMode: "AutoBulk"` — **un solo lote**, por debajo de `MaxBatchSize = 50`.
- Requiere `STUB_MODE=false` y `JPV_RAG_LLM_API_KEY`, con el contenedor recreado según el runbook de C12. Con el stub, el informe describiría una ficción.
- Después, **una sola** sincronización incremental del índice.
- **Comprobación previa:** que ningún perfil de la cohorte tenga `ReviewedByUserId` o `ReviewedAt` no nulos — `Upsert` los limpia y lo registra como `enrich_profile_review_reset`.

### Fuera de este ticket

Reenriquecer los 1.200 · `filigrana` · campo nuevo de clasificación de producto · `source-text/v1`, `embedding_version` e `indexing/embeddings.py` · migraciones · reejecutar la sugerencia de familias · regenerar `openapi.json` · el endpoint de facets agregados desde el surtido · cualquier cambio en `backend/src/`.

---

## Arquitectura

- **La fuente de verdad del vocabulario es `vocabularies.yaml`**, y las otras cuatro apariciones son réplicas: prompt (texto plano), espejo del frontend (código), y dos specs vivas (prosa normativa). El diccionario de consulta de C20 **no** es una réplica: lo deriva en `_base_layer()`, así que las cuatro clases de equivalencia nuevas aparecen solas.
- **La frontera de lenguaje no se mueve:** Python sigue haciendo sólo vectorial y LLM, .NET conserva la lógica de negocio. El único tráfico hacia .NET es la ejecución del endpoint de enriquecimiento que ya existe.
- **Versionado de prompt frente a versionado de embedding.** Mezclar `embedding_version` es comparar dos espacios geométricos y la base devolvería un número plausible sin significado —la corrupción silenciosa de S11—; este change **no lo toca**. Mezclar `PromptVersion` es tener dos poblaciones de atributos comparables como dato, y **el campo se creó para hacer visible esa diferencia**. Consecuencia única: las métricas agregadas se reportan **por versión de prompt**, la misma disciplina que C24 aplica a `data_origin`.
- **Se conserva la duplicación de la lista en el prompt**, con la alternativa nombrada y rechazada: renderizar el bloque desde el YAML haría que `prompt_version` dejase de identificar un texto fijo, que es exactamente lo que da valor al campo. Generarlo en build y commitearlo es mejor y desproporcionado para cuatro términos: queda anotado, no ejecutado.
- **Breaking changes:** ninguno. No hay ruta, campo ni esquema nuevo, `openapi.json` no se mueve y `AiSearchFilters.Category` ya es `string?` sin enumeración. El único contrato que cambia es **normativo** (las dos specs vivas), y para eso existe el change.

---

## Criterios de Aceptación

Los diez escenarios están en [HU-AIENG-FIX1](../../../../Documentos/Historias/AI-Eng/HU-AIENG-FIX1.md#criterios-de-aceptación). Los números que los verifican, medidos antes y después:

| Comprobación | Antes | Después |
|---|---:|---:|
| `piece_type = 'diadema'` en `ai.product_document` | 0 | **11** |
| `piece_type = 'gemelos'` / `'llavero'` / `'cinturon'` | 0 / 0 / 0 | **4 / 3 / 1** |
| `piece_type IS NULL` | 11 | **1** (SKU845) |
| Impostores en el facet `broche` | 6 de 85 | **0 de 79** |
| Impostores en `collar` / `colgante` | 2 / 1 | **0 / 0** |
| SKU822 `broche` y SKU882 `anillo` (control) | correctos | **sin cambio** |
| Opciones del desplegable «Tipo de pieza» | 8 | **12** |
| Perfiles en `enrichment/v2` | 0 | **22** |
| Filas reembebidas por la sincronización | — | = perfiles cuyo `doc_text` cambió |

---

## Definición de Hecho (DoD)

- [ ] Los cuatro términos están en `vocabularies.yaml` con la forma canónica acordada
- [ ] `prompts/enrichment/v2.md` existe con la lista ampliada y la línea sobre servicios, consumibles y regalo; **`v1.md` sin diff**
- [ ] `PROMPT_VERSION` es `enrichment/v2` y `load_prompt()` deriva la ruta de la constante
- [ ] Los cuatro tests fijados actualizados —incluido el cambio de ejemplo, **sin eliminar el test**— y los cuatro tests nuevos en verde
- [ ] `uv run pytest` en `ai-service` en verde **sin llamadas reales a LLM, embeddings ni RDS**
- [ ] Frontend: `PIECE_TYPE_OPTIONS` con 12 opciones y su test fijado en verde; `npm run build` sin errores (recordatorio: `tsc --noEmit` arrastra errores previos de las plantillas Metronic y **no es la puerta**)
- [ ] Comparación de la suite frente a la línea base **por nombres de test**, no por recuento, en backend y frontend
- [ ] Deltas emitidos para `catalog-enrichment-pipeline` (2 `MODIFIED` + 1 `ADDED`) y `query-expansion` (1 `MODIFIED`)
- [ ] `openspec validate --all --strict` reporta `0 failed`
- [ ] `ai-service/openapi.json` **sin diff** y `test_openapi_snapshot_is_stable` en verde
- [ ] Ninguna migración creada, ni de Alembic ni de EF Core
- [ ] Corrida ejecutada con `STUB_MODE=false`: 22 perfiles en `enrichment/v2`, y una sola sincronización incremental
- [ ] Informe `fix1-vocabulary-gaps-measurements.md` con el **diff completo** de las 22 filas, no sólo `piece_type`, y el veredicto de los dos de control
- [ ] Verificación por la interfaz: filtrar por «Diadema» y por «Broche» comprobando **recuentos**, no sólo que devuelve algo
- [ ] `Documentos/epicas.md` (EP12) actualizado y limitación declarada en el README de `ai-service`
- [ ] UI en español (es-ES); sin TODO/FIXME sin tarea asociada

---

## Requisitos No Funcionales

- **Seguridad:** sin superficie nueva. La corrida usa el endpoint de catálogo existente con sesión de administrador; `JPV_RAG_LLM_API_KEY` se inyecta por entorno y **nunca** se imprime ni se commitea.
- **Rendimiento y coste:** **22 llamadas al modelo** en un lote, con la concurrencia acotada por `JPV_RAG_LLM_CONCURRENCY` que ya existe. La sincronización posterior reembebe sólo las filas cuyo `source_hash` cambió. Ningún cambio en el plan de consulta: `piece_type` ya es columna del índice y el filtro ya existe.
- **Observabilidad:** los contadores del lote (`enrich_batch_completed`) y de la sincronización son la evidencia del informe. Cualquier `enrich_profile_review_reset` en la corrida debe investigarse antes de continuar.
- **Integridad de datos:** el corpus se mueve **por un solo camino** —perfil → `doc_text` → `source_hash` → embedding— y sólo para la cohorte. `embedding_version` y `source-text/v1` intactos, así que no se mezclan espacios geométricos. `v1.md` conservado para que la procedencia de los 1.178 perfiles no reenriquecidos siga siendo verificable.
- **Reproducibilidad:** la cohorte es una lista enumerada de SKU en `design.md`, no una consulta cuyo resultado dependa del estado de la base en el momento de ejecutarla.

---

## Preguntas Abiertas → Decisiones

Las nueve decisiones de diseño se cerraron en la sesión de exploración del 2026-09-05 y están en la tabla de [HU-AIENG-FIX1](../../../../Documentos/Historias/AI-Eng/HU-AIENG-FIX1.md#decisiones-de-diseño-ya-acordadas). Quedan abiertas tres, con opción por defecto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿Qué término sustituye a `diadema` como ejemplo de canónico desconocido en `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap`? | **`filigrana`**, que es la laguna que sigue viva y documentada como tal en el overlay: el test pasa a apuntar a un gap real en vez de a uno cerrado |
| 2 | ¿Qué se hace con los cuatro términos retirados de `exclusions`? | **Se eliminan del fichero.** El motivo por el que estaban —«pertenece a FIX1»— deja de ser cierto, y el historial vive en git y en el informe, no en una sección cuyo propósito es advertir de lo que no debe entrar |
| 3 | ¿Se ejecuta la corrida dentro del change o como operación posterior, al estilo del AutoBulk de C12? | **Dentro del change.** A diferencia del AutoBulk de 1.200, son 22 llamadas en un lote, y sin ejecutarla no hay informe, ni verificación de los dos de control, ni forma de saber si el prompt se sobreajustó |

---

## Prioridad / Estimación / Tags

- **Prioridad:** Media-alta — **no está en la cadena crítica** ni abre ninguna arista del grafo (es una hoja), pero arrastra un **plazo duro**: antes de que C24 etiquete su línea base, porque `source-text/v1` no delataría el cambio y el golden set describiría un corpus que ya no existe. **Recortable** según el §6 del plan: si cae, C24 etiqueta un corpus con once piezas sin tipo y se declara como limitación.
- **Estimación:** _Pendiente_ (complejidad **2** según la HU)
- **Tags:** `ai-service` · `frontend` · `enrichment` · `retrieval` · `openspec` · `no-migration` · `no-contract-change` · `data-migration` · `FIX1`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-FIX1](../../../../Documentos/Historias/AI-Eng/HU-AIENG-FIX1.md)
- **Change:** [`openspec/changes/fix-enrichment-vocabulary-gaps/`](./)
- **Mediciones:** [fix1-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/fix1-exploration-measurements.md)
- **Origen del hallazgo:** [c18a-family-suggestion-report.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c18a-family-suggestion-report.md), hallazgos (b) y (c)
- **Plan de changes:** [ficha FIX1](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) del §3 y su propuesta en el §0
- **Diseño RAG:** [`proyecto-final-diseno-rag-joiabagur.md`](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) — vocabularios cerrados y decisión 6 sobre el espejo del frontend
- **Specs vivas:** `openspec/specs/catalog-enrichment-pipeline/`, `openspec/specs/query-expansion/`
- **Runbook de la corrida:** [c12-catalog-autobulk-runbook.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c12-catalog-autobulk-runbook.md)
- **Procedimientos:** [User Stories](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Tickets de Trabajo](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-05 | Sergio Valdueza | Creación del ticket a partir de la sesión de exploración de FIX1 y de sus mediciones. Nueve decisiones cerradas. **Dos correcciones a la ficha del plan**: la población es de 22 productos y no de 11 —nueve están mal tipados, no sin tipar—, y su criterio de extremo a extremo ya se cumple hoy por la rama léxica de C21, así que los criterios se reescriben como estructurales. Se incorporan además tres hallazgos que la ficha no recoge: la segunda spec viva afectada, dos alambres adicionales que saltan, y el desacople entre `PROMPT_VERSION` y la ruta del prompt |
