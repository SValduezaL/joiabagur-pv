# HU-AIENG-043: El entorno de demostración vuelve a enseñar el sistema entero — la rama `demo` alcanza a `ai-eng`, los cuatro ajustes que faltan, el corpus dentro de la imagen y una verificación que no pasa en falso

## Formato estándar

**Como** desarrollador del proyecto,
**quiero** que el entorno de demostración del Proyecto Final vuelva a estar desplegado en AWS, accesible desde internet y verificado recorrido a recorrido, con su configuración auditada contra lo que el código realmente declara,
**para que** el evaluador pueda probar el sistema completo entrando con unas credenciales, sin instalar nada en local.

> **El §5 de la convocatoria es tajante:** *«si el evaluador no puede acceder al sistema funcionando, el
> proyecto no puede evaluarse correctamente»*. Esta historia existe para que esa frase no aplique.

---

## Descripción

El Proyecto Final tiene un entorno de demostración desplegado desde el 30 de agosto (C17), en una cuenta
de AWS separada de la de producción, con su propio *stack* de Terraform, sus propias imágenes y su propio
*runbook*. **Lo que esta historia descubre es que ese entorno lleva cinco semanas sirviendo una versión
vieja del sistema**, y que la configuración con la que arrancaría un redespliegue deja invisible
precisamente el pilar que no se puede enseñar de otra forma.

### El hallazgo que gobierna el alcance: la rama `demo` está en C34

El despliegue de la demo se dispara por `push` sobre la rama **`demo`** (`.github/workflows/deploy-demo.yml`).
Medido el 2026-09-27:

```
origin/demo   ->  d6a740f  «Registra el QA de C34…»   (2026-09-22)
ai-eng        ->  0d63f1a  merge del PR #45 de C42     (2026-09-27)

commits que ai-eng tiene y demo no:  84
commits que demo tiene y ai-eng no:   0
```

`demo` es un ancestro estricto. Lo que hay desplegado **no contiene**:

| Change | Lo que el evaluador no vería hoy |
|---|---|
| **C36** | la **ficha de venta** en `/sales/new/assist/:productId` — argumentario, variantes de la familia con confirmación, sustitutos y caja de pregunta |
| **C40** + **C40_FIX** | el **panel de consulta libre** (modo M1), el *toggle*, los dieciséis estados de respuesta y el ámbito «todas las tiendas» |
| **C41** | el **drenaje de la proyección de disponibilidad**, sin el cual la recuperación con ámbito degrada a la ruta léxica |
| **C42** | el **panel del agente** con la traza del bucle — la única prueba en pantalla de que hay un agente y no un prompt |

Son **cuatro de las cinco piezas más visibles del Proyecto Final**. La demo enseña hoy la búsqueda
asistida de C16 y las rutas .NET de C34, y nada de lo que vino después.

> **Medido contra la cuenta el 2026-09-27, y confirma lo anterior por una vía independiente.** La
> instancia `i-095f0ba16e2bb8278` está **en pie desde el 30 de agosto**, responde **`http=200`** con
> certificado válido sobre `52-49-209-14.sslip.io`, y su **`IMAGE_TAG` es `sha-d6a740fa5e0b…`** — cuyo
> prefijo `d6a740f` es **exactamente el HEAD de `origin/demo`**. Que la demo sirva C34 no es una
> inferencia a partir de git: es el commit desde el que se construyó la imagen que está corriendo. Y
> entre `demo` y `ai-eng` **no hay ninguna migración**, ni de EF Core ni de Alembic: 143 ficheros de
> código, +21.496 / −247, casi todo aditivo.

### Y la configuración con la que arrancaría tampoco está completa

Auditado `compose.demo.yaml` contra los ajustes que declaran los tres servicios —51 campos de
`ai-service/src/jbg_ai/config/settings.py`, las siete clases de opciones de
`backend/src/JoiabagurPV.Application/Configuration/` y el entorno de compilación del frontend—, el
resultado es que **un redespliegue limpio dejaría el pilar de agentes apagado**:

| Nº | Hueco | Consecuencia |
|---|---|---|
| **1** | **`AiAgentAssist__EnabledByDefault` ausente** del compose | Es `public bool` **sin inicializador**, o sea `false`. Los otros tres interruptores del mismo patrón —`AiSearch`, `AiSalesAssist`, `AiFreeQuerySearch`— **sí** están puestos; éste no. **El panel del agente de C42 no se sirve**: la cuarta tarjeta del *hub* no aparece |
| **2** | **`JPV_AGENT_LLM_API_KEY` ausente** en SSM, en `deploy.sh` y en el compose | El bucle no se construye y la ruta degrada por falta de credencial. Es uno de los **dos estados de pantalla que C42 declara nunca observados en producción**: se construyó contra escenarios |
| **3** | **`JPV_ROUTER_LLM_API_KEY` ausente** en los tres sitios | El enrutador de C31 repliega a la clave del argumentario — `stage=router_client … credential=assist_fallback`, **ya observado en el log del despliegue de C34**—. Funciona, y **no es lo declarado**: los dos modelos son distintos a propósito y compartir clave hace imposible separar sus costes |
| **4** | **El corpus de conocimiento no viaja en la imagen de `jbg-ai`** | Y **no es una línea `COPY` que falte**: el *build* usa contexto `ai-service` y el corpus vive en `data/knowledge`, en la raíz del repositorio, **fuera del contexto**. Además `jbg-demo-ai` **no declara `volumes:`**, así que el apaño manual con el que C34 lo sorteó no está codificado y no sobrevive a un despliegue limpio. Con `ai.knowledge_chunk` a cero, **M2 retira el argumentario y M3 responde `knowledge_not_covered`** — y parece un fallo de la ficha de venta |
| **5** | **`deploy/demo/verify.sh` no cubre** la ruta del agente ni el recuento de fragmentos | Son las dos cosas cuyo fallo es **silencioso**: la pantalla renderiza, el certificado es válido y el despliegue parece un éxito |

El hueco 5 es de la misma familia que el que C41 ya cerró. La spec viva lo dice con estas palabras
sobre la proyección vacía: *«el despliegue parece un éxito y no encuentra nada que el surtido debería
haber acotado. Es exactamente la forma del índice vacío, una tabla más allá, y ya ha llegado una vez a
un entorno desplegado»*. **El corpus vacío es la tercera tabla de esa misma serie.**

### Lo que la auditoría también establece, y evita trabajo

**No se añade ninguna variable de Terraform.** Los dos *stacks* —14 variables en `terraform/`, 10 en
`terraform/demo/`— **no tienen una sola variable de IA, y es correcto**: la configuración de IA vive en
`compose.demo.yaml` como literal versionado y en SSM bajo `/jbg-demo/` como secreto creado a mano,
deliberadamente fuera del fichero de estado. La spec viva lo exige en dos requisitos distintos, y el
`ssm.tf` de la demo lo explica en su cabecera: *«un valor pasado a Terraform se escribe en el estado en
claro»*.

**El frontend no tiene hueco, y conviene decir por qué.** No hay servicio de frontend en el compose y
no hay variable de entorno en ejecución: la SPA se sirve desde el `wwwroot` de la propia API y
`VITE_API_BASE_URL` se hornea en el *build* con valor **relativo `/api`**. Eso es lo que hace la imagen
agnóstica del *hostname* y permite pasar de un nombre derivado de la IP a un dominio comprado **sin
reconstruir**.

**El *runbook* no es pre-PF, y está un solo change por detrás.** Nació el 2026-08-30 con C17, tiene ocho
commits y el último es del 2026-09-26, de C41. Le falta C42 y nada más.

**La contraseña de `admin` ya es estable.** `DatabaseSeeder` la declara como constante — `admin` /
`Admin123!` — con el comentario *«debería cambiarse tras el primer acceso»*. Lo que falta no es fijarla:
es **escribirla en la entrega** y comprobar que el §5.3 del *runbook*, que reemplaza el personal real de
la tienda de forma obligatoria, no la elimina.

### Las dos rutas de despliegue están separadas, y producción no se toca

Es una **restricción dura** de esta historia, y la separación ya es estructural:

| | **Producción — no se toca en absoluto** | **Demo — es la de esta historia** |
|---|---|---|
| Disparador | `deploy-aws-ec2.yml`, `push` a `main`/`master` | `deploy-demo.yml`, `push` a **`demo`** |
| Región | `eu-west-3` | **`eu-west-1`** |
| Cuenta AWS | la de la tienda | **cuenta separada** (C17) |
| *Stack* | `terraform/` | `terraform/demo/` |
| Imágenes | `jpv-backend` (`Dockerfile.bundled`) | `jbg-demo-api` (`Dockerfile.demo`) + `jbg-demo-ai` |
| `VITE_API_BASE_URL` | dominio absoluto | **relativo `/api`** |

Y la comprobación que hace segura la tarea del corpus: **producción no construye la imagen de
`jbg-ai`**. `deploy-aws-ec2.yml` sólo construye `Dockerfile.bundled`, así que `ai-service/Dockerfile` es
**exclusivo de la ruta de demo** y mover su contexto de *build* no puede afectar a la tienda.

### La CI no se ha ejecutado nunca, ni una vez

`test-backend.yml` y `test-frontend.yml` disparan sobre `branches: [main, develop]`, y **ninguna de esas
dos ramas existe**: las del repositorio son `master`, `ai-eng` y `demo`. Los workflows están bien
escritos, sus filtros de ruta son razonables, y son **inertes**. Está documentado en
`openspec/DEFERRED_TASKS.md` desde el 2026-08-30, con la consecuencia dicha sin rodeos: *«ningún cambio
de este proyecto ha pasado por una comprobación automática antes de integrarse»*.

