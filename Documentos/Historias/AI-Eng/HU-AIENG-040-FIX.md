# HU-AIENG-040-FIX: Dar entrada al ámbito «todas las tiendas», que C40 construyó entero y nadie puede alcanzar

## Formato estándar

**Como** Administrador del sistema,
**quiero** poder buscar en **todas las tiendas** desde el panel de búsqueda asistida, y que al hacerlo la pantalla me diga con qué ruta puede contestarme y con cuál no,
**para** explorar el catálogo completo sin quedarme atado al surtido de una sola tienda — y que el ámbito global que el sistema ya sabe servir deje de ser una capacidad que existe y no se puede usar.

---

## Descripción

C40 construyó el ámbito «todas las tiendas» **completo**: la tercera clase de `AiCallScope` sin centinela ni constructor público, el tercer perfil de *claims* en `auth.py`, la autorización abierta a operarios y administradores con su requisito y sus tests, los DTO anulables, la hidratación agrupada por producto y la fila de resultado con sus tres estados. **Y nadie puede llegar a él.** El selector del panel enumera sólo tiendas, el efecto de carga fija la primera activa, la búsqueda no se dispara sin tienda y el botón *Buscar* está deshabilitado.

Un tramo entero de un change archivado —el grupo 12 de C40, con su frontera de autorización, su cambio de anulabilidad en el contrato interno y su copia— existe y **no se ejecuta en la aplicación real ni una vez**.

### Por qué no falló nada, que es el hallazgo de verdad

Los **136 escenarios de C40 salieron verdes** y su verificación independiente pasó por encima. Los tres escenarios del panel están condicionados con *«WHEN the search is scoped to every point of sale»*: describen qué hace la pantalla **estando** en ese estado y **ninguno exige que ofrezca la forma de entrar en él**.

Y hay algo peor que un hueco pasivo. El requisito que sí habla del ámbito dice hoy, en [`assisted-search-panel/spec.md:88`](../../../openspec/specs/assisted-search-panel/spec.md):

> *The panel SHALL send a concrete point of sale on every search.*

Eso **dejó de ser cierto con C40**. La spec no tiene un hueco: tiene una **afirmación contraria a lo que el sistema hace**. Y `openspec validate --all --strict` seguiría en verde sobre ella, porque valida estructura y no verdad — el mismo mecanismo que dejó pasar las tres specs malformadas de agosto, en su versión peor.

Es la **tercera aparición del mismo modo de fallo** en esta familia: el barrido de completitud de C40 emparejaba por nombre y se le escapó `FreeQuerySearchResponse.searchEventId` sin lector; su verificación arregló aquello y cometió la variante — auditar **el estado** sin comprobar su **alcanzabilidad**. Los tres son lo mismo: *verificar la pieza en aislamiento en vez del camino hasta ella.*

### Lo que la exploración del 2026-09-26 midió, y que reencuadra el ticket

El ticket, escrito el 25 de septiembre, declaraba que el fix eran **dos piezas**. Son **tres**, y la tercera decide el diseño.

**1 · La ruta rápida rechaza el ámbito global — y es la ruta por defecto.** El panel tiene **dos** rutas y `route` arranca en `'semantic'` ([`assisted.tsx:139`](../../../frontend/src/pages/sales/assisted.tsx)), deliberadamente: *«el valor por defecto es la barata»*. El ámbito global sólo se construyó para una de las dos:

|  | `route: semantic` (**por defecto**, barata) | `route: assisted` (generativa) |
|---|---|---|
| **ámbito: una tienda** | ✅ funciona | ✅ funciona |
| **ámbito: todas las tiendas** | ❌ **400** en [`AssistedSearchRequestValidator.cs:29`](../../../backend/src/JoiabagurPV.Application/Validators/AssistedSearchRequestValidator.cs) — `RuleFor(x => x.PointOfSaleId).NotEmpty()` | ✅ acepta la ausencia |

Los DTO lo dicen solos: [`AssistedSearchDtos.cs:18`](../../../backend/src/JoiabagurPV.Application/DTOs/Ai/AssistedSearchDtos.cs) es `Guid PointOfSaleId`; [`FreeQuerySearchDtos.cs:30`](../../../backend/src/JoiabagurPV.Application/DTOs/Ai/FreeQuerySearchDtos.cs) es `Guid?`.

**Síntoma exacto si se implementara el ticket tal cual:** el administrador elige «Todas las tiendas», pulsa *Buscar* sin tocar el toggle, el 400 se mapea a `{kind:'invalid'}` y el panel le escribe **«La búsqueda asistida requiere un punto de venta»** justo debajo del control que se lo acaba de ofrecer. La pantalla contradiciéndose a sí misma es peor que el hueco actual.

