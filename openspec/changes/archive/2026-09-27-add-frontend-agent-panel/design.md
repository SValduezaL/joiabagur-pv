## Context

El bucle del agente de venta está entregado desde C32b: recibe una conversación, decide vuelta a vuelta cuál de seis herramientas congeladas usa, y **no escribe la respuesta** — sólo reúne evidencia, que la misma capa de generación convierte en argumentario con la misma puerta numérica y la misma integridad referencial de citas que la ruta determinista. Por eso la respuesta del agente es subclase de la determinista: los mismos campos con el mismo significado, más cinco.

Lo que no existe es el camino hasta una persona:

```
 ┌──────────┐   ┌──────────────┐   ┌────────────────────┐   ┌──────────────────┐
 │ pantalla │ ? │ cliente de   │ ? │ POST /v1/assist/   │ ✓ │ bucle del agente │
 │  (nada)  │───│ la pasarela  │───│      agent         │───│ entregado y      │
 │          │   │ 7 ops.,      │   │ implementado y     │   │ medido con       │
 │          │   │ ninguna suya │   │ medido             │   │ proveedor real   │
 └──────────┘   └──────────────┘   └────────────────────┘   └──────────────────┘
       └────────── los dos eslabones que faltan ──────────┘
```

Dos hechos medidos sobre la pasada de 204 peticiones de C32b gobiernan el diseño, y ninguno es intuitivo:

- **El brazo del modelo domina cualquier otra variable.** Con el modelo servido, una respuesta incompleta por presupuesto ocurre en el **2,0 %** de las peticiones; con el barato, en el **58,8 %**, y su presupuesto de herramientas se agota 56 veces contra 2. Diseñar la pantalla alrededor de la respuesta cortada sería diseñarla para una configuración que no se sirve.
- **Una de cada cinco respuestas no trae ninguna pieza** (19,6 %, idéntico en los dos brazos), y de esas, tres cuartas partes son una repregunta o un rechazo cortés. **No es «sin resultados»: son estados normales de una conversación**, y son el estado especial más frecuente con diferencia.

Y hay un defecto de generación heredado: la tarea del agente vive en una versión de prompt cuyo *Sistema* ordena escribir marcadores de precio y existencias **sin condición**, mientras su payload no está anclado —correctamente, porque el argumentario habla de varias piezas— y C40 convirtió ese marcador en violación dura. El análogo estructural exacto **ya está medido**: bajo la misma frase, sobre payload sin anclar, los marcadores aparecieron en **3 de 90** generaciones y la reparación única los arregló **todas**, de modo que el defecto es real y su urgencia pequeña.

## Goals / Non-Goals

**Goals:**

- Que el agente tenga **superficie de operario** y que esa superficie **diga la verdad** sobre lo que el agente hizo: qué recuperó, en qué orden de pasos, qué es una coincidencia y qué un sustituto, y por qué paró.
- Que el argumentario del agente **pueda servirse**, dejando intacta la versión de prompt contra la que ya hay cifras medidas.
- Que la conversación **no se estrelle contra un rechazo** que la interfaz podía haber evitado.
- Que la pasada de medición **mida el sistema y no su desconfiguración**, con la antigüedad de la proyección registrada por fila.
- Que el agente **no se sirva por defecto**: ruta propia, comparable a simple vista con la determinista.

**Non-Goals:**

- El argumentario **por *streaming***. La mitigación es el estado de espera con la traza llegando al final.
- Preguntar por las existencias de **una tienda concreta o de varias**. Ninguna herramienta acepta punto de venta, y habilitarlo exige una tabla de qué tiendas ve cada usuario: es un cambio de modelo de autorización, no una herramienta más.
- Una **séptima herramienta**. Las seis están congeladas y sus dos ausencias son deliberadas.
- **Recalibrar los presupuestos** del bucle, aunque este change mida que el de herramientas es efectivamente seis y no ocho.
- El **desglose del consumo por etapa**, la **telemetría de la ficha** y el **registro de la consulta de ámbito global**, que arrastra migración.
- Los **escenarios puntuados del agente**, que pertenecen al change de evaluación.
- **Rehacer** la pasada de C32b. Se anota lo que de ella queda no medido.

