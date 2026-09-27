# QA — C24 `add-eval-harness-golden-set-and-baselines`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fechas:** implementación y medición el **2026-09-07**; esta pasada de QA, el **2026-09-11** · **Rama:** `c24-eval-harness-golden-set-and-baselines` · **Commit de artefactos:** `a03b4ad` · **Implementación:** en árbol de trabajo, sin commitear al cierre de esta pasada
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **84/84 tareas**. Las de medición (§7, §8, §9, §11, §13) se ejecutaron **contra el índice real y el proveedor real**, que es la primera regla que este change heredó de C23: un sustituto *offline* no puede arbitrar un pleito entre una rama léxica y una vectorial, porque **es** una de las partes.
> **Dos desviaciones declaradas en los artefactos**, ambas ejecutadas: el desempate determinista en ruta viva (§7, D2) y el cambio condicional de defaults, que **la regla no disparó** (§8.2).
> **Dos desviaciones más, abiertas durante el apply** y no previstas por los artefactos: el denominador acotado de `Recall@5` y las respuestas declaradas fuera del *pool*. Ver §9.3 y §9.4.
> **Lo que esta pasada de QA encontró y arregló:** tres huecos que sólo aparecen al recorrer los escenarios uno a uno, y una inconsistencia de cifras entre dos informes. Ver §9.10 a §9.13.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| PostgreSQL | `jpv-pv-postgres` (`pgvector/pgvector:pg15`) en el 5433, con **1.168 documentos vivos**, para el *pool*, la corrida y la migración; testcontainers efímero, base nueva por test, para los 17 tests `db` |
| Proveedor de embeddings | **`openai/text-embedding-3-small`, real**, usado **una sola vez** para congelar los 48 vectores de consulta y una vez más para medir su latencia. Ninguna corrida de evaluación lo llama |
| Proveedor de LLM | **`openai/gpt-4o-mini`, real**, 12 llamadas, sólo para `v0-cag`. Coste total del change: céntimos |
| TLS | `SSL_CERT_FILE` **y** `REQUESTS_CA_BUNDLE` apuntando al PEM de raíces de Windows concatenado con `certifi`. El segundo hace falta y no estaba previsto: ver §9.8 |
| .NET | **no ejecutado, y a propósito**: el diff no toca `backend/`, y §5 lo demuestra |
| Frontend | **no ejecutado**, por lo mismo |
| Contrato | `ai-service/openapi.json` **no se mueve**. Comprobado por **regeneración en memoria**, no por inspección (§6) |
| Freeze C11 | `git diff -- ai-service/src/jbg_ai/indexing/embeddings.py` **vacío** |
| Diccionario C20 | `git diff -- ai-service/src/jbg_ai/retrieval/{synonyms.py,query_synonyms.yaml}` **vacío**. Se **importa**, nunca se edita |
| Umbral de distancia | `JPV_RETRIEVAL_DISTANCE_THRESHOLD` **sin tocar**, por D8. Este change publica su distribución; re-fijarlo es C25 |

---

## 1. Suites automáticas

La línea base se midió **antes de tocar una línea de código**, sobre el árbol limpio en `a03b4ad`, que sólo contenía los cuatro artefactos del change.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`a03b4ad`, sólo artefactos) | **799 passed**, 0 failed, 206,8 s |
| `ai-service` al cerrar la implementación (2026-09-07) | **907 passed**, 0 failed, 183,6 s |
| `ai-service` re-ejecutada al abrir esta pasada de QA (2026-09-11) | **907 passed**, 0 failed, 66,8 s |
| `ai-service` tras cerrar los tres huecos de §9.10 a §9.12 | **912 passed**, 0 failed, 133,0 s |
| `uv run --system-certs pytest -m db` sobre `tests/evals` | **2 passed**, 0 skipped — ejecutados de verdad, no saltados |
| `openspec validate --all --strict` | **52 passed, 0 failed** |
| `uv run evals validate` | `golden set 1:1474bfc3aa3a: 56 queries (48 judged), 3926 judgements` |
| `dotnet test` · `npm run test` | **no ejecutados**: fuera del diff. Ver §5 |

**+113 tests** sobre la línea base (799 → 912), y el reparto cuadra al caso: **114 tests nuevos menos uno retirado**. El retirado es un caso parametrizado — `/v1/evals/runs` sale de la lista de rutas que responden 501 con los stubs apagados, porque dejó de responder 501, que es justo el cambio de comportamiento que la spec pide (§9.15). `test_stub_mode.py` colecciona **5 casos donde antes coleccionaba 6**, comprobado poniendo el fichero en `stash` y contando las dos versiones.

El recuento **sí es fiable** aquí, y conviene decir por qué: la suite de `ai-service` parte de **cero fallos**, así que la comparación por nombres que `CLAUDE.md` exige en `backend/` y en `frontend/` —donde el rojo preexistente hace del recuento una señal inútil— se satisface trivialmente: el conjunto de fallos es el mismo en las dos puntas, y está vacío.

> **La primera pasada de los tests `db` no se dio por buena por el color.** El README ya documenta la trampa para `tests/migrations/`: sin Docker saltan en silencio y una corrida verde no prueba que se ejercitó el SQL. Se comprobó explícitamente con `-m db` que los 2 tests `db` del arnés **corren**, no saltan.

### Desglose de tests nuevos

