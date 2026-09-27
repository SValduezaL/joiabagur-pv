# T-AIENG-041: Keep `ai.pos_projection` fresh by schedule and report its age on the administrator card (C41)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya siguen
> [T-AIENG-040](../../archive/2026-09-25-add-frontend-free-query-panel/ticket.md) y el resto de tickets
> del Proyecto Final.
>
> **Fuentes de verdad:** `openspec/project.md`, las specs vivas
> [`pos-projection`](../../../specs/pos-projection/spec.md),
> [`ai-service-runtime`](../../../specs/ai-service-runtime/spec.md),
> [`demo-deployment`](../../../specs/demo-deployment/spec.md) y
> [`ai-free-query-search`](../../../specs/ai-free-query-search/spec.md), y **el código real**, que es de
> donde sale todo lo que este ticket afirma.

**Change:** `add-pos-projection-scheduled-drain` (C41) · **Épica:** **EP14 — Búsqueda Semántica
Híbrida** *(corregido el 26 sep: este ticket decía EP15)*
**Abierto:** 2026-09-25 · **Enriquecido:** 2026-09-26, tras la exploración contra el código y contra la
base local · **Historia:** [HU-AIENG-041](../../../../Documentos/Historias/AI-Eng/HU-AIENG-041.md)
**Origen:** no es una historia de producto — sale de una **sesión de pruebas manuales** posterior al
cierre de C40, y eso condiciona cómo hay que leerlo.

---

## 0 · Qué pide este ticket, en una frase

Que **la frescura de `ai.pos_projection` deje de ser un acto manual**: un drenaje que corre **al
arrancar el servicio y cada diez minutos**, con lock, y la edad reportada **en la tarjeta de estado del
administrador**, que es donde se mira un dato de sistema.

---

## 0.1 · Lo que la exploración del 2026-09-26 corrige de este ticket

Seis cosas. Las tres primeras cambian el alcance; las tres últimas cambian lo que el ticket afirmaba.

| # | El ticket decía | Y es | Dónde queda |
|---|---|---|---|
| **1** | Épica **EP15** | **EP14.** La capability `pos-projection` nació en C22, que es de EP14. El criterio ya se aplicó a C40 — *«C40 es de EP15, aunque modifique la capability `assisted-search-panel` de esta épica»*: la épica la fija de qué trata el change | Cabecera, corregida |
| **2** | Tramo 1 en .NET, un `BackgroundService` | **En `jbg-ai`.** Lo que el ticket pedía no es un planificador: es **una segunda implementación del protocolo del keyset**, y como la spec obliga a conservar el CLI quedarían dos drenadores escribiendo la misma fila de checkpoint — la corrupción que este mismo ticket avisa, institucionalizada | **D1** |
| **3** | Tramo 2 «aditivo y pequeño» en `GET /api/ai/search/availability` | **Es el más caro de los tres.** Esa ruta tiene un `MUST` de spec viva que le prohíbe llamar al servicio de IA, y su método es síncrono. `GET /health` lleva el dato con **coste de contrato cero** | **D8** |
| **4** | «la edad de la proyección **de esa tienda**» (§2, tramo 2) | **La edad es global.** El checkpoint es `PRIMARY KEY (feed)`, como el propio §2 tramo 1 dice cuatro párrafos antes | **D13** |
| **5** | El lock protege «del solape consigo mismo y de cualquier disparo manual del tramo 3» | **Falta el caso que de verdad ocurrió: el CLI a mano.** Si el lock vive en el planificador, el CLI queda fuera y el riesgo declarado no se mitiga. Va **dentro** del drenaje | **D6** |
| **6** | «**Es la segunda vez**» | **Es la tercera**, y son dos modos de fallo distintos. C34 encontró la proyección **vacía** en la demo —`count_scope = 0`, **503 en toda recuperación**— y la deuda sigue abierta en `DEFERRED_TASKS.md` | **D9**, **D10** |

**Y un hallazgo que obliga a anotar un informe ya publicado:** la manipulación declarada en el §8 de
C40 **se aplicó a la columna equivocada** y no pudo funcionar. Ver §6.

---

## 1 · Contexto y problema

### Cómo se encontró, que importa para dimensionarlo

Al levantar el entorno para las pruebas manuales de C40, **ninguna de las once tiendas con surtido
tenía la proyección fresca**. El umbral es `JPV_POS_PROJECTION_MAX_AGE_SECONDS`, con defecto
**3.600 s**, y el *checkpoint* `ai.sync_checkpoint.last_incremental_sync_at` del feed `pos-availability`
venía del **5 de septiembre**: veinte días. Hubo que drenarlo a mano (`python -m jbg_ai.indexing
sync-pos --full`, 34 páginas, 6.050 *upserts*, 0 páginas fallidas) para que las pruebas midieran el
sistema y no su desconfiguración.

No es la primera vez, y **tampoco la segunda**. Son **tres**, y no todas del mismo modo de fallo:

