## Context

C40 construyó el ámbito «todas las tiendas» entero y **nadie puede alcanzarlo**. El grupo 12 de aquel
change entregó la tercera clase de `AiCallScope` sin centinela ni constructor público, el tercer perfil de
*claims* en `deps.py`, la autorización abierta a operarios y administradores con sus dos tests, los DTO
anulables, la hidratación agrupada por producto y la fila de resultado con sus tres estados. El panel no
ofrece la opción, el efecto de carga fija la primera tienda activa, la búsqueda no se dispara sin tienda y
el botón *Buscar* está deshabilitado. **Ese tramo no se ejecuta en la aplicación real ni una vez.**

Y no falló nada, que es el hallazgo que ordena este diseño. Los 136 escenarios de C40 salieron verdes
porque los tres del panel están condicionados con *«WHEN the search is scoped to every point of sale»*:
describen qué hace la pantalla **estando** en ese estado y ninguno exige que ofrezca la forma de entrar en
él. Peor: `assisted-search-panel/spec.md:88` afirma *«The panel SHALL send a concrete point of sale on
every search»*, que dejó de ser cierto con C40. **La spec viva no calla — contradice lo que el sistema
hace**, y `openspec validate --all --strict` seguiría en verde sobre ella porque valida estructura y no
verdad.

### Estado del árbol, verificado

Lo que hace posible que este change sea pequeño es que **la capa de repositorio ya es anulable de punta a
punta**. Lo que lo hace no trivial es que la ruta por defecto del panel no lo es.

| Pieza | Acepta la ausencia de tienda |
|---|---|
| `deps.py` — tercer perfil de *claims*, recuperación y assist | ✅ |
| `AiCallScope.ForAllPointsOfSale` | ✅ |
| `IAssistedSearchRepository.HydrateAsync(ids, Guid?, ct)` | ✅ **y agrupa por producto** |
| `IAssistedSearchRepository.SearchLexicalAsync(terms, Guid?, …)` | ⚠️ firma sí, **agrupación no** |
| `POST /api/ai/search/assisted` → `FreeQuerySearchRequest.PointOfSaleId` `Guid?` | ✅ distingue ausencia de `Guid.Empty` |
| `POST /api/ai/search` → `AssistedSearchRequest.PointOfSaleId` `Guid` + `.NotEmpty()` | ❌ **400** |
| `GET /api/ai/search/availability` → `[FromQuery] Guid` | ❌ **400** |
| `assisted.tsx` — selector, guards, efecto de disponibilidad | ❌ |

### Restricciones que el diseño hereda y no negocia

- **Ausencia ≠ centinela.** La propiedad que hace seguro este ámbito es que la ausencia de `pos_id` hace
  que el prefiltro **no se aplique**, no que case con todo. Un `Guid.Empty` viajando sería el comodín por
  accidente al que C40 dedicó un grupo entero.
- **Nulo ≠ cero.** Sin tienda no hay existencias que contar, y un cero sería una afirmación falsa sobre
  una pieza que puede estar en la tienda de al lado.
- **Una búsqueda sólo se emite cuando el operario la pide.** Cambiar de ámbito no puede disparar ninguna.
- **La sonda no llama al modelo ni consume cuota**, que es lo que la hace segura de leer en cada cambio.

## Goals / Non-Goals

**Goals:**

- Que el ámbito «todas las tiendas» sea **alcanzable** desde el panel, por el administrador, y que la
  spec lo **exija** con escenarios que puedan fallar.
- Que la spec viva deje de afirmar tres cosas falsas: que el panel envía siempre una tienda concreta, que
  la disponibilidad se enuncia sólo «para la tienda seleccionada», y que cambiar de tienda refresca las
  existencias.
- Que la sonda de disponibilidad **acepte la ausencia** y calcule **el mismo predicado que la ruta
  aplica**, para que la pantalla no pueda volver a decir algo distinto de lo que el backend hace.
- Que ningún camino del panel deje al operario delante de una capacidad apagada **sin motivo que leer**.
- Que el ámbito sea **utilizable de extremo a extremo en la demo**, no sólo en teoría.

**Non-Goals:**

- **Extender `POST /api/ai/search` —la ruta rápida— al ámbito global.** Decisión 2, con su alternativa
  descartada y su tarea diferida.
