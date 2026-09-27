## Why

**La frescura de `ai.pos_projection` no tiene dueño ejecutable, y eso ha costado tres sesiones.** Al
levantar el entorno para las pruebas manuales posteriores al cierre de C40, el *checkpoint*
`ai.sync_checkpoint.last_incremental_sync_at` del feed `pos-availability` venía del **5 de
septiembre** —veinte días contra un techo de 3.600 s— y hubo que drenarlo a mano para que las pruebas
midieran el sistema y no su desconfiguración.

**Y el planificador existe. Vive en prosa.** `ai-service/README.md` lleva desde C22 una receta de cron
cada diez minutos que **es inejecutable en la topología que desplegamos**: empieza por
`cd /srv/jbg-ai`, una ruta de host, y `jbg-ai` es un contenedor — la demo drena con
`docker exec -i jbg-demo-ai …`. Por eso nadie la instaló nunca. Este change no inventa un
planificador: **lo mueve de la prosa a algo que se despliega**.

**Son tres incidentes y dos modos de fallo distintos.** C34 encontró la proyección **vacía** en la
demo —`count_scope = 0` → **503 en toda recuperación**, con .NET degradando a léxico con 200, *«así
que desde fuera el entorno parece sano»*—, y sigue abierto en `openspec/DEFERRED_TASKS.md`. C40 y C41
la encontraron **rancia**, a 19,7 y 20 días.

**Los tres ocurrieron levantando un entorno para probar**, no en régimen permanente. Ésa es la
observación que fija el diseño: un cron de host no corre en el portátil de nadie, y un temporizador
deja una ventana abierta justo cuando se mide. **El disparo que mata los tres casos es el de
arranque.**

**No es una fuga, y conviene fijarlo antes de proponer nada.** Hay dos filtros y sólo uno es la
frontera: el prefiltro de `ai.pos_projection` estrecha la ventana de candidatos, y `Carried()` —en
`AssistedSearchRepository`, arrancando desde `Inventories`— decide qué se sirve, en **toda**
respuesta. Un operario **nunca** ve una pieza que su tienda no lleva. Lo que la rancidez causa es que
**la página llegue corta**: la avería que C22 midió —ocho de once tiendas por debajo de una página en
al menos seis de cada veinte búsquedas, peor caso **un solo producto**—. Y **degradar es la decisión
correcta**: filtrar con una proyección de veinte días escondería las piezas asignadas después del
último drenaje, un falso negativo invisible. **Este change no toca esa decisión.**

**Y hay un coste ya pagado que lo dimensiona.** La manipulación declarada en el §8 del informe de C40
—*«se actualizaron `refreshed_at` y `computed_as_of` en 1.176 filas»*— **se aplicó a la columna
equivocada**: el guard lee el *checkpoint*. Cuatro pruebas lo cierran —los dos campos del checkpoint
son idénticos (2026-09-25 20:49:24 UTC), el artefacto del grupo 8 está fechado 15 h 07 min antes,
quedan **94 filas** con la huella del `UPDATE`, y «1.176» es el total exacto de filas del POS
`0388f003…`—, así que **el reparto de los dieciséis estados de C40 describe el sistema degradado**. El
remate: `degraded_reason` es `null` en las 42 filas del artefacto, porque .NET **no tiene campo** para
la degradación de la proyección. Un dato que el sistema conoce, paga y descarta en la frontera.

## What Changes

**En este orden, y el primero es el núcleo.**

1. **El drenaje programado, en `jbg-ai`.** Una tarea en el `lifespan` de FastAPI que reutiliza
   `sync_pos_availability` **sin reescribirlo** — una sola implementación del protocolo del keyset.
   Drena **al arrancar** (completo si no hay checkpoint, incremental si lo hay) y **cada 600 s**. La
   tarea **no bloquea el arranque**: el `HEALTHCHECK` sondea `/health` con 3 s de tope y
   `compose.demo.yaml` encadena `depends_on: service_healthy`, así que esperar un completo de 34
   páginas marcaría el contenedor *unhealthy* y tumbaría el despliegue por culpa de la mejora. Un
   fallo del feed se registra y se reintenta con retroceso acotado; nunca tumba el arranque.

2. **El lock, o el tramo 1 no se construye.** `pg_try_advisory_lock` **no bloqueante**, tomado
   **dentro** del camino de drenaje para que lo hereden el CLI y el planificador. `ai.sync_checkpoint`
   es **una fila por feed** con `watermark` y `since_id`, y dos drenajes concurrentes escriben el
   keyset entrelazado — un keyset corrupto **no falla: se salta filas en silencio**, que es peor que la
   rancidez que veníamos a arreglar.

3. **La edad, dicha donde ya hay pantalla.** `GET /health` gana una sección `projection`: edad desde
   el **checkpoint** —nunca desde `refreshed_at`—, último drenaje, último completo, `stale` contra el
   techo configurado, páginas fallidas y **cuántos puntos de venta de la proyección no tienen ni una
   fila asignada**. `AiHealthResponse` y `ai-health.types.ts` la transportan hasta la tarjeta de
   estado del administrador que C17 ya construyó.