| Fichero | Tests | Qué cubre |
|---|---:|---|
| `tests/evals/test_golden_validation.py` | **16** | Un test **por cada fila de la matriz de trazabilidad**, cada uno con un golden set que rompe esa fila y sólo esa: menos de doce consultas sin anclaje, una subjetiva que nombra un material, cuatro consultas sobre una sola piedra, un tipo de sinónimo que el diccionario no corrobora, texto sin sentido en fuera de dominio, una fuera de dominio que resulta respondible, una literal que es una descripción, una categoría íntegramente sintética, el suelo de 45, el par juzgado dos veces, la consulta declarada sin juicios que trae juicios, **la carga sin abrir un socket** y **la versión que se mueve al apender un juicio** |
| `tests/evals/test_metrics.py` | **14** | nDCG contra un valor calculado a mano en las dos formas —expresión cerrada y decimal—; la lectura binaria que da otro número; la consulta sin respuesta que puntúa 0 y no 1; no juzgado separado de irrelevante; el desglose por origen que **cuenta** por origen sin **encoger** el corpus; ninguna configuración con knob de origen; desplazamiento sintético medido y su caso no aplicable; `Recall@5` acotado y clásico; juicios caducados; separabilidad de distancias; ventana de reranking dentro y fuera |
| `tests/evals/test_baselines_and_configs.py` | **11** | `v0-fts` compuesta **sólo** sobre nombre, SKU y descripción, con `doc_text` apareciendo exactamente dos veces y nunca como documento de búsqueda; **el prefijo `Descripción: ` como contrato del renderizador**; `v0-nombre` sin tokenizar ni derivar; las dos sentencias con orden total; el tokenizador de .NET término a término; el `OR` entre términos; las cinco configuraciones en orden de ablación; el coste cero **registrado**; el knob mal escrito que se rechaza; ninguna configuración escopada; los precios con fecha y fuente |
| `tests/evals/test_pooling_and_cag.py` | **11** | Unión sin repetición ordenada por mejor rango; parada cuando el último bloque no aporta; profundidad que llega al tope cuando sí aporta; el tope que no se rebasa; el *pool* sin etiquetar que no profundiza; **el juicio nuevo que no altera los ya registrados**; truncado determinista de un catálogo **mayor** que el presupuesto; omitidos registrados; **ningún precio en el contexto**; curva de escala hasta donde deja de caber; la respuesta leída como los códigos que citó |
| `tests/evals/test_provenance_and_report.py` | **31** | Procedencia comparable y no comparable, con el elemento que difiere nombrado; el `config_id` que **no** hace incomparable; la línea base sin modelo de embeddings; la revisión desconocida; la huella que nota un documento cambiado y que ignora el orden; vectores a seis decimales; **el arnés que se niega a embeber al vuelo**; latencia de recuperación sin el proveedor y sin negativos; la ejecución en frío excluida y reportada; el colector que lee las etapas ya registradas; **las tres condiciones de la regla de defaults, una a una**; el barrido direccional; **la constante del barrido separada del default de producción**; el informe sin base de datos; el runner que no importa la persistencia; las dos lecturas coincidiendo y divergiendo; la abstención marcada provisional; **la fila no comparable por no juzgado** y la que no lo es; **los precios no verificados declarados** |
| `tests/evals/test_reproducibility.py` | **5** *(2 `db`)* | Dos corridas con la misma procedencia dan métricas idénticas; el mismo documento sobrevive al empate en tres corridas; **ninguna llamada al proveedor durante una corrida**; ida y vuelta por la persistencia; **las líneas base sin coste persistidas como cualquier otra fila, con `NULL` en el modelo de embeddings** |
| `tests/retrieval/test_tiebreak.py` | **7** | Las dos sentencias terminan su orden con la clave determinista; la clave va **última** y nunca por delante de una señal real; empate de `coordination` y `ts_rank` que sobrevive igual en tres corridas; el empate que es un empate de verdad antes de que la clave decida; la clave que **no** reordena lo que difiere en coordinación ni en distancia; distancias iguales que se resuelven igual |
| `tests/migrations/test_c24_schema.py` | **15** *(todos `db`)* | Las tres tablas con sus columnas exactas; los índices que el informe y la ruta recorren; la línea base sin modelo de embeddings; el estado desconocido rechazado; el caso juzgado dos veces; la consulta fuera de dominio sin origen; el *bucket* inventado rechazado; **grado y `unjudged` que no pueden contradecirse**, en las dos direcciones; dos documentos en el mismo rango; la cascada; el caso huérfano; el orden más reciente primero; **`upgrade`/`downgrade` sin dejar rastro ni tipo huérfano** |
| `tests/api/test_evals_gating.py` | **+4** | La ruta que ya **no** responde 501 con stubs apagados; la historia vacía que es lista vacía y no error; las ejecuciones servidas con sus métricas; el 503 que nombra `DATABASE_URL` |
| `tests/evals/conftest.py` | — | Golden set de fixture **construido exactamente en los mínimos**: con márgenes holgados, cada test seguiría pasando después de que su requisito dejara de comprobarse |

**3.921 líneas** de paquete nuevo en `src/jbg_ai/evals/` y **2.360** de tests nuevos.

---

## 2. El golden set, comprobado por su propio validador

### 2.1. Composición

`uv run evals validate` más un recuento directo sobre los ficheros, contrastado con la tabla del §5 del informe de exploración, que la fijó **antes** de escribir una sola consulta:

| Categoría | Previsto | Entregado |
|---|---:|---:|
| Descripción natural sin anclaje léxico | 12 | **12** ✅ |
| Variante / talla | 7 | **7** ✅ |
| Materiales | 5 | **5** ✅ |
| Piedra | 4 | **4** ✅ |
| Subjetiva | 5 | **5** ✅ |
| Sinónimos | 6 | **6** ✅ |
| Léxico exacto | 4 | **4** ✅ |
| Fuera de dominio plausible | 5 | **5** ✅ |
| **Total juzgado** | **48** | **48** ✅ |
| Sustituto (C26) + ambigua (C30), declaradas sin juicios | 4 + 4 | **4 + 4** ✅ |
| **Total escrito** | **56** | **56** ✅ |

No es casualidad: `golden.py` **falla la carga** si alguna de las seis filas de la matriz baja de su mínimo, y los 16 tests de §1 lo demuestran fila a fila.

### 2.2. El criterio se escribió antes de etiquetar, y hay evidencia

No es una afirmación de proceso: son las marcas de tiempo del sistema de ficheros.

```
2026-09-07 00:22:40  evals/golden/criterion.md
2026-09-07 00:51:59  evals/golden/query_vectors.jsonl
2026-09-07 00:53:19  evals/golden/judgements.jsonl
```

**Treinta y un minutos** entre el criterio y el primer juicio. Es lo que exige el escenario *«The criterion exists before the first judgement»*, y es lo único de ese escenario que un test no puede comprobar: que el fichero exista sí se comprueba; que sea anterior, sólo el reloj lo sabe.

**Y hay un desfase aparente que conviene dejar explicado aquí, porque leído sólo sobre el golden set parece lo contrario de lo que es.** Los 3.926 juicios llevan `judged_at: 2026-09-06` y el criterio se declara escrito el 2026-09-07, de modo que sobre el dato desnudo *todos* los juicios preceden al criterio. Lo que ocurre es que las dos fechas no miden lo mismo: `judged_at` registra **la sesión de etiquetado**, que es la del 6, y el criterio lleva **la hora del reloj** del fichero, 00:22:40 — la sesión entró en la madrugada del 7. Las marcas de arriba son la prueba y ordenan los dos hechos como deben ir.

No se corrige el dato, y la razón es de procedencia y no de pereza. El digest que produce `golden_set_version` cubre `criterion.md`, `queries.jsonl` y `judgements.jsonl` ([`content_version`](../../../../ai-service/src/jbg_ai/evals/golden.py)), así que tocar cualquiera de los dos ficheros mueve la versión a `1:908ffd55add0` — y el informe, que dice haber corrido contra `1:1474bfc3aa3a`, pasaría a afirmar una procedencia bajo la que nunca corrió. Eso es peor defecto que el desfase de un día en un campo que **ningún cálculo lee**: `judged_at` se parsea al cargar y se reescribe al añadir juicios, y ni una métrica ni una validación lo consultan. **La corrección sale gratis en C25**, que vuelve a correr el arnés contra este mismo conjunto: ese día el `sed` no cuesta procedencia, porque la corrida nueva ya se hace contra la versión corregida.

### 2.3. El etiquetado

| | Valor |
|---|---:|
| Juicios totales | **3.926** |
| Grado 2 · grado 1 · grado 0 | 955 · 852 · **2.119** |
| Origen de los juicios: real · sintético | 2.000 · 1.926 |
| Juicios sobre documentos **fuera del *pool*** (respuestas declaradas, §9.4) | **381** |
| Consultas con al menos un grado 2 **que la rama léxica no alcanza** | **12** — exactamente el mínimo |
| Juicios apoyados en un texto que ya cambió | **0** |

