# QA — C21 `add-hybrid-search-rrf`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** 2026-09-02 · **Rama:** `c21-add-hybrid-search-rrf` · **Commit de artefactos:** `73d89dc` · **Commit de implementación:** `3965cc3`
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **38/38 tareas**. La 8.5 se ejecutó contra el índice local y el proveedor real el 2026-09-02; ver §11.
> **Seguimiento verify:** misma fecha. 1 CRITICAL (la 8.5, ya cerrada), 3 WARNING y 2 SUGGESTION, **todas cerradas**; ver §12.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11.15 |
| Gestor | `uv` 0.11.7 — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| Contrato | `ai-service/openapi.json` — **no se regenera**. `test_openapi_snapshot_is_stable` verde **sin** tocar el snapshot |
| Freeze C11 | `git diff -- ai-service/src/jbg_ai/indexing/embeddings.py` **vacío**, y además fijado por hash en `test_embeddings_module_is_unchanged` |
| Vocabulario C09 | `git diff -- ai-service/src/jbg_ai/enrichment/vocabularies.yaml` **vacío** |
| .NET | **No se ejecuta** `dotnet test`: C21 no cruza `backend/`. Ver §4 |
| Docker / pgvector | **No se exige.** `tests/retrieval/` inyecta fakes; el fake de búsqueda gana `doc_text` para ejercitar la rama léxica sin una configuración de texto en español |
| Proveedor de embeddings | **No se llama.** Ningún test abre socket a OpenAI / LiteLLM / RDS |

---

## 1. Suite automática de `ai-service`

La línea base se midió **de verdad**, no se supuso: `git checkout HEAD~1`, suite completa, y vuelta a la rama. El árbol estaba limpio y commiteado, así que la medición es reproducible.

| Ejecución | Resultado |
|---|---|
| Línea base en `HEAD~1` (artefactos, sin código) | **510 passed**, 0 failed, 35,5 s |
| Alcance de `tests/retrieval/` durante el apply | **112 passed** |
| Suite completa al cerrar los grupos 1-8 | **589 passed**, 0 failed, 44,5 s |
| Suite completa tras acotar `low_confidence` (§9.6) | **594 passed**, 0 failed, 39,1 s |
| `openspec validate --all --strict` | **49 passed, 0 failed** |
| `openspec validate add-hybrid-search-rrf --strict` | *valid* |
| Suite tras cerrar el verify y ejecutar la 8.5 | **598 passed**, 0 failed |

**+88 tests** sobre la línea base (510 → 598). El recuento de funciones `def test_` contra el commit de artefactos da exactamente los mismos 88, así que no hay tests recolectados y no ejecutados.

> El recuento **sí es fiable aquí**, a diferencia de las suites de backend y frontend: la de `ai-service` parte de cero fallos y no llama a proveedores ni a RDS. Para la de frontend, que arranca en rojo, la comparación se hace por **nombres** en §6.

### Desglose de tests nuevos o ampliados

| Fichero | Antes → Después | Qué cubre |
|---|---|---|
| `tests/retrieval/test_lexical.py` | 0 → **11** | Un placeholder por forma emitida y cero texto de operador en el SQL; `||` entre grupos y nunca `&&`; `plainto` y nunca `phraseto`; `websearch` con comillas y negación, y entrada malformada que no revienta; campos escasos que no cuentan; término no resuelto que sí cuenta; consulta sólo subjetiva → coordinación `0` |
| `tests/retrieval/test_fusion.py` | 0 → **13** | Consenso por encima del campeón de una lista; pureza (sin socket, sin sesión); scores crudos no consumidos; profundidad simétrica e independiente del overfetch; pesos desde settings y no en el código; peso vectorial por debajo del léxico; degradación exacta con expansión apagada; normalización a 1,0 monótona |
| `tests/retrieval/test_filters.py` | 0 → **15** | Extracción de techo de precio en cinco frases naturales; número suelto que **no** es un techo; talla y materiales desde `ExpandedQuery.matched`; bloque estable que degrada y nunca borra; proyección desconocida que no degrada; documento sin materiales que no se borra; `@>` excluido con su medición; filtros del body que siguen excluyendo; `piece_type` sin `WHERE` |
| `tests/retrieval/test_cache.py` | 0 → **7** | Cota dura con desalojo; LRU real (leer mantiene vivo); clave por texto+modelo+versión; techo `< 1` rechazado; interfaz C11 satisfecha; **freeze de `embeddings.py` por hash** |
| `tests/retrieval/test_orchestrator.py` | 17 → **40** | Modos honestos, procedencia real, diagnóstico ausente y no inventado, score fusionado, degradación 200/503, concurrencia con el proveedor, filtros que degradan, notas de `debug`, barrido de pesos en un proceso, seis etapas de log, y el alcance de `low_confidence` (§9.6) |
| `tests/retrieval/test_search_port.py` | 3 → **9** | SQL léxica con predicado GIN y los cuatro filtros del body; orden por coordinación y luego `ts_rank`; grupo muerto que no cambia el orden; campo escaso que no adelanta; profundidad de rama; ausencia de predicado de precio o stock en **ambas** ramas |
| `tests/retrieval/test_measure.py` | 4 → **8** | El `compare` salta limpio sin base de datos; los tres brazos son los dos extremos y el default; la rúbrica se lee de la propia consulta; placeholders con nombre |
| `tests/config/test_settings.py` | 29 → **35** | Los cinco ajustes no bloquean el arranque; blanco → default; ponderación medida preservada; override por entorno; `k` y profundidad no positivos rechazados; pin canónico |
| `tests/api/test_retrieval_real.py` | 12 → **14** | Los cuatro modos responden 200 y la nota `vector_only_until_c21` ha desaparecido; `mode=lexical` sin llamada al proveedor; degradación a léxico con 200; 503 sin nada léxico que servir; **singleton de proceso con caché acotado** |
| `tests/api/test_health.py` | 9 → **10** | `/health` arranca y responde sin ninguno de los cinco ajustes, y sin cargar el diccionario |
| **Total** | **74 → 162** | **+88** |

