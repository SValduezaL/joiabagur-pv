# C42 — informe de implementación: el agente llega al operario, y las trece cosas que se refutaron por el camino

**Change:** `add-frontend-agent-panel` · **Rama:** `c42-add-frontend-agent-panel` sobre `ai-eng`
**Artefactos de partida:** `946eb42` (specs y tareas) · **Implementación:** 2026-09-26
**Épica:** EP15 — Venta Asistida, Sustitutos y Agentes

---

## 0 · Qué se entregó, en una frase

El agente de venta —`POST /v1/assist/agent`, entregado y medido con proveedor real desde C32b y al
que **no llamaba nadie**— tiene pantalla: ruta propia `/sales/new/agent`, cuarta tarjeta en el hub de
venta, y un hilo de conversación donde **cada turno es dueño de su bloque de respuesta**, con los
grupos rotulados por procedencia, la traza de llamadas visible y los diez motivos de parada en
castellano. Por el camino su argumentario deja de retirarse por construcción.

**Sin ruta nueva bajo `/v1`, sin migración de EF Core ni de Alembic, sin séptima herramienta, y sin
tocar `assist/v5`, `assist/v4` ni los dos componentes de frontend que se reutilizan.** Comprobado
fichero a fichero en el §6.

---

## 1 · La puerta de entrada: las tres líneas base, y un desvío que no estaba escrito

### 1.1 · Las líneas base, por nombres

| Suite | Línea base sobre `c81c3fa` | Al cerrar | Veredicto |
|---|---|---|---|
| `dotnet test` | **53 rojos de 1.347** | **46 rojos de 1.401** | +54 tests, el rojo **baja 7** |
| `npm run test` | **113 rojos de 854**, 14 ficheros | **113 rojos de 953**, 14 ficheros | +99 tests, **el mismo recuento de rojos** |
| `uv run pytest` | **1.649 verde** | **1.659 verde, 0 rojos** | +10 tests, verde |

**Cero nombres rojos nuevos en el área propia** en las tres. En backend los cuatro nombres que
aparecen —tres de `InventoryIntegrationTests` y uno de `ReturnsControllerTests`— y los once que
desaparecen —todos de `InventoryIntegrationTests`— caen exactamente en las clases que `CLAUDE.md`
documenta como rotatorias entre pasadas del mismo commit. En frontend el único nombre nuevo de la
primera comparación **era una regresión propia**, corregida y contada en el §5.4.

### 1.2 · El desvío que no estaba escrito: **las tres suites no se pueden medir en paralelo**

La primera medición lanzó las tres a la vez y el backend dio **490 rojos de 1.347**. No era
regresión. La causa, leída en los propios rastros de pila:

```text
System.TimeoutException : The operation has timed out.
   at System.IO.Pipes.NamedPipeClientStream.ConnectInternal(...)
   at Docker.DotNet.DockerClient...
```

`vitest` con 14 *workers* saturó la máquina y **testcontainers no alcanzó el demonio de Docker por su
tubería con nombre**, así que todos los `IntegrationTests` fallaron al arrancar. En serie, el mismo
commit da **53**. Los dos rojos que `pytest` dio en esa misma pasada
—`test_the_wall_clock_budget_stops_the_loop` y
`test_several_tool_calls_of_one_turn_run_concurrently_rather_than_in_sequence`— son los dos tests de
reloj del agente, y **solos pasan**: 49 de 49.

> **Va al inventario de trampas del repositorio.** `CLAUDE.md` documenta que el recuento del backend
> es inestable y que se compara por nombres; lo que no documentaba es que **medir concurrentemente lo
> multiplica por nueve**, y que el modo de fallo no se parece a una regresión sino a un desastre. Una
> pasada de las tres suites es **serial**, y el coste es de unos 20 minutos.

### 1.3 · Las cinco afirmaciones que dimensionaban el change: **las cinco confirmadas**

| Afirmación | Comprobación |
|---|---|
| `IAiGatewayClient` tiene siete métodos y ninguno es el del agente | ✅ 7: `SearchAsync`, `EnrichAsync`, `HealthAsync`, `SuggestFamiliesAsync`, `AuditFamiliesAsync`, `AssistSaleAsync`, `SubstitutesAsync` |
| `assist/v5.md` **no** contiene la tarea del agente | ✅ 7 secciones de tarea, ninguna del agente; su tabla de versiones atribuye esa tarea a `assist/v4` |
| `origin` está en `payload_groups` y no en `response_groups` | ✅ `assist/agent.py:802` lo pone en el grupo del payload; `:807` construía el de la respuesta sin él |
| La ruta del agente usa `get_service_principal` | ✅ `api/routers/assist.py:340` |
| `agent_sweep.py` no cuenta marcadores ni registra antigüedad de proyección | ✅ 0 apariciones de `placeholder`, `projection_age` y `projection_synced` |

---

## 2 · Las siete cifras de la pasada, y la que las hace auditables

**Artefacto:** `ai-service/evals/results/c32b-agent-sweep-17fbdd15a18c.json`
**Procedencia completa:** `run_id 17fbdd15a18c` · `git_sha f1a2a4a…+dirty` (declarado: el árbol llevaba
los cambios de documentación sin commitear) · `pitch_prompt_version assist/v6` ·
`agent_prompt_version agent/v1` · `router_prompt_version router/v3` ·
`deterministic_route_prompt_version assist/v5` · `arms ['openai/gpt-4o']` · surtido 416 ·
`paced_seconds 4.853,3` · **102 peticiones** · coste **2,78 USD**.

**Reducción declarada:** un solo brazo, el que se sirve. Motivo en el §5.7.

### 2.0 · La frescura: la cifra que hace auditable todo lo demás

