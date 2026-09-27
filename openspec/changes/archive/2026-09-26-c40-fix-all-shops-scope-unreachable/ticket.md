# T-AIENG-040-FIX: The every-point-of-sale scope is unreachable from the panel — give the administrator a control, make the availability probe accept its absence, and give the spec the requirement that was missing (C40_FIX)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla de los
> tickets del Proyecto Final.
>
> **Fuentes de verdad:** las specs vivas
> [`ai-free-query-search`](../../../specs/ai-free-query-search/spec.md) y
> [`assisted-search-panel`](../../../specs/assisted-search-panel/spec.md), el
> [change archivado de C40](../../archive/2026-09-25-add-frontend-free-query-panel/) con su
> [ticket](../../archive/2026-09-25-add-frontend-free-query-panel/ticket.md) y su
> [informe](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md),
> la historia [HU-AIENG-040-FIX](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md),
> y **el código real**, que es de donde sale todo lo que sigue.

**Change:** `c40-fix-all-shops-scope-unreachable` (C40_FIX) · **Épica:** EP15
**HU origen:** [HU-AIENG-040-FIX](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md)
**Abierto:** 2026-09-25 · **Enriquecido:** 2026-09-26 · **Corrige:** C40, archivado el 2026-09-25
**Origen:** pruebas manuales del usuario sobre el entorno levantado tras el cierre de C40.

---

## Título

Dar entrada desde el panel al ámbito «todas las tiendas» que C40 construyó entero y dejó inalcanzable — **para el administrador**, por la ruta de respuesta asistida, con la sonda de disponibilidad aceptando la ausencia de punto de venta y con el requisito de spec que nadie escribió.

---

## Contexto y Problema

### El defecto, en una frase

**El ámbito «todas las tiendas» que C40 construyó no se puede alcanzar desde la pantalla, por ningún
rol, ni siquiera administrador.** El backend lo acepta en la ruta generativa, la autorización lo permite
a operarios y administradores, los DTO se volvieron anulables para ello y la fila tiene sus tres
estados — y **el selector del panel no ofrece la opción**, así que nadie puede usarlo.

> **⚠️ CORRECCIÓN DEL 2026-09-26 — el fix son TRES piezas, no dos.** La versión anterior de este ticket
> decía «DOS piezas» y **es falso**. Falta la tercera, que es la que decide el diseño: **la ruta rápida
> —`POST /api/ai/search`, la que el panel usa por defecto— rechaza el ámbito global con un 400 de
> validación.** Está en el §1.3. Sin resolverla, añadir la opción al selector hace que el primer
> *Buscar* del administrador pinte en pantalla «La búsqueda asistida requiere un punto de venta» justo
> debajo del control que se lo acaba de ofrecer.

### Por qué no falló nada, que es el hallazgo de verdad

Fui a las specs esperando una violación y **no la hay**. Los tres escenarios del panel están
condicionados así:

> **WHEN** the search is scoped to every point of sale → **THEN** the stock label states that a point
> of sale must be selected to read stock…

Describen qué hace el panel **estando** en ese estado. **Ninguno exige que el panel ofrezca la forma de
entrar en él.** Y el requisito de `ai-free-query-search` dice *«The route SHALL accept a request scoped
to every point of sale»* — **la ruta**, que sí lo hace.

Así que la letra se cumple, y por eso los **136 escenarios de C40 salieron verdes** y su verificación
independiente —que sí encontró una cuarta infracción de completitud y dos afirmaciones falsas del
informe— **pasó por encima de esto**.

**Pero el hueco no es pasivo: es peor.** [`assisted-search-panel/spec.md:88`](../../../specs/assisted-search-panel/spec.md) afirma hoy:

> *The panel SHALL send a concrete point of sale on every search.*

Eso **dejó de ser cierto con C40**. La spec viva no calla: **contradice lo que el sistema hace**. Y
`openspec validate --all --strict` seguiría en verde sobre ella, porque valida **estructura y no
verdad** — la misma puerta que dejó pasar las tres specs malformadas de agosto, en su versión peor:
aquéllas rompían el formato y el validador las cazó; ésta está bien formada y miente.

**Y es la tercera aparición del mismo modo de fallo en esta familia de cambios.** El §11 de C40 declara
que su barrido de completitud **empareja por nombre**, de modo que un campo leído en una superficie
cuenta como leído en todas — así se le escapó que `FreeQuerySearchResponse.searchEventId` no tenía
lector. Su verificación arregló eso y cometió la variante: auditó **el estado** sin comprobar su
**alcanzabilidad**. Los tres casos son la misma cosa — *verificar la pieza en aislamiento en vez del
camino hasta ella*. Eso debería dejar rastro en la spec, no sólo en el código.

### Estado actual del código, verificado línea a línea contra el árbol

> Exploración del 2026-09-25 ampliada el 2026-09-26. **No hace falta repetirla.**

#### 1.1 · La opción no existe en el selector — y para el operario de una sola tienda el selector tampoco

| Dónde | Qué impide |
|---|---|
| [`assisted.tsx:357`](../../../../frontend/src/pages/sales/assisted.tsx) | `{pointsOfSale.length > 1 \|\| isAdmin ? (…) : null}` — con **una sola asignación el selector no se renderiza**. Añadir un `SelectItem` no le llega a ese usuario |
| [`assisted.tsx:365-369`](../../../../frontend/src/pages/sales/assisted.tsx) | El `<SelectContent>` mapea **sólo** `pointsOfSale`. **No existe** una opción «Todas las tiendas» |
| [`assisted.tsx:196`](../../../../frontend/src/pages/sales/assisted.tsx) | `if (!trimmed \|\| !pointOfSaleId) return;` — la búsqueda **no se dispara** sin tienda |
| [`assisted.tsx:403`](../../../../frontend/src/pages/sales/assisted.tsx) | El botón *Buscar* está `disabled` sin tienda |
| [`ai-search.types.ts:284`](../../../../frontend/src/types/ai-search.types.ts) | `pointOfSaleId: string` — **obligatorio**, con el comentario *«Required: searching every shop is a scope of its own»* |
| [`ai-search.types.ts:19`](../../../../frontend/src/types/ai-search.types.ts) | Igual en `AssistedSearchRequest`: *«Always required — never inferred by the server»* |

