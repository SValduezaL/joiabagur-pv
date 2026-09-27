# T-AIENG-008: Product AI profile entity — per-field hybrid review, renegotiated enrichment contract and catalog-scoped calls (C08)

> Ticket técnico del change OpenSpec `add-product-ai-profile-entity`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, `Documentos/` (diseño RAG §7.8, plan de changes, apuntes del Máster S4/S6), specs vivas de `openspec/specs/`, el contrato `ai-service/openapi.json`, el código real de `backend/src/` y `ai-service/src/`, y [HU-AIENG-008](../../../../Documentos/Historias/AI-Eng/HU-AIENG-008.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-008 / C08** — Entidad `ProductAiProfile` con confianza y origen por campo, migración única, enrutado híbrido de revisión, contrato de enriquecimiento renegociado, scope de catálogo sin `pos_id` y endpoint `POST /api/ai/catalog/enrich-batch`

---

## Contexto y Problema

El catálogo de JoiaBagur **no tiene un solo atributo estructurado que sirva para buscar por semántica**. `Product` guarda `SKU`, `Name`, `Description`, `Price`, `CollectionId` e `IsActive`, y nada más. Toda la recuperación asistida diseñada para la Ola 2 —filtro por solape de materiales (§7.3), filtros estructurales por reglas (§7.6), agrupación por familia, sustitutos por materiales coincidentes (§6.3.2 de las specs v2)— presupone unos campos que **no existen en ninguna tabla del sistema**. C08 es el change que los crea en el lado .NET, que es donde el diseño §6.2 los coloca: *datos de negocio revisables por humanos*.

El segundo problema es de confianza, y es el que gobierna la forma de la entidad. Un atributo inferido por un modelo y aprobado por nadie **es peor que un atributo ausente**: si el sistema afirma que una pieza es de plata y es de acero, la operadora que se fía vende mal. La decisión 5 del diseño (§7.8) responde con revisión **híbrida por campo** —sensible inferido a revisión, sensible por regla no, etiquetas comerciales auto-aprobables por umbral— y con una salida operativa declarada para el hecho de que revisar mil fichas antes del 3 de septiembre es imposible: dos vías distinguibles en el dato, una revisada de verdad y cronometrada, otra masiva y marcada como tal.

El tercer problema apareció al ir a usar el contrato. **C08 es el primer y único consumidor de `POST /v1/enrich/products`**, congelado en C02 y nunca llamado. Su `ProposedProfile` lleva confianza por valor, pero **no lleva `source`**: no dice si un valor es inferido o viene de una regla determinista. Sin ese dato, la regla central de la decisión 5 no es implementable y los cuatro tests `Routing_*` de la ficha no tienen nada que distinguir. Tampoco lleva `piece_type`, `stone_type` ni `size_label`, y su `tags` plano no encaja con las tres columnas separadas que `ai.product_document` ya tiene desde C05.

Y hay un cuarto, heredado. `AiCallScope` **no se puede construir sin punto de venta** —la spec viva de C03 lo exige y prohíbe centinelas— y `decode_service_token` exige `pos_id` como claim obligatorio en **todas** las rutas `/v1`. Enriquecer el catálogo no pertenece a ningún punto de venta. El propio código de C03 dejó el problema anotado y adjudicado: *«Routes with no point of sale — catalog-wide enrichment and index sync — will need a different scope. Adding it is the job of the first change that calls them (C08 or C13)»*. Ese primer change es este.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `ProductAiProfile` (entidad, configuración, repositorio) | **Ausente.** `JoiabagurPV.Domain/Entities/` tiene 25 entidades y ninguna de perfil IA |
| Atributos estructurados en `Product` | **Ninguno.** `SKU`, `Name`, `Description`, `Price`, `CollectionId`, `IsActive`, `Photos`. Sin material, tipo de pieza, piedra ni talla |
| `IAiGatewayClient` | **Una sola operación:** `SearchAsync`. Su propia documentación declara que cada change añade la que primero llama |
| Cliente con nombre y resiliencia | **Solo `ai-retrieval`** (`RetrievalTimeoutMs = 800`, reintento 1, breaker propio). `AssistTimeoutMs = 5000` existe en opciones pero **no hay cliente registrado** para él; el registro deja escrito que C34 añadirá el suyo |
| `AiCallScope` | **Un solo constructor:** `ForPointOfSale`, que rechaza POS vacío. `PointOfSaleId` es `Guid` no nulable. El comentario del tipo **adjudica a C08 o C13** el scope sin POS |
| `AiServiceTokenFactory` | Emite **exactamente cinco entradas**: `user_id`, `role`, `pos_id`, `trace_id`, `exp`. `AiServiceTokenFactoryTests` afirma ese conjunto exacto |
| `decode_service_token` (Python) | `REQUIRED_CLAIMS = ("user_id", "role", "pos_id", "trace_id")` — **los cuatro obligatorios en todas las rutas** |
| `get_service_principal` | Dependencia **única** para todo `/v1`. No hay variante de catálogo |
| `ProposedProfile` (contrato) | `title`, `description`, `materials`, `family_id`, `variant_label`, `tags`, `warnings`. **Sin `source`, sin `piece_type`, sin `stone_type`, sin `size_label`, sin desglose de etiquetas** |
| `EnrichRequest` | `products` (1..**50**, constante `MAX_BATCH_SIZE`), `locale` (`es-ES`) |
| Router `/v1/enrich/products` | Existe, protegido, con `require_stub_mode(settings, "C09 (add-catalog-enrichment-pipeline)")`: con stubs apagados responde **501** |
| `EnrichResponse` | Hereda de `TracedResponse`, **no** de `ScopedResponse` → **no lleva `effective_pos_id`**, luego un principal sin POS no altera la respuesta |
| `Usage.model` | **Ya existe** en el contrato → `GeneratedByModel` se puede poblar sin tocar nada. `prompt_version` no existe |
| `SchemaAssert` (C04) | Tiene `ColumnTypeAsync`, `ColumnIsNullableAsync`, `ColumnMaxLengthAsync`, `IndexColumnsAsync`, `ForeignKeyDeleteRuleAsync`. **No sabe afirmar unicidad de índice** → hay que extenderlo |
| `MigrationModelDriftTests` | Existe y es **global**: cubre esta migración sin tocarlo |
| `AiContractSnapshotTests` | Existe; compara los modelos de **recuperación** contra `openapi.json`. Hay que extenderlo a los de enriquecimiento |
| Última migración de EF Core | `20260811061759_AddProductSearchEventTracking`. El turno de migración está **libre** |
| `ai-service/openapi.json` | 8 rutas `/v1` + `/health`, protegido por `test_openapi_snapshot_is_stable`. **Este change SÍ lo modifica** |
| Artefactos OpenSpec del change | Andamiaje creado (esquema `spec-driven`, 0/4). `proposal`, `design`, `specs` y `tasks` a generar desde esta HU y este ticket |

**Impacto en producto:** ninguno visible para el operador. Es un endpoint de administración sin interfaz. El valor es habilitador: C12 pasa de no tener qué filtrar a tener un predicado de aprobación, y C28 pasa de no poder medir a tener dónde leer.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `backend/src/JoiabagurPV.Domain/Entities/ProductAiProfile.cs` | **Nuevo.** Entidad del perfil |
| `backend/src/JoiabagurPV.Domain/Enums/` | **Nuevos.** `ProfileReviewStatus`, `ProfileReviewOrigin` |
| `backend/src/JoiabagurPV.Infrastructure/Data/Configurations/ProductAiProfileConfiguration.cs` | **Nuevo.** Tipos `jsonb`, índice único, reglas de borrado |
| `backend/src/JoiabagurPV.Infrastructure/Data/ApplicationDbContext.cs` · `Migrations/` | `DbSet` nuevo y **una única migración** |
| `backend/src/JoiabagurPV.Application/DTOs/Ai/` | Modelos de enriquecimiento, petición y respuesta del endpoint; `AiCallScope` modificado |
| `backend/src/JoiabagurPV.Application/Interfaces/` · `Services/` | `IAiGatewayClient.EnrichAsync`, `IProductAiProfileService`, política de enrutado |
| `backend/src/JoiabagurPV.Application/Configuration/AiGatewayOptions.cs` | Presupuesto de la familia `ai-enrich` |
| `backend/src/JoiabagurPV.Application/Configuration/` | **Nuevo.** Opciones de umbrales de enrutado, validadas al arranque |
| `backend/src/JoiabagurPV.API/Controllers/AiCatalogController.cs` | **Nuevo.** Un solo endpoint, solo Administrador |
| `backend/src/JoiabagurPV.Tests/` | Unitarios de política, contrato y token; integración de autorización y esquema |
| `ai-service/src/jbg_ai/api/schemas/enrich.py` | Contrato ampliado |
| `ai-service/src/jbg_ai/api/auth.py` · `deps.py` · `routers/enrich.py` | Principal de catálogo sin `pos_id` |
| `ai-service/src/jbg_ai/stubs/responses.py` | Stub coherente con el contrato nuevo |
| `ai-service/openapi.json` | **Regenerado** — es la renegociación, no un efecto colateral |
| `ai-service/tests/api/` | Contrato, autenticación de catálogo y snapshot |
| `openspec/` | Capability nueva `product-ai-profile`; deltas sobre `ai-gateway-client`, `ai-service-auth`, `ai-service-api-contracts` |
| `Documentos/` | HU-AIENG-008, `modelo-de-datos.md`, `epicas.md` (EP12), §0 del plan de changes |
| `frontend/`, `terraform/` | **Sin cambios** |

---

## Especificaciones Técnicas

### Entidad `ProductAiProfile`

Un perfil por producto. Sin propiedad de navegación desde `Product`: el catálogo no debe poder recorrerse hacia los datos de IA por accidente.

| Columna | Tipo | Null | Notas |
|---|---|---|---|
| `Id` | `uuid` PK | no | De `BaseEntity`, junto con `CreatedAt` y `UpdatedAt` |
| `ProductId` | `uuid` FK → `Product` | no | **`RESTRICT`** y **índice ÚNICO** |
| `PieceType`, `StoneType`, `SizeLabel` | `varchar` | sí | Vocabularios los cierra C09 → **`text`, nunca `ENUM`** |
| `MaterialsJson` | `jsonb` | no | Array; `"[]"` cuando no hay evidencia, **nunca nulo ni un valor por defecto** |
| `ColorTagsJson`, `StyleTagsJson`, `OccasionTagsJson` | `jsonb` | no | Separadas porque `ai.product_document` ya las tiene separadas |
| `AiConfidence` | `numeric` | no | Agregada; ordena la cola de revisión de C28 |
| `FieldConfidenceJson` | `jsonb` | no | `{ "materials": 0.72, "piece_type": 0.91, … }` |
| `FieldSourceJson` | `jsonb` | no | `{ "size_label": "rule", "materials": "inferred", … }` |
| `ProposedProfileJson` | `jsonb` | no | **Propuesta cruda de la IA, inmutable.** Base de la tasa de corrección de C28 |
| `GeneratedByModel` | `varchar` | sí | De `usage.model` |
| `PromptVersion` | `varchar` | sí | Evidencia de la progresión v1→v2 que C39 promete |
| `SourceHash` | `char(64)` | no | SHA-256 **de las entradas**, no del `doc_text` |
| `ReviewStatus` | `int` | no | `Pending` \| `Approved` \| `Rejected` |
| `ReviewOrigin` | `int` | no | `AutoBulk` \| `Human` |
| `ReviewedByUserId` | `uuid` FK → `User` | sí | **`RESTRICT`** |
| `ReviewedAt` | `timestamptz` | sí | |
| `ReviewDurationMs` | `int` | sí | Lo mide el navegador en C28; **nulo en aprobación masiva** |

**Índices:** `UNIQUE (ProductId)`; `(ReviewStatus)` para el feed de C12; `(ReviewStatus, ReviewOrigin)` para la cola de revisión y las métricas de C28. Ninguno mejora una latencia medible con ~1.000 filas: existen porque añadirlos después cuesta uno de los seis turnos de migración del plan y tenerlos no cuesta nada — el mismo razonamiento que C04 escribió para los suyos.

**Reglas de borrado, todas declaradas a mano.** El valor por defecto del framework para una relación requerida es `CASCADE`, que aquí significaría *«borrar un producto borra el trabajo de revisión»*. `Product` además ya se desactiva con `IsActive` en lugar de borrarse.

### Contrato renegociado — `POST /v1/enrich/products`

```python
class ProposedValue(BaseModel):
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: Literal["rule", "inferred"]      # NUEVO — sin él la decisión 5 no existe

class ProposedText(ProposedValue): value: str
class ProposedList(ProposedValue): value: list[str] = Field(default_factory=list)

class ProposedProfile(BaseModel):
    product_id: str;  sku: str
    title:         ProposedText | None
    description:   ProposedText | None
    piece_type:    ProposedText | None       # NUEVO
    materials:     ProposedList              # ahora con source
    stone_type:    ProposedText | None       # NUEVO
    size_label:    ProposedText | None       # NUEVO
    color_tags:    ProposedList              # NUEVO ┐
    style_tags:    ProposedList              # NUEVO ├─ sustituyen al `tags` plano
    occasion_tags: ProposedList              # NUEVO ┘
    family_id:     ProposedText | None       # se mantiene; C08 lo IGNORA
    variant_label: ProposedText | None       # se mantiene; C08 lo IGNORA
    warnings: list[str]

class EnrichResponse(TracedResponse):
    profiles: list[ProposedProfile]
    usage: Usage
    prompt_version: str                      # NUEVO — evidencia para C39
```

El stub debe seguir siendo **determinista y sin reloj**, y producir una mezcla que ejercite el enrutado: al menos un campo sensible `inferred`, al menos uno `rule`, etiquetas por encima y por debajo de un umbral razonable. Sin esa variedad, los tests de integración no distinguen nada.

**Regeneración obligatoria** de `ai-service/openapi.json` con el *one-liner* canónico del README. `test_openapi_snapshot_is_stable` se pone rojo a propósito: volver a verde **es** la renegociación.

### Scope de catálogo — dos cierres independientes

| Lado | Cambio |
|---|---|
| `AiCallScope` | Segundo constructor `ForCatalog(userId, role)`; `PointOfSaleId` pasa a `Guid?`; el tipo declara su clase (`PointOfSale` \| `Catalog`). `ForPointOfSale` **mantiene intactas** sus validaciones |
| `AiServiceTokenFactory` | Emite `pos_id` **solo** cuando el scope lo tiene. El resto del payload no se toca |
| `AiGatewayClient.SearchAsync` | **Rechaza** un scope de catálogo antes de emitir la petición |
| `auth.py` | `ServicePrincipal.pos_id` pasa a `str \| None`; `decode_service_token` recibe qué claims exigir |
| `deps.py` | `get_catalog_principal` — no exige `pos_id`. `get_service_principal` **no cambia** |
| `routers/enrich.py` | Pasa a `get_catalog_principal`. Recuperación, asistencia e inventario siguen igual |

Ningún cambio en el documento OpenAPI por este apartado: la autenticación no se describe ahí.

### Cliente y resiliencia

| Aspecto | Valor | Motivo |
|---|---|---|
| Cliente con nombre | `ai-enrich` | Familia de ruta propia, como `ai-retrieval` |
| Cortacircuitos | **Aislado** | Una extracción lenta no puede abrir el circuito de recuperación y empujar la búsqueda a su vía degradada |
| Presupuesto | `EnrichTimeoutMs`, orden de decenas de segundos, en configuración validada | Un lote de 50 con LLM real no cabe en 0,8 s |
| Reintento | **Ninguno** | Coste de LLM duplicado sin razón para esperar un resultado distinto |
| 501 del servicio | → **503** nombrando C09 | No hay degradación posible: el enriquecimiento ocurre o no ocurre |

### Política de enrutado híbrido

**Campos sensibles:** `piece_type`, `materials`, `stone_type`, `size_label`. La pertenencia a familia que §7.8 también lista **queda fuera**: es de C07 y C18.

| Campo | `source = rule` | `inferred`, conf ≥ umbral | `inferred`, conf < umbral |
|---|---|---|---|
| Los cuatro sensibles | no requiere revisión | **requiere revisión** | requiere revisión |
| `color_tags`, `style_tags`, `occasion_tags` | no requiere revisión | **auto-aprueba** | requiere revisión |

`ReviewStatus` = `Pending` si algún campo requiere revisión; `Approved` si ninguno. Clase **pura**, sin base de datos ni HTTP, en la capa de aplicación: los cuatro tests `Routing_*` deben correr en milisegundos y sin contenedor. Umbrales en opciones tipadas **validadas al arranque**, mismo patrón que `AiGatewayOptions` — un umbral que C24/C25 recalibrarán contra el golden set y está compilado en el código es un umbral que no se recalibra.

### Endpoint

```http
POST /api/ai/catalog/enrich-batch          [Authorize(Roles = "Administrator")]

{ "productIds": [ … ],                     // 1..50, espejo de MAX_BATCH_SIZE
  "reviewMode": "Routed" | "AutoBulk",     // por defecto Routed
  "force": false }                         // true = reenriquece aunque el hash no cambie

200 { "requested": 50, "enriched": 47, "skippedUnchanged": 3, "failed": 0,
      "profiles": [ { "productId", "reviewStatus", "fieldsPendingReview": [ … ] } ] }
```

- **Validación con FluentValidation**, invocada **explícitamente** en el controlador: este proyecto registra validadores pero no cablea pipeline automático, y un validador no invocado es peor que ninguno porque parece validación. Precedente literal en `AiSearchEventsController`.
- **Modo `AutoBulk`:** aprueba todo con origen de aprobación masiva, **pero `FieldConfidenceJson` y `FieldSourceJson` siguen registrando lo que el enrutado habría decidido**. Es lo que mantiene honesta la promesa del §7.8.
- **Idempotencia:** producto cuyo `SourceHash` no ha cambiado se omite **sin llamar al gateway**. Al cambiar el hash, el perfil vuelve al resultado del enrutado, `ReviewOrigin` vuelve a `AutoBulk` y los campos de revisión se limpian, con traza en el log.
- **Cero rutas de lectura, cero rutas de aprobación.** Son de C28 y C12.

### Tests

Nomenclatura .NET `Method_Scenario_ExpectedResult`, Python `test_<unidad>_<escenario>_<esperado>`.

| Test | Tipo | Qué protege |
|---|---|---|
| `EnrichBatch_AsOperator_Returns403` | integración | **Cliente nuevo de la factoría**, no el compartido: el de la clase conserva cookies de logins previos |
| `Routing_WhenSensitiveFieldInferred_MarksPendingReview` | unitario | Regla central de la decisión 5 |
| `Routing_WhenSensitiveFieldFromRule_DoesNotRequireReview` | unitario | La mitad de la regla que hace útil el `source` |
| `Routing_WhenTagConfidenceAboveThreshold_AutoApproves` | unitario | Umbral leído de configuración |
| `Profile_StoresMultipleMaterials` | persistencia | `materials` como lista, `[]` sin evidencia |
| `EnrichBatch_WhenSourceHashUnchanged_SkipsProductWithoutCallingGateway` | unitario | Coste de LLM y revisión humana |
| `EnrichBatch_WithAutoBulkMode_ApprovesButRecordsWhatRoutingWouldHaveSaid` | unitario | Que el atajo del §7.8 deje huella |
| `EnrichBatch_WithMoreThanContractBatchSize_ReturnsBadRequest` | unitario | Tope espejo del contrato |
| `SearchAsync_WithCatalogScope_IsRejected` | unitario | Primer cierre de la frontera de POS |
| `BuildToken_ForCatalogScope_OmitsPosClaim` | unitario | Payload sin claim vacío |
| `Migration_JsonColumnsAreJsonbNotText` | esquema | `text` en vez de `jsonb`: fallo mudo con datos dentro |
| `Migration_ProductIdIsUnique` | esquema | Sin él, C12 indexa duplicados **sin ningún error** |
| `Migration_DeletingProduct_IsRestrictedNotCascaded` | esquema | El `CASCADE` por defecto del framework |
| `test_enrich_profile_carries_source_per_field` | Python | El campo del que depende toda la decisión 5 |
| `test_catalog_token_without_pos_is_accepted_on_enrich` | Python | Segundo cierre, lado permisivo |
| `test_catalog_token_is_rejected_on_retrieval` | Python | Segundo cierre, lado restrictivo |
| `AiContractSnapshotTests` (extensión) | unitario | Deriva de contrato .NET ↔ snapshot |

**Extensión mínima de `SchemaAssert`**: una sola pregunta nueva —si un índice es único—, siguiendo el guardarraíl que C04 escribió para sí mismo (*solo lo que este change necesita hoy*).

**Verificación del propio arnés:** romper a propósito lo que cada detector vigila —quitar la unicidad, cambiar `jsonb` por `text`—, comprobar que **falla**, y revertir.

**Línea base primero.** `CLAUDE.md` documenta que la suite de .NET arranca con decenas de rojos preexistentes, algunos dependientes del orden. Se mide con `git stash push -u` antes de escribir nada y se comparan **nombres**, no recuentos.

---

## Arquitectura

**Frontera de responsabilidad (§6.2).** *Python calcula parecidos y redacta; .NET calcula números y decide.* `ProductAiProfile` es .NET porque es un **dato de negocio revisable por humanos**, exactamente como la tabla del §6.2 lo clasifica. Python propone y no persiste nada: `EnrichResponse` no escribe en ninguna parte, y este change no le da acceso a `public` ni se lo pide.

**Frontera de propiedad (§6.3).** Se mantiene intacta. C08 no añade ninguna lectura de Python hacia `public`; la única vía sigue siendo el feed HTTP que construirá C12.

**Decisiones previas que se heredan.**
- **C02** congeló el contrato y montó el snapshot como detector de renegociación. Este change es el primero que lo dispara — y hacerlo es usar el mecanismo, no romperlo.
- **C03** dejó tres cosas escritas que aquí se consumen: que cada change añade la operación de gateway que primero llama, que cada familia de ruta lleva su cortacircuitos aislado, y que **el scope sin punto de venta es de C08 o C13**.
- **C04** fijó el criterio de qué merece un test de esquema (*el valor está entero en las propiedades que están mal sin producir ningún error*) y el guardarraíl del arnés compartido. C08 es el segundo de los cinco herederos previstos.
- **C05** creó `ai.product_document` con `color_tags` / `style_tags` / `occasion_tags` separadas y `materials text[]`, lo que determina la forma que el perfil .NET debe alimentar.

**Patrones en uso.** Repository + Unit of Work para persistencia; Service Layer para el caso de uso; opciones tipadas con `ValidateOnStart` para umbrales y presupuestos; `HttpClient` con nombre + `Microsoft.Extensions.Http.Resilience`; política de dominio como clase pura para lo que debe testearse sin infraestructura.

**Control de acceso.** Endpoint **solo Administrador**, como el resto de la administración de catálogo (`ProductComponentsController`, `ComponentTemplatesController`, rutas de administración de `InventoryController`). No hay scoping por punto de venta porque el catálogo no lo tiene: es justamente lo que obliga al scope de catálogo en la llamada saliente.

**Breaking changes.**
1. **`ai-service/openapi.json` cambia.** Es un breaking change deliberado y negociado: la ruta afectada no tiene ningún otro consumidor. Rompe `test_openapi_snapshot_is_stable` hasta regenerarlo.
2. **`AiCallScope.PointOfSaleId` pasa a `Guid?`.** Afecta a todo lo que lo lea; hoy solo `AiServiceTokenFactory` y `AiGatewayClient`. Las guardas nuevas convierten el uso incorrecto en un fallo ruidoso.
3. **`ServicePrincipal.pos_id` pasa a opcional.** Las rutas de recuperación, asistencia e inventario **no cambian de comportamiento**: siguen exigiéndolo.
4. Ningún contrato REST del backend cambia: el endpoint es nuevo.

---

## Definición de Hecho (DoD)

- [ ] Entidad, configuración EF y **una única migración** aplicable, con `dotnet build` limpio
- [ ] `Model_HasNoPendingMigrationDifferences` en verde (modelo y migraciones sincronizados)
- [ ] Detectores de esquema en verde y **cada uno verificado rompiendo a propósito lo que vigila**, con la rotura revertida
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus; integración con Testcontainers; nomenclatura `Método_Escenario_ResultadoEsperado`; cobertura ≥70 % del código nuevo
- [ ] **Línea base de la suite medida antes de empezar** y comparada por nombres de test, no por recuento
- [ ] `ai-service`: `uv run --system-certs pytest` en verde, sin llamadas reales a LLM, embeddings ni RDS
- [ ] `ai-service/openapi.json` **regenerado** con el perfil canónico y `test_openapi_snapshot_is_stable` de nuevo en verde
- [ ] `AiContractSnapshotTests` extendido a los modelos de enriquecimiento y en verde
- [ ] Endpoint responde 403 a operador, 401 sin autenticar, 400 al superar el tope de lote y 503 cuando `jbg-ai` no tiene implementación
- [ ] Segunda ejecución del mismo lote: `skippedUnchanged` correcto y **cero llamadas al gateway**
- [ ] Specs del change en `openspec/changes/add-product-ai-profile-entity/specs/` y **`openspec validate --all --strict` con `0 failed`**
- [ ] Documentación actualizada: `Documentos/modelo-de-datos.md`, `Documentos/epicas.md` (EP12), `backend/README.md` (endpoint y matriz de autorización), `ai-service/README.md` (marcador de change y contrato), `openspec/project.md` (entidades clave)
- [ ] **§0 del plan de changes actualizado** con la corrección de zona y la renegociación del contrato
- [ ] Compatibilidad hacia atrás verificada: ninguna ruta `/v1` existente cambia de comportamiento
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] UI: **no aplica** — este change no tiene interfaz

