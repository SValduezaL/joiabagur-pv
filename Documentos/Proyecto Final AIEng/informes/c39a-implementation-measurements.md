# C39a · `redeploy-and-audit-demo-environment` — mediciones de implementación

**Rama:** `c39a-redeploy-and-audit-demo-environment`, derivada de `ai-eng`
**Historia:** [HU-AIENG-043](../../Historias/AI-Eng/HU-AIENG-043.md) · **Ticket:** `openspec/changes/redeploy-and-audit-demo-environment/ticket.md`
**Cuenta de la demo:** `666823181744`, `eu-west-1`, perfil `jbg-demo` · **Producción, intacta:** `eu-west-3`

> **Cómo leer este informe.** Cada afirmación va con su medición al lado o se declara como no medida.
> Las refutaciones de los propios artefactos de este change se marcan con ⚠ y no se corrigen en
> silencio: se corrige el artefacto y se dice aquí.

---

## 0 · Un desvío antes de la primera tarea: el bundle de CA de esta máquina estaba caducado

**No estaba en el ticket y bloqueaba todo el grupo 1.** La primera llamada a AWS desde este entorno murió
con `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`, y **también con el `--ca-bundle`
apuntando explícitamente** a `C:\Users\sergi\.aws\ca-bundle-norton.pem`. El §1.3 del *runbook* documenta
que ese fichero es obligatorio en esta máquina porque Norton intercepta TLS con su propia raíz, presente
en el almacén de Windows y ausente del `certifi` del CLI. Lo que **no** documenta es que **el fichero
caduca cuando Norton rota su raíz**.

| | |
|---|---|
| Bundle en uso | del **2026-08-11**, 131 certificados, 261,9 KB |
| Regenerado desde el almacén | `certifi` + `ssl.enum_certificates('ROOT')` + `('CA')` → **253 certificados**, 463,2 KB |
| Resultado | `aws sts get-caller-identity` responde `arn:aws:sts::666823181744:assumed-role/AWSReservedSSO_admin_…/svalduezal` |

**Arreglado de forma duradera y con autorización explícita**: copia de seguridad en
`ca-bundle-norton.pem.bak-20260927` y fichero sobrescrito, de modo que el `ca_bundle` del perfil vuelve a
funcionar sin variable de entorno — comprobado retirando `AWS_CA_BUNDLE` de la sesión.

**No se filtró por la bandera de confianza**, exactamente como `CLAUDE.md` advierte: la raíz de Norton no
la lleva y filtrar deja el bundle incompleto. Va al §1.3 del *runbook* como nota de caducidad.

---

## 1 · Puerta de entrada

### 1.1 · La foto desde fuera *(tarea 1.1)*

```
parámetros bajo /jbg-demo/     11   ·  4 no secretos + 7 secretos
instancia                      i-095f0ba16e2bb8278 · running · t3.small · 52.49.209.14
                               arrancada 2026-08-30T11:42:22Z  →  28 días en pie
DEMO_HOSTNAME                  52-49-209-14.sslip.io
ECR_REGISTRY                   666823181744.dkr.ecr.eu-west-1.amazonaws.com
IMAGE_TAG                      sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d
salud pública                  http=200  tls=0  214 ms
```

**La correlación que convierte una inferencia en un hecho.** El `IMAGE_TAG` desplegado, sin su prefijo
`sha-`, es `d6a740fa5e0b678eef32893f92c9a3a36bec7f8d`, y `git rev-parse origin/demo` devuelve **el mismo
valor** — comprobado programáticamente, no a ojo. Que la demo sirva C34 no es una deducción a partir de
git: **es el commit desde el que se construyó la imagen que está corriendo**.

```
origin/demo   d6a740fa5e0b678eef32893f92c9a3a36bec7f8d   «Registra el QA de C34…»   2026-09-22
ai-eng        0d63f1aeacc4b75daa27702eb2f9ad235dd80353   merge PR #45 (C42)         2026-09-27
adelanto      84 commits
```

