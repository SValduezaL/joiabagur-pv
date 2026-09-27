# QA — C40_FIX `c40-fix-all-shops-scope-unreachable`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados y su evidencia.
> **Fecha:** exploración y artefactos el **2026-09-26**, implementación el mismo día · **Rama:** `c40-fix-all-shops-scope-unreachable` · **Artefactos de partida:** `501c97c` (`proposal`, HU, ticket enriquecido y `epicas.md`), publicado en `origin` · **Implementación commiteada después** en `4b1d056`, que es el árbol que verifica el §11.
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la [HU](../../../../Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md).
> **Alcance:** **38/38 tareas**. La 10.2 —comprobación manual en el entorno— la ejecutó el desarrollador el 2026-09-26 sobre el entorno local; evidencia en el §6, **con una salvedad que se declara y no se disimula**.
> **Este change NO mueve el contrato:** `ai-service/openapi.json` sin diff y `ai-service/` sin tocar (§5).
> **Este change NO crea migraciones:** ninguna entidad, columna ni índice cambia (§5).
> **Este change SÍ llamó a un proveedor real**, una vez, en la verificación en vivo del §4: una consulta libre de ámbito global contra `jbg-ai` con `STUB_MODE=false`. Del orden de una milésima de dólar.
> **Lo que esta pasada encontró:** **tres defectos del método de medición, míos, los tres corregidos en el acto** (§8.1, §8.2, §8.3), **una segunda vía —no documentada— a la trampa del «`dotnet test` sale 0 sin ejecutar nada»** (§8.2), y una **medición que endurece lo que `CLAUDE.md` documenta** sobre la inestabilidad de `InventoryIntegrationTests` (§1.2).
>
> **▸ Los §1 a §10 son la autodeclaración del implementador. El [§11](#11-verificación-independiente--2026-09-26) es una verificación independiente posterior, que refutó cinco de sus afirmaciones y encontró un defecto de producción.** Las correcciones dentro de los §1 a §10 van marcadas en línea con su fecha, sin borrar lo que decían.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| .NET | SDK 10 · Windows 11 · Git Bash y PowerShell |
| Solución | `backend/src/JoiabagurPV.sln` — **no la raíz del repo**, ver §8.2 |
| PostgreSQL de integración | Testcontainers, el `ApiWebApplicationFactory` del repositorio |
| PostgreSQL de la verificación en vivo | `jpv-pv-postgres`, puerto **5433**, base `joiabagur_pv` sembrada: **11 tiendas activas**, 3 operarios, 1 administrador |
| API en la verificación en vivo | `dotnet run --launch-profile http` en `localhost:5056`, con **los tres interruptores activos** por variable de entorno |
| `jbg-ai` en la suite | **Nunca**: ni el frontend ni los tests .NET de este change lo alcanzan |
| `jbg-ai` en la verificación en vivo | Contenedor `jpv-pv-jbg-ai`, **`STUB_MODE=false`** y las tres claves de proveedor presentes — comprobado con `printenv`, no supuesto |
| Frontend | `vitest` sobre el árbol de la rama · verificación manual en `localhost:3000` |
| `ai-service` (pytest) | **No ejecutado**: el diff no toca `ai-service/` (§5). La suite de Python no puede haber cambiado |
| Contrato | `openapi.json` **no regenerado**; sin diff comprobado con `git status` |
| Migraciones | **Ninguna**: el diff no toca `JoiabagurPV.Infrastructure/Migrations/` |

---

## 1. Suites automáticas

**La línea base se midió antes de tocar una línea de código de aplicación**, sobre `501c97c`, y guardando los **nombres** de los fallos y no sólo los recuentos. Esa distinción no es ceremonia: el §1.2 documenta una medición en la que dos pasadas del **mismo binario** difieren en siete nombres.

| Ejecución | Resultado |
|---|---|
| **Línea base frontend** (`npm run test`, árbol limpio de código) | **113 en rojo · 721 en verde · 834 tests · 14 de 57 ficheros** · 253 s |
| **Línea base backend** (`dotnet test JoiabagurPV.sln`) | **45 con error · 1.284 superados · 1.329 tests** · 28 m 4 s |
| `assisted.test.tsx` **al empezar** | **verde entero**, 0 de 57 en rojo — la señal más limpia posible para el área propia |
| Clases .NET del área propia **al empezar** | **0 fallos** — ninguna de `AssistedSearch*`, `AiSearch*`, `FreeQuery*` ni `Availability*` en los 45 nombres |
| `dotnet build JoiabagurPV.sln` tras los grupos 2 y 3 | **Compilación correcta · 0 errores** |
| Clases afectadas, filtradas (`~AssistedSearchServiceTests`, `~AiSearchControllerTests`, `~FreeQuery`) | **122 / 0** en 2 m 4 s, con los 10 nuevos dentro |
| `assisted.test.tsx` tras los cambios de producción, **antes** de escribir tests nuevos | **80 / 80** junto a `assisted-search-result-row.test.tsx` — cero regresiones de producción |
| `assisted.test.tsx` **al cierre** | **71 / 71**, con los 14 nuevos |
| **Cierre frontend** (suite completa) | **114 en rojo · 734 en verde · 848 tests · 15 de 57 ficheros** |
| **Cierre backend** (suite completa) | **52 con error · 1.287 superados · 1.339 tests** · 28 m 19 s |
| `tsc --noEmit` filtrado a los ficheros propios | **sin errores**, en cada paso del frontend |
| `openspec validate c40-fix-all-shops-scope-unreachable --strict` | `Change '…' is valid` |
| `openspec validate --all --strict` | **63 passed · 0 failed**, al escribir las deltas y al cerrar |

### 1.1. La comparación por nombres del frontend: un solo nombre, y es el documentado

| Entra en rojo al cierre | Sale del rojo al cierre |
|---|---|
| `admin/__tests__/family-review.test.tsx :: family review screen should create a family with its members from the review screen` | — (ninguno) |

Ese nombre es **literalmente** el que `CLAUDE.md` registra como el que refutó la afirmación de que aquí el conjunto de fallos es estable entre corridas: *«failed at baseline and passed at close with nothing touching it or its production code»*. No se dio por bueno citando el documento. Dos comprobaciones:

1. **Ejecutado su fichero solo: `22 / 22` en verde.** Dependiente del orden, como está documentado.
2. **Cero dependencias de importación** entre `family-review` —test y producción— y cualquiera de los cinco ficheros de frontend tocados. `grep` de `ai-search`, `assisted`, `search-route-toggle` y `ai-availability` sobre los dos ficheros: sin resultados. No existe camino causal.

**El área propia queda verde**: `assisted.test.tsx` no aparece en los 114 nombres. Estaba verde al empezar y está verde al cerrar, con 14 tests más dentro.

### 1.2. La comparación del backend, y la medición que endurece lo que `CLAUDE.md` dice

**Once nombres difieren: nueve entran y dos salen.** El salto de recuento —45 → 52— es **mayor que el ±1 que documenta `CLAUDE.md`**, así que no se aceptó por analogía.

| Entran en rojo al cierre | Salen del rojo al cierre |
|---|---|
| `InventoryIntegrationTests.Adjustment_ResultingInNegativeStock_ShouldBeRejected` | `InventoryIntegrationTests.MovementHistory_WithPagination_ShouldReturnPagedResults` |
| `InventoryIntegrationTests.AssignProduct_WithNonExistentPOS_ShouldReturnNotFound` | `InventoryIntegrationTests.SaleMovement_ResultingInNegativeStock_ShouldBeRejected` |
| `InventoryIntegrationTests.AssignProduct_WithValidProduct_ShouldSucceed` | |
| `InventoryIntegrationTests.CreateSaleMovement_WithInsufficientStock_ShouldRollback` | |
| `InventoryIntegrationTests.EndToEnd_AssignAdjustView_Workflow` | |
| `InventoryIntegrationTests.ExcelImport_NegativeQuantityExceedingStock_ShouldReturnErrorAndLeaveStockUnchanged` | |
| `InventoryIntegrationTests.Operator_AccessCentralizedInventory_ShouldBeForbidden` | |
| `InventoryIntegrationTests.ProductSearch_AsOperator_ShouldOnlyFindAssignedProducts` | |
| `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct` | |

**Diez de los once están en `InventoryIntegrationTests`**, la primera de las tres clases que `CLAUDE.md` nombra como inestables. El undécimo está en `ProductsControllerTests`, que ya traía **cinco** fallos en la línea base.

Tres evidencias, en orden creciente de fuerza:

**a) No existe camino causal.** `grep` recursivo de los seis símbolos que el change modifica —`AiScopeSwitchExtensions`, `AiSearchAvailabilityResponse`, `IAssistedSearchService`, `AssistedSearchService`, `FreeQuerySearchService`, `AiSearchController`— sobre todos los ficheros de `Application`, `API` e `Infrastructure` cuyo nombre contiene `Inventor` o `Product`: **cero referencias** en los seis casos.

