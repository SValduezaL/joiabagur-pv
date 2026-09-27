# C36 — informe de implementación: la ficha de venta, y tres cosas que el árbol refutó

**Change:** `add-frontend-assist-card-and-family-disambiguation` (C36) · **Fecha:** 2026-09-22
**Rama:** `c36-add-frontend-assist-card-and-family-disambiguation`, derivada de `4552bcf`
**Línea base del apply:** `2b49685`, árbol limpio · **Zona:** `frontend/src/`

Este informe recoge **lo que se midió durante el apply**, no lo que se planeó. Las cifras de
exploración —el 31,2 % del bloque de familia, el 58,3 % de la falta de talla, el 98,3 % de las
etiquetas distinguibles— están en
[`c36-exploration-decisions.md`](c36-exploration-decisions.md) y **no se vuelven a medir aquí**: son
sobre la base de datos y este change no la toca.

Lo que sí se mide aquí es la suite, las puertas, y **cuatro puntos en los que la realidad del árbol no
coincidía con los artefactos** — el cuarto encontrado el 2026-09-24 al comprobarla con datos reales,
y era un defecto propio. Es el undécimo change consecutivo del que se puede decir eso.

---

## 1 · Las puertas

| Puerta | Al abrir (`2b49685`) | Al cerrar | Veredicto |
|---|---|---|---|
| Suite de frontend | **113 o 114 fallos de 597** (§2.1) | **113 fallos de 729**, 14 de 54 ficheros | **Cero nombres nuevos** |
| `npm run build` | verde, 49,59 s | verde, 1 m 17 s | ✅ |
| `openspec validate --all --strict` | 61 passed, 0 failed | **61 passed, 0 failed** | ✅ |
| `sha256` de `ai-service/openapi.json` | `d8d48f87…c2b875` | `d8d48f87…c2b875` | **idéntico** |
| Zona, excluyendo los dos ficheros tocados a propósito | — | vacío | ✅ |
| Cobertura del código nuevo (≥ 70 %) | — | **84–100 % sentencias**, 70–100 % ramas | ✅ |

El contrato congelado: `d8d48f87b279d45d22bce80a67c4fd51caef6e679363c413f5b697c99ec2b875`, el mismo
al abrir y al cerrar. `git diff --name-only 2b49685..HEAD | grep -v "^frontend/\|^openspec/\|^Documentos/\|^CLAUDE.md\|^backend/README.md"`
no devuelve nada: **`backend/`, `ai-service/`, `terraform/` y `.github/` no se tocan**, y no hay
migración de EF Core.

La ruta entra con **carga perezosa**: el paquete la emite como `assist-<hash>.js`, aparte del
`index`.

### La comparación válida, que es por nombres

Reproducible con el informador JSON, que es lo que permite comparar conjuntos y no recuentos:

```sh
cd frontend
npx vitest run --reporter=json --outputFile.json=<destino>
# y después, el conjunto de assertionResults[].status === 'failed'
```

```
baseline : 114 failing of 597
close    : 113 failing of 729

NEW failing names (must be 0): 0

names that STOPPED failing: 1
   - src/pages/admin/__tests__/family-review.test.tsx ::
     family review screen should create a family with its members from the review screen
```

**Subconjunto estricto**: ni un fallo nuevo, y uno que dejó de fallar sin que nadie tocara su
fichero. Es el tercer caso que este proyecto registra —tras C16 y C18b— y confirma la regla de
[testing-frontend.md](../../testing-frontend.md): **el número no sirve, el conjunto de nombres sí**.

**132 tests nuevos**, todos verdes (597 → 729). Seis ficheros nuevos, ninguno construido sobre uno
que ya viniera rojo.

### La cobertura, medida al verificar (2026-09-24)

