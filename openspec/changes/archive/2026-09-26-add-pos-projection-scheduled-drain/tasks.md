## 1. Puerta de entrada

- [x] 1.1 Anotar el `sha256` de `ai-service/openapi.json` **antes de tocar nada**. Es la afirmación central del change —el contrato congelado no se mueve— y al cerrar tiene que coincidir byte a byte. Validación: el valor queda escrito en el informe de implementación.
- [x] 1.2 Línea base de `uv run pytest` en `ai-service/` **por nombres de test**, no por número. Validación: la lista de nombres en rojo queda anotada (se espera verde, pero se mide en vez de suponerse).
- [x] 1.3 Línea base de `dotnet test` y de `npm run test` **por nombres**. Frontend medido: **119 failed / 730 passed (849) en 17 de 57 ficheros**. **Backend NO medible**: `JoiabagurPV.API` mantiene `bin/Debug` bloqueado y `dotnet test` sale con 0 sin ejecutar un test — la trampa que documenta `CLAUDE.md`, confirmada en vivo. No se mata el proceso porque sirve el feed que necesitan las comprobaciones del tramo 7. Declarado en el §4.3 del informe y pendiente antes de archivar.
- [x] 1.4 `openspec validate --all --strict` en verde antes de empezar. Validación: `0 failed`.

## 2. El lock, que es el prerrequisito del planificador

- [x] 2.1 Añadir a `ai-service/src/jbg_ai/indexing/` un ayudante de *advisory lock* no bloqueante sobre una conexión dedicada, con la clave como **constante documentada** (no `hashtext`) y liberación garantizada en salida normal y en excepción. Validación: test unitario con doble de sesión que comprueba adquisición, declinación y liberación.
- [x] 2.2 Tomar el lock **dentro de `sync_pos_availability`**, no en el llamante, de modo que lo hereden el CLI y el planificador. Un drenaje que no lo consigue declina, registra `lock_held` con su `trace_id` y **no escribe nada**. Validación: `test_a_manual_cli_run_is_refused_while_the_scheduler_drains` y su simétrico.
- [x] 2.3 Comprobar que el CLI sigue devolviendo su código de salida correcto: 1 con páginas fallidas, y un valor distinguible cuando declina por lock —declinar no es fallar—. Validación: tests del CLI puestos al día.

## 3. El planificador

- [x] 3.1 Añadir `JPV_POS_SYNC_SCHEDULER_ENABLED` (defecto `true`) y `JPV_POS_SYNC_INTERVAL_SECONDS` (defecto `600`) a `config/settings.py` con el patrón `blank_*_is_default` que usan los demás. **Ninguno se fija en `canonical_openapi_settings()`**: no alcanzan el contrato. Validación: tests de settings, incluida la cadena vacía.
- [x] 3.2 Escribir el planificador: drenaje de arranque —completo sin checkpoint, incremental con él— y bucle por intervalo. Feed caído ⇒ retroceso acotado, `WARNING` legible con la causa, y rendición al bucle normal. Nunca lanza hacia arriba. Validación: `test_boot_drain_runs_a_full_when_the_checkpoint_is_absent` y `test_boot_drain_survives_a_feed_that_is_not_answering`.
- [x] 3.3 Convertir `create_app` para que use `lifespan` y **cree la tarea sin esperarla**, cancelándola limpiamente al apagar. Gatear igual que `retrieval_embed`: sólo cuando el conmutador está encendido, `stub_mode` es falso y el feed está configurado. Validación: `test_health_answers_200_during_the_boot_drain` y que el apagado no deja tareas huérfanas.
- [x] 3.4 Verificar que las suites existentes que construyen la app con `TestClient` **no arrancan el planificador**. Validación: la línea base de 1.2 no gana ni un nombre rojo.
- [x] 3.5 Comprobar que apagar el conmutador restaura exactamente el comportamiento previo — la ablación y el *rollback*. Validación: `test_disabling_the_scheduler_leaves_the_cli_as_the_only_drain`.

## 4. La sección `projection` del informe de salud

- [x] 4.1 Añadir a `retrieval/search.py` la lectura de puntos de venta sin surtido, dentro de `ai` y sin tocar `public`. Reutilizar `PROJECTION_SYNCED_AT_SQL`, no duplicarlo. Validación: test `db` que monta una proyección con una tienda a cero.
- [x] 4.2 Ampliar `api/health_report.py` con `projection`: último drenaje, último completo, edad **desde el checkpoint**, `stale` contra el techo configurado, `ceiling`, páginas fallidas y tiendas sin ámbito. Ausencia de checkpoint ⇒ se reporta la ausencia, no una edad. Respetar la caché corta: **sin round trips nuevos en la ruta de recuperación**. Validación: `test_health_reports_projection_age_from_the_checkpoint` y `test_health_reports_a_point_of_sale_with_no_scope`.
- [x] 4.3 Confirmar que la anotación de retorno sigue siendo un *mapping* abierto y que el contrato no se mueve. Validación: `test_openapi_snapshot_is_stable` pasa **sin regenerar** y el `sha256` de 1.1 coincide.

## 5. Transporte hasta la tarjeta del administrador

