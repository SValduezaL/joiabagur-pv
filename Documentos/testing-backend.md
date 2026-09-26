# Testing Backend - Guía Completa

## Visión General

Stack de testing seleccionado para el backend .NET 10 del sistema de gestión de puntos de venta.

| Componente | Tecnología | Versión |
|------------|------------|---------|
| **Framework de Testing** | xUnit | 2.9.x |
| **Mocking** | Moq | 4.20.x |
| **Assertions** | FluentAssertions | 7.x |
| **CI/CD** | GitHub Actions | - |
| **Tests de Integración** | Testcontainers | 4.x |
| **Generación de Datos** | Bogus | 35.x |

---

## 📚 Índice de Documentación

### Configuración Inicial
| Documento | Descripción |
|-----------|-------------|
| [01 - Configuración](Testing/Backend/01-configuracion.md) | Stack tecnológico, paquetes NuGet, estructura de proyecto y convenciones |

### Tests Unitarios
| Documento | Descripción |
|-----------|-------------|
| [02 - Tests Unitarios](Testing/Backend/02-tests-unitarios.md) | Ejemplos básicos, [Theory], excepciones y generación de datos con Bogus |
| [04 - Mocking EF Core](Testing/Backend/04-mocking-efcore.md) | Mockear DbContext, DbSet, transacciones y uso de InMemory Database |
| [08 - Validaciones](Testing/Backend/08-validaciones.md) | FluentValidation.TestHelper, DataAnnotations y validaciones async |

### Tests de Integración
| Documento | Descripción |
|-----------|-------------|
| [03 - Testcontainers](Testing/Backend/03-testcontainers.md) | PostgreSQL en Docker, fixtures, Respawn y tests de repositorio/API |
| [05 - Autenticación JWT](Testing/Backend/05-autenticacion-jwt.md) | Generar tokens de test, roles, refresh tokens y endpoints protegidos |
| [09 - Archivos y Uploads](Testing/Backend/09-archivos-uploads.md) | Excel con ClosedXML, MockFileSystem y almacenamiento en la nube |

### CI/CD y Calidad
| Documento | Descripción |
|-----------|-------------|
| [06 - GitHub Actions](Testing/Backend/06-github-actions.md) | Workflows, matriz de tests, caché, artifacts y seguridad |
| [07 - Cobertura de Código](Testing/Backend/07-cobertura-codigo.md) | Coverlet, reportes HTML, umbrales mínimos y Codecov |

---

## 🚀 Inicio Rápido

### 1. Crear Proyectos de Test

```bash
# Tests unitarios
cd backend/tests
dotnet new xunit -n Joyeria.UnitTests
cd Joyeria.UnitTests
dotnet add package Moq
dotnet add package FluentAssertions
dotnet add package Bogus

# Tests de integración
cd ..
dotnet new xunit -n Joyeria.IntegrationTests
cd Joyeria.IntegrationTests
dotnet add package Microsoft.AspNetCore.Mvc.Testing
dotnet add package Testcontainers.PostgreSql
dotnet add package Respawn
```

### 2. Ejecutar Tests

```bash
# Todos los tests
dotnet test backend/Joyeria.sln

# Solo unitarios
dotnet test backend/tests/Joyeria.UnitTests

# Con cobertura
dotnet test --collect:"XPlat Code Coverage"

# Filtrar por nombre
dotnet test --filter "FullyQualifiedName~ProductService"
```

---

## 📋 Checklist de Implementación

### Fase 1: Setup Inicial
- [ ] Crear proyecto `Joyeria.UnitTests`
- [ ] Crear proyecto `Joyeria.IntegrationTests`
- [ ] Instalar paquetes NuGet
- [ ] Configurar referencias a proyectos
- [ ] Crear estructura de carpetas

### Fase 2: Tests Unitarios
- [ ] Crear `TestDataBuilder` con Bogus
- [ ] Tests de Services (ProductService, SaleService, etc.)
- [ ] Tests de Validators
- [ ] Tests de mappers/transformaciones

### Fase 3: Tests de Integración
- [ ] Configurar `DatabaseFixture` con Testcontainers
- [ ] Configurar `ApiFixture` con WebApplicationFactory
- [ ] Tests de Repositories
- [ ] Tests de Controllers
- [ ] Tests de autenticación

### Fase 4: CI/CD
- [ ] Crear workflow de GitHub Actions
- [ ] Configurar reporte de tests
- [ ] Configurar cobertura de código
- [ ] Verificar ejecución en PR

### Fase 5: Mantenimiento
- [ ] Añadir badge de tests en README
- [ ] Documentar cómo ejecutar tests localmente
- [ ] Establecer cobertura mínima requerida (70%)
- [ ] Revisar y actualizar tests regularmente

---

## 📖 Convenciones

### Nomenclatura de Tests

```
Método_Escenario_ResultadoEsperado
```