Añádase que el efecto de carga **fija la tienda a la primera activa** ([`assisted.tsx:152-154`](../../../../frontend/src/pages/sales/assisted.tsx)),
así que el estado «sin tienda» no es que sea difícil de alcanzar: **no se alcanza nunca**. Todo lo que
hay aguas abajo de él no se ejecuta en la aplicación real, ni una vez.

#### 1.2 · La sonda de disponibilidad exige punto de venta, y el panel se queda colgado

Lo rechaza con un 400 ([`AiSearchController.cs:239-250`](../../../../backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs)):

```csharp
public IActionResult Availability([FromQuery] Guid pointOfSaleId)
{
    ...
    if (pointOfSaleId == Guid.Empty)
        return BadRequest(new { errors = new[] { "El punto de venta es obligatorio." } });
```

Y el panel, sin tienda, **se pone en blanco a sí mismo** ([`assisted.tsx:171-176`](../../../../frontend/src/pages/sales/assisted.tsx)):

```tsx
useEffect(() => {
  if (!pointOfSaleId) { setAvailability(null); setAvailabilitySettled(false); return; }
```

**Y el síntoma es peor de lo que la primera pasada anotó.** Con `settled = false`,
[`ai-availability-badge.tsx:41-49`](../../../../frontend/src/components/sales/ai-availability-badge.tsx)
renderiza **«Comprobando disponibilidad…» para siempre**: no es sólo el toggle apagado sin motivo, es
un estado de carga que no termina nunca. Y el toggle
([`assisted.tsx:378-385`](../../../../frontend/src/pages/sales/assisted.tsx)) recibe
`assistedAvailable={availability?.assistedAnswerAvailable ?? false}` — **deshabilitado y sin motivo que
enseñar**. Es **la misma forma de avería que C40 existió para corregir**: un camino que se apaga solo y
no lo dice.

**Y el cambio no son tres líneas en el controlador**, como decía la versión anterior de este ticket.
`GetAvailability` **no vive en `FreeQuerySearchService`**: vive en
[`AssistedSearchService.cs:154-170`](../../../../backend/src/JoiabagurPV.Application/Services/AssistedSearchService.cs)
y llama a `IsEnabledFor(Guid)` sobre **tres** clases de opciones distintas —
`AiFreeQuerySearchOptions`, `AiSalesAssistOptions` y `AiSearchOptions`. Cambian la interfaz, la firma,
las tres ramas y el DTO de respuesta.

Lo que sí es cierto es que **el predicado ya está decidido y razonado** en
[`FreeQuerySearchService.cs:90-94`](../../../../backend/src/JoiabagurPV.Application/Services/FreeQuerySearchService.cs):

```csharp
// With no shop named there is no per-shop entry to look up, so the default governs.
// That is the narrow reading and the safe one: a deployment that enables the feature
// shop by shop has not enabled it for «all of them».
if (!IsEnabled(options, request.PointOfSaleId))
```

```csharp
private static bool IsEnabled(AiFreeQuerySearchOptions options, Guid? pointOfSaleId) =>
    pointOfSaleId is { } named ? options.IsEnabledFor(named) : options.EnabledByDefault;
```

#### 1.3 · **EL HALLAZGO NUEVO Y EL QUE DIMENSIONA EL TICKET** — la ruta rápida rechaza el ámbito global

El panel tiene **dos** rutas y `route` arranca en `'semantic'`
([`assisted.tsx:139`](../../../../frontend/src/pages/sales/assisted.tsx)), deliberadamente: *«el valor por
defecto es la barata»*. `runSearch` construye **un** payload y lo despacha por ruta
([`assisted.tsx:210-215`](../../../../frontend/src/pages/sales/assisted.tsx)). Y el ámbito global sólo se
construyó para una de las dos:

| | `route: semantic` → `POST /api/ai/search` (**por defecto**) | `route: assisted` → `POST /api/ai/search/assisted` |
|---|---|---|
| **DTO** | [`AssistedSearchDtos.cs:18`](../../../../backend/src/JoiabagurPV.Application/DTOs/Ai/AssistedSearchDtos.cs) → `Guid PointOfSaleId` | [`FreeQuerySearchDtos.cs:30`](../../../../backend/src/JoiabagurPV.Application/DTOs/Ai/FreeQuerySearchDtos.cs) → `Guid?` |
| **Validación** | [`AssistedSearchRequestValidator.cs:29`](../../../../backend/src/JoiabagurPV.Application/Validators/AssistedSearchRequestValidator.cs) → `.NotEmpty()`, **400** | El controlador distingue **ausencia de `Guid.Empty`**: ausente → global, en blanco → 400 |
| **Ámbito** | `AiCallScope.ForPointOfSale(...)` fijo | `ScopeOf(...)` → `ForAllPointsOfSale` con nulo |
| **ámbito «todas»** | ❌ **400** «La búsqueda asistida requiere un punto de venta» | ✅ 200, catálogo completo |

**Síntoma exacto si se implementara el ticket tal como estaba escrito:** el administrador elige «Todas
las tiendas», pulsa *Buscar* sin tocar el toggle, `toOutcome` mapea el 400 a `{kind:'invalid'}`
([`ai-search.service.ts:57-65`](../../../../frontend/src/services/ai-search.service.ts)) y el panel pinta
el mensaje del servidor. **La pantalla contradiciéndose a sí misma es peor que el hueco actual.**

#### 1.4 · El interruptor de la consulta libre no está puesto en ningún sitio del repositorio

`compose.demo.yaml` pone dos de los tres interruptores de despliegue y **no el tercero**
([`compose.demo.yaml:193,198`](../../../../compose.demo.yaml)):

