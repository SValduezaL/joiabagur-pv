# QA — C30a `add-assist-structure-and-rule-warnings`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** implementación y esta pasada de QA, el **2026-09-13** · **Rama:** `c30a-add-assist-structure-and-rule-warnings` · **Commit de artefactos:** `0ae0fdd` · **Implementación:** en árbol de trabajo, **sin commitear** al cierre de esta pasada
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **48/48 tareas**. Los tres spikes del §2 se corrieron **contra el índice vivo y el proveedor real**, y **antes de escribir una línea de código de producción**, que es el orden que `tasks.md` impone como dependencia y no como preferencia.
> **Este change mueve el contrato**, a diferencia de C23 y C24: `openapi.json` se regenera. El §6 demuestra por construcción **qué** se movió y qué no.
> **Lo que esta pasada de QA encontró:** tres escenarios de spec cuya cobertura era **indirecta** —se creían cubiertos y lo estaban sólo por implicación—, cerrados con tres tests nuevos. Ver §9.10.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| PostgreSQL | `jpv-pv-postgres` (`pgvector/pgvector:pg15`) en el 5433, con **1.168 documentos vivos, 491 en familia, 32 documentos y 161 fragmentos de conocimiento todos embebidos**, para los spikes y la evidencia; testcontainers efímero, base nueva por test, para el test `db` del roster |
| Proveedor de *embeddings* | **`openai/text-embedding-3-small`, real**, en el spike 1 (un lote de 72 consultas) y en la evidencia del §10 (2 consultas). **Ninguna corrida de tests lo llama** |
| Proveedor de LLM | **ninguna llamada, en ningún momento.** Es el invariante central del change y el §7 lo verifica de tres formas independientes |
| TLS | `SSL_CERT_FILE` **y** `REQUESTS_CA_BUNDLE` apuntando a un PEM del almacén de Windows concatenado con `certifi`. Hizo falta y no estaba previsto: ver §9.8 |
| Bucle de eventos | `WindowsSelectorEventLoopPolicy` en todo script suelto que abra el motor asíncrono; en tests lo resuelve `support/async_db.run_db`. Ver §9.9 |
| .NET | **no ejecutado, y a propósito**: el diff no toca `backend/`, y el §5 lo demuestra |
| Frontend | **no ejecutado**, por lo mismo |
| Contrato | `ai-service/openapi.json` **se mueve**. Comprobado por **regeneración en memoria**, no por inspección (§6) |
| Freeze C11 | `git diff -- ai-service/src/jbg_ai/indexing/embeddings.py` **vacío**, y además fijado por hash en `test_embeddings_module_is_untouched` |
| Vocabulario de enriquecimiento | `git diff -- ai-service/src/jbg_ai/enrichment/` **vacío**. Se **lee** para derivar las nueve fichas canónicas; nunca se escribe |
| Migraciones | **ninguna**. `alembic heads` → `d7c4e91b25a0`, la misma revisión que antes del change |
| Umbral de conocimiento | `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` **sin tocar**. El spike 1 lo midió y confirmó que **no hace falta moverlo** (§2.1) |
| Banda de abstención | `jpv_abstention_enabled`, `α` y `N` **sin tocar**. La regla ya decidía; este change la **propaga y la declara** |

---

## 1. Suites automáticas

La línea base se midió **antes de tocar una línea de código**, sobre el árbol limpio en `0ae0fdd`, que sólo contenía los artefactos del change. `git stash push -u` respondió *«No local changes to save»*, que es la condición correcta de línea base y no una omisión.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (`0ae0fdd`, sólo artefactos) | **1038 passed**, 0 failed, **0 skipped**, 336,1 s |
| `ai-service` al cerrar las 48 tareas | **1192 passed**, 0 failed, **0 skipped**, 323,4 s |
| `ai-service` re-ejecutada al abrir esta pasada de QA | **1192 passed**, 0 failed, **0 skipped**, 397,9 s |
| `ai-service` tras cerrar los tres huecos de §9.10 | **1195 passed**, 0 failed, **0 skipped**, 425,5 s |
| `openspec validate --all --strict` antes y después | **57 passed, 0 failed** en las dos puntas |
| `dotnet test` · `npm run test` | **no ejecutados**: fuera del diff. Ver §5 |

**+157 tests netos** sobre la línea base (1038 → 1195), y el reparto cuadra al caso: **159 identificadores de test nuevos menos dos retirados**, los dos parametrizaciones de `test_unimplemented_route_returns_501_when_stub_mode_off`:

- `[POST-/v1/assist/sale-body0]` **se va porque la ruta ya no responde 501**, que es el objeto del change. La propiedad no se borra: se **rehospeda**, como hizo C26 con substitutes, en `test_the_assistance_route_is_no_longer_left_answering_501`, que la afirma en negativo.
- `[POST-/v1/inventory/propose-body1]` **sigue existiendo, renombrado a `body0`**: al salir assist de la lista, inventario pasa a ser el primer parámetro. Comprobado **sobre el XML de JUnit de las dos pasadas**, no deducido.

### La comparación por nombres, que es la que vale

`CLAUDE.md` exige comparar por **nombres de test** y no por recuento. Ejecutado sobre los dos `--junitxml`:

```
ANTES    1038 tests | rojo 0 | skipped 0 | 336,1 s
DESPUES  1195 tests | rojo 0 | skipped 0 | 425,5 s

FAILING names NEW  (después − antes) : NONE
FAILING names GONE (antes − después) : NONE
SKIPPED                              : NONE

ids añadidos 159 · ids retirados 2 · delta neto +157
```

El conjunto de tests en rojo es **vacío en las dos puntas**. La suite de `ai-service` **no** es la de `backend/` ni la de `frontend/`, que `CLAUDE.md` advierte que llegan en rojo: ésta llega en verde, así que el criterio real es que no aparezca ningún nombre nuevo, y no aparece.

> **La duración importa tanto como el recuento, y por eso está en la tabla.** `CLAUDE.md` advierte que en este repositorio una pasada anormalmente corta significa que los Testcontainers no arrancaron y que el árbol de base de datos se omitió en bloque — lo que después se lee como una regresión catastrófica que no existe. **`skipped=0` en las tres pasadas** y duraciones del mismo orden dicen lo contrario: el demonio de Docker estaba accesible y los tests corrieron de verdad.

### Desglose de tests nuevos

