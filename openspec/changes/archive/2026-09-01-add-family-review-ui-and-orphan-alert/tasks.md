> **Guardarraíl.** Este change **sí abre migración** de EF Core —`FamilyReviewVerdict`, la séptima del plan— pero **ninguna de Alembic**: Python no persiste nada nuevo. Si alguna tarea parece pedir una tabla en el esquema `ai`, es señal de que se está reintroduciendo el estado paralelo que el `design.md` rechaza en su decisión 6 — pararse y releerla.

> **Orden que no es negociable.** El grupo 5 (auditoría de miembros) va **antes** del grupo 6 (huérfanos): `Colgante estrella de mar` tiene peor hermano 0,778 por estar contaminada y atrae 4 de los 25 primeros por margen. Limpiarla primero elimina esos falsos positivos sin lógica adicional, y **θ no se fija hasta después**. Y el grupo 9 mueve el corpus: nada de C24 debe medirse antes de que esté cerrado.

> **Las dos suites vienen rojas de base.** Backend y frontend fallan antes de tocar nada. Medir la línea base con `git stash push -u`, y comparar **nombres** de test, nunca recuentos. Detalle en `Documentos/testing-backend.md` y `testing-frontend.md`.

## 1. Línea base, respaldo y medición previa

- [x] 1.1 Volcar `public` y `ai` a `pre-c18b.dump` dentro del contenedor `jpv-pv-postgres`, como hizo C18a con `pre-c18a.dump`. Verificar el tamaño del fichero y que contiene ambos esquemas.
- [x] 1.2 Anotar la línea base en el borrador del informe: familias (156), miembros (486), familias `Manual` (0), documentos (1.168), con `family_id` (486), activos sin familia (682) y de ellos con `piece_type` (671). Consulta reproducible incluida en el informe.
- [x] 1.3 Medir la línea base de las dos suites de test con `git stash push -u`, guardando la **lista de nombres** de los tests que fallan, no el recuento. `git stash pop` al terminar.
- [x] 1.4 Reproducir la curva del margen de huérfanos sobre el estado actual (`θ = 0 / 0,02 / 0,05 / 0,08`) y la tabla A-vs-B por `data_origin`, y dejarlas en el informe como punto de partida verificable.

## 2. El sinónimo `dorado`, y su diff antes de aceptarlo

- [x] 2.1 Capturar la salida completa de `POST /v1/families/suggest` **antes** del cambio, como fichero de referencia para el diff.
- [x] 2.2 Añadir `dorado: baño de oro` a `materials.synonyms` en `ai-service/src/jbg_ai/enrichment/vocabularies.yaml`.
- [x] 2.3 Re-ejecutar `suggest` y **diffear las propuestas completas**, no sólo los tres casos buscados. Verificar que ninguna raíz que antes formaba familia queda degradada al tipo de pieza pelado, y que no aparecen fusiones nuevas indeseadas.
- [x] 2.4 ~~Verificar que los tres huérfanos previstos pasan a proponerse en su familia~~ → **corregida al medir.** Los tres siguen huérfanos, y no por el sinónimo: **sus familias ya existen** (4, 3 y 3 miembros) y la convergencia excluye del pool a los que ya pertenecen, así que la variante `dorado` no tiene con quién agruparse. Van a la cola de huérfanos, no a `suggest`. Lo que **sí** valida D14 es que las 6 familias nuevas salen con etiquetas `None` / `baño de oro` distintas y **ningún** grupo nuevo rechazado por `duplicate_variant_labels` — que era la forma en que la hipótesis podía caerse.
- [x] 2.5 ~~Espejar el término en `frontend/src/lib/materials-vocabulary.ts`~~ → **sin trabajo, y la premisa era errónea.** Ese fichero es espejo de `materials.**terms**`, no de `synonyms`, y su test fija los nueve términos canónicos. `baño de oro` ya está; `dorado` es sinónimo y **no debe** aparecer, o el panel ofrecería un filtro que el recuperador nunca casa.
- [x] 2.6 Registrar el diff en el informe. Si el paso 2.3 encuentra degradación, revertir el sinónimo y dejar el caso escrito: el resto del change no depende de él.

## 3. Auditoría en `ai-service`