**b) Dos de los once ya están registrados como intermitentes en el QA de C34.** `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct` tiene su propio apartado allí —*«es intermitente — hallazgo, no registrado antes»*— y `InventoryIntegrationTests.MovementHistory_WithPagination_ShouldReturnPagedResults` figura en su tabla de rotación. Los otros nueve son nombres nuevos **en las mismas dos clases**.

**c) La medición que lo cierra: dos pasadas aisladas del mismo binario dan conjuntos distintos.**

| Pasada | Comando | Resultado |
|---|---|---|
| Aislada nº 1 | `--filter "FullyQualifiedName~InventoryIntegrationTests"` | **9 con error de 34** · 2 m 0 s |
| Aislada nº 2 | idéntico, más **`--no-build`** | **9 con error de 34** · 1 m 57 s |

Mismo recuento, y **siete de los nueve nombres difieren** entre las dos. Sólo dos son estables. Y los **tres** que en la pasada nº 1 «seguían rojos en aislamiento» —`AssignProduct_WithNonExistentPOS_ShouldReturnNotFound`, `Operator_AccessCentralizedInventory_ShouldBeForbidden` y `ProductSearch_AsOperator_ShouldOnlyFindAssignedProducts`, los dos últimos de autorización de operario, que eran los que más inquietaban— **pasaron en la pasada nº 2**.

Además, la clase falla **4** dentro de la corrida completa y **9** corriendo sola: el mismo binario da respuestas distintas según el contexto, en las dos direcciones.

**Conclusión:** `InventoryIntegrationTests` no es «a veces inestable» — es **no determinista de una pasada a la siguiente sobre el mismo binario**. `CLAUDE.md` lo describe para el conjunto de clases rotatorias; esta pasada lo mide **dentro de una sola clase y sin recompilar**, que es una afirmación más fuerte y merece quedar escrita.

### 1.3. Desglose de los nuevos, y la aritmética cierra

| Fichero | Declaraciones | Casos ejecutados | Tipo |
|---|---:|---:|---|
| `AssistedSearchServiceTests` | 5 | **8** | unitario; una es `[Theory]` de 4 casos |
| `AiSearchControllerTests` | 2 | **2** | integración con Testcontainers |
| `assisted.test.tsx` | 14 | **14** | página, con `vi.mock` de los servicios |
| | **21** | **24** | |

Backend: 1.329 → 1.339 = **+10** ✓ (8 + 2). Frontend: 834 → 848 = **+14** ✓.

### 1.4. Los tests nuevos no pasan en vacío

Contra el código anterior **los 14 de página fallarían todos** en `findByRole('option', { name: 'Todas las tiendas' })`, porque la opción no existía: no hay forma de que pasen sin el cambio. De los .NET, `GetAvailability_WithoutPointOfSale_IgnoresThePerShopAllowlist` asserta **las dos direcciones** —el ámbito global apagado y la tienda de la lista encendida, con la misma configuración—, así que discrimina en vez de confirmar un interruptor que casualmente está a false.

> **Refutado por medición en la verificación independiente del 2026-09-26 (§11.4).** Revertido el frontend de producción a `501c97c` y ejecutado el fichero, **fallan 12 de los 14, no los 14**: pasan `should not offer the every-shop scope when the caller is an operator` y `should select a concrete shop on load rather than the every-shop scope`, porque los dos asertan **ausencias** que el código anterior también satisfacía. Siguen valiendo como guardas de regresión hacia adelante; lo que no hacen es demostrar este change. Y el primero de los dos es justamente el escenario que el `design.md` lista en D6 como *«el operario no lo tiene → falla si se enseña por error»*, así que ahí la afirmación de fallabilidad también se pasa de fuerte. Aritmética de la pasada: 71 = 59 verdes (57 antiguos + los 2 vacíos) + 12 rojos.

---

## 2. La puerta de entrada (grupo 1)

- **1.1** Línea base de las dos suites medida antes de tocar código de aplicación, **con nombres**. Tres tropiezos de método por el camino, todos míos: §8.1, §8.2 y §8.3.
- **1.2** Las **cuatro afirmaciones que dimensionan el change**, reconfirmadas contra el árbol antes de escribir nada:

| Afirmación | Comprobación | Resultado |
|---|---|---|
| `AssistedSearchRequestValidator` lleva `.NotEmpty()` en `PointOfSaleId` | `grep -A2` | ✅ presente, con su mensaje |
| `GetAvailability` vive en `AssistedSearchService` y consulta **tres** clases de opciones | `grep` en `Services/*.cs` + recuento de `IsEnabledFor` | ✅ un solo sitio, **3** llamadas |
| `compose.demo.yaml` **no** declara `AiFreeQuerySearch__EnabledByDefault` | `grep -c` | ✅ **0 ocurrencias** |
| `SearchLexicalAsync` acepta `Guid?` **sin** agrupar por producto | `grep -c GroupBy` en su cuerpo | ✅ **0** `GroupBy` |

Las cuatro se confirmaron, así que el plan del `design.md` se ejecutó sin desvíos.

---

## 3. Las deltas de spec

| Fichero | Requisitos | Escenarios |
|---|---:|---:|
| `specs/assisted-search-panel/spec.md` | **5** (2 `ADDED` + 3 `MODIFIED`) | **21** |
| `specs/ai-free-query-search/spec.md` | **1** (`MODIFIED`) | **4** |

### 3.1. Cada `## MODIFIED` reproduce el requisito vivo entero

Comprobado con `awk`, extrayendo los `#### Scenario:` de cada requisito en la spec viva y en la delta, y restando conjuntos:

