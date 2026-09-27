# QA — C41 `add-pos-projection-scheduled-drain`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados y su evidencia.
> **Fecha:** exploración, artefactos e implementación el **2026-09-26** · **Rama:** `c41-add-pos-projection-scheduled-drain` · **Artefactos de partida:** `55bacb6` (historia, ticket enriquecido, `epicas.md` y ficha del plan), publicado en `origin` · **Implementación NO commiteada**: lo que este documento verifica es el árbol de trabajo sobre `55bacb6`.
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la [HU](../../../../Documentos/Historias/AI-Eng/HU-AIENG-041.md).
> **Alcance:** **32/32 tareas**, con **dos ejecutadas por cobertura de test en vez de contra el entorno vivo** y declaradas como tales (§9).
> **Este change NO mueve el contrato:** `ai-service/openapi.json` con el **mismo `sha256`** antes y después, sin diff, sin regenerar (§5).
> **Este change NO crea migraciones:** ni revisión de Alembic ni migración de EF Core (§5).
> **Este change NO llamó a ningún proveedor.** El drenaje **no embebe nada** y no necesita clave de embeddings; las comprobaciones en vivo del §4 son SQL y HTTP contra el feed local. Coste de proveedor: **cero**.
> **Lo que esta pasada encontró:** **un defecto de arquitectura cazado por un test existente** que obligó a rediseñar el cableado (§8.1), **un defecto de spec propio —cinco escenarios que una delta se dejaba y habría borrado al sincronizar— encontrado al escribir este documento y corregido en el acto** (§8.2), **un requisito de spec propio que pedía un dato no persistido**, corregido antes de implementarlo (§8.3), **un test propio frágil** reescrito (§8.4), y **la trampa del `dotnet test` que sale 0 sin ejecutar nada**, confirmada en vivo (§8.5) y **cerrada después parando la API** (§1.5).
> **Las tres suites están medidas:** `ai-service` **1.649 · 0 fallos**, `frontend` con el área propia en 9/9 y ausente de las tres listas de rojos, y `backend` **1.347 · 48**, con los 9 nombres discrepantes concentrados en la clase que `CLAUDE.md` documenta como inestable y **mi área en 7/7**.
>
> **▸ Este documento es la autodeclaración del implementador.** No hay verificación independiente todavía.

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python / `ai-service` | `uv run --system-certs pytest`, Python 3.11, Windows 11 · Git Bash |
| PostgreSQL de las comprobaciones en vivo | `jpv-pv-postgres`, puerto **5433**, base `joiabagur_pv` — **6.720 filas** en `ai.pos_projection`, **12 puntos de venta**, 11 con surtido |
| Feed en las comprobaciones en vivo | API .NET real en `localhost:5056`, `GET /api/ai/index-feed/pos-availability` → **200** con `X-Index-Feed-Key` |
| `jbg-ai` en la suite | Nunca alcanza un proveedor: los dobles son inyectados, y el drenaje **no embebe** |
| `jbg-ai` como contenedor | `jpv-pv-jbg-ai` corre la **imagen anterior a este change**, así que la tarjeta no se pudo ver contra él (§9) |
| Frontend | `vitest` sobre el árbol de la rama · `tsc --noEmit` filtrado a ficheros propios |
| Backend | `dotnet build` del proyecto tocado y **`dotnet test JoiabagurPV.sln` completo con la API parada** (§1.5). Durante la implementación no era ejecutable — §8.5 |
| Contrato | `openapi.json` **no regenerado**; `sha256` comparado antes y después |
| Migraciones | **Ninguna**: el diff no toca `ai-service/migrations/` ni `JoiabagurPV.Infrastructure/` |

---

## 1. Suites automáticas

