# T-AIENG-034: Sale assist and substitutes endpoints — authoritative hydration, placeholder resolution and bounded degradation (C34)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-032b](../../archive/2026-09-21-add-sales-assistant-agent-loop/ticket.md),
> [T-AIENG-015](../../archive/2026-08-28-add-dotnet-ai-search-endpoint/ticket.md) y el resto de tickets
> del Proyecto Final.
>
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-034](../../../../Documentos/Historias/AI-Eng/HU-AIENG-034.md),
> [informe de exploración](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md)
> (nueve hallazgos, catorce decisiones, cinco mediciones reproducibles), [ficha C34 y §0 del
> 2026-09-21](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md),
> [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
> (§6.2, §6.4, §7.6, §7.7, §15.10, §15.12), `ai-service/openapi.json` y el código real de `backend/src/`.

**HU origen:** [HU-AIENG-034](../../../../Documentos/Historias/AI-Eng/HU-AIENG-034.md)
**Change:** `add-dotnet-assist-and-recommendation-endpoints` (C34) · **Épica:** EP15
**Rama:** `c34-add-dotnet-assist-and-recommendation-endpoints` · **Anterior en la rama:** C26/C30a ·
**Siguiente:** C36

---

## Título

Exponer en .NET las dos rutas del card de venta —**`POST /api/ai/products/{productId}/sales-assist`**
y **`GET /api/ai/products/{productId}/substitutes`**—, con autorización por punto de venta antes de
gastar una llamada, **hidratación autoritativa** del grupo y de los sustitutos, **resolución de
`{{price}}`/`{{stock}}` contra la pieza anclada** con retirada del argumentario —no de la respuesta—
cuando algo no se resuelve, los **dos avisos de stock** y el **recálculo de `family_has_variants`**,
**cuatro resultados vacíos distinguibles** en sustitutos, un cliente **`ai-assist` a 10 s sin reintento
en timeout** y un **422 que deja de leerse como «IA no disponible»**. Como última tarea, **encender la
generación en la demo**.

---

## Contexto y Problema

`POST /v1/assist/sale` y `POST /v1/retrieval/substitutes` están servidos y medidos en Python desde
C26, C30a, C30b y C31. **No tienen ningún consumidor .NET**, así que ninguna de las dos llega a un
operario. C34 es ese consumidor y **C36 no puede empezar sin él**.

La ficha se escribió antes de que existiera nada de lo que consume. La exploración del 2026-09-21 la
contrastó con el árbol, y cuatro hallazgos gobiernan el diseño:

1. **Los marcadores no dicen de qué pieza son.** Son dos tokens sin referencia. En M2 y M3 hay una sola
   pieza y se resuelven sin ambigüedad. En M1 y en el agente, el argumentario habla de varias piezas
   con los mismos tokens ([`v4.md:104-108`](../../../../ai-service/prompts/assist/v4.md#L104-L108)). **C34 se
   queda con el card**, y la anotación del 14 de septiembre que le daba la ruta de la consulta libre se
   marca como refutada.
2. **El presupuesto de 5 s está por debajo del peor caso de Python.** En la pasada de C30b, en el ancho
   que se sirve, el **7,5 %** de las peticiones pasa de 5 s sólo en llamadas al proveedor, el **55 %**
   hace la reparación, y el peor caso por construcción es `MAX_PITCH_PROVIDER_CALLS ×
   PITCH_TIMEOUT_SECONDS = 2 × 4 s` más las búsquedas.
3. **Hidratar cambia lo que los avisos de Python afirman.** Quitar los miembros que la tienda no lleva
   deja `family_has_variants` falso en el **19,2 %** de las piezas ancladas con familia.
4. **El filtro por stock es muy selectivo, y la ventana la decide .NET.** Con `top_k = 5` (ventana de
   15), el **71,1 %** de las piezas de Fornells no llena una página de 5 sustitutos. Con `top_k = 20`
   (ventana de 60), el **7,1 %**. Y para las piezas agotadas en su tienda, que es el caso que dispara
   el bloque, el **30,6 %** frente al **3,0 %**.

### Estado actual del código, verificado en el repositorio (2026-09-21, `d42e5d6`)

| Pieza | Fichero | Estado |
|---|---|---|
| Change OpenSpec | `openspec/changes/add-dotnet-assist-and-recommendation-endpoints/` | **Scaffold** (`.openspec.yaml`, `spec-driven`); proposal, design, specs y tasks **pendientes**; este ticket y la HU |
| `IAiGatewayClient` | `Application/Interfaces/IAiGatewayClient.cs` | Cinco métodos: `SearchAsync`, `EnrichAsync`, `HealthAsync`, `SuggestFamiliesAsync`, `AuditFamiliesAsync`. **Ninguno de assist ni de sustitutos** |
| Clientes con nombre | `Application/Services/AiGatewayClient.cs` | `ai-retrieval` (L27), `ai-enrich` (L38), `ai-health` (L51). **No hay cliente generativo** |
| Hueco reservado para C34 | `Application/Extensions/AiGatewayServiceCollectionExtensions.cs:148` | Comentario: *«C34 registers its own named client here for the generative route, with a 5 s budget»* |
| `AiGatewayOptions.AssistTimeoutMs` | `Application/Configuration/AiGatewayOptions.cs:59` | `5000`, **sin usar**. `RetrievalTimeoutMs = 2500` (L53) |
| Predicado de reintento y circuito | `AiGatewayServiceCollectionExtensions.cs:167-186` | Reintenta `HttpRequestException`, **`TimeoutRejectedException`**, 408 y 5xx salvo 501. Un 4xx no se reintenta ni cuenta para el circuito |
| `TranslateStatus` | `AiGatewayClient.cs:643-663` | 401 → `AiGatewayConfigurationException`; 501 → `AiNotImplementedException`; **cualquier otro no-2xx, incluido el 422 → `AiUnavailableException`** |
| `AiCallScope.ForPointOfSale` | `Application/DTOs/Ai/AiCallScope.cs` | Rechaza `Guid.Empty`. Es lo que pone `pos_id` en el token de servicio |
| `AssistedSearchService.AuthoriseAsync` | `Application/Services/AssistedSearchService.cs:135` | Punto de venta activo → excepción de administrador → `HasAccessAsync`. **Es exactamente la comprobación que C34 necesita** |
| `IAssistedSearchRepository.HydrateAsync(ids, posId, ct)` | `Domain/Interfaces/Repositories/IAssistedSearchRepository.cs:26` | Una consulta sobre `Inventories` activos de productos activos en el POS; **conserva cantidad 0**. Devuelve `AssistedSearchRow` (`ProductId`, `Sku`, `Name`, `Price`, `Quantity`, `PrimaryPhotoFileName`, `CollectionName`) |
| `IProductFamilyRepository.GetByProductIdAsync` | `Domain/Interfaces/Repositories/IProductFamilyRepository.cs:23` | La familia con sus miembros por `SortOrder`. `ProductFamilyMember` lleva `VariantLabel` |
| `AiSearchOptions` | `Application/Configuration/AiSearchOptions.cs` | Forma a imitar: `EnabledByDefault` (`false` por defecto), `EnabledPointOfSaleIds`, ventana, página, límite de peticiones, con `IOptionsMonitor` |
| `RateLimitPolicies` | `API/Extensions/ServiceCollectionExtensions.cs:19` | `Login` y `AiSearch`, esta última particionada por usuario |
| Stock bajo | `StockValidationService.cs:18-19` · `DashboardService.cs:208` | **Dos reglas incompatibles**: `max(10 %, 5)` sobre lo que queda tras vender, y `≤ 2` en el panel. No hay configuración compartida |
| Dobles de `IAiGatewayClient` en tests | `Tests/IntegrationTests/*.cs` | **Siete escritos a mano**; se rompen al añadir un método |
| Tests de integración de C15 | `Tests/IntegrationTests/AiSearchControllerTests.cs` | **No llegan nunca al gateway**: sin sección `AiSearch`, el interruptor vale `false` y recorren el camino desactivado |
| Deriva de contrato | `Tests/UnitTests/Application/AiContractSnapshotTests.cs` | Tabla `ModelToSchema` tipo .NET ↔ esquema de `openapi.json` |
| Ruta `api/ai/products` | `API/Controllers/` | **Libre**. El patrón es un controlador por capacidad bajo `api/ai/*`, sin versión |
| Demo | `compose.demo.yaml` | `AiSearch__EnabledByDefault: "true"` y `AiGateway__RetrievalTimeoutMs: "2500"`; **sin credencial generativa** en `jbg-demo-ai`, así que sirve `pitch: ""` |

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `backend/src/JoiabagurPV.API/Controllers/AiSalesAssistController.cs` | **Nuevo.** `[Route("api/ai/products")]`, `[Authorize]`, dos acciones con su política de límite de peticiones |
| `backend/src/JoiabagurPV.Application/Services/` | **Nuevos.** Servicio de asistencia (autorizar, comprobar, llamar, hidratar, avisos, marcadores, degradar) y servicio de sustitutos (autorizar, comprobar, ventana, filtrar, paginar, `outcome`). **Modificados:** `AiGatewayClient` (dos métodos y el 422) |
| `backend/src/JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs` | `AssistSaleAsync` y `SubstitutesAsync` |
| `backend/src/JoiabagurPV.Application/DTOs/Ai/` | **Nuevos.** DTO del contrato de Python (assist y sustitutos) y DTO de las dos rutas hacia el frontend |
| `backend/src/JoiabagurPV.Application/Exceptions/` | **Nueva.** `AiRequestRejectedException : AiGatewayException` |
| `backend/src/JoiabagurPV.Application/Configuration/` | **Nueva** `AiSalesAssistOptions`. `AiGatewayOptions.AssistTimeoutMs` pasa a **10.000** |
| `backend/src/JoiabagurPV.Application/Extensions/AiGatewayServiceCollectionExtensions.cs` | Cliente `ai-assist` en el hueco de la L148, con su propio *pipeline*, predicado y circuito; validación al arranque del suelo de presupuesto |
| `backend/src/JoiabagurPV.API/Extensions/ServiceCollectionExtensions.cs` | `RateLimitPolicies.AiSalesAssist` particionada por usuario |
| `backend/src/JoiabagurPV.API/appsettings*.json` | Sección `AiSalesAssist` y `AiGateway:AssistTimeoutMs` |
| `backend/src/JoiabagurPV.Tests/` | Clase base `ThrowingAiGatewayClient` y los siete dobles heredando de ella; unitarios del cliente y de los dos servicios; integración con Testcontainers; filas nuevas en `ModelToSchema` |
| `compose.demo.yaml` · `deploy/demo/deploy.sh` · `deploy/demo/README.md` | **Última tarea**: credencial y modelo de generación en `jbg-demo-ai`; `AssistTimeoutMs` e interruptor en la API de la demo |
| `openspec/changes/add-dotnet-assist-and-recommendation-endpoints/` | proposal, **design.md**, specs (capability nueva + `## MODIFIED` de `ai-gateway-client`), tasks |
| `Documentos/` · `backend/README.md` · `openspec/DEFERRED_TASKS.md` | Ver la tarea de documentación |

**No se tocan:** `ai-service/` entero (**`openapi.json` idéntico byte a byte**), `frontend/`,
`terraform/`, `.github/workflows/`, `AssistedSearchService` y la ruta `POST /api/ai/search`. **Sin
migración de EF Core.**

---

## Especificaciones Técnicas

### Endpoints

| Ruta | Método | Rol | Respuestas |
|---|---|---|---|
| `/api/ai/products/{productId:guid}/sales-assist` | `POST` | Autenticado (`Administrator` u `Operator`) | 200 (incluido el degradado), 400, 401, 403, 404, 429 |
| `/api/ai/products/{productId:guid}/substitutes` | `GET` | Autenticado (`Administrator` u `Operator`) | 200 (incluidos los cuatro `outcome`), 400, 401, 403, 404, 429 |

**Validación explícita** con FluentValidation, invocada en el controlador: el proyecto tiene
`SuppressModelStateInvalidFilter` activo, y la regla de C15 es que *«registering a validator without
invoking it is worse than having none»*.

| Campo | Regla |
|---|---|
| `pointOfSaleId` | **Obligatorio** en las dos. Sin él → 400 |
| `question` | Opcional. Si viene: no vacía tras `Trim()` y **≤ 500** caracteres, el máximo de `AssistRequest.query` en el contrato |
| `pageSize` | Opcional; **5** por defecto; **1–20** |

**Autorización, antes de ninguna llamada a la IA** (reutiliza la lógica de `AuthoriseAsync`):

| Situación | Respuesta |
|---|---|
| Punto de venta inexistente o inactivo | 400, para cualquier rol |
| Operario sin asignación activa al punto de venta | **403** |
| Administrador | Cualquier punto de venta **activo** |
| Pieza inexistente, inactiva, o sin inventario activo en ese punto de venta | **404** |

La comprobación de la pieza es un `HydrateAsync([productId], posId)`: si viene vacío, 404. La fila que
devuelve se reutiliza como pieza anclada.

### DTO hacia el frontend (esbozo; los nombres definitivos, en el `design.md`)

```text
SalesAssistRequest      { pointOfSaleId: Guid, question?: string }

SalesAssistResponse
  aiAvailable            bool
  pointOfSaleId          Guid
  intent                 string              // pasa tal cual (product_pitch en M2)
  groups[]               { familyId?, familyLabel?, members[] }
    members[]            { productId, sku, name, variantLabel?, price, quantityAtPointOfSale,
                           hasStock, primaryPhotoUrl?, collectionName?, materials[],
                           matchReasons[], isAnchor }
  pitch                  string?             // ya resuelto; null si no se entrega
  pitchStatus            generated | not_generated | withheld_by_ai
                         | withheld_unresolved | withheld_out_of_stock | ai_unavailable
  citations[]            { citationId, documentTitle, sectionTitle, docType, claimScope, snippet }
  warnings[]             string              // los de Python filtrados + los dos de stock
  clarificationQuestion  string?
  promptVersion          string?
  traceId                string

SubstitutesResponse
  outcome                ok | none_in_stock | product_not_indexed | ai_unavailable
  results[]              { productId, sku, name, variantLabel?, price, quantityAtPointOfSale,
                           primaryPhotoUrl?, collectionName?, materials[], matchReasons[],
                           familyMatch, materialOverlap, styleSimilarity }
  candidatesReturned     int
  survivedHydration      int
  pointOfSaleId          Guid
  traceId                string
```

`pitchStatus` se serializa en *snake_case* como los enums del gateway. El castellano de los códigos es
de C36.

### DTO del contrato con `jbg-ai`

A mano y en *snake_case* por `AiGatewaySerialization.Options`, como los existentes. **Ninguno envía
`pos_id`**: el ámbito viaja en el token, y hay un test del precedente que lo comprueba.

| DTO .NET | Esquema de `openapi.json` | Campos que se usan |
|---|---|---|
| `AiAssistSaleRequest` | `AssistRequest` | `product_id` (siempre), `query` (la pregunta o `null`) |
| `AiAssistSaleResponse` | `AssistResponse` | `trace_id`, `effective_pos_id`, `intent`, `groups`, `pitch`, `citations`, `warnings`, `clarification_question`, `usage`, `abstained`, `prompt_version` |
| `AiAssistGroup` / `AiAssistGroupMember` | `AssistGroup` / `AssistGroupMember` | `family_id?`, `family_label?`, `members` / `product_id`, `sku`, `variant_label?`, `materials`, `score`, `match_reasons` |
| `AiCitation` | `Citation` | los ocho campos |
| `AiSubstitutesRequest` | `SubstitutesRequest` | `product_id`, `top_k`, `reason?` |
| `AiSubstitutesResponse` / `AiSubstituteResult` / `AiSimilaritySignals` | `SubstitutesResponse` / `SubstituteResult` / `SimilaritySignals` | todos |

Se **reutilizan** `AiUsage`, `AiSearchFilters` y `AiDebugInfo`. **Cada tipo nuevo entra como fila de
`AiContractSnapshotTests.ModelToSchema`**, que falla si una propiedad no existe en el esquema o
difiere en nulabilidad.

### Flujo de `/sales-assist`

1. Validar la petición → 400.
2. Autorizar el punto de venta → 400 o 403.
3. Comprobar la pieza anclada con `HydrateAsync([productId], posId)` → 404. Guardar su fila.
4. Si el interruptor está apagado para ese punto de venta → **camino degradado** (paso 11).
5. `AiCallScope.ForPointOfSale(userId, role, posId)` y `AssistSaleAsync(product_id, query =
   question?.Trim())`.
6. **Hidratar el grupo** con una sola `HydrateAsync(memberIds, posId)`:
   - se descartan los identificadores que no son GUID (con aviso en el log) y los miembros que la
     tienda no lleva;
   - se conserva el orden de Python;
   - si el SKU del índice difiere del de catálogo, **manda el de catálogo** y se registra la
     divergencia;
   - la pieza anclada se marca con `isAnchor`.
7. **Avisos** (ver abajo).
8. **Citas**: se mapean tal cual, incluido `claim_scope`.
9. **Argumentario**: se determina `pitchStatus` y, si procede, se resuelven los marcadores (ver abajo).
10. Log del resultado (ver «Logs») y respuesta.
11. **Camino degradado** (interruptor apagado o excepción del gateway):
    - `aiAvailable: false` y `pitchStatus: ai_unavailable`;
    - la familia se lee de .NET con `GetByProductIdAsync` y se hidrata con la misma `HydrateAsync`,
      ordenada por `SortOrder` y con `variantLabel` de `ProductFamilyMember`;
    - avisos de stock y `family_has_variants` calculados en .NET;
    - sin argumentario, sin citas y sin `size_label_missing`.

**Mapeo de excepciones del gateway**, con el precedente de C15:

| Excepción | Qué se hace | Nivel de log |
|---|---|---|
| `AiUnavailableException` (timeout, circuito, transporte, 5xx) | Degradado | Warning |
| `AiRequestRejectedException` (422: la pieza no está en el índice) | Degradado | Warning, con `reason=product_not_indexed` |
| `AiGatewayConfigurationException` (401) | Degradado | **Error** |
| `AiNotImplementedException` (501) | Degradado | Error |

### Resolución de marcadores

**`pitchStatus` se decide en este orden:**

| # | Condición | `pitchStatus` | `pitch` |
|---|---|---|---|
| 1 | Camino degradado | `ai_unavailable` | `null` |
| 2 | `prompt_version` es `null` (no corrió la generación) | `not_generated` | `null` |
| 3 | `pitch` vacío con `prompt_version` presente (lo retiró Python) | `withheld_by_ai` | `null` |
| 4 | **M2** y la pieza anclada tiene **0 unidades** | `withheld_out_of_stock` | `null` |
| 5 | Tras sustituir, queda cualquier `{{` o `}}` | `withheld_unresolved` | `null` |
| 6 | Todo lo demás | `generated` | el texto resuelto |

**La sustitución:**

| Token | Valor | Evidencia |
|---|---|---|
| `{{price}}` | `Product.Price` de la pieza anclada con `ToString("C2", es-ES)`: «39,90 €», con espacio duro antes del símbolo | 147 de 213 son «disponible(s) por {{price}}» y 52 «es de {{price}}» |
| `{{stock}}` | La cantidad en ese punto de venta, **entero** en cultura invariante: «3» | **88,3 %** de los 213 lo escriben como número |

- Sólo se sustituyen los **dos tokens exactos**. No se normaliza `{{ price }}` ni `{{precio}}`: se
  retiran por la fila 5, que es el fallo cerrado.
- **El resolvedor, invocado sin pieza anclada, retira siempre.** C34 siempre ancla, pero la regla
  protege al primer consumidor de M1 o del agente, que heredaría el problema de H1.
- El texto resuelto **no se escribe en ningún log**. Contiene el precio real.
- Cuando .NET retira el argumentario (filas 4 y 5), `citations` sigue siendo la lista que el
  argumentario usó. Es un subconjunto de la que fundamentó la respuesta, y se declara como limitación.

### Avisos

| Código | Regla | Origen |
|---|---|---|
| `family_has_variants` | Se **conserva** el de Python sólo si sobreviven a la hidratación **dos o más miembros**; si no, se quita. En el camino nominal .NET **nunca lo añade**. En el degradado lo calcula sobre la familia de .NET | Python, ajustado por .NET |
| `size_label_missing` | Pasa tal cual en el camino nominal; no existe en el degradado | Python |
| `query_out_of_domain` · `query_not_in_catalogue` · `knowledge_not_covered` | Pasan tal cual; los dos primeros no llegan en M2/M3, pero el vocabulario es cerrado y **versionado** | Python |
| **`stock_critical`** | La pieza anclada tiene entre **1 y `StockCriticalThreshold`** unidades (**2** por defecto) | **.NET** |
| **`family_members_out_of_stock`** | **Otro** miembro del grupo hidratado tiene 0 unidades | **.NET** |

Orden: los de Python filtrados y después los dos de .NET. Un código que .NET no conozca **pasa
igual**: la etiqueta neutra para lo desconocido es regla de C36.

### Flujo de `/substitutes`

1. Validar, autorizar y comprobar la pieza anclada, igual que arriba.
2. Si el interruptor está apagado → `outcome: ai_unavailable`, con el log diciendo que fue el
   interruptor.
3. `SubstitutesAsync(product_id, top_k = SubstitutesCandidateWindow)` (**20** por defecto, que da la
   ventana de 60), en **una sola llamada**. `reason` sólo se envía como dato de log para Python: `"sin_stock"`
   cuando la pieza anclada tiene 0 unidades.
4. Hidratar la ventana con una `HydrateAsync`; quedarse con **`Quantity > 0`**; conservar el orden;
   `Take(pageSize)`.
5. `outcome`:

| Situación | `outcome` |
|---|---|
| Al menos un candidato con stock | `ok` |
| La IA contestó y ninguno tiene stock en la tienda | `none_in_stock` |
| `AiRequestRejectedException` (422) | `product_not_indexed` |
| Resto de excepciones del gateway, o interruptor apagado | `ai_unavailable` |

6. Log del embudo: `candidates_returned → carried → in_stock → returned`.

### Cliente del gateway

| | `AssistSaleAsync` | `SubstitutesAsync` |
|---|---|---|
| Ruta de Python | `POST /v1/assist/sale` | `POST /v1/retrieval/substitutes` |
| Cliente con nombre | **`ai-assist`**, nuevo | `ai-retrieval`, el existente |
| Ámbito | Sólo `AiCallScope` de punto de venta; uno de catálogo → `ArgumentException`, como `SearchAsync` | Ídem |
| Presupuesto | `AssistTimeoutMs` = **10.000** | `RetrievalTimeoutMs` (2.500), sin cambios |
| Reintentos | **Ninguno en timeout.** Uno sólo si la conexión no llegó a abrirse (`HttpRequestException.HttpRequestError == ConnectionError`) | Los del cliente de recuperación, sin cambios |
| Circuito | **Estado propio**: un fallo de assist no abre el de recuperación | El de recuperación |
| Cuenta para el circuito | Timeouts, transporte, 5xx salvo 501. **No** el 422 ni un 200 | Sin cambios |

**`AiRequestRejectedException : AiGatewayException`** para el **422** en los dos métodos. No se
reintenta, no cuenta para el circuito y no es «IA no disponible». Los demás métodos del cliente **no
cambian**: un 422 en `SearchAsync` sigue siendo `AiUnavailableException`, porque la ruta de búsqueda no
lo produce por una pieza.

**Suelo validado al arranque.** `AssistTimeoutMs` **< 8.000** rechaza el arranque, con un mensaje que
cita `MAX_PITCH_PROVIDER_CALLS × PITCH_TIMEOUT_SECONDS` de Python. Es el invariante de D-F: el
presupuesto de fuera no puede ser menor que el peor caso declarado dentro, o .NET tira respuestas que
Python iba a entregar.

### Opciones y configuración

```text
AiSalesAssist (IOptionsMonitor, validadas al arranque)
  EnabledByDefault              false      // como AiSearch: la demo lo enciende
  EnabledPointOfSaleIds         []
  StockCriticalThreshold        2
  SubstitutesCandidateWindow    20         // top_k hacia Python; tope 50, el del contrato
  SubstitutesDefaultPageSize    5
  SubstitutesMaxPageSize        20
  RateLimitPermitLimit          10
  RateLimitWindowSeconds        60

AiGateway:AssistTimeoutMs       10000      // antes 5000 reservado; suelo 8000
```

### Límite de peticiones

`RateLimitPolicies.AiSalesAssist = "AiSalesAssistRateLimit"`, ventana fija **particionada por
usuario** (no por IP: detrás del proxy, toda una tienda comparte dirección), con límite alto en el
entorno de test salvo que un test lo fije, como hace `AiSearchRateLimitTests`. **Los sustitutos usan
la política `AiSearch`**: no llaman al LLM. Rechazo con **429**.

### Logs y observabilidad

| Línea | Campos | Nunca |
|---|---|---|
| `stage=sales_assist` (Information) | `trace_id`, `pos_id`, `product_id`, `mode` (M2/M3), `ai_available`, `pitch_status`, `pitch_len`, `citation_ids`, `warnings`, `members_returned`, `members_carried`, `ai_ms`, `total_ms`, `prompt_version`, `model`, `prompt_tokens`, `completion_tokens` | **El argumentario, resuelto o no** |
| `stage=substitutes` (Information) | `trace_id`, `pos_id`, `product_id`, `outcome`, `candidates_returned`, `carried`, `in_stock`, `returned`, `ai_ms` | — |
| Pregunta del operario | Sólo a nivel **`Debug`**, como la consulta de C15 | Por encima de `Debug` |

El `trace_id` viaja en el token y en `X-Trace-Id`, y se devuelve en la respuesta para correlacionar con
el log de `jbg-ai`.

### Specs de OpenSpec

| Capability | Delta | Requisitos |
|---|---|---|
| **`ai-sales-assist`** | **nueva** (`## ADDED`) | Las dos rutas; punto de venta obligatorio; autorización y comprobación de la pieza **antes** de llamar a la IA; hidratación del grupo en orden y con autoridad de catálogo; avisos de stock y recálculo de variantes; resolución de marcadores y los seis estados de `pitchStatus`; retirada del argumentario de una pieza agotada sólo sin pregunta; ventana máxima y exclusión por stock en sustitutos; los cuatro `outcome`; degradación con la familia de .NET; política de logs |
| `ai-gateway-client` | `## ADDED` + `## MODIFIED` | **ADDED** «Typed gateway client exposes sale assistance and substitutes». **MODIFIED, cinco**: «Retry policy never retries a permanent condition» (el cliente generativo no reintenta timeouts; el 422 no se reintenta), «Degradation is bounded per call and isolated per route family» (cliente `ai-assist` con circuito propio), «Contract failure modes are distinguishable by the caller» (el 422 es un rechazo, no una indisponibilidad), «Gateway configuration is validated at application start» (el **suelo de 8.000 ms** comprobado al arrancar) y «Client models cannot drift from the committed contract» (las nueve filas nuevas de `ModelToSchema`) |

> **Aviso de `CLAUDE.md`, que cuesta una sesión la primera vez:** el validador lee **sólo la primera
> línea física** de la descripción de un requisito. El `SHALL`/`MUST` tiene que estar en esa línea, sin
> partirla a 90 columnas. Y un `## MODIFIED` copia el requisito **entero**, escenarios incluidos.

### Demo — última tarea

Los cuatro pasos de *«C30b — la demo no genera argumentario»* de
[`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md), más lo que C34 añade:

| Fichero | Cambio |
|---|---|
| Parámetro `/jbg-demo/ASSIST_LLM_API_KEY` | `SecureString`, **creado a mano por el desarrollador**, como los otros seis secretos. **Terraform no se toca** |
| `deploy/demo/deploy.sh` | `export ASSIST_LLM_API_KEY="$(read_parameter ASSIST_LLM_API_KEY \|\| true)"`, **sin** `:?`: su ausencia es un estado válido |
| `compose.demo.yaml` · `jbg-demo-ai` | `JPV_ASSIST_LLM_MODEL: openai/gpt-4o-mini` y `JPV_ASSIST_LLM_API_KEY: ${ASSIST_LLM_API_KEY}` |
| `compose.demo.yaml` · API | **`AiGateway__AssistTimeoutMs: "10000"`** y **`AiSalesAssist__EnabledByDefault: "true"`**. Sin ellas, el card no se vería en la demo |
| `deploy/demo/README.md` | El parámetro en la lista de secretos manuales, marcado como **el único opcional** |

**Verificación, sin abrir la consola de AWS ni leer ninguna clave:**

1. El log del contenedor dice `stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist`.
2. Una asistencia real devuelve `pitchStatus: generated` con precio y stock resueltos.
3. `docker stats` de `jbg-demo-ai` frente a su tope de 512 MiB: estaba en **232,5 MiB (45 %)** sin
   generación, y `DEFERRED_TASKS.md` pide volver a medir *«if a generative route lands»*.
4. La cuota de tokens por minuto de la organización se comprueba y se declara.

El enrutador de C31 **no** hace falta en la demo para C34: M2 y M3 no lo invocan.

---

## Arquitectura

```text
  SPA (card de C36, aún no existe)
        │ JWT usuario · pointOfSaleId · question en el cuerpo
        ▼
  AiSalesAssistController ── 400 validación · 403 POS · 404 pieza · 429 límite
        │
        ├── /sales-assist ─────────────────────────────────────────────────────────────
        │     autorizar → HydrateAsync([anclada]) ── vacío → 404, sin llamar a la IA
        │     interruptor apagado ────────────────────────────┐
        │     IAiGatewayClient.AssistSaleAsync                │
        │       ai-assist · 10 s · sin reintento en timeout   │
        │       excepción (incl. 422) ────────────────────────┼─► DEGRADADO
        │     HydrateAsync(miembros) → orden de Python        │   familia de .NET
        │     avisos: stock_critical · members_out_of_stock   │   + avisos de stock
        │             family_has_variants recalculado         │   sin argumentario
        │     pitchStatus → {{price}} {{stock}} ← ANCLADA     │
        │       ¿queda {{…}}? → se retira el argumentario     │
        │                                                     ▼
        │                                           200 · aiAvailable false
        │
        └── /substitutes ──────────────────────────────────────────────────────────────
              autorizar → comprobar la pieza → SubstitutesAsync(top_k=20 → ventana 60)
              ai-retrieval · 2,5 s · UNA llamada
              HydrateAsync(ventana) → Quantity > 0 → orden de Python → Take(pageSize)
              outcome: ok · none_in_stock · product_not_indexed · ai_unavailable
```

**Decisiones heredadas:**

- **§6.2** —*«Python calcula parecidos y redacta; .NET calcula números y decide»*.
- **§6.4** —*«el sistema nunca se cae por culpa de la IA»*, circuito por familia de rutas e
  interruptor por punto de venta.
- **§7.6** —sobre-recuperación en Python y descarte en .NET.
- **§7.7** —marcadores que .NET resuelve.
- **§15.10** —la proyección degrada y nunca excluye; la exclusión por stock es de aquí.
- **C15** —patrón de hidratación, ventana máxima en una llamada y vacíos distinguibles.
- **C26** —sustitutos que no se abstienen y que sobre-recuperan a propósito.
- **C30a** —forma de la respuesta y códigos de aviso.
- **C30b** —la codificación del estado del argumentario y la política de degradar la parte.
- **C31** —vocabulario del enrutador.
- **D-I de C30** —el argumentario no se loguea.

**Breaking:** ninguno.

- Rutas nuevas; `POST /api/ai/search` sin cambios.
- `IAiGatewayClient` **crece** con dos métodos. Sus consumidores de producción no se ven afectados; los
  siete dobles de test sí, y se resuelven con la clase base.
- `AiUnavailableException` sigue significando lo mismo para los métodos existentes.
- `ai-service/openapi.json` **no se mueve**.
- `AssistTimeoutMs` cambia de valor, pero hasta hoy **no lo leía nadie**.

---

## Definición de Hecho (DoD)

- [x] Código según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [x] Backend: xUnit + Moq + FluentAssertions + Bogus; integración con Testcontainers; nomenclatura `Método_Escenario_ResultadoEsperado`; cobertura ≥ 70 % en el código nuevo
- [x] **Línea base de la suite medida antes de tocar nada** (`git stash push -u`, correr, `git stash pop`): se compara el **conjunto de nombres** que fallan, nunca el número
- [x] Los tests de integración **invocan el doble del gateway** y lo comprueban. Un test en verde que no llega al gateway es el defecto de C15 (H8)
- [x] Un test comprueba que **no** se llama a la IA con 403, 404 ni 400
- [x] Un test comprueba que el argumentario **resuelto no aparece en ningún log** (proveedor de log de grabación, como en `AssistedSearchServiceTests`)
- [x] Un test comprueba que la **pregunta viaja en el cuerpo** y que el DTO hacia Python **no lleva `pos_id`**
- [x] Un test comprueba que el circuito de `ai-assist` **no abre** el de recuperación (patrón de `EnrichAsync_WhenItsCircuitOpens_RetrievalKeepsWorking`)
- [x] Un test comprueba el **suelo de 8.000 ms** al arranque
- [x] Los DTO nuevos están en `AiContractSnapshotTests.ModelToSchema`
- [x] Los objetos madre fijan `.WithPhone("600123456")`; las familias se crean por `POST /api/product-families` como administrador, porque **no hay madre de familias a propósito**
- [x] Las aserciones de 401 piden un **cliente nuevo** a la factoría: el compartido conserva las cookies
- [x] **Sin migración de EF Core**
- [x] `sha256` de `ai-service/openapi.json` **igual** al del inicio del change
- [x] Specs delta en `openspec/changes/add-dotnet-assist-and-recommendation-endpoints/specs/`, con la **primera línea física** de cada requisito llevando su `SHALL`/`MUST`
- [x] `openspec validate --all --strict` → **0 failed** (el de un solo change no basta)
- [x] Latencia de extremo a extremo de M2 y M3 medida en Docker Compose y escrita con su procedencia
- [x] Demo: los cuatro pasos hechos, la línea `credential=assist` vista en el log, una asistencia real con `pitchStatus: generated` y la memoria de `jbg-demo-ai` medida — **marcada con una salvedad**: el `generated` se obtuvo tras **dos arreglos manuales del entorno** (`sync-pos --full` y el corpus copiado dentro del contenedor), ninguno de C34 y los dos en `DEFERRED_TASKS.md`; un redespliegue con imagen nueva vuelve a necesitar el segundo. El runbook los recoge en su §5.5c
- [x] Documentación: `Documentos/epicas.md`, plan de changes, `backend/README.md` (endpoints, matriz de autorización y variables), `Documentos/arquitectura.md` y `Documentos/modelo-c4.md` si procede, `deploy/demo/README.md`, `openspec/DEFERRED_TASKS.md` (se cierra la entrada de C30b) y `openspec/config.yaml` si cambia algún hecho que resume
- [x] Sin TODO/FIXME sin tarea de seguimiento

**No aplica:** Vitest, Playwright, cobertura de frontend y UI es-ES (la pantalla es de C36);
`uv run pytest` y regenerar `openapi.json` (C34 no toca `ai-service/`).

---

## Requisitos No Funcionales

- **Seguridad:**
  - El `pos_id` hacia la IA sale del ámbito validado, nunca del cuerpo.
  - Un operario sólo alcanza piezas de sus puntos de venta; la excepción de administrador es explícita
    y sólo para puntos de venta activos.
  - La pregunta del cliente no viaja en la URL ni sube de `Debug` en los logs.
  - El argumentario resuelto no se escribe en ningún log.
  - Secretos en el almacén de parámetros, nunca en el repositorio ni en el estado de Terraform.
- **Rendimiento y free-tier:**
  - Una hidratación conjunta por respuesta (dos en `/sales-assist`, contando la comprobación de la
    pieza), nunca N+1.
  - Ventana máxima de sustitutos en una sola llamada; página máxima de 20.
  - Presupuesto de 10 s en la ruta generativa, con suelo validado al arranque.
  - Límite de 10 peticiones por minuto y usuario en la ruta que llama al LLM.
- **Observabilidad:**
  - Serilog estructurado con `trace_id` propagado.
  - Embudo de sustitutos en el log.
  - Estado del argumentario y tokens por petición, para el coste.
  - Los cuatro `outcome` y los seis `pitchStatus` se pueden contar desde el log.
- **Integridad de datos:**
  - Precio y stock siempre desde `public`; ninguna cifra de la IA llega a la respuesta.
  - `Sale.Price` sigue siendo *snapshot* y este change no lo toca.
  - .NET no lee el esquema `ai`.

---

## Preguntas Abiertas

Las cuatro decisiones de producto se cerraron con el desarrollador en la exploración (D-A, D-B, D-E y
D-N). Quedan éstas, todas con opción por defecto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| 1 | ¿Una capability para las dos rutas, o dos? | **Una**, `ai-sales-assist` |
| 2 | ¿El interruptor apaga las dos rutas? | **Sí**; el log distingue interruptor de caída |
| 3 | ¿Sustitutos con la política de límite de la búsqueda? | **Sí**; el argumentario tiene la suya |
| 4 | ¿Suelo exacto de `AssistTimeoutMs`? | **8.000 ms**, con los valores por defecto de Python citados en el mensaje |
| 5 | ¿Qué fallo de transporte se reintenta en `ai-assist`? | Sólo `HttpRequestError.ConnectionError`: la petición no llegó a salir |
| 6 | ¿La respuesta degradada de `/sales-assist` distingue el 422 de la caída? | **No en el cuerpo**: `aiAvailable: false` y `pitchStatus: ai_unavailable` en los dos casos, y el log lo distingue. Si C36 necesita decir «esta pieza aún no está preparada», se añade un campo sin romper nada |
| 7 | ¿Se reordena el grupo para poner la pieza anclada primero? | **No**: orden de Python y marca `isAnchor` |
| 8 | ¿Se expone `usage` al frontend? | **No**; se loguea con el modelo |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
abra migración, **no** toque `ai-service/`, **no** cambie `POST /api/ai/search` y **no** afloje ninguna
de las reglas de logs.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). *Nunca se recorta* según el §6 del plan. **Bloquea a C36** y aparece en
  los prerrequisitos de **C38**.
- **Estimación:** _Pendiente de refinamiento_. Orientativamente por encima de C15, al que se parece: dos
  rutas, un cliente nuevo con su política y una tarea de despliegue, pero sin migración ni cambio del
  contrato de Python.
- **Dependencias:** C15, C26 y C30a archivados; consume lo que dejaron C30b y C31. **No se abre a la
  vez que C15** (servicio de búsqueda compartido).
- **Línea de corte** (regla 5 del §1, si la sesión desborda):
  1. `/sales-assist` con hidratación, marcadores, avisos, autorización y degradación, que es archivable
     y desbloquea el card;
  2. `/substitutes` con sus cuatro `outcome`;
  3. la demo.

  El tercer tramo es decisión cerrada: si no cabe, **se declara aplazado con motivo**, no se calla.
- **Tags:** `HU-AIENG-034`, `C34`, `EP15`, `backend`, `dotnet`, `ai-gateway`, `sales-assist`,
  `substitutes`, `hydration`, `placeholders`, `resilience`, `demo`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-034](../../../../Documentos/Historias/AI-Eng/HU-AIENG-034.md)
- **Informe de exploración:** [c34-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md)
- **Plan y diseño:**
  - [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), ficha C34 y §0 del 2026-09-21;
  - [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md), §6.2, §6.4, §7.6, §7.7, §15.10 y §15.12.
- **Specs vivas:**
  - [`ai-gateway-client`](../../../specs/ai-gateway-client/spec.md) *(se modifica)*
  - [`ai-assisted-search`](../../../specs/ai-assisted-search/spec.md) *(patrón)*
  - [`assist-generation`](../../../specs/assist-generation/spec.md)
  - [`substitutes-retrieval`](../../../specs/substitutes-retrieval/spec.md)
  - [`access-control`](../../../specs/access-control/spec.md)
  - [`product-family`](../../../specs/product-family/spec.md)
- **Precedentes:**
  - [T-AIENG-015](../../archive/2026-08-28-add-dotnet-ai-search-endpoint/ticket.md): hidratación, ventana y degradación.
  - [T-AIENG-030a](../../archive/2026-09-13-add-assist-structure-and-rule-warnings/ticket.md): la forma.
  - [T-AIENG-030b](../../archive/2026-09-14-add-assist-pitch-generation/ticket.md): los estados del argumentario.
  - [T-AIENG-026](../../archive/2026-09-12-add-substitutes-retrieval/ticket.md): sustitutos.
- **Apuntes del Máster (guía, no dogma):**
  - [S4 · Guardrails y validación de outputs](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/Guardrails%20y%20validacion%20de%20outputs.md): las tres políticas de fallo.
  - [S9 · Retrieval que no es solo cosine](../../../../Documentos/Sesiones%20Master%20AIEng/S9_Fundamentos_RAG/Retrieval%20que%20no%20es%20solo%20cosine%20-%20top-K%2C%20threshold%20y%20filtros%20sobre%20pgvector.md): el post-filtrado instrumentado.
  - [S15 · Partir en servicios](../../../../Documentos/Sesiones%20Master%20AIEng/S15_Produccion_I/Partir%20en%20servicios.md): síncrono hasta que duela, errores como contrato.
- **Tareas diferidas:** [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md). Se cierra *«C30b — la demo no genera argumentario»*; siguen abiertas *«C32b — política de timeout y circuito de `/v1/assist/agent`»* y *«C32a — consulta puntual de disponibilidad»*.
- **Testing:** [testing-backend.md](../../../../Documentos/testing-backend.md), sección *Estado de la suite: fallos conocidos*.
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-21 | `/enrich-us` | Creación a partir de HU-AIENG-034 y del informe de exploración del mismo día. Recoge: sólo las dos rutas del card; `POST` con `question` en el cuerpo; marcadores resueltos contra la pieza anclada, con `{{stock}}` como entero; retirada del argumentario, no de la respuesta, con seis estados de `pitchStatus`; pieza agotada sin argumentario sólo sin pregunta; cliente `ai-assist` a 10 s sin reintento en timeout y con suelo de 8 s al arranque; 422 como rechazo y no como caída; `family_has_variants` recalculado y los dos avisos de stock con umbral 2; ventana máxima de sustitutos con cuatro `outcome`; degradación con la familia de .NET; y la generación encendida en la demo como última tarea |
