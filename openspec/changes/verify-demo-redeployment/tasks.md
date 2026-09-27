> **El despliegue YA OCURRIÓ.** C39a se archivó y se mergeó a `demo` el 2026-09-27 (PR #47, merge
> `2b357a1e`), y `deploy-demo.yml` corrió en la ejecución **36322635852**. El grupo 1 ya no espera un
> despliegue: **confirma el que hay**, y vuelve a tomar cada lectura en el momento de aplicar, porque
> las cifras de partida son de las 13:33 UTC de ese día y la proyección se mueve cada 600 s.
>
> **Punto de partida a contrastar, no a copiar** *(medido el 2026-09-27 ~13:33 UTC)*: `IMAGE_TAG`
> `sha-2b357a1e…` (antes `sha-d6a740fa…`) · `documents` 1200 · la ejecución **falló** en el paso
> «Verify the deployment from inside the host», con `1 point(s) of sale hold no assigned row in the
> projection`.
>
> **Y una restricción que se comprueba sobre el propio diff:** este change toca **sólo** ficheros
> que el `paths-ignore` de `deploy-demo.yml` ignora. Cualquier fichero fuera de esa lista lo
> convertiría en un redespliegue y perdería la razón por la que existe.

## 1. Confirmar el despliegue que ya ocurrió, no que el *push* llegó

- [x] 1.1 Confirmar que la ejecución de `deploy-demo.yml` **existe**, terminó, y que publicó las dos imágenes **pese a haber concluido en `failure`**. Validación: el identificador de la ejecución, su conclusión, y **el paso exacto que falló** — con la lista de pasos que sí pasaron, porque un `failure` de la ejecución no implica un despliegue no realizado y aquí es justo lo que hay que separar.
- [x] 1.2 Confirmar que **el `IMAGE_TAG` de SSM cambió** respecto al `sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d` que C39a registró, y que el nuevo corresponde al HEAD de `demo`. Validación: los dos valores y el `git rev-parse` al lado, **más el historial de versiones del parámetro**, que prueba la transición y no sólo el estado. **Es la única comprobación que no se puede simular**: sin cambio de tag no hubo despliegue, responda lo que responda la URL.
- [x] 1.3 Comprobar que el arranque registró las tres credenciales de generación como **propias**: `stage=assist_client`, `stage=router_client` y `stage=agent_client`, **ninguna con `assist_fallback`**. Validación: las tres líneas citadas, sin ningún valor de clave.
- [x] 1.4 Confirmar que los contenedores corren **el tag nuevo** y que la base **no** se recreó. Validación: la imagen de `jbg-demo-api` y `jbg-demo-ai` con su `sha-`, y el tiempo en pie de `jbg-demo-postgres` frente al de los otros dos — que es lo que distingue un redespliegue de una reinstalación.

## 2. Las siete condiciones, sobre el entorno real

- [x] 2.1 **Las siete condiciones, una por una, y HOY NO ESTÁN LAS SIETE EN VERDE.** `verify.sh` falla, así que la tarea no es «ponerlo verde» sino **clasificar cada condición que falle en una de dos categorías, y nombrar cuál**: (a) **falla por el estado del entorno** — hay algo realmente roto que hay que arreglar antes de mostrarlo; o (b) **falla por ser demasiado estricta** — el entorno está sano y la condición lo juzga mal. Validación: la salida completa de `verify.sh` ejecutado desde dentro del anfitrión, y **para cada condición en rojo, la categoría escrita con la medición que la sostiene**. Una condición en rojo sin categoría asignada deja la tarea sin hacer; y si alguna cae en (a), el entorno **no** se muestra.
- [x] 2.2 Las dos condiciones que C39a añadió, ejercitadas sobre el script **desplegado** y no canalizado: recuento de corpus y ruta del agente. Validación: las dos líneas `[verify] OK` con sus cifras. — **Las dos condiciones PASAN y están verificadas, pero esas dos líneas NO se pueden obtener y conviene decirlo:** `verify.sh` acumula los fallos y sale **antes** de imprimir ningún `[verify] OK`, así que mientras la quinta condición siga fallando el registro no publica ninguna. Verificadas por otra vía: corpus **161** leído de la base, y la ruta del agente respondiendo —sin entrada en `failures`— con la traza del arranque. Que un despliegue fallido no diga **qué pasó** es un defecto menor del propio guión, anotado junto al principal.
- [x] 2.3 Contrastar `ai.knowledge_chunk` con los **161** que C39a midió. Validación: la cifra; igual o mayor, y si fuera menor es un hallazgo.
- [x] 2.4 **La predicción de la proyección, confirmada o refutada.** C39a la midió a unas **120 veces** el techo y predijo que el drenaje de C41 la cura al arrancar. Validación: la frescura de `/health` contra el techo, y si **no** se ha curado, declararlo como refutación y anotarlo contra C41.
- [x] 2.5 Comprobar desde internet: HTTPS válido bajo el *hostname*, y que **sólo el proxy** publica puertos. Validación: el `curl` con su `ssl_verify_result` y el reparto de puertos de los cuatro contenedores. **Y el emisor del certificado se lee desde el anfitrión, no desde esta máquina**: el MITM de Norton que `CLAUDE.md` documenta reemplaza la cadena, así que un `ssl_verify_result=0` medido en local acredita la raíz de Norton y **no** la del emisor real. Validación: el emisor visto desde dentro del anfitrión, más las reglas de entrada del grupo de seguridad.

