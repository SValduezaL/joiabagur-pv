# QA — C34 `add-dotnet-assist-and-recommendation-endpoints`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados y su evidencia.
> **Fecha:** implementación del **2026-09-21** al **2026-09-22** · **Rama:** `c34-add-dotnet-assist-and-recommendation-endpoints` · **Artefactos de partida:** `6030aa3`, árbol limpio · **Implementación commiteada en `eb44711`** (51 ficheros, +6.162 / −211) y **este QA en `d6a740f`**, que es el commit desplegado en la demo. La ampliación del §13 y sus cambios de documentación quedaron commiteados en **`fd554c9`**, que **no toca una sola línea de código**: el árbol desplegado en la demo y la punta de la rama tienen el mismo `backend/`, así que lo verificado allí vale para lo que se archiva.
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **50/50 tareas**. Las dos últimas —11.3 y 11.4— las ejecutó el desarrollador en el entorno el 2026-09-22, con la evidencia en el §13. DoD del ticket: **20 de 20** casillas cumplidas con evidencia (§12).
> **Este change NO mueve el contrato:** `ai-service/openapi.json` tiene el mismo `sha256` al empezar y al terminar, y el commit no toca `ai-service/` (§8).
> **Este change llama a un proveedor real una vez**, para la medición de latencia (§9): 81 peticiones, **262.737 tokens de entrada y 30.903 de salida**, del orden de **0,06 USD** a precio de lista de `gpt-4o-mini`.
> **Lo que esta pasada encontró:** un doble de test de C03 que **no simula el fallo que su nombre dice**, que `coverlet` **no instrumenta el ensamblado `Application`** en este repositorio, una carrera de reloj no registrada en la suite, que el MITM de Norton **no alcanza a Docker**, y **siete defectos míos** —uno de test, dos de método, dos de herramienta de shell y dos de redacción—, todos corregidos, tres de ellos (§10.6, §10.10 y §10.11) cazados al redactar este mismo QA. Detalle en el §10.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| .NET | **SDK 10.0.303** · Windows 11 · Git Bash y PowerShell |
| Docker | **29.7.2**. Testcontainers levanta `postgres:15` por clase de integración |
| PostgreSQL de integración | Testcontainers + Respawn, el `ApiWebApplicationFactory` del repositorio |
| PostgreSQL de la medición | La base de desarrollo local (`jpv-pv-postgres`, puerto 5433), con el mundo sembrado e índice completo: **1.168** `ai.product_document` y **161** `ai.knowledge_chunk`, todos con *embedding* |
| `jbg-ai` en la suite | **Nunca**: cada test sustituye el gateway por un doble o por un `FakeHttpMessageHandler` bajo el *pipeline* real |
| `jbg-ai` en la medición | Imagen **reconstruida** desde el árbol de la rama (la local tenía dos semanas), `STUB_MODE=false`, proveedor real (§9) |
| TLS | El MITM de Norton **no intercepta** el tráfico de los contenedores: comprobado, §9.1. Sin `SSL_CERT_FILE` |
| `ai-service` (pytest) | **No ejecutado**: el diff no toca `ai-service/` (§8). La suite de Python no puede haber cambiado |
| Frontend | **No ejecutado**: `frontend/` fuera del diff (§8) |
| Contrato | `openapi.json` **no regenerado**; `sha256` comparado en las dos puntas (§8) |
| Migraciones | **Ninguna**: el commit no toca `JoiabagurPV.Infrastructure/`; `MigrationModelDriftTests` en verde en las dos corridas |

---

## 1. Suites automáticas

La línea base se midió **antes de tocar una línea de código**, sobre el árbol limpio en `6030aa3`.
`git stash push -u` respondió *«No local changes to save»* y `git stash pop` *«No stash entries
found»*: el `stash` que pide la tarea 1.1 fue un no-op, que es exactamente lo correcto en un árbol
limpio. La suite de backend **viene en rojo de fábrica**, como documenta `CLAUDE.md`: el recuento
no dice nada y lo que se compara son **nombres**.

| Ejecución | Resultado |
|---|---|
| **Línea base** (`6030aa3`, árbol limpio, suite completa) | **1.060 tests · 46 en rojo · 1.014 en verde** · 7 min 29 s |
| Gateway y contrato, tras los grupos 2 y 3 (`AiGatewayAssistTests`, `AiContractSnapshotTests`, `AiGatewayRegistrationTests`, `AiGatewayClientTests` y el resto de `AiGateway*`) | **109 / 0** en 782 ms — el test de timeout real incluido, gracias al `FakeTimeProvider` (§10.4) |
| Mutación de contrato sobre `AiSimilaritySignals.StyleSimilarity` | **1 en rojo, el esperado** (§6), revertida |
| Las cuatro clases de integración con los dobles migrados (grupo 4) | **53 / 0** en 51 s |
| Servicios, resolvedor, opciones y validadores, **primera ejecución** | **115 / 0** en 1 s |
| Dos mutaciones sobre `SalesAssistService` | **2 en rojo, los esperados** (§6), revertidas |
| Integración de C34, **primera ejecución** | **1 en rojo de 30** — una aserción mía equivocada (§10.1) |
| Integración de C34 tras corregirla, junto con los tests de C15 | **85 / 0** en 56 s |
| **Cierre** (suite completa) | **1.239 tests · 46 en rojo · 1.193 en verde** · 16 min 52 s |
| Los cuatro nombres que rotaron, aislados, más el test añadido tras el cierre | **5 / 0** en 17 s |
| Comprobación final: las clases de C34 y las de C15 | **268 / 0** en 50 s |
| Corrida de cobertura (§7) | **216 / 0** en 43 s |
| `openspec validate --all --strict` | **60 passed / 0 failed** al empezar, tras cambiar `config.yaml` y al cerrar |
| `openspec validate add-dotnet-assist-and-recommendation-endpoints --strict` | `Change '…' is valid` |

> La fila en rojo de la primera integración se deja escrita a propósito. Un QA que sólo enseña la
> pasada final describe un trabajo que no ocurrió.

### 1.1. La comparación por nombres, que es la que vale

Los nombres se extrajeron de los `.trx` de las dos corridas completas
(`--logger "trx;LogFileName=…"`), se normalizaron las entidades XML y se compararon como conjuntos.

```text
LÍNEA BASE   1060 nombres, 46 en rojo
CIERRE       1239 nombres, 46 en rojo
nombres de la línea base ausentes al cierre   →  0
nombres nuevos                                →  179
nombres nuevos en rojo                        →  0
entran en rojo                                →  4
salen del rojo                                →  4
```

| Entran en rojo al cierre | Salen del rojo al cierre |
|---|---|
| `InventoryIntegrationTests.Admin_AccessCentralizedInventory_ShouldSucceed` | `InventoryIntegrationTests.AssignProduct_WithNonExistentProduct_ShouldReturnNotFound` |
| `InventoryIntegrationTests.GetStock_WithNonExistentPOS_ShouldReturnEmpty` | `InventoryIntegrationTests.MovementHistory_WithPagination_ShouldReturnPagedResults` |
| `InventoryIntegrationTests.MovementHistory_WithDateRangeFilter_ShouldFilterCorrectly` | `InventoryIntegrationTests.ProductCatalog_AsAdmin_ShouldSeeAllProducts` |
| `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct` | `InventoryIntegrationTests.StockValidation_WithLowStockAfterSale_ShouldReturnWarning` |

**Por qué ninguno es de C34, con evidencia y no por descarte:**

1. **Los cuatro pasan ejecutados aislados sobre el árbol con C34**: `5 / 0` (fila 11 de la tabla).
2. **Los tres de `InventoryIntegrationTests` son la rotación documentada**:
   [testing-backend.md](../../../../Documentos/testing-backend.md) registra que la clase *«baraja los suyos
   de una vez a otra»*. El commit no toca inventario.
3. **`Update_WithValidData_ShouldReturnUpdatedProduct` falla por el reloj.** El mensaje es *«Expected
   updated.UpdatedAt to be on or after <2026-09-21 21:40:13.279962>, but found <2026-09-21
   21:40:13.279326>»*: `UpdatedAt` sale **0,6 ms antes** que `CreatedAt`, en `ProductsController`,
   que el commit no toca. No estaba en el inventario de fallos conocidos: queda anotado (§10.9).

### 1.2. Desglose de los nuevos, y la aritmética cierra

| Clase | Nuevos | Tipo |
|---|---|---|
| `SalesAssistServiceTests` | **41** al cierre (+1 después) | servicio con dobles |
| `SalesAssistConfigurationTests` | **39** | opciones, arranque, validadores, forma del cable |
| `AiSalesAssistControllerTests` | **27** | integración, doble del gateway comprobado |
| `AiGatewayAssistTests` | **19** | *pipeline* real, socket falso |
| `SubstitutesServiceTests` | **19** | servicio con dobles |
| `PitchPlaceholderResolverTests` | **16** | unidad pura |
| `AiContractSnapshotTests` | **11** (de 15 a 26) | contrato contra `openapi.json` |
| `AiGatewayRegistrationTests` | **3** (de 7 a 10) | arranque |
| `AiSalesAssistRateLimitTests` | **3** | integración, host propio con límite 2 |
| `AiGatewayClientTests` | **1** (`SearchAsync_When422_StillThrowsUnavailable`) | *pipeline* real |
| **Total al cierre** | **179** | |