Los cuatro parámetros no secretos son `DEMO_HOSTNAME`, `DEPLOYMENT_BUNDLE_URL`, `ECR_REGISTRY` e
`IMAGE_TAG`; los siete secretos, `AI_DB_PASSWORD`, `AI_SERVICE_SHARED_SECRET`, `ASSIST_LLM_API_KEY`,
`EMBEDDING_API_KEY`, `INDEX_FEED_SHARED_KEY`, `JWT_SIGNING_KEY` y `POSTGRES_PASSWORD`. **Listados por
nombre y nunca descifrados:** la consulta no lleva `--with-decryption`.

**Y los dos que este change viene a añadir no están:** `AGENT_LLM_API_KEY` y `ROUTER_LLM_API_KEY`
**confirmados ausentes contra la cuenta viva**, no sólo contra el repositorio.

### 1.2 · El sondeo desde dentro del anfitrión *(tarea 1.2)*

Ejecutado por el servicio de gestión de sistemas sobre el contenedor de IA, usando su propio
`DATABASE_URL` — el mismo patrón que `verify.sh`, para no manejar contraseñas.

| Tabla / *checkpoint* | Valor |
|---|---|
| `ai.knowledge_chunk` | **161** |
| `ai.knowledge_document` | **32** |
| `ai.product_document` | **1.200** |
| `ai.pos_projection` | **6.720** filas |
| *checkpoint* `pos-availability` | incremental **2026-09-22 18:22:29 UTC** · completo 2026-08-29 · 6.720 |
| *checkpoint* `catalog` | **2026-08-30 12:29:42 UTC** · 1.200 |

Las once tablas del esquema `ai`: `alembic_version`, `co_occurrence`, `eval_case`, `eval_result`,
`eval_run`, `knowledge_chunk`, `knowledge_document`, `pos_projection`, `product_document`,
`sync_checkpoint`, `sync_failure`.

### ⚠ 1.2a · El corpus NO está vacío, y eso refuta un supuesto de este change

**161 fragmentos y 32 documentos: el corpus de C23 íntegro.** La pregunta abierta Q3 del `design.md` y la
P7 del ticket asumían lo contrario, y **el razonamiento era mío y estaba mal**.

El motivo es obvio en retrospectiva: **el corpus se indexa en la base, y la base vive en el volumen
`jbg-demo-pgdata`**, cuya persistencia es un requisito vivo de esta misma capability —*«Data and
certificates survive a redeployment»*—. El hueco del `Dockerfile` **no vacía la tabla**: impide
**reindexar**, y dejaría vacío un **entorno nuevo**.

**Qué cambia y qué no.** El argumento de D5 —la imagen tiene que ser autosuficiente para ser
reproducible— **no cambia** y el hueco se cierra igual. Lo que cambia es su urgencia: de *«M2 y M3 están
roscados en la demo»* a *«lo estarían en el próximo entorno limpio»*. Los dos artefactos quedan
corregidos en el sitio.

**Dato de apoyo que lo confirma:** `jbg-demo-api` y `jbg-demo-ai` llevan **4 días** arriba y
`jbg-demo-postgres` **3 semanas**. Algo reinició los dos primeros sin recrear la base.

### ⚠ 1.2b · La proyección está a unas 120 veces el techo, y `verify.sh` no lo habría visto

```
último drenaje incremental   2026-09-22 18:22:29 UTC
techo declarado              jpv_pos_projection_max_age_seconds = 3.600 s
antigüedad al medir          ≈ 5 días  ≈ 432.000 s     →  ≈ 120 × el techo
referencia de C41            14,4 × el techo, que es con lo que se justificó
```

**Y pasa la verificación.** La quinta condición de `verify.sh` mira *filas ausentes* —proyección nunca
drenada, cero filas, o puntos de venta sin ámbito— y **nunca antigüedad**. Un entorno con 6.720 filas
rancias de cinco días la supera sin un aviso.

**No se cierra en este change, y el motivo está razonado:** el *fast-forward* trae el drenaje de C41, que
corre al arrancar y **en su forma completa cuando no hay *checkpoint***, así que la rancidez se cura sola y
lo que procede es medirla antes y después (tarea 5.3). Una condición por antigüedad **sobre un entorno que
acaba de arrancar** mediría el reloj del despliegue y no la salud del sistema. **Queda declarada como
hueco de la verificación, con su cifra.**

### 1.3 · El recorrido *(tarea 1.3)*