**Profundidad adaptativa, y funcionó como se diseñó:** 13 consultas pararon en la base de 20, 10 en 30, una en 50 y 24 llegaron al tope de 60. Si la regla hubiera sido profundidad fija 60, habrían sido 48 de 48; si hubiera sido fija 20, el denominador de recall habría sido optimista en la mitad del conjunto.

### 2.4. Tres sesiones agrupadas por categoría

El etiquetado se hizo por categoría y no por orden de identificador, como manda D3: descripción sin anclaje y variante/talla primero, luego materiales, piedra y subjetivas, y por último sinónimos, léxico exacto y fuera de dominio. Las consultas dudosas se releyeron en una pasada posterior (§9.1, §9.2), que es lo que sustituye a la conciliación entre anotadores que este proyecto no tiene.

---

## 3. Escenarios de las specs, uno a uno

**47 escenarios `#### Scenario:`** en 20 requisitos, repartidos en cuatro deltas. Todos tienen test nombrado salvo dos, que se verifican por evidencia y se dicen aquí en vez de disimularse.

### `retrieval-evaluation` — el golden set como artefacto (5)

| Escenario | Test | Resultado |
|---|---|---|
| The criterion exists before the first judgement | `test_a_set_without_an_annotation_criterion_is_refused` + marcas de tiempo (§2.2) | ✅ |
| The golden set is not read from the database | `test_the_golden_set_needs_no_database` | ✅ |
| A set without unanchored queries is rejected | `test_too_few_unanchored_queries_fails_the_load` | ✅ |
| Nonsense text does not satisfy the out-of-domain category | `test_nonsense_does_not_satisfy_the_out_of_domain_category` | ✅ |
| A wholly synthetic category is rejected | `test_a_wholly_synthetic_category_is_refused` | ✅ |

### Las dos lecturas y las tres particiones (4)

| Escenario | Test | Resultado |
|---|---|---|
| Both readings appear in the report | `test_the_report_publishes_both_readings_and_the_three_splits` | ✅ |
| **Divergence between readings is surfaced** | `test_disagreeing_readings_are_surfaced_as_a_finding` · `test_agreeing_readings_are_reported_as_a_robustness_result` | ✅ (§9.10) |
| The three readings are published | `test_the_report_publishes_both_readings_and_the_three_splits` | ✅ |
| A result that only holds on the tuning subset is not a confirmation | `test_a_result_that_only_holds_on_the_tuning_subset_is_not_a_confirmation` | ✅ |

### *Pooling* y juicios apendables (4)

| Escenario | Test | Resultado |
|---|---|---|
| A query with few relevant documents stops early | `test_pooling_stops_when_the_last_block_contributed_nothing` | ✅ |
| Pooling never exceeds what the retriever can show | `test_pooling_never_goes_past_what_the_retriever_can_show` | ✅ |
| A later configuration adds judgements without invalidating the previous ones | `test_a_new_judgement_does_not_alter_the_ones_already_recorded` · `test_appending_a_judgement_moves_the_version` | ✅ |
| **A configuration promoting unjudged documents is not silently penalised** | `test_a_configuration_promoting_unjudged_documents_is_not_presented_as_final` · `test_a_fully_judged_row_is_not_marked` | ✅ (§9.11) |

### Desglose por origen (2)

| Escenario | Test | Resultado |
|---|---|---|
| The real portion is not measured over a smaller corpus | `test_the_origin_breakdown_counts_only_that_origin_and_never_shrinks_the_corpus` · `test_no_configuration_can_restrict_the_corpus_by_data_origin` | ✅ |
| Synthetic interference is measured, not assumed | `test_synthetic_displacement_is_measured_and_not_assumed` · `test_displacement_does_not_apply_where_no_real_answer_exists` | ✅ |

### Las líneas base replican lo que dicen replicar (3)

| Escenario | Test | Resultado |
|---|---|---|
| The legacy baseline answers a natural-language query the way the old searcher did | `test_v0_nombre_matches_the_whole_query_as_a_substring_and_never_tokenises` **+ la medición**: `v0-nombre` saca 0,000 en siete de las ocho categorías y 0,902 en léxico exacto, que es exactamente la predicción falsable del §P7 de la exploración | ✅ |
| The full-text baseline does not see the extracted fields | `test_v0_fts_composes_only_over_the_dotnet_columns` | ✅ |
| A renderer change breaks the fidelity test, not the fidelity | `test_the_renderer_still_emits_the_description_line_with_its_prefix` | ✅ |

### La línea base sin recuperación (3)

| Escenario | Test | Resultado |
|---|---|---|
| A catalogue larger than the budget is truncated deterministically | `test_a_catalogue_larger_than_the_budget_is_truncated_the_same_way_every_run` · `test_the_number_of_omitted_documents_is_recorded_next_to_the_recall` | ✅ |
| The context carries no price | `test_no_price_reaches_the_context` | ✅ |
| The scale projection is part of the result | `test_the_scale_projection_says_where_the_catalogue_stops_fitting` | ✅ |

### Procedencia (2)

| Escenario | Test | Resultado |
|---|---|---|
| Repeating a run yields identical metrics | `test_repeating_a_run_yields_identical_metrics` · `test_the_same_document_survives_the_tie_on_every_run` | ✅ |
| A moved index makes previous runs incomparable | `test_a_moved_index_makes_two_runs_incomparable_and_names_what_moved` | ✅ |

### Abstención y distancias (2)

| Escenario | Test | Resultado |
|---|---|---|
| The distribution is published per grade | `test_the_distance_distribution_reports_whether_one_value_separates_the_two` **+ el informe**, cuya sección de distancias se genera de esa misma función | ✅ |
| Abstention figures are marked provisional | `test_the_report_marks_the_abstention_figures_provisional` | ✅ |

### Anclaje del texto juzgado (1)

| Escenario | Test | Resultado |
|---|---|---|
| A re-enriched product is detected after labelling | `test_stale_judgements_are_counted_against_the_text_they_were_made_on` | ✅ |

### *Artifact-first* (2)

| Escenario | Test | Resultado |
|---|---|---|
| A run without persistence still produces its report | `test_a_run_without_persistence_still_writes_its_report` · `test_the_runner_does_not_import_the_persistence_module` | ✅ |
| **Baseline runs are persisted like any other** | `test_the_zero_cost_baselines_are_persisted_like_any_other_row` | ✅ (§9.12) |

### Latencia y coste (4)

| Escenario | Test | Resultado |
|---|---|---|
| Both latency figures appear per configuration | `test_a_latency_summary_carries_both_figures` · `test_retrieval_latency_excludes_the_provider_round_trip` | ✅ |
| The cold execution is excluded | `test_the_cold_execution_is_excluded_from_the_percentiles_and_still_reported` | ✅ |
| A configuration without provider calls records zero | `test_the_zero_cost_baselines_record_zero_and_not_an_absent_value` | ✅ |
| **Unverifiable prices are declared, not invented** | `test_unverifiable_prices_are_declared_rather_than_invented` · `test_a_file_claiming_to_be_verified_without_a_date_is_not_believed` | ✅ (§9.11) |

