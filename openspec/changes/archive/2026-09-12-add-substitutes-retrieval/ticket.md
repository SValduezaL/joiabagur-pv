# T-AIENG-026: Out-of-stock substitutes retrieval over the stored product embedding (C26)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-025](../../archive/2026-09-12-recalibrate-ranking-and-abstention/ticket.md) y el
> resto de los tickets del Proyecto Final.

**HU origen:** [HU-AIENG-026](../../../../Documentos/Historias/AI-Eng/HU-AIENG-026.md)
**Change:** `add-substitutes-retrieval` (C26) · **Épica:** EP15 (con efecto en EP17)
**Rama:** `c26-add-substitutes-retrieval` · **Mediciones:** [c26-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c26-exploration-measurements.md)

---

## Título

Implementar `POST /v1/retrieval/substitutes` sobre el embedding ya almacenado, con filtro duro por
tipo de pieza, degradación suave por talla y señales explicables por candidato — cerrando el último
501 cerrable del contrato congelado, sin llamar al proveedor y sin mover el contrato.

---

## Contexto y Problema

El sistema sabe buscar y no sabe **qué ofrecer cuando la respuesta correcta no está disponible**.
La ruta existe en el contrato desde C02 y responde **501**.

La ficha del plan describe el motor como *«misma familia primero, luego similitud sobre el
documento»*. **La medición refuta ese orden.** La familia es, por construcción, el conjunto de
piezas que se diferencian **justo en el atributo que descalifica** — la talla —, de modo que
«familia primero» lidera con los candidatos invendibles:

```
  Vecinos por coseno de SKU13 «Anillo erizo de mar M»     (vector puro, sin reglas)

  #1  Anillo erizo de mar L      0,0868   familia ✅   tipo ✅   TALLA ❌
  #2  Anillo erizo de mar S      0,0908   familia ✅   tipo ✅   TALLA ❌
  #3  Anillo Erizo de mar XL     0,1229   familia ✅   tipo ✅   TALLA ❌
  #4  Colgante erizo de mar M    0,1306   familia ❌   TIPO ❌   talla ✅
  #5  Anillo Erizo oro S         0,1375   familia ❌   tipo ✅   TALLA ❌
  #6  Anillo oreja de mar M      0,1535   familia ❌   tipo ✅   talla ✅   ← el primero usable
```

**El top-5 del vector puro no contiene un solo sustituto usable**, y el #4 ni siquiera es del mismo
tipo de pieza. Pero la familia tampoco se puede excluir: el mejor sustituto de `SKU159 Anillo
lapislázuli mediano` es su hermano `mediano oro` — **misma talla, otro material**, y es el #1.

