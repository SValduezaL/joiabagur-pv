# C41 · `add-pos-projection-scheduled-drain` — mediciones de implementación

**Fecha:** 2026-09-26 · **Rama:** `c41-add-pos-projection-scheduled-drain` · **Historia:**
[HU-AIENG-041](../../Historias/AI-Eng/HU-AIENG-041.md) · **Ticket:**
[T-AIENG-041](../../../openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md)

---

## 1 · La afirmación central, verificada byte a byte

El change afirma que **el contrato congelado no se mueve**. Comprobado con el `sha256` anotado
antes de tocar nada y vuelto a tomar al cerrar:

| Momento | `sha256` de `ai-service/openapi.json` |
|---|---|
| Puerta de entrada | `8d9060acc5a74dff555ee3353354b503f81b71665bd8d04c0b3723128f027be4` |
| Cierre | `8d9060acc5a74dff555ee3353354b503f81b71665bd8d04c0b3723128f027be4` |

`git diff --stat ai-service/openapi.json` sale vacío, `test_openapi_snapshot_is_stable` pasa **sin
regenerar**, y la superficie sigue en **11 rutas bajo `/v1`** más `/health`. **Ninguna revisión de
Alembic ni migración de EF Core.**

## 2 · La medición que justifica el change, tomada sobre la base viva

### 2.1 · El arreglo manual caduca en una hora

La sesión que abrió C41 drenó a mano el 25 sep a las 20:49 UTC. Leído el checkpoint el 26 sep,
**antes** de implementar nada:

```
feed             | last_incremental_sync_at      | edad_seg | veredicto
pos-availability | 2026-09-25 20:49:24.836539+00 |   51.677 | STALE
```

**51.677 s — 14,4 veces el techo de 3.600 s.** Catorce horas rancio, un día después del arreglo
manual, sin que nadie lo supiera. Es la prueba de que el arreglo a mano no es un arreglo sino un
aplazamiento de sesenta minutos, y **es el argumento entero del change en una fila**.

### 2.2 · El drenaje de arranque lo cura solo

Ejecutado el camino real —`scheduler._boot_drain` con ajustes reales, feed real de la API .NET en
`localhost:5056` y base real—:

```
INFO scheduler  stage=pos_sync_scheduler trace_id=sync-pos-6ad52a7823eb boot_drain attempt=1
INFO httpx      GET /api/ai/index-feed/pos-availability?since=2026-08-29T10:13:38…&sinceId=0000… 200 OK
INFO orchestr.  stage=pos_sync done pages=1 upserted=1 soft_deleted=0 failed_pages=0
INFO scheduler  stage=pos_sync_scheduler drained pages=1 upserted=1 failed_pages=0
```

| | Antes | Después |
|---|---|---|
| `last_incremental_sync_at` | 2026-09-25 20:49:24 | **2026-09-26 12:16:14** |
| Edad | **55.545 s** | **9 s** |
| Veredicto del guard | `STALE` | **`FRESCA`** |

**Una página, un *upsert*, cero fallidas.** El incremental sobre una proyección de 6.720 filas que
llevaba un día sin drenarse cuesta **una página de feed**, que es la cifra que refuta la objeción de
C22 sobre el coste (*«un contenedor de 512 MiB compitiendo por un pool de cinco conexiones»*).

### 2.3 · El lock, contra PostgreSQL real

Con el lock tomado desde fuera, un drenaje real intentado encima:

```
INFO drain_lock stage=pos_sync trace_id=sync-pos-d6acb00c2e99 lock_held feed=pos-availability skipped=1
outer lock granted = True
inner drain declined = True   pages = 0
```

**Declinó de inmediato, no se bloqueó, y escribió cero páginas.** Ése es exactamente el escenario
que ocurrió las tres veces —alguien corriendo `sync-pos` a mano— y que el ticket original dejaba
fuera al colocar el lock en el planificador en lugar de dentro del drenaje.

