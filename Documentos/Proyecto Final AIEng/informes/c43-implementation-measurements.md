# C43 · `add-shop-activity-projection` — mediciones de la implementación

**Fecha:** 2026-09-27 · **Rama:** `c43-add-shop-activity-projection`, abierta sobre `ai-eng` en el
merge de la PR #48 (`cd285f1`) · **Estado de `demo` al abrir y al cerrar:** `2b357a1e`, **sin tocar**.

Este informe recoge lo medido, no lo heredado. Las cifras de partida del *brief* se **reprodujeron**
antes de darlas por buenas, y una de ellas resultó imprecisa (§6).

---

## 1 · Líneas base, medidas en serie

Las tres suites **nunca en paralelo**: `vitest` con 14 *workers* satura la máquina y
*testcontainers* pierde la tubería de Docker, lo que da cientos de rojos que no son del código.
Se leyó **la línea de resumen** en las tres, no el código de salida.

| Suite | Resultado | Esperado según `CLAUDE.md` |
|---|---|---|
| Backend (`dotnet test`) | **49 con error · 1.359 superadas · 1.408 total** | ~48-50 de 1.408 ✔ |
| Frontend (`npm run test`) | **113 fallidos · 846 pasados · 959 total**, en **14 de 63** ficheros | 113 de 959 en 14 de 63 ✔ |
| `ai-service` (`uv run pytest`) | **1.664 pasados · 0 fallidos** | limpia ✔ |

Los 49 nombres del backend y los 113 del frontend se guardaron para comparar al cierre. Reparto del
backend por clase, con la rotación documentada presente:

```text
8 InventoryIntegrationTests      5 ProductsControllerTests      5 ImageCompressionServiceTests
4 SalesControllerTests           4 ReturnsControllerTests       4 RepositoryTests
3 PointOfSalesControllerTests    3 EmbeddingEndpointsTests      2 RateLimitingTests
2 QrCodeServiceTests             2 InventoryServiceTests        2 AuthorizationTests
1 UsersControllerTests           1 SalesReportControllerTests    1 PaymentMethodsControllerTests
1 ImageRecognitionControllerTests 1 ExcelImportServiceTests
```

**Y la primera medición fue falsa, por la trampa que `CLAUDE.md` describe.** El primer
`dotnet test` se lanzó contra `backend/JoiabagurPV.sln`, que no existe —la solución está en
`backend/src/`—, y **salió con código 0**:

```text
MSBUILD : error MSB1009: El archivo de proyecto no existe.
Modificador: backend/JoiabagurPV.sln
```

Cero pruebas ejecutadas, cero como código de salida. Es exactamente el modo de fallo que el
repositorio documenta —«mide la línea de resumen, no el código de salida»— y se detectó por no
haber otra línea de resumen que leer.

`ai-service` **parte limpia**, lo que hace que la comparación al cierre sea trivial: cualquier rojo
allí es mío.

---

## 2 · El defecto, reproducido contra la base **desplegada**

No se dio por bueno el experimento del *brief*. Corrido por SSM el 2026-09-27 contra
`jbg-demo-postgres`:

```text
=== recuento VIEJO (sin filtro de actividad) ===
12|11|1                        points_of_sale=12  scoped=11  shops_without_scope=1  -> FALLA

=== actividad real en public (como superusuario) ===
12|11                          doce puntos de venta, once activos

=== recuento NUEVO (tiendas a la izquierda, NOT EXISTS) ===
11|0                           active=11  active_without_scope=0                    -> PASA

=== la tienda señalada ===
HT-ARTRUTX|Hotel Cap d'Artrutx|f
```

**Confirmado en los tres puntos**: el recuento antiguo da 1, el nuevo da 0, y la tienda señalada es
la cerrada a propósito. El *brief* acertaba.

Y el mismo sondeo confirmó las otras dos cifras de partida:

```text
=== ai.sync_failure por feed ===
catalog|66                     las 66 filas que nadie contaba, ninguna de pos-availability

=== checkpoint de pos-availability ===
pos-availability|2026-09-22 18:22:29|2026-09-27 18:13:08
                 ^ el completo, parado    ^ el incremental, al día
```

---

## 3 · El mecanismo, medido de punta a punta en local

Con el API de .NET sirviendo el *feed* nuevo contra la base de desarrollo:

