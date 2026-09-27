# Prompt para verificar C41 en una sesión nueva

Copia desde la línea siguiente hasta el final del documento y pégalo en un chat nuevo de Claude
Code, abierto en la raíz del repositorio y en la rama `c41-add-pos-projection-scheduled-drain`.

---

/opsx:verify add-pos-projection-scheduled-drain

Verifica C41 en la rama `c41-add-pos-projection-scheduled-drain`. La rama está publicada y el árbol
está limpio. **No implementes nada y no arregles nada**: este encargo es producir un informe de
verificación. Si encuentras algo que arreglar, lo listas con su recomendación y paras.

La implementación declara **32 de 32 tareas** y está en el commit **`13c86b9`**. La base contra la que
se compara todo es **`55bacb6`** —los artefactos de partida: historia, ticket enriquecido,
`epicas.md` y ficha del plan—. `git diff --stat 55bacb6..HEAD` da **32 ficheros, +3.673 / −72**.

**Qué hace este change, en una frase:** `ai.pos_projection` se drena **sola al arrancar `jbg-ai` y
cada 600 s**, con un *advisory lock* no bloqueante, y su edad llega a la tarjeta de estado del
administrador vía `GET /health`. **Sin ruta nueva bajo `/v1`, sin regenerar `openapi.json`, sin
migración, y sin botón de refresco para nadie.**

## Lee esto antes de emitir un solo juicio

1. `openspec/changes/add-pos-projection-scheduled-drain/tasks.md` — 9 grupos, 32 tareas, todas
   marcadas. **Tres de ellas están marcadas con su razón escrita en la propia línea** porque no se
   ejecutaron como estaban redactadas (1.3, 7.2, 7.4). Léelas antes de abrir un CRITICAL por ellas.
2. `openspec/changes/add-pos-projection-scheduled-drain/specs/**/spec.md` — **3 ficheros, 6
   requisitos** (3 `## MODIFIED` y 3 `## ADDED`), **28 escenarios**. Es el contrato.
3. **`openspec/changes/add-pos-projection-scheduled-drain/qa.md` — el registro de QA del
   implementador, 10 secciones.** Es donde están las cifras, las salvedades y **seis incidencias que
   el propio implementador se abrió**. Leerlo entero antes de abrir un CRITICAL te ahorrará casi
   todos los falsos positivos.
4. `openspec/changes/add-pos-projection-scheduled-drain/design.md` — **15 decisiones (D1–D15)** y 7
   preguntas ya resueltas. **No se reabren**: si la implementación las respeta, eso es coherencia y
   no conformismo. Lo que sí es tu trabajo es comprobar que **la implementación hace lo que la
   decisión dice**.
5. `Documentos/Proyecto Final AIEng/informes/c41-implementation-measurements.md` — las mediciones
   contra la base y el feed reales.
6. `Documentos/Historias/AI-Eng/HU-AIENG-041.md` — 10 escenarios de aceptación en Dado/Cuando/Entonces.
7. `openspec/project.md` y **`CLAUDE.md`** — convenciones y, sobre todo, las trampas del repositorio.
   **`CLAUDE.md` no es opcional aquí**: cuatro de las trampas de abajo están escritas en él.

## Siete trampas que te harán concluir algo falso si no las sabes

Cada una produce un veredicto **incorrecto** con toda naturalidad.

1. **`dotnet test` sale 0 sin ejecutar un solo test si algo bloquea `bin/Debug`.** Un
   `JoiabagurPV.API.exe` corriendo lo hace. **Lee la línea de resumen, nunca el código de salida.**
   Y ejecútalo contra `backend/src/JoiabagurPV.sln`, **no contra la raíz del repo**, que falla con
   `MSB1003` y también sale 0. Esta trampa **bloqueó la medición durante la implementación** y está
   documentada en el §8.5 del `qa.md`.

