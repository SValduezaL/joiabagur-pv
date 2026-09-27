# QA — C04 `add-product-search-event-tracking`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** 2026-08-11 · **Rama:** `c04-add-product-search-event-tracking` · **Commit previo a la implementación:** `e107c1a`
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| SDK | .NET 10.0.302 |
| Proyecto de test | `backend/src/JoiabagurPV.Tests/JoiabagurPV.Tests.csproj` |
| Base de datos | PostgreSQL 15 en Testcontainers, con Docker levantado |
| Herramienta nueva en la máquina | `dotnet-ef` 10.0.0 como herramienta global — no existía y el README del backend la asume |
| Contrato | `ai-service/openapi.json`, **leído** para derivar la longitud del texto de consulta, no modificado |

---

## 1. Suite automática

| Ejecución | Total | Fallos |
|---|---|---|
| **Línea base** (`git stash push -u`, sin código de C04) | 585 | **52** |
| Tras la implementación | 628 | **46** |
| Tras cerrar los huecos del verify | **633** | **51** |

**48 tests nuevos, todos en verde** (43 en la implementación, 5 más al cerrar el verify). `dotnet build`: **0 errores**. Comprobado además que **ninguna clase de C04 aparece entre los fallos**, no solo que el total cuadre.

La línea base se **midió**, no se supuso: se guardó el árbol completo con `git stash push -u`, se ejecutó la suite sobre `e107c1a` y se recuperó con `git stash pop`.

Las tres cifras de fallos —52, 46, 51— son la mejor demostración de por qué **el recuento no sirve como señal**: 633 − 48 = 585, exactamente el total de la línea base, y las tres ejecuciones se mueven en una banda de cinco por la familia de datos generados. Comparar nombres es la única lectura fiable, y por eso es la regla que se llevó a `CLAUDE.md`.

### Desglose de los 48 tests nuevos

| Fichero | Nº | Qué cubre |
|---|---|---|
| `UnitTests/Application/ProductSearchEventServiceTests` | 17 | Proyección, truncado, contador real, origen degradado, episodio, reformulación frente a abandono, ausencia de sobrecarga sin ámbito, derivación de rank, producto ausente, última escritura, propiedad, no propagación de fallos, confidencialidad del texto |
| `IntegrationTests/ProductSearchEventSchemaTests` | 20 | Tipos `jsonb`, longitud del texto, orden del índice compuesto, nulabilidad de doce columnas, las cuatro reglas de borrado |
| `UnitTests/Persistence/MigrationModelDriftTests` | 1 | Desfase entre el modelo y el snapshot de migraciones, **sin base de datos** |
| `IntegrationTests/AiSearchEventsControllerTests` | 10 | 204 con rank derivado, 400 con identificador vacío, 403 ajeno, 403 administrador, 404, 401, atribución de venta, ausencia de rutas de lectura, `SET NULL` real, ciclo completo |

### Los escenarios del spec, uno a uno

