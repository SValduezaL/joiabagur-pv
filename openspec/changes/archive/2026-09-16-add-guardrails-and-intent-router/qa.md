# QA — C31 `add-guardrails-and-intent-router`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** implementación y esta pasada, el **2026-09-15** · **Rama:** `c31-add-guardrails-and-intent-router` · **Artefactos de partida:** `e3f0403` · **Implementación: sin commitear al cerrar esta pasada** (53 rutas en `git status`).
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **48/48 tareas** y **18/18 casillas del DoD**. El grupo 8 —el argumentario de la consulta libre, que era la **línea de corte declarada**— **se entregó y se midió**, así que no se recortó nada.
> **Este change NO mueve la forma del contrato.** `openapi.json` se regenera por **tres descripciones**, y el §8 lo demuestra aplanando los dos documentos a hojas, no leyéndolos.
> **Lo que esta pasada encontró:** el **veto declarado antes de medir tumbó la primera configuración**, y llegar a una que pasara costó tres revisiones de prompt y un barrido de modelo; el **riesgo mayor declarado del change no se materializó ni una vez**; el criterio del veto **podía aprobar de forma vacía y aprobó**; y el test de la muestra de C30b **habría falsificado su propia procedencia**. Todo en el §10.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| PostgreSQL | `jpv-pv-postgres` (`pgvector/pgvector:pg15`) en el **5433**, con **1.168 productos activos con embedding** y **161 fragmentos de conocimiento**, para el barrido de la puerta numérica de M1 (§5); testcontainers efímero para los tests marcados `db` |
| Proveedor de LLM | **Llamado de verdad, y sólo fuera de la suite**: ~**1.063 llamadas** repartidas en 6 pasadas de enrutado (119 casos cada una) y 4 de la puerta de M1. **Ninguna corrida de tests lo llama** — §7 lo verifica |
| Proveedor de *embeddings* | Sólo el que la recuperación ya hacía, en el barrido de M1. Este change **no añade ninguna búsqueda vectorial** |
| TLS | `SSL_CERT_FILE` **y** `REQUESTS_CA_BUNDLE` a un PEM del almacén de Windows concatenado con `certifi` — **132 certificados añadidos**, sin filtrar por la bandera de confianza. Sin esto ninguna llamada real funciona en esta máquina |
| Bucle de eventos | `WindowsSelectorEventLoopPolicy` en el *runner* de la puerta de M1, que abre el motor asíncrono. `psycopg` rechaza el `ProactorEventLoop` |
| .NET | **no ejecutado, y a propósito**: el diff no toca `backend/` en absoluto. §7 lo demuestra |
| Frontend | **no ejecutado**: el diff no toca `frontend/`. §7 lo demuestra |
| Contrato | `ai-service/openapi.json` regenerado con `canonical_openapi_settings()`. Verificado **aplanando los dos documentos a hojas** (§8) |
| Migraciones | **ninguna**. `alembic heads` → **`d7c4e91b25a0`**, la misma revisión que antes del change y la misma que dejó C30b |
| Congelados | `git status` **vacío** en `retrieval/`, `enrichment/`, `knowledge/`, `indexing/`, `migrations/`, `backend/`, `frontend/`, `terraform/`, `.github/`, `data/knowledge/` y **`prompts/assist/v1.md`** |

---

## 1. Suites automáticas

La línea base se midió **antes de tocar una línea de código**, sobre el árbol limpio en `e3f0403`, que sólo contenía los cuatro artefactos del change. `git status --porcelain` respondió vacío, que es la condición correcta de línea base — **no hizo falta `git stash`**, y por eso no se usó.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`e3f0403`, árbol limpio) | **1320 passed**, 0 failed, 0 skipped, 127,2 s |
| `ai-service` tras cablear enrutador y guardarraíles | **1315 passed, 5 failed** — los cinco, consecuencia esperada del change (§1.2) |
| `ai-service` tras reconciliar los cinco | **1390 passed**, 0 failed, 218,5 s |
| `ai-service` al cierre de la implementación | **1415 passed**, 0 failed, 291,3 s |
| **`ai-service` tras la pasada de verificación** (§13) | **1418 passed**, 0 failed, 116,4 s |
| `openspec validate --all --strict` antes y después | **58 passed, 0 failed** en las dos puntas |
| `openspec validate add-guardrails-and-intent-router --strict` | `Change 'add-guardrails-and-intent-router' is valid` |
| `dotnet test` · `npm run test` al cierre | **no ejecutados**: fuera del diff. Ver §7 |

### 1.1. La comparación por nombres, que es la que vale

`CLAUDE.md` y la tarea 1.1 exigen comparar por **nombres de test** y no por recuento. Se capturaron
los *node id* de las dos puntas con `pytest --collect-only -q`, ordenados, y se compararon con
`comm`.

```
ANTES    1320 passed | rojo 0 | skipped 0
DESPUES  1415 passed | rojo 0 | skipped 0

Nombres en rojo NUEVOS  (después − antes) : NINGUNO
Nombres en rojo IDOS    (antes − después) : NINGUNO

Node id NUEVOS     :  99
Node id DESAPARECIDOS:  4   ← los cuatro, renombrados con sucesor
```

El conjunto en rojo es **vacío en las dos puntas**, así que el criterio se cumple de la forma más
fuerte posible. La suite de `ai-service` **no** es la de `backend/` ni la de `frontend/`, que
`CLAUDE.md` advierte que llegan en rojo: ésta llega en verde, así que **rojo habría sido mío**.

### 1.2. Los cuatro node id desaparecidos, y por qué ninguno es una pérdida

**Ningún test se borró.** Los cuatro afirmaban una propiedad que este change **invierte a
propósito**, y los cuatro tienen sucesor nombrado que afirma la propiedad nueva:

| Retirado | Sucesor | Qué afirmaba, y por qué deja de ser cierto |
|---|---|---|
| `test_warning_vocabulary_holds_exactly_two_codes` | `test_warning_vocabulary_holds_the_two_rule_codes_and_the_three_of_the_router` | el vocabulario de avisos estaba cerrado **en dos**; C31 le apila tres, y el sucesor comprueba que **los dos de C30a siguen primero e intactos** |
| `test_the_intent_vocabulary_has_exactly_two_members` | `test_the_intent_vocabulary_gained_the_routing_verdicts_and_kept_the_piece_anchored_one` | `ASSIST_INTENTS` tenía **dos**; ahora cinco, y el sucesor comprueba que `modes.py` **sigue derivando sólo dos** — los tres veredictos son inalcanzables sin clasificador |
| `test_the_free_query_mode_has_no_task_block_at_all` | `test_a_free_query_mode_cannot_pick_a_task_without_a_decided_route` | el modo de consulta libre **no tenía bloque de tarea**; ahora tiene tres, uno por ruta. **Sigue lanzando `ValueError`**, y ahora por la razón contraria: hay tres candidatas y el modo solo no elige |
| `test_the_prompt_file_carries_one_system_block_and_one_task_per_anchored_mode` | `test_the_prompt_file_carries_one_system_block_and_one_task_per_task_value` | dos tareas; ahora **seis**, y el sucesor comprueba que el bloque de sistema **sigue siendo exactamente uno** |

Mismo gesto que C26, C30a y C30b hicieron con sus 501 y con sus «no se llama al proveedor»: la
propiedad no se pierde, **se condiciona**, y el sucesor la sigue afirmando.

### 1.3. Desglose de los 99 nuevos, y la aritmética cierra exacta

Medido sobre el diff de *node id*, no sobre una tabla escrita a mano:

| Fichero | Nuevos | Qué cubre |
|---|---|---|
| `tests/assist/test_routing.py` | **33** | vocabulario cerrado por `Literal`, consulta como dato, prompt y su procedencia, plantillas de repregunta, *fail-open* con sus causas, techo derivado |
| `tests/assist/test_guardrails.py` | **27** | los guardarraíles cableados: dos rechazos, repregunta, M2/M3 sin clasificador, cobertura de M3, rutas, lista blanca de M1, *fail-open*, techo de 3 |
| `tests/evals/test_routing_cases.py` | **23** | manifiesto de 119 casos, proyección a clases, matriz, las dos cifras, el veto y su **cobertura** |
| `tests/assist/test_prompt.py` | **6** | versión↔fichero, conservación de `v1`/`v2`, seis tareas, resolución por ruta |
| `tests/api/test_assist_generation.py` | **5** | cadena de credencial router→assist→rag, modelo y *timeout* propios, log sin clave |
| `tests/api/test_assist_contract.py` | **4** | sólo descripciones, vocabulario de `intent`, `clarification_question` |
| `tests/assist/test_modes.py` | **1** | el vocabulario cerrado, ampliado |
| | **99** | = 1415 − 1320 + 4 renombrados ✓ |

---

## 2. La puerta de entrada (grupo 1)

| Tarea | Comprobación | Resultado |
|---|---|---|
| 1.1 | Línea base por **nombres** con el árbol limpio | **1320 passed / 0 failed**, node id guardados |
| 1.2 | `openspec validate --all --strict` antes de tocar nada | **58 passed, 0 failed** |
| 1.3 | `evals/routing/cases.yaml` carga y sus **cinco referencias resuelven** | ✅ — ver abajo |

La carga del manifiesto resuelve las cinco clases referenciadas contra el árbol vivo y **falla si
los recuentos declarados no cuadran** con los reales, como hace el golden set:

```
version 1  ·  total 119
  ambiguous             4  (declarado 4)
  both                 10  (declarado 10)
  catalog              48  (declarado 48)
  knowledge            32  (declarado 32)
  not_in_catalogue     20  (declarado 20)
  out_of_domain         5  (declarado 5)

catalog por categoría: descripcion-sin-anclaje 12 · variante-talla 7 · sinonimos 6 ·
                       materiales 5 · subjetiva 5 · sustituto 5 · piedra 4 · lexico-exacto 4
```

Y la negativa está probada: un manifiesto que declara 99 donde hay 4 **no carga**, y el error
nombra la clase, lo declarado y lo real (`test_a_declared_count_that_does_not_match_the_tree_refuses_the_load`).

---

## 3. La medición del enrutador: seis pasadas, 119 casos cada una

**Ninguna se borra.** Las cifras de una versión que fracasa son lo que hace repetible la decisión
de sustituirla.

| run | prompt | modelo | `catalog` | falso positivo | silenciadas | degradadas | veto |
|---|---|---|---|---|---|---|---|
| [`426a70070ad3`](../../../../ai-service/evals/results/c31-routing-confusion-426a70070ad3.md) | `router/v1` | `gpt-4o-mini` | 47,9 % | 31,25 % | **15** | 0 | **NO PASA** |
| [`de9297ad6515`](../../../../ai-service/evals/results/c31-routing-confusion-de9297ad6515.md) | `router/v2` | `gpt-4o-mini` | 79,2 % | 8,33 % | **4** | 22 ⚠ | **NO PASA** |
| [`e36e4b0196df`](../../../../ai-service/evals/results/c31-routing-confusion-e36e4b0196df.md) | `router/v3` | `gpt-4o-mini` | 81,3 % | 6,25 % | **3** | 0 | **NO PASA** |
| [`88de06b89194`](../../../../ai-service/evals/results/c31-routing-confusion-gpt4o-88de06b89194.md) | `router/v3` | `gpt-4o` | — | — | 0 | **89** ⚠ | *pasada rota, §10.3* |
| [`0d9f3fd1492a`](../../../../ai-service/evals/results/c31-routing-confusion-gpt4o-0d9f3fd1492a.md) | `router/v3` | `gpt-4o` | 81,3 % | 0,00 % | 0 | 26 ⚠ | **NO PASA** (cobertura) |
| **[`2b5b98c81e28`](../../../../ai-service/evals/results/c31-routing-confusion-gpt4o-2b5b98c81e28.md)** | **`router/v3`** | **`gpt-4o`** | **100 %** | **0,00 %** | **0** | **0** | **PASA** |