> **La pertenencia a familia es ortogonal al problema. El discriminante es la talla**, y cruza la
> frontera de la familia en las dos direcciones. Lo confirma el criterio de etiquetado que el
> proyecto ya tenía escrito: `criterion.md` clasifica «falla la talla que la consulta nombró» como
> **grado 1 — segunda opción**, no como respuesta.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado hoy | Qué hace C26 |
|---|---|---|
| [`api/routers/retrieval.py`](../../../../ai-service/src/jbg_ai/api/routers/retrieval.py) | `retrieve_substitutes` llama a `require_stub_mode(settings, "C26 (add-substitutes-retrieval)")` y devuelve el stub | Conecta la implementación real; retira esa guarda de **esa** ruta |
| [`stubs/responses.py`](../../../../ai-service/src/jbg_ai/stubs/responses.py) | `retrieval_substitutes_stub` fabrica señales inventadas (`0,9 − i·0,01`) | Se conserva **solo** para el modo stub y los tests de contrato |
| [`api/schemas/retrieval.py`](../../../../ai-service/src/jbg_ai/api/schemas/retrieval.py) | `SubstitutesRequest`, `SubstituteResult`, `SimilaritySignals`, `SubstitutesResponse` ya definidos y congelados | **Sin cambios.** `style_similarity` es requerido y no nulable; `visual_similarity` sí es nulable |
| [`ai-service/openapi.json`](../../../../ai-service/openapi.json) | Contiene `/v1/retrieval/substitutes` | **No se mueve.** `test_openapi_snapshot_is_stable` debe seguir en verde |
| [`retrieval/search.py`](../../../../ai-service/src/jbg_ai/retrieval/search.py) | `_SCOPE_CTE` + `_SCOPE_JOIN` (restringe) / `_SIGNAL_JOIN` (solo lee); el prefiltro filtra por `is_assigned_hint`, **nunca por `qty_bucket`** | Sentencia nueva: k-NN contra el embedding **de una fila**, con filtro por `piece_type` |
| [`retrieval/ports.py`](../../../../ai-service/src/jbg_ai/retrieval/ports.py) | `ProductSearchPort` con `search`, `search_lexical`, `count_scope`, `projection_synced_at`, `scope_buckets` | **Dos métodos nuevos**: leer el documento origen y buscar vecinos por embedding almacenado |
| [`retrieval/filters.py`](../../../../ai-service/src/jbg_ai/retrieval/filters.py) | `demotion_rank` = `(precio, talla, material, −business_score)`. La talla es **bloque entero**; `business_score` **solo resta** | Reutiliza `business_score` y `OUT_OF_STOCK_BUCKET`. **No reutiliza `demotion_rank`**: la talla pasa a término continuo |
| [`retrieval/projection.py`](../../../../ai-service/src/jbg_ai/retrieval/projection.py) | `parse_pos_id`, `resolve_scope`, `default_freshness`, caché de 10 s | Se reutiliza tal cual |
| [`retrieval/fusion.py`](../../../../ai-service/src/jbg_ai/retrieval/fusion.py) | Docstring: *«C26 (substitutes) is the next caller»* | **Predicción falsa**: con una sola lista no hay nada que fusionar. Se corrige el comentario |
| [`retrieval/orchestrator.py`](../../../../ai-service/src/jbg_ai/retrieval/orchestrator.py) | ~870 líneas, cinco responsabilidades | **No se toca.** El flujo nuevo vive en `substitutes.py` |
| [`evals/execute.py`](../../../../ai-service/src/jbg_ai/evals/execute.py) | Llama a `retrieve_products(RetrievalRequest(...))` **en proceso**, no por HTTP | Camino análogo para `retrieve_substitutes`, en rebanada propia |
| [`evals/golden/queries.jsonl`](../../../../ai-service/evals/golden/queries.jsonl) | 71 consultas, 63 juzgadas. `q49`–`q52` son `sustituto` con `judged: false` y nota *«La hereda C26»* | Se anclan con `source_product_id` y se etiquetan. **Entra una quinta, sin familia** |
| `ai.product_document` | 1.168 vivos · **1.168 con embedding** · índice HNSW · 491 con familia (156 familias de 2-8) · 1.046 con materiales · 1.168 con banda de precio | **Sin migración** |
| `ai.pos_projection` | 6.720 filas, con `qty_bucket`, `sales_30d` y `computed_as_of` | Se lee como señal, nunca como restricción |

### Las tres refutaciones de la propia ficha

| Punto de la ficha | Veredicto |
|---|---|
| «**Misma familia primero**, luego similitud» | **Refutado por medición.** Lidera con los invendibles en 3 de 4 casos y expulsa a `SKU39 Colgante oreja de mar S`, que es mejor sustituto que media familia. La familia entra en el conjunto pero **no impone orden** |
| `test_same_family_variant_ranks_first_when_available` | **Se reescribe** como `test_no_live_family_member_is_dropped_from_the_result`. Lo sostenible es la garantía de recall, no un orden que la medición desmiente |
| `test_excludes_out_of_stock_when_flag_enabled` | **Se retira.** La exclusión por stock está asignada dos veces, y la versión correcta es la de C34 (`Substitutes_ExcludeProductsWithoutStockAtTargetPos`), que respeta la frontera del §6.2: *«Python calcula parecidos; .NET calcula números y decide»* |

---

## Componentes Afectados

- **`ai-service/`** — `src/jbg_ai/retrieval/` (módulo nuevo `substitutes.py`, más `search.py`,
  `ports.py`, `fusion.py`), `src/jbg_ai/api/routers/retrieval.py`, `src/jbg_ai/config/settings.py`,
  `src/jbg_ai/evals/`, `evals/golden/`, `tests/`.
- **`openspec/`** — specs delta del change.
- **`Documentos/`** — informes, plan, épicas, historia.
- **Sin diff** en `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`.

---

## Especificaciones Técnicas

### ai-service (`jbg-ai`)

