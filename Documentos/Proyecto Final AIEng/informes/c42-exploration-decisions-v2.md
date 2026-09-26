# C42 — decisiones de exploración v2: el agente de venta llega a la pantalla

**Change previsto:** `add-frontend-agent-panel` (C42) · **Fecha:** 2026-09-26
**Sustituye a:** [c42-exploration-decisions.md](c42-exploration-decisions.md) (v1, misma fecha), que
**no se borra**: sus ocho hallazgos y doce decisiones siguen siendo la base y este informe los
referencia por su nombre. Lo que cambia está en el §0.
**Naturaleza de la exploración:** contra el código **y contra los artefactos ya escritos**. El v1 se
construyó leyendo código y dejó tres cosas por comprobar en su §11; este informe las cierra, y lo
hace **midiendo sobre `evals/results/` sin llamar al proveedor ni una vez**. Todas las cifras nuevas
salen de `c32b-agent-sweep-293fe5c6e470.json` (204 filas, proveedor real, 2026-09-21) y de los dos
artefactos de marcadores de C40.

**Estado:** informe cerrado. Las cuatro decisiones abiertas están tomadas. Este documento es la
entrada de `/enrich-us` para la historia y el ticket.

---

## 0 · Qué decide este informe, y qué corrige del v1

El v1 dejó **tres cosas por comprobar** y **cuatro decisiones sin tomar**. Están las siete cerradas.
Y al cerrarlas aparecieron **dos correcciones de fondo** que mueven la línea de corte.

| | v1 decía | v2 dice | Consecuencia |
|---|---|---|---|
| **F1 gobierna la línea de corte** | *«sin el arreglo, C42 entrega un panel de agente sin prosa»* | **Refutado con la medición de C40.** Sobre el análogo estructural exacto: **3 de 90** generaciones con marcador y **0 retiradas** | D2 baja del primer puesto. **El tramo 2 ocupa su sitio**, que es donde estaba el 100 % |
| **La referencia de la tasa de marcadores** | C30b: `{{price}}` 147/213, `{{stock}}` 188/213 | **Clase de referencia equivocada.** Son modos **anclados**; el agente es el caso **libre**, y `v5.md` ya escribe que la proporción no se traslada | La línea base se toma prestada de C40, declarada |
| **`agent_sweep --rescore` mide las retiradas por marcador** | *«recalcula agregados sin proveedor y sin base de datos»* | **Imposible.** El arnés **no cuenta marcadores** y **el texto del argumentario no se persiste**; `rescore` reagrega campos ya grabados | Nace un **T0 de instrumentos** antes de la primera tarea funcional |
| **Medir antes de escribir la primera tarea** | instrucción del §11 | **No era ejecutable**: medir exige escribir primero el instrumento | El contador es la tarea 0.1 |
| **La pasada de C32b es la base de comparación** | se cita sin reservas | **Corrió 2 h 44 min contra un techo de rancidez de 1 h**, sin drenaje automático disponible entonces. Parte de sus cifras describen una recuperación **sin ámbito** | §4 y §9: se anota, no se rehace. **El pivote sobrevive** |
| Profundidad de la conversación | maqueta: «turno 4/12» | **6 intercambios**, no 12: el tope de caracteres cuenta también los turnos del asistente | §6 y D15 |

### Las cuatro decisiones nuevas, en una línea

- **D13** — `assist/v6` **sólo para el agente**; `v5` queda intacto.
- **D14** — `fallo_proveedor` es **métrica y no entrada del circuito**; se **refuta** la entrada de `DEFERRED_TASKS.md`.
- **D15** — turno del asistente con el **argumentario íntegro**, **6 intercambios** de profundidad, **línea sintética** cuando se retiró.
- **D16** — **una sola pasada**, después del cambio, con **dos instrumentos** y **una precondición de runbook**.

---

## 1 · Los tres puntos del §11 del v1, resueltos

| §11 | Estado | Qué se encontró |
|---|---|---|
| **3.** ¿Cerró `c40-fix-all-shops-scope-unreachable` que la sonda acepte la ausencia de tienda? | ✅ **Sí** | `AiSearchController.Availability([FromQuery] Guid? pointOfSaleId)`: ausencia = ámbito global, `Guid.Empty` = **400**. **D8 se reduce al tercer interruptor.** Y C42 hereda además el predicado único que el fix extrajo, `IsEnabledFor(this <opciones>, Guid?)` sobre las tres clases de opciones, con su test de que sonda y ruta no pueden derivar |
| **1.** La tasa real de marcadores del agente | ❌ **No medible como el v1 supone** | `agent_sweep.py` **no cuenta marcadores**: cero apariciones de `placeholder`. El contador existe sólo en `evals/free_query_gate.py:212-213`, que es un script aparte que C40 escribió para su medición |
| **2.** Retiradas por `placeholder_in_free_query` vía `--rescore` | ❌ **Imposible** | `rescore()` (`agent_sweep.py:998`) recalcula agregados **sobre los campos que la pasada grabó**. La fila guarda `pitch_chars`, **no el texto**. Y la causa **nació en el mismo commit que su comprobación** — `efeedfe`, *«Escribe assist/v5 y la causa dura que hacen posible el argumentario de M1»* —, así que los **0** `placeholder_in_free_query` del barrido de C32b son **la ausencia del detector**, no una tasa baja |

> **El hallazgo de orden.** El v1 ordena medir «antes de escribir una sola tarea», y eso **no es
> ejecutable**: el instrumento no existe. No es un defecto del v1 —descubrió el requisito leyendo
> código, que es lo que podía hacer— pero sí obliga a un tramo cero. **Escribir el contador es la
> tarea 0.1, y va antes de D2.**

---

## 2 · Lo que el v1 dimensionó mal: F1 es real y su urgencia está refutada

Esta sección es la que mueve la línea de corte, así que va con la evidencia entera.

### 2.1 · La cadena de F1 es exacta

Los tres eslabones del v1 están verificados y ninguno se toca:

1. `AGENT_PITCH_PROMPT_VERSION = "assist/v4"` (`assist/constants.py:522`), y la sección *Sistema* de
   `v4` ordena marcadores **sin condición** (`prompts/assist/v4.md:59`).
2. El payload del bucle es un `FreeQueryPayload` con `is_anchored = ClassVar[bool] = False`
   (`assist/prompt.py:453`), construido en `assist/agent.py:940`.
3. C40 metió `CAUSE_PLACEHOLDER_IN_FREE_QUERY` en `HARD_VIOLATION_CAUSES`
   (`assist/constants.py:339`) y la comprobación dispara exactamente cuando el payload **no** está
   anclado (`assist/verification.py:256`).

### 2.2 · La analogía que el v1 no usó, y es literal

El v1 dimensiona la cadena con C30b sobre modos **anclados**. Pero existe un análogo mucho más
cercano, y la frase que lo gobierna es **idéntica palabra por palabra**:

```
prompts/assist/v3.md:47   «El precio y la disponibilidad son siempre marcadores.»  ← 3 tareas libres
prompts/assist/v4.md:59   «El precio y la disponibilidad son siempre marcadores.»  ← tarea del agente
```

Misma sección *Sistema*, misma orden sin condición. Y `## Tarea · evidencia del agente`
(`v4.md:132-166`) **no menciona precio ni stock**: hereda esa regla y nada más — exactamente la
situación de las tareas libres bajo `v3`.