### La regla de defaults y la ejecución *offline* (4)

| Escenario | Test | Resultado |
|---|---|---|
| A small improvement does not move a default | `test_a_small_improvement_does_not_move_a_default` | ✅ |
| A change of default is justified against the written rule | `test_a_material_improvement_in_every_reading_moves_the_default` · `test_a_category_paying_for_the_average_blocks_the_change` | ✅ |
| The suite passes with no provider reachable | `test_the_harness_never_calls_the_provider_during_a_run` | ✅ |
| A ranking metric is verified against a hand-computed value | `test_ndcg_matches_the_value_computed_by_hand` | ✅ |

### `vector-retrieval` — orden total en la rama vectorial (3)

| Escenario | Test | Resultado |
|---|---|---|
| Equal distances resolve the same way on every run | `test_equal_distances_survive_truncation_the_same_way_every_run` | ✅ |
| The tiebreak does not reorder candidates that are not tied | `test_the_tiebreak_does_not_reorder_candidates_whose_distances_differ` | ✅ |
| Repeating a retrieval yields the same candidate set | `test_the_same_document_survives_the_tie_on_every_run` · `test_repeating_a_run_yields_identical_metrics` | ✅ |

### `hybrid-fusion` — orden total en la rama léxica (3)

| Escenario | Test | Resultado |
|---|---|---|
| Equal coordination and rank resolve the same way on every run | `test_equal_coordination_and_rank_survive_truncation_the_same_way_every_run` · `test_a_tie_is_a_real_tie_before_the_key_decides` | ✅ |
| The tiebreak does not disturb the coordination ordering | `test_the_tiebreak_does_not_reorder_candidates_that_differ_in_coordination` | ✅ |
| The fused result is stable across runs | `test_the_same_document_survives_the_tie_on_every_run` | ✅ |

### `ai-service-api-contracts` — la ruta deja de ser stub (5)

| Escenario | Test | Resultado |
|---|---|---|
| Evals route serves persisted runs in the development profile | `test_the_route_serves_the_runs_it_is_given_with_their_metrics` · `test_a_persisted_report_can_be_read_back_through_the_repository` (`db`) | ✅ |
| An empty history is an empty list, not an error | `test_an_empty_history_is_an_empty_list_and_not_an_error` | ✅ |
| The route no longer answers 501 with stubs disabled | `test_the_route_no_longer_answers_501_with_stubs_disabled` + `/v1/evals/runs` retirado de la lista de rutas 501 en `test_stub_mode.py` | ✅ |
| Evals route is absent in the production profile | `test_dev_only_evals_route_absent_in_prod_profile` (ya existía y sigue en verde) | ✅ |
| The contract snapshot is unchanged | `test_openapi_snapshot_is_stable` + regeneración en memoria (§6) | ✅ |

---

## 4. Nombres exigidos por `tasks.md`

**`tasks.md` no nombra ni un solo test literalmente.** Describe comportamientos —*«Test que demuestra que dos documentos con la misma `ts_rank` … sobreviven al corte siempre en el mismo orden»*— y esa es la forma correcta de pedirlo. El único nombre literal en todos los artefactos es `test_run_is_reproducible_for_same_config_and_seed`, y aparece en `design.md` y en el ticket **citando la ficha**, para decir que sin el desempate ese test *«pasa en verde mientras el arnés produce ruido»*.

La exploración ya había releído los seis nombres de la ficha (§8 del informe) y había reinterpretado dos de ellos. La implementación los nombra en el estilo de la casa —una frase que dice qué es verdad, no qué función se llama— y el mapeo es éste:

| Nombre de la ficha | Test entregado | Nota |
|---|---|---|
| `test_ndcg_matches_hand_computed_value_on_fixture` | `test_ndcg_matches_the_value_computed_by_hand` | Sin cambio de contenido |
| `test_run_is_reproducible_for_same_config_and_seed` | `test_repeating_a_run_yields_identical_metrics` | «Seed» dejó de ser un RNG en D2: lo que hace comparable una corrida es la **procedencia**, y el nombre lo dice |
| `test_metrics_reported_per_data_origin` | `test_the_origin_breakdown_counts_only_that_origin_and_never_shrinks_the_corpus` | El nombre largo carga la semántica de D5, que es lo que se puede hacer mal |
| `test_lexical_baseline_matches_dotnet_search_semantics` | `test_v0_nombre_matches_the_whole_query_as_a_substring_and_never_tokenises` · `test_v0_fts_composes_only_over_the_dotnet_columns` | **Dos**, porque D1 partió la línea base en dos filas |
| `test_cag_baseline_respects_context_budget` | `test_a_catalogue_larger_than_the_budget_is_truncated_the_same_way_every_run` | **Reescrito por D6**: «cabe» se cae el día que el catálogo crezca |
| `test_cost_per_query_recorded_per_config` | `test_the_zero_cost_baselines_record_zero_and_not_an_absent_value` | Lo que puede fallar no es que haya columna, es que el cero se lea como hueco |

---

## 5. Alcance negativo

```bash
git status --short -- frontend/ terraform/ .github/ backend/ \
  ai-service/openapi.json \
  ai-service/src/jbg_ai/indexing/ ai-service/src/jbg_ai/enrichment/ \
  ai-service/src/jbg_ai/knowledge/ ai-service/src/jbg_ai/config/settings.py \
  ai-service/src/jbg_ai/retrieval/synonyms.py \
  ai-service/src/jbg_ai/retrieval/fusion.py \
  ai-service/src/jbg_ai/retrieval/query_synonyms.yaml
```

Salida **vacía**.

| Guardarraíl | Comprobación | Resultado |
|---|---|---|
| `indexing/embeddings.py` | `git diff` vacío. Se **importa** `LiteLlmEmbeddingClient`; el cliente congelado del arnés implementa el mismo puerto sin tocarlo | ✅ |
| `enrichment/vocabularies.yaml` · `retrieval/query_synonyms.yaml` | `git diff` vacío. El diccionario se **lee** para validar la categoría de sinónimos; nunca se escribe | ✅ |
| `retrieval/fusion.py` · `retrieval/synonyms.py` · `retrieval/orchestrator.py` | `git diff` vacío. El arnés **llama** a `retrieve_products`; no duplica pipeline, que es la versión sutil del error que C23 cometió con su embebedor sustituto | ✅ |
| **`config/settings.py`** | `git diff` **vacío**, y eso es un resultado: la regla de D13 **no se disparó** (§8.2). La desviación estaba autorizada y no hizo falta | ✅ |
| `retrieval/search.py` | **+13 / −2 líneas**, y son la desviación declarada: dos claves `, d.product_id ASC` reemplazando sus dos `ORDER BY`, más once de comentario que explican por qué un change de evaluación toca ruta viva | ✅ declarado |
| `frontend/` · `terraform/` · `.github/workflows/` · `backend/` | `git diff` vacío | ✅ |
| Migraciones de EF Core | **ninguna**. Una sola revisión de Alembic, aditiva, en el esquema `ai` | ✅ |
| Ruta `/v1` nueva | **ninguna**. `GET /v1/evals/runs` ya estaba publicada desde C02 | ✅ |
| Esquema `public` desde Python | ninguna sentencia lo lee. Las dos réplicas de línea base reproducen **semánticas** de .NET sobre el esquema `ai`, que es justo lo que obliga a recomponer el texto (§7, D1) | ✅ |
| `ai.query_log` | no existe y no se crea | ✅ |
| `dotnet test` · `npm run test` | **no ejecutados**, porque el diff no toca esos árboles | ✅ |