```yaml
AiSearch__EnabledByDefault:      "true"   # lo añadió C17
AiSalesAssist__EnabledByDefault: "true"   # lo añadió C34
#  ↑ falta AiFreeQuerySearch__EnabledByDefault — C40 no lo añadió
```

`AiFreeQuerySearchOptions.EnabledByDefault` es `bool` sin inicializador —`false`—,
`EnabledPointOfSaleIds` está vacío y **no hay sección `AiFreeQuerySearch` en ningún
`appsettings*.json`**. `backend/README.md:310,343,671` sí documenta la variable para el arranque local,
pero el compose de la demo —que existe precisamente para abrir las puertas de despliegue— se quedó
fuera.

**Deducción del código y la configuración, no comprobada sobre la demo levantada:** hoy
`GetAvailability` devuelve `assistedAnswerAvailable: false` con motivo `switched_off` para **todas** las
tiendas de la demo. El comentario que hay tres líneas más arriba en ese mismo fichero describe
exactamente este fallo: *«la que, al faltar, hizo que el entorno entero pareciera terminado sin
estarlo»*.

#### 1.5 · Una mina dormida en la rama léxica, que la decisión de alcance deja dormida a propósito

[`AssistedSearchRepository.cs`](../../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/AssistedSearchRepository.cs):

| Método | Acepta `Guid?` | Agrupa por producto con nulo |
|---|---|---|
| `HydrateAsync` | ✅ | ✅ **sí**, con comentario que explica el peligro |
| `SearchLexicalAsync` | ✅ | ❌ **no** — proyecta `ToRow` desde filas de `Inventory` |

`Carried(null)` suelta el filtro de tienda, así que un producto que tres tiendas llevan volvería **tres
veces** — y `BuildResultsAsync:405` hace `rows.ToDictionary(row => row.ProductId)`
**incondicionalmente**, en las dos ramas. Resultado: `ArgumentException` → **HTTP 500**.

Hoy el único llamante es `AssistedSearchService.DegradedAsync`, que siempre pasa una tienda concreta,
así que la rama nula es **código muerto**. Se activaría en el instante en que la ruta rápida aceptara el
ámbito global, y **primero en desarrollo local**, porque con `AiSearch:EnabledByDefault` ausente la
ruta degradada es la que corre siempre.

#### 1.6 · Lo que YA funciona y no hay que reconstruir

Comprobado en el código y en el §12 del
[informe de C40](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md):

- `AiCallScope.ForAllPointsOfSale` / `AiCallScopeKind.AllPointsOfSale`, aceptado en recuperación y
  assist, rechazado en ficha, sustitutos e inventario. El test por reflexión fija que hay exactamente
  tres caminos de construcción y ninguno acepta centinela.
- `FreeQuerySearchService.ScopeOf`: `pointOfSaleId is null → ForAllPointsOfSale`.
- `AssistedSearchResultDto.QuantityAtPointOfSale` y `HasStock` anulables — **DTO compartido** por las dos
  rutas, porque `FreeQueryGroupDto.Members` es `List<AssistedSearchResultDto>`. La hidratación sin tienda
  **agrupa por producto**: sin agrupar, un producto que tres tiendas llevan vuelve tres veces y el
  `ToDictionary` del llamador revienta por clave duplicada.
- `assisted-search-result-row.tsx` con sus **tres** estados y sus tests: no pinta cero, nombra la
  tienda cuando la hay y deshabilita el botón de ficha sin ella. **Decide por `result.hasStock === null`
  y no por `pointOfSaleName`**, así que el panel no necesita pasarle nada especial.
- `SearchRouteToggle` ya tiene el mecanismo genérico: `RouteOption` acepta `disabled` y
  `unavailableReason` y emite `data-testid="route-unavailable-<route>"`. **Falta sólo la propiedad del
  lado semántico.**
- **Autorización: el ámbito global está abierto a operarios y administradores** (tarea 12.4 de C40,
  tests `FreeQuery_ForOperatorWithAllPointsOfSale_IsServed` y
  `FreeQuery_WhenNamingAnUnassignedPointOfSale_IsRefused`). **No lo endurezcas a sólo administrador**:
  la frontera que se protege es no poder **nombrar** una tienda no asignada, no el ensanchado.
- El tercer perfil de *claims* en `deps.py` acepta un token **sin `pos_id`** en recuperación y assist,
  así que `ai-service/` no se toca en ningún escenario.
- El hueco de telemetría ya está declarado: una búsqueda global **no se registra**
  (`ProductSearchEvent.PointOfSaleId` es no nulo e indexado; registrarla exige migración de EF Core).
  Está en [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md), y el embudo ya tiene la línea «Sin
  registrar: búsqueda en todas las tiendas».
- `POST /api/ai/search/assisted` **sin** `pointOfSaleId` responde 200 y sirve resultados de todo el
  catálogo, con cantidad e indicador de stock nulos — comprobado contra el servicio en marcha.

**Un tramo entero de C40 —el grupo 12, con su frontera de autorización, su cambio de anulabilidad en
el contrato interno y su copia— existe y nadie puede llegar a él.**

#### 1.7 · Y la spec viva ya se contradice sobre el cambio de tienda

| Dónde | Qué dice |
|---|---|
| [`assisted-search-panel/spec.md:41`](../../../specs/assisted-search-panel/spec.md) | *«Changing the point of sale MUST clear the displayed results»* |
| [`assisted-search-panel/spec.md:596`](../../../specs/assisted-search-panel/spec.md) | *«Changing the selected point of sale MUST refresh the stock figures»* |

El código **limpia** ([`assisted.tsx:268-274`](../../../../frontend/src/pages/sales/assisted.tsx):
`setState({ kind: 'idle' })`), y el test de la tarea 12.6 de C40 —`should issue no assisted request when
the shop changes`— sólo comprobó el **segundo** `THEN` del escenario, nunca el primero. Es un **tercer
`SHALL` falso** en la misma spec, y toca este flujo de lleno: volver de «todas» a una tienda concreta
borra los resultados.

