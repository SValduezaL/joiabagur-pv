# C42 — decisiones de exploración: el agente de venta llega a la pantalla

**Change previsto:** `add-frontend-agent-panel` (C42) · **Fecha:** 2026-09-26
**Origen:** sesión abierta para decidir entre implementar C38 completo o dar superficie al agente,
que acabó acotando el segundo
**Naturaleza de la exploración:** **contra el código, no contra el servicio.** Ningún hallazgo de
este informe se ha medido llamando al proveedor. Lo que hay son derivaciones de camino de código,
con fichero y línea, y **dos de ellas exigen una medición antes de escribir una sola tarea** — van
nombradas en el §11.

---

## 0 · Qué decide este informe

El agente de venta (`POST /v1/assist/agent`, C32a + C32b) está implementado, probado y medido con
proveedor real, y **no lo llama nadie**: `IAiGatewayClient` tiene siete métodos y ninguno es el
suyo. De los cinco pilares que el Proyecto Final nombra —CAG, RAG, **agentes**, evaluación y
despliegue—, es el único sin superficie de operario, y por tanto el único que no puede aparecer ni
en la URL pública ni en el vídeo de 2-3 minutos.

C42 le da esa superficie. **Ocho hallazgos** y **doce decisiones**, repartidos en tres capas, con
una línea de corte fijada de antemano por el mismo criterio que usó C40: **primero lo que hoy
impide que la pantalla diga la verdad, después lo que la hace más cómoda**.

**El hallazgo que gobierna la línea de corte es F1**, y no es una carencia sino una **regresión
latente que C40 introdujo sin tocar el agente**.

---

## 1 · Qué es el agente, y en qué se diferencia de M1, M2 y M3

Esta sección existe porque la pregunta se hizo y la respuesta no es la intuitiva.

### El agente no tiene modos

`AssistRequest` (`ai-service/src/jbg_ai/api/schemas/assist.py:44`) lleva `product_id`, `query` y
`filters`. Los tres modos no se declaran: se leen de qué anclas trae la petición, y por eso son
estructurales y no pueden equivocarse sobre las palabras de la consulta
(`ai-service/src/jbg_ai/assist/modes.py`).

| Modo | `product_id` | `query` |
|---|---|---|
| **M1** `QUERY_ONLY` | — | ✓ |
| **M2** `PIECE_ONLY` | ✓ | — |
| **M3** `PIECE_AND_QUERY` | ✓ | ✓ |

`AgentAssistRequest` (`ai-service/src/jbg_ai/api/schemas/assist.py:118`) lleva **`turns`**, `top_k`,
`context`, `locale` y `pos_id`. **No lleva `product_id`, ni `query`, ni `filters`.**

El agente no tiene modos **porque no los necesita: los descubre**. Donde la ruta determinista obliga
al llamante a declarar de antemano si trae pieza, pregunta o las dos, el agente recibe una
conversación y decide él, vuelta a vuelta, qué herramienta usar.

### Los tres ejes en que se diferencian

| | `/v1/assist/sale` (M1/M2/M3) | `/v1/assist/agent` |
|---|---|---|
| **Quién decide qué se recupera** | El **código**. El modo lo fija la forma de la petición; en M1 el clasificador de C31 elige ruta `catalog` / `knowledge` / `both` y ahí termina la decisión | El **modelo**, entre seis herramientas, redactando sus propios argumentos |
| **Cuántos pasos** | **Uno.** Una recuperación, un argumentario | **Hasta cinco vueltas encadenadas.** Buscar → consultar disponibilidad → pivotar a sustitutos es un plan, no una consulta |
| **Unidad de entrada** | Una consulta suelta | Una **conversación**: hasta 12 turnos, 500 caracteres por turno, 4.000 en total (`assist/constants.py:739`) |

Y una cosa que **no** cambia, que es la mejor decisión de diseño de C32b: **el bucle no escribe la
respuesta**. Sólo reúne evidencia. El argumentario lo redacta la misma capa de generación, con la
misma puerta numérica, la misma integridad referencial de citas y la misma reparación única. Por eso
`AgentAssistResponse` es **subclase** de `AssistResponse`: todos los campos de la respuesta
determinista con idéntico significado, **más cinco** —`partial`, `stop_reason`, `iterations`,
`tool_calls_used`, `trace`— y `agent_prompt_version`.

### Las seis capacidades, congeladas

De `ai-service/src/jbg_ai/assist/tools.py:902`, con la descripción que ve el modelo:

