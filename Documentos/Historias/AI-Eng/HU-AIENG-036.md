# HU-AIENG-036: El card de venta en el mostrador — desambiguación por familia con confirmación explícita, citas con su alcance y la pregunta del cliente

## Formato estándar

**Como** Operador de un punto de venta,
**quiero** una ficha de venta que, sobre la pieza que tengo delante, me enseñe el argumentario con su
precio y su stock reales, me obligue a elegir la variante antes de vender cuando la familia tiene
varias, me deje escribir la pregunta que me acaba de hacer el cliente y me responda citando de dónde
sale cada afirmación, y me proponga alternativas vendibles hoy cuando la pieza está agotada,
**para** poder atender con criterio sin memorizar el catálogo ni las fichas de material, y sin
arriesgarme a vender una talla que no era.

---

## Descripción

Change OpenSpec `add-frontend-assist-card-and-family-disambiguation` / **C36**, épica **EP15 — Venta
Asistida, Sustitutos y Agentes**. Marcado 🔴 en la ruta crítica y en la lista de *nunca se recorta* del
§6 del plan. Prerrequisitos: **C16** (el panel de búsqueda asistida y su patrón de pantalla) y **C34**
(las dos rutas .NET del card), los dos archivados.

**Es el último eslabón visible de la cadena `C30a → C34 → C36`** y el único change del Proyecto Final
que pone la capa RAG delante de una persona. Hasta hoy, el argumentario, las citas, el agrupado por
familia y los sustitutos existen, están medidos y **sólo se demuestran en el arnés de evaluación o con
`curl`**. Aquí cambia el actor: C34 se escribió para el desarrollador del proyecto porque no había
pantalla; ésta se escribe **para el operario**, y su aceptación se comprueba mirando el mostrador.

La regla que gobierna la pantalla es la que el panel de C16 ya tiene en spec viva y esta historia
hereda entera: **no se enseña nada que el sistema no haya afirmado**. El frontend no reordena, no
recalcula stock ni precio, no añade avisos y no traduce un código que no conoce inventándose una
etiqueta.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado | Evidencia |
|---|---|---|
| `POST /api/ai/products/{id}/sales-assist` con `{pointOfSaleId, question?}` | ✅ real desde C34 | [`AiSalesAssistController.cs`](../../../backend/src/JoiabagurPV.API/Controllers/AiSalesAssistController.cs) |
| `GET /api/ai/products/{id}/substitutes` | ✅ real desde C34; sin modelo, sub-segundo | [`AiSalesAssistController.cs`](../../../backend/src/JoiabagurPV.API/Controllers/AiSalesAssistController.cs) |
| `SalesAssistResponse` con `pitchStatus` de 6 valores, `citations[].claimScope` y `warnings[]` de códigos | ✅ completo; **ningún campo hay que negociar** | [`SalesAssistDtos.cs`](../../../backend/src/JoiabagurPV.Application/DTOs/Ai/SalesAssistDtos.cs) |
| `AssistedSearchResultRow` con `ORIGIN_LABELS` exportado y testeado | ✅ el patrón de tabla de copy a copiar, y la fila que se extiende | [`assisted-search-result-row.tsx`](../../../frontend/src/components/sales/assisted-search-result-row.tsx) |
| `assisted.tsx`: selector de POS por rol, episodio por visita, guarda de respuestas fuera de orden, vacíos distinguibles | ✅ el patrón entero de una pantalla que consume IA aquí | [`assisted.tsx`](../../../frontend/src/pages/sales/assisted.tsx) |
| Entrega del producto elegido por estado de navegación a `new.tsx` | ✅ lo usan `scan`, `image` y `assisted` | [`routes.tsx`](../../../frontend/src/routing/routes.tsx) |
| Componentes de UI necesarios (`card`, `badge`, `alert`, `accordion`, `collapsible`, `skeleton`, `textarea`, `select`) | ✅ **todos existen** en Metronic; **no hace falta ninguno nuevo** | [`components/ui/`](../../../frontend/src/components/ui/) |
| Card de venta, tabla de copy de los códigos, caja de pregunta | ❌ **cero** | — |
| Ruta para la pieza + POS en el frontend | ❌ `ROUTES.SALES` no tiene entrada de ficha | [`routes.tsx`](../../../frontend/src/routing/routes.tsx) |
| Telemetría del card | ❌ **no existe** y no se crea aquí: no hay tabla equivalente a `ProductSearchEvent` | — |