| Fichero | Tests | Qué cubre |
|---|---:|---|
| `tests/assist/test_orchestrator.py` | **37** | Los tres modos y su `intent`; agrupación por familia con el invariante *familia nula ⇒ un miembro*, incluido el caso de **tres productos sin familia que no pueden compartir grupo**; el aviso de variantes disparando sobre un miembro que la recuperación **no** devolvió; la familia de uno que no lo dispara; el vocabulario cerrado en los cuatro modos de petición; la pieza con *bucket* cero que **no** produce aviso de stock ni filtra un *bucket*; el direccionamiento de M2 y su lista blanca y tope **por parámetro**; la abstención en sus tres formas —dispara, no silencia, y su configuración viaja por parámetro **y cae al default**—; los **tres** errores de pieza inservible, comprobando que son **tres frases distintas**; `pitch` vacío, `prompt_version` nulo y `usage` a cero en los tres modos; el ámbito del token; **ninguna búsqueda de similitud en M2**, **ninguna llamada a un LLM en ningún modo**, y la introspección de imports del paquete |
| `tests/assist/test_grounding.py` | **20** | La lista blanca comprobada **contra el corpus real**: las dos secciones existen y son `general` en **las nueve** fichas canónicas; `material-bano-de-oro` **sí** lleva una sección `establecimiento` —sin esa fila el invariante guardaría de nada—; la sección de piezas mixtas existe y es `general`; direccionamiento de uno y de dos materiales; el tope y la lista **por parámetro**; el sinónimo que resuelve a la ficha canónica; el material irresoluble que no direcciona nada; **el filtro de alcance que aguanta aunque se le pase la sección de compromiso por su nombre**; la cita con todos los campos de una buscada; la sección ausente que no rompe la llamada; cero llamadas al proveedor |
| `tests/api/test_assist_contract.py` | **18** | El bloque de contrato campo a campo: «al menos uno» nombrando los dos campos, `query` opcional pero no en blanco, `family_id` nulable y por defecto nulo, `match_reasons` con su default, los **seis** campos nuevos de `Citation` **uno a uno parametrizados**, `source` retirado, `abstained` obligatorio, `prompt_version` nulable, **`low_confidence` ausente del modelo**, el vocabulario de dos códigos sin espacios, los dos avisos de stock **no** en el vocabulario, y la descripción del campo `warnings` nombrándolos |
| `tests/knowledge/test_search_exclusion.py` | **16** | Exclusión ausente y vacía dando **los mismos fragmentos en el mismo orden**; el documento excluido que no aporta nada; **la exclusión llegando a la rama léxica**, comprobada también atacando la rama directamente; la cláusula presente sólo cuando se pide y **antes del `LIMIT`**; composición con la cláusula de `doc_type`; las nueve fichas canónicas; una pieza de un material excluyendo **ocho y nada más**; dos materiales excluyendo siete; la pieza sin material excluyendo **nada**; el sinónimo; el material desconocido; **diez documentos parametrizados que nunca se excluyen**; los dos con prefijo `material-` que no son fichas; el resto del corpus alcanzable; la ficha declarada alcanzable |
| `tests/api/test_assist_real.py` | **14** | La ruta real sobre `app.state`, sin abrir un socket: no responde 501 y el fixture sobrevive con stubs encendidos; **`DELIVERED_BY` ya no existe en el módulo**; ámbito del token contra cuerpo discrepante y 401 sin token; `pitch`/`prompt_version`/`usage` en los tres modos; `intent` siempre de los dos valores; **la línea de log con sus campos y sin un solo vector**; **precio y stock ausentes recorriendo la respuesta serializada entera por todos sus caminos**; los tres errores por HTTP como **422 con tres detalles distintos**; la petición sin anclajes; **las citas abriendo fichero y encabezado reales**; ninguna cita apuntando a un producto |
| `tests/retrieval/test_family_roster.py` | **12** *(1 `db`)* | Sólo los miembros de esa familia; `variant_label` y `family_name`; los inactivos fuera; el tope respetado y **declarado con su holgura medida**; el truncado **bajo el orden de la sentencia**, con `NULLS LAST`; la familia desconocida que es vacío y no error; el SQL que **no** nombra `public`, ni la proyección, ni `pos_id`, ni precio, ni stock, ni *bucket*; **una sola sentencia** con el tope acotado; el tope por debajo de uno rechazado; y **la sentencia real contra PostgreSQL**, que se omite si Docker no está |
| `tests/api/test_assist_stub.py` | **11** | El fixture ajustado: agrupa, **ejerce la familia ausente** con un solo miembro en cuatro tamaños de página, avisos del **vocabulario cerrado**, citas que parten en `documento#sección` con `claim_scope`, `intent` **estructural y no adivinado por la palabra «regalo»**, `abstained` y `prompt_version`, el rechazo sin anclajes, los *placeholders* intactos y el determinismo |
| `tests/assist/test_modes.py` | **10** | Los tres modos; ninguno de los dos anclajes como error nombrando ambos; **el blanco que no es un anclaje**, en los dos campos; el `intent` determinado sólo en el modo anclado; **cinco redacciones distintas dando un solo `intent`**; el vocabulario de dos valores cubriendo todos los modos |
| `tests/knowledge/test_addressing.py` | **9** | El fragmento direccionado con su cita completa; **indistinguible de uno buscado**, campo a campo contra el mismo fragmento obtenido por búsqueda; el `score` de 1 y por qué; ninguna búsqueda ni llamada al proveedor; la sección ausente que no rompe el resto; el documento desconocido; la lista vacía; **el orden preservado**; y la identidad resolviendo al `uuid5` que escribió el indexador |
| `tests/support/assist_world.py` · `tests/assist/conftest.py` | — | Identificadores **UUID reales** porque la capa los parsea, y el corpus real de 32 documentos en memoria: lo que se sustituye es el proveedor y el socket, no la lógica |

El reparto del diff, por zona y sin mezclar código con documentación:

| Zona | Diff sobre ficheros existentes | Ficheros nuevos |
|---|---|---|
| Producción (`src/` + `openapi.json`) | 9 ficheros · **+737 / −65** | **786 líneas** en `src/jbg_ai/assist/` (7 módulos) |
| Tests | 5 ficheros · **+225 / −17** | **2.347 líneas** en 8 ficheros nuevos |
| Documentación (`README`, `epicas`, plan, `CLAUDE.md`, `tasks.md`) | 5 ficheros · **+280 / −55** | el informe de implementación |

**Más línea de test nueva que de producción nueva, en proporción de 3 a 1.** No es celo: la mitad de lo que este change entrega son **invariantes** —ni prosa, ni proveedor, ni precio, ni stock, ni compromisos de la casa en un argumentario que nadie pidió— y un invariante que no tiene test es una convención.

---

## 2. Los tres spikes, corridos antes de escribir código

