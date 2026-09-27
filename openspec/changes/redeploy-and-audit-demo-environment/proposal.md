## Why

El entorno de demostración del Proyecto Final **lleva cinco semanas sirviendo un sistema que ya no es el que el proyecto ha construido**. El despliegue se dispara por `push` sobre la rama `demo`, y `origin/demo` está **84 commits por detrás** de `ai-eng`, parado en el QA de C34: medido contra la cuenta el 2026-09-27, el `IMAGE_TAG` que está corriendo es `sha-d6a740fa5e0b…`, cuyo prefijo es exactamente el HEAD de esa rama. Lo desplegado **no contiene C36, C40, C40_FIX, C41 ni C42** — la ficha de venta, el panel de consulta libre con su ámbito global, el drenaje de la proyección de disponibilidad y el panel del agente: cuatro de las cinco superficies más visibles del entregable.

Y un redespliegue tal cual **no basta**, porque la configuración con la que arrancaría deja apagado el único pilar que no se puede enseñar de otra forma: `AiAgentAssist__EnabledByDefault` está ausente del compose y su tipo es `bool` sin inicializador, o sea `false`. El §5 de la convocatoria es tajante —*«si el evaluador no puede acceder al sistema funcionando, el proyecto no puede evaluarse correctamente»*—, y **C39b no puede documentar un recorrido que nadie ha recorrido**, que es la razón por la que este change va primero.

## What Changes

- **La rama `demo` alcanza a `ai-eng`**, y con ella las cinco piezas ausentes. Medido: 143 ficheros de código, **+21.496 / −247**, y **ninguna migración** ni de EF Core ni de Alembic — el *fast-forward* no mueve esquema. Hay que comprobar que el workflow **se ejecuta** y no lo omite su `paths-ignore` sobre `openspec/**` y `Documentos/**`.
- **`AiAgentAssist__EnabledByDefault` entra en `compose.demo.yaml` como literal versionado.** Los otros tres interruptores del mismo patrón ya están; éste falta, y sin él la cuarta tarjeta del *hub* no aparece.
- **Dos credenciales nuevas, opcionales y en sus tres capas**: `/jbg-demo/AGENT_LLM_API_KEY` y `/jbg-demo/ROUTER_LLM_API_KEY` como `SecureString` creados a mano, leídos en `deploy/demo/deploy.sh` con el patrón exacto de `ASSIST_LLM_API_KEY` —`|| true`, sin validación de no-vacío— y pasados al contenedor con valor por defecto vacío. **Confirmado contra la cuenta viva: ninguna de las dos existe.** Sin la del agente la ruta degrada por falta de credencial; sin la del enrutador, éste toma prestada la del argumentario y los costes de dos etapas distintas dejan de ser separables.
- **El corpus de conocimiento pasa a viajar dentro de la imagen de `jbg-ai`**, moviendo el contexto de *build* a la raíz del repositorio como ya hace el de la API. No es una línea `COPY` que falte: `CORPUS_DIR` apunta a `data/knowledge` y el contexto actual es el subdirectorio `ai-service`, así que el corpus está **fuera** de él; y `jbg-demo-ai` no declara volúmenes, de modo que el apaño manual con el que C34 lo sorteó no está codificado. Con `ai.knowledge_chunk` a cero, M2 retira el argumentario y M3 responde `knowledge_not_covered`, y parece un fallo de la ficha de venta. **Cierra una tarea diferida de C34.**
- **`deploy/demo/verify.sh` pasa de cinco condiciones de fallo a siete**: corpus vacío y ruta del agente sin respuesta. Son las dos cuyo fallo es silencioso — la pantalla renderiza, el certificado es válido y el despliegue parece un éxito. Es la misma familia que la proyección vacía que C41 ya cerró, dos tablas más allá.
- **La CI se enciende, informativa.** `test-backend.yml` y `test-frontend.yml` **no se han ejecutado nunca, ni una vez**, porque disparan sobre `branches: [main, develop]` y **ninguna de esas dos ramas existe**: las del repositorio son `master`, `ai-eng` y `demo`. Pasan a `[ai-eng, master]` conservando el filtro `paths:`. **No se convierten en puerta**: con 53 fallos preexistentes en backend y 113 en frontend, una puerta sobre una suite roja es un bloqueo que alguien acabará saltándose.
- **Y un arreglo de fondo que la implementación destapó, en `ai-service/src`**: `CORPUS_DIR` se resolvía **dentro del entorno virtual** —medido en el contenedor desplegado, `/app/.venv/lib/data/knowledge`—, porque `Path(__file__).resolve().parents[3].parent` es correcto en un *checkout* de desarrollo y absurdo con el paquete instalado por `uv sync --no-editable`. Pasa a resolverse por **la misma búsqueda de tres candidatos que `load_prompt_file`**, cuyo *docstring* describe este problema con estas palabras: *«a second copy of this search would be a second place for a container layout to diverge from a developer checkout»*. El corpus no tenía búsqueda, y por eso C34 tuvo que copiar los ficheros a esa ruta a mano en el anfitrión, sin commitear. **Con esto el enlace simbólico que el arreglo local necesitaba desaparece**, y el corpus queda en `/app/data/knowledge`, junto a `/app/prompts`.
- **La auditoría de configuración se publica como entregable**, en tabla de tres columnas —ajuste declarado · valor en la demo · qué pasa si falta— sobre los tres servicios.
- **El recorrido del evaluador queda comprobado a mano sobre el entorno desplegado** con los cuatro usuarios que ya existen, y **escrito**: `admin` y los tres operadores del mundo sintético, con lo que cada uno enseña.
- **El *runbook* se pone al día con C42** y se le corrige un desajuste que la medición destapó: su §3 dice *«Terraform creates the three non-secret parameters»* y son **cuatro** — falta `DEPLOYMENT_BUNDLE_URL`, que `ssm.tf` sí declara y la cuenta sí tiene.