| Requisito modificado | Escenarios vivos | Conservados |
|---|---:|---|
| `The search is scoped to one point of sale, chosen according to role` | 3 | ✅ los 3, **+1 nuevo** |
| `The availability of each AI path is stated before any search is issued` | 3 | ✅ los 3, **+1 nuevo** |
| `The stock label names the shop, and says so plainly when there is no shop to name` | 4 | ✅ 3 literales **+1 renombrado a propósito**, **+1 nuevo** |

**El renombrado es deliberado y es el fondo del asunto.** La spec viva tiene `#### Scenario: Changing shop calls no model`, cuyo primer `THEN` dice *«the stock figures are refreshed»* — y el panel **limpia** los resultados, así que esa cláusula nunca fue verdad y el test de C40 sólo comprobó el segundo `AND`. La delta lo deja como `Changing shop clears rather than refreshes, and calls no model`: mismo `WHEN`, el `THEN` falso sustituido por el verdadero y el `AND` intacto. Renombrarlo es el punto: el nombre viejo describía sólo la mitad que se sostenía.

> **Matizado en la verificación independiente del 2026-09-26 (§11.5).** La comprobación es correcta pero **se hizo sobre la unidad equivocada**: cuenta escenarios, y un `## MODIFIED` reemplaza el requisito **entero**, párrafos de prosa incluidos. Comparados también los párrafos, con los cuatro requisitos modificados, aparece **una pérdida real**: en `ai-free-query-search` el párrafo *«The route exists because availability was previously observable only inside the response of a search that had already been paid for…»* —el motivo por el que la ruta de disponibilidad existe— **no se reproducía en ninguna parte de la delta**, así que el archivado lo habría borrado de la spec viva. Restituido en la delta. Los demás párrafos no reproducidos son, uno a uno, los enunciados que este change corrige a propósito, o superconjuntos suyos.

### 3.2. La regla de la primera línea física, en los 6 requisitos

El validador lee **sólo la primera línea física** de la descripción que sigue a `### Requirement:`. Comprobado con `awk` sobre los seis: **los seis llevan `SHALL` en ella**, y las seis líneas van sin ajustar —entre **228 y 346 caracteres**—, como las archivadas.

### 3.3. Se descartó `RENAMED`, y no por comodidad

El requisito de ámbito conserva su título —*«The search is scoped to one point of sale…»*— aunque ya no lo describa bien. La alternativa era `## RENAMED Requirements`, y se descartó al medir que **no existe un solo precedente en los 71 changes archivados** (`grep -rln "## RENAMED Requirements" openspec/changes/archive/` → vacío). Estrenar una vía del validador en la puerta del proyecto es el riesgo que este repositorio ya ha pagado tres veces. En su lugar: el `MODIFIED` corrige el `SHALL` falso y **el control va como `ADDED` con título propio**, que además es lo que la propia instrucción del artefacto recomienda —*«If adding new concerns without changing existing behavior, use ADDED instead»*—.

### 3.4. El `proposal.md` se puso al día, porque la delta creció

El `proposal.md` enumeraba **dos** requisitos modificados. Al escribir la delta salieron **dos nuevos y tres corregidos**: el control y el estado del toggle son concerns nuevos, y los enunciados falsos son tres —el de ámbito, el de disponibilidad y la cláusula del refresco— y no dos. Se corrigió el `proposal.md` en el mismo acto: **dejar que los artefactos de un change se contradigan entre sí es la misma deriva que este change persigue en las specs vivas.**

---

## 4. La verificación en vivo del backend (tarea 10.2, mitad servidor)

Entorno del §1 levantado, login real (`admin` / token JWT de 436 caracteres), `curl` contra `localhost:5056`.

| Caso | Esperado | Medido |
|---|---|---|
| `GET /api/ai/search/availability` **sin** `pointOfSaleId` | 200 · identificador **nulo** | ✅ `HTTP 200` · `{"pointOfSaleId":null,"semanticSearchAvailable":true,"assistedAnswerAvailable":true,"assistedAnswerUnavailableReason":null}` |
| `GET …?pointOfSaleId=43da2f6a-…` | 200, como antes | ✅ `HTTP 200` · identificador devuelto |
| `GET …?pointOfSaleId=00000000-0000-0000-0000-000000000000` | **400** | ✅ `HTTP 400` · `{"errors":["El punto de venta no es válido. Omítelo para consultar todas las tiendas."]}` |
| `POST /api/ai/search/assisted` **sin** punto de venta | 200, sin cantidades | ✅ `HTTP 200` · grupos con `"quantityAtPointOfSale":null,"hasStock":null` · pieza real del catálogo (`SKU143 Anillo rama`, `Colección Suspiro`) |
| `POST /api/ai/search` **sin** punto de venta | **400** | ✅ `HTTP 400` · `{"errors":["La búsqueda asistida requiere un punto de venta."]}` |

**La primera fila es el cambio: antes de este change era un 400.** Y la última es **el hallazgo que dimensionó el change**, demostrado contra el sistema real: es la razón de que el panel fije la ruta asistida en cuanto se elige el ámbito global. Sin eso, el primer *Buscar* del administrador escribiría ese error justo debajo del control que se lo acaba de ofrecer.

---

## 5. El contrato y el alcance negativo, demostrados

| Afirmación | Comprobación | Resultado |
|---|---|---|
| `ai-service/openapi.json` sin diff | `git diff --stat` y `git status` sobre `ai-service/` | ✅ vacío |
| `ai-service/` sin tocar | `git status --short ai-service/` | ✅ vacío |
| Ninguna migración creada | `git status --short …/Migrations/` | ✅ vacío |
| La fila de resultado sin tocar | `git status` — `assisted-search-result-row.tsx` no aparece | ✅ y sus 23 tests siguen verdes |
| `FreeQuerySearchService` y `AiCallScope` sin cambio funcional | diff leído: en el primero sólo se **retira** el `IsEnabled` privado y se llama al extraído; el segundo no aparece | ✅ |
| La autorización **no** se endurece | los tests `FreeQuery_ForOperatorWithAllPointsOfSale_IsServed` y `FreeQuery_WhenNamingAnUnassignedPointOfSale_IsRefused` siguen en verde en la corrida filtrada de 122 | ✅ |
| Sin TODO/FIXME/HACK/XXX | `grep` sobre los 14 ficheros del diff | ✅ ninguno |

**14 ficheros tocados** (6 backend de producción y test, 5 frontend, `compose.demo.yaml`, `DEFERRED_TASKS.md`, `proposal.md`), más los 3 artefactos nuevos del change y el `qa.md`.

---

## 6. La verificación manual del desarrollador (tarea 10.2, mitad pantalla)

Ejecutada por el desarrollador el **2026-09-26** sobre `localhost:3000`, con la API del §1 y `jbg-ai` con proveedor real.

**Como administrador:**

| Comprobación | Resultado |
|---|---|
| Con una tienda concreta, **las dos** vías de búsqueda siguen habilitadas | ✅ |
| Con «Todas las tiendas»: sale *«Verás piezas de todo el catálogo. Para leer existencias, elige una tienda.»*, se **deshabilita la búsqueda rápida** y la **respuesta asistida sigue habilitada** | ✅ — es el escenario que cierra el change |
| Buscando «un anillo de plata para regalar»: **ni un número** en las filas, sin nombre de tienda, botón de ficha deshabilitado, y **cada producto una sola vez** | ✅ |

**Como operario:** no puede escoger punto de venta.

**Y aquí va la salvedad, que se declara en vez de disimularse.** Ese resultado satisface el requisito —*«no se ofrece al operario ninguna opción para buscar en todas las tiendas»*— pero **lo satisface por la vía de la asignación única**, no por la que el escenario tenía en mente. Comprobado en la base:

```
 admin         | Administrator | 0 tiendas
 op-aeroport   | Operator      | 1 tienda
 op-ciutadella | Operator      | 1 tienda
 op-fornells   | Operator      | 1 tienda
```

Los tres operarios sembrados tienen **exactamente una** tienda, así que el selector **no se renderiza** por la regla previa de C16 —`pointsOfSale.length > 1 || isAdmin`, que este change no toca a propósito—. De modo que la comprobación manual confirma el camino de la asignación única y **no ejercita el del operario con varias tiendas**, que es el que enseña un selector **con** tiendas y **sin** la opción global. Ese camino queda cubierto por el test de página `should not offer the every-shop scope when the caller is an operator`, que simula dos tiendas justamente para que la ausencia de la opción no pueda achacarse a la ausencia del selector.

**No existe en los datos sembrados un operario con varias tiendas**, así que ese camino no es verificable a mano en este entorno sin crear uno. Queda anotado como lo que es: cobertura de test, no de pantalla.

---

## 7. El DoD del ticket, casilla a casilla

| Casilla | Evidencia |
|---|---|
| Código según las capas de `modelo-c4.md` y las convenciones de `project.md` | Domain intacto · Infrastructure intacto · el predicado en `Application/Configuration` · el controlador en `API` |
| Backend: xUnit + Moq + FluentAssertions, nomenclatura `Método_Escenario_ResultadoEsperado` | 10 casos nuevos, los diez con esa forma (§1.3) |
| Frontend: Vitest + RTL, nomenclatura `should … when …`, queries accesibles, cobertura ≥ 70 % | 14 casos nuevos; `getByLabelText`, `findByRole('option')`, `getByRole('button')`. **· La cobertura no se midió aquí y el DoD la pide: medida después en la verificación independiente — 93,7 % / 94,1 % / 83,3 % de línea en los tres componentes, y un hueco real en `ai-search.service.ts` cerrado con un test (§11.8)** |
| Cobertura ≥ 70 % sobre el código nuevo | **No medida con `coverlet`** — se declara en el §9. El código nuevo es un método de extensión ×3, una rama de nulo y seis condicionales de interfaz, y todos tienen test nominal. **· Medida después en la verificación independiente: 100 % de línea en el predicado, en `GetAvailability` y en el DTO; 87,5 % en el controlador. Casilla satisfecha — §11.8** |
| `ai-service`: sin cambios y `openapi.json` sin diff | §5, comprobado |
| Sin migración de EF Core | §5, comprobado |
| Deltas de spec y `openspec validate --all --strict` en `0 failed` | **63 passed · 0 failed** (§1) |
| Las tres specs dejan de afirmar algo falso, **leído y no sólo validado** | §3.1: el `SHALL` de ámbito, la disponibilidad *«for the selected point of sale»* y la cláusula del refresco |
| Suites comparadas por **nombres** contra la línea base del propio commit | §1.1 y §1.2 |
| `dotnet build` y `tsc --noEmit` filtrado en verde | §1 |
| Comprobación manual en el entorno | §4 y §6, con la salvedad del §6 |
| Documentación actualizada | `epicas.md` (EP15 + resumen), `frontend/README.md`, `backend/README.md`, `DEFERRED_TASKS.md` |
| Compatibilidad hacia atrás del contrato REST | `PointOfSaleId` anulable es **adición de tolerancia**: un cliente que leía un valor sigue leyéndolo cuando hay tienda. Único consumidor: el panel |
| Sin TODO/FIXME sin tarea asociada | §5 |
| UI en español y EUR | Las seis cadenas nuevas, en es-ES |

---

## 8. Incidencias de esta pasada

### 8.1. Medí dos veces con `tail` y me quedé sin los nombres — **defecto mío de método; corregido**

Las dos primeras corridas de línea base se pipearon por `tail -40` y `tail -30`, que devuelven los recuentos y **borran la lista de nombres**. Como el juicio de este repositorio se toma por nombres —el §1.2 mide siete nombres distintos entre dos pasadas del mismo binario—, el recuento solo no vale nada. Se repitieron las dos con captura completa: el frontend con `--reporter=json` y un script de extracción, el backend redirigiendo todo a fichero. **Coste: unos 35 minutos de reloj.**

### 8.2. `dotnet test` desde la raíz del repo falla y **sale 0** — **segunda vía a una trampa documentada a medias**

`CLAUDE.md` advierte de que si algo bloquea `bin/Debug` —un `JoiabagurPV.API.exe` vivo— el build falla, **no se ejecuta ni un test y `dotnet test` sale 0**. Hay una segunda vía al mismo desenlace, que no está escrita: **desde la raíz del repositorio no hay solución** —vive en `backend/src/JoiabagurPV.sln`—, así que MSBuild imprime `MSBUILD : error MSB1003: Especifique un archivo de proyecto o de solución` y **también sale 0**.

La lección de `CLAUDE.md` es la correcta y basta —*medir la línea de resumen y no el código de salida*—, pero su ejemplo cubre una sola causa. Se propone añadir la segunda al documento.

Y de paso: **había un `JoiabagurPV.API.exe` vivo (PID 25020) al empezar**, exactamente la primera vía. Se paró para poder medir y se volvió a levantar para el §4.

### 8.3. Dos heredoc de Bash reventaron por longitud — **defecto mío de herramienta; corregido**

Escribir bloques grandes con `cat > fichero <<'EOF'` falló dos veces: una con `ENAMETOOLONG: uv_spawn` y otra con `unexpected EOF while looking for matching`. Para bloques largos, la vía fiable en este entorno es escribir a un fichero con la herramienta de escritura y anexar con `cat >>`. Sin consecuencia sobre el resultado.

### 8.4. `SearchLexicalAsync` tiene un **HTTP 500 dormido** — hallazgo, anotado y **no arreglado a propósito**

`HydrateAsync` acepta `Guid?` **y agrupa** por producto con nulo, con un comentario que explica el peligro. `SearchLexicalAsync` acepta `Guid?` y **no agrupa**: `Carried(null)` suelta el filtro de tienda, así que un producto que tres tiendas llevan vuelve tres veces, y `BuildResultsAsync` hace `rows.ToDictionary(row => row.ProductId)` **incondicionalmente, en las dos ramas** → `ArgumentException` → **500**.

Hoy es código muerto: su único llamante pasa siempre una tienda concreta. Se activaría en cuanto la ruta rápida aceptara la ausencia, y **primero en desarrollo local**, donde `AiSearch__EnabledByDefault` no está declarado en ningún `appsettings` y la ruta degradada es la que corre siempre. **Queda anotado en `DEFERRED_TASKS.md` como una sola tarea con la extensión de la ruta rápida, y con el orden obligatorio: primero la agrupación y su test, después el DTO.**

### 8.5. El interruptor de la consulta libre no estaba en el compose de la demo — hallazgo, **corregido en este change**

`compose.demo.yaml` declaraba `AiSearch__EnabledByDefault` (C17) y `AiSalesAssist__EnabledByDefault` (C34) y **no** `AiFreeQuerySearch__EnabledByDefault` (C40). Con el valor por defecto a `false` y la lista vacía, en la demo `GET availability` respondía `switched_off` para **todas** las tiendas: el panel generativo de C40, apagado en el entorno cuyo único trabajo es enseñarlo. Es el fallo que el comentario situado tres líneas más arriba en ese mismo fichero describe palabra por palabra. Añadido con su comentario de clase.