| Ejecución | Resultado |
|---|---|
| `sha256` de `openapi.json` **antes de tocar nada** | `8d9060ac…27be4` |
| `openspec validate --all --strict` **antes de empezar** | **63 passed · 0 failed** |
| `pytest tests/indexing` antes de tocar `api/` | **98 passed · 0 failed** · 12,8 s |
| **Línea base frontend** (`npm run test`) | **119 en rojo · 730 en verde · 849 tests · 17 de 57 ficheros** · 466 s |
| **Línea base backend** | **45 de 1.329**, recuperada de `TestResults/baseline.trx` (26 sep 02:11) — ver §1.5 |
| `pytest tests/indexing/test_embeddings.py tests/config` tras el rediseño del §8.1 | **63 passed** · 0,65 s |
| `pytest tests/api tests/indexing` tras cablear el planificador | **343 passed · 0 failed** · 94,9 s |
| `pytest tests/indexing/test_pos_scheduler.py` | **17 passed** · 0,49 s |
| `pytest tests/api/test_health_report.py test_health.py test_openapi_snapshot.py` | **30 passed** · 2,76 s |
| `pytest tests/indexing` tras limpiar el import muerto | **116 passed · 0 failed** · 136,7 s |
| **Cierre `ai-service`** (suite completa) | **1.649 passed · 0 failed** · 771,5 s (12 m 51 s) |
| `vitest ai-service-status.test.tsx` | **9 / 9 en verde** — 4 previos más 5 nuevos |
| **Cierre frontend** (dos pasadas completas) | **114 en rojo · 740 en verde (854)** en 15 ficheros · **119 en rojo · 735 en verde (854)** en 18 ficheros |
| `tsc --noEmit` filtrado a `AdminDashboard` y `ai-health` | **sin errores** |
| `dotnet build JoiabagurPV.Application.csproj` | **Compilación correcta · 0 errores · 0 advertencias** · 65 s |
| **Cierre backend** (`dotnet test JoiabagurPV.sln`, **con la API parada**) | **1.347 tests · 1.299 correctas · 48 con error** · 19 m 51 s |
| `AiGatewayHealthTests` + `AiHealthControllerTests` al cierre | **7 / 7 en verde** |
| `openspec validate add-pos-projection-scheduled-drain --strict` | `Change '…' is valid` |
| `openspec validate --all --strict` **al cerrar** | **63 passed · 0 failed** |
| `sha256` de `openapi.json` **al cerrar** | `8d9060ac…27be4` — **idéntico** |

### 1.1. `ai-service`: la aritmética cierra exactamente

| | Tests |
|---|---|
| Línea base derivada | **1.625** |
| Cierre medido | **1.649 passed · 0 failed** |
| Diferencia | **+24** |

Los 24 son exactamente los que este change añade:

| Fichero | Nuevos |
|---|---|
| `tests/indexing/test_pos_scheduler.py` | **17** |
| `tests/api/test_health_report.py` | **6** |
| `tests/indexing/test_embeddings.py` | **1** |
| **Total** | **24** |

Corroborado por el subtotal, que se midió de forma independiente: `tests/indexing` pasó de **98** a
**116**, o sea **+18 = 17 + 1**, y `+6` en `tests/api`. Las dos cuentas coinciden.

> **Salvedad declarada, y es un defecto de método mío.** La línea base de **1.625** es **derivada, no
> medida limpiamente**. La pasada que iba a ser la línea base se lanzó **después** de haber editado ya
> `drain_lock.py` y `pos_orchestrator.py`, y terminó mientras yo editaba `main.py`: dio **2 failed ·
> 1.623 passed**, y los dos fallos eran los guardianes que mi propia edición en vuelo rompió (§8.1).
> No se volvió a medir con `git stash push -u` porque el árbol tiene 28 ficheros sin commitear y la
> orden era **no commitear**: arriesgar un `stash pop` sobre trabajo sin commitear para confirmar un
> número que la aritmética corrobora por dos vías no me pareció un intercambio razonable. **Queda
> dicho en vez de disimulado.**

### 1.2. Los 24 tests nuevos, por nombre

**Lock (6):**

```
test_a_drain_that_cannot_take_the_lock_declines_and_writes_nothing
test_a_declined_drain_is_not_reported_as_an_empty_success
test_the_lock_is_released_so_the_next_drain_proceeds
test_the_lock_is_released_even_when_the_drain_raises
test_a_real_drain_always_constructs_a_lock
test_the_lock_key_is_a_documented_constant
```

**Planificador (11):**

```
test_the_scheduler_does_not_run_under_stub_mode
test_the_scheduler_does_not_run_when_switched_off
test_the_scheduler_does_not_run_without_a_configured_feed
test_the_scheduler_runs_by_default
test_a_drain_that_raises_never_escapes_the_scheduler
test_an_unconfigured_feed_is_reported_and_not_raised
test_the_boot_drain_retries_until_the_feed_answers
test_the_boot_drain_gives_up_to_the_interval
test_the_boot_drain_does_not_force_a_full_run
test_the_interval_default_leaves_room_for_several_failures
test_a_blank_export_of_either_setting_is_the_default
```

**Informe de salud (6):**

```
test_health_reports_projection_freshness_from_the_checkpoint
test_health_reports_a_stale_projection_without_degrading_the_service
test_health_reports_a_point_of_sale_left_without_any_assortment
test_health_distinguishes_a_projection_never_drained_from_a_stale_one
test_health_reports_failed_pages_rather_than_swallowing_them
test_health_still_carries_the_projection_when_the_database_is_unreachable
```

**Guardián de arquitectura (1):**

```
test_lifespan_reaches_the_drain_without_the_provider_sdk
```

**Frontend (5):**

```
should show the projection age on the AI service card
should warn about completeness and never about reliability when the projection is stale
should name the points of sale with no scope when there are any
should tell a projection never drained from a stale one
should render the card unchanged when the AI service does not report the projection
```

