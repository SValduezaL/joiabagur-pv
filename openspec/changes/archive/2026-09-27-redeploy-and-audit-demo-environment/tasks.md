> **Partido en dos el 2026-09-27, durante el apply, y el motivo es de orden y no de tamaño.**
> Este change no podía cerrarse: sus tareas de verificación exigían un entorno desplegado, y el
> despliegue sólo ocurre **al mergear este change** a la rama `demo`. Un change que sólo se puede
> archivar después de archivarse no es un change.
>
> Aquí queda **todo lo que se puede hacer y comprobar antes de desplegar**. La verificación del
> entorno desplegado, el recorrido del evaluador y el cierre del plan pasan a **C39a-bis**, que
> toca **únicamente** ficheros que el `paths-ignore` de `deploy-demo.yml` ignora —`openspec/**`,
> `Documentos/**`, `**/README.md`, `CLAUDE.md`, `AGENTS.md`, `terraform/**`— y por tanto se puede
> mergear a `ai-eng` y a `demo` **sin disparar ningún despliegue**.
>
> El nombre se conserva: mergear este change a `demo` **es** lo que redespliega.

## 1. Puerta de entrada — sólo lectura, nada se modifica

- [x] 1.1 Re-tomar la foto desde fuera con el perfil `jbg-demo`: parámetros bajo `/jbg-demo/` **por nombre y nunca por valor**, estado y antigüedad de la instancia, `DEMO_HOSTNAME`, `IMAGE_TAG` vigente y `curl` al `/api/health` público. Validación: las salidas pegadas en el informe, y el `IMAGE_TAG` contrastado contra `git rev-parse origin/demo`.
- [x] 1.2 Medir desde **dentro** del anfitrión, por el servicio de gestión de sistemas: `count(*)` de `ai.knowledge_chunk`, `count(*)` de `ai.pos_projection` y el *checkpoint*. Validación: las cifras escritas.
- [x] 1.3 Confirmar que el recorrido es el corto y declararlo **antes** de la primera modificación. Validación: una frase con la decisión y su evidencia.
- [x] 1.4 Medir la línea base de las dos suites **en serie, nunca en paralelo**, leyendo la **línea de resumen** y no el código de salida. Validación: los dos recuentos y los nombres rojos guardados para comparar.

## 2. La auditoría, publicada como entregable

- [x] 2.1 Volcar los ajustes que declara cada servicio, con el comando que lo reproduce escrito en el informe.
- [x] 2.2 Cruzarlos contra `compose.demo.yaml` en tabla de tres columnas —**ajuste declarado · valor en la demo · qué pasa si falta**—, sin dejar ningún ajuste sin clasificar.
- [x] 2.3 Incluir la fila del frontend explicando que **no tiene entorno de ejecución**, citando el comentario del workflow que lo argumenta.
- [x] 2.4 Anotar los desajustes de documentación que la auditoría destape, con su cita textual.

## 3. Los cinco huecos de configuración

- [x] 3.1 `compose.demo.yaml`: `AiAgentAssist__EnabledByDefault: "true"`, con el comentario que explica por qué un interruptor omitido **no** es un valor por defecto neutro. Validación: `docker compose config` resuelve con el entorno vacío.
- [x] 3.2 `compose.demo.yaml`: las dos credenciales nuevas con valor por defecto vacío. Validación: la misma orden, y vacío equivale a no configurada.
- [x] 3.3 `deploy/demo/deploy.sh`: lectura opcional con el patrón **literal** de `ASSIST_LLM_API_KEY` y registro *presente/ausente* por etapa, sin revelar valor. Validación: cero líneas `:?` para las dos nuevas, y el patrón demostrado que no aborta bajo `set -e`.
- [x] 3.4 Crear a mano los dos parámetros como `SecureString`. Validación: aparecen **por nombre**, sin descifrarlos.
- [x] 3.5 Meter el corpus en la imagen de `jbg-ai`. Validación: `docker build`, el corpus visible **dentro** del contenedor en la ruta que el código lee, y los tamaños de contexto e imagen medidos antes y después.
- [x] 3.6 `verify.sh`: sexta condición — corpus sin fragmentos. Validación: provocada, y **falla** nombrando la causa.
- [x] 3.7 `verify.sh`: séptima — ruta del agente sin respuesta, distinguiendo el no responder de una degradación en banda. Validación: los dos casos por separado, y el degradado **no** hace fallar.

## 4. El arreglo de fondo que la implementación destapó · `ai-service/src`

> **Añadido durante el apply, y amplía la zona del change.** Al preparar la copia del corpus se
> midió que `CORPUS_DIR` se resolvía **dentro del entorno virtual** —`/app/.venv/lib/data/knowledge`—,
> porque `parents[3].parent` es correcto en un *checkout* y absurdo con el paquete instalado. El
> apaño era un enlace simbólico en la imagen; el arreglo es la búsqueda por candidatos que
> `load_prompt_file` ya hace, y cuyo *docstring* describe exactamente este problema.

