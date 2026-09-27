# T-AIENG-043: Redeploy and audit the PF demo environment — bring `demo` up to `ai-eng`, close the five configuration gaps, ship the corpus inside the image, and make verification fail when it should (C39a)

> **Idioma:** título e identificadores en inglés, cuerpo en español — la regla vigente del Proyecto
> Final, igual que `T-AIENG-042`.
>
> **Historia de origen:** [HU-AIENG-043](../../../../Documentos/Historias/AI-Eng/HU-AIENG-043.md)
> **Change:** `openspec/changes/redeploy-and-audit-demo-environment/` (schema `spec-driven`)
> **Rama:** `c39a-redeploy-and-audit-demo-environment`, derivada de `ai-eng`
> **Ficha del plan:** §3 · **C39a**, y §0 · *«C39 se parte en C39a y C39b»* (2026-09-27)

---

## 0 · Qué pide este ticket, en una frase

Que el entorno de demostración vuelva a servir **el sistema que el Proyecto Final ha construido** —no el
de hace cinco semanas—, alcanzable desde internet, con su configuración auditada contra lo que el código
declara, y con una verificación que **falle** en los dos casos en que hoy pasaría en falso.

---

## 0.1 · La restricción que hay que leer antes que nada

**La ruta de producción no se toca en absoluto.** No es una preferencia: es el encuadre del ticket, y la
separación ya es estructural.

| | **Producción — prohibido** | **Demo — el alcance de este ticket** |
|---|---|---|
| Workflow | `deploy-aws-ec2.yml` (`push` a `main`/`master`), `deploy-backend-aws.yml`, `deploy-frontend-aws.yml` | `deploy-demo.yml` (`push` a **`demo`**) |
| Región | `eu-west-3` | **`eu-west-1`** |
| Cuenta | la de la tienda | **cuenta separada** (C17) |
| *Stack* | `terraform/` (14 variables) | `terraform/demo/` (10 variables) |
| Imágenes | `jpv-backend` vía `backend/src/JoiabagurPV.API/Dockerfile.bundled` | `jbg-demo-api` vía `Dockerfile.demo` + `jbg-demo-ai` vía `ai-service/Dockerfile` |
| `VITE_API_BASE_URL` | dominio absoluto, horneado | **relativo `/api`**, horneado |

**Comprobado, y es lo que hace segura la tarea del corpus: producción no construye la imagen de
`jbg-ai`.** `deploy-aws-ec2.yml` construye únicamente `Dockerfile.bundled`. Por tanto
`ai-service/Dockerfile` es **exclusivo de la ruta de demo** y mover su contexto de *build* no puede
alcanzar a la tienda.

Queda **fuera** también el defecto conocido de que producción se redespliega ante cualquier cambio,
incluido uno que sólo toque documentación: está anotado en `openspec/DEFERRED_TASKS.md`, **es de otro
change**, y la spec de C17 tiene un escenario que exige que ese flujo quede inalterado.

---

## 1 · Contexto y problema

### El problema no es que la demo esté mal configurada: es que sirve otro sistema

El despliegue de la demo se dispara por `push` sobre la rama `demo`. Medido el 2026-09-27:

```
origin/demo   d6a740f  «Registra el QA de C34…»       2026-09-22
ai-eng        0d63f1a  merge del PR #45 de C42        2026-09-27

ai-eng \ demo :  84 commits
demo \ ai-eng :   0 commits      ← demo es un ancestro estricto
```

Los changes cuyo código **no** está desplegado:

| Change | Superficie ausente |
|---|---|
| **C36** | ficha de venta en `/sales/new/assist/:productId` — argumentario, variantes con confirmación, sustitutos, caja de pregunta |
| **C40** + **C40_FIX** | panel de consulta libre (M1), *toggle*, dieciséis estados de respuesta, ámbito global |
| **C41** | drenaje de la proyección de disponibilidad al arrancar y cada 600 s |
| **C42** | panel del agente con la traza del bucle |

Cuatro de las cinco superficies más visibles del PF. **El «redespliegue» es, ante todo, un
*fast-forward*.**

### Y un redespliegue limpio dejaría el pilar de agentes apagado