El apply no la midió y el informe salió sin la cifra, que es lo que la verificación reprochó: el
umbral del proyecto —70 % sentencias, líneas y funciones, 60 % ramas— está en
[`project.md`](../../../openspec/project.md) y codificado en `frontend/vite.config.ts`. Medida sobre
los seis ficheros de test nuevos:

| Fichero | Sentencias | Ramas | Funciones | Líneas |
|---|---|---|---|---|
| `lib/assist-copy.ts` | **100** | **100** | **100** | **100** |
| `services/sales-assist.service.ts` | 95,65 | 70,58 | 100 | 100 |
| `pages/sales/assist.tsx` | 92,72 | 89,77 | 100 | 95,87 |
| `components/sales/sales-assist-card/` | **91,04** | **82,29** | **95,83** | **95,16** |
| ├ `warnings-block.tsx` | 100 | 100 | 100 | 100 |
| ├ `pitch-block.tsx` | 100 | 93,75 | 100 | 100 |
| ├ `piece-header.tsx` | 100 | 81,25 | 100 | 100 |
| ├ `question-box.tsx` | 90,47 | 80 | 100 | 100 |
| ├ `substitutes-block.tsx` | 88,23 | 76,92 | 100 | 87,5 |
| ├ `family-block.tsx` | 84,61 | 79,16 | 80 | 91,66 |
| └ `index.ts` | 0 | 0 | 0 | 0 |

Todo lo que lleva lógica pasa el umbral, y la mayoría con holgura. **El único 0 % es el `index.ts` del
barril**: quince líneas de `export ... from`, que `v8` no cuenta como ejecutadas porque el empaquetador
las resuelve en tiempo de importación. No es lógica sin probar, y por eso no se persigue.

---

## 2 · Las cuatro refutaciones

### 2.1 · La línea base de la suite no es 113 de 595, y la cifra **oscila por orden de ejecución**

**Lo que decían los artefactos.** `CLAUDE.md`, el design y el ticket: *«113 fallos de 595, en 14 de
48 ficheros»*, medidos el 13 de septiembre al cerrar C28. El design añade que *«este conjunto de
nombres es estable entre ejecuciones»*.

**Lo medido el 22 de septiembre**, sobre el mismo árbol limpio: **114 de 597, en 15 de 48**. Dos
tests de más, un fallo de más, un fichero rojo de más.

**Y lo que la comparación de cierre explica, que es lo interesante.** El fichero de más es
`pages/admin/__tests__/family-review.test.tsx`, que el informe de C18b dejó con sus 19 verdes. Su
único fallo —`should create a family with its members from the review screen`— **falló en la línea
base y pasó al cierre**, sin que este change tocara ni ese fichero ni el suyo de producción.

Es decir: **no es una regresión acumulada, es un test dependiente del orden**. La suite creció en 6
ficheros y eso desplazó el orden de ejecución, que es exactamente el fenómeno que
`testing-frontend.md` documenta para `assisted.test.tsx` en C16 y C18b.

**Y la verificación del 2026-09-24 lo confirmó por la vía dura: regeneró la línea base** en un
worktree sobre `2b49685` y obtuvo **113 fallos en 14 ficheros, no 114 en 15** — el test de
`family-review` pasó también allí, así que en esa pasada el conjunto de nombres de la línea base y el
del cierre son **idénticos**, con cero nuevos y cero arreglados. Mismo commit, mismo código, dos
respuestas: la conclusión de este apartado se refuerza en vez de contradecirse, y la consecuencia
práctica es más fuerte de lo que estaba escrito — **el recuento no sirve ni siquiera como línea base,
sólo el conjunto de nombres**. El 114 de 597 de la tabla del §1 es la cifra de la pasada del apply, no
una propiedad del commit.

**Consecuencia para la documentación.** La afirmación de que *«aquí el conjunto de fallos sí es
estable entre ejecuciones»* es **demasiado fuerte**: hay al menos un test dependiente del orden en el
frontend, igual que en el backend, sólo que uno y no un puñado. Lo que no cambia es el método: la
comparación por nombres sigue dando una respuesta binaria y útil —cero nombres nuevos—, que es para
lo que existe.

