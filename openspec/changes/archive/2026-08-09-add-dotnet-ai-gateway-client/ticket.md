# T-AIENG-003: Typed .NET gateway client for jbg-ai with resilience and service token (C03)

> Ticket técnico del change OpenSpec `add-dotnet-ai-gateway-client`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, `Documentos/` (diseño RAG y plan de changes), specs vivas de `openspec/specs/`, el contrato congelado `ai-service/openapi.json` y [HU-AIENG-003](../../../../Documentos/Historias/AI-Eng/HU-AIENG-003.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-003 / C03** — Cliente tipado .NET hacia `jbg-ai` (`IAiGatewayClient` + JWT interno HS256 + resiliencia Polly v8 + traza estructurada)

---

## Contexto y Problema

Tras C02 ([HU-AIENG-002](../../../../Documentos/Historias/AI-Eng/HU-AIENG-002.md), change archivado `add-ai-service-contracts-and-auth`), `jbg-ai` expone ocho rutas `/v1` con contrato congelado, stubs deterministas y autenticación HS256. **Nadie lo llama todavía.**

Del lado .NET no existe ninguna pieza de integración: verificado en el repositorio, el backend **no tiene ni un solo cliente HTTP saliente**, ni Polly, ni `Microsoft.Extensions.Http`. C03 construye ese primer cliente y, con él, fija los patrones que heredarán C12 (feeds de indexación), C15 (endpoint de búsqueda) y C34 (venta asistida y sustitutos).

El riesgo que este ticket ataca no es funcional sino de diagnóstico. La spec `ai-service-auth` obliga a `jbg-ai` a rechazar cualquier token dudoso con un **401 que no revela la causa**. Eso es correcto como decisión de seguridad y brutal como experiencia de depuración: un campo de más en el JWT, un desfase de reloj o un secreto mal copiado producen exactamente el mismo síntoma mudo. Por eso este ticket convierte esas tres trampas en criterios de aceptación con test, y no en comentarios de código.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `ai-service/openapi.json` versionado y ocho rutas `/v1` congeladas | Existe (C02) |
| Specs vivas `ai-service-api-contracts`, `ai-service-auth` | Existen (C02) |
| Servicio `jbg-ai` en `backend/docker-compose.yml`, puertos `8001:8000`, `JWT_SECRET` local | Existe (C02) |
| Cliente HTTP saliente en `backend/src/` (`AddHttpClient`, `IHttpClientFactory`) | **Ninguno en todo el backend** |
| Polly / `Microsoft.Extensions.Http.Resilience` en los cuatro `.csproj` | **Ausente** |
| `IAiGatewayClient`, DTOs de IA, `AiController` | **Ausente** |
| `JwtTokenService` (token de usuario, `Jwt:SecretKey`, firma con `iss` y `aud`) | Existe — **no reutilizable** para el token de servicio |
| `ICurrentUserService` (`UserId`, `Username`, `Role`, `IsAdmin`) | Existe — **no expone punto de venta** |
| `CurrentUserService` en `JoiabagurPV.API/Services/` | Existe — patrón a replicar para el acceso al `trace_id` |
| Correlación de trazas en el backend (`Activity`, `TraceIdentifier`) | **Ausente** |
| Serilog vía `ReadFrom.Configuration`, sink de consola con `outputTemplate` de texto | Existe — **sin formatter JSON** |
| `appsettings.Production.json` | **Ausente** |
| `FakeHttpMessageHandler` en `JoiabagurPV.Tests/TestHelpers/` | **Ausente** |
| `UserPointOfSale` y `ProductService.SearchProductsAsync` (filtra por **todos** los POS asignados) | Existen (MVP) |
| Artefactos OpenSpec de este change (proposal, specs, design, tasks) | **A generar** desde esta HU y este ticket |

**Impacto en producto:** ninguno visible para el operador. El valor es desbloquear C15 y, con él, el hito de la Ola 2: un operador buscando en lenguaje natural desde producción.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `backend/src/JoiabagurPV.Application/` | **Principal** — interfaces, DTOs, `AiCallScope`, emisor de token, cliente, opciones, excepciones y registro en DI |
| `backend/src/JoiabagurPV.API/` | `Program.cs` (una línea de registro), `appsettings.json` (sección `AiGateway`), `appsettings.Production.json` (nuevo, salida JSON de logs), `Services/TraceContextAccessor.cs`, `Extensions/ServiceCollectionExtensions.cs` |
| `backend/src/JoiabagurPV.Tests/` | `TestHelpers/FakeHttpMessageHandler.cs` y `TestHelpers/RepositoryRoot.cs` (nuevos, heredados por C12/C15/C34) y tres suites unitarias |
| `openspec/changes/add-dotnet-ai-gateway-client/` | Artefactos del change y este ticket |
| `openspec/specs/` | Nueva capability del cliente de IA en .NET, más un delta **MODIFIED** sobre el requisito `Structured Logging` de la capability `backend` (decisión 8) |
| `Documentos/Historias/AI-Eng/HU-AIENG-003.md` | Historia de usuario origen |
| `ai-service/` | **Sin cambios.** Se consume el contrato congelado; tocarlo rompería el snapshot y exigiría renegociación |
| `frontend/` | Sin impacto: la SPA nunca habla con Python |
| Base de datos / EF Core | Sin impacto: **no hay migración** en este change |
| `terraform/`, `.github/workflows/` | Sin impacto: despliegue y secretos en SSM son C17 |

---

## Especificaciones Técnicas

### Backend (.NET)

**Interfaz pública** (`JoiabagurPV.Application/Interfaces/`):

| Miembro | Firma |
|---|---|
| `IAiGatewayClient` | `Task<AiSearchResponse> SearchAsync(AiSearchRequest request, AiCallScope scope, CancellationToken ct)` |
| `IAiServiceTokenFactory` | `string Create(AiCallScope scope, string traceId)` |
| `ITraceContextAccessor` | `string CurrentTraceId { get; }` |

**Endpoint consumido** (uno, y solo uno):

| Método | Ruta | Auth | Notas |
|---|---|---|---|
| `POST` | `/v1/retrieval/products` | Bearer JWT interno | El servicio devuelve `min(top_k × 3, 60)` candidatos; el cliente **no trunca** |

**DTOs** (`JoiabagurPV.Application/DTOs/Ai/`), espejo del contrato congelado:

| DTO | Campos |
|---|---|
| `AiSearchRequest` | `query`, `top_k`, `filters`, `mode`. **Sin `pos_id`**: el contrato lo acepta pero lo ignora, y no enviarlo evita sugerir que el body manda |
| `AiSearchFilters` | `materials`, `category`, `family_id`, `exclude_product_ids` |
| `AiSearchResult` | `product_id`, `sku`, `score`, `match_reasons`, `materials`, `family_id?`, `variant_label?`, `debug?` |
| `AiSearchResponse` | `results`, `candidates_returned`, `low_confidence`, `trace_id`, `effective_pos_id` |
| `AiDebugInfo` | `vector_score?`, `lexical_score?`, `rerank_score?`, `notes` |

Serialización con un único `JsonSerializerOptions` y política de nombres `snake_case`, sin atributos por propiedad. `family_id` y `variant_label` son nulables de verdad: el contrato garantiza `null`, no ausencia.

**`AiCallScope`** (`DTOs/Ai/AiCallScope.cs`): `UserId`, `Role`, `PointOfSaleId`, con **única** fábrica `ForPointOfSale(userId, role, pointOfSaleId)` que rechaza `Guid.Empty` y rol en blanco. No autoriza nada: quien lo construye ya ha validado la asignación contra `UserPointOfSale` (eso es C15).

**Token interno de servicio:**

| Aspecto | Valor |
|---|---|
| Algoritmo | HS256 con `AiGateway:JwtSecret` (secreto propio, distinto de `Jwt:SecretKey`) |
| Claims | `user_id`, `role`, `pos_id`, `trace_id` — nombres literales en `snake_case` |
| `exp` | Ahora + `TokenTtlSeconds` (por defecto `300`, alineado con `JWT_TTL_SECONDS` de C02) |
| `aud`, `iss`, `nbf` | **No se emiten** |
| Reloj | `TimeProvider` inyectado, para test con reloj falso |

**Opciones** (`JoiabagurPV.Application/Configuration/AiGatewayOptions.cs`, sección `AiGateway`):

| Clave | Obligatoria | Default | Notas |
|---|---|---|---|
| `BaseUrl` | sí | — | `http://localhost:8001` en desarrollo (el backend .NET no está en el Compose y solo ve el puerto publicado). En producción, **valor previsto** `http://jbg-ai:8000`, condicionado al prerrequisito de red que fija C17 — ver Arquitectura |
| `JwtSecret` | sí | — | Debe coincidir **literalmente** con `JWT_SECRET` del servicio `jbg-ai` |
| `TokenTtlSeconds` | no | `300` | |
| `RetrievalTimeoutMs` | no | `800` | Diseño v3 §6.4 |
| `AssistTimeoutMs` | no | `5000` | Reservado para C34 |
| `Enabled` | no | `true` | Permite desactivar el registro del cliente |

**Dónde viven los valores.** La cadena de precedencia de ASP.NET es `appsettings.json` → `appsettings.{Environment}.json` → variables de entorno. En desarrollo la sección vive en `appsettings.json`, siguiendo el estilo de la casa (ese fichero ya lleva la cadena de conexión a `localhost:5433` y un secreto JWT de desarrollo). En producción **no se usan ficheros**: [user_data.sh](../../../../terraform/templates/user_data.sh) lee SSM e inyecta variables de entorno con `__` como separador de sección (`ConnectionStrings__DefaultConnection`, `Jwt__SecretKey`…). C17 no tiene nada que inventar, los parámetros son:

| Parámetro SSM | Tipo | Clave de configuración |
|---|---|---|
| `/jpv/prod/AiGateway__BaseUrl` | String | `AiGateway:BaseUrl` |
| `/jpv/prod/AiGateway__JwtSecret` | SecureString | `AiGateway:JwtSecret` |

**Validación con `ValidateOnStart()`:** `BaseUrl` presente y URI absoluta, `JwtSecret` no vacío y con longitud suficiente para HS256, TTL y timeouts positivos. El mensaje de error nombra la clave y recuerda la correspondencia con el contenedor.

> **Matiz importante — el límite del fail-fast.** `ValidateOnStart()` detecta *ausente* y *malformado*, **no** *presente pero equivocado*. Si en producción faltara `AiGateway__BaseUrl`, la aplicación caería al valor de `appsettings.json` (`http://localhost:8001`), que es una URI absoluta válida: pasaría la validación y fallaría después con conexión rechazada. Mitigación en C03: incluir `base_url` como campo del evento `ai_gateway_call_failed`, para que el diagnóstico diga a dónde estaba apuntando. Mitigación definitiva: el `/health` enriquecido y la tarjeta del dashboard que entrega C17.

**Resiliencia** (`Microsoft.Extensions.Http.Resilience`, Polly v8), *named client* `ai-retrieval`:

| Estrategia | Configuración |
|---|---|
| Timeout | 0,8 s |
| Retry | `MaxRetryAttempts = 1`, backoff corto |
| Predicado de reintento | Fallos de transporte, timeout, 408 y 5xx **excepto 501** |
| Circuit breaker | Umbrales y ventana **explícitos** |

No se usa `AddStandardResilienceHandler()` sin configurar: sus valores por defecto (30 s totales, 3 reintentos) contradicen el diseño. Se deja preparado un segundo cliente `ai-assist` (5 s, breaker propio) para C34: **breakers independientes**, para que un modelo de lenguaje lento no abra el circuito de la búsqueda y dispare el fallback léxico de C15 sin motivo.

**Mapa de errores** (los errores son parte del contrato — S15 «Partir en servicios»):

| Respuesta | Traducción | ¿Reintenta? |
|---|---|---|
| 200 | `AiSearchResponse` | — |
| 401 | `AiGatewayConfigurationException`, log nivel `Error` | **Nunca** — es configuración, no algo transitorio |
| 501 | `AiNotImplementedException` | **Nunca** — C02 eligió 501 en vez de 503 precisamente para esto |
| 408 y 5xx salvo 501 | `AiUnavailableException` | Sí, **una vez** |
| Timeout, fallo de red, breaker abierto | `AiUnavailableException` | Fail-fast si el breaker está abierto |

Excepciones en `JoiabagurPV.Application/Exceptions/` con base común `AiGatewayException` (precedente: `Domain/Exceptions/DomainException.cs`).

**Observabilidad:** `ILogger<AiGatewayClient>` con plantillas semánticas y `BeginScope` para fijar `trace_id` y `endpoint` una sola vez por llamada.

| Evento | Campos |
|---|---|
| `ai_gateway_call_started` | `endpoint`, `trace_id`, `pos_id`, `role`, `top_k`, `query_length` |
| `ai_gateway_call_completed` | `endpoint`, `trace_id`, `status_code`, `latency_ms`, `attempts`, `candidates_returned`, `results_count`, `low_confidence` |
| `ai_gateway_call_failed` | `endpoint`, `trace_id`, `outcome`, `latency_ms`, `attempts`, `base_url` |

`outcome` ∈ `timeout` \| `circuit_open` \| `not_implemented` \| `unauthorized` \| `server_error` \| `transport`. El **texto de la consulta solo se registra en nivel `Debug`** (diseño v3 §8.5: ningún dato personal accidental en logs de producción). No hay tokens ni coste que registrar: C03 no llama a ningún modelo de lenguaje; eso llega con `usage` en C34.

`base_url` solo se emite en el evento de fallo: es donde hace falta —saber a qué dirección estaba apuntando— y evita ruido en el camino feliz.

Salida JSON bajo perfil de producción con `Serilog.Formatting.Compact`, en `appsettings.Production.json`. Patrón dual del máster (S3, «Observabilidad, logging y trazabilidad»): consola legible en desarrollo, JSON ingerible en producción. `ASPNETCORE_ENVIRONMENT=Production` ya viene fijado tanto en `Dockerfile.bundled` como en el `docker run` de `jpv-deploy.sh`, así que el fichero se carga sin trabajo adicional de infraestructura.

**Reparto entre capabilities (decisión 8):** los tres eventos, la correlación por `trace_id` y la regla de la consulta en `Debug` se especifican en la capability nueva del cliente, porque son el contrato de correlación con `jbg-ai`. El render dependiente del entorno amplía el requisito `Structured Logging` que ya existe en `backend`.

**Correlación:** `ITraceContextAccessor` en `Application`, implementado en `JoiabagurPV.API/Services/TraceContextAccessor.cs` siguiendo el patrón de `CurrentUserService` (`Activity.Current?.TraceId`, y `HttpContext.TraceIdentifier` como respaldo). El valor viaja en el claim **y** en la cabecera `X-Trace-Id`: C02 prefiere el claim, pero la cabecera es lo único que correlaciona `/health` y las respuestas 401.

**Layout propuesto:**

```text
backend/src/JoiabagurPV.Application/
  Configuration/AiGatewayOptions.cs
  DTOs/Ai/{AiSearchRequest,AiSearchFilters,AiSearchResult,AiSearchResponse,AiDebugInfo,AiCallScope}.cs
  Exceptions/{AiGatewayException,AiUnavailableException,AiNotImplementedException,AiGatewayConfigurationException}.cs
  Interfaces/{IAiGatewayClient,IAiServiceTokenFactory,ITraceContextAccessor}.cs
  Services/{AiGatewayClient,AiServiceTokenFactory}.cs
  Extensions/AiGatewayServiceCollectionExtensions.cs
backend/src/JoiabagurPV.API/
  Services/TraceContextAccessor.cs
  appsettings.json (sección AiGateway) · appsettings.Production.json (nuevo)
backend/src/JoiabagurPV.Tests/
  TestHelpers/{FakeHttpMessageHandler,RepositoryRoot}.cs
  UnitTests/Application/{AiGatewayClientTests,AiServiceTokenFactoryTests,AiContractSnapshotTests}.cs
```

### Fuera de este ticket

- `AiController`, `POST /api/ai/search`, hidratación de precio y stock, descarte tras hidratar, repetición con `top_k` mayor, fallback léxico y feature flag por punto de venta → **C15**.
- Los otros siete endpoints del contrato → el change que los consuma (C34, C13, C08).
- Firma de tokens sin punto de venta, para rutas de catálogo global → primer change que la necesite entre C08 y C13.
- `ProductAiProfile` → C08. Feeds de indexación → C12. Esquema `ai` → C05.
- Despliegue, `BaseUrl` de producción y secretos en SSM → C17.

---

## Arquitectura

- **Frontera:** SPA → JWT de usuario → API .NET → **JWT interno de servicio** → `jbg-ai` (diseño v3 §6.1 y §6.4). Regla de una frase: *Python calcula parecidos y redacta; .NET calcula números y decide*. Este ticket construye exactamente la flecha del medio.
- **Degradación:** el diseño exige que el sistema nunca se caiga por culpa de la IA. C03 entrega la mitad baja de esa promesa (timeout, reintento único, breaker y excepciones distinguibles); la mitad alta —responder con el buscador léxico y `ai_available: false`— es C15.
- **Patrones:** typed `HttpClient` con `IHttpClientFactory`, pipeline de resiliencia declarativo, `IOptions<>` con validación en el arranque, interfaz en `Application` implementada por `API` para lo que depende de `HttpContext` (precedente: `ICurrentUserService` / `CurrentUserService`).
- **Restricción de capas:** el cliente vive en `Application` y no en `Infrastructure` porque `JoiabagurPV.Infrastructure.csproj` solo referencia a `Domain`; implementarlo allí obligaría a subir los DTOs de IA al dominio de joyería. Merece constancia escrita: es la clase de decisión que alguien intentará «corregir» más adelante y se estrellará con una referencia circular.
- **Capabilities OpenSpec:** nueva capability para el cliente de IA en .NET, **más un delta `MODIFIED` sobre el requisito `Structured Logging` de `backend`** (decisión 8). El reparto: lo que pertenece al salto .NET↔Python —`trace_id` en claim y cabecera, los tres eventos, la consulta solo en `Debug`— vive en la capability nueva; lo global —render legible en desarrollo y JSON en producción, y correlación también en llamadas **salientes**— amplía el requisito que ya existe en `backend`.
- **Breaking changes:** ninguno. No cambia ningún contrato REST existente ni el snapshot de `jbg-ai`. `appsettings.json` gana una sección nueva, y el fail-fast implica que un despliegue sin esa sección no arranca — documentado en el DoD.
- **ADRs:** este repositorio no tiene `memory-bank/`; las decisiones equivalentes viven en `openspec/changes/archive/*/design.md` y en la tabla de decisiones de `Documentos/arquitectura.md`.

### Topología de red: la doble dirección del servicio

**Desarrollo (verificado).** El backend .NET corre en el host, no en Compose. `backend/docker-compose.yml` levanta `postgres` (publicado en 5433), `pgadmin` (8080) y `jbg-ai` (8000 → publicado **8001**) en `jpv-network`. Por eso `appsettings.json` ya apunta la base de datos a `localhost:5433`, y por eso la dirección del servicio de IA es `http://localhost:8001`.

La asimetría —infraestructura en Compose, código que editas en el host— es deliberada y está respaldada por el spec vivo: [backend/spec.md:170](../../../specs/backend/spec.md) especifica *«Hot Reload Development: WHEN code changes are made THEN application automatically restarts»*, que es el bucle de `dotnet watch` en el host. Meter la API en Compose rompería ese bucle y obligaría a cambiar la cadena de conexión de todos los desarrolladores. **No se hace.** Si en el futuro alguien quiere levantar la pila completa sin depurador, la vía limpia es un perfil opcional de Compose (`--profile full`), fuera del `up` por defecto y fuera de C03.

**Producción (verificado).** No hay Docker Compose en producción. `deploy-aws-ec2.yml` construye `Dockerfile.bundled`, lo empuja a ECR y dispara por SSM el script `jpv-deploy.sh` de [user_data.sh](../../../../terraform/templates/user_data.sh), que hace `docker run -d --name jpv-api -p 8080:8080` **sin `--network`**, es decir sobre la red *bridge* por defecto. Nginx hace de proxy TLS contra `127.0.0.1:8080`, y la base de datos es RDS, fuera de la instancia.

> ⚠️ **Prerrequisito para C17, no un hecho de hoy.** En la red *bridge* por defecto de Docker **los contenedores no se resuelven por nombre**: el DNS embebido solo funciona en redes definidas por el usuario. Tal como está el despliegue hoy, `http://jbg-ai:8000` **no resolvería**. Para que el valor de producción sea cierto, C17 debe:
>
> 1. `docker network create jpv-net` (o equivalente en Terraform / *user data*).
> 2. Añadir `--network jpv-net` a los `docker run` de `jpv-api` y de `jbg-ai`.
> 3. **No publicar** el puerto de `jbg-ai`, para que siga siendo inalcanzable desde nginx y desde fuera (diseño v3 §6.4).
> 4. Crear los dos parámetros SSM de la tabla anterior.
>
> **Valoración:** no hace falta introducir Compose en producción. Lo único que se necesita es resolución por nombre y aislamiento, y ambas cosas las dan una red de usuario y un puerto sin publicar. Compose obligaría a instalarlo en la EC2, reescribir `jpv-deploy.sh` y gestionar un fichero con secretos en la instancia, para dos contenedores; el reinicio ordenado ya lo cubre `--restart unless-stopped`. **Punto de revisión:** si el despliegue llega a tener tres o cuatro contenedores, Compose empieza a compensar.

```text
DESARROLLO                              PRODUCCIÓN (tras C17)
host: dotnet run                        EC2
  ├── BD → localhost:5433                 ├── nginx TLS → 127.0.0.1:8080
  └── IA → localhost:8001                 └── docker network jpv-net
docker · jpv-network                          ├── jpv-api :8080 (publicado)
  ├── postgres :5432 → 5433                   │     └── IA → http://jbg-ai:8000
  ├── pgadmin  :80   → 8080                   └── jbg-ai  :8000 (SIN publicar)
  └── jbg-ai   :8000 → 8001               RDS PostgreSQL (fuera de la EC2)
```

**Deuda de documentación detectada (para C17, no para este change).** `backend/docker-compose.prod.yml` **no lo invoca ningún workflow, ni Terraform, ni script alguno**, pero [backend/README.md:435](../../../../backend/README.md) sí lo documenta bajo el epígrafe *«Production Deployment › Docker»*. Además construye `src/JoiabagurPV.API/Dockerfile` en lugar del `Dockerfile.bundled` que usa producción, y declara un contenedor Postgres propio cuando producción usa RDS. Su último cambio es de 2026-01-17, el commit que movió producción a la imagen bundlada: sobrevivió al refactor sin borrarse. No es código muerto —está referenciado— sino un **camino de despliegue obsoleto que la documentación sigue presentando como el de producción**, lo que induce a error a quien lea el README buscando cómo funciona. Recomendación: C17 lo borra o lo marca deprecado **y corrige el README en el mismo movimiento**. Contexto colateral: `Dockerfile.prod` solo lo usa `deploy-backend-aws.yml`, que el propio workflow activo declara deprecado.

```text
C15 (futuro) --SearchAsync(request, scope)--> AiGatewayClient
                                               ├─ AiServiceTokenFactory: HS256, 4 claims snake_case,
                                               │    sin aud / iss / nbf, exp = now + TTL
                                               ├─ Authorization: Bearer <jwt>  +  X-Trace-Id
                                               ├─ pipeline: timeout 0,8s → retry ×1 → breaker
                                               └─ POST /v1/retrieval/products
                                                    ├─ 200 → AiSearchResponse
                                                    ├─ 401 → AiGatewayConfigurationException (sin reintento)
                                                    ├─ 501 → AiNotImplementedException  (sin reintento)
                                                    └─ 408/5xx/timeout → AiUnavailableException
```

---

## Criterios de Aceptación

Condiciones verificables para dar el ticket por hecho:

1. `SearchAsync` mapea una respuesta 200 completa, incluidos `candidates_returned`, `low_confidence` y `effective_pos_id`, y respeta los nulos de `family_id` y `variant_label`.
2. El token emitido lleva los cuatro claims obligatorios con nombres literales en `snake_case` y **no** lleva `aud`, `iss` ni `nbf`.
3. `AiCallScope` no puede construirse sin un punto de venta real y un rol no vacío.
4. Timeout, fallo de transporte y circuito abierto se traducen a la excepción de servicio no disponible; con el circuito abierto no se emite ninguna petición HTTP.
5. Un 501 y un 401 se propagan como excepciones distinguibles y **sin reintento**; un 503 se reintenta exactamente una vez.
6. Arrancar sin `AiGateway:JwtSecret`, o con un `BaseUrl` que no sea URI absoluta, falla de inmediato nombrando la clave.
7. Cada llamada emite traza estructurada correlacionable por `trace_id`, y el texto de la consulta no aparece por encima de nivel `Debug`.
8. El render de los logs depende del entorno: consola legible bajo perfil de desarrollo, JSON de una línea por evento bajo perfil de producción.
9. Los DTOs coinciden con el `ai-service/openapi.json` committeado en nombre y nulabilidad.
10. `dotnet build` y `dotnet test` en verde, sin regresión y **sin necesidad de levantar `jbg-ai`** ni acceso a red.

**Pruebas de validación** (`dotnet test` desde `backend/src/`):

| Test | Cubre |
|---|---|
| `SearchAsync_WhenServiceReturns200_MapsResponse` | Criterio 1 |
| `SearchAsync_WhenFamilyIdIsNull_MapsToNullWithoutThrowing` | Criterio 1 |
| `BuildToken_IncludesPosAndRoleClaims` | Criterio 2 |
| `BuildToken_UsesSnakeCaseClaimNames` | Criterio 2 |
| `BuildToken_OmitsAudienceAndIssuer` | Criterio 2 — blinda el 401 opaco por audiencia |
| `BuildToken_ExpiresAfterConfiguredTtl` | Criterio 2 |
| `ForPointOfSale_WhenPointOfSaleIsEmpty_ThrowsArgumentException` | Criterio 3 |
| `SearchAsync_WhenTimeout_ThrowsAiUnavailable` | Criterio 4 |
| `SearchAsync_WhenCircuitOpen_FailsFastWithoutCall` | Criterio 4 |
| `SearchAsync_WhenServiceReturns501_DoesNotRetryAndThrowsNotImplemented` | Criterio 5 |
| `SearchAsync_WhenServiceReturns401_DoesNotRetry` | Criterio 5 |
| `SearchAsync_WhenServiceReturns503_RetriesOnceThenSucceeds` | Criterio 5 |
| `AddAiGateway_WhenSecretMissing_FailsOnStart` | Criterio 6 |
| `SearchAsync_SendsBearerTokenAndTraceHeader` | Criterio 7 |
| `Dtos_MatchCommittedOpenApiSchema` | Criterio 9 |

El **criterio 8** no se cubre con un test unitario: es configuración de Serilog, y verificarla en proceso probaría el binder, no el render. Se comprueba arrancando la API con `ASPNETCORE_ENVIRONMENT=Production` y observando que la salida es JSON de una línea por evento. Queda anotado en el DoD como verificación manual.

> **Aviso sobre el test del breaker.** Con los valores por defecto de Polly v8, el circuito usa ventana de muestreo y mínimo de llamadas: un test que provoque dos fallos y compruebe el estado abierto **pasará en verde sin que el circuito llegue a abrirse**. Hay que configurar umbrales bajos explícitos en el pipeline de test o forzar el estado.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec del change generados y coherentes con HU-AIENG-003 y este ticket
- [ ] Código implementado según el layout y las decisiones de este ticket, respetando las capas de `Documentos/modelo-c4.md`
- [ ] Los quince tests de la tabla anterior en verde con `dotnet test`, nomenclatura `Método_Escenario_ResultadoEsperado`
- [ ] Sin llamadas de red reales en la suite: `FakeHttpMessageHandler` en todos los tests del cliente
- [ ] Suite existente sin regresión, incluidos los tests de integración con `WebApplicationFactory` (que ahora arrancan con `ValidateOnStart` activo)
- [ ] `appsettings.json` con la sección `AiGateway` y el secreto local **idéntico** al de `backend/docker-compose.yml`
- [ ] `appsettings.Production.json` con la salida JSON de Serilog, en la forma con clave para que el override no deje colgando los `Args` del fichero base
- [ ] **Verificación manual del criterio 8:** arrancar con `ASPNETCORE_ENVIRONMENT=Production` y comprobar que la salida es JSON de una línea por evento
- [ ] Spec de la capability nueva creada en `openspec/changes/add-dotnet-ai-gateway-client/specs/`, **más el delta `MODIFIED` sobre `Structured Logging` de `backend`**
- [ ] `openspec validate --all --strict` con `0 failed` — la forma `--all`, no la de un único change: este change toca un spec vivo
- [ ] `ai-service/` intacto y `ai-service/openapi.json` sin modificar: si el contrato tuviera que cambiar, se negocia y se abre un change propio
- [ ] Documentación actualizada según la tabla *Post-Implementation Documentation Update* de `openspec/project.md`
- [ ] Sin `TODO` ni `FIXME` sin tarea de seguimiento asociada
- [ ] Sin impacto en UI: no aplica la regla de es-ES / EUR en este change

---

## Requisitos No Funcionales

- **Seguridad:** el secreto del token de servicio nunca se committea fuera del placeholder local de desarrollo (producción vía SSM `/jpv/prod/*` en C17); el token es hop-to-hop con TTL corto (300 s) sobre la red interna de Docker; el puerto de `jbg-ai` no se publica en nginx. El cliente **no** decide permisos: transporta un ámbito ya validado y el servicio aplica el suyo desde el token.
- **Privacidad:** el texto de la consulta del operador solo se registra en nivel `Debug`. Ningún dato personal entra en un log de producción (diseño v3 §8.5).
- **Rendimiento:** presupuesto de 0,8 s para recuperación, coherente con el objetivo p95 < 500 ms del diseño (3devs §6.8); reintento único para no multiplicar el peor caso; el cliente no añade E/S propia más allá de la llamada HTTP.
- **Disponibilidad y degradación:** ningún fallo del servicio de IA puede propagarse como error no controlado al operador. C03 garantiza que el fallo llega tipado y acotado en el tiempo; C15 lo convierte en respuesta degradada.
- **Observabilidad:** logging estructurado con Serilog, `trace_id` propagado en claim y cabecera, latencia e intentos por llamada. Sin dependencias de observabilidad externas: OpenTelemetry, Logfire o Langfuse quedan documentados como alternativa para C17/C39, no se adoptan aquí.
- **Contrato:** el test de contrato del lado .NET es el recíproco de `test_openapi_snapshot_is_stable`. A partir de este change, renegociar el contrato rompe **los dos** builds, que es exactamente lo que se pretende.
- **Free-tier:** sin impacto en el pool de conexiones a base de datos ni en el bundle del frontend. Este change no toca ninguno de los dos.

---

## Preguntas Abiertas → Decisiones

**Cerradas antes de generar los artefactos OpenSpec:**

1. **Anchura del cliente → solo `SearchAsync`.**
   C02 congeló ancho el contrato con un buen argumento: reabrir un contrato *de cable* cuesta una negociación entre dos personas. Ese argumento **no se traslada** a un método C#, que se añade con un diff pequeño y sin negociar con nadie. Mapear los ocho endpoints ahora produciría unos veinticinco DTOs, la mitad sin consumidor hasta la Ola 4, en un change de ruta crítica que debe caber en una sesión. La anchura crece en el change que la consuma.

2. **Ubicación del cliente → `JoiabagurPV.Application`.**
   El instinto dice `Infrastructure` (es E/S externa, y el precedente más cercano es `S3FileStorageService`), pero `JoiabagurPV.Infrastructure.csproj` solo referencia a `Domain`: implementarlo allí obligaría a declarar `IAiGatewayClient` y sus DTOs en el dominio. Un `AiSearchResult` con `match_reasons` y `variant_label` no es dominio de joyería. Precedentes en `Application`: `ImageRecognitionService`, `JwtTokenService`.

3. **Forma del fallo → excepciones tipadas, no tipo resultado.**
   Reconocido como trade-off: «circuito abierto» es un modo de operación previsto, no excepcional, y usar excepciones para control de flujo esperado tiene mal olor. Se acepta porque C15 tiene un único punto de llamada, el `try/catch` es local, y los nombres de test ya están pactados en la ficha C03 del plan.

4. **Reutilizar `JwtTokenService` → no.**
   Otro secreto, otros claims, otro TTL y otro destinatario. Además, ese servicio firma con emisor y audiencia, y un `aud` en el token de servicio provoca rechazo sistemático en `jbg-ai` con un 401 que la spec obliga a no explicar.

**Cerradas en la revisión del 2026-08-09 (se aplicó la opción por defecto en 5, 6 y 7):**

5. **¿Cómo se firma un token para rutas sin punto de venta? → Se aplaza, con dueño nombrado.**
   El contrato exige `pos_id` en las ocho rutas, pero `POST /v1/enrich/products` es de catálogo global y `POST /v1/index/sync` lo dispara un proceso, no una persona en una tienda.
   **Decisión:** C03 **no** lo resuelve. Solo existe la fábrica `ForPointOfSale`, de modo que ningún valor centinela puede colarse en el filtro duro que C22 construirá sobre `pos_id`. El primer change que necesite un token administrativo —C08 o C13, el que llegue antes— añadirá la fábrica correspondiente **y**, en el mismo change, la regla del lado Python que impida a ese ámbito alcanzar las rutas de recuperación. Reabrir ahora la spec `ai-service-auth` significaría trabajo en zona Python dentro de un change marcado «.NET» y en ruta crítica.

6. **Versión de `Microsoft.Extensions.Http.Resilience` compatible con `net10.0` → la última estable compatible.**
   Verificada al implementar. Si hubiera fricción real, la alternativa documentada es `Polly.Extensions.Http` con `AddPolicyHandler`, a coste de usar el patrón antiguo.

7. **Forma de sobreescribir el sink de Serilog por entorno → forma con clave.**
   `ReadFrom.Configuration` fusiona el array `WriteTo` por índice, así que un fichero de producción que redefina la consola puede dejar colgando los `Args` del fichero base (`theme`, `outputTemplate`). Se usa `"WriteTo": { "console": { … } }` para que el override reemplace limpiamente esa entrada; comportamiento a verificar en la primera ejecución.

8. **¿El formato de logs es delta sobre `backend`, capability nueva o detalle de implementación? → Repartido: capability nueva + delta `MODIFIED` sobre `backend`.**

   **El dato que decide.** La capability `backend` **ya tiene** un requisito `Structured Logging` ([backend/spec.md:62](../../../specs/backend/spec.md)): *«…using Serilog, capturing relevant context and supporting **multiple output targets**»*, con un escenario *Request Logging* que exige registrar *«request details… **with correlation ID**»*. Dos consecuencias: el formatter JSON no añade un requisito nuevo, **cumple uno ya escrito**; y el escenario del identificador de correlación está especificado y **no implementado** —no hay un solo uso de `Activity` ni de `TraceIdentifier` en `backend/src/`—, así que C03 es el primer change que reduce esa deriva.

   **Por qué no una capability nueva.** `backend-observability` partiría el tema en dos: el requisito de logging estructurado seguiría en `backend` y el nuevo viviría al lado. Empeora la descubribilidad en vez de mejorarla, y ensancha C03 a dos capabilities en un change de ruta crítica.

   **Por qué no detalle de implementación.** Dejaría intacta la deriva del identificador de correlación, y el precedente del repositorio lo contradice: `ai-service-dev-compose` es literalmente una capability sobre un fichero de Compose, así que «la infraestructura no se especifica» no es la convención de esta casa. Además, sin requisito que lo respalde, un change futuro puede revertir el formato sin que falle ningún test.

   **El reparto que hace la decisión fácil.** Lo que pertenece al salto .NET↔Python —`trace_id` en claim y cabecera, los tres eventos `ai_gateway_call_*`, la consulta solo en `Debug`— es el contrato de correlación con `jbg-ai` y va en la **capability nueva**, que es donde alguien lo buscará. Solo el render global va como **delta `MODIFIED`** sobre `Structured Logging`, quirúrgico: hacer explícito que el render depende del entorno y ampliar el escenario de correlación para que cubra también las llamadas **salientes**, no solo las peticiones entrantes.

   **Nota operativa.** Al llevar delta sobre un spec vivo, hay que ejecutar `openspec validate --all --strict` antes de archivar, no solo la forma de un único change: es exactamente el escenario en el que este repositorio ya se rompió una vez (ver `CLAUDE.md`).

**Abiertas:** ninguna que bloquee el apply. El prerrequisito de red de producción no es una pregunta de C03: está documentado en Arquitectura como requisito nombrado sobre C17.

---

## Prioridad / Estimación / Tags

- **Prioridad:** Alta — Ola 0, ruta crítica 🔴. Bloquea C15 y, en cascada, C16, C17 y C34. El hito de la Ola 2 (operador buscando en lenguaje natural desde producción el 19 de agosto) depende de esta pieza.
- **Estimación:** **5 SP** (propuesta del PO, a validar en refinamiento). Superficie estrecha —un solo método— pero infraestructura enteramente nueva: primer cliente HTTP saliente, primer pipeline de resiliencia y primer emisor de token de servicio del backend.
- **Tags:** `HU-AIENG-003`, `C03`, `jbg-ai`, `dotnet`, `http-client`, `resilience`, `polly`, `jwt`, `observability`, `contracts`, `feature`, `tests`
- **Asignación:** cualquiera de los dos desarrolladores del PF (regla del plan: coger el 🔴 libre).
- **Conflictos de zona:** ninguno. `AiController` no existe todavía, así que C03 puede ejecutarse en paralelo a C04 sin colisión. La regla de «una sola migración EF Core activa» no aplica: este change no lleva migración.

---

## Enlaces o Referencias

- **User Story:** [HU-AIENG-003.md](../../../../Documentos/Historias/AI-Eng/HU-AIENG-003.md)
- **HU prerrequisito:** [HU-AIENG-002.md](../../../../Documentos/Historias/AI-Eng/HU-AIENG-002.md) (change archivado `add-ai-service-contracts-and-auth`)
- **Change:** `openspec/changes/add-dotnet-ai-gateway-client/`
- **Plan:** ficha C03 en [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Diseño:** [v3](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) §6.1–6.4 (frontera, seguridad y degradación), §7.6 (sobre-recuperación), §8.5 (privacidad) · [3devs](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) §6.6 (observabilidad), §6.8 (latencias objetivo)
- **Contrato congelado:** `ai-service/openapi.json` · specs vivas `openspec/specs/ai-service-api-contracts/spec.md` y `openspec/specs/ai-service-auth/spec.md`
- **Épica:** EP11 en [epicas.md](../../../../Documentos/epicas.md)
- **Material del máster:** `Documentos/Sesiones Master AIEng/S3_Patrones_Diseños_Wrappers_Modelos/` («Observabilidad, logging y trazabilidad», «Abstracción de proveedores y estrategias de fallback») · `S15_Produccion/Partir en servicios.md` (los errores como parte del contrato)
- **Contexto de proyecto:** `openspec/project.md`
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-08-08 | Creación del ticket enriquecido al abrir el change C03, con el estado del código verificado en el repositorio, el mapa de errores del contrato, las trampas del token de servicio y las cuatro decisiones cerradas más cuatro preguntas abiertas con opción por defecto |
| 2026-08-09 | Cerradas las preguntas 5, 6 y 7 con su opción por defecto. Pregunta 8 resuelta como reparto (capability nueva + delta `MODIFIED` sobre `Structured Logging` de `backend`) tras comprobar que ese requisito ya existe y que su escenario de identificador de correlación no está implementado. Nueva sección de topología de red con desarrollo y producción verificados, el prerrequisito de red de usuario para C17 y los parámetros SSM. Añadidos el criterio 8 (render por entorno), el campo `base_url` en el evento de fallo y el matiz sobre el límite del fail-fast. Documentada la deuda de `backend/docker-compose.prod.yml` tras verificar que ningún automatismo lo usa pero el README sí lo documenta |
