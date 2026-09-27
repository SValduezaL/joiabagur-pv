## Why

**La verificación posterior al despliegue juzga mal un entorno correcto, y lo hace en rojo.** El despliegue `36322635852` del 2026-09-27 construyó, publicó las dos imágenes, actualizó `IMAGE_TAG` y **falló** en «Verify the deployment from inside the host» con una sola causa:

```text
[verify] FAILED:
  - 1 point(s) of sale hold no assigned row in the projection; assisted search answers 503 for each of them
```

**El entorno estaba sano.** Las otras seis condiciones pasan. El punto de venta señalado es `cd9bfd1f-f1b2-4795-9d14-867a75c18f90` = `HT-ARTRUTX` / «Hotel Cap d'Artrutx», declarado inactivo **a propósito** desde el mundo sintético de C10 —`data/world/pos-profiles.yaml`, `is_active: false`, `closed_after: 2025-09-30`, `operator: null`—, y es el único de los doce. Conserva **144 filas** en `ai.pos_projection`, **todas con la asignación retirada**, que es exactamente lo que debe pasarle al surtido de una tienda que cerró. Los once activos van de **241 a 1.082** filas asignadas. El experimento, corrido contra la base desplegada:

```text
sin filtro de actividad   points_of_sale=12  scoped=11  shops_without_scope=1   -> FALLA
con filtro de actividad   points_of_sale=11  scoped=11  shops_without_scope=0   -> PASA
```

**El falso positivo no se queda en el registro del despliegue: llega a la pantalla.** `GET /api/ai/health` devuelve `shopsWithoutScope: 1` y `AdminDashboard.tsx` lo pinta en rojo como «1 tienda sin surtido sincronizado: su búsqueda asistida no funciona». Arreglar sólo `verify.sh` dejaría esa línea intacta, y por eso este change ataca el recuento y no la condición que lo lee.

**Y el arreglo no cabe donde parece.** Comprobado, no supuesto: el rol con el que corre el servicio de IA responde `permission denied for table PointOfSales`, así que ni `health_report.py` ni el bloque de `verify.sh` que se ejecuta **dentro** de `jbg-demo-ai` pueden leer la actividad de la tienda. La decisión D9 / Q-5 de C41 —contar contra lo que aparece en la proyección porque Python no lee `public`— **está impuesta por los permisos**, y hay un requisito vivo que la fija.

Van dos defectos juntos porque **el segundo es requisito previo del primero**. `deploy/demo/deploy.sh:208` corre `alembic upgrade head` **después** de levantar la pila y **antes** de `verify.sh`, así que la tabla nueva nace vacía a mitad del despliegue con el contenedor de IA ya arrancado. Si `verify.sh` sondea antes de que el drenaje la llene lee cero tiendas activas —y si la condición está mal escrita, **cero la hace pasar en vacío**, que sería la cuarta instancia de la familia de defectos que este change viene a cerrar. A eso se suma que `cached_health_report` reutiliza el informe 10 s: el 2026-09-27 el paso de verificación imprimió `"stale": true` con marca del 22 de septiembre **seis segundos después** de que el drenaje hubiera escrito el *checkpoint*, dejando en el registro permanente una cifra de 115 veces el techo que era falsa al escribirse.

## What Changes

- **`ai.pos_shop`: una fila por tienda** —`pos_id`, `is_active`, `refreshed_at`— en el esquema `ai`, poblada por el *feed* de .NET. Una revisión de Alembic **aditiva**, sobre la cabeza actual `d7c4e91b25a0`. **Sin migración de EF Core**: `PointOfSales.IsActive` ya existe.
- **Un *endpoint* de *feed* nuevo**, `GET /api/ai/index-feed/pos-shops`: doce filas, **sin cursor ni paginación**, con el `join` a `PointOfSales` que el *feed* de disponibilidad no tiene. Misma autenticación por `X-Index-Feed-Key`.
- **Un drenaje nuevo, siempre completo**, enganchado al planificador que C41 ya arranca. No embebe nada y no necesita clave de proveedor.
- **`shops_without_scope` pasa a contarse contra las tiendas activas**, con `NOT EXISTS` y las tiendas **a la izquierda** — no un `FILTER` sobre la proyección. Así detecta además **una tienda activa que no aparezca en absoluto** en la proyección, caso que hoy es invisible porque el contador sólo mira las que ya están.
- **La quinta condición de `verify.sh` lee el número nuevo y espera a que los drenajes reporten `drained` antes de sondear** (o pide un informe sin caché), y **falla con `ai.pos_shop` vacía** en lugar de pasar en vacío.
- **Higiene y registro**: redrenaje completo de `pos-availability` confirmando `drift_count = 0` —`last_full_sync_at` sigue en `2026-09-22T18:22:29` y nadie ha comprobado nunca la deriva contra este entorno—; nota fechada en el `qa.md` archivado de C41, que vio este mismo `shops_without_scope: 1` y escribió que «fallaría el despliegue, que es lo correcto» —**se anota, no se reescribe**—; y cierre de las dos entradas de C39a-bis en `DEFERRED_TASKS.md` que este change arregla.
- **Opcional y recomendado, porque es la misma línea de código**: `failed_pages` contado **por *feed***, que haría visibles las **66 filas** de `ai.sync_failure` del *feed* `catalog` que hoy nadie mira.