**Ejemplos:**
- `GetProductBySku_WhenProductExists_ShouldReturnProduct`
- `CreateSale_WithInsufficientStock_ShouldThrowException`
- `Login_WithValidCredentials_ShouldReturnToken`

### Estructura AAA

```csharp
[Fact]
public async Task NombreDelTest()
{
    // Arrange - Preparar datos y mocks
    
    // Act - Ejecutar la acción a testear
    
    // Assert - Verificar resultados
}
```

### Helpers compartidos

Viven en `backend/src/JoiabagurPV.Tests/TestHelpers/` y están pensados para reutilizarse, no para copiarse:

| Helper | Para qué sirve |
|---|---|
| `Mothers/` | Constructores de entidades de prueba (patrón *object mother*) |
| `FakeHttpMessageHandler` | Programa respuestas de un servicio externo y **cuenta las peticiones emitidas**, sin red ni contenedor |
| `RecordingLoggerProvider` | Captura eventos de log con su plantilla, propiedades nombradas y *scopes*, para afirmar sobre la traza |
| `RepositoryRoot` | Localiza la raíz del repositorio para leer artefactos externos al backend, como `ai-service/openapi.json` |
| `SchemaAssert` | Lee del catálogo de PostgreSQL la forma que una migración produjo de verdad: tipo y nulabilidad de una columna, longitud máxima, columnas de un índice **en orden**, y regla de borrado de una clave foránea |

Sobre los dos primeros conviene una precisión que ahorra tests engañosos. Al probar un cliente HTTP, **el tipo de excepción no distingue** una condición permanente bien tratada de una mal reintentada: un predicado que reintenta todo acaba lanzando la misma excepción, solo que más tarde. Lo que sí discrimina es el **número de peticiones emitidas**, y por eso `FakeHttpMessageHandler` lo expone. De forma equivalente, una regla que solo vive en el código —por ejemplo, que un texto libre no rebase el nivel `Debug`— desaparece en el primer refactor si nada la afirma: para eso está `RecordingLoggerProvider`.

`SchemaAssert` responde a la misma lógica una capa más abajo. Un test que solo comprueba que *la migración aplica* es teatro: el `TestDatabaseFixture` ya migra antes de cada test de integración, así que no descarta ninguna hipótesis. Lo que merece afirmarse es lo que **falla sin dar error**: una columna que nace `text` en lugar de `jsonb` y no se nota hasta que alguien la consulta meses después, un índice compuesto con las columnas invertidas que sigue existiendo y simplemente deja de servir a su consulta, o una regla de borrado que se quedó en el valor por defecto —que para relaciones obligatorias es en cascada— y el día de la primera purga se lleva por delante datos de negocio. Introducido por C04 y pensado para que las migraciones pendientes escriban sus aserciones en unas pocas líneas: solo contiene las preguntas que hicieron falta, y se amplía cuando haga falta otra.

---

## ⚠️ Estado de la suite: fallos conocidos

*Medido el 2026-08-11 sobre `c04-add-product-search-event-tracking`, con la rama guardada en `git stash` para aislar la línea base. .NET 10, Docker levantado.*

**585 tests, 52 fallos.** Ninguno tiene que ver con el código de aplicación en producción: son defectos de los propios tests y desajustes de dependencias. Se documentan aquí porque, sin este registro, cada persona que ejecuta la suite pierde una hora concluyendo que ha roto algo.

> **Actualización del 2026-08-16, sobre `c08-add-product-ai-profile-entity`.** La suite tiene ahora
> **729 tests** y los fallos se mueven en la banda de **45 a 51** según la ejecución. La cifra
> anterior sigue siendo válida como lo que era —una medición de aquel día sobre aquella rama—,
> pero quien ejecute la suite hoy no reconocerá ni el total ni el número de rojos.
>
> Lo importante de esta segunda medición no es el total, sino algo que la primera no registró:
> **el conjunto de fallos cambia entre ejecuciones idénticas**. Dos pasadas consecutivas sobre el
> mismo commit, sin tocar nada, dieron 48 y 51; dos pasadas posteriores dieron 46 y 48, y los
> nombres no coincidían. `InventoryIntegrationTests` baraja los suyos de una vez a otra.
>
> **Consecuencia práctica:** comparar recuentos no sirve para nada, ni siquiera para decidir que
> algo va mejor. La única comparación válida es **por nombres de test**, y un nombre nuevo en la
> lista solo cuenta como regresión si además falla al ejecutarlo en aislamiento. El procedimiento
> completo, con el caso concreto de tres nombres que parecían regresión y no lo eran, está en
> `openspec/changes/archive/2026-08-16-add-product-ai-profile-entity/qa.md` §1.1.