**2 · La sonda de disponibilidad rechaza la ausencia, y el panel se queda colgado.** [`AiSearchController.cs:239-250`](../../../backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs) responde **400** sin punto de venta. El panel, sin tienda, pone `availability = null` **y** `settled = false` ([`assisted.tsx:171-176`](../../../frontend/src/pages/sales/assisted.tsx)), y con `settled = false` la insignia renderiza **«Comprobando disponibilidad…» para siempre**. No es sólo el toggle apagado sin motivo: es un estado de carga que no termina nunca.

**3 · `AiFreeQuerySearch__EnabledByDefault` no está puesto en ningún sitio del repositorio.** `compose.demo.yaml` pone dos de los tres interruptores de despliegue y **no el tercero**:

```yaml
AiSearch__EnabledByDefault:      "true"   # lo añadió C17
AiSalesAssist__EnabledByDefault: "true"   # lo añadió C34
#  ↑ falta AiFreeQuerySearch__EnabledByDefault — C40 no lo añadió
```

`AiFreeQuerySearchOptions.EnabledByDefault` es `bool` sin inicializador —`false`—, `EnabledPointOfSaleIds` está vacío y no hay sección `AiFreeQuerySearch` en ningún `appsettings*.json`. **Deducción del código y la configuración, no comprobada en la demo levantada:** hoy `GetAvailability` devuelve `assistedAnswerAvailable: false` con motivo `switched_off` para **todas** las tiendas de la demo, y el toggle asistido está apagado en todas partes. La ironía es que el comentario que hay tres líneas más arriba en ese mismo fichero describe exactamente este fallo: *«la que, al faltar, hizo que el entorno entero pareciera terminado sin estarlo»*.

**4 · Hay una mina dormida en la rama léxica, y la decisión de alcance la deja dormida a propósito.** [`SearchLexicalAsync`](../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/AssistedSearchRepository.cs) ya acepta `Guid? pointOfSaleId` y `Carried(null)` suelta el filtro de tienda — pero **no agrupa por producto**, al contrario que `HydrateAsync`, que sí lo hace y lo documenta. Un producto que tres tiendas llevan volvería **tres veces**, y `BuildResultsAsync:405` hace `rows.ToDictionary(row => row.ProductId)` **incondicionalmente**, en las dos ramas. Resultado: `ArgumentException` → **HTTP 500**. Hoy nadie le pasa `null`, así que no se nota; se activaría en el instante en que la ruta rápida aceptara el ámbito global, y **primero en desarrollo local**, porque con `AiSearch:EnabledByDefault` ausente la ruta degradada es la que corre siempre.

**5 · El caso de uso del dependiente no existe hoy, y eso es lo que justifica el recorte.** El ámbito global **no informa existencias**: cantidad nula, sin nombre de tienda que enseñar, botón de ficha deshabilitado y sin registro en telemetría. Responde *«esta pieza existe en el catálogo»*; **no** responde *«está en la tienda del Puerto»*. Un dependiente que pregunta «¿lo tenemos en otra tienda?» no obtiene respuesta a esa pregunta ni con el ámbito abierto a él: obtiene un catálogo sin existencias y un callejón sin salida. Limitar el control al administrador no declina servir un caso de uso: **declina ofrecer una herramienta que no responde la pregunta que su nombre sugiere.**

**6 · La spec viva ya se contradice sobre el cambio de tienda.** [`assisted-search-panel/spec.md:41`](../../../openspec/specs/assisted-search-panel/spec.md) dice *«Changing the point of sale MUST clear the displayed results»*; la [línea 596](../../../openspec/specs/assisted-search-panel/spec.md) dice *«Changing the selected point of sale MUST refresh the stock figures»*. El código **limpia** ([`assisted.tsx:268`](../../../frontend/src/pages/sales/assisted.tsx)), y el test de la tarea 12.6 de C40 sólo comprobó el segundo `THEN` del escenario, nunca el primero. Es un **tercer `SHALL` falso** en la misma spec, y toca este flujo de lleno: volver de «todas» a una tienda concreta borra los resultados.

### Alcance de esta historia (sí)

