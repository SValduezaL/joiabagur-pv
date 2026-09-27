# T-AIENG-022: POS projection sync and soft prefilter, with an injected sales clock (C22)

> Ticket técnico del change OpenSpec `add-pos-projection-soft-prefilter`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, specs vivas de `openspec/specs/`, [HU-AIENG-022](../../../../Documentos/Historias/AI-Eng/HU-AIENG-022.md) y las mediciones de [c22-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-exploration-measurements.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-022 / C22** — Sincronizar `ai.pos_projection` desde el feed de disponibilidad, acotar la recuperación al surtido del punto de venta sin que la proyección pueda excluir por desfase, degradar por stock, y fijar el instante de referencia de las ventanas de venta

---

## Contexto y Problema

C12 dejó servido y especificado `GET /api/ai/index-feed/pos-availability`. C13 dejó construido el cliente (`fetch_pos_page`, `parse_pos_page`) y **prohibido consumirlo**. C05 dejó creada `ai.pos_projection` con su `CHECK` de `qty_bucket` y su índice inverso. Tres piezas encajadas y **cero filas escritas**: el alcance por punto de venta lo aplica hoy `.NET` al hidratar, después de que el retriever haya gastado su ventana de 60 candidatos sobre el catálogo entero.

La consecuencia es aritmética y está medida: **ocho de los once puntos de venta tienen al menos 6 de cada 20 búsquedas por debajo de una página de 10**, FORNELLS llega a 12 de 20 con un peor caso de **un solo producto**, y una consulta de MAO-AIR deja **cero** supervivientes — una página vacía que el panel de C16 pinta como abstención del modelo.

En paralelo, el mundo sintético de C10 tiene horizonte fijo (última venta real **2026-08-23**) y los agregados del feed se calculan contra el reloj de pared: `sales_30d` pasa del **16,28 %** de pares no nulos de hoy al **1,32 %** el 22 de septiembre y a **cero** el 26. C25 calibraría pesos sobre una señal muerta y concluiría que la rotación no aporta — un artefacto del reloj escrito como hallazgo.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `ai.pos_projection` (migración `f46c55c056e2`, `CHECK` de `qty_bucket`, `ix_..._product_id`) | Existe (C05) · **0 filas** |
| `ai.sync_checkpoint` con `feed` como PK (migración `b8e3c1a4d7f0`) | Existe (C13) · sólo la fila `catalog` |
| `GET /api/ai/index-feed/pos-availability` (página 200, keyset, tombstones, `X-Index-Feed-Key`) | Existe (C12), spec viva `index-feed` |
| `IndexFeedClient.fetch_pos_page` / `parse_pos_page` en `indexing/feed.py` | Existen · devuelven `dict` crudos, **sin tipar** |
| `IndexFeedRepository.GetSalesAggregatesAsync(pairs, now, ct)` | Existe · `now` **ya es parámetro**; lo alimenta `_timeProvider.GetUtcNow()` |
| `IndexFeedOptions` (`ApiKey`, `ApiKeyPrevious`) | Existe · **sin** `SalesAsOf` |
| `SqlAlchemyProductSearch.search` / `search_lexical` en `retrieval/search.py` | Existen · **no filtran por `pos_id`** (declarado en la spec viva) |
| `filters.demote()` / `demotion_rank()` en `retrieval/filters.py` | Existen (C21) · bloques `(precio, talla, materiales)` |
| `RetrievalResponse` (`results`, `candidates_returned`, `low_confidence`, `trace_id`, `effective_pos_id`) | Existe · **sin** `projection_age_seconds` |
| `ServicePrincipal.pos_id` | Existe · `str`, se transporta y se devuelve, **nunca toca SQL** |
| `TOKEN_POS_ID` en `ai-service/tests/support/settings.py` | Vale `"POS-B"` — **no es un UUID** |
| CLI `python -m jbg_ai.indexing sync` | Existe (C13) · **catálogo únicamente** |
| Artefactos OpenSpec de este change | **A generar** (0/4, schema `spec-driven`) |

**Impacto en producto:** el operador ve una página llena de productos vendibles en su tienda donde hoy ve una lista recortada. Es el primer cambio de la cadena que actúa sobre la **cantidad** de resultado útil y no sobre su orden.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/indexing/` | **Alto** — `feed.py` (tipado de ítems POS), repositorio y orquestación de `ai.pos_projection`, checkpoint propio, `cli.py` (`sync-pos`) |
| `ai-service/src/jbg_ai/retrieval/` | **Alto** — `search.py` (CTE de alcance en las tres sentencias), `ports.py`, `filters.py` (bloque de stock), `orchestrator.py` (frescura, guardias, flag) |
| `ai-service/src/jbg_ai/api/` | **Medio** — `schemas/retrieval.py` (`projection_age_seconds`), `routers/retrieval.py` (503 y degradación) |
| `ai-service/src/jbg_ai/config/settings.py` | **Medio** — flag de ablación y techo de antigüedad, con pin en `canonical_openapi_settings` |
| `ai-service/openapi.json` | **Medio** — se regenera. Primer movimiento del contrato desde C13 |
| `backend/src/JoiabagurPV.Application` | **Bajo** — `IndexFeedOptions.SalesAsOf`, `IndexFeedService.LoadSalesAsync`, DTO de página del feed POS |
| `backend/src/JoiabagurPV.Infrastructure` | **Bajo** — `IndexFeedRepository`: el `now` que recibe pasa a ser el instante de referencia |
| `openspec/changes/<change>/specs/` | **Alto** — capacidad nueva `pos-projection` + **tres deltas MODIFIED** |
| `Documentos/` | **Medio** — `epicas.md` (EP14), informe de llenado, limitación del README |
| `frontend/` · `terraform/` · `.github/workflows/` | **Ninguno** |

---

## Especificaciones Técnicas

### Servicio Python (`ai-service`)

**Sincronización de `ai.pos_projection`**

- Tipado de los ítems del feed POS sobre `fetch_pos_page`, que ya existe: `PosUpsertItem` (`point_of_sale_id`, `product_id`, `qty_bucket`, `is_assigned_hint`, `sales_30d`, `sales_90d`, `last_sale_at`, `watermark`) y `PosTombstoneItem` (`point_of_sale_id`, `product_id`, `reason`, `at`), con `parse_pos_item` análogo a `parse_catalog_item`.
- **Upsert idempotente** por `(pos_id, product_id)`, con `refreshed_at = now()`.
- **Tombstone `unassigned` como borrado suave**: `UPDATE … SET is_assigned_hint = false, qty_bucket = '0', refreshed_at = now()`. **Nunca `DELETE`.** Si la fila no existe, se inserta en ese estado.
- Cursor keyset propio en `ai.sync_checkpoint` con `feed = 'pos-availability'`, más `last_incremental_sync_at`, `last_full_sync_at`, `last_aggregate_hash` e `indexed_count`. **Sin migración**: la tabla tiene `feed` como clave primaria.
- Fallos por lote en `ai.sync_failure`, sin bloquear el resto.
- **CLI** `python -m jbg_ai.indexing sync-pos [--full]`, con la misma carga de `backend/.env` que `sync`. Receta de cron documentada en `ai-service/README.md`. **Sin ruta HTTP nueva** y **sin planificador en proceso**.

**Alcance por punto de venta**

- `pos_id` se toma del `ServicePrincipal` y se parsea a `UUID`. Si no parsea → **422**, nunca búsqueda global.
- CTE de alcance sobre `ai.pos_projection` filtrando `pos_id = :pos AND is_assigned_hint`, unido a `ai.product_document`, aplicado en las **tres** sentencias (vectorial, tecleada, expandida). La distancia se calcula sobre el subconjunto; **no se fuerza el índice HNSW**.
- El alcance es el **único** filtro duro que añade este change. Los filtros del cuerpo siguen excluyendo; los deducidos del texto siguen degradando (C21).

**Degradación por disponibilidad**

- `demotion_rank` pasa de `(precio, talla, materiales)` a `(precio, talla, materiales, sin_stock)` — **clave única**, un solo `sorted` estable, prioridad explícita.
- `sin_stock` es **binario**: `qty_bucket == '0'`. Los tres tramos se persisten y no se leen: los calibra C25.
- Nada se elimina: todo candidato permanece dentro de la ventana de sobre-recuperación.

**Frescura y guardias**

- `projection_age_seconds: float | None` en `RetrievalResponse`, calculado como `now − ai.sync_checkpoint.last_incremental_sync_at` para `feed = 'pos-availability'`. **Nunca** desde `max(refreshed_at)`: el feed es incremental y ese campo mide cuándo cambió la asignación, no cuándo se miró.
- Lectura **cacheada** unos segundos, por el pool capado a 5 sin overflow (mismo criterio que el informe de `/health` de C17).
- **Proyección vacía** para ese `pos_id` → `503`, con el mismo espíritu que `count_compatible == 0`: *refusing to abstain over an empty projection*.
- **Antigüedad por encima del techo configurado** → el filtro duro **no se aplica** en esa petición, se registra un `warning` y la respuesta declara la antigüedad. La página puede quedar corta; ningún producto válido desaparece antes de que .NET lo vea.

**Settings nuevos** (default en `Settings`, valor efectivo por parámetro del orquestador, pin en `canonical_openapi_settings`)

| Setting | Default | Para qué |
|---|---|---|
| `JPV_POS_PREFILTER_ENABLED` | `true` | Ablación de C24 sin reiniciar y sin mover el contrato |
| `JPV_POS_PROJECTION_MAX_AGE_SECONDS` | _a fijar en `design.md`_ | Techo de antigüedad que degrada el filtro duro |

**OpenAPI:** se regenera `ai-service/openapi.json` con la receta del README y se actualiza el snapshot de `test_openapi_snapshot_is_stable`. Es el primer movimiento del contrato desde C13 y es deliberado.

**Logs:** `stage=projection` (antigüedad, filas de alcance, si el filtro se aplicó) y ampliación de `stage=search` con la cardinalidad escopada — el hábito que S10 pide: *«verifica la cardinalidad de lo que vuelve, y déjala en los logs»*.

### Backend (.NET) — cambio quirúrgico

- `IndexFeedOptions.SalesAsOf` (`DateTime?`, nulo = reloj de pared), validado al arrancar si está presente. Valor de configuración: **`2026-08-23T23:59:59Z`**.
- `IndexFeedService.LoadSalesAsync` pasa `SalesAsOf ?? _timeProvider.GetUtcNow().UtcDateTime` al `now` que `GetSalesAggregatesAsync` **ya recibe como parámetro**. `IndexFeedRepository` no cambia de forma.
- `computedAsOf` en el DTO de página del feed de disponibilidad, persistido por Python en la proyección.
- **Sin migración de EF Core.** Sin endpoints nuevos. Sin tocar el feed de catálogo.
- **Una revisión de Alembic aditiva**, contra lo que decía la redacción original de este ticket: `ai.pos_projection` no tiene columna donde persistir el instante de referencia, y el inventario de arriba comprobó la existencia de la tabla —su `CHECK` y su índice— no la suficiencia de sus columnas. Ver el apartado *Riesgos* y la decisión D7 del `design.md`.

### Fuera de este ticket

Señales de venta en el ranking (**C25**) · sustitutos (**C26**) y complementarios (**C27**) · corpus de conocimiento (**C23**) · golden set (**C24**) · aviso de frescura en la interfaz (**C34/C36**) · revertir `AiGateway:RetrievalTimeoutMs` a 800 ms · índice HNSW parcial y `hnsw.iterative_scan` · los otros tres relojes del repositorio (informe de movimientos, ventana de devolución, dashboards) · `ai.query_log` · cualquier migración que cree, altere o elimine una tabla.

---

## Arquitectura

- **Frontera intacta** (diseño §6.2): *Python calcula parecidos y redacta; .NET calcula números y decide*. Python no lee `public` por SQL; toda la disponibilidad llega por el feed HTTP de C12. `.NET` sigue siendo la autoridad sobre precio, stock y permisos, y su hidratación sigue siendo el último filtro.
- **El orden del pipeline es el del §7.6 y el de S10**: lo excluyente y barato al principio —el alcance, en la propia consulta—, lo blando al cierre —el stock, sobre los finalistas ya fusionados—.
- **Patrones en uso:** repositorio inyectable con `Protocol` (`ProductSearchPort`, `IndexFeedClient`), función pura para la degradación por bloques, y el patrón de flag de C20/C21 (default en `Settings`, valor por parámetro) para que C24 barra configuraciones sin tocar el esquema congelado.
- **Decisiones previas que se respetan:** `indexing/embeddings.py` congelado desde C11 · `enrichment/vocabularies.yaml` intacto · pool de 5 sin overflow, una conexión por momento · `effective_pos_id` siempre del token, nunca del cuerpo.
- **Breaking changes:** `ai-service/openapi.json` se mueve por un **campo opcional de respuesta**, compatible hacia atrás para el deserializador .NET. La página del feed POS gana `computedAsOf`, también opcional. Ningún contrato REST del backend cambia de forma.
- **Deltas de specs obligatorias** — sin ellas, `openspec validate --all --strict` seguiría en verde sobre specs vivas falsas:

| Spec viva | Frase que queda falsa |
|---|---|
| `vector-retrieval` | «**AND** the search SQL does not filter by `pos_id`» |
| `product-document-indexer` | «MUST NOT invoke the POS availability feed and MUST NOT write `ai.pos_projection`» |
| `index-feed` | «`sales30d` and `sales90d` MUST be `SUM(Sale.Quantity)` … **over the last 30 and 90 days**» |

Más la capacidad nueva **`pos-projection`**, al estilo de `hybrid-fusion` en C21.

---

## Criterios de Aceptación

Los diez escenarios normativos están en [HU-AIENG-022](../../../../Documentos/Historias/AI-Eng/HU-AIENG-022.md#criterios-de-aceptación). En resumen ejecutable:

**Pruebas de validación** (`uv run pytest` desde `ai-service/`, `dotnet test` desde `backend/`):

- `test_unassigned_tombstone_soft_deletes_instead_of_removing_the_row`
- `test_out_of_stock_product_is_penalised_not_removed`
- `test_out_of_stock_product_still_present_in_candidates`
- `test_pos_scope_from_token_is_hard_filter`
- `test_body_pos_id_is_ignored_and_token_scope_is_echoed`
- `test_non_uuid_pos_id_is_rejected_and_never_widens_the_search`
- `test_projection_stores_bucket_not_exact_quantity`
- `test_response_reports_projection_age`
- `test_projection_age_comes_from_the_checkpoint_not_from_refreshed_at`
- `test_empty_projection_is_503_not_abstention`
- `test_stale_projection_disables_the_hard_filter_and_declares_it`
- `test_disabled_flag_restores_pre_change_behaviour`
- `test_scoped_vector_branch_returns_the_full_depth` (regresión del truncado a 40)
- `test_sync_pos_is_idempotent_and_resumes_from_the_checkpoint`
- `test_pos_sync_does_not_touch_the_catalog_checkpoint`
- `test_retrieval_makes_no_provider_or_public_schema_call`
- .NET: `SalesAggregates_WithConfiguredAsOf_CountWindowsAgainstIt`
- .NET: `SalesAggregates_WithoutAsOf_FallBackToWallClock`
- .NET: `PosAvailabilityPage_DeclaresComputedAsOf`

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec completos: `proposal`, **`design.md` obligatorio**, `specs` (capacidad `pos-projection` + tres deltas MODIFIED) y `tasks`
- [ ] `openspec validate --all --strict` en **`0 failed`**
- [ ] `uv run pytest` en verde, **sin llamadas reales** a LLM, embeddings ni RDS; tests de BD con testcontainers y pgvector
- [ ] `dotnet test` sin regresión respecto a la línea base medida con `git stash` (comparar **nombres** de test, nunca el número)
- [ ] `ai-service/openapi.json` regenerado con la receta del README y snapshot actualizado
- [ ] `TOKEN_POS_ID` corregido a un UUID y la batería dependiente en verde
- [ ] Exactamente **una** revisión de Alembic, aditiva (`computed_as_of` en `ai.pos_projection`), y **sin** migración de EF Core
- [ ] `indexing/embeddings.py`, `enrichment/vocabularies.yaml` y el árbol `frontend/` sin diff
- [ ] Informe de llenado por punto de venta, antes y después, versionado en `Documentos/Proyecto Final AIEng/informes/`
- [ ] `Documentos/epicas.md` (EP14) enlaza HU-AIENG-022; limitación del instante de referencia declarada para el README
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada

---

## Requisitos No Funcionales

- **Seguridad:** el alcance sale **siempre** del claim `pos_id` del token interno HS256, nunca del cuerpo; un `pos_id` inválido se rechaza y jamás degrada a búsqueda global. El feed sigue autenticado sólo con `X-Index-Feed-Key`, comparada en tiempo constante y nunca registrada. La CLI carga credenciales de `backend/.env`, que no está en el repositorio.
- **Rendimiento:** el alcance **reduce** el coste medido (7,3 ms escopado frente a 10,8 ms sin escopar). Pool de 5 sin overflow: una conexión en vuelo por petición, y la lectura de frescura cacheada unos segundos. Página del feed POS fijada por el servidor en 200 ítems.
- **Observabilidad:** `stage=projection` y cardinalidad escopada en `stage=search`, ambos con `trace_id`; contadores de la CLI; `projection_age_seconds` en la respuesta.
- **Integridad de datos:** la proyección **nunca** transporta la cantidad exacta, sólo el tramo — la cantidad la pone .NET. Un producto válido no puede desaparecer por una proyección desfasada: por encima del techo de antigüedad el filtro duro se desactiva. La sincronización es idempotente y reanudable por keyset.
- **Reproducibilidad:** con el instante de referencia configurado, la misma configuración y semilla producen el mismo resultado en días distintos — precondición del `test_run_is_reproducible_for_same_config_and_seed` de C24 y de la tabla de ablations del §16.

---

## Preguntas Abiertas → Decisiones

Las nueve decisiones de diseño se cerraron en la sesión de exploración del 2026-09-05 y están en la tabla de [HU-AIENG-022](../../../../Documentos/Historias/AI-Eng/HU-AIENG-022.md#decisiones-de-diseño-ya-acordadas). Quedan abiertas dos, con opción por defecto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | Valor de `JPV_POS_PROJECTION_MAX_AGE_SECONDS` | **3600 s**. La cadencia de diseño es de 5-10 min y la real será un cron; una hora degrada sólo ante un fallo sostenido, no ante un retraso normal. Se fija en `design.md` |
| 2 | Ventana de caché de la lectura de frescura | **10 s**, el mismo valor que el informe de `/health` de C17 usa por el mismo motivo (pool capado a 5) |

---

## Prioridad / Estimación / Tags

- **Prioridad:** Alta — ruta crítica `C21 → C22 → C25`; en la lista de *nunca se recorta* del §6 del plan. Arrastra además una **fecha dura**: `sales_30d` es cero para todo el catálogo a partir del 2026-09-26.
- **Estimación:** _Pendiente_ (complejidad **4** según la HU)
- **Tags:** `ai-service` · `backend` · `retrieval` · `indexing` · `openspec` · `no-migration` · `contract-change` · `C22`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-022](../../../../Documentos/Historias/AI-Eng/HU-AIENG-022.md)
- **Change:** [`openspec/changes/add-pos-projection-soft-prefilter/`](./)
- **Mediciones:** [c22-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-exploration-measurements.md)
- **Diseño RAG:** [§6.2, §6.3, §7.2, §7.6 y §11.2](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Plan de changes:** [ficha C22](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Specs vivas:** `openspec/specs/index-feed/`, `openspec/specs/product-document-indexer/`, `openspec/specs/vector-retrieval/`, `openspec/specs/hybrid-fusion/`, `openspec/specs/ai-service-api-contracts/`
- **Procedimientos:** [User Stories](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Tickets de Trabajo](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)
- **Apuntes:** [S10 · Filtrado contextual y temporal](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Filtrado%20contextual%20y%20temporal.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-05 | Sergio Valdueza | Creación del ticket a partir de la sesión de exploración de C22 y de sus mediciones. Nueve decisiones cerradas, incluida la incorporación del reloj inyectado (FIX2) dentro de este change |
| 2026-09-05 | Sergio Valdueza | Corrección durante la implementación: se abre **una** revisión de Alembic aditiva. `ai.pos_projection` no tiene columna para el instante de referencia que la decisión 8 exige persistir, y como el drenaje es incremental, sin ella la proyección puede acabar con filas calculadas contra dos relojes distintos e indistinguibles. Diferirla a C25 no la ahorra: la traslada sobre una proyección ya contaminada |