---

## Componentes Afectados

| Componente | Qué cambia |
|---|---|
| **`backend/src/JoiabagurPV.API`** | `Controllers/AiSearchController.cs` — la acción `Availability` acepta `Guid?` y sigue rechazando `Guid.Empty` |
| **`backend/src/JoiabagurPV.Application`** | `Interfaces/IAssistedSearchService.cs` y `Services/AssistedSearchService.cs` — `GetAvailability(Guid?)` con la rama del ámbito global en los **tres** interruptores · `DTOs/Ai/AiSearchAvailabilityResponse.cs` — `PointOfSaleId` a `Guid?` · `Configuration/` — el predicado `IsEnabledFor(this …, Guid?)` extraído para las tres clases de opciones |
| **`backend/src/JoiabagurPV.Tests`** | Casos nuevos de la sonda: ausencia → 200, `Guid.Empty` → 400, y que el predicado sin tienda coincide con el que la ruta aplica |
| **`frontend/src/pages/sales/assisted.tsx`** | Opción de ámbito global condicionada al administrador · los dos guards de búsqueda · el efecto de disponibilidad · la fijación de ruta y el enunciado del callejón sin salida |
| **`frontend/src/components/sales/search-route-toggle.tsx`** | Propiedad de indisponibilidad del lado semántico, sobre el `RouteOption` que ya la soporta |
| **`frontend/src/components/sales/ai-availability-badge.tsx`** | Variante de `switched_off` sin «en esta tienda» |
| **`frontend/src/types/ai-search.types.ts`** | `pointOfSaleId` deja de ser obligatorio en las dos peticiones del panel · `AiSearchAvailability.pointOfSaleId` admite nulo |
| **`frontend/src/services/ai-search.service.ts`** | `getAvailability` omite el parámetro en vez de enviarlo vacío |
| **`frontend/src/pages/sales/__tests__/assisted.test.tsx`** | Los siete casos nuevos |
| **`openspec/specs/`** | Deltas de `assisted-search-panel` (dos requisitos `MODIFIED`) y `ai-free-query-search` (uno `MODIFIED`) |
| **`compose.demo.yaml`** | `AiFreeQuerySearch__EnabledByDefault: "true"` |
| **`Documentos/`** | `epicas.md` (EP15), y `frontend/README.md` / `backend/README.md` en lo que toque a la sonda y al ámbito |

**Sin cambios:** `ai-service/` · `ai-service/openapi.json` · base de datos y migraciones ·
`FreeQuerySearchService` · `AiCallScope` · `assisted-search-result-query`/`row` · `terraform/` ·
`.github/workflows/`.

---

## Especificaciones Técnicas

### A · El requisito que falta y la corrección del que miente (esto primero, y es el núcleo)

Escribir el código sin el requisito **reproduce la condición que dejó el hueco**: si nadie lo exige, la
próxima vez vuelve a faltar.

En `assisted-search-panel`, el requisito de ámbito deja de decir *«The panel SHALL send a concrete point
of sale on every search»* y pasa a exigir **tres cosas, cada una con escenario fallable**:

1. El panel **ofrece al administrador** una manera explícita de buscar en todas las tiendas,
   distinguible de haber elegido una. → falla si desaparece la opción.
2. El panel **no la ofrece al operario**, porque el ámbito no informa existencias y no puede cerrar una
   venta — **y la ruta sigue autorizándola**, de modo que la estrechez es de la pantalla y no del
   backend. → falla si se enseña por error, y **protege el backend de un endurecimiento «de limpieza»**.
3. Con ese ámbito seleccionado, la **ruta rápida queda deshabilitada con su motivo** y la asistida
   **no**. → es el escenario que de verdad cierra el change.

El requisito de disponibilidad del panel, que hoy la enuncia *«for the selected point of sale»*, pasa a
cubrir también el ámbito sin tienda. Y se retira la cláusula falsa *«Changing the selected point of sale
MUST refresh the stock figures»* del §1.7.

En `ai-free-query-search`, el requisito de disponibilidad —que hoy SHALL informar *«for one point of
sale»*— pasa a **aceptar la ausencia** y a reportar el ámbito por defecto. **Su requisito de
autorización y su escenario *«An operator may search across every point of sale»* no se tocan: siguen
siendo verdad.**

> **Regla del validador que cuesta una sesión:** la descripción que sigue a `### Requirement:` se valida
> leyendo **sólo su primera línea física**. Va en **una línea larga**, sin ajustar a 90 columnas.

### B · Backend · la sonda de disponibilidad

| Elemento | Antes | Después |
|---|---|---|
| `GET /api/ai/search/availability` | `[FromQuery] Guid pointOfSaleId` | `[FromQuery] Guid? pointOfSaleId` |
| Ausente | **400** «El punto de venta es obligatorio.» | **200**, ámbito por defecto |
| `Guid.Empty` | 400 | **400**, con el texto de la consulta libre: «El punto de venta no es válido. Omítelo para buscar en todas las tiendas.» |
| `IAssistedSearchService.GetAvailability` | `(Guid)` | `(Guid?)` |
| `AiSearchAvailabilityResponse.PointOfSaleId` | `Guid` | `Guid?` — **nulo** en ámbito global, **nunca `Guid.Empty`** |
| Rol requerido | autenticado | autenticado (sin cambio; la sonda informa de interruptores y no revela nada) |
| `[DisableRateLimiting]` | sí | sí (sin cambio) |

**El predicado se extrae y se escribe una sola vez** — un método de extensión
`IsEnabledFor(this AiFreeQuerySearchOptions \| AiSalesAssistOptions \| AiSearchOptions, Guid?)` que
resuelve a `EnabledByDefault` cuando no hay tienda. **La sonda tiene que calcular exactamente el mismo
predicado que la ruta aplica**; si divergen se recrea la avería original de C40 — la pantalla diciendo
una cosa y la ruta haciendo otra.