Auditado `compose.demo.yaml` contra los 51 campos de `ai-service/src/jbg_ai/config/settings.py`, las
siete clases de `backend/src/JoiabagurPV.Application/Configuration/` y el entorno de compilación del
frontend. Cinco huecos, todos medidos, ninguno conjeturado.

---

## 2 · Estado actual del código, verificado en el repositorio (2026-09-27)

| Qué | Dónde | Estado |
|---|---|---|
| Interruptores de IA en el compose | `compose.demo.yaml` | `AiSearch__EnabledByDefault`, `AiSalesAssist__EnabledByDefault`, `AiFreeQuerySearch__EnabledByDefault` **presentes**; **`AiAgentAssist__EnabledByDefault` ausente** |
| Valor por defecto del interruptor | `Configuration/AiAgentAssistOptions.cs` | `public bool EnabledByDefault { get; set; }` — **sin inicializador, o sea `false`** |
| Credencial del argumentario | compose + `deploy.sh` + SSM | **presente**, opcional por diseño, interpolada como `${ASSIST_LLM_API_KEY:-}` |
| Credencial del agente | los tres sitios | **ausente en los tres** |
| Credencial del enrutador | los tres sitios | **ausente en los tres**; el log de C34 registró `stage=router_client … credential=assist_fallback` |
| *Timeout* del agente en .NET | `Configuration/AiGatewayOptions.cs` | **ya existe**: `AgentTimeoutMs = 18_000`, con suelo de 15 s validado al arrancar. No es un hueco |
| *Timeout* del agente en Python | `config/settings.py` | `jpv_agent_timeout_seconds = 8.0`, **por vuelta** y no por petición |
| Contexto de *build* de `jbg-ai` | `.github/workflows/deploy-demo.yml` | `docker build -f ai-service/Dockerfile … **ai-service**` — el contexto es el subdirectorio |
| Qué copia la imagen | `ai-service/Dockerfile` | `src`, `migrations`, `prompts`, `alembic.ini`. **Nada de `data/`** |
| Dónde vive el corpus | `ai-service/src/jbg_ai/knowledge/constants.py` | `CORPUS_DIR` = `<raíz>/data/knowledge` — **fuera del contexto de *build*** |
| Volúmenes del servicio de IA | `compose.demo.yaml` | `jbg-demo-ai` **no declara `volumes:`**. El apaño manual de C34 no está codificado |
| Verificación | `deploy/demo/verify.sh` | **cinco** condiciones de fallo; la quinta la añadió C41 (proyección vacía). **Ni corpus ni ruta del agente** |
| Parámetros de SSM | `terraform/demo/ssm.tf` + `deploy/demo/README.md` §3 | **3** no secretos creados por Terraform; **7** secretos creados a mano, uno de ellos opcional |
| Variables de Terraform | `terraform/variables.tf`, `terraform/demo/variables.tf` | 14 y 10, **ninguna de IA**, y es lo correcto |
| Entorno del frontend | `frontend/src`, `deploy-demo.yml` | sólo `VITE_API_BASE_URL`, **horneado en el *build* con valor relativo `/api`**. Sin entorno de ejecución |
| *Runbook* | `deploy/demo/README.md` | nació el 2026-08-30 con C17, 8 commits, **último el 2026-09-26 de C41**. Le falta C42 |
| Contraseña de `admin` | `Infrastructure/Data/DatabaseSeeder.cs` | **ya estable**: constantes `admin` / `Admin123!` |
| Operadores | `ai-service/src/jbg_ai/data/world/constants.py` | `op-ciutadella` → `CIU-CENTRE`, `op-fornells` → `FORNELLS`, `op-aeroport` → `MAO-AIR`, con `Operator123!` (BCrypt coste 12) |
| CI de tests | `.github/workflows/test-backend.yml`, `test-frontend.yml` | disparan sobre `branches: [main, develop]`; **ninguna de las dos ramas existe**. **Nunca se han ejecutado** |

### 2.1 · Y el estado del entorno vivo, medido contra la cuenta el 2026-09-27

**El recorrido es el corto: el entorno está en pie.** Medido con cuatro órdenes de lectura, perfil
`jbg-demo`, región `eu-west-1`:

| Qué | Valor medido |
|---|---|
| Instancia | `i-095f0ba16e2bb8278`, **`running`**, arrancada el **2026-08-30T11:42:22Z** — 28 días en pie |
| Alcanzable desde internet | **`http=200`, `tls=0`** sobre `52-49-209-14.sslip.io` — certificado válido, nombre derivado de la IP (§6 del *runbook*) |
| Parámetros | **11**: cuatro no secretos y **los siete secretos**, incluido el opcional `ASSIST_LLM_API_KEY` → la ficha de venta **genera hoy** |
| **`AGENT_LLM_API_KEY`, `ROUTER_LLM_API_KEY`** | **no existen.** Los huecos 2 y 3 quedan confirmados **contra la cuenta viva**, no sólo contra el repositorio |
| `IMAGE_TAG` | `sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d` → prefijo **`d6a740f`**, que es **exactamente el HEAD de `origin/demo`** |
| Migraciones entre `demo` y `ai-eng` | **ninguna**, ni de EF Core ni de Alembic. 143 ficheros de código, **+21.496 / −247** — casi todo aditivo |

**Lo del `IMAGE_TAG` es una confirmación independiente y conviene decirlo:** que la demo sirve C34 no es
una inferencia a partir de git, es el commit desde el que se construyó la imagen que está corriendo.

**Un hallazgo nuevo, del tipo que esta auditoría existe para pillar.** La cuenta tiene **cuatro**
parámetros no secretos —`DEMO_HOSTNAME`, `ECR_REGISTRY`, `IMAGE_TAG` y **`DEPLOYMENT_BUNDLE_URL`**— y el
§3 del *runbook* dice *«Terraform creates the **three** non-secret parameters»* enumerando sólo los tres
primeros. `ssm.tf` declara los cuatro. Entra en la corrección del §3.

**Y una consecuencia favorable:** la demo lleva cinco semanas **sin el drenaje de C41**, así que su
proyección estará rancia de largo — era la motivación de C41, que midió el entorno a **14,4 veces** el
techo de rancidez. Se cura con el propio *fast-forward*: el drenaje corre al arrancar, y **en su forma
completa cuando no existe *checkpoint***.

### 2.2 · Y lo que el sondeo desde dentro del anfitrión midió, con una refutación

Ejecutado el 2026-09-27 por el servicio de gestión de sistemas, contra el contenedor de IA y su propio
`DATABASE_URL`:

| Tabla / *checkpoint* | Valor |
|---|---|
| `ai.knowledge_chunk` | **161** |
| `ai.knowledge_document` | **32** |
| `ai.product_document` | **1.200** |
| `ai.pos_projection` | **6.720** filas |
| *checkpoint* `pos-availability` | incremental **2026-09-22 18:22:29 UTC** · completo 2026-08-29 |
| *checkpoint* `catalog` | **2026-08-30 12:29:42 UTC**, 1.200 documentos |

**El corpus NO está vacío, y eso refuta un supuesto de este ticket.** 161 fragmentos y 32 documentos son
el corpus de C23 íntegro. El razonamiento que asumía lo contrario era mío y estaba mal: **el corpus se
indexa en la base, y la base vive en el volumen `jbg-demo-pgdata`**, cuya persistencia es un requisito
vivo de esta misma capability. El hueco 4 **no vacía la tabla**: impide **reindexar** y dejaría vacío un
**entorno nuevo**. Se cierra igual por reproducibilidad —el argumento de D5 no cambia— pero su urgencia
pasa de *«M2 y M3 están roscados en la demo»* a *«lo estarían en el próximo entorno limpio»*.

**Y un dato peor de lo esperado: la proyección está a unas 120 veces el techo de rancidez.** Último
drenaje incremental el 22 de septiembre, techo de `jpv_pos_projection_max_age_seconds` en 3.600 s: unos
cinco días contra una hora. Cuando C41 se justificó, midió **14,4 veces**. Y **`verify.sh` no lo habría
pillado**: su quinta condición mira filas ausentes, nunca antigüedad, así que un entorno con 6.720 filas
rancias de cinco días **pasa la verificación**. Queda declarado como hueco de la verificación, con su
cifra, y la decisión de no cerrarlo aquí está en el §11.

