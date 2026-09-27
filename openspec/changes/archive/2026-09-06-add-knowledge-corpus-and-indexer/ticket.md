# T-AIENG-023: Commercial knowledge corpus, section chunker, idempotent indexer and citation-carrying search (C23)

> Ticket técnico del change OpenSpec `add-knowledge-corpus-and-indexer`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, specs vivas de `openspec/specs/`, [HU-AIENG-023](../../../../Documentos/Historias/AI-Eng/HU-AIENG-023.md) y las mediciones y decisiones de [c23-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c23-exploration-measurements.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-023 / C23** — Construir el segundo índice: corpus de conocimiento comercial **general, no por producto**, troceado por secciones, indexado de forma idempotente en `ai.knowledge_chunk` y consultable con citas que resuelven, localizan y declaran el alcance de lo que afirman

---

## Contexto y Problema

El sistema tiene **un solo índice**. `ai.product_document` responde a «enséñame anillos de plata» y no puede responder a «¿este anillo se puede mojar?», porque esa respuesta no vive en ningún producto. El §5 del diseño ya separó los dos problemas: el catálogo **no se trocea** (una entidad de ~15 atributos y 40-120 palabras), pero el conocimiento comercial general **sí**, y es *«lo que permite citas verificables»* sin violar la decisión 4 de la revisión, que prohíbe el conocimiento por producto.

C05 dejó creadas `ai.knowledge_document` y `ai.knowledge_chunk` con todo lo que hace falta —`doc_type` restringido a cinco valores, borrado en cascada, único `(document_id, chunk_index)`, HNSW coseno, GIN sobre `tsv` y sobre `metadata`— y **ningún código las escribe ni las lee**. C21 dejó el módulo de fusión puro y sin dominio, con un docstring que **nombra a C23** como importador futuro. C20 dejó la expansión de consulta cuyos grupos son, precisamente, el vocabulario de materiales y piedras de este corpus.

Faltan las dos mitades que nadie ha hecho: **el contenido** y **el camino de ida y vuelta hasta él**.

Y hay un problema que gobierna el diseño y que no es de código. El §8.1 daba los textos comerciales de la joyería como *«a pedir al negocio»*, el mismo estado en el que estaban las fotografías, **que nunca llegaron**. El corpus lo va a redactar un asistente. El apunte de S11 advierte de la consecuencia exacta: la verificación de citas es **estructural, no semántica** —confirma que la fuente citada existía y se recuperó, no que diga la verdad—, así que un corpus inventado puede pasar el 100 % de la comprobación y estar citando algo falso **con sello de verificado**. La respuesta del change no es fingir: es **separar por sección** lo comprobable fuera de lo que solo la joyería puede confirmar, y hacer que esa marca gobierne cómo se presenta la cita.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `ai.knowledge_document` (`doc_type` con `CHECK` de cinco valores, `source_ref`, índice por `doc_type`) | Existe (C05, migración `f46c55c056e2`) · **ningún código la escribe** |
| `ai.knowledge_chunk` (FK `ON DELETE CASCADE`, único `(document_id, chunk_index)`, `metadata jsonb`, `embedding vector(1536)`, `tsv` generada en español, HNSW coseno, GIN sobre `tsv` y sobre `metadata`) | Existe (C05) · **ningún código la escribe** |
| Spec viva `ai-vector-schema` con los requisitos de ambas tablas | Existe · cubre esquema e índices, **no** contenido ni búsqueda |
| `retrieval/fusion.py` — `RankedList`, `FusedCandidate`, `fuse`, `truncate`, `normalised_scores` | Existe (C21) · puro, sin dominio, **nombra a C23** en su docstring |
| `retrieval/synonyms.py` — `expand_query`, `ExpandedQuery`, `TermMatch`, `load_query_dictionary` | Existe (C20) · devuelve grupos de equivalencia, nunca una cadena reescrita |
| `retrieval/lexical.py` — `LexicalRequest`, `compose_group_fragments`, `build_fragments` | Existe (C21) · compone fragmentos `tsquery`; el SQL vive en `retrieval/search.py`, atado a `ai.product_document` |
| `indexing/embeddings.py` — `EmbeddingClient`, `LiteLlmEmbeddingClient`, `InMemoryEmbeddingCache` | Existe (C11) · **congelado**; su docstring dice literalmente *«C23 reuses this module and must not edit it»* |
| `app.state.retrieval_embed` (singleton del cliente de embeddings) | Existe · la deuda de «cliente por petición» de C15 **está pagada** |
| CLI `python -m jbg_ai.indexing sync` / `sync-pos` | Existen (C13, C22) · catálogo y disponibilidad. **No hay `sync-knowledge`** |
| `jbg_ai/knowledge/` | **No existe** |
| `ai-service/tests/knowledge/` | **No existe** |
| `data/knowledge/` | **No existe.** `data/catalog/` y `data/world/` sí; `git check-ignore` confirma que un fichero bajo `data/knowledge/` **no** queda ignorado |
| `ai-service/prompts/` | Existe con `catalog-synth/` (v1-v3 + schemas) y `enrichment/` (v1, v2). **No hay `knowledge/`** |
| `jpv_retrieval_distance_threshold` (0,65) y `FUSION_DEFAULTS` en `config/settings.py` | Existen · calibrados **para productos** |
| `api/routers/assist.py` | Stub · *«Real generation arrives in C30»* — el consumidor de este change |
| Artefactos OpenSpec de este change | **A generar** (0/4, schema `spec-driven`) |

**Impacto en producto:** abre una clase de pregunta que el sistema hoy no puede contestar en absoluto —cuidados, alergias, medidas, servicio— y entrega el único mecanismo del proyecto que permite responder **diciendo de dónde sale la respuesta**. El operador no lo ve hasta C30; sin esto, C30 no tiene nada que citar.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `data/knowledge/` | **Alto** — corpus nuevo: 32 documentos Markdown, ~161 secciones, más `README` de autoría y sidecar `.meta.json` |
| `ai-service/src/jbg_ai/knowledge/` | **Alto** — paquete nuevo: `corpus.py`, `chunking.py`, `indexer.py`, `search.py` |
| `ai-service/prompts/knowledge/` | **Alto** — ocho prompts versionados, uno por bloque de generación |
| `ai-service/src/jbg_ai/indexing/cli.py` | **Bajo** — un subcomando `sync-knowledge`. Único fichero compartido que se toca |
| `ai-service/src/jbg_ai/config/settings.py` | **Bajo** — umbral de conocimiento y flag de fusión, con default y valor efectivo por parámetro |
| `ai-service/tests/knowledge/` | **Alto** — batería nueva, íntegramente *offline* |
| `ai-service/README.md` | **Bajo** — comando de sincronización y filas de entorno |
| `openspec/changes/<change>/specs/` | **Alto** — capacidad nueva `knowledge-corpus` |
| `Documentos/` | **Medio** — `epicas.md` (EP12), informe de la mini-medición, limitación del README |
| `ai-service/openapi.json` · `backend/` · `frontend/` · `terraform/` · `.github/workflows/` | **Ninguno** |

---

## Especificaciones Técnicas

### Corpus (`data/knowledge/`)

**32 documentos, ~161 secciones**, con el desglose cerrado en el §5 del informe: 9 fichas de material (una por canónico de `vocabularies.yaml`) · 2 de combinaciones y marcajes · 3 de piedras · 4 de medidas y tallas · 4 de uso y entorno · 2 de piel y seguridad · 4 de servicio · 2 de regalo · 1 glosario · 1 de Menorca y el origen de las colecciones. `doc_type`: `material` 14 · `talla` 4 · `faq` 10 · `politica` 4 · **`guion_venta` 0**.

**Convención de talla de anillo de la casa** (D16, cerrada el 2026-09-06). `XS`–`XL` **no es un sistema normalizado de anillo**: es una escala de prenda aplicada a todo el catálogo, y para una red en hoteles y aeropuerto es la correcta. La letra mide la pieza en todos los tipos; **el anillo es el único con tabla de equivalencia**, y esa tabla vive en **un solo documento**, `tallas-anillos`:

| Letra | Talla española | Circunferencia interior | Diámetro interior |
|---|---|---|---|
| `XXS` * | 4 – 6 | 44 – 46 mm | 14,0 – 14,6 mm |
| `XS` | 7 – 9 | 47 – 49 mm | 15,0 – 15,6 mm |
| `S` | 10 – 12 | 50 – 52 mm | 15,9 – 16,6 mm |
| `M` | 13 – 15 | 53 – 55 mm | 16,9 – 17,5 mm |
| `L` | 16 – 18 | 56 – 58 mm | 17,8 – 18,5 mm |
| `XL` | 19 – 21 | 59 – 61 mm | 18,8 – 19,4 mm |
| `XXL` * | 22 – 24 | 62 – 64 mm | 19,7 – 20,4 mm |

\* Por encargo, no de surtido: son los dos únicos peldaños del vocabulario con **cero apariciones** en los 1.200 productos. `circunferencia = talla + 40` es la regla española de siempre → sección `general`; la asignación de letras a tramos es de la casa → sección `establecimiento`. `mini`, `extramini`, `pequeño`, `mediano` y `grande` describen el motivo y **nunca** un ajuste. Los límites de ajuste —±2 tallas en aro liso de plata u oro; nunca alianza con piedras en todo el contorno, motivo que recorre la banda, aro hueco, baño de oro, latón ni acero— deben decir **lo mismo** aquí, en las fichas de material y en `politica-reparaciones-y-ajustes`, y hay test que lo comprueba.

**Formato de autoría** (validado en la ingesta, no confiado al autor):

- Un fichero por documento, con `# Título` y a continuación **solo** secciones `##`. Texto antes de la primera sección → **error de ingesta**: un preámbulo sin sección es un fragmento sin localizador.
- Una sección = una afirmación citable, **80-250 palabras**. Por encima del tope → **error de ingesta**, nunca troceado automático. Misma disciplina que el tope de 1.000 caracteres de C06b.
- `claim_scope` obligatorio por sección, en comentario HTML bajo el encabezado (`<!-- claim_scope: general -->`), **retirado antes de construir `content`** para que no entre ni en el embedding ni en el `tsv`. Ausente → error de ingesta.
- `source_ref` opcional por sección: referencia externa, o el comando que re-mide el catálogo para las afirmaciones verificables contra los datos.
- **Prohibido** nombrar un SKU, un producto concreto o un precio (decisión 4 del diseño, y regla de placeholders de C30).
- **Modo descriptivo, nunca imperativo.**

**Sidecar `.meta.json`**, en el patrón de `data/catalog/*/generated/*.meta.json`: `generator_version`, `model`, `prompt_version`, `generated_at`, recuentos por `doc_type` y por `claim_scope`.

### Servicio Python (`ai-service`) — paquete `jbg_ai/knowledge/`

**`corpus.py` — carga y validación.** Lectura de `data/knowledge/*.md`, parseo de título, secciones y marcas, y las validaciones de arriba. Errores propios (`KnowledgeCorpusError`) que nombran fichero y sección.

**`chunking.py` — troceado por secciones.**

- Una sección `##` = un chunk. **Sin solape**: las secciones son autocontenidas por regla de autoría, y solapar fragmentos de 100 palabras duplicaría medio corpus.
- `content = "# <título del documento>\n## <título de la sección>\n\n<texto>"`. El `tsv` es **columna generada sobre `content`**, así que los dos títulos entran a la vez en el índice léxico y en el embedding: es lo único que desambigua nueve fichas de material casi gemelas, y sale gratis.
- `metadata`: `citation_id`, `document_slug`, `document_title`, `section_slug`, `section_title`, `claim_scope`, `content_hash`, `source_ref` (opcional).

**`indexer.py` — indexación idempotente.**

- `knowledge_document.id = uuid5(NS, document_slug)`; `knowledge_chunk.id = uuid5(NS, f"{document_slug}#{section_slug}")`. **Nunca `uuid4`**, y **nunca** identidad basada en `chunk_index`.
- `chunk_index` se sigue escribiendo (lo exige el único de la tabla) y **no** es identidad de cita.
- Upsert por documento; los chunks que la ejecución no produce **se borran**. Borrar un documento arrastra sus chunks por la FK, sin lógica de aplicación.
- Se re-embebe solo si `metadata.content_hash` cambió o si el `embedding_version` no coincide. **`content_hash` en `metadata`, no en columna nueva**: la tabla no la tiene y este change no abre migración.
- `embedding_model` / `embedding_version` con clave de versión propia del conocimiento, calculada **en este paquete**: `indexing/embeddings.py` no se toca, y su `document_version_key` sella `SOURCE_TEXT_VERSION`, que es del texto de producto.
- Cliente de embeddings **inyectable**, reutilizando `EmbeddingClient` de C11.

**`search.py` — búsqueda con citas.**

- Firma con forma de *tool*: pregunta en lenguaje natural, `top_k`, `doc_type` opcional; devuelve fragmentos con `citation_id`, `claim_scope`, títulos, texto y puntuación.
- **Rama vectorial**: k-NN coseno sobre `ai.knowledge_chunk.embedding`, alineado con `<=>`.
- **Rama léxica**: `tsquery` compuesta desde los grupos de `expand_query` de C20, con parámetros ligados y sin adyacencia posicional, sobre `knowledge_chunk.tsv`. SQL propio de este paquete: el de `retrieval/search.py` está atado a `ai.product_document` y **no se toca**.
- **Fusión por RRF** importando `retrieval/fusion.py` — sin reescribir una línea y sin leer puntuaciones crudas.
- **Umbral de abstención propio**: por debajo, **cero fragmentos**. No se reutiliza el 0,65 de productos.
- **Filtro por `doc_type` solo si el llamante lo pide.** Nada de filtro duro deducido de la consulta: la spec viva `query-expansion` ya fija que los filtros por regla degradan y no excluyen.
- **Ningún router.** El destino lo decide el llamante (diseño §9.1, tool `consultar_conocimiento`).

**CLI:** `python -m jbg_ai.indexing sync-knowledge [--full]`, con la misma carga de entorno que `sync` y `sync-pos`, y documentación en `ai-service/README.md`. **Sin ruta HTTP.**

**Settings nuevos** (default en `Settings`, valor efectivo como parámetro de la llamada, fila en la tabla de entorno del README):

| Setting | Default | Para qué |
|---|---|---|
| `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` | _a fijar en `design.md` con la mini-medición_ | Abstención propia del conocimiento |
| `JPV_KNOWLEDGE_HYBRID_ENABLED` | `true` | Apagar la rama léxica para medir qué aporta |

**Logs:** `stage=knowledge`, junto a `expand`, `embed`, `search`, `lexical`, `filters` y `fuse`, con `trace_id`.

### Generación del corpus — planificación obligatoria

**No cabe en una ventana de contexto y no se intenta.** 161 secciones de 80-250 palabras son ~25.000 palabras de salida útil, más las reglas de autoría, el esqueleto del bloque y la evidencia medida **en cada petición**. De una sola vez, las primeras fichas se olvidan y las últimas derivan del esqueleto: se pierde la homogeneidad que hace comparables a nueve fichas de material.

**Ocho encargos, uno por bloque, cada uno en un subagente o en una ventana de chat nueva.** Nunca el corpus entero; nunca un documento suelto por encargo.

| Encargo | Bloque | Docs | Secciones |
|---|---|---:|---:|
| 1 | A materiales frecuentes: `plata`, `oro`, `baño de oro`, `latón`, `hilo` | 5 | 31 |
| 2 | A materiales residuales: `perla`, `resina`, `acero`, `cuero` + B combinaciones y marcajes | 6 | 26 |
| 3 | C piedras | 3 | 16 |
| 4 | D medidas y tallas | 4 | 20 |
| 5 | E uso y entorno | 4 | 18 |
| 6 | F piel y seguridad + H regalo | 4 | 18 |
| 7 | G servicio *(todo `establecimiento`)* | 4 | 19 |
| 8 | I glosario + J Menorca | 2 | 13 |

**Prompts en `ai-service/prompts/knowledge/v1/`, uno por bloque**, en el patrón de `catalog-synth/` y `enrichment/`. Cada uno lleva: el esqueleto exacto de secciones con su `claim_scope`; las siete reglas de autoría **completas, no resumidas**; la evidencia medida de ese bloque (productos por material, pares multi-material, cruce `piece_type × size_label`, topónimos); la prohibición de nombrar SKU, producto o precio; y la instrucción de devolver **solo ficheros Markdown**, sin comentario alrededor.

**Revisión humana bloque a bloque según llega**, no acumulada: ~4-6 minutos por documento, ~2-3 horas en total, y el cuello de botella de atención de un revisor único ya está identificado en el §7.8 del diseño.

### Fuera de este ticket

Generación con citas, `pitch` y avisos por reglas (**C30**) · golden set y tablas `ai.eval_*` (**C24**) · RAGAS y validador anti-alucinación (**§11.3, C24**) · señales de negocio (**C25**) · sustitutos (**C26**) y complementarios (**C27**) · ruta `/v1/knowledge/*` y regeneración de `openapi.json` · router LLM · `guion_venta` · reranking · fusión de los dos índices · migración de cualquier clase · `ai.query_log` · tocar `indexing/embeddings.py`, `enrichment/vocabularies.yaml`, `retrieval/orchestrator.py`, `retrieval/search.py`, `frontend/`, `terraform/` o `.github/workflows/`.

---

## Arquitectura

- **Frontera intacta** (diseño §6.2): *Python calcula parecidos y redacta; .NET calcula números y decide*. Este change no cruza a .NET en absoluto y no lee el esquema `public`.
- **Segundo índice, y los dos no se fusionan.** Un producto es una entidad que se ordena y se hidrata; un chunk es una afirmación que se cita. S10 lo advierte: fusionar colecciones distintas por puntuación cruda es incomparable, y aplanarlas *«destruye información que costó un router obtener»*. Aquí la procedencia se conserva **no fusionando**.
- **Routing de nivel cero.** S10: *«el mejor router es no tener router»*, y la forma correcta de capturar el destino es el contrato o el llamante. El diseño §9.1 ya nombró la tool.
- **Citación según S11:** *resuelve* (el identificador estuvo en el contexto), *localiza* (apunta a la sección, no al documento) y *es trazable* (con el corpus en git, el `citation_id` abre fichero y encabezado). El servicio emite `document_id` y localizador, **nunca URLs ni permisos**: esa resolución es de la capa de negocio.
- **Patrones en uso:** puerto inyectable con `Protocol` para la búsqueda y para el cliente de embeddings, función pura para el troceado, y el patrón de flag de C20/C21/C22 —default en `Settings`, valor efectivo por parámetro— para poder medir sin reiniciar y sin mover contrato.
- **Decisiones previas que se respetan:** `indexing/embeddings.py` congelado desde C11 · `enrichment/vocabularies.yaml` intacto · pool de 5 sin overflow · superficie `/v1` congelada.
- **Breaking changes:** **ninguno**. No se toca `ai-service/openapi.json`, no cambia ningún contrato REST de `backend/`, y las dos tablas ya existen con su forma final.
- **Specs.** Capacidad **nueva** `knowledge-corpus`, al estilo de `hybrid-fusion` en C21 y `pos-projection` en C22. `ai-vector-schema` **no** necesita delta: ya especifica esquema e índices de ambas tablas, y este change no los altera — cubre contenido, troceado, indexación y búsqueda, que aquella no toca.

---

## Criterios de Aceptación

Los doce escenarios normativos están en [HU-AIENG-023](../../../../Documentos/Historias/AI-Eng/HU-AIENG-023.md#criterios-de-aceptación). En resumen ejecutable:

**Pruebas de validación** (`uv run pytest` desde `ai-service/`, todas *offline*):

- `test_chunker_preserves_section_titles_in_metadata` *(de la ficha)*
- `test_every_chunk_has_traceable_document_id` *(de la ficha)*
- `test_material_sheet_is_not_product_scoped` *(de la ficha)*
- `test_knowledge_search_returns_chunk_with_citation_id` *(de la ficha)*
- `test_citation_id_resolves_to_a_file_and_a_heading_in_the_corpus`
- `test_every_canonical_material_has_exactly_one_sheet`
- `test_chunk_identity_is_stable_across_reindexing`
- `test_inserting_a_section_does_not_repoint_existing_citations`
- `test_reindexing_removes_chunks_no_longer_produced`
- `test_unchanged_section_is_not_re_embedded`
- `test_section_over_the_size_limit_fails_ingestion`
- `test_document_with_text_before_first_section_is_rejected`
- `test_section_without_claim_scope_is_rejected`
- `test_corpus_contains_no_sku_product_or_price`
- `test_corpus_contains_no_sales_script_document`
- `test_claim_scope_travels_with_the_returned_chunk`
- `test_out_of_domain_question_returns_no_citation`
- `test_hybrid_disabled_falls_back_to_vector_only`
- `test_knowledge_search_makes_no_provider_call_with_injected_fake`
- `test_embeddings_module_is_untouched` *(guardia de la congelación de C11)*

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec completos: `proposal`, **`design.md` obligatorio**, `specs` (capacidad nueva `knowledge-corpus`) y `tasks`
- [ ] `openspec validate --all --strict` en **`0 failed`**
- [ ] Corpus completo: **32 documentos**, ~161 secciones, todas con `claim_scope`, revisadas bloque a bloque
- [ ] Ocho prompts versionados en `ai-service/prompts/knowledge/v1/` y sidecar `.meta.json` sellado
- [ ] `uv run pytest` en verde, **sin llamadas reales** a LLM, embeddings ni RDS; tests de BD con testcontainers y pgvector
- [ ] `dotnet test` y `npm run test` **sin ejecutar**: este change no toca `backend/` ni `frontend/` y su diff lo demuestra
- [ ] **Cero migraciones**, ni Alembic ni EF Core; `ai-service/openapi.json` **sin diff**
- [ ] `indexing/embeddings.py`, `enrichment/vocabularies.yaml`, `retrieval/orchestrator.py`, `retrieval/search.py` y el árbol `frontend/` **sin diff**
- [ ] Mini-medición ejecutada (~32 preguntas + 4-5 fuera de dominio) con Recall@3, MRR y abstención, y decisión registrada sobre la rama léxica
- [ ] Informe versionado en `Documentos/Proyecto Final AIEng/informes/`
- [ ] `Documentos/epicas.md` (EP12) enlaza HU-AIENG-023; limitación del corpus sintético declarada para el README
- [ ] `ai-service/README.md` documenta `sync-knowledge` y los settings nuevos
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] Corpus en español (es-ES)

---

## Requisitos No Funcionales

- **Seguridad:** el corpus es contenido público de la joyería y no lleva datos personales ni precios. La búsqueda no acepta identificadores de producto ni acota por punto de venta: el conocimiento es general por definición. El servicio emite `document_id` y localizador, **nunca URLs ni decisiones de permiso** — esa resolución es de la capa de negocio (S11).
- **Rendimiento:** ~161 chunks, dos ramas sobre una tabla diminuta. La consulta de conocimiento solo se dispara cuando el agente la pide, no en cada búsqueda. El embedding de la pregunta reutiliza el singleton y la caché de proceso ya existentes. La latencia se **mide y se anota** para que C30 herede el número; el presupuesto de recuperación de C16 (2.500 ms) no se toca.
- **Observabilidad:** `stage=knowledge` con `trace_id`; contadores de la CLI (documentos, chunks, re-embebidos, omitidos, borrados).
- **Integridad de datos:** la indexación es idempotente y la identidad del chunk es determinista, de modo que reindexar no rompe citas. Los chunks que el corpus ya no produce se borran, y borrar un documento arrastra los suyos por la FK. Ninguna sección puede entrar sin `claim_scope`.
- **Reproducibilidad:** el sidecar sella modelo, versión de prompt e instante; la mini-medición corre desde fixture y sin proveedor, de modo que su resultado no depende del día.

---

## Preguntas Abiertas → Decisiones

Las **quince** decisiones de diseño están en la tabla de [HU-AIENG-023](../../../../Documentos/Historias/AI-Eng/HU-AIENG-023.md#decisiones-de-diseño-ya-acordadas) y desarrolladas en [`design.md`](./design.md). Las cuatro preguntas que quedaban abiertas se **resolvieron con su opción por defecto el 2026-09-06**, al generar los artefactos:

| # | Pregunta | Resolución |
|---|---|---|
| 1 | Valor de `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` | **Se calibra, no se elige** (D8): el valor más estricto que mantiene en cero las preguntas fuera de dominio sin perder ninguna de las 32 con respuesta. Arranca con el de productos, **marcado provisional**, y sustituirlo por el calibrado es requisito del DoD |
| 2 | ¿Se queda la rama léxica? | **Sí por defecto, y se mide** (D7). Se mide vectorial solo primero; si el híbrido no mueve el número, la rama se retira y el informe lo declara |
| 3 | Tope de tamaño de sección | **1.200 caracteres** (D14), en el espíritu del tope de 1.000 de C06b, revisable con el corpus real delante |
| 4 | ¿`ai-vector-schema` necesita delta? | **No** (D0). Leídos sus quince requisitos: seis tocan el corpus y este change los **consume** sin alterar columna, índice ni restricción. Si durante el apply apareciera una frase que queda falsa, se emite el delta antes de archivar — es el fallo de agosto que `--all --strict` no caza solo |

Y la que era la única genuinamente abierta —**la convención de talla de anillo**— queda **cerrada en D16**, con la tabla de arriba. No queda ninguna pregunta que bloquee.

**Verificación posterior, no bloqueante:** confirmar la tabla de tallas con el negocio antes de grabar el vídeo de la demo. Si sus tramos son otros, cambia **una** sección de **un** documento, y su marca `establecimiento` ya la señala como compromiso de la casa y no como hecho.

---

## Prioridad / Estimación / Tags

- **Prioridad:** Media-alta — **no** está en la cadena crítica `C21 → C24 → C25 → C26 → C34 → C36`, pero es prerrequisito único de C30 y con él de toda la rama de generación `C30 → C31 → C32 → C38 → C39`. Entra por el lado y sin bloquear a nadie, que es exactamente lo que lo hace un buen candidato ahora.
- **Estimación:** _Pendiente_ (complejidad **4** según la HU: el código es modesto y acotado; lo caro es el corpus y su revisión)
- **Tags:** `ai-service` · `knowledge` · `retrieval` · `indexing` · `corpus` · `openspec` · `no-migration` · `no-contract-change` · `C23`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-023](../../../../Documentos/Historias/AI-Eng/HU-AIENG-023.md)
- **Change:** [`openspec/changes/add-knowledge-corpus-and-indexer/`](./)
- **Mediciones y decisiones:** [c23-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c23-exploration-measurements.md)
- **Diseño RAG:** [§5, §7.2, §7.7, §8.2, §8.3 y §11.3](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Plan de changes:** [ficha C23 y corte pre-autorizado del §13.4](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Specs vivas:** `openspec/specs/ai-vector-schema/`, `openspec/specs/hybrid-fusion/`, `openspec/specs/query-expansion/`, `openspec/specs/ai-service-api-contracts/`
- **Procedimientos:** [User Stories](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Tickets de Trabajo](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)
- **Apuntes:** [S11 · Citación y atribución verificable](../../../../Documentos/Sesiones%20Master%20AIEng/S11_RAG_avanzado/Citacion%20y%20Atribucion%20verificable.md) · [S10 · Multi-índice y routing](../../../../Documentos/Sesiones%20Master%20AIEng/S10_Tecnicas_Recuperacion/Multi-indice%20y%20routing.md) · [S11 · Reindexación y versionado de embeddings](../../../../Documentos/Sesiones%20Master%20AIEng/S11_RAG_avanzado/Reindexacion%20y%20Versionado%20Embeddings.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-06 | Sergio Valdueza | Creación del ticket a partir de la sesión de exploración de C23 y de sus mediciones. Catorce decisiones cerradas; el alcance sube de los 15 documentos del corte pre-autorizado a 32, porque el corte se expresó en documentos y el objetivo del diseño está en chunks (150-250) |
| 2026-09-06 | Sergio Valdueza | Artefactos generados con `/opsx:ff`. Las cuatro preguntas abiertas se resuelven con su opción por defecto, y se cierra la única que quedaba viva: **D16 fija la convención de talla de anillo** —tres tallas españolas enteras por letra, `XXS` y `XXL` por encargo, aritmética `general` y asignación `establecimiento`—. `tallas-anillos` pasa de 5 a 7 secciones y el corpus de ~159 a **~161**; entra un requisito de coherencia de la tabla en la spec y cuatro tests que la comprueban, incluido el que verifica que los límites de ajuste dicen lo mismo en la tabla, en las fichas de material y en la política de reparaciones |
