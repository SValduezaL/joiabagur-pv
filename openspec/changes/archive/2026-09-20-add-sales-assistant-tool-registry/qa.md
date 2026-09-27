# QA — C32a `add-sales-assistant-tool-registry`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** implementación y esta pasada, el **2026-09-20** · **Rama:** `c32a-add-sales-assistant-tool-registry` · **Artefactos de partida:** `df02beb`, árbol limpio · **Implementación: sin commitear al cerrar esta pasada** (16 rutas en `git status`).
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **44/44 tareas** y **10/10 casillas del DoD**. Ninguna tarea quedó a medias y no hubo línea de corte que usar.
> **Este change NO mueve el contrato en absoluto.** `openapi.json` es **idéntico byte a byte** —no «sólo descripciones», idéntico—, y el §7 lo demuestra por `sha256`, por `git status` y por recuento de rutas del documento generado.
> **Lo que esta pasada encontró:** el **invariante de solo-lectura de D-6, leído al pie de la letra, es insatisfacible** con los puertos que el propio diseño obliga a inyectar; **`low_confidence` no es la abstención** y emitirlo habría dicho lo contrario de la verdad, un hallazgo que **ningún test habría cazado**; la **trampa anunciada como la más cara no existía**; y dos recuentos de los artefactos de partida no cuadran con el árbol. Todo en el §9.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | **3.11.15** · Windows · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| Proveedor de LLM | **Cero llamadas, y no por configuración sino por construcción**: este change no llama a ningún proveedor de chat. No hizo falta ni exportar `SSL_CERT_FILE` ni el PEM del almacén de Windows que `CLAUDE.md` exige para una llamada real, porque **no se hizo ninguna** |
| Proveedor de *embeddings* | **Cero llamadas reales.** Las dos tools que embeben van por `FakeEmbeddingClient`, que conduce el cliente real sobre un lote guionizado |
| PostgreSQL | **Ninguna de las 50 pruebas nuevas toca base de datos** — verificado con `pytest -m db tests/assist/test_tools.py` → `no tests collected (50 deselected)`. Las **72** pruebas marcadas `db` **preexistentes** sí corrieron, sobre testcontainers efímero, y **ninguna es de este change** |
| Bucle de eventos | `asyncio.run` por escenario vía `support/assist_world.run`. **Un escenario, un bucle** — la regla que `CLAUDE.md` deja escrita. Una prueba construye el suyo **a mano y antes** del guardián de sockets, por la razón del §9.4 |
| .NET | **no ejecutado, y a propósito**: el diff no toca `backend/`. §8 lo demuestra |
| Frontend | **no ejecutado**: el diff no toca `frontend/`. §8 lo demuestra |
| Contrato | `ai-service/openapi.json` **no regenerado y no tocado**. Hash guardado **antes** de empezar (tarea 1.3) y verificado al cierre con `sha256sum -c` (§7) |
| Migraciones | **ninguna**. `alembic heads` → **`d7c4e91b25a0`**, la misma revisión que dejó C31 |
| Congelados | `git status --porcelain` **vacío** en `backend/`, `frontend/`, `terraform/`, `.github/`, `api/`, `knowledge/`, `indexing/`, `enrichment/`, `evals/`, `config/`, `prompts/`, `migrations/`, `data/knowledge/`, `pyproject.toml` y `openapi.json` (§8) |

---

## 1. Suites automáticas

La línea base se midió **antes de tocar una línea de código**, sobre el árbol limpio en `df02beb`,
que sólo contenía los cuatro artefactos del change. `git status --porcelain` respondió vacío, que
es la condición correcta de línea base — **no hizo falta `git stash`**, y por eso no se usó, aunque
la tarea 1.1 lo proponía.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`df02beb`, árbol limpio) | **1468 → no: 1418 passed**, 0 failed, **0 skipped**, 107,7 s |
| `ai-service` con la suite nueva recién escrita | **46 passed, 3 failed** — los tres, defectos **de las pruebas nuevas** y no del código (§9.4) |
| `ai-service` tras reconciliar los tres | **1467 passed**, 0 failed, 101,9 s |
| `ai-service` tras el hallazgo de `low_confidence` (§9.3) | **1468 passed**, 0 failed, 85,3 s |
| **`ai-service` definitiva, sobre el árbol final** | **1468 passed**, 0 failed, **0 skipped**, 87,3 s |
| **`ai-service` tras la segunda pasada (§11)** | **1469 passed**, 0 failed, **0 skipped** — el nuevo es el test de abstención del §11.3 |
| `openspec validate --all --strict` antes y después | **58 passed, 0 failed** en las dos puntas |
| `openspec validate add-sales-assistant-tool-registry --strict` | `Change 'add-sales-assistant-tool-registry' is valid` |
| Comprobador de enlaces antes / después | **1012 → 1026 enlaces, 0 rotos** en las dos puntas — los 14 nuevos los añaden el informe, las notas de documentación y este mismo fichero. **1029 tras la segunda pasada** (§11), también 0 rotos |
| `dotnet test` · `npm run test` al cierre | **no ejecutados**: fuera del diff. Ver §8 |

> La segunda fila de arriba lleva una corrección a la vista a propósito: la línea base es **1418**,
> no 1468. Se deja escrita porque el error de teclearlas al revés es exactamente el que produce un
> informe que dice «sin regresión» sobre una comparación que nunca se hizo.

### 1.1. La comparación por nombres, que es la que vale

`CLAUDE.md`, la tarea 1.1 y la tarea 8.2 exigen comparar por **nombres de test** y no por recuento.
Se capturaron los *node id* con sus resultados en las dos puntas (`pytest -rA`), se ordenaron y se
compararon con `comm`.