### 2.4 · `/health` reporta lo que nadie reportaba

Informe real contra la base viva:

```json
{
  "status": "ok",
  "synced_at": "2026-09-26T12:16:14.133120+00:00",
  "full_synced_at": "2026-09-25T20:49:24.836539+00:00",
  "age_seconds": 38.30,
  "ceiling_seconds": 3600,
  "stale": false,
  "failed_pages": 0,
  "points_of_sale": 12,
  "shops_without_scope": 1
}
```

**`shops_without_scope: 1`, y es un hallazgo real.** El POS `cd9bfd1f…` tiene **0 filas asignadas
sobre 144** en esta base, así que responde **503 a toda recuperación** con ámbito — el modo de fallo
que C34 encontró en la demo y que llevaba desde entonces sin reportarse en ninguna parte. Es la
primera vez que aparece en una pantalla.

Reparto por punto de venta de la proyección, para contexto:

| Asignados | Puntos de venta |
|---|---|
| 1.082 · 871 · 813 | los tres mayores |
| 469 · 457 · 441 · 434 · 422 · 416 · 404 · 241 | el resto con surtido |
| **0** *(sobre 144 filas)* | **`cd9bfd1f…` — 503 en toda recuperación** |

## 3 · Dos hallazgos de la implementación

### 3.1 · Una invariante de arquitectura cazó el primer diseño, y tenía razón

El primer cableado importaba `jbg_ai.indexing.scheduler` desde `api/main.py`, y
`test_main_does_not_import_indexing` falló. **No es una regla cosmética**: `indexing/cli.py` importa
`LiteLlmEmbeddingClient` y con él el SDK del proveedor, así que la cadena habría metido maquinaria de
proveedor en el grafo de importación de un proceso cuyo trabajo es responder HTTP.

Se arregló **por arquitectura y no editando el test**:

- `indexing/pos_drain.py`, nuevo, con la construcción del drenaje — feed, repositorio y lock — y
  **sin tocar embeddings**, porque este drenaje no embebe nada y no necesita clave de embeddings.
- `api/lifespan.py`, nuevo, para que `main.py` siga sin nombrar `jbg_ai.indexing`.
- **El guardián se extendió al fichero nuevo** en lugar de dejar el hueco abierto:
  `test_lifespan_reaches_the_drain_without_the_provider_sdk` comprueba que ni el lifespan ni el
  planificador importan `indexing.cli` ni `indexing.embeddings`.

### 3.2 · `failed_pages` se lee de `ai.sync_failure`, no del último drenaje

La spec delta decía inicialmente *«el recuento de páginas fallidas del drenaje más reciente»*. Ese
dato **no está persistido en ninguna parte**: se pierde al reiniciar. Se corrigió la spec antes de
implementar, para leer el recuento de **`ai.sync_failure`** — que es acumulativo, sobrevive al
reinicio, y **nadie leía hasta ahora**, así que una página que falló hace meses era invisible para
siempre.

## 4 · Estado de las suites

| Suite | Puerta de entrada | Cierre |
|---|---|---|
| `ai-service` (`uv run pytest`) | **1.623 passed · 0 failed** | **1.649 passed · 0 failed** |
| `frontend` (`npm run test`) | **119 failed / 730 passed** (849) en **17** de 57 ficheros | **119 failed / 735 passed** (854) en **18** de 57 ficheros |
| `backend` (`dotnet test`) | **45 failed / 1.284 passed** (1.329), del `baseline.trx` de las 02:11 | **48 failed / 1.299 passed** (1.347) · 19 m 51 s |

### 4.1 · `ai-service`: +26 tests y ni un fallo

1.623 → **1.649**, cero rojos a los dos lados. Los 26 son exactamente los que este change añade:

| Fichero | Tests |
|---|---|
| `tests/indexing/test_pos_scheduler.py` | **17**, nuevo |
| `tests/api/test_health_report.py` | **+6** sobre la sección `projection` |
| `tests/indexing/test_embeddings.py` | **+1**, el guardián de arquitectura extendido |
| `tests/indexing/` (subtotal) | 98 → **116** |

Incluye `test_openapi_snapshot_is_stable`, que pasa **sin regenerar** el contrato.

### 4.2 · `frontend`: la comparación se hace por nombres, y el área propia está limpia

**Tres pasadas completas sobre este árbol** dieron **119 / 114 / 119** fallos en **17 / 15 / 18**
ficheros. Es la rotación que `CLAUDE.md` documenta —anotada allí en 113-114 sobre 729 tests, y el
árbol ha crecido desde entonces—, y el recuento por sí solo no dice nada.

**Lo que sí dice algo: los 18 ficheros en rojo de la pasada de cierre, y ninguno es de este change.**

```
admin/__tests__/family-review · admin/__tests__/profile-review
payment-methods/payment-methods · products/__tests__/edit · products/edit
products/components/product-photo-upload
sales/__tests__/{assist-entrances, assisted, new-image, new, sales-index, scan}
services/__tests__/{image-recognition.service, ml-edge-cases, model-training.service}
services/{auth.service, payment-method.service, product.service}
```

`src/pages/dashboard/ai-service-status.test.tsx` **no aparece en ninguna de las tres**, y ejecutado
en aislamiento da **9 de 9 en verde** — los 4 que ya existían más los 5 que este change añade.

> **Limitación declarada:** la lista de nombres de la pasada de *puerta de entrada* se perdió, porque
> se capturó a través de `tail`. La comparación de arriba es entre las tres pasadas del árbol ya
> modificado más la verificación dirigida del área propia; no es una comparación contra la lista
> original. El recuento de la puerta de entrada (119 en 17) sí se conserva.

### 4.3 · El backend: bloqueado durante la implementación, medido al cierre

**Resultado con la API parada: 1.347 tests · 1.299 correctas · 48 con error · 19 m 51 s.**

Comparado **por nombres** contra el `baseline.trx` de las 02:11: **6 entran, 3 salen**.

| Entran en rojo | Salen del rojo |
|---|---|
| `InventoryIntegrationTests.Admin_ManageAllProducts_ShouldSucceed` | `InventoryIntegrationTests.MovementHistory_WithPagination_ShouldReturnPagedResults` |
| `InventoryIntegrationTests.AssignProduct_WithNonExistentProduct_ShouldReturnNotFound` | `InventoryIntegrationTests.Operator_ViewStock_ForUnassignedPOS_ShouldReturnEmpty` |
| `InventoryIntegrationTests.ExcelImport_ValidFile_ShouldImportSuccessfully` | `InventoryIntegrationTests.SaleMovement_ResultingInNegativeStock_ShouldBeRejected` |
| `InventoryIntegrationTests.Operator_ViewStock_ForAssignedPOS_ShouldSucceed` | |
| `InventoryIntegrationTests.StockAdjustment_WithNonExistentProduct_ShouldReturnBadRequest` | |
| `SalesControllerTests.CreateSale_OperatorNotAssignedToPOS_ReturnsBadRequest` | |

**Ocho de los nueve están en `InventoryIntegrationTests`**, la primera clase que `CLAUDE.md` nombra
como inestable. El noveno está en `SalesControllerTests`, que ya traía cuatro fallos en la línea base.
**Mi área —`AiGatewayHealthTests` (4) y `AiHealthControllerTests` (3)— da 7 de 7 en verde**, y no
aparece ni en los 45 de la base ni en los 48 del cierre. **No se añadió ni se modificó un solo test
.NET**, comprobado con `git status --porcelain backend/src/JoiabagurPV.Tests/`, que sale vacío.