**Así que C40 ya midió este caso**, con proveedor real, sobre 90 consultas libres —payload sin
anclar, varias piezas, lenguaje comparativo: la misma forma que el payload del agente—:

| | `v3` · ordena marcadores | `v5` · los prohíbe |
|---|---|---|
| Artefacto | `c40-placeholders-before-v3-ed9ee934e8c6.json` | `c40-placeholders-after-v5-53f4759f200f.json` |
| Consultas | 90 | 90 |
| `{{price}}` / `{{stock}}` totales | **2 / 1** | 0 / 0 |
| Generaciones con marcador | **3 de 90 (3,3 %)** | 0 de 90 |
| `placeholder_in_free_query`, primer intento | **3** | 0 |
| **`placeholder_in_free_query` tras la reparación** | **0** | 0 |
| Retirada del modo libre | 8,9 % *(por otras causas)* | 0 % |

**Cero de noventa argumentarios se retiraron por marcadores.** La reparación única los arregló todos.

Y la cabecera de `v5.md` ya había escrito la refutación de la extrapolación, con su mecanismo:

> *«**La medición de C40 lo desmiente**: sobre 90 consultas del conjunto etiquetado contra el
> proveedor real, `v3` escribió `{{price}}` 2 veces y `{{stock}}` 1, en 2 de 90 generaciones. La
> proporción de los modos anclados no se traslada. La razón está en la propia tarea: anclado hay
> **una** pieza y se la vende, así que nombrar su precio es natural; en libre hay hasta quince
> agrupadas y lo que se pide es **comparar**.»*

### 2.3 · «Consume la reparación única» no es lo que hace el código

`assist/pitch.py:24` lo escribe en negrita: ***«One repair, not one per check.»*** Y
`repair_message(violations)` (`pitch.py:169`) recibe **la lista entera de violaciones**. Un marcador
**no gasta** una reparación que `dangling_citation` fuera a usar: **se añade a la misma lista**. El
coste real se reduce a que una reparación a la que se piden dos cosas las haga peor — plausible, no
medido, y sobre una co-ocurrencia del orden del 3 %.

### 2.4 · Qué sobrevive de F1 y qué se cae

```
┌─ F1 · resultado de la verificación ─────────────────────────────────┐
│                                                                     │
│  ✅ La cadena de tres eslabones es correcta                         │
│  ✅ D2 es necesaria: el prompt pide lo que la puerta prohíbe        │
│  ✅ D2 es barata                                                    │
│                                                                     │
│  ❌ «Gobierna la línea de corte»                                    │
│  ❌ «Sin ella, C42 entrega un panel de agente sin prosa»           │
│  ❌ La referencia de C30b (147/213) — refutada en v5.md            │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.5 · Lo que sí gobierna la línea de corte

**El tramo 2, y no por argumento sino por aritmética:** `IAiGatewayClient`
(`backend/src/JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs`) tiene **siete** métodos
—`SearchAsync:34`, `EnrichAsync:59`, `HealthAsync:86`, `SuggestFamiliesAsync:122`,
`AuditFamiliesAsync:163`, `AssistSaleAsync:201`, `SubstitutesAsync:233`— y **ninguno es el del
agente**. Eso no es una degradación del 3 %: es el **100 %**.

**Y la causa que de verdad retira el argumentario del agente ya está medida, y no es el marcador.**
Del barrido de C32b, 204 filas:

| causa | primer intento | **sobrevive** |
|---|---|---|
| `dangling_citation` | **85** | **72** |
| `claim_not_in_pitch` | 8 | 6 *(no es dura, por decisión declarada)* |
| `figure_not_in_context` | 6 | 2 |

La reparación arregla **13 de 85** citas colgantes (15 %). Retirada medida en `gpt-4o`: **11 de 84 =
13,1 %**, que reproduce exactamente la cifra publicada por C32b. Y **el 92,2 % de las respuestas
traen cero citas** (188 de 204): la mayoría de las retiradas son identificadores inventados sobre un
corpus que no se entregó, que es lo que `v4.md:149` ya intenta prevenir a fuerza de prosa.

> **Consecuencia para el §10.** La primera cifra que C42 debe publicar **no es la de marcadores**: es
> `dangling_citation` sobre el agente, que está al **41,7 %** de incidencia y al **85 %** de
> supervivencia. La de marcadores entra igual, y saldrá cerca de cero.

---

## 3 · Las cuatro decisiones de esta sesión

### D13 · `assist/v6` sólo para el agente; `v5` queda intacto (cerrada)

**El problema que el v1 no plantea.** D2 dice que la sección *Tarea · evidencia del agente* «se
traslada a `v5`». Literalmente eso es editar `v5` en sitio, y `v5` **no contiene hoy esa tarea**:

```
v4.md · 8 tareas                        v5.md · 7 tareas
  pieza sin pregunta                      pieza sin pregunta
  pieza con pregunta                      pieza con pregunta
  pieza con pregunta sin cobertura        pieza con pregunta sin cobertura
  consulta libre · catálogo               consulta libre · catálogo
  consulta libre · conocimiento           consulta libre · conocimiento
  consulta libre · catálogo y conoc.      consulta libre · catálogo y conocimiento
  ▸ evidencia del agente          ✗       consulta libre · conocimiento sin cobertura  ← nace en v5
