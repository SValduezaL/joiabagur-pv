# QA — C22 `add-pos-projection-soft-prefilter`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** 2026-09-05 · **Rama:** `c22-add-pos-projection-soft-prefilter` · **Commit de artefactos:** `8dc7f39` · **Commit de implementación:** `c2af1da`
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **47/47 tareas**. Las de la §9 (medición) se ejecutaron contra el feed real servido por la API .NET local; ver §8.
> **Desviación de artefactos:** este change **abre una revisión de Alembic** contra lo que declaraban cinco documentos. La decisión, su fundamento y las enmiendas están en §9.1.
> **Seguimiento verify:** misma fecha. 1 CRITICAL, 2 WARNING y 3 SUGGESTION, **todas cerradas**; ver §13.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| PostgreSQL | 15.19 con `vector` 0.8.6 (`jpv-pv-postgres`, puerto 5433) para la base local; testcontainers `pgvector/pgvector:pg15` para los tests `db` |
| .NET | 10.0 · suite completa ejecutada dos veces con logger TRX, comparada **por nombres** |
| Contrato | `ai-service/openapi.json` **se regenera**, deliberadamente, con la receta del README. Ver §6 |
| Freeze C11 | `git diff -- ai-service/src/jbg_ai/indexing/embeddings.py` **vacío**, y fijado por hash en `test_embeddings_module_is_unchanged` |
| Vocabulario C09 | `git diff -- ai-service/src/jbg_ai/enrichment/vocabularies.yaml` **vacío** |
| Proveedor de embeddings | **No se llama en ningún test.** Las sondas de la §8 usan vectores ya persistidos en el índice |
| Docker | **Exigido** para los tests marcados `db` (esquema y repositorio SQL); el resto corre con fakes |

---

## 1. Suites automáticas

La línea base se midió **de verdad**, sobre el árbol limpio en `8dc7f39`, antes de tocar una línea de código.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`8dc7f39`, sólo artefactos) | **598 passed**, 0 failed, 45,7 s |
| `ai-service` al cerrar los grupos 1-8 | **683 passed**, 0 failed |
| `ai-service` al cerrar la §10 | **689 passed**, 0 failed, 56,6 s |
| `ai-service` tras cubrir el escenario que faltaba (§3.1) | **691 passed**, 0 failed, 40,2 s |
| `ai-service` tras cerrar los hallazgos del verify (§13) | **697 passed**, 0 failed, 40,7 s |
| **Línea base** `dotnet test` (`8dc7f39`) | **52 fallos** de 973 — rojo preexistente documentado en `CLAUDE.md` |
| `dotnet test` tras la implementación | **53 fallos** de 983 — ver §2 |
| `openspec validate add-pos-projection-soft-prefilter --strict` | *valid* |
| `openspec validate --all --strict` | **50 passed, 0 failed** |

**+99 tests** de Python sobre la línea base (598 → 697) y **+11** de .NET (973 → 984).

> El recuento **sí es fiable** en `ai-service`: parte de cero fallos y no llama a proveedores ni a RDS. En `backend/` **no lo es**, y la comparación se hace por nombres en §2.

### Desglose de tests nuevos o ampliados

| Fichero | Antes → Después | Qué cubre |
|---|---|---|
| `tests/retrieval/test_pos_scope.py` | 0 → **34** | Claim malformado en seis formas; scope aplicado a las tres ramas y tomado del token y nunca del body; fila en borrado blando fuera de alcance; profundidad completa bajo scope; degradación por stock que nunca elimina; restricción tecleada por encima del stock; `1-2` y `3+` sin ordenar entre sí; frescura desde el checkpoint y con caché; 503 en vacío; degradación en obsoleto con log; techo configurable por llamada; flag que restaura el comportamiento anterior; barrido en un proceso; `stage=projection` y cardinalidad escopada; ningún vector en logs; **cifras de venta ilegibles desde el pipeline** |
| `tests/indexing/test_pos_projection.py` | 0 → **21** | Mapeo camelCase del feed POS; par que nunca vendió; seis buckets fuera de vocabulario rechazados al parsear; `kind` desconocido; `computed_as_of` que viaja y que puede faltar; idempotencia; **borrado blando que conserva la historia**; tombstone de par desconocido que inserta; reasignación que devuelve la fila al alcance; el `CHECK` del esquema rechazando lo que el parser rechaza |
| `tests/indexing/test_pos_orchestrator.py` | 0 → **15** | Precedencia del cursor; cursor de agotamiento; reanudación frente a `--full`; seguimiento de `nextCursor`; **la fila `catalog` del checkpoint intacta**; página fallida registrada sin abortar el resto y **sin adelantar el marcador**; CLI con `--full`; contadores sin contenido de fila; ausencia de ruta `/v1` y de planificador |
| `tests/migrations/test_c22_schema.py` | 0 → **5** | La columna existe, es anulable y sin default; fila sin instante aceptada; **el resto de la tabla intacto**; reversibilidad `upgrade`/`downgrade`/`upgrade` |
| `tests/api/test_retrieval_projection.py` | 0 → **7** | 503 y no lista vacía; `/health` en 200 con proyección vacía y con obsoleta; 422 por claim malformado; edad reportada; página posiblemente corta con 200; **el contrato comprometido lleva el campo** |
| `tests/retrieval/test_filters.py` | 15 → **21** | Clave de orden de cuatro componentes con stock el último; bucket ausente ≠ bucket cero; los dos buckets no nulos empatan; el stock sólo decide entre iguales; `demote` reordena por stock aunque no haya regla; nada se elimina |
| `tests/support/` | — | `fake_pos_projection.py` (in-memory que **replica el `CHECK`**), `async_db.py` (un solo bucle por escenario, selector en Windows), `fake_product_search.py` gana proyección, scope y `qty_bucket` |
| **.NET** `IndexFeedSalesClockTests.cs` | 0 → **5** | Instante configurado que ancla las ventanas; ausencia que cae al reloj de pared; página que declara `computedAsOf` con y sin configuración y **también sin upserts**; catálogo intacto |
| **.NET** `IndexFeedRegistrationTests.cs` | 5 → **10** | Opción ausente que no cambia nada; **binding de `Z` que da el instante que se quiso**; valor sin offset que para el arranque; normalización idempotente |
| **.NET** `AiIndexFeedPosTests.cs` | 4 → **5** | Nuevo test de `computedAsOf`; el de ventanas de venta **anclado al instante** en vez de a `UtcNow` (§9.3) |

