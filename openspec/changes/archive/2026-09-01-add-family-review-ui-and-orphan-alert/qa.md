# QA — C18b `add-family-review-ui-and-orphan-alert`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fechas:** implementación y revisión humana el **2026-08-31**; cierre, backfill y pasada de verificación el **2026-09-01** · **Rama:** `c18b-add-family-review-ui-and-orphan-alert`, creada desde `ai-eng`
> **Alcance al cierre:** 68/68 tareas (62 del change + 6 de esta pasada) · 7/7 artefactos · **3 migraciones EF Core**, no una · 54 escenarios de spec
> **Pasada de verificación** el 2026-09-01, registrada en §11: **ocho tests que la spec o `tasks.md` exigían y no existían**, una tarea marcada con dos entregables de pantalla inexistentes, una carcasa prometida y no extraída, una premisa de diseño que no se cumplió, y un requisito que afirmaba una distinción que el código no hace.
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` **con `--system-certs` en toda llamada**, según `CLAUDE.md` |
| .NET | 10.0 · `dotnet test` contra `backend/src/JoiabagurPV.Tests/JoiabagurPV.Tests.csproj` |
| PostgreSQL | `jpv-pv-postgres` (pgvector/pg15) en `:5433`, con el corpus real de 1.200 productos y 1.168 documentos |
| Tests de integración | **Testcontainers**, base efímera propia. Nunca tocan la base de desarrollo — que es lo que permite que la revisión humana de 58 juicios conviva con la suite |
| Contrato | `ai-service/openapi.json` — **se regenera a propósito**: décima ruta. Ver §5 |
| Migraciones EF | **Tres**, todas sobre la tabla nueva: `AddFamilyReviewVerdict`, `AddFamilyReviewSeconds`, `AddVerdictSubjectPopulation` |
| Migraciones Alembic | **Ninguna revisión nueva.** `migrations/env.py` sí cambia, y no es una migración: ver §8.1 |
| Frontend | dev server en `:3000`; suite con `vitest run` |
| Respaldo | `pre-c18b.dump` (39,9 MB, esquemas `public` y `ai`) antes de escribir una sola fila |

---

## 1. Líneas base, medidas con el árbol limpio

Tomadas **antes** de tocar nada y guardadas **por nombre de test**, no por recuento — la regla de `CLAUDE.md`. Versionadas en [`baseline/`](./baseline/).

| Suite | Resultado | Nombres en rojo |
|---|---|---|
| `ai-service` | **0 failed / 356 passed** | ninguno |
| Frontend (`vitest run`) | **113 failed / 420 passed** (533) | 113 nombres en 14 ficheros |
| Backend (`dotnet test`) | **47 failed / 873 passed** (920) | 47 nombres en 17 clases |

**Ninguna de las 17 clases del backend ni de los 14 ficheros del frontend toca familias.** La superficie que C18b modifica está limpia en la línea base, lo que abarata la comparación de cierre: cualquier fallo en esas clases sería de este change.

> **Nota de método.** La línea base se midió sin `git stash` y a propósito: el árbol no tenía ni un cambio de código, sólo markdown, así que el estado del momento **era** la línea base. El guardarraíl existe para no medir sobre código propio, no para ejecutar el comando.

---

## 2. Comparación de cierre, por nombres

### `ai-service`

| | Fallos | Pasan | Total |
|---|---|---|---|
| Línea base | 0 | 356 | 356 |
| Cierre | **0** | 469 | 469 |
| Tras la pasada de verificación | **0** | **472** | **472** |

**Cero en las tres filas.** 116 tests nuevos, de los cuales 3 los añadió la pasada de verificación (§11.1).

Una anomalía la corrigió este change y merece constar: la suite **llegó roja de un change anterior** y no se dejó pasar como preexistente. Causa y arreglo en §8.1.

### Frontend

| | Fallos | Pasan | Total |
|---|---|---|---|
| Línea base | 113 | 420 | 533 |
| Cierre | **113** | 439 | **552** |

**Exacto: los 113 nombres son los mismos 113.** Cero nuevos, cero arreglados, y los **19** tests de la pantalla de revisión en verde.

### Backend

| | Fallos | Pasan | Total |
|---|---|---|---|
| Línea base | 47 | 873 | 920 |
| Cierre | 51 | 900 | 951 |
| Tras la pasada de verificación, ejecución A | 49 | 924 | **973** |
| Tras la pasada de verificación, ejecución B | 52 | 921 | **973** |

**Por nombre no cierra exacto, y hay que decir en qué.** Seis nombres que la línea base no tenía y dos que sí:

```
nuevos          InventoryIntegrationTests   ExcelImport_DownloadTemplate_ShouldSucceed
                                            ExcelImport_NegativeQuantityWithSufficientStock_...
                                            MovementHistory_WithPagination_ShouldReturnPagedResults
                                            Operator_AdjustStock_ShouldBeForbidden
                ProductsControllerTests     Update_WithValidData_ShouldReturnUpdatedProduct
                ReturnsControllerTests      GetReturnsHistory_WithFilters_ReturnsFilteredResults

desaparecidos   ReturnsControllerTests      GetReturnsHistory_WithExistingReturns_ReturnsPagedResults
                SalesControllerTests        CreateSale_OperatorNotAssignedToPOS_ReturnsBadRequest
