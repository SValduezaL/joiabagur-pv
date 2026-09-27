# HU-AIENG-040: El panel de búsqueda se convierte en M1 — consulta libre con enrutador, corpus y prosa, dos rutas elegibles sobre la misma consulta, y una pantalla que no presenta como encendido lo que está apagado

## Formato estándar

**Como** Operador de un punto de venta,
**quiero** poder preguntar en el panel de búsqueda con mis propias palabras —y no sólo describir una
pieza—, elegir entre una búsqueda barata y una asistida sabiendo lo que cuesta cada una, que los
filtros que pulso se apliquen siempre, y que la pantalla me diga antes de buscar si el asistente está
disponible y después si lo que veo viene de la IA o del catálogo,
**para** atender preguntas de oficio sin tener una pieza delante, sin que un chip pulsado deje de
filtrar en silencio y sin que el sistema me pida reformular cuando el problema es suyo.

---

## Descripción

Change OpenSpec `add-frontend-free-query-panel` / **C40**, épica **EP15 — Venta Asistida, Sustitutos y
Agentes**, que **se reabre con este change**. Prerrequisitos: **C16** (el panel), **C31** (el enrutador
de intención, sin el cual M1 no clasifica nada), **C34** (el cliente generativo de la pasarela) y
**C36** (la tabla de copy de avisos y la ficha a la que el panel enlaza), los cuatro archivados.

**C40 no estaba en el plan.** Nace el 2026-09-24 durante la tarea 8.5 de C36 —la comprobación en demo
de la ficha de venta— y lo primero que apareció no fue un defecto de C36: **el panel de búsqueda
asistida llevaba todo el proyecto sirviendo por su ruta degradada**, porque
`AiSearch:EnabledByDefault` está ausente de todos los `appsettings`. Y con él, un defecto que nadie
había visto: **en esa ruta degradada los filtros se descartan en silencio**.

> **La lección que gobierna la historia entera.** Los tres tropiezos de aquella sesión son el mismo
> problema: **una capacidad apagada que la interfaz presenta como encendida.** Dos de los tres avisan;
> el de los filtros **no avisa de nada**, que es el peor de los tres. Todo lo que C40 entrega se ordena
> por *cuánto engaña hoy la pantalla*, no por cuánto cuesta.