> **Actualización del 2026-08-17, sobre `c07-add-product-family-entity`.** La suite tiene ahora
> **771 tests** y **44 fallos**. La línea base de ese change, medida antes de escribir una línea de
> código, dio **729 y 49** — dentro de la banda que registró C08.
>
> Esta tercera medición aporta la confirmación que a la anterior le faltaba. Se ejecutó la suite
> completa dos veces sobre la misma rama, con la única diferencia de que entre una y otra el código
> **solo ganó tests**: la primera pasada trajo **tres** nombres nuevos y la segunda **uno distinto**,
> con los conjuntos **disjuntos** y los cuatro verdes al ejecutarlos en aislamiento. Un fallo real no
> desaparece solo. Eso convierte la no determinación del conjunto de fallos de sospecha razonable en
> hecho comprobado, y cierra la pregunta de si comparar recuentos podría servir «al menos para ver
> la tendencia»: no sirve.

> **Actualización del 2026-08-30, sobre `c17-add-ai-service-deployment`.** La suite tiene ahora
> **890 tests** y **53 fallos** en la línea base, y **897 y 54** al cierre del change — los siete de
> más son los siete tests nuevos de C17, todos verdes.
>
> Esta cuarta medición añade una tercera pasada al expediente de la no determinación, y con ella
> el argumento queda cerrado del todo. La comparación por nombres entre la línea base y el cierre
> **no dio un subconjunto limpio**: aparecieron 10 nombres y desaparecieron 9, casi todos de
> `InventoryIntegrationTests`. Antes de concluir nada se ejecutaron **esas mismas clases en
> aislamiento**, sobre el mismo árbol y sin recompilar, y salieron **14 fallos con nombres que no
> estaban ni en la línea base ni en el cierre**.
>
> Es decir: **tres ejecuciones del mismo código dieron tres conjuntos distintos**. Ninguna de las
> clases que se mueven es tocada por C17 —el change no entra en inventario, devoluciones, productos
> ni ventas—, y lo que sí toca está cubierto por siete tests nuevos en verde. El detalle está en
> `openspec/changes/archive/2026-08-30-add-ai-service-deployment/qa.md` §2.1.
>
> **Efecto colateral que conviene conocer:** añadir una clase de integración a la colección
> compartida cambia el orden y los tiempos, y con ellos **cuáles** de los tests dependientes del
> orden caen. No cambia que caigan.
>
> El procedimiento y el detalle de las dos pasadas están en
> `openspec/changes/archive/2026-08-17-add-product-family-entity/qa.md` §1.1.

> **Actualización del 2026-08-28, sobre `c15-add-dotnet-ai-search-endpoint`.** La suite tiene ahora
> **882 tests**. La línea base de ese change dio **829 y 54**; tras implementarlo, **874 y 48**; y
> tras una segunda tanda de arreglos, **882 y 49**.
>
> La aportación de esta cuarta medición es sobre la **misma clase de siempre**. `InventoryIntegrationTests`
> produjo **cuatro conjuntos distintos de fallos en cuatro ejecuciones**: 10 en la línea base, 4 tras
> implementar, **7 al ejecutarla en aislamiento sobre ese mismo código**, y 4 otra vez —con nombres
> diferentes— tras los arreglos. La pasada en aislamiento es la que zanja el asunto: ninguno de los
> cuatro «fallos nuevos» de la suite completa aparecía al correr la clase sola, y uno que «había
> dejado de fallar» sí fallaba allí.
>
> Es también un aviso sobre el propio procedimiento. Los recuentos de esta tanda **bajaron** —de 54
> a 48— y aun así el change contenía un defecto real, encontrado por revisión y no por la suite: la
> política de limitación de peticiones particionaba por dirección de red en vez de por usuario,
> porque `UseRateLimiter()` corría antes de `UseAuthentication()`. Un número que mejora no dice nada,
> ni sobre la salud de la suite ni sobre la del código.

> **Actualización del 2026-08-29, sobre `c16-add-frontend-assisted-search-panel`.** La suite tiene
> ahora **890 tests**. Línea base **882 y 48**; tras implementar, **890 y 49**; tras corregir un test
> propio, **890 y 49** otra vez.
>
> Esta quinta medición aporta la **prueba directa** de lo que las cuatro anteriores venían
> sospechando. Se ejecutó dos veces la suite completa **sobre el mismo código** y los conjuntos de
> fallos difirieron en **trece nombres**, todos confinados a tres clases: `InventoryIntegrationTests`,
> `PaymentMethodsControllerTests` y `ReturnsControllerTests`. No es que el conjunto «se mueva a
> veces»: se mueve entre dos pasadas idénticas, y siempre dentro de las mismas clases.
>
> El recuento subió de 48 a 49 y aun así **no había ninguna regresión**: de los siete fallos nuevos,
> seis eran ese churn y uno era un test recién escrito que fallaba por una razón legítima —borraba
> ventas para aislar una comparación, y una venta está referenciada por su movimiento de inventario—.
> La comparación por nombres lo separó en un minuto; el recuento habría dicho «has roto algo».
>
> Aviso para quien escriba tests aquí: **no borres ventas**. `FK_InventoryMovements_Sales_SaleId` lo
> impide, y el error llega como un `DbUpdateException` genérico cuyo detalle PostgreSQL redacta salvo
> que la cadena de conexión pida `Include Error Detail`. Para observar dos ventas por separado,
> créalas consecutivamente y compáralas entre sí.
>
> El procedimiento y las cuatro pasadas están en
> `openspec/changes/archive/2026-08-28-add-dotnet-ai-search-endpoint/qa.md` §1.1 y §10.