| Escenario | Test | Resultado |
|---|---|---|
| 1 · Búsqueda registrada con los campos del servidor | `RecordSearch_WithValidScope_PersistsEventWithServerKnownFields` | ✅ |
| 2 · Búsqueda degradada distinguible | `RecordSearch_WhenOriginIsLexicalFallback_PersistsDistinguishableOrigin` | ✅ |
| 3 · Búsqueda sin resultados | `RecordSearch_WithNoResults_PersistsZeroCountAndEmptyArray` | ✅ |
| 4 · Fallo de telemetría no propaga | `RecordSearch_WhenPersistenceFails_DoesNotThrowAndReturnsNull` | ✅ |
| 5 · Rank derivado en el servidor | `RecordSelection_WithProductInResults_DerivesRankFromStoredList` | ✅ |
| 6 · Producto ausente con rank nulo | `RecordSelection_WhenProductNotInResults_PersistsSelectionWithNullRank` | ✅ |
| 7 · Selección repetida, última gana | `RecordSelection_WhenCalledTwice_KeepsLastSelection` | ✅ |
| 8 · 403 por propiedad, sin excepción de administrador | `RecordSelection_WhenEventBelongsToAnotherUser_Returns403` · `..._WhenCallerIsAdminButNotOwner_Returns403` | ✅ |
| 9 · Truncado por entradas, contador real | `RecordSearch_WithMoreResultsThanCap_StoresOnlyTheCap` · `..._RecordsTrueDisplayedCount` | ✅ |
| 10 · Episodio agrupable | `RecordSearch_WithSessionId_KeepsTheCallerEpisode` | ✅ |
| 11 · Venta declara su búsqueda | `FullCycle_ProjectingARealGatewayResponse_RoundTripsThroughJsonbIntact` | ✅ |
| 12 · Purgar telemetría no destruye ventas | `DeletingSearchEvent_NullsSaleAttribution_WithoutDeletingSale` | ✅ |
| 13 · Texto de consulta no sube de `Debug` | `RecordSearch_QueryTextNeverRisesAboveDebug` | ✅ |
| 14 · Esquema verificado | `Migration_JsonColumnsAreJsonbNotText` · `..._CompositeIndexOrdersPointOfSaleBeforeCreatedAt` · `..._BusinessEntitiesDoNotCascadeIntoTelemetry` · `Model_HasNoPendingMigrationDifferences` | ✅ |
| 15 · Fuera de alcance explícito | Revisión de alcance (§5) | ✅ |

---

## 2. Revisión línea a línea de la migración

El `.cs` generado se leyó entero antes de aceptarlo, porque es el fichero que nadie mira en una revisión y donde los errores no dan error:

| Comprobación | Esperado | En la migración |
|---|---|---|
| `FiltersJson`, `ResultsJson` | `jsonb` | ✅ `jsonb` |
| `SearchText` | 500, del contrato congelado | ✅ `character varying(500)` |
| `TraceId` | acotado y nullable | ✅ `character varying(64)`, nullable |
| Índice compuesto | `PointOfSaleId` **antes** de `CreatedAt` | ✅ `{ "PointOfSaleId", "CreatedAt" }` |
| Evento → usuario / POS / producto | `Restrict` | ✅ los tres |
| Venta → evento | `SetNull` | ✅ `FK_Sales_ProductSearchEvents_SearchEventId` |

**Desviación aceptada:** EF generó además `IX_ProductSearchEvents_UserId` e `IX_ProductSearchEvents_SelectedProductId`, índices automáticos de clave foránea. Se conservan: las reglas `Restrict` obligan a la base a comprobar filas referenciadas antes de borrar un usuario o un producto, y sin ellos esa comprobación sería un recorrido secuencial. Recogido como precisión en la decisión 12 del [design](design.md).

---

## 3. El arnés probado contra sí mismo

La tarea 3.4 pedía comprobar que el arnés **falla** cuando el esquema no es el esperado. Un ayudante que devolviera siempre lo que el test espera pasaría igual y no protegería nada.

Se escribió un test desechable que afirmaba lo contrario en tres puntos y se ejecutó:

| Aserción invertida | Lo que devolvió el catálogo | ¿Falló? |
|---|---|---|
| `ResultsJson` es `text` | `jsonb` | ✅ |
| Índice compuesto en orden `CreatedAt, PointOfSaleId` | `PointOfSaleId, CreatedAt` | ✅ |
| Regla de borrado hacia la venta es `CASCADE` | `SET NULL` | ✅ |

Los tres fallaron como debían, confirmando que el ayudante lee el catálogo real. El fichero se borró acto seguido.

---

## 4. Los 52 fallos preexistentes: diagnóstico, no suposición

Es la parte más larga de este QA porque la primera lectura fue **equivocada** y la corrección tiene valor para el resto del proyecto.

### Lo que se dijo primero, y por qué era incorrecto