```

Y `v5.md` abre declarando la disciplina que eso rompería:

> *«**Todas las versiones se conservan en disco**, y no por coleccionismo: cada una tiene cifras
> medidas contra ella, y borrarla dejaría esas cifras sin texto que interpretar.»*

con una tabla cuya fila dice que `v5` aportó *«el modo libre deja de escribir marcadores, y nace la
cuarta tarea libre»*. Añadirle una octava tarea hace que **esa fila mienta** y que «medido contra
v5» deje de nombrar un texto único — **justo cuando C38 va a medir `v5`**.

| | A · Editar `v5` en sitio | B · `v6` completo, ambas constantes | **C · `v6` sólo para el agente** |
|---|---|---|---|
| Coste | 1 sección | fichero entero duplicado | fichero con *Sistema* duplicado |
| Cifras de C40 sobre `v5` | **ambiguas** | intactas | **intactas** |
| Objetivo de C38 | mide un `v5` movido | obliga a rehacer la comparación de C40 | **`v5` determinista + `v6` agente** |
| Respeta que las constantes están **deliberadamente apartadas** | sí | **no: las fusiona** | **sí** |
| Riesgo | ninguno | ninguno | **deriva entre los dos *Sistema*** |

**Decisión: C.** Es la única que preserva a la vez las cifras de C40, el objetivo de C38 y la
separación deliberada de `AGENT_PITCH_PROMPT_VERSION` y `PROMPT_VERSION`, que existe precisamente
porque el agente y la ruta determinista evolucionan a distinto ritmo.

**Y la deriva se convierte en un fallo de suite, no en un desvío silencioso:** test de que la sección
*Sistema* de `v6` es **idéntica** a la de `v5`. Es el riesgo real de esta opción y sale barato
cerrarlo.

Concretamente:

- `prompts/assist/v6.md` nace con el *Sistema* de `v5` y **una sola tarea**, la del agente, reescrita
  con la regla que `v5` ya escribe: *«Cuando NO hay pieza anclada… no hables de precio ni de
  disponibilidad en absoluto»*, con el lenguaje comparativo explícitamente permitido.
- `AGENT_PITCH_PROMPT_VERSION = "assist/v6"`. **`PROMPT_VERSION` no se toca.**
- `v6.md` estrena su fila en la tabla de versiones: qué aportó y qué midió.
- `v4.md` no se borra: tiene las cifras de C32b medidas contra él.

### D14 · El circuito: `fallo_proveedor` es métrica, no entrada del circuito (cerrada)

**Hay una contradicción entre dos documentos del propio repositorio, y C42 la resuelve.**

`openspec/DEFERRED_TASKS.md` §*C32b · La política de timeout y de circuito* dice:

> *«Lo que hay que contar es `stop_reason=fallo_proveedor`»*

Y el *pipeline* que ya sirve a la ruta hermana dice lo contrario, en un comentario deliberado
(`AiGatewayServiceCollectionExtensions.cs:190`):

> *«A 200 the service degraded internally — no argument because the provider failed — **is not a
> failure**: Python degraded, and the breaker protects from Python not answering.»*

Y hay un obstáculo mecánico: `AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions { ShouldHandle
= args => IsRetryable(args.Outcome) })` recibe un `Outcome<HttpResponseMessage>`. **Un 200 con
`stop_reason` en el cuerpo es un éxito en esa capa.** Contarlo exige salir del contrato de Polly-HTTP.

```
           ┌──────────────────── .NET ────────────────────┐
  pantalla │  AgentAssistService                          │
     ──────┼─▶  ¿circuito de dominio?  ← opción C         │
           │      │                                       │
           │      ▼                                       │
           │  HttpClient "ai-agent"                       │
           │    ├ retry: sólo conexión nunca abierta      │
           │    ├ breaker ← ve HttpResponseMessage        │
           │    │           NO ve stop_reason  ← opción B │
           │    └ timeout 18 s                            │
           └──────────────────────────────────────────────┘
                                │  200 + {partial, stop_reason}
                                ▼
                     jbg-ai · nunca 5xx por caída del proveedor
```

| | **A · No contarlo (heredar C34)** | B · *Handler* que lee el cuerpo | C · Circuito de dominio | D · Sin circuito |
|---|---|---|---|---|
| Coherencia con la ruta hermana | **total** | rompe el comentario de C34 | lo respeta | — |
| Complejidad | ninguna | **alta**: buffering, JSON parseado dos veces, transporte acoplado al vocabulario cerrado | media | ninguna |
| Cumple el diseño diferido | no | sí | sí | no |
| **¿Protege algo de verdad?** | — | — | — | — |

**Y la última fila es la que decide.** Medido en el barrido: `tokens_prompt` p50 **12.876**, p95
**19.036**, máx **23.210** con `gpt-4o`. Contra un techo de **25.000 TPM**, el sistema admite **una
petición por minuto**. Un cortafuegos cuyo `MinimumThroughput` exige N fallos dentro de una ventana
de muestreo **no se abrirá nunca** a ese ritmo: la ventana expira antes de acumular la muestra.

**Decisión: A, y se declara.** El cliente `ai-agent` se registra copiando `ai-assist` —*timeout*
propio, sin reintento salvo `IsConnectionNeverOpened`, `HttpClient.Timeout` infinito y el presupuesto
en el *pipeline*—, y **`fallo_proveedor` se instrumenta como métrica y log, nunca como entrada del
circuito**, con el motivo escrito: a una petición por minuto no hay muestra que abrir, y quien tiene
que decirle a la pantalla que el agente no está es **la sonda** (`agentAvailable`, D8), que ya existe,
no gasta cupo y se lee en cada cambio de tienda.

**Eso cierra la entrada de `DEFERRED_TASKS.md` refutándola con una medición**, que es lo que este
proyecto viene haciendo change tras change. La entrada se marca como *cerrada por refutación* y no
como hecha.

#### El *timeout*, con el número medido

| arm | p50 | p95 | **máx** |
|---|---|---|---|
| **`gpt-4o`** · el que se sirve | 5.311 ms | 9.021 ms | **11.917 ms** |
| `gpt-4o-mini` | 6.216 ms | 10.348 ms | 14.276 ms |

Reproduce exactamente el p50 5,3 / p95 9,0 / máx 11,9 s que `DEFERRED_TASKS.md` documenta.

**El presupuesto se fija en 18 s y no en 15**, por asimetría de coste: 15 s dejan 3,1 s de holgura
sobre el máximo observado, y el modo de fallo es cortar a los 15 s una petición que Python **ya pagó
entera**. Esperar tres segundos más cuesta un operario impaciente; cortar cuesta una llamada a
proveedor pagada y tirada. `AssistTimeoutMs` **no se toca**: el cliente del agente lleva su propia
opción.

### D15 · El turno del asistente, y la profundidad real de la conversación (cerrada)

**Hallazgo que el v1 no tiene.** `AgentAssistRequest._within_the_total_cap`
(`api/schemas/assist.py`) suma **todos** los turnos:

```python
total = sum(len(turn.text) for turn in self.turns)   # operario Y asistente
```

Con `MAX_TRANSCRIPT_TURNS = 12`, `MAX_TURN_CHARS = 500`, `MAX_TRANSCRIPT_CHARS = 4_000`
(`assist/constants.py:739-741`). Y el argumentario del agente mide, medido sobre 141 generaciones:
**mín 238, p50 386, p95 514, máx 605** caracteres.

Si el cliente reenvía el argumentario como turno `asistente` —que es lo que hace que «esa no la
tenéis, ¿verdad?» tenga antecedente—:

```
6 intercambios = 6 turnos operario + 6 turnos asistente = 12 turnos   ← TOPE DE TURNOS
caracteres:  6×25 (operario) + 6×386 (p50)  = 2.466 / 4.000
             6×25            + 6×605 (máx)  = 3.780 / 4.000   ← roza
