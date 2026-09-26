# HU-AIENG-042: El agente de venta llega al operario — ruta propia, hilo de conversación con un bloque de respuesta por turno, traza visible y el argumentario que hoy se retira por construcción

## Formato estándar

**Como** Operador de un punto de venta,
**quiero** una pantalla de conversación donde pueda pedirle al asistente lo que el cliente me está
describiendo, verle encadenar búsquedas —buscar, comprobar si lo tenemos, ofrecer alternativas cuando
no—, leer su argumentario con las piezas rotuladas según si son lo que pedí o un sustituto, y poder
vender desde ahí,
**para** atender al mostrador sin tener que traducir yo lo que el cliente dice a los filtros de un
buscador, y para que el trabajo del agente —que está entregado, probado y medido desde C32b— deje de
ser algo que sólo existe en los tests.

---

## Descripción

Change OpenSpec `add-frontend-agent-panel` / **C42**, épica **EP15 — Venta Asistida, Sustitutos y
Agentes**. Prerrequisitos: **C32b** (el bucle del agente, sus seis herramientas congeladas y sus
presupuestos), **C34** (las rutas .NET de asistencia y el patrón de cliente con nombre propio), **C36**
(la ficha de venta asistida, de la que se reutiliza `pitch-block`), **C40** (el panel de consulta
libre, del que se reutiliza `assisted-search-result-row` entero y se copia el modelo de ámbito),
**C40_FIX** (que ya hizo que la sonda acepte la ausencia de punto de venta) y **C41** (sin cuyo
drenaje programado la pasada de medición de este change describiría el sistema degradado — ver
*Escenario 14*). Todos archivados.

**C42 no estaba en el plan.** Nace el 2026-09-26 al valorar la cola pendiente del Proyecto Final, en
una sesión abierta para decidir entre implementar C38 entero o dar superficie al agente. El motivo por
el que gana el segundo lo escribe el §5 de la convocatoria: *«el sistema debe poder probarse»*.

> **El agujero que cierra, dicho sin adornos.** De los cinco pilares que el Proyecto Final nombra
> —CAG, RAG, **agentes**, evaluación y despliegue—, el del agente es **el único sin superficie de
> operario**. `POST /v1/assist/agent` está entregado, probado y medido con proveedor real desde C32b, y
> **no lo llama nadie**: [`IAiGatewayClient`](../../../backend/src/JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs)
> tiene **siete** métodos —`SearchAsync`, `EnrichAsync`, `HealthAsync`, `SuggestFamiliesAsync`,
> `AuditFamiliesAsync`, `AssistSaleAsync`, `SubstitutesAsync`— y **ninguno es el suyo**. Sin pantalla,
> el pilar no puede aparecer ni en la URL pública ni en el vídeo de 2-3 minutos.

**Va antes de C38**, por la misma cadena de prompts que puso a C40 antes que a C38: aquí la tarea del
agente sube de `assist/v4` a una versión nueva, así que unas cifras de generación del agente tomadas
antes describirían un prompt sustituido.

### El agente no tiene M1, M2 ni M3, y conviene decirlo porque no es lo que se espera

Los tres modos son una propiedad de `/v1/assist/sale`, leída **estructuralmente** de qué anclas trae la
petición (`ai-service/src/jbg_ai/assist/modes.py`). `AgentAssistRequest`
(`ai-service/src/jbg_ai/api/schemas/assist.py:118`) **no lleva `product_id`, ni `query`, ni
`filters`**: lleva **`turns`**.

| | `/v1/assist/sale` (M1/M2/M3) | `/v1/assist/agent` |
|---|---|---|
| **Quién decide qué se recupera** | El **código**: el modo lo fija la forma de la petición | El **modelo**, entre seis herramientas, redactando sus propios argumentos |
| **Cuántos pasos** | **Uno.** Una recuperación, un argumentario | **Hasta cinco vueltas encadenadas** |
| **Unidad de entrada** | Una consulta suelta | Una **conversación** |

El agente **no necesita modos porque los descubre**. Y lo que **no** cambia es lo mejor del diseño de
C32b: **el bucle no escribe la respuesta**, sólo reúne evidencia. El argumentario lo redacta la misma
capa de generación, con la misma puerta numérica y la misma integridad referencial de citas. Por eso
`AgentAssistResponse` es **subclase** de `AssistResponse`: los mismos campos con el mismo significado,
**más cinco** —`partial`, `stop_reason`, `iterations`, `tool_calls_used`, `trace`— y
`agent_prompt_version`.

### El hallazgo que el v1 de la exploración puso en el centro, y que el v2 refuta con números

La exploración se hizo en **dos pasadas** el mismo día. La primera
([v1](../../Proyecto%20Final%20AIEng/informes/c42-exploration-decisions.md)) leyó código y encontró una
**regresión latente que C40 introdujo sin tocar el agente**, en tres eslabones correctos por separado:

1. El agente redacta con `assist/v4`, cuya sección *Sistema* ordena **sin condición**: *«El precio y la
   disponibilidad son siempre marcadores»* (`ai-service/prompts/assist/v4.md:59`).
2. Su payload es un `FreeQueryPayload` con `is_anchored = False`
   (`ai-service/src/jbg_ai/assist/prompt.py:453`) — correcto, porque el argumentario habla de **varias**
   piezas y un marcador no tendría contra qué resolverse.
3. C40 metió `placeholder_in_free_query` en `HARD_VIOLATION_CAUSES`
   (`ai-service/src/jbg_ai/assist/constants.py:339`), disparando exactamente cuando el payload **no**
   está anclado.