| | C32b (2026-09-21) | **C42 (2026-09-26)** |
|---|---|---|
| Duración de la pasada | 9.870,8 s = **2 h 44 min** | 4.853,3 s = **1 h 21 min** |
| Techo de rancidez | 3.600 s | 3.600 s |
| Drenaje automático | **no existía** | **encendido**, cada 600 s |
| Antigüedad registrada | **ninguna** | procedencia **y las 102 filas** |
| **Filas rancias** | *imposible saberlo* | **0 de 102** |
| Rango de antigüedad | — | **2 s a 1.193 s** |

**La pasada volvió a durar más que el techo —1 h 21 min contra 1 h— y ninguna fila salió rancia.** Eso
no es suerte: el drenaje de C41 refresca cada 600 s, y el máximo observado de 1.193 s son dos
intervalos. **Es la prueba de que la precondición funciona**, y es exactamente la condición que C32b no
pudo cumplir porque el drenaje es cinco días posterior a su pasada.

Con esto, y sólo con esto, las cifras de recuperación de abajo describen el sistema y no su
desconfiguración.

### 2.1 · Marcadores con `v6` (tarea 10.4)

| | `{{price}}` | `{{stock}}` |
|---|---|---|
| Total | **0** | **0** |
| Generaciones con al menos uno | **0 de 102 · 0,0 %** | **0 de 102 · 0,0 %** |

**Línea base prestada de C40 y declarada como prestada**, que es lo que el §5.1 corrige del plan: `v3`
sobre 90 consultas libres con payload sin anclar escribió `{{price}}` 2 veces y `{{stock}}` 1, en
**3 de 90 generaciones**, y la reparación las arregló todas.

> **La cifra sale ~0 y eso era lo esperado, no un fallo del instrumento.** Comprobado con un caso
> sintético antes de concluirlo: `test_agent_sweep_counts_placeholders` guía un argumentario con dos
> `{{price}}` y un `{{stock}}` por el bucle real y el contador devuelve `(2, 1)`. El contador cuenta.

**El defecto queda cerrado por construcción**, y su magnitud confirmada como pequeña: era real y ya
costaba casi nada.

### 2.2 · `dangling_citation` sobre el agente con `v6` (tarea 10.3)

Comparado **brazo contra brazo, 102 filas contra 102**, que es la única comparación limpia:

| | C32b `v4` | **C42 `v6`** |
|---|---|---|
| Generaciones que corrieron | 84 | 83 |
| **Generaciones con cita colgante, primer intento** | **8 · 9,5 %** | **1 · 1,2 %** |
| **Sobreviven a la reparación** | **8 · 9,5 %** | **1 · 1,2 %** |
| Incidencias | 40 | 8 |
| Incidencias por generación afectada | 5,0 | **8,0** |
| Citas que el modelo declaró | 14 | 14 |
| Respuestas con cero citas | 93 de 102 · 91,2 % | 93 de 102 · **91,2 %** |

**La unidad comparable es la generación y no la incidencia**, y eso lo descubre esta pasada: las ocho
incidencias de C42 están **todas en una sola generación**. Contar incidencias diría «8 contra 40» y
sugeriría una mejora de cinco veces; contar generaciones dice «1 contra 8», que es la cifra con la que
se retira o no un argumentario.

**La reparación no arregla ninguna**, en las dos pasadas: 8 → 8 y 1 → 1. Es la causa dura que de verdad
retira el argumentario, y la reparación única no la toca.

### 2.3 · La retirada, partida por causa (tarea 10.5)

| Causa | C32b `v4` · 1er / sobrevive | **C42 `v6`** · 1er / sobrevive |
|---|---|---|
| `dangling_citation` | 40 / 34 | **8 / 8** |
| `claim_not_in_pitch` *(no dura, por decisión declarada)* | 3 / 1 | 2 / 1 |
| `figure_not_in_context` | 3 / 1 | **2 / 0** |
| `placeholder_in_free_query` | *(no existía como causa dura para esta tarea)* | **0 / 0** |
| **Retirada del argumentario** | **11 de 84 · 13,1 %** | **1 de 83 · 1,2 %** |

La descomposición que el informe de C32b publicó queda **confirmada**: de su 13,1 %, **9,5 puntos** son
`dangling_citation` —8 de 84 generaciones, exactamente— y el resto otras causas. En C42 el 1,2 % es
**íntegramente** `dangling_citation`: una generación, y ninguna otra causa retira nada.

### 2.4 · ⚠ La caída de la retirada es real y **`v6` no la explica**

**Diez veces menos retirada —13,1 % a 1,2 %— y no puedo atribuirla a este change.** Hay que decirlo
así, porque la tentación de cobrarse la mejora es exactamente el error que este repositorio corrige
cada vez.

`v6` hace **una** cosa: llevar la prohibición de marcadores a la tarea del agente. Su efecto medido es
el del §2.1 —0 marcadores— y ya era ~0 antes. **La caída está enteramente en `dangling_citation`**, una
causa que `v6` no menciona: de 8 generaciones afectadas a 1.

**Los confusores, nombrados:**

1. **El modelo del argumentario no se puede verificar idéntico.** El artefacto de C32b trae
   `stage_models: None` — **predata ese registro**, que es la misma razón por la que existe
   `legacy_router_usage`. El de C42 declara `pitch: openai/gpt-4o-mini`. No hay forma de saber desde
   los artefactos si corrieron el mismo modelo de argumentario.
2. **C40 y C41 entraron entre las dos pasadas.** C40 tocó `verification.py` y la fase de la abstención.
3. **Los números son pequeños.** 8 de 84 contra 1 de 83: sugestivo, no establecido, sobre **una** pasada.
4. **Y el modelo no es determinista.**