`1.060 + 179 = 1.239`, exacto. El test 180º, `SalesAssist_KnowledgeNotCovered_IsPassedThrough`, se
añadió **después** de la corrida de cierre, cuando la trazabilidad del escenario 2 de la HU mostró que
faltaba, y pasó aislado y en la comprobación final de 268.

### 1.3. Los de integración llegan al gateway, a diferencia de los de C15

El riesgo que el design nombra (D14): los tests de integración de C15 **nunca** alcanzan el gateway,
porque sin sección `AiSearch` el interruptor vale `false` y recorren el camino desactivado. Aquí:

- el host de `AiSalesAssistControllerTests` hace `UseSetting("AiSalesAssist:EnabledByDefault", "true")`
  y registra un `RecordingGateway : ThrowingAiGatewayClient` que **cuenta** sus llamadas;
- **cada test servido afirma el recuento** (`_gateway.AssistCalls.Should().Be(1)`, `…SubstitutesCalls…`),
  y **cada rechazo afirma cero**;
- el único que prueba el interruptor apagado construye **otro** host sin el ajuste y afirma **cero**
  llamadas en las dos rutas.

### 1.4. Por qué la corrida de cierre tardó más del doble

La suma de duraciones por test pasó de **113 s a 216 s**, y **las clases que más crecen son previas y no
se han tocado**: `RateLimitingTests` 14,7 → 33,7 s, `ProductFamiliesControllerTests` 10,6 → 28,8 s,
`FamilyReviewControllerTests` 12,2 → 26,8 s. Las diez clases de C34 suman **~10 s** y ninguna está
entre las catorce más lentas. Es carga de la máquina, no el change.

---

## 2. La puerta de entrada (grupo 1)

| Tarea | Comprobación | Resultado |
|---|---|---|
| 1.1 | Línea base por **nombres**, guardada | 1.060 nombres y 46 en rojo, en `baseline-all.txt` y `baseline-failed.txt` del *scratchpad* de la sesión; los 46 están listados en la salida de la sesión |
| 1.2 | `sha256` de `ai-service/openapi.json` antes de tocar nada | `d8d48f87b279d45d22bce80a67c4fd51caef6e679363c413f5b697c99ec2b875` |
| 1.3 | `openspec validate --all --strict` antes de empezar | **60 passed / 0 failed** |

---

## 3. Los 73 escenarios de las dos deltas

Recuento hecho con un *parser* por líneas sobre las dos deltas, no a ojo:

```text
ai-sales-assist    ADDED     15 requisitos · 45 escenarios
ai-gateway-client  ADDED      1 requisito  ·  5 escenarios
ai-gateway-client  MODIFIED   5 requisitos · 23 escenarios
```

Cada requisito, con los tests que lo sostienen. **Los 52 tests que `tasks.md` nombra existen y están
en verde en la corrida de cierre**, comprobado programáticamente contra el `.trx`: se extrajo de cada
línea de tarea todo identificador entre comillas invertidas con forma `Nombre_…` —descartando los
que son todo mayúsculas, que son variables de entorno— y se buscó cada uno por su nombre corto:
**52 presentes, 52 en verde, 0 ausentes**. Por grupo: 1 en el 2, 12 en el 3, 1 en el 5, 26 en el 6,
10 en el 7 y 2 en el 8. *(La primera versión de esta comprobación daba 38: su patrón exigía dos guiones
bajos y se saltaba los nombres de dos segmentos, como `Substitutes_LogsTheFunnel`. Ver §10.10.)*

| Requisito | Tests |
|---|---|
| **`ai-sales-assist`** | |
| Dos rutas autenticadas ancladas a una pieza | `SalesAssist_QuestionTravelsInTheBodyNeverInTheUrl` · `SalesAssist_WhenUnauthenticated_Returns401` · `SalesAssist_WithAnInvalidQuestion_Returns400WithoutCallingAi` (×2) · `SalesAssist_WithoutPointOfSale_Returns400WithoutCallingAi` · `Substitutes_WithPageSizeAboveTheMaximum_Returns400WithoutCallingAi` · `SalesCard_ExposesNoRouteForAFreeQuestionOrTheAgent` (×2) · los validadores de `SalesAssistConfigurationTests` |
| Punto de venta y pieza **antes** de llamar | `SalesAssist_AsOperatorOfAnotherPos_Returns403` · `SalesAssist_AnchorNotCarriedAtPos_Returns404WithoutCallingAi` · `SalesAssist_WhenPointOfSaleInactive_IsRefused` · `SalesAssist_AnchorWithZeroStock_IsServed` · `Substitutes_AsOperatorOfAnotherPos_Returns403` · `Substitutes_AnchorNotCarriedAtPos_Returns404WithoutCallingAi` · `AssistAsync_AdministratorWithoutAssignment_IsServed` · `SalesAssist_SendsThePointOfSaleThroughTheScope_NotTheBody` |
| El backend manda sobre los miembros del grupo | `SalesAssist_DropsMembersThePointOfSaleDoesNotCarry` · `SalesAssist_KeepsTheOrderOfTheAiService` · `SalesAssist_HydratesTheGroupInASingleQuery` · `SalesAssist_CatalogSkuWins_AndTheDriftIsLogged` · `SalesAssist_DropsAMemberWhoseIdentifierIsNotAGuid` |
| El aviso de variantes refleja la tienda | `SalesAssist_FamilyHasVariantsDroppedWhenOneMemberSurvives` · `SalesAssist_FamilyHasVariantsKeptWhenTwoMembersSurvive` · `SalesAssist_FamilyHasVariantsNeverAddedOnTheServedPath` |
| Avisos de stock tras hidratar | `SalesAssist_StockWarningsComputedAfterHydration_NotTakenFromPython` · `SalesAssist_CriticalStock_FollowsTheDefaultThreshold` (1, 2, 3) · `SalesAssist_ZeroStock_IsNotCriticalStock` · `SalesAssist_StockCodesInTheAiResponse_AreNotTakenAsTheirOwn` · `SalesAssist_UnknownWarningCode_IsPassedThrough` |
| Marcadores contra la pieza anclada | `PlaceholderResolver_ReplacesBothTokens_WithAnchorValues` · `…_VariantSpelling_Withholds` (×4) · `…_WithoutAnchor_Withholds` (×2) · `…_UnknownPlaceholder_Withholds` · `…_MalformedToken_Withholds` · `SalesAssist_ReplacesPlaceholdersWithRealValues` |
| Estado del argumentario explícito | `SalesAssist_WhenPlaceholderUnresolved_WithholdsThePitchInsteadOfShippingTheRawTemplate` · `SalesAssist_NoGenerationAndWithheldGeneration_AreToldApart` · `SalesAssist_WithheldByAi_WinsOverOutOfStock` · `PitchStatus_SerializesAsSnakeCase` (×6) |
| Pieza agotada: se retira sólo sin pregunta | `SalesAssist_AnchorOutOfStock_WithholdsPitchWithoutQuestion_KeepsItWithQuestion` · `SalesAssist_SoldOutAnchor_WithholdsTheArgumentWithoutQuestion_AndAnswersWithOne` *(int.)* |
| Citas con su alcance | `SalesAssist_WithQuestion_ReturnsCitationsCarryingClaimScope` · `SalesAssist_M3_ReturnsCitationsWithTheirScope` *(int.)* |
| Sustitutos: una llamada, ventana máxima, sólo lo vendible | `Substitutes_AlwaysRequestsTheLargestWindow` · `Substitutes_ShortPage_DoesNotTriggerASecondCall` · `Substitutes_ExcludeProductsWithoutStockAtTargetPos` · `Substitutes_KeepTheOrderOfTheAiService` · `Substitutes_TruncateToThePageAfterFiltering` · `Substitutes_HydrateTheWindowInASingleQuery` · `Substitutes_OfferOnlyWhatTheShopCanSellToday_InTheOrderOfTheAi` *(int.)* |
| Los cuatro vacíos se distinguen | `Substitutes_DistinguishesTheFourEmptyOutcomes` (×4) · `Substitutes_TheFourOutcomesAreDistinguishable` *(int., ×4)* · `Substitutes_AnyOtherGatewayFailure_IsAiUnavailable` (×2) · `SubstitutesOutcome_SerializesAsSnakeCase` (×4) |
| La IA caída degrada y no rompe | `SalesAssist_WhenAiUnavailable_ServesAnchorAndFamilyFromCatalog` · `SalesAssist_WhenAiUnavailable_ServesTheFamilyFromTheCatalog` *(int.)* · `SalesAssist_AnyGatewayFailure_DegradesAndNeverThrows` (×4) · `SalesAssist_WhenCredentialRejected_DegradesAndLogsError` · `SalesAssist_When422_DegradesAndLogsProductNotIndexed` |
| Interruptor por punto de venta | `SalesAssist_WhenSwitchedOff_DoesNotCallAi` (unidad **e** integración) · `Substitutes_WhenSwitchedOff_ReportsAiUnavailableWithoutCallingAi` · `SalesAssist_SwitchedOnForOnePointOfSale_CallsTheAi` |
| Coste acotado por usuario | `SalesAssist_WhenRateLimitExceeded_Returns429WithoutCallingAi` · `SalesAssist_RateLimitIsPartitionedByUser_NotByNetworkOrigin` · `SalesAssist_ExhaustedAllowance_DoesNotThrottleSubstitutes` |
| Nada de la pregunta ni del argumentario en un log | `SalesAssist_ResolvedPitchIsNeverLogged` · `SalesAssist_QuestionIsLoggedOnlyAtDebug` · `SalesAssist_LogLine_CarriesTheFieldsOfTheDesign` · `Substitutes_LogsTheFunnel` · y el log real del §9.4 |
| **`ai-gateway-client`** | |
| *ADDED* · Cliente tipado con assist y sustitutos | `AssistSaleAsync_WhenServiceReturns200_MapsResponseInFull` · `AssistSaleAsync_ContractNulls_SurviveMapping` · `SubstitutesAsync_WhenServiceReturns200_ReturnsTheWholeWindowInOrder` · `AssistSaleRequest_Serialization_OmitsPosId` · `SubstitutesRequest_Serialization_OmitsPosId` · `AssistSaleAsync_SendsThePointOfSaleInTheTokenAndNeverInTheBody` · `AssistSaleAsync_WithCatalogScope_IsRejected` · `SubstitutesAsync_WithCatalogScope_IsRejected` · `AssistSaleAsync_WithoutProduct_IsRejectedBeforeAnyRequest` · `AssistSaleAsync_CompletionEvent_CarriesNoArgumentText` |
| *MODIFIED* · Modos de fallo distinguibles | `AssistSaleAsync_When422_ThrowsRequestRejected_NotUnavailable` · `SubstitutesAsync_When422_ThrowsRequestRejected_NotUnavailable` · `SearchAsync_When422_StillThrowsUnavailable` · y los de C03 de 401/501/timeout/transporte, en verde |
| *MODIFIED* · Reintento que no reintenta lo permanente | `AssistSaleAsync_WhenTimeout_DoesNotRetry` · `AssistSaleAsync_When503_DoesNotRetry` · `AssistSaleAsync_WhenConnectionNeverOpened_RetriesOnce` · `AssistSaleAsync_WhenTransportFailsAfterConnecting_DoesNotRetry` · los dos 422 (una sola petición) · los de C03 |
| *MODIFIED* · Degradación acotada y aislada por familia | `AssistSaleAsync_WhenItsCircuitOpens_RetrievalKeepsWorking` · `SubstitutesAsync_WhenTheRetrievalCircuitIsOpen_FailsFastWithoutCall` · `AddAiGateway_RegistersTheAssistClientWithItsOwnConfiguredBudget` |
| *MODIFIED* · Configuración validada al arranque | `AddAiGateway_WhenAssistBudgetBelowServiceWorstCase_FailsAtStartup` · `AddAiGateway_WithTheAssistBudgetAtTheFloor_Starts` · los de C03 |
| *MODIFIED* · Los modelos no derivan del contrato | 9 filas nuevas de `Dtos_MatchCommittedOpenApiSchema` · la mutación del §6 |