**Fakes:** `tests/support/fake_product_search.py` gana `search_lexical`, `doc_text` y `lexical_calls`; el embed sigue siendo el `FakeEmbeddingClient` de C11. Ningún test de `tests/retrieval/` construye `SqlAlchemyProductSearch`.

---

## 2. Escenarios de las specs, uno a uno

**77 escenarios `#### Scenario:`** en los cinco deltas: `hybrid-fusion` 33, `vector-retrieval` 22, `assisted-search-panel` 9, `query-expansion` 7, `ai-service-runtime` 6. Todos tienen test o comprobación nombrada.

### `hybrid-fusion` (33)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Fusión por rango · Consensus outranks a single-list champion | `test_rrf_fuses_ranked_lists_preserving_top_hit` | ✅ |
| Fusión por rango · Raw branch scores are not consumed | `test_raw_branch_scores_are_not_consumed` (los campos de `RankedList` son exactamente `name`/`weight`/`keys`) | ✅ |
| Fusión por rango · Fusion performs no input or output | `test_fusion_performs_no_input_or_output` (socket parcheado a fallo) | ✅ |
| Fusión por rango · Provenance travels with each candidate | `test_provenance_reports_every_list_and_position` | ✅ |
| Pesos y suavizado · Weights are not hardcoded | `test_fusion_weights_and_k_load_from_settings_not_hardcoded`: `0.33` y `0.5` no aparecen en `fusion.py`, y `k`/`depth` **no tienen valor por defecto** en la firma (W1, §12) | ✅ |
| Pesos y suavizado · Two configurations run in one process | `test_two_weight_configurations_run_in_one_process` (settings sin mutar) | ✅ |
| Pesos y suavizado · The vector branch does not outweigh the lexical branch | `test_vector_branch_weight_defaults_below_lexical` | ✅ |
| Pesos y suavizado · Disabled expansion degrades to a single lexical vote | `test_disabled_expansion_degrades_to_single_lexical_vote` · `test_the_two_lexical_weights_sum_to_one_lexical_list` | ✅ |
| Profundidad · The three lists are cut at the same point | `test_branch_depth_is_symmetric_across_lists` | ✅ |
| Profundidad · Branch depth and the returned window are distinct | `test_branch_depth_is_independent_of_overfetch` · `test_branch_depth_does_not_follow_the_requested_page_size` | ✅ |
| Composición segura · A query with an unmatched word still returns candidates | `test_group_matching_nothing_does_not_change_order` · `test_a_group_matching_nothing_adds_zero_to_every_document` | ✅ |
| Composición segura · Terms never reach the SQL text | `test_one_placeholder_per_surface_form_and_no_operator_text_in_the_sql` · `test_lexical_sql_uses_the_gin_predicate_and_applies_every_body_filter` | ✅ |
| Composición segura · A multi-word dictionary form is not required to be adjacent | `test_surface_forms_use_plainto_not_phraseto` | ✅ |
| Coordinación · Matching more of the query ranks higher | `test_lexical_branch_ors_groups_and_ranks_by_coordination` | ✅ |
| Coordinación · A group matching no document changes nothing | `test_group_matching_nothing_does_not_change_order` | ✅ |
| Coordinación · A sparsely covered field cannot jump the queue | `test_sparse_group_cannot_jump_the_queue` · `test_sparse_vocabulary_fields_do_not_count_towards_coordination` | ✅ |
| Coordinación · A literal word the operator typed does decide the order | `test_unresolved_term_counts_towards_coordination` | ✅ |
| Coordinación · A mostly subjective query leaves the ordering to the vector branch | `test_a_query_of_only_sparse_terms_leaves_the_ordering_to_ts_rank` (coordinación `"0"`) | ✅ |
| Filtros que degradan · A price ceiling reorders without removing | `test_structural_filter_demotes_but_never_removes` (unidad y extremo a extremo) | ✅ |
| Filtros que degradan · A body filter still excludes | `test_body_filters_remain_hard` · `test_body_filters_materials_category_family_and_exclusions` | ✅ |
| Filtros que degradan · Multiple materials in the text do not require all of them | `test_multi_material_query_uses_contains_all` (invertido, ver §5) | ✅ |
| Filtros que degradan · No filter is invented | `test_never_invents_filter_absent_from_query` · `test_no_filter_is_invented_when_the_query_expresses_none` · `test_a_bare_number_is_not_a_price_ceiling` | ✅ |
| Filtros que degradan · A document with no extracted materials is not deleted | `test_a_document_with_no_extracted_materials_is_not_demoted` | ✅ |
| Procedencia · Provenance is real, not constant | `test_match_reasons_report_real_provenance` | ✅ |
| Procedencia · A diagnostic is absent rather than invented | `test_an_absent_diagnostic_is_none_never_fabricated` | ✅ |
| Procedencia · Total disagreement is reported without hiding results | `test_low_confidence_signals_absence_of_cross_branch_consensus` · `test_hybrid_still_reports_total_branch_disagreement` | ✅ |
| Procedencia · A single-branch response is not marked low confidence | `test_single_branch_modes_do_not_report_permanent_low_confidence` | ✅ |
| Procedencia · A response degraded to one branch is not marked low confidence either | `test_a_degraded_hybrid_response_is_not_marked_low_confidence` | ✅ |
| Procedencia · The fusion log says how many branches ran | `test_the_fuse_log_names_the_branches_that_actually_ran` | ✅ |
| Observabilidad · The new stages are traceable | `test_the_new_stages_are_traceable` (las seis etapas con `trace_id`) | ✅ |
| Observabilidad · The fusion log reports cross-branch agreement | `test_the_new_stages_are_traceable` (`typed=`, `expanded=`, `vector=`, `cross_branch=`, `low_confidence=`) | ✅ |
| Suite offline · The suite stays offline | `test_fusion_performs_no_input_or_output` + construcción con fakes | ✅ |
| Suite offline · The measured defaults are pinned | `test_vector_branch_weight_defaults_below_lexical` · `test_groups_are_ored_with_each_other_and_never_conjoined` | ✅ |