`SemanticSearchAvailable` **se sigue reportando con su predicado normal**. La sonda describe
interruptores; el panel describe alcanzabilidad. Devolver `false` ahí afirmaría que el interruptor está
apagado, que es otra cosa y es falso.

### C · Frontend · el control y el toggle

- **La opción**, condicionada a `isAdmin` (`user?.role === 'Administrator'`), la **primera** de la lista
  y visualmente separada de las tiendas. El selector ya se renderiza siempre para ese rol, así que **no
  hay que tocar la regla de ocultación** ni el requisito *«A single assignment needs no choice»*.
- **El centinela vive sólo en el componente** y se traduce a **ausencia** del campo antes de la
  petición. La página ya usa el patrón para la categoría
  ([`assisted.tsx:456`](../../../../frontend/src/pages/sales/assisted.tsx)):
  `value={category || 'all'}` con `onValueChange={(v) => setCategory(v === 'all' ? '' : v)}`.
- **Los dos guards relajados**, para que el ámbito sin tienda sea un estado válido de la pantalla y no
  un formulario incompleto.
- **El efecto de disponibilidad consulta la sonda también sin tienda**, en vez de ponerse en blanco y
  dejar la insignia colgada.
- **La ruta se fija a la asistida** y la rápida se deshabilita con motivo **de ámbito** — *«trabaja
  sobre una tienda concreta»*, nunca *«está desactivada»*.
- **El callejón sin salida se enuncia al llegar a él**: si el ámbito global está seleccionado y la
  respuesta asistida está apagada, una línea bajo el selector dice que el ámbito la necesita y que está
  desactivada. **No se pre-deshabilita la opción**, porque eso exigiría leer la sonda dos veces —el
  ámbito actual y el global— y seleccionar el ámbito no cuesta ninguna petición.

### D · La restricción que no se puede violar

**El centinela no sale al cable.** `FreeQuerySearchRequest.PointOfSaleId` es `Guid?` y **un `Guid.Empty`
viajando sería el comodín por accidente que C40 dedicó un grupo entero a cerrar.** La propiedad que hace
seguro este ámbito es que **la ausencia de `pos_id` hace que el prefiltro no se aplique**, no que case
con todo. Ver `test_a_blank_pos_claim_is_never_read_as_its_absence` y la regla que lo gobierna:
*ausencia es que la clave no esté en el payload; cualquier otra cosa es un valor, y un valor tiene que
ser usable*.

### E · Despliegue — prerrequisito, no mejora

`compose.demo.yaml` gana `AiFreeQuerySearch__EnabledByDefault: "true"` con su comentario de clase, junto
a los otros dos. **Con la decisión de fijar la ruta generativa, la función entera cuelga de ese
interruptor**: sin él el administrador se come el callejón sin salida en el primer clic y la
comprobación manual de la DoD no se puede hacer.

### F · Tests

**Los existentes no cubrían esto, y no era descuido**: los de la fila pasan `pointOfSaleName` —y el
`hasStock` nulo— **directamente al componente**
([`assisted-search-result-row.test.tsx:167`](../../../../frontend/src/components/sales/__tests__/assisted-search-result-row.test.tsx)),
así que nunca ejercitaron el camino del panel. Es la misma lección del hallazgo central en forma de test:
el componente estaba probado, el camino hasta él no.

Los nuevos van **a nivel de página**, en `frontend/src/pages/sales/__tests__/assisted.test.tsx`
(nomenclatura `should [comportamiento] when [condición]`):

- que la opción de ámbito global **exista y sea seleccionable para el administrador**;
- que **no exista para el operario** — es el escenario que protege la estrechez;
- que seleccionarla **no emita ninguna petición de búsqueda** — regla del panel: sólo se busca cuando el
  operario lo pide;
- que **la ruta rápida quede deshabilitada con su motivo**, y que ese motivo no sea el del interruptor;
- **que el toggle de respuesta asistida siga habilitado** con el ámbito global — es el §1.2, y es el
  test que de verdad cierra este ticket;
- que la fila deje de nombrar tienda y deshabilite el botón de ficha;
- que **no viaje `Guid.Empty`** al backend en ninguna de las dos peticiones;
- que el callejón sin salida **se enuncie** cuando la respuesta asistida está apagada.

Y del lado .NET (`Método_Escenario_ResultadoEsperado`): **sin punto de venta la sonda devuelve 200 con
el ámbito por defecto en vez de 400**; con `Guid.Empty` devuelve 400; y el predicado sin tienda coincide
con el que `FreeQuerySearchService` aplica.

**Cero tests existentes invertidos.** Es consecuencia directa de limitar el control al administrador.

### Fuera de este ticket

- **Extender `POST /api/ai/search` —la ruta rápida— al ámbito global.** Alternativa considerada y
  descartada: arrastra el DTO, el validador, `AuthoriseAsync`, el ámbito, la hidratación y el registro de
  `AssistedSearchService` —el servicio más transitado del árbol— **y la agrupación que le falta a
  `SearchLexicalAsync`** (§1.5), sin la cual la ruta degradada con ámbito global es un **HTTP 500**. Con
  audiencia de administración la objeción económica a fijar la ruta cara se cae. **Se anota como tarea
  diferida con su motivo, junto con la mina.**
- **No endurece la autorización a sólo administrador.** La spec la abre a operarios y administradores con
  su razón escrita, y la frontera que se protege es no poder **nombrar** una tienda no asignada, no el
  ensanchado. Tumbar `FreeQuery_ForOperatorWithAllPointsOfSale_IsServed` sería más trabajo y tiraría
  trabajo correcto.
- **No toca el endpoint de búsqueda de la consulta libre, sus DTO ni su hidratación.** Están hechos y
  comprobados.