### 1.3. La comparación del frontend: por nombres, y el área propia no aparece

**Tres pasadas completas sobre este árbol:** **119 / 114 / 119** fallos en **17 / 15 / 18** ficheros.
El recuento por sí solo no dice nada — `CLAUDE.md` lo registra en 113-114 sobre 729 tests y el árbol
ha crecido a 854. **Lo que sí dice algo son los nombres de fichero.** Los 18 de la pasada de cierre:

```
admin/__tests__/family-review            admin/__tests__/profile-review
payment-methods/payment-methods          products/__tests__/edit
products/edit                            products/components/product-photo-upload
sales/__tests__/assist-entrances         sales/__tests__/assisted
sales/__tests__/new-image                sales/__tests__/new
sales/__tests__/sales-index              sales/__tests__/scan
services/__tests__/image-recognition.service
services/__tests__/ml-edge-cases         services/__tests__/model-training.service
services/auth.service                    services/payment-method.service
services/product.service
```

**`src/pages/dashboard/ai-service-status.test.tsx` no aparece en ninguna de las tres**, y ejecutado en
aislamiento da **9 de 9 en verde**. Ninguno de los 18 importa nada que este change toque: los ficheros
modificados del frontend son `AdminDashboard.tsx` y `ai-health.types.ts`, y ningún test de esa lista
los alcanza.

> **Salvedad declarada, y es el mismo defecto de método que el §8.1 de C40_FIX registró.** La lista de
> nombres de la **línea base** se perdió: la pasada se capturó a través de `tail -60`, que se quedó con
> el resumen y no con el detalle. La comparación de arriba es **entre las tres pasadas del árbol ya
> modificado**, más la verificación dirigida del área propia. El recuento de la línea base (119 en 17)
> sí se conserva. **Volvió a pasarme lo que ese documento ya había documentado.**

### 1.5. El backend, medido con la API parada, y comparado por nombres

El §8.5 dejó esta casilla abierta. **Se cerró**: se paró `JoiabagurPV.API` (PID 29688) y se ejecutó la
suite entera contra `backend/src/JoiabagurPV.sln`.

| | Tests | Correctas | Con error |
|---|---|---|---|
| Línea base (`TestResults/baseline.trx`, 26 sep **02:11**) | 1.329 | 1.284 | **45** |
| **Cierre** (26 sep, API parada) | **1.347** | **1.299** | **48** |

**La comparación por nombres: 6 entran, 3 salen.**

| Entran en rojo al cierre | Salen del rojo |
|---|---|
| `InventoryIntegrationTests.Admin_ManageAllProducts_ShouldSucceed` | `InventoryIntegrationTests.MovementHistory_WithPagination_ShouldReturnPagedResults` |
| `InventoryIntegrationTests.AssignProduct_WithNonExistentProduct_ShouldReturnNotFound` | `InventoryIntegrationTests.Operator_ViewStock_ForUnassignedPOS_ShouldReturnEmpty` |
| `InventoryIntegrationTests.ExcelImport_ValidFile_ShouldImportSuccessfully` | `InventoryIntegrationTests.SaleMovement_ResultingInNegativeStock_ShouldBeRejected` |
| `InventoryIntegrationTests.Operator_ViewStock_ForAssignedPOS_ShouldSucceed` | |
| `InventoryIntegrationTests.StockAdjustment_WithNonExistentProduct_ShouldReturnBadRequest` | |
| `SalesControllerTests.CreateSale_OperatorNotAssignedToPOS_ReturnsBadRequest` | |

**Ocho de los nueve nombres discrepantes están en `InventoryIntegrationTests`**, la primera de las
tres clases que `CLAUDE.md` nombra como inestables — *«un nombre rojo nuevo en
`InventoryIntegrationTests` es un martes»*. El noveno está en `SalesControllerTests`, que **ya traía
cuatro fallos en la línea base**, así que la clase venía roja.

**Tres evidencias de que ninguno es mío**, en orden creciente de fuerza:

1. **No existe camino causal.** El único fichero de `backend/` que este change toca es
   `AiHealthResponse.cs`, y sólo por **adición de una propiedad anulable**. Ninguna de las clases de
   arriba lo referencia.
2. **No añadí ni modifiqué un solo test .NET.** `git status --porcelain backend/src/JoiabagurPV.Tests/`
   devuelve **vacío**.
3. **Mi área está verde: 7 de 7.** `AiGatewayHealthTests` (4) y `AiHealthControllerTests` (3), todas
   correctas, y **ninguna aparece en los 45 de la línea base ni en los 48 del cierre**.