2. **Las tres suites no parten de cero rojos. Compara por NOMBRES, nunca por número.**
   - `ai-service` (pytest) **sí parte de cero**: 1.625 antes, **1.649 passed · 0 failed** al cierre.
     Aquí un rojo sí es un hallazgo.
   - `frontend` viene roja de fábrica y **oscila**: tres pasadas sobre este mismo árbol dieron
     **119 / 114 / 119** fallos en **17 / 15 / 18** ficheros. `CLAUDE.md` lo documenta en 113-114
     sobre 729 tests y el árbol ha crecido a 854. **El recuento no dice nada.** Lo que dice algo es
     si algún fichero rojo pertenece al área de este change, que son exactamente dos:
     `frontend/src/pages/dashboard/AdminDashboard.tsx` y `frontend/src/types/ai-health.types.ts`.
   - `backend` viene roja de fábrica: la línea base es **45 de 1.329**, tomada el 2026-09-26 a las
     02:11 —nueve horas antes de empezar este change— y conservada en
     `backend/src/JoiabagurPV.Tests/TestResults/baseline.trx`, que **no está en git**. Hay *churn*
     documentado entre pasadas del mismo commit, concentrado en `InventoryIntegrationTests`,
     `PaymentMethodsControllerTests` y `ReturnsControllerTests`. El criterio útil es **si el nombre
     discrepante cae en esas clases y si el área del change está limpia**.

   **El cierre ya está medido: 1.347 tests · 1.299 correctas · 48 con error**, con la API parada, en
   19 m 51 s. Comparado por nombres: **6 entran, 3 salen, y 8 de los 9 están en
   `InventoryIntegrationTests`**; el noveno está en `SalesControllerTests`, que ya traía cuatro
   fallos en la base. El área .NET de este change son exactamente dos clases —
   `UnitTests/Application/AiGatewayHealthTests` e `IntegrationTests/AiHealthControllerTests`— y da
   **7 de 7 en verde**, sin aparecer ni en los 45 de la base ni en los 48 del cierre.

   **El recuento total sube de 1.329 a 1.347 y no es de este change**: el `baseline.trx` es de antes
   de que C40_FIX cerrara, y su propio QA registra que pasó de 1.329 a 1.339 tests y de 45 a 52
   fallos. Contra **su cierre**, este árbol da cuatro fallos menos. Compruébalo: `git status
   --porcelain backend/src/JoiabagurPV.Tests/` debe salir vacío en el diff del change, porque **no
   se añadió ni se modificó un solo test .NET**.

3. **`vitest` sale 0 cuando lo canalizas.** `npm run test | tail` devuelve el código de `tail`. Un
   prompt verde no significa nada; lee el resumen.

4. **No captures las suites a través de `tail`.** El implementador lo hizo dos veces y perdió los
   nombres de la línea base del frontend — está confesado en el §1.3 del `qa.md`. Si vas a comparar
   por nombres, captura la salida entera.

5. **`uv` necesita `--system-certs` en esta máquina**, o PyPI falla con `UnknownIssuer`. **No hace
   falta PEM para nada de este change**: el drenaje de POS **no embebe** y no llama a ningún
   proveedor. Si ves una llamada a proveedor en este change, es un hallazgo.

6. **La frescura NO se mide con `MAX(ai.pos_projection.refreshed_at)`.** El guard lee
   `ai.sync_checkpoint.last_incremental_sync_at`. Esta confusión **ya ha costado dos sesiones** —una
   diagnosticando y otra *reparando* con la columna equivocada, lo que invalidó parcialmente una
   medición publicada de C40—. Si verificas la frescura contra la base, **lee el checkpoint**.

7. **`openspec validate --all --strict` valida estructura, no verdad.** Daba **63 passed · 0 failed**
   mientras una delta se dejaba cinco escenarios que habría borrado de la spec viva al sincronizar
   (§8.2 del `qa.md`). **El validador en verde no es evidencia de que las deltas estén bien.**
   Compruébalas a mano, y ver el punto siguiente para cómo.

## Cómo comprobar las deltas, porque la forma ingenua da 41 falsos positivos

Un `## MODIFIED` **reemplaza el requisito entero**, escenarios incluidos. Si la delta reproduce menos
escenarios de los que tiene el requisito vivo, sincronizar los borra.

**La comparación tiene que acotarse al requisito**, no al fichero: comparar los escenarios del
fichero delta contra los del fichero vivo entero devuelve decenas de «perdidos» falsos, y un defecto
real se esconde en ese ruido. Extrae los escenarios **bajo cada cabecera `### Requirement:` concreta**
a los dos lados y compara esos conjuntos.