## Decisions

### D1 · Ruta propia, y no un modo del panel existente

El panel de consulta libre es *una consulta → resultados*; el agente es *una conversación*. Y ese panel **ya tiene un conmutador** con otro significado —ruta degradada frente a generativa—: dos interruptores de nombre parecido en la misma pantalla es la clase de avería que C40 nació para arreglar.

| Alternativa | Por qué no |
|---|---|
| Colgarlo de la ficha de pieza | La ficha parte de una pieza elegida y el agente **no acepta pieza**: sería forzar el contrato |
| Un conmutador dentro del panel de consulta libre | Segundo interruptor de nombre parecido, y el cambio de comportamiento en el sitio **no se lee** en una demostración |

Y la ablación se demuestra mejor así: la misma pregunta hecha en los dos paneles es comparable a simple vista — la determinista contesta en una pasada, el agente enseña su escalera de llamadas.

### D2 · Versión de prompt propia para el agente, dejando la determinista intacta

La versión que sirve hoy a la ruta determinista **no contiene** la tarea del agente, y su cabecera declara que cada versión se conserva porque tiene cifras medidas contra ella. Editarla haría mentir esa declaración justo cuando otro change va a medirla.

| Alternativa | Coste | Cifras ya publicadas | Constantes deliberadamente separadas |
|---|---|---|---|
| Editar la versión determinista | 1 sección | **quedan ambiguas** | se respetan |
| Una versión nueva con **ambas** tareas | fichero entero | intactas | **se fusionan** |
| **Una versión nueva sólo para el agente** | *Sistema* duplicado | **intactas** | **se respetan** |

Se elige la tercera. Su riesgo real —que los dos *Sistema* deriven— **se convierte en un fallo de suite** con una comprobación de identidad, en vez de quedar como un desvío silencioso.

### D3 · La procedencia viaja como subclase, no como campo del modelo compartido

El modelo de grupo compartido es lo que publica la ruta determinista, y ensancharlo movería el esquema de esa ruta. El precedente exacto ya está sentado por el registro de consumo del agente, que se añadió como subclase por el mismo motivo. **Adición pura.**

### D4 · El circuito no cuenta la degradación que el servicio sirve con 200

Dos documentos del repositorio se contradicen: la deuda diferida pide contar el motivo de parada por fallo de proveedor, y el *pipeline* de la ruta hermana declara lo contrario —una degradación interna servida con 200 **no es un fallo**, porque el circuito protege de que el servicio no conteste—. Y hay un obstáculo mecánico: el cortafuegos recibe un resultado de transporte y **no ve el cuerpo**.

| Alternativa | Por qué no |
|---|---|
| Interceptor que lee el cuerpo | Exige bufferizar la respuesta, interpretar el JSON dos veces y acoplar el transporte al vocabulario cerrado del contrato |
| Circuito de dominio en el servicio de aplicación | Correcto en capas, pero **inalcanzable**: a una petición por minuto la ventana de muestreo expira antes de acumular el umbral |
| Contar todas las respuestas incompletas | Se abriría sobre una ruta que **funciona como está diseñada** |

**Decisión: no se cuenta**, se instrumenta como métrica, y quien avisa a la pantalla es la sonda — que ya existe, no gasta cupo y se lee en cada cambio de tienda. La deuda diferida se cierra **por refutación** y no por ejecución, con la aritmética escrita: con el tamaño de petición medido contra el techo de cuota, el sistema admite **una petición por minuto**.

El presupuesto de tiempo se fija **por encima del techo del bucle más el margen de red**, y no ajustado al máximo observado: el modo de fallo de apretarlo es cortar una petición que el servicio **ya pagó entera**.

### D5 · El hilo es el eje: cada turno es dueño de su bloque

La alternativa —un panel de resultados fijo que se refresca— se descarta por dos consecuencias concretas:

1. El operario sigue leyendo el argumentario de un turno mientras las filas de debajo ya son las del siguiente.
2. **Cuando el bucle pivota a sustitutos, la pieza que estaba mirando desaparece sin explicación** — y el pivote es justo lo que el agente existe para demostrar; se invocó 125 veces en la pasada medida.