```

**La conversación son 6 intercambios, no 12.** El tope de turnos muerde primero; el de caracteres
queda cerca y muerde en conversaciones verbosas.

> **La maqueta del v1 rotula «turno 4/12» con tres intercambios ya en el hilo**, es decir contando
> sólo los turnos del operario. **Un contador así llega a «turno 9/12» con el 422 ya disparado**, que
> es literalmente la avería que el propio v1 dice que los contadores existen para evitar.

Y hay una pregunta que nadie había decidido: **¿qué texto lleva el turno `asistente` cuando el
argumentario se retiró?** Ocurre en el **13,1 %** de las peticiones con `gpt-4o`, y `AgentTurn.text`
tiene `min_length=1`.

| | **A · Argumentario íntegro** | B · Resumen sintético | C · Sólo turnos del operario |
|---|---|---|---|
| Profundidad | **6 intercambios** | ~9-10 | 12 |
| «esa no la tenéis» tiene antecedente | **sí** | parcial | **no** |
| Argumentario retirado | **sin texto que enviar** | resuelto | no aplica |
| ¿Lo permite el contrato? | sí | **sí** | sí |
| El cliente fabrica habla del asistente | no | **sí** | no |

**Decisión: A como comportamiento base, B como respuesta al caso del argumentario retirado.** El
contrato lo autoriza explícitamente al declarar el rol: *«`asistente` is **attributed and never
trusted**: this service stores no conversation, so every turn arrives from the client»*.

Concretamente:

- Turno `asistente` = **el argumentario, íntegro**, cuando existe.
- Cuando se retiró, o cuando la respuesta fue una repregunta: **línea sintética** que nombre las
  piezas por SKU y diga que no hubo argumento. Y **la spec lo escribe**, para que no parezca un
  descuido del cliente.
- **El contador del compositor cuenta el transcript que se va a enviar**, no lo que el operario
  escribió: `turnos 8/12 · 2.466/4.000`.
- Al alcanzar cualquiera de los tres topes, el compositor **se cierra con su motivo** en vez de
  dejar pulsar contra un 422.

**C se descarta**: rompe el escenario que es el vídeo entero del agente.

### D16 · Una sola pasada, con dos instrumentos y una precondición (cerrada)

El v1 promete cinco cifras. Tras medir sobre los artefactos, **tres ya existen** y **dos exigen
proveedor**:

| Cifra del v1 §9 | Estado |
|---|---|
| 3. Reparto de los `stop_reason` | ✅ **ya medida**, §5 |
| 4. Latencia p50/p95 | ✅ **ya medida** en Python, §5; falta sólo la de .NET extremo a extremo |
| 5. Piezas por respuesta y reparto catálogo/sustitutos | 🟡 medida pero **contaminada**, §4 |
| 1. Marcadores antes y después | ❌ exige **contador nuevo** + pasada real |
| 2. Retirada por causa, partida | ❌ misma pasada |

A ~1 petición/minuto, una pasada de 204 peticiones cuesta **2 h 44 min** de reloj. Dos pasadas,
~5 h 30 min.

**Decisión: una sola pasada, después del cambio.** La línea base se toma **prestada de C40 y
declarada**: 3 de 90 generaciones con marcador y 0 retiradas, sobre la misma tarea estructural, con
la frase que la gobierna idéntica palabra por palabra. Dado que el efecto esperado es ~0, pagar una
segunda pasada para confirmar un cero no lo vale — y la comparación sigue siendo defendible porque la
clase de referencia es la misma.

**Pero la pasada necesita dos instrumentos que hoy no existen y una precondición operativa.** Van en
el §7 como tramo 0, y el segundo instrumento sale del §4.

---

## 4 · La rancidez de la proyección: el hallazgo de C41, aplicado al arnés

El hallazgo que C41 anotó sobre el informe de C40 —la manipulación del §8 aplicada a
`ai.pos_projection.refreshed_at` cuando el guard lee `ai.sync_checkpoint.last_incremental_sync_at`—
**tiene una segunda vida en el arnés del agente, y ahí es peor**: no es una columna equivocada, es que
**no hay ninguna comprobación, y los dos caminos leen cosas distintas**.

### 4.1 · Qué degrada el guard, exactamente

`jpv_pos_projection_max_age_seconds`, por defecto **3.600 s** (`config/settings.py:580`), *«Measured
against `ai.sync_checkpoint.last_incremental_sync_at`, never against `ai.pos_projection.refreshed_at`,
which records when an assignment last changed»*. Verificado en los dos sitios que lo consumen:

```
retrieval/orchestrator.py:282   scope = await resolve_scope(pos_id, …, max_age_seconds=max_age)
retrieval/orchestrator.py:305   if scope.stale: → log "degraded=unscoped"
                                → EL PREFILTRO DE PUNTO DE VENTA NO SE APLICA
                                → buscar_catalogo saca de 1.168 documentos, no de los 416 de MAO-AIR

assist/tools.py:873   bucket = await search.availability_bucket(product_id, pos_id=pos_id)
                      ← LECTURA DIRECTA. SIN GUARD
assist/tools.py:880   age = age_seconds(await projection.synced_at(search))
                      ← la antigüedad VIAJA AL MODELO como «antiguedad_proyeccion_segundos»
assist/tools.py:891   «Freshness travels with the label, and a stale projection degrades the
                       observation instead of failing it: the rule is degrade, never remove.»
```

> **La buena noticia, y es la que más importa para C42: la etiqueta de disponibilidad no está
> guardada.** El pivote se decide con `availability_bucket`, que lee la fila directamente. Así que
> **el 3 de 3 en `sin_existencias` con `gpt-4o` sobrevive**, y con él la justificación de **D6** —que
> era la cifra que sostenía «el ámbito global apaga el pivote»—. **Eso no hay que anotarlo.**

### 4.2 · La asimetría que hace el arnés ciego

```
     ┌─ ARNÉS · agent_sweep ─────────────────┐   ┌─ CAMINO DE SERVICIO ──────────────┐
     │  resolve_pieces()        (:348)       │   │  resolve_scope()                  │
     │    └─ search.scope_buckets(MAO_AIR)   │   │    └─ projection_synced_at()      │
     │       retrieval/search.py:490-499     │   │       retrieval/search.py:501     │
     │       SELECT crudo · SIN GUARD        │   │       vs max_age = 3.600 s        │
     │       ports.py:204: «Read by the      │   │       stale → degraded=unscoped   │
     │        evaluation only»               │   │                                   │
     └───────────────────────────────────────┘   └───────────────────────────────────┘
                 │                                          │
                 │ resuelve 4 etiquetas perfectas           │ sirve sin ámbito
                 │ por rancia que esté la proyección        │
                 └──────── misma pasada, dos verdades ──────┘