Los tres requisitos `## MODIFIED` y su capability viva:

| Capability | Requisito `## MODIFIED` |
|---|---|
| `pos-projection` | `The POS availability feed is drained into ai.pos_projection by a CLI` |
| `ai-service-runtime` | `Service exposes public health with version` |
| `demo-deployment` | `Deployment is verified from inside the host` |

**Hay exactamente un escenario que NO se conserva, y es deliberado**: `pos-projection` sustituye
`The only schema change is one additive nullable column` por `No schema change is opened`. La razón
está en el §3.2 del `qa.md`. **No es un hallazgo.** Cualquier otro escenario perdido sí lo es.

Y comprueba la **regla de la primera línea física** que `CLAUDE.md` documenta: el validador lee sólo
la primera línea de la descripción, así que un `SHALL` que caiga a la segunda falla con un mensaje
que no dice que el problema es tipográfico. Los 6 requisitos deberían cumplirla.

## Seis incidencias ya declaradas. No son hallazgos

Están en el §8 del `qa.md`, con su corrección. Volver a abrirlas es ruido:

1. **El primer cableado importaba `jbg_ai.indexing` desde `api/main.py`** y rompió
   `test_main_does_not_import_indexing`. Se arregló creando `indexing/pos_drain.py` y
   `api/lifespan.py`, **y extendiendo el guardián** al fichero nuevo.
2. **La delta de `ai-service-runtime` se dejaba cinco escenarios.** Restaurados.
3. **Un requisito propio pedía «páginas fallidas del último drenaje»**, dato no persistido. Se
   corrigió **la spec** para leerlo de `ai.sync_failure`.
4. **Un test propio era frágil** (buscaba `hashtext` en el texto fuente de un módulo que documenta
   por qué no lo usa). Reescrito contra el SQL real.
5. **`dotnet test` bloqueado** por la API corriendo.
6. **Un import muerto** en `cli.py` tras convertirlo en delegación. Retirado.

## Cinco afirmaciones que el `qa.md` hace. Compruébalas, no las aceptes

1. **El contrato congelado no se mueve.** `sha256` de `ai-service/openapi.json` declarado idéntico
   antes y después: `8d9060acc5a74dff555ee3353354b503f81b71665bd8d04c0b3723128f027be4`. Compruébalo
   contra `55bacb6` y contra `HEAD`, y que `test_openapi_snapshot_is_stable` pasa **sin regenerar**.
2. **+24 tests en `ai-service`, y la aritmética cierra**: 17 (`test_pos_scheduler.py`) + 6
   (`test_health_report.py`) + 1 (`test_embeddings.py`). Cuenta los `def test_` del diff.
3. **`tests/indexing` pasó de 98 a 116.**
4. **Cero migraciones y cero rutas `/v1` nuevas.** `git diff 55bacb6..HEAD` no debe tocar
   `ai-service/migrations/` ni `JoiabagurPV.Infrastructure/`, y `openapi.json` debe seguir con 11
   rutas bajo `/v1`.
5. **Los dos ajustes nuevos no aparecen en `canonical_openapi_settings()`.**

## Qué mirar con más cuidado, y por qué

**1. El lock está DENTRO del drenaje, no en el planificador — y eso es el requisito.** La decisión D6
dice que un lock en el planificador dejaría **al CLI corrido a mano** sin cubrir, y correr el CLI a
mano es como se repararon los tres incidentes. Comprueba que `python -m jbg_ai.indexing sync-pos`
pasa por el mismo camino que el planificador. Si encuentras una ruta de drenaje que **no** toma el
lock, es un CRITICAL.

**2. El arranque no puede bloquearse.** D3: el `HEALTHCHECK` sondea `/health` con 3 s y
`compose.demo.yaml` encadena `depends_on: service_healthy`, así que esperar un drenaje completo
marcaría el contenedor *unhealthy* y **tumbaría el despliegue por culpa de la mejora**. Comprueba que
la tarea se crea y **no se espera**, y que se cancela limpiamente al apagar.