`tasks.md` los pone en el grupo 2 y el enunciado lo subraya: **el orden de los grupos es una dependencia, no una preferencia**, porque el resultado del spike 1 decidía cómo se implementa el grupo 5. Las cifras se escribieron **antes** de decidir sobre ellas, en [`c30a-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30a-implementation-measurements.md).

### 2.1. Spike 1 — el filtro de exclusión, en dos brazos

Contra el **índice vivo** y al **umbral de producción `0,51`**, no contra el sustituto *offline*. La pregunta era *«¿devuelve `0,51` citas espurias sobre consultas de producto?»*, y ésa es una pregunta sobre ese umbral y ningún otro: el embebedor *offline* vive en otra escala y obliga a `0,81`, así que habría contestado otra cosa.

Las 72 consultas se embebieron **una vez, en lote**, y las diez pasadas posteriores no hicieron **ninguna** llamada más: la caché acotada del cliente las sirvió todas. Es el hallazgo del spike 2 usado como herramienta antes de escribirlo.

| | brazo A (sin filtro) | brazo B (con filtro, media de 9 anclas) |
|---|---:|---:|
| Citas | **101** | **76,4** |
| Consultas que abstienen | **41 de 72** | **44,3 de 72** |
| Citas de ficha de material | 41 (40,6 %) | — |
| Citas de ficha **ajena** retiradas | — | **36,4** |

**Tres cosas decididas con la cifra delante:**

1. **El modo de consulta libre NO necesita umbral propio.** Era la opción por defecto declarada, y la medición la **sostiene** en vez de limitarse a no contradecirla: de 101 citas, **una** es inequívocamente espuria —`material-bano-de-oro` sobre *«un lingote de oro»*— y el umbral **ya abstiene en 41 de 72**. Endurecerlo costaría las 25 citas de `materiales`, las 21 de `sinonimos` y las 13 de `piedra`, que son las correctas. Las cinco consultas fuera de dominio que sí citan están **nombradas una a una** en el informe, con su veredicto.
2. **El filtro asimétrico hace lo que D8 dice y no lo que D8 temía.** Retira 36,4 citas de ficha ajena y sube las abstenciones sólo de 41 a 44,3: **no produce falsa abstención en masa**.
3. **Un efecto que el diseño no anticipó: el filtro no sólo borra, promueve.** Las 36,4 retiradas producen una caída neta de **24,6**, porque la cláusula filtra **antes del `LIMIT`** y unos **11,8 fragmentos correctos por ancla** ascienden desde debajo del corte.

### 2.2. Spike 2 — reutilización del vector de consulta

**Viable, y la costura ya existía.**

| Comprobación | Resultado |
|---|---|
| Mismo cliente | `search_knowledge(embed=…)` está tipado contra el **mismo** `EmbeddingClient` que resuelve la ruta de recuperación desde `app.state` |
| Misma dimensión | `EMBEDDING_DIM = 1536`, **una sola constante** leída por los dos caminos |
| Misma `model_version_key` | `openai/text-embedding-3-small:1536` por los dos lados, **carácter por carácter** |
| Los dos corpus | Sufijos distintos (`…:source-text/v1` y `…:knowledge/v1`) y **los dos casan** con el `LIKE '<modelo>:<dim>%'` de ambas sentencias |
| La reutilización, medida | Dos `embed()` del mismo texto → **1 sola llamada al proveedor**, la segunda con `cache_hits=1` y **vector idéntico** |
| **La trampa, medida** | La clave es `hash_source_text(text)`: **un espacio final es un fallo de caché**. Y `retrieve_products` embebe `payload.query` **tal cual** mientras `search_knowledge` embebe `question.strip()` |

**Consecuencia aplicada en el código:** `assist_sale` recorta el texto **una vez** y pasa el mismo a los dos, con el porqué escrito en el propio módulo. Sin eso, M3 pagaría un *embedding* por una diferencia invisible.

### 2.3. Spike 3 — cardinalidad de familia

| miembros | 2 | 3 | 4 | 5 | 8 |
|---|---:|---:|---:|---:|---:|
| familias | 44 | 52 | 56 | 3 | **1** |

**156 familias · 491 miembros · máximo 8 · media 3,15 · p95 4 · ninguna por encima de 8.**
Tope elegido: **24**, tres veces el máximo observado, fijado en `FAMILY_ROSTER_CAP` y **verificado por test** (`test_family_roster_cap_is_a_declared_value_with_measured_slack`).

---

## 3. Escenarios de las specs, uno a uno

**67 escenarios `#### Scenario:`** en **22 requisitos**, repartidos en cuatro deltas. Todos tienen test nombrado. **Tres de ellos sólo lo tenían por implicación y se les puso uno directo al redactar este documento** (§9.10).

### `assist-generation` — tres modos y anclajes (5)

| Escenario | Test | Resultado |
|---|---|---|
| A piece with no question is served as a piece-anchored assistance | `test_a_piece_with_no_question_is_served_as_one_group` | ✅ |
| A free query with no piece is served | `test_a_free_query_is_served_over_the_retrieved_candidates` | ✅ |
| A piece with a question is served as both | `test_a_piece_with_a_question_is_anchored_and_answers_the_question` | ✅ |
| A request with neither anchor is rejected | `test_neither_anchor_is_an_error_naming_both_fields` · `test_assist_request_without_any_anchor_is_rejected_naming_both_fields` · `test_a_request_with_neither_anchor_is_rejected_naming_both` | ✅ ×3 |
| The scope comes from the token and never from the body | `test_the_scope_applied_is_the_token_claim_and_never_the_body` · `test_the_scope_comes_from_the_token_and_never_from_the_body` | ✅ ✅ |

### `assist-generation` — el `intent` es estructural (2)

| Escenario | Test | Resultado |
|---|---|---|
| A piece with no question reports a determinate intent | `test_the_piece_anchored_mode_is_the_only_one_reporting_a_determinate_intent` | ✅ |
| A query reports an unclassified intent whatever it says | `test_two_queries_worded_differently_with_the_same_anchors_report_one_intent` (5 redacciones) · `test_two_wordings_with_the_same_anchors_report_the_same_intent` | ✅ ✅ |

### `assist-generation` — agrupación por familia (4)

| Escenario | Test | Resultado |
|---|---|---|
| Members of one family are grouped under it | `test_a_piece_with_a_family_is_grouped_under_it_with_its_variants` · `test_candidates_of_one_family_share_a_group_on_the_query_path` | ✅ ✅ |
| A product with no family is a group of one | `test_a_piece_with_no_family_is_a_group_of_exactly_one` | ✅ |
| No group with a null family carries more than one member | `test_no_group_with_a_null_family_ever_carries_more_than_one_member` (tres sin familia en un mismo resultado) · `test_assist_stub_never_groups_several_members_under_a_null_family` (4 tamaños de página) | ✅ ✅ |
| Each member carries the reasons it was retrieved for | `test_every_member_carries_the_match_reasons_the_retrieval_recorded` | ✅ |

### `assist-generation` — avisos como vocabulario cerrado (4)

| Escenario | Test | Resultado |
|---|---|---|
| A family with other members raises the variants warning | `test_the_variants_warning_fires_on_a_member_the_retrieval_did_not_return` | ✅ |
| A missing size label raises its warning | `test_a_missing_size_label_raises_its_warning` · `test_a_declared_size_label_raises_no_warning` | ✅ ✅ |
| Every warning belongs to the closed vocabulary | `test_every_warning_belongs_to_the_closed_vocabulary` (4 formas de petición) · `test_no_warning_code_is_a_sentence_in_natural_language` | ✅ ✅ |
| No stock warning is emitted by this service | `test_a_piece_out_of_stock_raises_no_stock_warning_and_leaks_no_bucket` · `test_no_stock_warning_is_emitted_by_this_service` | ✅ ✅ |

### `assist-generation` — el aviso sale del roster (3)

| Escenario | Test | Resultado |
|---|---|---|
| The warning fires on a member the retrieval did not return | `test_the_variants_warning_fires_on_a_member_the_retrieval_did_not_return` — familia de 4, la recuperación devuelve **1**, y comprueba además que se llamó al roster con el tope | ✅ |
| A family of one raises no variants warning | `test_a_family_of_one_raises_no_variants_warning` · `test_a_piece_with_no_family_raises_no_variants_warning` | ✅ ✅ |
| The roster is bounded | `test_family_roster_respects_the_declared_cap` · `test_family_roster_truncates_under_the_statement_order` · `test_family_roster_cap_is_a_declared_value_with_measured_slack` | ✅ ×3 |

### `assist-generation` — direccionamiento determinista en M2 (5)

| Escenario | Test | Resultado |
|---|---|---|
| The citations come from the declared materials' sheets | `test_the_citations_come_from_the_declared_material_sheet` · `test_the_piece_anchored_mode_cites_the_sheets_of_its_own_materials` | ✅ ✅ |
| No sheet of an undeclared material is cited | `test_no_sheet_of_an_undeclared_material_is_cited` | ✅ |
| A commitment of the establishment never enters an unrequested argument | `test_no_commitment_of_the_establishment_enters_an_unrequested_argument` · **`test_the_scope_filter_holds_even_if_the_allow_list_were_widened`** · `test_the_piece_anchored_mode_cites_no_establishment_claim` | ✅ ×3 |
| **No similarity search runs for this mode** | **`test_no_similarity_search_runs_for_the_piece_anchored_mode`** · `test_the_piece_anchored_mode_makes_no_provider_call` · `test_grounding_makes_no_provider_call_at_all` | ✅ (§9.10) |
| A piece declaring two materials also receives the mixed-piece guidance | `test_two_materials_add_the_mixed_piece_section` · `test_a_piece_of_two_materials_also_receives_the_mixed_piece_guidance` · `test_a_piece_over_the_cap_still_gets_the_mixed_piece_guidance` | ✅ ×3 |

### `assist-generation` — citas del corpus, nunca del catálogo (3)

| Escenario | Test | Resultado |
|---|---|---|
| A citation resolves and locates | `test_every_citation_resolves_to_a_real_document_and_heading` — abre el fichero y busca el encabezado por su título | ✅ |
| The claim scope travels with every citation | `test_assist_stub_citations_resolve_and_carry_their_claim_scope` · `test_a_citation_carries_every_field_a_searched_one_carries` · el mismo test anterior, que compara `claim_scope` contra el del corpus | ✅ ×3 |
| The catalogue is never cited | `test_no_citation_points_at_a_product_or_at_the_catalogue` | ✅ |

### `assist-generation` — abstención declarada (3)

| Escenario | Test | Resultado |
|---|---|---|
| An abstained query returns nothing and says so | `test_an_abstained_query_returns_no_group_and_says_so` | ✅ |
| An answerable query is not silenced | `test_an_answerable_query_is_not_silenced` | ✅ |
| The field is always present | `test_the_abstention_field_is_present_in_every_mode_and_false_when_anchored` · `test_assist_stub_declares_abstention_and_a_null_prompt_version` | ✅ ✅ |

### `assist-generation` — pieza inservible (4)

| Escenario | Test | Resultado |
|---|---|---|
| An unknown product is an error | `test_an_unknown_piece_is_an_error_naming_that_case` | ✅ |
| An inactive product is a different error | `test_an_inactive_piece_is_a_different_error` | ✅ |
| A product without an embedding is a third error | `test_a_piece_without_an_embedding_is_a_third_error` | ✅ |
| None of the three is served as an abstention | `test_the_three_unusable_cases_give_three_different_sentences` · `test_an_unusable_piece_is_a_422_and_never_a_200_with_abstained` | ✅ ✅ |

### `assist-generation` — ni prosa ni proveedor (2)

| Escenario | Test | Resultado |
|---|---|---|
| The argument is empty and its provenance absent | `test_the_argument_is_empty_its_provenance_absent_and_the_usage_zero` · `test_the_real_path_emits_an_empty_pitch_a_null_prompt_and_zero_usage` | ✅ ✅ |
| **No provider is called** | **`test_no_language_model_provider_is_called_in_any_mode`** · `test_the_assist_package_imports_no_provider_client` | ✅ (§9.10) |

### `assist-generation` — ni precio ni stock (1)

| Escenario | Test | Resultado |
|---|---|---|
| The whole response is free of price and stock figures | `test_no_field_of_the_response_carries_a_price_or_a_stock_figure` — recorre la respuesta serializada **entera**, con precio real y tres *buckets* en el índice | ✅ |

### `assist-generation` — la ruta real y el fixture (3)

| Escenario | Test | Resultado |
|---|---|---|
| The route no longer answers 501 with stubs disabled | `test_the_route_does_not_answer_501_with_stubs_disabled` · `test_the_assistance_route_is_no_longer_left_answering_501` | ✅ ✅ |
| The fixture stays deterministic | `test_assist_stub_is_deterministic` · `test_assist_sale_groups_by_family` (con `forbid_network`) | ✅ ✅ |
| The fixture exercises the absent family | `test_assist_stub_exercises_the_absent_family` | ✅ |

### `assist-generation` — los tests corren *offline* (2)

| Escenario | Test | Resultado |
|---|---|---|
| No external call is made by the suite | `forbid_network` sobre el fixture; `LocalEmbeddingClient.calls` y `_RefusingIndex` en la capa; introspección de imports. **Y la evidencia global: 1195 tests sin una sola clave de proveedor en el entorno de la suite** | ✅ |
| Database tests skip when the container is unavailable | `test_family_roster_against_postgres` pide el fixture `migrated`, que llama a `pytest.skip` cuando el demonio no está. **Comprobado que en esta máquina NO saltó**: `skipped=0` en las tres pasadas | ✅ |

### `ai-service-api-contracts` (9)

| Escenario | Test | Resultado |
|---|---|---|
| Assist response groups members under a family | `test_assist_sale_groups_by_family` | ✅ |
| A group without a family carries a single member | `test_assist_stub_never_groups_several_members_under_a_null_family` | ✅ |
| The request requires at least one anchor | `test_assist_sale_rejects_a_request_with_neither_anchor` | ✅ |
| Citations carry their identifier and their claim scope | `test_assist_stub_citations_resolve_and_carry_their_claim_scope` · `test_citation_exposes_its_six_new_fields` · `test_citation_requires_every_new_field` (6 parametrizaciones) | ✅ ×3 |
| The response declares abstention and prompt provenance | `test_assist_stub_declares_abstention_and_a_null_prompt_version` · `test_assist_response_requires_abstained` · `test_assist_response_prompt_version_defaults_to_null` | ✅ ×3 |
| Pitch keeps placeholders unresolved | `test_assist_sale_groups_by_family` · `test_pitch_never_resolves_price_or_stock` | ✅ ✅ |
| No field of the response carries a price or a stock figure | `test_no_field_of_the_response_carries_a_price_or_a_stock_figure` | ✅ |
| The assistance route no longer answers 501 | `test_the_route_does_not_answer_501_with_stubs_disabled` | ✅ |
| A route that is still unimplemented keeps answering 501 | `test_unimplemented_route_returns_501_when_stub_mode_off[POST-/v1/inventory/propose-body0]` · `test_501_message_names_the_delivering_change` (exige el literal `C35`) | ✅ ✅ |

### `knowledge-corpus` — exclusión por documento (4)

| Escenario | Test | Resultado |
|---|---|---|
| An excluded document contributes no fragment | `test_an_excluded_document_contributes_no_fragment` | ✅ |
| The exclusion reaches the lexical branch too | `test_the_exclusion_reaches_the_lexical_branch_too` — comprueba el híbrido, el vector-only **y ataca la rama léxica directamente** | ✅ |
| An empty exclusion set changes nothing | `test_an_absent_and_an_empty_exclusion_set_return_the_same_fragments_in_order` — compara identificadores **y puntuaciones**, en orden | ✅ |
| The exclusion is addressed by document identity | `test_a_piece_of_one_material_excludes_the_other_eight_and_nothing_else` (vía `document_id`) · `test_both_compiled_statements_carry_the_clause_only_when_asked` (sobre `d.id`, sin columna nueva) | ✅ ✅ |

### `knowledge-corpus` — el filtro asimétrico por pieza (4)

| Escenario | Test | Resultado |
|---|---|---|
| The sheet of an undeclared material is unreachable | `test_no_sheet_of_an_undeclared_material_survives_the_piece_scoped_set` (3 preguntas) · `test_a_question_about_the_piece_never_cites_another_materials_sheet` | ✅ ✅ |
| The declared material's own sheet stays reachable | `test_the_declared_material_sheet_stays_reachable` | ✅ |
| The rest of the corpus stays reachable | `test_the_rest_of_the_corpus_is_still_reachable_with_a_piece_scoped_set` · `test_the_piece_scoped_set_never_excludes_a_document_that_is_not_a_sheet` (**10 documentos parametrizados**) | ✅ ✅ |
| The prefixed documents that are not material sheets stay reachable | `test_the_two_prefixed_documents_that_are_not_sheets_stay_reachable` — comprueba además que **llevan `doc_type: material`** y aun así pasan | ✅ |

### `knowledge-corpus` — direccionamiento por identidad (3)

| Escenario | Test | Resultado |
|---|---|---|
| An addressed fragment comes back with its full citation | `test_an_addressed_fragment_comes_back_with_its_full_citation` · **`test_an_addressed_fragment_is_indistinguishable_from_a_searched_one`**, campo a campo contra el mismo fragmento obtenido buscando | ✅ ✅ |
| Addressing runs no search and no provider call | `test_addressing_runs_no_search_and_makes_no_provider_call` · `test_no_similarity_search_runs_for_the_piece_anchored_mode` | ✅ ✅ |
| An absent section is not an error | `test_an_absent_section_yields_nothing_and_the_rest_resolve` (sobre `material-acero`, que tiene cuatro secciones y no seis) · `test_an_unknown_document_yields_nothing_at_all` | ✅ ✅ |

### `retrieval-abstention` (6)

| Escenario | Test | Resultado |
|---|---|---|
| An abstained query yields no group on the assistance path | `test_an_abstained_query_returns_no_group_and_says_so` | ✅ |
| The cross-branch signal is not repurposed | `test_assist_response_does_not_reuse_low_confidence_for_abstention` — el campo **no existe** en el modelo, así que no puede reutilizarse por descuido | ✅ |
| An answerable query is not silenced on the assistance path | `test_an_answerable_query_is_not_silenced` | ✅ |
| A consuming path can be driven with a configuration of its own | `test_the_abstention_configuration_travels_by_parameter` — **dos llamadas en un mismo proceso** con configuraciones opuestas | ✅ |
| **Absent parameters fall back to the configured default** | **`test_an_absent_abstention_parameter_falls_back_to_the_configured_default`** | ✅ (§9.10) |
| An unusable anchor is an error and not an abstention | `test_an_unusable_piece_is_a_422_and_never_a_200_with_abstained` | ✅ |

---

## 4. Las validaciones que `tasks.md` exige, tarea a tarea

A diferencia de C23 y C24, las 48 tareas de C30a **no nombran tests literalmente**: cada una declara su *«Validación:»* en prosa. La tabla las recorre y nombra qué la satisface.

| Grupo | Validación pedida | Evidencia |
|---|---|---|
| **1.1** | Fichero de nombres y **duración** anotada | `baseline-junit.xml` con 1038 nombres, 0 en rojo · 336,1 s · `skipped=0` |
| **1.2** | `0 failed` antes de tocar código | **57 passed, 0 failed** |
| **1.3** | `git_sha` y hash de `openapi.json` | `0ae0fdd999b0e7cc…` · `sha256 cec649272cbd7546…` |
| **2.1** | Tabla de dos columnas escrita **antes** de fijar el umbral | §2.1, con el recuento de espurias **por categoría** y las cinco fuera de dominio nombradas |
| **2.2** | Afirmación con la evidencia delante y la costura identificada | §2.2, con la trampa del espacio final **medida** |
| **2.3** | Cifra máxima y tope con su holgura | §2.3 · máximo **8**, tope **24** |
| **2.4** | Informe con las tres secciones | [`c30a-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30a-implementation-measurements.md) §1-§3 |
| **3.1** | Error nombrando los dos campos | `test_assist_request_without_any_anchor_is_rejected_naming_both_fields` |
| **3.2** | El modelo acepta `None` | `test_assist_group_accepts_a_null_family_id` |
| **3.3** | Campo presente, default lista vacía | `test_assist_group_member_defaults_match_reasons_to_an_empty_list` |
| **3.4** | Seis campos obligatorios, `source` ausente | `test_citation_requires_every_new_field` (parametrizado ×6) · `test_citation_no_longer_carries_a_free_text_source` |
| **3.5** | `abstained` obligatorio, `prompt_version` nulable | `test_assist_response_requires_abstained` · `test_assist_response_prompt_version_defaults_to_null` |
| **3.6** | Dos miembros, ninguno con espacios | `test_warning_vocabulary_holds_exactly_two_codes` · `test_no_warning_code_is_a_sentence_in_natural_language` |
| **3.7** | Determinista y con familia nula | `test_assist_stub_is_deterministic` · `test_assist_stub_exercises_the_absent_family` |
| **3.8** | Snapshot en verde y diff revisado campo a campo | `test_openapi_snapshot_is_stable` ✅ · §6 |
| **4.1** | Protocolo declara el método; `mypy`/`ruff` pasan | Método declarado ✅ · **`mypy` y `ruff` no existen en este repositorio** → §9.3 |
| **4.2** | Testcontainers, con omisión si no hay Docker | `test_family_roster_against_postgres` · ejecutado de verdad, `skipped=0` |
| **4.3** | Los tests de retrieval siguen pasando | `tests/retrieval` **267 passed** |
| **4.4** | No lee `public` | `test_family_roster_sql_reads_only_the_index_schema` · grep del §5 |
| **5.1** | Ausente y vacío dan lo mismo, en orden | `test_an_absent_and_an_empty_exclusion_set_return_the_same_fragments_in_order` |
| **5.2** | Excluido por **ninguna de las dos ramas** | `test_the_exclusion_reaches_the_lexical_branch_too` |
| **5.3** | Ocho fichas y ninguna más | `test_a_piece_of_one_material_excludes_the_other_eight_and_nothing_else` |
| **5.4** | Test explícito por cada grupo que pasa | `test_the_piece_scoped_set_never_excludes_a_document_that_is_not_a_sheet`, **10 parametrizaciones** |
| **5.5** | `alembic` sin revisión nueva, `migrations/` sin diff | `alembic heads` → `d7c4e91b25a0` · `git status` vacío |
| **6.1** | Tres modos y el error sin anclajes | `tests/assist/test_modes.py`, 10 tests |
| **6.2** | Dos redacciones, un `intent` | `test_two_queries_worded_differently_with_the_same_anchors_report_one_intent` (5 redacciones) |
| **6.3** | Familia presente, ausente, y el invariante | tres tests de `test_orchestrator.py` |
| **6.4** | Dispara con un miembro **no** devuelto; familia de uno no | `test_the_variants_warning_fires_on_a_member_the_retrieval_did_not_return` · `test_a_family_of_one_raises_no_variants_warning` |
| **6.5** | *Bucket* cero sin aviso ni *bucket* en la respuesta | `test_a_piece_out_of_stock_raises_no_stock_warning_and_leaks_no_bucket` |
| **6.6** | Fichas declaradas, sin `establecimiento`, sin proveedor | tres tests, más `test_no_similarity_search_runs_for_the_piece_anchored_mode` |
| **6.7** | Abstenida, contestable, y presente en los tres modos | tres tests, más el *fallback* al default |
| **6.8** | Tres respuestas distintas, ninguna 200 con `abstained` | `test_the_three_unusable_cases_give_three_different_sentences` · `test_an_unusable_piece_is_a_422_and_never_a_200_with_abstained` |
| **6.9** | Introspección de imports | `test_the_assist_package_imports_no_provider_client` |
| **7.1** | Sin stubs no es 501; con stubs, fixture | `test_the_route_does_not_answer_501_with_stubs_disabled` · `test_stub_mode_still_serves_the_fixture` · `test_the_delivering_change_constant_is_gone_from_the_module` |
| **7.2** | Token contra cuerpo, y 401 sin token | `test_the_scope_comes_from_the_token_and_never_from_the_body` · `test_a_call_without_a_token_is_rejected` |
| **7.3** | Los tres valores con stubs apagados | `test_the_real_path_emits_an_empty_pitch_a_null_prompt_and_zero_usage` |
| **7.4** | Log con esos campos y **ningún vector** | `test_the_log_line_reports_the_decision_and_carries_no_vector` |
| **7.5** | Recorrer la respuesta serializada | `test_no_field_of_the_response_carries_a_price_or_a_stock_figure` |
| **8.1-8.5** | §1, §5, §6, §10 de este documento | ✅ |
| **9.1-9.5** | §11 de este documento | ✅ |

---

## 5. Alcance negativo

```bash
git status --short -- frontend/ terraform/ .github/ backend/ \
  ai-service/migrations/ ai-service/src/jbg_ai/enrichment/ \
  ai-service/prompts/ data/
```

Salida **vacía**.

| Guardarraíl | Comprobación | Resultado |
|---|---|---|
| `backend/` · `frontend/` · `terraform/` · `.github/workflows/` | `git status` vacío. **Ésta es la razón por la que no se ejecutan `dotnet test` ni `npm run test`**, y es lo que el DoD del ticket pide | ✅ |
| `ai-service/migrations/` | Vacío · `alembic heads` devuelve **la misma revisión** que antes del change | ✅ |
| `ai-service/src/jbg_ai/enrichment/` | Vacío. `vocabularies.yaml` se **lee** para derivar las nueve fichas; tocarlo forzaría bump de prompt y re-enriquecimiento | ✅ |
| `ai-service/prompts/` | Vacío. Este change no escribe prosa, así que no tiene prompt | ✅ |
| `data/knowledge/` | Vacío. El corpus se **lee** y se direcciona; ni una línea de contenido cambia | ✅ |
| `indexing/embeddings.py` | `git diff` vacío **y** hash SHA-256 fijado por `test_embeddings_module_is_untouched` | ✅ |
| **Esquema `public` desde Python** | `grep -n "public\." ` sobre las tres unidades con SQL nuevo → **ninguna coincidencia**, más el test dedicado del roster | ✅ |
| **DDL en el paquete nuevo** | `grep -rniE "create table\|alter table\|drop table\|create index\|add column" src/jbg_ai/assist/` → **ninguna** | ✅ |
| **Precio, stock y `qty_bucket` leídos por assist** | `grep -rn "qty_bucket\|\.price\|sales_30d" src/jbg_ai/assist/` → **ninguno**. No es que no se emitan: **no se leen** | ✅ |
| **Cliente de proveedor importado por assist** | `grep -rn "litellm\|openai\|anthropic\|httpx\|aiohttp" src/jbg_ai/assist/` → **ninguno**, más la introspección del grafo de módulos | ✅ |
| Ruta `/v1` nueva | **ninguna**: 11 rutas antes y 11 después, mismo conjunto (§6) | ✅ |

**Diff total: 19 ficheros modificados (+1.242 / −137) y 4 árboles/ficheros nuevos.** Todo dentro de `ai-service/`, `openspec/changes/<change>/` y `Documentos/`.

> **Una excepción declarada al alcance del ticket.** La tabla de estado del ticket dice que `retrieval/orchestrator.py` *«se consume, no se modifica»*. **Se modifica**, en 14 líneas de las que 12 son comentario. El porqué está en §9.2, y la alternativa —inferir la abstención de `low_confidence`— es exactamente lo que D9 prohíbe.

---

## 6. El contrato, **movido**, y exactamente dónde

A diferencia de C23 y C24, aquí `openapi.json` **sí se regenera**. Comprobado por **construcción** y no por lectura:

```python
live = create_app(canonical_openapi_settings()).openapi()
live == json.load(open("openapi.json"))     # True
```

Y el diff contra el snapshot anterior, **campo a campo** como pedía la tarea 3.8:

```
rutas          : 11 → 11   ·  mismo conjunto        ·  rutas con diff: NINGUNA
esquemas       : 46 → 46   ·  añadidos: []  ·  retirados: []
esquemas MOVIDOS: AssistGroup · AssistGroupMember · AssistRequest · AssistResponse · Citation
resto del documento: IDÉNTICO
```

**Cinco esquemas, cero rutas.** Las otras nueve rutas del contrato congelado quedan byte a byte como estaban, que es la condición que la tarea 3.8 exige y el riesgo que el diseño declaraba —*«la regeneración arrastra cambios no intencionados del perfil canónico»*—. Regenerado con `canonical_openapi_settings()`, el perfil documentado.

El movimiento, campo a campo:

| Esquema | `required` antes → después | Añadido | Retirado |
|---|---|---|---|
| `AssistRequest` | `["query"]` → **ninguno** | `product_id`; `query` pasa a `anyOf[string, null]` | — |
| `AssistGroup` | `["family_id","members"]` → `["members"]` | `family_id` pasa a `anyOf[string, null]` | — |
| `AssistGroupMember` | sin cambio | `match_reasons` | — |
| `Citation` | `["source","snippet"]` → `["citation_id","document_title","section_title","doc_type","claim_scope","score","snippet"]` | seis campos | **`source`** |
| `AssistResponse` | `+ abstained` | `abstained`, `prompt_version` | — |

> **Una limitación del snapshot, declarada porque no se puede expresar y sí se puede aclarar.** «Al menos uno de `product_id` y `query`» vive en un `model_validator` de Pydantic y **no es expresable en el JSON Schema que FastAPI emite**: tras el cambio, `AssistRequest` no declara `required`, así que un generador de cliente que lea sólo el esquema aceptará `{}`. En ejecución eso es un **422 que nombra los dos campos**, y la regla está escrita en la `description` del modelo, que sí viaja en el snapshot. Se deja así a propósito: meter un `anyOf` en la raíz del esquema es justo el tipo de forma que los generadores de cliente .NET manejan mal, y el coste de no expresarla es un mensaje de error en vez de un fallo de compilación.

---

## 7. Decisiones de diseño, verificadas en código

| Decisión | Evidencia |
|---|---|
| **D1** · El contrato se renegocia ahora, en bloque | §6: cinco esquemas en un solo movimiento, cero rutas. `IAiGatewayClient` sigue sin método de assist, así que el impacto real es cero |
| **D2** · «Al menos uno», no «exactamente uno» | `AssistRequest._requires_an_anchor` · `test_assist_request_accepts_each_anchor_on_its_own_and_both_together` — los tres modos existen y M3 es servible |
| **D3** · `intent` estructural, sin palabras clave | `AssistMode.intent` es una propiedad de la **forma**, no de la consulta. `test_two_queries_worded_differently_with_the_same_anchors_report_one_intent` lo ataca con cinco redacciones, «REGALO» incluida |
| **D4** · Agrupar y avisar son consultas distintas | `family_roster` existe como método del puerto y el aviso lo consume. `test_the_variants_warning_fires_on_a_member_the_retrieval_did_not_return` es la demostración: 4 en la familia, **1** recuperado, aviso disparado |
| **D5** · Códigos cerrados; los de stock no son de aquí | `ASSIST_WARNING_CODES` de dos miembros · `test_the_two_stock_warnings_are_not_part_of_this_vocabulary` · y el paquete **no lee** `qty_bucket` (§5) |
| **D6** · Cita con identificador resoluble y alcance | `Citation` con seis campos obligatorios · `test_every_citation_resolves_to_a_real_document_and_heading` abre fichero y encabezado · `test_no_citation_points_at_a_product_or_at_the_catalogue` |
| **D7** · En M2 se direcciona, no se busca | `_RefusingIndex` hace fallar el test si cualquiera de las dos ramas se toca · la lista blanca y el tope viajan **por parámetro**, con test · **sólo `general`**, y el filtro aguanta aunque se le pase la sección de compromiso por su nombre |
| **D8** · Filtro asimétrico en M1/M3 | Cláusula condicional sobre `d.id` en **las dos** sentencias, con la misma forma que `_DOC_TYPE_CLAUSE` · el conjunto se construye **enumerando las nueve a excluir** · 10 documentos parametrizados que nunca se excluyen · **y las cifras del §2.1** |
| **D9** · La abstención se honra y se declara | `abstained` en el modelo, `low_confidence` **ausente** · la configuración **por parámetro** y con *fallback* medido · `on_abstention` en el orquestador (§9.2) |
| **D10** · Pieza inservible es error, no abstención | `UnusableAnchorProductError` con tres causas · 422 con **tres detalles distintos**, comprobado por conjunto |
| **D11** · El fixture sobrevive y gana un grupo sin familia | `_ASSIST_FAMILYLESS_EVERY = 4`, con el índice 0 siempre sin familia → **cualquier `top_k` ejerce el caso nulo**. Comprobado en 1, 2, 5 y 20 |

---

## 8. Mediciones

Las tres del §2, más lo que la implementación midió después. Todo en [`c30a-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30a-implementation-measurements.md).

### 8.1. Lo que la medición **no** demuestra, dicho aquí

- **Las 72 consultas del golden set son de catálogo, no preguntas de mostrador.** El spike 1 midió exactamente lo que quería medir —M1 y M3 sobre consultas de producto— y **no dice nada** sobre preguntas de conocimiento, que C23 ya midió por su cuenta. El ancla del brazo B es **hipotética**, y por eso se barrieron las nueve.
- **El brazo B no es M3 real.** Simula el filtro sobre consultas que nadie formuló con una pieza en la mano. Es la mejor aproximación disponible hoy, porque el modo M3 no tenía consumidor hasta este change.
- **El tope del roster no se ha ejercitado con una familia real que lo alcance**, porque no existe: el máximo es 8 contra un tope de 24. Lo que sí está ejercitado es el **mecanismo** de truncado, con topes artificiales de 2 y 3 y bajo el orden de la sentencia.
- **La atribución cruzada entre los materiales que la pieza SÍ declara sigue sin resolverse**, y ningún filtro puede: las dos fichas son correctas. Está mitigada (tope de 2, sección de piezas mixtas, etiquetado por material) y **declarada** como límite del modo, no cerrada.

---

## 9. Incidencias de esta pasada

### 9.1. El diseño cita 486 miembros y «familias de 7 y 8»; son 491 y no hay ninguna de 7

Medido sobre el índice vivo: **491 miembros** —cinco más que la cifra de C18b, por sincronizaciones posteriores— y los tamaños presentes son **2, 3, 4, 5 y 8**. El número de familias (156) y la media (~3,1) sí coinciden. No mueve la decisión, porque el tope se fija sobre el **máximo**, que sigue siendo 8. Se anota porque una ficha que nombra un tamaño inexistente invita a construir un test sobre él.

### 9.2. El ticket afirmaba que el orquestador de recuperación no se modificaba

**Es falso, y hubo que corregirlo.** La decisión de abstención **no es recuperable desde `RetrievalResponse`**: un `results` vacío es también lo que produce una consulta que simplemente no encontró nada, y el único campo que se mueve con la abstención —`low_confidence`— tiene un significado **medido y anticorrelacionado** (1 de 20 fuera de dominio contra 10 de 43 contestables), que es justo lo que D9 prohíbe reutilizar.

Se añade **una costura aditiva de observabilidad**, `on_abstention`, con la misma forma y el mismo motivo que el `on_fused_candidates` que ya existía para el arnés de evaluación: **14 líneas, 12 de ellas comentario**, cero cambios de comportamiento, y una llamada que no la pasa ve la función de siempre.

Lo que **no** hizo falta, y el ticket daba por necesario: sacar `size_label` del candidato interno. `source_document` ya lo devuelve, así que los tres modos leen la pieza foco por la misma puerta.

### 9.3. La tarea 4.1 exige que pasen `mypy` y `ruff`, que no existen en este repositorio

Ni están en `pyproject.toml`, ni hay configuración de ninguno de los dos, ni `.github/workflows/` tiene flujo de `ai-service`. La puerta real es `uv run pytest`, y es la que se ha usado. La tarea pedía una comprobación contra una herramienta que el proyecto no tiene.

### 9.4. Un hueco que los artefactos dejaron sin decidir: a qué pieza describen los avisos

Ni la HU ni el diseño lo dicen. Los dos hablan de *«el producto»* en singular, y en M2/M3 es inequívoco: la pieza anclada. **En M1 no hay pieza anclada**, y sin embargo el escenario 3 de la historia exige que el aviso de variantes dispare cuando *«la recuperación sólo devolvió dos»*, que sólo puede ser M1.

**Decisión tomada y declarada:** los avisos describen la **pieza foco** — la anclada en M2/M3, y el primer miembro del primer grupo en M1, que es el candidato mejor clasificado y la pieza que la respuesta encabeza. Las dos alternativas se descartaron con motivo: *«alguno de los candidatos»* haría que `size_label_missing` disparase en cuanto una de quince piezas no declarase talla —casi siempre, y por tanto sin información—, y *no emitir avisos en M1* contradice el escenario 3.

### 9.5. El vocabulario cerrado obliga a mover el fixture, y la tarea no lo decía

El invariante dice *«every warning **any response** carries belongs to the closed vocabulary»*, y el fixture emite una. `assist_sale_stub` emitía `STUB_WARNING`, **una frase en castellano**. Sustituido por códigos del vocabulario; y por la misma razón el `intent` del fixture pasó de `gift_search`/`product_search` —una heurística por la palabra «regalo»— a la **misma regla estructural** que usa el camino real, para que un cliente aprenda una sola regla. La tarea 3.7 sólo pedía el grupo sin familia y las citas de seis campos.

### 9.6. `piece_scoped_exclusions([])` excluía las nueve fichas

Leído literalmente, *«excluye lo que la pieza no declara»* excluye las nueve cuando la pieza no declara nada — y se lleva por delante todo el corpus de materiales. **Lo detectó un test escrito contra la intención documentada**, no contra el código. Corregido: sin material que acotar no hay nada de lo que proteger a la pregunta, y la respuesta honesta es el corpus sin filtrar.

### 9.7. Dos tests de C23 vigilaban su invariante con un proxy que dejó de valer

`test_knowledge_opens_no_http_surface` y su gemelo buscaban la subcadena `knowledge` **en todo el snapshot, prosa incluida**. C30a le da a una descripción publicada un motivo legítimo para nombrar el corpus: `Citation` se documenta como *«a fragment of the knowledge corpus»*, que es exactamente lo que el lado .NET necesita leer para pintarla con honestidad.

**Afilados, no debilitados**: ahora comprueban **rutas, nombres de esquema, `tags` y `operationId`**, que es donde una superficie HTTP aparecería. Mantener la forma antigua habría obligado a escribir una descripción vaga para satisfacer una búsqueda de texto.

### 9.8. El certificado: `--system-certs` arregla a `uv`, no al proceso Python

`CLAUDE.md` recoge que `uv sync` y `uv run` necesitan `--system-certs`. **Eso no cubre el runtime**: `litellm` sale por `aiohttp`/`httpx`, que usan el bundle de `certifi` y **no** el almacén de Windows, y esta máquina tiene un MITM de **Norton Web/Mail Shield** cuya raíz vive sólo ahí. Toda llamada real al proveedor muere con `CERTIFICATE_VERIFY_FAILED`.

La salida: exportar el almacén a un PEM y apuntar `SSL_CERT_FILE` y `REQUESTS_CA_BUNDLE` a él. **Y un detalle que costó un intento**: filtrar por la bandera de confianza deja fuera la raíz de Norton y el bundle sale incompleto — hay que concatenar todos los certificados de `ROOT` y `CA`. **No afecta a ningún test**: ninguno llama al proveedor. Anotado en `CLAUDE.md`.

### 9.9. `psycopg` rechaza el bucle de eventos por defecto de Windows

Cualquier script suelto que abra el motor asíncrono muere con *«cannot use the 'ProactorEventLoop'»*. En los tests ya lo resuelve `support/async_db.run_db`, que además dispone el motor a ambos lados — el motor es de proceso y sus conexiones pertenecen al bucle que las abrió, así que **dos `asyncio.run` en un mismo test fallan con `InterfaceError`**. El test `db` del roster se escribió primero con dos y falló por eso, no por el SQL. Anotado en `CLAUDE.md`.

### 9.10. Tres escenarios cuya cobertura era indirecta, y este documento los destapó

Recorrer los 67 escenarios uno a uno es lo que un recuento verde no hace. Tres estaban cubiertos **por implicación** y no por un test que afirmara la propiedad:

| Escenario | Qué había | Qué faltaba | Test nuevo |
|---|---|---|---|
| *No similarity search runs for this mode* | `embed.calls == []` | Que no se **compute** un vector no prueba que no **corra** una búsqueda: el índice en memoria no llama al proveedor para buscar | `test_no_similarity_search_runs_for_the_piece_anchored_mode`, con un índice que **falla ruidosamente** si se toca cualquiera de las dos ramas |
| *No provider is called* | Introspección de imports | La introspección prueba que el módulo no importa el cliente; no prueba que nadie lo alcance en ejecución | `test_no_language_model_provider_is_called_in_any_mode`, parcheando `litellm.acompletion` para que reviente, en los tres modos |
| *Absent parameters fall back to the configured default* | Tests con `abstain` explícito, y el resto llamando sin él | Nadie afirmaba que el valor **venía de `Settings`**: los demás tests pasaban por el *default* sin comprobarlo | `test_an_absent_abstention_parameter_falls_back_to_the_configured_default`, con el mismo perfil plano y dos configuraciones |

Los tres pasan. **+3 tests**, 1192 → **1195**.

### 9.11. Dos identificadores de test desaparecen, y ninguno es cobertura perdida

Ver §1. El de assist **se rehospeda** en afirmación negativa, como hizo C26; el de inventario **sigue existiendo** con el índice de parámetro corrido. Comprobado sobre el XML de las dos pasadas, no deducido de la aritmética.

### 9.12. La evidencia del §10 devolvió 503 en su primer intento, y fue correcto

El primer intento usó el `pos_id` del token de test, que **la proyección local no carga**. `resolve_scope` trata un surtido vacío como fallo de dependencia y devuelve 503 — el comportamiento que C22 define. Repetido con un punto de venta real (1.082 filas asignadas). **No es un defecto y no se ha cambiado nada por ello**; se anota porque un 503 en una pasada de evidencia se lee como un fallo del change si no se sabe de dónde sale.

### 9.13. El test `db` chocó con un `CHECK` del esquema antes de probar nada

`ck_product_document_text_provenance` admite `'merchant' | 'ai_assisted' | 'synthetic'`, y la inserción del test usaba `'generated'`. Falló al insertar, no al leer. Corregido en el test; **ninguna implicación para el código**, y se anota porque un `IntegrityError` en un test nuevo invita a sospechar del SQL bajo prueba.

---

## 10. Verificado a mano

- **La ruta real contra el Postgres local, en los tres modos, sin un solo fake.** La aplicación resuelve `SqlAlchemyProductSearch`, `SqlAlchemyKnowledgeIndex` y el `LiteLlmEmbeddingClient` real. Los tres devuelven **200**.
- **Las 15 citas de M2 y M3 resuelven a fichero y número de línea**, comprobado abriendo el fichero y buscando el encabezado por su título:

  | cita | fichero | línea | alcance |
  |---|---|---:|---|
  | `material-plata#cuidados-y-limpieza-en-casa` | `data/knowledge/material-plata.md` | 21 | general |
  | `material-plata#piel-sensible-y-alergias` | `data/knowledge/material-plata.md` | 54 | general |
  | `material-bano-de-oro#cuidados-y-limpieza-en-casa` | `data/knowledge/material-bano-de-oro.md` | 21 | general |
  | `material-bano-de-oro#piel-sensible-y-alergias` | `data/knowledge/material-bano-de-oro.md` | 50 | general |
  | `material-piezas-mixtas#limpiar-una-pieza-mixta-sin-estropear-nada` | `data/knowledge/material-piezas-mixtas.md` | 72 | general |

- **Lo que NO salió es la mitad de la evidencia.** La pieza de la prueba es de `plata` + `baño de oro`, y `material-bano-de-oro` tiene una **séptima sección** —«Nuestra garantía sobre el baño», `claim_scope: establecimiento`— en la **línea 94 del mismo fichero que sí se citó**. Pidió su argumentario y **no salió**. Es el escalón de D7, medido sobre la única pieza del catálogo que lo tiene.
- **El escenario 3 de la historia, sucediendo en vivo.** En M1 el primer grupo trajo **4** miembros de una familia que el roster declara de **8**, y el aviso disparó por el roster.
- **M3 sobre la familia de 8**, la mayor del índice: `family_label` relleno, ocho `variant_label` distintos, **8 documentos excluidos** y **cinco citas, ninguna de las ocho fichas excluidas**, alcanzando **cuatro secciones** de la ficha correcta — no las dos de la lista blanca de M2. Es la diferencia entre direccionar y buscar, vista en la misma pieza.
- **La comprobación de frontera sobre el cuerpo serializado completo** de las tres respuestas: sin `price`, sin `stock`, sin `qty_bucket`, `pitch` vacío, `prompt_version` nulo y `usage` a cero.
- **El diff de `retrieval/orchestrator.py` leído entero**, línea a línea, para confirmar que las 14 líneas son la costura y nada más.
- `\d ai.product_document` contra la base local, leído entero, antes de escribir `FAMILY_ROSTER_SQL`: confirma que `family_name` está denormalizado en cada fila, que es lo que permite traer la etiqueta del grupo **sin una segunda lectura**.
- **La lista blanca comprobada contra los ficheros**, no contra el diseño: `grep '^## \|claim_scope'` sobre las nueve fichas canónicas, leído entero, confirmando que las dos secciones existen y son `general` en las nueve, y que la séptima de `baño de oro` es la única `establecimiento` del conjunto.
- `git stash push -u` respondió *«No local changes to save»*, y se comprobó con `git status --short` que el árbol estaba efectivamente limpio antes de medir la línea base.

---

## 11. Documentación de contexto

| Documento | Qué se alineó |
|---|---|
| `ai-service/README.md` | Sección nueva **«Structured sale assistance (C30a)»** con los tres modos, el vocabulario cerrado, el roster, el filtro asimétrico **con sus cifras** y lo que la capa nunca hace; fila de `/v1/assist/sale` en la tabla de rutas; **`## Stubs and 501` reescrito**: una sola ruta sigue en 501 y se nombra; `assist/` en el árbol de `src` y de `tests`; `knowledge/` ampliado con la exclusión y el direccionamiento; y los no-objetivos con la mitad que entrega C30a y la que no |
| `Documentos/epicas.md` | Párrafo nuevo en **EP15** con lo que la implementación midió, los tres spikes y las dos refutaciones que pesan; fila de resumen con **C30a (implementado, sin archivar)** |
| Plan de changes, §0 | Entrada nueva del **2026-09-13** con la tabla de los tres spikes, el efecto de promoción que el diseño no anticipó, las dos refutaciones y la corrección de las dos cifras |
| Plan de changes, §2 y §3 | Estado de C30a a **🟢 implementado**; recuento de pendientes matizado; **ficha de C34 revisada** con los cuatro hechos del contrato nuevo que su implementación necesitará; **ficha de C36 revisada** con las dos garantías que ahora tiene |
| `CLAUDE.md` | La trampa del validador de OpenSpec —**lee sólo la primera línea física** de la descripción de un requisito—; y **dos trampas de máquina**: el bundle de certificados en runtime y el bucle de eventos de Windows con `psycopg` |
| Informe nuevo | [`c30a-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30a-implementation-measurements.md): línea base, los tres spikes con sus tablas, **seis refutaciones**, la tabla de los 19 escenarios de la HU y la evidencia de los tres modos |

---

## 12. Fuera de esta pasada

- **El argumentario en prosa, su prompt versionado y la puerta numérica** — es **C30b**, y el corte es lo que lo hace medible: misma ruta, mismos candidatos, mismas citas, con prosa y sin ella. Es la ablación que el §11.2 del diseño pide y que ninguna otra fila aporta.
- **Barrer la lista blanca de secciones y el tope de materiales.** Los valores actuales (2 secciones, 2 materiales) son **punto de partida de un barrido, no calibración**, y viajan por parámetro precisamente para que C30b compare 1/2/3 en un proceso.
- **Los dos avisos de stock** — son de **C34**, tras hidratar, por autoridad sobre el dato.
- **`?question=` en .NET y la caja en la tarjeta** — son C34 y C36. El modo M3 está servido y medido; lo que falta es la superficie por la que un joyero lo alcance.
- **Clasificar la intención** — es **C31** entero. `unclassified` es el único valor honesto que esta capa puede emitir, y C31 sustituirá ése y nunca `product_pitch`.
- **`family_label` en el camino de consulta libre.** Sale nulo porque rellenarlo costaría **una sentencia por grupo** —doce en la respuesta de evidencia—. El campo es opcional en el contrato; queda declarado, no cerrado.
- **La atribución cruzada entre materiales que la pieza sí declara.** Mitigada y declarada; ningún filtro la resuelve.
- **Re-medir el spike 1 con preguntas de mostrador escritas por alguien que no construyó el sistema.** Es la única mitigación real del sesgo del anotador único, y no es del alcance de este change.

---

## Veredicto

**Sin problemas abiertos.** `uv run --system-certs pytest` **1195 passed, 0 failed, 0 skipped** sobre una línea base medida de **1038**, con el test `db` del roster ejecutado de verdad contra pgvector y comprobado que **no saltó**. La comparación por nombres que `CLAUDE.md` exige da **conjunto de fallos vacío en las dos puntas** y ningún nombre nuevo en rojo. `openspec validate --all --strict` **57 passed, 0 failed**. **67/67 escenarios** con test nombrado, **48/48 tareas**.

**El contrato se movió una sola vez y exactamente donde debía**: cinco esquemas, **cero rutas**, cero esquemas añadidos o retirados, y el resto del documento idéntico — comprobado por regeneración en memoria y por diff campo a campo, no por lectura. **Ninguna migración**, ni Alembic ni EF Core. Los ficheros congelados, sin diff; `indexing/embeddings.py` además fijado por hash.

**El invariante central se verifica de tres formas independientes y no por convención**: el paquete no importa ningún cliente de proveedor, no lo alcanza en ejecución en ninguno de los tres modos —parcheando `litellm.acompletion` para que reviente—, y emite `pitch` vacío, `prompt_version` nulo y `usage` a cero. Y el segundo invariante —ni precio ni stock— se comprueba **recorriendo la respuesta serializada entera**, con precio real y tres *buckets* en el índice, precisamente porque un `pitch` vacío haría que una comprobación sobre el `pitch` pasara sin afirmar nada.

**Tres decisiones se tomaron con la cifra delante y antes de escribir el código que dependía de ellas**, que es lo que `tasks.md` imponía como dependencia: el modo de consulta libre **no** necesita umbral propio (1 cita espuria de 101), el filtro asimétrico **no** produce falsa abstención en masa (41 → 44,3 de 72) y además **promueve** ~11,8 fragmentos correctos por ancla, y el tope del roster es 24 sobre un máximo medido de 8.

**Seis refutaciones de los artefactos, todas declaradas y ninguna silenciada** (§9.1 a §9.7): dos cifras del diseño, un supuesto del ticket sobre el orquestador que obligó a una costura, una herramienta que el repositorio no tiene, un hueco de especificación que se cerró decidiendo por escrito, y dos tests de C23 cuyo proxy se afiló en vez de rebajar la documentación publicada.

**Y tres escenarios cuya cobertura era indirecta**, destapados por recorrer los 67 uno a uno y no por mirar un recuento verde (§9.10). Los tres cerrados, con tres tests nuevos.

**Listo para archivar.** La nota que esta pasada dejó abierta —la implementación estaba **en árbol de trabajo y sin commitear** al cerrarla— queda **resuelta**: se comprometió como [`186a8db`](https://github.com/skydr4g0n-it/joiabagur-pv/commit/186a8db) el 2026-09-13, con el árbol limpio.

> **Verificación independiente del 2026-09-13, posterior a esta pasada.** Re-ejecutadas las dos puertas sobre el commit, sin fiarse del código de salida —que con `| tail` es el de `tail` y no el de `pytest`— sino leyendo la línea de resumen: `uv run pytest` **1195 passed, 0 failed, 1 warning en 422,65 s**, con **`skipped=0`**, lo que confirma que el test `db` del roster corrió de verdad contra pgvector en vez de omitirse; y `openspec validate --all --strict` **57 passed, 0 failed**. Comprobado además que los **91 nombres de test** que cita el §3 **existen** en el árbol de tests, uno a uno, en vez de dar la tabla por buena.