```
ANTES    1418 passed | rojo 0 | skipped 0
DESPUES  1468 passed | rojo 0 | skipped 0

Nombres en rojo NUEVOS  (después − antes) : NINGUNO
Nombres en rojo IDOS    (antes − después) : NINGUNO

Node id NUEVOS       : 50   ← los 50, en tests/assist/test_tools.py
Node id DESAPARECIDOS:  0   ← NINGUNO. No hubo que renombrar nada
```

**Ningún test desaparece, y esta vez ni siquiera hay sucesores que declarar**, al contrario que en
C31 —que renombró cuatro— o que en C30a y C30b. Este change **no invierte ninguna propiedad
afirmada antes**: sólo añade una capability nueva que no existía, así que no hay ninguna aserción
previa que dejara de ser cierta.

La suite de `ai-service` **no** es la de `backend/` ni la de `frontend/`, que `CLAUDE.md` advierte
que llegan en rojo: ésta llega **verde de fábrica, 1418 de 1418**, así que **rojo habría sido mío**.

### 1.2. Desglose de los 50 nuevos, y la aritmética cierra exacta

Los 50 *node id* son **48 funciones**, una de ellas parametrizada con **3** casos
(`test_availability_answers_with_the_label_of_the_stored_bucket`, un caso por bucket):

```
48 funciones − 1 parametrizada + 3 casos = 50 node id  ✓
1418 + 50 = 1468                                        ✓
```

> **La segunda pasada (§11.3) añadió uno**, `test_the_catalogue_search_reports_an_abstention_when_
> the_retriever_abstains`, en la sección «las tools que envuelven código probado», que pasa de **9
> a 10**. La tabla de abajo es el desglose **de la primera pasada** y se deja como estaba; con el
> añadido el total es **49 funciones** y **51 node id**, y `1418 + 51 = 1469`. Ninguna función
> desapareció ni se renombró: las cuatro correcciones del §11 son enmiendas dentro de tests
> existentes más este único añadido, comparado otra vez por nombres con `comm`.

Medido sobre las secciones del fichero, no sobre una tabla escrita a mano:

| Sección de `test_tools.py` | Funciones | Qué cubre |
|---|---|---|
| escenario 1 · el conjunto congelado | **4** | seis exactas, esquema y descripción por tool, séptima rechazada, quinta rechazada |
| escenario 2 · el invariante de solo lectura | **5** | los tres ejes, el puerto que escribe, la anti-vacuidad y la regla de comparación |
| escenario 3 · el fallo como observación | **3** | dependencia caída, causa siempre del vocabulario, nombre de tool inventado |
| escenario 4 · etiqueta y nunca cifra | **6** | los tres buckets, sin dígito, sin cantidad, frescura, proyección vieja, cobertura del mapa |
| escenario 5 · «sin ámbito» ≠ «agotado» | **2** | principal sin punto de venta, pieza sin fila |
| escenario 6 · la repregunta | **3** | determinismo por eje, eje fuera del enum, el enum publicado |
| escenario 7 · direccionamiento por SKU | **6** | resolución, desconocido, descatalogado, sin id interno, sin score, posición |
| escenario 8 · la mitad sin proveedor | **4** | sin credencial, sin llamada de chat, contador propio, `usage.calls` intacto |
| escenario 9 · aquí no hay bucle | **2** | sin ruta ni presupuesto, forma de `AssistResponse` |
| los tests corren sin red | **1** | el registro entero con el socket cerrado |
| validación antes de tocar un puerto | **3** | argumento fuera de cota, argumento no declarado, cotas del esquema |
| las tools que envuelven código probado | **9** | conocimiento anclado y sin anclar, familia vacía, sustitutos, sin *embedding*, tope del roster, lectura por pieza, log sin argumentos, abstención |
| | **48** | |

---

## 2. La puerta de entrada (grupo 1)

| Tarea | Comprobación | Resultado |
|---|---|---|
| **1.1** | Línea base **por nombres** sobre árbol limpio | ✅ 1418 *node id* guardados con su resultado, antes de tocar código |
| **1.2** | `openspec validate --all --strict` **antes** de empezar | ✅ **58 passed, 0 failed** — cifra de partida anotada |
| **1.3** | Hash de `openapi.json` **antes** de empezar | ✅ `sha256 43f70fdadd2bd9aa90068d3e74ec2ee25c8d3b3b530f6d33907b1e73d068c684`, guardado en fichero para `sha256sum -c` al cierre |

La tarea 1.1 proponía `git stash push -u` / `git stash pop`. **No se usó, y no hacía falta**: el
árbol estaba limpio en `df02beb`, que es la condición que el *stash* existe para fabricar. Hacer el
*stash* sobre un árbol limpio habría sido una operación sin efecto con riesgo de perder trabajo.

---

## 3. Los 25 escenarios de la delta, uno a uno

**13 requisitos · 25 escenarios**, todos `ADDED`. Doce requisitos con dos escenarios y uno con uno.

> **Son 25 y no 27.** El encargo de la sesión y el primer borrador del informe decían «27
> escenarios»; el fichero tiene **25**, contados a máquina. Corregido en el informe. Ver §9.5.

