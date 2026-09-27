# T-AIENG-032b: Sales-assistant agent loop — the decision layer, its six budgets and the pass that fixes them (C32b)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-032a](../../archive/2026-09-20-add-sales-assistant-tool-registry/ticket.md),
> [T-AIENG-031](../../archive/2026-09-16-add-guardrails-and-intent-router/ticket.md) y
> [T-AIENG-030b](../../archive/2026-09-14-add-assist-pitch-generation/ticket.md).

**HU origen:** [HU-AIENG-032b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032b.md)
**Change:** `add-sales-assistant-agent-loop` (C32b) · **Épica:** EP15
**Rama:** `c32b-add-sales-assistant-agent-loop` · **Anterior:** C32a, el registro · **Siguiente:** C38

---

## Título

Añadir el **bucle agéntico del asistente de venta** sobre el registro que dejó C32a: *function
calling* manual con ejecución paralela, **seis presupuestos duros**, `partial: true`, traza doble,
**`POST /v1/assist/agent`** con transcripción multi-turno en la petición, **dos prompts versionados**
y una **pasada con proveedor real de dos brazos** que fija el presupuesto de tokens y el de reloj y
responde las dos preguntas que C32a dejó abiertas. **`POST /v1/assist/sale` no se toca.**

---

## Contexto y Problema

C32 se partió el 2026-09-20. C32a entregó la mitad sin proveedor —las seis tools, el registro y sus
invariantes— y dejó a C32b **la única pieza cara**: la capa de decisión.

De las cuatro cosas que el PF evalúa de la capa agéntica —**el bucle, el presupuesto duro, el
invariante de solo-lectura y el `partial: true`**—, C32a entregó **una**. Este ticket entrega las
tres restantes, y con ellas la fila de ablación del §11.4 que justifica el sobrecoste de la
autonomía: *pipeline contra agente, mismo golden set, mismas tools*. Esa fila desaparecería si el
bucle **sustituyera** al pipeline en vez de convivir con él, que es exactamente por lo que la ruta es
nueva y `/v1/assist/sale` sigue intacta.

### Estado actual del código, verificado en el repositorio

| Pieza | Fichero | Estado |
|---|---|---|
| `build_registry()`, `registry.schemas()`, `registry.invoke()`, `registry.embedding_calls` | `assist/tools.py` | ✅ existe — C32a, con puertos inyectados |
| `verify_read_only(registry)` en la construcción | `assist/tools.py` | ✅ existe — C32a |
| `generate_pitch()`, `free_query_payload_from()`, `PitchTask`, `QUERY_OPEN`/`QUERY_CLOSE` | `assist/pitch.py`, `assist/prompt.py` | ✅ existe — C30b |
| `classify_query()`, `RoutingOutcome`, `clarification_for()` | `assist/routing.py` | ✅ existe — C31 |
| `TokenUsage` con `__add__` y `calls` | `assist/llm.py` | ✅ existe — C30b |
| Puerto de *function calling* | — | ❌ **cero** — `AssistLlm.generate()` está fijado a `response_format=AssistPitch`; `RouterLlm.classify()` a `RouteDecision` |
| Bucle, iteraciones, presupuestos, `partial` | — | ❌ **cero** |
| `POST /v1/assist/agent` | `ai-service/openapi.json` | ❌ **cero** — el contrato congelado **nunca reservó ruta** para el agente de venta |
| Transcripción multi-turno | `api/schemas/assist.py` | ❌ **cero** — `AssistRequest.query` es una cadena suelta con `max_length=500` |
| Prompt del bucle | `ai-service/prompts/` | ❌ **cero** — hay `assist/v1-v3` y `router/v1-v3`, ninguno del agente |
| `Usage.calls` en el contrato | `api/schemas/common.py` | ❌ **no existe** — el techo de tres de C31 se asegura **sólo en código**, no en el cable |
| Pool de conexiones | `db/engine.py` | ⚠️ **5 con `max_overflow=0`**; `SqlAlchemyProductSearch` abre un `session_scope` por método |
| Consulta puntual de disponibilidad en .NET | `Controllers/AiIndexFeedController.cs` | ❌ sigue **identificada, acotada y no hecha** (`DEFERRED_TASKS.md`) |