### `vector-retrieval` (22 + 1 REMOVED)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Embed C11 · Retrieval embed client does not retry | `test_retrieval_embed_client_uses_max_attempts_one_and_a_bounded_cache` · `test_embeddings_module_is_unchanged` | ✅ |
| Embed C11 · The retrieval embed client is built once per process | `test_retrieval_embed_client_is_a_process_singleton` · `test_embedding_cache_is_bounded` | ✅ |
| Embed C11 · Missing embedding key is 503 | `test_missing_embedding_key_is_503` | ✅ |
| Embed C11 · A provider failure degrades to the lexical branch | `test_embedding_failure_in_hybrid_degrades_to_lexical` · `test_provider_failure_degrades_to_the_lexical_branch` | ✅ |
| Embed C11 · A provider failure with nothing lexical to serve is 503 | `test_embedding_failure_with_no_lexical_hits_is_503` · `test_provider_failure_with_nothing_lexical_to_serve_is_503` | ✅ |
| Embed C11 · Lexical mode never calls the provider | `test_lexical_mode_makes_no_provider_call` (orquestador y HTTP) | ✅ |
| Coseno · Results are ordered by fused relevance | `test_score_is_the_fused_rank_score_normalised_to_the_first_result` · `test_real_mode_is_not_501` (primer score 1,0) | ✅ |
| Coseno · The vector diagnostic keeps the distance | `test_an_absent_diagnostic_is_none_never_fabricated` (`vector_score == 0,9` para distancia 0,1) | ✅ |
| Coseno · Distance above the threshold is excluded from the vector list | `test_returns_empty_with_low_confidence_when_no_branch_produces_anything` · `test_overfetch_does_not_refill_from_rows_above_threshold` | ✅ |
| Coseno · A single-branch mode that returns results is not low confidence | `test_single_branch_modes_do_not_report_permanent_low_confidence` | ✅ |
| Coseno · Incompatible embeddings do not count as abstention | `test_empty_compatible_index_raises_dependency_error` · `test_empty_compatible_index_is_503_not_abstention` | ✅ |
| Over-retrieval · Overfetch is capped after fusion | `test_returns_overfetched_candidate_count` (`top_k=5` → 15) | ✅ |
| Over-retrieval · Overfetch does not refill from rows above the threshold | `test_overfetch_does_not_refill_from_rows_above_threshold` | ✅ |
| Over-retrieval · Branch depth does not follow the requested page size | `test_branch_depth_does_not_follow_the_requested_page_size` · `test_branch_depth_is_a_call_parameter` | ✅ |
| Over-retrieval · Token pos_id is echoed and body pos_id is ignored | `test_body_pos_id_is_ignored` · `test_lexical_sql_uses_the_gin_predicate_and_applies_every_body_filter` (`pos_id` ausente) | ✅ |
| Body filters · The four body predicates are applied | `test_body_filters_materials_category_family_and_exclusions` · `test_body_filters_remain_hard` (en **ambas** ramas) | ✅ |
| Body filters · Invalid family_id is 422 | `test_invalid_family_id_raises_before_search` · `test_invalid_family_id_is_422` | ✅ |
| Body filters · Malformed exclusions are ignored | `test_malformed_exclusions_are_ignored` (caplog DEBUG) | ✅ |
| Body filters · A price constraint from the text never deletes a candidate | `test_structural_filter_demotes_but_never_removes` · `test_neither_branch_carries_a_price_or_stock_predicate` | ✅ |
| Logs · trace_id appears in stage logs | `test_the_new_stages_are_traceable` · `test_trace_id_appears_in_stage_logs` (HTTP, las cinco etapas) | ✅ |
| Logs · The fusion log records branch agreement | `test_the_new_stages_are_traceable` · `test_the_fuse_log_names_the_branches_that_actually_ran` | ✅ |
| Logs · The search stage does not borrow the response-level confidence field | `test_the_search_stage_does_not_borrow_the_response_confidence_field` (W2, §12) | ✅ |
| **REMOVED** · Desaparece `vector_only_until_c21` | `test_vector_only_until_c21_no_longer_appears_in_any_response` (los cuatro modos) · `test_every_mode_answers_and_the_c21_placeholder_note_is_gone` | ✅ |

### `query-expansion` (7)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Flag sin tocar el contrato · Disabled expansion yields the original tokens | `test_disabled_flag_returns_original_query` (C20) · `test_disabled_expansion_emits_one_form_per_token` | ✅ |
| Flag sin tocar el contrato · The flag is not part of the request contract | `test_query_expansion_is_not_part_of_the_request_contract` (C20) · `test_openapi_snapshot_is_stable` | ✅ |
| Flag sin tocar el contrato · Two configurations run in one process | `test_expansion_flag_sweeps_two_configurations_in_one_process` | ✅ |
| Flag sin tocar el contrato · Disabling expansion degrades the fusion exactly | `test_disabled_expansion_degrades_to_single_lexical_vote` | ✅ |
| Consumida por la rama léxica · The expansion stage is traceable | `test_the_expansion_stage_no_longer_reports_itself_unconsumed` (`consumed=True`) | ✅ |
| Consumida por la rama léxica · The groups reach the lexical query | `test_hybrid_mode_fuses_all_three_lists` (las dos peticiones) · **`test_the_expansion_finds_what_the_typed_form_alone_would_miss`** (W3, §12: la segunda cláusula, que estaba sin cubrir) | ✅ |
| Consumida por la rama léxica · The resolved terms feed the structural filters | `test_materials_and_size_come_from_the_terms_expansion_already_resolved` | ✅ |