- **No reabre** la decisión de que la cantidad viaje **nula** y no cero. Es correcta y es la razón de que
  el ámbito exista como clase aparte.
- **No añade telemetría** para el ámbito global: sigue siendo la tarea diferida de C40, con su motivo
  (exigiría migración de EF Core y la spec prohíbe el marcador de posición). **El recorte al
  administrador la vuelve marginal**, lo que refuerza el motivo para diferirla.
- **No desagrega existencias por tienda**, que es lo que de verdad responde «¿en qué tienda está?». Otro
  change: mueve el DTO de resultado, la hidratación y la fila.
- **No añade un requisito transversal de alcanzabilidad.** No produciría ningún escenario fallable — el
  mismo modo de fallo un nivel más arriba. La lección va a la documentación de verificación.
- **No toca la fila de resultado**, que ya tiene sus tres estados y decide por los datos.
- **No es C41.** C41 es la frescura de `ai.pos_projection` y no comparte ni un fichero con esto.

---

## Arquitectura

### Decisión 1 · ¿Quién ve el control? → **sólo el administrador**

El ámbito global **no informa existencias**: cantidad nula, sin tienda que nombrar, botón de ficha
deshabilitado, sin telemetría. Responde *«esta pieza existe en el catálogo»*, **no** *«está en la tienda
del Puerto»*. Así que limitar el control al administrador no declina servir un caso de uso: **declina
ofrecer una herramienta que no responde la pregunta que su nombre sugiere.** Razón escrita para la spec:

> *El ámbito global no informa existencias, así que no puede cerrar una venta: es una herramienta de
> exploración del catálogo, y explorar la cadena entera es trabajo de administración, no de un
> mostrador.*

**`isAdmin` en el cliente no es una frontera de seguridad.** El backend sigue sirviendo el ámbito a un
operario que construya la petición, y eso está bien: la frontera real es no poder **nombrar** una tienda
ajena. Es una decisión de producto en la interfaz, **y el requisito tiene que decirlo** o el siguiente
lector endurecerá el backend por simetría.

*Alternativas descartadas:* abrirlo a operarios —obligaría a mostrar siempre el selector, a modificar el
requisito *«A single assignment needs no choice»* y a invertir su test, y entregaría al mostrador una
herramienta que no responde su pregunta—; y un control aparte tipo `[Esta tienda ▾] [Todas]` —
conceptualmente más limpio, porque «todas las tiendas» no es una tienda sino otra pregunta, pero
innecesario una vez el selector ya se muestra siempre a ese rol.

### Decisión 2 · ¿Qué hace el toggle de ruta? → **el ámbito global fija la generativa**

```
                    │ route: semantic (barata) │ route: assisted (generativa)
 ───────────────────┼──────────────────────────┼─────────────────────────────
  ámbito: 1 tienda  │  ✅ sin cambios          │  ✅ sin cambios
  ámbito: todas     │  🚫 deshabilitada        │  ✅ funciona
  (sólo admin)      │     CON MOTIVO ESCRITO   │     (si el interruptor está on)
```

*Alternativa descartada — extender la ruta rápida:* es la opción «coherente», y el repositorio está más
listo de lo que parece (`HydrateAsync` y `SearchLexicalAsync` ya aceptan `Guid?`, `AiCallScope` ya tiene
la tercera clase, `deps.py` ya acepta el token sin `pos_id`). Se descarta porque toca
`AssistedSearchService` entero **y** obliga a arreglar la mina del §1.5 antes de que nadie pueda usarlo.
Con la audiencia reducida a administración, la objeción de coste que hacía preferible extenderla —atar
el ámbito más exploratorio a la ruta de 4× presupuesto y 3× cuota— se cae: son consultas ocasionales, no
cien mostradores en ráfagas.

*Alternativa descartada — no fijar nada y dejar que el 400 hable:* es el estado que este change viene a
retirar.

### Decisión 3 · El callejón sin salida → **se enuncia al llegar**

Con el interruptor de la consulta libre apagado, el ámbito global deja las **dos** opciones del toggle
deshabilitadas. Pre-deshabilitar la propia opción «Todas las tiendas» sería más pulcro pero exigiría
**leer la sonda dos veces** —el ámbito seleccionado y el global—, porque hoy sólo se lee la del
seleccionado. Se enuncia en su lugar: seleccionar el ámbito no emite ninguna petición, así que no se
desperdicia nada, y con el prerrequisito del §E es un estado raro y no el normal. Es el
*safe-completion* de S16: decir qué no se puede **y qué haría falta para poder**.

### Patrones y decisiones previas aplicables

- **Ausencia ≠ centinela**, de C40: la ausencia hace que el prefiltro no se aplique; un valor en blanco
  es un valor y tiene que ser usable. Gobierna el §D y el §B.
- **Un interruptor por función**, de C16/C34/C40: tres rollout gates independientes, con su límite y su
  presupuesto. Gobierna el §B y el §E.
- **La pantalla no presenta como encendido lo que está apagado**, que es la lección que ordenó C40
  entero. Gobierna la Decisión 3.
- **Service Layer + Repository + DI**, sin novedad; el predicado extraído es un método de extensión sobre
  las clases de `Configuration/`, no un servicio nuevo.

### Breaking changes

- **Contrato REST .NET ↔ SPA:** `AiSearchAvailabilityResponse.PointOfSaleId` pasa a anulable. Los dos
  lados cambian en el mismo change; el único consumidor es el panel.
- **`ai-service/openapi.json`: sin diff.** `openapi.json` es la frontera con `jbg-ai` y no se mueve.
- **Base de datos: sin migración.** Ninguna entidad, columna ni índice cambia.

---

## Criterios de Aceptación