El arreglo es de una línea. Lo que **no** se puede hacer, y la misma tarea diferida lo argumenta, es
convertirla en puerta: con **53 fallos preexistentes en backend y 113 en frontend**, *«una puerta sobre
una suite roja no es una puerta; es un bloqueo permanente que alguien terminará saltándose»*. Entra como
**informativa**.

---

### Alcance de esta historia (sí)

1. **Puerta de entrada — establecer el estado real del entorno antes de tocar nada.** Si la instancia y
   los siete secretos de `/jbg-demo/` existen, esto es «dos parámetros, tres ficheros y un
   redespliegue»; si se aplicó el §7 del *runbook* y se desmontó, entra además `terraform apply`,
   recrear secretos, restaurar datos, reemplazar personal y correr las sincronizaciones. **Son dos
   caminos distintos y el primer grupo de tareas decide cuál se recorre**, con su evidencia escrita.
2. **La rama `demo` alcanza a `ai-eng`** y el despliegue se dispara solo. Con un aviso de mecánica: el
   workflow lleva `paths-ignore` sobre `openspec/**` y `Documentos/**`, así que un *push* que sólo
   tocara documentación **no despliega** — hay que comprobar que el disparo ocurre de verdad.
3. **Los cinco huecos de la auditoría**, cerrados: el interruptor del agente, las dos credenciales en
   sus tres capas (parámetro en SSM, lectura en `deploy.sh` con el patrón opcional de
   `ASSIST_LLM_API_KEY`, y paso en el compose), el corpus dentro de la imagen, y `verify.sh` ampliado.
4. **La auditoría publicada como entregable**, en tabla de tres columnas —ajuste declarado · valor en la
   demo · qué pasa si falta—, cubriendo los tres servicios. Es lo que convierte «lo revisé» en algo que
   otro puede volver a comprobar.
5. **El recorrido del evaluador, comprobado a mano sobre el entorno desplegado** y no en local, con los
   cuatro usuarios y las cuatro superficies de IA: búsqueda asistida, ficha de venta, panel de consulta
   libre y panel del agente.
6. **Accesibilidad desde internet verificada**: HTTPS bajo el *hostname* parametrizado, y sólo el proxy
   expuesto — los dos son requisitos vivos de `demo-deployment` y aquí se comprueban, no se reescriben.
7. **La CI se enciende como informativa**, corrigiendo las ramas a `[ai-eng, master]` y conservando el
   filtro `paths:` de los tests.
8. **El *runbook* al día con C42**, y las credenciales del evaluador escritas con lo que cada una enseña.

### Fuera de alcance (no)

- **El README de entrega, el vídeo, el tag `v1.0-final-[INICIALES]` y las evidencias**: son de **C39b**.
  Esta historia existe para que C39b pueda documentar un recorrido ya recorrido.
- **Cualquier cosa de la ruta de producción**: `deploy-aws-ec2.yml`, `deploy-backend-aws.yml`,
  `deploy-frontend-aws.yml`, el *stack* `terraform/`, `eu-west-3` y `Dockerfile.bundled`. Incluido el
  defecto conocido de que producción se redespliega ante cualquier cambio, **que es de otro change** y
  cuya inalterabilidad C17 verifica con un escenario propio.
- **Variables nuevas de Terraform**, por la razón de arriba.
- **Poner las suites en verde.** La CI entra informativa; los 53 y los 113 fallos preexistentes se
  declaran y no se arreglan aquí.
- **Convertir la CI en puerta obligatoria**, con la trampa que la tarea diferida ya nombra: un workflow
  omitido por filtro de rutas nunca reporta, y una comprobación requerida que no reporta bloquea el PR
  para siempre.
- **Recalibrar ningún ajuste de comportamiento.** Umbrales, pesos de fusión, banda de abstención y
  presupuestos del bucle se quedan como están: son literales versionados y moverlos aquí invalidaría las
  cifras publicadas.
- **Las tres tareas supervivientes de C38** —definición de éxito de tarea del agente, su tabla por
  `--rescore`, y la declaración del validador .NET no implementado—, que son de **C39b**.

### Decisiones de diseño ya acordadas