### Los cinco hallazgos de la exploración que gobiernan el diseño

1. **El enrutado que proponía la ficha cuesta O(N²) y rompe su propio techo.** *«Clasificar todos los
   turnos»* con contrato sin estado son **N clasificaciones en la petición N**: 15 llamadas en una
   conversación de cinco turnos en vez de 5, y el techo de ocho roto desde el turno 8. Además compra
   dos veces la misma respuesta a temperatura cero, que es el argumento con el que C31 rechazó el
   reintento del clasificador.
2. **El turno de seguimiento es elíptico y la matriz de C31 se midió sobre consultas sueltas.**
   `«¿y en dorado?»` en solitario clasifica como insuficiente y produciría una repregunta sobre un
   eje que la conversación acaba de responder.
3. **No existe puerto de *function calling*.** Hacen falta un tercer puerto, una tercera cadena de
   credencial y una tercera variable de modelo.
4. **El ×19 de coste se descompone en ×5 de tokens y ×4 de modelo.** Derivado de cifras medidas aquí:
   enrutador **0,00205 USD** (C31) más argumentario **0,00077 USD** sobre 120 generaciones (C30b) dan
   un pipeline de ~**0,0028 USD/petición**; el bucle en `gpt-4o` con cinco vueltas sale ~**0,054 USD**.
   El ×5 es estructural; el ×4 es **elección reversible con una variable**.
5. **Falta el presupuesto de reloj de pared**, que es el único que un mostrador siente.

---

## Componentes Afectados

- **`ai-service/src/jbg_ai/assist/`** — `agent.py` (nuevo, el bucle), `agent_llm.py` (nuevo, el
  puerto), `transcript.py` (nuevo), `constants.py` (ampliado: presupuestos, versiones de prompt,
  quinta causa).
- **`ai-service/src/jbg_ai/api/`** — `schemas/assist.py` (dos modelos nuevos), `routers/assist.py`
  (ruta nueva y resolución del cliente del agente).
- **`ai-service/src/jbg_ai/evals/`** — `agent_sweep.py` (nuevo, dos brazos).
- **`ai-service/prompts/`** — `agent/v1.md` (nuevo), `assist/v4.md` (nuevo; **`v3` intacto**).
- **`ai-service/evals/agent/`** — `load-set.yaml` y `calibration.yaml` (nuevos).
- **`ai-service/openapi.json`** — **se regenera**. Primera vez desde C30a.
- **`ai-service/tests/`** — `assist/test_agent.py`, `assist/test_transcript.py`, `api/test_agent_route.py`.
- **`openspec/`** — change `add-sales-assistant-agent-loop`, su delta, y **`## MODIFIED` sobre la
  capability viva `sales-assistant-tools`**.
- **`Documentos/`** — `epicas.md`, plan de changes, `ai-service/README.md`, `tests/README.md`,
  `openspec/config.yaml`, `.env.example`.

**No se tocan:** `backend/`, `frontend/`, `terraform/`, `.github/workflows/`, `alembic/`,
`ai-service/evals/golden/`. **Sin migración de EF Core.**

---

## Especificaciones Técnicas

### ai-service — el puerto del agente

```text
jbg_ai/assist/agent_llm.py

  AgentToolCall   id · name · arguments
  AgentStep       tool_calls · usage · finish_reason      ← SIN campo de texto
  AgentLlm        Protocol:  async decide(messages, tools) -> AgentStep
  LiteLlmAgentClient   temperatura 0 · sin response_format · num_retries 0 · timeout explícito
```