### 2.2 · `scan.tsx` no tiene punto de venta, así que no puede llevar ninguno

**Lo que decía el ticket.** La tabla de entradas del §*Ruta y entradas*: *«`scan.tsx` · Salto tras
resolver el código · `{pointOfSaleId}` del escaneo»*.

**Lo medido:**

```sh
grep -c -i "pointofsale\|pos" frontend/src/pages/sales/scan.tsx   # → 0
```

Cero coincidencias sobre `2b49685`. La página **nunca ha tenido** punto de venta: no llama a
`pointOfSaleService`, no lo guarda en estado y no lo pasa en el traspaso a la caja —`new.tsx` elige
el primero de la lista al recibir el producto—. De las tres entradas, **sólo dos pueden llevar uno**.

**Cómo se resolvió, y por qué no hizo falta cambiar el diseño.** La entrada de escaneo navega **sin
estado** y la ficha cae en su selector de respaldo por rol, que es exactamente lo que la Q-6 del
design manda para una ficha abierta en frío. **El ticket se corrige**, en el mismo commit que el
código.

**Y la spec también, al verificar (2026-09-24).** El apply decidió no tocarla, razonando que su
escenario —*«se abre para el punto de venta de esa venta»*— era vacuo en el escaneo, porque esa venta
todavía no tiene punto de venta elegido. La verificación lo rechazó, y con razón: archivar convierte
esa delta en spec viva, y un `THEN` **insatisfacible** se queda como verdad del proyecto — el mismo
patrón que las tres specs malformadas que sobrevivieron hasta el 2026-08-06. El escenario ahora dice
que la ficha **abre con el selector por rol, porque el flujo de escaneo aún no ha elegido tienda**, y
el cuerpo del requisito nombra cuáles de las tres entradas llevan una y cuáles no. Es lo que el test
afirmaba desde el principio: `expect(navigate).toHaveBeenCalledWith('/sales/new/assist/prod-9')`, sin
estado, y sin punto de venta.

### 2.3 · Cambiar de punto de venta con la ficha servida no pedía nada, y dejaba precios de una tienda bajo el nombre de otra

**Cómo apareció.** Escribiendo el test de la guarda de orden. Lo escribí sobre dos preguntas seguidas
y **no puede ocurrir**: la caja de pregunta se deshabilita mientras una está en vuelo, que es en sí
mismo una guarda del presupuesto de diez por minuto. Al buscar el camino por el que sí pueden
desordenarse dos respuestas apareció el hueco.

**El defecto.** La guarda de una petición por visita era un booleano (`askedRef`). Una vez servida la
ficha, cambiar de tienda en el selector —posible siempre que la ruta se abra en frío— **no emitía
ninguna petición**: la pantalla seguía enseñando el precio, las unidades y las variantes de la tienda
anterior bajo el nombre de la nueva.

**El arreglo.** `askedForRef` guarda **el punto de venta** en vez de un booleano. Las tres cosas que
la spec prohíbe —renderizar de nuevo, que llegue la respuesta, que algo falle— lo dejan igual y no
piden nada; que el operario nombre otra tienda es un **acto explícito**, como navegar aquí, y la ficha
que pide es otra ficha. Los sustitutos se limpian cuando la pieza nueva sí tiene existencias.

**No contradice la spec**, que prohíbe emitir otra petición *«como consecuencia de re-renderizar, de
que llegue la respuesta, o de cualquier fallo»*. Un cambio de tienda no es ninguna de las tres, y las
tres se comprobaron una a una sobre el código de la guarda.

