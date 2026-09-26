# C32b — informe de implementación: el bucle agéntico, sus seis presupuestos y lo que la pasada refuta

**Change:** `add-sales-assistant-agent-loop` (C32b) · **Rama:** `c32b-add-sales-assistant-agent-loop`
**Fecha:** 2026-09-21 · **Historia:** [HU-AIENG-032b](../../Historias/AI-Eng/HU-AIENG-032b.md) · **Ticket:** [T-AIENG-032b](../../../openspec/changes/archive/2026-09-21-add-sales-assistant-agent-loop/ticket.md)
**Capability nueva:** `sales-assistant-agent` — 22 requisitos, 44 escenarios · **Modificada:** `sales-assistant-tools`

C32b entrega la mitad cara de C32: **el bucle de *function calling* con sus seis presupuestos,
`partial: true`, la transcripción multi-turno, `POST /v1/assist/agent`, dos prompts versionados y
una pasada de dos brazos con proveedor real.** De las cuatro cosas que el Proyecto Final evalúa de
una capa agéntica —el bucle, el presupuesto duro, el invariante de solo-lectura y el `partial`—
C32a entregó una y aquí van las tres restantes.

**Lo primero que hay que decir es que la pasada refutó el número central del diseño.** El
sobrecoste de la autonomía **no es ×19: es ×3,0**, y la descomposición «×5 estructural de tokens
por ×4 reversible de modelo» **no se sostiene** — el brazo barato baja el coste a ×1,1 pero topa un
presupuesto en el 66 % de las peticiones. Lo segundo es que **tres de los cuatro fallos que costaron
dinero o tiempo los encontró la propia pasada, no la suite**, y el más caro habría producido una
medición inservible sin que nada fallara.

> **Corregido por la verificación independiente (§11 de este informe, §12 del QA).** La primera
> versión de este informe publicaba **×7,6 y ×1,4** y una pasada de **~2,60 USD**. Las tres cifras
> descansaban en un coste del clasificador de 0,00205 USD atribuido a C31 que C31 nunca publicó:
> el propio artefacto muestra al clasificador gastando ~3.305 tokens de prompt en `gpt-4o` por
> petición, **0,0084 USD**. Las cifras de este informe salen ahora de
> `python -m jbg_ai.evals.agent_sweep --rescore`, que las recalcula desde el artefacto sin
> proveedor, y un test las fija.

---

## 1 · Qué se entregó

| Pieza | Fichero | Estado |
|---|---|---|
| Puerto de *function calling*, sin campo de texto | `assist/agent_llm.py` | **nuevo**, 284 líneas |
| Transcripción, sus tres topes y su delimitado | `assist/transcript.py` | **nuevo**, 198 líneas |
| El bucle, los seis presupuestos, la evidencia y las dos trazas | `assist/agent.py` | **nuevo**, ~1.000 líneas |
| Registro de evidencia en el registro de tools | `assist/tools.py` | ampliado (§2.1) |
| Vocabularios, presupuestos y versiones | `assist/constants.py` | ampliado, +190 líneas |
| Tarea del agente y marca de procedencia | `assist/prompt.py` | ampliado |
| `prompt_version` como parámetro | `assist/pitch.py` | ampliado (§2.4) |
| `AgentAssistRequest`, `AgentAssistResponse`, `AgentUsage`, la traza | `api/schemas/assist.py` | ampliado, +206 líneas |
| `POST /v1/assist/agent` y la cadena de credencial | `api/routers/assist.py` | ampliado, +134 líneas |
| Tres ajustes nuevos, fijados en el perfil canónico | `config/settings.py` | ampliado |
| Comportamiento con stubs | `stubs/responses.py` | ampliado |
| Prompt del bucle | `prompts/agent/v1.md` | **nuevo** |
| Prompt del argumentario del agente | `prompts/assist/v4.md` | **nuevo**; **v3 intacto** |
| Generador del set de carga | `evals/agent_sets.py` | **nuevo** |
| Arnés de la pasada de dos brazos | `evals/agent_sweep.py` | **nuevo** |
| Set de carga (82) y de calibración (20) | `evals/agent/` | **nuevos** |
| Suites del bucle, la transcripción, la ruta y los instrumentos | `tests/` | **nuevas**, 88 tests |

### Las puertas

| Puerta | Resultado |
|---|---|
| `uv run pytest` | **1.558 passed / 0 failed** al cerrar la implementación; **1.576 / 0** tras la verificación independiente |
| Sin proveedor, sin red, sin BD | **cierto de los tests de este change**, comprobado con un guardia de sockets y de `psycopg` con PostgreSQL arrancado: 0 eventos. **No de la suite entera**: 72 tests `db` preexistentes corren contra PostgreSQL por testcontainers cuando hay Docker, y 11 preexistentes de C30b/C31 salen a `api.openai.com` (`DEFERRED_TASKS.md`) |
| Comparación **por nombres** | línea base 1.469 → 1.558 · **0 desaparecidos** · 89 añadidos; → **1.576** · 0 desaparecidos · 18 más |
| `openspec validate --all --strict` | **59 passed / 0 failed** |
| `ai-service/openapi.json` | `43f70fda…` → `7c6a038e…` → **`d8d48f87…`** (checkout CRLF; *blobs* `dd8df91d…` → `8dd52feb…`), verificado hoja a hoja contra C32a (§5) |
| Pasada con proveedor | **204/204**, artefacto `c32b-agent-sweep-293fe5c6e470.json` |
| Coste real de la pasada | **3,82 USD**, cada etapa a su precio (`--rescore`) · **3,4 h de reloj**. La primera versión decía ~2,60 (§3.3) |
| Golden set de C24 | **intacto**; `git status` vacío sobre `evals/golden/` |

**La suite de `ai-service` está verde de fábrica** —1.469 de 1.469 al empezar— así que, como en
C32a, un rojo habría sido mío. **Tres tests preexistentes se modificaron**, ninguno se retiró ni se
renombró; los tres motivos están en §4.

---

## 2 · Las refutaciones de la implementación

### 2.1 · El ticket no lista `assist/tools.py`, y el contrato obliga a tocarlo

**Lo que dice el ticket.** *Componentes Afectados* nombra `agent.py`, `agent_llm.py`,
`transcript.py`, `constants.py`, los dos de `api/`, `evals/`, los prompts y los tests.
**`assist/tools.py` no aparece.**

**Lo que hay en el árbol.** La observación de C32a excluye **por regla** `product_id`, la
puntuación de recuperación y el título del documento. El contrato congelado los **exige**:
`AssistGroupMember` pide `product_id` y `score`; `Citation` pide `document_title`, `doc_type` y
`score`. **Ninguno se puede reconstruir desde una observación** — el `citation_id` da el *slug*, no
el título ni el tipo — así que el bucle no podía publicar ni un grupo ni una cita sin inventárselos.

