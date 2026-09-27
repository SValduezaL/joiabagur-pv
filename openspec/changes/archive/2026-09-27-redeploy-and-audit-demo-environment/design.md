## Context

El entorno de demostración existe desde el 2026-08-30 (C17): cuenta de AWS separada, *stack* de Terraform propio, imágenes propias y un *runbook* de 28 KB. **Está en pie y funciona** — medido contra la cuenta el 2026-09-27: instancia `i-095f0ba16e2bb8278` en `running` desde el día en que se creó, HTTPS válido sobre `52-49-209-14.sslip.io`, `http=200`, los siete parámetros secretos presentes. Lo que no está es al día.

### Las dos rutas de despliegue, que conviene tener delante

```
                        ┌─ push a main/master ─→ deploy-aws-ec2.yml ─→ eu-west-3
   PRODUCCIÓN           │                                             terraform/
   PROHIBIDO TOCAR      │                                             jpv-backend  (Dockerfile.bundled)
                        │                                             VITE_API_BASE_URL absoluto
   ─────────────────────┼───────────────────────────────────────────────────────────────────────
                        │                                             eu-west-1
   DEMO · este change   └─ push a demo ────────→ deploy-demo.yml ───→ terraform/demo/
                                                 paths-ignore:        jbg-demo-api (Dockerfile.demo)
                                                   openspec/**        jbg-demo-ai  (ai-service/Dockerfile)
                                                   Documentos/**      VITE_API_BASE_URL = /api
```

**Producción no construye la imagen de `jbg-ai`.** Comprobado sobre `deploy-aws-ec2.yml`, que sólo construye `Dockerfile.bundled`. Ése es el hecho que hace segura la única tarea de este change que toca un fichero compartido entre árboles.

### El estado que el change tiene que corregir

```
 ai-eng   0d63f1a  merge PR #45 (C42)     2026-09-27   ─┐
                                                        │  84 commits
 demo     d6a740f  «QA de C34»            2026-09-22   ─┘  0 en sentido contrario

 IMAGE_TAG desplegado: sha-d6a740fa5e0b…  ← el HEAD de `demo`, no una inferencia
```

Ausentes del entorno: **C36** (ficha de venta), **C40** + **C40_FIX** (panel de consulta libre, ámbito global), **C41** (drenaje de la proyección), **C42** (panel del agente). Entre las dos ramas, **143 ficheros de código, +21.496 / −247, y cero migraciones** — ni EF Core ni Alembic.

### Restricciones que gobiernan el diseño

| Restricción | Origen |
|---|---|
| La ruta de producción no se toca | encuadre del change; la spec de C17 tiene un escenario que exige que ese flujo quede inalterado |
| Los secretos no entran en el estado de Terraform | `terraform/demo/ssm.tf`: *«un valor pasado a Terraform se escribe en el estado en claro»* |
| Los ajustes de comportamiento son literales versionados, no parámetros | requisito vivo de `demo-deployment`: cambiar lo que el sistema computa debe pasar por revisión |
| Los secretos llegan sólo por el entorno del proceso que despliega | requisito vivo: ni en fichero del anfitrión, ni en imagen, ni en la salida del comando |
| La cuota del proveedor permite del orden de **una petición por minuto** | ~13.000 tokens contra 25.000 TPM, declarado por C42 |

## Goals / Non-Goals

**Goals:**

- Que el entorno sirva **el sistema que el proyecto ha construido**, no el de hace cinco semanas.
- Que las **cuatro superficies de IA** —búsqueda asistida, ficha de venta, panel de consulta libre y panel del agente— estén alcanzables desde internet y comprobadas a mano sobre el entorno desplegado.
- Que la configuración quede **auditada contra lo que el código declara**, con la tabla publicada y recomprobable por otro.
- Que la verificación **falle** en los dos casos en que hoy pasaría en falso.
- Que el evaluador pueda entrar con credenciales escritas y sepa **qué probar con cada una**.

**Non-Goals:**