> Las pasadas marcadas ⚠ degradaron por **`RateLimitError` del proveedor**, no por el
> clasificador. Se repitieron a concurrencia 1 y con pausa hasta obtener **cobertura completa**;
> el arnés reintenta el límite de tasa y **nunca un fallo de parseo**, que es la degradación que
> se está midiendo (`test_the_harness_retries_a_rate_limit_and_never_a_parse_failure`).

### 3.1. La matriz publicada — `router/v3` sobre `gpt-4o`, 0 degradaciones

| esperada \ predicha | `catalog` | `knowledge` | `both` | `ambiguous` | `not_in_catalogue` | `out_of_domain` | n | acierto |
|---|---|---|---|---|---|---|---|---|
| `catalog` | **48** | 0 | 0 | 0 | 0 | 0 | 48 | **100 %** |
| `knowledge` | 1 | **28** | 3 | 0 | 0 | 0 | 32 | 88 % |
| `both` | 2 | 0 | **8** | 0 | 0 | 0 | 10 | 80 % |
| `ambiguous` | 0 | 0 | 0 | **4** | 0 | 0 | 4 | **100 %** |
| `not_in_catalogue` | 0 | 0 | 0 | 0 | **20** | 0 | 20 | **100 %** |
| `out_of_domain` | 0 | 0 | 0 | 0 | 1 | **4** | 5 | 80 % |

Por categoría del golden set dentro de `catalog`, **las ocho perfectas**, incluidas las doce que
el veto protege: `descripcion-sin-anclaje` 12/12, `variante-talla` 7/7, `sinonimos` 6/6,
`materiales` 5/5, `subjetiva` 5/5, `sustituto` 5/5, `piedra` 4/4, `lexico-exacto` 4/4.

### 3.2. Las dos cifras separadas (tarea 10.3, HU escenario 15)

| cifra | valor | mecanismo |
|---|---|---|
| **Rechazo del enrutador** | **21,01 %** (25 de 119) | clasifica **antes** de recuperar |
| **Abstención del retriever** (C25, sin tocar) | **10 %** | lee el perfil de distancias **después** de recuperar |

El objeto publicado lleva `"summable": false` y la nota que lo explica; hay un test que lo lee
(`test_the_report_keeps_the_two_rates_apart_and_says_they_are_not_summable`). Las 25 rechazadas
son **exactamente** las 25 que había que rechazar.

### 3.3. El falso positivo sobre `catalog`, como cifra propia (tarea 10.4)

**0,00 %**, sobre **48 medidas y 0 degradadas**. Es una cifra propia y **no el complemento de
ningún acierto**: una consulta de `catalog` enviada a `knowledge` es un error de ruta que enseña
una explicación en vez de piezas —recuperable— y una **rechazada** no enseña nada.

### 3.4. El veto (D12, HU escenario 3)

```
Criterio: cero «descripcion-sin-anclaje» silenciadas; una sola tumba la configuración
Declarado antes de medir: True
PASA — 0 silenciadas, 48 medidas, 0 degradadas de la clase contestable
Degradaciones en toda la pasada: 0 de 119
```

---

## 4. Escenarios de la delta, uno a uno

**20 requisitos · 31 escenarios**: 17 `ADDED`, **2** `MODIFIED` y 1 `REMOVED`.

> **El segundo `MODIFIED` lo añadió el archivado, no la implementación.** La delta llegó al
> archivado con 19 requisitos y la evaluación de sincronización destapó una **contradicción que
> se habría escrito en la spec viva**: el requisito vivo *«Warnings are computed from rules and
> travel as a closed vocabulary of codes»* dice **«SHALL emit exactly two codes»**, y C31 lleva
> el vocabulario a **cinco**. Nadie lo habría visto: `openspec validate --all --strict` no lee
> coherencia semántica, y los tests afirman sobre la constante y no sobre la spec. Corregido
> **en la delta y no en la spec viva** —que es donde corresponde, porque la spec viva se deriva
> del change y no al revés—, con un párrafo que además exige que **los dos códigos de rechazo
> sigan siendo dos** y un quinto escenario que lo comprueba. Detalle en el §12.4.

### `assist-generation` — `ADDED`