**Diff total: 9 ficheros modificados (+338 / −102) y 13 árboles o ficheros nuevos**, este documento incluido. Los nueve modificados son exactamente los que el ticket declaraba, más los tres de test que el cambio de comportamiento obliga a mover.

---

## 6. El contrato, **no** movido

Comprobado por construcción y no por lectura, como en C23:

```python
app = create_app(canonical_openapi_settings())
spec = get_openapi(title=app.title, version=app.version, routes=app.routes)
spec == json.load(open("openapi.json"))   # True
```

→ `regenerado == comiteado: True`, **11 rutas**, `/v1/evals/runs` presente **y sin un solo byte de diferencia**.

Es el punto que hacía falta cuidar: la ruta **cambia de comportamiento** —deja de servir un fixture y pasa a leer `ai.eval_run`— sin cambiar ni su modelo de petición ni el de respuesta. `EvalRunsResponse` ya encajaba con las columnas de esa tabla, que es precisamente lo que D10 argumentaba: el contrato no se diseñó para el stub, se diseñó para esto.

Dos detalles del mapeo, decididos y no accidentales:

- **`suite` ← `config_id`.** Es lo que distingue una fila de una tabla de ablations de otra; una constante como `"retrieval-golden-set"` habría sido indistinguible entre filas.
- **Las métricas booleanas no viajan.** `EvalMetric.value` es un `float`, y `abstained: true` serializado como `1.0` sería un número inventado. `read_runs` filtra los booleanos explícitamente, y el test lo fija.

---

## 7. Decisiones de diseño, verificadas en código

| Decisión | Evidencia |
|---|---|
| **D1** · Dos líneas base léxicas | `evals/configs/v0-nombre.yaml` y `v0-fts.yaml`, con nombres que no se confunden. La fidelidad de `v0-fts` **recompone** `name ‖ sku ‖ <línea Descripción>` porque `ai.product_document` no tiene columna `description` y un FTS sobre `doc_text` sería **cota superior**; `test_v0_fts_composes_only_over_the_dotnet_columns` cuenta las apariciones de `doc_text` y rechaza las líneas extraídas |
| **D2** · Reproducibilidad | 48 vectores congelados a 6 decimales (756 KB); tupla de procedencia en cada `eval_run`; y el **desempate**, que es el diff entero de ruta viva: `ORDER BY … ASC, d.product_id ASC` en la vectorial y `ORDER BY coordination DESC, ts_rank DESC, d.product_id ASC` en la léxica. `FrozenEmbeddingClient` **levanta excepción** si falta un vector, en vez de llamar al proveedor por detrás |
| **D3** · Graduado 0-2 con lectura binaria | `RELEVANT_FROM = 1` declarado una vez en `golden.py` y usado por las dos lecturas; el informe publica ambas y **señala si divergen** (§9.10) |
| **D4** · 48 juzgadas, tres lecturas | 48/56 exactas; 8 consultas marcadas `in_tuning_set`; `split_readings` produce siempre las tres. La contaminación salió **cuantificada**: 0,942 en ajuste contra 0,535 en nuevas para el híbrido (§8.1) |
| **D5** · Agrupar por consulta, contar por juicio | `score_case(origin=…)` filtra **el recuento**, nunca el corpus; `test_no_configuration_can_restrict_the_corpus_by_data_origin` recorre las cinco configuraciones buscando un knob de origen que no existe |
| **D6** · `v0-cag` acotado | `cag.py` es puro y testable sin proveedor; `cag_run.py` es el que llama al modelo, separado a propósito para que una cifra irreproducible no entre en una tabla de filas reproducibles. Sin precio, verificado sobre el prompt construido |
| **D7** · *Pooling* adaptativo | Base 20, bloques de 10, tope 60, `judged_depth` por consulta. La regla mira **el último bloque** y no el *pool* entero: ver §9.5, donde esa distinción estuvo mal implementada |
| **D8** · Abstención medida, umbral intacto | `git diff` de `settings.py` vacío; el informe marca las cifras provisionales; y la distribución publicada **contesta la pregunta**: no hay hueco (§8.3) |
| **D9** · `source_hash` por juicio | Grabado en los 3.926 juicios; `stale_judgements` los cuenta contra el índice vivo y el informe lo publica junto a las métricas, no en un log aparte |
| **D10** · *Artifact-first* | `test_the_runner_does_not_import_the_persistence_module` inspecciona los `import` del módulo, no su texto — el docstring menciona la palabra a propósito |
| **D11** · `pricing.yaml` | `as_of: 2026-09-07`, fuente verificada **ese día**; cero registrado y no ausente; y el camino de precios no verificados, que ahora tiene test (§9.11) |
| **D12** · Dos columnas de latencia | 96 muestras por configuración, primera ejecución descartada y reportada aparte. El proveedor, que los vectores congelados eliminan por construcción, se mide con `evals provider-latency` (§9.9) |
| **D13** · Regla escrita antes de medir | `evals/sweep.py` con las tres condiciones y los dos márgenes; tres tests, uno por condición; y `test_the_sweep_grid_and_the_production_default_are_separate_constants`, que es **la regla que C23 pagó por aprender**: ninguna constante puede a la vez gobernar una medición y aseverar un default |

---

## 8. Mediciones

Todas contra el índice real y el proveedor real. El detalle completo está en
[`c24-baselines-2026-09-07.md`](../../../../ai-service/evals/results/c24-baselines-2026-09-07.md),
[`c24-sweep.md`](../../../../ai-service/evals/results/c24-sweep.md),
[`c24-cag-measurement.json`](../../../../ai-service/evals/results/c24-cag-measurement.json) y el
[informe de implementación](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c24-implementation-measurements.md).

### 8.1. La decisión 12, respondida (tarea 13.1)

| Configuración | nDCG@5 | nDCG@5 bin | Recall@5 | P@3 | MRR | coste/consulta |
|---|---:|---:|---:|---:|---:|---:|
| `v0-nombre` | **0,082** | 0,077 | 0,071 | 0,035 | 0,104 | $0 |
| `v0-fts` | **0,454** | 0,518 | 0,500 | 0,493 | 0,592 | $0 |
| `v1-vectorial` | **0,548** | 0,580 | 0,571 | 0,563 | 0,645 | $0,0000002 |
| `v2-hibrido` | **0,603** | 0,634 | 0,625 | 0,597 | 0,690 | $0,0000002 |

**Las dos lecturas ordenan igual**, así que la comparación es robusta a la elección de escala — la objeción del apunte de S10 contestada con datos.