```

Los ocho caen **dentro de clases que ya fallaban en la línea base**, y ninguna de las cuatro toca familias, el controlador de catálogo IA ni la entidad nueva.

**Y tras la pasada de verificación aparece una clase que la línea base no tenía: `DashboardServiceTests`.** No es de este change, y la causa es comprobable sin ejecutar nada: `GetGlobalStatsAsync_WithSalesToday_ShouldReturnCorrectKPIs` construye sus ventas contra `DateTime.UtcNow` —una a `now`, otra a `now.AddDays(-5)`— y afirma `MonthlyRevenue = 450`, que exige que las dos caigan en el mismo mes. La línea base se midió el **31 de agosto**, cuando `now-5d` seguía siendo agosto; esta ejecución es del **1 de septiembre**, y `now-5d` es el 27 de agosto. Lo mismo con la devolución de `now.AddDays(-2)` y `MonthlyReturnsCount = 1`.

Es una **bomba de calendario que estalla los primeros cinco días de cada mes**, en un fichero que este change no toca —ni `DashboardServiceTests.cs` ni `DashboardService.cs` tienen un solo commit en esta rama—. Se anota aquí en vez de contarla como regresión, y queda como candidata a arreglo en otro change: el test debería anclar sus fechas al mes en curso en lugar de restar días al reloj.

**Y el nombre no es unidad estable en esta suite.** Se midió aquí: **dos ejecuciones del mismo código dieron 48 y 54 fallos**, con nombres distintos dentro de las mismas clases. `CLAUDE.md` avisa de que un puñado de estos fallos dependen del orden; lo que esta medición añade es que la inestabilidad llega **al nivel de nombre**, y que la unidad que sí se sostiene es la **clase**.

> **El conjunto de clases con fallos es el de la línea base más `DashboardServiceTests`, cuya causa es el cambio de mes y no este change. Ninguna clase de familia aparece en él.**

Y por el lado positivo, que es el que importa para este change: las **siete clases** que cubren la superficie tocada —`FamilyReviewControllerTests`, `FamilyReviewVerdictSchemaTests`, `ProductFamiliesControllerTests`, `ProductFamilySchemaTests`, `AiCatalogControllerTests`, `FamilySuggestionControllerTests` y `AiGatewayFamilyAuditTests`— corren **133 de 133 en verde**.

> **Una trampa de método que costó una ejecución.** `dotnet test` sale con **código 0 aunque la compilación falle**. Con la API de desarrollo levantada, MSBuild no puede copiar las DLL —el proceso las tiene bloqueadas—, la compilación muere y el comando informa éxito. Y filtrar a una sola clase de integración tampoco vale: `ResetDatabaseAsync` corre en `InitializeAsync` y Respawn revienta con *«No tables found»* si ninguna otra clase de la colección ha creado el esquema antes. Ambas cosas se leen como veinte tests rotos y ninguna lo es.

---

## 3. Escenarios de las specs, uno a uno

**54 escenarios en cuatro specs.** Ninguno queda cubierto sólo por la ejecución manual. Los marcados **(nuevo)** los añadió la pasada de verificación del §11.

### `family-review` (nueva) — 30 escenarios

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Auditar recomputa sobre lo persistido · Un miembro al que otra familia le queda más cerca | `test_audit_flags_member_when_stranger_beats_worst_sibling` · `Audit_ReturnsFlaggedMembersAndCandidates_ForAdministrator` | ✅ |
| … · La marca se produce para productos que `suggest` ya no ve | `test_flag_is_produced_for_products_suggestion_can_no_longer_see` | ✅ |
| … · Ningún umbral global decide una marca | `test_a_member_without_similarity_is_not_flagged` · `test_the_veto_universe_is_keyed_by_the_family_a_product_belongs_to` | ✅ |
| Huérfanos por margen relativo · Más cerca que el peor miembro | `test_orphan_detection_lists_unassigned_similar_products` | ✅ |
| … · La pureza no nomina | `test_purity_does_not_nominate` · `test_purity_is_reported_but_is_not_the_criterion` · `should report purity without ever filtering on it` | ✅ |
| … · Nunca cruza tipos de pieza | `test_orphan_nomination_never_crosses_piece_type` | ✅ |
| … · Sin tipo de pieza no se nomina para nada | **`test_orphan_without_piece_type_is_never_nominated`** *(nuevo)* | ✅ |
| … · Se reporta el `data_origin` de cada candidato | `test_a_candidate_carries_the_evidence_a_reviewer_needs` · **`AuditFamiliesAsync_KeepsEveryFieldACandidateIsJudgedBy`** *(nuevo)* | ✅ |
| … · El margen de nominación viene de configuración | `test_orphan_margin_comes_from_configuration` | ✅ |
| Auditar no escribe · La auditoría deja el catálogo intacto | **`test_audit_writes_nothing`** *(nuevo)* · `Audit_WritesNothing_WhenRequested` | ✅ |
| Veredicto persistido · Un candidato descartado no vuelve | `Verdict_DismissedPair_ExcludedFromNextAudit` · `test_judged_pairs_are_omitted_from_both_lists` · `should keep a dismissed suggestion out of the next run` | ✅ |
| … · Juzgar dos veces el mismo par corrige | `Verdict_SamePairTwice_CorrectsInsteadOfDuplicating` · `Migration_ProductAndFamilyPairIsUnique` | ✅ |
| … · Confirmar registra sin mover el catálogo | **`Verdict_ConfirmingWithoutEditing_RecordsTheJudgementAndMovesNothing`** *(nuevo)* | ✅ |
| … · Disolver una familia se lleva sus veredictos | `DeleteFamily_CascadesVerdictsAndFreesProducts` · `Migration_DeletingAFamilyCascadesToItsVerdicts` | ✅ |
| … · Un veredicto caduco se muestra caduco, no se reabre | **`Verdict_KeepsTheMarginItWasTakenAt_AndTravelsWithTheNextAudit`** *(nuevo)* · `test_judged_pairs_are_omitted_from_both_lists` para la omisión, que es del servicio; ver §11.3 | ✅ |
| Sólo administradores · Un operador no puede auditar ni juzgar | `Audit_ReturnsForbidden_ForOperator` · `Verdict_RequiresAdministrator` | ✅ |
| … · Un llamante sin autenticar es rechazado | `Audit_Unauthenticated_ReturnsUnauthorized` · `test_the_route_requires_the_service_token` | ✅ |
| Una lista no calculada nunca se pinta vacía · Auditoría no disponible | `Audit_WhenServiceUnavailable_ReturnsServiceUnavailableNotAnEmptyResult` · `should show the audit as unavailable when the ai service does not answer` · **verificación a mano, §7** | ✅ |
| … · Una lista calculada y vacía se muestra vacía | `should show an empty audit as computed and empty, not as unavailable` | ✅ |
| … · La revisión de familias sobrevive a una auditoría caída | `should keep family review usable when the audit is unavailable` · **verificación a mano, §7** | ✅ |
| Un veredicto no es una pertenencia · Un juicio no ejecutado se lista como pendiente | `should list only the judgements the catalogue has not acted on` · `should count the pending changes on its tab` · `should say nothing is pending only when every decision is reflected` | ✅ |
| … · Ejecutar un juicio mueve la pertenencia y el watermark | `should enact a pending addition with the variant label the reviewer typed` · `DeleteFamily_StampsDepartingProducts` | ✅ |
| Corregir la etiqueta a posteriori · Se corrige sin tocar el resto | `should let the reviewer correct the variant label of a member` · `MoveProductBetweenFamilies_ReordersAndSwapsLabels_WithoutPhantomUpdate` | ✅ |
| … · Una etiqueta que colisiona con un hermano se rechaza | `ReplaceMembers_WithDuplicateVariantLabel_ReturnsBadRequest` — el `PUT` declarativo de C07 es el único camino de escritura, y su rechazo es atómico | ✅ |
| Tiempo por juicio, no en la pantalla · Los segundos sobreviven a la sesión | `Verdict_RecordsTheSecondsSpentReviewing` · `should send the seconds spent with each judgement` · `should show the average review time from the server, not from this session` | ✅ |
| … · Sin nada cronometrado se informa la ausencia, nunca un cero | `Metrics_WithNoTimings_ReportsNullAverageRatherThanZero` · `should say when nothing was timed rather than showing a zero average` | ✅ |
| … · Las dos poblaciones se reportan por separado | `Metrics_ReportEachPopulationApart` | ✅ |
| … · Ejecutar un juicio no lo mueve de población | **`Metrics_RejectedMemberRemovedFromItsFamily_IsStillCountedAsAMember`** *(nuevo)* | ✅ |
| Determinista y sin modelo · Dos auditorías sobre lo mismo coinciden | `test_audit_is_deterministic` | ✅ |
| … · No se llama al proveedor | **`test_audit_calls_no_provider`** *(nuevo)* | ✅ |

### `ai-service-api-contracts` (delta) — 8 escenarios

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Superficie `/v1` congelada · Cada ruta responde con su modelo | `test_stub_matches_response_schema` · `test_snapshot_covers_the_frozen_surface` | ✅ |
| … · El contrato de salud no cambia | `test_health_contract_is_unchanged` (C17, sin tocar) | ✅ |
| … · `families/suggest` exige el token de servicio | `test_the_route_requires_the_service_token` (C18a) | ✅ |
| … · `families/audit` exige el token de servicio | `test_the_route_requires_the_service_token` | ✅ |
| … · El snapshot regenerado casa con el esquema vivo | `test_openapi_snapshot_is_stable` — **verificado fallando**, §5 | ✅ |
| Contrato de auditoría · Una llamada devuelve los dos lados | `test_stub_populates_both_findings_and_both_refusals` | ✅ |
| … · Los pares juzgados viajan y no se guardan | `test_judged_pairs_are_omitted` · `test_judged_pairs_are_not_remembered_between_calls` · `test_judged_pairs_match_regardless_of_guid_case` | ✅ |
| … · El tope de candidatos nunca trunca un rechazo | `test_the_candidate_cap_never_truncates_a_refusal` · `test_margins_out_of_range_are_refused` | ✅ |

### `ai-gateway-client` (delta) — 8 escenarios

**Los ocho estaban sin un solo test sobre el cliente antes de la pasada de verificación.** Ver §11.1.

| Requisito · escenario | Test | Resultado |
|---|---|---|
| El cliente expone la auditoría · Ambas listas sin truncar | **`AuditFamiliesAsync_WhenServiceReturns200_SurfacesBothListsWithoutTruncating`** · **`AuditFamiliesAsync_KeepsTheOrderReceived`** · **`AuditFamiliesAsync_DoesNotDropACandidateForItsOriginOrItsPurity`** *(nuevos)* | ✅ |
| … · La evidencia sobrevive al mapeo | **`AuditFamiliesAsync_KeepsEveryFieldACandidateIsJudgedBy`** · **`AuditFamiliesAsync_KeepsTheMarginAndTheStrangerOfAFlaggedMember`** · **`AuditFamiliesAsync_MapsAnAbsentVariantToNullAndNotToEmptyString`** *(nuevos)* | ✅ |
| … · Los pares ya juzgados viajan con la petición | **`FamilyAuditRequest_SerializesTheJudgedPairsWithContractNames`** *(nuevo)* · `Verdict_DismissedPair_ExcludedFromNextAudit` (afirma sobre `gateway.LastRequest.JudgedPairs`) | ✅ |
| … · Los nombres de cable siguen el contrato | **`FamilyAuditRequest_SerializesInSnakeCase`** · **`FamilyAuditResponse_DeserializesTheSnakeCaseContract`** *(nuevos)* | ✅ |
| Fallos distinguibles · Una dependencia inalcanzable no es una auditoría vacía | **`AuditFamiliesAsync_WhenServiceFails_RaisesUnavailableAndNeverAnEmptyAudit`** · **`AuditFamiliesAsync_WhenTransportFails_RaisesUnavailable`** *(nuevos)* | ✅ |
| … · Un cuerpo vacío es un fallo, no una auditoría vacía *(escenario reescrito, §11.2)* | **`AuditFamiliesAsync_WhenBodyIsEmpty_RaisesRatherThanReturningNoFindings`** *(nuevo)* | ✅ |
| … · Una petición inválida se rechaza antes de enviarse *(escenario reescrito, §11.2)* | **`AuditFamiliesAsync_RefusesAnInvalidRequestWithoutCallingTheService`** · **`AuditFamiliesAsync_RejectsAPointOfSaleScope`** · **`AuditFamiliesAsync_WhenRouteIsNotImplemented_RaisesTheNotImplementedError`** · **`AuditFamiliesAsync_WhenCredentialsAreRejected_RaisesTheConfigurationError`** *(nuevos)* | ✅ |
| … · Una auditoría fallida no cambia nada | **`AuditFamiliesAsync_ProducesNoAuditWhenItFails`** *(nuevo)* · **`Verdict_FailedAudit_ChangesNothing`** *(nuevo)* | ✅ |

### `product-family` (delta) — 8 escenarios

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Listado paginado · Página a página | `ListFamilies_ReportsMemberAndReviewCounts` · **`ListFamilies_ReturnsAtMostFiftyPerPage`** *(nuevo)* · `should list families a page at a time when the screen opens` | ✅ |
| … · Se estrecha por cómo llegó a existir la familia | `ListFamilies_FiltersByOrigin` · `ListFamilies_UnknownOrigin_ReturnsBadRequest` | ✅ |
| … · Se estrecha a familias con miembros marcados | `ListFamilies_ReportsMemberAndReviewCounts` | ✅ |
| … · Un operador no puede listar | `ListFamilies_RequiresAdministrator` | ✅ |
| Disolver, no sólo vaciar · Libera a sus miembros | `DeleteFamily_CascadesVerdictsAndFreesProducts` | ✅ |
| … · Los productos que salen son visibles al feed incremental | `DeleteFamily_StampsDepartingProducts` | ✅ |
| … · Borrar una familia ausente se reporta como ausente | `DeleteFamily_Absent_ReturnsNotFound` | ✅ |
| … · Un operador no puede disolver | `DeleteFamily_RequiresAdministrator` | ✅ |

---

## 4. Nombres exigidos por `tasks.md`

Los 24 nombres que las tareas nombran por escrito, cruzados contra los que existen. **Cinco no existían** y los escribió la pasada de verificación (§11.1); ninguno se renombró para hacerlo cuadrar.

| Estado | Nombres |
|---|---|
| Ya existían | `Audit_ReturnsFlaggedMembersAndCandidates_ForAdministrator` · `Audit_ReturnsForbidden_ForOperator` · `Audit_Unauthenticated_ReturnsUnauthorized` · `Audit_WritesNothing_WhenRequested` · `DeleteFamily_Absent_ReturnsNotFound` · `DeleteFamily_CascadesVerdictsAndFreesProducts` · `DeleteFamily_StampsDepartingProducts` · `ListFamilies_FiltersByOrigin` · `ListFamilies_RequiresAdministrator` · `Verdict_DismissedPair_ExcludedFromNextAudit` · `Verdict_SamePairTwice_CorrectsInsteadOfDuplicating` · `test_audit_flags_member_when_stranger_beats_worst_sibling` · `test_audit_is_deterministic` · `test_judged_pairs_are_omitted` · `test_openapi_snapshot_is_stable` · `test_orphan_detection_lists_unassigned_similar_products` · `test_orphan_margin_comes_from_configuration` · `test_orphan_nomination_never_crosses_piece_type` · `test_purity_does_not_nominate` |
| **No existían** | `ListFamilies_ReturnsAtMostFiftyPerPage` · `Verdict_FailedAudit_ChangesNothing` · `test_audit_calls_no_provider` · `test_audit_writes_nothing` · `test_orphan_without_piece_type_is_never_nominated` |

---

## 5. Cuatro guardas verificadas **fallando**

Un test que no muerde no sirve, y este proyecto lleva encontrando de esos. Las tres guardas de código nuevas se mutaron una a una y se restauraron.

| Guarda | Mutación | Resultado |
|---|---|---|
| Deriva del contrato | Décima ruta añadida **antes** de regenerar el snapshot | `test_openapi_snapshot_is_stable` **falla**; tras regenerar, verde. La lista explícita de `test_snapshot_covers_the_frozen_surface` se actualizó aparte, porque el snapshot por sí solo pasaría sobre cualquier fichero regenerado sin que nadie note una ruta nueva |
| La auditoría no escribe | Añadido `_MUTANT = "UPDATE ai.product_document SET family_id = NULL"` a `families/repository.py` | `test_audit_writes_nothing` **falla**; retirado, verde |
| La puerta de `piece_type` | Sustituido `AND piece_type IS NOT NULL` por un comentario en el SQL de huérfanos | `test_orphan_without_piece_type_is_never_nominated` **falla**; restaurado, verde |
| Sin llamada al proveedor | `from jbg_ai.indexing import embeddings` añadido a `families/audit.py` | `test_audit_calls_no_provider` **falla**; retirado, verde |

Las tres últimas son guardas **sobre el código fuente** y no sobre la conducta, deliberadamente: la auditoría es de sólo lectura por construcción, así que no hay cambio de estado que observar y un test que lo vigilara pasaría sobre una base vacía para siempre. Lo que sí puede regresar es que alguien **añada** una escritura o una llamada al proveedor, y eso es lo que muerden. Es el mismo idioma que `test_no_term_list_is_declared_inside_the_families_package`, de C18a.

Un caso más, verificado fallando durante la implementación y no por mutación deliberada: **`Metrics_RejectedMemberRemovedFromItsFamily_IsStillCountedAsAMember`**. La primera versión de la métrica deducía la población del estado actual, y este test la cazó leyendo **dos candidatos y ningún miembro**. Es el origen de la columna `SubjectWasMember` y de la tercera migración.

---

## 6. Alcance negativo, verificado con `git diff` contra `ai-eng`

| Lo que **no** debía cambiar | Comprobación |
|---|---|
| `indexing/embeddings.py` | diff **vacío** (freeze de C11) |
| `indexing/source_text.py` | diff **vacío**: la plantilla no cambia; `preprocessing_id` sigue `source-text/v1` |
| `terraform/` y `.github/` | diff **vacío** |
| `frontend/src/lib/materials-vocabulary.ts` | diff **vacío** — es espejo de `materials.terms`, no de `materials.synonyms`; ver §8.2 |
| `piece_type.terms` y `prompt_version` | sin cambios: no hay salto a `enrichment/v2` |
| `vocabularies.yaml` | **una sola línea**: `+    dorado: baño de oro` |
| Revisiones nuevas de Alembic | **cero** ficheros en `migrations/versions/` |
| SQL contra el esquema `public` desde el runtime | **ninguno** en `api/`, `families/`, `indexing/` ni `retrieval/`. La auditoría lee **sólo `ai.product_document`** |
| `data/ingest.py` | diff **vacío** — sus consultas a `public` son del CLI de ingesta de C06a, ajeno a este change |
| Tabla de propuestas | **no existe**: los pares juzgados viajan en la petición y el servicio no guarda ninguno |

---

## 7. Ejecución sobre datos reales

Por el camino completo `.NET → jbg-ai → pgvector`, no por un script suelto. Detalle en [`informes/c18b-family-review-report.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c18b-family-review-report.md).

