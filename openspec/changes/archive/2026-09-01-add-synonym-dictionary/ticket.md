# T-AIENG-020: Query-side synonym dictionary for the lexical branch (C20)

> Ticket técnico del change OpenSpec `add-synonym-dictionary`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-020](../../../../Documentos/Historias/AI-Eng/HU-AIENG-020.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C20 reescrita y entrada de §0 del 2026-09-01), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§7.3, §7.4, §7.6), sesión de exploración 2026-09-01 medida contra el Postgres local y el proveedor real, y código de `ai-service/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-020 / C20** — Diccionario de sinónimos de consulta: base `vocabularies.yaml` sin modificar + overlay de consulta con artefactos del stemmer, `expand_query` pura devolviendo grupos de equivalencia, flag en la firma del orquestador, log `stage=expand` e informe de medición versionado

---

## Contexto y Problema

C14 dejó un retriever vectorial vivo. C05 dejó, desde el primer día, una columna `tsv` generada con `to_tsvector('spanish', doc_text)` y su índice GIN — **poblada en 1.168 de 1.168 filas y que hoy no consulta nadie**. C21 la encenderá. C20 fabrica la pieza sin la cual, al encenderla, contestará cero.

La decisión 4 de la revisión sacó `SearchAliases` del perfil de producto: era texto generado por IA, persistido por producto, con deriva. El sustituto acordado en el §7.4 del diseño es un diccionario del dominio aplicado **en expansión de consulta, nunca en indexación**.

**La exploración del 2026-09-01 midió y obligó a reencuadrar la ficha.** Cinco hechos, todos contra el índice real:

1. **`doc_text` ya está canonicalizado.** `build_source_text` escribe `Tipo:` y `Materiales:` con el vocabulario cerrado de C09 — 1.157 y 1.042 de 1.168 documentos —, y buscar léxicamente el canónico **equivale exactamente a filtrar por `piece_type`**: `anillo` 268 = 268, `pendientes` 275 = 275, `pulsera` 207 = 207, `collar` 140 = 140. La dirección útil de la expansión es *palabra del operador → canónico*, que es la que `vocabularies.yaml` ya codifica.

2. **Sin diccionario, la rama léxica contesta cero a frases ordinarias.**

   | consulta | sin expansión | con expansión |
   |---|---|---|
   | `gargantilla dorada` | **0** | 64 |
   | `collares de plata` | **0** | 66 |
   | `criollas de oro` | 1 | 102 |
   | `sortija de plata` | 3 | 144 |
   | `aros de plata` | 22 | 205 |

3. **El stemmer español rompe dos sustantivos del dominio.** No es un problema de sinónimos, es de tokenizador:

   | par | lexemas | documentos |
   |---|---|---|
   | `collar` / `collares` | `'coll'` ≠ `'collar'` | **140 frente a 1** |
   | `aro` / `aros` | `'aro'` ≠ `'aros'` | 32 y 24, conjuntos distintos |
   | `baño` / `bano` | `'bañ'` ≠ `'ban'` | `baño de oro` 38, **`bano de oro` 0** |
   | `pequeño` / `pequeno` | `'pequeñ'` ≠ `'pequen'` | 134 y 71, ambas legítimas |

   El stemmer **sí** pliega tildes agudas (`ámbar`=`ambar`, `ónix`=`onix`, `clásico`=`clasico`) **pero no la `ñ`**.

4. **Una sola `tsquery` ensanchada destruye la coincidencia exacta.** Con `(sortij|anill) & plat` ordenado por `ts_rank`, los tres productos llamados literalmente «Sortija» caen **fuera del top-10**. Fusionando por RRF (k=60) la lista original con la expandida vuelven a **1, 2 y 3**, conservando los 144 candidatos. Es el problema de Stripe del artículo de búsqueda híbrida de S10, reproducido dentro del mecanismo de expansión.

5. **La rama vectorial no cubre el hueco y no abstiene.** Doce embeddings reales de `text-embedding-3-small`, misma búsqueda coseno de C14 con umbral 0,65, aciertos en el top-10 contra la diana (`piece_type` y material correctos): `criollas de oro` **1/10**, `sortija de plata` **4/10**, `gargantilla dorada` **6/10** (solape del top-10 con la forma canónica: **0/10**), `aros de plata` 9/10, `collares de plata` 10/10. Siempre devuelve diez candidatos bajo el umbral, así que el fallo llega a pantalla con apariencia de acierto — la firma que C17 encontró siete veces. El plural sí lo cruza el vector sin ayuda, lo que confirma que el problema del stemmer es estrictamente léxico.

**Estado actual del código y de la BD (verificado 2026-09-01 en repo):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-synonym-dictionary` | **Scaffold** (`.openspec.yaml`, esquema `spec-driven`, 0/4). `proposal`/`design`/`specs`/`tasks` **pendientes**; este ticket + HU |
| `jbg_ai/retrieval/` | Existe: `__init__.py`, `errors.py`, `orchestrator.py`, `ports.py`, `search.py`. **No hay nada de expansión ni de sinónimos** |
| `retrieval/orchestrator.py` | `retrieve_products(payload, principal, *, settings, embed, search)`. Lee `settings.jpv_retrieval_distance_threshold` **directamente**. Emite `stage=embed` y `stage=search`. `match_reasons=["vector"]` literal. `VECTOR_UNTIL_C21_NOTE = "vector_only_until_c21"` |
| `retrieval/search.py` | `compile_search_sql` monta `<=>` + filtros del body. **Ni una referencia a `tsv`, `ts_rank`, `plainto_tsquery` ni `websearch_to_tsquery`** |
| `enrichment/vocab.py` | `fold()` (minúsculas, sin tildes, `ñ`→`n`), `ClosedVocab.resolve()` (empareja sobre plegado → devuelve canónico **con** tilde), `phrases_for()` (**devuelve plegado**), `load_vocabularies()` con `lru_cache` |
| `enrichment/vocabularies.yaml` | 7 vocabularios con `terms` + `synonyms`. Ya trae `sortija→anillo`, `alianza→anillo`, `gargantilla→collar`, `brazalete→pulsera`, `esclava→pulsera`, `aro`/`aros`/`criollas→pendientes`, `plata de ley`/`925`/`sterling`/`silver→plata`, `18k`/`gold→oro`, `dorado`/`chapado en oro`/`gold plated→baño de oro`. **No se toca** |
| `enrichment/confidence.py` | Único consumidor de `phrases_for()`. Precedente de reutilización de la base |
| `indexing/source_text.py` | `build_source_text` emite `Tipo:`, `Materiales:`, `Piedra:`, `Talla:`, `Colores:`, `Estilo:`, `Ocasiones:` con valores canónicos. **Congelado**: `source-text/v1` no se toca |
| `config/settings.py` | `jpv_retrieval_distance_threshold` (0.65) y `jpv_family_*`. **Sin flag de expansión.** `canonical_openapi_settings` pinnea todos los campos |
| `tests/retrieval/` | `conftest.py`, `test_orchestrator.py`, `test_search_port.py`. Docstring del conftest: *«must not open provider or RDS sockets»* |
| `ai.product_document` | 1.168 filas activas, 1.168 con embedding 1536-d. `tsv` **columna generada** `to_tsvector('spanish', doc_text)` + GIN `ix_product_document_tsv`. `Tipo:` en 1.157, `Materiales:` en 1.042 |
| Extensiones de Postgres | Instaladas: `plpgsql`, `vector`. **Disponibles y NO instaladas:** `unaccent`, `pg_trgm`, `fuzzystrmatch` |
| `public."ProductSearchEvents"` | **31 filas, 12 textos distintos**, todos del desarrollador y en vocabulario canónico. No hay distribución real de consultas de la que curar |
| `openapi.json` | Contrato congelado. Este change **no** lo regenera y **no** puede añadir endpoint |
| Alembic | Head C18b. C20 **no** añade revisión |
| `openspec/DEFERRED_TASKS.md` | Singleton del cliente de embeddings y revertir `RetrievalTimeoutMs` 2500→800 ms: asignados a **C21/C22**. C20 no los toca |
| `backend/`, `frontend/`, EF Core | **Sin cambios** |
| HU-AIENG-020 | **Creada** y alineada con este ticket |