**El veredicto de la rúbrica de C21 se invierte.** Daba 67/120 a la rama vectorial contra 107 de la léxica; contra un juez que no es parte, la vectorial **bate** a la línea léxica, y en las doce consultas sin anclaje saca 0,431 contra 0,035.

**Y la contaminación del conjunto de ajuste, cuantificada:** el híbrido saca **0,942** sobre las 8 consultas con las que se calibró y **0,535** sobre las 40 que no vio nunca. Ninguna línea base, que nadie calibró, muestra ese hueco.

### 8.2. El barrido y la regla de D13 (tareas 13.2-13.4)

`uv run evals sweep`, 12 puntos, dirección única hacia arriba por el argumento de P2.

- Óptimo medido: **`wC` entre 0,75 y 1,0** (0,659 contra los 0,603 vigentes).
- Delta global **+0,057** (supera el margen de 0,05) · consultas nuevas **+0,073** · **conjunto de ajuste −0,024**.
- **Veredicto: el default NO se mueve.** La tercera condición —mismo signo en las tres lecturas— falla, y falla precisamente en la lectura contaminada.

Es el caso incómodo para el que la regla se escribió, y **no se ha reinterpretado después de verlo**: cambiarla ahora sería el ajuste *post hoc* que escribirla antes servía para evitar. El hallazgo se documenta y pasa a C25. `config/settings.py` queda sin diff.

### 8.3. La distribución de distancias contesta a C25 (tarea 13.5)

| grado | documentos | mínimo | mediana | máximo |
|---|---:|---:|---:|---:|
| 0 | 2.119 | 0,3268 | 0,5338 | 0,8710 |
| 1 | 852 | 0,2745 | 0,4668 | 0,7465 |
| 2 | 955 | 0,2071 | 0,5167 | 0,8008 |

Relevantes hasta **0,8008**, irrelevantes desde **0,3268**: **hueco de −0,4739**, solape total. Donde el corpus de conocimiento tenía ocho milésimas limpias, el de productos **no tiene ninguna**. Queda demostrado que un umbral escalar no puede ser la respuesta. Es un resultado, no una tarea pendiente.

### 8.4. Latencia y los dos huérfanos de C21 §12 (tareas 11.1-11.3)

`p95` de recuperación del híbrido: **128,6 ms** contra los 500 ms del criterio del diseño. Se cumple, y se cumple en la columna a la que D12 dice que hay que aplicarlo.

- **Rama léxica dentro del orquestador: p50 19,1 ms.** Se solapa entera con la espera del proveedor, así que su coste marginal en la ruta viva es **cero**, y la decisión D10 de C21 queda confirmada.
- **Singleton del cliente de embeddings:** en frío p50 223,4 ms / p95 831,7 ms; en caliente **0,0 ms**. No reduce el ida y vuelta: **lo elimina** en la segunda consulta idéntica.

### 8.5. `v0-cag` (tareas 7.1-7.6)

17.583 tokens, $0,00267 por consulta, 0 documentos omitidos, curva de escala que deja de caber en 6.643 productos. Recall@5 sobre las 12 consultas sin anclaje: **0,133**, contra **0,483** de la rama vectorial sola — y respondió literalmente `NINGUNO` en **10 de 12**. Cuatro órdenes de magnitud más caro para un tercio del acierto, en el terreno que más le favorece.

### 8.6. El número que hace decidible el reranking (tarea 13.6)

**1 consulta de 48** tiene su grado 2 dentro de la ventana que un reranker reordenaría y fuera de las cinco que se muestran. Un cross-encoder de ~250 ms gastaría el 10-15 % del presupuesto de C16 para un techo del 2 %. El «no» deja de ser un argumento.

### 8.7. Lo que la medición **no** demuestra, dicho aquí

- **El criterio de aceptación del §8.1.1 no se cumple.** `Recall@5` sobre la porción real es **0,483** contra el 0,85 que el diseño fija, y el intervalo de ±0,13 no alcanza a cubrir la diferencia. La porción real resultó ser **41 consultas** y no las ~25-30 estimadas, así que el criterio **es concluyente** y lo que dice es que no se cumple.
- **El corpus sintético estorba.** En el **22 %** de las consultas con respuesta real, un sintético irrelevante se cuela por delante — y la cifra es idéntica en las tres configuraciones que recuperan algo, así que es propiedad del corpus y no de la configuración.
- **Ningún número de este change es un juicio sobre el otro anotador**, porque no hay otro. Ver §11 del informe de implementación.

---

## 9. Incidencias de esta pasada

### 9.1. `brazalete de cuero`, una consulta del propio C20, no tiene respuesta posible

Al construir el *pool* se vio que la categoría de materiales tenía una consulta con **cero documentos relevantes**. El catálogo tiene exactamente **un** artículo de cuero, `SKU1178`, y es un **colgante**, no una pulsera. Una consulta sin ningún relevante mide abstención, no materiales: habría sido una sexta consulta fuera de dominio colocada en la categoría equivocada, inflando la abstención y vaciando los materiales.

Sustituida por `aros de plata`, también de C20 y también marcada `in_tuning_set`. El motivo queda escrito **en el propio registro de la consulta**, no sólo aquí, y el hallazgo entra en el informe: era la elección natural precisamente por el falso amigo `piel`→`cuero` que el diccionario excluye por escrito, y resulta que el falso amigo no tenía nada que contaminar.

### 9.2. El *pool* no contenía la respuesta en cuatro de las doce consultas sin anclaje

`la lagartija que toma el sol en las paredes`, `el calzado típico…`, `una brújula…` y `el bicho con púas…` devolvían *pools* en los que **ninguna configuración** había traído la pieza correcta. Con el supuesto estándar de *pooling* —lo que queda fuera cuenta 0— esas cuatro consultas habrían tenido cero relevantes y habrían sido indistinguibles de las de fuera de dominio.

Ver §9.4: es lo que motivó las respuestas declaradas.

### 9.3. `Recall@5` clásico tiene techo en 0,055 en este conjunto

Dos consultas del golden set tienen ~90 documentos relevantes —el catálogo real es una línea marinera y hay noventa piezas con motivo de concha—. Con `|relevantes| = 90`, `Recall@5 = |rel ∩ top5| / 90` no puede pasar de 0,055 por perfecta que sea la recuperación: **mide el tamaño del catálogo, no el recuperador**.

**Desviación declarada:** el informe publica `Recall@5` con el denominador acotado a `min(5, |relevantes|)` **y** la lectura clásica, las dos, y el JSONL por consulta lleva ambas. El criterio de aceptación se lee contra la acotada, y el informe dice por qué en el mismo párrafo. No se eligió después de ver los números: se eligió al ver que el techo era estructural.

### 9.4. Respuestas declaradas fuera del *pool*

**Desviación declarada.** El conjunto juzgado es el *pool* **más** las respuestas que el autor declara por patrón de nombre o por campo —los abarca, las herraduras, los erizos, las piezas etiquetadas `boda`—, resueltas una vez contra el índice y congeladas como juicios con `pooled_in: []`. Son **381 de 3.926**.

