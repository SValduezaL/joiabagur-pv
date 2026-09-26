# T-AIENG-042: Give the sales agent an operator surface — own route, per-turn answer blocks, visible trace, and the pitch that today is withheld by construction (C42)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya siguen
> [T-AIENG-041](../archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md) y
> [T-AIENG-040](../archive/2026-09-25-add-frontend-free-query-panel/ticket.md).
>
> **Fuentes de verdad:** `openspec/project.md`, las specs vivas
> [`sales-assistant-agent`](../../specs/sales-assistant-agent/spec.md),
> [`sales-assistant-tools`](../../specs/sales-assistant-tools/spec.md),
> [`assist-generation`](../../specs/assist-generation/spec.md),
> [`ai-gateway-client`](../../specs/ai-gateway-client/spec.md),
> [`ai-free-query-search`](../../specs/ai-free-query-search/spec.md) y
> [`ai-search-telemetry`](../../specs/ai-search-telemetry/spec.md), y **el código real**, de donde sale
> todo lo que este ticket afirma con fichero y línea.

**Change:** `add-frontend-agent-panel` (C42) · **Épica:** **EP15 — Venta Asistida, Sustitutos y Agentes**
**Abierto:** 2026-09-26 · **Historia:** [HU-AIENG-042](../../../Documentos/Historias/AI-Eng/HU-AIENG-042.md)
**Exploración:** dos pasadas el mismo día —
[v1](../../../Documentos/Proyecto%20Final%20AIEng/informes/c42-exploration-decisions.md) (contra el
código) y
[v2](../../../Documentos/Proyecto%20Final%20AIEng/informes/c42-exploration-decisions-v2.md) (contra los
artefactos ya escritos, **sin llamar al proveedor**). **El v2 es el que gobierna este ticket.**
**Origen:** sesión abierta para decidir entre implementar C38 entero o dar superficie al agente.

---

## 0 · Qué pide este ticket, en una frase

Que **el agente de venta llegue al operario**: ruta propia, cuarta tarjeta en el hub, un hilo de
conversación donde cada turno es dueño de su bloque de respuesta con las filas rotuladas por
procedencia y la traza visible — y, de camino, que el argumentario del agente deje de retirarse por
construcción.

---

## 0.1 · Lo que la segunda pasada de exploración corrige, y hay que leerlo antes de dimensionar

| El v1 decía | El v2 mide | Efecto en este ticket |
|---|---|---|
| **F1 gobierna la línea de corte**: sin subir el prompt, *«C42 entrega un panel de agente sin prosa»* | La frase que ordena marcadores es **idéntica** en `v3.md:47` y `v4.md:59`, así que **C40 ya midió este caso**: **3 de 90** generaciones con marcador y **0 retiradas tras la reparación** | El arreglo del prompt **entra igual** pero **no gobierna**. Lo que gobierna es el **tramo 2** |
| Referencia: C30b, `{{price}}` 147/213 y `{{stock}}` 188/213 | Son los modos **anclados**. `v5.md` ya escribió que la proporción **no se traslada** | **Clase de referencia equivocada.** La línea base se presta de C40 |
| `agent_sweep --rescore` mide las retiradas por marcador *«sin proveedor y sin base de datos»* | El arnés **no cuenta marcadores** y **el texto del argumentario no se persiste**; `rescore` reagrega campos ya grabados | Nace un **tramo 0 de instrumentos** |
| «Medir antes de escribir la primera tarea» | **No era ejecutable**: medir exige escribir primero el contador | El contador es la **tarea 0.1** |
| La pasada de C32b se cita sin reservas | Duró **2 h 44 min** contra un techo de rancidez de **1 h**, sin drenaje automático disponible entonces | **§6**: se anota, no se rehace. **El pivote sobrevive** |
| Maqueta del compositor: «turno 4/12» | El tope de caracteres cuenta **también** los turnos del asistente → **6 intercambios** | **§8**, y D15 |

---

## 1 · Contexto y problema

De los cinco pilares que el Proyecto Final nombra —CAG, RAG, **agentes**, evaluación y despliegue—, el
del agente es **el único sin superficie de operario**. `POST /v1/assist/agent` está entregado, probado y
medido con proveedor real desde C32b, y **no lo llama nadie**.

### El problema no es una carencia de calidad: es que no hay camino

```
 ┌──────────┐   ┌──────────────┐   ┌────────────────────┐   ┌──────────────────┐
 │ pantalla │ ? │ IAiGateway   │ ? │ POST /v1/assist/   │ ✓ │ bucle del agente │
 │  (nada)  │───│  Client      │───│      agent         │───│  6 tools, 5      │
 │          │   │ 7 métodos,   │   │  implementado y    │   │  vueltas, medido │
 │          │   │ ninguno suyo │   │  medido            │   │  con proveedor   │
 └──────────┘   └──────────────┘   └────────────────────┘   └──────────────────┘
       └────────── los dos eslabones que faltan ──────────┘
```

**Eso no es una degradación del 3 %: es el 100 %**, y es el motivo por el que el tramo 2 gobierna la
línea de corte y no el arreglo del prompt.

### El defecto de generación, con su cadena y su tamaño real

Tres eslabones, cada uno correcto por separado:

1. `AGENT_PITCH_PROMPT_VERSION = "assist/v4"` (`ai-service/src/jbg_ai/assist/constants.py:522`),
   deliberadamente apartado de `PROMPT_VERSION`, que ya va por `assist/v5`. Y la sección *Sistema* de
   `v4` ordena **sin condición**: *«El precio y la disponibilidad son siempre marcadores»*
   (`ai-service/prompts/assist/v4.md:59`).
2. El payload del bucle es un `FreeQueryPayload` con `is_anchored = ClassVar[bool] = False`
   (`ai-service/src/jbg_ai/assist/prompt.py:453`), construido por `free_query_payload_from(…)`
   (`ai-service/src/jbg_ai/assist/agent.py:940`). **Es correcto**: el argumentario del agente habla de
   varias piezas.
