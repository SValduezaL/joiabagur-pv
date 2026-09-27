> **Orden y corte.** Los grupos 1 a 9 son el **tramo 1** y el **tramo 2** de la línea de corte, y
> **el tramo 2 no se corta**: sin el grupo 4 el panel asistido sale sin prosa. Los grupos 10 a 13 son
> los tramos 3 a 6, en el orden en que se cortan: el **grupo 12 sale antes que el 13**, porque una
> frontera de autorización arriesga más que enseñar un dato que hoy no está. Lo que no entre **se
> declara aplazado con su motivo** en el grupo 14.
>
> **Nomenclatura de tests:** backend `Método_Escenario_ResultadoEsperado`, frontend
> `should [comportamiento] when [condición]`, Python `test_<lo que sostiene>`.

## 1. Puerta de entrada

- [x] 1.1 Medir la **línea base de la suite de backend por nombres de test**: `git stash push -u`, `dotnet test`, volcar los nombres que fallan a un fichero de trabajo, `git stash pop`. Viene roja de fábrica; **se compara el conjunto de nombres, nunca el número**
- [x] 1.2 Medir la **línea base de la suite de frontend por nombres**, con la misma maniobra y `npm run test`. Leer **la línea de resumen** y no el código de salida, que al pipear siempre es 0. Anotar que **oscila entre 113 y 114** por un test dependiente del orden
- [x] 1.3 Medir la línea base de `ai-service`: `uv run pytest`, que **sí viene verde**, y anotar el recuento
- [x] 1.4 Anotar el `sha256` de `ai-service/openapi.json` y guardar una copia de la línea base para la verificación hoja a hoja del grupo 3
- [x] 1.5 `openspec validate --all --strict` en verde antes de tocar nada, y anotar el total

## 2. Tramo 1 · lo que hoy miente en silencio (sólo .NET y frontend)

- [x] 2.1 Ampliar `IAssistedSearchRepository.SearchLexicalAsync` con los filtros y con un punto de venta nullable, y su implementación con el `JOIN` a `ProductAiProfiles` y los dos `AND`. Test de integración con Testcontainers: `SearchLexicalAsync_WithPieceTypeFilter_ReturnsOnlyThatCategory` y `SearchLexicalAsync_WithMaterialFilter_ReturnsOnlyPiecesCarryingIt`
- [x] 2.2 Pasar los filtros desde `AssistedSearchService` a la ruta degradada y declarar en la respuesta un filtro que no se haya podido aplicar. Test: `SearchAsync_WhenDegradedAndFilterSelected_AppliesTheFilter` y `SearchAsync_WhenFilterCannotBeApplied_DeclaresIt`
- [x] 2.3 Añadir `DegradedReason` a `SalesAssistResponse` reenviando el valor que `SalesAssistService` ya calcula, y comprobar que **coincide con el de su línea de registro** para el mismo `trace_id`. Tests: `SalesAssist_WhenProductNotIndexed_ReportsThatReason`, `SalesAssist_WhenSwitchedOff_ReportsThatReason`, `SalesAssist_WhenHealthy_ReportsNoReason`
- [x] 2.4 Añadir `SearchOrigin.AssistedGenerative = 4` con su documentación, y un test que compruebe que **la columna sigue siendo `int` y no hizo falta migración**: `SearchOrigin_AddingTheFourthValue_RequiresNoMigration`
- [x] 2.5 Crear `GET /api/ai/search/availability` con los dos interruptores de un punto de venta, **sin llamar a la IA y sin consumir cuota**. Tests: `Availability_WhenCalled_MakesNoAiCall`, `Availability_WhenCalledRepeatedly_ConsumesNoQuota`
- [x] 2.6 Pintar el **badge de cuatro estados** en el panel leyendo esa ruta antes de cualquier búsqueda, y **deshabilitar la opción asistida con su motivo** cuando no está disponible. Tests: `should state availability of both paths before any search`, `should disable the assisted option with its reason when the assisted path is off`
- [x] 2.7 Pintar `degradedReason` en la ficha de C36 distinguiendo pieza no indexada de caída. Test: `should tell a piece that is not indexed from an unavailable service`
- [x] 2.8 **Verificación del tramo**: `dotnet build` y `npm run build` en verde, y comparación de las dos suites **por nombres** contra la línea base — cero nombres nuevos

