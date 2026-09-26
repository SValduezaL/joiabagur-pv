# C42 — informe de implementación: el agente llega al operario, y las seis cosas que se refutaron por el camino

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

## 2 · Las siete cifras de la pasada

> *(Sección pendiente de la pasada, en curso al escribir esto. Se rellena con el artefacto.)*

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

### 5.5 · El brazo barato no se mide, y es una reducción declarada

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
| 10 · Medición | *(en curso — §2)* |
| 11 · Specs y anotaciones | ✅ 5/5 |
| 12 · Cierre | *(12.1 en manos del operario, con su guion en `c42-manual-check-runbook.md`)* |

**Tests nuevos:** 10 en `ai-service`, 54 en `backend`, 99 en `frontend`.
**`openspec validate --all --strict`: 63 passed, 0 failed.**
**`dotnet build`: 0 errores. `npm run build`: verde. `tsc --noEmit` filtrado: sin errores nuevos.**