| | |
|---|---|
| Familias examinadas / pertenencias | **156 / 486** |
| Miembros marcados, y resueltos | **18** → 17 confirmados, 1 sacado (**94 %**) |
| Huérfanos nominados con θ = 0, y resueltos | **40** → 6 aceptados (**15 %**) |
| Decisiones aplicadas al catálogo | **7** — 6 altas, 1 baja |
| Pertenencias al cierre | 486 → **491** (+6 −1) · familias **156**, sin cambio |
| Índice final | 1.168 documentos · **491 con `family_id`**, que cuadra con `ProductFamilyMembers` · 473 con `variant_label` · **0 sin embedding** · un único `embedding_version` |
| Reparto por `data_origin` | **56 reales / 2 sintéticos**, sobre un corpus indexado 65 % sintético |

**Verificación a mano de los tres estados, con `jbg-ai` realmente parado** *(2026-09-01, tarea 6.6)*. No sólo con MSW, que es lo que la tarea exigía además:

| Con el servicio caído | Resultado |
|---|---|
| `POST /api/ai/catalog/family-audit` | **503** — *«The AI service is unavailable. No audit was produced.»* Nunca 200 con listas vacías |
| `GET /api/product-families` | **200**, las 156 familias — la revisión sigue operativa |
| `GET /api/ai/catalog/family-review-metrics` | **200** |