**Qué queda dicho, entonces:** el defecto que `v6` cierra está cerrado y su coste era pequeño; la
retirada del agente hoy es del **1,2 %** contra el **2,2 %** de la ruta determinista que C32b publicó,
o sea que **la brecha de seis veces que C32b encontró ya no se observa**. Por qué, **esta pasada no lo
dice**, y es de C38 medirlo sobre el conjunto etiquetado.

### 2.5 · Piezas por respuesta y reparto de procedencia (tarea 10.6)

| | C32b `v4` | **C42 `v6`** |
|---|---|---|
| Grupos por respuesta | p50 8 · p95 8 · **máx 8** | p50 8 · p95 8 · **máx 8** |
| Respuestas sin ninguna pieza | 20 · 19,6 % | **21 · 20,6 %** |
| `buscar_sustitutos` invocada | 10 | **11** |

**La tarea pedía esta cifra «esta vez con ámbito aplicado y auditable», y el ámbito lo está —0 filas
rancias— pero la cifra sigue sin medir lo que se quería.** Los grupos **saturan al tope** en las dos
pasadas: p50 = p95 = máximo = 8, que es `MAX_AGENT_PIECES`. Lo que se está midiendo es **la constante**,
no el catálogo ni el surtido.

> **Es una refutación de la premisa de la tarea.** El informe de C32b marcó esta cifra como «tratar
> como NO medida» y atribuyó la duda al ámbito; con el ámbito arreglado y auditable, **sigue sin
> medirse**, porque la restricción que muerde es el tope de piezas y no el surtido. Arreglar la
> frescura era necesario y no suficiente. Quien quiera esta cifra tiene que mover `MAX_AGENT_PIECES` —
> que es justo lo que el design declara fuera de alcance, porque de esa constante depende un
> invariante que la suite afirma.

Lo que sí queda medido y auditable: **la tasa de respuestas sin ninguna pieza, 20,6 %**, que reproduce
el 19,6 % de C32b y confirma la cifra que gobierna el orden del frontal.

### 2.6 · Latencia (tarea 10.7)

| | C32b `v4` | **C42 `v6`** |
|---|---|---|
| p50 | 5.311 ms | **4.707 ms** |
| p95 | 9.021 ms | **7.060 ms** |
| Máximo | 11.918 ms | **8.719 ms** |

**Medida en proceso por el arnés, y NO extremo a extremo por .NET, que es lo que la tarea pedía.** El
motivo está en el §5.8: medirla por .NET exige una segunda pasada de ~102 peticiones contra el
proveedor a través de la API, y la decisión Q-10 del ticket es **una pasada**. Lo que .NET añade sobre
esta cifra es el salto de red más la hidratación, y queda **instrumentado en cada petición** —`ai_ms` y
`total_ms` en el registro de embudo `stage=agent_assist`—, de modo que la cifra es recolectable en
explotación sin gastar una pasada.

**Y confirma el presupuesto de 18 s con margen amplio**: el máximo observado baja de 11.918 a 8.719 ms
contra un techo de servicio de 15 s. El presupuesto sigue **deliberadamente sin apretarse**.

### 2.7 · Reparto de los motivos de parada (tarea 10.8)

| Motivo | C32b `v4` | **C42 `v6`** |
|---|---|---|
| `sin_mas_herramientas` | 86 | **88** |
| `aclaracion` | 10 | **10** |
| `rechazado` | 4 | **4** |
| `presupuesto_tools` | 2 | **0** |
| **`partial`** | **2 · 2,0 %** | **0 · 0,0 %** |

**Cero respuestas incompletas en 102 peticiones**, contra las 2 de C32b. Contrasta con el informe de
exploración v2, que publicaba el 2,0 % del brazo servido y lo usaba para poner la cinta de respuesta
incompleta **la última** del frontal: la decisión era correcta y **la cifra ha bajado aún más**. La
cinta sirve a menos del 1 % en la configuración que se sirve, y sigue construida contra escenario y no
contra observación.

### 2.8 · ⚠ Y una refutación del informe de exploración: **la tabla de herramientas está agrupada por los dos brazos y la domina el barato**

El informe v2 —y con él el orden del tramo de frontend— justificaba poner `origin` primero con esto:
*«`buscar_sustitutos` se invocó **125 veces** en la pasada medida: rotular la procedencia es lo que más
veces impide que la pantalla mienta»*. Partido por brazo desde el mismo artefacto:

| Herramienta | `gpt-4o` · **el que se sirve** | `gpt-4o-mini` · descartado | Total publicado |
|---|---|---|---|
| `consultar_disponibilidad` | 103 | 273 | 376 |
| `buscar_catalogo` | 79 | 87 | 166 |
| **`buscar_sustitutos`** | **10** | **115** | **125** |
| `consultar_conocimiento` | 31 | 82 | 113 |
| `listar_familia` | 8 | 86 | 94 |
| `pedir_aclaracion` | 10 | 14 | 24 |
| **Total** | **241** | **657** | **898** |

**De las 125 invocaciones de `buscar_sustitutos`, 115 son del brazo barato y 10 del que se sirve.** El
brazo descartado hace **2,7 veces** más llamadas a herramienta que el servido, así que domina cada fila
de esa tabla.

> **Es el mismo error que la verificación independiente de C32b ya corrigió una vez, una tabla más
> allá.** Aquella agrupaba los dos brazos en la tasa de pivote, llamaba «6 escenarios» a 3 × 2 brazos y
> publicaba un 83 % cuyo único fallo era del brazo descartado. La tabla de herramientas del informe de
> exploración repite la composición.
>
> **Y no cambia la decisión, que también hay que decirlo.** `origin` tenía que llegar al consumidor
> igual: la pantalla no tenía **nada** con que rotular las filas, y eso es una cuestión de corrección y
> no de frecuencia. Lo que cambia es la **magnitud** con que se justificó el orden: el pivote ocurre
> **una vez cada diez peticiones** en la configuración que se sirve —10 en C32b y **11** en C42, así que
> la tasa no se movió con `v6`—, no «125 veces, rutina».