**Impacto en producto:** ninguno visible. Hasta que C21 encienda la rama léxica, la expansión **se calcula, se registra y no se consume**. Se declara así en lugar de disimularlo.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/retrieval/query_synonyms.yaml` | **Nuevo.** Overlay de consulta, versionado, con motivo por familia de entradas |
| `ai-service/src/jbg_ai/retrieval/synonyms.py` *(nombre tentativo)* | **Nuevo.** Cargador base+overlay, singularización, `expand_query` pura |
| `ai-service/src/jbg_ai/retrieval/orchestrator.py` | Llamada a `expand_query`, log `stage=expand`, parámetro de flag en la firma |
| `ai-service/src/jbg_ai/api/routers/retrieval.py` | Pasa el default de `Settings` al orquestador. Sin cambio de contrato |
| `ai-service/src/jbg_ai/config/settings.py` | `JPV_QUERY_EXPANSION_ENABLED` con default; pin en `canonical_openapi_settings` |
| `ai-service/src/jbg_ai/retrieval/` (CLI de medición) | **Nueva.** Mide el alcance sobre el índice y escribe el informe |
| `ai-service/evals/` *(o la ruta que fije el `design.md`)* | **Nuevo.** Informe versionado que C24 reutiliza |
| `ai-service/tests/retrieval/` | Tests nuevos: expansión, artefactos del stemmer, plurales, token desconocido, flag apagado, pureza de la función |
| `ai-service/tests/config/` | Default y pin del flag |
| `openspec/changes/add-synonym-dictionary/` | `proposal`, **`design.md`**, `specs`, `tasks` (hoy sólo scaffolding) |
| `ai-service/README.md` | Fila del flag en la tabla de entorno |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-020 (**en el apply**) |
| `enrichment/vocabularies.yaml`, `indexing/`, `openapi.json`, Alembic, `backend/`, `frontend/` | **Sin cambios** |

---

## Especificaciones Técnicas

### ai-service — modelo del diccionario

Dos capas, una sola definición por término:

```
enrichment/vocabularies.yaml   (C09, NO se modifica)
        │  clases base: canónico + sinónimos ya declarados
        ▼