**El tipo no tiene dónde poner prosa**, y ésa es la especificación. *«El contenido textual de las
vueltas se descarta»* deja de ser disciplina y pasa a ser verdad del tipo — el mismo criterio con el
que C32a comprobó el invariante de solo-lectura por introspección en vez de con un `writes: bool`.
El adaptador descarta el texto en la frontera y registra **longitud y digest**, nunca el texto.

### ai-service — el bucle y sus seis presupuestos

```text
  clasificar el turno que se contesta        1 llamada, y sólo una
      └─ rechazo → cortocircuito, 0 tools, códigos de C31
  ┌── por vuelta, hasta 5 ────────────────────────────────────┐
  │   decide(messages, registry.schemas())                    │
  │       sin tool_calls            → parar (modelo terminó)  │
  │       pedir_aclaracion          → parar (TERMINAL)        │
  │   asyncio.gather(...)  tope de 4 concurrentes             │
  │   las que no caben en el presupuesto → presupuesto_agotado│
  │   acumular observaciones en el contexto y en la evidencia │
  └───────────────────────────────────────────────────────────┘
  generate_pitch(payload de evidencia, tarea nueva de assist/v4)   ≤2 llamadas
```

| Presupuesto | Valor | Cómo se hace cumplir |
|---|---|---|
| Iteraciones | **≤5** | `for … range(N)` con rama de agotamiento explícita |
| Llamadas a tool | **≤6** | contador acumulado entre vueltas; recorte por orden de emisión |
| Llamadas al proveedor | **≤8** | `1 + ≤5 + ≤2`, **derivado de las constantes** y nunca escrito como dígito; aserción al cierre al modo de C31 |
| Tokens | **medido en la pasada** | **post-hoc**: se acumula `prompt_tokens` y se corta tras la vuelta que lo excede |
| Contexto en caracteres | **medido en la pasada** | **pre-vuelo y determinista**, por sección y global |
| Reloj de pared | **medido en la pasada** | *deadline* de la petición entera |

Los **embeddings** van aparte, en `registry.embedding_calls`: `usage.calls` sigue significando
*llamadas de chat de una petición*, que es lo que C31 publicó y lo que un test pincha.

### ai-service — el guardarraíl de entrada

| Veredicto de `classify_query()` | `/v1/assist/sale` (no cambia) | `/v1/assist/agent` |
|---|---|---|
| `out_of_domain` / `not_in_catalogue` | cortocircuita | **cortocircuita en cualquier turno**, 0 tools |
| servido pero insuficiente | repregunta determinista | **se ignora** — la repregunta es del bucle, vía `pedir_aclaracion` |
| `index` = catalog / knowledge / both | decide qué retriever corre | **se descarta** — el agente elige su propia tool |

En esta ruta el clasificador **es un guardarraíl, no un enrutador**. Entra una consulta suelta y sale
un veredicto, así que la matriz de confusión publicada por C31 **no se toca**.

### ai-service — la evidencia que llega a la generación

```text
  observaciones ─► acumulador ─► FreeQueryPayload  ─► generate_pitch()
                      │
                      ├─ candidatos vistos, con tope de piezas distintas
                      ├─ SUSTITUTOS como grupo distinguido (vocabulario cerrado)
                      ├─ citas vistas
                      └─ etiquetas de disponibilidad ──✗ NO ENTRAN
```

**Ninguna etiqueta de disponibilidad entra.** La autoridad sobre el stock es de .NET (§6.2), la
proyección se desfasa minutos, `{{stock}}` es la única expresión de existencias que el contrato
admite, y `disponible` es literalmente miembro de `STOCK_MARKERS` en la puerta numérica.

El **tope de piezas distintas** es la regla de C30b aplicada: cada campo del *payload* ensancha la
lista blanca de numerales, y la puerta midió cero violaciones sobre un *payload* con **un** SKU.

### ai-service — los prompts

