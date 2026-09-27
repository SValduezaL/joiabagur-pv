## Context

`ai.pos_projection` es la proyección de disponibilidad por punto de venta que C22 creó, y el prefiltro
blando de la recuperación la lee para estrechar la ventana de candidatos al surtido de la tienda. Su
frescura se mide contra `ai.sync_checkpoint.last_incremental_sync_at` del feed `pos-availability`, con
un techo de `JPV_POS_PROJECTION_MAX_AGE_SECONDS` (3.600 s), y por encima de ese techo `resolve_scope`
**deja de aplicar el ámbito y lo declara**.

**Quién la drena hoy: nadie.** `python -m jbg_ai.indexing sync-pos` es un CLI, y la única receta
programada que existe vive en `ai-service/README.md` y es **inejecutable en la topología real**
(`cd /srv/jbg-ai`, ruta de host, contra un `jbg-ai` que se despliega como contenedor).

**Estado medido de la base local el 2026-09-26**, que es la línea de partida de este diseño:

```
feed             | last_incremental_sync_at      | last_full_sync_at             | indexed_count
pos-availability | 2026-09-25 20:49:24.836539+00 | 2026-09-25 20:49:24.836539+00 |          6720
                   edad: 51.677 s  →  STALE, 14,4 × el techo

is_assigned_hint = true : 6.050      false : 670
12 puntos de venta en la proyección; uno (cd9bfd1f…) con 0 asignados sobre 144 filas → 503
94 filas con computed_as_of = 2026-09-25 05:32:04   ← huella del UPDATE manual de C40
```

**El drenaje tiene dos mitades con dueños distintos**, y ahí está toda la decisión:

```
        LECTURA                                    ESCRITURA
   ┌──────────────────────┐                 ┌──────────────────────────┐
   │ GET /api/ai/index-   │                 │ ai.pos_projection        │
   │   feed/pos-availab.  │  ── keyset ──▶  │ ai.sync_checkpoint       │
   │ dueño: .NET          │                 │ ai.sync_failure          │
   │ auth: X-Index-Feed-  │                 │ dueño: Python            │
   │       Key            │                 │ grant: SÓLO rol jbg_ai   │
   └──────────────────────┘                 └──────────────────────────┘
```

La escritura **no es un `INSERT`: es un protocolo.** Precedencia de cursor, el centinela
`EXHAUSTED_SINCE_ID`, el borrado suave del *tombstone*, el registro en `ai.sync_failure`, y la regla
de que una página posterior que sí escribe mueve el marcador por delante de una fallida. Son ~250
líneas comentadas y probadas en `indexing/pos_orchestrator.py`.

## Goals / Non-Goals

**Goals:**

- Que **«el entorno está levantado» implique «la proyección está fresca»**, sin que nadie se acuerde
  de nada.
- Que la edad y el estado de la proyección **lleguen a una pantalla**, en vez de quedarse en una línea
  de etapa.
- Que un despliegue con la proyección vacía **no pase** la verificación posterior.
- Que el keyset **no se pueda entrelazar**, ni entre drenajes programados ni contra el CLI a mano.
- Que todo lo anterior se consiga **sin mover el contrato congelado** ni abrir migración.

**Non-Goals:**

- **Cambiar la decisión de degradar** ante una proyección rancia. Es correcta y está argumentada.
- **Tocar `Carried()`** o cualquier frontera de autorización.
- **Añadir rutas bajo `/v1`** o regenerar `ai-service/openapi.json`.
- **Un botón de drenaje manual**, ni para el operario ni para el administrador (D12).
- **Una insignia de frescura en la pantalla del operario** (D11).
- **Leer o reprocesar `ai.sync_failure`.** Se cuenta y se reporta; recuperarlo sigue siendo un
  `--full` a mano.