| # | Requisito | Escenario | Evidencia |
|---|---|---|---|
| 1 | Registro de seis, nombres congelados | The registry holds exactly the six expected tools | `test_the_registry_holds_exactly_the_six_frozen_tools` — seis entradas, nombres = `TOOL_NAMES`, y **`perfil_punto_venta` y `buscar_complementarios` ausentes por nombre** |
| 2 | ” | A tool outside the frozen set is rejected | `test_a_tool_outside_the_frozen_set_is_refused_at_construction` · `test_a_registry_missing_one_of_the_six_is_refused_at_construction` — el conjunto es **igualdad**, no techo |
| 3 | Esquema publicado y argumentos validados antes de ejecutar | Arguments are validated before execution | `test_an_invalid_argument_is_refused_before_any_port_is_touched` — **comprueba que los registros de llamada del puerto están vacíos** · `test_an_undeclared_argument_is_refused_rather_than_ignored` |
| 4 | ” | The catalogue search bounds its result size | `test_the_catalogue_search_bounds_its_result_size` — `minimum` y `maximum` en el esquema publicado |
| 5 | Nada escribe, comprobado estructuralmente | No captured port exposes a write method | `test_no_collaborator_captured_by_a_tool_exposes_a_write_method` · `test_no_collaborator_captured_by_a_tool_can_issue_a_write_http_verb` |
| 6 | ” | A writing tool fails the check rather than passing it | `test_a_tool_capturing_a_writing_port_is_refused_however_it_describes_itself` — **registra un puerto que escribe de verdad** y con un descriptor que afirma lo contrario |
| 7 | El fallo es observación con causa cerrada | A dependency failure comes back as data | `test_a_dependency_failure_comes_back_as_a_failed_observation_and_not_an_exception` |
| 8 | ” | An unknown piece reference is an observation and not an error | `test_an_unknown_sku_is_a_failed_observation_with_its_cause` (3 tools) · `test_a_failure_cause_is_always_a_code_of_the_closed_vocabulary` |
| 9 | Disponibilidad como etiqueta, nunca cifra | The label carries no figure | `test_no_availability_label_contains_a_digit` · `test_the_availability_observation_carries_no_stock_quantity_anywhere` — **busca los valores de `QTY_BUCKETS` en toda la observación** |
| 10 | ” | Every bucket the feed defines maps to a label | `test_every_bucket_the_feed_can_store_has_a_label` — compara contra `QTY_BUCKETS` **importado del feed** |
| 11 | «Sin ámbito» es valor propio | A principal with no point of sale gets the unscoped value | `test_a_principal_with_no_point_of_sale_gets_the_unscoped_value` |
| 12 | ” | A piece the point of sale does not carry is not reported as sold out | `test_a_piece_the_point_of_sale_does_not_carry_is_not_reported_as_out_of_stock` — **los dos mundos en la misma prueba**, y comprueba que difieren |
| 13 | La observación declara su frescura | Freshness travels with the label | `test_the_availability_observation_declares_the_age_of_the_projection` |
| 14 | ” | A stale projection still answers | `test_a_stale_projection_still_answers_and_carries_its_age` — proyección de 9 h, responde y declara > 3600 s |
| 15 | La repregunta elige eje, el código escribe | The same axis always produces the same question | `test_the_same_axis_always_produces_the_same_question` — **los cuatro ejes, dos invocaciones cada uno**, comparado contra `CLARIFICATION_TEMPLATES` |
| 16 | ” | An axis outside the closed set is rejected before execution | `test_an_axis_outside_the_closed_set_is_rejected_before_execution` — causa `argumento_invalido` y `content == {}` |
| 17 | Direccionamiento por SKU | A tool resolves a piece from its SKU | `test_a_piece_anchored_tool_resolves_the_piece_from_its_sku` — **comprueba que la lectura fue por la puerta del SKU** |
| 18 | ” | No tool schema admits an internal identifier | `test_no_tool_schema_declares_an_internal_product_identifier` — recorre los seis esquemas |
| 19 | Observaciones acotadas, sin *score* crudo | No observation carries a raw score | `test_no_observation_carries_a_raw_score_or_an_internal_identifier` — **recorre recursivamente toda la observación** de las seis tools y además busca el UUID de la pieza |
| 20 | ” | Ordering travels as a position | `test_ordering_travels_as_a_position` — `posicion` consecutiva desde 1 |
| 21 | Ninguna tool llama a un proveedor de chat | The registry runs with no provider credential configured | `test_every_tool_produces_its_observation_with_no_chat_provider_configured` — borra cuatro variables de entorno y ejerce las seis |
| 22 | ” | Embedding calls are visible and kept apart | `test_embedding_calls_are_counted_in_a_counter_of_their_own` — **y comprueba que las tools que no embeben no mueven el contador** · `test_the_assistance_layer_provider_call_figure_is_untouched_by_this_capability` |
| 23 | Sin ruta y el contrato no se mueve | The snapshot is untouched | `tests/api/test_openapi_snapshot.py::test_openapi_snapshot_is_stable` *(preexistente, verde sin regenerar)* · §7 |
| 24 | ” | Sale assistance is unaffected | **Las 1418 pruebas de la línea base, intactas y verdes** — incluidas las de `test_generation.py`, `test_guardrails.py` y `test_orchestrator.py`, que ejercen los tres modos · `test_the_sale_assistance_response_shape_is_the_one_the_router_change_left` fija el conjunto de campos |
| 25 | Los tests corren sin red | The suite opens no socket | `test_the_whole_registry_runs_with_no_socket_available` · `test_the_assist_package_imports_no_provider_client` *(preexistente)* |

**El escenario 24 se apoya en la línea base y conviene decirlo así.** La prueba que escribí fija el
**conjunto de campos** de `AssistResponse`, no el comportamiento de los tres modos. Lo que demuestra
que la asistencia de venta no se ha movido es que **las 1418 pruebas previas siguen en verde con
sus mismos nombres**, y entre ellas están las que recorren M1, M2 y M3 de punta a punta. Escribir
una prueba nueva que repitiera eso habría sido duplicar cobertura, no añadirla.

---

## 4. Los nueve escenarios de la HU

La tabla completa, escenario a escenario, está en el **§6 del
[informe de implementación](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c32a-implementation-measurements.md)**
(tarea 7.6). Resumen de cobertura:

| Escenario de la HU | Tests | Estado |
|---|---|---|
| 1 · seis herramientas exactas | 4 | ✅ |
| 2 · ninguna puede escribir | 5 | ✅ |
| 3 · fallo de dependencia como observación | 3 | ✅ |
| 4 · etiqueta y nunca cifra | 6 | ✅ |
| 5 · «sin ámbito» ≠ «agotado» | 2 | ✅ |
| 6 · repregunta determinista | 3 | ✅ |
| 7 · SKU y referencia desconocida | 6 | ✅ |
| 8 · ninguna llama a un modelo de chat | 4 | ✅ |
| 9 · aquí no hay bucle | 2 + §7 | ✅ |