**3. El planificador no debe arrancar donde no debe.** `scheduler_should_run` exige conmutador
encendido, `stub_mode` falso y feed configurado. **Comprueba en particular que las suites existentes
que construyen la app con `TestClient` no lo arrancan** — un planificador disparándose en los tests
sería un hallazgo serio y silencioso.

**4. `failed_pages` y `declined` son cosas distintas.** Una página fallida significa que alguien
tiene que ir a mirar; un drenaje declinado significa que otro proceso está haciendo el trabajo.
Comprueba que el CLI los distingue en su código de salida y que `describe()` no los confunde.

**5. La copia de la tarjeta es de COMPLETITUD, no de corrección.** Una proyección rancia **no
esconde piezas**: `Carried()` sigue poniendo la verdad, así que lo que cuesta es una página corta.
«Los resultados no son fiables» sería **falso**. Comprueba que la copia en es-ES no lo dice.

**6. El alcance negativo es parte del entregable.** Este change **no** debe tener: insignia de
frescura para el operario, botón de refresco para nadie, cambios en
`GET /api/ai/search/availability`, ni en `Carried()`. Si encuentras cualquiera de ellos, es un
hallazgo.

**7. La edad es del DRENAJE y es GLOBAL.** El checkpoint es una fila por feed. Cualquier campo,
comentario o copia de pantalla que sugiera frescura *por tienda* es falso. Lo que sí es por tienda es
`shops_without_scope`.

## Dos limitaciones del encargo que conviene que sepas de entrada

**La primera.** El contenedor `jpv-pv-jbg-ai` que corre en local lleva la **imagen anterior a este
change**, así que **no emite la sección `projection`** en `/health`. Si consultas ese contenedor y no
ves la sección, **no es un defecto del change**: es la imagen. Para verlo en vivo hay que ejecutar el
código del árbol, no el contenedor.

**La segunda.** Las comprobaciones en vivo del §4 del `qa.md` necesitan la API .NET sirviendo el feed
en `localhost:5056` **y** `jpv-pv-postgres` en el 5433. Si los levantas, ten en cuenta la trampa 1:
la API corriendo bloquea `dotnet test`. **Haz la suite de .NET primero y la comprobación en vivo
después**, o al revés parando la API — pero no las dos a la vez.

## El entorno, tal como está

| Pieza | Valor |
|---|---|
| PostgreSQL | `jpv-pv-postgres`, puerto **5433**, base `joiabagur_pv` |
| Proyección | **6.720 filas**, 12 puntos de venta, **11 con surtido y uno con cero** |
| `cd9bfd1f-f1b2-4795-9d14-867a75c18f90` | **0 asignados sobre 144 filas** → 503 en toda recuperación. **Es un hallazgo real preexistente, no un defecto de este change** |
| 94 filas con `computed_as_of = 2026-09-25 05:32:04` | **Residuo declarado** de la manipulación de C40, dejado a propósito como prueba forense. Son `is_assigned_hint = false` y el prefiltro exige `IS TRUE` |
| `jbg-ai` en contenedor | Imagen **anterior** a este change |
| Solución .NET | `backend/src/JoiabagurPV.sln` |
| Python | `uv run --system-certs pytest` desde `ai-service/` |

## Cómo quiero el informe

Sigue el formato del comando —tabla resumen de Completeness / Correctness / Coherence, y los
hallazgos agrupados en **CRITICAL / WARNING / SUGGESTION** con recomendación accionable y referencia
`fichero:línea`—, y además:

- **Di explícitamente qué comprobaste ejecutando y qué comprobaste leyendo.** Un juicio sobre una
  suite que no corriste no vale lo mismo que uno sobre una que sí.
- **Si refutas una afirmación del `qa.md`, dilo con esas palabras y con la evidencia.** El QA de
  C40_FIX refutó cinco afirmaciones de su implementador y encontró un defecto de producción; ese es
  el listón. **Que el implementador se haya abierto seis incidencias no significa que las haya
  encontrado todas.**
- **Si relanzas la suite de .NET, hazla sola.** Tarda ~20 minutos, levanta contenedores por test con
  Testcontainers, y una pasada en paralelo con otra suite da resultados que no describen el código.
  Y **para la API primero**, o repetirás la trampa 1.
- Si algo no se puede verificar en este entorno, **dilo en una sección propia** en vez de
  convertirlo en un WARNING.