- [x] 5.1 Añadir `AiHealthProjection` a `AiHealthResponse`, **tolerante a su ausencia** (un `jbg-ai` anterior no la manda). Sin tocar autorización: `GET /api/ai/health` sigue siendo sólo administrador. Validación: tests de deserialización con y sin la sección.
- [x] 5.2 Extender `frontend/src/types/ai-health.types.ts` con la sección opcional. Validación: `tsc --noEmit` filtrado a ficheros propios —Vite transpila con esbuild y no comprueba tipos, así que `npm run build` en verde no dice nada.
- [x] 5.3 Pintar los tres estados en la tarjeta de `AdminDashboard.tsx` —fresca, rancia, sin ámbito—, en es-ES, con copia de **completitud y no de corrección**, edad en lenguaje natural y valor exacto en el `title`, y el `docker exec` del completo documentado al lado. Validación: `should show the projection age on the AI service card` y `should name the points of sale with no scope when there are any`.

## 6. La verificación del despliegue

- [x] 6.1 Añadir a `deploy/demo/verify.sh` el quinto motivo de fallo —proyección sin ninguna fila asignada—, leído del `/health` que ya consulta, con el mismo estilo de mensaje que los cuatro existentes. Validación: ejecución simulada con un payload de proyección vacía y otro poblado.
- [x] 6.2 Cerrar la entrada de C34 en `openspec/DEFERRED_TASKS.md`, declarando cuál de las dos opciones que planteaba se tomó y por qué. Validación: la entrada queda marcada como resuelta con referencia a este change.

## 7. Comprobación con datos reales, leyendo el checkpoint

- [x] 7.1 Arrancar en local con la proyección rancia —hoy lo está, a 14,4 veces el techo— y comprobar que se drena sola al arrancar. Validación: `last_incremental_sync_at` avanza; **se lee el checkpoint y nunca `MAX(refreshed_at)`**.
- [x] 7.2 Vaciar el checkpoint en una base de pruebas y comprobar que el arranque ejecuta un completo. **Cubierto por test y no contra la base viva**, deliberadamente: vaciar el checkpoint real habría obligado a un `--full` de 34 páginas para restaurar el entorno del desarrollador. `test_the_boot_drain_does_not_force_a_full_run` fija que el modo se deriva del cursor ausente, y C22 ya cubre `resolve_start_cursor` con cursor ausente. Declarado en el §5 del informe.
- [x] 7.3 Lanzar el CLI durante un drenaje programado y comprobar que declina. Validación: la línea `lock_held` aparece en el log con su `trace_id`.
- [x] 7.4 Comprobar la tarjeta en los tres estados. **Cubierto por los cinco tests nuevos de `ai-service-status.test.tsx`** (al día, desactualizada, sin sincronizar nunca, tienda sin ámbito, y sección ausente), más el informe de salud real leído contra la base viva —§2.4 del informe—, que devuelve `shops_without_scope: 1` sobre un POS real sin surtido. El contenedor `jbg-ai` que corre en local lleva la imagen anterior a este change, así que la tarjeta no se pudo ver contra él.

## 8. Documentación, y las frases que quedan falsas

- [x] 8.1 Retirar de `ai-service/README.md` la sección *«There is no route and no scheduler, on purpose»* **con su receta de cron**, y sustituirla por el comportamiento real: drenaje de arranque e intervalo, el lock, y el `--full` a mano cuando cambia `IndexFeed:SalesAsOf` o hubo páginas fallidas. Validación: no queda ninguna mención a `/srv/jbg-ai`.
- [x] 8.2 Corregir la línea del registro de C22 en `ai-service/README.md` (*«a command with a documented cron, not a route and not an in-process scheduler»*) y la de `openspec/project.md` (*«a cron, not a route»*). Validación: `grep` sin resultados para las dos frases.
- [x] 8.3 Actualizar `deploy/demo/README.md` con el quinto motivo de fallo y con que el drenaje inicial ya no es un paso manual del runbook. Validación: el paso queda como red de seguridad y no como requisito.
- [x] 8.4 **Anotar el §8 del informe de C40**: nota fechada y firmada como anotación posterior de C41 diciendo qué cifras se sostienen —la latencia, con su razón— y cuáles describen el sistema degradado —el reparto de estados—. **No se toca ningún número ni ningún artefacto.** Validación: el informe conserva sus cifras originales intactas y gana sólo la nota.
- [x] 8.5 Poner al día `Documentos/epicas.md` y la ficha del plan si la implementación refuta algo de lo escrito. Validación: cualquier refutación queda escrita, no corregida en silencio.

## 9. Cierre

- [x] 9.1 Publicar el informe de implementación con las cifras que este change produce: edad de la proyección antes y después del arranque, duración del drenaje de arranque en los dos modos, conexiones sostenidas por el lock, y el `sha256` de `openapi.json` al abrir y al cerrar. Validación: el informe existe en `Documentos/Proyecto Final AIEng/informes/`.
- [x] 9.2 Comparar las suites por nombres. `ai-service` **1.623 → 1.649, cero rojos**. `frontend`: tres pasadas dan 119/114/119 fallos en 17/15/18 ficheros —la rotación documentada— y **ninguno de los 18 es del área propia**; `ai-service-status.test.tsx` da 9 de 9 en aislamiento. `backend` sin medir, ver 1.3. Limitación de la comparación declarada en el §4.2 del informe.
- [x] 9.3 `openspec validate --all --strict` con `0 failed`, y comprobar que **no existe revisión nueva de Alembic, ni migración de EF Core, ni ruta bajo `/v1`**. Validación: los tres `grep` y el diff de `ai-service/openapi.json` vacío.