3. C40 metió `CAUSE_PLACEHOLDER_IN_FREE_QUERY` en `HARD_VIOLATION_CAUSES`
   (`ai-service/src/jbg_ai/assist/constants.py:339`) y la comprobación dispara exactamente cuando el
   payload **no** está anclado (`ai-service/src/jbg_ai/assist/verification.py:256`).

**Y el tamaño está medido, sobre el análogo estructural exacto.** `c40-placeholders-before-v3-ed9ee934e8c6.json`,
90 consultas libres con payload sin anclar y el mismo *Sistema* que ordena marcadores:

| | `v3` · ordena marcadores | `v5` · los prohíbe |
|---|---|---|
| Generaciones con marcador | **3 de 90 · 3,3 %** | 0 de 90 |
| `placeholder_in_free_query`, primer intento | **3** | 0 |
| **Tras la reparación** | **0** | 0 |

> **Y «consume la reparación única» no es lo que hace el código.** `ai-service/src/jbg_ai/assist/pitch.py:24`
> lo escribe: ***«One repair, not one per check.»*** `repair_message(violations)` recibe **la lista
> entera**, así que un marcador **se añade a la lista**, no gasta un turno que otra causa fuera a usar.

### Lo que de verdad retira el argumentario, medido

| causa | primer intento | **sobrevive** |
|---|---|---|
| `dangling_citation` | **85** | **72** |
| `claim_not_in_pitch` | 8 | 6 *(no es dura, por decisión declarada)* |
| `figure_not_in_context` | 6 | 2 |

La reparación arregla **13 de 85** citas colgantes. Retirada en `gpt-4o`: **11 de 84 = 13,1 %**, que
reproduce la cifra publicada por C32b. Con **el 92,2 % de las respuestas trayendo cero citas**, la
mayoría de las retiradas son identificadores inventados sobre un corpus que no se entregó.

---

## 2 · Estado actual del código, verificado en el repositorio (2026-09-26)

| Pieza | Fichero | Estado |
|---|---|---|
| Ruta del agente | `ai-service/src/jbg_ai/api/routers/assist.py:340` | ✅ existe · **exige `pos_id`** vía `get_service_principal` |
| Ruta determinista | `ai-service/src/jbg_ai/api/routers/assist.py:232` | ✅ `get_unscoped_principal` **desde C40** |
| Las seis herramientas | `ai-service/src/jbg_ai/assist/tools.py:902` | ✅ congeladas. Dos ausencias deliberadas con test |
| `AgentAssistRequest` | `ai-service/src/jbg_ai/api/schemas/assist.py:118` | ✅ `turns`, `top_k`, `context`, `locale`, `pos_id` **aceptado e ignorado** |
| Los tres topes | `ai-service/src/jbg_ai/assist/constants.py:739-741` | ✅ 12 turnos, 500 car./turno, **4.000 en total sumando TODOS los turnos** |
| `AGENT_STOP_REASONS` | `ai-service/src/jbg_ai/assist/constants.py:710-721` | ✅ **diez** valores; cinco de presupuesto apartados en `AGENT_BUDGET_STOP_REASONS` |
| `origin` de los grupos | `ai-service/src/jbg_ai/assist/agent.py:779` | ⚠️ **está en `payload_groups` y NO en `response_groups`** |
| Miembro de la respuesta | `ai-service/src/jbg_ai/assist/agent.py:847` | ⚠️ `product_id`, `sku`, `variant_label`, `materials`, `score`, `match_reasons` y nada más |
| Tarea del agente en el prompt | `ai-service/prompts/assist/v4.md:132` | ⚠️ **`v5` no la contiene**: tiene 7 tareas y ésta no está |
| Contador de marcadores en el arnés | `ai-service/src/jbg_ai/evals/agent_sweep.py` | ❌ **no existe** (0 apariciones de `placeholder`) |
| Antigüedad de proyección en el arnés | `ai-service/src/jbg_ai/evals/agent_sweep.py` | ❌ **no se registra** ni en procedencia ni por fila |
| Puerto del arnés para el surtido | `ai-service/src/jbg_ai/retrieval/search.py:490-499` | ⚠️ `SELECT` crudo, **sin guard de rancidez**; `ports.py:204` lo declara *«Read by the evaluation only»* |
| Guard de rancidez del servicio | `ai-service/src/jbg_ai/retrieval/orchestrator.py:282-305` | ✅ degrada a `degraded=unscoped` |
| Etiqueta de disponibilidad | `ai-service/src/jbg_ai/assist/tools.py:873-891` | ✅ **lectura directa, sin guard**; la edad viaja al modelo |
| `IAiGatewayClient` | `backend/src/JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs` | ❌ **7 métodos, ninguno del agente** |
| Cliente `ai-assist` | `backend/src/.../AiGatewayServiceCollectionExtensions.cs:161-203` | ✅ patrón a copiar. Su breaker declara que un 200 degradado **no es fallo** |
| `AssistedSearchResultDto` | `backend/src/JoiabagurPV.Application/` | ✅ `Name`, `Price`, `QuantityAtPointOfSale`, `HasStock` **anulables**, foto, colección, `Score`, `MatchReasons`, `Materials`, `FamilyId`, `VariantLabel` |
| Hidratación | `backend/src/.../SalesAssistService.cs:219` | ✅ hidrata `ai.Groups.SelectMany(g => g.Members)` — **todos los miembros de todos los grupos** |
| `PitchPlaceholderResolver` | `backend/src/.../SalesAssistService.cs:369` | ✅ sólo se invoca desde **la ruta anclada**. No afecta al agente |
| Sonda de disponibilidad | `backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs:241` | ✅ **`Guid?` desde C40_FIX**: ausencia = ámbito global, `Guid.Empty` = 400 |
| Predicado del interruptor | `AiScopeSwitchExtensions` (C40_FIX) | ✅ extraído y único para sonda y ruta |
| `SearchOrigin` | `backend/src/JoiabagurPV.Domain/Enums/SearchOrigin.cs` | ✅ cuatro valores; `AssistedGenerative = 4` de C40, **sin migración** |
| Fila de resultado | `frontend/src/components/sales/assisted-search-result-row.tsx` (248 líneas) | ✅ **se reutiliza entera**: resuelve `pointOfSaleName: null`, `familyNote`, vender, abrir ficha, y `hasStock === null` deshabilitando la venta |
| Prosa y citas | `frontend/src/components/sales/sales-assist-card/pitch-block.tsx` (170 líneas) | ✅ **se reutiliza tal cual**: es de respuesta, no de pieza |
| `substitutes-block` | `frontend/src/components/sales/sales-assist-card/substitutes-block.tsx` | ❌ **imposible reutilizar**: se alimenta de `familyMatch`, `materialOverlap` y `styleSimilarity`, que llegan por endpoint aparte |
| Panel de consulta libre | `frontend/src/pages/sales/assisted.tsx` (806 líneas) | ✅ modelo de ámbito a copiar. `:186` la opción global es **sólo de administrador** |
| Drenaje programado | `ai-service/src/jbg_ai/indexing/scheduler.py:143`, `api/lifespan.py:50` | ✅ C41. **Vive sólo en el lifespan de FastAPI**; el arnés es un CLI y **no drena** |