retrieval/query_synonyms.yaml  (C20, sólo consulta)
        │  artefactos del stemmer · coloquialismos · puentes entre vocabularios
        ▼
   clases de equivalencia fusionadas  →  expand_query()
```

Tocar `vocabularies.yaml` obligaría a `enrichment/v2` y arrastraría reenriquecimiento del corpus: es `fix-enrichment-vocabulary-gaps`, no este change. Crear un fichero suelto y completo sería la segunda definición de `sortija→anillo` que diverge en silencio — el motivo por el que se anuló C19.

**Precedencia:** el overlay puede **añadir** formas a una clase y **crear** clases nuevas; no puede reasignar un canónico de la base. Un test lo fija.

### ai-service — contenido del overlay

| Familia | Entradas | Motivo, medido |
|---|---|---|
| Artefactos del stemmer | `collares`, `aros`, `bano de oro`, `banado en oro`, `pequeño`/`pequeno` | Lexemas que no casan entre sí: 140 vs 1, 38 vs 0, 134 vs 71 |
| Sinónimos que la base no tiene | `arete`, `aretes`, `criolla`, `zarcillos`, `aro de dedo`, `choker`, `dije`, `medalla`, `prendedor`, `alfiler`, `cordon`, `cuerda`, `bronce`, `acrilico`, `acero inoxidable` | `criollas` está en la base pero `criolla` no; el resto son variantes de dominio ausentes |
| Puente entre vocabularios | `dorado` → {`dorado` color, `baño de oro`, `oro`} | La clase completa alcanza **64** documentos frente a **22** de la canonicalización simple |

**Exclusiones declaradas en el propio fichero, con su motivo:**

| Excluido | Motivo |
|---|---|
| `piel` → `cuero` | **Falso amigo.** Los 7 documentos que casan dicen «sobre la piel», «acaricia la piel»: piel humana en prosa comercial. `cuero` tiene **un** producto en todo el catálogo |
| `llavero`, `diadema`, `gemelos`, `cinturon` | No son sinónimos: son huecos de `piece_type` → `fix-enrichment-vocabulary-gaps` |
| `filigrana` | No necesita expansión: casa **66** documentos por sí sola, repartidos por todos los tipos de pieza. Es un hueco de `style_tags` |
| `925`, `sterling`, `silver`, `gold`, `18kt`, `cz`, `zirconia`, `gold plated` | Ya en la base y con 0 documentos en el corpus: inocuas, no se duplican |

### ai-service — `expand_query`

Función **pura**: sin sesión de base de datos, sin proveedor, sin sockets.

```
ExpandedQuery(
    original = "gargantilla dorada",
    groups   = [["gargantilla", "collar"],
                ["dorado", "baño de oro", "oro"]],
    matched  = [("gargantilla", "piece_type", "collar"),
                ("dorado",      "color_tags", "dorado")],
)
```

- **`groups`** — una lista de formas de superficie por token de la consulta, en el orden en que aparecen. Un token desconocido es un grupo de un elemento con su forma exacta.
- **`matched`** — `(término tecleado, campo del vocabulario, canónico)`. No es adorno: **es lo que C21 necesita** para su extracción de filtros estructurales por reglas sin construir una segunda tabla de consulta. Sin esto, C21 repite el error de C19 a menor escala.
- **`original`** — el texto intacto, para que C21 pueda fusionar la lista original con la expandida. Es la información que la medición del punto 4 demuestra que no puede perderse.

**Emparejamiento sobre plegado, emisión sobre formas de superficie.** Reutilizar `fold()` y `ClosedVocab.resolve()` — `resolve("bano de oro")` ya devuelve `"baño de oro"` hoy. **`ClosedVocab.phrases_for()` NO sirve para emitir**: devuelve las frases plegadas, y `to_tsvector('spanish','bano')` da `'ban'`, que no casa con `'bañ'`. Las formas con tilde salen de `ClosedVocab.canonical` y del overlay.

**Emparejamiento por frase más larga primero**, para que `aro de dedo` → `anillo` gane a `aro` → `pendientes`.

**Singularización en ambos lados al cargar** —claves del diccionario y token de la consulta—, que resuelve `sortijas`, `gargantillas`, `brazaletes`, `esclavas` y `dorados` sin una entrada por forma. Sólo se aplica cuando la forma reducida existe en el diccionario: nunca inventa un canónico.

**Lo que C20 NO hace: construir la `tsquery`.** Eso es de C21, y la forma segura queda documentada en el `design.md` por haberse verificado contra el índice — composición con los operadores de `tsquery`, sin concatenar sintaxis y sin riesgo de inyección:

```sql
(plainto_tsquery('spanish','gargantilla') || plainto_tsquery('spanish','collar'))
  && (plainto_tsquery('spanish','dorado')  || plainto_tsquery('spanish','baño de oro')
                                           || plainto_tsquery('spanish','oro'))