```text
1. feed       GET /api/ai/index-feed/pos-shops
              sin clave -> 401
              con clave -> 12 items, la única isActive:false es
                           cd9bfd1f-f1b2-4795-9d14-867a75c18f90  (HT-ARTRUTX)
              computedAsOf: 2026-08-23T23:59:59Z

2. drenaje    python -m jbg_ai.indexing sync-pos-shops
              pos-shops written=12 removed=0 active=11

3. recuento   viejo:  points_of_sale=12  scoped=11  shops_without_scope=1   -> FALLA
              nuevo:  active_points_of_sale=11      active_without_scope=0  -> PASA

4. informe    el que construye SqlAlchemyHealthProbe contra la base real:
              { "active_points_of_sale": 11,
                "shops_without_scope": 0,          <- el falso positivo, ido
                "points_of_sale": 12,              <- sin cambiar
                "failed_pages": 0,
                "failed_pages_by_feed": {"catalog": 9} }

5. condición  ejecutando el BLOQUE REAL extraído de deploy/demo/verify.sh
              contra ese informe real: sin fallos -> la quinta condición PASA
```

El paso 5 no simula la lógica: **lee el bloque del propio guión** con una expresión regular y lo
ejecuta, así que no puede divergir de lo que se desplegará.

---

## 4 · Los trece casos de la quinta condición

Mismo método —el bloque real del guión, extraído y ejecutado— contra cuerpos de `/health`
sintéticos, uno por caso. Herramienta en
`openspec/changes/add-shop-activity-projection/verify-fifth-condition.py`.

| Caso | Esperado | Resultado |
|---|---|---|
| Tienda cerrada a propósito *(el falso positivo del 2026-09-27)* | **pasa** | ✔ |
| Tienda **activa** sin surtido | falla | ✔ |
| `ai.pos_shop` vacía | **falla** *(no pasa en vacío)* | ✔ |
| Sección de proyección ilegible | falla | ✔ |
| Proyección nunca drenada | falla | ✔ |
| Proyección vacía | falla | ✔ |
| Imagen anterior a C43 *(sin `active_points_of_sale`)* | **no falla** *(desfase de versión)* | ✔ |
| Imagen anterior a C41 *(sin sección alguna)* | no falla | ✔ |
| `drains_have_run` · drenado con once activas | no espera | ✔ |
| `drains_have_run` · `never_drained` | espera | ✔ |
| `drains_have_run` · cero activas | espera | ✔ |
| `drains_have_run` · imagen anterior a C43 | no espera | ✔ |
| `drains_have_run` · sin sección | no espera | ✔ |

La tercera fila es la que impide que este change introduzca **la cuarta instancia** de la familia
de defectos que cierra: índice vacío (C34), proyección vacía (C41), corpus vacío (C39a) — y una
tabla de tiendas vacía habría sido la cuarta, introducida precisamente por el arreglo de la tercera.

---

## 5 · Higiene: el drenaje completo y la deriva

Corrido contra el entorno desplegado, que es lo que la tarea pedía y **nadie había hecho nunca**:

```text
=== ANTES ===
pos-availability | full: 2026-09-22 18:22:29 | incr: 2026-09-27 18:13:08 | hash 3c239b0001ed2aeb | 6720 filas

=== DRENAJE COMPLETO ===
upserted=6050 soft_deleted=670 pages=34 failed_pages=0 computed_as_of=2026-08-23T23:59:59+00:00

=== DESPUÉS ===
pos-availability | full: 2026-09-27 18:21:48 | incr: 2026-09-27 18:21:48 | hash 3c239b0001ed2aeb | 6720 filas
```

**Deriva cero, y por tres vías que concuerdan:**

1. El `last_aggregate_hash` es **idéntico** antes y después (`3c239b0001ed2aeb…`), sobre una
   relectura completa del *feed*.
2. El recuento de filas no se movió: **6.720** antes y después.
3. La aritmética cuadra exactamente: **6050 + 670 = 6720**, o sea que toda fila existente fue
   reescrita y el conjunto es el mismo.

Y `last_full_sync_at` deja de estar parado desde el 22 de septiembre.

---

## 6 · Una imprecisión del encargo, corregida

El encargo pedía «confirmar `drift_count = 0`» tras el drenaje completo. **`drift_count` no existe
para `pos-availability`**: es un campo de `CatalogStatusResult` en `indexing/orchestrator.py`, lo
calcula `report_index_status` y es una noción **del catálogo**. El *feed* de la proyección guarda
`last_aggregate_hash` en su *checkpoint* pero nada deriva de él un número de deriva.