- [x] 4.1 `knowledge/constants.py`: resolver `CORPUS_DIR` por candidatos —*checkout*, directorio de trabajo, `/app`—, **sin levantar excepción al importar**, para que un corpus ausente no se presente como una caída total del servicio. Validación: `discover_documents` sigue siendo quien falla, con el directorio nombrado.
- [x] 4.2 Test nuevo `tests/knowledge/test_corpus_location.py`: la resolución en *checkout*, que los candidatos cubren el contenedor, que el orden decide, que nunca levanta excepción, y que las rutas derivadas cuelgan de la resuelta. Validación: **5 passed**.
- [x] 4.3 Retirar el enlace simbólico del `Dockerfile`, que el arreglo hace innecesario, y reconstruir. Validación: `CORPUS_DIR` = `/app/data/knowledge`, **no es enlace**, 33 documentos y *sidecar* presente.
- [x] 4.4 Suite de `ai-service` completa, en serie con las otras dos. Validación: la línea de resumen, y cero rojos atribuibles a este cambio.

## 5. CI informativa

- [x] 5.1 `test-backend.yml` y `test-frontend.yml`: disparador de `[main, develop]` —**ninguna de las dos ramas existe**— a `[ai-eng, master]`, en `push` y en `pull_request`, conservando el filtro `paths:`. Validación: los dos YAML parsean con las ramas nuevas y los filtros intactos.

> **La observación de que se ejecutan pasa a C39a-bis**, porque sólo se puede hacer cuando la PR
> exista. Y se sabe de antemano que **saldrán en rojo**: 50 de 1.408 en backend y 113 de 959 en
> frontend, preexistentes y declarados. Informativos, no puerta.

## 6. El contrato y el esquema

- [x] 6.1 Confirmar que el *fast-forward* de 84 commits **no arrastra esquema**: ninguna migración de EF Core ni de Alembic entre `origin/demo` y `ai-eng`. Validación: los dos árboles de migraciones sin diferencias, escrito en el informe.
- [x] 6.2 Confirmar que `ai-service/openapi.json` no se mueve: este change no toca contrato. Validación: el snapshot sin diferencias y su test en verde.

## 7. Specs, documentación y cierre

- [x] 7.1 Deltas de `demo-deployment` y `backend-testing` al día con lo implementado, incluida la refutación de D5 y el arreglo de `CORPUS_DIR`. Validación: **`openspec validate --all --strict` a `0 failed`**.
- [x] 7.2 `deploy/demo/README.md`: los dos parámetros nuevos marcados como opcionales en el §3, el recuento de no secretos corregido a **cuatro**, C42 incorporado y la **nota de caducidad del bundle de CA** en el §1.3. Validación: relectura completa buscando afirmaciones que este change haya dejado falsas. *(La **tabla de credenciales del evaluador** se movió a C39a-bis, que es quien lleva su requisito de spec: tenerla en los dos sitios la habría escrito dos veces.)*
- [x] 7.3 Cerrar en `openspec/DEFERRED_TASKS.md` la entrada *«C34 · el corpus de conocimiento no viaja en la imagen»*, con la fecha y con las **dos** evidencias: el corpus dentro de la imagen y la resolución arreglada en el código. Validación: marcada como cerrada y **no borrada**.
- [x] 7.4 Informe `c39a-implementation-measurements.md` completo, con la auditoría, las cifras del entorno, los tamaños de imagen, el desvío del bundle de CA **y las tres refutaciones de los propios artefactos**. Validación: cada afirmación con su medición al lado, o declarada como no medida.
- [x] 7.5 Poner al día la ficha de **C39a** y el §0 del plan con la partición en C39a y C39a-bis y con lo refutado. Validación: ninguna afirmación de la ficha contradicha por el informe.
- [x] 7.6 Comprobar la restricción dura: **cero ficheros de la ruta de producción modificados** —`deploy-aws-ec2.yml`, `deploy-backend-aws.yml`, `deploy-frontend-aws.yml`, `terraform/`, `Dockerfile.bundled`—, revisando el diff fichero a fichero. Validación: la lista completa de modificados con el motivo por el que cada uno es de la ruta de demo, y el aviso de que `backend/docker-compose.yml` es el compose de **desarrollo** y no el de producción, que es `docker-compose.prod.yml`.

> **Las dos suites de siempre no se vuelven a medir aquí, y hay motivo.** Este change no toca
> `backend/src` ni `frontend/src`: lo que toca es compose, scripts de despliegue, `Dockerfile`,
> workflows, `ai-service/src` y documentos. Los insumos de esas dos suites **no han cambiado**, así
> que una segunda pasada de veinte minutos no compraría información. Y la comparación real llega
> gratis: **la PR de este change dispara los dos workflows**, porque toca sus propios ficheros. Esa
> ejecución se lee en C39a-bis.