**Corto.** El entorno está en pie con sus siete secretos, responde 200 con certificado válido y su base
conserva catálogo, corpus y proyección. No entra nada del §2 ni del §5 del *runbook*: ni `terraform
apply`, ni recrear secretos, ni restaurar esquemas, ni reemplazar personal. **Declarado antes de la
primera modificación.**

### 1.4 · Línea base de las suites *(tarea 1.4)*

Medidas **en serie**, nunca en paralelo, y leyendo la **línea de resumen** y no el código de salida.
Comprobado antes de arrancar que no había ningún `JoiabagurPV.API.exe` ni proceso `dotnet` vivo que
bloqueara `bin/Debug` — la trampa que `CLAUDE.md` describe, en la que la compilación falla, **cero tests
corren y `dotnet test` sale 0**.

| Suite | Resumen | Reloj | Contra lo documentado |
|---|---|---|---|
| **backend** | `Con error: 50 · Superado: 1358 · Total: 1408` | 9 m 53 s | `CLAUDE.md` midió **50 y 51** sobre el mismo commit. **Dentro de banda** |
| **frontend** | `Test Files 14 failed \| 49 passed (63)` · `Tests 113 failed \| 846 passed (959)` | 197 s | documentaba **113 de 729 en 14 de 54** al cierre de C40. **El recuento de rojos y de ficheros es idéntico** y la suite ha crecido de 729 a 959 tests |

**La línea de resumen de `dotnet test` viene en castellano en esta máquina** —`Con error:` en lugar de
`Failed:`—, y merece decirse porque un filtro escrito contra la inglesa devuelve **cero** y se lee como
«no hay rojos». Es la misma familia de trampa que el `vitest` que sale 0 al canalizarse.

**Los 50 nombres del backend, por clase:** `InventoryIntegrationTests` 9 · `ImageCompressionServiceTests`
5 · `ProductsControllerTests` 5 · `SalesControllerTests` 4 · `ReturnsControllerTests` 4 ·
`RepositoryTests` 4 · `PointOfSalesControllerTests` 3 · `EmbeddingEndpointsTests` 3 · y diez clases más con
uno o dos. **Las tres clases que `CLAUDE.md` declara inestables están las tres**, y
`InventoryIntegrationTests` encabeza con 9.

**Los 14 ficheros del frontend**, entre los que está `scan.test.tsx`, uno de los tres que la documentación
nombra como rotatorios: `payment-methods.test.tsx`, `products/__tests__/edit.test.tsx`,
`product-photo-upload.test.tsx`, `products/edit.test.tsx`, `sales/__tests__/new-image.test.tsx`,
`new.test.tsx`, `sales-index.test.tsx`, `scan.test.tsx`, `image-recognition.service.test.ts`,
`ml-edge-cases.test.ts`, `model-training.service.test.ts`, `auth.service.test.ts`,
`payment-method.service.test.ts`, `product.service.test.ts`.

Los dos conjuntos de nombres quedan guardados para la comparación de la tarea 8.4, que compara **nombres
y no recuentos**.

---

## 2 · La auditoría de configuración

### 2.1 · Lo que declara cada servicio, y cómo reproducir el volcado *(tarea 2.1)*

| Servicio | Superficie declarada | Comando que lo reproduce |
|---|---:|---|
| `jbg-ai` | **51** ajustes, **3** obligatorios (`app_env`, `service_version`, `jwt_secret`) | `uv run python -c "from jbg_ai.config.settings import Settings; f=Settings.model_fields; print(len(f)); [print(k, v.is_required(), v.default) for k,v in sorted(f.items())]"` desde `ai-service/` |
| `backend` | **7** clases de opciones con sección propia | `grep -rn "SectionName" backend/src/JoiabagurPV.Application/Configuration/` |
| `frontend` | **1** variable, y **de compilación** | `grep -rhoE "import\.meta\.env\.[A-Z_]+" frontend/src` |

Las siete secciones de .NET: `AiAgentAssist`, `AiFreeQuerySearch`, `AiGateway`, `AiSalesAssist`,
`AiSearch`, `IndexFeed`, `ProfileReview`.

### 2.2 · El cruce contra `compose.demo.yaml` *(tarea 2.2)*