---

## 3 · Lo que se pide

### Tramo 0 · Instrumentos — antes de cualquier tarea funcional · `ai-service/`

- **0.1** Contador de marcadores en `agent_sweep.py`: `{{price}} `/ `{{stock}}` por fila y agregados en
  el resumen, con el patrón de `evals/free_query_gate.py:212-213`.
- **0.2** Antigüedad de la proyección: `projection_synced_at()` al arrancar y **en cada fila**, con
  `age_seconds` y `stale` contra `jpv_pos_projection_max_age_seconds`.
- **0.3** Precondición de runbook, comprobada y escrita: contenedor `jbg-ai` arriba con
  `JPV_POS_SYNC_SCHEDULER_ENABLED=true`, intervalo 600 s < techo 3.600 s, verificado en `/health`.

### Tramo 1 · `ai-service/` — el contrato y el prompt

- **1.1** `AgentAssistGroup(AssistGroup)` con `origin: Literal["catalogo","sustitutos"]`. **Primero del
  tramo.** Subclase, no campo en el modelo compartido. Adición pura.
- **1.2** `prompts/assist/v6.md`: el *Sistema* de `v5` **sin una coma de diferencia**, más **una sola
  tarea** — la del agente — con la prohibición de marcadores de `v5`.
  `AGENT_PITCH_PROMPT_VERSION = "assist/v6"`. **`PROMPT_VERSION` y `v5.md` no se tocan.**
- **1.3** `get_unscoped_principal` en la ruta del agente. Sustitutos e inventario **intactos**.
- **1.4** Regenerar `ai-service/openapi.json` y **sustituir el *fixture*** del snapshot con sus adiciones
  permitidas declaradas.

### Tramo 2 · `backend/` — el consumidor que no existe · **gobierna la línea de corte**

- **2.1** Método en `IAiGatewayClient` e implementación en `AiGatewayClient`.
- **2.2** Cliente con nombre `ai-agent`: `AgentTimeoutMs = 18000`, `HttpClient.Timeout` infinito,
  presupuesto en el *pipeline*, reintento **sólo** para `IsConnectionNeverOpened`, breaker HTTP-only.
- **2.3** El breaker **no cuenta `stop_reason=fallo_proveedor`**, y el comentario escribe por qué.
- **2.4** DTO del agente: el `FreeQuerySearchResponse` de C40 **más** `partial`, `stopReason`,
  `iterations`, `toolCallsUsed`, `trace`, `agentPromptVersion`. Hidratación por `AssistedSearchResultDto`.
- **2.5** Validación de los tres topes con FluentValidation, para no delegar el 422.
- **2.6** `agentAvailable` en `AiSearchAvailabilityResponse` y en `GetAvailability`, reutilizando el
  predicado extraído por C40_FIX.
- **2.7** `SearchOrigin.AssistedAgent = 5`, **sin migración** (se persiste con `HasConversion<int>()`).
- **2.8** Servicio de aplicación y endpoint, con *scoping* por rol idéntico al de C40.

### Tramo 3 · `frontend/` — la pantalla, en orden de frecuencia medida

- **3.1** Tipos TypeScript y `agentAssistService`.
- **3.2** Ruta `/sales/new/agent` en `routing/routes.tsx` y **cuarta tarjeta** en el hub, con los tres
  estados de la sonda.
- **3.3** Hilo con **un bloque de respuesta por turno**; sólo el último abierto.
- **3.4** Compositor con los contadores del **transcript que se va a enviar**, y cierre con motivo al
  alcanzar cualquiera de los tres topes.
- **3.5** Bloque de respuesta **sin filas primero** (19,6 %), después con filas y con los dos rótulos de
  `origin`.
- **3.6** Tabla de copy de los **diez** `stop_reason` y de los avisos del agente.
- **3.7** La traza, colapsada, como escalera de pasos.
- **3.8** Cinta de `partial` — **la última**: sirve al 2,0 % del arm servido.

### Tramo 4 · `frontend/`

- **4.1** Contador de coste acumulado de la sesión en la barra fija. **El único que no arregla nada que
  hoy engañe.**

---

## 4 · Lo que este ticket declara y no pide

- El ***streaming*/SSE** del argumentario.
- **Preguntar por el stock de una tienda concreta o de varias.** `ai-service/src/jbg_ai/api/auth.py:27`:
  *«un `pos_id` comodín es exactamente lo que nunca debe existir»*. **Cambio de modelo de autorización,
  no una tool más.**
- El **desglose de `usage` por etapa**.
- La **telemetría de la ficha** y el **registro de la consulta de ámbito global** (migración de EF Core).
- Los **escenarios puntuados del agente** — son de C38.
- **Recalibrar el presupuesto de herramientas**, aunque se mida que el efectivo es **6 y no 8**: nunca
  se observó 7 ni 8, porque con 4 llamadas concurrentes el bucle para cuando la siguiente tanda cruzaría
  el tope. **Se declara.**
