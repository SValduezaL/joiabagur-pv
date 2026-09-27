# T-AIENG-025bis: Retire the flat fusion, the per-list weights and the knobs left without a reader (C25bis)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-024](../../archive/2026-09-11-add-eval-harness-golden-set-and-baselines/ticket.md) y
> [T-AIENG-025](../../archive/2026-09-12-recalibrate-ranking-and-abstention/ticket.md).

**HU origen:** [HU-AIENG-025bis](../../../../Documentos/Historias/AI-Eng/HU-AIENG-025bis.md)
**Change:** `clean-plain-fusion` (C25bis) · **Épica:** EP14 (la cierra) · **Rama:** `c25bis-clean-plain-fusion`
**Decisiones y evidencias:** [c25bis-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25bis-exploration-decisions.md)

---

## Título

Retirar la fusión plana de tres listas, los tres pesos por lista y la clave `fusion` de las
configuraciones de evaluación — conservando el **registro** de la composición, la **memoria** del
defecto y la **cita** de la línea base, y demostrando con un diff por consulta que el borrado no
movió nada.

---

## Contexto y Problema

C25 conservó la fusión plana como modo seleccionable para poder demostrar su propia corrección: sin
ella la fila `v2-hibrido` dejaba de ser reproducible y la tabla perdía su referencia. Congelada la
decisión y publicada la tabla, ese modo pasa a ser un **camino muerto activable por error cuya
aritmética el proyecto midió como defectuosa**:

```
  score(d) = Σᵢ wᵢ / (k + rangoᵢ(d))        k = 60, profundidad = 60
  rama léxica    w_typed 0,50 + w_expanded 0,50 = 1,00 votos, hasta 120 documentos
  rama vectorial                     w_vector = 0,33 votos,  hasta  60 documentos

  documento léxico en el rango 60  →  1,00/120 = 0,008333
  #1 de la rama vectorial          →  0,33/61  = 0,005410     ← pierde SIEMPRE
```

El grado 2 que la rama vectorial pone en primer lugar cae a la **posición 33** en tres consultas del
golden set. La fusión en dos etapas vale **+0,083** sobre esa línea base en la lectura que decide, y
es la única que la ruta viva ejecuta hoy.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado hoy | Qué hace C25bis |
|---|---|---|
| [`retrieval/orchestrator.py`](../../../../ai-service/src/jbg_ai/retrieval/orchestrator.py) | `_fuse_branches` con **dos modos**; `fusion_mode` gobierna la traza de `stage=coverage` y la de `stage=fuse` | Retira la rama plana, el parámetro `fusion`, los tres `weight_*` y la ramificación del log |
| `_fuse_two_stage` (líneas 775-800) | Recibe `internal_weights=(w_typed, w_expanded)` **desde los ajustes** | Pesos iguales declarados en el módulo. Orden **bit-idéntico**: de la etapa 1 sólo se reenvía el orden |
| [`config/settings.py`](../../../../ai-service/src/jbg_ai/config/settings.py) | `FUSION_DEFAULTS` con `jpv_fusion_mode` y los tres pesos por lista; `FUSION_MODE_*`; validador `known_fusion_mode`; entradas en el fallback de blancos y en `canonical_openapi_settings()` | Los retira todos. `jpv_rrf_k`, `jpv_branch_depth` y los pesos por rama **se quedan** |
| `Settings.model_config` | `extra="ignore"` | **Sin cambios** (D-G) |
| [`evals/configs.py`](../../../../ai-service/src/jbg_ai/evals/configs.py) | `EvalConfig` con `fusion`, `weight_typed`, `weight_expanded`, `weight_vector`; `v2-hibrido` en `ABLATION_ORDER` y `POOLED`; `load_all()` hace `glob("*.yaml")` **no recursivo** y ya rechaza claves desconocidas (127-131) | Retira los cuatro campos y las dos entradas. La guarda de claves desconocidas **se conserva y pasa a ser el mecanismo del escenario de fallo ruidoso** |
| [`evals/sweep.py`](../../../../ai-service/src/jbg_ai/evals/sweep.py) | `FusionFingerprint` con `mode` y los tres `weight_*`, persistida en el fichero de captura | Retira esos cuatro campos. Las capturas anteriores dejan de ser legibles: declarado, no versionadas |
| [`evals/runner.py`](../../../../ai-service/src/jbg_ai/evals/runner.py) `_fusion_mode_of` | Resuelve `config.fusion or settings.jpv_fusion_mode` | Resuelve desde constante: la composición viva, o `NO_FUSION` para las filas que no fusionan |
| [`evals/provenance.py`](../../../../ai-service/src/jbg_ai/evals/provenance.py) | Tupla de **seis** elementos; el docstring justifica el sexto por la existencia del modo plano | **Conserva el campo**; reescribe la justificación. El requisito vivo que lo mandataba desaparece, así que pasa a mandatarlo `retrieval-evaluation` |
| [`evals/report.py`](../../../../ai-service/src/jbg_ai/evals/report.py) | Columna `fusión` por fila | **Sin cambios**: sigue distinguiendo las filas que fusionan de las que no |
| [`evals/configs/v2-hibrido.yaml`](../../../../ai-service/evals/configs/retired/v2-hibrido.yaml) | Fija `fusion: flat`, los tres pesos y `abstain: false` | Se mueve a `evals/configs/retired/` con cabecera de histórico |
| `COVERAGE_RULES` | `("continuous", "none")`; la forma binaria se implementó y se retiró **dentro de C25** | **Sin cambios.** La pata se declara cumplida y se comprueba |
| `coverage_rule` | No es campo de `Settings`; el router no lo pasa ([`retrieval.py`](../../../../ai-service/src/jbg_ai/api/routers/retrieval.py) 118-124) | **Sin cambios** en código; se corrige la cláusula de la spec que promete un rollback de despliegue inexistente |
| [`ai-service/openapi.json`](../../../../ai-service/openapi.json) | Congelado; no menciona la fusión | **No se mueve** |
| Configuración de despliegue | **No existe** `.env.example`, ni `JPV_` en `terraform/`, ni compose de ai-service | Sólo se comprueba; se espera vacío |