### D6 · La transcripción se cuenta como se va a enviar

El tope total suma **todos** los turnos, incluidos los del asistente, y el argumentario mide del orden de 386 caracteres en la mediana. Con el argumentario reenviado, la conversación son **seis intercambios** y el tope de turnos muerde antes que el de caracteres.

| Alternativa | Profundidad | La referencia deíctica del turno siguiente | El cliente pone palabras en boca del asistente |
|---|---|---|---|
| **Argumentario íntegro** | **6 intercambios** | **funciona** | no |
| Resumen sintético siempre | ~9-10 | parcial | **sí** |
| Sólo turnos del operario | 12 | **no funciona** | no |

Se elige el primero, **con el segundo como respuesta al caso del argumentario retirado** —que ocurre en el 13,1 % de las peticiones y dejaría el turno sin texto—. El contrato lo autoriza explícitamente al declarar ese rol como atribuido y nunca fiable.

**Y el contador del compositor cuenta esa transcripción**, no lo que el operario teclea: un contador que sólo cuente lo tecleado llega a la mitad de su cuenta con el rechazo ya disparado, que es exactamente lo que el contador existe para evitar.

### D7 · La puerta se cierra antes de entrar; la respuesta incompleta se pinta dentro

Los dos modos degradados del agente no se conocen en el mismo momento: la falta de credencial **antes de gastar nada**, y la caída del proveedor **a mitad del bucle**, con herramientas ya ejecutadas y evidencia reunida. De ahí que uno cierre la puerta y el otro se pinte como respuesta cortada.

| Estado de la sonda | La tarjeta |
|---|---|
| Disponible | activa |
| No disponible | **deshabilitada con el motivo** |
| No contesta | **activa, con aviso** — fallar la sonda no puede cerrar una puerta que quizá funciona |

### D8 · El orden del frontal sale de las frecuencias medidas, no de la maqueta

| Estado del bloque | Frecuencia medida | Orden |
|---|---|---|
| Sin ninguna pieza | **19,6 %** | **primero** |
| Con filas y sus dos rótulos de procedencia | mayoría | segundo |
| Citas presentes | 7,8 % | dentro del bloque de prosa |
| Avisos presentes | 3,9 % | con su tabla de copy propia |
| Respuesta incompleta por presupuesto | **2,0 %** | **el último** |

### D9 · El ámbito se copia del panel hermano sin endurecerlo

Dos paneles hermanos con dos reglas de autorización distintas se rompen sin que falle ningún test. Se copia: abierto a los dos roles en el servidor, ofrecido **sólo al administrador** en el frontal, y la frontera que se protege es la fina —no se puede nombrar una tienda no asignada—.

**Pero la consecuencia se declara al seleccionarlo**: sin punto de venta la etiqueta de disponibilidad no puede valer «sin existencias», así que **el pivote no se dispara nunca**. No es estética: es una capacidad que se pierde, y la única persona que puede elegir ese ámbito es la única que no debería usarlo aquí.

> **Alternativa considerada:** que el panel del agente **no ofrezca** ámbito global. Coste cero y protege el comportamiento que el panel existe para demostrar. Se descarta por coherencia entre paneles hermanos, y queda declarada.

### D10 · Los instrumentos van antes de la medida

El arnés del agente **no cuenta marcadores** y **no registra la antigüedad de la proyección**. Lo segundo es lo que convierte «medimos sobre el sistema» en una afirmación comprobable, y su ausencia ya costó una vez: los dos caminos leen cosas distintas.

```
 ┌─ ARNÉS ────────────────────────────────┐   ┌─ CAMINO DE SERVICIO ────────────┐
 │ resuelve las piezas de referencia con  │   │ resuelve el ámbito consultando  │
 │ una consulta cruda a la proyección     │   │ el punto de control de sincronía│
 │ «leída sólo por la evaluación»         │   │ contra el techo de rancidez     │
 │ SIN comprobación de frescura           │   │ rancio → NO aplica el prefiltro │
 └────────────────────────────────────────┘   └─────────────────────────────────┘
        resuelve referencias perfectas                 sirve SIN ámbito
        por rancia que esté la proyección
```

