## Why

De los cinco pilares que el Proyecto Final nombra —CAG, RAG, **agentes**, evaluación y despliegue—, el del agente es **el único sin superficie de operario**: `POST /v1/assist/agent` está entregado, probado y medido con proveedor real desde C32b, y no lo llama nadie —el cliente de la pasarela tiene siete operaciones y ninguna es la suya—, así que el pilar no puede aparecer ni en la URL pública ni en el vídeo de la entrega.

Y de camino se cierra un defecto de generación que C40 introdujo sin tocar el agente: la tarea del agente vive en un prompt cuyo *Sistema* ordena escribir marcadores de precio y existencias **siempre**, su payload no está anclado —correctamente, porque el argumentario habla de varias piezas— y C40 convirtió ese marcador en violación dura. Los tres eslabones son correctos por separado y juntos hacen que un argumentario que obedezca a su propio prompt se retire.

## What Changes

- **El agente llega al operario**: ruta propia bajo el árbol de ventas, cuarta tarjeta en la página de entrada de venta, y un **hilo de conversación donde cada turno del asistente es dueño de su bloque de respuesta**, con su argumentario, sus citas, sus grupos, su traza y su estado de parada. Sólo el último bloque queda abierto.
- **La procedencia de cada grupo viaja en la respuesta** del agente, de modo que la pantalla pueda rotular lo que se pedía frente a lo que se ofrece en su lugar. Hoy esa distinción existe en el payload que ve el modelo y **no** en la respuesta que recibe el consumidor.
- **La tarea del agente pasa a una versión de prompt propia** que prohíbe los marcadores cuando no hay pieza anclada. La versión que sirve a la ruta determinista **no se toca**, porque tiene cifras medidas contra ella y otro change las va a usar.
- **La ruta del agente acepta un token con y sin punto de venta**, como ya hace la ruta determinista desde C40. Las demás rutas de una sola tienda siguen rechazando la omisión.
- **Nace el consumidor .NET que falta**: operación en el cliente de la pasarela sobre un **cliente con nombre propio y presupuesto propio**, un circuito que **no** cuenta como fallo una degradación servida con 200, el transporte de los cinco campos que el agente añade a la respuesta determinista, la hidratación autoritativa de todos los miembros de todos los grupos y la **validación de los tres topes de la transcripción antes de llamar**.
- **La sonda de disponibilidad gana el interruptor del agente**, porque el agente tiene cadena de credencial propia y sin él la pantalla afirmaría que está encendido lo que vuelve degradado en cada petición.
- **La venta originada en el agente se registra con un origen propio**, para que la comparación de las dos rutas sea una consulta a la base y no una demostración en pantalla.
- **El arnés de evaluación del agente gana dos instrumentos** que hoy no tiene y sin los cuales las cifras que este change debe publicar no se pueden tomar ni auditar: el recuento de marcadores por generación y **la antigüedad de la proyección de punto de venta, por pasada y por fila**.
- **No BREAKING.** El contrato del servicio de IA se mueve por **adición pura** —un campo nuevo en el grupo de la respuesta del agente— y un consumidor que lo ignore recibe exactamente la respuesta que recibía.

## Capabilities

### New Capabilities

- `ai-agent-assist`: la ruta .NET del agente de venta — su endpoint y su autorización por rol y punto de venta, el transporte de los cinco campos propios del agente y de la procedencia de cada grupo, la hidratación autoritativa de precio y existencias sobre todos los miembros, la validación de los tres topes de la transcripción antes de gastar una llamada, la degradación que nunca es un 5xx y el origen de búsqueda propio con que se registra una venta nacida en el agente.
- `sales-agent-panel`: el panel del agente en el frontal — la ruta propia y la cuarta forma de empezar una venta, la puerta leída antes de entrar con sus tres estados, el hilo como eje con un bloque de respuesta por turno, el compositor que cuenta la transcripción que se va a enviar y no lo que se teclea, el ámbito fijo durante la conversación, la traza de llamadas como única prueba de que hay un agente, el castellano de los diez motivos de parada y las maneras de responder sin ninguna pieza sin que parezcan un vacío.

### Modified Capabilities

- `sales-assistant-agent`: el grupo de la respuesta declara su procedencia; la ruta acepta un token sin punto de venta; y el arnés de la capability registra el recuento de marcadores y la antigüedad de la proyección con que corrió cada fila.
- `assist-generation`: la tarea de evidencia del agente se sirve con una versión de prompt propia que prohíbe los marcadores de precio y existencias, y la versión que sirve a la ruta determinista queda intacta.
- `ai-gateway-client`: el cliente expone la operación del agente sobre un cliente con nombre y presupuesto propios, con un circuito que cuenta condiciones de transporte y **no** una degradación que el servicio sirve con 200.
- `ai-free-query-search`: la sonda de disponibilidad, que hoy informa de dos caminos, informa de tres.
- `ai-service-auth`: la lista de rutas que aceptan un token sin reclamación de punto de venta gana la del agente, sin que la ausencia deje de significar «no apliques el prefiltro» y sin que ninguna otra ruta de una sola tienda deje de rechazarla.

## Impact

- **`ai-service/`** — esquemas y router de asistencia, el bucle del agente, las constantes de versión de prompt, un fichero de prompt nuevo, el arnés del agente y el *snapshot* del contrato, que se regenera con sus adiciones declaradas.
- **`backend/`** — el enumerado de origen de búsqueda en el dominio; el cliente de la pasarela, su registro de clientes con nombre, sus opciones de configuración, los DTO y el servicio de aplicación del agente en la capa de aplicación; el endpoint y la sonda en la capa de API; y sus pruebas.
- **`frontend/`** — una página nueva bajo el árbol de ventas, la página de entrada de venta, el enrutado, los componentes propios del panel —bloque de respuesta, traza, compositor—, los tipos y el servicio. **La fila de resultado de C40 y el bloque de prosa de C36 se consumen y no se modifican**; el bloque de sustitutos de C36 no es reutilizable, porque se alimenta de señales que llegan por otro endpoint.
- **Contrato** — `ai-service/openapi.json` se mueve por adición pura; el guardián del *snapshot* se actualiza con la adición declarada, como hizo el change anterior que lo movió.
- **Datos** — **ninguna migración**, ni de EF Core ni de Alembic. El origen de búsqueda se persiste como entero por conversión, así que un valor nuevo no abre migración; y la consulta de ámbito global sigue sin registrarse, limitación heredada y declarada.
- **Entorno** — la pasada de medición **exige el drenaje programado de la proyección encendido y el servicio de IA levantado**: dura más que el techo de rancidez, y el drenaje vive en el ciclo de vida del servicio mientras el arnés es una herramienta de línea de comandos que no drena nada.
- **Coste y ritmo** — la cuota de tokens por minuto, y no el dinero, fija el ritmo: una petición por minuto. Eso es lo que hace inalcanzable un cortafuegos por umbral de muestra y lo que obliga a que la pantalla diga el coste antes de que se pulse.
- **Orden** — este change **va antes** del de evaluación de generación y agentes: sube la versión del prompt del agente, así que unas cifras tomadas antes describirían un prompt sustituido.