Juntos: **un argumentario del agente que obedezca a su propio prompt comete una violación dura.** El
v1 concluyó que sin arreglarlo *«C42 entrega un panel de agente sin prosa»* y que eso gobernaba la
línea de corte.

> **La segunda pasada ([v2](../../Proyecto%20Final%20AIEng/informes/c42-exploration-decisions-v2.md))
> lo refuta, y la evidencia estaba publicada en el propio repositorio.** La frase que ordena marcadores
> es **idéntica palabra por palabra** en `v3.md:47` y en `v4.md:59`, y la tarea del agente
> (`v4.md:132-166`) **no menciona precio ni stock**: hereda esa regla y nada más — exactamente la
> situación de las tareas libres bajo `v3`. **Así que C40 ya midió este caso**, con proveedor real,
> sobre 90 consultas libres con payload sin anclar: **`{{price}}` 2 veces, `{{stock}}` 1, en 3 de 90
> generaciones**, y `placeholder_in_free_query` **presente 3 veces en el primer intento y 0 tras la
> reparación**. **Cero de noventa argumentarios se retiraron por marcadores.**
>
> Y la cabecera de [`v5.md`](../../../ai-service/prompts/assist/v5.md) ya escribía por qué la
> extrapolación falla: *«anclado hay una pieza y se la vende, así que nombrar su precio es natural; en
> libre hay hasta quince agrupadas y lo que se pide es comparar»*. La referencia que el v1 usó —C30b,
> `{{price}}` en 147 de 213 y `{{stock}}` en 188 de 213— es de los modos **anclados**: **clase de
> referencia equivocada.**

**Consecuencia para esta historia:** el arreglo del prompt **entra igual** —el prompt pide lo que la
puerta prohíbe, y eso es un defecto— pero **no gobierna la línea de corte**. Lo que la gobierna es el
**consumidor .NET que no existe**: siete métodos y ninguno es el del agente, que es el **100 %** y no
el 3 %.

> **Y la causa que de verdad retira el argumentario del agente ya está medida, y no es el marcador.**
> Sobre las 204 filas del barrido de C32b: `dangling_citation` **85 en el primer intento y 72
> sobrevivientes** —la reparación arregla 13 de 85, un 15 %—, con una retirada del **13,1 %** en
> `gpt-4o`. Y **el 92,2 % de las respuestas traen cero citas**: la mayoría de las retiradas son
> identificadores inventados sobre un corpus que no se entregó.

### Lo que el sistema hace hoy, medido y no supuesto

Todo de `ai-service/evals/results/c32b-agent-sweep-293fe5c6e470.json` (204 peticiones, proveedor real,
2026-09-21), reagregado sin llamar al proveedor:

| | **`gpt-4o`** · el arm servido | `gpt-4o-mini` |
|---|---|---|
| Latencia p50 / p95 / máx | **5.311 / 9.021 / 11.917 ms** | 6.216 / 10.348 / 14.276 ms |
| `partial: true` | **2 de 102 · 2,0 %** | 60 de 102 · **58,8 %** |
| `presupuesto_tools` | **2** | **56** |
| Respuestas **sin ninguna pieza** | **20 · 19,6 %** | 20 · 19,6 % |
| Argumentario retirado | **13,1 %** | 16,0 % |

Cinco cosas que esto dice y que gobiernan el diseño de la pantalla:

- **Una de cada cinco respuestas no tiene ni una fila**, y es idéntico en los dos arms. Descompuesto:
  de las 20 por arm, **14 son repregunta o rechazo** y sólo **6 de 102 (5,9 %)** son «busqué y no
  encontré nada». **No es «sin resultados»: son estados normales de una conversación.**
- **`partial` sirve al 2,0 %** en el arm servido. La cinta de respuesta incompleta hace falta, pero es
  el último elemento por frecuencia, no el primero.
- **Las citas están vacías en el 92,2 %** y **los avisos en el 96,1 %**: los dos son la excepción.
- **El pivote es rutina y no anécdota**: `buscar_sustitutos` se invocó **125 veces**, y en los
  escenarios de `sin_existencias` pivotó **3 de 3 con `gpt-4o`**.
- **`gpt-4o-mini` no sirve para esta ruta**: quema el presupuesto de herramientas **56 veces contra 2**.

### Cuánta conversación cabe de verdad, y por qué la maqueta del v1 se quedaba corta

`AgentAssistRequest._within_the_total_cap` suma **todos** los turnos, incluidos los del asistente:

```python
total = sum(len(turn.text) for turn in self.turns)
```

Con `MAX_TRANSCRIPT_TURNS = 12`, `MAX_TURN_CHARS = 500` y `MAX_TRANSCRIPT_CHARS = 4_000`
(`ai-service/src/jbg_ai/assist/constants.py:739-741`). Y el argumentario del agente mide, sobre 141
generaciones: **mín 238, p50 386, p95 514, máx 605** caracteres. Reenviándolo como turno del asistente
—que es lo que hace que *«esa no la tenéis, ¿verdad?»* tenga antecedente—:

```
6 intercambios = 6 turnos operario + 6 turnos asistente = 12 turnos   ← TOPE DE TURNOS
caracteres:  6×25 + 6×386 (p50) = 2.466 / 4.000
             6×25 + 6×605 (máx) = 3.780 / 4.000   ← roza
```

**La conversación son seis intercambios, no doce.** Y un contador que cuente sólo lo que el operario
escribió llega a *«turno 9/12»* con el **422 ya disparado**, que es precisamente la avería que el
contador existe para evitar.