- El README de entrega, el vídeo, el tag y las evidencias: **C39b**.
- Poner las suites en verde. La CI entra informativa y los fallos preexistentes se declaran.
- Convertir la CI en puerta obligatoria.
- Recalibrar ningún ajuste de comportamiento.
- Un dominio comprado. El §6 del *runbook* lo cubre y la imagen es agnóstica del nombre, así que puede hacerse después **sin reconstruir**.
- Un workflow de `pytest` para `ai-service`: no existe, y crearlo es trabajo nuevo. Se declara como hueco.
- Tocar `backend/src`, `frontend/src`, `ai-service/src`, `terraform/` o `terraform/demo/`.

## Decisions

### D1 · El redespliegue se hace llevando `demo` a `ai-eng`, no por un camino lateral

`deploy-demo.yml` dispara por `push` sobre `demo`. Cualquier otra vía —construir a mano, `workflow_dispatch` sobre otra rama— sería un despliegue fuera del mecanismo que la spec verifica, y dejaría el `IMAGE_TAG` de SSM describiendo algo que nadie puede reconstruir desde git.

**Alternativa considerada:** cortar una rama nueva de `ai-eng` y apuntar el workflow a ella. **Rechazada:** cambia el disparador de un flujo que funciona para evitar un `merge` que es trivial —`demo` es ancestro estricto, no hay conflicto posible— y deja la rama `demo` como un fósil que la próxima vez confundirá a alguien.

**Riesgo que la decisión introduce, y su comprobación:** el workflow lleva `paths-ignore` sobre `openspec/**` y `Documentos/**`. Un *push* cuyo contenido cayera entero en esas rutas **no despliega y no avisa**. La tarea exige comprobar que el workflow **se ejecutó**, no que el *push* llegó.

### D2 · Las dos credenciales nuevas son opcionales, con el patrón literal de `ASSIST_LLM_API_KEY`

```sh
export AGENT_LLM_API_KEY="$(read_parameter AGENT_LLM_API_KEY || true)"
export ROUTER_LLM_API_KEY="$(read_parameter ROUTER_LLM_API_KEY || true)"
# Sin `: "${…:?}"`  ← deliberado
```

La ausencia de cada una es un **estado válido, declarado e implementado**: sin la del agente el bucle no se construye y la ruta responde 200 sin ejecutarlo —*fail-open*, ablación y *rollback* a la vez—; sin la del enrutador, el clasificador no se construye, el intent vuelve `unclassified` y la ruta sirve exactamente lo que servía antes de C31.

**Alternativa considerada:** declararlas obligatorias con `: "${…:?}"`, como las cinco de infraestructura. **Rechazada:** convertiría una degradación diseñada, con test detrás, en un fallo de despliegue. Y rompería el *rollback*: hoy borrar el parámetro y redesplegar es la forma de volver atrás.

### D3 · Tres claves para tres etapas, y no una compartida

Los repliegues `agent → assist → rag` y `router → assist → rag` ya están implementados, y cada proceso registra una vez cuál ganó. **El repliegue es red, no configuración.** Con él activo —que es lo que pasa hoy, y el log de C34 lo registró como `credential=assist_fallback`— los costes de tres modelos distintos son inseparables, y el clasificador corre `gpt-4o` mientras el argumentario corre `gpt-4o-mini`: una clasificación de ~30 tokens de salida y un párrafo no son la misma llamada.

**Alternativa considerada:** un solo parámetro `LLM_API_KEY` leído tres veces. **Rechazada** por lo anterior, y porque la spec ya distingue el caso en que **sí** conviene compartir parámetro —`AI_SERVICE_SHARED_SECRET` e `INDEX_FEED_SHARED_KEY`, cada uno leído dos veces— por una razón opuesta: ahí dos parámetros podrían derivar, y un par derivado produce un 401 cuya causa el servicio está especificado para no revelar. Compartir tiene sentido cuando la deriva es el riesgo; aquí el riesgo es la confusión de costes.