| # | Decisión | Motivo |
|---|---|---|
| **D1** | El redespliegue se hace **llevando `demo` a `ai-eng`**, no cortando una rama nueva | `deploy-demo.yml` dispara por `push` sobre `demo`; cualquier otro camino sería un despliegue a mano fuera del mecanismo que la spec verifica |
| **D2** | Las dos credenciales nuevas son **opcionales al arrancar**, con el patrón exacto de `ASSIST_LLM_API_KEY`: `read_parameter … \|\| true` y sin validación de no-vacío | Su ausencia es un estado válido y declarado —fail-open, ablación y *rollback* a la vez—. Validarlas como obligatorias convertiría una degradación diseñada en un fallo de despliegue |
| **D3** | **No se reutiliza una sola clave para las tres etapas.** Cada una tiene su parámetro | El repliegue existe como red, no como configuración: `agent → assist → rag` y `router → assist → rag` ya están implementados y se registra cuál ganó. Compartir clave a propósito haría imposible separar los costes de tres modelos distintos |
| **D4** | `AiAgentAssist__EnabledByDefault` se pone a `"true"` **en el compose**, no en SSM | Es un ajuste de comportamiento, y la spec viva exige que ésos sean literales bajo control de versiones para que cambiarlos pase por revisión |
| **D5** | El corpus entra en la imagen **moviendo el contexto de *build* a la raíz**, como ya hace el *build* de la API, y no montándolo por volumen | Un volumen deja el contenido fuera de la imagen y reintroduce el apaño: la imagen dejaría de ser reproducible por sí sola, que es un requisito vivo. El contexto de la API ya demuestra que el `.dockerignore` de raíz lo mantiene en decenas de megas |
| **D6** | `verify.sh` gana **dos condiciones de fallo**, no una: corpus vacío y ruta del agente que no responde | Son fallos silenciosos, y la spec ya fija el patrón con las cinco que tiene |
| **D7** | La CI entra **informativa y con filtro de rutas**, sobre `[ai-eng, master]` | La tarea diferida lo argumenta entero: los despliegues fallan hacia el lado de sobrar, los tests hacia el de faltar, a propósito |
| **D8** | La contraseña de `admin` **no se cambia**: se documenta | Ya es una constante estable en `DatabaseSeeder`. Cambiarla movería una entidad sembrada por una razón cosmética |
| **D9** | Se verifican con los **tres** operadores, no dos | Existen y no cuestan nada, y cada uno enseña algo distinto que el evaluador no encontraría solo |

### Referencias

