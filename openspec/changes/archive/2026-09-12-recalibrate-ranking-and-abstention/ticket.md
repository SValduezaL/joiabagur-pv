# T-AIENG-025: Two-stage fusion, business-signals ranking and retrieval abstention (C25)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-024](../../archive/2026-09-11-add-eval-harness-golden-set-and-baselines/ticket.md)
> y el resto de los tickets del Proyecto Final.

**HU origen:** [HU-AIENG-025](../../../../Documentos/Historias/AI-Eng/HU-AIENG-025.md)
**Change:** `recalibrate-ranking-and-abstention` (C25) · **Épica:** EP14 (con efecto en EP17)
**Mediciones y decisiones:** [c25-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25-exploration-measurements.md)

---

## Título

Corregir la fusión híbrida para que la rama vectorial pueda colocar resultados, hacer que la
disponibilidad y la rotación del punto de venta pesen en el orden, y re-fijar la abstención —
cada efecto en su propia fila de la tabla de ablations.

---

## Contexto y Problema

C24 entregó el juez y, al usarlo, dejó tres deudas y un defecto. El defecto es el que gobierna
el ticket: **la fusión vigente no fusiona, concatena**.

```
  score(d) = Σᵢ wᵢ / (k + rangoᵢ(d))        k = 60, profundidad = 60
  rama léxica    w_typed 0,50 + w_expanded 0,50 = 1,00 votos, hasta 120 documentos
  rama vectorial                     w_vector = 0,33 votos,  hasta  60 documentos

  documento léxico en el rango 60  →  1,00/120 = 0,008333
  #1 de la rama vectorial          →  0,33/61  = 0,005410     ← pierde SIEMPRE
```

Medido sobre el run `d9222333`: el documento de grado 2 que la rama vectorial pone en el #1 cae
en la **posición 33** en `q06`, `q08` y `q10`, y los 32 anteriores son **sólo léxicos** mientras
la cola conserva **exactamente** el orden vectorial. Ejecutando `fuse()` con `wC = 0,33` sobre
una lista léxica de 32 documentos, el #1 vectorial cae en la posición 33: el modelo predice el
dato.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado hoy | Qué hace C25 |
|---|---|---|
| [`retrieval/fusion.py`](../../../../ai-service/src/jbg_ai/retrieval/fusion.py) | RRF ponderado, puro y sin dominio. Su docstring ya anuncia que C25 lo importaría | **Sin cambios en la fórmula**; se compone en dos etapas |
| [`retrieval/orchestrator.py`](../../../../ai-service/src/jbg_ai/retrieval/orchestrator.py) | Fusión **plana de tres listas** con `w_typed`/`w_expanded`/`w_vector` | Fusión en **dos etapas** con pesos por rama; modo plano conservado |
| `LexicalHit.coordination` en [`ports.py`](../../../../ai-service/src/jbg_ai/retrieval/ports.py) | Se calcula en SQL, viaja en el *hit* y **el orquestador no lo lee nunca** | Lo consume la regla adaptativa. Cuarto cable pelado, tras `tsv`, la expansión y `qty_bucket` |
| `_SCOPE_CTE` / `_SCOPE_JOIN` en [`search.py`](../../../../ai-service/src/jbg_ai/retrieval/search.py) | Un solo flag `scoped` hace dos cosas: `INNER JOIN` **y** `s.qty_bucket`. Sin escopar, `NULL AS qty_bucket` | Se separan: `scope_pos_id` (INNER, restringe) y `signal_pos_id` (LEFT, sólo lee) |
| `sales_30d` / `sales_90d` / `last_sale_at` | Persistidos en `ai.pos_projection` desde C22, con **un test guardián** que impide leerlos | `sales_30d` entra en los *hits*; **cae el guardián** |
| `demotion_rank` en [`filters.py`](../../../../ai-service/src/jbg_ai/retrieval/filters.py) | Clave lexicográfica `(precio, talla, material, stock)`. Su docstring declara ser *«the seam C25 replaces»* | Score continuo **sólo** en el último bloque |
| `qty_bucket` en evaluación | `v2-hibrido.yaml` lleva `pos_prefilter: false`. **En las 192 filas del run la penalización no se disparó ni una vez** | `signal_pos_id` con el POS de referencia |
| `jpv_retrieval_distance_threshold` | 0,65; deja pasar 1.168 de 1.168. Abstención **0,000** sobre fuera-de-dominio en las tres configuraciones de pipeline | Re-fijado tras M1 |
| `evals/sweep.py` | Rejilla fija `WEIGHT_VECTOR_GRID × BRANCH_DEPTH_GRID`, con proveedor en cada punto | Rejilla de `ρ` de una dimensión + fases `capture`/`rescore` |
| `ai.pos_projection` | Tiene `sales_30d`, `sales_90d`, `last_sale_at` y `computed_as_of` por fila | **Ninguna migración** |
| `ai-service/openapi.json` | Congelado desde C02; C22 lo regeneró para `projection_age_seconds` | **No se mueve**: no se emite señal de familia |

