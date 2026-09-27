# T-AIENG-017: Isolated demo environment deployment for the AI service (C17)

> Ticket técnico del change OpenSpec `add-ai-service-deployment`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-017](../../../../Documentos/Historias/AI-Eng/HU-AIENG-017.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C17 y §0 de 2026-08-29), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.1, §6.4, §12, §15, §16), sesión de exploración 2026-08-29, código real de `terraform/`, `.github/workflows/`, `ai-service/src/`, `backend/src/` y `frontend/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-017 / C17** — Entorno de demo autocontenido en una cuenta AWS separada: Terraform con estado propio, `compose.demo.yaml` con cuatro servicios tras Caddy, workflow OIDC + ECR + SSM, `/health` enriquecido sin llamar al proveedor, tarjeta de estado para administradores y camino del dato hasta el índice

---

## Contexto y Problema

C15 dejó `POST /api/ai/search` y C16 el panel que lo consume. El sistema completo funciona — **y sólo funciona contra el Docker de un portátil**. El §16 del diseño pide como criterio de entrega *«URL pública con usuario demo y vídeo de 2-3 min»*, y no existe ninguna URL que enseñar.

Al diseñar sobre la infraestructura real aparecen cinco hechos que la ficha v3 no podía conocer.

**Primero: no hay acceso a la cuenta AWS de la tienda.** Y aunque lo hubiera, su RDS es la base de datos real del negocio. La ficha decía *«servicio en producción, alcanzable solo desde el backend»*; lo que C17 puede y debe hacer es levantar un **entorno de demo autocontenido en otra cuenta**, sin una sola arista hacia la de la joyería.

**Segundo: en producción no hay `docker-compose`.** El §12.1 del diseño lo daba por sentado. La realidad de [`user_data.sh`](../../../../terraform/templates/user_data.sh) es `docker run -d --name jpv-api -p 8080:8080` desde un heredoc, y `ec2.tf` declara `lifecycle { ignore_changes = [user_data] }`: editar el fichero no propaga nada, y re-ejecutarlo sobrescribiría la configuración de nginx que certbot ya modificó. En la demo **sí** hay compose, en una instancia nueva donde el repositorio es la fuente de verdad desde el minuto cero.

**Tercero: el dato es el problema, no el despliegue.** Los 1.200 productos, las 38 colecciones, los 12 puntos de venta, las 6.720 filas de inventario, los 1.200 `ProductAiProfile` en `Approved` y los 1.200 `ai.product_document` con sus vectores **no existen fuera de local**. Un despliegue impecable con el índice vacío pasa todos los tests y entrega una URL donde no se encuentra nada. Es la firma de A1 (C04) y de B5 (C16), por tercera vez.

**Cuarto: dos valores mienten sin dar error.** `STUB_MODE=true` devuelve fixtures con apariencia de funcionar. Un `JPV_EMBEDDING_MODEL` distinto del que generó los vectores compara dos espacios vectoriales como si fueran uno: ruido, con `200` y sin traza.

**Quinto: el `/health` que pedía la ficha es el que S15 y S16 desaconsejan.** *«Si dependiera de que el proveedor de LLM responda […] un sistema que se autodestruye cada vez que el LLM tose»* y *«no confundáis el latido con la vigilancia»*.

**Estado actual del código (verificado 2026-08-29 en repo):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-ai-service-deployment` | **Scaffold** (`.openspec.yaml`, schema `spec-driven`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| Rama de trabajo | `c17-add-ai-service-deployment`, creada desde `ai-eng` en `5e377f1` |
| `terraform/` | Un solo estado, para la cuenta de la tienda: `ec2.tf`, `rds.tf`, `ecr.tf` (**un** repo, `jpv-backend`), `iam.tf`, `ssm.tf`, `s3.tf`. **Sin acceso a esa cuenta** |
| `terraform/ec2.tf` | `t3.micro` por defecto, disco gp3 de 30 GiB, **`ignore_changes = [user_data]`**, AMI por `var.ami_id` con nota de «actualízala antes de aplicar» |
| `terraform/iam.tf` | `ECRPush` acotado a `aws_ecr_repository.api.arn`; OIDC con `sub` = `repo:<org>/<repo>:*` (**cualquier rama**); lectura SSM en `parameter/jpv/prod/*` |
| `terraform/templates/user_data.sh` | Instala docker, nginx y certbot **en el host**; escribe `/etc/nginx/conf.d/jpv.conf` y `/usr/local/bin/jpv-deploy.sh` por heredoc; el script inyecta **7 variables fijas**, ninguna `AiGateway__*` ni `IndexFeed__*`, y hace `docker run` **sin `--network`** |
| `.github/workflows/` | `deploy-aws-ec2.yml` (activo, OIDC + ECR + SSM), `deploy-backend-aws.yml` y `deploy-frontend-aws.yml` (**deprecados**, `workflow_dispatch`), `test-backend.yml`, `test-frontend.yml` |
| `ai-service/Dockerfile` | Una etapa; **corre como root**; `COPY --from=ghcr.io/astral-sh/uv:latest` (**sin fijar versión**); **sin `HEALTHCHECK`**; migraciones copiadas tras `uv sync` con comentario que cita C17 |
| `backend/.../Dockerfile.bundled` | **Producción.** Multietapa, no-root, `HEALTHCHECK`, `ARG VITE_API_BASE_URL` horneado en build |
| `backend/.../Dockerfile` · `Dockerfile.prod` | **Muertos.** `Dockerfile.prod` sólo lo usa `deploy-backend-aws.yml` (deprecado); `Dockerfile` sólo `backend/docker-compose.prod.yml` (no lo invoca nada) |
| `backend/docker-compose.prod.yml` | **Camino obsoleto.** Construye desde fuente y declara un Postgres propio cuando producción usa RDS. `backend/README.md` lo documenta como «Production Deployment › Docker». **Deuda asignada a C17 por el ticket de C03** |
| `.dockerignore` en la raíz | **No existe.** Contexto de build de `Dockerfile.bundled` ≈ **1 GB**: 711 MB `node_modules`, 265 MB `.venv`, 36 MB `.git`, 30 MB `data/` |
| `backend/docker-compose.yml` | Local: `postgres` (`pgvector/pgvector:pg15`, `:5433`), `pgadmin`, `jbg-ai` (`:8001`), red `jpv-network`. **La spec viva `ai-service-dev-compose` fija su ruta y su red literalmente en dos requirements** |
| `ai-service/.../api/main.py` → `/health` | `{"status": "OK", "version": ...}`, retorno `dict[str, Any]`, `tags=["health"]`, «Public liveness probe». **Sin BD, sin índice, sin proveedor** |
| `ai-service/openapi.json` | `/health` presente con schema `{additionalProperties: true, type: object}`. **Enriquecer el payload no lo mueve; un modelo Pydantic o una ruta nueva sí** |
| `Settings` (`config/settings.py`) | `app_env`, `service_version`, `jwt_secret` obligatorios; `database_url`, `jpv_embedding_*`, `jpv_index_feed_*`, `jpv_retrieval_distance_threshold`, `stub_mode`, `enable_dev_endpoints` (se apaga solo con `APP_ENV` = `prod`/`production`) |
| `ai.product_document` | Columnas **`embedding_model`** y **`embedding_version`** por fila (migración `f46c55c056e2`). Índice HNSW, tsv y materiales |
| `ai-service/migrations/bootstrap.sql` | Uno-off con privilegios de administrador: `CREATE EXTENSION vector`, esquema `ai`, rol `jbg_ai` con mínimo privilegio. Su cabecera **ya cita C17** |
| `IAiGatewayClient` | **Dos métodos**: `SearchAsync`, `EnrichAsync`. Documentado que cada endpoint lo añade el change que primero lo llama |
| `AiGatewayOptions` | `BaseUrl`, `JwtSecret`, `RetrievalTimeoutMs = 2500` (**temporal de C16**), breaker con `BreakerFailureRatio`, etc. Su XMLdoc **ya dice que C17 debe crear la red de usuario** |
| `appsettings.json` | Comentarios que anticipan `AiGateway__BaseUrl`, `AiGateway__JwtSecret` e `IndexFeed__ApiKey` desde el almacén, «(C17)» |
| `HealthController` (.NET) | `api/health` y `api/health/detailed`, anónimos, estáticos. **No consulta a `jbg-ai`** |
| `DashboardController` · `AdminDashboard.tsx` | `api/dashboard/stats`, `low-stock`; AdminDashboard de 519 líneas con `Card`, `Table`, `recharts`. **Sin tarjeta de estado de servicios** |
| `frontend/src/services/api.service.ts` · `lib/image-url.ts` | `VITE_API_BASE_URL` con `/api`. **Verificado que `/api` relativo funciona**: `getImageUrl` reduce la base a cadena vacía y devuelve rutas de mismo origen |
| Corpus local | `"Products"` 1.200, `"Collections"` 38, `ProductAiProfiles` 1.200 `Approved`, `ai.product_document` ~1.200 con vectores. **Todo «Docker, no RDS»** |
| Migraciones EF | Seis previstas (C04, C07, C08, C19, C27, C29). C17 **no abre una séptima** |

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `terraform/demo/` | **Nuevo, con estado propio.** OIDC (`resource`, cuenta virgen), rol acotado a `environment:demo`, EC2 `jbg-demo-host`, SG sólo 80/443, IP elástica, dos repos ECR con ciclo de vida, parámetros `/jbg-demo/*`, AMI por `data "aws_ssm_parameter"` |
| `terraform/demo/templates/user_data.sh` | **Nuevo.** Cuatro pasos, sin nada de la aplicación. Plugin de Compose por binario **con versión fijada** |
| `compose.demo.yaml` (raíz) | **Nuevo.** `jbg-demo-proxy` (único con `ports:`), `jbg-demo-api`, `jbg-demo-ai`, `jbg-demo-postgres`. Volúmenes `jbg-demo-pgdata` / `-caddy-data` / `-caddy-config`, red `jbg-demo-net`, `mem_limit` en el servicio de IA |
| `deploy/demo/Caddyfile` | **Nuevo.** Parametrizado por `${DEMO_HOSTNAME}` |
| `deploy/demo/deploy.sh` | **Nuevo.** Lee SSM al entorno del proceso, valida con `:?`, **sin `set -x`**, `up -d` y **jamás `down -v`**, más llamada de calentamiento |
| `deploy/demo/README.md` | **Nuevo.** Runbook: alta de la cuenta, `bootstrap.sql`, volcado y restauración, cuentas de demo, migración del hostname |
| `.github/workflows/deploy-demo.yml` | **Nuevo.** Rama `demo` + `workflow_dispatch`; build de las dos imágenes; despliegue y smoke por `aws ssm send-command` + `docker exec` |
| `.dockerignore` (raíz) | **Nuevo.** Recorta ~1 GB de contexto |
| `backend/.../Dockerfile.demo` | **Nuevo e independiente.** `VITE_API_BASE_URL=/api` por defecto. **`Dockerfile.bundled` no se toca** |
| `ai-service/Dockerfile` | **Endurecido:** multietapa, usuario no-root, `uv` con versión fijada, `HEALTHCHECK` sin instalar `curl` |
| `ai-service/.../api/main.py` | `/health` enriquecido en el sitio, cacheado, **retorno `dict[str, Any]` intacto** |
| `ai-service/.../api/health_report.py` (o equivalente) | **Nuevo.** Sondas de BD, índice y `provider: configured\|missing`, con contraste de `embedding_model` |
| `backend/.../Controllers/AiHealthController.cs` | **Nuevo.** `api/ai/health`, `[Authorize(Roles = "Administrator")]` |
| `backend/.../Interfaces/IAiGatewayClient.cs` · `Services/AiGatewayClient.cs` | `HealthAsync`, **fuera del circuit breaker** (cliente con nombre propio) |
| `backend/.../DTOs/Ai/` | DTO de la respuesta de salud |
| `frontend/src/pages/dashboard/AdminDashboard.tsx` | Tarjeta de estado del servicio de IA |
| `frontend/src/services/` · `types/` | Servicio y tipos de la tarjeta |
| `backend/.../Dockerfile` · `Dockerfile.prod` · `backend/docker-compose.prod.yml` | **Cabecera de deprecado** |
| `backend/README.md` | Corregir «Production Deployment › Docker» |
| `openspec/changes/add-ai-service-deployment/` | proposal, **design.md**, specs, tasks |
| `openspec/DEFERRED_TASKS.md` | Bifurcación del `/health` y medición del presupuesto en la demo |
| `Documentos/epicas.md` (EP11) | Enlazar HU-AIENG-017 (**en el apply**) |
| **Cuenta AWS de la tienda**, `Dockerfile.bundled`, `backend/docker-compose.yml`, `ai-service-dev-compose`, `openapi.json`, migraciones | **Sin cambios** |

---

## Especificaciones Técnicas

### Topología y frontera

```
internet ──443──▶ jbg-demo-proxy (Caddy)  ← ÚNICO servicio con ports:
                        │
        ┌───────────────┴──── red jbg-demo-net ────────────────┐
        │  jbg-demo-api :8080  ⇄  jbg-demo-ai :8000            │
        │         └──────▶ jbg-demo-postgres :5432 ◀───────────┘
        └───────────────────────────────────────────────────────┘
```

`api`, `ai` y `postgres` **no declaran `ports:`**. El SG sólo abre 80/443. La frontera de S15 se cumple en tres capas independientes.

### Clasificación de la configuración

| Clase | Dónde vive | Valores |
|---|---|---|
| **A · Secreto** | SSM `SecureString` → entorno del proceso → `${VAR}` | `POSTGRES_PASSWORD`, `AI_DB_PASSWORD`, `AI_SERVICE_SHARED_SECRET`, `INDEX_FEED_SHARED_KEY`, `JWT_SIGNING_KEY`, `EMBEDDING_API_KEY` |
| **B · Ajuste de entorno** | SSM `String` o el compose | `DEMO_HOSTNAME`, `ECR_REGISTRY`, `IMAGE_TAG`, `APP_ENV=demo`, `AiGateway__BaseUrl`, `JPV_INDEX_FEED_BASE_URL` |
| **C · Ajuste de comportamiento** | **git**, literal en el compose | `JPV_EMBEDDING_MODEL=openai/text-embedding-3-small`, `JPV_RETRIEVAL_DISTANCE_THRESHOLD=0.65`, `STUB_MODE=false`, `AiGateway__RetrievalTimeoutMs=2500` |
| **D · Constante** | Imagen / compose | Puertos internos, nombres de servicio |

**Parejas que deben coincidir literalmente**, resueltas con **un solo parámetro leído dos veces** para que no puedan derivar:

| Parámetro SSM | Se inyecta como |
|---|---|
| `/jbg-demo/AI_SERVICE_SHARED_SECRET` | `JWT_SECRET` (ai) **y** `AiGateway__JwtSecret` (api) |
| `/jbg-demo/INDEX_FEED_SHARED_KEY` | `JPV_INDEX_FEED_API_KEY` (ai) **y** `IndexFeed__ApiKey` (api) |

Derivar produce un `401` cuya causa el servicio tiene prohibido revelar.

### `/health` enriquecido

Retorno **`dict[str, Any]`**, sin modelo Pydantic ni ruta nueva: `openapi.json` no se mueve.

| Campo | Contenido | Coste |
|---|---|---|
| `status` | `OK` \| `degraded` | — |
| `version` | `service_version` | — |
| `database` | `ok` \| `unavailable` | `SELECT 1`, cacheado ~10 s |
| `index.documents` | recuento de `ai.product_document` | cacheado ~10 s |
| `index.model` | `DISTINCT embedding_model` del índice | cacheado ~10 s |
| `index.status` | `ok` \| **`model_mismatch`** | comparación con `JPV_EMBEDDING_MODEL` |
| `provider` | **`configured`** \| `missing` | ¿hay clave? **Nunca se llama al proveedor** |

`model_mismatch` nombra ambos modelos y degrada `status`. La caché evita que una sonda por segundo consuma el pool de 5 conexiones compartido.

### `api/ai/health` (.NET)

| Ruta | Método | Rol | Notas |
|---|---|---|---|
| `api/ai/health` | `GET` | **Administrator** | Proxea el `/health` de `jbg-ai`. `403` para operador, `401` sin token |

Cliente HTTP con nombre propio, **sin el circuit breaker** del gateway: la sonda debe poder diagnosticar precisamente cuando el camino principal está roto. Timeout corto y propio. La respuesta **no** expone la cadena de conexión, el host de la base ni ningún fragmento de clave.

### Despliegue

1. OIDC → ECR login → build y push de `jbg-demo-api` (con `--build-arg VITE_API_BASE_URL=/api`) y `jbg-demo-ai`.
2. `aws ssm send-command` → `deploy.sh` en la instancia.
3. `deploy.sh`: `set -euo pipefail` **sin `-x`**; `export` de los parámetros; validación `: "${VAR:?}"`; `docker compose -f compose.demo.yaml up -d`; `alembic upgrade head`; calentamiento.
4. Smoke por `docker exec` sobre `/health`: `database: ok`, `index.documents > 0`, `index.status: ok`, `provider: configured`.

### Camino del dato

`pg_dump` de `public` y `pg_dump -n ai` desde local → sustituir usuarios reales por cuentas de demo (una de administrador, una de operador) → restaurar tras `bootstrap.sql` y `alembic upgrade head` → **un** `POST /v1/index/sync` → verificar `GET /v1/index/status` con `drift_count = 0`.

---

## Arquitectura

- **Frontera público/privado (§6.4 y S15):** el frontend nunca habla con Python; .NET → Python con JWT interno HS256; red interna, sin puerto publicado. C17 la materializa por primera vez sobre infraestructura real.
- **Patrón de despliegue existente** (OIDC + ECR + SSM de `deploy-aws-ec2.yml`) reutilizado como forma, **no como fichero**: el workflow de la demo es nuevo y apunta a otra cuenta.
- **Un controlador por capacidad** (patrón fijado en C15: `AiCatalogController`, `AiIndexFeedController`, `AiSearchController`, `AiSearchEventsController`) → `AiHealthController`.
- **`IAiGatewayClient` crece un método**, que es el patrón que su propia documentación describe.
- **Breaking changes:** ninguno. No se tocan contratos REST existentes ni el snapshot de OpenAPI. `AssistedSearchResultDto`, `CreateSaleRequest` y el resto quedan como los dejó C16.
- **Decisión que revierte una del diseño:** el §12.1 daba por hecho `docker-compose` en la EC2 de producción. No lo hay. La demo sí lo usa, en otra máquina y por otro motivo — registrado en §0 del plan.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec completos (`proposal`, **`design.md`**, `specs`, `tasks`) y `openspec validate --all --strict` en **`0 failed`**
- [ ] `terraform plan` de la demo **no lista ningún recurso de la cuenta de la tienda**
- [ ] `terraform apply` de la demo levanta el entorno en una cuenta virgen sin pasos manuales fuera del runbook
- [ ] `docker compose -f compose.demo.yaml config` válido; **sólo el proxy declara `ports:`**
- [ ] Workflow verde por `workflow_dispatch` **antes** de tocar la rama `demo`
- [ ] Smoke post-deploy en verde: `database: ok`, `index.documents > 0`, `index.status: ok`, `provider: configured`
- [ ] URL pública por **HTTPS con certificado válido**, con las dos cuentas de demo operativas
- [ ] Una búsqueda en lenguaje natural devuelve resultados con **origen asistido**, no degradado
- [ ] `ai-service`: `uv run pytest` en verde sin llamadas reales a LLM, embeddings ni RDS; **`openapi.json` sin cambios** y `test_openapi_snapshot_is_stable` en verde
- [ ] Backend: xUnit + Moq + FluentAssertions, nomenclatura `Método_Escenario_ResultadoEsperado`
- [ ] Frontend: Vitest + RTL, nomenclatura `should [comportamiento] when [condición]`, queries accesibles
- [ ] Baseline de ambas suites comparado **por nombres de test**, nunca por número
- [ ] Ninguna migración nueva, ni EF Core ni Alembic
- [ ] Deprecaciones aplicadas y `backend/README.md` corregido
- [ ] `DEFERRED_TASKS.md` actualizado (bifurcación del `/health`, medición del presupuesto)
- [ ] Documentación actualizada según la tabla *Post-Implementation Documentation Update* de `openspec/project.md`
- [ ] Sin TODO/FIXME sin tarea asociada
- [ ] UI en español (es-ES) y moneda EUR (€)

**Tests nombrados:**

| Test | Zona |
|---|---|
| `test_health_reports_database_index_and_provider` | ai-service |
| `test_health_reports_model_mismatch_when_index_disagrees` | ai-service |
| `test_health_never_calls_the_embedding_provider` | ai-service |
| `test_health_result_is_cached_between_probes` | ai-service |
| `test_openapi_snapshot_is_stable` *(debe seguir verde)* | ai-service |
| `AiHealth_ReturnsUnauthorized_ForAnonymousRequest` | backend |
| `AiHealth_ReturnsForbidden_ForOperatorRole` | backend |
| `AiHealth_BypassesCircuitBreaker_WhenGatewayCircuitIsOpen` | backend |
| `AiHealth_DoesNotLeakConnectionStringOrApiKey` | backend |
| `should show ai service status card when user is administrator` | frontend |
| `should not show ai service status card when user is operator` | frontend |
| `should render model mismatch as an error state` | frontend |

---

## Requisitos No Funcionales

- **Seguridad:** el servicio de IA **no publica puerto** y el SG sólo abre 80/443 — la clave del proveedor no es alcanzable desde Internet. Secretos en SSM `SecureString`, inyectados en el arranque, **nunca en la imagen, nunca en el repositorio, nunca en disco**. `set -x` prohibido en el tramo que los lee: la salida del comando remoto se conserva en el historial del almacén. Confianza OIDC acotada a `environment:demo`, más estricta que la de producción. `api/ai/health` sólo para administradores y sin filtrar cadenas de conexión ni claves. **Nota honesta:** las variables de entorno de un contenedor son visibles con `docker inspect` para root en el host — es proporcionado para una demo, y no debe describirse como una bóveda de secretos.
- **Rendimiento y free-tier:** `t3.small` de partida con `mem_limit: 512m` en el servicio de IA, de modo que un OOM mata **sólo** la IA y el breaker degrada a léxico; swap en el disco ya pagado; pool de 5 conexiones respetado gracias a la caché del `/health`. **`deploy.resources` no vale**: se ignora fuera de swarm.
- **Coste:** los vectores viajan en el volcado, así que no se re-facturan; el entorno es destruible con `terraform destroy` cuando deje de hacer falta. El §12 del diseño se compromete a que el coste esté instrumentado y reportado.
- **Observabilidad:** `trace_id` propagado; logs estructurados; el `/health` es el **latido**, no la vigilancia — la calidad, la latencia y el coste son trabajo del dashboard y de las trazas, según S16.
- **Integridad de datos:** el volumen de Postgres es persistente y el script **jamás** ejecuta `down -v`; el volumen de Caddy conserva los certificados frente al límite de cinco duplicados por semana de la autoridad; los usuarios reales de la joyería **no** viajan al entorno público.
- **Reproducibilidad:** ninguna etiqueta `latest` en imágenes ni en el plugin de Compose; AMI resuelta por parámetro público; el entorno se levanta en cualquier cuenta AWS cambiando variables.

---

## Preguntas Abiertas

Ninguna pendiente de producto. Cerradas en la exploración del 2026-08-29 y registradas en §0 del plan.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿Se despliega a la cuenta de la tienda? | **No. No hay acceso**, y su RDS es la base real del negocio. Entorno de demo autocontenido en otra cuenta |
| 2 | ¿RDS o Postgres en contenedor? | **Contenedor**, `pgvector/pgvector:pg15`. Vuelve irrelevante la verificación de `CREATE EXTENSION vector` que el plan marcaba como obligatoria y nunca se hizo |
| 3 | ¿Compose o `docker run`? | **Compose**, en una instancia nueva. En producción no hay compose, pero producción no se toca |
| 4 | ¿Se mueve `backend/docker-compose.yml` a la raíz? | **No.** La spec viva `ai-service-dev-compose` fija su ruta y su red. `compose.demo.yaml` es autocontenido |
| 5 | ¿nginx o Caddy? | **Caddy en contenedor.** Elimina certbot, su cron y el heredoc de configuración |
| 6 | ¿Dominio propio? | Pendiente de compra, **no bloquea**: `sslip.io` como puente y `${DEMO_HOSTNAME}` para migrar |
| 7 | ¿El `/health` comprueba el proveedor? | **No.** `provider: configured\|missing`. S15 y S16 lo desaconsejan explícitamente |
| 8 | ¿Se bifurca en liveness y readiness? | **Todavía no.** Disparador escrito en la HU y en `DEFERRED_TASKS.md` |
| 9 | ¿Se regenera `openapi.json`? | **No.** El retorno sigue siendo `dict[str, Any]` |
| 10 | ¿Dónde vive el modelo de embeddings? | **En git**, literal. No es un secreto y **no debe variar por entorno** |
| 11 | ¿Se re-embebe en la demo? | **No.** Volcado de `ai` + un `sync` de reconciliación. Los vectores son fila a fila los de las métricas del README |
| 12 | ¿Viajan los usuarios reales? | **No.** Cuentas de demo. **Los 436 SKU con precios reales sí se publican** |
| 13 | ¿`Dockerfile.bundled` para la demo? | **No.** `Dockerfile.demo` independiente. Producción no se toca |
| 14 | ¿Se revierte el presupuesto de 2500 ms? | **No.** Se **mide y anota**; el arreglo es de C21/C22 |
| 15 | ¿`design.md`? | **Sí.** Veinte decisiones con alternativas defendibles y seis zonas |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que **no** toque la cuenta de la tienda, **no** modifique `Dockerfile.bundled` ni `backend/docker-compose.yml`, **no** regenere `openapi.json`, **no** abra migración y **no** adelante trabajo de C21 ni de C22.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. El §6 del plan lo nombra en el disparador del orden de corte —*«si el 26 de agosto no están la tabla de ablations y el sistema desplegado»*— y esa fecha ya pasó. Sin C17 no hay criterio del §16 que marcar.
- **Estimación:** **8 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C15 y C16 archivados. Alta de la cuenta AWS de demo. Compra del dominio (**no bloqueante**). No compite en zona con ningún change activo, pero sí por horas con C21, C22 y C24.
- **Línea de corte** (si la sesión desborda, regla 5 del procedimiento): (1) Terraform, `user_data`, compose, workflow y despliegue del sistema con el corpus cargado y URL con TLS — **archivable**; (2) `/health` enriquecido con contraste de modelo; (3) `api/ai/health` y tarjeta del dashboard; (4) endurecimiento del Dockerfile de `ai-service`, `.dockerignore` y deprecaciones.
- **Tags:** `HU-AIENG-017`, `C17`, `EP11`, `infra`, `terraform`, `docker`, `compose`, `caddy`, `aws`, `oidc`, `ssm`, `deployment`, `health`, `observability`, `demo`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-017](../../../../Documentos/Historias/AI-Eng/HU-AIENG-017.md)
- **Change OpenSpec:** `openspec/changes/add-ai-service-deployment/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C17 y §0 de 2026-08-29) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.1, §6.4, §12, §15, §16)
- **Apuntes del Máster (guía, no dogma):** [S15 · Qué entendemos por producción](../../../../Documentos/Sesiones%20Master%20AIEng/S15_Produccion_I/Que%20entendemos%20por%20produccion.md) *(las cuatro promesas y la frontera público/privado)* · [S15 · Despliegue en Clouds](../../../../Documentos/Sesiones%20Master%20AIEng/S15_Produccion_I/Despliegue%20en%20Clouds.md) *(el health check barato; la herramienta más simple que resuelva el problema; persistencia y arranque en frío)* · [S15 · Contenerización con Docker](../../../../Documentos/Sesiones%20Master%20AIEng/S15_Produccion_I/Contenerizacion%20Docker.md) *(un secreto dentro de una imagen es un secreto con pasaporte; sólo el backend publica puerto)* · [S16 · Observabilidad](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Observabilidad.md) *(no confundáis el latido con la vigilancia)*
- **Specs vivas:** `ai-service-runtime` · `ai-service-dev-compose` *(**no** se modifica)* · `ai-assisted-search` · `vector-retrieval` · `product-document-indexer` · `dashboard-analytics` · `access-control`
- **Precedentes:** C01 (Dockerfile y esqueleto) · C05 (`bootstrap.sql`, esquema `ai`, rol de mínimo privilegio) · C03 (**deuda de deprecación asignada a C17** en su ticket) · C12 (runbook de AutoBulk, patrón de procedimiento no ejecutado en el merge) · C15 (patrón de un controlador por capacidad) · C16 (presupuesto temporal de 2500 ms)
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Testing:** [testing-backend.md](../../../../Documentos/testing-backend.md) · [testing-frontend.md](../../../../Documentos/testing-frontend.md) — *Estado de la suite: fallos conocidos*
- **UI:** [analisis-metronic-frontend.md](../../../../Documentos/Propuestas/analisis-metronic-frontend.md) — componentes reutilizados en la tarjeta: `card`, `badge`, `alert`, `skeleton`, `separator`
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-29 | `/enrich-us` | Creación a partir de HU-AIENG-017 y de la exploración del 2026-08-29. Recoge: entorno de demo autocontenido en una cuenta AWS separada por no haber acceso a la de la tienda, Postgres+pgvector en contenedor en lugar de RDS, `compose.demo.yaml` autocontenido con Caddy como único servicio con puertos, workflow OIDC + ECR + SSM sobre la rama `demo` con confianza acotada al entorno, taxonomía de secretos frente a ajustes con el modelo de embeddings versionado en git, `/health` enriquecido sin llamar al proveedor y con contraste de `embedding_model` contra el índice, `api/ai/health` fuera del circuit breaker con tarjeta para administradores, camino del dato por volcado más un `sync` de reconciliación, y las deprecaciones que el ticket de C03 ya había asignado a C17 |
