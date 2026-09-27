## 1. Puerta de entrada y corrida de referencia

- [x] 1.1 Verificar que **C25 está archivado** y su tabla de ablations publicada en `ai-service/evals/results/`. **Si no lo está, parar**: este change retiraría el andamio mientras sostiene la tabla — *archivado el 2026-09-12*
- [x] 1.2 Comprobar que la **huella del conjunto indexado** sigue siendo la de la tabla publicada. Si se ha movido, **parar**: sin corrida previa comparable no hay verificación posible — *`051a6b06021efc3fb18891ffc7acfa2c6e3499f161aa81e9e96dd061233e073b`, 1168 documentos, coincide*
- [x] 1.3 Comprobar que la **versión del golden set** es la de la tabla publicada — *`1:198c4af44506`, 71 consultas (63 juzgadas), 3926 juicios*
- [x] 1.4 Tomar la **corrida de referencia previa al borrado** y versionarla — *`334bd6dc-b6c9-4c64-8738-993feb765014`, en [`evals/results/c25bis/`](../../../../ai-service/evals/results/c25bis/), 378 filas: 6 configuraciones × 63 consultas*
- [x] 1.5 Registrar por qué la referencia es esta corrida y **no** la tabla publicada: aquélla se tomó `+dirty`, con código que aterrizó en el commit siguiente. *Medido: la corrida previa **reproduce la tabla publicada fila por fila** a tres decimales, así que la cautela no se materializó — pero la comparación sigue haciéndose contra la corrida previa, que es la que garantiza el mismo árbol*
- [x] 1.6 Medir la línea base de la suite **antes de tocar nada**: `uv run pytest`, guardando los **nombres** de los tests que fallan y no su recuento — ***994 passed, 0 failed*. La lista de nombres en rojo está vacía**, así que la comparación de 4.1 es más estricta de lo que el `CLAUDE.md` prevé: tras el borrado la suite debe seguir en cero fallos y el recuento sólo puede bajar por los tests retirados

## 2. Inventario de lo que se retira, comprobado y no recordado