**Sin *breaking changes*.** Ninguna ruta REST cambia de forma, `ai-service/openapi.json` queda intacto, el modelo de datos no se toca y no hay migración. Las dos credenciales nuevas son **opcionales**: su ausencia es un estado válido y declarado, no un fallo de despliegue.

## Capabilities

### New Capabilities

Ninguna. Este change no introduce comportamiento de producto: hace que el comportamiento ya construido llegue a un entorno alcanzable, y eso cae dentro de capacidades que ya existen.

### Modified Capabilities

- `demo-deployment`: cuatro de sus trece requisitos se mueven. **Los secretos que llegan por el entorno** crecen en dos, y los dos son **opcionales** —a diferencia de los obligatorios, que tienen su escenario de fallo ruidoso, éstos no pueden hacer fallar el despliegue por estar ausentes—. **Los ajustes de comportamiento versionados** incorporan el interruptor de la ruta del agente. **La verificación desde dentro del anfitrión** pasa de cinco condiciones de fallo a siete. Y **la reproducibilidad de las imágenes** cambia: la de IA pasa a contener el corpus, con un contexto de *build* distinto.
- `backend-testing`: su requisito **«Backend Test CI Workflow»** especifica el disparo *«on code changes to main/develop branches»*, y **ninguna de esas dos ramas existe en el repositorio**. La spec describe un workflow que no puede dispararse nunca, y el requisito pasa a nombrar las ramas reales. Se corrige además la expectativa de que la CI actúe como puerta mientras la suite arrastre fallos preexistentes.

> **Tres capabilities que este change toca y a las que deliberadamente NO escribe delta**, cada una con su motivo:
>
> - **`frontend-testing`.** Modifica `test-frontend.yml`, pero esa capability **no dice nada sobre CI**: sus nueve requisitos son de infraestructura de test —Vitest, componentes, MSW— y ninguno menciona ramas ni workflows. Escribir un requisito nuevo ahí sería ampliar la capability, no corregirla.
> - **`ai-service-dev-compose`.** Modifica `backend/docker-compose.yml`, y su primer requisito exige *«a `jbg-ai` service built from `ai-service/` (Dockerfile)»* — que **sigue siendo cierto**: el contexto primario no se mueve, sólo se añade uno con nombre. Ninguno de sus cuatro requisitos —red, pgvector, correr sin RDS, credenciales internas— cambia.
> - **`knowledge-corpus`.** Modifica cómo se **resuelve** la ruta del corpus, no qué es el corpus. Sus catorce requisitos hablan de documentos *«versionados en el repositorio»* y de que la cita resuelva a fichero y encabezado; **dónde mira el proceso no está especificado**, y sigue sin estarlo.