Lo que se midió es el equivalente exacto para este *feed*, y es más fuerte que un contador: el
digesto agregado que el lado .NET calcula sobre el conjunto global de pares asignados, comparado
antes y después de una relectura completa. Iguales ⇒ sin deriva. Es la misma prueba que
`report_index_status` aplica al catálogo (`local_hash == page.aggregate_hash → drift = 0`), sólo que
aquí se aplica a mano porque no hay función que la envuelva.

---

## 7 · Estado de las suites al cierre, comparado **por nombre**

| Suite | Línea base | Al cierre | Veredicto |
|---|---|---|---|
| `ai-service` | 1.664 pasados · **0** fallidos | **1.687 pasados · 0 fallidos** | +23 tests, cero rojos |
| Backend | **49** con error de 1.408 | **49** con error de **1.415** | +7 tests, mismo recuento |
| Frontend | **113** de 959, 14 de 63 ficheros | **114** de 959, **14** de 63 ficheros | +1 nombre, rotación conocida |
| `tsc --noEmit` | — | 176 errores, **ninguno** en ficheros de este change | plantilla de Metronic |

**El recuento no es la prueba; los nombres sí.** Comparados uno a uno:

### Backend — seis aparecen, seis desaparecen, y el área propia está limpia

| | |
|---|---|
| Aparecen | 5 de `InventoryIntegrationTests` + `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct` |
| Desaparecen | 6 de `InventoryIntegrationTests` |
| Reparto por clase | sin cambios salvo `InventoryIntegrationTests` **8 → 7** y `ProductsControllerTests` **5 → 6** |
| **Área propia (`AiIndexFeed*`)** | **cero nombres en rojo**; las 30 pruebas de las cuatro clases pasan |

`InventoryIntegrationTests` es una de las tres clases cuya rotación `CLAUDE.md` documenta.
`ProductsControllerTests` **no** lo es, así que se comprobó en lugar de suponerse:
`Update_WithValidData_ShouldReturnUpdatedProduct` **pasa cuando se ejecuta sola**
(`Con error: 0, Superado: 1`), o sea dependencia de orden y no regresión. Es coherente con la
causa: añadir `AiIndexFeedShopsTests` a `IntegrationTestCollection` cambia el orden de ejecución
de una colección que comparte base de datos.

### Frontend — un nombre más, en un fichero que ya estaba rojo, en un árbol que no se toca

| | |
|---|---|
| Aparece | `should reject files exceeding size limit (5MB)`, en `src/pages/products/components/product-photo-upload.test.tsx` |
| Desaparece | ninguno |
| Ese fichero en la línea base | **ya estaba en rojo** — es uno de los 14 |
| Ficheros de `frontend/` tocados por este change | **ninguno**, comprobado con `git diff --stat ai-eng...HEAD -- frontend/` |

Es exactamente el 113-o-114 que `CLAUDE.md` describe, y la comprobación decisiva es la última fila:
este change no tiene ni un fichero en ese árbol, así que no puede ser suyo.

### Cuatro rojos que sí fueron míos, y se arreglaron

Cuatro rojos aparecieron durante la implementación y **los cuatro eran míos**, ninguno una
regresión ajena:

- Tres de `test_health_report.py` que construían el doble con
  `projection_scoped_points_of_sale`, el campo que el nuevo modelo sustituye.
- `test_c24_schema.py::test_upgrade_downgrade_is_reversible_and_leaves_no_trace`, que **subía a
  `head`** y por tanto afirmaba, sin pretenderlo, que ninguna revisión posterior a C24 añade una
  tabla. La primera que lo hizo —`ai.pos_shop`— lo destapó. Se fijó el test a `C24`, que es lo que
  siempre quiso decir: que *sus* tres tablas van y vienen sin dejar rastro.

---

## 8 · Lo que este change **no** verifica, dicho aquí

| | Por qué |
|---|---|
| **La quinta condición en un despliegue real** | Es el despliegue, y ocurre **después** de archivar. La verificación de extremo a extremo exige mergear `ai-eng` → `demo`, que es la decisión que este change deja al responsable. La recoge **C39b** |
| **Que el panel deje de pintar la línea roja** | Mismo motivo: el contenedor desplegado corre la **imagen anterior** a este change. Medido el 2026-09-27, el `/health` desplegado sigue diciendo `shops_without_scope: 1` y **no trae `active_points_of_sale`** — que es exactamente el caso de desfase de versión que la condición tolera |
| **El drenaje de tiendas contra el entorno desplegado** | La imagen desplegada no lo tiene. Medido contra el *feed* y la base **locales**, con el API de .NET sirviendo de verdad |
| **`verify.sh` ejecutado entero en el anfitrión** | Requiere la imagen nueva. Lo que sí se ejecutó es **su bloque real** contra informes reales y sintéticos (§3 y §4) |
| **El intervalo de 600 s transcurrido** | Los tests cubren el bucle con `asyncio.sleep` sustituido. Nadie esperó diez minutos |
| **Dos drenajes de tiendas concurrentes** | Este drenaje **no toma lock** a propósito: no tiene cursor que interleavar, así que dos pasadas escriben el mismo retrato. Razonado en `pos_shop_drain.py`, no medido con dos procesos |

