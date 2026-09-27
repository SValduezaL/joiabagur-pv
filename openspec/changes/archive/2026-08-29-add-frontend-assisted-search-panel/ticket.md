# T-AIENG-016: Assisted search panel with sale attribution (C16)

> Ticket técnico del change OpenSpec `add-frontend-assisted-search-panel`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-016](../../../../Documentos/Historias/AI-Eng/HU-AIENG-016.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C16 y §0 de 2026-08-29), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.4, §7.6, §11), sesión de exploración 2026-08-29, código real de `frontend/src/`, `backend/src/` y `ai-service/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-016 / C16** — Panel «Buscar con ayuda» en `/sales/new/assisted`: envío explícito, filtros de materiales, cinco estados, arrastre de `searchEventId` hasta la caja y tramo .NET de atribución de venta

---

## Contexto y Problema

C15 dejó `POST /api/ai/search` con hidratación autoritativa, degradación acotada, caché de candidatos y telemetría completa. **Nadie le llama.** El operador sólo puede encontrar un producto escaneando su código o tecleando el SKU exacto, porque `ProductService.SearchProductsAsync` casa la cadena completa contra el nombre y devuelve lista vacía ante cualquier frase.

Al diseñar sobre el código entregado aparecen cuatro hechos que la ficha v3 no podía conocer.

**Primero: B5 no es implementable desde el navegador, y detrás hay una spec viva que miente.** La requirement *«Sale attribution is carried by the sale, not by the event»* de `ai-search-telemetry` está archivada como cumplida, y la columna `Sale.SearchEventId` existe con índice y clave foránea desde C04. Pero ni `CreateSaleRequest` ni `BulkSaleLineRequest` tienen el campo, y ningún servicio lo asigna: el único sitio del repositorio que lo escribe es `AiSearchEventsControllerTests`, tocando la entidad a mano. Es la clase de defecto de la obligación A1 —compila, los tests pasan, `openspec validate --all --strict` da verde y la columna llega vacía—, agravada porque aquí hay una spec afirmando lo contrario.

**Segundo: teclear cuesta dinero.** La clave de la caché de candidatos de C15 incluye la cadena de consulta completa, así que ningún prefijo acierta. Con `debounce` de 400 ms una consulta de treinta caracteres genera de tres a seis peticiones, cada una con su embedding facturado, y el límite de 30 peticiones por minuto y por usuario se agota en cinco o seis consultas. El presupuesto de recuperación son 800 ms más hidratación: «resultados mientras escribo» nunca estuvo disponible.

**Tercero: los filtros duros se apilan y ninguno es del panel.** El de materiales corre en el SQL de C14 —`AND materials && CAST(:materials AS text[])`— **antes** del umbral y del `LIMIT`; la hidratación por punto de venta de C15 corta después. Con las coberturas de C10, un material poco frecuente combinado con Fornells (0,22) vacía la página casi con seguridad.

**Cuarto: los «cero resultados» son cuatro, no tres.** La spec de C15 exige que superar el límite de peticiones (`429`) sea distinguible de la indisponibilidad de la IA. La ficha sólo enumeraba tres.

**Estado actual del código (verificado 2026-08-29 en repo):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-frontend-assisted-search-panel` | **Scaffold** (`.openspec.yaml`, schema `spec-driven`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `POST /api/ai/search` (`AiSearchController`) | **Listo.** `[Authorize]`, `[EnableRateLimiting(RateLimitPolicies.AiSearch)]`, sin versión en la ruta. Devuelve `403` (POS no asignado), `400` (POS inactivo o petición inválida), `429` |
| `AssistedSearchRequest` | `query`, `pointOfSaleId` (**obligatorio**), `pageSize?`, `searchSessionId?`, `materials[]`, `category?` |
| `AssistedSearchResponse` | `results[]`, `searchEventId?`, `aiAvailable`, `lowConfidence`, `pointOfSaleId`, `candidatesReturned`, `survivedHydration` |
| `AssistedSearchResultDto` | `productId`, `sku`, `name`, `price`, `quantityAtPointOfSale`, `hasStock`, `primaryPhotoUrl?`, `collectionName?`, `score?`, `matchReasons[]`, `familyId?`, `variantLabel?`. **No lleva `materials`** |
| `AssistedSearchService.BuildResultsAsync` | Construye el DTO y **descarta `candidate.Materials`**, que sí llega del retriever |
| `AiSearchOptions` | `DefaultPageSize = 10`, `MaxPageSize = 50`, `RateLimitPermitLimit = 30`, `RateLimitWindowSeconds = 60`, `CandidateCacheTtlSeconds = 60` |
| `POST /api/ai/search-events/{id}/selection` | **Listo** (C04). Cuerpo de un campo: `productId`. `404` si el evento no existe, `403` si no es del usuario — **sin excepción de administrador** |
| `Sale.SearchEventId` | Columna, índice `IX_Sales_SearchEventId` y FK con `SetNull`, desde la migración de C04. **Ningún servicio la escribe** |
| `CreateSaleRequest` / `BulkSaleLineRequest` | `productId`, `quantity`, `price?`, `photoBase64?`, `photoFileName?` (+ POS y método de pago en el request padre del masivo). **Sin `searchEventId`** |
| `ai.product_document` | Indexa `materials`, `family_id`, `variant_label`. `variant_label` lo puebla **C18**: hoy nulo |
| `retrieval/orchestrator.py` | `match_reasons=["vector"]` **literal**, para todos los resultados, hasta C21 |
| `vocabularies.yaml` → `materials.terms` | 9 términos: `plata`, `oro`, `baño de oro`, `hilo`, `latón`, `acero`, `resina`, `cuero`, `perla`. **Ningún endpoint .NET los expone** |
| `ProductAiProfile.MaterialsJson` | Existe en .NET, poblado vía `AiCatalogController` / `ProductAiProfileService`. No hay ruta de lectura agregada |
| `frontend/src/pages/sales/index.tsx` | Hub con **dos** tarjetas (escanear, manual) + accesos a carrito e historial |
| `frontend/src/pages/sales/scan.tsx` | Patrón de entrega: `navigate(ROUTES.SALES.NEW, { state: { productId } })` |
| `frontend/src/pages/sales/new.tsx` | **702 líneas.** Lee `location.state.productId`; dos salidas: `salesService.createSale` y `addLine` |
| `frontend/src/pages/sales/cart.tsx` | `salesService.createBulkSales` con `Idempotency-Key` |
| `CartLine` (`types/sales.types.ts`) | Sin `searchEventId` |
| `pointOfSaleService.getPointsOfSale()` | Devuelve asignados al operador y todos al administrador. `PointOfSale.isActive` disponible |
| `apiClient` (`services/api.service.ts`) | `VITE_API_BASE_URL` **ya incluye `/api`**. Interceptor que normaliza el error a `{ message, statusCode, errors }` |
| `useDebouncedCallback` | Existe y lo usa `products/catalog.tsx`. **No se usa aquí** |
| Metronic / `components/ui/` | `card`, `badge`, `button`, `input`, `select`, `skeleton`, `alert`, `toggle-group`, `collapsible`, `separator`, `tooltip` disponibles. **Sin componentes nuevos de librería** |
| MSW en tests | `onUnhandledRequest: 'warn'` — una petición sin manejador **no rompe el test** |
| Migraciones EF | Seis previstas (C04, C07, C08, C19, C27, C29). C16 **no abre una séptima** |

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `frontend/src/pages/sales/assisted.tsx` | **Nuevo.** Panel completo: episodio, envío explícito, filtros, selector de POS, cinco estados, embudo de administrador |
| `frontend/src/components/sales/assisted-search-result-row.tsx` | **Nuevo.** Fila de resultado aislada, **para que C36 la amplíe en vez de sustituirla** |
| `frontend/src/services/ai-search.service.ts` | **Nuevo.** `search()` y `reportSelection()`, con mapeo de `429`/`403`/`400` a estados propios |
| `frontend/src/types/ai-search.types.ts` | **Nuevo.** Espejo de `AssistedSearchRequest` / `AssistedSearchResponse` / `AssistedSearchResultDto` |
| `frontend/src/config/` | **Nuevo.** Constante del vocabulario cerrado de materiales, con etiqueta mostrada y término canónico |
| `frontend/src/routing/routes.tsx` · `app-routing-setup.tsx` | `SALES.NEW_ASSISTED = '/sales/new/assisted'`, ruta perezosa bajo `ProtectedRoute` + `Layout8` |
| `frontend/src/pages/sales/index.tsx` | **Tercera tarjeta** «Buscar con ayuda» |
| `frontend/src/pages/sales/new.tsx` | Lee `searchEventId` del estado de navegación; lo envía en `createSale` y lo pasa a `addLine` |
| `frontend/src/pages/sales/cart.tsx` | Envía `searchEventId` **por línea** en `createBulkSales` |
| `frontend/src/types/sales.types.ts` | `CartLine.searchEventId?`, `CreateSaleRequest.searchEventId?`, `BulkSaleLineRequest.searchEventId?` |
| `backend/.../DTOs/Sales/CreateSaleRequest.cs` · `CreateBulkSalesRequest.cs` | `Guid? SearchEventId` |
| `backend/.../Services/` (servicio de ventas) | Asigna `Sale.SearchEventId` tras comprobar **existencia y propiedad**; degrada a nula sin fallar |
| `backend/.../DTOs/Ai/AssistedSearchDtos.cs` | `List<string> Materials` en `AssistedSearchResultDto` |
| `backend/.../Services/AssistedSearchService.cs` | `Materials = candidate?.Materials ?? []` en `BuildResultsAsync` |
| `backend/src/JoiabagurPV.Tests/` | Unitarios del servicio de ventas; integración de la atribución |
| `openspec/changes/add-frontend-assisted-search-panel/` | proposal, **design.md**, specs (capacidad nueva + `## MODIFIED` de `sales-management` y de `ai-assisted-search`), tasks |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-016 (**en el apply**) |
| `ai-service/`, `openapi.json`, `IAiGatewayClient`, migraciones EF, `/api/v1/products/search`, buscador por SKU de `new.tsx` | **Sin cambios** |

---

## Especificaciones Técnicas

### Rutas y endpoints consumidos

| Ruta | Método | Rol | Notas |
|---|---|---|---|
| `/ai/search` | `POST` | Autenticado | Ruta **relativa**: `VITE_API_BASE_URL` ya trae `/api` (obligación B1) |
| `/ai/search-events/{id}/selection` | `POST` | Autenticado, propietario del evento | Cuerpo `{ productId }`. Sin `await` en el panel |
| `/point-of-sales` | `GET` | Autenticado | Ya filtra por rol; el panel descarta además los `isActive === false` |

**Endpoints modificados (tramo .NET):** `POST /api/v1/sales` y `POST /api/v1/sales/bulk` aceptan `searchEventId` **opcional**. Campo nuevo y anulable: **sin ruptura de contrato**.

### Panel: modelo de interacción

- **Episodio.** `searchSessionId = crypto.randomUUID()` en el montaje del panel, en un `useRef`. Se envía en **todas** las búsquedas de esa visita. Cambiar de punto de venta no lo cambia (B2).
- **Disparo.** Enter o botón. **Prohibido `useDebouncedCallback`** sobre la caja de consulta: la clave de caché de C15 incluye la cadena completa, ningún prefijo acierta, y el límite es de 30 peticiones por minuto y por usuario.
- **Consultas de ejemplo.** 3-5 *chips* que rellenan la caja **y** lanzan la búsqueda en un gesto.
- **Filtros.** Materiales en multi-selección (`toggle-group`) sobre el vocabulario cerrado, más categoría de pieza (`select` sobre `piece_type`). **No disparan solos.** Acción visible de «quitar filtros».
- **Punto de venta.** Preseleccionado; selector oculto con un único POS asignado; sólo activos. Cambiar de POS **limpia resultados y no relanza**.
- **Guardia de respuestas obsoletas.** Identificador monótono de petición o `AbortController`: enviar → cambiar POS → enviar puede resolver fuera de orden.
- **Orden.** Se renderiza `results` tal cual llega. **Ningún `sort()` en cliente** (B3).

### Estados de la interfaz

| Condición | Estado | Mensaje |
|---|---|---|
| petición en vuelo | Cargando | Esqueletos, no lista vacía |
| `results.length > 0` | Resultados | Filas en orden recibido |
| `aiAvailable && lowConfidence && results = []` | **Abstención** | «No he encontrado nada que encaje» + sugerir reformular |
| `aiAvailable && !lowConfidence && candidatesReturned > 0 && results = []` | **Sin surtido** | «Hay piezas parecidas, ninguna en esta tienda» + **quitar filtros** |
| `!aiAvailable` | **Degradado o desactivado** | «Búsqueda asistida no disponible; resultados por texto» |
| HTTP `429` | **Cuota agotada** | «Demasiadas búsquedas seguidas, espera unos segundos» — **nunca** como caída de la IA |
| HTTP `403` | Sin acceso al POS | Distinguible de un fallo del servicio |
| HTTP `400` | Petición inválida / POS inactivo | Se pintan los `errors` del backend |
| `0 < results.length < pageSize` | **Página corta** (B7) | Línea discreta: resultados en esa tienda y candidatos considerados |

**Embudo de administrador.** Bloque `collapsible`, colapsado, visible sólo con rol administrador: identificador de correlación y `candidatesReturned → survivedHydration → results.length`.

### Fila de resultado

Foto (`getImageUrl`, con reserva cuando no hay), SKU, nombre, precio en **EUR (€)** con formato es-ES, stock del punto de venta con marca de agotado cuando `hasStock === false` —**la fila se muestra igual**—, insignia de origen y **chips de materiales**.

`variantLabel` se pinta **sólo cuando existe**: hoy es nulo en todas las filas y se enciende solo cuando llegue C18. `matchReasons` **no se pinta**: es `["vector"]` literal hasta C21; la insignia se deriva de `aiAvailable` con un mapa preparado para que C21 aporte valores reales sin tocar el panel. `score`, `familyId` y `collectionName` no se pintan en C16; llegan en el DTO y los consumirá C36.

### Selección y arrastre

```text
clic  →  POST /ai/search-events/{searchEventId}/selection   (sin await, sin toast de error)
      →  navigate('/sales/new', { state: { productId, searchEventId } })
                     │
        new.tsx ─────┼──▶ createSale({ …, searchEventId })
                     └──▶ addLine({ …, searchEventId })  →  CartLine  →  cart.tsx
                                                                        └─▶ BulkSaleLineRequest.searchEventId (por línea)
```

`searchEventId` nulo —la telemetría no persistió— **omite la llamada en silencio**: ni error, ni aviso. No se usa `sendBeacon`: la navegación es de SPA y `sendBeacon` no puede poner la cabecera de autorización de `apiClient`.

### Tramo .NET: atribución

- `Guid? SearchEventId` en `CreateSaleRequest` y en `BulkSaleLineRequest`. **Opcional**: una venta sin búsqueda detrás sigue siendo válida.
- Antes de asignar, comprobación explícita de que el evento **existe y pertenece al usuario que vende**. Sin excepción de administrador, por coherencia con `RecordSelectionAsync`: un evento registra lo que hizo una persona concreta, y permitir atribuirse el de otro corrompería el dato sin dejar rastro.
- Un identificador desconocido o ajeno → `SearchEventId = null`. **Nunca** un error de validación, **nunca** una venta fallida. No se delega en la clave foránea, que abortaría la transacción en lugar de degradar.
- El masivo atribuye **línea a línea**: cada `Sale` creada lleva la suya.
- Sin migración: columna, índice y clave foránea son de C04.

### Vocabulario de materiales

Constante en el frontend, espejo de `ai-service/src/jbg_ai/enrichment/vocabularies.yaml` → `materials.terms`, con etiqueta mostrada y **término canónico enviado**. Test de fijación que congela la lista. La deriva no da error: devuelve cero.

---

## Arquitectura

- **Frontera de servicio intacta.** El frontend habla sólo con .NET. C16 no toca `ai-service/` ni el contrato congelado; la única razón por la que se cruza a `Application/` es que la spec de atribución no se puede cumplir de otro modo.
- **La verdad sigue siendo de .NET** (decisión 11 del diseño). El panel no recalcula precio ni stock, no reordena y no filtra en cliente: todo eso lo decidió la hidratación de C15.
- **Patrón de entrega ya validado.** `navigate(state)` es lo que hacen `scan.tsx` y `new-image.tsx`; el estado sólo crece en un campo.
- **Capas.** Frontend: `pages` → `services` → `apiClient`. Backend: `API` → `Application` (objetos de transferencia y servicio de ventas) → `Domain` (`Sale`). No se toca `Infrastructure` salvo lo que ya persiste `Sale`.
- **Aislamiento para C36.** La fila de resultado es un componente propio desde el día uno: C36 añadirá argumentario, citas y agrupación por familia ampliándolo, no reescribiendo la página.
- **Compatibilidad.** `searchEventId` es un campo nuevo y anulable en dos objetos de transferencia: los clientes existentes siguen funcionando. `materials` es un campo nuevo en una respuesta: aditivo. `ai-service/openapi.json` sin diff.
- **Lo que no se puede distinguir, y se acepta.** `aiAvailable: false` cubre tanto el circuito abierto como la asistencia desactivada en ese punto de venta. La telemetría los separa (`LexicalFallback` / `Disabled`), la API no; el mensaje al operador es el mismo.

---

## Definición de Hecho (DoD)

- [ ] Código según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] Frontend: Vitest + React Testing Library + MSW; nomenclatura `should [comportamiento] when [condición]`; queries accesibles; cobertura ≥ 70 %
- [ ] **Manejadores de MSW declarados explícitamente** para las dos rutas del panel: `onUnhandledRequest: 'warn'` deja pasar un test que no prueba nada
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus; integración con Testcontainers; nomenclatura `Método_Escenario_ResultadoEsperado`; cobertura ≥ 70 %
- [ ] Baseline de la suite medido con `git stash push -u` **antes** de comparar rojos: se compara el **conjunto de nombres** que fallan, no el número
- [ ] Los objetos madre de test fijan `.WithPhone("600123456")`: el generador de Bogus desborda `PointOfSale.Phone`
- [ ] Un test verifica que **teclear no emite peticiones** y que el envío emite exactamente una
- [ ] Un test verifica que los resultados se pintan **en el orden recibido**, con un fixture cuyo orden por precio o por nombre sea distinto del de llegada
- [ ] Un test verifica que las tres reformulaciones de una visita comparten `searchSessionId`
- [ ] Un test por cada uno de los **cuatro** estados sin resultados, incluido `429`
- [ ] Un test verifica que un fallo al reportar la selección **no bloquea la navegación** ni muestra error
- [ ] Un test verifica que `searchEventId` llega a la línea del carrito y de ahí a `BulkSaleLineRequest`
- [ ] Un test verifica que una venta con `searchEventId` **desconocido** y otra con uno **de otro usuario** se crean con atribución nula
- [ ] Un test verifica que una respuesta obsoleta tras cambiar de punto de venta se descarta
- [ ] Test de fijación del vocabulario de materiales
- [ ] **Sin migración de EF Core**
- [ ] Specs delta en `openspec/changes/add-frontend-assisted-search-panel/specs/`, incluidos los `## MODIFIED` de `sales-management` y `ai-assisted-search`
- [ ] `openspec validate --all --strict` → **0 failed** (no basta la forma de un solo change)
- [ ] `npm run build` y `dotnet build` sin errores; bundle inicial < 500 KB (ruta perezosa)
- [ ] Documentación: HU, este ticket, `Documentos/epicas.md` (EP14) en el apply
- [ ] Compatibilidad hacia atrás: `/api/v1/products/search`, buscador por SKU de `new.tsx` y `ai-service/openapi.json` sin cambios
- [ ] UI íntegramente en español (es-ES) y moneda EUR (€)
- [ ] Sin TODO/FIXME sin tarea de seguimiento
- [ ] Verificación **posterior** (no DoD de merge): búsqueda real desde `op-ciutadella` y desde `op-fornells` con el índice poblado, comprobando que la segunda declara página corta, que el embudo lo refleja y que la venta resultante guarda `SearchEventId`