> **Actualización del 2026-08-31, sobre `c18a-add-family-suggestion-and-approval`.** La suite tiene
> ahora **920 tests**. La línea base de ese change dio **897 y 47**, y al cierre **907 y 50**.
>
> Esta medición aporta el caso **más limpio de todos**, y por eso conviene tenerlo a mano cuando
> alguien pregunte si de verdad hace falta comparar por nombres. Al verificar el change se ejecutó
> la suite completa **dos veces seguidas sobre el mismo árbol**, sin recompilar y sin tocar una sola
> línea entre las dos: **51 fallos la primera y 50 la segunda**. No hay aquí tests nuevos de por
> medio ni orden alterado entre pasadas; el mismo binario, dos números. Los 50 se reparten por **17
> clases**, y **ninguna es de las que el change toca**: cero fallos en `FamilySuggestionControllerTests`,
> `AiGatewayFamilySuggestionTests`, `AiCatalogControllerTests` y cualquier `ProductFamily*`. La clase
> nueva, ejecutada aparte, pasa 13 de 13.
>
> **Un descuadre anotado y sin explicar:** el cierre registró 907 tests descubiertos y la verificación
> descubre 920, con un solo test añadido entre medias. La diferencia no sale del change y no se
> rastreó. Queda escrito porque un recuento que aparece de la nada es exactamente lo que esta
> sección advierte que no debe usarse como señal.
>
> El detalle está en
> `openspec/changes/archive/2026-08-31-add-family-suggestion-and-approval/qa.md` §2 y §11.

> **Actualización del 2026-09-01, sobre `c18b-add-family-review-ui-and-orphan-alert`.** La suite
> tiene ahora **973 tests**. La línea base de ese change dio **920 y 47**; al cierre **951 y 51**; y
> tras la pasada de verificación, que añadió 22 tests, **973** con **49 y 52 fallos en dos
> ejecuciones del mismo código**. La inestabilidad que la entrada anterior documentaba sigue igual
> de viva.
>
> **Actualización del 2026-09-05, sobre `c22-add-pos-projection-soft-prefilter`.** La suite tiene
> ahora **984 tests**: C22 añade 11 —cinco de `IndexFeedSalesClockTests`, cinco de
> `IndexFeedRegistrationTests` y dos de `AiIndexFeedPosTests`, uno de ellos el que fija que
> `lastSaleAt` no se mueva por una venta posterior al instante de referencia—. La línea base del
> change dio **52 fallos de 973**; al cierre, **53 de 984**.
>
> **Y esa diferencia de un fallo es ruido, medido y no supuesto.** Comparados por nombre aparecen
> 7 y desaparecen 6, todos `22001: value too long for type character varying(20)` — el teléfono de
> Bogus que documenta la entrada de más abajo. Para descartar que fuera del change se ejecutaron
> **dos veces las dos clases que rotan** (`InventoryIntegrationTests`, `ReturnsControllerTests`)
> sobre el **mismo binario y con `--no-build`**: 11 y 13 fallos, con **10 nombres de diferencia**.
> Más rotación sin tocar una línea que la que había entre línea base y cierre.
>
> **Las clases del feed de indexación están limpias:** cero fallos en `AiIndexFeedCatalogTests`,
> `AiIndexFeedPosTests`, `AiIndexFeedAuthTests`, `IndexFeedRegistrationTests`,
> `IndexFeedSalesClockTests`, `IndexFeedAggregateHashTests`, `IndexFeedKeyComparerTests` y
> `AiContractSnapshotTests` — 68 de 68.

