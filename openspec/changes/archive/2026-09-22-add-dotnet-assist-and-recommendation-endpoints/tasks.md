## 1. Puerta de entrada

- [x] 1.1 Medir la línea base de la suite de backend con `git stash push -u`, correr `dotnet test`, `git stash pop`, y guardar **el conjunto de nombres** de los tests que fallan, no el número (`CLAUDE.md`: la suite viene en rojo de antes y algunos fallos dependen del orden). Verificación: fichero con la lista de nombres en el *scratchpad*, citado en el informe de implementación
- [x] 1.2 Anotar el `sha256` de `ai-service/openapi.json` antes de tocar nada. Verificación: el valor queda escrito en el informe de implementación, para compararlo en el cierre
- [x] 1.3 `openspec validate --all --strict` en verde antes de empezar. Verificación: `0 failed`

## 2. Contrato con `jbg-ai` en .NET

- [x] 2.1 DTO del contrato de asistencia en `Application/DTOs/Ai/`: petición con `product_id` y `query` —sin `pos_id`—, respuesta con `intent`, `groups`, `pitch`, `citations`, `warnings`, `clarification_question`, `usage`, `abstained`, `prompt_version`, `trace_id` y `effective_pos_id`, y los anidados de grupo, miembro y cita con la nulabilidad del esquema. Reutilizar `AiUsage`. Verificación: compila y serializa en *snake_case* con `AiGatewaySerialization.Options`
- [x] 2.2 DTO del contrato de sustitutos: petición con `product_id`, `top_k` y `reason` opcional —sin `pos_id`—, respuesta con `results`, `candidates_returned`, `low_confidence`, `trace_id` y `effective_pos_id`, y resultado con `similarity_signals`. Reutilizar `AiSearchFilters` y `AiDebugInfo`. Verificación: compila
- [x] 2.3 Añadir cada tipo nuevo a `AiContractSnapshotTests.ModelToSchema`. Verificación: el test pasa contra el `openapi.json` sin modificar, y falla si se renombra a mano una propiedad de un DTO nuevo
- [x] 2.4 Test `AssistSaleRequest_Serialization_OmitsPosId` y su gemelo de sustitutos, con el patrón del test que ya existe para `AiSearchRequest`. Verificación: verdes

## 3. Cliente del gateway

- [x] 3.1 `AiRequestRejectedException : AiGatewayException` en `Application/Exceptions/`, con el código de estado. Verificación: compila
- [x] 3.2 `IAiGatewayClient.AssistSaleAsync` y `SubstitutesAsync`, con la guarda de `ArgumentException` para un ámbito de catálogo antes de emitir la petición, como en `SearchAsync`. Verificación: tests `AssistSaleAsync_WithCatalogScope_IsRejected` y `SubstitutesAsync_WithCatalogScope_IsRejected`
- [x] 3.3 Traducción del **422** a `AiRequestRejectedException` **sólo en esas dos operaciones**; las demás conservan `TranslateStatus` tal cual. Verificación: `SubstitutesAsync_When422_ThrowsRequestRejected_NotUnavailable`, `AssistSaleAsync_When422_ThrowsRequestRejected_NotUnavailable` y `SearchAsync_When422_StillThrowsUnavailable`
- [x] 3.4 Cliente con nombre **`ai-assist`** en el hueco de `AiGatewayServiceCollectionExtensions.cs:148`: `HttpClient.Timeout` infinito, *pipeline* propio con el presupuesto `AssistTimeoutMs`, circuito con estado propio y un predicado de reintento que **sólo** acepta `HttpRequestException` con `HttpRequestError.ConnectionError`. Los sustitutos usan `ai-retrieval`. Verificación: `AssistSaleAsync_WhenTimeout_DoesNotRetry`, `AssistSaleAsync_When503_DoesNotRetry`, `AssistSaleAsync_WhenConnectionNeverOpened_RetriesOnce` y `AssistSaleAsync_WhenItsCircuitOpens_RetrievalKeepsWorking`, con `AiGatewayTestHost` ampliado con el manejador del cliente nuevo
- [x] 3.5 `AiGatewayOptions.AssistTimeoutMs` pasa a **10.000**, en código y en `appsettings.json`, y la validación al arranque rechaza un valor **menor de 8.000** con un mensaje que nombra la clave y las constantes de Python que lo fijan. Verificación: `AddAiGateway_WhenAssistBudgetBelowServiceWorstCase_FailsAtStartup` y `AddAiGateway_RegistersTheAssistClientWithItsOwnConfiguredBudget`
- [x] 3.6 Log del cliente para las dos operaciones: inicio, fin y fallo con el patrón existente; **ni el argumentario ni la pregunta** por encima de `Debug`. Verificación: `AssistSaleAsync_CompletionEvent_CarriesNoArgumentText`, con `RecordingLoggerProvider`