| Tool | Qué hace |
|---|---|
| `buscar_catalogo` | Piezas del catálogo a partir de lo que describe el cliente, por referencia y en orden |
| `buscar_sustitutos` | Alternativas a una pieza, con el motivo del parecido |
| `listar_familia` | Variantes de la misma pieza: medidas, acabados, materiales |
| `consultar_conocimiento` | Cuidados, materiales, tallas, garantías y políticas, **citando la ficha** |
| `consultar_disponibilidad` | Si la pieza está en esta tienda, **cualitativo y sin un solo dígito** |
| `pedir_aclaracion` | Pide concretar el eje que falta; **la pregunta la redacta el código** |

Dos ausencias deliberadas, con test que las nombra: `perfil_punto_venta` y `buscar_complementarios`.

### Los presupuestos que acotan una petición

De `ai-service/src/jbg_ai/assist/constants.py`: **5** vueltas, **8** llamadas a herramienta, **4**
concurrentes, **40.000** tokens, **36.000** caracteres de contexto, **15 s** de reloj y **8 piezas
distintas** por petición. Agotar cualquiera sirve lo reunido con `partial: true` y un `stop_reason`
del vocabulario cerrado de diez valores, **nunca inferido de los contadores**.

---

## 2 · Los ocho hallazgos

### F1 · El argumentario del agente se retira por construcción, y la causa la introdujo C40

**Éste es el hallazgo que gobierna la línea de corte.** Es una cadena de tres eslabones, cada uno
correcto por separado:

1. **El agente redacta con `assist/v4`.** `AGENT_PITCH_PROMPT_VERSION = "assist/v4"`
   (`assist/constants.py:522`), deliberadamente apartado de `PROMPT_VERSION`, que ya va por
   `assist/v5`. Y la sección *Sistema* de `v4` ordena, **sin condición**:

   > *«El precio y la disponibilidad son **siempre** marcadores. Escribe `{{price}}` donde
   > corresponda hablar del precio y `{{stock}}` donde corresponda hablar de existencias.»*

2. **El payload del agente no está anclado.** El bucle lo construye con `free_query_payload_from(…)`
   (`assist/agent.py:940`), que devuelve un `FreeQueryPayload`, cuya `is_anchored` es
   `ClassVar[bool] = False` (`assist/prompt.py:453`). Es correcto: el argumentario del agente habla
   de **varias** piezas, así que un marcador no tiene contra qué resolverse.

3. **C40 convirtió eso en violación dura.** `CAUSE_PLACEHOLDER_IN_FREE_QUERY` entra en
   `HARD_VIOLATION_CAUSES` (`assist/constants.py:339`) y la comprobación dispara exactamente cuando
   el payload **no** está anclado (`assist/verification.py:256`): `if payload.is_anchored: return ()`.

**Conclusión de la cadena:** un argumentario del agente que obedezca a su propio prompt comete una
violación dura, consume la reparación única y, si reincide, **se retira entero**. C40 arregló las
tareas de consulta libre en `v5` y **no tocó la del agente**, porque el agente no tenía consumidor y
nadie iba a ver el resultado.

> **Lo que esto NO es.** No es que .NET rechace la petición: `AiGatewayClient` dejó de exigir
> `product_id` en C40 —*«el contrato exige **al menos** un ancla, no exactamente una, y desde C40
> este cliente lo cumple»*— y `PitchPlaceholderResolver.Resolve` sólo se invoca desde
> `SalesAssistService.cs:369`, la ruta anclada. La retirada ocurre **antes**, en Python.

> **Lo que falta, y es medición y no argumento.** La tasa a la que el agente escribe marcadores hoy
> **no está medida**. La referencia conocida es de C30b sobre los modos anclados con `v3`:
> `{{price}}` en **147 de 213** y `{{stock}}` en **188 de 213**. La cifra del agente es la primera
> que C42 tiene que publicar, antes y después del arreglo.

### F2 · La ruta del agente es la única de assist que C40 no ensanchó

| Ruta | Dependencia | `pos_id` |
|---|---|---|
| `/v1/assist/sale` | `get_unscoped_principal` (`api/routers/assist.py:232`) | **Opcional** desde C40 |
| `/v1/assist/agent` | `get_service_principal` (`api/routers/assist.py:340`) | **Obligatorio** |

