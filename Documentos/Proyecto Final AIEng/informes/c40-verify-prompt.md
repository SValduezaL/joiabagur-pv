# Prompt para verificar C40 en una sesión nueva

Copia desde la línea siguiente hasta el final del documento y pégalo en un chat nuevo de Claude
Code, abierto en la raíz del repositorio y en la rama `c40-add-frontend-free-query-panel`.

---

/opsx:verify add-frontend-free-query-panel

Verifica C40 en la rama `c40-add-frontend-free-query-panel`, cuya cabeza es `3650ece`. La rama está
publicada y el árbol está limpio. **No implementes nada y no arregles nada**: este encargo es
producir un informe de verificación. Si encuentras algo que arreglar, lo listas con su
recomendación y paras.

La implementación declara **67 de 67 tareas** y la base contra la que se compara todo es `93115cf`,
la cabeza anterior al primer commit del change. `git diff --stat 93115cf..HEAD` da 114 ficheros.

## Lee esto antes de emitir un solo juicio

1. `openspec/changes/add-frontend-free-query-panel/tasks.md` — 14 grupos, 67 tareas, todas marcadas.
2. `openspec/changes/add-frontend-free-query-panel/specs/**/spec.md` — **11 ficheros, 36 requisitos,
   136 escenarios**. Es el contrato: cada escenario debería tener implementación o test, o una razón
   escrita de por qué no.
3. `Documentos/Proyecto Final AIEng/informes/c40-implementation-measurements.md` — **el informe de
   implementación, 14 secciones**. Es donde están las cifras, las desviaciones declaradas y los
   errores corregidos. **Leerlo entero antes de abrir un CRITICAL te ahorrará casi todos los falsos
   positivos**, porque la mayoría de lo que parece un hueco está ahí explicado y medido.
4. `openspec/changes/add-frontend-free-query-panel/design.md` — 10 decisiones y 11 preguntas ya
   resueltas. Las once **no se reabren**: si la implementación las respeta, es coherencia, no
   conformismo.
5. `Documentos/Proyecto Final AIEng/informes/c40-m1-panel-states.md` — la tabla de los dieciséis
   estados. Es el contrato real de la pantalla; `frontend/src/lib/free-query-states.ts` la
   implementa y `free-query-states.test.ts` la fija.
6. `openspec/DEFERRED_TASKS.md` — lo que quedó fuera, con su motivo. **Dos entradas nuevas de C40 y
   una de C34 agravada.**
7. `openspec/project.md` y `CLAUDE.md` — convenciones y, sobre todo, las trampas del repositorio.

## Ocho trampas que te harán concluir algo falso si no las sabes

Estas no son consejos de estilo: cada una produce un veredicto **incorrecto** con toda naturalidad.

1. **Las tres suites no parten de cero rojos, y dos vienen rojas de fábrica.** Comparar por
   **nombres**, nunca por número:
   - `backend` — `dotnet test` da **47 de 1 328** al cierre, y la línea base daba 50–51. Hay
     **churn documentado**: dos pasadas del mismo commit dan hasta quince nombres distintos,
     siempre en `InventoryIntegrationTests`, `PaymentMethodsControllerTests` y
     `ReturnsControllerTests`. El criterio útil es **si el nombre discrepante cae en esas clases y
     si el área del change está limpia**.
   - `frontend` — **113 de 833 en 14 ficheros**, y el conjunto de nombres es **idéntico** al de la
     línea base. Oscila entre 113 y 114 sobre el mismo commit.
   - `ai-service` — **1 625 en verde, 0 rojos**. Ésta sí es una puerta binaria.
2. **`vitest` sale con código 0 al pipearlo.** `npm run test | tail` devuelve el código de `tail`.
   Lee la línea de resumen, no el prompt.
3. **`dotnet test` sale 0 habiendo corrido cero tests** si algo tiene bloqueado `bin/Debug` — una
   `JoiabagurPV.API.exe` en marcha lo hace. Lee el recuento.