### Las tres refutaciones de la propia ficha

| Punto de la ficha | Veredicto, comprobado sobre el árbol |
|---|---|
| *«los pesos por lista que sólo ella consumía»* | **Refutado.** `weight_typed` y `weight_expanded` alimentan también la etapa 1 viva. Se retiran igualmente, pero por ser **trampas** —la spec ya prohíbe moverlos— y no por estar muertos |
| *«retirar la variante de ponderación adaptativa que perdió el barrido»* | **Pata vacía.** La forma binaria se retiró dentro de C25 y hay un test que falla si vuelve. Se declara cumplida y se comprueba |
| *«que el arranque falle nombrando la perilla»* | **Inalcanzable por el mecanismo previsto y peor que el mal.** Se acota a la configuración de evaluación, donde el daño es de medición y donde la guarda **ya existe** |

---

## Componentes Afectados

- **`ai-service/`** — único componente con cambio de código, y **sólo por borrado**:
  `src/jbg_ai/retrieval/orchestrator.py`, `src/jbg_ai/config/settings.py`,
  `src/jbg_ai/evals/{configs,sweep,runner,execute,cli,provenance}.py`,
  `evals/configs/v2-hibrido.yaml` → `evals/configs/retired/`, y los tests de
  `tests/{retrieval,evals,config,api}/`.
- **`openspec/`** — seis deltas: cuatro en `hybrid-fusion`, dos en `retrieval-evaluation`.
- **`Documentos/`** — informe de implementación, ficha y §0 del plan, `epicas.md`, y la cabecera de
  histórico sobre el informe de C25.
- **Sin diff**: `backend/`, `frontend/`, `terraform/`, `.github/workflows/`, `ai-service/openapi.json`
  y `ai-service/migrations/`.

---

## Especificaciones Técnicas

### 1. Retirada de la fusión plana (`retrieval/orchestrator.py`)

- Desaparece la rama `if mode == FUSION_MODE_FLAT` de `_fuse_branches`, con su `flat_weights` y su
  `lexical_names = (TYPED_LIST, EXPANDED_LIST)`.