- **Endurecer la autorización a sólo administrador.** La ruta sigue abierta a operarios; la estrechez es
  de la pantalla y el requisito lo dice.
- **Desagregar existencias por tienda**, que es lo que de verdad responde «¿en qué tienda está?». Otro
  change.
- **Telemetría del ámbito global.** Tarea diferida de C40 con su motivo; el recorte al administrador la
  vuelve marginal.
- **Un requisito transversal de alcanzabilidad.** Decisión 6.
- Tocar `ai-service/`, `openapi.json`, la base de datos, `FreeQuerySearchService`, `AiCallScope` o la fila
  de resultado.

## Decisions

### D1 · El control se ofrece **sólo al administrador**

El ámbito global **no informa existencias**: cantidad nula, sin tienda que nombrar, botón de ficha
deshabilitado, sin registro en telemetría. Responde *«esta pieza existe en el catálogo»* y **no** *«está
en la tienda del Puerto»*. El dependiente que pregunta «¿lo tenemos en otra tienda?» no obtiene respuesta
a esa pregunta ni con el ámbito abierto a él: obtiene un catálogo sin existencias y un callejón sin salida.

Razón que va escrita en la spec, porque tiene que seguir leyéndose verdadera dentro de seis meses:

> *El ámbito global no informa existencias, así que no puede cerrar una venta: es una herramienta de
> exploración del catálogo, y explorar la cadena entera es trabajo de administración, no de un mostrador.*

**`isAdmin` en el cliente no es una frontera de seguridad.** El backend sigue sirviendo el ámbito a un
operario que construya la petición, y eso es correcto: la frontera real es no poder **nombrar** una tienda
no asignada. Es una decisión de producto en la interfaz, **y el requisito debe decirlo explícitamente** o
el siguiente lector endurecerá el backend por simetría.

| Alternativa | Por qué se descarta |
|---|---|
| **Abrirlo a operarios** | Obliga a mostrar siempre el selector —hoy se oculta con una sola asignación—, a modificar el requisito *«A single assignment needs no choice»* y a **invertir su test**. Y entrega al mostrador una herramienta que no responde su pregunta |
| **Control aparte `[Esta tienda ▾] [Todas]`** | Conceptualmente más limpio, porque «todas las tiendas» no es una tienda sino otra pregunta. Innecesario: con D1 el selector ya se renderiza siempre para ese rol, así que un control extra en una pantalla cargada no compra nada |

**Consecuencia medible: cero tests existentes invertidos.**

### D2 · El ámbito global **fija la ruta generativa**, y la rápida se deshabilita con motivo propio

```
                    │ route: semantic (barata)  │ route: assisted (generativa)
 ───────────────────┼───────────────────────────┼──────────────────────────────
  ámbito: 1 tienda  │  ✅ sin cambios           │  ✅ sin cambios
  ámbito: todas     │  🚫 deshabilitada         │  ✅ funciona
  (sólo admin)      │     CON MOTIVO DE ÁMBITO  │     (si el interruptor está on)
```

El motivo tiene que ser **de ámbito** —«la búsqueda rápida trabaja sobre una tienda concreta»— y **nunca**
de interruptor. Decir «la búsqueda semántica está desactivada» sería falso, y es exactamente la clase de
afirmación que este change viene a retirar.

| Alternativa | Por qué se descarta |
|---|---|
| **Extender la ruta rápida al ámbito global** | Es la opción «coherente» y el árbol está más listo de lo que parece. Pero arrastra `AssistedSearchRequest`, su validador, `AuthoriseAsync`, `ScopeOf`, la hidratación, `RecordAsync` y `AssistedSearchResponse` de **`AssistedSearchService`, el servicio más transitado y más probado del árbol** — y obliga a arreglar la agrupación de `SearchLexicalAsync` **antes** de que nadie pueda usarlo, porque su rama nula es un **HTTP 500** (ver R1). Con la audiencia de D1 la objeción económica que la hacía preferible —atar el ámbito más exploratorio a la ruta de 4× presupuesto y 3× cuota— se cae: son consultas ocasionales de administración, no cien mostradores en ráfagas. **Queda como tarea diferida con su motivo** |
| **No fijar nada y dejar que el 400 hable** | Es el estado que este change viene a retirar: la pantalla ofreciendo un control y contradiciéndose al primer clic |