---

## 2. Suite de .NET, comparada por nombres

`CLAUDE.md` avisa de que el recuento no es fiable. No me limité a citarlo: lo **reproduje**.

| Medición | Resultado |
|---|---|
| Línea base (`8dc7f39`, TRX) | 52 nombres fallando de 973 |
| Tras la implementación (TRX) | 53 nombres fallando de 983 |
| Diferencia por nombres | **7 aparecen, 6 desaparecen** |

Los 7 «nuevos» son todos `DbUpdateException` → **`22001: value too long for type character varying(20)`**, que es literalmente la trampa que `CLAUDE.md` documenta: el teléfono que genera Bogus no siempre cabe en `PointOfSale.Phone`. Es **aleatorio por ejecución**.

**La prueba decisiva:** ejecuté dos veces las dos clases que rotan (`InventoryIntegrationTests`, `ReturnsControllerTests`) sobre **el mismo binario, con `--no-build`**:

| Ejecución | Fallos |
|---|---|
| Pasada 1 | 11 de 45 |
| Pasada 2 | 13 de 45 |
| **Nombres que difieren entre las dos** | **10** |

Diez nombres de diferencia sin cambiar una línea, frente a los siete entre línea base y after. La rotación observada es **menor** que el ruido del propio banco.

**Lo que sí es señal**, y está en verde:

| Clase que C22 toca | Tests | Resultado |
|---|---|---|
| `AiIndexFeedCatalogTests` · `AiIndexFeedPosTests` · `AiIndexFeedAuthTests` | 22 | ✅ |
| `IndexFeedRegistrationTests` | 9 | ✅ |
| `IndexFeedSalesClockTests` | 5 | ✅ |
| `IndexFeedAggregateHashTests` | 4 | ✅ |
| `IndexFeedKeyComparerTests` | 6 | ✅ |
| `AiContractSnapshotTests` | 15 | ✅ |
| **Fallos dentro del radio del cambio** | | **0** |

---

## 3. Escenarios de las specs, uno a uno

**36 escenarios `#### Scenario:`** en los cuatro deltas: `pos-projection` 22, `index-feed` 6, `vector-retrieval` 5, `product-document-indexer` 3. Todos tienen test nombrado. El sexto de `index-feed` lo añadió el verify (§13.3).