El compose declara **39** claves de entorno repartidas en cuatro servicios. Éste es el cruce; la columna
de la derecha es lo que pasa si la clave falta.

#### `jbg-demo-ai` — 15 claves

| Ajuste declarado | Valor en la demo | Qué pasa si falta |
|---|---|---|
| `app_env` **(obligatorio)** | `demo` | el servicio no arranca |
| `service_version` **(obligatorio)** | `0.1.0` | el servicio no arranca |
| `jwt_secret` **(obligatorio)** | `${AI_SERVICE_SHARED_SECRET}` — secreto de SSM | no arranca; y un valor **derivado** del de .NET produciría un 401 cuya causa el servicio está especificado para no revelar |
| `log_level` | `INFO` | por defecto `INFO`; inocuo |
| `enable_dev_endpoints` | `"false"` — **literal, y no redundante** | deriva de `app_env`, y **sólo** los literales `prod`/`production` lo apagan: `demo` no es ninguno, así que sin esta clave la ruta de evaluación quedaría montada en un entorno demostrado |
| `database_url` | `postgresql+psycopg://jbg_ai:${AI_DB_PASSWORD}@…` | sin base no hay recuperación |
| `jpv_index_feed_base_url` / `_api_key` | `http://jbg-demo-api:8080` / `${INDEX_FEED_SHARED_KEY}` | el feed de catálogo rechaza cada sincronización |
| `jpv_index_sync_time_budget_seconds` | `"180"` | por defecto 180; idéntico |
| `stub_mode` | `"false"` — **literal versionado por requisito** | por defecto `true`: **serviría un fixture determinista en lugar del sistema** |
| `jpv_embedding_model` | `openai/text-embedding-3-small` — **literal versionado** | sin modelo no hay vectores; y un modelo distinto del indexado pone consultas y documentos en dos espacios vectoriales, que `verify.sh` comprueba |
| `jpv_embedding_api_key` | `${EMBEDDING_API_KEY}` | la recuperación responde 503 |
| `jpv_retrieval_distance_threshold` | `"0.65"` — **literal versionado** | por defecto 0,65; el requisito exige que sea literal para que coincida con el valor con que se calcularon las cifras de evaluación |
| `jpv_assist_llm_model` | `openai/gpt-4o-mini` | por defecto el mismo |
| `jpv_assist_llm_api_key` | `${ASSIST_LLM_API_KEY:-}` — **el único secreto opcional** | el argumentario no se genera: `prompt_version: null` y `pitchStatus: not_generated`. **Es también su *rollback*** |
| `jpv_assist_pitch_timeout_seconds` | **ausente a propósito**, con su comentario | por defecto 4 s por llamada. El comentario dice que espera una medición de este entorno |
| **`jpv_router_llm_api_key`** | ⚠ **AUSENTE — hueco 2** | el enrutador **repliega a la clave del argumentario** (`credential=assist_fallback`, observado en el log de C34). Funciona, y **no es lo declarado**: hace inseparables los costes de un clasificador de ~30 tokens y de un párrafo |
| **`jpv_agent_llm_api_key`** | ⚠ **AUSENTE — hueco 3** | el bucle **no se construye**: la ruta responde 200 sin ejecutarlo. Es uno de los dos estados de pantalla que C42 declara **nunca observados en producción** |
| `jpv_router_llm_model`, `jpv_agent_llm_model` | ausentes; por defecto **`openai/gpt-4o`** los dos | **correcto y no se toca**: el `gpt-4o-mini` del enrutador fue **vetado por medición** en C31 (silenciaba 3 consultas contestables, 6,25 % de falso positivo) |
| `jpv_pos_sync_scheduler_enabled` / `_interval_seconds` | ausentes; por defecto **`true`** y **600 s** | correctos. El intervalo es **derivado** y no elegido: techo ÷ intervalo ≥ 4, o sea 3.600 ÷ 600 = 6 drenajes fallidos tolerados |
| Los ~30 restantes | ausentes, por defecto | recuperación, fusión, abstención, familias y sustitutos: **literales versionados en código**, que es donde el requisito manda que estén |

#### `jbg-demo-api` — 14 claves