**Pero la spec tampoco lo amparaba, y eso se corrigió al verificar (2026-09-24).** No contradecirla no
es lo mismo que estar en ella: el titular del requisito decía *«exactly one … per visit»*, la pregunta
del cliente tenía su propio permiso en un requisito aparte, y el cambio de tienda —con test propio,
`should ask again when the operator names a different point of sale`— no aparecía en ninguno. Archivar
habría dejado un comportamiento probado y sin requisito que lo describa. El requisito pasa a llamarse
*«… on entry to the card … and only an explicit act issues another»*, gana el párrafo que nombra el
cambio de tienda como el segundo de los dos únicos actos que piden otra ficha, y gana el escenario
*«Naming a different point of sale asks again»*. **La conducta no cambia; lo que cambia es que ahora
está escrita.**

### 2.4 · La cabecera de la ficha decía «en esta tienda», y el defecto era mío

**Encontrado el 2026-09-24**, al comprobar la ficha con datos reales. La cabecera ya quería pintar
el nombre de la tienda:

```tsx
{piece.quantityAtPointOfSale} en {pointOfSaleName || 'esta tienda'}
```

Pero la página sólo carga la lista de puntos de venta cuando se abre **en frío**:

```tsx
if (navigatedPointOfSaleId) return;   // ...así que posName se quedaba en ''
```

Cuando el punto de venta llega por estado de navegación —**el camino normal**, y el de las tres
entradas— el nombre no se pedía nunca y la etiqueta caía al literal. La pantalla decía *«24 en esta
tienda»* teniendo el identificador de la tienda en la mano.

**El arreglo** es un efecto que lee esa única tienda con `getPointOfSale(id)`: una lectura, sin IA,
y **con el fallo invisible a propósito** — el nombre es lo que la frase preferiría decir, no algo de
lo que la ficha dependa. El selector sigue oculto porque su guarda es `!navigatedPointOfSaleId` y no
la longitud de la lista, cosa que ahora tiene test propio.

**Por qué importa más de lo que parece:** *«esta tienda»* es ambiguo en cuanto hay más de una en
juego, y una cifra de existencias ambigua es de las que cuestan una venta. Con «Todos los puntos de
venta» a la vista en C40, sólo iba a empeorar.

Tres tests nuevos, y los tres caen al romper la guarda a mano.

### 2.5 · Y una menor: `tasks.md` tiene 50 tareas, no 45

El commit de los artefactos dice *«tasks: 9 grupos, 45 tareas»*. Contadas: 4 + 3 + 3 + 7 + 6 + 4 + 12
+ 6 + 5 = **50**. No cambia nada del trabajo; se anota porque el recuento se cita en el commit.

**Y un segundo recuento del mismo mensaje, encontrado al verificar:** dice *«11 requisitos y 40
escenarios para la ficha»*. Contados: **37** —38 tras el escenario que la verificación añadió en el
§2.3—. El requisito sí son 11. Tampoco cambia nada del trabajo, y se anota por lo mismo: el mensaje
de un commit no se reescribe, así que la cifra correcta tiene que vivir aquí.

---

## 3 · Las mutaciones de control

Un test verde que nunca se ha visto fallar no demuestra nada. Las tres invariantes que más fácilmente
se romperían en silencio se rompieron a mano, una a una, y se revirtieron con `git checkout`.

| Mutación | Qué se rompió | Tests que caen | ¿Los correctos? |
|---|---|---|---|
| **A · la preselección** | `data-selected="true"` en la fila del ancla | **1** | sí: `should preselect no member when the group has several` |
| **B · la etiqueta neutra** | `warningLabel` devuelve el código en bruto | **5** | sí: 3 del módulo y **2 de la pantalla** |
| **C · el disparador de sustitutos** | `hasStock` → `pitchStatus === 'withheld_out_of_stock'` | **8** | sí: el bloque entero, encabezado por `should trigger on the anchored member stock and not on the state of the argument` |

**Mutación A** deja verdes los otros seis tests de familia, que es lo correcto: no toca ni el orden,
ni el botón por fila, ni la degradación al SKU. La granularidad es la que se buscaba.