Hoy un token sin punto de venta recibe **401** en el agente, y está afirmado con test:
`test_pos_scoped_route_still_rejects_it`. El informe de C40 lo dice por su nombre —*«toda ruta de
una sola tienda —sustitutos, inventario, agente— sigue rechazando la omisión»*—, con motivo: la ruta
no tenía consumidor.

### F3 · La procedencia de un grupo no viaja en la respuesta

En `assist/agent.py:779` se construyen **dos** listas de grupos a partir de la misma evidencia:

- `payload_groups` → lo que ve el modelo, **con `origin`**: `catalogo` o `sustitutos`
- `response_groups` → lo que recibe el consumidor: `AssistGroup(family_id, family_label, members)`

**`origin` no está en la respuesta.** El argumentario dice en prosa *«y como alternativa…»* porque el
prompt se lo ordena, pero **la pantalla no puede rotular las filas**. Es exactamente lo que
`GROUP_ORIGIN` existe para impedir, y su propio comentario lo escribe: *«un payload que las aplanara
dejaría que el argumento ofreciera un segundo mejor como si fuera lo que se había pedido»*.

### F4 · Un miembro de grupo no trae nombre, ni precio, ni existencias, ni foto

`_response_member` (`assist/agent.py:847`) publica: `product_id`, `sku`, `variant_label`,
`materials`, `score`, `match_reasons`. Y nada más.

**Pero la hidratación ya existe y ya cubre el caso.** `SalesAssistService.cs:219` hidrata
`ai.Groups.SelectMany(group => group.Members)` — **todos los miembros de todos los grupos**, no sólo
el ancla. Y C40 dejó el DTO que corresponde: `AssistedSearchResultDto` con `Name`, `Price`,
`QuantityAtPointOfSale` y `HasStock` **anulables**, `PrimaryPhotoUrl`, `CollectionName`, `Score`,
`MatchReasons`, `Materials`, `FamilyId` y `VariantLabel`.

### F5 · De la ficha de C36 sólo es reutilizable la mitad, y el bloque de sustitutos no lo es

| Componente de C36 | ¿Sirve para el agente? | Por qué |
|---|---|---|
| `pitch-block` | **Sí, tal cual** | Es de respuesta, no de pieza |
| `warnings-block` | **Sí, con tabla de copy propia** | El vocabulario de avisos del agente no es el de la pieza anclada |
| `question-box` | Sustituido | Su función la cumple el compositor de la conversación |
| `piece-header` | **No** | Es un héroe de una pieza: foto grande, precio, unidades. Ocho de esos no son una respuesta |
| `family-block` | **No como componente** | Es *«otras tallas de la pieza que miras»*, y aquí no hay pieza mirada |
| `substitutes-block` | **Imposible** | Se alimenta de `familyMatch`, `materialOverlap` y `styleSimilarity`, que llegan por **endpoint aparte** (`salesAssistService.substitutes`) y que el miembro del agente **no lleva** |

Y **el panel de consulta libre de C40 no tiene bloque de sustitutos**: cero apariciones en
`frontend/src/pages/sales/assisted.tsx`. Los sustitutos sólo existen en la ficha, por segunda
llamada.

> **El componente que sí encaja es `assisted-search-result-row`**, y encaja entero: ya resuelve
> `pointOfSaleName: null` sin afirmar cantidad, `familyNote` para *«también en XS, S y 4 tallas
> más»*, botón de vender, botón de abrir ficha, y `hasStock === null` deshabilitando la venta. Es la
> pieza que C40 dejó lista sin saberlo.

### F6 · El agente sí tiene modo degradado, y está vacío

Dos valores del vocabulario de parada son exactamente eso (`assist/constants.py:680`):

- **`sin_cliente`** — no hay credencial de agente. La spec lo escribe: *«without an agent credential
  the route degrades instead of failing»*.
- **`fallo_proveedor`** — el proveedor cayó. La ruta **no devuelve 5xx**: responde 200 con
  `partial: true`.

La diferencia con las rutas deterministas es la que decide el diseño. En C34/C36 degradar vale
mucho, porque los datos del catálogo siguen ahí: *«un fallo del servicio nunca deja al joyero delante
de un card vacío»*. **En el agente no queda nada**: toda la evidencia viene de llamadas a herramienta
que pide el modelo. Sin modelo no hay llamadas, y sin llamadas no hay grupos, ni prosa, ni citas.

Pero las dos causas no se conocen en el mismo momento:

| | Cuándo se sabe | Consecuencia de diseño |
|---|---|---|
| `sin_cliente` | **Antes** de gastar nada | La puerta se cierra |
| `fallo_proveedor` | **A mitad del bucle**, con herramientas ya ejecutadas | Dentro, como respuesta cortada: hay evidencia y falta el argumento |

### F7 · La sonda de disponibilidad no cubre al agente, y hoy además exige tienda

C40 construyó la sonda que hace falta: `aiSearchService.getAvailability(pointOfSaleId)` devuelve
`AiSearchAvailability` con `semanticSearchAvailable`, `assistedAnswerAvailable` y
`assistedAnswerUnavailableReason`, **sin gastar ni una llamada al proveedor ni cupo**, que es lo que
la hace segura de leer en cada cambio de tienda. Su límite está declarado en su propio comentario:
*«Only `switched_off` is knowable without making a call, and this route deliberately makes none»* —
informa de los interruptores propios, no del proveedor. Es exactamente el alcance que un portero
necesita.

Le faltan dos cosas para servir al agente:

1. **Un tercer interruptor**, `agentAvailable`. El agente tiene **cadena de credencial propia**
   —agente → assist → enriquecimiento—, así que la sonda diría «la asistida está encendida» mientras
   cada petición del agente vuelve con `sin_cliente`.
2. **Que acepte la ausencia de punto de venta.** Hoy `AiSearchController.Availability` devuelve
   **400** con `Guid.Empty`. Es el mismo defecto que el fix abierto el 2026-09-25
   (`c40-fix-all-shops-scope-unreachable`) tiene que cerrar para el panel de C40; **C42 hereda el
   arreglo y no lo duplica**.

### F8 · La etiqueta de disponibilidad no llega al argumentario, y eso hay que respetarlo

`consultar_disponibilidad` acumula su etiqueta en el libro de evidencia con un comentario que es una
regla: *«para la decisión del bucle y para la calibración, nunca para el payload»*. La autoridad
sobre existencias sigue siendo de .NET, por candidato y por tienda. La etiqueta gobierna **una sola
cosa**: si el bucle pivota a sustitutos.

Consecuencia directa para la pantalla: **el ámbito global apaga el pivote**. Sin `pos_id`, la
etiqueta es siempre `AVAILABILITY_NO_SCOPE`, nunca `sin_existencias`, y el comportamiento más
demostrable del agente no se dispara.

---

## 3 · Las doce decisiones

### D1 · Ruta propia `/sales/new/agent` y cuarta tarjeta en el hub `/sales` (cerrada)

El patrón que ya usan `scan.tsx` y el panel de C40 (`frontend/src/routing/routes.tsx:39`). Las dos
alternativas se descartan con motivo:

- **Colgarlo de la ficha `/sales/new/assist/:productId`**: la ficha parte de una pieza elegida y el
  agente no acepta `product_id`. Sería forzar el contrato.
- **Un toggle dentro del panel de consulta libre**: el panel de C40 es *una consulta → resultados* y
  el agente es *una conversación*; y ese panel **ya tiene un toggle** con otro significado (ruta
  degradada frente a generativa). Dos interruptores de nombre parecido en la misma pantalla es la
  clase de avería que C40 nació para arreglar.

> **Y la ablación se demuestra mejor así.** La misma pregunta hecha en los dos paneles es comparable
> a simple vista: la ruta determinista contesta en una pasada, el agente enseña su escalera de
> llamadas. Un toggle que cambia el comportamiento en el sitio no se lee en un vídeo.

### D2 · La tarea del agente sube a `assist/v5` con la prohibición de marcadores (cerrada)

Cierra F1. La sección *Tarea · evidencia del agente* se traslada a `v5` y hereda la regla que `v5` ya
escribe para la consulta libre: *«Cuando NO hay una pieza anclada… no hables de precio ni de
disponibilidad en absoluto»*, con el lenguaje comparativo explícitamente permitido —«el más asequible
de los tres»—.

**Es la primera tarea de la línea de corte y sin ella no hay pantalla que valga**: sin el arreglo,
C42 entrega un panel de agente sin prosa, que es la misma avería que C40 vino a corregir.

### D3 · `AgentAssistGroup(AssistGroup)` gana `origin` (cerrada)

Cierra F3. **Subclase y no campo en el modelo compartido**, que es el precedente exacto que C32b ya
sentó con `AgentUsage`: *«añadido aquí y deliberadamente no a `Usage`; el modelo compartido es lo que
publica `POST /v1/assist/sale`, y ensancharlo movería el esquema de esa ruta»*. Adición pura, cero
movimiento de la ruta determinista.