> **El recuento total sube de 1.329 a 1.347 y no es mío.** El `baseline.trx` es de las **02:11**,
> antes de que C40_FIX cerrara: su propio QA registra que pasó de **1.329 a 1.339** tests y de **45 a
> 52** fallos. Medido contra **su cierre**, este árbol da **1.347 · 48**: cuatro fallos menos.

### 4.4 · Por qué estuvo bloqueado, y la trampa confirmada

`dotnet test` devolvió **exit code 0 sin ejecutar un solo test**:

```
error MSB3027: No se pudo copiar "JoiabagurPV.Domain.dll" … Se superó el número de 10 reintentos.
El archivo se ha bloqueado por: "JoiabagurPV.API (29688)"
```

Es **exactamente la trampa que `CLAUDE.md` documenta** —*«si algo mantiene `bin/Debug` bloqueado, la
build falla, cero tests se ejecutan, y `dotnet test` sigue saliendo con 0»*—, confirmada en vivo. El
proceso que bloquea es la API .NET que sirve el feed, y **hacía falta corriendo** para las
comprobaciones del §2. **No se mató**: es el entorno del desarrollador, y pararla habría impedido
medir justo lo que este change viene a medir.

**Lo que sí se verificó:** `dotnet build JoiabagurPV.Application.csproj` → **compilación correcta, 0
errores, 0 advertencias**. Es el único proyecto de `backend/` que este change toca, y sólo por
**adición de una propiedad anulable** a `AiHealthResponse`; no se retira ni cambia de tipo ningún
campo.

> **Cerrado.** Se paró la API y se ejecutó la suite entera; el resultado y la comparación por nombres
> están en el §4.3. La build pasó a la primera, lo que confirma que el bloqueo era el proceso y nada
> más.

### 4.2 · El backend no se pudo medir, y la causa está documentada

`dotnet test` devolvió **exit code 0 sin ejecutar un solo test**:

```
error MSB3027: No se pudo copiar "JoiabagurPV.Domain.dll" … Se superó el número de 10 reintentos.
El archivo se ha bloqueado por: "JoiabagurPV.API (29688)"
```

Es **exactamente la trampa que `CLAUDE.md` documenta** —*«si algo mantiene `bin/Debug` bloqueado, la
build falla, cero tests se ejecutan, y `dotnet test` sigue saliendo con 0»*—, confirmada en vivo. El
proceso que bloquea es la API .NET que está sirviendo el feed, y **hacía falta corriendo** para las
comprobaciones del §2. **No se mató**: es el entorno del desarrollador, y cerrarlo habría impedido
medir lo que este change viene a medir.

**Consecuencia declarada:** el único fichero de `backend/` que este change toca es
`AiHealthResponse.cs`, y sólo por **adición de una propiedad anulable**. No se retira ni cambia de
tipo ningún campo existente, así que el riesgo es acotado — pero **la suite del backend no está
medida en esta rama** y hay que correrla con la API parada antes de archivar.

## 5 · Lo que no se hizo, y por qué

| | Razón |
|---|---|
| **Vaciar el checkpoint para probar el drenaje completo contra la base viva** | Habría obligado a un `--full` de 34 páginas para restaurar el entorno del desarrollador. Cubierto por `test_the_boot_drain_does_not_force_a_full_run` y por la cobertura que C22 ya tiene de `resolve_start_cursor` con cursor ausente |
| **Limpiar las 94 filas residuales del `UPDATE` de C40** | Son la prueba forense del hallazgo, son `is_assigned_hint = false` y el prefiltro exige `IS TRUE`, así que no alcanzan ninguna consulta viva |
| **Re-medir el grupo 8 de C40** | Decisión D15. El arnés nunca se commiteó, así que rehacerlo es reescribirlo; y hacerlo antes de este change reproduciría el defecto |
| **Un botón de drenaje manual** | Cortado en el diseño. Con arranque y 600 s ahorra como mucho diez minutos, y costaría una ruta en un contrato congelado |
