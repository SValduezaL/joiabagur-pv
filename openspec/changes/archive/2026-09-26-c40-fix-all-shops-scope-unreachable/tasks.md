## 1. Puerta de entrada

- [x] 1.1 **Medir la línea base de las dos suites antes de tocar nada**, sobre el commit de partida, y guardar los **nombres** de los fallos. `dotnet test` (~50 rojos) y `npm run test` en `frontend/` (~113-114 de 729 en 14 ficheros). Leer la **línea de resumen** y no el código de salida: `vitest` sale 0 al pipearlo, y un `JoiabagurPV.API.exe` vivo hace que `dotnet test` salga 0 con cero tests ejecutados. Validación: la lista de nombres queda escrita, y `git status` está limpio
- [x] 1.2 Confirmar sobre el árbol las **cuatro afirmaciones que dimensionan el change**, porque si alguna ha cambiado el plan cambia: `AssistedSearchRequestValidator` tiene `.NotEmpty()` en `PointOfSaleId`; `GetAvailability` vive en `AssistedSearchService` y consulta tres clases de opciones; `compose.demo.yaml` no declara `AiFreeQuerySearch__EnabledByDefault`; y `SearchLexicalAsync` acepta `Guid?` **sin** agrupar por producto. Validación: las cuatro comprobadas, o el desvío anotado en el informe

## 2. Backend · el predicado, escrito una sola vez

- [x] 2.1 Extraer el predicado del ámbito a un método de extensión `IsEnabledFor(this <opciones>, Guid?)` para `AiFreeQuerySearchOptions`, `AiSalesAssistOptions` y `AiSearchOptions`, resolviendo a `EnabledByDefault` cuando no hay tienda — la lectura estrecha de D4. Validación: compila, y los tests existentes de las tres clases siguen verdes
- [x] 2.2 Hacer que **`FreeQuerySearchService` consuma el predicado extraído** en lugar de su `IsEnabled` privado, para que sonda y ruta no puedan derivar. Validación: los tests de `FreeQuerySearchService` sobre el interruptor siguen verdes sin cambiarlos
- [x] 2.3 Test .NET de que el predicado es **uno**: `IsEnabledFor_WithoutPointOfSale_MatchesTheRoutePredicate` — para la misma configuración, lo que la sonda calcularía y lo que la ruta aplica coinciden en los tres interruptores. Es la guarda de R4

## 3. Backend · la sonda acepta la ausencia

- [x] 3.1 `AiSearchAvailabilityResponse.PointOfSaleId` pasa a `Guid?`, con su documentación diciendo que **nulo es el ámbito global y `Guid.Empty` no viaja nunca**. Validación: compila
- [x] 3.2 `IAssistedSearchService.GetAvailability` y su implementación pasan a `Guid?`, usando el predicado del grupo 2 en los tres interruptores. `SemanticSearchAvailable` **se sigue reportando con su predicado normal** (D4: la sonda describe interruptores). Validación: compila, y los cinco tests existentes de `GetAvailability` siguen verdes
- [x] 3.3 El controlador pasa a `[FromQuery] Guid? pointOfSaleId`: ausente → ámbito global; **`Guid.Empty` → 400** con el texto de la ruta de consulta libre, «El punto de venta no es válido. Omítelo para buscar en todas las tiendas.». Validación: compila
- [x] 3.4 Tests .NET de la sonda: `Availability_WithoutPointOfSale_ReturnsDefaultScope` (200, identificador nulo), `Availability_WithBlankPointOfSale_ReturnsBadRequest` (400) y `Availability_WithoutPointOfSale_CallsNoAiService`. **Cliente fresco de la factoría** para la llamada no autenticada, si se añade — el `HttpClient` compartido arrastra las cookies de cada login
- [x] 3.5 Comprobar que **`ai-service/openapi.json` no tiene diff** y que no se ha creado ninguna migración. Validación: `git status` sobre esos dos árboles, y `dotnet build` en verde