### 3.1. Cada `## MODIFIED` reproduce el requisito vivo **entero**

Comprobado con un *parser* que lee la spec viva `openspec/specs/ai-gateway-client/spec.md` y la
delta, normalizando CRLF:

```text
Contract failure modes are distinguishable by the caller
  live scenarios 4 → delta 6 · live missing in delta: none · preserved byte-identical 4/4 · first paragraph identical
Retry policy never retries a permanent condition
  live scenarios 3 → delta 7 · live missing in delta: none · preserved byte-identical 3/3 · first paragraph CHANGED
Degradation is bounded per call and isolated per route family
  live scenarios 2 → delta 5 · live missing in delta: none · preserved byte-identical 2/2 · first paragraph identical
Gateway configuration is validated at application start
  live scenarios 2 → delta 3 · live missing in delta: none · preserved byte-identical 2/2 · first paragraph identical
Client models cannot drift from the committed contract
  live scenarios 2 → delta 2 · live missing in delta: none · preserved byte-identical 0/2 · first paragraph CHANGED
```

**Ningún escenario vivo falta en la delta.** Las tres diferencias se inspeccionaron una a una y **las
tres son superconjuntos del texto vivo, no sustituciones**:

- *Retry policy*: la delta **añade** una frase —*«It MUST NOT retry HTTP 422, which reflects a request
  the service cannot process»*— y cambia «either» por «any of them». Nada se retira.
- *Client models*, primer párrafo: la lista de modelos cubiertos **gana** *«and the sale assistance and
  substitutes request, response and nested models»* y el ejemplo final gana *«or the claim scope of a
  citation»*.
- *Client models*, los dos escenarios: *«every retrieval and enrichment model property»* pasa a
  *«every retrieval, enrichment, sale assistance and substitutes model property»*; ídem en el de deriva.

### 3.2. El `SHALL`/`MUST` en la primera línea física, en los 21 requisitos

La regla de [CLAUDE.md](../../../../CLAUDE.md) sobre el validador, comprobada con el mismo *parser*:
**21 de 21** requisitos llevan `SHALL` o `MUST` en la primera línea física de su descripción. Y
`openspec validate --all --strict` lo confirma por su lado.

---

## 4. Los trece escenarios de la HU

Trazados uno a uno en el **§8 del
[informe de implementación](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c34-implementation-measurements.md)**.
Aquí las observaciones de método:

1. **El escenario 2 tenía un hueco que sólo se vio al trazarlo**: *«si el corpus no cubre la pregunta,
   la respuesta lo declara con el código que lo dice»* no tenía test propio —estaba cubierto sólo de
   forma genérica por `SalesAssist_UnknownWarningCode_IsPassedThrough`—. Se añadió
   `SalesAssist_KnowledgeNotCovered_IsPassedThrough`, y la medición real lo vio ocurrir: 9 de las 40
   M3 traen `knowledge_not_covered` (§9.3).
2. **Los escenarios 10 y 11 tienen, además de sus tests, evidencia de la pasada real**: 0 de 80 por
   encima de 8 s, y un log de backend sin «€», sin `{{` y sin preguntas (§9).
3. **El escenario 12 queda sin cubrir**: pide la demo con la credencial, y eso es 11.3. La medición
   local enseña que el mecanismo funciona con el proveedor real, **pero no es la demo**, y este QA no
   lo da por equivalente.
4. **El escenario 13 tiene cuatro evidencias independientes**: dos tests de rutas inexistentes, el
   `sha256`, el `git show` del commit sobre las zonas congeladas (§8) y los tests de C15 sin cambio.

---

## 5. Las validaciones que `tasks.md` exige, grupo a grupo

| Grupo | Exigencia | Evidencia |
|---|---|---|
| 2 | DTO que compilan y serializan en *snake_case*; filas en `ModelToSchema`; el test falla si se renombra una propiedad | 9 filas nuevas en verde contra el `openapi.json` sin tocar; mutación del §6; `…_Serialization_OmitsPosId` ×2 comprobando los nombres **del cuerpo serializado**, no de la reflexión |
| 3 | Guardas de ámbito, 422 sólo en las dos operaciones, `ai-assist` con su política, suelo de 8 s, logs | Los **12** tests nombrados por las tareas 3.2–3.6, en verde; timeout **real** de Polly con `FakeTimeProvider` (§10.4) |
| 4 | Base de dobles; ninguno de sus tests cambia de resultado | `ThrowingAiGatewayClient` y los 7 dobles migrados; **53 / 0** en las cuatro clases que los alojan, las mismas que estaban en verde en la línea base |
| 5 | Un test por valor por defecto; un arranque fallido por regla; 429 sin llamar a la IA | 6 tests de valores por defecto; `AddSalesAssist_WithAValueOutOfRange_FailsAtStartup_NamingTheKey` ×9, **uno por regla y cada uno afirmando la clave en el mensaje**; `SalesAssist_WhenRateLimitExceeded_Returns429WithoutCallingAi` |
| 6 | Los 26 tests nombrados por 6.1–6.9 | **26 / 26 en verde** en la corrida de cierre |
| 7 | Los 10 tests nombrados por 7.1–7.5 | **10 / 10 en verde**, `Substitutes_DistinguishesTheFourEmptyOutcomes` con un caso por valor |
| 8 | Un test de serialización por enum; un test por regla del validador; 401 con **un cliente nuevo**; arranque | `PitchStatus_…` ×6, `SubstitutesOutcome_…` ×4; 11 tests de validadores; `SalesAssist_WhenUnauthenticated_Returns401` hace `_factory.CreateClient()` y no reutiliza los autenticados; el host arranca en cada clase de integración |
| 9 | Doble invocado en cada test; flujo completo; C15 igual | §1.3; los 27 tests de `AiSalesAssistControllerTests`; C15 en verde en las dos corridas |
| 10 | p50, p95 y máximo con su procedencia, y la decisión | §9 |
| 11 | `docker compose -f compose.demo.yaml config` resuelve | Resuelve **con y sin** `ASSIST_LLM_API_KEY`, con variables de ejemplo exportadas; `bash -n deploy/demo/deploy.sh` correcto; `JPV_ASSIST_LLM_API_KEY` vacía equivale a no configurada (`blank_assist_llm_key_is_unset` en `settings.py`, leído) |
| 12 | Suite por nombres; hash; gate; informe; documentación; sin TODO | §1, §8, §1 (fila del gate), el informe, los ocho documentos del commit; `git diff -U0` + ficheros nuevos sin `TODO` ni `FIXME` |