### Las dos refutaciones de la propia ficha

| Punto de la ficha | Veredicto |
|---|---|
| *«penalizaciones por […] variante ambigua dentro de familia»* | **Refutado.** Reparto real de familias (C18a): 44 de dos miembros, 55 de tres, 55 de cuatro, **una de cinco y una de ocho** — sólo 2 de 156 pueden llenar cinco huecos, y el panel muestra **10**. El panel ya pinta `Talla {variantLabel}`. `variante-talla` ya es la mejor categoría (0,830). Y sin talla nombrada las hermanas son legítimamente grado 2, así que diversificar **baja** el nDCG@5. La agrupación es presentación: **C30/C36** |
| *«los tres niveles se almacenan y los calibra C25»* (`1-2` vs `3+`) | **Refutado por construcción.** Con `g_efectivo`, los dos caen en la rama `qty_bucket ≠ '0'`, ninguno pierde grado y **no existe función objetivo que pueda ordenarlos**. Además la lectura de negocio tiene signo ambiguo. Se conserva el binario y se confirma con M4 |

---

## Componentes Afectados

- **`ai-service/`** — único componente con código nuevo.
  - `src/jbg_ai/retrieval/` — `orchestrator.py`, `search.py`, `lexical.py`, `ports.py`, `filters.py`
  - `src/jbg_ai/config/settings.py` — `FUSION_DEFAULTS` reformulado, `BUSINESS_DEFAULTS` nuevo, umbral
  - `src/jbg_ai/evals/` — `metrics.py`, `configs.py`, `sweep.py`, `cli.py`, `report.py`
  - `evals/configs/` — `v2b-fusion.yaml`, `v3-senales.yaml`
  - `evals/golden/` — `queries.jsonl`, `judgements.jsonl`, `criterion.md` (ampliación)
  - `evals/results/` — informe versionado
  - `tests/retrieval/`, `tests/evals/`
  - `README.md`, `tests/README.md`
- **`openspec/`** — change `recalibrate-ranking-and-abstention`: dos capacidades nuevas
  (`business-signals-ranking`, `retrieval-abstention`) y tres deltas `MODIFIED`.
- **`Documentos/`** — `epicas.md`, `Historias/AI-Eng/HU-AIENG-025.md`, ficha C25 y §0 del plan,
  §11.2 del diseño RAG, informe de exploración.
- **Sin tocar:** `backend/`, `frontend/`, `terraform/`, `.github/workflows/`. Cero diff.

---

## Especificaciones Técnicas

### 1. Fusión en dos etapas (`retrieval/orchestrator.py`)

```
   ETAPA 1 — dentro de la rama léxica
     typed     (websearch_to_tsquery del texto crudo, AND)   w_int = 0,5
     expanded  (OR de los grupos de equivalencia de C20)     w_int = 0,5
          └─── fuse(k, depth) ───▶ UNA lista léxica          (sólo sobrevive el ORDEN)

   ETAPA 2 — entre ramas
     lexical   (la lista de la etapa 1)                      w_lex
     vector    (<=> coseno)                                  w_vec
          └─── fuse(k, depth) ───▶ lista final
```

