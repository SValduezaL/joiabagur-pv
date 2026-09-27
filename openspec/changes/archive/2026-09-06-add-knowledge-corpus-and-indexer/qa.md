# QA — C23 `add-knowledge-corpus-and-indexer`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** 2026-09-06 · **Rama:** `c23-knowledge-corpus-and-indexer` · **Commit de artefactos:** `ea5b68a` · **Implementación:** en árbol de trabajo, sin commitear al cierre de esta pasada
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **58/58 tareas**. Las de la §9 (medición) se ejecutaron: la mini-medición y la calibración *offline* según exige la spec, la latencia contra PostgreSQL real, y la re-medición del catálogo contra `ai.product_document` con la base local levantada.
> **Desviación de artefactos:** este change **amplía la regla 5 de autoría** con una segunda mitad que los artefactos no preveían, y con ella la spec y el diseño. El origen, el fundamento y las enmiendas están en §9.1.
> **Lo que este change NO deja hecho, y conviene leer antes que nada:** el índice real **está vacío**. Ver §12.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11.15 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| SQLAlchemy | 2.0.52, Core, sin clase mapeada y sin segundo *engine* |
| PostgreSQL | testcontainers `pgvector/pgvector:pg15` → **15.19 con `vector` 0.8.6** para los tests `db` y para la medición de latencia; `jpv-pv-postgres` (misma imagen) para la re-medición del catálogo |
| .NET | **no ejecutado, y a propósito**: este change no toca `backend/`, y su diff lo demuestra (§5) |
| Frontend | **no ejecutado**, por lo mismo |
| Contrato | `ai-service/openapi.json` **no se mueve**. Comprobado por regeneración en memoria, no por inspección (§6) |
| Freeze C11 | `git diff -- ai-service/src/jbg_ai/indexing/embeddings.py` **vacío**, y fijado por hash SHA-256 en `test_embeddings_module_is_untouched` |
| Vocabulario C09 | `git diff -- ai-service/src/jbg_ai/enrichment/vocabularies.yaml` **vacío**. Se **lee** para derivar la cobertura, nunca se escribe |
| Proveedor de embeddings | **No se llama en ninguna prueba ni en ninguna medición.** Los tests usan `FakeEmbeddingClient` (C11) y la medición usa el embebedor determinista de `knowledge/offline.py` |
| Proveedor de LLM | **No se llama en absoluto.** El corpus lo generaron ocho subagentes en la sesión de implementación, no el código |

---

## 1. Suites automáticas

La línea base se midió **de verdad**, con `git stash push -u` sobre el árbol en `ea5b68a`, y el árbol se restauró y se verificó idéntico con `diff` antes y después.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`ea5b68a`, sólo artefactos) | **704 passed**, 0 failed, 24,1 s |
| `ai-service` al cerrar los grupos 1-8, sin Docker | 774 passed, **3 skipped** (los `db`) |
| `ai-service` con Docker levantado | **795 passed**, 0 failed, 68,7 s |
| `ai-service` tras cubrir los tres escenarios que faltaban (§9.2) | **798 passed**, 0 failed, 58,2 s |
| `openspec validate --all --strict` | **51 passed, 0 failed** |
| `python -m jbg_ai.knowledge validate` | `ok: 32 documentos, 161 secciones, 7 filas en la tabla de tallas` |
| `dotnet test` · `npm run test` | **no ejecutados**: fuera del diff. Ver §5 |

**+94 tests** sobre la línea base (704 → 798). El recuento **sí es fiable** aquí: la suite de `ai-service` parte de **cero fallos** y no llama a proveedores ni a RDS, así que no aplica la comparación por nombres que `CLAUDE.md` exige en `backend/` y en `frontend/`.

> **Los tres tests `db` saltan si Docker no responde, y la primera pasada saltó.** Está dicho porque es exactamente la trampa que el README ya documenta para `tests/migrations/`: una corrida verde no prueba por sí sola que se ejercitó el SQL. Se levantó Docker y **se volvieron a correr en verde**; los resultados de §2.3 son de esa segunda pasada.

### Desglose de tests nuevos