**No se toca el *feed* de disponibilidad**: ni su cursor, ni su `aggregateHash`, ni su contrato. Ése es el camino que funciona, y moverlo para llevar un dato de tienda sería cambiar lo que está bien por lo que falta.

**No se toca el frontend.** La línea roja del panel desaparece porque el número que la dispara pasa a ser cero, no porque se edite la plantilla. Si se editara, el panel dejaría de avisar de una tienda activa realmente rota, que es justo lo que debe seguir avisando.

**Y una vía descartada, para que no se reabra:** una columna `is_shop_active` en `ai.pos_projection` **se quedaría rancia para siempre**. El *feed* es incremental por *keyset* sobre el *watermark* de la fila de inventario, así que si una tienda cambia de estado ninguna fila de `Inventories` se toca, el *watermark* no se mueve y el incremental no reemite nada. El `aggregateHash` tampoco lo vería: se calcula sobre pares `(PointOfSaleId, ProductId)`. La otra descartada, `GRANT SELECT` a `jbg_ai`, viola el requisito vivo de `pos-projection` y cruza la frontera de esquemas que C17 dibujó adrede.

## Capabilities

### New Capabilities

Ninguna. El mecanismo cae dentro de lo que `pos-projection` ya cubre —la proyección, sus drenajes y lo que el informe de salud dice de ella—, y partirlo en una capability nueva fragmentaría en dos specs la frontera «Python no lee el esquema `public` por SQL» y el requisito del recuento, que es precisamente lo que hay que mantener leyéndose junto.

### Modified Capabilities

- `index-feed`: **una adición**. Un *endpoint* de actividad de tiendas, sin cursor y sin paginación porque su cardinalidad es el número de tiendas del negocio y no el del inventario. Es la única forma de que el dato cruce la frontera de esquemas sin aflojar ningún permiso.
- `pos-projection`: **dos adiciones y una modificación**. Se añaden `ai.pos_shop` y su drenaje completo; se modifica el requisito del recuento para contar contra tiendas **activas**. La cláusula «*counted within schema `ai` and never by reading schema `public` by SQL*» **se mantiene íntegra** y la vía B2 la respeta: la actividad entra en el esquema `ai` por el *feed*. Lo que sí cae es el párrafo que razonaba que alcanzar ese dato por el *feed* «ensancharía esta capability para un recuento» — es exactamente lo que este change decide hacer, y con un motivo que entonces no se tenía: el recuento equivocado ya ha marcado en rojo un despliegue sano.
- `ai-service-runtime`: **una modificación**. El informe de salud reporta el número de puntos de venta **activos** sin fila asignada, y publica también cuántas tiendas activas conoce, para que un consumidor pueda distinguir «cero tiendas sin surtido» de «no sé de ninguna tienda». Cabe sin coste de contrato: el anotado de retorno sigue siendo un *mapping* abierto y no se añade ninguna ruta, así que el *snapshot* de OpenAPI no se mueve.
- `demo-deployment`: **una modificación**. La quinta condición, **tal como está redactada hoy, obliga al falso positivo**: exige fallar «when the point-of-sale availability projection holds no assigned row for **any** point of sale». Pasa a hablar de puntos de venta **activos**, y gana el escenario que hoy falta — la condición **falla** cuando el servicio no conoce ninguna tienda, en lugar de pasar en vacío.

## Impact

**Código que se toca:**

- `ai-service/migrations/versions/` — una revisión aditiva sobre `d7c4e91b25a0`
- `ai-service/src/jbg_ai/indexing/` — cliente del *feed* nuevo, repositorio de `ai.pos_shop`, drenaje y enganche al planificador
- `ai-service/src/jbg_ai/api/health_report.py` — el recuento y la sección del informe
- `backend/src/JoiabagurPV.API/Controllers/AiIndexFeedController.cs`, `…/Application/DTOs/Ai/IndexFeedDtos.cs`, `…/Application/Services/IndexFeedService.cs`, `…/Application/Interfaces/IIndexFeedService.cs`, `…/Domain/Interfaces/Repositories/IIndexFeedRepository.cs`, `…/Infrastructure/Data/Repositories/IndexFeedRepository.cs`
- `deploy/demo/verify.sh` — la quinta condición y la espera al drenaje

**Documentación y registro:** `openspec/DEFERRED_TASKS.md` (dos entradas cerradas), el `qa.md` archivado de C41 (nota fechada, sin reescribir), y los documentos de contexto que el apply deje desactualizados.

**No se toca:** `frontend/src`, ningún `Dockerfile`, `compose.demo.yaml`, `deploy/demo/deploy.sh`, ninguna migración de EF Core, ninguna ruta bajo `/v1`, `ai-service/openapi.json`, ni el *feed* `pos-availability` en ninguna de sus piezas.

**La verificación de extremo a extremo es el propio despliegue, y ocurre después de archivar.** Este change se cierra sin ella: local y en CI se prueban el informe de salud con la tabla nueva —**incluido el caso de tabla vacía**—, el *endpoint* en .NET con un test de integración, y `verify.sh` contra el compose local. La confirmación de que la ejecución concluye `success` y de que el panel ya no pinta la línea roja **la recoge C39b**, que es documentación y no redespliega.
