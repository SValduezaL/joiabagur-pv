# T-AIENG-021: Hybrid search — lexical branch, three-list RRF fusion and demoting structural filters (C21)

> Ticket técnico del change OpenSpec `add-hybrid-search-rrf`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-021](../../../../Documentos/Historias/AI-Eng/HU-AIENG-021.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C21, §0), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§5, §6.4, §7.3, §7.6), [informe de mediciones del 2026-09-02](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md), y código de `ai-service/src/`, `backend/src/` y `frontend/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-021 / C21** — Búsqueda híbrida: rama léxica sobre `tsv` con OR y ordenación por coordinación, fusión RRF de tres listas con pesos configurables, filtros estructurales por reglas que degradan y nunca excluyen, degradación honesta a léxico cuando cae el proveedor, y singleton del cliente de embeddings con caché acotado

---

## Contexto y Problema

C05 creó `ai.product_document.tsv` —`to_tsvector('spanish', doc_text)`, **columna generada** con índice GIN— y está **poblada en las 1.168 filas vivas sin un solo consumidor** desde entonces. C14 construyó la rama vectorial y dejó `mode=hybrid` y `mode=lexical` ejecutando la vectorial, diciéndolo en `debug.notes` con la nota `vector_only_until_c21`. C20 fabricó el diccionario de expansión, que hoy **se calcula, se registra en `stage=expand` y no lo lee nadie**.

C21 enchufa los dos cables. Y el problema que resuelve está medido, no supuesto: hoy la rama vectorial **acierta 67 de 120** en el top-10 sobre doce consultas de operador —`sortija de plata` 4/10 con *Pulsera Río de Plata* en primera posición, `criollas de oro` 1/10, `dije de plata` **0/10**— y, lo que es peor, **no abstiene**: devuelve siempre sus candidatos bajo el umbral, así que el fallo llega a la pantalla con apariencia de acierto. Es la firma que C17 encontró siete veces.

### Las nueve mediciones que gobiernan el diseño

Todas del **2026-09-02**, contra el PostgreSQL local (1.168 documentos vivos) y contra `openai/text-embedding-3-small` real. El registro completo, con las 36 configuraciones barridas, está en [c21-hybrid-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md).

**1. Cobertura del corpus — decide qué puede filtrar y qué no.**

| línea de `doc_text` | documentos | % |
|---|---:|---:|
| `Tipo:` | 1.157 | 99 % |
| `Materiales:` | 1.042 | 89 % |
| `Talla:` | 529 | **45 %** |
| `Colores:` | 224 | 19 % |
| `Ocasiones:` | 150 | **13 %** |
| `Estilo:` | 133 | **11 %** |

`boda` casa **5** documentos y `regalo` **7** en todo el catálogo, pese a estar ambos en `occasion_tags`. Cualquier regla que exija un término de ocasión o estilo trabaja sobre un campo cubierto al 11-13 %.

**2. La conjunción estricta deja muda a la rama léxica.** Sobre las **10 consultas reales** de `public."ProductSearchEvents"`, `&&` entre grupos devuelve **cero en 7**, y el *zero-drop* —descartar los grupos que no casan nada— **rescata sólo 1**:

| consulta real | A tecleada | B · AND | B · zero-drop | B · OR |
|---|---:|---:|---:|---:|
| un anillo de plata para regalar | 0 | **0** | **0** | 767 |
| collar elegante para una boda | 0 | **0** | **0** | 259 |
| pulsera de plata con motivos marinos | 0 | **0** | **0** | 832 |
| joya con forma de concha marina | 0 | **0** | **0** | 175 |
| anillo de filigrana tradicional menorquina | 0 | **0** | **0** | 350 |
| algo dorado para el dia de la madre | 0 | **0** | 46 | 506 |
| anillo de plata | 144 | 144 | 144 | 763 |

El fallo no es «una palabra desconocida»: `anillo & plata & regalar` da 0 porque sólo 7 documentos mencionan `regalo` y ninguno es un anillo de plata.

**3. OR con ordenación por coordinación domina al AND.** Conjunto = OR de los grupos; orden = `(nº de grupos que casan) DESC, ts_rank DESC`. Verificado: (a) los documentos que casan **todos** los grupos tienen coordinación máxima, luego el conjunto del AND queda literalmente en cabeza; (b) un grupo que no casa nada suma 0 a **todos** los documentos, luego el *zero-drop* es un no-op y su maquinaria sobra; (c) rescata el término discriminante — con `ts_rank` solo, `anillo de filigrana tradicional menorquina` pone anillos genéricos en las seis primeras posiciones y los *Anillo de Filigrana* en 7.ª y 8.ª; **con coordinación suben a 1.ª y 2.ª**.

**4. `@>` sobre materiales es un precipicio de recall.**

| par | `&&` (alguno) | `@>` (todos) |
|---|---:|---:|
| plata, oro | 913 | **60** |
| plata, baño de oro | 658 | **14** |
| oro, baño de oro | 376 | **1** |

Cardinalidad de `materials`: **0 → 126 documentos (10,8 %)**, 1 → 951, 2 → 90, 3 → 1. El 91,6 % tiene un material o ninguno, así que `@>` sólo puede alcanzar a los 91 con dos o más. Y los 126 sin materiales —36 anillos, 19 broches, 18 pulseras, 17 collares, 14 pendientes, 11 colgantes— desaparecerían de toda consulta de material bajo un `&&` duro.

**5. La paridad de peso entre ramas es la peor de las fusiones.** Rúbrica idéntica a la que usó C20 (aciertos en top-10 con `piece_type` y material correctos), 12 consultas:

| configuración | /120 |
|---|---:|
| Sólo vectorial (producción hoy) | **67** |
| Fusión, peso vectorial **1,0** | **96** |
| Fusión, peso vectorial 0,5 | 102 |
| **Fusión, peso vectorial 0,33** | **105** |
| Sólo léxico (A+B) | 107 |

Barrido de 36 configuraciones: el **peso vectorial es la palanca dominante** (67-77 con 1,0; 104-106 con 0,33); `k` entre 20 y 60 mueve ≤2 puntos; la profundidad vectorial entre 10 y 60, ≤4. Causa estructural: la rama vectorial **no abstiene**, así que bajo RRF vota siempre y con la misma fuerza. Casos extremos: `dije de plata` cae de 10 (léxico) a **2** con peso 1,0; `gargantilla dorada` de 10 a **5**.

**6. El realce de exacto no compra nada, y los constructores de `tsquery` no son intercambiables.**

| consulta | lista A | lista B | lista C |
|---|---|---|---|
| `anillo Ses Salines plata` | los 4, `ts_rank` 0,99 / 0,99 / 0,96 / 0,95 | los mismos 4, coordinación 4 | — |
| `pulsera Cala Galdana` | las 2, 0,92 / 0,70 | las mismas 2, coordinación 3 | — |
| **`SKU690`** | **1 documento** | **1 documento**, el mismo | **0 documentos** |

| forma emitida | `plainto` | `phraseto` |
|---|---:|---:|
| `baño de oro` | 38 | 38 |
| `acero inoxidable` | 1 | 1 |
| **`aro de dedo`** | **6** | **0** |

`phraseto_tsquery` aniquila `aro de dedo`, la entrada del overlay a la que el informe de C20 atribuye **+262 documentos**.

**7. El umbral de distancia no corta: la profundidad es el corte.** Documentos que pasan `distancia <= 0,65`, sin tope:

| consulta | `d_min` | mediana | pasan 0,65 | umbral que dejaría 60 |
|---|---:|---:|---:|---:|
| `sortija de plata` | 0,387 | 0,521 | **1.168 / 1.168** | 0,447 |
| `gargantilla dorada` | 0,366 | 0,508 | **1.168** | 0,445 |
| `collar elegante para una boda` | 0,396 | 0,596 | **1.090** | 0,493 |
| `bano de oro` | 0,508 | 0,693 | 268 | 0,594 |
| `xyzzy quimbombo alfanumerico` (control) | 0,700 | 0,840 | **0** | 0,778 |

El umbral está **por encima de la mediana**. Matiza lo que C20 dejó escrito: el vector **sí** abstiene, pero **sólo ante texto sin sentido**; entre consultas plausibles no discrimina. Un umbral que cortara tendría que ser un **cuantil por consulta**, que es lo que la ficha de C25 pide y **C21 no toca**.

**8. La asimetría de profundidad costaba 6-8 puntos de 120.** Separando peso y profundidad:

| profundidad A/B | profundidad C | `wC=1,0` | `wC=0,5` | `wC=0,33` |
|---:|---:|---:|---:|---:|
| 200 | 60 | 96 | 102 | **105** |
| 200 | 200 | 96 | 106 | 107 |
| 400 | 400 | 95 | 106 | 108 |

Barrido fino con profundidad **simétrica** y `wC = 0,33`: 20 → 108 · 30 → 109 · **40 → 113** · **50 → 113** · **60 → 111** · 80 → 109 · 100 → 107 · 200 → 107. Meseta en **40-60**, decaimiento monótono a partir de 100. **`k` y la profundidad no son independientes**: con `k=60` el documento de la posición 200 conserva el **38 %** del voto del primero, así que una lista larga reparte voto positivo entre 140 documentos que la otra rama ni siquiera puntúa y desplaza a los que dos ramas colocan bien sin colocar primero. Regla adoptada: **`profundidad ≈ k`**.

**9. Los campos subjetivos están cubiertos al 11-19 %, y la coordinación los convertía en dictadores.** Bajo ordenación por coordinación, casar un grupo más adelanta por delante de **todos** los que casan menos. Con `Ocasiones:` en 150/1.168 y `boda` casando **5** documentos, cinco piezas etiquetadas adelantarían a 1.163 igual de válidas. Restringiendo la coordinación a los campos de cobertura alta y a los términos no resueltos:

| variante (profundidad 60, `wC=0,33`) | total /120 |
|---|---:|
| coordinación sobre **todos** los grupos | 111 |
| **sin `occasion_tags` ni `style_tags`** | **113** |
| **sin `occasion_tags`, `style_tags` ni `color_tags`** | **114** |

Ganancias en `collar elegante para una boda` (9 → 10), `pulsera de plata con motivos marinos` (9 → 10) y `pendientes de oro con piedra azul` (8 → 9), **sin una sola pérdida** en las doce.

### Estado actual del código y de la BD (verificado 2026-09-02 en repo)

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-hybrid-search-rrf` | **Scaffold** (`.openspec.yaml`, esquema `spec-driven`, **0/4**). `proposal` / `design` / `specs` / `tasks` pendientes; este ticket + HU |
| Rama git | `c21-add-hybrid-search-rrf`, creada sobre `ai-eng` al día (`839c97e`) |
| `retrieval/search.py` | `compile_search_sql` monta `<=>` + filtros del body. **Ni una referencia a `tsv`, `ts_rank`, `plainto_tsquery` ni `websearch_to_tsquery`** |
| `retrieval/ports.py` | `ProductSearchPort` con `count_compatible` y `search`. **No hay método léxico** |
| `retrieval/orchestrator.py` | `retrieve_products(payload, principal, *, settings, embed, search, expand_synonyms=None)`. Ya llama a `expand_query` y emite `stage=expand` con `consumed=False`. `match_reasons=["vector"]` **literal**; `VECTOR_UNTIL_C21_NOTE = "vector_only_until_c21"`; `score = clamp(1 − distancia)` |
| `retrieval/synonyms.py` | C20, completo: `expand_query` pura devolviendo `ExpandedQuery(original, groups, matched)`; `lru_cache` del diccionario |
| `retrieval/measure.py` | C20. **`compose_tsquery` ya existe**: `plainto_tsquery` por forma, `||` dentro del grupo, `&&` entre grupos, términos como parámetros. C21 hereda la forma segura y **cambia `&&` por `||` más coordinación** |
| `api/routers/retrieval.py` | `_resolve_embed` construye `LiteLlmEmbeddingClient` **por petición** (`build_retrieval_embed_client`) salvo inyección en `app.state.retrieval_embed` |
| `api/main.py` | `create_app` no crea ningún cliente de embeddings. Punto donde entra el singleton |
| `indexing/embeddings.py` | **Congelado desde C11.** `InMemoryEmbeddingCache` es un `dict` **sin cota y sin TTL**; `LiteLlmEmbeddingClient` recibe `cache` por constructor (`field(default_factory=...)`) — la costura por la que se inyecta un caché acotado sin tocar el fichero |
| `config/settings.py` | `jpv_retrieval_distance_threshold` (0.65), `jpv_query_expansion_enabled` (true), `jpv_family_*`. **Sin pesos, sin `k`, sin profundidades.** `canonical_openapi_settings` pinnea todos los campos |
| `api/schemas/retrieval.py` | `RetrievalMode {hybrid, vector, lexical}`, `RetrievalResult.match_reasons: list[str]`, `DebugInfo{vector_score, lexical_score, rerank_score, notes}`. **Todo lo que C21 necesita ya cabe** |
| `ai.product_document` | 1.168 filas activas con embedding 1536-d. `tsv` generada + GIN `ix_product_document_tsv`; `materials` + GIN; HNSW `vector_cosine_ops` (m=16, ef_construction=128); B-tree en `family_id`, `piece_type`, `price_band`, `data_origin`. **`price` poblado en las 1.168**: min 2,50 €, mediana 230 €, máx 4.175 €; **228 por debajo de 80 €** |
| `size_label` | **529 de 1.168 (45 %)**: S 122 · M 103 · L 87 · XL 83 · `pequeno` 71 · mini 21 · grande 14 · XS 10 · mediano 6 · y 42/9/10 sueltas. **`numero` casa 0 documentos** |
| Extensiones de Postgres | Instaladas: `plpgsql`, `vector`. Disponibles y **no** instaladas: `unaccent`, `pg_trgm`, `fuzzystrmatch` |
| `AssistedSearchService.cs` | Envía `Mode = AiRetrievalMode.Hybrid` y `TopK = 20`. **`MatchReasons` ya se propaga** al DTO (líneas 373 y 402) y `ProductSearchEventService` lo persiste. **.NET no necesita cambios** |
| `assisted-search-result-row.tsx` | `ORIGIN_LABELS` ya contiene `lexical: 'Búsqueda por texto'`, con comentario que anticipa C21 por escrito. Hoy la insignia se decide con el **`aiAvailable` global**, no por resultado |
| `ai-search.types.ts` | `matchReasons: string[]` ya existe en el tipo, documentado como *«la constante `["vector"]` hasta C21»* |
| `appsettings.json` / `AiGatewayOptions` | `RetrievalTimeoutMs = 2500` (temporal de C16). **C21 no lo revierte** |
| `openapi.json` | Contrato congelado. Este change **no** lo regenera |
| Alembic | Head `b8e3c1a4d7f0`. C21 **no** añade revisión |
| `ai.query_log` | **No existe** en ninguna migración. Fuera de alcance |
| `openspec/specs/` | 44 capabilities vivas. `vector-retrieval` y `query-expansion` son las que C21 modifica |