| Fichero | Tests | Qué cubre |
|---|---:|---|
| `tests/knowledge/test_corpus_rules.py` | **23** *(37 casos con parametrización)* | Las siete reglas de autoría contra documento sintético **y** contra el corpus real: tope de tamaño que falla en vez de trocear, texto antes de la primera sección, `claim_scope` ausente y desconocido, `guion_venta` rechazado por nombre, `eval_question` obligatoria, encabezado de tercer nivel, marca colocada tras el cuerpo, **cinco formas de SKU y precio**, **siete formas de recuento del catálogo** y **seis cifras legítimas que deben pasar**; cobertura derivada del vocabulario y el fallo al ampliarlo sin ficha; y el recuento exacto del corpus |
| `tests/knowledge/test_chunking.py` | **12** | Títulos en metadatos y al principio del contenido; marca retirada del índice; ausencia de solape; trazabilidad del documento; **el `citation_id` abriendo fichero y encabezado reales**; identidad estable entre reindexados y **fijada por valor**; inserción de sección que no repunta citas y que **sí** mueve las posiciones; hash por contenido y no por posición; `claim_scope` que viaja; `source_ref` opcional |
| `tests/knowledge/test_indexer.py` | **13** *(3 marcados `db`)* | Espacio de versiones propio distinto del de producto; identidad determinista escrita en cada fila; no re-embeber lo no cambiado; dos corridas que dejan las mismas filas; borrado de lo que la corrida no produce; **versión de preprocesado caducada que recomputa**; **ningún identificador de producto en la fila**; `--full`; editar una sección que re-embebe una sola; el corpus entero indexado *offline*. Y contra **PostgreSQL real**: indexar/reindexar, **reordenar secciones sin romper el único `(document_id, chunk_index)`** y **cascada al borrar un documento** |
| `tests/knowledge/test_search.py` | **11** | Cita resoluble en el resultado; `claim_scope` que viaja hasta el llamante; **abstención en tres preguntas fuera de dominio**; umbral que devuelve cero; híbrido apagado que degrada a vectorial puro; **ninguna llamada a proveedor con el cliente inyectado**; pregunta vacía que no embebe nada; filtro por `doc_type` sólo si se pide; puntuación normalizada de RRF y no distancia cruda; ninguna ruta HTTP; pregunta de cuidados que responde desde la ficha de su material |
| `tests/knowledge/test_sizing.py` | **7** | Tabla de D16 **fila a fila**: tallas enteras, tres por letra, tramos contiguos y sin solape, `circunferencia = talla + 40` y diámetro derivado; las siete letras del vocabulario con `XXS` y `XXL` por encargo; **la tabla en un solo documento**; aritmética `general` y asignación `establecimiento`; palabras de escala de motivo que nunca son ajuste; **límites de ajuste que coinciden en los cinco documentos que los enuncian** |
| `tests/knowledge/test_measure.py` | **9** *(1 marcado `slow`)* | Fixture de 32 + 5; preguntas fuera de dominio versionadas; **sidecar que sella cómo se produjo el corpus**; medición reproducible; abstención puntuada; **el default de `Settings` es el valor calibrado**; el híbrido gana al vectorial; ninguna tabla `ai.eval_*` nombrada en código; y la regla de calibración aplicada al barrido |
| `tests/knowledge/test_frozen.py` | **4** | Hash SHA-256 de `indexing/embeddings.py`; existencia de los cuatro ficheros congelados; **`knowledge` ausente del snapshot de OpenAPI**; **ninguna sentencia DDL en el paquete** |
| `tests/support/fake_knowledge_repo.py` | — | Repositorio en memoria que **replica el camino de omisión** del real: conserva vector, modelo, versión e instante cuando el hash no cambia |

---

## 2. El corpus, comprobado por su propio validador

### 2.1. Composición

`python -m jbg_ai.knowledge stats`, contrastado contra el §5 del informe de exploración, que fijó las cifras **antes** de escribir una línea:

| | Previsto | Entregado |
|---|---:|---:|
| Documentos | 32 | **32** ✅ |
| Secciones | ~161 | **161** ✅ |
| `material` · `talla` · `faq` · `politica` | 14 · 4 · 10 · 4 | **14 · 4 · 10 · 4** ✅ |
| `guion_venta` | **0** | **0** ✅ |
| `general` · `establecimiento` | ~136 · ~25 | **136 · 25** ✅ |
| Cuota `establecimiento` | 15,5 % | **15,5 %** ✅ |

No es suerte: el esqueleto de secciones iba **literal** en los ocho prompts de bloque, y `test_the_corpus_declares_the_composition_the_report_publishes` fija los seis números.

### 2.2. Generación en ocho ventanas separadas, como manda D15

Los ocho encargos se ejecutaron en **subagentes independientes**, uno por bloque, cada uno leyendo su prompt versionado. Ninguno vio el corpus de otro. Es la planificación obligatoria del §7 del informe de exploración, y la razón de que nueve fichas de material sigan siendo comparables entre sí.

### 2.3. El SQL, ejercitado contra PostgreSQL real

Tres tests `db` contra `pgvector/pgvector:pg15` efímero, base nueva por test:

| Prueba | Qué demuestra |
|---|---|
| `test_indexing_and_reindexing_against_postgres` | 32 documentos y 161 fragmentos escritos; segunda corrida con **0 embebidos y 3 omitidos**; borrar una sección deja 2 filas con `chunk_index` `0,1` **compactado**; `embedding_version` correcta y `embedding` no nula |
| `test_reordering_sections_does_not_trip_the_unique_constraint` | Reordenar tres secciones no borra nada, **no re-embebe nada** y deja las citas en el orden nuevo. Es el test que justifica el rango de aparcamiento negativo (§9.4) |
| `test_deleting_a_document_takes_its_chunks_by_cascade` | La FK `ON DELETE CASCADE` se lleva los fragmentos **sin lógica de aplicación** |

---

## 3. Escenarios de las specs, uno a uno

**39 escenarios `#### Scenario:`** en 11 requisitos del delta `knowledge-corpus`. Todos tienen test nombrado. **Tres de ellos no lo tenían y se les puso al redactar este documento** (§9.2).

### Conocimiento general, nunca por producto (6)

