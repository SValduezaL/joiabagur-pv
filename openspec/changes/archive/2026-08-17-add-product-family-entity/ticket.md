# T-AIENG-007: Product family as an explicit, editable business entity — declarative membership, one family per product, and storage reserved for the assisted flow (C07)

> Ticket técnico del change OpenSpec `add-product-family-entity`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, `Documentos/` (diseño RAG §3 decisión 2, §6.2, §6.3, §7.4, §7.5, §7.8; plan de changes; especificaciones funcionales v2 §1, §4.4 y §4.6), specs vivas de `openspec/specs/`, el contrato `ai-service/openapi.json`, el código real de `backend/src/`, y [HU-AIENG-007](../../../../Documentos/Historias/AI-Eng/HU-AIENG-007.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-007 / C07** — Entidades `ProductFamily` y `ProductFamilyMember`, migración única con tres índices únicos, reemplazo declarativo de miembros, distinción entre producto huérfano y producto inexistente, y almacenamiento reservado para el flujo asistido de C18

---

## Contexto y Problema

El catálogo de JoiaBagur **no tiene forma de saber que dos productos son la misma pieza en tallas distintas**. `Product` guarda `SKU`, `Name`, `Description`, `Price`, `CollectionId` e `IsActive`. La única agrupación que existe es `Collection`, que es editorial —«Verano 2024»— y por tanto responde a otra pregunta.

Ese hueco es el caso de negocio crítico del proyecto, no un detalle de modelado. Tres anillos con la misma foto y tallas S, M y L producen tres resultados indistinguibles en cualquier buscador, y el error se detecta cuando el cliente vuelve. La recuperación semántica no lo arregla: los tres son legítimamente parecidos y devolverlos los tres es lo correcto. Lo que falta es que el sistema **sepa que son variantes** y obligue a confirmar cuál.

Las especificaciones v2 lo resolvían con `VariantGroupKey`, una cadena dentro del perfil de IA. La **decisión 2 de la revisión** la elimina con tres argumentos que son tres requisitos: se rompe por un guion (*«anillo-erizo-mar»* vs *«anillo-erizo-de-mar»*) y deja de avisar justo donde importaba; no la puede corregir un administrador, y si la corrige, el siguiente enriquecimiento la machaca; y sin una entidad con identidad propia **no hay contra qué comparar** para detectar un producto huérfano que debería pertenecer a una familia existente.

El segundo problema es de secuencia. El §7.5 del diseño acuerda un flujo mixto —*la IA propone, el admin aprueba, la familia queda editable después*— pero ese flujo necesita que primero exista lo que se aprueba. C07 construye el sitio donde la familia vive y se corrige; C18 construye quien la propone. Repartir la autoridad de otro modo crearía dos verdades sobre lo mismo, que es exactamente lo que C08 evitó al excluir la pertenencia a familia de sus campos sensibles y adjudicarla aquí.

Y hay un tercero, que la ficha no anticipa. **C18 no está marcado 🗄️** y el plan cuenta seis migraciones de EF Core, ninguna suya. Si C18 necesitara registrar que una familia salió de una sugerencia aprobada —que es la evidencia de intervención humana que el proyecto va a defender—, tendría que abrir una séptima en plena Ola 3, compitiendo con C19, C27 y C29. Es la misma situación que C08 resolvió el día anterior reservando `ProposedProfileJson` y `ReviewDurationMs` para C28, y se resuelve igual.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `ProductFamily` / `ProductFamilyMember` | **Ausentes.** `JoiabagurPV.Domain/Entities/` no contiene ninguna entidad de familia; el grep de `family\|familia\|variant\|sibling` sobre `backend/` solo devuelve falsos positivos («familia de ruta» del AiGateway, «familias de etiquetas» de C08) |
| `Product` | `SKU`, `Name`, `Description`, `Price`, `CollectionId`, `Collection`, `IsActive`, `Photos`, más `IsPriceValid()`/`IsSkuValid()`. **Sin `FamilyId` y sin ninguna colección hacia familias** |
| Agrupación existente | Solo `Collection`, 1‑N opcional con `OnDelete(SetNull)`. **Otro eje**: editorial, muchos productos, pertenencia opcional y no excluyente |
| `BaseEntity` | `Guid Id` (asignado en cliente con `Guid.NewGuid()`), `CreatedAt`, `UpdatedAt`. **No hay `CreatedBy`, ni soft‑delete, ni multi‑tenancy** en todo el backend |
| Tablas puente del modelo | **Todas con `Guid Id` surrogate** heredado de `BaseEntity` (`ComponentTemplateItem`, `ReturnSale`). Ninguna usa clave compuesta |
| Convención de tablas | **PascalCase plural declarado a mano** con `ToTable("…")` en cada `IEntityTypeConfiguration<T>`; `ApplyConfigurationsFromAssembly` las descubre solas |
| Enums persistidos | `HasConversion<int>()`. **Nunca tipos `ENUM` de PostgreSQL** — sobreviven al `DROP TABLE` y rompen la siguiente migración (razón escrita en `ProductAiProfileConfiguration`) |
| Última migración de EF Core | `20260816113455_AddProductAiProfile`. **El turno de migración está libre**: C08 se mergeó en `08d707b` |
| Arnés de migración | Dos capas, heredadas de C04. `MigrationModelDriftTests.Model_HasNoPendingMigrationDifferences` (sin base de datos) y `SchemaAssert` con `ColumnTypeAsync`, `ColumnIsNullableAsync`, `ColumnMaxLengthAsync`, `IndexColumnsAsync`, `IndexIsUniqueAsync` (añadido por C08) y `ForeignKeyDeleteRuleAsync`. **C07 no necesita extenderlo** |
| Repositorios | Genérico `IRepository<T>` + específicos por herencia. Interfaces en `Domain/Interfaces/Repositories/`, implementaciones en `Infrastructure/Data/Repositories/`. `AddAsync`/`UpdateAsync` **no guardan**: lo hace `IUnitOfWork` |
| Capa de aplicación | **Sin MediatR, sin CQRS, sin AutoMapper.** Servicios clásicos `IXxxService`/`XxxService`, DTOs POCO por área, mapeo a mano con `MapToDto` privado |
| FluentValidation | Registrado con `AddValidatorsFromAssembly`, **sin pipeline automático**. El controlador inyecta `IValidator<T>` y llama `ValidateAsync` a mano (comentario literal en `AiCatalogController`) |
| Reemplazo de colección hija | Precedente literal en `ComponentTemplateService.UpdateAsync`: `template.Items.Clear()` + re‑añadir, con la relación padre→hijo en `Cascade` |
| Cómo se devuelve un 409 | El servicio lanza `DomainException` y el controlador la filtra; `ProductsController.Create` usa `catch (DomainException ex) when (ex.Message.Contains("already exists"))` → `Conflict(new { error = ex.Message })`. El middleware global **no traduce a 409** |
| Violación de unicidad concurrente | Patrón ya escrito en `ProductAiProfileService`: se lee `DbException.SqlState == "23505"` —de la biblioteca base, **no** `PostgresException`— para que `Application` no referencie el driver de PostgreSQL |
| Rutas de controlador | Conviven `[Route("api/[controller]")]` y ruta literal kebab‑case (`api/component-templates`, `api/ai/catalog`). **Para `product-families` el precedente correcto es la literal** |
| `BaseController` | Existe y **ningún controlador lo hereda**. Andamiaje muerto: ignorar |
| Tests | Un solo proyecto `JoiabagurPV.Tests` con carpetas `UnitTests/`, `IntegrationTests/`, `TestHelpers/`. xUnit + FluentAssertions + Moq + Bogus + Testcontainers + Respawn. Dos colecciones: `IntegrationTestCollection` (API por HTTP) y `RepositoryTestCollection` (`TestDatabaseFixture`, que **aplica migraciones de verdad** y es de quien cuelgan los tests de esquema) |
| Object mothers | `TestHelpers/Mothers/TestDataMother.cs` con fábricas fluidas. **`ProductMother` existe**; no hay `ProductFamilyMother` |
| Suite de .NET | 729 tests, **45‑51 fallos preexistentes**, y el conjunto **cambia entre ejecuciones idénticas del mismo commit**. Comparar recuentos no sirve; solo nombres |
| `ai.product_document` (C05) | **Ya tiene** `family_id uuid` nullable **sin clave foránea**, `family_name text`, `variant_label text` y **B‑tree sobre `family_id`**. El índice está reservado; C07 solo produce el dato del lado .NET |
| `ai-service/openapi.json` | **Ya transporta** `family_id` y `variant_label` en recuperación, asistencia, inventario y enriquecimiento, congelados desde C02. **Este change NO lo modifica** |
| C08 | Ignora `family_id`/`variant_label` deliberadamente y lo declara en su spec viva |
| `openspec/specs/` | 33 capabilities, **ninguna de familias**. `product-management` cubre `Collection` |
| `openspec/changes/` | **Sin changes activos** antes de este |
| `modelo-c4.md` | Su sección EP13 **ya nombra** `ProductFamily` y `ProductFamilyMember` en el backend → **no hay que tocarlo** |
| `Documentos/modelo-de-datos.md` · `openspec/project.md` | **No las contienen.** Hay que añadirlas |
| Frontend | Cero rastro de familia o variante en tipos, servicios o pantallas. **No se toca** |

**Impacto en producto:** ninguno visible todavía. Es administración sin interfaz. El valor es habilitador: C12 pasa de no tener familia que emitir a tenerla, C18 pasa de no tener dónde aprobar a tenerlo, y C30/C36 pasan de no poder agrupar a poder exigir confirmación de variante.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `backend/src/JoiabagurPV.Domain/Entities/ProductFamily.cs` · `ProductFamilyMember.cs` | **Nuevas.** Las dos entidades |
| `backend/src/JoiabagurPV.Domain/Enums/FamilyOrigin.cs` | **Nuevo.** `Manual` \| `AiApproved` |
| `backend/src/JoiabagurPV.Domain/Interfaces/Repositories/IProductFamilyRepository.cs` | **Nuevo.** Dos lecturas con `Include` ordenado |
| `backend/src/JoiabagurPV.Infrastructure/Data/Configurations/ProductFamilyConfiguration.cs` · `ProductFamilyMemberConfiguration.cs` | **Nuevas.** Tres índices únicos, dos índices de cursor y las reglas de borrado declaradas a mano |
| `backend/src/JoiabagurPV.Infrastructure/Data/ApplicationDbContext.cs` · `Migrations/` | Dos `DbSet` nuevos y **una única migración** |
| `backend/src/JoiabagurPV.Infrastructure/Data/Repositories/ProductFamilyRepository.cs` | **Nuevo** |
| `backend/src/JoiabagurPV.Application/DTOs/Products/ProductFamilyDtos.cs` | **Nuevos.** Petición y respuesta de los cinco endpoints |
| `backend/src/JoiabagurPV.Application/Interfaces/IProductFamilyService.cs` · `Services/ProductFamilyService.cs` | **Nuevos.** Reemplazo declarativo, cortocircuito y detección de conflicto |
| `backend/src/JoiabagurPV.Application/Validators/` | **Nuevos.** Validadores de las dos peticiones de escritura |
| `backend/src/JoiabagurPV.Application/Extensions/ServiceCollectionExtensions.cs` | Registro del servicio |
| `backend/src/JoiabagurPV.Infrastructure/Extensions/ServiceCollectionExtensions.cs` | Registro del repositorio |
| `backend/src/JoiabagurPV.API/Controllers/ProductFamiliesController.cs` | **Nuevo.** Cuatro rutas |
| `backend/src/JoiabagurPV.API/Controllers/ProductsController.cs` | **Una sola ruta añadida:** `GET {id}/family` |
| `backend/src/JoiabagurPV.Tests/` | Unitarios de servicio y validadores; integración de API; detectores de esquema; `ProductFamilyMother` |
| `openspec/` | Capability **nueva** `product-family`. **Ninguna spec viva se modifica** |
| `Documentos/` | HU-AIENG-007, `modelo-de-datos.md`, `epicas.md` (EP13), §0 del plan de changes |
| `openspec/project.md` · `backend/README.md` | *Key Entities*, regla de negocio nueva, endpoints y matriz de autorización |
| `ai-service/`, `frontend/`, `terraform/`, `modelo-c4.md` | **Sin cambios** |

---

## Especificaciones Técnicas

### Entidad `ProductFamily` → tabla `ProductFamilies`

| Columna | Tipo | Null | Notas |
|---|---|---|---|
| `Id` | `uuid` PK | no | De `BaseEntity`, junto con `CreatedAt` y `UpdatedAt` |
| `Name` | `varchar(200)` | no | Longitud espejo de `Product.Name`. Indexado, **no único** |
| `Description` | `text` | sí | |
| `Origin` | `int` | no | `Manual = 1` \| `AiApproved = 2`, con `HasConversion<int>()`. **Nunca `ENUM` nativo** |
| `ApprovedByUserId` | `uuid` FK → `User` | sí | **`RESTRICT`.** Nulo en C07; lo puebla C18 |
| `ApprovedAt` | `timestamptz` | sí | Ídem |

### Entidad `ProductFamilyMember` → tabla `ProductFamilyMembers`

| Columna | Tipo | Null | Notas |
|---|---|---|---|
| `Id` | `uuid` PK | no | Surrogate, como toda tabla puente de este modelo. **No es estable entre escrituras** y nada lo referencia |
| `ProductFamilyId` | `uuid` FK → `ProductFamily` | no | **`CASCADE`** |
| `ProductId` | `uuid` FK → `Product` | no | **`RESTRICT`** e **índice ÚNICO global** |
| `VariantLabel` | `varchar(50)` | sí | `S`, `M`, `L`, `ajustable`, `talla 12`… |
| `SortOrder` | `int` | no | Derivado de la posición en el array de la petición |
| `CreatedAt` | `timestamptz` | no | **No significa «cuándo entró el producto en la familia»** sino cuándo se escribió la lista por última vez. Debe decirse en `modelo-de-datos.md` |

### Índices

| Índice | Único | Qué protege |
|---|---|---|
| `IX_ProductFamilyMembers_ProductId` | **sí** | *Un producto pertenece como máximo a una familia*. Una comprobación aplicativa deja la carrera abierta y un segundo miembro **no da ningún error**: el feed emitiría dos familias y el indexador construiría documentos incoherentes |
| `IX_ProductFamilyMembers_ProductFamilyId_SortOrder` | **sí** | Orden determinista. Duplicado ⇒ lista de hermanos distinta entre recargas, **sin error** |
| `IX_ProductFamilyMembers_ProductFamilyId_VariantLabel` | **sí** | Dos «M» en la misma familia. Los `NULL` no colisionan entre sí en PostgreSQL, así que la nulabilidad sale gratis y sin filtro |
| `IX_ProductFamilies_Name` | no | Búsqueda y listado de la pantalla de C18 |
| `IX_ProductFamilies_UpdatedAt` · `IX_ProductFamilyMembers_UpdatedAt` | no | Cursor `since` de C12. Con ~350 familias ninguno mejora una latencia medible: existen porque añadirlos después cuesta un turno de migración y tenerlos no cuesta nada |

**Reglas de borrado, ambas declaradas a mano.** El valor por defecto del framework para una relación requerida es `CASCADE`. Hacia el producto eso significaría *«borrar un producto destruye la curación»*, y `Product` además se desactiva con `IsActive` en lugar de borrarse. Hacia la familia, en cambio, la cascada **es** lo correcto: los miembros no tienen vida propia.

Ese reparto no es una invención de este change: es **literalmente el que ya usa `ComponentTemplate`**, la única pareja padre‑hijo comparable del modelo. `ComponentTemplateConfiguration.cs:31` declara `Cascade` del padre hacia sus ítems, y `ComponentTemplateItemConfiguration.cs:33` declara `Restrict` del ítem hacia el componente que referencia. `ProductFamily`/`ProductFamilyMember`/`Product` reproduce la misma forma con los mismos motivos.

### Endpoints

```http
POST   /api/product-families                     [Administrator]  201 · 400 · 409
       { "name": "Anillo erizo de mar", "description": "…",
         "members": [ { "productId": "…", "variantLabel": "S" }, … ] }   // members opcional

GET    /api/product-families/{id}                [Authenticated]  200 · 404

PUT    /api/product-families/{id}                [Administrator]  200 · 400 · 404
       { "name": "…", "description": "…" }                              // solo metadatos

PUT    /api/product-families/{id}/members        [Administrator]  200 · 400 · 404 · 409
       { "members": [ { "productId": "…", "variantLabel": "S" }, … ] }
       // reemplazo declarativo · SortOrder = índice en el array · [] vacía la familia

GET    /api/products/{id}/family                 [Authenticated]  200 · 204 · 404
```

Respuesta de familia, deliberadamente mínima:

```jsonc
{ "id": "…", "name": "…", "description": "…", "origin": "Manual",
  "members": [ { "productId": "…", "sku": "ERIZO-S", "name": "Anillo erizo de mar",
                 "variantLabel": "S", "sortOrder": 0 } ] }
```

Sin foto ni precio: hidratar exige `IFileStorageService` y arrastra la política de visibilidad por rol del catálogo dentro de un endpoint de dominio. La hidratación autoritativa para la interfaz es de C34.

- **Validación con FluentValidation invocada explícitamente en el controlador**: este proyecto registra validadores pero no cablea pipeline automático, y un validador no invocado es peor que ninguno porque parece validación. Precedente literal en `AiCatalogController`.
- **`GET /api/products/{id}/family`** distingue **404** (producto inexistente) de **204** (producto huérfano). El generador de C06 mete un **15 % de huérfanos a propósito**: es uno de cada siete productos, no un borde.
- **Sin listado paginado y sin borrado.** Cuando C18 añada el listado, le será exigible el máximo de 50 ítems por página de `openspec/project.md`.

### Conflicto por doble pertenencia

Dos cierres independientes:

1. **Comprobación previa en el servicio**, que produce el mensaje útil: **qué productos** y **qué familia los tiene ya**. Un 409 que solo dice «conflicto» obliga a la pantalla de C18 a adivinar cuál de veinte miembros falló.
2. **Traducción de la violación de unicidad de la base** (`SqlState 23505`) por si dos administradores escriben a la vez, leyendo `DbException.SqlState` y no `PostgresException`, para que `Application` no referencie el driver.

### Cómo se escribe el reemplazo de miembros

**Borrar todo e insertar todo**, con **cortocircuito de no‑operación**: si la lista pedida es idéntica a la vigente —mismos productos, mismas etiquetas, mismo orden—, no se escribe nada.

La alternativa aparentemente más cuidadosa —casar por producto y actualizar en su sitio para preservar la identidad de las filas— es la que **crea** el problema. Con tres índices únicos, intercambiar dos posiciones es un ciclo de actualizaciones que el planificador de comandos de EF no puede ordenar, porque no puede partir un `UPDATE` en borrado más alta:

```
borrar + insertar                       actualizar en sitio
  DELETE m1 (orden 0) ─┐                  UPDATE m1: 0 -> 1  ─┐
  DELETE m2 (orden 1) ─┼─> INSERT (0)     UPDATE m2: 1 -> 0  <┘ y viceversa
                       └─> INSERT (1)
  grafo ACÍCLICO                          CICLO
```

Nadie referencia el `Id` de un miembro —ni el esquema `ai`, que indexa por producto; ni el feed, que emite por producto; ni ninguna clave foránea—, así que preservar la identidad no compra nada y cuesta el ciclo. El coste declarado es que `CreatedAt` deja de ser la fecha de alta en la familia; si algún día hace falta historial de pertenencia, es una tabla de auditoría, no un retoque de esta.

### Tests

Nomenclatura .NET `Method_Scenario_ExpectedResult`.

| Test | Tipo | Qué protege |
|---|---|---|
| `CreateFamily_WithMembers_PersistsOrder` | integración | Ficha. El orden declarado se persiste |
| `AddMember_WhenProductAlreadyInAnotherFamily_ReturnsConflict` | integración | Ficha. El invariante central, por la puerta de la API |
| `GetFamily_ReturnsSiblingsOrderedBySortOrder` | integración | Ficha. Orden de lectura, no de escritura |
| `RemoveMember_KeepsFamilyWhenOthersRemain` | integración | Ficha. El reemplazo no arrastra la familia |
| `ReplaceMembers_WithEmptyList_LeavesFamilyWithoutMembers` | integración | Vaciar es disolver sin borrar |
| `ReplaceMembers_ReorderingExistingMembers_Succeeds` | integración | **Decide si hace falta escalonar la escritura** en una transacción explícita |
| `ReplaceMembers_SwappingTwoVariantLabels_Succeeds` | integración | El caso de ciclo puro, sobre el índice de etiqueta |
| `ReplaceMembers_WithIdenticalList_DoesNotRewriteRows` | integración | Cortocircuito: sin él, cada `PUT` ensucia el cursor de C12 |
| `ReplaceMembers_WithDuplicateVariantLabel_ReturnsBadRequest` | unitario | Dos «M» en la misma familia |
| `ReplaceMembers_WithTwoUnlabelledMembers_Succeeds` | persistencia | Que los `NULL` no colisionen, que es lo que hace útil la nulabilidad |
| `ReplaceMembers_WithSameProductTwice_ReturnsBadRequest` | unitario | Duplicado dentro del propio cuerpo, antes de tocar la base |
| `GetFamily_WhenProductHasNoFamily_Returns204` | integración | El huérfano, que es 1 de cada 7 |
| `GetFamily_WhenProductDoesNotExist_Returns404` | integración | La otra mitad de la distinción |
| `CreateFamily_AsOperator_Returns403` | integración | **Cliente nuevo de la factoría**, no el compartido |
| `CreateFamily_Unauthenticated_Returns401` | integración | Ídem — es la trampa que convierte un 401 legítimo en un 403 que pasa |
| `GetFamily_AsOperator_ReturnsFamily` | integración | La lectura sí es del operador, y sin filtrar por punto de venta |
| `Migration_ProductIdIsUnique` | esquema | Sin él, dos familias por producto **sin ningún error** |
| `Migration_SortOrderIsUniqueWithinFamily` · `Migration_VariantLabelIsUniqueWithinFamily` | esquema | Orden no determinista y etiquetas duplicadas |
| `Migration_DeletingFamily_CascadesToMembers` | esquema | Mitad permisiva de la regla de borrado |
| `Migration_DeletingProduct_IsRestrictedNotCascaded` | esquema | Mitad restrictiva. El valor por defecto del framework es `CASCADE` |
| `Migration_ApprovalColumnsAcceptNull` | esquema | Que la reserva para C18 no obligue a inventar un revisor |
| `Model_HasNoPendingMigrationDifferences` | ya existe | Global, cubre esta migración sin tocarlo |

**`SchemaAssert` no se extiende.** Las siete aserciones que este change necesita ya existen. Se respeta el guardarraíl que C04 escribió para sí mismo: solo lo que el change necesita hoy.

**Verificación del propio arnés:** romper a propósito lo que cada detector vigila —quitar la unicidad, cambiar `RESTRICT` por `CASCADE`—, comprobar que falla **exactamente** ese detector y ninguno más, y revertir.

**Línea base primero.** `git stash push -u` → `dotnet test` → `git stash pop`, antes de escribir nada, comparando **nombres** de tests fallidos y nunca recuentos.

---

## Arquitectura

**Frontera de responsabilidad (§6.2).** *Python calcula parecidos y redacta; .NET calcula números y decide.* `ProductFamily` y `ProductFamilyMember` son .NET porque el §6.2 los clasifica literalmente como **datos de negocio revisables por humanos**, en la misma fila que `ProductAiProfile`. Este change **no llama a `jbg-ai` ni una vez** y no le da acceso a nada.

**Frontera de propiedad (§6.3).** Intacta. `ai.product_document.family_id` es un `uuid` plano **sin clave foránea**, precisamente para no acoplar el ciclo de vida de los dos esquemas; quien lo rellena es el indexador a través del feed de C12.

**Decisiones previas que se heredan.**

- **C04** fijó el criterio de qué merece un test de esquema —*el valor está entero en las propiedades que están mal sin producir ningún error*— y montó el arnés de dos capas. C07 es el tercero de los cinco herederos previstos.
- **C05** creó `ai.product_document` con `family_id`, `family_name`, `variant_label` y su índice B‑tree, lo que determina que la familia debe tener **identificador `uuid`**, **nombre** y **etiqueta por miembro**.
- **C08** excluyó la pertenencia a familia de sus campos sensibles y la adjudicó aquí, para no sostener dos autoridades sobre lo mismo. También dejó escrito el patrón de traducción de la violación de unicidad y el de reservar almacenamiento a un change sin turno de migración.
- **La decisión 2 de la revisión** es el origen: entidad explícita y editable en lugar de clave textual generada.

**Patrones en uso.** Repository + Unit of Work; Service Layer para el caso de uso; DTOs con mapeo a mano; FluentValidation invocada explícitamente; configuración de EF por `IEntityTypeConfiguration<T>` descubierta por ensamblado.

**Control de acceso.** Escritura **solo Administrador**, como el resto de la administración de catálogo (`ProductComponentsController`, `ComponentTemplatesController`). Lectura para **cualquier usuario autenticado y sin filtrado por punto de venta**: la pertenencia a familia es un hecho del catálogo, no del inventario. Filtrar hermanos por POS metería lógica de stock dentro de un change de dominio y haría el orden dependiente de la existencia; ese filtrado pertenece a la venta asistida de C30/C34, que ya tiene su contexto.

**Breaking changes.** **Ninguno.** Los cinco endpoints son nuevos, `Product` no cambia, `ai-service/openapi.json` no se toca y ninguna spec viva se modifica. La única alteración de comportamiento posible sería el `CASCADE` desde la familia, que solo afecta a filas que este change crea.

---

## Definición de Hecho (DoD)

- [ ] Dos entidades, sus configuraciones de EF y **una única migración** aplicable, con `dotnet build` limpio
- [ ] `Model_HasNoPendingMigrationDifferences` en verde
- [ ] Detectores de esquema en verde y **cada uno verificado rompiendo a propósito lo que vigila**, con la rotura revertida
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus; integración con Testcontainers; nomenclatura `Método_Escenario_ResultadoEsperado`; cobertura ≥70 % del código nuevo
- [ ] **Línea base de la suite medida antes de empezar** y comparada por nombres de test, no por recuento
- [ ] Los cinco endpoints responden 403 a operador en escritura, 401 sin autenticar, 409 ante doble pertenencia con mensaje accionable, y 204 frente a 404 en la consulta de familia
- [ ] Reordenar e intercambiar etiquetas funciona, y repetir la misma lista **no reescribe filas**
- [ ] Specs del change en `openspec/changes/add-product-family-entity/specs/product-family/` y **`openspec validate --all --strict` con `0 failed`**
- [ ] Documentación actualizada: `Documentos/modelo-de-datos.md` (dos entidades, índices, reglas de borrado y **la distinción explícita frente a `Collection`**), `Documentos/epicas.md` (EP13), `openspec/project.md` (*Key Entities* y regla de negocio nueva), `backend/README.md` (endpoints y matriz de autorización)
- [ ] **§0 del plan de changes actualizado** con la corrección de zona, la reserva para C18 y las dos obligaciones heredadas por C12
- [ ] `ai-service/openapi.json` **sin modificar** y suite de `ai-service` sin ejecutar cambios: este change no cruza la frontera
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] UI: **no aplica** — este change no tiene interfaz