- **Re-medir el grupo 8 de C40.** Se anota (D15).
- **Limpiar las 94 filas residuales** del `UPDATE` de C40. Son la prueba forense y son inofensivas
  (`is_assigned_hint = false`, y el prefiltro exige `IS TRUE`).

## Decisions

### D1 · El drenaje vive en `jbg-ai`, no en un `BackgroundService` de .NET

El ticket pedía un `BackgroundService` con el patrón de `ModelTrainingBackgroundService`. **Lo que
pedía no es un planificador: es una segunda implementación del protocolo del keyset.**

| Opción | Contrato | Spec viva | Frontera `ai.*` | ¿Arregla dev local? | Veredicto |
|---|---|---|---|---|---|
| **A** · .NET drena entero | — | `pos-projection` | **Rota — grants** | ✅ | ❌ Duplica el protocolo; con el CLI obligatorio quedan **dos drenadores sobre la misma fila de checkpoint** |
| **B** · .NET programa, Python ejecuta por ruta `/v1` | **Ruta 12ª bajo `/v1`** | `api-contracts` | — | ✅ | ❌ Mueve el contrato congelado; HU-AIENG-022 ya rechazó `POST /v1/index/sync-pos` por escrito |
| **D** · cron de host o *sidecar* de Compose | — | — | — | ❌ / ⚠️ | ❌ **Es lo que ya existía y falló.** Nada en la aplicación sabe que el drenaje existe, así que nada puede reportarlo |
| **E** · Python programa y ejecuta: arranque + intervalo | — | `pos-projection` | — | ✅ | ✅ **Elegida** |

**A es más cómoda hoy y peor dentro de seis meses.** Su acoplamiento de ciclo de vida es perfecto —la
API .NET es el único proceso garantizadamente arriba en todos los entornos donde falló esto, y su
dependencia, el feed, es ella misma—, pero duplica un protocolo cuyo modo de fallo es *saltarse filas
en silencio*, y el lock protegería la **concurrencia**, no la **divergencia semántica** entre dos
implementaciones. Además exige otorgar al rol de la API privilegios sobre `ai`, debilitando para
siempre una frontera que `migrations/bootstrap.sql` hace estructural — *«make the boundary the default
rather than a convention»*.

### D2 · Arranque **y** intervalo, y el arranque es lo que de verdad arregla

Los tres incidentes comparten forma: *alguien levantó un entorno y se puso a probar*. Un cron de host
no corre en el portátil de nadie, y un intervalo de 10-30 min deja una ventana abierta justo cuando se
mide.

```
   arranque del contenedor
        │
        ├── ¿hay checkpoint? ── no ──▶  drenaje COMPLETO     (cura el caso C34)
        │                    ── sí ──▶  drenaje incremental  (cura C40 y C41)
        │                                      │
        │                          feed caído ─┤─▶ retroceso acotado, WARNING legible,
        │                                      │   NUNCA tumba el arranque
        ▼                                      ▼
   ┌──────────────────────────────────────────────────┐
   │  bucle: cada 600 s, incremental, con lock        │
   └──────────────────────────────────────────────────┘
```

### D3 · La tarea no bloquea el arranque

El `HEALTHCHECK` del Dockerfile sondea `/health` con 3 s de tope y `compose.demo.yaml` encadena
`depends_on: service_healthy`. Un drenaje completo son 34 páginas contra un presupuesto de 180 s:
esperarlo marcaría el contenedor *unhealthy* y **tumbaría el despliegue por culpa de la mejora**. La
tarea se **crea** en el `lifespan` y no se espera.

### D4 · Intervalo de 600 s, derivado y no elegido

Tres documentos daban tres números —README 10 min, diseño §6.3 «5-10 min», ticket «15-30 min»— y
ninguno argumentado. Lo que importa no es el intervalo sino **cuántos fallos consecutivos se toleran
antes de que el guard degrade**:

| Intervalo | Fallos tolerados contra un techo de 3.600 s |
|---|---|
| 1.800 s | **1** |
| 900 s | 3 |
| **600 s** | **5** |