- **Reparto interno 0,5 / 0,5, fijo y no barrido.** La evidencia de C21 establece que las dos
  listas son *necesarias* —`typed` rescata los nueve productos llamados «Sortija», `expanded`
  rescata `gargantilla`— no que una valga más.
- **La rama léxica entra en la etapa 2 con 60 documentos**, los mismos que la vectorial. Hoy
  puede meter hasta 120.
- **Consecuencia gratis:** en la etapa 2 hay dos listas que son dos ramas, así que
  `len(ranks) > 1` **es** el consenso entre ramas y `low_confidence` deja de necesitar la
  excepción que su docstring explica hoy.
- **Coste declarado:** de la etapa 1 sólo sobrevive el orden; la magnitud del consenso
  intra-léxico se aplana.

### 2. Pesos por rama y la rejilla

Medido con `fuse()` real: **sólo importa el cociente `ρ = w_vec / w_lex`** —escalar los dos
preserva el orden— así que el barrido es de **una dimensión**.

Posición final del #1 vectorial según `ρ`, con lista léxica de 60 sin consenso (predicción y
medición coincidentes en los once puntos):

| `ρ` | 0,33 | 0,50 | 0,75 | 0,85 | 0,90 | **0,95** | 0,98 | 1,00 | ≥1,10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| posición | 61 | 61 | 22 | 12 | 8 | **5** | 3 | 2 | 1 |

**Banda útil `ρ ∈ [0,9 ; 1,1]`**, donde la rejilla de C24 tenía **un solo punto**. Por eso su
óptimo (`wC = 1,0`) parecía un filo de cuchillo: es el umbral de cruce exacto del régimen en que
las dos listas léxicas coinciden.

- **Rejilla:** `ρ ∈ {0,6 · 0,8 · 0,9 · 0,95 · 1,0 · 1,05 · 1,1 · 1,25}`, normalizada como
  `w_lex + w_vec = 1`.
- **Arranque `ρ = 1,0` (0,5 / 0,5)**, valor **de principio** y no ajustado: *cada rama tiene un
  voto; el mejor resultado de cada rama ocupa uno de los dos primeros puestos, y lo que las dos
  señalan va primero*. Con `ρ = 1` el resultado es consenso primero y **round-robin** después.
- `k` y `depth` se conservan (60 / 60) y se re-barren **juntos**, por la regla de C21
  (*depth ≈ k*).

### 3. Regla adaptativa por cobertura

```
                coordinación del MEJOR documento de la lista expandida
   cobertura = ───────────────────────────────────────────────────────
                grupos contables cuya tsquery NO es vacía

   w_lex_efectivo = w_lex × cobertura                    cobertura ∈ (0, 1]
```

- **Numerador gratis:** la lista viene `ORDER BY coordination DESC`, así que
  `expanded_hits[0].coordination` *es* el máximo.
- **Denominador — el punto crítico del ticket.** Medido con `expand_query` + `counting_flags`,
  las palabras vacías **cuentan como grupo** y su `plainto_tsquery` es vacía:

  ```
  'sortija de plata'       →  ['sortija','anillo','aro de dedo']  ['de']  ['plata']
  'anillo de plata y oro'  →  ['anillo','aro de dedo'] ['de'] ['plata'] ['y'] ['oro']
  'una bicicleta antigua'  →  ['una']  ['bicicleta']  ['antigua']
  ```

  | consulta | denominador ingenuo | corregido | nDCG@5 hoy |
  |---|---:|---:|---:|
  | `sortija de plata` | 2/3 = **0,67** ✗ | 2/2 = **1,00** ✓ | 1,000 |
  | `anillo de plata y oro` | 3/5 = **0,60** ✗ | 3/3 = **1,00** ✓ | — |
  | `bano de oro` | 1/1 = 1,00 | 1/1 = 1,00 ✓ | 1,000 |
  | `gargantilla dorada` | 1/1 = 1,00 | 1/1 = 1,00 ✓ | 0,903 |
  | `una bicicleta antigua` | 1/3 = 0,33 | 1/2 = **0,50** ✓ | 0,000 |
  | `follaje seco que cae en septiembre` | 1/6 = 0,17 | 1/4 = **0,25** ✓ | 0,100 |

  **Con el ingenuo, la regla recorta un tercio del peso léxico en una consulta que puntúa 1,000**
  — destruye exactamente las categorías que existe para no tocar.