- **El requisito que falta y la corrección del que miente**, en `assisted-search-panel`: el de ámbito deja de afirmar que el panel envía un punto de venta concreto en toda búsqueda y pasa a exigir **el control**, con **tres escenarios fallables** — que el administrador lo tenga, que el operario no, y que el ámbito global deshabilite la ruta rápida con su motivo.
- **El requisito de disponibilidad del panel**, que hoy la enuncia *«for the selected point of sale»* y por eso apaga el toggle en silencio, pasa a cubrir también el ámbito sin tienda.
- **La sonda de disponibilidad acepta la ausencia de punto de venta** y devuelve el ámbito por defecto: `Guid?` en el parámetro, en la firma del servicio, en la interfaz y en el DTO de respuesta — y **`Guid.Empty` sigue siendo un 400**, con el mismo texto y el mismo motivo que ya usa el controlador de la consulta libre.
- **La opción «Todas las tiendas» en el selector del panel, sólo para el administrador**, y los dos guards relajados para que el ámbito sin tienda sea un estado válido de la pantalla y no un formulario incompleto.
- **La ruta rápida se deshabilita con motivo propio** cuando el ámbito es global, y la asistida **no**. El componente ya tiene el mecanismo: `RouteOption` acepta `disabled` y `unavailableReason` y emite `data-testid="route-unavailable-<route>"`; falta la propiedad del lado semántico.
- **El callejón sin salida se enuncia al llegar a él**: si el ámbito global está seleccionado y la respuesta asistida está desactivada, el panel dice que el ámbito la necesita y que está apagada, en vez de dejar las dos opciones del toggle muertas sin explicación.
- **La copia nueva y la corregida**: el motivo de la ruta rápida —que no puede leerse como «lo semántico está apagado»—, y la variante de `switched_off`, que hoy dice **«en esta tienda»** y en ámbito global no hay «esta tienda».
- **`AiFreeQuerySearch__EnabledByDefault: "true"` en `compose.demo.yaml`**, como **prerrequisito** y no como mejora: con la ruta generativa apagada el control nace muerto.
- **La delta de `ai-free-query-search`** para el requisito de disponibilidad, que hoy SHALL informar *«for one point of sale»*.
- **Tests a nivel de página** en `frontend/src/pages/sales/__tests__/assisted.test.tsx`, más el caso nuevo de la sonda en .NET.

### Fuera de alcance (no)

- **Extender `POST /api/ai/search` —la ruta rápida— al ámbito global.** Era la alternativa considerada y descartada con motivo: obliga a mover el DTO, el validador, la autorización, el ámbito, la hidratación y el registro de `AssistedSearchService`, que es el servicio más transitado y más probado del árbol, **y a arreglar la agrupación de `SearchLexicalAsync`** antes de que nadie pueda usarlo sin provocar un 500. Con la audiencia reducida al administrador, la objeción económica a fijar la ruta generativa se cae: no son cien dependientes en ráfagas, son consultas ocasionales de administración. **Queda anotado como tarea diferida con su motivo, junto con la mina de la rama léxica.**
- **Endurecer la autorización a sólo administrador.** La spec de `ai-free-query-search` abre el ámbito a operarios y administradores **con su razón escrita**, y su escenario *«An operator may search across every point of sale»* **sigue siendo verdad y no se toca**. La estrechez es **de la pantalla**, y el requisito del panel lo dice explícitamente para que nadie «arregle» el backend por simetría. Tumbar el test `FreeQuery_ForOperatorWithAllPointsOfSale_IsServed` sería más trabajo, no menos, y tiraría trabajo correcto.
- **Que el ámbito global sea el valor por defecto del selector**, ni siquiera para el administrador. El efecto de carga sigue fijando la primera tienda activa.
- **Desagregar existencias por tienda en la respuesta**, que es lo que de verdad responde «¿en qué tienda está?». Es la función que serviría al dependiente y es **otro change**: mueve el DTO de resultado, la hidratación y la fila. Esta historia le deja el hueco nombrado en vez de prometerlo con la copia.
- **Telemetría del ámbito global.** Sigue siendo la tarea diferida de C40 con su motivo: `ProductSearchEvent.PointOfSaleId` es obligatorio e indexado y registrarla exige migración de EF Core, que el encargo de C40 excluía. **Y el recorte al administrador la vuelve marginal**: la línea «Sin registrar: búsqueda en todas las tiendas» del embudo pasa de ser un hueco potencial en los datos de todos los mostradores a un puñado de consultas de administración, así que el motivo para diferirla se refuerza.
- **Reabrir que la cantidad viaje nula y no cero.** Es correcta y es la razón de que el ámbito exista como clase aparte.
- **Un requisito transversal de alcanzabilidad.** Considerado y descartado: *«todo estado que la spec describa DEBE ser alcanzable»* **no produce ningún escenario que un runner pueda fallar**, y sería el mismo modo de fallo un nivel más arriba — un requisito que valida en verde y no cambia nada. La lección va a la documentación de verificación; a la spec van escenarios fallables.
- **La fila de resultado** (`assisted-search-result-row.tsx`). Ya tiene sus tres estados y sus tests, y decide por `result.hasStock === null` y **no** por `pointOfSaleName`, así que no hay que tocarla.
- **`ai-service/`, la base de datos, `openapi.json` y el resto del backend.** El tercer perfil de *claims* de C40 ya acepta un token sin `pos_id` en recuperación y assist; no se mueve nada allí.
- **No es C41.** C41 es la frescura de `ai.pos_projection` y no comparte ni un fichero con esto.

### Decisiones de diseño ya acordadas

Tomadas el **2026-09-26** sobre la exploración del código, en dos rondas: la primera midió el estado y la segunda reencuadró el alcance al limitar el control al administrador.

