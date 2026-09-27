# Proyecto Final — Descomposición en changes OpenSpec

**Versión:** 3 — consenso tras la revisión de la [PR #4](https://github.com/skydr4g0n-it/joiabagur-pv/pull/4) y las [especificaciones funcionales v2](joiabagur-ia-especificaciones-funcionales-v2.md)
**Documento hermano de:** [proyecto-final-diseno-rag-joiabagur.md](proyecto-final-diseno-rag-joiabagur.md)
**Ventana:** arranque el 3 de agosto de 2026 · **prórroga abierta desde el 31 de agosto** — no hay fecha de entrega, el objetivo es entregar cuanto antes
**Equipo:** **1 desarrollador**, trabaja en Python, .NET y frontend
**Total:** **44 fichas** — **42 numeradas** (39 de la v3, más los partos de C06, C18 y **C30**) más `FIX1` y `C25bis`, fuera de la numeración C · **38 vivas** tras anular la rama de C19 y cortar C27 — **37 archivadas · 2 pendientes** *(recuento rehecho el 13 sep: la cifra anterior mezclaba dos bases, contando sólo las numeradas en el total y las 37 con `FIX1` y `C25bis` en las vivas)*

> **Dos supuestos de la versión 3 ya no valen, y conviene leer el resto del documento con eso puesto.** Se escribió para **dos personas** y con **entrega el 3 de septiembre de 2026**. Desde el 31 de agosto de 2026 hay **prórroga abierta** y el proyecto lo desarrolla **una sola persona**. En consecuencia: no se planifica por calendario ni por «carga por persona y semana», sino por **desbloqueo del grafo**; los marcadores 👥 son de una sola persona; y las olas del §5 se conservan como registro de lo ya ejecutado, no como plan.

---

## 0. Revisiones posteriores a la versión 3

Este documento se escribió antes de implementar. Cuando una sesión de diseño de un change concreto altera lo que su ficha decía, el cambio se registra aquí con fecha y motivo, y la ficha afectada se corrige en el sitio.

### 2026-09-27 — C39a-bis: el entorno está sano, el despliegue figura en rojo, y las cuentas del recorrido no existían

Aplicado el mismo día que C39a, sobre el entorno que su merge a `demo` desplegó. **Ninguna línea de
código.** Informe en
[c39a-bis-implementation-measurements.md](informes/c39a-bis-implementation-measurements.md).

**El despliegue ocurrió y el entorno está sano.** Ejecución `36322635852`: los doce primeros pasos en
verde —las dos imágenes construidas y publicadas—, `IMAGE_TAG` de `sha-d6a740fa…` (versión 8) a
`sha-2b357a1e…` (versión 9), idéntico a `git rev-parse origin/demo`. Las tres credenciales de generación
arrancan **propias**, sin ningún `assist_fallback`. Certificado real de **Let's Encrypt** y sólo 80 y 443
abiertos.

#### El hallazgo: una condición de verificación juzga mal un entorno correcto

**La ejecución figura en `failure` por un solo motivo, y es un falso positivo.** La quinta condición de
`verify.sh` falla si algún punto de venta carece de surtido, contando
`count(DISTINCT pos_id) FILTER (WHERE is_assigned_hint)` **sin preguntar si la tienda está activa**. El
señalado es `HT-ARTRUTX`, **declarada inactiva a propósito desde C10** (`is_active: false`,
`closed_after: 2025-09-30`) y la única de las doce; conserva sus 144 filas con la asignación retirada,
que es lo correcto. Los once activos van de 241 a 1.082 filas. El experimento: **`1` sin el filtro de
actividad, `0` con él**.

**Y el arreglo no puede vivir donde parecía.** Comprobado: el rol `jbg_ai` recibe `permission denied for
table PointOfSales`, así que la decisión D9 de C41 —Python no lee `public`— **está impuesta por los
permisos**, no sólo elegida. La vía barata es comprobarlo desde el anfitrión como superusuario, donde
`verify.sh` ya corre. **De paso refuta a C41**, cuyo `qa.md` había visto este mismo `1` y escribió que
«fallaría el despliegue, que es lo correcto».

#### Las cuentas de demostración no existían, y es el segundo hallazgo

**La premisa de la propia delta de este change era falsa.** No había `admin` activo más tres operarios:
había **dos** cuentas `demo.*`, `admin` **desactivada a propósito** —el sembrador la recrea con una
contraseña que es constante de un repositorio público— y las dos operarias sintéticas del volcado
renombradas a `retirado-*` y desactivadas. `op-ciutadella`, `op-fornells` y `op-aeroport` **sólo vivían
en el mundo sintético local**. Con un único operario activo ligado a `MAO-AIR`, **la abstención, los
sustitutos y el pivote no se podían demostrar en absoluto**.

Decidido con el responsable durante el apply: se **aprovisionan los tres operarios** por SQL contra la
base desplegada —rol `Operator`, hash BCrypt `2a`/12 generado fuera del anfitrión, contraseña que ya era
constante pública—. Acto seguido, y a petición del responsable, se **desactiva `demo.operador`**:
estaba ligada a `MAO-AIR`, que `op-aeroport` ya cubre, así que era una segunda credencial para un
mostrador que ya tenía la suya. Desactivada y **no borrada, porque la referencian 3.380 ventas**. El
entorno queda con **cuatro cuentas que entran** —un administrador y un operario por tienda—,
declaradas en el nuevo **§5.8 del *runbook***. Son mutaciones de un entorno público que **no aparecen
en ningún diff**, y por eso se escriben.

**`demo.admin` es el único administrador que puede entrar**, y su contraseña **no está en el
repositorio** —correctamente—. Con ella, aportada por el responsable, **la tarjeta de salud de la IA
quedó ejercitada**: `200`, índice en 1.200, proyección `ok`. Y esa lectura añadió dos cosas. Una:
`shopsWithoutScope: 1` aparece **al otro lado del proxy**, de modo que el falso positivo llega en rojo
hasta la pantalla del evaluador. Otra: el mismo panel avisa en **`CRITICAL`** de que no existe modelo de
reconocimiento de imagen, y **no puede existir**, porque el catálogo sintético tiene **0 fotos de 1.200
productos** — funcionalidad del MVP, no del PF. **Dos rojos en la misma pantalla y ninguno señala nada
roto**; el segundo queda anotado como tarea diferida.

#### Lo que se confirmó, y lo que se refutó

| | |
|---|---|
| **Confirmado** | La proyección **se cura sola**: de ~115 veces el techo a `stale: false`, cero páginas fallidas, drenando cada 600 s. El corpus sigue en **161**. El pivote del agente funciona **por referencia**: 4 iteraciones con `buscar_sustitutos` |
| **Refutado** | Las siete condiciones **no** están en verde: seis, y la séptima falla por estricta. La CI no corrió dos veces sino **cuatro**. La suite de frontend **nunca había corrido**: moría en un lint imposible, porque `eslint.config.js` no existía. Y el pivote **por nombre** no ocurre: 3 iteraciones, 2 herramientas, ninguna de sustitutos |

**Dos matices de la confirmación de la proyección**, que conviene no tapar: la cura es del drenaje
**incremental** —`last_full_sync_at` sigue en el 22 de septiembre— y **el registro del despliegue no la
vio**, porque el informe de salud se cachea 10 s y el drenaje de arranque necesitó dos intentos
(`feed_not_configured` en el primero). El log dice `stale: true` seis segundos después de que dejara de
serlo.

#### La CI, medida por primera vez de verdad

Cuatro ejecuciones el 2026-09-27: el par `pull_request` y el par `push`, duplicación que motivó retirar
después el disparo por `push`. Backend **49 y 48 de 1.408**, con **trece nombres rotando y los trece
dentro de las clases que `CLAUDE.md` declara inestables** — lo que añade un dato nuevo: **la rotación no
es un artefacto de la máquina de desarrollo**, se reproduce en un *runner* limpio. Frontend, provocado a
mano con `workflow_dispatch`: **113 de 959 en 14 de 63**, **idéntico cifra por cifra y fichero por
fichero** a la línea base local de C39a. Lint: **89 errores y 82 avisos**, declarados y no arreglados.
Y **no bloquean**: ninguna rama tiene protección configurada.

#### Lo que queda pendiente, dicho y no dado por hecho

**Sin navegador en la sesión, no hay capturas.** El recorrido ejercitó los mismos *endpoints* que llaman
las pantallas —y con eso quedan medidos el argumentario generado con citas, la abstención, los
sustitutos, el aviso de agotado, el pivote, el ámbito global y el rechazo del enrutador—, pero **las
cuatro tarjetas no se han visto**. La tarjeta de salud **sí quedó ejercitada por su ruta**, con la
credencial que aportó el responsable; de las cuatro superficies de IA existe la respuesta de la API y no
la pantalla que la pinta.

### 2026-09-27 — C39a se implementa, se parte otra vez, y refuta tres cosas propias

Implementado el mismo día que se escribió. **Se parte en C39a y C39a-bis durante su propio apply**, y el
motivo es de orden: sus tareas de verificación exigían un entorno desplegado, y **el despliegue ocurre al
mergear el change a la rama `demo`**. Un change que sólo se puede archivar después de archivarse no es un
change. C39a queda con todo lo previo; **C39a-bis** (`verify-demo-redeployment`) recorre el entorno
resultante y toca **sólo** ficheros que el `paths-ignore` de `deploy-demo.yml` ignora —`openspec/**`,
`Documentos/**`, `**/README.md`, `CLAUDE.md`, `AGENTS.md`, `terraform/**`—, así que **verificar no cuesta
un redespliegue**. Informe en
[c39a-implementation-measurements.md](informes/c39a-implementation-measurements.md).

#### Las tres refutaciones, que son el valor de la pasada

| Refutado | Qué se creía | Qué se midió |
|---|---|---|
| **El corpus estaba vacío** | `ai.knowledge_chunk` a cero, con M2 y M3 roscados en la demo | **161 fragmentos y 32 documentos**. El corpus se indexa en la base y la base vive en `jbg-demo-pgdata`, cuya persistencia es requisito vivo. El hueco impide **reindexar**; no vacía nada. Urgencia rebajada, cierre igual |
| **D5: mover el contexto de *build* a la raíz** | la imagen quedaría autosuficiente | **habría roto el desarrollo local**: `backend/docker-compose.yml` construye el mismo `Dockerfile` con `context: ../ai-service`. Sustituido por un **contexto adicional con nombre**, que además **falla en voz alta** si se omite — comprobado, código 1 |
| **El corpus sólo faltaba en la imagen** | una línea `COPY` y listo | **la ruta que el servicio lee estaba mal calculada**: `CORPUS_DIR` resolvía a `/app/.venv/lib/data/knowledge`, dentro del árbol de dependencias. Copiar sin arreglarlo habría tapado el defecto |

**Y el arreglo de la tercera amplía la zona del change a `ai-service/src`**, decidido sobre una medición y
no por ensanchar alcance: `CORPUS_DIR` pasa a resolverse por **la misma búsqueda de tres candidatos que
`load_prompt_file`**, cuyo *docstring* describe este problema literalmente —*«a second copy of this search
would be a second place for a container layout to diverge from a developer checkout»*—. Ésa es la razón de
que los prompts sí funcionaran y el corpus no: `PROMPTS_DIR` **tampoco existe** en el contenedor, y da
igual porque nadie lo usa. Cierra la tarea diferida de C34 **con dos arreglos y no uno**.

#### El interruptor del agente es la TERCERA vez que el mismo defecto llega al mismo fichero

Y eso lo descubre la implementación al buscar dónde ponerlo, porque el comentario del hueco de al lado ya
lo cuenta: **C17** lo encontró para la búsqueda asistida —200 con resultados de la ruta léxica y la IA
nunca llamada—, **C40_FIX** para la consulta libre —el panel generativo entero apagado para todas las
tiendas—, y **C39a** para el agente. Los cuatro interruptores son `bool` sin inicializador con lista de
puntos de venta vacía, así que **omitir uno no es un valor por defecto neutro**: apaga la ruta. Es el
argumento del escenario que la delta añade a `demo-deployment`.

#### Dos cosas más que la pasada deja medidas

**La proyección está a unas 120 veces el techo de rancidez** —último drenaje incremental el 22 de
septiembre contra un techo de 3.600 s—, y **`verify.sh` no lo habría visto**: su quinta condición cuenta
filas ausentes, nunca antigüedad. Se cura sola con el *fast-forward*, porque el drenaje de C41 corre al
arrancar; medirlo es de C39a-bis. Cuando C41 se justificó midió **14,4 veces**. **Medido: la predicción
se cumple** —de ~115 veces el techo a `stale: false` con cero páginas fallidas—, y de paso se descubre
que la quinta condición sí falla, pero por otra cosa y **sobre un entorno sano** (§0, C39a-bis).

**Y un desvío que no estaba en el ticket y bloqueaba todo:** el bundle de CA de la máquina de desarrollo
**caduca**. Norton rota su raíz de interceptación, y el fichero de agosto ya no la contenía: toda llamada a
AWS moría con `CERTIFICATE_VERIFY_FAILED` **incluso apuntando al bundle explícitamente**, que se lee como
un problema de perfil y no lo es. Regenerado, de 131 certificados a 253. Va al §1.3 del *runbook* como nota
de caducidad, que es lo que no decía.

### 2026-09-27 — C39 se parte en C39a y C39b, y el despliegue deja de ser documentación

Misma sesión que retira C38, una vez decidido que la cola quedaba en un solo change. Al mirar **qué
tendría que contener ese change** aparece que su propia ficha se equivoca en una palabra: dice
**`Zona. docs`**, y el redespliegue de la demo en AWS no es documentación.

#### Por qué se parte, y el orden no es indiferente

**No se documenta un recorrido que no se ha recorrido.** El README tiene que decirle al evaluador que
entre con unas credenciales y pruebe cuatro pantallas; escribirlo antes de haber comprobado que esas
cuatro pantallas responden en el entorno desplegado es escribir una hipótesis. Es exactamente el
patrón que este proyecto ya ha pagado cuatro veces: **C40, C41, C42 y `C40_FIX` nacieron de
comprobaciones manuales**, no de ninguna ola, y los cuatro destaparon cosas que las tres suites verdes
no veían — el panel sirviendo por su ruta degradada, los filtros descartándose en silencio, el ámbito
global inalcanzable, el pivote inalcanzable por nombre.

| | |
|---|---|
| **C39a** `redeploy-and-audit-demo-environment` | El entorno desplegado, **accesible desde internet** y verificado recorrido a recorrido, con la auditoría de `compose.demo.yaml` contra los ajustes que declaran los tres servicios |
| **C39b** `finalize-pf-readme-and-evidence` | README de entrega, vídeo, tag, evidencias y las tres tareas que sobreviven a C38 |

#### Cuatro huecos ya medidos, y ninguno es una conjetura

La exploración auditó `compose.demo.yaml` contra las opciones que declaran los tres servicios, y el
resultado es que **redesplegar hoy tal cual dejaría el pilar de agentes invisible**:

| Hueco | Consecuencia |
|---|---|
| **`AiAgentAssist__EnabledByDefault` ausente** | `public bool` sin inicializador, o sea **`false`**. La cuarta tarjeta de C42 **no se sirve** y el panel del agente no aparece: el único pilar que no se puede enseñar de otra forma |
| `JPV_AGENT_LLM_API_KEY` ausente | la ruta del agente degrada por falta de credencial — uno de los dos estados de pantalla que C42 declara **nunca observados en producción** |
| `JPV_ROUTER_LLM_API_KEY` ausente | el enrutador repliega a la clave de assist (`credential=assist_fallback`, ya observado en el log de C34). Funciona y **no es lo declarado** |
| **el corpus de conocimiento no viaja en la imagen** | tarea diferida de C34, **sorteada a mano y no resuelta**: `CORPUS_DIR` apunta a `data/knowledge` y el `Dockerfile` copia sólo `src`, `migrations` y `prompts`. Con `ai.knowledge_chunk` a cero, **M2 retira el argumentario y M3 responde `knowledge_not_covered`** — y parece un fallo del card |

#### Y el hallazgo mayor, que la auditoría encontró después: **la rama `demo` está en C34**

El despliegue se dispara por `push` sobre la rama **`demo`**, y medido el mismo día: `origin/demo` está
**84 commits por detrás** de `ai-eng` y **cero por delante** —es un ancestro estricto—, con su último
commit en el QA de C34, del 22 de septiembre. Lo desplegado **no contiene C36, C40, C40_FIX, C41 ni
C42**: la ficha de venta, el panel de consulta libre con su ámbito global, el drenaje de la proyección y
el panel del agente. **Cuatro de las cinco superficies más visibles del PF no están desplegadas**, así
que el «redespliegue» es ante todo un *fast-forward*.

Con él aparecen **dos cosas más** que entran en C39a: **`verify.sh` no cubre la ruta del agente ni el
recuento de fragmentos** —los dos fallos silenciosos, misma familia que la proyección vacía que C41 ya
cerró— y **la CI no se ha ejecutado nunca, ni una vez**: `test-backend.yml` y `test-frontend.yml`
disparan sobre `branches: [main, develop]` y **ninguna de esas dos ramas existe**. Entra como
**informativa y no como puerta**, porque con 53 fallos preexistentes en backend y 113 en frontend *«una
puerta sobre una suite roja no es una puerta»*. Y el defecto hermano —que producción se redespliega ante
cualquier cambio— **sigue siendo de otro change**, porque la spec de C17 exige que ese flujo quede
inalterado.

**Tres correcciones de la propia auditoría, para que no se hereden mal.** `AiGatewayOptions.AgentTimeoutMs
= 18_000` **ya existe**, así que la tarea diferida de C32b sobre el *timeout* de la ruta del agente está
casi cerrada. El corpus **no es una línea `COPY` que falte**: el *build* usa contexto `ai-service` y el
corpus vive en la raíz, **fuera del contexto**, así que hay que mover el contexto como ya hace el *build*
de la API. Y la contraseña de `admin` **ya es estable** —constantes `admin` / `Admin123!` en
`DatabaseSeeder`—: lo que falta es escribirla, no fijarla.

**Lo que la auditoría también establece, y evita trabajo:** los dos *stacks* de Terraform —14 variables
en `terraform/`, 10 en `terraform/demo/`— **no tienen una sola variable de IA, y es correcto**. La
configuración de IA vive en `compose.demo.yaml` como literal versionado y en SSM bajo `/jbg-demo/`
como secreto creado a mano, deliberadamente fuera del *state*. Así que **C39a no añade variables de
Terraform**: audita el compose y la lista de secretos del runbook.

#### Y las credenciales del evaluador ya existen, con sus diferencias diseñadas

No hay que crear usuarios. `admin` lo siembra `DatabaseSeeder`; los tres operadores vienen del mundo
sintético de C10 con `Operator123!`, y sus perfiles **ya contrastan** por diseño: `op-ciutadella`
(*flagship*, máximo stock) enseña el camino feliz; `op-fornells` (mínimo stock retail, estacionalidad
extrema) enseña abstención, sustitutos y avisos de agotado; `op-aeroport` es la *persona* del PF y el
punto con más agotados —411 candidatos de 3.774, y 13 de 48 consultas con una pieza agotada en el
top-5—, que es donde **el pivote del agente se demuestra**. Lo único que hay que cerrar es que la
contraseña de `admin` sea **estable y escrita**, porque hoy el seeder la deja con la nota de
cambiarla al primer acceso.

### 2026-09-27 — C38 se retira entero, y lo decide que sus datos ya están medidos

Sesión abierta para explorar **la implementación** de C38 y cerrada retirándolo. Es el segundo corte
sobre la misma ficha en dos días —el 26 perdió RAGAS— y esta vez cae lo que quedaba. **Se decide por
valor marginal y sobre mediciones tomadas en la propia sesión**, no por plazo, y con la prórroga
abierta desde el 31 de agosto no hay ninguna fecha que lo empuje.

#### Pieza por pieza, y ninguna sobrevive por el mismo motivo

| Pieza | Qué encontró la exploración |
|---|---|
| **Validador determinista** | Su mitad .NET es **un espejo**: la regla que aplicaría —ninguna cifra pegada a una marca de moneda o de existencias— es **la misma** que la puerta numérica de Python ya aplica **al mismo texto**, así que todo lo que .NET rechazaría Python lo rechazó antes y la cifra esperada es **cero**. Sigue siendo un seguro defendible, porque de los tres caminos **sólo la ficha de venta comprueba algo en .NET** —`FreeQuerySearchService` y `AgentAssistService` hacen `Pitch = ai.Pitch` y `grep "{{\|Resolve"` sobre los dos devuelve **cero líneas**—, pero es un seguro y no un arreglo: `placeholder_in_free_query` es **causa dura** desde C40 y C42 midió **0 marcadores de 102** |
| **Escenarios del agente** | **Los datos ya existen y están committed.** Los 20 escenarios de `evals/agent/calibration.yaml` se han corrido **dos veces contra el proveedor real** —C32b con dos brazos, C42 con `gpt-4o` y `assist/v6`— y cada fila trae ya el veredicto por escenario y los campos de estado terminal. No falta una pasada: falta **una definición de éxito** y un párrafo |
| **Adversarios** | La única que arranca de verdad en cero. Lo que hay son **dos** tests y los dos son estructurales —que el mensaje de sistema no cambie, `test_prompt.py:269` y `test_transcript.py:74`—; ninguno mide si un modelo obedece una inyección. Es la pieza con más trabajo nuevo y menos apoyo existente |

#### Las dos mediciones que lo deciden

Tomadas **sobre artefactos committed**, sin llamar al proveedor, y por eso reproducibles por
cualquiera con `--rescore`:

1. **17 de 20 escenarios cumplen su expectativa**, sobre la pasada de C42 —`c32b-agent-sweep-17fbdd15a18c.json`, 102 peticiones, `gpt-4o`, `assist/v6`—. Los tres fallos son **C14** (elíptico, no llamó a `buscar_catalogo`), **C17** (guardarraíl) y **C19** (abstención, y su discrepancia **ya estaba declarada** en el propio conjunto).
2. **El ruido entre pasadas es 2 de 20, un 10 %.** Puntuando el brazo `gpt-4o` de C32b y el de C42 contra el fichero de escenarios de hoy, el veredicto coincide en **17 de 20**; de los tres que discrepan, **C05 cambia porque el escenario se corrigió** tras la primera pasada y está documentado en la cabecera del fichero, así que los vuelcos reales son **C14 y C17**.

**La segunda cifra es la que cambia qué se puede publicar.** Con un 10 % de ruido, una *«tasa de éxito
del 85 %»* sería una precisión fingida. Lo publicable es **«17 de 20, y éstos son los tres que fallan
y por qué»** — que además es más informativo, y es lo que ya hizo el informe de C32b.

#### Y la objeción que remata: el agregado no necesita pantalla, porque el comportamiento ya la tiene

El panel de C42 **pinta la traza del bucle** —herramientas por vuelta, iteraciones, motivo de
parada—, así que el pivote a sustitutos se enseña **en vivo** en el vídeo. El agregado, en cambio, es
una fila de la sección de evidencias del README, exactamente como el golden set, la tabla de
ablations, la matriz de confusión de C31, el 20,9 % de C28, el ×3,0 de C32b y las cinco cifras de
C40: **ninguna de ellas tiene pantalla, y nadie la espera**. Un número de evaluación en una pantalla
de mostrador sería lo raro.

#### Lo que esto tiene en contra, dicho antes de que lo diga el lector

**Se pasa por encima del §6**, que lista *«Nunca se recortan: … el validador de C38 y C39»*. Es la
primera vez que un elemento de esa lista se retira, y queda escrito aquí en vez de descubrirse al
comparar el README con el plan. El argumento que lo sostiene es el mismo que retiró RAGAS el día
anterior —*«evals reales, no sólo pruebas manuales»* ya está demostrado— y ahora con **ocho** fuentes:
C24, C25, C28, C30b, C31, C32b, C40 y C42.

**Lo que sobrevive son tres tareas dentro de C39**, no una rama: definir el éxito de tarea, emitir la
tabla con `--rescore`, y escribir la limitación del validador .NET no implementado con su vía de
cierre. Con ello **la cola pendiente del Proyecto Final queda en un solo change, C39** — que la misma
sesión parte acto seguido en **C39a** y **C39b**, por el motivo que la entrada de arriba explica. Las
tres tareas supervivientes caen en **C39b**.

### 2026-09-26 — Nace C42, C38 se reduce y RAGAS se retira

Una sola sesión, abierta para decidir qué hacer con la cola pendiente —C38 y C39— y **si merecía la
pena implementar C38 entero**. Sale con dos decisiones que se sostienen la una a la otra, y con un
hallazgo que ninguna de las dos buscaba. Exploración completa en
[c42-exploration-decisions.md](informes/c42-exploration-decisions.md).

#### C38 se reduce, y el corte lo tenía pre-escrito

El alcance de C38 eran **cuatro piezas independientes**, y su propia ficha llevaba escrito desde el
principio el orden en que se parten: *«validador → escenarios de venta → adversarios → RAGAS. **RAGAS
es lo primero que se cae**»*. Se dispara ese corte, y **por valor marginal y no por plazo**:

| Pieza | Qué había ya | Qué faltaba de verdad |
|---|---|---|
| Validador | La puerta numérica **corre en ejecución** desde C30b, con 0 violaciones en 120 generaciones; `evals/free_query_gate.py` mide el modo libre | Consolidarlo y su equivalente .NET. **Poco** |
| Escenarios de agente | `agent_sweep.py` conduce el bucle real, persiste traza rica y tiene `--rescore` | **Anotación**, no código |
| Adversarios | Defensas escritas con tests unitarios (delimitadores, `transcript.py`) | Un conjunto con tasa de bloqueo por categoría. Anotación otra vez |
| **RAGAS** | **Nada** | Dependencia pesada, juez LLM, cableado a LiteLLM, cuota y el MITM de Norton de esta máquina |

**Lo que el §5 de la convocatoria premia —*«evals reales, no sólo pruebas manuales»*— ya está
demostrado y de sobra**: golden set de 72 consultas con escala de tres grados, *pooling* y dos
lecturas (C24); ablations v0→v3; matriz de confusión del enrutador sobre 119 casos (C31); barrido del
agente con p50/p95 y coste por brazo (C32b); 20,9 % / 10,4 % / 42,3 % de revisión humana sobre 204
perfiles (C28); y las cinco cifras de C40. **RAGAS añadiría una fila más a un informe ya denso.**

Se retira, y **la retirada es en sí misma defendible ante el otro epígrafe del §5** —*«se identifican
limitaciones actuales y se propone cómo resolverlas»*—: la *alucinación con coartada* pasa a
limitación declarada con su vía de cierre escrita, coherente con el §11.3, que ya había decidido *«sin
LLM juez»* para el camino de servicio. **Coste de reescritura, medido:** cero referencias en specs
vivas; cuatro comentarios de código y una línea de README.

#### Nace C42, y el motivo es que un pilar no se puede enseñar

El PF nombra cinco: CAG, RAG, **agentes**, evaluación y despliegue. El agente está entregado, probado
y medido con proveedor real desde C32b, y **`IAiGatewayClient` no tiene método para él**: no hay
pantalla, así que no aparece ni en la URL pública ni en el vídeo. Y el §5 es tajante —*«si el
evaluador no puede acceder al sistema funcionando, el proyecto no puede evaluarse correctamente»*—.

C42 le da superficie: ruta propia, cuarta tarjeta en el hub y un panel de conversación que **pinta la
traza del bucle**, que es la única prueba en pantalla de que hay un agente y no un prompt. No se
sirve por defecto: su única cifra comparativa dice **×3,0** de coste y **13,1 %** de retirada contra
2,2 %, así que entra como **demostración de ablación** y no como modo del mostrador.

#### Y un hallazgo que ninguna de las dos decisiones buscaba

**C40 dejó una regresión latente en el agente sin tocarlo.** Tres eslabones correctos por separado:
la tarea del agente vive en **`assist/v4`**, cuyo *Sistema* ordena escribir `{{price}}` y `{{stock}}`
**siempre**; su payload es un `FreeQueryPayload` con **`is_anchored = False`**; y C40 metió
**`placeholder_in_free_query` en `HARD_VIOLATION_CAUSES`**, que dispara exactamente cuando el payload
no está anclado. Juntos: **el argumentario del agente se retira por construcción**. C40 arregló las
tareas de consulta libre en `v5` y no tocó ésta, porque el agente no tenía consumidor y nadie iba a
ver el resultado.

Eso encadena el orden de los tres pendientes: **C42 antes que C38**, porque C42 sube la tarea del
agente a `assist/v5` y unas cifras de generación tomadas antes describirían un prompt sustituido —la
misma razón por la que C40 fue antes que C38—.

> **La tasa real no está medida, y se dice.** Esta exploración se hizo **contra el código**, no
> llamando al proveedor. La cadena es inequívoca; el número no existe todavía, y es la primera cifra
> que C42 debe publicar. Referencia comparable, de C30b sobre modos anclados con `v3`: `{{price}}` en
> **147 de 213** y `{{stock}}` en **188 de 213**.

### 2026-09-21 — C34 explorado: sólo el card, y unos marcadores que no dicen de quién son

**La anotación del 14 de septiembre que daba a C34 la ruta de la consulta libre es falsa en su
premisa.** Decía *«ninguna hidratación nueva: no hay más `{{price}}` ni `{{stock}}` que los de los
candidatos»*. Pero los dos tokens no llevan referencia a una pieza. En M2 y M3 da igual, porque sólo
hay una. En M1 y en el agente, el prompt pide hablar de **varias piezas** con los mismos dos tokens,
y .NET no puede asignarlos sin adivinar, cuando el propio prompt llama a una cifra equivocada *«un
error de venta»*. **C34 se queda con las dos rutas del card**, y el §15.12 del diseño (*«la pregunta
libre sin pieza elegida no tiene pantalla»*) sigue siendo cierto. El arreglo que lo desbloquearía es
de Python y es pequeño: prohibir los marcadores en las tareas sin pieza anclada, porque las filas ya
enseñan el precio hidratado. Queda identificado y no hecho.

**Cinco mediciones reproducibles decidieron el resto**, tres sobre la base local y dos sobre el
artefacto de C30b:

| | medido | qué decidió |
|---|---|---|
| Latencia del argumentario, en el ancho que se sirve | p50 3,8 s · p95 5,2 s · **7,5 % por encima de 5 s** · 55 % con reparación | El presupuesto de .NET pasa de **5 s a 10 s**, derivado del peor caso de Python (2 × 4 s), y **sin reintento en timeout** |
| Cómo escribe el modelo `{{stock}}` | **88,3 %** como número («tenemos {{stock}} en tienda») | Se sustituye por el entero, no por «N unidades» ni por una etiqueta |
| `family_has_variants` después de hidratar | **19,2 %** falso en las tiendas | .NET lo recalcula sobre los miembros que ese punto de venta lleva |
| Ventana de sustitutos | Con `top_k = 5`, en Fornells el **71,1 %** no llena una página de 5; con `top_k = 20`, el 7,1 % | .NET pide siempre la ventana máxima |
| Umbral de stock bajo | `≤ 2` salta en el 4,2 % de las filas con stock; `≤ 5`, en el 14,4 % | `stock_critical` = 1 o 2 unidades, configurable, frente a las dos definiciones incompatibles que ya hay en .NET |

**Cuatro decisiones se cerraron con el desarrollador:** sólo el card; `POST` con `question` en el
cuerpo, porque en una URL la pregunta del cliente acaba en el log de nginx; con la pieza anclada sin
stock, el argumentario se retira si no hay pregunta y se conserva si la hay; y **encender la
generación en la demo es la última tarea de C34**, así que su zona gana `deploy/demo/` y
`compose.demo.yaml`. **Un cambio de política respecto a la ficha**: un marcador sin resolver retira el
argumentario y **no la respuesta**, que es lo que ya hacen las puertas de C30b.

Ficha corregida en el sitio. Informe con las catorce decisiones, sus alternativas descartadas y el
SQL de cada cifra: [`c34-exploration-decisions.md`](informes/c34-exploration-decisions.md).

### 2026-09-21 — C32b implementado: el sobrecoste es ×3,0 y el brazo barato no sostiene la selección

La pasada `293fe5c6e470` —**204 peticiones, dos brazos, 3,82 USD y 3,4 h**— refuta el número
central de la ficha y una de sus dos mitades:

| | ficha | medido |
|---|---|---|
| Sobrecoste del agente | ~×19 | **×3,0** (0,0274 USD/petición contra ~0,0092 del pipeline) |
| Brazo barato | «el ×4 es elección reversible con una variable» | **×1,1 en precio, pero topa un presupuesto en el 66 % de las peticiones** contra el 1,2 % del caro |

> **Corregido por la verificación independiente del mismo día.** Esta entrada publicaba **×7,6,
> ×1,4 y ~2,60 USD**. El clasificador se había tarifado a 0,00205 USD, una cifra atribuida a C31
> que C31 nunca publicó; el artefacto lo mide a **0,0084 USD** (~3.305 tokens de prompt en
> `gpt-4o`), y es lo que domina el coste del *pipeline*. Las cifras salen hoy de
> `python -m jbg_ai.evals.agent_sweep --rescore`, sin proveedor, y un test las fija. La misma
> verificación corrigió el reloj —ahora acota la petición entera, argumentario incluido—, la tabla
> de pivote, que sumaba los dos brazos, y cuatro tests que no afirmaban lo que decían: ver el §12
> del QA de C32b.

**El ×4 de modelo es reversible en el precio y no en el comportamiento.** `gpt-4o-mini` no elige
peor: **no sabe parar** — 50 `presupuesto_tools` y 4 `presupuesto_iteraciones` sobre 82
transcripciones, y 168 llamadas devueltas con `presupuesto_agotado` contra 5. Q-7 queda
respondida en no, con el mismo desenlace que C31 midió para el clasificador y por otro síntoma.

**Tres presupuestos dejan de ser marcadores y pasan a ser mediciones**: tokens **40.000**
(p95 16.244 de clasificador + bucle, que es lo que el presupuesto compara), contexto **30.000**
caracteres (p95 4.709) y reloj **15,0 s** (p95 9,0 s) **para la petición entera**, que **tensa** el
peor caso de 20 s que el diseño había declarado — desde la verificación independiente, porque el
bucle corre contra 15 s menos 8 s de reserva para el argumentario; antes el reloj sólo se miraba
antes de cada vuelta y el peor caso por construcción eran 31 s. El techo de herramientas sube de 6
a **8** tras medir p95 5 con un 3,9 % truncado — y con el aviso de que de esas peticiones
truncadas **nadie sabe cuántas llamadas habrían usado**, así que el 8 es un juicio informado.

**O-5 se cierra con el dato:** la curva de crecimiento va de 1.974 a 3.470 tokens entre la vuelta
1 y la 5, casi lineal. **No hace falta compactar.**

**Las dos preguntas de C32a quedan respondidas:** cero herramientas muertas, **cero nombres
inventados** y cero llamadas consecutivas idénticas; y la etiqueta cualitativa es **compatible**
con gobernar el pivote: `gpt-4o` pivota en 3 de 3 escenarios sin existencias y en **ninguno** de
las tres etiquetas caras, sobre un escenario por etiqueta — la evidencia que C38 tiene que ampliar.

**Lo que queda abierto y medido:** se retira el **13,1 %** de los argumentarios de `gpt-4o`
—**9,5 puntos por `dangling_citation`**, el resto *timeouts* del argumentario y otra causa— contra
el 2,2 % de la ruta determinista. Y una restricción operativa que ninguna ficha anticipaba:
**la cuota de tokens por minuto de la organización**, y no el dinero, es lo que fija el reloj de
una medición de agente — a 25.000 TPM con peticiones de ~13.000 tokens cabe **una por minuto**.

### 2026-09-20 — C32 se parte en C32a y C32b, y tres supuestos de su ficha se caen contra el árbol

**C32 se desdobla por la regla 5 del §1** —*«si un change se desborda de la sesión, se parte y se entrega primero la mitad que desbloquea el grafo»*—, con el mismo corte que funcionó en C30: **la mitad que no llama a ningún proveedor va primero**.

| Mitad | Qué entrega | Llamadas a LLM |
|---|---|---|
| **C32a** `add-sales-assistant-tool-registry` | las seis tools, el registro, los esquemas de *function calling*, el invariante de solo-lectura comprobado por introspección y la etiqueta cualitativa de disponibilidad | **cero** |
| **C32b** `add-sales-assistant-agent-loop` | el bucle, los tres presupuestos, `partial: true`, la traza, `POST /v1/assist/agent` y la tarea de prompt del agente | sí |

**El corte vuelve a dejar una ablación gratis**, igual que el de C30: C32a es un registro de herramientas medible por sí solo —cada tool se prueba contra su puerto sin que nadie decida nada— y C32b añade **la capa de decisión como pieza separable cuyo valor se mide contra el pipeline determinista de C31**. Esa fila —*pipeline contra agente, mismo golden set, mismas tools*— es la que el §11.4 del diseño pide, y es la que desaparecería si el bucle **sustituyera** al pipeline en vez de convivir con él.

**Convención de lectura:** donde este documento dice **C32** sin sufijo —y todas las notas fechadas antes del 20 de septiembre lo dicen— se refiere **al par**. Los prerrequisitos, el grafo del §4 y las tablas de los §5 y §6 sí llevan sufijo, porque ahí la distinción decide qué se abre.

**Cuatro decisiones de arquitectura quedan tomadas en la exploración**, las cuatro con su alternativa descartada por escrito:

1. **El bucle vive en ruta propia, `POST /v1/assist/agent`, y `/v1/assist/sale` no se toca.** No es preferencia: el peor caso del bucle es **2 s de enrutador + 5 vueltas + 4 s de argumentario ≈ 15-20 s**, contra los **5 s** que el §6.4 del diseño declara para `/v1/assist`. Un *flag* en la ruta existente pondría ese camino en la misma que C34 va a llamar síncrona desde el mostrador, y obligaría a meter `partial` y la traza en el `AssistResponse` que C34 y C36 leen. La ruta nueva es **adición pura** al contrato —ningún campo se retira ni cambia de tipo—, que es la verificación hoja a hoja que C31 ya ejecutó.
2. **`consultar_disponibilidad` se sirve desde `ai.pos_projection`, no desde .NET.** El §6.1 del diseño dejaba el esquema de la llamada de vuelta Python → .NET como *«decisión abierta del change del agente de venta»*, y la exploración la resuelve **difiriéndola con motivo**: no hay que inventar un esquema de autenticación de vuelta para un dato que Python ya tiene proyectado. El endpoint .NET queda **identificado, acotado y no hecho**, con la tool diseñada para que sea un reemplazo directo.
3. **El bucle reúne evidencia; redacta `generate_pitch()`.** Si la última vuelta escribiera prosa se esquivarían de golpe la puerta numérica por lista blanca, la integridad referencial de las citas y la reparación única, las tres de C30b. El invariante que lo hace comprobable es nuevo y es un test: **el contenido textual de las vueltas del bucle se descarta; sólo se honran sus `tool_calls`**. De paso resuelve solo el *«nada se persiste»*, porque el razonamiento intermedio no sale del proceso.
4. **El multi-turno viaja en la petición y el servicio no guarda nada.** Los 20-25 escenarios multi-turno del §11.4 no caben en un contrato sin estado, y un almacén de sesión chocaría de frente con la propiedad que C30b y C31 dejaron con test. La transcripción la envía el cliente, **con dos consecuencias que ninguna ficha tenía escritas**: el delimitado `QUERY_OPEN`/`QUERY_CLOSE` de C30b hay que aplicarlo a **cada turno** y no sólo al último —una inyección se esconde en el turno 3—, y **los turnos del asistente son falsificables**, así que se tratan como dato igual que la consulta y con tope de turnos y de caracteres, porque el contexto acumulado es el factor dominante del coste de un bucle y ahora lo controla el cliente.

**Y tres supuestos de la ficha resultaron falsos del árbol**, comprobados antes de escribir una línea:

1. **La sexta tool no tiene servicio detrás, y la ficha se contradecía a sí misma.** `consultar_disponibilidad` es la única de las seis sin implementación: la única arista Python → .NET que existe es [`AiIndexFeedController`](../../backend/src/JoiabagurPV.API/Controllers/AiIndexFeedController.cs), autenticada por `X-Index-Feed-Key`, **sin `[Authorize]` a propósito** y sin transportar `pos_id`, y su ruta `pos-availability` es un **feed paginado de 200 filas con keyset**, no una consulta puntual por producto. Aplicando literalmente la regla que la propia ficha invoca dos veces —*«una tool que devuelve error es peor que una tool ausente»*— habría que retirarla y quedarse en cinco; pero la misma ficha nombra `test_out_of_stock_query_triggers_substitutes_tool`, que **sin señal de disponibilidad no tiene disparador**. Las dos frases no pueden ser ciertas a la vez, y lo que las reconcilia es la decisión 2.
2. **El techo de 3 llamadas no se puede heredar como número.** La tabla del §2 decía que C32 *«hereda de C31 el techo observable por `usage.calls`»*, pero un bucle de cinco vueltas hace cinco decisiones: lo heredable es **el patrón** —techo declarado, observable desde el mismo objeto que el consumidor lee, con aserción en ejecución—, no la cifra, que pasa a **8 por petición HTTP** (1 enrutador + ≤5 vueltas + ≤2 argumentario). Y la ficha sólo escribía presupuesto de iteraciones y de tools: **el de llamadas al proveedor no lo escribía nadie**, ni el de tokens, que es el que de verdad domina porque el contexto engorda en cada vuelta. Tampoco los **embeddings**: `_usage()` suma enrutador y argumentario, y cada búsqueda del bucle paga una llamada que ningún contador ve.
3. **El vocabulario de buckets son dígitos.** `QTY_BUCKETS = {"0", "1-2", "3+"}` en [`indexing/feed.py`](../../ai-service/src/jbg_ai/indexing/feed.py), así que pasarle el bucket crudo al modelo es pasarle **literalmente una cifra de stock**, que es justo lo que el §6.2 y el §15.10 prohíben. La tool traduce a etiqueta cualitativa sin dígitos —`sin_existencias` / `ultimas_unidades` / `disponible`—, que además es el patrón de vocabulario cerrado que el proyecto ya usa para los `warnings`. La puerta numérica de C30b sigue siendo la red, pero deja de tener que salvarnos.

**Y un hallazgo que no es de C32 y conviene no perder:** el contrato congelado **nunca reservó ruta para el agente de venta**. Reservó `/v1/inventory/propose` para el de inventario —hoy anulado y en 501— y ninguna para éste, mientras el §6.1 del diseño sí lo dibuja dentro del servicio (`R2["/v1/assist · generación con citas + agente de venta"]`). La ruta nueva de la decisión 1 cierra esa discrepancia **en el momento más barato que queda**: `/v1/assist/sale` sigue sin consumidor .NET hasta que C34 se escriba, que es el mismo argumento con el que C30a y C31 movieron el contrato sin coste.

**Un hilo abierto que la historia de usuario tiene que cerrar:** si el enrutador de C31 clasifica **todos** los turnos del operario o sólo el primero. Clasificar sólo el primero deja pasar la deriva fuera de dominio en el turno 5; clasificar todos y cortocircuitar siempre le cuelga al cliente a mitad de conversación. La propuesta sobre la mesa es clasificar todos y que **sólo el primero cortocircuite**, con los turnos posteriores produciendo los mismos dos códigos y una negativa cortés que no gasta tools — reutiliza `routing.short_circuits` tal cual y **no toca la matriz de confusión publicada**, que se midió sobre consultas sueltas.

### 2026-09-13 — C30a implementado: `POST /v1/assist/sale` deja de ser un fixture, y cae el último 501 cerrable

**`POST /v1/assist/sale` sirve la capa estructurada real con `STUB_MODE=false`.** Con ello
**`/v1/inventory/propose` queda como la única ruta que responde 501**, y no por trabajo
pendiente: su rama se canceló el 31 de agosto. La suite pasa de **1038 a 1195 tests con 0 en
rojo antes y después**, `openapi.json` se regenera moviendo **sólo los cinco esquemas de
assist** —cero rutas, cero esquemas añadidos o retirados, las otras nueve rutas idénticas— y
**no hay ninguna migración**. **Archivado el 2026-09-13**, sincronizando **20 requisitos nuevos
y 2 modificados** y haciendo nacer la capability viva **`assist-generation`** con 13 requisitos.

**Los tres spikes se corrieron antes de escribir código, contra el índice vivo y al umbral de
producción, y sus cifras decidieron.**

| spike | cifra | qué decidió |
|---|---|---|
| **1** · las 72 consultas del golden set, con y sin filtro | **101 citas / 41 abstenciones** sin filtro; con filtro, **−36,4 citas de ficha ajena** y abstenciones de **41 → 44,3** | El modo de consulta libre **no necesita umbral propio**: de 101 citas, **una** es inequívocamente espuria. Y el filtro **no produce falsa abstención en masa**, que era el riesgo de D8 |
| **2** · reutilización del vector de consulta | `model_version_key` idéntica carácter por carácter; segundo `embed()` del mismo texto → **1 sola llamada al proveedor** | **Viable, y la costura ya existía**: es la caché acotada del cliente. Con una condición **medida**: la clave es un hash del texto, así que M3 tiene que pasar el **mismo texto recortado** a los dos o paga un *embedding* por un espacio |
| **3** · cardinalidad de familia | **156 familias, 491 miembros, máximo 8**, media 3,15, p95 4 | Tope del roster en **24**, tres veces el máximo observado |

**Un efecto del filtro que el diseño no anticipó:** no sólo borra, **promueve**. Las 36,4 citas
ajenas retiradas cuestan una caída neta de 24,6, porque la cláusula filtra **antes del
`LIMIT`** y unos 11,8 fragmentos correctos por ancla ascienden a los huecos liberados.

**Y seis refutaciones más, todas en
[c30a-implementation-measurements.md](informes/c30a-implementation-measurements.md).** Las dos
que pesan:

1. **`retrieval/orchestrator.py` sí se modifica**, contra lo que el ticket afirmaba. La decisión
   de abstención **no es recuperable desde `RetrievalResponse`** —un `results` vacío es también
   lo que produce una consulta que no encontró nada, y `low_confidence` tiene un significado
   medido y **anticorrelacionado**, que es justo lo que D9 prohíbe reutilizar—. Se añade una
   **costura aditiva de observabilidad**, `on_abstention`, con la misma forma y el mismo motivo
   que el `on_fused_candidates` que ya existía. Cero cambios de comportamiento.
2. **Ni la HU ni el diseño decían a qué pieza describen los avisos cuando no hay pieza
   anclada**, y el escenario 3 de la historia exige que el aviso de variantes dispare en ese
   modo. Se cierra declarándolo: los avisos describen la **pieza foco** — la anclada en M2/M3,
   y el candidato mejor clasificado en M1. Leerla cuesta una lectura por clave primaria, que es
   la misma que hacen los modos anclados.

Y una corrección de dato: el diseño cita **486 miembros** y *«familias de 7 y 8»*. Son **491**,
y **no existe ninguna familia de 7** — los tamaños presentes son 2, 3, 4, 5 y 8. El tope se fija
sobre el máximo, así que la decisión no se mueve.

### 2026-09-13 — C30 se parte en C30a y C30b, y cinco supuestos de su ficha se caen contra el árbol

**C30 se desdobla por la regla 5 del §1** —*«si un change se desborda de la sesión, se parte y se entrega primero la mitad que desbloquea el grafo»*—, y el corte no es por tamaño solamente: es por **dependencia real de sus consumidores**. C34 y C36 necesitan **la forma** de la respuesta, no la prosa. Así que la mitad que desbloquea es la estructurada, y llega sin una sola llamada a un proveedor.

| Mitad | Qué entrega | Llamadas a LLM |
|---|---|---|
| **C30a** `add-assist-structure-and-rule-warnings` | contrato, tres modos, agrupación, roster, avisos por reglas, filtro de slug, abstención y **citas verificables ya** | **cero** |
| **C30b** `add-assist-pitch-generation` | el argumentario en prosa, la integridad referencial de citas y la puerta numérica | sí |

**El corte deja una ablación que no se buscaba.** C30a demuestra por sí solo recuperación, atribución resoluble y abstención —`search_knowledge` ya existe y el direccionamiento de fichas de material es determinista—, y C30b añade la prosa como **capa separable cuyo valor se mide contra C30a**. Es la estructura que el §11.2 del diseño y el checklist de C39 piden, y sale gratis del propio corte.

**Convención de lectura:** donde este documento dice **C30** sin sufijo, se refiere **al par**. Los prerrequisitos, el grafo del §4 y las tablas de los §5 y §6 sí llevan el sufijo, porque ahí la distinción decide qué se abre.

**Y cinco supuestos de la ficha resultaron falsos del árbol**, comprobados antes de escribir una línea. Es el **décimo change consecutivo cuya exploración refuta lo escrito antes**:

1. **El contrato congelado no puede agrupar por familia.** `AssistGroup.family_id` es **obligatorio y no nullable**, y **~58 % del catálogo no tiene familia** (C18b: 156 familias y 486 miembros sobre ~1.168 filas indexadas). Se renegocia `openapi.json` en C30a, **en un solo bloque y al momento más barato posible**: `IAiGatewayClient` no tiene método de assist y C34 y C36 no existen, así que hoy la ruta tiene **cero consumidores** y el coste sólo puede subir. Precedente propio: C18a y C18b regeneraron el snapshot en el mismo change en que movieron la frontera.
2. **El único consumidor previsto está anclado a pieza, y la request sólo acepta texto.** C34 expone `GET /api/ai/products/{id}/sales-assist` y `.../substitutes`, las dos por producto; `AssistRequest` no tiene `product_id` y su `query` es obligatoria. Nacen **tres modos** con validación de «al menos uno»: **M1** pregunta libre, **M2** argumentario de la pieza, **M3** pregunta sobre la pieza. El flujo por consulta **ya estaba servido** por `POST /api/ai/search` (C15) y el panel (C16).
3. **Dos de los cuatro avisos no son de Python.** «Stock crítico» y «miembros sin stock» necesitan el stock real, y `SearchHit.qty_bucket` está declarado como algo que *«never emitted: a bucket on the wire would be the beginning of one»*, además de poder desfasarse. Pasan a **C34, calculados tras hidratar**. Es **el segundo caso de la misma forma**: la ficha de C34 ya lleva anotada la exclusión por stock que C26 retiró de la suya el 12 de septiembre por el mismo motivo.
4. **Las citas se morían en la frontera.** `Citation` del contrato tiene 3 campos contra los 10 de `KnowledgeCitation`, y se perdían `citation_id` —el que *«resolves, locates and opens the file and the heading in git»*— y **`claim_scope`**, que C23 declaró no opcional precisamente para que un compromiso de la casa no se lea como un hecho del mundo: son **25 de 161** fragmentos, el 15,5 %.
5. **La abstención está al 10 %, y el camino de assist no la mira.** `jpv_abstention_enabled` está **activa por defecto** (`α = 0,03`, `N = 15`), y en esa banda abstiene en **2 de 20** consultas fuera de dominio y en **0 de 43** contestables — o sea que **18 de 20 llegan con candidatos**, sobre un golden set cuya categoría mayor son precisamente esas **20 de 72**. Sin puerta, C30 contestaría *«¿qué tiempo hace mañana?»* con cinco familias y un argumentario convencido **durante toda una vuelta de manivela**, porque el arreglo es C31 y C31 lleva C30 de prerrequisito. C30a **no clasifica intención** —eso sigue siendo de C31— y **no enciende nada**: lo que hace es **honrar y declarar** una decisión que ya se toma, en `abstained`, y no generar cuando ha saltado. **No se llama `low_confidence` a propósito**: ese nombre ya significa consenso entre ramas y está *anticorrelacionado* con lo que aquí hace falta (dispara en 1 de 20 fuera de dominio y en 10 de 43 contestables). *(Corregido el mismo 13 sep: la primera redacción decía «desactivada por defecto», tomado de un estado intermedio del apply de C25. El 18 de 20 —que es lo que sostiene la decisión— no cambia.)*

**Un hueco que la exploración descubre y que no es de C30.** El corpus de C23 —32 documentos, 161 fragmentos, indexado y calibrado— **no tiene hoy ninguna ruta hasta la pantalla del joyero**: C34 expone dos rutas por pieza y C36 pinta un card. Diez de los 32 documentos son mostrador puro (la piscina, la piel sensible, el regalo sin talla, los niños, el perfume). Se cierra por el camino más barato que existe —**`?question=` en la ruta que C34 ya va a escribir y una caja de pregunta en el card que C36 ya va a construir**—, y **M1 se implementa en Python sin superficie de operario en esta ronda**: su consumidor es el bucle de C32 y el arnés de C38.

Las once decisiones, con sus alternativas descartadas, las mediciones estáticas del corpus y los tres spikes previos, en [`c30-exploration-decisions.md`](informes/c30-exploration-decisions.md).

### 2026-09-12 — El corte nº 1 se dispara, y no por juicio: C27 sale del alcance con cinco mediciones

**El §6 llevaba a C27 pre-autorizado desde el 31 de agosto con un disparador redactado en términos de juicio —*«si el núcleo peligra»*—, y eso deja el corte a merced del calendario. Se sustituye por un disparador de medición.** Con prórroga abierta, el plazo ya no es argumento para nada; la pregunta correcta no es si cabe, sino si aporta. Medido contra el Postgres local sobre los 1.168 documentos vivos, antes de escribir una línea del change: **las dos señales de C27 están vacías, y el proyecto nunca previó medirlo**. El corte pasa de concesión a **decisión técnica justificada**, que es la diferencia que el rubro del PF premia por escrito.

**Primero, y es lo que decide: el generador no tiene modelo de afinidad — tiene lo contrario.** La co-ocurrencia se deriva del `BulkOperationId`, y **todas las ventas del sistema las escribe el simulador de C10**. Su `_pack_operations` baraja las líneas del día —muestreadas de forma independiente, ponderadas sólo por colección y POS— y luego elige activamente el siguiente artículo **cuyo lexema de nombre o cuya colección difieran**. La matriz de co-ocurrencia es, por construcción, el producto exterior de la popularidad marginal por POS con un empujón **anti**-correlativo contra los pares afines. Leerla como *«co-venta histórica»* es circular en la peor dirección: el generador fue escrito para **evitar** emparejar lo parecido. No es una señal débil, es una señal sesgada en contra de lo que se le pide. C10 no tiene la culpa —nunca prometió afinidad, y diversificar la cesta es correcto para el stock coherente que sí debía producir—; el error es que C27 dé por supuesta una propiedad que nadie generó.

**Segundo: aunque la tuviera, es un booleano y no un ordenador.** De 22.968 ventas, 5.641 llevan `BulkOperationId` en 2.381 operaciones, y salen **4.078 pares distintos** de ~719.400 posibles (0,57 %). De ellos, **4.019 — el 98,6 % — se han visto una sola vez**, 59 dos veces y **ninguno tres o más en dieciséis meses**. Por producto y restringido a tipo distinto, que es la regla de la ficha: **463 de 1.168 productos (39,6 %) no tienen ni un socio**, y los 705 que lo tienen reciben una mediana de **nueve socios empatados a 1**. Sólo el **7,2 %** tiene algún socio repetido. Es el caso que C25 ya resolvió con la rotación —*«como desempate estricto decidía **cero** pares del top-5»*— y aquí es peor, porque la rotación al menos salía de agregados reales. La tabla, además, tiene hoy **0 filas**: persistirla es trabajo del propio C27.

**Tercero: la otra mitad de la regla está igual de vacía, y sobre todo donde importa.** El solape exigido de `color_tags`/`style_tags` se apoya en dos campos cuya cobertura es **226 (19,4 %) y 131 (11,2 %)** del catálogo — y **872 documentos, el 74,7 %, no tienen ninguno de los dos**. Desglosado por origen, en la porción **real**, que es la que el criterio de aceptación del §11.2 designa como resultado principal: **37 de 404 con color y exactamente 1 de 404 con estilo**. Retiradas las dos señales, lo que queda de C27 es `WHERE piece_type <> :tipo AND price_band IN (…) AND stock > 0`: una cláusula sin una sola llamada a un LLM, que es el criterio exacto con el que el 31 de agosto se anularon cinco changes.

**Cuarto, y es información sobre el change y no sobre los datos: nunca hubo intención de medirlo.** La tabla del golden set del §11.1 del diseño reserva **6 consultas a sustitutos y ninguna a complementarios**; el golden set real tiene **8 consultas sin juzgar, 4 a nombre de C26 y 4 a nombre de C31, y cero a nombre de C27**; `criterion.md` define el grado 1 citando literalmente al sustituto; y `/v1/retrieval/substitutes` está en el `openapi.json` congelado mientras `/v1/retrieval/complementary` no. **C27 es, por construcción del propio proyecto, una funcionalidad no medible** — cuesta la última migración viva y no añade ni una fila a la tabla de ablations.

**Quinto, la condición que hace el corte firme y no aplazado: no hay cestas reales, ni las habrá.** El export del 17 de agosto fue **catálogo y nada más** —436 productos, 28 colecciones—; **cero ventas reales**. La fila `D8 · Histórico de ventas · Co-ocurrencia por operación de venta` del §8.3 describe un dataset **generado**, no recibido. Es una condición de datos, no de esfuerzo.

**Lo que el corte retira es la implementación, no el diseño** —precedente del §10, el inventario anulado cuyo diseño íntegro se entrega como próximo paso—. Se conservan la ficha con su sello, la tabla `ai.co_occurrence` vacía (no cuesta nada y es el enganche del día que lleguen tickets) y `cooccurrence.py` con su test, que derivan correctamente lo que se les pide: el defecto está en el generador de cestas, no en ellos. Se retiran la tool `buscar_complementarios` de C32 —misma regla que retiró `perfil_punto_venta`: una tool que falla siempre es peor que una ausente—, la ruta `.../recommendations` y su test en C34, y el bloque «También puede encajar» de C36. **Y `/v1/retrieval/complementary` no se añade al contrato: un 501 menos, no uno más.** La **condición de reactivación se deja comprobable y no opinable**: un export con histórico real a nivel de ticket cuyo percentil 95 de `co_sales_count` sea ≥ 3. Con la matriz actual ese percentil es **1**.

**Una cautela sobre el vídeo, declarada y no barrida.** La card de venta pierde uno de sus cuatro bloques y se ve más pobre en la demo. Se acepta: el rubro premia *«se identifican limitaciones actuales y se propone cómo resolverlas»*, y una limitación medida con cinco cifras y con su condición de reactivación escrita vale más que una señal de ruido enviada. **C27 habría sido el primer change de este proyecto en entregar una señal que su propia medición declara vacía.**

**C26 no se toca y sube a siguiente a abrir.** Es el caso simétrico y por eso conviene contrastarlo aquí: tiene contrato congelado con un 501 que cerrar, **4 consultas del golden set reservadas a su nombre con la nota escrita** (*«La hereda C26»*), todos sus datos puestos —1.168 de 1.168 con embedding e índice HNSW, 156 familias, 90 % con materiales, 100 % con banda de precio, `ai.pos_projection` con 6.720 filas—, y **cero llamadas al proveedor en tiempo de consulta**, porque sustituto es producto→producto y el embedding de origen ya está almacenado.

Informe con el SQL reproducible y los contraargumentos en [`c27-cut-measurements.md`](informes/c27-cut-measurements.md).

### 2026-09-12 — C25bis implementado: el andamio retirado, y tres puntos de su propia ficha refutados

**El borrado no movió nada, y está demostrado y no argumentado.** Dos corridas completas del arnés, una antes y otra después, sobre el mismo golden set (`1:198c4af44506`) y la misma huella de índice (`051a6b06021efc3f…`): **las 315 filas por consulta de las cinco configuraciones supervivientes son idénticas**, listas de resultados incluidas. El listón se había subido antes de medir de *«cifras idénticas»* a *«líneas idénticas»*, porque seis agregados iguales pueden esconder reordenaciones que se compensan. El **único** elemento de la procedencia que difiere es la revisión del código, que es precisamente la hipótesis bajo prueba, y la excepción se declaró por escrito y acotada. Suite: **994 → 997, con cero fallos a los dos lados** (−4 tests retirados, +7 añadidos).

**La ficha de este change describía un inventario supuesto, y la regla D3 de su propio diseño exigía uno comprobado. Al comprobarlo, tres de sus afirmaciones resultaron falsas:**

- *«los pesos por lista que sólo ella consumía»* — **falso**: `weight_typed` y `weight_expanded` alimentaban también la etapa 1 **viva**. Se retiran igualmente, pero por ser **trampas** —la spec exige que sean iguales y prohíbe barrerlas, así que una perilla así sólo podía moverse hacia la violación sin que nada lo detectase— y no por estar muertas. Sólo `weight_vector` carecía realmente de lector.
- *«retirar la variante de ponderación adaptativa que perdió el barrido»* — **pata vacía**: la forma binaria se implementó y se retiró **dentro de C25**, y hay un test que falla si vuelve. Se declara cumplida y se comprueba.
- *«que el arranque falle al nombrar una perilla retirada»* — **inalcanzable por el mecanismo supuesto y peor que el mal**: con `extra="ignore"`, pasar a `forbid` no caza variables de entorno, y un validador que barra el entorno convertiría un residuo inofensivo en un fallo de arranque. La obligación se acota a la configuración de evaluación, donde el daño es de **medición** —una fila que mide otra cosa— y no de creencia; y ahí la guarda **ya existía**, así que el escenario se cumplió con **cero código nuevo**. El precedente decide: `JPV_BUSINESS_WEIGHT_ROTATION` se retiró el 11 de septiembre con campo, default, fallback y validador propio, y no llevó guarda alguna.

**El principio que el change deja escrito, y que resuelve la mitad de sus dudas:** *una perilla es algo que se puede poner; un registro es algo que se escribe.* De ahí salen que `Provenance.fusion_mode` **sobreviva al selector** —una corrida archivada bajo la composición retirada debe seguir declarándose no comparable—, que `POOLED` pierda `v2-hibrido` mientras `judgements.jsonl` lo conserva en `pooled_in`, y que no haga falta rechazar la entrada equivocada si el registro dice siempre lo que ocurrió de verdad.

**Lo que se conserva de la fila de referencia.** Deja de ser ejecutable y pasa a ser **citable** con tres artefactos versionados: su informe, su JSONL por consulta y **su propia configuración**, movida a `evals/configs/retired/` —porque el informe publicado lleva etiqueta, procedencia y cifras pero **no los valores de las perillas**, y el YAML es el único sitio donde vive la configuración misma—. Su inercia es estructural y no convencional: el cargador hace `glob("*.yaml")` sin recursión. Y **por qué se retiró sigue siendo demostrable sin ser activable**: un test de aritmética pura sobre `fuse()`, con los pesos de C21 como literales locales, prueba que el peor documento léxico (`1,00/120 = 0,008333`) gana al mejor vectorial (`0,33/61 = 0,005410`) y que el #1 vectorial cae al puesto 33.

**Dos hallazgos que el plan no preveía.** La guarda de claves desconocidas disparó contra **tres configuraciones congeladas** —`v1-vectorial` seguía nombrando los pesos por lista, `v2b` y `v3` fijaban `fusion: branch`—, y las tres claves eran **inertes**: `v1-vectorial` corre con la rama léxica apagada y `branch` era el default vivo. Y la comprobación de despliegue no encontró ninguna perilla retirada en `.env`, `terraform/` ni compose, pero sí en **`openspec/config.yaml`**, el contexto que todo agente carga primero, que además describía la fusión plana como seleccionable. Corregido.

**Una cautela propia, refutada:** la exploración advirtió que la tabla publicada de C25 no servía como referencia por haberse tomado `+dirty`. Medido, la corrida previa la **reproduce fila por fila**. La comparación se hizo igualmente contra la corrida previa, porque lo que la hace válida es salir del mismo árbol y no que coincida.

Informes en [`c25bis-exploration-decisions.md`](informes/c25bis-exploration-decisions.md) y [`c25bis-implementation-measurements.md`](informes/c25bis-implementation-measurements.md).

### 2026-09-12 — C25 archivado, y el andamio que deja abierto entra en el plan como `C25bis`

**C25 pasa a hecho** y con él la cadena crítica arranca en **C26**. Recuento: **27 archivadas, 11 pendientes**. Al archivarse **nacen dos capacidades vivas** — `business-signals-ranking`, la disponibilidad como reordenación blanda calibrada contra el golden set, y `retrieval-abstention`, la regla que decide **si** contestar — y se modifican `hybrid-fusion`, `pos-projection` y `retrieval-evaluation`. Esta última **pierde** un requisito: cae el de C24 que congelaba el umbral de distancia, sustituido por el que permite re-fijar la regla bajo un criterio escrito antes de medir.

**`C25bis` (`clean-plain-fusion`) entra en el §2, el §3 y el §4.** Se creó el 11 de septiembre, junto con los artefactos de C25, y hasta hoy no figuraba en este documento: estaba en `openspec/changes/` y en `epicas.md`, pero no en el plan, que es donde se decide el orden. Va **fuera de la numeración C** por el mismo motivo que `FIX1` — no sale de la descomposición original sino de una consecuencia de otro change — y su prerrequisito duro, *«C25 archivado»*, **queda cumplido hoy**. No entra en la ruta crítica: es una hoja y cede el turno a C26.

**Y la ficha de C25 se pone al día con lo que de verdad entregó.** Seguía titulada `add-business-signals-ranking` —el nombre anterior al renombrado del 1 de septiembre— y describía un alcance que la medición desmintió en tres puntos: la penalización de variante ambigua, la calibración de `1-2` frente a `3+` y la rotación como criterio de orden. También decía *«re-fijación del umbral con la distribución empírica»*, y lo que ocurrió fue lo contrario: el escalar resultó incapaz de separar las dos poblaciones —el rango de las imposibles cae **dentro** del de las contestables— así que el umbral se queda donde estaba, ahora por decisión y no por aplazamiento, y la regla adoptada es relativa por consulta.

---

### 2026-09-11 — C25, al aplicar: la fusión no fusionaba, y dos puntos de la ficha se caen por medición

**Medido contra el Postgres local, sobre los 1.168 documentos vivos y el golden set de C24.** El
change se renombra de `add-business-signals-ranking` a **`recalibrate-ranking-and-abstention`**,
porque el nombre viejo cubría un tercio de lo que había que hacer. El número **se conserva**:
renumerar rompería las referencias de C26 (`prereq C22, C25`) y C27 (`C10, C25`) a cambio de nada.

**El hallazgo que reordenó el change.** La fusión de C21 no fusionaba: **concatenaba**. Con
`wC = 0,33` los sesenta documentos léxicos ganaban al mejor acierto vectorial en **toda** consulta,
de modo que un documento de grado 2 que la rama vectorial ponía **primero** caía a la **posición
33** — reproducido en tres consultas distintas y también en el modelo. Es un defecto **aritmético**
y no un peso mal calibrado, así que la ficha pasa de «calibrar pesos» a **rehacer la composición**:
dos etapas, pesos por rama, y la rama léxica deja de meter 120 candidatos contra 60.

**Tres puntos de la ficha se retiran, los tres refutados por medición y no por argumento:**

1. **Penalizar la variante ambigua dentro de familia.** 29,2 % de las consultas tienen 3+ hermanas
   en el top-10 pero **ninguna pasa de cuatro**, así que la familia nunca ocupa más de 4 de los 10
   huecos que el operador ve. Es un problema de **presentación** y pertenece a C30/C36; penalizar
   costaría relevancia y escondería al operador que las tallas existen.
2. **Calibrar `1-2` frente a `3+`.** Con la función de ganancia operativa los dos caen en la misma
   rama y ninguno pierde grado, así que **no existe función objetivo** que pueda ordenarlos. Y
   `1-2` son 191 pares contra 5.431: aunque existiera, calibraría sobre ruido.
3. **Ordenar por rotación.** Retirada **durante el apply**. Como el desempate estricto que su
   propio requisito describía decidía **cero** pares del top-5 en las 48 consultas; como clave de
   ordenación no desempataba sino que **particionaba** —11.067 pares invertidos, el 71,2 % a más de
   diez puestos— y costaba relevancia donde actuaba. `sales_30d` se sigue leyendo para diagnóstico
   y no ordena nada.

**Lo que el change entrega, con su cifra.** La fusión por rama gana **+0,083** sobre la línea base
en la lectura que decide. La ponderación adaptativa por cobertura aporta **+0,128** en
`descripcion-sin-anclaje` y **cero exacto** en las otras siete categorías, y convierte la elección
del cociente de rama de **acantilado en meseta** (recorrido del barrido 0,070 → 0,007). La señal de
disponibilidad retira el **91 %** de las piezas agotadas del top-5. La abstención pasa de 0,050 a
**0,150** sin silenciar ni una consulta contestable.

**Y tres listones no se alcanzan, declarados y no cerrados:** el `Recall@5 ≥ 0,85` del §11.2 se
queda en **0,758**; la abstención de 0,80 de la ficha, en **0,150**; y `v3` no bate a `v2b` por el
margen de 0,05 —**+0,030** operativo— aunque cumple su propia regla de adopción. Los tres son
listones fijados **antes de que existiera el instrumento** que los mediría. Ninguno se ha cerrado
moviendo el listón después de medir, y ninguna etiqueta se ha reescrito.

**Zona.** Decimotercera vez que la ficha se queda corta: además de `retrieval/` toca `evals/`,
`config/settings.py` y `evals/golden/`. Sin diff en `backend/`, `frontend/`, `terraform/`,
`.github/` ni `openapi.json`, y sin migración de Alembic.

### 2026-09-01 — C20, al explorar: el diccionario no es sólo de sinónimos, y una consulta ensanchada tira el término exacto

**Medido contra el Postgres local, sobre los 1.168 documentos vivos de `ai.product_document` y con 12 embeddings reales del proveedor.** La ficha describía un fichero YAML de sinónimos comerciales. Es eso y dos cosas más que nadie había nombrado.

**Primero: `doc_text` ya está canonicalizado, así que la expansión tiene diana garantizada.** `build_source_text` escribe las líneas `Tipo:` y `Materiales:` con el vocabulario cerrado de C09 — presentes en **1.157 y 1.042 de 1.168** documentos. La consecuencia es exacta, no aproximada: buscar léxicamente el término canónico **equivale a filtrar por `piece_type`** (`anillo` 268 = 268, `pendientes` 275 = 275, `pulsera` 207 = 207, `collar` 140 = 140). Eso fija la dirección útil de la expansión —palabra del operador → término canónico— que es justo la que `enrichment/vocabularies.yaml` ya codifica.

**Segundo: sin diccionario la rama léxica de C21 contesta cero a frases ordinarias.**

| consulta del operador | sin expansión | con expansión |
|---|---|---|
| `gargantilla dorada` | **0** | 64 |
| `collares de plata` | **0** | 66 |
| `criollas de oro` | 1 | 102 |
| `sortija de plata` | 3 | 144 |
| `aros de plata` | 22 | 205 |

**Tercero, y esto no estaba en ninguna parte: el stemmer español rompe dos sustantivos del dominio.** No es un problema de sinónimos sino de tokenizador, y se corrige con el mismo mecanismo:

| par | lexemas | documentos que casan |
|---|---|---|
| `collar` / `collares` | `'coll'` ≠ `'collar'` | **140 frente a 1** |
| `aro` / `aros` | `'aro'` ≠ `'aros'` | 32 y 24, conjuntos distintos |
| `baño` / `bano` | `'bañ'` ≠ `'ban'` | `baño de oro` 38, **`bano de oro` 0** |
| `pequeño` / `pequeno` | `'pequeñ'` ≠ `'pequen'` | 134 y 71, ambas legítimas |

El matiz que lo hace tratable: **el stemmer sí pliega las tildes agudas** (`ámbar`=`ambar`, `ónix`=`onix`, `clásico`=`clasico`) **pero no la `ñ`**. Un operador en un TPV que teclea sin `ñ` obtiene cero. Se arregla en el overlay por tres entradas, **no** instalando `unaccent` ni creando una configuración `ts` propia: `tsv` es columna **generada**, y cambiar la configuración exigiría migración que la reescribe y reconstruye el GIN. C20 sigue sin ser 🗄️.

**Cuarto, el hallazgo que decide el contrato: una sola `tsquery` ensanchada destruye la coincidencia exacta.** Con `(sortij|anill) & plat`, ordenado por `ts_rank`, los **tres** productos que literalmente se llaman «Sortija» caen **fuera del top-10**: `ts_rank` deja de premiar el término que el operador escribió. Es el problema de Stripe del artículo de búsqueda híbrida de S10, reproducido dentro del propio mecanismo de expansión. Fusionando por RRF (k=60) las dos listas —la original y la expandida— las tres sortijas vuelven a las posiciones **1, 2 y 3** y el recall sigue siendo de 144 candidatos. Por eso **la expansión entrega grupos de equivalencia, nunca una cadena reescrita**: la fusión es de C21, y C20 no puede quitarle la información con la que fusionar.

**Quinto: la rama vectorial no cubre el hueco, y falla sin abstenerse.** Doce embeddings reales (`text-embedding-3-small`), misma búsqueda coseno de C14 con umbral 0,65, contando aciertos en el top-10 contra la diana (`piece_type` correcto y material correcto):

| consulta | variante | forma canónica | solape del top-10 |
|---|---|---|---|
| `sortija de plata` → `anillo de plata` | **4/10** | 10/10 | 2/10 |
| `gargantilla dorada` → `collar dorado` | **6/10** | 10/10 | **0/10** |
| `criollas de oro` → `pendientes de oro` | **1/10** | 8/10 | 1/10 |
| `aros de plata` → `pendientes de plata` | 9/10 | 10/10 | 0/10 |
| `collares de plata` → `collar de plata` | 10/10 | 10/10 | 8/10 |

Dos lecturas. La primera: **el vector no es sustituto del diccionario** — con «criollas de oro» acierta 1 de 10, y devuelve «Pulsera Río de Plata» como primer resultado de «sortija de plata». La segunda es peor: **siempre devuelve diez candidatos por debajo del umbral**, así que no abstiene, no marca `low_confidence` y el fallo llega a la pantalla con apariencia de acierto. Es la misma firma que C17 encontró siete veces. El plural, en cambio, el vector lo cruza sin ayuda (`collares` 10/10, solape 8/10), lo que confirma que el problema del stemmer es estrictamente léxico.

**Consecuencia de reparto:** la expansión **no toca la rama vectorial en C20**. Duplicar la consulta duplicaría los embeddings, y el cliente se sigue construyendo **por petición** —la deuda asignada a C21/C22— sobre un presupuesto que ya está en los 2500 ms temporales de C16 con 1707 ms medidos en una de cada cuatro llamadas. Pero los números de arriba **son una hipótesis para la ablación de C24**, y quedan anotados como tal: una configuración que embeba también la forma canónica y fusione por RRF es defendible en cuanto el cliente sea singleton.

**Sexto: el 60-70 % del diccionario ya existe, y crear un segundo fichero suelto es el error de C19.** `enrichment/vocabularies.yaml` ya tiene `sortija→anillo`, `gargantilla→collar`, `aro→pendientes`, `brazalete→pulsera`, `plata de ley→plata`, con la dirección correcta y las tildes correctas, y `ClosedVocab.resolve()` empareja sobre texto plegado con `fold()`, que quita la `ñ` — de modo que `resolve("bano de oro")` → `"baño de oro"` **ya funciona hoy**. Se adopta **base + overlay**: se lee `vocabularies.yaml` como clases de equivalencia base y **no se modifica** (tocarlo obliga a `enrichment/v2` y arrastra reenriquecimiento: eso es `fix-enrichment-vocabulary-gaps`), y se añade `retrieval/query_synonyms.yaml` **sólo de consulta** para lo que no debe entrar en el contrato de extracción. Inventariados 96 términos de operador contra el índice: **22 ya cubiertos por la base**, **46 sin acción** y **~18 de overlay** tras aplicar una singularización en ambos lados al cargar, que por sí sola resuelve `sortijas`, `alianzas`, `gargantillas`, `brazaletes`, `esclavas` y `dorados`.

**Tres exclusiones con motivo medido, que son el argumento de por qué el diccionario se cura y no se genera:**

- **`piel` → `cuero` se descarta.** Los 7 documentos que casan dicen «sobre la piel», «acaricia la piel»: piel humana en prosa comercial. `cuero` tiene **un** producto en todo el catálogo; el mapeo metería siete errores en cada consulta de cuero.
- **`llavero`, `diadema`, `gemelos`, `cinturon` no son sinónimos**, son huecos de `piece_type`. Van a `fix-enrichment-vocabulary-gaps`, como su ficha ya dice.
- **`filigrana` no necesita expansión**: casa 66 documentos por sí sola, repartidos por **todos** los tipos de pieza. Es un hueco de `style_tags`, y un término real del dominio menorquín —una de las 12 consultas registradas es literalmente *«anillo de filigrana tradicional menorquina»*—. Se anota para el mismo change, no para éste.

**Y una limitación a declarar en el README, hermana de la del doble etiquetado de C24: el diccionario se cura contra el corpus, no contra demanda observada.** `public."ProductSearchEvents"` tiene **31 filas y 12 textos distintos**, todos escritos por el propio desarrollador y todos en vocabulario canónico. Las consultas de operador del D10 del diseño no existen todavía.

| Lo que decía la ficha | Lo que la exploración obligó | Motivo |
|---|---|---|
| **Zona:** `ai-service/src/jbg_ai/retrieval/` | **`retrieval/` + lectura de `enrichment/` + una CLI de medición.** Sigue sin migración y sin tocar `openapi.json` | **Octava vez** que la zona de una ficha se queda corta, tras C08, C07, C15, C16, C17 y C18b |
| «Fichero YAML curado a mano (~40-60 entradas)» | **Base `vocabularies.yaml` (no se toca) + overlay de consulta de ~18 entradas** | 22 de los términos inventariados ya están en la base, con la dirección y las tildes correctas. Un segundo fichero suelto es la segunda definición que divergiría: el motivo por el que se anuló C19 |
| «Diccionario de sinónimos» | **Sinónimos comerciales *y* artefactos del stemmer** | `collar`/`collares` da 140 documentos frente a 1, y `bano de oro` da 0 frente a 38. Sin esto C21 nace con un fallo de usabilidad de TPV que nadie había nombrado |
| «Expansión en consulta» | **Grupos de equivalencia, no una cadena reescrita** | Una sola `tsquery` ensanchada saca del top-10 los tres productos que el operador nombró. Con RRF sobre las dos listas vuelven a 1-2-3 |
| «Se decide con la medición de C24» | **C24 está aguas abajo por C21: C20 trae su propia evidencia** | El grafo es `C20 → C21 → C24`. La ficha pedía medir con un harness que su propio change desbloquea. C20 mide sobre el índice real y deja informe versionado; C24 lo re-mide con relevancia graduada |
| Nada sobre dónde vive el flag | **Default en `Settings`, parámetro en la firma del orquestador** | C24 barrerá `v0`/`v1`/`v2-hibrido` en el mismo proceso. Un interruptor sólo de entorno obliga a reiniciar por configuración, y llevarlo a `RetrievalRequest` movería el `openapi.json` congelado |

**Un hallazgo de entorno que conviene no perder.** La clave de embeddings vive en `backend/.env`, que es la fuente única que ya usa Compose, y el cargador **ya existe**: `jbg_ai.data.envload.load_local_env()` la busca ahí primero. No hace falta symlink ni `env_file:` — el propio `backend/docker-compose.yml` lo rechaza por escrito para no inyectar claves de CLI en el runtime. Pero **`python -m jbg_ai.indexing` no llama al cargador** y depende de que la variable esté exportada a mano: mismo hueco, y conviene cerrarlo. Y en esta máquina el TLS está interceptado: `curl` pasa porque usa el almacén de Windows y Python falla con `CERTIFICATE_VERIFY_FAILED` porque usa `certifi`, que es la misma causa del `--system-certs` que `CLAUDE.md` ya documenta para `uv`. Cualquier medición contra el proveedor necesita `SSL_CERT_FILE` apuntando al almacén del sistema.

### 2026-08-31 — C18b, al explorar: su ficha describe un mundo que C18a ya no dejó en pie

**Los tres números que la ficha manda pintar están caducados, y el mecanismo que los produciría ya no los produce.** La ficha dice *«pintar la cola de revisión que C18a ya calcula: 15 miembros marcados, 4 grupos rechazados y 37 productos excluidos»*. Medido contra el Postgres local el mismo día que C18a se archivó:

| La ficha | Medido | Por qué |
|---|---|---|
| 15 miembros marcados | **0 recalculables** | Los 486 ya pertenecen a una familia y `build_candidate_groups` los excluye en su paso 1 por convergencia. Las marcas vivían **sólo en la respuesta de `suggest`**, y la decisión 3 de C18a fue no persistir propuestas |
| 4 grupos rechazados | **2** — `Alianzas Plata/oro` y `Cadena oro/plata` | `Encargos` y `Presión` salieron del índice con `ReviewStatus = Rejected` en el mismo lote: ya no son candidatos y su grupo no llega a formarse |
| 37 productos excluidos | **11** | 26 de los 37 estaban entre los 32 retirados |
| «una propuesta descartada reaparece» | **0 propuestas** | Se aplicaron las 156. `POST /v1/families/suggest` devuelve hoy lista vacía |

Construir C18b literalmente entregaría **una pantalla vacía** — cuarta aparición de la firma que este proyecto persigue desde C17, tras A1 en C04, B5 en C16 y el índice en C17. **La ficha se reencuadra:** el objeto de la pantalla son las **156 familias que nadie ha mirado** (las 156 llevan `Origin = AiApproved` con aprobador e instante de un lote que se disparó de una vez, y hay **cero** familias `Manual`) y los **682 productos activos sin familia**, de los que **671 tienen `piece_type`**.

**El hallazgo que hace pequeño el change: marcados y huérfanos son el mismo predicado.** Un miembro marcado es un producto **dentro** de una familia al que un extraño le gana a su peor hermano; un huérfano candidato es uno **fuera** al que le pasa lo mismo. Mismo cálculo, mismo objeto de revisión —el par `(producto, familia)`—, mismo veredicto humano: un endpoint, una consulta y una tabla, reutilizando `apply_relative_veto` con el universo de familias **persistidas** en vez de propuestas.

**Y la medición volvió a desmentir la hipótesis de partida, como en C18a.** Se entró suponiendo que el umbral relativo se dispararía en cientos sobre 671 huérfanos y que la **pureza de vecindad** sería más segura por estar acotada por construcción. Es al revés:

| `data_origin` | huérfanos | **A** · margen relativo > 0,02 | **B** · pureza ≥ 3 de 5 | A ∧ B |
|---|---|---|---|---|
| `real` | 216 | **21** | 19 | 6 |
| `synthetic` | 434 | **1** | **55** | 0 |

**A dispara 95 % sobre catálogo real; B, 74 % sobre sintético** — camina directo a la trampa que el `design.md` de C18a ya tenía escrita (*«fracasa en el sintético, donde `v2`/`v3`/`v4`/`v5` son casi-duplicados deliberados»*), nominando `Anillo Llama Eterna v3` → `Anillo llama eterna v2` y compañía. **A nomina y B ordena.** Curva del margen: `0 → 40` · `0,02 → 22` · `0,05 → 5` · `0,08 → 3`.

**La alerta no es sólo calidad de catálogo: diagnostica el agrupador.** Los primeros por margen tienen causa nombrable — `Pendientes botón erizo de mar S dorado` (0,109), `Colgante Lapa Mini Dorado` (0,096) y `Pendientes botón estrella de mar dorado` (0,056) quedaron fuera porque **`dorado` no figura en `materials`** de `vocabularies.yaml`, que sí tiene `baño de oro` con `chapado en oro` y `gold plated` como sinónimos. Y como el agrupador lee `name` y no `materials[]`, **el sinónimo recupera familias sin reenriquecer y sin salto de prompt**: va en C18b, no en `fix-enrichment-vocabulary-gaps`, cuya mitad de `piece_type.terms` sí exige `enrichment/v2`.

**Una familia contaminada es un imán.** `Colgante estrella de mar`, la que se comió un sintético, tiene peor hermano **0,778** frente a una media de 0,85–0,95, y atrae 4 de los 25 primeros por margen. Se corrige con orden y no con lógica: **auditar miembros antes que huérfanos** sube el listón y esos falsos positivos desaparecen solos.

| Lo que decía la ficha | Lo que la exploración obligó | Motivo |
|---|---|---|
| **Zona:** frontend + `Application/` | **Python + .NET + frontend, y con migración** | El endpoint de auditoría necesita los vectores, y **.NET no mapea el esquema `ai`** (cero referencias en `Infrastructure/`). El propio test que la ficha pide, `test_orphan_detection_...`, es de pytest. **Séptima vez** que la zona de una ficha se queda corta, tras C08, C07, C15, C16 y C17 |
| «lista de **descartes** persistente» de propuestas | **Veredictos sobre pares `(producto, familia)`** | Los tres objetos descartables no son equivalentes: una propuesta **no tiene clave estable** y hoy hay cero; un miembro marcado y un huérfano candidato **comparten clave**. Y esa misma fila **es el sello por ítem** que la decisión 7 de C18a aplazó aquí: una tabla responde a tres promesas |
| Sin migración *(C18 nunca fue 🗄️)* | **🗄️ — séptima migración del plan**, `FamilyReviewVerdict` | La contención **caducó**: anulados C19 y C29, el §12 ya sólo cuenta la de C27. Una tabla en `ai` reintroduciría *«un estado paralelo a .NET que nada invalida»*, porque `ai.product_document` es una proyección que se lapida y reconstruye |
| «el frontend es lo único nuevo» | Faltan además **`GET /api/product-families`** y **`DELETE /api/product-families/{id}`** | No hay listado: una pantalla que revisa 156 familias no puede enumerarlas. Y sin borrado, disolver una familia mala deja **una familia fantasma sin miembros** |
| Revisión sólo de lo marcado | **Se reaprueban las 156 ítem a ítem** | Es lo que produce la evidencia del renglón *«métricas de revisión humana»* del §16, que **hoy no tiene ninguna**: cero productos y cero familias han pasado por revisión real. Y revisar no mueve el corpus — sólo lo mueve **cambiar** |

**Y una consecuencia de reparto que conviene fijar aquí:** C18b y **C28** son la misma pantalla dos veces —ambas *frontend + `Application/`*, sólo administrador, revisión por lotes de salida de IA, y EP13 ya las agrupa—. C18b construye la **carcasa** y es su primer inquilino; C28 es el segundo. Lo que se extrae es **sólo lo que la ficha de C28 pide por escrito** (tabla editable, atajos de teclado, aprobación masiva, registro de quién revisó y qué cambió), nada conjeturado. Las dos alimentan la misma tabla del README: corrección del **agrupador** y corrección del **extractor**. *(Añadido el 1 sep, al cerrar C18b: la carcasa llega a C28 con **un hueco identificado y su caso de prueba** —crear una familia desde la pantalla, para las dos raíces degeneradas que la auditoría por vecindad no puede nominar—, más una mejora medida: **ponderar la nominación por la cohesión de la familia destino**, cuya precisión va de 0 % a 100 % según a quién apunte.)*

### 2026-08-31 — Prórroga abierta y equipo de uno: se deja de planificar por calendario

El proyecto pasa a tener **prórroga abierta**: no hay fecha de entrega, y el objetivo es entregar cuanto antes. Y lo desarrolla **una sola persona**, no dos.

Las dos cosas juntas invalidan tres mecanismos del documento, que se sustituyen en lugar de borrarse:

| Mecanismo de la v3 | Sustituto |
|---|---|
| Calendario por olas del §5 y «~4,4 changes por persona y semana» | **Orden por desbloqueo del grafo** (§4). Las olas se conservan como registro de lo ejecutado, no como plan |
| Reglas de asignación del §1 (anunciar antes de empezar, no coger el mismo change, repartir la mitad que desbloquea) | Sin objeto. Sobrevive la **regla de migración única activa**, que ahora es una regla de *rama*, no de persona |
| «Pares que NO deben ejecutarse en paralelo» (§5) | Sigue vigente **como conflicto de zona entre changes consecutivos**: dos changes que tocan el mismo fichero no se abren a la vez aunque los abra la misma persona |

Y una consecuencia que no es de proceso sino de contenido: **el doble etiquetado del golden set de C24 desaparece**. Su ficha lo daba por hecho «entre los dos, etiquetando por separado y conciliando», y el §6 lo declaraba irrenunciable — *«nunca renunciando al doble etiquetado»*. Con un solo etiquetador no existe, y el sustituto no es fingirlo: se etiqueta **una vez**, y el README declara la ausencia de acuerdo entre anotadores como limitación explícita del golden set en lugar de reclamar una mitigación que no se aplicó. La compensación asequible es de método, no de personas: *pooling* sobre la unión de configuraciones (que se mantiene) y **relectura diferida** de las consultas cuya relevancia se etiquetó con dudas.

### 2026-08-31 — Se anula C19 y toda su rama: C19, C29, C33, C35 y C37

**El motivo no es de plazo, es de contenido: C19 no aporta nada al sistema RAG, y el plan lo dice sin decirlo.**

El diseño afirma en su §10.1 que las señales de demanda son *«reutilizadas por el ranking de búsqueda»*. Es cierto del concepto y **falso del cableado**. La señal que pondera el retriever es `sales_30d` y `qty_bucket`, y llega por otro sitio:

```text
C25 ranking ──usa──▶ ai.pos_projection ──sincroniza──▶ /api/ai/index-feed/pos-availability
                        (C22: C10,C12,C14)              (C12 · archivado)
                                                        IndexFeedRepository.GetSalesAggregatesAsync
                                                        └── sales30d · sales90d · lastSaleAt
```

C22 depende de C10, C12 y C14. C25 depende de C21, C22 y C24. **Ninguno de los dos depende de C19.** La suma que necesita el RAG está implementada, archivada y es normativa desde `openspec/specs/index-feed/spec.md`. C19 habría construido una segunda copia de la misma agregación para otro consumidor — con el riesgo, además, de que las dos definiciones de `sales_30d` divergieran y el agente de inventario contradijera al ranking en la misma pantalla.

**Lo que C19 compraba de verdad era el segundo agente**, y el precio son cinco changes de los cuales tres no tienen ni una llamada a un LLM:

| Change | Zona | Contenido de IA |
|---|---|---|
| **C19** `add-demand-signal-service` | .NET 🗄️ | ninguno — agregación SQL |
| **C29** `add-inventory-recommendation-entity` | .NET 🗄️ | ninguno — motor de reglas |
| **C33** `add-pos-sales-profile` | .NET + Python | el LLM redacta el resumen |
| **C35** `add-inventory-agent-proposals` | Python | **el segundo agente** |
| **C37** `add-frontend-inventory-review-and-print` | Frontend | ninguno — pantalla y vista imprimible |

**Y el propio plan ya lo había decidido, en su otra versión.** La variante para tres desarrolladores —retirada del repositorio el 2026-09-12 por obsoleta— agrupaba exactamente esta rama bajo *«§6. Bloque opcional — Agente de reposición ⚠️ · Solo si el núcleo está cerrado. Es el primer bloque que se cae»*, y su orden de corte empieza literalmente por ella. En esta versión la misma señal estaba repartida y por eso no se veía: **cuatro de los ocho cortes pre-acordados del §6 viven dentro de la rama** — Rotate de C29 (nº 2), Transfer de C29 (nº 4), vista imprimible de C37 (nº 5) y C35 entero (nº 8). Si esos cuatro se hubieran disparado, lo que quedaba en pie era una migración, un motor de reglas .NET y una pantalla de aprobación: todo el esfuerzo fuera de lo que el Proyecto Final evalúa.

**Lo que se pierde, exactamente y sin adornos:**

1. **De dos agentes se pasa a uno.** El asistente de venta (C30→C31→C32), que el diseño marca «Núcleo · Requisito del PF», se conserva entero.
2. **El agente de venta pierde una tool de ocho:** `perfil_punto_venta` era C33. **La ficha de C32 queda corregida en el sitio**; sin eso el agente arrancaría registrando una tool sin servicio detrás.
3. **C38 pierde** los 8-10 escenarios de agente de inventario y el test de fidelidad del perfil por POS. Conserva validador anti-alucinación, escenarios de venta, adversarios y RAGAS.
4. Los ítems **9** (agente de inventario) y **11** (vista imprimible) del alcance acordado del diseño pasan a fase posterior, junto a la packing list que ya estaba ahí.

**Lo que sobrevive es todo el RAG:** corpus híbrido, enriquecimiento y revisión humana, familias, índice y `source_hash`, recuperación híbrida con sinónimos y prefiltro blando, sustitutos, corpus de conocimiento con citas, generación con avisos por reglas, guardrails, agente de venta, endpoints .NET, frontend, golden set, ablations, validador, RAGAS y despliegue.

**Dos hallazgos de la sesión de exploración que conviene no perder**, porque son la puerta de entrada si algún día se resucita algo de esta rama:

- **C33 no necesitaba C19.** Su dependencia estaba sobre-especificada. Sus métricas (`top_piece_types`, `top_materials`, `top_price_ranges`, `top_collections`, `average_ticket`, `best_selling`, `slow_moving`) son agregados a nivel POS sobre `Sales` × `ProductAiProfile`, y lo único per-producto que necesitan —`sales_30d` y `lastSaleAt`— **ya lo calcula `GetSalesAggregatesAsync`**. No usa `IsSupplySource`, ni `stock_in_other_pos`, ni `estimated_days_to_stockout`, ni `is_top_seller_in_pos`, ni `sales_7d`, ni `sales_60d`. Si el núcleo cierra y sobra sesión, **C33 con prereq C08+C12 es un change suelto y sin migración** que devuelve la octava tool al agente de venta y da a §11.3 su test de fidelidad.
- **`sales_7d` estaba muerta al nacer, y se midió.** El mundo de C10 termina el 2026-08-23; medido el 2026-08-31 contra el reloj de pared, `sales_7d` es distinto de cero en **3 de 6.050** pares (producto, POS) activos — 0,05 %. Anclada al fin del mundo serían 443. Cualquier resucitación de las señales de demanda necesita **primero** decidir el reloj (`asOf` inyectado y `computedAsOf` declarado en la respuesta, como `projection_age_seconds` en C22), y no al revés.

**Cortes confirmados de antemano**, elegidos en la misma sesión y ya reordenados en el §6: **C27** (complementarios) y **C23 reducido a 15 documentos**. No están anulados — están pre-autorizados, y se disparan en ese orden si hace falta. *(Epílogo: los dos se resolvieron por **medición** y en direcciones opuestas. El de C23 **se refutó** el 6 de septiembre —quince documentos daban la mitad del mínimo en fragmentos, y la abstención dejaba de poder demostrarse—; el de C27 **se disparó** el 12 de septiembre, con cinco mediciones que vaciaron sus dos señales. Ninguno de los dos lo decidió el calendario, que es lo que este bloque temía.)*

### 2026-08-31 — C18, al aplicar: el umbral del §7.5 no existe, y el plan se contradecía

**C18 se parte en C18a y C18b** por la regla 5: primero la mitad que desbloquea. C18a es el motor y el camino de escritura; C18b la pantalla y la alerta de huérfanos, que necesitan familias existentes para tener algo que revisar. Y **C18a entra en la lista de nunca-recortar**, porque el plan tenía una contradicción: declaraba irrecortables a C30 y C36 —cuyos tests de familia son `test_variants_grouped_by_family_id` y `should require variant confirmation when family has multiple members`— y recortable al único change que crea familias. Con cero familias esos dos tests pasan en vacío, que es la firma que este proyecto lleva persiguiendo desde C17.

El grafo del §4 tampoco dibujaba las aristas **C18→C25, C26, C30 y C36**. Ya están.

**Lo que la medición sobre los 1.200 vectores obligó a corregir del §7.5 del diseño.** Su enunciado —*«agrupa candidatos por similitud de embedding (umbral alto) + mismo `piece_type` + raíz común de nombre»*— **no funciona**: las poblaciones de «peor hermano» y «mejor extraño» se solapan (real 0,847–0,920 frente a 0,867–0,936), y dos familias sintéticas distintas por construcción llegan a quedar a **cinco milésimas**. Ningún corte absoluto las separa. Pero en relativo el vector es excelente —el vecino más próximo es hermano en 96,2 % de los miembros reales y 99,7 % de los sintéticos—, así que **la raíz del nombre agrupa y el embedding veta**, comparando contra las otras pertenencias propuestas y nunca contra una constante.

| Lo que decía la ficha | Lo que el apply obligó | Motivo |
|---|---|---|
| Umbral alto de similitud | **Veto relativo entre grupos**, margen 0,05 en configuración | Medido: no existe corte absoluto. Y la primera implementación, `mediana − k·MAD` contra el centroide, era una prueba *dentro* del grupo y disparaba al 16,9 % marcando al miembro menos típico de cada clúster |
| «raíz común de nombre» | Raíz **más fusión por material**, nunca stripping global | Quitar talla y material a la vez degenera `Anillo plata S/M/L/XL` a la raíz `anillo`, que absorbería cualquier otro «Anillo ‹material›» |
| El 1,7 % de la exploración | **3,1 %** (15 de 486 en 5 familias) | Aquella cifra se midió sobre familias de sufijo de talla solamente —24 reales en vez de 68— cuyos miembros son mucho más homogéneos. Más riqueza, más dispersión, más marcas |
| «pantalla de revisión que crea las familias» | La creación es de **C18a**, la pantalla de **C18b** | Sin partirlo, `family_id` seguiría nulo hasta que existiera un frontend |

**Y un matiz de mecanismo que sólo apareció al escribir el test.** El estampado de `Product.UpdatedAt` es la mitad de la historia: el watermark del feed es `greatest(Product, perfil, familia cuando es miembro actual)`, así que **crear** una familia lo mueve por el `UpdatedAt` de la propia familia. El estampado hace falta en el **reemplazo**, donde un producto que sale deja de unirse a la fila de familia. La regla —escribir siempre por `ProductFamilyService`— no cambia; el argumento correcto es que el servicio mantiene el watermark coherente en las **dos** direcciones.

**Decisiones que C18a deja planteadas y no resuelve:**

1. ~~**El doble etiquetado del golden set de C24.**~~ **Resuelto el 2026-08-31** *(ver la entrada de esa fecha sobre prórroga y equipo de uno)*: se etiqueta una vez, se conserva el *pooling*, se añade relectura diferida de las dudosas, y la ausencia de acuerdo entre anotadores se declara como limitación del golden set en el README en vez de reclamar una mitigación que no se aplicó.
2. **`Product.CollectionId` es una FK única y anulable**, pero la spec viva `product-family` justifica la distinción con las colecciones diciendo que un producto puede pertenecer *«to one of many unrelated collections»*. Ambas cardinalidades son 0..1. Los discriminadores reales, medidos: una colección abarca 1–154 productos (mediana 15) y **13–16 tipos de pieza**; una familia, 2–4 de **un solo tipo**.
3. **Las lagunas del vocabulario de enriquecimiento**, en **un solo change** y no tres. Ver la propuesta de abajo. ~~Escala métrica en el vocabulario de talla~~ → **descartado el 2026-08-31**: `Cadena Barbara oro 40/42/45 cm` no son tallas de una misma pieza sino **tres cadenas de longitud distinta**, y declararlas familia forzaría el modelo — la familia agrupa variantes de una pieza, no productos parecidos. Caerán juntas por proximidad de vector cuando alguien busque una cadena de esa colección, que es el comportamiento correcto sin pertenencia declarada.

### 2026-08-31 — Propuesta: `fix-enrichment-vocabulary-gaps` 🟢, un change y no tres

> **Actualización del 1 sep, al cerrar C20.** La propuesta pasa de idea a **ficha propia, `FIX1`, colocada detrás de C21** en el §3 y en el grafo del §4. Se confirma que **exige change y no un commit suelto**, con un motivo que no estaba escrito: cambia el contenido normativo de `openspec/specs/catalog-enrichment-pipeline/spec.md`, que enumera los ocho `piece_type` canónicos en un MUST y fija `prompt_version` = `enrichment/v1` en un escenario — y `openspec validate --all --strict` **seguiría en verde**, porque valida estructura y no verdad. Y se fija el momento: **después de C21**, porque antes no hay rama léxica con la que demostrar que sirve de algo.

Sale de C18a y **corrige dos cosas que su propio informe dejó mal escritas.**

**La primera: el problema es tres veces más pequeño de lo que decía.** La limpieza de C18a se llevó 26 de los 37 productos con `piece_type` nulo. Quedan **once**: las nueve joyas sintéticas que el vocabulario no sabe nombrar —un cinturón de 1.300 €, cinco diademas de 340 a 1.040 €, dos gemelos y una «Joya del Zodiaco»— y los dos llaveros reales que se decidió conservar en el índice.

**La segunda: la premisa de «dar a C09 una salida *no es una pieza*» era falsa.** Esa salida ya existe — el prompt dice literalmente *«`piece_type`: un hiperónimo de la lista cerrada, **o null**»*. Lo que falta no es la opción sino **el encargo**: el prompt abre con *«Eres un extractor de atributos de joyería»* y no contempla que el catálogo contenga otra cosa. Ante `Arreglos oro` hace exactamente lo que se le pidió —extraer atributos de joyería de algo que menciona oro— y *collar* es una conjetura razonable. **No es un fallo del modelo sino una laguna del enunciado**, y se arregla con una línea, no con un cambio de contrato.

**Por qué un solo change.** Los dos arreglos tocan los mismos dos ficheros, exigen el mismo salto de versión de prompt y mueven el corpus por el mismo camino. Separarlos significa bumpear el prompt dos veces y mover el corpus dos veces, que es justo lo que C18a existe para no hacer.

**Alcance.** `piece_type.terms` += `diadema`, `gemelos`, `cinturon` y **`llavero`** —los dos conservados dejan de ser invisibles al filtro, y el cuarto término sale gratis—; prompt **`enrichment/v2`** con la lista nueva más la línea que advierte de servicios, consumibles y regalo; espejo `materials-vocabulary.ts` y su test de fijación; reenriquecer **sólo los once** con **`Force`**; una sola sincronización incremental.

**Corrección del 1 sep: la bandera no se llama `ignoreHash`.** Ese nombre no existe en el repositorio. El mecanismo sí está, y es `request.Force`: [`AiCatalogController.cs`](../../backend/src/JoiabagurPV.API/Controllers/AiCatalogController.cs) salta el reenriquecimiento con `if (!request.Force && stored.SourceHash == hash)`. Se corrige aquí para que nadie abra el change buscando una bandera que no está.

**Fuera de alcance: reenriquecer los 1.200 con `v2`.** Serían ~1.200 llamadas y, peor, podría **reclasificar productos existentes** —algo hoy etiquetado `collar` podría pasar a `cinturon`— cambiando el comportamiento de búsqueda de forma difusa y sin que nadie lo pidiera.

**Coste.** Cuatro ficheros, once productos, **0,9 % del corpus**. Menos de media sesión: no hay algoritmo, ni migración, ni interfaz. **Lo que compra es filtro y búsqueda por tipo**, no familias: las nueve tienen nueve raíces distintas y ninguna agruparía con otra.

**Cuándo.** Mueve el corpus, así que **antes de la línea base de C24**, por el mismo argumento que ordenó C18a: `preprocessing_id` sigue siendo `source-text/v1` y no delataría el cambio.

**Riesgo a comprobar, no a suponer.** Reenriquecer con `v2` puede cambiar otros campos de esos once —materiales, etiquetas— además del tipo. Hay que mirar el diff completo, no sólo `piece_type`.

#### ¿Pueden convivir perfiles `v1` y `v2` en el catálogo? Sí, y el campo existe para eso

Conviene no confundir dos versionados que se parecen y no lo son:

| | `PromptVersion` | `embedding_version` |
|---|---|---|
| Dónde vive | `ProductAiProfiles`, lado .NET | `ai.product_document`, lado Python |
| Qué registra | qué prompt produjo los **atributos** | `modelo : dims : preprocessing_id` |
| ¿Llega al índice? | **No.** Ni al DTO del feed ni a `source_text.py` ni al `source_hash` | **Es** el índice |
| Mezclar versiones | **seguro y trazable** | **la corrupción silenciosa de S11** |

Mezclar `embedding_version` es comparar dos espacios geométricos: la base devuelve un número plausible que no significa nada, sin error. **Este change no lo toca**: la plantilla del documento no cambia, sólo el contenido de once filas.

Mezclar `PromptVersion` es otra cosa. Son dos poblaciones de atributos producidas con instrucciones distintas, comparables como dato, y **el campo se creó para hacer visible esa diferencia en lugar de evitarla** — el perfil problemático es el que no dice con qué prompt nació, no el que sí lo dice.

La única consecuencia real es de **informe, no de corrección**: las métricas que agregan sobre todo el corpus —tasa de corrección por campo de C28, métricas de enriquecimiento del §11.5— mezclarían dos poblaciones. Se resuelve **reportando por `PromptVersion`**, la misma disciplina que C24 ya aplica al reportar por `data_origin`. Estado a 2026-08-31: los 1.200 perfiles están en `enrichment/v1`.

### 2026-08-30 — C17, al cerrar: el riesgo se materializó, y no donde se esperaba

C17 quedó archivado con 86/86 tareas y el entorno vivo. La entrada de abajo advertía de que el change podía «terminar en verde y entregar una URL pública donde *Buscar con ayuda* no encuentra nada». **Ese riesgo se materializó, en una forma que la advertencia no anticipaba**: el índice llegó lleno —1.200 documentos, `drift_count = 0`— y aun así la búsqueda devolvía **200 con diez resultados plausibles** servidos por el camino **léxico**, porque C16 había dejado la búsqueda asistida tras una puerta de despliegue progresivo (`AiSearch:EnabledByDefault`, en `false`) que `compose.demo.yaml` no abría. Sin error, sin traza, y con resultados en pantalla.

Lo encontró la verificación de extremo a extremo —una búsqueda real por la URL pública, leyendo `aiAvailable` en vez del número de resultados—, que es exactamente para lo que la tarea 9.6 existía. **La lección se confirma con un matiz nuevo:** la firma no es sólo «llega vacío», es «llega **degradado y con apariencia de lleno**», que es peor porque ni siquiera un recuento lo delata.

Otros dos hallazgos del apply que afectan a changes anteriores:

- **C13 tenía un defecto de conformidad.** `of_product_ids` ordenaba los identificadores como el `Guid.CompareTo` del .NET *Framework* (con signo) cuando .NET Core compara sin signo, que equivale al orden de bytes. Los dos lados nunca coincidían y `drift_count` **no podía dar cero** con un índice real. La spec viva ya nombraba a .NET como referencia normativa, así que era el código el que la incumplía. La prueba que lo guardaba usaba dos UUID de la misma mitad del rango, donde ambos órdenes coinciden.
- **El presupuesto de recuperación, medido en la demo**: 170, 184 y 383 ms en llamadas calientes; **1707 ms** en una de cada cuatro. El de 2500 ms no se consume en el caso normal, pero volver a los 800 ms del §6.4 degradaría un cuarto de las búsquedas. Se mantiene, y la deuda del cliente de embeddings por petición sigue siendo de C21 o C22.

Detalle completo en `openspec/changes/archive/2026-08-30-add-ai-service-deployment/qa.md`.

### 2026-08-29 — C17, tras la sesión de exploración previa al proposal

La ficha de C17 se escribió dando por hecho que «producción» era un sitio al que este equipo puede desplegar. **No lo es: la cuenta AWS donde vive la tienda no es accesible**, su RDS contiene el catálogo real del negocio, y el script que despliega está horneado dentro de una instancia viva bajo `ignore_changes`. De las seis cosas que la ficha da por sentadas, **cinco no se sostienen**, y la sexta —el `/health` enriquecido— es justo lo que S15 y S16 desaconsejan por escrito. El detalle vive en [HU-AIENG-017](../Historias/AI-Eng/HU-AIENG-017.md) y en el ticket del change; aquí queda el resumen y la ficha corregida.

| Qué decía la ficha | Qué es en realidad | Por qué |
|---|---|---|
| **Zona:** infra | **Seis zonas:** `terraform/demo/`, `.github/workflows/`, la raíz (`compose.demo.yaml`, `deploy/demo/`, `.dockerignore`), `ai-service/`, `backend/` y `frontend/`. **Sigue sin migración:** C17 no es 🗄️ | El `/health` enriquecido es código Python, no infraestructura. Y la tarjeta del dashboard **no puede llamar al servicio desde el navegador** —es privado por diseño—, así que exige un endpoint .NET que lo proxee. Quinta vez que la zona de una ficha se queda corta, tras C08, C07, C15 y C16 |
| «Servicio **en producción** el 19 de agosto, alcanzable solo desde el backend» | **No hay acceso a la cuenta AWS de la tienda.** C17 levanta un **entorno de demo autocontenido en otra cuenta**, sin una sola arista hacia la de producción: ni Terraform, ni grupo de seguridad, ni IAM, ni workflow | La RDS de producción es la base de datos real de la joyería. Inyectar allí 764 productos sintéticos y 12 puntos de venta simulados no es una opción técnica sino un daño al negocio. La frontera de S15 se cumple igual —y con margen— en una cuenta separada |
| «`docker-compose` gana el servicio jbg-ai en la EC2» *(diseño §12.1)* | **En producción no hay docker-compose.** Se despliega con `docker run -d --name jpv-api -p 8080:8080` desde un heredoc dentro de `user_data`, con `lifecycle { ignore_changes = [user_data] }`. [`backend/docker-compose.prod.yml`](../../backend/docker-compose.prod.yml) existe pero es un camino muerto | El §12 se escribió sin leer [`user_data.sh`](../../terraform/templates/user_data.sh). En la demo **sí** hay compose, así que el §12.1 acaba siendo cierto — pero en otra máquina y por otro motivo |
| «`CREATE EXTENSION vector` en RDS» | **La demo no lleva RDS.** Postgres+pgvector en contenedor, con la misma imagen `pgvector/pgvector:pg15` que ya usa el compose local | Vuelve **irrelevante** la verificación que el propio plan marcaba como *tarea obligatoria fuera de código* y que nunca se ejecutó: *«verificar que RDS admite `CREATE EXTENSION vector`; si no, el plan B hay que saberlo hoy, no el 25 de agosto»*. Se adopta el plan B que el plan ya nombraba, y se gana simetría exacta con el entorno local |
| «red interna **sin exposición en nginx**» | **Caddy en contenedor**, no nginx en el host. La frontera queda escrita en el fichero: sólo el proxy declara `ports:` | Caddy emite y renueva el certificado solo. Elimina certbot, su cron, el heredoc de configuración y el paso manual posterior al DNS. La asimetría con producción no cuesta nada, precisamente porque la demo es deliberadamente otro sistema |
| «`/health` enriquecido (BD **y proveedor** OK)» | Enriquecido **sí**; con el proveedor **no**. `provider` informa de si la clave está **configurada**, nunca de si el proveedor responde | S15: *«si dependiera de que el proveedor de LLM responda, un hipo del proveedor haría que vuestro healthcheck fallara [...] un sistema que se autodestruye cada vez que el LLM tose»*. S16: *«el `/health` sigue siendo barato y tonto [...] no confundáis el latido con la vigilancia»*. Ninguno de los tres consumidores del latido necesita despertar al proveedor |
| «Smoke post-deploy» | **No puede alcanzar el servicio**: es privado por diseño y el runner de GitHub está fuera. Va por `aws ssm send-command` + `docker exec`, como el propio despliegue | |
| Nada sobre `design.md` | **C17 lleva `design.md`** | Veinte decisiones cerradas con alternativas defendibles y seis zonas. Sexta vez que la lista del §7 se queda corta, tras C08, C07, C15 y C16 |

**El hallazgo que gobierna el change: desplegar no es el problema, el dato lo es.** C17 puede terminar en verde —`/health` OK, smoke verde, `openspec validate --all --strict` en `0 failed`— y entregar una URL pública donde «Buscar con ayuda» no encuentra nada, nunca. Todo el corpus vive en el Docker local y el plan lo dice en tres sitios: *«INSERT local […] (Docker, no RDS)»*, *«RDS/producción»* en el fuera de alcance de C06b, y el runbook de C12 *«una persona, en local (y más adelante en demo)»*. Son 1.200 productos, 38 colecciones, 12 puntos de venta, 6.720 filas de inventario, 1.200 `ProductAiProfile` en `Approved` y 1.200 `ai.product_document` con sus vectores, y **ninguno de esos números existe fuera de un portátil**. El §16 pide como criterio de entrega *«URL pública con usuario demo y vídeo de 2-3 min»*: el entregable es exactamente la cosa que quedaría vacía. Es la tercera vez que aparece esta firma en el proyecto —A1 en C04, B5 en C16, y ahora el índice— y las tres comparten síntoma: compila, pasa, valida, y llega vacío a septiembre. **C17 se lleva el camino del dato, y no lo deja en un runbook.**

**El segundo hallazgo: hay dos valores que, mal puestos, mienten sin dar un solo error.** `STUB_MODE` en `true` devuelve fixtures con toda la apariencia de funcionar. Y un `JPV_EMBEDDING_MODEL` distinto del que generó los vectores compara dos espacios vectoriales como si fueran uno: la búsqueda devuelve ruido, con HTTP 200 y sin traza. Ninguno de los dos es un secreto, y de ahí sale la regla que gobierna la configuración del change: **se versionan en git como literales, no en el almacén de parámetros**, porque el almacén es un sitio donde alguien puede cambiar un valor sin revisión de código y estos dos exigen revisión de código y reindexado. Además se comprueban: `ai.product_document` guarda `embedding_model` **por fila** desde C13, así que el `/health` puede contrastar lo configurado contra lo indexado y pintar `model_mismatch` en la tarjeta del administrador. Es el fallo más silencioso del despliegue convertido en una línea roja.

**Decisiones cerradas en la sesión.**

| # | Tema | Decisión |
|---|---|---|
| 1 | Entorno | **EC2 de demo autocontenida** con Postgres+pgvector en contenedor, en **otra cuenta AWS**. Terraform en directorio y **estado propios**, de modo que un `apply` no pueda ni siquiera planificar un cambio sobre un recurso de la tienda |
| 2 | OIDC | Se **crea** el `aws_iam_openid_connect_provider` porque la cuenta es virgen. Queda escrito en `design.md` que es un **singleton por cuenta y emisor**: en una cuenta que ya tenga GitHub OIDC registrado hay que cambiar el `resource` por un `data`, o el `apply` falla con `EntityAlreadyExists` |
| 3 | Ramas | Trabajo en `c17-add-ai-service-deployment`, desde `ai-eng`. Despliegue desde **`demo`**, emparejada con un **GitHub Environment** homónimo, y confianza OIDC acotada a `repo:<org>/<repo>:environment:demo` — **más estricta que la de producción**, que confía en `:*`. `workflow_dispatch` para iterar sin ensuciar `demo` |
| 4 | Plugin de Compose | **Binario de la release con versión fijada** en `/usr/libexec/docker/cli-plugins/`. Ni `dnf install` (el nombre del paquete no está garantizado en AL2023) ni `latest` (rompe la reproducibilidad que S15 exige) |
| 5 | `user_data` | **Mínimo, cuatro pasos**, sin nada específico de la aplicación: instalar Docker y el plugin, arrancar Docker y el agente SSM, traer el compose y el script, ejecutarlo. AMI resuelta con `data "aws_ssm_parameter"` del alias público de AL2023, lo que **elimina `var.ami_id` y su paso manual** |
| 6 | Proxy y TLS | **Caddy en contenedor.** `${DEMO_HOSTNAME}` parametrizado: se arranca con un nombre `sslip.io` derivado de la IP elástica y se migra al dominio propio **cambiando un parámetro y redesplegando**. El dominio no bloquea el change |
| 7 | Compose | **`compose.demo.yaml` autocontenido en la raíz**, con los cuatro servicios. [`backend/docker-compose.yml`](../../backend/docker-compose.yml) **no se toca**: la spec viva `ai-service-dev-compose` **fija su ruta y su red literalmente** en dos requirements, y moverlo costaría un delta de spec, cinco documentos y el flujo diario de desarrollo |
| 8 | Frontera | **Sólo el proxy publica puertos** (80/443). `api`, `ai` y `postgres` sin `ports:`. Un error en el grupo de seguridad no puede exponer el servicio de IA **porque no hay puerto que exponer** |
| 9 | Secretos y ajustes | Taxonomía en cuatro clases: **A secreto** (SSM SecureString → entorno del proceso → `${VAR}`, **nunca a disco**), **B ajuste de entorno** (SSM String), **C ajuste de comportamiento** (**git**) y **D constante** (imagen). `environment:` explícito, **nunca `env_file:`** en el servicio de IA, conservando el motivo que ya razonaba el compose local |
| 10 | Los dos valores que mienten | `JPV_EMBEDDING_MODEL` (`openai/text-embedding-3-small`), `JPV_RETRIEVAL_DISTANCE_THRESHOLD` (0,65) y `STUB_MODE` (`false`) son **clase C: literales versionados**. Más la salvaguarda: el `/health` contrasta el modelo configurado contra el `DISTINCT embedding_model` del índice |
| 11 | Parejas de secretos | `JWT_SECRET` ↔ `AiGateway__JwtSecret` y la clave del feed salen de **un solo parámetro leído dos veces**, no de dos que puedan derivar. Derivar produce un **401 cuya causa el servicio tiene prohibido revelar** |
| 12 | Health | **Enriquecido en el sitio, cacheado ~10 s, sin llamar al proveedor.** Mantiene `dict[str, Any]`, así que **`openapi.json` no se regenera** y el contrato congelado sigue congelado. El disparador de la futura bifurcación queda escrito abajo |
| 13 | Health en .NET | `AiHealthController` en `api/ai/health`, sólo administrador, siguiendo el patrón «un controlador por capacidad» de C15, y **fuera del circuit breaker**: el trabajo de la sonda es diagnosticar precisamente cuando el camino principal está roto |
| 14 | Imágenes | **`Dockerfile.demo` nuevo e independiente** para API+SPA, con `VITE_API_BASE_URL=/api`. `Dockerfile.bundled` **intacto**: es el de producción. `ai-service/Dockerfile` se endurece en su sitio —usuario no-root, `uv` con versión fijada en lugar de `latest`, multietapa y `HEALTHCHECK`— porque **no tiene ningún consumidor en producción** |
| 15 | Base relativa | `VITE_API_BASE_URL=/api` funciona: la SPA se sirve desde `wwwroot/` del **mismo contenedor**, así que es mismo origen, y tanto `api.service.ts` como `image-url.ts` resuelven bien. La imagen de demo queda **agnóstica del hostname** y sirve incluso sobre una IP desnuda |
| 16 | Deprecaciones | `Dockerfile`, `Dockerfile.prod` y `backend/docker-compose.prod.yml` reciben cabecera de deprecado **y se corrige `backend/README.md`**, que hoy presenta un camino obsoleto como el de producción. Es la deuda que **el ticket de C03 ya asignó a C17** por escrito |
| 17 | `.dockerignore` | **Nuevo en la raíz.** El contexto de build de `Dockerfile.bundled` son hoy **~1 GB**: 711 MB de `node_modules`, 265 MB de `.venv`, 36 MB de `.git` y 30 MB de `data/` |
| 18 | Memoria | `mem_limit: 512m` en el contenedor de IA: un OOM mata **sólo** la IA y el breaker degrada a léxico, que es la degradación diseñada extendida a la capa de infraestructura. Más swap en el disco ya pagado. **`deploy.resources` no vale**: se ignora fuera de swarm |
| 19 | Camino del dato | `pg_dump` de `public` más `pg_dump -n ai` desde local, restaurar en la demo, y **un** `POST /v1/index/sync` de reconciliación con `drift_count = 0`. Los vectores viajan: no se re-facturan y son **fila a fila los mismos** sobre los que se calculan las métricas del README y la ablation del §11.2 |
| 20 | Usuarios de la demo | Se sustituye el personal real de la joyería —correos y hashes— por **cuentas de demo** (una de administrador y una de operador, para que se vean los dos dashboards y el embudo que sólo ve admin). **Los 436 SKU reales con sus precios sí se publican**, decisión de negocio tomada en la sesión |

**Cuándo se bifurca el `/health`, escrito de antemano.** Hoy uno solo, enriquecido y barato. Se parte en `/health` (liveness) y `/health/ready` (readiness) cuando se cumpla **cualquiera** de estas tres, y no antes: cuando algo pueda **reiniciar el contenedor** en función de la respuesta —un orquestador en lugar de un único host Docker, que es la condición que activa el bucle de autodestrucción de S15 y que hoy no se da porque `--restart unless-stopped` no reinicia por `unhealthy`—; cuando la parte cara **deje de ser cacheable barata**, por ejemplo si el estado del índice exigiera un recuento real sobre un corpus mucho mayor que 1.200 documentos; o cuando el servicio de IA **se despliegue a la cuenta real de la tienda**, donde la sonda deja de servir a una demo y pasa a gobernar la disponibilidad de un sistema con clientes. Al bifurcar, `/health/ready` es ruta nueva y por tanto **regenera `openapi.json`** y rompe `test_openapi_snapshot_is_stable`, que es lo correcto: la frontera se habrá movido y toca renegociarla. Anotado en `DEFERRED_TASKS.md` junto a la deuda de los 800 ms.

**Tres avisos que el ticket lleva en grande.** El volumen `jbg-demo-caddy-data` **guarda los certificados**: si se pierde en un redespliegue, Caddy los vuelve a pedir y Let's Encrypt limita a **cinco certificados duplicados por semana** — dos descuidos y la demo se queda sin HTTPS hasta la semana siguiente, con la entrega el 3 de septiembre; el script usa `up -d` y **jamás `down -v`**. `set -x` está **prohibido** en el tramo que lee parámetros `SecureString`, porque la salida de `aws ssm send-command` se conserva en el historial de SSM. Y cada variable requerida se valida con `:?`: una vacía no falla, arranca un contenedor que devuelve 401 a todo.

**Lo que C17 no puede hacer todavía, y no disimula.** El presupuesto de recuperación sigue en los **2500 ms temporales de C16** y en la demo, contra un proveedor a más latencia que un portátil, puede quedarse corto otra vez: C17 **mide y anota**, no arregla —el singleton del cliente de embeddings sigue siendo de C21 o C22—. El **arranque en frío** paga importación de LiteLLM más embedding frío en la primera consulta, así que el despliegue incluye una llamada de calentamiento antes de grabar nada. Y `aiAvailable: false` sigue sin distinguir circuito abierto de asistencia desactivada: decisión cerrada en C16, que C17 no reabre.

**Cortes que no se reabren:** la cuenta AWS de la tienda **no se toca en absoluto** —ni Terraform, ni grupo de seguridad, ni IAM, ni workflow, ni `jpv-deploy.sh`—; `Dockerfile.bundled` no se toca; `backend/docker-compose.yml` y la spec viva `ai-service-dev-compose` no se tocan; el contrato C02 no se toca y `openapi.json` no se regenera; C17 no abre migración, ni de EF Core ni de Alembic más allá del `upgrade head` que ya existe; y no se adelanta nada de C21 ni de C22.

### 2026-08-29 — C16, tras la sesión de exploración previa al proposal

La ficha de C16 se escribió cuando no existían ni el retriever ni el endpoint. Con C15 archivado se puede leer el contrato real, y **la ficha promete tres cosas que el código no puede dar hoy y una que no cabe en una sola zona**. El detalle vive en [HU-AIENG-016](../Historias/AI-Eng/HU-AIENG-016.md) y en el ticket del change; aquí queda el resumen y la ficha corregida.

| Qué decía la ficha | Qué es en realidad | Por qué |
|---|---|---|
| **Zona:** `frontend/src/` | **Tres zonas:** `frontend/src/` más dos tramos pequeños en `Application/` y `Tests/` del backend. **Sigue sin migración:** C16 no es 🗄️ | B5 exige enviar `searchEventId` en `CreateSaleRequest` / `BulkSaleLineRequest`, y **ninguno de los dos objetos de transferencia tiene el campo**. La columna `Sale.SearchEventId`, su índice y su clave foránea existen desde C04, pero el único sitio del repositorio que los escribe es un test de integración asignando la entidad a mano |
| B5 dado por implementable desde el navegador | **No lo es**, y detrás hay algo peor: la spec viva `ai-search-telemetry` declara la requirement *«Sale attribution is carried by the sale, not by the event»* con su escenario, archivada como cumplida, y **no se puede cumplir a través de la API** | Es la misma clase de defecto que A1: compila, los tests pasan, `openspec validate --all --strict` da verde y la columna llega vacía a la entrega. La diferencia es que aquí ya hay una spec archivada afirmando lo contrario, así que el síntoma no es la ausencia de un dato sino una spec que miente |
| «resultados con … **motivo**» | `match_reasons` es la cadena literal `["vector"]` para **todos** los resultados, fijada en [`retrieval/orchestrator.py`](../../ai-service/src/jbg_ai/retrieval/orchestrator.py) hasta que C21 añada la rama léxica | Renderizarla sería enseñarle al operador una palabra de ingeniería. Se sustituye por **insignia de origen + chips de materiales**, lo que exige devolver `materials` en `AssistedSearchResultDto`: los materiales ya llegan del retriever a .NET y `BuildResultsAsync` los descarta. Es una línea |
| «resultados con … **talla**» | Es `variantLabel`, y lo puebla **C18**, que no se ha ejecutado. Hoy es nulo en todas las filas | Se renderiza condicionalmente y aparece sola cuando C18 entre. No se inventa un sustituto ni se hidrata `ProductAiProfile.SizeLabel`, que sería rehacer trabajo de C15 |
| «los **tres** cero resultados» (B6) | **Son cuatro.** El contrato de C15 obliga a un estado que la ficha no menciona: **cuota de peticiones agotada**, que su spec exige distinguir explícitamente de «la IA no está disponible» | El límite es de 30 peticiones por minuto y por usuario. Confundirlo con la degradación haría que una cuota agotada se leyera en pantalla como una caída del servicio, y que un `debounce` mal ajustado pareciera un problema de infraestructura |
| Nada sobre `design.md` | **C16 lleva `design.md`** | Hay ocho decisiones con alternativas defendibles y un cruce de tres zonas. Cuarta vez que la lista del §7 se queda corta, tras C08, C07 y C15 |

**El hallazgo que gobierna el change: en este panel cada pulsación cuesta dinero, y eso decide el modelo de interacción.** El buscador de catálogo existente usa `useDebouncedCallback` y copiarlo aquí sería el camino natural; la aritmética lo desaconseja. La clave de la caché de candidatos de C15 incluye la cadena de consulta completa, así que **ningún prefijo acierta**: una consulta en lenguaje natural de treinta caracteres produce entre tres y seis peticiones con un `debounce` de 400 ms, y cada una factura un embedding que nadie llegó a leer. Con el límite de C15, un operador agota su cuota en **cinco o seis consultas**. Y el presupuesto de recuperación son 800 ms más hidratación, de modo que la sensación de «resultados mientras escribo» nunca estuvo disponible: no se renuncia a nada. Se elige **envío explícito** más un conjunto de consultas de ejemplo, que es además lo que S4 llama hornear el prompting en la interfaz en lugar de delegarlo en el usuario.

**El segundo hallazgo: los filtros duros se apilan y vacían la página.** El filtro de materiales de C14 es un solapamiento de conjuntos aplicado **antes** del umbral y del límite; la hidratación por punto de venta de C15 corta después, y ninguno de los dos es del panel. Con las coberturas de C10, un material poco frecuente —`perla`, `cuero`, `resina`— combinado con Fornells (0,22) produce página vacía casi con seguridad. De ahí dos consecuencias de interfaz: el estado «sin surtido» ofrece **quitar filtros** como primer remedio, no «reformula»; y la página corta **se declara en pantalla** en lugar de disimularse, porque es la línea base «antes» de la ablation de C22 en §11.2 contada al operador en una frase.

**Decisiones cerradas en la sesión.**

| # | Tema | Decisión |
|---|---|---|
| 1 | Atribución de venta (B5) | **C16 incluye el tramo .NET mínimo:** `Guid? SearchEventId` en los dos objetos de transferencia de venta y asignación en el servicio. Un identificador desconocido **o perteneciente a otro usuario** degrada la atribución a nula; la venta **nunca** falla. Sin migración: la columna es de C04 |
| 2 | Ubicación del panel | **Ruta propia** `/sales/new/assisted` y **tercera tarjeta** en `/sales`, con el patrón de `scan.tsx`: entrega por estado de navegación. Aísla el fichero que C36 va a ampliar y mantiene la arquitectura de información del hub de ventas |
| 3 | Disparo de la búsqueda | **Envío explícito** (Enter o botón) más 3-5 consultas de ejemplo. Los filtros rápidos **no disparan por sí solos**; cambiar de punto de venta limpia los resultados y no relanza |
| 4 | El «motivo» | **Insignia de origen + chips de materiales**, con `materials` añadido a `AssistedSearchResultDto`. El mapa de insignias queda preparado para que C21 añada `lexical` sin tocar el panel |
| 5 | Estados sin resultados | **Cuatro:** abstención, sin surtido en este punto de venta, degradado o desactivado, y cuota agotada. Más un quinto que no está vacío: **página corta**, declarada en pantalla |
| 6 | Vocabulario de materiales | **Constante en el frontend**, espejo de [`vocabularies.yaml`](../../ai-service/src/jbg_ai/enrichment/vocabularies.yaml), fijada por un test. Un endpoint que agregue los materiales realmente presentes en el surtido de ese punto de venta es mejor producto y se anotó para C28. **C28 no lo hizo** *(corregido el 2026-09-13, al archivarlo)*: sí extendió el espejo a los **seis** vocabularios cerrados —piedra, color, estilo y ocasión además de material y tipo de pieza, todos fijados por test— y los usa como selección en la pantalla de revisión, pero el endpoint de agregación sigue sin escribirse y **permanece sin ficha** en [`DEFERRED_TASKS.md`](../../openspec/DEFERRED_TASKS.md), donde `FIX1` lo dejó. C28 sí aporta la medición que lo justifica mejor que antes: el espejo **no puede descubrir un hueco de cobertura**, y la revisión humana encontró uno de 67 productos (`vidrio`) que ninguna consulta sobre el vocabulario podía ver |
| 7 | Embudo | Bloque colapsado **solo para administradores** con el identificador de correlación y `candidatos → supervivientes → mostrados`. Evidencia directa para §11 y para el checklist de §16, a coste casi nulo |
| 8 | Episodio de búsqueda | Un `searchSessionId` por **montaje del panel**. B2 existe para que las reformulaciones de una visita no cuenten como abandonos, y las reformulaciones ocurren dentro de la visita: dos visitas que acaban cada una en selección son dos episodios legítimos, no dos falsos abandonos |

**Lo que el panel no puede distinguir, y se acepta.** La respuesta trae `aiAvailable: false` tanto si el circuito está abierto como si la asistencia está desactivada en ese punto de venta. La telemetría **sí** los separa (`LexicalFallback` frente a `Disabled`); la API no. Para el operador el mensaje es el mismo —la búsqueda asistida no está sirviendo—, así que se deja como decisión consciente y escrita, en lugar de pedirle a C15 un discriminador que sólo cambiaría el texto de un aviso.

**Cortes que no se reabren:** el contrato C02 no se toca, `ai-service/` no se toca, C16 no abre migración, `/api/v1/products/search` se queda como está, y `C16 ‖ C36` sigue sin poder ejecutarse en paralelo.

### 2026-08-28 — C15, tras la sesión de exploración previa al proposal

La ficha de C15 se escribió cuando el retriever no existía. Con C13 y C14 archivados se puede leer el SQL real, y tres de las cosas que la ficha da por hechas no se sostienen. El detalle vive en [HU-AIENG-015](../Historias/AI-Eng/HU-AIENG-015.md) y en el ticket del change; aquí queda el resumen y la ficha corregida.

| Qué decía la ficha | Qué es en realidad | Por qué |
|---|---|---|
| «**repide con `top_k` mayor** si quedan pocos» | **Se elimina.** C15 pide `top_k = 20` → `min(20×3, 60) = 60` candidatos, el techo absoluto del contrato, en **una sola llamada** | El SQL de C14 aplica el umbral 0,65 **antes** del `LIMIT`. Si vuelven menos candidatos que el `overfetch`, ató el umbral y no el `LIMIT`: repedir devuelve **exactamente las mismas filas** cobrando un segundo embedding. Sólo aportaría algo con `top_k < 20`, y jamás por encima de 60 |
| «`ai_available: false` + **resultados léxicos**» con el buscador existente | **Buscador degradado nuevo**, acotado al POS de la búsqueda, con `to_tsvector('spanish', …)` calculado en consulta, **semántica OR** y orden por `ts_rank` | [`ProductService.SearchProductsAsync`](../../backend/src/JoiabagurPV.Application/Services/ProductService.cs) hace `Name.Contains(consulta)` sobre la cadena completa: ante *«un anillo de plata para regalar»* devuelve **la lista vacía, siempre**. Y filtra por *todos* los POS asignados, no por el de la búsqueda. Un fallback que nunca encuentra nada es una caída silenciosa con HTTP 200 |
| **Zona:** `API/Controllers/`, `Application/` | Igual, más `Tests/`. **No** `Infrastructure/`: C15 no lleva migración | Ninguna de las decisiones cerradas necesita esquema nuevo, y el plan contabiliza seis migraciones sin ninguna suya |
| Nada sobre `design.md` | **C15 lleva `design.md`** | Hay seis decisiones con alternativas defendibles y coste asimétrico. Tercera vez que la lista del §7 se queda corta, tras C08 y C07 |
| «Mismo controlador `AiController.cs`» (§5, pares que no van en paralelo) | **No existe `AiController.cs`.** El patrón real es un controlador por capacidad: `AiCatalogController`, `AiIndexFeedController`, `AiSearchEventsController`. C15 crea `AiSearchController` en `api/ai/search`, sin versión | El conflicto de zona **C15 ‖ C34 deja de ser el fichero del controlador** y pasa a ser el servicio de búsqueda compartido. Siguen sin poder ir en paralelo, por otro motivo |

**El hallazgo que gobierna el change: el filtro más selectivo del pipeline está al final, a un salto de red, y correlaciona con el ranking.** El §7.6 paso 1 sitúa el `pos_id` como filtro duro **en Python**. Pero C13 no indexó disponibilidad y C14 declara explícitamente que *«the search SQL does not filter by `pos_id`»*, difiriéndolo a C22. C15 vive en la ventana intermedia y sólo puede aplicarlo al hidratar, que es el paso 6.

Medido con el generador de C10 (`n_take = round(coverage × 1200)`, más `inactive_inventory_ratio_live_pos: 0.08`; la suma da 6.720, exactamente el inventario del informe):

| POS | cobertura | activos ≈ | supervivientes de 30 | de 60 |
|---|---|---|---|---|
| CIU-CENTRE (`op-ciutadella`) | 0,78 | 861 | 21,5 | 43 |
| MAO-AIR (`op-aeroport`) | 0,38 | 420 | 10,5 | 21 |
| **FORNELLS (`op-fornells`)** | **0,22** | **243** | **6,1** | **12,1** |

Con 30 candidatos, FORNELLS llena una página de 10 en el **~4 %** de las búsquedas. Y `collection_weights` sesga el surtido (`Tramontana` y `Caliza` a 3,5; `Filigrana` y `Cielo estrellado` a 0,3), así que el descarte **no es un adelgazamiento uniforme del 20 %**: correlaciona con la señal de ranking, y una consulta alineada con una colección que ese POS casi no tiene devuelve 0-2 resultados. Es el fallo que S10 describe como *«el filtro descartó 48 y la consulta entregó 2 sin ningún error visible»*, agravado. **Dos de los tres operadores de demo están en 0,38 o por debajo**, así que esto es el vídeo de la entrega, no un caso borde.

**Se acepta el corte y se mide**, en lugar de adelantar C22 fuera de zona. La tasa de llenado por POS es la línea base «antes» de la ablation de C22 en §11.2, y **se computa con lo que C04 ya persiste**: `% de búsquedas con ResultsCount < página`, agrupado por `PointOfSaleId`. Ninguna columna nueva. Distinguir la **abstención** (la IA no encontró nada) del **sin surtido** (la hidratación lo tiró todo) se resuelve uniendo por `TraceId` con el log `stage=search` de C14, que ya está obligado a emitir `low_confidence` y `candidates` — el cruce que la decisión 6 de HU-014 dejó previsto.

**Dos deudas que C15 anota y no paga.** La primera es de otro servicio: [`api/routers/retrieval.py`](../../ai-service/src/jbg_ai/api/routers/retrieval.py) construye un `LiteLlmEmbeddingClient` **por petición**, así que la caché RAM que C11 congeló nace vacía y muere con la respuesta — en retrieval **no hay ni un acierto en producción**. Tres líneas en `main.py` lo arreglan, y le tocan a **C21 o C22**, que ya trabajan en `retrieval/`; C15 no cruza a Python y mitiga por su lado con una caché de candidatos. La segunda: un índice GIN sobre `public."Products"` sólo tendrá sentido si el catálogo crece un orden de magnitud. Con 1.200 filas ese índice compraría lematización, no velocidad, y la lematización ya se obtiene sin él.

**Obligación heredada por C16.** Los tres «cero resultados» —abstención, sin surtido en este POS, y camino degradado— tienen que decirle cosas distintas al operador. Con un único `results: []` son indistinguibles, y el panel mentiría en dos de los tres casos.

### 2026-08-27 — C14 archivado

Change [`2026-08-27-add-vector-retrieval-endpoint`](../../openspec/changes/archive/2026-08-27-add-vector-retrieval-endpoint/). Spec viva: `vector-retrieval`. `POST /v1/retrieval/products` real (`STUB_MODE=false`); stub C02 si stub mode. Umbral `JPV_RETRIEVAL_DISTANCE_THRESHOLD` 0,65; hybrid/lexical = vector hasta C21. 503 si faltan key/DB/índice compatible. Sin `query_log`, sin regenerar OpenAPI, sin `embeddings.py`, sin `pos_id`.

### 2026-08-26 — C13 archivado

Change [`2026-08-26-add-product-document-indexer`](../../openspec/changes/archive/2026-08-26-add-product-document-indexer/). Spec viva: `product-document-indexer`. `POST /v1/index/sync` y `GET /v1/index/status` reales (`STUB_MODE=false`); stub C02 si stub mode. Keyset OpenAPI `since_id` / `cursor_id`. Mapa `sku_provenance.json` en `src/`. Alembic `text_provenance` + `sync_checkpoint`. Sin POS, sin `embeddings.py`, sin migración EF.

### 2026-08-26 — C12 archivado

Change [`2026-08-26-add-dotnet-index-feed-endpoints`](../../openspec/changes/archive/2026-08-26-add-dotnet-index-feed-endpoints/). Spec viva: `index-feed`. Feeds HTTP de catálogo (50) y POS (200) con API Key; 401 ante JWT de usuario o token C03. Tombstones por `kind`/`reason` (la ficha v3 nombraba `{deleted_at|deactivated_at}` y 403). Sin migración, sin push a `/v1/index/sync`. Runbook AutoBulk escrito, no ejecutado.

### 2026-08-22 — C06a archivado: corpus offline, no generador de servicio

La ficha original de C06a adjudicaba generadores en `ai-service/src/jbg_ai/data/generators/`, cliente LLM y migración Alembic de `text_provenance`. El change archivado [`2026-08-22-add-real-catalog-ingestion-and-text-assist`](../../openspec/changes/archive/2026-08-22-add-real-catalog-ingestion-and-text-assist/) entrega el resultado (JSONL de 436, dos ejes de procedencia, ingesta local de `Description`) por otro camino, documentado en su `design.md`:

| Ficha original | Apply cerrado |
|---|---|
| Zona `jbg_ai.data` + `prompts/` | Pipeline offline en [`scripts/catalog/`](../../scripts/catalog/) (`catalog-pipeline`: lectura, agrupación interna, reparto, redacción, validación, ingesta) |
| Cliente LLM en `ai-service` | Pasada de vendedor `catalog-assist/v2` en `assist.py` (plantillas deterministas, **sin** proveedor); `model: null` en el sidecar |
| Migración `text_provenance` | **C13** — C06a **no** es 🗄️ |
| JSONL on-demand | JSONL **commiteado**: [`data/catalog/real/generated/catalog-real-enriched.jsonl`](../../data/catalog/real/generated/catalog-real-enriched.jsonl) + sidecar `.meta.json` |
| ~10 % «sin descripción» / tier `empty` | Tier **`original`**: se deja la `Description` del xlsx (no se vacía ni se reescribe) |
| Semilla de familias en el JSONL | **No se emite.** Agrupación solo interna para el sorteo. C18 no lee este corpus |
| Ingesta | `UPDATE` local de `Description` por SKU; **0 unmatched**; 436 filas tocadas; identidad intacta |

**Artefactos de traza.** `generator_version` `c06a-assist/v2`, semilla `20260822`. Sidecar: 293 `rich` (67,20 %), 94 `sparse` (21,56 %), 49 `original` (11,24 %) — dentro de 70/20/10 ±3 pp. Procedencia: 387 `ai_assisted` / 49 `merchant`. Agrupación interna (no serializada): **354 grupos**, 44 multi-variante, 310 unarios (la referencia de exploración ~403/~23 era orientativa). Contrato de línea: `sku`, `name`, `description`, `price`, `collection_name`, `data_origin: real`, `text_provenance`, `text_quality_tier`. Tope `Description` 1000 caracteres. Spec viva: `real-catalog-corpus`. Informe: [`informes/c06a-catalog-enrichment-report.md`](informes/c06a-catalog-enrichment-report.md).

**Lo que esto deja escrito para C06b.** La zona `jbg_ai.data` **sigue vacía**: C06a no la inauguró. El JSONL real es el ancla de SKUs y de colecciones a no reutilizar (436 SKUs `SKU01`…, 28 colecciones). La voz v2 es **plantilla** —por eso huele a determinista—; C06b no reutiliza `assist.py`. `text_provenance` sigue sin columna: vive en JSONL hasta C13.

### 2026-08-22 — C06b, tras la sesión de exploración previa al proposal

La ficha v3 de C06b (y la fila de C06b en la tabla del 17 ago) mezclaba tres trabajos y copiaba cifras dimensionadas para un catálogo 100 % sintético. Con C06a archivado y el real en 436 productos / 354 grupos internos, esas cifras ya no significan lo mismo. Decisiones de la exploración:

| Ficha 17 ago | Ahora |
|---|---|
| Zona `jbg_ai.data.generators/` como generador determinista de servicio | Mismo paquete, **CLI** que no se importa desde `jbg_ai.api.main`. Ni FastAPI ni API .NET. C10, cuando llegue, se sienta al lado (mundo numérico, también CLI) |
| Calibrar precio, SKU, materiales y tamaño de familia al real | **No.** SKU lo reserva el código (sin colisión con C06a). Precio y copy los razona un **LLM**. Materiales multi-valor en la **prosa** (~35 %), no como `materials[]` en el JSONL |
| ~350 familias S/M/L y 15 % de huérfanos | **Fuera de C06b.** `Product` no tiene columna de familia; D4 es **C18**. Los sintéticos nacen huérfanos (204). Tallas en el nombre, si el LLM las escribe, son catálogo, no semilla |
| 900-1.200 productos, calibrados | Presupuesto **~1.200 totales** (436 + sintéticos; holgura, no cifra exacta) |
| JSONL versionado | JSONL + sidecar en `data/catalog/synthetic/generated/` **e `INSERT`** local de colecciones nuevas y productos (Docker, no RDS) |
| Tests de distribución de precio y ratio de huérfanos | Caen. Entran unicidad de SKU, ingesta sin tocar reales, tope 1000, LLM fake en pytest, settings sin API key obligatoria al boot |

Colecciones: **solo nuevas**, pensadas como brief de vitrina de hotel, aeropuerto/turista o tienda clásica — no un campo de canal en `Product`. Un par pueden seguir la temática menorquina; el resto divergen del mar saturado del real.

El grafo `C06b → C11` sigue siendo cierto **porque hay ingesta**: sin filas en `public."Products"`, el feed de C12 no ve el sintético.

### 2026-08-22 — C06b, longitud del copy alineada al real

La nota de calibración de la ficha («no se hereda la longitud de descripción») queda acotada: **precio y tamaño de familia siguen sin heredarse**; la **longitud del copy sí** se aproxima a las medias del JSONL C06a (`rich` ~289 / `sparse` ~115 / `original` ~14). El código declara el `text_quality_tier` **antes** del draft (`catalog-synth/v3`), recorta solo frases enteras y deja ~20 % de los `short` vacíos. Sidecar vigente: `c06b-synth/v3`. El JSONL sintético ya está generado (764).

### 2026-08-23 — C09 archivado

Change [`2026-08-23-add-catalog-enrichment-pipeline`](../../openspec/changes/archive/2026-08-23-add-catalog-enrichment-pipeline/). Spec viva: `catalog-enrichment-pipeline`. Extractor real en `jbg_ai.enrichment/` detrás de `POST /v1/enrich/products` cuando `STUB_MODE=false`; prompt `enrichment/v1`; LiteLLM temp 0; puertas de lote en auditor fuera del HTTP. `openapi.json` no se regeneró.

### 2026-08-23 — C06b archivado

Change [`2026-08-23-add-synthetic-catalog-augmentation`](../../openspec/changes/archive/2026-08-23-add-synthetic-catalog-augmentation/). Spec viva: `synthetic-catalog-corpus`. JSONL 764 + sidecar `c06b-synth/v3` / `catalog-synth/v3`. Ingesta local el 2026-08-22: `"Products"` 1200, `"Collections"` 38, `"ProductFamily*"` 0. GET familia sobre SKU440 → 204. `jbg_ai.data` queda inaugurada (CLI; `api.main` no la importa).

### 2026-08-17 — C06, tras la sesión de exploración previa al proposal: el export real sirve por tamaño y no por texto

El export llegó y se importó: **436 productos**. El plan se había preparado para que fuera **pequeño** —§14 pregunta 7 pregunta por su tamaño, §13.5 teme que sea insuficiente— y resultó ser de tamaño razonable (la mitad del objetivo de 900-1.200) pero **textualmente casi vacío**: 38,5 caracteres de media entre nombre y descripción, con 51 productos sin descripción ninguna.

Medido por campo que C09 tiene que extraer, el corpus no es pobre de forma uniforme, es **ciego a las etiquetas comerciales**:

| Campo | Evidencia en los 436 reales | |
|---|---|---|
| `piece_type` | 383 | **88 %** |
| `materials[]` | 384 | **88 %** |
| `size_label` | 66 | 15 % (por regex, como ya diseñaba C09) |
| `stone_type` | 34 | **8 %** |
| tags de color / estilo / ocasión | ~0 | **sin ninguna base** |

Eso destapa **dos contradicciones que ya estaban en el documento** y que nadie podía ver hasta tener el dato:

| # | Contradicción | Resolución |
|---|---|---|
| 1 | **C09 no puede aprobar su propia puerta.** §8.5 exige `cobertura de tags ≥ 90 %` y §7.1 exige «devuelve `[]` si no hay evidencia, nunca inventa». Sobre 38 caracteres sin vocabulario de estilo ni ocasión, ambas a la vez son insatisfacibles | La puerta baja a **70 % global** y se mide además **≥ 90 % sobre el estrato con texto asistido**. Ver la ficha de C09 |
| 2 | **C06 se contradice consigo mismo.** §8.1.1 regla 2 calibra el sintético con lo real «incluida la longitud típica de descripción»; §8.4 exige «~30 % de descripciones pobres». Calibrar sobre 15 caracteres da **100 %** pobres | El reparto de calidad deja de heredarse del real y se **declara**: ~70 % rico, ~20 % escueto, ~10 % sin descripción |

**C06 se parte en dos, y el motivo es de ruta crítica, no de calidad.** C09 se construye y prueba con LLM falso sobre fixtures: necesita *un* corpus, no *el* corpus. Los 900-1.200 sintéticos los necesitan C11, C10 y C24, no C09.

| Change | Alcance | Desbloquea |
|---|---|---|
| **C06a** `add-real-catalog-ingestion-and-text-assist` | Ingesta de los 436; asistencia de redacción; reparto de calidad; JSONL versionado | **C09 y C10** |
| **C06b** `add-synthetic-catalog-augmentation` | Ampliación a ~1.200 totales; colecciones nuevas; LLM+CLI; ingesta INSERT; **sin** familias (C18) | C11, C24 |

Partir no es recortar, así que la lista «nunca se recorta» del §13.4 no lo impide; y Python no tiene la regla de migración única, así que la revisión de Alembic que esto añade es barata.

**Tres decisiones de diseño que salen de la sesión:**

1. **`data_origin` confundía dos ejes independientes** —«¿el producto es real?» y «¿de dónde sale su texto?»— y por eso se rompía al mejorar el corpus. Se separa: `data_origin` sigue significando identidad del producto (SKU, precio y colección son reales y .NET manda sobre ellos) y aparece **`text_provenance`** (`merchant` | `ai_assisted` | `synthetic`). La regla 3 de §8.1.1 se reescribe sobre el eje nuevo.
2. **La unidad del reparto de calidad es la familia de variantes, nunca el producto suelto.** Si dentro de una familia una talla tiene texto rico y otra ninguno, el recuperador puede separarlas por riqueza de texto en vez de por talla — y la desambiguación de variantes son 10 de las 60-70 consultas del golden set, la categoría que §8.4 llama «el caso crítico». Medido: **403 grupos**, de los cuales 23 con variantes (56 productos) y 380 sueltos. Cuidado con leer «familia» como tipo de pieza: hay 37 tipos pero cuatro concentran el 78 %, y sortear por ahí daría *todos* los pendientes ricos y *todos* los colgantes vacíos.
3. **El texto asistido simula un reconocimiento multimodal que no existe y que el diseño excluyó.** §8.1 dice de las fotos «no se usan (el índice visual ya existe y es otro problema)», y se ha verificado que hay **0 fotos y 0 embeddings visuales** en la base. Sin fotos el modelo no puede saber cuántas piedras lleva una joya: expande lo que ya consta y acota por banda de precio lo que no. Esto **entra en §15 como limitación declarada**, no como detalle de implementación.

**Consecuencia sobre el resultado que publica el README.** §15 limitación 1 obliga a publicar la porción real como resultado principal, y §11.2 y C24 aplican ahí el umbral de aceptación. Con el texto real redactado por un LLM, ese número deja de decir lo que decía: la afirmación del proyecto pasa de «funciona sobre un catálogo real de joyería» a «funciona sobre un catálogo realista». Sigue siendo defendible, pero hay que escribirlo. Las métricas de **enriquecimiento** (§11.5, tasa de corrección por campo) sobreviven intactas —miden al extractor, no a la verdad—; las de **recuperación** son las que dejan de hablar del negocio real.

**Puerta que se deja abierta a coste cero.** El corpus original queda archivado (`.xlsx` y volcado `pg_dump` en `data/catalog/real/`, fuera de git). C24 admitirá un segundo `eval_run` sobre él, de modo que el delta «con asistencia − sin asistencia» siga siendo medible más adelante. Es el resultado más fuerte que este proyecto podría enseñar y perderlo era irreversible.

---

### 2026-08-17 — C07, al aplicar: la zona, una reserva para C18 y dos deudas que hereda C12

| Qué decía la ficha | Qué es en realidad | Por qué |
|---|---|---|
| **Zona:** `Domain/`, `Application/`, `API/Controllers/` | **Cinco carpetas:** más `Infrastructure/` (configuración EF y migración) y `Tests/` | Tercera vez que se corrige lo mismo, tras C04 y C08. **Un change 🗄️ siempre toca `Infrastructure/` y `Tests/`**; conviene darlo por supuesto en las tres fichas 🗄️ que quedan (C19, C27, C29) en lugar de volver a anotarlo |
| Nada sobre `design.md` | **C07 lleva `design.md`** | El §7 no se lo asigna, pero hay cinco decisiones con alternativas defendibles y coste asimétrico. Segunda vez que la lista del §7 se queda corta, tras C08 |
| `ProductFamily` (Name, Description) | **Más `Origin`, `ApprovedByUserId` y `ApprovedAt`**, nulables y sin uso en C07 | **C18 no está marcado 🗄️** y el plan cuenta seis migraciones, ninguna suya. Sin esta reserva tendría que abrir una séptima en plena Ola 3, compitiendo por el turno con C19, C27 y C29. Es la misma jugada que C08 hizo para C28, y por el mismo motivo |

**Obligaciones que C07 no puede cerrar y adjudica a C12 por escrito.** Las dos salen de que la pertenencia se declara como lista completa:

1. **Un producto que sale de una familia pierde su fila de miembro**, así que no queda ninguna marca temporal que le diga al feed `?since=` que ese producto debe reindexarse *sin* familia. Su documento conservaría la familia antigua indefinidamente.
2. **Renombrar una familia no toca ninguna fila de miembro**, y el índice denormaliza `family_name`, con lo que C11 se compromete a que el hash cambie.

Ninguna se resuelve dentro de C07: exigiría borrado lógico y una columna más para un mecanismo que el **§6.3 ya diseña en otro sitio** —*«.NET empuja una invalidación cuando se aprueba un perfil o cambia una familia»*—, y ese empujón es de C12. C07 deja preparados los índices sobre `UpdatedAt` de ambas tablas para que el feed pueda unir por familia y no solo por miembro. **C12 debe invalidar los productos que entraron y los que salieron, no solo los miembros actuales.**

**Lo que el apply enseñó y no estaba en ninguna ficha.** El reemplazo declarativo de miembros falla si las altas se declaran añadiéndolas a la colección de navegación de la familia: `BaseEntity` asigna el `Guid` en el constructor, así que EF toma al miembro nuevo por una fila existente y emite un `UPDATE` contra nada. Solo se manifiesta cuando una misma petición borra e inserta a la vez —reordenar variantes, intercambiar dos etiquetas—, nunca cuando solo añade o solo quita. Es un aviso para C18, C19 y C29, que van a mover colecciones hijas por el mismo camino.

---

### 2026-08-16 — C08, al aplicar: la ficha se quedaba corta en dos cosas

| Qué decía la ficha | Qué es en realidad | Por qué |
|---|---|---|
| **Zona:** `Domain/`, `Application/`, `API/Controllers/` | **Seis carpetas:** más `Infrastructure/` (configuración EF y migración), `Tests/` y **`ai-service/`** | Mismo error que la ficha de C04 tuvo que corregir. Un change 🗄️ siempre toca `Infrastructure/`, y este además cruza a Python |
| El contrato de `POST /v1/enrich/products` bastaba tal cual | **C08 lo renegocia** | Sus perfiles propuestos no llevaban `source` (`rule` \| `inferred`). Sin ese campo la decisión 5 —*sensible inferido → revisión; sensible por regla → no*— **no es implementable**, y dos de los cuatro tests `Routing_*` de la propia ficha no tendrían nada que distinguir. Se añaden además `piece_type`, `stone_type`, `size_label`, el desglose de `tags` en `color_tags`/`style_tags`/`occasion_tags` y `prompt_version` |

Renegociar aquí fue barato porque **C08 es el único consumidor que la ruta ha tenido nunca**: romperla no invalidó una sola línea. Hacerlo en C09 habría obligado a construir la entidad y el enrutado sobre una forma que ya se sabía insuficiente. El coste real fueron un snapshot regenerado y dos suites en verde, que es exactamente el mecanismo que C02 montó para este momento.

**Obligación heredada por C09.** El contrato ya declara `source` y `prompt_version`: el pipeline de enriquecimiento debe **producirlos de verdad**, marcando `rule` en la normalización determinista previa (talla por regex) y `inferred` en lo que salga del modelo. Si C09 devolviera todo como `inferred`, la revisión híbrida seguiría compilando y mandaría el catálogo entero a una cola que nadie tiene tiempo de vaciar.

**Consecuencia sobre C28.** No está marcado 🗄️ y el plan cuenta seis migraciones, así que C08 le reserva el almacenamiento de sus dos métricas: `ProposedProfileJson` (propuesta cruda inmutable, de la que sale la tasa de corrección por campo) y `ReviewDurationMs` (que mide el navegador y queda nulo en aprobación masiva). C28 no necesita abrir una séptima migración.

---

### 2026-08-15 — C05, al aplicar: dos lagunas del propio plan

La ficha de C05 se cumplió sin desviaciones, así que no se corrige. Pero implementarla dejó a la vista **dos huecos que no son de ningún change y que, sin registrar aquí, se pierden**:

| Laguna | Estado | Qué se ha hecho |
|---|---|---|
| **`ai.query_log`** aparece en el diseño §7.2 junto a las tablas de evaluación, pero **ninguna ficha la reclama**: las de evaluación son de C24 y esta no es de nadie | Sin adjudicar | C05 **no la crea**, a propósito y con el motivo escrito: no hay regla de migración única en Python, así que una segunda revisión de Alembic es barata, mientras que adivinar hoy sus columnas no lo es. Queda anotada para que no aparezca improvisada dentro de C14 |
| **No existe integración continua para Python.** El repositorio tiene `test-backend.yml` y `test-frontend.yml`; nada ejecuta `uv run pytest` | Sin adjudicar | Condiciona una decisión de C05: los tests de base de datos **se omiten con motivo** cuando Docker no responde, en lugar de fallar. Sin CI, unos rojos permanentes en local solo enseñarían a ignorar el rojo. Si alguien añade el flujo, esa decisión debería revisarse |

Ninguna de las dos bloquea a nadie hoy. Se registran porque el coste de olvidarlas se paga tarde: la primera, cuando C14 necesite registrar consultas y no tenga dónde; la segunda, el día que un cambio rompa la suite de Python y nadie se entere hasta la entrega.

---

### 2026-08-10 — C04, tras la sesión de exploración previa al proposal

Diseñar C04 en detalle movió tres cosas de sitio y añadió obligaciones sobre dos changes posteriores. El detalle completo está en [HU-AIENG-004](../Historias/AI-Eng/HU-AIENG-004.md) y en el ticket del change; aquí queda el resumen y las fichas corregidas.

| Qué cambia | Antes (v3 / specs v2) | Ahora | Por qué |
|---|---|---|---|
| **Quién escribe el evento** | implícito: el frontend envía `ProductSearchEvent` (ficha C16) | el **backend** escribe la mitad de búsqueda desde C15; el cliente solo reporta la selección | Origen, `trace_id`, latencia real y lista realmente devuelta **solo los conoce el servidor**. Es §6.2 y §7.6 aplicados a la telemetría. Efecto buscado: el contrato de C16 —🔴, ola congestionada— se reduce a un `POST` con un campo |
| **Endpoint** | `POST /api/products/search-events` (specs v2 §5.9) | `POST /api/ai/search-events/{id}/selection` | Un evento sin selección y sin resultados no pertenece a ningún producto: anidarlo bajo `/products` miente sobre la propiedad del recurso. `api/ai/*` es el namespace que ya usan C15, C19 y C34 |
| **Enlace venta↔búsqueda** | `ProductSearchEvent.CreatedSaleId` (specs v2 §5.8) | `Sale.SearchEventId`, con `ON DELETE SET NULL` | La atribución la declara el hecho derivado en el mismo `INSERT`, sin llamadas de seguimiento. Con el checkout masivo la diferencia es de N llamadas extra contra N campos opcionales en una petición que ya se envía |
| **Duración** | un campo `SearchDurationMs` (specs v2 §5.8) | `RetrievalMs` + `TotalMs` + `SelectedAt` | El campo original era ambiguo entre latencia de recuperación y tiempo hasta la selección. La diferencia de los dos primeros mide el **coste de la hidratación**, cifra que hoy nadie conoce y que el README querrá defender |
| **Granularidad** | no especificada | una fila por consulta, agrupadas por `SearchSessionId` | Sin agrupar, cada reformulación se contabiliza como un falso «consulta sin resultado» |
| **Búsquedas degradadas** | no contempladas | columna `SearchOrigin` (`Assisted` / `LexicalFallback`) | §6.4 obliga a responder con el buscador léxico si el circuito abre. Sin distinguirlas, una semana de cortacircuitos se lee como «la IA rankea peor». Y da online la comparación v0 vs v3 de §11.2 |
| **Utillaje de migración** | *«test de migración»* en seis fichas, sin más detalle | arnés de dos capas construido en C04 y heredado por C07, C08, C19, C27 y C29 | No existe ningún test de migración en el repositorio. La primera migración paga un coste fijo que las otras cinco no pagan, y debe caer en el change sin dependientes |

**Consecuencia de orden.** Coger C04 antes que C07 contradice la regla 2 (prioridad a la ruta crítica): C07 desbloquea C12 🔴 y C04 no desbloquea nada. Se acepta la inversión **por el coste fijo del arnés**, que conviene pagar fuera de la ruta crítica. Si finalmente se coge C07 primero, el arnés viaja con C07 y C04 lo hereda.

---

## 1. Cómo se trabaja

Cada entrada es **un change OpenSpec completo**, ejecutable de principio a fin en **una sesión de 2-3 horas**:

```text
/opsx:propose (proposal.md · design.md · tasks.md · specs/<capability>/spec.md)
  → /opsx:apply  (código + tests)
  → /opsx:verify (build + tests verdes + revisión de alcance)
  → /opsx:archive (openspec/changes/archive/YYYY-MM-DD-<change-id>/)
```

### Reglas de orden *(reescritas el 2026-08-31: equipo de uno, prórroga abierta)*

1. **Se coge el siguiente change desbloqueado**, sea Python o .NET. No hay dueño por zona.
2. **Prioridad al desbloqueo, no al calendario.** Entre los changes libres se coge el que **más aristas abre en el grafo del §4**, no el que antes vence. Un 🟢 que tapona a un 🔴 va primero: el caso vivo es C20, marcado 🟢, que es lo único que separa a C21 de arrancar y C21 bloquea a la vez a C24 y a C30.
3. **Una sola migración EF Core activa a la vez** (marcados 🗄️). Se mergea antes de abrir otra. Ya no es coordinación entre personas sino disciplina de rama: dos migraciones abiertas colisionan igual aunque las escriba la misma mano.
4. **No se abren a la vez dos changes de la misma zona.** La tabla de *pares que no deben ejecutarse en paralelo* del §5 sigue vigente, ahora leída como changes consecutivos y no como desarrolladores simultáneos.
5. **Si un change se desborda de la sesión, se parte** y se entrega primero la mitad que desbloquea el grafo.
6. **C24 (golden set) se etiqueta una vez.** El doble etiquetado y la conciliación no existen con un solo anotador; se conserva el *pooling* y se declara la ausencia de acuerdo entre anotadores como limitación del README.

### Definition of Done común

- [ ] Artefactos OpenSpec creados y `openspec validate` en verde
- [ ] Código aplicado, `dotnet build` / `uv run pytest` / `npm run build` sin errores
- [ ] **Tests unitarios nuevos, verdes**
- [ ] Tests existentes sin regresión
- [ ] Documentación afectada actualizada
- [ ] Change archivado el mismo día

### Reglas transversales de testing

- **Ninguna llamada real a un LLM ni a embeddings en tests unitarios.** Fakes inyectados + fixtures en `ai-service/tests/fixtures/`.
- PostgreSQL: Testcontainers (.NET) o contenedor efímero con pgvector (Python).
- Generadores: tests de **propiedades** (invariantes), no de valores concretos.
- Nomenclatura: .NET `Method_Scenario_ExpectedResult` · frontend `should [behavior] when [condition]` · Python `test_<unidad>_<escenario>_<esperado>`.

### Leyenda

🔴 ruta crítica · 🟢 fuera de la ruta crítica · 🗄️ incluye migración EF Core · ⛔ **anulado** *(no se implementa; la ficha se conserva como registro)*

Dos marcas de la v3 quedaron sin objeto el 2026-08-31 y ya no se usan: **👥** *(«se hace entre los dos»)* y **⏳** *(«pendiente de acuerdo con el compañero»)*. Donde aparecen en fichas antiguas, léanse como trabajo de una sola persona y como decisión propia.

---

## 2. Tabla maestra

| # | Change ID | Zona | Prereq. | Ruta | Origen |
|---|---|---|---|---|---|
| **C01** | `init-ai-service-skeleton` | Python, infra | — | 🔴 | — |
| **C02** | `add-ai-service-contracts-and-auth` | Python | C01 | 🔴 | — |
| **C03** | `add-dotnet-ai-gateway-client` | .NET | C02 | 🔴 | — |
| **C04** | `add-product-search-event-tracking` | .NET 🗄️ | — | 🟢 | specs v2 §5.8 |
| **C05** | `add-pgvector-schema-foundation` | Python, infra | C01 | 🔴 | — |
| **C06a** | `add-real-catalog-ingestion-and-text-assist` | scripts/catalog/ | C01 | 🔴 | **rev. 17 ago**, **22 ago · archivado** |
| **C06b** | `add-synthetic-catalog-augmentation` | jbg_ai.data (CLI) | C06a | 🟢 | **23 ago · archivado** |
| **C07** | `add-product-family-entity` | .NET 🗄️ | — | 🟢 | **rev. dec. 2** |
| **C08** | `add-product-ai-profile-entity` | .NET 🗄️ | C03 | 🟢 | rev. dec. 3, 5 |
| **C09** | `add-catalog-enrichment-pipeline` | Python | C06a | 🔴 | rev. dec. 3, 5, **17 ago**, **23 ago · archivado** |
| **C10** | `add-synthetic-world-simulator` | Python | C06a | 🟢 | rev. dec. 8 |
| **C11** | `add-source-text-and-embedding-client` | Python | C05, C09 | 🟢 | **25 ago · archivado** |
| **C12** | `add-dotnet-index-feed-endpoints` | .NET | C07, C08 | 🔴 | **rev. dec. 10**, **26 ago · archivado** |
| **C13** | `add-product-document-indexer` | Python | C11, C12 | 🔴 | **26 ago · archivado** |
| **C14** | `add-vector-retrieval-endpoint` | Python | C13 | 🔴 | **27 ago · archivado** |
| **C15** | `add-dotnet-ai-search-endpoint` | .NET | C03, C14 | 🔴 | **rev. dec. 11**, **28 ago · archivado** |
| **C16** | `add-frontend-assisted-search-panel` | Frontend + .NET | C15 | 🔴 | **rev. 29 ago · archivado** |
| **C17** | `add-ai-service-deployment` | Infra + Python + .NET + FE | C15 | 🔴 | **rev. 29 ago** |
| **C18a** | `add-family-suggestion-and-approval` | Python + .NET | C07, C13 | 🟢 | **rev. dec. 2**, **31 ago · archivado** |
| **C18b** | `add-family-review-ui-and-orphan-alert` | Python + .NET 🗄️ + FE | C18a | 🟢 | **rev. dec. 2**, **partido el 31 ago**, **ficha reescrita el 31 ago**, **aplicado el 1 sep** *(3 migraciones; 62/62 tareas; pendiente de archivar)* |
| ~~**C19**~~ | ~~`add-demand-signal-service`~~ | .NET 🗄️ | C10 | ⛔ | **rev. dec. 6** · **anulado el 31 ago** |
| **C20** | `add-synonym-dictionary` | Python | C14 | 🟢 | **rev. dec. 4** · *tapona a C21: se coge primero* · **ficha reescrita el 1 sep** |
| **C21** | `add-hybrid-search-rrf` | Python | C14, C20 | 🟢 | **archivado el 2 sep** · *tres puntos de la ficha refutados con medición* |
| **FIX1** | `fix-enrichment-vocabulary-gaps` | Python + FE | C21 | 🟢 | **archivado el 5 sep** · *dos puntos de la ficha refutados con medición: la población era de 22 y no de 11, y su criterio de extremo a extremo ya se cumplía antes* · *fuera de la numeración C* |
| **C22** | `add-pos-projection-soft-prefilter` | Python + .NET | C10, C12, C14 | 🟢 | **archivado el 5 sep** · *tres puntos de la ficha refutados con medición; entra además el reloj inyectado (FIX2)* |
| **C23** | `add-knowledge-corpus-and-indexer` | Python | C11 | 🟢 | **archivado el 6 sep** · *zona, alcance y conflicto de zona de la ficha refutados por la implementación* |
| **C24** | `add-eval-harness-golden-set-and-baselines` | Python | C14, C21 | ✅ | **archivado el 2026-09-11** · dec. 12 respondida: la vectorial bate a la léxica · etiquetado simple |
| **C25** | `recalibrate-ranking-and-abstention` | Python | C21, C22, C24 | ✅ | **archivado el 2026-09-12** · renombrado desde `add-business-signals-ranking`; **3 puntos de la ficha retirados por medición** y un defecto de C21 corregido: la fusión concatenaba |
| **C25bis** | `clean-plain-fusion` | Python | C25 | ✅ | **implementado el 2026-09-12**, 45/45 · *retiró la fusión plana y los tres pesos por lista; las 315 filas por consulta, idénticas* |
| **C26** | `add-substitutes-retrieval` | Python | C22, C25 | ✅ | specs v2 §6.3.2 · **archivado el 2026-09-12**, 62/62 · *nace la capability `substitutes-retrieval` con diez requisitos y cae el último 501 cerrable del contrato* |
| ~~**C27**~~ | ~~`add-complementary-recommendations`~~ | ~~Python + .NET 🗄️~~ | C10, C25 | ⛔ | **rev. dec. 8** · **corte nº 1 disparado el 2026-09-12** con cinco mediciones (§0) |
| **C28** | `add-profile-review-ui-and-metrics` | Frontend + .NET | C08 | ✅ **archivado 2026-09-13** | **rev. dec. 5** · *lo pide el checklist §16* · entrega 20,9 % ponderado y 32,1 s |
| ~~**C29**~~ | ~~`add-inventory-recommendation-entity`~~ | .NET 🗄️ | C19 | ⛔ | **rev. dec. 6** · **anulado el 31 ago** |
| **C30a** | `add-assist-structure-and-rule-warnings` | Python | C07, C21, C23 | ✅ **archivado 2026-09-13** | **rev. dec. 4** · **partido el 13 sep**; renombrado desde `add-assist-generation-with-rule-warnings` · *movió el contrato congelado: sólo los cinco esquemas de assist* |
| **C30b** | `add-assist-pitch-generation` | Python | C30a | ✅ **archivado 2026-09-14** | **nace el 13 sep** al partir C30 · *la única mitad que llama a un LLM* · **implementado el 14 sep**: la puerta numérica rechaza **0 de 120** y el *timeout* sube a 4 s con la cifra delante |
| **C31** | `add-guardrails-and-intent-router` | Python | C30b | ✅ **archivado 2026-09-16** | *prereq afinado el 13 sep: su validación de salida necesita una salida* · **el veto tumbó la primera configuración** y lo que lo cerró fue el **modelo**, no el prompt: `gpt-4o-mini` silencia 3 contestables, `gpt-4o` con el mismo prompt silencia **0** y acierta **48/48** en `catalog` |
| **C32a** | `add-sales-assistant-tool-registry` | Python | C30b, C31 | ✅ **archivado 2026-09-20** | — · **nace el 20 sep** al partir C32 (§0) · *la mitad sin proveedor: seis tools, registro, esquemas de function calling e invariante de solo-lectura por introspección* · **resuelve la decisión abierta del §6.1 del diseño difiriéndola**: `consultar_disponibilidad` se sirve desde `ai.pos_projection` con **etiqueta cualitativa**, porque `QTY_BUCKETS` son dígitos y el bucket crudo en el contexto del modelo es una cifra de stock |
| **C32b** | `add-sales-assistant-agent-loop` | Python | **C32a** | ✅ **archivado 2026-09-21** | — · **hereda de C31 el patrón del techo, no la cifra**: cinco vueltas no caben en 3, y el techo pasa a **8 por petición** (1 enrutador + ≤5 vueltas + ≤2 argumentario), más el de tokens que nadie había escrito. **Ruta propia `POST /v1/assist/agent`**, porque el peor caso son ~15-20 s contra los 5 s que el §6.4 declara para `/v1/assist`. Su tool `pedir_aclaracion` **no es** la `clarification_question` de C31: elige **eje** de un enum cerrado y el texto lo sigue escribiendo el código |
| ~~**C33**~~ | ~~`add-pos-sales-profile`~~ | .NET + Python | ~~C19~~ → C08, C12 | ⛔ | **rev. dec. 7** · **anulado el 31 ago** · *rescatable suelto* |
| **C34** | `add-dotnet-assist-and-recommendation-endpoints` | .NET | C15, C26, **C30a** *(C27 cortado el 12 sep)* | ✅ **archivado 2026-09-22** | — · *prereq afinado el 13 sep: depende de la **forma**, no de la prosa — es la razón del corte* · **gana los dos avisos de stock y `question`** · **y de C31** ~~la ruta de la consulta libre~~ *(no entra: 21 sep)* **tres códigos nuevos de `warnings[]`** (`query_out_of_domain`, `query_not_in_catalogue`, `knowledge_not_covered`) y el campo `clarification_question`, que deja de ser nulo. **`intent` gana tres valores**: un consumidor que compare contra `unclassified` verá `in_domain`, `out_of_domain` y `not_in_catalogue`. ~~**El presupuesto de 5 s se hereda sin resolver**~~ · **explorado el 21 sep** ([informe](informes/c34-exploration-decisions.md)): **sólo las dos rutas del card**, porque en M1 y en el agente los marcadores no dicen de qué pieza son; `POST` con `question` en el cuerpo; el presupuesto pasa a **10 s** porque 5 s cortan el **7,5 %**; y la zona gana `deploy/demo/` para encender la generación en la demo · **implementado el 21 sep, sin archivar** ([informe](informes/c34-implementation-measurements.md)): latencia medida de extremo a extremo —p95 7,1 s, máx 7,9 s, el presupuesto se queda en 10 s— y **demo desplegada y verificada el 22 sep**: argumentario generado con «250,00 €» y «5» resueltos en el texto, 269,9 MiB de 512 en `jbg-demo-ai`, y la cuota del proveedor descartada como restricción |
| ~~**C35**~~ | ~~`add-inventory-agent-proposals`~~ | Python | C26, C29, C32, C33 | ⛔ | **rev. dec. 6** · **anulado el 31 ago** |
| **C36** | `add-frontend-assist-card-and-family-disambiguation` | Frontend | C16, C34 | ✅ **archivado 2026-09-24** | — · **hereda de C31 tres filas más en la tabla de copy** —los dos rechazos, que son **dos textos distintos** y no uno, más «el corpus no cubre esta pregunta»— y **una excepción razonada**: `clarification_question` viaja **como prosa ya resuelta** y no como código, porque el contrato la tipa así; el frontend la pinta tal cual. **Pintar el rechazo igual que `abstained` borraría la distinción** que las dos cifras publicadas existen para sostener |
| ~~**C37**~~ | ~~`add-frontend-inventory-review-and-print`~~ | Frontend | C29, C35 | ⛔ | **rev. dec. 6** · **anulado el 31 ago** |
| ~~**C38**~~ | ~~`add-generation-and-agent-evals`~~ | ~~Python + .NET~~ | C24, **C30b**, **C32b**, C34, **C42** | ⛔ | **RETIRADO ENTERO el 2026-09-27** (§0 · *C38 se retira entero*), un día después de perder RAGAS. Lo deciden dos mediciones sobre artefactos committed: **17 de 20** escenarios cumplen su expectativa en la pasada de C42 con `v6`, y el **ruido entre pasadas es 2 de 20** —el tercer desacuerdo es una corrección documentada del escenario C05—. Los datos de la tabla del agente **ya existen y están corridos dos veces contra el proveedor**; el validador .NET resultó ser **un espejo** de la regla que Python ya aplica al mismo texto, con cifra esperada cero; y los adversarios eran la única pieza que arrancaba de verdad en cero. Sobreviven **tres tareas dentro de C39**. Se pasa por encima del §6, que protegía «el validador de C38», y queda escrito. Lo que sigue es el registro previo · ~~**Reducido a su mínima expresión el 2026-09-26, y RAGAS sale entero**~~ (§0 · *C38 se reduce y RAGAS se retira*). Lo que queda: **validador determinista consolidado + su equivalente .NET, escenarios de venta puntuados y casos adversarios**. Se dispara el corte que el propio change llevaba **pre-escrito** —*«orden obligatorio si hay que partirlo: validador → escenarios de venta → adversarios → RAGAS; RAGAS es lo primero que se cae»*—, y se dispara por valor marginal y no por plazo: *«evals reales»* ya está demostrado por C24, C25, C28, C30b, C31, C32b y C40, mientras que RAGAS arrastra dependencia pesada, juez LLM, cuota y el MITM de esta máquina. La *alucinación con coartada* **pasa a limitación declarada con su vía de cierre**, que es lo que el §16 premia · **gana a C42 de prerrequisito**: sube la tarea del agente a `assist/v5`, así que unas cifras de generación del agente tomadas antes describirían un prompt sustituido · *sin escenarios de inventario* · **la excepción de persistencia del arnés la declara C30b** · **de C31 hereda el conjunto de enrutado ya cableado** (119 casos, seis clases, carga que falla si los recuentos no cuadran) y **una cifra que contradice lo esperado**: la puerta numérica de la consulta libre rechaza **0 por cifras** con una lista blanca de ~13 numerales, así que el riesgo que quedaba abierto ahí **no era el numérico** sino `dangling_citation`. Los casos adversarios y de inyección sistemáticos siguen siendo suyos · **y de C32b hereda cinco cosas escritas**: (1) el **golden set está intacto y comprobado** — dos tests cruzan sus 72 consultas contra los dos conjuntos del agente en las dos direcciones, así que puede arbitrar la ablación sin reservas; (2) `evals/agent/calibration.yaml` está declarado **`calibration-only`** y contra él se iteraron DOS prompts, así que C38 escribe los suyos aparte y comprueba el no solape, que es la razón de que la etiqueta exista; (3) la ablación ya tiene una de sus dos filas medida — **×3,0 el agente contra el pipeline, 0,0274 frente a ~0,0092 USD/petición, cada etapa tarifada con su propio modelo** *(corregido el 21 sep: la primera cifra, ×7,6, tarifaba el clasificador con un coste sin fuente)* — y la fila del brazo barato **descartada por comportamiento y no por precio**; (4) el hallazgo abierto que C38 tiene que medir sobre el golden set: **se retira el 13,1 % de los argumentarios del agente en `gpt-4o` —9,5 puntos por `dangling_citation`— contra el 2,2 % de la ruta determinista**, seis veces más, con `assist/v4` ya mejorado una vez y sin cerrar; y (5) **dos cosas que la verificación independiente le deja por medir**: si el argumento menciona disponibilidad —nada lo impide, y el arnés ya lo cuenta por fila (`pitch_availability_terms`)— y la calidad del argumento tras un pivote, cuyo *payload* cambió (la pieza abandonada ya no llega como coincidencia) sin que la pasada lo midiera; `agent_sweep --rescore` recalcula cualquier artefacto sin proveedor. Y un aviso operativo: la cuota de **tokens por minuto de la organización** fija el reloj de cualquier pasada — 204 peticiones costaron 3,4 h a 25.000 TPM |
| **C39a** | `redeploy-and-audit-demo-environment` | Deploy + Python + .NET | todos los vivos | ✅ **archivado 2026-09-27** | **nace el 2026-09-27 al partir C39** (§0). Redespliegue de la demo en AWS **verificado y accesible desde internet**, con la **auditoría completa de `compose.demo.yaml` contra los ajustes que declaran los tres servicios**. Cuatro huecos ya medidos en la exploración: `AiAgentAssist__EnabledByDefault` **ausente** y `bool` sin inicializador, o sea el panel del agente de C42 **no se sirve**; `JPV_AGENT_LLM_API_KEY` y `JPV_ROUTER_LLM_API_KEY` ausentes; y el **corpus de conocimiento sigue sin viajar en la imagen** —tarea diferida de C34, sorteada a mano—, con lo que M2 retira el argumentario y M3 responde `knowledge_not_covered`. **Va antes de C39b** y el motivo no es de tamaño: no se documenta un recorrido que no se ha recorrido |
| **C39a-bis** | `verify-demo-redeployment` | Docs | **C39a desplegado** | ✅ **archivado 2026-09-27** | **nace el 2026-09-27, durante el apply de C39a**, y por una razón de orden: la verificación exigía un entorno que sólo existe **al mergear C39a a `demo`**. Recorre el entorno resultante —siete condiciones, tres credenciales propias, la predicción de la proyección, y el recorrido del evaluador con los cuatro usuarios sobre las cuatro superficies de IA— y **toca sólo ficheros del `paths-ignore` de `deploy-demo.yml`**, así que mergearlo no dispara despliegue. Lleva **una adición a `demo-deployment`**: el entorno debe declarar sus cuentas de demostración y **qué ejercita cada una**, porque las tres tiendas tienen surtidos deliberadamente distintos y hay comportamientos alcanzables desde una sola. **No toca código por diseño**: si el recorrido destapa un defecto, se anota o se abre otro change |
| **C39b** | `finalize-pf-readme-and-evidence` | Docs | **C39a-bis** | 🔴 | **queda con el alcance original de C39** menos el despliegue, más tres cosas que la sesión del 27 sep añade: la **frontera contable** entre lo que ya existía y lo que es del PF (32 changes del MVP antes del 2026-08-03 · 41 del PF después, verificable contra `openspec/changes/archive/`), el **resumen de fases** incluidos los cuatro changes que nacieron de comprobaciones manuales y no de ninguna ola, y la **taxonomía explícita de métodos de búsqueda** —léxico, CAG, vectorial, fusión RRF por rama, señales, M1/M2/M3 y agéntico—, cada fila con su cifra ya medida. Hereda de C38 sus **tres tareas supervivientes** |
| **C40** | `add-frontend-free-query-panel` | Python + .NET + Frontend | C16, C31, C34, **C36** | 🔴 | **nace el 24 sep**, durante la comprobación en demo de C36 (tarea 8.5) y **no estaba en el plan**: la sesión destapó que el panel de búsqueda asistida llevaba todo el proyecto sirviendo por su ruta degradada, con los filtros **descartándose en silencio**. Explorado en dos pasadas ([informe](informes/c40-exploration-decisions.md) · [tabla de estados](informes/c40-m1-panel-states.md)): **once hallazgos, diecisiete decisiones y una regla transversal de completitud**. Saca a pantalla **M1**, la pregunta libre sin pieza, convirtiendo el panel de C16 en su superficie, y **cierra tres limitaciones del §15** —la 12, la 13 y la 3 de C34—. **Mueve `openapi.json`** (`filters` en `AssistRequest`, adición pura) y **toca `retrieval-abstention`, spec viva con tres consumidores**. **Va antes de C38**: sube el prompt a `assist/v5` y mueve la fase de la abstención, así que unas cifras tomadas antes describirían un prompt sustituido. **El hallazgo que gobierna su línea de corte:** `AiGatewayClient` **rechaza M1 hoy por construcción** —`PitchPlaceholderResolver` retira el argumentario siempre que no hay ancla, y `v3` ordena escribir los marcadores de precio y stock también en las tareas de consulta libre, medido en **147 de 213**—, así que sin el tramo 2 completo entregaría **un panel asistido sin prosa** |
| **C41** | `add-pos-projection-scheduled-drain` | **ai-service** (+ despliegue y un retoque .NET/Frontend) *(corregido el 26 sep: decía «.NET + Frontend»)* | **C22**, **C17** *(corregido el 26 sep: decía C40, y la lectura previa de C40 deja de usarse)* | 🔴 | **nace el 25 sep**, durante las pruebas manuales posteriores al cierre de C40, y **no estaba en el plan**. Al levantar el entorno **ninguna de las once tiendas activas tenía la proyección fresca**: el *checkpoint* de `pos-availability` venía del 5 de septiembre —veinte días contra un umbral de 3 600 s— y hubo que drenarla a mano para que las pruebas midieran el sistema y no su desconfiguración. **Es la tercera vez** *(corregido el 26 sep: esta fila decía «la segunda»)*: el §8 del informe de C40 declara la misma causa con 19,7 días —y su arreglo **se aplicó a la columna equivocada**, ver la ficha—, y antes **C34 encontró la proyección vacía en la demo**, que es otro modo de fallo (`count_scope = 0` → **503 en toda recuperación**) y sigue abierto en `DEFERRED_TASKS.md`. Eso es lo que lo convierte en ficha: **el planificador existe y vive en prosa** —`ai-service/README.md` lleva desde C22 una receta de cron que empieza por `cd /srv/jbg-ai`, una ruta de host, y `jbg-ai` es un contenedor—, así que `sync-pos` es sólo CLI y alguien tiene que acordarse. **No es una fuga** —la frontera es `Carried()` en .NET y ningún operario ve una pieza que su tienda no lleva—: lo que causa es que **la página llegue corta**, que es exactamente la avería que C22 midió (ocho de once tiendas por debajo de una página en seis de cada veinte búsquedas, peor caso **un solo producto**). Núcleo *(reescrito el 26 sep)*: una tarea de `lifespan` en **`jbg-ai`** —no un `BackgroundService` de .NET, que sería **una segunda implementación del protocolo del keyset** sobre la misma fila de checkpoint— que drena **al arrancar y cada 600 s**, con `pg_try_advisory_lock` **dentro del drenaje** para que cubra al CLI, porque `ai.sync_checkpoint` es **una fila por feed** y dos drenajes entrelazados **se saltan filas en silencio**. Tramo aditivo: la **edad en `GET /health`** —no en `GET /api/ai/search/availability`, que tiene un `MUST` de spec viva prohibiéndole llamar a la IA— más el **quinto fallo de `verify.sh`** que caza la proyección vacía. **Cortado en el diseño:** el drenaje manual, **también el del administrador** — el argumento que mata el botón del operario mata el suyo |
| **C42** | `add-frontend-agent-panel` | Python + .NET + Frontend | C32b, C34, C36, **C40** | ✅ **archivado 2026-09-27** | **Nace el 2026-09-26**, al valorar la cola pendiente del PF, y **no estaba en el plan**. Explorado contra el código en [informe](informes/c42-exploration-decisions.md): **ocho hallazgos y doce decisiones**. Da superficie al **único de los cinco pilares del PF que no la tiene** —CAG, RAG, **agentes**, evaluación, despliegue—: `POST /v1/assist/agent` está entregado y medido desde C32b y **nadie lo llama**, así que no puede aparecer ni en la URL pública ni en el vídeo. **El hallazgo que gobierna su línea de corte es una regresión latente que C40 introdujo sin tocar el agente**: la tarea del agente vive en `assist/v4`, cuyo *Sistema* ordena escribir `{{price}}` y `{{stock}}` **siempre**; su payload es un `FreeQueryPayload` con `is_anchored = False`; y C40 metió `placeholder_in_free_query` en `HARD_VIOLATION_CAUSES`. Los tres eslabones son correctos por separado y juntos **retiran el argumentario del agente por construcción**. Ejecuta además la política de *timeout* y circuito que `DEFERRED_TASKS.md` dejó **diseñada y no hecha** desde C32b, y **el agente no se sirve por defecto**: ruta propia y demostración de ablación, porque su única cifra comparativa hoy dice ×3,0 de coste y 13,1 % de retirada contra 2,2 % · **Archivado el 2026-09-27 con 75/75 tareas y trece refutaciones medidas**, de las que cuatro gobiernan. **El orden de ejecución no fue el del ticket**: el v1 pedía medir antes de la primera tarea y eso **no era ejecutable**, porque el arnés no contaba marcadores ni registraba la antigüedad de la proyección — de ahí un tramo 0 de instrumentos antes de cualquier tarea funcional, que es lo que impide que una pasada más larga que el techo de 3.600 s se lea como fresca, la contaminación que ya estropeó sin arreglo parte de las cifras de recuperación de C32b. **La caída del argumentario retirado del 13,1 % al 1,2 % NO es atribuible a `assist/v6`** y el informe nombra los confundidores: era lo esperado, porque la frase que ordena escribir marcadores es idéntica palabra por palabra en `v3` y `v4` y C40 ya había medido ahí 3 de 90 — el arreglo del prompt es real y **su urgencia era pequeña**, tal como el propio ticket anticipaba. **Las piezas por respuesta siguen saturando en `MAX_AGENT_PIECES`**, así que el tope sigue mordiendo. **La tabla de herramientas del informe de exploración mezcla los dos arms**: 115 de las 125 invocaciones de `buscar_sustitutos` pertenecen al arm descartado, así que la cifra que justificaba rotular la procedencia era correcta en la conclusión y no en la magnitud. Y **nada ejercitaba la ruta del agente sobre HTTP**: el contenedor servía código anterior al change, lo que sólo apareció al montar la comprobación manual. El contrato congelado se movió **por adición pura** (`origin` en subclase, sin ensanchar `AssistGroup`) y el fixture pasó a `openapi-c42-baseline.json`; `SearchOrigin` gana un quinto valor **sin migración**; la entrada de C32b en `DEFERRED_TASKS.md` se cierra **por refutación y no por ejecución**, con la aritmética escrita —~13.000 tokens contra 25.000 TPM es una petición por minuto, así que 204 peticiones cuestan 2 h 44 min—. **La comprobación manual encontró dos cosas que ningún test vio**: la tira de estado afirmaba un motivo de parada cuando la pasarela no había contestado, ya corregido; y **el pivote es inalcanzable si el operario nombra la pieza por su nombre**, porque `buscar_catalogo` no devuelve el nombre del producto — establecido con un experimento HTTP (por SKU pivota, por nombre no), **fuera del alcance de C42** y abierto en `DEFERRED_TASKS.md`. Informe [`c42-implementation-measurements.md`](informes/c42-implementation-measurements.md) y guion de comprobación manual [`c42-manual-check-runbook.md`](informes/c42-manual-check-runbook.md) |
| **C43** | `add-shop-activity-projection` | **ai-service** + .NET *(feed)* + despliegue | **C41**, **C39a-bis** | ✅ **archivado 2026-09-27** | **Nace el 2026-09-27, del hallazgo principal de C39a-bis, y no estaba en ninguna ola**: es el quinto change del proyecto salido de una comprobación manual. El despliegue `36322635852` **falló con el entorno sano** porque la quinta condición de `verify.sh` contaba puntos de venta sin surtido **sin preguntar si la tienda está activa**, y `HT-ARTRUTX` lleva cerrada a propósito desde C10; el falso positivo llegaba además en rojo a la tarjeta del administrador, así que arreglar sólo el guión no bastaba. **El arreglo no cabía donde parecía**: el rol `jbg_ai` recibe `permission denied for table PointOfSales`, de modo que la decisión D9 / Q-5 de C41 estaba **impuesta por los permisos**. Vía B2: `ai.pos_shop` en el esquema `ai`, poblada por un *feed* nuevo sin cursor —una columna en `ai.pos_projection` habría nacido rancia para siempre, porque el *feed* de disponibilidad es incremental por *keyset* sobre el *watermark* de inventario y un cambio de estado de tienda no mueve ninguna fila—. Lleva con él el **segundo defecto de la misma familia**, que es su requisito previo: la espera acotada al drenaje en `verify.sh`. Cierra **dos** de las cuatro fichas diferidas de C39a-bis y hace la mitad barata de una tercera (`failed_pages` por *feed*: las 66 filas de `catalog` dejan de ser invisibles). **Sin migración de EF Core, sin ruta bajo `/v1`, sin mover `openapi.json` y sin tocar el frontend ni el *feed* de disponibilidad.** La confirmación de extremo a extremo **es el despliegue** y la recoge C39b |

**Origen** indica de dónde sale el change: en **negrita**, los que existen por la revisión del compañero.

**⛔ Anulados el 2026-08-31 (5):** C19, C29, C33, C35 y C37 — la rama del agente de inventario. Motivo y consecuencias en el §0. Las fichas se conservan como registro y llevan el sello en el sitio.

**⛔ Cortado el 2026-09-12 (1):** **C27**, complementarios — el corte nº 1 del §6, disparado **con medición y no por juicio de plazo**. Sus dos señales están vacías (co-ocurrencia: 98,6 % de los pares vistos **una sola vez** y ninguno tres veces, sobre un generador que **diversifica las cestas a propósito**; etiquetas de color/estilo: **1 de 404** productos reales con estilo) y el proyecto nunca le reservó categoría en el golden set. Ficha conservada con el sello y la condición de reactivación; detalle en el §0 y en [`c27-cut-measurements.md`](informes/c27-cut-measurements.md).

> **Recuento puesto al día el 2026-09-27, dos veces el mismo día.** Se archiva **C42**, se **retira C38
> entero**, **C39 se parte en C39a y C39b** y, al implementar C39a, **éste se parte a su vez en C39a y
> C39a-bis** (§0). Pendientes: **3 — C39a, C39a-bis y C39b, en ese orden**, y el orden lo fija el
> despliegue: C39a lo dispara al mergearse a `demo`, C39a-bis lo verifica sin volver a dispararlo, y C39b
> documenta lo verificado.
>
> **Puesto al día por tercera vez ese mismo día:** C39a queda **archivado**, su merge a `demo`
> **desplegó de verdad** (ejecución `36322635852`), y **C39a-bis queda archivado** sobre el entorno
> resultante, con su delta sincronizada —`demo-deployment` de **13 a 14** requisitos—. Pendiente
> **1 — C39b**. El despliegue figura en `failure` por un **falso positivo** de la quinta condición de
> `verify.sh`, no por el estado del entorno.
>
> **Puesto al día por cuarta vez ese mismo día — nace C43, y el falso positivo deja de ser una
> nota al pie.** La entrada anterior dice que el despliegue figura en `failure` «por un falso
> positivo de la quinta condición de `verify.sh`, no por el estado del entorno». **C43**
> (`add-shop-activity-projection`) es el change que lo arregla, y arregla con él el segundo
> defecto de la misma familia —la rancidez que el despliegue registraba ya curada—, porque el
> segundo es **requisito previo** del primero: `alembic upgrade head` corre a mitad del
> despliegue, así que la tabla nueva nace vacía con el contenedor de IA arrancado, y sin la
> espera la quinta condición sondearía antes de que el drenaje la llenase.
>
> Entra en **EP14** —modifica `pos-projection`, como C41— y **no estaba en ninguna ola**: es el
> quinto change del proyecto nacido de una comprobación manual, tras C40, C41, C42 y `C40_FIX`.
> Modifica cuatro capabilities: `index-feed` (una adición, el *feed* de tiendas), `pos-projection`
> (dos adiciones y una modificación), `ai-service-runtime` y `demo-deployment`. Reproducido contra
> la base desplegada: `12|11|1` sin filtro de actividad frente a `11|0` con él. Pendiente sigue
> siendo **1 — C39b**, que recoge la confirmación de extremo a extremo: la quinta condición sólo
> da su veredicto real en un despliegue, y ése ocurre al mergear a `demo` **después** de archivar
> C43. **No se abre un C43-bis.**
>
> **La frase de abajo es del primer recuento del día** y decía «2 pendientes: C39a y C39b». Contra `openspec/changes/archive/`, que es la única base fiable: **41
> fichas del Proyecto Final archivadas** —de 74 archivadas en total; las otras 32 son del MVP, todas
> anteriores al 2026-08-03—, **1 retirada** —C38, que se suma a los cinco anulados de la rama de C19 y
> al cortado C27— y **2 pendientes: C39a y C39b, en ese orden**. La frase siguiente es el recuento
> anterior y se conserva como registro.

**Vivos: 42** (40 numerados más `FIX1` y `C25bis`) *(C32 partido en **C32a** y **C32b** el 2026-09-20, §0; **C40 añadido el 2026-09-24**, nacido durante la comprobación en demo de C36; **C41 añadido el 2026-09-25**, nacido durante las pruebas manuales posteriores al cierre de C40 — **C42 añadido el 2026-09-26**, nacido al valorar la cola pendiente del PF — ninguno de los tres previsto en ninguna ola)*. Archivados **40** (C01–C18b, C20, C21, C22, C23, C24, C25, `FIX1`, `C25bis`, **C26**, **C28**, **C30a**, **C30b**, **C31**, **C32a**, **C32b**, **C34**, **C36**, **C40**, **C40_FIX** y **C41**). Pendientes **3**: **C42**, C38 y C39 — **en ese orden**, y la cadena de prompts es la que lo fija: C40 subió a `assist/v5` y movió la fase de la abstención, **C42 sube la tarea del agente a esa misma versión**, y sólo entonces las cifras de generación de C38 describen el prompt que se sirve. *(Recuento puesto al día el 2026-09-26, al rebasar C42 sobre `ai-eng` tras archivar C41: la frase anterior arrastraba «Pendientes 3: C38, C39 y C41» y era de antes de su archivo — el commit que lo archivó sincronizó las specs y no tocó este recuento, exactamente el mismo desfase que ya se corrigió al archivar C40. Contado contra `openspec/changes/archive/`, que es la única base fiable: **40 fichas del Proyecto Final archivadas** —las 41 posteriores al 2026-08-03 menos `barcode-qr-scanning`, que es del MVP—, más las 3 pendientes, dan las 42 vivas más `C40_FIX`, que está archivado y fuera de la numeración.)* *(Recuento puesto al día el 2026-09-26, al archivar C40_FIX: entra en las archivadas y **no** en las fichas numeradas, igual que `FIX1` y `C25bis`, porque corrige a C40 en vez de salir de la descomposición original.)* *(Recuento puesto al día el 2026-09-25, al archivar C40: la frase anterior arrastraba «37 · 3 con C40 pendiente» y era de antes de su archivo.)* El orden que ataba C40 antes de C38 **ya está cumplido**: C40 subió el prompt a `assist/v5` y movió la fase de la abstención, así que las cifras de C38 se tomarán sobre el prompt vigente. **C41 no compitió con ninguno de los dos** —no tocaba prompt, ni fase, ni contrato congelado— y se archivó el 2026-09-26. *(Recuento puesto al día el 2026-09-24, al archivar C36: arrastraba el 35 · 4 desde el archivo de C32b, porque ni C34 ni C36 lo movieron en su momento. Contado contra `openspec/changes/archive/`, que es la única base fiable.)* **C23 se archivó el 2026-09-06** y su corte pre-autorizado —bajar a 15 documentos— se refutó por su propia unidad de medida: el diseño fija el tamaño en fragmentos y quince documentos dan la mitad del mínimo, con lo que la abstención dejaba de poder demostrarse. **C21 se archivó el 2026-09-02**, y con él caen los prerrequisitos de C24 y C30, o sea las dos mitades del proyecto que estaban esperando a la fusión. **C22 y `FIX1` se archivaron el 2026-09-05**, con lo que la ventana que `FIX1` tenía que respetar —entrar antes de que C24 etiquete su línea base— queda cumplida. **C24 se archivó el 2026-09-11 y C25 el 2026-09-12**, con lo que la cadena crítica `C21 → C24 → C25 → C26 → C34 → C36` arranca ahora en **C26**. C25 se archiva habiendo **refutado tres puntos de su propia ficha con mediciones** — la penalización de variante ambigua, la calibración de `1-2` frente a `3+` y la rotación como criterio de orden — y habiendo corregido un defecto que no estaba en su alcance: la fusión de C21 **concatenaba en vez de fusionar**. Deja **tres brechas declaradas y no cerradas** (`Recall@5` 0,758 contra 0,85, abstención 0,150 contra 0,80, y `v3` sin batir a `v2b` por el margen) y **desbloquea C25bis** (`clean-plain-fusion`), que retira el andamio de la fusión plana. **`C25bis` y C26 se archivaron el 2026-09-12**, y con ellos la cadena crítica deja de arrancar en C26 y pasa a arrancar en ~~**C34**~~ → **C30a** *(corregido el 13 sep: C34 lleva C30 de prerrequisito, así que nunca pudo ser el eslabón de arranque; era un error de la frase y no un cambio de plan)*. C26 se archiva habiendo cerrado el **último 501 cerrable** del contrato congelado —`/v1/inventory/propose` sigue en 501, pero por una rama anulada y ya declarada como limitación— y habiendo **refutado tres puntos de su propia ficha con mediciones**: «misma familia primero» estaba invertida, la exclusión por stock no le correspondía y `style_similarity` no tiene dato sobre catálogo real. Deja **dos limitaciones medidas y declaradas**, y anotada en la ficha de C34 la exclusión por stock que sí es suya. **C28 se archivó el 2026-09-13**, entregando las dos cifras del §16 que no existían —**20,9 % ponderado** y **32,1 s de media** sobre 204 perfiles, **204 cronometrados**— y publicándolas partidas, porque los **10,4 %** de los campos sensibles y los **42,3 %** de las etiquetas comerciales no miden lo mismo: aquéllas llegaban vacías y el revisor las rellenó con su criterio. Es el **noveno change consecutivo cuya exploración refuta lo escrito antes**, y el primero que además se refuta a sí mismo **durante la revisión**: la marca «pendiente de revisión» por campo resultó constante en seis de los siete campos y se retiró enmendando la spec. Confirma media predicción —las retiradas se concentran en el estrato B, 8 de 9— y refuta la otra mitad. **Deja tres cosas declaradas sin medir** (el A/B de teclado, la tesis de ceguera del span y la comparación de versiones de prompt) y **un hallazgo que ninguna consulta podía encontrar**: `vidrio` falta en el vocabulario de `materials` y alcanza 67 productos, el 5,6 % del catálogo.

---

## 3. Fichas

### Ola 0 — Cimientos y contratos (3-5 ago)

---

#### C01 · `init-ai-service-skeleton` 🔴

**Objetivo.** Servicio Python `jbg-ai` vacío pero ejecutable: `uv`, FastAPI, configuración por entorno, `GET /health`, contenedor y entrada en `docker-compose`.
**Prereq.** — · **Zona.** `ai-service/`, `docker-compose.yml`
**Alcance.** `pyproject.toml`, `src/jbg_ai/api/main.py`, `config/settings.py` (pydantic-settings), logging estructurado con `trace_id`, `Dockerfile`, servicio en red interna sin publicar puerto.
**Tests.** `test_health_returns_ok_with_version`; `test_settings_fail_fast_when_required_env_missing`; smoke con `TestClient`.
**Tarea obligatoria fuera de código.** Verificar en la consola de AWS que **RDS admite `CREATE EXTENSION vector`**. Si no, el plan B (contenedor Postgres+pgvector en la misma EC2) hay que saberlo hoy, no el 25 de agosto.

---

#### C02 · `add-ai-service-contracts-and-auth` 🔴

**Objetivo.** **Congelar el contrato** de los endpoints con modelos Pydantic, stubs deterministas y autenticación de servicio. Es lo que permite que las dos personas no se esperen durante un mes.
**Prereq.** C01 · **Zona.** `ai-service/src/jbg_ai/api/`
**Alcance.** Routers `retrieval`, `assist`, `inventory`, `index`, `enrich` y `evals` (este último solo con perfil de desarrollo); modelos request/response completos (§6.8 del diseño), incluidos **`materials[]`**, `family_id`/`variant_label` y **sobre-recuperación** (`top_k` vs `candidates_returned`); stubs tras flag `STUB_MODE`; dependencia FastAPI que valida el JWT interno HS256 y extrae `user_id`/`role`/`pos_id`/`trace_id`; OpenAPI exportado a `ai-service/openapi.json` versionado.
**Entregado.** 8 endpoints `/v1` congelados: `POST /v1/retrieval/products`, `POST /v1/retrieval/substitutes`, `POST /v1/assist/sale`, `POST /v1/inventory/propose`, `POST /v1/enrich/products`, `POST /v1/index/sync`, `GET /v1/index/status` y `GET /v1/evals/runs`, más `GET /health` público. Con `STUB_MODE=false`, la ruta sin lógica real responde 501 nombrando el change que la entregará.
**Tests.** `test_retrieval_stub_matches_response_schema`; `test_openapi_snapshot_is_stable` (rompe el build si alguien cambia el contrato sin avisar); `test_request_without_token_is_rejected`; `test_pos_id_from_token_overrides_body_value` (**el body no manda**); `test_health_is_public`.

---

#### C03 · `add-dotnet-ai-gateway-client` 🔴

**Objetivo.** Cliente tipado hacia `jbg-ai` con resiliencia desde el primer día, contra los stubs de C02.
**Prereq.** C02 · **Zona.** `JoiabagurPV.Application/`
**Alcance.** `IAiGatewayClient` + `AiGatewayClient` (typed `HttpClient`), Polly (0,8 s retrieval / 5 s assist, reintento único, circuit breaker), emisión y firma del JWT interno, propagación de `trace_id`, configuración en `appsettings` + SSM.
**Tests.** `SearchAsync_WhenServiceReturns200_MapsResponse`; `SearchAsync_WhenTimeout_ThrowsAiUnavailable`; `SearchAsync_WhenCircuitOpen_FailsFastWithoutCall`; `BuildToken_IncludesPosAndRoleClaims`. Con `HttpMessageHandler` falso.

---

#### C04 · `add-product-search-event-tracking` 🟢 🗄️

> **Ficha revisada el 2026-08-10** tras la sesión de exploración previa al proposal. Ver [§0](#0-revisiones-posteriores-a-la-versión-3) para el registro de qué cambió y por qué, y [HU-AIENG-004](../Historias/AI-Eng/HU-AIENG-004.md) para el detalle.

**Objetivo.** Telemetría consulta→selección desde el primer día, escrita por quien conoce cada dato. Sin prerrequisitos hacia atrás: es el change que se coge si la ruta crítica está ocupada. **Sí tiene un prerrequisito hacia adelante sobre C15**, que es una propiedad distinta y está nombrada abajo.
**Prereq.** — · **Zona.** `Domain/`, `Infrastructure/`, `Application/`, `API/Controllers/`, `Tests/` (la ficha v3 solo citaba dos de las cinco)
**Alcance.** Entidad `ProductSearchEvent` con `SearchSessionId`, `SearchOrigin`, `TraceId`, `ResultsCount`, `RetrievalMs`, `TotalMs` y `SelectedAt`; columna `Sale.SearchEventId` con `ON DELETE SET NULL`; **una única migración** con las cuatro reglas de borrado declaradas a mano; servicio con dos caminos de escritura (`RecordSearchAsync`, que nunca lanza y devuelve `Guid?`, más el registro de selección); **un solo endpoint**, `POST /api/ai/search-events/{id}/selection` con cuerpo `{ productId }` y respuesta `204`; columnas `jsonb` con truncado por número de entradas; dos índices, `(PointOfSaleId, CreatedAt)` y `(CreatedAt)`; arnés de test de migración reutilizable.
**Fuera de alcance.** **Cero rutas de lectura**: ni `GET`, ni agregación, ni panel. El análisis del entregable se hace con SQL a mano en C39.
**Tests.** `RecordSearch_WithValidScope_PersistsEventWithServerKnownFields`; `RecordSearch_WhenPersistenceFails_DoesNotThrowAndReturnsNull`; `RecordSelection_WithProductInResults_DerivesRankFromStoredList`; `RecordSelection_WhenCallerIsAdminButNotOwner_Returns403`; `RecordSearch_WithMoreResultsThanCap_RecordsTrueDisplayedCount`; `DeletingSearchEvent_NullsSaleAttribution_WithoutDeletingSale`; `Migration_JsonColumnsAreJsonbNotText`; `Model_HasNoPendingMigrationDifferences`.
**Prerrequisito hacia adelante (crítico).** C15 debe invocar `RecordSearchAsync` y devolver `searchEventId`. Es la única obligación cuyo incumplimiento deja el change **sin efecto y sin síntoma**: todo compilaría, todos los tests pasarían y la tabla estaría vacía en septiembre.
**Nota de utillaje.** Construye el arnés de test de esquema que heredan C07, C08, C19, C27 y C29: test de desfase modelo↔migración (sin base de datos) más aserciones sobre `information_schema`/`pg_indexes`. **Guardarraíl:** solo las aserciones que C04 necesita hoy; los cinco changes siguientes extienden la capa común cuando sepan qué les hace falta.
**Punto de partición predefinido.** Si desborda la sesión (regla 5): primero esquema + migración + arnés, que libera el slot de migración y es archivable solo; después servicio + endpoint + tests, que no lleva migración y convive con el C07 del compañero.

---

### Ola 1 — Datos y modelo (6-12 ago)

---

#### C05 · `add-pgvector-schema-foundation` 🔴

**Objetivo.** Persistencia lista: extensión `vector`, esquema `ai`, usuario dedicado, Alembic y tablas vacías con índices.
**Prereq.** C01 · **Zona.** `ai-service/migrations/`
**Alcance.** `CREATE EXTENSION vector`; esquema `ai`; migración inicial con `product_document` (**`materials text[]`**, `family_id`, `variant_label`, **`data_origin`**), `knowledge_document`/`knowledge_chunk`, `pos_projection`, `co_occurrence`, `sync_failure`; índices **HNSW `vector_cosine_ops`**, **GIN sobre `tsv` y sobre `materials`**, B-tree sobre `family_id`/`piece_type`/`price_band`/`data_origin`; pool acotado a 5 conexiones.
**Tests.** `test_migration_creates_vector_extension_and_ai_schema`; `test_hnsw_index_uses_cosine_operator_class` (consulta a `pg_indexes`; protege del antipatrón que desactiva el índice sin dar error); `test_gin_index_exists_on_materials`; `test_upgrade_downgrade_is_reversible`.

---

> **Fichas revisadas el 2026-08-17** tras la sesión de exploración previa al proposal, con el export real ya importado. C06 se parte en dos. Ver [§0](#0-revisiones-posteriores-a-la-versión-3) para el registro de qué cambió y por qué.

#### C06a · `add-real-catalog-ingestion-and-text-assist` 🔴 *(archivado 2026-08-22)*

> **Ficha alineada con el apply.** Change: [`openspec/changes/archive/2026-08-22-add-real-catalog-ingestion-and-text-assist/`](../../openspec/changes/archive/2026-08-22-add-real-catalog-ingestion-and-text-assist/). Spec viva: `real-catalog-corpus`. **No es 🗄️.**

**Objetivo.** Convertir el export real en un corpus sobre el que el enriquecimiento de C09 sea demostrable, sin falsear lo que el corpus es. **Desbloquea C09 y C10 sin esperar al volumen sintético.**
**Prereq.** C01 · **Zona.** `scripts/catalog/` *(no `jbg_ai.data` ni `prompts/`; `text_provenance` en `ai.product_document` queda para C13 — ver [§0](#0-revisiones-posteriores-a-la-versión-3))*
**Alcance entregado.** Corpus JSONL de **436 productos reales** (`data_origin: real`) en `data/catalog/real/generated/catalog-real-enriched.jsonl` + sidecar `c06a-assist/v2` / semilla `20260822` / `model: null`; pipeline `catalog-pipeline` (generate / validate / spike / ingest); **reparto por familia interna** 293 `rich` / 94 `sparse` / 49 `original` (11,24 %; texto del xlsx, no se vacía) **sin** emitir `variant_group_key` / `variant_label` / `family_seed`; agrupación interna 354 / 44 / 310; voz de vendedor en `assist.py`; `text_provenance` solo en JSONL; ingesta local `UPDATE` de `Description` por SKU (**0 unmatched**, 436 filas); informe en `informes/c06a-catalog-enrichment-report.md`.
**Tests.** En `scripts/catalog/tests/`: `test_generator_is_deterministic_for_same_seed`; **`test_variant_family_shares_text_quality`**; `test_jsonl_omits_family_seed_fields`; `test_original_tier_keeps_source_description`; `test_assisted_copy_does_not_mention_photos_or_source_sheet`; **`test_sku_price_name_and_collection_are_never_modified`**; `test_ingest_lists_unmatched_without_insert`; `test_ingest_rolls_back_when_identity_would_change`; más `test_description_over_1000_is_rejected`, `test_jsonl_lines_parse_with_real_origin_and_unique_skus`, ratios y rebalanceo de familias.
**Limitación que hereda §15.** El texto asistido **simula un reconocimiento multimodal que no se ha implementado y que §8.1 excluyó**; no hay fotos en el sistema (verificado: 0 `ProductPhotos`, 0 embeddings visuales). Los atributos no derivables de la evidencia previa son plausibles, no verificados. La voz v2 es **plantilla determinista**, no un LLM: sirve a C09; no es un estilo que C06b deba copiar si busca más inventiva.

---

#### C06b · `add-synthetic-catalog-augmentation` 🟢 *(archivado 2026-08-23)*

> **Ficha revisada el 2026-08-22**; archivada el 2026-08-23. Ver [§0](#0-revisiones-posteriores-a-la-versión-3). Change: `openspec/changes/archive/2026-08-23-add-synthetic-catalog-augmentation/`.

**Objetivo.** Llevar el corpus a **~1.200 productos totales** (holgura, no cifra exacta) con piezas sintéticas que un joyero podría fabricar y vender en tienda clásica, vitrina de hotel o aeropuerto, sin falsear el ancla real. **Desbloquea el volumen de C11 y C24.** No crea familias: eso es C18.
**Prereq.** C06a · **Zona.** `ai-service/src/jbg_ai/data/` — **CLI**, no se importa desde `jbg_ai.api.main`, no hay ruta HTTP, no toca la API .NET. Artefactos en `data/catalog/synthetic/generated/`. Ingesta local Docker (`localhost:5433` / `joiabagur_pv`).
**Alcance.** Orquestador + cliente LLM + prompt versionado: nombres, descripciones y **precios razonados** (pieza, tamaño, materiales, público del brief; **sin** bandas fijas ni canal de venta en `Product`). El código reserva SKUs que no colisionen con el JSONL de C06a ni con `"Products"."SKU"`, sella `data_origin: synthetic` y `text_provenance: synthetic`, valida `Description` ≤ 1000 e **`INSERT`** de colecciones **nuevas** y productos en una transacción. Un par de colecciones pueden seguir la temática menorquina; el resto divergen (hotel, aeropuerto/turista, atelier clásico). ~35 % de las descripciones mencionan dos o más materiales **en la prosa** (sin campo `materials[]` en el JSONL). **No** escribe `ProductFamily` / `ProductFamilyMember` ni emite `family_seed` / `variant_group_key`. Settings `LLM_*` **opcionales** al boot de `/health` (solo las exige el CLI). Sidecar con `generator_version`, `seed`, `model`, `prompt_version`, `generated_at`. El JSONL commiteado es la fuente; regenerar texto exige flag explícito.
**Fuera de alcance.** C09, C10, C18, migración `text_provenance` (C13), `openapi.json`, RDS/producción, reutilizar `scripts/catalog/assist.py`.
**Tests.** Con LLM falso: `test_skus_are_unique_across_real_and_synthetic`; `test_sku_allocator_is_deterministic_for_same_seed`; `test_jsonl_omits_family_seed_fields`; `test_ingest_inserts_new_products_without_touching_real_skus`; `test_ingest_creates_new_collections_with_unique_names`; `test_description_over_1000_is_rejected`; `test_settings_do_not_require_llm_key_to_boot`; `test_unit_suite_makes_no_provider_calls`. «Mismas descripciones a igual semilla» **no aplica** (temperatura > 0).
**Nota sobre calibración.** No se heredan del real la distribución de precios ni el tamaño de familia. El esquema de SKU **sí** se copia (sin reutilizar los 436). La **longitud** del copy se aproxima a las medias del JSONL real (`rich` / `sparse` / `original`); el código declara el 70/20/10 **antes** del draft y recorta por frases enteras (revisión 22 ago, tarde). El agrupamiento es por stem de nombre, no `ProductFamily`.
**Puede correr en paralelo** a C09. C10 no lo necesita. C11 y C24 sí, por volumen **ya ingerido** en .NET.

---

#### C07 · `add-product-family-entity` 🟢 🗄️

**Objetivo.** Familias como **entidad de negocio explícita y editable**, no como clave textual generada. Es la decisión 2 de la revisión.
**Prereq.** — · **Zona.** `Domain/`, `Application/`, `Infrastructure/`, `API/Controllers/`, `Tests/` *(corregida al aplicar)*
**Alcance.** `ProductFamily` (Name, Description, **Origin, ApprovedByUserId, ApprovedAt** reservados para C18) y `ProductFamilyMember` (ProductId, VariantLabel, SortOrder), migración, repositorio, `POST /api/product-families`, `GET /api/product-families/{id}`, `PUT /api/product-families/{id}`, `PUT /api/product-families/{id}/members`, `GET /api/products/{id}/family`. Un producto pertenece como máximo a una familia, por índice único. Miembros **declarativos**: la petición trae la lista completa y el orden sale de su posición. Huérfano (204) distinguible de producto inexistente (404).
**Tests.** `CreateFamily_WithMembers_PersistsOrder`; `AddMember_WhenProductAlreadyInAnotherFamily_ReturnsConflict`; `GetFamily_ReturnsSiblingsOrderedBySortOrder`; `RemoveMember_KeepsFamilyWhenOthersRemain`; **`ReplaceMembers_ReorderingExistingMembers_Succeeds` y `ReplaceMembers_SwappingTwoVariantLabels_Succeeds`** (los que destaparon el fallo de estado `Added`/`Modified`); detectores de esquema.

---

#### C08 · `add-product-ai-profile-entity` 🟢 🗄️

**Objetivo.** Perfil IA revisable en .NET, con `materials[]` y **revisión híbrida por campo** (decisión 5).
**Prereq.** C03 · **Zona.** `Domain/`, `Application/`, `API/Controllers/`
**Alcance.** `ProductAiProfile` con `MaterialsJson`, `PieceType`, `StoneType`, `SizeLabel`, tags, `AiConfidence`, **`FieldConfidenceJson`**, **`FieldSourceJson`** (`rule` \| `inferred`), `ReviewStatus`, `SourceHash`; migración; `POST /api/ai/catalog/enrich-batch`; enrutado híbrido: campos sensibles inferidos → `Pending`, tags con confianza alta → `Approved`, resto → `Pending`. Marca `review_state = auto_bulk` para la vía masiva.
**Tests.** `EnrichBatch_AsOperator_Returns403`; `Routing_WhenSensitiveFieldInferred_MarksPendingReview`; `Routing_WhenSensitiveFieldFromRule_DoesNotRequireReview`; `Routing_WhenTagConfidenceAboveThreshold_AutoApproves`; `Profile_StoresMultipleMaterials`; test de migración.

---

#### C09 · `add-catalog-enrichment-pipeline` 🔴 *(archivado 2026-08-23)*

**Objetivo.** De producto crudo a perfil propuesto: extracción estructurada con **`materials[]`**, vocabulario cerrado, confianza por campo y puertas de calidad de lote.
**Prereq.** C06a · **Zona.** `ai-service/src/jbg_ai/enrichment/`
**Alcance.** Normalización determinista previa (talla por regex → `source: rule`); prompt **v1 versionado** en `ai-service/prompts/enrichment/v1.md`; JSON schema estricto a temperatura 0; **vocabulario cerrado de materiales** con normalización de sinónimos ("plata de ley", "925" → `plata`); `materials` como lista, `[]` si no hay evidencia; confianza **por campo**; puertas de lote (unicidad SKU, **cobertura de tags ≥ 70 % global y ≥ 90 % sobre el estrato `text_provenance: ai_assisted`**, vocabulario respetado); `POST /v1/enrich/products` real.
**Tests.** Con LLM falso: `test_extracts_multiple_materials_from_description`; `test_material_synonym_normalized_to_canonical_term`; `test_rejects_value_outside_closed_vocabulary`; `test_empty_materials_flags_review_not_default_value`; `test_size_regex_marks_field_source_as_rule`; `test_batch_fails_when_tag_coverage_below_threshold`; **`test_tag_coverage_gate_is_evaluated_per_text_provenance`**.
**Por qué la puerta baja de 90 % a 70 %** *(revisado el 2026-08-17)*. Con el reparto de C06a el techo alcanzable es ≈ 77 % —0,70 × 95 % + 0,20 × 40 % + 0,10 × 20 %—, así que un 90 % global es **inalcanzable por construcción** y bloquearía el pipeline siempre. Un umbral solo global tendría además el defecto de **medir en parte nuestra propia política de ruido**: cambiar el reparto a 60/25/15 lo haría saltar sin que el extractor hubiera cambiado. El desglose por estrato conserva el 90 % donde sí significa algo y deja de castigar el ~10 % `original` (texto del comerciante, no reescrito). Es lo que permite aprobar la puerta **sin violar** la regla de §7.1: «devuelve `[]` si no hay evidencia, nunca inventa».
**Si se desborda:** partir en pipeline+prompt / puertas de calidad.

---

#### C10 · `add-synthetic-world-simulator` 🟢

**Objetivo.** POS, inventario, histórico de ventas y **co-ocurrencia**, coherentes por construcción con el catálogo.
**Prereq.** C06a · **Zona.** `ai-service/src/jbg_ai/data/world/`
**Alcance.** 10-14 POS con perfil de clientela, estacionalidad y **marca de origen de suministro**; matriz de propensión producto×POS; 5.000-9.000 filas de inventario respetando `Inventory.IsActive`; simulación Poisson → 15.000-25.000 ventas sobre 14-18 meses; movimientos derivados; **co-ocurrencia por operación de venta** (`BulkOperationId` o mismo POS y día) para complementarios.
**Tests.** `test_no_sale_without_stock_at_that_pos`; `test_seasonality_peaks_match_pos_profile`; `test_inventory_movements_reconcile_with_final_stock`; `test_co_occurrence_only_counts_same_operation`; `test_simulation_is_deterministic_for_same_seed`.
**Si se desborda:** partir en POS+inventario / ventas+co-ocurrencia.

**Hecho (2026-08-23).** CLI en `jbg_ai.data.world` (`world simulate|ingest`), no `generators/`. 12 POS en YAML commiteado; JSONL y dump gitignored. Co-ocurrencia solo `BulkOperationId`, no `ai.*`. Se retira el test de bit-identidad. `is_supply_source` solo YAML (SQL = C19). Informe [`informes/c10-synthetic-world-report.md`](informes/c10-synthetic-world-report.md).

---

#### C11 · `add-source-text-and-embedding-client` 🟢

**Objetivo.** `SourceText` canónico, `SourceHash` e idempotencia. Es lo que hace barato y determinista todo el reindexado.
**Prereq.** C05, C09 · **Zona.** `ai-service/src/jbg_ai/indexing/`
**Alcance.** Constructor de `doc_text` con orden fijo, **incluyendo materiales (ordenados alfabéticamente para estabilidad del hash), familia y variante**; `source_hash` SHA-256; cliente de embeddings con reintento, batching y caché por hash; `embedding_model`/`embedding_version`.
**Tests.** `test_source_text_is_stable_for_same_profile`; `test_material_order_does_not_change_hash`; `test_hash_changes_when_family_changes`; `test_embedding_not_recomputed_when_hash_unchanged`.

**Hecho (2026-08-25).** Biblioteca `jbg_ai.indexing`: plantilla `source-text/v1`, SHA-256 del `doc_text` renderizado, LiteLLM `aembedding` 1536d con caché RAM, batch 64 y backoff 429/5xx. `api.main` no importa el paquete; `/v1/index/*` sigue siendo el stub C13. Spec viva `catalog-source-text`.

---

#### C12 · `add-dotnet-index-feed-endpoints` 🔴 *(archivado 2026-08-26)*

**Objetivo.** La única vía de lectura de Python: feeds HTTP paginados con cursor, **con tombstones** (decisión 10).
**Prereq.** C07, C08 · **Zona.** `API/Controllers/`, `Application/`
**Alcance.** `GET /api/ai/index-feed/catalog?since=` (producto + perfil aprobado + familia) y `GET /api/ai/index-feed/pos-availability?since=` (asignación, `qty_bucket`, ventas 30/90 d); **tombstones** `{product_id, deleted_at|deactivated_at}`; hash agregado para detección de divergencia; paginación obligatoria (máx. 50); solo autenticación de servicio.
**Tests.** `CatalogFeed_WithSinceCursor_ReturnsOnlyChangedRows`; `CatalogFeed_EmitsTombstoneWhenProductDeactivated`; `CatalogFeed_ExcludesUnapprovedProfiles`; `PosAvailabilityFeed_ReturnsBucketNotExactQuantity`; `Feed_WithUserJwt_Returns403`; `Feed_ReturnsAggregateHashForDriftDetection`.

**Hecho (2026-08-26).** `GET /api/ai/index-feed/catalog` (página 50) y `.../pos-availability` (página 200), header `X-Index-Feed-Key`, 401 (no 403) ante JWT/C03/sin key. Tombstones `kind`+`reason` (`deactivated`/`unapproved`/`unassigned`). `price-band/v1`. Hash SHA-256 del conjunto indexable. `ReplaceMembers` sella `Product.UpdatedAt` vía `ExecuteUpdateAsync`. Sin migración; `openapi.json` intacto. Spec viva `index-feed`. Change [`2026-08-26-add-dotnet-index-feed-endpoints`](../../openspec/changes/archive/2026-08-26-add-dotnet-index-feed-endpoints/).

---

### Ola 2 — Slice vertical desplegado (13-19 ago)

> **Hito:** el 19 de agosto un operador busca en lenguaje natural desde `pv.joiabagur.com` y ve resultados con stock real. Con dos personas, integrar y desplegar pronto es la única defensa contra una sorpresa de infraestructura en la última semana.

---

#### C13 · `add-product-document-indexer` 🔴 *(archivado 2026-08-26)*

**Objetivo.** Poblar `ai.product_document` desde el feed y dejar el índice consultable y observable.
**Prereq.** C11, C12 · **Zona.** `ai-service/src/jbg_ai/indexing/`
**Alcance.** Upsert idempotente por `product_id`; **procesamiento de tombstones**; `tsvector` con configuración `'spanish'`; `POST /v1/index/sync` y `GET /v1/index/status` con `drift_count` y `last_full_sync_at`; fallos a `ai.sync_failure` con backoff.
**Tests.** `test_upsert_is_idempotent_for_same_source_hash`; `test_tombstone_removes_document_from_index`; `test_tsvector_uses_spanish_configuration`; `test_status_reports_drift_when_counts_diverge`; `test_failed_batch_recorded_and_does_not_block_others`.

**Hecho (2026-08-26).** Dreno del feed de catálogo con keyset y tope 180 s; skip-embed si `source_hash` coincide; tombstones idempotentes; mapa `sku_provenance.json` en `src/`; Alembic `text_provenance` + `sync_checkpoint`; OpenAPI `since_id` / `cursor_id`; CLI `python -m jbg_ai.indexing sync`; deriva por un GET (`aggregateHash`). 503 nombrado si faltan feed/embed/mapa. Sin POS, sin editar `embeddings.py`. Spec viva `product-document-indexer`. Change [`2026-08-26-add-product-document-indexer`](../../openspec/changes/archive/2026-08-26-add-product-document-indexer/).

---

#### C14 · `add-vector-retrieval-endpoint` 🔴 *(archivado 2026-08-27)*

**Objetivo.** Primera recuperación real: vectorial con top-k, umbral, abstención y **sobre-recuperación**.
**Prereq.** C13 · **Zona.** `ai-service/src/jbg_ai/retrieval/`
**Alcance.** `POST /v1/retrieval/products` real: embedding de consulta, `<=>` sobre HNSW, umbral configurable, `low_confidence: true` con lista vacía; **devuelve `top_k × 3` candidatos (tope 60)** para que .NET tenga margen al hidratar; log estructurado por etapa con `trace_id`.
**Tests.** `test_returns_empty_with_low_confidence_when_all_above_threshold`; `test_returns_overfetched_candidate_count`; `test_results_ordered_by_ascending_distance`; `test_trace_id_appears_in_stage_logs`.

**Hecho (2026-08-27).** `POST /v1/retrieval/products` real cuando `STUB_MODE=false`; stub C02 si stub mode. Embed `max_attempts=1` sin editar `embeddings.py`. `<=>` cosine, umbral 0,65 en SQL, overfetch **después** del umbral (como mucho `min(top_k × 3, 60)` de las filas que pasan el umbral), filtros del body. `mode=hybrid`/`lexical` ejecutan la rama vectorial hasta C21. 503 si faltan `JPV_EMBEDDING_API_KEY` / `DATABASE_URL` / índice compatible; abstención 200 + `low_confidence`. Sin `query_log`, sin OpenAPI, sin filtro `pos_id`. Spec viva `vector-retrieval`. Change [`2026-08-27-add-vector-retrieval-endpoint`](../../openspec/changes/archive/2026-08-27-add-vector-retrieval-endpoint/).

---

#### C15 · `add-dotnet-ai-search-endpoint` 🔴 *(archivado 2026-08-28)*

**Objetivo.** El endpoint del frontend, con **hidratación autoritativa** y degradación. Implementa la decisión 11: la verdad la pone .NET.
**Prereq.** C03, C14 · **Zona.** `API/Controllers/`, `Application/`, `Tests/` *(sin migración: C15 no es 🗄️)* · **Lleva `design.md`**
**Alcance** *(corregido el 2026-08-28; ver [§0](#0-revisiones-posteriores-a-la-versión-3))***.** `POST /api/ai/search` en `AiSearchController`: pide al gateway la **ventana máxima del contrato en una sola llamada** (`top_k = 20` → 60 candidatos), **hidrata desde PostgreSQL** con una consulta conjunta —nunca `ProductService`, cuyo camino son ~120 viajes— descarta lo que no tiene `Inventory` activo **en ese POS** o `Product.IsActive = false`, **conserva el stock 0** y trunca a la página pedida; feature flag por POS en configuración; caché de candidatos de TTL corto y limitación de peticiones por `userId`; `ai_available: false` + **buscador degradado propio** (full-text español en consulta, acotado al POS, semántica OR, orden por `ts_rank`) si el circuito está abierto.
**Tests.** `Search_HydratesPriceAndStockFromDatabase_NotFromAiResponse`; `Search_WhenCandidateNoLongerAssigned_DropsItAfterHydration`; `Search_RequestsTheMaximumCandidateWindowInASingleCall`; `Search_WhenPosCoverageIsLow_ReturnsFewerThanTopK_WithoutASecondCall`; `Search_KeepsAssignedProductWithZeroStock`; `Search_HydratesInASingleQuery`; `Search_WhenAiUnavailable_FallsBackToLexicalSearch`; `Fallback_MatchesAnyQueryTerm_NotTheWholeString`; `Fallback_IsScopedToTheSearchPointOfSale`; `Search_WhenFeatureFlagOff_UsesLegacySearch`; `Search_WhenFeatureFlagOff_RecordsOriginDisabled`; `Search_RepeatedQueryHitsCandidateCache_WithoutSecondEmbedding`; `Search_CacheKeyIncludesPointOfSale`; `Search_AdminMayChooseAnyActivePos`; `Search_OperatorCannotChooseUnassignedPos`; `Search_WhenTelemetryFails_StillReturnsResults`; integración con Testcontainers.

**Obligaciones heredadas de C04** *(añadidas el 2026-08-10; ver [§0](#0-revisiones-posteriores-a-la-versión-3))*

| | |
|---|---|
| **A1 · crítica** | Invocar `RecordSearchAsync` **después** de hidratar y truncar, y devolver `searchEventId` en la respuesta. **Sin esto C04 es código muerto sin síntoma:** compila, los tests pasan y la tabla llega vacía a la entrega |
| **A2** | Pasar filtros efectivos, `SearchOrigin` (`Assisted` o `LexicalFallback` según haya respondido `jbg-ai` o el buscador léxico), `traceId`, `RetrievalMs`, `TotalMs` y el `searchSessionId` que envía el cliente |
| **A3** | El servicio de C04 **no lanza nunca**: devuelve `Guid?`. C15 solo tiene que tolerar el nulo y responder igual — la búsqueda nunca falla por culpa de la telemetría |
| **A4** | Aplicar una política de limitación de peticiones a `POST /api/ai/search`. **Es cuestión de coste antes que de seguridad:** un `debounce` mal ajustado o un dedo apoyado en una tecla genera llamadas de embedding facturables, y §12 se compromete a que el coste esté instrumentado y reportado |

**Hecho (2026-08-28).** `POST /api/ai/search` en `AiSearchController`, sin versión en la ruta. Ventana máxima del contrato en **una sola llamada** (`top_k = 20` → 60 candidatos) y **sin repetición**. Hidratación autoritativa en una consulta conjunta que parte de `Inventory` y no de `Product`: descarta lo no asignado o inactivo, **conserva la cantidad cero** marcándola, y devuelve la cantidad de ese punto de venta. Buscador degradado propio con `to_tsvector('spanish', …)` calculado en consulta —sin índice, sin migración—, semántica OR y orden por `ts_rank`; usa la conversión **tolerante** (`websearch_to_tsquery`) en coincidencia y ordenación, porque la estricta lanza ante un `&` suelto y convertiría el único camino que queda en pie en un error del servidor. Flag por POS en configuración con `IOptionsMonitor` y **`SearchOrigin.Disabled = 3`**. Caché de candidatos con el POS en la clave más limitación por `userId`. Punto de venta **obligatorio**; el admin puede elegir cualquiera **activo**. Embudo en log estructurado, sin columnas nuevas. Specs vivas: `ai-assisted-search` (nueva, 12 requisitos y 38 escenarios) y `ai-search-telemetry` (`## MODIFIED` por el tercer origen).

**`/opsx:verify` encontró un defecto crítico que la suite no vio:** la limitación particionaba por **dirección de red y no por usuario**, porque `UseRateLimiter()` corría antes que `UseAuthentication()` y la clave de partición se leía sin identidad. Corregido, con test de regresión que se comprobó **reintroduciendo el defecto** para verificar que falla. Más tres huecos menores: `CandidateCacheSize` se validaba al arranque sin acotar nada (instancia dedicada de `MemoryCache` con `SizeLimit`), la garantía de degradación era enumerativa (cláusula final sobre el tipo abstracto) y `survivedHydration` no era comparable entre orígenes (el camino degradado pide la misma ventana y se trunca después).

**Verificación con el mundo sembrado:** el corte de recall es real y está medido — **0 % de páginas cortas en CIU-CENTRE frente al 37,5 % en FORNELLS**, con medias de supervivientes de 41,6 y 14,6 contra las 43 y 12,1 que predijo el diseño. Change [`2026-08-28-add-dotnet-ai-search-endpoint`](../../openspec/changes/archive/2026-08-28-add-dotnet-ai-search-endpoint/).

---

#### C16 · `add-frontend-assisted-search-panel` 🔴 *(archivado 2026-08-29)*

**Objetivo.** Punto de entrada del operador: panel "Buscar con ayuda" en el flujo de venta.
**Prereq.** C15 · **Zona.** `frontend/src/`, más dos tramos pequeños en `Application/` y `Tests/` del backend *(sin migración: C16 no es 🗄️)* · **Lleva `design.md`**
**Alcance** *(corregido el 2026-08-29; ver [§0](#0-revisiones-posteriores-a-la-versión-3))***.** `ai-search.service.ts`; panel en **ruta propia** `/sales/new/assisted` y **tercera tarjeta** en el hub de ventas; entrada natural con **envío explícito** —nunca `debounce`, que factura embeddings por pulsación— y 3-5 consultas de ejemplo; **filtros rápidos con materiales (multi-selección)** que no disparan por sí solos, sobre el vocabulario cerrado replicado en el frontend; punto de venta preseleccionado, con selector cuando el operador tiene varios o es administrador; resultados con foto, SKU, nombre, precio, stock, **insignia de origen y chips de materiales** —y talla sólo cuando `variantLabel` exista, lo que ocurrirá con C18—; **cinco estados**: carga, abstención, sin surtido, degradado y cuota agotada, más el aviso de **página corta**; embudo colapsado sólo para administradores; "Seleccionar para venta" que prellena el flujo existente (`productId` por state, patrón de `scan.tsx`) y arrastra `searchEventId` hasta la caja. **Tramo .NET:** `Guid? SearchEventId` en `CreateSaleRequest` y `BulkSaleLineRequest` con degradación a nula, y `materials` en `AssistedSearchResultDto`.
**Tests.** `should render results with reason when search succeeds`; `should show legacy results banner when ai is unavailable`; `should allow selecting multiple materials in quick filters`; `should emit search event when a result is selected`; `should keep the search session id across reformulations in one panel visit`; `should render results in the order received`; `should distinguish abstention from empty assortment`; `should show a rate limit message when the server answers 429`; `should not block navigation when reporting the selection fails`; `should carry the search event id into the cart line`; `should ignore a stale response when the point of sale changed`; .NET: `CreateSale_WithUnknownSearchEvent_StoresNullAttribution`; `CreateSale_WithSearchEventOfAnotherUser_StoresNullAttribution`; `BulkSale_AttributesEachLineToItsOwnSearchEvent`.

**Obligaciones heredadas de C04** *(añadidas el 2026-08-10; ver [§0](#0-revisiones-posteriores-a-la-versión-3))*

El envío de `ProductSearchEvent` **ya no consiste en construir el evento**: el backend escribe la mitad de búsqueda. C16 solo reporta la selección, y el cuerpo tiene un único campo.

| | |
|---|---|
| **B1** | Ruta relativa `/ai/search-events`, sin duplicar el prefijo: `VITE_API_BASE_URL` ya trae `/api` |
| **B2** | Generar un `searchSessionId` por episodio al abrir el panel y enviarlo en **todas** las búsquedas de ese episodio. Sin él, cada reformulación cuenta como un falso «consulta sin resultado». *(2026-08-29: un episodio = un montaje del panel; dos visitas que acaban en selección son dos episodios legítimos, no dos falsos abandonos)* |
| **B3** | Renderizar los resultados **en el orden recibido**; nada de `sort()` en cliente. Si se reordena, el rank pasa a medir la UI en lugar de la calidad del retriever, y el KPI `% selección rank 1/3` deja de significar lo que dice |
| **B4** | Enviar la selección **en el instante del clic**, no diferida ni agrupada al cerrar el panel, y sin bloquear la navegación. El servidor sella el instante: si la llamada se retrasa, el KPI mide cuándo se acordó el navegador. *(2026-08-29: basta un `POST` sin `await`; la navegación es de SPA, no hay descarga de página, y `sendBeacon` no puede poner la cabecera de autorización. Si `searchEventId` es nulo, la llamada se omite en silencio)* |
| **B5** | Arrastrar `searchEventId` desde la selección hasta el checkout, **por línea**, y enviarlo en `CreateSaleRequest` / `BulkSaleLineRequest`. Un `searchEventId` desconocido debe degradar la atribución a nula: **nunca hacer fallar la venta**. *(2026-08-29: **ninguno de los dos objetos de transferencia tiene el campo**, así que B5 obliga a un tramo .NET dentro de C16. La degradación a nula cubre también el evento **de otro usuario**, por coherencia con el endpoint de selección, que exige propiedad sin excepción de administrador)* |
| **B6** *(de C15, 2026-08-28; ampliada el 2026-08-29)* | Distinguir en pantalla los **cuatro** «cero resultados»: **abstención** (la IA respondió pero nada superó el umbral → «prueba a reformular»), **sin surtido** (había candidatos y ninguno está en este POS → «nada de esto está en tu tienda», con **quitar filtros** como primer remedio), **degradado** (`aiAvailable: false` → «búsqueda asistida no disponible») y **cuota agotada** (`429`, que la spec de C15 exige no confundir con la indisponibilidad de la IA). Con un único `results: []` el panel miente en tres de los cuatro casos. C15 los expone con `aiAvailable`, `lowConfidence`, el código de estado y los contadores del embudo |
| **B7** *(2026-08-29)* | Declarar la **página corta** cuando sobrevivan menos resultados que la página pedida, con los contadores que C15 ya devuelve. Es la línea base «antes» de la ablation de C22 en §11.2 dicha al operador en una frase, y evita que el corte por punto de venta se lea como que el sistema no sabe buscar |

**Lo que C16 ya *no* tiene que hacer** *(y que la ficha v3 daba por suyo)*: emitir un evento al abandonar la búsqueda, calcular y enviar el rank 1-based de la lista mostrada, reportar el origen de los resultados, y medir el tiempo hasta la selección. Las cuatro las cubre el servidor.

**Lo que C16 no puede hacer todavía, y no disimula** *(2026-08-29)*: el «motivo» real —`match_reasons` es la cadena literal `["vector"]` hasta C21—, la talla —`variantLabel` lo puebla C18—, y distinguir «asistencia desactivada en este punto de venta» de «la IA se cayó», porque la API devuelve `aiAvailable: false` en ambos casos aunque la telemetría sí los separe.

**Hecho (2026-08-29).** Panel en `/sales/new/assisted` con tercera tarjeta en el hub y entrega al flujo manual por estado de navegación. **Envío explícito**, nunca `debounce`: la clave de la caché de C15 incluye la consulta completa, así que ningún prefijo acierta y a 400 ms se agotan las 30 peticiones/min en cinco consultas. Filtros de material y tipo de pieza sobre el vocabulario cerrado replicado con test de fijación; no disparan solos. Insignia de origen y chips de materiales en lugar de `matchReasons`; talla condicional. **Cuatro** estados sin resultados —el `429` incluido— más el aviso de página corta. Embudo colapsado sólo para admin. **Tramo .NET sin migración:** `SearchEventId` opcional en `CreateSaleRequest` y `BulkSaleLineRequest`, asignado tras comprobar **existencia y propiedad**; desconocido o ajeno → nulo, la venta nunca falla. Cierra el requisito de atribución de `ai-search-telemetry`, archivado como cumplido y sin camino por el que cumplirse. `materials` en `AssistedSearchResultDto`. **`AiGateway:RetrievalTimeoutMs` 800 → 2500 ms, temporal**: medido contra el mundo sembrado, a 800 ms la vía asistida degradaba en *todas* las búsquedas; revertir cuando C21/C22 hagan singleton el cliente de embeddings (anotado en `DEFERRED_TASKS.md`). Verificación manual con recuperación real: CIU-CENTRE 60 → 32 → página llena, FORNELLS 60 → 8 → **página corta**, confirmando la aritmética de C15. Specs vivas `assisted-search-panel` (nueva), `sales-management` y `ai-assisted-search`. Change [`2026-08-29-add-frontend-assisted-search-panel`](../../openspec/changes/archive/2026-08-29-add-frontend-assisted-search-panel/).

---

#### C17 · `add-ai-service-deployment` 🔴

**Objetivo** *(corregido el 2026-08-29; ver [§0](#0-revisiones-posteriores-a-la-versión-3))***.** **Entorno de demo desplegado y con datos**, en una **cuenta AWS distinta de la de la tienda**, con el servicio de IA alcanzable **sólo** desde el backend. Cubre el criterio de entrega del §16 *«URL pública con usuario demo y vídeo de 2-3 min»*. No despliega a la cuenta de producción: **no hay acceso a ella**, y su RDS es la base de datos real del negocio.

**Prereq.** C15 · **Zona.** `terraform/demo/`, `.github/workflows/`, raíz (`compose.demo.yaml`, `deploy/demo/`, `.dockerignore`), `ai-service/`, `backend/`, `frontend/` *(sin migración: C17 no es 🗄️)* · **Lleva `design.md`**

**Alcance.** **Infra:** módulo Terraform en directorio y **estado propios** (EC2 `jbg-demo-host` t3.small, grupo de seguridad sólo 80/443, IP elástica, dos repos ECR `jbg-demo-api` / `jbg-demo-ai`, parámetros `/jbg-demo/*`, rol OIDC propio acotado a `environment:demo`); AMI resuelta por `data "aws_ssm_parameter"`; `user_data` **mínimo de cuatro pasos** con el plugin de Compose descargado **con versión fijada**. **Runtime:** `compose.demo.yaml` autocontenido en la raíz con **cuatro servicios** —`jbg-demo-proxy` (Caddy, único con `ports:`), `jbg-demo-api`, `jbg-demo-ai`, `jbg-demo-postgres` (`pgvector/pgvector:pg15`)—, volúmenes `jbg-demo-pgdata` / `jbg-demo-caddy-data` / `jbg-demo-caddy-config`, red `jbg-demo-net`, `mem_limit` en el servicio de IA. **Workflow** `deploy-demo.yml` (OIDC + ECR + SSM) sobre la rama `demo`, con secretos leídos de SSM **al entorno del proceso**, nunca a disco. **Imágenes:** `Dockerfile.demo` nuevo para API+SPA con `VITE_API_BASE_URL=/api`; `ai-service/Dockerfile` endurecido (no-root, `uv` con versión fijada, multietapa, `HEALTHCHECK`); `.dockerignore` en la raíz. **Aplicación:** `/health` enriquecido en el sitio —BD, índice y `provider: configured|missing`, cacheado, **sin llamar al proveedor**— con contraste de `embedding_model` contra el índice; `AiHealthController` en `api/ai/health` sólo para administradores y **fuera del circuit breaker**; tarjeta de estado en el dashboard de admin. **Datos:** volcado de `public` y de `ai` desde local, cuentas de demo sustituyendo al personal real, y **un** `POST /v1/index/sync` de reconciliación. **Deprecaciones:** cabecera en `Dockerfile`, `Dockerfile.prod` y `backend/docker-compose.prod.yml`, más la corrección de `backend/README.md` — deuda que el ticket de C03 ya asignó a C17.

**Fuera de alcance.** La cuenta AWS de la tienda **en su totalidad**; `Dockerfile.bundled`; `backend/docker-compose.yml` y la spec viva `ai-service-dev-compose`; regenerar `openapi.json`; la bifurcación `/health` ÷ `/health/ready` (disparador escrito en §0); revertir los 2500 ms de C16 (es C21/C22); cualquier migración nueva.

**Tests.** Smoke post-deploy por `aws ssm send-command` + `docker exec` —**el servicio es privado y el runner no lo alcanza**— comprobando `/health` con BD e índice OK y `provider: configured`; `test_health_reports_model_mismatch_when_index_disagrees`; `AiHealth_ReturnsUnauthorized_ForNonAdministrator`; `AiHealth_BypassesCircuitBreaker`; frontend `should show ai service status card when admin`; validación del workflow con `workflow_dispatch` antes de tocar la rama `demo`.

---

#### C18a · `add-family-suggestion-and-approval` 🟢 *(archivado 2026-08-31)*

**Objetivo.** La mitad que desbloquea del flujo mixto: la IA propone y el administrador aprueba **por lotes**. Es lo que hace que `family_id` deje de ser nulo, y con ello que dejen de ser vacuos los tests de familia de C25, C26, **C30a** y C36.
**Prereq.** C07, C13 · **Zona.** `ai-service/src/jbg_ai/families/`, `backend/` · **Lleva `design.md`**
**Alcance.** Motor determinista sin LLM: raíz normalizada, **fusión por material** (nunca stripping global), guarda de raíz degenerada, puerta de `piece_type` con el nulo como valor propio, **veto relativo por embedding** que marca y no elimina, `variant_label` verbatim y `position` por rango canónico. **Novena ruta del contrato congelado**, `POST /v1/families/suggest`. En .NET, `POST /api/ai/catalog/family-suggestions` y `/apply`, que persiste vía `ProductFamilyService` —nunca por SQL— y escribe `Origin = AiApproved` con aprobador e instante. Sin migración, sin frontend, sin persistir propuestas.

**Hecho (2026-08-31).** **156 familias y 486 miembros**, cero conflictos. 32 entradas que no son joyería terminada retiradas del índice con `ReviewStatus = Rejected` —nunca `IsActive`: la tienda las vende—. Reconciliación en **una sola** sincronización incremental: `upserted 486, deleted 32, failed 0`. Cola de revisión de **15 miembros en 5 familias** (margen 0,05). Informe: [`informes/c18a-family-suggestion-report.md`](informes/c18a-family-suggestion-report.md). Change [`add-family-suggestion-and-approval`](../../openspec/changes/archive/2026-08-31-add-family-suggestion-and-approval/).

**Tres correcciones que el apply obligó a hacer.** *(1)* El **umbral absoluto del §7.5 no existe**: peor hermano y mejor extraño se solapan (real 0,847–0,936). La raíz agrupa y el embedding veta, **en relativo**. *(2)* El **stripping global de material degenera** `Anillo plata S/M/L/XL` a la raíz `anillo`; la fusión no. *(3)* El 1,7 % que la exploración midió describía familias de sufijo de talla solamente; sobre el algoritmo entregado la cifra honesta es **3,1 %**.

#### C18b · `add-family-review-ui-and-orphan-alert` 🟢 🗄️

> **Ficha reescrita el 2026-08-31** tras la sesión de exploración. Sus tres números —15 marcados, 4 rechazados, 37 excluidos— quedaron caducados al aplicarse C18a, y su zona se quedaba corta por séptima vez. Motivo, medición y decisiones en el **§0 · *C18b, al explorar***.

**Objetivo.** El segundo caso de intervención humana del PF: **auditar lo que existe**, no pintar propuestas que ya no hay. Y producir la evidencia del renglón *«métricas de revisión humana»* del §16, que hoy no tiene ninguna.
**Prereq.** C18a · **Zona.** `ai-service/src/jbg_ai/families/`, `backend/` *(incluidos `Infrastructure/` y `Tests/`: es 🗄️)*, `frontend/` · **Lleva `design.md`**

**Punto de partida medido (2026-08-31).** 156 familias · 486 miembros · **0 familias `Manual`** · 1.168 documentos · **682 activos sin familia**, 671 de ellos con `piece_type` · 2 grupos rechazados · 11 excluidos por la puerta.

**Alcance.** **`POST /v1/families/audit`**, **décima ruta** del contrato congelado, devolviendo en una llamada los **miembros marcados** sobre familias *persistidas* —`apply_relative_veto` de C18a con el universo cambiado— y los **huérfanos candidatos**, nominados por **margen relativo** y ordenados por pureza de vecindad, con la puerta de `piece_type` y reportando `data_origin`; **`FamilyReviewVerdict`** y la **séptima migración** —que acabaron siendo **tres**, ver la nota de cierre—, con el par `(ProductId, FamilyId)` como identidad del juicio, borrado en cascada desde la familia, y que **es a la vez la lista de descartes y el sello de aprobación por ítem**; **`GET /api/product-families`** paginado y **`DELETE /api/product-families/{id}`**, que hoy no existen; `POST /api/ai/catalog/family-audit` y `.../family-verdicts`; **`materials.synonyms` += `dorado: baño de oro`**, que recupera familias sin reenriquecer, con diff completo de propuestas antes de aceptarlo; y la **pantalla de revisión** en frontend —tabla, confirmación en bloque, cronómetro por ítem— de la que **C28 extraerá lo que le sirva**. *(Corregido el 1 sep: no se extrajo carcasa alguna, y los atajos de teclado se descopan a C28. Ver las revisiones fechadas de las decisiones 5 y 12 del `design.md`.)* Se **reaprueban las 156** ítem a ítem, y el informe del lote publica tasa de corrección del agrupador y tiempo medio.

**Fuera de alcance.** Ampliar `piece_type.terms` y el salto a `enrichment/v2` — es `fix-enrichment-vocabulary-gaps`, propuesto en el §0 y **sin número** *(no es C20, que es el diccionario de sinónimos **de consulta**)*; reenriquecer producto alguno; tocar la fusión por material, la guarda de raíz degenerada o el rango canónico de tallas; persistir propuestas de `suggest`; `source-text/v1`, `embedding_version` e `indexing/embeddings.py`; y la pantalla de perfiles y su endpoint de métricas (**C28**).

**Un requisito que estuvo fuera y volvió, el mismo día.** El comportamiento con `jbg-ai` caído se recortó dejándolo sólo en el cliente .NET, y se revirtió al ver que ahí no alcanza: **una lista vacía pintada sin más *es* la respuesta equivocada**, la distinga o no la capa de debajo. La pantalla distingue **tres estados por lista** —calculada y vacía, no disponible, con contenido—, y la revisión de familias sigue operativa mientras la auditoría no lo esté, porque no usa vectores. Es el riesgo de C17 trasladado aquí, y sobre una pantalla de calidad de catálogo *«no hay nada que revisar»* se lee como *«el catálogo está limpio»*: justo la conclusión que este change existe para sostener con evidencia.

**Orden.** Cambia pertenencias y `preprocessing_id` sigue siendo `source-text/v1`, que no delataría el movimiento: **antes de la línea base de C24**. Barato de cumplir, porque **confirmar sin cambiar no mueve el corpus**.

**Tests.** `test_audit_flags_member_when_stranger_beats_worst_sibling`; `test_orphan_detection_lists_unassigned_similar_products`; `test_orphan_nomination_never_crosses_piece_type`; `test_audit_writes_nothing`; `Verdict_DismissedPair_ExcludedFromNextAudit`; `DeleteFamily_CascadesVerdictsAndFreesProducts`; `ListFamilies_RequiresAdministrator`; test de desfase modelo↔migración; `should keep a dismissed suggestion out of the next run`; `should show why a group was rejected`; `should show the audit as unavailable when the ai service does not answer`; `should keep family review usable when the audit is unavailable`.

> **Cierre el 2026-09-01 — lo que la revisión real cambió sobre esta ficha.**
>
> **Tres migraciones, no una.** A `AddFamilyReviewVerdict` se sumaron `AddFamilyReviewSeconds` y `AddVerdictSubjectPopulation`, ambas sobre la tabla nueva y ambas surgidas de **usar la pantalla**, no de leer el diseño: el cronómetro vivía en el estado del componente y moría con la pestaña, y la población del juicio no se puede deducir a posteriori —un miembro rechazado que se saca de su familia queda idéntico a un candidato rechazado—. La regla de migración única se respeta: son tres turnos consecutivos del mismo change sobre su propia tabla, no dos changes a la vez.
>
> **Tres huecos que sólo aparecieron al revisar de verdad**, y que entraron al alcance en lugar de irse a C28: registrar un veredicto **no movía** la pertenencia y nada lo señalaba (58 juicios, catálogo intacto, 7 decisiones sin aplicar); **no había forma de corregir la etiqueta** de un miembro ya dentro de una familia, y las cuatro correcciones hubo que hacerlas por API; y el tiempo por ítem **no se persistía**, que es justo la mitad del renglón del §16.
>
> **«Se reaprueban las 156 ítem a ítem» no se cumplió como está escrito, y no debía.** Se juzgaron **58 pares** —los 18 miembros que los vectores no sostienen y los 40 candidatos—, que es lo que la auditoría señala; las 156 se recorrieron como lista. Las 468 pertenencias no marcadas son precisamente aquellas sobre las que los vectores no tienen objeción, y juzgarlas una a una es otro trabajo.
>
> **Y dos cosas que `/opsx:verify` corrigió el 1 sep.** La tarea 6.4 estaba marcada afirmando **TanStack Table** —que no se usa, y no debe: sólo 9 de 85 pantallas lo hacen, todas listados planos— y **navegación por teclado**, que no existe y se descopa a C28. Y la decisión 12 prometía una carcasa compartida que **no se extrajo**: todo vive en un fichero de 920 líneas. De las cuatro cosas que la ficha de C28 pide por escrito, tres ya están en esa pantalla; la cuarta es el teclado.
>
> **Resultado: 17 de 18 pertenencias confirmadas (94 %) y 6 de 40 candidatos aceptados (15 %)**, 7 aplicados. **El tiempo medio no existe para esta ejecución** —la columna llegó después—, y el informe lo dice en vez de estimarlo. El hallazgo (d) de C18a se resolvió **al revés de como se predijo**: el sintético `SKU610` fue **confirmado** como miembro legítimo, así que el peor hermano no sube y la predicción de la decisión 5 del diseño queda **sin comprobar**. Todo en [`informes/c18b-family-review-report.md`](informes/c18b-family-review-report.md).

---

#### ~~C19 · `add-demand-signal-service`~~ ⛔ 🗄️

> **⛔ Anulado el 2026-08-31**, con toda su rama (C29, C33, C35, C37). No aporta nada al sistema RAG: la señal que pondera el ranking (`sales_30d`, `qty_bucket`) llega por `ai.pos_projection` desde el feed de C12, y ni C22 ni C25 dependen de este change. Lo que compraba era el segundo agente, a cambio de cinco changes de los que tres no tienen LLM. Razonamiento completo, lo que se pierde y las dos vías de rescate en el **§0 · *Se anula C19 y toda su rama***. La ficha se conserva como registro; nada de lo que sigue se implementa.
>
> **Si alguna vez se resucita:** decidir **primero** el reloj. Medido el 2026-08-31, `sales_7d` contra el reloj de pared es distinto de cero en **3 de 6.050** pares (producto, POS) activos, porque el mundo de C10 termina el 2026-08-23. Anclada al fin del mundo serían 443. Y la definición de `sales_30d` debe salir del mismo sitio que la del feed (`GetSalesAggregatesAsync`), no de una segunda copia.

**Objetivo.** Señales de demanda **en SQL, en .NET**, más el origen de suministro. Base de todo el inventario y señal de ranking para la búsqueda.
**Prereq.** C10 · **Zona.** `Domain/`, `Application/`, `Infrastructure/`
**Alcance.** **Migración: `IsSupplySource bool` en `PointOfSale`** (decidido: existe tienda central) con endpoint de administración para marcarlo. Señales por producto y POS: `sales_7d`, `sales_30d`, `sales_60d`, `current_stock`, `stock_in_other_pos`, `days_since_last_sale`, `avg_daily_sales_30d`, `estimated_days_to_stockout`, `is_top_seller_in_pos`. `GET /api/ai/inventory/demand-signals?pointOfSaleId=`. Sin LLM.
**Tests.** `Signals_ComputeSalesWindowsCorrectly`; `Signals_EstimatedDaysToStockout_HandlesZeroVelocity`; `Signals_StockInOtherPos_ExcludesTargetPos`; `Signals_TopSeller_UsesPosScopedRanking`; `PointOfSale_IsSupplySource_DefaultsToFalse`; test de migración.
**Nota de orden.** C10 genera los POS ya con la marca de origen de suministro; la importación de esos datos a la base debe ejecutarse **después** de esta migración, o repetirse tras ella.

---

### Ola 3 — Calidad, medición y base de inventario (20-26 ago)

---

#### C20 · `add-synonym-dictionary` 🟢

> **Es el siguiente change a abrir** *(fijado el 31 ago; ficha reescrita el 1 sep tras medir)*. Está pintado 🟢 pero **tapona el grafo entero**: es el único prerrequisito que le falta a C21, y C21 bloquea a la vez a C24 y a C30, o sea las dos mitades del proyecto. La marca ⏳ desaparece: sin compañero no hay acuerdo que esperar, y el flag ya era el mecanismo previsto para decidir con la medición en vez de con argumentos.
>
> **Lo que la exploración midió está en el §0.** Tres cosas que la ficha no sabía: `doc_text` ya está canonicalizado, así que la expansión tiene diana garantizada; **el stemmer español rompe `collar`/`collares` y `baño`/`bano`**, lo que hace que el diccionario no sea sólo de sinónimos; y una sola `tsquery` ensanchada **saca del top-10 los productos que el operador nombró literalmente**, lo que fija el contrato en grupos de equivalencia y no en una cadena reescrita.

**Objetivo.** Sustituir `SearchAliases` sin persistir texto por producto (decisión 4), y dar a la rama léxica de C21 la capa que la hace responder algo: sin ella, `gargantilla dorada` y `collares de plata` devuelven **cero** documentos sobre el índice real. Se implementa **tras flag** para que C24 pueda medir su efecto por ablación, no para dudar de que haga falta.
**Prereq.** C14 · **Zona.** `ai-service/src/jbg_ai/retrieval/`, lectura de `enrichment/vocabularies.yaml` (que **no se modifica**) y una CLI de medición. Sin migración, sin tocar `openapi.json`, sin `Dockerfile`.
**Alcance.** **Base + overlay**: `vocabularies.yaml` aporta las clases de equivalencia que ya existen —`sortija→anillo`, `gargantilla→collar`, `plata de ley→plata`, con dirección y tildes correctas— y `retrieval/query_synonyms.yaml`, versionado y **sólo de consulta**, añade lo que no debe entrar en el contrato de extracción: **artefactos del stemmer** (`collares`, `aros`, `bano de oro`, `pequeño`/`pequeno`), sinónimos comerciales que la base no tiene (`arete`, `criolla`, `zarcillos`, `aro de dedo`, `choker`, `dije`, `medalla`, `prendedor`, `alfiler`, `cordon`, `cuerda`, `bronce`, `acrilico`, `acero inoxidable`) y el puente `dorado` → {color `dorado`, `baño de oro`, `oro`}. **Singularización en ambos lados al cargar**, que resuelve `sortijas`, `gargantillas`, `brazaletes`, `esclavas` y `dorados` sin una entrada por forma. `expand_query` es **función pura, sin base de datos ni proveedor**, y devuelve **grupos de equivalencia más los términos resueltos** (`término → campo, canónico`), que es lo que C21 necesita para su extracción de filtros por reglas sin construir una segunda tabla de consulta. Expansión **en consulta, nunca en indexación**, y **nunca en la rama vectorial** (medido: duplicaría los embeddings sobre un cliente que aún se construye por petición). Flag con **default en `Settings` y parámetro en la firma del orquestador**, para que C24 barra configuraciones sin reiniciar y sin mover el contrato congelado. Log estructurado `stage=expand` junto a `stage=embed` y `stage=search`, y **CLI de medición que deja informe versionado** con el alcance sobre el índice real, que C24 reutiliza como categoría de sinónimos del golden set.
**Tests.** `test_query_with_synonym_matches_canonical_term`; `test_expansion_does_not_modify_indexed_documents`; `test_unknown_term_passes_through_unchanged`; `test_disabled_flag_returns_original_query`; `test_expansion_returns_groups_not_a_rewritten_string`; `test_stemmer_split_terms_are_expanded` (`collares`→`collar`, `bano de oro`→`baño de oro`); `test_plural_is_resolved_without_a_dedicated_entry`; `test_base_vocabulary_file_is_not_modified`; `test_overlay_never_overrides_a_base_canonical`; `test_expansion_makes_no_database_or_provider_call`.
**Fuera de alcance.** La rama léxica, `ts_rank` y la fusión RRF (**C21**) · `vocabularies.yaml`, el salto a `enrichment/v2` y los huecos `llavero`/`diadema`/`gemelos`/`cinturon`/`filigrana` (**`fix-enrichment-vocabulary-gaps`**) · instalar `unaccent` o crear una configuración `ts` propia, que exigiría migración porque `tsv` es columna generada · el singleton del cliente de embeddings y revertir los 2500 ms de C16 (**C21/C22**, anotado en `DEFERRED_TASKS.md`) · erratas y `pg_trgm` · `ai.query_log` · regenerar `openapi.json`.
**Exclusión con motivo medido.** `piel` → `cuero` **no entra**: los 7 documentos que casan dicen «sobre la piel», piel humana en prosa comercial, y `cuero` tiene un solo producto. Es el ejemplo de por qué el diccionario se cura y no se genera.
**Limitación a declarar.** El diccionario se cura **contra el corpus, no contra demanda observada**: `ProductSearchEvents` tiene 31 filas y 12 textos, todos escritos por el desarrollador y en vocabulario canónico. Hermana de la ausencia de acuerdo entre anotadores que C24 declara.

---

#### C21 · `add-hybrid-search-rrf` 🟢

**Hecho (2026-09-02).** Rama léxica sobre `tsv` y **fusión RRF ponderada de tres listas** —la tecleada con `websearch_to_tsquery`, la expandida con `plainto_tsquery` por forma emitida, y la vectorial— a profundidad simétrica acoplada a `k`. **La medición refutó tres puntos de esta ficha**: el *boost* de SKU y nombre exacto no compra nada —un nombre exacto ya encabeza las dos listas léxicas, y ante un SKU la rama vectorial devuelve **cero** candidatos—, `@>` para multi-material es un precipicio de recall —60 documentos frente a 913, con 126 documentos sin materiales extraídos— y la conjunción estricta entre grupos deja **7 de las 10** consultas reales en cero documentos. Los filtros deducidos del texto **degradan y nunca excluyen**; los del body siguen excluyendo. La coordinación sólo cuenta los campos cuya ausencia es evidencia, con lo que una consulta subjetiva queda en manos de la rama vectorial sin un segundo peso que calibrar. `mode` deja de mentir y desaparece `vector_only_until_c21`; `match_reasons` lleva procedencia real por resultado; `score` pasa a RRF normalizado, declarado **no comparable** con lo persistido antes; `low_confidence` es desacuerdo entre ramas **sólo cuando corrieron dos**. Cliente de embeddings **singleton con caché acotado**, sin descongelar `embeddings.py`: baja la latencia en caliente a **76 ms** frente a 273-1328 ms en frío. Medido sobre 24 consultas del índice real (12 curadas + 12 grabadas): vector-only **157/240**, lexical-only **219/240**, **fusión 224/240**. Sin migración, sin tocar `openapi.json` y sin tocar `backend/`. Specs vivas `hybrid-fusion` (**nueva**), `vector-retrieval`, `query-expansion`, `assisted-search-panel` y `ai-service-runtime`. Change [`2026-09-02-add-hybrid-search-rrf`](../../openspec/changes/archive/2026-09-02-add-hybrid-search-rrf/).

**Objetivo.** Rama léxica + fusión RRF + filtros estructurales por reglas, incluido el **filtro por solape de materiales**.
**Prereq.** C14, C20 · **Zona.** `ai-service/src/jbg_ai/retrieval/`
**Alcance.** `ts_rank` en español sobre `tsv` con expansión de sinónimos; *boost* de SKU y nombre exacto; fusión RRF con `k` configurable; `match_reasons` por resultado; extracción **por reglas** de filtros (`menos de 80`, `talla M`, materiales del vocabulario); **`materials && ARRAY[...]`** por defecto y **`@>`** cuando la consulta nombra varios.
**Tests.** `test_exact_sku_query_ranks_target_first`; `test_rrf_fuses_ranked_lists_preserving_top_hit`; `test_material_filter_uses_overlap_by_default`; `test_multi_material_query_uses_contains_all`; `test_extracts_price_ceiling_from_natural_phrase`; `test_never_invents_filter_absent_from_query`.

---

#### FIX1 · `fix-enrichment-vocabulary-gaps` 🟢 archivado el 5 sep

> **Fuera de la numeración C por decisión propia** *(fijado el 1 sep)*. No sale de la descomposición original del proyecto sino de un hallazgo de C18a, y darle un número C sugeriría que estaba planificado. Lleva ficha porque **exige change propio**, no porque sea una ola más.
>
> **Por qué exige change y no un commit suelto.** Cambia el **contenido normativo de una spec viva**: `openspec/specs/catalog-enrichment-pipeline/spec.md` enumera en un MUST los ocho `piece_type` canónicos, y un escenario suyo fija `prompt_version` = `enrichment/v1`. Añadir cuatro términos y saltar a `v2` deja las dos frases mintiendo — y `openspec validate --all --strict` **seguiría en verde**, porque valida estructura y no verdad. Sería peor que las tres specs malformadas de agosto: aquéllas rompían el formato y el validador las cazó; ésta quedaría bien formada y falsa. La única vía sancionada para mover una spec viva es una delta spec dentro de un change. Se suman dos razones menores que apuntan igual: **mueve el corpus** —reenriquecer cambia `ProductAiProfile`, `doc_text`, `source_hash` y los embeddings de esos productos: es una migración de datos aunque no lleve Alembic— y es **multicomponente**, porque toca el espejo del frontend.

**Objetivo.** Dar nombre a lo que el vocabulario cerrado no sabe nombrar, y arreglar la laguna del enunciado del prompt que la revisión de C18a diagnosticó: el prompt abre con *«Eres un extractor de atributos de joyería»* y no contempla que el catálogo contenga otra cosa, así que ante `Arreglos oro` conjetura *collar* porque es exactamente lo que se le pidió.
**Prereq.** C21 · **Zona.** `ai-service/src/jbg_ai/enrichment/`, `ai-service/prompts/enrichment/`, `frontend/src/lib/`, y una pasada de reenriquecimiento por `backend/`. **Sin migración.**
**Población. La ficha decía 11 y son 22** *(refutado por la exploración del 5 sep)*. Los 11 sin `piece_type` estaban bien contados, pero eran la mitad honesta del problema: hay **otros 9 mal tipados**, y un tipo erróneo es peor que un nulo porque el filtro de categoría es duro (`AND d.piece_type = :category`), de modo que **seis de los 85 `broche` eran tres diademas, dos gemelos y un llavero**, más dos diademas en `collar` y una en `colgante`. Reenriquecer sólo los once habría entregado una faceta «Diadema» que devuelve **5 de 11** — la firma de C17 en su versión peor: no dice cero, dice cinco. La cohorte son los **22**, con **`Broche Cinturón de Orión` (SKU822) y `Anillo Cinturón de Orión` (SKU882) como grupo de control que debía no moverse** — «Cinturón de Orión» es la constelación, un falso amigo medido de la familia de `piel → cuero`.
**Alcance entregado.** `piece_type.terms` += `diadema`, `gemelos`, `cinturon` y **`llavero`**; prompt **`enrichment/v2`** con la lista nueva más la línea que advierte de servicios, consumibles y regalo; **`load_prompt()` deriva su ruta de `PROMPT_VERSION`**, que hasta entonces se declaraban por separado y podían sellar un perfil con una versión que no lo produjo; espejo `materials-vocabulary.ts` a doce opciones y su test de fijación; reenriquecer **los 22** con **`Force`** *(el §0 lo llamaba `ignoreHash`, que no existe: la bandera real es `request.Force` en `AiCatalogController`)*; una sola sincronización incremental; **cierre de las cuatro exclusiones del overlay de C20** y forma de superficie `gemelo`; y **dos deltas de specs vivas y no una** — `catalog-enrichment-pipeline` y `query-expansion`.
**Tests. Los alambres que saltan eran cuatro, no dos** *(refutado)*. A `test_base_vocabulary_terms_are_pinned` y `materials-vocabulary.test.ts` se suman `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in`, que exigía los cuatro términos en las exclusiones del overlay, y sobre todo **`test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap`, que usaba `diadema` como ejemplo de canónico desconocido y falla con `DID NOT RAISE`** — la dirección contraria a la esperada, que es justo la que invita a borrar el test. No se borró: es el guardián que impide que una laguna entre como sinónimo, y su ejemplo pasa a `filigrana`, que sigue abierta. Entregados además siete tests nuevos (697 → 704), entre ellos el que fija que el encabezado del prompt cargado coincide con `PROMPT_VERSION` y el que cruza la lista escrita en el prompt contra el YAML.
**Fuera de alcance.** **Reenriquecer los 1.200 con `v2`** — serían ~1.200 llamadas y, peor, podría **reclasificar productos existentes** cambiando el comportamiento de búsqueda de forma difusa y sin que nadie lo pidiera. Tampoco: `source-text/v1`, `embedding_version`, `indexing/embeddings.py`, ni el diccionario de consulta de C20, que es de otra capa.
**Cuándo, y por qué ahí.** **Después de C21 y antes de la línea base de C24.** No dentro de C21: ese change tiene que calibrar RRF y `ts_rank` **contra un corpus quieto**, y meterle dentro algo que mueve documentos es calibrar sobre arena. No antes de C21, por la regla 2 del §1 —*prioridad al desbloqueo*—: C21 abre C24, C25 y C30, y esto no abre ninguna arista, es una hoja. Y hay un motivo mejor: **antes de C21 esta corrección no se puede medir**, porque la rama léxica todavía no existe y los once productos ganarían `piece_type` sin que nadie pueda enseñar que sirve de algo — la firma que este proyecto persigue desde C17. **Y aquí la ficha se refutó a sí misma:** *«buscar «diadema» pasa de cero a resultados»* **ya se cumplía antes del change**, porque la rama léxica de C21 alcanza los 11 documentos por el nombre, que vive en `doc_text` — un verificador lo habría firmado verde por el motivo equivocado. Los criterios se reescribieron como **estructurales**: nulos 11 → 1, faceta `diadema` 0 → 11, impostores en `broche` 6 → 0. El plazo duro sigue siendo el del §0: antes de que C24 etiquete, porque `preprocessing_id` sigue siendo `source-text/v1` y no delataría el cambio.
**Riesgo a comprobar, no a suponer.** Reenriquecer con `v2` puede cambiar **otros campos** de esos once —materiales, etiquetas— además del tipo. Hay que mirar el diff completo, no sólo `piece_type`.
**Recortable.** No entraba en la lista de nunca-recortar del §6: son 22 productos, el **1,9 %** del corpus, y la mayoría sintéticos. Si se cae, C24 etiqueta un corpus donde once piezas no tienen tipo, y eso se declara como limitación en vez de fingirse.
**Coste real.** Cinco ficheros de código, cuatro tests fijados, dos lenguajes y dos deltas de specs vivas, para cuatro términos — la medición de lo que cuesta mover un vocabulario replicado en cinco sitios. Sin migración, sin tocar `openapi.json` y sin mover `source-text/v1` ni `embedding_version`. La corrida encontró además lo que ningún test podía encontrar: la línea nueva sobre servicios, consumibles y regalo dejó sin tipo a dos de los tres llaveros —**un llavero *es* un artículo de regalo**—, así que `v2` declara la precedencia de la lista cerrada sobre esa advertencia y la cohorte se volvió a correr entera. Informe en [`fix1-vocabulary-gaps-measurements.md`](informes/fix1-vocabulary-gaps-measurements.md).

---

#### C22 · `add-pos-projection-soft-prefilter` 🟢 archivado el 5 sep

**Objetivo.** La proyección acota por surtido y **degrada por stock sin excluir**. Es la decisión 11 de la revisión y la corrección técnica más importante de esta versión.
**Prereq.** C10, C12, C14 · **Zona.** `ai-service/src/jbg_ai/retrieval/`, `indexing/` **y `backend/src/JoiabagurPV.Application`** (el reloj inyectado cruzó de lenguaje)
**Alcance entregado.** Sincronización de `ai.pos_projection` desde el feed con cursor propio bajo `feed = 'pos-availability'` y CLI `python -m jbg_ai.indexing sync-pos` —sin ruta `/v1` y sin planificador—; el único filtro duro es el **`pos_id` del token**, aplicado en SQL a las tres ramas; `qty_bucket = '0'` **degrada** como último bloque de `demotion_rank`; `projection_age_seconds` sale del checkpoint y **gobierna** (vacía → 503, obsoleta → deja de filtrar y lo declara); y el reloj inyectado `IndexFeed:SalesAsOf = 2026-08-23T23:59:59Z` con `computedAsOf` en la página del feed.

**Tres puntos de la ficha refutados con medición**, y por eso el alcance no es el que este plan preveía:

- El filtro duro correcto es **`is_assigned_hint`, no la existencia de fila**: `Carried()` de .NET excluye exactamente eso, así que un desasignado mantenido gastaría ventana para nada — el 7-9 % en los puntos de venta con operador. Lo que degrada sin eliminar es el **stock**, y MAO-AIR tiene el 34,4 % de su surtido a cero. En consecuencia `test_unassigned_product_is_penalised_not_removed` se renombra a **`test_out_of_stock_product_is_penalised_not_removed`**: protege el principio que está realmente en vigor.
- La página corta **no era de FORNELLS** sino de **ocho de los once** puntos de venta. Tras el change, ninguno.
- El índice HNSW **nunca se ha usado en la ruta viva**, así que escopar con CTE no cambia de motor. Lo que justifica esa forma no es la velocidad —medida, 14,8-17,3 ms frente a 18,0-33,1 ms— sino la corrección: el subconjunto existe antes de ordenar.

**Y una desviación declarada:** el change **abre una revisión de Alembic aditiva** (`ai.pos_projection.computed_as_of`), contra el «sin migración de ninguna clase» que declaraban su ficha, su HU y su propuesta. La tabla no tenía dónde persistir el instante de referencia que el propio alcance exige, y como el drenaje es incremental, sin esa columna la proyección puede acabar con filas contadas contra dos relojes distintos e indistinguibles.

**Tests.** `test_out_of_stock_product_is_penalised_not_removed`; `test_pos_scope_from_token_is_hard_filter` (como `test_candidates_come_only_from_the_assortment`); `test_projection_stores_bucket_not_exact_quantity`; `test_response_reports_projection_age`; más los de .NET del reloj inyectado (`SalesAggregates_WithConfiguredAsOf_CountWindowsAgainstIt`, `SalesAggregates_WithoutAsOf_FallBackToWallClock`, `PosAvailabilityPage_DeclaresComputedAsOf`).
**Informe.** [`c22-implementation-measurements.md`](informes/c22-implementation-measurements.md).

---

#### C23 · `add-knowledge-corpus-and-indexer` 🟢 archivado el 6 sep

**Objetivo.** Segundo índice: conocimiento comercial **general, no por producto** — lo que permite citas verificables sin violar la decisión 4.
**Prereq.** C11 · **Zona.** `ai-service/src/jbg_ai/knowledge/` —paquete propio, desviación declarada en D9: la ficha asignaba zona solo de indexación y a la vez pedía un test de búsqueda—, más `data/knowledge/` y un subcomando en `indexing/cli.py`
**Alcance.** 32 documentos y 161 secciones: **fichas por material** (cuidados, alergias, durabilidad), equivalencias de talla, política de devoluciones, FAQ, piedras, glosario y origen de las colecciones; chunking por secciones; indexación en `ai.knowledge_chunk` reutilizando el cliente de C11. **Cero guiones de venta**, y no por recorte de alcance (D13): un guion es texto imperativo, y un fragmento imperativo recuperado dentro de un prompt es indistinguible de una instrucción, lo que convertiría al propio corpus en superficie de inyección con C31 todavía sin existir. Cada sección declara su `claim_scope`, y esa marca viaja con el fragmento recuperado.
**Tests.** `test_chunker_preserves_section_titles_in_metadata`; `test_every_chunk_has_traceable_document_id`; `test_material_sheet_is_not_product_scoped`; `test_knowledge_search_returns_chunk_with_citation_id`.
**Conflicto de zona.** Usa el paquete `knowledge/`; `indexing/knowledge.py` nunca llegó a existir. No toca `indexing/products.py` ni `indexing/embeddings.py` (congelado en C11, y con un test que compara su SHA-256).

---

#### C24 · `add-eval-harness-golden-set-and-baselines` ✅ *(archivado el 2026-09-11)*

> **El doble etiquetado no existe** *(corregido el 31 ago)*. La ficha lo daba por hecho entre dos personas y el §6 lo declaraba irrenunciable; con un solo anotador, el sustituto no es fingirlo. Se etiqueta **una vez**, se conserva el *pooling* sobre la unión de configuraciones, se añade **relectura diferida** de las consultas etiquetadas con dudas, y el README declara la **ausencia de acuerdo entre anotadores** como limitación del golden set en lugar de reclamar una mitigación que no se aplicó.

**Objetivo.** Convertir "parece que va mejor" en números.
**Prereq.** C14, C21 · **Zona.** `ai-service/src/jbg_ai/evals/`
**Alcance.** Tablas `ai.eval_run/case/result`; golden set de **60-70 consultas** en 9 categorías (incluidas **materiales multi-valor** y **sinónimos**), relevancia graduada 0-2, construido por *pooling* y **etiquetado una sola vez, con relectura diferida de las dudosas**; **se etiqueta primero sobre productos reales** y solo se completa con sintéticos si no hay material para cubrir las categorías; CLI `uv run evals run --config vX`; métricas Recall@5, nDCG@5, MRR, P@3, abstención, p50/p95, coste, **reportadas por `data_origin` (real / sintético / global)**; configs `v0-lexico` (replica el buscador .NET actual — **es la comparación que pide la decisión 12**) y `v0-cag`; informe versionado en `ai-service/evals/results/`.
**Tests.** `test_ndcg_matches_hand_computed_value_on_fixture`; `test_run_is_reproducible_for_same_config_and_seed`; `test_metrics_reported_per_data_origin`; `test_lexical_baseline_matches_dotnet_search_semantics`; `test_cag_baseline_respects_context_budget`; `test_cost_per_query_recorded_per_config`.
**Planificación.** Dos sesiones: runner y configs, y etiquetado. **Tope de 2 h en etiquetado**; superado, se recorta a 45 consultas antes que alargarlo, porque un etiquetador cansado y único es exactamente el fallo que el doble etiquetado ya no puede corregir.
**Criterio de aceptación.** El umbral se aplica a **la porción real**. Si el global cumple y el real no, la conclusión es que el corpus sintético es demasiado fácil.

---

#### C25 · `recalibrate-ranking-and-abstention` ✅ *(archivado el 2026-09-12)*

> **Renombrado desde `add-business-signals-ranking`** *(11 sep)*: el nombre anterior describía un tercio de lo que acabó haciendo. El número se conserva porque renumerar rompería las referencias de C26 (`prereq C22, C25`) y C27 (`C10, C25`) a cambio de nada. La narrativa completa, con las cifras, está en la entrada del §0 del 2026-09-11.

**Objetivo.** Disponibilidad, rotación y perfil de POS como reordenación suave, con pesos **calibrados contra el golden set**.
**Prereq.** C21, C22, C24 · **Zona.** `ai-service/src/jbg_ai/retrieval/` y `ai-service/src/jbg_ai/evals/`. **Sin migración, sin `openapi.json` y sin diff fuera de `ai-service/`.**
**Alcance entregado.** El objetivo de arriba sobrevivió a medias, porque la exploración encontró **un defecto que valía más que toda la ficha: la fusión de C21 no fusionaba, concatenaba**, y los 60 documentos léxicos ganaban al mejor acierto vectorial en toda consulta. Entra por delante la **fusión en dos etapas con pesos por rama** (+0,083 en la lectura que decide), la **ponderación adaptativa por cobertura sin parámetros**, la señal de POS **separada del alcance** (`LEFT JOIN` que lee frente a `INNER JOIN` que restringe), el **score continuo en el último bloque** de la clave, la métrica **`nDCG@5 operativo`**, el barrido en dos fases `capture`/`rescore`, la **abstención relativa por consulta** y la tabla de ablations de **seis filas**.
**Tres puntos de la ficha, retirados por medición y no por argumento.** La **penalización de variante ambigua** (D16: sólo 2 de 156 familias pueden llenar cinco huecos, y diversificar **baja** el nDCG@5 — es presentación, y pertenece a C30/C36); la **calibración de `1-2` frente a `3+`** (D17: no tiene función objetivo posible, porque ninguno de los dos pierde grado); y la **rotación como criterio de orden** (D10, refutada durante el apply: como desempate estricto decidía **cero** pares del top-5, y como clave de ordenación particionaba, invirtiendo 11.067). `sales_30d` se sigue leyendo **para diagnóstico** y no ordena nada.
**Y la re-fijación del umbral no fue una re-fijación.** El escalar no podía servir: el mejor acierto por consulta de las contestables llega a 0,7118 y el de las imposibles arranca en 0,4469, o sea **contención total y no solape parcial**. La regla adoptada es **relativa por consulta**, corre después de la fusión y **no altera el conjunto de candidatos**. El escalar se queda donde estaba, ahora por decisión y no por aplazamiento.
**Tests.** `test_out_of_stock_product_ranks_below_equivalent_in_stock`; `test_weights_load_from_config_not_hardcoded`; `test_calibration_sweep_is_reproducible` *(ahora estructural)*. `test_ambiguous_variant_penalty_applies_only_within_family` **no se escribe**: su requisito se retiró. Entran en su lugar `test_branch_vote_is_independent_of_how_many_of_its_lists_matched`, `test_signal_join_never_restricts_the_candidate_set`, `test_rotation_does_not_order_anything` y `test_window_captured_under_a_different_fusion_is_refused`. Suite en **994**.
**Tres listones no se alcanzan, y se declaran en vez de cerrarse.** `Recall@5` **0,758** contra 0,85; abstención **0,150** contra 0,80 —llegar a 0,80 costaría silenciar 21 de las 43 contestables—; y `v3-senales` no bate a `v2b-fusion` por el margen (**+0,030** operativo) aunque cumple su propia regla de adopción. Informes en [`c25-exploration-measurements.md`](informes/c25-exploration-measurements.md) y [`c25-implementation-measurements.md`](informes/c25-implementation-measurements.md); tabla en [`c25-baselines-2026-09-11.md`](../../ai-service/evals/results/c25-baselines-2026-09-11.md).
**Deja abierto C25bis**, que retira el andamio que este change tuvo que conservar.

---

#### C25bis · `clean-plain-fusion` ✅ *(creado el 2026-09-11, desbloqueado e implementado el 12)*

> **Fuera de la numeración C por el mismo motivo que `FIX1`** *(fijado el 11 sep)*. No sale de la descomposición original del proyecto sino de una **consecuencia de C25**, y darle un número C sugeriría que estaba planificado. Lleva ficha porque **exige change propio**: retira requisitos de dos specs vivas —`hybrid-fusion` y `retrieval-evaluation`— y la única vía sancionada para mover una spec viva es una delta dentro de un change.

**Objetivo.** Retirar el andamio que C25 tuvo que conservar. Aquél **mantiene la fusión plana como modo seleccionable** porque sin ella la fila `v2-hibrido` de la tabla de ablations deja de ser reproducible, y con ella se pierde la referencia contra la que se leen todas las demás filas. Publicada la tabla y congelada la configuración, ese modo pasa a ser lo contrario de lo que era: **un camino muerto, activable por error, cuya aritmética el proyecto midió como defectuosa** — los 60 documentos léxicos ganando al mejor candidato vectorial en toda consulta, y el grado 2 cayendo a la posición 33.
**Prereq.** C25 **archivado** — prerrequisito duro, cumplido el 2026-09-12 · **Zona.** `ai-service/src/jbg_ai/retrieval/`, `ai-service/src/jbg_ai/evals/` y `ai-service/evals/configs/`. **Sin migración, sin contrato y sin diff fuera de `ai-service/`.**
**Alcance.** Retirar `JPV_FUSION_MODE` y la rama plana del orquestador; retirar la variante de ponderación adaptativa que perdió el barrido y las perillas que queden sin lector, con un **inventario comprobado por búsqueda y no por memoria** — este subsistema ya sorprendió cuatro veces con cables calculados y sin consumidor (`tsv`, la expansión, `qty_bucket` y `coordination`), y aquí el riesgo es el simétrico: retirar algo que sí tenía lector.
**Acepta un coste y lo declara.** La fila de la línea base deja de poder re-medirse y pasa a ser **histórica y citable** —su informe y su JSONL por consulta quedan versionados—, porque la alternativa era mantener vivo un camino medido como roto, y un camino muerto que se puede activar por error es cómo un defecto corregido regresa.
**No re-mide nada y no tiene autoridad para mover una cifra.** Su criterio de verificación es que las filas supervivientes den cifras **idénticas** tras el borrado; cualquier diferencia es un fallo del change que se revierte, no un resultado que discutir.
**Cuándo, y por qué ahí.** Sólo cuando la decisión de fusión esté congelada y publicada, y lo está desde el archivado de C25. No antes: mientras la tabla siga pudiendo re-correrse, la fila plana es la referencia y no el andamio. Es una **hoja** —no abre ninguna arista—, así que por la regla 2 del §1 cede el turno a C26, que sí desbloquea.
**Tres puntos de su ficha, refutados por comprobación y no por argumento** *(2026-09-12)*. Los pesos por lista **no** los consumía sólo el modo plano —dos de los tres alimentaban la etapa 1 viva, y se retiran por ser **trampas** que la spec prohíbe mover, no por estar muertos—; la **variante adaptativa perdedora no existe**, porque se retiró dentro de C25 y hay un test que falla si vuelve; y el **fallo al arranque** no es alcanzable con `extra="ignore"` y tendría más radio de daño que el defecto que previene, así que la obligación se acota a la configuración de evaluación, donde ya estaba implementada. Detalle en [`c25bis-exploration-decisions.md`](informes/c25bis-exploration-decisions.md).

**Lo entregado.** Retirados `JPV_FUSION_MODE` y los tres pesos por lista; la etapa 1 queda con pesos **iguales declarados en el módulo**; `Provenance.fusion_mode` **se conserva** poblado desde constante —*el selector muere, el registro vive*—; `v2-hibrido.yaml` se mueve a `evals/configs/retired/` y deja de cargar, por diseño; y la aritmética del defecto sobrevive como **fósil en un test** sobre `fuse()`, que ninguna configuración puede alcanzar. Seis deltas de specs vivas, ninguna perdiendo escenarios sin decirlo.

**Verificado con las cifras delante.** Las **315 filas** por consulta de las cinco configuraciones supervivientes son **idénticas** antes y después, listas de resultados incluidas; el único elemento de la procedencia que difiere es la revisión del código. Suite **994 → 997 con cero fallos** a los dos lados. Sin migración, sin contrato, sin diff fuera de `ai-service/`, `Documentos/` y `openspec/`.

**Estado.** **45/45 tareas**, pendiente de verificar y archivar. Change [`clean-plain-fusion`](../../openspec/changes/archive/2026-09-12-clean-plain-fusion/) · informe en [`c25bis-implementation-measurements.md`](informes/c25bis-implementation-measurements.md).

---

#### C26 · `add-substitutes-retrieval` 🟢 *(implementado el 2026-09-12; pendiente de archivar)*

**Objetivo.** Sustitutos por falta de stock, con señales explicables. Cierra el último **501 cerrable** del contrato congelado y hace real la tool `buscar_sustitutos` de C32a.
**Prereq.** C22, C25, ambos archivados · **Zona.** `ai-service/src/jbg_ai/retrieval/` **+ `evals/` + `evals/golden/`** — **decimocuarta vez** que la zona de una ficha se queda corta. Sin migración, sin mover `openapi.json`, sin diff fuera de `ai-service/`, `Documentos/` y `openspec/`, y **sin una sola llamada al proveedor**: sustituto es producto→producto y el embedding de origen ya está almacenado.
**Alcance.** `POST /v1/retrieval/substitutes` en módulo nuevo `substitutes.py`: **filtro duro por `piece_type`**, orden por similitud vectorial sobre el embedding almacenado, **degradación suave por talla** y degradación por disponibilidad reutilizando `business_score` de C25; `similarity_signals` y `match_reasons` por candidato. Cinco consultas del golden set ancladas con `source_product_id` y medidas en **rebanada separada**.

> **Tres puntos de esta ficha, refutados por medición** *(2026-09-12)*. **«Misma familia primero» está invertida**: la familia es, por construcción, el conjunto de piezas que se diferencian **justo en el atributo que descalifica** —la talla—, y para `SKU13` el top-5 del vector puro **no contiene un solo sustituto usable**. Pero excluirla perdería el #1 de `SKU159`, que es su hermano de **misma talla y otro material**: la pertenencia a familia es **ortogonal** y el discriminante es la talla. Lo confirma `criterion.md`, que ya clasificaba «falla la talla nombrada» como **grado 1 — segunda opción**. La familia entra en el conjunto **sin imponer orden**, y la talla va como **término continuo en la cola** (`w ≈ 0,05`, barrido), **inerte si alguna de las dos piezas no declara talla** —el 54 % de los anillos no tiene `size_label`—. **No se reutiliza `demotion_rank`**: su bloque entero de talla particiona, el fallo exacto que C25 midió con la rotación. Y **la exclusión por stock sale de aquí**: estaba especificada dos veces y la cubre C34, donde vive la autoridad sobre el stock. Detalle en [`c26-exploration-measurements.md`](informes/c26-exploration-measurements.md).

> **Lo entregado, y en qué se desvía de la ficha** *(2026-09-12)*. Detalle y cifras en
> [`c26-implementation-measurements.md`](informes/c26-implementation-measurements.md).
>
> - **`w_size = 0,05` sale del barrido y no del argumento**, once puntos de rejilla sobre las
>   cinco consultas. El término hace algo —de `0` a `0,05`, **+0,1039 de nDCG@5**—, con lo que
>   la conclusión de C25 *«el valor del peso no cambia el orden, sólo su signo»* queda
>   confirmada como **no trasladable**. Las dos lecturas **discrepan**: el nDCG graduado premia
>   `0,075`, pero a partir de `0,07` la lectura binaria cae de 1,0000 a 0,9738 y `Recall@5` de
>   0,4241 a 0,4135, porque entra `SKU334 Anillo plata M` —talla correcta y nada más, el grado 0
>   explícito de `criterion.md`— en un top-5. Bajo el guardarraíl de C25 el mejor punto que no
>   degrada es `0,06`, que supera a `0,05` en **0,0051** por un solo intercambio de posiciones
>   en una consulta: bajo el ruido, así que se aplica la regla declarada y gana `0,05`.
> - **El bloque entero, medido.** Reordenando los diez vecinos reales de `SKU13` con la clave de
>   bloque, el hermano más cercano cae del puesto 1 al **4** —detrás de un anillo que está al
>   doble de distancia— y el más lejano sale de la ventana. Con el término continuo, puestos 1 y
>   5. `test_different_size_sibling_stays_inside_the_visible_window` falla las dos aserciones
>   bajo el bloque, que es lo que lo hace un test y no una decoración.
> - **La tarea 6.7 pasó de verificar a corregir.** Los ficheros publicados no cambian, pero el
>   *runner* iteraba `judged_queries`, que subió de **63 a 68** al etiquetar las cinco consultas:
>   una re-ejecución de la tabla de C24/C25 habría absorbido consultas que `v0-fts` y `v0-nombre`
>   **no pueden ejecutar**. Se añadió `GoldenSet.retrieval_queries` y la separación queda en
>   código, no en una convención. Antes de C26 los dos conjuntos coincidían, así que el alcance
>   era correcto **por accidente**.
> - **La edad de la proyección viaja en `debug.notes`**, no en un campo de respuesta:
>   `SubstitutesResponse` no tiene `projection_age_seconds` —`RetrievalResponse` sí— y el
>   contrato no se mueve. `debug` ya está en el contrato congelado.
> - **`match_reasons` declara además la banda de precio cuando difiere**, que es la decisión
>   aplicada de la pregunta abierta 2; sin ella `price_band` no tendría lector. Y
>   **`material_overlap` entra como desempate estricto**, no como cuarto término: fijar cuánta
>   similitud vale un material compartido es un peso que ninguna consulta puede calibrar.
> - **Sesgo declarado:** el etiquetado de las 126 parejas lo hizo quien diseñó el orden. Lo
>   acota que la rúbrica es del 2026-09-07 —anterior al change, y ya nombraba la talla como
>   degradador a grado 1— y que se etiquetó sobre **atributos** y nunca sobre posiciones. No lo
>   elimina. Y el barrido lo deciden **2 de las 5 consultas**: las otras tres no tienen talla.
> - **Suite:** 997 → **1038 passed, 0 failed**. `openspec validate --all --strict`: **55/0**.
>   `openapi.json`, `evals/results/` y `evals/configs/` **sin diff**; 126 juicios añadidos y
>   **0 borrados**.

**Tests.** `test_no_live_family_member_is_dropped_from_the_result` *(sustituye a `test_same_family_variant_ranks_first_when_available`)*; `test_same_size_candidate_outranks_same_family_different_size`; `test_different_size_sibling_stays_inside_the_visible_window`; `test_size_term_is_inert_when_either_side_declares_no_size`; `test_never_returns_a_different_piece_type`; `test_material_overlap_increases_similarity_score`; `test_out_of_stock_candidate_is_demoted_and_never_removed`; `test_substitutes_never_abstains_and_says_so`; `test_style_similarity_absence_is_declared_in_match_reasons`; `test_no_embedding_provider_call_is_made`; `test_unknown_or_unindexed_source_product_is_an_explicit_error`; `test_source_product_never_returned_as_own_substitute`. **`test_excludes_out_of_stock_when_flag_enabled` no se escribe**: su requisito se retiró. Entregados **los doce**, en `tests/retrieval/test_substitutes.py`, más `tests/api/test_substitutes_route.py` y `tests/evals/test_substitutes_slice.py`.

**Artefactos.** Historia [HU-AIENG-026](../Historias/AI-Eng/HU-AIENG-026.md) · ticket [T-AIENG-026](../../openspec/changes/archive/2026-09-12-add-substitutes-retrieval/ticket.md) · mediciones [`c26-exploration-measurements.md`](informes/c26-exploration-measurements.md) y [`c26-implementation-measurements.md`](informes/c26-implementation-measurements.md) · rebanada [`c26-substitutes-slice.md`](../../ai-service/evals/results/c26-substitutes-slice.md) · change [`add-substitutes-retrieval`](../../openspec/changes/archive/2026-09-12-add-substitutes-retrieval/), rama `c26-add-substitutes-retrieval`.

---

#### ~~C27 · `add-complementary-recommendations`~~ ⛔ 🗄️

> **⛔ Corte nº 1 disparado el 2026-09-12, con medición y no por juicio de plazo.** Estaba pre-autorizado desde el 31 de agosto con el disparador *«si el núcleo peligra»*; con prórroga abierta ese disparador no decide nada, así que se sustituyó por uno de evidencia. Las cinco mediciones están en el §0 y en [`c27-cut-measurements.md`](informes/c27-cut-measurements.md). En resumen: **el simulador de C10 no tiene modelo de afinidad** —`_pack_operations` baraja y luego escoge deliberadamente lo de lexema o colección distinta, así que la co-ocurrencia está sesgada **en contra** de lo que se le pide medir—; **98,6 % de los 4.078 pares se han visto una sola vez** y ninguno tres, con **39,6 % de productos sin ningún socio**; el solape de `color_tags`/`style_tags` está indefinido para el 74,7 % del catálogo y para **403 de 404 productos reales**; **no existe categoría de complementarios en el golden set** ni en la tabla del §11.1 del diseño, así que el change no puede añadir una sola fila a la evaluación; y **no hay ventas reales**, sólo las 22.968 de C10. Lo que quedaría en pie es `WHERE piece_type <> :tipo AND price_band IN (…) AND stock > 0`, sin una llamada a un LLM.
>
> **Qué se conserva:** esta ficha, la tabla `ai.co_occurrence` vacía de C05 (no cuesta nada y es el enganche futuro) y [`cooccurrence.py`](../../ai-service/src/jbg_ai/data/world/cooccurrence.py) con su test — deriva correctamente lo que se le pide, el defecto está en el generador de cestas. **Qué se retira:** la tool `buscar_complementarios` de C32, la ruta `.../recommendations` y su test en C34, y el bloque «También puede encajar» de C36. **`/v1/retrieval/complementary` no se añade al contrato congelado**: un 501 menos, no uno más.
>
> **Condición de reactivación, comprobable y no opinable:** un export con histórico de ventas reales **a nivel de ticket** cuyo percentil 95 de `co_sales_count` sea **≥ 3**. Con la matriz actual ese percentil es **1**.

**Objetivo.** Complementarios por reglas + co-ocurrencia, con curación manual. Decisión 8 de la revisión.
**Prereq.** C10, C25 · **Zona.** Python + `Domain/`
**Alcance.** Regla: **distinto `piece_type`**, solape de `color_tags`/`style_tags`, banda de precio compatible, disponible en el POS; señal adicional de **co-ocurrencia** desde `ai.co_occurrence`; entidad `ProductRecommendation` en .NET **solo para pares curados manualmente** (`GeneratedBy: Manual`), que tienen prioridad sobre la regla; `POST /v1/retrieval/complementary`. **Sin upsell ni downsell.**
**Tests.** `test_complementary_never_returns_same_piece_type`; `test_co_occurrence_boosts_pair_score`; `test_manual_pair_overrides_rule_result`; `test_respects_price_band_compatibility`; .NET: test de migración.

---

#### C28 · `add-profile-review-ui-and-metrics` 🟢

**Objetivo.** Que la revisión híbrida (decisión 5) sea real y medible, no una promesa del documento.
**Prereq.** C08 · **Zona.** frontend + `Application/`
**Alcance.** Pantalla de revisión **por lotes** con tabla editable, atajos de teclado y aprobación masiva por campo; muestra confianza y `source` (`rule`/`inferred`) por campo; registra **quién revisó, cuándo y qué cambió**; endpoint de métricas que expone **tasa de corrección por campo** y **tiempo medio de revisión** para el README.
**Tests.** `should highlight inferred sensitive fields pending review`; `should record correction when material list is edited`; `Metrics_CorrectionRate_ComputedPerField`; `Metrics_ExcludesAutoBulkProfiles`.

> **Heredado de C18b el 2026-09-01 — los atajos de teclado, que C18b dio por hechos y no entregó.** La tarea 6.4 de aquel change los daba por implementados y en la pantalla no hay un solo manejador de teclado. Se descopan aquí en vez de añadirse a última hora a una pantalla ya revisada por una persona, porque la prueba que importa es **volver a recorrer una cola con ellos**, no un test que compruebe que el manejador está enganchado. Y llegan con el caso concreto delante: de las cuatro cosas que esta ficha pide por escrito, **tres ya existen** en [`family-review.tsx`](../../frontend/src/pages/admin/family-review.tsx) —tabla editable, aprobación masiva y registro de quién revisó y qué cambió—; **la carcasa compartida no se extrajo** y extraerla, si hace falta, es de C28, que es quien tendrá dos inquilinos a la vista.

> **Heredado de C18b el 2026-09-01 — dos familias manuales que nadie puede crear todavía.** C18b cierra dejando abiertas las dos raíces degeneradas que C18a delegó en una persona (D11 de aquella HU), y el motivo es que **su auditoría no puede verlas**: `Cadena plata` (SKU328), `Cadena oro` (SKU329), `Cadena baño oro` (SKU381), las tres `Cadena Barbara oro` (SKU398, SKU399, SKU401) y `Colgante Estel Cadena` (SKU295) son de `piece_type` **`cadena`, del que no existe ni una sola familia**, así que no hay contra qué calcular un margen; y `Alianzas Plata` (SKU327) con `Alianzas oro` (SKU397) son de `anillo`, pero una alianza lisa no se parece lo bastante a ningún anillo de rama ni de erizo como para ser nominada. Los nueve piden **dos familias de variante creadas a mano**, y C18b lista y disuelve familias pero **no las crea**. C28 hereda la pantalla, así que hereda el hueco: **crear una familia desde la revisión** es la pieza que falta, y estos nueve SKU son su caso de prueba real. Detalle en §8.3 de [`informes/c18b-family-review-report.md`](informes/c18b-family-review-report.md).

---

#### ~~C29 · `add-inventory-recommendation-entity`~~ ⛔ 🗄️

> **⛔ Anulado el 2026-08-31** con la rama de C19 (§0). Motor de reglas y migración, sin una sola llamada a un LLM; y su tipo `Rotate` y su tipo `Transfer` ya eran los cortes nº 2 y nº 4 del §6. Ficha conservada como registro.

**Objetivo.** Recomendaciones de inventario como entidad con ciclo de aprobación, **generadas por reglas en .NET**. Base de la decisión 6.
**Prereq.** C19 · **Zona.** `Domain/`, `Application/`, `API/Controllers/`
**Alcance.** `InventoryRecommendation` (tipo `Replenish|Transfer|Substitute|Rotate|Review`, producto, POS origen/destino, cantidad, prioridad, motivo, `SignalsJson`, estado `Proposed|Approved|Rejected|Applied|Expired`, revisor, fechas), migración; **motor de reglas en .NET** para `Replenish`, `Transfer` y `Rotate` (§10.2 del diseño); endpoints `GET`, `approve`, `reject`. Sin LLM.
**Tests.** `Rules_ReplenishWhenStockZeroAndRecentSales`; `Rules_TransferRequiresIdleSourceAndSellingTarget`; `Rules_RotateWhenIdleOverNinetyDays`; `Approve_SetsReviewerAndTimestamp`; `Reject_KeepsSignalsForAudit`; test de migración.
**Dependencia resuelta.** El POS origen de suministro existe y `IsSupplySource` llega en C19, dos olas antes.

---

### Ola 4 — Agentes, inventario asistido y evaluación (27-31 ago)

---

#### C30a · `add-assist-structure-and-rule-warnings` ✅ *(archivado el 2026-09-13)*

> **Partido el 2026-09-13** desde `add-assist-generation-with-rule-warnings` (§0). Es la mitad que
> desbloquea: C34 y C36 dependen de **la forma** de la respuesta y no de la prosa. **Cero llamadas a
> un proveedor**, y aun así entrega citas verificables — `search_knowledge` ya existe y el
> direccionamiento de las fichas de material es determinista. Las once decisiones, en
> [`c30-exploration-decisions.md`](informes/c30-exploration-decisions.md).

**Objetivo.** La capa estructurada de la venta asistida: **tres modos**, agrupación por **familia**, avisos **por reglas** y **citas resolubles**. Implementa la decisión 4 salvo la prosa.
**Prereq.** C07, C21, C23 · **Zona.** `ai-service/src/jbg_ai/assist/` *(no existe)*
**Alcance.**

- **Movimiento del contrato congelado, en un solo bloque** *(D-A)*: `product_id` en `AssistRequest` con validación de «al menos uno» frente a `query`; `AssistGroup.family_id` **nullable** con el invariante *sin familia ⇒ un solo miembro*; `match_reasons` en el miembro —que es el `reason` por candidato del §7.7, sin vocabulario nuevo—; `Citation` reformada con `citation_id`, `document_title`, `section_title`, **`claim_scope`**, `doc_type` y `score`, retirando `source`; `abstained` y `prompt_version` en la respuesta. `openapi.json` **se regenera aquí**, mientras la ruta tiene cero consumidores.
- **Tres modos** *(D-B)*: **M1** consulta libre · **M2** pieza sin pregunta · **M3** pieza con pregunta. `intent` se deriva **estructuralmente**: `product_pitch` en M2, `unclassified` en M1 y M3 — sin heurística de palabras clave, que C31 borraría.
- **Agrupación** por `family_id` con `variant_label` destacado, más `family_roster(family_id)` **nuevo en `ProductSearchPort`**, leyendo sólo `ai.product_document`. Sirve a la vez el aviso de variantes y la futura tool `listar_familia` de C32a. *Agrupar opera sobre lo recuperado; avisar de que existen variantes necesita el roster — son dos consultas distintas.*
- **`warnings[]` como códigos de vocabulario cerrado** *(D-C)*, no prosa: **`family_has_variants` y `size_label_missing`**. El copy castellano es del frontend, con el precedente de `assisted-search-panel` —*«MUST NOT render the retriever's raw match reason values, which are engineering vocabulary»*. **Los dos avisos de stock pasan a C34.**
- **Citas verificables, sin LLM** *(D-D, D-E, D-F)*: en **M2**, direccionamiento **determinista** por `chunk_id(document_slug, section_slug)` sobre una **lista blanca** de secciones, y **sólo `claim_scope: general`** — la ficha de `baño de oro` lleva una séptima sección que es compromiso de la casa. En **M1/M3**, `search_knowledge` con **filtro de slug asimétrico**: excluye las fichas de las **nueve** materiales canónicas que la pieza no declara, y deja pasar `faq`, `politica`, `talla`, `piedras-*`, `piezas-mixtas` y `marcajes-y-punzones`. Un filtro general por material cortaría **23 de los 32 documentos**.
- **Puerta de abstención** *(D-G)*: la regla relativa de C25 **ya corre**, así que aquí se la **honra y se la declara** — el camino de assist no genera cuando ha saltado, y la respuesta lo dice en `abstained`, **nunca en `low_confidence`**, cuyo significado medido está anticorrelacionado. El valor efectivo viaja **por parámetro** y no leído del entorno, para que el arnés barra configuraciones en un proceso.
- `pitch: ""`, `prompt_version: null`, `usage` a cero. **Ninguna llamada a un proveedor.**
- **Nace la capability `assist-generation`** *(nombre fijado el 13 sep)*, más deltas sobre `ai-service-api-contracts`, `knowledge-corpus` y `retrieval-abstention`. C30b añade requisitos **sobre esa misma capability** en vez de crear otra.

**Tests.** `test_variants_grouped_by_family_id`; `test_warnings_are_rule_derived_not_model_generated`; `test_citations_reference_retrieved_chunk_ids_only`; `test_group_without_family_has_exactly_one_member`; `test_pitch_context_excludes_establishment_claim_scope`; `test_slug_filter_keeps_faq_politica_talla_and_mixed_sheets`; `test_abstains_when_candidate_profile_is_flat`.
**Conflicto de zona.** Misma zona que C30b, C31, C32a y C32b → **nunca simultáneos**.

---

#### C30b · `add-assist-pitch-generation` ✅ *(archivado el 2026-09-14)*

> **Nace el 2026-09-13** al partir C30 (§0). Es la única mitad que llama a un LLM, y su valor **se
> mide contra C30a**: misma ruta, mismos candidatos, mismas citas, con prosa y sin ella. Esa
> ablación sale gratis del propio corte y es la que el §11.2 del diseño pide.

**Objetivo.** El argumentario en prosa sobre la base que C30a deja, con la garantía anti-alucinación **en ejecución** y no sólo en evaluación.
**Prereq.** C30a · **Zona.** `ai-service/src/jbg_ai/assist/`
**Alcance.**

- **Prompt versionado**: `prompts/assist/v1.md` con `PROMPT_VERSION = "assist/v1"` y su test de fichero↔constante, como `enrichment/` y `knowledge/`.
- **Cliente generativo** por la costura de `LiteLlmEnrichClient`: LiteLLM, `JPV_RAG_LLM_*`, **`gpt-4o-mini` a temperatura 0** *(D-K)*, *backoff* de proveedor, un reintento de parseo, fake inyectable. Temperatura 0 no es sólo reproducibilidad de las evaluaciones: es lo que hace viable no guardar el texto.
- **Salida estructurada donde el modelo declara qué `citation_id` usó**, y **verificación de integridad referencial en código, después de generar** *(D-D)*. `citations[]` son las que el pitch **usó**, no las que el retriever devolvió: emitir todo lo recuperado es decoración y hace imposible la comprobación. Cita colgante → un reintento con instrucción más dura, y si reincide se entrega la parte estructurada **sin pitch**. Nunca se ignora.
- **Placeholders `{{price}}`/`{{stock}}`** que el modelo no puede rellenar, y **la puerta que el mecanismo no cubría** *(D-H)*: el pitch sólo puede contener cifras **presentes literalmente en el payload que se le entregó** —tallas, mm, `925`, dígitos de SKU— más los dos tokens. Es **lista blanca y no lista negra**, porque `talla 12` y `plata de ley 925` son cifras legítimas. Un pitch con «39,90 €» literal pasa hoy el rechazo de C34 —no hay placeholder sin resolver— y llega al operario: eso es lo que esta puerta cierra, en ejecución.
- **El pitch no se persiste, y eso incluye no loguearlo** *(D-I)*. Se registran `trace_id`, `prompt_version`, `model`, `usage`, latencia, los `citation_id` usados, los códigos de aviso, `abstained`, longitud y hash — **nunca el texto**. Una línea de log es almacenamiento durable fuera de la base, sin el `effective_pos_id` que la respuesta sí lleva. **Excepción declarada**: el arnés de C38 sí guarda el texto generado, en `evals/results/` y en `ai.eval_*`, atado a `run_id`, `git_sha` y `prompt_version`, fuera del camino de servicio.
- **Barrido de contexto**: la lista blanca de secciones y el tope de materiales viajan **por parámetro**, para comparar 1/2/3 secciones en un proceso y publicar el efecto sobre la tasa de rechazo de la puerta numérica y sobre *faithfulness*. Es la progresión de prompts que el §11.6 y C39 piden.

**Tests.** `test_response_contains_no_literal_price_or_stock_number`; `test_pitch_is_not_persisted_anywhere` *(con listener `before_cursor_execute` contando DML, no «el módulo no importa un repositorio»)*; `test_pitch_text_is_never_written_to_the_log`; `test_dangling_citation_triggers_single_retry_then_drops_the_pitch`; `test_figure_absent_from_context_is_rejected_even_if_plausible`.
**Conflicto de zona.** Misma zona que C30a, C31, C32a y C32b → **nunca simultáneos**.

> **Implementado el 2026-09-14, y el barrido refuta el riesgo que esta ficha declaraba como el
> mayor.** Los cinco tests de arriba están en verde, con dos matices de nombre: la reparación es
> **una sola para las tres comprobaciones** y no un reintento por puerta, así que el test se
> llama `test_dangling_citation_triggers_single_repair_then_drops_the_pitch`; y
> `test_response_contains_no_literal_price_or_stock_number` corre sobre la respuesta **completa y
> con un argumentario no vacío**, que es la comprobación que C30a no podía hacer porque su `pitch`
> estaba vacío y el test pasaba por construcción.
>
> **Lo que el barrido midió** —120 generaciones reales, 3 anchos de contexto, muestra propia de 40
> piezas declarada antes de medir, `gpt-4o-mini` a temperatura 0—:
>
> | | 1 sección | 2 secciones *(se sirve)* | 3 secciones |
> |---|---|---|---|
> | citas ofrecidas | 2,0 | 3,5 | 5,0 |
> | rechazo en 1.ª pasada | 12,5 % | 55,0 % | 70,0 % |
> | **violaciones de la puerta numérica** | **0** | **0** | **0** |
> | argumentarios retenidos | **0** | **0** | **0** |
> | citas publicadas / ofrecidas | 85,0 % | **42,9 %** | 30,5 % |
> | USD por petición | 0,00048 | **0,00077** | 0,00099 |
>
> **La puerta numérica no rechazó nada en 120 generaciones.** Esta ficha decía que el pitch
> *«sólo puede contener cifras presentes literalmente en el payload»* y el diseño declaraba como
> riesgo mayor que esa puerta se comiera los argumentarios buenos: la tasa de falso positivo
> medida es **cero**. No significa que sobre —la regla de adyacencia nace de que `750` y `585`
> viven en `material-oro.md`, y eso sigue siendo cierto— sino que **la prevención en el prompt
> hizo el trabajo**: prosa corrida, placeholders obligatorios y un fichero de prompt sin un solo
> dígito. Las 121 violaciones del barrido son **todas** de correspondencia del tramo de apoyo, y
> **ninguna costó un argumentario**, porque su política es proporcionada.
>
> **La fila que más dice del diseño es la de citas publicadas:** en el ancho que se sirve se
> ofrecen 140 citas y sólo **60 sobreviven a la verificación**. Emitir todo lo recuperado —lo que
> D-D llamaba decorar— habría publicado más del doble de citas de las que el argumentario puede
> sostener. Es el argumento de D9 convertido en cifra.
>
> **Dos umbrales decididos con la cifra delante.** *Plegado de signos*: **no** — sólo el 2,5 % de
> los fallos de correspondencia son de puntuación, contra el 10 % declarado antes de medir.
> *Timeout*: **sube de 3 s a 4 s y pasa a `Settings`** (`JPV_ASSIST_PITCH_TIMEOUT_SECONDS`), que
> es lo que el diseño mandaba hacer *«sólo si el barrido mide que corta generaciones buenas»* —
> medido **por llamada**, que es como se aplica, el p95 es 2.863 ms y 3 s estaba a 1,05 × p95,
> cortando *jitter* en 8 de 175 llamadas.
>
> **Y tres cosas que la implementación refuta de sus propios artefactos.** **(1) El *backoff* de
> proveedor de C09 no se replica**: su base son 2 s y el presupuesto de una llamada es 4, y
> mantenerlo haría falsa la garantía de *«nunca más de dos llamadas por petición»*, que con
> reintentos transitorios debajo serían cuatro HTTP. **(2) La consulta del operario NO entra en
> la lista blanca numérica**: es qué contestar, no qué es cierto, y es la única superficie que
> controla alguien fuera del código — dejarla ensanchar la puerta es la misma apertura que la
> regla de adyacencia existe para cerrar. **(3) El modelo es constante del módulo y no
> `JPV_RAG_LLM_MODEL`**: esa variable es el modelo de enriquecimiento de C09 —`gpt-4o`— y
> heredarla movería el modelo de una llamada de mostrador cuyo coste y tasa de rechazo se
> midieron sobre otro. Suite **1195 → 1320, 0 en rojo antes y después**. De paso, la comparación por nombres destapó un defecto real de aislamiento —`get_engine` cacheaba un motor global e **ignoraba el `Settings` que recibe**, así que el test que configura un host inalcanzable envenenaba a los posteriores del proceso—, corregido con cuatro tests de regresión. Cifras completas en
> [c30b-implementation-measurements.md](informes/c30b-implementation-measurements.md).

---

> **Pendiente de despliegue que C30b deja escrito y NO puede cerrar** *(14 sep)*. C30b añade dos
> ajustes opcionales con su mitad de Python entregada y probada — `JPV_ASSIST_LLM_API_KEY`, que
> separa la credencial de la generación de mostrador de la del enriquecimiento por lotes de C09, y
> `JPV_ASSIST_LLM_MODEL`, que fija el modelo de esa llamada sin heredar el de C09 —. **La demo no
> genera hoy**: comprobado, `compose.demo.yaml` no pasa ninguna credencial de proveedor al
> servicio `jbg-demo-ai`, así que sirve la respuesta de C30a con 200 — que es el comportamiento
> declarado y con test, no un fallo.
>
> **Y una corrección, porque la primera versión de esta nota culpaba a Terraform y se equivocaba:
> `terraform/` no hace falta tocarlo.** El rol de instancia ya lee **todo el prefijo**
> `/jbg-demo/`, así que no hay cambio de IAM; y los secretos **no se declaran en Terraform a
> propósito**, porque un valor pasado a Terraform acaba en claro en el fichero de estado. Lo que
> falta son cuatro pasos pequeños —un `put-parameter` a mano, una línea en `deploy/demo/deploy.sh`
> leída **sin `:?`** porque su ausencia es un estado válido, dos líneas en `compose.demo.yaml` y
> una entrada en el runbook—, detallados en
> [`openspec/DEFERRED_TASKS.md`](../../openspec/DEFERRED_TASKS.md). Mientras tanto la clave
> **repliega** a `JPV_RAG_LLM_API_KEY` y **se puede comprobar en el log** cuál está en vigor:
> `stage=assist_client … credential=assist|rag_fallback`. Anotarlo es lo que evita que se
> descubra dentro de seis meses mirando una factura.

#### C31 · `add-guardrails-and-intent-router` ✅ *(archivado el 2026-09-16)*

**Objetivo.** Que el sistema sepa cuándo no debe responder y no se deje instruir por la consulta.
**Prereq.** **C30b** *(afinado el 13 sep: su validación de salida necesita una salida que validar, y el rechazo cortés necesita la ruta; las dos cosas las tiene C30b)* · **Zona.** `ai-service/src/jbg_ai/assist/`
**Alcance.** Clasificador de intención (catálogo / conocimiento / ambos / fuera de dominio); rechazo cortés sin llamar al retriever; consulta tratada como dato; validación de salida contra JSON schema con reintento único.

> **Lo que C30a ya deja hecho, y lo que sigue siendo de aquí** *(13 sep)*. C30a **no clasifica
> intención**: eso es de este change entero. Lo que sí trae es la **puerta de abstención**, para
> que la capa de generación no redacte sobre un perfil de candidatos plano durante la vuelta de
> manivela que separa a C30 de C31 — medido, **18 de 20** consultas fuera de dominio llegan hoy con
> candidatos, y son la categoría más grande del golden set. Aquí esa puerta pasa de red a
> decisión: el clasificador corta **antes de llamar al retriever**, que es lo que la puerta de
> C30a no puede hacer porque necesita los candidatos para leer su forma. Y `intent` deja de valer
> `unclassified`, que es el único valor que C30a puede emitir en M1 y M3.

> **Y lo que C30b le deja escrito, al implementarse** *(14 sep)*. Dos cosas, las dos **declaradas en
> la capability viva `assist-generation`** y no sólo aquí, que es la diferencia entre heredar y
> suponer. **Uno · el argumentario del modo de consulta libre es de este change.** C30b genera en
> los dos modos anclados a pieza y en el de consulta libre **no llama al proveedor**, con un
> requisito y un test que lo comprueban (`test_free_query_mode_calls_no_provider`): redactar sobre
> un conjunto de candidatos cuya intención nadie ha clasificado es prosa sobre una suposición, y el
> clasificador es de aquí. **Dos · `clarification_question` se declara de C31**, cerrando la
> orfandad que arrastraba desde C30a — está en el contrato devolviendo siempre nulo desde entonces,
> el §7.7 la lista como parte de la respuesta, y **ninguna ficha la reclamaba por escrito**. Generar
> una pregunta de aclaración es una decisión de enrutado sobre una consulta libre; la tool
> `pedir_aclaracion` de C32 es otra cosa. El campo ya está en el esquema, así que **no cuesta
> movimiento de contrato**.
>
> **Y una mitigación que NO hay que rehacer**: la consulta del operario ya viaja como **dato
> delimitado** en el mensaje de usuario, nunca concatenada al de sistema, con su bloque etiquetado
> y una regla invariante del prompt que lo dice. `test_prompt_injection_does_not_change_system_behavior`
> tiene aquí su equivalente ya en verde (`test_prompt_injection_in_the_query_does_not_change_the_system_message`);
> lo que falta y es de aquí es **clasificar y rechazar**, que es otra cosa.
**Tests.** `test_out_of_domain_query_short_circuits_before_retrieval`; `test_prompt_injection_does_not_change_system_behavior`; `test_invalid_model_output_triggers_single_retry_then_safe_error`; `test_care_question_routes_to_knowledge_index`.

---

#### C32a · `add-sales-assistant-tool-registry` ✅ *(archivado el 2026-09-20)*

**Objetivo.** Las herramientas del agente y su registro, sin nadie que decida todavía. **Ni una llamada a un proveedor.**
**Prereq.** **C30b**, C31 · **Zona.** `ai-service/src/jbg_ai/assist/` *(+ `retrieval/ports.py` y `retrieval/search.py`, declarado)*
**Alcance.** Seis tools con su esquema de *function calling* —`buscar_catalogo`, `consultar_disponibilidad`, `listar_familia`, `buscar_sustitutos`, `consultar_conocimiento`, `pedir_aclaracion`—; el registro; errores devueltos **como datos** y nunca como excepción; el invariante de **solo lectura comprobado por introspección**; y la etiqueta cualitativa de disponibilidad.
**Cuatro de las seis son envoltorios de código que ya existe** *(20 sep)*. `buscar_catalogo` la sirve `retrieve_products()`, `buscar_sustitutos` la sirve `retrieve_substitutes()`, `listar_familia` la sirve el `family_roster(family_id)` que C30a añadió al puerto, y `consultar_conocimiento` la sirve `search_knowledge` con el filtro de slug de C30a. **Lo nuevo aquí no son las tools: es el registro y sus invariantes.**
**`consultar_disponibilidad` era la única sin servicio detrás, y aquí lo tiene** *(20 sep)*. Se sirve desde `ai.pos_projection` —`scope_buckets(pos_id)` ya existe en `ProductSearchPort`— y **traduce el bucket a etiqueta cualitativa sin dígitos**: `QTY_BUCKETS = {"0", "1-2", "3+"}` son cifras, y una cifra de stock en el contexto del modelo es exactamente lo que el §6.2 y el §15.10 del diseño prohíben. La observación declara además su **frescura**, igual que `projection_age_seconds` hace en el §7.6. **El endpoint .NET queda identificado, acotado y no hecho** —con él, el esquema de la llamada de vuelta que el §6.1 dejaba abierto—, y la tool se diseña para que sea un reemplazo directo: misma forma de observación, puerto inyectado.
**`pedir_aclaracion` no escribe la pregunta** *(20 sep)*. Recibe **un eje de un enum cerrado** —`clarification_axes()` ya existe— y el castellano lo sigue escribiendo `clarification_for()`. El modelo decide *qué falta*; el código decide *cómo se pregunta*. Dejarle escribir el texto sería la primera prosa de un modelo en el único campo que ninguna puerta numérica inspecciona, y **rompería un requisito vivo** de `assist-generation`: *«The clarification question is resolved in code from a closed catalogue of templates»*.
**El invariante de solo-lectura es estructural, no declarativo** *(20 sep)*. Un campo `writes: bool = False` lo puede poner cualquiera a `False`. El test comprueba tres cosas por introspección: que el registro contiene **exactamente** el conjunto congelado de nombres; que ningún puerto capturado por una tool expone método alguno del vocabulario de escritura (`insert|update|delete|write|save|upsert|persist|sync|apply`); y que ningún cliente HTTP registrado emite otra cosa que `GET`.
**Tools retiradas** *(31 ago y 12 sep, heredado de la ficha de C32)*. **`perfil_punto_venta`** sale del registro: la servía C33, anulada con la rama de C19 (§0). **`buscar_complementarios`** sale el **12 de septiembre** al dispararse el corte nº 1 sobre C27 (§0). Misma regla las dos, y no una distinta: registrar una tool sin servicio detrás le da al modelo una herramienta que falla siempre, y el bucle la reintenta y quema presupuesto. **Seis tools, y el recuento no es lo que el PF evalúa del agente**: lo son el bucle, el presupuesto duro, el invariante de solo-lectura y el `partial: true`.
**Tests.** `test_no_registered_tool_performs_writes` (introspección del registro); `test_tool_error_is_returned_as_data_not_exception`; `test_availability_tool_returns_a_qualitative_label_and_never_a_figure`; `test_clarification_tool_picks_an_axis_and_never_writes_the_question`; `test_registry_holds_exactly_the_six_expected_tools`.
**Conflicto de zona.** Misma zona que C30a, C30b, C31 y C32b → **nunca simultáneos**.

**Implementado el 2026-09-20, y la implementación refuta seis cosas.** Cierre: **1.468 passed / 0 failed** comparados **por nombres** contra una línea base de **1.418**, sin ningún test retirado ni renombrado; `openspec validate --all --strict` en **58 · 0**; **1.021 enlaces, 0 rotos**; y `openapi.json` **idéntico byte a byte**, verificado contra su `sha256` y no supuesto. **Archivado el 2026-09-20 con 1.469 passed / 0 failed**, tras una pasada de verificación independiente que reprodujo cada cifra contra el árbol y encontró **cuatro cosas, dos de ellas defectos de código**: la exclusión de objetos inertes del invariante estaba escrita **por categoría** —todo modelo de pydantic y toda dataclass— y eso dejaba `InMemoryKnowledgeIndex`, el puerto que `consultar_conocimiento` captura, **fuera de los tres ejes**, además de permitir que un puerto que escribiera construyera el registro si estaba escrito como cualquiera de las dos; y `document_by_sku()` resolvía con `.first()` apoyándose en un comentario que afirmaba que `sku` es único en `ai.product_document`, cuando no lo es y el ticket archivado de `add-pgvector-schema-foundation` **decidió expresamente no crear ese índice**. Las otras dos son enunciados que se leían más fuertes que el código: el campo `abstenido` no tenía test que ejerciera su camino `True`, y lo que el vocabulario de escritura pierde no es una flexión sino **un verbo que nunca tuvo** (`put_checkpoint()`). Capability viva `sales-assistant-tools` nacida con **13 requisitos y 25 escenarios**. Lo que se cae: **(1)** el vocabulario de escritura leído como subcadena es **insatisfacible** —`sync` está dentro de `projection_synced_at()` y de `synced_at()`, que son lecturas, y la primera vive en el puerto que `consultar_disponibilidad` debe capturar—, así que el vocabulario se conserva y lo que se fija es la comparación **token a token**; **(2)** `Settings` tropieza igual, por el shim deprecado `update_forward_refs` de pydantic, y se excluye la configuración **por tipo**, nunca por una bandera de la tool; **(3)** hacía falta una **cuarta** causa de fallo, `referencia_no_utilizable`, porque una pieza descatalogada no es una desconocida —la distinción que C26 ya hace—; **(4)** `low_confidence` **no es la abstención** y emitirlo habría dicho lo contrario de la verdad sobre el conjunto juzgado, así que `buscar_catalogo` usa la costura `on_abstention` de C30a y emite `abstenido`; **(5)** ampliar `ProductSearchPort` **no rompe los dobles** —`Protocol` sin `@runtime_checkable`, ningún `isinstance`, y el repositorio no tiene `mypy` ni CI para `ai-service`—, así que la tarea 3.5 es necesaria por otra razón: la suite **llama** a los dos métodos nuevos; **(6)** una pieza sin familia es observación correcta con lista vacía, y `pedir_aclaracion` **no captura ningún colaborador**, así que el invariante pasa sobre ella **vacuamente** — límite declarado, con un test de anti-vacuidad que fija qué puertos se ve capturar a cada tool.

**Los nombres de test de esta ficha no son los que se escribieron.** La ficha proponía `test_no_registered_tool_performs_writes`, `test_tool_error_is_returned_as_data_not_exception` y `test_availability_tool_returns_a_band_not_a_number`; la suite usa la convención `test_<unidad>_<escenario>_<esperado>` que la DoD exige, y un escenario de la ficha se reparte en varios tests porque afirma varias cosas. La trazabilidad de los **nueve escenarios** de la HU a test nombrado está en el §6 del [informe](informes/c32a-implementation-measurements.md).

---

#### C32b · `add-sales-assistant-agent-loop` ✅ *(archivado el 2026-09-21)*

**Objetivo.** La capa de decisión: bucle con *function calling*, presupuesto duro y `partial: true`.
**Prereq.** **C32a** *(y con él C30b y C31)* · **Zona.** `ai-service/src/jbg_ai/assist/` + `api/routers/assist.py` + `openapi.json`
**Alcance.** El bucle manual —decidir, ejecutar tools en paralelo, observar, volver a decidir—; los tres presupuestos; `partial: true` al agotarlos; la traza con tokens y coste por iteración; **`POST /v1/assist/agent`** con la transcripción en la petición; y la tarea de prompt del agente en `assist/v4`.
**La respuesta la redacta la capa de C30b, no el modelo** *(20 sep)*. El bucle reúne evidencia y `generate_pitch()` escribe. Si la última vuelta escribiera prosa se esquivarían de golpe la puerta numérica por lista blanca, la integridad referencial de las citas y la reparación única. El invariante que lo hace comprobable: **el contenido textual de las vueltas se descarta; sólo se honran sus `tool_calls`** — que de paso mantiene el *«nada se persiste»* sin esfuerzo, porque el razonamiento intermedio no sale del proceso. `free_query_payload_from()` se reutiliza tal cual y los sustitutos entran como grupo distinguido.
**Ruta propia, y por medición** *(20 sep)*. Peor caso: **2 s de enrutador + 5 vueltas + 4 s de argumentario ≈ 15-20 s**, contra los **5 s** que el §6.4 declara para `/v1/assist`. Un *flag* en `/v1/assist/sale` pondría ese camino en la ruta que C34 llama síncrona desde el mostrador, y metería `partial` y la traza en el `AssistResponse` que C34 y C36 leen. **`/v1/assist/sale` no se toca** y sigue siendo la fila determinista de la ablación. Mover el contrato es **adición pura** —ningún campo se retira ni cambia de tipo— y se verifica hoja a hoja, como hizo C31.
**Tres presupuestos y un contador, porque la ficha sólo escribía uno** *(20 sep)*: **≤5 iteraciones**, **≤6 tool calls**, **≤8 llamadas al proveedor** por petición HTTP —1 enrutador + ≤5 vueltas + ≤2 argumentario— con aserción en ejecución al modo de C31, y un **presupuesto de tokens fijado con medición**, porque lo que domina el coste de un bucle es el contexto acumulado y no el número de pasos. Los **embeddings** van en contador aparte: `usage.calls` sigue significando lo que C31 publicó.
**El multi-turno viaja en la petición** *(20 sep)*. El servicio no guarda conversación. Dos consecuencias, las dos con test: el delimitado `QUERY_OPEN`/`QUERY_CLOSE` se aplica a **cada turno** y no sólo al último; y los turnos del asistente, que el cliente puede falsificar, se tratan como dato igual que la consulta, con tope de turnos y de caracteres.
**Decisión abierta que la historia de usuario tiene que cerrar.** Si el enrutador clasifica **todos** los turnos del operario o sólo el primero. Propuesta: clasificar todos y que **sólo el primero cortocircuite**; un veredicto de rechazo en un turno posterior emite los mismos dos códigos y una negativa cortés que no gasta tools. No toca la matriz de confusión de C31, medida sobre consultas sueltas.
**Tests.** `test_loop_stops_at_iteration_budget_and_flags_partial`; `test_token_usage_accumulated_across_iterations`; `test_out_of_stock_query_triggers_substitutes_tool`; `test_loop_turn_text_never_reaches_the_response`; `test_every_transcript_turn_travels_as_delimited_data`; `test_provider_call_ceiling_holds_for_one_request`.
**Conflicto de zona.** Misma zona que C30a, C30b, C31 y C32a → **nunca simultáneos**.

**Lo que C32a le deja escrito y en verde** *(20 sep)*. Las seis tools existen con sus puertos **inyectados**, así que C32b sólo aporta el bucle. Cinco cosas concretas que hereda y que no tiene que decidir:

1. **`build_registry(principal=…, settings=…, embed=…, search=…, knowledge=…)` ata el principal en la construcción**, no en la llamada: el ámbito de lectura es del token, como en todo `/v1`. Se construye **un registro por petición** y no cuesta E/S, porque no se construye ningún puerto.
2. **`registry.schemas()`** devuelve los seis esquemas de *function calling* en el orden congelado, listos para el parámetro `tools` de la llamada. **No hay *snapshot* versionado**: se fijan con test de forma.
3. **`await registry.invoke(nombre, argumentos)` no lanza nunca.** Devuelve `ToolObservation` con `ok`, `content` acotado y `cause` de vocabulario cerrado — incluido el caso de que el modelo **invente un nombre de tool**, que vuelve como observación y no como excepción. El bucle gasta una vuelta y sigue.
4. **`registry.embedding_calls`** es el contador propio de *embeddings*. El presupuesto de llamadas al proveedor de **chat** de C32b se cuenta aparte y `usage.calls` **no cambia de significado**: hay un test que lo pincha.
5. **El invariante de solo-lectura corre en la construcción.** Si C32b inyecta un puerto que escribe, `build_registry` **falla al construir** y no en la vuelta número tres. Y una advertencia heredada del §7 del informe: **un cliente HTTP de propósito general no pasa el tercer eje**, porque expone `post`/`put`/`patch`/`delete`; el día que la disponibilidad venga de .NET habrá que envolverlo en una superficie de sólo lectura.

**Y dos cosas que C32b tendrá que decidir y C32a no pudo:** si la **granularidad de seis** es la correcta —iterar descripciones exige un modelo, y esta mitad no llama a ninguno—, y si la **etiqueta cualitativa se queda corta** para decidir el pivote a sustitutos. Ensanchar el vocabulario no mueve ningún contrato; lo que no se hará es volver al bucket crudo. La pregunta viva sobre si el enrutador clasifica todos los turnos **sigue abierta** y C32a no la toca, porque aquí no hay conversación.

---

#### ~~C33 · `add-pos-sales-profile`~~ ⛔

> **⛔ Anulado el 2026-08-31** con la rama de C19 (§0). **Es el único rescatable de los cinco**, y su prerrequisito estaba sobre-especificado: **no necesita C19**. Sus siete métricas son agregados a nivel POS sobre `Sales` × `ProductAiProfile`, y lo único per-producto que usan —`sales_30d` y `lastSaleAt`— ya lo calcula `IndexFeedRepository.GetSalesAggregatesAsync` (C12). No toca `IsSupplySource`, `stock_in_other_pos`, `estimated_days_to_stockout`, `is_top_seller_in_pos`, `sales_7d` ni `sales_60d`.
>
> **Si el núcleo cierra y sobra sesión**, se reabre **con prereq C08 + C12, sin migración**: devuelve al agente de venta su octava tool (`perfil_punto_venta`, hoy retirada del registro de C32a) y da al §11.3 del diseño su test de fidelidad del perfil. Mientras tanto, C32a registra **seis** *(corregido el 20 sep: esta frase decía siete, y el recuento bajó a seis el 12 de septiembre con el corte de C27)*.

**Objetivo.** Argumentario por POS como **perfil periódico calculado**, no como texto libre. Decisión 7.
**Prereq.** ~~C19~~ → **C08, C12** *(corregido el 31 ago)* · **Zona.** `Application/` + `ai-service/src/jbg_ai/assist/`
**Alcance.** Cálculo SQL en .NET de `top_piece_types`, `top_materials`, `top_price_ranges`, `top_collections`, `average_ticket`, `best_selling`, `slow_moving`; persistencia estructurada; el LLM **solo redacta el resumen a partir de ese payload**; `GET /api/ai/pos/{id}/sales-profile`; consumo como prior de ranking y por la tool `perfil_punto_venta`.
**Tests.** `Profile_MetricsComputedFromSalesNotLlm`; `test_narrative_mentions_only_metrics_present_in_payload`; `Profile_PosWithoutSales_ProducesEmptyProfileNotHallucination`; `Profile_RegeneratedWhenPeriodChanges`.

---

#### C34 · `add-dotnet-assist-and-recommendation-endpoints` 🔴

**Objetivo.** Exponer venta asistida y sustitutos con hidratación y resolución de placeholders. *(Los complementarios salieron con C27 el 12 sep; corregido el 21 sep.)*
**Prereq.** C15, C26, **C30a** *(afinado el 13 sep: este change depende de la **forma** de la respuesta y no de la prosa, y ésa es precisamente la razón por la que C30 se partió — con C30a archivado, C34 puede abrirse sin esperar al argumentario)* *(C27 **cayó** el 12 sep: la cláusula condicional se ejecuta — fuera la ruta `.../recommendations` y fuera su test `Recommendations_ManualPairsRankedFirst`, y el resto del change no se toca, tal como esta ficha ya instruía)* · **Zona.** `API/Controllers/`, `Application/` **+ `deploy/demo/` y `compose.demo.yaml`** *(añadidos el 21 sep, sólo para la última tarea: activar la generación en la demo)*
**Alcance** *(reescrito el 21 sep al explorar C34; ver la revisión de abajo)*. **`POST /api/ai/products/{id}/sales-assist`** con cuerpo `{pointOfSaleId, question?}` y **`GET /api/ai/products/{id}/substitutes?pointOfSaleId=&pageSize=`**, las dos con el punto de venta **obligatorio**; **sustitución de `{{price}}`/`{{stock}}` contra la pieza anclada**; **retirada del argumentario —no de la respuesta— si queda algún marcador sin resolver**; y, como última tarea, **la generación encendida en la demo**. *(Decía `GET …/sales-assist` sin punto de venta y «rechazo de la respuesta si queda algún placeholder sin resolver».)*
**Dos añadidos del 13 sep, y los dos vienen de que la autoridad sobre el dato es de aquí:**

- **Los dos avisos de stock.** `stock_critical` y `family_members_out_of_stock` **se calculan aquí, tras hidratar**, y se apilan sobre los códigos estructurales que trae C30a (`family_has_variants`, `size_label_missing`). En Python sólo existe `qty_bucket`, declarado como algo que *«never emitted: a bucket on the wire would be the beginning of one»* y capaz de desfasarse minutos: un aviso «stock crítico» mostrado cuando hay doce unidades en el cajón no es un matiz, es la credibilidad del asistente en el mostrador. **Es el segundo caso de la misma forma** que la exclusión por stock que la nota de abajo recoge — misma regla, no una distinta.
- **`question` en `/sales-assist`.** Un campo opcional que viaja al modo **M3** de `POST /v1/assist/sale`. Es el camino más barato que existe para que el corpus de conocimiento de C23 —32 documentos y 161 fragmentos, indexados desde el 6 de septiembre— llegue por fin a una pantalla: hoy **no tiene ninguna ruta hasta el joyero**, porque esta ficha sólo exponía rutas por pieza y C36 sólo pinta un card. No hay contrato nuevo en Python: un `question` que se reenvía. *(Hasta el 21 sep decía `?question=` en la URL; pasa al **cuerpo de un `POST`** porque es texto libre del cliente y en una URL acaba en el log de acceso de nginx — D-B del [informe](informes/c34-exploration-decisions.md).)*

**Tests.** `SalesAssist_ReplacesPlaceholdersWithRealValues`; **`SalesAssist_WhenPlaceholderUnresolved_WithholdsThePitchInsteadOfShippingTheRawTemplate`** *(renombrado el 21 sep: era `…_ReturnsErrorInsteadOfRawTemplate`, y lo que se retira es el argumentario, no la respuesta)*; `Substitutes_ExcludeProductsWithoutStockAtTargetPos`; `SalesAssist_AsOperatorOfAnotherPos_Returns403`; **`SalesAssist_StockWarningsComputedAfterHydration_NotTakenFromPython`**; **`SalesAssist_WithQuestion_ReturnsCitationsCarryingClaimScope`**; y **los catorce que añade la exploración del 21 sep**, uno por decisión que lo necesita, en el §7 del [informe](informes/c34-exploration-decisions.md). *(`Recommendations_ManualPairsRankedFirst` no se escribe: su ruta se retiró con C27.)*
**Conflicto de zona.** Mismo controlador que C15 → nunca simultáneos.

> **Revisada el 2026-09-13, al implementar C30a. La ficha se sostiene entera; se le añaden
> cuatro hechos del contrato que ya existe**, porque este change nacerá contra él y no contra
> el congelado que la ficha conoció:
>
> - **`Citation.source` ya no existe.** La cita lleva `citation_id` —`<documento>#<sección>`,
>   que abre fichero y encabezado en git—, `document_title`, `section_title`, `doc_type`,
>   `claim_scope` y `score`. Un mapeo de `source` no compila contra el `openapi.json` vivo.
> - **`AssistGroup.family_id` es nulable**, y un grupo sin familia trae **exactamente un
>   miembro**. La hidratación tiene que manejar el caso: es el **58 %** del catálogo.
> - **La respuesta trae `abstained`.** Cuando vale `true` no hay grupos, y eso **no** es «no
>   encontrado»: es «el catálogo no puede contestar esta consulta». Pintarlos igual borra la
>   distinción que C30a existe para entregar.
> - **`family_label` puede venir nulo en el modo de consulta libre** y sí llega relleno en los
>   dos modos anclados, que son los que esta ficha usa. Está medido y declarado en el §6 de
>   [`c30a-implementation-measurements.md`](informes/c30a-implementation-measurements.md).
>
> Y los dos añadidos del 13 sep siguen en pie **con su base ya construida**: los códigos
> estructurales sobre los que apilar son literalmente `family_has_variants` y
> `size_label_missing`, y `?question=` viaja al modo M3, que está servido y medido.

> **La exclusión por falta de stock es de este change, y no está en C26** *(anotado el
> 2026-09-12, al implementar C26)*. Estaba especificada **dos veces** —en la ficha de C26 y
> aquí— y C26 la retiró de la suya al implementarse: excluir en Python rompería el
> invariante del §15.10, donde la proyección de disponibilidad **degrada y nunca elimina**
> porque puede desfasarse minutos, y ocultaría piezas que la tienda sí puede vender.
> `POST /v1/retrieval/substitutes` **sobre-recupera a propósito** y lo declara en
> `candidates_returned`, precisamente para que quien filtre aquí tenga de dónde llenar la
> página. La autoridad sobre el stock es de .NET y el test que lo fija es el que esta ficha
> ya lleva: `Substitutes_ExcludeProductsWithoutStockAtTargetPos`. **No se busque en Python.**
>
> Un aviso medido que viene con ello: el término de disponibilidad de C26 reutiliza
> `w_availability = 1,0` de C25, y ahí la similitud vive en `[0, 1]`, así que en la práctica
> ese peso **particiona** — agotados detrás de disponibles, siempre. No elimina nada y por
> eso se deja, pero conviene saberlo antes de medir aquí. Está en el §7 de
> [`c26-implementation-measurements.md`](informes/c26-implementation-measurements.md).

> ⚠ **Refutada en parte el 2026-09-21, al explorar C34** — la ruta de la consulta libre **no entra
> en este change**, y el párrafo «Ninguna hidratación nueva» de abajo **es falso**: los marcadores
> no dicen de qué pieza son. Ver la revisión que sigue a esta anotación. Se conserva como registro.
>
> **La consulta libre gana ruta, y la ruta es de aquí** *(anotado el 2026-09-14, al explorar
> C31)*. C31 pone argumentario en el modo **M1** —consulta sin pieza—, con lo que ese modo deja
> de ser un hueco del servicio y pasa a tener respuesta redactada, **rechazo cortés** y
> **repregunta**. El §15.12 del diseño declara que **no tiene pantalla**: sus consumidores son el
> bucle de C32 y el arnés de C38, no una caja de texto. La consecuencia de no cerrarlo está
> escrita en ese mismo párrafo — el *«no lo sé»* del sistema **se demuestra con escenarios y no en
> pantalla**, y las diez fichas de mostrador del corpus siguen alcanzándose sólo si el cliente
> tiene ya una pieza en la mano.
>
> **El coste es el que el diseño ya acotó, y no crece con C31:** una ruta nueva en .NET y un
> bloque de respuesta en el panel de búsqueda. **No hay contrato nuevo.** La ruta reenvía `query`
> a `POST /v1/assist/sale` **sin `product_id`** y devuelve lo que ya devuelve el modo M3 —grupos,
> citas, avisos— más los tres campos que C31 llena: `intent` con el veredicto del enrutador,
> `clarification_question` cuando la consulta no basta para buscar, y `pitch` cuando sí. El bloque
> de pantalla es de **C36**, que ya pinta citas distinguiendo `claim_scope` y ya tiene tabla de
> copy para códigos de vocabulario cerrado: el rechazo y la repregunta son **dos filas más de esa
> tabla**, no un componente nuevo.
>
> ~~**Ninguna hidratación nueva.** M1 no ancla pieza, así que no hay más `{{price}}` ni `{{stock}}`
> que los de los candidatos, que es el mismo camino que `/sales-assist` ya recorre; y el rechazo
> del enrutador llega **sin grupos**, con lo que no hay nada que hidratar en el caso que esta
> anotación añade.~~ **Falso** *(21 sep)*: en M1 el argumentario habla de **varias piezas** con
> los mismos dos tokens, y .NET no puede saber a cuál se refiere cada uno sin adivinar.
>
> **Lo único que esta ficha hereda de C31 es mapear el veredicto a pantalla, y ahí hay una
> distinción que no se puede perder.** `abstained: true` y el rechazo del enrutador son **dos
> negativas distintas** —*«el catálogo no puede contestar esta consulta»* frente a *«eso no lo
> vendemos»*— producidas por **dos mecanismos distintos**: la primera lee la forma del perfil de
> distancias después de recuperar (C25), la segunda clasifica antes de recuperar (C31). Pintarlas
> con la misma pantalla borra justamente la distinción que las **dos cifras publicadas por
> separado** existen para sostener. La tercera, `clarification_question`, no es una negativa: es
> una petición de dato, y su pantalla tiene que invitar a escribir, no cerrar la consulta.

> **Revisada el 2026-09-21, al explorar C34.** Catorce decisiones, cuatro de ellas cerradas con el
> desarrollador en la sesión, y cinco mediciones reproducibles, todas en
> [`c34-exploration-decisions.md`](informes/c34-exploration-decisions.md). Lo que cambia en esta
> ficha:
>
> - **Sólo las dos rutas del card** *(cerrada)*. Ni la consulta libre ni la ruta del agente: en las
>   dos, el argumentario habla de varias piezas con los mismos `{{price}}` y `{{stock}}`, y no hay a
>   cuál asignarlos. El arreglo es pequeño y es de Python —prohibir los marcadores en las tareas sin
>   pieza anclada, porque las filas ya enseñan el precio hidratado—, y queda identificado y no hecho.
>   **El §15.12 del diseño sigue siendo cierto.**
> - **`POST` con `question` en el cuerpo** *(cerrada)*, y `pointOfSaleId` obligatorio en las dos rutas,
>   con la regla de C15.
> - **Los marcadores se resuelven contra la pieza anclada**: el precio con formato «39,90 €» y el
>   stock **como entero**, porque el 88,3 % de los 213 argumentarios de C30b lo escribe como número
>   («tenemos {{stock}} en tienda»). Si queda cualquier `{{…}}`, **se retira el argumentario y se
>   sirve el resto**, que es la misma política de las puertas de C30b.
> - **Pieza anclada con stock 0** *(cerrada)*: sin pregunta se retira el argumentario —147 de 213
>   escriben «disponible por {{price}}» antes de saber el stock—; con pregunta se sustituye el 0.
> - **El presupuesto de 5 s pasa a 10 s**, derivado del peor caso de Python (2 × 4 s): con 5 s se
>   cortaría el **7,5 %** de las peticiones en el ancho que se sirve. Además, **ningún reintento en
>   timeout** y un 422 que deja de leerse como «IA no disponible».
> - **`family_has_variants` se recalcula tras hidratar**: sin eso, el **19,2 %** de las piezas
>   ancladas con familia llevaría un aviso de variantes falso. **`stock_critical` = 1 o 2 unidades**,
>   configurable, frente a las dos definiciones incompatibles que .NET ya tiene.
> - **Sustitutos con la ventana máxima (`top_k = 20`)**: con la de 15, en Fornells el **71,1 %** de
>   las piezas ancladas no llenaría una página de 5; con la de 60, el 7,1 %.
> - **Activar la generación en la demo es la última tarea** *(cerrada)*, con los cuatro pasos ya
>   escritos en `DEFERRED_TASKS.md` más la configuración .NET de la demo y una nueva medición de la
>   memoria del `t3.small`.

> **Implementada el 2026-09-21** — [informe de implementación](informes/c34-implementation-measurements.md).
> Las dos rutas, los dos servicios, el cliente `ai-assist` y la configuración de la demo están
> hechos, con **las 50 tareas** marcadas y la suite comparada **por nombres** contra la línea
> base. Sin migración, `openapi.json` idéntico byte a byte y `POST /api/ai/search` intacto.
> **La latencia de extremo a extremo se midió** con proveedor real en Docker Compose, sin el
> interceptor de Norton: sobre 80 peticiones, p95 **7,1 s** y máximo **7,9 s**, ninguna por encima
> de 8 s, así que **`AssistTimeoutMs` se queda en 10 s**. **La demo quedó desplegada y verificada el 2026-09-22** (§6 del informe, §13 del QA):
> parámetro creado, `credential=assist` en el log, una asistencia real `generated` con precio y stock
> resueltos en el texto, sustitutos con tres tramos de su embudo —60 candidatos, 28 en la tienda, página de
> 5— y `jbg-demo-ai` en **269,9 MiB de 512**, sin moverse al generar. **Y dos hallazgos que no son de
> C34**: un entorno recién desplegado deja `ai.pos_projection` vacía y **toda** la recuperación responde
> 503 —arreglado con `sync-pos`—, y el corpus de conocimiento **no viaja en la imagen** de `jbg-ai`, así
> que M2 nacía con el argumentario retirado. Los dos quedan en `DEFERRED_TASKS.md`. Lo que la
> implementación refina de esta ficha está en el §2 del informe; ninguna decisión cerrada se ha movido.

---

#### ~~C35 · `add-inventory-agent-proposals`~~ ⛔

> **⛔ Anulado el 2026-08-31** con la rama de C19 (§0). Era el segundo agente, y ya era el corte nº 8 del §6. Con él cae la única pieza con contenido agéntico de la rama; el asistente de venta (C30→C31→C32) se conserva entero y es el que el diseño marca «Núcleo · Requisito del PF». Ficha conservada como registro.

**Objetivo.** Segundo agente: prioriza, elige sustituto y redacta el motivo. **Los números los calcula .NET.**
**Prereq.** C26, C29, C32, C33 · **Zona.** `ai-service/src/jbg_ai/assist/`
**Alcance.** `POST /v1/inventory/propose` batch por POS; tools `senales_demanda` (.NET), `stock_por_pos` (.NET), `buscar_sustitutos`, `perfil_punto_venta`; salida: lista priorizada con motivo redactado y sustituto cuando la reposición no es satisfacible; **todas las propuestas nacen `Proposed`** y se persisten vía .NET.
**Tests.** `test_agent_never_computes_quantities_itself`; `test_unsatisfiable_replenishment_triggers_substitute_tool`; `test_reason_mentions_only_signals_from_payload`; `test_all_proposals_created_in_proposed_state`; `test_budget_exhausted_returns_partial`.
**Degradación planificada.** Si este change no llega, C29 ya genera recomendaciones por reglas puras: se pierde la priorización y la redacción, no la funcionalidad.

---

#### C36 · `add-frontend-assist-card-and-family-disambiguation` 🔴

**Objetivo.** Cerrar el flujo visible de venta: card con desambiguación por familia, citas, sustitutos y complementarios.
**Prereq.** C16, C34 · **Zona.** `frontend/src/`
**Alcance.** Card con argumentario, avisos calculados y citas desplegables; bloque de **variantes de la familia con `variant_label` destacado y confirmación explícita antes de vender**; bloque de sustitutos cuando `stock = 0`. ~~Bloque "También puede encajar" con complementarios~~ — **retirado el 12 sep con el corte de C27** (§0): la card entrega **tres bloques de los cuatro previstos**, y el que falta se declara en el §15 del diseño con su medición, no se calla.
**Dos añadidos del 13 sep:**

- **Caja de pregunta en el card**, que llama a `POST /api/ai/products/{id}/sales-assist` (C34) con `question` en el cuerpo y con ella al modo **M3** *(corregido el 21 sep: decía `/sales-assist?question=`; la pregunta del cliente pasa al cuerpo para que no acabe en el log de acceso de nginx — D-B del [informe de C34](informes/c34-exploration-decisions.md))*. Es la superficie por la que el corpus de C23 llega al joyero, y cubre la situación real del mostrador: el cliente tiene la pieza en la mano y pregunta. Las citas que se despliegan **deben distinguir `claim_scope`**: un compromiso de la casa —**25 de los 161 fragmentos**— no se presenta con el mismo aspecto que un hecho del mundo, y la ficha de `baño de oro` dice ella misma que sus condiciones *«se confirman en tienda antes de trasladarlas a un cliente»*.
- **Tabla de copy para los códigos de aviso.** C30a y C34 emiten **códigos**, no prosa, así que el castellano lo escribe esta capa. Hay precedente literal en la spec viva del panel —*«MUST NOT render the retriever's raw match reason values, which are engineering vocabulary»*—, incluida su regla de tolerar un valor desconocido con una etiqueta neutra en vez de romper la fila.

> **Revisada el 2026-09-13, al implementar C30a. Sin cambios de alcance, y con dos garantías
> que antes no tenía.**
>
> - **`should require variant confirmation when family has multiple members` deja de poder
>   pasar en vacío.** El contrato impone ahora *familia nula ⇒ exactamente un miembro*, y la
>   capa lo construye estructuralmente, así que un grupo sintético de uno no puede disparar la
>   confirmación. Era justamente el fallo que el `family_id` sintético habría dejado pasar.
> - **Las citas ya traen con qué pintarse.** `document_title` y `section_title` llegan
>   rellenos, así que el desplegable no tiene que enseñar un slug, y `claim_scope` viaja en
>   **todas** — verificado en vivo sobre las quince citas de la evidencia de C30a.
>
> La tabla de copy cubre **dos códigos** de `ai-service` (`family_has_variants`,
> `size_label_missing`) más los dos de stock que apila C34, y la regla de etiqueta neutra para
> un código desconocido sigue siendo necesaria: el vocabulario es cerrado, pero versionado.

> **Revisada el 2026-09-22, al explorar e implementar C36. Tres correcciones en el sitio, y ninguna
> de alcance.**
>
> - **La tabla de copy cubre cinco códigos, no cuatro, y dos del vocabulario no llevan fila.**
>   `classify_query` corre **sólo en M1** y las dos rutas de C34 son siempre ancladas, así que
>   `query_out_of_domain` y `query_not_in_catalogue` **no pueden llegar a esta pantalla** y
>   `clarification_question` es constante `null`. Escribir su castellano daría dos pruebas verdes
>   sobre caminos imposibles; en su lugar hay **un test que comprueba que caen en la etiqueta
>   neutra**. `clarification_question` se lee del contrato y se pinta si llegara, sin bloque ni copy
>   propios: es un campo del objeto de transferencia, no una funcionalidad. Los cinco con fila son
>   `family_has_variants`, `stock_critical`, `family_members_out_of_stock`, `knowledge_not_covered` y
>   `size_label_missing`.
> - **`size_label_missing` no se pinta como los otros.** Salta en el **58,3 %** de las fichas y está
>   anticorrelacionado con tener familia —**4,0 %** con ella contra **92,5 %** sin ella—, así que
>   informa del estado del enriquecimiento y no de la pieza. Va como **línea neutra junto al SKU**,
>   nunca en el bloque de avisos, y **se pinta siempre**: no se suprime nada que el backend haya
>   emitido. Como alerta canibalizaría a `stock_critical`, que salta en el 3,9 % y sí puede costar una
>   venta.
> - **El test de variantes se precisa.** `should require variant confirmation…` no basta: lo que hay
>   que sostener es que **ningún miembro está preseleccionado** y que no existe acción de venta que no
>   nombre a uno. Son dos tests, y la garantía es **estructural** —el bloque no tiene estado de
>   selección— en vez de una regla que alguien tenga que mantener.
>
> **La ruta es propia**: `/sales/new/assist/:productId`, con carga perezosa y **tres entradas** —la
> fila del panel, el producto elegido en la página de venta y la pieza resuelta tras escanear—, porque
> la situación que la ficha nombra, *el cliente con la pieza en la mano*, llega por las dos últimas.
> **Corrección al ticket**: `scan.tsx` **no tiene punto de venta** (cero coincidencias de `pointOfSale`
> en el fichero), así que esa entrada navega sin estado y la ficha cae en su selector de respaldo por
> rol.
>
> **Implementada el 2026-09-22**: 129 tests nuevos, cero nombres nuevos en rojo contra la línea base,
> `openapi.json` idéntico byte a byte. Detalle en
> [c36-implementation-measurements.md](informes/c36-implementation-measurements.md).

**Tests.** `should require variant confirmation when family has multiple members`; **`should preselect no member when the group has several`**; `should show substitutes block when selected product is out of stock`; `should render citations when pitch has sources`; **`should mark an establishment claim differently from a general one`**; **`should fall back to a neutral label for an unknown warning code`**; **`should label a router refusal code with the neutral fallback`**; **`should render size label missing as a piece attribute and not as a warning`**; **`should tell a degraded card from one whose argument was not generated`**. *(`should render complementary block when recommendations exist` no se escribe: su bloque se retiró con C27.)*

---

#### ~~C37 · `add-frontend-inventory-review-and-print`~~ ⛔

> **⛔ Anulado el 2026-08-31** con la rama de C19 (§0). Pantalla de React sin IA, y su vista imprimible ya era el corte nº 5 del §6. Ficha conservada como registro.

**Objetivo.** Aprobación humana de recomendaciones y salida física. Sustituye a la packing list completa.
**Prereq.** C29, C35 · **Zona.** `frontend/src/`
**Alcance.** Pantalla de revisión con filtros por tipo y POS, señales visibles, motivo, y aprobar/rechazar por recomendación; desde las aprobadas, **vista imprimible agrupada por POS destino** (SKU, nombre, foto, cantidad, origen, motivo) usable en móvil. **Sin máquina de estados de packing list.**
**Tests.** `should list proposals grouped by recommendation type`; `should approve recommendation and remove it from pending list`; `should render printable view grouped by destination pos`; `should show substitute origin when recommendation is a substitute`.

---

#### ~~C38 · `add-generation-and-agent-evals`~~ ⛔

> **RETIRADO ENTERO el 2026-09-27.** La ficha se conserva como registro, igual que las de C19, C27,
> C29, C33, C35 y C37. La sesión se abrió para explorar **su implementación** y la cerró retirándolo,
> un día después de que perdiera RAGAS, y **por valor marginal sobre mediciones tomadas en la propia
> sesión** — detalle completo en el §0, *«C38 se retira entero»*.
>
> **Las tres piezas que quedaban, y por qué cae cada una.** El **validador** resultó ser **un espejo**:
> la regla que su mitad .NET aplicaría es la misma que la puerta numérica de Python ya aplica al mismo
> texto, así que su cifra esperada es **cero**. Sigue siendo un seguro defendible —de los tres caminos
> sólo la ficha de venta comprueba algo en .NET; `FreeQuerySearchService` y `AgentAssistService` hacen
> `Pitch = ai.Pitch`— pero es un seguro y no un arreglo, porque `placeholder_in_free_query` es causa
> dura desde C40 y C42 midió **0 de 102**. Los **escenarios** no necesitan pasada: los 20 de
> `calibration.yaml` están corridos **dos veces contra el proveedor real** y sus filas ya traen
> veredicto y estado terminal — **17 de 20** cumplen con `v6`, con **2 de 20 de ruido** entre pasadas.
> Y los **adversarios** eran la única pieza que arrancaba de verdad en cero: dos tests, los dos
> estructurales.
>
> **Sobreviven tres tareas dentro de C39b** *(en C39 cuando esto se escribió; el mismo día se partió)*: definir el éxito de tarea, emitir la tabla con
> `agent_sweep --rescore`, y declarar el validador .NET no implementado con su vía de cierre. **No
> sobrevive nada que necesite una rama.**
>
> **Y se pasa por encima del §6**, que listaba «el validador de C38» entre lo que nunca se recorta.
> Primera vez que un elemento de esa lista cae, y queda dicho aquí en vez de aparecer como una
> discrepancia entre el README y el plan.

*Lo que sigue es el registro anterior, del día en que la ficha perdió RAGAS y conservaba las otras
tres piezas. Se conserva porque es el razonamiento contra el que se leen las dos mediciones de arriba.*

> **Reducido a su mínima expresión el 2026-09-26, y RAGAS sale entero.** Se dispara el corte que
> esta misma ficha llevaba **pre-escrito desde el principio** —véase *Orden obligatorio* al final—,
> y se dispara **por valor marginal, no por plazo**: lo que el §5 de la convocatoria premia es
> *«evals reales, no sólo pruebas manuales»*, y eso ya lo sostienen el golden set de 72 consultas en
> dos lecturas con *pooling* (C24), la recalibración de C25, las métricas de revisión humana sobre
> 204 perfiles (C28), el barrido de generación con 0 violaciones en 120 (C30b), la matriz de
> confusión de 119 casos (C31), el barrido del agente con p50/p95 y coste por brazo (C32b) y las
> cinco cifras de C40. **RAGAS añadiría una fila más a un informe ya denso** a cambio de una
> dependencia pesada, un juez LLM, cuota de proveedor y el MITM de Norton de la máquina de
> desarrollo. Se retira, y la *alucinación con coartada* **pasa a limitación declarada con su vía de
> cierre escrita**, que es exactamente lo que el §5 premia en el otro epígrafe —*«se identifican
> limitaciones actuales y se propone cómo resolverlas»*— y lo que el §11.3 ya venía argumentando al
> decidir *«sin LLM juez»* para el camino de servicio.
>
> **Coste de la retirada, medido y pequeño:** **cero** referencias a C38 en specs vivas, y sólo
> cuatro comentarios de código (`assist/pitch.py`, `assist/schema.py`, `assist/verification.py`,
> `evals/assist_sweep.py`) más una línea del README de `ai-service` dicen «se mide con RAGAS en
> C38». Se reescriben aquí.

**Objetivo.** Cerrar la evaluación con lo que el PF puntúa: validador anti-alucinación, escenarios del agente de venta y casos adversarios.
**Prereq.** C24, **C30b**, **C32b**, C34, **C42** *(afinado el 13 sep; ~~C35~~, anulado · sufijo puesto el 20 sep al partir C32 · **C42 añadido el 26 sep**)* · **Zona.** `ai-service/src/jbg_ai/evals/` + `Application/`
**Alcance, reducido** *(26 sep)*. (1) **Validador determinista** que extrae toda cifra de precio/stock de la respuesta final y la contrasta con el hidratador, umbral **cero fallos**, más su equivalente en .NET antes de responder — es la pieza con mejor retorno y **no arranca en cero**, porque C30b ya corre la puerta por lista blanca en ejecución y `evals/free_query_gate.py` ya mide el modo libre; (2) **escenarios de agente de venta puntuados**, con éxito definido, tools invocadas contra esperadas, pasos, coste medio y tasa de escalado — **una decena larga basta para publicar la tabla**, y la muestra sale de `evals/assist/sweep-sample.yaml`, no del golden set, que no ancla ninguna pieza; (3) **casos adversarios** con criterio de bloqueo por categoría, incluido el que C30b nombró: *preguntar por un material describiéndolo sin nombrarlo*. Todo integrado en el runner e informe de C24.
**~~(4) RAGAS~~** — **retirado el 2026-09-26.** Pasa a limitación declarada del §15 con su vía de cierre: *faithfulness* sobre el subconjunto con citas, que el arnés ya persiste **alineado por afirmación** gracias a los tramos de apoyo que C30b guarda.
**Por qué gana C42 de prerrequisito** *(26 sep)*. C42 sube la tarea del agente de `assist/v4` a `assist/v5` para que deje de escribir `{{price}}` y `{{stock}}` sobre un payload sin ancla. Unas cifras de generación del agente tomadas antes de ese cambio **describirían un prompt sustituido**, que es la misma razón por la que C40 tuvo que ir antes que este change.
**Recortado el 31 ago** con la rama de C19 (§0): salen los **8-10 escenarios de agente de inventario** —no hay segundo agente— y el **test de fidelidad del perfil por POS**, que evaluaba C33. Sobrevive lo que el PF puntúa: validador, escenarios de venta, adversarios y ~~RAGAS~~ *(retirado el 26 sep, arriba)*.
**Tests.** `test_detects_injected_fake_price_in_response`; `test_ignores_numbers_that_are_sizes_or_skus`; `test_scenario_runner_replays_multi_turn_conversation`; `test_injection_cases_all_blocked`; .NET: `Response_WithUnverifiedNumber_IsRejected`. **Los cinco siguen en pie tras la reducción**: ninguno era de RAGAS, que es otra señal de dónde estaba el valor.
**Tres cosas que C30b le deja resueltas de antemano** *(13 sep)*. **(1) El validador ya no arranca en cero**: la puerta numérica por lista blanca corre **en ejecución** dentro de C30b, así que aquí se evalúa un invariante que el sistema ya sostiene en vez de descubrirlo. **(2) La excepción de persistencia está declarada**: el pitch no se persiste ni se loguea en el camino de servicio, pero **el arnés sí guarda el texto generado** —en `evals/results/` y en `ai.eval_*`, atado a `run_id`, `git_sha` y `prompt_version`—, y eso viene escrito en la spec de C30b. Sin esa cláusula, la primera sesión de aquí rompe el invariante sin darse cuenta o se queda bloqueada por él. **(3) Un caso adversario nuevo, nombrado**: *preguntar por un material describiéndolo sin nombrarlo*. Es el hueco de **M1**, el único modo donde no hay pieza y por tanto no se puede aplicar el filtro de slug de C30a, sobre nueve fichas que C23 describe como *«structurally identical»*.

> **Lo que C30b le deja hecho y lo que le deja pendiente, al implementarse** *(14 sep)*. **(1) La
> excepción de persistencia ya no está sólo escrita: está implementada.** `evals/assist_sweep.py`
> guarda el **objeto de generación completo** —el argumentario más cada cita usada con su tramo de
> apoyo, y también el objeto del primer intento antes de la reparación— atado a `run_id`, `git_sha`
> y `prompt_version`, fuera del camino de servicio, en `evals/results/`. Con los tramos, los pares
> afirmación↔cita llegan **ya alineados** y *faithfulness* se puede medir por afirmación en vez de
> sobre la respuesta entera. **(2) El golden set no sirve para la generación, y ya está comprobado:
> 72 consultas y ninguna ancla una pieza.** C30b declara su propia muestra en
> `ai-service/evals/assist/sweep-sample.yaml` —40 piezas, estratificadas a partes iguales entre 1
> material y ≥2, seleccionadas por `md5(product_id)` y **escritas, no re-derivadas**—, y **es de ahí
> de donde deben salir los escenarios de generación de aquí**. La estratificación no es proporcional
> a propósito: medido sobre el índice, las piezas de ≥2 materiales son el **7,8 %**, y son las
> únicas que arrastran la sección de piezas mixtas. **(3) Lo que C30b mide y lo que deja para aquí:**
> publica **tasa de rechazo clasificada por causa** y coste, y **no** publica *faithfulness* — la
> alucinación con coartada sobrevive a las tres comprobaciones deterministas y está **declarada como
> limitación en la capability**, con estas palabras, para que se mida aquí y no se dé por cerrada.
**Orden obligatorio si hay que partirlo:** validador → escenarios de venta → adversarios → ~~RAGAS~~. **RAGAS es lo primero que se cae** — *y se cayó, el 2026-09-26. El orden sigue vigente para los tres que quedan.*

---

#### C40 · `add-frontend-free-query-panel` ✅

> **Nace el 2026-09-24**, durante la comprobación en demo de C36 (tarea 8.5). No estaba en el plan:
> la sesión iba a verificar la ficha de venta y destapó que **el panel de búsqueda asistida llevaba
> todo el proyecto sirviendo por su ruta degradada**, con los filtros descartándose en silencio.
> Exploración en dos pasadas: [c40-exploration-decisions.md](informes/c40-exploration-decisions.md)
> —§1-§9 contra el servicio real, §10 contra el código— y la tabla de estados de la pantalla en
> [c40-m1-panel-states.md](informes/c40-m1-panel-states.md).

**Objetivo.** Que el **tercer modo de la venta asistida —la pregunta libre sin pieza, M1— llegue al operario**, convirtiendo el panel de búsqueda de C16 en su superficie en vez de construir una pantalla nueva. Con ello se cierran **tres limitaciones declaradas del §15** del diseño.
**Prereq.** C16, C31, C34, C36 · **Zona.** `ai-service/src/jbg_ai/`, `backend/src/`, `frontend/src/` — **tres capas, y el contrato se mueve**, que es lo que lo separa de C36 sin discusión.
**Va antes de C38**, y no es indiferente: C40 sube el prompt a `assist/v5` y mueve la fase de la abstención, así que unas cifras de C38 tomadas antes describirían un prompt sustituido y una fase movida.

**Alcance, en seis tramos con línea de corte fijada de antemano** (§10.10 del informe; sustituye a la del §4). El criterio de ordenación es **cuánto engaña hoy la pantalla**, no cuánto cuesta:

1. **Lo que hoy miente en silencio, y no toca el contrato** — sólo .NET y frontend, **archivable solo**: los **filtros en la ruta degradada** (D5: `PieceType` al 97,7 %, un `JOIN` y dos `AND`), el **badge de disponibilidad** con sus **cuatro estados** y su **ruta de lectura nueva** de los dos interruptores por POS (D16), **`degraded_reason` al DTO** —seis valores que `SalesAssistService` ya calcula y descarta— y **`SearchOrigin = 4`**, que no abre migración y convierte la ablación del toggle en una consulta SQL (D15).
2. **El contrato se mueve, con tres prerrequisitos**: `filters` en `AssistRequest` (D2, adición pura, cuatro sitios); **`assist/v5` para que las tareas de consulta libre no hablen de precio ni disponibilidad, más la causa dura `placeholder_in_free_query`** (D11); **`uncovered` en M1 y una cuarta tarea de consulta libre sin cobertura** (D12); el **segundo endpoint** `POST /api/ai/search/assisted` con su interruptor, su límite, su presupuesto y su circuito (D14); el **toggle** (D3) y el **castellano de los dos rechazos** (§15.13). Y dos entregables que no son código: **la tabla de estados** y la **medición de latencia extremo a extremo por .NET**.
3. **La abstención lee una sonda sin filtro** (D17), sólo cuando hay filtros, con `filters_too_narrow` como código nuevo del vocabulario cerrado y el requisito de persistencia para `--rescore`. **Toca `retrieval-abstention`, spec viva con tres consumidores** — el panel, los sustitutos y la tool `buscar_catalogo` del agente. Y la **Q3 corregida**: `route=none` son dos estados.
4. **«Todos los puntos de venta»** (D6 y D13), con la etiqueta que nombra la tienda (D7) y la ficha deshabilitada sin tienda.
5. **La fila enseña su grupo** (D10): *«también en XS, S, M, L y 4 tallas más»*, con el 19,2 % de filas que el agrupado ya ahorra.
6. **El embudo de observabilidad** para administrador: latencia partida, modelo, tokens, contadores. **Va el último porque es el único que no arregla nada que hoy engañe.**

**Fuera de alcance, declarado:** la **telemetría de uso** y el panel de administrador sobre todas las consultas, que son **una cuarta zona** —migración de EF Core— y salen como change propio (§7 del informe); el ***streaming* / SSE** del argumentario; el **consumidor del agente**, que arrastra dos tareas diferidas de C32b; y el `v5` de `dangling_citation` en la ruta `both`, que es trabajo de prompt y no de pantalla.

> **El hallazgo que gobierna la línea de corte** *(§10.1 del informe)*. **.NET rechaza M1 hoy, por
> construcción**: `AiGatewayClient.cs:671` lanza `ArgumentException` sin `product_id`, porque
> `PitchPlaceholderResolver` **retira el argumentario siempre que no hay ancla** y el prompt `v3`
> ordena escribir `{{price}}` y `{{stock}}` **también en las tres tareas de consulta libre**. Medido
> en C30b sobre los modos anclados: `{{price}}` en **147 de 213** y `{{stock}}` en **188 de 213**.
> Las 42 consultas del informe se midieron con `curl` **contra Python**, saltándose esa etapa, así
> que su «37 respuestas con argumentario» **no dice nada de lo que el operario vería**. Sin el tramo
> 2 completo, C40 entregaría **un panel asistido sin prosa** — la misma avería que vino a corregir.

> **Dos limitaciones declaradas que C40 cierra, y una que no.** Cierra la **§15.12** —los tres modos
> llegan al operario— y la **§15.13** —el rechazo cortés tiene pantalla, y con él los dos códigos
> que C36 se negó a traducir con razón, porque desde la ficha eran caminos imposibles y desde el
> panel son caminos reales—. Y cierra, **casi gratis y sin estar en la lista**, la **limitación 3 de
> C34 / D12 de C36**: una pieza no indexada deja de verse igual que una caída, con un campo que .NET
> ya calcula. **No cierra** el consumidor del agente. La **§15.14**, la telemetría, la cierra el
> change que sale de aquí.

> **Lo que la segunda pasada corrige de la primera** *(§10.7 y §10.8)*. **`route=none` son dos
> estados** y sólo `intent` los separa: con `in_domain` el clasificador corrió y se contradijo
> —devolvió veredicto servido con `index` nulo, 11,9 % medido— y se arregla **coercionando a
> `both`**, porque el *fail-open* ya recupera las dos ramas y luego tira la prosa; con
> `unclassified` **el clasificador no corrió**, y ahí pedirle al operario que reformule es echarle
> la culpa de una credencial ausente. **D8 estaba demasiado ancho**: `refusal_codes` se apila en el
> mismo `warnings[]`, así que la partición es **por sujeto del aviso** —los de pieza no se pintan en
> M1, los de consulta sí—. Y **el toggle no es un A/B test**: es una demostración de la ablación; lo
> que la hace medición es `SearchOrigin = 4` más la telemetría de C04.

> **El presupuesto de tiempo está en su techo y hay que medirlo.** `AssistTimeoutMs` es 10.000 con
> mínimo validado de 8.000. C34 midió **p95 7,1 s** extremo a extremo para los modos anclados, que
> **no llaman al enrutador**; M1 le suma ~2 s. La mitigación es el toggle, y la interfaz tiene que
> decir el coste **antes** de pulsarse: **2.500 ms contra 10.000 ms** de presupuesto y **30/min
> contra 10/min** de cupo. Si no cabe, el corte es **no generar en la ruta `catalog` de M1** —el 40 %
> de las generaciones— y queda nombrado en D11 por eso.

**Cinco cifras que la implementación tiene que publicar** *(§10.12)*: marcadores en el argumentario de M1 antes y después de `v5` —**la que decide si M1 tiene prosa**—, reparto de los 16 estados sobre las 42 consultas, latencia p50/p95 por .NET, tasa de `router_index_absent` tras la coerción, y el efecto de la sonda sin filtro sobre una búsqueda filtrada. **Y el artefacto se persiste** con `run_id`, `git_sha` y `prompt_version`: la pasada de 42 del informe no quedó guardada en `evals/results/`, así que es reproducible pero no re-puntuable.

**Tests.** `should disable the assisted mode when the sale assist switch is off for the point of sale`; `should apply piece type and material filters on the degraded path`; `should tell a router refusal from an abstention`; `should tell an unrouted query from a degraded classifier`; `should not announce an empty result set on the knowledge route`; `should render the clarification question and return focus to the query box`; `should label a withdrawn citation without alarming`; **`test_free_query_pitch_carries_no_placeholder`**; **`test_free_query_without_corpus_uses_the_uncovered_task`**; **`test_abstention_reads_the_unfiltered_profile`**; **`test_served_verdict_without_index_is_routed_to_both`**; y el de ámbito: `ForAllPointsOfSale_IsRefusedByEveryPointOfSaleOperation`.

---

#### C41 · `add-pos-projection-scheduled-drain` 🔴

> **Nace el 2026-09-25**, durante las pruebas manuales posteriores al cierre de C40. No estaba en el
> plan. Al levantar el entorno **ninguna de las once tiendas activas tenía la proyección fresca**: el
> *checkpoint* `ai.sync_checkpoint.last_incremental_sync_at` del feed `pos-availability` venía del
> **5 de septiembre** contra un umbral de **3 600 s**, y hubo que drenarla a mano
> (`sync-pos --full`: 34 páginas, 6 050 *upserts*, 0 fallidas) para que las pruebas midieran el
> sistema y no su desconfiguración.
>
> **Y es la segunda vez, que es lo que lo convierte en ficha.** El §8 del
> [informe de C40](informes/c40-implementation-measurements.md) declara **la misma manipulación** como
> una de sus cuatro del entorno, con 19,7 días. Dos sesiones distintas, la misma causa, el mismo
> arreglo a mano: **la frescura no tiene dueño**, porque `sync-pos` es sólo CLI y alguien tiene que
> acordarse. Petición registrada en el
> [ticket](../../openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md).

**Objetivo.** Que la frescura de `ai.pos_projection` **deje de ser un acto manual**, y que su edad
**se diga antes de buscar** en vez de quedarse en una línea de etapa que no llega a ninguna pantalla.
**Prereq.** C22 (que creó la proyección y el prefiltro), C17 (que creó el informe de salud enriquecido y la tarjeta de administrador donde va la edad) · **Zona.** `ai-service/` —**corregido el 26 sep**, ver abajo—, más `deploy/demo/` y un retoque en el DTO de salud de `backend/src/` y en la tarjeta de `frontend/src/`. **No toca el contrato congelado ni añade migración**: `ai.pos_projection` y `ai.sync_checkpoint` existen desde C22, y no se añade ruta bajo `/v1`.
**No compite con C38 ni C39**: no toca prompt, ni fase de abstención, ni `openapi.json`, así que puede ir antes, después o en paralelo — **pero va antes de cualquier remedición**, porque hoy el entorno está a **14,4 veces** el techo de rancidez.

> **Corregido el 2026-09-26, al explorar C41 contra el código y contra la base local.** Esta ficha
> declaraba **tres cosas que la exploración refutó**, y las tres se reescriben abajo en vez de
> matizarse. **(1) El núcleo no es un `BackgroundService` de .NET**: lo que la ficha pedía no es un
> planificador, es **una segunda implementación del protocolo del keyset**, y como la spec viva obliga
> a conservar el CLI quedarían **dos drenadores escribiendo la misma fila de checkpoint** — la
> corrupción de la que esta misma ficha avisa. Además .NET tendría que escribir `ai.*`, frontera que
> `bootstrap.sql` hace **estructural por *grants***. **(2) El tramo aditivo no va en
> `GET /api/ai/search/availability`**, que tiene un `MUST` de spec viva prohibiéndole llamar al
> servicio de IA y cuyo método es síncrono: va en **`GET /health`**, *mapping* abierto en los dos lados,
> con **coste de contrato cero**, y llega a la tarjeta que C17 ya construyó. **(3) La zona era
> `backend/` y `frontend/` y es `ai-service/`**, consecuencia directa de (1).
>
> Y **dos cosas más que esta ficha decía mal**: *«es la segunda vez»* — **es la tercera**, porque C34
> encontró la proyección **vacía** en la demo, que es otro modo de fallo (503 en toda recuperación) y
> sigue abierto en `DEFERRED_TASKS.md`; y el prerrequisito **C40 no lo es** — la lectura previa que
> creó C40 deja de usarse, y quien aporta la superficie es **C17**.
>
> **Y un hallazgo que obliga a anotar un informe publicado.** La manipulación del §8 del informe de C40
> —*«se actualizaron `refreshed_at` y `computed_as_of` en 1.176 filas»*— **se aplicó a la columna
> equivocada**, porque el guard lee `ai.sync_checkpoint.last_incremental_sync_at`. Cuatro pruebas: los
> dos campos del checkpoint son **idénticos** (2026-09-25 20:49:24 UTC), luego el único drenaje fue el
> `--full` de la sesión de C41; el artefacto del grupo 8 está fechado **15 h 07 min antes**; quedan
> **94 filas** con la huella del `UPDATE` (`computed_as_of = 2026-09-25 05:32:04`, diez minutos antes de
> medir); y «1.176» es el **total exacto de filas del POS `0388f003…`**. **El reparto de los dieciséis
> estados describe el sistema degradado**; la latencia **se sostiene** —sin ámbito el SQL es 2-3 ms más
> lento contra un p95 de 7.160 ms dominado por dos llamadas a proveedor, y está verificado que .NET
> **no repide** cuando la página llega corta—. **Se anota, no se rehace**: el arnés del grupo 8 nunca
> se commiteó, así que rehacerlo es reescribirlo. Historia
> [HU-AIENG-041](../Historias/AI-Eng/HU-AIENG-041.md), ticket
> [T-AIENG-041](../../openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md).

**Lo primero que hay que entender, porque la lectura intuitiva está equivocada.** La rancidez **no es
una fuga**. Hay dos filtros y sólo uno es la frontera: el prefiltro de `ai.pos_projection` estrecha la
**ventana de candidatos**, y `Carried()` —en `AssistedSearchRepository`, arrancando desde `Inventories`
con `PointOfSaleId == pointOfSaleId`— es el que decide qué se sirve, en **toda** respuesta. Es la
convención 14: *el servicio de IA propone candidatos; el backend pone la verdad*. Un operario **nunca**
ve una pieza que su tienda no lleva, pase lo que pase con la proyección.

Lo que la rancidez causa es que **la página llegue corta**: el comportamiento de **antes de C22**, que
C22 midió — **ocho de los once puntos de venta** por debajo de una página en al menos **seis de cada
veinte** búsquedas, y en el peor caso **sobrevivía un solo producto**. Y **degradar es la decisión
correcta**, no un descuido: filtrar con una proyección de veinte días esconderría las piezas asignadas
después del último drenaje, un **falso negativo invisible**. Mostrar candidatos de más es recuperable
porque .NET los tira; esconder algo vendible no lo es. **Esta ficha no toca esa decisión.**

**Alcance, en tres tramos con línea de corte:**

1. **El drenaje programado, y no se corta.** Una tarea en el `lifespan` de FastAPI de `jbg-ai` que reutiliza `sync_pos_availability` **sin reescribirlo** — una sola implementación del protocolo del keyset. **Al arrancar y por intervalo**, y el disparo que de verdad arregla es **el de arranque**: los tres incidentes ocurrieron *levantando un entorno para probar*, y un cron de host no corre en el portátil de nadie. Completo si no hay checkpoint —lo que cura el caso de C34 y es **gratis**, porque `resolve_start_cursor` ya devuelve `(None, None)`—, incremental si lo hay, cada **600 s**: no elegido sino **derivado** de `techo / intervalo ≥ 4`, que tolera cinco fallos seguidos antes de que el guard degrade. **La tarea no bloquea el arranque**, o el `HEALTHCHECK` marcaría el contenedor *unhealthy* y el despliegue se caería por culpa de la mejora. **Con lock, o no se construye**: `ai.sync_checkpoint` es **una fila por feed** (`PRIMARY KEY (feed)`) con `watermark` y `since_id`, y dos drenajes concurrentes escriben el keyset entrelazado — un keyset corrupto **no falla: se salta filas en silencio**. `pg_try_advisory_lock` **no bloqueante y DENTRO del drenaje**, para que cubra también **al CLI corrido a mano**, que es el caso que de verdad ocurrió las tres veces y que esta ficha se dejaba fuera. Y `failed_pages` no se puede tragar: el CLI ya devuelve 1 cuando hay páginas fallidas, con su razón escrita.
2. **La edad, dicha donde ya hay pantalla.** **`GET /health`**, no la lectura previa de C40: el informe de salud es *mapping* abierto en los dos lados —C17 lo dejó así *«para que enriquecerlo no mueva el contrato congelado»*— y llega a la **tarjeta de estado del administrador**, que ya existe. Gana `projection` con la edad tomada del **checkpoint**, el último drenaje, el último completo, `stale` contra el techo configurado, las páginas fallidas y **cuántas tiendas se han quedado sin ámbito** — que es el modo de fallo de C34, es **por tienda** y hoy no lo dice nadie. `resolve_scope` ya calcula `reported_age` y `stale`, así que el trabajo es **transportarlos, no computarlos**. Y `verify.sh` gana su **quinto** motivo de fallo, porque hoy *«un entorno con índice lleno y proyección vacía pasa la verificación posterior al despliegue»*. Es **informar, no delegar**.
3. **Cortado en el diseño, con su razón escrita: el drenaje manual, tampoco para el administrador.** **El argumento que mata el botón del operario mata también el suyo.** Con el tramo 1 hecho —arranque más 600 s—, «refrescar ahora» ahorra como mucho diez minutos de espera, y eso no paga una ruta nueva en un contrato congelado cuya superficie está enumerada en un `MUST`. El único caso que ningún intervalo cubre es el **completo**, y para eso basta que la tarjeta informe y que el `docker exec` esté documentado al lado. **Para el operario limitado a su tienda tampoco se podía construir hoy**, y no por diseño sino por la forma de las piezas: no hay ruta HTTP para ese drenaje (el contrato publica once bajo `/v1` más `/health`, y `POST /v1/index/sync` es la del catálogo); `GET /api/ai/index-feed/pos-availability` acepta **sólo** `since` y `sinceId` —feed paginado por keyset sobre todas las tiendas, no consulta puntual—; y las rutas de índice usan el principal de **catálogo**, que no lleva `pos_id`.

> **El argumento que pesa más que los tres, y que ahora decide los dos botones.** Un botón «refrescar»
> en la pantalla del mostrador le entrega al operario **un problema que no es suyo**. La rancidez no le
> esconde piezas; lo único que le pasa es que la página llega corta. El botón le enseñaría que cuando
> la búsqueda da poco la culpa es de un dato que él debe arreglar, y le invitaría a pulsarlo cuando el
> buscador simplemente no encontró mucho — que es otra cosa. **Con el tramo 1 hecho, el botón del
> operario no tiene caso de uso** — *y el del administrador tampoco*, que es la conclusión que esta
> ficha no sacaba y que el 26 sep se sacó.

**Una nota de método que cuesta una corrección.** La frescura **no se mide** leyendo
`MAX(refreshed_at)` de las filas: el guard lee el *checkpoint*. El feed es **incremental por keyset**,
así que una asignación que no cambia nunca se re-emite y `refreshed_at` registra cuándo cambió **la
asignación**, no cuándo se miró la proyección. El *docstring* de `retrieval/projection.py` advierte de
que leerlo de las filas *«reportaría meses de rancidez sobre una proyección sincronizada hace treinta
segundos»*. La sesión que abrió esta ficha cometió ese error y acertó **por casualidad**, porque el
checkpoint venía del mismo drenaje. **Cualquier verificación de este change lee el checkpoint.**

#### C42 · `add-frontend-agent-panel` 🔴

> **Nace el 2026-09-26**, al valorar la cola pendiente del Proyecto Final. **No estaba en el plan.**
> La sesión se abrió para decidir entre implementar C38 completo o dar superficie al agente, y la
> comparación de valor contra esfuerzo salió a favor del segundo por un motivo que el §5 de la
> convocatoria escribe: *«el sistema debe poder probarse»*. Explorado **contra el código y no contra
> el servicio** en [c42-exploration-decisions.md](informes/c42-exploration-decisions.md): **ocho
> hallazgos, doce decisiones** y **tres cosas que hay que medir o comprobar antes de escribir la
> primera tarea**, nombradas en su §11.

**Objetivo.** Que el **agente de venta llegue al operario**. `POST /v1/assist/agent` está entregado, probado y medido con proveedor real desde C32b, y **no lo llama nadie**: `IAiGatewayClient` tiene siete métodos y ninguno es el suyo. De los cinco pilares que el PF nombra —CAG, RAG, **agentes**, evaluación y despliegue— es **el único sin superficie**, y por tanto el único que no puede aparecer ni en la URL pública ni en el vídeo de 2-3 minutos.
**Prereq.** C32b, C34, C36, **C40** · **Zona.** `ai-service/src/jbg_ai/`, `backend/src/`, `frontend/src/` — **tres capas, y el contrato se mueve**, igual que C40.
**Va antes de C38**, por la misma cadena de prompts que puso a C40 antes que a C38: aquí la tarea del agente sube a `assist/v5`, así que unas cifras de generación del agente tomadas antes describirían un prompt sustituido.

**El agente no tiene M1, M2 ni M3, y conviene decirlo porque no es lo que se espera.** `AgentAssistRequest` **no lleva `product_id`, ni `query`, ni `filters`**: lleva `turns`. Los tres modos son una propiedad de `/v1/assist/sale`, leída estructuralmente de qué anclas trae la petición. El agente **no los necesita porque los descubre**: recibe una conversación de hasta 12 turnos y decide él, vuelta a vuelta, cuál de las seis tools congeladas usa. Lo que **no** cambia es que el bucle **no escribe la respuesta** —sólo reúne evidencia—, y por eso `AgentAssistResponse` es subclase de `AssistResponse`: los mismos campos con el mismo significado, más `partial`, `stop_reason`, `iterations`, `tool_calls_used` y `trace`.

**Alcance, en cuatro tramos con línea de corte fijada de antemano.** El criterio es el de C40: **primero lo que impide que la pantalla diga la verdad**.

1. **`ai-service`, y sin esto no hay pantalla que valga** — la tarea del agente **sube a `assist/v5`** con la prohibición de marcadores (D2); **`AgentAssistGroup(AssistGroup)` gana `origin`** (D3, subclase por el precedente de `AgentUsage`, adición pura); y la ruta **acepta token con y sin punto de venta** (D4).
2. **`backend`, el consumidor que no existe** — método en `IAiGatewayClient`; **cliente con nombre propio** de 15 s más margen, sin reintento; **circuito que cuenta `stop_reason=fallo_proveedor` y no cuenta `partial`**, porque esta ruta no devuelve 5xx cuando el proveedor cae; DTO = el `FreeQuerySearchResponse` de C40 más los cinco campos del agente; **`agentAvailable` en la sonda** (D8); y **quinto `SearchOrigin`** (D12).
3. **`frontend`, la pantalla** — ruta `/sales/new/agent` y **cuarta tarjeta** en el hub (D1), con la **puerta cerrada antes de entrar** y sus tres estados (D7); el hilo como eje, **un bloque de respuesta por turno** (D9); la **traza** (D10); y el castellano de los **diez** `stop_reason` (D11). Las filas son `assisted-search-result-row` **sin tocar**; la prosa y las citas, `pitch-block` de C36.
4. **El contador de coste acumulado** en la barra fija. **Va el último porque es el único que no arregla nada que hoy engañe.**

> **El hallazgo que gobierna la línea de corte, y no es una carencia sino una regresión latente que
> C40 introdujo sin tocar el agente.** Tres eslabones, cada uno correcto por separado: la tarea del
> agente vive en **`assist/v4`**, cuyo *Sistema* ordena escribir `{{price}}` y `{{stock}}`
> **siempre**; su payload es un `FreeQueryPayload` con **`is_anchored = False`**, que es correcto
> porque el argumentario habla de varias piezas; y C40 metió **`placeholder_in_free_query` en
> `HARD_VIOLATION_CAUSES`**, disparando exactamente cuando el payload no está anclado. Juntos:
> **un argumentario del agente que obedezca a su propio prompt se retira por construcción.** C40
> arregló las tareas de consulta libre en `v5` y no tocó ésta, porque el agente no tenía consumidor.
> **La tasa real no está medida y es la primera cifra que C42 debe publicar**; la referencia
> comparable es la de C30b sobre modos anclados con `v3`: `{{price}}` en 147 de 213 y `{{stock}}` en
> 188 de 213.
>
> ### ⚠ Corregido por la segunda pasada de exploración de C42 · 2026-09-26 · **las dos frases de arriba son falsas**
>
> **Uno: este hallazgo NO gobierna la línea de corte.** La frase que ordena escribir marcadores es
> **idéntica palabra por palabra** en `assist/v3.md:47` y en `assist/v4.md:59`, y la tarea del agente
> (`v4.md:132-166`) **no menciona precio ni existencias**: hereda esa regla y nada más. Así que C40 ya
> midió este caso exacto —misma frase, payload sin anclar— sobre 90 consultas libres contra el
> proveedor real: **3 de 90 generaciones con marcador y 0 retiradas tras la reparación**. El defecto es
> real y **su urgencia es pequeña**. Lo que de verdad retira el argumentario del agente es
> `dangling_citation`: **85 incidencias y 72 supervivientes** en la pasada de C32b, con el 92,2 % de
> las respuestas trayendo cero citas. Y «consume la reparación única» tampoco es lo que hace el
> código: `assist/pitch.py:24` escribe *«One repair, not one per check»* y `repair_message` recibe la
> lista entera, así que un marcador **se suma a la lista** y no gasta un turno que otra causa fuera a
> usar. **Lo que gobierna la línea de corte es el consumidor .NET**: `IAiGatewayClient` tiene siete
> métodos y ninguno es el del agente, que no es una degradación del 3 % sino el **100 %** del camino.
>
> **Dos: la referencia comparable no es la de C30b.** Los 147 de 213 y 188 de 213 son de los **modos
> anclados**, donde hay UNA pieza y nombrar su precio es natural; en libre hay hasta quince agrupadas
> y lo que se pide es comparar. La cabecera de `assist/v5.md` **ya había escrito que la proporción no
> se traslada**, y la medición de C40 lo confirma: `v3` sobre 90 consultas libres escribió `{{price}}`
> **2 veces** y `{{stock}}` **1**, en 2 de 90 generaciones. La referencia comparable es **ésa**, la del
> análogo estructural de C40, y así se declara al publicar la cifra: **línea base prestada**.

> **El agente no se sirve por defecto, y eso es criterio y no cautela.** Su única cifra comparativa
> hoy dice **×3,0 de coste** y **13,1 % de retirada del argumentario** contra el 2,2 % de la ruta
> determinista. Servir eso por defecto a un joyero sería mala ingeniería; como **ruta propia y
> demostración de ablación** —la misma pregunta en los dos paneles, legible en diez segundos de
> vídeo— la misma cifra pasa de penalización a decisión justificada. El ámbito por defecto es **la
> tienda del operario y no «todas»**, porque sin `pos_id` la etiqueta de disponibilidad es siempre
> «no consta» y **el pivote a sustitutos no se dispara nunca** — que es el comportamiento que el
> agente existe para demostrar, medido 3 de 3 en `sin_existencias` con `gpt-4o`.

**Ejecuta un diseño ya escrito, no lo reabre.** La política de *timeout* y de circuito de esta ruta está **identificada, acotada y no hecha** en `openspec/DEFERRED_TASKS.md` desde C32b, con la tabla que explica por qué no puede ser la de `/v1/assist/sale`: p50 **5,3 s**, p95 **9,0 s**, máximo **11,9 s** sobre 102 peticiones, contra los 5 s que el §6.4 declara para la determinista.

**Fuera de alcance, declarado:** el ***streaming*/SSE** del argumentario; **preguntar por el stock de una tienda concreta o de varias** —ninguna tool acepta punto de venta, y habilitarlo exige un modelo de autorización que hoy no existe, no una tool más—; el **desglose de `usage` por etapa**; la **telemetría de la ficha** y el registro de la consulta de ámbito global, que arrastran migración de EF Core; y los **escenarios puntuados del agente**, que son de C38.

**Hereda el fix de C40.** El ámbito «todos los puntos de venta» resultó **inalcanzable desde el frontal para todos los roles**, y su arreglo —la opción en el selector y que la sonda acepte la ausencia de tienda— vive en `c40-fix-all-shops-scope-unreachable`. C42 lo da por hecho; si no hubiera entrado, entra aquí y se declara.

**Cinco cifras que la implementación tiene que publicar:** marcadores en el argumentario del agente antes y después de `v5` —la que decide si el agente tiene prosa—; tasa de retirada por causa, partida entre `dangling_citation` y `placeholder_in_free_query`; reparto de los `stop_reason`; latencia p50/p95 por .NET; y piezas por respuesta con su reparto catálogo/sustitutos contra el tope de 8. **Y el artefacto se persiste** con `run_id`, `git_sha` y `prompt_version`.

**Tests.** `test_agent_pitch_carries_no_placeholder`; `test_agent_route_accepts_a_token_without_pos_claim`; `test_agent_group_declares_its_origin`; .NET: `AgentAssist_WhenProviderFails_DoesNotOpenTheCircuitOnPartial`, `AgentAssist_UsesItsOwnTimeoutAndNotTheAssistOne`; frontend: `should close the agent card when the probe says the agent is off`, `should open the agent card when the probe cannot answer`, `should keep each turn's answer anchored to its own turn`, `should tell a budget-cut answer from a complete one`, `should label a substitutes group as alternatives`, `should render an answer with prose and no pieces`, `should show the transcript caps before the request is refused`.

---

### Ola 5 — Entrega

---

#### C39a · `redeploy-and-audit-demo-environment` 🔴

> **Nace el 2026-09-27, al partir C39** (§0). La ficha de C39 decía **`Zona. docs`** y el redespliegue
> de la demo no es documentación: toca `compose.demo.yaml`, `deploy/demo/`, `ai-service/Dockerfile` y
> las opciones de `Application/`. El orden con C39b **no es indiferente**: no se documenta un recorrido
> que no se ha recorrido, y este proyecto ya ha pagado cuatro veces por comprobar en la demo lo que las
> tres suites verdes no veían — C40, C41, C42 y `C40_FIX` nacieron así.

**Objetivo.** Que la demo vuelva a estar **desplegada en AWS, accesible desde internet y verificada recorrido a recorrido**, y que su configuración esté auditada contra lo que el código realmente declara.
**Prereq.** todos los vivos · **Zona.** `compose.demo.yaml`, `deploy/demo/`, `ai-service/Dockerfile`, `backend/src/JoiabagurPV.Application/Configuration/`
**Alcance.** (0) **Puerta de entrada**: establecer si el entorno sigue en pie o se desmontó —dos recorridos muy distintos— antes de modificar nada, con su evidencia, al modo de «las tres líneas base» de C42. (0b) **La rama `demo` alcanza a `ai-eng`**: son **84 commits** y es lo que trae C36, C40, C40_FIX, C41 y C42 al entorno, comprobando que el workflow **se ejecuta** y no lo omite su `paths-ignore` de `openspec/**` y `Documentos/**`. (1) **Auditoría completa de `compose.demo.yaml`** contra los ajustes que declaran los tres servicios —`config/settings.py` de `jbg-ai`, las siete clases de opciones de .NET y el entorno del frontend—, publicada como tabla de tres columnas: ajuste declarado · valor en la demo · qué pasa si falta. (2) **Los cuatro huecos ya medidos**: `AiAgentAssist__EnabledByDefault`, `JPV_AGENT_LLM_API_KEY`, `JPV_ROUTER_LLM_API_KEY` y el **corpus de conocimiento dentro de la imagen**, que cierra una tarea diferida de C34 hoy sorteada a mano. (3) **El recorrido del evaluador comprobado a mano** con los cuatro usuarios —`admin` y los tres operadores—, pantalla a pantalla y sobre el entorno desplegado, no en local. (4) **Contraseña de `admin` estable y escrita**. (5) Puesta al día del *runbook*, incluido el §5.5c, cuyo primer drenaje **lo cerró C41** — y el *runbook* **no es pre-PF**: nació el 2026-08-30 con C17 y su último commit es de C41, así que le falta **un solo change**. (6) **`verify.sh` gana dos condiciones de fallo**: corpus vacío y ruta del agente sin respuesta, los dos silenciosos. (7) **La CI se enciende como informativa** sobre `[ai-eng, master]`: hoy `test-backend.yml` y `test-frontend.yml` **no se han ejecutado nunca** porque disparan sobre ramas que no existen. **No puede ser puerta** con 53 y 113 fallos preexistentes, y el defecto hermano de producción sigue siendo de otro change.
**Fuera de alcance.** El README de entrega, el vídeo, el tag y las evidencias: son de C39b. Y **no se añaden variables de Terraform**: los dos *stacks* no tienen ninguna de IA y es correcto — la configuración de IA vive en el compose como literal versionado y en SSM como secreto manual, fuera del *state*.
**Specs que mueve.** `demo-deployment` es capacidad viva con **13 requisitos**, y al menos cuatro se tocan: los secretos que llegan por entorno, los ajustes de comportamiento versionados, la verificación desde dentro del anfitrión y la reproducibilidad de las imágenes.
**Tests.** Verificación desde dentro del anfitrión con `deploy/demo/verify.sh` ampliado a la ruta del agente y al recuento de `ai.knowledge_chunk`; y `openspec validate --all --strict` a cero fallos.

> **Implementado el 2026-09-27, partido otra vez, y con tres refutaciones propias** (§0 · *C39a se
> implementa*). Lo entregado: los cinco huecos cerrados y **un sexto que no estaba en la ficha** —la
> resolución de `CORPUS_DIR` dentro del entorno virtual, que amplía la zona a `ai-service/src`—, la
> auditoría de los 51 ajustes de `jbg-ai` y las 7 clases de .NET publicada, las dos condiciones nuevas de
> verificación **probadas en los dos sentidos**, la CI encendida sobre ramas que existen, y el *runbook*
> al día con C42 y con la caducidad del bundle de CA.
>
> **Medido:** `ai-service` **1.664 passed**; `test_corpus_location.py` **5 passed**; snapshot del contrato
> **4 passed** y `openapi.json` intacto; imagen **426 MB antes y después**; contexto **388 kB → 2,78 MB**;
> línea base de las otras dos suites **50 de 1.408** y **113 de 959**, las dos dentro de banda.
>
> **La verificación del entorno desplegado es de C39a-bis**, y la partición es lo que permite archivar
> esto antes de desplegar.

---

#### C39b · `finalize-pf-readme-and-evidence` 🔴

> **Queda con el alcance original de C39 menos el despliegue** *(27 sep, §0)*, más tres cosas que esa
> misma sesión añade: la **frontera contable** entre lo preexistente y el PF, el **resumen de fases** y
> la **taxonomía de métodos de búsqueda**. Y hereda las **tres tareas que sobreviven a C38**: definir
> el éxito de tarea del agente, emitir su tabla con `agent_sweep --rescore`, y declarar el validador
> .NET no implementado con su vía de cierre.
>
> **La frontera es contable, y eso vale más que la prosa:** **74** changes archivados, **32** antes del
> 2026-08-03 que son el MVP que ya existía —POS, usuarios, catálogo, ventas, inventario, devoluciones,
> componentes, informes, despliegue AWS, reconocimiento por *embeddings*, escaneo de códigos— y **41**
> del 2026-08-03 en adelante que son el Proyecto Final. Verificable por cualquiera contra
> `openspec/changes/archive/`.

**Objetivo.** Empaquetar la entrega para que un evaluador externo entienda, reproduzca y pruebe el sistema.
**Prereq.** **C39a** · **Zona.** docs
**Alcance.** README del PF (dominio, arquitectura con la frontera .NET/Python justificada, CAG/RAG/agentes/evaluación/despliegue, arranque local, autoría, limitaciones, próximos pasos); **tabla de ablations v0→v3**; **métricas de revisión humana** (tasa de corrección y tiempo medio); sección del reranking descartado con su protocolo; progresión de prompts v1→v2 con impacto medido; **declaración explícita de lo que queda para fase posterior** (packing list, liquidación, upsell, políticas de inventario); vídeo de 2-3 min; usuario demo; `docker compose up` verificado desde cero; rama `finalproject-[INICIALES]` y tag `v1.0-final-[INICIALES]`.
**Tres declaraciones nuevas** *(31 ago)*, que son puntos a favor si están escritas y huecos si faltan: **un solo agente**, con el diseño del de inventario (§10 del documento hermano) adjunto como próximo paso; **golden set sin acuerdo entre anotadores**, por etiquetador único; y **proyecto individual**, no en pareja.
**Tests.** Ensayo de reproducibilidad en máquina limpia y `openspec validate --all`.

---

## 4. Grafo de dependencias

**Solo changes vivos** *(reescrito el 2026-08-31)*. Los cinco anulados —C19, C29, C33, C35, C37— y sus aristas ya no aparecen: el grafo es lo que más se consulta para decidir qué se abre a continuación, y dibujar nodos muertos ahí es la forma más rápida de volver a planificarlos por error. Quedan en la tabla maestra del §2 y en sus fichas del §3.

```mermaid
flowchart LR
    C01 --> C02 & C05 & C06a
    C02 --> C03
    C03 --> C08 & C15
    C05 --> C11
    C06a --> C06b & C09 & C10
    C06b --> C11
    C07 --> C12 & C18a & C30a
    C08 --> C12 & C28
    C09 --> C11
    C10 --> C22
    C11 --> C13 & C23
    C12 --> C13 & C22
    C13 --> C14 & C18a
    C14 --> C15 & C20 & C21 & C22 & C24
    C15 --> C16 & C17 & C34
    C16 --> C36
    C18a --> C18b & C25 & C26 & C30a & C36
    C20 --> C21
    C21 --> C24 & C25 & C30a & FIX1
    FIX1 --> C24
    C22 --> C25 & C26
    C23 --> C30a
    C24 --> C25
    C25 --> C26 & C25bis
    C26 --> C34
    C30a --> C30b & C34
    C30b --> C31
    C31 --> C32a
    C32a --> C32b
    C32b --> C42
    C34 --> C36 & C42
    C36 --> C40 & C42
    C31 --> C40
    C40 --> C42

    C27["C27 · complementarios<br/>CORTADO 12 sep"]
    C38["C38 · evals de generación y agente<br/>RETIRADO 27 sep"]

    classDef hecho fill:#d9ead3,stroke:#38761d,color:#274e13
    classDef ahora fill:#fce5cd,stroke:#b45f06,color:#7f3f00,stroke-width:3px
    classDef corte fill:#f4cccc,stroke:#a61c00,color:#660000,stroke-dasharray:4 3
    class C01,C02,C03,C05,C06a,C06b,C07,C08,C09,C10,C11,C12,C13,C14,C15,C16,C17,C18a,C18b,C20,C21,FIX1,C22,C23,C24,C25,C26,C28,C30a,C30b,C31,C32a,C32b,C34,C36,C40,C42 hecho
    class C27,C38 corte
```

🟩 archivado · 🟧 **siguiente a abrir** · 🟥 **cortado** *(C27 el 2026-09-12, **C38 el 2026-09-27** — §0)* · sin color: pendiente

> **Puesto al día el 2026-09-27, y el grafo se queda sin nodo naranja.** Se archiva **C42**, que pasa
> a verde, y **se retira C38**, con lo que desaparecen sus cinco aristas entrantes —`C24 → C38`,
> `C30b → C38`, `C32b → C38`, `C34 → C38` y `C42 → C38`— y el nodo pasa a rojo punteado junto a C27.
> **No hay naranja porque C39a y C39b están fuera del dibujo a propósito** (véase más abajo: dependen de todos
> los vivos, así que su arista no informa). El grafo queda **enteramente consumido**: lo único
> pendiente del Proyecto Final es **`C39a → C39b`**, y esa arista sí es real —C39b documenta el
> entorno que C39a despliega—, pero vive fuera del dibujo como el resto de la entrega.

> **La arista que justifica el corte de C30** *(13 sep)*: `C30a → C34` existe y `C30b → C34` **no**.
> C34 y C36 necesitan la forma de la respuesta, no la prosa, así que la mitad estructurada
> desbloquea la cadena entera mientras el argumentario se escribe después. `C30b` sólo cuelga de
> C31 y C38, que son los dos que sí necesitan una salida generada. **C30a pasa a 🟧** y **C26 a 🟩**.
>
> `C25bis` se queda **sin color a propósito**: está implementado pero **no archivado**, y el verde significa archivado.

> **Puesto al día el 2026-09-24, al explorar C40.** El verde recoge ahora **todo lo archivado contra
> `openspec/changes/archive/`** —se habían quedado sin color C28, C30a, C30b, C31, C32a, C32b, C34 y
> C36—, y **🟧 pasa a C40**, que es el único nodo libre que abre una arista: `C40 → C38`. Sus dos
> prerrequisitos nuevos son `C36 → C40` y `C31 → C40`, el segundo porque M1 sólo tiene enrutador desde
> C31 y es el enrutador el que hace que los dos rechazos corteses puedan llegar a una pantalla.

**Fuera del dibujo, a propósito:** **C04** no tiene prerrequisitos ni dependientes *(está archivado)*, y **C39** depende de todos los vivos, así que ninguna de las dos arista añade información.

**Cómo se lee para decidir qué se abre.** No por el color de ruta, sino por cuántas aristas abre cada nodo libre:

| Libre ahora | Desbloquea | |
|---|---|---|
| **C30a** 🟧 | **C30b y C34** → y con C34, C36 y C38 | **es el siguiente a abrir** *(13 sep)*. Con C26 archivado nadie más abre aristas: es el único nodo libre que desbloquea algo, y desbloquea **la cadena entera que queda**. Además **mueve el contrato congelado**, y ése es el argumento de calendario —no de tamaño— para no posponerlo: hoy `/v1/assist/sale` tiene **cero consumidores** y a partir de C34 los tendrá |
| ~~**C20**~~ | ~~**C21** → y con él C24, C25, C30~~ | **archivado el 1 sep: el tapón ha caído** |
| **FIX1** | nada — es una hoja | **por eso va detrás de C21 y no delante**: la regla 2 del §1 da prioridad a lo que abre aristas. Y antes de C21 no habría rama léxica con la que medir su efecto |
| ~~C23~~ | ~~C30~~ → **C30a** | **archivado el 6 sep** |
| C22 | C25, C26 | |
| **C25bis** | nada — es una hoja, como `FIX1` | **por eso cede el turno a C26**: la regla 2 del §1 da prioridad a lo que abre aristas. Y antes de que C25 se archivara no se podía hacer, porque la fila plana seguía siendo la referencia de la tabla y no el andamio |
| **C26** ✅ | **C34** → y con él C36 y C38 | **entregado y archivado el 2026-09-12**. Cerró el **último 501 cerrable** del contrato congelado y los **4 huecos del golden set** que C24 dejó a su nombre, más una quinta consulta sin familia que añadió él. ~~**El turno pasa a C34**~~ → **a C30a** *(corregido el 13 sep: C34 lleva C30 de prerrequisito y no podía ser el siguiente)*. C34 hereda la exclusión por falta de stock **y los dos avisos de stock de C30** —los dos anotados en su ficha— porque la autoridad sobre el stock es de .NET |
| C28 | nada — pero lo pide el checklist §16 del diseño | hoja obligatoria |
| C18b | nada — pero es la única evidencia posible del checklist §16 sobre familias | hoja, ya no gratis de recortar |

**Cadena crítica que queda** *(reescrita el 13 sep al partir C30)*: **`C30a → C34 → C36`**, con `C30a → C30b → C31 → C32a → C32b → C38 → C39` cerrando por el otro lado *(C32 partido el 20 sep)*. `C20`, `C22`, `C23`, `C24`, `C25`, `C25bis` y `C26` ya están dentro. El nodo de arranque es **C30a** y no C34: C34 lleva C30 de prerrequisito, y ésa es exactamente la razón por la que la mitad estructurada se entrega primero.

> **Reescrita el 2026-09-24, al explorar C40.** Con C36 archivado la cadena se ha consumido por
> completo y lo que queda es **`C40 → C38 → C39`**, con **C40 como nodo de arranque**. El orden no es
> arbitrario: C40 sube el prompt a `assist/v5` y mueve la fase de la abstención, así que C38 medido
> antes describiría un prompt sustituido y una fase movida. **Y C40 no estaba en ninguna ola**: nace
> el 24 de septiembre durante la comprobación en demo de C36, al descubrir que el panel de búsqueda
> asistida llevaba todo el proyecto sirviendo por su ruta degradada.
>
> **Y consumida por completo el 2026-09-27.** Archivado C42 y **retirado C38** (§0), la cadena no es
> `C40 → C38 → C39` sino **`C39a → C39b`**. El orden que ataba C38 al `assist/v5` de C40 y al `assist/v6` de
> C42 **queda sin objeto**: no hay cifras de generación que tomar, porque las que hacían falta están
> ya tomadas en los artefactos de C32b y C42 y se leen con `--rescore`.

**Y el hueco que el corte de C27 deja a la vista, que conviene no perder de vista al elegir el siguiente:** `ai-service/src/jbg_ai/assist/` **no existe**. C30a, C30b, C31 y C32 están a cero, y son lo que el rubro del PF nombra por su nombre —*«escala desde un prototipo CAG hasta un sistema RAG **con agentes**»*—. Ésa, y no complementarios, es la deuda grande que queda.

**Un segundo hueco, descubierto el 13 sep al explorar C30 y que tampoco es de C30:** el corpus de conocimiento de C23 —32 documentos, 161 fragmentos, indexado y calibrado desde el 6 de septiembre— **no tiene ninguna ruta hasta la pantalla del joyero**. C34 exponía sólo rutas por pieza y C36 sólo un card. Se cierra con un `question` en C34 —en el cuerpo de un `POST`, no en la URL *(corregido el 21 sep)*— y una caja de pregunta en C36, las dos anotadas en sus fichas. Sin eso, una capacidad que costó una sesión entera sólo se demostraría en el arnés.

---

## 5. Calendario por olas

| Ola | Fechas | Changes | Ruta crítica de la ola |
|---|---|---|---|
| **O0** | 3-5 ago | C01-C04 (4) | C01 → C02 → C03 |
| **O1** | 6-12 ago | C05-C12 (9, tras partir C06) | C06a → C09 → C11 → C12, con **C06b en paralelo** |
| **O2** | 13-19 ago | C13-C19 (7) | C13 → C14 → C15 → C16, C17 |
| **O3** | 20-26 ago | C20-C29 (10) | C21 → C22 → C24 → C25 |
| **O4** | 27-31 ago | C30-C38 (11, tras partir C30 y C32) | C30a → C30b → C31 → C32a → C32b, C30a → C34 → C36, C38 |
| **O5** | 1-3 sep | C39 (1) | C39 |

> **Este calendario es registro, no plan** *(desde el 2026-08-31)*. Con prórroga abierta y un solo desarrollador ya no hay fechas que cumplir ni carga por persona y semana que repartir: las olas describen cómo se ejecutó C01–C18a y en qué orden estaba previsto lo demás. **Lo que decide qué se abre a continuación es el grafo del §4**, no esta tabla. Las olas 3 y 4 tal como están dibujadas ya no existen: la 3 pierde C29 y la 4 pierde C33, C35 y C37. **Y desde el 2026-09-24 la 4 gana uno que no estaba previsto**: **C40**, nacido durante la comprobación en demo de C36 — la prueba más limpia de que esta tabla es registro, porque un change que aparece al verificar otro no cabe en ninguna ola dibujada de antemano.

### Pares que NO deben ejecutarse a la vez

Con un solo desarrollador esto deja de ser coordinación y pasa a ser disciplina de rama: son changes que no se abren simultáneamente aunque los escriba la misma mano.

| Par | Motivo |
|---|---|
| C15 ‖ C34 | ~~Mismo controlador `AiController.cs`~~ → **mismo servicio de búsqueda**. `AiController.cs` no existe: el patrón real es un controlador por capacidad *(corregido el 2026-08-28)* |
| C16 ‖ C36 ‖ **C40** | Misma página y servicio del frontend. **C40 amplía `assisted.tsx`**, que es el fichero de C16, y reutiliza la tabla de copy de avisos de C36 *(añadido el 24 sep)* |
| Cualquier par de 🗄️ (C04, C07, C08, **C18b**, C27) | Dos migraciones EF Core simultáneas colisionan en el orden. **De seis planificadas quedaban cuatro** —C19 y C29 anulados, las tres primeras archivadas— y **C18b abre una quinta el 31 de agosto**: la contención que la impedía desapareció con la rama de C19. **Y acabaron siendo tres**, las tres del mismo change sobre su propia tabla, aplicadas en serie *(ver la nota de cierre de su ficha)*. **Vivas: las de C18b y la de C27**, que además lleva corte pre-autorizado. No se abren a la vez |
| C13 ‖ C11 | C13 depende del cliente de embeddings congelado en C11 |
| C21 ‖ C22 ‖ C25 ‖ **C40** | Los cuatro tocan el pipeline de ranking en `retrieval/`. **C40 mueve la fase de la abstención**, que es spec viva con tres consumidores: el panel, los sustitutos y la tool `buscar_catalogo` del agente *(añadido el 24 sep)* |
| C13 ‖ C23 | Zona `indexing/` compartida: separados por fichero, pero no solapar si hay dudas |
| **C30a ‖ C30b ‖ C31 ‖ C32a ‖ C32b** | *(añadido el 13 sep; ampliado el 20 sep al partir C32)* Los **cinco** son `ai-service/src/jbg_ai/assist/`, y además son **estrictamente secuenciales** por dependencia: `C30a → C30b → C31 → C32a → C32b`. No es sólo disciplina de rama, es el orden obligado |
| ~~**C40 ‖ C38**~~ | *(añadido el 24 sep; **sin objeto desde el 2026-09-27**, al retirarse C38 — §0)* Decía que era orden obligado, y lo era: C40 subió el prompt a `assist/v5` y movió la fase de la abstención, y C42 subió la tarea del agente a `assist/v6`. **El orden se cumplió y ya no hay nada que ordenar**: las cifras que C38 iba a tomar están tomadas en los artefactos de C32b y C42, sobre los prompts vigentes, y se leen sin proveedor con `--rescore` |

---

## 6. Orden de corte, fijado de antemano

**Reescrito el 2026-08-31.** La lista de la v3 tenía ocho posiciones y **cuatro de ellas vivían dentro de la rama de C19** —Rotate y Transfer de C29, vista imprimible de C37, y C35 entero—, que es precisamente lo que delató que la rama sobraba: un plan que se compromete de antemano a destripar una funcionalidad está diciendo que no la necesita. Anulada la rama, quedan cuatro cortes, y el disparador ya no es una fecha sino el juicio de que el núcleo peligra:

1. ~~**C27** complementarios~~ → **DISPARADO el 2026-09-12**, y no por el disparador de esta lista sino por **cinco mediciones** que vaciaron sus dos señales (§0 e [informe](informes/c27-cut-measurements.md)). Pasa a fase posterior con condición de reactivación escrita; los sustitutos (C26) ya cubren el caso de venta. **Ahorra la última migración EF Core viva**, y arrastra la retirada de la tool `buscar_complementarios` de C32 y de la ruta `.../recommendations` de C34
2. **C23** corpus 30-45 → **15 documentos**, manteniendo las citas verificables, que es lo que el PF evalúa
3. ~~**RAGAS dentro de C38**~~ → **DISPARADO el 2026-09-26**, y **rebasado el 2026-09-27**: no se conservó nada, porque C38 se retiró entero al día siguiente (§0). El corte estaba bien ordenado —RAGAS cayó primero, como esta lista decía— pero la exploración de la implementación encontró que las otras tres piezas o estaban ya medidas o eran un espejo de lo que ya corre
4. **Golden set de C24** 70 → 45 consultas
5. **C40 tiene su propia línea de corte de seis tramos** *(añadida el 24 sep)*, ordenada por **cuánto engaña hoy la pantalla** y no por coste — está en el §10.10 de su [informe](informes/c40-exploration-decisions.md) y resumida en su ficha. Los dos cortes que esa lista pre-autoriza: **«todos los puntos de venta»** (tramo 4), que es una frontera de autorización y por eso sale **antes** que el embudo de observabilidad, que no arriesga nada; y, si la latencia no cabe, **no generar argumentario en la ruta `catalog` de M1**, que ahorra cerca del 40 % de sus generaciones. Lo que **no** admite corte en C40 es el tramo 2 entero: sin él entrega un panel asistido **sin prosa**

Los cortes **1 y 2 están confirmados de antemano** y se aplican desde el principio del change, no a mitad: C23 se escribe ya con 15 documentos en lugar de redactar 45 y tirar 30.

**Nunca se recortan:** C01, C02, C03, C05, **C06a**, C07, C09, C11, C12, C13, C14, C15, C16, C17, **C18a**, C20, C21, C22, C24, C28, **C30a**, **C30b**, C31, **C32a**, **C32b**, C34, C36, ~~el validador de C38~~ y C39.

> **Corregido el 2026-09-27, y es la primera vez que esta lista pierde un elemento.** *«El validador
> de C38»* sale al retirarse C38 entero (§0). El motivo no invalida la lista: el validador se protegía
> por ser *«la pieza de evaluación con mejor retorno»*, y la exploración de su implementación midió que
> su mitad .NET es **un espejo** de la regla que la puerta numérica de Python ya aplica al mismo texto,
> con cifra esperada **cero**. Una pieza cuyo retorno medido es cero deja de ser la de mejor retorno.
> **Queda declarada en C39b** como limitación con su vía de cierre, que es lo que el §5 de la
> convocatoria premia en su otro epígrafe. **C39 no se recorta, y al partirse en C39a y C39b el mismo
> día, ninguna de las dos mitades se recorta: las dos siguen en la lista.**

> **Las dos mitades de C30 entran las dos, y por motivos distintos** *(13 sep)*. **C30a** porque es
> ahora el nodo de arranque de la cadena crítica y porque mueve el contrato congelado, que sólo se
> abarata hacia atrás. **C30b** porque sin argumentario el PF no tiene capa de generación, que es
> literalmente lo que el rubro nombra. **Y el corte no es una forma encubierta de recortar C30b:**
> si C30b se cayera, C30a seguiría entregando recuperación, citas resolubles con su `claim_scope` y
> abstención —todo medible y sin una llamada a un proveedor—, lo que convierte una pérdida total en
> una pérdida parcial y declarable. Eso es una propiedad del corte, no un permiso para usarlo.

Tres entradas nuevas en esa lista, y conviene el porqué: **C20** porque tapona a C21 y con él al grafo entero; **C31** porque sin guardrails el agente de C32 no es defendible como sistema en producción; y **C28** porque el checklist de entrega del documento hermano pide literalmente *«métricas de revisión humana del enriquecimiento»* y su §11.5 advierte de que esos números *«no existen sin la vía revisada»* — es una casilla marcada o vacía, no un grado.

**C06b sí admite recorte** *(ya archivado, se conserva la nota)*: si no hubiera llegado, el corpus se quedaba en los 436 reales, con las métricas reportadas sobre ellos y el README declarando que no hubo ampliación sintética. **C18b** sigue siendo hoja del grafo —nadie depende de ella— pero **ya no cae sin efectos** *(revisado el 2026-08-31)*: es lo único que puede revisar las 156 familias que hoy nadie ha mirado y lo único que produce la tasa de corrección del agrupador para el §16. Recortarla deja esa casilla del checklist con la mitad de la evidencia, la de C28. Y se lleva por delante la alerta que destapó que el agrupador de C18a se dejó miembros fuera por una laguna del vocabulario.

---

## 7. Riesgos de esta descomposición

| Riesgo | Mitigación |
|---|---|
| ~~Las olas 3 y 4 concentran 19 de los 39 changes~~ | **Sin objeto desde el 31 ago.** No hay olas que equilibrar: quedan 17 changes pendientes y se ordenan por desbloqueo del grafo. La concentración se resolvió anulando cinco de ellos, no repartiéndolos |
| **C20 tapona el grafo entero y está pintado 🟢** | Es lo único que separa a C21 de arrancar, y C21 bloquea a C24 y a C30. Marcado como siguiente a abrir en su ficha y en el §4; el color de ruta ya no decide el orden. **Medido el 1 sep:** sin él la rama léxica de C21 devuelve **cero** documentos a `gargantilla dorada` y a `collares de plata` |
| C02 se queda corto y el contrato cambia, invalidando C03/C15/C16 | `test_openapi_snapshot_is_stable`: cualquier cambio de contrato rompe el build y obliga a decidirlo, en vez de filtrarse |
| C24 (golden set) bloquea C25 y ~~C38~~ | El runner y las configs van por delante; el etiquetado tiene tope de 2 h y recorte definido a 45 consultas. *(C38 retirado el 2026-09-27 — §0. El riesgo se materializó a medias y en otra dirección: el golden set se etiquetó entero, 72 consultas, y lo que no llegó a arbitrar nada fue la ablación del agente, porque el change que la iba a correr no se implementó)* |
| **El golden set lo etiqueta una sola persona** | No se finge la conciliación: *pooling* sobre la unión de configuraciones, relectura diferida de las dudosas, y la ausencia de acuerdo entre anotadores **declarada** en el README como limitación |
| C09, C10 y ~~C38~~ son sesiones largas | Punto de partición predefinido en cada ficha; se entrega primero la mitad que desbloquea. *(La mitigación funcionó tres veces y en C38 funcionó de más: su orden de partición pre-escrito —validador → escenarios → adversarios → RAGAS— se aplicó dos días seguidos y acabó dejando el change vacío. **Un punto de partición honesto puede terminar diciendo que no hay nada que partir**, y eso es un resultado de la mitigación, no un fallo suyo)* |
| ~~C29 necesita saber cuál es el POS origen de suministro~~ | **Sin objeto:** C29 anulada. `IsSupplySource` no llega a existir en SQL, y sigue viviendo solo en el YAML de C10 |
| ~~Seis~~ ~~Cuatro~~ ~~Cinco~~ **Cuatro** migraciones EF Core (C04, C07, C08, **C18b**) | **Sin objeto desde el 2026-09-12.** Las cuatro están archivadas: C18b abrió la suya el 31 de agosto —`FamilyReviewVerdict`, que terminó siendo tres, porque la revisión real obligó a `ReviewSeconds` y a `SubjectWasMember`— y **C27 era la última viva, cortada con medición**. **No queda ninguna migración EF Core pendiente en el plan**, así que la regla de migración única ya no tiene a qué aplicarse |
| Artefactos OpenSpec consumen tiempo de sesión | `design.md` solo cuando hay decisión con alternativas reales (C02, C11, C21, C22, C24, **C32a**, **C32b**, y de hecho también **C17**, **C18a** y **C18b**); en el resto, `proposal` + `tasks` + spec delta |