Servicio relanzado y comprobado idéntico (`version: c18b-review`, 1.168 documentos), y la auditoría vuelve a responder 200 sobre 156 familias y 491 pertenencias.

**Backfill de `SubjectWasMember`** *(2026-09-01, autorizado expresamente)*: `UPDATE 18`, dejando 18 filas en `true` y 40 en `false`. La métrica leída por el endpoint real pasa de lo que habría sido *0 de 18* a **17 de 18 miembros confirmados y 6 de 40 candidatos aceptados**, con `averageReviewSeconds: null` —nunca cero— y `pendingActions: 0`.

---

## 8. Incidencias de la implementación

### 8.1 La suite de Python llegó rota, y no se dejó pasar como preexistente

Dos tests de `retrieval` fallaban en la ejecución completa y pasaban en aislamiento. La causa no estaba en `retrieval`: **`migrations/env.py` llamaba a `fileConfig(config.config_file_name)` sin `disable_existing_loggers=False`**, y ese valor por defecto es `True`. Bajo el CLI de Alembic es inocuo porque el proceso termina justo después; **en proceso es destructivo**, y los tests de migración corren Alembic dentro del mismo intérprete que el resto de la suite, así que dejaban muertos los loggers de `jbg_ai` para todo lo que se ejecutara después.