- Desaparecen los parámetros `fusion`, `weight_typed`, `weight_expanded` y `weight_vector` de
  `retrieve_products`, y la comprobación `if fusion_mode not in FUSION_MODES`.
- La traza `stage=fuse` deja de ramificar entre dos juegos de pesos y emite siempre los de rama; la
  de `stage=coverage` deja de estar condicionada al modo.
- `lexical_names` pasa a ser siempre `(LEXICAL_BRANCH_LIST,)`, con lo que la salvedad escrita sobre
  «un candidato visto por las dos listas léxicas no es cross-branch» pasa de explicada a
  **estructural**. El comportamiento no cambia y su requisito tampoco.

### 2. La etapa 1, con pesos iguales declarados (`_fuse_two_stage`)

```python
# Los pesos internos de la rama léxica son IGUALES por norma y no se barren: la evidencia
# medida establece que ambas listas son necesarias, no que una valga más. Como de la etapa 1
# sólo se reenvía el ORDEN, el valor concreto no puede alterar el resultado.
LEXICAL_INTERNAL_WEIGHT = 0.5
```

**Argumento de identidad, que es lo que permite exigir cifras idénticas:** en la etapa 1 ambas
listas llevan el mismo peso, RRF escala linealmente con el peso, y `_fuse_two_stage` sólo reenvía
`lexical_ids` a la etapa 2 — la magnitud se descarta. El resultado es bit-idéntico **por
construcción**, no por comprobación afortunada.

### 3. Ajustes (`config/settings.py`)

Salen de `FUSION_DEFAULTS`, de los campos, del validador `blank_fusion_setting_is_default`, del
validador `known_fusion_mode` y de `canonical_openapi_settings()`:

| Nombre | Variable de entorno |
|---|---|
| `jpv_fusion_mode` | `JPV_FUSION_MODE` |
| `jpv_rrf_weight_typed` | `JPV_RRF_WEIGHT_TYPED` |
| `jpv_rrf_weight_expanded` | `JPV_RRF_WEIGHT_EXPANDED` |
| `jpv_rrf_weight_vector` | `JPV_RRF_WEIGHT_VECTOR` |

Se quedan, y su permanencia se comprueba: `jpv_rrf_k`, `jpv_branch_depth`,
`jpv_branch_weight_lexical`, `jpv_branch_weight_vector`, `jpv_business_weight_availability`,
`jpv_retrieval_distance_threshold` y las tres de abstención. Son el mecanismo de calibración de C26
y C38. **`extra="ignore"` no se toca** (D-G).

### 4. Evaluación (`evals/configs.py`, `sweep.py`, `runner.py`, `execute.py`, `cli.py`)

- `EvalConfig` pierde `fusion`, `weight_typed`, `weight_expanded` y `weight_vector`.
- `ABLATION_ORDER` y `POOLED` pierden `v2-hibrido`. Esto es **obligatorio y no opcional**:
  `test_every_configuration_loads_and_the_table_is_in_order` exige igualdad **exacta** entre
  `load_all()` y `ABLATION_ORDER`.
- `FusionFingerprint` pierde `mode` y los tres `weight_*`. Las capturas de barrido tomadas antes del
  change dejan de poder cargarse; no están versionadas y se declara.
- `_fusion_mode_of` deja de leer los ajustes y resuelve desde constante.

**`POOLED` frente a `pooled_in`:** sacar `v2-hibrido` de `POOLED` no contradice que
`judgements.jsonl` siga nombrándolo. `POOLED` es quién **entra** al próximo pooling; `pooled_in` es
el registro de quién **entró**.

### 5. La procedencia conserva el registro (`evals/provenance.py`)

`Provenance` sigue teniendo **seis** elementos. `fusion_mode` se puebla desde constante de módulo y
nunca desde el entorno, y `differences()` lo sigue comparando. El docstring se reescribe: deja de
justificarse por la existencia del modo plano y pasa a justificarse por que **una corrida archivada
bajo otra composición debe seguir declarándose no comparable**.

Es además lo que cierra el hueco que habría justificado una lista negra de perillas: una fila medida
por alguien que creyó seleccionar el modo plano se imprimiría marcada con la composición real.

### 6. El fichero de la línea base