---

## 9. Lo que esta pasada **no** verifica, dicho aquí

- **Cobertura con `coverlet`.** No se midió. El QA de C34 documenta que `coverlet` **no instrumenta el ensamblado `Application`** en este repositorio, que es donde cae casi todo el código nuevo, así que la cifra habría descrito la herramienta y no el cambio.
- **El operario con varias tiendas, en pantalla.** §6: no existe tal usuario en los datos sembrados. Cubierto por test de página.
- **El callejón sin salida, en pantalla.** El texto *«La búsqueda en todas las tiendas usa la respuesta asistida, y está desactivada»* tiene su test de página y **no se comprobó a ojo**: exigiría reiniciar la API sin `AiFreeQuerySearch__EnabledByDefault`.
- **La ruta rápida con ámbito global.** Fuera de alcance por decisión (§8.4). Lo que sí se verificó es que **responde 400**, que es la premisa de la decisión (§4).
- **`ai-service`.** Ni la suite de Python ni el contrato: el diff no los toca (§5).
- **La demo desplegada.** Este change añade su interruptor al compose, pero **no se desplegó** el entorno de demostración para comprobarlo allí. La verificación del §4 y del §6 es sobre el entorno local.
- **Telemetría del ámbito global.** Sigue siendo tarea diferida de C40: una búsqueda global **no se registra**, así que su uso no es medible. El recorte al administrador la vuelve marginal, y eso refuerza el motivo para diferirla en vez de erosionarlo.
- **La suite del frontend no se ejecutó con `npm run build`** al cierre; sí `tsc --noEmit` filtrado, que es la puerta que este repositorio documenta como la única que ve un error de tipos.

---

## 10. Estado final

| | |
|---|---|
| Tareas | **38 / 38** |
| `openspec validate --all --strict` | **63 passed · 0 failed** |
| Frontend | 113 → **114** en rojo · **1** nombre nuevo, el documentado como rotatorio · área propia **verde** |
| Backend | 45 → **52** con error · **11** nombres difieren, 10 en la clase no determinista · área propia **verde** |
| Tests nuevos | **24 casos** de 21 declaraciones · la aritmética de las dos suites cierra |
| Contrato · migraciones | sin diff · ninguna |
| Commit | **ninguno**, a petición del desarrollador |

---

## 11. Verificación independiente — 2026-09-26

> Segunda pasada, **con la intención de refutar** lo escrito arriba y no de confirmarlo. Sobre `4b1d056`, el commit de implementación. Todo lo que aquí se afirma se volvió a medir; donde no se pudo medir, se dice.
> **Resultado en una línea:** el change hace lo que dice **y** dos de sus afirmaciones no se sostienen —el test que guarda su invariante central es tautológico, y la sonda de disponibilidad sigue divergiendo de la ruta en una dirección— más **un defecto de producción nuevo, introducido por este change y corregido aquí**: la ruta de disponibilidad servía como «todas las tiendas» cualquier identificador ilegible de la *query string*.
> **Entregado por esta pasada:** 1 fix de producción con 4 casos de test, 1 clase de test nueva que sí demuestra el invariante, 3 mutaciones de control compiladas y ejecutadas, las 5 casillas del §9 medidas (4 cerradas, 1 pendiente), y 6 correcciones en los artefactos.

### 11.1. Lo que se refutó

| Afirmación | Dónde | Veredicto |
|---|---|---|
| El test `…MatchesTheRoutePredicate` demuestra que sonda y ruta calculan el mismo predicado | `tasks.md` 2.3, `design.md` D4/R4, `qa.md` §1.4, mensaje de `4b1d056` | **Refutada.** Es tautológico: calcula lo esperado con los mismos métodos de extensión que la sonda y **nunca invoca `FreeQuerySearchService`**. Sobrevive a dos mutaciones (§11.2) |
| «el predicado extraído … de modo que no puedan divergir» | `design.md` D4 | **Refutada en parte.** Comparte la regla del nulo; el veredicto sigue divergiendo (§11.3). Corregido en `design.md` |
| «los 14 de página fallarían todos» contra el código anterior | `qa.md` §1.4 | **Refutada por medición: fallan 12** (§11.4). Corregido en `qa.md` |
| «Cada `## MODIFIED` reproduce el requisito vivo entero» | `qa.md` §3.1 | **Matizada:** comprobado sobre escenarios, no sobre prosa; **un párrafo se perdía** (§11.5). Restituido en la delta |
| `Guid.Empty` no viaja nunca y las dos rutas y la sonda lo rechazan | `design.md`, delta `ai-free-query-search` | **Refutada para la sonda:** `?pointOfSaleId=`, `=%20`, `=notaguid` y un GUID truncado devolvían **200** con el ámbito global (§11.6). Corregido en el controlador, con test |
| «Implementación sin commitear» | cabecera del `qa.md` | Obsoleta: está en `4b1d056`. Corregida |
| La casilla de cobertura del DoD es sólo la del backend | `qa.md` §7 y §9 | **Incompleta:** el DoD pide `≥70 %` en **las dos** capas. Medidas las dos (§11.8), y al medir la del frontend apareció **un hueco en la rama que este change introduce** en `ai-search.service.ts`: cerrado con un test |
| Los nombres de test que `tasks.md` promete | `tasks.md` 2.3 y 3.4 | **Cuatro no existen con ese nombre**, y uno no existe en esa capa (§11.12) |

### 11.2. El test de la guarda no guarda nada: tres mutaciones, compiladas y ejecutadas

`GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate` afirma

```csharp
probe.AssistedAnswerAvailable.Should().Be(_freeQueryOptions.IsEnabledForScope(null) && _assistOptions.IsEnabledForScope(null))
```

que es **la misma expresión que `GetAvailability` evalúa**, línea por línea. No hay nada de la ruta en el test.

| Mutación | Qué inyecta | `…MatchesTheRoutePredicate` | La suite del área | `AiScopePredicateAgreementTests` (nuevo) |
|---|---|---|---|---|
| **M1** | `IsEnabledForScope(null)` devuelve `!EnabledByDefault`, en las tres clases | **4/4 VERDE** | 3 rojos de 122 | **3 rojos de 4** |
| **M2** | la ruta resuelve la ausencia con `EnabledPointOfSaleIds.Count > 0` en vez del predicado compartido | **4/4 VERDE** | **1 rojo** de 122 | **3 rojos de 4** |
| **M3** | la **sonda** resuelve la ausencia con una regla propia | 1 rojo de 4 | — | 1 rojo de 4 |

**Lectura exacta, que es más interesante que «está mal».** El test sí ata la sonda a `AiScopeSwitchExtensions` (M3 lo caza). Lo que no hace es atar **la ruta** a nada, que es la mitad que el nombre promete y la mitad donde vive la avería de C40. Y M1 no la caza **ninguna** comparación sonda-contra-ruta, porque mueve la regla compartida a los dos lados a la vez: el valor de la regla necesita aserción propia en cada lado, y la divergencia necesita ejecutar las dos piezas. Son dos tests, no uno.

### 11.3. El test que sí lo demuestra, y lo que encuentra al primer intento