> **Las clases de familia siguen limpias:** cero fallos en `FamilyReviewControllerTests`,
> `FamilyReviewVerdictSchemaTests`, `ProductFamiliesControllerTests`, `ProductFamilySchemaTests`,
> `AiCatalogControllerTests`, `FamilySuggestionControllerTests` y `AiGatewayFamilyAuditTests`. Las
> siete, ejecutadas aparte, pasan **133 de 133**.
>
> **Y esta medición aporta una trampa nueva que conviene conocer antes de perder una hora con ella:
> `DashboardServiceTests` aparece entre los fallos y no estaba en la línea base.** No es una
> regresión de nada:
>
> ```csharp
> var now = DateTime.UtcNow;
> CreateSale(posId, pmId, 200m, 1, now.AddDays(-5), "Efectivo"),   // hoy: 27 de agosto
> ...
> result.MonthlyRevenue.Should().Be(450m);                          // exige que las dos sean del mismo mes
> ```
>
> `GetGlobalStatsAsync_WithSalesToday_ShouldReturnCorrectKPIs` construye sus ventas restando días al
> reloj y luego afirma un total **mensual**. La línea base se midió el **31 de agosto**, cuando
> `now-5d` seguía siendo agosto; la verificación es del **1 de septiembre**, y esos cinco días caen
> en el mes anterior, así que `MonthlyRevenue` baja de 450 a 250. Lo mismo con la devolución de
> `now-2d` y su `MonthlyReturnsCount`.
>
> Es decir: **este test falla los primeros cinco días de cada mes y pasa los otros veinticinco**, en
> un fichero que aquel change no toca. Queda anotado como candidato a arreglo —debería anclar sus
> fechas al mes en curso en vez de restar días a `UtcNow`— y, mientras tanto, como aviso: si lo ves
> en rojo a principios de mes, mira el calendario antes que tu diff.
>
> **Otras dos trampas de método**, ambas de esa misma pasada. `dotnet test` **sale con código 0
> aunque la compilación falle**: con la API de desarrollo levantada, MSBuild no puede copiar las DLL
> porque el proceso las bloquea, la compilación muere y el comando informa éxito. Y **filtrar a una
> sola clase de integración tampoco vale**: `ResetDatabaseAsync` corre en `InitializeAsync` y
> Respawn revienta con *«No tables found»* si ninguna otra clase de la colección ha creado el
> esquema antes. Las dos se leen como veinte tests rotos y ninguna lo es.
>
> El detalle está en
> `openspec/changes/archive/2026-09-01-add-family-review-ui-and-orphan-alert/qa.md` §2 y §11.

> **Actualización del 2026-09-13, sobre `c28-add-profile-review-ui-and-metrics`.** La suite tiene
> ahora **1.060 tests**: C28 añade 76 —62 unitarios repartidos en cuatro clases nuevas y 14 de
> integración en `ProfileReviewControllerTests`, doce de ellos las dos teorías de permisos sobre las
> seis rutas—. La línea base dio **52 fallos de 984**; al cierre, **46 de 1.060**. Comparados por
> **nombre**, catorce de las diecisiete clases con fallos tienen recuento idéntico; las tres que se
> mueven son `InventoryIntegrationTests` (10 → 4), `SalesControllerTests` (5 → 4) y
> `ReturnsControllerTests` (4 → 5), las de siempre. **Cero fallos en los 77 tests del change.**
>
> **Esta quinta medición aporta la variación más extrema del expediente, y por un orden de
> magnitud.** Sobre el **mismo árbol limpio**, verificado con `git stash push -u`, dos ejecuciones
> de la línea base dieron **420 fallos en una pasada de 42 segundos y 52 en otra de 10 minutos**.
> No son dos conjuntos distintos del mismo tamaño como en las cuatro mediciones anteriores: es un
> factor de ocho. La diferencia de duración señala la causa —la pasada rápida no llegó a levantar
> los Testcontainers y los ~370 tests de integración cayeron en bloque— y de ahí sale la regla
> práctica que conviene añadir a las de más abajo:
>
> **Antes de comparar nada, mira la duración.** Una pasada de la suite completa que termine en
> menos de un minuto **no ha ejecutado la integración**, y su recuento no es comparable con nada.
> El recuento por sí solo no lo delata: 420 parece una regresión catastrófica y es un contenedor
> que no arrancó.
>
> **Dos trampas de método que ya estaban documentadas más arriba y volvieron a morder**, así que
> quedan confirmadas en una segunda ocasión: la API de desarrollo en marcha bloquea las DLL y la
> compilación muere sin que se ejecute un solo test, y una clase de integración ejecutada **en
> aislamiento** revienta con *«No tables found»* porque `ResetDatabaseAsync` construye Respawn antes
> de que nada haya levantado el host que aplica las migraciones. Lo segundo se resolvió en el
> propio `ProfileReviewControllerTests` pidiendo un cliente a la factoría antes de resetear —lo que
> arranca el host— y así la clase se puede correr sola, que es como se depura.
>
> El detalle está en
> `Documentos/Proyecto Final AIEng/informes/c28-implementation-measurements.md`.