### Lo que la exploración refutó de la ficha

La exploración del 2026-09-22 dejó **siete hallazgos, diez decisiones y tres mediciones reproducibles**
en [`c36-exploration-decisions.md`](../../Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md).
Los cuatro que más pesan en esta historia:

1. **Tres de las cinco filas de copy que la ficha hereda de C31 no pueden llegar al card.** El
   enrutador de intención corre **sólo en M1** ([`orchestrator.py:270-280`](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L270-L280)),
   y las dos rutas de C34 son siempre ancladas. Así que `clarification_question` es constante `null` y
   los dos códigos de rechazo (`query_out_of_domain`, `query_not_in_catalogue`) son **inalcanzables**.
   Escribir su castellano daría dos tests verdes sobre caminos imposibles.
2. **`size_label_missing` salta en el 58,3 % de los cards**, y está anticorrelacionado con tener
   familia: **4,0 %** con ella contra **92,5 %** sin ella. No informa de la pieza, informa del estado
   del enriquecimiento del catálogo.
3. **Los datos baratos del card y los caros llegan soldados.** El grupo, los avisos y el stock no
   necesitan ni un token y sólo se obtienen pagando una generación de 4 a 8 s. No hay ninguna ruta que
   devuelva la familia que una tienda lleva a partir de un `productId`.
4. **El bloque de familia es sólido, y eso se comprobó en vez de suponerse**: el **98,3 %** de los 544
   grupos con dos o más miembros trae todas las etiquetas de variante presentes y distintas, ninguno
   las trae todas nulas, y el **99,6 %** cabe en dos a cuatro filas. La sospecha de que el bloque
   pudiera enseñar filas indistinguibles **queda refutada**.

---

### Alcance de esta historia (sí)

1. **Ruta propia `/sales/new/assist/:productId`**, con carga perezosa, punto de venta por estado de
   navegación y selector de respaldo por rol cuando la ruta se abre en frío.
2. **Tres entradas**: la fila de resultados de la búsqueda asistida, el producto seleccionado en la
   página de venta manual, y la pieza resuelta tras escanear un código.
3. **Una petición de asistencia por visita**, disparada al entrar, **sin reintento automático**, con
   guarda de respuestas fuera de orden y estado de carga.
4. **Bloque de familia** con una fila por variante, `variantLabel` destacado, precio y unidades de esa
   tienda, **sin ninguna preselección** y con un botón de venta por miembro.
5. **Traspaso a la venta**: el miembro elegido viaja por estado de navegación a la página de venta
   manual, como ya hacen las otras tres entradas.
6. **Bloque de argumentario** con los **seis estados** de `pitchStatus` pintados como **cinco
   mensajes**, y los retenidos terminando en una acción.
7. **Citas desplegables** con documento, sección y fragmento, **distinguiendo `claimScope`**:
   `establecimiento` lleva insignia y frase propias.
8. **Caja de pregunta** con preguntas sugeridas del corpus que rellenan y envían en un solo acto,
   límite de 500 caracteres comprobado en el cliente, y la pregunta **siempre en el cuerpo**.
9. **Bloque de avisos** con los **cinco códigos alcanzables** traducidos y **etiqueta neutra** para
   cualquier otro; `size_label_missing` **degradado a atributo de la pieza**, no a alerta.
10. **Bloque de sustitutos**, disparado por el miembro anclado sin stock, con los **cuatro desenlaces
    distinguibles** y la regla de página corta.
11. **Tabla de copy en un módulo propio**, exportada y testeada directamente.
12. **La fila de resultados de C16 se extiende** con una acción secundaria hacia el card, que **no
    sustituye** a «Seleccionar para venta» ni la bloquea.

### Fuera de alcance (no)

1. **La pregunta libre sin pieza (M1)** y su pantalla. La limitación **12** del §15 del diseño se
   reescribe pero **no se cierra**: dos de los tres modos llegan al operario, el tercero no.
2. **El rechazo cortés de C31** (`query_out_of_domain`, `query_not_in_catalogue`) y
   `clarification_question`: **inalcanzables** desde estas rutas. No se escribe su castellano. La
   limitación **13** del §15 se conserva íntegra.