## 4. Dobles de test

- [x] 4.1 Clase base `ThrowingAiGatewayClient` en `Tests/TestHelpers/`, con todos los métodos de `IAiGatewayClient` lanzando `NotSupportedException` y virtuales. Verificación: compila
- [x] 4.2 Migrar los siete dobles escritos a mano (`StubHealthGateway`, `SucceedingGateway`, `ThrowingGateway`, `RaceWinningGateway`, `AuditingGateway`, `UnavailableGateway`, `ProposingGateway`) a heredar de la base, sobrescribiendo sólo lo que usan. Verificación: la suite compila y **ninguno de sus tests cambia de resultado** respecto a la línea base de 1.1

## 5. Opciones, activación y límite de peticiones

- [x] 5.1 `AiSalesAssistOptions` en `Application/Configuration/`, con `EnabledByDefault` (`false`), `EnabledPointOfSaleIds`, `StockCriticalThreshold` (2), `SubstitutesCandidateWindow` (20, tope 50), `SubstitutesDefaultPageSize` (5), `SubstitutesMaxPageSize` (20), `RateLimitPermitLimit` (10) y `RateLimitWindowSeconds` (60), leídas con `IOptionsMonitor` y un `IsEnabledFor(posId)` como el de `AiSearchOptions`. Verificación: un test de opciones por cada valor por defecto
- [x] 5.2 Validación al arranque: umbral ≥ 1, ventana entre 1 y 50, página por defecto ≤ máxima ≤ 50, límites positivos, y un fallo que nombra la clave. Verificación: un test de arranque fallido por regla
- [x] 5.3 `RateLimitPolicies.AiSalesAssist = "AiSalesAssistRateLimit"`, ventana fija particionada por `NameIdentifier`, con límite alto en el entorno de test salvo que `AiSalesAssist:RateLimitPermitLimit` esté fijado, como hace `AiSearch`. Verificación: `SalesAssist_WhenRateLimitExceeded_Returns429WithoutCallingAi`, con el patrón de `AiSearchRateLimitTests`

## 6. Servicio de asistencia