El motivo es de método y no de comodidad: un denominador de recall construido **sólo con lo que los sistemas ya encuentran** favorece a todos por igual y esconde exactamente el caso que este change existe para medir. Cuatro de las doce consultas sin anclaje habrían pasado de «ninguna configuración la encuentra» a «no había nada que encontrar», que son cosas distintas.

### 9.5. La regla de profundidad adaptativa estaba mal implementada

La primera versión comprobaba si **el *pool* entero** tenía algún relevante antes de profundizar, en vez de **el último bloque añadido**. Con esa lectura, cualquier consulta con un primer tramo rico caminaba hasta el tope de 60 por muchos ceros que dieran las extensiones — que es exactamente el coste de la profundidad fija que la regla adaptativa existe para evitar.

Corregido, y el test lo fija en las dos direcciones: `test_pooling_stops_when_the_last_block_contributed_nothing` compra un bloque y para, `test_pooling_deepens_while_each_block_keeps_paying` llega al tope. El resultado se ve en el reparto de profundidades del §2.3: 13 consultas pararon en 20.

### 9.6. `perla` resuelve como material y no como piedra

La validación de la categoría de piedra iba a exigir que el término resolviera al campo `stone_type`. Pero el diccionario de consulta clasifica `perla` en `materials`, mientras el extractor la clasifica en `stone_type` en 31 documentos y en `materials` en **cero** — y ese desacuerdo es justo lo que la consulta `pendientes de perla` mide.

Exigir el campo habría expulsado del conjunto la única consulta de la categoría que prueba la trampa. La comprobación se hizo **agnóstica del campo**: exige que el diccionario resuelva el término al valor declarado, sea cual sea la casilla. El porqué está escrito en `names_stone`.

### 9.7. El `pos_id` es obligatorio aunque el prefiltro esté apagado

El orquestador parsea la reivindicación del punto de venta **siempre**, incluso con `pos_prefilter=false`, y por una razón buena que C22 dejó escrita: un token cuyo punto de venta no se puede leer está roto haga lo que haga la petición. El arnés, que etiqueta **sin escopar**, no tiene ninguno.

Se resuelve presentando el UUID nulo, documentado en `HARNESS_POS_ID`: con el prefiltro apagado no selecciona nada, y tomar prestado el identificador de una tienda real habría sugerido un escopado que no se está aplicando.

### 9.8. Dos obstáculos del entorno, que no son del servicio

- **`REQUESTS_CA_BUNDLE`, además de `SSL_CERT_FILE`.** El contador de tokens de `v0-cag` descarga su codificación por HTTPS usando `requests`, que **no** lee `SSL_CERT_FILE`. Con el TLS de esta máquina interceptado, `evals cag` fallaba con `CERTIFICATE_VERIFY_FAILED` en un punto que no tiene nada que ver con el proveedor. Documentado en la tabla de entorno del README.
- **`psycopg` y el `ProactorEventLoop`.** La CLI fija `WindowsSelectorEventLoopPolicy`; los tests de la ruta **doblan el repositorio** en vez de abrir una base, porque el cliente de pruebas corre la ruta en su propio bucle y el mensaje de error no nombra ni a psycopg ni a la política.

### 9.9. El `p95` extremo a extremo no puede incluir al proveedor

Los vectores congelados son lo que hace repetible una corrida, y **por eso mismo** eliminan el ida y vuelta del proveedor de la columna extremo a extremo: `p50 e2e` y `p50 recuperación` coinciden hasta la décima. Publicarlo así habría sido engañoso en la dirección contraria a la que D12 temía.

Se añadió `uv run evals provider-latency`, que mide el proveedor por separado, en frío y en caliente. Es también lo que adjudica el segundo huérfano de C21 §12 (§8.4).

### 9.10. Las dos lecturas se publicaban, pero una divergencia no se señalaba

Recorriendo los escenarios uno a uno: la spec exige que **cuando** las dos lecturas ordenen distinto las configuraciones, el informe lo **declare como hallazgo**. El informe publicaba ambas columnas y dejaba la comparación al lector. Con los datos de hoy coinciden, así que el requisito se cumplía **por suerte** y no por mecanismo.

Añadido `reading_divergence`, con las dos ramas escritas y sus dos tests. El informe dice ahora, explícitamente, que las dos lecturas coinciden y que por tanto la comparación es robusta a la escala.

### 9.11. Dos huecos más del mismo recorrido

- **Una fila con mucho top-5 sin juzgar no se marcaba como no comparable.** La spec lo exige; `unjudged@5` se publicaba pero nada marcaba la fila. Hoy todas valen 0,000 porque el *pool* se construyó con esas mismas configuraciones, así que el hueco era invisible — y explotaría en C25, que es cuando `v3-señales` promueva documentos que nadie juzgó. Añadido el umbral `NOT_COMPARABLE_UNJUDGED` con su marca en la tabla y su párrafo, más dos tests.
- **El camino de precios no verificados no tenía test.** El informe sabía escribir «NO VERIFICADOS», pero nada lo ejercitaba. Dos tests: uno sobre el informe, otro sobre el cargador, que **no cree** a un fichero que se declara verificado con fecha desconocida.

### 9.12. Que las líneas base se persistieran no tenía test, sólo evidencia viva

`ai.eval_run` contiene las cuatro filas, `v0-nombre` y `v0-fts` incluidas, con `NULL` en el modelo de embeddings. Pero eso es una observación sobre una base, no una prueba: un sumidero escrito alrededor de «lo que costó el proveedor» dejaría caer exactamente las dos filas sobre las que descansa la comparación. Añadido `test_the_zero_cost_baselines_are_persisted_like_any_other_row`, que persiste una configuración con coste y otra sin él y comprueba las dos.

### 9.13. El informe de implementación citaba la latencia de una corrida anterior

El informe se escribió con las cifras de una corrida y el informe versionado se regeneró después, con otra: el `p95` del híbrido aparecía como 136,8 ms en un documento y 128,6 ms en el otro. Las métricas de relevancia son deterministas y no se movieron; **la latencia no lo es**, y ésa es la única familia de cifras que puede desincronizarse entre dos documentos.

Alineados los dos —y el README—, con una frase que dice cuánto se movió y por qué eso no toca al criterio, que se lee contra un margen de casi cuatro veces.

### 9.14. Un test de «no abrir sockets» fallaba por el bucle de eventos, no por el proveedor

El primer intento de probar que una corrida no llama al proveedor bloqueaba `socket.socket.connect`. En Windows, el bucle de eventos abre un par de sockets para su propia tubería interna, así que el test fallaba por una razón que no tenía nada que ver con lo que quería demostrar. Se bloquea **el adaptador del proveedor**, `litellm.aembedding`, que es lo que se quería vigilar.

### 9.15. `test_stub_mode` esperaba 501 en la ruta de evals

La lista `_REAL_WHEN_STUBS_OFF` no incluía `/v1/evals/runs`, así que un test existente afirmaba que la ruta debía responder 501 con stubs apagados — que es **exactamente lo que la spec de este change cambia**. Actualizado con el motivo en el comentario, junto a las otras tres rutas que dejaron de ser stub en su momento.

---

## 10. Verificado a mano