| Prompt | Fichero | Qué es |
|---|---|---|
| `agent/v1` | `prompts/agent/v1.md` | **Nuevo.** El mensaje de sistema del bucle: qué herramientas hay, cuándo pivotar, cuándo preguntar, y que su prosa se descarta |
| `assist/v4` | `prompts/assist/v4.md` | `v3` más una sección de tarea para la evidencia del agente, que explica qué es un grupo de sustitutos |
| `assist/v3` | `prompts/assist/v3.md` | **Intacto en disco.** Las 120 generaciones medidas contra él tienen que seguir siendo interpretables — precedente de C31 con `v1` y `v2` |

La respuesta del agente publica **las dos versiones**: la del argumentario conserva el significado que
`prompt_version` ya tiene, y la del bucle viaja en campo propio.

### ai-service — contrato y configuración

```text
POST /v1/assist/agent
  AgentAssistRequest    turns[{role, text}] · topes de turnos, de chars por turno y totales
                        top_k · context · locale · pos_id (aceptado e ignorado)
  AgentAssistResponse(AssistResponse)        ← SUBCLASE, para que la ablación sea un diff
                        + partial · iterations · tool_calls_used · stop_reason
                        + trace[] acotada · agent_prompt_version · usage con calls
```

- **`ai-service/openapi.json` SE REGENERA.** Movimiento de **adición pura**: ningún campo se retira ni
  cambia de tipo. Se verifica **hoja a hoja** como hizo C31, y la forma de `AssistResponse` queda
  pinchada como conjunto para que el test de C32a siga en verde.
- **Ajustes nuevos**, pinchados en `canonical_openapi_settings()` como los de C30b y C31:
  `JPV_AGENT_LLM_API_KEY` (cadena de respaldo `agent → assist → rag`, y se registra cuál ganó),
  `JPV_AGENT_LLM_MODEL` (**`openai/gpt-4o`**, y **nunca** hereda el del argumentario ni el del
  clasificador) y los *timeouts* y presupuestos que la pasada fije.
- **Sin credencial del agente, la ruta responde igual que hoy responde `/sale` sin credencial de
  generación**: no construye cliente y sirve lo que pueda sin bucle. Es el *fail-open*, la ablación y
  el *rollback* en uno.
- `POST /v1/assist/sale` es **idéntico**, campo a campo y techo a techo.

### ai-service — la traza, en dos formas

| Forma | Contenido | Por qué |
|---|---|---|
| **En el cable** | por iteración: nombres de tool, `ok`, causa, tokens, ms | Un consumidor .NET **loguea la respuesta**, y la regla viva de C30b y C31 es que el texto del operario no entra en almacenamiento durable. C38 necesita *«tools invocadas contra esperadas»*, y los nombres bastan |
| **En proceso** | lo anterior más argumentos y observaciones | La lee el arnés sin pasar por HTTP, como ya hacen todos los `evals/` |

### ai-service — la pasada, y su muro de contaminación

| Instrumento | Tamaño | Mide | Contaminación |
|---|---|---|---|
| `evals/agent/load-set.yaml` | ~60-100 **sintéticas generadas** | p50/p95 de tokens y de reloj, curva de crecimiento, coste por brazo | Ninguna: mide acumulación, no calidad |
| `evals/agent/calibration.yaml` | ~15-20 **a mano, con tool esperada por turno** | granularidad de las seis, tasa de pivote por etiqueta, iteración de `agent/v1` | **Declarado calibration-only.** C38 escribe sus 20-25 aparte, con comprobación de no solape |
| `evals/golden/` | 48 consultas | — | **NO SE TOCA.** Queda limpio para la ablación de C38 |

Dos tamaños porque son dos preguntas: **a temperatura cero repetir un escenario devuelve casi lo
mismo**, así que el p95 necesita variedad de transcripciones y las dos preguntas de C32a necesitan
verdad de terreno.

**Lo que la calibración responde, todo leído de la traza:**

