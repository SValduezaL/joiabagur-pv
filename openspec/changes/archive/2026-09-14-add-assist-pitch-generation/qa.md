# QA — C30b `add-assist-pitch-generation`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** implementación y esta pasada, el **2026-09-14** · **Rama:** `c30b-add-assist-pitch-generation` · **Artefactos:** `f0d5a0c` · **Implementación:** `a149f26` (aislamiento del motor) y `9645176` (C30b)
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **44/44 tareas**. El barrido del grupo 11 —la línea de corte declarada si la sesión se desbordaba— **se ejecutó**, así que no se recortó nada.
> **Este change NO mueve la forma del contrato.** `openapi.json` se regenera por **una descripción**, y el §8 lo demuestra por construcción y no por lectura.
> **Lo que esta pasada encontró:** la puerta numérica —el riesgo mayor declarado del change— **no rechazó nada en 120 generaciones**; el *timeout* de 3 s estaba mal puesto y la primera métrica que lo midió estaba mal escrita; y la comparación de suites por nombres destapó **un defecto real de aislamiento de tests** que no era de este change. Todo en el §10.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| PostgreSQL | `jpv-pv-postgres` (`pgvector/pgvector:pg15`) en el 5433, con **1.168 productos activos con embedding, 32 documentos y 161 fragmentos de conocimiento**, para la muestra y el barrido; testcontainers efímero para los tests marcados `db` |
| Proveedor de LLM | **Llamado de verdad, y sólo fuera de la suite**: 1 petición en el *spike* del certificado (§2) y **175 llamadas** en el barrido (§3). **Ninguna corrida de tests lo llama** — §7 lo verifica |
| Proveedor de *embeddings* | Sólo el que la recuperación ya hacía. Este change **no añade ninguna búsqueda vectorial** |
| TLS | `SSL_CERT_FILE` **y** `REQUESTS_CA_BUNDLE` a un PEM del almacén de Windows concatenado con `certifi` — **131 certificados**. Sin esto ninguna llamada real funciona en esta máquina (§2) |
| Bucle de eventos | `WindowsSelectorEventLoopPolicy` en el *runner* del barrido, que abre el motor asíncrono. `psycopg` rechaza el `ProactorEventLoop` |
| .NET | **no ejecutado, y a propósito**: el diff no toca `backend/` salvo `.env.example`. §7 lo demuestra |
| Frontend | **no ejecutado.** Línea base medida igualmente, para poder demostrar que no se toca |
| Contrato | `ai-service/openapi.json` se regenera con `canonical_openapi_settings()`. Verificado **aplanando los dos documentos a hojas** (§8) |
| Migraciones | **ninguna**. `alembic heads` → `d7c4e91b25a0`, la misma revisión que antes del change |
| Congelados | `git diff` vacío en `retrieval/`, `knowledge/`, `enrichment/`, `indexing/embeddings.py`, `terraform/`, `.github/`, `frontend/` |

---

## 1. Suites automáticas

La línea base se midió **antes de tocar una línea de código**, sobre el árbol limpio en `f0d5a0c`, que sólo contenía los artefactos del change. `git status` respondió limpio, que es la condición correcta de línea base.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`f0d5a0c`, sólo artefactos) | **1195 passed**, 0 failed, 0 skipped, 141,9 s |
| **Línea base** `frontend/` | **113 failed de 597**, 14 ficheros de 48, 149,6 s |
| `ai-service` al cerrar el código de la capa | **1284 passed**, 0 failed, 144,1 s |
| `ai-service` tras el barrido y sus tests | **1303 passed**, 0 failed, 127,9 s |
| `ai-service` tras el arreglo del motor (§10.4) | **1307 passed**, 0 failed, 130,8 s |
| **`ai-service` al cierre** | **1320 passed**, 0 failed, 126,8 s |
| `openspec validate --all --strict` antes y después | **58 passed, 0 failed** en las dos puntas |
| `dotnet test` · `npm run test` al cierre | **no ejecutados**: fuera del diff. Ver §7 |

### La comparación por nombres, que es la que vale

`CLAUDE.md` exige comparar por **nombres de test** y no por recuento.

```
ANTES    1195 passed | rojo 0 | skipped 0
DESPUES  1320 passed | rojo 0 | skipped 0

Nombres en rojo NUEVOS  (después − antes) : NINGUNO
Nombres en rojo IDOS    (antes − después) : NINGUNO
```

El conjunto en rojo es **vacío en las dos puntas**, así que el criterio se cumple de la forma más fuerte posible. La suite de `ai-service` **no** es la de `backend/` ni la de `frontend/`, que `CLAUDE.md` advierte que llegan en rojo: ésta llega en verde.

> **La comparación por nombres no fue ceremonia.** Es lo que destapó el defecto del §10.4: un recuento habría dicho «igual de verde» y el fallo seguiría ahí.

### Desglose, y la aritmética cierra exacta

**+125 tests netos** (1195 → 1320), y el reparto cuadra al caso — **ningún test retirado**, sólo dos renombrados:

| Fichero | Tests | Qué cubre |
|---|---|---|
| `tests/assist/test_prompt.py` | **15** | prompt↔constante, secciones, el prompt sin dígitos, la consulta como dato, la lista blanca |
| `tests/assist/test_verification.py` | **27** | las tres comprobaciones, la adyacencia por marcador, las causas |
| `tests/assist/test_pitch.py` | **23** | reparación única, las dos políticas, acumulación de coste, degradación |
| `tests/assist/test_generation.py` | **16** | la capa cableada en el orquestador, los dos cortes, el log |
| `tests/api/test_assist_generation.py` | **15** | la ruta real: frontera, no persistencia, credencial y modelo |
| `tests/evals/test_assist_sweep.py` | **11** | la muestra declarada y la aritmética del barrido |
| `tests/config/test_settings.py` | 36 → **50** | *(+14)* el *timeout*, la credencial y el modelo de assist |
| `tests/db/test_engine.py` | 9 → **13** | *(+4)* el aislamiento del motor, §10.4 |
| | **107 + 18 = 125** | = 1320 − 1195 ✓ |

**Tres tests renombrados y ninguno borrado.** Medido sobre los conjuntos de *node id* de las dos puntas, no sobre la tabla: **128 node id aparecen y 3 desaparecen**, y los tres que desaparecen reaparecen con otro nombre, así que los tests **nuevos** son 128 − 3 = **125** y la tabla de arriba los reparte enteros.

| Antes | Después |
|---|---|
| `tests/assist/test_orchestrator.py::test_the_argument_is_empty_its_provenance_absent_and_the_usage_zero` | `test_without_a_generation_client_the_argument_is_empty_and_its_provenance_absent` |
| `tests/assist/test_orchestrator.py::test_no_language_model_provider_is_called_in_any_mode` | `test_no_language_model_provider_is_called_when_no_client_is_configured` |
| `tests/api/test_assist_real.py::test_the_real_path_emits_an_empty_pitch_a_null_prompt_and_zero_usage` | `test_without_a_provider_credential_the_route_emits_no_pitch_and_a_null_prompt_version` |

Los tres afirmaban como **requisito universal** lo que tras C30b es un **estado de despliegue**; la propiedad no se pierde, se condiciona, y sigue verde. Mismo gesto que C26 y C30a hicieron con sus 501.

> **La primera redacción de este informe decía «dos».** El tercero —el de la ruta HTTP— es el mismo gesto que los otros dos y se renombró en el mismo commit, pero no se listó. Lo destapó la pasada de verificación comparando los conjuntos de *node id* en lugar de leer la tabla: el neto de 125 cuadraba igual, porque una renombrada suma y resta a la vez.

---

## 2. La puerta de entrada: el certificado, comprobado con una llamada real

Tarea 1.4, y va **antes** de escribir el código que depende de ella. `--system-certs` arregla a `uv`, **no al proceso Python**: en tiempo de ejecución `litellm` sale por `aiohttp`/`httpx`, que usan el bundle de `certifi` y no el almacén de Windows, y esta máquina tiene un MITM de Norton cuya raíz vive sólo ahí.

```
certifi + ssl.enum_certificates('ROOT'|'CA'), SIN filtrar por bandera de confianza
  -> C:\Users\sergi\.jbg-ai\ca-bundle.pem  ·  certifi + 131 certificados
```

Filtrar por la bandera **no** basta: la raíz de Norton no la lleva y el bundle sale incompleto. Verificado con una petición real de una sola llamada, no con una comprobación de que el fichero existe:

```
content: ok
usage:   12 prompt · 1 completion · 13 total
model:   gpt-4o-mini-2024-07-18
```

Esa corrida dejó además un dato que se usó en el diseño del cliente: `response.model` devuelve el identificador **resuelto** por el proveedor, distinto del solicitado. Se reporta el configurado, que es el que la tabla de precios de `evals/golden/pricing.yaml` sabe buscar.

**Ningún test lo nota**, porque ninguno llama al proveedor.

---

## 3. El barrido de contexto, y la muestra declarada antes de medir

### 3.1. La muestra (grupo 2), escrita antes de tomar una sola cifra

Medición sobre el índice vivo, **antes de elegir nada**, de 1.168 piezas activas con embedding:

| materiales declarados | piezas | % |
|---|---|---|
| 0 | 122 | 10,4 % |
| 1 | 955 | 81,8 % |
| 2 | 90 | 7,7 % |
| 3 | 1 | 0,1 % |

Las de **≥2 materiales son el 7,8 %** y son las únicas que arrastran la sección de piezas mixtas, o sea donde vive el riesgo de atribución cruzada. De ahí que la muestra sea **estratificada a partes iguales** —20 y 20— y no proporcional, que habría traído una o dos. Las de **0 materiales quedan fuera y no por descuido**: `ground_piece` no les direcciona ningún fragmento, así que el parámetro barrido no puede moverlas.