| Requisito | Escenarios | Dónde se ejerce |
|---|---|---|
| El `intent` es veredicto en M1 y estructural en las ancladas | 2 | `test_a_piece_with_no_question_makes_no_classifier_call` · `test_a_catalogue_query_receives_an_argument_written_over_the_candidates` · `test_the_intent_vocabulary_gained_the_routing_verdicts_and_kept_the_piece_anchored_one` |
| Fuera de dominio se rechaza antes de recuperar | 1 | `test_an_out_of_domain_query_is_refused_before_anything_is_retrieved` — el índice **lanza** si se toca |
| Fuera de catálogo, rechazo con código **distinto** | 2 | `test_a_neighbouring_trade_request_is_refused_with_its_own_distinct_code` · `test_an_admitted_and_sufficient_query_carries_no_clarification` |
| Consulta insuficiente ⇒ repregunta, sin generar | 1 | `test_an_ambiguous_query_is_answered_with_a_question_and_no_candidates` |
| La repregunta sale de catálogo cerrado en código | 1 | `test_the_same_query_always_yields_the_same_clarification_text` (4 ejes) · `test_no_clarification_template_carries_a_figure` |
| El rechazo **nunca** reutiliza `abstained` | 2 | `test_a_refused_request_does_not_claim_to_have_abstained` · `test_an_abstained_request_still_declares_its_abstention` |
| M3 es `both` por construcción y no llama al clasificador | 1 | `test_an_anchored_question_consults_both_indexes_and_makes_no_classifier_call` |
| Pregunta sin cobertura ⇒ aviso, sin llamada extra | 1 | `test_an_uncovered_anchored_question_is_declared_and_costs_no_extra_call` · `test_a_covered_anchored_question_raises_no_coverage_warning` |
| M1 redacta sobre la ruta decidida | 1 | `test_a_knowledge_question_is_routed_to_the_corpus_and_shows_no_pieces` · `test_the_both_route_consults_the_two_indexes_and_uses_its_own_task` |
| Ninguna cifra ausente del contexto de M1 | 2 | `test_an_invented_figure_is_refused_in_the_free_query_mode_too` · `test_the_free_query_material_carries_no_internal_identifier_and_no_score` |
| Clasificador no disponible ⇒ `unclassified` y antes | 2 | `test_a_classifier_fault_serves_the_answer_the_capability_served_before_it_routed` (2 casos) · `test_no_classifier_credential_is_a_valid_deployment_state` |
| Techo de **3** llamadas | 2 | `test_a_routed_generated_and_repaired_request_makes_exactly_three_calls` · `test_an_unparseable_reply_is_not_retried` |
| La etiqueta se valida contra conjunto cerrado | 1 | `test_a_label_outside_the_closed_vocabulary_fails_the_parse` (5 casos) · `test_an_unknown_label_reaches_the_client_as_an_unparseable_reply` |
| La consulta viaja como dato también al clasificador | 1 | `test_an_instruction_shaped_query_does_not_change_the_classifier_system_message` |
| Las dos tasas se publican por separado | 1 | `test_the_report_keeps_the_two_rates_apart_and_says_they_are_not_summable` |
| El prompt del clasificador no sale de los conjuntos de evaluación | 1 | `test_the_classifier_prompt_declares_its_provenance_in_writing` · §9 de este informe |
| La versión nueva del prompt no pisa a la anterior | 1 | `test_the_previous_prompt_version_is_present_and_was_not_edited` · `test_every_assist_prompt_version_is_preserved_with_its_measurement` |

### `assist-generation` — `MODIFIED`: no se llama al proveedor cuando no hay sobre qué escribir (3)

| Escenario | Evidencia |
|---|---|
| Abstenida ⇒ sin llamada | `test_an_abstained_request_still_declares_its_abstention` — el cliente **lanza** si se le llama |
| Rechazada ⇒ sin llamada, `pitch` vacío y `prompt_version` nula | `test_an_out_of_domain_query_is_refused_before_anything_is_retrieved` |
| Repreguntada ⇒ sin llamada, `pitch` vacío y `prompt_version` nula | `test_an_ambiguous_query_is_answered_with_a_question_and_no_candidates` |

### `assist-generation` — `REMOVED`: «el intent se deriva de la forma y nunca se adivina»

El requisito se retira porque este change **entrega el clasificador cuya ausencia lo hacía
cierto**. Su mitad anclada se conserva **verbatim** en el requisito que lo reemplaza, y
`test_the_intent_vocabulary_gained_the_routing_verdicts_and_kept_the_piece_anchored_one` comprueba
que `modes.py` **sigue derivando exactamente dos valores** — la promesa del docstring de C30a,
*«ese router reemplazará a `unclassified`, nunca a `product_pitch`»*, cumplida literalmente.

---

## 5. La puerta numérica de M1, medida **aparte** (tarea 10.5)

Contra el **índice real**, con el enrutador real decidiendo la ruta, sobre las 90 consultas del
conjunto que pueden generar.

**Cuatro pasadas, y sólo la última se publica como tasa.** Las cuatro se conservan, por la misma
razón que las seis del enrutado:

| run | prompt | consultas | generadas | retiradas | estado |
|---|---|---|---|---|---|
| `ab3a0aaf0a44` | `assist/v2` | 4 | 4 | 4 | sonda; sin captura de causas |
| `ab6f3e56ead3` | `assist/v2` | 4 | 4 | **3** | sonda que **destapó `dangling_citation`** — recuento, no tasa |
| `2498116e6f5b` | `assist/v3` | 90 | 41 | 2 | **superseded**: 49 degradaciones del enrutador y el fallo de captura del §10.8 |
| **[`387fa94e792a`](../../../../ai-service/evals/results/c31-free-query-gate-387fa94e792a.json)** | **`assist/v3`** | **90** | **89** | **2** | **la publicada** — 0 degradaciones |

| | M2/M3 (C30b) | **M1 (C31)** |
|---|---|---|
| Generaciones medidas | 120 | **89 de 90** · 0 degradaciones del enrutador |
| Numerales de la lista blanca | ~4 (una pieza) | **13,0 de media, máximo 23** |
| Candidatos en el material | 1 | **9,4 de media, máximo 15** |
| **Violaciones de la puerta numérica** | **0** | **0** |
| Argumentario retirado | 0 | **2 de 89 — 2,25 %** |

**Cero.** Ni una `figure_not_in_context`, `currency_adjacent_figure`, `stock_adjacent_figure`,
`decimal_form` ni `enumeration_format`, con listas blancas tres veces más anchas que las de C30b.

Las dos retiradas, y una de ellas **no es de la puerta**:

