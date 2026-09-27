## Why

C34 dejó las dos rutas del card servidas, medidas y **sin ningún consumidor**. El argumentario con
precio y stock resueltos, las citas con su alcance, el agrupado por familia hidratado y los sustitutos
vendibles hoy existen desde el 22 de septiembre y **sólo se demuestran con `curl` y con el arnés de
evaluación**. Este change es la pantalla, y es **el único del Proyecto Final que pone la capa RAG
delante de una persona**: cierra la cadena crítica `C30a → C34 → C36` y es lo que el vídeo de entrega
tiene que mostrar.

La exploración del 2026-09-22 ([informe](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md))
contrastó la ficha con el árbol y **refutó tres de las cinco filas de copy que hereda de C31**: el
enrutador de intención corre sólo en el modo de consulta libre y las dos rutas de C34 son siempre
ancladas, así que `clarification_question` es constante nulo y los dos códigos de rechazo son
inalcanzables desde esta pantalla. Escribir su castellano daría dos pruebas verdes sobre caminos
imposibles. Y midió tres cifras que fijan el diseño: el bloque de familia dispara en el **31,2 %** de
las fichas y sus variantes se distinguen en el **98,3 %** de los grupos, el de sustitutos en el
**8,7 %**, y el aviso de falta de talla en el **58,3 %** — un aviso que está anticorrelacionado con
pertenecer a una familia (**4,0 %** frente a **92,5 %**) y que, por tanto, describe el estado del
enriquecimiento del catálogo y no la pieza que el cliente tiene delante.

## What Changes

- **Nueva pantalla de ficha de venta en ruta propia**, cargada de forma perezosa bajo el árbol de
  ventas, anclada a una pieza y a un punto de venta, con **tres entradas**: la fila de resultados de la
  búsqueda asistida, el producto elegido en la página de venta manual y la pieza resuelta tras
  escanear un código. La situación que motiva la caja de pregunta —*el cliente tiene la pieza en la
  mano*— llega por las dos últimas, no por el panel.
- **Una petición de asistencia por visita**, emitida al entrar, **sin reintento automático**, con
  guarda de respuestas fuera de orden y estado de carga explícito. La pregunta del cliente es una
  **segunda** petición explícita. El límite es de diez peticiones por minuto y usuario, y la respuesta
  del card no se puede cachear.
- **Bloque de desambiguación por familia** con una fila por variante, etiqueta de variante destacada,
  precio y unidades de esa tienda, **sin ninguna preselección** y con una acción de venta por miembro:
  el clic es la confirmación. Con un solo miembro vuelve la acción directa.
- **Traspaso a la venta** del miembro elegido por estado de navegación, el mecanismo que las otras
  tres entradas de venta ya usan.
- **Los seis estados del argumentario pintados como cinco mensajes**, conservando la distinción entre
  una IA no disponible —donde media pantalla es catálogo puro— y un argumentario que no se generó.
  Los tres estados retenidos terminan en una acción, no en un punto.
- **Citas desplegables** con documento, sección y fragmento, **distinguiendo el alcance de la
  afirmación**: un compromiso de la casa no se presenta como un hecho del mundo. No se resuelven a
  enlaces y se ocultan cuando el argumentario no se entrega.
- **Caja de pregunta** con preguntas sugeridas derivadas del corpus que rellenan y envían en un solo
  acto, límite de quinientos caracteres comprobado en el cliente, y la pregunta **siempre en el cuerpo
  de la petición**, nunca en la dirección de la página ni en el estado del enrutador.
- **Bloque de avisos** con los **cinco códigos alcanzables** traducidos al castellano y **etiqueta
  neutra** para cualquier otro, porque el vocabulario es cerrado pero versionado. La falta de talla se
  degrada a **atributo de la pieza** junto al SKU, no a alerta, para que no canibalice los dos avisos
  de stock.
- **Bloque de sustitutos** disparado por la pieza anclada sin existencias, no pedido cuando la IA no
  está disponible, con los **cuatro desenlaces distinguibles** y la regla de página corta declarada.
- **Tabla de copy en un módulo propio**, exportada y probada directamente, con el patrón que la fila de
  resultados de la búsqueda asistida ya estableció.

Sin cambios de ruptura: ruta nueva, `backend/` y `ai-service/` intactos, contrato de `jbg-ai`
**idéntico byte a byte**, sin migración, y la selección para venta del panel de búsqueda asistida sin
cambiar de comportamiento ni de firma.

## Capabilities

### New Capabilities
- `sales-assist-card`: la ficha de venta del frontend — ruta propia anclada a una pieza y a un punto de
  venta con tres entradas y ámbito de respaldo por rol, una petición por visita sin reintento
  automático, traducción del vocabulario cerrado de avisos con etiqueta neutra para lo desconocido, la
  falta de talla como atributo y no como alerta, confirmación explícita de variante sin preselección,
  los seis estados del argumentario reducidos a cinco mensajes sin perder la procedencia de lo que se
  enseña, citas con su alcance distinguido y ocultas cuando el argumentario se retira, la pregunta del
  cliente acotada y fuera de la dirección de la página, y los cuatro desenlaces de sustitutos
  distinguibles con la página corta declarada.

### Modified Capabilities
- `assisted-search-panel`: la fila de resultados gana una **acción secundaria** hacia la ficha de venta
  que **no sustituye ni bloquea** la selección para venta, no consume el evento de selección de la
  telemetría de búsqueda y conserva intacta la firma de la selección. El resto del panel —una búsqueda
  sólo cuando el operario la pide, filtros rápidos, ámbito por rol, orden recibido, explicación por
  resultado, los cuatro vacíos, el embudo de administrador y el episodio por visita— no cambia.

## Impact

- **Frontend `React`** — página y ruta nuevas con carga perezosa; componentes de la ficha (cabecera de
  la pieza, avisos, argumentario con citas, familia, caja de pregunta, sustitutos); servicio con
  desenlaces tipados que nunca lanzan; tipos fieles a los objetos de transferencia del backend; módulo
  de copy; modificación mínima de la fila de resultados, de la página de venta manual y de la de
  escaneo; pruebas con Vitest y React Testing Library, con los servicios sustituidos por dobles y los
  proveedores de contexto envueltos.
- **Sin componentes de interfaz nuevos**: la plantilla ya trae todos los que hacen falta.
- **Sin cambios** en `backend/`, en `ai-service/` (el contrato no se mueve), en `terraform/`, en el
  carrito ni en la confirmación de venta: **no se abre migración**.
- **No bloquea a nadie**: C38 depende de C34 y no de esta pantalla, así que los dos pueden avanzar en
  paralelo. **No se ejecuta a la vez que C16**, con el que comparte página y servicio.
- **Reescribe la limitación 12** del §15 del diseño —dos de los tres modos de asistencia llegan al
  operario; la consulta libre sin pieza sigue sin pantalla— y **conserva íntegra la 13**: el rechazo
  cortés del enrutador no tiene superficie, así que la distinción entre *«el catálogo no puede
  contestar esto»* y *«esto no es una pregunta de joyería»* sólo se demuestra en el arnés.
- **Añade una limitación nueva**: la ficha **no tiene telemetría**. Ninguna de las tres cosas que
  decide —abrir, preguntar, elegir variante— deja rastro, así que su uso no es medible.
- **Abre dos tareas diferidas**: servir la parte estructural de la ficha sin pagar una generación, y la
  telemetría anterior. **Agrava una existente**: sin el corpus de conocimiento cargado en el entorno,
  la caja de pregunta responde siempre que la documentación no cubre la pregunta.