---

## 5. Las validaciones que `tasks.md` exige, grupo a grupo

| Grupo | Qué exige | Resultado |
|---|---|---|
| **1** Puerta de entrada | línea base por nombres, validate, hash del contrato | ✅ §2 |
| **2** Vocabularios cerrados | 4 etiquetas, mapa desde `QTY_BUCKETS`, sin dígitos, causas de fallo, seis nombres congelados | ✅ `test_no_availability_label_contains_a_digit` · `test_every_bucket_the_feed_can_store_has_a_label` |
| **3** Lecturas nuevas del puerto | pieza por SKU, disponibilidad por pieza, sólo esquema `ai`, frescura reutilizada, dobles ampliados | ✅ §8 — **116 inserciones, 0 borrados** en `retrieval/` |
| **4** Descriptor y registro | descriptor, observación, puertos ya construidos, validación previa, esquemas exportados | ✅ `registry.schemas()` · `test_every_registered_tool_publishes_a_schema_and_a_spanish_description` |
| **5** Las seis tools | las seis sobre su servicio, `top_k` acotado, observaciones acotadas | ✅ §3 filas 1-22 |
| **6** Los invariantes | conjunto congelado, solo-lectura por introspección, falla al registrar, sin proveedor, sin id interno, forma de los esquemas | ✅ §6 |
| **7** Trazabilidad | los cinco tests nombrados más los nueve escenarios | ✅ §3, §4 |
| **8** Cierre | contrato, suite por nombres, validate, enlaces, informe, docs, C32b y `DEFERRED_TASKS` | ✅ §1, §7 · [informe](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c32a-implementation-measurements.md) · [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) |

**44/44 tareas marcadas, y ninguna a medias.**

---

## 6. El invariante de solo-lectura, comprobado de las tres formas

El eje que más fácil es aprobar en falso, así que se comprueba tres veces y una de ellas es contra
un puerto que sí escribe.

**Eje 1 — los nombres.** `verify_read_only` exige igualdad con `TOOL_NAMES` antes de mirar nada más.

**Eje 2 — los métodos de cada colaborador capturado.** Medido sobre el registro real, lo que la
introspección encuentra por tool:

```
buscar_catalogo          -> ['CountingEmbeddings', 'FakeProductSearch']
buscar_sustitutos        -> ['FakeProductSearch']
listar_familia           -> ['FakeProductSearch']
consultar_conocimiento   -> ['CountingEmbeddings', 'FakeProductSearch', 'InMemoryKnowledgeIndex']
consultar_disponibilidad -> ['FakeProductSearch', 'ProjectionFreshness']
pedir_aclaracion         -> []
```

> **`InMemoryKnowledgeIndex` aparece aquí desde la segunda pasada, y antes no.** La primera versión
> de la comprobación excluía toda dataclass, y el índice de conocimiento lo es: el único
> colaborador real de `consultar_conocimiento` quedaba fuera de los tres ejes sin que ninguna
> aserción se pusiera roja. Ver §11.1.

**Eje 3 — los verbos HTTP.** Ningún colaborador expone `post`/`put`/`patch`/`delete`. Y hay una
comprobación más fuerte que ésta y es **preexistente**:
`test_the_assist_package_imports_no_provider_client` recorre **todos los módulos de `jbg_ai.assist`**
—ahora también `tools.py`— y exige que ninguno importe `litellm`, `openai`, `anthropic` **ni
`httpx`**. Es decir: en este paquete no hay cliente HTTP que pueda emitir un verbo, porque no hay
forma de construirlo. **Esa prueba extendió su cobertura al módulo nuevo sin que nadie la tocara**,
que es exactamente lo que un invariante escrito por introspección debe hacer.

**La anti-vacuidad, que es lo que falta casi siempre.** Dos de los tres ejes son aserciones sobre
listas: si `captured_collaborators` devolviera `[]` para todo, los dos pasarían sin comprobar nada.
`test_the_read_only_check_reaches_every_port_the_registry_was_handed` fija **qué puertos se ve
capturar a cada tool**, y además deja escrito que `pedir_aclaracion` **no captura ninguno** — sobre
esa tool el invariante pasa **vacuamente**, y eso está declarado y no disimulado (§9.6).

**Y la prueba que hace que esto valga algo dentro de seis meses.**
`test_a_tool_capturing_a_writing_port_is_refused_however_it_describes_itself` construye
`_WritingProjectionPort`, con la forma que tendría un escritor de proyección real
(`save_availability`), lo captura en el cierre de una tool, y **le pone al descriptor una
descripción que afirma explícitamente que no escribe**. La construcción falla. El descriptor no
tiene voto.

---

## 7. El contrato, y que no se movió en absoluto

A diferencia de C31 —que movió tres descripciones y hubo que aplanar los documentos a hojas para
demostrarlo—, aquí **el fichero es idéntico**, así que la prueba es más simple y más fuerte:

```
sha256 guardado ANTES (tarea 1.3) : 43f70fdadd2bd9aa90068d3e74ec2ee25c8d3b3b530f6d33907b1e73d068c684
sha256 al cierre                  : 43f70fdadd2bd9aa90068d3e74ec2ee25c8d3b3b530f6d33907b1e73d068c684
sha256sum -c                      : ai-service/openapi.json: OK
git status --porcelain -- ai-service/openapi.json : (vacío)
```

Y contra el documento **generado**, que es lo que el *snapshot* debería reflejar:

```
rutas en el snapshot congelado : 11
rutas en el documento generado : 11
añadidas por C32a              : NINGUNA
retiradas por C32a             : NINGUNA
¿alguna ruta de agente?        : NINGUNA
```