### Alcance de esta historia (sí)

**Tramo 0 · Instrumentos de medición** — *nuevo, y va antes de cualquier tarea funcional*

1. **Contador de marcadores en `agent_sweep.py`**: `{{price}}` y `{{stock}}` por fila, agregados en el
   resumen. **Hoy no existe** —cero apariciones de `placeholder` en ese fichero—, y sin él la cifra que
   el change tiene que publicar no se puede tomar.
2. **Antigüedad de la proyección en la procedencia y por fila**: `projection_synced_at()` al arrancar y
   en cada fila, con `age_seconds` y `stale` contra `jpv_pos_projection_max_age_seconds`. Sin esto la
   pasada de C42 es tan inauditable como la de C32b.
3. **Precondición de runbook comprobada y anotada**: contenedor `jbg-ai` arriba con
   `JPV_POS_SYNC_SCHEDULER_ENABLED=true`, verificada en `/health` antes de arrancar la pasada.

**Tramo 1 · `ai-service`**

4. **`AgentAssistGroup(AssistGroup)` gana `origin`** (`catalogo` / `sustitutos`). **Va primero** del
   tramo: con 125 invocaciones de `buscar_sustitutos`, rotular el origen es lo que más veces impide que
   la pantalla mienta. Subclase y no campo en el modelo compartido, por el precedente exacto de
   `AgentUsage`. **Adición pura**, mueve `openapi.json`.
5. **La tarea del agente sube a `assist/v6`**, un fichero nuevo que lleva el *Sistema* de `v5` y **una
   sola tarea**, con la prohibición de marcadores que `v5` ya escribe. `AGENT_PITCH_PROMPT_VERSION`
   pasa a `assist/v6`; **`PROMPT_VERSION` no se toca**. Test de que la sección *Sistema* de `v6` es
   **idéntica** a la de `v5`.
6. **La ruta del agente acepta token con y sin punto de venta**: `get_unscoped_principal` en lugar de
   `get_service_principal`, copiando literalmente lo que C40 hizo con `/v1/assist/sale`. El resto de
   rutas de una sola tienda —sustitutos, inventario— **intactas**.

**Tramo 2 · `backend` — el que gobierna**

7. **Método en `IAiGatewayClient`** y su implementación, con **cliente con nombre propio** `ai-agent`:
   presupuesto de **18 s**, sin reintento salvo conexión nunca abierta, `HttpClient.Timeout` infinito y
   el presupuesto en el *pipeline*.
8. **El circuito NO cuenta `stop_reason=fallo_proveedor`**, y se declara por qué. Ejecuta la entrada de
   `DEFERRED_TASKS.md` **refutándola**.
9. **DTO** = el `FreeQuerySearchResponse` de C40 **más** `partial`, `stopReason`, `iterations`,
   `toolCallsUsed`, `trace` y `agentPromptVersion`. Hidratación por `AssistedSearchResultDto`, que **ya
   cubre todos los miembros de todos los grupos**.
10. **Validación de los tres topes del transcript en .NET**, para no delegar el 422 a Python.
11. **`agentAvailable` en la sonda** — sólo el tercer interruptor: que acepte la ausencia de tienda **ya
    lo cerró C40_FIX**.
12. **Quinto `SearchOrigin`** para la selección desde el agente, sin migración.

**Tramo 3 · `frontend` — la pantalla, ordenada por frecuencia medida**

13. **Ruta `/sales/new/agent` y cuarta tarjeta** en el hub `/sales`, con la **puerta cerrada antes de
    entrar** y sus tres estados.
14. **El hilo como eje**: un bloque de respuesta por turno, anclado, con sus grupos, citas, traza y
    estado de parada. Sólo la última abierta.
15. **Compositor con los contadores del transcript real**, incluidos los turnos del asistente.
16. **El bloque de respuesta sin filas primero** (19,6 %), después con filas.
17. **Castellano de los diez `stop_reason`**, traducidos enteros y **nunca inferidos de los contadores**.
18. **La traza**, pintada como escalera de pasos: el único componente genuinamente nuevo.
19. **La cinta de `partial`** — la última, porque sirve al 2,0 %.

**Tramo 4**

20. **Contador de coste acumulado de la sesión** en la barra fija. Va el último porque es el único que
    no arregla nada que hoy engañe.

### Fuera de alcance (no)

- **El *streaming* / SSE del argumentario.** Con p95 de 9,0 s la tentación es real; queda fuera por la
  misma razón que quedó fuera de C40, y la mitigación es el estado de espera con la traza al final.
- **Preguntar por el stock de una tienda concreta, o de varias a la vez.** Ninguna de las seis tools
  acepta punto de venta —`_SkuArgs` es `sku` con `extra="forbid"`— y `ai-service/src/jbg_ai/api/auth.py:27`
  escribe el motivo: *«un `pos_id` comodín es exactamente lo que nunca debe existir»*. Habilitarlo
  exige una tabla de qué tiendas ve cada usuario. **No es una tool más: es un cambio de modelo de
  autorización.**
- **El desglose de `usage` por etapa.** Sólo entra si el contador de coste del tramo 4 lo necesita.
- **La telemetría de la ficha** y el **registro de la consulta de ámbito global**, que arrastran
  migración de EF Core. Siguen en `openspec/DEFERRED_TASKS.md`.
- **Los escenarios puntuados del agente**, que son de C38.
- **La recalibración del presupuesto de herramientas**, aunque la exploración mida que el efectivo es
  **6 y no 8** —nunca se observó 7 ni 8, porque con 4 llamadas concurrentes el bucle para cuando la
  siguiente tanda cruzaría el tope—. Se declara y se deja.
