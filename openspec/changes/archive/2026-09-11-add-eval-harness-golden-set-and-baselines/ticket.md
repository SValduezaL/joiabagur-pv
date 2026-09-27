# T-AIENG-024: Evaluation harness, hand-labelled golden set and retrieval baselines (C24)

> Ticket técnico del change OpenSpec `add-eval-harness-golden-set-and-baselines`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, specs vivas de `openspec/specs/`, [HU-AIENG-024](../../../../Documentos/Historias/AI-Eng/HU-AIENG-024.md) y las decisiones cerradas de [c24-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c24-exploration-measurements.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-024 / C24** — Construir el juez imparcial del recuperador: tablas `ai.eval_*`, golden set de 48 consultas juzgadas con relevancia graduada, CLI de ejecución reproducible y cinco líneas base que responden por fin la decisión 12

---

## Contexto y Problema

El recuperador híbrido está completo —expansión (C20), fusión RRF de tres listas (C21), prefiltro por punto de venta (C22)— y **ninguna de sus decisiones se tomó con una métrica de relevancia**. Se tomaron con una rúbrica de conveniencia que los propios informes declararon insuficiente, y los cuatro escribieron la misma frase: *«C24 lo re-mide»*.

La rúbrica que gobierna todas esas decisiones cuenta aciertos como *«tipo de pieza correcto y material correcto»*. El informe de C21 la recusa él mismo: *«`doc_text` lleva líneas canónicas `Tipo:` y `Materiales:`, y la expansión apunta justo ahí; medir "tipo correcto y material correcto" premia por construcción a quien casa esas líneas»*. Bajo ese juez, la rama vectorial saca **67 de 120** frente a **107** de la léxica sola y **113-114** de la mejor fusión: siete puntos de ciento veinte para justificar el proveedor externo, los 170-1707 ms por consulta y el índice HNSW.

**El riesgo dejó de ser teórico el 2026-09-06.** En el corpus de conocimiento, C23 midió con un embebedor sustituto que *«la rama léxica gana +6,2 pp de Recall@3»*; al re-medir contra el proveedor real el veredicto **se invirtió** —93,8 % en las dos configuraciones, la rama léxica sólo mejora el orden— y el informe lo escribe sin adornos: *«el +6,2 pp del §1 era un efecto del sustituto léxico, no una propiedad del sistema»*. El umbral que aquel sustituto calibró (0,81) resultó **citar 4 de las 5 preguntas fuera de dominio**: no una imprecisión, sino el mecanismo de abstención inoperante. El valor correcto contra el embebedor real es **0,51**.

Ese episodio fija dos requisitos de este change: **se mide contra el proveedor real y el índice real**, y **ninguna constante del arnés puede a la vez gobernar una medición y aseverar un default de producción** — que es exactamente la causa de fondo que C23 documentó: *«ese test pasaba en verde mientras el defecto se enviaba, porque ataba dos números que viven en escalas distintas»*.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `retrieve_products(...)` con **nueve knobs por parámetro** además del default en `Settings` | Existe (C20/C21/C22) · su docstring dice literalmente *«C24 sweeps configurations inside one process»*. **El barrido no hay que construirlo** |
| `retrieval/search.py` — `ORDER BY d.embedding <=> :q ASC` (l. 99) y `ORDER BY coordination DESC, ts_rank DESC` (l. 124) | Existen · **sin tercera clave de desempate**. Con `LIMIT 60` y empates de `ts_rank`, qué filas sobreviven no está definido |
| `ai.eval_run` / `ai.eval_case` / `ai.eval_result` | **No existen.** La migración fundacional `f46c55c056e2` no las crea |
| `GET /v1/evals/runs` + `EvalRunsResponse` (`run_id`, `suite`, `status`, `started_at`, `finished_at`, `metrics[]`) | **Publicado en el `openapi.json` congelado**, montado sólo con `ENABLE_DEV_ENDPOINTS` · stub que **nombra a C24** como quien lo entregará |
| `ai.product_document.data_origin` (`NOT NULL`) y `.source_hash` (`CHAR(64) NOT NULL`) | Existen (C05/C11) · el desglose y el anclaje de juicios no necesitan columnas nuevas |
| `indexing/set_hash.py` — huella estable de un conjunto, orden **sin signo** | Existe (C17) · es el `index_set_hash` de la tupla de procedencia |
| `retrieval/measure.py` — `measure` (C20) y `compare` (C21), read-only, informe a `evals/results/` | Existe · su docstring dice *«A real evaluation CLI with graded relevance is C24»* |
| `knowledge/measure.py` — fixture, Recall@3, MRR, abstención, comparación de arms | Existe (C23) · *«It does not touch `ai.eval_run`, `ai.eval_case` or `ai.eval_result`. Those tables belong to C24»* |
| `ai-service/evals/results/` con `c20-…md` y `c21-…md` | Existe · el sitio del informe está fijado |
| `ai-service/evals/golden/`, `ai-service/evals/configs/`, `ai-service/src/jbg_ai/evals/`, `ai-service/tests/evals/` | **No existen** |
| `ProductService.SearchProductsAsync` — `Name.Contains(query)` + SKU exacto, en memoria, orden alfabético | Existe · **es el buscador anterior al trabajo de IA**: la línea base de la decisión 12 |
| `AssistedSearchRepository.SearchLexicalAsync` — `to_tsvector('spanish', Name+SKU+Description)`, `websearch_to_tsquery`, OR, `ts_rank` | Existe (C15/C16) · es la **ruta degradada**, construida por el propio trabajo de IA |
| `ai.product_document` — tiene `name`, `sku`, `doc_text`; **no tiene `description`** | `doc_text` es `source-text/v1` completo: un FTS sobre él es **cota superior**, no réplica |
| `SearchHit.price` | Existe · *«Carried for the demoting filters of C21 and **never** emitted: the boundary rule is that .NET owns price»* |
| `JPV_RETRIEVAL_DISTANCE_THRESHOLD` = 0,65 | Existe (C14) · medido en C21 §9: deja pasar **1.168 de 1.168** en consultas ordinarias |
| CAG en el repositorio | **Cero líneas, cero menciones** en `ai-service/README.md`. Sólo aparece en el diseño §11.2 y en los checklists del PF |
| Artefactos OpenSpec de este change | **A generar** (0/4, schema `spec-driven`) |

**Impacto en producto:** ninguno visible para el operador. El impacto es sobre **la capacidad de decidir**: sin este change, la arquitectura RAG entera está justificada por argumento, la pregunta central del PF —¿mejora sobre lo que había?— no tiene respuesta, y C25 no tiene contra qué calibrar sus pesos.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/evals/` | **Alto** — paquete nuevo: `golden.py`, `pooling.py`, `metrics.py`, `configs.py`, `runner.py`, `report.py`, `repository.py`, `cli.py` |
| `ai-service/evals/golden/` | **Alto** — golden set versionado: `criterion.md`, `queries.jsonl`, `judgements.jsonl`, `query_vectors.jsonl`, `pricing.yaml` |
| `ai-service/evals/configs/` | **Medio** — cinco configuraciones declarativas |
| `ai-service/migrations/versions/` | **Medio** — **una** revisión con las tres tablas `ai.eval_*` |
| `ai-service/src/jbg_ai/retrieval/search.py` | **Bajo** — dos líneas de desempate. **Desviación declarada: toca ruta viva** |
| `ai-service/src/jbg_ai/api/routers/evals.py` | **Bajo** — deja de ser stub; sirve desde `ai.eval_run` sin mover el contrato |
| `ai-service/src/jbg_ai/config/settings.py` | **Bajo, condicional** — sólo si D13 se dispara |
| `ai-service/tests/evals/` | **Alto** — batería nueva, ejecutable sin proveedor |
| `ai-service/evals/results/` | **Medio** — informe de la tabla de ablations y `runs/<run_id>.jsonl` |
| `ai-service/README.md` | **Bajo** — comando, filas de entorno y limitaciones declaradas |
| `openspec/changes/<change>/specs/` | **Alto** — capacidad nueva `retrieval-evaluation` |
| `Documentos/` | **Medio** — `epicas.md` (EP17) e informe de implementación |
| `ai-service/openapi.json` · `backend/` · `frontend/` · `terraform/` · `.github/workflows/` | **Ninguno** |

---

## Especificaciones Técnicas

### Golden set (`ai-service/evals/golden/`)

**48 consultas juzgadas, 56 escritas, suelo duro 45.** Una fila por pleito, sin categorías de relleno.

| Categoría | Nº | Pleito | Recortable |
|---|---:|---|---|
| Descripción natural **sin anclaje léxico** | **12** | P1 — vector vs léxica | **No** |
| Variante / talla | **7** | el caso crítico del dominio | **No** |
| Materiales (incl. multi-valor) | 5 | P3 — solape `&&` vs `@>` | a 4 |
| Piedra (aísla `stone_type`) | 4 | P3 — pregunta abierta de C21 §12 | a 3 |
| Subjetiva (ocasión / estilo / regalo) | 5 | P3 — la propiedad emergente | a 4 |
| Sinónimos (2 por cada uno de los 3 tipos) | **6** | P4 | **No** |
| Léxico exacto (SKU y nombre) | 4 | P7 — donde el baseline puede ganar | a 3 |
| Fuera de dominio **plausible** | 5 | P5 — abstención | **No** |
| **Total juzgado** | **48** | | |
| Sustituto / sin stock — *declaradas, `pooled_in: []`* | 4 | C26 | — |
| Ambigua → requiere aclaración — *declaradas* | 4 | C30 | — |

Diferencias frente al §11.1 del diseño, todas con motivo medido: desaparece «descripción natural con anclaje» (era relleno, ese control lo dan materiales y sinónimos); «precio/ocasión/regalo» encoge de 8 a 5 porque `Ocasiones:` cubre el 13 % del corpus y `boda` casa 5 documentos de 1.168; y aparece «piedra» (4), que cierra la pregunta abierta de C21 §12.

**Matriz de trazabilidad, comprobada por código al cargar el golden set.** `golden.py` **falla la carga** si no se cumple:

| Requisito | Nº mínimo |
|---|---:|
| Consultas con ≥1 documento de grado 2 cuyo `doc_text` **no contiene ningún término de la consulta tras `expand_query`** | 12 |
| Consultas que resuelven a `occasion_tags` o `style_tags` y a ningún campo de cobertura alta | 5 |
| Consultas que nombran un valor de `stone_type` sin que `piece_type` discrimine | 4 |
| Cobertura de los 3 tipos del diccionario: artefacto de stemmer · sinónimo comercial · puente direccional | 6 |
| Consultas plausibles en dominio con **cero** documentos de grado ≥1 | 5 |
| Consultas que son un SKU o un nombre literal | 4 |

**Anclaje a productos reales por categoría**, no globalmente: ninguna categoría puede quedar íntegramente sintética, porque un desglose por `data_origin` con una categoría de un solo origen no es comparable.

### Escala de relevancia (`criterion.md`, escrito antes de etiquetar)

```
 2  Se lo enseño al cliente como respuesta a ESA consulta.
 1  Mismo piece_type o misma familia, pero falla UN atributo que la consulta
    nombró explícitamente (talla, uno de varios materiales, color, piedra).
    O bien: sustituto plausible que el operador ofrecería como segunda opción.
 0  Todo lo demás.
```

Lectura binaria derivada y publicada junto a la graduada: `relevante ⇔ grado ≥ 1`.

### Esquema de ficheros

```jsonl
# queries.jsonl
{"id":"q07","text":"...","category":"descripcion-sin-anclaje","in_tuning_set":false,
 "expected_origin":"real","judged_depth":40}

# judgements.jsonl   — clave (query_id, product_id), APENDABLE
{"query_id":"q07","product_id":"…","grade":2,"pooled_in":["v1-vectorial","v2-hibrido"],
 "judged_at":"2026-09-…","source_hash":"a3f…"}

# query_vectors.jsonl — 6 decimales, ~700 KB
{"query_id":"q07","model_version_key":"openai/text-embedding-3-small:1536:…",
 "vector":[0.012345, -0.098765, …]}
```

### Migración Alembic (una sola revisión)

```
ai.eval_run     run_id (uuid PK) · config_id · golden_set_version · index_set_hash
                · embedding_model_version_key · git_sha · started_at · finished_at
                · status · metrics jsonb · documents_omitted int · notes text
ai.eval_case    run_id FK · query_id · category · in_tuning_set · data_origin_bucket
                · judged_depth · métricas por consulta jsonb
ai.eval_result  run_id FK · query_id · product_id · rank · score · grade (nullable)
                · unjudged bool
```

`metrics jsonb` en vez de columnas por métrica: C38 añadirá métricas de generación al mismo runner y no debe forzar una segunda revisión. Índices: por `config_id` y por `started_at` sobre `eval_run`; `(run_id, query_id)` sobre `eval_case`; `(run_id, query_id, rank)` sobre `eval_result`.

### Las cinco configuraciones

| Config | Qué hace | Coste/consulta |
|---|---|---:|
| `v0-nombre` | Réplica de `ProductService.SearchProductsAsync`: coincidencia de subcadena sobre `name` + SKU exacto, orden alfabético | **0** |
| `v0-fts` | Réplica de `AssistedSearchRepository.SearchLexicalAsync`: `to_tsvector('spanish', name ‖ ' ' ‖ sku ‖ ' ' ‖ <línea Descripción de doc_text>)` con `websearch_to_tsquery`, términos OR, orden `ts_rank` | **0** |
| `v0-cag` | Catálogo completo compactado en contexto, **sin recuperación y sin precio** | ~$0,0039 |
| `v1-vectorial` | `mode=vector`, sin rama léxica | ~$0,0000002 |
| `v2-hibrido` | Configuración viva: `mode=hybrid`, expansión activa, filtros estructurales | ~$0,0000002 |

**Fidelidad de `v0-fts`.** `ai.product_document` no tiene columna `description`; `doc_text` es el `source-text/v1` completo (`SKU · Nombre · Descripción · Colección · Tipo · Materiales · Piedra · Talla · Familia · Variante · Colores · Estilo · Ocasiones`). Un FTS sobre `doc_text` vería más de lo que ve .NET, así que la sentencia **recompone** el texto equivalente extrayendo la línea `Descripción: `. Un test fija ese prefijo como contrato del renderizador, para que un cambio en `build_source_text` rompa el test y no la fidelidad en silencio. Leer `public."Products"` está descartado: el puerto declara *«implementations must not read `public`»*.

**`v0-cag`, forma acotada.** No es una fila de calidad: es la prueba medida de por qué existe RAG, porque CAG no tiene una sola línea en el sistema y el PF exige describir *«CAG/RAG»* como componentes. Produce (1) tokens y coste del catálogo compactado, (2) Recall@5 sobre el subconjunto de 12 consultas sin anclaje léxico —donde CAG debería brillar por tener el catálogo entero delante—, (3) curva de escala hasta 2.500 y 5.000 productos. Contexto: `sku · nombre · tipo · materiales`, una línea por producto, **sin precio** por la regla de frontera. Es una medición fechada y no reproducible bit a bit: se registra con su modelo y su fecha y no se re-ejecuta en cada run.

### *Pooling* de profundidad adaptativa

```
 1. Base 20 en las cuatro configuraciones indexadas (= el top_k×3 que recibe .NET).
 2. Se continúa en bloques de 10 mientras el bloque anterior haya dado ≥1 grado ≥1.
 3. Tope 60 = branch_depth: más allá, el pipeline vivo no puede mostrarlo.
 4. judged_depth se registra por consulta.
```

Estimación: ~1.500-2.000 juicios, **~3 h 15**, en tres sesiones agrupadas por categoría. Lo no juzgado cuenta grado 0 (supuesto estándar, declarado), y por eso se reporta `unjudged@5` por configuración.

### Métricas

| Métrica | Nota |
|---|---|
| `ndcg_at_5` | Con grados 0-2 |
| `recall_at_5`, `precision_at_3`, `mrr` | Con la lectura binaria `grado ≥ 1`, y publicadas también en graduado donde aplique |
| `abstention_rate` | Sobre la categoría fuera de dominio. **Provisional**, ver D8 |
| `unjudged_at_5` | Proporción del top-5 sin juicio. Marca una fila como no comparable |
| `desplazamiento_sintetico_at_5` | Fracción de consultas reales en las que un sintético de grado 0 precede al primer grado 2 real |
| `p50_retrieval` / `p95_retrieval` | Sin el ida y vuelta del proveedor. **Es la que lleva el criterio de aceptación** |
| `p50_e2e` / `p95_e2e` | Con el proveedor. Va al README junto al presupuesto de C16 |
| `cost_per_query_usd` | Desde `pricing.yaml`. **Cero es un valor registrado, no un hueco** |
| `stale_judgements` | Juicios cuyo `source_hash` ya no coincide |

**Desglose por `data_origin` (D5):** la recuperación corre **siempre sobre los 1.168 documentos**; las consultas se agrupan por el origen de sus relevantes y el recuento considera sólo los relevantes de ese origen. Restringir el corpus a un origen **no es una configuración disponible**.

**Tres lecturas por métrica (D4):** global · sólo `in_tuning_set` · sólo consultas nuevas.

**Latencia:** se descarta la primera ejecución y se toman 3 por consulta (48 × 3 = 144 muestras). La instrumentación ya existe: el orquestador emite `latency_ms` por etapa (`expand`, `embed`, `projection`, `lexical`, `search`, `fuse`).

### Reproducibilidad

**Tupla de procedencia** guardada por `eval_run`: `(golden_set_version, config_id, index_set_hash, embedding_model_version_key, git_sha)`. Dos ejecuciones cuya tupla no coincide se marcan como no comparables.

**Desempate determinista** en `retrieval/search.py`: `, d.product_id` como última clave en las dos sentencias. Es una **desviación declarada** —la ficha describe C24 como change de evaluación y esto toca ruta viva— y se hace porque sin ella `test_run_is_reproducible_for_same_config_and_seed` pasa en verde mientras el arnés produce ruido. Precedente: C22 abrió una revisión de Alembic contra su propia ficha y lo escribió.

**Regla heredada de C23**, que este change debe respetar en el diseño de sus tests: ninguna constante del arnés puede a la vez gobernar una medición y aseverar un default de producción. Si un test compara ambos, comprueba que son **distintos** y explica por qué copiarlos vuelve a romperlo.

### Persistencia *artifact-first*

```
 runner  ──produce──▶  Report (objeto en memoria)
                          ├──▶ report.py      → Markdown + JSONL en git   [SIEMPRE]
                          └──▶ repository.py  → ai.eval_run/case/result   [SÓLO --persist]

 El runner no importa repository.py: no sabe que la base de datos existe.
```

`GET /v1/evals/runs` deja de ser stub leyendo `ai.eval_run`, **sin regenerar `openapi.json`**: la ruta ya está publicada y `EvalRunsResponse` encaja con las columnas de esa tabla. Sigue montada sólo con `ENABLE_DEV_ENDPOINTS`.

### Cambio de defaults (D13)

```
 Se cambia un default de Settings si y sólo si:
   · delta de nDCG@5 > 0,05, Y
   · mismo signo en las tres lecturas de D4, Y
   · ninguna de las 7 categorías medibles empeora más de 0,05.
```

Candidatos posibles: `JPV_RRF_WEIGHT_VECTOR` y `JPV_BRANCH_DEPTH`. El barrido es **direccional**: la rúbrica de C21 infravalora la rama vectorial por construcción, así que el óptimo verdadero está en `wC ≥ 0,33`. **No** se toca `JPV_RETRIEVAL_DISTANCE_THRESHOLD`: es alcance de C25.

---

## Arquitectura

- **Frontera .NET / Python intacta.** El arnés vive íntegramente en Python, lee sólo el esquema `ai` y no llama a `backend/`. Las dos réplicas de líneas base reproducen **semánticas** de .NET sobre datos del esquema `ai`, no consultas contra `public`.
- **Contrato congelado, sin movimiento.** `openapi.json` no cambia. La ruta de evals ya está publicada; el change la llena.
- **Autoridad sobre el precio.** `RetrievalResult` no emite precio y el contexto de CAG tampoco lo lleva. La decisión no es de comodidad: C38 entregará un validador determinista que contrasta toda cifra de precio de la respuesta final contra el hidratador, y meter precios en un prompt desde Python abriría por adelantado la superficie que ese validador existe para cerrar.
- **Patrón de sumidero (`sink`)**, alineado con la inyección de dependencias ya usada en `retrieve_products`: el productor construye un `Report` y no conoce a sus consumidores.
- **Reutilización, no reescritura.** El arnés **importa** `retrieve_products`, `expand_query`, `fuse` y el `LiteLlmEmbeddingClient` existentes. No duplica pipeline: si lo duplicara, mediría una copia y no el sistema — que es la versión sutil del error que C23 acaba de cometer con su embebedor sustituto.
- **Breaking changes:** ninguno en contratos REST ni en el snapshot OpenAPI. El único cambio observable en la ruta viva es el orden entre documentos empatados, que hoy es indefinido.

---

## Definición de Hecho (DoD)

- [ ] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] `ai-service`: `uv run pytest` en verde **sin llamadas reales a LLM, embeddings ni RDS**; los tests del arnés usan fixtures y dobles
- [ ] `openapi.json` **byte a byte idéntico** (verificado por el test de snapshot)
- [ ] Revisión de Alembic creada, aplicable y reversible; `ai.eval_run` legible por `GET /v1/evals/runs`
- [ ] `golden.py` **falla la carga** si la matriz de trazabilidad no se cumple, con un test por requisito
- [ ] Desempate determinista en las dos sentencias, con test que lo demuestra sobre puntuaciones empatadas
- [ ] Informe versionado en `ai-service/evals/results/` con la tabla v0→v2, las tres lecturas de D4, la distribución de distancias por grado y la curva de escala de CAG
- [ ] Spec de la capability `retrieval-evaluation` en `openspec/changes/<change>/specs/` y `openspec validate --all --strict` en **`0 failed`**
- [ ] Suite completa comparada **por nombre de test** contra la línea base previa al change (regla de `CLAUDE.md`: el recuento no es señal)
- [ ] Documentación actualizada: `ai-service/README.md` (comando, entorno, limitaciones) y `Documentos/epicas.md` (EP17)
- [ ] Las cuatro limitaciones declaradas en el README: sin acuerdo entre anotadores · el etiquetador escribió parte del corpus · conjunto pequeño con IC de ±0,13 sobre la porción real · coste del prefiltro sin medir si se recorta la fila escopada
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] Documentación y textos en español (es-ES); identificadores técnicos en inglés

---

## Requisitos No Funcionales

- **Seguridad.** `GET /v1/evals/runs` conserva la autenticación por JWT interno HS256 y sigue montada sólo con `ENABLE_DEV_ENDPOINTS`: bajo perfil de producción la ruta **no existe**, en lugar de responder un 404 documentado y engañoso. El arnés no expone ninguna ruta nueva. Ningún secreto entra en el repositorio: `pricing.yaml` lleva precios públicos, no credenciales.
- **Rendimiento y free-tier.** El pool de conexiones sigue capado a 5 y el arnés es un cliente más: las configuraciones se ejecutan **en serie**, nunca en paralelo, porque tres runs concurrentes agotarían el pool que la ruta viva comparte. Los vectores congelados evitan 48 × N llamadas de pago por ejecución. El coste medido del change completo es de céntimos: ~48 embeddings una vez y ~12 llamadas de CAG.
- **Observabilidad.** El arnés reutiliza los logs por etapa que ya emite el orquestador (`stage=expand|embed|projection|lexical|search|fuse`) y no añade un canal propio. Cada ejecución queda trazada por su tupla de procedencia, que es lo que permite reconstruir a posteriori con qué índice y con qué código se obtuvo un número.
- **Integridad de datos.** El arnés es **read-only sobre el índice**: no escribe en `ai.product_document`, no reindexa y no toca `ai.pos_projection`. Lo único que escribe son las tres tablas `ai.eval_*`, y sólo bajo `--persist`. El golden set y sus juicios viven en git, de modo que modificar la vara de medir exige revisión de código.
- **Reproducibilidad como requisito no funcional de primera clase.** Es la razón de ser del change: sin ella el arnés mide, pero no compara — y comparar es lo que S16 identifica como el valor real de un arnés.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | **Modelo para `v0-cag`.** ¿`gpt-4o-mini` vía la configuración `JPV_RAG_LLM_*` ya existente, u otro? | `gpt-4o-mini` con `JPV_RAG_LLM_*`, temperatura 0, registrando modelo y fecha en el informe |
| 2 | **Precios de `pricing.yaml`.** Los valores deben verificarse contra la fuente el día de la implementación; los que aparecen en el informe de exploración son orientativos | Verificar contra `https://openai.com/api/pricing/` y sellar `as_of` con la fecha de la corrida. **Si la fuente no es accesible, se registra `as_of: unknown` y el coste se declara no verificado**, en vez de copiar cifras de memoria |
| 3 | **Fila escopada por punto de venta** (P6). ¿Entra en alcance o queda como recortable declarado? | **Recortable declarado.** Si se cae, el README dice que el coste del prefiltro en recall queda sin medir. Si entra, se ejecuta contra un POS nombrado excluyendo `HT-ARTRUTX`, que tiene surtido cero y responde 503 |
| 4 | **Tamaño real de la porción real.** Sólo se sabrá al escribir las 48 consultas; la estimación es ~25-30 | Si baja de 20, el criterio de aceptación sobre la porción real **se declara no concluyente** en el informe en lugar de darse por cumplido o incumplido |
| 5 | **Nombre de la capability nueva.** `retrieval-evaluation` frente a `eval-harness` | `retrieval-evaluation`, coherente con `vector-retrieval`, `hybrid-fusion` y `query-expansion`, y con sitio para las métricas de generación que traerá C38 |
| 6 | **¿Se persisten los runs de las líneas base sin coste (`v0-nombre`, `v0-fts`)?** | Sí. Una tabla de ablations en la que faltan las filas de referencia no es una tabla de ablations |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta.** Es el único change pendiente que bloquea a dos (C25 y C38) y está en la cadena crítica `C21 → C24 → C25 → C26 → C34 → C36`.
- **Estimación:** _Pendiente_. Dos sesiones según la ficha: arnés y configuraciones primero, etiquetado después. El etiquetado se estima en **~3 h 15** repartidas en tres sesiones por categoría.
- **Tags:** `ai-service` · `evaluation` · `golden-set` · `retrieval` · `alembic-migration` · `no-openapi-change` · `no-backend-change` · `live-path-deviation` · `C24` · `EP17`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-024](../../../../Documentos/Historias/AI-Eng/HU-AIENG-024.md)
- **Decisiones y pleitos:** [c24-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c24-exploration-measurements.md)
- **Informes que dejaron pleitos abiertos:** [c21-hybrid-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md) · [c22-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c22-implementation-measurements.md) · [c23-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c23-implementation-measurements.md)
- **Diseño RAG:** [§7.6, §8.1.1, §11.1, §11.2, §15](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Plan de changes:** [ficha C24](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Specs vivas:** `openspec/specs/vector-retrieval/` · `openspec/specs/hybrid-fusion/` · `openspec/specs/query-expansion/` · `openspec/specs/pos-projection/` · `openspec/specs/ai-vector-schema/` · `openspec/specs/ai-service-api-contracts/`
- **Procedimientos:** [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Apuntes:** [S10 · Medición artesanal de relevancia](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Como%20saber%20reranking%20compensa%20-%20medicion%20artesanal%20relevancia%20.md) · [S16 · Tratamiento de regresiones](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Tratamiento%20de%20regresiones.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-06 | Creación del ticket con `/enrich-us`, sobre las trece decisiones cerradas en la exploración del mismo día. Incorpora la evidencia de `5ec4b95` (recalibración del umbral de conocimiento): el sustituto offline produjo un mecanismo de abstención inoperante e invirtió el veredicto sobre la rama léxica, lo que fija el requisito de medir contra el proveedor real y la regla sobre constantes compartidas entre escalas |