| Escenario | Test | Resultado |
|---|---|---|
| A section naming a product or a price is rejected | `test_a_section_naming_a_product_or_a_price_is_rejected` (5 casos) | ✅ |
| **A section counting the assortment is rejected** | `test_a_section_counting_the_catalogue_is_rejected` (7 casos) | ✅ (§9.1) |
| **A proportion that is not about the assortment is kept** | `test_a_figure_that_is_not_about_the_catalogue_is_allowed` (6 casos) | ✅ (§9.1) |
| **Adding or withdrawing a product invalidates no document** | `test_corpus_does_not_depend_on_the_current_contents_of_the_catalogue` | ✅ (§9.1) |
| The corpus contains no sales scripts | `test_corpus_contains_no_sales_script_document` · `test_a_sales_script_document_is_rejected_by_name` | ✅ |
| Knowledge is general rather than product scoped | `test_material_sheet_is_not_product_scoped` · **`test_an_indexed_chunk_carries_no_product_identifier`** | ✅ (§9.2) |

### Cobertura derivada del vocabulario (2)

| Escenario | Test | Resultado |
|---|---|---|
| Coverage matches the vocabulary | `test_every_canonical_material_has_exactly_one_sheet` | ✅ |
| A new vocabulary term without its sheet is a failure | `test_a_new_vocabulary_term_without_its_sheet_is_a_failure` (inyecta `titanio`) | ✅ |

### La convención de talla, D16 (5)

| Escenario | Test | Resultado |
|---|---|---|
| The table is arithmetically consistent | `test_ring_size_table_is_arithmetically_consistent` | ✅ |
| The table covers the vocabulary, including the unused rungs | `test_ring_size_table_covers_the_size_vocabulary` | ✅ |
| Motif-scale words are never a fit label | `test_motif_scale_words_are_never_a_ring_fit_label` | ✅ |
| The arithmetic and the assignment carry different scopes | `test_the_arithmetic_and_the_assignment_carry_different_scopes` | ✅ |
| Resizing limits agree across the documents that state them | `test_resizing_limits_agree_across_documents` | ✅ |

### Alcance de la afirmación (3)

| Escenario | Test | Resultado |
|---|---|---|
| A section without a declared scope is rejected | `test_section_without_claim_scope_is_rejected` · `test_an_unknown_claim_scope_is_rejected` | ✅ |
| The declared scope travels with the retrieved chunk | `test_claim_scope_travels_with_the_returned_chunk` (por búsqueda) · `test_claim_scope_travels_with_the_chunk` (por troceado) | ✅ |
| One document carries sections of both kinds | `test_no_document_carries_a_single_scope_of_its_own` | ✅ |

### Troceado por secciones (4)

| Escenario | Test | Resultado |
|---|---|---|
| Section titles are preserved in chunk metadata | `test_chunker_preserves_section_titles_in_metadata` · `test_the_indexed_content_carries_both_titles` | ✅ |
| Metadata markers do not reach the index | `test_metadata_markers_do_not_reach_the_index` | ✅ |
| Text before the first section is rejected | `test_document_with_text_before_first_section_is_rejected` | ✅ |
| An oversized section fails ingestion | `test_section_over_the_size_limit_fails_ingestion` · `test_an_oversized_section_is_not_split_automatically` | ✅ |

### Identidad determinista y citas que resuelven (4)

| Escenario | Test | Resultado |
|---|---|---|
| Every chunk is traceable to its document | `test_every_chunk_has_traceable_document_id` | ✅ |
| Identity survives reindexing | `test_chunk_identity_is_stable_across_reindexing` — **y fijada por valor**, no sólo por autoconsistencia | ✅ |
| Inserting a section does not repoint existing citations | `test_inserting_a_section_does_not_repoint_existing_citations` — comprueba además que la **posición sí se movió**, o el test no probaría nada | ✅ |
| A citation that no longer resolves is detected | `test_citation_id_resolves_to_a_file_and_a_heading_in_the_corpus` (161 citas) · `test_a_citation_naming_a_heading_that_no_longer_exists_is_detected` | ✅ |

### Indexación idempotente (3)

| Escenario | Test | Resultado |
|---|---|---|
| Unchanged content is not re-embedded | `test_unchanged_section_is_not_re_embedded` · `test_editing_one_section_re_embeds_only_that_one` | ✅ |
| Chunks no longer produced are removed | `test_reindexing_removes_chunks_no_longer_produced` · `test_indexing_and_reindexing_against_postgres` (SQL real) | ✅ |
| Indexing adds no schema object | `test_the_knowledge_package_contains_no_ddl` (AST sobre el paquete) · `git status` de `migrations/` vacío | ✅ |

### Espacio de versiones propio (2)

| Escenario | Test | Resultado |
|---|---|---|
| Knowledge chunks carry their own preprocessing version | `test_knowledge_chunks_carry_their_own_preprocessing_version` | ✅ |
| **Changing the chunking rules invalidates knowledge embeddings only** | **`test_changing_the_preprocessing_version_recomputes_only_knowledge`** | ✅ (§9.2) |

### Búsqueda con citas y abstención (6)