### `ai-service-runtime` (6)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Ajustes de fusión · Health starts without the fusion settings | `test_settings_do_not_require_the_fusion_settings_to_boot` · `test_health_boots_and_answers_without_the_fusion_settings` (200 y diccionario sin cargar) | ✅ |
| Ajustes de fusión · Blank fusion settings are treated as the defaults | `test_blank_fusion_settings_are_treated_as_the_defaults` | ✅ |
| Ajustes de fusión · The measured default weighting is preserved | `test_the_measured_default_weighting_is_preserved` | ✅ |
| Ajustes de fusión · Branch depth is coupled to the smoothing constant | `test_branch_depth_is_of_the_same_order_as_the_smoothing_constant` | ✅ |
| Ajustes de fusión · The settings can be overridden by environment | `test_fusion_settings_can_be_overridden_by_environment` | ✅ |
| Ajustes de fusión · Canonical OpenAPI settings pin the fusion settings | `test_canonical_openapi_settings_pin_the_fusion_settings` · `test_openapi_snapshot_is_stable` | ✅ |

### `assisted-search-panel` (9)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| El resultado se explica · The badge and the materials explain the match | `should display the materials the retriever recognised` + los dos de insignia | ✅ |
| El resultado se explica · A result served only by the lexical branch says so | `should show the lexical origin badge when a result has no vector provenance` · `should show the assisted badge when the result came from both branches` · `should decide per result, so one list can carry both origins` | ✅ |
| El resultado se explica · An unknown origin does not break the row | `should fall back to a neutral label for an origin it does not know` | ✅ |
| El resultado se explica · The raw match reasons are not shown | `should not render the raw match reasons` | ✅ |
| El resultado se explica · An absent variant label leaves no gap | `should leave no gap when the variant label is absent` · `should show the size when the variant label is present` | ✅ |
| Modo de la búsqueda · A degraded semantic branch is stated rather than hidden | `should say the semantic branch did not run when only lexical results came back` · `should report the service text search when nothing came from the semantic branch` | ✅ |
| Modo de la búsqueda · A fused response is not warned about | `should not warn about the semantic branch when it did run` | ✅ |
| Modo de la búsqueda · The caller's own text search keeps its own message | `should show legacy results banner when ai is unavailable` · `should report the legacy text search when the assisted path did not serve` | ✅ |
| Modo de la búsqueda · No results means no claim about the mode | `should claim nothing about the mode when there are no results to read` | ✅ |

---

## 3. Nombres exigidos por `tasks.md`

**30/30 presentes y en verde.** Verificado por script sobre el árbol de tests, no a ojo.

| Nombre | Fichero |
|---|---|
| `test_sparse_vocabulary_fields_do_not_count_towards_coordination` | `test_lexical.py` |
| `test_unresolved_term_counts_towards_coordination` | `test_lexical.py` |
| `test_surface_forms_use_plainto_not_phraseto` | `test_lexical.py` |
| `test_lexical_branch_ors_groups_and_ranks_by_coordination` | `test_search_port.py` |
| `test_group_matching_nothing_does_not_change_order` | `test_search_port.py` |
| `test_rrf_fuses_ranked_lists_preserving_top_hit` | `test_fusion.py` |
| `test_branch_depth_is_symmetric_across_lists` | `test_fusion.py` |
| `test_branch_depth_is_independent_of_overfetch` | `test_fusion.py` |
| `test_fusion_weights_and_k_load_from_settings_not_hardcoded` | `test_fusion.py` |
| `test_vector_branch_weight_defaults_below_lexical` | `test_fusion.py` |
| `test_disabled_expansion_degrades_to_single_lexical_vote` | `test_fusion.py` |
| `test_lexical_query_runs_concurrently_with_embedding` | `test_orchestrator.py` |
| `test_lexical_mode_makes_no_provider_call` | `test_orchestrator.py` **y** `test_retrieval_real.py` |
| `test_match_reasons_report_real_provenance` | `test_orchestrator.py` |
| `test_embedding_failure_in_hybrid_degrades_to_lexical` | `test_orchestrator.py` |
| `test_embedding_failure_with_no_lexical_hits_is_503` | `test_orchestrator.py` |
| `test_low_confidence_signals_absence_of_cross_branch_consensus` | `test_orchestrator.py` |
| `test_single_branch_modes_do_not_report_permanent_low_confidence` | `test_orchestrator.py` |
| `test_a_degraded_hybrid_response_is_not_marked_low_confidence` | `test_orchestrator.py` |
| `test_the_fuse_log_names_the_branches_that_actually_ran` | `test_orchestrator.py` |
| `test_extracts_price_ceiling_from_natural_phrase` | `test_filters.py` |
| `test_never_invents_filter_absent_from_query` | `test_filters.py` |
| `test_structural_filter_demotes_but_never_removes` | `test_filters.py` **y** `test_orchestrator.py` |
| `test_body_filters_remain_hard` | `test_filters.py` |
| `test_material_filter_uses_overlap_by_default` | `test_filters.py` |
| `test_multi_material_query_uses_contains_all` | `test_filters.py` |
| `test_embedding_cache_is_bounded` | `test_cache.py` |
| `test_embeddings_module_is_unchanged` | `test_cache.py` |
| `test_retrieval_embed_client_is_a_process_singleton` | `test_retrieval_real.py` |
| `test_openapi_snapshot_is_stable` | `test_openapi_snapshot.py` (preexistente, verde sin regenerar) |

Nombres exigidos en el frontend, los cuatro presentes: `should show the lexical origin badge when a result has no vector provenance`, `should show the assisted badge when the result came from both branches`, `should say the semantic branch did not run when only lexical results came back`, `should not warn about the semantic branch when it did run`.

---

## 4. Alcance negativo

```powershell
git status --short -- backend/ ai-service/openapi.json ai-service/src/jbg_ai/indexing/embeddings.py ai-service/src/jbg_ai/enrichment/vocabularies.yaml
```

Salida **vacía**, comprobada antes y después del commit.