La primera conclusión fue *«fallos preexistentes y flaky, el recuento varía entre ejecuciones»*. La variación es cierta, pero «flaky» no describe el conjunto: al abrir los mensajes aparecieron fallos **deterministas** con causas concretas, incluidos tests unitarios puros que no tocan base de datos ni red. Documentar «flaky» habría enterrado cinco defectos distintos bajo una etiqueta que invita a ignorarlos.

### Diagnóstico verificado

Los dos árboles se comportan de forma distinta, y ahí está la explicación:

| Árbol | Tests | Fallos | Desde cuándo se sabe |
|---|---|---|---|
| `UnitTests/` | 315 | **10** | El QA de C03 (2026-08-09) registró exactamente estos 10, **nombre por nombre** |
| `IntegrationTests/` | 270 | **~42** | **Nunca se habían medido** |

C03 registró «315 total» — que es **exactamente el recuento del árbol unitario**. Los de integración necesitan Docker y en aquella sesión no llegaron a ejecutarse. Y en CI tampoco: [`test-backend.yml`](../../../../.github/workflows/test-backend.yml) corre la solución completa sobre `ubuntu-latest`, que sí tiene Docker, **pero solo se dispara en `push`/`pull_request` a `main` y `develop`**, y todo el Proyecto Final se está construyendo en `ai-eng` y sus ramas de change. Un árbol de 270 tests lleva semanas sin ejecutarse ni en local ni en CI.

Eso no es una suite que se haya podrido: es una suite que nadie estaba mirando.

### Familias identificadas

**Unitarios (10, estables desde C03):** umbrales de tamaño comprimido escritos contra una versión anterior de ImageSharp (5); `MissingMethodException` sobre `ImageSharp.Image.Load` por incompatibilidad binaria con `PdfSharpCore`, más un PDF sin páginas (2); expectativas de Moq sobre transacciones que el servicio ya no invoca (2); una validación de importación (1). Los dos primeros son **deriva de dependencias**, no lógica rota.

**Integración (~42):** dieciséis del tipo «se esperaba 401 y llegó 200/403/201», porque el `HttpClient` compartido de la clase es el que hace los `login` y **arrastra sus cookies**; cuatro de `Cannot create a DbSet for 'TestEntity'`; cuatro de `22001: value too long for character varying(20)`, **la única familia genuinamente no determinista** y la que explica que dos ejecuciones del mismo código den recuentos distintos; el resto, casos sueltos.

### Dos de esas familias se toparon dentro de este change

No son teoría: aparecieron escribiendo los tests nuevos y se corrigieron en ellos, así que el patrón de arreglo ya está escrito.

| Familia | Cómo se manifestó aquí | Corrección |
|---|---|---|
| Cliente compartido con cookies | `RecordSelection_WhenUnauthenticated_Returns401` devolvió **204**: la llamada «anónima» llevaba las cookies de los logins previos | Pedir un cliente nuevo a la factoría para la aserción anónima |
| Dato generado que no cabe | `22001` intermitente al crear el punto de venta: Bogus genera teléfonos de longitud variable y la columna es `varchar(20)` | Fijar el campo con `.WithPhone("600123456")`, como ya hacía `SalesControllerTests` |

### Dónde queda registrado

- **[CLAUDE.md](../../../../CLAUDE.md)** — la regla operativa duradera: un recuento en rojo no es señal de regresión, se compara **por nombres** contra la línea base, y las dos trampas concretas con las que tropezará quien escriba el siguiente test. Sin cifras, que caducan.
- **[Documentos/testing-backend.md](../../../../Documentos/testing-backend.md)**, sección *Estado de la suite: fallos conocidos* — el inventario fechado con causas raíz, la explicación del hueco de CI y el orden de rentabilidad para cerrarlo.
- Este QA — lo medido en este change.

**No se ha arreglado ninguno**, y es deliberado: no son de este change y tocarlos habría mezclado dos cosas distintas en un mismo diff. **Merece un change propio**, y el primer punto —extender el disparador de CI a las ramas de trabajo— es el que impide que siga creciendo en silencio.

---

## 5. Comprobaciones de disciplina y alcance