- [x] 2.6 **El falso positivo de la quinta condición, con su experimento.** `verify.sh` falla con `1 point(s) of sale hold no assigned row in the projection`, y ese punto de venta es `cd9bfd1f-f1b2-4795-9d14-867a75c18f90` = `HT-ARTRUTX` / «Hotel Cap d'Artrutx», **declarado inactivo a propósito** en el mundo sintético de C10 (`data/world/pos-profiles.yaml`: `is_active: false`, `closed_after: 2025-09-30`, `operator: null`) y el único de los doce. La condición cuenta `count(DISTINCT pos_id) FILTER (WHERE is_assigned_hint)` sobre `ai.pos_projection` en `health_report.py` **sin filtrar por si la tienda está activa**, así que una tienda cerrada legítimamente la hace fallar. Validación: (i) los doce puntos de venta con sus filas totales y asignadas; (ii) el `IsActive` de `HT-ARTRUTX` leído en la base desplegada; (iii) **el experimento**: el mismo recuento con y sin el filtro de actividad, que debe dar `1` y `0`; (iv) **dónde puede vivir el arreglo**, comprobado y no supuesto — si el rol del servicio de IA puede leer la tabla de puntos de venta de .NET, porque de eso depende. **No se arregla aquí**: el arreglo es código, y se anota en `openspec/DEFERRED_TASKS.md` con el experimento y la vía de cierre.

- [x] 2.7 **Y la lectura de la proyección que hizo el propio workflow no es la del entorno curado.** El paso de verificación leyó `status: stale` con `synced_at` del 22 de septiembre, y minutos después la misma llamada da `status: ok`: el informe de salud se **cachea 10 s** y el drenaje de arranque necesitó dos intentos. Validación: la marca de tiempo de cada lectura, las dos líneas de `boot_drain` del arranque, y la constatación de que la rancidez **no** es ninguna de las siete condiciones — así que no fue lo que hizo fallar el despliegue.

## 3. El recorrido del evaluador, a mano y sobre el entorno desplegado

> **Las cuentas que este grupo daba por existentes NO existían en el entorno desplegado, y es un
> hallazgo del change.** El §5.3 del *runbook* —«replace the shop's staff», obligatorio— sustituye el
> personal real por **exactamente dos** cuentas, `demo.admin` y `demo.operador`; deja `admin`
> **desactivada a propósito**, porque el sembrador la recrea con una contraseña que es una constante de
> un repositorio público; y las dos operarias sintéticas que venían en el volcado quedaron renombradas
> a `retirado-<prefijo>` y desactivadas. `op-ciutadella`, `op-fornells` y `op-aeroport` **sólo viven en
> el mundo sintético local** (`data/world/constants.py`), nunca en la demo.
>
> **Consecuencia:** la premisa de la delta de `demo-deployment` —tres operarios con surtidos distintos
> que hacen alcanzables la abstención, los sustitutos y el pivote— **era falsa para este entorno**, y
> con una sola cuenta de operario ligada a `MAO-AIR` ninguna de las tres se podía demostrar.
>
> **Resolución, decidida con el responsable durante el apply:** se aprovisionan los tres operarios
> sintéticos por SQL contra la base desplegada, con rol `Operator`, hash BCrypt `2a`/12 generado **fuera
> del anfitrión** con el ayudante del propio proyecto, y contraseña `Operator123!` —que **ya es una
> constante pública documentada** del mundo sintético, así que no añade ningún secreto nuevo. No es
> código, no redespliega, y **no toca** `admin` ni `demo.admin`. Lo que sí obliga es a corregir el §5.3,
> que dice «exactamente dos cuentas» y ya no describe el entorno.