Los once escenarios en formato Dado/Cuando/Entonces están en la historia
[HU-AIENG-040-FIX](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md#criterios-de-aceptación).
Resumen de los que gobiernan el cierre:

1. El administrador ve la opción de ámbito global; el operario **no**, y la ruta sigue sirviéndosela.
2. Seleccionar el ámbito **no emite petición**; cambiar de ámbito limpia resultados.
3. La ruta rápida queda deshabilitada **con motivo de ámbito**, no de interruptor.
4. **El toggle de respuesta asistida sigue habilitado** con el ámbito global, y la insignia sale de
   «Comprobando disponibilidad…». ← *el que cierra el ticket*
5. Con la respuesta asistida apagada, el callejón sin salida **se enuncia**.
6. La sonda responde **200** sin punto de venta y **400** con punto de venta en blanco.
7. Ningún identificador en blanco viaja en ninguna petición del panel.
8. La fila no muestra cero, no nombra tienda, deshabilita la ficha y no duplica productos.
9. El interruptor de la consulta libre está activado en el compose de la demo.
10. Fuera de alcance explícito: ruta rápida sin ámbito global, autorización sin endurecer, sin migración,
    sin diff en `openapi.json`, sin diff en la fila.

---

## Definición de Hecho (DoD)

- [ ] Código implementado según las capas de [`Documentos/modelo-c4.md`](../../../../Documentos/modelo-c4.md)
      y las convenciones de [`openspec/project.md`](../../../project.md)
- [ ] **Backend:** xUnit + Moq + FluentAssertions + Bogus, nomenclatura
      `Método_Escenario_ResultadoEsperado`, cobertura ≥70 % sobre el código nuevo
- [ ] **Frontend:** Vitest + React Testing Library + MSW, nomenclatura
      `should [comportamiento] when [condición]`, queries accesibles, cobertura ≥70 % sobre el código
      nuevo
- [ ] **`ai-service`: sin cambios**, y `openapi.json` **sin diff** — comprobado, no supuesto
- [ ] **Sin migración de EF Core**, porque el modelo de datos no se mueve
- [ ] Deltas de spec en `openspec/changes/c40-fix-all-shops-scope-unreachable/specs/` y
      **`openspec validate --all --strict` en `0 failed`** — la forma de un solo change **no es la
      puerta**
- [ ] **Las tres specs afectadas dejan de afirmar algo falso**, comprobado leyendo el requisito y no sólo
      validando su forma
- [ ] Las suites **vienen rojas de fábrica**: comparar **nombres**, no recuentos, contra la línea base
      del propio commit. Frontend ~113-114 de 729 en 14 ficheros; backend ~50. **Cero nombres nuevos en
      rojo en el área propia.** Detalle en [`CLAUDE.md`](../../../../CLAUDE.md)
- [ ] `dotnet build` y `npm run build` en verde, **y `tsc --noEmit` filtrado a los ficheros propios sin
      errores nuevos** — obligatorio porque el change mueve un tipo, y C40 se comió un commit entero con
      `npm run build` verde sobre un error de tipos
- [ ] **Comprobación manual en el entorno levantado**, por la interfaz y con los dos roles — es la única
      puerta que detecta el defecto que este change corrige
- [ ] Documentación actualizada: [`Documentos/epicas.md`](../../../../Documentos/epicas.md) (EP15),
      `frontend/README.md`, `backend/README.md`, y las dos tareas diferidas en
      [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) con su motivo
- [ ] Compatibilidad hacia atrás verificada en el contrato REST; el único consumidor es el panel
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] UI en español (es-ES) y moneda EUR (€)

---

## Requisitos No Funcionales

- **Seguridad.** El control es una decisión de **interfaz** y no de autorización: el backend sigue
  sirviendo el ámbito a operarios y administradores, y la frontera real —no poder **nombrar** una tienda
  no asignada— no se toca. La sonda sigue exigiendo autenticación y no revela nada nuevo: informa de
  interruptores, no de datos. RBAC Admin/Operador sin cambios en el backend.
- **Rendimiento y coste.** La sonda mantiene `[DisableRateLimiting]`, no llama al modelo y no consume
  cuota, que es lo que la hace segura de leer en cada cambio de ámbito. **No se añade una segunda
  lectura de la sonda** — es el motivo de la Decisión 3. El ámbito global se sirve por la ruta de 10 s de
  presupuesto y 10 peticiones/minuto, con audiencia de administración y uso ocasional. Sin paginación
  nueva: el tamaño de página del panel no cambia.
- **Observabilidad.** Logging estructurado con Serilog sin campos nuevos. **Limitación declarada y no
  disimulada:** una búsqueda de ámbito global **no se registra** en `ProductSearchEvent`, así que su uso
  no es medible; el motivo (columna obligatoria e indexada, migración de EF Core, y la spec prohíbe el
  marcador de posición) está en `DEFERRED_TASKS.md` y el embudo ya lo dice en pantalla.
- **Integridad de datos.** Ninguna escritura. La regla que se protege es semántica: **nulo y cero son
  respuestas distintas** y un cero sin tienda sería una afirmación falsa sobre una pieza que puede estar
  en la tienda de al lado.
- **Accesibilidad y copia.** Motivos marcados por texto y no sólo por color, como la etiqueta de origen
  de la fila: el mostrador no es sitio para fiarse de un punto verde. Ningún texto puede afirmar «en esta
  tienda» cuando no hay tienda de la que hablar.

---

## Preguntas Abiertas → Decisiones (cerradas antes de artefactos OpenSpec)

**Las seis quedan cerradas.** Dos las cerró la exploración del 25 de septiembre y cuatro la del 26, y se
registran cerradas para que el `design.md` no las reabra.