| Ajuste declarado | Valor en la demo | Qué pasa si falta |
|---|---|---|
| `ConnectionStrings__DefaultConnection` | `Host=jbg-demo-postgres;…` | la API no arranca |
| `Jwt__SecretKey` / `__Issuer` / `__Audience` | `${JWT_SIGNING_KEY}` / `JoiabagurPV` / `JoiabagurPV` | los tokens de usuario se firmarían con nada |
| `AiGateway__BaseUrl` | `http://jbg-demo-ai:8000` | sin destino no hay IA |
| `AiGateway__JwtSecret` | `${AI_SERVICE_SHARED_SECRET}` — **el mismo parámetro leído dos veces** | 401 en cada llamada interna. Dos parámetros podrían derivar, y por eso es uno |
| `AiGateway__RetrievalTimeoutMs` | `"2500"` | por defecto 2.500; idéntico |
| `AiGateway__AssistTimeoutMs` | `"10000"` | por defecto 10.000, con **suelo de 8 s validado al arrancar** |
| `AiGateway__AgentTimeoutMs` | ausente; por defecto **18.000** | **correcto y suficiente**, con suelo de 15 s validado al arrancar porque 15 s es el reloj de pared del propio servicio. **No es un hueco** — contradice lo que la exploración supuso al principio |
| `AiSearch__EnabledByDefault` | `"true"` | `bool` sin inicializador → `false`, y la búsqueda asistida no se sirve |
| `AiSalesAssist__EnabledByDefault` | `"true"` | idem para la ficha de venta |
| `AiFreeQuerySearch__EnabledByDefault` | `"true"` | idem para el panel de consulta libre |
| **`AiAgentAssist__EnabledByDefault`** | ⚠ **AUSENTE — hueco 1** | `public bool` **sin inicializador = `false`**, con `EnabledPointOfSaleIds` vacío: **el panel del agente no se sirve para ningún punto de venta**. Es el único pilar del PF que no se puede enseñar por otra vía |
| `IndexFeed__ApiKey` | `${INDEX_FEED_SHARED_KEY}` — leído dos veces, como el anterior | el feed rechaza cada sincronización |
| `Cors__AllowedOrigins__0` | `https://${DEMO_HOSTNAME}` | el navegador rechazaría las llamadas |
| `ProfileReview__*` | ausentes, por defecto | umbral 0,80 y confianza mínima 0,50; no afectan a la demostración |

#### `jbg-demo-postgres` y `jbg-demo-proxy`

Sin ajustes de IA. La base recibe `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`; el proxy, sólo
`DEMO_HOSTNAME`, que es el nombre para el que pide el certificado.

### 2.3 · El frontend no tiene entorno de ejecución, y es deliberado *(tarea 2.3)*

**No hay servicio de frontend en el compose, y no hay una sola variable de entorno en ejecución.** La SPA
se sirve desde el `wwwroot` de la propia API, y su única variable —`VITE_API_BASE_URL`— **se hornea en el
*build*** con valor **relativo `/api`**. El comentario del propio workflow lo argumenta:

> *«`VITE_API_BASE_URL` is RELATIVE. The interface is served by this same container, so every call is
> same-origin, and the image stays agnostic of the hostname it answers under — which is what lets the
> environment start on a name derived from its IP address and move to a purchased domain without a
> rebuild. The production image bakes an absolute domain and is not reused here for exactly that
> reason.»*

**Consecuencia práctica para la entrega:** el *hostname* `52-49-209-14.sslip.io` puede sustituirse por un
dominio comprado **sin reconstruir imagen**, que es el §6 del *runbook*. Y consecuencia para esta
auditoría: **la fila del frontend no puede tener huecos de configuración**, porque no hay configuración
que pueda faltar en ejecución. Es la única de las tres que se cierra por construcción.

### 2.4 · Dos desajustes de documentación que la auditoría destapó *(tarea 2.4)*