3. **La ruta del agente**, `POST /v1/assist/agent`: sigue sin consumidor y sin pantalla de
   conversación.
4. **Ningún cambio en `backend/`**: las dos rutas de C34 se consumen tal como están. En particular,
   **no se añade el campo que distinguiría un 422 de una caída** (limitación 3 de C34).
5. **Ningún cambio en `ai-service/`**: `openapi.json` queda **idéntico byte a byte**.
6. **Sin migración de EF Core** y sin tabla nueva.
7. **Telemetría del card**: no se crea tabla ni evento. El uso del card **no será medible**, y así se
   declara.
8. **Complementarios**: el bloque «También puede encajar» salió con el corte de C27 el 12 de
   septiembre. El card entrega **tres bloques de los cuatro previstos**.
9. **Sin *streaming*** del argumentario: la puerta de marcadores de C34 necesita el texto entero antes
   de decidir si lo entrega.
10. **Sin caché** de la respuesta del card, que la spec viva de C34 prohíbe.
11. **Ni `terraform/` ni `.github/workflows/`**.

---

### Decisiones de diseño ya acordadas

Las cuatro marcadas **«cerrada»** se tomaron con el desarrollador en la sesión de exploración; el resto
son la recomendación de la exploración, aceptada por defecto. Las alternativas descartadas de cada una
están en el [informe](../../Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md).

| # | Decisión | Razón |
|---|---|---|
| **D-A** *(cerrada)* | **Cinco códigos alcanzables y ninguno más.** Los dos rechazos no llevan copy; en su lugar, **un test comprueba que caen en la etiqueta neutra** | El enrutador sólo corre en M1 y estas rutas son ancladas (H1, H2). Un test verde sobre un camino imposible es la firma que el proyecto persigue desde C17 |
| **D-B** *(cerrada)* | **Ruta propia `/sales/new/assist/:productId`** con tres entradas; la fila de C16 se extiende con un botón | La situación que la ficha nombra —*«el cliente tiene la pieza en la mano»*— llega por escaneo y por SKU, no por el panel (H6). Un card confinado a la fila deja esas dos entradas sin acceso al corpus |
| **D-C** *(cerrada)* | **Navegar al card es el acto explícito**: una petición por visita, sin reintento automático; la pregunta es una segunda llamada | Es la regla que la spec viva de C16 ya impone para una llamada más barata. El límite es de **10 peticiones por minuto y usuario** y la caché está prohibida (H5) |
| **D-D** | **Tabla de copy en `lib/assist-copy.ts`**, exportada y testeada directamente | Patrón de `ORIGIN_LABELS`/`originLabel` de C16. El vocabulario es cerrado **pero versionado**, así que la etiqueta neutra es lo único que impide que una versión nueva rompa una fila |
| **D-E** *(cerrada)* | **`size_label_missing` se pinta como línea neutra junto al SKU**, no como alerta. Se pinta **siempre**: no se suprime nada | Salta en el **58,3 %** de los cards y es casi un sinónimo de «no entró en ninguna familia con tallas» (92,5 % sin familia contra 4,0 % con ella). Canibaliza a `stock_critical`, que salta en el 3,9 % y sí puede costar una venta |
| **D-F** | **Un botón de venta por miembro, sin preselección**: el clic *es* la confirmación. Con un solo miembro, la acción directa vuelve | Preseleccionar y confirmar es el patrón que se pulsa sin leer. El bloque cabe (99,6 % en 2-4 filas, máximo real 6) y las variantes se distinguen (98,3 %) |
| **D-G** | **Seis estados, cinco mensajes**: `withheld_by_ai` y `withheld_unresolved` comparten texto; `ai_unavailable` y `not_generated` **no** | En el degradado media pantalla es catálogo puro y en `not_generated` no; fundirlos haría que el card mintiera sobre de dónde salen los materiales. Los retenidos terminan en una acción, como pide S16 |
| **D-H** | **Citas verificables por lectura, no por enlace**; `claimScope` distinguido; **ocultas cuando el argumentario se retiró** | No hay ruta HTTP que lea el corpus y C34 prohíbe resolver enlaces. De las tres propiedades de S11 se entregan dos, y la tercera se declara. Enseñar fuentes de un texto que no se puede leer es decorar |
| **D-I** | **Sustitutos disparados por `hasStock` del miembro anclado**, automáticos, **no pedidos si el card degradó**; cuatro desenlaces y página de 5 | `hasStock` está en todos los estados servidos; `pitchStatus` sólo cuando no hubo pregunta. Con la IA caída la llamada devolvería «no disponible» con certeza |
| **D-J** | **Caja de pregunta con sugerencias del corpus**, 500 caracteres, nunca en la URL | S4: *«la información sobre qué pedir se puede hornear en la interfaz»*. Y medido: **9 de 40** preguntas reales de mostrador cayeron en `knowledge_not_covered` |