`test_openapi_snapshot_is_stable` **verde sin regenerar nada**, junto con
`test_snapshot_covers_the_frozen_surface`, `test_snapshot_comparison_detects_drift` y
`test_interactive_docs_stay_disabled`.

**Y la razón estructural por la que no podía moverse:** nada en `src/` importa `assist/tools.py`.
Comprobado por `grep` sobre todo el árbol — las **únicas** referencias están en su propio fichero
de pruebas. No es que el módulo no se haya cableado a una ruta: es que **no es alcanzable** desde la
aplicación.

---

## 8. Alcance negativo, demostrado

`git status --porcelain -- <ruta>` **vacío** en todas:

| Ruta | Estado |
|---|---|
| `backend/` · `frontend/` · `terraform/` · `.github/` | **0 cambios** — y por tanto **sin migración de EF Core**, que es la casilla 10 del DoD |
| `ai-service/openapi.json` | **0 cambios** — §7 |
| `ai-service/migrations/` · `alembic.ini` | **0 cambios** · `alembic heads` → `d7c4e91b25a0`, sin mover |
| `ai-service/src/jbg_ai/api/` | **0 cambios** — ninguna ruta, ningún esquema de contrato |
| `ai-service/src/jbg_ai/knowledge/` | **0 cambios** — `search_knowledge` se **consume**, no se modifica |
| `ai-service/src/jbg_ai/indexing/` | **0 cambios** — `QTY_BUCKETS` sólo se **lee**, y sólo desde un test |
| `ai-service/src/jbg_ai/enrichment/` · `evals/` · `config/` · `prompts/` | **0 cambios** |
| `ai-service/pyproject.toml` | **0 cambios** — **ninguna dependencia nueva**; `pydantic` ya estaba |
| `data/knowledge/` | **0 cambios** |

**Y `retrieval/` se tocó sólo para añadir, demostrado por el propio diff** en vez de por lectura:

```
ai-service/src/jbg_ai/retrieval/ports.py  | 41 +++++++++++++++++
ai-service/src/jbg_ai/retrieval/search.py | 75 +++++++++++++++++++++++++++++++
 2 files changed, 116 insertions(+)

líneas borradas en retrieval/ : NINGUNA
líneas borradas en el doble compartido : NINGUNA
```

**116 inserciones y 0 borrados.** El riesgo que la HU declaraba —*«que el registro se lleve por
delante la frontera de `retrieval/`»*— no se materializó, y no hace falta creerlo: una modificación
de una consulta existente habría producido una línea borrada.

**Sin ajustes ni variables de entorno nuevas:** `config/` sin cambios, y
`test_the_assistance_layer_provider_call_figure_is_untouched_by_this_capability` comprueba además
que no existe ninguna constante de techo de proveedor para las tools.

**Sin TODO/FIXME** en el código nuevo (`grep` sobre `assist/`, `test_tools.py`, `ports.py` y
`search.py`): ninguno.

---

## 9. Incidencias de esta pasada

### 9.1. El invariante de D-6, leído al pie de la letra, es insatisfacible — **CRÍTICO**

D-6 y el ticket fijan el vocabulario de escritura como
`insert|update|delete|write|save|upsert|persist|sync|apply`. Leído como **subcadena**, `sync`
coincide con dos **lecturas**:

| Método | Qué hace |
|---|---|
| `ProductSearchPort.projection_synced_at()` | lee `ai.sync_checkpoint` |
| `ProjectionFreshness.synced_at()` | cachea la lectura anterior |

La primera vive **en el puerto que `consultar_disponibilidad` está obligada a capturar**, así que no
es un caso raro: **no hay registro posible**. Y `Settings` cae por lo mismo, medido:

```
Settings   -> ['blank_index_sync_time_budget_is_default', 'update_forward_refs']
```

`update_forward_refs` es el *shim* deprecado de pydantic v1, que está ahí lo quiera uno o no.

**Qué se hizo, y qué NO.** El vocabulario **no se tocó** —está en dos artefactos, es una decisión
tomada, y cambiarlo por mi cuenta era justo lo que el encargo prohibía—. Lo que se fijó es la
**regla de comparación**, que ningún artefacto especifica: **token a token con igualdad exacta**.
Y la configuración se excluye **por tipo**, nunca por nada que la tool declare sobre sí misma — la
diferencia con una bandera `writes: bool` es que la exclusión vive en el módulo del invariante, y
una tool no puede sacar sus dependencias de la comprobación.

> **Enmendado en la segunda pasada (§11).** La exclusión se escribió primero por *categoría* —todo
> modelo de pydantic y toda dataclass— y eso era un fallo, no un matiz: dejaba fuera un puerto vivo.
> Ahora excluye **dos tipos nombrados**, `Settings` y `ServicePrincipal`. Ver §11.1.

**Queda dicho, porque es lo que se pierde, y decirlo mal ya costó una revisión.** No es una forma
flexionada: es un **verbo que el vocabulario nunca tuvo**. El ejemplo no hay que inventarlo, está en
este repositorio — `SqlAlchemyPosProjection.put_checkpoint()` es un `INSERT … ON CONFLICT DO UPDATE`
y no casa ningún token, **ni casaría por subcadena tampoco**, así que no es la regla de comparación
la que lo pierde. Con él se pierde su familia entera: `put_`, `store_`, `record_`, `commit`,
`flush`. El borrador anterior de este párrafo decía *«una forma flexionada (`saves`, `syncing`)
escaparía; no existe ninguna en el árbol»*, que es cierto y deja al lector con la impresión
equivocada de que el hueco es marginal. **El conjunto es un suelo bajo el grafo de objetos, no una
demostración de que ningún método escribe.** Ensancharlo es una decisión de D-6 y no un parche.

**Esto está señalado al usuario** y consta en el §2.1 y §2.2 del informe. Si la lectura correcta de
D-6 incluye también la regla de comparación, hay que volver sobre ello.

### 9.2. La trampa anunciada como la más cara no existía — **hallazgo**