Regla: `techo / intervalo ≥ 4` ⇒ ≤ 900 s. Se elige **600 s**, que además empata con la receta del
README y con el §6.3 del diseño sin coste alguno.

### D5 · Incremental por defecto; completo cuando no hay checkpoint

El incremental es keyset y baratísimo. Y «completo si no hay checkpoint» **es gratis**:
`resolve_start_cursor` ya devuelve `(None, None)` en ausencia de cursor e `is_full` se calcula solo.
Con eso, el modo de fallo de C34 —proyección vacía, 503 en toda recuperación— se cura al arrancar.

### D6 · `pg_try_advisory_lock`, no bloqueante, **dentro** del drenaje

| Mecanismo | Veredicto |
|---|---|
| Mutex de aplicación | **Insuficiente.** Sólo protege del solape intra-proceso; no ve al CLI, que corre en otro proceso |
| `SELECT … FOR UPDATE` sobre el checkpoint | **Inviable.** El drenaje son 34 transacciones, no una; mantener una abierta retendría 1 de 5 conexiones durante minutos |
| **`pg_try_advisory_lock`** | ✅ De sesión, cruza procesos y contenedores. **No bloqueante**: el segundo drenaje declina y lo registra |

**Va dentro del camino de drenaje, no en el planificador.** El ticket lo colocaba en el planificador y
decía que protegía «del solape consigo mismo y de cualquier disparo manual del tramo 3» — faltaba **el
caso que de verdad ocurrió: el CLI a mano**, que es como se arregló las tres veces. El propio
`pos_orchestrator.py` ya lo anticipa: *«un cron disparando mientras alguien lo corre a mano»*.

**No bloqueante** porque encolar temporizadores es cómo se construye una estampida: si un drenaje
tarda más que el intervalo, la cola crece sin límite. Declinar es la respuesta correcta.

**Clave: constante fija y documentada**, no `hashtext('pos-availability')`. `hashtext` no garantiza
estabilidad entre versiones de PostgreSQL, y un cambio silencioso de clave **desactivaría el lock sin
fallar** — exactamente el modo de fallo que el lock existe para evitar.

**Coste declarado:** 1 de las 5 conexiones del pool mientras dura el drenaje.

### D7 · La edad se dice en `GET /health`, no en `GET /api/ai/search/availability`

El ticket llamaba a esto *«aditivo y pequeño»*. Es **el más caro normativamente de los tres tramos**:
`ai-free-query-search` tiene un `MUST` que C40 escribió a propósito —*«that route MUST NOT call the AI
service, MUST NOT consume any request-rate quota and MUST NOT run any model»*— y `GetAvailability` es
**síncrono**, así que volverlo `async` mueve interfaz, servicio, controlador y tests.

```
ai.sync_checkpoint          GET /health              GET /api/ai/health        AdminDashboard
 last_incremental_  ──▶  projection: {         ──▶   AiHealthResponse    ──▶   tarjeta jbg-ai
   sync_at                 synced_at, age,           + AiHealthProjection      (ya existe)
                           stale, ceiling,
                           failed_pages,
                           shops_without_scope }
                              ▲                          ▲                        ▲
                       mapping abierto:            admin-only, sin             ya renderiza
                       0 coste de contrato         circuit breaker             index/provider
```

C17 dejó la anotación de retorno de `/health` como *mapping* abierto **exactamente para esto**, y el
DTO de .NET lo declara en su propia documentación: *«an unrecognised field is ignored rather than
fatal»*. **Coste de contrato cero en los dos lados**, y llega a la pantalla que el propio ticket
nombraba para el tramo 3: *«la pantalla de administración es donde se mira un dato de sistema»*.

### D8 · La edad **y** el booleano, y no es redundancia