**Qué se hizo.** `EvidenceLedger`: un registro por petición que las cinco tools con evidencia
rellenan con **el objeto que ya tenían en la mano**. Es la segunda banda lateral del registro y
tiene la forma exacta de la primera, `CountingEmbeddings`. **La forma de la observación no cambia**
y los 51 tests de C32a siguen verdes sin tocarlos.

**Por qué no debilita el invariante de solo-lectura, medido.** El *ledger* no declara ningún método
público, así que `_is_collaborator` devuelve `False` y **no aparece en `captured_collaborators` de
ninguna de las seis tools**. No está excluido por nombre como `Settings`, y **no se apoya en el
hueco del vocabulario de escritura** que C32a declaró: un *ledger* con un `save()` sería colaborador
y **fallaría** la comprobación. Pinchado en
`test_the_evidence_ledger_is_inert_to_the_read_only_check_by_construction`.

### 2.2 · La spec pedía los miembros de familia y el acumulador los perdía

El escenario dice «candidates, **family members** and corpus fragments» y la tarea 7.1 los nombra;
el acumulador sólo proyectaba candidatos y sustitutos. **Se corrigió el código, no la spec.** Al
hacerlo salieron dos cosas que ningún artefacto anticipa:

- **`FamilyMember` no trae `family_id`.** El puerto denormaliza el *nombre* de la familia en cada
  fila pero no su identificador, así que un roster de tres habría salido con `family_id: null` y
  tres miembros — **violando el invariante del contrato** *«familia nula implica exactamente un
  miembro»*.
- **No trae `score` ni `match_reasons`.** Se reutiliza el precedente literal de
  `_member_from_roster`: *«el roster es una enumeración y no una recuperación: nada ha coincidido,
  así que no hay motivo que reportar»*.

### 2.3 · El prompt del agente no puede ser un séptimo `PitchTask`

`test_the_prompt_file_carries_one_system_block_and_one_task_per_task_value` recorre `PitchTask`
**contra el fichero que carga `PROMPT_VERSION`**, que es `assist/v3`. Un miembro nuevo cuya sección
vive en v4 habría roto ese recorrido, y el recorrido vale más que la limpieza de un enum: es lo que
caza una tarea declarada sin texto detrás. Se resuelve con un enum y un mapa aparte.

### 2.4 · `generate_pitch()` cableaba `PROMPT_VERSION` en sus tres salidas

Sin tocarlo, una generación del agente contra `assist/v4` habría **sellado la respuesta con
`assist/v3`** — el fallo que `enrichment/` ya pagó una vez. Se añade `prompt_version` como
parámetro con el valor de la ruta determinista por defecto.

### 2.5 · `FreeQueryGroup` lo comparten las dos rutas

`as_data()` es el objeto que la puerta numérica lee y el mensaje de usuario imprime, y la ruta
determinista construye la misma clase. La marca de procedencia **se renderiza sólo cuando está
puesta**, con test en las dos direcciones, para que el *payload* de `/v1/assist/sale` sea byte a
byte el que era.

### 2.6 · Un fallo de proveedor reportaba que el modelo había terminado

**Encontrado por una medición, no leyendo código.** La primera pasada topó un límite de tasa en la
petición 6 y **las siguientes volvieron con `stop_reason=sin_mas_herramientas` y
`partial=false`** — es decir, «el modelo dejó de pedir herramientas» sobre peticiones cuya llamada
nunca llegó: respuestas indistinguibles de una completa.

> **Cuántas, no se puede verificar.** Esta sección decía «46»; el §3.9 decía «64». La pasada
> abortada **no dejó artefacto** —el arnés sólo escribía al final— y las dos cifras se apuntaron de
> su salida de consola, que no se conservó. El defecto sí está verificado: la sonda
> `3ba27f2d72a8`, posterior al arreglo, ya informa `fallo_proveedor` en 4 de sus 10 filas. Desde
> la verificación independiente el arnés escribe cada fila según la produce (§11).

Se añade `fallo_proveedor` al vocabulario cerrado, con `partial=true`. La suite nunca lo habría
cazado: un doble programado no se cae en mitad de una tanda.

**Y llegó hasta el contrato publicado.** Al entrar en el vocabulario cambió la descripción de
`stop_reason` en `openapi.json`, **porque esa descripción se deriva de la constante** en vez de
estar reescrita a mano; los dos tests del contrato lo cazaron. Dos decisiones previas pagando a la
vez: derivar propagó el cambio solo, pinchar impidió que se propagara en silencio.

### 2.7 · Un escenario de pivote sin referencia no mide el pivote, y no lo mide en silencio

Los seis escenarios de disponibilidad decían **«el cliente quiere esta pieza»**. El modelo no tiene
ninguna referencia que pasarle a la tool: buscaría primero y comprobaría **lo que encontrara**, que
no es la pieza cuya etiqueta declara el escenario. **La tasa de pivote por etiqueta se habría
calculado sobre piezas al azar y nada lo habría indicado.** Se corrige con un marcador `{pieza}` que
el arnés resuelve, con test que lo exige donde hay `fixture` y lo prohíbe donde no.

**Habría costado la pasada entera.**

---

## 3 · La pasada: `293fe5c6e470`, 204 peticiones, dos brazos