- **Implementación:** el denominador es constante por consulta y se calcula en la **misma
  sentencia** que ya tally-a la coordinación, con `numnode(<fragmento del grupo>) > 0`. Sin viaje
  extra a la base.
- **Cero parámetros.** Alternativa de reserva: forma binaria con un `α` declarado, que entra como
  **segunda fila candidata** del barrido, no como sustituto.
- **Predicción falsable:** `materiales`, `sinonimos`, `lexico-exacto` y `piedra` tienen cobertura
  1,00 y su nDCG@5 debe moverse en **cero**.

### 4. Señal de punto de venta separada del alcance

```sql
-- CTE ya existente, sin cambios en su cuerpo
WITH scope AS MATERIALIZED (
  SELECT product_id, qty_bucket, sales_30d
  FROM ai.pos_projection
  WHERE pos_id = :pos_id AND is_assigned_hint IS TRUE
)
-- alcance (C22):  JOIN scope s ON s.product_id = d.product_id     -- restringe
-- señal  (C25):   LEFT JOIN scope s ON s.product_id = d.product_id -- sólo lee
```

- `scope_pos_id` y `signal_pos_id` como parámetros **independientes** de
  `retrieve_products`, no como un solo flag `scoped`.
- **En evaluación: `scope_pos_id = None`, `signal_pos_id = <POS de referencia>`.** Mide la
  reordenación **sin** pagar el coste de recall del prefiltro, que es la confusión que C22 se negó
  a introducir y que su config declara como no medida.
- `qty_bucket` y `sales_30d` **nulos** para el no asignado, que no es lo mismo que cero — la regla
  que `_out_of_stock` ya sigue hoy.
- **POS:** calibrar en **MAO-AIR** (34,4 % del surtido a cero), validar en **FORNELLS** (12,0 %) y
  **HT-GALDANA** (11,7 %). `HT-ARTRUTX` excluido: surtido cero, responde 503.

### 5. Score continuo en el último bloque

```
  HOY   (precio↑, talla↑, material↑, stock↑)          cuatro enteros
  C25   (precio↑, talla↑, material↑) ▸ −score_negocio  continuo en la cola
```

- Conserva el MUST vivo de `pos-projection`: *«dentro del techo precede a fuera, sea cual sea el
  stock»*.
- **No pierde alcance:** `demote()` hace *early return* cuando ningún filtro tecleado se dispara
  —el caso mayoritario— así que la clave es `(0,0,0)` para todos y el bloque de cola **es la lista
  entera**.
- `score_negocio` = disponibilidad **calibrada** + rotación como **desempate de peso fijo**, que
  no puede revertir la disponibilidad ni un filtro tecleado.

### 6. Métrica objetivo y guardarraíl (`evals/metrics.py`)

```
  g_efectivo(doc) =  grado                si qty_bucket ≠ '0'
                     máx(grado − 1, 0)     si qty_bucket = '0'
```

- **No introduce una constante: reutiliza la escala.** El grado 1 de `criterion.md` ya es
  *«sustituto plausible que el operador ofrecería como segunda opción»*.
- **`judgements.jsonl` no se modifica:** el grado etiquetado sigue siendo el que se etiquetó.
- **Regla de decisión:** objetivo `nDCG@5 operativo` sube · guardarraíl `nDCG@5` puro no cae más
  de 0,05 · ninguna categoría cae más de 0,05 · la lectura que decide es `new`.

### 7. Abstención (`retrieval-abstention`)

- **M1 primero, y decide la forma y la fase.** C24 midió el solape **por documento**
  (grado 2 hasta 0,8008; grado 0 desde 0,3268; hueco **−0,4739**) y concluyó que un escalar no
  sirve. Pero la abstención la decide el **mejor acierto por consulta**, y esa cantidad **no está
  en ningún artefacto**: el JSONL por consulta guarda métricas, no distancias. C23 separó
  limpiamente con exactamente esa cantidad (0,5062 contra 0,5145).