### D4 · La ruta del agente acepta token con y sin punto de venta (cerrada)

Cierra F2, copiando literalmente lo que C40 hizo con `/v1/assist/sale`: `get_unscoped_principal`, la
ausencia como *no aplicar el prefiltro* y nunca como comodín, y el resto de rutas de una sola tienda
—sustitutos, inventario— intactas.

### D5 · La autorización del ámbito global se copia de C40, sin endurecerla (cerrada)

La tarea 12.4 de C40 lo dejó decidido y probado: el ámbito global está abierto a **operarios y
administradores** (`FreeQuery_ForOperatorWithAllPointsOfSale_IsServed`), y la frontera que se protege
es otra y más fina: **no se puede nombrar una tienda no asignada**
(`FreeQuery_WhenNamingAnUnassignedPointOfSale_IsRefused`). El criterio de visibilidad del selector
tampoco es el rol, es `pointsOfSale.length > 1 || isAdmin`, así que un operario de una sola tienda
sigue sin poder cambiarlo.

Dos paneles hermanos con dos reglas de autorización distintas es de las cosas que se rompen sin que
falle ningún test. **Se copia.**

### D6 · El ámbito por defecto es la tienda del operario, y abrir a todas lo dice (cerrada)

Por F8: abrir a todas las tiendas **apaga el pivote**. No es una preferencia estética, es una
capacidad que se pierde, así que la interfaz lo declara al seleccionarlo en vez de dejar que el
operario descubra que el agente dejó de ofrecer alternativas.

### D7 · La puerta se cierra antes de entrar; `partial` se pinta dentro (cerrada)

Cierra F6. La cuarta tarjeta del hub lee la sonda **antes** de dejar pasar, con tres estados:

| Estado de la sonda | Tarjeta |
|---|---|
| **Disponible** | Activa |
| **No disponible** (`switched_off`, sin credencial) | Deshabilitada **con el motivo**, como ya hace `SearchRouteToggle` |
| **No contesta** (`unknown`) | **Activa, con aviso.** Fallar la sonda no puede cerrar una puerta que quizá funciona — es la regla que C40 ya escribió para su insignia |

Y dentro, `partial: true` es una **cinta de respuesta incompleta que nombra el presupuesto agotado**,
nunca un error ni un color de alarma.

### D8 · La sonda gana `agentAvailable` (cerrada)

Cierra la primera mitad de F7. La segunda mitad —que la sonda acepte la ausencia de tienda— **es del
fix de C40 y C42 la hereda**; si el fix no hubiera entrado cuando C42 empiece, entra aquí y se
declara.

### D9 · El hilo es el eje: cada turno es dueño de su bloque de respuesta (cerrada)

La alternativa —un panel de resultados fijo que se refresca— se descarta por dos consecuencias
concretas, no por gusto:

1. El operario sigue leyendo el argumentario del turno 2 mientras las filas de debajo ya son las del
   turno 3.
2. **Cuando el bucle pivota, la pieza que estaba mirando desaparece sin explicación** — y el pivote
   es justo lo que el agente existe para demostrar.

Así que: turno del asistente = bloque propio, anclado en el hilo, con sus grupos, sus citas, su traza
y su estado de parada.

### D10 · La traza se pinta, y es el único componente genuinamente nuevo (cerrada)

`AgentTraceIteration` da, por iteración: qué herramientas se invocaron, si cada una fue bien y con
qué causa si no, tokens y milisegundos. **Nunca argumentos ni contenido de observaciones** — el
contrato los excluye por regla. Pintado como una escalera de pasos, es la única prueba en pantalla de
que hay un agente y no un prompt.

### D11 · El estado de parada se traduce entero, y no se infiere de los contadores (cerrada)

Los diez valores de `AGENT_STOP_REASONS` necesitan castellano, por la razón que el propio contrato
escribe: *«cinco iteraciones no dice si la quinta fue la última necesaria o la que se agotó, y son
afirmaciones opuestas sobre la respuesta que se está leyendo»*. Se sigue el método de la tabla de
copy de C36 y C40.

### D12 · Quinto `SearchOrigin` para la selección desde el agente (cerrada)

C40 añadió `SearchOrigin = 4` (`AssistedGenerative`) y declaró que **no abre migración**,
convirtiendo la comparación de las dos rutas en una consulta SQL. El agente necesita el suyo, por el
mismo motivo y con el mismo coste: sin él, una venta originada en el agente es indistinguible de una
originada en el panel, y la ablación vuelve a ser una demostración en pantalla en vez de un dato.