```
granularidad      tool nunca elegida            → tool muerta
                  argumento_invalido recurrente → esquema confuso
                  NOMBRE DE TOOL INVENTADO      → el dato más informativo: qué tool falta
                  dos llamadas casi idénticas   → granularidad demasiado gruesa

etiqueta          sin_existencias  → debería pivotar   · fallo = infra-pivote
                  ultimas_unidades → NO debería        · fallo = SOBRE-pivote, el caro
                  disponible       → NO debería
                  sin_ambito       → NO debería        · fallo = el colapso que C32a prohíbe
```

Hay datos reales para ejercerlo: C25 midió **411 candidatos agotados de 3.774**, y en **MAO-AIR 13 de
48** consultas enseñaban una pieza agotada en el top-5. Es el punto de venta contra el que calibrar.

### ai-service — precondiciones de la pasada

1. **`SSL_CERT_FILE`** apuntando a un PEM que incluya la raíz del interceptor TLS de la máquina.
   `litellm` sale por `aiohttp`/`httpx`, que usan el bundle de `certifi` y **no** el almacén de
   Windows: sin esto toda llamada muere con `CERTIFICATE_VERIFY_FAILED`. Filtrar por la bandera de
   confianza al exportar **no basta**.
2. **`WindowsSelectorEventLoopPolicy`**, como ya hace `evals/assist_sweep.py`.
3. **`--dry-run`** (procedencia y tamaño, nada ejecutado) y **`--limit`** para una prueba de humo de
   tres transcripciones **antes** de la pasada larga.

Coste estimado de la pasada completa: **~7 USD y ~1,5 h de reloj** para los dos brazos, contra los
**0,0897 USD** que costó la de C30b. El dinero es irrelevante; el reloj no.

---

## Arquitectura

- **Frontera intacta.** *Python calcula parecidos y redacta; .NET calcula números y decide.* El bucle
  decide **qué mirar**, nunca qué vale ni cuánto queda, y ninguna cifra de stock o precio entra en su
  contexto.
- **Ruta separada como palanca de coste.** El apunte de S12 pone *«enruta: no mandes al agente lo que
  un pipeline resuelve»* como la palanca número uno, y D-1 **ya es ese enrutado**. Conviene decirlo
  porque es la decisión de coste más importante del change y estaba tomada sin nombrarse así.
- **Puertos inyectados**, el patrón de `assist/` desde C30a: el bucle recibe registro y cliente
  construidos, y ningún test abre un socket.
- **Se replica, no se reutiliza.** `LiteLlmAgentClient` no hereda de `LiteLlmAssistClient`: aquél
  fija `response_format` y éste no debe poder hacerlo. Mismo criterio con el que C31 replicó en vez de
  reutilizar.
- **Sin LangGraph, sin *checkpointer*, sin almacén de sesión.** El §9.2 lo descarta por escrito —*«no
  hay ramificación con estado ni reanudación que lo justifique»*— y un almacén chocaría con la
  propiedad *«nada se persiste»* que C30b y C31 dejaron con test. El punto de migración queda
  identificado.
- **Breaking changes:** **ninguno**. `AssistResponse` no pierde ni cambia campos; la ruta es nueva;
  `Usage` del contrato **no se amplía** —el `calls` viaja en el modelo de uso propio del agente—, de
  modo que el esquema de `/v1/assist/sale` queda idéntico. Lo que sí cambia y hay que declarar:
  `TOOL_FAILURE_CAUSES` gana un quinto valor, y eso es un `## MODIFIED` sobre una capability viva.

---

## Definición de Hecho (DoD)