La edad informa; `stale` dice **qué decidió el guard contra el techo que ese servicio tiene
configurado**. Derivarlo en el cliente duplicaría el umbral en dos sitios, que es justo lo que el
ticket quería evitar. Se transporta también `ceiling`, para que la tarjeta pueda explicar el veredicto
sin conocer la configuración del servicio.

### D9 · La edad es del **drenaje** y es **global**

El ticket decía *«la edad de la proyección de esa tienda»*. No existe tal cosa: el checkpoint es
`PRIMARY KEY (feed)`, así que `resolve_scope` devuelve el mismo `reported_age` para los doce puntos de
venta. Los campos se nombran por lo que son, y nada sugiere frescura por tienda.

Lo que **sí** es por tienda es `count_scope(pos_id)`, y su valor interesante es **cero** — el modo de
fallo de C34. De ahí `shops_without_scope`, contado **contra los puntos de venta que aparecen en la
proyección**, porque Python **no lee `public` por SQL**: contarlo contra los activos de .NET exigiría
una consulta al feed que este change no abre.

### D10 · `verify.sh` gana su quinto motivo de fallo

Cinco líneas de bash contra un modo de fallo que, según su propia entrada de `DEFERRED_TASKS.md`,
*«pasa hoy la verificación posterior al despliegue»*. Se ejerce de verdad: **la demo se vuelve a
desplegar antes de la entrega**.

### D11 y D12 · Sin insignia de operario, y sin botón manual — tampoco para el administrador

La rancidez **no le esconde piezas** al operario: sólo le llega la página corta. Enseñárselo le
entregaría un problema que no es suyo y le invitaría a leer «no encontré mucho» como «el dato está
mal».

**Y el argumento que mata el botón del operario mata también el del administrador.** Con arranque más
600 s, «refrescar ahora» ahorra como mucho diez minutos de espera, y eso no paga una ruta nueva en un
contrato cuya superficie está enumerada en un `MUST`. El único caso que ningún intervalo cubre es el
**completo** —tras un cambio de `IndexFeed:SalesAsOf`, o tras páginas fallidas—, y para eso basta que
la tarjeta informe y que el `docker exec` esté documentado al lado. **Informar, no delegar.**

### D13 · La copia de la tarjeta avisa de **completitud**, no de corrección

Tres estados: fresca (nada que decir), rancia («puede que falten resultados»), sin ámbito (la tienda
no tiene surtido proyectado). «Los resultados no son fiables» sería **falso** —`Carried()` sigue
poniendo la verdad— y es la alarma que C36 evitó con `size_label_missing`.

### D14 · La `MODIFIED` de `pos-projection` refuta a C22 con números, no lo ignora

C22 escribió tres razones para prohibir el planificador en proceso, y hay que enfrentarlas:

| Razón de C22 | Respuesta |
|---|---|
| *«un contenedor limitado a 512 MiB compitiendo por un pool de cinco conexiones»* | Un incremental toca **0-1 páginas de ≤200 ítems** y retiene **una** conexión durante segundos, cada 600 s. La tarea no mantiene estado entre ticks |
| *«`api-contracts` enumera la superficie `/v1` en un MUST»* | **No aplica a un planificador**, sólo a una ruta. Este change no añade ninguna |
| *«la honestidad viene de `projection_age_seconds`, no de un cron oculto»* | **Es la tesis que este change derriba**: la honestidad existió durante veinte días y **no llegó a ninguna pantalla**. Y el cron deja de ser oculto precisamente porque `/health` lo reporta |

### D15 · El grupo 8 de C40 se anota, no se rehace

Sólo una cifra queda en duda —el reparto de estados— y su dirección es conocida: sin ámbito, **más**
masa en los estados de resultado escaso. La latencia **se sostiene**: sin ámbito el SQL es 2-3 ms más
lento (C22 midió 7,3 ms con CTE contra 8-11 ms sin) frente a un p95 de 7.160 ms dominado por dos
llamadas a proveedor, y **.NET no repide** cuando la página llega corta —`AssistedSearchService` hace
una sola llamada con `CandidateWindow` fijo—, así que no hay viaje extra.