-- ( 'gargantill' | 'coll' ) & ( 'dor' | 'bañ' & 'oro' | 'oro' )  →  64 documentos
```

### ai-service — flag

`JPV_QUERY_EXPANSION_ENABLED`, booleano, **default `true`**, opcional al boot y sin bloquear `GET /health` (delta de `ai-service-runtime`, misma familia que `JPV_RETRIEVAL_DISTANCE_THRESHOLD`). Pin en `canonical_openapi_settings`.

**El interruptor viaja además por la firma del orquestador**, no sólo por entorno. C24 barrerá `v0-lexico`, `v0-cag` y `v2-hibrido` en el mismo proceso; un flag sólo de entorno obligaría a reiniciar por configuración, y llevarlo a `RetrievalRequest` movería el `openapi.json` congelado. `Settings` aporta el default; el parámetro decide la llamada.

Con el flag apagado: cada token es un grupo de un elemento, `matched` vacío, y el log lo declara — para que una ablación de C24 sea legible a posteriori.

### ai-service — observabilidad

Etapa nueva junto a las dos existentes:

- `stage=expand` — `trace_id`, `enabled`, `tokens`, `matched_terms`, `groups_expanded`, `latency_ms`

La consulta del operador **sólo en Debug** (precedente C03/C04/C14). No se registran las clases completas en Information: el recuento basta y evita volcar el diccionario en cada línea.

**No** se inserta en `ai.query_log` — sigue sin dueño.

### ai-service — CLI de medición e informe

Reproduce sobre `ai.product_document.tsv` el alcance del diccionario: por consulta de una lista curada, documentos que casan con y sin expansión, y por entrada del overlay, documentos que gana. Escribe informe versionado en el repositorio.

Necesita base de datos: **se salta limpiamente** cuando no la hay, como los tests de pgvector de C05. No forma parte de la suite unitaria.

Credenciales por `jbg_ai.data.envload.load_local_env()`, que lee `backend/.env` — la fuente única que Compose interpola. Precedente inmediato: `python -m jbg_ai.indexing` pasó a llamarlo en esta misma rama.

### Contrato OpenAPI

Cero cambios. `test_openapi_snapshot_is_stable` verde **sin** regenerar. No se añade endpoint: si hiciera falta exponer la expansión por HTTP, el contrato se movería y eso exige acuerdo con quien posee el cliente .NET.

### Tests

| Test | Qué prueba |
|---|---|
| `test_query_with_synonym_matches_canonical_term` | `sortija` alcanza la clase de `anillo`; `matched` lo registra |
| `test_expansion_returns_groups_not_a_rewritten_string` | La salida son grupos; no hay cadena reescrita ni sintaxis de `tsquery` |
| `test_stemmer_split_terms_are_expanded` | `collares`→`collar`, `bano de oro`→`baño de oro`, `pequeño`↔`pequeno` |
| `test_plural_is_resolved_without_a_dedicated_entry` | `sortijas`, `gargantillas`, `brazaletes`, `esclavas`, `dorados` |
| `test_longest_phrase_wins_over_shorter_token` | `aro de dedo`→`anillo` gana a `aro`→`pendientes` |
| `test_unknown_term_passes_through_unchanged` | Token desconocido = grupo de uno, forma exacta |
| `test_disabled_flag_returns_original_query` | Flag apagado por `Settings` y por parámetro |
| `test_expansion_does_not_modify_indexed_documents` | `doc_text` / `tsv` / `source_hash` intactos |
| `test_base_vocabulary_file_is_not_modified` | Fijación: `vocabularies.yaml` sin diff |
| `test_overlay_never_overrides_a_base_canonical` | El overlay añade, no reasigna |
| `test_expansion_makes_no_database_or_provider_call` | Pureza: ni sesión ni socket |
| `test_excluded_false_friend_is_absent` | `piel` no está en ninguna clase de `cuero` |

Sin fakes de red porque no hay red. Ningún test exige que el índice tenga 1.168 filas.

---

## Arquitectura

```
  POST /v1/retrieval/products            JWT interno (con pos_id)
              │
              └─ STUB_MODE=false
                     │
                     ▼
              retrieval/ ──► expand_query(text, enabled)   ← C20  · función pura
                     │            │
                     │            ├─ groups   ──┐
                     │            └─ matched  ──┼─► C21: rama léxica, RRF, filtros
                     │                          │        (NO en este change)
                     │        log stage=expand ─┘
                     │
                     ├─ embed(TEXTO ORIGINAL)   ← el vector NO se expande
                     │
                     ▼
              SQL  embedding <=> q ≤ threshold   ← C14, sin cambios
                     │
                     ▼
              200 results / low_confidence

  ai.product_document.tsv  ── generada, GIN, poblada, SIN CONSUMIDOR hasta C21