> **Hereda el hueco declarado de C40**: una consulta de ámbito global **no se registra**, porque
> `ProductSearchEvent.PointOfSaleId` es no nulo e indexado y registrarla exige una migración de EF
> Core. Está en `openspec/DEFERRED_TASKS.md` y no se reabre aquí.

---

## 4 · La pantalla: anatomía, y qué es fijo y qué scrollea

```
┌─ BARRA FIJA ─────────────────────────────────────────────┐
│ Ámbito: [Tienda Centro ▾] │ Todas las tiendas            │
│ Sesión: 3 peticiones · 41k tokens · 0,08 €               │
│ ⚠ Modo agente · ~9 s por respuesta   [Panel directo →]   │
└──────────────────────────────────────────────────────────┘
┌─ HILO · SCROLLEABLE ─────────────────────────────────────┐
│  operario: quiero un regalo                              │
│  ╭ respuesta 1 · COLAPSADA ─────────────────────╮        │
│  │ «¿Para quién es?» · aclaración · 1 vuelta    │        │
│  ╰──────────────────────────────────────────────╯        │
│  operario: para mi madre, algo de plata                  │
│  ╭ respuesta 2 · COLAPSADA ─────────────────────╮        │
│  │ «Estas tres piezas…» · 5 piezas · 2 vueltas  │        │
│  ╰──────────────────────────────────────────────╯        │
│  operario: esa no la tenéis, ¿verdad?                    │
│  ╭ respuesta 3 · ABIERTA ───────────────────────╮        │
│  │ completa · sin más herramientas · 3 vueltas  │        │
│  │ ARGUMENTARIO (prosa)                         │        │
│  │ > Fuentes (2)      ! avisos                  │        │
│  │ ── Coincidencias ──────────────              │        │
│  │ [fila] [fila] [fila]                         │        │
│  │ ── Alternativas ───────────────              │        │
│  │ [fila] [fila]                                │        │
│  │ > Cómo lo ha averiguado  (traza)             │        │
│  ╰──────────────────────────────────────────────╯        │
└──────────────────────────────────────────────────────────┘
┌─ COMPOSITOR FIJO ────────────────────────────────────────┐
│ [caja]                        turno 4/12 · 312/4000 car. │
└──────────────────────────────────────────────────────────┘
```

- **Fijo:** barra de ámbito y coste arriba; compositor abajo.
- **Scrollea:** el hilo entero, que es el rastro de auditoría.
- **Abierta:** sólo la última respuesta. Las anteriores colapsan a una línea con chips y se reabren
  al pulsarlas, de modo que la acción de vender está siempre en lo que está abierto.

**Los contadores del compositor no son adorno: son los tres topes del contrato.** Sin ellos el
operario se estrella contra un 422 que la interfaz podía haber evitado.

**El bloque de respuesta tiene que poder renderizarse sin filas.** Una pregunta de conocimiento
—«¿se puede mojar?»— responde con prosa y citas y **cero piezas**, y eso no es «sin resultados»: es
la avería de las cinco ramas de vacío que C40 dedicó un tramo entero a separar.

---

## 5 · Qué se mantiene y qué se renueva en cada turno

Cada envío manda **el transcript entero** y recibe **una respuesta completa y nueva**. No hay
actualización incremental de nada.

| Dato | Comportamiento |
|---|---|
| `turns` | **Se acumula.** Es lo que se reenvía; el servicio no guarda estado entre llamadas |
| `pitch` + `pitchStatus` | **Nuevo, anclado a su turno.** Los anteriores quedan, colapsados |
| `groups` (≤8 piezas) | **Nuevos, anclados a su turno.** Pueden repetir piezas de turnos previos: es correcto y **no se deduplica entre turnos** |
| `citations` | **Nuevas**, bajo su prosa. Vacía es un caso normal |
| `warnings` | **Nuevos**, con tabla de copy propia (F5) |
| `clarificationQuestion` | **Nueva**, y devuelve el foco a la caja |
| `stopReason`, `partial`, `iterations`, `toolCallsUsed`, `trace` | **Nuevos por turno**, en la tira de estado del bloque |
| `usage` | **Se acumula** en la barra fija. Es lo que hace visible el sobrecoste en vivo |
| Ámbito (`effectivePosId`) | **Fijo durante la conversación.** Cambiarlo **reinicia el hilo**: la evidencia previa se reunió en otra tienda |
| `aiAvailable` / `degradedReason` | **Nuevos**, pero se pintan en la barra fija, no en el bloque |