---

## 6. Mutaciones de control

Un test en verde a la primera no demuestra nada si no se ha visto fallar. Tres mutaciones a mano,
cada una **revertida** después, con el fichero comprobado de vuelta en su estado:

| Mutación | Resultado |
|---|---|
| `AiSimilaritySignals.StyleSimilarity` → `StyleScore` | **1 en rojo**: `Dtos_MatchCommittedOpenApiSchema(AiSimilaritySignals, "SimilaritySignals")`, *«AiSimilaritySignals.StyleScore serializes as 'style_score', which must exist in schema SimilaritySignals of the committed contract, but found False»* |
| `family_has_variants` nunca se retira (`Members.Count < 0`) | **1 en rojo**: `SalesAssist_FamilyHasVariantsDroppedWhenOneMemberSurvives` |
| La regla de pieza agotada ignora la pregunta | **1 en rojo**: `SalesAssist_AnchorOutOfStock_WithholdsPitchWithoutQuestion_KeepsItWithQuestion` |

El primer intento de la mutación de contrato no demostró nada, y el porqué está en el §10.2.

---

## 7. Cobertura del código nuevo (DoD: ≥ 70 %)

Medida con `coverlet.collector` 6.0.4, que el proyecto ya referencia, sobre las diez clases de test de
C34 (216 tests). **No se pudo medir a la primera** (§10.8): `coverlet` no instrumenta el ensamblado
`JoiabagurPV.Application` en este repositorio. Con el arreglo del §10.8:

| Fichero nuevo | Líneas | Ramas |
|---|---|---|
| `AiSalesAssistController.cs` | 67/71 · 94,4 % | 18/22 · 81,8 % |
| `AiSalesAssistOptions.cs` | 9/9 · 100 % | 2/2 · 100 % |
| `AiAssistSaleDtos.cs` | 30/30 · 100 % | — |
| `AiSubstitutesDtos.cs` | 22/22 · 100 % | — |
| `SalesAssistDtos.cs` | 62/62 · 100 % | — |
| `AiRequestRejectedException.cs` | 5/5 · 100 % | — |
| `AiSalesAssistServiceCollectionExtensions.cs` | 28/28 · 100 % | 8/8 · 100 % |
| `PitchPlaceholderResolver.cs` | 17/17 · 100 % | 8/8 · 100 % |
| `SalesAssistService.cs` | 290/297 · 97,6 % | 82/84 · 97,6 % |
| `SalesCardAccess.cs` | 13/13 · 100 % | 8/8 · 100 % |
| `SubstitutesService.cs` | 169/181 · 93,4 % | 38/41 · 92,7 % |
| `SalesAssistRequestValidator.cs` | 25/25 · 100 % | 4/4 · 100 % |
| **Total de los ficheros nuevos** | **737/760 · 97,0 %** | **168/177 · 94,9 %** |

Y los tres métodos que C34 añade a `AiGatewayClient`, fichero que ya existía:

| Método | Líneas |
|---|---|
| `TranslateAnchoredStatus` | 10/10 · 100 % |
| `AssistSaleAsync` | 88/95 · 92,6 % |
| `SubstitutesAsync` | 68/89 · **76,4 %** |

**Cumple el DoD con margen.** El punto más bajo es `SubstitutesAsync`: sus ramas de timeout, transporte,
cuerpo vacío y cuerpo que no casa con el contrato no tienen test propio —las de `AssistSaleAsync`, que
son el mismo código, sí—. Se declara en vez de rellenarlo con tests hechos para subir la cifra.

---

## 8. El contrato y el alcance negativo, demostrados

| Comprobación | Evidencia |
|---|---|
| `openapi.json` idéntico byte a byte | `sha256` **`d8d48f87b279d45d22bce80a67c4fd51caef6e679363c413f5b697c99ec2b875`** al empezar y al cerrar; `git diff --stat 6030aa3 eb44711 -- ai-service/openapi.json` vacío |
| El commit no toca las zonas congeladas | `git show --stat eb44711 -- ai-service frontend terraform .github backend/src/JoiabagurPV.Infrastructure` → **0 líneas**; ídem `JoiabagurPV.Domain` |
| Sin migración de EF Core | El commit no toca `Infrastructure/` (donde viven las migraciones); `MigrationModelDriftTests` en verde en la línea base y al cierre |
| `POST /api/ai/search` se comporta igual | `AiSearchControllerTests` (15), `AiSearchRateLimitTests` (3) y `AssistedSearchServiceTests` (37) en verde en las dos corridas; `AssistedSearchService.cs` y `AiSearchController.cs` fuera del diff |
| `TranslateStatus` intacto para las demás operaciones | `SearchAsync_When422_StillThrowsUnavailable`; el 422 se traduce en un método aparte, `TranslateAnchoredStatus`, que sólo invocan `AssistSaleAsync` y `SubstitutesAsync` |
| No hay ruta para la consulta libre ni para el agente | `SalesCard_ExposesNoRouteForAFreeQuestionOrTheAgent` ×2; y el cliente rechaza una petición sin pieza antes de emitirla |
| Terraform no se toca para la demo | Fuera del diff; el rol de instancia ya lee todo `/jbg-demo/` |

---

## 9. La pasada con proveedor real (tarea 10.1)

### 9.1. La precondición de TLS, comprobada y no supuesta

La tarea pedía medir *«sin pasar por el interceptor TLS de Norton (o declarando que pasa)»*, y
`CLAUDE.md` avisa de que cualquier llamada real al proveedor muere con `CERTIFICATE_VERIFY_FAILED`.
Antes de levantar nada se abrió un socket TLS **desde un contenedor** `python:3.11-slim-bookworm` con
el contexto por defecto, sin ningún PEM:

```text
api.openai.com  →  VERIFIED with system bundle; issuer: Google Trust Services
pypi.org        →  VERIFIED, issuer: GlobalSign nv-sa
```

**El MITM de Norton no alcanza al tráfico de la VM de Docker.** La medición se hizo, por tanto, en el
caso limpio, sin interceptor y sin `SSL_CERT_FILE`. La reconstrucción de la imagen bajó sus
dependencias sin tocar certificados, y ninguna de las 81 peticiones dio un error de TLS. `CLAUDE.md`
se precisó en una línea (commit `eb44711`).

### 9.2. El montaje

| Pieza | Cómo |
|---|---|
| `jbg-ai` | `docker compose build jbg-ai` desde la rama: la imagen local tenía **dos semanas**, anterior a C30b, C31 y C32b. Levantado con un *override* **fuera del repositorio** que pone `STUB_MODE=false`, `JPV_EMBEDDING_MODEL=openai/text-embedding-3-small` y `JPV_ASSIST_LLM_MODEL=openai/gpt-4o-mini`, y pasa las dos claves por **interpolación** desde `backend/.env`. Ningún valor de clave se imprimió ni se escribió: sólo se comprobó que estaban definidas y su longitud |
| `/health` | `{"status":"OK", …, "index":{"documents":1168,"model":"openai/text-embedding-3-small","configured_model":"openai/text-embedding-3-small","status":"ok"},"provider":"configured"}` |
| API .NET | `dotnet run` en el host, `Development`, `AiSalesAssist__EnabledByDefault=true` y `AiSalesAssist__RateLimitPermitLimit=1000` **sólo para esta pasada**: 80 peticiones de un mismo usuario agotarían los 10 por minuto |
| Muestra | Las 40 piezas de `ai-service/evals/assist/sweep-sample.yaml` (20 de un material, 20 de dos o más), cada una en el punto de venta activo que más unidades tiene de ella —por SQL determinista, `DISTINCT ON … ORDER BY Quantity DESC, Code`—; las 40 con stock |
| Peticiones | Por pieza, una M2 y una M3 con una de cuatro preguntas de mostrador rotando; **en serie**, como administrador; más **una de calentamiento** excluida, que paga la construcción perezosa de los clientes (4,6 s) |

### 9.3. Lo que se midió

| | n | p50 | p95 | máx | mín | > 8 s | > 10 s |
|---|---|---|---|---|---|---|---|
| **M2** | 40 | 3,64 s | 7,28 s | 7,93 s | 2,35 s | 0 | 0 |
| **M3** | 40 | 5,39 s | 7,04 s | 7,54 s | 1,30 s | 0 | 0 |
| **Todas** | 80 | **4,42 s** | **7,13 s** | **7,93 s** | 1,30 s | **0** | **0** |

- **El tiempo es la IA**: cruzando cada petición con su línea `stage=sales_assist` por `trace_id`
  (**80 de 80** casadas), `ai_ms` p50 4,40 s · p95 7,12 s · máx 7,91 s; `total_ms − ai_ms` p50 **4 ms**,
  máx 13 ms; y el tramo HTTP del cliente, p50 7 ms.