## 4. Frontend · tipos y servicio

- [x] 4.1 `AssistedSearchRequest.pointOfSaleId` y `FreeQuerySearchRequest.pointOfSaleId` pasan a opcionales, con el comentario corregido: hoy dicen *«Required»* y *«Always required — never inferred by the server»*, que es lo que este change retira. `AiSearchAvailability.pointOfSaleId` admite `string | null`
- [x] 4.2 `aiSearchService.getAvailability` acepta la ausencia y **omite el parámetro** en lugar de enviarlo vacío. Validación: `tsc --noEmit` filtrado a los ficheros propios, sin errores nuevos — es la puerta de R7, porque `npm run build` es verde sobre un error de tipos

## 5. Frontend · el control del ámbito

- [x] 5.1 Un centinela de ámbito local al módulo, y la opción **«Todas las tiendas»** en el `SelectContent` condicionada a `isAdmin`, **la primera de la lista** y separada visualmente de las tiendas. **No se toca** la condición de renderizado del selector. Validación: la opción aparece para administrador y no para operario, comprobado en el navegador o en el test del grupo 8
- [x] 5.2 El centinela **se traduce a ausencia** antes de la petición, siguiendo el patrón que la página ya usa para la categoría. Es la restricción que no se puede violar: `Guid.Empty` sería el comodín por accidente
- [x] 5.3 Relajar los dos guards: el `if (!trimmed || !pointOfSaleId) return;` de `runSearch` y el `disabled` del botón *Buscar*, de modo que el ámbito sin tienda sea **un estado válido de la pantalla** y no un formulario incompleto
- [x] 5.4 El efecto de disponibilidad **consulta la sonda también sin tienda**, en vez de poner `availability` a nulo y `settled` a falso — que es lo que deja la insignia en «Comprobando disponibilidad…» para siempre. Se conserva la guarda contra respuestas obsoletas
- [x] 5.5 Comprobar que **el efecto de carga sigue fijando la primera tienda activa** también para el administrador: el ámbito global no es el valor por defecto de nadie. Validación: el escenario nuevo del requisito de ámbito

## 6. Frontend · el toggle de ruta y el callejón sin salida

- [x] 6.1 `SearchRouteToggle` gana la propiedad de indisponibilidad del lado semántico, sobre el `RouteOption` que ya acepta `disabled` y `unavailableReason` y ya emite `data-testid="route-unavailable-<route>"`. Validación: el `testid` del lado semántico se renderiza cuando se le pasa motivo
- [x] 6.2 Con el ámbito global seleccionado, la ruta pasa a `'assisted'` y la rápida queda deshabilitada **con motivo de ámbito** — «la búsqueda rápida trabaja sobre una tienda concreta»—, nunca con el del interruptor. Validación: los dos tests del grupo 8 que lo separan
- [x] 6.3 **El callejón sin salida se enuncia** (D3): si el ámbito global está seleccionado y la respuesta asistida está apagada, una línea bajo el selector dice que el ámbito la necesita y que está desactivada. **No se pre-deshabilita la opción**, porque exigiría leer la sonda dos veces
- [x] 6.4 La línea de consecuencia al seleccionar el ámbito: resultados de todo el catálogo, y hay que elegir una tienda para leer existencias. Validación: el escenario del requisito nuevo

## 7. Frontend · la copia que hoy queda falsa

- [x] 7.1 Variante de `switched_off` que **no diga «en esta tienda»** cuando el ámbito es global, en `UNAVAILABLE_REASONS` / `assistedUnavailableText`. Validación: el test del grupo 8 que comprueba que ese texto no aparece en ámbito global
- [x] 7.2 Repasar las cadenas del panel que asumen una tienda seleccionada —placeholder del selector, subtítulo de la página *«lo que hay en tu tienda»*— y corregir las que sean falsas en este ámbito. Validación: revisión a ojo de la pantalla en los dos ámbitos, anotando lo que se deja y por qué

## 8. Tests de página, que es donde nunca se probó el camino