**Impacto en producto:** es el primer change de la cadena C14-C20 que el operador nota. Medido, `sortija de plata` pasa de 4/10 a 10/10 y `criollas de oro` de 1/10 a 6/10.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/retrieval/fusion.py` *(nuevo)* | Fusión RRF pura con pesos por lista y procedencia por candidato |
| `ai-service/src/jbg_ai/retrieval/lexical.py` *(nuevo)* | Composición segura de la `tsquery` a partir de los grupos de C20 y SQL de la rama léxica |
| `ai-service/src/jbg_ai/retrieval/filters.py` *(nuevo)* | Extracción por reglas (techo de precio, talla, materiales) y ordenación por bloques que degrada |
| `ai-service/src/jbg_ai/retrieval/ports.py` | Método léxico en `ProductSearchPort` y tipo de resultado con `ts_rank` y coordinación |
| `ai-service/src/jbg_ai/retrieval/search.py` | Implementación SQL de la rama léxica sobre `tsv` |
| `ai-service/src/jbg_ai/retrieval/orchestrator.py` | Consume la expansión, orquesta las tres ramas, funde, degrada, calcula `match_reasons` y `low_confidence`, emite `stage=lexical` / `stage=filters` / `stage=fuse`, retira `vector_only_until_c21` |
| `ai-service/src/jbg_ai/retrieval/measure.py` | Ampliada: comparación de configuraciones e informe versionado que C24 reutiliza |
| `ai-service/src/jbg_ai/api/main.py` | Singleton del cliente de embeddings de recuperación con caché **acotado** inyectado |
| `ai-service/src/jbg_ai/api/routers/retrieval.py` | Resuelve el cliente desde `app.state` en vez de construirlo por petición; pasa los defaults de fusión |
| `ai-service/src/jbg_ai/config/settings.py` | Pesos, `k`, profundidades por rama; pin en `canonical_openapi_settings` |
| `ai-service/tests/retrieval/` | Fusión, rama léxica, extracción de filtros, degradación, modos, consenso, singleton |
| `ai-service/evals/results/` | Informe versionado de la línea base híbrida |
| `ai-service/README.md` | Filas nuevas en la tabla de entorno y párrafo de C21 |
| `frontend/src/components/sales/assisted-search-result-row.tsx` | Insignia de origen **por resultado**, leída de `matchReasons` |
| `frontend/src/pages/sales/__tests__/` | Test de la insignia por resultado |
| `openspec/changes/add-hybrid-search-rrf/` | `proposal`, **`design.md`**, `specs` (`vector-retrieval` MODIFIED + `hybrid-fusion` nueva), `tasks` |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-021 (**en el apply**) |
| `openspec/DEFERRED_TASKS.md` | Marcar pagado el singleton; dejar viva la reversión de los 2500 ms |
| `backend/`, EF Core, `openapi.json`, Alembic, `terraform/` | **Sin cambios** |

---

## Especificaciones Técnicas

### ai-service — las tres listas

```
consulta del operador
   │
   ├─ A ─ websearch_to_tsquery('spanish', texto tecleado)
   │        ORDER BY ts_rank DESC              LIMIT profundidad_lexica (200)
   │
   ├─ B ─ grupos de C20 → plainto_tsquery por forma, `||` dentro del grupo,
   │        `||` ENTRE grupos (no `&&`)
   │        ORDER BY (Σ (tsv @@ grupo_i)::int  sólo sobre los grupos QUE CUENTAN) DESC,
   │                  └──────────── coordinación ────────────┘        ts_rank DESC
   │                                                     LIMIT profundidad (60)
   │
   └─ C ─ embedding <=> q  ≤ umbral 0,65   ← medido: no filtra, deja pasar el corpus
            ORDER BY distancia ASC              LIMIT profundidad (60)  ← el corte real