**Ruta.** `POST /v1/retrieval/substitutes`, ya congelada. Entrada `SubstitutesRequest`
(`product_id`, `top_k`, `filters`, `reason`, `pos_id` ignorado). El **alcance sale del token**
(`pos_id`), nunca del body — regla vigente de `deps.get_service_principal`.

**Puerto.** Dos métodos nuevos en `ProductSearchPort`:

1. Leer el documento origen — `piece_type`, `size_label`, `materials`, `style_tags`, `family_id`,
   `price_band`, `embedding` — o señalar que no existe, está inactivo o carece de embedding.
2. Vecinos por embedding almacenado, con filtro duro `piece_type = :tipo`, exclusión del propio
   `product_id` y de `filters.exclude_product_ids`, y la proyección por punto de venta unida con
   **`LEFT JOIN`** (`signal_pos_id`), nunca con `JOIN`.

**Orden.** Una sola lista, así que **no hay fusión**. Clave descendente:

```
  orden(c) = sim(c)                                sim = 1 − distancia coseno
           − w_size · [talla distinta]             solo si AMBAS declaran talla
           − w_availability · [qty_bucket = '0']   business_score de C25, reutilizado
```

- `w_size` es un ajuste nuevo (`JPV_SUBSTITUTE_WEIGHT_SIZE`, por defecto **0,05**, opcional al
  arranque), **barrido** en la rebanada de evaluación antes de adoptarse. Medido: 0,02 no mueve
  nada y 0,08 manda el hermano al puesto 8; **0,05 interleava**, que es la degradación *suave*
  acordada.
- **Advertencia que hay que llevar al diseño:** la conclusión de C25 *«el valor del peso no cambia
  el orden, solo su signo»* **no se traslada**. Allí el score tomaba dos valores; aquí la cola
  mezcla similitud continua con un término binario, así que el peso fija un tipo de cambio real y
  el barrido tiene sentido.
- `w_availability` es el peso ya calibrado de C25. **Degrada y nunca elimina.**

**Sobre-recuperación.** Se mantiene la regla del contrato: `top_k` es la página que .NET quiere
**después** de hidratar y filtrar, así que el recuperador devuelve más y lo declara en
`candidates_returned`.

**Señales por candidato** (`SimilaritySignals`, contrato congelado):

| Campo | Cálculo | Cobertura medida |
|---|---|---|
| `material_overlap` | Jaccard de `materials` | **97,8 %** de los productos reales tiene par con el que compartir material |
| `style_similarity` | Jaccard de `style_tags` | **1 de 404** productos reales. Se emite y **se declara la ausencia en `match_reasons`** |
| `family_match` | `family_id` igual y no nulo | 491 de 1.168 productos tienen familia |
| `visual_similarity` | **`null`** por diseño | §15.7: los dos espacios vectoriales no se fusionan |

**`match_reasons`** es la vía de explicación para lo que el contrato congelado no puede expresar
—señaladamente la **talla**, que discrimina en 2 de las 4 consultas reservadas—: por ejemplo
`["misma familia", "talla contigua (L) — se pidió M", "mismo material (plata)", "sin etiquetas de
estilo que comparar"]`.

**Abstención.** `low_confidence` se emite **falso** siempre, por decisión medida: todo producto del
catálogo tiene vecino a menos de **0,255**, y el rango de los productos sin familia contiene el de
los que la tienen. Mismo precedente que C25 al dejar su umbral escalar donde estaba.

**Errores.** Producto origen inexistente, inactivo o sin embedding → error explícito que nombra la
causa. **Nunca lista vacía con apariencia de respuesta válida** — es la firma que este proyecto
persigue desde C17.

**Coste.** **Cero llamadas al proveedor**: el embedding de origen está almacenado. Sin rama léxica,
sin expansión de sinónimos, sin fusión. Una consulta SQL.

### Datos

Ninguna entidad, campo ni índice nuevo. `ai.product_document` ya tiene el índice HNSW
(`vector_cosine_ops`), btree sobre `family_id`, `piece_type` y `price_band`, y GIN sobre
`materials`. **Sin migración de Alembic ni de EF Core.** `Documentos/modelo-de-datos.md` no cambia.

### Evaluación

