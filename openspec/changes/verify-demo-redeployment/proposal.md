## Why

**C39a arregla el entorno y no puede comprobarlo.** El despliegue de la demo se dispara al mergear C39a a la rama `demo`, así que sus tareas de verificación exigían un entorno que sólo existe **después** de archivar el change que las contenía. Un change que sólo se puede cerrar después de cerrarse no es un change, y por eso C39a se partió en dos el 2026-09-27, durante su propio apply.

Este es el otro lado: **recorrer el entorno ya desplegado y dejar la evidencia escrita**. Y tiene una propiedad que lo hace barato: toca **únicamente** ficheros que el `paths-ignore` de `deploy-demo.yml` ignora —`openspec/**`, `Documentos/**`, `**/README.md`, `CLAUDE.md`, `AGENTS.md`, `terraform/**`—, así que mergearlo a `ai-eng` y a `demo` **no dispara ningún despliegue**. Verificar no cuesta un redespliegue.

Y hay una razón de fondo para que esto sea un change y no una nota al pie: **cuatro changes de este proyecto nacieron de comprobaciones manuales** —C40, C41, C42 y `C40_FIX`— y los cuatro destaparon cosas que las tres suites verdes no veían: el panel sirviendo por su ruta degradada, los filtros descartándose en silencio, el ámbito global inalcanzable, el pivote inalcanzable por nombre. El recorrido a mano es el instrumento que más defectos ha encontrado en este proyecto.

## What Changes

- **Se confirma que el despliegue ocurrió de verdad**, y no sólo que el *push* llegó: la ejecución del workflow existe, publicó las dos imágenes y **el `IMAGE_TAG` de SSM cambió** respecto al `sha-d6a740fa5e0b…` que C39a midió. El filtro `paths-ignore` hace posible un *push* que no despliega y no avisa, así que la comprobación es la ejecución y no el empuje.
- **Las siete condiciones de `verify.sh` se ejercitan sobre el entorno desplegado**, incluidas las dos que C39a añadió y que hasta ahora sólo se probaron canalizando el script contra el entorno anterior.
- **Se comprueba que las tres credenciales de generación son propias y no un repliegue**: el log debe decir `stage=agent_client` y `stage=router_client` sin `assist_fallback`, que es lo que el despliegue de C34 registró y el motivo por el que C39a creó los dos parámetros.
- **Se mide si la proyección se ha curado sola.** C39a la midió a **unas 120 veces** el techo de rancidez —último drenaje incremental el 22 de septiembre contra un techo de 3.600 s—, y el drenaje de C41 corre al arrancar y en su forma completa cuando no hay *checkpoint*. Es una predicción que se confirma o se refuta con dos lecturas.
- **El recorrido del evaluador, a mano, con los cuatro usuarios y las cuatro superficies de IA**: búsqueda asistida, ficha de venta, panel de consulta libre y panel del agente. Con el aviso que C42 dejó medido: el pivote a sustitutos es **inalcanzable si la pieza se nombra por su nombre** en lugar de por su referencia, así que el recorrido usa la referencia y la limitación se declara.
- **Las cuentas de demostración quedan declaradas**, con qué ejercita cada una, para que quien reciba la URL alcance las cuatro superficies sin adivinar. Hoy existen —`admin` sembrado y tres operadores del mundo sintético— y **no están escritas en ninguna parte junto a lo que demuestran**.
- **Se lee la primera ejecución de la CI**, que la PR de C39a dispara por tocar sus propios ficheros de workflow, y se confirma que **no actúa como puerta**: los dos saldrán en rojo con los 50 de 1.408 y los 113 de 959 preexistentes.
- **Se cierra el plan del Proyecto Final**: informe de despliegue, ficha de C39a-bis y §0 al día.

**Sin código, y es una restricción y no una casualidad.** Si la verificación encuentra un defecto que exija tocar código, **no se arregla aquí**: se abre un change propio. Arreglarlo dentro de éste convertiría un change que no despliega en uno que sí, y perdería la propiedad que lo hace barato.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `demo-deployment`: **una adición**. La capability especifica que los datos de demostración llevan el catálogo y no el personal real de la tienda, pero **no dice nada de las cuentas con las que se entra ni de qué demuestra cada una**. Un entorno cuyo único propósito es ser evaluado necesita que eso esté declarado, porque las diferencias entre sus puntos de venta —surtido máximo, surtido mínimo, más agotados— son las que hacen alcanzables la abstención, los sustitutos y el pivote del agente, y nadie las adivina desde fuera. Se añade el requisito, y su implementación es documentación: el *runbook*, que está en el `paths-ignore` del despliegue.

## Impact

**Se toca, y sólo esto:**

- `deploy/demo/README.md` — la tabla de cuentas de demostración con lo que ejercita cada una *(`**/README.md`, ignorado por el despliegue)*
- `Documentos/Proyecto Final AIEng/informes/c39a-bis-implementation-measurements.md` — la evidencia del recorrido
- `Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md` — §0 y la ficha
- `Documentos/Historias/AI-Eng/HU-AIENG-043.md` — cierre de los escenarios que este change verifica
- `openspec/changes/verify-demo-redeployment/` y `openspec/specs/demo-deployment/spec.md` al sincronizar
- `openspec/DEFERRED_TASKS.md` — si el recorrido destapa algo, **se anota y no se arregla**

**No se toca nada más.** Ni `compose.demo.yaml`, ni `deploy/demo/deploy.sh`, ni `deploy/demo/verify.sh`, ni ningún `Dockerfile`, ni `backend/src`, ni `frontend/src`, ni `ai-service/src`, ni los workflows. **Es un criterio de aceptación comprobable sobre el propio diff**, no una intención: cualquier fichero fuera de la lista de `paths-ignore` convertiría este change en un redespliegue.

Y la ruta de **producción** sigue prohibida, igual que en C39a.

### Una limitación que C39a destapó y que este change declara sin cerrar

**Nada detecta que la demo esté sirviendo una rama vieja.** El entorno estuvo **84 commits y cinco semanas** por detrás sin que ninguna comprobación lo dijera: `verify.sh` mira índice, modelo, base, credencial, proyección y —desde C39a— corpus y ruta del agente, y **ninguna de las siete condiciones compara lo desplegado con la rama que debería servir**. El dato existe: `IMAGE_TAG` en SSM es el `sha-` del commit, y `git rev-parse origin/demo` es el otro lado. Lo que no existe es quien los compare.

**Vía de cierre, escrita y no hecha:** una condición de deriva en el workflow de despliegue —que conoce el commit que construye— o un aviso en la tarjeta de administración. No entra aquí porque ambos son código y este change no toca código, que es exactamente la restricción que lo hace mergeable sin desplegar.