| Escenario | Test | Resultado |
|---|---|---|
| A search result carries a resolvable citation | `test_knowledge_search_returns_chunk_with_citation_id` | ✅ |
| A question about one material does not answer with another | `test_a_care_question_about_one_material_answers_from_that_sheet` | ✅ *(matizado: ver §8.5)* |
| An out-of-domain question returns nothing | `test_out_of_domain_question_returns_no_citation` (3 preguntas) · `test_below_the_threshold_the_search_returns_nothing_at_all` | ✅ |
| Fusion consumes ranks and not raw scores | `test_fusion_consumes_ranks_and_not_raw_scores` | ✅ |
| The lexical branch can be disabled to measure it | `test_hybrid_disabled_falls_back_to_vector_only` | ✅ |
| Knowledge search opens no HTTP surface | `test_knowledge_search_opens_no_http_surface` · `test_knowledge_opens_no_http_surface` | ✅ |

### Procedencia y medición (3)

| Escenario | Test | Resultado |
|---|---|---|
| **The record accompanies the corpus** | **`test_the_sidecar_records_how_the_corpus_was_produced`** | ✅ (§9.2) |
| The measurement runs offline and is reproducible | `test_the_measurement_runs_offline_and_is_reproducible` | ✅ |
| Out-of-domain questions are part of the measurement | `test_out_of_domain_questions_are_scored_as_abstentions` | ✅ |
| The evaluation tables are untouched | `test_the_measurement_reads_and_writes_no_evaluation_table` (AST, no texto — §9.8) | ✅ |

---

## 4. Nombres exigidos por `tasks.md`

Las tareas 8.2 a 8.9 nombran **24 tests literalmente**. Los 24 existen, con ese nombre exacto:

| Tarea | Nombres | Existen |
|---|---|---|
| 8.2 | `test_chunker_preserves_section_titles_in_metadata` | ✅ |
| 8.3 | `test_every_chunk_has_traceable_document_id` · `test_citation_id_resolves_to_a_file_and_a_heading_in_the_corpus` | ✅ ✅ |
| 8.4 | `test_chunk_identity_is_stable_across_reindexing` · `test_inserting_a_section_does_not_repoint_existing_citations` | ✅ ✅ |
| 8.5 | `test_section_over_the_size_limit_fails_ingestion` · `test_document_with_text_before_first_section_is_rejected` · `test_section_without_claim_scope_is_rejected` · `test_corpus_contains_no_sku_product_or_price` · `test_corpus_contains_no_sales_script_document` | ✅ ×5 |
| 8.6 | `test_every_canonical_material_has_exactly_one_sheet` · `test_material_sheet_is_not_product_scoped` · `test_claim_scope_travels_with_the_returned_chunk` | ✅ ×3 |
| 8.6b | `test_ring_size_table_is_arithmetically_consistent` · `test_ring_size_table_covers_the_size_vocabulary` · `test_motif_scale_words_are_never_a_ring_fit_label` · `test_resizing_limits_agree_across_documents` | ✅ ×4 |
| 8.7 | `test_reindexing_removes_chunks_no_longer_produced` · `test_unchanged_section_is_not_re_embedded` | ✅ ✅ |
| 8.8 | `test_knowledge_search_returns_chunk_with_citation_id` · `test_out_of_domain_question_returns_no_citation` · `test_hybrid_disabled_falls_back_to_vector_only` · `test_knowledge_search_makes_no_provider_call_with_injected_fake` | ✅ ×4 |
| 8.9 | `test_embeddings_module_is_untouched` | ✅ |

---

## 5. Alcance negativo

```bash
git status --short -- frontend/ terraform/ .github/ backend/ \
  ai-service/openapi.json ai-service/migrations/ \
  ai-service/src/jbg_ai/indexing/embeddings.py \
  ai-service/src/jbg_ai/enrichment/vocabularies.yaml \
  ai-service/src/jbg_ai/retrieval/
```

Salida **vacía**.

| Guardarraíl | Comprobación | Resultado |
|---|---|---|
| `indexing/embeddings.py` | `git diff` vacío **y** hash SHA-256 fijado en `test_embeddings_module_is_untouched` | ✅ |
| `enrichment/vocabularies.yaml` | `git diff` vacío. Se lee para derivar cobertura; **nunca se escribe** | ✅ |
| `retrieval/orchestrator.py` · `retrieval/search.py` | `git diff` vacío. Se **importan** `fusion.py`, `lexical.py` y `synonyms.py`; el SQL de conocimiento es propio | ✅ |
| `frontend/` · `terraform/` · `.github/workflows/` · `backend/` | `git diff` vacío | ✅ |
| **Migración** | **ninguna**, ni Alembic ni EF Core. `test_the_knowledge_package_contains_no_ddl` recorre el AST del paquete buscando `create table`, `alter table`, `drop table`, `create index`, `add column` | ✅ |
| Ruta `/v1` nueva | **ninguna**. `openapi.json` regenerado en memoria e idéntico; `knowledge` ausente del snapshot | ✅ |
| `canonical_openapi_settings` | **sin tocar**, como pedía la tarea 7.4: los dos ajustes nuevos no entran en el contrato | ✅ |
| Tablas `ai.eval_*` | no se nombran en código; comprobado por AST y no por texto (§9.8) | ✅ |
| Esquema `public` desde Python | ninguna sentencia lo lee; el indexador sólo escribe `ai.knowledge_*` | ✅ |
| `dotnet test` · `npm run test` | **no ejecutados**, porque el diff no toca esos árboles. Es lo que el DoD del ticket pide y lo que el `git status` demuestra | ✅ |

