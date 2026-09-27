# C36 — decisiones de exploración: el card de venta, y tres códigos que no pueden llegar a él

**Change:** `add-frontend-assist-card-and-family-disambiguation` (C36) · **Fecha:** 2026-09-22
**Árbol explorado:** `ai-eng` en `4552bcf`, limpio · **Rama de implementación:** pendiente, derivada de `ai-eng`

Este informe recoge lo que la exploración **comprobó sobre el árbol** y las diez decisiones de
arquitectura que salen de ello. Es la entrada de `/enrich-us` y del `/opsx:propose` posterior.

**Qué contiene y qué no.** Contiene **tres mediciones nuevas** —M-1 con su variante M-1b, M-2 y
M-3—, todas sobre la base local con el mundo de C10 y el índice de C13, todas reproducibles con el
SQL del §5. **No contiene ninguna medición de C36**, porque C36 no existe: ninguna cifra de latencia
percibida, de uso del card ni de tasa de pregunta aparece aquí. Las de latencia extremo a extremo se
**citan** de [`c34-implementation-measurements.md`](c34-implementation-measurements.md) §4 y no se
vuelven a medir; las de familia, stock y sustitutos de
[`c34-exploration-decisions.md`](c34-exploration-decisions.md) se **recalculan sobre otro
denominador** y se contrastan con las suyas, que cuadran.

**Cuatro de las diez decisiones se cerraron con el desarrollador en la sesión** (D-A, D-B, D-C y
D-E) y llevan la marca **«cerrada»**. Las demás son la recomendación de la exploración. Quedan en
pie salvo que la historia de usuario las revise.

La razón de ser del informe es que la ficha de C36 se escribió en agosto y se anotó dos veces —el 13
de septiembre al implementar C30a y el 21 al explorar C34—, siempre **antes de que existiera el
consumidor**. Al contrastarla con el árbol, **tres de las cinco filas de copy que hereda de C31
corresponden a valores que las rutas de C34 no pueden emitir**, un cuarto aviso satura seis de cada
diez pantallas, y el card no puede servir sus datos baratos sin pagar los caros. Las cuatro cosas se
corrigen aquí.

---

## 1. El inventario, comprobado sobre el árbol y no sobre la ficha

### 1.1 · El andamio que ya existe