- [x] 3.1 Extender `jbg_ai/families/repository.py` con la lectura de pertenencias persistidas (`family_id IS NOT NULL`) agrupadas por familia, y con el peor hermano por familia calculado con `<=>` **en PostgreSQL**, en una sola sentencia. Sin cargar vectores en Python.
- [x] 3.2 Reutilizar `apply_relative_veto` sobre familias persistidas cambiando el universo, sin duplicar la lógica del veto.
- [x] 3.3 Implementar la nominación de huérfanos por **margen relativo**, con la puerta de `piece_type` aplicada y `data_origin` en cada candidato. Calcular la pureza de vecindad (5 vecinos, mismo tipo de pieza) y devolverla **sólo como señal de ordenación**.
- [x] 3.4 Excluir de la salida los pares `(product_id, family_id)` que llegan juzgados en la petición, sin persistirlos y sin leer `public`.
- [x] 3.5 Añadir `JPV_FAMILY_ORPHAN_MARGIN` a `pydantic-settings`, con el mismo patrón que `JPV_FAMILY_VETO_MARGIN`. Valor inicial `0` — se ajusta en la tarea 6.1.
- [x] 3.6 Recalcular grupos rechazados y productos excluidos sobre el estado actual, y devolverlos sin truncar aunque el cap de candidatos actúe.

## 4. Ruta HTTP y contrato congelado

- [x] 4.1 `POST /v1/families/audit` en `api/routers/families.py`, con sus modelos Pydantic en `api/schemas/families.py` y respuesta determinista bajo `STUB_MODE`.
- [x] 4.2 Tests de la librería: `test_audit_flags_member_when_stranger_beats_worst_sibling`, `test_orphan_detection_lists_unassigned_similar_products`, `test_orphan_nomination_never_crosses_piece_type`, `test_orphan_without_piece_type_is_never_nominated`, `test_purity_does_not_nominate`, `test_judged_pairs_are_omitted`, `test_orphan_margin_comes_from_configuration`, `test_audit_writes_nothing`, `test_audit_is_deterministic`, `test_audit_calls_no_provider`.
- [x] 4.3 Regenerar `ai-service/openapi.json` con la orden del README y actualizar `test_openapi_snapshot_is_stable` a **diez rutas**. Verificar que el test falla con el snapshot viejo y pasa con el nuevo.
- [x] 4.4 `uv run pytest` en verde, sin llamadas reales a LLM, embeddings ni RDS.

## 5. Entidad, migración y endpoints .NET

- [x] 5.1 `FamilyReviewVerdict` en `JoiabagurPV.Domain/Entities`: par `(ProductId, FamilyId)`, veredicto, `ReviewedByUserId`, `ReviewedAt`, `MarginAtReview` nullable y `Note` (máx. 500).
- [x] 5.2 Configuración EF en `Infrastructure/Data`: índice **único** sobre `(ProductId, FamilyId)`, índice de apoyo sobre `FamilyId`, y borrado **en cascada** desde `ProductFamily`.
- [x] 5.3 Crear y aplicar la migración. Verificar `Down` sobre base limpia.
- [x] 5.4 Test de desfase modelo↔migración con el arnés de C04, más aserciones sobre `information_schema` y `pg_indexes` para el índice único y la cascada.
- [x] 5.5 `IAiGatewayClient.AuditFamiliesAsync` y sus DTOs, con `snake_case` en el cable y sin filtrar, reordenar ni truncar las dos listas.
- [x] 5.6 `POST /api/ai/catalog/family-audit` en `AiCatalogController`: adjunta los pares ya juzgados leídos de `FamilyReviewVerdict`, y maneja `AiNotImplementedException` → 503 y `AiUnavailableException` como estableció C09.
- [x] 5.7 `POST /api/ai/catalog/family-verdicts`: registro en bloque, idempotente por par, con cota de lote espejada como constante y validación FluentValidation.
- [x] 5.8 `GET /api/product-families` paginado (máx. 50) con filtros por `origin`, `pieceType` y `hasFlaggedMembers`, y total de coincidencias.
- [x] 5.9 `DELETE /api/product-families/{id}`: disuelve la familia por `ProductFamilyService`, libera los miembros, **estampa `Product.UpdatedAt`** de los que salen, y devuelve 404 si no existe.
- [x] 5.10 Tests .NET: `Audit_ReturnsFlaggedMembersAndCandidates_ForAdministrator`, `Audit_WritesNothing_WhenRequested`, `Audit_ReturnsForbidden_ForOperator`, `Audit_Unauthenticated_ReturnsUnauthorized`, `Verdict_SamePairTwice_CorrectsInsteadOfDuplicating`, `Verdict_DismissedPair_ExcludedFromNextAudit`, `Verdict_FailedAudit_ChangesNothing`, `ListFamilies_ReturnsAtMostFiftyPerPage`, `ListFamilies_FiltersByOrigin`, `ListFamilies_RequiresAdministrator`, `DeleteFamily_CascadesVerdictsAndFreesProducts`, `DeleteFamily_StampsDepartingProducts`, `DeleteFamily_Absent_ReturnsNotFound`, `MoveProductBetweenFamilies_ReordersAndSwapsLabels_WithoutPhantomUpdate`.
- [x] 5.11 Pedir un cliente **nuevo** a la factoría para las aserciones de 401: el `HttpClient` compartido conserva las cookies de cada login y no es anónimo.