`backend/src/JoiabagurPV.Tests/UnitTests/Application/AiScopePredicateAgreementTests.cs` (4 casos, verdes sobre `4b1d056`): construye `AssistedSearchService` y `FreeQuerySearchService` sobre **los mismos objetos de opciones**, pregunta a una y **ejecuta la otra**, y compara veredictos.

- `ProbeAndRoute_AgreeOnTheWiderScope_WhateverTheFreeQuerySwitchSays` — caza M2 y M3.
- `Route_ReadsTheAbsenceAsTheDeploymentDefault_AndIgnoresTheAllowlist` — el valor de la regla **por la ruta**, no por el método de extensión. Caza M1.
- `Probe_AlsoReportsTheSaleCardSwitch_WhichTheRouteNeverApplies` — fija el desacuerdo que sigue vivo.

**Y ese desacuerdo es el hallazgo de fondo.** La sonda devuelve `freeQuery && salesAssist`; `FreeQuerySearchService` **no lee `AiSalesAssistOptions` en ningún punto**. Con el primero encendido y el segundo apagado, contra la API real:

| Llamada | Respuesta medida |
|---|---|
| `GET /api/ai/search/availability` sin tienda | `{"assistedAnswerAvailable":false,"assistedAnswerUnavailableReason":"switched_off"}` |
| `POST /api/ai/search/assisted` sin tienda | `200` · `aiAvailable:true` · `degradedReason:null` · `pitchStatus:"generated"` · prosa real |

En pantalla, con «Todas las tiendas» esa combinación deshabilita **las dos** vías y escribe *«La búsqueda en todas las tiendas usa la respuesta asistida, y está desactivada»* de un ámbito que el backend sirve: **el defecto que este change vino a cerrar, alcanzable por interruptores en vez de por una opción que falta.** Es herencia de C40, no de C40_FIX — pero el requisito que C40_FIX escribe lo prohíbe, y el comentario que justificaba la conjunción (*«whether the AI service will write prose for this shop»*) **es falso**: nada del camino de la consulta libre lee ese interruptor. Comentario corregido, decisión anotada en `DEFERRED_TASKS.md`, respuesta de hoy fijada en test. **No se cambió el comportamiento**: qué lado está mal es decisión de producto y las dos salidas tienen coste.

### 11.4. Los 14 tests de página contra el código anterior: **12, no 14**

Revertidos a `501c97c` los cinco ficheros de producción del frontend —`assisted.tsx`, `ai-availability-badge.tsx`, `search-route-toggle.tsx`, `ai-search.service.ts`, `ai-search.types.ts`—, ejecutado `assisted.test.tsx`, y restaurado el árbol (`git status` limpio después).

**71 tests · 59 verdes · 12 rojos.** Los dos nuevos que pasan sin el cambio:

| Test nuevo verde contra el código anterior | Por qué |
|---|---|
| `should not offer the every-shop scope when the caller is an operator` | Asserta una **ausencia**. Antes del change la opción no existía para nadie, así que pasa vacío |
| `should select a concrete shop on load rather than the every-shop scope` | El efecto de carga ya fijaba la primera tienda activa antes del change |

Siguen siendo guardas de regresión válidas —fallarían si mañana la opción se enseñara a un operario, que es justo lo que `design.md` D6 quiere proteger—, pero **no demuestran este change**, y el primero es precisamente el escenario que D6 presenta como fallable. La aritmética cierra: 59 = 57 antiguos + 2 vacíos.

### 11.5. Las deltas, comparadas párrafo a párrafo y no sólo escenario a escenario

Comparación mecánica de los 4 `## MODIFIED` contra `openspec/specs/`, sobre **escenarios y prosa**:

| Requisito | Escenarios vivos | Literales | Cambiados a propósito | Nuevos | Prosa viva no reproducida |
|---|---:|---:|---:|---:|---|
| `The search is scoped to one point of sale…` | 3 | 3 | 0 | 1 | 1 — el `SHALL` falso, retirado a propósito |
| `The availability of each AI path…` | 3 | 2 | 1 (`for the scope currently selected`) | 1 | 1 — el `SHALL` falso, retirado a propósito |
| `The stock label names the shop…` | 4 | 3 | 1 (renombrado) | 1 | 2 — una es la cláusula falsa del refresco; la otra se reproduce **ampliada** |
| `Availability of both AI paths…` (free query) | 2 | 2 | 0 | 2 | 2 — una es el «for one point of sale»; **la otra se perdía** |

**El renombrado es correcto.** Mismo `WHEN`, el `THEN` falso sustituido por el verdadero, el `AND` intacto, y el nombre nuevo describe las dos cláusulas en vez de la mitad que se sostenía. Sobrevive al archivado sin pérdida: el `MODIFIED` reemplaza el requisito entero, así que el escenario viejo desaparece con su cláusula falsa, que es el propósito.

**La pérdida que sí había.** El párrafo *«The route exists because availability was previously observable only inside the response of a search that had already been paid for…»* no aparecía en ninguna parte de la delta (`grep` sobre el change: 0 ocurrencias; sólo vive en `openspec/specs/ai-free-query-search/spec.md:72`). Un `MODIFIED` reemplaza el bloque completo, así que el archivado habría borrado de la spec viva **el motivo por el que la ruta de disponibilidad existe**. Restituido en la delta, y la regla de la primera línea física comprobada de nuevo después de restituirlo.

**La regla de la primera línea física, en los 6 requisitos:** los seis llevan `SHALL` en la primera línea física de su descripción, con longitudes de **228 a 346** caracteres, sin ajustar. Vuelto a comprobar tras editar la delta. `openspec validate --all --strict` → **63 passed · 0 failed**.

### 11.6. **Defecto nuevo, introducido por este change** — un identificador ilegible se leía como «todas las tiendas»

`Availability` pasó de `[FromQuery] Guid` a `[FromQuery] Guid?`. Con el tipo no anulable, un valor que no parsea dejaba `Guid.Empty` y caía en la guarda `== Guid.Empty` → 400. Con `Guid?`, **el binder devuelve `null`** — y `null` es ahora el ámbito global. `SuppressModelStateInvalidFilter` está activado globalmente (`ServiceCollectionExtensions.cs:69`), así que nada más lo rechaza.

Medido contra `localhost:5056`, autenticado como administrador, **antes del fix**:

| Petición | Antes de C40_FIX | Con C40_FIX (medido) | La delta exige |
|---|---|---|---|
| `?pointOfSaleId=00000000-…-0000` | 400 | 400 ✅ | refusal |
| `?pointOfSaleId=` | 400 | **200 · `pointOfSaleId:null`** ❌ | refusal |
| `?pointOfSaleId=%20` | 400 | **200 · `pointOfSaleId:null`** ❌ | refusal |
| `?pointOfSaleId=notaguid` | 400 | **200 · `pointOfSaleId:null`** ❌ | refusal |
| `?pointOfSaleId=22222222-2222-2222-2222` | 400 | **200 · `pointOfSaleId:null`** ❌ | refusal |

La delta lo dice sin margen: *«absence is the field not being there and anything else is a value that has to be usable»*, con su escenario `A blank point of sale is refused rather than read as an absence`. El test del change cubría **sólo** la forma `Guid.Empty`.

**Impacto real, dicho sin inflarlo:** es la sonda, que no llama al modelo ni gasta cuota, así que no hay búsqueda más ancha ni fuga de datos. Lo que produce es una **afirmación falsa en pantalla** —la disponibilidad del ámbito global presentada como la de la tienda que el cliente creía estar preguntando— que es la clase de fallo de esta capacidad. Y el panel no puede provocarlo: `aiSearchService.getAvailability` omite el parámetro cuando no hay tienda, comprobado en el tráfico real.

