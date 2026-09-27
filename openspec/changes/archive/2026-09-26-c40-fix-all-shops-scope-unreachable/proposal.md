## Why

C40 construyó el ámbito «todas las tiendas» entero —tercera clase de `AiCallScope`, tercer perfil de
claims en Python, autorización abierta a operarios y administradores, DTO anulables, hidratación
agrupada por producto y una fila con sus tres estados— **y nadie puede llegar a él**. El selector del
panel enumera sólo tiendas, el efecto de carga fija la primera activa, la búsqueda no se dispara sin
tienda y el botón *Buscar* está deshabilitado. Un tramo completo de un change archivado existe y no se
ejecuta en la aplicación real **ni una vez**.

**Y no falló nada, que es el hallazgo de verdad.** Los 136 escenarios de C40 salieron verdes y su
verificación independiente pasó por encima, porque los tres escenarios del panel están condicionados
con *«WHEN the search is scoped to every point of sale»*: describen qué hace la pantalla **estando** en
ese estado y **ninguno exige que ofrezca la forma de entrar en él**. Peor: el requisito que sí habla del
ámbito dice hoy *«The panel SHALL send a concrete point of sale on every search»*, que desde C40 **es
falso**. La spec no tenía un hueco pasivo — tenía una afirmación contraria a lo que el sistema hace.

Es la **tercera aparición del mismo modo de fallo** en esta familia: el barrido de completitud de C40
emparejaba por nombre y se le escapó un campo sin lector; su verificación arregló aquello y cometió la
variante, auditar **el estado** sin comprobar su **alcanzabilidad**. Los tres son lo mismo —verificar la
pieza en aislamiento en vez del camino hasta ella—, y por eso este change empieza por el requisito y no
por el control: escribir el código sin él reproduce la condición que dejó el hueco.

## What Changes

**En este orden, y el primero es el núcleo.**

1. **El requisito que falta, y la corrección del que miente.** `assisted-search-panel` deja de exigir
   un punto de venta concreto en toda búsqueda y pasa a exigir **que el panel ofrezca, a quien está
   autorizado, una manera explícita de buscar en todas las tiendas, distinguible de haber elegido
   una**, con escenario propio que falle si el control desaparece.
2. **La sonda de disponibilidad acepta la ausencia de tienda.** Hoy `GET /api/ai/search/availability`
   responde **400** sin punto de venta, el panel se pone en blanco a sí mismo y el toggle de respuesta
   asistida **sale deshabilitado y sin motivo que enseñar** — exactamente la avería que C40 vino a
   retirar. El servicio ya sabe contestar ese caso: `IsEnabled` resuelve a `EnabledByDefault` cuando no
   hay tienda. **No es opcional y no es cortable**: sin esto, el punto 3 entrega el ámbito global con la
   ruta generativa apagada.
3. **El control.** Una opción «todas las tiendas» en el selector del panel, y los dos guards relajados
   para que el ámbito sin tienda sea **un estado válido de la pantalla** y no un formulario incompleto.
4. **Los tests a nivel de página.** Los existentes pasan el estado sin tienda **directamente al
   componente**, así que nunca ejercitaron el camino del panel: es la lección del §2 del ticket en forma
   de test. El que de verdad cierra este change es *que el toggle asistido siga habilitado con el ámbito
   global*.

**Restricción que gobierna el punto 3 y no se puede violar:** el centinela del `Select` vive **sólo en
el componente** y se traduce a **ausencia** del campo antes de la petición. Un `Guid.Empty` viajando
sería el comodín por accidente al que C40 dedicó un grupo entero, porque la propiedad que hace seguro
este ámbito es que **la ausencia hace que el prefiltro no se aplique**, no que case con todo.

**Lo que NO cambia:** el endpoint de búsqueda, los DTO y la hidratación, que están hechos y
comprobados; la autorización, que **sigue abierta a operarios y administradores** —la frontera que se
protege es no poder **nombrar** una tienda no asignada, no el ensanchado—; la decisión de que la
cantidad viaje **nula** y no cero; y la telemetría del ámbito global, que sigue siendo tarea diferida de
C40 con su motivo (exigiría migración de EF Core y la spec prohíbe el marcador de posición).

## Capabilities

### New Capabilities

Ninguna. Este change no introduce capacidad nueva: corrige lo que dos specs vivas dicen sobre una que
ya existe.

### Modified Capabilities

- `assisted-search-panel`: **dos requisitos nuevos y tres corregidos.** Los nuevos son **el control** —que
  el panel ofrezca al administrador una manera explícita de entrar en el ámbito global, distinguible de
  haber elegido una tienda, y que **no** la ofrezca al operario, con su motivo escrito— y **el estado del
  toggle de ruta en ese ámbito**, donde la ruta rápida queda deshabilitada con un motivo **de ámbito** y no
  de interruptor. Los corregidos son los tres enunciados que hoy son falsos: el de ámbito, que **afirma que
  el panel envía un punto de venta concreto en toda búsqueda**; el de disponibilidad, que la enuncia **«para
  el punto de venta seleccionado»** y por eso deja la lectura sin resolver y apaga la ruta asistida en
  silencio; y el de la etiqueta de existencias, cuya cláusula *«cambiar de tienda refresca las
  existencias»* nunca describió lo que el panel hace —limpia los resultados— y cuyo test sólo comprobó la
  otra mitad del escenario.
- `ai-free-query-search`: la ruta de disponibilidad SHALL informar hoy **«for one point of sale»**;
  pasa a **aceptar la ausencia** y a reportar el ámbito por defecto, que es lo que el servicio ya
  calcula y el controlador rechaza.

## Impact

**Frontend** (`frontend/src/`) — `pages/sales/assisted.tsx`: opción del selector, los dos guards de
búsqueda, el efecto que lee disponibilidad y el que fija la tienda inicial; `types/ai-search.types.ts`:
`pointOfSaleId` deja de ser obligatorio en la petición del panel;
`pages/sales/__tests__/assisted.test.tsx`: los cinco casos nuevos. La fila
(`assisted-search-result-row.tsx`) **no se toca**: ya tiene sus tres estados y sus tests.

**Backend** (`backend/src/`) — `API/Controllers/AiSearchController.cs`: la acción de disponibilidad
acepta la ausencia de punto de venta; su DTO decide si el identificador viaja nulo o se omite, y **en
ningún caso `Guid.Empty`**. `FreeQuerySearchService` y `AiCallScope` **no se tocan**.

**Specs** — deltas de `assisted-search-panel` y `ai-free-query-search`.

**Sin impacto** en `ai-service/`, en la base de datos, en el contrato congelado `openapi.json` ni en
el despliegue.

**Riesgo abierto que el `design.md` tiene que cerrar:** si el control se limitara sólo al
administrador, habría que **enmendar la spec** en vez de dejarla diciendo una cosa y la pantalla otra.
La respuesta prevista es que se ofrece a los dos, que es lo que `ai-free-query-search` ya autoriza con
su razón escrita.