```

**Las tres profundidades son la misma.** No es una simplificación: la asimetría 200/60 de la primera versión cuesta **6-8 puntos de 120** (medición 8). Con `k = 60`, el documento de la posición 200 conserva el 38 % del voto del primero, así que una lista larga no amplifica su cabeza pero reparte voto positivo entre 140 documentos que la otra rama ni siquiera puntúa. **`k` y la profundidad se eligen juntos: `profundidad ≈ k`.** Se toma 60 y no 50 —2 puntos, dentro del ruido de doce consultas— porque coincide con `OVER_RETRIEVAL_CAP`, que ya existe: **un número arbitrario menos**. Sigue siendo un parámetro **conceptualmente distinto** del overfetch de salida, que depende de `top_k`.

**Composición segura.** Se hereda de `measure.py`: cada forma emitida entra como **parámetro** de un `plainto_tsquery`; nunca se concatena sintaxis de consulta. El único cambio es el operador entre grupos, de `&&` a `||`, más la expresión de coordinación en el `SELECT` y en el `ORDER BY`.

**Por qué `plainto` y no `phraseto` para las formas emitidas:** medido, `phraseto` deja `aro de dedo` en 0 documentos frente a 6. No hay regla de «cuándo es multi-palabra» que escribir: `plainto` siempre.

**Por qué `websearch` para la lista A:** regala `"comillas"` y `-negación` sin coste, y un error de sintaxis del operador **no puede vaciar el resultado**, porque la lista B no interpreta sintaxis alguna.

### ai-service — fusión

```python
rrf(listas, pesos, k) :  score(d) = Σ_i  w_i / (k + rank_i(d))
```

Función **pura**, sin conocimiento del dominio, que recibe listas de identificadores y devuelve el orden fundido **más la procedencia por candidato** (en qué listas apareció y en qué posición). Defaults:

| parámetro | default | motivo |
|---|---:|---|
| peso lista A (tecleada) | `0,5` | Con A y B a 0,5 cada una, la rama léxica pesa 1,0 en total, y la degradación es exacta: si la expansión está apagada, A ≡ B y `0,5/(k+r) + 0,5/(k+r) = 1/(k+r)` |
| peso lista B (expandida) | `0,5` | ídem |
| **peso lista C (vectorial)** | **`0,33`** | **Medido**: 105/120 frente a 96/120 con 1,0. La rama vectorial no abstiene, así que vota siempre; darle voto pleno la deja mandar cuando no entiende |
| `k` | `60` | El valor de la literatura. Medido, `k` entre 20 y 60 mueve ≤2 puntos sobre 120: se conserva para no tener que defender un número propio |
| **profundidad, las tres listas** | **`60`** | **Simétrica.** La asimetría 200/60 cuesta 6-8 puntos (105 frente a 111). Meseta medida en 40-60, decaimiento monótono a partir de 100. Acoplada a `k`; coincide con `OVER_RETRIEVAL_CAP` para no introducir otra constante |

Todo en `Settings` **y** como parámetro de la llamada de orquestación, el mismo asiento que C20 fijó para su flag: C24 barre configuraciones en un proceso, sin reiniciar y sin mover `openapi.json`.

> **Nota de rigor frente a S10.** El apunte desaconseja **ponderar puntuaciones brutas**, cuya distribución cambia por consulta. Ponderar **recíprocos de rango** es adimensional y estable: el peso no calibra escalas, declara cuántos votos tiene cada rama. Es una diferencia que hay que dejar escrita, porque superficialmente se parece a lo rechazado.

### ai-service — qué grupos cuentan para la coordinación

**Regla:** un grupo cuenta **si y sólo si la ausencia de su término es evidencia de no-relevancia.**

| clase de grupo | cobertura del campo en el corpus | ¿cuenta? |
|---|---:|---|
| resolvió a `piece_type` | 99 % | **sí** — un documento sin `anillo` no es un anillo |
| resolvió a `materials` | 89 % | **sí** |
| **no resolvió** (palabra literal del operador) | — | **sí** — es el caso Stripe, y el que subió los *Anillo de Filigrana* de la 7.ª a la 1.ª posición |
| resolvió a `color_tags` | 19 % | **no** |
| resolvió a `occasion_tags` | 13 % | **no** |
| resolvió a `style_tags` | 11 % | **no** |
| resolvió a `size_label` | 45 % | **no** — ya es propiedad del filtro que degrada. Un campo, un mecanismo |
| resolvió a `stone_type` | 54 % | **sí**, en la frontera. Se anota para que C24 lo revise: ninguna de las doce consultas lo aísla |

Un grupo que no cuenta **sigue puntuando en `ts_rank`**; lo que pierde es el derecho a saltarse la cola. La clasificación no requiere código nuevo de análisis: `ExpandedQuery.matched` de C20 ya entrega `(término → campo → canónico)`.

**Por qué importa, con números.** `Ocasiones:` existe en 150 de 1.168 documentos y `boda` casa **5** en todo el catálogo. Bajo coordinación, casar un grupo más adelanta por delante de **todos** los que casan menos: sin esta regla, cinco piezas etiquetadas adelantarían a 1.163 igual de válidas para una boda pero sin etiquetar. La coincidencia léxica sobre un campo escaso fabrica **precisión falsa**.

**La propiedad emergente, que es el verdadero premio.** Cuando la consulta es mayoritariamente subjetiva —*«algo elegante para una ceremonia»*— quedan pocos grupos que cuenten o ninguno, la coordinación deja de discriminar, la lista léxica degenera a `ts_rank` sobre un OR ancho —señal débil— y **la rama vectorial decide por defecto**. Es la *ponderación dinámica* que S10 describe, obtenida **sin el número mágico** que el mismo apunte advierte que alguien tendrá que justificar, recalibrar y depurar. Una ponderación adaptativa explícita queda como configuración `v3-adaptativa` de la ablación de C24, no como alcance de C21.

> **Honestidad sobre esta medición.** La rúbrica puntúa «es un collar», no «sirve para una boda»: estructuralmente **no puede** juzgar lo que esta regla pretende arreglar. La ganancia de 111 → 113/114 mide recuperación de tipo de pieza. El juez real es una **categoría subjetiva en el golden set de C24**, que hoy no existe y que este ticket pide crear.

### ai-service — filtros estructurales

Regla de una frase: **lo que un humano pulsó, filtra; lo que una regla dedujo del texto, degrada.**

| origen | señal | tratamiento |
|---|---|---|
| Body (`filters.materials`, `filters.category`, `filters.family_id`, `filters.exclude_product_ids`) | los pulsó el operador en el panel | **Filtro duro en SQL, sin cambios.** `&&` para materiales, igualdad para categoría y familia |
| Texto: techo de precio (`menos de 80`) | regla | **Degrada.** 228 de 1.168 documentos cumplen un techo de 80 € |
| Texto: talla (`talla M`) | regla | **Degrada.** `size_label` cubre el 45 % del corpus |
| Texto: materiales del vocabulario | ya resueltos en `ExpandedQuery.matched` | **Degrada.** Nunca `@>`; nunca un `&&` duro que borraría 126 documentos sin materiales |
| Texto: `piece_type` | — | **No se filtra en absoluto.** La rama léxica ya lo expresa exactamente (`anillo` 268 = 268); añadir un `WHERE` sólo constreñiría la rama vectorial, que es la que rescata la paráfrasis |

**Cómo degrada, sin un solo número mágico:**

```
tras la fusión, ordenación estable por bloques:
   ( supera_techo_precio , no_casa_talla , no_casa_material_deducido , −rrf_score )
     └──────────── booleanos ────────────┘                             └ orden RRF ┘