- [x] 2.1 Buscar sobre el árbol todos los lectores de cada perilla candidata: ruta viva, configuraciones de evaluación supervivientes y tests que ejerzan comportamiento vivo — *hecho en la exploración; resultado en el `## Context` del `design.md` y en [`c25bis-exploration-decisions.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25bis-exploration-decisions.md)*
- [x] 2.2 Escribir el inventario en el `design.md` del change **antes** de borrar, con el motivo por el que cada elemento se retira — *y con las **tres afirmaciones de la ficha que refutó**: los pesos por lista sí tienen lector vivo, la variante adaptativa perdedora no existe, y el fallo al arranque no es alcanzable por el mecanismo supuesto*
- [x] 2.3 Confirmar que **no** entran en el inventario las perillas que siguen teniendo lector: pesos de negocio, umbral de distancia, `k`, profundidad y `coverage_rule`
- [x] 2.4 Declarar la **pata 2 cumplida por C25**: comprobar `COVERAGE_RULES == ("continuous", "none")` y que `rule="binary"` levanta

## 3. El borrado

- [x] 3.1 `retrieval/orchestrator.py` — retirar la rama del modo plano de `_fuse_branches`, con su `flat_weights` y su `lexical_names` de dos entradas
- [x] 3.2 `retrieval/orchestrator.py` — retirar los parámetros `fusion`, `weight_typed`, `weight_expanded` y `weight_vector` de `retrieve_products`, la comprobación de modo desconocido y la ramificación de las trazas `stage=coverage` y `stage=fuse`
- [x] 3.3 `retrieval/orchestrator.py` — fijar la etapa 1 con **pesos iguales declarados en el módulo**, con el comentario que explica por qué el valor no puede alterar el resultado: de la etapa 1 sólo se reenvía el orden
- [x] 3.4 `config/settings.py` — retirar `jpv_fusion_mode`, `jpv_rrf_weight_typed`, `jpv_rrf_weight_expanded` y `jpv_rrf_weight_vector` de `FUSION_DEFAULTS`, de los campos, del validador de blancos, del validador `known_fusion_mode` y de `canonical_openapi_settings()`. **`extra="ignore"` no se toca** (D-G)
- [x] 3.5 `evals/configs.py` — retirar `fusion` y los tres `weight_*` de `EvalConfig`; sacar `v2-hibrido` de `ABLATION_ORDER` y de `POOLED`. **Obligatorio y no opcional**: `test_every_configuration_loads_and_the_table_is_in_order` exige igualdad exacta
- [x] 3.6 `evals/sweep.py` — retirar `mode` y los tres `weight_*` de `FusionFingerprint`; `evals/execute.py`, `runner.py` y `cli.py` — retirar las lecturas correspondientes y simplificar `_fusion_mode_of`
- [x] 3.7 `evals/provenance.py` — **conservar** `fusion_mode`, poblado desde constante de módulo, y reescribir el docstring: deja de justificarse por la existencia del modo plano y pasa a justificarse por que una corrida archivada bajo otra composición debe seguir declarándose no comparable
- [x] 3.8 Mover `evals/configs/v2-hibrido.yaml` a `evals/configs/retired/v2-hibrido.yaml`, con cabecera que lo declara **histórico y no ejecutable** y remite a su informe y a su JSONL
- [x] 3.9 Retirar los tests del comportamiento retirado: `test_flat_fusion_mode_reproduces_the_published_baseline` y los tres usos de `fusion="flat"` como testigo diferencial; las aserciones sobre los pesos por lista en `test_settings.py` y `test_health.py`; y las que fijan `fusion`/`weight_*` de `v2-hibrido` en `test_baselines_and_configs.py`, `test_metrics.py`, `test_reproducibility.py` y `test_sweep_phases.py`
- [x] 3.10 Añadir `test_no_flat_fusion_path_exists` ~~y `test_no_per_list_weight_is_defined`~~ — **consolidados en uno**: el escenario `No flat fusion path exists` tiene dos mitades (*ninguna configuración selecciona una fusión de una etapa* y *no hay peso por lista definido*) y las dos se afirman en el mismo test, para que el requisito mapee a un solo sitio. El segundo nombre no existe, y se dice aquí en vez de darse por entregado
- [x] 3.11 Añadir `test_the_retired_baseline_config_no_longer_loads`, que carga el YAML retirado y exige que falle por **claves desconocidas** — la guarda que ya existe en `configs.py`, ahora ejercitada contra el artefacto archivado
- [x] 3.12 Añadir el fósil de D-F, `test_the_flat_arithmetic_that_was_retired_buried_the_vector_leader`: aritmética pura sobre `fuse()`, sin orquestador, sin ajustes y sin modo, con los pesos de C21 como literales locales comentados como históricos

## 4. Verificación de que el borrado no movió nada

- [x] 4.1 `uv run pytest`: comparar los **nombres** de los tests que fallan con la línea base de 1.6; deben caer exactamente los del comportamiento retirado y **ninguno más** — ***997 passed, 0 failed*** contra 994/0. La cuenta cuadra exactamente: **−4 retirados** (`test_flat_fusion_mode_reproduces_the_published_baseline`, `test_vector_branch_weight_defaults_below_lexical`, `test_the_two_lexical_weights_sum_to_one_lexical_list`, `test_baseline_row_is_still_selectable_and_reproducible`) **+7 añadidos**. La lista de nombres en rojo sigue **vacía** en las dos corridas
- [x] 4.2 Re-ejecutar la tabla **una vez**, sobre la misma versión del golden set y la misma huella de índice — *`e0a10740-4c61-466c-b86d-56a6df94b1a0`, cinco filas, en [`evals/results/c25bis/`](../../../../ai-service/evals/results/c25bis/)*
- [x] 4.3 **Diff línea a línea** del JSONL por consulta contra el de 1.4, emparejando por `(config_id, query_id)` sobre `ranked` **completo** y todas las métricas, para las **cinco** configuraciones supervivientes: **cero líneas distintas** — ***las 315 filas son idénticas*** (5 configuraciones × 63 consultas), listas de resultados incluidas. Y las cifras publicadas coinciden a tres decimales en las cinco filas
- [x] 4.4 Comprobar que el **único** elemento de la procedencia que difiere es `git_sha` — *confirmado: versión del golden set `1:198c4af44506` y huella del índice `051a6b06021efc3f…` **idénticas**; los embeddings salen del mismo artefacto congelado; la revisión pasa de `b16242203ba3+dirty` a `59f63ef04738+dirty`, que es precisamente la hipótesis bajo prueba*
- [x] 4.5 Verificar que `ai-service/openapi.json` queda **sin diff** y que no hay migración — *comprobado: `git status` vacío en `openapi.json` y en `migrations/`*
- [x] 4.6 Verificar que `backend/`, `frontend/`, `terraform/` y `.github/workflows/` quedan **sin diff** — *comprobado: `git status` vacío en los cuatro*
- [x] 4.7 Comprobar que ninguna configuración de despliegue (`.env`, SSM, `docker-compose`) trae una perilla retirada — ***ninguna***: cero coincidencias en `backend/.env`, `backend/.env.example`, `frontend/.env.development`, `frontend/.env.example`, en `terraform/` y en los dos `docker-compose` del backend; `ai-service/` no tiene `.env.example` ni compose propio. **El único sitio del repo que todavía las nombra es `openspec/config.yaml`**, que es documentación de contexto y no configuración: se corrige en la tarea 6.9

## 5. Specs

- [x] 5.1 `hybrid-fusion` · `REMOVED` — `The flat fusion remains selectable so the published baseline stays reproducible`, con la nota `Migration` **corregida**: un entorno que aún nombre la perilla no tiene efecto, en lugar de exigir que el arranque falle
- [x] 5.2 `hybrid-fusion` · `MODIFIED` — `Weights and smoothing are configuration, and the weakest branch weighs less`: prohíbe la fusión plana **en el código**, declara que los pesos internos no son configuración, y **acota a la evaluación** el escenario del fallo ruidoso
- [x] 5.3 `hybrid-fusion` · `MODIFIED` — `The lexical branch weighs less when its best candidate matched less of the query`: **verbatim del vivo, con sus seis escenarios y su `MUST be continuous`**, corrigiendo **una** cláusula — apagar la regla es brazo de control de la evaluación, no ajuste de despliegue
- [x] 5.4 `hybrid-fusion` · `MODIFIED` — `Fusion tests run offline and pin the measured defaults`: sustituir el pin del peso de lista, ya declarado retirado por C25, por uno que siga siendo cierto
- [x] 5.5 `retrieval-evaluation` · `MODIFIED` — `An ablation table isolates each change it reports`: conservación y declaración en lugar de reproducibilidad
- [x] 5.6 `retrieval-evaluation` · `MODIFIED` — `A run is comparable to another only when its provenance matches`: incorpora la composición de las ramas como sexto elemento
- [x] 5.7 Comprobar que **ninguna** MODIFIED pierde escenarios vivos sin decirlo, comparando bloque a bloque contra `openspec/specs/`
- [x] 5.8 `openspec validate --all --strict` en **`0 failed`**

## 6. Documentación, y sólo con las cifras idénticas delante

- [x] 6.1 `ai-service/README.md` — retirar la documentación del modo plano y de los tres pesos por lista
- [x] 6.2 `ai-service/README.md` — declarar que la fila de la línea base es **histórica y no re-ejecutable**, con enlaces a su informe, a su JSONL y al YAML retirado
- [x] 6.3 `ai-service/evals/results/c25-baselines-2026-09-11.md` — cabecera que marca la fila `v2-hibrido` como histórica y no re-ejecutable
- [x] 6.4 `ai-service/tests/README.md` — los tests que caen y los que se añaden
- [x] 6.5 Informe de implementación en `Documentos/Proyecto Final AIEng/informes/` con el inventario retirado, el diff de 4.3 y el hueco declarado del brazo de control
- [x] 6.6 Entrada fechada en el §0 y actualización de la ficha en `Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md`
- [x] 6.7 Actualizar `Documentos/epicas.md` (estado del change, recuento y cierre de EP14)
- [x] 6.8 `/opsx:verify` antes de archivar, con atención a que ninguna cifra se haya movido
- [x] 6.9 `openspec/config.yaml` — el párrafo de contexto todavía enumera `JPV_FUSION_MODE`, `JPV_RRF_WEIGHT_TYPED`, `_EXPANDED` y `_VECTOR`, y describe la fusión plana como seleccionable. **Encontrado por la tarea 4.7**, que lo buscaba como configuración de despliegue y lo halló como documentación