```

La pasada de C32b resolvió las cuatro etiquetas —`sin_existencias: SKU637`, `disponible: SKU530`,
`ultimas_unidades: SKU488`, `sin_ambito: SKU01`— con `skipped: []`. **Eso no es evidencia de
frescura**: el puerto que las resolvió no mira el checkpoint. Y `assortment_size: 416` sale de
`search.count_scope(MAO_AIR)` (`agent_sweep.py:1173`), que es **otro contador crudo del arnés**, no
el `scope.size` que el camino de servicio aplicó.

### 4.3 · La aritmética que condena parte de la pasada de C32b

```
provenance.paced_seconds  =  9.870,8 s  =  2 h 44 min
techo de rancidez         =      3.600 s  =  1 h
arreglo manual            →  «caduca en una hora»  (informe de C41, §2.1)
drenaje automático        →  NO EXISTÍA: el scheduler es de C41 (26 sep); la pasada es del 21 sep
```

**A lo sumo las primeras ~74 de 204 filas corrieron con el ámbito aplicado.** Y es una **cota
superior**, porque no se sabe la antigüedad en t=0: si la pasada arrancó ya rancia, fueron cero. El
orden de ejecución, además, pone el conjunto de **calibración al final** —`load/gpt-4o` → … →
`calibration/gpt-4o-mini`—, así que las filas del pivote corrieron ~1 h 45 min pasado el techo.

**Y la contaminación no se puede limpiar a posteriori.** La `provenance` **no registra ninguna
antigüedad de proyección**. El corte ingenuo primeras-74 contra el resto da 6,72 → 5,32 grupos de
media y 9,5 % → 25,4 % de respuestas vacías, **pero está confundido por composición**: las filas 1-74
son todas `load/gpt-4o` y el resto mezcla `calibration` y `mini`, que por construcción tienen otro
perfil. **No prueba nada, y que no se pueda decidir es exactamente el hallazgo.**

### 4.4 · Por qué C41 hace la pasada de C42 posible, y la trampa del runbook

`jpv_pos_sync_interval_seconds = 600` (`config/settings.py:620`) contra el techo de 3.600, con la
regla escrita en su propia descripción —*«ceiling / interval >= 4»*—, tolera **cinco drenajes
fallidos consecutivos** y drena **al arrancar**. Una pasada de 2 h 44 min se queda dentro de la
ventana de principio a fin.

**Pero hay una trampa operativa que va al runbook:**

```
api/lifespan.py:50    run_scheduler(resolved)   ← el scheduler vive SÓLO en el lifespan de FastAPI
evals/agent_sweep.py  ← CLI: cero apariciones de «scheduler» y de «drain»
```

**La pasada no drena nada por sí misma.** Lanzada contra la base sin el contenedor `jbg-ai`
levantado, la proyección envejece una hora y **se reproduce exactamente la condición de C32b**. La
precondición no es «C41 está archivado»: es **«el contenedor está arriba con el scheduler encendido
mientras la pasada corre»**, comprobado en `/health` antes de arrancar.

---

## 5 · El estado medido del sistema, con su grado de confianza

Todo de `c32b-agent-sweep-293fe5c6e470.json` · `git_sha 2c9fd6a4…+dirty` · 2026-09-21T06:32:23Z ·
204 filas · `agent/v1` + `assist/v4` · 102 por arm (`load` 82 + `calibration` 20).

### 5.1 · Por arm, y el arm importa más que cualquier otra variable

| | **`gpt-4o`** · el que se sirve | `gpt-4o-mini` |
|---|---|---|
| p50 / p95 / máx | **5.311 / 9.021 / 11.917 ms** | 6.216 / 10.348 / 14.276 ms |
| `partial: true` | **2 de 102 · 2,0 %** | 60 de 102 · **58,8 %** |
| `presupuesto_tools` | **2** | **56** |
| `sin_mas_herramientas` | 86 | 24 |
| `aclaracion` | 10 | 12 |
| `rechazado` | 4 | 4 |
| `presupuesto_iteraciones` | 0 | 4 |
| Respuestas sin piezas | 20 · 19,6 % | 20 · 19,6 % |
| Argumentario retirado | 11 de 84 · **13,1 %** | 13 de 81 · 16,0 % |

> **`mini` no vale para esta ruta, y ahora está cuantificado**: quema el presupuesto de herramientas
> **56 veces contra 2**. Confirma por comportamiento lo que el plan ya declaraba —el brazo barato
> *«descartado por comportamiento y no por precio»*—. **Y explica que `partial` no sea un problema de
> diseño en la ruta servida: sirve al 2 %.**

### 5.2 · Tabla de confianza

| Cifra | Valor | Confianza | Por qué |
|---|---|---|---|
| Pivote `sin_existencias` | **5/6 global; 3/3 en `gpt-4o`** | ✅ **intacta** | camino de etiqueta, sin guard (§4.1) |
| Latencia p50/p95/máx | 5,3 / 9,0 / 11,9 s | ✅ intacta | C41 ya verificó que sin ámbito el SQL es 2-3 ms más lento contra un p95 dominado por dos llamadas a proveedor |
| `pitch_chars` | n=141 · p50 **386** · p95 514 · máx 605 | ✅ intacta | lado generación |
| Retirada del argumentario | **13,1 %** (`gpt-4o`) | ✅ intacta | lado generación |
| Violaciones: `dangling_citation` | **85 → 72** | ✅ intacta | lado generación |
| Citas por respuesta | **0 en el 92,2 %** (188/204) | ✅ intacta | corpus, no proyección |
| Avisos por respuesta | **0 en el 96,1 %** (196/204) | ✅ intacta | vocabulario cerrado |
| `tokens_prompt` | p50 **12.876** · p95 19.036 · máx 23.210 | ✅ intacta | sostiene D14 |
| `partial` por arm | 2,0 % vs 58,8 % | 🟡 **sostenible** | el arm domina por dos órdenes de magnitud; el tamaño del pool no invierte eso |
| **Grupos por respuesta** | 8→104 · 0→40 · 6→22 · 5→19 · 7→18 · 3→1 | ❌ **contaminada** | es exactamente lo que el prefiltro cambia: 1.168 contra 416 candidatos |
| **Saturación a 8 grupos** | 51 % | ❌ **tratar como no medida** | idem |
| Respuestas sin piezas | **19,6 %** | ✅ **robusta** | ver 5.3 |

### 5.3 · Por qué el 19,6 % aguanta, y es la cifra que más manda en la pantalla

Descompuesto, porque el titular engaña:

| arm | sin piezas | `aclaracion` | `rechazado` | **«busqué y no encontré nada»** |
|---|---|---|---|---|
| `gpt-4o` | 20 | 10 | 4 | **6 de 102 · 5,9 %** |
| `gpt-4o-mini` | 20 | 12 | 4 | 4 de 102 · 3,9 % |

**Los componentes dominantes son independientes del ámbito**: una repregunta y un rechazo no
consultan la proyección. Sólo la cola —6 de 102— es sensible al prefiltro. **Así que el 19,6 % es
sólido**, y es el estado especial más frecuente con diferencia: **una de cada cinco respuestas no
tiene ni una fila**, y las tres cuartas partes de esas son repreguntas y rechazos, no vacíos.

### 5.4 · Reparto de herramientas: qué comportamiento se verá en pantalla

```
consultar_disponibilidad  ████████████████████████  376
buscar_catalogo           ███████████               166
buscar_sustitutos         ████████                  125   ← el pivote: comportamiento habitual
consultar_conocimiento    ███████                   113
listar_familia            ██████                     94
pedir_aclaracion          ██                         24
```

**`buscar_sustitutos` con 125 invocaciones confirma que el pivote es rutina y no anécdota** — y eso
convierte **D3 (`origin` en la respuesta) en el requisito más valioso del tramo 1, por encima de
D2**. Sin `origin`, una parte grande de las respuestas pinta alternativas sin rotularlas.

### 5.5 · El presupuesto efectivo de herramientas es 6, no 8

`tool_calls_used` observado: 6→69, 2→64, 1→27, 5→14, 3→12, 0→9, 4→9. **Nunca 7 ni 8**, con un tope de
8 y **4 llamadas concurrentes** por vuelta: el bucle para cuando la siguiente tanda cruzaría el tope.
Así que parte de los `presupuesto_tools` es **cuantización y no agotamiento real**. Se declara; no se
recalibra en C42.

---

## 6 · La pantalla: anatomía corregida

Igual que en el v1, con **el contador corregido** y las frecuencias medidas anotadas:

```
┌─ BARRA FIJA ─────────────────────────────────────────────┐
│ Ámbito: [Tienda Centro ▾] │ Todas las tiendas (admin)    │
│ Sesión: 3 peticiones · 41k tokens · 0,08 €               │
│ ⚠ Modo agente · ~5 s típico, hasta 12 s  [Panel directo →]│
└──────────────────────────────────────────────────────────┘
┌─ HILO · SCROLLEABLE ─────────────────────────────────────┐
│  operario: quiero un regalo                              │
│  ╭ respuesta 1 · COLAPSADA ─────────────────────╮        │
│  │ «¿Para quién es?» · aclaración · 1 vuelta    │  ← 10 %│
│  ╰──────────────────────────────────────────────╯        │
│  operario: para mi madre, algo de plata                  │
│  ╭ respuesta 2 · COLAPSADA ─────────────────────╮        │
│  │ «Estas piezas…» · 8 piezas · 3 vueltas       │        │
│  ╰──────────────────────────────────────────────╯        │
│  operario: esa no la tenéis, ¿verdad?                    │
│  ╭ respuesta 3 · ABIERTA ───────────────────────╮        │
│  │ completa · sin más herramientas · 3 vueltas  │        │
│  │ ARGUMENTARIO (prosa, ~386 car.)              │        │
│  │ > Fuentes (2)   ← sólo en el 7,8 %           │        │
│  │ ! avisos        ← sólo en el 3,9 %           │        │
│  │ ── Coincidencias ──────────────  (origin)    │        │
│  │ [fila] [fila] [fila] …                       │        │
│  │ ── Alternativas ───────────────  (origin)    │        │
│  │ [fila] [fila]                                │        │
│  │ > Cómo lo ha averiguado  (traza)             │        │
│  ╰──────────────────────────────────────────────╯        │
└──────────────────────────────────────────────────────────┘
┌─ COMPOSITOR FIJO ────────────────────────────────────────┐
│ [caja]              turnos 6/12 · 2.466/4.000 car.       │
│                     ↑ CUENTA LOS TURNOS DEL ASISTENTE    │
└──────────────────────────────────────────────────────────┘
```

- **Fijo:** barra de ámbito y coste arriba; compositor abajo.
- **Scrollea:** el hilo entero, que es el rastro de auditoría.
- **Abierta:** sólo la última respuesta; las anteriores colapsan a una línea con chips.
- **El bloque tiene que renderizarse sin filas**, y no es un caso raro: **19,6 %**.
- **El bloque tiene que renderizarse con 8 filas**, que es el tope del contrato; la frecuencia
  exacta queda sin medir (§5.2).

### Qué se mantiene y qué se renueva en cada turno

| Dato | Comportamiento |
|---|---|
| `turns` | **Se acumula, incluidos los del asistente** (D15). Es lo que se reenvía; el servicio no guarda estado |
| Turno `asistente` | **Argumentario íntegro**; **línea sintética** si se retiró o si fue repregunta (D15) |
| `pitch` + `pitchStatus` | Nuevo, anclado a su turno. Los anteriores quedan, colapsados |
| `groups` + **`origin`** | Nuevos, anclados a su turno. **No se deduplica entre turnos** |
| `citations` | Nuevas, bajo su prosa. **Vacía es el caso normal: 92,2 %** |
| `warnings` | Nuevos, con tabla de copy propia. **Vacío en el 96,1 %** |
| `clarificationQuestion` | Nueva, y devuelve el foco a la caja |
| `stopReason`, `partial`, `iterations`, `toolCallsUsed`, `trace` | Nuevos, en la tira de estado |
| `usage` | **Se acumula** en la barra fija |
| Ámbito (`effectivePosId`) | **Fijo durante la conversación.** Cambiarlo **reinicia el hilo** |
| `aiAvailable` / `degradedReason` | Nuevos, en la barra fija |

### El ámbito global, con su matiz verificado

`assisted.tsx:186` — `const canScopeToAllPointsOfSale = isAdmin;` — y `:439` la condición de que el
**selector** se pinte, `pointsOfSale.length > 1 || isAdmin`. Son dos cosas distintas: el backend
sirve el ámbito global a operarios y administradores (D5), **pero el frontal sólo ofrece la opción al
administrador**, y C40_FIX lo fijó con test (*«should not offer the every-shop scope when the caller
is an operator»*).

Encadenado con F8 —sin `pos_id` la etiqueta es siempre `AVAILABILITY_NO_SCOPE` y el pivote no se
dispara—: **el único rol que puede elegir el ámbito global es el único que no debería usarlo aquí.**

**Se copia C40 igual (D5 y D6 sin cambios)**, porque dos paneles hermanos con dos reglas distintas se
rompen sin que falle ningún test. **Pero D6 no es cosmética**: la línea de consecuencia al
seleccionar «todas» tiene que decir **que el agente deja de ofrecer alternativas**, no sólo que no se
leen existencias.

> **Alternativa considerada y descartada:** que el panel del agente **no ofrezca** ámbito global.
> Coste cero y protege el comportamiento que el panel existe para demostrar. Se descarta por
> coherencia entre paneles hermanos. **Y el camino global del agente está medido a 2 escenarios**
> (`sin_ambito`: 2, pivotados 0, `should_pivot: false`); si entra, entra con esa cifra declarada.

---

## 7 · Línea de corte reordenada

```
┌─ T0 · INSTRUMENTOS ─ antes de cualquier tarea funcional ────────────┐
│ 0.1  Contador de marcadores en agent_sweep.py                       │
│      {{price}} / {{stock}} por fila + agregados en el resumen.      │
│      Patrón ya escrito en evals/free_query_gate.py:212-213          │
│ 0.2  Antigüedad de la proyección en la provenance Y por fila        │
│      projection_synced_at() al empezar y en cada fila: age_seconds  │
│      + stale (bool) contra jpv_pos_projection_max_age_seconds.      │
│      Sin esto la pasada de C42 es tan inauditable como la de C32b   │
│ 0.3  PRECONDICIÓN de runbook, comprobada y anotada                  │
│      contenedor jbg-ai arriba · JPV_POS_SYNC_SCHEDULER_ENABLED=true │
│      interval 600 s < techo 3.600 s · /health confirmándolo         │
└─────────────────────────────────────────────────────────────────────┘
┌─ T1 · ai-service ───────────────────────────────────────────────────┐
│ D3   AgentAssistGroup(AssistGroup) gana origin   ← PRIMERO:         │
│      buscar_sustitutos son 125 invocaciones (§5.4)                  │
│ D13  assist/v6 sólo para el agente + test de no-deriva del Sistema  │
│ D4   get_unscoped_principal en la ruta del agente                   │
└─────────────────────────────────────────────────────────────────────┘
┌─ T2 · backend · EL QUE GOBIERNA, y es el 100 % ────────────────────┐
│ Método en IAiGatewayClient + implementación                         │
│ Cliente «ai-agent»: timeout 18 s, sin reintento salvo conexión      │
│   nunca abierta, breaker HTTP-only                                  │
│ D14  fallo_proveedor como métrica; DEFERRED_TASKS cerrada refutada  │
│ DTO = FreeQuerySearchResponse + partial, stopReason, iterations,    │
│   toolCallsUsed, trace, agentPromptVersion                          │
│ Hidratación por AssistedSearchResultDto (ya cubre todos los         │
│   miembros de todos los grupos: SalesAssistService.cs:219)          │
│ D8   agentAvailable en la sonda (sólo el interruptor: §1)           │
│ D12  quinto SearchOrigin                                            │
│ Validación de los tres topes en .NET, para no delegar el 422        │
└─────────────────────────────────────────────────────────────────────┘
┌─ T3 · frontend ─ en orden de frecuencia medida ────────────────────┐
│ Ruta /sales/new/agent + cuarta tarjeta con sus tres estados (D7)    │
│ Hilo y compositor con D15: contador del transcript real            │
│ Bloque de respuesta: SIN FILAS primero (19,6 %), luego con filas    │
│ D11  castellano de los diez stop_reason                             │
│ D10  la traza                                                       │
│ Cinta de partial   ← la última: 2,0 % en el arm servido            │
│ Filas: assisted-search-result-row SIN TOCAR · prosa: pitch-block    │
└─────────────────────────────────────────────────────────────────────┘
┌─ T4 · contador de coste acumulado ─ el único que no arregla nada ──┐
└─────────────────────────────────────────────────────────────────────┘
```

### Qué cambia respecto al v1, y por qué

| Cambio | Motivo |
|---|---|
| Nace **T0** | Los dos instrumentos no existen y sin ellos no hay cifra ni auditoría (§1, §4) |
| **D3 antes que D13/D2** dentro de T1 | 125 invocaciones de `buscar_sustitutos`: rotular el origen es lo que más veces impide que la pantalla mienta |
| **T1 deja de ser «sin esto no hay pantalla»** | La medición de C40 dice que sí la hay: 3/90 afectados, 0 retirados (§2.2) |
| **T2 pasa a gobernar** | Siete métodos y ninguno es el del agente: el 100 %, no el 3 % |
| **T3 se ordena por frecuencia medida** | El vacío es el 19,6 %; la cinta de `partial`, el 2,0 % |

---

## 8 · Fuera de alcance, declarado

Todo lo del v1 §8, que se mantiene sin cambios:

- El ***streaming*/SSE** del argumentario.
- **Preguntar por el stock de una tienda concreta o de varias.** Ninguna de las seis tools acepta
  punto de venta —`_SkuArgs` es `sku` con `extra="forbid"`— y `api/auth.py:27` escribe el motivo: *«un
  `pos_id` comodín es exactamente lo que nunca debe existir»*. **No es una tool más: es un cambio de
  modelo de autorización.**
- El **desglose de `usage` por etapa**.
- La **telemetría de la ficha** y el registro de la consulta de ámbito global, que arrastran migración
  de EF Core.
- Los **escenarios puntuados del agente**, que son de C38.

Y tres que este informe añade:

- **La recalibración del presupuesto de herramientas**, aunque el §5.5 demuestre que el efectivo es 6
  y no 8. Se declara y se deja para quien recalibre.
- **La segunda pasada de medición** (D16): línea base prestada y declarada.
- **Limpiar retroactivamente las cifras de recuperación de C32b.** No se puede (§4.3): se anota.

---

## 9 · Las dos anotaciones a informes publicados

Ninguna obliga a rehacer nada, igual que la de C41 sobre C40.

### 9.1 · `c32b-implementation-measurements.md` y la entrada de `DEFERRED_TASKS.md` que la cita

La pasada `293fe5c6e470` duró **2 h 44 min** (`paced_seconds: 9.870,8`) contra un techo de rancidez
de **1 h**, sin drenaje automático disponible en esa fecha —el scheduler es de C41, cinco días
posterior— y su `provenance` **no registra antigüedad de proyección**. **A lo sumo las primeras ~74 de
204 filas corrieron con el prefiltro de punto de venta aplicado**, y es cota superior.

**Se anota, no se rehace**, y el reparto es el del §5.2:

- **Se sostienen**: latencia, `pitch_chars`, retirada del argumentario, violaciones, citas, avisos,
  tokens, el reparto de `stop_reason` por arm y **el pivote** —que decide con
  `availability_bucket`, ungated—.
- **Quedan como no medidas**: grupos por respuesta y saturación al tope.

**Y el pivote se anota explícitamente como superviviente**, porque a primera vista parecería caer con
el resto y es load-bearing para D6.

### 9.2 · La ficha C42 del plan

Dos frases hay que tocar:

1. *«El hallazgo que gobierna su línea de corte…»* → sigue siendo un hallazgo real, pero **no
   gobierna**: la medición de C40 sobre el análogo estructural da 3 de 90 y 0 retiradas. El que
   gobierna es el tramo 2.
2. *«la referencia comparable es la de C30b… 147 de 213 y 188 de 213»* → **clase de referencia
   equivocada**, refutada en la cabecera de `v5.md`. La comparable es **3 de 90**.

Y una que **se confirma y conviene decir por qué**: *«medido 3 de 3 en `sin_existencias` con
`gpt-4o`»* **se sostiene**, por el §4.1.

> **Lo que no hace falta anotar.** C42 hereda de C40 la **taxonomía** de estados del panel, no su
> reparto. La taxonomía sale del código; el reparto de los dieciséis estados es lo que el hallazgo de
> C41 declara degradado, y **C42 no lo consume**.

---

## 10 · Cifras que la implementación tiene que publicar, revisadas

| # | Cifra | Fuente |
|---|---|---|
| **1** | **`dangling_citation` sobre el agente con `v6`**, incidencia y supervivencia | **La pasada.** Es la que de verdad retira: 85→72 con `v4`, 41,7 % de incidencia |
| **2** | **Marcadores en el argumentario del agente con `v6`** | **La pasada.** Línea base **prestada y declarada**: 3 de 90 y 0 retiradas (C40, `v3` sobre payload sin anclar) |
| **3** | **Tasa de retirada partida por causa** | La pasada. Referencia abierta de C32b: 13,1 % en `gpt-4o`, contra 2,2 % de la ruta determinista |
| **4** | **Latencia p50/p95 extremo a extremo medida por .NET** | Nueva. Contra 5,3 / 9,0 / 11,9 s de Python (§5.1) |
| **5** | **Piezas por respuesta y reparto catálogo/sustitutos** | **La pasada, y esta vez con ámbito aplicado y auditable** (T0.2). La de C32b queda como no medida |
| **6** | **Reparto de los `stop_reason`** | ✅ **ya publicada en el §5.1**, por arm |
| **7** | **Antigüedad de la proyección durante la pasada** | **Nueva, y es la que hace auditable a todas las demás** (T0.2) |

**Y el artefacto se persiste** con `run_id`, `git_sha` y `prompt_version` —más `projection_age` por
fila—, por la lección de C40: una pasada no guardada es reproducible pero no re-puntuable.

---

## 11 · Riesgos y restricciones operativas

- **La cuota de tokens por minuto fija el ritmo, no el dinero.** ~13.000 tokens por petición contra
  25.000 TPM = **una petición por minuto**. Sostiene D14 y fija el coste de la pasada en 2 h 44 min.
  Para un operario y un evaluador basta; para dos mostradores simultáneos no, y el síntoma es un
  `RateLimitError` que la capa convierte en `fallo_proveedor` y sirve degradado.
- **La proyección rancia degrada en silencio y el arnés no lo ve.** Cerrado por T0.2 y T0.3. **Es el
  riesgo que ya se materializó una vez**, en C32b.
- **El agente cuesta ×3,0 y hoy no tiene contrapartida medida.** Por eso D1 lo pone en ruta propia:
  servir por defecto una ruta medida como más cara y más propensa a retirar su argumentario sería mal
  criterio. Como demostración de ablación, la misma cifra pasa de penalización a decisión justificada.
- **Los estados degradados del agente no se han observado nunca.** Cero `fallo_proveedor` y cero
  `sin_cliente` en 204 filas: la pantalla se construye para dos estados que sólo existen en test. Se
  declara.
- **`mini` no sirve** (§5.1): 56 agotamientos del presupuesto de herramientas contra 2.
- **Cambiar de ámbito a mitad de conversación invalida la evidencia previa.** D6 lo resuelve
  reiniciando el hilo, y la interfaz lo avisa antes.
- **`openapi.json` se mueve**, por D3. Es adición pura, y `test_openapi_snapshot_is_stable` tiene
  mecanismo declarado de adiciones permitidas: *«The next change that moves the contract replaces this
  fixture and the allowed additions below, deliberately»*. C40 fue ese change; **C42 es el siguiente**.

---

## 12 · Tests nombrados

Los del v1, más los que salen de las cuatro decisiones nuevas:

**`ai-service`**
- `test_agent_pitch_carries_no_placeholder`
- `test_agent_route_accepts_a_token_without_pos_claim`
- `test_agent_group_declares_its_origin`
- **`test_v6_system_section_matches_v5`** — la guarda de la deriva de D13
- **`test_agent_sweep_counts_placeholders`** — T0.1
- **`test_agent_sweep_records_projection_age`** — T0.2

**.NET**
- `AgentAssist_WhenProviderFails_DoesNotOpenTheCircuitOnPartial`
- `AgentAssist_UsesItsOwnTimeoutAndNotTheAssistOne`
- **`AgentAssist_WhenTranscriptExceedsItsCaps_IsRefusedBeforeTheCall`** — D15 en .NET
- **`AgentAvailability_WithoutPointOfSale_ReportsTheAgentSwitch`** — D8 sobre el fix heredado

**Frontend**
- `should close the agent card when the probe says the agent is off`
- `should open the agent card when the probe cannot answer`
- `should keep each turn's answer anchored to its own turn`
- `should tell a budget-cut answer from a complete one`
- `should label a substitutes group as alternatives`
- `should render an answer with prose and no pieces`
- **`should count the assistant turns towards the transcript caps`** — D15, el que cierra la maqueta
- **`should stop the composer with a reason when a cap is reached`**
- **`should send a synthetic assistant turn when the pitch was withheld`**
- **`should warn that the every-shop scope stops the agent offering alternatives`** — D6