| Guardarraíl | Comprobación | Resultado |
|---|---|---|
| `backend/` | `git diff` vacío; no se ejecuta `dotnet test` porque no hay nada que ejecutar | ✅ |
| `ai-service/openapi.json` | `git diff` vacío + `test_openapi_snapshot_is_stable` verde | ✅ |
| `indexing/embeddings.py` | `git diff` vacío **y** hash SHA-256 fijado en `test_embeddings_module_is_unchanged`, que además exige que el módulo no mencione `BoundedEmbeddingCache` ni `max_entries` | ✅ |
| `enrichment/vocabularies.yaml` | `git diff` vacío | ✅ |
| Alembic | ninguna revisión nueva: `migrations/versions/` sigue con `f46c55c056e2` y `b8e3c1a4d7f0` | ✅ |
| EF Core | ninguna migración: `backend/` intacto | ✅ |
| `terraform/` | `git diff` vacío | ✅ |
| Esquema `public` | ninguna consulta de servicio lo lee. La única referencia está en `measure.py`, que es CLI de desarrollo, tolera que la tabla no exista y hace `rollback` | ✅ |
| Precio / stock como exclusión | `test_neither_branch_carries_a_price_or_stock_predicate`: ninguna línea `AND`/`WHERE`/`OR` menciona `price`, y `stock` no aparece. `price` **sí** se selecciona, para degradar con él | ✅ |
| `pos_id` como predicado | ausente en las dos ramas | ✅ |
| `ai.query_log` | no existe; se emiten seis etapas de log en su lugar | ✅ |
| TODO / FIXME sin seguimiento | `rg "TODO|FIXME"` sobre `jbg_ai/retrieval/` vacío | ✅ |

---

## 5. Decisiones de diseño, verificadas en código

| Decisión | Evidencia |
|---|---|
| D1 · Tres listas y no dos | `_fuse_branches` recibe `typed`, `expanded` y `vector`; `test_hybrid_mode_fuses_all_three_lists` comprueba que se piden las dos léxicas por nombre |
| D2 · OR entre grupos con coordinación | `build_fragments` une con `\|\|`; `test_groups_are_ored_with_each_other_and_never_conjoined` falla si vuelve `&&`. El orden es `coordination DESC, ts_rank DESC` |
| D3 · RRF ponderado con la rama vectorial por debajo | `0.33` no aparece en `fusion.py`: vive en `FUSION_DEFAULTS`, y `test_fusion_weights_and_k_load_from_settings_not_hardcoded` lo comprueba leyendo el fichero |
| D3b · Profundidad simétrica acoplada a `k` | una sola `depth` para las tres listas; `test_branch_depth_is_symmetric_across_lists` cuenta 10 y 10 con listas de 200 y 60 |
| D4 · Coordinación sólo sobre campos cuya ausencia es evidencia | `SPARSE_VOCABULARY_FIELDS` es constante de módulo con la cobertura medida en el comentario, **no** un ajuste; `test_every_sparse_field_is_excluded_and_the_structural_ones_are_not` fija el conjunto exacto |
| D5 · Los filtros deducidos degradan | `demote()` es un `sorted` estable sobre tres booleanos; devuelve el mismo número de candidatos, y el test lo comprueba por longitud además de por orden |
| D6 · `websearch` para la tecleada, `plainto` para las formas | dos constantes distintas en `lexical.py`, cada una con su test |
| D7 · Sin anclaje de SKU ni nombre exacto | no hay código de realce; nada que verificar salvo su ausencia |
| D8 · `mode` honesto y degradación | `run_vector` / `run_lexical` derivados del modo; `test_lexical_mode_makes_no_provider_call` y `test_vector_mode_does_not_query_tsv` fijan los dos extremos |
| D9 · `low_confidence` como señal | `_low_confidence` no cambia ni el número ni el orden de resultados; ver la corrección de §9.6 |
| D10 · La rama léxica corre contra el proveedor | `asyncio.gather(_embed_stage(), _lexical_stage())`, y dentro de `_lexical_stage` las dos consultas van **secuenciales** para retener una sola conexión del pool de 5 sin overflow. `test_lexical_query_runs_concurrently_with_embedding` bloquea el embed hasta que la léxica arranca: si fueran secuenciales, la prueba se cuelga y el `wait_for` la mata |
| D11 · Singleton con caché acotado sin descongelar C11 | `BoundedEmbeddingCache` en `retrieval/cache.py`, inyectado por el campo `cache` que ya existía; `create_app` lo construye una vez; el router **resuelve**, no construye |
| D12 · `score` cambia de escala y se declara | `normalised_scores`; declarado en el README de `ai-service` como cambio de comportamiento numerado |
| D13 · Una capacidad, tres módulos | `fusion.py` sin imports de dominio ni de base de datos, `filters.py` como costura de C25, `lexical.py` con el SQL |

---

## 6. Suite de frontend, comparada por nombres

`vitest` sale con 0 al canalizar la salida y la suite **arranca en rojo**, así que el recuento no dice nada. La comparación se hizo por **nombres de test fallido**, midiendo la línea base sobre el árbol con `git stash` y restaurándolo después.

| Medición | Fallos | Tests |
|---|---:|---:|
| Línea base (árbol sin C21) | **113** | 552 |
| Con C21 | **113** | 568 |

**Fallos nuevos introducidos por C21: 0.** Y ninguno de los 113 dejó de fallar, que también se comprueba: un cambio en ese conjunto sería una señal aunque fuese hacia el verde.

Los 16 tests añadidos (14 del componente + 2 del panel) pasan.

| Comprobación | Resultado |
|---|---|
| `npm run build` | **verde**, 23,9 s |
| `npx tsc --noEmit`, filtrado a los ficheros propios | **sin errores**. Sin filtrar arrastra los errores preexistentes de las plantillas Metronic, que `CLAUDE.md` documenta y que no son puerta |

---

## 7. Verificado a mano

- `python -m jbg_ai.retrieval compare` sin perfil cargado → `skipping measurement: settings are not loadable: …`, **exit 0**. La ayuda de desarrollo no puede convertirse en una puerta que falla en un portátil sin Docker, que es la regla que C20 estableció para `measure`.
- Línea base de pytest medida de verdad: `git checkout HEAD~1` → **510 passed** → vuelta a la rama, árbol limpio. Coincide exactamente con la cifra que dejó el `qa.md` de C20, así que nada se movió entre medias.
- El `stage=fuse` se leyó a mano en la salida de `caplog` para confirmar que los campos existen y no sólo que el test los busca: `typed=1 expanded=1 vector=1 fused=1 branches=lexical+vector cross_branch=1 returned=1 low_confidence=False k=60 depth=60`.
- El commit `3965cc3` se verificó con `git status --short` vacío después, para descartar ficheros generados sin querer.