- **Si hay hueco** → escalar sobre `min(distancia)`, como C23. **Va en la fase A**: está en el
  `WHERE` del SQL y **mueve la ventana**.
- **Si no hay hueco** → regla relativa por consulta (`d ≤ d_min·(1+α)`) o cuantil, combinable con
  el `low_confidence` por ausencia de consenso entre ramas, que ya existe. **Va en la fase D**: es
  post-recuperación y **no mueve la ventana**.
- **`fuera-de-dominio` pasa de 5 a 15-20 consultas.** Por la rúbrica todo es grado 0, así que no
  hay etiquetado documento a documento. Con n=5 la única cifra de aceptación alcanzable no es
  creíble.
- **El lado difícil:** subir la abstención sin empezar a callar en las 43 contestables.

### 8. El barrido en dos fases (`evals/sweep.py`, `evals/cli.py`)

```
  fase A — FIJAR LA FUSIÓN        con proveedor · la ventana SE MUEVE
              ↓ decisión congelada
  fase B — CAPTURAR               1 recuperación por consulta; se persiste la ventana de 60
                                  con qty_bucket, sales_30d, family_id, score y ramas
              ↓ ventana INMÓVIL
  fase C — FIJAR LAS SEÑALES      re-puntuado en memoria · cero proveedor · cero base
```

**El orden es una restricción, no una preferencia:** el barrido barato depende de que la ventana
no cambie y la fusión la cambia. `test_calibration_sweep_is_reproducible` pasa de promesa sobre
semillas a **propiedad estructural**.

### 9. La tabla de seis filas

| fila | qué aísla |
|---|---|
| `v0-nombre` · `v0-fts` · `v0-cag` · `v1-vectorial` | sin cambios; se re-corren por procedencia |
| `v2-hibrido` | la fusión **plana** viva — línea base publicada |
| **`v2b-fusion`** | la fusión **por rama** con adaptativa, **sin** señales |
| **`v3-senales`** | `v2b` + disponibilidad + rotación |

- **Sin `v2b`, un `v3` que mejorase sería inatribuible.**
- **La fusión plana se conserva como modo seleccionable.** Si se sustituye, `v2-hibrido` deja de
  reproducir la línea base y la tabla pierde su fila de referencia.
- Al profundizar el *pool* se mueve `golden_set_version`: **las seis se re-corren**. `v0-cag` son
  12 consultas a $0,002673 = **tres céntimos**, así que se re-corre para que la tabla comparta una
  sola procedencia. El ganador del barrido se **re-confirma** en la versión nueva: un punto, no la
  rejilla.

### 10. Tests

| Test | Qué protege |
|---|---|
| `test_vector_top_hit_reaches_the_top_five_without_lexical_consensus` | El defecto de la posición 33 |
| `test_full_coverage_leaves_the_lexical_weight_untouched` | Que la adaptativa no cobre donde no hay daño |
| `test_stopword_group_does_not_lower_coverage` | El denominador corregido |
| `test_signal_join_never_restricts_the_candidate_set` | `LEFT` frente a `INNER` |
| `test_out_of_stock_product_ranks_below_equivalent_in_stock` | El de la ficha, ahora sin escopar |
| `test_typed_constraint_outranks_the_business_score` | El MUST lexicográfico de `pos-projection` |
| `test_rotation_only_breaks_ties` | Que la rotación no derribe nada |
| `test_weights_load_from_config_not_hardcoded` | El de la ficha |
| `test_operational_gain_is_a_declared_function_of_grade_and_availability` | D3, sin constantes sueltas |
| `test_a_weight_that_costs_more_than_the_margin_is_rejected` | El guardarraíl |
| `test_calibration_sweep_is_reproducible` | El de la ficha, ahora estructural |
| `test_flat_fusion_mode_reproduces_the_published_baseline` | La fila de referencia |
| `test_abstention_does_not_fire_on_answerable_queries` | El lado caro de la abstención |