**Corregido** en `AiSearchController.Availability`: la clave presente con un valor que no parsea se rechaza con el mismo texto. **Test añadido**: `Availability_WithAnUnusablePointOfSale_Returns400`, `[Theory]` de 4 casos. Rojo 4/4 antes del fix, verde después; las 40 pruebas de `~Availability` en verde.

### 11.7. Las cinco casillas del §9, medidas

| Casilla del §9 | Estado |
|---|---|
| **Cobertura con `coverlet`** | **Medida.** La afirmación del QA de C34 —`coverlet` no instrumenta `Application`— **confirmada al reproducirla**: el informe por defecto sólo trae `API`, `Domain` e `Infrastructure`. Aplicado su apaño (copiar al `bin` los 47 `Microsoft.Extensions.*.dll` del framework compartido, correr con `--no-build`, borrarlos — 0 restantes, comprobado) y medida la cifra que el DoD pide (§11.8) |
| **El operario con varias tiendas, en pantalla** | **Cerrada.** Creado `op_verif_2t` con dos tiendas y conducido el navegador: selector visible con **exactamente sus dos tiendas** y **sin** «Todas las tiendas». El recorte no es un artefacto de la asignación única |
| **El callejón sin salida, en pantalla** | **Cerrada.** API reiniciada **sin** `AiFreeQuerySearch__EnabledByDefault`. Leído: *«La búsqueda en todas las tiendas usa la respuesta asistida, y está desactivada»*, las dos vías deshabilitadas, y la insignia dice *«La respuesta asistida está desactivada»* **sin** «en esta tienda» |
| **`npm run build`** | **Cerrada.** Verde en 27,7 s. `tsc --noEmit` filtrado: **0 errores** en los ficheros del change (176 preexistentes en la plantilla Metronic) |
| **La demo desplegada** | **Sigue sin verificar.** No se desplegó el entorno de demostración. Lo comprobado es que la línea existe en `compose.demo.yaml` con su comentario, y que la variable hace lo que dice en local: reiniciando la API sin ella el panel entra en el callejón sin salida, y con ella no |

### 11.8. La cobertura que el DoD pedía, medida

Con el apaño del §11.7 aplicado, 105 tests del área (`AssistedSearchServiceTests`, `AiScopePredicateAgreementTests`, `FreeQuerySearchServiceTests`, `~Availability`), `coverlet.collector` 6.0.4, informe Cobertura:

| Código nuevo o cambiado por el change | Líneas | Cobertura de línea | De rama |
|---|---:|---:|---:|
| `AiScopeSwitchExtensions` (los 3 métodos de extensión) | 3/3 | **100 %** | 100 % |
| `AssistedSearchService.GetAvailability` | 21/21 | **100 %** | 100 % |
| `AiSearchAvailabilityResponse` | 4/4 | **100 %** | 100 % |
| `FreeQuerySearchService` (clase entera) | — | **100 %** | 76,9 % |
| `AiSearchController.Availability` | 14/16 | **87,5 %** | 90 % |

Las dos líneas sin cubrir de `Availability` son la guarda `Unauthorized`, inalcanzable por detrás de `[Authorize]`.

**Y el DoD pide la cifra del frontend también**, que ni el §7 ni el §9 mencionan. Medida con `@vitest/coverage-v8`:

| Fichero del frontend | Líneas | Rama |
|---|---:|---:|
| `pages/sales/assisted.tsx` | **93,7 %** | 83,0 % |
| `components/sales/ai-availability-badge.tsx` | **94,1 %** | 91,7 % |
| `components/sales/search-route-toggle.tsx` | **83,3 %** | 100 % |
| `services/ai-search.service.ts` | **100 %** | 100 % **tras añadir un test** (abajo) |

**Y aquí salió un hueco real.** Con sus tests tal como los dejó el change, `ai-search.service.ts` quedaba en **93,75 % de rama con la línea 130 sin cubrir** — que es **precisamente la rama que este change introduce**: `params: pointOfSaleId ? { pointOfSaleId } : undefined`. Los tres tests de `getAvailability` pasan siempre un identificador, y el test de página sólo ve que la función se llamó con `undefined`, no lo que la función hace entonces. O sea: la pieza que garantiza que el ámbito global viaja **como ausencia y no como cadena vacía** —la propiedad de la que cuelga la seguridad del ámbito— no tenía aserción propia en su capa. Añadido `should omit the query parameter entirely when no point of sale is given`: el fichero pasa a **100 / 100**.

**Casilla del DoD satisfecha en las dos capas: todo por encima del 70 %.**

### 11.9. Las dos suites, medidas otra vez y comparadas por **nombres**

**Backend.** Línea base propia sobre `4b1d056` en un `git worktree` aparte, y la pasada del árbol verificado a continuación, en el mismo binario de solución:

| Pasada | Resultado |
|---|---|
| Línea base propia, `4b1d056` limpio (worktree) | **51 con error · 1.288 superados · 1.339 tests** · 10 m 57 s |
| Árbol verificado (`4b1d056` + el fix del §11.6 + 8 tests nuevos) | **53 con error · 1.294 superados · 1.347 tests** · 9 m 18 s |
| El §1 del implementador, sobre el mismo `4b1d056` | 52 con error · 1.339 tests |

Aritmética: **1.339 + 8 = 1.347** ✓ — los 4 casos de `Availability_WithAnUnusablePointOfSale_Returns400` y los 4 de `AiScopePredicateAgreementTests`, los ocho verdes.

**Doce nombres difieren entre mi línea base y mi cierre —siete entran, cinco salen— y los doce están en `InventoryIntegrationTests`.** Cero nombres distintos fuera de esa clase. Es la primera de las tres que `CLAUDE.md` nombra como no deterministas de una pasada a la siguiente sobre el mismo binario, y esta pasada la mide **más inestable todavía** que las anteriores: el QA del implementador contó siete nombres rotando en dos corridas aisladas de esa clase, y aquí rotan doce entre dos corridas completas. El fix del §11.6 no tiene camino causal hacia ella —toca una guarda de `[FromQuery]` en `AiSearchController.Availability`— y el `+2` neto es exactamente el saldo de esa rotación (7 − 5), no de los tests nuevos.

**Frontend.** El change no toca el frontend en esta pasada, así que el árbol verificado **es** el frontend de `4b1d056` y una corrida sirve de las dos:

| Pasada | Resultado |
|---|---|
| Esta verificación, sobre `4b1d056` | **113 en rojo · 735 en verde · 848 tests · 14 ficheros** |
| El §1 del implementador, sobre el mismo commit | **114 en rojo · 15 ficheros** |

**El nombre que sobra en su pasada y falta en la mía es `admin/__tests__/family-review.test.tsx :: family review screen should create a family with its members from the review screen`** — el mismo que `CLAUDE.md` registra como el que refutó la idea de que aquí el conjunto es estable, y el mismo al que el §1.1 atribuye su +1. **Tercera observación independiente del mismo nombre rotando**, ahora en la dirección contraria. De paso se confirma el otro par que `CLAUDE.md` describe: en `scan.test.tsx`, `should render loading state initially` sale rojo y `should show manual SKU input fallback after initialization` verde.