**Mutación B** cae en los **dos niveles**, que es la prueba de que la regla no sólo está en el módulo
sino que llega a la pantalla.

**Mutación C** merece una nota porque su resultado es contraintuitivo. Cae también
`should not request substitutes when the card is degraded`, aunque con la mutación **tampoco** se
piden: el retorno temprano ocurre antes de poner el estado `not-requested`, así que la ficha se calla.
El test no comprueba sólo que no se pida — comprueba que **se explique por qué**. Callarse leería como
una pieza sin alternativas, que es una afirmación distinta y falsa.

Tras revertir las tres: **132 de 132 en verde** en los seis ficheros nuevos, y `git status` limpio.

---

## 4 · Trazabilidad: los once escenarios de la HU a tests concretos

Cada escenario de [HU-AIENG-036](../../Historias/AI-Eng/HU-AIENG-036.md) contra los tests que lo
sostienen. Ninguno se apoya en un solo test.

| # | Escenario | Tests |
|---|---|---|
| **1** | La ficha se abre desde donde el operario ya está, y pide una sola vez | `should reach the card from the result row scoped to the panel point of sale` · `should reach the card for the resolved product` · `should offer the sale card for the selected product` · `should issue exactly one assist request per visit` · `should not issue another request when the card re-renders` · `should show a loading state rather than an empty screen while the request is in flight` · `should not retry a failed assist request` · `should offer an explicit retry when the request failed` |
| **2** | Una familia con varias tallas obliga a elegir antes de vender | `should require variant confirmation when family has multiple members` · `should preselect no member when the group has several` · `should carry the chosen member to the manual sale page` · `should mark the anchored member as the one in hand` · `should mark a member with no stock` · `should restore the direct action when the group carries exactly one member` · `should accept a product identifier different from the one it already had` |
| **3** | La pregunta del cliente se responde citando de dónde sale | `should issue exactly one further request when a question is asked` · `should fill and send in one act from a suggested question` · `should never put the question in the url` · `should send the question in the body when one is asked` · `should reject a question over five hundred characters before sending` · `should accept a question of exactly five hundred characters` · `should render citations when pitch has sources` · `should show the snippet when a citation is expanded` · `should mark an establishment claim differently from a general one` *(×2: módulo y pantalla)* · `should tell the operator to confirm an establishment claim in store` |
| **4** | Lo que la documentación no cubre se dice, no se disimula | `should translate knowledge_not_covered into Spanish a counter can read` · `should show a known warning code in Spanish and never the raw code` · `should hide citations when the argument was withheld` · `should show citations only when the argument was delivered` |
| **5** | Un argumentario retenido dice qué hacer, y se distingue de la IA caída | `should say what to do next when the argument is withheld` *(×2)* · `should tell a degraded card from one whose argument was not generated` *(×2)* · `should keep the two withheld states distinguishable although they share a text` · `should share one text between the two withheld states` · `should end every message for a state without an argument in an action` · `should render the six states as six distinguishable documents` · `should render the six states as five distinct renderings` |
| **6** | Una pieza agotada ofrece alternativas que se pueden vender hoy | `should show substitutes block when selected product is out of stock` · `should request no substitutes when the anchored member has stock` · `should trigger on the anchored member stock and not on the state of the argument` · `should display the substitutes in the order received` · `should declare a short substitutes page instead of padding it` · `should not request substitutes when the card is degraded` · `should announce the alternatives when the piece is out of stock` |
| **7** | Los cuatro finales de las alternativas se distinguen | `should tell the four substitute outcomes apart` *(×2: módulo y pantalla)* · `should say a piece is not ready yet rather than calling it an outage` *(×2)* · `should say nothing has stock when the service answered and nothing survived` · `should treat the four substitute outcomes as answers and not as failures` · `should degrade an unknown outcome rather than failing` |
| **8** | Un código de aviso desconocido no rompe la fila | `should fall back to a neutral label for an unknown warning code` *(×2)* · `should never show the raw code for an unknown warning` · `should label a router refusal code with the neutral fallback` · `should fall back to the neutral label for the two router refusal codes` · `should cover exactly the five reachable codes and no more` |
| **9** | El aviso de talla no compite con los de stock | `should render size label missing as a piece attribute and not as a warning` · `should never suppress the missing size label` · `should keep the missing size label out of the alert block` · `should not suppress any other code the backend emitted` · `should still translate the missing size label, because it is shown as an attribute` |
| **10** | Pedir demasiadas fichas seguidas se distingue de una caída | `should distinguish a rate limited response from an unavailable service` *(×2: servicio y pantalla)* · `should map status 429 to its own member when the request fails` · `should not retry a failed assist request` |
| **11** | Fuera de alcance explícito — ni pregunta libre, ni rechazo cortés, ni backend | `should label a router refusal code with the neutral fallback` · `should fall back to the neutral label for the two router refusal codes` · `should keep selecting for sale behaving exactly as it did` · `should report no selection when the card is opened from a result row` · `should cost no search when the card is opened from a result row` · `should neither replace nor disable the selection for sale` · **más las puertas del §1**: `sha256` idéntico y `git status` sin cambios fuera de la zona |