- **Resultado de cada petición**: **0 degradadas**; **74 `generated`** y **6 `withheld_by_ai`** (3 en
  M2, 3 en M3); **0 argumentarios con `{{` o `}}` sobrantes**; de los 37 generados en M2, **22 llevan el
  precio de catálogo** formateado; en M3, 3 de 37.
- **Coste**: **262.737 tokens de entrada y 30.903 de salida**, sumados de `prompt_tokens` y
  `completion_tokens` del log; a precio de lista de `gpt-4o-mini` (0,15 / 0,60 USD por millón) son
  **~0,058 USD**, más los *embeddings* de las 40 preguntas, despreciables. El precio es un supuesto,
  no una factura.
- **Decisión**: `AssistTimeoutMs` **se queda en 10.000**. El máximo, 7,91 s en la IA, está al 99 % del
  suelo de 8.000; bajar al suelo dejaría sin margen justo las peticiones más lentas.

### 9.4. La política de logs, comprobada sobre el log real

Sobre el fichero de log completo de la API durante la pasada:

```text
líneas con «€»                                  →  0   (el precio resuelto)
líneas con «{{»                                 →  0   (la plantilla cruda)
«Se puede mojar» / «piel sensible o con alergias»
  / «limpia en casa» / «no le queda bien»       →  0 / 0 / 0 / 0   (las cuatro preguntas)
líneas stage=sales_assist                       →  81
```

Y en el log de `jbg-ai`, exactamente las dos líneas que el §2.4 del informe anticipaba:

```text
stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist
stage=router_client model=openai/gpt-4o timeout_s=2.0 credential=assist_fallback
```

### 9.5. Limpieza

La API se detuvo; se comprobó que **nada** quedaba escuchando en el 5056. El contenedor de `jbg-ai` se
**eliminó** —guardaba en su configuración las claves interpoladas— y el próximo `docker compose up`
lo recreará con la configuración base del repositorio. Postgres sigue como estaba. El *override* y
los resultados crudos (`latency-results.json`: estado, longitudes y tiempos, **sin el texto de ningún
argumentario**) quedan en el *scratchpad* de la sesión, fuera del repositorio.

---

## 10. Incidencias de esta pasada

### 10.1. Una aserción mía de 405 donde el host responde 404 — **defecto mío de test**

`SalesAssist_QuestionTravelsInTheBodyNeverInTheUrl` afirmaba que un `GET` sobre la ruta de
`sales-assist` daba **405**. El host responde **404** a un verbo sin acción, igual que ya acepta
`AiCatalog_ExposesNoReadRoute` de C12. Lo que el test tiene que demostrar —que **no existe** ruta `GET`
que una precarga pudiera disparar— se cumple con cualquiera de los dos, y la aserción pasó a
`BeOneOf(NotFound, MethodNotAllowed)` con el precedente citado en el comentario.

### 10.2. La primera mutación de contrato no demostró nada — **defecto de método**

Renombrar `AiCitation.ClaimScope` rompió **la compilación** de otro test que la nombra, así que la
suite corrió contra los binarios **anteriores** y salió en verde. Un verde que no probaba nada. Se
repitió sobre una propiedad que ningún test nombra (§6), y ahí sí falló donde debía.

### 10.3. `sed -i` de Git Bash pasó seis ficheros a LF — **defecto mío de herramienta; corregido**

Las ediciones hechas con `sed -i` convirtieron los finales de línea de seis ficheros de CRLF a LF.
`git ls-files --eol` lo delató (`w/lf` frente al `w/crlf` del resto). **No tuvo efecto en el commit**
—`core.autocrlf=true` normaliza a LF en el índice, y el `git diff --stat` fue idéntico antes y después
de corregirlo (1.004 / 199)—, pero se devolvieron a CRLF para no dejar el árbol incoherente.

### 10.4. `EnqueueHang` de C03 no simula un timeout — **hallazgo sobre el precedente**

El doble lanza `TaskCanceledException` **en el acto**: la estrategia de timeout de Polly nunca ve
expirar su presupuesto, y el predicado de reintento no recibe un `TimeoutRejectedException`. Un test de
«no reintenta el timeout» escrito con él **pasaría aunque el predicado reintentara timeouts**. Y el
suelo de 8 s impide el remedio del test de recuperación (un presupuesto de 60 ms). Se añadió
`EnqueueHangUntilCancelled()` y un `FakeTimeProvider` registrado antes de `AddAiGateway`, que el
*pipeline* toma del contenedor: `AssistSaleAsync_WhenTimeout_DoesNotRetry` avanza 10.001 ms y la
estrategia dispara de verdad; el log dice `outcome=timeout` y la suite del gateway sigue en 782 ms.
**`SearchAsync_WhenTimeout_ThrowsAiUnavailable` sigue usando `EnqueueHang`** y no ejercita el timeout de
Polly; no se toca porque no es de este change.

### 10.5. Un contenedor huérfano bloqueaba el nombre — **entorno**

`docker compose up jbg-ai` fallaba con *«The container name "/jpv-pv-jbg-ai" is already in use»*, ni
siquiera con `--force-recreate`. Antes de tocar nada se inspeccionó: mismo proyecto de compose
(`backend`), **parado desde hacía dos semanas** (`Exited (255)`), **sin volúmenes**, imagen ya sin
nombre. Se eliminó ese contenedor, y sólo ese, porque el `docker-compose.yml` del repositorio lo
recrea.

### 10.6. El informe decía «13 requisitos» y son 15 — **defecto mío de redacción; corregido**

La cabecera del informe de implementación daba `ai-sales-assist — 13 requisitos`, confundiendo la
cifra con los 13 escenarios de la HU. El recuento programático del §3 dio **15 requisitos y 45
escenarios**. Corregido en el informe; **esa corrección entró en `d6a740f`**, junto con este QA.

### 10.7. Unas comillas invertidas en bash se comieron un identificador — **defecto mío de herramienta; corregido antes del commit**

Un `node -e "…"` con `` `AssistTimeoutMs` `` entre comillas dobles hizo que bash lo ejecutara como
sustitución de orden, y la ficha del plan quedó con *«así que \*\*\*\* se queda en 10 s»*. Se detectó por
el aviso `AssistTimeoutMs: command not found`, se corrigió con un script en fichero y se comprobó que
ni el plan ni `epicas.md` contenían `****` ni tildes invertidas perdidas.

### 10.8. `coverlet` no instrumenta `JoiabagurPV.Application` en este repositorio — **hallazgo de herramienta**

La primera corrida con `--collect:"XPlat Code Coverage"` produjo un informe **sin el paquete
`JoiabagurPV.Application`**, que es donde vive casi todo el código nuevo. Con `--diag`:

```text
[coverlet]Unable to instrument module: …\JoiabagurPV.Tests\bin\Debug\net10.0\JoiabagurPV.Application.dll
Coverlet.Core.Exceptions.CecilAssemblyResolutionException: AssemblyResolutionException for
'Microsoft.Extensions.Logging.Abstractions, Version=10.0.0.0, …'
```

El ensamblado llega del **framework compartido de ASP.NET Core** y nunca se copia al `bin`, así que
Mono.Cecil no lo resuelve. **La sugerencia de `coverlet`, `-p:CopyLocalLockFileAssemblies=true`, no lo
arregla** (probado). Lo que sí: copiar temporalmente al `bin` los 47 `Microsoft.Extensions.*.dll` del
framework `Microsoft.AspNetCore.App/10.0.11` que no estaban, sólo para que Cecil los resuelva
—en ejecución no cuentan, porque el host carga por `deps.json` y el framework—, correr con
`--no-build`, y **borrarlos a continuación** (comprobado: 0 restantes). Los 216 tests pasaron igual con
y sin ellos.

**La consecuencia va más allá de C34**: cualquier cifra de cobertura de `Application` tomada en este
repositorio con el comando por defecto **no incluye `Application`**, y no avisa salvo con `--diag`.
Queda anotado aquí para que no se lea como una cobertura baja.

### 10.9. `Update_WithValidData_ShouldReturnUpdatedProduct` es intermitente — **hallazgo, no registrado antes**

Carrera de reloj de 0,6 ms entre `CreatedAt` y `UpdatedAt` (§1.1). Pasa aislado. No es de este change
y no se toca; conviene añadirlo al inventario de fallos conocidos de `testing-backend.md`.

### 10.10. Mi comprobación de tests nombrados contaba 38 y son 52 — **defecto de método en este QA; corregido**

Al redactar este QA, la verificación de que cada test nombrado en `tasks.md` existe y pasa usó un
patrón que exigía **dos** guiones bajos. Los nombres de dos segmentos —`Substitutes_LogsTheFunnel`,
`Substitutes_ExcludeProductsWithoutStockAtTargetPos`, `SalesAssist_DropsMembersThePointOfSaleDoesNotCarry`
y once más— **no se comprobaban**, y el resultado, «38 de 38», sonaba completo. Se detectó al cuadrar
el recuento por grupo del §5 contra las tareas a mano, y se repitió con el patrón correcto: **52 de 52
presentes y en verde**.

### 10.11. El recuento del DoD — **redacción de este QA; corregido**