### Referencias

- Change de OpenSpec: `openspec/changes/add-frontend-assist-card-and-family-disambiguation/` (C36),
  rama `c36-add-frontend-assist-card-and-family-disambiguation`
- Ticket: [T-AIENG-036](../../../openspec/changes/archive/2026-09-24-add-frontend-assist-card-and-family-disambiguation/ticket.md)
- Informe de exploración: [`c36-exploration-decisions.md`](../../Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md)
- Ficha del plan: [§3 · C36](../../Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- Diseño RAG: [§7.7, §7.8, §15.12, §15.13](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- Capability que se consume: [`ai-sales-assist`](../../../openspec/specs/ai-sales-assist/spec.md)
- Capability que se modifica: [`assisted-search-panel`](../../../openspec/specs/assisted-search-panel/spec.md)
- Precedente directo de pantalla: [HU-AIENG-016](HU-AIENG-016.md) y su capability
- Historia anterior de la cadena: [HU-AIENG-034](HU-AIENG-034.md) · [HU-AIENG-030a](HU-AIENG-030a.md)
  · [HU-AIENG-030b](HU-AIENG-030b.md) · [HU-AIENG-031](HU-AIENG-031.md)
- Testing: [testing-frontend.md](../../testing-frontend.md), sección *Estado de la suite: fallos
  conocidos*
- Componentes reutilizables: [analisis-metronic-frontend.md](../../Propuestas/analisis-metronic-frontend.md)
- Épica: [EP15 — Venta Asistida, Sustitutos y Agentes](../../epicas.md)

---

## Criterios de Aceptación

### Escenario 1: La ficha se abre desde donde el operario ya está, y pide una sola vez

- **Dado que** el operario ha encontrado una pieza —por búsqueda asistida, escaneando su código o
  buscándola por SKU en la página de venta,
- **Cuando** activa la acción de ver su ficha de venta,
- **Entonces** llega a la ficha de esa pieza para el punto de venta en el que está trabajando,
- **Y** se emite **exactamente una** petición de asistencia,
- **Y** mientras llega se ve un estado de carga, no una pantalla vacía,
- **Y** si la petición falla, **no se reintenta sola**: el operario decide si vuelve a pedirla.

### Escenario 2: Una familia con varias tallas obliga a elegir antes de vender

- **Dado que** la pieza pertenece a una familia de la que esa tienda lleva tres variantes,
- **Cuando** se muestra la ficha,
- **Entonces** aparecen las tres con su etiqueta de variante, su precio y sus unidades en esa tienda,
- **Y** **ninguna está preseleccionada**,
- **Y** no existe ninguna acción de venta que no diga a qué variante se refiere,
- **Y cuando** el operario elige una, esa pieza concreta es la que llega a la página de venta,
- **Y** si de la familia esa tienda sólo lleva una, la acción de venta directa vuelve y el aviso de
  variantes no aparece.

### Escenario 3: La pregunta del cliente se responde citando de dónde sale

- **Dado que** el cliente pregunta algo sobre la pieza que tiene en la mano,
- **Cuando** el operario escribe la pregunta —o activa una de las sugeridas, que rellena y envía en un
  solo acto—,
- **Entonces** la pregunta viaja en el cuerpo de la petición y **no aparece en la dirección** de la
  página ni en el historial del navegador,
- **Y** una pregunta de más de 500 caracteres se rechaza antes de enviarse,
- **Y** la respuesta llega con sus citas desplegables, cada una con su documento, su sección y su
  fragmento,
- **Y** una cita que es un **compromiso de la casa** se distingue a simple vista de un hecho general, y
  dice que conviene confirmarlo en tienda antes de trasladarlo a un cliente.

### Escenario 4: Lo que la documentación no cubre se dice, no se disimula

- **Dado que** el operario pregunta algo que el corpus de conocimiento no cubre,
- **Cuando** la respuesta llega con el código que lo declara,
- **Entonces** la ficha lo dice con palabras del mostrador y no con el código,
- **Y** el texto que sí llega no se presenta como si hubiera contestado la pregunta,
- **Y** no se pinta ninguna cita, porque no hay ninguna.

### Escenario 5: Un argumentario retenido dice qué hacer, y se distingue de la IA caída

- **Dado que** la asistencia se sirve sin argumentario,
- **Cuando** el motivo es que el propio servicio lo retuvo, o que quedó un marcador sin resolver,
- **Entonces** la ficha dice que no se ha podido redactar algo sostenible y **termina en una acción**,
  no en un punto,
- **Y** el resto de la ficha —grupo, avisos, precios y unidades— se sigue viendo,
- **Y cuando** el motivo es que la IA no está disponible, el mensaje es **distinto** y advierte de que
  lo que se ve viene del catálogo,
- **Y cuando** el motivo es que no se generó, el mensaje es **también distinto** y no insinúa una
  caída.

### Escenario 6: Una pieza agotada ofrece alternativas que se pueden vender hoy

- **Dado que** la pieza de la ficha está agotada en ese punto de venta,
- **Cuando** se muestra la ficha,
- **Entonces** se piden sus alternativas automáticamente,
- **Y** sólo se ofrecen las que esa tienda puede vender hoy, en el orden en que llegaron,
- **Y** si sobreviven menos de las pedidas, se dice cuántas hay en vez de rellenar el hueco,
- **Y** si la IA no estaba disponible para esta ficha, **no se pide nada** y se explica por qué.

### Escenario 7: Los cuatro finales de las alternativas se distinguen

- **Dado que** se han pedido alternativas,
- **Cuando** ninguna tiene stock en esa tienda, se dice exactamente eso,
- **Y cuando** la pieza todavía no está preparada en el índice, se dice eso y **no** «la IA no está
  disponible»,
- **Y cuando** la IA no contesta, se dice eso,
- **Y** en ninguno de los tres casos la pantalla muestra un error de aplicación.

### Escenario 8: Un código de aviso desconocido no rompe la fila

- **Dado que** el servicio emite un código de aviso que esta pantalla no conoce —porque el vocabulario
  es cerrado pero versionado,
- **Cuando** se pinta el bloque de avisos,
- **Entonces** ese código aparece con una **etiqueta neutra**,
- **Y** el resto de avisos se pintan con normalidad,
- **Y** en ningún caso se muestra al operario el código en bruto ni se rompe la pantalla.

### Escenario 9: El aviso de talla no compite con los de stock

- **Dado que** la pieza no declara talla, cosa que ocurre en cerca de seis de cada diez fichas,
- **Cuando** se muestra la ficha,
- **Entonces** eso se ve como un **atributo de la pieza**, junto a su SKU, y no como una alerta,
- **Y** los avisos de stock —quedan pocas unidades, alguna variante agotada— se ven como alertas y
  destacan sobre él,
- **Y** el dato **no se oculta** en ningún caso.

### Escenario 10: Pedir demasiadas fichas seguidas se distingue de una caída

- **Dado que** el operario ha agotado su cuota de peticiones de asistencia del minuto,
- **Cuando** abre otra ficha,
- **Entonces** se le dice que espere unos segundos,
- **Y** ese mensaje es **distinto** del de la IA no disponible,
- **Y** el card no reintenta por su cuenta.

### Escenario 11: Fuera de alcance explícito — ni pregunta libre, ni rechazo cortés, ni backend

- **Dado que** este change es sólo de frontend,
- **Cuando** se revisa lo entregado,
- **Entonces** no existe ninguna pantalla para la pregunta libre sin pieza,
- **Y** no hay castellano escrito para los dos códigos de rechazo del enrutador, que estas rutas no
  pueden emitir, sino un test que comprueba que caen en la etiqueta neutra,
- **Y** no se ha tocado `backend/` ni `ai-service/`, y `openapi.json` es idéntico byte a byte,
- **Y** no hay migración de EF Core,
- **Y** el panel de búsqueda asistida de C16 se comporta igual que antes, con su selección para venta
  intacta.

---

## Notas adicionales

**Actor.** **Operador**, y esta vez de verdad. C34 se escribió para el desarrollador del proyecto
porque no había pantalla que enseñar; ésta se acepta mirando el mostrador. El Administrador puede usar
cualquier punto de venta activo, con la misma regla de la búsqueda asistida.

**Encaje con los apuntes del máster.** La caja con preguntas sugeridas es el remedio de S4
(*«la información sobre qué pedir se puede hornear en la interfaz»*), con un matiz propio: aquí la
pregunta es del cliente y literal, así que no hay *prompting* delegado, y la razón para hornear las
sugerencias es la cobertura medida. Las citas cumplen dos de las tres propiedades de S11 —resuelven y
localizan— y la tercera se declara, usando la salida que el propio apunte concede. El aviso de talla
degradado es el mismo argumento de S11 sobre la citación que cansa. Los mensajes de argumentario
retenido siguen a S16: la abstención honesta dice qué haría falta para superarla. **Una desviación
consciente**: no hay *streaming* (S3), porque la puerta de marcadores de C34 necesita el texto entero.

**Limitaciones conocidas que se declaran y no se cierran.**

1. **La pregunta libre sin pieza sigue sin pantalla** (§15.12). Se reescribe la limitación, no se
   borra.
2. **El rechazo cortés de C31 sigue sin pantalla** (§15.13), así que la distinción entre *«el catálogo
   no puede contestar esto»* y *«esto no es una pregunta de joyería»* sólo se demuestra en el arnés.
3. **El card no tiene telemetría.** A diferencia de la búsqueda asistida, que persiste
   `ProductSearchEvent`, ninguna de las tres cosas que el card decide —abrir, preguntar, elegir
   variante— deja rastro. Su uso **no es medible**.
4. **El card estructural no se puede servir sin pagar una generación.** Un `generate=false` en la ruta
   de C34 lo resolvería en unos 10 ms; queda diferido con su medición.
5. **Una pieza que el servicio no puede procesar se ve como «IA no disponible»** (limitación 3 de
   C34): el cuerpo no los distingue y añadir el campo es trabajo de backend.
6. **El bloque de complementarios no existe**, y el §15 del diseño lo declara con su medición.

**Change de OpenSpec por el que se implementa.**
`openspec/changes/add-frontend-assist-card-and-family-disambiguation/`, rama
`c36-add-frontend-assist-card-and-family-disambiguation`.

---

## Tareas

1. **Puerta de entrada**: línea base de la suite de frontend **por nombres de test** (`git stash push
   -u`, `npm run test`, `git stash pop`) — viene roja de fábrica, 113 de 595 el 13 sep—,
   `openspec validate --all --strict` en verde y `sha256` de `ai-service/openapi.json` anotado.
2. **Tipos** de las dos respuestas de C34 en `types/sales-assist.types.ts`, fieles a los DTO de .NET.
3. **Servicio** `sales-assist.service.ts` con las dos llamadas y desenlaces tipados que **nunca
   lanzan**, con 429 como miembro propio, siguiendo `ai-search.service.ts`.
4. **Tabla de copy** `lib/assist-copy.ts`: cinco códigos, etiqueta neutra, cinco mensajes de estado y
   cuatro desenlaces de sustitutos, con sus tests directos.
5. **Componentes del card**: cabecera de la pieza con el atributo de talla, bloque de avisos, bloque de
   argumentario con citas desplegables y `claimScope`, bloque de familia con un botón por miembro,
   caja de pregunta con sugerencias, bloque de sustitutos.
6. **Página y ruta** `/sales/new/assist/:productId` con carga perezosa, POS por estado de navegación,
   selector de respaldo, episodio por visita y guarda de respuestas fuera de orden.
7. **Las tres entradas**: botón en la fila de resultados de C16, botón en la página de venta manual y
   salto tras escanear.
8. **Traspaso a la venta** por estado de navegación, comprobando que la página de venta acepta un
   producto distinto al que ya tenía.
9. **Tests** con Vitest y React Testing Library, envolviendo los proveedores y con los servicios
   mockeados con `vi.mock` —MSW no falla una petición sin *handler*—, sobre el fichero
   `pages/sales/__tests__/cart.test.tsx` como plantilla.
10. **Specs**: capability nueva del card y `## MODIFIED` de `assisted-search-panel`, con
    `openspec validate --all --strict` en verde.
11. **Comprobación con datos reales**: abrir una ficha real, ver el argumentario con precio y stock
    resueltos, una pregunta con citas y un bloque de familia con varias variantes.
    *(Ejecutada el 2026-09-24 en el **entorno local**, no en el demo desplegado: mismo código,
    misma base con el mundo de C10 y el índice de C13, y el mismo `jbg-ai` con credencial real y
    `STUB_MODE=false`. `compose.demo.yaml` tira de imágenes de ECR y de secretos del almacén de
    parámetros, que no están en la máquina de desarrollo. Los tres criterios y sus cifras, en el
    §7 del informe de implementación; la comprobación sobre el demo desplegado queda como el
    §5.6b de `deploy/demo/README.md` para cuando se despliegue.)*
12. **Documentación**: `Documentos/epicas.md`, plan de changes, diseño (§15.12 reescrita, §15.13
    ampliada y la limitación nueva de telemetría), `frontend/README.md`, `openspec/DEFERRED_TASKS.md`
    con las dos entradas nuevas.

---

## Estimaciones y atributos de priorización

| Atributo | Valor |
|---|---|
| Puntos de historia | _Pendiente_ — a fijar en refinamiento |
| Impacto en usuario / valor de negocio | **5/5** — es el único change que pone la capa RAG delante de una persona. Sin él, todo lo que C30a, C30b, C31 y C34 entregaron sólo se demuestra con `curl` y con el arnés |
| Urgencia | **5/5** — **cierra la cadena crítica** `C30a → C34 → C36` y es *nunca se recorta* según el §6 del plan. Lo que enseña es lo que el vídeo del PF tiene que mostrar |
| Complejidad / esfuerzo | **3/5** — ninguna capa nueva, ningún contrato que negociar, ningún componente de Metronic que crear y ningún dato que calcular. La dificultad está en **cuántos estados hay que distinguir sin mentir**: seis de argumentario, cinco códigos, cuatro desenlaces de sustitutos y la degradación |
| Riesgos | **La suite de frontend viene roja de fábrica** y el card arrastra proveedores de contexto (mitigado por la línea base por nombres y por copiar `cart.test.tsx`). **MSW no falla una petición sin *handler***, así que un test puede pasar sin afirmar nada (mitigado con `vi.mock`). **El presupuesto de 10 peticiones por minuto** se agota abriendo fichas (mitigado por una petición por visita y sin reintento). **La espera de 4 a 8 s** con un cliente delante, que no se puede partir sin tocar backend (declarada) |
| Dependencias | **C16** y **C34** archivados. **No se abre a la vez que C16**: comparten página y servicio del frontend. No bloquea a nadie: **C38** depende de C34, no de esta pantalla |

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| **Q-1** | ¿Una capability nueva para el card, o se amplía `assisted-search-panel`? | **Nueva**, `sales-assist-card`: es otra pantalla, con otra ruta y otro contrato. `assisted-search-panel` sólo gana la acción secundaria de la fila |
| **Q-2** | ¿La ficha se abre también desde el detalle de producto del catálogo? | **No** en esta historia: es una pantalla de administración de catálogo y el card necesita un punto de venta. Se deja identificado |
| **Q-3** | ¿Cuántas preguntas sugeridas y cuáles? | **Cinco**, derivadas de las situaciones de mostrador que el corpus cubre: mojar la pieza, piel sensible, limpieza en casa, regalo sin saber la talla y uso en playa o piscina |
| **Q-4** | ¿La pregunta se conserva al volver a abrir la ficha? | **No.** Un episodio por visita, y conservarla invitaría a reenviarla sin querer |
| **Q-5** | ¿El embudo de administrador de C16 se replica en el card? | **No**: el card no tiene embudo que enseñar, y el de sustitutos ya viaja en los contadores de su respuesta. Si se quiere, es una insignia y no una pantalla |
| **Q-6** | ¿Qué pasa si la ruta se abre en frío y el operario tiene varios puntos de venta? | **Selector de respaldo** con la misma regla de rol del panel, y **ninguna petición** hasta que haya punto de venta elegido |
| **Q-7** | ¿El botón de la fila de resultados reporta la selección de telemetría, como hace «Seleccionar para venta»? | **No**: ver la ficha no es elegir la pieza para vender, y contarlo como selección falsearía la métrica de C04. La selección se reporta cuando se vende desde el card |