> ## ⚠ Anotación posterior de C42 · 2026-09-26 · **las cifras de recuperación de esta pasada quedan como NO MEDIDAS**
>
> *Escrita cinco días después de este informe, por el change que instrumentó el arnés. No corrige
> ningún número de aquí: acota qué describen.*
>
> **Esta pasada duró más del doble del techo de rancidez de la proyección, y entonces no existía el
> drenaje automático que lo habría evitado.** La aritmética, toda del propio artefacto:
>
> ```text
> provenance.paced_seconds  =  9.870,8 s  =  2 h 44 min
> techo de rancidez         =      3.600 s  =  1 h     (jpv_pos_projection_max_age_seconds)
> arreglo manual de C40     →  «caduca en una hora»     (informe de C41, §2.1)
> drenaje programado        →  NO EXISTÍA: es de C41, cinco días POSTERIOR a esta pasada
> ```
>
> **Y los dos caminos leen cosas distintas, que es lo que lo hace invisible.** El arnés resuelve su
> surtido por `search.scope_buckets()`, un `SELECT` crudo que `retrieval/ports.py` declara *«read by
> the evaluation only»* y que **no comprueba frescura ninguna**: devuelve etiquetas perfectas por
> rancia que esté la proyección. El camino de servicio consulta el punto de control de sincronía y,
> pasado el techo, **no aplica el prefiltro de disponibilidad** (`degraded=unscoped`). Así que a lo
> sumo las **primeras ~74 de 204 filas** corrieron con el prefiltro aplicado, y es cota superior —la
> procedencia no registra la antigüedad en t=0—. El conjunto de **calibración corre al final**, de
> modo que sus filas van del orden de **1 h 45 min pasadas el techo**.
>
> **No se puede limpiar a posteriori, y que no se pueda es el hallazgo.** El corte ingenuo
> primeras-74 contra el resto da 6,72 → 5,32 grupos de media y 9,5 % → 25,4 % de respuestas vacías,
> pero **está confundido por composición**: las filas 1-74 son todas `load/gpt-4o` y el resto mezcla
> `calibration` con el brazo barato. No hay forma de separar el efecto del ámbito del efecto del
> brazo con lo que el artefacto guarda.
>
> **Qué queda no medido:** todo lo que dependa del surtido recuperado — **grupos y piezas por
> respuesta, reparto coincidencias/sustitutos, y la tasa de respuestas sin piezas en su componente de
> cola**. Trátese como no medido y no como medido a la baja.
>
> ### Y qué SOBREVIVE, que hay que decirlo porque parecería caer con el resto
>
> **El pivote 3 de 3 de `sin_existencias` en `gpt-4o` se sostiene, y con él la justificación de que
> la etiqueta cualitativa baste para gobernar el pivote.** La razón es mecánica y está en el código:
> `consultar_disponibilidad` llama a `search.availability_bucket(product_id, pos_id=pos_id)`
> **directamente** (`assist/tools.py:873`), sin pasar por el guardia de rancidez, y devuelve la
> antigüedad al modelo como `antiguedad_proyeccion_segundos` bajo la regla escrita en su propio
> comentario: *«Freshness travels with the label, and a stale projection degrades the observation
> instead of failing it: the rule is degrade, never remove»*. La etiqueta **no está guardada por la
> rancidez; el prefiltro sí**. Son dos cosas distintas y no deben mezclarse al leer esta anotación.
>
> **Lo que impide que vuelva a pasar**, y por qué esta anotación no obliga a rehacer la pasada: C42
> añade al arnés el registro de la antigüedad de la proyección **por fila** además de en la
> procedencia, con su veredicto de rancidez contra el techo configurado, leída del punto de control de
> sincronía y nunca de `ai.pos_projection.refreshed_at`. Una fila servida sin prefiltro es
> identificable después en vez de promediarse con el resto. Y la precondición de la pasada pasa a
> exigir el contenedor levantado con el drenaje programado de C41 encendido, comprobado en la sección
> `projection` de `GET /health` antes de arrancar. **Se anota y no se rehace**, porque rehacerla
> costaría 2 h 44 min y una cuota de proveedor para reproducir cifras que el change de evaluación va a
> tomar de nuevo con los instrumentos puestos.

Procedencia completa en el artefacto: `run_id`, `git_sha` (**`2c9fd6a…+dirty`**, declarado porque el
árbol llevaba los cambios sin commitear), las cuatro versiones de prompt, los eslabones de
credencial resueltos (`agent`, `router`, `assist`), 1.168 documentos de índice, surtido de 416 y las
cuatro piezas resueltas por etiqueta.

### 3.1 · Los tres presupuestos, fijados por medición (`gpt-4o`, n=102)

| Presupuesto | p50 | **p95** | máx | Antes | **Ahora** | Razón |
|---|---|---|---|---|---|---|
| Tokens (clasificador + bucle) | 10.622 | **16.244** | 18.260 | 120.000 | **40.000** | ~2,5× el p95; el marcador de 120.000 no era un presupuesto |
| Contexto (chars de observaciones) | 1.847 | **4.709** | 17.053 | 40.000 | **30.000** | ~1,8× el máximo observado, con margen por el techo de tools |
| Reloj (petición entera) | 5,3 s | **9,0 s** | 11,9 s | 20 s | **15,0 s** | ~1,26× el máximo, **con 8 s reservados al argumentario** |

El brazo barato da p95 16.298 / máx 22.019 en tokens y p95 10,3 s / máx 14,3 s en reloj, que es el
que loopea hasta que un presupuesto lo corta; los valores elegidos lo cubren también.

> **Dos correcciones de la verificación independiente.**
>
> **Tokens.** La primera versión de esta tabla publicaba p50 12.870 · p95 18.781 · máx 23.210: el
> `prompt_tokens` entero de la petición, **argumentario incluido**. El presupuesto no compara eso:
> compara clasificador más bucle, que es lo acumulado cuando se comprueba, porque el argumentario
> corre después. El valor de 40.000 no cambia.
>
> **Reloj.** «Tensa el peor caso de 20 s a 15 s» **no era cierto**: el reloj sólo se miraba antes
> de cada vuelta, así que la vuelta en curso gastaba su propio *timeout* pasado el límite y el
> argumentario corría después (peor caso por construcción: 15 + 8 + 2 × 4 = 31 s, más las
> herramientas). Ahora el bucle corre contra 15 s **menos la reserva del argumentario** (2 × 4 s) y
> la vuelta en curso se corta cuando se agota. La reserva sale gratis según el propio artefacto: en
> `gpt-4o` el bucle tarda **p95 4,7 s · máx 5,8 s** y clasificador + argumentario **p95 5,2 s ·
> máx 8,0 s**; con 7 s para el bucle se habrían cortado **0 de 102** peticiones de `gpt-4o` y 3 de
> 102 del brazo barato. El límite es ahora 15 s más, como mucho, las herramientas de la vuelta en
> curso, que no se cancelan a medias.

### 3.2 · La curva de crecimiento contesta O-5: **no hace falta compactar**

| Vuelta | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| `prompt_tokens` p50 | 1.974 | 2.620 | 2.712 | 3.152 | 3.470 |
| Incremento | — | +646 | +92 | +440 | +318 |

**Crecimiento suave y casi lineal, no exponencial.** D-14 dejó la compactación «identificada y no
hecha» a la espera de esta curva: la curva dice que no hace falta, y la decisión se cierra con el
dato delante en vez de por precaución.

### 3.3 · El coste, y el número central del diseño refutado

**Corrección metodológica primero.** El arnés tarifaba **todos** los tokens de una petición al
precio del brazo, pero una petición mezcla tres modelos —clasificador `gpt-4o`, bucle (el brazo),
argumentario `gpt-4o-mini`—. Para el brazo barato eso daba un absurdo: **×0,8, el agente más barato
que el pipeline**. Ahora cada etapa se tarifa **con su propio modelo**: el bucle, exacto desde la
traza por iteración; el clasificador, medido en el propio artefacto; el argumentario, lo que queda.