- Una **segunda pasada** de medición.
- **Limpiar retroactivamente** las cifras de recuperación de C32b — no se puede (§6).
- Una **séptima herramienta**.

---

## 5 · El estado medido del sistema, y su grado de confianza

De `ai-service/evals/results/c32b-agent-sweep-293fe5c6e470.json`, 204 filas, `agent/v1` + `assist/v4`,
reagregado sin proveedor.

### 5.1 · Por arm, y el arm domina cualquier otra variable

| | **`gpt-4o`** · servido | `gpt-4o-mini` |
|---|---|---|
| p50 / p95 / máx | **5.311 / 9.021 / 11.917 ms** | 6.216 / 10.348 / 14.276 ms |
| `partial` | **2 · 2,0 %** | 60 · **58,8 %** |
| `presupuesto_tools` | **2** | **56** |
| `sin_mas_herramientas` | 86 | 24 |
| `aclaracion` / `rechazado` | 10 / 4 | 12 / 4 |
| Sin piezas | 20 · 19,6 % | 20 · 19,6 % |
| Retirada del argumentario | **13,1 %** | 16,0 % |
| `tokens_prompt` p50 / p95 / máx | **12.876 / 19.036 / 23.210** | — |

**`gpt-4o-mini` no vale para esta ruta**, y sostiene por comportamiento lo que el plan ya declaraba.

### 5.2 · Confianza por cifra

| Cifra | Valor | Confianza |
|---|---|---|
| Pivote `sin_existencias` | **3/3 en `gpt-4o`** (5/6 global) | ✅ **intacta** — camino de etiqueta, sin guard |
| Latencia | 5,3 / 9,0 / 11,9 s | ✅ intacta — C41 verificó que sin ámbito el SQL es 2-3 ms más lento contra un p95 dominado por el proveedor |
| `pitch_chars` | n=141 · **p50 386** · p95 514 · máx 605 | ✅ intacta |
| Retirada | 13,1 % | ✅ intacta |
| `dangling_citation` | 85 → 72 | ✅ intacta |
| Citas / avisos vacíos | **92,2 % / 96,1 %** | ✅ intacta |
| `partial` por arm | 2,0 % vs 58,8 % | 🟡 sostenible |
| Sin piezas | **19,6 %** | ✅ **robusta** — ver 5.3 |
| **Grupos por respuesta y saturación al tope** | 8 grupos en 104/204 | ❌ **tratar como NO medida** |

### 5.3 · Por qué el 19,6 % aguanta

| arm | sin piezas | `aclaracion` | `rechazado` | **«busqué y no encontré nada»** |
|---|---|---|---|---|
| `gpt-4o` | 20 | 10 | 4 | **6 de 102 · 5,9 %** |
| `gpt-4o-mini` | 20 | 12 | 4 | 4 de 102 · 3,9 % |

Los componentes dominantes **no consultan la proyección**. Sólo la cola es sensible al prefiltro.

### 5.4 · Herramientas invocadas

```
consultar_disponibilidad  ████████████████████████  376
buscar_catalogo           ███████████               166
buscar_sustitutos         ████████                  125   ← el pivote es rutina
consultar_conocimiento    ███████                   113
listar_familia            ██████                     94
pedir_aclaracion          ██                         24
```

**125 invocaciones de `buscar_sustitutos` es lo que pone `origin` (1.1) primero en el tramo 1.**

---

## 6 · El hallazgo de C41 tiene una segunda vida en el arnés, y es peor

C41 anotó que la manipulación del §8 de C40 se aplicó a `ai.pos_projection.refreshed_at` cuando el
guard lee `ai.sync_checkpoint.last_incremental_sync_at`. **Aquí no hay columna equivocada: no hay
ninguna comprobación, y los dos caminos leen cosas distintas.**

```
 ┌─ ARNÉS · agent_sweep ──────────────────┐   ┌─ CAMINO DE SERVICIO ─────────────┐
 │ resolve_pieces()            (:348)     │   │ resolve_scope()                  │
 │   └─ search.scope_buckets(MAO_AIR)     │   │   └─ projection_synced_at()      │
 │      retrieval/search.py:490-499       │   │      retrieval/orchestrator.py   │
 │      SELECT crudo · SIN GUARD          │   │      stale → degraded=unscoped   │
 │      ports.py:204 «Read by the         │   │                                  │
 │       evaluation only»                 │   │                                  │
 └────────────────────────────────────────┘   └──────────────────────────────────┘
       resuelve 4 etiquetas perfectas                sirve SIN ámbito
       por rancia que esté la proyección
```

**La aritmética:**

```
provenance.paced_seconds  =  9.870,8 s  =  2 h 44 min
techo de rancidez         =      3.600 s  =  1 h
arreglo manual            →  «caduca en una hora»  (informe de C41, §2.1)
drenaje automático        →  NO EXISTÍA: es de C41, cinco días posterior a la pasada
```

**A lo sumo las primeras ~74 de 204 filas corrieron con el prefiltro aplicado**, y es cota superior
—no se conoce la antigüedad en t=0—. El conjunto de **calibración corre al final**, así que las filas
del pivote van ~1 h 45 min pasadas el techo.

**Y no se puede limpiar a posteriori.** La procedencia no registra antigüedad, y el corte ingenuo
primeras-74 contra el resto (6,72 → 5,32 grupos de media; 9,5 % → 25,4 % de vacías) **está confundido
por composición**: las filas 1-74 son todas `load/gpt-4o` y el resto mezcla `calibration` y `mini`.
**Que no se pueda decidir es el hallazgo.**

