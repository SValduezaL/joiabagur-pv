## Context

C34 dejó `POST /api/ai/products/{productId}/sales-assist` y
`GET /api/ai/products/{productId}/substitutes` servidas, medidas y **sin consumidor**. Todo lo que el
frontend necesita llega ya resuelto: el argumentario con el precio y las unidades reales sustituidos,
las citas con su alcance, el grupo de la familia hidratado contra el inventario de esa tienda, los
avisos ajustados a lo que la tienda lleva y los sustitutos filtrados a lo vendible hoy. **Ningún campo
hay que negociar y ningún número hay que calcular aquí.**

Lo que sí hay que decidir es **cómo se presenta sin mentir**, y ése es todo el trabajo de este change:
seis estados del argumentario, siete códigos de aviso de los que sólo cinco pueden llegar, cuatro
desenlaces de sustitutos, una degradación que cambia la procedencia de media pantalla, y un grupo de
familia cuya elección es una decisión de venta irreversible.

**Restricciones que gobiernan el diseño**, todas verificadas sobre el árbol en `4552bcf`:

| Restricción | Origen |
|---|---|
| **10 peticiones por minuto y usuario** en la ruta generativa | `AiSalesAssistOptions.RateLimitPermitLimit` |
| **La respuesta del card no se puede cachear** | spec viva `ai-sales-assist` |
| Latencia **p50 4,42 s · p95 7,13 s** (1,3 a 3,8 s en la demo) | informe de implementación de C34, §4 |
| La pregunta va **en el cuerpo**, máximo **500 caracteres** | `SalesAssistRequestValidator` y el contrato congelado |
| El vocabulario de avisos es **cerrado pero versionado** | `assist/constants.py` y `SalesAssistService` |
| Una búsqueda **sólo cuando el operario la pide** | spec viva `assisted-search-panel` |
| **No se pinta lo que el sistema no ha afirmado** | spec viva `assisted-search-panel` |
| La suite de frontend **viene roja**: 113 de 595 | `Documentos/testing-frontend.md` |

**Y una que la exploración descubrió:** los datos baratos del card —grupo, avisos, existencias— y los
caros —argumentario y citas— **llegan soldados en la misma respuesta**. No existe ninguna ruta que
devuelva la familia que una tienda lleva a partir de un `productId`: `GET /api/product-families/{id}`
está indexada por familia, el objeto de transferencia de producto no lleva el identificador de familia
y la ruta no devuelve cantidades por punto de venta. Servir la parte estructural cuesta, hoy, una
generación entera.

## Goals / Non-Goals

**Goals:**

- Que el operario vea, sobre la pieza que tiene delante, el argumentario con cifras reales, las
  variantes que su tienda lleva, la respuesta a la pregunta del cliente con su procedencia, y
  alternativas vendibles cuando la pieza está agotada.
- Que **ningún estado del sistema se pinte como otro**: una IA caída, un argumentario no generado, uno
  retirado y una pieza agotada dicen cosas distintas y se leen distintas.
- Que la elección de variante sea **estructuralmente explícita**, no un clic de confirmación sobre algo
  ya preseleccionado.
- Que el coste quede acotado: una petición por visita, ninguna automática de más, ningún reintento.
- Que un valor desconocido del backend **degrade la fila y no rompa la pantalla**.

**Non-Goals:**

- La consulta libre sin pieza y su pantalla; el rechazo cortés del enrutador; la ruta del agente.
- Cualquier cambio en `backend/` o en `ai-service/`, incluido el campo que distinguiría una pieza no
  indexada de una caída.
- Telemetría de la ficha: no se crea tabla ni evento.
- Emisión en continuo del argumentario.
- Complementarios: su bloque salió con el corte de C27.
- Componentes de interfaz nuevos: la plantilla ya trae todos los necesarios.

## Decisions

Las cuatro marcadas **(cerrada)** se tomaron con el desarrollador en la exploración. Las alternativas
descartadas de cada una están en el
[informe](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md).

### D1. Cinco códigos alcanzables, y ninguna copia muerta (D-A, cerrada)