---

## 3 · El arnés: los dos instrumentos, y por qué van antes de la medida

`agent_sweep.py` **no contaba marcadores y no registraba la antigüedad de la proyección**. Lo segundo
es lo que convierte «medimos sobre el sistema» en una afirmación comprobable, y su ausencia ya costó
una vez.

### 3.1 · Los dos caminos leen cosas distintas, y el arnés no lo notaba

```text
┌─ ARNÉS ─────────────────────────────────┐  ┌─ CAMINO DE SERVICIO ──────────────┐
│ resolve_pieces() → scope_buckets()      │  │ resolve_scope()                   │
│   retrieval/search.py:490-499           │  │   → projection_synced_at()        │
│   SELECT crudo · SIN GUARDIA            │  │   contra el techo de rancidez     │
│   ports.py:204 «read by the             │  │   rancio → NO aplica el prefiltro │
│    evaluation only»                     │  │   (degraded=unscoped)             │
└─────────────────────────────────────────┘  └───────────────────────────────────┘
   etiquetas perfectas por rancia               sirve SIN ámbito
   que esté la proyección
```

**Una pasada dura más que el techo**, así que la antigüedad se registra **por fila** y no sólo por
pasada: sin eso una fila servida sin prefiltro no se distingue de una fresca.

- **Por fila:** `projection_age_seconds` y `projection_stale`, más un marcador `RANCIA` en la consola
  mientras corre, porque el momento de reaccionar es antes de pagar las filas que quedan.
- **En la procedencia:** `projection_freshness_at_start`.
- **En el resumen:** `projection_freshness` con `rows_recorded`, `rows_stale` y los percentiles de la
  edad. Un subconjunto cuyas filas discrepen en rancidez **fue servido de dos maneras**, así que sus
  agregados de recuperación no describen ninguna.
- **La edad sale del punto de control de sincronía** y nunca de `ai.pos_projection.refreshed_at`, que
  registra cuándo cambió una asignación. C41 encontró esa confusión exacta en C40.
- **`None` y no cero** para las filas que preceden al instrumento: cero sería una afirmación.

### 3.2 · Los marcadores, sobre el primer intento

`price_placeholders` y `stock_placeholders` por fila, con los agregados en el resumen. Contados sobre
el **primer** intento, que es la regla de `free_query_gate` y por el mismo motivo: contar el
argumentario servido daría cero por cada marcador que la reparación quitó, y mediría la reparación en
vez del prompt.

---

## 4 · El contrato: adición con **una** excepción medida y declarada

`ai-service/openapi.json` se regeneró con el *one-liner* del README y el *fixture* del guardián pasó
a `openapi-c42-baseline.json` (`sha256 8d9060ac…`, el estado en `c81c3fa`). Medido hoja a hoja con el
mismo `_walk` del propio guardián:

| | Antes | Después |
|---|---|---|
| Hojas | **1.295** | **1.316** |
| Eliminadas | — | **0** |
| Añadidas | — | **21** (el esquema `AgentAssistGroup` y la descripción de la propiedad que lo apunta) |
| **Cambiadas** | — | **1** |

### La hoja cambiada, y por qué se nombra en vez de admitirse por regla

`$.components.schemas.AgentAssistResponse.properties.groups.items.$ref` pasa de `AssistGroup` a
`AgentAssistGroup`.

**El ticket decía que el diff sería «sólo adición», y no lo es.** En el cable sigue siéndolo —la
subclase lleva **toda** propiedad de la compartida con idéntica definición, más `origin`, y el test lo
comprueba **propiedad por propiedad** en vez de fiarse del nombre de la clase—, así que un consumidor
que deserialice la forma antigua lee exactamente lo que leía e ignora un campo desconocido. Lo que un
`$ref` estrechado rompería es un consumidor que **genere** desde el esquema y fije el nombre del tipo.

El propio guardián declaraba que *«any changed `type` or `$ref` still fails»*, así que la hoja se
nombra **individualmente** en `allowed_changes` con su motivo escrito: **el siguiente `$ref` que se
mueva vuelve a fallar.**

Y lo que no se movió, comprobado en el mismo test: `AssistGroup` es idéntico al del *fixture*, y
`AssistResponse.groups.items.$ref` sigue apuntando a él.

---

## 5 · Lo que se refutó, y no se implementó en silencio de otra manera

### 5.1 · El hallazgo del prompt **no gobierna la línea de corte**, y la referencia era la clase equivocada

La ficha del plan de changes decía dos cosas falsas, y quedan corregidas en su sitio:

1. **«El hallazgo que gobierna la línea de corte».** La frase que ordena escribir marcadores es
   **idéntica palabra por palabra** en `assist/v3.md:47` y `assist/v4.md:59`, y la tarea del agente
   (`v4.md:132-166`) **no menciona precio ni existencias**: hereda esa regla y nada más. C40 ya midió
   ese caso exacto sobre 90 consultas libres con payload sin anclar: **3 de 90 generaciones con
   marcador y 0 retiradas tras la reparación**. Y «consume la reparación única» tampoco es lo que hace
   el código: `assist/pitch.py:24` escribe *«One repair, not one per check»* y `repair_message` recibe
   la lista entera, así que un marcador **se suma** y no gasta un turno de otra causa.
   **Lo que gobierna es el consumidor .NET**: siete métodos y ninguno el del agente, que no es una
   degradación del 3 % sino el **100 %** del camino.