> **Salvedad sobre el recuento total, y no es mía.** La línea base marca **1.329 tests** y el cierre
> **1.347**: dieciocho más. **Yo no añadí ninguno** (evidencia 2). El `baseline.trx` está fechado a las
> **02:11**, antes de que C40_FIX cerrara: su propio QA registra que pasó de **1.329 a 1.339** tests y
> de **45 a 52** fallos, y su commit de verificación es de las 10:59. Los dieciocho son suyos, no míos.
> Medido contra **su cierre** —1.339 · 52— este árbol da **1.347 · 48**, o sea **cuatro fallos menos**.

### 1.4. Los tests nuevos no pasan en vacío

Dos comprobaciones de que los tests del lock miden algo:

1. **`test_a_drain_that_cannot_take_the_lock_declines_and_writes_nothing`** no se conforma con
   `declined is True`: afirma además `feed.requests == []` y `repo.checkpoints == {}`. Un lock que
   declinara **después** de pedir la primera página pasaría la primera aserción y fallaría las otras
   dos, que son las que describen el daño que el lock existe para evitar.
2. **`test_a_declined_drain_is_not_reported_as_an_empty_success`** ejecuta los **dos** casos —declinado
   y vacío— y comprueba que sus contadores son idénticos (`upserted == 0` los dos) y que sólo
   `describe()` los distingue. Es la aserción de que el problema existía.

Y el del guardián se comprobó **en rojo antes de estar en verde**: es el que falló y provocó el §8.1.

---

## 2. La puerta de entrada

| Comprobación | Resultado |
|---|---|
| `sha256` de `openapi.json` anotado **antes** de la primera edición | `8d9060acc5a74dff555ee3353354b503f81b71665bd8d04c0b3723128f027be4` |
| `openspec validate --all --strict` | **63 passed · 0 failed** |
| `pytest tests/indexing` | **98 passed** |
| `npm run test` | **119 / 730 / 849** en 17 ficheros |
| `dotnet test` | **bloqueado** (§8.5) |

---

## 3. Las deltas de spec

### 3.1. Cada `## MODIFIED` reproduce el requisito vivo entero — **y una no lo hacía**

Comprobado **por comparación automática** de los escenarios del requisito en la delta contra los del
mismo requisito en la spec viva:

| Capability | Requisito | Escenarios perdidos |
|---|---|---|
| `pos-projection` | `The POS availability feed is drained into ai.pos_projection by a CLI` | **1, deliberado** — ver 3.2 |
| `ai-service-runtime` | `Service exposes public health with version` | **0** *(eran 5 antes de corregir — §8.2)* |
| `demo-deployment` | `Deployment is verified from inside the host` | **0** |

Las tres cabeceras `### Requirement:` coinciden **carácter a carácter** con las de la spec viva,
comprobado con `grep -qxF`. Los tres requisitos `## ADDED` de `pos-projection` **no** existen en la
viva, como debe ser.

### 3.2. El único escenario que no se conserva, y por qué

`pos-projection` pierde **`#### Scenario: The only schema change is one additive nullable column`**, y
es **intencionado**. Ese escenario afirmaba que *«exactamente una revisión nueva existe y sólo añade
`computed_as_of`»*, que era la entrega de C22. C41 **no abre ninguna revisión**, así que se sustituye
por `#### Scenario: No schema change is opened`, que afirma lo que hay que afirmar sobre este árbol:
cero revisiones nuevas, cero migraciones de EF Core, ninguna tabla creada, alterada o borrada.
Conservar el original habría dejado en la spec viva una afirmación que el árbol ya no puede satisfacer.

### 3.3. La regla de la primera línea física, en los 6 requisitos

`CLAUDE.md` avisa de que el validador lee **sólo la primera línea física** de la descripción y falla con
*«must contain SHALL or MUST»* aunque lo contenga. Comprobado uno a uno:

| Requisito | Longitud de la 1ª línea | `SHALL`/`MUST` |
|---|---|---|
| `The POS availability feed is drained…` | 864 | ✅ |
| `The POS drain runs at start-up and on an interval…` | 522 | ✅ |
| `Concurrent drains are refused rather than interleaved` | 459 | ✅ |
| `The projection reports how many points of sale carry no assortment` | 194 | ✅ |
| `Service exposes public health with version` | 225 | ✅ |
| `Deployment is verified from inside the host` | 472 | ✅ |

### 3.4. La delta corrige su propio requisito antes de implementarlo

El requisito de `ai-service-runtime` pedía originalmente *«el recuento de páginas fallidas del drenaje
más reciente»*. **Ese dato no está persistido en ninguna parte**: se pierde al reiniciar el proceso. Se
corrigió la spec **antes** de escribir el código, para leerlo de `ai.sync_failure` — acumulativo,
persistido, y **sin lector hasta ahora**. Detalle en el §8.3.

---

## 4. Las comprobaciones en vivo, contra la base y el feed reales