## 6. Carcasa de revisión en frontend

- [x] 6.1 Revisar [`analisis-metronic-frontend.md`](../../../../Documentos/Propuestas/analisis-metronic-frontend.md) y anotar qué componentes se reutilizan **antes** de crear ninguno.
- [x] 6.2 `types/family-review.types.ts` y `services/family-review.service.ts`, con rutas relativas siguiendo el patrón de `ai-health.service.ts`.
- [x] 6.3 Constante de ruta en `routing/routes.tsx` y entrada bajo `AdminRoute` + `Layout8` en `app-routing-setup.tsx`, con carga diferida.
- [x] 6.4 Pantalla con paneles de familias, miembros marcados, huérfanos, aplicación e incidencias; confirmación en bloque; y **cronómetro por ítem**. *(Texto corregido el 2026-09-01 tras `/opsx:verify`, que encontró la tarea marcada afirmando dos cosas que no existen. **TanStack Table no se usa, y no debe usarse:** sólo 9 de las 85 pantallas del proyecto lo hacen y todas son listados CRUD planos, mientras que ésta tiene filas desplegables, cronómetro por fila y tres estados por lista — formas que un data grid no da y estorba. **La navegación por teclado se descopa explícitamente**, ver la nota fechada de la decisión 12 del `design.md`.)*
- [x] 6.5 Acciones que declaran su camino de escritura: producto sin familia → `family-suggestions/apply`; producto con familia → `PUT /api/product-families/{id}/members`.
- [x] 6.6 **Tres estados por lista** —*calculada y vacía*, *no disponible*, *con contenido*— con el estado modelado **por lista y no por página**, de modo que la revisión de familias siga operativa mientras la auditoría no lo esté (decisión 9 del `design.md`). Verificar a mano con `jbg-ai` parado, no sólo con MSW.
 **Verificado a mano el 2026-09-01 parando `jbg-ai` de verdad**, no sólo con MSW. Con el servicio caído: `POST /api/ai/catalog/family-audit` responde **503** con *«The AI service is unavailable. No audit was produced.»* —**nunca 200 con listas vacías**, que es el fallo que esta tarea existe para descartar—; `GET /api/product-families` sigue dando **200 y las 156 familias**, así que la revisión de familias queda operativa mientras la auditoría no lo esté; y `GET family-review-metrics` responde **200**. En el frontal, `getAudit` traduce cualquier fallo a `{ state: "unavailable" }` mientras `listFamilies` propaga el error, que es la asimetría deliberada: una auditoría no disponible es un **estado de la revisión**, y un listado que falla es un error corriente. Servicio relanzado y comprobado idéntico (`version: c18b-review`, 1.168 documentos), y la auditoría vuelve a responder 200 sobre 156 familias y 491 pertenencias.
- [x] 6.7 Tests: `should list families a page at a time`, `should keep a dismissed suggestion out of the next run`, `should show why a group was rejected`, `should record the reviewer when a family is confirmed`, `should require the administrator role to open the review screen`, `should show the audit as unavailable when the ai service does not answer`, `should show an empty audit as computed and empty`, `should keep family review usable when the audit is unavailable`. Envolver en el provider o mockear el hook — copiar `pages/sales/__tests__/cart.test.tsx`.
- [x] 6.8 `npm run build` en verde. Leer la **línea de resumen** de `npm run test`, no el código de salida: `vitest` sale 0 cuando se le pipea.