2. **La referencia comparable no es la de C30b.** Los 147 de 213 y 188 de 213 son de los **modos
   anclados**, donde hay una pieza; la cabecera de `assist/v5.md` ya había escrito que la proporción
   no se traslada, y C40 lo confirmó. La referencia es la del análogo de C40, declarada como **línea
   base prestada**.

### 5.2 · El escenario de la venta deshabilitada **es falso sobre el componente que la propia spec manda reutilizar**

El escenario decía *«the sale is disabled when stock is unknown»*. `assisted-search-result-row.tsx`
—reutilizado **sin modificar**, y con test propio de C40 que lo fija— **no hace eso**: con
`hasStock === null` sustituye la línea de existencias por «Selecciona una tienda para ver existencias»
y deshabilita **abrir la ficha de venta**, dejando «Seleccionar para venta» activo.

Implementarlo como estaba escrito exigía un diff a esa fila, **explícitamente fuera de alcance**, y
habría dejado a los dos paneles hermanos en desacuerdo sin que fallara ningún test.

**Y es además el comportamiento correcto**, que es por lo que no merece el diff: el ámbito global
existe para saber **dónde** está una pieza, y el flujo de venta manual al que entrega exige tienda
propia y valida existencias allí; deshabilitar la selección dejaría al ámbito sin poder llevar a
ningún sitio. Lo que no debe pasar —presentar existencias desconocidas como «no queda»— es lo que la
fila ya previene con sus tres estados.

**Enmendado en la delta del change y no en la spec viva**, con el motivo escrito en el propio
escenario y en la tarea 8.6.

### 5.3 · La precondición de 2.6 tenía **dos mitades**, y la tarea sólo describía una

*«Contenedor `jbg-ai` levantado con el drenaje encendido»* resultó insuficiente por dos razones que
se descubrieron al comprobarlo:

1. **La imagen que estaba corriendo era anterior a la sección `projection` del informe de salud**, así
   que `/health` **no la traía en absoluto** — no «la traía mal»: no existía. Reconstruida desde HEAD,
   responde, y el planificador arranca con `interval_seconds=600` contra `ceiling_seconds=3600`
   (600 < 900 = techo/4 ✓).
2. **El drenaje necesita la API .NET sirviendo el *index feed* en `:5056`.** Sin ella el arranque
   registra `feed_not_configured` y la proyección **sigue rancia**, que es exactamente el estado que
   la precondición existe para descartar. Con la API arriba:

   ```text
   stage=pos_sync ... done pages=1 upserted=1 soft_deleted=0 failed_pages=0
   /health → projection.status="ok"  age_seconds=0.38  ceiling_seconds=3600  stale=false
   ```

**Tener C41 archivado no basta, y tener el contenedor arriba tampoco: hace falta el otro extremo del
feed.** Va al *runbook*.

### 5.4 · Una regresión propia, y la encontró la comparación por nombres y no un test nuevo

La viñeta «Más lento y más caro que **buscar con ayuda**» de la tarjeta del agente hacía que el nombre
accesible de **su** enlace también encajara con `/Buscar con Ayuda/i`, con lo que la consulta del test
del hub —`getByRole('link', { name: /Buscar con Ayuda/i })`— pasaba a encontrar **dos** elementos y
fallaba. Reescrita como «el panel directo», que es además el rótulo del enlace de vuelta.

> **Lo que esto dice del método.** Ningún test nuevo la habría visto: el defecto no estaba en lo
> nuevo, estaba en lo que lo nuevo le hacía a lo viejo, y sólo la comparación **por nombres** contra la
> línea base lo señaló. Es la tercera vez que este repositorio paga por confiar en un recuento.

### 5.5 · La guarda de paridad del contrato no cubría al agente, y al cubrirla encontró un desajuste

`AiContractSnapshotTests` es la recíproca del *snapshot* de Python: compara **propiedad a propiedad**
los DTO de .NET contra `ai-service/openapi.json`, nombre en el cable y anulabilidad incluidas. Cubría
diecinueve modelos y **ninguno era del agente**.

Eso dejaba el hueco justo donde más duele. Los tests del cliente del agente deserializan un cuerpo
JSON que **este repositorio escribió**, así que un nombre mal puesto en los **dos** lados —
`toolCallsUsed` donde el contrato dice `tool_calls_used` — los habría pasado los dos y habría llegado
a producción como un `null` silencioso. Y la ruta del agente es precisamente la que **nadie había
llamado nunca**, así que no había nada más comprobando el cable.

**Al añadir los siete DTO, la guarda encontró un desajuste a la primera:**

```text
Expected IsNullableInContract(declared) to be True because nullability of 'top_k' must match
between AiAssistAgentRequest and schema AgentAssistRequest …, but found False.
```

`AiAssistAgentRequest.TopK` era `int?`; el contrato declara `top_k: int = Field(default=5, ge=1,
le=20)`, **no anulable con defecto** — la misma forma que `AiAssistSaleRequest.Filters` ya usaba por
el mismo motivo. Corregido a `int` con el defecto del contrato.

> **Es la clase de defecto que C40 se comió por no correr `tsc --noEmit`**: verde en todas partes y
> desalineado en el único sitio que importa. La diferencia es que aquí la guarda ya existía y sólo
> había que extenderla.

### 5.6 · La trampa del `.exe` vivo se manifestó primero como **silencio**

`CLAUDE.md` documenta que un `JoiabagurPV.API.exe` corriendo bloquea `bin/Debug`, la compilación falla
y `dotnet test` sale 0 con cero tests ejecutados. Ocurrió al correr la guarda de paridad con la API
levantada para la comprobación manual, y el detalle que la documentación no daba es **cómo se ve**: el
primer intento, con la salida filtrada a las líneas de resumen, **no imprimió absolutamente nada** —
ni un error, ni un recuento—. Sin filtro salen veinte `MSBUILD warning MSB3026` de reintento y tres
`error MSB3021`, todos nombrando el proceso que bloquea y su PID.

