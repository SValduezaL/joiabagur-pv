# HU-AIENG-041: La frescura de `ai.pos_projection` deja de ser un acto manual — drenaje al arrancar y por horario, con lock, y la edad dicha en la tarjeta del administrador

## Formato estándar

**Como** Administrador del sistema,
**quiero** que la proyección de disponibilidad por punto de venta se mantenga fresca sola —al levantar
el entorno y cada diez minutos—, y poder ver en la tarjeta del servicio de IA cuándo se drenó por
última vez, si está rancia y qué tiendas se han quedado sin ámbito,
**para** que ningún operario reciba páginas cortas por un dato que nadie refrescó, y para que una
medición del sistema no acabe describiendo su desconfiguración.

---

## Descripción

Change OpenSpec `add-pos-projection-scheduled-drain` / **C41**, épica **EP14 — Búsqueda Semántica
Híbrida**, que es donde nació `ai.pos_projection` con C22. Prerrequisitos: **C22** (la proyección, el
prefiltro blando y el techo de rancidez) y **C17** (el informe de salud enriquecido y la tarjeta de
estado del dashboard de administrador), los dos archivados.

> **Corrección de encaje respecto al ticket abierto el 25 sep.** Su cabecera declaraba **EP15**. Es un
> error: la capability que este change modifica es
> [`pos-projection`](../../../openspec/specs/pos-projection/spec.md), nacida en **C22**, que es de
> **EP14**. El criterio del repositorio es el que ya se aplicó a C40 — *«C40 es de EP15, aunque
> modifique la capability `assisted-search-panel` de esta épica»*—: la épica la fija **de qué trata el
> change**, no qué capability toca. C41 trata de la frescura de la proyección → EP14. Su superficie
> secundaria —`GET /health` y la tarjeta— es de **EP11**, igual que C40 tocaba una capability de EP14
> desde EP15.

**C41 no estaba en el plan.** Nace el 2026-09-25 durante las pruebas manuales posteriores al cierre de
C40: al levantar el entorno, **ninguna de las once tiendas con surtido tenía la proyección fresca**. El
checkpoint `ai.sync_checkpoint.last_incremental_sync_at` del feed `pos-availability` venía del **5 de
septiembre** —veinte días contra un techo de 3.600 s— y hubo que drenarlo a mano (`sync-pos --full`:
34 páginas, 6.050 *upserts*, 0 fallidas) para que las pruebas midieran el sistema y no su
desconfiguración.