- [x] 3.1 **La cuenta administradora, y lo que el §5.3 hizo con ella.** Validación: que `admin` **no fue eliminada** sino **desactivada** (`IsActive = false`), con su identificador, y la constatación de que eso es lo correcto y no un defecto. La **tarjeta de salud de la IA** está en una ruta `[Authorize(Roles = "Administrator")]`, así que **no es alcanzable con una cuenta de operario**: se comprueba el `403` que devuelve. — **Y la tarjeta SÍ quedó ejercitada**, con la contraseña de `demo.admin` que aportó el responsable: la ruta responde `200` en sesión de administrador y devuelve el informe completo, con `shopsWithoutScope: 1` **atravesando el proxy y la capa .NET**, que es donde se ve que el falso positivo llega hasta la pantalla y no se queda en el servicio. La contraseña **sigue fuera del repositorio**, y este change no creó ninguna cuenta administradora.
- [x] 3.2 `op-ciutadella` (CIU-CENTRE, surtido máximo): búsqueda asistida y ficha de venta con argumentario **generado**, con precio y existencias resueltos en el texto. Validación: la respuesta de la API verbatim y el `pitchStatus` observado.
- [x] 3.3 `op-fornells` (FORNELLS, surtido mínimo): abstención, sustitutos y avisos de agotado. Validación: los tres alcanzados o **declarado cuál no se pudo reproducir y por qué**, sin darlo por visto. El surtido de hoy: **241 filas asignadas, de ellas 29 en el saco `0`**, que es lo que hace alcanzable el agotado.
- [x] 3.4 `op-aeroport` (MAO-AIR, más agotados): el panel del agente, con la **traza del bucle** y el **pivote a sustitutos**, nombrando la pieza por su **referencia**. Validación: la traza, el pivote observado, y **la misma consulta repetida por nombre** para dejar medida la limitación declarada en lugar de sólo citarla.
- [x] 3.5 Panel de consulta libre (M1): una consulta sin pieza contestada, un **rechazo cortés** del enrutador, y el **ámbito global** (`PointOfSaleId` omitido, que es la ausencia de tienda y no un comodín). Validación: los tres estados con su respuesta.

- [x] 3.6 Medir la latencia extremo a extremo de las cuatro superficies y contrastar los tres relojes del agente —8 s por vuelta, 15 s de reloj del servicio, 18 s de presupuesto en .NET— con el proxy delante. Validación: las cifras publicadas; **no se recalibra nada**.

> **Y una limitación de método, declarada y no disimulada:** esta sesión **no tiene navegador**, así que
> **no hay capturas de pantalla**. El recorrido ejercita por HTTPS público los mismos *endpoints* que
> llaman las pantallas, y eso acredita el camino de extremo a extremo —enrutador, recuperación,
> generación, citas, cortes de reloj— pero **no** que la pantalla los pinte. Las validaciones que pedían
> una captura quedan cubiertas por la respuesta de la API y **la comprobación visual queda pendiente**,
> dicho así y no dado por visto.

## 4. La primera ejecución de la CI de la historia del repositorio

> **Este grupo quedó desfasado el mismo día en que se escribió, y por partida doble.**
>
> **No fueron dos ejecuciones, sino cuatro.** El merge de la PR #46 disparó el par `push` sobre
> `ai-eng` —**36319840972** (backend) y **36319840968** (frontend)—, pero antes la propia PR había
> disparado el par `pull_request` sobre su rama: **36319378725** y **36319378727**. Las cuatro en
> `failure`. Esa duplicación es precisamente la medición que motivó **retirar el disparo por `push`**,
> así que hoy sólo queda `pull_request` sobre `[ai-eng, master]` más `workflow_dispatch`, y correr la
> suite a demanda es `gh workflow run test-frontend.yml --ref ai-eng`.
>
> **Y la CI destapó que `npm run lint` no podía funcionar nunca:** no existía `frontend/eslint.config.js`.
> Sin él el paso de lint fallaba y dejaba el de tests en `skipped`, de modo que **la suite de frontend
> no se había ejecutado ni una vez en CI**. Creado el fichero y puesto el paso en `continue-on-error`,
> el lint pasa a informar y el de tests por fin corre.