Selección determinista y **escrita, no re-derivada**: `ORDER BY md5(product_id::text) LIMIT 20` por estrato, con los 40 identificadores en [`evals/assist/sweep-sample.yaml`](../../../../ai-service/evals/assist/sweep-sample.yaml). Una muestra que se recalcula puede moverse entre dos brazos, y dos brazos medidos sobre piezas distintas no son una ablación de nada. `test_the_sweep_sample_is_declared_and_not_derived_at_run_time` lo fija.

El golden set **no sirve** para esto y está comprobado: 72 consultas, **0 con ancla de pieza**. Anotado en la ficha de C38.

### 3.2. El barrido, ejecutado

120 generaciones · 3 brazos · `gpt-4o-mini` a temperatura 0 · **0,0897 USD** · artefacto [`c30b-assist-sweep-5a6e1b4b8621.json`](../../../../ai-service/evals/results/c30b-assist-sweep-5a6e1b4b8621.json), atado a `run_id`, `git_sha` y `prompt_version`.

| Brazo | Citas ofrecidas | Rechazo 1.ª pasada | Causas | **Retenidos** | Citas retiradas | Frases | USD/petición |
|---|---|---|---|---|---|---|---|
| 1 sección | 2,0 | 5/40 = 12,5 % | 7 × correspondencia | **0** | 5 | 4,38 | 0,00048 |
| **2 secciones** *(se sirve)* | 3,5 | 22/40 = 55,0 % | 40 × correspondencia | **0** | 29 | 4,55 | 0,00077 |
| 3 secciones | 5,0 | 28/40 = 70,0 % | 74 × correspondencia | **0** | 49 | 4,40 | 0,00099 |

**0 errores de proveedor en 175 llamadas. 0 argumentarios retenidos. 0 violaciones de la puerta numérica.**

### 3.3. La decoración, medida

De las citas **ofrecidas** al modelo, qué acaba publicándose:

| Brazo | Ofrecidas | Declaradas y verificadas | Declaradas y no verificables | Nunca declaradas | % publicado |
|---|---|---|---|---|---|
| 1 sección | 80 | 68 | 5 | 7 | 85,0 % |
| 2 secciones | 140 | **60** | 29 | 51 | **42,9 %** |
| 3 secciones | 200 | 61 | 49 | 90 | 30,5 % |

Es el argumento de D9 convertido en cifra: en el ancho que se sirve, emitir todo lo recuperado habría publicado **140 citas donde 60 sobreviven a la verificación**.

### 3.4. Las dos decisiones que el barrido tenía que tomar (tarea 11.4)

| Decisión | Umbral declarado **antes** | Medido | Resultado |
|---|---|---|---|
| Plegado de signos en la correspondencia | se añade si >10 % de los fallos son de puntuación | **3 de 121 = 2,5 %** | **NO se añade** |
| *Timeout* de 3 s | se promueve a `Settings` si corta generaciones buenas | p95 **2.863 ms** por llamada; **8 de 175 = 4,6 %** por encima de 3 s, 1 de 175 por encima de 4 | **sube a 4 s y pasa a `Settings`** |

---

## 4. Escenarios de la delta, uno a uno

**15 requisitos** —13 `ADDED`, 1 `MODIFIED`, 1 `REMOVED`— y **27 escenarios**. Cada escenario, su test.

### `assist-generation` — la capa escribe en los dos modos anclados (2)

| Escenario | Test |
|---|---|
| A piece with no question receives an argument | `test_a_piece_with_no_question_receives_its_argument_and_the_citations_it_used` |
| A question about the piece is answered in prose | `test_a_question_about_the_piece_is_answered_in_prose_with_a_citation` |

### `assist-generation` — ninguna cifra ausente del contexto (3)

| Escenario | Test |
|---|---|
| A figure absent from the context is rejected even when plausible | `test_figure_absent_from_context_is_rejected_even_if_plausible` |
| A figure adjacent to a currency marker is rejected even when admitted | `test_price_adjacent_figure_is_rejected_even_when_whitelisted` *(parametrizado sobre los 4 marcadores)* + `test_the_recorded_cause_tells_currency_adjacency_from_absence_from_the_context` |
| Price and stock travel as placeholders | `test_the_generated_argument_carries_the_placeholders_and_never_a_figure` + `test_response_contains_no_literal_price_or_stock_number` |

### `assist-generation` — la cita publicada es la que se usó (3)

| Escenario | Test |
|---|---|
| The model declares which fragment each citation supports | `test_a_verified_argument_is_published_with_the_citations_it_declared` |
| The declared fragment does not reach the response | `test_no_field_of_the_response_exposes_the_declared_supporting_fragment` |
| Echoing every supplied identifier does not satisfy the requirement | `test_echoing_every_supplied_identifier_does_not_satisfy_the_requirement` |

### `assist-generation` — una reparación y dos políticas (3)

| Escenario | Test |
|---|---|
| Two checks fail and share a single repair | `test_two_failed_checks_share_a_single_repair` |
| A dangling citation survives the repair and the argument is dropped | `test_dangling_citation_triggers_single_repair_then_drops_the_pitch` |
| An unverifiable claim withdraws its citation and keeps the argument | `test_unverifiable_claim_withdraws_its_citation_not_the_pitch` + `test_unverifiable_claim_withdraws_its_citation_and_the_prose_is_served` |