La primera versión decía «18 de 20» y que la casilla de la demo eran «dos del DoD». En el ticket es
**una** casilla; el recuento correcto es **19 de 20**, y la que falta es la de la demo.

---

## 11. Lo que esta pasada **no** verifica, dicho aquí

- **La demo quedó verificada** (§13), así que este apartado ya no la incluye. Lo que sigue sin medirse es la
  **cuota del proveedor bajo concurrencia real**: el límite propio corta en 10 peticiones por minuto y
  usuario, y para alcanzar la cuota harían falta varios operarios a la vez.
- **La latencia en producción.** La del §9 es de una máquina de desarrollo, n = 80, una franja
  horaria y sin concurrencia. No sustituye la de la demo en eu-west-1.
- **La concurrencia real** frente a la cuota de tokens por minuto: la pasada fue en serie a propósito.
- ~~**Una verificación independiente**: esta es la pasada del autor. `/opsx:verify` no se ha ejecutado.~~
  **Hecha el 2026-09-22 y registrada en el §14**, con línea base propia y mutaciones de control. Encontró
  una cifra falsa en el §13.1 de este QA —las migraciones de EF Core del salto de la demo— y un hueco de
  test en el orden del D6, los dos corregidos.
- **La suite de `ai-service` y la del frontend**: no se ejecutaron porque el diff no toca ninguno de
  los dos (§8).
- **Las ramas de fallo de `SubstitutesAsync` en el cliente** (timeout, transporte, cuerpo vacío o
  malformado): sin test propio, 76,4 % de líneas (§7).
- **`update-docs`** no se ejecutó: los documentos de la tarea 12.5 se revisaron a mano. La skill la lanza
  `archive-docs` al archivar.

---

## 12. El DoD del ticket, casilla a casilla

| # | Casilla | Estado | Evidencia |
|---|---|---|---|
| 1 | Código según las capas de `modelo-c4.md` y las convenciones | ✅ | DTO, opciones, servicios y validadores en `Application`; controlador y política en `API`; nada en `Domain` ni en `Infrastructure` (§8) |
| 2 | xUnit + Moq + FluentAssertions + Bogus; Testcontainers; nomenclatura; **cobertura ≥ 70 %** | ✅ | §1.2; **97,0 %** de líneas y **94,9 %** de ramas en el código nuevo (§7) |
| 3 | Línea base medida antes de tocar nada, por nombres | ✅ | §1, §2 |
| 4 | Los tests de integración invocan el doble del gateway y lo comprueban | ✅ | §1.3 |
| 5 | Un test comprueba que no se llama a la IA con 403, 404 ni 400 | ✅ | Cinco tests de integración, con `AssistCalls`/`SubstitutesCalls` a **0** |
| 6 | El argumentario resuelto no aparece en ningún log | ✅ | `SalesAssist_ResolvedPitchIsNeverLogged` y el log real (§9.4) |
| 7 | La pregunta viaja en el cuerpo y el DTO hacia Python no lleva `pos_id` | ✅ | `SalesAssist_QuestionTravelsInTheBodyNeverInTheUrl`; `…_Serialization_OmitsPosId` ×2; `AssistSaleAsync_SendsThePointOfSaleInTheTokenAndNeverInTheBody` |
| 8 | El circuito de `ai-assist` no abre el de recuperación | ✅ | `AssistSaleAsync_WhenItsCircuitOpens_RetrievalKeepsWorking` |
| 9 | El suelo de 8.000 ms al arranque | ✅ | `AddAiGateway_WhenAssistBudgetBelowServiceWorstCase_FailsAtStartup` y `…AtTheFloor_Starts` |
| 10 | Los DTO nuevos en `ModelToSchema` | ✅ | 9 filas (§5, grupo 2) |
| 11 | `.WithPhone("600123456")` y familias por `POST /api/product-families` | ✅ | Las dos clases de integración nuevas; la familia se crea como administrador y se afirma `201 Created` |
| 12 | Aserciones de 401 con un cliente nuevo | ✅ | `SalesAssist_WhenUnauthenticated_Returns401` |
| 13 | Sin migración de EF Core | ✅ | §8 |
| 14 | `sha256` de `openapi.json` igual | ✅ | §8 |
| 15 | Deltas con el `SHALL`/`MUST` en la primera línea física | ✅ | 21 / 21 (§3.2) |
| 16 | `openspec validate --all --strict` → 0 failed | ✅ | 60 / 0 |
| 17 | Latencia de M2 y M3 medida en Docker Compose, con su procedencia | ✅ | §9 |
| 18 | **Demo**: los cuatro pasos, `credential=assist` en el log, asistencia `generated` y memoria medida | ✅ | §13: parámetro creado, desplegado `sha-d6a740fa…`, `credential=assist` en el log, SKU1051 `generated` con «250,00 €» y «5» en el texto, y 269,9 MiB de 512 medidos antes y después de las diez generaciones de la ventana (6 + 4, §13.3) |
| 19 | Documentación | ✅ | Los siete documentos de la tarea 12.5, más `CLAUDE.md`, en `eb44711` |
| 20 | Sin TODO/FIXME sin tarea de seguimiento | ✅ | §5, grupo 12 |

**20 de 20 cumplidas** tras la verificación en el entorno del §13, que cierra la casilla 18.

---

## 13 · La demo, desplegada y verificada (tareas 11.3 y 11.4)

Ejecutado el **2026-09-22** por el desarrollador, con asistencia en la sesión. Todo lo de abajo son
salidas reales, no expectativas.

### 13.1 · La secuencia

| Paso | Evidencia |
|---|---|
| Cuenta correcta | `sts get-caller-identity` → **666823181744**, la cuenta de la demo, distinta de la de producción |
| Parámetro creado | `/jbg-demo/ASSIST_LLM_API_KEY`, **`SecureString`**, versión 1. Verificado **sin descifrarlo** |
| Código desplegado | `git push origin c34-…:demo` — avance rápido `f5212a7..d6a740f`, **188 commits**, porque la demo corría C17 |
| Riesgo comprobado antes de empujar | **Tres migraciones de EF Core** entre `demo` y la rama —`AddFamilyReviewVerdict`, `AddFamilyReviewSeconds` y `AddVerdictSubjectPopulation`, las tres de **C28** y **ninguna de C34**—, que la API aplica sola al arrancar (`Program.cs:67`, `context.Database.MigrateAsync()`); 2 revisiones de Alembic, que `deploy.sh` aplica. **Esta fila decía «0 migraciones de EF Core» y era falso**: corregido por la verificación independiente (§14) |
| Despliegue | `[deploy] Generation credential: present` · `Applying schema revisions` · `Deployed sha-d6a740fa…` |
| Verificación del despliegue | `verify.sh`: **1.200 documentos indexados**, en verde |
| Cliente generativo | `stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist` |
| El enrutador, previsto en §2.4 del informe | `stage=router_client … credential=assist_fallback`, construido y sin uso |

### 13.2 · La asistencia real, y el precio dentro del texto

Seis piezas distintas del punto de venta *Aeroport de Menorca*, modo M2:

```text
SKU1022  200  2853 ms · generated  citas 2 · precio no · stock no · marcadores no
SKU611   200  1555 ms · generated  citas 0 · precio no · stock no · marcadores no
SKU1051  200  2977 ms · generated  citas 2 · precio SÍ · stock SÍ · marcadores no
SKU490   200  1372 ms · generated  citas 0 · precio SÍ · stock SÍ · marcadores no
SKU984   200  3849 ms · generated  citas 2 · precio SÍ · stock SÍ · marcadores no
SKU983   200  2484 ms · generated  citas 2 · precio SÍ · stock SÍ · marcadores no
```

**6 de 6 `generated`, 0 con marcadores sobrantes, 4 de 6 con el precio y el stock dentro del texto**.
Eso **no es** la misma cifra que el 22 de 37 del §4, y no debe leerse como su confirmación: aquélla
cuenta **sólo el precio** sobre 37 M2, y ésta **precio y stock a la vez** sobre 6. Con n = 6 el
intervalo es tan ancho que lo único que se sostiene es que el mecanismo escribe las dos cifras cuando
el modelo las pide. El ejemplo, SKU1051 a 250 € con 5 unidades:
*«Este anillo está disponible por **250,00 €** y cuenta con **5**.»* Precio en formato es-ES, stock como
entero: los dos, resueltos por .NET contra la pieza anclada.

Sustitutos de la misma pieza: **`outcome: ok`, 60 candidatos → 28 en la tienda → página de 5**.

### 13.3 · Memoria y cuota (11.4)

| Contenedor | En reposo | Tras las diez generaciones de la ventana (6 + 4) |
|---|---|---|
| `jbg-demo-ai` | **269,9 MiB / 512 MiB · 52,7 %** | **269,9 MiB · 52,7 %**, idéntico |
| `jbg-demo-api` | 235,2 MiB | 238,6 MiB |
| `jbg-demo-postgres` | 96,6 MiB | 96,8 MiB |
| Host | 751 MB de 1.909, 836 disponibles, **sin swap** | igual |

Eran **232,5 MiB** en C17 sin generación: los ~37 MiB de más son la construcción de los clientes y el
corpus, y **generar no mueve la aguja**, porque el modelo vive en el proveedor. El `t3.small` y el tope
de 512 MiB siguen bien dimensionados.