### D3 · El callejón sin salida **se enuncia al llegar**, no se pre-deshabilita la opción

Con el interruptor de la consulta libre apagado, el ámbito global deja las **dos** opciones del toggle
deshabilitadas: la rápida por ámbito, la asistida por interruptor. Un ámbito que se puede elegir y desde
el que no se puede buscar.

Pre-deshabilitar la propia opción «Todas las tiendas» sería más pulcro, pero exigiría **leer la sonda dos
veces** —el ámbito seleccionado **y** el global—, porque hoy sólo se lee la del seleccionado. Se enuncia en
su lugar: seleccionar el ámbito no emite ninguna petición, así que no se desperdicia nada, y con D5 es un
estado raro y no el normal.

Es el *safe-completion* de S16: decir **qué no se puede y qué haría falta para poder**, en vez de callar.

| Alternativa | Por qué se descarta |
|---|---|
| **Pre-deshabilitar la opción** | Una segunda lectura de la sonda en cada carga del panel, por un estado que D5 convierte en excepcional |
| **No ofrecer la opción cuando la asistida está apagada** | Invisible, que es el defecto que este change corrige |

### D4 · La sonda describe **interruptores**; el panel describe **alcanzabilidad**

`GetAvailability` pasa a `Guid?` y sigue reportando `SemanticSearchAvailable` con su predicado normal.
Devolver `false` ahí para el ámbito global afirmaría que el interruptor semántico está apagado, que es otra
cosa y es mentira. Que la ruta rápida no sea alcanzable en ese ámbito **lo sabe el panel**, y lo dice con
su propia copia.

**Y el predicado se extrae y se escribe una sola vez.** Ésta es la decisión con más consecuencia técnica
del change:

```
Hoy:   AssistedSearchService.GetAvailability(Guid pos)
         ├── _freeQueryOptions.IsEnabledFor(pos)   ─┐
         ├── _assistOptions.IsEnabledFor(pos)       ├─ tres llamadas a Guid
         └── _options.IsEnabledFor(pos)            ─┘

       FreeQuerySearchService.IsEnabled(options, Guid? pos)
         └── pos is { } named ? IsEnabledFor(named) : EnabledByDefault   ← el predicado real

Después: IsEnabledForScope(this <opciones>, Guid?)  —— un método de extensión por clase,
         consumido por la sonda Y por la ruta, de modo que **la regla del nulo** no
         pueda divergir.
```

> **Corregido en la verificación independiente (2026-09-26).** Lo que el predicado extraído garantiza es
> que **la resolución de la ausencia** —nulo → `EnabledByDefault`— es la misma a los dos lados. **No**
> garantiza que el veredicto de la sonda coincida con el de la ruta, porque la sonda devuelve la
> *conjunción* del interruptor de la consulta libre **y** el de la ficha de venta, y
> `FreeQuerySearchService` no lee el segundo en ningún punto. Medido: con
> `AiFreeQuerySearch__EnabledByDefault=true` y `AiSalesAssist__EnabledByDefault=false` la sonda responde
> `switched_off` para un ámbito que la ruta sirve con prosa generada. Ver R4 y `DEFERRED_TASKS.md`.

Si sonda y ruta calculan predicados distintos se recrea **la avería original de C40**: la pantalla
diciendo una cosa y el backend haciendo otra. El predicado sin tienda es `EnabledByDefault`, la lectura
estrecha, ya razonada en el código de C40:

> *«Con ninguna tienda nombrada no hay entrada por tienda que consultar, así que gobierna el valor por
> defecto. Ésa es la lectura estrecha y la segura: un despliegue que habilita la función tienda a tienda
> no la ha habilitado para “todas ellas”.»*

Forma de la respuesta: `AiSearchAvailabilityResponse.PointOfSaleId` pasa a `Guid?`, **nulo** en ámbito
global y **nunca `Guid.Empty`**. Y `Guid.Empty` en la petición sigue siendo **400**, con el mismo texto que
ya usa la ruta de consulta libre.