**Diff total: 9 ficheros modificados (+337 / −67) y 6 árboles nuevos.** Los nueve modificados son exactamente los que el ticket declaraba: `settings.py`, `indexing/cli.py`, `tests/support/settings.py`, `ai-service/README.md`, `Documentos/epicas.md`, el informe de exploración y los tres artefactos del change.

---

## 6. El contrato, **no** movido

A diferencia de C22, aquí `openapi.json` **no se regenera**. Comprobado por construcción y no por lectura:

```python
app = create_app(canonical_openapi_settings())
spec = get_openapi(title=app.title, version=app.version, routes=app.routes, ...)
spec == json.load(open("openapi.json"))   # True
```

→ `openapi.json: sin diff`, 11 rutas, **0 rutas de conocimiento**.

La búsqueda es un *callable* del servicio, no una ruta. `ai-service-api-contracts` congela la superficie `/v1` con un MUST que enumera diez rutas, y el único consumidor —C30— vive en el mismo proceso Python: abrir una ruta habría obligado a regenerar el contrato y acordarlo con el lado .NET **para conectar dos módulos del mismo proceso**.

Los dos ajustes nuevos no viajan en ninguna petición: son *default* en `Settings` y **valor efectivo por parámetro de la llamada**, el patrón de C20/C21/C22.

---

## 7. Decisiones de diseño, verificadas en código

| Decisión | Evidencia |
|---|---|
| D0 · Espacio de versiones propio | `knowledge_version_key` se calcula en `indexer.py`; `document_version_key` de C11 **no se importa**. `test_knowledge_chunks_carry_their_own_preprocessing_version` exige que difieran y compartan modelo y dimensión |
| D1 · Ninguna ruta HTTP | `test_knowledge_search_opens_no_http_surface` sobre el snapshot; subcomando de CLI en su lugar |
| D2 · Ningún router | `search_knowledge` no clasifica: recibe la pregunta y un `doc_type` **opcional que sólo el llamante pone** |
| D3 · Identidad `uuid5`, nunca la posición | `chunk_id` sobre `<doc>#<sección>`; `test_inserting_a_section_does_not_repoint_existing_citations` falla si alguien vuelve a `(document_id, chunk_index)` |
| D4 · Alcance por sección, no por documento | `claim_scope` en `Section`, no en `KnowledgeDocument`; `test_no_document_carries_a_single_scope_of_its_own` comprueba que **existe** un documento con las dos clases |
| D5 · Troceado sin solape, con los dos títulos dentro | `compose_content`; `test_chunks_do_not_overlap` y `test_the_indexed_content_carries_both_titles` |
| D6 · Los dos índices no se fusionan | `search.py` sólo consulta `ai.knowledge_chunk`; ninguna sentencia menciona `product_document` |
| D7 · Híbrido por RRF importando C21 | `from jbg_ai.retrieval.fusion import fuse` — **cero líneas reescritas**. Medido y confirmado (§8.1) |
| D8 · Umbral propio, calibrado | `JPV_KNOWLEDGE_DISTANCE_THRESHOLD = 0.81`, separado del 0,65 de productos. `test_the_calibrated_default_is_the_one_the_settings_carry` ata el default a la medición |
| D11 · `content_hash` en `metadata`, no en columna | `KnowledgeChunk.metadata()`; ninguna migración |
| D13 · Cero `guion_venta` | rechazado **por nombre** en el parser, con el porqué en el mensaje de error |
| D14 · Tope de 1.200 que falla en vez de trocear | `MAX_SECTION_CHARS`; no existe ninguna función de partición en el paquete |
| D15 · Ocho encargos en ventanas separadas | ocho prompts versionados, ocho subagentes independientes (§2.2) |
| D16 · La convención de talla | `sizing.py` **re-parsea la tabla del Markdown** y comprueba su aritmética fila a fila: la tabla no se copia al código, se lee del corpus |
| **D17 · El corpus no cuenta el catálogo** | `forbidden_content_reason` con nueve patrones; `test_corpus_does_not_depend_on_the_current_contents_of_the_catalogue` (§9.1) |

---

## 8. Mediciones