- [x] 4.1 Leer las **cuatro** ejecuciones del 2026-09-27 —el par `pull_request` y el par `push`— y, para cada una, **el paso en que murió**. Validación: las cuatro con su identificador, evento, rama, conclusión y paso fallido; y la constatación de que en las dos de frontend el paso de tests quedó en `skipped`, que es la razón por la que **nunca** se había medido la suite en CI. **Es la primera vez** que estos flujos se ejecutan: hasta C39a disparaban sobre ramas inexistentes.
- [x] 4.2 Comparar los rojos **por nombre** contra la línea base que C39a midió en local: **backend 50 de 1.408** y **frontend 113 de 959 en 14 de 63 ficheros**. En la CI el backend dio **48** y **49** en las dos ejecuciones, dentro de la rotación que `CLAUDE.md` documenta. **El frontend nunca había corrido en CI**, así que hay que provocarlo a mano con `workflow_dispatch` — ésa es la primera medición que existe. Validación: cero nombres nuevos fuera de las clases y ficheros ya declarados inestables; los que difieran, nombrados uno a uno con la clase en que caen.
- [x] 4.3 Recoger las cifras del lint, **declaradas y no arregladas**: 89 errores y 82 avisos en 104 ficheros. Validación: la cifra leída de la ejecución, y la constancia de que el paso está en `continue-on-error` **a propósito**, para que el lint informe sin volver a tapar los tests.
- [x] 4.4 Confirmar que **no actúan como puerta** y que ninguno está configurado como comprobación requerida. Validación: la PR se pudo integrar con los dos en rojo, y queda escrito por qué con las cifras.

## 5. Las cuentas de demostración, declaradas

- [x] 5.1 `deploy/demo/README.md`: tabla con **todas** las cuentas que hay hoy —las dos de `demo.*`, los tres operarios sintéticos, y `admin` con su estado desactivado y el motivo—, su punto de venta y **qué behaviour es alcanzable desde cada una**, más la restricción del pivote por nombre. Validación: la tabla cubre las seis, distingue la que **no** se puede usar de las que sí, y nombra la restricción como limitación declarada y no como defecto.
- [x] 5.2 **Corregir el §5.3, que ha dejado de describir el entorno.** Dice «create exactly two accounts» y ahora hay cinco activas. Validación: el §5.3 dice qué cuentas existen y por qué, sigue exigiendo que no quede personal real, y mantiene `admin` desactivada como condición de seguridad.
- [ ] 5.3 Sincronizar la delta de `demo-deployment`. Validación: **`openspec validate --all --strict` a `0 failed`**. — **Deliberadamente sin hacer, y no es un olvido.** La fusión de la delta en `openspec/specs/demo-deployment/spec.md` la hace `openspec archive`; adelantarla a mano y archivar después aplicaría el requisito **dos veces**, que es exactamente cómo `CLAUDE.md` describe una sincronización rota —una spec viva con sintaxis de delta y sin `## Purpose`. La puerta ya está verde sin ella: **`openspec validate --all --strict` → 65 passed, 0 failed**. Esta casilla la cierra el archivado.

## 6. Cierre

- [x] 6.1 Informe `c39a-bis-implementation-measurements.md` con las cifras del entorno desplegado, el recorrido con su evidencia, las latencias, y **lo que se refutó** de las predicciones de C39a. Validación: cada afirmación con su medición al lado o declarada como no medida.
- [x] 6.2 Cerrar en [HU-AIENG-043](../../../Documentos/Historias/AI-Eng/HU-AIENG-043.md) los escenarios que este change verifica, dejando constancia de cuáles quedaron cubiertos por C39a y cuáles por éste. Validación: los catorce escenarios con su veredicto.
- [x] 6.3 Poner al día el §0 del plan y las fichas de C39a y C39a-bis con el resultado del despliegue. Validación: ninguna afirmación de las fichas contradicha por los dos informes.
- [x] 6.4 Anotar en `openspec/DEFERRED_TASKS.md` lo que el recorrido destape **sin arreglarlo**, y la deriva de rama que C39a dejó declarada: nada compara lo desplegado con la rama que debería servirse. Validación: cada entrada con su experimento y su vía de cierre.
- [x] 6.5 **Comprobar la restricción propia de este change sobre el diff completo**: cero ficheros fuera de `openspec/**`, `Documentos/**`, `**/README.md`, `CLAUDE.md`, `AGENTS.md` y `terraform/**`. Validación: la lista de modificados, fichero a fichero, y la confirmación de que el merge a `demo` **no** dispara `deploy-demo.yml`.