| # | Decisión | Motivo |
|---|---|---|
| 1 | **El control se ofrece sólo al administrador** | El ámbito no informa existencias, así que no puede cerrar una venta: es una herramienta de exploración del catálogo, y explorar la cadena entera es trabajo de administración, no de un mostrador. No se le quita nada al dependiente, porque hoy el ámbito no responde su pregunta |
| 2 | **La ruta del backend se queda abierta a operarios** | La spec la autoriza con su razón y la frontera que se protege es no poder **nombrar** una tienda ajena, no el ensanchado. `isAdmin` en el cliente es una decisión de producto en la interfaz, **no un control de acceso**, y el requisito del panel lo dice para que el siguiente lector no endurezca el backend «de limpieza» |
| 3 | **El ámbito global fija la ruta generativa**, y la rápida se deshabilita **con motivo propio** | Es la alternativa que no toca `AssistedSearchService` ni activa la mina de `SearchLexicalAsync`. Con audiencia de administración el sobrecoste de la ruta cara deja de ser un problema agregado. Y el motivo tiene que ser **de ámbito**, no de disponibilidad: decir «lo semántico está apagado» sería falso |
| 4 | **La sonda sigue describiendo interruptores; el panel describe alcanzabilidad** | Si la sonda devolviera `false` para lo semántico en ámbito global estaría afirmando que el interruptor está apagado, que es otra cosa y es mentira. Cada uno informa de lo que sabe |
| 5 | **El callejón sin salida se enuncia al llegar**, no se pre-deshabilita la opción | Pre-deshabilitar «Todas las tiendas» exigiría **leer la sonda dos veces** —el ámbito actual y el global—, porque hoy sólo se lee la del seleccionado. Seleccionar el ámbito no emite ninguna petición, así que enunciarlo no desperdicia nada. Es el *safe-completion* de S16: decir qué no se puede y qué haría falta |
| 6 | **El predicado sin tienda es `EnabledByDefault`**, la lectura estrecha | Ya está escrito y razonado en [`FreeQuerySearchService.cs:90`](../../../backend/src/JoiabagurPV.Application/Services/FreeQuerySearchService.cs): *«un despliegue que habilita la función tienda a tienda no la ha habilitado para “todas ellas”»*. **Y la sonda tiene que calcular el mismo predicado que la ruta aplica**, o se recrea la avería original de C40 |
| 7 | **Extraer el predicado** en vez de escribir la rama tres veces | `GetAvailability` vive en `AssistedSearchService` —no en `FreeQuerySearchService`— y llama a `IsEnabledFor(Guid)` sobre **tres** clases de opciones. Escrito una vez, sonda y ruta no pueden derivar |
| 8 | **El centinela del `Select` vive sólo en el componente** y se traduce a **ausencia** antes de la petición | Un `Guid.Empty` viajando sería el comodín por accidente al que C40 dedicó un grupo entero. La propiedad que hace seguro este ámbito es que **la ausencia hace que el prefiltro no se aplique**, no que case con todo. La página ya usa el patrón para la categoría |
| 9 | **`Guid.Empty` sigue siendo 400 también en la sonda** | Ausencia es que la clave no esté; cualquier otra cosa es un valor, y un valor tiene que ser usable. Es la regla de `test_a_blank_pos_claim_is_never_read_as_its_absence` |
| 10 | **`PointOfSaleId` del DTO de disponibilidad pasa a `Guid?`**, sin discriminante nuevo | Se consideró añadir `scope: 'point_of_sale' \| 'all_points_of_sale'`, más autodescriptivo. Se descarta por coherencia: `FreeQuerySearchResponse.PointOfSaleId` ya es `Guid?`, y no hay riesgo de contrato porque `openapi.json` es la frontera con `jbg-ai`, no con la SPA |
| 11 | **«Todas las tiendas» se mantiene como etiqueta**, con aviso al seleccionarla | Coincide con el reporte y con el lenguaje de la spec. El reparo —que promete existencias— se debilita con audiencia de administración, y el aviso lo cierra |
| 12 | **El interruptor de la demo es prerrequisito**, no mejora | Con la decisión 3 la función entera cuelga de `AiFreeQuerySearch__EnabledByDefault`, que no está puesto en ningún sitio. Sin esa línea el administrador se come el callejón sin salida en el primer clic |
| 13 | **Sin requisito meta de alcanzabilidad**; tres escenarios fallables en su lugar | Un requisito que ningún test puede fallar es el mismo modo de fallo un nivel más arriba |
| 14 | **El `SHALL` falso sobre el cambio de tienda se corrige**, y el comportamiento se acepta tal cual | Limpiar los resultados es correcto por coste —la clave de caché incluye la tienda—; lo que hay que retirar es la cláusula que dice que las existencias «se refrescan», que nunca fue verdad y cuyo test nunca la comprobó |