**La lectura práctica:** si la salida filtrada de `dotnet test` viene vacía, no es que no haya nada que
decir — es que no se compiló. Y la coincidencia de tener la API levantada para la 12.1 **mientras** se
corren tests es exactamente la situación en la que pasa.

### 5.7 · La latencia extremo a extremo por .NET **no se mide**, y el motivo es la decisión de una sola pasada

La tarea 10.7 pedía *«la latencia p50/p95 extremo a extremo medida por .NET»*. Lo publicado en el §2.6
es **la del arnés, en proceso**, y la diferencia se declara en vez de disimularse.

Medirla por .NET exige llevar ~102 peticiones **a través de la API**, o sea **una segunda pasada contra
el proveedor**: otros 1 h 21 min y otros 2,78 USD, para una cifra que es la del §2.6 más el salto de red
y la hidratación. La decisión Q-10 del ticket es explícita —**una pasada, después del cambio**— y ésta
es la clase de gasto que esa decisión existe para evitar.

**Y la cifra no se pierde, se recoge donde de verdad importa:** el registro de embudo
`stage=agent_assist` publica `ai_ms` y `total_ms` en **cada** petición, así que la latencia extremo a
extremo es una consulta a los logs en explotación, con tráfico real en vez de con un conjunto
sintético. Es una cifra mejor que la que una segunda pasada habría dado.

### 5.8 · ⚠ La comprobación manual encontró dos defectos, y **ninguna de las tres suites podía verlos**

Esto es la justificación de la puerta 12.1, escrita con lo que encontró. Síntoma reportado por el
operario: con el administrador y **una tienda seleccionada** el agente contesta bien; con **«todas las
tiendas»** *todas* las respuestas caen con aviso de asistente no disponible y cero piezas.

#### Defecto 1 · El contenedor servía código anterior al change, y `restart` no lo arregla

`docker compose restart` **reutiliza la imagen**. La que estaba corriendo se construyó al comprobar la
precondición del drenaje, **antes** del tramo de `ai-service`, así que el contenedor servía la ruta del
agente con `get_service_principal` — el que **rechaza con 401 un token sin `pos_id`**. Verificado
dentro del contenedor: no tenía `v6.md` y su ruta seguía con el principal antiguo.

De ahí que el fallo fuera **parcial y por eso desconcertante**: sólo el ámbito global viaja sin la
reclamación, así que sólo él caía. .NET lo degradaba a `credential_rejected` y servía la respuesta con
`aiAvailable: false`, que es lo correcto.

> **Y la razón de que ninguna suite lo viera es la que importa: nada ejercitaba la ruta del agente por
> HTTP.** El arnés de evaluación importa `run_agent` y lo llama **en proceso** —las 102 peticiones de la
> pasada no pasaron por el contenedor—; los tests de integración de .NET usan una pasarela falsa; y los
> tests de ruta de Python levantan la app con `TestClient`. Las tres capas verdes, y el cable entre las
> dos últimas sin recorrer por nadie. **Es exactamente la clase de defecto que C40 dejó pasar con 136
> escenarios en verde**, y es la razón por la que esta puerta está en la definición de hecho.
>
> Reconstruida la imagen, la ruta responde **200 con y sin `pos_id`**, comprobado por HTTP con los dos
> tokens. La precondición —y el porqué— van al *runbook*.

#### Defecto 2 · El bloque afirmaba un motivo de parada que no existía. **Éste es de código y sobrevivía al arreglo del contenedor**

Con la pasarela degradada, la respuesta llega sin motivo de parada y sin contadores, y el bloque
mostraba:

```text
El agente terminó por un motivo que esta pantalla no reconoce
0 vueltas · 0 consultas
El asistente no está disponible
Lo que ves viene del catálogo: el precio, las unidades y las variantes son reales…
```

**Tres cosas falsas a la vez.** La primera culpa a la pantalla de un servicio que simplemente no
contestó —el motivo no es que no se reconozca, es que no hay motivo—. La segunda describe un bucle que
no corrió. Y la tercera es la copia de C36 para `ai_unavailable`, escrita para **la ficha de venta**,
donde sí hay una pieza delante: aquí no hay ninguna fila, así que «lo que ves viene del catálogo» no
describe nada.

**Arreglado keyándolo en `aiAvailable`:** cuando el servicio no contestó, la tira dice **la
degradación** —que el servicio ya traía en `degradedReason` y que `degradedReasonText` ya traducía, y
que el bloque no usaba— y no se pinta ni el motivo de parada, ni los contadores, ni el bloque de C36.
Cuando el servicio **sí** contestó reportando que su proveedor cayó, eso **sí** es un motivo de parada
con copia propia y los contadores significan algo, y la tira lo dice así.

**Seis tests nuevos** cubren el estado, incluido el que separa las dos degradaciones. La que ninguno
tenía: **no había un solo test del bloque con `aiAvailable: false`**, y ésa es la lección de método —
los estados degradados de la pasarela se probaron en el servicio de aplicación y no en la pantalla que
los pinta.

#### Y lo que la comprobación confirmó, tras los dos arreglos

Con el administrador y **«todas las tiendas»**, observado en el entorno levantado:

| Lo que se ve | Qué confirma |
|---|---|
| **Precios sí, existencias no** | La hidratación con ámbito global reporta cantidad y existencias como **desconocidas y no como cero**, y la fila lo dice en vez de afirmar «sin existencias» |
| El bucle consulta **catálogo, conocimiento, familias y disponibilidad** | Las cuatro herramientas se eligen con el ámbito ausente: la omisión de la reclamación **no mutila el bucle**, sólo el prefiltro |
| `consultar_disponibilidad` **se invoca igual** | El escenario *«with no scope the loop reports no scope rather than no stock»*, confirmado **en el entorno** y no sólo a nivel de bucle: la etiqueta vale `sin_ambito`, que no es «agotado», y por eso **el pivote no se dispara** — que es la consecuencia que D9 obliga a declarar en pantalla |

**La premisa de D9 queda verificada por observación**: ofrecer el ámbito global cuesta la capacidad de
pivotar, y la línea que lo advierte al seleccionarlo no es estética.

#### Y la economía del transcript, que era una predicción aritmética, queda **medida**

El ticket la calculó así: `6 × 25 + 6 × 386 (p50) = 2.466 / 4.000`, y de ahí salió que la conversación
son **seis intercambios y no doce**. Observado en la comprobación manual, al cerrarse el compositor:

```text
turnos 12/12 · 2.731/4.000 car.        ← el tope de TURNOS es el que muerde
Sesión: 6 preguntas · 87k tokens · 0,52 €
```

Y corroborado petición a petición en el registro de embudo de la API, que apunta `transcript_chars` en
cada una:

| Turnos enviados | 1 | 3 | 5 | 7 |
|---|---|---|---|---|
| Caracteres | 24 | 536 | 679 | 1.121 |

**La predicción y la medida coinciden dentro del 11 %** —2.466 predicho contra 2.731 medido— y el
reparto es el que fija D6: **el tope de turnos se alcanza con los caracteres al 68 % de su límite**. Un
contador que sólo hubiera medido lo tecleado habría ido por unos 150 caracteres de 4.000, o sea el
**4 %**, con el rechazo por turnos ya ganado.

> **Dos cosas que el log confirma de paso.** Los argumentarios llegan a **528 y 497 caracteres**, por
> encima del p50 de 386 que C32b midió, así que el recorte por turno a 500 **no es decorativo**: recorta
> de verdad. Y el coste de una conversación completa de seis intercambios es **0,52 € con 87k tokens**,
> que es la cifra que la barra fija existe para poner delante del operario antes de que pulse otra vez.

### 5.9 · ⚠ Y el hallazgo mayor de la comprobación manual: **el pivote es inalcanzable si el operario nombra la pieza por su nombre**

**El pivote a sustitutos es lo que este panel existe para demostrar**, y está medido **3 de 3** en
`sin_existencias` con `gpt-4o`. La comprobación manual estableció que **esa medición se tomó en una
situación que no existe en la pantalla.**

El experimento, sobre una pieza agotada de verdad —`SKU759`, con `qty_bucket = '0'` en
`ai.pos_projection` para `CIU-CENTRE`, comprobado en la base— preguntada de las dos maneras contra el
proveedor real por HTTP:

| Cómo la nombra el operario | Herramientas que eligió el bucle | ¿Pivota? |
|---|---|---|
| **Por su referencia**, `SKU759` | `consultar_disponibilidad` → **`buscar_sustitutos`** | ✅ 6 grupos, **todos `sustitutos`** |
| **Por su nombre** | `consultar_disponibilidad`❗`referencia_desconocida` → `buscar_catalogo` → `consultar_disponibilidad` | ❌ 8 grupos, **todos `catalogo`** |

**El mecanismo es estructural y el bucle hace lo correcto en cada paso.** `buscar_catalogo` devuelve al
modelo `posicion`, `sku`, `materiales`, `variante` y `motivos` — **nunca el nombre del producto**. Así
que el modelo pasa el nombre a `consultar_disponibilidad` y recibe `referencia_desconocida`; se recupera
buscando en catálogo; y recibe ocho candidatos **identificados sólo por SKU, material y variante**, sin
nada con que saber cuál de los ocho es la pieza que el cliente nombró. Consulta la disponibilidad de
otra, que sí tiene stock, y **correctamente** no pivota.

> **Por qué el arnés no podía verlo, que es el mismo patrón que este informe ya cuenta dos veces más.**
> `scenario_turns` resuelve el marcador `{pieza}` a un **SKU** y lo escribe en el turno, así que en las
> 204 peticiones de C32b y en las 102 de C42 **el modelo siempre recibió la referencia servida**. Un
> operario teclea un nombre. Las tres suites verdes, la pasada limpia, y la capacidad que el panel existe
> para demostrar inalcanzable por el camino que un operario recorre.

**Fuera del alcance de C42**, que declara no tocar las seis herramientas ni añadir una séptima. Queda
en `openspec/DEFERRED_TASKS.md` como entrada propia, con el experimento, el mecanismo y **tres opciones
de arreglo con su coste**: el campo `nombre` en la observación de `buscar_catalogo` —donde el argumento
de C30b contra ensanchar **no se aplica tal cual**, porque es sobre numerales y un nombre no lleva
cifras—; el paliativo de que el operario nombre la referencia que la fila ya enseña; y la que **no** hay
que hacer, que es colapsar `referencia_desconocida` en una búsqueda por nombre dentro de
`consultar_disponibilidad`.

**Y el pivote sí se demuestra**, nombrando la referencia, que es realista en un mostrador porque la
pieza lleva su etiqueta delante. Es lo que dice el *runbook*.

### 5.10 · El brazo barato no se mide, y es una reducción declarada

La pasada se toma **sólo sobre `gpt-4o`**, el arm que se sirve: 102 peticiones en vez de 204. El brazo
barato ya está **descartado por comportamiento y no por precio** —58,8 % de respuestas incompletas
contra 2,0 %, y su presupuesto de herramientas agotado 56 veces contra 2— y C42 no decide nada sobre
él. La comparación por brazo está publicada por C32b y no cambia con `v6`, que sólo mueve la tarea del
argumentario.