- **Una segunda pasada de medición.** Se toma **una sola**, después del cambio, con la línea base
  prestada de C40 y declarada.
- **Limpiar retroactivamente las cifras de recuperación de C32b.** No se puede: se anotan.
- **Añadir una séptima herramienta.** Las seis están congeladas, y las dos ausencias
  —`perfil_punto_venta` y `buscar_complementarios`— son deliberadas y tienen test que las nombra.

### Decisiones de diseño ya acordadas

Doce vienen del v1 de la exploración; cuatro se cerraron en la segunda pasada.

| # | Decisión | Por qué |
|---|---|---|
| **D1** | Ruta propia `/sales/new/agent` y cuarta tarjeta en el hub | Colgarlo de la ficha forzaría el contrato (el agente no acepta `product_id`); un toggle dentro del panel de C40 pondría **dos interruptores de nombre parecido** en la misma pantalla, que es la clase de avería que C40 nació para arreglar. Y la ablación se lee mejor: la misma pregunta en los dos paneles es comparable a simple vista |
| **D2 → D13** | La tarea del agente sube a **`assist/v6`**, no a `v5` | Ver D13 |
| **D3** | `AgentAssistGroup(AssistGroup)` gana `origin` | Precedente exacto de `AgentUsage`: el modelo compartido es lo que publica `/v1/assist/sale`, y ensancharlo movería el esquema de esa ruta. Adición pura |
| **D4** | La ruta del agente acepta token con y sin punto de venta | Copia literal de lo que C40 hizo con `/v1/assist/sale`: la ausencia es **no aplicar el prefiltro**, nunca un comodín |
| **D5** | La autorización del ámbito global se copia de C40 **sin endurecerla** | Dos paneles hermanos con dos reglas de autorización distintas se rompen sin que falle ningún test |
| **D6** | El ámbito por defecto es la tienda del operario, y abrir a todas **lo dice** | Sin `pos_id` la etiqueta es siempre `AVAILABILITY_NO_SCOPE`, nunca `sin_existencias`, y **el pivote no se dispara nunca**. No es estética: es una capacidad que se pierde |
| **D7** | La puerta se cierra **antes** de entrar; `partial` se pinta **dentro** | `sin_cliente` se sabe antes de gastar nada; `fallo_proveedor` a mitad del bucle, con herramientas ya ejecutadas. Y fallar la sonda **no puede cerrar una puerta que quizá funciona** |
| **D8** | La sonda gana `agentAvailable` | El agente tiene **cadena de credencial propia** —agente → assist → enriquecimiento—, así que la sonda diría «la asistida está encendida» mientras cada petición del agente vuelve con `sin_cliente` |
| **D9** | El hilo es el eje: cada turno es dueño de su bloque | Un panel fijo que se refresca deja al operario leyendo el argumentario del turno 2 con las filas del turno 3 debajo — y **cuando el bucle pivota, la pieza que miraba desaparece sin explicación**, que es justo lo que el agente existe para demostrar |
| **D10** | La traza se pinta, y es el único componente nuevo | Es la única prueba en pantalla de que hay un agente y no un prompt. **Nunca argumentos ni contenido de observaciones**: el contrato los excluye por regla |
| **D11** | Los diez `stop_reason` se traducen enteros, y **no se infieren de los contadores** | *«Cinco iteraciones no dice si la quinta fue la última necesaria o la que se agotó, y son afirmaciones opuestas sobre la respuesta que se está leyendo»* |
| **D12** | Quinto `SearchOrigin` para la selección desde el agente | Sin él, una venta originada en el agente es indistinguible de una originada en el panel, y la ablación vuelve a ser una demostración en pantalla en vez de un dato |
| **D13** | **`assist/v6` sólo para el agente; `v5` queda intacto** | `v5` **no contiene** la tarea del agente y su cabecera declara que *«todas las versiones se conservan en disco… cada una tiene cifras medidas contra ella»*. Editarlo haría que su fila de la tabla mienta **justo cuando C38 va a medir `v5`**. Un `v6` completo con las dos constantes fusionaría dos versiones deliberadamente apartadas y obligaría a rehacer la comparación de C40. El riesgo de C —deriva entre los dos *Sistema*— se cierra con un test |
| **D14** | **`fallo_proveedor` es métrica, no entrada del circuito** | Dos documentos del repositorio se contradicen: `DEFERRED_TASKS.md` pide contarlo y el *pipeline* de `ai-assist` declara lo contrario. **Y la aritmética decide**: ~13.000 tokens por petición contra 25.000 TPM = **una petición por minuto**, así que un cortafuegos con `MinimumThroughput` **no se abrirá nunca** — la ventana de muestreo expira antes de acumular la muestra. Quien avisa a la pantalla es la sonda |
| **D15** | Turno del asistente con el **argumentario íntegro**, **6 intercambios**, **línea sintética** si se retiró | El contrato autoriza la línea sintética al declarar el rol: *«`asistente` is attributed and never trusted»*. Y el contador cuenta **el transcript que se va a enviar**. Enviar sólo los turnos del operario daría 12 intercambios pero rompería *«esa no la tenéis»*, que es el vídeo entero |
| **D16** | **Una sola pasada** de medición, después del cambio | El efecto esperado es ~0 y el análogo ya está medido. Dos pasadas cuestan ~5 h 30 min de reloj a una petición por minuto. La línea base se **presta de C40 y se declara** |