| Alternativa | Por qué se descarta |
|---|---|
| **Discriminante explícito `scope: 'point_of_sale' \| 'all_points_of_sale'`** | Más autodescriptivo —un lector del JSON no infiere el significado de una ausencia— y es lo que `AiCallScopeKind` ya hace por dentro. Se descarta por coherencia: `FreeQuerySearchResponse.PointOfSaleId` ya es `Guid?`, y añadir una forma nueva al lado de una existente cuesta más de lo que aclara |
| **Escribir la rama nula tres veces en `GetAvailability`** | Tres sitios donde el predicado puede derivar del que la ruta aplica |
| **Tratar `Guid.Empty` como ausencia** | Convertiría un bug de cliente en una búsqueda más ancha. Es la regla de `test_a_blank_pos_claim_is_never_read_as_its_absence` |

### D5 · El interruptor de la demo es **prerrequisito**, no mejora

`compose.demo.yaml` pone `AiSearch__EnabledByDefault` (C17) y `AiSalesAssist__EnabledByDefault` (C34) y
**no** `AiFreeQuerySearch__EnabledByDefault` (C40). El valor por defecto de la propiedad es `false` y
`EnabledPointOfSaleIds` está vacío, así que en la demo el toggle asistido está apagado en todas las
tiendas.

Con D2, la función entera cuelga de ese interruptor. Sin la línea, el administrador se come el callejón sin
salida de D3 en el primer clic y la comprobación manual de la DoD no se puede hacer. El comentario que hay
tres líneas más arriba en ese mismo fichero describe este fallo palabra por palabra: *«la que, al faltar,
hizo que el entorno entero pareciera terminado sin estarlo»*.

### D6 · Sin requisito meta de alcanzabilidad: **tres escenarios fallables** en su lugar

Un requisito del tipo *«todo estado que la spec describa DEBE ser alcanzable por un control que el panel
ofrezca»* **no puede producir ningún escenario que un runner falle**. ¿Cuál sería? *«WHEN se especifica un
estado THEN existe un control»* no es comprobable por una suite. Sería un requisito que valida en verde y
no cambia nada — **el mismo modo de fallo, un nivel más arriba**.

En su lugar, el requisito concreto de `assisted-search-panel` lleva tres escenarios que sí pueden fallar:

1. el administrador **tiene** el control → falla si desaparece la opción;
2. el operario **no lo tiene** → falla si se enseña por error, **y protege el backend** de un
   endurecimiento «de limpieza»;
3. el ámbito global **deshabilita la ruta rápida con su motivo** → es el que cierra el change.

La lección —*auditar el estado no es auditar el camino hasta él*— va a la documentación de verificación,
donde vive la definición del barrido de completitud que ya falló dos veces.

### D7 · El `SHALL` falso sobre el cambio de tienda se **corrige**; el comportamiento se acepta

La spec viva se contradice: la línea 41 dice que cambiar de tienda **limpia** los resultados, la 596 que
**refresca las existencias**. El código limpia, y el test de C40 sólo comprobó la segunda cláusula del
escenario, nunca la primera. Limpiar es correcto por coste —la clave de caché incluye la tienda—, así que
lo que se retira es la cláusula que nunca fue verdad.

Consecuencia aceptada: volver de «todas» a una tienda concreta **borra los resultados** y hay que buscar de
nuevo. Rehidratar sin volver a recuperar exigiría una ruta nueva («hidrata estos productos en esta
tienda»), que es capacidad nueva y no cabe en un fix.

### Flujo resultante

```
 Administrador                 assisted.tsx                    .NET                      jbg-ai
      │                             │                            │                          │
      │── abre el panel ──────────▶ │                            │                          │
      │                             │── GET /point-of-sales ───▶ │                          │
      │                             │◀── tiendas activas ─────── │                          │
      │                             │  setPointOfSaleId(primera activa)   ← D: no cambia    │
      │                             │── GET /availability?pos=X ▶│                          │
      │                             │◀── 200 {semantic, assisted, reason} ─── sin modelo ── │
      │                             │                            │                          │
      │── selecciona «Todas» ─────▶ │  scope := ALL                                         │
      │                             │  route  := 'assisted'          ← D2                   │
      │                             │  results:= idle                ← D7                   │
      │                             │  ✗ NINGUNA petición de búsqueda                       │
      │                             │── GET /availability (sin pos) ▶│                       │
      │                             │                            │ IsEnabledForScope(null)  │
      │                             │                            │  → EnabledByDefault ← D4 │
      │                             │◀── 200 {pointOfSaleId: null, …} ───────────────────── │
      │                             │                                                       │
      │   ┌─ assisted ON  → toggle habilitado, rápida deshabilitada con motivo de ámbito     │
      │   └─ assisted OFF → se enuncia: «el ámbito usa la respuesta asistida, y está         │
      │                      desactivada»                              ← D3                  │
      │                             │                            │                          │
      │── Buscar ─────────────────▶ │── POST /search/assisted ──▶│                          │
      │                             │   { query, …, SIN pointOfSaleId }   ← D8 del ticket    │
      │                             │                            │ ScopeOf(null)            │
      │                             │                            │  → ForAllPointsOfSale    │
      │                             │                            │── token SIN pos_id ────▶ │
      │                             │                            │◀── candidatos ────────── │
      │                             │                            │ HydrateAsync(ids, null)  │
      │                             │                            │  → AGRUPA por producto   │
      │                             │                            │ RecordAsync → omitido    │
      │                             │◀── 200, cantidad nula ──── │   (telemetría diferida)  │
      │◀── filas sin cero, sin tienda, ficha deshabilitada ────── │                          │
```