| caso | tarea | lista blanca | causa | qué pasó |
|---|---|---|---|---|
| `b05` | `free_query_both` | 15 | `dangling_citation` | sobrevivió a la reparación — **la única retirada real: 1 de 89, 1,12 %** |
| `q11` | `free_query_catalog` | 5 | *ninguna* | el modelo devolvió `pitch` **vacío** que pasó las tres comprobaciones |

Y una tercera cifra que **no** es tasa de rechazo: `claim_not_in_pitch` apareció **30 veces en la
primera generación, 23 sobrevivieron** (25,8 %). Es una violación **blanda por política** —retira
**esa cita** y publica la prosa— y se publica como lo que es, no dentro del 2,25 %.

Reparto de rutas sobre las 90, decidido por el enrutador: `catalog` **50**, `knowledge` **28**,
`both` **11**, **0 degradaciones**.

---

## 6. Las validaciones que `tasks.md` exige, grupo a grupo

| Grupo | Qué exige | Resultado |
|---|---|---|
| **1** Puerta de entrada | línea base por nombres, validate, manifiesto | ✅ §1, §2 |
| **2** Vocabularios | 3 intenciones, 2 códigos de rechazo **distintos**, 1 de cobertura, constantes | ✅ `test_warning_vocabulary_holds_the_two_rule_codes_and_the_three_of_the_router` |
| **3** Prompt del clasificador | desde `vocabularies.yaml` y el README; declaración escrita; consulta delimitada | ✅ §9 · `test_the_classifier_prompt_names_the_twelve_closed_piece_types` |
| **4** Clasificador | `Literal`, costura replicada, una llamada sin reparación, 3 ajustes, log, perfil canónico | ✅ `test_the_classifier_client_is_its_own_class_and_pins_its_own_schema` |
| **5** Cableado | sólo M1, corte antes de recuperar, M2/M3 sin clasificador, rechazo, *fail-open*, techo 3 | ✅ §4 · los 27 de `test_guardrails.py` |
| **6** Repregunta | catálogo cerrado, determinismo, sin generación | ✅ 4 ejes × 2 ejecuciones |
| **7** Guardarraíl de M3 | cero citas ⇒ aviso sin llamada extra; tarea degradada | ✅ `provider.call_count == 1` en la pasada con corpus vacío |
| **8** Argumentario de M1 | *payload* propio, lista blanca sin ids ni scores, `v2` conservando `v1`, generación por ruta | ✅ §5 · **la línea de corte no se usó** |
| **9** Contrato | descripciones, regeneración, verificación hoja a hoja | ✅ §8 |
| **10** Evaluación | manifiesto que falla, matriz, dos cifras, falso positivo, M1 aparte, contraste, `run_id` | ✅ §3, §5, §11 |
| **11** Cierre | suite por nombres, validate, `DEFERRED_TASKS`, informe, docs, fichas | ✅ §1 · `DEFERRED_TASKS.md` · [informe](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c31-implementation-measurements.md) |

---

## 7. Alcance negativo, demostrado

`git status --porcelain -- <ruta>` **vacío** en todas:

| Ruta | Estado |
|---|---|
| `ai-service/src/jbg_ai/retrieval/` | **0 cambios** — la abstención de C25 no se toca ni se recalibra |
| `ai-service/src/jbg_ai/enrichment/` | **0 cambios** — `vocabularies.yaml` **sólo se lee** |
| `ai-service/src/jbg_ai/knowledge/` | **0 cambios** — el guardarraíl de M3 se construye **sobre** `search_knowledge`, no dentro |
| `ai-service/src/jbg_ai/indexing/` | **0 cambios** |
| `ai-service/migrations/` | **0 cambios** · `alembic heads` → `d7c4e91b25a0`, sin mover |
| `ai-service/prompts/assist/v1.md` | **0 cambios** — y un test lo fija sección a sección |
| `data/knowledge/` | **0 cambios** — el corpus **sólo se lee** |
| `backend/` · `frontend/` · `terraform/` · `.github/` | **0 cambios** |

**Sin llamadas reales en la suite.** `test_the_assist_package_imports_no_provider_client` sigue
verde, y los clientes nuevos importan `litellm` **dentro** de la llamada, igual que los de C30b y
C09. Los tests conducen el **cliente real** sobre un `complete` guionizado
(`support/assist_router.py`), así que se ejercitan el parseo, la validación del conjunto cerrado,
el *timeout* y la extracción de coste reales — sólo se sustituye el socket.

**Sin TODO/FIXME** en el código nuevo (`grep` sobre `assist/`, `evals/routing*.py`,
`evals/free_query_gate.py` y los prompts nuevos): ninguno.

---

## 8. El contrato, y exactamente qué se movió

Aplanados los dos `openapi.json` a **hojas** (cada valor escalar con su ruta completa) y
comparados uno a uno. **No leídos a ojo**, que es lo que el innegociable nº 6 prohíbe:

```
hojas: 1102 -> 1103
AÑADIDAS  1 : components.schemas.AssistResponse.properties.clarification_question.description
RETIRADAS 0 : []
CAMBIADAS 2 : [DESCRIPCION] components.schemas.AssistResponse.properties.intent.description
              [DESCRIPCION] components.schemas.AssistResponse.properties.warnings.description
tipos idénticos    : True  (346 hojas)
required idénticos : True  (125 hojas)
VERIFICADO: sólo descripciones.
```

La única hoja «añadida» es una clave `description` sobre un campo **que ya existía y no la tenía**.
**Ningún campo se añade, se retira ni cambia de tipo.** El diff de git son **3 líneas**, que es
exactamente por qué leerlo a ojo no habría bastado.

Un test permanente fija la mitad que una suite puede seguir comprobando
(`test_the_router_added_no_field_and_changed_no_type`): `intent` sigue siendo `string` plano,
`warnings` un `array` de `string`, `clarification_question` una prosa opcional, y **no existen**
`refusal_reason`, `route` ni `missing_axis` en la respuesta.