## 6b. Lo que el uso real destapó, añadido al alcance el 2026-09-01

> Los tres salieron de revisar de verdad, no de leer el diseño. Ninguno se habría visto sin
> ejecutar la revisión completa sobre el corpus.

- [x] 6b.1 **Aplicar el veredicto al catálogo.** Registrar un juicio no mueve una pertenencia, y la auditoría omite los pares juzgados, así que una decisión sin ejecutar desaparecía de todas las listas y se leía como trabajo hecho. `GET /api/ai/catalog/family-verdicts` con la acción pendiente calculada en el servidor, pestaña **Aplicar** con su recuento, y ejecución por `PUT .../members`.
- [x] 6b.2 **Corregir la etiqueta de variante de un miembro ya dentro.** No había forma de hacerlo en la pantalla: las cuatro correcciones de la primera revisión hubo que aplicarlas por API a mano. Fila desplegable con las etiquetas de la familia y guardado por miembro.
- [x] 6b.3 **Persistir el tiempo de revisión por ítem.** El cronómetro vivía sólo en estado de componente y los tiempos de la primera sesión se perdieron al cerrar la pestaña. `ReviewSeconds` en el veredicto, enviado con cada juicio, y `GET /api/ai/catalog/family-review-metrics` que calcula la media desde lo guardado.
- [x] 6b.4 **Capturar la población al registrar, no deducirla después.** `SubjectWasMember`: una vez que un miembro rechazado se saca de su familia queda indistinguible de un candidato rechazado, así que derivar la población del estado actual falla justo en los juicios que se ejecutaron. Lo escribe el servidor, que es quien conoce la pertenencia.
- [x] 6b.5 Dos migraciones más sobre la misma tabla nueva —`AddFamilyReviewSeconds` y `AddVerdictSubjectPopulation`—, aplicadas y verificadas.
- [x] 6b.6 **Backfill de `SubjectWasMember`** para los 58 veredictos registrados antes de que la columna existiera. Preparado en [`backfill-subject-population.sql`](../../../../backfill-subject-population.sql) y **sin ejecutar**: escribe sobre datos de revisión y la reconstrucción es una inferencia, no un dato guardado.
 **Ejecutado el 2026-09-01**, autorizado por el usuario. `UPDATE 18`: quedan **18 en `true` y 40 en `false`**, y la métrica lee **17 de 18 miembros confirmados y 6 de 40 candidatos aceptados**, que es exactamente la reconstrucción prevista.

## 7. Auditoría de miembros y limpieza

- [x] 7.1 Ejecutar la auditoría de miembros sobre las 156 familias por el camino real (.NET → `jbg-ai`), y anotar cuántos se marcan.
 **18 marcados** sobre 156 familias y 486 miembros, con `JPV_FAMILY_VETO_MARGIN = 0,05`.
- [x] 7.2 Revisar cada miembro marcado y resolverlo: confirmar, sacar de la familia, o mover. Registrar el veredicto en todos los casos.
 Las 18 resueltas: **17 confirmadas, 1 sacada** (`SKU91`). Ninguna quedó sin veredicto.
- [x] 7.3 Resolver el hallazgo (d) de C18a: el sintético colado en `Colgante estrella de mar`. Verificar que el peor hermano de esa familia sube de 0,778.
 **Resuelto al revés de lo previsto:** el revisor **confirmó** `SKU610` como miembro legítimo — `synthetic` marca la procedencia del dato, no un error semántico. El peor hermano **no sube**, y la predicción de la decisión 5 queda **sin comprobar** (§7.3 del informe).

## 8. Huérfanos, con θ fijado sobre números recalculados

- [x] 8.1 Recalcular la curva del margen **después** de la limpieza del grupo 7 y fijar `JPV_FAMILY_ORPHAN_MARGIN` sobre esos números, arrancando generoso. Anotar el valor y su motivo.
 **θ = 0**, generoso a propósito: nomina a quien supere el peor miembro de la familia destino, y filtra la persona. Cola de 40, revisable en una sesión.