El ticket, el diseño y el encargo de la sesión anunciaban: *«Ampliar `ProductSearchPort` rompe los
dobles de la suite… es la tarea 3.5 y es trabajo previsto»*.

**No ocurrió, y no podía ocurrir.** `ProductSearchPort` es un `typing.Protocol` **sin
`@runtime_checkable`**, nada hace `isinstance` contra él, y el repositorio **no tiene `mypy` en las
dependencias de desarrollo ni workflow de CI para `ai-service`** — verificado en `pyproject.toml`
(declara `pytest` y `testcontainers`) y en `.github/workflows/` (sólo backend y frontend).

Ampliar `FakeProductSearch` **sigue siendo necesario**, pero por otra razón que es la que había que
escribir: **la suite nueva llama a los dos métodos**. Un lector que confíe en la formulación del
ticket buscará un error de tipos que no existe.

**Corolario que conviene no perder:** nada en esta suite protege el `Protocol`. Una implementación
futura que olvide uno de los dos métodos fallará donde se use, no al construirse.

### 9.3. `low_confidence` no es la abstención — **CRÍTICO, y ningún test lo habría cazado**

La primera versión de `buscar_catalogo` emitía `confianza_baja: response.low_confidence`. Pasaba
todas las pruebas. El propio `retrieval/orchestrator.py` avisa en un comentario de por qué está mal:

> *«An empty `results` is also what a query that simply found nothing produces, and the one field
> that does move with an abstention — `low_confidence` — carries a DIFFERENT, measured meaning
> (cross-branch consensus: 1 of 20 out-of-domain against 10 of 43 answerable). A caller reading it
> as abstention would report the opposite of the truth on the judged set.»*

Sobre el conjunto juzgado, la cifra se mueve **al revés**. Y como la abstención **también** vacía la
lista de candidatos, una observación con cero candidatos y `confianza_baja: true` es exactamente la
confusión contra la que C30a creó la costura `on_abstention`.

**Se encontró leyendo el código del que se depende, no por un test en rojo** — no había test que
pudiera ponerse rojo, porque el campo existía y tenía el tipo correcto. Corregido: la tool usa
`on_abstention` y emite **`abstenido`**; `low_confidence` **no se reexporta bajo ningún nombre**, y
`test_the_catalogue_search_reports_abstention_and_not_the_consensus_flag` lo fija.

> **Matizado en la segunda pasada (§11.3).** Decía aquí que ese test *«lo fija en las dos
> direcciones»*. Las dos direcciones que fijaba eran **qué entra y qué sale del diccionario** —
> `abstenido` presente, `confianza_baja` y `low_confidence` ausentes—, no `True` y `False`: ningún
> test llevaba `buscar_catalogo` a una abstención real, así que **un `"abstenido": False` cableado a
> mano habría pasado las cuatro aserciones**. Que es exactamente el modo de fallo que dejó colarse
> `low_confidence` en primera instancia. Cerrado con
> `test_the_catalogue_search_reports_an_abstention_when_the_retriever_abstains`.

### 9.4. Tres defectos de las pruebas nuevas, y los tres eran míos

La primera ejecución de la suite nueva dio **46 passed / 3 failed**. Ninguno era del código:

| Fallo | Causa | Arreglo |
|---|---|---|
| `test_the_registry_publishes_no_route_…` | `create_app()` sin argumento intenta leer `Settings()` del entorno | Pasar `build_settings()`, y leer las rutas del **documento generado** (`.openapi()["paths"]`) en vez de `app.routes`, que contiene objetos `_IncludedRouter` sin `.path` — y que además es lo que el *snapshot* compara |
| `test_the_sale_assistance_response_shape_…` | Escribí el conjunto de campos **de memoria**: puse `mode` y `debug`, y falta `prompt_version` | Leer los campos reales de `AssistResponse` y fijarlos. **Es la razón de ser de la prueba**: si yo me equivoco escribiéndolos, alguien se equivocará cambiándolos |
| `test_the_whole_registry_runs_with_no_socket_available` | El guardián `forbid_network` de `tests/conftest.py` se instala **antes** que el cuerpo, y en Windows el `ProactorEventLoop` abre un `socketpair` de *loopback* para su propia tubería de despertar. Fallaba en la fontanería de `asyncio`, no en una tool | Construir el bucle **a mano y antes** de levantar el guardián. Es la misma regla de orden que `tests/api/test_health_report.py` ya dejó escrita, y está citada en el docstring |

El segundo es el que más dice: **una prueba de contrato escrita de memoria es una prueba que
documenta la memoria de quien la escribió.** Se arregló leyendo el modelo, no ajustando la aserción
hasta que pasara.

### 9.5. Dos recuentos de los artefactos de partida no cuadran con el árbol — **enmendado**

| Dónde | Decía | Es | Qué se hizo |
|---|---|---|---|
| Encargo de la sesión e informe (primer borrador) | «13 requisitos y **27** escenarios» | **25** | Corregido en el informe. El fichero de delta no se toca: **es él el que tiene razón** |
| Encargo de la sesión | «8 grupos, **39** tareas» | **44** | No se corrige nada: `tasks.md` es el artefacto y tiene 44. Se anota para que el recuento no se propague |

Ninguno de los dos cambia una decisión; se dejan escritos porque un recuento equivocado repetido en
tres sitios acaba pareciendo el correcto.

### 9.6. Los límites del invariante, declarados y no disimulados

1. **`pedir_aclaracion` no captura ningún colaborador**, así que los tres ejes pasan **vacuamente**
   sobre ella. No es un fallo —esa tool no puede escribir porque no tiene con qué— pero un lector
   merece saberlo. Mitigado con la prueba de anti-vacuidad del §6.