## 3. Tramo 2 · el contrato se mueve

- [x] 3.1 Añadir `filters: RetrievalFilters` a `AssistRequest` con defecto vacío, y pasarlos a `retrieve_products` en el modo libre. Tests: `test_free_query_forwards_filters_to_retrieval`, `test_free_query_without_filters_behaves_as_before`, `test_anchored_mode_ignores_filters`
- [x] 3.2 Regenerar `ai-service/openapi.json` con el *one-liner* del README y **verificar hoja a hoja** contra la copia del 1.4: **0 hojas retiradas y 0 cambiadas de tipo**. Actualizar `test_openapi_snapshot_is_stable`
- [x] 3.3 Añadir `Filters` a `AiAssistSaleRequest` y serializarlo con los nombres del contrato, omitido cuando no hay ninguno. Tests: `AssistSaleAsync_WithFilters_SerializesThemWithContractNames`, `AssistSaleAsync_WithoutFilters_OmitsTheProperty`
- [x] 3.4 Poner al día el doble de `assist_sale_stub` para que el modo libre **no emita marcadores**. Test: `test_stub_free_query_carries_no_placeholder`

## 4. Tramo 2 · el argumentario de M1 (PRERREQUISITO, no se corta)

- [x] 4.1 Escribir `ai-service/prompts/assist/v5.md`: las tres tareas de consulta libre **prohíben hablar de precio y de disponibilidad** y no piden marcadores; el lenguaje comparativo sin cifra sigue permitido. Fijar la versión al fichero como ya hace `v3`
- [x] 4.2 Añadir la **cuarta tarea** de consulta libre, «sin cobertura», con la misma regla que la anclada: no contestar de memoria, no esquivar con una generalidad, no citar nada
- [x] 4.3 Calcular `uncovered` también en el modo libre para las rutas de conocimiento y mixta, emitiendo `knowledge_not_covered`, **sin llamada adicional al proveedor**. Tests: `test_free_query_knowledge_without_corpus_declares_it`, `test_free_query_uncovered_costs_no_extra_provider_call`
- [x] 4.4 Extender `resolve_task` con la cuarta entrada y su selección. Test: `test_free_query_without_corpus_uses_the_uncovered_task`
- [x] 4.5 Añadir `CAUSE_PLACEHOLDER_IN_FREE_QUERY` al vocabulario y a las **causas duras**, comprobada **sólo** cuando `product_id is None`. Tests: `test_placeholder_in_free_query_withholds_the_argument`, `test_anchored_mode_placeholder_is_not_a_violation`, `test_sweep_reports_placeholder_cause_apart`
- [x] 4.6 **Retirar el guardia** de `AiGatewayClient` que rechaza la consulta libre, y dejar el rechazo sólo para una petición **sin ningún ancla**. Tests: `AssistSaleAsync_WithQueryAndNoProduct_IssuesTheRequest`, `AssistSaleAsync_WithNeitherAnchor_ThrowsBeforeAnyRequest`
- [x] 4.7 **La medición que decide si M1 tiene prosa**: pasada sobre las 42 consultas del conjunto etiquetado con `STUB_MODE=false`, contando `{{price}}` y `{{stock}}` en el texto generado **antes y después de `v5`**. Publicar las dos cifras y **persistir el artefacto** con `run_id`, `git_sha` y `prompt_version` en `ai-service/evals/results/`

## 5. Tramo 2 · el endpoint de la consulta libre