| Pieza | Estado verificado | Qué aporta a C36 |
|---|---|---|
| [`POST /api/ai/products/{id}/sales-assist`](../../../backend/src/JoiabagurPV.API/Controllers/AiSalesAssistController.cs) | Real desde C34. Pregunta en el cuerpo, POS obligatorio, argumentario ya resuelto | La llamada única del card, en M2 y M3 |
| [`GET /api/ai/products/{id}/substitutes`](../../../backend/src/JoiabagurPV.API/Controllers/AiSalesAssistController.cs) | Real desde C34. Sin modelo, sub-segundo, filtrado a lo que la tienda puede vender hoy | El bloque de alternativas |
| [`SalesAssistResponse`](../../../backend/src/JoiabagurPV.Application/DTOs/Ai/SalesAssistDtos.cs) | `aiAvailable`, `groups[].members[]` hidratados, `pitch`, `pitchStatus` (6 valores), `citations[]` con `claimScope`, `warnings[]` de códigos, `clarificationQuestion`, `traceId` | La forma exacta que el card pinta. **Ningún campo hay que negociar** |
| [`AssistedSearchResultRow`](../../../frontend/src/components/sales/assisted-search-result-row.tsx) | Componente propio desde C16, con `ORIGIN_LABELS` como tabla de copy exportada y testeada | El patrón de tabla de copy a copiar, y la fila que se extiende |
| [`assisted.tsx`](../../../frontend/src/pages/sales/assisted.tsx) | Selector de POS por rol, episodio por visita, guarda de respuestas fuera de orden, cinco vacíos distinguibles, embudo de administrador | El patrón entero de una pantalla que consume IA en este repositorio |
| Spec viva `assisted-search-panel` | *«MUST NOT render the retriever's raw match reason values, which are engineering vocabulary»* y su regla de etiqueta neutra | El precedente literal de la tabla de copy que la ficha pide |
| Spec viva `assisted-search-panel` | *«A search is issued only when the operator asks for one»* | El precedente de D-C, aplicado a una llamada diez veces más cara |
| [`ROUTES.SALES`](../../../frontend/src/routing/routes.tsx#L34) y el patrón de `scan.tsx` | Entrega del producto elegido **por estado de navegación** a `new.tsx` | Cómo entra y cómo sale el card |
| [`AiSalesAssistOptions`](../../../backend/src/JoiabagurPV.Application/Configuration/AiSalesAssistOptions.cs) | **10 peticiones por minuto y usuario**, página de sustitutos 5 por defecto y 20 máximo, umbral de stock crítico 2 | Los límites que el card no puede ignorar |
| [`ASSIST_WARNING_CODES`](../../../ai-service/src/jbg_ai/assist/constants.py#L51) + [`SalesAssistService`](../../../backend/src/JoiabagurPV.Application/Services/SalesAssistService.cs#L18) | 5 códigos de Python y 2 de .NET | El vocabulario cerrado que hay que traducir |

**Y un bloque que ya no existe.** El «También puede encajar» de complementarios se retiró con el
corte de C27 el 12 de septiembre. El card entrega **tres bloques de los cuatro previstos**, y el §15
del diseño lo declara con su medición. No se reabre aquí.

### 1.2 · Los siete hallazgos

| # | La ficha supone | El árbol dice | Decisión |
|---|---|---|---|
| **H1** | `clarification_question` *«viaja como prosa ya resuelta … el frontend la pinta tal cual»* | **Es constante `null` en las dos rutas de C34.** [`orchestrator.py:270-280`](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L270-L280) deja `routing = RoutingOutcome()` vacío salvo en M1, y C34 prohíbe M1 por escrito en su spec viva. La excepción razonada de la ficha protege un campo que nadie puede emitir | D-A |
| **H2** | Hereda de C31 *«los dos rechazos, que son dos textos distintos y no uno»* | `query_out_of_domain` y `query_not_in_catalogue` sólo los pone `classify_query`, que sólo corre en M1. **Inalcanzables desde el card.** Escribir su copy daría dos tests verdes sobre caminos imposibles, que es la firma que el proyecto persigue desde C17 | D-A, D-D |
| **H3** | Los cuatro avisos se pintan igual | **`size_label_missing` dispara en el 58,3 % de los cards** (M-2) y está anticorrelacionado con tener familia: 4,0 % con familia contra **92,5 %** sin ella (M-3). No informa de la pieza, informa del estado del enriquecimiento. El propio orquestador tiene escrita la regla que esto viola: *«…which is almost always and therefore informs of nothing»* ([`orchestrator.py:661`](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L661)) | D-E |
| **H4** | — | **Los datos baratos del card y los caros llegan soldados.** El grupo, los cuatro avisos y el estado de stock no requieren ni un token, y sólo se obtienen pagando una generación de 4-8 s. `GET /api/product-families/{id}` existe y no es sólo de administrador, pero está indexada por **familia**, el DTO de producto **no lleva `familyId`**, y no devuelve cantidad por POS: desde un `productId` no hay camino. C34 mide el reparto: **.NET pone 4 ms p50 y la IA 4,4 s** | D-C |
| **H5** | — | **10 peticiones por minuto y usuario**, y la spec viva de C34 prohíbe cachear la respuesta del card. Un card que se dispara solo y un reintento automático agotan el presupuesto abriendo diez fichas | D-C |
| **H6** | *«C16 ‖ C36 — misma página y servicio del frontend»*, y el docstring de C16 pide *«extend this row rather than rewrite the page»* | La situación que la propia ficha nombra —*«el cliente tiene la pieza en la mano y pregunta»*— **no llega por el panel de búsqueda**: llega por `scan.tsx` y por el buscador de SKU de `new.tsx`. Un card confinado a la fila deja esas dos entradas sin acceso al corpus de C23, que es el hueco que la caja de pregunta existía para cerrar | D-B |
| **H7** | — | En el cuerpo de `/sales-assist`, **el 422 no se distingue de la caída**: los dos dan `aiAvailable: false` (limitación 3 de C34). El card no puede decir *«esta pieza aún no está preparada»* y tiene que decir *«el asistente no está disponible»*, que es menos cierto. C34 deja escrito que añadir el campo *«no rompe nada»* | D-G, §6 |

---

## 2. Las diez decisiones

### D-A · Alcance: cinco códigos alcanzables, y el «no lo sé» sigue sin pantalla — **cerrada**

**Decisión.** C36 cubre los **cinco códigos que las rutas de C34 pueden emitir** y ninguno más:

| código | origen | alcanzable | frecuencia |
|---|---|---|---|
| `family_has_variants` | Python, ajustado por .NET | sí | 31,2 % tras hidratar (M-2) |
| `size_label_missing` | Python | sí | 58,3 % (M-2) |
| `stock_critical` | .NET tras hidratar | sí | 3,9 % (M-2) |
| `family_members_out_of_stock` | .NET tras hidratar | sí | 4,3 % (M-2) |
| `knowledge_not_covered` | Python, sólo M3 | sí | 22,5 % de las M3 (C34 §4) |
| `query_out_of_domain` | Python, **sólo M1** | **no** | — |
| `query_not_in_catalogue` | Python, **sólo M1** | **no** | — |

Los dos inalcanzables **no llevan copy**. En su lugar se escribe **un test que comprueba que caen en
la etiqueta neutra**, que convierte dos cadenas muertas en una prueba viva de la regla de tolerancia
que la ficha sí exige. `clarification_question` se lee del contrato y se pinta si llega, sin bloque
propio ni copy: es un campo del DTO, no una funcionalidad.

**Consecuencia declarada, no disimulada.** Las limitaciones **12 y 13** del §15 del diseño siguen
abiertas: la pregunta libre sin pieza no tiene pantalla, y el *rechazo cortés* de C31 —distinto de
la abstención honesta— sólo se demuestra en el arnés de C38. **El bucle agéntico de C32b tampoco
tiene consumidor.** Exponer M1 es un change propio, posterior a C36.

| Alternativa | Descartada porque |
|---|---|
| Escribir las dos filas de copy «por si acaso», el vocabulario es versionado | Dos tests verdes sobre caminos imposibles. El coste no es escribir las cadenas, es lo que declara la entrega |
| Ampliar C36 con la ruta M1 en .NET | Rompe *«Zona: `frontend/src/`»*, mete dos capas en un change y la regla 5 del §1 lo partiría. Y M1 arrastra el problema que llevó a C34 a excluirlo: sus marcadores no dicen de qué pieza son |
| Un change propio (C40) después de C36 | **No descartada, aplazada.** Es la vía por la que las limitaciones 12 y 13 se cierran, con un diseño estrecho: retirar el argumentario siempre que sobreviva cualquier marcador |

### D-B · El card vive en ruta propia, con tres entradas — **cerrada**

**Decisión.** `/sales/new/assist/:productId`, carga perezosa, POS por estado de navegación con
selector de respaldo por rol cuando la ruta se abre en frío. Un solo componente
(`components/sales/sales-assist-card.tsx`) montado en una ruta, con **tres entradas**:

```text
  assisted.tsx ──[«Ver ficha de venta» en la fila]──┐
  new.tsx ───────[botón junto al producto elegido]──┼──▶ /sales/new/assist/:productId
  scan.tsx ──────[tras resolver el código]──────────┘            │
                                                                 │ [Vender esta]
                                                                 ▼
                                                      /sales/new  (estado de navegación)
```

La fila de C16 **se extiende con un botón y no se reescribe**, que es exactamente lo que su docstring
pide. La salida del card reusa el traspaso por estado de navegación que `scan`, `image` y `assisted`
ya usan: el card no duplica ni el método de pago, ni la cantidad, ni la validación de stock.

| Alternativa | Descartada porque |
|---|---|
| Desplegable dentro de la fila de resultados | Lectura literal del docstring, pero deja la pieza escaneada y la buscada por SKU sin acceso al corpus (H6); mete cuatro bloques y prosa larga en un `<li>`; y diez filas con un botón cada una invitan a agotar las 10 peticiones del minuto |
| Drawer o *sheet* sobre la página actual | En móvil, cuatro bloques y prosa en un *sheet* es incómodo, y «elegir variante → vender» sale a doble salto |
| Panel en línea dentro de `new.tsx` | `new.tsx` son 723 líneas y es la caja; y el panel de búsqueda necesitaría su propia copia igualmente |

### D-C · Navegar al card es el acto explícito: una llamada por visita — **cerrada**

**Decisión.**

1. **Una petición de assist por visita al card**, disparada al entrar. Pulsar «Ver ficha de venta»
   **es** el acto explícito que la spec viva de C16 exige para una llamada cara; navegar otra vez es
   otra visita y vuelve a pagar, y eso se dice en la spec en vez de ocultarse con una caché que C34
   prohíbe.
2. **La pregunta del cliente es una segunda llamada explícita** (M3). Máximo típico por visita: dos
   de las diez del minuto.
3. **Ningún reintento automático.** Sobre una ruta de p95 7,1 s y 10 por minuto, un reintento duplica
   el coste y la espera. El reintento lo pide el operario, con un botón.
4. Guarda de respuestas fuera de orden y guarda de episodio, las dos copiadas de `assisted.tsx`.
5. El 429 se pinta **distinguible** de la caída de la IA, como ya hace el panel.

**Por qué no se parte en dos llamadas.** Porque no se puede sin mover .NET (H4). Se declara como
limitación y se anota como tarea diferida: un `generate=false` en la ruta de C34 serviría el card
estructural en ~10 ms, y la cifra que lo justifica ya está publicada.

| Alternativa | Descartada porque |
|---|---|
| Card vacío con botón «Preparar la ficha» | Aplica la regla de C16 al pie de la letra, pero el card abre medio vacío y una funcionalidad que hay que pedir dos veces no se usa |
| Disparar y además pedir `generate=false` a .NET | Arquitectónicamente lo correcto, y **no descartado: diferido**. Rompe la zona de C36 y reabre un change recién archivado |
| Refrescar el card al volver atrás | Cada vuelta atrás costaría una generación |

### D-D · La tabla de copy: dónde vive, qué cubre y qué se testea

**Decisión.** Un módulo propio —`lib/assist-copy.ts`— con funciones exportadas y testeadas
directamente, siguiendo el patrón de `ORIGIN_LABELS`/`originLabel` de C16 y de
`materials-vocabulary.ts`. Nada de literales dispersos por el componente. Cubre:

- los **cinco** códigos de aviso alcanzables de D-A, con la **etiqueta neutra** para cualquier otro;
- los **cinco mensajes** de los seis estados del argumentario (D-G);
- los **cuatro** desenlaces de sustitutos (D-I).

El vocabulario es cerrado **pero versionado**, así que la etiqueta neutra no es una cortesía: es la
única forma de que una versión nueva del servicio no rompa una fila de la pantalla. Y es lo que
recoge los dos rechazos inalcanzables el día que dejen de serlo.

### D-E · `size_label_missing` se degrada a atributo de la pieza, no a alerta — **cerrada**

**Decisión.** Se pinta **siempre** —no se suprime nada de lo que el backend emitió— pero **como una
línea neutra junto al SKU** (*«Sin talla declarada»*), no como una de las alertas del bloque de
avisos. La justificación va escrita en la spec con su cifra: **58,3 % de los cards, y 92,5 % de las
piezas sin familia contra 4,0 % de las que la tienen** (M-2, M-3).

El motivo es de atención, no de veracidad: un aviso que salta en seis de cada diez pantallas
canibaliza a `stock_critical`, que salta en el 3,9 % y es el que puede costar una venta. El apunte
de S11 lo dice del mismo modo para las citas —*«demasiada citación cansa y deja de leerse»*—, y el
propio orquestador ya rechazó un cálculo de este aviso por esa razón exacta.

| Alternativa | Descartada porque |
|---|---|
| Pintarlo como los otros cuatro | Fatiga de avisos en el 58 % de los cards; al tercero no se lee ninguno |
| No pintarlo cuando la pieza no tiene familia | El frontend estaría **suprimiendo** un código que el backend emitió, que es justo lo que la spec viva del panel prohíbe hacer con las razones de coincidencia |

### D-F · La confirmación de variante: un botón por miembro, sin preselección

**Decisión.** Cuando el grupo trae **dos o más miembros**, el card **no preselecciona ninguno** y no
ofrece ninguna acción de venta que no nombre a un miembro concreto: una fila por variante con su
`variantLabel` destacado, su precio, sus unidades en esa tienda y su propio botón. El clic **es** la
confirmación. Con un solo miembro, la acción directa vuelve.

La garantía se cierra **en el card y no en la caja**: el traspaso lleva ya un `productId` concreto, y
confirmar otra vez en `new.tsx` obligaría a la caja a conocer familias sin añadir garantía.

**Dos mediciones sostienen la forma.** El bloque cabe: **el 99,6 % de los grupos pintados tiene entre
2 y 4 miembros** y el máximo real es 6 (M-1b) — el tope de 8 del *roster* no sobrevive a la
hidratación de una tienda. Y las variantes se distinguen: **el 98,3 % de los 544 grupos trae todas
las etiquetas presentes y distintas entre sí**, con **cero** grupos de etiquetas todas nulas y cero
con duplicados (M-1). La sospecha de que el bloque pudiera enseñar filas indistinguibles **queda
refutada**.

| Alternativa | Descartada porque |
|---|---|
| Ancla preseleccionada más diálogo de confirmación | Preseleccionar y confirmar es el patrón que se pulsa sin leer |
| Nada preseleccionado y un botón único deshabilitado | Añade un paso y un estado para la misma garantía que un botón por fila da sin ninguno |
| Repetir la confirmación en `new.tsx` | Obliga a la caja a conocer familias por cero garantía añadida |

### D-G · Seis estados del argumentario, cinco mensajes

**Decisión.**

| `pitchStatus` | ¿el resto del card es real? | mensaje |
|---|---|---|
| `generated` | sí | — (se pinta el argumentario) |
| `ai_unavailable` | **no**: sin citas, sin `matchReasons`, familia leída de `ProductFamily` | «El asistente no está disponible. Lo que ves viene del catálogo.» |
| `not_generated` | **sí, íntegro** | «Los datos de la pieza son los del índice; el argumentario no se ha generado.» |
| `withheld_by_ai` | sí | «No he podido redactar algo que pueda sostener con los datos de esta pieza.» |
| `withheld_unresolved` | sí | *(el mismo texto)* |
| `withheld_out_of_stock` | sí | «Esta pieza está agotada aquí. Te propongo alternativas.» |

**`ai_unavailable` y `not_generated` no se funden**, aunque para el operario suenen parecido: en el
primero media pantalla es catálogo puro y en el segundo no, y fundirlos haría que el card mintiera
sobre de dónde salen los materiales y las razones de coincidencia. **`withheld_by_ai` y
`withheld_unresolved` sí comparten texto** —el operario no puede hacer nada distinto— pero se
conservan distinguibles en el DOM para que un test los separe.

Los tres estados retenidos **terminan en una acción y no en un punto**, siguiendo el apunte de S16:
*«reconoce el límite y, de paso, dice qué haría falta para superarlo»*. Es lo que separa una
abstención honesta de un fallo.

**Lo que no se puede decir**, por H7: con `ai_unavailable` el card no distingue una pieza que el
servicio no puede procesar de una caída, así que dice lo segundo. Queda declarado.

### D-H · Citas: verificables por lectura, no por enlace

**Decisión.** Cada cita se pinta con `documentTitle`, `sectionTitle` y `snippet`, plegadas por
defecto. **`claimScope` se distingue visualmente y con palabras**: `establecimiento` —25 de los 161
fragmentos— lleva una insignia propia y la frase que la propia ficha de `baño de oro` se aplica,
*«conviene confirmarlo en tienda antes de trasladarlo a un cliente»*. `general` no la lleva.

**No se resuelven a enlaces**, porque la spec viva de C34 lo prohíbe y porque no hay ninguna ruta
HTTP que lea el corpus: vive en `ai-service/prompts/knowledge/v1/*.md`. De las tres propiedades que
pide el apunte de S11, C36 entrega **dos**: la cita *resuelve* (C30b comprueba integridad
referencial en código después de generar) y *localiza* (título de documento, título de sección y
fragmento). La tercera —*trazable con un clic*— **se declara como limitación**, con la salida que el
propio apunte concede: *«la citación textual verificable es una opción digna»*.

**Las citas se ocultan cuando el argumentario no se entrega.** Enseñar fuentes de un texto que el
operario no puede leer es decorar, y además serían sólo las que ese argumentario usó y no las que
fundamentaron la respuesta (limitación 2 de C34).

### D-I · Sustitutos: disparador, los cuatro vacíos y la página corta

**Decisión.**

1. **El disparador es `hasStock === false` en el miembro anclado**, no `pitchStatus ===
   withheld_out_of_stock`. El primero está presente en **todos** los estados servidos; el segundo
   sólo cuando no hubo pregunta. Dispara en el **8,7 %** de los cards (M-2).
2. **Automático**, porque no llama a ningún modelo y es exactamente el momento en que hace falta.
3. **No se pide si el card degradó.** Con `aiAvailable: false` el interruptor está apagado o el
   circuito abierto, y la llamada devolvería `ai_unavailable` con certeza: más honesto decirlo que
   gastarla.
4. **Los cuatro desenlaces, cuatro textos.** `product_not_indexed` se pinta como *«esta pieza aún no
   está preparada»* y **nunca** como una caída, que es lo que C34 pide por escrito.
5. **Página de 5**, el valor por defecto de la configuración, con la regla de página corta de C16: si
   sobreviven tres, se dice «3 alternativas» y no se rellena.

### D-J · La caja de pregunta: sugerencias horneadas, 500 caracteres, nunca en la URL

**Decisión.** Caja de texto **con cuatro a seis preguntas sugeridas derivadas del corpus**, que
rellenan y envían en un solo acto, con el patrón de `EXAMPLE_QUERIES` que la spec viva del panel ya
tiene. Límite de **500 caracteres**, el del contrato congelado que .NET valida, comprobado en el
cliente antes de enviar. La pregunta viaja **en el cuerpo del `POST`** y no se escribe en la URL, ni
en el estado del router que acaba en el historial del navegador.

**Por qué sugerencias y no sólo una caja.** El apunte de S4 es explícito: *«la información sobre qué
pedir y cómo pedirlo se puede hornear en la interfaz»*. Aquí el matiz es que la pregunta es del
cliente y literal, así que no es *prompting* delegado; pero el remedio sigue aplicando por otra
razón, medida: **9 de 40 preguntas reales de mostrador cayeron en `knowledge_not_covered`** (C34 §4).
El corpus cubre diez situaciones concretas —piscina, piel sensible, regalo sin talla, niños,
perfume—, y enseñarlas sube la tasa de cobertura además de la usabilidad.

---

## 3. Contraste con los apuntes del máster

| Apunte | Relación con C36 |
|---|---|
| S4 *«De interfaz conversacional a interfaz de producto»*: *«la información sobre qué pedir se puede hornear en la interfaz»* | D-J: preguntas sugeridas del corpus, no un `textarea` desnudo. **Matiz propio**: aquí la pregunta es del cliente y literal, así que no hay *prompting* delegado; la razón para hornearla es la cobertura medida |
| S11 *Citación y atribución verificable*: resuelve · localiza · trazable con un clic | D-H: **dos de tres**. La tercera se declara como limitación, con la salida que el propio apunte concede |
| S11: *«demasiada citación cansa y deja de leerse»* | D-E: el mismo argumento, aplicado a un aviso que satura el 58,3 % de los cards |
| S16 *Un sistema debe saber decir «no lo sé»*: la abstención honesta *«dice qué haría falta para superarlo»* | D-G: los tres estados retenidos terminan en una acción |
| S16: *«la seguridad es un eje distinto de la calidad»* | D-A: el rechazo cortés de C31 **no tiene pantalla** y se declara, no se finge con copy inalcanzable |
| S3 *Streaming y manejo de respuestas largas* | **Desviación consciente.** No hay *streaming*: la puerta de marcadores de C34 necesita el texto **entero** antes de decidir si lo entrega, y un token a token o enseñaría `{{price}}` o no podría detectar un marcador malformado que se completa después |
| S3 *Cacheo*: no cachear lo que depende de precio o inventario | D-C: sin caché, que además la spec viva de C34 prohíbe |
| **Lo que los apuntes no cubren** | Un card cuyos datos baratos y caros llegan soldados en la misma respuesta (H4), y traducir un vocabulario cerrado y versionado en la capa de presentación |

En la rúbrica del PF, C36 cae en **Funcionalidad (25 %)** —*«el flujo principal resuelve el caso de
uso»*—: es el único change que pone la capa RAG delante del operario.

---

## 4. Mapa de deltas

### Specs

| Capability | Delta | Qué lleva |
|---|---|---|
| **`sales-assist-card`** | **ADDED**, nueva | La ruta y sus tres entradas, el episodio por visita sin reintento, la tabla de copy con sus cinco códigos y la etiqueta neutra, el aviso de talla degradado a atributo, la confirmación de variante sin preselección, los cinco mensajes de los seis estados, las citas con su alcance, los cuatro desenlaces de sustitutos y la caja de pregunta con sus límites |
| `assisted-search-panel` | **MODIFIED** | La fila gana una acción secundaria hacia el card que **no sustituye** a la selección para venta ni la bloquea. El requisito exacto que se modifica lo fija la historia de usuario |

### Fichas del plan

| Ficha | Cambio |
|---|---|
| **C36** | Corregida en el sitio: se retiran las dos filas de copy de los rechazos y la excepción razonada de `clarification_question` (H1, H2); se nombra la ruta propia; se añade el aviso de talla degradado; el test `should require variant confirmation…` se precisa como «ningún miembro preseleccionado» |
| §4 del plan | El párrafo que cierra el hueco del corpus de C23 sigue siendo correcto: la caja de pregunta es de C36 y llama a `/sales-assist` con `question` en el cuerpo |

### Diseño

**Al archivar C36** habrá que tocar el §15:

- **Limitación 12** deja de ser íntegra: dos de los tres modos llegan al operario **y ya tienen
  pantalla**; la pregunta libre sigue sin ella. Se reescribe, no se borra.
- **Limitación 13** se conserva intacta y gana una frase: el rechazo cortés de C31 no tiene
  pantalla, así que la distinción entre *«el catálogo no puede contestar»* y *«esto no es una
  pregunta de joyería»* sólo se demuestra en el arnés.
- **Limitación nueva**: el card **no tiene telemetría**. A diferencia de la búsqueda asistida, que
  persiste `ProductSearchEvent`, no hay tabla que registre una apertura de card, una pregunta ni una
  variante elegida, así que su uso no es medible.
- El §7.7 gana la nota de que la traducción de los códigos al castellano la hace esta capa, y que dos
  de los siete códigos del vocabulario no tienen consumidor.

### `DEFERRED_TASKS.md`

| Entrada | Qué pasa con C36 |
|---|---|
| **Nueva**: `generate=false` en `/sales-assist` para servir el card estructural sin generar | Se abre, con la medición que la justifica (.NET 4 ms p50, IA 4,4 s) y con la condición de reactivación: que el uso real del card muestre aperturas que no leen el argumentario |
| **Nueva**: telemetría del card | Se abre: ninguna de las tres cosas que el card decide —abrir, preguntar, elegir variante— deja rastro |
| *C32b — política de timeout y circuito de `/v1/assist/agent`* | **Sigue diferida.** D-A deja el agente fuera y C36 no le da consumidor |
| *C32b — desglose del uso por etapa* | Sigue diferida, por el mismo motivo |
| *C34 — el corpus no viaja en la imagen de `jbg-ai`* | **Sigue abierta y ahora importa más**: sin corpus cargado, la caja de pregunta de D-J responde siempre `knowledge_not_covered` en un entorno nuevo |

---

## 5. Mediciones reproducibles

Las tres se reproducen con el árbol en `4552bcf` y el contenedor local de PostgreSQL
(`jpv-pv-postgres`) con el mundo de C10 y el índice de C13 cargados. **Esos datos describen el mundo
simulado, no la tienda**: el stock y la cobertura por POS los generó C10.

**El universo, y por qué es otro que el de C34.** Una fila por par **(POS, pieza indexada que ese POS
lleva)**, con cualquier cantidad, que es la condición de servicio de C34: **4.910 anclas** sobre las
diez tiendas. Se excluye el *Taller Joia Bagur, Maó*, que es origen de suministro y no mostrador,
igual que hizo C34. La diferencia con las cifras de su M-2 es el denominador: aquél contaba sólo las
anclas **con familia** (1.897), porque medía dos avisos que sólo se ven juntos ahí; éste cuenta
**todas**, porque el card se abre sobre cualquier pieza. Las dos series cuadran allí donde se pueden
comparar, y el contraste va anotado abajo.

Contexto del índice, comprobado en la misma sesión: **1.168 documentos activos**, **156 familias**,
**491 miembros**, mínimo 2, máximo 8, media 3,15 — idéntico a lo que C18b publicó y a lo que
`constants.py` documenta.

### M-1 · Distinguibilidad de las variantes dentro del grupo que el card pinta

**Qué replica.** El grupo tal como llega al card **después** de la hidratación de C34: los miembros
de la familia que ese POS lleva con inventario activo de producto activo. La pregunta es si el
operario puede distinguirlos, que es la condición para que la confirmación de variante de D-F
signifique algo.

```bash
docker exec -i jpv-pv-postgres psql -U postgres -d joiabagur_pv <<'SQL'
WITH carried AS (
  SELECT i."PointOfSaleId" AS pos_id, i."ProductId" AS product_id
  FROM "Inventories" i JOIN "Products" p ON p."Id" = i."ProductId"
  WHERE i."IsActive" AND p."IsActive"
),
doc AS (SELECT product_id, family_id, variant_label FROM ai.product_document WHERE is_active IS TRUE),
grp AS (
  SELECT c.pos_id, d.family_id,
         count(*)                        AS miembros,
         count(d.variant_label)          AS con_etiqueta,
         count(DISTINCT d.variant_label) AS etiquetas_distintas
  FROM carried c
  JOIN doc d ON d.product_id = c.product_id
  JOIN "PointOfSales" s ON s."Id" = c.pos_id
  WHERE d.family_id IS NOT NULL AND s."Name" <> 'Taller Joia Bagur, Maó'
  GROUP BY c.pos_id, d.family_id
  HAVING count(*) >= 2
)
SELECT count(*)        AS grupos_pintados,
       sum(miembros)   AS filas_pintadas,
       round(100.0*avg((con_etiqueta = miembros AND etiquetas_distintas = miembros)::int),1) AS pct_distinguibles,
       round(100.0*avg((con_etiqueta = 0)::int),1)                                           AS pct_todas_nulas,
       round(100.0*avg((con_etiqueta > 0 AND con_etiqueta < miembros)::int),1)               AS pct_mixtas,
       round(100.0*avg((con_etiqueta = miembros AND etiquetas_distintas < miembros)::int),1) AS pct_duplicadas
FROM grp;
SQL
```

```text
 grupos_pintados | filas_pintadas | pct_distinguibles | pct_todas_nulas | pct_mixtas | pct_duplicadas
-----------------+----------------+-------------------+-----------------+------------+----------------
             544 |           1532 |              98.3 |             0.0 |        1.7 |            0.0
```

**Lectura.** El bloque de desambiguación es sólido: en **98,3 %** de los 544 grupos las etiquetas
están todas presentes y son todas distintas; **ninguno** tiene todas las etiquetas nulas y **ninguno**
tiene duplicados. Los 9 grupos mixtos (1,7 %) son el caso que la fila tiene que degradar sin romper
—mostrar el SKU cuando falte la etiqueta—, no un caso que haya que resolver. **La sospecha de que el
bloque pudiera enseñar filas indistinguibles queda refutada.**

### M-1b · Cuántas filas pinta ese bloque

Es M-1 sin la clasificación de etiquetas, agregando por tamaño de grupo.

```bash
docker exec -i jpv-pv-postgres psql -U postgres -d joiabagur_pv <<'SQL'
WITH carried AS (
  SELECT i."PointOfSaleId" AS pos_id, i."ProductId" AS product_id
  FROM "Inventories" i JOIN "Products" p ON p."Id" = i."ProductId"
  WHERE i."IsActive" AND p."IsActive"
),
doc AS (SELECT product_id, family_id FROM ai.product_document WHERE is_active IS TRUE),
grp AS (
  SELECT c.pos_id, d.family_id, count(*) AS miembros
  FROM carried c JOIN doc d ON d.product_id = c.product_id
  JOIN "PointOfSales" s ON s."Id" = c.pos_id
  WHERE d.family_id IS NOT NULL AND s."Name" <> 'Taller Joia Bagur, Maó'
  GROUP BY 1,2 HAVING count(*) >= 2
)
SELECT miembros, count(*) AS grupos FROM grp GROUP BY 1 ORDER BY 1;
SQL
```

```text
 miembros | grupos
----------+--------
        2 |    209
        3 |    229
        4 |    104
        5 |      1
        6 |      1
```

**Lectura.** **542 de 544 grupos (99,6 %) caben en 2 a 4 filas**, y el máximo real es 6. El tope de 8
del *roster* del índice no sobrevive nunca a la hidratación de una tienda. Un botón por miembro
(D-F) no degenera en una lista larga.

### M-2 · Con qué frecuencia dispara cada bloque y cada aviso

**Qué replica.** Las reglas tal como están escritas: `family_has_variants` desde el *roster* del
índice ([`_warnings`](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L202-L221)), el bloque de
familia desde lo que sobrevive a la hidratación de C34, los dos avisos de stock desde las cantidades
del POS con el umbral por defecto de 2, y `size_label_missing` desde el `size_label` del documento
indexado de la pieza anclada.

```bash
docker exec -i jpv-pv-postgres psql -U postgres -d joiabagur_pv <<'SQL'
WITH carried AS (
  SELECT i."PointOfSaleId" AS pos_id, i."ProductId" AS product_id, i."Quantity" AS qty
  FROM "Inventories" i JOIN "Products" p ON p."Id" = i."ProductId"
  WHERE i."IsActive" AND p."IsActive"
),
doc AS (
  SELECT product_id, family_id, variant_label, size_label
  FROM ai.product_document WHERE is_active IS TRUE
),
roster AS (
  SELECT family_id, count(*) AS roster_size
  FROM doc WHERE family_id IS NOT NULL GROUP BY family_id
),
anchor AS (
  SELECT c.pos_id, c.qty AS anchor_qty, d.family_id, d.size_label,
         COALESCE(r.roster_size, 0) AS roster_size,
         (SELECT count(*) FROM carried cm JOIN doc m ON m.product_id = cm.product_id
           WHERE cm.pos_id = c.pos_id AND m.family_id = d.family_id)          AS carried_members,
         (SELECT count(*) FROM carried cm JOIN doc m ON m.product_id = cm.product_id
           WHERE cm.pos_id = c.pos_id AND m.family_id = d.family_id
             AND m.product_id <> c.product_id AND cm.qty = 0)                 AS others_zero
  FROM carried c
  JOIN doc d ON d.product_id = c.product_id
  LEFT JOIN roster r ON r.family_id = d.family_id
),
scoped AS (
  SELECT a.* FROM anchor a JOIN "PointOfSales" s ON s."Id" = a.pos_id
  WHERE s."Name" <> 'Taller Joia Bagur, Maó'
)
SELECT count(*)                                                        AS anclas,
       round(100.0*avg((family_id IS NOT NULL)::int),1)                AS pct_con_familia,
       round(100.0*avg((roster_size > 1)::int),1)                      AS pct_variants_py,
       round(100.0*avg((carried_members >= 2)::int),1)                 AS pct_bloque_familia,
       round(100.0*avg((anchor_qty = 0)::int),1)                       AS pct_bloque_sustitutos,
       round(100.0*avg((anchor_qty BETWEEN 1 AND 2)::int),1)           AS pct_stock_critical,
       round(100.0*avg((others_zero > 0)::int),1)                      AS pct_members_oos,
       round(100.0*avg((size_label IS NULL OR size_label = '')::int),1) AS pct_size_missing
FROM scoped;
SQL
```

```text
 anclas | pct_con_familia | pct_variants_py | pct_bloque_familia | pct_bloque_sustitutos | pct_stock_critical | pct_members_oos | pct_size_missing
--------+-----------------+-----------------+--------------------+-----------------------+--------------------+-----------------+------------------
   4910 |            38.6 |            38.6 |               31.2 |                   8.7 |                3.9 |             4.3 |             58.3
```

**Cinco lecturas.**

1. **El bloque de familia se ve en 1 de cada 3 cards** (31,2 %). Es el bloque más frecuente de los
   tres que el card entrega.
2. **`pct_con_familia` y `pct_variants_py` son el mismo número**, y no es casualidad: la familia más
   pequeña del índice tiene **dos** miembros, así que Python emite `family_has_variants` siempre que
   la pieza tiene familia. Los **7,4 puntos** de diferencia hasta el 31,2 % son exactamente lo que
   **C34 retira al hidratar** — su regla «sólo se quita, nunca se añade» trabaja en una de cada cinco
   piezas con familia.
3. **Las tres cifras que se pueden contrastar con C34 cuadran.** Sobre las 1.897 anclas con familia,
   este 8,7 % da 6,7 % (C34: 6,5 %), el 3,9 % da 4,0 % (C34: 4,0 %) y el 4,3 % da 11,1 %
   (C34: 11,2 %). La pequeña diferencia del primero es de denominador y no de regla.
4. **El bloque de sustitutos dispara en el 8,7 %** de los cards.
5. **`size_label_missing` dispara en el 58,3 %**, que es lo que motiva D-E y lo que M-3 explica.

### M-3 · Por qué `size_label_missing` no informa de la pieza

```bash
docker exec -i jpv-pv-postgres psql -U postgres -d joiabagur_pv <<'SQL'
WITH carried AS (
  SELECT DISTINCT i."PointOfSaleId" AS pos_id, i."ProductId" AS product_id
  FROM "Inventories" i JOIN "Products" p ON p."Id" = i."ProductId"
  WHERE i."IsActive" AND p."IsActive"
),
doc AS (SELECT product_id, family_id, variant_label, size_label FROM ai.product_document WHERE is_active IS TRUE),
a AS (
  SELECT c.pos_id, d.* FROM carried c JOIN doc d ON d.product_id = c.product_id
  JOIN "PointOfSales" s ON s."Id" = c.pos_id WHERE s."Name" <> 'Taller Joia Bagur, Maó'
)
SELECT (family_id IS NOT NULL) AS con_familia, count(*) AS anclas,
       round(100.0*avg((size_label IS NULL OR size_label = '')::int),1) AS pct_sin_size_label,
       round(100.0*avg((variant_label IS NULL)::int),1)                 AS pct_sin_variant_label
FROM a GROUP BY 1 ORDER BY 1;

SELECT piece_type, count(*) AS docs,
       round(100.0*avg((size_label IS NULL OR size_label = '')::int),1) AS pct_sin_size_label
FROM ai.product_document WHERE is_active IS TRUE
GROUP BY 1 ORDER BY docs DESC LIMIT 8;
SQL
```

```text
 con_familia | anclas | pct_sin_size_label | pct_sin_variant_label
-------------+--------+--------------------+-----------------------
 f           |   3013 |               92.5 |                 100.0
 t           |   1897 |                4.0 |                   1.4

 piece_type | docs | pct_sin_size_label
------------+------+--------------------
 pendientes |  275 |               49.5
 anillo     |  268 |               54.1
 pulsera    |  207 |               58.0
 colgante   |  160 |               47.5
 collar     |  138 |               57.2
 broche     |   79 |               62.0
 tobillera  |   14 |              100.0
 diadema    |   11 |               90.9
```

*(La segunda consulta es sobre los 1.168 documentos del índice, no sobre las 4.910 anclas: describe
el catálogo, no lo que cada tienda lleva.)*

**Lectura.** El aviso está casi perfectamente **anticorrelacionado con pertenecer a una familia**:
**4,0 %** de las piezas con familia contra **92,5 %** de las que no la tienen. Dicho de otro modo,
`size_label_missing` es casi un sinónimo de *«esta pieza no entró en ninguna familia con tallas»* —
una afirmación sobre el estado del enriquecimiento del catálogo, no sobre la pieza que el cliente
tiene delante. El reparto por tipo lo confirma: 100 % en tobilleras y 90,9 % en diademas, contra
~50 % en anillos y pendientes.

`variant_label` es **nulo en el 100 %** de las piezas sin familia, lo cual es correcto por
construcción: una etiqueta de variante sólo significa algo dentro de una familia.

---

## 6. Las mediciones que esta exploración no hace

1. **Latencia percibida del card en la demo.** C34 mide la petición (p50 4,42 s, p95 7,13 s en
   máquina de desarrollo; 1,3 a 3,8 s en la demo con n = 18), pero nadie ha medido cuánto tarda el
   card **desde el clic hasta que hay algo en pantalla**, que incluye la navegación y la carga
   perezosa de la ruta. Se toma en la implementación, con la demo.
2. **Tasa de aperturas que no leen el argumentario.** Es la condición de reactivación del
   `generate=false` que D-C deja diferido, y **no es medible hoy**: el card no tiene telemetría
   (§4). Queda como limitación declarada, no como medición pendiente.
3. **El 422 frente a la caída.** H7 no se cierra en C36: distinguirlos pide un campo en el DTO de
   .NET, que C34 dejó escrito como *«se añade sin romper nada»*. Si la historia de usuario lo quiere,
   deja de ser un change de frontend.

---

## 7. Tests

**Los de la ficha que se mantienen**, con la precisión que la exploración les añade:

| Test | Precisión |
|---|---|
| `should require variant confirmation when family has multiple members` | Se comprueba como **«ningún miembro preseleccionado y ninguna acción de venta que no nombre a un miembro»** (D-F). C30a y C34 ya impiden que pase en vacío: el contrato impone *familia nula ⇒ exactamente un miembro*, y la hidratación retira el aviso cuando sobrevive uno |
| `should show substitutes block when selected product is out of stock` | El disparador es `hasStock` del miembro anclado, no `pitchStatus` (D-I) |
| `should render citations when pitch has sources` | — |
| `should mark an establishment claim differently from a general one` | — |
| `should fall back to a neutral label for an unknown warning code` | — |

**El que no se escribe:** `should render complementary block when recommendations exist`, cuyo bloque
se retiró con el corte de C27.

**Los que añade la exploración**, uno por decisión que lo necesita:

| Test | Decisión |
|---|---|
| `should label a router refusal code with the neutral fallback` | D-A |
| `should reach the card from the result row, the sale page and the scan page` | D-B |
| `should issue exactly one assist request per visit` | D-C |
| `should not retry a failed assist request` | D-C |
| `should distinguish a rate limited response from an unavailable service` | D-C |
| `should render size label missing as a piece attribute and not as a warning` | D-E |
| `should preselect no member when the group has several` | D-F |
| `should carry the chosen member to the manual sale page` | D-F |
| `should degrade a member row with no variant label to its sku` | D-F |
| `should tell a degraded card from one whose argument was not generated` | D-G |
| `should say what to do next when the argument is withheld` | D-G |
| `should hide citations when the argument was withheld` | D-H |
| `should not request substitutes when the card is degraded` | D-I |
| `should tell the four substitute outcomes apart` | D-I |
| `should declare a short substitutes page instead of padding it` | D-I |
| `should fill and send in one act from a suggested question` | D-J |
| `should reject a question over five hundred characters before sending` | D-J |
| `should never put the question in the url` | D-J |

Los nombres siguen la convención `should …` de la suite de frontend. La historia de usuario los puede
fusionar o partir.

**Dos trampas de la suite que esta zona pisa de lleno**, documentadas en
[`testing-frontend.md`](../../testing-frontend.md) y en `CLAUDE.md`: el card arrastra `AuthProvider`
—y `CartProvider` si se monta cerca de la caja—, que es la causa de un tercio de los 113 fallos de
línea base; y MSW **no falla una petición sin *handler***, así que un test del card podría pasar sin
haber afirmado nada. El fichero a copiar es `pages/sales/__tests__/cart.test.tsx`, y los servicios se
piden con `vi.mock`. **La línea base se toma por nombres antes de tocar nada.**