4. **`verify.sh` gana su quinto motivo de fallo.** Proyección vacía ⇒ despliegue fallido. Hoy *«un
   entorno con índice lleno y proyección vacía pasa la verificación posterior al despliegue»*, según
   su propia entrada de `DEFERRED_TASKS.md`, que este change cierra.

5. **Tres frases de documentación retiradas, no matizadas.** `ai-service/README.md` (la sección *«There
   is no route and no scheduler, on purpose»* con su receta de cron, y la línea del registro de C22) y
   `openspec/project.md` (*«a cron, not a route»*).

6. **El informe de C40, anotado.** Nota fechada y firmada como anotación posterior diciendo qué cifras
   se sostienen —la latencia, con su razón— y cuáles describen el sistema degradado. **No se toca
   ningún número ni ningún artefacto.**

**Lo que NO cambia, y es parte del alcance que no cambie:** ninguna ruta bajo `/v1`;
`ai-service/openapi.json` no se regenera y `test_openapi_snapshot_is_stable` pasa contra el fichero ya
commiteado; `GET /api/ai/search/availability` no se toca, y su `MUST` de no llamar al servicio de IA
se conserva; `Carried()` y la frontera de autorización se quedan donde están; no hay migración de
Alembic ni de EF Core; no hay insignia de operario ni botón manual de drenaje, **tampoco para el
administrador**.

## Capabilities

### New Capabilities

Ninguna. Este change modifica comportamiento de tres capacidades vivas y no introduce ninguna
superficie nueva — que es precisamente lo que permite afirmar que el contrato congelado no se mueve.

### Modified Capabilities

- `pos-projection`: deroga la prohibición *«MUST NOT start an in-process scheduler or background
  task»* con refutación numérica de las razones de C22, y añade el drenaje de arranque e intervalo, el
  lock no bloqueante que cubre también al CLI, y la lectura de puntos de venta sin ámbito.
- `ai-service-runtime`: el informe de salud público gana una sección `projection` leída del
  *checkpoint*, sin mover el contrato congelado porque su anotación de retorno es un *mapping*
  abierto.
- `demo-deployment`: la verificación desde el host gana una quinta condición de fallo — una proyección
  sin ninguna fila asignada.

## Impact

**Zona principal: `ai-service/`.** La ficha del plan decía *«`backend/src/` y `frontend/src/` — no
toca `ai-service/`»* y **está corregida**: el drenaje se queda en `jbg-ai` porque llevarlo a un
`BackgroundService` de .NET no sería un planificador sino **una segunda implementación del protocolo
del keyset** sobre la misma fila de checkpoint, y porque .NET tendría que escribir `ai.*`, frontera
que `migrations/bootstrap.sql` hace **estructural por *grants***.

| Zona | Qué cambia |
|---|---|
| `ai-service/src/jbg_ai/indexing/` | El lock dentro del camino de drenaje y el planificador. `pos_orchestrator.sync_pos_availability` **no se reescribe** |
| `ai-service/src/jbg_ai/api/` | `lifespan` crea la tarea sin esperarla; `health_report.py` gana la sección `projection` |
| `ai-service/src/jbg_ai/config/settings.py` | `JPV_POS_SYNC_SCHEDULER_ENABLED` (true) y `JPV_POS_SYNC_INTERVAL_SECONDS` (600). Ninguno se fija en `canonical_openapi_settings()` |
| `ai-service/src/jbg_ai/retrieval/search.py` | Una lectura de conteo por punto de venta. `PROJECTION_SYNCED_AT_SQL` se **reutiliza** |
| `backend/src/…/DTOs/Ai/AiHealthResponse.cs` | Gana `AiHealthProjection`, **tolerante a su ausencia** |
| `frontend/src/types/` · `src/pages/dashboard/` | `ai-health.types.ts` y la tarjeta con sus tres estados, en es-ES |
| `deploy/demo/verify.sh` | Quinto motivo de fallo del despliegue |
| `Documentos/` · READMEs · `openspec/project.md` | Tres frases falsas retiradas y la anotación del informe de C40 |

**Dependencias.** Prerrequisitos **C22** (la proyección, el prefiltro y el techo) y **C17** (el
informe de salud enriquecido, la tarjeta y `verify.sh`), los dos archivados. **No compite con C38 ni
C39** —no toca prompt, ni fase de abstención, ni `openapi.json`—, pero **va antes de cualquier
remedición**: el entorno está hoy a **14,4 veces** el techo de rancidez, así que una pasada tomada
ahora volvería a describir un sistema desconfigurado.

**Riesgos.** Que la tarea bloquee el arranque y marque el contenedor *unhealthy* (mitigado: se crea y
no se espera, con escenario de aceptación propio). Que el lock retenga 1 de las 5 conexiones del pool
mientras dura el drenaje (aceptado y declarado; un incremental dura segundos). Que en dev local
`jbg-ai` esté arriba y la API .NET no, de modo que el drenaje de arranque falle y reintente (aceptado:
se autocura justo cuando empiezan las pruebas, que es el único momento que importa).

**Contrato y datos.** Sin *breaking changes*: `openapi.json` sin diff, sin migración, y la sección
nueva del informe de salud es aditiva en los dos lados.