No aplica: `uv run pytest`, regenerar OpenAPI, migración EF.

---

## Requisitos No Funcionales

- **Seguridad:** el punto de venta viaja en el cuerpo pero el servidor lo valida contra las asignaciones del usuario; el panel no puede ampliar su propio alcance. La atribución comprueba **propiedad** del evento, sin excepción de administrador. El `searchEventId` es un identificador opaco sin significado fuera de la telemetría. Sin secretos en el cliente.
- **Rendimiento y free-tier:** ruta perezosa como el resto (`bundle` inicial < 500 KB); **una** petición por búsqueda; sin `debounce` sobre la consulta; página por defecto 10 y tope 50, alineados con `AiSearchOptions`; imágenes por `getImageUrl` sin recarga adicional.
- **Coste:** cada búsqueda no cacheada factura un embedding. El envío explícito, los filtros que no disparan solos y el no relanzar al cambiar de punto de venta son controles de coste, no de estilo. §12 del diseño se compromete a que el coste esté instrumentado y reportado.
- **Observabilidad:** el identificador de correlación de C15 se muestra en el bloque de administrador, para poder cruzar una búsqueda concreta con los logs de .NET y de `jbg-ai`. La consulta del operador no se registra en cliente.
- **Accesibilidad y UX:** queries accesibles en los tests; los cinco estados son texto, no sólo iconografía; el resultado agotado se marca por texto además de por color.
- **Integridad de datos:** la venta **nunca** falla por la atribución; `Sale.Price` sigue siendo snapshot y esta historia no lo toca; el stock mostrado es el del punto de venta de la búsqueda, no la suma.