Todos ejecutables **sin proveedor**; los de base con `testcontainers` y *skip* si Docker no
responde.

---

## Arquitectura

- **Frontera intacta.** Python sigue haciendo sólo vectorial y LLM; .NET conserva la autoridad
  sobre precio, stock y permisos. Las señales de negocio **ponderan y nunca eliminan**, así que un
  producto válido no puede desaparecer por una proyección desfasada: como mucho baja de posición
  y .NET siempre lo ve. Es la promesa del §7.6 del diseño.
- **Orden del pipeline conforme al apunte de S10** (*«lo barato y excluyente, al principio; lo
  caro y fino, al final; lo blando, al cierre»*): las señales de negocio son lo blando y ya están
  al cierre.
- **`fusion.py` no se reescribe.** Es puro y sin dominio por decisión de C21, y su docstring ya
  anuncia que C25 lo importaría; se **compone**, no se modifica.
- **Sin migración.** `ai.pos_projection` ya tiene las tres columnas y `computed_as_of` por fila.
- **Sin *breaking changes*.** `openapi.json` no se mueve; el contrato de `RetrievalResult` no
  gana campos. La señal de familia se deja al change que la consuma (C30/C36).
- **Reloj declarado.** `sales_30d` se lee contra el `computed_as_of` de la fila y **nunca** contra
  el reloj de pared: el mundo de C10 termina el 2026-08-23 y con reloj de pared la señal se va a
  cero, además de hacer el ranking irreproducible por diseño.
- **Deltas sobre specs vivas** (nunca editadas a mano; sólo por delta spec dentro del change):
  `pos-projection` (*«Availability demotes… binary»* y *«Sales aggregates… read by none of it»*),
  `hybrid-fusion` (pesos por lista → por rama), `retrieval-evaluation`
  (*«MUST NOT modify the live distance threshold»* y la regla de cambio de defaults).

---

## Definición de Hecho (DoD)

- [ ] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] `ai-service`: `uv run pytest` en verde **sin** llamadas reales a LLM, *embeddings* ni RDS
- [ ] `openapi.json` **sin diff** (no cambia el contrato)
- [ ] **Ninguna** migración de Alembic
- [ ] `backend/`, `frontend/`, `terraform/` y `.github/workflows/` **sin diff**
- [ ] Las cuatro mediciones de la fase 0 ejecutadas y publicadas **antes** de implementar ranking
- [ ] La regla de decisión reformulada escrita y **fechada antes** de ejecutar el barrido
- [ ] `v2-hibrido` reproduce las cifras del informe de C24 sobre la misma versión del golden set
- [ ] Tabla de ablations de **seis filas**, las seis bajo una sola tupla de procedencia
- [ ] Informe versionado en `ai-service/evals/results/` con el antes/después de las consultas sin anclaje
- [ ] Specs de las dos capacidades nuevas y los tres deltas en `openspec/changes/<change>/specs/`
- [ ] `openspec validate --all --strict` en **`0 failed`**
- [ ] Documentación actualizada: `ai-service/README.md`, `tests/README.md`, `Documentos/epicas.md`, ficha C25 y §0 del plan, §11.2 del diseño
- [ ] Limitaciones declaradas en el README: criterio absoluto incumplido, coste del prefiltro sin medir, rotación no calibrada, calibración en un POS
- [ ] Sin TODO/FIXME sin tarea de seguimiento

---

## Requisitos No Funcionales

- **Rendimiento.** `p95` de recuperación **128,6 ms** contra los 500 ms del criterio. C25 añade un
  `LEFT JOIN` sobre un CTE que ya se materializa y aritmética en Python sobre ≤60 candidatos: no
  debe mover el `p95` de forma medible. Se publican las dos columnas de latencia, como fijó C24.
- **Pool de conexiones capado en 5 con `max_overflow=0`.** La etapa 1 no añade consultas: las dos
  listas léxicas ya se ejecutan en serie detrás del proveedor, por la decisión D10 de C21. Ninguna
  fase del barrido debe abrir conexiones concurrentes.