## Risks / Trade-offs

**R1 · La rama nula de `SearchLexicalAsync` es un HTTP 500 dormido.** Acepta `Guid?` y `Carried(null)`
suelta el filtro de tienda, pero **no agrupa por producto** como sí hace `HydrateAsync` —con un comentario
que explica el peligro—, y `BuildResultsAsync` hace `rows.ToDictionary(row => row.ProductId)`
**incondicionalmente**, en las dos ramas. Un producto que tres tiendas llevan volvería tres veces y la
petición acabaría en `ArgumentException`. → **Mitigación:** D2 la deja dormida —ningún llamante le pasa
`null`— y se **anota en `DEFERRED_TASKS.md` con su motivo**, junto a la extensión de la ruta rápida, porque
son la misma tarea. Sin esa nota, quien acometa la extensión la pisará, y **primero en desarrollo local**,
donde `AiSearch:EnabledByDefault` no está puesto y la ruta degradada es la que corre siempre.

**R2 · La tentación de añadir sólo el `SelectItem`.** → **Mitigación:** el escenario 3 del requisito
—«el ámbito global deshabilita la ruta rápida con su motivo»— falla si no se hace, y las tareas ponen el
toggle antes de los tests.

**R3 · La tentación de endurecer la autorización «por coherencia»** con el requisito nuevo del panel.
Contradiría `ai-free-query-search`, que la abre con su razón escrita, y tumbaría un test correcto de C40.
→ **Mitigación:** el requisito del panel **afirma explícitamente que la ruta sigue abierta**, y el
escenario 2 lo fija.

**R4 · Que la sonda y la ruta calculen predicados distintos.** Es la avería original de C40. →
**Mitigación:** D4, el predicado extraído, más un test que compara las dos respuestas para el mismo ámbito.

> **La mitigación quedó a medias, y la verificación independiente del 2026-09-26 lo midió.** Dos cosas:
>
> 1. **El test no comparaba nada.** `GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate` calcula
>    el valor esperado con los mismos métodos de extensión que la sonda y **nunca invoca**
>    `FreeQuerySearchService`. Sobrevive en verde a invertir la rama nula del predicado compartido **y** a
>    reescribir la ruta con una regla distinta para la ausencia (dos mutaciones, compiladas y ejecutadas).
>    Lo único que fija es la sonda contra `AiScopeSwitchExtensions`, que es un lado. Sustituido por
>    `AiScopePredicateAgreementTests`, que construye las dos piezas sobre las mismas opciones, **ejecuta la
>    ruta** y compara veredictos; caza las dos mutaciones.
> 2. **El riesgo sigue vivo, en una dirección.** La sonda reporta `freeQuery && salesAssist`; la ruta
>    aplica `freeQuery` a secas. Con el primero encendido y el segundo apagado, la sonda dice
>    `switched_off` de un ámbito que la ruta sirve con prosa —comprobado por HTTP contra la API en
>    marcha—, y en el panel eso deshabilita **las dos** vías y escribe «…usa la respuesta asistida, y está
>    desactivada» de algo que funciona: el propio defecto que este change vino a cerrar, alcanzable por
>    una combinación de interruptores. Es comportamiento heredado de C40, no introducido aquí, pero el
>    requisito que este change escribe lo prohíbe. Decisión pendiente en `DEFERRED_TASKS.md`; fijado en
>    código por `Probe_AlsoReportsTheSaleCardSwitch_WhichTheRouteNeverApplies`.