---

## 8. Documentación de contexto

| Documento | Qué se alineó |
|---|---|
| `ai-service/README.md` | Párrafo C21 en la lista de changes; **cinco filas nuevas** en la tabla de entorno; los dos cambios de comportamiento declarados y numerados (`score` cambia de escala y no es comparable con lo persistido antes; el umbral de distancia no discrimina); y dos líneas de estado que habían quedado obsoletas — «vector only until C21» en los non-goals y la lista de etapas de log |
| `Documentos/epicas.md` | C21 pasa de «en curso» a «implementado» en el bloque de EP14, en la lista de historias y en la tabla de cobertura; se precisa el alcance de `low_confidence` |
| `openspec/DEFERRED_TASKS.md` | El paso 1 de la deuda queda **pagado** y tachado, con la explicación de por qué no eran las tres líneas que la nota suponía; los pasos 2-4 siguen abiertos y se nombran las cifras a batir |
| `tasks.md` | 36/37; la 4.6 se precisó y se añadió la 7.3 al aparecer trabajo que las tareas originales no cubrían |

---

## 9. Incidencias de esta pasada

### 9.1. La forma segura tenía que salir de `measure.py` sin arrastrar su semántica

La tarea 1.1 pide mover la composición segura fuera de `measure.py`. Moverla entera habría cambiado el `&&` del informe de alcance de C20 por el `||` de C21, y ese informe dejaría de ser comparable **consigo mismo**. La composición por grupos vive ahora en `lexical.py` y `measure.py` la importa, pero **decide su propio unión**: conjunción para medir alcance, disyunción para servir. El motivo está escrito en el docstring de `compose_tsquery`, donde está la tentación.

### 9.2. Tres estilos de parámetro para la misma consulta

SQLAlchemy quiere `:nombre`, psycopg con nombre quiere `%(nombre)s` y la medición de C20 usa `%s` posicional. La primera versión indexaba los parámetros por el **texto** del placeholder, que se rompe en cuanto un fragmento aparece dos veces —y aparece: la expresión de coincidencia va en el `SELECT` (dentro de `ts_rank`) y otra vez en el `WHERE`—. Corregido moviendo el **nombre** a `lexical.py` (`term_name`), de forma que el llamante sólo decide cómo se renderiza. Con nombres, un fragmento repetido liga el parámetro una vez.

### 9.3. Un test existente prohibía la palabra `price` en el SQL

`test_search_sql_does_not_use_pos_id_as_a_predicate` afirmaba `"price" not in sql`. C21 **necesita** seleccionar `price` para degradar con él, y la tarea 5.4 pide exactamente «ningún **predicado** de precio». El test se dividió: uno comprueba `pos_id` / `public.` / `stock`, y `test_neither_branch_carries_a_price_or_stock_predicate` mira sólo las líneas que empiezan por `AND` / `WHERE` / `OR`. Seleccionar no es excluir, y ahora el test dice cuál de las dos cosas prohíbe.

### 9.4. `overfetch` renombrado a `depth` en el puerto

La spec exige que la profundidad de rama y la ventana de over-retrieval sean parámetros distintos aunque coincidan en 60. Mantener el nombre `overfetch` para lo que ahora es la profundidad habría dejado el código diciendo lo contrario de la spec.

### 9.5. Tres premisas mías eran falsas y el código tenía razón

Vale la pena registrarlas porque las tres son errores de razonamiento, no de implementación:

| Lo que asumí | Lo que pasa |
|---|---|
| Con `branch_depth=3` vuelven 3 resultados | Vuelven hasta **9**: tres listas de tres pueden nombrar nueve productos distintos |
| `anillo de plata` no extrae ningún filtro estructural | Extrae `materials=plata`, que es justo lo que la spec pide. La prueba de «no se inventa un filtro» necesitaba una consulta sin material, `anillo` |
| Con peso vectorial 5,0 gana el candidato sólo vectorial | No: la ventaja de RRF es por **rango**, no por escala, y el candidato de las dos ramas seguía sumando más. Se demuestra mejor poniendo los pesos léxicos a 0 |

### 9.6. `low_confidence` marcaba todas las respuestas de una sola rama

**Detectado en revisión, después de la primera pasada verde.** Con la regla de consenso aplicada sin condición, en `mode=lexical`, en `mode=vector` y en un `hybrid` degradado por caída del proveedor ningún candidato puede aparecer en dos listas, así que `low_confidence` salía **true siempre**. Un campo que vale siempre lo mismo no informa de nada: es el mismo defecto que la constante `["vector"]` que este change elimina.

Corregido: la señal de desacuerdo se aplica **sólo cuando corrieron dos ramas**; con una sola conserva el significado de C14, «no se devolvió nada». `stage=fuse` emite `branches=` para poder leer la marca contra cómo se calculó. Se actualizaron los tres deltas afectados —`hybrid-fusion` con tres escenarios nuevos, `vector-retrieval` con uno y una cláusula, `assisted-search-panel` con un requisito nuevo— porque el arreglo cambia lo que la spec promete, no sólo el código.

De ahí salió también el hueco del frontal: una respuesta servida sólo por la rama léxica llega con 200, resultados en pantalla y `aiAvailable` **true**, así que era **invisible**. Ahora el panel lo dice, derivándolo de la procedencia de los resultados en vez de un campo nuevo, que habría movido el contrato.

### 9.7. Un fixture del panel describía un estado imposible

`assisted.test.tsx` construía el caso degradado con `aiAvailable: false` y `matchReasons: ['vector']` a la vez. El sistema no produce eso: sin ruta asistida no hay procedencia. Mientras la insignia se decidía por respuesta daba igual; al decidirse por resultado, deja de dar igual. El fixture pasa a `matchReasons: []`.

---

## 10. Fuera de esta pasada