| Dónde | Qué dice | Qué es verdad |
|---|---|---|
| `deploy/demo/README.md` §3 | *«Terraform creates the **three** non-secret parameters (`DEMO_HOSTNAME`, `ECR_REGISTRY`, `IMAGE_TAG`)»* | Son **cuatro**. `terraform/demo/ssm.tf` declara además **`DEPLOYMENT_BUNDLE_URL`**, y la cuenta lo tiene. La frase enumera tres y omite el cuarto |
| `deploy/demo/README.md`, en conjunto | último commit del 2026-09-26, de C41 | Está **un change por detrás**: no menciona C42 ni su panel del agente. Nace el 2026-08-30 con C17 y acumula 8 commits, así que **no es un documento pre-PF** — el temor de partida queda refutado |

Y una tercera, que no es del *runbook* sino de la exploración de este mismo change: **`AgentTimeoutMs` ya
existía** con 18.000 ms y suelo de 15 s validado al arrancar. La primera pasada de la exploración lo dio
por ausente; la auditoría lo corrigió antes de escribir el ticket.

---

## 3 · Los cinco huecos, cerrados

### 3.1 · El interruptor del agente, y es la TERCERA vez que este defecto llega a este fichero

`AiAgentAssist__EnabledByDefault: "true"`, literal versionado en `jbg-demo-api`. Lo que la
implementación descubrió al buscar dónde ponerlo es que **el comentario del hueco de al lado ya cuenta
esta misma historia**: `AiFreeQuerySearch__EnabledByDefault` está anotado como *«THE THIRD OF THE FAMILY,
missing until C40_FIX»*.

| Vez | Interruptor | Quién lo encontró | Cómo se manifestaba |
|---|---|---|---|
| 1ª | `AiSearch__EnabledByDefault` | **C17**, corriendo una búsqueda real por la URL pública | 200 con resultados plausibles servidos por la ruta **léxica**, `aiAvailable: false`, la IA nunca llamada |
| 2ª | `AiFreeQuerySearch__EnabledByDefault` | **C40_FIX** | `assistedAnswerAvailable: false` con `switched_off` para **todas** las tiendas: el panel generativo entero, apagado |
| **3ª** | **`AiAgentAssist__EnabledByDefault`** | **C39a**, en esta auditoría | la cuarta tarjeta del *hub* no se sirve para ningún punto de venta |

**La forma es idéntica las tres veces, y eso es el dato.** No es un despiste que se repite: es lo que un
interruptor omitido **hace** aquí, porque los cuatro son `bool` sin inicializador con lista de puntos de
venta vacía. Es el argumento del escenario que la delta de spec añade —*«every demonstrated AI route
declares its switch»*— y el motivo de que sea un requisito y no una nota.

### 3.2 · Las dos credenciales, en sus tres capas

SSM —dos parámetros `SecureString`, versión 1—, `deploy.sh` con el patrón **literal** de
`ASSIST_LLM_API_KEY`, y el compose con valor por defecto vacío. El inventario pasa de **11 a 13**
parámetros: cuatro no secretos y nueve secretos, tres de ellos opcionales.

**Validado en lo que importa, que es que no rompan un despliegue:** cero líneas `:?` para los dos nombres
nuevos, y el patrón demostrado sobre un caso sintético —`x="$(false || true)"` bajo `set -euo pipefail`
no aborta—. Y `docker compose config` con el entorno vacío resuelve las tres claves nuevas a `""`, que es
la definición de «vacío equivale a no configurada».

**La clave nunca pasó por el registro.** Los dos parámetros se crearon canalizando el valor de
`ASSIST_LLM_API_KEY` por sustitución de comandos; de ella sólo se imprimió la longitud (164) y el prefijo
(`sk-`).

### 3.3 · Las dos condiciones nuevas de la verificación

Probadas **en los dos sentidos**, que es lo que las separa de una afirmación:

| | Resultado |
|---|---|
| Camino de paso, contra el entorno vivo *(script canalizado por SSM, sin sobrescribir nada en el host)* | `[verify] OK — 1200 documents indexed` · `[verify] OK — knowledge corpus holds 161 fragment(s)` · `[verify] OK — the agent route answered, stop_reason='aclaracion'` |
| Camino de fallo, **provocado** *(corpus forzado a 0 y puerto del agente muerto)* | **código 1**, y las dos causas nombradas en `stderr` |