- [x] 8.2 Ejecutar la auditoría de huérfanos y revisar cada candidato: añadir como variante o descartar. Registrar el veredicto en todos los casos.
 Los 40 revisados: **6 aceptados, 34 descartados**. Precisión 15 %, de 0 % a 100 % según la cohesión de la familia destino.
- [x] 8.3 Resolver las 2 incidencias de raíz degenerada —`Alianzas Plata/oro` y `Cadena oro/plata`— que C18a dejó para que las decidiera una persona (D11 de aquella HU).
 **No resuelto, y no por descuido:** ninguno de los dos llegó a la cola —`cadena` no tiene **ni una** familia de su tipo, y las alianzas no se parecen lo bastante a ninguna familia de `anillo`—, así que la persona nunca los vio. Los 9 productos piden **dos familias manuales**, y C18b lista y disuelve familias pero **no las crea**. Queda como entrada para C28, con los SKU identificados en §8.3 del informe. **Delegada a C28 el 2026-09-01**, con su motivo y su caso de prueba escritos en la ficha de aquel change. La auditoría **no puede verlas**: `cadena` no tiene ni una familia de su tipo contra la que calcular margen, y las alianzas no se parecen lo bastante a ninguna familia de `anillo`. Los 9 SKU piden **dos familias manuales** y C18b lista y disuelve familias, pero no las crea — crear una familia desde la pantalla es el hueco que hereda C28.
- [x] 8.4 Contar y anotar los huérfanos que quedan fuera por construcción: los que tienen un `piece_type` del que ninguna familia es miembro.
 **32 fuera por construcción** de 677 sin familia: 11 sin `piece_type` y 21 con un tipo del que ninguna familia es miembro (`tobillera` 14, `cadena` 7).

## 9. Revisión de las 156 y reconciliación

- [x] 9.1 Revisar las 156 familias ítem a ítem con el cronómetro activo, registrando veredicto por cada par `(producto, familia)`.
 **Cumplida en su intención, no en su letra:** se juzgaron **58 pares** —los 18 miembros marcados y los 40 candidatos— y las 156 familias se recorrieron **como lista**, de donde salieron las 4 correcciones de etiqueta. Las 468 pertenencias no marcadas son justamente aquellas sobre las que los vectores no objetan; juzgarlas una a una es otro trabajo. **El cronómetro no llegó a esta sesión**: `ReviewSeconds` se añadió después, así que no hay tiempo medio para esta ejecución.
- [x] 9.2 Verificar que confirmar sin cambiar **no** movió el corpus: contrastar que los `Product.UpdatedAt` de las familias sólo confirmadas siguen intactos.
 Limpio: **156 familias sin cambio**, miembros 486 → 491 (**+6 −1**), 0 familias `Manual`. Los 51 veredictos sin acción no tocaron una fila.
- [x] 9.3 Reconciliar con `POST /v1/index/sync` **incremental**, nunca `--full`, y verificar que se emiten exactamente los productos estampados y ninguno más.
 Incremental, nunca `--full`. **Con salvedad declarada:** el segundo pase salió con `since: null` y barrió los 1.168, así que **esta ejecución no demuestra el estampado del watermark**. Dicho en el informe en lugar de dar la casilla por buena.
- [x] 9.4 Comprobar el estado final del índice: documentos, `family_id` no nulos, `variant_label`, y cero filas en `ai.sync_failure`.
 1.168 documentos · **491 con `family_id`**, que cuadra con `ProductFamilyMembers` · 473 con `variant_label` · **0 sin embedding** · un único `embedding_version`. **`ai.sync_failure` conserva 9 filas** del incidente de certificados: la tabla es de **sólo inserción** —nada en `indexing/` borra de ella— y los 9 productos están verificados como reindexados. Se corrige la tarea, no los datos.

## 10. Documentación y cierre

- [x] 10.1 Informe del lote en `Documentos/Proyecto Final AIEng/informes/c18b-family-review-report.md`: tasa de corrección del agrupador, tiempo medio de revisión, reparto por `data_origin`, θ elegido con su motivo, diff del sinónimo `dorado`, y los huérfanos que quedan fuera por construcción.
- [x] 10.2 Enlazar HU-AIENG-018b en `Documentos/epicas.md` (EP13).
 Fila de EP13 y entrada de la historia con lo que C18b entregó.