---

## Preguntas Abiertas

Ninguna pendiente de producto. Cerradas en la exploración del 2026-08-29 y registradas en §0 del plan.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿B5 se implementa sólo en frontend? | **No puede.** C16 incluye el tramo .NET mínimo. La alternativa —enviar un campo que el servidor descarta— es el patrón «código muerto sin síntoma» que el plan ya pagó con C04 |
| 2 | ¿Atribución con evento de otro usuario? | **Degrada a nula**, igual que un identificador desconocido. Coherente con `RecordSelectionAsync`, que exige propiedad sin excepción de administrador |
| 3 | ¿Dónde vive el panel? | **Ruta propia** `/sales/new/assisted` + tercera tarjeta. No dentro de `new.tsx` (702 líneas) ni en un `Sheet` |
| 4 | ¿`debounce` como en el catálogo? | **No.** Ningún prefijo acierta en la caché, se agota la cuota en cinco o seis consultas y «resultados al teclear» nunca fue posible con 800 ms de presupuesto |
| 5 | ¿Qué se pinta como «motivo»? | **Insignia de origen + chips de materiales.** `matchReasons` es `["vector"]` literal hasta C21 y no se pinta |
| 6 | ¿Y la talla? | `variantLabel`, **sólo cuando exista**. La puebla C18. No se hidrata `ProductAiProfile.SizeLabel` |
| 7 | ¿De dónde salen los materiales del filtro? | **Constante en el frontend**, espejo de `vocabularies.yaml`, con test de fijación. El endpoint que agregue los materiales del surtido de un POS es mejor producto y **se anota para C28** |
| 8 | ¿Cuántos estados sin resultados? | **Cuatro**, con `429` incluido. Más **página corta**, que no está vacía y también se declara |
| 9 | ¿Se enseña el embudo? | Sí, **colapsado y sólo a administradores**. Evidencia para §11 y §16 |
| 10 | ¿Un episodio por qué? | Por **montaje del panel**. Dos visitas que acaban en selección son dos episodios legítimos, no dos falsos abandonos |
| 11 | ¿Se distingue «desactivado» de «caído»? | **No se puede**: la API devuelve `aiAvailable: false` en ambos. Decisión escrita, no descuido |
| 12 | ¿`design.md`? | **Sí.** Ocho decisiones con alternativas defendibles y un cruce de tres zonas |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** abra migración, **no** toque `ai-service/`, **no** modifique `IAiGatewayClient` ni `/api/v1/products/search`, y **no** cambie el orden ni el contenido que decide C15.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. Con C17 cierra el hito de la Ola 2: un operador buscando en lenguaje natural desde `pv.joiabagur.com`.
- **Estimación:** **8 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C15 archivado. **No paralelizar con C36** (misma página y mismo servicio del frontend). Los `## MODIFIED` sobre specs archivadas obligan a `openspec validate --all --strict`.
- **Línea de corte** (si la sesión desborda, regla 5 del procedimiento): (1) tramo .NET de atribución + panel con búsqueda, resultados en orden, selección y arrastre — archivable; (2) los cinco estados completos y la página corta; (3) filtros de materiales y categoría; (4) bloque de embudo de administrador y consultas de ejemplo.
- **Tags:** `HU-AIENG-016`, `C16`, `EP14`, `frontend`, `react`, `dotnet`, `search`, `telemetry`, `attribution`, `ux`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-016](../../../../Documentos/Historias/AI-Eng/HU-AIENG-016.md)
- **Change OpenSpec:** `openspec/changes/add-frontend-assisted-search-panel/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C16 y §0 de 2026-08-29) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.4, §7.6, §11)
- **Apuntes del Máster (guía, no dogma):** [S4 · De interfaz conversacional a interfaz de producto](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/De%20interfaz%20conversacional%20a%20interfaz%20de%20producto.md) *(hornear el prompting en la interfaz: formulario y verbo, no caja de texto desnuda)* · [S16 · Un sistema debe saber decir «No lo sé»](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Un%20sistema%20debe%20saber%20decir%20%E2%80%9CNo%20lo%20se%E2%80%9D.md) *(la abstención es el sistema funcionando bien; hay que poder decirla en pantalla)* · [S16 · Coste, latencia y A/B testing](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Coste,%20latencia%20y%20A%20B%20Testing.md) · [S10 · Filtrado contextual y temporal](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Filtrado%20contextual%20y%20temporal.md) *(el filtro que descarta 48 y entrega 2 sin error visible)*
- **Specs vivas:** `ai-assisted-search` *(se modifica)* · `sales-management` *(se modifica)* · `ai-search-telemetry` · `frontend` · `access-control` · `point-of-sale-management` · `inventory-management`
- **Precedentes:** C04 (telemetría, `Sale.SearchEventId`, sin excepción de administrador) · C15 (endpoint, cuatro estados, límite de peticiones) · `scan.tsx` y `new-image.tsx` (entrega por estado de navegación) · `products/catalog.tsx` (patrón de listado que **no** se copia en el disparo)
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Testing:** [testing-frontend.md](../../../../Documentos/testing-frontend.md) · [testing-backend.md](../../../../Documentos/testing-backend.md) — *Estado de la suite: fallos conocidos*
- **UI:** [analisis-metronic-frontend.md](../../../../Documentos/Propuestas/analisis-metronic-frontend.md) — componentes reutilizados: `card`, `badge`, `button`, `input`, `select`, `toggle-group`, `skeleton`, `alert`, `collapsible`, `separator`
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-29 | `/enrich-us` | Creación a partir de HU-AIENG-016 y de la exploración del 2026-08-29. Recoge: el tramo .NET de atribución de venta que B5 exige y que la ficha no contemplaba, panel en ruta propia con tercera tarjeta, envío explícito con consultas de ejemplo frente a `debounce`, insignia de origen y chips de materiales en lugar de `matchReasons`, los cuatro estados sin resultados más la página corta, vocabulario de materiales replicado con test de fijación, embudo colapsado para administradores, y episodio por montaje del panel |