### `assist-generation` — degradar no empobrece (1)

| Escenario | Test |
|---|---|
| The argument is dropped and the citations remain | `test_degraded_response_keeps_the_citations_that_grounded_it` |

> Comparado **contra lo que la capa estructurada produce sola en la misma corrida**, no contra una lista recordada: el test sirve dos veces, con cliente y sin él, y compara citas, grupos, avisos y abstención.

### `assist-generation` — `prompt_version` dice si la capa corrió (2)

| Escenario | Test |
|---|---|
| A rejected argument still reports its prompt version | `test_rejected_pitch_still_reports_its_prompt_version` + `test_rejected_pitch_still_reports_its_prompt_version_over_the_whole_layer` |
| A mode that does not generate reports no prompt version | `test_free_query_mode_calls_no_provider` + `test_a_deployment_without_a_generation_client_serves_the_structured_response` |

### `assist-generation` — no se persiste, ni en base ni en log (2)

| Escenario | Test |
|---|---|
| Serving a request writes nothing | `test_pitch_is_not_persisted_anywhere` |
| The log carries the provenance and not the text | `test_pitch_text_is_never_written_to_the_log` + `test_the_argument_is_not_written_to_any_log_by_the_http_path` + `test_the_log_records_why_an_argument_was_refused` |

### `assist-generation` — el prompt está fijado a su fichero (1)

| Escenario | Test |
|---|---|
| The declared version and the loaded file agree | `test_prompt_version_matches_the_loaded_prompt_file` |

### `assist-generation` — no se llama cuando no hay sobre qué escribir (2)

| Escenario | Test |
|---|---|
| An abstained request calls no provider | `test_abstained_request_calls_no_provider` |
| The free-query mode calls no provider | `test_free_query_mode_calls_no_provider` |

> Los dos con un `complete` que **falla ruidosamente** si se le llama, no con un contador que se lee después: un corte que dejara de cortar no puede pasar en silencio.

### `assist-generation` — el fallo del proveedor degrada (1)

| Escenario | Test |
|---|---|
| The provider fails and the structured response is served | `test_provider_failure_degrades_to_structure_without_prose` + `test_a_provider_failure_is_answered_with_two_hundred_and_the_structured_response` + `test_a_timeout_degrades_and_is_recorded_as_a_timeout` |

### `assist-generation` — el uso se acumula (1)

| Escenario | Test |
|---|---|
| A repaired request reports the sum of both calls | `test_usage_is_accumulated_across_the_repair` + `test_the_reported_usage_is_the_sum_of_both_calls` |

### `assist-generation` — la consulta es dato (1)

| Escenario | Test |
|---|---|
| A query shaped like an instruction does not change the system behaviour | `test_prompt_injection_in_the_query_does_not_change_the_system_message` + `test_an_instruction_shaped_query_reaches_the_provider_as_delimited_data` |

### `assist-generation` — la fidelidad semántica NO se comprueba (1)

| Escenario | Test |
|---|---|
| The limitation is declared and no judge runs in the serving path | `test_out_of_scope_is_declared_and_not_quietly_performed` + el techo de dos llamadas de `test_two_failed_checks_share_a_single_repair` |

### `assist-generation` — `MODIFIED`: las citas son las que usó (4)

| Escenario | Test |
|---|---|
| A citation resolves and locates | *(C30a, sigue verde)* `test_every_citation_resolves_to_a_real_document_and_heading` |
| The claim scope travels with every citation | *(C30a, sigue verde)* `test_the_piece_anchored_mode_cites_no_establishment_claim` |
| The catalogue is never cited | *(C30a, sigue verde)* `test_no_citation_points_at_a_product_or_at_the_catalogue` |
| A response carrying an argument publishes only the citations it used | `test_a_response_carrying_an_argument_publishes_only_the_citations_it_used` + `test_only_the_citations_the_argument_declared_reach_the_response` |

### `assist-generation` — `REMOVED`: la prohibición de generar

El requisito *This capability generates no prose and calls no provider* se retira. Sus garantías **no se pierden, se estrechan**, y cada mitad tiene test:

| Garantía | Dónde sobrevive |
|---|---|
| No llamar al proveedor en el modo de consulta libre | `test_free_query_mode_calls_no_provider` |
| No llamar al proveedor con abstención | `test_abstained_request_calls_no_provider` |
| No añadir llamadas de *embedding* | ninguna búsqueda vectorial nueva; `git diff` vacío en `retrieval/` y `knowledge/` |
| Argumentario vacío y `prompt_version` nulo en un despliegue sin capa | `test_a_deployment_without_a_generation_client_serves_the_structured_response` |

---

## 5. Los 19 escenarios de la historia, uno a uno