| # | Cuándo | Entorno | Modo | Efecto |
|---|---|---|---|---|
| 1 | C34 | **demo** | Proyección **vacía** | `count_scope = 0` → **503 en toda recuperación**; .NET degrada a léxico con 200, *«así que desde fuera el entorno parece sano»*. Deuda abierta en [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) |
| 2 | C40 (§8 del informe) | local | **Rancia**, 19,7 días | `degraded=unscoped`. **Y el arreglo aplicado no funcionó** — ver §6 |
| 3 | C41 (este ticket) | local | **Rancia**, 20 días | `degraded=unscoped`. Arreglado con `sync-pos --full` |

**Tres sesiones distintas, la misma causa.** Eso es lo que convierte un detalle de operaciones en un
ticket.

### La causa real, mejor enunciada de lo que este ticket la enunciaba

El ticket decía *«la frescura no tiene dueño»*. Es más preciso decir esto:

> **El planificador existe y vive en prosa.** [`ai-service/README.md:330`](../../../../ai-service/README.md#L330)
> lleva desde C22 una receta de cron cada diez minutos, y **es inejecutable en la topología que
> desplegamos**: empieza por `cd /srv/jbg-ai`, una ruta de host, y `jbg-ai` se despliega como
> contenedor — la demo drena con `docker exec -i jbg-demo-ai …`. **Por eso nadie la instaló nunca.**

Y un agravante medido durante la exploración: **el arreglo manual caduca en una hora.** Un día después
del drenaje del 25 sep, el checkpoint marcaba **51.677 s de edad — 14,4 veces el techo**, y nadie lo
supo en catorce horas.

### Los dos incidentes locales ocurrieron *levantando el entorno*

No en producción, no con el sistema corriendo: **al arrancar, para ponerse a probar**. Eso tiene una
consecuencia de diseño que el ticket original no extraía:

> **Un cron de host no habría evitado ninguno de los tres**, porque no corre en el portátil de nadie; y
> un temporizador de 15 minutos deja una ventana abierta justo cuando se mide. **El disparo que mata
> los tres casos es el de arranque.** «El entorno está levantado» tiene que implicar «la proyección
> está fresca».

### Lo que la rancidez hace, y lo que NO hace

Conviene fijarlo antes de proponer nada, porque la primera lectura de este problema es alarmista y está
equivocada — la sesión que abrió este ticket la hizo y tuvo que corregirse.

**No es una fuga.** Un operario **nunca** ve una pieza que su tienda no lleva, pase lo que pase con la
proyección. Hay dos filtros y sólo uno es la frontera:

| | Dónde | Qué hace | ¿Frontera? |
|---|---|---|---|
| Prefiltro de `ai.pos_projection` | `retrieval/projection.py`, antes de ordenar | Estrecha la **ventana de candidatos** al surtido de la tienda | **No** |
| `Carried()` | [`AssistedSearchRepository.cs:156-162`](../../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/AssistedSearchRepository.cs) | Parte de `Inventories` con `PointOfSaleId == pointOfSaleId && IsActive && Product.IsActive` | **Sí** |

La segunda corre en **toda** respuesta, y su consulta arranca desde `Inventory` precisamente para que
la regla de visibilidad sea **estructural** y no una condición que alguien pueda olvidar. Es el
principio del §6.2 del diseño: *el servicio de IA propone candidatos; .NET calcula números y decide*.

**Lo que hace es que la página llegue corta.** Con la proyección rancia la ventana se dibuja sobre el
catálogo entero y .NET descarta después lo que la tienda no lleva. Eso es, literalmente, el
comportamiento de **antes de C22**, y C22 lo midió: **ocho de los once puntos de venta** caían por
debajo de una página en al menos **seis de cada veinte** búsquedas, y en el peor caso **sobrevivía un
solo producto**.

**Y degradar es la decisión correcta**, no un descuido. El *docstring* de
[`projection.py:139-142`](../../../../ai-service/src/jbg_ai/retrieval/projection.py) lo escribe así:

> **Stale** — older than the ceiling. The scope is dropped for this request and the age is reported.
> The page may come back short; **no valid product is hidden from the authority that hydrates it**,
> which is the promise staleness has to keep.

Filtrar con una proyección de veinte días esconderría las piezas asignadas después del último drenaje:
un **falso negativo invisible**. Mostrar candidatos de más es recuperable porque .NET los tira; esconder
algo vendible no lo es. **Este ticket no toca esa decisión.**

---

## 2 · Estado actual del código, verificado en el repositorio (2026-09-26)

| Pieza | Estado | Evidencia |
|---|---|---|
| `sync-pos [--full]`, checkpoint propio, *tombstone* en borrado suave, página fallida a `ai.sync_failure` | ✅ real desde C22, ~250 líneas comentadas y probadas | [`pos_orchestrator.py`](../../../../ai-service/src/jbg_ai/indexing/pos_orchestrator.py) |
| El guard de frescura lee `ai.sync_checkpoint.last_incremental_sync_at` | ✅ y **nunca** `refreshed_at` | [`search.py:79-83`](../../../../ai-service/src/jbg_ai/retrieval/search.py#L79-L83) |
| `resolve_scope` ya calcula `reported_age` y `stale` | ✅ **transportarlos, no computarlos** | [`projection.py:120-165`](../../../../ai-service/src/jbg_ai/retrieval/projection.py#L120) |
| `ProjectionFreshness`, caché de 10 s | ✅ mismo patrón y razón que el informe de salud de C17 | [`projection.py:80-105`](../../../../ai-service/src/jbg_ai/retrieval/projection.py#L80) |
| Receta de cron cada 10 min | ⚠️ **existe en prosa y es inejecutable** (`cd /srv/jbg-ai`) | [`README.md:330`](../../../../ai-service/README.md#L330) |
| `verify.sh` falla el despliegue por cuatro condiciones | ⚠️ **ninguna es la proyección** | [`verify.sh`](../../../../deploy/demo/verify.sh) |
| `GET /health` es *mapping* abierto en los dos lados | ✅ **enriquecerlo no mueve el contrato** | [`health_report.py`](../../../../ai-service/src/jbg_ai/api/health_report.py) · [`AiHealthResponse.cs`](../../../../backend/src/JoiabagurPV.Application/DTOs/Ai/AiHealthResponse.cs) |
| Tarjeta de estado de `jbg-ai` en el dashboard de administrador | ✅ desde C17, con `unreachable` de primera clase | [`AdminDashboard.tsx`](../../../../frontend/src/pages/dashboard/AdminDashboard.tsx) |
| .NET lee o escribe el esquema `ai` | ❌ **cero referencias** en todo `backend/src` | — |
| La frontera `ai.*` está acotada por *grants* | ✅ estructural, no convencional | [`bootstrap.sql`](../../../../ai-service/migrations/bootstrap.sql) |
| `GET /api/ai/search/availability` no llama al servicio de IA | ✅ **`MUST` de spec viva**; además el método es **síncrono** | [`ai-free-query-search/spec.md`](../../../specs/ai-free-query-search/spec.md) |
| Superficie `/v1`: 11 rutas más `/health`, enumeradas en un `MUST` | ✅ añadir una es cambio normativo | [`openapi.json`](../../../../ai-service/openapi.json) |
| `pos-projection` prohíbe el planificador en proceso | ⚠️ **es lo que este change deroga** | [`pos-projection/spec.md`](../../../specs/pos-projection/spec.md) |
| Lock de cualquier tipo | ❌ **no existe ninguno** en todo el repositorio | — |
| `uvicorn` sin `--workers`, `mem_limit: 512m`, pool de 5 | ✅ instancia única **en la práctica**, no por garantía | [`Dockerfile`](../../../../ai-service/Dockerfile) |

**Estado de la base local, medido el 26 sep** (lectura, sin modificar nada):

```
feed             | last_incremental_sync_at      | last_full_sync_at             | indexed_count
pos-availability | 2026-09-25 20:49:24.836539+00 | 2026-09-25 20:49:24.836539+00 |          6720
                   edad: 51.677 s → STALE (14,4 × el techo de 3.600 s)

is_assigned_hint = true : 6.050    false : 670
12 puntos de venta en la proyección; uno (cd9bfd1f…) con 0 asignados sobre 144 filas → 503
94 filas con computed_as_of = 2026-09-25 05:32:04  ← huella del UPDATE manual de C40
```

---

## 3 · Lo que se pide

### Tramo 1 · El drenaje programado (el núcleo, no se corta) · `ai-service/`

Una tarea de fondo en el `lifespan` de FastAPI que reutilice `sync_pos_availability` **tal cual**:

- **Al arrancar**: completo si no hay checkpoint (cura el caso de C34), incremental si lo hay (cura
  C40 y C41). **No bloquea el arranque** ni `/health`.
- **Por intervalo**: incremental cada **600 s**, por configuración.
- **Con lock, o no se construye**: `pg_try_advisory_lock` **no bloqueante**, **dentro** del drenaje
  para que lo hereden el CLI y el planificador.
- **Un fallo no rompe nada**: registro y reintento acotado; nunca tumba el arranque.
- **`failed_pages` no se traga**: se reporta, heredando la lectura del CLI — *«una página que falló es
  una página que nadie drenó; reportar éxito dejaría que una proyección parcialmente sincronizada
  pareciera completa»*.

### Tramo 2a · La edad dicha donde ya hay pantalla · `ai-service/`, `backend/`, `frontend/`, `deploy/demo/`

- `GET /health` gana una sección `projection`: edad desde el **checkpoint**, último drenaje, último
  completo, `stale` contra el techo configurado, páginas fallidas y **cuántos puntos de venta de la
  proyección no tienen ni una fila asignada**.
- `AiHealthResponse` y `ai-health.types.ts` la transportan; la tarjeta del dashboard la pinta.
- `verify.sh` gana un **quinto** motivo de fallo: proyección vacía. Cierra la deuda de C34.

### Tramo 3 · Documentación que queda falsa, retirada y no matizada

`ai-service/README.md:325-330` (con su receta de cron), `ai-service/README.md:1229` y
`openspec/project.md:372`.

---

## 4 · Lo que este ticket declara y no pide

- **No cambia la decisión de degradar** ante una proyección rancia. Es correcta y está argumentada.
- **No toca `Carried()`** ni la frontera de autorización.
- **No añade migración**: ni Alembic ni EF Core.
- **No mueve el contrato congelado**: ninguna ruta bajo `/v1`, y `test_openapi_snapshot_is_stable` debe
  pasar contra el `openapi.json` **ya commiteado**.
- **No toca `GET /api/ai/search/availability`**, cuyo `MUST` de no llamar al servicio de IA se conserva.
- **No propone botón para el operario, y tampoco para el administrador.** El argumento que mata el
  primero mata también el segundo: con el tramo 1 hecho, «refrescar ahora» ahorra como mucho diez
  minutos. El único caso que ningún intervalo cubre es el **completo**, y para eso basta la tarjeta
  informando y el `docker exec` documentado al lado.
- **No re-mide el grupo 8 de C40.** Lo **anota**. Ver §6.
- **No limpia las 94 filas residuales.** Son la prueba forense y son inofensivas.

---

## 5 · Una nota de método, porque costó una corrección — dos veces

**La frescura NO se mide leyendo `MAX(refreshed_at)` de las filas.** El guard lee
`ai.sync_checkpoint.last_incremental_sync_at`, y el *docstring* de `projection.py` advierte
explícitamente del error: el feed es **incremental por keyset**, así que una asignación que no cambia
nunca se re-emite y `refreshed_at` registra cuándo cambió **la asignación**, no cuándo se miró la
proyección. Leerlo de las filas *«reportaría meses de rancidez sobre una proyección sincronizada hace
treinta segundos, y el guard desactivaría el ámbito sobre una proyección perfectamente al día, de forma
permanente»*.

La sesión que abrió este ticket cometió ese error **al diagnosticar**; la conclusión resultó correcta
por casualidad, porque el checkpoint venía del mismo drenaje del 5 de septiembre que las filas. **Y la
sesión de C40 lo cometió al arreglar** — ver §6. Dos veces, en dos sentidos distintos. **Cualquier
verificación de este change lee el checkpoint.**

---

## 6 · El hallazgo que obliga a anotar el informe de C40

El §8 del [informe de C40](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md)
declara: *«La proyección del punto de venta se refrescó. Llegaba con 19,7 días y el servicio la
declaraba `degraded=unscoped` […] Se actualizaron `refreshed_at` y `computed_as_of` en 1.176 filas»*.

**El guard no lee `refreshed_at`. Lee el checkpoint. La manipulación no pudo funcionar.** Cuatro piezas
lo cierran:

| Evidencia | Valor |
|---|---|
| `ai.sync_checkpoint` · `pos-availability` | `last_incremental_sync_at` = `last_full_sync_at` = **2026-09-25 20:49:24 UTC**. Los dos iguales ⇒ el único drenaje fue el `--full` de la sesión de C41 |
| Artefacto `c40-dotnet-latency-42.json` | `measured_at` = **2026-09-25T05:42:42.933Z** — **15 h 07 min antes** de ese drenaje |
| Filas con la huella del `UPDATE` | **94**, todas con `computed_as_of = 2026-09-25 05:32:04` — diez minutos antes de que empezara la medición |
| «1.176 filas» | Es el **total exacto de filas del POS `0388f003…`**: 1.082 asignadas + esas 94 |

Un drenaje sólo avanza el checkpoint, nunca lo retrocede, así que a las 05:42 seguía en el 5 de
septiembre ≈ **19,9 días**, que es el «19,7» que el informe declara. **Las cifras del grupo 8 se
tomaron con el ámbito de punto de venta caído.**

**Qué se sostiene y qué no:**

| Cifra | ¿Se sostiene? | Por qué |
|---|---|---|
| p50 3.404 / p95 7.160 / 0 de 42 fuera de presupuesto | ✅ **Sí** | Sin ámbito el SQL es 2-3 ms más lento (C22: 7,3 ms con CTE contra 8-11 ms) contra un p95 dominado por dos llamadas a proveedor. **Y está verificado que .NET no repide** cuando la página llega corta: `AssistedSearchService` hace una sola llamada con `CandidateWindow` fijo, así que no hay viaje extra |
| Coste de la capa .NET, 17 ms en p95 | ✅ Sí | Por diferencia contra `usage.totalMs`; no depende del ámbito |
| Reparto de los 16 estados sobre 71 consultas | ⚠️ **Describe el sistema degradado** | Sin ámbito, .NET recibe candidatos que la tienda no lleva y `Carried()` los tira. Los estados que dependen de un conjunto corto o vacío pueden haberse desplazado — y la dirección es conocida: **más** masa en los de resultado escaso |
| «Estado 15 a cero en las 71» | ✅ Sí | Es ausencia de marcadores en el argumentario; otro conjunto de candidatos no los crea |

**Daño colateral, declarado:** ese `UPDATE` estampó `computed_as_of = now()`, rompiendo el reloj
inyectado `IndexFeed:SalesAsOf = 2026-08-23T23:59:59Z` que C22 instaló para que `sales_30d` fuera
reproducible. La spec exige `computed_as_of` **por fila** precisamente para que una mezcla de relojes
sea *visible en vez de silenciosa*. Funcionó: 94 filas siguen declarando el segundo reloj.

**Y el remate, que es la tesis de este ticket con factura:** en las 42 filas del artefacto,
`degraded_reason` es **`null` las 42 veces** — no porque no hubiera degradación, sino porque **.NET no
tiene campo para la degradación de la proyección**, sólo para la suya. La prueba existía únicamente en
el log del contenedor. *Un dato que el sistema conoce, paga y descarta en la frontera.*

**Decisión (D15): se anota, no se rehace.** El arnés del grupo 8 **no está en el árbol** —el commit
`be45e07` añadió sólo el informe y los dos artefactos—, así que rehacerlo significa **reescribirlo**;
el dinero de proveedor sería ≈ 0,65 USD las 71 consultas y es irrelevante al lado de eso. Y rehacerlo
**hoy** reproduciría el defecto, porque el entorno ya está a 14,4 veces el techo. La secuencia correcta
es **primero C41**; si C39 lo pide, la remedición se hace después y sobre un entorno que se drena solo.

---

## 7 · Componentes Afectados

| Componente | Qué cambia |
|---|---|
| **`ai-service/src/jbg_ai/indexing/`** | El lock dentro del camino de drenaje y el planificador de arranque e intervalo. `pos_orchestrator.sync_pos_availability` **no se reescribe** |
| **`ai-service/src/jbg_ai/api/`** | `lifespan` crea la tarea (sin esperarla); `health_report.py` gana la sección `projection` |
| **`ai-service/src/jbg_ai/config/settings.py`** | Dos ajustes nuevos con el patrón `blank_*_is_default`; **ninguno** se fija en `canonical_openapi_settings()` |
| **`ai-service/src/jbg_ai/retrieval/search.py`** | Una lectura de conteo por punto de venta para `shops_without_scope`. `PROJECTION_SYNCED_AT_SQL` se **reutiliza** |
| **`backend/src/JoiabagurPV.Application/DTOs/Ai/`** | `AiHealthResponse` gana `AiHealthProjection`, **tolerante a su ausencia** |
| **`frontend/src/types/` y `src/pages/dashboard/`** | `ai-health.types.ts` y la tarjeta con sus tres estados |
| **`deploy/demo/verify.sh`** | Quinto motivo de fallo del despliegue |
| **`openspec/specs/`** | `pos-projection` (MODIFIED), `ai-service-runtime`, `demo-deployment` |
| **`Documentos/` y READMEs** | Tres frases falsas retiradas, `epicas.md`, ficha del plan y anotación del informe de C40 |
| **NO se toca** | `ai-service/openapi.json` · `AiSearchController.Availability` · `Carried()` · migraciones · `backend/` fuera del DTO de salud |

---

## 8 · Especificaciones Técnicas

### ai-service · el lock

`pg_try_advisory_lock` sobre una **conexión dedicada retenida durante todo el drenaje**, con clave
**constante y documentada** (no `hashtext`, que no garantiza estabilidad entre versiones y cambiaría la
clave en silencio, desactivando el lock sin fallar). No bloqueante: el segundo drenaje **declina y lo
registra** con su `trace_id`, en vez de encolarse — encolar temporizadores es cómo se construye una
estampida. Coste declarado: **1 de las 5 conexiones del pool** mientras dura el drenaje.

**Va dentro del camino de drenaje**, no en el planificador, para que el CLI quede cubierto. Un mutex de
aplicación **no sirve**: no ve al CLI, que corre en otro proceso. Un `SELECT … FOR UPDATE` sobre el
checkpoint **tampoco**: el drenaje son 34 transacciones, no una.

### ai-service · el planificador

Tarea creada en el `lifespan` y **no esperada**. El `HEALTHCHECK` del Dockerfile sondea `/health` con
3 s de tope y `compose.demo.yaml` encadena `depends_on: service_healthy`: esperar un completo de 34
páginas contra un presupuesto de 180 s marcaría el contenedor *unhealthy* y **tumbaría el despliegue
por culpa de la mejora**.

Arranque: `resolve_start_cursor` ya devuelve `(None, None)` sin checkpoint e `is_full` se calcula solo,
así que «completo si no hay checkpoint» **es gratis**. Feed caído: retroceso acotado, registro por
intento, y al primer tick del intervalo el problema deja de ser especial.

### ai-service · los ajustes

`JPV_POS_SYNC_SCHEDULER_ENABLED` (defecto **true**) y `JPV_POS_SYNC_INTERVAL_SECONDS` (defecto
**600**). Prefijo `jpv_pos_*`, igual que `jpv_pos_prefilter_enabled` y
`jpv_pos_projection_max_age_seconds`.

**Los 600 s son derivados, no elegidos.** Lo que importa es cuántos fallos seguidos se toleran antes de
que el guard degrade: con techo de 3.600 s, la regla `techo / intervalo ≥ 4` da ≤ 900 s. **600 s tolera
cinco**, y además empata con la receta del README y con el §6.3 del diseño (*«cada 5-10 min»*).

**Apagar el conmutador restaura exactamente el comportamiento previo**, que es la ablación y el
*rollback* a la vez.

### ai-service · la sección `projection` de `GET /health`

Campos: instante del último drenaje y del último completo, edad en segundos **desde el checkpoint**,
`stale` contra el techo **configurado en ese servicio**, páginas fallidas y `shops_without_scope`.

**La edad y el booleano no son redundantes**: la edad informa, el booleano dice qué decidió el guard
contra su propio techo. Derivarlo en el cliente duplicaría el umbral, que es justo lo que había que
evitar. **Y la edad se nombra como lo que es: la del drenaje, global.** El checkpoint es una fila por
feed.

`shops_without_scope` se cuenta **contra los puntos de venta que aparecen en la proyección**, porque
Python **no lee `public` por SQL**: contarlo contra los activos de .NET exigiría una consulta al feed
que este change no abre.

### backend y frontend · el transporte y la tarjeta

DTO y tipos **tolerantes a la ausencia** de la sección: un `jbg-ai` anterior a este change no la manda,
y el propio `AiHealthResponse` declara que *«an unrecognised field is ignored rather than fatal»*.

Tres estados en la tarjeta —fresca, rancia, sin ámbito—, en **es-ES**. La copia es de **completitud, no
de corrección**: «puede que falten resultados» es cierto; «los resultados no son fiables» es falso y es
la alarma que C36 evitó con `size_label_missing`. Edad en lenguaje natural, valor exacto en el `title`.

### deploy · el quinto fallo de `verify.sh`

Proyección vacía ⇒ despliegue fallido. Hoy *«un entorno con índice lleno y proyección vacía pasa la
verificación posterior al despliegue»*, según su propia entrada de `DEFERRED_TASKS.md`. Se ejerce de
verdad: **la demo se vuelve a desplegar antes de la entrega**.

### Specs de OpenSpec

`pos-projection` · **MODIFIED**: deroga *«MUST NOT start an in-process scheduler or background task»*
**refutando a C22 con números**, no ignorándolo:

- *«un contenedor limitado a 512 MiB compitiendo por un pool de cinco conexiones»* → un incremental
  toca 0-1 páginas de ≤200 ítems y retiene **una** conexión durante segundos, cada 600 s.
- *«`api-contracts` enumera la superficie `/v1` en un MUST»* → **no aplica a un planificador**, sólo a
  una ruta. Este change no añade ninguna.
- *«la honestidad viene de `projection_age_seconds`, no de un cron oculto»* → **es la tesis que este
  change derriba**: la honestidad existió durante veinte días y no llegó a ninguna pantalla.

`ai-service-runtime` y `demo-deployment` · requisitos nuevos para la sección de salud y el quinto fallo.

> ⚠️ La descripción de cada requisito va en **una sola línea física**. Si el `SHALL` cae a la segunda
> por ajuste de ancho, el validador falla con *«must contain SHALL or MUST»* y el mensaje no dice que
> el problema es tipográfico.

---

## 9 · Arquitectura

**La decisión que arrastra a todas las demás es dónde vive el drenaje**, y la pregunta del ticket
original —*«¿.NET o Python?»*— estaba mal planteada: el drenaje tiene **dos mitades con dueños
distintos**.

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

| Opción | Contrato | Spec viva | Frontera `ai.*` | ¿Arregla dev local? | Veredicto |
|---|---|---|---|---|---|
| **A** · .NET drena entero | — | `pos-projection` | **Rota — grants** | ✅ | ❌ **Duplica el protocolo del keyset.** Y como la spec obliga a conservar el CLI, quedan **dos drenadores sobre la misma fila de checkpoint** |
| **B** · .NET programa, Python ejecuta por ruta `/v1` | **Ruta 13** | `api-contracts` | — | ✅ | ❌ Mueve el contrato congelado, y HU-AIENG-022 ya rechazó `POST /v1/index/sync-pos` por escrito |
| **D** · cron de host o *sidecar* | — | — | — | ❌ / ⚠️ | ❌ **Es lo que ya existía y falló.** Nada en la aplicación sabe que el drenaje existe |
| **E** · Python programa y ejecuta, arranque + intervalo | — | `pos-projection` | — | ✅ | ✅ **Elegida (D1, D2)** |

**Por qué E y no A**, que era lo que el ticket pedía: A es más cómoda hoy —acoplamiento de ciclo de
vida perfecto, el tramo 2 se vuelve local, el botón sería una llamada a un método— y **peor dentro de
seis meses**, porque duplica un protocolo cuyo modo de fallo es *saltarse filas en silencio*. Y exige
otorgar al rol de la API privilegios sobre `ai`, debilitando para siempre una frontera que
`bootstrap.sql` hace **estructural** — *«make the boundary the default rather than a convention»*.

**Patrones reutilizados:** el `lifespan` de FastAPI, `session_scope`, `ProjectionFreshness` y su caché
corta, el informe de salud de C17 con su *mapping* abierto, y `sync_pos_availability` sin tocar.

**Breaking changes:** ninguno. El contrato congelado no se mueve, no hay migración, y la sección nueva
del informe de salud es aditiva en los dos lados.

---

## 10 · Criterios de Aceptación

Los diez escenarios en Dado/Cuando/Entonces están en la historia
[HU-AIENG-041](../../../../Documentos/Historias/AI-Eng/HU-AIENG-041.md#criterios-de-aceptación). En
resumen: el entorno se drena al arrancar (1, 2), se mantiene fresco solo (3), dos drenajes no se pisan
**y el CLI tampoco** (4), el administrador ve la frescura (5), un fallo no rompe nada y no se traga
(6), un despliegue con la proyección vacía ya no pasa (7), la rancidez sigue degradando y nunca
escondiendo (8), **el contrato congelado no se mueve** (9) y el fuera de alcance es explícito (10).

---

## 11 · Definición de Hecho (DoD)

- [ ] Planificador de arranque e intervalo implementado en `ai-service/`, **sin reescribir**
      `sync_pos_availability`
- [ ] `pg_try_advisory_lock` no bloqueante **dentro** del camino de drenaje, con test que demuestra
      que **el CLI también queda cubierto**
- [ ] El arranque **no se bloquea**: `GET /health` responde 200 durante todo el drenaje inicial, con
      test
- [ ] Sección `projection` en `GET /health`, leída del **checkpoint** y nunca de `refreshed_at`
- [ ] `AiHealthResponse` / `ai-health.types.ts` / tarjeta del dashboard, los tres tolerantes a la
      ausencia de la sección
- [ ] `verify.sh` falla con la proyección vacía; entrada de `DEFERRED_TASKS.md` cerrada
- [ ] `uv run pytest` en verde **sin llamadas reales a proveedor, embeddings ni RDS**
- [ ] **`test_openapi_snapshot_is_stable` pasa contra el `openapi.json` ya commiteado, sin
      regenerarlo**, y su `sha256` coincide con el anotado en la puerta de entrada
- [ ] Backend: xUnit + FluentAssertions, nomenclatura `Método_Escenario_ResultadoEsperado`
- [ ] Frontend: Vitest + RTL, nomenclatura `should [comportamiento] when [condición]`, queries
      accesibles
- [ ] **Línea base de las tres suites por nombres de test, no por número**; cero nombres rojos nuevos
      en el área propia
- [ ] Specs actualizadas y `openspec validate --all --strict` con **0 failed**
- [ ] **Ninguna migración** de Alembic ni de EF Core
- [ ] **Ninguna ruta nueva** bajo `/v1`; `GET /api/ai/search/availability` sin tocar
- [ ] Las tres frases falsas retiradas de los READMEs y de `openspec/project.md`
- [ ] Informe de C40 **anotado** —firmado y fechado como anotación posterior de C41—, **sin tocar
      ningún número ni ningún artefacto**
- [ ] `Documentos/epicas.md`, ficha del plan (**con la corrección de zona**) y `deploy/demo/README.md`
      al día
- [ ] UI en español (es-ES)
- [ ] Sin TODO/FIXME sin tarea de seguimiento

---

## 12 · Requisitos No Funcionales

- **Seguridad.** Ningún cambio en autorización. El drenaje se autentica con `X-Index-Feed-Key`, como
  ya hace el CLI. La sección nueva del informe de salud describe **estado**, nunca secretos: no viaja
  cadena de conexión, ni host, ni fragmento de credencial. `GET /api/ai/health` sigue siendo **sólo
  administrador**. **La frontera `ai.*` no se debilita**: .NET no gana ni un privilegio.
- **Rendimiento y free-tier.** El lock retiene **1 de 5 conexiones** mientras dura el drenaje
  (declarado). Un incremental toca 0-1 páginas de ≤200 ítems. La lectura de frescura en la ruta de
  recuperación **no gana round trips**: se reutiliza `ProjectionFreshness` con su caché de 10 s.
  `mem_limit: 512m` respetado: la tarea no mantiene estado entre ticks.
- **Observabilidad.** Toda línea del planificador lleva `trace_id` —el drenaje ya genera el suyo con
  `new_trace_id()`, precisamente porque *«una página que falló … sin un id, las entradas de dos
  ejecuciones solapadas son indistinguibles»*—. Se registran: drenaje de arranque y su modo, lock
  declinado, feed caído con su reintento, y `failed_pages`. **Ningún vector en los logs.**
- **Integridad de datos.** El keyset **no puede entrelazarse**: es la invariante que el lock protege y
  la razón de que el tramo 1 no se construya sin él. `failed_pages` no se presenta como éxito. El
  reloj inyectado `IndexFeed:SalesAsOf` **no se toca**, y la mezcla de relojes que dejó C40 se declara
  en vez de borrarse.
- **Degradación.** Un fallo del drenaje **nunca** tumba el arranque ni `GET /health`. La rancidez
  conserva su comportamiento: el ámbito se cae, la edad se reporta y **ningún producto válido se
  esconde**.

---

## 13 · Preguntas Abiertas → Decisiones (cerradas antes de los artefactos de OpenSpec)

Las seis del §4 original, cerradas:

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿.NET o `jbg-ai`? | **`jbg-ai`** (D1). La pregunta estaba mal planteada: decide quién sostiene las dos mitades **sin duplicar el protocolo** |
| 2 | ¿Cómo se implementa el lock? | **`pg_try_advisory_lock` dentro del drenaje** (D6, D7), para que cubra al CLI |
| 3 | ¿Incremental por defecto? | **Sí, más completo automático sin checkpoint** (D5), que es gratis y cura el caso de C34 |
| 4 | ¿Edad en segundos o booleano `stale`? | **Los dos**, y no es redundancia: la edad informa, el booleano dice qué decidió el guard contra **su** techo |
| 5 | ¿El tramo 3 reutiliza el servicio o expone el CLI? | **Ninguno: se corta** (D12) |
| 6 | ¿Qué dice la insignia? | **No hay insignia de operario** (D11). Tres estados en la tarjeta de administrador, y el aviso es de **completitud, no de corrección** |

Las siete que quedan abiertas, con su opción por defecto, están en la
[historia](../../../../Documentos/Historias/AI-Eng/HU-AIENG-041.md#preguntas-abiertas): nombres de los
ajustes, conmutador encendido por defecto, clave del lock, reintento del arranque, base de conteo de
`shops_without_scope`, formato de la edad en la tarjeta y firma de la anotación del informe de C40.

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
añada ruta bajo `/v1`, **no** regenere `openapi.json`, **no** abra migración, **no** haga que .NET lea
ni escriba el esquema `ai`, y **no** cambie el comportamiento de degradación.

---

## 14 · Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Alta.** La demo se vuelve a desplegar antes de la entrega, así que el drenaje de arranque y el quinto fallo de `verify.sh` se ejercen en esa ventana. Y **cualquier remedición futura depende de esto** |
| **Impacto** | 4/5 — cierra un modo de fallo que ha costado **tres sesiones** y que invalidó parcialmente una medición publicada |
| **Complejidad** | 3/5 — el drenaje **ya existe y no se reescribe**; la dificultad es derogar un `MUST NOT` deliberado **con refutación numérica** y no romper la afirmación de que el contrato no se mueve |
| **Estimación** | _Pendiente_ — a fijar en refinamiento |
| **Tags** | `ai-service` · `pos-projection` · `scheduler` · `advisory-lock` · `health-report` · `demo-deployment` · `no-contract-change` · `no-migration` |

---

## 15 · Enlaces o Referencias

- **Historia origen:** [HU-AIENG-041](../../../../Documentos/Historias/AI-Eng/HU-AIENG-041.md)
- **Change:** `openspec/changes/add-pos-projection-scheduled-drain/` (C41)
- **Ficha del plan:** [§3 · C41](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Diseño RAG:** [§6.2, §6.3, §7.6, §12](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Specs vivas modificadas:** [`pos-projection`](../../../specs/pos-projection/spec.md) ·
  [`ai-service-runtime`](../../../specs/ai-service-runtime/spec.md) ·
  [`demo-deployment`](../../../specs/demo-deployment/spec.md)
- **Specs que NO se tocan, y es alcance:**
  [`ai-service-api-contracts`](../../../specs/ai-service-api-contracts/spec.md) ·
  [`ai-free-query-search`](../../../specs/ai-free-query-search/spec.md) ·
  [`vector-retrieval`](../../../specs/vector-retrieval/spec.md)
- **Historias anteriores:** [HU-AIENG-022](../../../../Documentos/Historias/AI-Eng/HU-AIENG-022.md) ·
  [HU-AIENG-017](../../../../Documentos/Historias/AI-Eng/HU-AIENG-017.md)
- **Deuda que cierra:** [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md), entrada de C34
- **Informe a anotar:**
  [`c40-implementation-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md), §8
- **Procedimientos:**
  [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) ·
  [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Testing:** [testing-backend.md](../../../../Documentos/testing-backend.md) ·
  [testing-frontend.md](../../../../Documentos/testing-frontend.md)

---

## 16 · Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-25 | Apertura del ticket tras las pruebas manuales posteriores al cierre de C40 |
| 2026-09-26 | **Enriquecido con la exploración verificada contra el código y contra la base local.** Épica corregida de EP15 a **EP14**. Quince decisiones cerradas y las seis preguntas del §4 respondidas. **El tramo 1 se mueve de .NET a `jbg-ai`** y gana el disparo de arranque; **el tramo 2 se mueve de `GET /api/ai/search/availability` a `GET /health`**; **el tramo 3 se corta** con su razón escrita. Se añade el **tercer incidente** (C34, proyección vacía en la demo) y el quinto fallo de `verify.sh` que lo caza. Se corrige que **el lock va dentro del drenaje**, no en el planificador, y que **la edad es global y no por tienda**. Se documenta el **§6**: la manipulación del §8 de C40 se aplicó a la columna equivocada, con las cuatro pruebas, y se decide **anotar y no rehacer** |