- [x] 8.1 `should offer the every-shop scope when the caller is an administrator` y `should not offer the every-shop scope when the caller is an operator` — el segundo es el que protege la estrechez y el backend
- [x] 8.2 `should issue no search request when the scope changes to every shop` y `should clear the displayed results when the scope changes`
- [x] 8.3 `should disable the fast route with a reason of scope when every shop is selected` y `should not state the semantic path as switched off when the fast route is disabled by scope`
- [x] 8.4 **`should keep the assisted route enabled when every shop is selected`** — es el hallazgo §1.2 del ticket y **el test que de verdad cierra este change**
- [x] 8.5 `should state that the scope needs the assisted answer when it is switched off` y `should not claim the assisted answer is off at this shop when every shop is selected`
- [x] 8.6 `should send no point of sale when searching every shop` — que la petición **no lleva el campo**, no que lo lleva vacío
- [x] 8.7 `should state that a shop is needed to read stock when every shop is selected` y `should disable the sale card action when every shop is selected`, **a nivel de página** y no pasando props al componente, que es lo que los tests de la fila ya hacían y por lo que no cubrían esto
- [x] 8.8 `should settle the availability statement when every shop is selected` — que la insignia sale del texto de pendiente

## 9. Despliegue · el prerrequisito

- [x] 9.1 `AiFreeQuerySearch__EnabledByDefault: "true"` en `compose.demo.yaml`, con su comentario de clase junto a los otros dos y la razón de por qué faltaba. Validación: el fichero declara los **tres** interruptores de la familia

## 10. Cierre

- [x] 10.1 **Anotar en `openspec/DEFERRED_TASKS.md`** las dos tareas diferidas **como una sola**, con su motivo: extender `POST /api/ai/search` al ámbito global **exige** antes agrupar por producto en `SearchLexicalAsync`, porque `BuildResultsAsync` hace `ToDictionary(ProductId)` incondicionalmente y su rama nula es un **HTTP 500** — y se activaría primero en desarrollo local, donde la ruta degradada es la que corre. Es la mitigación de R1
- [x] 10.2 **Comprobación manual en el entorno levantado**, por la interfaz y con los dos roles — es la única puerta que detecta esta clase de defecto, porque `openspec validate` pasa sobre specs bien formadas y falsas. Con administrador: seleccionar el ámbito, leer la insignia y el toggle, buscar, revisar la fila, volver a una tienda concreta. Con operario: que la opción no exista. Y con el interruptor apagado: que el callejón sin salida se enuncie · **Ejecutada por el desarrollador el 2026-09-26** sobre el entorno local, con los dos roles. Las cuatro comprobaciones de administrador pasan. La de operario pasa **por la vía de la asignación única**: los tres operarios sembrados tienen exactamente una tienda, así que el selector no se renderiza por la regla previa de C16 —que este change no toca— y por tanto la opción no se ofrece. **El camino del operario con varias tiendas no existe en los datos sembrados** y queda cubierto sólo por el test de página. Evidencia en `qa.md` §6
- [x] 10.3 **Comparación final de las dos suites por nombres** contra la línea base de 1.1 — **cero nombres nuevos en rojo en el área propia**, y los que difieran dentro de los ficheros y clases ya conocidos por inestables. Más `dotnet build`, `npm run build` y **`tsc --noEmit` filtrado** en verde
- [x] 10.4 `openspec validate --all --strict` en **0 failed** — la forma de un solo change no es la puerta
- [x] 10.5 Actualizar la documentación: `Documentos/epicas.md` (EP15, la anotación de implementación), y `frontend/README.md` y `backend/README.md` en lo que toque a la sonda y al ámbito. `Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md` y el ticket ya están al día
- [x] 10.6 Comprobar que **no queda ningún TODO ni FIXME** sin tarea de seguimiento asociada, y que la limitación queda declarada: el ámbito global **sólo se sirve por la ruta asistida** y **no se registra en telemetría**