**Lo que sí se admite**, y ya es práctica del *runbook* con la clave de *embeddings*: tres parámetros distintos **con el mismo valor**. Separa la contabilidad sin multiplicar las cuentas del proveedor.

### D4 · El interruptor del agente es literal en el compose, no parámetro en SSM

`AiAgentAssist__EnabledByDefault: "true"` en el servicio `jbg-demo-api`. La spec viva lo exige para todo ajuste que cambie **lo que el sistema computa** frente a **dónde corre**: el almacén de parámetros es un sitio donde un valor cambia sin revisión de código, y encender o apagar una ruta de IA no debe poder hacerse así.

**Y el defecto que se corrige es de omisión, no de valor.** Los otros tres interruptores del mismo patrón —`AiSearch`, `AiSalesAssist`, `AiFreeQuerySearch`— están puestos; éste falta, y su tipo es `public bool` sin inicializador, con `EnabledPointOfSaleIds` vacío. El resultado es `false` para todo punto de venta.

### D5 · El corpus entra por contexto de *build*, no por volumen

```
HOY
  docker build -f ai-service/Dockerfile … ai-service     ← contexto = subdirectorio
  CORPUS_DIR = <raíz>/data/knowledge                     ← FUERA del contexto
  COPY: src · migrations · prompts · alembic.ini         ← ninguna línea puede alcanzarlo
  jbg-demo-ai: sin `volumes:`                            ← el apaño de C34 no está codificado

DESPUÉS
  docker build -f ai-service/Dockerfile … .              ← contexto = raíz, como el de la API
  COPY data/knowledge ./data/knowledge
```

| Camino | Veredicto |
|---|---|
| ~~**Contexto a la raíz**~~ | ~~**Elegido.** La imagen queda autosuficiente, que es requisito vivo de reproducibilidad. El *build* de la API ya usa contexto de raíz y su comentario documenta que el `.dockerignore` lo mantiene en decenas de megas frente a los 1,18 GB que eran antes de C17~~ → **REFUTADO AL IMPLEMENTAR**, recuadro de abajo |
| **Contexto adicional con nombre** — `--build-context corpus=./data/knowledge` | **ELEGIDO tras la refutación.** Deja el contexto primario intacto y trae el corpus aparte, declarado en el propio `Dockerfile` |
| Copiar el corpus a `ai-service/` en el workflow antes del *build* | **Rechazado.** Un `docker build ai-service` a secas produciría **en silencio** una imagen sin corpus, que es el modo de fallo que este hueco existe para eliminar |
| Volumen desde el paquete de despliegue | **Rechazado.** Deja el contenido fuera de la imagen y reintroduce el apaño de C34 en forma declarativa: la imagen dejaría de poder indexar por sí sola, y un anfitrión nuevo volvería a arrancar con `ai.knowledge_chunk` a cero |
| `docker cp` o indexar desde el anfitrión | **Rechazado.** Es el apaño actual, y no sobrevive a un despliegue limpio: es exactamente lo que hay que cerrar |