**Nota de suite.** Las dos líneas base se miden antes de tocar nada y se comparan **por nombres**:
`dotnet test` (~50 rojos preexistentes) y `npm run test` en `frontend/` (~113-114 de 729 en 14
ficheros). Leer la **línea de resumen** y no el código de salida.

---

## 13 · Reproducir lo comprobado

```bash
# --- §1: el arnés no cuenta marcadores y el texto no se persiste
grep -c "placeholder" ai-service/src/jbg_ai/evals/agent_sweep.py          # 0
grep -n "price_placeholders" ai-service/src/jbg_ai/evals/free_query_gate.py

# --- §1: la causa y su comprobación nacieron en el mismo commit (C40)
git log --oneline -S "CAUSE_PLACEHOLDER_IN_FREE_QUERY" -- ai-service/src/jbg_ai/assist/constants.py
git log --oneline -S "placeholder" -- ai-service/src/jbg_ai/assist/verification.py

# --- §2.2: la frase es idéntica en v3 y en v4
sed -n '47p' ai-service/prompts/assist/v3.md
sed -n '59p' ai-service/prompts/assist/v4.md

# --- §2.2: v5 NO tiene la tarea del agente
grep -n "^## " ai-service/prompts/assist/v4.md ai-service/prompts/assist/v5.md

# --- §2.3: una reparación, con la lista entera
sed -n '24p;165,172p' ai-service/src/jbg_ai/assist/pitch.py

# --- §2.5: siete métodos, ninguno del agente
grep -n "Task<" backend/src/JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs

# --- D14: el breaker ve HttpResponseMessage, no el cuerpo
sed -n '186,205p' backend/src/JoiabagurPV.Application/Extensions/AiGatewayServiceCollectionExtensions.cs

# --- D15: el tope suma TODOS los turnos
grep -n -A 4 "_within_the_total_cap" ai-service/src/jbg_ai/api/schemas/assist.py
grep -n "MAX_TRANSCRIPT_TURNS\|MAX_TURN_CHARS\|MAX_TRANSCRIPT_CHARS" ai-service/src/jbg_ai/assist/constants.py

# --- §4.1: el guard degrada la recuperación; la etiqueta NO está guardada
sed -n '300,312p' ai-service/src/jbg_ai/retrieval/orchestrator.py
sed -n '870,893p' ai-service/src/jbg_ai/assist/tools.py

# --- §4.2: el puerto del arnés no mira el checkpoint
sed -n '204,211p' ai-service/src/jbg_ai/retrieval/ports.py
sed -n '490,505p' ai-service/src/jbg_ai/retrieval/search.py

# --- §4.4: el scheduler vive sólo en el lifespan; el sweep no drena
grep -n "run_scheduler" ai-service/src/jbg_ai/api/lifespan.py
grep -c "scheduler\|drain" ai-service/src/jbg_ai/evals/agent_sweep.py    # 0
sed -n '620,636p' ai-service/src/jbg_ai/config/settings.py               # 600 s vs 3.600 s

# --- §1: la sonda ya acepta la ausencia de tienda (C40_FIX)
grep -n "Guid? pointOfSaleId" backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs

# --- §6: la opción «todas» es de administrador; el selector, no
sed -n '186p;439p;452p' frontend/src/pages/sales/assisted.tsx
```