Arreglado con el argumento explícito y **tres tests de regresión**, uno de los cuales fija que el valor por defecto *habría sido* destructivo (`test_the_default_would_have_disabled_them`), que es lo que impide que alguien lo "simplifique" de vuelta.

> **Un intento anterior se revirtió por invasivo.** La primera hipótesis fue `root.handlers.clear()` en `api/main.py`, y se llegó a cambiar. La medición demostró que ese cambio no hacía falta, y se retiró: era alcance que no tocaba.

### 8.2 Dos correcciones que el diff del sinónimo obligó a hacer sobre las tareas

- **La tarea 2.4 esperaba ver agrupados tres productos que no se agrupan.** `SKU25`, `SKU420` y `SKU90` siguen huérfanos tras el sinónimo, y no por un fallo suyo: **sus familias base ya existían**, y la regla de convergencia excluye del pool a los productos que ya pertenecen a una familia. De ahí una conclusión que refuerza el change entero — el sinónimo sólo recupera familias donde los dos miembros siguen libres, y donde la base ya se aprobó, la variante `dorado` sólo puede entrar por la cola de huérfanos. Los tres entraron por ahí.
- **La tarea 2.5 no tenía nada que hacer y su premisa era errónea.** `materials-vocabulary.ts` es espejo de `materials.terms`, no de `materials.synonyms`. `dorado` es un sinónimo y `baño de oro` ya estaba, así que el espejo no cambia — y **no debe** cambiar: el panel ofrece valores canónicos de filtro, y añadir `dorado` daría al operador un filtro que el recuperador no casa nunca.