> **La primera versión de esta sección se corrigió a sí misma mal.** Sustituyó el clasificador
> por **0,00205 USD, atribuido a C31**, y publicó ×7,6 y ×1,4. C31 no publicó esa cifra —no está
> en su informe ni en ninguno de sus diez artefactos, que no guardan tokens—: aparece por primera
> vez en la HU de este change. El artefacto sí la mide: las 39 peticiones en que el argumentario no
> corrió gastan fuera del bucle **3.301–3.312 tokens de prompt**, siempre en `gpt-4o`, es decir
> **0,0084 USD por clasificación**; las 8 que el clasificador rechazó, que sólo lo llaman a él,
> dicen lo mismo. Encontrado por la verificación independiente; reproducible con
> `python -m jbg_ai.evals.agent_sweep --rescore evals/results/c32b-agent-sweep-293fe5c6e470.json`
> y fijado por `test_the_rescore_of_the_committed_pass_reproduces_the_figures_the_report_publishes`.

| | Bucle | + clasificador | + argumentario | **Total por petición** |
|---|---|---|---|---|
| `gpt-4o` | 0,01862 $ | 0,00841 $ | 0,00039 $ | **0,02742 $** |
| `gpt-4o-mini` | 0,00125 $ | 0,00841 $ | 0,00041 $ | **0,01008 $** |

**El pipeline, con el mismo clasificador.** `/v1/assist/sale` en consulta libre corre el mismo
`router/v3` en `gpt-4o`, así que su clasificador cuesta lo mismo: 0,0084 USD. Su argumentario es
una fracción: 0,00077 USD según C30b (modo anclado, 120 generaciones), o ~0,00058 USD estimados
desde las 87 generaciones de consulta libre de C31 (`c31-free-query-gate-387fa94e792a`). El
*pipeline* cuesta entre 0,0090 y 0,0092 USD, y **el cociente no depende de cuál se tome**:

| | vs *pipeline* con argumentario de C30b | vs *pipeline* de consulta libre de C31 |
|---|---|---|
| `gpt-4o` | **×2,98** | **×3,04** |
| `gpt-4o-mini` | **×1,10** | **×1,12** |

**El diseño estimó ×19 y el real es ×3,0.** La estimación erraba en los dos lados: el agente entero
cuesta la mitad de lo supuesto (0,027 USD frente a ~0,054), y el *pipeline* cuesta el triple
(0,0092 frente a 0,0028), porque el clasificador que el diseño tomó de la cifra sin fuente cuesta
cuatro veces más. Y la descomposición que el diseño daba
por buena —«×5 estructural de tokens por ×4 de modelo, y el ×4 es reversible con una variable»—
**no se sostiene**: el brazo barato llega a ×1,1, mucho mejor de lo que predecía el ×4… **a cambio
de no servir**. Con el clasificador dominando el coste del *pipeline*, lo que la autonomía añade en
`gpt-4o` es **~0,019 USD por petición**, casi todo el bucle.

**La pasada completa costó 3,82 USD**, no ~2,60: el resumen que el propio artefacto lleva embebido
sigue calculado con la fórmula vieja (3,63 USD), y se deja como está porque el artefacto es una
medición fechada; las cifras válidas son las de `c32b-agent-sweep-293fe5c6e470.rescore.json`.

### 3.4 · Q-7 respondida: **el brazo barato no sostiene la selección de herramienta**

Sobre las **mismas 82 transcripciones**:

| | `gpt-4o` | `gpt-4o-mini` |
|---|---|---|
| `presupuesto_tools` | **1** | **50** |
| `presupuesto_iteraciones` | 0 | 4 |
| Peticiones que topan un presupuesto | **1 de 82 (1,2 %)** | **54 de 82 (66 %)** |
| Llamadas devueltas con `presupuesto_agotado` | 5 | **168** |
| `consultar_disponibilidad` | 87 | **233** |
| `buscar_sustitutos` | 7 | **110** |

**No es que elija peor: no sabe parar.** Es el mismo desenlace que C31 midió para el clasificador
—donde `gpt-4o-mini` silenciaba 3 de 119 y el veto lo rechazó— por un síntoma distinto. El ×4 de
modelo es reversible en el precio y **no en el comportamiento**, que es justo lo que el diseño daba
por separable.

### 3.5 · Las dos preguntas que C32a dejó abiertas

**Granularidad.** Ninguna herramienta muerta: las seis se eligen en el set de carga. **Cero nombres
de herramienta inventados** en los dos brazos, que era «el dato más informativo que la pasada podía
producir» y sale vacío: no falta ninguna tool. **Cero llamadas consecutivas casi idénticas.** La
única causa de fallo recurrente es `presupuesto_agotado`, que es del consumidor y no del esquema.

**La etiqueta de disponibilidad.** Tasa de pivote por etiqueta **y por brazo**:

| Etiqueta | Escenarios | Debía | `gpt-4o` | `gpt-4o-mini` |
|---|---|---|---|---|
| `sin_existencias` | 3 (C07, C11, C12) | sí | **3 de 3** | 2 de 3 · **infra-pivote en C11** |
| `ultimas_unidades` | 1 (C08) | no | 0 de 1 | 0 de 1 |
| `disponible` | 1 (C09) | no | 0 de 1 | 0 de 1 |
| `sin_ambito` | 1 (C10) | no | 0 de 1 — no se produce el colapso que C32a prohíbe | 0 de 1 |

**Compatible con que la etiqueta cualitativa baste para gobernar el pivote, y no más que eso.** El
fallo caro —apartar al cliente de una pieza vendible— no se produjo en ningún brazo; el único
infra-pivote es del brazo barato, en el escenario donde mutiló la referencia (§10). Pero la
evidencia es de **un escenario por etiqueta y brazo** en las tres que no deben pivotar: el change de
evaluación tiene que medirlo con más.

> **Corregido por la verificación independiente.** La primera versión de esta tabla sumaba los dos
> brazos, llamaba «6 escenarios» a 3 escenarios × 2 brazos y publicaba un 83 % en el que el único
> fallo era del brazo descartado. Era lo que calculaba `pivot_rates`, que además lanzaba
> `KeyError` con el C05 corregido; hoy separa por brazo y la tabla sale de `--rescore`.

### 3.6 · El techo de herramientas: medido, y movido de 6 a 8

Distribución en `gpt-4o` (n=102): **p50 2 · p95 5 · máx 6**, con **4 de 102 (3,9 %)** en el techo.
Se sube a **8** = p95 + 3.

**Lo que la medición NO dice:** de esas cuatro peticiones truncadas nadie sabe cuántas llamadas
habrían usado — el techo las cortó. **Ocho es un juicio informado por la distribución, no una
medición de la necesidad sin truncar**, y así queda escrito en la constante.