> ### ⚠ D5 refutada al implementar, el 2026-09-27, por un consumidor que el diseño no buscó
>
> **Mover el contexto de *build* a la raíz habría roto el desarrollo local.**
> `backend/docker-compose.yml` construye **este mismo `Dockerfile`** con `context: ../ai-service`, y
> `ai-service-dev-compose` es una **capability viva**. Con las rutas reescritas a `ai-service/…`, ese
> compose deja de construir. El diseño razonó sobre el *build* de la API y sobre el `.dockerignore`, y
> **no buscó el segundo consumidor del fichero**.
>
> Y había un coste más que tampoco vio: el `.dockerignore` de la raíz **declara por escrito** que no
> gobierna a este `Dockerfile` porque su contexto es el subdirectorio. Mover el contexto habría dejado
> esa frase falsa y las exclusiones de `ai-service/.dockerignore` —`tests/`, `openapi.json`, `*.md`— sin
> aplicar.
>
> **Lo que se hace en su lugar, un contexto adicional con nombre de BuildKit:**
>
> ```text
> docker build -f ai-service/Dockerfile --build-context corpus=./data/knowledge … ai-service
> COPY --from=corpus . ./data/knowledge
> ```
>
> Contexto primario intacto, `ai-service/.dockerignore` sigue gobernando, el comentario de la raíz sigue
> siendo verdad, y **ninguna ruta del `Dockerfile` se reescribe**.
>
> **Y cumple el requisito de reproducibilidad en el punto que de verdad importa, comprobado y no supuesto:
> construir sin el flag FALLA EN VOZ ALTA.** BuildKit intenta resolver `corpus` como una imagen y aborta
> con código 1 —`failed to resolve source metadata for docker.io/library/corpus:latest`—, así que **no
> existe una imagen sin corpus construida en silencio**. Ésa era la objeción que descartaba copiar el
> corpus en el workflow, y esta opción sí la sostiene.
>
> **Consecuencia que hay que asumir, y es una línea:** al declarar el `COPY`, el compose de desarrollo
> **también** necesita el contexto (`additional_contexts`) o deja de construir. De paso el entorno de
> desarrollo **gana** un corpus que hasta ahora su imagen no llevaba.

**Consecuencia observable de cerrarlo**, y es la que la verificación comprueba: `ai.knowledge_chunk` deja de estar a cero, con lo que **M2 deja de retirar el argumentario** por no tener material al que anclarse y **M3 deja de responder `knowledge_not_covered`** sin citas.

### D6 · La verificación gana dos condiciones, y una de ellas necesita un matiz

`verify.sh` tiene cinco condiciones de fallo; la quinta —proyección sin filas— la añadió C41 por una razón que la spec escribe entera: *«el despliegue parece un éxito y no encuentra nada que el surtido debería haber acotado. Es exactamente la forma del índice vacío, una tabla más allá, y ya ha llegado una vez a un entorno desplegado»*. **El corpus vacío es la tercera tabla de esa misma serie.**

La séptima —ruta del agente sin respuesta— lleva un matiz que hay que respetar: una **degradación en banda** (200 con `stop_reason` de fallo de proveedor o de falta de cliente) **no es un fallo**. El cortacircuitos de .NET tampoco la cuenta, y deliberadamente: Polly ve el resultado de transporte y no el cuerpo, así que un 200 degradado es un éxito en esa capa y se instrumenta como métrica. La condición nueva tiene que distinguir lo mismo, o convertirá una degradación diseñada en un despliegue fallido.

### D7 · La CI entra informativa, con filtro de rutas, y sobre las ramas que existen

Los dos workflows de test **no se han ejecutado nunca**. Su disparador nombra `main` y `develop`, que no existen. Y no es sólo el fichero: el requisito **«Backend Test CI Workflow»** de `backend-testing` **especifica esas mismas ramas inexistentes**, así que la spec describe un workflow que no puede dispararse.

- **Ramas → `[ai-eng, master]`**, en `push` y en `pull_request`.
- **Informativa, no puerta.** `CLAUDE.md` documenta 53 fallos preexistentes en backend y 113 en frontend, con rotación de nombres entre pasadas del mismo commit. Una puerta sobre eso es un bloqueo permanente.
- **Filtro `paths:` conservado**, al contrario que en los despliegues. Los dos filtros fallan hacia lados distintos a propósito: un test que sobra cuesta minutos, un despliegue que falta deja el entorno corriendo código viejo en silencio.
- **Y no se hace obligatoria**, por la trampa que la tarea diferida ya nombra: un workflow **omitido** por filtro de rutas nunca reporta su estado, y una comprobación requerida que no reporta bloquea el PR para siempre.

**Alternativa considerada:** dejar la CI fuera del change y anotarla. **Rechazada:** el arreglo es de una línea por fichero, y la spec de `backend-testing` está describiendo algo imposible — dejarla así es mantener una spec que miente.