4. **`npm run build` no comprueba tipos.** Vite transpila con esbuild y esbuild descarta los tipos
   sin mirarlos, así que build verde significa «compila» y no «los tipos casan». C40 encontró así un
   commit entero con un DTO anulable en .NET y `number` en TypeScript. Para verificar tipos:
   `npx tsc --noEmit` **filtrando la salida a los ficheros del change**, porque trae decenas de
   errores preexistentes de la plantilla Metronic.
5. **`openspec validate` sin destino no valida nada** y sale 1. La puerta es
   `openspec validate --all --strict` → **0 failed**. Al cierre da **62 passed, 0 failed**.
6. **MSW no falla una petición sin handler** (`onUnhandledRequest: 'warn'`), así que un test de
   frontend puede pasar sin haber afirmado nada. Si dudas de la cobertura de un escenario, mira si
   el test mockea el servicio con `vi.mock` o declara handlers.
7. **Una suite que acaba demasiado rápido ha fallado, no ha corrido.** Pasó tres veces en este
   change: dos por cuota del proveedor —una llamada limitada vuelve en ~150 ms y arrastra un p95
   hacia abajo— y una por saturar Docker, que dio **484 fallos en 2 minutos** contra 47 en 20. Si
   relanzas el backend, **hazlo solo**, sin otra suite ni una reconstrucción de imagen en paralelo.
8. **`uv sync` y `uv run` necesitan `--system-certs`** en esta máquina.

## Diez desviaciones ya declaradas. No son hallazgos

Todas están argumentadas en el informe. Confírmalas si quieres, pero **abrirlas como CRITICAL sería
un falso positivo**; si crees que alguna está mal argumentada, ábrela como WARNING citando el
párrafo que la declara.

| # | Desviación | Dónde se declara |
|---|---|---|
| 1 | `AssistRequest.filters` es **no anulable y siempre se serializa**, contra la tarea 3.3 que pedía «omitido cuando no hay ninguno». Se siguió el precedente de `AiSubstitutesRequest` en vez de exceptuar el guard del contrato | §3 |
| 2 | El escenario «se declara un filtro que no se pudo aplicar» es **inalcanzable** desde la forma de la petición del panel. El canal (`unappliedFilters`) se construyó y quedó **dormido**, con su razón en el propio DTO | §2, §11 |
| 3 | `filters_too_narrow` se emite **sólo con la regla de abstención encendida**, porque los dos umbrales que lo definen son de la regla | §10 |
| 4 | `SearchFilters.is_empty` cuenta los **cuatro** campos, lectura literal de «no trae filtro de cuerpo» | §10 |
| 5 | **`CAPTURE_VERSION` no se movió**: la sonda lee otro perfil, no altera el conjunto de candidatos, así que las capturas anteriores siguen válidas | §10 |
| 6 | Una consulta libre de **ámbito global no se registra**: exigiría migración de EF Core —excluida— y la spec prohíbe el marcador de posición | §12, `DEFERRED_TASKS.md` |
| 7 | `ForAllPointsOfSale_IsRefusedByInventory` **no tiene superficie .NET**: `IAiGatewayClient` no tiene operación de inventario. La garantía vive en Python y el test .NET afirma que la superficie no existe | §12 |
| 8 | **Tres campos raíz sin lector al cierre** —`traceId` ×2 y `unappliedFilters`— de 38, cada uno con su motivo. Sobre los 82 pares (clase, campo) auditados quedan seis nombres: los tres más `familyId`, `docType`, `score` y `totalTokens` | §11 |
| 9 | Cuatro **manipulaciones del entorno** en la medición de latencia: calentamiento descartado, proyección del punto de venta refrescada, dos pasadas descartadas por cuota, y `q54` vuelta a medir sola | §8 |
| 10 | **El corpus no viaja en la imagen** y la tarea diferida de C34 **se agrava**: `CORPUS_DIR` se deriva de `REPO_ROOT`, que en el contenedor resuelve a `/app/.venv/lib` | §14, `DEFERRED_TASKS.md` |

## Cinco cifras que el informe afirma. Compruébalas contra los artefactos

Están en `ai-service/evals/results/c40-*.json`, los siete con `run_id`, `git_sha` y
`prompt_version`. **Tres de las cinco refutan lo que la exploración predijo, y eso es deliberado**:
si el informe y el artefacto discrepan, el artefacto manda y es un hallazgo.

