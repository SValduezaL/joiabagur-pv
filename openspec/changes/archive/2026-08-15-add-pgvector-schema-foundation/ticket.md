# T-AIENG-005: pgvector schema foundation — `ai` schema, Alembic migrations and bounded pool (C05)

> Ticket técnico del change OpenSpec `add-pgvector-schema-foundation`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, `Documentos/` (diseño RAG, plan de changes y apuntes del Máster S8), specs vivas de `openspec/specs/`, el contrato congelado `ai-service/openapi.json` y [HU-AIENG-005](../../../../Documentos/Historias/AI-Eng/HU-AIENG-005.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-005 / C05** — Extensión `vector`, esquema `ai`, rol dedicado, andamiaje Alembic, migración inicial de seis tablas con sus índices, y motor asíncrono con pool acotado a 5 conexiones

---

## Contexto y Problema

Cerrada la Ola 0 con C01–C04, el servicio `jbg-ai` arranca, tiene su contrato congelado y el backend .NET sabe hablar con él — pero **el servicio no tiene memoria**. No hay una sola línea de código de base de datos en `ai-service/`: ni dependencia, ni migración, ni motor, ni esquema. Todo lo que el servicio devuelve hoy sale de fixtures deterministas bajo `STUB_MODE`.

Eso convierte a C05 en el cuello de botella real de la Ola 1. La cadena que sostiene el hito del **19 de agosto** —C11 texto canónico → C13 indexador → C14 recuperación → C15 endpoint .NET → C16 panel— arranca en C11, y C11 no puede escribir un `source_hash` en ninguna parte mientras `ai.product_document` no exista. C05 es además el único change de la ola que puede empezar hoy: su único prerrequisito, C01, está archivado.

El segundo problema es de naturaleza distinta y es el que gobierna el diseño de los tests. **Los errores caros de este change no producen ningún error.** Los apuntes del Máster S8 lo dicen del caso principal sin rodeos: crear el índice HNSW con una *operator class* que no coincide con el operador de la consulta hace que *«Postgres no emita ningún error ni warning; la query funciona y devuelve resultados»*, cayendo a *sequential scan* en silencio. Sobre los ~1.500 vectores del proyecto ni siquiera se notaría en latencia, así que el fallo llegaría intacto a la defensa del proyecto. La misma familia de fallo mudo incluye la tabla de versiones de Alembic naciendo en `public` (violando la frontera del diseño §6.3 en la primera migración del lado Python), un tipo `ENUM` sobreviviendo al `downgrade` y rompiendo el siguiente `upgrade` semanas después, y una `tsvector` construida con la configuración por defecto en lugar de la española.

Hay un tercer problema, de compatibilidad hacia atrás. La spec viva `ai-service-dev-compose` afirma que *«el arranque de `jbg-ai` no debe requerir conexión a base de datos»* y que *«las ejecuciones locales no necesitan proveedor de IA ni base de datos»*. Introducir `DATABASE_URL` como ajuste obligatorio convertiría en falso un escenario ya aceptado y archivado, y dejaría sin arrancar el servicio de Compose, que hoy no la define.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `ai-service/migrations/`, `alembic.ini` | **Ausentes.** No existe ningún árbol de migraciones de Python |
| Dependencias de base de datos en `ai-service/pyproject.toml` | **Ninguna.** Runtime: `fastapi`, `pydantic-settings`, `pyjwt`, `uvicorn`. Dev: `httpx`, `pytest` |
| `DATABASE_URL` o cualquier ajuste de base de datos en `config/settings.py` | **Ausente.** Los ajustes son `app_env`, `service_version`, `log_level`, `jwt_secret`, `jwt_ttl_seconds`, `stub_mode`, `enable_dev_endpoints` |
| Marcador `db` de pytest | **Ya declarado** en `pyproject.toml`: *«needs a PostgreSQL instance with pgvector»* — C01 lo dejó preparado |
| Carpeta `ai-service/tests/migrations/` | **Reservada por nombre** en `tests/README.md` y adjudicada explícitamente a C05; aún no creada (las carpetas se crean bajo demanda) |
| Regla de dónde va el fixture de base de datos | **Ya escrita** en `tests/README.md`: *«a database fixture belongs to `migrations/conftest.py`, not to the global one»* |
| Imagen de PostgreSQL en Compose | **`pgvector/pgvector:pg15`** en `backend/docker-compose.yml`, con el comentario *«Do NOT create schema `ai` or run CREATE EXTENSION here — that is C05»* |
| Servicio `jbg-ai` en Compose | Existe, con `APP_ENV`, `SERVICE_VERSION`, `LOG_LEVEL`, `JWT_SECRET`, `STUB_MODE`. **Sin `DATABASE_URL` y sin `depends_on`** |
| `backend/scripts/init.sql` | Existe y está montado en `docker-entrypoint-initdb.d`, pero **solo emite un `RAISE NOTICE`**. Se ejecuta únicamente sobre volumen nuevo |
| Disponibilidad de `vector` en RDS | **Resuelta en C01:** PostgreSQL 15.17, riesgo cerrado en su `design.md`. La ejecución real sobre RDS es de C17 |
| `ai-service/Dockerfile` | Copia **solo** `pyproject.toml`, `uv.lock`, `README.md` y `src`. Un árbol `migrations/` no llegaría al contenedor |
| `ai-service/openapi.json` | Congelado, 8 rutas `/v1` más `/health`, protegido por `test_openapi_snapshot_is_stable`. **Este change no lo toca** |
| `tests/support/` | Existe con `paths.py`, `settings.py`, `sample_requests.py`. `AI_SERVICE_ROOT` ya se resuelve ahí — **no anclar rutas con `Path(__file__).parents[N]`** |
| `tests/fixtures/` | **Ausente.** Reservada para datos de test; este change no la necesita |
| Flujo de integración continua para Python | **Ninguno.** Existen `test-backend.yml` y `test-frontend.yml`; nada ejecuta `uv run pytest` |
| `SchemaAssert` de C04 (`information_schema` / `pg_indexes`) | Existe, pero es **C# sobre Testcontainers .NET**: no es reutilizable desde Python. Sí es reutilizable su **criterio** |
| Artefactos OpenSpec de este change | Andamiaje creado (`.openspec.yaml`); proposal, design, specs y tasks **a generar** desde esta HU y este ticket |

**Impacto en producto:** ninguno visible. El servicio sigue respondiendo exactamente lo mismo que antes del change. El valor es habilitador: C11, C13, C14, C22, C23 y C24 pasan de bloqueados a ejecutables.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/pyproject.toml`, `uv.lock` | `sqlalchemy[asyncio]`, `psycopg[binary,pool]`, `pgvector`, `alembic` en runtime; `testcontainers[postgres]` en dev |
| `ai-service/alembic.ini` | **Nuevo.** Configuración de Alembic, con `script_location` apuntando a `migrations/` |
| `ai-service/migrations/` | **Nuevo.** `env.py`, `script.py.mako`, `bootstrap.sql` y la única revisión del change en `versions/` |
| `ai-service/src/jbg_ai/db/` | **Nuevo.** Motor asíncrono perezoso con pool acotado y fábrica de sesiones |
| `ai-service/src/jbg_ai/config/settings.py` | `database_url` y `db_pool_size`, **ambos opcionales** |
| `ai-service/tests/migrations/` | **Nuevo.** `conftest.py` con contenedor efímero y base por test, más los cuatro detectores |
| `ai-service/Dockerfile` | Copiar `alembic.ini` y `migrations/` para que C17 pueda migrar desde el contenedor |
| `backend/docker-compose.yml` | `DATABASE_URL` en el servicio `jbg-ai`, apuntando al servicio `postgres` de la red interna |
| `ai-service/README.md` | Variables nuevas, secuencia de preparación previa, cómo migrar y cómo ejecutar los tests de base de datos |
| `openspec/` | Capability nueva `ai-vector-schema`; modificaciones en `ai-service-runtime` y `ai-service-dev-compose` |
| `Documentos/` | HU-AIENG-005, `modelo-de-datos.md` (esquema `ai`), `epicas.md` (EP11) |
| `backend/`, `frontend/`, `terraform/` | **Sin cambios** |

---

## Especificaciones Técnicas

### Preparación previa (`migrations/bootstrap.sql`) — fuera de Alembic

Ejecutado **una sola vez y con privilegios de administrador**. Los roles son objetos de clúster, no de base de datos: crearlos desde una migración exigiría privilegio de creación de roles a quien migra y haría fallar el `downgrade` si el rol ya posee objetos.

| Sentencia | Nota |
|---|---|
| `CREATE EXTENSION IF NOT EXISTS vector` | En `public`, el destino por defecto. En RDS lo ejecuta el usuario maestro; en local, `postgres` |
| `CREATE SCHEMA IF NOT EXISTS ai` | Propiedad de Python |
| `CREATE ROLE` del usuario dedicado, con `LOGIN` | Contraseña por parámetro; en producción sale de SSM `/jpv/prod/*` (C17) |
| `GRANT USAGE, CREATE ON SCHEMA ai` al rol | `CREATE` porque ese mismo rol ejecuta las migraciones |
| `GRANT USAGE ON SCHEMA public` al rol | Solo para **resolver el tipo `vector`**. Sin `SELECT` sobre ninguna tabla: la frontera §6.3 se mantiene |

La consecuencia de este reparto es que **basta una sola cadena de conexión**: `CREATE EXTENSION IF NOT EXISTS` es no-op cuando el administrador ya la instaló (camino de RDS) y funciona tal cual cuando se migra como superusuario (camino local). No hacen falta `DATABASE_URL` y `DATABASE_ADMIN_URL` separadas.

### Andamiaje de Alembic

| Aspecto | Decisión |
|---|---|
| `version_table_schema` | **`ai`**. El valor por defecto crearía `public.alembic_version` y violaría la frontera en la primera migración |
| Creación previa del esquema | En `env.py`, **antes** de ejecutar las revisiones. Alembic materializa su tabla de versiones antes del primer script, así que un `CREATE SCHEMA` dentro de `upgrade()` llega tarde |
| Idempotencia | `env.py` y la migración declaran esquema y extensión con `IF NOT EXISTS`, de modo que el SQL de la revisión siga siendo autodescriptivo sin romper el arranque |
| Driver y URL | **psycopg 3**, `postgresql+psycopg://`. Sync para Alembic y async para la aplicación con **un solo esquema de URL** |
| Autogenerate | **No se usa.** No expresa *operator classes* de HNSW, GIN sobre `text[]` ni columnas generadas. La revisión se escribe a mano |
| Modelos ORM | **Ninguno en este change.** El acceso tipado nace en C11/C13 cuando conozcan su forma |

### Migración inicial — seis tablas en el esquema `ai`

Convención: `snake_case`, frente al `PascalCase` entrecomillado que EF Core usa en `public`. Los dos esquemas conviven en la misma base de datos y **no comparten convención a propósito**.

**`ai.product_document`** — una fila por producto, sin *chunking* (diseño §7.2)

| Columna | Tipo | Null | Notas |
|---|---|---|---|
| `product_id` | `uuid` PK | no | Identificador de .NET. **Sin clave foránea hacia `public`** |
| `sku`, `name`, `collection_name` | `text` | `collection_name` sí | |
| `price` | `numeric(10,2)` | sí | Copia para banda y ordenación; la cifra autoritativa la pone .NET |
| `price_band` | `text` + `CHECK` | sí | Vocabulario cerrado, no `ENUM` |
| `piece_type`, `stone_type`, `size_label` | `text` | sí | |
| `materials` | `text[]` | no | `DEFAULT '{}'`. Filtro por solape (`&&`) y contención (`@>`), §7.3 |
| `family_id` | `uuid` | sí | Sin FK: la familia vive en .NET (C07) |
| `family_name`, `variant_label` | `text` | sí | |
| `color_tags`, `style_tags`, `occasion_tags` | `text[]` | no | `DEFAULT '{}'` |
| `doc_text` | `text` | no | `SourceText` canónico que construye C11 |
| `source_hash` | `char(64)` | no | SHA-256; gobierna si se recalcula el embedding |
| `embedding` | `vector(1536)` | **sí** | Nulable a propósito: permite insertar la fila antes de calcular el embedding |
| `tsv` | `tsvector` **generada** | — | `GENERATED ALWAYS AS (to_tsvector('spanish', doc_text)) STORED` |
| `is_active` | `boolean` | no | `DEFAULT true` |
| `data_origin` | `text` + `CHECK (real\|synthetic)` | no | Toda métrica se reporta desglosada por este campo (§8.1.1) |
| `embedding_model`, `embedding_version` | `text` | sí | Cambiar de modelo va en **columna nueva**, nunca sobrescribiendo (§6.3) |
| `indexed_at` | `timestamptz` | sí | |

**`ai.knowledge_document`** — `id uuid` PK, `doc_type text` + `CHECK` (`material|talla|guion_venta|politica|faq`), `title`, `source_ref`, `created_at timestamptz`.

**`ai.knowledge_chunk`** — `id uuid` PK, `document_id uuid` **FK hacia `ai.knowledge_document` con `ON DELETE CASCADE`** (intra-esquema, legítima y recomendada por S8), `chunk_index int`, `content text`, `metadata jsonb DEFAULT '{}'`, `embedding vector(1536)` nulable, `tsv` generada sobre `content` con `'spanish'`.

**`ai.pos_projection`** — PK compuesta `(pos_id, product_id)`, `is_assigned_hint boolean`, `qty_bucket text` + `CHECK (0|1-2|3+)`, `sales_30d int`, `sales_90d int`, `last_sale_at timestamptz`, `refreshed_at timestamptz`. **Bucket, nunca cantidad exacta** (§7.2): guardar el número real invitaría a mostrarlo y la proyección puede estar desfasada.

**`ai.co_occurrence`** — PK `(product_a, product_b)` más **`CHECK (product_a < product_b)`**, `co_sales_count int`, `last_seen_at timestamptz`. Sin la restricción de orientación cada par se almacena dos veces y C27 dobla su señal.

**`ai.sync_failure`** — `id bigserial` PK, `feed text`, `cursor_since timestamptz`, `payload jsonb`, `error text`, `attempts int`, `next_retry_at timestamptz`, `created_at timestamptz`.

### Índices — catorce declarados, más las seis claves primarias

| Tabla | Índice | Motivo |
|---|---|---|
| `product_document` | **HNSW** `(embedding vector_cosine_ops)` `WITH (m = 16, ef_construction = 128)` | S8: `ef_construction` explícito, 128 en lugar del 64 por defecto de pgvector, para 1536 dimensiones |
| `product_document` | GIN `(tsv)` | Rama léxica de C21 |
| `product_document` | GIN `(materials)` | Solape y contención del §7.3 |
| `product_document` | B-tree `family_id`, `piece_type`, `price_band`, `data_origin` | Filtros estructurales del §7.2 y desglose de métricas por origen |
| `knowledge_document` | B-tree `(doc_type)` | Enrutado por tipo de documento (C23, C30) |
| `knowledge_chunk` | **HNSW** `(embedding vector_cosine_ops)`, mismos parámetros | Segundo índice vectorial |
| `knowledge_chunk` | GIN `(tsv)`, GIN `(metadata)` | El GIN sobre `metadata` lo pide §7.2 y lo justifica S8 |
| `knowledge_chunk` | UNIQUE `(document_id, chunk_index)` | Invariante de *chunking*; sirve también la búsqueda por documento |
| `pos_projection` | B-tree `(product_id)` | Búsqueda inversa producto → POS |
| `sync_failure` | B-tree `(next_retry_at)` | Cola de reintentos con backoff de C13 |

`CONCURRENTLY` **no** se usa: S8 lo declara obligatorio en producción para no bloquear escrituras durante la construcción, pero aquí las seis tablas nacen vacías y el índice se construye de forma instantánea. Además `CREATE INDEX CONCURRENTLY` no puede ejecutarse dentro de la transacción en la que Alembic envuelve la revisión.

### `downgrade`

Borra **las seis tablas y nada más**. La extensión es un objeto compartido de la base de datos y el esquema `ai` alberga la propia tabla de versiones de Alembic: borrarlo dejaría a Alembic sin dónde registrar el resultado de la operación que está ejecutando. Al no haber ningún tipo `ENUM`, no queda nada huérfano que limpiar — que es precisamente el motivo de la decisión `text` + `CHECK`.

### Motor y pool

| Aspecto | Valor | Motivo |
|---|---|---|
| `pool_size` | `5` | «Acotado a 5» en su lectura literal; `openspec/project.md` fija *máx. 5-10 conexiones*, compartidas con .NET sobre el mismo RDS |
| `max_overflow` | `0` | Con desbordamiento, el tope de 5 sería decorativo |
| `pool_timeout` | Muy por debajo de los 30 s por defecto | .NET corta la recuperación a 0,8 s con Polly: esperar más es trabajar para un cliente que ya se marchó |
| `pool_pre_ping` | Activado | RDS cierra conexiones ociosas |
| Creación | **Perezosa** | Importar el módulo no puede abrir conexiones, o el arranque sin base de datos dejaría de funcionar |
| Sin `DATABASE_URL` | Error claro **al pedir sesión**, no al arrancar | Preserva el escenario aceptado de `ai-service-dev-compose` |

### Configuración

| Variable | Requerida | Defecto | Nota |
|---|---|---|---|
| `DATABASE_URL` | **no** | ausente | `postgresql+psycopg://…`. Su ausencia no impide arrancar |
| `DB_POOL_SIZE` | no | `5` | Tope efectivo de conexiones simultáneas |

En Compose apunta al servicio `postgres` por nombre de red y **puerto interno 5432**, no al 5433 publicado en el host. Sin `depends_on`: el motor es perezoso y en `STUB_MODE` nadie lo invoca.

### Tests — cuatro detectores de fallo mudo

Nomenclatura Python del plan (`test_<unidad>_<escenario>_<esperado>`), en `ai-service/tests/migrations/`, marcados con `@pytest.mark.db`.

| Test | Qué fallo mudo caza |
|---|---|
| `test_migration_creates_vector_extension_and_ai_schema` | Que la migración aplique pero deje la extensión o el esquema sin crear |
| `test_hnsw_index_uses_cosine_operator_class` | **El antipatrón de S8.** *Operator class* `vector_l2_ops` con consultas `<=>`: índice desactivado, sin error |
| `test_gin_index_exists_on_materials` | Filtro por solape del §7.3 degradado a recorrido secuencial |
| `test_upgrade_downgrade_is_reversible` | Objetos huérfanos tras revertir, que rompen el siguiente `upgrade` semanas después |

Dos precisiones de método:

- **Cómo se afirma la *operator class*.** Join al catálogo (`pg_index` → `pg_opclass` → `pg_am`), afirmando `opcname = 'vector_cosine_ops'` y `amname = 'hnsw'`. Buscar la cadena en `pg_indexes.indexdef` también funcionaría —PostgreSQL **omite la *operator class* cuando es la de por defecto**, así que un índice L2 se renderiza como `USING hnsw (embedding)` y la comprobación fallaría— pero depende de una regla de renderizado en lugar de un hecho del catálogo.
- **Tercera pierna de la reversibilidad.** `upgrade` → `downgrade` → **`upgrade` otra vez**. Sin la tercera, un objeto huérfano pasa desapercibido, que es exactamente lo que el test existe para detectar.

**Arnés.** Contenedor efímero `pgvector/pgvector:pg15` de ámbito de sesión, y **una base de datos nueva por test**: el test de reversibilidad muta el esquema y compartir base lo haría dependiente del orden — el patrón que `CLAUDE.md` documenta como veneno en la suite de .NET. Sin Docker accesible, los tests se **omiten con motivo legible**: no hay integración continua para Python y unos rojos permanentes en local enseñarían a ignorar el rojo.

**Verificación del propio arnés.** Como en C04, tarea explícita de romper a propósito lo que cada detector vigila —empezando por sustituir `vector_cosine_ops` por `vector_l2_ops`—, comprobar que el test **falla**, y revertir.

### Fuera de alcance técnico

Ni `SELECT` ni `<=>` en código de aplicación (C14); ni una fila insertada (C13, C22, C23); sin modelos ORM ni repositorios; sin `ai.eval_*` (C24); sin `/health` enriquecido ni ejecución sobre RDS (C17); sin `halfvec`, `hnsw.iterative_scan`, `CONCURRENTLY`, `REINDEX` ni tuning de `shared_buffers` / `maintenance_work_mem`; y **sin tocar routers, modelos Pydantic ni `openapi.json`**.

---

## Arquitectura

**Frontera de propiedad (diseño §6.3).** `public.*` es de .NET; `ai.*` es de Python; **Python nunca escribe en `public` ni lo lee por SQL**. Este change es la primera vez que esa frontera se materializa en objetos reales, y de ahí salen tres de sus decisiones: la tabla de versiones de Alembic en `ai`, la ausencia de claves foráneas cruzadas, y el `GRANT USAGE ON SCHEMA public` reducido a resolver el tipo `vector` sin `SELECT` sobre ninguna tabla.

**La excepción declarada.** La extensión se instala en `public`, su destino por defecto. `CREATE EXTENSION vector SCHEMA ai` sería más purista pero obligaría a cualificar el tipo como `ai.vector(1536)` y a manipular el `search_path` en cada conexión, para siempre. La regla de propiedad habla de **datos**, no de instalación de extensiones.

**Por qué HNSW y no IVFFlat.** No es preferencia: IVFFlat necesita entrenamiento k-means sobre datos existentes y **no puede construirse sobre una tabla vacía**, mientras que HNSW absorbe inserciones de forma incremental. Que las seis tablas nazcan vacías con sus índices puestos —el enunciado literal de la ficha C05— solo es posible con HNSW. S8 añade el argumento de operación: IVFFlat degrada su recall en silencio a medida que la distribución se aleja de los centroides originales, y este corpus crece con cada sincronización.

**Decisiones previas que se heredan.** C01 fijó una sola instancia de RDS con separación por esquema en lugar de una segunda base de datos, y adoptó la imagen pgvector dejando la extensión explícitamente para C05. C04 fijó el criterio de qué merece un test de esquema: *«el valor está entero en las propiedades que están mal sin producir ningún error»*. Este change aplica ese criterio en Python, sin reutilizar el código C# de `SchemaAssert`, que no cruza de lenguaje.

**Patrones en uso.** Configuración por `pydantic-settings` con fallo temprano, ya establecida en C01/C02 — con la salvedad de que los dos ajustes nuevos son **opcionales** por compatibilidad hacia atrás. Motor y sesión perezosos, para no convertir un módulo importado en una conexión abierta.

**Breaking changes.** Ninguno. No cambia ningún contrato REST, ni el snapshot OpenAPI, ni el comportamiento observable del servicio. El único cambio de infraestructura es la variable nueva en Compose, que es aditiva y opcional. La preparación previa sobre RDS de producción no se ejecuta aquí: es de C17.

---

## Definición de Hecho (DoD)

- [ ] Migración aplicable y reversible sobre PostgreSQL 15 con pgvector, verificada con las tres piernas (`upgrade` → `downgrade` → `upgrade`)
- [ ] Las seis tablas existen en el esquema `ai`, vacías, con los catorce índices declarados y las seis claves primarias
- [ ] Ningún objeto creado fuera del esquema `ai`, salvo la extensión `vector` en `public`, que es la excepción declarada
- [ ] `ai-service`: `uv run pytest` en verde, sin llamadas reales a LLM, embeddings ni RDS de producción; los cuatro tests de migración pasan con Docker disponible y se **omiten con motivo** sin él
- [ ] Cada detector verificado rompiendo a propósito lo que vigila y comprobando que falla, con la rotura revertida
- [ ] `test_openapi_snapshot_is_stable` en verde y `ai-service/openapi.json` **sin cambios** — si se pone rojo, el change se ha salido de su alcance
- [ ] El servicio arranca y sirve `GET /health` y las rutas `/v1` **sin `DATABASE_URL` definida**
- [ ] `docker compose up jbg-ai` arranca sin configuración extra, como antes del change
- [ ] `alembic.ini` y `migrations/` presentes en la imagen, verificado ejecutando la migración desde el contenedor
- [ ] Spec de la capability en `openspec/changes/add-pgvector-schema-foundation/specs/` y **`openspec validate --all --strict` con `0 failed`**
- [ ] Documentación actualizada: `ai-service/README.md`, `Documentos/modelo-de-datos.md` y `Documentos/epicas.md` (EP11)
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] Migración de EF Core: **no aplica** — este change no toca el modelo de .NET

---

## Requisitos No Funcionales

- **Seguridad:** rol de base de datos dedicado con el permiso mínimo (`USAGE, CREATE` sobre `ai`; `USAGE` sobre `public` solo para resolver el tipo `vector`, sin `SELECT` sobre tabla alguna). Credenciales nunca en el repositorio: placeholder de desarrollo en Compose, y SSM `/jpv/prod/*` en producción (C17). La preparación previa exige privilegios de administrador y se ejecuta a mano, una sola vez.
- **Rendimiento y free-tier:** pool de 5 conexiones sin desbordamiento, dentro del presupuesto de 5-10 que `openspec/project.md` fija para el conjunto del sistema. Espera por conexión recortada muy por debajo del presupuesto de 0,8 s que .NET concede a la recuperación. Índices dimensionados para ~1.500 vectores: el diseño §7.2 ya declara que a esta escala pgvector es holgado y que la elección se justifica por operación, no por escala.
- **Observabilidad:** sin cambios en el `trace_id` ni en el logging estructurado de C01. El `/health` enriquecido con estado de base de datos es de C17. Los apuntes S8 señalan `pg_stat_user_indexes.idx_scan` como la forma más rápida de detectar en producción el antipatrón de la *operator class*; queda anotado como práctica para C17, no como código de este change.
- **Integridad de datos:** vocabularios cerrados por `CHECK`, orientación única de los pares de co-ocurrencia, unicidad de `(document_id, chunk_index)`, `ON DELETE CASCADE` dentro del esquema y **ninguna clave foránea cruzada** que acople `ai` al ciclo de vida de las tablas de EF Core. `qty_bucket` almacena bucket y no cantidad, para que la proyección desfasada no pueda mostrarse como dato.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | **`ai.query_log`** aparece en el diseño §7.2 pero **ninguna ficha del plan la adjudica** (las de evaluación son de C24; esta no es de nadie). ¿Entra aquí? | **No se crea.** Una segunda migración Alembic es barata —no hay regla de migración única en Python—, así que el coste de posponerla es bajo y el de adivinar sus columnas hoy no lo es. Queda anotada para que no se cuele improvisada en C14 |
| 2 | ¿Índice **único sobre `sku`** en `product_document`? C06 garantiza unicidad en el generador, pero el índice la haría infalsificable | **No se crea.** La unicidad es del corpus, y C13 hace *upsert* por `product_id`. Añadirlo después es una migración de una línea |
| 3 | Valores concretos del vocabulario de **`price_band`** | `CHECK` declarado con las bandas que fije C09 al calcularlas; hasta entonces, columna nulable con `CHECK` permisivo antes que un vocabulario inventado hoy |
| 4 | ¿Se añade un flujo **`test-ai-service.yml`** de integración continua? | **Fuera de alcance.** Ninguna ficha del plan lo adjudica; se recoge como observación. Mientras no exista, los tests de base de datos se omiten con motivo en lugar de fallar |
| 5 | ¿Se ejecuta la preparación previa contra el **RDS de producción** en este change? | **No.** Es alcance explícito de C17, junto con el despliegue del contenedor y los secretos en SSM |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** — 🔴 ruta crítica. Primer change desbloqueado de la Ola 1 y único prerrequisito de C11, del que cuelga la cadena hasta el hito del 19 de agosto.
- **Estimación:** **5 SP** *(pendiente de validar en refinamiento)*. Sin algoritmo ni lógica de negocio, pero es la primera capa de datos en Python del proyecto: cinco dependencias, andamiaje de migraciones, arnés con contenedor y seis tablas con catorce índices, cada uno con una decisión detrás.
- **Dependencias:** C01 (archivado). **No compite** por el turno de migración de EF Core: Alembic es un árbol independiente, así que C05 puede convivir con C04, C07, C08, C19, C27 o C29.
- **Línea de corte:** si la sesión se desborda, primero **andamiaje + preparación previa + migración + arnés + los cuatro tests** (mitad archivable por sí sola); después **motor + configuración + Compose + documentación**. C11 necesita el esquema mucho antes que el motor, y además espera a C09.
- **Tags:** `HU-AIENG-005`, `C05`, `EP11`, `ai-service`, `python`, `alembic`, `pgvector`, `hnsw`, `migration`, `database`, `critical-path`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-005](../../../../Documentos/Historias/AI-Eng/HU-AIENG-005.md)
- **Change OpenSpec:** `openspec/changes/add-pgvector-schema-foundation/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C05, reglas transversales de testing) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.3, §7.2, §7.3, §7.6)
- **Apuntes del Máster (S8):** [Anatomía de un índice vectorial](../../../../Documentos/Sesiones%20Master%20AIEng/S8_BBDD_Vectoriales/Anatomia%20de%20un%20Indice%20Vectorial%20HNSW,%20IVFFlat%20y%20el%20horizonte%20DiskANN.md) · [Diseño del esquema y búsqueda semántica](../../../../Documentos/Sesiones%20Master%20AIEng/S8_BBDD_Vectoriales/Dise%C3%B1o%20del%20esquema%20y%20busqueda%20semantica.md) · [Del prototipo a producción](../../../../Documentos/Sesiones%20Master%20AIEng/S8_BBDD_Vectoriales/Del%20prototipo%20a%20produccion%20Tuning,%20Monitorizacion%20y%20techo%20PGVector.md)
- **Specs vivas afectadas:** `openspec/specs/ai-service-runtime/spec.md`, `openspec/specs/ai-service-dev-compose/spec.md`
- **Precedentes:** `openspec/changes/archive/2026-08-03-init-ai-service-skeleton/design.md` (una sola RDS, imagen pgvector, riesgo de la extensión) · `openspec/changes/archive/2026-08-11-add-product-search-event-tracking/` (criterio del test de esquema y guardarraíl del arnés)
- **Contrato congelado:** `ai-service/openapi.json` — **se lee, no se modifica**
- **Convenciones de test:** `ai-service/tests/README.md` (carpeta `migrations/`, marcador `db`, fixture local)
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-15 | `/enrich-us` | Creación del ticket a partir de HU-AIENG-005 y de la sesión de exploración previa al proposal. Recoge las once decisiones cerradas en esa sesión y los parámetros HNSW (`m = 16`, `ef_construction = 128`) tomados de los apuntes del Máster S8 |