Las cuatro se ejecutaron contra `jpv-pv-postgres` (6.720 filas) y la API .NET real en `localhost:5056`,
y las cuatro **leen el checkpoint y nunca `MAX(refreshed_at)`**, que es lo que la nota de método del
ticket exige.

### 4.1. El entorno estaba rancio, y es la medición que justifica el change

```
feed             | last_incremental_sync_at      | edad_seg | veredicto
pos-availability | 2026-09-25 20:49:24.836539+00 |   51.677 | STALE
```

**51.677 s — 14,4 veces el techo de 3.600 s**, catorce horas después de que la sesión que abrió C41 lo
drenara a mano. **El arreglo manual caduca en una hora.**

### 4.2. El drenaje de arranque lo cura solo

Ejecutado el camino real (`scheduler._boot_drain`) con ajustes reales:

```
INFO scheduler  stage=pos_sync_scheduler trace_id=sync-pos-6ad52a7823eb boot_drain attempt=1
INFO httpx      GET /api/ai/index-feed/pos-availability?since=2026-08-29T10:13:38…&sinceId=0000… 200 OK
INFO orchestr.  stage=pos_sync done pages=1 upserted=1 soft_deleted=0 failed_pages=0
INFO scheduler  stage=pos_sync_scheduler drained pages=1 upserted=1 soft_deleted=0 failed_pages=0
```

| | Antes | Después |
|---|---|---|
| `last_incremental_sync_at` | `2026-09-25 20:49:24` | **`2026-09-26 12:16:14`** |
| Edad | **55.545 s** | **9 s** |
| Veredicto | `STALE` | **`FRESCA`** |

**Una página, un *upsert*, cero fallidas.** Es también la cifra que refuta la objeción de coste de C22
(*«un contenedor de 512 MiB compitiendo por un pool de cinco conexiones»*).

### 4.3. El lock, contra PostgreSQL real

Con el lock tomado desde fuera y un drenaje real intentado encima:

```
INFO drain_lock stage=pos_sync trace_id=sync-pos-d6acb00c2e99 lock_held feed=pos-availability skipped=1
outer lock granted = True
inner drain declined = True   pages = 0
```

**Declinó de inmediato, no se bloqueó, escribió cero páginas**, y registró `lock_held` con su
`trace_id`. Es exactamente el escenario que ocurrió las tres veces —alguien corriendo `sync-pos` a
mano— y el que el ticket original dejaba fuera al colocar el lock en el planificador.

### 4.4. `/health` reporta lo que nadie reportaba, y encuentra algo real

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

**`shops_without_scope: 1` no es un valor de prueba: es un hallazgo.** El punto de venta
`cd9bfd1f-f1b2-4795-9d14-867a75c18f90` tiene **0 filas asignadas sobre 144** en esta base, así que
responde **503 a toda recuperación** con ámbito. Es el modo de fallo que C34 encontró en la demo el
2026-09-22 y que llevaba desde entonces **sin reportarse en ninguna parte**. Primera vez que aparece en
un informe.

Reparto completo, leído de `ai.pos_projection`:

| Asignados | Filas | Punto de venta |
|---|---|---|
| 1.082 · 871 · 813 | 1.176 · 936 · 888 | los tres mayores |
| 469 · 457 · 441 · 434 · 422 · 416 · 404 · 241 | — | el resto con surtido |
| **0** | **144** | **`cd9bfd1f…` — 503 en toda recuperación** |

---

## 5. El contrato y el alcance negativo, demostrados

| Afirmación | Cómo se comprobó | Resultado |
|---|---|---|
| **El contrato congelado no se mueve** | `sha256sum` antes y después | `8d9060ac…27be4` = `8d9060ac…27be4` |
| | `git diff --stat ai-service/openapi.json` | **0 líneas** |
| | `test_openapi_snapshot_is_stable` | **pasa sin regenerar** |
| **Ninguna ruta nueva bajo `/v1`** | `grep -c '"/v1/' openapi.json` | **11**, las mismas |
| **Ninguna migración** | `git status --porcelain ai-service/migrations/ JoiabagurPV.Infrastructure/` | **0 ficheros** |
| **`Carried()` no se toca** | `git status --porcelain …/Data/Repositories/` | **0 ficheros** |
| **`GET /api/ai/search/availability` no se toca** | `git status --porcelain JoiabagurPV.API/ JoiabagurPV.Domain/` | **0 ficheros** |
| **Los ajustes nuevos no alcanzan el contrato** | `grep -c jpv_pos_sync` en `canonical_openapi_settings()` | **0** de 4 apariciones |
| **Sin insignia de operario, sin botón manual** | El diff del frontend son 2 ficheros: la tarjeta de administrador y sus tipos | ✅ |

---

## 6. El DoD del ticket, casilla a casilla