| # | Pregunta | **Resuelta** |
|---|---|---|
| 1 | ¿El control se ofrece a operarios **y** administradores, o sólo a administradores? | **Sólo al administrador** *(26 sep, revisa la respuesta del 25)*. El ámbito no informa existencias, así que no cierra una venta: es exploración de catálogo, trabajo de administración. **La ruta del backend se queda abierta a operarios** y el requisito lo dice, para que nadie la endurezca por simetría |
| 2 | ¿Qué dice la insignia de disponibilidad sin tienda? | **Lo que responda la sonda**, una vez acepte la ausencia: el ámbito por defecto, vía `options.EnabledByDefault`. Es la lectura estrecha y ya está razonada en el código de C40 |
| 3 | ¿Es el ámbito global el valor **por defecto** del selector? | **No.** El efecto de carga sigue fijando la primera tienda activa, también para el administrador. Cambiarlo movería el coste y el comportamiento de todo el panel |
| 4 | ¿Cómo se llama la opción en castellano? | **«Todas las tiendas»**, coincidiendo con el reporte y con el lenguaje de la spec, **más una línea de aviso al seleccionarla** que diga que se verá catálogo completo y que para leer existencias hay que elegir una tienda. Con audiencia de administración el reparo —que la etiqueta promete existencias— se debilita, y el aviso lo cierra |
| 5 | ¿Debe la spec del panel ganar una regla **transversal** sobre alcanzabilidad? | **No.** *«Todo estado especificado DEBE ser alcanzable»* no produce ningún escenario que un runner pueda fallar: sería un requisito que valida en verde y no cambia nada — el mismo modo de fallo un nivel más arriba. En su lugar, **tres escenarios fallables** en el requisito concreto, y la lección a la documentación de verificación |
| 6 | ¿La sonda sin tienda responde `200` con qué forma exacta? | **`PointOfSaleId` a `Guid?`, nulo en ámbito global**, sin discriminante nuevo — se consideró `scope: 'point_of_sale' \| 'all_points_of_sale'`, más autodescriptivo, y se descartó por coherencia con `FreeQuerySearchResponse.PointOfSaleId`, que ya es `Guid?`. Y **`Guid.Empty` sigue siendo 400**, con el texto de la consulta libre |

**Nada queda abierto para el `design.md`.** Lo que sí tiene que hacer es **dejar escritas las tres
alternativas descartadas de la sección Arquitectura con su motivo**, porque las dos primeras contradicen
la versión original de este ticket.

---

## Prioridad / Estimación / Tags

- **Prioridad:** Media-alta. No desbloquea ninguna arista del grafo de changes, pero **una spec viva
  miente ahora mismo** y cada change archivado encima consolida esa mentira. C38 viene detrás sobre la
  misma zona.
- **Estimación:** _Pendiente_ (la HU no estima en el primer borrador). **Complejidad 2 de 5**: sin
  algoritmo, sin migración, sin pantalla nueva, sin movimiento de contrato con `jbg-ai`. Lo que hay es
  una decisión de diseño con tres alternativas reales, tres requisitos de spec que hay que **corregir**
  en vez de añadir, un predicado que debe escribirse una sola vez y una cadena de copia que no puede
  mentir.
- **Impacto de negocio:** 3 de 5 · **Urgencia:** 4 de 5.
- **Tags:** `fix` · `EP15` · `assisted-search-panel` · `ai-free-query-search` · `frontend` · `backend`
  · `spec-correction` · `reachability` · `feature-flag` · `no-migration` · `no-openapi-change`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-040-FIX](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md)
- **Change:** [`c40-fix-all-shops-scope-unreachable`](./) · [proposal.md](./proposal.md)
- **Change que origina el defecto:** [`2026-09-25-add-frontend-free-query-panel`](../../archive/2026-09-25-add-frontend-free-query-panel/)
  · su [ticket](../../archive/2026-09-25-add-frontend-free-query-panel/ticket.md) · su
  [informe §12](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md)
  · [HU-AIENG-040](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040.md)
- **Specs vivas:** [`assisted-search-panel`](../../../specs/assisted-search-panel/spec.md) ·
  [`ai-free-query-search`](../../../specs/ai-free-query-search/spec.md)
- **Precedente de ticket correctivo:** [T-AIENG-FIX1](../../archive/2026-09-05-fix-enrichment-vocabulary-gaps/ticket.md),
  que también nace de una spec bien formada y falsa
- **Procedimientos:** [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)
  · [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Contexto:** [`openspec/project.md`](../../../project.md) ·
  [`Documentos/arquitectura.md`](../../../../Documentos/arquitectura.md) ·
  [`Documentos/modelo-c4.md`](../../../../Documentos/modelo-c4.md) ·
  [`Documentos/epicas.md`](../../../../Documentos/epicas.md) (EP15)
- **Pruebas:** [testing-backend.md](../../../../Documentos/testing-backend.md) ·
  [testing-frontend.md](../../../../Documentos/testing-frontend.md) · [`CLAUDE.md`](../../../../CLAUDE.md)
- **Tareas diferidas:** [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md)

---

## Historial de Cambios

| Fecha | Qué cambió |
|---|---|
| **2026-09-25** | Apertura del ticket con la evidencia de las pruebas manuales: el ámbito global es inalcanzable desde el selector. Se declaraba que **no tocaba el backend** |
| **2026-09-25** *(más tarde)* | Primera exploración verificada. **Corrige la afirmación anterior:** el fix toca `AiSearchController.Availability`, y son **dos piezas**. Cierra las preguntas 1 y 2 |
| **2026-09-26** | Segunda exploración, contra el código de las tres capas. **Corrige de nuevo: son TRES piezas** — la ruta rápida rechaza el ámbito global con un 400 de validación (§1.3), que ninguna pasada anterior había mirado. Tres hallazgos más: el interruptor de la demo ausente (§1.4), la mina de `SearchLexicalAsync` (§1.5) y el tercer `SHALL` falso de la spec (§1.7). **Y se revisa la respuesta a la pregunta 1: el control pasa a ser sólo del administrador**, lo que disuelve la modificación del requisito de ocultación del selector y deja cero tests invertidos. Se cierran las preguntas 3, 4, 5 y 6. Se añaden las secciones que pedía el procedimiento: Componentes Afectados, Especificaciones Técnicas, Arquitectura con las alternativas descartadas, Criterios de Aceptación, DoD, Requisitos No Funcionales, Prioridad, Enlaces e Historial |