| # | Escenario | Test |
|---|---|---|
| 1 | Pieza sin pregunta recibe argumentario con sus citas | `test_a_piece_with_no_question_receives_its_argument_and_the_citations_it_used` |
| 2 | Pregunta sobre la pieza, en prosa y con cita | `test_a_question_about_the_piece_is_answered_in_prose_with_a_citation` |
| 3 | Precio y stock como placeholder, ningún campo con cifra | `test_the_generated_argument_carries_the_placeholders_and_never_a_figure` · `test_response_contains_no_literal_price_or_stock_number` |
| 4 | Cifra ausente rechazada aunque plausible | `test_figure_absent_from_context_is_rejected_even_if_plausible` · `test_a_surviving_invented_figure_drops_the_pitch` |
| 5 | Cifra pegada a moneda rechazada aunque esté en la lista blanca | `test_price_adjacent_figure_is_rejected_even_when_whitelisted` · `test_a_surviving_currency_adjacent_figure_drops_the_pitch` |
| 6 | Cita colgante: una reparación y luego sin argumentario | `test_dangling_citation_is_never_published` · `test_dangling_citation_triggers_single_repair_then_drops_the_pitch` |
| 7 | Tramo ausente: se retira esa cita, la prosa se publica, queda en el log | `test_unverifiable_claim_withdraws_its_citation_not_the_pitch` · `test_unverifiable_claim_withdraws_its_citation_and_the_prose_is_served` |
| 8 | Las dos puertas comparten una sola reparación | `test_two_failed_checks_share_a_single_repair` |
| 9 | Al degradar, las citas no se pierden | `test_degraded_response_keeps_the_citations_that_grounded_it` |
| 10 | El contrato distingue «no redactamos» de «se rechazó» | `test_rejected_pitch_still_reports_its_prompt_version` · `test_a_deployment_without_a_generation_client_serves_the_structured_response` |
| 11 | La consulta libre sigue sin argumentario y sin llamada | `test_free_query_mode_calls_no_provider` |
| 12 | La abstención no llama al proveedor | `test_abstained_request_calls_no_provider` |
| 13 | Fallo del proveedor: 200 y nunca 5xx | `test_provider_failure_degrades_to_structure_without_prose` · `test_a_provider_failure_is_answered_with_two_hundred_and_the_structured_response` |
| 14 | El argumentario no se persiste | `test_pitch_is_not_persisted_anywhere` |
| 15 | El texto no llega a ningún log | `test_pitch_text_is_never_written_to_the_log` · `test_the_argument_is_not_written_to_any_log_by_the_http_path` |
| 16 | Prompt y constante no pueden divergir | `test_prompt_version_matches_the_loaded_prompt_file` |
| 17 | La consulta es dato y nunca instrucción | `test_prompt_injection_in_the_query_does_not_change_the_system_message` · `test_an_instruction_shaped_query_reaches_the_provider_as_delimited_data` |
| 18 | El uso de tokens se acumula sobre la reparación | `test_usage_is_accumulated_across_the_repair` · `test_the_reported_usage_is_the_sum_of_both_calls` |
| 19 | Fuera de alcance explícito | `test_out_of_scope_is_declared_and_not_quietly_performed` |

### Los dos tests que C30a **no podía** escribir

- **`test_response_contains_no_literal_price_or_stock_number`** corre sobre la respuesta completa y con un argumentario **no vacío**, y lo afirma en el propio test (`assert body["pitch"]`, con el comentario de que un *pitch* vacío haría pasar la comprobación por construcción). Su equivalente de C30a corría sobre un `pitch` vacío y no afirmaba nada sobre la prosa.
- **`test_pitch_is_not_persisted_anywhere`** cuenta DML con un listener `before_cursor_execute` sobre la **clase `Engine`**, así que ve cualquier motor creado durante la petición, incluido uno que la capa se construyera — que es justo lo que una comprobación de importaciones no puede ver. Y **demuestra que el contador está vivo** ejecutando un `INSERT` de control: una comprobación rota daría el mismo resultado limpio que una capa que de verdad no escribe.

---

## 6. Las validaciones que `tasks.md` exige, grupo a grupo