Y las cifras del §5, sobre el artefacto ya escrito, sin proveedor y sin base de datos:

```bash
cd ai-service
uv run --system-certs python - <<'PY'
import json, collections, statistics as st
d = json.load(open('evals/results/c32b-agent-sweep-293fe5c6e470.json', encoding='utf-8'))
rows = d['rows']
print('paced_seconds', d['provenance']['paced_seconds'], '| ceiling 3600')
for arm in sorted({r['arm'] for r in rows}):
    s = [r for r in rows if r['arm'] == arm]
    el = sorted(r['elapsed_ms'] for r in s)
    print(arm, 'p50=%d p95=%d max=%d partial=%d/%d' % (
        st.median(el), el[int(.95*len(el))-1], max(el),
        sum(1 for r in s if r['partial']), len(s)))
    print('  ', dict(collections.Counter(r['stop_reason'] for r in s)))
PY
```

---

## 14 · Resumen para `/enrich-us`

- **Doce decisiones del v1 siguen en pie**, con D5 y D6 matizadas por el §6 y D2 reemplazada por D13.
- **Cuatro decisiones nuevas**: D13 (`v6` sólo para el agente), D14 (circuito refutado), D15 (turno
  del asistente y 6 intercambios), D16 (una pasada, con instrumentos).
- **Cinco tramos**, con T0 nuevo y T2 gobernando.
- **Dos anotaciones** a informes publicados, ninguna obliga a rehacer.
- **Siete cifras** a publicar, de las que una ya está publicada aquí y otra es nueva y hace auditables
  al resto.
- **Lo que no se puede olvidar al escribir el ticket:** el contenedor `jbg-ai` arriba con el scheduler
  encendido durante la pasada. Es la diferencia entre medir el sistema y medir el sistema degradado, y
  ya falló una vez.
