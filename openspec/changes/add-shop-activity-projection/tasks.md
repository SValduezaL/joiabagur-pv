## 0. Líneas base, antes de tocar nada

- [x] 0.1 Medir la línea base de las **tres suites en serie**, nunca en paralelo, y **guardar los nombres** de los fallos, no sólo el recuento: `dotnet test` (esperado ~48-50 de 1.408, rotación confinada a `InventoryIntegrationTests`, `ReturnsControllerTests` y `PaymentMethodsControllerTests`), `npm run test` en `frontend/` (esperado 113 de 959 en 14 de 63 ficheros) y `uv run pytest` en `ai-service/`. **Leer la línea de resumen** —en esta máquina el de .NET dice «Con error: N»—, porque `vitest` sale 0 al canalizarse y `dotnet test` sale 0 si la compilación falló por un `.exe` que bloquea `bin/Debug`. *Validación: los tres resúmenes y los nombres, escritos en el informe del change.*
- [x] 0.2 Confirmar la cabeza de Alembic (`d7c4e91b25a0`) y que `ai-service/openapi.json` está limpio en el árbol, para poder afirmar al cierre que no se movió. *Validación: `alembic heads` y `git status` limpios.*

## 1. La tabla `ai.pos_shop`

- [x] 1.1 Escribir la revisión de Alembic **aditiva** sobre `d7c4e91b25a0`: `ai.pos_shop` con `pos_id` (clave primaria), `is_active` y `refreshed_at`. Hecha a mano, **sin autogenerar** —el árbol tiene índices HNSW/GIN y columnas generadas que el autogenerado reescribiría—, con un `downgrade` que la elimina sin dejar rastro y sin crear ningún tipo enumerado. *Validación: `alembic upgrade head` y `alembic downgrade -1` contra un contenedor limpio, ida y vuelta.*
- [x] 1.2 Repositorio de `ai.pos_shop` en `ai-service/src/jbg_ai/indexing/`, siguiendo el patrón de `pos_projection.py` — SQLAlchemy Core, sin clase mapeada, protocolo inyectable. Expone el reemplazo completo del retrato **en una sola transacción**: inserta o actualiza lo presente y borra lo ausente. *Validación: test que comprueba que una fila ausente del retrato desaparece y que un fallo a mitad deja la tabla como estaba.*

## 2. El *endpoint* de *feed* en .NET

- [x] 2.1 DTO del retrato en `IndexFeedDtos.cs`: un ítem por tienda con `pointOfSaleId` e `isActive`, y la página con su `computedAsOf`. **Sin cursor, sin `hasMore`, sin `pageSize`** — no deriva de `IndexFeedPageDto`, porque heredar su forma añadiría tres campos permanentemente nulos a un contrato que no los usa. *Validación: compila y el nombre de los campos en el JSON serializado es el camelCase que Python espera.*
- [x] 2.2 Lectura en `IndexFeedRepository` + `IIndexFeedRepository`: todas las tiendas de `PointOfSales` con su `IsActive`, ordenadas por identificador. **Es el `join` que el *feed* de disponibilidad no tiene**, y no se toca `GetPosPageAsync`. *Validación: test de integración que devuelve las doce y marca la inactiva.*
- [x] 2.3 Método en `IndexFeedService` + `IIndexFeedService` y ruta `GET /api/ai/index-feed/pos-shops` en `AiIndexFeedController`, bajo el mismo `[IndexFeedKey]`. *Validación: test de integración `GetPosShops_WithoutFeedKey_ReturnsUnauthorized` y `GetPosShops_WithFeedKey_ReturnsEveryPointOfSale`, siguiendo `AiIndexFeedAuthTests` y `AiIndexFeedPosTests`.*
- [x] 2.4 Test de integración que fija la **no regresión del *feed* de disponibilidad**: cursor, tamaño de página doscientos y `aggregateHash` idénticos a antes del change. *Validación: el test pasa y `AiIndexFeedPosTests` sigue verde por nombre.*

## 3. El drenaje de tiendas en Python