- [x] 6.1 Autorización y comprobación de la pieza **antes** de llamar a la IA: punto de venta activo, excepción de administrador y `HasAccessAsync` (misma lógica que `AssistedSearchService.AuthoriseAsync`), y después `HydrateAsync([productId], posId)` guardando la fila de la pieza anclada. Verificación: `SalesAssist_AsOperatorOfAnotherPos_Returns403`, `SalesAssist_AnchorNotCarriedAtPos_Returns404WithoutCallingAi`, `SalesAssist_WhenPointOfSaleInactive_IsRefused` y `SalesAssist_AnchorWithZeroStock_IsServed`, con el doble del gateway comprobando **cero** llamadas en los rechazos
- [x] 6.2 Llamada a `AssistSaleAsync` con `query = question?.Trim()` y el ámbito de punto de venta. Verificación: `SalesAssist_SendsThePointOfSaleThroughTheScope_NotTheBody`
- [x] 6.3 Hidratación del grupo con **una** `HydrateAsync`: descarta lo que la tienda no lleva y los identificadores no GUID, conserva el orden de la IA, el SKU de catálogo manda, y `isAnchor` en la pieza anclada. Verificación: `SalesAssist_DropsMembersThePointOfSaleDoesNotCarry`, `SalesAssist_KeepsTheOrderOfTheAiService`, `SalesAssist_ReplacesPlaceholdersWithRealValues` en lo que toca a precio y cantidad, y un test de que la hidratación es una sola consulta
- [x] 6.4 Avisos: conservar `family_has_variants` sólo con ≥ 2 miembros supervivientes, **nunca añadirlo**, `stock_critical` con 1 ≤ qty ≤ umbral, `family_members_out_of_stock` por otro miembro a 0, y los códigos desconocidos pasan. Verificación: `SalesAssist_FamilyHasVariantsDroppedWhenOneMemberSurvives`, `SalesAssist_StockWarningsComputedAfterHydration_NotTakenFromPython`, `SalesAssist_ZeroStock_IsNotCriticalStock` y `SalesAssist_UnknownWarningCode_IsPassedThrough`
- [x] 6.5 Resolvedor de marcadores como unidad pura: `{{price}}` con `ToString("C2", es-ES)`, `{{stock}}` como entero invariante, sólo los dos tokens exactos, retirada si queda `{{` o `}}`, y retirada siempre si no hay pieza anclada. Verificación: `PlaceholderResolver_ReplacesBothTokens_WithAnchorValues`, `PlaceholderResolver_UnknownPlaceholder_Withholds`, `PlaceholderResolver_VariantSpelling_Withholds` y `PlaceholderResolver_WithoutAnchor_Withholds`
- [x] 6.6 Decisión del `pitchStatus` en el orden del design (D6): degradado, no generado, retirado por la IA, agotado en M2, sin resolver, generado; argumentario nulo en todos salvo el último. Verificación: `SalesAssist_WhenPlaceholderUnresolved_WithholdsThePitchInsteadOfShippingTheRawTemplate`, `SalesAssist_NoGenerationAndWithheldGeneration_AreToldApart` y `SalesAssist_AnchorOutOfStock_WithholdsPitchWithoutQuestion_KeepsItWithQuestion`
- [x] 6.7 Mapeo de citas con `claim_scope`, documento, sección, tipo y fragmento. Verificación: `SalesAssist_WithQuestion_ReturnsCitationsCarryingClaimScope`
- [x] 6.8 Camino degradado para el interruptor apagado y para cualquier excepción del gateway: familia de `GetByProductIdAsync` hidratada con `HydrateAsync` en `SortOrder`, avisos de stock y de variantes calculados en .NET, sin argumentario ni citas, `aiAvailable: false` y `pitchStatus: ai_unavailable`, con el nivel de log del design (D11). Verificación: `SalesAssist_WhenAiUnavailable_ServesAnchorAndFamilyFromCatalog`, `SalesAssist_WhenCredentialRejected_DegradesAndLogsError`, `SalesAssist_When422_DegradesAndLogsProductNotIndexed` y `SalesAssist_WhenSwitchedOff_DoesNotCallAi`
- [x] 6.9 Línea de log `stage=sales_assist` con los campos del design (D13); la pregunta sólo a `Debug`; **nunca** el argumentario. Verificación: `SalesAssist_ResolvedPitchIsNeverLogged` y `SalesAssist_QuestionIsLoggedOnlyAtDebug`, con `RecordingLoggerProvider`

## 7. Servicio de sustitutos

- [x] 7.1 Autorización y comprobación de la pieza, las mismas de 6.1. Verificación: `Substitutes_AsOperatorOfAnotherPos_Returns403` y `Substitutes_AnchorNotCarriedAtPos_Returns404WithoutCallingAi`
- [x] 7.2 Llamada única con `top_k = SubstitutesCandidateWindow`, y `reason = "sin_stock"` cuando la pieza anclada tiene 0. Verificación: `Substitutes_AlwaysRequestsTheLargestWindow` y `Substitutes_ShortPage_DoesNotTriggerASecondCall`
- [x] 7.3 Hidratación de la ventana con una `HydrateAsync`, filtro `Quantity > 0`, orden de la IA y `Take(pageSize)`. Verificación: `Substitutes_ExcludeProductsWithoutStockAtTargetPos`, `Substitutes_KeepTheOrderOfTheAiService` y `Substitutes_TruncateToThePageAfterFiltering`
- [x] 7.4 Los cuatro `outcome` y el interruptor. Verificación: `Substitutes_DistinguishesTheFourEmptyOutcomes` (con un caso por valor) y `Substitutes_WhenSwitchedOff_ReportsAiUnavailableWithoutCallingAi`
- [x] 7.5 Línea de log `stage=substitutes` con el embudo `candidates_returned → carried → in_stock → returned` y el `outcome`. Verificación: `Substitutes_LogsTheFunnel`

## 8. Controlador y contrato hacia el frontend