- [x] 5.1 Crear `AiFreeQuerySearchOptions` con interruptor por punto de venta, límite de peticiones y tamaños de página **propios**, validada al arranque. Test: `FreeQueryOptions_WhenInvalid_FailsAtStartup`
- [x] 5.2 Crear `FreeQuerySearchService`: resolución de ámbito, llamada al assist con los filtros, **hidratación reutilizada** de `AssistedSearchService` extraída a un colaborador, y telemetría con el origen nuevo
- [x] 5.3 Crear `POST /api/ai/search/assisted` con su política de límite propia. Tests: `FreeQuery_WhenSwitchedOff_MakesNoAiCall`, `FreeQuery_WhenQuotaExhausted_ReportsTooManyRequests`, `FreeQuery_WhenQuotaExhausted_DoesNotReportUnavailable`, `FreeQuery_QuotaIsIndependentOfTheCardQuota`
- [x] 5.4 Construir `FreeQuerySearchResponse` con grupos, argumentario y su estado, citas, intención, abstención, avisos **de consulta**, repregunta y motivo de degradación; `usage` y el reparto de tiempos **sólo para administrador**. Tests: `FreeQuery_ForOperator_CarriesNoUsage`, `FreeQuery_DoesNotCarryPieceWarnings`
- [x] 5.5 Comprobar que el circuito generativo **no abre el de recuperación**. Test: `FreeQuery_WhenGenerativeBudgetExceeded_LeavesRetrievalCircuitClosed`
- [x] 5.6 Persistir el evento con el origen generativo y el texto de la consulta, y que un fallo de telemetría **no rompa la búsqueda**. Tests: `FreeQuery_RecordsTheGenerativeOrigin`, `FreeQuery_WhenTelemetryFails_StillServes`

## 6. Tramo 2 · el toggle y la copia

- [x] 6.1 Añadir al servicio y a los tipos del frontend la llamada asistida y la de disponibilidad, con **desenlaces tipados que nunca lanzan** y `rate-limited` como miembro propio, siguiendo `ai-search.service.ts`
- [x] 6.2 Añadir el **toggle** con la ruta rápida por defecto, el coste dicho antes de pulsar y **sin recordar la elección entre visitas**. Tests: `should default to the fast route`, `should state the cost difference before any search`, `should issue no request when the route changes`, `should not remember the route between visits`
- [x] 6.3 Ampliar `lib/assist-copy.ts` con **los dos rechazos como textos distintos**, `filters_too_narrow`, los dos estados de consulta sin ruta y «sin fuente verificable», con sus tests directos. Tests: `should word an out-of-domain refusal differently from a not-in-catalogue one`
- [x] 6.4 Implementar la **partición de avisos por sujeto**: los de consulta se pintan, los de pieza no, y un código desconocido cae en la etiqueta neutra. Tests: `should render a query warning`, `should not render a piece warning above the result list`, `should fall back to a neutral label for an unknown query warning`

## 7. Tramo 2 · los dieciséis estados en pantalla

- [x] 7.1 Escribir la **tabla de los dieciséis estados** en `design.md` o en un módulo de copia comentado, con qué trae cada uno y qué acción ofrece, **antes** de tocar el render
- [x] 7.2 Pintar el bloque de argumentario con citas desplegables y `claimScope`, reutilizando lo de C36, y **«sin fuente verificable» como línea discreta**. Tests: `should state a withdrawn citation without alarming`, `should not describe a withdrawn citation as invented`
- [x] 7.3 Distinguir **el estado de consulta admitida sin ruta del de clasificador degradado**: al segundo **no se le pide reformular**. Tests: `should invite rephrasing when the classifier could not route`, `should not invite rephrasing when the classifier did not run`
- [x] 7.4 Que `route=knowledge` con cero piezas **no se anuncie como vacío**. Test: `should not announce an empty result set on the knowledge route`
- [x] 7.5 Pintar la **repregunta verbatim** y devolver el foco a la caja. Test: `should render the clarification question and return focus to the query box`
- [x] 7.6 No pintar citas cuando no hay prosa. Test: `should render no citation when there is no argument`
- [x] 7.7 Estado de carga con la línea de expectativa en la ruta asistida. Test: `should state that the assisted answer may take seconds while in flight`
- [x] 7.8 **Verificación del tramo 2**: `npm run build` y `dotnet build` en verde, las tres suites comparadas **por nombres**, y `openspec validate --all --strict` en verde