**El área propia, verde en las dos suites:** `assisted.test.tsx` no aparece entre los 113 nombres, y ninguna clase `AssistedSearch*`, `AiSearch*`, `FreeQuery*`, `AiScope*` ni `Availability*` aparece entre los rojos del backend, ni en la línea base ni al cierre.

### 11.10. Lo verificado en vivo por esta pasada, con las respuestas medidas

Navegador conducido con Playwright contra `localhost:3000` y la API en `localhost:5056`, con `jpv-pv-jbg-ai` y proveedor real.

**Administrador, tres interruptores encendidos:**

| Comprobación | Medido |
|---|---|
| «Todas las tiendas» **la primera** de la lista, y sólo 11 tiendas activas de las 12 | ✅ 12 opciones: la global + 11 |
| Consecuencia antes de buscar | ✅ *«Verás piezas de todo el catálogo. Para leer existencias, elige una tienda.»* |
| Vía rápida deshabilitada **con motivo de ámbito**, no de interruptor | ✅ *«La búsqueda rápida trabaja sobre una tienda concreta»*; la insignia sigue diciendo *«Búsqueda inteligente disponible»* |
| Vía asistida habilitada y seleccionada | ✅ `aria-checked=true`, no deshabilitada |
| Cambiar de ámbito **no emite búsqueda** | ✅ cero `POST`; sólo la relectura de la sonda |
| La sonda se relee **omitiendo el parámetro** | ✅ `GET /api/ai/search/availability` sin *query string* |
| El campo y el botón siguen usables | ✅ `Buscar` deshabilitado en vacío, habilitado al escribir |
| El `POST` **no lleva el campo** | ✅ `{"query":…,"pageSize":10,"searchSessionId":…,"materials":[]}` — la clave no está |
| Resultados: sin cifras, sin tienda, ficha deshabilitada, cada producto una vez | ✅ *«Selecciona una tienda para ver existencias»* en las 10 filas, **0 SKU duplicados**, **10/10** botones de ficha deshabilitados |

**Operario con dos tiendas (`op_verif_2t`, creado para esto):** selector visible con `["Aeroport de Menorca","Ciutadella Centre"]` y **sin** la opción global. Y la ruta **sí** le sirve el ámbito: `GET availability` sin tienda → `200`; `POST /api/ai/search/assisted` sin tienda → `200` con cantidades nulas; nombrando una tienda no asignada → **403**. La estrechez es de pantalla y no de autorización, como el requisito exige.

> **`op_verif_2t` / `Verif123!` queda creado en la base de desarrollo** con dos tiendas asignadas. Es el usuario que faltaba para ejercitar ese camino; bórralo si estorba.

### 11.11. Lo que **esta** pasada tampoco verifica

- **La demo desplegada.** Igual que el §9: la línea del compose está y hace lo que dice en local, pero el entorno de demostración no se levantó.
- **`ai-service`.** Ni la suite de Python ni `openapi.json`: comprobado que el diff no los toca, no ejecutado.
- **La ruta rápida con ámbito global.** Fuera de alcance por decisión; comprobado sólo que sigue respondiendo 400.
- **El `HTTP 500` dormido de `SearchLexicalAsync`.** Confirmada la **estructura** del defecto —`GroupBy` sólo en `HydrateAsync`, `ToDictionary(row => row.ProductId)` incondicional, único llamante con tienda concreta— pero **no se provocó el 500**, porque haría falta llamar al repositorio con nulo desde el servicio y hoy no hay camino. Sigue siendo razonamiento sobre el código, no una medición.
- **Cuál de los dos lados del desacuerdo del §11.3 es el correcto.** Es decisión de producto; queda en `DEFERRED_TASKS.md` con las dos salidas y su coste.
- **La cobertura del `ai-service`.** No se midió, y el DoD no la pide porque el change no lo toca.
- **Los 176 errores de `tsc` de la plantilla.** Filtrados, no revisados: son preexistentes y ajenos al change.

### 11.12. Los nombres que `tasks.md` promete y el árbol no tiene

Buscado en el árbol cada identificador de test que las tareas nombran. **Cuatro no existen así:**

| `tasks.md` dice | El árbol tiene |
|---|---|
| 2.3 `IsEnabledFor_WithoutPointOfSale_MatchesTheRoutePredicate` | `GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate` |
| 3.4 `Availability_WithoutPointOfSale_ReturnsDefaultScope` | `Availability_WithoutPointOfSale_ReturnsTheDefaultScope` |
| 3.4 `Availability_WithBlankPointOfSale_ReturnsBadRequest` | `Availability_WithBlankPointOfSale_Returns400` |
| 3.4 `Availability_WithoutPointOfSale_CallsNoAiService` | **no existe como test de integración**; lo cubre el unitario `GetAvailability_WithoutPointOfSale_MakesNoAiCall` |

Renombrar entre plan e implementación es normal, y los tres primeros son sólo eso. El cuarto es una tarea marcada `[x]` cuyo entregable literal —un test de integración— **no está**: lo que hay es un unitario que comprueba lo mismo sobre los dobles, sin pasar por HTTP. La cobertura existe; el recuento del §1.3 ya lo refleja (2 declaraciones en `AiSearchControllerTests`, no 3). Y la tarea 2.3 prometía comparar «los tres interruptores»: el test entregado compara dos, y el semántico va en un test aparte.

### 11.13. Lo que esta pasada reprodujo tal cual, midiéndolo otra vez

Que también es resultado, y aquí es la mayor parte:

| Afirmación del §1 al §10 | Reproducida |
|---|---|
| El área propia del backend, 122/122 en verde sobre `4b1d056` | ✅ **122/122**, idéntico |
| `openspec validate --all --strict` → `0 failed` | ✅ **63 passed · 0 failed**, antes y después de mis ediciones |
| La regla de la primera línea física en los 6 requisitos | ✅ los 6, 228–346 caracteres |
| `coverlet` no instrumenta `Application` (hallazgo del QA de C34) | ✅ **confirmado al reproducirlo**, y su apaño funciona |
| `SearchLexicalAsync` es un `HTTP 500` dormido | ✅ estructura confirmada: `GroupBy` sólo en `HydrateAsync`, `ToDictionary` incondicional en `AssistedSearchService:415`, único llamante con tienda concreta |
| `AiScopeSwitchExtensions` es el único sitio donde se decide el ámbito | ✅ los `IsEnabledFor(Guid)` que quedan están los tres en rutas cuyo punto de venta es obligatorio y validado: ruta rápida, ficha de venta y sustitutos. **Ningún camino que deba tratar la ausencia usa la sobrecarga no anulable** |
| La autorización **no** se endureció | ✅ comprobado contra la API viva con un operario real, no sólo por los tests: ámbito global servido con `200`, tienda no asignada con `403` |
| `openapi.json` sin diff, sin migraciones, `ai-service` sin tocar | ✅ `git diff` sobre los tres árboles: vacío |
| El área propia, verde en las dos suites | ✅ cero nombres de `AssistedSearch*`, `AiSearch*`, `FreeQuery*`, `AiScope*` ni `Availability*` en los rojos del backend; `assisted.test.tsx` ausente de los 113 del frontend |
| Sin `TODO`/`FIXME`/`HACK`/`XXX` | ✅ `grep` sobre el diff: ninguno |
| UI en es-ES, sin cifras en el ámbito global | ✅ leído en pantalla, las seis cadenas |