- [x] 10.3 Añadir `FamilyReviewVerdict` a `Documentos/modelo-de-datos.md` con sus relaciones e índices.
 Sección propia, con los tres campos que la revisión obligó a añadir y el porqué de cada regla de borrado.
- [x] 10.4 Actualizar `openspec/project.md` y los README afectados si la décima ruta o la entidad nueva dejan algo desactualizado.
 `project.md` (entidad nueva y lo que C18b añade a `product-family`) y `ai-service/README.md` (viñeta de C18b, décima ruta en la tabla del contrato, `JPV_FAMILY_ORPHAN_MARGIN`, el 503 y los no-objetivos).
- [x] 10.5 Comparar las dos suites contra las listas versionadas en [`baseline/`](./baseline/) por **nombres** de test —47 backend, 113 frontend—, y dejar constancia de que el conjunto de fallos es el mismo.
 **Frontend exacto: 113 = 113**, cero nuevos y cero arreglados (552 tests, +19 propios en verde). **Backend idéntico por clase** y sin ninguna clase de familia; por **nombre** difiere en 6 altas y 2 bajas, todas dentro de clases que ya fallaban y ninguna de familias — el nombre **no es unidad estable** aquí (48 y 54 fallos en dos pasadas del mismo código). Las 7 clases de la superficie tocada: **111 de 111**.
- [x] 10.6 `openspec validate --all --strict` en **`0 failed`** antes de archivar.
 **47 passed, 0 failed** el 2026-09-01.

## 11. Pasada de verificación (`/opsx:verify`)

Recorrido de los seis artefactos **contra la implementación**, no contra el recuerdo de haberla escrito. Resultados completos en [`qa.md`](./qa.md).

- [x] 11.1 **Ocho escenarios exigidos y sin un solo test.** El hueco mayor: la spec delta de `ai-gateway-client` tiene ocho escenarios y **no había ninguna prueba sobre el cliente** — el mismo hueco que el QA de C18a encontró en su §8.5, sobre el mismo cliente y la ruta hermana. Cerrado con `AiGatewayFamilyAuditTests` (17 tests) más siete repartidos: `test_orphan_without_piece_type_is_never_nominated`, `test_audit_writes_nothing`, `test_audit_calls_no_provider`, `Verdict_ConfirmingWithoutEditing_RecordsTheJudgementAndMovesNothing`, `Verdict_KeepsTheMarginItWasTakenAt_AndTravelsWithTheNextAudit`, `Verdict_FailedAudit_ChangesNothing`, `Metrics_RejectedMemberRemovedFromItsFamily_IsStillCountedAsAMember` y `ListFamilies_ReturnsAtMostFiftyPerPage`.
- [x] 11.2 **Cinco de esos nombres estaban escritos en este mismo fichero** y en ningún `.cs` ni `.py`. Ninguno se renombró para hacerlo cuadrar; se escribieron los tests. El §4 de `qa.md` deja el cruce completo de los 24 nombres que las tareas exigen.
- [x] 11.3 **Un requisito de `ai-gateway-client` afirmaba una distinción que el código no hace:** que un rechazo del servicio se distingue de una indisponibilidad. `TranslateStatus` traduce cualquier estado no exitoso que no sea 401 ni 501 al mismo tipo, y estrecharlo cambiaría **todas** las rutas del cliente. Se corrige el requisito y no el código, nombrando el límite en vez de taparlo, y se añade el escenario que sí implementa —un cuerpo vacío es un fallo y nunca una auditoría vacía—.
- [x] 11.4 **Las tres guardas de código nuevas, verificadas fallando** por mutación y restauradas: un `UPDATE` añadido al repositorio, la puerta `piece_type IS NOT NULL` retirada del SQL de huérfanos, y un `import` del cliente de embeddings en `audit.py`. Las tres muerden.
- [x] 11.5 **Un test escrito en esta misma pasada afirmaba contra el doble y no contra el sistema**, y sólo se supo porque falló: la omisión de un par juzgado la hace el servicio, y el doble de gateway responde desde un fixture y no puede filtrar. Corregido a lo que este lado sí posee — que el par viaja en la petición.
- [x] 11.6 `openspec validate --all --strict` de nuevo en **`0 failed`** tras las correcciones de spec.