**Y la prueba de paso destapó algo que refuerza el hueco 3 con evidencia en vez de con razonamiento:** el
agente **respondió**, y no con `sin_cliente`. Sin `JPV_AGENT_LLM_API_KEY` en el contenedor, el bucle
corrió **replegando a la clave del argumentario** — el mismo problema que el enrutador, ahora observado
también en el agente.

Un detalle de la sonda que quedó escrito en el propio script para que nadie lo lea como defecto: usa un
**punto de venta aleatorio**, como el calentamiento, y a diferencia de aquél **eso cambia el resultado**.
El calentamiento sólo necesita que la consulta se incruste; el agente busca un ámbito, y un ámbito que no
corresponde a ninguna tienda no le da nada con lo que trabajar, así que el bucle **termina legítimamente
pidiendo aclaración**. `stop_reason='aclaracion'` es una ruta que **responde**, que es todo lo que la
condición pregunta.

---

## 4 · ⚠ El arreglo de fondo, y la refutación de D5

### 4.1 · D5 elegía un camino que habría roto el desarrollo local

El diseño decidió **mover el contexto de *build* a la raíz**. Al implementarlo apareció el consumidor que
el diseño no buscó: **`backend/docker-compose.yml` construye el mismo `Dockerfile`** con
`context: ../ai-service`, y `ai-service-dev-compose` es capability viva. Reescribir cada `COPY` a
`ai-service/…` lo habría dejado sin construir. Y un coste más: el `.dockerignore` de la raíz **declara por
escrito** que no gobierna a este fichero, así que mover el contexto habría dejado esa frase falsa y las
exclusiones de `ai-service/.dockerignore` sin aplicar.

**Lo que se hace en su lugar**, y la propiedad que lo justifica está medida:

| | |
|---|---|
| Mecanismo | `--build-context corpus=./data/knowledge` + `COPY --from=corpus . ./data/knowledge` |
| Contexto primario | **intacto**, `ai-service` — el compose de desarrollo sigue construyendo, con una línea de `additional_contexts` |
| Construir **sin** el flag | **falla, código 1**: `failed to resolve source metadata for docker.io/library/corpus:latest` |
| Imagen | **426 MB antes y después** — el corpus es texto |
| Contexto transferido | **388,16 kB → 2,78 MB** |

La opción de copiar el corpus en el workflow antes del *build* se descartó por eso mismo: dejaría a
`docker build ai-service` produciendo **en silencio** una imagen sin corpus, que es el modo de fallo que
el hueco existe para eliminar.

### 4.2 · Y la mitad que ni el diseño ni la tarea diferida habían visto: la ruta estaba mal calculada

Al preparar la copia se le preguntó al contenedor en marcha, en vez de razonarlo:

```text
paths.py    : /app/.venv/lib/python3.11/site-packages/jbg_ai/data/paths.py
CORPUS_DIR  : /app/.venv/lib/data/knowledge   | existe: True
PROMPTS_DIR : /app/.venv/lib/python3.11/prompts | existe: False
```

**`CORPUS_DIR` se resolvía dentro del árbol de dependencias.** `parents[3].parent` es correcto en un
*checkout* y absurdo con el paquete instalado por `uv sync --no-editable`. Un `COPY` a `/app/data/knowledge`
no habría servido de nada, y el enlace simbólico que se escribió primero habría **tapado** el defecto en
vez de cerrarlo.

**Y la segunda línea del volcado dice por qué los prompts sí funcionaban:** `PROMPTS_DIR` **tampoco
existe**, y da igual, porque `load_prompt_file` **busca tres candidatos** en lugar de confiar en la
constante — y su *docstring* explica exactamente este riesgo: *«a second copy of this search would be a
second place for a container layout to diverge from a developer checkout»*. El corpus no tenía búsqueda.

**El arreglo es darle la misma.** `_CORPUS_CANDIDATES` = *checkout*, directorio de trabajo, `/app`; el
primero que sea directorio gana; **y no levanta excepción al importar**, porque esto corre en tiempo de
importación y un corpus ausente no debe presentarse como una caída total del servicio — `/health` dejaría
de responder. `discover_documents` sigue siendo quien falla, con el directorio nombrado.