## 8. Tramo 2 · la latencia, medida

- [x] 8.1 Medir **p50 y p95 extremo a extremo por .NET** sobre las 42 consultas, como hizo C34 para los modos anclados, y publicarlo. Si el p95 no cabe en el presupuesto de 10 s, **disparar el corte pre-autorizado**: no generar en la ruta `catalog` de M1, y **declararlo**
- [x] 8.2 Publicar el **reparto de los dieciséis estados** sobre esas 42 consultas, partiendo `route=none` por `intent`, y persistir el artefacto

## 9. Tramo 2 · documentación mínima para que no se repita la avería

- [x] 9.1 Anotar **los tres interruptores** —búsqueda asistida, ficha y consulta libre— en la documentación de puesta en marcha, con el hecho de que su ausencia deja la pantalla sirviendo en degradado sin decirlo

## 10. Tramo 3 · la abstención y los vacíos

- [x] 10.1 Implementar la **sonda vectorial sin filtro** en `retrieval/orchestrator.py`, **secuencial**, reutilizando el vector y **sólo cuando la petición trae filtros**. Tests: `test_filtered_request_issues_two_statements`, `test_unfiltered_request_issues_one_statement`, `test_probe_costs_no_provider_call`, `test_probe_never_reaches_the_response`
- [x] 10.2 Pasar las distancias de la sonda a `should_abstain` y **persistirlas** junto a la ventana, para que `--rescore` siga pudiendo recalcular una pasada filtrada. Tests: `test_abstention_reads_the_unfiltered_profile`, `test_rescore_recomputes_the_decision_from_the_persisted_probe`
- [x] 10.3 Añadir la traza de la sonda al registro de etapa, **sin vector y sin texto de consulta**. Test: `test_probe_log_carries_no_vector_and_no_query`
- [x] 10.4 Añadir `filters_too_narrow` al vocabulario cerrado y emitirlo cuando el perfil sin filtro tiene pico y el filtrado es escaso, **en las dos rutas**. Tests: `test_narrow_filter_over_answerable_query_is_declared`, `test_unanswerable_query_abstains_instead_of_blaming_the_filter`
- [x] 10.5 Implementar la **coerción a `both`** cuando el veredicto es servido, sin eje pendiente y sin índice, con la causa `router_index_absent` en el registro. Tests: `test_served_verdict_without_index_is_routed_to_both`, `test_coercion_is_recorded_with_its_own_cause`
- [x] 10.6 Pintar los dos mensajes del filtro estrecho y de la abstención distinguidos. Tests: `should tell a narrow filter from an unanswerable query`
- [x] 10.7 Medir la **tasa de `router_index_absent`** tras la coerción y el **efecto de la sonda sobre la latencia de una búsqueda filtrada**, y publicar las dos

## 11. Tramo 3 · verificación de completitud

- [x] 11.1 Recorrer **campo a campo** `SalesAssistResponse`, `AssistedSearchResponse` y `FreeQuerySearchResponse`, y por cada campo **señalar dónde se pinta o declarar por qué no**. Es la disciplina que habría cazado las tres infracciones que la exploración encontró; el resultado va escrito en el informe de implementación

## 12. Tramo 4 · «todos los puntos de venta» (primer candidato a corte)