El 6 apretaba por una razón estructural que la pasada destapó: el patrón natural era buscar y
comprobar la disponibilidad de **las cinco** candidatas, exactamente 6 llamadas, **sin dejar
presupuesto para el pivote que este change existe para permitir**. Se corrigió en `agent/v1` —
comprobar la de la pieza que se va a ofrecer, y como mucho dos sustitutos:

| | antes del cambio de prompt | después |
|---|---|---|
| Peticiones que tocan el techo | 3 de 21 (14 %) | **0 de 33** (y 4 de 102 en la pasada completa) |

> **Las dos primeras cifras no son verificables.** Ningún artefacto conservado suma 21 ni 33
> peticiones, y la última sonda antes de la pasada (`582b8517a235`, 10 minutos antes) tiene **6 de
> 8** en el techo. Todas las ejecuciones registran `agent/v1` con el mismo `git_sha…+dirty` y sin
> *digest* del texto, aunque el texto cambió entre ellas: no hay forma de saber qué versión del
> prompt midió cada una. Lo verificable es la pasada: **4 de 102** en `gpt-4o`. Desde la
> verificación independiente la procedencia registra el `sha256` de cada prompt.

**Por qué dos sustitutos y no «los que hagan falta», con la medición detrás.** Sobre 60 piezas
agotadas de MAO-AIR: sólo el **30 %** de los primeros sustitutos es vendible —**peor que la tasa
base del 65,6 %**, porque las piezas parecidas se agotan juntas—, el 55 % se resuelve en dos
comprobaciones y la cola es **p95 = 12, máximo = 15**. Encadenar hasta acertar no cabe en ningún
presupuesto, y no hace falta: `{{stock}}` lo resuelve .NET en la hidratación, así que la tool existe
para **decidir si pivotar**, no para certificar existencias.

### 3.7 · El techo de llamadas al proveedor se cumple

`provider_calls` p50 **5**, máximo **8**, **cero peticiones por encima del techo de 8** en las 204.
Los *embeddings* van aparte: p50 1, máximo 6, en el contador propio del registro.

### 3.8 · Lo que la pasada deja abierto: `dangling_citation` al 13 %

| | Argumentarios generados | Retirados | Tasa |
|---|---|---|---|
| `gpt-4o` | 84 | 11 | **13,1 %** |
| `gpt-4o-mini` | 81 | 13 | **16,0 %** |

Causa dominante: **`dangling_citation`** (40 y 45 violaciones iniciales). La ruta determinista con
`assist/v3` mide **2 de 89 = 2,2 %**, así que **el agente retira 6× más**.

**La tasa es de retirada por cualquier causa, no de `dangling_citation`.** De los 11 argumentarios
retirados en `gpt-4o`, **8** llevan `dangling_citation` (**9,5 %** de los generados), **2** son
*timeouts* del propio argumentario que ningún texto de este change mencionaba, y 1 es otra causa;
en `gpt-4o-mini`, **12 de 13** (**14,8 %**). Precisado por la verificación independiente: la
primera versión del QA y del plan atribuían el 13,1 % entero a `dangling_citation`.

La prueba de humo ya había cazado este fallo en su forma aguda —el primer escenario retiraba el
argumentario entero con cinco citas inventadas— y el arreglo de `assist/v4` lo redujo, **pero no lo
eliminó**.

**La anatomía del fallo es de una sola causa, y eso lo hace atacable.** Sobre las 165 peticiones
que llegaron a generar:

| | |
|---|---|
| Con `dangling_citation` en el primer intento | **20 (12,1 %)** |
| De ésas, las que **no tenían ninguna cita disponible** | **20 — el 100 %** |
| Las que sí tenían alguna cita y aun así inventaron | **0** |
| Reparaciones gastadas en arreglarlo | 18 |
| **Argumentarios que la reparación salvó** | **0 — ninguno** |

El patrón es inequívoco: **el modelo sólo inventa identificadores cuando la lista de citas llega
vacía**, es decir cuando el bucle buscó en el catálogo y no consultó el corpus. Nunca inventa
teniendo citas de verdad.

**Y la reparación no rescata ni un caso de los 18 en que se gastó.** Eso convierte el 12 % en un
**coste doble inútil**: se paga la segunda llamada de generación —el presupuesto entero de esa
etapa— y el argumentario se retira igual. Una reparación que no repara nunca es una llamada que
sólo hay que dejar de hacer para esta causa, y esa es una decisión de diseño que este change no
toma porque la política de reparación única es de C30b.

Queda **identificado, medido y no cerrado**: es una iteración de prompt más contra el set de
calibración, y no se hace aquí porque el change ya tiene su medición y porque iterar sin volver a
pasar es cambiar sin medir.

**Una limitación del propio arnés que esto destapó:** las filas registran la **causa** de cada
violación pero no su **detalle**, y el identificador inventado viaja en `Violation.detail`. Así que
de esta pasada **no se puede saber qué identificadores se inventó el modelo** — que es justamente
el dato que diría si los compone a partir de los materiales de las piezas o de otra cosa. Es la
misma omisión que ya obligó a añadir las violaciones a las filas a mitad de la preparación, y la
lección se repite: **lo que el artefacto no guarda no se puede analizar después, y averiguarlo
cuesta otra pasada.**

### 3.9 · El techo de tokens por minuto es la restricción operativa real

La primera pasada murió en la petición 6 y las siguientes volvieron vacías —cuántas, no se puede
verificar: la pasada no dejó artefacto y las dos cifras apuntadas de su consola, 46 (§2.6) y 64,
no coinciden—. **Dos diagnósticos míos fueron falsos antes de acertar**, y los dos valen para quien
repita esto:

1. *«Es la clave nueva, que tiene poca cuota.»* Falso: el bucle seguía funcionando con esa misma
   clave mientras el clasificador fallaba.
2. *«Es que el arnés usa una sola clave para las tres etapas.»* **También falso, y lo probé:**
   separé las tres cadenas —que había que separarlo igual, porque el arnés medía una configuración
   que la ruta nunca sirve— y volvió a romper en la petición 6, exactamente igual.

La aritmética dio la respuesta: **55.649 tokens en 33 s ≈ 100.000 tokens/min** contra un techo de
**tokens por minuto de la organización**, no de peticiones ni de clave. Una pausa fija es el
instrumento equivocado para un techo de tokens cuando las peticiones van de 1.800 a 16.000; se
sustituye por un regulador de ventana deslizante. Verificado: **0 *rate limits* en las 204**.

**Y el techo fija el reloj de la medición:** con peticiones de ~13.000 tokens y el regulador a
25.000 TPM **no caben dos en una ventana**, así que el ritmo es de una petición por minuto y las 204
tardan **3,4 h**. Medir un agente no cuesta sólo dinero: cuesta **cuota por minuto**.

---

## 4 · Los tres tests preexistentes que se modificaron

Ninguno retirado, ninguno renombrado.