`classify_query` corre **sólo en el modo de consulta libre**
([`orchestrator.py:270-280`](../../../../ai-service/src/jbg_ai/assist/orchestrator.py#L270-L280)) y las
dos rutas de C34 son siempre ancladas. Por tanto `clarificationQuestion` es **constante nulo** y
`query_out_of_domain` y `query_not_in_catalogue` **no pueden llegar a esta pantalla**.

El card traduce los **cinco** códigos que sí llegan y deja los dos restantes a la regla de etiqueta
neutra, **con una prueba que lo comprueba**. Eso convierte dos cadenas muertas en una prueba viva de la
tolerancia que la ficha exigía, y deja el vocabulario preparado para el día en que exista la consulta
libre sin fingir que ya existe.

`clarificationQuestion` se lee del contrato y se pinta si alguna vez llega, sin bloque propio ni copia:
es un campo del objeto de transferencia, no una funcionalidad.

| Alternativa | Descartada porque |
|---|---|
| Escribir las dos filas «por si acaso» | Dos pruebas verdes sobre caminos imposibles, que es la firma que el proyecto persigue desde C17 |
| Exponer la consulta libre aquí | Rompe la zona del change y arrastra el problema por el que C34 la excluyó: sus marcadores no dicen de qué pieza son |

### D2. Ruta propia con tres entradas (D-B, cerrada)

`/sales/new/assist/:productId`, con carga perezosa, bajo el árbol de ventas y con la misma protección
que el resto. El punto de venta llega por **estado de navegación**; abierta en frío, la página ofrece
el **mismo selector por rol** que el panel de búsqueda asistida y **no emite ninguna petición** hasta
que hay uno elegido (Q-6 del ticket).

Tres entradas: la fila de resultados del panel, el producto elegido en la página de venta manual y la
pieza resuelta tras escanear. La razón no es de comodidad: la situación que la ficha nombra —*el
cliente tiene la pieza en la mano y pregunta*— **llega por las dos últimas**, y un card confinado a la
fila dejaría al corpus de conocimiento sin ninguna ruta hasta el joyero, que es justo el hueco que la
caja de pregunta existía para cerrar.

La fila del panel **se extiende con un botón y no se reescribe**, que es lo que su propia documentación
interna pedía.

| Alternativa | Descartada porque |
|---|---|
| Desplegable dentro de la fila | Deja escaneo y búsqueda por SKU sin acceso al corpus; mete cuatro bloques y prosa larga en un elemento de lista; y diez filas con un botón invitan a agotar el límite del minuto |
| Panel lateral sobre la página actual | En móvil, cuatro bloques y prosa larga son incómodos, y elegir variante y vender sale a doble salto |
| Panel en línea en la página de venta manual | Esa página ya es larga y es la caja; el panel de búsqueda necesitaría su propia copia igualmente |

### D3. Navegar al card es el acto explícito (D-C, cerrada)

**Una petición de asistencia por visita**, emitida al entrar. Pulsar «Ver ficha de venta» **es** el acto
explícito que la spec viva del panel exige para una llamada cara; aquí se aplica a una diez veces más
cara. La pregunta del cliente es una **segunda** petición explícita. Máximo típico por visita: dos de
las diez del minuto.

**Ningún reintento automático.** Sobre una ruta de p95 7,1 s y diez por minuto, un reintento duplica
coste y espera. El reintento lo pide el operario con un botón.

Volver atrás y entrar de nuevo **es otra visita y vuelve a pagar**. Se dice en la spec en vez de
ocultarse con una caché que la spec de C34 prohíbe. La pregunta **no se conserva** entre visitas
(Q-4): conservarla invita a reenviarla sin querer y cada reenvío es una llamada de pago.

Se copian del panel las dos guardas que ya están probadas allí: **episodio por visita** —un
identificador en una referencia inicializada de forma perezosa, no en cada renderizado— y **guarda de
orden**, para que una respuesta obsoleta nunca sobrescriba a una más nueva.

| Alternativa | Descartada porque |
|---|---|
| Ficha vacía con botón «Preparar» | Aplica la regla del panel al pie de la letra, pero abre medio vacía y lo que hay que pedir dos veces no se usa |
| Pedir a .NET servir la ficha sin generar | Arquitectónicamente correcto y **no descartado: diferido**. Rompe la zona del change y reabre un change recién archivado |

### D4. La tabla de copia vive en un módulo propio (D-D)

Funciones exportadas y probadas **directamente**, con el patrón que la fila de resultados del panel ya
estableció, no literales dispersos por los componentes. Cubre los cinco códigos con su etiqueta neutra,
los cinco mensajes de estado del argumentario y los cuatro desenlaces de sustitutos.

La etiqueta neutra no es cortesía: el vocabulario es cerrado **pero versionado**, y es lo único que
impide que una versión nueva del servicio rompa una fila de la pantalla. La spec viva del panel ya
obliga a esa regla para las razones de coincidencia del recuperador.

### D5. La falta de talla es un atributo, no una alerta (D-E, cerrada)

Se pinta **siempre** —no se suprime nada que el backend haya emitido— pero **como línea neutra junto al
SKU**, nunca dentro del bloque de avisos.

La justificación va escrita en la spec con su cifra: salta en el **58,3 %** de las fichas, y está
anticorrelacionada con pertenecer a una familia —**4,0 %** con ella contra **92,5 %** sin ella—. Es
casi un sinónimo de *«esta pieza no entró en ninguna familia con tallas»*: describe el estado del
enriquecimiento, no la pieza. Un aviso que salta en seis de cada diez pantallas canibaliza a *stock
crítico*, que salta en el 3,9 % y sí puede costar una venta. El propio orquestador del servicio de IA
rechazó un cálculo de este mismo aviso por esta misma razón.

| Alternativa | Descartada porque |
|---|---|
| Pintarlo como los otros cuatro | Fatiga de avisos en el 58 % de las fichas; al tercero no se lee ninguno |
| No pintarlo sin familia | El frontend estaría **suprimiendo** un código que el backend emitió, que es lo que la spec del panel prohíbe hacer con las razones de coincidencia |

### D6. Una acción de venta por miembro, sin preselección (D-F)

Con **dos o más miembros**, el card no preselecciona ninguno y **no ofrece ninguna acción de venta que
no nombre a un miembro concreto**: una fila por variante con su etiqueta destacada, su precio, sus
unidades en esa tienda y su propio botón. El clic **es** la confirmación. Con un solo miembro vuelve la
acción directa, y el aviso de variantes ya no llega —C34 lo retira al hidratar.

La garantía se cierra **en el card y no en la caja**: el traspaso lleva ya un identificador de producto
concreto, y confirmar otra vez en la página de venta obligaría a la caja a conocer familias sin añadir
garantía.

**Dos mediciones sostienen la forma.** El bloque cabe: **el 99,6 %** de los 544 grupos tiene entre dos
y cuatro miembros y el máximo real es seis; el tope de ocho del registro de familia no sobrevive nunca
a la hidratación de una tienda. Y las variantes se distinguen: **el 98,3 %** de los grupos trae todas
las etiquetas presentes y distintas, **cero** con todas nulas y **cero** con duplicados. El 1,7 %
restante son grupos mixtos, y para ellos la fila **degrada al SKU** en lugar de dejar el hueco.

| Alternativa | Descartada porque |
|---|---|
| Ancla preseleccionada más diálogo | Preseleccionar y confirmar es el patrón que se pulsa sin leer |
| Nada preseleccionado y un botón único inhabilitado | Añade un paso y un estado para la misma garantía que una fila con su botón da sin ninguno |

### D7. Seis estados, cinco mensajes (D-G)

| estado | ¿el resto de la ficha es real? | mensaje |
|---|---|---|
| generado | sí | se pinta el argumentario |
| IA no disponible | **no**: sin citas, sin razones de coincidencia, familia del catálogo transaccional | «El asistente no está disponible. Lo que ves viene del catálogo.» |
| no generado | **sí, íntegro** | «Los datos de la pieza son los del índice; el argumentario no se ha generado.» |
| retirado por el servicio · retirado por marcador | sí | «No he podido redactar algo que pueda sostener con los datos de esta pieza.» + acción |
| retirado por falta de existencias | sí | «Esta pieza está agotada aquí. Te propongo alternativas.» |

**Los dos primeros no se funden**, aunque para el operario suenen parecido: en el degradado media
pantalla es catálogo puro y en el otro no. Fundirlos haría que la ficha mintiera sobre **de dónde salen
los materiales y las razones de coincidencia** que enseña. **Los dos retirados sí comparten texto** —el
operario no puede hacer nada distinto— pero se conservan distinguibles en el árbol del documento para
que una prueba los separe.

Los tres retenidos **terminan en una acción y no en un punto**: es lo que separa una abstención honesta
de un fallo, y es lo que el apunte de producción pide de un sistema que sabe decir que no sabe.

### D8. Citas verificables por lectura, no por enlace (D-H)

Plegadas por defecto, con título de documento, título de sección y fragmento. **El alcance de la
afirmación se distingue visualmente y con palabras**: un compromiso de la casa —25 de los 161
fragmentos del corpus— lleva insignia propia y la frase de confirmarlo en tienda antes de trasladarlo a
un cliente, que es lo que la propia ficha de material dice de sí misma.

**No se resuelven a enlaces**: la spec de C34 lo prohíbe y no existe ninguna ruta que lea el corpus, que
vive como ficheros en el repositorio del servicio de IA. De las tres propiedades que pide el apunte de
citación —resolver, localizar y ser trazable con un clic— se entregan **dos**, y la tercera se declara
como limitación con la salida que el propio apunte concede.

**Se ocultan cuando el argumentario no se entrega.** Enseñar fuentes de un texto que el operario no
puede leer es decorar; y además serían sólo las que ese argumentario usó, no las que fundamentaron la
respuesta.

### D9. Sustitutos: disparador, cuatro desenlaces y página corta (D-I)

El disparador es **la ausencia de existencias en el miembro anclado**, no el estado del argumentario:
el primero está presente en **todos** los estados servidos, el segundo sólo cuando no hubo pregunta.

Se piden **automáticamente** —no llaman a ningún modelo y es exactamente el momento en que hacen
falta—, **salvo si la IA no estaba disponible para esta ficha**: entonces la llamada devolvería «no
disponible» con certeza, así que no se gasta y se explica.

Los cuatro desenlaces, cuatro textos. Una pieza que el servicio no puede procesar se pinta como *«esta
pieza aún no está preparada»* y **nunca** como una caída. Y la página corta se **declara**, no se
rellena: si sobreviven tres, se dice que hay tres.

### D10. La caja de pregunta, con lo que se puede preguntar horneado (D-J)

Campo de texto con **cinco preguntas sugeridas** derivadas de las situaciones de mostrador que el
corpus cubre —mojar la pieza, piel sensible, limpieza en casa, regalo sin saber la talla, playa o
piscina (Q-3)—, que rellenan y envían en un solo acto, con el patrón de las consultas de ejemplo del
panel. **500 caracteres** comprobados antes de enviar.

La pregunta viaja **en el cuerpo** y **no se escribe en la dirección de la página ni en el estado del
enrutador**, que acaba en el historial del navegador. C34 lo prohíbe en el servidor; aquí se prohíbe en
el cliente.

Hornear las sugerencias no es sólo usabilidad: **9 de 40 preguntas reales de mostrador cayeron en «la
documentación no cubre esta pregunta»**, y enseñar lo que el corpus sí responde sube esa cobertura.

### D11. El servicio: desenlaces tipados que nunca lanzan

Calcado del servicio del panel: cada fallo se traduce a un miembro de una unión discriminada y **nada
se propaga como excepción**, para que la pantalla diga algo verdadero en lugar de mostrar un error de
aplicación.

Dos miembros propios que el panel no necesitaba:

- **429**, que el panel ya separa, y que aquí sigue siendo obligatorio: exceder el presupuesto no es
  una caída y el mensaje es distinto.
- **404**, que aquí significa **«esta tienda no lleva esta pieza»** —C34 lo responde antes de llamar a
  la IA— y merece su propia frase.

### D12. Lo que la ficha **no** puede decir

Con la IA no disponible, el cuerpo de la respuesta de C34 **no distingue** una pieza que el servicio no
puede procesar de una caída del servicio: los dos dan la misma bandera y el mismo estado, y sólo el
registro del backend los separa (Q-8, limitación 3 de C34). La ficha dice «no disponible», que es lo
más preciso que el contrato permite, y se declara. Añadir el campo es trabajo de backend y C34 dejó
escrito que no rompe nada.

### Flujo de la ficha

```text
  entrada (fila · página de venta · escaneo)
        │  estado: { pointOfSaleId }
        ▼
  /sales/new/assist/:productId   ── en frío → selector por rol, sin pedir nada
        │
        │  episodio por visita · guarda de orden · sin reintento
        ▼
  POST .../sales-assist { pointOfSaleId }        ── 429 ≠ caída · 404 = no la lleva
        │
        ├─ cabecera: nombre · SKU · «Sin talla declarada» (atributo)
        ├─ avisos: 4 códigos + etiqueta neutra
        ├─ argumentario: 6 estados → 5 mensajes
        │     └─ citas ▸ alcance distinguido · ocultas si no está generado
        ├─ familia (≥2 miembros): una fila y un botón por variante, sin preselección
        │     └─ [Vender esta] ──▶ /sales/new  { productId }
        ├─ caja de pregunta (500) + 5 sugeridas
        │     └─ POST .../sales-assist { pointOfSaleId, question }   (2ª llamada)
        └─ ancla sin existencias ∧ IA disponible
              └─ GET .../substitutes { pointOfSaleId }
                    ok · ninguno con existencias · pieza no preparada · IA no disponible
```

## Risks / Trade-offs

- **La suite de frontend viene roja** (113 de 595, medidos el 13 sep) y la ficha arrastra proveedores
  de contexto, que es la causa de un tercio de esos fallos → línea base **por nombres** antes de tocar
  nada, y la plantilla de pruebas del carrito como modelo.
- **El intermediario de peticiones no falla una llamada sin manejador**: una prueba puede pasar **sin
  haber afirmado nada** → los servicios se sustituyen con dobles del módulo, no con manejadores de red.
- **La comprobación de tipos no es una puerta**: arrastra decenas de errores previos de la plantilla →
  la puerta real es la compilación, y la salida de tipos se filtra a los ficheros propios.
- **El corredor de pruebas termina con código 0 al canalizarlo** → se lee la línea de resumen, no el
  código de salida.
- **El presupuesto de diez peticiones por minuto se agota abriendo fichas** → una por visita, sin
  reintento, y un 429 distinguible que dice que espere unos segundos.
- **Una espera de 4 a 8 s con un cliente delante**, que no se puede partir sin tocar el backend →
  estado de carga desde el primer instante y la limitación declarada, con la tarea diferida abierta.
- **Sin corpus cargado en un entorno nuevo, la caja de pregunta responde siempre que la documentación
  no cubre la pregunta** → no es un defecto de este change; se anota en la tarea diferida que C34 dejó
  abierta y se comprueba antes de la demostración.
- **La ficha no deja rastro**: su uso no será medible, así que la condición de reactivación de la tarea
  diferida de generación no se podrá comprobar con datos → se declara como limitación, no como
  medición pendiente.

## Migration Plan

No hay migración: ni esquema, ni contrato, ni ruta existente que cambie de comportamiento.

- **Despliegue**: el paquete del frontend, con la ruta nueva en carga perezosa. Nada que configurar.
- **Reversión**: retirar la ruta y los tres botones de entrada. El panel de búsqueda asistida, la
  página de venta y la de escaneo vuelven a su comportamiento anterior, porque sus cambios son
  aditivos y no tocan ninguna firma.
- **Compatibilidad**: la ficha lee un contrato que ya está desplegado. Un backend anterior a C34
  devolvería 404 en las dos rutas, y el servicio lo traduce a su miembro propio en lugar de romper.
- **Comprobación en la demostración**: una ficha real con argumentario resuelto, una pregunta con
  citas y un grupo de familia con varias variantes.

## Open Questions

Las cuatro decisiones de producto se cerraron en la exploración (D1, D2, D3 y D5). Las ocho preguntas
abiertas del ticket **se resuelven aquí con su opción por defecto**, y quedan registradas por si el
refinamiento las revisa:

| # | Pregunta | Resolución aplicada |
|---|---|---|
| 1 | ¿Capacidad nueva o ampliar la del panel? | **Nueva**, `sales-assist-card`: otra pantalla, otra ruta y otro contrato. El panel sólo gana la acción secundaria |
| 2 | ¿La ficha se abre desde el detalle de producto del catálogo? | **No**: es pantalla de administración y la ficha necesita un punto de venta. Queda identificado |
| 3 | ¿Cuántas preguntas sugeridas y cuáles? | **Cinco**: mojar la pieza, piel sensible, limpieza en casa, regalo sin saber la talla, playa o piscina |
| 4 | ¿La pregunta se conserva al reabrir? | **No**: un episodio por visita, y conservarla invita a reenviarla sin querer |
| 5 | ¿Se replica el embudo de administrador del panel? | **No**: la ficha no tiene embudo propio; los contadores de sustitutos bastan |
| 6 | ¿Ruta en frío con varios puntos de venta? | **Selector de respaldo** por rol y **ninguna petición** hasta elegir uno |
| 7 | ¿El botón de la fila reporta selección de telemetría? | **No**: ver la ficha no es elegir la pieza, y contarlo falsearía la métrica de búsqueda. Se reporta al vender desde la ficha |
| 8 | ¿La ficha distingue una pieza no preparada de una caída? | **No**: el cuerpo de C34 no los separa. Se pinta «no disponible» y se declara (D12) |

**Lo que queda genuinamente abierto y no bloquea:** si el uso real justifica pedir al backend una forma
de servir la ficha estructural sin pagar una generación. No es decidible hoy, porque la ficha no deja
rastro con el que medirlo.