**Y el arnés del grupo 8 no está en el árbol**: el commit `be45e07` añadió sólo el informe y los dos
artefactos. Rehacerlo significa **reescribirlo**; el dinero de proveedor (≈ 0,65 USD las 71 consultas)
es irrelevante al lado de eso. Rehacerlo **hoy** reproduciría el defecto, porque el entorno ya está a
14,4 veces el techo: la secuencia correcta es **primero este change**.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| **La tarea bloquea el arranque** y marca el contenedor *unhealthy*, tumbando el despliegue por culpa de la mejora | D3: se crea y no se espera. Escenario de aceptación propio: `/health` responde 200 durante todo el drenaje inicial |
| **El lock retiene 1 de 5 conexiones** mientras dura el drenaje | **Aceptado y declarado.** Un incremental dura segundos; un completo, minutos, y ocurre una vez por entorno nuevo |
| **En dev local `jbg-ai` está arriba y la API .NET no**, así que el drenaje de arranque falla y reintenta | **Aceptado**, y es ruido útil: se autocura en el momento exacto en que la API aparece, que es cuando empiezan las pruebas. Retroceso acotado y `WARNING` legible |
| **La `MODIFIED` toca un `MUST NOT` deliberado** de una spec viva | D14: se refuta con números y se escribe la refutación en la propia spec, en vez de retirar la frase en silencio |
| **Un drenaje más lento que el intervalo** encolaría temporizadores | D6: el lock es **no bloqueante**; el tick que llega tarde declina y lo registra |
| **`ai.sync_failure` sigue sin lector automático** | **Limitación conocida y conservada.** Se cuenta y se reporta en `/health`; recuperarla sigue siendo un `--full` a mano, documentado junto a la tarjeta |
| **Las 94 filas residuales** de C40 declaran un segundo reloj | **Declarado, no borrado.** Son `is_assigned_hint = false` y el prefiltro exige `IS TRUE`, así que no alcanzan ninguna consulta viva. Borrarlas destruiría la prueba del hallazgo |

## Open Questions

Ninguna bloqueante. Las siete de la historia se resuelven con su opción por defecto:

| # | Pregunta | Decisión aplicada |
|---|---|---|
| Q-1 | Nombres de los ajustes | `JPV_POS_SYNC_SCHEDULER_ENABLED` y `JPV_POS_SYNC_INTERVAL_SECONDS`, prefijo `jpv_pos_*` como los dos que ya existen |
| Q-2 | ¿Conmutador encendido por defecto? | **Sí.** Apagado reproduciría el problema que el change cierra: algo que hay que acordarse de activar. Apagarlo es la ablación y el *rollback* |
| Q-3 | Clave del lock | **Constante fija documentada**, no `hashtext` (D6) |
| Q-4 | ¿Y si el feed nunca responde en el arranque? | Retroceso acotado y rendición al bucle normal, registrando cada intento. Al primer tick del intervalo el problema deja de ser especial |
| Q-5 | Base de conteo de `shops_without_scope` | **Los que aparecen en la proyección** (D9) |
| Q-6 | Formato de la edad en la tarjeta | **Lenguaje natural**, valor exacto en el `title`. Es diagnóstico para una persona |
| Q-7 | Firma de la anotación del informe de C40 | **Firmada y fechada como anotación posterior de C41**, para distinguirla de lo que la sesión de C40 midió |

**Opción por defecto ante cualquier detalle menor no listado:** la más estrecha que **no** añada ruta
bajo `/v1`, **no** regenere `openapi.json`, **no** abra migración, **no** haga que .NET lea ni escriba
el esquema `ai`, y **no** cambie el comportamiento de degradación ante una proyección rancia.