**Cortes que no se reabren:** la ruta de búsqueda semántica no se toca · la autorización no se endurece · la cantidad sigue viajando nula · sin migración de ninguna clase · sin telemetría del ámbito global · `ai-service/` y `openapi.json` intactos · la fila de resultado intacta.

**Referencias:**

- Change: [`c40-fix-all-shops-scope-unreachable`](../../../openspec/changes/archive/2026-09-26-c40-fix-all-shops-scope-unreachable/) · ticket [T-AIENG-040-FIX](../../../openspec/changes/archive/2026-09-26-c40-fix-all-shops-scope-unreachable/ticket.md) · [proposal](../../../openspec/changes/archive/2026-09-26-c40-fix-all-shops-scope-unreachable/proposal.md).
- Historia que origina el defecto: [HU-AIENG-040](HU-AIENG-040.md) · change archivado [`2026-09-25-add-frontend-free-query-panel`](../../../openspec/changes/archive/2026-09-25-add-frontend-free-query-panel/) · su [informe de implementación](../../Proyecto%20Final%20AIEng/informes/c40-implementation-measurements.md), §12.
- Specs vivas afectadas: [`assisted-search-panel`](../../../openspec/specs/assisted-search-panel/spec.md) (dos requisitos modificados) · [`ai-free-query-search`](../../../openspec/specs/ai-free-query-search/spec.md) (el de disponibilidad).
- Precedente de historia correctora: [HU-AIENG-FIX1](HU-AIENG-FIX1.md), que también nace de una spec bien formada y falsa.
- Épica: [EP15](../../epicas.md) · tareas diferidas en [`openspec/DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md).
- Apuntes del máster aplicables: *Un sistema debe saber decir «No lo sé»* (S16) — el derecho a abstenerse con honestidad, que es exactamente lo que el panel debe hacer con el callejón sin salida en vez de callar; y *Tratamiento de regresiones* (S16), que es la disciplina de comparar **nombres** contra la línea base y no recuentos.

---

## Criterios de Aceptación

### Escenario 1: El administrador alcanza el ámbito de todas las tiendas

**Dado que** el administrador abre el panel de búsqueda asistida
**Y** que el selector de punto de venta se le muestra siempre, con las tiendas activas
**Cuando** despliega el selector
**Entonces** ve una opción explícita para buscar en **todas las tiendas**, distinguible de haber elegido una
**Y** al seleccionarla el panel queda en un estado válido: el campo de consulta y el botón *Buscar* siguen utilizables
**Y** el punto de venta preseleccionado al cargar sigue siendo la primera tienda activa, no el ámbito global

### Escenario 2: El operario no ve el control, y eso está especificado

**Dado que** un operario con una o con varias tiendas asignadas abre el panel
**Cuando** despliega el selector, si se le muestra
**Entonces** **no** existe ninguna opción para buscar en todas las tiendas
**Y** el motivo está escrito en el requisito: el ámbito no informa existencias, así que no puede cerrar una venta
**Y** la ruta del backend **sigue sirviendo** el ámbito global a un operario que lo solicite, porque la estrechez es de la pantalla y no de la autorización

### Escenario 3: Seleccionar el ámbito no cuesta una búsqueda

**Dado que** el administrador tiene resultados en pantalla de una búsqueda sobre una tienda concreta
**Cuando** cambia el ámbito a todas las tiendas
**Entonces** **no se emite ninguna petición de búsqueda**, porque el panel sólo busca cuando el operador lo pide
**Y** los resultados mostrados se limpian, en lugar de quedarse describiendo un ámbito que ya no es el seleccionado
**Y** al volver a seleccionar una tienda concreta los resultados se limpian igualmente y hay que buscar de nuevo, que es el comportamiento real y el que la spec pasa a declarar

### Escenario 4: La ruta rápida se deshabilita con su propio motivo, que no es el del interruptor

**Dado que** el ámbito de todas las tiendas está seleccionado
**Cuando** el administrador mira el selector de ruta
**Entonces** la opción de búsqueda rápida está deshabilitada **con un motivo que dice que trabaja sobre una tienda concreta**
**Y** ese motivo **no** dice que la búsqueda semántica esté desactivada, porque sería falso
**Y** la ruta elegida pasa a ser la asistida sin que el administrador tenga que pulsarla

### Escenario 5: El interruptor de la respuesta asistida sigue habilitado en ámbito global

**Dado que** la respuesta asistida está activada
**Y** que el ámbito de todas las tiendas está seleccionado
**Cuando** el panel lee la disponibilidad
**Entonces** la sonda contesta para el ámbito sin tienda en vez de rechazarlo
**Y** la insignia de disponibilidad **sale de «Comprobando disponibilidad…» y enuncia un estado**
**Y** el interruptor de la respuesta asistida queda **habilitado**, no deshabilitado y sin motivo que enseñar

### Escenario 6: Sin respuesta asistida, el callejón sin salida se dice en voz alta

**Dado que** la respuesta asistida está desactivada, por interruptor
**Y** que el ámbito de todas las tiendas está seleccionado
**Cuando** el administrador mira el panel
**Entonces** el panel enuncia que la búsqueda en todas las tiendas usa la respuesta asistida y que está desactivada
**Y** no deja las dos opciones del selector de ruta deshabilitadas sin explicación
**Y** el texto del motivo no afirma «en esta tienda», porque en este ámbito no hay una tienda de la que hablar

### Escenario 7: La sonda acepta la ausencia y rechaza el valor en blanco

**Dado que** un llamante autenticado consulta la disponibilidad
**Cuando** **omite** el punto de venta
**Entonces** la respuesta es **200** y reporta el ámbito por defecto de los interruptores, el mismo que la ruta de búsqueda aplicaría
**Y** el identificador de punto de venta viaja **nulo** en la respuesta, nunca como un identificador en blanco
**Cuando** en cambio envía un punto de venta **en blanco**
**Entonces** la respuesta es **400**, con el mismo criterio que ya aplica la ruta de consulta libre: la ausencia es que la clave no esté, y cualquier otra cosa es un valor que tiene que ser usable

### Escenario 8: El centinela del desplegable no sale al cable

**Dado que** la opción de ámbito global necesita un valor en el componente de selección
**Cuando** el administrador lanza una búsqueda con ese ámbito
**Entonces** la petición viaja **sin el campo de punto de venta**, no con un identificador en blanco
**Y** el prefiltro de disponibilidad **no se aplica**, en lugar de casar con todas las tiendas
**Y** ninguna petición del panel —búsqueda ni disponibilidad— lleva un identificador de punto de venta en blanco

### Escenario 9: La fila dice lo que sabe y no ofrece lo que no puede

**Dado que** una búsqueda en todas las tiendas ha devuelto resultados
**Cuando** el administrador los mira
**Entonces** la etiqueta de existencias dice que hay que seleccionar una tienda para leerlas, y **no muestra un cero**
**Y** no nombra ninguna tienda
**Y** la acción que abre la ficha de venta está deshabilitada
**Y** cada producto aparece **una sola vez**, aunque varias tiendas lo lleven

### Escenario 10: El entorno de demostración puede enseñarlo

**Dado que** el ámbito global se sirve por la ruta de respuesta asistida
**Y** que su interruptor no está declarado en ningún fichero de configuración ni en el compose de la demo
**Cuando** se despliega el entorno de demostración
**Entonces** el interruptor de la consulta libre está activado, junto a los otros dos que ya lo están
**Y** el ámbito global es utilizable de extremo a extremo allí, en lugar de presentar un control que se apaga en el primer clic

### Escenario 11: Fuera de alcance explícito

**Dado que** esta historia da entrada a un ámbito que ya existe
**Cuando** se revisa el entregable
**Entonces** la ruta de búsqueda rápida **no** acepta el ámbito global, y ese corte está declarado con su motivo y con la mina de la rama léxica anotada
**Y** la autorización **no** se endurece: el test que sirve el ámbito a un operario sigue en verde
**Y** no hay desagregación de existencias por tienda, ni telemetría del ámbito global, ni migración de ninguna clase
**Y** `ai-service/openapi.json` no tiene diff
**Y** la fila de resultado no tiene diff
**Y** el ámbito global no es el valor por defecto de ningún selector

---

## Notas adicionales

- **Actor: el Administrador, y es la primera vez en esta familia.** C21 y C22 fueron del Operador, C34 y C36 le dieron la ficha, C40 le dio la consulta libre. Esta historia es de administración porque lo que entrega es exploración de catálogo, no venta — y decirlo así es lo que evita prometer con la copia una respuesta que el sistema no da.

- **El valor no es «más búsqueda»: es que una capacidad construida deje de ser inalcanzable.** C40 pagó el grupo 12 entero —ámbito, *claims*, autorización, anulabilidad, hidratación agrupada, fila de tres estados— y el retorno fue cero porque faltaba un `SelectItem` y sobraba un `NotEmpty`. Los criterios están escritos sobre la alcanzabilidad a propósito.

- **Esta historia contradice su propio ticket en dos puntos, y ambos con el código delante:** que el fix son dos piezas y no tres —falta la ruta rápida—, y que la sonda es «un cambio de tres líneas en el controlador», cuando `GetAvailability` vive en otro servicio y consulta tres interruptores distintos. Es el precedente de FIX1 repitiéndose: la exploración refuta lo escrito antes porque mide contra el árbol vivo.

- **`design.md` es obligatorio en el change.** Hay al menos seis decisiones con alternativa real y coste asimétrico: quién ve el control, qué hace el toggle de ruta, cómo se enuncia el callejón sin salida, qué reporta la sonda para lo semántico, la forma de la respuesta sin tienda y si el interruptor de la demo entra. Dos de ellas —la audiencia y el alcance del backend— contradicen el ticket original.

- **La prueba que de verdad cierra el change** es la del escenario 5: el interruptor de la respuesta asistida **habilitado** con el ámbito global. Es el hallazgo que dimensiona el fix y el único cuyo fallo devuelve el panel al estado que C40 vino a retirar.

- **Los tests existentes no cubrían esto, y no era descuido.** Los de la fila pasan `pointOfSaleName` y el `hasStock` nulo **directamente al componente** ([`assisted-search-result-row.test.tsx:167`](../../../frontend/src/components/sales/__tests__/assisted-search-result-row.test.tsx)), así que nunca ejercitaron el camino del panel. Es la misma lección del hallazgo central en forma de test: el componente estaba probado, el camino hasta él no.

- **Cero tests existentes invertidos.** Es consecuencia directa de limitar el control al administrador: el selector ya se renderiza siempre para ese rol, así que `should hide the point of sale selector when the operator has a single assignment` **no se toca** y el requisito *«A single assignment needs no choice»* se queda como está. Con el control abierto a operarios habría habido que invertir los dos.

- **Las dos suites vienen rojas de fábrica** y se comparan por **nombres** contra la línea base del propio commit: frontend ~113-114 de 729 en 14 ficheros, backend ~50. El conjunto rota dentro de clases y ficheros conocidos. Detalle en [`CLAUDE.md`](../../../CLAUDE.md), [testing-frontend.md](../../testing-frontend.md) y [testing-backend.md](../../testing-backend.md).

- **`tsc --noEmit` filtrado es puerta obligatoria en este change**, porque mueve un tipo: `pointOfSaleId` deja de ser obligatorio en la petición del panel y `AiSearchAvailability.pointOfSaleId` pasa a admitir nulo. C40 se comió un commit entero con `npm run build` en verde sobre un error de tipos, porque Vite transpila con esbuild y esbuild descarta los tipos sin mirarlos.

- **Limitación a declarar**, hermana de las de C34 y C40: el ámbito «todas las tiendas» **sólo se sirve por la ruta de respuesta asistida** y **no se registra en telemetría**, así que su uso no es medible y su coste por consulta es el de la ruta cara.

- **El hueco que esta historia nombra y no cierra:** responder «¿en qué tienda está?» exige desagregar existencias por tienda en la respuesta, y eso mueve el DTO de resultado, la hidratación y la fila. Esta historia le sube el precio a no hacerlo y le entrega la primera prueba de que hace falta.

---

## Tareas

1. Completar los artefactos OpenSpec del change `c40-fix-all-shops-scope-unreachable`: `proposal` (hecho), **`design.md` obligatorio**, `specs` (deltas de `assisted-search-panel` y `ai-free-query-search`) y `tasks`.
2. **Deltas de spec, primero y es el núcleo.** `assisted-search-panel`: corregir el `SHALL` falso del requisito de ámbito y añadirle el control con sus tres escenarios fallables; ampliar el requisito de disponibilidad al ámbito sin tienda; retirar la cláusula falsa sobre el refresco de existencias al cambiar de tienda. `ai-free-query-search`: el requisito de disponibilidad acepta la ausencia.
3. **Backend · la sonda.** `Guid?` en el parámetro del controlador, en `IAssistedSearchService.GetAvailability`, en su implementación y en `AiSearchAvailabilityResponse.PointOfSaleId`; `Guid.Empty` sigue devolviendo 400 con el texto de la consulta libre.
4. **Backend · el predicado, escrito una vez.** Extraer `IsEnabledFor(this <opciones>, Guid?)` para las tres clases de configuración, de modo que sonda y ruta no puedan derivar, y que el ámbito sin tienda resuelva a `EnabledByDefault` en las tres.
5. **Frontend · tipos.** `pointOfSaleId` deja de ser obligatorio en la petición del panel y `AiSearchAvailability.pointOfSaleId` admite nulo; el servicio omite el parámetro en lugar de enviarlo vacío.
6. **Frontend · el control.** Opción de ámbito global en el selector, condicionada al administrador, con el centinela viviendo sólo en el componente; relajar el guard de `runSearch` y el `disabled` del botón *Buscar*; que el efecto de disponibilidad consulte la sonda también sin tienda en vez de ponerse en blanco.
7. **Frontend · el toggle de ruta.** Propiedad de indisponibilidad del lado semántico, aprovechando el `RouteOption` que ya acepta `disabled` y `unavailableReason`; fijar la ruta asistida cuando el ámbito es global.
8. **Frontend · la copia.** Motivo de la ruta rápida deshabilitada; aviso de consecuencia al seleccionar el ámbito global; variante de `switched_off` sin «en esta tienda»; enunciado del callejón sin salida.
9. **Tests de página** en `assisted.test.tsx`: la opción existe para el administrador y no para el operario; seleccionarla no emite petición; la ruta rápida queda deshabilitada con su motivo; **el interruptor asistido sigue habilitado**; la fila deja de nombrar tienda y deshabilita la ficha; no viaja ningún identificador en blanco; el callejón sin salida se enuncia.
10. **Tests .NET de la sonda:** sin punto de venta devuelve 200 con el ámbito por defecto; con punto de venta en blanco devuelve 400; el predicado sin tienda coincide con el que la ruta de búsqueda aplica.
11. **`compose.demo.yaml`:** añadir `AiFreeQuerySearch__EnabledByDefault: "true"` con su comentario de clase, junto a los otros dos.
12. **Anotar en `openspec/DEFERRED_TASKS.md`** las dos tareas diferidas con su motivo: extender la ruta rápida al ámbito global, y la agrupación que le falta a la rama léxica para que no provoque un 500 cuando alguien le pase la ausencia.
13. **Comprobación manual** en el entorno levantado, por la interfaz: con administrador, seleccionar el ámbito global, comprobar el estado del toggle y de la insignia, lanzar una búsqueda y verificar la fila; con operario, comprobar que la opción no existe.
14. Actualizar [`Documentos/epicas.md`](../../epicas.md) (EP15), y el `frontend/README.md` y `backend/README.md` en lo que toque a la sonda y al ámbito.
15. `openspec validate --all --strict` en **0 failed**, `dotnet build` y `npm run build` en verde, y `tsc --noEmit` filtrado a los ficheros propios **sin errores nuevos**.

---

## Estimaciones y atributos de priorización

- **Puntos de historia:** _Pendiente_
- **Impacto en usuario / valor de negocio:** **3** — no desbloquea ninguna arista del grafo de changes y su audiencia es el administrador, no el mostrador. Lo que recupera es el retorno de un tramo entero ya pagado por C40, que hoy es cero, y retira de la spec viva una afirmación falsa que el validador daría por buena.
- **Urgencia (mercado / feedback):** **4** — no está en la cadena crítica, pero **una spec viva miente ahora mismo** y cada change que se archive encima consolida esa mentira. Y C38 viene detrás sobre la misma zona.
- **Complejidad / esfuerzo:** **2** — sin algoritmo, sin migración, sin pantalla nueva, sin movimiento de contrato con `jbg-ai`. Lo que hay es una decisión de diseño con tres alternativas reales, tres requisitos de spec que hay que corregir en vez de añadir, un predicado que debe escribirse una sola vez y una cadena de copia que no puede mentir.
- **Riesgos y dependencias:**
  - **La tentación de añadir sólo el `SelectItem`.** Entregaría el ámbito global con **la ruta por defecto respondiendo 400** y el mensaje del servidor pintado debajo del control que lo ofrece. Es la avería que este change viene a retirar, reproducida.
  - **La tentación de endurecer la autorización «por coherencia»** con el requisito nuevo del panel. Contradiría `ai-free-query-search`, que la abre con su razón escrita, y tumbaría un test correcto de C40. **El requisito del panel tiene que decir explícitamente que la ruta sigue abierta.**
  - **La tentación de extender la ruta rápida «ya que estamos».** Arrastra `AssistedSearchService` entero **y** la agrupación que le falta a `SearchLexicalAsync`, sin la cual la ruta degradada con ámbito global es un **HTTP 500** — y la degradada es la que corre en local, donde `AiSearch:EnabledByDefault` no está puesto.
  - **Olvidar el interruptor de la demo** deja el control muerto en el primer clic, porque la decisión 3 hace que la función cuelgue de él. Es prerrequisito, no mejora.
  - **Que la sonda y la ruta calculen predicados distintos.** Es la avería original de C40 —la pantalla dice una cosa y la ruta hace otra— y por eso el predicado se extrae en vez de escribirse tres veces.
  - **`openspec validate --all --strict` no detecta el defecto que este change corrige.** Las tres specs afectadas están **bien formadas**; lo que falla es su contenido. La puerta de verdad es la comprobación manual de la tarea 13.
  - **La regla de la primera línea física** del validador: la descripción que sigue a `### Requirement:` se lee **sólo hasta el primer salto**, así que en las deltas va en una línea larga sin ajustar a 90 columnas.
  - **Zona compartida con C38**, que viene detrás sobre la misma familia. No se abren en paralelo.
  - **Dependencia de entorno para la tarea 13:** `AiFreeQuerySearch__EnabledByDefault` y `AiSalesAssist__EnabledByDefault` activos, y credencial real del proveedor si se quiere ver prosa. En esta máquina las llamadas reales al proveedor necesitan además `SSL_CERT_FILE` apuntando a un PEM con la raíz de Norton, según [`CLAUDE.md`](../../../CLAUDE.md).

---