| Grupo | Exigencia | Evidencia |
|---|---|---|
| **1** Puerta de entrada | Línea base por nombres, `validate --all --strict`, certificado | §1 y §2. `58 passed, 0 failed` antes de tocar nada |
| **2** Muestra del barrido | Declarada **antes** de medir, estratificada, con criterio escrito | §3.1 · `sweep-sample.yaml` con los 40 identificadores · 3 tests la fijan |
| **3** Prompt versionado | Fichero, constante, test fichero↔constante, prosa corrida | `prompts/assist/v1.md` · `test_prompt_version_matches_the_loaded_prompt_file` · `test_the_system_message_forbids_lists_and_pins_the_placeholders` |
| **4** Esquema de salida | `AssistPitch`/`UsedCitation` **fuera** de `api/schemas/`, y no en el cable | `assist/schema.py` · `test_no_field_of_the_response_exposes_the_declared_supporting_fragment` |
| **5** Cliente generativo | Costura replicada, `usage` devuelto, `timeout`, fake por constructor | `assist/llm.py` · `test_usage_is_accumulated_across_the_repair` · `test_the_usage_type_adds_rather_than_replacing` |
| **6** Las tres comprobaciones | Resolución, correspondencia, puerta numérica sobre el **objeto** | `assist/verification.py` · **27 tests** · `test_the_whitelist_is_built_from_the_payload_and_not_from_the_rendered_prompt` |
| **7** Reparación y degradación | Una reparación, techo de 2 llamadas, dos políticas, citas preservadas | `assist/pitch.py` · **23 tests** |
| **8** Cableado | Los dos cortes, `prompt_version` siempre que corre, degradación, consulta como dato | `assist/orchestrator.py` · **16 tests** |
| **9** No persistencia | Listener `before_cursor_execute` contando DML; texto nunca en log | `test_pitch_is_not_persisted_anywhere` · `test_pitch_text_is_never_written_to_the_log` |
| **10** Contrato | Una descripción, verificada **campo a campo** | §8 |
| **11** Barrido | Ejecutado en 1/2/3 secciones, tasa **por causa**, coste, sin *faithfulness* | §3 |
| **12** Specs | `validate <change> --strict` y `--all --strict` | `Change ... is valid` · `58 passed, 0 failed` |
| **13** Cierre | Suite por nombres, informe, documentación, fichas de C31 y C38 | §1 · informe · `epicas.md`, plan, `README.md` · notas en C31 y C38 |

**44/44.** El grupo 11 era la línea de corte declarada y **no se cortó**.

---

## 7. Alcance negativo, demostrado

`git diff f0d5a0c..HEAD --stat` sobre las zonas declaradas fuera de alcance:

```
backend/.env.example | 24 ++++++++++++++++++++----
1 file changed, 21 insertions(+), 3 deletions(-)
```

**Un solo fichero de código fuera de `ai-service/`**, y es el que se pidió expresamente después de entregar: el ejemplo de entorno, sin ningún secreto. `backend/.env` sigue ignorado por git, comprobado con `git check-ignore`. El resto del diff fuera de `ai-service/` es **documentación** y está dentro del alcance declarado: `Documentos/` —el informe, `epicas.md` y el plan— y `openspec/` —los artefactos del change y `DEFERRED_TASKS.md`—.

> **Esta cifra estuvo mal en la primera redacción**, que citaba `38 insertions(+), 2 deletions(-)`: es el estado de `9645176`. El commit que añadió este mismo `qa.md` —`6e765f2`— adelgazó el ejemplo de entorno en la misma pasada y el bloque no se volvió a ejecutar. La conclusión no se mueve; el número sí, y se corrige en vez de repetirse.

Vacío en: `frontend/`, `terraform/`, `.github/workflows/`, `ai-service/migrations/`, `ai-service/src/jbg_ai/retrieval/`, `ai-service/src/jbg_ai/knowledge/`, `ai-service/src/jbg_ai/enrichment/`, `ai-service/src/jbg_ai/indexing/embeddings.py`.

**Ninguna migración**: `alembic heads` → `d7c4e91b25a0`, la misma revisión que antes.

**Ni una llamada real en los tests.** Tres verificaciones independientes:

1. `test_the_assist_package_imports_no_provider_client` recorre el grafo de módulos de `jbg_ai.assist` y comprueba que ninguno importa `litellm`, `openai`, `anthropic` ni `httpx` a nivel de módulo. `assist/llm.py` lo importa **dentro de la llamada**, igual que `enrichment/llm.py`.
2. `test_no_language_model_provider_is_called_when_no_client_is_configured` parchea `litellm.acompletion` para que reviente y sirve los tres modos.
3. Los 107 tests nuevos conducen el cliente **real** sobre un `complete` guionizado: se ejercitan el parseo, el *timeout*, la extracción de `usage` y su acumulación, y sólo se sustituye el socket.

---

## 8. El contrato, y exactamente qué se movió

Regenerado con `canonical_openapi_settings()`. La verificación **no fue leer el diff**, sino aplanar los dos documentos a hojas y compararlas:

```
hojas antes = 1102     hojas después = 1102
añadidas 0 · retiradas 0 · cambiadas 1

  $.components.schemas.AssistResponse.properties.prompt_version.description
    - "Version of the prompt that wrote the pitch. Null while there is no pitch"
    + "Version of the prompt the generation layer ran with; null when it did not run"
  ¿es una description? True

forma de prompt_version sin la descripción: IDÉNTICA
  {"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Prompt Version"}

campos añadidos []  ·  retirados []  ·  con el tipo cambiado []
bloques `required` idénticos: sí   ·   rutas idénticas: sí
```

`test_openapi_snapshot_is_stable` en verde. Y `supported_claim` **no viaja al cable**, así que toda la verificación de atribución cuesta **cero** movimiento de forma.

Los tres ajustes nuevos —`JPV_ASSIST_PITCH_TIMEOUT_SECONDS`, `JPV_ASSIST_LLM_API_KEY`, `JPV_ASSIST_LLM_MODEL`— **no tocan el contrato**, y están **fijados en el perfil canónico** para que un valor exportado en el entorno no pueda colarse en el *snapshot*: `test_canonical_openapi_settings_pin_the_pitch_timeout` y `test_canonical_openapi_settings_pin_the_assist_provider_fields`.