- Plan de changes: [§0 · *C39 se parte en C39a y C39b*](../../Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) y la ficha de **C39a**
- Diseño: [§12 *Despliegue*](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) y [§16 *Checklist de entrega*](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- Spec viva: [`openspec/specs/demo-deployment/spec.md`](../../../openspec/specs/demo-deployment/spec.md) — 13 requisitos
- *Runbook*: [`deploy/demo/README.md`](../../../deploy/demo/README.md) — §3 parámetros, §5 camino de datos, §5.5c drenajes, §5.6 comprobación extremo a extremo, §7 desmontaje
- Tareas diferidas: [`openspec/DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md) — *«Este repositorio no tiene CI»* y *«C34 · el corpus de conocimiento no viaja en la imagen de `jbg-ai`»*
- Historia anterior: [HU-AIENG-042](HU-AIENG-042.md) · Change: `openspec/changes/redeploy-and-audit-demo-environment/`
- Mundo sintético y usuarios: [HU-AIENG-010](HU-AIENG-010.md) y `ai-service/src/jbg_ai/data/README.md`

---

## Criterios de Aceptación

### Escenario 1: El estado del entorno se establece antes de tocarlo

- **Dado que** no consta si la instancia de la demo sigue en pie ni si los siete secretos de
  `/jbg-demo/` existen
- **Cuando** se ejecuta el primer grupo de tareas
- **Entonces** queda escrito, con la salida del comando, si la instancia existe y en qué estado, qué
  parámetros hay bajo `/jbg-demo/` **por nombre y nunca por valor**, y si el *hostname* resuelve y
  responde
- **Y** la rama del recorrido —redespliegue sobre lo existente, o recreación desde cero— se declara
  antes de la primera tarea que modifique algo

### Escenario 2: La rama `demo` alcanza a `ai-eng` y el despliegue se dispara de verdad

- **Dado que** `origin/demo` está 84 commits por detrás de `ai-eng` y su último commit es el QA de C34
- **Cuando** se lleva `demo` a `ai-eng` y se empuja
- **Entonces** `deploy-demo.yml` se ejecuta, publica las dos imágenes y registra el `IMAGE_TAG` en SSM
- **Y** el despliegue **no** se omite por el filtro `paths-ignore` de `openspec/**` y `Documentos/**`,
  porque el conjunto empujado toca código

### Escenario 3: El panel del agente se sirve en la demo

- **Dado que** `AiAgentAssist__EnabledByDefault` es `bool` sin inicializador y por tanto `false`
- **Cuando** el compose lo declara como literal `"true"` y el entorno se redespliega
- **Entonces** un operador autenticado ve la **cuarta tarjeta** en el *hub* de venta asistida
- **Y** la ruta del agente responde 200 con su traza en vez de la puerta cerrada

### Escenario 4: El agente usa su propia credencial y no un repliegue

- **Dado que** el repliegue `agent → assist → rag` existe como red y deja constancia de cuál ganó
- **Cuando** `/jbg-demo/AGENT_LLM_API_KEY` está creado y `deploy.sh` lo exporta
- **Entonces** el log del arranque registra `stage=agent_client` con la credencial **propia** y no
  `assist_fallback`
- **Y** el valor de la clave no aparece en ningún fichero del anfitrión ni en la salida del comando de
  despliegue

### Escenario 5: Sin la credencial del agente, la ruta degrada y el despliegue no falla

- **Dado que** la ausencia de esa clave es un estado válido y declarado
- **Cuando** el parámetro no existe y se despliega
- **Entonces** `deploy.sh` **no** aborta: la lee con el patrón opcional y sigue
- **Y** la ruta del agente responde 200 sin ejecutar el bucle, que es el *fail-open*, la ablación y el
  *rollback* a la vez

### Escenario 6: El enrutador de intención deja de tomar prestada la clave del argumentario

- **Dado que** el despliegue de C34 registró `stage=router_client … credential=assist_fallback`
- **Cuando** `/jbg-demo/ROUTER_LLM_API_KEY` está creado y llega al contenedor
- **Entonces** el log registra la credencial propia del enrutador
- **Y** el coste de la clasificación queda separable del de la generación

### Escenario 7: El corpus viaja en la imagen y la pregunta sobre una pieza responde con citas

- **Dado que** hoy el *build* de `jbg-ai` usa contexto `ai-service` y el corpus vive fuera de él, y que
  `jbg-demo-ai` no declara volúmenes
- **Cuando** la imagen se construye con el contexto que alcanza `data/knowledge`
- **Entonces** dentro del contenedor el corpus existe y `sync-knowledge` indexa sus fragmentos
- **Y** `ai.knowledge_chunk` deja de estar a cero
- **Y** una pregunta sobre una pieza en la ficha de venta devuelve respuesta **con citas desplegables**
  en vez de `knowledge_not_covered`

### Escenario 8: La verificación falla cuando el corpus está vacío

- **Dado que** un entorno con índice vectorial lleno y corpus vacío **hoy pasa la verificación**
- **Cuando** `verify.sh` corre sobre un entorno cuyo `ai.knowledge_chunk` está a cero
- **Entonces** la verificación **falla** nombrando esa condición
- **Y** el despliegue no se declara correcto

### Escenario 9: La verificación falla cuando la ruta del agente no responde

- **Dado que** el fallo de esa ruta es silencioso: la pantalla renderiza y el certificado es válido
- **Cuando** `verify.sh` corre y la ruta del agente no contesta
- **Entonces** la verificación falla nombrando esa condición
- **Y** una degradación en banda —una respuesta 200 con motivo de parada por fallo de proveedor o por
  falta de cliente— **no** se cuenta como fallo de transporte, porque no lo es

### Escenario 10: La demo es alcanzable desde internet y sólo por donde debe

- **Dado que** la spec viva exige que sólo el proxy inverso sea alcanzable desde internet y que el
  transporte se sirva bajo un *hostname* parametrizado
- **Cuando** se comprueba el entorno desde fuera
- **Entonces** el *hostname* resuelve y sirve HTTPS con certificado válido para ese nombre
- **Y** ni la API, ni el servicio de IA, ni la base de datos exponen puerto alguno al exterior
- **Y** el servicio de IA sólo es alcanzable por nombre dentro de la red interna

### Escenario 11: El evaluador entra con cuatro credenciales y ve tres mostradores distintos

- **Dado que** `admin` lo siembra `DatabaseSeeder` y los tres operadores vienen del mundo sintético con
  `Operator123!`
- **Cuando** el evaluador entra con cada uno sobre el entorno desplegado
- **Entonces** `admin` alcanza la tarjeta de salud de la IA y el resto de la administración
- **Y** `op-ciutadella` encuentra piezas con existencias y recibe argumentario generado
- **Y** `op-fornells` se topa con abstención, sustitutos y avisos de agotado, porque su tienda tiene el
  mínimo de surtido
- **Y** `op-aeroport` puede llevar al agente a **pivotar a sustitutos**, porque su tienda es la de más
  agotados
- **Y** la entrega dice, por usuario, **qué hay que probar ahí**

### Escenario 12: Producción queda intacta — no regresión

- **Dado que** la ruta de producción está fuera de alcance por restricción dura
- **Cuando** se revisa el conjunto de ficheros modificados
- **Entonces** ninguno es `deploy-aws-ec2.yml`, `deploy-backend-aws.yml`, `deploy-frontend-aws.yml`, el
  *stack* `terraform/` ni `Dockerfile.bundled`
- **Y** el cambio de contexto de *build* de `ai-service/Dockerfile` no afecta a producción, porque
  producción **no construye esa imagen**

### Escenario 13: La CI se ejecuta por primera vez y no bloquea a nadie

- **Dado que** `test-backend.yml` y `test-frontend.yml` no se han ejecutado nunca porque disparan sobre
  ramas que no existen
- **Cuando** se corrigen a `[ai-eng, master]`
- **Entonces** los dos workflows se ejecutan y publican su resultado
- **Y** su resultado **no** bloquea la integración: entran informativos, con los fallos preexistentes
  declarados y no arreglados

### Escenario 14: Fuera de alcance explícito — ni README, ni vídeo, ni suites en verde

- **Dado que** esta historia entrega el entorno y no la entrega
- **Cuando** se cierra
- **Entonces** el README del Proyecto Final, el vídeo, el tag y las evidencias **no** forman parte de lo
  entregado, y quedan nombrados como de C39b
- **Y** las suites siguen rojas en su nivel preexistente, declarado con sus cifras
- **Y** ningún ajuste de comportamiento —umbrales, pesos, presupuestos— se ha movido

---
---

## Cierre de los catorce escenarios

**Repartido entre dos changes, y por una razón estructural:** el despliegue de la demo se dispara al
mergear a la rama `demo`, o sea **después** de archivar el change que lo prepara. C39a dejó el árbol
correcto y no podía verificar el resultado; **C39a-bis** recorre el entorno ya desplegado. La evidencia
está en [`c39a-implementation-measurements.md`](../../Proyecto%20Final%20AIEng/informes/c39a-implementation-measurements.md)
y [`c39a-bis-implementation-measurements.md`](../../Proyecto%20Final%20AIEng/informes/c39a-bis-implementation-measurements.md).

| # | Escenario | Cerrado por | Veredicto |
|---|---|---|---|
| 1 | El estado del entorno se establece antes de tocarlo | **C39a** | ✅ cumplido |
| 2 | La rama `demo` alcanza a `ai-eng` y el despliegue se dispara de verdad | **C39a-bis** | ✅ **cumplido** — PR #47, ejecución `36322635852`, `IMAGE_TAG` de `sha-d6a740fa…` (v8) a `sha-2b357a1e…` (v9), idéntico a `git rev-parse origin/demo` |
| 3 | El panel del agente se sirve en la demo | **C39a-bis** | ⚠️ **parcial** — `AiAgentAssist__EnabledByDefault=true` en el contenedor y la ruta responde con el bucle completo, pero **la tarjeta no se ha visto**: sin navegador en la sesión de verificación |
| 4 | El agente usa su propia credencial y no un repliegue | **C39a-bis** | ✅ **cumplido** — `stage=agent_client … credential=agent`, y lo mismo `router` y `assist`. **Ningún `assist_fallback`** |
| 5 | Sin la credencial del agente, la ruta degrada y el despliegue no falla | **C39a** | ✅ cumplido por construcción; **no se ejercitó** contra el entorno vivo, porque exigiría borrar el parámetro y redesplegar |
| 6 | El enrutador deja de tomar prestada la clave del argumentario | **C39a-bis** | ✅ **cumplido** — `stage=router_client … credential=router`, parámetro propio creado el 2026-09-27 |
| 7 | El corpus viaja en la imagen y la pregunta sobre una pieza responde con citas | **C39a-bis** | ✅ **cumplido** — 161 fragmentos, y la ficha de `SKU983` llegó citando `material-laton#cuidados-y-limpieza-en-casa` |
| 8 | La verificación falla cuando el corpus está vacío | **C39a** | ✅ cumplido — la condición existe y pasa con 161. Su rama de fallo **no** se provocó: vaciar el corpus del entorno vivo no es aceptable |
| 9 | La verificación falla cuando la ruta del agente no responde | **C39a** | ✅ cumplido — la condición existe y pasa. Igual que la anterior, su rama de fallo no se provocó |
| 10 | La demo es alcanzable desde internet y sólo por donde debe | **C39a-bis** | ✅ **cumplido** — `200` con certificado real de **Let's Encrypt `YE1`** (leído desde el anfitrión, porque en local el MITM de Norton falsea la cadena), `308` de `http` a `https`, y el grupo de seguridad abre **sólo** 80 y 443 |
| 11 | El evaluador entra con cuatro credenciales y ve tres mostradores distintos | **C39a-bis** | ⚠️ **cumplido tras corregir una premisa falsa.** Las tres cuentas `op-*` **no existían** en la demo y `admin` estaba desactivada a propósito; se aprovisionaron los tres operarios y las cinco cuentas activas quedan declaradas en el §5.8 del *runbook*. Los tres mostradores se recorrieron y **rinden lo que el escenario pedía**. Lo que **no** se cumple es la primera línea: `admin` **no** alcanza la tarjeta de salud, y no debe — ver abajo |
| 12 | Producción queda intacta — no regresión | **C39a-bis** | ✅ **cumplido** — ninguna ruta de producción tocada, ningún ajuste de comportamiento movido, y el diff entero cae en el `paths-ignore` del despliegue |
| 13 | La CI se ejecuta por primera vez y no bloquea a nadie | **C39a-bis** | ⚠️ **cumplido con una corrección.** Se ejecutaron **cuatro** veces, no dos; **las de frontend no publicaron resultado**, porque morían en un lint que no podía funcionar. Con `eslint.config.js` creado y el paso en `continue-on-error`, la suite corrió por fin: **113 de 959 en 14 de 63**. Y **no bloquea**: ninguna rama tiene protección configurada |
| 14 | Fuera de alcance explícito — ni README, ni vídeo, ni suites en verde | **C39a-bis** | ✅ **cumplido** — nada de eso se entregó, queda nombrado como C39b, y las suites siguen rojas en su nivel preexistente con sus cifras declaradas |

### Lo que el escenario 11 pedía y NO se cumple, dicho explícitamente

El escenario abre con «**Dado que** `admin` lo siembra `DatabaseSeeder`… **Entonces** `admin` alcanza la
tarjeta de salud de la IA». **Eso no ocurre, y no debe ocurrir.** El §5.3 del *runbook* deja `admin`
**desactivada a propósito**, porque el sembrador la recrea en cada arranque con una contraseña que es
una constante de un repositorio público y el entorno es accesible desde internet. La premisa del
escenario era incorrecta al escribirse.

La cuenta administradora utilizable es `demo.admin`, cuya contraseña **no está en el repositorio** —se
generó fuera del anfitrión y sólo viajó el hash—, así que **la tarjeta de salud de la IA quedó sin
ejercitar**. Verificado sí está que la ruta es `[Authorize(Roles = "Administrator")]` y que devuelve
`403` a un operario, y que los cuatro interruptores `*__EnabledByDefault` están en `true`.

### Y dos cosas que el recorrido destapó y que no se arreglan aquí

- **La quinta condición de `verify.sh` marca en rojo un despliegue sano**, porque cuenta puntos de venta
  sin surtido **sin preguntar si la tienda está activa**, y `HT-ARTRUTX` está cerrada desde C10 a
  propósito. El experimento da `1` sin el filtro y `0` con él. Es la razón por la que el despliegue del
  2026-09-27 figura como fallido.
- **El pivote del agente sigue siendo inalcanzable por nombre**, y ahora está medido sobre el entorno
  desplegado: por referencia, 4 iteraciones y `buscar_sustitutos`; por nombre, 3 iteraciones, 2
  herramientas y **ningún** pivote.

Las dos, con su experimento y su vía de cierre, en
[`openspec/DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md).


## Notas adicionales

- **Actor beneficiario real:** el evaluador del Proyecto Final. El actor que ejecuta es el desarrollador
  del proyecto; ninguna de las dos figuras es un rol del sistema, y por eso la historia se escribe como
  habilitadora.
- **Esta historia no añade comportamiento de producto.** Lo que añade es que el comportamiento ya
  construido **llegue** a un entorno alcanzable. Los cinco huecos son de configuración y empaquetado,
  no de lógica.
- **El patrón de la puerta de entrada se hereda de C42**, que abrió con «las tres líneas base» y
  descubrió por el camino que las tres suites no se pueden medir en paralelo. Aquí la incógnita es el
  estado de la cuenta de AWS, y se trata igual: primero se mide, después se decide.
- **Cuatro changes de este proyecto nacieron de comprobaciones manuales** —C40, C40_FIX, C41 y C42— y
  los cuatro destaparon cosas que las tres suites verdes no veían. Es la razón por la que el recorrido
  del escenario 11 es un entregable y no un trámite.
- **Aviso operativo heredado:** la cuota de tokens por minuto de la organización permite del orden de
  **una petición por minuto** en este entorno. Basta para un mostrador y para un evaluador; no para dos
  mostradores simultáneos. Es un límite declarado, no un defecto a corregir aquí.
- Se implementa por el change de OpenSpec **`redeploy-and-audit-demo-environment`**, sobre la rama
  `c39a-redeploy-and-audit-demo-environment` derivada de `ai-eng`.

---

## Tareas

1. **Puerta de entrada — el estado del entorno.** Inventariar por nombre los parámetros bajo
   `/jbg-demo/`, el estado de la instancia, la resolución del *hostname* y la respuesta de `/api/health`.
   Declarar cuál de los dos recorridos se sigue.
2. **Auditoría publicada.** Tabla de tres columnas sobre los tres servicios: ajuste declarado · valor en
   la demo · qué pasa si falta. Incluye la fila del frontend explicando por qué no tiene entorno de
   ejecución.
3. **`compose.demo.yaml`** — `AiAgentAssist__EnabledByDefault`, `JPV_AGENT_LLM_API_KEY`,
   `JPV_ROUTER_LLM_API_KEY` y sus modelos si procede.
4. **`deploy/demo/deploy.sh`** — lectura opcional de los dos parámetros nuevos, con el patrón de
   `ASSIST_LLM_API_KEY` y su registro de *presente/ausente* sin revelar el valor.
5. **SSM** — crear los dos parámetros nuevos como `SecureString`, a mano, y anotarlos en el §3 del
   *runbook* marcados como opcionales.
6. **`ai-service/Dockerfile` y el workflow** — mover el contexto de *build* a la raíz y copiar el
   corpus, comprobando el tamaño resultante del contexto.
7. **`deploy/demo/verify.sh`** — dos condiciones de fallo nuevas: corpus vacío y ruta del agente sin
   respuesta.
8. **Specs de OpenSpec** — delta sobre `demo-deployment` para los requisitos que se mueven.
9. **CI** — ramas de `test-backend.yml` y `test-frontend.yml` a `[ai-eng, master]`, informativas, con el
   filtro `paths:` conservado.
10. **`demo` alcanza a `ai-eng`** y el despliegue se dispara; comprobar que no se omite por filtro.
11. **Verificación desde dentro del anfitrión** y desde internet.
12. **Recorrido manual con los cuatro usuarios** sobre las cuatro superficies de IA, con evidencia.
13. **Documentación** — *runbook* al día con C42, credenciales del evaluador con lo que cada una enseña,
    y cierre de la tarea diferida del corpus.

---

## Estimaciones y atributos de priorización

| Atributo | Valor |
|---|---|
| Puntos de historia | _Pendiente_ — depende del recorrido que decida la tarea 1 |
| Impacto | **Máximo.** Sin esto el §5 de la convocatoria no se cumple: el sistema no es accesible |
| Urgencia | **Máxima.** Es el primero de los dos changes que quedan, y C39b depende de él |
| Complejidad | **Media.** Ninguna tarea es difícil; el riesgo está en la cantidad de superficies y en que dos de los cinco huecos fallan en silencio |

### Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| ~~El entorno se desmontó y el recorrido es el largo~~ | **Descartado por medición el 2026-09-27**: está en pie desde el 30 de agosto con los siete secretos. Si el *apply* lo encontrara caído, el §7 del *runbook* documenta el desmontaje y el §2 la recreación |
| La proyección de disponibilidad lleva cinco semanas sin drenar y la demo enseña ámbitos degradados | **Se cura con el propio *fast-forward***: el drenaje de C41 corre al arrancar, y en su forma completa cuando no existe *checkpoint*. Se comprueba en el tramo de verificación, no se da por hecho |
| Mover el contexto de *build* de `jbg-ai` engorda la imagen o rompe el *build* | El contexto de la API ya lo hace y su comentario documenta que el `.dockerignore` de raíz lo mantiene en decenas de megas. Se mide el tamaño antes y después |
| Tocar por error un fichero de producción | La tabla de separación es explícita y el escenario 12 lo comprueba sobre el conjunto de ficheros modificados |
| Un despliegue omitido por `paths-ignore` que parezca hecho | El escenario 2 exige comprobar que el workflow **se ejecutó**, no que se empujó |
| Encender la CI destapa cientos de fallos y parece una regresión | Entra informativa, y `CLAUDE.md` ya documenta los rangos preexistentes y su rotación |
| La cuota de un minuto por petición alarga el recorrido manual | Se acepta y se declara; cuatro superficies por tres operadores caben en una sesión |
| Dependencia: **C39b** no puede empezar antes | Es el motivo de la partición, y está escrito en el §0 del plan |

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta |
|---|---|---|
| ~~**P1**~~ | ~~¿Sigue en pie el entorno, o se desmontó?~~ | **CERRADA el 2026-09-27 con medición contra la cuenta: en pie.** Instancia arrancada el 30 de agosto, los siete secretos existentes —incluido el opcional del argumentario—, HTTPS válido y cero migraciones pendientes. **Recorrido corto.** Y con ello queda confirmado contra la cuenta viva, y no sólo contra el repositorio, que `AGENT_LLM_API_KEY` y `ROUTER_LLM_API_KEY` **no existen** |
| **P6** | ¿`ai.knowledge_chunk` está a cero en el entorno vivo, o el apaño manual de C34 sobrevive desde el 22 de septiembre? | Se asume **a cero o inservible**: aunque hubiera sobrevivido al contenedor, no sobrevive a la imagen nueva. Se mide en la tarea 1 y el hueco se cierra igual |
| **P2** | ¿Las dos claves nuevas apuntan al mismo proveedor y valor que `ASSIST_LLM_API_KEY`, o a claves distintas? | **Parámetros distintos con el mismo valor**, que es lo que el *runbook* ya admite para la de *embeddings*: separa los costes sin multiplicar las cuentas |
| **P3** | ¿El corpus entra por contexto de *build* o por volumen? | **Contexto de *build***, por D5 — la imagen tiene que ser reproducible por sí sola |
| **P4** | ¿Se aprovecha para dar al *hostname* un dominio comprado? | **No.** El §6 del *runbook* lo documenta y la imagen es agnóstica del nombre, así que puede hacerse después sin reconstruir |
| **P5** | ¿La CI cubre también `ai-service`? | **No en esta historia.** No hay workflow de `pytest` y crearlo es trabajo nuevo; se declara como hueco |