### 8.3 El criterio de nominación se eligió al revés de lo previsto, y por medición

La hipótesis de partida era que el margen relativo dispararía de más y la pureza sería más segura. **La medición sobre el corpus dio lo contrario**: la pureza dispara sobre 55 productos sintéticos frente a 19 reales, porque los casi-duplicados sintéticos fueron construidos para ser familias distintas. El margen relativo dispara casi en exclusiva sobre huecos reales. La pureza quedó como **señal de orden y nunca de nominación**, con dos tests que lo fijan.

### 8.4 Tres huecos que sólo aparecieron al usar la pantalla de verdad

Ninguno se veía leyendo el diseño. Registrar un veredicto **no movía** la pertenencia y nada lo señalaba —58 juicios, catálogo intacto, 7 decisiones sin aplicar—; **no había forma de corregir la etiqueta** de un miembro ya dentro de una familia; y el tiempo por ítem **no se persistía**, que es la mitad del renglón del §16. Los tres entraron al alcance en lugar de irse a C28, con el grupo 6b de tareas, tres requisitos nuevos de spec y once escenarios.

### 8.5 Se destruyeron datos de revisión reales

Se ejecutó `DELETE FROM "FamilyReviewVerdicts"` sobre la base de desarrollo dando por supuesto que las 18 filas eran ruido de pruebas propio. **Eran la revisión humana en curso.** Sin archivado WAL no había recuperación posible y el trabajo hubo que rehacerlo. De ahí el compromiso, respetado en el resto del change: **ninguna escritura sobre esa base sin decirlo antes** — que es también por lo que el backfill de `SubjectWasMember` esperó a una autorización expresa en vez de ejecutarse al escribir el script.

### 8.6 Tres obstáculos de entorno, ninguno del producto

- **`CERTIFICATE_VERIFY_FAILED`** en la primera sincronización, 9 documentos de 16. No era la red —`curl` al mismo host devolvía 200— sino la confianza de certificados de la máquina. Resuelto con un bundle de `certifi` más las 183 raíces del almacén de Windows.
- **`psycopg` async no funciona con el `ProactorEventLoop`** de Windows, y fijar la política antes de `uvicorn.run()` no basta porque uvicorn monta su propio bucle. Resuelto con un lanzador que construye el bucle correcto y le entrega el servidor ya dentro; vive en el scratchpad y **no en el repositorio**, porque en producción el servicio corre sobre Linux.
- **La pantalla salía en blanco** tras entregar la ruta y el servicio. No era caché ni antivirus: **faltaba la entrada del menú lateral**.

---

## 9. Puertas del proyecto

| Puerta | Resultado |
|---|---|
| `openspec validate --all --strict` | **47 passed, 0 failed** |
| `openspec validate <change> --strict` | válido |
| Artefactos | **7/7** — `proposal`, `design`, `tasks`, `ticket`, `qa`, 4 specs delta, `baseline/` |
| Tareas | **68/68** |
| `dotnet test` (cierre) | 51 fallos preexistentes de 951, **ninguno en una clase de familia**; las siete clases de la superficie **133/133** |
| `uv run pytest` | **472 passed, 0 failed** |
| `vitest run` | 113 fallos preexistentes de 552, **los mismos 113 nombres**; los 19 propios en verde |
| `test_openapi_snapshot_is_stable` | verde tras regeneración deliberada (décima ruta) |
| Migraciones EF | **tres**, aplicadas y verificadas con 9 tests de esquema |
| Migraciones Alembic | **ninguna revisión nueva**, verificado |

---

## 10. Fuera de esta pasada (no DoD)

- **Las dos raíces degeneradas** —`Alianzas Plata/oro` y `Cadena oro/plata`, 9 SKU— **delegadas a C28 por escrito**, con el motivo: `cadena` no tiene ni una familia de su tipo contra la que calcular un margen, así que la auditoría no puede verlas. Piden dos familias manuales, y C18b lista y disuelve familias pero **no las crea**.
- **Ponderar la nominación por la cohesión de la familia destino.** Medido: la precisión va de 0 % a 100 % según a quién apunte. Exige recalibrar sobre una cola ya revisada, que es lo que este change acaba de producir y no existía al empezar.
- **La predicción de la decisión 5 del diseño queda sin comprobar.** El revisor **confirmó** el sintético `SKU610` como miembro legítimo, así que no hubo intruso que sacar y el peor hermano de esa familia no subió. No refutada: sin comprobar.
- **`ai.sync_failure` no se drena.** Sus columnas `attempts` y `next_retry_at` no las lee nadie y nada borra de la tabla. Sus 9 filas son la traza de un incidente resuelto y se dejan: vaciarlas con un `DELETE` para poner verde una casilla sería destruir el registro y llamarlo cierre.
- **El estampado del watermark sigue sin verificarse.** El segundo pase de sincronización salió con `since: null` y barrió los 1.168 documentos. El estado final es correcto y está verificado, pero un barrido completo tapa exactamente el fallo que la tarea 9.3 buscaba.
- **Los atajos de teclado de la pantalla, descopados a C28** el 2026-09-01 con nota fechada en el `design.md` y en las dos fichas del plan. La tarea 6.4 los daba por hechos y no existen; entran donde la ficha que los pide por escrito, en vez de añadirse a una pantalla ya revisada por una persona.
- **La carcasa compartida no se extrajo**, y no se extrae ahora: abstraer con un solo inquilino a la vista produce la abstracción equivocada. Tres de las cuatro cosas que C28 pide por escrito ya están en la página; extraerlas es de C28.
- **Un 4xx que emite el servicio no se distingue por tipo de una indisponibilidad.** `TranslateStatus` es compartido por todas las rutas del cliente y estrecharlo no es de este change. Ver §11.2.