**Contexto de los contenedores:** `jbg-demo-api` y `jbg-demo-ai` llevan **4 días** arriba y
`jbg-demo-postgres` **3 semanas**, así que algo reinició los dos primeros sin recrear la base — otra razón
por la que los datos de la base sobrevivieron.

---

## 3 · Lo que se pide

### Tramo 0 · La puerta de entrada — antes de modificar nada

**El recorrido ya está decidido y es el corto** (§2.1): el entorno está en pie, los siete secretos
existen y responde 200 con certificado válido. Así que este tramo **no elige camino**, sólo vuelve a
tomar la foto en el momento de aplicar —porque la del 27 de septiembre es de ese día y no del día del
*apply*— y cierra lo que desde fuera no se ve:

- Repetir las cuatro órdenes de lectura: parámetros **por nombre y nunca por valor**, estado de la
  instancia, *hostname* y `IMAGE_TAG` vigente.
- **Y lo que sólo se ve desde dentro del anfitrión:** `SELECT count(*) FROM ai.knowledge_chunk`, el
  recuento de `ai.pos_projection` y `last_incremental_sync_at` del *checkpoint*. Es la única incógnita
  que queda y es la que decide si el hueco 4 se manifiesta ya en el entorno vivo.

> **El recorrido largo queda descartado, no olvidado.** Si el *apply* encontrara el entorno desmontado,
> entran el §2 y el §5 del *runbook* —`terraform apply`, recrear siete secretos, restaurar los dos
> esquemas, reemplazar el personal y dos sincronizaciones—. Medido el 27 de septiembre, **no es el caso**.
>
> Este tramo existe porque C42 abrió igual —«las tres líneas base»— y descubrió por el camino que las
> tres suites no se pueden medir en paralelo. Aquí la incógnita estaba en la cuenta de AWS; se midió, y
> lo que queda es la mitad que vive dentro del anfitrión.

### Tramo 1 · La auditoría como entregable · `Documentos/Proyecto Final AIEng/informes/`

Tabla de tres columnas —**ajuste declarado · valor en la demo · qué pasa si falta**— sobre los tres
servicios. Incluye la fila del frontend explicando que **no tiene entorno de ejecución** y por qué eso es
deliberado. Es lo que convierte «lo revisé» en algo recomprobable.

### Tramo 2 · Los cinco huecos · `compose.demo.yaml`, `deploy/demo/`, `ai-service/Dockerfile`

1. `AiAgentAssist__EnabledByDefault: "true"` en `jbg-demo-api`, **como literal versionado**.
2. `/jbg-demo/AGENT_LLM_API_KEY` y `/jbg-demo/ROUTER_LLM_API_KEY` creados a mano como `SecureString`;
   leídos en `deploy.sh` **con el patrón opcional** de `ASSIST_LLM_API_KEY` —`|| true`, sin validación de
   no-vacío, y registro de *presente/ausente* sin revelar el valor—; pasados al contenedor con valor por
   defecto vacío para que `docker compose config` resuelva sin el script.
3. El corpus dentro de la imagen, **moviendo el contexto de *build* a la raíz** y copiándolo en el
   `Dockerfile`. Se mide el tamaño del contexto antes y después.
4. `verify.sh` con **dos** condiciones de fallo nuevas: `ai.knowledge_chunk` a cero, y ruta del agente
   sin respuesta.
5. §3 del *runbook* con los dos parámetros nuevos marcados como opcionales.

### Tramo 3 · El despliegue · rama `demo`

`demo` alcanza a `ai-eng` y se empuja. **Comprobar que el workflow se ejecutó**, no sólo que se empujó:
`deploy-demo.yml` lleva `paths-ignore` sobre `openspec/**` y `Documentos/**`.

### Tramo 4 · Verificación · desde dentro y desde fuera

- Desde dentro del anfitrión, por el servicio de gestión de sistemas, con las **siete** condiciones.
- Desde internet: HTTPS válido bajo el *hostname*, y que **sólo** el proxy esté expuesto.
- **Recorrido manual con los cuatro usuarios** sobre las cuatro superficies de IA, con evidencia por
  recorrido.