---

## 9. Los ocho no negociables, verificados en código

| # | No negociable | Verificación |
|---|---|---|
| 1 | No reutilizar `LiteLlmEnrichClient`; replicar la costura y devolver `usage` | `assist/llm.py` propio · `test_usage_is_accumulated_across_the_repair` |
| 2 | La puerta lee el **objeto** de payload, nunca el prompt renderizado | `test_the_whitelist_is_built_from_the_payload_and_not_from_the_rendered_prompt` · `test_the_instructions_carry_no_figure_of_their_own` |
| 3 | Adyacencia a moneda o stock rechaza **siempre** | `test_price_adjacent_figure_is_rejected_even_when_whitelisted`, con `750` **en la lista blanca** afirmado como premisa del test |
| 4 | La prosa corrida se impone en el **prompt**, no perdonando en la puerta | `test_the_system_message_forbids_lists_and_pins_the_placeholders` · `test_an_enumeration_numeral_is_rejected_and_classified_apart` (rechaza igual, sólo **clasifica** aparte) |
| 5 | `supported_claim` **no** viaja al cable | `test_no_field_of_the_response_exposes_the_declared_supporting_fragment` |
| 6 | Una sola reparación, violaciones acumuladas, techo de 2 llamadas | `test_two_failed_checks_share_a_single_repair` · `test_the_repair_message_names_every_violation_in_one_turn` |
| 7 | Dos políticas distintas; al degradar las citas **no** se vacían | `test_a_hard_violation_beside_a_soft_one_still_drops_the_whole_argument` · `test_degraded_response_keeps_the_citations_that_grounded_it` |
| 8 | Consulta libre y abstención cortan **antes**; proveedor caído degrada con 200 | `test_free_query_mode_calls_no_provider` · `test_abstained_request_calls_no_provider` · `test_a_provider_failure_is_answered_with_two_hundred_and_the_structured_response` |

---

## 10. Incidencias de esta pasada

### 10.1. La puerta numérica no rechazó nada, y era el riesgo mayor declarado

**0 de 120 generaciones.** El diseño declara como riesgo mayor del change que *«la puerta numérica se coma los argumentarios buenos»*. No ocurrió ni una vez: las 121 violaciones del barrido son **todas** de correspondencia.

La lectura honesta **no** es que la puerta sobre. La regla de adyacencia nace de una medición del corpus —`750` y `585` viven en `material-oro.md`— que sigue siendo cierta, y la puerta está probada por unitarios incluido el caso de `750 €` que la motivó. La prevención en el prompt hizo el trabajo y la detección no tuvo que actuar.

**Y el denominador de ese cero no es 120.** Contados los numerales de los 120 argumentarios generados del artefacto:

| Medida sobre los 120 argumentarios | Valor |
|---|---|
| Contienen **algún** dígito | **2** |
| Numerales totales que la puerta tuvo que juzgar | **2** — el mismo `2` de «anillo de 2mm» (`SKU315`), en la lista blanca por la talla |
| Rechazados por la puerta | **0** |
| Usan `{{price}}` y `{{stock}}` | **106** |
| Contienen `€` | **0** |

Así que la frase correcta es **«2 numerales vistos, 0 rechazados»**, y no «tasa de falso positivo cero en 120 generaciones», que es lo que la primera redacción de este informe decía. La conclusión no cambia —sale reforzada: **118 de 120 argumentarios no escriben un solo dígito**, que es la prevención del prompt medida directamente en vez de inferida del silencio de la puerta—. Lo que cambia es qué se puede afirmar con esta cifra: el barrido **no** mide la discriminación de la puerta sobre prosa con cifras, porque el modelo casi nunca escribió una. Medir eso exige un brazo que induzca cifras a propósito, y este change no lo corre.

### 10.2. El coste real es 1,9 × el estimado

El ticket estimaba ~0,0004 USD por petición; medido en el ancho que se sirve, **0,00077 USD**. Dos causas visibles en el artefacto: el contexto real es mayor que los ~1.500 tokens estimados (**2.245 de media por llamada**) y **el 55 % de las peticiones gasta la reparación**. Sigue siendo despreciable, pero la cifra de la ficha queda corregida en vez de repetida.

### 10.3. Una métrica del propio arnés estaba mal escrita, y era mía

La primera pasada del *runner* marcaba `would_be_cut_by_serving_timeout` comparando el **tiempo total de la petición** contra un *timeout* que se aplica **por llamada**. Como el 55 % de las peticiones hace dos llamadas, contaba casi toda reparación como un corte: **leía 70 % donde había 4,6 %**, y esa lectura habría justificado mover el umbral tres veces más de lo que la medición sostiene.

Corregido instrumentando la latencia **por llamada** (`PitchOutcome.call_latencies_ms`), repetido el barrido entero, y fijado con `test_the_timeout_is_measured_per_call_and_never_per_request`.

### 10.4. Dos tests que parecían dependientes del orden, y eran un fallo real