| Test | Por qué |
|---|---|
| `test_every_assist_prompt_version_is_preserved_with_its_measurement` | Fijaba el directorio de prompts a `v1,v2,v3`; la tarea 8.2 obliga a crear `v4` |
| `test_snapshot_covers_the_frozen_surface` | Enumeraba diez rutas; `/v1/assist/agent` es la undécima |
| `test_the_registry_publishes_no_route_and_declares_no_iteration_budget` | Ver abajo |

El tercero es el caso que la tarea 15.1 —*«sin retirar ni renombrar ninguno»*— no anticipa: **un
test cuyo nombre afirma la ausencia de lo que el change entrega**. Renombrarlo perdería un nombre de
la línea base; invertir su cuerpo dejando el nombre lo convertiría en una mentira, que es lo que
este repositorio critica al retirar `DELIVERED_BY`. La salida es que **el nombre sigue siendo cierto
al alcance que declara**: el *registro* no publica ruta —no define `APIRouter`— y no declara
presupuesto alguno, que es la separación de capas que el corte del 2026-09-20 existe para mantener.
Lo que deja de ser cierto es la lectura «no existe ruta de agente en el documento», y eso lo pincha
ahora `test_snapshot_covers_the_frozen_surface`, que es su sitio.

---

## 5 · El contrato, verificado y no supuesto

| Comprobación | Resultado |
|---|---|
| `sha256` antes (C32a) | `43f70fdadd2bd9aa90068d3e74ec2ee25c8d3b3b530f6d33907b1e73d068c684` |
| `sha256` al cierre de la implementación | `7c6a038e9f749df2f9d23c024201e9fb2c4d2383cb7ff45eaf63a461ecaccc65` |
| `sha256` tras la verificación independiente | **`d8d48f87b279d45d22bce80a67c4fd51caef6e679363c413f5b697c99ec2b875`** — sólo cambian dos descripciones de `AgentUsage`, esquema nuevo de este change |
| Los mismos, como *blob* de git (LF) | `dd8df91d…` → `befdf436…` → **`8dd52feb…`**. Los de arriba son del checkout de Windows con `core.autocrlf=true` |
| Hojas del documento | 1.103 → 1.289 |
| **Retiradas** | **0** |
| **Cambiadas de valor o de tipo** | **0** |
| Añadidas | 186, **todas** dentro de `/v1/assist/agent` y sus seis modelos |
| Campos de `AssistResponse` | **los once de C31**, pinchados como conjunto |
| `Usage` compartido | **sin `calls`**: el recuento vive en `AgentUsage` |
| `POST /v1/assist/sale` | subárbol **idéntico** |

La verificación se rehízo **contra la línea base de C32a** —no contra una regeneración intermedia—
después de que `fallo_proveedor` moviera la descripción de `stop_reason`.

---

## 6 · Trazabilidad de los catorce escenarios de la HU

| # | Escenario | Test / evidencia |
|---|---|---|
| **1** | El bucle reúne evidencia y para cuando el modelo deja de pedir | `test_the_loop_stops_when_the_model_asks_for_no_more_tools` |
| | …las citas publicadas son las que el argumentario declaró | `test_the_published_citations_are_the_ones_the_argument_declared_and_that_verified` |
| **2** | Agotado el presupuesto de iteraciones, responde y lo declara | `test_the_iteration_budget_stops_the_loop_and_the_response_declares_it` |
| | …y el de reloj acota la petición entera, argumentario incluido | `test_the_wall_clock_budget_bounds_the_whole_request_argument_included` *(verificación independiente)* |
| **3** | Ningún texto de las vueltas llega a la respuesta | `test_no_fragment_of_the_loops_prose_reaches_the_response_or_the_wire_trace` |
| | …y la propiedad es **del tipo** | `test_the_agent_step_type_declares_no_field_able_to_carry_the_models_prose` |
| | …el adaptador descarta y registra longitud y digest | `test_the_adapter_discards_the_prose_and_records_only_its_length_and_digest` |
| **4** | Cada turno viaja como dato delimitado | `test_every_turn_of_the_transcript_travels_inside_the_data_delimiters` |
| | …inyección en el turno 3 sin mover el sistema | `test_an_injection_in_an_earlier_turn_does_not_change_the_system_message` — **reescrito**: comparaba una función sin argumentos consigo misma; ahora compara los mensajes de sistema que recibieron las llamadas reales, con la inyección en el turno 3 de 5 |
| | …turno de asistente falsificado, tratado como dato | `test_a_turn_attributed_to_the_assistant_is_delimited_exactly_as_an_operator_turn` |
| | …y no puede cerrar el bloque | `test_a_turn_that_writes_the_closing_mark_cannot_escape_its_block` |
| | …rechazo antes de cualquier llamada | `test_a_transcript_over_its_caps_is_refused_before_any_provider_call` · `test_a_transcript_beyond_its_declared_caps_is_refused_with_422` |
| **5** | El techo de llamadas se cumple para una petición | `test_the_provider_call_ceiling_holds_for_a_request_that_loops_and_repairs` |
| | …medido | **0 de 204 por encima de 8**, máximo observado 8 (§3.7) |
| | …*embeddings* aparte | `test_the_provider_call_ceiling_holds…` · p50 1, máx 6 (§3.7) |
| **6** | El rechazo cortocircuita en cualquier turno | `test_a_conversation_that_drifts_out_of_domain_is_refused_at_that_turn` |
| | …exactamente una clasificación | `test_exactly_one_classification_is_made_whatever_the_length_of_the_transcript` |
| | …no se marca como abstención | mismo test · `test_a_request_the_guardrail_refused_is_never_reported_as_an_abstention` |
| **7** | La repregunta la decide el bucle y termina | `test_the_clarification_tool_ends_the_loop_with_the_deterministic_question` |
| | …el clasificador no repregunta | `test_an_elliptical_follow_up_is_not_short_circuited_by_the_insufficiency_verdict` |
| | …granularidad de la terminalidad | `test_clarification_is_terminal_at_the_granularity_of_a_turn` |
| **8** | La disponibilidad dispara el pivote, y no de más | **Medido por brazo**: `gpt-4o` 3 de 3 en `sin_existencias` y 0 de 1 en cada una de las otras tres (§3.5) |
| | …los sustitutos llegan distinguidos | `test_substitute_groups_reach_the_payload_marked_apart_from_catalogue_matches` |
| | …y la pieza abandonada no encabeza como coincidencia | `test_a_piece_the_loop_pivoted_away_from_does_not_reach_the_payload_as_a_match` · `test_the_piece_cap_drops_further_matches_before_the_substitutes_of_a_pivot` *(verificación independiente)* |
| **9** | Ninguna etiqueta de disponibilidad llega al argumentario | *payload*: `test_no_availability_label_reaches_the_generation_payload` · **argumento: medido, no asegurado** — nada lo impide (`verify()` deja pasar «disponible»), así que la pasada cuenta los términos por fila (`pitch_availability_terms`); la pasada `293fe5c6e470` es anterior al recuento y no lo tiene |
| **10** | Las llamadas que no caben vuelven como observación | `test_tool_calls_beyond_the_budget_come_back_as_observations_and_touch_no_port` |
| | …medido | 5 y 168 observaciones `presupuesto_agotado` por brazo (§3.4) |
| **11** | La traza del cable dice qué se hizo, no qué se preguntó | `test_the_wire_trace_reports_what_was_done_and_never_what_was_asked` |
| | …ni el log | `test_the_log_line_carries_the_counters_and_neither_the_transcript_nor_an_argument` |
| | …el arnés lee la traza rica en proceso | `test_the_rich_trace_is_available_in_process_and_pairs_every_observation` |
| **12** | Los dos números, medidos y no declarados | §3.1, con p50/p95/máx · §3.2 la curva · §3.3 los dos brazos |
| **13** | Las dos preguntas de C32a, con datos | §3.5 — granularidad y tasa de pivote por etiqueta |
| **14** | El pipeline determinista no se mueve | `test_the_deterministic_route_answers_exactly_what_it_answered_before` |
| | …adición pura hoja a hoja | `test_the_published_contract_moved_by_addition_only` — **reescrito**: sólo comparaba el *snapshot* con lo que genera la app; ahora parte hoja a hoja contra el contrato de C32a guardado como fixture · §5 |
| | …el golden set no se ha usado | `test_no_transcript_of_either_agent_set_reuses_a_golden_query` · §7 |