- [x] 12.1 Añadir la **tercera clase de ámbito** a `AiCallScope`, sin constructor público y sin centinela. Tests: `ForAllPointsOfSale_CarriesNoPointOfSale`, `AiCallScope_ExposesExactlyThreeConstructionPaths`
- [x] 12.2 Aceptarla **sólo** en recuperación y assist, y **rechazarla** en la ficha, los sustitutos y el inventario, antes de emitir petición. Tests: `ForAllPointsOfSale_IsAcceptedByRetrievalAndAssistance`, `ForAllPointsOfSale_IsRefusedBySubstitutes`, `ForAllPointsOfSale_IsRefusedByInventory`
- [x] 12.3 Añadir el **tercer perfil de claims** en `auth.py` y `deps.py`, aplicado sólo a recuperación y assist. Tests: `test_retrieval_accepts_a_token_without_pos_claim`, `test_pos_scoped_route_still_rejects_it`, `test_rejection_does_not_reveal_the_missing_claim`
- [x] 12.4 Autorizar el ámbito a **operarios y administradores**, con requisito y test que lo nombren, y seguir rechazando un punto de venta concreto no asignado. Tests: `FreeQuery_ForOperatorWithAllPointsOfSale_IsServed`, `FreeQuery_WhenNamingAnUnassignedPointOfSale_IsRefused`
- [x] 12.5 La **etiqueta de existencias nombra la tienda**, y sin tienda dice que hay que seleccionar una en vez de mostrar un cero. Tests: `should name the shop in the stock label`, `should not show a zero when no shop is selected`
- [x] 12.6 **Deshabilitar el botón de ficha** sin tienda, y que cambiar de tienda **no llame a ningún modelo**. Tests: `should disable the sale card action when no shop is selected`, `should issue no assisted request when the shop changes`

## 13. Tramos 5 y 6 · la fila y el embudo

- [x] 13.1 La **fila enseña su grupo**, con degradación al SKU y nada escrito con un solo miembro, sin reordenar ni ofrecer venta de otro miembro. Tests: `should state what else the family carries`, `should name a member by its SKU when the variant label is missing`, `should state nothing for a single-member group`
- [x] 13.2 Ampliar el **embudo de administrador**: `ai_ms` frente a `total_ms`, modelo, tokens, motivo de degradación y contadores, plegado por defecto. Tests: `should split the elapsed time in the assisted funnel`, `should show no monetary amount in the funnel`, `should show neither the query nor the argument in the funnel`, `should render no funnel for a non-administrator`

## 14. Cierre

- [x] 14.1 **Declarar aplazado con su motivo** todo tramo que no haya entrado, en el informe de implementación y en `openspec/DEFERRED_TASKS.md`. Cortar el tramo 3 deja el filtro estrecho **más grave que antes de C40**, porque M1 añade el párrafo que hoy no existe: eso se escribe
- [x] 14.2 **Comprobación con datos reales** en local, con `STUB_MODE=false` y credencial real: una consulta de catálogo, una de conocimiento, una mixta, los dos rechazos, una repregunta, un filtro estrecho y el ámbito «todos». Comprobar de paso si el **corpus viaja en la imagen** —tarea diferida de C34, que pesa más aquí: sin corpus, M1 responde siempre sin citas— y declararlo si no
- [x] 14.3 Comparación final de las **tres suites por nombres** contra la línea base del grupo 1 — cero nombres desaparecidos y cero nuevos en rojo—, `dotnet build` y `npm run build` en verde, y `openspec validate --all --strict` en **0 failed**
- [x] 14.4 Escribir `Documentos/Proyecto Final AIEng/informes/c40-implementation-measurements.md` con las cinco cifras: marcadores antes y después de `v5`, reparto de los dieciséis estados, latencia p50/p95 por .NET, tasa de `router_index_absent` y efecto de la sonda
- [x] 14.5 Actualizar la documentación de contexto: `Documentos/epicas.md`, la ficha del plan, el diseño (**§15.12 y §15.13 cerradas**, §15.14 matizada), `frontend/README.md`, `backend/README.md`, `ai-service/README.md` y `openspec/DEFERRED_TASKS.md`
- [x] 14.6 Comprobar que **no queda ningún TODO ni FIXME** sin tarea de seguimiento asociada