**Dos tests que la lista de tareas no pedía y la spec sí**, ambos en el escenario que ningún otro
cubría:

- `should write neither the question nor the argument to the console`, espiando los cinco niveles de
  `console`. La spec lo exige literalmente y no estaba en `tasks.md`.
- `should render the six states as six distinguishable documents`, que es lo que sostiene *«MUST keep
  all six distinguishable in the rendered document»* cuando dos de ellos comparten texto.

---

## 5 · Lo que se entregó, fichero a fichero

| Fichero | Líneas | Qué sostiene |
|---|---|---|
| `types/sales-assist.types.ts` | 211 | El contrato de C34, fiel a `SalesAssistDtos.cs`. Enumerados en snake_case |
| `services/sales-assist.service.ts` | 140 | Dos llamadas, desenlaces tipados que **nunca lanzan**, `429` y `404` con miembro propio |
| `lib/assist-copy.ts` | 287 | Cinco códigos, etiqueta neutra, cinco mensajes de seis estados, cuatro desenlaces, cinco sugeridas |
| `components/sales/sales-assist-card/` | 795 | Seis bloques: pieza, avisos, argumentario con citas, familia, pregunta, sustitutos |
| `pages/sales/assist.tsx` | 469 | La orquestación: episodio por visita, guarda de orden, sin reintento, disparador de sustitutos |
| `routing/routes.tsx` · `app-routing-setup.tsx` | 9 | `SALES.ASSIST(productId)` y la ruta con carga perezosa |
| `components/sales/assisted-search-result-row.tsx` | +39 | La acción secundaria, **opcional**, sin tocar la firma de `onSelect` |
| `pages/sales/new.tsx` · `scan.tsx` | +103 | Las otras dos entradas |
| Tests (6 ficheros) | 2 212 | 132 tests |

**Ningún componente de interfaz nuevo.** `card`, `badge`, `alert`, `collapsible`, `skeleton`,
`textarea`, `select` y `button` ya estaban en la plantilla, como el ticket anticipaba.

---

## 6 · Una decisión de comportamiento que este apply tomó, y que conviene no perder

**`scan.tsx` ya no salta solo a la caja.** Antes, al resolver un código, la página navegaba
inmediatamente a `/sales/new`. Ahora se detiene en una tarjeta con las dos acciones: *«Continuar con
la venta»*, que es la primaria y aterriza **exactamente donde aterrizaba antes**, con el mismo estado
de navegación; y *«Ver ficha de venta»*, que es la nueva.

