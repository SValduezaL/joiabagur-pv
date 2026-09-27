> **No se puede empezar antes de que C39a esté archivado y mergeado a `demo`.** El grupo 1 verifica
> el despliegue que ese merge dispara.
>
> **Y una restricción que se comprueba sobre el propio diff:** este change toca **sólo** ficheros
> que el `paths-ignore` de `deploy-demo.yml` ignora. Cualquier fichero fuera de esa lista lo
> convertiría en un redespliegue y perdería la razón por la que existe.

## 1. Que el despliegue ocurrió, no que el *push* llegó

- [ ] 1.1 Confirmar que la ejecución de `deploy-demo.yml` **existe** y terminó, y que publicó las dos imágenes. Validación: el identificador de la ejecución y su conclusión, escritos.
- [ ] 1.2 Confirmar que **el `IMAGE_TAG` de SSM cambió** respecto al `sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d` que C39a registró, y que el nuevo corresponde al HEAD de `demo`. Validación: los dos valores y el `git rev-parse` al lado. **Es la única comprobación que no se puede simular**: sin cambio de tag no hubo despliegue, responda lo que responda la URL.
- [ ] 1.3 Comprobar que el arranque registró las tres credenciales de generación como **propias**: `stage=assist_client`, `stage=router_client` y `stage=agent_client`, **ninguna con `assist_fallback`**. Validación: las tres líneas citadas, sin ningún valor de clave.

## 2. Las siete condiciones, sobre el entorno real

- [ ] 2.1 `verify.sh` en verde con las siete condiciones, ejecutado por el propio workflow desde dentro del anfitrión. Validación: la salida completa en el informe.
- [ ] 2.2 Las dos condiciones que C39a añadió, ejercitadas sobre el script **desplegado** y no canalizado: recuento de corpus y ruta del agente. Validación: las dos líneas `[verify] OK` con sus cifras.
- [ ] 2.3 Contrastar `ai.knowledge_chunk` con los **161** que C39a midió. Validación: la cifra; igual o mayor, y si fuera menor es un hallazgo.
- [ ] 2.4 **La predicción de la proyección, confirmada o refutada.** C39a la midió a unas **120 veces** el techo y predijo que el drenaje de C41 la cura al arrancar. Validación: la frescura de `/health` contra el techo, y si **no** se ha curado, declararlo como refutación y anotarlo contra C41.
- [ ] 2.5 Comprobar desde internet: HTTPS válido bajo el *hostname*, y que **sólo el proxy** publica puertos. Validación: el `curl` con su `ssl_verify_result` y el reparto de puertos de los cuatro contenedores.

## 3. El recorrido del evaluador, a mano y sobre el entorno desplegado

- [ ] 3.1 `admin`: acceso con las credenciales sembradas, y la **tarjeta de salud de la IA** pintando. Validación: captura, y confirmación de que el reemplazo de personal del §5.3 del *runbook* no eliminó la cuenta.
- [ ] 3.2 `op-ciutadella`: búsqueda asistida y ficha de venta con argumentario **generado**, con precio y existencias resueltos en el texto. Validación: captura y el `pitchStatus` observado.
- [ ] 3.3 `op-fornells`: abstención, sustitutos y avisos de agotado. Validación: los tres alcanzados o **declarado cuál no se pudo reproducir y por qué**, sin darlo por visto.
- [ ] 3.4 `op-aeroport`: el panel del agente, con la **traza del bucle** visible y el **pivote a sustitutos**, nombrando la pieza por su **referencia**. Validación: la traza capturada, el pivote observado, y la limitación del nombre recordada en la evidencia.
- [ ] 3.5 Panel de consulta libre (M1): una consulta sin pieza contestada, un **rechazo cortés** del enrutador, y el ámbito global. Validación: los tres estados capturados.
- [ ] 3.6 Medir la latencia extremo a extremo de las cuatro superficies y contrastar los tres relojes del agente —8 s por vuelta, 15 s de reloj del servicio, 18 s de presupuesto en .NET— con el proxy delante. Validación: las cifras publicadas; **no se recalibra nada**.

## 4. La primera ejecución de la CI de la historia del repositorio

- [ ] 4.1 Leer las dos ejecuciones que la PR de C39a disparó por tocar sus propios ficheros de workflow. Validación: las dos existen y publican resultado — **es la primera vez**, porque hasta C39a disparaban sobre ramas inexistentes.
- [ ] 4.2 Comparar sus rojos **por nombre** contra la línea base que C39a guardó: 50 de 1.408 en backend y 113 de 959 en frontend. Validación: cero nombres nuevos en áreas que C39a toca; los que difieran deben caer en las clases y ficheros ya conocidos como inestables.
- [ ] 4.3 Confirmar que **no actúan como puerta** y que ninguno está configurado como comprobación requerida. Validación: la PR se pudo integrar con los dos en rojo, y queda escrito por qué con las cifras.

## 5. Las cuentas de demostración, declaradas

- [ ] 5.1 `deploy/demo/README.md`: tabla con los cuatro usuarios, su punto de venta y **qué behaviour es alcanzable desde cada uno**, más la restricción del pivote por nombre. Validación: la tabla cubre los cuatro y nombra la restricción como limitación declarada, no como defecto.
- [ ] 5.2 Sincronizar la delta de `demo-deployment`. Validación: **`openspec validate --all --strict` a `0 failed`**.

## 6. Cierre

- [ ] 6.1 Informe `c39a-bis-implementation-measurements.md` con las cifras del entorno desplegado, el recorrido con su evidencia, las latencias, y **lo que se refutó** de las predicciones de C39a. Validación: cada afirmación con su medición al lado o declarada como no medida.
- [ ] 6.2 Cerrar en [HU-AIENG-043](../../../Documentos/Historias/AI-Eng/HU-AIENG-043.md) los escenarios que este change verifica, dejando constancia de cuáles quedaron cubiertos por C39a y cuáles por éste. Validación: los catorce escenarios con su veredicto.
- [ ] 6.3 Poner al día el §0 del plan y las fichas de C39a y C39a-bis con el resultado del despliegue. Validación: ninguna afirmación de las fichas contradicha por los dos informes.
- [ ] 6.4 Anotar en `openspec/DEFERRED_TASKS.md` lo que el recorrido destape **sin arreglarlo**, y la deriva de rama que C39a dejó declarada: nada compara lo desplegado con la rama que debería servirse. Validación: cada entrada con su experimento y su vía de cierre.
- [ ] 6.5 **Comprobar la restricción propia de este change sobre el diff completo**: cero ficheros fuera de `openspec/**`, `Documentos/**`, `**/README.md`, `CLAUDE.md`, `AGENTS.md` y `terraform/**`. Validación: la lista de modificados, fichero a fichero, y la confirmación de que el merge a `demo` **no** dispara `deploy-demo.yml`.