- [x] 8.1 DTO de salida `SalesAssistResponse` y `SubstitutesResponse` con los campos del ticket; `pitchStatus` y `outcome` como enums serializados en *snake_case*. Verificación: compila y un test de serialización de cada enum
- [x] 8.2 Validadores FluentValidation: `pointOfSaleId` obligatorio en los dos; `question` no vacía tras `Trim()` y ≤ 500 si viene; `pageSize` entre 1 y el máximo configurado. Verificación: un test por regla
- [x] 8.3 `AiSalesAssistController` con `[Route("api/ai/products")]` y `[Authorize]`: `POST {productId:guid}/sales-assist` con la política `AiSalesAssist` y `GET {productId:guid}/substitutes` con la política `AiSearch`; validación invocada explícitamente y cuerpo nulo tratado, porque `SuppressModelStateInvalidFilter` está activo; 400, 403, 404, 429 y 200. Verificación: `SalesAssist_QuestionTravelsInTheBodyNeverInTheUrl` y `SalesAssist_WhenUnauthenticated_Returns401`, este último con **un cliente nuevo** de la factoría
- [x] 8.4 Registrar los servicios en ~~`Application/Extensions/ServiceCollectionExtensions.cs`~~ **`Application/Extensions/AiSalesAssistServiceCollectionExtensions.cs` (`AddSalesAssist`), invocado desde `Program.cs`** —el patrón de `AddAssistedSearch` de C15: las opciones necesitan `IConfiguration` y la firma de `AddApplication()` la usan los tests de integración— y la política en la capa de API. Verificación: la aplicación arranca en el entorno de test

## 9. Integración

- [x] 9.1 Tests de integración con Testcontainers, **con un doble del gateway** inyectado con `WithWebHostBuilder` + `ConfigureServices` (patrón de `AiCatalogControllerTests`) y **el interruptor encendido de forma explícita**. Las familias se crean por `POST /api/product-families` como administrador —no hay madre de familias a propósito— y los objetos madre fijan `.WithPhone("600123456")`. Verificación: cada test comprueba que el doble **se invocó**, para no repetir el verde en vacío de C15
- [x] 9.2 Flujo completo de las dos rutas: M2 con marcadores resueltos, M3 con citas, pieza agotada con y sin pregunta, miembro no llevado, sustitutos filtrados y los cuatro `outcome`. Verificación: verdes
- [x] 9.3 Comprobar que `POST /api/ai/search` se comporta igual: sus tests de integración y unitarios no cambian de resultado. Verificación: comparación por nombres contra la línea base de 1.1 — *hecho: `AiSearchControllerTests` (15), `AiSearchRateLimitTests` (3) y `AssistedSearchServiceTests` (37) en verde en las dos corridas; §3 del informe*

## 10. Medición de latencia

- [x] 10.1 Medir en Docker Compose, **sin pasar por el interceptor TLS de Norton** (o declarando que pasa), la latencia de extremo a extremo de `/sales-assist` en M2 y en M3 desde el backend, con una muestra de la población de `evals/assist/sweep-sample.yaml`. Verificación: p50, p95 y máximo escritos en el informe de implementación con su procedencia. Si la distribución permite bajar `AssistTimeoutMs`, se baja **sin cruzar el suelo de 8.000**; si no, se deja en 10.000 y se dice por qué — *hecho el 2026-09-22 (§4 del informe): 40 piezas × {M2, M3}, `jbg-ai` en Docker con proveedor real y **sin** Norton (comprobado: el TLS del contenedor lo firma la CA real). M2 p50 3,6 s · p95 7,3 s · máx 7,9 s; M3 p50 5,4 s · p95 7,0 s · máx 7,5 s; 0 de 80 por encima de 8 s. Se deja en **10.000**: el máximo está al 99 % del suelo*

## 11. Demo — última tarea

