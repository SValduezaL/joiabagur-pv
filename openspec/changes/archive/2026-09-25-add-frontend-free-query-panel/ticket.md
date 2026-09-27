# T-AIENG-040: Free-query panel — M1 on the assisted search screen, filters on every path, an availability badge before the search, and sixteen states told apart (C40)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya siguen
> [T-AIENG-036](../../archive/2026-09-24-add-frontend-assist-card-and-family-disambiguation/ticket.md),
> [T-AIENG-034](../../archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/ticket.md) y el
> resto de tickets del Proyecto Final.
>
> **Fuentes de verdad:** `openspec/project.md`,
> [HU-AIENG-040](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040.md),
> [informe de exploración](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md)
> (once hallazgos, diecisiete decisiones, una regla transversal de completitud, cuatro preguntas
> cerradas), [tabla de estados](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md),
> [ficha C40](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md),
> [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
> (§4, §6.4, §7.3, §7.7, §11.2, §15.11-§15.14), las specs vivas
> [`assisted-search-panel`](../../../specs/assisted-search-panel/spec.md),
> [`ai-assisted-search`](../../../specs/ai-assisted-search/spec.md),
> [`assist-generation`](../../../specs/assist-generation/spec.md) y
> [`retrieval-abstention`](../../../specs/retrieval-abstention/spec.md), y el código real de las tres capas.

**HU origen:** [HU-AIENG-040](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040.md)
**Change:** `add-frontend-free-query-panel` (C40) · **Épica:** EP15, que **se reabre**
**Rama:** `c40-add-frontend-free-query-panel` · **Anterior:** C36 · **Siguiente:** C38
**Orden obligado:** C40 **antes** de C38 — sube el prompt a `assist/v5` y mueve la fase de la
abstención, así que unas cifras de C38 tomadas antes describirían un prompt sustituido.

---

## Título

Convertir el **panel de búsqueda asistida en M1** —la consulta libre sin pieza— con **enrutador, corpus
y prosa**, un **toggle** entre la ruta semántica y la asistida sobre la misma consulta, **filtros que se
aplican también en la ruta degradada**, un **badge de disponibilidad con cuatro estados visible antes de
buscar**, `degradedReason` y un **cuarto `SearchOrigin`** que convierten la ablación en una consulta SQL,
la **abstención leyendo una sonda sin filtro**, el **ámbito «todos los puntos de venta»** como tercera
clase de ámbito explícita, la **fila que enseña su grupo**, y **`assist/v5` más una causa dura de puerta
sin las cuales el argumentario de M1 no llega al operario**.

---

## Contexto y Problema

C40 **no estaba en el plan**. Nace el 2026-09-24 durante la tarea 8.5 de C36 —la comprobación en demo de
la ficha de venta— y lo primero que apareció no fue un defecto de C36:

| Interruptor | Estado | Síntoma en pantalla |
|---|---|---|
| `AiSalesAssist:EnabledByDefault` | `false`, **ausente de todo `appsettings`** | «El asistente no está disponible» |
| `AiSearch:EnabledByDefault` | `false`, **ausente de todo `appsettings`** | «Búsqueda asistida no disponible» |
| Filtros en la ruta degradada | **se descartan en silencio** | *ninguno* — los chips siguen pulsados |

Los dos primeros son configuración. **El tercero es un defecto**, y los tres son el mismo problema: una
capacidad apagada que la interfaz presenta como encendida. **Todo lo que sigue se ordena por cuánto
engaña hoy la pantalla, no por cuánto cuesta.**

Y hay un hallazgo que **gobierna la línea de corte** y que sólo aparece leyendo el código:

```csharp
// AiGatewayClient.cs:668-677
// The contract also serves a free query with no product. This client refuses it: the
// placeholders of the generated argument name no product, so with several pieces on the
// table there is nothing to resolve them against.
if (string.IsNullOrWhiteSpace(request.ProductId))
    throw new ArgumentException(
        "Sale assistance requires an anchored product. Without one the price and stock "
        + "placeholders of the argument cannot be resolved.", nameof(request));
```

La cadena completa: `assist/v3` ordena escribir `{{price}}` y `{{stock}}` **también en las tres tareas de
consulta libre** → `PitchPlaceholderResolver.Resolve(text, null)` devuelve `Withheld` **siempre**, por
diseño y con test → medido en C30b sobre los modos anclados, `{{price}}` en **147 de 213 · 69 %** y
`{{stock}}` en **188 de 213 · 88,3 %**. **Las 42 consultas del informe se midieron con `curl` contra
Python**, saltándose esa etapa, así que su «37 respuestas con argumentario» no dice nada de lo que .NET
entregaría. **Sin el tramo 2 completo, C40 entrega un panel asistido sin prosa** — la avería que vino a
corregir, hecha por él mismo.

> **MEDIDO EN EL GRUPO 4.7, Y CORRIGE ESTE PÁRRAFO.** El tercer eslabón —el guardia de la pasarela—
> es real y **total**: rechazaba M1 al 100 %, y es lo que de verdad impedía la prosa. El primero
> **no se traslada**: extrapolar el 69 % / 88,3 % de los modos anclados al modo libre predecía que
> «la mayoría de los argumentarios de M1 se retirarían», y sobre 90 consultas contra el proveedor
> real `v3` escribió `{{price}}` **2 veces** y `{{stock}}` **1**, en 2 de 90 generaciones. Anclado
> hay una pieza y se la vende; en libre hay hasta quince y lo que se pide es comparar. La regla lo
> permitía, la tarea no lo pedía. `v5` y la causa dura siguen valiendo —la tasa de rechazo del modo
> libre cae de **8,9 % a 0 %**— pero por esa magnitud, no por la predicha. Las dos cifras y sus
> artefactos, en [c40-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md).

### Estado actual del código, verificado en el repositorio (2026-09-24, `810dd70`)

| Pieza | Fichero | Estado |
|---|---|---|
| Change OpenSpec | `openspec/changes/add-frontend-free-query-panel/` | **Scaffold** (`.openspec.yaml`, `spec-driven`); proposal, design, specs y tasks **pendientes**; este ticket y la HU |
| Panel de C16 | `frontend/src/pages/sales/assisted.tsx` | 521 líneas: selector de POS por rol, episodio por visita (`sessionRef`), guarda de orden (`requestSeq`), **cinco ramas de vacío**, 429 distinguible, embudo de administrador plegado |
| Fila de resultados | `frontend/src/components/sales/assisted-search-result-row.tsx` | `ORIGIN_LABELS`/`searchOrigin` exportados y testeados; lista **plana**, sin noción de grupo |
| Servicio y tipos del panel | `frontend/src/services/ai-search.service.ts` · `types/ai-search.types.ts` | Desenlaces tipados que **nunca lanzan**, con `rate-limited` propio. **Es el patrón** |
| Tabla de copy | `frontend/src/lib/assist-copy.ts` | Cinco códigos con fila, etiqueta neutra, cinco mensajes de estado. `knowledge_not_covered` **ya traducido**; los dos rechazos **sin fila, a propósito** |
| Endpoint de búsqueda | `API/Controllers/AiSearchController.cs` · `Application/Services/AssistedSearchService.cs` | `POST /api/ai/search` con `materials[]` y `category`. `BuildFilters()` **sólo alimenta la ruta asistida** |
| Searcher degradado | `Domain/.../IAssistedSearchRepository.cs` · `Infrastructure/.../AssistedSearchRepository.cs` | `SearchLexicalAsync(terms, pointOfSaleId, take, ct)` — **sin parámetro de filtros** |
| Cobertura de los campos que el filtro degradado necesita | `Domain/Entities/ProductAiProfile.cs` | `PieceType` **1.172/1.200 · 97,7 %** (276 `pendientes`), `MaterialsJson` 1.098/1.200 · 91,5 % |
| Dos interruptores independientes | `Application/Configuration/AiSearchOptions.cs` · `AiSalesAssistOptions.cs` | **30/min** contra **10/min**; secciones separadas a propósito |
| Presupuestos y circuitos | `Application/Configuration/AiGatewayOptions.cs` | `RetrievalTimeoutMs = 2500` · `AssistTimeoutMs = 10_000` con **suelo validado de 8.000**; clientes `ai-retrieval` y `ai-assist` con **circuitos separados** |
| Cliente generativo | `Application/Services/AiGatewayClient.cs:650-677` | `AssistSaleAsync` existe y **rechaza la consulta libre** con `ArgumentException` |
| Ámbito de llamada | `Application/DTOs/Ai/AiCallScope.cs` · `Tests/.../AiCallScopeTests.cs` | *«exactly two construction paths and no third»*, `ForCatalog` **refusado por toda operación de POS**, y un test que **fija que no hay constructor público** |
| Claims exigidas por ruta | `ai-service/src/jbg_ai/api/auth.py:21` | `REQUIRED_CLAIMS = (user_id, role, trace_id, pos_id)`; *«which claims are required is a property of the route, not of the token»* |
| `degradedReason` | `Application/Services/SalesAssistService.cs:104` | **Seis valores** —`switched_off`, `credential_rejected`, `not_implemented`, `product_not_indexed`, `ai_unavailable`, `unclassified`— que se escriben en `stage=sales_assist` y **se descartan al construir la respuesta** |
| Telemetría de búsqueda | `Domain/Enums/SearchOrigin.cs` · `Infrastructure/.../ProductSearchEventConfiguration.cs:57` | Tres valores, `HasConversion<int>()`: **un cuarto no abre migración**. `ProductSearchEvent` ya lleva `FiltersJson`, `RetrievalMs`, `TotalMs`, `SelectedFromRank` |
| Ruta de lectura de los interruptores por POS | — | **No existe.** `aiAvailable` llega *dentro* de la respuesta. `AiHealthResponse` es de administrador y describe infraestructura |
| `AssistRequest` | `ai-service/.../api/schemas/assist.py:43` | `product_id`, `query`, `top_k`, `context`, `locale`, `pos_id`. **Sin `filters`** |
| `RetrievalFilters` | `ai-service/.../api/schemas/retrieval.py:24` | `materials`, `category`, `family_id`, `exclude_product_ids`. **Existe y M1 no lo rellena** |
| Filtros en SQL | `ai-service/.../retrieval/search.py:172-182` | `AND d.materials && CAST(:materials AS text[])` y `AND d.piece_type = :category` — **prefiltro, antes de puntuar** |
| Abstención | `ai-service/.../retrieval/abstention.py` · `orchestrator.py:449` | Regla relativa `candidatos_en_banda ≥ 15`, `alpha = 0,03`, calibrada **sin filtros**; recibe las distancias **ya filtradas** |
| Máquina del enrutador | `ai-service/.../assist/routing.py` · `schema.py:54,74` | `is_sufficient` **es** `missing_axis is None`; **`index` es nullable** en una decisión servida y suficiente; `refusal_codes` devuelve `()` con `decision is None` |
| Tareas de prompt | `ai-service/prompts/assist/v3.md` · `assist/prompt.py:139` | Seis secciones. `FREE_QUERY_TASKS` tiene **tres entradas y ninguna variante «sin cobertura»** |
| `uncovered` | `ai-service/.../assist/orchestrator.py:311-318` | Se calcula **sólo en la rama anclada** |
| Vocabulario de la puerta | `ai-service/.../assist/constants.py:283-306` | Siete causas, seis duras. **Ninguna relativa a marcadores** |
| Artefacto de la pasada de 42 | `ai-service/evals/results/` | **No existe ningún `c40-*.json`**: las cifras del informe son reproducibles pero **no re-puntuables** |
| Suites | `frontend/` · `backend/` | **Las dos rojas de fábrica**: frontend **113 de 729** en 14 de 54 ficheros y backend **50 de 1.241** en 17 clases, los dos **medidos en el grupo 1 sobre `93115cf`**. La cifra de frontend que este ticket traía —113 o 114 de 597 en 14 o 15 de 48— era la línea base *de apertura* de C36, y el árbol está en su *cierre*. `vitest` sale con código 0 al pipearlo |

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/prompts/assist/v5.md` | **Nuevo.** Las tres tareas de consulta libre **sin precio ni disponibilidad**, más una **cuarta**: consulta libre sin cobertura |
| `ai-service/src/jbg_ai/api/schemas/assist.py` | **Modificado.** `AssistRequest` gana `filters: RetrievalFilters` — **adición pura** |
| `ai-service/src/jbg_ai/assist/prompt.py` · `modes.py` | **Modificados.** Cuarta entrada de `FREE_QUERY_TASKS`; `resolve_task` admite `uncovered` en el modo libre |
| `ai-service/src/jbg_ai/assist/orchestrator.py` | **Modificado.** `filters` viajan a `retrieve_products`; `uncovered` se calcula en M1; la contradicción del enrutador se registra |
| `ai-service/src/jbg_ai/assist/routing.py` | **Modificado.** Coerción a `both` con veredicto servido, `missing_axis` nulo e `index` nulo, con causa `router_index_absent` en el registro |
| `ai-service/src/jbg_ai/assist/constants.py` · `verification.py` | **Modificados.** Causa dura `placeholder_in_free_query`, activa sólo con `product_id is None`; `filters_too_narrow` en `ASSIST_WARNING_CODES` |
| `ai-service/src/jbg_ai/retrieval/orchestrator.py` | **Modificado.** Sonda vectorial **sin filtros**, ejecutada sólo cuando hay filtros, reutilizando el embedding; la abstención lee su perfil |
| `ai-service/src/jbg_ai/api/auth.py` · `deps.py` | **Modificados.** Tercer perfil de claims para la recuperación y el assist sin ámbito de punto de venta |
| `ai-service/src/jbg_ai/stubs/responses.py` | **Modificado.** El doble del modo libre deja de emitir marcadores, o mentiría en los tests |
| `ai-service/openapi.json` | **Regenerado.** Movimiento de **adición pura**, verificado hoja a hoja |
| `backend/.../Domain/Interfaces/Repositories/IAssistedSearchRepository.cs` | **Modificado.** `SearchLexicalAsync` gana filtros |
| `backend/.../Infrastructure/Data/Repositories/AssistedSearchRepository.cs` | **Modificado.** `JOIN` a `ProductAiProfiles` y dos `AND` |
| `backend/.../Domain/Enums/SearchOrigin.cs` | **Modificado.** Cuarto valor, **sin migración** |
| `backend/.../Application/DTOs/Ai/AiCallScope.cs` | **Modificado.** Tercera clase de ámbito, explícita, **no una relajación** |
| `backend/.../Application/DTOs/Ai/AiAssistSaleRequest` · `SalesAssistDtos.cs` | **Modificados.** `Filters` en la petición; `DegradedReason` en `SalesAssistResponse` |
| `backend/.../Application/Services/AiGatewayClient.cs` | **Modificado.** Se retira el guardia de la consulta libre; el ámbito nuevo se acepta sólo en las rutas que lo admiten |
| `backend/.../Application/Services/FreeQuerySearchService.cs` | **Nuevo.** Orquestación de M1: enrutado del ámbito, llamada al assist, hidratación reutilizada, telemetría con el origen nuevo |
| `backend/.../Application/Configuration/AiFreeQuerySearchOptions.cs` | **Nuevo.** Interruptor por POS, límite de peticiones y tamaños de página propios |
| `backend/.../API/Controllers/AiSearchController.cs` | **Modificado.** `POST /api/ai/search/assisted` con su política de límite, y `GET /api/ai/search/availability` sin IA |
| `backend/.../Application/Services/AssistedSearchService.cs` · `SalesAssistService.cs` | **Modificados.** Filtros a la ruta degradada; `degradedReason` reenviado |
| `frontend/src/pages/sales/assisted.tsx` | **Modificado, en profundidad.** Toggle, badge, ámbito «todos», los dieciséis estados |
| `frontend/src/components/sales/assisted-search-result-row.tsx` | **Modificado.** La fila enseña su grupo y la etiqueta de existencias nombra la tienda |
| `frontend/src/components/sales/free-query/` | **Nuevos.** Bloque de argumentario con citas, bloque de estados, badge, toggle, embudo ampliado |
| `frontend/src/services/ai-search.service.ts` · `types/ai-search.types.ts` | **Modificados.** La llamada asistida y la de disponibilidad, con desenlaces tipados que nunca lanzan |
| `frontend/src/lib/assist-copy.ts` | **Modificado.** Los dos rechazos ganan fila; `filters_too_narrow` también; los dos estados de `route=none`; «sin fuente verificable» |
| `openspec/changes/add-frontend-free-query-panel/` | proposal, **design.md**, specs (una `## ADDED` y nueve `## MODIFIED`), tasks |
| `Documentos/` · los tres README · `openspec/DEFERRED_TASKS.md` | Ver la tarea de documentación |

**No se tocan:** `terraform/`, `.github/workflows/`, el carrito y la confirmación de venta de `new.tsx`,
el escaneo, el reconocimiento de imágenes, y la lógica de la ficha de C36 más allá de pintar
`degradedReason`. **Sin migración de EF Core y sin tabla nueva.**

---

## Especificaciones Técnicas

### ai-service · `assist/v5` y la puerta

Las tres tareas de consulta libre añaden la prohibición, y nace una cuarta:

```text
## Tarea · consulta libre · catálogo | conocimiento | catálogo y conocimiento
+ En esta tarea NO hables de precio ni de disponibilidad: no escribas {{price}} ni {{stock}}.
+ El operario tiene la lista con precios y existencias delante. El lenguaje comparativo sí
+ cabe —«el más asequible de los tres»— porque no lleva ninguna cifra.

## Tarea · consulta libre · conocimiento sin cobertura            ← NUEVA
  Los datos NO traen ningún fragmento del corpus. No finjas haber contestado: no respondas de
  memoria, no lo esquives con una generalidad que suene a respuesta y no cites nada.
```

Y la garantía, que es código y no una frase en el prompt:

```python
# assist/constants.py
CAUSE_PLACEHOLDER_IN_FREE_QUERY = "placeholder_in_free_query"   # ∈ HARD_VIOLATION_CAUSES
# verification.py: se comprueba SÓLO cuando product_id is None
```

`uncovered` se calcula también para `route in ("knowledge", "both")` en el modo libre, emitiendo
`WARNING_KNOWLEDGE_NOT_COVERED` — **cuya copia castellana ya existe** desde C36.

### ai-service · `filters` en `AssistRequest`

```python
class AssistRequest(BaseModel):
    ...
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
```

Y en el orquestador, el único cambio que M1 necesitaba:

```python
retrieved = await retrieve_products(
    RetrievalRequest(query=question, top_k=payload.top_k, filters=payload.filters), ...)
```

**Adición pura**: ningún campo se retira ni cambia de tipo. Se verifica **hoja a hoja** contra la línea
base del snapshot, como ya hizo C31.

### ai-service · la sonda sin filtro

```text
si filters.is_empty:            una sola sentencia, comportamiento idéntico al de hoy
si no:                          dos sentencias, SECUENCIALES (una conexión de pool a la vez, D10)
   1ª  sin filtros  → distances_probe  → should_abstain(distances_probe, rule)
   2ª  con filtros  → vector_hits      → candidatos, orden y ventana (prefiltro intacto, H2)
```

El embedding **ya está calculado**, así que no hay segunda llamada al proveedor. El módulo de filtros ya
midió que *«at 1.168 rows a hard filter saves no time»*, así que el escaneo extra es de un dígito de
milisegundos y **sólo se paga cuando el operario ha filtrado**.

Dos mensajes que hoy no se distinguen:

| Situación | Qué se emite |
|---|---|
| Perfil **sin filtro** plano | abstención — «No tengo nada que encaje con lo que describes» |
| Perfil con pico + conjunto filtrado escaso | `filters_too_narrow` — «Hay piezas que encajan, pero ninguna es una diadema de oro» |

**Y el requisito que esta forma obliga a escribir:** la spec de `retrieval-abstention` dice que la regla
*«does not alter the candidate set, which is what lets the calibration re-score persisted windows»*. Con
un insumo distinto de la ventana persistida, `--rescore` deja de poder recalcular la decisión **en las
pasadas filtradas** — en las sin filtrar, que son todo el conjunto dorado, nada cambia. La spec debe
declarar **que la sonda es sin filtro y por qué**, y **que sus distancias se persisten**.

### ai-service · la contradicción del enrutador

```python
# routing.py — RoutingOutcome.route
# served=in_domain + missing_axis=None + index=None es una respuesta internamente
# contradictoria: el esquema dice de index «Null cuando NO se atiende», y un veredicto
# in_domain ES atender. El fail-open ya consulta las dos ramas, así que se atiende.
if self.decision.index is None:
    return "both"        # y se registra cause=router_index_absent
```

Dispara en **5 de 42 · 11,9 %** (H7). Hoy el servicio **ya paga las dos ramas** y luego no genera
porque no hay sección de tarea: es trabajo tirado dentro del servicio. La contradicción sigue siendo
**observable** por causa en el registro, que es el patrón con el que este repositorio lee su puerta.

### ai-service · el tercer perfil de claims

```python
# auth.py
UNSCOPED_CLAIMS = BASE_CLAIMS   # recuperación y assist sin ámbito de punto de venta
```

**El argumento que hay que escribir en la spec**, porque el comentario de `AiCallScope` parece
prohibirlo: lo que ese comentario teme es un **valor centinela llegando al filtro duro**. Una claim
**ausente** hace que el prefiltro **no se aplique**, no que «case con todo», y **falla cerrado** en
cualquier ruta que la exija —ficha y inventario—. Un test por cada operación que debe seguir
rechazándolo.

### backend · filtros en la ruta degradada

```csharp
Task<IReadOnlyList<AssistedSearchRow>> SearchLexicalAsync(
    IReadOnlyList<string> terms, Guid? pointOfSaleId, AiSearchFilters filters,
    int take, CancellationToken cancellationToken);
```

`JOIN` a `ProductAiProfiles` y dos `AND`: `PieceType` al **97,7 %** y `MaterialsJson` al **91,5 %**.
**Filtros duros porque los pulsó una persona** (Q4), con el riesgo declarado: el **8,5 %** del catálogo
sin materiales extraídos desaparece al filtrar por material. `pointOfSaleId` pasa a nullable para el
ámbito «todos» del tramo 4.

### backend · el segundo endpoint y el de disponibilidad

| Ruta | Método | Rol | Notas |
|---|---|---|---|
| `POST /api/ai/search/assisted` | POST | autenticado, POS autorizado o ámbito «todos» | **Su propia** política de límite, su interruptor, su presupuesto y su circuito (`ai-assist`) |
| `GET /api/ai/search/availability?pointOfSaleId=` | GET | autenticado | **Ninguna llamada a la IA.** Devuelve los dos interruptores para ese POS |

Por qué dos endpoints y no un campo `mode`: **el límite de peticiones es un atributo de endpoint en
ASP.NET**, y las cuatro propiedades ya difieren y ya están modeladas por feature. El precedente está
escrito en `AiSalesAssistOptions`: *«the card is a different feature … and its generative route has a
cost profile search does not»*.

```csharp
public class FreeQuerySearchResponse          // hereda el embudo, añade lo de M1
{
    public List<FreeQueryGroupDto> Groups { get; set; } = [];   // ← agrupado, no lista plana
    public string? Pitch { get; set; }
    public FreeQueryPitchStatus PitchStatus { get; set; }
    public List<SalesAssistCitationDto> Citations { get; set; } = [];
    public List<string> Warnings { get; set; } = [];            // sólo los de CONSULTA (D8)
    public string? ClarificationQuestion { get; set; }
    public string? Intent { get; set; }                         // separa los dos route=none
    public bool Abstained { get; set; }
    public bool AiAvailable { get; set; }
    public string? DegradedReason { get; set; }
    public FreeQueryUsageDto? Usage { get; set; }               // sólo para administrador
    // + SearchEventId, PointOfSaleId?, CandidatesReturned, SurvivedHydration, TraceId
}
```

### backend · `degradedReason` y el cuarto `SearchOrigin`

```csharp
public enum SearchOrigin { Assisted = 1, LexicalFallback = 2, Disabled = 3,
                           AssistedGenerative = 4 }   // HasConversion<int>() ⇒ SIN migración
```

Con ese valor la ablación del toggle pasa a ser **una consulta SQL** sobre `ProductSearchEvent`, que ya
lleva `FiltersJson`, `RetrievalMs`, `TotalMs` y `SelectedFromRank`. El comentario del propio enum dice
que su tercer valor existe para ser *«el brazo de control»*.

`SalesAssistResponse` gana `DegradedReason` con los **seis valores** que ya se calculan: cierra la
limitación 3 de C34 y separa `product_not_indexed` de `ai_unavailable`.

### frontend · los dieciséis estados

La tabla completa, con qué trae cada estado y qué acción ofrece, está en
[`c40-m1-panel-states.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md).
Los cinco que hay que leer antes de escribir una línea:

| # | Estado | Qué pinta, y el error por defecto que evita |
|---|---|---|
| **4** | `in_domain` + sin ruta · **11,9 %** | «No he acabado de entender la consulta» **con los resultados delante**. Tras la coerción a `both`, casi desaparece |
| **5** | `unclassified` + sin ruta | «El argumentario no está disponible ahora mismo». **No se pide reformular**: el clasificador no corrió, y pedirlo sería culpar al operario de una credencial ausente |
| **9** | ruta `knowledge` con prosa | **Cero piezas y una respuesta correcta.** Las cinco ramas de vacío de hoy escribirían «Sin resultados» encima de ella |
| **12** vs **14** | la puerta retiró el argumentario · no hubo generación | Se distinguen **sólo por `promptVersion`**, y C36 ya sabe pintar esa distinción: se reutiliza |
| **7** | filtro estrecho | `filters_too_narrow`, **con argumentario si hay piezas**: las que sobrevivieron sí encajan, y eso es lo que la sonda acaba de establecer |

**La partición de los avisos es por sujeto, no por lista** —y así resuelve la contradicción de D8, que
literalmente se comería los dos códigos de rechazo porque `refusal_codes` se apila en el mismo
`warnings[]`:

| Sujeto | Códigos | En M1 |
|---|---|---|
| **una pieza** | `family_has_variants`, `size_label_missing`, y los dos de stock de .NET | **no se pintan** |
| **la consulta** | `query_out_of_domain`, `query_not_in_catalogue`, `knowledge_not_covered`, `filters_too_narrow` | **sí se pintan** |

### frontend · toggle, badge y ámbito

- **Toggle**: dos opciones sobre la misma consulta, **por defecto la semántica**, que es la barata, y
  **sin recordar la elección entre visitas**. El coste se dice **antes** de pulsar: **2.500 ms contra
  10.000 ms** de presupuesto y **30/min contra 10/min** de cupo.
- **Badge**: cuatro estados leídos de `GET /api/ai/search/availability` **antes** de buscar. Con la
  asistida apagada, **la opción del toggle se deshabilita con su motivo**, no falla al pulsarla.
- **Ámbito «todos»**: la etiqueta de existencias dice **«Selecciona tienda para ver stock»** y no un
  cero; el botón de ficha **se deshabilita**; cambiar de tienda **sólo refresca la cifra y no llama a
  ningún modelo**.
- **La fila enseña su grupo**: «también en XS, S, M, L y 4 tallas más», con degradación al SKU cuando
  falta la etiqueta —la misma regla que C36 aplica en el bloque de familia— y **nada escrito** con un
  solo miembro.

### Specs de OpenSpec

| Capability | Delta | Contenido |
|---|---|---|
| **`ai-free-query-search`** | **ADDED** | El endpoint de M1 con su interruptor, su límite, su presupuesto y su circuito propios · la ruta de disponibilidad sin IA · el ámbito «todos» y quién puede usarlo · la forma agrupada de la respuesta · `degradedReason` · el origen de telemetría nuevo |
| `assisted-search-panel` | **MODIFIED** | Toggle con su coste dicho antes · badge de cuatro estados · los dieciséis estados y la partición de avisos por sujeto · la fila que enseña su grupo · la etiqueta que nombra la tienda · el embudo ampliado sin euros |
| `ai-assisted-search` | **MODIFIED** | Los filtros se aplican también en la ruta degradada, y si no se aplicaran se dice |
| `assist-generation` | **MODIFIED** | `filters` en la petición · `v5` sin precio ni disponibilidad en el modo libre · la cuarta tarea sin cobertura y `uncovered` en M1 · la causa dura de marcador · la coerción a `both` |
| `retrieval-abstention` | **MODIFIED** | La decisión lee una **sonda sin filtro**, y sus distancias se persisten para el re-scoring |
| `vector-retrieval` | **MODIFIED** | La sonda como segunda sentencia, secuencial y sólo con filtros presentes |
| `ai-service-api-contracts` | **MODIFIED** | `AssistRequest.filters` y el snapshot regenerado, adición pura |
| `ai-sales-assist` | **MODIFIED** | `degradedReason` sube a la respuesta |
| `ai-search-telemetry` | **MODIFIED** | Cuarto origen, y la ablación como consulta |
| `ai-gateway-client` | **MODIFIED** | Se retira el rechazo de la consulta libre; tercera clase de ámbito, refusada donde el punto de venta es obligatorio |
| `ai-service-auth` | **MODIFIED** | Tercer perfil de claims para las rutas sin ámbito de punto de venta |

**Una `ADDED` y diez `MODIFIED`.** Es mucho, y es la razón de que la línea de corte agrupe los tramos
**por subconjunto de specs**: un tramo aplazado no deja ninguna spec a medias.

Descripción de requisito **en una sola línea física**, con su `SHALL`/`MUST` en ella: el validador sólo
lee la primera.

---

## Arquitectura

```text
            ┌──────────── GET /api/ai/search/availability ─────────── sin IA, 4 estados
            │
   assisted.tsx ──[toggle]──┬──▶ POST /api/ai/search            2.500 ms · 30/min · ai-retrieval
                            │        └─ degradada: AHORA con filtros (D5)
                            │
                            └──▶ POST /api/ai/search/assisted  10.000 ms · 10/min · ai-assist
                                         │
                                         ▼
                            AssistSaleAsync(product_id=null, query, FILTERS)   ← D2, guard retirado
                                         │
                      ┌──────────────────┴──────────────────┐
                      │        POST /v1/assist/sale         │
                      │  classify_query  ← 1 llamada, ~2 s  │
                      │    índice nulo → both (P1)          │
                      │  retrieve_products(filters)         │
                      │    sonda SIN filtro → abstención    │  ← D17
                      │  search_knowledge → uncovered (D12) │
                      │  generate_pitch  assist/v5          │  ← D11, sin marcadores
                      │  puerta: placeholder_in_free_query  │
                      └──────────────────┬──────────────────┘
                                         ▼
                      hidratación .NET (reutilizada) · telemetría SearchOrigin=4
                                         ▼
      ┌──────────────────────────────────────────────────────────────────┐
      │ badge (4 estados) · toggle con su coste dicho                    │
      │ 16 estados distinguidos · avisos SÓLO de consulta (D8)           │
      │ argumentario + citas ▸ claimScope · «sin fuente verificable»     │
      │ filas agrupadas: «también en XS, S, M y 4 tallas más»            │
      │ stock: «8 en Ciutadella Centre» | «Selecciona tienda…»           │
      │ embudo admin: ai_ms · total_ms · modelo · tokens · SIN euros     │
      └──────────────────────────────────────────────────────────────────┘
```

**Decisiones heredadas:**

- **C16** — *«a search is issued only when the operator asks for one»*, aquí sobre una llamada cuatro
  veces más lenta; etiqueta neutra para un código desconocido; vacíos distinguibles; página corta
  declarada; guarda de respuestas fuera de orden; episodio por visita.
- **C31** — el enrutador corre **una vez y sólo en M1**, sin reintento y sin reparación; los dos
  rechazos son **dos códigos distintos**; la repregunta la escribe el código y nunca el modelo; el
  *fail-open* consulta las dos ramas.
- **C34** — el cliente `ai-assist` con su presupuesto, su suelo y su circuito; un marcador sin resolver
  **retira el argumentario y no la respuesta**; el 422 no se lee como caída.
- **C36** — la tabla de copy con etiqueta neutra, y la distinción `withheld_by_ai` / `not_generated`,
  que se reutilizan tal cual.
- **C25 / `retrieval-abstention`** — la regla es **relativa** y sobre el perfil de distancias, calibrada
  contra 20 consultas fuera de dominio y 43 contestables **sin filtros**.
- **§7.3 del diseño** — *«lo que un humano pulsa filtra; lo que una regla infiere del texto degrada»*,
  que es exactamente Q4 aplicada también a la ruta degradada.

**Breaking changes:**

- **`ai-service/openapi.json` se mueve**, por **adición pura** verificada hoja a hoja. Un consumidor
  que no envíe `filters` recibe el comportamiento de hoy.
- **`SearchLexicalAsync` cambia de firma** — interfaz interna del backend, sin consumidores externos.
- **`AiCallScope` gana una tercera clase**, y el ámbito nuevo debe ser **refusado** por toda operación
  que exija punto de venta. Es la relajación de una invariante con test, y va con su propio test.
- **`SalesAssistResponse` gana un campo**: aditivo, y la ficha de C36 ya sabe pintar estados
  distinguidos.
- **Ningún campo se retira ni cambia de tipo** en ninguna de las dos fronteras.

---

## Definición de Hecho (DoD)

- [ ] Código según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] **Línea base de las DOS suites medida antes de tocar nada** (`git stash push -u`, ejecutar,
      `git stash pop`): se compara el **conjunto de nombres** que fallan, nunca el número. Las dos vienen
      rojas de fábrica, y el frontend además **oscila entre 113 y 114** por un test dependiente del orden
- [ ] La salida de `vitest` se lee **en su línea de resumen**, no por el código de salida
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus, integración con Testcontainers, nomenclatura
      `Método_Escenario_ResultadoEsperado`, cobertura ≥ 70 % en el código nuevo
- [ ] Un test de integración comprueba que **la ruta degradada aplica tipo de pieza y material**
- [ ] Un test comprueba que el **ámbito nuevo es refusado** por la ficha, los sustitutos y el inventario
- [ ] Un test comprueba que `SalesAssistResponse.DegradedReason` distingue `product_not_indexed` de
      `ai_unavailable`
- [ ] `ai-service`: `uv run pytest` en verde **sin llamadas reales** a LLM, embeddings ni RDS
- [ ] `test_free_query_pitch_carries_no_placeholder` — y el **recuento de `{{price}}`/`{{stock}}` sobre
      el texto generado, antes y después de `v5`**, publicado. **Es la cifra que decide si M1 tiene prosa**
- [ ] `test_free_query_without_corpus_uses_the_uncovered_task`
- [ ] `test_abstention_reads_the_unfiltered_profile` y un test de que **sin filtros no se emite una
      segunda sentencia**
- [ ] `test_served_verdict_without_index_is_routed_to_both`, con `router_index_absent` en el registro
- [ ] `test_openapi_snapshot_is_stable` actualizado, y el movimiento verificado **hoja a hoja**: **0
      hojas retiradas y 0 cambiadas de tipo** contra la línea base
- [ ] Frontend: Vitest + React Testing Library, `should [comportamiento] when [condición]`, queries
      accesibles, cobertura ≥ 70 % en el código nuevo
- [ ] Los tests **envuelven los proveedores** o mockean el hook —causa de un tercio de los fallos de
      línea base—, con `pages/sales/__tests__/cart.test.tsx` como plantilla
- [ ] Los servicios se mockean con **`vi.mock`** y no se confía en MSW: con `onUnhandledRequest: 'warn'`
      un test puede pasar **sin haber afirmado nada**
- [ ] Un test comprueba que el badge se pinta **antes** de cualquier búsqueda y **sin llamar a la IA**
- [ ] Un test comprueba que con la asistida apagada **la opción del toggle está deshabilitada con su
      motivo**
- [ ] Un test distingue **el estado 4 del 5** y comprueba que al 5 **no se le pide reformular**
- [ ] Un test comprueba que `route=knowledge` con cero piezas **no se anuncia como vacío**
- [ ] Un test comprueba que los avisos **de pieza no se pintan** en M1 y los **de consulta sí**
- [ ] Un test comprueba que con ámbito «todos» la etiqueta **no muestra un cero** y el botón de ficha
      **está deshabilitado**
- [ ] Un test comprueba que el embudo **no muestra euros** y que **un operador no lo ve**
- [ ] Un test comprueba que cambiar de tienda **no emite ninguna petición a la IA**
- [ ] `npm run build` y `dotnet build` en verde — `tsc --noEmit` se filtra a los ficheros propios
- [ ] **Sin migración de EF Core** y sin tabla nueva; el cuarto `SearchOrigin` se comprueba sobre la
      columna `int` existente
- [ ] UI en **es-ES** y moneda **EUR (€)** con `Intl.NumberFormat('es-ES')`
- [ ] **Verificación de completitud**: recorrido **campo a campo** de `SalesAssistResponse`,
      `AssistedSearchResponse` y `FreeQuerySearchResponse`, señalando dónde se pinta cada campo o
      declarando por qué no
- [ ] Specs delta con la **primera línea física** de cada requisito llevando su `SHALL`/`MUST`
- [ ] `openspec validate --all --strict` → **0 failed** (el de un solo change **no basta**)
- [ ] **Latencia p50/p95 extremo a extremo por .NET** sobre las 42 consultas, publicada
- [ ] **Reparto de los dieciséis estados** sobre esas 42, publicado y **persistido** con `run_id`,
      `git_sha` y `prompt_version` en `ai-service/evals/results/`
- [ ] Comprobación con datos reales en local (`STUB_MODE=false`, credencial real): catálogo,
      conocimiento, mixta, los dos rechazos, la repregunta, el filtro estrecho y el ámbito «todos»
- [ ] Documentación: `Documentos/epicas.md`, plan de changes, diseño (§15.12 y §15.13 **cerradas**,
      §15.14 matizada), los tres README y `openspec/DEFERRED_TASKS.md`
- [ ] Sin TODO/FIXME sin tarea de seguimiento

**No aplica:** migración de EF Core; Playwright (el flujo crítico de venta no cambia de comportamiento);
`terraform/` y `.github/workflows/`.

---

## Requisitos No Funcionales

- **Seguridad y privacidad:**
  - **El ámbito nuevo no es una relajación, es una tercera clase**, y toda operación que exija punto de
    venta debe **rechazarlo con test**. Una claim ausente hace que el prefiltro **no se aplique** —no que
    case con todo— y **falla cerrado**.
  - La consulta de M1 se persiste en `ProductSearchEvent.SearchText`, heredando la **limitación de
    retención del §15.11** y declarándola. **La pregunta de la ficha sigue sin guardarse.**
  - Ni el argumentario resuelto ni la consulta se escriben en `console` en ningún nivel, ni entran en el
    embudo de administrador.
  - La autorización la decide .NET; el panel **no la anticipa** ni oculta piezas por su cuenta.
- **Rendimiento y coste:**
  - **Una petición por acto explícito.** Sin búsqueda al teclear, al cambiar filtro ni al cambiar de
    tienda. Sin reintento automático y **sin caché** en la ruta generativa.
  - **El presupuesto está en su techo**: 10.000 ms con suelo validado de 8.000. C34 midió **p95 7,1 s**
    sin enrutador y M1 le suma ~2 s, así que **se mide y se publica**; si no cabe, el corte
    pre-autorizado es **no generar en la ruta `catalog`** de M1 (≈ 40 % de sus generaciones).
  - La sonda sin filtro **no se emite si no hay filtros**, y nunca hay una segunda llamada al proveedor.
  - Estado de carga explícito desde el primer instante, nunca una pantalla en blanco.
- **Observabilidad:**
  - `trace_id` propagado; `stage=assist` ya registra `intent`, `route`, `router_degraded`, `task`,
    `groups`, `citations`, `abstained`, `pitch_chars`, `violations` y `withdrawn`, y gana
    `router_index_absent`.
  - El embudo enseña **las entradas de un coste y nunca el coste**: tokens y modelo, jamás euros. Una
    tarifa en el frontend está mal el día que el proveedor la mueve, y `usage.model` **no es una clave de
    precio** en la ruta del agente.
- **Accesibilidad y presentación:**
  - Estados marcados **por texto además de por color**, como ya hace la fila de C16.
  - Legible en móvil: el panel se usa de pie, en el mostrador.
- **Robustez:**
  - Ningún desenlace del servicio lanza; **los dieciséis estados** se pintan con una frase verdadera.
  - Un código de aviso desconocido **degrada la fila**, no la rompe.
  - Una respuesta obsoleta nunca sobreescribe a una más nueva.
  - El *fail-open* del enrutador se conserva: sin clasificador, la ruta sirve lo que servía antes.

---

## Preguntas Abiertas

Las diecisiete decisiones de diseño se cerraron con el desarrollador en las dos sesiones del
2026-09-24. Quedan éstas, todas con opción por defecto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| 1 | ¿Capability nueva para el endpoint de M1, o se amplía `ai-assisted-search`? | **Nueva**, `ai-free-query-search`, siguiendo el precedente de `ai-sales-assist`: otro interruptor, otro límite, otro presupuesto, otro circuito. El panel sí se queda en `assisted-search-panel` modificada (D1) |
| 2 | ¿Ruta del endpoint nuevo? | `POST /api/ai/search/assisted`, bajo el árbol que el operario ya conoce |
| 3 | ¿El toggle recuerda la última ruta entre visitas? | **No**, y por defecto **la semántica**: recordar la cara es la forma de gastarla sin querer |
| 4 | ¿M1 reutiliza el cupo de 10/min de la ficha? | **No**, sección propia: la ficha se abre una vez por pieza y el panel se usa en ráfaga |
| 5 | ¿Quién puede usar «todos los puntos de venta»? | **Operarios y administradores** (D6, D13), con requisito y test. La variante conservadora —sólo administrador— es el corte del tramo 4 |
| 6 | ¿Se guarda la consulta de M1 en `SearchText`? | **Sí**, por coherencia con C04, con la limitación del §15.11 heredada y declarada. La pregunta de la ficha **sigue sin guardarse** |
| 7 | ¿El embudo muestra `usage.model` como clave de precio? | **No.** Modelo y tokens, nunca el producto |
| 8 | ¿La coerción a `both` necesita requisito propio? | **Sí**, en `assist-generation`: cambia qué recibe un consumidor en el 11,9 % de las consultas libres. Lo interno es la causa de registro |
| 9 | ¿Se persiste el artefacto de la pasada de verificación? | **Sí**, con `run_id`, `git_sha` y `prompt_version`. La pasada de 42 de la exploración **no quedó guardada**, y de ahí la exigencia |
| 10 | ¿El argumentario de M1 se genera también en la ruta `catalog`? | **Sí**, salvo que la latencia medida no quepa: entonces se corta esa ruta —≈ 40 % de las generaciones— y **se declara** |
| 11 | ¿`filters_too_narrow` se emite también en la ruta semántica del toggle? | **Sí.** La sonda vive en `retrieval/`, así que el panel semántico gana la misma distinción sin coste añadido |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
añada migración de EF Core, **no** cambie el comportamiento de la ficha de C36 más allá de
`degradedReason`, **no** retire ni cambie de tipo ningún campo del contrato congelado, y **no** suprima
ningún dato que el backend haya emitido.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Es el **nodo de arranque de lo que queda**, `C40 → C38 → C39`, y cierra
  **tres limitaciones declaradas** del §15. Su tramo 2 **no admite corte**.
- **Estimación:** _Pendiente de refinamiento_. Orientativamente **por encima de C34 y C36**: tres capas,
  el contrato congelado se mueve, una frontera de autorización se toca y **once capabilities** entran en
  el delta. La dificultad no es ninguna pieza suelta: es que **dieciséis estados tienen que distinguirse
  sin mentir**.
- **Dependencias:** C16, C31, C34 y C36 archivados. **No se abre a la vez que C16 ni C36** (misma página
  y servicio del frontend) ni a la vez que **C21, C22 o C25** (pipeline de ranking en `retrieval/`). Con
  **C38** no es disciplina de rama, es **orden obligado**.
- **Línea de corte** (regla 5 del §1, y ordenada por *cuánto engaña hoy la pantalla*):
  1. **Filtros en la degradada, badge con su ruta de lectura, `degradedReason` y el cuarto
     `SearchOrigin`** — sólo .NET y frontend, **archivable solo**, y arregla las tres averías que la
     sesión encontró por accidente.
  2. **`filters` en el contrato, `assist/v5` con la causa dura, la cobertura de M1, el segundo endpoint,
     el toggle y el castellano de los dos rechazos** — **este tramo no se corta**: sin él, el panel
     asistido sale **sin prosa**.
  3. **La sonda sin filtro, `filters_too_narrow`, los dos `route=none`, la repregunta y la coerción.**
  4. **«Todos los puntos de venta»** — **el primer candidato a salir**, por delante del embudo: una
     frontera de autorización arriesga más que enseñar un dato que hoy no está. Variante conservadora:
     sólo administrador.
  5. **La fila que enseña su grupo.**
  6. **El embudo de observabilidad** — el último, porque es el único que **no arregla nada que hoy
     engañe**.

  Los tramos que no entren **se declaran aplazados con su motivo**, no se callan. Cortar el 3 deja el
  filtro estrecho **más grave que antes de C40**, porque M1 añade el párrafo que hoy no existe: eso se
  escribe.
- **Tags:** `HU-AIENG-040`, `C40`, `EP15`, `free-query`, `M1`, `intent-router`, `abstention`,
  `filters`, `frontend`, `dotnet`, `python`, `contract-change`, `observability`, `es-ES`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-040](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040.md)
- **Informes de exploración:**
  [c40-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md)
  *(§1-§9 contra el servicio real, §10 contra el código)* ·
  [c40-m1-panel-states.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md)
  *(los dieciséis estados, y las tres recomendaciones P1, P2 y P3)*
- **Plan y diseño:**
  [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md),
  ficha C40 y su línea de corte;
  [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md),
  §4, §6.4, §7.3, §7.7, §11.2 y §15.11-§15.14.
- **Specs vivas que entran en el delta:**
  [`assisted-search-panel`](../../../specs/assisted-search-panel/spec.md) ·
  [`ai-assisted-search`](../../../specs/ai-assisted-search/spec.md) ·
  [`assist-generation`](../../../specs/assist-generation/spec.md) ·
  [`retrieval-abstention`](../../../specs/retrieval-abstention/spec.md) ·
  [`vector-retrieval`](../../../specs/vector-retrieval/spec.md) ·
  [`ai-service-api-contracts`](../../../specs/ai-service-api-contracts/spec.md) ·
  [`ai-sales-assist`](../../../specs/ai-sales-assist/spec.md) ·
  [`ai-search-telemetry`](../../../specs/ai-search-telemetry/spec.md) ·
  [`ai-gateway-client`](../../../specs/ai-gateway-client/spec.md) ·
  [`ai-service-auth`](../../../specs/ai-service-auth/spec.md) ·
  [`sales-assist-card`](../../../specs/sales-assist-card/spec.md) *(consume `degradedReason`)*
- **Precedentes:**
  [T-AIENG-016](../../archive/2026-08-29-add-frontend-assisted-search-panel/ticket.md) *(el panel que se
  amplía)* · [T-AIENG-031](../../archive/2026-09-16-add-guardrails-and-intent-router/ticket.md) *(el
  enrutador y sus dos cifras que nunca se suman)* ·
  [T-AIENG-034](../../archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/ticket.md) *(el
  cliente generativo y los marcadores)* ·
  [T-AIENG-036](../../archive/2026-09-24-add-frontend-assist-card-and-family-disambiguation/ticket.md) *(la
  tabla de copy y la distinción de estados)*
- **Apuntes del Máster (guía, no dogma):**
  [S4 · De interfaz conversacional a interfaz de producto](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/De%20interfaz%20conversacional%20a%20interfaz%20de%20producto.md)
  *(el panel es «chat con parámetros», no un chat)* ·
  [S9 · Retrieval que no es sólo cosine](../../../../Documentos/Sesiones%20Master%20AIEng/S9_Fundamentos_RAG/Retrieval%20que%20no%20es%20solo%20cosine%20-%20top-K,%20threshold%20y%20filtros%20sobre%20pgvector.md)
  *(pre contra post filtrado: el que descarta la alternativa barata de D17)* ·
  [S16 · Un sistema debe saber decir «no lo sé»](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Un%20sistema%20debe%20saber%20decir%20%E2%80%9CNo%20lo%20se%E2%80%9D.md)
  *(los tres caminos, y «un guardrail es código, no una frase en el prompt»)* ·
  [S16 · Coste, latencia y A/B testing](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Coste,%20latencia%20y%20A%20B%20Testing.md)
  *(que es lo que matiza D3: el toggle demuestra la ablación, no la mide)* ·
  [S11 · Citación y atribución verificable](../../../../Documentos/Sesiones%20Master%20AIEng/S11_RAG_avanzado/Citacion%20y%20Atribucion%20verificable.md)
- **Tareas diferidas:** [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md). Se **cierra** la limitación 3 de
  C34. Siguen abiertas *«C32b — política de timeout y circuito de `/v1/assist/agent`»*, *«C34 — el
  corpus no viaja en la imagen de `jbg-ai`»* —que **pesa más aquí**: sin corpus, M1 responde siempre sin
  citas— y *«telemetría de la ficha»*, que sale como change propio.
- **Testing:** [testing-frontend.md](../../../../Documentos/testing-frontend.md) ·
  [testing-backend.md](../../../../Documentos/testing-backend.md), las dos en *Estado de la suite: fallos
  conocidos*.
- **Componentes:** [analisis-metronic-frontend.md](../../../../Documentos/Propuestas/analisis-metronic-frontend.md).
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
  · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-24 | `/enrich-us` | Creación a partir de HU-AIENG-040 y de las **dos pasadas** de exploración del mismo día. Recoge: el panel de C16 convertido en M1 sin pantalla nueva; `filters` en `AssistRequest` como adición pura; **`assist/v5` más la causa dura `placeholder_in_free_query` y la retirada del guardia de la pasarela, sin los cuales M1 no tiene prosa**; `uncovered` y una cuarta tarea de consulta libre sin cobertura; un **segundo endpoint** con interruptor, límite, presupuesto y circuito propios, más una **ruta de disponibilidad sin IA** para el badge de cuatro estados; filtros duros en la ruta degradada con `PieceType` al 97,7 %; `degradedReason` al DTO y un **cuarto `SearchOrigin` sin migración** que convierte la ablación en una consulta SQL; la **abstención leyendo una sonda sin filtro** y `filters_too_narrow`; **`route=none` partido en dos estados** con copia distinta y la **coerción a `both`** para el 11,9 % contradictorio; la **partición de los avisos por sujeto**, que resuelve que D8 se comiera los dos códigos de rechazo; el ámbito «todos los puntos de venta» como **tercera clase explícita** con tests de rechazo; la fila que enseña su grupo; y el embudo de administrador **sin euros**. Una capability `ADDED` y diez `MODIFIED`, con la línea de corte agrupada por subconjunto de specs |