| Casilla | Estado | Evidencia |
|---|---|---|
| Planificador de arranque e intervalo sin reescribir `sync_pos_availability` | ✅ | El page loop se extrajo a `_drain()` sin cambiar una línea de su lógica |
| `pg_try_advisory_lock` no bloqueante **dentro** del drenaje, con test de que cubre al CLI | ✅ | `test_a_real_drain_always_constructs_a_lock` + §4.3 en vivo |
| El arranque no se bloquea; `/health` 200 durante el drenaje inicial | ✅ | `build_lifespan` crea la tarea sin `await`; §4.2 arrancó y respondió |
| Sección `projection` leída del **checkpoint** y nunca de `refreshed_at` | ✅ | `_PROJECTION_CHECKPOINT_SQL` + `test_health_reports_projection_freshness_from_the_checkpoint` |
| DTO/tipos/tarjeta tolerantes a la ausencia de la sección | ✅ | `AiHealthProjection?` anulable + `should render the card unchanged when the AI service does not report the projection` |
| `verify.sh` falla con proyección vacía; deuda de C34 cerrada | ✅ | Quinta condición añadida; entrada de `DEFERRED_TASKS.md` marcada como cerrada |
| `uv run pytest` en verde sin proveedor, embeddings ni RDS | ✅ | **1.649 passed · 0 failed** |
| `test_openapi_snapshot_is_stable` pasa sin regenerar, `sha256` coincide | ✅ | §5 |
| Backend: xUnit, nomenclatura `Método_Escenario_Resultado` | ✅ | **No se añadió ni un test .NET**, y es correcto: el cambio es una propiedad anulable en un DTO que ningún test referencia. `dotnet build` en verde, y **la suite completa se ejecutó con la API parada**: 1.347 · 48, con las 7 de `AiHealth*` en verde (§1.5) 
| Frontend: Vitest + RTL, `should … when …`, queries accesibles | ✅ | 5 tests nuevos, todos con `findByText` |
| Línea base de las tres suites **por nombres** | ⚠️ | Python y frontend sí, con las salvedades de 1.1 y 1.3. **Backend no** (§8.5) |
| Specs actualizadas y `openspec validate --all --strict` en verde | ✅ | **63 passed · 0 failed** |
| Ninguna migración | ✅ | §5 |
| Ninguna ruta nueva; `availability` sin tocar | ✅ | §5 |
| Las tres frases falsas retiradas | ✅ | `ai-service/README.md` ×2 y `openspec/project.md` ×1 |
| Informe de C40 anotado sin tocar ningún número | ✅ | Bloque `⚠ Anotación posterior` insertado; las cifras originales intactas |
| `epicas.md`, ficha del plan y `deploy/demo/README.md` al día | ✅ | Commit `55bacb6` y el diff actual |
| UI en es-ES | ✅ | Toda la copia nueva de la tarjeta |
| Sin TODO/FIXME sin seguimiento | ✅ | Ninguno introducido |

---

## 7. Lo que la implementación refutó de lo escrito antes

| Escrito en | Decía | Y es |
|---|---|---|
| `ai-service-runtime`, delta propia | «el recuento de páginas fallidas del **drenaje más reciente**» | **No está persistido.** Se lee de `ai.sync_failure`, acumulativo — §8.3 |
| Diseño propio, primer cableado | El planificador se importa desde `main.py` | **Rompe una invariante con test.** Arrastraba el SDK del proveedor al *app factory* — §8.1 |
| `tasks.md` 7.2 | «vaciar el checkpoint en una base de pruebas» | **No se hizo contra la base viva**, y está declarado — §9 |

Ninguna se corrigió en silencio: las tres están escritas donde se tomaron.

---

## 8. Incidencias de esta pasada

### 8.1. Un test existente cazó mi diseño, y tenía razón — **defecto mío, corregido por arquitectura**

El primer cableado importaba `jbg_ai.indexing.scheduler` desde `api/main.py`. Dos tests fallaron:

```
FAILED tests/indexing/test_embeddings.py::test_main_does_not_import_indexing
FAILED tests/indexing/test_embeddings.py::test_unit_suite_makes_no_provider_calls
```

**No es una regla cosmética.** `indexing/cli.py` importa `LiteLlmEmbeddingClient`, y con él el SDK del
proveedor: la cadena `main → scheduler → cli → embeddings` habría metido maquinaria de proveedor en el
grafo de importación de un proceso cuyo trabajo es responder HTTP.

**Se arregló por arquitectura, no editando el test:**

- `indexing/pos_drain.py`, nuevo: la construcción del drenaje —feed, repositorio y lock— **sin tocar
  embeddings**, porque este drenaje no embebe nada y no necesita clave.
- `api/lifespan.py`, nuevo: el `lifespan` sale de `main.py`, que sigue sin nombrar `jbg_ai.indexing`.
- `cli.py` pasa a **delegar** en `pos_drain`, conservando `run_cli_sync_pos` para no romper llamantes.