`ai-service/evals/configs/v2-hibrido.yaml` → `ai-service/evals/configs/retired/v2-hibrido.yaml`,
con cabecera que declara que es **histórico y no ejecutable** y remite al informe y al JSONL.

La inercia es estructural: `CONFIG_DIR.glob("*.yaml")` **no es recursivo**, así que el
subdirectorio es inalcanzable por el cargador. Y `load_config("v2-hibrido")` falla nombrando la ruta
y listando las disponibles.

### 7. Tests

**Caen** (comportamiento retirado):

| Test | Fichero |
|---|---|
| `test_flat_fusion_mode_reproduces_the_published_baseline` | `tests/retrieval/test_fusion.py:259` |
| Los tres usos de `fusion="flat"` como testigo diferencial | `tests/retrieval/test_orchestrator.py:776, 876, 893` |
| Aserciones sobre los pesos por lista y su suma | `tests/config/test_settings.py:390-401, 435-437, 446-452` |
| Aserciones sobre los pesos por lista en el arranque | `tests/api/test_health.py:107-139` |
| `modes["v2-hibrido"] == "flat"` | `tests/evals/test_baselines_and_configs.py:160-179` |
| Aserciones sobre `baseline.fusion` y `baseline.weight_*` | `tests/evals/test_metrics.py:383-391` |
| Carga de `v2-hibrido` | `tests/evals/test_reproducibility.py:111` |
| Campos retirados de la huella | `tests/evals/test_sweep_phases.py:42-43, 186` |

**Entran:**

| Test | Qué fija |
|---|---|
| `test_no_flat_fusion_path_exists` | Ninguna configuración selecciona una fusión de una etapa |
| `test_no_per_list_weight_is_defined` | No hay peso por lista en ajustes ni en configuración de evaluación |
| `test_the_retired_baseline_config_no_longer_loads` | El YAML retirado sigue versionado y ya no carga, fallando por claves desconocidas |
| `test_the_flat_arithmetic_that_was_retired_buried_the_vector_leader` | **El fósil (D-F)**: aritmética pura sobre `fuse()`, sin orquestador, sin ajustes y sin modo, con los pesos históricos como literales locales |
| `test_only_the_continuous_scaling_form_exists` *(o refuerzo del existente)* | Una sola forma de escalado; `none` sigue siendo brazo de control |

### 8. Las seis deltas de spec

**`hybrid-fusion`**

1. `REMOVED` — `The flat fusion remains selectable so the published baseline stays reproducible`.
   Ya redactada; se **corrige su nota `Migration`**, que hoy exige que el arranque falle.
2. `MODIFIED` — `Weights and smoothing are configuration, and the weakest branch weighs less`.
   Ya redactada y bien formada; se **acota** el escenario del knob a la evaluación.
3. `MODIFIED` — `The lexical branch weighs less when its best candidate matched less of the query`.
   Se **reescribe la delta**: verbatim del vivo, con sus **seis** escenarios y su `MUST be
   continuous`, corrigiendo **una** cláusula (el rollback es del arnés, no del despliegue).
4. `MODIFIED` — `Fusion tests run offline and pin the measured defaults`. **Nueva.** Sustituye el
   pin del peso de lista —ya declarado retirado desde C25— por uno cierto: los pesos internos son
   iguales y no configurables, y el cociente de rama por defecto es el declarado.

**`retrieval-evaluation`**

5. `MODIFIED` — `An ablation table isolates each change it reports`. Ya redactada y bien formada.
6. `MODIFIED` — `A run is comparable to another only when its provenance matches`. **Nueva.**
   Añade el sexto elemento, cuyo único mandato vivía en el requisito que se elimina.

**Sin delta** sobre `Deepening the golden set re-runs every row…`: una configuración retirada deja
de ser fila.

### 9. Protocolo de verificación

```
 1. ANTES    uv run pytest  → NOMBRES de los tests en rojo, nunca el recuento
             comprobar index_set_hash == 051a6b06021efc3f…     <-- puerta: si se movió, PARAR
             uv run evals run  (v0-nombre, v0-fts, v1-vectorial, v2b-fusion, v3-senales)
 2. BORRADO
 3. DESPUÉS  uv run evals run  (las mismas cinco, mismo golden set)
 4. DIFF     por (config_id, query_id): `ranked` COMPLETO + todas las métricas → CERO diferencias
```