### El hallazgo de C41 tiene una segunda vida en el arnés, y es peor

C41 anotó que la manipulación del §8 del informe de C40 se aplicó a `ai.pos_projection.refreshed_at`
cuando el guard lee `ai.sync_checkpoint.last_incremental_sync_at`. **En el arnés del agente no hay
columna equivocada: no hay ninguna comprobación, y los dos caminos leen cosas distintas.**

| | Arnés (`agent_sweep`) | Camino de servicio |
|---|---|---|
| Qué llama | `search.scope_buckets(MAO_AIR)` | `resolve_scope()` → `projection_synced_at()` |
| Dónde | `retrieval/search.py:490-499` | `retrieval/orchestrator.py:282-305` |
| Guard de rancidez | **ninguno.** `ports.py:204` lo declara *«Read by the evaluation only»* | **sí**, y al pasarse degrada a `degraded=unscoped` |

**Así que el arnés resuelve fixtures perfectos por rancia que esté la proyección, mientras el camino
que mide sirve sin ámbito.** Y la aritmética condena parte de la pasada de C32b: duró **2 h 44 min**
(`paced_seconds: 9.870,8`) contra un techo de **1 h**, el arreglo manual *«caduca en una hora»* y el
drenaje automático **no existía** —es de C41, cinco días posterior—. **A lo sumo las primeras ~74 de
204 filas corrieron con el prefiltro aplicado**, y es cota superior.

> **Lo que sobrevive, y hay que decirlo porque parecería caer con el resto.** `consultar_disponibilidad`
> lee `availability_bucket` **directamente, sin pasar por el guard**
> (`ai-service/src/jbg_ai/assist/tools.py:873`), y la antigüedad **viaja al modelo** como
> `antiguedad_proyeccion_segundos` con la regla escrita: *«degrade, never remove»*. **Así que el pivote
> 3 de 3 en `sin_existencias` con `gpt-4o` se sostiene, y con él la justificación de D6.** Lo que queda
> como no medido son **grupos por respuesta y saturación al tope**, que es exactamente lo que el
> prefiltro cambia: 1.168 candidatos contra los 416 del surtido.

### Referencias

- **Informe de exploración v2 (el que gobierna):**
  [c42-exploration-decisions-v2.md](../../Proyecto%20Final%20AIEng/informes/c42-exploration-decisions-v2.md)
- **Informe de exploración v1 (base, no sustituido):**
  [c42-exploration-decisions.md](../../Proyecto%20Final%20AIEng/informes/c42-exploration-decisions.md)