**Y el guardián se extendió al fichero nuevo en vez de dejar el hueco abierto:**
`test_lifespan_reaches_the_drain_without_the_provider_sdk` comprueba que ni `lifespan.py` ni
`scheduler.py` importan `indexing.cli` ni `indexing.embeddings`. Sacar el `lifespan` a otro fichero
habría satisfecho la letra del test original y roto su propósito; esto lo impide.

### 8.2. Una delta mía se dejaba **cinco escenarios** — **defecto mío, encontrado al escribir este documento**

Al comprobar automáticamente el §3.1 —escenario a escenario, delta contra spec viva— apareció que mi
`## MODIFIED` de `ai-service-runtime` reproducía **tres** de los ocho escenarios del requisito. Un
`MODIFIED` **reemplaza el requisito entero**, así que sincronizar habría **borrado cinco escenarios de
la spec viva**:

```
Health reports a missing provider credential without failing
Health never calls the provider
Health degrades when the database is unreachable
Health state is cached between probes
Enriched health does not move the frozen contract
```

Los cinco restaurados **literalmente**, y la comparación vuelve a dar **0 perdidos**.

> **Lo que esto dice del método.** `openspec validate --all --strict` daba **63 passed · 0 failed**
> con los cinco escenarios ausentes, porque **valida estructura y no verdad** — la misma limitación que
> C40_FIX documentó sobre una spec bien formada y falsa. El validador no podía cazarlo. Lo cazó
> escribir este documento, y sólo porque la comparación se hizo **automática y acotada al requisito**:
> la primera versión de la comprobación comparaba ficheros enteros y daba 41 «perdidos» falsos, que es
> ruido en el que este defecto se habría escondido.

### 8.3. Mi propia spec pedía un dato que no existe — **corregido antes de implementarlo**

El requisito decía *«el recuento de páginas fallidas del drenaje más reciente»*. Al ir a implementarlo:
ese recuento vive en el `PosSyncResult` de la ejecución y **no se persiste**, así que un reinicio lo
pierde y `/health` no tiene de dónde leerlo. Se corrigió la spec —no el código— para leerlo de
**`ai.sync_failure`**, que es acumulativo, sobrevive al reinicio y **nadie leía**: una página que falló
hace meses era invisible para siempre. La razón quedó escrita dentro del propio requisito.

### 8.4. Un test mío era frágil — **reescrito**

`test_the_lock_key_is_a_documented_constant` buscaba la cadena `hashtext` en el **texto fuente** de
`drain_lock.py`… que documenta largamente **por qué no se usa `hashtext`**. Falló, y con razón.
Reescrito para afirmar contra **el SQL que realmente se ejecuta** (`:classid`, `:objid`, y `hashtext`
ausente), que es la propiedad, y deja al módulo libre de explicarse.

### 8.5. `dotnet test` sale **0 sin ejecutar un test** — **trampa documentada, confirmada, y bloqueante**

```
error MSB3027: No se pudo copiar "JoiabagurPV.Domain.dll" … Se superó el número de 10 reintentos.
El archivo se ha bloqueado por: "JoiabagurPV.API (29688)"
```

Es **exactamente** lo que `CLAUDE.md` describe: *«si algo mantiene `bin/Debug` bloqueado —un
`JoiabagurPV.API.exe` que hayas dejado corriendo lo hará—, la build falla, cero tests se ejecutan, y
`dotnet test` sigue saliendo con 0»*. Confirmado en vivo, y detectado **sólo porque se leyó la línea de
resumen** en vez del código de salida.

**No se mató el proceso**, y la decisión se declara: esa API es la que sirve el feed que necesitaban las
comprobaciones del §4, y es el entorno del desarrollador. Pararla habría impedido medir justo lo que
este change viene a medir.

*(Segunda vía a la misma trampa, ya registrada por C40_FIX: `dotnet test` desde la raíz del repo falla
con `MSB1003` y **también sale 0**. Aquí se ejecutó contra `backend/src/JoiabagurPV.sln`.)*

> **Cerrado después.** Se paró `JoiabagurPV.API` (PID 29688) y se ejecutó la suite entera contra
> `backend/src/JoiabagurPV.sln`: **1.347 · 1.299 correctas · 48 con error** en 19 m 51 s. La build pasó
> a la primera, confirmando que el bloqueo era el proceso y nada más. Comparación por nombres en §1.5.

**Consecuencia mientras duró:** la suite del backend no estuvo medida durante la implementación. Lo
que sí estaba: `dotnet build
JoiabagurPV.Application.csproj` en verde con 0 errores y 0 advertencias, y el único cambio en
`backend/` es la **adición de una propiedad anulable** a `AiHealthResponse` — no se retira ni cambia de
tipo ningún campo existente.

### 8.6. Un import muerto — **corregido**