Al comparar por nombres —y **no** por recuento— aparecieron dos fallos en `tests/evals/test_reproducibility.py` con la selección `tests/config tests/assist tests/api tests/evals`, que pasaban en la suite completa y en aislamiento. Comprobado **con el árbol limpio y con el modificado**: mismos dos nombres, así que no eran de este change.

No era *flakiness*. Es reproducible en un comando:

```
pytest tests/api/test_retrieval_real.py tests/evals/test_reproducibility.py  -> 2 failed
pytest tests/evals/test_reproducibility.py tests/api/test_retrieval_real.py  -> 19 passed
```

`get_engine(settings)` cacheaba un motor **global de proceso** e **ignoraba el `Settings` que recibe**, así que el primer llamante decidía la base de datos de todos los demás. `test_retrieval_real.py` configura a propósito un host inalcanzable (`@db:5432`, para demostrar el 503) y envenenaba el proceso. En la suite completa no se veía porque un test intermedio llamaba a `dispose_engine()` por casualidad. Segundo escalón: `get_sessionmaker` devolvía su fábrica cacheada **antes** de preguntar por el motor.

Corregido en `a149f26`, **fuera del alcance de C30b y a petición expresa**, con cuatro tests de regresión — uno de los cuales fija que **una URL idéntica sigue reutilizando el mismo motor**, porque el *singleton* de proceso es el objetivo y no debía romperse.

### 10.5. Tres cosas que la implementación refuta de los artefactos del change

| Artefacto decía | La implementación | Por qué |
|---|---|---|
| *«backoff de proveedor propio»* (tarea 5.1) | **No se replica** | `ENRICH_BACKOFF_BASE_SECONDS` son 2 s contra un presupuesto de 4, y con reintentos debajo la garantía de *«no más de dos llamadas»* sería **falsa**: dos llamadas de generación serían cuatro HTTP. Medido: 0 errores de proveedor en 175 llamadas |
| La consulta forma parte del *«payload entregado»* | **No entra en la lista blanca** | Es qué contestar, no qué es cierto; y es la única superficie que controla alguien fuera del código, así que ensancharía la puerta desde el teclado |
| *«`JPV_RAG_LLM_*` ya existen, reutilizables»* | **Modelo propio; clave propia con repliegue** | `JPV_RAG_LLM_MODEL` es el de enriquecimiento y **no se lee**: heredarlo movería un modelo de mostrador cuyas cifras se midieron sobre otro. `JPV_ASSIST_LLM_API_KEY` separa gasto, cupo y rotación, pero es **opcional y se repliega a `JPV_RAG_LLM_API_KEY`** —exigirla habría dejado de generar a un despliegue existente el día que apareció el campo, y en silencio, porque la ruta degrada a 200 sin prosa en vez de fallar—. Cuál está en vigor se registra una vez, `stage=assist_client credential=assist\|rag_fallback`, así que «tenemos credenciales separadas» es comprobable y no supuesto. Degradar exige por tanto que **falten las dos** |

### 10.6. Una corrección de este mismo informe, sobre Terraform

La primera redacción del informe de implementación decía que llevar la credencial a la demo vivía en `terraform/`. **Es falso**, comprobado sobre el árbol: el rol de instancia ya lee **todo el prefijo** `/jbg-demo/` —sin cambio de IAM— y los secretos **no se declaran en Terraform a propósito**, porque un valor pasado a Terraform acaba en claro en el fichero de estado. Lo que falta son cuatro pasos en `deploy/demo/` y `compose.demo.yaml`, detallados en [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md).

Comprobado además que **la demo no genera hoy**: `compose.demo.yaml` no pasa ninguna credencial de proveedor al contenedor, así que sirve la respuesta de C30a con 200 — el comportamiento declarado, no un fallo.

---

## 11. Lo que esta pasada **no** verifica, dicho aquí

- **La fidelidad semántica.** Que un fragmento citado **diga** lo que la frase afirma no lo comprueba ninguna de las tres puertas. Es la *alucinación con coartada*, está **declarada como requisito en la capability** con esas palabras, y se mide con RAGAS en **C38**. No hay juez en el camino del mostrador.
- **La calidad de la prosa.** El barrido mide tasa de rechazo por causa, coste, latencia y longitud. **No** mide si el argumentario vende.
- **La latencia de producción.** Las cifras del §3.4 están tomadas desde una máquina de desarrollo en España, secuencialmente, a través de un interceptor TLS. Son una **cota superior** de la latencia del proveedor, y por eso el *timeout* pasó a ser ajustable.
- **`2 secciones / 2 materiales` no se recalibran.** El barrido mide y no decide: 1 sección rechaza mucho menos (12,5 % contra 55,0 %) y publica mucha más de la cita que ofrece (85,0 % contra 42,9 %), a cambio de la mitad del contexto. Es una decisión de producto con datos delante, y este change no la toma.
- **La atribución cruzada entre materiales que la pieza sí declara.** Heredada de C30a, mitigada por el tope y por la sección de piezas mixtas, declarada y no resuelta.