| Comprobación | Antes | Después |
|---|---|---|
| `CORPUS_DIR` en la imagen | `/app/.venv/lib/data/knowledge`, **inexistente** | **`/app/data/knowledge`**, existe, **no es enlace**, 33 documentos, *sidecar* presente |
| Tests | ninguno cubría la resolución | `test_corpus_location.py`, **5 passed** |
| Suite de `ai-service` | — | **1.664 passed**, cero rojos |
| Contrato congelado | — | snapshot **4 passed**, `openapi.json` intacto en el árbol |
| Enlace simbólico | necesario | **retirado** |

**Consecuencia declarada:** el compose de desarrollo necesita `additional_contexts` o deja de construir —
una línea—, y de paso el entorno local **gana** un corpus que su imagen no llevaba.

---

## 5 · Lo que este change NO midió, dicho para que no se dé por hecho

- **Nada sobre el entorno desplegado con los cambios de este change.** Todo lo de arriba está medido
  contra el entorno **anterior** —el que sirve C34— o localmente. La verificación del entorno resultante
  es de **C39a-bis**, y es la razón por la que el change se partió.
- **Las dos suites de siempre no se volvieron a medir.** Este change no toca `backend/src` ni
  `frontend/src`, así que sus insumos no cambiaron. Y la comparación llega gratis: **la PR de este change
  dispara los dos workflows**, porque toca sus propios ficheros, y ésa es la primera ejecución de esos
  workflows en la historia del repositorio. Se lee en C39a-bis.
- **La deriva de rama sigue sin detectarse por nadie.** El entorno estuvo 84 commits y cinco semanas por
  detrás sin que ninguna comprobación lo dijera, y las siete condiciones de `verify.sh` **siguen sin
  comparar lo desplegado con la rama que debería servirse**. El dato existe en los dos lados —`IMAGE_TAG`
  en SSM y `git rev-parse origin/demo`— y falta quien los cruce. Declarado con su vía de cierre en el
  *proposal* de C39a-bis; su arreglo es código, y por eso no cabe allí.
- **La rancidez de la proyección no es condición de verificación.** Está medida a unas 120 veces el techo
  y `verify.sh` no la mira: su quinta condición cuenta filas ausentes, nunca antigüedad. No se cierra
  aquí, por el motivo del §1.2b.

---

## 6 · La restricción dura, comprobada fichero a fichero

**Diecisiete entradas, y ninguna de la ruta de producción.** No es una intención declarada: es el diff
completo, revisado uno a uno.

| Fichero | Por qué está permitido |
|---|---|
| `compose.demo.yaml` | composición **de la demo** |
| `deploy/demo/deploy.sh` · `verify.sh` · `README.md` | directorio **de la demo** |
| `.github/workflows/deploy-demo.yml` | workflow **de la demo**, disparado por `push` a `demo` |
| `.github/workflows/test-backend.yml` · `test-frontend.yml` | workflows de **test**, no de despliegue. Su único cambio son las ramas del disparador |
| `ai-service/Dockerfile` | **exclusivo de la demo**: comprobado que `deploy-aws-ec2.yml` construye sólo `Dockerfile.bundled` y **no** la imagen de `jbg-ai` |
| `ai-service/src/jbg_ai/knowledge/constants.py` · `tests/knowledge/test_corpus_location.py` | el arreglo de fondo y su test. Amplía la zona y queda declarado en el *proposal* |
| **`backend/docker-compose.yml`** | ⚠ **parece de producción y NO lo es**: es el compose de **desarrollo local**. El de producción es `backend/docker-compose.prod.yml`, **sin tocar** |
| `Documentos/…` (3) · `openspec/…` (3) | documentación y artefactos |

Sin tocar, y comprobado por ausencia en el diff: `deploy-aws-ec2.yml`, `deploy-backend-aws.yml`,
`deploy-frontend-aws.yml`, el *stack* `terraform/`, `terraform/demo/`, `Dockerfile.bundled`,
`Dockerfile.prod`, `docker-compose.prod.yml`, `backend/src`, `frontend/src` y `ai-service/openapi.json`.

**Y ninguna variable de Terraform**, que era una decisión y no un olvido: los dos *stacks* no tienen
ninguna de IA porque la configuración de IA vive en el compose como literal versionado y en SSM como
secreto creado a mano, deliberadamente fuera del fichero de estado.