- Las cuatro consultas `q49`–`q52` se anclan con **`source_product_id` explícito**: `SKU13`
  (familia de 4), `SKU77` (familia de 8, **contaminada** con el sintético `SKU610`), `SKU106`
  (familia de 3), `SKU159` (familia de 4, mezcla talla y material).
- **Quinta consulta nueva sin familia**, anclada en `SKU102 Anillo caracola` (real, huérfano), que
  cubre el **58 %** del catálogo que no tiene familia y que hoy ninguna consulta ejercita.
- **Rebanada separada** con informe propio. La tabla de ablations publicada de C24/C25 **no se
  toca**: el endpoint recibe `product_id` y no texto, así que `v0-fts` y `v1-vectorial` ni siquiera
  podrían ejecutarlo, y añadir filas movería su denominador.
- Criterio de etiquetado reutilizado de `criterion.md` sin cambios: su grado 1 ya está redactado en
  términos de sustituto.

---

## Arquitectura

- **Frontera .NET/Python (§6.2 del diseño):** *«Python calcula parecidos y redacta; .NET calcula
  números y decide.»* Por eso la exclusión por stock **no** entra aquí.
- **Invariante de disponibilidad (§15.10 y `ports.py`):** la proyección puede desfasarse minutos;
  `pos_id` **restringe** por surtido y `signal_pos_id` **solo lee**. Nada se elimina por stock.
- **Ausencia no es cero** (`ports.py`, `business_score` de C25): se aplica al término de talla, que
  queda **inerte** si alguna de las dos piezas no declara talla. El **54 % de los anillos** no tiene
  `size_label`, así que sin esta guarda media población se ordenaría por un desajuste inexistente.
- **Bloques enteros frente a score continuo (C25, `filters.py`):** un bloque entero **particiona**
  —11.067 pares invertidos con la rotación, el 71,2 % a más de diez puestos—. La talla va en la cola
  continua, no como bloque.
- **Breaking changes:** ninguno. El contrato REST de .NET no se toca y el snapshot OpenAPI no se
  mueve. El único cambio observable es que una ruta que devolvía 501 pasa a devolver 200.

---

## Definición de Hecho (DoD)

- [ ] `retrieval/substitutes.py` implementado según las capas de `Documentos/modelo-c4.md`
- [ ] `uv run --system-certs pytest` en verde, **sin llamadas reales** a LLM, embeddings ni RDS
- [ ] Comparación de la suite por **nombres** de test en rojo contra la línea base, nunca por recuento
- [ ] `test_openapi_snapshot_is_stable` en verde: `ai-service/openapi.json` **sin diff**
- [ ] Sin migración de Alembic ni de EF Core
- [ ] Specs delta en `openspec/changes/add-substitutes-retrieval/specs/` y
      `openspec validate --all --strict` con **0 failed**
- [ ] Rebanada de evaluación ejecutada, peso de talla barrido e informe publicado
- [ ] Tabla de ablations de C24/C25 verificada **sin cambios**
- [ ] Documentación actualizada: README del servicio, README de tests, informe de implementación,
      `Documentos/epicas.md` y el plan de changes
- [ ] Sin diff en `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`, verificado contra el
      punto de nacimiento de la rama
- [ ] Sin TODO/FIXME sin tarea de seguimiento

### Tests

| Test | Qué fija |
|---|---|
| `test_never_returns_a_different_piece_type` | Filtro duro; el vector puro lo viola en 2 de 4 casos |
| `test_source_product_never_returned_as_own_substitute` | Auto-exclusión |
| `test_no_live_family_member_is_dropped_from_the_result` | Garantía de recall de variantes declaradas |
| `test_same_size_candidate_outranks_same_family_different_size` | El hallazgo de la exploración; caso real `SKU13` |
| `test_different_size_sibling_stays_inside_the_visible_window` | Que la degradación sea **suave** y no un destierro |
| `test_size_term_is_inert_when_either_side_declares_no_size` | Ausencia ≠ desajuste; el 54 % de los anillos |
| `test_material_overlap_increases_similarity_score` | La señal que sí tiene cobertura |
| `test_out_of_stock_candidate_is_demoted_and_never_removed` | Invariante §15.10 |
| `test_substitutes_never_abstains_and_says_so` | D5, declarado y no aplazado |
| `test_style_similarity_absence_is_declared_in_match_reasons` | Un cero que no miente |
| `test_no_embedding_provider_call_is_made` | Doble que falla al ser invocado |
| `test_unknown_or_unindexed_source_product_is_an_explicit_error` | Nunca una lista vacía con apariencia de éxito |