### `pos-projection` (22)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Drenaje por CLI · Draining the POS feed populates the projection | `test_a_drain_writes_the_page_and_stores_its_own_checkpoint` · `test_applying_the_same_page_twice_does_not_duplicate` · `test_upsert_is_idempotent_and_stores_the_reference_instant` | ✅ |
| Drenaje por CLI · The projection stores a bucket and never the exact quantity | `test_a_bucket_outside_the_vocabulary_is_rejected_while_parsing` (6 casos) · `test_the_schema_refuses_a_bucket_outside_the_vocabulary` · `test_no_bucket_reaches_the_response` | ✅ |
| Drenaje por CLI · The only schema change is one additive nullable column | `test_the_revision_touches_nothing_else` · `test_computed_as_of_is_nullable_and_has_no_default` | ✅ |
| Checkpoint propio · A second run resumes instead of restarting | `test_a_second_run_resumes_instead_of_restarting` | ✅ |
| Checkpoint propio · A full run ignores the stored cursor | `test_full_ignores_the_cursor_the_previous_run_stored` · `test_a_full_run_ignores_a_stored_cursor` | ✅ |
| Tombstone · Unassignment keeps the row and flips the hint | `test_a_tombstone_soft_deletes_and_keeps_the_history` (SQL real) | ✅ |
| Tombstone · A tombstone for an unknown pair inserts the soft-deleted row | `test_a_tombstone_for_an_unknown_pair_inserts_the_soft_deleted_row` | ✅ |
| Alcance · Candidates come only from the point of sale's assortment | `test_candidates_come_only_from_the_assortment` · `test_the_scope_is_applied_to_every_branch` | ✅ |
| Alcance · A soft-deleted assignment is out of scope | `test_a_soft_deleted_assignment_is_out_of_scope` | ✅ |
| Alcance · A malformed point of sale claim never widens the search | `test_a_malformed_claim_never_produces_an_unscoped_search` · `test_a_malformed_pos_id_claim_is_422` (HTTP) · `test_no_claim_shape_short_of_a_uuid_is_accepted` (6 formas) | ✅ |
| Disponibilidad · An out-of-stock product is demoted, not removed | `test_out_of_stock_product_is_penalised_not_removed` · `test_demote_keeps_every_candidate_inside_the_window` | ✅ |
| Disponibilidad · A typed constraint outranks the stock signal | `test_a_typed_constraint_outranks_the_stock_signal` · `test_stock_only_decides_between_candidates_the_typed_blocks_rank_equally` | ✅ |
| Disponibilidad · The two non-zero buckets are not ordered against each other | `test_the_two_non_zero_buckets_are_not_ordered_against_each_other` · `test_the_two_non_zero_buckets_rank_identically` | ✅ |
| Frescura · Freshness reflects the last synchronisation, not the last change | `test_freshness_reflects_the_last_synchronisation_not_the_last_change` · `test_the_age_is_read_through_a_cache` | ✅ |
| Frescura · The regenerated contract is committed | `test_the_committed_contract_carries_the_new_field` · `test_openapi_snapshot_is_stable` | ✅ |
| Guardias · An unsynchronised projection is 503 and not an abstention | `test_an_unsynchronised_projection_is_503_and_not_an_abstention` · `test_an_empty_projection_is_503_and_not_a_successful_empty_list` · `test_health_stays_200_when_the_projection_is_empty` | ✅ |
| Guardias · A stale projection stops filtering instead of hiding products | `test_a_stale_projection_stops_filtering_instead_of_hiding_products` · `test_a_stale_projection_logs_the_degradation` · `test_a_stale_projection_answers_200_with_a_possibly_short_page` · `test_health_stays_200_when_the_projection_is_stale` | ✅ |
| Flag · Disabling the prefilter restores the previous behaviour | `test_disabling_the_prefilter_restores_the_previous_behaviour` · `test_resolve_scope_skips_every_query_when_disabled` | ✅ |
| Flag · A sweep overrides the default without restarting | `test_a_sweep_overrides_the_default_without_restarting` · `test_the_flag_is_not_part_of_the_request_contract` | ✅ |
| Observabilidad · Every scoped retrieval records what the scope admitted | `test_the_projection_stage_reports_what_the_scope_admitted` · `test_the_search_stage_reports_the_scoped_cardinality` · `test_no_vector_reaches_the_logs` · **y el drenaje**: `test_every_drain_log_entry_carries_a_trace_id` (§13.1) | ✅ |
| Ventas · Sales figures are persisted without influencing the ranking | `test_the_retrieval_path_cannot_read_the_sales_figures` · `test_sales_figures_do_not_change_the_order` · `test_upsert_is_idempotent_and_stores_the_reference_instant` | ✅ (§3.1) |
| Suite offline · The offline suite makes no external call | Toda `tests/retrieval/` inyecta fakes; los `db` usan PostgreSQL efímero y **saltan** si Docker no responde | ✅ |

### `index-feed` (5)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Feed POS · The feed returns a bucket not an exact quantity | `PosAvailabilityFeed_ReturnsBucketNotExactQuantity` (existente, sigue verde) | ✅ |
| Feed POS · A configured reference instant anchors the sales windows | `SalesAggregates_WithConfiguredAsOf_CountWindowsAgainstIt` · `PosAvailabilityFeed_SalesWindows_DoNotSubtractReturns` (reanclado) | ✅ |
| Feed POS · Without configuration the clock is the current time | `SalesAggregates_WithoutAsOf_FallBackToWallClock` · `AddIndexFeed_WithNoSalesAsOf_LeavesTheWallClockInCharge` | ✅ |
| Feed POS · Unassignment emits a tombstone | `PosAvailabilityFeed_Unassigned_EmitsTombstone` (existente) | ✅ |
| Feed POS · The POS page cap is 200 and is not copied to UI lists | `PosAvailabilityFeed_PageSize_Is200` (existente) | ✅ |
| Feed POS · A sale after the reference instant does not move the last-sale timestamp | `PosAvailabilityFeed_SaleAfterTheReferenceInstant_DoesNotMoveLastSaleAt` (§13.3) | ✅ |

`computedAsOf` en la página se fija además con `PosAvailabilityPage_DeclaresComputedAsOf`, `PosAvailabilityPage_DeclaresComputedAsOf_EvenWithNoUpserts` y `PosAvailabilityFeed_DeclaresTheClockItCounted_Against` (extremo a extremo por HTTP).

### `vector-retrieval` (5)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Over-retrieval · Overfetch is capped after fusion | `test_overfetch_is_capped_after_fusion` (existente) | ✅ |
| Over-retrieval · Overfetch does not refill from rows above the threshold | existente, sigue verde | ✅ |
| Over-retrieval · Branch depth does not follow the requested page size | `test_branch_depth_does_not_follow_the_requested_page_size` | ✅ |
| Over-retrieval · Token pos_id is echoed and body pos_id is ignored | `test_the_scope_comes_from_the_token_and_never_from_the_body` · `test_body_pos_id_is_ignored` | ✅ |
| Over-retrieval · The scoped branch still returns its full depth | `test_the_scoped_branch_returns_its_full_depth` | ✅ |