**La cuota de tokens por minuto no es la restricción operativa, y esto refuta lo que yo esperaba.**
Las **diez** generaciones que la ventana permitió salieron **todas `generated`**, sin una sola
degradación del proveedor. Lo que corta es el límite propio de la ruta: **10 por minuto y usuario**,
con **429 a partir de la 11.ª petición de la ventana** — verificado en el entorno real, no sólo en el
test de integración.

**Y no fueron diez seguidas, aunque al escribirlo lo pareciera.** Fueron **6 + 4**: las 6 piezas del
§13.2 y luego 4 de una ráfaga de 12, con las **8 restantes rechazadas con 429**. La ráfaga se leyó mal
al principio (4 servidas y 8 rechazos donde se esperaban 10 y 2) hasta caer en que la fase anterior ya
había gastado 6 peticiones **de la misma ventana**: 6 + 4 = 10, que es exactamente lo que da una
ventana fija de 10 por minuto y usuario. Las dos lecturas de `docker stats` de la tabla de arriba
abarcan **las dos fases**, no una ráfaga sola. El límite estaba bien; el guion de medición, no.

### 13.4 · Dos hallazgos del entorno, ninguno de C34

- **`ai.pos_projection` vacía deja la recuperación en 503.** Los primeros sustitutos degradaron a
  `ai_unavailable`; el log mostró `jbg-ai` respondiendo **503** dos veces (`Attempts: 2`, el reintento
  del cliente de recuperación) y a .NET degradando con **200**, como está especificado. La causa,
  `resolve_scope` negándose a abstenerse sobre una proyección vacía — una regla de C22 que la demo,
  desplegada en C17, nunca había satisfecho. La llaman **las dos** rutas, así que la búsqueda asistida
  también estaba caída. Resuelto con `sync-pos --full`. §6.1 del informe.
- **El corpus no viaja en la imagen de `jbg-ai`.** `ai.knowledge_chunk` tenía 0 filas y por eso M2 salía
  `withheld_by_ai`; `CORPUS_DIR` apunta a `<raíz>/data/knowledge` y el `Dockerfile` copia sólo `src`,
  `migrations` y `prompts`. Resuelto copiando el corpus desde el paquete de despliegue y ejecutando
  `sync-knowledge --full`; tras eso, M2 pasó a `generated` con 2 citas. §6.2 del informe.

### 13.5 · Tres cosas que se corrigieron por el camino

- **La contraseña de `demo.admin` no la tenía nadie**, y no está —correctamente— en el repositorio. Se
  restableció generando el hash **BCrypt con factor 12 en local** y enviando sólo el hash: la
  contraseña en claro no pasó por el canal de administración remota, que queda archivado.
- **El runbook dice que las cuentas se crean «por la ruta de registro de la API»**, y los usuarios son
  `demo.admin` y `demo.operador`, **con punto**, que el validador de la API no admite
  (`^[a-zA-Z0-9_]+$`). Se crearon por SQL. Corregido en `deploy/demo/README.md`.
- **Aviso de seguridad levantado y retirado con el dato en la mano.** El sembrador recrea `admin` con
  `Admin123!` si no existe, y el runbook vacía la tabla de usuarios; parecía una credencial por defecto
  en un entorno público. La consulta lo desmintió: `admin` existe **desactivado** (`IsActive = f`), y
  `LoginAsync` rechaza a un usuario desactivado aunque la contraseña sea correcta.

---

## 14 · Verificación independiente (`/opsx:verify`, 2026-09-22)

> Pasada **adversarial** sobre `fd554c9`, hecha por una sesión distinta de la que implementó y escribió
> los §1–§13, con el encargo de buscar lo que a aquélla se le escapó y no de confirmarla. Nada se
> desplegó y no se llamó al proveedor: la demo se auditó **leyendo**. El árbol de partida estaba limpio
> y la rama sincronizada con `origin`.

### 14.1 · Lo que se reprodujo, midiéndolo otra vez

| Afirmación de este QA | Cómo se comprobó | Resultado |
|---|---|---|
| `openspec validate --all --strict` → 0 failed | Ejecutado | **60 passed / 0 failed**, y el change es uno de los 60. `openspec validate <change> --strict` → *valid* |
| `sha256` de `ai-service/openapi.json` | `sha256sum` sobre el árbol y `git rev-parse` sobre el blob | **`d8d48f87…c2b875`** en el árbol (CRLF), y el **blob es el mismo objeto** —`f70594f9…`— en `687e98a`, `6030aa3` y `HEAD`: idéntico byte a byte. La cifra del §8 es la del fichero tal y como lo deja el *checkout* de esta máquina |
| El change no toca las zonas congeladas | `git diff --stat 687e98a^..HEAD` sobre las cinco rutas | **Vacío**, para **toda la rama** y no sólo para `eb44711`. **0** ficheros bajo `Infrastructure/`, luego 0 migraciones propias |
| Deltas: 15 + 45, 1 + 5, 5 + 23 | *Parser* propio, escrito sin mirar el suyo | **Exacto**: `ai-sales-assist` ADDED 15 · 45; `ai-gateway-client` ADDED 1 · 5 y MODIFIED 5 · 23 |
| `SHALL`/`MUST` en la primera línea física | El mismo *parser* | **21 de 21** |
| Los `## MODIFIED` reproducen el requisito vivo entero | Comparación contra `openspec/specs/ai-gateway-client/spec.md` | **Ningún escenario vivo falta**, y los cuerpos conservados son byte-idénticos salvo los dos de *Client models*, que **amplían** y no sustituyen — igual que dice el §3.1 |
| Los 52 tests que `tasks.md` nombra existen y están en verde | *Parser* propio contra mi `.trx` de cierre | **52 de 52 presentes y en verde.** Además, **63 de 63** de los nombrados en el §8 del informe y **91 de 91** de los nombrados en este QA |
| `MaxQueryLength = 500` y `MaxTopK = 50` salen del contrato | Leídos de `openapi.json` | `AssistRequest.query.maxLength = 500` y `SubstitutesRequest.top_k.maximum = 50`: **coinciden**, no son números elegidos aquí |
| `top_k = 20` da la ventana de 60 | `over_retrieval_count` en `stubs/responses.py` | `min(3 × 20, 60) = 60`. Y `candidates_returned = len(results)` en `retrieval/substitutes.py`, así que el `Results.Count` que usa el servicio **es** el `candidates_returned` del contrato |

### 14.2 · La suite, con línea base propia y comparada por nombres

El árbol está limpio y la implementación commiteada, así que `git stash` **no** habría medido nada. La
línea base se tomó en un **`git worktree` desprendido en `6030aa3`**, fuera del repositorio, sin tocar
la rama.

```text
LÍNEA BASE  (6030aa3, worktree propio)          1060 nombres, 49 en rojo   8 m 08 s
CIERRE      (fd554c9, sin el test de 14.4)      1240 nombres, 49 en rojo   8 m 29 s
CIERRE      (fd554c9 + el test de 14.4)         1241 nombres, 50 en rojo   7 m 40 s

Contra la línea base, en las dos corridas de cierre:
  nombres de la línea base ausentes    →  0        y  0
  nombres nuevos                       →  180      y  181
  nombres NUEVOS en rojo               →  0        y  0
  entran en rojo / salen del rojo      →  7 / 7    y  6 / 5
```

**Ningún nombre nuevo falla en ninguna de las dos**, y **ningún nombre de la línea base desaparece**.
Todo lo que rota está identificado:

- **`InventoryIntegrationTests`**, la clase que
  [testing-backend.md](../../../../Documentos/testing-backend.md) documenta como *«baraja los suyos de una
  vez a otra»*: aporta los 7 ↔ 7 de la primera corrida y 5 ↔ 5 de la segunda. Los nombres **no se
  repiten entre corridas** ni coinciden con los que el §1.1 vio rotar — que es justo lo que hace una
  rotación por orden de ejecución.
- **El +1 de rojo de la última corrida es
  `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct`**, la carrera de reloj que
  el §10.9 registró: *«Expected updated.UpdatedAt to be on or after ‹…16.462865›, but found
  ‹…16.462797›»* — **68 µs**, contra los 0,6 ms de aquella vez. `ProductsController` está fuera del
  diff de C34.

De ahí que el **recuento suba de 49 a 50 sin que nada empeore**, que es exactamente el aviso de
`CLAUDE.md`: se comparan nombres, no números.

Dos precisiones al §1, ninguna de ellas un defecto:

- **Mi línea base da 49 en rojo y no 46.** Mismo árbol, mismo commit, distinta corrida. Es el aviso de
  `CLAUDE.md` en estado puro. Lo que importa —**0 nombres desaparecidos y 0 nombres nuevos en rojo**—
  coincide con el §1.1.
- **Son 180 nombres nuevos, no 179, y el total es 1240, no 1239.** El §1.2 lo dice: el 180º
  (`SalesAssist_KnowledgeNotCovered_IsPassedThrough`) se añadió **después** de la corrida de cierre. La
  consecuencia, que el §1 no saca: **hasta esta pasada, el árbol que se va a archivar no se había
  corrido entero nunca de una vez**. Ahora sí.

