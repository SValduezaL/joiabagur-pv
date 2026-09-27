## Context

C39a dejó el árbol correcto y el entorno sin tocar. Su merge a `demo` es lo que redespliega, así que todo lo que hay que comprobar **sobre el resultado** vive necesariamente después de archivarlo. Este change es ese después.

```
C39a                    árbol arreglado, verificado localmente y contra el entorno ANTERIOR
  │  archivar
  │  PR → ai-eng
  │  demo ← ai-eng   ──────────────→  deploy-demo.yml construye y despliega
  ▼
C39a-bis                recorre el entorno RESULTANTE y deja la evidencia
  │  PR → ai-eng
  │  demo ← ai-eng   ──────────────→  NO despliega: todo lo que toca está en paths-ignore
  ▼
C39b                    README de entrega, vídeo, tag, evidencias
```

### Lo que C39a midió y este change contrasta

| Medido antes del despliegue | Qué se esperaba después | **Qué salió** *(2026-09-27)* |
|---|---|---|
| `IMAGE_TAG` = `sha-d6a740fa5e0b…`, que es el HEAD de `origin/demo` | otro, y correspondiente al HEAD nuevo | ✅ `sha-2b357a1e…`, versión **9** del parámetro, idéntico a `git rev-parse origin/demo` |
| `ai.knowledge_chunk` = **161** | igual o mayor; la tabla vive en el volumen y el despliegue no lo toca | ✅ **161**, exactamente. El volumen sobrevivió: `jbg-demo-postgres` llevaba **4 semanas** en pie frente a los 19 minutos de los otros dos |
| proyección a **~120 ×** el techo de rancidez | curada, porque el drenaje de C41 corre al arrancar | ✅ curada — **pero la lectura del propio workflow no lo vio**, porque el informe se cachea 10 s y el drenaje de arranque necesitó **dos intentos**. Ver Q1 |
| las siete condiciones de `verify.sh`, probadas canalizando el script | ejecutadas por el propio workflow, sobre el script desplegado | ⚠️ ejecutadas, y **la quinta falla**: no por el entorno, sino por contar una tienda cerrada a propósito. **Seis de siete en verde** |
| ruta del agente respondiendo con credencial **de repliegue** | `stage=agent_client` con credencial propia | ✅ las tres propias: `credential=agent`, `credential=router`, `credential=assist`, **ningún `assist_fallback`** |
| `AiAgentAssist__EnabledByDefault` ausente → cuarta tarjeta invisible | la tarjeta presente | ✅ `AiAgentAssist__EnabledByDefault=true` en el contenedor, y la ruta del agente responde con el bucle completo. **La tarjeta no se pudo ver**: sin navegador. La de **salud de la IA** sí quedó ejercitada por su ruta, con la credencial del responsable |
| *(no previsto)* las cuentas del recorrido | — | ❌ **`op-*` no existían y `admin` estaba desactivada.** El §5.3 había dejado **dos** cuentas. Ver la nota del grupo 3 de `tasks.md` |

### La restricción que gobierna el diseño

```
paths-ignore de deploy-demo.yml:
   openspec/**   Documentos/**   **/README.md   CLAUDE.md   AGENTS.md   terraform/**
```

**Todo lo que este change escribe cae dentro.** No es una preferencia de estilo: es lo que le permite mergearse a `demo` sin construir imágenes ni reiniciar contenedores, y por tanto verificar sin arriesgar lo verificado.

## Goals / Non-Goals

**Goals:**

- Confirmar que el despliegue **ocurrió**, no que el *push* llegó.
- Ejercitar las **siete** condiciones de verificación sobre el entorno real.
- Establecer que las **tres** credenciales de generación son propias y no repliegues.
- Confirmar o **refutar** la predicción de que la proyección se cura sola.
- Recorrer las **cuatro** superficies de IA con los **cuatro** usuarios, y dejar la evidencia.
- Declarar las cuentas de demostración con lo que cada una ejercita.
- Leer la **primera** ejecución de la CI de la historia del repositorio.

**Non-Goals:**

- **Tocar código.** Ni una línea. Si el recorrido encuentra un defecto, se anota como tarea diferida o se abre un change; arreglarlo aquí haría que este change desplegara.
- El README de entrega, el vídeo y el tag: **C39b**.
- Cerrar la deriva de rama que C39a destapó: se declara con su vía, y su arreglo es código.
- Recalibrar cualquier ajuste, incluidos los tres relojes del agente.
- Volver a medir las suites de backend y frontend: **la PR de C39a ya las ejecuta en CI**, y esa ejecución es la que se lee.

## Decisions

### D1 · La comprobación del despliegue es la ejecución del workflow, no el *push*

`deploy-demo.yml` lleva `paths-ignore`, así que **un empuje cuyo contenido cayera entero en esas rutas no despliega y no avisa**. La comprobación mira tres cosas: que la ejecución exista, que haya publicado las dos imágenes, y que **el `IMAGE_TAG` de SSM haya cambiado** respecto al que C39a registró. El tercero es el único que no se puede simular: si el tag no se movió, no se desplegó, dijera lo que dijera el resto.

**Alternativa considerada:** dar por bueno el despliegue si la URL responde 200. **Rechazada**: la URL respondía 200 durante las cinco semanas en que el entorno servía C34. Un 200 no distingue un entorno actualizado de uno viejo, y ése es precisamente el defecto que este change existe para no repetir.