| Comprobación | Resultado |
|---|---|
| `openspec validate --all --strict` | ✅ **31 passed, 0 failed** |
| Ninguna ruta de lectura sobre eventos | ✅ el único endpoint es la selección |
| Sin propiedades de navegación en la entidad | ✅ |
| `ProductSearchEvent` sin `CreatedSaleId` | ✅ el enlace vive en `Sale.SearchEventId` |
| Contrato `ai-service/openapi.json` sin tocar | ✅ solo leído |
| Frontend, `ai-service/`, `terraform/` sin cambios | ✅ |
| Una sola migración | ✅ `20260811061759_AddProductSearchEventTracking` |
| El DTO del cliente tiene un solo campo | ✅ `{ productId }` |

---

## 6. Decisiones tomadas durante la aplicación

| Qué | Decisión | Motivo |
|---|---|---|
| Tarea 1.5, repositorio dedicado | **Descartada** | `IRepository<T>` ya expone `GetByIdAsync`, `AddAsync` y `UpdateAsync`, y está registrado genéricamente. Una interfaz dedicada sería un marcador vacío más una línea de DI |
| Espacio de nombres del test de desfase | `UnitTests.Persistence`, no `UnitTests.Infrastructure` | Dentro de `...Infrastructure` la directiva `using Microsoft.EntityFrameworkCore.Infrastructure` no resuelve: las directivas se buscan primero contra los espacios de nombres contenedores |
| Aserción sobre `ResultsJson` en integración | Sobre el JSON parseado, no sobre el texto | **`jsonb` normaliza el documento**: reordena claves y reescribe separadores. Una aserción por subcadena estaría comprobando el formateo de PostgreSQL, no la proyección |
| Borrado del evento en el test de `SET NULL` | SQL directo | Con EF, el arreglo en memoria anularía la referencia aunque el esquema no estuviera de acuerdo; lo que se quiere probar es la restricción de la base |

---

## 7. Lo que **no** se ha comprobado

- **El camino real de C15**: nadie invoca todavía `RecordSearchAsync` desde un endpoint de búsqueda. La obligación A1 está escrita en el proposal y en la ficha de C15, pero hasta que ese change llegue, la tabla solo se llena desde tests.
- **La escritura de `Sale.SearchEventId`**: la columna existe y su regla de borrado está probada, pero ningún camino de aplicación la escribe. La regla «identificador desconocido ⇒ atribución nula, venta intacta» está especificada y **no implementada**, por lo que tampoco está probada.
- **Volumen real**: los índices se justifican por opción de futuro, no por medición. A ~3.000 filas no hay nada que medir.
- **La reversión de la migración**: omitida con motivo escrito — es generada, no artesanal, y probarla exigiría un contenedor propio.

---

## 8. Huecos detectados en el `/opsx:verify` y cerrados

La verificación no fue un trámite: encontró un defecto crítico **en los propios artefactos** y dos huecos de cobertura. Todos cerrados antes de archivar.

### Crítico — el spec prometía comportamiento que este change no implementa

El requisito *«A sale declares the search it originated from»* afirmaba que la referencia *«MUST be recordable per line»* y describía un escenario *«WHEN a sale is created naming the search event it originated from»*. **Ninguna de las dos cosas existe**: `CreateSaleRequest` y `BulkSaleLineRequest` no tienen ese campo y `SalesService` no lo asigna — verificado, cero referencias. Lo mismo con el párrafo de *«A telemetry failure never propagates»* sobre tolerar un identificador desconocido.

Es exactamente la trampa que la exploración había señalado —*«un requisito especificado y no implementado haría fallar la verificación»*— y que se coló igualmente. Al archivar, esas frases se habrían fundido en una spec viva afirmando comportamiento que el sistema no tiene, que es la clase de defecto contra la que avisa `CLAUDE.md`.