### 14.3 · Mutaciones de control, compilando cada una

Ocho mutaciones, aplicadas de una en una con un guion que **compila antes de correr** —la trampa del
§10.2— y revierte comprobando el `sha256` del fichero. Las ocho compilaron.

| # | Mutación | Resultado |
|---|---|---|
| 1 | **D6: intercambiar la regla 4 (agotado) y la 5 (sin resolver)** | **VERDE — la mutación sobrevivió.** Ver §14.4 |
| 2 | Sustitutos: `Quantity > 0` → `>= 0` | **4 en rojo**: `…_ExcludeProductsWithoutStockAtTargetPos`, `…_TruncateToThePageAfterFiltering`, `…_DistinguishesTheFourEmptyOutcomes(none_in_stock)`, `…_LogsTheFunnel` |
| 3 | `family_has_variants` no se retira nunca | **1 en rojo**: `SalesAssist_FamilyHasVariantsDroppedWhenOneMemberSurvives` |
| 4 | `stock_critical` con `<` en vez de `<=` (umbral 2) | **2 en rojo**: `…_CriticalStock_FollowsTheDefaultThreshold(quantity: 2)` y `…_StockWarningsComputedAfterHydration_NotTakenFromPython` |
| 5 | `stock_critical` desde 0 unidades | **1 en rojo**: `SalesAssist_ZeroStock_IsNotCriticalStock` |
| 6 | El resolvedor deja de buscar un `}}` suelto | **1 en rojo**: `PlaceholderResolver_MalformedToken_Withholds(template: "Quedan stock}} unidades.")` |
| 7 | `family_has_variants` **añadido** en el camino servido | **1 en rojo**: `SalesAssist_FamilyHasVariantsNeverAddedOnTheServedPath` |
| 8 | `pos_id` de vuelta en el cuerpo hacia `jbg-ai` | **1 en rojo**: `AssistSaleRequest_Serialization_OmitsPosId` |

**Siete de ocho mueren donde deben.** El filtro de stock de sustitutos, el umbral de stock crítico, la
regla de variantes, la resolución de marcadores y la ausencia de `pos_id` en el cuerpo están pinchados
por tests que fallan si la regla se invierte.

### 14.4 · El hueco que la mutación 1 destapó, y el test que lo cierra

El orden del **D6** fija que la regla 4 —pieza agotada y sin pregunta— gana a la regla 5 —marcador sin
resolver—. Intercambiarlas dejaba **las 42 pruebas de `SalesAssistServiceTests` en verde**: el par no
estaba cubierto. `SalesAssist_WithheldByAi_WinsOverOutOfStock` cubre el par 3↔4, y
`…_AnchorOutOfStock_WithholdsPitchWithoutQuestion_KeepsItWithQuestion` usa una plantilla que **sí**
resuelve, así que nunca llega a la regla 5.

No es cosmético: los dos estados retiran el argumentario, pero **son los estados los que C36 pinta**, y
`withheld_out_of_stock` manda al operario al bloque de sustitutos mientras que `withheld_unresolved` es
un defecto de la plantilla.

Añadido **`SalesAssist_OutOfStockAnchor_WinsOverAnUnresolvedPlaceholder`** —pieza a 0, sin pregunta, y
un argumentario con `{{precio}}`—. Verde sobre el árbol (43 de 43) y **rojo, él solo, bajo la mutación
1**. Es el único cambio de código de esta pasada, y es de test.

### 14.5 · Los invariantes, uno a uno

| Invariante | Veredicto |
|---|---|
| Ninguna cifra que vea el operario viene de la IA | **Se sostiene.** `ToMemberAsync` y `SubstituteDto` toman `Price` y `Quantity` de `AssistedSearchRow`. `SalesAssistMemberDto` **no** expone el `score` de la IA. `VariantLabel`, `Materials` y `MatchReasons` sí vienen de la IA, y la spec los deja fuera de la lista de campos que manda la hidratación, a propósito |
| Autorizar y comprobar la pieza **antes** de llamar | **Se sostiene**, con el doble a cero llamadas en los cinco rechazos de integración |
| `{{price}}` con `ToString("C2", es-ES)`, `{{stock}}` entero invariante, sólo los dos tokens | **Se sostiene**; mutación 6 y los 16 tests del resolvedor. Los tests **formatean con la cultura** en vez de escribir el espacio duro a mano, que es la trampa del repositorio |
| El argumentario resuelto no aparece en ningún log | **Se sostiene, y más allá del test.** No hay middleware que registre cuerpos —`API/Middleware/` sólo tiene el de excepciones—, `AiGatewayClient` registra `PitchLength` y nunca el texto, y el `RecordingLoggerProvider` corre a nivel `Trace`, así que la aserción de «sólo a `Debug`» no es un verde en vacío |
| El 422 se traduce sólo en `AssistSaleAsync` y `SubstitutesAsync` | **Se sostiene.** Vive en `TranslateAnchoredStatus`, un método aparte que sólo invocan esas dos; `TranslateStatus` está intacto |
| `ai-assist` no reintenta *timeouts* ni 5xx | **Se sostiene.** El predicado es `HttpRequestException { HttpRequestError: ConnectionError }` y nada más, y el test del *timeout* dispara la estrategia de Polly de verdad con `FakeTimeProvider` |
| Una llamada de sustitutos con `top_k = 20`, orden intacto, `Take(pageSize)` | **Se sostiene** |
| `POST /api/ai/search` se comporta igual | **Se sostiene.** `AssistedSearchService.cs` y `AiSearchController.cs` fuera del diff, y sus tests con el mismo resultado en mis dos corridas |
| La clave de generación no puede acabar en un log | **Se sostiene.** `deploy.sh` sólo prueba si está vacía —y documenta por qué no hay `set -x`—, y `jbg-ai` registra el **nombre** de la credencial, nunca su valor |
| El `credential=assist_fallback` no puede activarse por accidente | **Se sostiene, por tres vías independientes.** `classify_query` corre **sólo** en `AssistMode.QUERY_ONLY`; el cliente .NET lanza `ArgumentException` ante una petición sin pieza; y `jbg-demo-ai` **no publica puertos**, así que nadie de fuera puede pedirle un M1 |

### 14.6 · Lo que se corrigió en esta pasada

1. **La cifra falsa del §13.1.** Decía *«0 migraciones de EF Core entre `demo` y la rama»*. Son **tres**,
   las de C28. Corregido aquí y en el §6 del informe, con la razón real de que el salto fuera seguro:
   `Program.cs:67` aplica las migraciones al arrancar, en todos los entornos.
2. **Las 20 casillas del DoD del ticket**, que seguían sin marcar mientras el §12 afirmaba *«20 de 20
   cumplidas»*. Marcadas, con la salvedad anotada en la del despliegue.
3. **Tres frases desfasadas por sus propios commits**: la cabecera y el §10.6 decían *«queda sin
   commitear»* de cosas que `d6a740f` y `fd554c9` ya habían commiteado, y el §11 daba `/opsx:verify`
   por no ejecutado.
4. **Dos comparaciones que iban más lejos que su evidencia**: el «4 de 6» de la demo no es el «22 de 37»
   del §4 —bases distintas y n = 6—, y el embudo de sustitutos que se enseña tiene **tres** de sus
   cuatro tramos, no los cuatro.
5. **El «diez generaciones seguidas»**, en los seis sitios donde estaba (§13.3 y la casilla 18 de este
   QA, la tarea 11.4, el §6 del informe y las dos apariciones de `DEFERRED_TASKS.md`). La aritmética
   era correcta; la descripción, no: fueron **6 + 4** con **8 rechazos de por medio**, y las dos
   lecturas de `docker stats` abarcan las dos fases.
6. **La tabla de specs del ticket**, que nombraba **tres** requisitos `MODIFIED` de `ai-gateway-client`
   cuando la delta tiene **cinco** —faltaban *Gateway configuration is validated at application start*
   y *Client models cannot drift from the committed contract*, los dos sí anticipados en `proposal.md`—.
   De paso, el suelo de 8.000 ms estaba atribuido al requisito de degradación en vez de al de
   configuración.
7. **El test de §14.4.**

### 14.7 · Lo que esta pasada tampoco verifica

- **Nada de la demo se ejecutó.** Las cifras del §13 —memoria, ráfaga, `credential=assist`, las seis
  piezas— se auditaron por coherencia interna y contra el código, no reproduciéndolas. Lo que **sí**
  quedó establecido es que `fd554c9` no toca código, así que lo verificado sobre `d6a740f` vale para lo
  que se archiva.
- **No se llamó al proveedor.** La latencia del §9 se acepta como venía.
- **La lectura corregida de la ráfaga se acepta como correcta** —6 gastadas + 4 servidas = 10, y 429
  desde la 11.ª, que es exactamente lo que da un `FixedWindow` de 10 por minuto y usuario con la demo
  sin `RateLimitPermitLimit` configurado—, pero **no se volvió a ejecutar**: se comprobó contra el
  código de la política, no contra el entorno. Su descripción como «diez generaciones seguidas» sí se
  corrigió (§14.6).
- **`update-docs` sigue sin ejecutarse** (tarea 12.5), que es su propio criterio de verificación.