| Cifra | Valor afirmado | Artefacto |
|---|---|---|
| Marcadores en el argumentario de M1 | **2 de 90** y **1 de 90** en `assist/v3`; **0 y 0** en `v5` | `c40-placeholders-before-v3-*.json` · `c40-placeholders-after-v5-*.json` |
| Reparto de los dieciséis estados | **9 observados** sobre 71 consultas | `c40-dotnet-latency-42.json` · `c40-dotnet-states-refusals-29.json` |
| Latencia extremo a extremo por .NET | **p50 3 404 ms · p95 7 160 ms**, 0 de 42 fuera del presupuesto de 10 s | `c40-dotnet-latency-42.json` |
| Tasa de `router_index_absent` | **0 de 42** (la exploración predijo 11,9 %) | `c40-router-index-absent.json` |
| Coste de la sonda sin filtro | **p50 20,9 ms · p95 29,3 ms**, y **0 sondas** sin filtro | `c40-probe-cost.json` |

Y la comprobación con datos reales: **8 de 8 casos y 0 marcadores**, en `c40-real-data-check.json`.

## Qué mirar con más cuidado, y por qué

No son sospechas: son los sitios donde un error costaría más y donde la verificación aporta más que
en el resto.

- **La frontera de autorización del grupo 12.** `AiCallScope` expone **exactamente tres** caminos de
  construcción y ninguno acepta un centinela; el ámbito de todas las tiendas lo aceptan sólo
  recuperación y assist. La propiedad que lo hace seguro es que **la ausencia de `pos_id` hace que
  el prefiltro no se aplique**, no que case con todo. Comprueba en particular que un `pos_id`
  **presente y en blanco** se rechaza: es el agujero que el propio grupo abrió y cerró, y su test es
  `test_a_blank_pos_claim_is_never_read_as_its_absence`.
- **Los dieciséis estados.** Están resueltos en `free-query-states.ts` como unión discriminada y no
  como escalera de comprobaciones de campo, porque los estados son **combinaciones**. Tres se
  pintarían mal por defecto: el vacío de la ruta de conocimiento, y los dos sin ruta que necesitan
  copia opuesta según `intent`.
- **El contrato congelado `ai-service/openapi.json`.** Se movió **dos veces** y el DoD exige
  verificación hoja a hoja: **1 300 hojas** en `tests/api/fixtures/openapi-c40-baseline.json` y
  **1 306** al cierre, con **0 retiradas y 0 cambiadas de tipo**; las 2 que cambian de valor son
  `description`. El guardián es
  `tests/api/test_agent_route.py::test_the_published_contract_moved_by_addition_only`, que nombra
  esas dos una por una para que una tercera siga fallando.

  > **Cuidado con el recuento si lo haces con tu propio contador.** «Hoja» no es un concepto único:
  > contando sólo primitivas salen **1 295**, y contando como lo hace el guardián —el mismo
  > recorrido que produce las rutas tipo `/components/schemas/X/properties/y/type`— salen 1 306. Las
  > dos cifras son correctas para su definición y **discrepar con la del informe no es un hallazgo**
  > salvo que uses su mismo recorrido. Lo que sí es verificable sin ambigüedad es lo que decide el
  > DoD: **retiradas y cambiadas de tipo, ambas a cero**.
- **Sin migración de EF Core**, y comprobado por test:
  `ProductSearchEventSchemaTests` incluye `HasPendingModelChanges().Should().BeFalse()`.
- **Nada de dinero en el embudo de administrador.** El test no busca un símbolo: busca `€`, `EUR`,
  `$`, «coste» y «precio». Y ni la consulta del operario ni el argumentario aparecen en él.
- **La verificación de completitud campo a campo** del §11 se auditó con un barrido mecánico que
  parte del contrato y no de los componentes. Si lo rehaces, ojo con dos cosas que ya sesgaron la
  primera versión de esa sección: el barrido **empareja por nombre**, así que un campo leído en una
  superficie cuenta como leído en todas —`intent` y `promptVersion` tienen lector en el panel y no
  en la ficha—; y las cifras **se movieron al cerrar el change**, porque el embudo del grupo 13 es el
  consumidor de `usage`. Las del informe son las corregidas: **35 de 38 campos raíz con lector**.