**Por qué.** El escenario 1 de la HU pide que el operario **active** la acción, no que ocurra sola, y
sin un instante en el que elegir no hay dónde ponerla. Es un toque más en el flujo de escaneo, y es
el precio de que la entrada que más importa —el cliente con la pieza en la mano— tenga acceso al
corpus. Los dos tests de `scan.test.tsx` no afirman nada sobre la navegación, así que no cambian de
resultado.

La alternativa era dejar el salto automático y que la ficha se alcanzara desde el botón de `new.tsx`.
Se descartó porque convierte la entrada de escaneo en dos saltos y deja el escenario 1 sin cumplir en
su literalidad.

---

## 7 · La comprobación con datos reales, y los dos interruptores que casi la impiden

**La tarea 8.5 se ejecutó el 2026-09-24**, en el **entorno local** y no en el demo desplegado. Es
el mismo código, la misma base —el mundo de C10 y el índice de C13—, el mismo `jbg-ai` con
credencial real y `STUB_MODE=false`, y el mismo prompt `assist/v3`. Lo que no es el mismo es el
despliegue, y eso se dice en vez de pasarlo por alto: `compose.demo.yaml` tira de imágenes de ECR
y de secretos del almacén de parámetros, que no están en esta máquina.

### Los tres criterios

| # | Criterio | Resultado |
|---|---|---|
| 1 | **Ficha con argumentario resuelto** | `pitchStatus: generated`, `promptVersion: assist/v3`, **7,4 s**. Texto en castellano, **sin `{{price}}` ni `{{stock}}`** |
| 2 | **Pregunta con citas** | `ai.knowledge_chunk` con **161 fragmentos** indexados. Citas completas con `citationId`, documento, sección, `docType` y `claimScope` — incluida una de `establecimiento` |
| 3 | **Familia con varias variantes** | `SKU158` en Ciutadella Centre, **4 variantes**, **ninguna preseleccionada**, un botón por miembro nombrando la talla |

La pieza del criterio 1 y 3 es `SKU158` (*Anillo lapislázuli pequeño*, 24 unidades). La petición se
sirvió con el token de `admin`, lo que comprueba además que **un administrador sin tienda asignada
puede usar la ficha**: elige una y el backend la autoriza por la excepción que `SalesAssistService`
le concede.

### Y lo que casi impide la comprobación: dos interruptores apagados y sin documentar

Esto es lo que más valor tiene de esta sección, porque **costó una sesión entera** y no estaba
escrito en ninguna parte.

| Interruptor | Por defecto | En `appsettings` | Síntoma |
|---|---|---|---|
| `AiSalesAssist:EnabledByDefault` | `false` | **ausente de todos** | «El asistente no está disponible» |
| `AiSearch:EnabledByDefault` | `false` | **ausente de todos** | «Búsqueda asistida no disponible» |

Los dos están documentados en su clase de opciones —*«Defaults to false, so enabling a shop is an
explicit act»*— y **ninguno aparece en `appsettings.json` ni en `appsettings.Development.json`**, de
modo que un entorno recién arrancado los tiene apagados sin decirlo en ningún sitio que alguien vaya
a leer.

Con el de la ficha apagado, `SalesAssistService` **ni siquiera llama** al servicio de IA —
`degradedReason = "switched_off"`— y la pantalla pinta correctamente su estado degradado. Parece un
defecto de C36 y no lo es.

**Se encienden sin tocar ningún fichero versionado**, con variable de entorno:

```powershell
cd backend\src\JoiabagurPV.API
$env:AiSalesAssist__EnabledByDefault = "true"
$env:AiSearch__EnabledByDefault = "true"
dotnet run
```

El doble guion bajo es cómo .NET mapea la sección desde el entorno. Y el servicio de IA hay que
levantarlo en modo real: el `jbg-ai` de `backend/docker-compose.yml` viene con `STUB_MODE: "true"` y
sin credenciales, así que sirve fixtures que parecen un sistema funcionando.

**Cómo comprobar que funcionó**, sin depender de lo que se vea en pantalla:

```sh
docker logs jpv-pv-jbg-ai --tail 20                       # tiene que haber /v1/assist/sale
docker logs jpv-pv-jbg-ai 2>&1 | grep "stage=assist_client"  # credential=assist, no rag_fallback
```

### Lo que sigue sin comprobarse

**El demo desplegado.** Cuando se despliegue, la comprobación equivalente es el §5.6b de
`deploy/demo/README.md` —*«The sale card generates (C34)»*—, ampliado con el bloque de familia y la
caja de pregunta. Con un aviso que esa misma guía ya documenta: **`ai.knowledge_chunk` nace vacía**
en un entorno nuevo, porque el corpus no viaja en la imagen, así que las cinco preguntas sugeridas
responderán todas que la documentación no las cubre hasta que se sortee con el `docker cp` que la
tarea diferida describe.

## 8 · Limitaciones que este change declara y no cierra

1. **La ficha no tiene telemetría.** Ninguna de las tres cosas que decide —abrir, preguntar, elegir
   variante— deja rastro. Su uso **no es medible**, y por tanto la condición de reactivación de la
   tarea diferida de `generate=false` no se puede comprobar con datos. Se declara como limitación, no
   como medición pendiente.
2. **Una pieza que el servicio no puede procesar se ve como «IA no disponible»** en la ruta de
   asistencia (limitación 3 de C34): el cuerpo no los distingue. En **sustitutos sí** se distinguen,
   porque ahí `product_not_indexed` es un desenlace propio y la ficha lo pinta como *«esta pieza aún no
   está preparada»*.
3. **La pregunta libre sin pieza sigue sin pantalla** (§15.12 del diseño), y el **rechazo cortés del
   enrutador tampoco** (§15.13). Los dos códigos de rechazo existen en el vocabulario y esta pantalla
   los trata como desconocidos, con un test que lo comprueba.
4. **La espera de 4 a 8 s no se puede partir** sin tocar el backend. Estado de carga desde el primer
   instante, y la tarea diferida abierta.
5. **Sin corpus cargado, la caja de pregunta responde siempre que la documentación no cubre la
   pregunta.** No es de este change; agrava la tarea diferida que C34 dejó abierta.

---

## 9 · Reproducir las cifras de este informe

```sh
# La suite, con el informador que permite comparar por nombres
cd frontend
npx vitest run --reporter=json --outputFile.json=/tmp/close.json
#   → Test Files 14 failed | 40 passed (54) · Tests 113 failed | 616 passed (729)

# La puerta real
npm run build            # ✓ built in 14.58s

# El contrato congelado
sha256sum ai-service/openapi.json
#   → d8d48f87b279d45d22bce80a67c4fd51caef6e679363c413f5b697c99ec2b875

# La zona
git diff --name-only 2b49685..HEAD | grep -v "^frontend/\|^openspec/\|^Documentos/\|^CLAUDE.md\|^backend/README.md"
#   → (vacío)   ← CLAUDE.md y backend/README.md están tocados a propósito (§2.1 y §7),
#                 y por eso van excluidos: sin excluirlos el comando devuelve esos dos.

# La cobertura del código nuevo (§1)
npx vitest run --coverage src/lib/assist-copy.test.ts src/services/sales-assist.service.test.ts src/pages/sales/__tests__/assist.test.tsx src/pages/sales/__tests__/assist-entrances.test.tsx src/pages/sales/__tests__/new-assist-card-entrance.test.tsx src/components/sales/__tests__/assisted-search-row-card-action.test.tsx
#   → 132 tests, 0 fallando; assist-copy 100 %, assist.tsx 92,72 %, la carpeta del card 91,04 %

# Las specs
openspec validate --all --strict
#   → Totals: 61 passed, 0 failed (61 items)

# El punto de venta que scan.tsx no tiene (§2.2)
git show 2b49685:frontend/src/pages/sales/scan.tsx | grep -c -i "pointofsale"
#   → 0
```