- [x] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [x] `ai-service`: `uv run pytest` en verde **sin llamadas reales a LLM, embeddings ni RDS**; comparado **por nombres de test** contra la línea base, nunca por recuento — 1.576 / 0, 0 nombres desaparecidos (QA §1.1 y §12)
- [x] `ai-service/openapi.json` **regenerado y verificado hoja a hoja**; la forma de `AssistResponse` pinchada como conjunto y **sin cambios** — y desde la verificación independiente, contra el contrato de C32a guardado como fixture
- [ ] Nomenclatura `test_<unidad>_<escenario>_<esperado>`; fakes inyectados, ningún socket abierto en la suite — **no marcada: cierto de los tests de este change** (0 eventos bajo un guardia de sockets y de `psycopg`), **no de la suite**: 11 tests preexistentes de C30b/C31 salen a `api.openai.com` (`DEFERRED_TASKS.md`, QA §12)
- [x] Los **catorce escenarios** de [HU-AIENG-032b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032b.md) trazados a test nombrado — §6 del informe; la segunda cláusula del escenario 9 pasa a medición
- [x] Delta de spec en `openspec/changes/add-sales-assistant-agent-loop/specs/`, **incluido el `## MODIFIED` de `sales-assistant-tools`**, y **`openspec validate --all --strict` en verde** — no la forma de un solo change: 59 / 0
- [x] **Pasada con proveedor real ejecutada**, con artefacto JSON versionado y su procedencia (`run_id`, `git_sha`, versiones de prompt, modelo, recuento de índice) — sin los modelos del clasificador y del argumentario ni el `sha256` de los prompts, que el arnés registra desde la verificación independiente
- [x] **Presupuesto de tokens, de contexto y de reloj fijados por medición**, publicados con p50 y p95 y no sólo con la media
- [x] **Curva de crecimiento del contexto por vuelta** publicada, y **sobrecoste contra el pipeline** publicado — ×3,0, corregido desde ×7,6 (informe §3.3)
- [x] **Las dos preguntas de C32a** respondidas con cifra, o declaradas como limitación con su motivo
- [x] El **golden set de C24 no se ha usado** para calibrar ni para iterar ningún prompt, y se declara
- [x] Documentación actualizada según la tabla *Post-Implementation Documentation Update* de `openspec/project.md`, `.env.example` incluido
- [x] Informe de implementación con lo que la implementación refute de este ticket
- [x] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] Sin migración de EF Core (no aplica), sin cambios en `backend/`, `frontend/` ni `terraform/` — **no marcada: `backend/.env.example` cambió**, excepción declarada en el §8 del QA; ningún `.cs`, `.csproj` ni migración
- [x] UI no aplica: este change no llega a pantalla

---

## Requisitos No Funcionales

- **Seguridad.** El ámbito de lectura lo fija **el token** y nunca el cuerpo, como en todo `/v1`; el
  registro se construye por petición con el principal atado. **Los turnos atribuidos al asistente son
  falsificables por el cliente** y se tratan como dato igual que la consulta, con los mismos topes y
  el mismo delimitado. Ninguna tool escribe, y C32a lo comprueba al construir.
- **Privacidad.** Nada se persiste: ni transcripción, ni observaciones, ni razonamiento intermedio —
  D-2 lo resuelve solo, porque el texto de las vueltas no sale del proceso. **La consulta del operario
  no se escribe en ningún log**, y la traza del cable no lleva argumentos. El arnés de evaluación
  sigue siendo la excepción declarada y escribe sus propios ficheros.
- **Rendimiento y free-tier.** Pool de **5 sin overflow**: el paralelismo por vuelta se topa en 4 para
  que la última tool no espere `pool_timeout` y se lea como base de datos caída. El contexto acumulado
  es el factor dominante del coste, y por eso lleva cota determinista además del corte por tokens.
- **Latencia.** Peor caso **15-20 s**, contra los 5 s que el §6.4 declara para `/v1/assist`. Es la
  razón de la ruta separada y queda **declarado como limitación**, no mitigado: sin streaming y sin
  respuesta en dos fases.
- **Observabilidad.** `trace_id` propagado a cada vuelta y a cada ejecución de tool. La línea de log
  lleva iteraciones, tools gastadas, motivo de parada, tokens, coste y latencia; **nunca argumentos ni
  texto del modelo**. `stage=agent_client` una vez por proceso dice qué credencial y qué modelo
  ganaron, sin secreto.
- **Coste.** Publicado **por brazo de modelo**, con **distribución y no media** —los agentes tienen
  cola larga y es donde vive la sorpresa— y siempre **relativo al pipeline**, que es el número que
  justifica o no la autonomía.