### `product-document-indexer` (3)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Cliente reutilizable · POS feed is not called during catalog sync | `test_catalog_sync_does_not_call_pos_feed` (existente) | ✅ |
| Cliente reutilizable · The two drains do not share a checkpoint | `test_the_catalog_checkpoint_row_is_never_touched` | ✅ |
| Cliente reutilizable · embeddings.py stays frozen | `test_embeddings_module_is_unchanged` (hash SHA-256) · `git diff` vacío | ✅ |

### 3.1. Un escenario que no tenía test, y se le puso

Al montar esta tabla descubrí que **«Sales figures are persisted without influencing the ranking» no tenía ninguna comprobación nombrada**. Estructuralmente era cierto —ni `SearchHit`, ni `LexicalHit`, ni `_Candidate` llevan campo de ventas— pero «es cierto por cómo quedó el código» no es lo mismo que «está fijado». Se añadieron dos tests antes de escribir esta sección, no después:

- `test_the_retrieval_path_cannot_read_the_sales_figures`: ningún tipo de hit declara `sales_*` ni `last_sale_at`, y ni `orchestrator.py`, ni `filters.py`, ni `fusion.py` los mencionan en su fuente.
- `test_sales_figures_do_not_change_the_order`: dos candidatos que la fusión empata mantienen el orden fusionado.

---

## 4. Nombres exigidos por `tasks.md`

| Tarea | Nombre exigido | Existe |
|---|---|---|
| 2.5 | `SalesAggregates_WithConfiguredAsOf_CountWindowsAgainstIt` | ✅ |
| 2.5 | `SalesAggregates_WithoutAsOf_FallBackToWallClock` | ✅ |
| 2.5 | `PosAvailabilityPage_DeclaresComputedAsOf` | ✅ |
| 6.3 | `test_out_of_stock_product_is_penalised_not_removed` | ✅ |

El nombre de la 6.3 es el que D1 **renombró** desde el `test_unassigned_product_is_penalised_not_removed` de la ficha: con `is_assigned_hint` como filtro duro, el producto desasignado sí se excluye —igual que hace `Carried()` en .NET— y lo que degrada sin eliminar es el stock. El test protege el principio que está realmente en vigor.

---

## 5. Alcance negativo

```bash
git status --short -- frontend/ terraform/ .github/ \
  ai-service/src/jbg_ai/indexing/embeddings.py \
  ai-service/src/jbg_ai/enrichment/vocabularies.yaml \
  backend/src/JoiabagurPV.Infrastructure/Migrations
```

Salida **vacía**, comprobada antes y después del commit.

| Guardarraíl | Comprobación | Resultado |
|---|---|---|
| `indexing/embeddings.py` | `git diff` vacío **y** hash SHA-256 en `test_embeddings_module_is_unchanged` | ✅ |
| `enrichment/vocabularies.yaml` | `git diff` vacío | ✅ |
| `frontend/` · `terraform/` · `.github/workflows/` | `git diff` vacío | ✅ |
| **Migración de EF Core** | ninguna: `backend/…/Migrations` intacto | ✅ |
| **Revisión de Alembic** | **exactamente una**, aditiva (`c9a71f2b6d54`), fijada por `test_the_revision_touches_nothing_else`. Ver §9.1 | ⚠️ declarado |
| Ruta `/v1` nueva | `test_no_v1_route_and_no_scheduler_were_added` recorre `openapi()["paths"]` | ✅ |
| Planificador en proceso | el mismo test prohíbe `create_task`, `BackgroundTasks`, `APScheduler` y `add_event_handler` en el fuente del orquestador POS | ✅ |
| Esquema `public` desde Python | ninguna sentencia del servicio lo lee; el drenaje sólo escribe `ai.*` | ✅ |
| `AiGateway:RetrievalTimeoutMs` | sigue en **2500 ms** | ✅ |
| `ai.query_log` | no existe; se emiten etapas de log en su lugar | ✅ |
| Fila `catalog` del checkpoint | `test_the_catalog_checkpoint_row_is_never_touched` verifica watermark, `indexed_count` y hash | ✅ |
| Stock exacto en la respuesta | `test_no_bucket_reaches_the_response`: ni `qty_bucket` ni `3+` aparecen en el `model_dump()` | ✅ |

---

## 6. El contrato, movido a propósito

`ai-service/openapi.json` se regenera **por primera vez desde C13**, con la receta del README y nunca a mano.

```
 ai-service/openapi.json | 13 +++++++++++++
 1 file changed, 13 insertions(+)
```

Un solo campo opcional en `RetrievalResponse`. **Compatible hacia atrás**, y no de palabra: `AiContractSnapshotTests.Dtos_MatchCommittedOpenApiSchema` barre **de .NET hacia el contrato** —exige que cada propiedad .NET exista en el schema, no al revés— así que un campo nuevo que .NET no declara no rompe nada. Las 15 pruebas de esa clase están en verde.

`RetrievalRequest` **no se mueve**: `test_the_flag_is_not_part_of_the_request_contract` fija sus campos exactos en `{query, top_k, filters, mode, pos_id}`.

---

## 7. Decisiones de diseño, verificadas en código

