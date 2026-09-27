# T-AIENG-036: Sale assist card and family disambiguation — one request per visit, explicit variant confirmation and scoped citations (C36)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya siguen
> [T-AIENG-034](../../archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/ticket.md),
> [T-AIENG-016](../../archive/2026-08-29-add-frontend-assisted-search-panel/ticket.md) y el resto de
> tickets del Proyecto Final.
>
> **Fuentes de verdad:** `openspec/project.md`,
> [HU-AIENG-036](../../../../Documentos/Historias/AI-Eng/HU-AIENG-036.md),
> [informe de exploración](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md)
> (siete hallazgos, diez decisiones, tres mediciones reproducibles),
> [ficha C36](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md),
> [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
> (§7.7, §7.8, §15.12, §15.13), la spec viva
> [`ai-sales-assist`](../../../specs/ai-sales-assist/spec.md) y el código real de `frontend/src/`.

**HU origen:** [HU-AIENG-036](../../../../Documentos/Historias/AI-Eng/HU-AIENG-036.md)
**Change:** `add-frontend-assist-card-and-family-disambiguation` (C36) · **Épica:** EP15
**Rama:** `c36-add-frontend-assist-card-and-family-disambiguation` · **Anterior en la rama:** C34 ·
**Siguiente:** C38

---

## Título

Construir el **card de venta del frontend** en ruta propia
—**`/sales/new/assist/:productId`**— con **tres entradas** (fila de búsqueda asistida, página de venta
manual y escaneo), **una petición por visita y sin reintento automático**, **desambiguación por
familia sin preselección** con un botón de venta por miembro, **citas desplegables que distinguen
`claimScope`**, **caja de pregunta con sugerencias del corpus** limitada a 500 caracteres y siempre en
el cuerpo, **bloque de sustitutos** con sus cuatro desenlaces, y una **tabla de copy** que traduce los
**cinco códigos alcanzables** y tolera cualquier otro con una etiqueta neutra. `size_label_missing` se
degrada a **atributo de la pieza**, no a alerta.

---

## Contexto y Problema

C34 dejó las dos rutas del card servidas, medidas y **sin ningún consumidor**. El argumentario con
precio y stock resueltos, las citas con su alcance, el agrupado por familia hidratado y los sustitutos
vendibles hoy existen desde el 22 de septiembre y **sólo se demuestran con `curl` y con el arnés**.
C36 es la pantalla, y es **el único change del Proyecto Final que pone la capa RAG delante de una
persona**.

La ficha de C36 se escribió en agosto y se anotó dos veces —el 13 de septiembre al implementar C30a y
el 21 al explorar C34—, siempre **antes de que existiera el consumidor**. La exploración del
2026-09-22 la contrastó con el árbol, y cuatro hallazgos gobiernan el diseño:

1. **Tres de las cinco filas de copy que la ficha hereda de C31 no pueden llegar al card.**
   `classify_query` corre **sólo en M1** ([`orchestrator.py:270-280`](../../../../ai-service/src/jbg_ai/assist/orchestrator.py#L270-L280))
   y las dos rutas de C34 son siempre ancladas, así que `clarification_question` es constante `null` y
   los dos códigos de rechazo son inalcanzables. Escribir su castellano daría **dos tests verdes sobre
   caminos imposibles**.
2. **`size_label_missing` salta en el 58,3 % de los cards** y está anticorrelacionado con tener
   familia: **4,0 %** con ella contra **92,5 %** sin ella. Informa del estado del enriquecimiento, no
   de la pieza. El propio orquestador ya rechazó un cálculo de este aviso por esa razón exacta
   ([`orchestrator.py:661`](../../../../ai-service/src/jbg_ai/assist/orchestrator.py#L661)).
3. **Los datos baratos del card y los caros llegan soldados.** El grupo, los cuatro avisos y el stock
   no necesitan ni un token y sólo se obtienen pagando una generación de **p50 4,42 s / p95 7,13 s**
   (C34 §4). `GET /api/product-families/{id}` existe y es accesible a cualquier autenticado, pero está
   indexada por **familia**, el DTO de producto **no lleva `familyId`** y no devuelve cantidad por
   punto de venta: desde un `productId` no hay camino.
4. **El bloque de familia es sólido, comprobado y no supuesto**: el **98,3 %** de los 544 grupos con
   dos o más miembros llevados trae todas las etiquetas presentes y distintas, **cero** grupos con
   todas nulas, **cero** con duplicados, y el **99,6 %** cabe en dos a cuatro filas.

### Estado actual del código, verificado en el repositorio (2026-09-22, `4552bcf`)

| Pieza | Fichero | Estado |
|---|---|---|
| Change OpenSpec | `openspec/changes/add-frontend-assist-card-and-family-disambiguation/` | **Scaffold** (`.openspec.yaml`, `spec-driven`); proposal, design, specs y tasks **pendientes**; este ticket y la HU |
| Rutas de C34 | `API/Controllers/AiSalesAssistController.cs` | `POST /api/ai/products/{productId}/sales-assist` (cuerpo `{pointOfSaleId, question?}`) y `GET /api/ai/products/{productId}/substitutes?pointOfSaleId=&pageSize=` |
| Contrato hacia el frontend | `Application/DTOs/Ai/SalesAssistDtos.cs` | `SalesAssistResponse` con `aiAvailable`, `pointOfSaleId`, `productId`, `intent`, `groups[]`, `pitch`, `pitchStatus` (6), `citations[]`, `warnings[]`, `clarificationQuestion`, `promptVersion`, `traceId`. `SubstitutesResponse` con `outcome` (4), `results[]`, `candidatesReturned`, `survivedHydration` |
| Límite de peticiones y caché | `Application/Configuration/AiSalesAssistOptions.cs` | `RateLimitPermitLimit = 10` / `RateLimitWindowSeconds = 60` por usuario; `SubstitutesDefaultPageSize = 5`, `SubstitutesMaxPageSize = 20`. La spec viva **prohíbe cachear** la respuesta del card |
| Longitud de la pregunta | `Application/Validators/SalesAssistRequestValidator.cs` · `ai-service/openapi.json` | **500 caracteres**, el máximo del contrato congelado |
| Vocabulario de avisos | `ai-service/.../assist/constants.py:51` · `Application/Services/SalesAssistService.cs:18` | 5 de Python + 2 de .NET. **Dos de los siete son inalcanzables** desde estas rutas |
| Fila de resultados de C16 | `frontend/src/components/sales/assisted-search-result-row.tsx` | Componente propio con `ORIGIN_LABELS`/`originLabel` **exportados y testeados**. Su docstring anticipa C36 |
| Panel de C16 | `frontend/src/pages/sales/assisted.tsx` | 506 líneas: selector de POS por rol, episodio por visita (`sessionRef`), guarda de orden (`requestSeq`), cinco vacíos distinguibles, 429 distinguible, embudo de administrador |
| Servicio de C16 | `frontend/src/services/ai-search.service.ts` | Desenlaces tipados que **nunca lanzan**, con `rate-limited` como miembro propio. **Es el patrón** |
| Entrega por estado de navegación | `frontend/src/pages/sales/new.tsx:48-57` | `LocationState { productId?, photoDataUrl?, searchEventId? }`. Lo usan `scan`, `image` y `assisted` |
| Rutas | `frontend/src/routing/routes.tsx:34-43` | `SALES.NEW`, `NEW_SCAN`, `NEW_IMAGE`, `NEW_ASSISTED`, `CART`, `HISTORY`, `DETAIL`. **No hay entrada de ficha de venta** |
| Componentes de UI | `frontend/src/components/ui/` | `card`, `badge`, `alert`, `accordion`, `collapsible`, `skeleton`, `textarea`, `select`, `separator`, `button` — **todos existen; ninguno nuevo** |
| Card, tabla de copy, caja de pregunta | — | **Cero** |
| Telemetría del card | — | **No existe.** `ProductSearchEvent` es de la búsqueda, no del card |
| Suite de frontend | `frontend/` | **Roja de fábrica**: 113 fallos de 595 en 14 de 48 ficheros (13 sep). `vitest` sale con código 0 al pipearlo; MSW con `onUnhandledRequest: 'warn'` |

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `frontend/src/pages/sales/assist.tsx` | **Nuevo.** Página del card: POS por estado de navegación con selector de respaldo, episodio por visita, guarda de orden, orquestación de los dos servicios |
| `frontend/src/components/sales/sales-assist-card/` | **Nuevos.** Cabecera de la pieza, bloque de avisos, bloque de argumentario con citas, bloque de familia, caja de pregunta, bloque de sustitutos |
| `frontend/src/components/sales/assisted-search-result-row.tsx` | **Modificado.** Acción secundaria hacia el card. **No** sustituye ni bloquea «Seleccionar para venta» |
| `frontend/src/pages/sales/new.tsx` | **Modificado, mínimo.** Botón hacia el card junto al producto seleccionado, y aceptar un `productId` distinto al que ya tenía |
| `frontend/src/pages/sales/scan.tsx` | **Modificado, mínimo.** Salto opcional al card tras resolver el código |
| `frontend/src/services/sales-assist.service.ts` | **Nuevo.** Dos llamadas con desenlaces tipados que nunca lanzan, con `rate-limited` propio |
| `frontend/src/types/sales-assist.types.ts` | **Nuevo.** Fiel a los DTO de C34, incluidos los seis `pitchStatus` y los cuatro `outcome` en snake_case |
| `frontend/src/lib/assist-copy.ts` | **Nuevo.** Cinco códigos + etiqueta neutra, cinco mensajes de estado, cuatro desenlaces, cinco preguntas sugeridas |
| `frontend/src/routing/routes.tsx` · `app-routing.tsx` | `SALES.ASSIST(productId)` y su ruta con carga perezosa |
| `frontend/src/**/__tests__/` | Tests del card, de la fila modificada, del servicio y de la tabla de copy |
| `openspec/changes/add-frontend-assist-card-and-family-disambiguation/` | proposal, **design.md**, specs (capability nueva + `## MODIFIED` de `assisted-search-panel`), tasks |
| `Documentos/` · `frontend/README.md` · `openspec/DEFERRED_TASKS.md` | Ver la tarea de documentación |

**No se tocan:** `backend/` entero, `ai-service/` entero (**`openapi.json` idéntico byte a byte**),
`terraform/`, `.github/workflows/`, el carrito y la confirmación de venta de `new.tsx`, y la lógica de
búsqueda de `assisted.tsx`. **Sin migración de EF Core.**

---

## Especificaciones Técnicas

### Ruta y entradas

```text
ROUTES.SALES.ASSIST = (productId: string) => `/sales/new/assist/${productId}`
```

Carga perezosa, bajo el árbol de ventas, protegida como el resto. El punto de venta llega por
**estado de navegación** (`{ pointOfSaleId }`); abierta en frío, la página muestra el **mismo selector
por rol** que el panel de C16 y **no emite ninguna petición** hasta que hay uno elegido.

Tres entradas, todas con la acción explícita:

| Origen | Acción | Estado que viaja |
|---|---|---|
| `assisted-search-result-row.tsx` | Botón secundario «Ver ficha de venta» | `{ pointOfSaleId }` del panel |
| `new.tsx` | Botón junto al producto seleccionado | `{ pointOfSaleId }` del formulario |
| `scan.tsx` | Salto tras resolver el código | `{ pointOfSaleId }` del escaneo |

La salida es el traspaso que ya existe: `navigate(ROUTES.SALES.NEW, { state: { productId } })`.

### Tipos

`types/sales-assist.types.ts`, fiel a `SalesAssistDtos.cs`. Los dos enumerados viajan en
**snake_case** porque .NET los serializa así (`JsonStringEnumMemberName`):

```ts
type PitchStatus =
  | 'generated' | 'ai_unavailable' | 'not_generated'
  | 'withheld_by_ai' | 'withheld_unresolved' | 'withheld_out_of_stock';

type SubstitutesOutcome = 'ok' | 'none_in_stock' | 'product_not_indexed' | 'ai_unavailable';
```

`SalesAssistResponse`, `SalesAssistGroup`, `SalesAssistMember` (con `variantLabel`, `hasStock`,
`isAnchor`, `quantityAtPointOfSale`), `SalesAssistCitation` (con `claimScope`) y `SubstitutesResponse`
con `SubstituteResult`. **No se inventa ningún campo** ni se deriva ninguno que .NET no envíe.

### Servicio

`services/sales-assist.service.ts`, calcado de `ai-search.service.ts`: **nunca lanza**, devuelve
desenlaces tipados, y `429` es un miembro propio distinto de `error`.

```ts
type SalesAssistOutcome =
  | { kind: 'ok'; response: SalesAssistResponse }
  | { kind: 'rate-limited' } | { kind: 'forbidden' }
  | { kind: 'not-found' } | { kind: 'invalid'; errors: string[] }
  | { kind: 'error'; message: string };
```

`404` gana miembro propio, que el panel no necesitaba: aquí significa que **esa tienda no lleva la
pieza**, y es un mensaje distinto de un fallo.

### Una petición por visita

- Se emite **al entrar**, una sola vez, con la guarda de episodio (`useRef` inicializado de forma
  perezosa) y la guarda de orden (`requestSeq`) del panel de C16.
- **Sin reintento automático.** Un botón de reintento, sí.
- La **pregunta** es una **segunda** petición explícita al mismo endpoint, con `question` en el cuerpo.
- Volver atrás y entrar de nuevo **es otra visita y vuelve a pagar**: se dice en la spec, no se oculta
  con una caché que la spec viva de C34 prohíbe.

### Tabla de copy — `lib/assist-copy.ts`

Funciones exportadas y testeadas directamente, como `originLabel` en C16.

| código | origen | castellano |
|---|---|---|
| `family_has_variants` | Python, ajustado por .NET | «Esta pieza tiene otras variantes en esta tienda» |
| `stock_critical` | .NET | «Quedan pocas unidades» |
| `family_members_out_of_stock` | .NET | «Alguna variante de la familia está agotada aquí» |
| `knowledge_not_covered` | Python, sólo M3 | «La documentación no cubre esta pregunta» |
| `size_label_missing` | Python | **No entra en el bloque de avisos** — ver abajo |
| cualquier otro | — | **etiqueta neutra**, sin mostrar el código en bruto |

**`query_out_of_domain` y `query_not_in_catalogue` no llevan fila**, y un test comprueba que caen en la
etiqueta neutra. El vocabulario es cerrado **pero versionado**: esa regla es lo único que impide que
una versión nueva del servicio rompa una fila de la pantalla.

### `size_label_missing` — atributo, no alerta

Se pinta **siempre** (no se suprime nada que el backend haya emitido) pero **como línea neutra junto al
SKU**: *«Sin talla declarada»*. Nunca en el bloque de avisos. Justificación en la spec, con la cifra:
**58,3 %** de los cards, **92,5 %** de las piezas sin familia contra **4,0 %** de las que la tienen.

### Bloque de familia

- Se pinta cuando el grupo trae **dos o más miembros**.
- Una fila por miembro con `variantLabel` destacado, precio en es-ES/EUR, unidades de esa tienda y
  marca de agotado; el miembro anclado, señalado.
- **Ninguna preselección.** Un botón «Vender esta» **por fila**; no existe ninguna acción de venta que
  no nombre a un miembro.
- Con `variantLabel` nulo, la fila **degrada al SKU** en vez de dejar el hueco (1,7 % de los grupos).
- Con **un** miembro, vuelve la acción directa y el aviso de variantes no aparece — C34 ya lo retira.

### Bloque de argumentario y citas

Seis `pitchStatus` → **cinco mensajes**:

| estado | mensaje |
|---|---|
| `generated` | se pinta el argumentario |
| `ai_unavailable` | «El asistente no está disponible. Lo que ves viene del catálogo.» |
| `not_generated` | «Los datos de la pieza son los del índice; el argumentario no se ha generado.» |
| `withheld_by_ai` · `withheld_unresolved` | «No he podido redactar algo que pueda sostener con los datos de esta pieza.» *(+ acción)* |
| `withheld_out_of_stock` | «Esta pieza está agotada aquí. Te propongo alternativas.» |

Los dos primeros **no se funden**: en el degradado no hay citas ni `matchReasons` y la familia viene de
`ProductFamily`; fundirlos haría que el card mintiera sobre la procedencia de lo que enseña. Los tres
retenidos **terminan en una acción**, no en un punto.

**Citas**: plegadas por defecto (`accordion`/`collapsible`), con `documentTitle`, `sectionTitle` y
`snippet`. `claimScope === 'establecimiento'` lleva insignia propia y la frase de confirmarlo en
tienda; `general`, no. **No se resuelven a enlaces** (C34 lo prohíbe y no hay ruta que lea el corpus) y
**se ocultan cuando `pitchStatus !== 'generated'`**.

### Caja de pregunta

`textarea` con **cinco preguntas sugeridas** del corpus que rellenan y envían en un solo acto, patrón
de `EXAMPLE_QUERIES`. **500 caracteres** comprobados antes de enviar. La pregunta viaja en el cuerpo y
**no se escribe en la URL ni en el estado del router**, que acaba en el historial del navegador.

### Bloque de sustitutos

- Disparador: **`hasStock === false` en el miembro anclado** —presente en todos los estados servidos—,
  nunca `pitchStatus`.
- **Automático**, salvo si `aiAvailable === false`: entonces **no se pide** y se explica.
- `pageSize` por defecto (5). Cuatro desenlaces, cuatro textos; `product_not_indexed` como «esta pieza
  aún no está preparada» y **nunca** como caída.
- Página corta declarada, no rellenada, con la regla de C16.

### Specs de OpenSpec

| Capability | Delta | Contenido |
|---|---|---|
| **`sales-assist-card`** | **ADDED** | Ruta y entradas · una petición por visita sin reintento · tabla de copy con cinco códigos y etiqueta neutra · talla como atributo · confirmación de variante sin preselección · cinco mensajes de seis estados · citas con alcance y ocultas al retirar · cuatro desenlaces de sustitutos · caja de pregunta con sus límites |
| `assisted-search-panel` | **MODIFIED** | La fila gana una acción secundaria hacia el card que **no** sustituye ni bloquea la selección para venta |

Descripción de requisito **en una sola línea física**, con su `SHALL`/`MUST` en ella: el validador sólo
lee la primera.

---

## Arquitectura

```text
  assisted.tsx ──[«Ver ficha de venta»]──┐
  new.tsx ──────[botón del producto]─────┼──▶ /sales/new/assist/:productId
  scan.tsx ─────[tras resolver]──────────┘         │
                                                   │  estado: { pointOfSaleId }
                                                   │  en frío → selector por rol, sin pedir nada
                                                   ▼
                        ┌──────────────────────────────────────────────┐
                        │ assist.tsx · episodio por visita · sin retry │
                        └──────────────────────────────────────────────┘
                                   │                          │
     POST .../sales-assist  ◀──────┘                          └──────▶  GET .../substitutes
     una vez al entrar, + una por pregunta                     sólo si !anchor.hasStock
     429 ≠ caída · 404 = la tienda no la lleva                 y aiAvailable
                                   │                                    │
                                   ▼                                    ▼
      ┌──────────────────────────────────────────┐        outcome: ok · none_in_stock
      │ pieza + «Sin talla declarada»            │                 product_not_indexed
      │ avisos (4 códigos + neutra)              │                 ai_unavailable
      │ argumentario: 6 estados → 5 mensajes     │
      │   citas ▸ claimScope · ocultas si ≠ gen. │
      │ familia ≥2 → 1 botón por miembro         │──[Vender esta]──▶ /sales/new
      │   sin preselección                       │    state: { productId }
      │ caja de pregunta (500) + 5 sugeridas     │
      └──────────────────────────────────────────┘
```

**Decisiones heredadas:**

- **C16** — *«a search is issued only when the operator asks for one»*, aplicado aquí a una llamada
  diez veces más cara; etiqueta neutra para un valor desconocido; vacíos distinguibles; página corta
  declarada; guarda de respuestas fuera de orden; entrega por estado de navegación.
- **C34** — seis `pitchStatus`, cuatro `outcome`, citas que son *las que el argumentario usó*, avisos
  ya ajustados a lo que la tienda lleva, 10 peticiones por minuto y **sin caché**.
- **C30a** — *familia nula ⇒ exactamente un miembro*, que es lo que impide que la confirmación de
  variante se dispare sobre un grupo sintético de uno.
- **§7.7 del diseño** — los avisos viajan como códigos y **el castellano lo escribe esta capa**.
- **§7.8** — `claim_scope` separa un hecho del mundo de un compromiso de la casa.

**Breaking:** ninguno.

- Ruta nueva; `assisted.tsx` conserva su flujo y su telemetría de selección.
- `assisted-search-result-row.tsx` **gana** una acción; su `onSelect` no cambia de firma.
- No se toca ningún contrato REST ni `ai-service/openapi.json`.

---

## Definición de Hecho (DoD)

- [ ] Código según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] **Línea base de la suite de frontend medida antes de tocar nada** (`git stash push -u`, `npm run test`, `git stash pop`): se compara el **conjunto de nombres** que fallan, nunca el número. Viene roja de fábrica
- [ ] La salida de `vitest` se lee **en su línea de resumen**, no por el código de salida: pipearlo da 0 siempre
- [ ] Frontend: Vitest + React Testing Library, nomenclatura `should [comportamiento] when [condición]`, queries accesibles, cobertura ≥ 70 % en el código nuevo
- [ ] Los tests **envuelven los proveedores** (`AuthProvider`, y `CartProvider` donde toque) o mockean el hook: es la causa de un tercio de los 113 fallos de línea base. Plantilla: `pages/sales/__tests__/cart.test.tsx`
- [ ] Los servicios se mockean con **`vi.mock`** y no se confía en MSW: con `onUnhandledRequest: 'warn'` un test puede pasar **sin haber afirmado nada**
- [ ] Un test comprueba que se emite **exactamente una** petición de asistencia por visita
- [ ] Un test comprueba que un fallo **no se reintenta solo**
- [ ] Un test comprueba que con dos o más miembros **ninguno está preseleccionado** y que no existe acción de venta sin miembro
- [ ] Un test comprueba que los dos códigos de rechazo del enrutador **caen en la etiqueta neutra**
- [ ] Un test comprueba que `size_label_missing` **no** se pinta en el bloque de avisos y **sí** junto al SKU
- [ ] Un test distingue `ai_unavailable` de `not_generated` y el 429 de la caída
- [ ] Un test comprueba que la pregunta **no aparece en la URL** ni en el estado del router
- [ ] Un test comprueba que **no se piden sustitutos** con el card degradado
- [ ] `npm run build` en verde — la puerta real; `tsc --noEmit` trae decenas de errores preexistentes de Metronic y se filtra a los ficheros propios
- [ ] UI en **es-ES** y moneda **EUR (€)** con `Intl.NumberFormat('es-ES')`, como la fila de C16
- [ ] **Sin migración de EF Core**; `backend/` y `ai-service/` sin tocar
- [ ] `sha256` de `ai-service/openapi.json` **igual** al del inicio del change
- [ ] Specs delta en `openspec/changes/add-frontend-assist-card-and-family-disambiguation/specs/`, con la **primera línea física** de cada requisito llevando su `SHALL`/`MUST`
- [ ] `openspec validate --all --strict` → **0 failed** (el de un solo change no basta)
- [ ] Comprobación en la demo: una ficha real con argumentario resuelto, una pregunta con citas y un bloque de familia con varias variantes
- [ ] Documentación: `Documentos/epicas.md`, plan de changes, diseño (§15.12 reescrita, §15.13 ampliada, limitación nueva de telemetría), `frontend/README.md`, `openspec/DEFERRED_TASKS.md` con las dos entradas nuevas
- [ ] Sin TODO/FIXME sin tarea de seguimiento

**No aplica:** xUnit, Moq, Testcontainers y cobertura de backend; `uv run pytest` y regenerar
`openapi.json`; migración de EF Core; Playwright (el flujo crítico de venta sigue siendo el de
`new.tsx`, que no cambia de comportamiento).

---

## Requisitos No Funcionales

- **Seguridad y privacidad:**
  - La pregunta del cliente **nunca** en la URL ni en el estado del router: acaba en el historial del
    navegador y en el log de acceso del proxy. C34 lo prohíbe en el servidor; aquí se prohíbe en el
    cliente.
  - El punto de venta que se envía es el del ámbito elegido; la autorización la decide .NET, y el card
    **no la anticipa** ni oculta piezas por su cuenta.
  - Ni el argumentario resuelto ni la pregunta se escriben en `console` en ningún nivel.
- **Rendimiento y coste:**
  - **Una petición de asistencia por visita** más una por pregunta, contra un límite de **10 por minuto
    y usuario**. Sin reintento automático y **sin caché**.
  - Espera esperable de **p50 4,4 s / p95 7,1 s** (1,3 a 3,8 s en la demo): estado de carga explícito
    desde el primer instante, nunca una pantalla en blanco.
  - Ruta con **carga perezosa**, para no engordar el *bundle* inicial por debajo de 500 KB.
- **Accesibilidad y presentación:**
  - Estados marcados **por texto además de por color** (regla que la fila de C16 ya aplica al «Sin
    existencias»).
  - Legible en móvil: el card se usa de pie, en el mostrador.
  - es-ES y EUR con `Intl.NumberFormat`.
- **Robustez:**
  - Ningún desenlace del servicio lanza; todos se pintan con una frase verdadera.
  - Un código de aviso desconocido **degrada la fila**, no la rompe.
  - Una respuesta obsoleta nunca sobreescribe a una más nueva.

---

## Preguntas Abiertas

Las cuatro decisiones de producto se cerraron con el desarrollador en la exploración (D-A, D-B, D-C y
D-E). Quedan éstas, todas con opción por defecto:

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| 1 | ¿Capability nueva, o se amplía `assisted-search-panel`? | **Nueva**, `sales-assist-card`; el panel sólo gana la acción secundaria |
| 2 | ¿El card se abre desde el detalle de producto del catálogo? | **No**: es pantalla de administración y el card necesita punto de venta. Queda identificado |
| 3 | ¿Cuántas preguntas sugeridas? | **Cinco**: mojar la pieza, piel sensible, limpieza en casa, regalo sin saber la talla, playa o piscina |
| 4 | ¿La pregunta se conserva al reabrir la ficha? | **No**: un episodio por visita, y conservarla invita a reenviarla sin querer |
| 5 | ¿El embudo de administrador de C16 se replica? | **No**: el card no tiene embudo propio; los contadores de sustitutos bastan como insignia |
| 6 | ¿Ruta en frío con varios puntos de venta? | **Selector de respaldo** por rol y **ninguna petición** hasta elegir uno |
| 7 | ¿El botón de la fila reporta selección de telemetría? | **No**: ver la ficha no es elegir la pieza, y contarlo falsearía la métrica de C04. Se reporta al vender desde el card |
| 8 | ¿El card distingue una pieza no indexada de una caída? | **No**: el cuerpo de C34 no los separa (su limitación 3). Se pinta «no disponible» y se declara |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
toque `backend/` ni `ai-service/`, **no** cambie el comportamiento del panel de C16 ni el de la página
de venta, y **no** suprima ningún dato que el backend haya emitido.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). *Nunca se recorta* según el §6 del plan. **Cierra la cadena crítica**
  `C30a → C34 → C36` y es lo que el vídeo del PF tiene que mostrar.
- **Estimación:** _Pendiente de refinamiento_. Orientativamente por debajo de C34: ninguna capa nueva,
  ningún contrato que negociar, ningún componente de Metronic que crear y ningún dato que calcular. La
  dificultad está en **cuántos estados hay que distinguir sin mentir**.
- **Dependencias:** C16 y C34 archivados. **No se abre a la vez que C16** (misma página y servicio del
  frontend). No bloquea a nadie: C38 depende de C34, no de esta pantalla.
- **Línea de corte** (regla 5 del §1, si la sesión desborda):
  1. ruta, servicio, tipos, tabla de copy, cabecera, avisos, argumentario con citas y **bloque de
     familia** — que es archivable y es lo que el PF puntúa;
  2. **caja de pregunta** con sus sugerencias;
  3. **bloque de sustitutos**.

  Los tramos 2 y 3 se **declaran aplazados con motivo** si no caben, no se callan. Cortar el 2 deja la
  limitación 12 del §15 **más grave**, porque el corpus de C23 se queda otra vez sin ninguna ruta a
  pantalla: eso se escribe.
- **Tags:** `HU-AIENG-036`, `C36`, `EP15`, `frontend`, `react`, `sales-assist`, `family-disambiguation`,
  `citations`, `copy-table`, `substitutes`, `es-ES`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-036](../../../../Documentos/Historias/AI-Eng/HU-AIENG-036.md)
- **Informe de exploración:** [c36-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md)
- **Plan y diseño:**
  - [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), ficha C36;
  - [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md), §7.7, §7.8, §15.12 y §15.13.
- **Specs vivas:**
  - [`assisted-search-panel`](../../../specs/assisted-search-panel/spec.md) *(se modifica; y es el patrón)*
  - [`ai-sales-assist`](../../../specs/ai-sales-assist/spec.md) *(lo que el card consume)*
  - [`assist-generation`](../../../specs/assist-generation/spec.md) · [`substitutes-retrieval`](../../../specs/substitutes-retrieval/spec.md)
  - [`knowledge-corpus`](../../../specs/knowledge-corpus/spec.md) · [`product-family`](../../../specs/product-family/spec.md)
  - [`frontend`](../../../specs/frontend/spec.md) · [`frontend-testing`](../../../specs/frontend-testing/spec.md)
- **Precedentes:**
  - [T-AIENG-016](../../archive/2026-08-29-add-frontend-assisted-search-panel/ticket.md): el patrón de pantalla que consume IA aquí.
  - [T-AIENG-034](../../archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/ticket.md): el contrato que se consume.
  - [T-AIENG-030a](../../archive/2026-09-13-add-assist-structure-and-rule-warnings/ticket.md): la forma de la respuesta y los códigos.
- **Apuntes del Máster (guía, no dogma):**
  - [S4 · De interfaz conversacional a interfaz de producto](../../../../Documentos/Sesiones%20Master%20AIEng/S4_Productos_IA_avanzados/De%20interfaz%20conversacional%20a%20interfaz%20de%20producto.md): hornear en la interfaz lo que se puede pedir.
  - [S11 · Citación y atribución verificable](../../../../Documentos/Sesiones%20Master%20AIEng/S11_RAG_avanzado/Citacion%20y%20Atribucion%20verificable.md): resuelve, localiza, trazable — y *«demasiada citación cansa»*.
  - [S16 · Un sistema debe saber decir «no lo sé»](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/Un%20sistema%20debe%20saber%20decir%20%E2%80%9CNo%20lo%20se%E2%80%9D.md): la abstención honesta dice qué haría falta.
- **Tareas diferidas:** [`DEFERRED_TASKS.md`](../../../DEFERRED_TASKS.md). Se **abren** dos: `generate=false` en `/sales-assist` y telemetría del card. Siguen abiertas *«C32b — política de timeout y circuito de `/v1/assist/agent`»* y *«C34 — el corpus no viaja en la imagen de `jbg-ai`»*, ésta con más peso: sin corpus, la caja de pregunta responde siempre `knowledge_not_covered`.
- **Testing:** [testing-frontend.md](../../../../Documentos/testing-frontend.md), sección *Estado de la suite: fallos conocidos*.
- **Componentes:** [analisis-metronic-frontend.md](../../../../Documentos/Propuestas/analisis-metronic-frontend.md).
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-09-22 | `/enrich-us` | Creación a partir de HU-AIENG-036 y del informe de exploración del mismo día. Recoge: ruta propia con tres entradas; una petición por visita sin reintento automático, con la pregunta como segunda llamada; cinco códigos de aviso con copy y etiqueta neutra para los dos inalcanzables, comprobada con test; `size_label_missing` degradado a atributo por su 58,3 %; confirmación de variante con un botón por miembro y sin preselección; seis `pitchStatus` pintados como cinco mensajes, con `ai_unavailable` y `not_generated` separados; citas con `claimScope` distinguido, sin enlaces y ocultas cuando el argumentario se retira; caja de pregunta con cinco sugerencias, 500 caracteres y nunca en la URL; sustitutos disparados por `hasStock` del ancla, no pedidos con el card degradado, con sus cuatro desenlaces |