---

## 6 · El alcance, comprobado fichero a fichero

| Lo que no se toca | Estado |
|---|---|
| `ai-service/prompts/assist/v5.md` | **sin diff** ✅ |
| `ai-service/prompts/assist/v4.md` | **sin diff** ✅ |
| `PROMPT_VERSION` | `assist/v5`, **sin cambio** ✅ |
| `frontend/.../assisted-search-result-row.tsx` | **sin diff** ✅ |
| `frontend/.../sales-assist-card/pitch-block.tsx` | **sin diff** ✅ |
| `frontend/.../sales-assist-card/substitutes-block.tsx` | **sin diff** ✅ |
| `AssistGroup` del esquema compartido | **sin `origin`** ✅ — `origin` va en la subclase |
| Migraciones de EF Core | **ninguna creada** ✅ |
| Migraciones de Alembic | **ninguna creada** ✅ |
| Las seis herramientas | **sin tocar** ✅ |

`AGENT_PITCH_PROMPT_VERSION` es lo único que se mueve: `assist/v4` → `assist/v6`.

---

## 7 · Las decisiones que el código ejecuta, y dónde comprobarlas

| Decisión | Dónde vive | Cómo se comprueba |
|---|---|---|
| **D1** Ruta propia y no un modo del panel | `routes.tsx` · `AgentEntryCard` | La ruta resuelve con chunk propio (`agent-*.js`), y el panel hermano no gana ningún conmutador |
| **D2** Versión de prompt propia, la determinista intacta | `assist/v6.md` · `constants.py` | `test_v6_system_section_matches_v5` compara el *Sistema* **carácter por carácter** |
| **D3** La procedencia como subclase | `AgentAssistGroup` | `test_the_shared_group_model_did_not_grow_the_field` |
| **D4** El circuito no cuenta la degradación de 200 | `AiGatewayServiceCollectionExtensions` | `AgentAssist_WhenProviderFails_DoesNotOpenTheCircuitOnPartial` |
| **D5** Cada turno dueño de su bloque | `pages/sales/agent.tsx` | `should keep each turn's answer anchored to its own turn` |
| **D6** La transcripción se cuenta como se va a enviar | `agent-transcript.ts` | `should count the assistant turns towards the transcript caps` |
| **D7** La puerta con tres estados | `AgentEntryCard` | Los tres, más `agentGateState` sobre el campo ausente |
| **D8** El orden sale de las frecuencias medidas | `AgentAnswerBlock` | El bloque sin filas primero, la cinta de incompleta la última |
| **D9** El ámbito copiado del panel hermano | `agent.tsx` · `AgentAssistService` | `should warn that the every-shop scope stops the agent offering alternatives` |
| **D10** Los instrumentos antes de la medida | `agent_sweep.py` | `test_agent_sweep_counts_placeholders` · `test_agent_sweep_records_projection_age` |

---

## 8 · Lo que queda declarado y no cerrado

- **Una conversación de ámbito global no se registra.** Limitación **heredada** de C40: la columna de
  punto de venta del evento es obligatoria y con índice, así que cerrarlo abre migración, y escribir
  una tienda de relleno es lo que la spec prohíbe. La respuesta vuelve sin `searchEventId`.
- **Una petición por minuto.** ~13.000 tokens contra 25.000 TPM. Basta para un mostrador y un
  evaluador; **no** para dos mostradores simultáneos. Es lo que hace inalcanzable un cortafuegos por
  umbral de muestra y lo que fija el cupo del agente en cuatro por minuto.
- **Dos estados de la pantalla nunca observados en producción**: ni la falta de credencial ni la caída
  del proveedor aparecieron en las 204 peticiones de C32b. Construidos contra escenarios y declarados
  como tales.
- **El presupuesto de herramientas efectivo es seis y no ocho**, por la granularidad de la
  concurrencia. Se declara y **no se recalibra aquí**: movería una constante de la que depende un
  invariante que la suite afirma.
- **El coste en euros de la barra de sesión es un orden de magnitud y no una factura.** Los tokens de
  un turno suman hasta tres etapas que pueden correr tres modelos distintos, así que ningún arancel
  por modelo sería honesto; lo que el operario necesita saber es si la conversación ha costado
  céntimos o euros.

---

## 9 · Trazabilidad

| Grupo de tareas | Estado |
|---|---|
| 1 · Puerta de entrada | ✅ 2/2 |
| 2 · Tramo 0 · instrumentos | ✅ 6/6 |
| 3 · Tramo 1 · `ai-service` | ✅ 10/10 |
| 4 · Tramo 2 · `backend` | ✅ 13/13 |
| 5-8 · Tramo 3 · `frontend` | ✅ 25/25 |
| 9 · Tramo 4 · el coste | ✅ 1/1 |
| 10 · Medición | ✅ 8/8 — 10.7 publicada como la del arnés y no como la de .NET, con su razón en el §5.7 |
| 11 · Specs y anotaciones | ✅ 5/5 |
| 12 · Cierre | ✅ 5/5 — **12.1 recorrida con los dos roles y los cinco recorridos**, y es la que encontró los tres defectos del §5.8 y §5.9 |

**Tests nuevos:** 10 en `ai-service`, **61** en `backend` —54 propios más los 7 modelos del agente que
entran en la guarda de paridad del contrato— y **105** en `frontend` —99 más los 6 del estado degradado que la comprobación manual obligó a escribir—.
**`openspec validate --all --strict`: 63 passed, 0 failed.**
**`dotnet build`: 0 errores. `npm run build`: verde. `tsc --noEmit` filtrado: sin errores nuevos.**