- **Tarea 8.5**, la única sin marcar: correr el CLI de medición contra el índice local para reproducir `sortija de plata` 4/10 → 10/10 y `criollas de oro` 1/10 → 6/10, y medir la latencia del pipeline en frío y en caliente. El propio ticket la define como **verificación posterior al merge y no como puerta**, y necesita PostgreSQL con los 1.168 documentos y el proveedor real, ninguno de los dos disponible en esta pasada. El CLI existe (`python -m jbg_ai.retrieval compare`) y salta limpio sin ellos.
- Revertir `AiGateway:RetrievalTimeoutMs` de 2500 a 800 ms: pide despliegue en demo, remedición en frío y en caliente y confirmación por el log del embudo. Sigue abierto en `DEFERRED_TASKS.md` con las cifras a batir.
- Recalibrar el umbral de distancia: haría falta un cuantil por consulta y no una constante. Declarado como limitación, reclamado por la ficha de C25.
- Señales de negocio (C22, C25), corpus de conocimiento (C23), golden set graduado (C24), substitutes (C26).
- `dotnet test`: C21 no toca `backend/`.

---

## 11. Tarea 8.5, ejecutada contra el índice local

Dejó de ser verificación pendiente: se ejecutó el 2026-09-02 contra los 1.168 documentos vivos y el proveedor real.

### 11.1. ¿Hacía falta re-embeber tras C20?

**No**, comprobado por dos vías independientes antes de medir nada.

Por código: `git log` sobre lo que alimenta el texto indexado — `indexing/source_text.py`, `indexing/constants.py` y `enrichment/vocabularies.yaml` — no muestra ningún cambio de C20. El diff de C20 (`74a7451`) no toca `indexing/` en absoluto: es enteramente del lado de la consulta.

Por índice, que es lo que decide:

| Comprobación | Valor |
|---|---|
| Filas totales / activas | 1168 / 1168 |
| Activas con `embedding` | **1168** |
| Activas con `tsv` | **1168** |
| Compatibles con el `model_version_key` vivo | **1168** |
| Activas cuya `embedding_version` difiere del `document_version_key` vivo | **0** |
| `indexed_at` más reciente | 2026-08-31 22:09 UTC |

Una sola versión almacenada, `openai/text-embedding-3-small:1536:source-text/v1`, idéntica a la viva. Bastó una pasada.

### 11.2. Comparación de configuraciones

`python -m jbg_ai.retrieval compare`, informe versionado en [`ai-service/evals/results/c21-fusion-configuration-comparison.md`](../../../../ai-service/evals/results/c21-fusion-configuration-comparison.md). **24 consultas**: las 12 curadas de C20 más las **12 grabadas** de `public."ProductSearchEvents"`.

| configuración | aciertos |
|---|---:|
| vector-only | 157/240 |
| lexical-only | 219/240 |
| **fused-default** | **224/240** |

El orden de los tres brazos reproduce lo medido en la exploración, y **la fusión gana a las dos ramas por separado**. El caso más claro es `pendientes de oro con piedra azul`: 3 → 6 → **9**.

**Lo que el ticket pedía confirmar, y lo que salió:**

| Consulta | Objetivo del ticket | Medido |
|---|---|---|
| `sortija de plata` | 4/10 → 10/10 | **4/10 → 10/10** ✅ exacto |
| `criollas de oro` | 1/10 → 6/10 | 1/10 → **5/10** ⚠️ un punto corto |

El primero reproduce exactamente. **El segundo no**, y no lo redondeo: la rúbrica de este CLI se deriva automáticamente de los términos que la expansión resuelve (`pendientes` + `oro`), mientras que la de la exploración se curó a mano por consulta. Con `criollas` resolviendo a `pendientes`, un resultado que sea unos pendientes de plata no cuenta, y la exploración pudo puntuar de otro modo. Los totales absolutos también se separan por lo mismo — vector-only 58/120 aquí frente a 67/120 allí sobre las mismas 12 curadas.

**La conclusión no cambia y la dirección se sostiene en las 24 consultas**, pero el número exacto de `criollas de oro` queda como discrepancia declarada. Quien la persiga tiene el brazo y la rúbrica en el código; el juez de verdad es el golden set graduado de C24, que es exactamente lo que la ficha dice.

`brazalete de cuero` sale 0/0/0 en los tres brazos, que es honesto y no un fallo: `cuero` tiene un producto en todo el catálogo, como C20 ya documentó.

### 11.3. Latencia del pipeline completo, en frío y en caliente

Seis consultas de operador, pipeline entero (expansión, dos listas léxicas, embedding, rama vectorial, fusión, filtros que degradan), con el singleton de C21 y su caché acotado de 512 entradas.

| | mín | media | máx |
|---|---:|---:|---:|
| **En frío** (primera vez que se ve el texto) | 273 ms | 475 ms | **1328 ms** |
| **En caliente** (acierta el caché del singleton) | **74 ms** | **76 ms** | 78 ms |

**El singleton hace lo que la deuda decía que haría.** 76 ms de media en caliente es un orden de magnitud por dentro del presupuesto de 800 ms, frente a los 170-383 ms que medía el entorno de demostración *antes* de que existiera. El caché elimina por completo la ida y vuelta al proveedor en un texto repetido.

**Lo que no elimina es la primera llamada de cada texto distinto**: 1328 ms en `criollas de oro`, coherente con los 1707 ms medidos en demo. Cinco de seis consultas en frío caben en 800 ms; seis de seis en caliente.

Las 24 respuestas devolvieron 30 candidatos (`over_retrieval_count(10)`), con entre 4 y 25 candidatos vistos por **las dos** ramas, así que `low_confidence` fue false en todas: la fusión está fusionando de verdad y no sirviendo una rama disfrazada.

`DEFERRED_TASKS.md` recoge estas cifras como la línea base que decidirá los 800 ms. La decisión sigue abierta a propósito: esto es un portátil contra una base local, no el entorno de demostración.

### 11.4. Tres defectos que sólo aparecieron al ejecutarlo