---

## 6 · Las etapas de una conversación

| Etapa | `stop_reason` | Qué pinta el bloque |
|---|---|---|
| **Aclaración** | `aclaracion` | Sólo la repregunta, y el foco vuelve a la caja. **Cero filas, y no es «sin resultados»** |
| **Conocimiento** | `sin_mas_herramientas` | Prosa y citas. **Cero filas, y tampoco es un vacío** |
| **Catálogo** | `sin_mas_herramientas` | Prosa + grupo `catalogo` |
| **Pivote** | `sin_mas_herramientas` | Prosa + grupo `catalogo` **y** grupo `sustitutos`, separados y rotulados |
| **Cortada** | `presupuesto_*` | Lo anterior **más `partial: true`** y la cinta que nombra el presupuesto agotado |
| **Rechazo** | `rechazado` | Rechazo cortés, `partial: false`. Reutiliza el castellano que C40 ya escribió |

---

## 7 · Alcance por capa, y línea de corte fijada de antemano

El criterio de ordenación es el de C40: **primero lo que impide que la pantalla diga la verdad**.

### Tramo 1 · `ai-service` — sin esto no hay pantalla

- **D2**: la tarea del agente a `assist/v5` con la prohibición de marcadores. Cierra F1.
- **D3**: `AgentAssistGroup` con `origin`. Mueve `openapi.json`, **adición pura**.
- **D4**: `get_unscoped_principal` en la ruta del agente.

### Tramo 2 · `backend` — el consumidor que no existe

- Método en `IAiGatewayClient` y su implementación, con **cliente con nombre propio**: *timeout* de
  **15 s más margen de red** —no los 10 s de `ai-assist`—, sin reintento, `HttpClient.Timeout`
  infinito y el presupuesto en el *pipeline*, que es el patrón que C34 ya dejó escrito.
- **Circuito que distingue degradación de fallo**: esta ruta no devuelve 5xx cuando el proveedor cae,
  así que lo que hay que contar es `stop_reason=fallo_proveedor`. Un circuito que contase todas las
  respuestas `partial` se abriría sobre una ruta que funciona como está diseñada.
- DTO: **`FreeQuerySearchResponse` de C40 más** `partial`, `stopReason`, `iterations`,
  `toolCallsUsed`, `trace` y `agentPromptVersion`. Hidratación por `AssistedSearchResultDto`.
- **D8**: `agentAvailable` en la sonda.
- **D12**: quinto `SearchOrigin`.

> Todo esto está **diseñado y no hecho** en `openspec/DEFERRED_TASKS.md`, §*C32b · La política de
> timeout y de circuito*. C42 ejecuta ese diseño; no lo reabre.

### Tramo 3 · `frontend` — la pantalla

- Ruta, cuarta tarjeta con sus tres estados (D7), hilo y compositor con sus contadores.
- **Bloque de respuesta con tira de estado**: el único componente genuinamente nuevo.
- Traza (D10) y castellano de los diez `stop_reason` (D11).
- Filas: `assisted-search-result-row` **sin tocar**. Prosa y citas: `pitch-block` de C36.

### Tramo 4 · el último, y el único que no arregla nada que hoy engañe

- Contador de coste acumulado de la sesión en la barra fija.

---

## 8 · Fuera de alcance, declarado

- **El *streaming* / SSE del argumentario.** Con p95 de 9,0 s la tentación es real; queda fuera por
  la misma razón que quedó fuera de C40, y la mitigación es el estado de espera con la traza llegando
  al final.
- **Preguntar por el stock de una tienda concreta, o de varias a la vez.** Ninguna de las seis tools
  acepta un punto de venta —`_SkuArgs` es `sku` y `extra="forbid"`— y el motivo está escrito en
  `api/auth.py:27`: *«un `pos_id` comodín es exactamente lo que nunca debe existir»*. Habilitarlo
  exige una tabla de qué tiendas ve cada usuario, que hoy no existe. **No es una tool más: es un
  cambio de modelo de autorización.**
- **El desglose de `usage` por etapa.** Está identificado en `DEFERRED_TASKS.md` como adición pura a
  `AgentUsage`; sólo entra si el contador de coste del tramo 4 lo necesita.