- [x] 3.1 Cliente tipado del *feed* nuevo en `feed.py`: `fetch_pos_shops_page`, parseo tolerante con `dict.get` como el resto, y su ítem. Sin cursor y sin *keyset*. *Validación: tests de parseo, incluido un cuerpo con campos desconocidos y otro sin `isActive`.*
- [x] 3.2 Drenaje en `indexing/` —módulo propio, al modo de `pos_drain.py`— que lee el retrato completo y lo aplica con el repositorio de 1.2. **No embebe nada y no construye ningún cliente de proveedor**, que es lo que permite alcanzarlo desde el proceso que responde HTTP. *Validación: test que verifica que se completa sin ninguna credencial configurada y que no abre socket hacia ningún proveedor.*
- [x] 3.3 Engancharlo al planificador de C41: misma `lifespan`, mismo intervalo, mismas tres condiciones de `scheduler_should_run`, mismo reintento de arranque, y **antes** del drenaje de disponibilidad en cada pasada. Un fallo de uno no impide intentar el otro y **ninguno levanta excepción fuera de la tarea**. *Validación: tests del orden dentro de una pasada, del fallo aislado y de que `GET /health` responde durante el arranque.*
- [x] 3.4 Alcanzarlo también desde la línea de órdenes, junto a `sync-pos`, para poder repararlo a mano — que es como se reparó cada incidente registrado de proyección rancia. *Validación: el comando corre contra el compose local y llena la tabla.*

## 4. El recuento en el informe de salud

- [x] 4.1 Sustituir `_PROJECTION_SHOPS_SQL` por la lectura con las **tiendas a la izquierda** y `NOT EXISTS`, en la **misma sesión** que el resto del informe para que siga costando una conexión. Publica `active_points_of_sale` y `shops_without_scope`; este último **`null`** cuando `ai.pos_shop` está vacía, nunca `0`. *Validación: tests de `build_projection_section` con tienda inactiva sin surtido (no cuenta), tienda activa sin surtido (cuenta), **tienda activa ausente por completo de la proyección** (cuenta) y **tabla vacía** (`null`).*
- [x] 4.2 `failed_pages` desglosado **por *feed***, conservando el escalar actual del *feed* de la proyección para no mover la lectura de `verify.sh` ni la de la tarjeta. Hace visibles las 66 filas de `catalog`. *Validación: test con fallos de `catalog` y ninguno de `pos-availability`.*
- [ ] 4.3 Comprobar que **no se movió el contrato**: `test_openapi_snapshot_is_stable` pasa sin regenerar, no hay ruta nueva bajo `/v1`, el anotado de retorno sigue siendo un *mapping* abierto, y **ni el DTO de .NET ni el frontend se tocan** — el `null` viaja limpio por `int?` → `number | null` → `?? 0`. *Validación: el test del snapshot verde y `git status` sin cambios en `backend/` ni `frontend/` por este grupo.*

## 5. La quinta condición de `verify.sh`

- [ ] 5.1 Reescribir el bloque: **(a)** falla si `active_points_of_sale` está presente y es 0 —«el servicio no conoce ninguna tienda activa»—; **(b)** falla si `shops_without_scope > 0`, nombrándolas **activas**. Conservar la tolerancia con una imagen anterior que **omita** la sección entera, que es desfase de versión y no un entorno vacío. *Validación: el guión canalizado contra cuerpos de `/health` sintéticos, uno por caso, incluido el de la imagen vieja.*
- [ ] 5.2 Añadir la **espera acotada**: reintentar la sonda hasta que el informe declare los dos drenajes hechos, con techo de tiempo, y sólo entonces evaluar las condiciones. Arregla de paso la rancidez caducada que el despliegue registra por el caché de 10 s. *Validación: se ejercita contra el compose local arrancando la pila y lanzando `verify.sh` inmediatamente; la sonda espera en lugar de fallar.*
- [ ] 5.3 Actualizar la cabecera del guión: la quinta condición pasa a hablar de tiendas activas, y se nombra **esta** como la cuarta instancia de la familia —C34, C41, C39a— para que el índice quede en el sitio donde se lee. *Validación: lectura de la cabecera; las siete condiciones siguen siendo siete.*
- [ ] 5.4 Prueba completa contra el **compose local**: levantar la pila, aplicar la revisión, dejar drenar y correr `verify.sh` entero. *Validación: sale 0 y la quinta condición imprime cero tiendas activas sin surtido.*