La pasada de C32b duró más del doble del techo de rancidez sin drenaje automático disponible entonces, así que **parte de sus cifras de recuperación describen una recuperación sin ámbito** y no se pueden limpiar a posteriori. **La etiqueta de disponibilidad sí sobrevive**, porque se lee directamente y la antigüedad viaja con ella bajo la regla *degradar, nunca retirar* — y con ella sobrevive la cifra que sostiene D9.

### Flujo, de la tecla a la fila

```
operario   panel            .NET (aplicación)        jbg-ai              proveedor
   │         │                     │                    │                   │
   │ escribe │                     │                    │                   │
   │────────▶│ cuenta turnos y caracteres               │                   │
   │         │ de la transcripción a enviar             │                   │
   │ envía   │                     │                    │                   │
   │────────▶│────── transcripción completa ───────────▶│                   │
   │         │                     │ valida los 3 topes │                   │
   │         │                     │────────────────────▶ bucle: hasta 5 vueltas
   │         │                     │                    │──── tools ───────▶│
   │         │                     │                    │◀── evidencia ─────│
   │         │                     │                    │ genera el argumentario
   │         │                     │                    │ puerta numérica + citas
   │         │                     │◀─ grupos con procedencia, prosa, traza, parada
   │         │                     │ hidrata precio y existencias
   │         │                     │ (TODOS los miembros de TODOS los grupos)
   │         │◀── bloque de respuesta del turno ─────────┤                   │
   │◀────────│ lo ancla al hilo; colapsa el anterior     │                   │
```

**La autoridad no se mueve**: el servicio de IA decide qué recuperar y redacta; **el precio y las existencias los pone .NET**, por candidato y por tienda. La etiqueta cualitativa de disponibilidad del bucle gobierna **una sola cosa** —si pivota— y nunca llega al argumentario.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| **Saltarse los instrumentos** y tomar la pasada sin ellos reproduce el error ya cometido: cifras inauditables | Los instrumentos son el primer tramo, antes de cualquier tarea funcional, y la antigüedad queda **por fila** para que una fila degradada sea identificable y no se promedie |
| **La pasada exige entorno, no sólo código**: dura más que el techo de rancidez, y el drenaje vive en el ciclo de vida del servicio mientras el arnés es una herramienta de línea de comandos | Precondición explícita y comprobada en el informe de salud antes de arrancar |
| **Deriva entre los dos *Sistema*** de la versión determinista y la del agente | Comprobación de identidad en la suite |
| **Dos estados de la pantalla nunca observados**: ni la falta de credencial ni la caída del proveedor aparecieron en las 204 peticiones medidas | Se declara; se construyen contra escenarios y no contra observación |
| **El hilo puede crecer mucho**: hasta seis bloques, cada uno con filas y fotos | Sólo el último queda abierto; los anteriores colapsan a una línea con chips, y la fila colapsada tiene que ser barata |
| **El contrato se mueve** | Adición pura, verificada hoja a hoja, con el guardián del *snapshot* actualizado con su adición declarada — el mecanismo que el propio test describe para el siguiente change que lo mueva |
| **El agente cuesta tres veces la ruta determinista** y retira su argumentario seis veces más | **Por eso no se sirve por defecto**: como ruta propia y demostración de ablación, la misma cifra pasa de penalización a decisión justificada. Y la interfaz dice el coste **antes** de que se pulse |
| **La cuota por minuto, no el dinero, fija el ritmo**: una petición por minuto | Suficiente para un mostrador y un evaluador; **no** para dos mostradores simultáneos. Se declara, y es lo que hace inalcanzable un cortafuegos por umbral de muestra |
| **Cambiar de ámbito a mitad de conversación invalida la evidencia previa** | Reinicia el hilo, y la interfaz avisa antes |
| **El presupuesto de herramientas efectivo es seis y no ocho**, por la granularidad de la concurrencia | Se declara y no se recalibra aquí: recalibrar movería una constante de la que depende un invariante que la suite afirma |