**Corrección:** el requisito se reescribió como *«Sale attribution is carried by the sale, not by the event»*, acotado a lo que el change entrega de verdad —la columna opcional, que el evento no apunta a la venta, y que el KPI sale de la tabla de ventas sola—, y sus escenarios pasaron de *«a sale is created naming…»* a *«a sale is stored with a reference…»*, que sí es cierto y comprobable hoy. El párrafo sobrante se eliminó. **Nada se perdió**: las reglas retiradas ya vivían en el proposal como obligaciones B5 y C1.

### El validador estaba registrado y nadie lo invocaba

Este proyecto **no tiene pipeline de validación automática**: los validadores se inyectan a mano como `IValidator<T>` (patrón de `AuthController`). `RecordSearchSelectionRequestValidator` estaba registrado por el escaneo de ensamblado y ningún código lo llamaba, así que un `productId` vacío llegaba al servicio, no casaba con ningún resultado y persistía una fila basura con rank nulo — justo lo que el diseño quería evitar. Registrado y no invocado es peor que ausente, porque aparenta validación.

**Corrección:** inyectado y validado en el controlador, con `400` como respuesta. Cubierto por `RecordSelection_WithAnEmptyProductId_Returns400AndPersistsNothing`.

### Tres escenarios sin test, y uno a medias

| Escenario | Test añadido |
|---|---|
| *The point-of-sale scope cannot be bypassed* | `RecordSearchAsync_HasNoOverloadTakingABarePointOfSaleIdentifier` — por reflexión, siguiendo el precedente de C03 |
| *Reformulation and abandonment are distinguishable* | `RecordSearch_GroupedByEpisode_TellsReformulationFromAbandonment` |
| *No read route exists* | `Capability_ExposesNoRouteThatReadsSearchEvents` — 404 en las tres rutas de lectura plausibles |
| *A sale can carry its originating search* | `Sale_CanCarryOrOmitItsOriginatingSearch` |
| *«at most the last one carries a selection»* (cláusula suelta) | Aserción añadida a `RecordSearch_WithSessionId_KeepsTheCallerEpisode` |

Al escribir el de reformulación apareció una fragilidad propia: la derivación por `CreatedAt` puede fallar si dos llamadas consecutivas caen en el mismo tic de reloj. Se reescribió por posición en la lista, y se añadió aparte una aserción de orden ascendente de `CreatedAt`, que sí es determinista. Un test flaky nuevo habría sido especialmente irónico en este change.

### Requisito sin test, resuelto donde se puede romper

*«Timestamps and durations MUST be captured while the search is being served, even when persistence is deferred»* no es comprobable aquí, porque nada difiere todavía la escritura. En vez de dejarlo solo declarado, el aviso se puso **en el XML doc del método**, que es donde lo verá quien algún día mueva la llamada a trabajo de fondo: diferir la escritura dentro del método es correcto, diferir la llamada desplaza todas las marcas de tiempo, y más cuanto más cargado esté el sistema.

**Resultado tras cerrar los huecos: 48 tests, 0 fallos.**

---

## 9. Riesgos vivos tras la verificación

| Riesgo | Estado |
|---|---|
| C15 no invoca el servicio y el change queda inerte **sin síntoma** | Vivo. Mitigado solo por escrito: proposal + ficha de C15 |
| Los ~42 fallos de integración siguen sin ejecutarse en las ramas de trabajo | Vivo. Documentado, sin arreglar; requiere change propio |
| La regla C1 (identificador desconocido ⇒ nulo) se implementa mal al conectar la venta | Vivo. Especificada, no implementada, no probada |
| Bloqueo de la migración única sobre C07, C08, C19, C27 y C29 | Vivo mientras el change no se archive |

---

## Veredicto

**Apto.** 43 tests nuevos en verde, migración revisada línea a línea y verificada contra el catálogo real, arnés probado contra sí mismo, y `openspec validate --all --strict` en `0 failed`. Los 52 fallos preexistentes quedan medidos, diagnosticados por familias y registrados en los dos sitios donde alguien los buscará; ninguno pertenece a este change y ninguno se ha tocado.