`test_openapi_snapshot_is_stable` verde.

---

## 9. Los siete innegociables, verificados

| # | Innegociable | Verificación |
|---|---|---|
| **1** | Cero `descripcion-sin-anclaje` silenciadas | **0 de 12**, con cobertura completa. La configuración que lo incumplía (`gpt-4o-mini`) **fue rechazada y no se sirve** |
| **2** | `abstained` **no** se reutiliza | `test_a_refused_request_does_not_claim_to_have_abstained` (2 veredictos) y `test_an_abstained_request_still_declares_its_abstention`. Los dos sentidos |
| **3** | Prompt escrito **antes** de abrir los ficheros de evaluación | **El orden lo garantiza:** `prompts/router/v1.md` y `prompts/assist/v2.md` se escribieron antes de la primera lectura de `queries.jsonl` y `cases.yaml`. Declarado en los tres ficheros de prompt, en el informe y en un test |
| **4** | Techo literal de **3** llamadas, sin reintento ni reparación del clasificador | `MAX_PROVIDER_CALLS` **derivado** (1 + 2), aserción en el orquestador, `test_an_unparseable_reply_is_not_retried` y `test_a_routed_generated_and_repaired_request_makes_exactly_three_calls` |
| **5** | *Fail-open* como **rama con test**, nunca un `except` mudo | `RoutingOutcome.degraded_cause` es `None` exactamente cuando hubo decisión; 4 causas parametrizadas + `timeout` + `absent`, cada una con su test, y la causa en el log |
| **6** | `openapi.json` sólo en descripciones, **verificado aplanando** | §8 — 0 añadidos, 0 retirados, 0 tipos, 346 hojas de `type` y 125 de `required` idénticas |
| **7** | Nada se persiste; el log no lleva la consulta | Sin migración, sin tabla. `test_the_degradation_is_logged_with_its_cause_and_without_the_query` y `test_the_degradation_and_its_cause_reach_the_request_log` **buscan el texto de la consulta en lo emitido y exigen no encontrarlo** |

### La declaración de D11, por escrito

**El prompt del clasificador se redactó desde `enrichment/vocabularies.yaml` y la documentación
del corpus, y no desde las anotaciones de los conjuntos de evaluación.** En concreto:

- **No se abrieron** los campos `note` de `evals/golden/queries.jsonl` ni los `why` de
  `evals/routing/cases.yaml` antes de escribir `prompts/router/v1.md`. Los dos llevan la regla de
  clasificación escrita con todas sus letras —*«lo que guarda las joyas, no una joya»*—.
- **El orden de trabajo fue el mecanismo**, no la voluntad: es una puerta de un solo sentido y no
  hay forma de deshacerla.
- Las revisiones **v2 y v3 se escribieron desde las mismas fuentes**, ampliadas con los **nombres
  de producto del propio catálogo** (`data/catalog/real/`), que son catálogo y no anotación. Lo
  que se miró para decidir que hacían falta fue **qué clases fallaban y con qué etiqueta**, que es
  para lo que existe una medición.
- **La declaración viaja en los tres ficheros de prompt**, no sólo aquí, y hay un test que lo
  comprueba versión a versión.

---

## 10. Incidencias de esta pasada

### 10.1. El veto tumbó la primera configuración, y eso es el veto funcionando

`router/v1` silenciaba **15 de 48** consultas contestables, diez de ellas `descripcion-sin-anclaje`,
con un falso positivo del **31,25 %**. Es el riesgo que la ficha declaraba como principal,
ocurriendo. Y con las veinte imposibles capturadas al 95 %, **la tentación de llamarlo
«suficientemente bueno» estaba servida** — que es exactamente para lo que el criterio se declaró
antes de medir.

### 10.2. Lo que fallaba no era clasificar intención, sino no saber cómo se nombra el catálogo

Las diez silenciadas son del mismo tipo: `la lagartija que toma el sol en las paredes`, `el fruto
de la encina`, `el bicho con puas que se pisa en las rocas`. Leído el catálogo real:

```
SKU01  Pendientes botón erizo de mar mini     SKU102 Anillo caracola
SKU06  Colgante erizo de mar S                SKU107 Colgante cono de mar oro
```

**Las piezas se llaman `<tipo> <motivo>`.** Una consulta que describe una cosa **es** una consulta
de catálogo, porque pide la pieza que la representa. La distinción fina que la ficha no veía no es
*intención contra cobertura* sino **artículo de otro oficio contra motivo de éste**, y la regla que
la corta es negativa: `not_in_catalogue` es una lista corta de cosas que alguien compra de verdad
en una joyería, y **nadie entra en una joyería a comprar una bicicleta**.

### 10.3. El veto podía aprobar de forma vacía, y aprobó

Una pasada de `gpt-4o` con 89 de 119 casos muertos por límite de tasa informó **«PASA — 0
consultas contestables silenciadas»**. Correcto por construcción y falso como criterio: un caso
que no se clasificó **no es un rechazo**.

`veto.passed` ahora exige **cobertura completa sobre la clase contestable**, el informe publica las
degradaciones de toda la pasada, y `test_a_run_that_degraded_cannot_pass_the_veto` lo fija.
**Un criterio que una pasada rota satisface no es un criterio**, y esto no estaba en ningún
artefacto del change.

### 10.4. El riesgo mayor declarado no se materializó, y el que tumbó M1 era otro