2. **La introspección no recorre los atributos de un colaborador.** El límite es «lo que la tool
   recibe», y está declarado en el docstring de `captured_collaborators`. Recorrer atributos
   convierte la comprobación en un barrido del proceso entero: `Settings` sola arrastra toda la
   configuración. Un puerto escondido dentro de otro objeto se escaparía, y quien esté dispuesto a
   esconder una escritura tiene caminos más fáciles.
3. **La introspección ve sólo lo que el ejecutor CIERRA.** *(Añadido en la segunda pasada, §11.4.)*
   Una función de módulo que alcanzara un puerto de módulo por búsqueda global no tiene celda de
   cierre: llegaría a `captured_collaborators` con **cero colaboradores** y pasaría los tres ejes
   sobre una lista vacía. Hoy es inocuo —las seis se construyen como closures anidadas en
   `build_registry`, que es la única costura de construcción— y por eso mismo conviene que esté
   escrito: una tool futura tiene que seguir construyéndose igual, y no tirando de un global.
4. **El vocabulario de escritura no es exhaustivo**, y eso es distinto de la regla de comparación.
   Ver el párrafo enmendado del §9.1.
5. **La exclusión de tipos inertes es por nombre y no por categoría.** `Settings` y
   `ServicePrincipal`, y nada más. Excluir las categorías a las que pertenecen fue el primer
   intento y fue un fallo medido: ver §11.1.

### 9.7. Lo que la implementación refuta de los artefactos, y qué se enmendó

| Refuta | Artefacto | Enmienda |
|---|---|---|
| El vocabulario de escritura como subcadena | `design.md` D-6, `ticket.md` | **Ninguna al artefacto.** Se fija la regla de comparación en el código, se documenta en `tools.py`, en el README y en el informe. **Señalado al usuario para que decida** |
| Faltaba una cuarta causa de fallo | `spec.md`, `ticket.md` | `referencia_no_utilizable` añadida al vocabulario, con su razón: es la distinción que C26 ya hace |
| Ampliar el `Protocol` rompe los dobles | `ticket.md`, `design.md`, encargo | Anotado en informe, plan y `epicas.md`. La tarea 3.5 se hizo igual, por la razón correcta |
| `low_confidence` ≠ abstención | **ningún artefacto lo decía** | `abstenido` en la observación, con test |
| «27 escenarios» / «39 tareas» | encargo e informe | Informe corregido a 25; el recuento de tareas anotado |
| Una pieza sin familia no tiene comportamiento definido | `spec.md` | Observación correcta con `familia: null` y `miembros: []`, documentado en el código |

---

## 10. Lo que esta pasada **no** verifica, dicho aquí

1. **Que las descripciones de las tools sirvan para que un modelo elija bien.** Es la limitación
   estructural del corte: esta mitad **no llama a ningún proveedor**, y una descripción es un
   *prompt* que se itera con medición. Ocurre en **C32b**.
2. **Que la granularidad de seis sea la correcta.** Mismo motivo. El registro queda con los puertos
   inyectados para que C32b pueda reagrupar sin tocarlos ni tocar su suite.
3. **Que la etiqueta cualitativa baste para decidir el pivote a sustitutos.** No hay bucle que lo
   ejerza. Ensanchar el vocabulario no mueve ningún contrato; lo que no se hará es volver al bucket
   crudo.
4. **El comportamiento contra la proyección real.** Las dos consultas SQL nuevas están escritas y
   **no se han ejecutado contra PostgreSQL**: ninguna prueba de este change está marcada `db`, y el
   doble las simula. Se apoyan en las mismas tablas y las mismas columnas que consultas ya en
   producción (`SOURCE_DOCUMENT_SQL`, `SCOPE_BUCKETS_SQL`), pero **eso es un argumento, no una
   medición**. La primera ejecución real ocurrirá en C32b o en el primer despliegue que las use.
5. **`dotnet test` y `npm run test`.** Fuera del diff por completo (§8). `CLAUDE.md` advierte de que
   las dos llegan en rojo de fábrica; no se midió su línea base porque no se tocó ni un fichero de
   ninguna de las dos.
6. **El endpoint .NET de disponibilidad puntual.** Identificado, acotado y **no hecho**, con su
   motivo en [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md). Con una advertencia heredada: **un
   cliente HTTP de propósito general no pasará el tercer eje del invariante**, porque expone `post`,
   `put`, `patch` y `delete`.

---

## 11. Segunda pasada: verificación independiente

> Ejecutada sobre el árbol **ya commiteado** en `ac9adef`, reproduciendo contra el repositorio cada
> cifra y cada «✅» de los §1–§10 en vez de releerlos. Casi todo reprodujo. Lo que no, está aquí.
>
> La distinción que importa: los §1–§10 los escribió quien implementó, y esta sección la escribió
> quien la comprobó. **Cuatro hallazgos, los cuatro corregidos**; ninguno cambia una decisión de
> `design.md`, y tres de los cuatro son enmiendas a afirmaciones que se leían más fuertes de lo que
> el código sostenía.

### 11.1. La exclusión por categoría dejaba fuera un puerto vivo — **CRÍTICO, corregido**

`_is_collaborator` excluía **todo modelo de pydantic y toda dataclass**. `InMemoryKnowledgeIndex`
es una dataclass, y es el puerto que `consultar_conocimiento` captura: **los tres ejes del
invariante nunca lo miraban**. Medido antes de la corrección, y no deducido:

```
consultar_conocimiento   -> ['FakeProductSearch', 'CountingEmbeddings']     ← el índice no está
```

Y no era sólo cobertura perdida: un puerto escrito como dataclass —o como modelo de pydantic— con
`save_availability`, capturado en el cierre exactamente como lo hace `build_registry`, **construía
el registro sin que nada lo rechazara**. Verificado con el control al lado:

```
ANTES   plain class (control)     -> refused          @dataclass -> CONSTRUCTED   pydantic -> CONSTRUCTED
DESPUES plain class (control)     -> refused          @dataclass -> refused       pydantic -> refused
```

