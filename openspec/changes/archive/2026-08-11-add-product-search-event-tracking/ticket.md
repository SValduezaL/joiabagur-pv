# T-AIENG-004: Product search event tracking — query→selection telemetry (C04)

> Ticket técnico del change OpenSpec `add-product-search-event-tracking`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, `Documentos/` (diseño RAG, plan de changes y especificaciones funcionales v2), specs vivas de `openspec/specs/`, el contrato congelado `ai-service/openapi.json` y [HU-AIENG-004](../../../../Documentos/Historias/AI-Eng/HU-AIENG-004.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-004 / C04** — Entidad `ProductSearchEvent`, migración, servicio de registro en dos caminos y endpoint de selección (`POST /api/ai/search-events/{id}/selection`)

---

## Contexto y Problema

Cerrada la Ola 0 con C01, C02 y C03, el backend .NET ya sabe hablar con `jbg-ai` pero **no guarda ninguna huella de lo que los operadores buscan ni de lo que eligen**. Seis de los KPIs de las especificaciones funcionales v2 §5.11 —tiempo búsqueda→selección, porcentaje de ventas iniciadas desde búsqueda asistida, porcentaje de consultas sin resultado, selección en rank 1/3, ticket medio asistido frente a no asistido, y ventas con sustituto sugerido— no tienen hoy ningún soporte de datos.

El diseño v3 §15.3 fija la barra con precisión: *«los KPIs de negocio están **instrumentados**, no medidos»*. Instrumentado significa que el dato se captura aunque nadie lo mire; no significa que se pueda inferir después con un `JOIN` difuso por usuario, punto de venta, producto y ventana temporal —que es lo único que quedaría sin esta tabla, y que produce falsos positivos en el caso más frecuente del negocio: vender dos veces el mismo artículo.

Hay un segundo problema, menos evidente. El diseño v3 §6.4 obliga a que, con el circuito abierto, .NET responda con el **buscador léxico existente** y `ai_available: false`. Si esas búsquedas degradadas no se distinguen de las asistidas en la telemetría, una semana con el cortacircuitos abriéndose se leería como *«la IA rankea peor»* cuando la IA sencillamente no corrió. Distinguirlas da además, gratis y en producción, la comparación **v0-léxico frente a v3** que §11.2 solo contempla offline sobre 60-70 consultas etiquetadas a mano.

Y un tercero, de calendario. Este es el **primer change con migración de EF Core** del Proyecto Final, de seis previstos, y la regla 4 del plan permite **una sola migración activa a la vez**. La primera paga un coste fijo de utillaje —no existe ni un test de migración en todo el repositorio— que las otras cinco no pagarán. Ese coste debe caer en el change que no bloquea a nadie.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| Entidad `ProductSearchEvent`, enum `SearchOrigin`, su repositorio | **Ausentes** en `JoiabagurPV.Domain` |
| `Sale.SearchEventId` | **Ausente**; `Sale` tiene 10 propiedades y 6 navegaciones |
| Cualquier ruta bajo `api/ai/*` | **Ninguna**; 18 controllers, ninguno de IA |
| Migraciones de EF Core | 14, la última `20260322113038_AddProductPhotoEmbeddings` |
| Tests de migración o aserciones de esquema | **Ninguno.** `Migrat` solo aparece en `TestDatabaseFixture.MigrateAsync()` |
| Columnas `jsonb` en todo el modelo | **Ninguna.** El único `HasColumnType` es `text` en `ProductPhotoEmbeddingConfiguration` |
| `TestDatabaseFixture` (Testcontainers `postgres:15` + Respawn, expone `ConnectionString`) | Existe — **el arnés se apoya en él, no necesita infraestructura nueva** |
| `AiCallScope` con fábrica única `ForPointOfSale(...)` | Existe (C03) — **se reutiliza como garantía de ámbito validado** |
| `AiSearchResult` / `AiSearchFilters` / `AiSearchResponse.TraceId` | Existen (C03) — **la proyección se deriva de ellos, no se inventa** |
| `AiRetrievalMode` (`Hybrid`/`Vector`/`Lexical`) | Existe (C03) — **no reutilizable**: describe la estrategia interna de `jbg-ai`, no el origen de los resultados que vio el operador |
| Patrón de validación de punto de venta (`IUserPointOfSaleRepository.HasAccessAsync` + `UnauthorizedAccessException` → `Forbid()`) | Existe (`DashboardService` / `DashboardController`) |
| `ApplicationDbContext.SaveChangesAsync` pisa `UpdatedAt` en cada guardado | Existe — **por eso `SelectedAt` es columna propia** |
| `BaseController` con `[Route("api/v1/[controller]")]` | Existe y **nadie lo hereda**. Andamiaje muerto; no se toca en este change |
| Limitador de peticiones | Configurado, con una sola política (`LoginRateLimit`), aplicada solo al login |
| `SearchAsync_QueryTextNeverRisesAboveDebug` | Existe (C03) — **la regla de privacidad del log se hereda con su test** |
| `query.maxLength = 500` en `ai-service/openapi.json` | Existe — **origen de la longitud de `SearchText`** |
| Productos: borrado | **Soft delete** (`IsActive = false`); nunca `Remove` |
| Artefactos OpenSpec de este change (proposal, design, specs, tasks) | **A generar** desde esta HU y este ticket |

**Impacto en producto:** ninguno visible para el operador. El valor es que la entrega pueda presentar KPIs calculados en lugar de estimados, y que C16 —🔴, en la ola más congestionada— herede un contrato de un solo campo.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `backend/src/JoiabagurPV.Domain/` | Entidad `ProductSearchEvent`, enum `SearchOrigin`, `IProductSearchEventRepository`, propiedad `Sale.SearchEventId` |
| `backend/src/JoiabagurPV.Infrastructure/` | `ProductSearchEventConfiguration`, ampliación de `SaleConfiguration`, `DbSet`, repositorio, **la única migración del change** |
| `backend/src/JoiabagurPV.Application/` | `IProductSearchEventService` + implementación, DTO de selección y su validador, proyección y truncado de resultados |
| `backend/src/JoiabagurPV.API/` | `AiSearchEventsController` con un único endpoint |
| `backend/src/JoiabagurPV.Tests/` | `TestHelpers/SchemaAssert`, test de desfase modelo↔migración, unitarios del servicio, integración con Testcontainers |
| `backend/api-tests/` | `ai-search-events.http` |
| `openspec/` | Capability nueva `ai-search-telemetry` y los cuatro artefactos del change |
| `Documentos/` | HU-AIENG-004, `modelo-de-datos.md`, y las especificaciones del Proyecto Final |
| `frontend/`, `ai-service/`, `terraform/` | **Sin cambios** |

---

## Especificaciones Técnicas

### Backend (.NET) — modelo de datos

**Entidad `ProductSearchEvent : BaseEntity`** (tabla `ProductSearchEvents`)

| Columna | Tipo PostgreSQL | Null | Notas |
|---|---|---|---|
| `Id` | `uuid` PK | no | de `BaseEntity` |
| `CreatedAt` | `timestamptz` | no | de `BaseEntity`. **Es el instante de la consulta**: se captura al servir la búsqueda, no al persistir |
| `UpdatedAt` | `timestamptz` | no | de `BaseEntity`. Auditoría; **no** se usa como instante de selección |
| `UserId` | `uuid` → `Users` | no | del ámbito validado, nunca del cuerpo de la petición |
| `PointOfSaleId` | `uuid` → `PointOfSales` | no | ídem |
| `SearchSessionId` | `uuid` | no | agrupa el episodio; el servidor genera uno si el llamante no lo aporta |
| `SearchText` | `varchar(500)` | no | longitud derivada de `ai-service/openapi.json` |
| `FiltersJson` | `jsonb` | no | filtros **efectivos** (proyección de `AiSearchFilters`); `{}` si no hubo |
| `ResultsJson` | `jsonb` | no | lista **mostrada** proyectada; `[]` si vacía |
| `ResultsCount` | `int` | no | mostrados de verdad; `> jsonb_array_length(ResultsJson)` ⇒ hubo truncado |
| `SearchOrigin` | `int` | no | enum con valores explícitos: `Assisted = 1`, `LexicalFallback = 2` |
| `TraceId` | `varchar(64)` | sí | traza W3C de 32 hex, o el identificador de respaldo de ASP.NET |
| `RetrievalMs` | `int` | sí | obtener candidatos, **agnóstico del origen** |
| `TotalMs` | `int` | sí | hasta tener la lista final lista para devolver, antes de persistir |
| `SelectedProductId` | `uuid` → `Products` | sí | |
| `SelectedFromRank` | `int` | sí | **derivado en servidor**, 1-based; nulo si el producto no está en la lista |
| `SelectedAt` | `timestamptz` | sí | sellado por el servidor al recibir la selección |

**Índices:** `IX_ProductSearchEvents_PointOfSaleId_CreatedAt` (en ese orden) e `IX_ProductSearchEvents_CreatedAt`. Nada más.

**Ampliación de `Sale`:** columna `SearchEventId uuid NULL` → `ProductSearchEvents`. EF genera además `IX_Sales_SearchEventId`, que sirve a la dirección evento→venta; **no se elimina**.

**Reglas de borrado, las cuatro declaradas a mano:**

| Relación | Default de EF | Decisión | Motivo |
|---|---|---|---|
| `Event.UserId` → `Users` | **Cascade** (obligatoria) | `Restrict` | Borrar un usuario no puede evaporar el histórico en silencio; la supresión es un `DELETE` deliberado en dos pasos |
| `Event.PointOfSaleId` → `PointOfSales` | **Cascade** | `Restrict` | Cerrar un punto de venta no borra su telemetría |
| `Event.SelectedProductId` → `Products` | Restrict | `Restrict` explícito | Los productos se desactivan, no se borran; que falle ruidosamente si algún día alguien borra uno |
| `Sale.SearchEventId` → `Events` | Restrict | **`SetNull`** | Purgar telemetría no puede bloquear ni destruir ventas |

Asimetría deliberada: **`SetNull` hacia la venta, `Restrict` hacia todo lo demás.** La telemetría es prescindible; nada que dependa de ella puede romperse al desaparecer, y nada de lo que ella depende puede desaparecer por accidente arrastrándola.

**Sin propiedades de navegación** en `ProductSearchEvent`: las claves foráneas se configuran sin navegación, sosteniendo el techo de cero lectura y evitando sorpresas de carga diferida en una entidad que solo se escribe.

### Backend (.NET) — capa de aplicación

`IProductSearchEventService`, dos caminos de escritura:

**1. `RecordSearchAsync(AiCallScope scope, …) → Guid?`** — API interna, sin HTTP, que invocará C15.

- Recibe `AiCallScope`, no un `Guid` suelto: su fábrica única exige un punto de venta ya validado, así que la firma **hace imposible** registrar una búsqueda fuera de un ámbito autorizado.
- **Nunca lanza.** Cualquier fallo de persistencia se traga y se registra con nivel de error; devuelve `null`. Convierte en garantía verificable lo que si no sería una obligación que C15 podría incumplir.
- Proyecta la lista mostrada a `ResultsJson` con la forma `{ productId, sku, rank, score, matchReasons }`, en `camelCase`, en orden de rank 1-based.
- **Truncado por número de entradas, tope 50, nunca por bytes.** Guardarraíl contra un defecto propio: con `top_k` en torno a 10-20 no salta en operación normal. `ResultsCount` guarda siempre los mostrados reales.

**2. Registro de la selección** — expuesto por HTTP.

- Deriva `SelectedFromRank` buscando el producto en `ResultsJson`; si no aparece, guarda producto e instante con rank nulo y emite un aviso.
- Sella `SelectedAt` con el reloj del servidor.
- Última escritura gana, sin conflicto.

**Criterio de proyección:** entra solo lo **irrecuperable**. `score` y `matchReasons` dependían del índice, del modelo de embeddings y de los pesos de ese día — misma lógica por la que `Sale.Price` congela el precio. `materials`, `familyId`, `variantLabel`, precio y stock se reconstruyen con un `JOIN` y quedan fuera. `sku` entra por legibilidad al consultar a mano, con precedente en `ProductPhotoEmbedding.ProductSku`.

### Backend (.NET) — capa API

```http
POST /api/ai/search-events/{id}/selection
Authorization: Bearer <jwt de usuario>
Content-Type: application/json

{ "productId": "3f2a…" }

→ 204 No Content
→ 403 Forbidden   si el evento no pertenece a quien llama (incluido rol Administrador)
→ 404 Not Found   si el evento no existe
```

- Controller `AiSearchEventsController` con `[ApiController]`, `[Route("api/ai/search-events")]`, `[Authorize]` a nivel de clase. **Un controller por recurso**, no un `AiController` compartido: cuatro changes van a añadir rutas bajo `api/ai/*` con dos desarrolladores en paralelo.
- **Sin versión en la ruta**, coherente con los 18 controllers existentes.
- **Sin `CreatedAtAction`**: el helper `Created<T>()` de `BaseController` apunta a un `GetById` que aquí no existe y produciría un `Location` roto.
- **Sin política de limitación de peticiones**: una llamada por clic, sin coste externo, escribiendo solo en filas propias.
- Autorización por propiedad del evento, **sin bypass de administrador** — desviación deliberada del patrón de la casa, documentada en el design y con test que la fija.

### Datos

Reflejo obligatorio en `Documentos/modelo-de-datos.md`: entidad nueva, columna nueva en `Sale`, los dos índices y las cuatro reglas de borrado.

### Fuera de este ticket

- **Toda ruta de lectura**: `GET`, agregaciones, panel de KPIs. El análisis del entregable se hace con SQL a mano en C39.
- `POST /api/ai/search` y la invocación real de `RecordSearchAsync` → **C15**.
- Panel de búsqueda asistida, generación del identificador de episodio y envío de la selección → **C16**.
- `SearchEventId` en `CreateSaleRequest` / `BulkSaleLineRequest` y su asignación en `SaleService` → C16 o el change que conecte el flujo de venta.
- Política de retención o anonimización de `SearchText`.
- Test de reversibilidad de la migración, con motivo escrito: es generada, no artesanal, y su `Down` no es código nuestro.

---

## Arquitectura

### El reparto de escritura, y por qué no lo escribe todo el cliente

```
┌──────────────────────────────────────────────────────────────────────┐
│  NAVEGADOR (C16)          │  BACKEND, en POST /api/ai/search (C15)   │
│  ✔ qué producto eligió    │  ✔ consulta, filtros efectivos, POS      │
│  ✔ el episodio            │  ✔ la lista exacta tras hidratar y truncar│
│  ✗ qué devolvió jbg-ai    │  ✔ origen de los resultados               │
│  ✗ si el circuito abrió   │  ✔ trace_id                               │
│  ✗ el trace_id            │  ✔ latencia medida donde ocurre           │
│  ✗ la latencia real       │  ✗ si el operador llegó a elegir          │
└──────────────────────────────────────────────────────────────────────┘
```

La partición es complementaria: ninguno de los dos puede escribir el evento entero sin inventarse la mitad. Es la misma regla que gobierna el resto del diseño —§6.2 *«.NET calcula números y decide»*, §7.6 el hidratador como autoridad final—: pedirle al navegador que reporte la lista que el propio servidor acaba de calcular es el mismo error de categoría que fiarse de `jbg-ai` para el precio.

Efecto colateral buscado: el contrato de C16 se reduce a `{ productId }`, y **tres obligaciones desaparecen** (emitir en abandono, enviar el rank 1-based, reportar el origen) porque dejan de depender de que alguien se acuerde.

### Granularidad: una fila por consulta, agrupadas por episodio

Un operador con un cliente delante reformula. Una fila por episodio pierde la reformulación —que es la señal de que el primer intento fue malo—; una fila por consulta sin agrupar convierte cada reformulación en un falso «consulta sin resultado». La solución cuesta una columna:

```
  SearchSessionId (uuid, generado en cliente al abrir el panel)

  → nº de consultas por sesión                    = calidad del primer intento
  → sesión sin ninguna selección                  = abandono REAL
  → consulta sin selección con hermana posterior  = reformulación (derivable)
  → SelectedAt − min(CreatedAt) de la sesión      = el KPI de tiempo a selección
```

### Los tiempos: dos duraciones de servidor y una marca de tiempo

`SearchDurationMs` de specs v2 §5.8 podía significar la latencia de recuperación o el tiempo hasta la selección. Se desdobla:

- `RetrievalMs` — obtener candidatos, agnóstico del origen, de modo que la ruta degradada sea comparable.
- `TotalMs` — hasta tener la lista final. **`TotalMs − RetrievalMs` ≈ coste de la hidratación**, cifra que el proyecto quiere poder defender, porque la hidratación autoritativa es una decisión de firma del diseño y hoy nadie sabe lo que cuesta.
- `SelectedAt` en lugar de un delta calculado en cliente: con reformulaciones, el cliente solo puede medir el último tramo, y el reloj del servidor no depende de aritmética que nadie puede verificar.

### Frontera entre el log y la tabla

El log estructurado de C03 sigue existiendo y no se toca. `AiGatewayAttemptTracker` (reintentos) y el estado del cortacircuitos **se quedan en el log**: sirven fila a fila para diagnosticar una llamada concreta. `RetrievalMs`, `TotalMs` y el desenlace **cruzan a la tabla**: se agregan y se cruzan con lo que hizo el operador. Dos sistemas, dos preguntas; ni se sustituyen ni se duplican.

### El arnés de test de migración

No existe ninguno en el repositorio y el plan pide *«test de migración»* en seis changes. La clave es que un test que solo afirma *«la migración aplica»* es teatro: `TestDatabaseFixture.InitializeAsync()` ya ejecuta `MigrateAsync()` en cada test de integración. El valor está exclusivamente en **lo que falla sin dar error**:

| Fallo posible | ¿Rompe al aplicar? | ¿Cuándo se descubre de verdad? |
|---|---|---|
| Falta `HasColumnType("jsonb")` → la columna nace `text` | **no** | en C39, al consultar el JSON, con semanas de datos dentro |
| Índice compuesto con las columnas al revés | **no** | nunca; solo un plan de consulta lento |
| `OnDelete` en `Cascade` | **no** | el día que se purgue telemetría **y desaparezcan ventas** |
| `OnDelete` en `Restrict` | **no** | el día que se ejerza una supresión y no se pueda |
| Configuración cambiada sin generar migración | a veces | según qué test toque esa entidad |

Es el mismo fenómeno que motiva `test_hnsw_index_uses_cosine_operator_class` en C05: un índice mal declarado no da error, simplemente deja de usarse.

**Capa 1, reutilizable:** test de desfase modelo↔migración —que compara el snapshot con el modelo actual y **no necesita base de datos**, así que es un test unitario de milisegundos— y un ayudante de aserciones sobre `information_schema` y `pg_indexes` en `TestHelpers/`, apoyado en el `TestDatabaseFixture` existente.

**Capa 2:** las aserciones propias de C04. C07, C08, C19, C27 y C29 escriben su capa 2 en diez líneas y heredan la capa 1 gratis.

### Breaking changes

Ninguno. No se modifica ningún contrato REST existente, ni el snapshot `ai-service/openapi.json`, ni ningún comportamiento actual. `Sales` gana una columna nullable que nadie escribe todavía.

---

## Criterios de Aceptación

Los quince escenarios en formato BDD están en [HU-AIENG-004](../../../../Documentos/Historias/AI-Eng/HU-AIENG-004.md#criterios-de-aceptación). Traducción a nombres de test, según la convención `Método_Escenario_ResultadoEsperado`:

| Escenario | Test |
|---|---|
| 1 | `RecordSearch_WithValidScope_PersistsEventWithServerKnownFields` |
| 2 | `RecordSearch_WhenOriginIsLexicalFallback_PersistsDistinguishableOrigin` |
| 3 | `RecordSearch_WithNoResults_PersistsZeroCountAndEmptyArray` |
| 4 | `RecordSearch_WhenPersistenceFails_DoesNotThrowAndReturnsNull` |
| 5 | `RecordSelection_WithProductInResults_DerivesRankFromStoredList` |
| 6 | `RecordSelection_WhenProductNotInResults_PersistsSelectionWithNullRank` |
| 7 | `RecordSelection_WhenCalledTwice_KeepsLastSelection` |
| 8 | `RecordSelection_WhenEventBelongsToAnotherUser_Returns403` · `RecordSelection_WhenCallerIsAdminButNotOwner_Returns403` |
| 9 | `RecordSearch_WithMoreResultsThanCap_StoresOnlyTheCap` · `RecordSearch_WithMoreResultsThanCap_RecordsTrueDisplayedCount` |
| 10 | `RecordSearch_WithSameSessionId_GroupsQueriesOfOneEpisode` |
| 11 | `Migration_AddsNullableSearchEventIdToSales` |
| 12 | `DeletingSearchEvent_NullsSaleAttribution_WithoutDeletingSale` |
| 13 | `RecordSearch_QueryTextNeverRisesAboveDebug` |
| 14 | `Migration_JsonColumnsAreJsonbNotText` · `Migration_CompositeIndexOrdersPointOfSaleBeforeCreatedAt` · `Migration_ForeignKeyDeleteRulesAreExplicit` · `Model_HasNoPendingMigrationDifferences` |
| 15 | revisión de alcance en `/opsx:verify` |

---

## Definición de Hecho (DoD)

- [ ] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus; integración con Testcontainers/PostgreSQL; nomenclatura `Método_Escenario_ResultadoEsperado`; cobertura ≥70%
- [ ] **Una única migración** de EF Core creada, aplicable, y con las cuatro reglas de borrado declaradas a mano
- [ ] Arnés de esquema en `TestHelpers/` **limitado a lo que C04 necesita hoy**: ningún método «por si acaso»
- [ ] Spec de la capability `ai-search-telemetry` en `openspec/changes/add-product-search-event-tracking/specs/` y `openspec validate --all --strict` con `0 failed`
- [ ] Las diez obligaciones hacia adelante recogidas en `proposal.md`, **no** en `specs/` — un requisito especificado y no implementado haría fallar `/opsx:verify`
- [ ] Obligación crítica sobre C15 anotada además en la ficha de C15 de `Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md`
- [ ] `Documentos/modelo-de-datos.md` actualizado con la entidad, la columna nueva de `Sale`, los índices y las reglas de borrado
- [ ] `backend/api-tests/ai-search-events.http` añadido y ejecutable contra el backend local
- [ ] Compatibilidad hacia atrás verificada: ningún contrato REST existente ni el snapshot OpenAPI han cambiado
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] `dotnet build` y `dotnet test` en verde, sin regresión en la suite existente

---

## Requisitos No Funcionales

- **Seguridad:** endpoint bajo `[Authorize]`; identidad del token, nunca del cuerpo; autorización por propiedad del evento sin bypass de administrador; la garantía de punto de venta la aporta la firma del servicio (`AiCallScope`), no una comprobación que alguien pueda olvidar.
- **Privacidad:** `SearchText` es texto libre que puede recoger incidentalmente datos de terceros —los puntos de venta son hoteles—. Se hereda la regla de C03: **el texto no aparece en ningún log por encima de `Debug`**, con su test. No procede el pipeline de anonimización del máster: este texto nunca entra al espacio vectorial ni se recupera semánticamente, así que el control de acceso sí basta. La supresión por usuario queda operable gracias al `SET NULL` hacia la venta.
- **Resiliencia:** un fallo de telemetría **nunca** propaga error. `RecordSearchAsync` no lanza; un `SearchEventId` desconocido en una venta degrada la atribución a nula en lugar de hacer fallar la venta. Es la extensión natural de *«el sistema nunca se cae por culpa de la IA»*: tampoco por culpa de medirla.
- **Rendimiento:** volumen esperado ~200 filas/día, ~3.000 en la entrega, ~70.000 en un año. A esa escala ningún índice mejora nada medible; los dos que se ponen son opción de futuro, porque añadirlos después cuesta un slot de migración de un presupuesto de seis. **Se documenta explícitamente para que nadie añada más.**
- **Observabilidad:** log estructurado con Serilog en los caminos de escritura, con el texto de consulta confinado a `Debug` y el `trace_id` disponible para correlacionar con los logs de `jbg-ai`.
- **Integridad de datos:** `score` y `matchReasons` se congelan como instantánea, misma lógica que `Sale.Price`; `jsonb` obliga a Postgres a validar en la escritura, lo que hace imposible por construcción el truncado que corrompe el JSON.

---

## Preguntas Abiertas → Decisiones

Las cuatro preguntas abiertas de la sesión de exploración quedaron cerradas; se registran aquí con su resolución, y las que siguen abiertas llevan opción por defecto.

| # | Pregunta | Decisión / opción por defecto |
|---|---|---|
| 1 | ¿Quién emite el evento y cuándo? | **Cerrada.** El servidor escribe la búsqueda desde C15; el cliente reporta solo la selección |
| 2 | `text` o `jsonb` para resultados y filtros | **Cerrada.** `jsonb`, con propiedad `string` + `HasColumnType`, sin `ToJson()` |
| 3 | Uno o dos relojes | **Cerrada.** Dos duraciones de servidor (`RetrievalMs`, `TotalMs`) más `SelectedAt`; cero aritmética en el cliente |
| 4 | ¿Guardar el `trace_id`? | **Cerrada.** Sí, `varchar(64)` nullable; bajo este modelo está disponible en el punto de escritura y no cuesta nada |
| 5 | Tope de entradas del truncado | **Por defecto 50.** Holgado sobre cualquier `top_k` plausible, de modo que solo salte ante un defecto. Revisable si C15 fija un `top_k` mayor |
| 6 | ¿Se coge C04 antes que C07 pese a la regla 2 del plan? | **Por defecto sí**, por el coste fijo del arnés. Requiere anuncio previo al compañero (regla 3). Si se decide lo contrario, el arnés viaja con C07 y C04 lo hereda |
| 7 | ¿Se parte el change si desborda la sesión? | **Por defecto no se parte**, pero las tareas van ordenadas para que el corte esquema/escritura sea mecánico si hiciera falta (regla 5) |
| 8 | ¿Quién conecta `Sale.SearchEventId` al flujo de venta? | **Por defecto C16.** Si se prefiere un change propio, la columna ya está y no requiere migración nueva |

---

## Prioridad / Estimación / Tags

- **Prioridad:** Media — 🟢 paralelizable, no bloquea a nadie. Su urgencia real es indirecta: adelantarlo saca trabajo de C16, que sí es 🔴.
- **Estimación:** 5 puntos de historia.
- **Tags:** `backend`, `dotnet`, `ef-core`, `migration`, `postgresql`, `jsonb`, `telemetry`, `observability`, `testing`, `proyecto-final-ia`, `EP17`, `C04`.

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-004](../../../../Documentos/Historias/AI-Eng/HU-AIENG-004.md)
- **Change OpenSpec:** `openspec/changes/add-product-search-event-tracking/`
- **Plan de changes:** [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) — ficha C04
- **Diseño RAG v3:** [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) — §6.2, §6.4, §7.6, §11.2, §15
- **Especificaciones funcionales v2:** [joiabagur-ia-especificaciones-funcionales-v2.md](../../../../Documentos/Proyecto%20Final%20AIEng/joiabagur-ia-especificaciones-funcionales-v2.md) — §5.8, §5.9, §5.11
- **Épicas:** [epicas.md](../../../../Documentos/epicas.md) — EP17
- **Modelo de datos:** [modelo-de-datos.md](../../../../Documentos/modelo-de-datos.md)
- **Precedente de ticket y de prerrequisito hacia adelante:** `openspec/changes/archive/2026-08-09-add-dotnet-ai-gateway-client/`
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Cambio | Origen |
|---|---|---|
| 2026-08-10 | Creación del ticket a partir de la sesión de exploración `/opsx:explore` sobre la ficha C04, con las once decisiones de diseño, las tres divergencias respecto a specs v2 y las diez obligaciones hacia C15 y C16 | `/enrich-us` |