La lista blanca numérica de M1 resultó de **~13 numerales y no de cinco** —`top_k=5` cuenta
familias tras hidratar y la recuperación devuelve **15 candidatos**— y la puerta numérica rechazó
**cero**. Lo que retiraba el argumentario —**3 de 4** en la sonda de cuatro consultas que lo
destapó; recuento y no porcentaje, porque cuatro casos no sostienen una tasa— era
`dangling_citation`: la ruta `catalog`
entrega candidatos y una lista `corpus` **vacía**, y el modelo declaraba citas igualmente, porque
la sección de tarea **no las mencionaba** y la regla invariante «puedes no citar nada» **permite
sin obligar**. Corregido en `prompts/assist/v3.md`; `v2.md` se conserva con su recuento medido.

### 10.5. La primera llamada de un proceso paga el `import litellm` dentro de su propio *timeout*

Medido: los **dos primeros** casos de una pasada agotaron **20 s** por eso y por nada más. Con el
corte de servicio en 2 s, **la primera consulta libre tras un arranque en frío degrada** — cae en
el *fail-open*, que es correcto, pero es evitable calentando el import al arrancar. Fuera de
alcance aquí; anotado en `DEFERRED_TASKS.md`.

### 10.6. El test de la muestra de C30b habría falsificado su propia procedencia

`evals/assist/sweep-sample.yaml` declara `prompt_version: assist/v1` porque **es la versión contra
la que se midieron las 120 generaciones de C30b**, y su test lo comparaba contra la constante del
código. Al mover la constante, el test falla y **la reparación obvia —actualizar el fichero—
falsificaría una medición ya publicada**, que es exactamente lo que D10 existe para impedir,
llegando por la dirección que nadie había previsto. El test fija ahora la versión histórica
literalmente y comprueba que **difiere** de la actual.

### 10.8. Un fallo de instrumentación del arnés, y era mío

La primera pasada completa de la puerta de M1 leía `captured[-1]` sin comprobar si **esa** consulta
había generado algo, así que a una petición que no generó le atribuía la tarea, la lista blanca y
las causas de **la anterior**. Se leía como 54 generaciones de `catalog` donde había 24. Corregido
comparando la longitud de la captura antes y después de servir, y la pasada se repitió entera: la
publicada (`387fa94e792a`) tiene **0 degradaciones del enrutador** y la atribución correcta.

Es el mismo tipo de defecto que C30b encontró en su propia métrica de *timeout*: el arnés medía
algo distinto de lo que decía medir, y sólo se ve releyendo lo que se publica.

### 10.9. Una corrección de este mismo informe, sobre el 75 %

La primera redacción publicaba **«75 % de rechazo»** para `assist/v2` en tres sitios —el propio
prompt, el informe y este documento— **a partir de una sonda de cuatro consultas**. Tres de cuatro
es un recuento que basta para localizar una causa y **no** para publicar una tasa, y presentarlo
como porcentaje le daba un peso que la muestra no sostiene. Corregido a recuento en los tres.

### 10.7. Lo que la implementación refuta de los artefactos, y qué se enmendó

| Artefacto | Qué decía | Qué se midió | Enmienda |
|---|---|---|---|
| `ticket.md`, pregunta abierta 4 | «mismo `gpt-4o-mini` de partida» | `gpt-4o-mini` **falla el veto**; `gpt-4o` lo pasa con 48/48 | Fila nueva en el **Historial de Cambios** |
| `design.md`, riesgo de la lista blanca | «cinco candidatos aportan cinco SKU» | **15 candidatos, ~13 numerales**, y **0 violaciones** | Párrafo de medición en el propio riesgo |
| `design.md`, pregunta abierta 4 | punto de partida `gpt-4o-mini` | movido por medición | Nota «Amended by the implementation» |
| `DEFERRED_TASKS.md` | — | la configuración vetada no puede desplegarse | Entrada nueva con la tabla y el aviso |

Las **deltas de spec no se tocan**: siguen describiendo con exactitud lo implementado, y
`openspec validate --all --strict` sigue en **58 passed / 0 failed**.

---

## 11. El contraste enrutador ↔ umbral `0,51` (tarea 10.6, D3)

C23 fijó el umbral sobre un **hueco limpio de 8 milésimas** y su propio informe advirtió de que el
margen es estrecho *«y por construcción»*. El enrutador da una segunda opinión **independiente**:

| | umbral `0,51` (C23) | enrutador (`gpt-4o`) |
|---|---|---|
| 32 preguntas que el corpus responde | 32 por debajo (**100 %**) | **32 admitidas**, 0 rechazadas |
| 5 preguntas de fuera | 5 por encima, 0 citas (**0 %**) | **5 rechazadas**, 0 admitidas |

**Discrepancias sobre el eje servir / no servir: 0 de 37.** Dos mecanismos que no comparten ni
entrada ni método coinciden por completo, que es la evidencia más fuerte disponible de que aquel
margen separa algo real.

Donde difieren es en el **grano**, y eso es información nueva: de las 32 que el umbral trata como
una sola clase, el enrutador manda 28 a `knowledge`, 3 a `both` y 1 a `catalog`; y de las 5 de
fuera distingue **4 `out_of_domain` de 1 `not_in_catalogue`**, una distinción que el umbral no
puede hacer porque sólo sabe decir «ninguna cita».

---

## 12. La pasada de verificación, y los tres defectos que encontró

Ejecutada **después** de commitear la implementación (`a74f7ad`), releyendo las deltas requisito a
requisito contra el código en vez de contra la memoria. Encontró tres cosas, y las tres son mías.

### 12.1. Dos dobles de test que no podían fallar — **CRÍTICO**

`test_guardrails.py` afirmaba «no se ejecuta ninguna recuperación» con dobles que sobreescribían
métodos que **la producción nunca llama**:

| doble | sobreescribía | lo que de verdad se invoca | efecto |
|---|---|---|---|
| `_refusing_knowledge` | `search` | `vector_search`, `lexical_search`, `fetch_chunks` | **totalmente vacío** — y el índice iba vacío, así que el test pasaba por la razón equivocada |
| `_refusing_search` | `search` ✅ y `lexical_search` ❌ | `search` y **`search_lexical`** | la mitad del guardián era un *no-op* |

**Un doble que no puede fallar es peor que no tener doble**: hace que cada test que lo usa pase
por el motivo equivocado, y nada lo reporta. Corregidos los dos por el nombre real, y añadido
**`test_the_refusing_doubles_actually_refuse`**, que conduce cada doble por la llamada exacta que
hace la producción y **exige que levante**. Si alguien renombra un método del puerto, falla ahí en
vez de desarmar en silencio cuatro tests de guardarraíl.

**Los 30 tests de `test_guardrails.py` siguen verdes con los dobles ya armados**, así que la
propiedad —el corte ocurre *antes* de las dos recuperaciones— queda **probada** y no supuesta.

### 12.2. Dos escenarios de la delta sin cobertura literal — **WARNING**

| Escenario | Qué faltaba | Test añadido |
|---|---|---|
| «A label outside the vocabulary never reaches the response» | la mitad «degrada a `unclassified`» estaba; la mitad **«la etiqueta desconocida no aparece en la respuesta»** no | `test_an_unknown_label_never_appears_anywhere_in_the_response` — comprueba sobre el **volcado entero**, no sobre `intent` |
| «The reported value MUST belong to a closed vocabulary» | nadie recorría los siete caminos | `test_the_reported_intent_always_belongs_to_the_closed_vocabulary` — tres veredictos, repregunta, *fail-open* y los dos modos anclados, y además comprueba que **los cinco valores son alcanzables**: ninguno es decorativo |

### 12.3. `proposal.md` decía `assist/v2` — **SUGGESTION, enmendado**

Era el único artefacto que aún nombraba v2 como la versión servida. Enmendado con la misma nota
que `design.md` y `ticket.md` ya llevaban.

### 12.4. Una contradicción que la delta habría escrito en la spec viva — **CRÍTICO, corregido**

Encontrada en la **evaluación de sincronización del archivado**, no antes. El requisito vivo
*«Warnings are computed from rules and travel as a closed vocabulary of codes»* declara:

> This capability SHALL emit **exactly two codes**: one stating that the product's family holds
> other members, and one stating that the product declares no size label.

C31 lleva `ASSIST_WARNING_CODES` a **cinco** y la delta **no modificaba ese requisito**. Sin
corregirlo, el sync habría dejado la spec viva afirmando «exactamente dos» en un requisito y
enumerando cinco en otro y en el `## Purpose`.

**Nada lo habría detectado.** `openspec validate --all --strict` comprueba la estructura, no la
coherencia semántica; y los tests afirman sobre `ASSIST_WARNING_CODES`, que es la constante, no
sobre lo que la spec dice de ella. Es exactamente la forma de deriva que `CLAUDE.md` describe
—una spec viva que se contradice y valida igual— y por eso el archivado **sí** evalúa el sync
antes de aplicarlo en vez de copiar ficheros.

**Corregido en la delta y no en la spec viva**, que es donde corresponde: la spec viva se deriva
del change, no al revés. La delta gana un segundo `MODIFIED` que lleva el requisito a cinco
códigos, añade un párrafo exigiendo que **los dos de rechazo sigan siendo dos** —lo que la spec
sólo decía en el requisito de la puerta de cobertura— y un quinto escenario que lo comprueba. La
delta pasa de 19 a **20 requisitos** y de 26 a **31 escenarios**.

### Lo que la verificación comprobó y estaba bien

- Los **17 requisitos `ADDED`** no chocan con ninguno de la spec viva; el `MODIFIED` y el
  `REMOVED` **existen** en ella, así que el archivado posterior encajará.
- Las **doce decisiones D1-D12** se siguen en el código, incluida D9 —cliente cacheado en
  `app.state`, así que el log de credencial sale **una vez por proceso** y no por petición—.
- `alembic heads` sin mover, congelados sin tocar, `openapi.json` sólo en descripciones.

---

## 13. Lo que esta pasada **no** verifica, dicho aquí

- **Fidelidad semántica (`faithfulness` / RAGAS).** Fuera de alcance por ficha: es **C38**. Las
  tres comprobaciones confirman que la fuente existía, que la cita se usó para algo escrito y que
  ninguna cifra se inventó — **no** que el fragmento *diga* lo que la frase afirma.
- **Casos adversarios y de inyección sistemáticos.** Son **C38** (20-25 casos). Aquí se comprueba
  la mitigación estructural sobre la llamada nueva, no un conjunto adversario.
- **La pantalla del rechazo y de la repregunta.** M1 no tiene ruta .NET ni superficie: anotado en
  las fichas de **C34** y **C36**.
- **La latencia del enrutador en el despliegue.** `JPV_ROUTER_TIMEOUT_SECONDS` queda **declarado
  no calibrado** y deliberadamente **fuera** de los pasos de despliegue hasta que la demo mida su
  propia distribución.
- **La cifra final del enrutador es dentro de muestra.** Tres revisiones de prompt y un barrido de
  modelo se decidieron mirando resultados sobre este mismo conjunto, y la partición de ajuste del
  golden set —8 consultas, sólo una de `descripcion-sin-anclaje`— es demasiado pequeña para
  sostener una lectura retenida. **Se dice en vez de disimularse.** Lo que **no** queda
  contaminado es el **veto**: es un criterio de rechazo declarado antes de medir, y una
  configuración que lo falla sigue rechazada por muchas iteraciones que se hayan hecho.
- **`dotnet test` y `npm run test`.** No ejecutados porque el diff no toca `backend/` ni
  `frontend/`, y el §7 lo demuestra en vez de afirmarlo.