```

Decisiones heredadas: §6.2 del diseño (Python parecido / .NET números) · C02 contrato congelado · C05 `tsv` generada + GIN · C09 vocabulario cerrado y su normalización de sinónimos **en extracción** · C11 `source-text/v1` y `embeddings.py` congelados · C14 umbral, overfetch y etapas de log.

**Breaking:** ninguno. Ni OpenAPI, ni EF, ni contrato REST. El comportamiento observable de `POST /v1/retrieval/products` es **idéntico** antes y después: sólo aparece una línea de log más. Es deliberado, y es lo que hace que C20 sea seguro de archivar antes de que exista su consumidor.

---

## Definición de Hecho (DoD)

- [ ] Código según C4 / `openspec/project.md` (Python vectorial y léxico; .NET y frontend no se tocan)
- [ ] `uv run pytest` verde **sin** llamadas reales a embeddings, LLM, API .NET ni RDS
- [ ] Tests nuevos con nomenclatura `test_<unidad>_<escenario>_<esperado>`; la expansión no abre sesión ni socket
- [ ] `enrichment/vocabularies.yaml` **sin diff**, verificado por test de fijación
- [ ] `ai-service/openapi.json` **sin** regenerar; `test_openapi_snapshot_is_stable` verde
- [ ] Sin revisión de Alembic, sin migración de EF Core, sin extensión de Postgres nueva
- [ ] `indexing/embeddings.py` y `indexing/source_text.py` sin diff; ningún documento reindexado
- [ ] Specs delta en `openspec/changes/add-synonym-dictionary/specs/` y `openspec validate --all --strict` → `0 failed`
- [ ] `design.md` presente, con las cuatro decisiones de alternativa real y sus números
- [ ] Informe de medición versionado en el repositorio y citado desde el `qa.md`
- [ ] Documentación: HU, este ticket, fila del flag en `ai-service/README.md`, `epicas.md` (EP14) en el apply
- [ ] Sin TODO/FIXME huérfano
- [ ] Verificación **posterior** (no merge): la CLI reproduce `gargantilla dorada` 0 → 64 y `collares de plata` 0 → 66 contra el índice local

No aplica: xUnit, Vitest, Playwright, UI es-ES, cobertura de frontend, migración, regenerar OpenAPI.

---

## Requisitos No Funcionales

- **Seguridad:** la expansión no toca credenciales. La consulta del operador sólo en Debug, como en C03/C04/C14. La CLI de medición lee `backend/.env` por `load_local_env()` y nunca imprime valores. Ninguna clave nueva.
- **Rendimiento / free-tier:** `expand_query` es aritmética de diccionarios sobre una consulta de ≤ 500 caracteres. **Medido tras implementar** (`/opsx:verify`, 2026-09-01): **0,02–0,09 ms** en consultas de operador reales y **1,76 ms** en el máximo de 500 caracteres del contrato — el objetivo inicial de «< 1 ms» se cumple con tres órdenes de magnitud de margen en el tráfico real y **no** se cumple en el extremo, que es una consulta que nadie escribe y sigue siendo ruido frente a los 170–1707 ms del embed. El diccionario se carga **una vez por proceso** con `lru_cache`, como `load_vocabularies()`: **28,3 ms** que paga la primera búsqueda y no el arranque, porque cargarlo al boot encarecería `GET /health`, que es un latido y debe seguir siendo barato. **Cero llamadas nuevas al proveedor y cero consultas SQL nuevas**: es el motivo por el que no toca la rama vectorial.
- **Observabilidad:** `stage=expand` con `trace_id`, junto a `stage=embed` y `stage=search`. Recuentos, no el diccionario entero. Sin `ai.query_log`.
- **Integridad:** la expansión es de **consulta**; ningún documento se reescribe ni se reindexa, y `source_hash` no puede moverse. Python no lee el esquema `public`. El diccionario es determinista: la misma consulta produce siempre los mismos grupos, requisito de `test_run_is_reproducible_for_same_config_and_seed` de C24.

---

## Preguntas Abiertas

Las diez decisiones de diseño quedaron cerradas en la exploración del 2026-09-01 y están en la tabla de la HU y en el §0 del plan. Queda esto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿La expansión es una **capability nueva** (`query-expansion`) o un **delta de `vector-retrieval`**? | **Capability nueva**, más delta de `ai-service-runtime` por el flag. `vector-retrieval` describe el comportamiento del endpoint, que no cambia; una capability propia es lo que C21 heredará |
| 2 | Nombre del módulo: `retrieval/synonyms.py` o `retrieval/query_expansion.py` | **`retrieval/synonyms.py`** — el fichero de datos es `query_synonyms.yaml` y el change se llama `add-synonym-dictionary` |
| 3 | Ruta del informe de medición: `ai-service/evals/results/` (territorio de C24) o una carpeta propia de C20 | **`ai-service/evals/results/`**, creando el árbol. C24 lo reutiliza y no se duplican dos sitios para el mismo tipo de artefacto |
| 4 | ¿La CLI es subcomando de `python -m jbg_ai.indexing` o entrypoint propio? | **Entrypoint propio** bajo `jbg_ai.retrieval`, para no ampliar la superficie de la CLI de indexado, que escribe en la base |
| 5 | ¿Cuántas entradas exactas lleva el overlay al cerrar? | Las **~18** inventariadas, ni una más «por si acaso». Cada entrada nueva se justifica con su recuento de documentos o no entra |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** edite `vocabularies.yaml`, **no** regenere `openapi.json`, **no** toque la rama vectorial, **no** abra migración y **no** adelante nada de C21.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta**. Pintado 🟢 pero es **el tapón del grafo**: lo único que separa a C21 de arrancar, y C21 bloquea a C24 y a C30. Nunca se recorta (§6 del plan).
- **Estimación:** **2 SP** *(pendiente de refinamiento)*. No hay algoritmo, ni migración, ni interfaz, ni contrato. El trabajo real es de **curación y medición**.
- **Dependencias:** C14 archivado · índice local poblado, sólo para la CLI de medición · **bloquea C21**, y con él C24, C25 y C30 · **no paralelizar con C21**: misma zona `retrieval/`.
- **Línea de corte** si desborda (regla 5 del plan): (1) cargador base+overlay + `expand_query` + flag + tests, archivable por sí solo; (2) log `stage=expand`; (3) CLI de medición e informe.
- **Tags:** `HU-AIENG-020`, `C20`, `EP14`, `ai-service`, `python`, `retrieval`, `lexical`, `synonyms`, `full-text-search`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-020](../../../../Documentos/Historias/AI-Eng/HU-AIENG-020.md)
- **Change OpenSpec:** `openspec/changes/add-synonym-dictionary/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C20, entrada de §0 del 2026-09-01) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§7.3, §7.4, §7.6)
- **Apuntes del Máster (guía, no dogma):** [Búsqueda híbrida](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Busqueda%20hibrida.md) (RRF, `ts_rank`, el problema del término exacto) · [Expansión y descomposición de consultas](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Expansion%20y%20descomposicion%20de%20consultas.md) (proponen multi-query con LLM; aquí se elige diccionario por latencia, coste y reproducibilidad)
- **Specs vivas:** `vector-retrieval` · `catalog-enrichment-pipeline` · `catalog-source-text` · `ai-vector-schema` · `ai-service-runtime` · `ai-service-api-contracts`
- **Precedentes:** C09 (`vocabularies.yaml`, `fold()`, `resolve()`) · C11 (`source-text/v1`, cliente congelado) · C14 (etapas de log, umbral, patrón stub/real) · C18a/C18b (medir antes de creerse la ficha) · C19 (por qué no se duplica una definición)
- **Deuda ajena que este change no paga:** [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) — singleton del cliente de embeddings y `RetrievalTimeoutMs` 2500→800 ms, ambos de C21/C22
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-01 | `/enrich-us` | Creación a partir de HU-AIENG-020 y de la exploración medida del mismo día. Recoge: base `vocabularies.yaml` + overlay de consulta, artefactos del stemmer como contenido de primera clase, grupos de equivalencia en vez de cadena reescrita, flag en la firma del orquestador, observe-only con `stage=expand` e informe versionado, exclusión de `piel` con motivo medido, y la rama vectorial fuera de alcance con sus números |