Con esta historia **los tres modos de la venta asistida llegan al operario**: el argumentario de una
pieza y la pregunta sobre una pieza llegaron con C36; **la pregunta libre sin pieza —M1— llega aquí**.
Y llega **en el panel que ya existe**, no en una pantalla nueva: el panel ya hace la mitad —misma
recuperación, mismo selector de tienda, misma hidratación, mismo episodio por visita— y M1 es ese panel
más el enrutador, el corpus y la prosa.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado | Evidencia |
|---|---|---|
| `POST /api/ai/search` con `materials[]` y `category` | ✅ real desde C15 | [`AiSearchController.cs`](../../../backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs) |
| Panel con selector de POS por rol, episodio por visita, guarda de orden, cinco vacíos y embudo de administrador | ✅ el patrón entero y el fichero que se amplía | [`assisted.tsx`](../../../frontend/src/pages/sales/assisted.tsx) |
| `POST /v1/assist/sale` sirve **los tres modos**, M1 incluido, con enrutador, corpus y prosa | ✅ real desde C30b + C31 | [`orchestrator.py`](../../../ai-service/src/jbg_ai/assist/orchestrator.py) |
| `RetrievalRequest.filters` con `materials`, `category`, `family_id`, `exclude_product_ids` | ✅ real; entran como `AND` en el SQL, **antes de puntuar** | [`search.py:172`](../../../ai-service/src/jbg_ai/retrieval/search.py#L172) |
| `AssistRequest` | ⚠️ **no tiene `filters`**, así que M1 sabe *menos* de lo que el operario pidió | [`assist.py:43`](../../../ai-service/src/jbg_ai/api/schemas/assist.py#L43) |
| `IAiGatewayClient.AssistSaleAsync` | ⚠️ **rechaza M1 con `ArgumentException`**, y el motivo escrito es el que C40 tiene que resolver | [`AiGatewayClient.cs:671`](../../../backend/src/JoiabagurPV.Application/Services/AiGatewayClient.cs#L671) |
| `SearchLexicalAsync(terms, pointOfSaleId, take, ct)` | ❌ **sin parámetro de filtros**: la ruta degradada los tira | [`IAssistedSearchRepository.cs`](../../../backend/src/JoiabagurPV.Domain/Interfaces/Repositories/IAssistedSearchRepository.cs) |
| `ProductAiProfiles.PieceType` / `MaterialsJson` en el catálogo transaccional | ✅ **1.172 de 1.200 · 97,7 %** y 1.098 de 1.200 · 91,5 % | [`ProductAiProfile.cs`](../../../backend/src/JoiabagurPV.Domain/Entities/ProductAiProfile.cs) |
| `degradedReason` con seis valores | ⚠️ **se calcula, se registra y se descarta** al construir la respuesta | [`SalesAssistService.cs:104`](../../../backend/src/JoiabagurPV.Application/Services/SalesAssistService.cs#L104) |
| `SearchOrigin` con tres valores, persistido `HasConversion<int>()` | ✅ **un cuarto valor no abre migración** | [`SearchOrigin.cs`](../../../backend/src/JoiabagurPV.Domain/Enums/SearchOrigin.cs) |
| Tabla de copy de avisos con etiqueta neutra | ✅ desde C36; `knowledge_not_covered` **ya traducido** | [`assist-copy.ts`](../../../frontend/src/lib/assist-copy.ts) |
| Ruta de lectura de los interruptores por punto de venta | ❌ **no existe.** `aiAvailable` llega *dentro* de la respuesta, o sea después | — |
| Copia castellana de `query_out_of_domain` y `query_not_in_catalogue` | ❌ **cero**, y C36 hizo bien en no escribirla: desde la ficha eran caminos imposibles | [`assist-copy.ts:39`](../../../frontend/src/lib/assist-copy.ts#L39) |
| `uncovered` y tarea «sin cobertura» en el modo libre | ❌ **sólo existen en la rama anclada** | [`prompt.py:139`](../../../ai-service/src/jbg_ai/assist/prompt.py#L139) |
| Telemetría de uso de la ficha y panel de administrador de consultas | ❌ no existe, y **no se crea aquí**: es una cuarta zona y sale como change propio | — |

### Lo que la exploración midió y refutó

Dos pasadas el 2026-09-24. La primera contra el servicio real —**siete hallazgos, diez decisiones,
cuatro preguntas cerradas**—; la segunda contra el código —**cuatro hallazgos más, siete decisiones,
dos contradicciones internas resueltas**—. Las dos en
[`c40-exploration-decisions.md`](../../Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md),
con la tabla de estados de la pantalla en
[`c40-m1-panel-states.md`](../../Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md).

Los seis que más pesan en esta historia:

1. **El argumentario de M1 no puede llegar al operario hoy, y .NET lo rechaza por construcción.** El
   prompt `assist/v3` ordena escribir `{{price}}` y `{{stock}}` **también en las tres tareas de
   consulta libre**, `PitchPlaceholderResolver` **retira el argumentario siempre que no hay ancla** —y
   en M1 no hay ancla, por definición— y `AiGatewayClient` lanza `ArgumentException` antes de intentar
   la llamada. Medido en C30b sobre los modos anclados: `{{price}}` en **147 de 213** y `{{stock}}` en
   **188 de 213**. **Las 42 consultas del informe se midieron con `curl` contra Python**, saltándose esa
   etapa, así que su «37 respuestas con argumentario» no dice nada de lo que el operario vería.
2. **Los filtros de la ruta degradada no se aplican en absoluto, y sí se pueden aplicar.** Medido:
   `plata` con `category: pendientes` devuelve *Anillo Bruma grapas granate*, *Colgante mejillón
   doppio* y *Presión plata*. Con `PieceType` al **97,7 %** es un `JOIN` y dos `AND`.
3. **El agrupado por familia hace trabajo real y hoy se tira al pintar.** Medido sobre 8 consultas y
   `top_k=10`: **194 filas de 240 · −19,2 %**, colapsando algo en **7 de 8**. *«Colgante estrella de
   mar»* gastaría **8 de sus 30 filas** en el mismo colgante. El operario ve una fila y no sabe que
   detrás hay ocho piezas.
4. **`route=none` son dos estados y sólo `intent` los separa**, y a uno de los dos **no se le puede
   pedir al operario que reformule**: con `intent=in_domain` el clasificador corrió y se contradijo
   —devolvió veredicto servido con `index` nulo, **5 de 42 · 11,9 %**—; con `intent=unclassified` el
   clasificador **no corrió**, y pedir que reformule es echarle la culpa de una credencial ausente.
5. **M1 no tiene la salvaguarda de cobertura que M3 sí tiene.** Una consulta de conocimiento sin
   fragmentos ejecuta la tarea que dice *«Responde a la pregunta apoyándote en esos fragmentos»*
   **sin fragmentos**. El caso está medido en el propio informe y se leyó como otra cosa: *«un anillo
   que se pueda mojar en la piscina»* → ruta `both`, 15 piezas, **0 citas**.
6. **Con un filtro estrecho la abstención no puede dispararse.** Medido: sin filtro **30** candidatos,
   `tipo=diadema` **7**, `tipo=pendientes + oro` **10**. Con 7 candidatos, `candidatos_en_banda ≥ 15` es
   imposible, así que el sistema devolvería siete piezas mediocres **y escribiría un párrafo hablando
   bien de ellas** — un párrafo que hoy no existe y que M1 crea.

---

### Alcance de esta historia (sí)

Seis tramos con **línea de corte fijada de antemano**, ordenados por *cuánto engaña hoy la pantalla*.

**Tramo 1 — lo que hoy miente en silencio. Sólo .NET y frontend, y es archivable solo.**

1. **Los filtros se aplican también en la ruta degradada**, material y tipo de pieza, como filtros
   duros porque los pulsó una persona. Si por lo que sea no se aplicaran, **la pantalla lo dice**.
2. **Badge de disponibilidad con sus cuatro estados**, visible **antes** de buscar, y una **ruta de
   lectura nueva, barata y sin IA** que reporte los dos interruptores para un punto de venta.
3. **`degradedReason` sube al DTO** de .NET: seis valores que ya se calculan y se descartan. Cierra la
   limitación 3 de C34 y separa «esta pieza no está indexada» de «la IA se ha caído».
4. **Un cuarto valor de `SearchOrigin`**, sin migración, que convierte la comparación de las dos rutas
   en una consulta SQL sobre la telemetría que existe desde C04.

**Tramo 2 — el contrato se mueve, y con tres prerrequisitos.**

5. **`AssistRequest` gana `filters`**, adición pura, tocando cuatro sitios: el modelo de Python,
   `openapi.json`, `AiAssistSaleRequest` y el doble del *stub*.
6. **`assist/v5`: las tres tareas de consulta libre dejan de hablar de precio y de disponibilidad**, y
   **una causa dura en la puerta de integridad** lo garantiza cuando el modelo la ignore. El guardia de
   la pasarela se retira, con su motivo ya resuelto.
7. **La salvaguarda de cobertura llega a M1**: `uncovered` se calcula para las rutas de conocimiento y
   una **cuarta tarea de consulta libre** dice explícitamente que no se finja haber contestado.
8. **Un segundo endpoint de .NET** para la consulta libre, con su propio interruptor, su propio límite
   de peticiones, su propio presupuesto de tiempo y su propio circuito.
9. **El toggle**, dos rutas visibles y elegibles sobre la misma consulta, con el coste dicho **antes**
   de pulsarse.
10. **El castellano de los dos rechazos corteses**, que son **dos textos distintos** y no uno.
11. **La tabla de los dieciséis estados**, escrita antes de una línea de código, y la **medición de
    latencia extremo a extremo por .NET** sobre las 42 consultas del conjunto etiquetado.

**Tramo 3 — toca `retrieval-abstention`, spec viva con tres consumidores.**

12. **La abstención lee una sonda sin filtro**, ejecutada sólo cuando el operario ha filtrado y
    reutilizando el embedding ya calculado, con **dos mensajes que hoy no se distinguen**.
13. **`filters_too_narrow`** como código nuevo del vocabulario cerrado.
14. **Los dos estados de `route=none` con su copia propia**, y la **repregunta del enrutador**, que en
    M1 sí llega y devuelve el foco a la caja de consulta.
15. **La coerción a `both`** cuando el clasificador admite la consulta y no nombra índice, con la
    contradicción **observable** en el registro.

**Tramo 4 — «todos los puntos de venta», que es una frontera de autorización.**

16. **Una tercera clase de ámbito, explícita**, y un tercer perfil de claims en las rutas de
    recuperación y de assist. **Abierto a operarios y administradores**, con requisito y test que
    nombren quién puede.
17. **La etiqueta de existencias nombra la tienda** —«8 en Ciutadella Centre»— y sin tienda dice
    «Selecciona tienda para ver stock», que es la versión honesta de lo que si no sería un cero.
18. **Sin tienda, el botón de ficha de venta se deshabilita**, porque la ficha exige tienda.

**Tramo 5 — la fila usa el grupo.** «También en XS, S, M, L y 4 tallas más», con degradación al SKU
cuando falta la etiqueta de variante y nada escrito cuando el grupo trae un solo miembro.

**Tramo 6 — el embudo de observabilidad del administrador**, plegado por defecto: latencia partida en
`ai_ms` frente a `total_ms`, modelo, tokens de entrada y salida, motivo de degradación y contadores.
**Nunca euros**, y nunca nada del contenido.

### Fuera de alcance (no)

1. **La telemetría de uso y el panel de administrador sobre todas las consultas.** Es una **cuarta
   zona** —migración de EF Core— y su valor no depende de que C40 exista. Sale como change propio, y
   con él la §15.14. Sin ella, la condición de reactivación de la tarea diferida de `generate=false`
   **sigue sin ser observable**, y así se declara.
2. **La ruta del agente**, `POST /v1/assist/agent`: sigue sin consumidor .NET, y arrastra dos tareas
   diferidas de C32b que son prerrequisito. La limitación **no se cierra**.
3. **El *streaming* del argumentario** (SSE): es una capa arquitectónica entera y la puerta de
   integridad necesita el texto completo antes de decidir.
4. **Los euros.** El embudo enseña las entradas de un coste —tokens y modelo—, nunca el producto: una
   tarifa escrita en el frontend está mal el día que el proveedor la mueve.
5. **El `v5` que arregla `dangling_citation` en la ruta `both`** (1 de 42). La puerta lo caza, el coste
   es un argumentario perdido, y es trabajo de prompt y no de pantalla. Queda anotado.
6. **Bajar la tasa de `claim_not_in_pitch`**, del orden del 30 % en los dos modos. Mejoraría la
   atribución de todas las pantallas a la vez, y también está fuera.
7. **Los avisos por pieza emitidos por el servicio.** Que `warnings` describa cada pieza en vez de
   sólo la primera es lo correcto de verdad, y es cambio de contrato aparte.
8. **Caché de la respuesta asistida**, que la spec viva prohíbe para la ruta generativa.
9. **Ni `terraform/` ni `.github/workflows/`.**

---

### Decisiones de diseño ya acordadas

Las diecisiete se tomaron con el desarrollador en las dos sesiones de exploración del 2026-09-24. Las
alternativas descartadas de cada una están en el
[informe](../../Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md).

| # | Decisión | Razón |
|---|---|---|
| **D1** | **El panel de búsqueda asistida se convierte en M1.** No se construye pantalla nueva | El panel ya hace la mitad. Una pestaña aparte duplicaría el buscador para no reutilizar nada |
| **D2** | **`AssistRequest` gana `filters`**, y el contrato se mueve | Sin ello M1 **sabe menos** que el panel al que sustituye, y un operario que pulsa *pendientes* y recibe anillos no vuelve a pulsar nada. Adición pura, verificada hoja a hoja como ya hizo C31 |
| **D3** | **Un toggle entre recuperación semántica y asistida** | Dos rutas elegibles sobre la misma consulta. Y una razón de más que la usabilidad: la rúbrica pide comparar configuraciones y hoy eso sólo se demuestra en el arnés |
| **D4** | **Badge permanente de disponibilidad**, visible antes de buscar | Los tres tropiezos de la sesión fueron capacidades apagadas que la pantalla presentaba como encendidas |
| **D5** | **Los filtros también en la ruta degradada**, y si no se aplicaran, la pantalla lo dice | Es lo que el operario ve y lo que espera. `PieceType` al 97,7 %: un `JOIN` y dos `AND`. Un chip pulsado que no filtra es la única de las tres averías que engañaba en silencio |
| **D6** | **«Todos los puntos de venta»**, y el ámbito se abre | No abre una puerta nueva: **cierra una incoherencia**. `GET /api/inventory/product/{id}` ya devuelve el desglose de las tres tiendas a cualquier operario autenticado |
| **D7** | **La etiqueta de existencias nombra la tienda**; sin tienda, «Selecciona tienda para ver stock» | Con varias tiendas en juego, *«esta tienda»* es ambiguo, y la ambigüedad en una cifra de stock es lo que cuesta una venta. Cambiar de tienda **no llama a ningún modelo** |
| **D8** | **Los avisos de pieza no se pintan en el listado**, y **los de consulta sí** | `warnings` describe **la primera pieza del primer grupo**, no el conjunto: pintarlo como banda superior sería mentir. Pero `refusal_codes` se apila en esa misma lista, así que la partición es **por sujeto del aviso** y no por lista |
| **D9** | **La abstención se mide antes de filtrar** | Tres razones escritas en el propio repositorio, y una medida: con filtro estrecho la abstención **no puede dispararse** (7 candidatos contra un mínimo de 15) |
| **D10** | **La fila de M1 enseña su grupo**, no sólo a su mejor miembro | El agrupado ahorra el **19,2 %** de las filas y la información que lo justifica se tira al pintar. Y es información que el modo semántico **no puede dar**: su lista es plana |
| **D11** | **`assist/v5` + causa dura `placeholder_in_free_query`** | El prompt es la petición, la puerta es la garantía: *«un guardrail es código, no una frase en el prompt»*. Y hace la frecuencia **medible partida por causa**, que es como este repositorio lee su puerta |
| **D12** | **`uncovered` en M1 y una cuarta tarea de consulta libre sin cobertura** | Sin ella, una consulta de conocimiento sin corpus recibe la instrucción de apoyarse en fragmentos que no existen. La copia castellana ya existe desde C36 |
| **D13** | **Una tercera clase de ámbito, explícita**, abierta a operarios | Es el patrón que el propio código declara: *«not a relaxation of the first: it is a different scope»*. Una claim **ausente** hace que el prefiltro no se aplique, no que «case con todo», y **falla cerrado** en cualquier ruta que la exija |
| **D14** | **Un segundo endpoint de .NET**, no un campo `mode` | Cuatro propiedades operativas ya difieren y ya están modeladas por feature: interruptor, límite (30/min contra 10/min), presupuesto (2.500 ms contra 10.000 ms) y circuito. El límite de peticiones es **un atributo de endpoint**, así que un solo endpoint obligaría a elegir un único valor |
| **D15** | **`SearchOrigin` gana un cuarto valor** | Se persiste con `HasConversion<int>()`, así que no abre migración, y convierte la ablación del toggle en una consulta SQL. El comentario del enum ya dice que su tercer valor existe para ser *«el brazo de control»* |
| **D16** | **El badge tiene cuatro estados y necesita una ruta de lectura nueva** | `aiAvailable` llega *dentro* de la respuesta. Y hay un **tercer eje** que ningún interruptor ve: el enrutador. Son dos avisos —uno antes, uno durante—, no uno |
| **D17** | **Sonda sin filtro para la abstención**, sólo cuando hay filtros | Post-filtrar destriparía los filtros estrechos —`diadema` da 7 candidatos de todo el índice—, y la alternativa barata *«hay piezas que encajan, pero ninguna es X»* **escribiría una frase falsa** cuando la consulta es incontestable |

### Las cuatro preguntas cerradas, y las tres recomendaciones que resuelven los hallazgos

| # | Pregunta | Respuesta |
|---|---|---|
| **Q1** | ¿El argumentario en cada búsqueda, o a petición? | **En cada búsqueda asistida.** El enrutador corre en la misma llamada, así que el rechazo cortés **llega a tiempo**. La regla de C16 se conserva íntegra: no hay búsqueda al teclear, ni al cambiar un filtro, ni al cambiar de tienda |
| **Q2** | ¿Y una cita retirada por la puerta de integridad? | **Decirlo**: «sin fuente verificable». Aparecerá en **una de cada cuatro** respuestas de conocimiento de M1, así que **discreta** —una línea junto al argumentario— y **sin alarmar**: no es una alucinación cazada |
| **Q3** | ¿Y una consulta `in_domain` sin ruta? | **Pedir que se reformule** — pero **sólo en uno de los dos estados**. Los resultados se enseñan igual y la frase ocupa el hueco del argumentario, no el de la lista |
| **Q4** | ¿El filtro de materiales, duro o blando? | **Duro, porque lo pulsó una persona.** El riesgo se acepta y se declara: el **8,5 %** del catálogo sin materiales extraídos desaparece al filtrar por material |
| **P1** | El estado de «admitida sin índice» | **Se arregla en el enrutado, no en la pantalla**: coerción a `both`, con `router_index_absent` en el registro |
| **P2** | El filtro estrecho | **Código nuevo del vocabulario cerrado**, y la partición de D8 **por sujeto del aviso** |
| **P3** | La ruta de conocimiento | **La ausencia de piezas no es un vacío** y no se anuncia como tal |

### Referencias

- Change de OpenSpec: `openspec/changes/add-frontend-free-query-panel/` (C40), rama
  `c40-add-frontend-free-query-panel`
- Ticket: [T-AIENG-040](../../../openspec/changes/archive/2026-09-25-add-frontend-free-query-panel/ticket.md)
- Informes de exploración:
  [`c40-exploration-decisions.md`](../../Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md)
  · [`c40-m1-panel-states.md`](../../Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md)
- Ficha del plan: [§3 · C40](../../Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- Diseño RAG: [§4, §6.4, §7.3, §7.7, §11.2, §15.12, §15.13, §15.14](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- Capabilities que se modifican:
  [`assisted-search-panel`](../../../openspec/specs/assisted-search-panel/spec.md) ·
  [`ai-assisted-search`](../../../openspec/specs/ai-assisted-search/spec.md) ·
  [`assist-generation`](../../../openspec/specs/assist-generation/spec.md) ·
  [`retrieval-abstention`](../../../openspec/specs/retrieval-abstention/spec.md) ·
  [`vector-retrieval`](../../../openspec/specs/vector-retrieval/spec.md) ·
  [`ai-service-api-contracts`](../../../openspec/specs/ai-service-api-contracts/spec.md) ·
  [`ai-sales-assist`](../../../openspec/specs/ai-sales-assist/spec.md) ·
  [`ai-search-telemetry`](../../../openspec/specs/ai-search-telemetry/spec.md) ·
  [`ai-gateway-client`](../../../openspec/specs/ai-gateway-client/spec.md) ·
  [`ai-service-auth`](../../../openspec/specs/ai-service-auth/spec.md)
- Historias anteriores: [HU-AIENG-016](HU-AIENG-016.md) *(el panel que se amplía)* ·
  [HU-AIENG-031](HU-AIENG-031.md) *(el enrutador)* · [HU-AIENG-034](HU-AIENG-034.md) *(el cliente
  generativo)* · [HU-AIENG-036](HU-AIENG-036.md) *(la ficha y la tabla de copy)*
- Testing: [testing-frontend.md](../../testing-frontend.md) · [testing-backend.md](../../testing-backend.md),
  las dos en su sección *Estado de la suite: fallos conocidos*
- Componentes reutilizables: [analisis-metronic-frontend.md](../../Propuestas/analisis-metronic-frontend.md)
- Épica: [EP15 — Venta Asistida, Sustitutos y Agentes](../../epicas.md), que **se reabre**

---

## Criterios de Aceptación

### Escenario 1: Un chip pulsado filtra siempre, y si no filtrara se diría

- **Dado que** el operario pulsa el tipo de pieza *pendientes* y el material *plata*,
- **Cuando** busca **por cualquiera de las dos rutas**, incluida la degradada por texto,
- **Entonces** todos los resultados son pendientes de plata,
- **Y** ninguno es un anillo ni un colgante,
- **Y** si por lo que fuera un filtro pulsado no se hubiera podido aplicar, **la pantalla lo dice** en
  vez de dejar el chip pulsado engañando,
- **Y** el operario que no pulsa ningún chip recibe el catálogo entero, sin filtro.

### Escenario 2: El operario sabe si el asistente está disponible antes de buscar

- **Dado que** el operario abre el panel,
- **Cuando** la pantalla termina de cargar y **antes de que haya buscado nada**,
- **Entonces** ve si el asistente está disponible para esa tienda,
- **Y** si la búsqueda asistida está apagada, **la opción del toggle se deshabilita diciendo por qué**
  en vez de fallar al pulsarla,
- **Y** ese aviso es independiente del que aparezca luego con los resultados,
- **Y** comprobarlo **no gasta ninguna llamada a un modelo**.

### Escenario 3: Las dos rutas se eligen sobre la misma consulta, y la interfaz dice lo que cuestan

- **Dado que** el operario ha escrito una consulta,
- **Cuando** mira el selector de ruta,
- **Entonces** ve que una es una búsqueda rápida y la otra una respuesta asistida, **con su diferencia
  de coste dicha antes de pulsar**,
- **Y cuando** elige la asistida, se emite **exactamente una** petición y se ve un estado de carga
  desde el primer instante, no una pantalla en blanco,
- **Y** ninguna de las dos se dispara al teclear, al cambiar un filtro ni al cambiar de tienda,
- **Y** si agota su cuota del minuto, el mensaje es **distinto** del de la IA no disponible.

### Escenario 4: Una pregunta de oficio se responde sin tener ninguna pieza delante

- **Dado que** el cliente pregunta si la plata se puede mojar,
- **Cuando** el operario lo escribe en el panel con la ruta asistida,
- **Entonces** recibe una respuesta apoyada en la documentación de la casa, con sus citas,
- **Y** la ausencia de piezas en la lista **no se presenta como «sin resultados»**, porque la respuesta
  es la que se pidió,
- **Y** una cita que es un **compromiso de la casa** se distingue a simple vista de un hecho general.

### Escenario 5: Una pregunta que no es de joyería se rechaza con cortesía, y de dos maneras distintas

- **Dado que** el operario escribe algo que no es del negocio —«¿qué tiempo hará mañana?»—,
- **Cuando** llega la respuesta,
- **Entonces** la pantalla dice que eso no es una pregunta de joyería,
- **Y cuando** lo que escribe es de joyería pero de un objeto que la casa no vende —«¿vendéis relojes
  automáticos?»—, el texto es **otro y distinto**,
- **Y** ninguno de los dos se parece a una abstención del catálogo, que significa otra cosa,
- **Y** en ninguno de los dos se muestra el código en bruto.

### Escenario 6: Cuando la consulta no dice bastante, el sistema pregunta en vez de adivinar

- **Dado que** el operario escribe una consulta que no determina qué busca —«algo bonito»—,
- **Cuando** llega la respuesta,
- **Entonces** la pantalla muestra **la pregunta que el servicio devuelve**, tal cual, sin reescribirla,
- **Y** el foco vuelve a la caja de consulta, que es la acción que la pregunta pide,
- **Y** no se ha recuperado ni se ha redactado nada, así que no se enseña ninguna lista.

### Escenario 7: «No te he entendido» y «no estoy disponible» no son lo mismo

- **Dado que** la respuesta llega con resultados y sin argumentario,
- **Cuando** el motivo es que el clasificador corrió y no supo encaminar la consulta,
- **Entonces** se invita al operario a formularla de otra manera,
- **Y cuando** el motivo es que **el clasificador no llegó a correr**, el mensaje es **distinto** y
  **no se le pide reformular nada**, porque el problema no es suyo,
- **Y** en los dos casos **los resultados se enseñan igual**, y ocupan la lista,
- **Y** en los dos casos **no se pinta ninguna cita**, porque una cita sin afirmación no atribuye nada.

### Escenario 8: Un filtro estrecho se distingue de una consulta incontestable

- **Dado que** el operario describe algo que el catálogo sí puede atender y además filtra por un tipo
  de pieza del que hay muy pocas —una diadema de oro—,
- **Cuando** llega la respuesta,
- **Entonces** la pantalla dice que **hay piezas que encajan con su descripción pero ninguna es una
  diadema de oro**,
- **Y cuando** lo que describe no lo puede atender el catálogo en absoluto, el mensaje es **otro**: que
  no hay nada que encaje con lo que describe,
- **Y** los dos mensajes terminan en una acción distinta: quitar el filtro, o describirlo de otra forma.

### Escenario 9: Una fila dice qué más lleva su familia

- **Dado que** un resultado pertenece a una familia de la que el índice conoce varias variantes,
- **Cuando** se pinta la fila en el modo asistido,
- **Entonces** la fila dice qué otras tallas o características lleva la familia,
- **Y** si alguna variante no tiene etiqueta, se nombra por su SKU en vez de dejar el hueco,
- **Y** si el grupo trae un solo miembro, **no se escribe nada**,
- **Y** la fila **no repite el trabajo de la ficha**: anuncia que hay familia, no vende desde el
  listado.

### Escenario 10: Un argumentario sin fuente verificable se dice, y no alarma

- **Dado que** el servicio redactó una respuesta y la puerta de integridad retiró las citas que el
  modelo declaró —algo que ocurre en cerca de una de cada cuatro respuestas de conocimiento,
- **Cuando** se pinta el argumentario,
- **Entonces** aparece una línea discreta que dice que no hay fuente verificable,
- **Y** ese texto **no insinúa una invención**: la cita existía y lo que no se pudo verificar es el
  tramo que sostenía,
- **Y** se distingue de una ruta de catálogo, donde no haber citas es lo correcto,
- **Y cuando** la puerta retiró el argumentario entero, el mensaje es **otro** y se distingue de no
  haberse generado.

### Escenario 11: Buscar sin acotar tienda es posible, y lo que no se puede saber no se finge

- **Dado que** el operario elige el ámbito «todos los puntos de venta» para asistir una venta de otra
  tienda,
- **Cuando** busca,
- **Entonces** recibe resultados de todo el catálogo,
- **Y** en cada fila, donde habría una cifra de existencias, dice **«Selecciona tienda para ver stock»**
  y **no un cero**,
- **Y** el botón de ver la ficha de venta **está deshabilitado**, porque la ficha exige tienda,
- **Y cuando** elige una tienda concreta, la etiqueta pasa a nombrarla —«8 en Ciutadella Centre»— y
  **ese cambio no llama a ningún modelo**.

### Escenario 12: El administrador ve lo que costó, y el operario no

- **Dado que** un administrador ha hecho una búsqueda asistida,
- **Cuando** despliega el embudo, que está **plegado por defecto**,
- **Entonces** ve la latencia partida entre lo que tardó la IA y lo que tardó el total, el modelo, los
  tokens de entrada y salida, el motivo de degradación si lo hubo, y los contadores del embudo,
- **Y** no ve ningún importe en euros,
- **Y** no ve ni el argumentario ni la consulta dentro del embudo,
- **Y** un operador **no ve ese bloque en absoluto**.

### Escenario 13: Una pieza que no está indexada se distingue de una caída

- **Dado que** una pieza se dio de alta después de la última sincronización del índice,
- **Cuando** el operario abre su ficha de venta,
- **Entonces** la pantalla dice que **esa pieza todavía no está preparada**,
- **Y** ese mensaje es **distinto** del de la IA no disponible,
- **Y** esa distinción vale también cuando la causa es que el interruptor está apagado o que la
  credencial fue rechazada.

### Escenario 14: Fuera de alcance explícito — ni telemetría de uso, ni agente, ni euros

- **Dado que** se revisa lo entregado,
- **Cuando** se busca la telemetría de uso de la ficha,
- **Entonces** **no existe**: no hay tabla nueva ni migración de EF Core, y la limitación §15.14 se
  conserva, con la condición de reactivación de `generate=false` **todavía no observable**,
- **Y** la ruta del agente sigue **sin consumidor .NET** y sin pantalla,
- **Y** el argumentario **no llega en *streaming***,
- **Y** en ninguna parte de la interfaz aparece un importe en euros de coste de IA,
- **Y** la ficha de venta de C36 se comporta igual que antes, salvo que ahora sabe decir por qué
  degradó.

---

## Notas adicionales

**Actor.** **Operador**, y en dos situaciones que hoy no tiene: preguntar sin pieza delante, y asistir
una venta de otra tienda. El **Administrador** gana además el embudo de observabilidad y puede usar
cualquier punto de venta activo, con la misma regla del panel.

**Encaje con los apuntes del máster.**

- **S4 · De interfaz conversacional a interfaz de producto** es el respaldo más fuerte de D1 y D3: el
  panel no es un chat, es **«chat con parámetros»** —consulta, chips y selector de modo—, el mismo
  cuadrante que Perplexity con su selector *Search / Academic*. *«La información sobre qué pedir se
  puede hornear en la interfaz»* es literalmente el badge, las consultas de ejemplo y los chips. Y
  *«¿dónde vive el prompt?»* ya está bien resuelto aquí: vive versionado en el backend, que es lo que
  permite el `v5` de D11.
- **S9 · Retrieval que no es sólo cosine** es el que **descarta el post-filtrado** de D17, con su propia
  frase. Y da el marco que faltaba: aquí los filtros van de baja selectividad (`pendientes`, 30 de 30)
  a alta (`diadema`, 7 de todo el índice), así que **ni pre ni post sirven para todos**.
- **S16 · Un sistema debe saber decir «no lo sé»**: los tres caminos —responder, abstenerse con
  honestidad, escalar— son la tabla de estados. El filtro estrecho y el `route=none` son
  *safe-completion* de libro, porque **dicen qué haría falta**. Y su tesis central —*«un guardrail es
  código, no una frase en el prompt»*— es la segunda mitad de D11.
- **S11 · Citación y atribución verificable** respalda Q2 y su tratamiento discreto.
- **Una matización consciente a la propia decisión D3**: **el toggle no es un A/B test**. Lo elige el
  usuario y no un reparto de tráfico, así que sus dos poblaciones están sesgadas por quién elige qué.
  Es una **demostración** de la ablación; lo que la convierte en medición es el cuarto valor de
  `SearchOrigin` más la telemetría de C04. El README del PF debe decirlo así y no de más.

**Limitaciones que esta historia cierra.** Tres del §15 del diseño: la **12** —la pregunta libre sin
pieza no tiene pantalla: desde aquí es una caja de texto—, la **13** —el rechazo cortés no tiene
pantalla: desde M1 los dos códigos sí llegan— y la **limitación 3 de C34** —una pieza no indexada no se
distingue de una caída: se cierra con un campo que .NET ya calcula y descarta—.

**Limitaciones que se declaran y no se cierran.**

1. **El agente sigue sin consumidor** y sin pantalla de conversación.
2. **La telemetría de uso no existe**, así que la condición de reactivación de `generate=false` sigue
   sin ser observable con datos.
3. **La espera de la ruta asistida no se puede partir sin *streaming***, y el presupuesto de diez
   segundos **ya está en su techo documentado**, con un suelo validado de ocho.
4. **`dangling_citation` vive en la ruta `both`**, a 1 de 42. La puerta lo caza y el coste es un
   argumentario perdido.
5. **La tasa de `claim_not_in_pitch` es del orden del 30 %** en los dos modos, y bajarla es trabajo de
   prompt.
6. **Los avisos se calculan sólo para la primera pieza del primer grupo**, así que en M1 no se pintan.

**Change de OpenSpec por el que se implementa.** `openspec/changes/add-frontend-free-query-panel/`,
rama `c40-add-frontend-free-query-panel`.

---

## Tareas

1. **Puerta de entrada**: línea base de las **dos** suites **por nombres de test**, no por número
   —`git stash push -u`, ejecutar, `git stash pop`—; las dos vienen rojas de fábrica (frontend 113 o
   114 de 597; backend con decenas de fallos preexistentes). `openspec validate --all --strict` en
   verde y `sha256` de `ai-service/openapi.json` anotado.
2. **Tramo 1 · filtros en la ruta degradada**: `SearchLexicalAsync` gana filtros, con `JOIN` a
   `ProductAiProfiles` y dos `AND`; tests de integración con Testcontainers.
3. **Tramo 1 · la ruta de lectura de los interruptores** y el badge con sus cuatro estados.
4. **Tramo 1 · `degradedReason` al DTO** y la pantalla que lo distingue en la ficha y en el panel.
5. **Tramo 1 · el cuarto `SearchOrigin`**, con su documentación y sin migración.
6. **Tramo 2 · `filters` en `AssistRequest`**, `openapi.json` regenerado y verificado **hoja a hoja**,
   `AiAssistSaleRequest` y el doble del *stub* puestos al día.
7. **Tramo 2 · `assist/v5`** con las tres tareas libres sin precio ni disponibilidad, la **cuarta tarea
   sin cobertura**, `uncovered` en M1 y la causa dura `placeholder_in_free_query`.
8. **Tramo 2 · el segundo endpoint de .NET** con su interruptor, su límite, su presupuesto y su
   circuito; el guardia de la pasarela retirado.
9. **Tramo 2 · el toggle, el castellano de los dos rechazos y la tabla de los dieciséis estados.**
10. **Tramo 2 · medición de latencia p50/p95 extremo a extremo por .NET** sobre las 42 consultas, y
    **recuento de marcadores antes y después de `v5`** — la cifra que decide si M1 tiene prosa.
11. **Tramo 3 · la sonda sin filtro**, `filters_too_narrow`, los dos estados de `route=none`, la
    repregunta y la coerción a `both` con `router_index_absent`.
12. **Tramo 4 · la tercera clase de ámbito**, el tercer perfil de claims, la etiqueta que nombra la
    tienda y el botón de ficha deshabilitado sin tienda, con tests de rechazo por cada operación que
    debe seguir exigiendo punto de venta.
13. **Tramo 5 · la fila que usa el grupo.**
14. **Tramo 6 · el embudo de administrador** ampliado, plegado por defecto y sin euros.
15. **Verificación de completitud**: recorrer **campo a campo** `SalesAssistResponse`,
    `AssistedSearchResponse` y la respuesta nueva, y por cada campo **señalar dónde se pinta o declarar
    por qué no**. Es la disciplina que C36 aplicó a sus siete códigos y la que habría cazado las tres
    infracciones que la exploración encontró.
16. **Specs**: una capability nueva para el endpoint de consulta libre y `## MODIFIED` en las nueve
    vivas que se tocan, con la descripción de cada requisito **en una sola línea física**.
17. **Comprobación con datos reales** en local, con `STUB_MODE=false` y credencial real: una consulta
    de catálogo, una de conocimiento, una mixta, un rechazo de cada tipo, una repregunta, un filtro
    estrecho y el ámbito «todos».
18. **Documentación**: `Documentos/epicas.md`, plan de changes, diseño (§15.12 y §15.13 cerradas,
    §15.14 matizada), `frontend/README.md`, `backend/README.md`, `ai-service/README.md`,
    `openspec/DEFERRED_TASKS.md` y la **persistencia del artefacto** de la pasada de verificación.

---

## Estimaciones y atributos de priorización

| Atributo | Valor |
|---|---|
| Puntos de historia | _Pendiente_ — a fijar en refinamiento |
| Impacto en usuario / valor de negocio | **5/5** — arregla **tres capacidades que la pantalla presentaba como encendidas y estaban apagadas**, una de ellas en silencio, y pone el tercer modo delante del operario. Cierra **tres limitaciones declaradas** del §15 |
| Urgencia | **5/5** — es el **nodo de arranque de lo que queda**, `C40 → C38 → C39`, y va **antes de C38** porque sube el prompt a `v5` y mueve la fase de la abstención |
| Complejidad / esfuerzo | **5/5** — **tres capas y una frontera de autorización**, el contrato congelado se mueve, y toca **diez capabilities vivas**. La dificultad no es ninguna pieza: es que **dieciséis estados tienen que distinguirse sin mentir** y que el tramo 2 tiene tres prerrequisitos que si se saltan entregan un panel asistido **sin prosa** |
| Riesgos | **El argumentario de M1 no llega si `v5` no entra** (mitigado: es prerrequisito declarado del tramo 2, con su cifra de verificación). **El p95 puede sentarse en el techo**: C34 midió p95 7,1 s sin enrutador y M1 le suma ~2 s contra un presupuesto de 10 s que no se puede subir (mitigado por el toggle y por el corte pre-autorizado de no generar en la ruta `catalog`). **D6 relaja una invariante fijada con test** (mitigado por una tercera clase de ámbito explícita y tests de rechazo, no por una excepción). **Diez capabilities vivas modificadas** (mitigado porque la línea de corte agrupa tramos por subconjunto de specs, así que un tramo aplazado no deja specs a medias). **Las dos suites vienen rojas de fábrica** y el frontend además oscila entre 113 y 114 por un test dependiente del orden (mitigado por la línea base por nombres) |
| Dependencias | **C16, C31, C34 y C36** archivados. **No se abre a la vez que C16 ni C36** (misma página y servicio del frontend) ni a la vez que **C21, C22 o C25** (pipeline de ranking en `retrieval/`). **Y no se solapa con C38**: es orden obligado, no disciplina de rama |

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| **Q-1** | ¿Capability nueva para el endpoint de consulta libre, o se amplía `ai-assisted-search`? | **Nueva**, siguiendo el precedente de `ai-sales-assist` frente a `ai-assisted-search`: es otro interruptor, otro límite, otro presupuesto y otro circuito. El panel del frontend sí se queda en `assisted-search-panel` modificada, porque D1 dice que no hay pantalla nueva |
| **Q-2** | ¿Cuál es la ruta del endpoint nuevo? | `POST /api/ai/search/assisted`, bajo el árbol que el operario ya conoce y sin inventar un nombre de dominio nuevo |
| **Q-3** | ¿El toggle recuerda la última ruta elegida entre visitas? | **No.** Un episodio por visita, y recordar la ruta cara es la forma de gastarla sin querer. La ruta por defecto es la **semántica**, que es la barata |
| **Q-4** | ¿La consulta libre reutiliza el límite de 10/min de la ficha, o tiene el suyo? | **El suyo**, en su propia sección de configuración: la ficha se abre una vez por pieza y el panel se usa en ráfaga, así que compartir el cupo dejaría a una de las dos sin poder trabajar |
| **Q-5** | ¿Quién puede usar «todos los puntos de venta»? | **Operarios y administradores** (D6 y D13), con requisito y test que lo nombren. La variante conservadora —sólo administrador— es el corte si el tramo 4 aprieta |
| **Q-6** | ¿La consulta de M1 se guarda en `ProductSearchEvent.SearchText`, como la del panel de hoy? | **Sí**, por coherencia con lo que ya persiste desde C04, y **con su limitación de retención del §15.11 heredada y declarada**. Lo que **no** se guarda nunca es la pregunta de la ficha, que es de otra naturaleza |
| **Q-7** | ¿El embudo enseña `usage.model` como clave de precio? | **No.** Se enseña el modelo y los tokens, nunca el producto: en la ruta del agente `usage.model` nombra sólo la última de hasta tres etapas, y enseñar la multiplicación aquí invitaría a copiarla allí, donde es falsa |
| **Q-8** | ¿La coerción a `both` de P1 necesita su propio requisito de spec, o es interna? | **Requisito propio** en `assist-generation`, porque cambia qué respuesta recibe un consumidor en el 11,9 % de las consultas libres. Lo interno es la causa de registro |
| **Q-9** | ¿Se persiste el artefacto de la pasada de verificación de los 16 estados? | **Sí**, con `run_id`, `git_sha` y `prompt_version`, como C30b, C31 y C32b. La pasada de 42 de la exploración **no quedó guardada**, y esa es la razón de que se pida |

**Opción por defecto si el *apply* descubre un detalle menor no listado:** la más estrecha que **no**
añada migración de EF Core, **no** cambie el comportamiento de la ficha de C36 más allá de
`degradedReason`, **no** retire ni cambie de tipo ningún campo del contrato congelado, y **no** suprima
ningún dato que el backend haya emitido.