### Tramo 5 · CI informativa · `.github/workflows/`

`branches: [ai-eng, master]` en los dos workflows de test, conservando el filtro `paths:`. **Informativa,
no puerta.**

### Tramo 6 · Documentación

*Runbook* al día con C42; credenciales del evaluador escritas con lo que cada una enseña; cierre de la
tarea diferida del corpus en `openspec/DEFERRED_TASKS.md`.

---

## 4 · Lo que este ticket declara y no pide

- **README de entrega, vídeo, tag `v1.0-final-[INICIALES]` y evidencias** → **C39b**.
- **Las tres tareas supervivientes de C38** —éxito de tarea del agente, su tabla por `--rescore`, y la
  declaración del validador .NET no implementado— → **C39b**.
- **Variables nuevas de Terraform** → ninguna, y el motivo está en el §7.
- **Poner las suites en verde** → no. Los 53 fallos de backend y los 113 de frontend se declaran.
- **CI como puerta obligatoria** → no, con la trampa nombrada: un workflow omitido por filtro de rutas
  nunca reporta, y una comprobación requerida que no reporta bloquea el PR para siempre.
- **Recalibrar ajustes de comportamiento** → no. Umbrales, pesos de fusión, banda de abstención y
  presupuestos del bucle se quedan: son literales versionados y moverlos invalidaría cifras publicadas.
- **Dominio comprado** → no. El §6 del *runbook* lo cubre y la imagen es agnóstica del nombre.
- **Workflow de `pytest` para `ai-service`** → no existe; se declara como hueco.

---

## 5 · Componentes Afectados

| Componente | Qué se toca |
|---|---|
| **`compose.demo.yaml`** | tres claves de entorno nuevas (una de .NET, dos de `jbg-ai`) |
| **`deploy/demo/deploy.sh`** | lectura opcional de dos parámetros y su registro sin valor |
| **`deploy/demo/verify.sh`** | dos condiciones de fallo nuevas |
| **`deploy/demo/README.md`** | §3 parámetros, §5.6 comprobación, credenciales del evaluador, C42 |
| **`ai-service/Dockerfile`** | copia del corpus |
| **`.github/workflows/deploy-demo.yml`** | contexto de *build* de la imagen de IA |
| **`.github/workflows/test-backend.yml`**, **`test-frontend.yml`** | ramas del disparador |
| **`openspec/`** | delta sobre `demo-deployment`; cierre de la tarea diferida del corpus |
| **`Documentos/`** | informe de auditoría y de implementación; plan de changes |
| **SSM** *(fuera del repositorio)* | dos parámetros `SecureString` creados a mano |
| **`backend/`**, **`frontend/`**, **`ai-service/src/`** | **no se tocan** — ninguna línea de lógica |
| **`terraform/`**, **`terraform/demo/`** | **no se tocan** |

---

## 6 · Especificaciones Técnicas

### 6.1 · El interruptor del agente

`AiAgentAssistOptions.EnabledByDefault` es `bool` sin inicializador. El compose declara los otros tres
interruptores del mismo patrón y omite éste, así que la ruta del agente queda apagada para todo punto de
venta que no esté en `EnabledPointOfSaleIds`, que está vacío. Se declara **literal `"true"`** en el
servicio `jbg-demo-api`, no en SSM: la spec viva exige que los ajustes que cambian *lo que el sistema
computa* vivan bajo control de versiones.

### 6.2 · Las dos credenciales

Cada etapa tiene su propia clave y su propio modelo, a propósito: `jpv_agent_llm_model` por defecto
`openai/gpt-4o`, `jpv_router_llm_model` por defecto `openai/gpt-4o`, `jpv_assist_llm_model` por defecto
`openai/gpt-4o-mini`. Los repliegues implementados son `agent → assist → rag` y `router → assist → rag`,
y cada proceso registra una vez cuál ganó. **El repliegue es red, no configuración**: con él activo los
costes de las tres etapas son inseparables, y ése es el motivo del hueco 3 y no un detalle de estilo.

Patrón de lectura, copiado literalmente del de `ASSIST_LLM_API_KEY`:

```sh
export AGENT_LLM_API_KEY="$(read_parameter AGENT_LLM_API_KEY || true)"
export ROUTER_LLM_API_KEY="$(read_parameter ROUTER_LLM_API_KEY || true)"
# Sin `: "${…:?}"`. Su ausencia es un estado válido, declarado y con test.
```

En el compose se interpolan con valor por defecto vacío —`${AGENT_LLM_API_KEY:-}`— para que
`docker compose config` resuelva también sin el script, y porque **vacío equivale a no configurada**.

### 6.3 · El corpus dentro de la imagen

Hoy: contexto `ai-service`, y `CORPUS_DIR` = `<raíz>/data/knowledge`. El corpus está **fuera del
contexto**, así que ninguna línea `COPY` puede alcanzarlo. Dos caminos, y sólo uno cumple la spec:

| Camino | Veredicto |
|---|---|
| **Contexto de *build* a la raíz** + `COPY data/knowledge ./data/knowledge` | **El elegido.** La imagen queda reproducible por sí sola, que es requisito vivo. El *build* de la API ya usa contexto de raíz y su comentario documenta que el `.dockerignore` lo mantiene en decenas de megas |
| Volumen desde el paquete de despliegue | **Rechazado.** Deja el contenido fuera de la imagen y reintroduce el apaño de C34: la imagen dejaría de ser autosuficiente |

Consecuencia observable de cerrarlo: `ai.knowledge_chunk` deja de estar a cero, con lo que **M2 deja de
retirar el argumentario por falta de material al que anclarse** y **M3 deja de responder
`knowledge_not_covered` sin citas**.

### 6.4 · Las dos condiciones de verificación nuevas

`verify.sh` tiene cinco. Se añaden la sexta y la séptima:

- **Corpus vacío.** Misma forma que el índice vacío, dos tablas más allá. Un entorno con índice lleno y
  corpus vacío **pasa hoy** la verificación.
- **Ruta del agente sin respuesta.** Con un matiz que hay que respetar: una **degradación en banda** —200
  con motivo de parada por fallo de proveedor o por falta de cliente— **no** es un fallo. El cortacircuitos
  de .NET tampoco la cuenta, deliberadamente, porque Polly ve el transporte y no el cuerpo.

### 6.5 · Specs de OpenSpec

Delta sobre **`demo-deployment`** (13 requisitos), tocando al menos cuatro:

| Requisito | Qué le cambia |
|---|---|
| *Secrets reach containers through the process environment only* | el conjunto de secretos crece en dos, los dos **opcionales**: su ausencia no puede hacer fallar el despliegue, a diferencia de los obligatorios que sí tienen su escenario de fallo ruidoso |
| *Behaviour-affecting settings are version controlled, not stored as parameters* | entra el interruptor del agente como literal versionado |
| *Deployment is verified from inside the host* | de cinco condiciones de fallo a **siete** |
| *Images and provisioning are reproducible* | la imagen de IA pasa a contener el corpus; cambia su contexto de *build* |

---

## 7 · Arquitectura

- **La frontera .NET / Python no se mueve.** Ninguna línea de lógica cambia: esto es empaquetado y
  configuración.
- **Los secretos siguen fuera del estado de Terraform.** `terraform/demo/ssm.tf` declara sólo los tres no
  secretos y su cabecera explica por qué: *«un valor pasado a Terraform se escribe en el estado en
  claro»*. Los dos parámetros nuevos se crean a mano, como los otros siete.
- **Dos credenciales compartidas siguen derivando de un parámetro único** —`AI_SERVICE_SHARED_SECRET` y
  `INDEX_FEED_SHARED_KEY`, cada uno leído dos veces—, y eso no se toca: dos parámetros podrían derivar, y
  un par derivado produce un 401 cuya causa el servicio está especificado para no revelar.
- **Sin migración de EF Core.** El modelo de datos no se toca.
- **Sin movimiento del contrato congelado.** `ai-service/openapi.json` queda intacto.
- **Compatibilidad hacia atrás:** ninguna ruta REST cambia de forma.

---

## 8 · Criterios de Aceptación

Los catorce escenarios de [HU-AIENG-043](../../../../Documentos/Historias/AI-Eng/HU-AIENG-043.md), y en
particular estos cuatro, que son los que pueden pasar en falso:

1. **El panel del agente aparece** en el *hub* sobre el entorno desplegado, no en local.
2. **`ai.knowledge_chunk` > 0** y una pregunta sobre una pieza devuelve **citas desplegables**.
3. **`verify.sh` falla** cuando el corpus está vacío y cuando la ruta del agente no responde — probado
   provocándolo, no razonándolo.
4. **Ningún fichero de producción modificado**, comprobado sobre el diff.

---

## 9 · Definición de Hecho (DoD)

- [ ] Tramo 0 cerrado con evidencia y el recorrido declarado **antes** de la primera modificación
- [ ] La tabla de auditoría publicada, con los tres servicios y la fila del frontend explicada
- [ ] Los cinco huecos cerrados, cada uno en **todas** sus capas (SSM · `deploy.sh` · compose · imagen)
- [ ] `demo` alcanzado a `ai-eng` y **el workflow ejecutado**, no sólo empujado
- [ ] Verificación desde dentro del anfitrión en verde con las **siete** condiciones
- [ ] HTTPS válido bajo el *hostname*, y sólo el proxy expuesto
- [ ] Recorrido manual con `admin`, `op-ciutadella`, `op-fornells` y `op-aeroport` sobre las cuatro
      superficies de IA, con evidencia por recorrido
- [ ] Las dos condiciones nuevas de `verify.sh` probadas **provocando el fallo**
- [ ] `test-backend.yml` y `test-frontend.yml` ejecutados por primera vez, informativos
- [ ] Delta de `demo-deployment` escrita, y `openspec validate --all --strict` a **0 failed** — la forma `--all --strict`, que es la única que es puerta del proyecto
- [ ] *Runbook* al día con C42 y credenciales del evaluador escritas
- [ ] Tarea diferida del corpus cerrada en `openspec/DEFERRED_TASKS.md`
- [ ] **Cero ficheros de la ruta de producción modificados**
- [ ] Ningún secreto en el repositorio, en ningún fichero del anfitrión, ni en la salida de ningún comando
- [ ] Informe de implementación en `Documentos/Proyecto Final AIEng/informes/c39a-implementation-measurements.md`
- [ ] UI en es-ES y moneda EUR — sin cambios de UI en este ticket, se comprueba que sigue así

> **Nota sobre las suites:** no se exige verde. Se exige **comparar nombres de test contra la línea base**
> según `CLAUDE.md`, y **medir en serie**: las tres a la vez dan 490 rojos de 1.347 en backend donde en
> serie dan 53, porque `vitest` satura la máquina y *testcontainers* pierde el demonio de Docker.

---

## 10 · Requisitos No Funcionales

- **Seguridad.** Secretos sólo por el entorno del proceso que despliega; nunca en fichero del anfitrión,
  nunca en imagen, nunca en la salida del comando. Sin `set -x` cerca de la sección que los lee. Los dos
  parámetros nuevos como `SecureString`. JWT interno HS256 entre .NET y `jbg-ai`; el navegador no alcanza
  Python.
- **Exposición.** Sólo el proxy inverso publica puertos. `jbg-demo-ai` **no** declara `ports:` y no debe
  empezar a hacerlo: es el contenedor que tiene la credencial del proveedor.
- **Free-tier.** `mem_limit: 512m` en el servicio de IA se mantiene —con `mem_limit` y **no**
  `deploy.resources.limits`, que fuera de *swarm* se ignora en silencio—. La imagen crece al incorporar el
  corpus: se mide y se declara.
- **Observabilidad.** `/health` con su sección de proyección; `GET /api/ai/health` para la tarjeta de
  administración; `trace_id` propagado.
- **Cuota.** Del orden de **una petición por minuto** con ~13.000 tokens contra 25.000 TPM. Suficiente
  para un mostrador y un evaluador; **no** para dos mostradores simultáneos. Se declara.
- **Integridad.** Ningún cambio de datos. Si el recorrido es el largo, el §5.3 del *runbook* reemplaza el
  personal real de forma obligatoria, y hay que comprobar que `admin` sobrevive a ese reemplazo.

---

