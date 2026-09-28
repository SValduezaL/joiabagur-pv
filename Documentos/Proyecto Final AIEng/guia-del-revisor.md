# Guía del revisor — cómo probar cada funcionalidad

Recorrido paso a paso por la demo, entrando como **administrador**. Cada apartado dice cómo llegar a la
pantalla, qué hacer y qué debe aparecer.

## Índice

0. [Introducción: qué ya existía y qué se ha añadido](#0-introducción-qué-ya-existía-y-qué-se-ha-añadido)
1. [Dashboard y tarjeta «Servicio de IA»](#1-dashboard-y-tarjeta-servicio-de-ia)
2. [Configuración → Modelo de IA (no es del Proyecto Final)](#2-configuración--modelo-de-ia-no-es-del-proyecto-final)
3. [Configuración → Revisión de familias](#3-configuración--revisión-de-familias)
4. [Configuración → Revisión de perfiles](#4-configuración--revisión-de-perfiles)
5. [Ventas → Buscar con Ayuda](#5-ventas--buscar-con-ayuda)
6. [Ventas → Buscar con Ayuda → Ver ficha de venta](#6-ventas--buscar-con-ayuda--ver-ficha-de-venta)
7. [Ventas → Preguntar al Agente](#7-ventas--preguntar-al-agente)
8. [Limitaciones que puedes encontrarte](#8-limitaciones-que-puedes-encontrarte)

---

## 0. Introducción: qué ya existía y qué se ha añadido

La aplicación es un sistema de gestión de puntos de venta para una joyería con varias tiendas. **Ese
sistema ya existía** antes del Proyecto Final. El Proyecto Final le añade una **capa de IA generativa**:
un sistema RAG sobre el catálogo y sobre el corpus comercial de la casa, y un agente de venta.

| Ya existía (MVP, fuera del Proyecto Final) | Añadido en el Proyecto Final (RAG + agente) |
|---|---|
| Catálogo, inventario por tienda, ventas, devoluciones, métodos de pago, usuarios, dashboards, escaneo de códigos, reconocimiento de imagen con TensorFlow.js | Servicio de IA en Python, búsqueda híbrida (semántica + texto), respuesta asistida con argumentario y fuentes citadas, salvaguardas, sustitutos, agente de venta, enriquecimiento del catálogo, familias de variantes, revisión humana, evaluación y despliegue en AWS |

**Acceso**

| | |
|---|---|
| URL | <https://52-49-209-14.sslip.io> |
| Usuario | `demo.admin` |
| Contraseña | `DemoAdmin123!` |

El administrador puede elegir **cualquier tienda** en todas las pantallas, así que no hace falta cambiar
de cuenta. Si quieres ver la aplicación como la ve un dependiente, las cuentas de operador están en el
[README, apartado 1.4.2](../../README.md#142-cuentas-de-la-demo).

**Tres avisos antes de empezar**

1. **Al entrar salta un aviso rojo, «Modelo de IA: Acción Requerida»**, con un texto en inglés. Es del
   reconocimiento de imagen del MVP, no del Proyecto Final (apartado 2). Ciérralo y sigue.
2. **La IA tiene límites de uso.**
   - Búsqueda rápida: 30 por minuto.
   - Respuesta asistida y ficha de venta: 10 por minuto.
   - Agente: 4 por minuto, y en la práctica **uno por minuto**, por la cuota de tokens del proveedor.

   Una respuesta asistida tarda unos segundos; el agente, unos 5 s y hasta 12 s. Si ves «Demasiadas
   búsquedas seguidas», espera un minuto.
3. **La primera consulta después de un rato sin uso puede ser lenta.** Si la primera búsqueda sale
   degradada, repítela.

---

## 1. Dashboard y tarjeta «Servicio de IA»

**Cómo llegar:** es la pantalla de inicio tras el login (menú **Dashboard**).

### Los datos de la demo

El dashboard no enseña contadores de catálogo, así que conviene saber de antemano con qué datos trabaja
la demo:

| Dato | Cantidad | Origen |
|---|---|---|
| Productos del catálogo | **1.200** | **436 reales** (export de la joyería, 28 colecciones) + **764 sintéticos** generados con LLM (10 colecciones nuevas) |
| Productos indexados para la IA | **1.167** | Se excluyen 32 que no son joyería (servicios de taller, velas, envíos…) y 1 perfil rechazado en la revisión humana |
| Puntos de venta | **12** (11 activos) | Sintéticos: tiendas urbanas, boutiques de costa, hoteles, aeropuerto, estación marítima y el taller. `HT-ARTRUTX` está cerrado a propósito |
| Filas de inventario | **6.720** | Simuladas, con surtidos deliberadamente distintos por tienda |
| Histórico de ventas | **22.961** ventas | Simuladas, del 2025-04-23 al 2026-08-23. El export real no traía ventas |

**Por qué hay productos sintéticos:**
- **Volumen suficiente** para que un índice vectorial y su evaluación tengan sentido.
- **Casos difíciles a propósito:** variantes que solo cambian de talla, descripciones escuetas o
  ausentes, y colecciones para las tiendas de hotel y aeropuerto.
- **Separación en las métricas:** cada producto lleva su origen, y las métricas se miden por separado
  sobre la parte real.

> Como el histórico simulado termina el 2026-08-23, las tarjetas de ventas del mes y algunos gráficos
> pueden salir vacíos. Esas tarjetas son del MVP y no afectan a nada de la IA.

### Qué es del MVP y qué es nuestro

- **Del MVP:** «Ventas hoy», «Ingresos del mes», «Devoluciones del mes», «Stock crítico», «Últimas
  ventas» y los gráficos.
- **Del Proyecto Final:** la tarjeta **«Servicio de IA»**, abajo del todo.

### Tarjeta «Servicio de IA»

Es el diagnóstico del servicio de IA, visible solo para administradores. El navegador no puede hablar
directamente con el servicio de IA, así que el backend .NET se lo pregunta y se lo sirve.

| Campo | Qué significa | Qué debería verse |
|---|---|---|
| **Base de datos** | Si el servicio de IA llega a su PostgreSQL con pgvector | «Accesible» |
| **Documentos indexados** | Productos que tiene el índice de búsqueda | **1.167** |
| **Proveedor de embeddings** | Si tiene la clave del proveedor de embeddings | «Credencial configurada» |
| **Disponibilidad por tienda** | La copia del surtido de cada tienda que usa el buscador. Se refresca sola al arrancar y cada 10 minutos | «Al día», con «Última sincronización: hace N minutos» |
| Tiendas sin surtido (línea roja) | Tiendas **abiertas** cuya búsqueda no funcionaría | No debe aparecer |
| Pie | Versión del servicio y modelo con el que se construyó el índice | `openai/text-embedding-3-small` |

**Una alerta que solo aparece cuando hay problema:** si el modelo de embeddings configurado no coincide
con el del índice, sale «Modelo de embeddings incompatible con el índice». Es el fallo más traicionero
posible, porque la búsqueda devuelve resultados sin sentido sin dar ningún error. Por eso tiene su
propia alerta.

---

## 2. Configuración → Modelo de IA (no es del Proyecto Final)

**Cómo llegar:** menú **Configuración → Modelo de IA**.

**Esta pantalla es del MVP anterior, no del Proyecto Final.** Gestiona el reconocimiento de productos
por foto con TensorFlow.js en el navegador.

Muestra «Acción Requerida» y «Sin modelo» porque **ningún producto de la demo tiene foto** (0 de 1.200),
así que no hay nada con lo que entrenar. **No pulses «Entrenar Modelo».** Es el mismo motivo del aviso
rojo que sale al entrar.

---

## 3. Configuración → Revisión de familias

**Cómo llegar:** menú **Configuración → Revisión de familias**.

### Por qué hubo que enriquecer el catálogo

El catálogo real no servía para una búsqueda semántica tal como venía:
- **Textos casi vacíos:** 38,5 caracteres de media entre nombre y descripción, y 51 productos sin
  descripción.
- **Atributos casi ausentes:** el texto decía la talla en el 15 % de los casos, la piedra en el 8 % y
  el color, el estilo o la ocasión prácticamente nunca.
- **Cada talla era un producto distinto:** el mismo colgante en S, M y L eran tres SKU sin relación
  entre sí. Al buscar, las tres tallas competían entre ellas y ocupaban toda la página.

Hubo dos respuestas: el **enriquecimiento de perfiles** con LLM (apartado 4) y las **familias de
variantes**. Un algoritmo determinista agrupó **486 productos en 156 familias** y una persona las
aprobó. Esta pantalla sirve para auditarlas.

### Qué ver en cada pestaña

La cabecera muestra cuántos pares se han juzgado y el tiempo medio por decisión, además de los atajos de
teclado (A aprobar, R rechazar, J/K moverse, Enter guardar).

| Pestaña | Qué contiene | Qué se puede hacer |
|---|---|---|
| **Familias (156)** | El catálogo de familias: origen («Aprobada por IA»), miembros, revisados y rechazados | Crear una familia a mano, editar las etiquetas de variante (lápiz) o disolver una familia (papelera) |
| **Marcados** | Miembros que el vector no respalda: un producto de otra familia se parece más a ellos que su propio hermano menos parecido | **Confirmar** o **Descartar** la pertenencia |
| **Huérfanos** | Productos sin familia que se parecen mucho a una | **Confirmar** o **Descartar** |
| **Aplicar** | Decisiones registradas que aún no se han aplicado al catálogo | **Aplicar** |
| **Incidencias** | Grupos que el algoritmo rechazó y productos excluidos por falta de tipo de pieza | Solo lectura: se arreglan en el catálogo |

Un veredicto **registra** lo que decides; la pestaña **Aplicar** es la que **mueve** la pertenencia.
Están separados a propósito. **Recalcular** vuelve a pedir la auditoría al servicio de IA.

Lo hecho hasta ahora: **64 pares producto–familia juzgados**, y las familias pasan de 486 a 492
miembros tras aplicar las decisiones. Detalle en los informes de
[propuesta de familias](informes/c18a-family-suggestion-report.md) y de
[revisión](informes/c18b-family-review-report.md).

---

## 4. Configuración → Revisión de perfiles

**Cómo llegar:** menú **Configuración → Revisión de perfiles**.

### Qué es un perfil de IA

Para cada producto, un LLM extrae del texto sus **atributos estructurados**: tipo de pieza, materiales,
piedra, talla, color, estilo y ocasión. Cada campo lleva su confianza y su procedencia («regla»,
«inferido», «ausente»). La búsqueda y la ficha de venta se apoyan en esos atributos, así que una persona
tiene que poder revisarlos.

**La pregunta que se hace al revisor** es si **el texto del producto respalda** cada valor, no si es
cierto de la pieza. No hay fotos, así que eso no se puede comprobar.

### Qué se puede hacer

| Pestaña | Qué contiene | Qué se puede hacer |
|---|---|---|
| **Cola** | Un lote **estratificado** de perfiles aprobados automáticamente que nadie ha mirado. Los estratos son A (sin evidencia), B (afirmado sin frase que lo respalde) y C (afirmado con frase) | Corregir un campo cambiando su valor **«En vigor»**, **«Aprobar y siguiente»**, **«Rechazar»**. Con un estrato elegido, **aprobación masiva** de un campo |
| **Rechazados** | Perfiles rechazados; casi todos son artículos de regalo, bien rechazados | **Devolver a aprobado** si alguno se rechazó por error |
| **Huecos de vocabulario** | Términos que el texto nombra y el vocabulario cerrado no tiene | Anotarlos y copiarlos como tabla (se guardan en tu navegador) |
| **Métricas** | Tiempos de revisión y **tasa de corrección**, por estrato y por campo | Solo lectura |

### Qué debe verse

- En la cabecera: **204 perfiles revisados con cronómetro**, con **32,1 s de media**.
- En **Métricas**: una **tasa de corrección ponderada del 20,9 %**. Por tipo de campo, las etiquetas
  comerciales (color, estilo, ocasión) se corrigen mucho más que los campos sensibles (tipo, material,
  piedra): 42,3 % frente a 10,4 %.
- La **Cola** sigue teniendo perfiles: son los que el enriquecimiento aprobó automáticamente y todavía
  nadie ha revisado. La revisión fue por muestreo estratificado, no exhaustiva.

Puedes revisar uno y ver cómo sube el contador; no rompe nada. Detalle en el
[informe de la revisión de perfiles](informes/c28-implementation-measurements.md).

---

## 5. Ventas → Buscar con Ayuda

**Cómo llegar:** menú **Ventas** → tarjeta **«Buscar con Ayuda»** (`/sales/new/assisted`).

Arriba aparece una **insignia de disponibilidad**, por ejemplo «Búsqueda inteligente y respuesta asistida
disponibles». Dice qué vías están encendidas **antes** de buscar, para no descubrirlo al usarlas.

### Búsqueda rápida frente a respuesta asistida

El selector **«¿Cómo quieres que te responda?»** ofrece dos vías:

| | **Búsqueda rápida** | **Respuesta asistida** |
|---|---|---|
| Qué hace | Búsqueda híbrida (semántica + texto en español) sobre el catálogo de la tienda | Lo mismo, más un clasificador de intención, agrupación por familia y un **argumentario** con fuentes citadas |
| Coste | Respuesta inmediata · 30 por minuto | Unos segundos · 10 por minuto (llama a un LLM) |
| Cuándo usarla | El cliente describe una pieza | El cliente plantea una necesidad («algo para regalar…») |

La elección **no se recuerda entre visitas**, a propósito: recordar la vía cara sería gastar sin que
nadie lo decida.

### Una tienda concreta frente a «Todas las tiendas»

El selector **«Punto de venta»** tiene una opción extra solo para administradores: **«Todas las
tiendas»**.

- **Con una tienda:** los resultados se limitan a lo que esa tienda lleva, con **su precio y sus
  existencias** leídos del inventario real. Lo agotado baja en la lista, pero no desaparece.
- **Con «Todas las tiendas»:** busca en todo el catálogo y **fuerza la respuesta asistida** (la rápida
  trabaja sobre una tienda concreta). Sin tienda no hay existencias que dar, así que cada fila dice
  «Selecciona una tienda para ver existencias» en lugar de un cero falso, y «Ver ficha de venta» queda
  desactivado.

### Filtros

Hay dos filtros: **Materiales** (Plata, Oro, Baño de oro, Perla…) y **Tipo de pieza** (Anillo,
Pendientes, Collar…).
- **Solo se aplican al pulsar Buscar**: cambiarlos no lanza la búsqueda.
- Si los filtros dejan fuera piezas que sí encajaban, la pantalla lo distingue de «no hay nada»: dice
  **«Hay piezas que encajan con tu descripción, pero ninguna pasa los filtros»**. Son dos situaciones
  con arreglos opuestos: quitar un filtro, o describirlo de otra forma.

### Ejemplos para probar

| # | Tienda | Vía | Escribe | Qué debe aparecer |
|---|---|---|---|---|
| 1 | CIU-CENTRE | Rápida | `gargantilla de plata` | Collares de plata, aunque el catálogo no usa nunca la palabra «gargantilla» (diccionario de sinónimos). Cada fila lleva su precio y «N en Ciutadella Centre», y una insignia con la vía que la encontró: «Coincidencia semántica» o «Búsqueda por texto» |
| 2 | CIU-CENTRE | Asistida | `algo para regalar a mi madre, que no sea muy llamativo` | Piezas **agrupadas por familia**, con «… también en: M, L» cuando hay más tallas, y un **Argumentario** con **«De dónde sale»** |
| 3 | CIU-CENTRE | Asistida | `qué tiempo hará mañana en Ciutadella` | Guardarraíl: **«Esto no es una pregunta de joyería»** |
| 4 | CIU-CENTRE | Asistida | `un salero de plata` | Guardarraíl distinto: **«No trabajamos ese tipo de pieza»**. Es platería, pero no está en el catálogo. Ante un cliente se dice de otra forma que el caso 3, y por eso son dos mensajes distintos |
| 5 | CIU-CENTRE | Asistida | `algo bonito` | Una **repregunta** («¿Qué tipo de pieza busca?…», «¿Para qué ocasión es?…»), elegida de un catálogo cerrado y no inventada por el modelo. El foco vuelve a la caja |
| 6 | CIU-CENTRE | Rápida | `aro pequeño` con filtros **Plata** + **Anillo** | «Hay piezas que encajan con tu descripción, pero ninguna pasa los filtros» |
| 7 | Todas las tiendas | (asistida, forzada) | `collares con motivos marinos` | Resultados de todo el catálogo, sin existencias y con la ficha desactivada |

Como administrador ves además un **embudo** desplegable bajo los resultados: candidatos, supervivientes
y mostrados; en la vía asistida, también el tiempo del proveedor, el propio, el modelo y los tokens.
Nunca un importe.

---

## 6. Ventas → Buscar con Ayuda → Ver ficha de venta

**Cómo llegar:** haz una búsqueda con una tienda elegida (por ejemplo el ejemplo 1 o 2 en CIU-CENTRE) y
pulsa **«Ver ficha de venta»** en un resultado. También se llega desde el agente, la venta manual y el
escaneo.

La ficha reúne lo que un dependiente puede contar de **esa** pieza, con el precio y las unidades de
**esa** tienda.

| Sección | Qué contiene |
|---|---|
| Cabecera | Nombre, talla, SKU, colección, materiales, **precio** y **«N en {tienda}»** |
| **A tener en cuenta** | Avisos derivados por reglas: «Esta pieza tiene otras variantes en esta tienda», «Quedan pocas unidades»… |
| **Argumentario** | Un texto de venta redactado por un LLM y **verificado sin otro LLM de juez**: cada cita debe existir, debe haber una frase del texto que la apoye y no puede aparecer ninguna cifra inventada. El precio y las unidades **no los escribe el modelo**: los rellena el backend con el inventario de la tienda |
| **De dónde sale (n)** | Las fuentes del argumentario, desplegables como «documento · sección» del corpus comercial (32 documentos, 161 fragmentos). Cada una lleva una insignia: **«Información general»** (un dato del mundo) o **«Compromiso de la casa»** (una política de la joyería, con el aviso «Conviene confirmarlo en tienda antes de trasladárselo a un cliente») |
| Variantes | Si la familia tiene varias tallas en la tienda: «Elige cuál le vendes. **Ninguna está seleccionada por defecto**». Hay un botón por talla, para que vender la talla equivocada exija elegirla a mano |

### «¿Te ha preguntado algo el cliente?»

Es la parte que más se apoya en el RAG de conocimiento. Ofrece cinco preguntas sugeridas («¿Se puede
mojar esta pieza?», «¿Va bien para una piel sensible?», «¿Cómo se limpia en casa?», «Es un regalo y no
sé la talla, ¿qué hago?», «¿Se puede llevar a la playa o a la piscina?») y una caja libre de hasta 500
caracteres.

- Al preguntar, el **Argumentario** se sustituye por una respuesta **sobre esa pieza**, citando el
  documento y la sección exactos de donde sale.
- Si el corpus no cubre la pregunta (prueba `¿puedo pagar con criptomonedas?`), no contesta de memoria:
  aparece **«La documentación no cubre esta pregunta»**.

### Estados que merece la pena distinguir

| Mensaje | Significado |
|---|---|
| «El asistente no está disponible» | La IA no ha respondido. Lo que ves viene del catálogo y es real, pero no hay argumentario |
| «El argumentario no se ha generado» | La IA respondió, pero sin texto. Los datos de la pieza están completos |
| **«Esta pieza está agotada aquí»** | No redacta argumentos de algo que no se puede vender hoy. En su lugar muestra **«Alternativas disponibles hoy»**, cada una con el motivo por el que aparece |

**Para ver el caso de pieza agotada:** abre directamente la ficha de `SKU1164` («Anillo Mar de Plata»)
en <https://52-49-209-14.sslip.io/sales/new/assist/1eeb708e-0e44-400b-91c7-54a9cd3f8f18>. Como llegas
sin tienda, la ficha te pide una: elige **FORNELLS** en el selector «Punto de venta».

---

## 7. Ventas → Preguntar al Agente

**Cómo llegar:** menú **Ventas** → tarjeta **«Preguntar al Agente»** (`/sales/new/agent`). Si el agente
estuviera apagado, la tarjeta saldría desactivada y diría por qué.

El agente es un bucle de *function calling* que **decide por sí mismo qué consultar**. Tiene seis
herramientas de solo lectura: buscar en el catálogo, proponer sustitutos, listar la familia de una
pieza, consultar la documentación de la casa, consultar la disponibilidad y pedir una aclaración.

### Qué hay en la pantalla

- **Ámbito**: la tienda sobre la que pregunta. Como administrador, puedes elegir también «Todas las
  tiendas».
- **Coste de la sesión**: preguntas, tokens y coste aproximado.
- Bajo la caja, los límites de la conversación: **«turnos n/12 · x/4.000 car.»**. La conversación entera
  viaja en cada petición, porque el servicio no guarda estado.
- **Un bloque por pregunta.** Los anteriores se pliegan a una línea, pero **cada pregunta conserva su
  respuesta**.
- En cada bloque:
  - una **franja de estado** con el motivo de parada y «N vueltas · M consultas»;
  - el argumentario y sus fuentes;
  - las piezas separadas en **«Coincidencias»** (lo que se pidió) y **«Alternativas»** (sustitutos);
  - **«Cómo lo ha averiguado»**, desplegable con la herramienta que usó en cada vuelta.

### Ejemplos para probar

**Espera alrededor de un minuto entre preguntas** por la cuota del proveedor.

| # | Ámbito | Escribe | Qué debe pasar |
|---|---|---|---|
| 1 | CIU-CENTRE | `busco un anillo de plata para un regalo` | Respuesta normal: **«Respuesta completa»**, piezas bajo «Coincidencias», argumentario con fuentes |
| 2 | CIU-CENTRE | `¿cómo se limpia la plata?` | Consulta la documentación: prosa y fuentes, sin piezas |
| 3 | CIU-CENTRE | `quiero algo bonito` | **«Falta un dato para poder buscar»**: el agente pide una aclaración en vez de enseñar piezas al azar |
| 4 | CIU-CENTRE | `busco un tractor de juguete para el nieto de un cliente` | **«Consulta fuera de lo que esta tienda atiende»**: rechazo cortés |
| 5 | CIU-CENTRE | `enséñame algo de titanio` | Rechazo por no estar en el catálogo: «Es joyería, pero este catálogo no la tiene» |
| 6 | **MAO-AIR** | `El cliente quiere la referencia SKU1127, ¿la tenemos?` | **Cambio de plan:** comprueba la disponibilidad, ve que está agotada y **busca sustitutos**. En «Cómo lo ha averiguado» aparece `buscar_sustitutos`, y las piezas salen bajo **«Alternativas»**, nunca bajo «Coincidencias» |
| 7 | MAO-AIR | La misma pieza nombrada **por su nombre** | No cambia de plan: limitación declarada (apartado 8) |
| 8 | Todas las tiendas | cualquiera de las anteriores | Aviso previo: sin tienda **no dirá existencias ni ofrecerá alternativas** |
| 9 | — | Cambia el ámbito a mitad de conversación | Pide confirmación: «Cambiar de tienda reinicia la conversación…» |

Para el ejemplo 6 en CIU-CENTRE, la referencia agotada allí es `SKU759`.

### Los diez motivos de parada

**Ninguno se pinta como una avería.** Pedir una aclaración o declinar son desenlaces normales de una
conversación, y lo encontrado antes de un corte sigue sirviendo para vender.

| Texto en pantalla | Cuándo ocurre |
|---|---|
| Respuesta completa | El agente terminó por sí mismo |
| Respuesta incompleta: se agotaron las vueltas de búsqueda | Tope de vueltas |
| Respuesta incompleta: se agotaron las consultas al catálogo | Tope de llamadas a herramientas |
| Respuesta incompleta: se agotó el presupuesto de texto | Tope de tokens |
| Respuesta incompleta: la conversación acumulada llegó a su tope | Tope de contexto |
| Respuesta incompleta: se agotó el tiempo de búsqueda | Tope de tiempo (15 s) |
| Falta un dato para poder buscar | Pidió una aclaración |
| Consulta fuera de lo que esta tienda atiende | El clasificador la rechazó antes de empezar |
| El agente no está configurado en este entorno | Falta la credencial del agente |
| El proveedor de IA falló a mitad de la búsqueda | Error del proveedor; se muestra lo reunido hasta entonces |

---

## 8. Limitaciones que puedes encontrarte

- **El agente solo cambia de plan si la pieza se nombra por su referencia.** La herramienta con la que
  busca no devuelve el nombre del producto, así que, si le das el nombre, no sabe cuál de los
  candidatos es la pieza. Es una limitación declarada, con su arreglo descrito. En el mostrador es
  realista: la pieza lleva la etiqueta delante.
- **Aviso del modelo de imagen:** es del MVP. La demo no tiene fotos (apartado 2).
- **La disponibilidad cambia con cada sincronización.** Si `SKU1127`, `SKU759` o `SKU1164` ya no están
  agotadas cuando pruebes, busca en la ficha de venta de cualquier pieza con «Sin existencias» en esa
  tienda. El comportamiento es el mismo.
- **La revisión humana de perfiles es un muestreo**, no una revisión exhaustiva: la Cola seguirá
  teniendo perfiles pendientes.

Lo que queda pendiente, con su vía de cierre, está en [DEFERRED_TASKS.md](../../openspec/DEFERRED_TASKS.md).
Las cifras que se citan aquí se justifican en el
[informe de cierre](informes/c39b-implementation-measurements.md).