> **Actualización del 2026-09-24, sobre `c40-add-frontend-free-query-panel`.** La suite tiene ahora
> **1.328 tests**: C40 añade **87**. La línea base dio **50 fallos de 1.241**; al cierre, **47 de
> 1.328**. **Cero fallos en el área del change** —`AiCallScope`, `AiGateway`, `FreeQuerySearch`,
> `AssistedSearch`, `SalesAssist`, `Substitutes`, `ProductSearchEvent` y `AiContract`—, comprobado
> con cuatro pasadas dirigidas a lo largo del change y una más en la verificación, con 410 de 410.
>
> **Y ésta es la medición que convierte «compara nombres» en un criterio utilizable**, porque pone
> número a la rotación que las entradas anteriores describían de oído. Dos pasadas completas del
> **mismo commit** `93115cf`, mismo árbol, **sin recompilar entre medias**:
>
> | | Pasada 1 | Pasada 2 |
> |---|---|---|
> | Con error | **50** | **51** |
> | Total | 1.241 | 1.241 |
> | Duración | 8 m 58 s | 8 m 1 s |
>
> Comparadas **por nombre**: **43 estables**, **8 que aparecen sólo en la segunda**, **7 que
> desaparecen tras la primera** — **rotación total de quince nombres**. Y el dato que la hace
> utilizable: **los quince están confinados a dos clases**, 14 en `InventoryIntegrationTests` y 1 en
> `ReturnsControllerTests`. **Cero rotación fuera de ellas.** `PaymentMethodsControllerTests`, la
> tercera del trío histórico, no rotó ese día pero mantiene su fallo fijo.
>
> **Cómo se lee el DoD con esta tabla al lado.** El criterio literal «cero nombres desaparecidos y
> cero nuevos en rojo» **no es alcanzable** en este backend, y exigirlo lleva a perseguir ruido. La
> lectura correcta es: **los nombres que difieran deben caer dentro de las clases inestables
> conocidas, y ninguno en una clase que el change toque.** El único nombre nuevo del cierre de C40 es
> `InventoryIntegrationTests.Operator_ViewStock_ForAssignedPOS_ShouldSucceed`, dentro de ellas.
>
> **La regla de la duración volvió a morder, y de otra forma.** La primera pasada del grupo de cierre
> dio **484 fallos de 1.328 en 2 minutos**, contra 47 en 20. No era una regresión: eran
> `System.TimeoutException` en masa, porque se lanzaron **las tres suites a la vez** y además una
> reconstrucción de la imagen de `jbg-ai`, y Testcontainers no pudo levantar sus contenedores.
> Confirma la regla de la entrada anterior y le añade una causa: **no sólo «mira la duración», sino
> corre la suite del backend en solitario**, sin otra suite ni un build de imagen en paralelo.
>
> El detalle está en
> `Documentos/Proyecto Final AIEng/informes/c40-implementation-measurements.md` §1 y §14.3.

> **Actualización del 2026-09-26, sobre `c40-fix-all-shops-scope-unreachable` (C40_FIX).** La suite
> llega a **1.339 tests** con la implementación (+10) y a **1.347** tras su verificación
> independiente (+8). Cuatro pasadas completas, dos de cada pasada:
>
> | Pasada | Con error | Total |
> |---|---|---|
> | Línea base del implementador, sobre `501c97c` | 45 | 1.329 |
> | Cierre del implementador, sobre `4b1d056` | 52 | 1.339 |
> | Línea base de la verificación, **sobre el mismo `4b1d056`** | **51** | 1.339 |
> | Cierre de la verificación | 53 | 1.347 |
>
> **Cero fallos en el área del change** —`AssistedSearch*`, `AiSearch*`, `FreeQuery*`, `AiScope*`,
> `Availability*`— en las cuatro. Las dos pasadas dirigidas dieron 122/122 y 130/130.
>
> **Y aquí está la medición más fuerte que este documento tiene sobre la rotación.** Las dos pasadas
> completas de la verificación difieren en **doce nombres** —siete entran, cinco salen— y **los doce
> están en `InventoryIntegrationTests`**. Cero rotación fuera de ella: ni una clase más aparece o
> desaparece. La entrada de C40 midió quince nombres repartidos entre dos clases; ésta los concentra
> en una sola, y el `+2` neto del recuento (51 → 53) es **exactamente** el saldo de esa rotación
> (7 − 5), no de los ocho tests nuevos, que salieron los ocho en verde. Nótese además que
> la línea base de la verificación y el cierre del implementador **son el mismo commit y dan 51 y
> 52**: el recuento no identifica un árbol.
>
> **Un corolario de método, que costó una sesión al implementador.** `dotnet test` **desde la raíz
> del repositorio** imprime `MSBUILD : error MSB1003` —no hay solución ahí, vive en
> `backend/src/JoiabagurPV.sln`— y **sale 0 sin ejecutar un solo test**. Es una segunda vía al mismo
> desenlace que el `JoiabagurPV.API.exe` vivo bloqueando `bin/Debug`, y refuerza la única regla que
> vale: **leer la línea de resumen, nunca el código de salida.**
>
> El detalle está en el `qa.md` del change archivado, §1 y §11.9.

