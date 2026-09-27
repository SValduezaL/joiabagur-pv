# T-AIENG-015: Assisted search endpoint with authoritative hydration (C15)

> Ticket técnico del change OpenSpec `add-dotnet-ai-search-endpoint`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-015](../../../../Documentos/Historias/AI-Eng/HU-AIENG-015.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C15 y §0 de 2026-08-28), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §6.4, §7.6), sesión de exploración 2026-08-28, código real de `backend/src/` y `ai-service/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-015 / C15** — `POST /api/ai/search`: ventana máxima de candidatos en una llamada, hidratación autoritativa por punto de venta, buscador degradado propio, flag por POS, caché de candidatos y telemetría de C04

---

## Contexto y Problema

C03 dejó el cliente tipado con presupuesto de 800 ms, reintento único y circuit breaker. C04 dejó `RecordSearchAsync`, que nunca lanza. C14 dejó el retriever vectorial real. **Falta el endpoint que los une**, y sin él C16 y C17 no pueden empezar.

Tres cosas que la ficha v3 daba por hechas no se sostienen al leer el código:

1. **«Repide con `top_k` mayor si quedan pocos».** El SQL de C14 aplica el umbral 0,65 **antes** del `LIMIT`. Si `len(results) < overfetch`, ató el umbral y no el `LIMIT`: repedir devuelve las mismas filas y cobra un segundo embedding. El techo de `over_retrieval_count` es 60, alcanzado con `top_k = 20`.
2. **«Resultados léxicos» con el buscador existente.** `SearchProductsAsync` hace `Name.Contains(consulta)` sobre la cadena completa: ante una consulta en lenguaje natural devuelve **la lista vacía, siempre**. Y filtra por *todos* los puntos de venta del usuario, no por el de la búsqueda.
3. **El `pos_id` como filtro duro en Python.** §7.6 paso 1 lo sitúa ahí, pero C14 declara que *«the search SQL does not filter by `pos_id`»* y lo difiere a C22. C15 sólo puede aplicarlo al hidratar, que es el paso 6.

**Consecuencia medida de (3).** Con `n_take = round(coverage × 1200)` de C10 y `inactive_inventory_ratio_live_pos: 0.08`:

| POS | cobertura | activos ≈ | supervivientes de 30 | de 60 |
|---|---|---|---|---|
| CIU-CENTRE (`op-ciutadella`) | 0,78 | 861 | 21,5 | 43 |
| MAO-AIR (`op-aeroport`) | 0,38 | 420 | 10,5 | 21 |
| **FORNELLS (`op-fornells`)** | **0,22** | **243** | **6,1** | **12,1** |

Con 30 candidatos, FORNELLS llena una página de 10 en el **~4 %** de las búsquedas. Y `collection_weights` sesga el surtido, así que el descarte **correlaciona con la señal de ranking**: no adelgaza uniformemente, vacía las consultas alineadas con colecciones que ese punto de venta casi no tiene. Dos de los tres operadores de demo están en 0,38 o por debajo.

**Estado actual del código (verificado 2026-08-28 en repo):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-dotnet-ai-search-endpoint` | **Scaffold** (`.openspec.yaml`, schema `spec-driven`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `IAiGatewayClient.SearchAsync` | **Listo.** No trunca el overfetch; devuelve `Results`, `CandidatesReturned`, `LowConfidence`, `TraceId`, `EffectivePosId`. **Sin cambios** |
| `AiSearchRequest` | `Query`, `TopK` (default 10), `Filters`, `Mode` (default `Hybrid`). **No** envía `pos_id`: el ámbito viene del token |
| `AiCallScope` | Dos rutas de construcción. `ForPointOfSale` **rechaza** `Guid.Empty` y no admite centinelas. `ForCatalog` es rechazado por `SearchAsync` |
| `AiGatewayOptions` | `RetrievalTimeoutMs = 800`, breaker configurado, `Enabled` **global**. **No** hay flag por POS |
| `IProductSearchEventService.RecordSearchAsync` | **Listo.** Devuelve `Guid?`, no lanza. Exige `RecordSearchRequest` con `AiCallScope` de punto de venta |
| `SearchOrigin` | Enum con `Assisted = 1`, `LexicalFallback = 2`. **Falta** el tercer valor |
| `AiSearchEventsController` | `api/ai/search-events`, sin versión, `[Authorize]`. Patrón a seguir. **No se toca** |
| `AiController.cs` | **No existe.** El patrón real es un controlador por capacidad |
| `ProductService.SearchProductsAsync` | `GetAllAsync()` completo en memoria + `SKU ==` + `Name.Contains`. Ámbito: todos los POS asignados. **No se modifica** |
| `ProductService.GetInventoryQuantitiesAsync` | `foreach` con `FindByProductAsync` por producto → N+1 |
| `ProductService.MapToListDtoAsync` | `await GetUrlAsync` por foto → segundo N+1 |
| `ProductListDto.AvailableQuantity` | **Suma** todos los POS asignados. Semántica distinta de la que necesita C15 |
| `IUserPointOfSaleService.HasAccessAsync` | Va directo al repositorio: **sin excepción de administrador** |
| `ICurrentUserService` | `UserId`, `Role`, `IsAdmin`. Sin punto de venta |
| `ITraceContextAccessor.CurrentTraceId` | **Listo.** Nunca vacío |
| Rate limiter | `app.UseRateLimiter()` activo; sólo existe la política `LoginRateLimit`, particionada por IP y con límite alto en test |
| `AddMemoryCache()` | **Ya registrado** en `ServiceCollectionExtensions` (línea 62). Sin dependencia nueva |
| Npgsql EF Core | `10.0.0`. Traducción de full-text **a verificar en spike** |
| `ai.product_document.tsv` | Columna generada `to_tsvector('spanish', doc_text)` + GIN `ix_product_document_tsv`, desde **C05**. Consumidor previsto: **C21**. C15 **no la lee** |
| `api/routers/retrieval.py` | Construye `LiteLlmEmbeddingClient` **por petición** → caché RAM inútil en recuperación. **Deuda para C21/C22**; C15 no cruza a Python |
| Migraciones EF | Seis previstas (C04, C07, C08, C19, C27, C29). C15 **no abre una séptima** |
| HU-AIENG-015 | **Creada** y alineada con este ticket |

**Impacto en producto:** primer punto del sistema RAG que toca un operador, aunque la pantalla llegue en C16. Y hace que C04 deje de ser código muerto.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs` | **Nuevo.** `api/ai/search`, sin versión, `[Authorize]`, política de limitación de peticiones |
| `backend/src/JoiabagurPV.Application/Services/` | **Nuevo.** Orquestador de búsqueda, hidratador conjunto, buscador degradado, caché de candidatos |
| `backend/src/JoiabagurPV.Application/DTOs/Ai/` | **Nuevo.** Petición y respuesta del endpoint, con los contadores del embudo |
| `backend/src/JoiabagurPV.Application/Configuration/` | Opciones de búsqueda asistida: POS habilitados, ventana, TTL, límites |
| `backend/src/JoiabagurPV.Domain/Enums/SearchOrigin.cs` | `Disabled = 3` |
| `backend/src/JoiabagurPV.API/Extensions/ServiceCollectionExtensions.cs` | Política `AiSearchRateLimit` particionada por usuario |
| `backend/src/JoiabagurPV.Application/Extensions/ServiceCollectionExtensions.cs` | Registro de los servicios nuevos y validación de opciones al arranque |
| `backend/src/JoiabagurPV.Tests/` | Unitarios con gateway falso; integración con Testcontainers |
| `openspec/changes/add-dotnet-ai-search-endpoint/` | proposal, **design.md**, specs (capability nueva + `## MODIFIED` de `ai-search-telemetry`), tasks |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-015 (**en el apply**) |
| `IAiGatewayClient`, `ai-service/`, `openapi.json`, migraciones EF, `frontend/`, `/api/v1/products/search` | **Sin cambios** |

---

## Especificaciones Técnicas

### Endpoint

| Ruta | Método | Rol | Notas |
|---|---|---|---|
| `/api/ai/search` | `POST` | Autenticado (`Administrator` u `Operator`) | Sin versión, como el resto de `api/ai/*` |

**Petición.** `query` (obligatoria, tope alineado con el máximo del contrato congelado: 500), `pointOfSaleId` (**obligatorio**), `pageSize` (default 10, tope 50), `searchSessionId` (opcional), `filters` con materiales y categoría. Validación con FluentValidation, invocada explícitamente en el controlador: el proyecto registra validadores sin cablear pipeline automático, y `SuppressModelStateInvalidFilter` está activo.

**Respuesta.** `results[]` en orden recibido, con `productId`, `sku`, `name`, `price`, `quantityAtPointOfSale`, `hasStock`, `primaryPhotoUrl`, `collectionName`, `score`, `matchReasons`, `familyId`, `variantLabel`; más `searchEventId`, `aiAvailable`, `lowConfidence`, `pointOfSaleId` y los contadores del embudo.

`score`, `familyId` y `variantLabel` se exponen aunque C16 no los pinte todavía: C36 los necesitará y el DTO es más caro de cambiar después.

### Flujo

1. Resolver identidad y validar el punto de venta. Sin `pointOfSaleId` → **400**. Operador no asignado → **403**. Administrador → cualquier punto de venta **activo**.
2. Construir `AiCallScope.ForPointOfSale(userId, role, posId)`.
3. Comprobar el flag del punto de venta. Apagado → buscador clásico, `aiAvailable: false`, origen `Disabled`, **sin** llamar al gateway.
4. Consultar la caché de candidatos. Acierto → saltar al paso 6.
5. Llamar a `SearchAsync` con `TopK` = ventana configurada (**20** por defecto → 60 candidatos). Cronometrar `RetrievalMs`.
6. Hidratar y descartar. Truncar a `pageSize`.
7. Capturar `TotalMs`.
8. `RecordSearchAsync` con la lista **mostrada**. Tolerar `null`.
9. Emitir el log del embudo y responder.

### Ventana de candidatos

`over_retrieval_count(top_k) = min(top_k × 3, 60)` y `MAX_TOP_K = 50` en el contrato congelado. La ventana de 20 alcanza el tope de 60 en una llamada; pedir más no aporta nada. **No hay segunda llamada al gateway por escasez de resultados.**

### Hidratación

Una consulta conjunta, no `ProductService`:

```
Product ⋈ Inventory                      (Product.Id = ANY(@candidateIds)
        ⋈ ProductPhoto (primaria)         AND Inventory.PointOfSaleId = @posId
        ⋈ Collection                      AND Inventory.IsActive
                                          AND Product.IsActive)
```

| Regla | Efecto |
|---|---|
| Sin fila de `Inventory` en el POS | descarta |
| `Inventory.IsActive = false` | descarta |
| `Product.IsActive = false` | descarta |
| **`Quantity = 0`** | **conserva**, marca `hasStock: false` |

La cantidad devuelta es la de ese punto de venta. Precio y stock **nunca** vienen de la respuesta de la IA. Si el `sku` indexado difiere del de catálogo, manda el de catálogo y se registra la divergencia.

### Buscador degradado

`to_tsvector('spanish', Name || ' ' || coalesce(Description,''))` calculado en consulta —sin columna generada y **sin índice**—, acotado a los productos con inventario activo en el punto de venta, con **semántica OR** y orden por `ts_rank`. Con 1.200 productos el escaneo secuencial está en el orden de decenas de milisegundos.

⚠️ `plainto_tsquery` **conjunta** los términos y sobre este corpus devuelve cero: hay que usar `websearch_to_tsquery` con semántica de alternativa, o construir el `tsquery` uniendo con `|`. Filtrar por `ts_rank` sería el mismo error; `ts_rank` **ordena**.

**Spike previo (primera tarea):** verificar que Npgsql 10 traduce `EF.Functions.ToTsVector` / `WebSearchToTsQuery` / `ts_rank`. Caída controlada: OR de términos sobre SKU, nombre y descripción, ordenado por número de términos que casan.

### Feature flag y telemetría

Opciones enlazadas y validadas al arranque, con `IOptionsMonitor` para recarga en caliente: lista de puntos de venta habilitados y valor por defecto. **Sin columna, sin migración.**

`SearchOrigin.Disabled = 3` se añade con un `## MODIFIED Requirements` sobre la spec viva `ai-search-telemetry`. La columna es entera: no hay migración. Convierte el flag en el brazo de control del A/B por punto de venta de §11.2.

| Situación | `SearchOrigin` | `aiAvailable` |
|---|---|---|
| La IA respondió | `Assisted` | `true` |
| Circuito abierto, timeout, 5xx, 401 de configuración | `LexicalFallback` | `false` |
| Flag apagado para ese POS | `Disabled` | `false` |

### Caché de candidatos y coste

`IMemoryCache` (ya registrado), TTL corto configurable, tamaño acotado. Clave: `(posId, consulta normalizada, filtros, ventana)`. Guarda **sólo** identificadores y scores de la IA; **la hidratación se rehace siempre**, de modo que nunca se sirve precio ni stock rancios.

El `posId` entra en la clave desde el primer día aunque hoy la recuperación no dependa de él: cuando C22 añada el filtro duro, una clave sin punto de venta sería una fuga entre tiendas y nadie revisaría la clave de una caché.

Política `AiSearchRateLimit` particionada por **`userId`**, no por IP: detrás de nginx toda una tienda comparte dirección. Límite alto en entorno de test, como ya hace `LoginRateLimit`. Rechazo con **429**, distinguible de una caída de la IA.

### Mapeo de errores del gateway

| Excepción | Respuesta |
|---|---|
| `AiUnavailableException` | Buscador degradado, 200, `aiAvailable: false`, log de aviso |
| `AiGatewayConfigurationException` | Buscador degradado, 200, `aiAvailable: false`, **log de error** |
| `AiNotImplementedException` | Buscador degradado, 200, `aiAvailable: false`, log de error |

*«El sistema nunca se cae por culpa de la IA»* (§6.4). Un secreto mal configurado degrada; no tumba la búsqueda.

### Instrumentación del embudo

Log estructurado con `trace_id` y `posId`: `candidatesReturned → survivedHydration → displayed`. **No** hay columnas nuevas.

- Línea base para la ablation de C22: `% de búsquedas con ResultsCount < pageSize` agrupado por `PointOfSaleId`, con lo que C04 ya persiste.
- Abstención vs sin surtido: unión por `TraceId` con el log `stage=search` de C14, que ya emite `low_confidence` y `candidates`. Es el cruce previsto en la decisión 6 de HU-AIENG-014.

La consulta del operador **no** sale por encima de nivel Debug.

---

## Arquitectura

```
  SPA (C16, aún no existe)
        │ JWT usuario + pointOfSaleId
        ▼
  AiSearchController ── 400 sin POS · 403 no asignado · 429 rate limit
        │
        ▼
  AiSearchService
        ├─ flag apagado ──────────────► buscador clásico · Disabled
        │
        ├─ caché de candidatos (hit) ──┐
        │                              │
        ├─ IAiGatewayClient.SearchAsync│  top_k=20 → 60 candidatos
        │        │ 800 ms · breaker    │  UNA llamada
        │        └─ excepción ─────────┼─► buscador degradado · LexicalFallback
        │                              │   (ts_vector español · OR · ts_rank · POS)
        ▼                              ▼
  Hidratador  ── Product ⋈ Inventory@POS ⋈ Photo ⋈ Collection
        │        descarta no asignado / inactivo · conserva stock 0
        ▼
  truncar a pageSize
        │
        ▼
  RecordSearchAsync (C04) ── nunca lanza · TotalMs capturado antes
        │
        ▼
  respuesta + searchEventId + aiAvailable + lowConfidence + embudo
```

Decisiones heredadas: §6.2 (Python calcula parecidos, .NET calcula números); §6.4 (degradación y flag por POS); §7.6 (sobre-recuperación y «la disponibilidad pondera, nunca excluye»); C03 (presupuesto y breaker); C04 (telemetría en dos escrituras); C14 (umbral antes del `LIMIT`, sin filtro de POS).

**Breaking:** ninguno. Endpoint nuevo, contrato de `jbg-ai` intacto, `IAiGatewayClient` sin diff, `/api/v1/products/search` sin cambios. `SearchOrigin.Disabled` amplía un enum entero sin romper las filas existentes.

---

## Definición de Hecho (DoD)

- [ ] Código según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus; integración con Testcontainers; nomenclatura `Método_Escenario_ResultadoEsperado`; cobertura ≥ 70 %
- [ ] Baseline de la suite medido con `git stash push -u` **antes** de comparar rojos: se compara el **conjunto de nombres** que fallan, no el número
- [ ] Un test verifica que `RecordSearchAsync` **se invoca** (obligación A1: su incumplimiento no tiene síntoma)
- [ ] Un test verifica que **no** hay segunda llamada al gateway cuando la hidratación deja la página corta
- [ ] Un test verifica que la clave de caché incluye el punto de venta
- [ ] Los objetos madre de test fijan `.WithPhone("600123456")`: el generador de Bogus desborda `PointOfSale.Phone`
- [ ] Las aserciones de 401 piden un cliente nuevo a la factoría: el `HttpClient` compartido conserva las cookies del login
- [ ] **Sin migración de EF Core** y sin índice nuevo
- [ ] Specs delta en `openspec/changes/add-dotnet-ai-search-endpoint/specs/`, incluido el `## MODIFIED` de `ai-search-telemetry`
- [ ] `openspec validate --all --strict` → **0 failed** (no basta la forma de un solo change)
- [ ] Documentación: HU, este ticket, `Documentos/epicas.md` (EP14) en el apply
- [ ] Compatibilidad hacia atrás: `/api/v1/products/search` sin cambios de comportamiento; `ai-service/openapi.json` sin diff
- [ ] Sin TODO/FIXME sin tarea de seguimiento
- [ ] Verificación **posterior** (no DoD de merge): búsqueda real desde `op-ciutadella` y desde `op-fornells` con el índice local poblado, comprobando que la segunda devuelve página corta y que el embudo lo refleja

No aplica: Vitest, Playwright, cobertura de frontend, `uv run pytest`, regenerar OpenAPI, UI es-ES *(C15 no entrega pantalla; llega en C16)*.

---

## Requisitos No Funcionales

- **Seguridad:** el `pos_id` que viaja al gateway sale siempre del ámbito validado, nunca del cuerpo. `AiCallScope.ForPointOfSale` no admite centinelas. Sin excepción de administrador en `HasAccessAsync`: si C15 la concede, es explícita y limitada a puntos de venta activos. Secretos en SSM (`/jpv/prod/*`). La consulta del operador no sube de nivel Debug.
- **Rendimiento y free-tier:** **una** hidratación conjunta, nunca N+1; página máxima 50; ventana de candidatos acotada a 60; caché de candidatos con TTL corto y tamaño limitado; presupuesto de 800 ms respetado con una sola llamada; buscador degradado sin índice, aceptable con 1.200 productos y revisable si el catálogo crece un orden de magnitud.
- **Observabilidad:** Serilog estructurado; `trace_id` propagado y presente en el evento y en el log; embudo por punto de venta; `RetrievalMs` mide la obtención de candidatos sea cual sea su origen, para que los tres orígenes sigan siendo comparables.
- **Integridad de datos:** precio y stock siempre desde `public`; `Sale.Price` sigue siendo snapshot y esta historia no lo toca; un fallo de telemetría nunca propaga; `.NET` no lee el esquema `ai`.

---

## Preguntas Abiertas

Ninguna pendiente de producto. Cerradas en la exploración del 2026-08-28 y registradas en §0 del plan.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿Repedir con `top_k` mayor si falta gente? | **No.** Ventana máxima (`top_k = 20` → 60) en una sola llamada. La repetición se elimina con la prueba aritmética escrita en `design.md` |
| 2 | ¿Qué descarta la hidratación? | Sin `Inventory` activo en ese POS, o `Product.IsActive = false`. **`Quantity = 0` se conserva** y se marca |
| 3 | ¿Reutilizar el buscador léxico existente? | **No.** Buscador degradado propio, POS-scoped, full-text español en consulta, OR, `ts_rank`. `/api/v1/products/search` no se toca |
| 4 | ¿Índice GIN sobre `public."Products"`? | **No.** Con 1.200 filas compra lematización, no velocidad, y la lematización se obtiene sin él. Sería además un segundo corpus, más pobre que `ai.product_document` |
| 5 | ¿Leer `ai.product_document` desde .NET? | **No.** Compartiría cuatro eslabones con la cadena que acaba de fallar y acoplaría .NET a migraciones de Alembic sin red de seguridad |
| 6 | ¿Dónde vive el flag por POS? | **Configuración** con `IOptionsMonitor`. Una columna abriría la séptima migración de un plan que cuenta seis |
| 7 | ¿Qué se registra con el flag apagado? | **`SearchOrigin.Disabled = 3`**, vía `## MODIFIED` sobre `ai-search-telemetry`. Sin migración |
| 8 | ¿Caché de candidatos o sólo rate limit? | **Ambos.** Caché con `posId` en la clave desde el día uno; rate limit por `userId` |
| 9 | ¿Administrador sin punto de venta? | El body **exige `pointOfSaleId` siempre**; el administrador puede elegir cualquiera **activo** |
| 10 | ¿El embudo en columnas? | **No.** Log estructurado. La línea base sale de `ResultsCount` + `PointOfSaleId`; abstención vs sin surtido, uniendo por `TraceId` con los logs de C14 |
| 11 | ¿`design.md`? | **Sí.** El plan v3 no se lo asignaba; siete decisiones con alternativas defendibles lo exigen |
| 12 | ¿Arreglar el singleton de embeddings en Python? | **No aquí.** Deuda anotada para C21/C22, que ya trabajan en `retrieval/` |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** abra migración, **no** toque `ai-service/`, **no** modifique `IAiGatewayClient` y **no** cambie `/api/v1/products/search`.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. Desbloquea **C16** y **C17**, que cierran el hito de la Ola 2.
- **Estimación:** **8 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C03 y C14 archivados. **Bloquea** C16 y C17. **No paralelizar con C34** (servicio de búsqueda compartido; el conflicto ya no es el fichero del controlador). El `## MODIFIED` sobre una spec archivada obliga a `openspec validate --all --strict`.
- **Línea de corte** (si la sesión desborda, regla 5 del procedimiento): (1) endpoint + ventana máxima + hidratación + truncado + telemetría A1-A3 + degradación, archivable; (2) flag por POS con `Disabled`; (3) caché de candidatos y rate limit.
- **Tags:** `HU-AIENG-015`, `C15`, `EP14`, `backend`, `dotnet`, `ai-gateway`, `search`, `hydration`, `telemetry`, `resilience`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-015](../../../../Documentos/Historias/AI-Eng/HU-AIENG-015.md)
- **Change OpenSpec:** `openspec/changes/add-dotnet-ai-search-endpoint/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C15 y §0 de 2026-08-28) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §6.4, §7.6)
- **Apuntes del Máster (guía, no dogma):** [S10 · Filtrado contextual y temporal](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Filtrado%20contextual%20y%20temporal.md) *(el filtro duro va lo más temprano posible; verifica la cardinalidad de lo que vuelve)* · [S16 · Coste, latencia y A/B testing](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Coste,%20latencia%20y%20A%20B%20Testing.md) *(cachear resultados de búsqueda para consultas repetidas)* · [S16 · Un sistema debe saber decir «No lo sé»](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Un%20sistema%20debe%20saber%20decir%20%E2%80%9CNo%20lo%20se%E2%80%9D.md)
- **Specs vivas:** `ai-gateway-client` · `ai-search-telemetry` *(se modifica)* · `vector-retrieval` · `product-management` · `inventory-management` · `access-control` · `point-of-sale-management`
- **Precedentes:** C03 (cliente, resiliencia, `AiCallScope`) · C04 (telemetría, `SearchOrigin`, sin ruta de lectura) · C08 (`AiCatalogController`, validación explícita) · C12 (`IndexFeedService`, consultas conjuntas) · C14 (umbral antes del `LIMIT`)
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Testing:** [testing-backend.md](../../../../Documentos/testing-backend.md) — *Estado de la suite: fallos conocidos*
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-28 | `/enrich-us` | Creación a partir de HU-AIENG-015 y de la exploración del 2026-08-28. Recoge: ventana máxima en una llamada y eliminación de la repetición, hidratación por punto de venta conservando stock 0, buscador degradado propio con full-text español sin índice, flag en configuración con `SearchOrigin.Disabled`, caché de candidatos con `posId` en la clave más rate limit por usuario, punto de venta obligatorio con administrador sobre cualquier POS activo, embudo en log estructurado, y las dos deudas anotadas (singleton de embeddings en Python; índice GIN si crece el catálogo) |