**R5 · `openspec validate --all --strict` no detecta el defecto que este change corrige.** Las tres specs
implicadas están **bien formadas**; lo que falla es su contenido. → **Mitigación:** la puerta de verdad es
la comprobación manual por la interfaz con los dos roles, y está en la DoD como casilla propia.

**R6 · La regla de la primera línea física del validador.** La descripción que sigue a
`### Requirement:` se valida leyendo **sólo su primera línea**. → **Mitigación:** las deltas se escriben con
la descripción en una línea larga, sin ajustar a 90 columnas.

**R7 · El change mueve un tipo y `npm run build` no lo vería.** `pointOfSaleId` deja de ser obligatorio y
`AiSearchAvailability.pointOfSaleId` admite nulo; Vite transpila con esbuild, que descarta los tipos sin
mirarlos. C40 se comió un commit entero por esto. → **Mitigación:** `tsc --noEmit` filtrado a los ficheros
propios, como casilla de la DoD.

**R8 · Las dos suites vienen rojas de fábrica** —frontend ~113-114 de 729 en 14 ficheros, backend ~50— y
el conjunto **rota** entre ejecuciones dentro de clases y ficheros conocidos. → **Mitigación:** comparar
**nombres** contra la línea base del propio commit, y exigir **cero nombres nuevos en rojo en el área
propia** en vez de un recuento.

**Trade-off asumido · el ámbito global cuesta la ruta cara.** Se sirve por la generativa, con 10 s de
presupuesto y 10 peticiones/minuto, y **no se registra en telemetría**, así que su uso no es medible. Es
aceptable porque la audiencia es de administración y el uso ocasional; y el recorte de D1 **refuerza** el
motivo para diferir la telemetría, en vez de erosionarlo.

**Trade-off asumido · el callejón sin salida existe.** Con el interruptor apagado, el ámbito es
seleccionable y no buscable. Se acepta porque D3 lo **enuncia** y D5 lo vuelve excepcional — y porque la
alternativa cuesta una segunda lectura de la sonda en cada carga.

**Trade-off asumido · volver a una tienda concreta borra los resultados.** D7. La alternativa es una ruta
de rehidratación, que es capacidad nueva.

## Migration Plan

**Sin migración de base de datos.** Ninguna entidad, columna ni índice cambia, y `openapi.json` —la
frontera con `jbg-ai`— queda sin diff, porque el tercer perfil de *claims* de C40 ya acepta un token sin
`pos_id` en recuperación y assist.

**Despliegue:** una variable de entorno nueva en el compose de la demo (D5). Nada más.

**Rollback en tres niveles, todos sin revertir código:**

| Nivel | Acción | Resultado |
|---|---|---|
| Apagar `AiFreeQuerySearch__EnabledByDefault` | El ámbito global queda seleccionable y no buscable, **con su motivo en pantalla** (D3) | El panel vuelve a comportarse como antes para todo lo demás |
| Retirar la opción del selector | Estado previo a este change, exactamente | El ámbito vuelve a ser inalcanzable — y la spec vuelve a mentir, así que el rollback de código **debe** revertir también las deltas |
| Contrato | `AiSearchAvailabilityResponse.PointOfSaleId` anulable es **adición de tolerancia**: un cliente que ya leía un valor sigue leyéndolo cuando hay tienda | Sin breaking change para el único consumidor, que es el panel |

## Open Questions

**Ninguna.** Las seis preguntas del ticket quedaron cerradas antes de este documento, y se registran
cerradas para que este diseño no las reabra: la audiencia del control (D1), la copia de la insignia sin
tienda (D4), el valor por defecto del selector (sigue siendo la primera tienda activa), el nombre de la
opción («Todas las tiendas» más la línea de consecuencia), la regla transversal de alcanzabilidad (D6) y la
forma exacta de la respuesta sin tienda (D4).

Lo que este documento añade y el ticket no tenía es el **por qué de los descartes**: las dos alternativas
de D1, las dos de D2, las dos de D3 y las tres de D4 — y **dos de ellas contradicen la versión original del
ticket**, que declaraba que el fix no tocaba el backend y que eran dos piezas.