---

## 11. La pasada de verificación

Recorrió los siete artefactos frente a la implementación en vez de frente al recuerdo de haberla escrito, y encontró **ocho escenarios sin un solo test**, **una tarea marcada cuyos entregables no existían**, **una carcasa prometida y no extraída**, **una premisa de diseño incumplida** y **un requisito que afirmaba algo que el código no hace**. Se arreglan aquí porque las specs delta se sincronizan a `openspec/specs/` al archivar, y **un requisito falso sincronizado sobrevive al change que lo escribió**.

### 11.1 Ocho escenarios exigidos y sin cubrir, cinco de ellos con nombre propio en `tasks.md`

El hueco mayor: **la spec delta de `ai-gateway-client` tiene ocho escenarios y no había un solo test sobre el cliente.** Es literalmente el mismo hueco que el QA de C18a encontró en su §8.5, sobre el mismo cliente y la ruta hermana. Y se explica igual: los tests de integración ejercitan el cliente a través de un doble que ya habla en tipos mapeados, así que nada allí notaría un nombre de cable que dejó de casar con el contrato congelado o un campo del candidato caído en el mapeo.

Cerrado con **`AiGatewayFamilyAuditTests`, 17 tests**, más siete repartidos entre las otras tres specs:

| Escenario | Test escrito | Dónde |
|---|---|---|
| Sin tipo de pieza no se nomina para nada | `test_orphan_without_piece_type_is_never_nominated` | `families/test_audit.py` |
| La auditoría deja el catálogo intacto | `test_audit_writes_nothing` | ídem |
| No se llama al proveedor | `test_audit_calls_no_provider` | ídem |
| Confirmar registra sin mover el catálogo | `Verdict_ConfirmingWithoutEditing_RecordsTheJudgementAndMovesNothing` | `FamilyReviewControllerTests` |
| Un veredicto caduco se muestra caduco | `Verdict_KeepsTheMarginItWasTakenAt_AndTravelsWithTheNextAudit` | ídem |
| Una auditoría fallida no cambia nada | `Verdict_FailedAudit_ChangesNothing` | ídem |
| Ejecutar un juicio no lo mueve de población | `Metrics_RejectedMemberRemovedFromItsFamily_IsStillCountedAsAMember` | ídem |
| Página de a lo sumo cincuenta | `ListFamilies_ReturnsAtMostFiftyPerPage` | ídem |

Dos merecen una línea. **`test_audit_writes_nothing` y `test_audit_calls_no_provider` son guardas sobre el fuente**, y esa forma es deliberada: no hay estado que observar en una operación de sólo lectura, y un test conductual pasaría sobre una base vacía para siempre. **`ListFamilies_ReturnsAtMostFiftyPerPage` afirma sobre el tamaño de página que el servidor reporta** en vez de sembrar cincuenta y una familias: lo que puede regresar es el `clamp`, y regresa igual con tres familias que con trescientas.

### 11.2 Un requisito de `ai-gateway-client` afirmaba una distinción que el código no hace

El escenario decía que *«el servicio rechaza la petición como inválida»* y que **el llamante puede distinguir ese resultado de que el servicio no esté disponible**. No es cierto: `TranslateStatus` traduce **cualquier** estado no exitoso que no sea 401 ni 501 a `AiUnavailableException`, con el código sólo dentro del mensaje. Un 422 y un 503 llegan al llamante como el mismo tipo.

Arreglar el código habría cambiado la conducta de **todas** las rutas del cliente —recuperación, enriquecimiento, sugerencia—, cada una con su spec archivada y sus tests. Desproporcionado para un escenario sobre una ruta. Lo que sí es cierto, y es más fuerte, es que **el cliente rechaza la petición inválida antes de enviarla**: el ámbito que no es de catálogo y el `max_orphans` fuera de rango salen por `ArgumentException` sin tocar la red.

El escenario se reescribe a eso, y el requisito gana una frase que **nombra el límite en vez de taparlo**. Se añade además un escenario que faltaba y que el código sí implementa —un cuerpo vacío es un fallo y nunca una auditoría vacía—, que en esta ruta es la diferencia entre *«no hay nada que revisar»* y *«no se sabe»*.

### 11.3 Una tarea marcada afirmaba dos entregables de pantalla que no existen

La tarea 6.4 decía *«Pantalla con **TanStack Table** … **navegación por teclado**; confirmación en bloque; y cronómetro por ítem»*. Las dos últimas están; las dos primeras no: cero referencias a TanStack Table y cero manejadores de teclado en las 920 líneas de `family-review.tsx`.

Es el **tercer caso del mismo patrón** en este change, tras los cinco nombres de test del §11.1 y los ocho escenarios sin cubrir: tareas marcadas leyendo lo que decían en vez de comprobando lo que existía.

Las dos mitades se resuelven distinto porque no son la misma clase de error:

- **TanStack Table es una elección, y la elección fue correcta.** Sólo 9 de las 85 pantallas del proyecto lo usan, y todas son listados CRUD planos; ésta tiene filas desplegables, cronómetro por fila y tres estados por lista, formas que un data grid no da y estorba. Lo que está mal es el texto de la tarea, y se corrige.
- **La navegación por teclado falta de verdad**, y está en alcance por la regla que la propia decisión 12 fija: se generaliza lo que la ficha de C28 pide por escrito, y esa ficha pide atajos de teclado. **Se descopa explícitamente a C28**, con nota fechada en el `design.md` y en las dos fichas del plan — no se añade a última hora a una pantalla ya revisada por una persona, porque la prueba que importa es volver a recorrer una cola con ella y no un test que compruebe que el manejador está enganchado.

### 11.4 La carcasa que la decisión 12 prometía no se extrajo

*«C18b construye la carcasa; C28 es el segundo inquilino.»* No se extrajo **ni un componente compartido**: todo vive en un fichero, y los únicos ficheros nuevos de `frontend/` son la página, su servicio, sus tipos, su test, la ruta y el menú.

No se arregla extrayendo ahora, y el motivo es esa misma decisión: abstraer con un solo inquilino a la vista produce la abstracción equivocada. Lo que se arregla es la frase, con una revisión fechada que dice lo que hay — **C18b construye la primera pantalla; la carcasa, si hace falta, la extrae C28 de ella** — y que anota que **tres de las cuatro cosas que C28 pide por escrito ya existen** en esa página.

### 11.5 La premisa de la decisión 5 no se cumplió

El diseño apoya el orden del change en que limpiar `Colgante estrella de mar` subirá su peor hermano de 0,778 y disolverá los falsos positivos. **No ocurrió:** el revisor confirmó `SKU610` como miembro legítimo, así que no hubo limpieza y θ se fijó igualmente en 0. Revisión fechada en D5: la predicción **no queda refutada, queda sin comprobar**, y la dispersión de esa familia resulta ser real — lo que reabre el cuantil robusto que aquel apartado anotaba como alternativa, ahora con una cola revisada contra la que calibrarlo.

### 11.6 Un test escrito en esta pasada afirmaba contra el doble y no contra el sistema

`Verdict_KeepsTheMarginItWasTakenAt_…` se escribió afirmando dos cosas: que el margen registrado sobrevive, y que el par juzgado **no vuelve a aparecer** en la auditoría siguiente. La segunda **falló al ejecutarla**, y el fallo tenía razón.

La omisión de un par juzgado la hace **el servicio**, con los pares que el cliente le envía. En un test de integración el gateway es un doble que responde desde un fixture y **no puede filtrar nada**, así que esperar que la marca desaparezca de esa respuesta era afirmar contra el doble. Habría sido peor si hubiera pasado: un test verde que no comprueba nada, que es exactamente el hallazgo que el §11.1 acaba de corregir ocho veces.

Corregido a lo que este lado sí posee —**el par viaja en la petición**, comprobado sobre `gateway.LastRequest.JudgedPairs`— y con la omisión referida a `test_judged_pairs_are_omitted_from_both_lists`, que es donde ocurre. La frontera importa: .NET recuerda los juicios y los envía, el servicio los omite.

---

## Veredicto

**Listo para archivar.** Los **54** escenarios de las cuatro specs tienen test nombrado; las tres suites no registran ninguna regresión atribuible al change comparadas por nombre —y el frontend cierra exacto, 113 = 113—; el alcance negativo está verificado con `git diff`; las cuatro guardas se comprobaron **fallando**; y el camino del dato se ejecutó de verdad, con 58 juicios humanos, 7 decisiones aplicadas y un índice reconciliado a 491 pertenencias.

**Sin huecos abiertos.** Los ocho del §11.1 se cerraron con test; la divergencia del §11.2 corrigiendo el requisito en vez del código; y las tres del §11.3 al §11.5 con revisiones fechadas que dicen lo que hay, más un descope explícito a C28. Ninguna se resolvió reescribiendo un documento para que cuadrara sin decirlo. Lo que queda fuera es alcance de otros changes y está en el §10.

Cuatro cosas de esta pasada merecen sobrevivir al change:

**El hueco del cliente tipado se repitió exactamente.** C18a lo encontró en su §8.5, sobre el mismo cliente y la ruta hermana; C18b lo repitió sobre la ruta nueva. Dos veces seguidas no es descuido, es que la cobertura por integración **parece** cubrir el cliente y no lo hace. Merece ser lo primero que se mire en C28.

**Tres veces se marcó una tarea leyendo lo que decía, no comprobando lo que existía.** Cinco nombres de test que vivían en `tasks.md` y en ningún fichero, ocho escenarios de spec sin cubrir, y una tarea de pantalla que afirmaba una librería que no se usa y unos atajos de teclado que no existen. El §4 de este documento existe para que el primer caso no vuelva a pasarse por alto; los otros dos dicen que la comprobación tiene que alcanzar también a lo que una tarea promete en prosa.

**Un test escrito para cerrar un hueco casi abrió otro.** El del §11.3 afirmaba contra el doble de gateway en vez de contra el sistema, y sólo se supo porque falló. Un test de integración con un doble que responde desde un fixture puede comprobar lo que el sistema envía, nunca lo que el servicio decide con ello — y confundir las dos cosas produce verde sin evidencia, que es la misma enfermedad que esta pasada vino a curar.

**Y lo más caro del change no lo encontró ningún test, sino usar la pantalla.** Los tres huecos del §8.4 y la columna `SubjectWasMember` salieron de revisar 58 pares de verdad, no de leer el diseño. Es el argumento para que un change de intervención humana **se ejecute con un humano** antes de darse por cerrado.