---

## Requisitos No Funcionales

- **Seguridad:** endpoint restringido a Administrador vía RBAC. El scope de catálogo **no es una relajación de permisos**: es un scope distinto, con dos cierres independientes que impiden su uso en recuperación, precisamente porque desde C22 el `pos_id` del token es el único filtro duro del recuperador. El secreto HS256 sigue viniendo de configuración y, en producción, de SSM `/jpv/prod/*`. Ninguna credencial en el repositorio.
- **Rendimiento y free-tier:** lote acotado a 50, espejo del contrato. Sin trabajo en segundo plano ni hilos adicionales: el pool de 5-10 conexiones se respeta porque cada llamada es una transacción corta. Presupuesto de tiempo propio para la familia `ai-enrich`, aislado del de recuperación para no arrastrar la búsqueda a su vía degradada. **Coste de LLM controlado por diseño**: idempotencia por hash y cero reintentos automáticos.
- **Observabilidad:** logging estructurado con Serilog, `trace_id` propagado como claim y como cabecera igual que en recuperación. Se registran producto, modo, resultado del enrutado y campos pendientes; **el texto de la descripción del producto no sube de nivel Debug**, por la misma razón por la que la consulta del operador no lo hace en C03/C04. `usage` de cada lote se registra para que el coste sea reportable en §12.
- **Integridad de datos:** un perfil por producto garantizado por índice único en la base, no por comprobación aplicativa. Borrados restringidos en las dos claves foráneas. `MaterialsJson` y las tres de etiquetas nunca nulas. `ProposedProfileJson` inmutable una vez escrita para un `SourceHash` dado. **Ninguna escritura sobre `Product`** en ningún camino de código, incluido el de corrección.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿Debe `.NET` calcular por su cuenta la talla con una expresión regular sobre nombre y SKU, marcándola `source: rule`, o esperar a que C09 la produzca en la normalización determinista previa (§7.1)? | **Esperar a C09.** El §7.1 coloca esa normalización en el pipeline de Python; duplicarla en .NET crearía dos reglas de talla que divergirían. C08 se limita a **honrar** el `source` que reciba |
| 2 | Valores concretos de los umbrales de auto-aprobación de etiquetas | **0,80** como punto de partida documentado, en configuración. Es una cifra provisional por definición: C24 la recalibra contra el golden set, y ese es el motivo de no compilarla |
| 3 | ¿Debe el reenriquecimiento tras un cambio de `SourceHash` **conservar** la revisión humana anterior en lugar de limpiarla? | **Limpiarla**, con traza en el log. El texto del producto cambió, así que la revisión anterior es sobre otro texto. Conservarla haría que una ficha figurara como revisada por alguien que nunca vio ese contenido |
| 4 | ¿Cuenta `AiConfidence` agregada como media simple de las confianzas por campo, o ponderada dando más peso a los sensibles? | **Media simple** de los campos presentes. La ponderada exige justificar los pesos y no hay con qué; C28 ordena su cola por ella y para eso basta |
| 5 | ¿`prompt_version` entra en el contrato ahora o lo añade C09 junto al prompt real? | **Ahora.** Cuesta un campo, la renegociación ya está abierta, y sin él la progresión de prompts v1→v2 que C39 promete no se puede reconstruir a posteriori |
| 6 | ¿Se expone algún recuento de perfiles por estado para el panel de administración? | **No.** Toda lectura es de C28. Añadir «solo un contador» es la vía por la que un change sin superficie de lectura acaba con tres |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta**, pese al 🟢. No está en la ruta crítica, pero **C12 sí lo está y lo tiene como prerrequisito** junto con C07. Además ocupa el turno único de migración de EF Core, que es un recurso compartido con C07, C19, C27 y C29.
- **Estimación:** **8 SP** *(pendiente de validar en refinamiento)*. Ninguna pieza es difícil por separado; la carga está en la anchura —dos lenguajes, un contrato congelado, tres specs vivas modificadas, un turno de migración— y en las cuatro decisiones que la ficha no anticipaba.
- **Dependencias:** C03 (archivado). **Bloquea** a C12 y a C28. **No solapar** con ningún otro change 🗄️.
- **Línea de corte:** si desborda la sesión (regla 5 del plan), primero **entidad + configuración + migración + detectores de esquema** —mitad archivable que libera el turno de migración y desbloquea a C12—; después **contrato + scope + cliente + enrutado + endpoint**, que no lleva migración y convive con el C07 del compañero.
- **Tags:** `HU-AIENG-008`, `C08`, `EP12`, `backend`, `dotnet`, `ai-service`, `python`, `ef-core`, `migration`, `contract-change`, `hitl`, `enrichment`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-008](../../../../Documentos/Historias/AI-Eng/HU-AIENG-008.md)
- **Change OpenSpec:** `openspec/changes/add-product-ai-profile-entity/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C08, §0 revisiones, reglas transversales de testing) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §6.3, §7.1, §7.2, §7.3, **§7.8**) · [especificaciones funcionales v2](../../../../Documentos/Proyecto%20Final%20AIEng/joiabagur-ia-especificaciones-funcionales-v2.md) (§4.5, §4.6, §4.9)
- **Apuntes del Máster (S4, S6):** [Extracción de datos estructurados](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/Extraccion%20de%20datos%20estructurados.md) · [Guardrails y validación de outputs](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/Guardrails%20y%20validacion%20de%20outputs.md) · [Calidad del Dato y decisiones de Arquitectura](../../../../Documentos/Sesiones%20Master%20AIEng/S6_Fundamentos_Data_Driven_AI/Calidad%20del%20Dato%20y%20decisiones%20de%20Arquitectura.md)
- **Specs vivas afectadas:** `openspec/specs/ai-gateway-client/spec.md` · `openspec/specs/ai-service-auth/spec.md` · `openspec/specs/ai-service-api-contracts/spec.md` · `openspec/specs/ai-vector-schema/spec.md` (consumidor aguas abajo)
- **Precedentes de código:** `ProductSearchEventConfiguration.cs` (jsonb, índices, reglas de borrado) · `AiSearchEventsController.cs` (validación explícita, sin superficie de lectura) · `SchemaAssert.cs` y `ProductSearchEventSchemaTests.cs` (arnés heredado) · `AiGatewayServiceCollectionExtensions.cs` (familia de ruta con breaker propio)
- **Contrato:** `ai-service/openapi.json` — **este change lo modifica**, con el snapshot como testigo
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-16 | `/enrich-us` | Creación del ticket a partir de HU-AIENG-008 y de la sesión de exploración previa al proposal. Recoge las cuatro decisiones cerradas en esa sesión —renegociación del contrato de enriquecimiento, scope de catálogo sin `pos_id`, estado y origen de revisión ortogonales con modo `Routed`/`AutoBulk`, y almacenamiento reservado para las métricas de C28— y la corrección de zona, que pasa de tres carpetas a seis |
| 2026-08-16 | — | Renumerado de `T-AIENG-006` a **`T-AIENG-008`**, siguiendo a la HU, para que el número de historia y de ticket coincida con el del change (C08). La serie deja de ser correlativa por orden de creación y pasa a estar **alineada con el change**: `HU-AIENG-006` y `HU-AIENG-007` quedan reservadas para C06 y C07 |