| Decisión | Evidencia |
|---|---|
| D1 · El filtro duro es `is_assigned_hint`, no la existencia de fila | la CTE filtra `is_assigned_hint IS TRUE`; `test_a_soft_deleted_assignment_is_out_of_scope` falla si se relaja |
| D2 · CTE de alcance más distancia exacta | `WITH scope AS MATERIALIZED`; ningún `SET hnsw.*` ni índice forzado en `search.py`. **Matizada por medición**: ver §8.4 |
| D3 · El stock degrada como bloque de `demotion_rank` | `demotion_rank` devuelve una tupla de **4**, con el stock último y binario; seis tests unitarios sobre la clave |
| D4 · El tombstone es un borrado blando | `_SOFT_DELETE_SQL` es un `INSERT … ON CONFLICT DO UPDATE`, **no hay `DELETE` en el módulo**; `test_a_tombstone_soft_deletes_and_keeps_the_history` comprueba contra SQL real que la fila sobrevive y que `sales_30d` no se pisa |
| D5 · La frescura sale del checkpoint | `PROJECTION_SYNCED_AT_SQL` lee `ai.sync_checkpoint`; **`refreshed_at` no aparece en `retrieval/`**; caché de 10 s con `test_the_age_is_read_through_a_cache` |
| D6 · La frescura gobierna | `resolve_scope` decide vacío → 503, obsoleto → sin alcance con warning, fresco → alcance. Cuatro tests HTTP y seis unitarios |
| D7 · Reloj inyectado con constante declarada | `SalesAsOfUtc` alimenta el `now` que `GetSalesAggregatesAsync` ya recibía; `IndexFeedRepository` **no cambia de forma** |
| D8 · CLI y no ruta ni planificador | `test_no_v1_route_and_no_scheduler_were_added` |
| D9 · `pos_id` que no parsea se rechaza | `parse_pos_id` lanza antes de que ninguna rama corra; `test_a_malformed_claim_never_produces_an_unscoped_search` comprueba que `search_calls` y `lexical_calls` están **vacíos** |
| D10 · Flag en el patrón C20/C21 | `pos_prefilter` y `projection_max_age_seconds` son parámetros de `retrieve_products`, no campos de la request; el default no se muta |

---

## 8. Medición contra el feed real