## 11 · Preguntas Abiertas → decisión por defecto

| # | Pregunta | Por defecto |
|---|---|---|
| ~~**P1**~~ | ~~¿El entorno sigue en pie?~~ | **CERRADA el 2026-09-27 con medición** (§2.1): **sí**. Instancia en pie desde el 30 de agosto, siete secretos, HTTPS válido, `IMAGE_TAG` = HEAD de `demo`, cero migraciones pendientes. **Recorrido corto** |
| ~~**P7**~~ | ~~¿`ai.knowledge_chunk` está a cero en el entorno vivo?~~ | **CERRADA Y REFUTADA el 2026-09-27: no lo está.** **161 fragmentos y 32 documentos** — el corpus de C23 completo. El supuesto era mío y estaba mal razonado: el corpus se indexa **en la base**, y la base vive en el volumen `jbg-demo-pgdata`, cuya persistencia es requisito vivo de esta capability. El hueco 4 **no vacía la tabla**: impide reindexar y deja vacío un **entorno nuevo**. Se cierra igual, por reproducibilidad, con **urgencia menor** de la que este ticket le atribuía |
| **P8** | La proyección está a **~120 veces** el techo de rancidez —último incremental el 2026-09-22, techo 3.600 s— y `verify.sh` **no** la habría pillado, porque su quinta condición mira filas ausentes y no antigüedad. ¿Se añade la rancidez como octava condición? | **No en este ticket.** El *fast-forward* trae el drenaje de C41, que corre al arrancar, así que la rancidez se cura sola y medirla antes y después es la tarea 5.3. Añadir una condición por antigüedad **sobre un entorno que acaba de arrancar** mediría el reloj del despliegue y no la salud del sistema. Queda **declarado como hueco de la verificación**, con su cifra |
| **P2** | ¿Las dos claves nuevas apuntan al mismo valor que la del argumentario? | **Parámetros distintos con el mismo valor**, que es lo que el *runbook* ya admite para la de *embeddings*: separa los costes sin multiplicar cuentas |
| **P3** | ¿Corpus por contexto de *build* o por volumen? | **Contexto de *build***, §6.3 |
| **P4** | ¿Dominio comprado? | **No**; el §6 del *runbook* lo cubre y no exige reconstruir |
| **P5** | ¿CI para `ai-service`? | **No** en este ticket; se declara como hueco |
| **P6** | ¿`jpv_agent_timeout_seconds` (8 s por vuelta) y `AgentTimeoutMs` (18 s) conviven bien tras el proxy? | Se **mide** en el tramo 4 y se declara; no se recalibra aquí |

---

## 12 · Prioridad / Estimación / Tags

| | |
|---|---|
| Prioridad | **Máxima** — sin esto el §5 de la convocatoria no se cumple, y **C39b depende de él** |
| Estimación | _Pendiente_ — depende del recorrido que decida el tramo 0 |
| Tags | `deployment` · `demo-environment` · `configuration-audit` · `ci` · `pf-delivery` · `no-production` |

---

## 13 · Enlaces o Referencias

- Historia: [HU-AIENG-043](../../../../Documentos/Historias/AI-Eng/HU-AIENG-043.md)
- Spec viva: [`openspec/specs/demo-deployment/spec.md`](../../../specs/demo-deployment/spec.md)
- *Runbook*: [`deploy/demo/README.md`](../../../../deploy/demo/README.md)
- Tareas diferidas: [`openspec/DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md) — *«Este repositorio no tiene CI»*, *«C34 · el corpus de conocimiento no viaja en la imagen de `jbg-ai`»*
- Plan: [§0 y ficha de C39a](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- Precedente de formato: [`T-AIENG-042`](../../archive/2026-09-27-add-frontend-agent-panel/ticket.md)
- Procedimientos: [`Procedimiento-TicketsTrabajo.md`](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [`Procedimiento-UserStories.md`](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)

---

## 14 · Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-27 | Creado a partir de la sesión de exploración que retiró C38 y partió C39. Incorpora la auditoría completa de `compose.demo.yaml` contra los tres servicios, el hallazgo de que `origin/demo` está 84 commits por detrás, y la restricción dura de no tocar producción |