> **Actualización del 2026-09-26, sobre `c42-add-frontend-agent-panel` (C42).** La suite tiene ahora
> **1.401 tests**: C42 añade **54** —16 de la pasarela, 21 del servicio de aplicación, 13 de endpoint y
> 4 de arranque—, los 54 en verde. La línea base dio **53 fallos de 1.347**; al cierre, **46 de 1.401**:
> el rojo **baja siete** mientras la suite crece 54.
>
> **La rotación, otra vez confinada.** Cuatro nombres entran y once salen; los cuatro que entran son
> tres de `InventoryIntegrationTests` y uno de `ReturnsControllerTests`, y los once que salen son todos
> de `InventoryIntegrationTests`. **Cero fallos en el área del change** —`Agent*`, `AiGateway*`,
> `AiSearch*`, `AssistedSearch*`, `FreeQuery*`, `AiScope*`— en las dos pasadas.
>
> **Y una tercera vía al mismo desenlace de «sale 0 sin medir nada», que esta entrada añade: medir en
> paralelo.** La primera pasada de C42 lanzó las tres suites del repositorio a la vez y **el backend
> dio 490 fallos de 1.347**. No era regresión ni orden: `vitest` con 14 *workers* satura la máquina y
> **testcontainers deja de alcanzar el demonio de Docker por su tubería con nombre**, así que todos los
> `IntegrationTests` mueren al arrancar con
> `System.TimeoutException at System.IO.Pipes.NamedPipeClientStream.ConnectInternal` bajo
> `Docker.DotNet.DockerClient`. El mismo commit, en serie, da 53.
>
> Es peor que las otras dos vías porque **sí ejecuta tests y sí imprime una línea de resumen**: la
> línea dice 490 y es verdad, sólo que no mide el código. La regla que lo cubre no es la del código de
> salida sino una nueva: **una pasada de las tres suites es serial**, y cuesta unos 20 minutos.
>
> El detalle está en `Documentos/Proyecto Final AIEng/informes/c42-implementation-measurements.md` §1.

### `coverlet` no mide `JoiabagurPV.Application`, y no avisa

**Cualquier cifra de cobertura tomada en este repositorio con el comando por defecto excluye la capa
donde vive la lógica de negocio.** Encontrado en el QA de C34 y **reproducido el 2026-09-26** al
verificar C40_FIX, así que no es una anomalía de una máquina.

```bash
dotnet test --collect:"XPlat Code Coverage"   # el informe NO trae JoiabagurPV.Application
```

El informe Cobertura sale con `JoiabagurPV.API`, `JoiabagurPV.Domain` y `JoiabagurPV.Infrastructure`
y **sin** `JoiabagurPV.Application`. No hay error, no hay aviso: el paquete simplemente no está. Con
`--diag` aparece la causa:

```text
[coverlet]Unable to instrument module: …\JoiabagurPV.Tests\bin\Debug\net10.0\JoiabagurPV.Application.dll
Coverlet.Core.Exceptions.CecilAssemblyResolutionException: AssemblyResolutionException for
'Microsoft.Extensions.Logging.Abstractions, Version=10.0.0.0, …'
```

Ese ensamblado llega del **framework compartido de ASP.NET Core** y nunca se copia al `bin`, así que
Mono.Cecil no lo resuelve y coverlet abandona el módulo entero. **La sugerencia de coverlet,
`-p:CopyLocalLockFileAssemblies=true`, no lo arregla** (probado en C34 y en C40_FIX).

Lo que sí funciona, y hay que deshacerlo después:

1. copiar a `backend/src/JoiabagurPV.Tests/bin/Debug/net10.0/` los `Microsoft.Extensions.*.dll` del
   framework `Microsoft.AspNetCore.App/10.0.11` que no estén ya ahí —fueron **47** las dos veces—,
   sólo para que Cecil los resuelva: en ejecución no cuentan, porque el host carga por `deps.json`;
2. correr con `--no-build`;
3. **borrarlos a continuación** y comprobar que no queda ninguno.

Con eso `JoiabagurPV.Application` aparece en el informe. **Consecuencia práctica:** si el DoD de un
change pide cobertura sobre código nuevo que vive en `Application` —que es donde vive casi todo—, el
comando del README no la mide, y la cifra que devuelve describe la herramienta y no el cambio.

### Por qué se acumularon sin que nadie los viera

Los dos árboles se comportan de forma muy distinta, y esa es la clave:

| Árbol | Tests | Fallos | Desde cuándo se sabe |
|---|---|---|---|
| `UnitTests/` | 315 | **10** | Registrados en el QA de C03 (2026-08-09), **idénticos nombre por nombre** |
| `IntegrationTests/` | 270 | **~42** | **Nunca se habían medido** |