> **Qué sobrevive, y hay que decirlo porque parecería caer con el resto.**
> `consultar_disponibilidad` llama a `search.availability_bucket(product_id, pos_id=pos_id)`
> **directamente** (`assist/tools.py:873`) y devuelve la edad al modelo como
> `antiguedad_proyeccion_segundos`, con la regla escrita en el comentario: *«Freshness travels with the
> label, and a stale projection degrades the observation instead of failing it: the rule is degrade,
> never remove»*. **Así que el pivote 3/3 se sostiene y con él la justificación de D6.**

**Decisión: se anota, no se rehace** (§13, Q-9), y el tramo 0 impide que vuelva a pasar.

---

## 7 · Componentes Afectados

- **`ai-service/`** — `api/routers/assist.py`, `api/schemas/assist.py`, `assist/agent.py`,
  `assist/constants.py`, `prompts/assist/v6.md` *(nuevo)*, `evals/agent_sweep.py`, `openapi.json`.
- **`backend/`** — `JoiabagurPV.Domain/Enums/SearchOrigin.cs`;
  `JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs`, `Services/AiGatewayClient.cs`,
  `Extensions/AiGatewayServiceCollectionExtensions.cs`, `Configuration/AiGatewayOptions.cs`, DTOs y
  servicio de aplicación del agente; `JoiabagurPV.API/Controllers/` (endpoint y sonda);
  `JoiabagurPV.Tests/`.
- **`frontend/`** — `pages/sales/agent.tsx` *(nuevo)*, `pages/sales/` (hub), `routing/routes.tsx`,
  `components/sales/agent/` *(nuevo: bloque de respuesta, traza, compositor)*, `services/`, `types/`.
  **`assisted-search-result-row.tsx` y `pitch-block.tsx` se consumen y NO se modifican.**
- **`openspec/`** — deltas de `sales-assistant-agent`, `assist-generation`, `ai-gateway-client`,
  `ai-free-query-search`, `ai-search-telemetry` y **una capability nueva** para el panel del agente
  (Q-8); `DEFERRED_TASKS.md` (entrada de C32b, cerrada por refutación).
- **`Documentos/`** — `epicas.md`, el plan de changes, `testing-*.md` si cambia el inventario de rojos,
  y el informe de C32b (anotación).

**No se toca:** `terraform/`, `.github/workflows/`, ninguna migración de EF Core ni de Alembic,
`pos-projection`, las seis herramientas.

---

## 8 · Especificaciones Técnicas

### 8.1 · `ai-service` · el contrato

```python
class AgentAssistGroup(AssistGroup):
    """Subclase y no campo en AssistGroup, por el precedente de AgentUsage: el modelo
    compartido es lo que publica POST /v1/assist/sale, y ensancharlo movería el esquema
    de esa ruta."""
    origin: Literal["catalogo", "sustitutos"]
```

`AgentAssistResponse.groups` pasa a `list[AgentAssistGroup]`. **Adición pura**: un cliente que ignore
`origin` recibe exactamente la respuesta que recibía.

### 8.2 · `ai-service` · el prompt

- `prompts/assist/v6.md`: cabecera con su fila en la tabla de versiones, *Sistema* **idéntico** al de
  `v5`, y `## Tarea · evidencia del agente` con la regla de `v5` —*«Cuando NO hay pieza anclada… no
  hables de precio ni de disponibilidad en absoluto»*— y el lenguaje comparativo permitido.
- `AGENT_PITCH_PROMPT_VERSION = "assist/v6"`.
- **`v4.md` no se borra**: tiene las cifras de C32b medidas contra él.

### 8.3 · `ai-service` · la ruta

`get_service_principal` → `get_unscoped_principal` en el *endpoint* del agente
(`api/routers/assist.py:340`). La ausencia de `pos_id` significa **no aplicar el prefiltro**, nunca un
comodín. `test_pos_scoped_route_still_rejects_it` se conserva **para sustitutos e inventario**.

### 8.4 · `ai-service` · el arnés

| Campo | Dónde | Qué |
|---|---|---|
| `price_placeholders`, `stock_placeholders` | por fila | recuento en el **primer** intento |
| `..._total`, `generations_with_a_*_placeholder` | resumen | agregados |
| `projection_age_seconds`, `projection_stale` | procedencia **y por fila** | contra `jpv_pos_projection_max_age_seconds` |

### 8.5 · `backend` · el cliente

```csharp
public const string AgentClientName = "ai-agent";
```

```
AddHttpClient("ai-agent")          → BaseAddress, Timeout = InfiniteTimeSpan
  .AddResilienceHandler("ai-agent-pipeline")
      AddRetry        MaxRetryAttempts = 1, ShouldHandle = IsConnectionNeverOpened
      AddCircuitBreaker  ShouldHandle = IsRetryable(args.Outcome)   ← HTTP-only, NO lee el cuerpo
      AddTimeout      AgentTimeoutMs = 18000
```

**Por qué el breaker no cuenta `fallo_proveedor`**, y va en el comentario del código:

| Alternativa | Por qué no |
|---|---|
| *Handler* que lee el cuerpo | Exige bufferizar la respuesta, parsear el JSON dos veces y acoplar el transporte al vocabulario cerrado del contrato |
| Circuito de dominio en el servicio | Correcto en capas, pero **inalcanzable**: ~13.000 tokens/petición contra 25.000 TPM = **1 petición/minuto**, así que la ventana de muestreo expira antes de acumular `MinimumThroughput` |
| Contar todas las `partial` | Se abriría sobre una ruta que **funciona como está diseñada** |

**Y hay precedente explícito**: el breaker de `ai-assist` ya declara que *«a 200 the service degraded
internally… is not a failure: Python degraded, and the breaker protects from Python not answering»*.
Quien avisa a la pantalla es **la sonda**.

### 8.6 · `backend` · el DTO

`FreeQuerySearchResponse` (C40) **más**: `Partial` (bool), `StopReason` (string, vocabulario cerrado de
diez), `Iterations` (int), `ToolCallsUsed` (int), `Trace` (lista de iteraciones), `AgentPromptVersion`
(string). Los grupos llevan `Origin`. Miembros hidratados con `AssistedSearchResultDto`.