- [x] 11.1 Los cuatro pasos de *«C30b — la demo no genera argumentario»* de `openspec/DEFERRED_TASKS.md`: la lectura `ASSIST_LLM_API_KEY` en `deploy/demo/deploy.sh` **sin** `:?`, `JPV_ASSIST_LLM_MODEL: openai/gpt-4o-mini` y `JPV_ASSIST_LLM_API_KEY` en `jbg-demo-ai`, y el parámetro en la lista de secretos manuales de `deploy/demo/README.md`, marcado como opcional. **Terraform no se toca.** Verificación: `docker compose -f compose.demo.yaml config` resuelve sin error
- [x] 11.2 Configuración .NET de la demo: `AiGateway__AssistTimeoutMs: "10000"` y `AiSalesAssist__EnabledByDefault: "true"` en la API. Verificación: la misma resolución del compose
- [x] 11.3 **Paso manual del desarrollador**: crear `/jbg-demo/ASSIST_LLM_API_KEY` como `SecureString` y desplegar. Verificación: el log de `jbg-demo-ai` dice `stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist`, y una asistencia real devuelve `pitchStatus: generated` con precio y stock resueltos — *hecho el 2026-09-22: parámetro creado como `SecureString` (versión 1), rama `demo` avanzada a `d6a740f` y desplegada. `deploy.sh` registró `Generation credential: present`; el log de `jbg-demo-ai` dio `stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist` junto a `stage=router_client … credential=assist_fallback`, como preveía el §2.4 del informe. Una asistencia real sobre SKU1051 devolvió `pitchStatus: generated` con **«disponible por 250,00 € y cuenta con 5»**: precio y stock resueltos dentro del texto. 4 de 6 piezas probadas llevan los dos. Sustitutos en `outcome: ok`, 60 candidatos → 28 en la tienda → página de 5*
- [x] 11.4 Volver a medir la memoria de `jbg-demo-ai` con `docker stats` frente a su tope de 512 MiB (estaba en 232,5 MiB sin generación), y comprobar la cuota de tokens por minuto con varias peticiones seguidas. Verificación: las dos cifras en el informe de implementación y en `openspec/DEFERRED_TASKS.md` (*Instance sizing*) — *hecho el 2026-09-22: `jbg-demo-ai` en **269,9 MiB de 512 (52,7 %)**, idéntico antes y después de las 10 generaciones que permitió la ventana —la generación no carga nada en el contenedor—, frente a los 232,5 MiB de C17. Host: 751 MB de 1.909, 836 disponibles, sin swap. **La cuota de tokens por minuto no fue la restricción**: las 10 generaciones salieron todas `generated`, y quien corta es el límite propio de 10 por minuto y usuario, que rechazó con 429 a partir de la 11.ª. **No fueron 10 seguidas**: 6 del sondeo de piezas + 4 de una ráfaga de 12, con las otras 8 en 429 (§13.3 del QA)*

## 12. Cierre

- [x] 12.1 Correr la suite completa y compararla con la línea base de 1.1 **por nombres**: ningún nombre nuevo en rojo. Verificación: la comparación escrita en el informe de implementación — *1.060 → 1.239 tests, 46 → 46 en rojo; ningún nombre de C34 en rojo y 0 nombres de la línea base desaparecidos. Cuatro nombres rotan (tres de `InventoryIntegrationTests`, rotación documentada, y una carrera de reloj de `ProductsControllerTests`); los cuatro pasan aislados. §3 del informe*
- [x] 12.2 `sha256` de `ai-service/openapi.json` **igual** al de 1.2, y `git diff` vacío en `ai-service/`, `frontend/`, `terraform/` y las migraciones. Verificación: los dos valores de hash lado a lado en el informe — *`d8d48f87…c2b875` antes y después*
- [x] 12.3 `openspec validate --all --strict` → `0 failed`: la delta modifica una spec viva, así que no basta validar el change — *60 passed / 0 failed*
- [x] 12.4 Informe de implementación `Documentos/Proyecto Final AIEng/informes/c34-implementation-measurements.md` con lo que la implementación refute de la historia, siguiendo el patrón de los anteriores
- [x] 12.5 Documentación:
  - `Documentos/epicas.md` (EP15);
  - la ficha de C34 en el plan de changes;
  - `backend/README.md` (endpoints, matriz de autorización y variables `AiSalesAssist:*` y `AiGateway:AssistTimeoutMs`);
  - `Documentos/arquitectura.md` y `Documentos/modelo-c4.md` si cambian las integraciones;
  - `deploy/demo/README.md`;
  - `openspec/DEFERRED_TASKS.md`: se cierra la entrada de C30b y se actualiza *Instance sizing*;
  - `openspec/config.yaml` si cambia algún hecho que resume.

  Verificación: `update-docs` no detecta nada pendiente — *los siete revisados y actualizados a mano, `config.yaml` incluido; la entrada de C30b queda cerrada en el repositorio salvo el paso manual. La pasada de `update-docs` no se ejecutó en esta sesión: la lanza `archive-docs` al archivar, que es decisión del desarrollador*
- [x] 12.6 Ningún TODO ni FIXME sin tarea de seguimiento. Verificación: `git grep` sobre el diff del change — *ninguno en las líneas añadidas ni en los ficheros nuevos*