> **Partido en C39a y C39a-bis el 2026-09-27, durante el apply.** Este change no podía cerrarse: sus tareas de verificación exigían un entorno desplegado, y el despliegue ocurre **al mergearlo** a `demo`. Aquí queda todo lo previo; la verificación del entorno, el recorrido del evaluador y el cierre del plan pasan a **C39a-bis**, que toca sólo ficheros que el `paths-ignore` de `deploy-demo.yml` ignora y por tanto **no dispara despliegue** al mergearse.

## Impact

**Se toca:**

- `compose.demo.yaml` — tres claves de entorno nuevas (una de .NET, dos de `jbg-ai`)
- `deploy/demo/deploy.sh` — lectura opcional de dos parámetros, con registro de *presente/ausente* que nunca revela el valor
- `deploy/demo/verify.sh` — dos condiciones de fallo nuevas
- `deploy/demo/README.md` — §3 parámetros (y su recuento corregido), §5.6 comprobación, credenciales del evaluador, C42
- `ai-service/Dockerfile` — copia del corpus desde un contexto adicional con nombre
- **`ai-service/src/jbg_ai/knowledge/constants.py`** — la resolución de `CORPUS_DIR` por candidatos. **Amplía la zona declarada del change**, y es una ampliación decidida durante el apply sobre una medición, no un ensanche de alcance: sin ella el arreglo del corpus sería un enlace simbólico que tapa el defecto en vez de cerrarlo
- **`ai-service/tests/knowledge/test_corpus_location.py`** — el test que hoy no existe, y que es lo que convierte el arreglo en garantía
- `backend/docker-compose.yml` — el contexto adicional para el **entorno de desarrollo**, que hasta ahora tampoco llevaba el corpus dentro de su imagen. **No es el compose de producción**, que es `docker-compose.prod.yml`
- `.github/workflows/deploy-demo.yml` — contexto de *build* de la imagen de IA
- `.github/workflows/test-backend.yml`, `test-frontend.yml` — ramas del disparador
- `openspec/DEFERRED_TASKS.md` — cierre de la entrada del corpus de C34
- SSM, **fuera del repositorio** — dos parámetros `SecureString` creados a mano
- `Documentos/` — informe de auditoría e informe de implementación

**No se toca, y es una restricción dura del change: la ruta de producción.** `deploy-aws-ec2.yml`, `deploy-backend-aws.yml`, `deploy-frontend-aws.yml`, el *stack* `terraform/`, la región `eu-west-3`, la imagen `jpv-backend` y `Dockerfile.bundled`. La separación es estructural —cuenta AWS distinta, región distinta, *stack* distinto, imágenes distintas— y hay una comprobación que hace segura la tarea del corpus: **producción no construye la imagen de `jbg-ai`**, así que `ai-service/Dockerfile` es exclusivo de la ruta de demo. Queda fuera también el defecto conocido de que producción se redespliega ante cualquier cambio, incluido uno de sólo documentación: está anotado como tarea diferida, **es de otro change**, y la spec de C17 tiene un escenario que exige que ese flujo quede inalterado.

**Tampoco se toca:** `backend/src`, `frontend/src` ni `ai-service/src` — ninguna línea de lógica. Ni `terraform/demo/`: los dos *stacks* no tienen una sola variable de IA y **es correcto** que no la tengan, porque la configuración de IA vive en el compose como literal versionado y en SSM como secreto creado a mano, deliberadamente fuera del fichero de estado. Y ningún ajuste de comportamiento —umbrales de recuperación, pesos de fusión, banda de abstención, presupuestos del bucle— se recalibra: son literales versionados y moverlos invalidaría cifras ya publicadas.

**Fuera de alcance, y de C39b:** el README de entrega, el vídeo, el tag `v1.0-final-[INICIALES]`, las evidencias, y las tres tareas que sobrevivieron a la retirada de C38.