Los tres estaban en código que la suite daba por bueno, porque la suite corre sin base de datos y sin proveedor — que es precisamente su virtud y su límite.

| # | Defecto | Corrección |
|---|---|---|
| 1 | `compare` construía `Settings()`, que exige `APP_ENV`, `SERVICE_VERSION` y `JWT_SECRET`. `backend/.env` sólo tiene las claves `JPV_*`, así que **el CLI saltaba precisamente en la única máquina capaz de ejecutarlo** | `ComparisonConfig.from_env()`: lee lo que usa y nada más, con `FUSION_DEFAULTS` de respaldo. Misma regla que `measure` |
| 2 | Un fallo del proveedor reventaba con traceback en vez de saltar: litellm lanza su propia jerarquía (`InternalServerError`), que no es `EmbeddingError` | Se captura cualquier excepción del proveedor y se convierte en `MeasurementUnavailable` |
| 3 | **El peor.** La consulta de telemetría usaba `"QueryText"`; la columna real es `"SearchText"`. El `except` mudo devolvía tupla vacía, así que el informe **decía cubrir las consultas grabadas sin haber leído ninguna** | Nombre corregido y el fallback dejó de ser mudo: ahora devuelve el motivo y lo escribe en el informe, para que un conjunto vacío no pueda hacerse pasar por uno completo |

El tercero es la firma que este proyecto persigue desde C17: algo que aparenta funcionar y no se ejecuta. El primer informe generado tenía doce consultas y parecía completo.

### 11.5. Dos obstáculos del entorno, que no son del servicio

- **TLS.** `Norton Web/Mail Shield` intercepta la conexión con su propia raíz. El almacén de Windows la acepta, pero `httpx` —que es lo que litellm usa— va contra el bundle de `certifi`, que no la tiene, y el proveedor falla con `Connection error`. Es la misma causa que la nota de `--system-certs` de `CLAUDE.md`, que sólo cubre `uv`. Resuelto para la medición exportando `SSL_CERT_FILE` a un bundle de `certifi` más los 131 certificados del almacén de Windows.
- **Bucle de eventos.** `psycopg` en modo async no funciona con el `ProactorEventLoop`, el de Windows por defecto. `uvicorn` fija el suyo, así que esto sólo afecta a un arnés de medición fuera del servidor; se resuelve con `WindowsSelectorEventLoopPolicy`.

Ninguno de los dos es un defecto del servicio, y ambos quedan aquí porque son lo que costará repetir la medición.

---

## 12. Hallazgos del `/opsx:verify`, cerrados

| # | Hallazgo | Corrección |
|---|---|---|
| W1 | La constante de suavizado **sí** estaba escrita en el código: `DEFAULT_RRF_K = 60` y `DEFAULT_BRANCH_DEPTH = 60` en `fusion.py`, y el guardián sólo escaneaba los pesos, así que una `k` cableada no la detectaba nadie | Constantes eliminadas y `k`/`depth` pasan a ser argumentos **obligatorios**. La guarda se amplía sobre la firma (`inspect.signature`), no sobre el texto, para que el razonamiento medido pueda seguir en la prosa |
| W2 | `low_confidence` significaba dos cosas en la misma traza: en `stage=search` la rama vectorial vacía, en `stage=fuse` la marca de la respuesta. **Y divergen de verdad**: una rama vectorial sana cuyos candidatos la léxica no vio da `False` en una y `True` en la otra | Renombrado a `vector_empty` en el log de búsqueda, con el requisito de `vector-retrieval` corregido —que es el origen del nombre— y un escenario nuevo |
| W3 | El escenario *The groups reach the lexical query* estaba cubierto a medias: el test comprobaba que se emiten las dos peticiones, no que la expandida alcance lo que la tecleada no. **Era una sobreafirmación de este mismo documento** | `test_the_expansion_finds_what_the_typed_form_alone_would_miss`: documento que dice `anillo`, operador que escribe `sortija`, y la misma consulta sin expansión devolviendo cero |
| S1 | «Embedding vectors MUST NOT be logged at Information» era cierto por construcción y no lo fijaba nadie | `test_embedding_vectors_are_never_logged_at_information` |
| S2 | La otra mitad de D10 —que las dos listas léxicas van secuenciales para retener **una** conexión del pool— sólo la sostenía un comentario | `test_only_one_lexical_query_is_in_flight_at_a_time`, con un fake que cuenta consultas en vuelo |

**Las cinco guardas se mutaron una a una y las cinco muerden**: default restaurado en `fuse`, nombre del campo revertido, lista expandida sustituida por la tecleada, vector añadido al log de embed, y las dos léxicas puestas en `asyncio.gather`. Ninguna pasó con la mutación puesta.

Dos veces durante el cierre una premisa mía fue falsa y el código tenía razón, y las dos quedan en el registro: el caso en que las dos `low_confidence` divergen es el contrario del que escribí primero, y el comentario del código lo decía mal hasta que el test lo corrigió.

---

## Veredicto

**Sin problemas críticos.** `uv run --system-certs pytest` **598 passed, 0 failed** sobre una línea base medida de **510**, sin abrir un socket a proveedor, LLM ni RDS. `openspec validate --all --strict` **49 passed, 0 failed**. Snapshot OpenAPI verde **sin** regenerar, y diffs vacíos en `backend/`, `openapi.json`, `embeddings.py` y `vocabularies.yaml`. `npm run build` verde y la suite de frontend con **cero fallos nuevos** comparada por nombres contra su línea base roja documentada. 77/77 escenarios con test o comprobación nombrada, 30/30 nombres exigidos por `tasks.md`, **38/38 tareas**, y los 6 hallazgos del verify cerrados con sus guardas mutadas.

**Listo para archivar.** La 8.5 se ejecutó: la fusión mide **224/240** frente a 157/240 de la rama vectorial sola, `sortija de plata` reproduce exactamente el 4/10 → 10/10 del ticket, `criollas de oro` se queda en 5/10 contra los 6/10 esperados —discrepancia declarada en §11.2, no redondeada—, y el singleton lleva la latencia en caliente a **76 ms**.