## Una limitación del encargo que conviene que sepas de entrada

**Los ficheros con los nombres de los tests que fallaban en la línea base no están en el
repositorio**: se produjeron en el directorio de trabajo de la sesión de implementación y no
sobreviven a ella. Así que no puedes hacer el `diff` de conjuntos de nombres que la implementación
hizo en cada grupo. Tienes tres caminos que sí sirven, en este orden:

1. **Reproducir la línea base**, que es lo único concluyente:
   `git stash` no hace falta —el árbol está limpio— así que `git checkout 93115cf`, correr las suites,
   volcar los nombres, y `git checkout c40-add-frontend-free-query-panel`. Cuesta unos 45 minutos de
   reloj entre las tres. Si lo haces, **corre el backend solo** (trampa 7).
2. **Comparar contra lo documentado**: el `CLAUDE.md` da las cifras y, más útil, **nombra las clases
   rotatorias**. Un nombre nuevo dentro de ellas no es un hallazgo; uno fuera, sí.
3. **Correr sólo el área de C40**, que es donde una regresión de este change tendría que aparecer:
   `dotnet test --filter "FullyQualifiedName~AiCallScope|FullyQualifiedName~AiGateway|FullyQualifiedName~FreeQuerySearch|FullyQualifiedName~AssistedSearch|FullyQualifiedName~SalesAssist|FullyQualifiedName~Substitutes|FullyQualifiedName~ProductSearchEvent"`.
   La implementación lo hizo y dio **limpio** en las cuatro veces que lo corrió (341, 115, 22 y 13
   tests). Si ahí sale algo rojo, es un hallazgo de primer orden.

Elige uno y **di cuál elegiste** en el informe. Lo que no vale es afirmar «cero nombres nuevos» sin
haber podido comparar: eso es precisamente el tipo de conclusión que este repositorio castiga.

## El entorno, tal como está

- **El contenedor `jpv-pv-jbg-ai` está en marcha**, reconstruido con el código actual, en la red
  `backend_jpv-network`, puerto 8001, con **claves reales y `STUB_MODE=false`**. Está sano y con el
  índice cargado. **Si vas a reconstruirlo o recrearlo, no lo hagas mientras corre una suite.**
- La **API de .NET está parada**. Si la necesitas: `localhost:5056`, los tres interruptores
  encendidos por variable de entorno (`AiSearch__EnabledByDefault`,
  `AiSalesAssist__EnabledByDefault`, `AiFreeQuerySearch__EnabledByDefault`), usuario `admin`. Párala
  antes de compilar el backend o el build fallará por DLL bloqueados.
- **Los tres interruptores están apagados por defecto** y no aparecen en ningún `appsettings`. Está
  documentado en `backend/README.md`; si verificas a mano y todo sale degradado, es esto.

## Cómo quiero el informe

El formato del comando —las tres dimensiones y el marcador con CRITICAL, WARNING y SUGGESTION— con
tres añadidos:

1. **Cada hallazgo con su referencia**, `fichero:línea`, y una recomendación concreta. Nada de
   «considera revisar».
2. **Si algo del informe de implementación resulta falso al contacto con el código, es un hallazgo
   de primer orden** y lo quiero arriba, no entre las sugerencias. En este change la medición refutó
   a la exploración **tres veces**, y la implementación se corrigió a sí misma otras tres: la
   afirmación de que el corpus viajaba en la imagen (§14, falsa), el recuento de campos con lector
   del §11 (escrito a mano y mal: decía 31 de 38, son 35) y el encabezado que decía «siete campos»
   sobre una lista de ocho. **Las tres se encontraron mirando otra cosa**, así que el sitio más
   probable de una cuarta es una cifra escrita en prosa que nadie recontó. Si encuentras una,
   arriba.
3. **Di explícitamente qué comprobaciones no has hecho y por qué.** Un informe que calla lo que no
   miró vale menos que uno que lo enumera.

Si al acabar no hay CRITICAL, dilo y propón `/opsx:archive`.