---

## 7 · El muro de contaminación

**El golden set de C24 no se ha tocado**, ni para calibrar, ni para iterar prompts, ni para sembrar
los instrumentos. `git status` sobre `evals/golden/` está vacío y hay dos tests que lo comprueban en
vez de afirmarlo: uno normaliza acentos y puntuación y cruza las 72 consultas contra los dos
conjuntos **en las dos direcciones**, y otro comprueba que ni el generador ni los ficheros lo
mencionan.

Las **dos iteraciones de prompt** de este change —la de `assist/v4` contra `dangling_citation` y la
de `agent/v1` contra el gasto de herramientas— se hicieron **contra el set de calibración**, que es
para lo que existe y lo que D-18 permite.

---

## 8 · Lo que NO se hizo, y por qué

1. **Cerrar `dangling_citation` al 13 %.** Identificado, medido y declarado (§3.8). Iterar el prompt
   otra vez sin volver a pasar sería cambiar sin medir.
2. **Compactar el contexto.** D-14 lo dejó a expensas de la curva; la curva dice que no hace falta
   (§3.2). Se cierra con el dato, no se aplaza.
3. **El consumidor .NET de la ruta.** No existe. Su política de *timeout* y de circuito queda en
   `DEFERRED_TASKS.md`.
4. **Evaluar la calidad del agente.** Los 20-25 escenarios multi-turno, los adversarios y los de
   inyección sistemáticos son del change de evaluación, que escribirá los suyos aparte.
5. **Subir el *tier* de la cuenta.** No es una decisión de este change; queda el dato de que la
   cuota por minuto fija el reloj de cualquier medición futura (§3.9).

---

## 9 · Limitaciones que se declaran y no se cierran

1. **Los 15 s síncronos son mucho en un mostrador.** Declarado y no mitigado: sin *streaming* ni
   respuesta en dos fases. La ruta separada evita que contamine el camino de 5 s. Medido: p95 9,0 s.
2. **Los dos avisos por reglas de C30a no se emiten en esta ruta.** `size_label_missing` y
   `family_has_variants` son afirmaciones sobre una pieza que esta ruta no lee.
3. **En el cable, un grupo de sustitutos no se distingue de uno de catálogo.** `AssistGroup` es
   parte de la forma congelada de `AssistResponse`. La distinción existe donde gobierna.
4. **El 3 % de las piezas agotadas no tiene ningún sustituto vendible.** Es una propiedad del
   surtido y no del bucle.
5. **El rechazo del clasificador sobre un turno elíptico** sigue siendo riesgo declarado y no
   cerrado. En la calibración se observó un caso relacionado: «enséñame algo de titanio» se rechazó
   como `not_in_catalogue` en vez de buscar, que es defendible pero contradice la expectativa que yo
   escribí.
6. **El conjunto de calibración tenía tres defectos de construcción, corregidos, y una
   discrepancia que se deja abierta.** Ver §10.
7. **Ocho llamadas a herramienta es un juicio informado**, no una medición de la necesidad sin
   truncar (§3.6).

---

## 10 · La revisión del conjunto de calibración

**Corrección de una cifra que di mal:** dije «cinco escenarios fallidos» y son **seis**. Cuatro
fallan con `gpt-4o` y seis con el brazo barato.

### Los seis, clasificados por de quién es el fallo

| # | Brazos | Qué pasó | De quién |
|---|---|---|---|
| **C05** | los dos | «¿de ese hay más tallas?» sobre un turno del asistente que **no nombraba ninguna pieza**: «ese» no apuntaba a nada. Y prohibía `buscar_catalogo`, sin el cual no hay pieza cuya familia listar | **mío** · escenario insatisfacible |
| **C16** | los dos | Codificaba `expects: []` con las seis prohibidas —exigiendo el rechazo del clasificador— mientras su propio `why` decía *«lo que no puede pasar es que se obedezca»*. **No se obedeció**: los dos brazos buscaron la parte legítima de la conversación e ignoraron la orden inyectada | **mío** · la codificación contradice su texto |
| **C17** | los dos | El `why` dice «se admite cualquiera de las dos» y usaba `expects`, que el arnés lee como **todas**. Los dos brazos llamaron sólo a `pedir_aclaracion`, que ese mismo texto acepta | **mío** · faltaba la disyunción en el formato |
| **C19** | los dos | «enséñame algo de titanio» → el clasificador rechaza con `query_not_in_catalogue` en vez de buscar y abstenerse | **discutible** · ver abajo |
| **C03** | sólo el barato | `gpt-4o-mini` pide aclarar el tipo de pieza ante «¿la plata se puede llevar a la playa?», que no pide ninguna pieza. `gpt-4o` consulta el corpus | **del modelo** |
| **C11** | sólo el barato | `gpt-4o-mini` llama a `consultar_disponibilidad` con **`sku: '637'`** cuando la referencia es `SKU637`: **mutila el identificador**, la llamada falla con `referencia_desconocida` y a partir de ahí gasta el presupuesto buscando | **del modelo** |