- **Observabilidad.** Log estructurado por etapa con `trace_id`, como el resto del orquestador:
  `stage=fuse` gana `w_lex`, `w_vec`, `cobertura` y el modo de fusión; `stage=signals` publica los
  pesos aplicados y cuántos candidatos reordenó. **Ningún vector en los logs.**
- **Seguridad.** `pos_id` sigue saliendo del token y nunca del cuerpo; un claim que no parsea sigue
  siendo un rechazo y **nunca** una búsqueda global. `signal_pos_id` es un parámetro **interno del
  orquestador**, no un campo del contrato: no puede llegar del navegador.
- **Integridad.** Ningún valor de stock alcanza la respuesta como cantidad exacta. Las señales
  reordenan y **nunca** eliminan.
- **Reproducibilidad.** Procedencia por ejecución y `sales_30d` leído contra `computed_as_of`.
  El barrido de señales es exacto por construcción.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿La forma de la regla de abstención es escalar o relativa por consulta? | **La que dicte M1.** Si el hueco existe, escalar en la fase A; si no, relativa en la fase D |
| 2 | ¿Cuánto crece el *pooling* con lo que promuevan `v2b` y `v3`? | No se puede dimensionar hasta cerrar la fase A. Se estima entonces; si supera dos horas, se prioriza por categoría |
| 3 | ¿Cuánto crece la partición de ajuste? | Al menos hasta que ninguna de sus consultas esté en el techo de tres métricas. Cifra exacta tras la ampliación de `fuera-de-dominio` |
| 4 | ¿Se adopta la adaptativa continua o la binaria con `α`? | **La continua**, por tener cero parámetros. La binaria se mide como segunda fila y sólo gana si la continua no se sostiene en las tres lecturas |
| 5 | ¿Se retira la fusión plana tras decidir? | **No en este change.** La tabla necesita su fila de referencia. Retirarla es un change posterior de limpieza |
| 6 | ¿Se emite alguna señal de familia al contrato? | **No.** El consumidor (C30/C36) no existe todavía y mover `openapi.json` sin consumidor es deuda |

---

## Prioridad / Estimación / Tags

- **Prioridad: Alta.** Con C24 archivado, **la cadena crítica arranca aquí**:
  `C25 → C26 → C34 → C36`. Bloquea a C26 y a C27.
- **Estimación:** _Pendiente_. El código es acotado; lo caro es la **secuencia de fases**, el
  etiquetado incremental y las cuatro mediciones previas.
- **Tags:** `ai-service` · `retrieval` · `ranking` · `fusion` · `abstention` · `evals` ·
  `business-signals` · `no-migration` · `no-contract-change` · `python`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-025](../../../../Documentos/Historias/AI-Eng/HU-AIENG-025.md)
- **Mediciones y las quince decisiones:** [c25-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25-exploration-measurements.md)
- **Informes que dejaron el trabajo preparado:** [c24-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c24-implementation-measurements.md) · [c22-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-implementation-measurements.md) · [c21-hybrid-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md)
- **Diseño RAG** [§7.6, §11.1, §11.2, §15](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) · **Plan de changes, ficha C25** [aquí](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Specs vivas:** `openspec/specs/hybrid-fusion/` · `pos-projection/` · `retrieval-evaluation/` · `vector-retrieval/` · `query-expansion/`
- **Procedimientos:** [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Apuntes:** [S10 · Filtrado contextual y temporal](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Filtrado%20contextual%20y%20temporal.md) · [S10 · Búsqueda híbrida](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Busqueda%20hibrida.md) · [S16 · Un sistema debe saber decir «No lo sé»](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Un%20sistema%20debe%20saber%20decir%20%E2%80%9CNo%20lo%20se%E2%80%9D.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-11 | Creación del ticket tras la sesión de exploración. Quince decisiones cerradas, **dos puntos de la ficha refutados por medición** (penalización de variante ambigua y calibración de `1-2`/`3+`), y el change **renombrado** de `add-business-signals-ranking` a `recalibrate-ranking-and-abstention` porque el nombre anterior describía un tercio de su alcance. El número C25 se conserva |