> **La lección que gobierna la historia entera.** No es que falte un planificador: **es que el
> planificador existe y vive en prosa.** [`ai-service/README.md:330`](../../../ai-service/README.md#L330)
> lleva desde C22 una receta de cron cada diez minutos, y **es inejecutable en la topología que
> desplegamos**: empieza por `cd /srv/jbg-ai`, una ruta de host, y `jbg-ai` se despliega como
> contenedor. Por eso nadie la instaló nunca. C41 no inventa un planificador — **lo mueve de la prosa
> a algo que se despliega.**

### Lo que la rancidez hace, y lo que NO hace

La lectura intuitiva es alarmista y está equivocada. **No es una fuga.** Hay dos filtros y sólo uno es
la frontera:

| | Dónde | Qué hace | ¿Frontera? |
|---|---|---|---|
| Prefiltro de `ai.pos_projection` | [`projection.py`](../../../ai-service/src/jbg_ai/retrieval/projection.py), antes de ordenar | Estrecha la **ventana de candidatos** al surtido de la tienda | **No** |
| `Carried()` | [`AssistedSearchRepository.cs:156-162`](../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/AssistedSearchRepository.cs) | Parte de `Inventories` con `PointOfSaleId == pointOfSaleId && IsActive && Product.IsActive` | **Sí** |

La segunda corre en **toda** respuesta. Es la convención del diseño §6.2: *el servicio de IA propone
candidatos; .NET calcula números y decide.* Un operario **nunca** ve una pieza que su tienda no lleva,
pase lo que pase con la proyección.

Lo que la rancidez causa es que **la página llegue corta** — el comportamiento de antes de C22, que C22
midió: **ocho de los once puntos de venta** por debajo de una página en al menos **seis de cada
veinte** búsquedas, y en el peor caso **un solo producto superviviente**.

**Y degradar es la decisión correcta**, no un descuido: filtrar con una proyección de veinte días
escondería las piezas asignadas después del último drenaje, un **falso negativo invisible**. Mostrar
candidatos de más es recuperable porque .NET los tira; esconder algo vendible no lo es. **Esta historia
no toca esa decisión.**

### Estado actual del código, verificado en el repositorio (2026-09-26)

| Pieza | Estado | Evidencia |
|---|---|---|
| `python -m jbg_ai.indexing sync-pos [--full]`, checkpoint propio, *tombstone* en borrado suave, página fallida a `ai.sync_failure` | ✅ real desde C22, ~250 líneas comentadas y probadas | [`pos_orchestrator.py`](../../../ai-service/src/jbg_ai/indexing/pos_orchestrator.py) |
| El guard de frescura lee `ai.sync_checkpoint.last_incremental_sync_at` | ✅ y **nunca** `refreshed_at` | [`search.py:79-83`](../../../ai-service/src/jbg_ai/retrieval/search.py#L79-L83) |
| `resolve_scope` ya calcula `reported_age` y `stale` | ✅ el trabajo es **transportarlos, no computarlos** | [`projection.py:120-165`](../../../ai-service/src/jbg_ai/retrieval/projection.py#L120) |
| `ProjectionFreshness`, caché de 10 s sobre esa lectura | ✅ mismo patrón y misma razón que el informe de salud de C17 | [`projection.py:80-105`](../../../ai-service/src/jbg_ai/retrieval/projection.py#L80) |
| Receta de cron cada 10 min | ⚠️ **existe en prosa y es inejecutable**: `cd /srv/jbg-ai` es ruta de host | [`README.md:330`](../../../ai-service/README.md#L330) |
| Drenaje de la demo | ⚠️ paso manual de runbook: `docker exec -i jbg-demo-ai python -m jbg_ai.indexing sync-pos --full` | [`deploy/demo/README.md`](../../../deploy/demo/README.md) |
| `verify.sh` falla el despliegue por **cuatro** condiciones | ⚠️ **ninguna es la proyección**: un entorno con índice lleno y proyección vacía **pasa hoy** | [`verify.sh`](../../../deploy/demo/verify.sh) |
| `GET /health` declarado como *mapping* abierto en Python, y el DTO de .NET ignora campos desconocidos | ✅ **enriquecerlo no mueve el contrato congelado** | [`health_report.py`](../../../ai-service/src/jbg_ai/api/health_report.py) · [`AiHealthResponse.cs`](../../../backend/src/JoiabagurPV.Application/DTOs/Ai/AiHealthResponse.cs) |
| Tarjeta de estado de `jbg-ai` en el dashboard de administrador, con `unreachable` como resultado de primera clase | ✅ desde C17 | [`AdminDashboard.tsx`](../../../frontend/src/pages/dashboard/AdminDashboard.tsx) · [`ai-health.types.ts`](../../../frontend/src/types/ai-health.types.ts) |
| .NET escribe o lee el esquema `ai` | ❌ **cero referencias** en todo `backend/src` | — |
| La frontera `ai.*` está acotada por *grants*, no por convención | ✅ `GRANT … ON SCHEMA ai TO jbg_ai` y `ALTER DEFAULT PRIVILEGES … REVOKE` explícito | [`bootstrap.sql`](../../../ai-service/migrations/bootstrap.sql) |
| `GET /api/ai/search/availability` **no llama al servicio de IA** | ✅ **es un `MUST` de spec viva**, y además el método es **síncrono** | [`ai-free-query-search/spec.md`](../../../openspec/specs/ai-free-query-search/spec.md) |
| Superficie `/v1` enumerada en un `MUST`: 11 rutas más `/health` | ✅ añadir una es cambio normativo del contrato congelado | [`openapi.json`](../../../ai-service/openapi.json) |
| `pos-projection` prohíbe el planificador | ⚠️ *«MUST NOT start an in-process scheduler or background task»* — **es lo que este change deroga** | [`pos-projection/spec.md`](../../../openspec/specs/pos-projection/spec.md) |
| Lock de cualquier tipo sobre el drenaje | ❌ **no existe ninguno**; ni `pg_advisory_lock` ni equivalente en todo el repositorio | — |
| `uvicorn` sin `--workers`, un contenedor, `mem_limit: 512m`, pool de 5 | ✅ el planificador sería de instancia única **en la práctica**, no por garantía | [`Dockerfile`](../../../ai-service/Dockerfile) · [`compose.demo.yaml`](../../../compose.demo.yaml) |
| `JPV_POS_PROJECTION_MAX_AGE_SECONDS`, defecto **3.600** | ✅ el techo que el intervalo tiene que respetar | [`settings.py`](../../../ai-service/src/jbg_ai/config/settings.py) |

### Lo que la exploración midió, y el hallazgo que dimensiona el change

Exploración del 2026-09-26 contra el código y contra la base local. **Seis hallazgos que reencuadran el
ticket**, y uno de ellos obliga a anotar un informe ya publicado.

1. **Son tres incidentes, no dos, y dos modos de fallo distintos.** A los de C40 (19,7 días) y C41 (20
   días) se suma el de **C34 en la demo**, registrado en
   [`DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md): proyección **vacía**, `count_scope = 0`,
   **HTTP 503 en toda recuperación**, .NET degradando correctamente a léxico con 200 — *«así que desde
   fuera el entorno parece sano»*. Ese modo es **por tienda** y más grave que la rancidez, y el ticket
   no lo cubría.
2. **Los dos incidentes locales ocurrieron levantando el entorno para probar.** No en producción, no
   con el sistema corriendo: **al arrancar**. Un cron de host no corre en el portátil de nadie, y un
   temporizador de 15 minutos deja una ventana justo cuando se mide. **El disparo que mata los tres
   casos es el de arranque**, no el del intervalo.
3. **La edad no es de la tienda: es del drenaje.** El checkpoint es `PRIMARY KEY (feed)`, así que
   `resolve_scope` devuelve el mismo `reported_age` para los doce puntos de venta. Lo que sí es por
   tienda es `count_scope(pos_id)`, y su valor interesante es **cero**.
4. **El tramo 2 del ticket era el más caro de los tres, no el más barato.** Poner la edad en
   `GET /api/ai/search/availability` exige derogar un `MUST` que C40 escribió a propósito y volver
   `async` un método síncrono. **`GET /health` la lleva con coste de contrato cero** y llega a una
   tarjeta que ya existe — que es, además, el sitio que el propio ticket nombraba para el tramo 3:
   *«la pantalla de administración es donde se mira un dato de sistema»*.
5. **La manipulación de C40 se aplicó a la columna equivocada.** Está probado con cuatro piezas:

   | Evidencia | Valor |
   |---|---|
   | `ai.sync_checkpoint` · `pos-availability` | `last_incremental_sync_at` = `last_full_sync_at` = **2026-09-25 20:49:24 UTC** — los dos iguales, luego el único drenaje fue el `--full` de la sesión de C41 |
   | Artefacto del grupo 8 de C40 | `measured_at` = **2026-09-25T05:42:42.933Z**, **15 h 07 min antes** |
   | Filas con la huella del `UPDATE` manual | **94**, todas con `computed_as_of = 2026-09-25 05:32:04`, diez minutos antes de la medición |
   | «1.176 filas» del informe | Es el **total exacto de filas del POS `0388f003…`** (1.082 asignadas + esas 94) |

   El informe de C40 no menciona el *checkpoint* ni una vez, y el guard lee el *checkpoint*. **Las
   cifras del grupo 8 se tomaron con el ámbito de punto de venta caído.** Y el remate: en las 42 filas
   del artefacto `degraded_reason` es **`null` las 42 veces**, porque .NET no tiene campo para la
   degradación de la proyección — sólo para la suya. *Un dato que el sistema conoce, paga y descarta en
   la frontera.*

6. **Y el arreglo manual caduca en una hora.** Medido durante esta exploración, un día después del
   drenaje: **51.677 s de edad, 14,4 veces el techo.** El entorno volvió a estar rancio a los sesenta
   minutos y nadie lo supo en catorce horas. **Es la prueba de que el arreglo a mano no es un arreglo,
   sino un aplazamiento de una hora.**

---

### Alcance de esta historia (sí)

**Tramo 1 · El drenaje programado (el núcleo, no se corta).** Zona `ai-service/`.

- Una tarea de fondo en el `lifespan` de FastAPI que drene el feed `pos-availability` **al arrancar y
  por intervalo**, reutilizando `sync_pos_availability` tal cual — **una sola implementación del
  protocolo del keyset**, la que ya existe y está probada.
- **Al arrancar**: completo si no hay checkpoint, incremental si lo hay. Con el feed caído, registro y
  reintento acotado; **nunca** tumba el arranque ni bloquea `/health`.
- **Por intervalo**: incremental, cada **600 s** por configuración.
- **Con lock, o no se construye**: `pg_try_advisory_lock` **no bloqueante**, tomado **dentro** del
  drenaje, de modo que cubra también al CLI corrido a mano.
- `failed_pages > 0` se reporta y no se traga, heredando la lectura del CLI.

**Tramo 2a · La edad dicha donde ya hay pantalla.** Zona `ai-service/`, `backend/`, `frontend/`,
`deploy/demo/`.

- `GET /health` gana una sección `projection` con la edad tomada del **checkpoint**, el instante del
  último drenaje, el último completo, si está rancia contra el techo configurado, las páginas fallidas
  y **cuántos puntos de venta de la proyección no tienen ni una fila asignada**.
- `AiHealthResponse` y `ai-health.types.ts` la transportan; la tarjeta del dashboard de administrador
  la pinta.
- `verify.sh` gana un **quinto** motivo de fallo del despliegue: proyección vacía. Cierra la entrada
  abierta de `DEFERRED_TASKS.md`.

**Tramo 3 · Las tres frases de documentación que quedan falsas**, retiradas y no matizadas.

---

### Fuera de alcance (no)

- **La insignia del operario.** `GET /api/ai/search/availability` no se toca: su `MUST` de no llamar al
  servicio de IA se conserva intacto. Con el tramo 1 hecho, el operario no tiene que enterarse de nada.
- **El botón de drenaje manual, ni para operario ni para administrador.** Ver decisiones **D11** y
  **D12**.
- **Cualquier ruta nueva bajo `/v1`.** El contrato congelado no se mueve, y
  `test_openapi_snapshot_is_stable` tiene que seguir pasando **sin regenerar nada**.
- **La decisión de degradar** ante una proyección rancia. Es correcta y está argumentada.
- **`Carried()` y la frontera de autorización.** Se quedan donde están.
- **Migraciones.** Ni Alembic ni EF Core: `ai.pos_projection` y `ai.sync_checkpoint` existen desde C22
  y no ganan ninguna columna.
- **Re-medir el grupo 8 de C40.** Se **anota**, no se rehace. Ver **D15**.
- **Leer o reprocesar `ai.sync_failure`.** Se cuenta y se reporta; recuperarlo sigue siendo un `--full`
  a mano.
- **Las 94 filas residuales del `UPDATE` de C40.** Se declaran como prueba forense y se dejan: son
  `is_assigned_hint = false`, así que el prefiltro (`WHERE is_assigned_hint IS TRUE`) no las ve nunca.

---

### Decisiones de diseño ya acordadas

Las quince se tomaron con el desarrollador en la sesión de exploración del 2026-09-26.

| # | Decisión | Razón |
|---|---|---|
| **D1** | **El drenaje vive en `jbg-ai`**, no en un `BackgroundService` de .NET | El ticket pedía un `BackgroundService` creyendo que eso es un planificador. **No lo es: es una segunda implementación del protocolo del keyset** — precedencia de cursor, centinela `EXHAUSTED_SINCE_ID`, borrado suave, `ai.sync_failure`. Y como la spec **obliga** a conservar el CLI, quedarían **dos drenadores escribiendo la misma fila de checkpoint**: la corrupción de la que el ticket avisa, institucionalizada. Además .NET tendría que escribir `ai.*`, frontera que `bootstrap.sql` hace **estructural por *grants*** |
| **D2** | **Arranque + intervalo**, y el arranque es lo que de verdad arregla | Los tres incidentes comparten forma: *alguien levantó un entorno y se puso a probar*. Con el drenaje de arranque, **«el entorno está levantado» implica «la proyección está fresca»** — que es exactamente la invariante que faltaba |
| **D3** | **La tarea no bloquea el arranque** de FastAPI: se crea y no se espera | El `HEALTHCHECK` sondea `/health` con 3 s de tope y `compose.demo.yaml` encadena `depends_on: service_healthy`. Un completo son 34 páginas contra un presupuesto de 180 s: esperarlo marcaría el contenedor *unhealthy* y **el despliegue se caería por culpa de la mejora** |
| **D4** | **Intervalo de 600 s**, por configuración | Derivado, no elegido: lo que importa no es el intervalo sino **cuántos fallos seguidos tolera antes de que el guard degrade**. Con techo de 3.600 s, la regla `techo / intervalo ≥ 4` da ≤ 900 s; **600 s tolera cinco** y además empata con el README y con el §6.3 del diseño (*«cada 5-10 min»*), que es un empate que no cuesta nada ganar |
| **D5** | **Incremental por defecto; completo cuando no hay checkpoint** | El incremental es keyset y baratísimo. Y «completo si no hay checkpoint» **es gratis**: `resolve_start_cursor` ya devuelve `(None, None)` e `is_full` se calcula solo. Con eso, el modo de fallo de C34 —proyección vacía, 503 en todo— se cura al arrancar |
| **D6** | **`pg_try_advisory_lock`, no bloqueante, DENTRO del drenaje** | **El ticket lo ponía en el sitio equivocado.** Decía que protege del solape consigo mismo y del disparo manual del tramo 3 — y falta **el caso que de verdad ocurrió: el CLI a mano**, que es como se arregló las tres veces. Si el lock vive en el planificador, el CLI queda fuera y el riesgo declarado no se mitiga. **No bloqueante** porque encolar temporizadores es cómo se construye una estampida: el segundo drenaje declina y lo registra |
| **D7** | **Un mutex de aplicación no sirve** | Sólo protege del solape intra-proceso; no ve al CLI, que corre en otro proceso. Y un `SELECT … FOR UPDATE` sobre el checkpoint tampoco: el drenaje son 34 transacciones, no una, y sostener una abierta retendría **1 de 5 conexiones** durante minutos |
| **D8** | **La edad se dice en `GET /health`**, no en `GET /api/ai/search/availability` | El informe de salud es *mapping* abierto **en los dos lados** —C17 lo dejó así *«para que enriquecerlo no mueva el contrato congelado»*, y el DTO de .NET declara que *«an unrecognised field is ignored rather than fatal»*—. **Coste de contrato cero** y llega a una tarjeta que ya existe. La alternativa exigía derogar un `MUST` y volver `async` un método síncrono |
| **D9** | **`/health` también dice cuántas tiendas se quedaron sin ámbito** | Es el modo de fallo de C34, es **por tienda**, y es el único de los dos que produce un **503 en toda recuperación**. Hoy no lo dice nadie |
| **D10** | **`verify.sh` gana su quinto fallo** | Cinco líneas de bash contra un modo de fallo que *«pasa hoy la verificación posterior al despliegue»*, según su propia entrada de `DEFERRED_TASKS.md`. Y la demo **se va a volver a desplegar antes de la entrega**, así que se ejerce de verdad |
| **D11** | **Sin insignia para el operario** | La rancidez no le esconde piezas: sólo le llega la página corta. Enseñárselo le entregaría **un problema que no es suyo** y le invitaría a leer «no encontré mucho» como «el dato está mal» |
| **D12** | **Sin botón de drenaje manual, tampoco para el administrador** | El ticket demuele el botón del operario con *«con el tramo 1 hecho, no tiene caso de uso»* — y **el mismo argumento aplica al del administrador**: con arranque y 600 s, «refrescar ahora» ahorra como mucho diez minutos. El único caso que ningún intervalo cubre es el **completo**, y para eso basta la tarjeta informando y el `docker exec` documentado al lado. **Informar, no delegar**, que es la propia regla del tramo 2 |
| **D13** | **La edad se nombra por lo que es: la del drenaje, global** | El checkpoint es una fila por feed. Un campo que sugiera «de esta tienda» sería falso, y el ticket lo decía así |
| **D14** | **La `MODIFIED` de `pos-projection` deroga el `MUST NOT` refutando a C22 con números** | Las razones de C22 están escritas y hay que enfrentarlas, no ignorarlas. *«Un contenedor limitado a 512 MiB compitiendo por un pool de cinco conexiones»*: un incremental toca 0-1 páginas de ≤200 ítems y retiene **una** conexión durante segundos, cada 600 s. La otra razón —el `MUST` que enumera `/v1`— **no aplica a un planificador**, sólo a una ruta. Y la tercera —*«la honestidad viene de `projection_age_seconds`, no de un cron oculto»*— es la tesis que este change derriba: **la honestidad existió durante veinte días y no llegó a ninguna pantalla** |
| **D15** | **El grupo 8 de C40 se anota, no se rehace** | Sólo una cifra queda en duda —el reparto de estados— y su dirección es conocida: sin ámbito, más masa en los estados de resultado escaso. **La latencia se sostiene**: sin ámbito el SQL es 2-3 ms más lento (C22: 7,3 ms con CTE contra 8-11 ms) contra un p95 de 7.160 ms dominado por dos llamadas a proveedor, y está verificado que **.NET no repide** cuando la página llega corta, así que no hay viaje extra. Rehacerlo **hoy** reproduciría el defecto, porque el entorno ya está rancio otra vez: la secuencia correcta es **primero C41** |

### Las seis preguntas del ticket, cerradas

| # | Pregunta del ticket | Respuesta |
|---|---|---|
| **1** | ¿El drenaje vive en .NET o en `jbg-ai`? | **En `jbg-ai`** (D1). La pregunta estaba mal planteada: el drenaje tiene dos mitades con dueños distintos —la lectura es de .NET, la escritura es de Python— y lo que decide es **quién puede sostener las dos sin duplicar el protocolo** |
| **2** | ¿Cómo se implementa el lock? | **`pg_try_advisory_lock`, dentro del drenaje** (D6, D7). Cruza procesos y contenedores, así que cubre al CLI, que es el caso que realmente ocurrió |
| **3** | ¿Incremental por defecto y completo sólo a mano? | **Sí, más un completo automático cuando no hay checkpoint** (D5), que es gratis y cura el caso de C34 |
| **4** | ¿El campo es la edad en segundos o un booleano `stale`? | **Los dos, y no es redundancia**: la edad informa, el booleano dice qué decidió el guard **contra el techo que ese servicio tiene configurado**. Derivarlo en el cliente duplicaría el umbral, que es justo lo que el ticket quería evitar |
| **5** | ¿El tramo 3 reutiliza el servicio del tramo 1 o expone el CLI? | **Ninguno de los dos: el tramo 3 se corta** (D12) |
| **6** | ¿Qué dice la insignia, y en qué estados? | **No hay insignia de operario** (D11). En la tarjeta de administrador son **tres estados** —fresca, rancia y sin ámbito—, y el aviso es de **completitud, no de corrección**: «puede que falten resultados» es cierto, «los resultados no son fiables» es falso y es la alarma que C36 evitó con `size_label_missing` |

### Referencias

- Change de OpenSpec: `openspec/changes/add-pos-projection-scheduled-drain/` (C41)
- Ticket: [T-AIENG-041](../../../openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md)
- Ficha del plan: [§3 · C41](../../Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- Diseño RAG: [§6.2, §6.3, §7.6, §12](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- Capabilities que se modifican:
  [`pos-projection`](../../../openspec/specs/pos-projection/spec.md) *(la `MODIFIED` que deroga el
  `MUST NOT`)* · [`ai-service-runtime`](../../../openspec/specs/ai-service-runtime/spec.md) *(la
  sección `projection` del informe de salud)* ·
  [`demo-deployment`](../../../openspec/specs/demo-deployment/spec.md) *(el quinto fallo de
  `verify.sh`)*
- Capabilities que **no** se tocan, y es parte del alcance que no se toquen:
  [`ai-service-api-contracts`](../../../openspec/specs/ai-service-api-contracts/spec.md) ·
  [`ai-free-query-search`](../../../openspec/specs/ai-free-query-search/spec.md) ·
  [`vector-retrieval`](../../../openspec/specs/vector-retrieval/spec.md)
- Historias anteriores: [HU-AIENG-022](HU-AIENG-022.md) *(la proyección, el prefiltro y el techo)* ·
  [HU-AIENG-017](HU-AIENG-017.md) *(la salud enriquecida, la tarjeta y `verify.sh`)*
- Deuda registrada que este change cierra:
  [`DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md), entrada de C34 sobre la proyección vacía
  de la demo
- Informe a anotar:
  [`c40-implementation-measurements.md`](../../Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md), §8
- Testing: [testing-backend.md](../../testing-backend.md) ·
  [testing-frontend.md](../../testing-frontend.md), las dos en *Estado de la suite: fallos conocidos*
- Épica: [EP14 — Búsqueda Semántica Híbrida](../../epicas.md)

---

## Criterios de Aceptación

### Escenario 1: Levantar el entorno deja la proyección fresca

- **Dado que** el servicio `jbg-ai` arranca en un entorno donde el feed `pos-availability` tiene
  checkpoint
- **Cuando** el proceso completa su arranque
- **Entonces** se ejecuta un drenaje **incremental** sin que nadie lo pida
- **Y** `ai.sync_checkpoint.last_incremental_sync_at` del feed `pos-availability` avanza
- **Y** el arranque del servicio no se bloquea esperándolo
- **Y** `GET /health` responde 200 durante todo el proceso

### Escenario 2: Un entorno nuevo se drena entero solo

- **Dado que** `ai.sync_checkpoint` no tiene fila para el feed `pos-availability`
- **Cuando** el servicio arranca
- **Entonces** el drenaje de arranque se ejecuta en modo **completo**
- **Y** al terminar, ninguna recuperación responde 503 por proyección vacía
- **Y** `last_full_sync_at` queda registrado

### Escenario 3: La proyección se mantiene fresca sin intervención

- **Dado que** el servicio lleva arrancado más de un intervalo configurado
- **Cuando** transcurren 600 segundos desde el último drenaje
- **Entonces** se ejecuta un drenaje incremental
- **Y** la edad reportada nunca supera el techo de `JPV_POS_PROJECTION_MAX_AGE_SECONDS` mientras el
  feed responda
- **Y** el prefiltro por punto de venta sigue aplicándose en todas las recuperaciones

### Escenario 4: Dos drenajes no se pisan, y el CLI tampoco

- **Dado que** un drenaje programado está en curso
- **Cuando** alguien ejecuta `python -m jbg_ai.indexing sync-pos` a mano
- **Entonces** el segundo declina inmediatamente sin bloquearse
- **Y** registra que el lock estaba tomado, con su `trace_id`
- **Y** el keyset de `ai.sync_checkpoint` no queda entrelazado
- **Y** el caso simétrico —el CLI primero y el temporizador después— se comporta igual

### Escenario 5: El administrador ve la frescura sin preguntar a nadie

- **Dado que** un administrador abre el dashboard
- **Cuando** la tarjeta de estado del servicio de IA se carga
- **Entonces** muestra cuándo fue el último drenaje, la edad y si está rancia contra el techo
  configurado
- **Y** muestra cuántos puntos de venta de la proyección no tienen ni una fila asignada
- **Y** el valor procede del **checkpoint** y nunca de `ai.pos_projection.refreshed_at`

### Escenario 6: Un fallo del drenaje no rompe nada, y no se traga

- **Dado que** el feed `GET /api/ai/index-feed/pos-availability` no responde
- **Cuando** el drenaje de arranque lo intenta
- **Entonces** el servicio arranca igualmente y `GET /health` responde 200
- **Y** el fallo queda registrado con su causa
- **Y** el drenaje se reintenta sin intervención
- **Y** si una página falla durante un drenaje que sí corre, `failed_pages` se reporta en `/health` y
  **no** se presenta como éxito

### Escenario 7: Un despliegue con la proyección vacía ya no pasa la verificación

- **Dado que** un entorno se despliega con el índice de productos poblado y `ai.pos_projection` vacía
- **Cuando** se ejecuta `verify.sh`
- **Entonces** la verificación **falla** nombrando la proyección como causa
- **Y** no se declara el despliegue correcto

### Escenario 8: La rancidez sigue degradando y nunca escondiendo

- **Dado que** la proyección supera el techo configurado
- **Cuando** se sirve una recuperación de productos
- **Entonces** el ámbito de punto de venta no se aplica para esa petición
- **Y** la respuesta sigue reportando la edad
- **Y** ningún producto válido queda oculto a la autoridad que lo hidrata
- **Y** el comportamiento es **idéntico** al de antes de este change

### Escenario 9: El contrato congelado no se mueve

- **Dado que** el change está implementado
- **Cuando** se ejecuta `test_openapi_snapshot_is_stable`
- **Entonces** pasa contra el `ai-service/openapi.json` **ya commiteado**, sin regenerarlo
- **Y** no existe ninguna ruta nueva bajo `/v1`
- **Y** `GET /api/ai/search/availability` sigue sin llamar al servicio de IA

### Escenario 10: Fuera de alcance explícito — ni botón, ni insignia, ni migración

- **Dado que** el change está implementado
- **Cuando** un operario usa el panel de búsqueda
- **Entonces** no ve ningún control para refrescar la proyección
- **Y** no ve ninguna insignia sobre su frescura
- **Y** no existe ninguna revisión nueva de Alembic ni migración de EF Core
- **Y** `Carried()` y la frontera de autorización siguen exactamente donde estaban

---

## Notas adicionales

- **Actor principal:** Administrador del sistema. El **Operador** es el beneficiario silencioso: no ve
  nada nuevo y recibe páginas completas, que es precisamente el objetivo.
- **La frescura NO se mide leyendo `MAX(refreshed_at)`.** El feed es incremental por keyset, así que
  una asignación que no cambia nunca se re-emite y `refreshed_at` registra cuándo cambió **la
  asignación**, no cuándo se miró la proyección. Esta confusión ya ha costado dos veces: **la sesión de
  C40 la cometió al arreglar y la de C41 al diagnosticar.** Cualquier verificación de este change lee
  el **checkpoint**.
- **La zona de la ficha del plan está mal** y hay que corregirla: dice *«`backend/src/` y
  `frontend/src/` — no toca `ai-service/`»*. Con D1, la zona principal es **`ai-service/`**, más
  `deploy/demo/` y un retoque menor en `backend/` y `frontend/` para transportar y pintar la sección
  nueva del informe de salud.
- **C41 no compite con C38 ni con C39**: no toca prompt, ni fase de abstención, ni el contrato
  congelado. Puede ir antes, después o en paralelo — **pero va antes de cualquier remedición**, por
  D15.
- **Limitación conocida que se conserva:** `ai.sync_failure` sigue sin tener lector automático. Una
  página fallida se cuenta y se reporta; recuperarla sigue siendo un `--full` a mano.
- **Residuo declarado:** las 94 filas con `computed_as_of = 2026-09-25 05:32:04` se dejan como prueba
  forense del hallazgo 5. Son `is_assigned_hint = false`, así que el prefiltro no las ve nunca.
- **Trampa viva que hay que conocer antes de medir nada:** `free_query_gate.py --pos-id` apunta por
  defecto a `b0000000-0000-4000-8000-000000000002`, que no tiene ni una fila en la proyección, y el POS
  `cd9bfd1f…` tiene **0 asignados sobre 144 filas**. Las dos producen 503.

---

## Tareas

1. **Puerta de entrada**: línea base de las **tres** suites **por nombres de test**, no por número
   —`git stash push -u`, ejecutar, `git stash pop`—; backend y frontend vienen rojas de fábrica.
   `openspec validate --all --strict` en verde y **`sha256` de `ai-service/openapi.json` anotado**,
   porque la afirmación central del change es que ese fichero no se mueve.
2. **Tramo 1 · el lock**: `pg_try_advisory_lock` no bloqueante sobre una conexión dedicada, tomado
   **dentro** del camino de drenaje para que lo hereden el CLI y el planificador. Clave constante y
   **documentada**.
3. **Tramo 1 · el planificador**: tarea de `lifespan` no bloqueante, drenaje de arranque (completo sin
   checkpoint, incremental con él), bucle por intervalo, retroceso acotado ante feed caído.
4. **Tramo 1 · los ajustes**: intervalo y conmutador de encendido en `settings.py`, con el patrón
   `blank_*_is_default` que usan los demás, defecto **600 s**, y **apagarlo restaura exactamente el
   comportamiento previo** (que es la ablación y el *rollback*).
5. **Tramo 2a · `/health`**: sección `projection` con edad desde el checkpoint, último drenaje, último
   completo, `stale` contra el techo, páginas fallidas y puntos de venta sin ámbito. Reutilizar
   `projection_synced_at()` y la caché corta; **no añadir round trips a la ruta de recuperación**.
6. **Tramo 2a · transporte**: `AiHealthResponse` + `AiHealthProjection` en .NET y `ai-health.types.ts`
   en el frontend, los dos tolerantes a su ausencia (un `jbg-ai` antiguo no la manda).
7. **Tramo 2a · la tarjeta**: tres estados en `AdminDashboard.tsx`, copia sobria de completitud y no de
   corrección, con el `docker exec` del completo documentado al lado.
8. **Tramo 2a · `verify.sh`**: quinto motivo de fallo por proyección vacía, y entrada de
   `DEFERRED_TASKS.md` cerrada.
9. **Specs**: `## MODIFIED` sobre `pos-projection` derogando el `MUST NOT` **con la refutación numérica
   escrita**, más `ai-service-runtime` y `demo-deployment`. Descripción de cada requisito **en una sola
   línea física**, o el validador falla con un mensaje que no dice que el problema es tipográfico.
10. **Comprobación con datos reales** en local: arrancar con la proyección rancia y comprobar que se
    drena sola; arrancar sin checkpoint y comprobar el completo; lanzar el CLI durante un drenaje y
    comprobar que declina; y **leer el checkpoint, no las filas**, para verificar.
11. **Anotación del informe de C40**: nota fechada en el §8 diciendo qué cifras se sostienen (latencia,
    con su razón) y cuáles describen el sistema degradado (reparto de estados). **No se toca ningún
    número ni ningún artefacto.**
12. **Documentación**: retirar las tres frases que quedan falsas —`ai-service/README.md:325-330` con su
    receta de cron, `ai-service/README.md:1229` y `openspec/project.md:372`—, más
    `Documentos/epicas.md`, la ficha del plan (incluida **la corrección de zona**) y
    `deploy/demo/README.md`.

---

## Estimaciones y atributos de priorización

| Atributo | Valor |
|---|---|
| Puntos de historia | _Pendiente_ — a fijar en refinamiento |
| Impacto en usuario / valor de negocio | **4/5** — cierra un modo de fallo que ha costado **tres sesiones** y que **invalidó parcialmente una medición ya publicada**. No añade capacidad visible al operario: le devuelve la que C22 entregó y que la rancidez venía apagando en silencio |
| Urgencia | **4/5** — **la demo se vuelve a desplegar antes de la entrega**, así que el drenaje de arranque y el quinto fallo de `verify.sh` se ejercen de verdad en esa ventana. Y **cualquier remedición futura depende de esto**: hoy el entorno está a 14,4 veces el techo |
| Complejidad / esfuerzo | **3/5** — el drenaje **ya existe y no se reescribe**. La dificultad es de encaje: derogar un `MUST NOT` de spec viva **refutando a C22 con números**, y no romper por accidente la afirmación de que el contrato congelado no se mueve |
| Riesgos | **El arranque podría bloquearse** y marcar el contenedor *unhealthy*, tumbando el despliegue por culpa de la mejora (mitigado por D3: tarea creada y no esperada, con escenario de aceptación propio). **El lock retiene 1 de 5 conexiones** mientras dura el drenaje (aceptado y declarado; el incremental dura segundos). **En dev local `jbg-ai` suele estar arriba y la API .NET no**, así que el drenaje de arranque fallará y reintentará (aceptado: se autocura justo cuando empiezan las pruebas, que es el único momento que importa). **La `MODIFIED` toca una spec cuyo `MUST NOT` fue deliberado** (mitigado escribiendo la refutación, no ignorándola) |
| Dependencias | **C22** y **C17** archivados. **No compite con C38 ni C39.** No debe abrirse a la vez que ningún change que toque `retrieval/` o `indexing/` |

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| **Q-1** | ¿Los ajustes nuevos se llaman `JPV_POS_SYNC_SCHEDULER_ENABLED` y `JPV_POS_SYNC_INTERVAL_SECONDS`? | **Sí**, siguiendo el prefijo `jpv_pos_*` que ya usan `jpv_pos_prefilter_enabled` y `jpv_pos_projection_max_age_seconds`. Ninguno se fija en `canonical_openapi_settings()`, porque ninguno alcanza el contrato |
| **Q-2** | ¿El conmutador viene **encendido** por defecto? | **Sí.** Apagado por defecto reproduce el problema exacto que el change viene a cerrar: algo que hay que acordarse de activar. Apagarlo explícitamente es la ablación y el *rollback* |
| **Q-3** | ¿La clave del *advisory lock* es `hashtext('pos-availability')` o una constante fija? | **Constante fija documentada**, con el nombre del feed en el comentario: `hashtext` no garantiza estabilidad entre versiones de PostgreSQL y un cambio silencioso de clave desactivaría el lock sin fallar |
| **Q-4** | ¿Qué hace el drenaje de arranque si el feed nunca responde? | **Reintenta con retroceso acotado y se rinde al bucle normal**, registrando cada intento. No hay número mágico de reintentos: al primer tick del intervalo el problema deja de ser especial |
| **Q-5** | ¿`shops_without_scope` cuenta contra los puntos de venta **activos** de .NET o contra los que aparecen en la proyección? | **Contra los que aparecen en la proyección**, porque Python **no lee `public` por SQL** y el número tiene que salir del esquema `ai`. Contarlo contra los activos exigiría una consulta al feed que este change no abre |
| **Q-6** | ¿La tarjeta muestra la edad en segundos o en lenguaje natural? | **Lenguaje natural** («hace 12 minutos»), con el valor exacto en el `title`. Es una tarjeta de diagnóstico para una persona, no un artefacto de medición |
| **Q-7** | ¿La nota del informe de C40 la firma C41 o se publica sin atribución? | **Firmada y fechada como anotación posterior de C41**, para que se distinga de lo que la sesión de C40 midió y escribió |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
añada ruta bajo `/v1`, **no** regenere `ai-service/openapi.json`, **no** abra migración de Alembic ni de
EF Core, **no** haga que .NET lea ni escriba el esquema `ai`, y **no** cambie el comportamiento de
degradación ante una proyección rancia.