- **La referencia es la corrida previa de esta rama, no la tabla publicada.** El informe de C25
  declara que su corrida se tomó `+dirty`, con código que aterrizó en `8ace5ac`.
- **Excepción de procedencia declarada:** el arnés marcará las dos corridas no comparables por
  `git_sha`, y tiene razón — esa diferencia **es** la hipótesis bajo prueba. Si difiere cualquier
  otro elemento, la verificación es **inválida**, no floja.
- **Cero llamadas a proveedor**: los vectores de consulta están congelados en
  `evals/golden/query_vectors.jsonl`.
- **La corrida previa se toma sin `v2-hibrido`**, aunque todavía se pueda.

---

## Arquitectura

- **Principio rector, y es el que resuelve la mitad de las dudas del change:** *una perilla es algo
  que se puede poner; un registro es algo que se escribe.* Este change retira perillas y conserva
  registros. De ahí salen D-B (la procedencia sobrevive al selector), D-E (`POOLED` frente a
  `pooled_in`) y D-G (no hace falta rechazar la entrada equivocada si el registro dice siempre lo
  que ocurrió de verdad).
- **Frontera intacta:** Python sigue haciendo sólo vectorial y LLM. No hay lógica de negocio, ni
  contrato, ni esquema tocados.
- **Decisiones previas que gobiernan:** las de
  [C25](../../archive/2026-09-12-recalibrate-ranking-and-abstention/design.md) —la fusión en dos etapas,
  la regla adaptativa sin parámetro, la señal que lee sin restringir— **no se revisan**. C25bis las
  da por firmes y retira únicamente lo que existía para demostrarlas.
- **Breaking change interno y declarado:** `v2-hibrido` deja de ser ejecutable. No hay breaking
  change externo: ni REST, ni OpenAPI, ni base de datos.
- **Rollback:** revertir el commit. No hay migración, ni cambio de contrato, ni ajuste de despliegue
  que dependa de lo retirado.

---

## Definición de Hecho (DoD)

- [ ] La rama de fusión plana no existe en el código y ninguna configuración puede seleccionarla
- [ ] No hay ningún peso por lista en ajustes, configuración de evaluación ni parámetros de
      orquestación; la etapa 1 usa pesos iguales declarados en el módulo
- [ ] `Provenance` conserva sus seis elementos, poblado el sexto desde constante
- [ ] `v2-hibrido.yaml` vive en `evals/configs/retired/` con cabecera de histórico, fuera de
      `ABLATION_ORDER` y de `POOLED`
- [ ] `uv run pytest` en verde, sin llamadas reales a LLM, embeddings ni RDS; los **nombres** de los
      tests en rojo coinciden con la línea base salvo los del comportamiento retirado
- [ ] El diff de los dos JSONL por consulta da **cero diferencias** en `ranked` y en todas las
      métricas de las cinco configuraciones supervivientes
- [ ] La única diferencia de procedencia entre las dos corridas es `git_sha`
- [ ] `ai-service/openapi.json` sin diff; sin migración de Alembic
- [ ] Sin diff en `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`
- [ ] Ninguna configuración de despliegue, `.env` ni fichero de infraestructura nombra una perilla
      retirada
- [ ] Las seis deltas escritas y `openspec validate --all --strict` en **`0 failed`**
- [ ] Documentación actualizada **después** de la verificación: README del servicio, README de
      tests, cabecera de histórico en el informe de C25, informe de implementación, §0 y ficha del
      plan, `epicas.md`
- [ ] Sin TODO/FIXME sin tarea asociada

---

## Requisitos No Funcionales

- **Comportamiento observable invariante.** Es el requisito no funcional principal y el criterio de
  éxito: ni el operador ni el administrador ven nada distinto. Cualquier cambio observable es un
  fallo del borrado.
- **Rendimiento.** Sin efecto esperado: se retira una rama que no se ejecutaba. No se mide latencia
  porque no hay hipótesis que medir.