Informe completo en [`c23-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c23-implementation-measurements.md).

### 8.1. La rama léxica se queda, y por medición (tarea 9.3)

Sobre 32 preguntas del fixture más 5 fuera de dominio, al umbral calibrado:

| Configuración | Recall@3 | MRR | Abstención |
|---|---:|---:|---:|
| **Híbrido** | **78,1 %** (25/32) | **0,729** | **100 %** (5/5) |
| Vectorial solo | 71,9 % (23/32) | 0,688 | 100 % (5/5) |
| Diferencia | **+6,2 pp** | **+0,042** | 0 |

**La predicción de D7 se cumple donde apretaba**: las dos preguntas que el híbrido recupera son las de `material-cuero` y `material-resina`, dos de las cuatro fichas compactas. Y **no cuesta abstención**, que es lo que no se podía dar por supuesto.

### 8.2. Umbral calibrado (tarea 9.4)

`python -m jbg_ai.knowledge calibrate` sobre once umbrales. **0,81**, con las citas fuera de dominio apareciendo en **0,84** y sin ganancia de recall entre 0,81 y 0,83. Sustituye al 0,65 provisional en `Settings`, y está anotado en `design.md` D8 con la tabla completa.

### 8.3. Latencia (tarea 9.5)

Contra PostgreSQL con los 161 fragmentos indexados, en caliente, 100 muestras por configuración:

| Configuración | media | p50 | p95 |
|---|---:|---:|---:|
| Híbrido | 60,9 ms | **60,7 ms** | 67,0 ms |
| Vectorial solo | 56,7 ms | 57,7 ms | 62,9 ms |

**La rama léxica cuesta ~3 ms.** Excluye el embebido de la pregunta, que comparte cliente y caché con la rama de productos.

### 8.4. Re-medición contra `ai.product_document` (tarea 9.6)

Con `jpv-pv-postgres` levantado y 1.168 documentos activos. Confirmados al producto: `plata`, `latón`, `baño de oro`, `resina`, `acero`, `cuero`, y **las cinco letras de talla más `mini`, `extramini` y `mediano`**. Movidos: `oro` 418→343, `hilo` 63→37, `perla` 8→**0** (el extractor la clasifica sólo como piedra), multi-material 12,0 %→7,8 %, `coral` 102→23. **`XXS` y `XXL` siguen en cero**, así que D16 sale intacta. El §2 del informe de exploración lleva ahora una nota con los deltas.

### 8.5. Lo que la medición **no** demuestra, dicho aquí

- **El embebedor es un sustituto.** La spec exige medir sin proveedor, así que el barrido usa el embebedor determinista de `knowledge/offline.py`, que puntúa **solape léxico y no significado**. Lo calibrado es **la regla**; el número hay que reconfirmarlo contra producción. Por eso `test_a_care_question_about_one_material_answers_from_that_sheet` asegura el top 3 y **no la primera posición**: fijar la posición uno sería fijar el sustituto, no la propiedad.
- **Tres de los siete fallos no son fallos de recuperación.** Dos preguntas sobre ajuste de talla devuelven `politica-reparaciones-y-ajustes`, que **responde la pregunta**; el fixture las cuenta mal porque asigna un documento esperado por pregunta. El 78,1 % es un **suelo**.

---

## 9. Incidencias de esta pasada

### 9.1. El corpus se había atado al catálogo de hoy — **detectado por el usuario**

**La incidencia más importante del change, y no la encontró un test.**

Los ocho prompts llevan la evidencia medida de su bloque porque es lo que justifica **qué** documentos existen y con **cuánta** profundidad. Los documentos generados hicieron lo natural: citarla. Cuatro secciones acabaron diciendo *«`pequeño` encabeza con 108 etiquetas»*, *«el 44,6 % del surtido no depende de talla»*, *«144 piezas declaran dos materiales»*.

**Eso convierte el corpus en una foto del catálogo.** Entra un producto de oro, se agota el último zafiro, y la sección queda falsa **en silencio** — la cita sigue resolviendo y sigue localizando, así que la verificación estructural la sella como comprobada. Es el modo de fallo que el change entero existe para evitar, entrando por una puerta que nadie miraba, y el corpus de conocimiento y el índice de catálogo tienen ritmos de cambio distintos **a propósito**.

**Corregido en tres capas, no sólo en el texto:**

| Capa | Qué se hizo |
|---|---|
| Corpus | **Seis secciones reescritas en cinco documentos**, más el piloto escrito a mano, que decía *«el noventa por ciento de los casos»* — precisión inventada, ahora *«casi todos los casos»* |
| Regla | La regla 5 gana su segunda mitad en `data/knowledge/README.md` y en **los ocho prompts**, con la instrucción explícita de que las cifras del encargo **no se copian** |
| Ingesta | `forbidden_content_reason` con cuatro patrones nuevos, y **13 casos de test** — 7 que deben caer y 6 que deben pasar |

**El detector lee el vecindario, no el símbolo**, y eso costó una segunda iteración: la primera versión prohibía el porcentaje a secas y **borró mineralogía legítima** — *«el ópalo lleva entre un tres y un diez por ciento de agua»*, que seguirá siendo verdad dentro de veinte años. Un porcentaje sólo cae si está a menos de 40 caracteres de un sustantivo que cuenta catálogo. Y los numerales en letra cuentan **a partir de once**: *«dos piezas de oro que comparten cajón se rayan»* es prosa corriente, *«veintiocho colecciones»* es un censo.

**Enmiendas de artefactos:** decisión **D17** en `design.md`; **tres escenarios nuevos** en el delta de spec, incluido el que enuncia la propiedad de verdad —*añadir o retirar un producto no invalida ningún documento*—; §6 del informe de implementación.

> **La segunda medición cambió el umbral calibrado.** Al reescribir las seis secciones, la curva de calibración se movió: el valor sigue siendo 0,81, pero el recall dejó de ser **no monótono** —antes 0,82-0,83 caían al 75 %— y el MRR del híbrido pasó de +0,057 a +0,042. Las tres afirmaciones que citaban la curva vieja se corrigieron en `settings.py`, en el README y en el test.

### 9.2. Tres escenarios de la spec no tenían test, y este documento los encontró

Al construir la tabla del §3 aparecieron tres escenarios sin comprobación. Es exactamente para lo que sirve escribir el `qa.md` escenario a escenario en vez de fiarse del recuento verde:

| Escenario | Test añadido |
|---|---|
| Changing the chunking rules invalidates knowledge embeddings only | `test_changing_the_preprocessing_version_recomputes_only_knowledge` — caduca la versión de tres filas y comprueba que se recomputan las tres, y que **ninguna tabla fuera de `ai.knowledge_*` se direcciona** |
| Knowledge is general rather than product scoped | `test_an_indexed_chunk_carries_no_product_identifier` — indexa el corpus entero y exige que las claves de `metadata` estén en una lista blanca de nueve y que **ningún UUID** aparezca ni en los metadatos ni en el contenido |
| The record accompanies the corpus | `test_the_sidecar_records_how_the_corpus_was_produced` — los cinco campos de procedencia y los cuatro recuentos, **contrastados contra el corpus vivo** |

Suite: 795 → **798**.

### 9.3. La regla de calibración de D8 era una conjunción que ningún valor satisface

D8 pide *«el valor más estricto que mantiene en cero las fuera de dominio **sin perder ninguna** con respuesta»*. Medido, el recall se agota en el 78 % mucho antes de que la abstención se rompa: **leída al pie de la letra, la regla no calibra nada** y `calibrated_threshold` devolvía `None`.

Se aplica por lo que significa, y está escrito en el docstring de la función: **cero citas fuera de dominio es una restricción**, dentro de esa banda se maximiza Recall@3, y los empates los gana el valor más estricto — que es la palabra que la propia regla usa. No se cambió la regla en el diseño: se documentó cómo se aplica y por qué.

### 9.4. Reordenar secciones rompía el único `(document_id, chunk_index)`

`chunk_index` se sigue escribiendo porque la restricción lo exige. Consecuencia no obvia: **intercambiar dos secciones colisiona a mitad del upsert**, porque la fila que va a ocupar el índice 0 aún lo tiene otra.

Se resuelve aparcando las filas supervivientes en un rango negativo —`chunk_index = -1 - chunk_index`— dentro de la misma transacción, antes de escribir los índices finales. Fijado por `test_reordering_sections_does_not_trip_the_unique_constraint`, contra SQL real, que además comprueba que **no se re-embebe nada**: reordenar no cambia contenido.

### 9.5. Los tests `db` saltaron en silencio en la primera pasada

Docker no estaba levantado y `postgres_container` **salta** en vez de fallar, por decisión del proyecto documentada en el README. La primera corrida completa dio **774 passed, 3 skipped** y parecía verde. Se levantó Docker Desktop, se arrancó `jpv-pv-postgres` y se volvieron a correr: **3 passed**. Todos los números de este documento son de corridas con Docker vivo.

### 9.6. La consola de Windows rompía la salida de la medición

`python -m jbg_ai.knowledge measure` fallaba con `UnicodeEncodeError` al imprimir `→` bajo `cp1252`. Sustituido por `->`. Es un fallo de presentación, no de cálculo, pero habría hecho inservible el comando en la máquina donde se usa.

### 9.7. El guardarraíl de `ai.eval_*` se delataba a sí mismo

`test_the_measurement_reads_and_writes_no_evaluation_table` buscaba las tres cadenas en el texto de los ficheros, y **falló contra el docstring de `measure.py`**, que las nombra a propósito para explicar por qué no se usan. Reescrito sobre el **AST**: excluye docstrings y mira literales, `Name` y `Attribute`. Un guardarraíl que castiga la explicación de por qué existe está mal escrito.

### 9.8. Dos cifras del informe de exploración no cuadran entre sí

El §7 reparte 31 y 26 secciones entre los encargos 1 y 2; el esqueleto del §5 da **30 y 27**. El total —57, y 161 en el corpus— es el mismo, así que ninguna decisión depende de ello. Se siguió el esqueleto, que es lo que los prompts copian literalmente. **No se corrigió el informe de exploración**: es un registro fechado, y la discrepancia queda anotada aquí.

### 9.9. El rango de 80-250 palabras y el tope de 1.200 caracteres no son compatibles

1.200 caracteres son unas 190 palabras de español, así que el tramo alto del rango no cabe. **El tope de caracteres es el que se comprueba**; el de palabras es la horquilla de intención. Está escrito así en la guía de autoría y en los ocho prompts, que piden apuntar a **110-170 palabras**. La sección más larga del corpus entregado ocupa **872 caracteres**, holgadamente dentro.

---

## 10. Verificado a mano

- **Las 161 citas resuelven**: `test_citation_id_resolves_to_a_file_and_a_heading_in_the_corpus` abre cada fichero y busca el encabezado con una expresión anclada. No es una muestra.
- La tabla de tallas se leyó **impresa desde el fichero**, no desde el prompt, para confirmar que el subagente la copió carácter a carácter incluido el guion U+2013.
- `\d ai.knowledge_chunk` contra la base local, leído entero: confirma que `tsv` es `generated always as (to_tsvector('spanish'::regconfig, content)) stored` — es decir, **el código no la escribe ni puede equivocarse de idioma** — y que los tres índices (HNSW coseno con `m=16, ef_construction=128`, GIN sobre `tsv`, GIN sobre `metadata`) existen esperando filas.
- `python -m jbg_ai.indexing --help` comprobado tras añadir el subcomando: `{sync,sync-pos,sync-knowledge}`.
- El detector de la regla 5 se probó con **once frases a mano** —seis que deben pasar y cinco que deben caer— antes de escribir el test, para no fijar un comportamiento equivocado.
- `git stash push -u` / `git stash pop` con `diff` de `git status --porcelain` antes y después: **árbol restaurado idéntico**, 15 entradas en ambos casos.
- El estado real del índice se consultó en vez de suponerse: `ai.knowledge_document` y `ai.knowledge_chunk` a **0 filas** (§12).

---

## 11. Documentación de contexto

| Documento | Qué se alineó |
|---|---|
| `ai-service/README.md` | Entrada de C23 en la lista de changes; **dos filas nuevas** en la tabla de entorno con la curva de calibración y la medición del híbrido; sección nueva **«The knowledge corpus and its index (C23)»** con los cinco comandos, el porqué de que no haya ruta y **la declaración de limitación** (corpus sintético, 15,5 % ilustrativo, verificación estructural y no semántica); `knowledge/` en el árbol de `src`, `prompts` y `tests`; y la línea obsoleta «`ai.knowledge_*` stays empty until C23» corregida |
| `data/knowledge/README.md` | Guía de autoría nueva con las siete reglas, el formato exacto, y la declaración de lo que el corpus es y no es |
| `design.md` | **D17** nueva; D7 y D8 con sus mediciones; tabla de preguntas abiertas actualizada; **dos** verificaciones posteriores en vez de una |
| `specs/knowledge-corpus/spec.md` | Cláusula y **tres escenarios** en el primer requisito (§9.1) |
| `Documentos/epicas.md` | Párrafo nuevo en EP12 con lo que la implementación midió |
| Informe de exploración | Nota en el §2 con los deltas de la re-medición, **sin reescribir las cifras originales**: la diferencia entre ambas es el dato |
| Informe nuevo | `c23-implementation-measurements.md`, con la mini-medición, la calibración, la latencia, la re-medición del catálogo y el §6 sobre la regla que se descubrió |

---

## 12. Fuera de esta pasada

- **El índice real está vacío, y es lo primero que hay que saber.** `ai.knowledge_document` y `ai.knowledge_chunk` tienen **0 filas** en `jpv-pv-postgres`. Troceado y embebido sólo han ocurrido en contenedores efímeros y **con vectores falsos**. No es un descuido: el DoD del ticket exige *«sin llamadas reales a LLM, embeddings ni RDS»*, y poblar el índice son 161 llamadas de pago al proveedor. El comando es `python -m jbg_ai.indexing sync-knowledge` y necesita `JPV_EMBEDDING_API_KEY`.
- **Re-calibrar el umbral contra el embebedor de producción**, por lo dicho en §8.5. Ajuste de entorno, sin cambio de código y sin reindexar.
- **Confirmar la tabla de tallas de D16 con el negocio** antes del vídeo de la demo. Cambia **una sección de un documento** y su marca `establecimiento` ya la señala.
- **Generación con citas, `pitch` y avisos** — es C30. Este change entrega el *callable* con la firma en forma de tool y la latencia medida.
- **Golden set, tablas `ai.eval_*`, RAGAS y validador anti-alucinación** — es C24, que podrá absorber el fixture de las 32 preguntas con relevancia graduada y subir el Recall@3 real sin tocar el índice.
- **Router de consultas, reranking y fusión de los dos índices.** Ninguno se hace, y D2 y D6 explican por qué no es una omisión.
- **Los textos comerciales reales de la joyería.** Si llegan, el eje «quién lo escribió» deja de ser constante y gana su campo, de forma aditiva y sin migración.

---

## Veredicto

**Sin problemas abiertos.** `uv run --system-certs pytest` **798 passed, 0 failed** sobre una línea base medida de **704**, sin abrir un socket a proveedor, LLM ni RDS, y con los tres tests de base ejecutados de verdad contra pgvector. `openspec validate --all --strict` **51 passed, 0 failed**. **39/39 escenarios** con test nombrado, **24/24 nombres** exigidos por `tasks.md`, **58/58 tareas**.

**Cero migraciones y `openapi.json` byte a byte idéntico**, comprobado por regeneración en memoria y no por lectura. Los cuatro ficheros congelados, sin diff; `indexing/embeddings.py` además fijado por hash.

**Dos decisiones que se tomaron con el número y no con la intuición**, en la cultura que C20, C21 y C22 dejaron: la rama léxica se queda porque gana **+6,2 pp de Recall@3 sin costar abstención**, y el umbral es **0,81** porque a partir de 0,84 empieza a citar lo que no debe. Las dos con su limitación declarada: el embebedor de la medición es un sustituto léxico, así que lo calibrado es la regla y el número es provisional.

**Una desviación de artefactos, y la encontró el usuario, no un test** (§9.1): el corpus se había atado al catálogo de hoy citando cifras medidas, y un documento que caduca en silencio bajo una cita verificada es peor que uno que nunca dio el número. Corregido en las tres capas —texto, regla y validador—, con D17 en el diseño y tres escenarios nuevos en la spec.

**Y tres escenarios sin test que este propio documento destapó** (§9.2), porque recorrerlos uno a uno es lo que un recuento verde no hace.

**Listo para archivar**, con una advertencia que no bloquea y que conviene no perder: **el índice real sigue vacío**. C30 necesita que alguien corra `sync-knowledge` con una clave de embeddings antes de tener algo que citar.