API .NET local en `127.0.0.1:5056`, base local con 1.168 documentos y 6.720 filas de inventario. Informe completo en [`c22-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-implementation-measurements.md).

### 8.1. El drenaje (tarea 9.1)

```
upserted=6050 soft_deleted=670 pages=34 failed_pages=0 computed_as_of=2026-08-23T23:59:59+00:00
exit=0   duración=10,9 s
```

6.050 + 670 = **6.720**, exactamente las filas de `Inventories`. Los 670 borrados blandos coinciden con los desasignados que contó la exploración.

### 8.2. Deriva (tarea 9.2)

```
feed  = 3c239b0001ed2aeb6c061dd1b307de6a14e4eb8121e5115458a42e9207c4dd52
local = 3c239b0001ed2aeb6c061dd1b307de6a14e4eb8121e5115458a42e9207c4dd52
```

**Deriva = 0.** Calculada con el orden por bytes sin signo que documenta `set_hash.py`.

### 8.3. Tasa de llenado (tarea 9.3)

20 sondas, profundidad 60, umbral 0,65, página de 10.

| | Antes | Después |
|---|---|---|
| POS con al menos una sonda por debajo de la página | **8 de 11** | **0** |
| Peor caso (FORNELLS) | 3 supervivientes | 60 |
| Mediana (FORNELLS) | 10 | 60 |

Los ocho coinciden con lo que midió la exploración. **Y está declarado en el informe que el 60 no es una medida de calidad**: es la profundidad de rama, y se alcanza siempre porque el surtido más pequeño supera la ventana y porque el umbral deja pasar casi todo el corpus. El change garantiza que la página se llena, **no que se llene bien**; eso lo mide C24.

`sales_30d` no nulos con el instante aplicado: **1.424 de 6.050 = 23,54 %**.

### 8.4. Dos predicciones del diseño que no se confirmaron

| Predicción | Medido | Consecuencia |
|---|---|---|
| Escopado **7,3 ms** vs 10,8 ms sin escopar | **14,8-17,3 ms** vs 18,0-33,1 ms | La dirección se sostiene, la cifra no. **D2 corregida en `design.md`** |
| La distancia se calcula sobre el subconjunto escopado | El planificador **filtra los 1.168 documentos y hace el join después** | La CTE no ahorra cómputo. Lo que la justifica es la **corrección** —la profundidad se respeta por construcción— no la velocidad. **D2 corregida** |
| `sales_30d` «recupera un 16,28 % estable» | **23,54 %** | No es un error: el 16,28 % era contra el reloj de pared *hoy*; la ventana anclada cae en el pico de verano. **C25 calibra sobre 23,54 %** |

---

## 9. Incidencias de esta pasada

### 9.1. La columna que cinco documentos daban por innecesaria

La spec de `pos-projection` exige persistir el instante de referencia («both rows carry their sales figures **and the reference instant** in the projection»), y D7 dice «persisted alongside the projection». **`ai.pos_projection` no tiene esa columna**, ni en la base viva ni en las dos revisiones de Alembic. A la vez, la propuesta, el Migration Plan, un MUST de la propia spec, la HU y el ticket declaran «sin migración de ninguna clase».

La contradicción **venía del origen**, no de los artefactos de OpenSpec: el inventario del ticket comprobó de la tabla su `CHECK` y su índice, es decir su **existencia**, no la suficiencia de sus columnas.

Se paró la implementación y se consultó. Recomendación dada y aceptada: **abrir la revisión**, por tres razones:

1. **Sin la columna, la proyección puede contener dos relojes mezclados y es indetectable.** El drenaje es incremental: un par que no cambia nunca se reemite, así que conserva para siempre el `sales_30d` de la sincronización que lo escribió. El propio Migration Plan prescribía la secuencia que lo produce.
2. **Diferirla a C25 no la ahorra**: la traslada un change más tarde, sobre una proyección ya contaminada.
3. **El coste es mínimo y hay precedente exacto**: columna aditiva, anulable, sin default ni backfill, en el mismo patrón manuscrito que la revisión `b8e3c1a4d7f0` de C13.

Enmendados con la justificación escrita: `proposal.md`, `design.md` (D7 y Migration Plan), `specs/pos-projection/spec.md`, `tasks.md` (tarea 3.1 nueva y 10.2 reformulada), `ticket.md` (fila de historial) y la HU.

### 9.2. El paso 4 del Migration Plan no hacía lo que decía

Decía «fijar `IndexFeed:SalesAsOf` y **re-sincronizar** para que los agregados almacenados se recalculen contra el instante de referencia». Una pasada **incremental no recalcula nada**: el feed sólo reemite los pares cuyo inventario se movió. El plan se reordenó para fijar el instante **antes** del primer drenaje, y se dejó escrito por qué la redacción anterior fallaba en silencio.

### 9.3. El instante de referencia rompió un test existente, y con razón

`PosAvailabilityFeed_SalesWindows_DoNotSubtractReturns` sembraba ventas con `DateTime.UtcNow.AddDays(-10)`. Con el instante en 2026-08-23 y la ejecución en 2026-09-05, esa venta cae **después** del final de la ventana y suma cero. No es un fallo del cambio: es un test que era función del día en que se ejecutaba. Se ancló al instante que gobierna, leyéndolo de la configuración, de modo que sigue siendo cierto con la opción puesta o quitada.

### 9.4. El cursor de reanudación no podía ser el `productId`

El keyset del feed POS es `(watermark, Inventory.Id)` y **ese identificador nunca llega al cliente**. La primera versión del orquestador guardaba `(watermark, product_id)` al agotar el feed, lo que compara contra una columna distinta y **habría saltado filas en silencio**. Se cambió a `(último watermark, UUID cero)`: el predicado es estrictamente mayor, así que reemite las filas que comparten ese watermark —idempotente— y excluye todo lo anterior. `EXHAUSTED_SINCE_ID` lleva el porqué escrito y `test_the_exhausted_cursor_is_the_last_watermark_and_a_zero_id` lo fija.

### 9.5. La caché de frescura se contaminaba entre aplicaciones

Un test HTTP de edad falló con 172.800 s cuando esperaba 45. La causa era real, no del test: `default_freshness` era **de proceso**, y un proceso puede tener más de una aplicación —cualquier test que construya la segunda—, que entonces comparten una respuesta cacheada sobre un checkpoint que no comparten. Se ató al `app.state`, como ya se hacía con el cliente de embeddings, con el razonamiento escrito en `_resolve_freshness`.

### 9.6. `asyncio.run` no basta contra PostgreSQL

Dos problemas encadenados en los tests `db`. El motor es global y sus conexiones pertenecen al bucle que las abrió, así que un test con varios `asyncio.run` recibe en el segundo una conexión del primero y muere con un `InterfaceError` que no habla del código. Y en Windows psycopg **rechaza el `ProactorEventLoop`** que Python instala por defecto —la misma trampa que el README ya documenta para uvicorn—. Se centralizó en `tests/support/async_db.py`: un bucle por escenario, selector en Windows, y el motor dispuesto a ambos lados. **Y se llevó también al CLI** (`run_async` en `indexing/cli.py`), porque un comando cuyo único trabajo es escribir en PostgreSQL no debería obligar a cada operador a redescubrirlo.

### 9.7. Las fixtures de PostgreSQL efímero vivían en el sitio equivocado

Estaban en `tests/migrations/conftest.py`, y el repositorio de la proyección las necesitaba desde `tests/indexing/`. Se promovieron al conftest raíz, dejando en el de migraciones sólo lo específico. Las 49 pruebas de `tests/migrations/` se ejecutaron después del movimiento: **todas verdes**.

### 9.8. El alias `d` rompió dos aserciones de SQL existentes

Unir la CTE hace ambiguo `product_id`, así que las sentencias pasan a aliasar `ai.product_document` como `d` y cualificar los predicados. Dos tests de C21 comprobaban las cadenas sin cualificar (`AND materials && …`, `ts_rank(tsv,`). Se actualizaron a `d.`; **los predicados no cambian**, sólo su cualificación.

### 9.9. El orden de las dos guardias de 503

Con la guardia de proyección delante, `test_empty_compatible_index_raises_dependency_error` recibía el mensaje de la proyección en vez del del índice. Se movió la resolución del alcance **detrás** de `count_compatible`: un índice sin embeddings compatibles es un fallo más profundo que una proyección sin drenar, y es el que C14 ya nombra. El parseo del claim se queda delante de todo, porque un token roto lo está haga lo que haga la petición.

---

## 10. Verificado a mano

- `computedAsOf` leído directamente de una página real del feed: `2026-08-23T23:59:59Z`, con `pageSize=200`, `hasMore=true` y 200 ítems.
- `EXPLAIN (ANALYZE)` de la sentencia escopada leído entero, no sólo su tiempo — que es como se descubrió que el join va después del filtro (§8.4).
- Las dos pasadas de las clases que rotan en .NET se ejecutaron con `--no-build` a propósito, para descartar que la diferencia viniera de una recompilación.
- `python -m jbg_ai.indexing --help` comprobado a mano tras añadir el subcomando: `{sync,sync-pos}`.
- El diff de `openapi.json` se leyó línea a línea: 13 insertadas, ninguna borrada, ningún otro schema tocado.
- `git status --porcelain` vacío tras el commit `c2af1da`, para descartar ficheros generados sin querer.

---

## 11. Documentación de contexto

| Documento | Qué se alineó |
|---|---|
| `ai-service/README.md` | Sección nueva **«Synchronising the POS availability projection»** con la receta de cron y por qué no hay ruta ni planificador; **dos filas nuevas** en la tabla de entorno; la limitación del horizonte fijo declarada en los non-goals con las dos cifras (23,54 % frente a 16,28 %); y dos líneas obsoletas corregidas — «`ai.pos_projection` stays empty until C22» y «No drain of the POS feed» |
| `backend/README.md` | Fila `IndexFeed__SalesAsOf` en la tabla de entorno, con la exigencia de offset UTC y el porqué del valor |
| `Documentos/epicas.md` | C22 pasa de «en curso» a hecho dentro de EP14; el total se precisa a «22 archivadas, **1 implementada sin archivar** (C22), 14 pendientes» |
| `Documentos/Historias/AI-Eng/HU-AIENG-022.md` | Dos líneas corregidas por la revisión de Alembic (§9.1) |
| `ticket.md` | Fila de historial con la corrección, y tres líneas de alcance ajustadas |
| Informe nuevo | `c22-implementation-measurements.md`, con las tres predicciones contrastadas y las dos que no se confirmaron |

---

## 12. Fuera de esta pasada

- **Consultas reales de operador contra el proveedor.** Las sondas de llenado son de auto-similitud, reproducibles sin credenciales y comparables con la exploración; no sustituyen a la telemetría de C04 como línea base de «antes». Declarado en el informe.
- **Calidad del orden dentro del surtido.** El change llena la página; ordenarla bien es C24 con el golden set, etiquetado **sin escopar** a propósito.
- **Las señales de venta en el ranking** (C25), los sustitutos (C26), el aviso de frescura en la interfaz (C34/C36).
- **Los otros tres relojes del repositorio** —informe de movimientos, ventana de devolución, dashboards—. Inventariados en el informe de exploración, fuera de las métricas de RAG.
- **Índice HNSW parcial y `hnsw.iterative_scan`.** La medición dice que a 1.168 filas no hacen falta; el README los declara como techo de escalado y la cardinalidad escopada que ahora se registra es lo que mostrará cuándo hacen falta.
- **El rojo preexistente de `dotnet test`.** 52 nombres en línea base, con dos causas conocidas y documentadas. No se tocó ninguno: no es de este change.

---

## 13. Hallazgos del `/opsx:verify`, cerrados

La pasada de verify no releyó este documento: fue a buscar lo que pudiera contradecirlo. Salieron seis cosas.

### 13.1. CRITICAL — el drenaje no emitía `trace_id`, y la spec lo exige

`specs/pos-projection/spec.md:153` dice «The drain **and** the retrieval MUST emit structured logs carrying `trace_id`». La recuperación lo hacía; **el drenaje no emitía ninguno**. El de catálogo de C13 tampoco, así que no había precedente que copiar — pero el MUST es de esta capacidad, y no es cosmético: una pasada escribe 34 páginas y puede fallar en cualquiera, así que sin id las entradas de dos ejecuciones solapadas —un cron disparando mientras alguien lo lanza a mano— son indistinguibles.

**Cerrado:** `new_trace_id()` genera `sync-pos-<12 hex>`, aceptable por parámetro para que un llamador correlacione, presente en las cuatro líneas del drenaje más una línea `done` de cierre. Tres tests: `test_every_drain_log_entry_carries_a_trace_id`, `test_a_failed_page_is_logged_with_the_same_trace_id`, `test_a_drain_without_a_given_trace_id_generates_one`.

### 13.2. WARNING — un comentario afirmaba una garantía que el código no daba

El comentario decía *«A failed page keeps the cursor where it was, so the retry starts before it rather than after»*, y el test se llamaba `test_a_failed_page_does_not_advance_the_bookmark_past_itself`. **Sólo era cierto si la página fallida era la última**: el test pasaba porque su feed tenía una sola página. Probado con dos:

```
failed_pages=1  upserted=1
checkpoint watermark = 2026-08-22 11:00:00+00   ← la página 2, que sí funcionó
la página que FALLÓ cubría 2026-08-22 10:00:00+00
>>> el marcador AVANZÓ POR DELANTE de la página fallida
```

El **comportamiento** es correcto y deliberado —si el marcador se quedara atrás, una página permanentemente mala bloquearía todas las siguientes para siempre— pero el comentario y el nombre del test mentían sobre él.

**Cerrado:** comentario reescrito diciendo lo que pasa y por qué; el test renombrado a `test_a_page_that_fails_alone_does_not_move_the_bookmark`, y añadido `test_a_later_successful_page_does_move_the_bookmark_past_a_failed_one`, que fija la realidad y deja escrito que la página fallida se recupera de `ai.sync_failure` o de un `--full`, **no del cursor**.

### 13.3. WARNING — `lastSaleAt` no estaba anclado al instante de referencia

`GetSalesAggregatesAsync` acotaba las dos ventanas con `SaleDate <= now`, pero `LastSaleAt = MAX(SaleDate)` **no**. Verificado contra la proyección real: **3 filas** llevaban `last_sale_at` de 2026-08-29 contra un `computed_as_of` de 2026-08-23 — las ventas manuales de C16.

Era **conforme a la letra** de la spec, que pedía `MAX(SaleDate)`, y **contrario a su propósito**: era la única cifra de la página que seguía derivando cada vez que se registra una venta en la demo, justo lo que el instante de referencia existe para impedir, y es candidata a alimentar el decaimiento de C25.

No se tocó por iniciativa propia porque cambiaba comportamiento y contradecía una frase viva: **se consultó y se decidió anclarlo**.

**Cerrado:** `MAX(CASE WHEN SaleDate <= now)` en el repositorio, la frase de la spec de `index-feed` enmendada con el porqué, y un **escenario nuevo** en el delta. Test de integración —y no unitario— a propósito: el límite vive dentro de una expresión LINQ que EF Core traduce, así que sólo una base real prueba que el `MAX(CASE WHEN …)` traducido ignora las filas excluidas en vez de devolver null para el grupo. Redrenado y verificado:

| | Antes | Después |
|---|---:|---:|
| Filas con `last_sale_at` > `computed_as_of` | 3 | **0** |
| `last_sale_at` máximo | 2026-08-29 10:13 | 2026-08-23 19:56 |
| Filas con `last_sale_at` no nulo | 4.021 | 4.021 |
| `sales_30d` no nulos | 1.424 | 1.424 |

### 13.4. SUGGESTION — el código de salida del CLI no tenía guarda

El README promete «exits non-zero when any page failed» y **nada lo fijaba**: un cron que leyera 0 daría por buena una proyección medio drenada y no avisaría a nadie. **Cerrado** con `test_the_cli_exits_non_zero_when_a_page_failed` y `test_the_cli_exits_zero_on_a_clean_drain`.

### 13.5. SUGGESTION — un `getattr` defensivo contra un campo que el protocolo declara

`_out_of_stock` leía `getattr(item, "qty_bucket", None)` aunque `Constrained` ya declara el campo. Resultó **load-bearing**: el fixture `_Item` de `test_filters.py` no lo tenía, así que quitarlo sin más habría roto seis tests. **Cerrado** dándoselo al fixture y leyendo el atributo directamente: un protocolo cuyos campos la implementación no se atreve a leer no es un protocolo.

### 13.6. SUGGESTION — dos consultas de más, no tocadas

`count_scope` corre por petición sin cachear, y `_persist_checkpoint` hace un `count(*)` por página. Ambas correctas y dentro de presupuesto —la primera es un `count` sobre el prefijo de la PK, la segunda son 34 por drenaje—. Se anotan y se dejan: cachear la primera exigiría invalidarla al drenar, que es más superficie de la que ahorra.

### Lo que el verify comprobó y encontró bien

| Comprobación | Resultado |
|---|---|
| Ambas ventanas de venta usan el instante inyectado, acotadas también por arriba | ✅ |
| Ningún `DateTime.UtcNow` en la ruta del feed | ✅ ninguno |
| D4 · Ningún `DELETE` en el módulo de proyección | ✅ sólo `INSERT … ON CONFLICT` |
| D5 · `refreshed_at` nunca leído en `retrieval/` | ✅ sólo en comentarios que explican por qué no |
| D5/D6 · Constantes 10 s y 3600 s | ✅ |
| 14/14 requisitos con implementación | ✅ |

---

## Veredicto

**Sin problemas críticos abiertos.** El verify encontró uno —un MUST de spec sin implementar— y está cerrado (§13.1). `uv run --system-certs pytest` **697 passed, 0 failed** sobre una línea base medida de **598**, sin abrir un socket a proveedor, LLM ni RDS. `openspec validate --all --strict` **50 passed, 0 failed**. `dotnet test` con **cero fallos en las seis clases que el change toca**, y la rotación de nombres del resto demostrada como ruido del banco reproduciéndola sobre el mismo binario. **36/36 escenarios** con test nombrado, **4/4 nombres** exigidos por `tasks.md`, **47/47 tareas**, y los **6 hallazgos del verify cerrados** con sus guardas.

**Una desviación de artefactos, declarada y consultada:** se abre una revisión de Alembic aditiva de una columna anulable, con las seis piezas de documentación enmendadas (§9.1).

**Tres afirmaciones del diseño corregidas contra medición** en vez de citadas: las latencias de D2, la forma real del plan escopado, y el porcentaje estable de `sales_30d` (§8.4). **Y dos afirmaciones del propio código** que el verify demostró falsas: un comentario sobre el marcador de páginas fallidas (§13.2) y la promesa de reproducibilidad, que `lastSaleAt` incumplía en tres filas reales (§13.3).

**Listo para archivar.** El drenaje real escribe 6.720 filas con deriva 0 contra el `aggregateHash`, las páginas cortas pasan de ocho puntos de venta a ninguno, y la única consecuencia operativa nueva —HT-ARTRUTX, sin surtido, responde 503— queda escrita antes de que aparezca en un log.