- **Ficha del plan:** [§3 · C42](../../Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Diseño RAG:** [proyecto-final-diseno-rag-joiabagur.md](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Ticket:** [T-AIENG-042](../../../openspec/changes/archive/2026-09-27-add-frontend-agent-panel/ticket.md)
- **Specs vivas que el change modifica:**
  [`sales-assistant-agent`](../../../openspec/specs/sales-assistant-agent/spec.md) ·
  [`assist-generation`](../../../openspec/specs/assist-generation/spec.md) ·
  [`ai-gateway-client`](../../../openspec/specs/ai-gateway-client/spec.md) ·
  [`ai-free-query-search`](../../../openspec/specs/ai-free-query-search/spec.md) ·
  [`ai-search-telemetry`](../../../openspec/specs/ai-search-telemetry/spec.md)
- **Specs que NO se tocan, y es alcance:**
  [`sales-assistant-tools`](../../../openspec/specs/sales-assistant-tools/spec.md) ·
  [`ai-sales-assist`](../../../openspec/specs/ai-sales-assist/spec.md) ·
  [`assisted-search-panel`](../../../openspec/specs/assisted-search-panel/spec.md) ·
  [`pos-projection`](../../../openspec/specs/pos-projection/spec.md)
- **Historias anteriores:** [HU-AIENG-032b](HU-AIENG-032b.md) · [HU-AIENG-034](HU-AIENG-034.md) ·
  [HU-AIENG-036](HU-AIENG-036.md) · [HU-AIENG-040](HU-AIENG-040.md) ·
  [HU-AIENG-040-FIX](HU-AIENG-040-FIX.md) · [HU-AIENG-041](HU-AIENG-041.md)
- **Deuda que cierra:** [`DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md), entrada de C32b
  sobre la política de *timeout* y de circuito — **cerrada por refutación**
- **Informes a anotar:**
  [c32b-implementation-measurements.md](../../Proyecto%20Final%20AIEng/informes/c32b-implementation-measurements.md)
- **Componentes a reutilizar:**
  [`assisted-search-result-row.tsx`](../../../frontend/src/components/sales/assisted-search-result-row.tsx) ·
  [`pitch-block.tsx`](../../../frontend/src/components/sales/sales-assist-card/pitch-block.tsx) ·
  [`search-route-toggle.tsx`](../../../frontend/src/components/sales/search-route-toggle.tsx)
- **Testing:** [testing-backend.md](../../testing-backend.md) · [testing-frontend.md](../../testing-frontend.md)

---

## Criterios de Aceptación

### Escenario 1: La puerta se abre cuando el agente está disponible

**Dado que** soy un operador autenticado con una tienda asignada
**Y** la sonda de disponibilidad responde que la respuesta asistida y el agente están encendidos
**Cuando** abro el hub de venta `/sales`
**Entonces** veo una **cuarta tarjeta** para el modo agente, activa
**Y** al pulsarla llego a `/sales/new/agent` con el ámbito **preseleccionado en mi tienda**
**Y** la barra fija advierte de que es el modo agente y del tiempo típico de respuesta.

### Escenario 2: La puerta se cierra con el motivo cuando el agente está apagado

**Dado que** la sonda responde que el agente **no** está disponible
**Cuando** abro el hub de venta
**Entonces** la cuarta tarjeta aparece **deshabilitada y con el motivo escrito**, igual que ya hace
`SearchRouteToggle` con su lado semántico
**Y** el motivo **no** es el de la respuesta asistida cuando lo que falta es la credencial del agente
**Y** no se ha gastado ni una llamada al proveedor para averiguarlo.

### Escenario 3: Una sonda que no contesta no cierra una puerta que quizá funciona

**Dado que** la sonda de disponibilidad falla o devuelve un estado desconocido
**Cuando** abro el hub de venta
**Entonces** la cuarta tarjeta aparece **activa, con un aviso** de que no se ha podido confirmar la
disponibilidad
**Y** nunca deshabilitada, que es la regla que C40 ya escribió para su insignia.

### Escenario 4: Una conversación de catálogo pinta prosa y filas rotuladas

**Dado que** estoy en el panel del agente con mi tienda como ámbito
**Cuando** escribo «algo de plata para regalar a mi madre» y envío
**Entonces** aparece un **bloque de respuesta anclado a ese turno** con el argumentario en prosa
**Y** las filas van bajo un rótulo de **Coincidencias**, porque su grupo declara `origin: catalogo`
**Y** cada fila usa `assisted-search-result-row` **sin modificar**, con su nombre, precio, existencias
de mi tienda, foto, botón de vender y botón de abrir ficha
**Y** la tira de estado del bloque dice el motivo de parada, las vueltas y las herramientas usadas.

### Escenario 5: El pivote a sustitutos se lee como lo que es

**Dado que** he preguntado por una pieza que mi tienda no tiene
**Cuando** el bucle consulta la disponibilidad y pivota a sustitutos
**Entonces** el bloque pinta **dos grupos separados y rotulados**: *Coincidencias* para
`origin: catalogo` y **Alternativas** para `origin: sustitutos`
**Y** las alternativas **nunca** se presentan como si fueran lo que se había pedido
**Y** la traza muestra la escalera: buscar → consultar disponibilidad → buscar sustitutos.

### Escenario 6: Una respuesta con prosa y cero piezas no es «sin resultados»

**Dado que** estoy en el panel del agente
**Cuando** pregunto «¿el baño de oro se puede mojar?» y el agente responde apoyándose en el corpus
**Entonces** el bloque pinta **el argumentario y sus citas, con cero filas**
**Y** **no** se muestra el vacío de «no se han encontrado piezas», porque no es un vacío
**Y** cuando el corpus no entregó fragmentos, la lista de citas viene vacía y **eso también es normal**
—ocurre en el 92,2 % de las respuestas medidas—.

### Escenario 7: Una repregunta devuelve el foco a la caja

**Dado que** he escrito «quiero un regalo», sin más contexto
**Cuando** el agente decide pedir una aclaración
**Entonces** el bloque pinta **sólo la repregunta**, con `stop_reason` traducido como aclaración
**Y** el foco vuelve a la caja del compositor
**Y** el bloque **no** pinta el estado de vacío ni un color de alarma.

### Escenario 8: Una respuesta cortada por presupuesto se distingue de una completa

**Dado que** una petición agota uno de los presupuestos del bucle
**Cuando** la respuesta llega con `partial: true`
**Entonces** el bloque pinta una **cinta de respuesta incompleta que nombra el presupuesto agotado**
**Y** la cinta **no** es un error ni usa color de alarma: la evidencia reunida sigue siendo útil
**Y** el motivo sale del `stop_reason` traducido y **nunca se infiere de los contadores de vueltas o de
herramientas**.

### Escenario 9: Los topes del transcript se dicen antes de que la petición se rechace

**Dado que** llevo cinco intercambios en el hilo, con sus cinco argumentarios del asistente
**Cuando** miro el compositor
**Entonces** los contadores reflejan **el transcript que se va a enviar**, turnos del asistente
incluidos — del orden de `turnos 10/12 · 2.100/4.000 caracteres`
**Y** al alcanzar cualquiera de los tres topes el compositor **se cierra con su motivo**
**Y** en ningún momento se envía una petición que .NET o Python vayan a rechazar con 422.

### Escenario 10: Un argumentario retirado no rompe el hilo

**Dado que** el argumentario de un turno se retiró por la puerta de integridad
**Cuando** ese turno queda en el hilo y envío el siguiente
**Entonces** el bloque de ese turno dice que no hubo argumentario, **con su motivo y sin inventarlo**
**Y** el turno del asistente que viaja en la petición lleva una **línea sintética** que nombra las
piezas por SKU en lugar de un texto vacío
**Y** la petición no falla por un turno de longitud cero.

### Escenario 11: Cambiar de ámbito reinicia el hilo, y se avisa antes

**Dado que** soy administrador, tengo una conversación en curso sobre una tienda
**Cuando** cambio el ámbito a otra tienda o a «todas las tiendas»
**Entonces** la interfaz **avisa antes** de que la evidencia previa se reunió en otro ámbito y que el
hilo se reinicia
**Y** al seleccionar «todas las tiendas» la línea de consecuencia dice **que el agente deja de ofrecer
alternativas**, porque sin punto de venta la etiqueta de disponibilidad no puede valer
`sin_existencias`
**Y** el ámbito permanece **fijo durante toda la conversación**.

### Escenario 12: La ruta del agente deja de exigir punto de venta

**Dado que** un token válido **no** lleva la reclamación de punto de venta
**Cuando** se llama a `POST /v1/assist/agent`
**Entonces** la petición **se sirve**, y la ausencia significa **no aplicar el prefiltro** y nunca un
comodín
**Y** las demás rutas de una sola tienda —sustitutos e inventario— **siguen rechazando la omisión**,
con su test intacto.

### Escenario 13: El argumentario del agente deja de escribir marcadores

**Dado que** la tarea del agente se sirve con `assist/v6`
**Cuando** el agente redacta un argumentario sobre varias piezas sin ancla
**Entonces** el texto **no contiene `{{price}}` ni `{{stock}}`**
**Y** puede usar lenguaje comparativo —«el más asequible de los tres»— sin nombrar cifras
**Y** la sección *Sistema* de `assist/v6` es **idéntica** a la de `assist/v5`, comprobado por test
**Y** `assist/v5` **no se ha modificado**, y `PROMPT_VERSION` sigue apuntando a él.

### Escenario 14: La pasada de medición mide el sistema y no su desconfiguración

**Dado que** voy a tomar la pasada de medición del agente
**Cuando** la arranco
**Entonces** el contenedor `jbg-ai` está levantado con el drenaje programado de C41 encendido,
verificado en `/health`
**Y** el artefacto registra la **antigüedad de la proyección** al empezar y en cada fila, con su
indicador de rancidez
**Y** una fila tomada con la proyección rancia queda **identificable después**, en lugar de promediarse
con las demás
**Y** el artefacto se persiste con `run_id`, `git_sha` y `prompt_version`.

### Escenario 15: El circuito no se abre por una ruta que funciona como está diseñada

**Dado que** el proveedor del modelo está caído
**Cuando** `POST /v1/assist/agent` responde **200 con `partial: true`** y
`stop_reason=fallo_proveedor`
**Entonces** el cortocircuito del cliente `ai-agent` **no** cuenta esa respuesta como fallo
**Y** `fallo_proveedor` queda registrado como **métrica y log**
**Y** el cliente `ai-agent` usa **su propio presupuesto de tiempo** y no el de `ai-assist`.

### Escenario 16: Fuera de alcance explícito — ni *streaming*, ni stock por tienda, ni séptima herramienta

**Dado que** C42 queda implementado y verificado
**Cuando** se revisa lo entregado
**Entonces** el argumentario **no** llega por SSE ni token a token
**Y** ninguna herramienta acepta un punto de venta como argumento
**Y** las herramientas siguen siendo **seis**, con sus dos ausencias deliberadas
**Y** no se ha creado ninguna migración de EF Core ni de Alembic
**Y** `assisted-search-result-row` y `pitch-block` **no se han modificado**.

---

## Notas adicionales

- **Actor principal:** Operador de punto de venta. El **Administrador** es actor secundario y es el
  único que puede elegir el ámbito «todas las tiendas», por la regla que C40_FIX fijó con test
  (`frontend/src/pages/sales/assisted.tsx:186`, `canScopeToAllPointsOfSale = isAdmin`). El backend sí
  sirve ese ámbito a operadores, y esa asimetría **se conserva tal cual**: la frontera que se protege
  es más fina —no se puede nombrar una tienda no asignada— y ya tiene sus dos tests.
- **El agente no se sirve por defecto, y eso es criterio y no cautela.** Su única cifra comparativa
  hoy dice **×3,0 de coste** y **13,1 % de retirada** contra el 2,2 % de la ruta determinista. Servir
  eso por defecto a un joyero sería mala ingeniería; como **ruta propia y demostración de ablación**
  la misma cifra pasa de penalización a decisión justificada.
- **Dos estados de la pantalla no se han observado nunca.** Cero `fallo_proveedor` y cero `sin_cliente`
  en 204 filas: la interfaz se construye para dos estados que hoy sólo existen en test. Se declara.
- **Limitación heredada y no reabierta:** una consulta de **ámbito global no se registra** en
  telemetría, porque `ProductSearchEvent.PointOfSaleId` es no nulo e indexado y registrarla exige
  migración de EF Core. Está en `openspec/DEFERRED_TASKS.md` desde C40.
- **El contrato congelado se mueve**, por `origin`. Es adición pura, y
  `test_openapi_snapshot_is_stable` tiene mecanismo declarado de adiciones permitidas: *«The next
  change that moves the contract replaces this fixture and the allowed additions below,
  deliberately»*. C40 fue ese change; **C42 es el siguiente**.
- **Change de OpenSpec por el que se implementa:** `add-frontend-agent-panel`, en la rama
  `c42-add-frontend-agent-panel`, derivada de `ai-eng`.

---

## Tareas

Ordenadas por tramo, con el criterio de C40: **primero lo que impide que la pantalla diga la verdad**;
y con el tramo 0 delante, porque medir exige tener el instrumento.

1. **Tramo 0 · instrumentos.** Contador de marcadores en `agent_sweep.py`; antigüedad de la proyección
   en la procedencia y por fila; precondición de runbook comprobada en `/health`.
2. **Tramo 1 · `ai-service`.** `origin` en `AgentAssistGroup`; `assist/v6` con la tarea del agente y su
   test de no-deriva; `get_unscoped_principal` en la ruta; regenerar `openapi.json` y sustituir el
   *fixture* del snapshot con sus adiciones permitidas.
3. **Tramo 2 · `backend`.** Método en `IAiGatewayClient` e implementación; cliente con nombre `ai-agent`
   y su *pipeline*; DTO del agente y hidratación; validación de los tres topes; `agentAvailable` en la
   sonda; quinto `SearchOrigin`; servicio de aplicación y endpoint.
4. **Tramo 3 · `frontend`.** Tipos y servicio; ruta y cuarta tarjeta con sus tres estados; hilo y
   compositor con los contadores del transcript real; bloque de respuesta —sin filas primero—; tabla de
   copy de los diez `stop_reason` y de los avisos; traza; cinta de `partial`.
5. **Tramo 4.** Contador de coste acumulado en la barra fija.
6. **Medición.** Una pasada con `gpt-4o`, artefacto persistido, y las siete cifras del informe
   publicadas.
7. **Specs y documentación.** Deltas de las capabilities afectadas; `openspec validate --all --strict`
   en verde; las **dos anotaciones** a informes publicados; `Documentos/` al día.

---

## Estimaciones y atributos de priorización

| Atributo | Valor |
|---|---|
| Puntos de historia | _Pendiente_ — a fijar en refinamiento |
| Impacto en usuario / valor de negocio | **5/5** — da superficie al **único de los cinco pilares del Proyecto Final que no la tiene**. Sin esto el pilar de agentes no puede aparecer ni en la URL pública ni en el vídeo, y la convocatoria pide que el sistema **pueda probarse** |
| Urgencia | **5/5** — es el **primero de los tres pendientes** y bloquea a C38: aquí la tarea del agente sube de versión, así que unas cifras de generación tomadas antes describirían un prompt sustituido |
| Complejidad / esfuerzo | **4/5** — **tres capas y el contrato se mueve**, igual que C40. Lo que lo abarata: el bucle está entregado y medido, `assisted-search-result-row` se reutiliza **entero**, `pitch-block` también, y la hidratación de .NET ya cubre todos los miembros de todos los grupos. Lo que lo encarece: el hilo y el bloque por turno no tienen precedente en el repositorio, y la traza es el único componente genuinamente nuevo |
| Riesgos | **El instrumento antes que la medida**: si el tramo 0 se salta, la pasada sale inauditable y se repite el error que C41 anotó sobre C40. **La pasada cuesta 2 h 44 min de reloj** a una petición por minuto, y exige el contenedor arriba con el drenaje de C41. **La deriva entre los dos `Sistema`** de `v5` y `v6` (mitigada con test). **Dos estados de pantalla sin observar nunca** (`fallo_proveedor`, `sin_cliente`). **El hilo puede crecer mucho**: hasta seis bloques con filas cada uno, y el tope del contrato son 8 piezas por respuesta — de ahí que sólo la última quede abierta. **`openapi.json` se mueve**, así que hay que acordar el cambio con quien consume el contrato antes de regenerarlo |
| Dependencias | **C32b, C34, C36, C40, C40_FIX y C41** archivados. **C41 no es opcional**: sin su drenaje programado la pasada mide el sistema degradado. **Bloquea a C38.** No debe abrirse a la vez que ningún change que toque `assist/` o `retrieval/` |

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| **Q-1** | ¿El fichero nuevo se llama `assist/v6.md` o `assist/v5-agent.md`? | **`assist/v6.md`**, siguiendo la serie que la tabla de versiones ya numera. Un sufijo rompería el orden y la tabla es el índice |
| **Q-2** | ¿El presupuesto del cliente `ai-agent` son 18 s o 15 s? | **18 s.** 15 dejan 3,1 s sobre el máximo observado (11.917 ms) y el modo de fallo es cortar una petición que Python ya pagó entera. Se declara como opción propia, `AssistTimeoutMs` no se toca |
| **Q-3** | ¿La línea sintética del turno del asistente lleva los SKU o sólo un texto genérico? | **Con los SKU**, para que la referencia deíctica del turno siguiente tenga antecedente. Es el único motivo por el que el turno se envía |
| **Q-4** | ¿La traza se pinta colapsada o abierta en el último bloque? | **Colapsada, con el número de vueltas visible en la tira de estado.** Es prueba de mecanismo, no información de venta |
| **Q-5** | ¿La cuarta tarjeta del hub lee la sonda al montar o al pulsar? | **Al montar**, como ya hace el panel de C40: la sonda no gasta cupo ni llamada al proveedor, y ése es el motivo de que exista |
| **Q-6** | ¿El contador de coste del tramo 4 necesita el desglose de `usage` por etapa? | **No.** Se pinta el agregado que `AgentUsage` ya publica. El desglose queda fuera de alcance y sólo entra si el contador resulta insuficiente |
| **Q-7** | ¿El panel del agente ofrece el ámbito «todas las tiendas»? | **Sí, sólo al administrador**, copiando C40 sin endurecerlo (D5), y con la línea de consecuencia de D6 diciendo que el pivote se apaga. La alternativa —no ofrecerlo— queda **declarada y descartada** en el informe |
| **Q-8** | ¿Se crea una capability nueva para el panel del agente o se amplía `assisted-search-panel`? | **Capability nueva.** `assisted-search-panel` describe *una consulta → resultados* y el agente es *una conversación*; ampliarla haría que sus requisitos hablaran de dos pantallas distintas, que es la clase de spec que miente sin romper el validador |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
añada ruta bajo `/v1`, **no** modifique `assist/v5` ni `PROMPT_VERSION`, **no** toque las seis
herramientas, **no** abra migración de EF Core ni de Alembic, **no** modifique
`assisted-search-result-row` ni `pitch-block`, y **no** cambie el comportamiento de degradación ante
una proyección rancia.