```

El candidato que incumple baja detrás de los que cumplen, **conserva su orden RRF dentro de su bloque** y **nunca sale de la ventana de overfetch**: .NET, que es la autoridad sobre el precio real, lo sigue viendo. Cuando llegue **C25** con pesos calibrados contra el golden set, esta ordenación es la costura donde se sustituye por un *score*, sin deshacer nada.

**`ExpandedQuery.matched` es la tabla de consulta**, con su `(término tecleado → campo del vocabulario → canónico)`. C20 lo entregó exactamente para esto: construir una segunda sería el error de C19 a menor escala.

### ai-service — orquestación, modos y degradación

```
count_compatible()                              ← 503 si el índice es incompatible
   │
   ├── asyncio.gather(  embed(texto ORIGINAL)  ,  léxico(A y B)  )
   │        170–1707 ms                            < 10 ms
   │        ↑ la rama léxica se esconde entera detrás del proveedor
   │        ↑ una sola conexión del pool de 5 sin overflow, en todo momento
   │
   ├── búsqueda vectorial (sólo si el embed devolvió vector)
   ├── RRF(A, B, C)  →  filtros que degradan  →  overfetch de salida
   └── 200
```

| `mode` | comportamiento |
|---|---|
| `hybrid` (lo que envía .NET) | Las tres listas. Si el proveedor falla y **hay** léxico → 200 con `match_reasons: ["lexical"]`. Si falla y **no** hay léxico → **503** |
| `lexical` | **No se llama al proveedor.** Sólo A y B |
| `vector` | No se consulta `tsv`. Sólo C, como C14 |

La nota `vector_only_until_c21` **desaparece**.

**Por qué la léxica va contra el embedding y no contra la vectorial:** paralelizar rama contra rama —lo que sugiere el apunte de S10— haría que cada petición retuviera 2 de las 5 conexiones del *pool*, que no tiene *overflow* y espera 2 s. Y optimizaría lo que no cuesta: sobre 1.168 filas con GIN, la rama léxica es ruido frente al proveedor.

**Por qué 503 cuando tampoco hay léxico:** un 200 vacío sería indistinguible de una abstención legítima, y el panel de C16 pinta el estado *«abstenido»* con `results.length === 0 && aiAvailable && lowConfidence`. Servir un fallo de dependencia con la pantalla de «no hemos encontrado nada» es la mentira que la decisión 11 existe para evitar.

### ai-service — respuesta

| campo | antes | después |
|---|---|---|
| `match_reasons` | constante `["vector"]` | procedencia real: `["vector"]`, `["lexical"]` o `["vector","lexical"]` |
| `score` | `clamp(1 − distancia)` | **puntuación RRF normalizada al primer resultado**; sigue en `[0,1]` y monótona con el orden |
| `debug.vector_score` | igual a `score` | la distancia mapeada, **sólo si** la rama vectorial vio el candidato; `null` si no |
| `debug.lexical_score` | siempre `null` | `ts_rank` de la lista en que apareció |
| `debug.notes` | `vector_only_until_c21` en hybrid/lexical | procedencia y rango por rama, filtros extraídos (`filter:price_max=80`), y `vector_branch_unavailable` cuando aplique |
| `low_confidence` | `len(results) == 0` | `len(results) == 0` **o** ningún candidato aparece en más de una rama |

> **`score` cambia de significado y la telemetría de C04 lo persiste.** Hay que declararlo en el README y en la spec: comparar puntuaciones de antes y después de C21 no significa nada.

### ai-service — singleton del cliente de embeddings

`DEFERRED_TASKS.md` describe la deuda como *«roughly three lines in `main.py`»*. **No lo es**, y el motivo es la razón de que se pague aquí y no en un change trivial:

- `InMemoryEmbeddingCache` es un `dict` **sin cota y sin TTL**. Por petición es inofensivo: nace vacío y muere con la respuesta. Como singleton de proceso es una caché de por vida con una entrada por consulta distinta (~13 KB por vector) en un contenedor **capado a 512 MiB que ya usa 232**.
- `indexing/embeddings.py` está **congelado por C11**. La salida limpia existe y no lo toca: `LiteLlmEmbeddingClient` recibe `cache` por constructor, así que se define un caché **acotado (LRU)** en `retrieval/` y se inyecta al construir el singleton en `main.py`.

**`AiGateway:RetrievalTimeoutMs` sigue en 2500 ms.** Revertirlo a 800 exige desplegar a la demo, re-medir en frío y en caliente y confirmar `Origin=Assisted` en el embudo: change propio, y la entrada de `DEFERRED_TASKS.md` se queda viva con las cifras nuevas como línea base.

### frontend — insignia de origen por resultado

Hoy: `originLabel(aiAvailable ? 'assisted' : 'lexical')` — decisión **global** de la respuesta.
Después: la decisión es **por resultado**, a partir de `result.matchReasons`. Un resultado sin `vector` en su procedencia muestra «Búsqueda por texto».

Es exactamente lo que C16 dejó preparado por escrito en el comentario de `ORIGIN_LABELS`, y **no toca .NET ni el contrato**: `matchReasons` ya viaja desde `AssistedSearchService` hasta `ai-search.types.ts`.

### Contrato OpenAPI

**No se regenera.** `test_openapi_snapshot_is_stable` debe seguir verde. Todo lo nuevo cabe en campos que existen desde C02: `match_reasons` (lista de cadenas), `debug.lexical_score`, `debug.notes`. Los parámetros de fusión viven en `Settings` y en la firma del orquestador, nunca en `RetrievalRequest`.

### Tests

**ai-service (`uv run pytest`, sin sockets):**

| Test | Qué fija |
|---|---|
| `test_exact_sku_query_ranks_target_first` | **De la ficha.** Cambia de naturaleza: verifica una **propiedad emergente**, no un mecanismo. Si deja de cumplirse, ahí se discute el anclaje |
| `test_rrf_fuses_ranked_lists_preserving_top_hit` | **De la ficha.** Fusión pura sobre listas de prueba |
| `test_material_filter_uses_overlap_by_default` | **De la ficha**, reinterpretado: el material del **body** usa `&&`; el deducido del texto no filtra |
| `test_multi_material_query_uses_contains_all` | **De la ficha**, invertido con medición: `@>` **no** se aplica por defecto. El test fija la exclusión y cita las cifras 913 / 60 |
| `test_extracts_price_ceiling_from_natural_phrase` | **De la ficha.** `menos de 80` → techo 80 |
| `test_never_invents_filter_absent_from_query` | **De la ficha.** Ningún filtro que la consulta no pidió |
| `test_lexical_branch_ors_groups_and_ranks_by_coordination` | Un documento que casa más grupos precede a uno que casa menos |
| `test_group_matching_nothing_does_not_change_order` | El *zero-drop* es innecesario |
| `test_vector_branch_weight_defaults_below_lexical` | El default medido no se pierde en un refactor |
| `test_fusion_weights_and_k_load_from_settings_not_hardcoded` | Barrido de C24 posible |
| `test_branch_depth_is_symmetric_across_lists` | Fija la medición 8: las tres listas se truncan al mismo punto |
| `test_branch_depth_is_independent_of_overfetch` | Dos parámetros distintos aunque compartan valor por defecto |
| `test_sparse_vocabulary_fields_do_not_count_towards_coordination` | Fija la medición 9: ocasión, estilo, color y talla no deciden el orden |
| `test_unresolved_term_counts_towards_coordination` | La otra mitad de la regla: la palabra literal sí manda (el caso `filigrana`) |
| `test_subjective_query_leaves_ordering_to_the_vector_branch` | La adaptación emergente, sin peso adaptativo |
| `test_structural_filter_demotes_but_never_removes` | El candidato caro sigue en la ventana |
| `test_body_filters_remain_hard` | La regla de una frase |
| `test_lexical_mode_makes_no_provider_call` | `mode=lexical` honesto |
| `test_embedding_failure_in_hybrid_degrades_to_lexical` | 200 con `["lexical"]` |
| `test_embedding_failure_with_no_lexical_hits_is_503` | No hay 200 vacío disfrazado de abstención |
| `test_match_reasons_report_real_provenance` | Se acabó la constante |
| `test_low_confidence_signals_absence_of_cross_branch_consensus` | La señal de C24 |
| `test_lexical_query_runs_concurrently_with_embedding` | Una sola conexión a la vez |
| `test_retrieval_embed_client_is_a_process_singleton` | La deuda pagada |
| `test_embedding_cache_is_bounded` | La fuga que la deuda no anticipaba |
| `test_embeddings_module_is_unchanged` | Fijación del congelado de C11 |
| `test_openapi_snapshot_is_stable` | Existente, debe seguir verde |
| `test_surface_forms_use_plainto_not_phraseto` | Fija la medición 6 |

**frontend (Vitest + RTL):** `should show the lexical origin badge when a result has no vector provenance`, `should show the assisted badge when the result came from both branches`.

**No aplica:** xUnit (no se toca `backend/`), Playwright, migración, regenerar OpenAPI.

---

## Arquitectura

**Decisiones previas que gobiernan y no se reabren:**

- **§6.2 del diseño** — *«Python calcula parecidos y redacta; .NET calcula números y decide»*. Es el motivo por el que el techo de precio **degrada** en Python en vez de excluir: el número lo decide .NET.
- **§7.6 del diseño** — sobre-recuperación y prefiltro blando: *«un producto válido no puede desaparecer»*. C21 lo extiende del stock al precio y a la talla.
- **§6.4 del diseño** — el circuito abierto y el buscador léxico de .NET siguen siendo la degradación de último recurso. La degradación a léxico **dentro** de jbg-ai es un escalón **anterior**, no un sustituto, y por eso la respuesta lo declara por resultado en lugar de disimularlo.
- **C11** — `indexing/embeddings.py` congelado. El caché acotado se **inyecta**, no se edita.
- **C02** — `openapi.json` es contrato acordado con el lado .NET. No se mueve.
- **C19** — no se duplica una definición. `ExpandedQuery.matched` es la tabla de consulta de los filtros; no se construye una segunda.
- **C20** — el flag vive en `Settings` **y** en la firma del orquestador. C21 añade sus parámetros al mismo asiento.

**Reparto de specs:**

| Spec | Operación |
|---|---|
| `vector-retrieval` | **MODIFIED.** Cae *«Hybrid and lexical modes run the vector branch until C21»*; se modifica *«Over-retrieval applies after the distance filter»* (profundidad por rama ≠ overfetch), *«Results are ordered by ascending distance»* (`score` pasa a ser RRF normalizado), *«Provider failure is not an empty success»* (degradación a léxico), *«The search MUST NOT filter by price or stock»* → **MUST NOT *exclude*** y *«Stage logs»* (etapas nuevas) |
| `query-expansion` | **MODIFIED.** Caen *«the expansion result MUST NOT alter the retrieval response»* y *«is not consumed until the lexical branch exists»* |
| **`hybrid-fusion`** | **ADDED.** Fusión por rango con pesos configurables; función pura sin conocimiento del dominio; procedencia por candidato; ausencia de consenso como señal; filtros estructurales por reglas que degradan y nunca excluyen; composición de la consulta léxica con términos siempre parametrizados |
| `ai-service-runtime` | **MODIFIED** si los parámetros de fusión entran en spec de configuración |
| `assisted-search-panel` | **MODIFIED.** La insignia de origen pasa de global a por resultado |

**Por qué `hybrid-fusion` es capacidad y no detalle del endpoint:** C23 (corpus de conocimiento), C25 (señales de negocio) y C26 (sustitutos) van a fundir listas **sin pasar por `POST /v1/retrieval/products`**. Si la fusión vive dentro de la spec del endpoint, esos tres changes tendrían que citar una spec que habla de otro endpoint, o reescribir el comportamiento. Coste real y acotado: una capability viva más de 44, y `openspec validate --all --strict` tiene que seguir en `0 failed` tras el sync.

**Breaking changes:** ninguno de contrato. Dos de **comportamiento**, ambos declarados: `score` cambia de escala, y `match_reasons` deja de ser constante — que es precisamente lo que C16 documentó como pendiente.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec completos: `proposal`, **`design.md`**, `specs` (`vector-retrieval` + `query-expansion` MODIFIED, `hybrid-fusion` ADDED) y `tasks`
- [ ] `openspec validate --all --strict` en **`0 failed`**
- [ ] `uv run pytest` verde, **sin sockets** a proveedor, LLM ni RDS
- [ ] `test_openapi_snapshot_is_stable` verde y `ai-service/openapi.json` **sin diff**
- [ ] `indexing/embeddings.py` y `enrichment/vocabularies.yaml` **sin diff**
- [ ] `backend/` **sin diff**; sin revisión de Alembic; sin migración de EF Core
- [ ] `npm run build` verde en `frontend/`; suite de frontend comparada **por nombres de test** contra la línea base roja documentada, nunca por recuento
- [ ] Pesos, `k` y profundidades leídos de `Settings`, pinneados en `canonical_openapi_settings` y documentados en la tabla de entorno del README
- [ ] `stage=lexical`, `stage=filters` y `stage=fuse` con `trace_id`; la consulta del operador sólo en Debug
- [ ] `DEFERRED_TASKS.md` actualizado: singleton **pagado**, reversión de los 2500 ms **viva** con cifras nuevas
- [ ] HU-AIENG-021 enlazada en `Documentos/epicas.md` (EP14)
- [ ] Sin TODO/FIXME sin tarea de seguimiento
- [ ] Verificación **posterior** (no merge): la CLI reproduce `sortija de plata` 4/10 → 10/10 y `criollas de oro` 1/10 → 6/10 contra el índice local, y deja medida la latencia del pipeline completo en frío y en caliente

No aplica: xUnit, Playwright, migración, regenerar OpenAPI, `terraform/`.

---

## Requisitos No Funcionales

- **Seguridad:** los términos de la consulta viajan **siempre como parámetros**; nunca se concatena sintaxis de `tsquery`. El `pos_id` sigue viniendo del token y el body se sigue ignorando. La consulta del operador sólo en Debug. Ninguna credencial nueva.
- **Rendimiento y free-tier:** la rama léxica corre **en paralelo con la llamada al proveedor**, así que su latencia queda escondida tras los 170-1707 ms del embed; sobre 1.168 filas con GIN es ruido. **Una sola conexión del *pool* de 5 sin *overflow*** en todo momento. La fusión es aritmética sobre ≤ 460 identificadores. El singleton convierte la caché de embeddings en útil por primera vez —hoy no tiene **ni un acierto** en recuperación— y su cota impide que un contenedor de 512 MiB se llene con una entrada por consulta.
- **Observabilidad:** `stage=lexical` (candidatos, `ts_rank` máximo, latencia), `stage=filters` (qué se extrajo, cuántos se degradan), `stage=fuse` (tamaño de cada lista, solape entre ramas, consenso), todos con `trace_id`. Recuentos, nunca vectores ni el diccionario. El embudo de .NET conserva `LowConfidence`, que ahora significa desacuerdo entre ramas.
- **Integridad:** ningún documento se reescribe ni se reindexa; `doc_text`, `tsv` y `source_hash` son idénticos antes y después. Python no lee el esquema `public`. **La fusión es determinista**: mismos parámetros y mismas listas producen siempre el mismo orden, con desempate estable — requisito de `test_run_is_reproducible_for_same_config_and_seed` de C24. .NET sigue siendo la autoridad sobre precio, stock y permisos.

---

## Preguntas Abiertas

Las dieciséis decisiones de diseño quedaron cerradas en la exploración del 2026-09-02 y están en la tabla de la HU. Queda esto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿`hybrid-fusion` como capability nueva, o todo dentro de un delta de `vector-retrieval`? | **Capability nueva**, más los deltas MODIFIED. C23, C25 y C26 fundirán listas fuera de este endpoint |
| 2 | Nombres de los settings de fusión | `JPV_RRF_K`, `JPV_RRF_WEIGHT_TYPED`, `JPV_RRF_WEIGHT_EXPANDED`, `JPV_RRF_WEIGHT_VECTOR`, `JPV_BRANCH_DEPTH` (**uno solo**, las tres listas comparten profundidad) — prefijo `JPV_` como el resto |
| 2b | ¿La lista de campos «escasos» es configuración o constante del código? | **Constante en el código, con la cobertura medida en el comentario.** Es una propiedad del corpus, no del despliegue; hacerla configurable invitaría a tocarla sin volver a medir. C24 la revisa con el golden set |
| 2c | ¿Cuenta `stone_type` (54 % de cobertura) para la coordinación? | **Sí**, provisionalmente: está en la frontera entre el bloque alto (89-99 %) y el escaso (11-19 %), y ninguna de las doce consultas lo aísla. Anotado para C24 |
| 3 | ¿`score` como RRF normalizado al primero, o RRF crudo? | **Normalizado al primero.** Mantiene el rango `[0,1]` que el contrato promete; el crudo daría valores de 0,0001-0,03 que la telemetría persistiría sin significado |
| 4 | ¿El retoque de frontend entra en C21 o se difiere? | **Entra.** Sin él la pantalla dice «Coincidencia semántica» sobre resultados servidos sólo por la rama léxica, que es la mentira que la decisión 11 evita. Son ~5 líneas y un test |
| 5 | Un módulo (`hybrid.py`) o tres (`lexical.py`, `fusion.py`, `filters.py`) | **Tres.** `fusion.py` es puro y sin dominio —C23, C25 y C26 lo reutilizan—; `filters.py` es la costura que C25 sustituye; mezclarlos obligaría a esos changes a importar de un módulo que hace tres cosas |
| 6 | ¿Se amplía `measure.py` o se crea una CLI de evaluación nueva? | **Se amplía.** Una CLI nueva de evaluación es C24, y adelantarla duplicaría el sitio donde vive el mismo tipo de informe |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** regenere `openapi.json`, **no** toque `backend/`, **no** edite `indexing/embeddings.py` ni `enrichment/vocabularies.yaml`, **no** abra migración, **no** introduzca un filtro que excluya, y **no** adelante nada de C22, C24 ni C25.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Máxima**. Es el cuello del grafo tras C20: desbloquea **C24**, **C25** y **C30** a la vez. Nunca se recorta (§6 del plan). Y es el primer change de la cadena que el operador nota.
- **Estimación:** **5 SP** *(pendiente de refinamiento)*. Dos consultas SQL nuevas, una función de fusión pura, un extractor por reglas, una costura de reordenación, un singleton con caché acotado y ~5 líneas de frontend. Sin migración y sin contrato, pero con **seis decisiones** que hay que dejar defendidas, de las que **cuatro contradicen** a la ficha o a una recomendación previa de la propia exploración.
- **Dependencias:** C14 y C20 archivados · índice local poblado, sólo para la verificación posterior · **bloquea C24, C25 y C30** · **no paralelizar con C22 ni C25**: misma zona `retrieval/`.
- **Línea de corte** si desborda (regla 5 del plan): (1) rama léxica + fusión + `match_reasons` reales + modos honestos, archivable por sí solo; (2) filtros estructurales que degradan; (3) singleton y caché acotado; (4) `low_confidence` por consenso y ampliación de la CLI de medición.
- **Tags:** `HU-AIENG-021`, `C21`, `EP14`, `ai-service`, `python`, `frontend`, `retrieval`, `hybrid-search`, `rrf`, `full-text-search`, `ts_rank`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-021](../../../../Documentos/Historias/AI-Eng/HU-AIENG-021.md)
- **Change OpenSpec:** `openspec/changes/add-hybrid-search-rrf/` · rama `c21-add-hybrid-search-rrf`
- **Mediciones que gobiernan el diseño:** [c21-hybrid-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md) (2026-09-02) · [c20-query-expansion-reach.md](../../../../ai-service/evals/results/c20-query-expansion-reach.md)
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C21, §0 del 2026-09-01, §4 grafo) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§5, §6.2, §6.4, §7.3, §7.6)
- **Apuntes del Máster (guía, no dogma):** [Búsqueda híbrida](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Busqueda%20hibrida.md) (RRF, `ts_rank`, el problema del término exacto; propone `k=60` sin pesos y paralelizar rama contra rama — aquí se mide y se corrige) · [Filtrado contextual y temporal](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Filtrado%20contextual%20y%20temporal.md) (*«los filtros duros se reservan para metadatos en los que se confía; lo dudoso, como mucho, pondera»*)
- **Specs vivas:** `vector-retrieval` · `query-expansion` · `ai-vector-schema` · `ai-service-runtime` · `assisted-search-panel` · `ai-assisted-search` · `ai-search-telemetry`
- **Precedentes:** C05 (`tsv` generada y GIN, sin consumidor) · C11 (cliente de embeddings congelado, caché sin cota) · C14 (umbral, etapas de log, patrón stub/real) · C15 (hidratación autoritativa, buscador degradado de .NET) · C16 (insignia de origen preparada por escrito para C21) · C20 (grupos de equivalencia, flag en la firma) · C18a/C18b (medir antes de creerse la ficha)
- **Deuda que este change paga a medias:** [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) — singleton **sí**; `RetrievalTimeoutMs` 2500 → 800 ms **no**
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-02 | `/enrich-us` | Creación a partir de HU-AIENG-021 y de la exploración medida del 2026-09-02. Recoge las dieciséis decisiones cerradas, y en particular las cuatro que **contradicen** lo escrito antes: OR con coordinación en vez de AND estricto (7 de 10 consultas reales daban cero) y sin *zero-drop* (rescataba 1); `@>` fuera y materiales que degradan en vez de filtrar (60 de 913; 126 documentos sin materiales); peso vectorial 0,33 en vez de la paridad entre ramas (105/120 frente a 96/120); y **sin realce de SKU ni de nombre exacto**, que la medición demostró redundante |
| 2026-09-02 | revisión | Tres mediciones nuevas al preguntar por el efecto de las profundidades desiguales y por la subjetividad de ocasión y estilo. **Corrige este mismo ticket en dos puntos y desmonta un supuesto de C14:** (a) la **profundidad pasa a ser simétrica en 60** — la asimetría 200/60 costaba 6-8 puntos de 120, porque con `k=60` el documento de la posición 200 conserva el 38 % del voto del primero y la cola larga desplaza al consenso; regla `profundidad ≈ k`; (b) **la coordinación deja de contar los campos escasos** (`occasion_tags` 13 %, `style_tags` 11 %, `color_tags` 19 %, `size_label` 45 %), porque en un campo así la ausencia no es evidencia y cinco piezas etiquetadas `boda` adelantarían a 1.163 — 113/120 y 114/120 frente a 111, sin pérdidas, y con la adaptación al tipo de consulta como propiedad **emergente** en vez de un segundo peso; (c) el **umbral de 0,65 no filtra**: deja pasar 1.168 de 1.168 en consultas ordinarias y sólo abstiene ante texto sin sentido, así que la profundidad vectorial es el corte real y la recalibración por cuantil queda anotada para C25 |