- **Integridad de datos.** Ninguna escritura en ninguna parte. La proyección **degrada y nunca
  elimina**; la ausencia de fila no es cero.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto |
|---|---|---|
| **Q-1** | ¿Capability propia o ampliación de `assist-generation`? | **Capability propia** `sales-assistant-agent`. `assist-generation` pasa de 40 requisitos y describe otra ruta; es el mismo criterio con el que C32a se separó |
| **Q-2** | ¿La traza del cable es siempre presente o se pide por parámetro? | **Siempre presente y acotada.** Un campo opcional crea dos formas de respuesta que hay que probar por separado |
| **Q-3** | ¿El set de carga se genera con el simulador de mundo sintético o con un guion propio? | **Guion propio** en `evals/agent/`, sembrado del vocabulario real del catálogo |
| **Q-4** | ¿El tope de contexto es global o por sección? | **Por sección y además global**, para que una transcripción larga no se coma el presupuesto de observaciones |
| **Q-5** | ¿La pasada corre contra desarrollo o contra una copia congelada? | **Desarrollo**, con procedencia registrada, como la de C30b. Una copia congelada es más limpia y no existe |
| **Q-6** | ¿Cómo se distingue «el modelo paró» de «cortó un presupuesto»? | **Motivo de parada explícito** de vocabulario cerrado: `sin_mas_herramientas`, `presupuesto_iteraciones`, `presupuesto_tools`, `presupuesto_tokens`, `presupuesto_reloj`, `aclaracion` |
| **Q-7** | ¿El brazo `gpt-4o-mini` corre sobre los dos sets o sólo sobre el de carga? | **Sobre los dos.** Si sostiene el coste pero no la selección de herramienta, hay que verlo donde hay verdad de terreno |
| **Q-8** | ¿La ruta necesita comportamiento bajo `STUB_MODE`? | **Sí**, por consistencia: toda ruta `/v1` tiene comportamiento declarado con stubs, y ésta no debe ser la única excepción |

---

## Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Alta** — **taponea a C38 y a C39**, que son el cierre del proyecto. El §6 del plan marca C32a y C32b como «nunca se recortan» |
| **Estimación** | _Pendiente_ — complejidad **5/5**: el change más caro de los que quedan. Puerto nuevo, contrato que se mueve, seis presupuestos, dos prompts, dos sets de datos, pasada de dos brazos y una capability viva modificada |
| **Tags** | `ai-service` · `python` · `assist` · `agent-loop` · `function-calling` · `budgets` · `contract-change` · `real-provider-pass` · `C32b` · `EP15` |

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-032b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032b.md)
- **Ficha del plan:** [§3 · C32b](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) y la nota del **§0 del 2026-09-20**
- **Diseño RAG:** [§6.1, §6.4, §9.1, §9.2, §11.2, §11.4](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Capability que se modifica:** [`sales-assistant-tools`](../../../specs/sales-assistant-tools/spec.md)
- **Capability consumida:** [`assist-generation`](../../../specs/assist-generation/spec.md)
- **Informe de C32a:** [`c32a-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c32a-implementation-measurements.md)
- **Precedente de pasada con proveedor:** [`c30b-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30b-implementation-measurements.md)
- **Tickets precedentes:** [T-AIENG-032a](../../archive/2026-09-20-add-sales-assistant-tool-registry/ticket.md) · [T-AIENG-031](../../archive/2026-09-16-add-guardrails-and-intent-router/ticket.md)
- **Aplazado y no hecho:** [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) — la consulta puntual de disponibilidad en .NET
- **Procedimientos:** [Tickets de trabajo](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [User Stories](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Épica:** [EP15](../../../../Documentos/epicas.md)

---

## Historial de Cambios

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-09-20 | Creación del ticket a partir de la sesión de exploración de C32b, con las nueve decisiones que cierran la ficha y los cinco hallazgos que la reencuadran | Sergio Valdueza Lozano |