Tres afirmaciones escritas lo daban por bueno y las tres eran falsas: el §2.2 del informe
(*«lo que queda dentro es exactamente lo que puede alcanzar un sistema de registro»*), el docstring
de `_is_collaborator` —que enumeraba las exclusiones **omitiendo las dataclasses**, que es lo que el
código sí excluía— y el docstring del test de anti-vacuidad.

**Corregido estrechando la exclusión**, que es la opción que sostiene lo que la propuesta promete:
se excluyen **dos tipos nombrados**, `Settings` y `ServicePrincipal` —configuración e identidad, sin
E/S, que tropiezan con el vocabulario sólo por el *shim* `update_forward_refs` de pydantic v1— y
nada más. **Un puerto se inspecciona sea cual sea la construcción con la que esté escrito.** La
lista vive en el módulo del invariante, así que añadir un tercer nombre es editar el fichero cuya
única razón de existir es comprobar. `test_the_read_only_check_reaches_every_port_the_registry_was_handed`
nombra ahora `InMemoryKnowledgeIndex` para que no pueda volver a caerse en silencio.

### 11.2. `ai.product_document.sku` **no** es único, y el comentario se apoyaba en que lo fuera — corregido

`DOCUMENT_BY_SKU_SQL` llevaba escrito: *«`sku` is UNIQUE on `ai.product_document`, so there is no
ORDER BY and no LIMIT: a second row would be a broken index and silently taking the first would
hide it»*. En las migraciones de `ai-service` la **única** `UniqueConstraint` es
`uq_knowledge_chunk_document_chunk_index`; `sku` es `sa.Column("sku", sa.Text(), nullable=False)`,
sin restricción única y **sin índice de ningún tipo**. La unicidad la impone .NET sobre su propia
tabla (`ProductConfiguration`: `HasIndex(p => p.SKU).IsUnique()`), no este esquema.

**Y no es un descuido de aquella migración: es una decisión registrada.** El ticket del change que
creó la tabla plantea la pregunta y la responde —
[`2026-08-15-add-pgvector-schema-foundation`](../../archive/2026-08-15-add-pgvector-schema-foundation/ticket.md),
pregunta abierta 2: *«¿Índice único sobre `sku` en `product_document`? … **No se crea.** La unicidad
es del corpus, y C13 hace upsert por `product_id`»*. Así que el comentario no sólo afirmaba algo
falso del árbol: **contradecía una decisión tomada y archivada**, y lo hacía para justificar el
`first()`.

Y `document_by_sku` usaba `.mappings().first()`, que hace **exactamente** lo que el comentario decía
querer evitar: ante dos filas devuelve una arbitraria de un resultado sin `ORDER BY`. Resuelven por
esa puerta **cuatro de las seis tools**.

**Corregido a `.one_or_none()`**, que lanza `MultipleResultsFound` —un `SQLAlchemyError`, así que
llega al llamante como `dependencia_no_disponible` con el mensaje real— y el comentario dice ahora
dónde vive la unicidad. Un feed roto se lee como roto, en vez de como una pieza que nadie eligió.

**Esto es lo que la ausencia de prueba `db` dejó pasar, y una prueba `db` tampoco lo habría cazado:**
una fixture pone una fila por SKU. Lo cazó leer la migración. El punto 4 del §10 sigue en pie tal
como está escrito.

### 11.3. La dirección positiva de `abstenido` no la comprobaba nadie — corregido

Ver el recuadro del §9.3. El arreglo del hallazgo que este documento declara como el que más cerca
estuvo de colarse descansaba en un campo cuyo camino `True` **no ejecutaba ningún test**. Cerrado
con `test_the_catalogue_search_reports_an_abstention_when_the_retriever_abstains`, que construye un
mundo de perfil de distancias plano —20 filas, que es la forma sobre la que abstiene la regla
relativa de C25— y afirma `content["abstenido"] is True` y la lista de candidatos vacía. El test que
ya existía pasa a afirmar `is False` explícitamente, para que los dos casos queden fijados.

### 11.4. Tres enunciados que se leían más fuertes que el código — corregidos

| Dónde | Decía | Enmienda |
|---|---|---|
| §9.1 y el docstring de `WRITE_METHOD_VERBS` | lo que se pierde es *«una forma flexionada»* | Es **un verbo que el vocabulario nunca tuvo**: `put_checkpoint()` escribe y no casa, ni por token ni por subcadena. Ver §9.1 |
| §9.6 | dos límites del invariante | **Cinco**. Faltaba el de los cierres (una función de módulo pasaría sobre lista vacía) y el de la exclusión por tipo |
| §3 fila 9 | *«busca los valores de `QTY_BUCKETS` en toda la observación»* | Recorría sólo los valores de primer nivel. Ahora usa `_rows_of`, que es recursivo, y el enunciado es cierto |

### Lo que la segunda pasada **sí** reprodujo

Línea base y cierre por **nombres de test** con `comm` sobre los *node id* (0 desaparecidos);
`sha256` del contrato idéntico y `git diff` vacío; 116 inserciones y 0 borrados en `retrieval/`;
`50 deselected` en `pytest -m db`; 48 funciones + 1 parametrize de 3; `openspec validate --all
--strict` en 58/0; 1026 enlaces con 0 rotos; `alembic heads` en `d7c4e91b25a0`; que nada en `src/`
importa `assist/tools.py`; y **los nueve escenarios de la HU y los 25 de la delta abriendo cada test
citado**, uno a uno, para comprobar que afirma lo que la tabla dice que afirma. No apareció ningún
doble que no pudiera fallar.

Una sola cifra no reprodujo literalmente y no es del change: la línea base medida en un `git
worktree` limpio da **1416 passed / 2 failed**, porque `tiktoken` descarga ahí su fichero BPE con la
caché en frío. Los dos ficheros no están en el diff y los dos tests pasan en el checkout principal.
1416 + 2 = **1418**, la cifra del §1.