### D8 · La contraseña de `admin` se documenta, no se cambia

`DatabaseSeeder` la declara como constante: `admin` / `Admin123!`. Ya es estable. Lo que falta es **escribirla en la entrega** y comprobar que el §5.3 del *runbook*, que reemplaza el personal real de la tienda de forma obligatoria, no la elimina.

**Alternativa considerada:** generarla y guardarla en SSM. **Rechazada:** movería una entidad sembrada por una razón cosmética, y añadiría un secreto a un inventario que la spec quiere corto.

### D9 · Se verifica con los tres operadores, no con dos

Existen, no cuestan nada, y cada uno enseña algo que el evaluador no encontraría solo:

| Usuario | Tienda | Qué demuestra |
|---|---|---|
| `op-ciutadella` | Ciutadella Centre | *flagship*, máximo surtido: el camino feliz — encuentra piezas y el argumentario se genera |
| `op-fornells` | Fornells | mínimo surtido retail, estacionalidad extrema: **abstención**, **sustitutos** y avisos de agotado |
| `op-aeroport` | Aeroport de Menorca | la *persona* del PF y el punto con más agotados —411 candidatos de 3.774; 13 de 48 consultas con una pieza agotada en el top-5—: donde **el pivote del agente a sustitutos** se demuestra |

Y un aviso heredado de la comprobación manual de C42, que hay que respetar en el recorrido: **el pivote es inalcanzable si el operario nombra la pieza por su nombre** en lugar de por su referencia, porque `buscar_catalogo` no devuelve el nombre del producto. El recorrido usa la **referencia**, que es lo realista en un mostrador porque la pieza lleva su etiqueta delante, y la limitación queda declarada.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| El *push* a `demo` cae íntegro en `paths-ignore` y parece desplegado sin estarlo | La tarea exige comprobar que el **workflow se ejecutó** y que el `IMAGE_TAG` de SSM cambió, no que el *push* llegó |
| Mover el contexto de *build* de `jbg-ai` engorda la imagen o rompe la construcción | El *build* de la API ya usa contexto de raíz y documenta que el `.dockerignore` lo contiene. **Se mide el tamaño del contexto y de la imagen antes y después**, y se publica |
| Tocar por error un fichero de la ruta de producción | La tabla de separación está en el diseño y hay un criterio de aceptación que lo comprueba **sobre el conjunto de ficheros modificados** |
| Encender la CI destapa cientos de rojos y se lee como una regresión del change | Entra informativa; `CLAUDE.md` documenta los rangos preexistentes, su rotación y las clases inestables. **Y se mide en serie**: las tres suites a la vez dan 490 rojos de 1.347 en backend donde en serie dan 53, porque `vitest` satura la máquina y *testcontainers* pierde la tubería de Docker |
| El entorno lleva cinco semanas sin el drenaje de C41 y su proyección está rancia | **Se cura con el propio *fast-forward***: el drenaje corre al arrancar, y **en su forma completa cuando no existe *checkpoint***. Se comprueba en la verificación, no se da por hecho |
| La cuota de una petición por minuto alarga el recorrido manual | Se acepta y se declara. Cuatro superficies por tres operadores caben en una sesión; **dos mostradores simultáneos no**, y eso es una limitación del entorno, no un defecto a corregir aquí |
| Un secreto se filtra al añadir dos parámetros | El patrón existente no se altera: sin `env_file:`, sin `set -x` cerca de la sección que los lee, y el registro dice *presente/ausente* y nunca el valor |
| El apaño manual del corpus siguiera en pie y enmascarase el hueco 4 | Irrelevante para el resultado: aunque hubiera sobrevivido al contenedor, **no sobrevive a la imagen nueva**. El tramo 0 lo mide para dejarlo escrito, no para decidir |

### Trade-off que el change acepta a la cara

**La imagen de `jbg-ai` crece.** Incorporar el corpus a la imagen es la razón por la que queda autosuficiente, y también por la que ocupa más. Es el precio de que un anfitrión nuevo no arranque con la tabla vacía, y se paga con el tamaño medido y publicado en lugar de estimado.