- **Los *pools* se leyeron.** El etiquetado no fue un `sed` sobre una regla: se imprimieron las fichas compactas de cada *pool* —SKU, origen, alcanzabilidad léxica, configuraciones que lo trajeron, rango, nombre, tipo, materiales, piedra, talla, colección— y se recorrieron por categoría antes de escribir ninguna regla de grado.
- **Las listas de grado 2 se releyeron después**, que es la relectura diferida de D7. Así se confirmó que las 90 piezas de concha de `q01` son piezas de concha de verdad —caracola, conchiglie, shells, oreja de mar, mejillón, lapa, cono de mar— y no un desbordamiento de la expresión regular; y que los seis grado 2 de `pendientes de perla` salen por `stone_type` y no por el nombre, que es lo que esa consulta mide.
- **La predicción falsable de `v0-nombre` se cumplió**: 0,000 en siete categorías de ocho y 0,902 en léxico exacto. El §P7 de la exploración la escribió **antes** de medir para que la medición pudiera desmentirla.
- `\d ai.eval_run` y sus dos hermanas leídas contra la base local: las restricciones `CHECK` están donde se declararon, incluida `(grade IS NULL) = unjudged`, que es la que impide que «medido irrelevante» y «no medido» se confundan.
- `alembic upgrade head` contra la base local: `c9a71f2b6d54 -> d7c4e91b25a0`, y `ai.alembic_version` en `d7c4e91b25a0`.
- **Las filas persistidas se consultaron**, no se supusieron: `eval_run=4`, `eval_case=192`, `eval_result=6970`, con la misma tupla de procedencia que el informe versionado — `1:1474bfc3aa3a`, `051a6b06021efc3f…`, `a03b4adc0f0c`. El `run_id` difiere del informe final porque la pasada con `--persist` precedió a la última regeneración; la procedencia, que es lo que decide la comparabilidad, coincide.
- `uv run evals run --config v0-cag` comprobado a mano: **se niega** y explica que esa configuración responde en prosa y se mide con `evals cag`.
- Las marcas de tiempo del golden set, leídas del sistema de ficheros (§2.2).

---

## 11. Documentación de contexto

| Documento | Qué se alineó |
|---|---|
| `ai-service/README.md` | Sección nueva **«The evaluation harness and the golden set (C24)»**: los siete comandos, la tabla de ablations, la comparación RAG↔CAG, las dos columnas de latencia, la tabla de entorno del arnés y **las cuatro limitaciones declaradas**. Tres no-objetivos reescritos: `ai.eval_*` deja de ser «no existe», y se añaden el «no» al reranking **con su número** y el «no» a recalibrar el umbral **con la razón medida** |
| `Documentos/epicas.md` | Entrada de C24 en EP17 con el veredicto medido, el enlace al informe de implementación y los tres hallazgos que nadie buscaba |
| Informe nuevo | `c24-implementation-measurements.md`: el titular, la inversión del veredicto de P1, el barrido y su regla, la contaminación cuantificada, la distribución de distancias, el desplazamiento sintético, `v0-cag`, la latencia con los dos huérfanos adjudicados, el reranking, **las ocho cosas que se movieron respecto a la exploración** y las seis limitaciones |
| `evals/results/` | `c24-baselines-2026-09-07.md` (la corrida), `c24-sweep.md` (el barrido y su veredicto), `c24-cag-measurement.json` (la medición fechada) y `runs/<run_id>.jsonl` (192 líneas, detalle por consulta y configuración) |
| `evals/golden/criterion.md` | El criterio de anotación, escrito antes de etiquetar, con las tres anclas, los casos de grado 1 y las reglas de proceso |
| Informe de exploración | **Sin reescribir.** Sus cifras eran citas de informes anteriores y se declaró así; lo que la implementación movió está en el §9 del informe nuevo, y la diferencia entre ambos es el dato |

---

## 12. Fuera de esta pasada

- **El criterio de aceptación del §8.1.1 no se cumple**, y es lo primero que hay que saber: `Recall@5` sobre la porción real es 0,483 contra 0,85. No es un fallo de este change —que entrega el juez, no las mejoras que el juez apruebe— pero es el dato que C25 tiene que mover.
- **Re-fijar el umbral de distancia por cuantil** — es C25, y este change le entrega la demostración de que un escalar no puede servir.
- **Recalibrar `wC` con un conjunto que resuelva ±0,024** en la partición de ajuste. El óptimo medido está en 0,75-1,0 y la regla lo bloqueó; con 8 consultas de ajuste, esa lectura no distingue señal de ruido.
- **Revisar la fusión en las consultas sin anclaje léxico**, donde el híbrido pierde más de la mitad de la ventaja de su propia rama vectorial (0,172 contra 0,431). Es el sitio con más que ganar y nadie lo había visto.
- **Medir el coste del prefiltro por punto de venta en recall**: el golden set va sin escopar por decisión de C22, y la fila escopada quedó recortada por decisión declarada.
- **Repetir la evaluación con consultas escritas por alguien que no construyó el sistema.** Es la única mitigación real del sesgo del anotador único, y no es del alcance de este change.
- **RAGAS, validador anti-alucinación y escenarios de agente** — es C38, que se integra en este mismo runner y hereda `metrics jsonb` para no forzar una segunda revisión de Alembic.

---

## Veredicto

**Sin problemas abiertos.** `uv run --system-certs pytest` **912 passed, 0 failed** sobre una línea base medida de **799**, con los 2 tests `db` del arnés ejecutados de verdad contra pgvector y comprobado explícitamente que no saltaron. `openspec validate --all --strict` **52 passed, 0 failed**. **47/47 escenarios** con test nombrado, **84/84 tareas**.

**`openapi.json` byte a byte idéntico**, comprobado por regeneración en memoria, con la ruta cambiando de comportamiento sin cambiar de contrato. **Una** revisión de Alembic, aditiva y reversible sin dejar rastro. Los ficheros congelados, sin diff.

**Las dos desviaciones autorizadas, resueltas de forma distinta y las dos por escrito.** El desempate se hizo: **trece líneas añadidas y dos sustituidas** en la ruta viva, y sin ellas el arnés sería un generador de ruido. El cambio de defaults **no** se hizo, porque la regla escrita antes de medir lo bloqueó — y se bloqueó en el caso incómodo, con la mejora real en las consultas nuevas y el freno en la partición contaminada. `config/settings.py` sale de este change sin una sola línea de diff, y eso es un resultado y no una omisión.

**Dos desviaciones más, abiertas durante el apply** y declaradas donde se usan: el denominador acotado de `Recall@5`, porque la lectura clásica tenía un techo estructural de 0,055 en este conjunto, y las respuestas declaradas fuera del *pool*, porque un denominador hecho sólo de lo que los sistemas ya encuentran los favorece a todos por igual.

**Y cuatro cosas que sólo aparecen recorriendo los escenarios uno a uno**, no mirando un recuento verde: una divergencia entre lecturas que no se señalaba, una fila no comparable que no se marcaba, un camino de precios no verificados sin test, y una persistencia de líneas base apoyada en una observación en vez de en una prueba. Las cuatro cerradas, con cinco tests nuevos.

**Listo para archivar.**