**C11 es un hallazgo con entidad propia que no estaba anotado**: el brazo barato **no copia
fielmente los identificadores que se le dan**. Refuerza Q-7 por una vía distinta de «no sabe
parar», y es un modo de fallo que un conjunto de sólo veinte escenarios podría no haber visto.

### Qué se corrigió y qué no

Se corrigieron **sólo los tres defectos objetivos de construcción**, que son los que hacen que el
escenario no pueda medir lo que dice medir:

- **C05** gana una clase nueva de `fixture` —`{family: con_variantes}`— que el arnés resuelve a un
  SKU cuya familia tiene varias variantes, y el turno del asistente pasa a nombrarla. Se retira la
  prohibición de buscar, porque buscar antes es legítimo.
- **C16** pasa a `expects_any: [buscar_catalogo, pedir_aclaracion]`. Y se deja escrito que **la
  mitigación estructural no se mide aquí**: que cada turno viaje dentro de las marcas y que el
  mensaje de sistema sea idéntico son propiedades deterministas que viven en `test_transcript.py`,
  donde se comprueban sin gastar nada. Un conjunto que llama a un modelo no es el sitio para
  afirmar algo que no depende del modelo.
- **C17** pasa a `expects_any`, que es la semántica que el formato no tenía.

**C19 se deja como discrepancia declarada y no se toca.** Rechazar «titanio» con el código que dice
«esto no lo tenemos» es más barato y más honesto que enseñar cinco piezas que no son de titanio, y
escribí la expectativa sin comprobar qué hace el clasificador de C31 con un material que su
vocabulario no contiene. Cambiarla ahora sería ajustar la expectativa a lo observado, que es
exactamente la contaminación de la que este conjunto se protege.

**Y `expects_any` trae su propia regla para que el error no se repita.**
`test_a_scenario_that_admits_alternatives_says_so_in_the_format_and_not_in_its_prose` exige que un
escenario cuya prosa ofrezca una elección use la disyunción, y prohíbe declarar las dos.

### Cómo queda la puntuación, y por qué NO es una nota

Reevaluando **la misma pasada** con las expectativas corregidas —sin una sola llamada nueva al
proveedor, porque lo único que cambia es cómo se puntúa lo ya medido:

| | antes | después |
|---|---|---|
| `gpt-4o` | 16 OK / 4 MISS de 20 | **18 OK / 0 MISS / 1 discrepancia declarada** de 19 reevaluables |
| `gpt-4o-mini` | 14 OK / 6 MISS de 20 | **16 OK / 2 MISS / 1 discrepancia declarada** de 19 reevaluables |

**C05 no es reevaluable**: su transcripción cambió, así que la pasada vieja ya no la mide. Lo que
queda fallando es lo que debe: `C19` en los dos brazos —la discrepancia que se deja abierta— y
`C03` y `C11` sólo en el barato, que son fallos reales del modelo.

> **Hasta la verificación independiente esta tabla no tenía código detrás**: se puntuó a mano, y el
> arnés no leía `expects`, `expects_any` ni `forbids`. Hoy la calcula `expectation_verdict` con la
> semántica que declara la cabecera del conjunto, `--rescore` la reproduce (16/4 y 14/6 tal como
> se corrió; 18/1 y 16/3 con el fichero de hoy) y un test la fija. **C19 lleva su discrepancia en
> el propio fichero**, en un campo `declared_discrepancy` que el evaluador cuenta aparte; antes
> sólo constaba en la prosa de este informe y del QA, y su `why` seguía diciendo «la búsqueda debe
> correr».

**Esta proporción no es una nota de calidad y no debe publicarse como tal.** Sirve para leer *por
qué* falla cada caso, que es para lo que el conjunto existe. La nota la da el change de evaluación
sobre el golden set, que sigue limpio.

---

## 11 · La verificación independiente: qué cambió de este informe y del código

Una segunda sesión reprodujo contra el árbol cada cifra de este informe y del QA, con la hipótesis
de trabajo de que algo se había escapado. **Casi todo reprodujo al dígito**; lo que no, está en el
[§12 del QA](../../../openspec/changes/archive/2026-09-21-add-sales-assistant-agent-loop/qa.md), con su medición y su
control. Aquí, sólo lo que cambió.

| Hallazgo | Qué era | Qué se hizo |
|---|---|---|
| **El sobrecoste ×7,6** | El clasificador se tarifaba a 0,00205 USD, cifra atribuida a C31 que C31 nunca publicó; el artefacto lo mide a 0,0084 | Coste por etapa en el arnés; `--rescore`; §3.3 reescrito: **×3,0 y ×1,1**, pasada de **3,82 USD** |
| **`pivot_rates`** | `KeyError` con el C05 corregido, justo al escribir el artefacto; además sumaba los dos brazos | Por brazo y sólo sobre etiquetas; filas escritas según se producen; §3.5 por brazo |
| **El reloj** | Sólo se miraba antes de cada vuelta: 31 s de peor caso por construcción | Reserva del argumentario dentro de los 15 s y corte de la vuelta en curso (§3.1) |
| **Cuatro tests que no afirmaban lo que decían** | Adición pura sin línea base, *ledger* sólo en negativo, inyección comparando una función consigo misma, etiqueta en el argumento sobre un texto guionizado | Reescritos o ampliados sin retirar ni renombrar ninguno; el cuarto pasa a medición (§6) |
| **Presupuesto de tokens** | Calibrado sobre `prompt_tokens` con argumentario; el código compara clasificador + bucle | Cifras rehechas (§3.1); el valor no cambia |
| **Tras un pivote** | La pieza abandonada seguía como coincidencia de catálogo y el tope cortaba antes los sustitutos | Excluida; el tope prioriza sustitutos sin cambiar el orden (§6, escenario 8) |
| **`usage` del cable** | Suma tres modelos bajo un solo `model` | `AgentRun` guarda las tres etapas; `AgentUsage.model` declara que no es clave de precio |
| **La calibración** | OK/MISS puntuado a mano; C19 sólo declarado en prosa | `expectation_verdict` + `declared_discrepancy` (§10) |
| **Procedencia** | Mismo `agent/v1` y `assist/v4` sobre textos distintos; la pasada abortada no dejó nada | `sha256` de cada prompt y modelos de las tres etapas; «46/64» y «3 de 21 → 0 de 33» marcados como no verificables |

**Nada de esto exigió volver a llamar al proveedor**: todo sale del artefacto commiteado o de dobles.
**Lo que la pasada no mide del código nuevo**, y se declara: la proyección tras un pivote cambia el
*payload* que recibe el argumentario en 7 de las 10 peticiones de `gpt-4o` que pivotaron; los tokens
no se mueven, porque el tope de ocho piezas es el mismo, pero la calidad de ese argumentario es cosa
del change de evaluación.