## 6. Higiene del entorno desplegado

- [ ] 6.1 Redrenaje completo de `pos-availability` con `python -m jbg_ai.indexing sync-pos --full` —**no necesita clave de proveedor**— y **confirmar `drift_count = 0`**. Motivo: `last_full_sync_at` sigue en `2026-09-22T18:22:29` mientras el incremental avanza cada 600 s, y nadie ha comprobado nunca la deriva contra este entorno. *Validación: la cifra de deriva y el `last_full_sync_at` nuevo, anotados.*
- [ ] 6.2 Reproducir contra la base desplegada el experimento que abre el change —`sin filtro 12/11/1` frente a `con filtro 11/11/0`— **sin darlo por bueno**, y dejar la medición escrita. Recordar `MSYS_NO_PATHCONV=1` y quitar la `-i` de `docker exec` en guiones canalizados. *Validación: las dos cifras, con la fecha.*

## 7. Registro

- [ ] 7.1 Nota **fechada** en el `qa.md` archivado de C41 (`openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/qa.md`, §9), donde escribió que este mismo `shops_without_scope: 1` «fallaría el despliegue, que es lo correcto». **Se anota, no se reescribe**: la casa conserva las fichas archivadas como registro y les pone el sello en el sitio. *Validación: la nota cita la línea original y la fecha de hoy.*
- [ ] 7.2 Cerrar en `openspec/DEFERRED_TASKS.md` las **dos** entradas de C39a-bis que este change arregla —la quinta condición y la rancidez falsa—, tachándolas con la marca de cerrada como se hizo con las de C34 y C22. **No se cierran** la de `ai.sync_failure` del catálogo (se matiza: el informe ya la publica, falta decidir la purga) ni la del modelo de reconocimiento de imagen, que es de C39b. *Validación: las dos entradas marcadas y las otras dos intactas.*
- [ ] 7.3 Actualizar la documentación de contexto que el apply deje desactualizada: `Documentos/epicas.md` (EP14 y el recuento de changes), el plan del Proyecto Final, `deploy/demo/README.md` si la espera de `verify.sh` cambia el *runbook*, y `ai-service/README.md` si aparece un comando nuevo. *Validación: `/update-docs` o revisión manual de los cuatro.*
- [ ] 7.4 Escribir el informe de mediciones del change en `Documentos/Proyecto Final AIEng/informes/`, con las líneas base de 0.1, el experimento de 6.2 y la deriva de 6.1. *Validación: el informe existe y sus cifras son las medidas, no las heredadas del brief.*

## 8. Puerta de salida

- [ ] 8.1 Las **tres suites en serie** otra vez, comparando **por nombre** contra 0.1. Criterio: **cero nombres nuevos en el área propia**; un nombre nuevo en las clases de rotación conocida no es regresión. *Validación: la comparación por nombres, escrita.*
- [ ] 8.2 `tsc --noEmit` filtrado a ficheros propios — aunque este change no toca el frontend, se corre para dejar constancia de que no lo toca. *Validación: cero errores fuera de la plantilla de Metronic.*
- [ ] 8.3 **`openspec validate --all --strict` con `0 failed`**, corrido **antes de archivar** y no sólo la forma de un solo change: un change puede estar verde mientras las specs vivas en las que sincroniza están rotas. *Validación: la línea de resumen dice `0 failed`.*
- [ ] 8.4 Archivar, abrir la PR a **`ai-eng`** y mergear. **`demo` no se toca**, y aquí **se para y se dice**: el merge `ai-eng` → `demo` es el que despliega y lo decide el responsable. La confirmación de que la ejecución concluye `success` y de que el panel ya no pinta la línea roja **la recoge C39b** — no se abre un C43-bis. *Validación: PR mergeada a `ai-eng` y `origin/demo` intacta en `2b357a1e`.*