---

## 9 · El despliegue, y el defecto que encontró — **añadido el 2026-09-27 tras mergear a `demo`**

El §8 decía que la confirmación de extremo a extremo no era de este change. Ocurrió el mismo día, y
**encontró un defecto de C43**. Se recoge aquí porque el hallazgo es de esta implementación.

**Despliegue `36343020047`** sobre `cd8d6c3`. Construyó las dos imágenes, las publicó, actualizó
`IMAGE_TAG`, desplegó — y **falló en la verificación**:

```text
[verify] waited 180s for the start-up drains to report
"active_points_of_sale": 0,
"shops_without_scope": null,
"synced_at": "2026-09-27T19:07:08.851185+00:00"     <- la proyección SÍ se drenó
[verify] FAILED:
  - the AI service knows of no active point of sale; ai.pos_shop is empty, so the count of
    shops without assortment is vacuous and proves nothing about this environment
```

**La condición (a) hizo exactamente su trabajo.** Es la que C43 añadió para que una tabla vacía no
pasara en vacío, y lo primero que cazó fue un fallo del propio C43.

**La causa, del registro del contenedor:**

```text
19:07:07,442  boot_drain attempt=1
19:07:07,644  WARNING pos_shop_scheduler feed_not_configured error=POS shops feed is unavailable
19:07:08,857  pos_sync_scheduler drained pages=1 upserted=1 soft_deleted=0 failed_pages=0
```

El drenaje de tiendas falló **por 1,2 segundos** —el lado .NET aún no servía el *feed*—, el de
disponibilidad salió bien un segundo después, y `_boot_drain` reintentaba mientras `drain_pass(...)`
devolviera `None` — **devolviendo el resultado del de disponibilidad**. Uno de los dos bastó para
terminar el bucle de los dos. No hubo intento 2.

**Es la misma familia de defectos que C43 cierra, un nivel más arriba:** *parte del trabajo salió
bien* leído como *el trabajo salió bien*.

**Por qué los tests no lo cazaron:** `test_the_boot_drain_runs_a_whole_pass` da por buenos los dos
drenajes, así que nunca ejercitó el caso mixto. Y la spec no lo pedía: decía que los dos drenajes
corren al arrancar y en orden, pero no que el **reintento** cubriera a los dos.

**El entorno se curó solo**, lo que confirma que el mecanismo está bien y que sólo falla el arranque:

```text
19:17:08,912  pos_shop_scheduler drained written=12 removed=0 active=11
```

y el informe pasó a `active_points_of_sale: 11`, `shops_without_scope: 0`, `points_of_sale: 12`,
`failed_pages_by_feed: {"catalog": 66}`. **El falso positivo original está resuelto**; lo que quedó
pendiente es que el arranque no deje la tabla a medias.

Arreglado en `fix-boot-drain-retries-both-drains`: el reintento pasa a ser **por drenaje**, con tres
tests nuevos —uno reproduce literalmente esta secuencia— y el escenario que le faltaba a la spec.

**Dos cosas que este episodio deja dichas:**

1. **La condición (a) se pagó sola el día que entró.** Sin ella el despliegue habría concluido
   `success` con `ai.pos_shop` vacía, `shops_without_scope: null` en la tarjeta y nadie mirando.
2. **La verificación de extremo a extremo no era una formalidad.** Tres suites verdes, trece casos de
   la quinta condición y el bloque real ejecutado contra informes reales no encontraron esto, porque
   ninguno reproducía la carrera de arranque entre dos contenedores.

---

## 10 · Referencias

- Hallazgo de partida: `Documentos/Proyecto Final AIEng/informes/c39a-bis-implementation-measurements.md`
- Fichas diferidas cerradas: las dos primeras de C39a-bis en `openspec/DEFERRED_TASKS.md`
- Sello sobre la valoración de C41:
  `openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/qa.md`, §9
- Artefactos del change: `openspec/changes/add-shop-activity-projection/`