Los de integración necesitan Docker: sin él no se ejecutan, y quien corre la suite en una máquina sin Docker ve 315 tests y 10 fallos, que es exactamente lo que registró C03. En CI sí hay Docker, pero [`test-backend.yml`](../.github/workflows/test-backend.yml) solo se dispara en `push`/`pull_request` a `main` y `develop`, y **todo el Proyecto Final de IA se está construyendo en `ai-eng` y sus ramas de change**. El resultado es un árbol de 270 tests que no se ejecuta ni en local ni en CI durante semanas.

### Los 10 fallos unitarios (estables desde C03)

| Clase | Nº | Causa raíz |
|---|---|---|
| `ImageCompressionServiceTests` | 5 | Umbrales de tamaño comprimido escritos a mano contra una versión anterior de ImageSharp; la actual codifica distinto y produce bytes de más |
| `QrCodeServiceTests` | 2 | `MissingMethodException` sobre `ImageSharp.Image.Load` — **incompatibilidad binaria**: `PdfSharpCore` se compiló contra otra API. Y `PdfSharpCore` rechaza guardar un PDF sin páginas |
| `InventoryServiceTests` | 2 | Expectativas de Moq sobre `BeginTransactionAsync` / `RollbackTransactionAsync` que el servicio ya no invoca |
| `ExcelImportServiceTests` | 1 | La validación devuelve `false` donde el test espera `true` |

Los dos primeros grupos son **deriva de dependencias**, no lógica rota; los dos últimos son tests que se quedaron atrás respecto al código.

### Los ~42 fallos de integración

| Familia | Nº aprox. | Causa raíz |
|---|---|---|
| «Se esperaba 401 y llegó 200 / 403 / 201» | 16 | El `HttpClient` compartido de la clase de test es el que hace los `login`, así que **arrastra sus cookies**: la llamada «anónima» no lo es. Se arregla pidiendo un cliente nuevo a la factoría |
| `Cannot create a DbSet for 'TestEntity'` | 4 | `RepositoryTests` usa una entidad que no está en el modelo del contexto |
| `22001: value too long for character varying(20)` | 4 | Las *object mothers* generan datos con Bogus y el teléfono generado no siempre cabe en `PointOfSale.Phone`. Es **no determinista**, y explica que dos ejecuciones del mismo código den recuentos distintos |
| `UpdatedAt` anterior a `CreatedAt` por microsegundos | 1 | `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct`. Los dos sellos se toman del reloj del sistema dentro de la misma operación y el segundo cae **antes** que el primero por una fracción de milisegundo: *«Expected updated.UpdatedAt to be on or after ‹…16.462865›, but found ‹…16.462797›»*. Medido en **0,6 ms** y en **68 µs** en corridas distintas. **Pasa ejecutado aislado.** La **segunda familia no determinista**, anotada al verificar C34 (§10.9 de su QA) |
| Varios | resto | Concurrencia en venta de última unidad, validaciones de importación, un 500 y un 400 puntuales |

### Cómo distinguir una regresión propia

**Por nombres, no por número.** El recuento varía entre ejecuciones por la familia de Bogus:

```bash
git stash push -u          # guardar el trabajo en curso
dotnet test JoiabagurPV.Tests/JoiabagurPV.Tests.csproj
git stash pop              # recuperarlo
# el cambio está limpio si el CONJUNTO DE NOMBRES que falla es el mismo
```

### Qué haría falta para cerrarlo

No es trabajo de un change de funcionalidad y **merece uno propio**. En orden de rentabilidad: extender el disparador de CI a las ramas de trabajo, para que esto deje de crecer en silencio; arreglar la familia de las cookies, que son 16 tests con una sola corrección; fijar los datos generados que chocan con límites de columna; y alinear ImageSharp con lo que `PdfSharpCore` espera.

Dos de estas familias se toparon y se corrigieron **dentro de los tests nuevos** de C04, así que el patrón de arreglo ya está escrito en `AiSearchEventsControllerTests`.

---

## 🔗 Recursos Externos

- [xUnit Documentation](https://xunit.net/docs/getting-started/netcore/cmdline)
- [FluentAssertions Documentation](https://fluentassertions.com/introduction)
- [Moq Quickstart](https://github.com/moq/moq4/wiki/Quickstart)
- [ASP.NET Core Integration Tests](https://learn.microsoft.com/en-us/aspnet/core/test/integration-tests)
- [Testcontainers .NET](https://dotnet.testcontainers.org/)
- [Unit Testing Best Practices](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices)

---

## 🎯 Conclusión

Esta combinación de herramientas ofrece:

- ✅ **Productividad**: Sintaxis clara y herramientas bien documentadas
- ✅ **Confiabilidad**: Tests reproducibles con contenedores Docker
- ✅ **Escalabilidad**: Fácil de extender y mantener
- ✅ **Integración**: Compatible con GitHub Actions y free-tier
- ✅ **Comunidad**: Amplio soporte y ejemplos disponibles