---

## Requisitos No Funcionales

- **Seguridad**: JWT interno HS256; `pos_id`, `role` y `trace_id` salen del token y **el token manda
  sobre el body**. El navegador nunca llama a Python.
- **Rendimiento**: pool limitado a 5 sin overflow — **una** conexión por petición y **una** sentencia.
  Sin llamada al proveedor, así que el presupuesto de latencia de retrieval (0,8 s) queda holgado.
  Sobre 1.168 filas el planificador elige escaneo exacto, como midió C22.
- **Observabilidad**: `trace_id` propagado; traza de la etapa con número de candidatos y cuántos se
  degradaron por talla y por disponibilidad; `projection_age_seconds` declarado en la respuesta.
- **Integridad**: Python **no escribe** en `public` ni lo lee por SQL; la autoridad sobre stock y
  precio sigue siendo .NET.

---

## Preguntas Abiertas — **resueltas el 2026-09-12**

Las cuatro se plantearon con una opción por defecto y **el negocio confirmó aplicar esas cuatro
opciones tal cual**. Se conservan con su pregunta original en vez de reescribirse como afirmaciones:
una decisión sin la alternativa que descartó no se puede revisar más adelante.

| # | Pregunta | **Decisión aplicada** |
|---|---|---|
| 1 | ¿El barrido confirma `w_size = 0,05`? | **Gana el barrido sobre las cinco consultas.** Si la diferencia entre candidatos es menor que el ruido, **`0,05`**, por ser el valor medido como interleave. El número **no se fija por argumento**: si el barrido señala otro, se adopta el otro y se declara en el informe |
| 2 | ¿La banda de precio entra en el orden? El §6.3.2 de las especificaciones funcionales la pide con peso «medio-alto», pero `SimilaritySignals` declara por escrito *«no price signal by design»* | **No entra en el orden.** Se declara en `match_reasons` cuando difiere. Meterla obligaría a fijar un peso que **ninguna consulta del golden set puede medir**, y este proyecto no adopta pesos que no puede calibrar. Queda anotado como divergencia consciente frente al §6.3.2 |
| 3 | ¿`reason` del request llega a gobernar algo? Es texto libre en el contrato | **No gobierna nada.** Se propaga a la traza. Convertirlo en enumerado exigiría mover el contrato congelado |
| 4 | ¿La ventana de sobre-recuperación es la misma que la de `retrieve_products` (`min(top_k·3, 60)`)? | **Sí**, por coherencia, hasta que la rebanada de evaluación diga otra cosa. Si la evaluación la mueve, se declara con su cifra |

**Consecuencia para el apply:** ninguna de las cuatro bloquea. Las decisiones 2, 3 y 4 se
implementan tal como están escritas; la 1 es la **única con una cifra pendiente de medir**, y su
valor sale del barrido y no de esta tabla.

---

## Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| Prioridad | **Alta** — único eslabón vivo de la cadena crítica `C26 → C34 → C36` |
| Estimación | _Pendiente_ — a fijar en refinamiento |
| Tags | `ai-service` · `retrieval` · `substitutes` · `pgvector` · `evaluation` · `no-migration` · `frozen-contract` |

---

## Enlaces o Referencias

- HU origen: [HU-AIENG-026](../../../../Documentos/Historias/AI-Eng/HU-AIENG-026.md)
- Change: [`add-substitutes-retrieval`](./)
- Mediciones: [c26-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c26-exploration-measurements.md)
- Plan de changes: [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), ficha C26
- Diseño RAG: [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) §4 fila 6, §6.2, §7.6, §15.10
- Ticket previo: [T-AIENG-025](../../archive/2026-09-12-recalibrate-ranking-and-abstention/ticket.md)
- Procedimientos: [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-12 | Creación del ticket a partir de la exploración de C26: siete decisiones de diseño (D1-D7), seis mediciones contra el Postgres local y tres puntos de la ficha del plan refutados |
| 2026-09-12 | **Las cuatro preguntas abiertas quedan resueltas**, aplicando las opciones por defecto propuestas. Ninguna bloquea el apply; la única cifra pendiente es `w_size`, que sale del barrido |