## Migration Plan

```
0 · foto del entorno                     lectura, nada se modifica
        │                                 parámetros por nombre · instancia · hostname · IMAGE_TAG
        │                                 y DESDE DENTRO: count(ai.knowledge_chunk), checkpoint
        ▼
1 · cambios en el árbol, sobre ai-eng    compose · deploy.sh · verify.sh · Dockerfile · workflows
        │                                 + dos parámetros creados a mano en SSM
        ▼
2 · demo ← ai-eng  (fast-forward)        84 commits, sin conflicto posible, sin migraciones
        │                                 el workflow construye y publica las dos imágenes
        ▼
3 · verificación                          desde dentro: 7 condiciones
        │                                 desde fuera: HTTPS, y sólo el proxy expuesto
        ▼
4 · recorrido manual                      4 usuarios × 4 superficies, con evidencia
```

**El orden de 1 antes de 2 no es indiferente.** Si `demo` alcanzase a `ai-eng` antes de que los cinco huecos estén cerrados, el despliegue publicaría un entorno con el panel del agente apagado y el corpus vacío, y habría que desplegar dos veces. Los parámetros de SSM pueden crearse en cualquier momento antes del paso 2, porque `deploy.sh` los lee en tiempo de despliegue.

**Rollback.** Cada pieza tiene el suyo y ninguno exige revertir código:

| Qué falla | Vuelta atrás |
|---|---|
| El argumentario del agente resulta caro o ruidoso | **Borrar `/jbg-demo/AGENT_LLM_API_KEY` y redesplegar.** La ruta vuelve a degradar, que es su estado declarado |
| Igual con el enrutador | Borrar su parámetro; el intent vuelve a `unclassified` y la ruta sirve lo de antes de C31 |
| El panel del agente estorba en la demo | `AiAgentAssist__EnabledByDefault: "false"`, un literal y un redespliegue |
| El entorno entero | `IMAGE_TAG` anterior es `sha-d6a740fa5e0b…`, y está registrado en SSM: `deploy.sh` acepta un tag por argumento |

## Open Questions

| # | Pregunta | Por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| **Q1** | ¿Las tres claves apuntan al mismo valor de proveedor, o a claves distintas? | **Parámetros distintos con el mismo valor**, que es lo que el *runbook* ya admite para la de *embeddings* |
| **Q2** | `jpv_agent_timeout_seconds` son 8 s **por vuelta**, el reloj del servicio 15 s y `AgentTimeoutMs` 18 s. ¿Aguanta el proxy? | Se **mide** en el paso 3 y se declara. **No se recalibra aquí**: movería una constante de la que depende un invariante que la suite afirma |
| ~~**Q3**~~ | ~~¿`ai.knowledge_chunk` está a cero en el entorno vivo?~~ | **CERRADA Y REFUTADA por medición el 2026-09-27: NO está a cero.** 161 fragmentos y 32 documentos, que es el corpus de C23 entero. El razonamiento que asumía lo contrario estaba mal, y el motivo es obvio en retrospectiva: **el corpus se indexa en la base, y la base vive en el volumen `jbg-demo-pgdata`**, cuya persistencia es un requisito vivo de esta misma capability —*«Data and certificates survive a redeployment»*—. El hueco del `Dockerfile` **no vacía la tabla**: impide **reindexar** y deja vacío un **entorno nuevo**. Sigue habiendo que cerrarlo por reproducibilidad, que es el argumento de D5 y no cambia, pero **su urgencia baja de «M2 y M3 están roscados en la demo» a «lo estarían en el próximo entorno limpio»** |
| **Q4** | ¿Se aprovecha para un dominio comprado? | **No.** El §6 del *runbook* lo cubre y no exige reconstruir, así que puede hacerse después |
| **Q5** | ¿La CI cubre también `ai-service`? | **No en este change.** No hay workflow de `pytest`; se declara como hueco |