---

## Requisitos No Funcionales

- **Seguridad:** RBAC con escritura restringida a Administrador y lectura para usuario autenticado. **No hay scoping por punto de venta y es deliberado**: la familia no pertenece a ningún POS, y añadir aquí un filtro por inventario mezclaría dos autoridades. El operador no gana ninguna capacidad de escritura sobre el catálogo.
- **Rendimiento y free‑tier:** sin listas expuestas, luego sin paginación que dimensionar. Las dos lecturas son puntuales y con `Include` acotado a una familia; el respeto al pool de 5‑10 conexiones sale de que cada operación es una transacción corta. El cortocircuito de no‑operación evita escrituras inútiles y, con ellas, trabajo de reindexado inventado aguas abajo.
- **Observabilidad:** logging estructurado con Serilog. Se registran la familia, el número de miembros resultante y los productos en conflicto cuando se rechaza por doble pertenencia; **los nombres de producto no suben de nivel Debug**, por la misma razón por la que la consulta del operador no lo hace en C03/C04.
- **Integridad de datos:** los tres invariantes —un producto en una familia, un orden por familia, una etiqueta por familia— garantizados por **índices únicos en la base**, no por comprobaciones aplicativas. Borrado restringido hacia `Product` y hacia `User`, en cascada hacia los miembros. **Ninguna escritura sobre `Product`** en ningún camino de código.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿Debe el reemplazo de miembros **preservar la identidad** de las filas que no cambian? | **No.** Borrar e insertar. Preservar la identidad exige actualizar en su sitio, y eso es lo que convierte un intercambio de posiciones en un ciclo que EF no puede ordenar. Nadie referencia el `Id` de un miembro. Coste asumido y documentado: `CreatedAt` no es la fecha de alta en la familia |
| 2 | ¿Longitud de `VariantLabel`? | **`varchar(50)`.** «talla 12 ajustable» cabe de sobra, y el vocabulario lo cerrará C18 al detectarlo — igual que C09 cerrará el de materiales |
| 3 | ¿Debe `POST /api/product-families` aceptar miembros en la creación? | **Sí, opcionales.** `CreateFamily_WithMembers_PersistsOrder` lo da por hecho, y obligar a dos llamadas para el caso normal es fricción sin ganancia |
| 4 | ¿`GET /api/product-families/{id}` para cualquier autenticado o solo Administrador? | **Cualquier autenticado**, por simetría con la consulta por producto: es el mismo hecho de catálogo leído por otra puerta |
| 5 | ¿Se expone algún recuento de familias, de huérfanos o algún listado? | **No.** Toda lectura agregada es de C18. Añadir «solo un contador» es la vía por la que un change sin superficie de lectura acaba con tres |
| 6 | ¿Debe `PUT /api/product-families/{id}` (metadatos) tocar las filas de los miembros para que el cursor de C12 los vea? | **No.** Se resuelve con `IX_ProductFamilies_UpdatedAt` y uniendo por familia en el feed. Amplificar escrituras para servir a un lector futuro es acoplarse a un diseño que todavía no existe |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta**, pese al 🟢. No está en la ruta crítica, pero **desbloquea C12 🔴, C18 y C30 🔴**, y el §6 del plan lo lista entre los que nunca se recortan. Además ocupa el turno único de migración de EF Core, que es un recurso compartido con C19, C27 y C29.
- **Estimación:** **5 SP** *(pendiente de validar en refinamiento)*. Más estrecho que C08 —un solo lenguaje, ningún contrato que renegociar, ninguna llamada saliente—; la carga está en dos entidades relacionadas, cinco endpoints, tres índices únicos que interactúan entre sí en el reordenado y siete aserciones de esquema.
- **Dependencias:** ninguna. **Bloquea** a C12, C18 y C30. **No solapar** con ningún otro change 🗄️.
- **Línea de corte:** si desborda la sesión (regla 5 del plan), primero **entidades + configuración + migración + detectores de esquema** —mitad archivable que libera el turno de migración y adelanta medio prerrequisito de C12—; después **repositorio + servicio + endpoints + tests de API**, que no lleva migración y convive con cualquier otro change.
- **Tags:** `HU-AIENG-007`, `C07`, `EP13`, `backend`, `dotnet`, `ef-core`, `migration`, `catalog`, `variants`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-007](../../../../Documentos/Historias/AI-Eng/HU-AIENG-007.md)
- **Change OpenSpec:** `openspec/changes/add-product-family-entity/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C07, §0 revisiones, reglas de asignación, reglas transversales de testing) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (**§3 decisión 2**, §6.2, §6.3, §7.2, §7.4, **§7.5**, §7.8) · [especificaciones funcionales v2](../../../../Documentos/Proyecto%20Final%20AIEng/joiabagur-ia-especificaciones-funcionales-v2.md) (§1 campos eliminados, §4.4 reglas funcionales, §4.6 modelo de datos)
- **Apuntes del Máster (S6):** [Calidad del Dato y decisiones de Arquitectura](../../../../Documentos/Sesiones%20Master%20AIEng/S6_Fundamentos_Data_Driven_AI/Calidad%20del%20Dato%20y%20decisiones%20de%20Arquitectura.md) · [Limpieza, Normalizacion y Validacion de datos](../../../../Documentos/Sesiones%20Master%20AIEng/S6_Fundamentos_Data_Driven_AI/Limpieza,%20Normalizacion%20y%20Validacion%20de%20datos.md)
- **Specs vivas relacionadas (ninguna se modifica):** `openspec/specs/product-management/spec.md` (`Collection`, el otro eje) · `openspec/specs/product-ai-profile/spec.md` (ignora la familia a propósito) · `openspec/specs/ai-vector-schema/spec.md` (consumidor aguas abajo, ya reserva `family_id`)
- **Precedentes de código, verificados línea a línea:**
  - `ComponentTemplateConfiguration.cs:31` (`Cascade` padre → hijos) y `ComponentTemplateItemConfiguration.cs:33` (`Restrict` hijo → entidad referenciada, más unicidad compuesta) — **el reparto de borrado que C07 reproduce**
  - `ComponentTemplateService.cs:85` (`template.Items.Clear()` + re‑añadir) — el reemplazo declarativo de la colección hija
  - `ProductAiProfileService.cs:165,226` (`UniqueViolationSqlState = "23505"` leído de `DbException.SqlState`, no de `PostgresException`) — traducción del conflicto sin que `Application` referencie el driver
  - `ProductAiProfileConfiguration.cs` — declarar a mano todo lo que falla en silencio, y por qué nunca un `ENUM` nativo
  - `ProductsController.cs:180` (`Conflict(new { error = ex.Message })`) y su validación explícita — la forma del 409 en este repositorio
  - `ComponentTemplatesController.cs:13` (`[Route("api/component-templates")]`) — ruta literal kebab‑case, el precedente correcto para `api/product-families`
  - `SchemaAssert.cs:41,52,67,83,120,138` (las seis preguntas ya disponibles, `IndexIsUniqueAsync` incluida) y `ProductAiProfileSchemaTests.cs` — el arnés heredado, que **no hay que extender**
  - `TestDataMother.cs:35‑70` (ocho fábricas fluidas, ninguna de familia) — dónde encaja `ProductFamilyMother`
- **Contrato:** `ai-service/openapi.json` — **este change NO lo modifica**
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-16 | `/enrich-us` | Creación del ticket a partir de HU-AIENG-007 y de la sesión de exploración previa al proposal. Recoge las decisiones cerradas en esa sesión —superficie de API mínima coherente, reemplazo declarativo de miembros, etiqueta de variante opcional y única por familia, matriz de autorización con lectura abierta, reserva del almacenamiento de aprobación para C18, y distinción entre producto huérfano y producto inexistente—, el análisis de la estrategia de escritura frente a los tres índices únicos, y las dos obligaciones que quedan adjudicadas a C12 |