**La traza publica por iteración**: herramientas invocadas, resultado de cada una y su causa si falló,
tokens y milisegundos. **Nunca argumentos ni contenido de observaciones** — el contrato los excluye.

### 8.7 · `backend` · la validación de los topes

`AgentAssistRequestValidator`: `Turns` entre 1 y 12; `Text` entre 1 y 500 por turno; **suma de todos
los turnos ≤ 4.000**; al menos un turno `operario`. Mensajes en es-ES. Es lo que evita que el operario
se estrelle contra un 422 de Python.

### 8.8 · `backend` · la sonda y la telemetría

- `AiSearchAvailabilityResponse` gana `AgentAvailable`, calculado con el predicado extraído por C40_FIX
  y **la cadena de credencial del agente** —agente → assist → enriquecimiento—.
- `SearchOrigin.AssistedAgent = 5`, con su comentario de por qué no se pliega en `AssistedGenerative`.
  **Sin migración.**

### 8.9 · `frontend` · la pantalla

```
┌─ BARRA FIJA ─────────────────────────────────────────────┐
│ Ámbito: [Tienda ▾] │ Todas las tiendas (sólo admin)      │
│ Sesión: 3 peticiones · 41k tokens · 0,08 €               │
│ ⚠ Modo agente · ~5 s típico, hasta 12 s [Panel directo →]│
└──────────────────────────────────────────────────────────┘
┌─ HILO · SCROLLEABLE (el rastro de auditoría) ────────────┐
│ operario: …                                              │
│ ╭ respuesta N · COLAPSADA: una línea con chips ─╮        │
│ ╭ respuesta N+1 · ABIERTA ──────────────────────╮        │
│ │ tira de estado: parada · vueltas · tools      │        │
│ │ ARGUMENTARIO  (pitch-block, sin tocar)        │        │
│ │ > Fuentes   ← 7,8 %     ! avisos  ← 3,9 %     │        │
│ │ ── Coincidencias ──  (origin: catalogo)       │        │
│ │ ── Alternativas  ──  (origin: sustitutos)     │        │
│ │ [assisted-search-result-row, sin tocar]       │        │
│ │ > Cómo lo ha averiguado  (traza, colapsada)   │        │
│ ╰───────────────────────────────────────────────╯        │
└──────────────────────────────────────────────────────────┘
┌─ COMPOSITOR FIJO ────────────────────────────────────────┐
│ [caja]        turnos 6/12 · 2.466/4.000 car.             │
│               ↑ CUENTA LOS TURNOS DEL ASISTENTE          │
└──────────────────────────────────────────────────────────┘
```

**La economía del transcript, que fija la profundidad:**

```
6 intercambios = 6 operario + 6 asistente = 12 turnos   ← EL TOPE DE TURNOS MUERDE PRIMERO
caracteres: 6×25 + 6×386 (p50) = 2.466 / 4.000
            6×25 + 6×605 (máx) = 3.780 / 4.000
```

| Caso | Qué lleva el turno `asistente` |
|---|---|
| Argumentario servido | **el argumentario íntegro** |
| Argumentario retirado (13,1 %) | **línea sintética** con los SKU y la mención de que no hubo argumento |
| Repregunta | la repregunta |

El contrato lo autoriza: *«`asistente` is **attributed and never trusted**: this service stores no
conversation, so every turn arrives from the client»*.

### 8.10 · Specs de OpenSpec

| Capability | Operación | Qué |
|---|---|---|
| `sales-assistant-agent` | **MODIFIED** | `origin` en el grupo de la respuesta; la ruta acepta token sin punto de venta |
| `assist-generation` | **MODIFIED** | la tarea del agente se sirve con `assist/v6` y no escribe marcadores |
| `ai-gateway-client` | **ADDED** | el método del agente, su cliente con nombre y su política de *timeout* y circuito |
| `ai-free-query-search` | **MODIFIED** | `agentAvailable` en la sonda |
| `ai-search-telemetry` | **MODIFIED** | quinto `SearchOrigin` |
| *capability nueva* (Q-8) | **ADDED** | el panel del agente: hilo, bloque por turno, traza, topes y los tres estados de la puerta |
| `sales-assistant-tools`, `ai-sales-assist`, `assisted-search-panel`, `pos-projection` | **sin tocar** | y es alcance |

> **Recordatorio del validador:** en una delta, la descripción que sigue a `### Requirement:` se valida
> **leyendo sólo su primera línea física**. Se escriben en **una sola línea larga**.

---

## 9 · Arquitectura

- **La frontera estrecha se respeta entera.** Python decide qué recuperar y redacta; **la autoridad
  sobre precio y existencias sigue siendo de .NET**, por candidato y por tienda. La etiqueta de
  `consultar_disponibilidad` gobierna **una sola cosa**: si el bucle pivota — *«para la decisión del
  bucle y para la calibración, nunca para el payload»*.
- **El bucle no escribe la respuesta.** Sólo reúne evidencia; el argumentario lo redacta la misma capa
  de generación con la misma puerta numérica. Por eso `AgentAssistResponse` es subclase.
- **Cliente por ruta y no compartido**, el patrón que C34 dejó escrito: un modelo lento no debe abrir el
  circuito de recuperación y empujar al llamante a su alternativa léxica.
- **Estado cero en el servidor.** El transcript viaja en la petición porque `jbg-ai` **no guarda
  conversación**, propiedad que las capabilities de generación y enrutado ya sostienen con tests. El
  precio es que el cliente controla el factor que domina el coste, y de ahí que los tres topes sean
  parte del contrato.
- **Capas:** Domain (`SearchOrigin`) → Application (cliente, DTO, servicio) → API (endpoint, sonda) →
  Frontend, según `Documentos/modelo-c4.md`.
- **Breaking changes:** ninguno en REST. `openapi.json` **se mueve** por adición pura, con el mecanismo
  de adiciones permitidas del snapshot.

---

## 10 · Criterios de Aceptación