### D2 · La proyección se mide antes y después, y la predicción puede salir mal

C39a dejó escrito que el drenaje de C41 cura la rancidez al arrancar. **Es una predicción, no un hecho**, y este change la trata como tal: dos lecturas de la sección `projection` de `/health` y una comparación contra el techo. Si no se cura, el hallazgo es que el drenaje no corre como su spec dice, y eso es un defecto que se anota y **no se arregla aquí**.

### D3 · El recorrido del agente usa la **referencia** de la pieza, no su nombre

La comprobación manual de C42 estableció el mecanismo: `buscar_catalogo` devuelve posición, SKU, materiales, variante y motivos, **nunca el nombre del producto**. Preguntado por nombre, el bucle pasa el nombre a `consultar_disponibilidad`, recibe `referencia_desconocida`, se recupera buscando, y recibe candidatos identificados sólo por SKU: no puede saber cuál era la pieza que el cliente nombró, consulta la disponibilidad de otra y **correctamente no pivota**.

Así que el recorrido nombra la **referencia**, que es realista en un mostrador porque la pieza lleva su etiqueta delante, y la limitación se recuerda en la evidencia. **No se intenta arreglar**: está en `DEFERRED_TASKS.md` con tres opciones y su coste, y las tres son código.

### D4 · Las cuentas de demostración se declaran en el *runbook*, no en el informe

El informe es un registro de mediciones con fecha; el *runbook* es lo que alguien lee para operar el entorno. Una tabla de credenciales en el informe envejece con él. Y el *runbook* es `**/README.md`, o sea que está en el `paths-ignore`: se puede escribir sin desplegar.

**Y las diferencias entre operarios son el contenido, no un adorno:** `op-ciutadella` con surtido máximo da el camino feliz; `op-fornells` con el mínimo hace alcanzables la abstención, los sustitutos y los avisos de agotado; `op-aeroport`, el punto con más agotados —411 candidatos de 3.774, 13 de 48 consultas con una pieza agotada en el top-5—, es donde el pivote del agente se demuestra. Sin eso escrito, un evaluador entra con el primero y concluye que la abstención no existe.

### D5 · Un defecto encontrado durante el recorrido no se arregla en este change

Se anota en `DEFERRED_TASKS.md` con su experimento y su mecanismo, o se abre un change. **El motivo es estructural**: cualquier arreglo toca código, código está fuera del `paths-ignore`, y este change dejaría de poder mergearse sin desplegar — perdiendo la propiedad que lo separa de C39a.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| El despliegue de C39a falla y este change no tiene nada que verificar | Se para y se arregla **en C39a o en un change nuevo**, no aquí. `deploy.sh` valida los cinco secretos obligatorios en voz alta y `verify.sh` falla con la causa nombrada |
| La verificación destapa un defecto de las dos condiciones que C39a añadió | Es el resultado más valioso posible, y va al informe. Su arreglo es otro change |
| El recorrido manual se alarga por la cuota de una petición por minuto | Se acepta. Cuatro superficies por tres operarios caben en una sesión; **dos mostradores simultáneos no**, y es limitación declarada del entorno |
| Se cuela un fichero fuera del `paths-ignore` y el change redespliega | **Criterio de aceptación sobre el propio diff**, revisado fichero a fichero antes de la PR |
| La proyección no se cura y se lee como un fallo del despliegue | La predicción está escrita como predicción. Si se refuta, el hallazgo es del drenaje de C41 y se declara |
| Las dos ejecuciones de CI salen rojas y se leen como regresión de C39a | Se sabe de antemano: **50 de 1.408 y 113 de 959**, preexistentes, con nombres guardados por C39a para comparar |

## Open Questions

| # | Pregunta | Por defecto si no hay respuesta |
|---|---|---|
| **Q1** | ~~¿La proyección se cura sola al arrancar, como C39a predijo?~~ **CERRADA Y CONFIRMADA** *(2026-09-27)* | **La predicción se cumple.** De ~414.629 s —unas **115 veces** el techo de 3.600 s, con el último drenaje incremental el 22 de septiembre— a `status: ok`, `stale: false`, **cero páginas fallidas**, y el planificador drenando cada **600 s** desde el arranque. Con dos matices que la confirmación no debe tapar: la cura la hace el drenaje **incremental**, y `last_full_sync_at` **sigue** en el 22 de septiembre; y el **primer intento** de drenaje al arrancar falló con `feed_not_configured` porque el lado .NET aún no servía el *feed* — el segundo, nueve segundos después, es el que la curó |
| **Q2** | ¿El argumentario del agente llega generado, ahora que la ruta tiene credencial propia? | Se observa. C42 midió **1,2 %** de retirada con `v6`, así que lo esperable es que llegue |
| **Q3** | ¿Se alcanzan los tres estados de `op-fornells` —abstención, sustitutos, avisos de agotado— con el surtido que tenga hoy? | Se intenta y, si alguno no se reproduce, **se declara cuál y por qué** en vez de darlo por visto |
| **Q4** | ¿Conviene un dominio comprado antes de entregar? | **No.** El §6 del *runbook* lo cubre y la imagen es agnóstica del nombre, así que puede hacerse después sin reconstruir. Decisión de C39b |