Tras convertir `run_cli_sync_pos` en delegación, `SqlAlchemyPosProjectionRepo` quedó importado y sin
usar en `cli.py`. Detectado con una comprobación de AST, retirado, y `tests/indexing` vuelto a pasar
(**116 passed**) para confirmar que nada dependía de él.

---

## 9. Lo que esta pasada **no** verifica, dicho aquí

| | Por qué |
|---|---|
| ~~**La suite de .NET**~~ | **Cerrada.** Era la casilla que faltaba; se paró `JoiabagurPV.API` y se ejecutó la suite entera — resultado y comparación por nombres en §1.5 |
| **El drenaje completo contra la base viva** (tarea 7.2) | Habría exigido vaciar el checkpoint real y luego un `--full` de 34 páginas para restaurar el entorno del desarrollador. Cubierto por `test_the_boot_drain_does_not_force_a_full_run` y por la cobertura que C22 ya tiene de `resolve_start_cursor` con cursor ausente |
| **La tarjeta vista en el navegador** (tarea 7.4) | El contenedor `jpv-pv-jbg-ai` corre la **imagen anterior** a este change, así que no emite la sección `projection`. Cubierto por los 5 tests de la tarjeta y por el informe de salud real del §4.4 |
| **`verify.sh` ejecutado de verdad** | Requiere el entorno de demo. Se verificó la lógica leyendo el `/health` real contra el que se ejecutaría — que devuelve `shops_without_scope: 1`, o sea que **fallaría el despliegue**, que es lo correcto |
| **El intervalo de 600 s transcurrido** | Los tests cubren el bucle con `asyncio.sleep` sustituido. Nadie esperó diez minutos |
| **Comportamiento con varias instancias de `jbg-ai`** | El despliegue corre una. El lock es de base de datos y cruzaría instancias por construcción, pero **no se ha medido con dos** |
| **La línea base limpia de `ai-service`** | Derivada, no medida. Razón y aritmética en §1.1 |
| **Los nombres de la línea base del frontend** | Perdidos por capturar con `tail`. Razón en §1.3 |

> **Sello del 2026-09-27, puesto por C43 (`add-shop-activity-projection`) — la fila de
> `verify.sh` se equivocaba en el juicio, no en el dato.** La fila dice que `/health` devolvía
> `shops_without_scope: 1` «o sea que **fallaría el despliegue**, que es lo correcto». Lo
> primero era cierto y sigue siéndolo; **lo segundo no**. Ese `1` es
> `cd9bfd1f-f1b2-4795-9d14-867a75c18f90` = `HT-ARTRUTX` / «Hotel Cap d'Artrutx», **cerrada a
> propósito** desde el mundo sintético de C10 —`is_active: false`, `closed_after: 2025-09-30`,
> `operator: null`— y la única de las doce. Sus 144 filas conservan la asignación retirada, que
> es exactamente lo que debe pasarle al surtido de una tienda que cerró. El despliegue
> `36322635852` del 2026-09-27 **falló por esta única causa con el entorno sano**, y el falso
> positivo llegaba también en rojo a la tarjeta del administrador.
>
> La predicción de esta fila era, pues, correcta como predicción —el despliegue efectivamente
> falló— y equivocada como valoración. **No se reescribe: la casa conserva las fichas
> archivadas como registro.** Lo que C41 no podía saber es que el recuento no tenía forma de
> distinguir una tienda cerrada de una rota, porque el rol `jbg_ai` recibe `permission denied
> for table PointOfSales` — de modo que la decisión D9 / Q-5 de este mismo change estaba
> **impuesta por los permisos** y no sólo elegida. C43 lleva la actividad al esquema `ai` por
> un *feed* propio y cuenta contra las tiendas **activas**.

---

## 10. Estado final

| | |
|---|---|
| Tareas | **32 / 32** |
| Artefactos OpenSpec | **4 / 4** — `proposal`, `design`, `specs`, `tasks` |
| `openspec validate --all --strict` | **63 passed · 0 failed** |
| `ai-service` | **1.649 passed · 0 failed** (+24) |
| Frontend, área propia | **9 / 9**; no aparece en ninguna de las tres listas de rojos |
| Backend | **1.347 · 1.299 correctas · 48 con error** · 9 nombres discrepantes, **8 en la clase inestable documentada** · **área propia 7/7** |
| Contrato congelado | **sin mover**, `sha256` idéntico |
| Migraciones | **ninguna** |
| Coste de proveedor | **cero** |
| Defectos encontrados y corregidos en esta pasada | **4 míos** (§8.1, §8.2, §8.3, §8.4) más **1 import muerto** (§8.6) |
| Hallazgos que no son de este change | **1**: un punto de venta real sin surtido proyectado, invisible hasta ahora (§4.4) |
| Commit | **ninguno** — el árbol queda sin commitear, según lo pedido |