- **Observabilidad.** La traza `stage=fuse` sigue emitiendo tamaño de cada lista, candidatos
  cruzados, `low_confidence`, `k`, profundidad y pesos; deja de emitir un modo que ya no puede
  variar, y `trace_id` se sigue propagando.
- **Seguridad.** Sin superficie nueva: no hay endpoint, ni claim, ni secreto tocado. El token sigue
  mandando sobre el cuerpo.
- **Reproducibilidad.** Los vectores de consulta congelados y la huella del índice son lo que hace
  la verificación determinista y repetible por terceros.
- **Integridad de la evidencia.** Los artefactos de la línea base —informe, JSONL y YAML retirado—
  quedan versionados en el repositorio y enlazados desde el README.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | Al desaparecer `jpv_fusion_mode` de los ajustes, ¿dónde viven las constantes de composición que la procedencia registra? | En `evals/provenance.py`, junto a `NO_FUSION`, que ya está ahí. El orquestador no necesita nombrarla: su traza puede emitirla literal |
| 2 | ¿Se conserva la columna `fusión` del informe de ablations? | **Sí.** Sigue distinguiendo las filas que fusionan de las cuatro que no |
| 3 | Nombre del test fósil de D-F | `test_the_flat_arithmetic_that_was_retired_buried_the_vector_leader` |
| 4 | ¿`_fusion_mode_of` desaparece o se simplifica? | Se **simplifica**: sigue existiendo para decidir entre la composición viva y `NO_FUSION` según el tipo de configuración, que es una decisión real y no una lectura de ajuste |
| 5 | ¿Se añade una fila de control con `coverage_rule: none`? | **No.** El change no tiene autoridad sobre la tabla. El hueco se declara en el informe |
| 6 | ¿Qué pasa si la huella del índice se ha movido al abrir el change? | **Parar.** Sin corrida previa comparable no hay verificación posible, y sin verificación este change no puede afirmar lo único que afirma |

---

## Prioridad / Estimación / Tags

- **Prioridad:** media-baja. Es una **hoja**: no desbloquea ningún change y cede el turno a C26. Su
  urgencia es de erosión —cuanto más se aleja C25, menos gente recuerda por qué ese camino sigue
  ahí— y no de bloqueo.
- **Estimación:** _Pendiente_ — a fijar en refinamiento. El borrado es mecánico; el trabajo real es
  demostrar que no movió nada.
- **Tags:** `ai-service`, `retrieval`, `evals`, `cleanup`, `tech-debt`, `openspec`, `no-migration`,
  `no-contract-change`, `EP14`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-025bis](../../../../Documentos/Historias/AI-Eng/HU-AIENG-025bis.md)
- **Decisiones de exploración:** [c25bis-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25bis-exploration-decisions.md)
- **Change origen del andamio:** [C25 · recalibrate-ranking-and-abstention](../../archive/2026-09-12-recalibrate-ranking-and-abstention/)
- **Specs vivas:** [`hybrid-fusion`](../../../specs/hybrid-fusion/spec.md) · [`retrieval-evaluation`](../../../specs/retrieval-evaluation/spec.md)
- **Tabla publicada:** [c25-baselines-2026-09-11.md](../../../../ai-service/evals/results/c25-baselines-2026-09-11.md)
- **Mediciones de C25:** [c25-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25-implementation-measurements.md)
- **Plan de changes:** [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), ficha C25bis
- **Procedimientos:** [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-11 | Se crean los artefactos del change (`proposal`, `design`, `tasks`, deltas) junto a los de C25 |
| 2026-09-12 | C25 archivado: el prerrequisito duro queda cumplido y el change se desbloquea |
| 2026-09-12 | Exploración sobre el árbol. **Tres afirmaciones de la ficha refutadas** (los pesos por lista tienen lector vivo, la pata de la variante adaptativa está vacía, el fallo ruidoso al arranque es inalcanzable y contraproducente) y **cuatro contradicciones internas encontradas** (la delta perdía dos escenarios vivos; la spec viva ya se contradecía desde C25; las tareas 3.5 y 3.8 se anulaban; la tabla publicada no sirve como referencia por ser `+dirty`). Se fijan las siete decisiones y se redactan HU y ticket |