- **La telemetría de la ficha** (§15.14) y el registro de la consulta de ámbito global, que arrastran
  migración de EF Core.
- **Los escenarios puntuados del agente**, que son de C38.

---

## 9 · Cifras que la implementación tiene que publicar

1. **Marcadores en el argumentario del agente, antes y después de `v5`.** Es la que decide si el
   agente tiene prosa, y hoy no existe. Referencia comparable: C30b midió `{{price}}` en 147 de 213
   y `{{stock}}` en 188 de 213 sobre los modos anclados con `v3`.
2. **Tasa de retirada del argumentario por causa**, partida por `dangling_citation` y
   `placeholder_in_free_query`. La referencia abierta de C32b es **13,1 %** de retirada en `gpt-4o`
   —9,5 puntos por `dangling_citation`— contra **2,2 %** de la ruta determinista.
3. **Reparto de los `stop_reason`** sobre una pasada de conversaciones reales, que es lo que dice si
   los presupuestos están bien puestos.
4. **Latencia p50/p95 extremo a extremo medida por .NET**, contra el p50 5,3 s / p95 9,0 s / máx
   11,9 s que C32b midió en Python sobre 102 peticiones.
5. **Piezas por respuesta y reparto catálogo/sustitutos**, contra el tope de 8.

**Y el artefacto se persiste** con `run_id`, `git_sha` y `prompt_version`, por la lección de C40: una
pasada no guardada es reproducible pero no re-puntuable.

---

## 10 · Riesgos y restricciones operativas

- **La cuota de tokens por minuto, y no el dinero, fija el ritmo.** Con peticiones de ~13.000 tokens,
  un techo de 25.000 TPM admite **una petición por minuto**. Para un operario y un evaluador basta;
  para dos mostradores simultáneos no, y el síntoma es un `RateLimitError` que la capa convierte en
  `fallo_proveedor` y sirve degradado. **La interfaz tiene que decir el coste antes de que se
  pulse**, como hizo C40 con su presupuesto.
- **El agente cuesta ×3,0 y hoy no tiene contrapartida medida.** Por eso D1 lo pone en ruta propia y
  no como modo por defecto del mostrador: servir por defecto una ruta medida como más cara y más
  propensa a retirar su argumentario sería mal criterio de ingeniería. Como demostración de ablación,
  la misma cifra pasa de penalización a decisión justificada.
- **Cambiar de ámbito a mitad de conversación invalida la evidencia previa.** D6 lo resuelve
  reiniciando el hilo, y la interfaz lo avisa antes.

---

## 11 · Qué verificar antes de escribir la primera tarea

Este informe se construyó leyendo código. **Dos cosas hay que medirlas antes de fijar el alcance**, y
una tercera hay que comprobarla:

1. **La tasa real de marcadores del argumentario del agente** (F1). La cadena de código es
   inequívoca, pero el número no está medido. Si resultara ser bajo, D2 sigue siendo necesaria y deja
   de ser urgente; si es alto, gobierna la línea de corte tal como está escrita.
2. **Cuántos argumentarios se retiran hoy por `placeholder_in_free_query`** en una pasada del agente.
   `agent_sweep --rescore` recalcula agregados sobre un artefacto ya escrito, sin proveedor y sin
   base de datos.
3. **Si el fix `c40-fix-all-shops-scope-unreachable` ya cerró** que la sonda acepte la ausencia de
   punto de venta. Si sí, D8 se reduce al tercer interruptor; si no, entra entero aquí.

### Reproducir lo que sí está comprobado

```bash
# La ruta del agente exige pos_id y la determinista no
grep -n "get_unscoped_principal\|get_service_principal" ai-service/src/jbg_ai/api/routers/assist.py

# El payload del agente no está anclado, y el marcador es violación dura
grep -n "is_anchored" ai-service/src/jbg_ai/assist/prompt.py
grep -n "CAUSE_PLACEHOLDER_IN_FREE_QUERY" ai-service/src/jbg_ai/assist/constants.py

# assist/v4 ordena escribir marcadores siempre; assist/v5 sólo con pieza anclada
sed -n '47,83p' ai-service/prompts/assist/v4.md | grep -n "marcadores"
sed -n '54,97p' ai-service/prompts/assist/v5.md | grep -n "anclada"

# origin existe en el payload y no en la respuesta
sed -n '779,813p' ai-service/src/jbg_ai/assist/agent.py

# la sonda exige punto de venta
sed -n '234,252p' backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs
```