Los dieciséis escenarios de [HU-AIENG-042](../../../Documentos/Historias/AI-Eng/HU-AIENG-042.md), que
son la fuente. En resumen: la puerta con sus **tres** estados; una conversación de catálogo con filas
rotuladas; el pivote separado y rotulado; **una respuesta con prosa y cero piezas**; la repregunta; la
respuesta cortada distinguible de la completa; **los topes dichos antes del 422**; el argumentario
retirado sin romper el hilo; el cambio de ámbito reiniciando el hilo con aviso; la ruta sirviendo sin
punto de venta; **el argumentario sin marcadores y `v5` intacto**; la pasada midiendo el sistema y no su
desconfiguración; el circuito que no se abre por una ruta que funciona; y el fuera de alcance explícito.

---

## 11 · Definición de Hecho (DoD)

- [ ] Código por capas según `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] **Líneas base de las dos suites medidas ANTES de tocar nada**, guardando los **nombres**:
      `dotnet test` (~50 rojos preexistentes) y `npm run test` en `frontend/` (~113-114 de 729 en 14
      ficheros). **Leer la línea de resumen, no el código de salida**
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus, `Método_Escenario_ResultadoEsperado`, ≥70 %.
      **Cliente fresco de la factoría** para cualquier llamada no autenticada, y `PointOfSale.Phone`
      fijado explícitamente
- [ ] Frontend: Vitest + RTL + MSW, `should [comportamiento] when [condición]`, queries accesibles,
      ≥70 %. **Envolver en los providers o mockear los hooks** — `cart.test.tsx` es el fichero a copiar
- [ ] `ai-service`: `uv run pytest` en verde **sin llamadas reales** a proveedor, embeddings ni RDS
- [ ] `ai-service/openapi.json` regenerado y el *fixture* del snapshot sustituido con sus adiciones
      declaradas
- [ ] **`tsc --noEmit` filtrado a los ficheros propios, sin errores nuevos** — `npm run build` es verde
      sobre un error de tipos, así que no basta
- [ ] **Ninguna migración** de EF Core ni de Alembic creada
- [ ] `assist/v5.md` **sin diff** y `PROMPT_VERSION` **sin cambio**, comprobado con `git status`
- [ ] `assisted-search-result-row.tsx` y `pitch-block.tsx` **sin diff**
- [ ] Deltas en `openspec/changes/add-frontend-agent-panel/specs/` y
      **`openspec validate --all --strict` con `0 failed`**
- [ ] **La pasada de medición tomada con el contenedor arriba y el drenaje de C41 encendido**,
      verificado en `/health`, con el artefacto persistido (`run_id`, `git_sha`, `prompt_version`,
      antigüedad de proyección)
- [ ] Las **siete cifras** del §10 del informe v2 publicadas
- [ ] Las **dos anotaciones** escritas (§13, Q-9)
- [ ] `Documentos/` al día según la tabla *Post-Implementation Documentation Update*
- [ ] **Comprobación manual en el entorno levantado**, con los dos roles — es la puerta que cazó el
      defecto de C40 y que ningún test habría encontrado
- [ ] Sin TODO/FIXME sin tarea asociada · UI en es-ES y moneda EUR (€)

---

## 12 · Requisitos No Funcionales

- **Seguridad.** JWT interno HS256 con `user_id`, `role`, `pos_id`, `trace_id`, y **el token manda sobre
  el body** — `AgentAssistRequest.pos_id` está *«accepted for client compatibility and ignored»*. RBAC
  Admin/Operador; el ámbito global abierto a los dos en backend y ofrecido **sólo al administrador** en
  el frontal; **no se puede nombrar una tienda no asignada**. Secretos en SSM `/jpv/prod/*`.
- **Rendimiento.** Presupuesto de **18 s** para `ai-agent`, contra el máximo medido de 11.917 ms. p95
  objetivo ≤ 12 s extremo a extremo. **La cuota de tokens por minuto, y no el dinero, fija el ritmo**:
  ~13.000 tokens/petición contra 25.000 TPM ⇒ **una petición por minuto**. La interfaz dice el coste
  **antes** de que se pulse. Bundle inicial < 500 KB.
- **Observabilidad.** `trace_id` propagado; `stop_reason=fallo_proveedor` como **métrica y log**;
  `agent_prompt_version` en cada respuesta. **El texto del argumentario no se persiste ni se loguea** —
  sólo `trace_id`, `prompt_version`, `model`, `usage`, latencia, `citation_id` usados, códigos de aviso,
  `abstained`, longitud y hash. La excepción declarada es el arnés.
- **Integridad.** Vender desde el hilo reutiliza el camino de venta existente, con `Sale.Price` como
  *snapshot*; `hasStock === null` deshabilita la venta en vez de suponer existencias.

---

## 13 · Preguntas Abiertas → Decisiones (cerradas antes de los artefactos de OpenSpec)

| # | Pregunta | Decisión |
|---|---|---|
| **Q-1** | ¿`assist/v6.md` o `assist/v5-agent.md`? | **`assist/v6.md`**: la tabla de versiones es el índice y un sufijo rompe la serie |
| **Q-2** | ¿Editar `v5` o crear `v6`? | **`v6`, sólo para el agente.** Editar `v5` haría mentir su fila justo cuando C38 va a medirlo; un `v6` con ambas constantes fusionaría dos versiones deliberadamente apartadas. **Test de que el *Sistema* de `v6` es idéntico al de `v5`** |
| **Q-3** | ¿18 s o 15 s de presupuesto? | **18 s.** 15 dejan 3,1 s sobre el máximo y el modo de fallo es cortar lo ya pagado |
| **Q-4** | ¿El circuito cuenta `fallo_proveedor`? | **No.** A 1 petición/minuto no hay muestra que abra la ventana; se instrumenta como métrica y **la entrada de `DEFERRED_TASKS.md` se cierra por refutación** |
| **Q-5** | ¿Qué va en el turno `asistente`? | **Argumentario íntegro**; **línea sintética con SKU** cuando se retiró o fue repregunta. Profundidad resultante: **6 intercambios** |
| **Q-6** | ¿Qué cuenta el contador del compositor? | **El transcript que se va a enviar**, turnos del asistente incluidos |
| **Q-7** | ¿El panel ofrece ámbito global? | **Sí, sólo al administrador**, copiando C40 sin endurecerlo, con la línea de consecuencia diciendo que **el pivote se apaga**. La alternativa —no ofrecerlo— queda declarada y descartada |
| **Q-8** | ¿Capability nueva o ampliar `assisted-search-panel`? | **Nueva.** Aquélla describe *una consulta → resultados*; el agente es *una conversación*. Ampliarla daría una spec bien formada que habla de dos pantallas |
| **Q-9** | ¿Se rehace la pasada de C32b? | **No: se anota.** El artefacto no registra antigüedad y el corte está confundido por composición. **El pivote se anota como superviviente**, porque parecería caer con el resto |
| **Q-10** | ¿Una pasada o dos? | **Una, después del cambio.** Línea base **prestada de C40 y declarada**: 3 de 90 y 0 retiradas |
| **Q-11** | ¿La traza colapsada o abierta? | **Colapsada**, con las vueltas visibles en la tira de estado |
| **Q-12** | ¿La tarjeta lee la sonda al montar o al pulsar? | **Al montar**: la sonda no gasta cupo ni llamada al proveedor, y ése es su motivo de existir |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
añada ruta bajo `/v1`, **no** modifique `assist/v5` ni `PROMPT_VERSION`, **no** toque las seis
herramientas, **no** abra migración, **no** modifique `assisted-search-result-row` ni `pitch-block`, y
**no** cambie la degradación ante una proyección rancia.

---

## 14 · Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Máxima.** Es el primero de los tres pendientes y **bloquea a C38**. Da superficie al único de los cinco pilares que no la tiene, y sin ella el pilar no entra ni en la URL pública ni en el vídeo |
| **Impacto** | 5/5 |
| **Complejidad** | 4/5 — **tres capas y el contrato se mueve.** Abarata: el bucle está entregado y medido, dos componentes se reutilizan enteros, la hidratación ya cubre todos los miembros. Encarece: el hilo con bloque por turno no tiene precedente y la traza es nueva |
| **Estimación** | _Pendiente_ — a fijar en refinamiento |
| **Tags** | `ai-service` · `backend` · `frontend` · `sales-assistant-agent` · `assist-generation` · `ai-gateway-client` · `prompt-version` · `named-http-client` · `circuit-breaker` · `search-origin` · `eval-harness` · `contract-change` · `no-migration` |

---

## 15 · Enlaces o Referencias

- **Historia origen:** [HU-AIENG-042](../../../Documentos/Historias/AI-Eng/HU-AIENG-042.md)
- **Change:** `openspec/changes/add-frontend-agent-panel/` (C42)
- **Exploración v2 (gobierna):**
  [c42-exploration-decisions-v2.md](../../../Documentos/Proyecto%20Final%20AIEng/informes/c42-exploration-decisions-v2.md)
- **Exploración v1 (base):**
  [c42-exploration-decisions.md](../../../Documentos/Proyecto%20Final%20AIEng/informes/c42-exploration-decisions.md)
- **Ficha del plan:** [§3 · C42](../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Diseño RAG:** [proyecto-final-diseno-rag-joiabagur.md](../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Specs vivas modificadas:** [`sales-assistant-agent`](../../specs/sales-assistant-agent/spec.md) ·
  [`assist-generation`](../../specs/assist-generation/spec.md) ·
  [`ai-gateway-client`](../../specs/ai-gateway-client/spec.md) ·
  [`ai-free-query-search`](../../specs/ai-free-query-search/spec.md) ·
  [`ai-search-telemetry`](../../specs/ai-search-telemetry/spec.md)
- **Specs que NO se tocan, y es alcance:**
  [`sales-assistant-tools`](../../specs/sales-assistant-tools/spec.md) ·
  [`ai-sales-assist`](../../specs/ai-sales-assist/spec.md) ·
  [`assisted-search-panel`](../../specs/assisted-search-panel/spec.md) ·
  [`pos-projection`](../../specs/pos-projection/spec.md)
- **Deuda que cierra por refutación:** [`DEFERRED_TASKS.md`](../../DEFERRED_TASKS.md), entrada de C32b
  sobre *timeout* y circuito
- **Informe a anotar:**
  [c32b-implementation-measurements.md](../../../Documentos/Proyecto%20Final%20AIEng/informes/c32b-implementation-measurements.md)
- **Tickets anteriores:** [T-AIENG-041](../archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md) ·
  [T-AIENG-040](../archive/2026-09-25-add-frontend-free-query-panel/ticket.md) ·
  [T-AIENG-040-FIX](../archive/2026-09-26-c40-fix-all-shops-scope-unreachable/ticket.md)
- **Procedimientos:**
  [Procedimiento-TicketsTrabajo.md](../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) ·
  [Procedimiento-UserStories.md](../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Testing:** [testing-backend.md](../../../Documentos/testing-backend.md) ·
  [testing-frontend.md](../../../Documentos/testing-frontend.md)

---

## 16 · Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-26 | **Apertura del ticket**, con las dos pasadas de exploración ya hechas y las **dieciséis decisiones cerradas** — las doce del v1 más D13 a D16. Nace con el **tramo 0 de instrumentos** por delante, porque el v1 pedía medir antes de escribir la primera tarea y **el instrumento no existe**. La línea de corte va **reordenada respecto al v1**: el arreglo del prompt baja del primer puesto —C40 ya midió el análogo en 3 de 90 y 0 retiradas— y el **consumidor .NET pasa a gobernar**, que es el 100 %. Se documenta el **§6**: el hallazgo que C41 anotó sobre C40 tiene una segunda vida en el arnés del agente, donde no hay columna equivocada sino **ninguna comprobación**, y se decide **anotar y no rehacer** dejando constancia de que **el pivote sobrevive** |
