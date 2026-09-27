## Why

La comprobación en demo de C36 destapó que **el panel de búsqueda asistida llevaba todo el proyecto
sirviendo por su ruta degradada** —`AiSearch:EnabledByDefault` está ausente de todos los
`appsettings`— y que **en esa ruta los filtros de material y tipo de pieza se descartan en silencio**:
los chips seguían pulsados y no filtraban nada. Los tres tropiezos de aquella sesión son el mismo
problema, **una capacidad apagada que la interfaz presenta como encendida**, y dos de los tres avisan
mientras el de los filtros no avisa de nada.

Al mismo tiempo, **el tercero de los tres modos de la venta asistida —la pregunta libre sin pieza, M1—
sigue sin pantalla** (§15.12 del diseño) y con él **el rechazo cortés del enrutador de C31** (§15.13),
porque `classify_query` corre sólo en M1 y las dos rutas de C36 son siempre ancladas. Las dos
limitaciones se cierran poniendo M1 **en el panel que ya existe**, que hace la mitad del trabajo —misma
recuperación, mismo selector de tienda, misma hidratación, mismo episodio por visita—.

## What Changes

**Ordenado por cuánto engaña hoy la pantalla, no por cuánto cuesta.** Seis tramos con línea de corte
fijada de antemano; el tramo 2 **no admite corte**.

**Tramo 1 — lo que hoy miente en silencio. Sólo .NET y frontend, archivable solo.**

- Los **filtros se aplican también en la ruta degradada**, duros porque los pulsó una persona
  (`PieceType` al 97,7 %: un `JOIN` y dos `AND`). Si un filtro pulsado no pudiera aplicarse, **la
  pantalla lo dice**.
- **Badge de disponibilidad con cuatro estados, visible antes de buscar**, y una **ruta de lectura nueva
  sin IA** que reporta los dos interruptores de un punto de venta. Hoy `aiAvailable` sólo llega *dentro*
  de la respuesta, o sea después.
- **`degradedReason` sube al DTO** de la ficha: seis valores que `SalesAssistService` ya calcula, registra
  y descarta. Cierra la limitación 3 de C34 y separa `product_not_indexed` de `ai_unavailable`.
- **Cuarto valor de `SearchOrigin`**, `AssistedGenerative`, **sin migración** porque la columna es `int`.
  Convierte la comparación de las dos rutas en una consulta SQL sobre la telemetría de C04.

**Tramo 2 — el contrato se mueve, y con tres prerrequisitos.**

- **`AssistRequest` gana `filters`** — **adición pura**, ningún campo se retira ni cambia de tipo, y el
  snapshot se verifica hoja a hoja. Sin ello M1 sabe *menos* de lo que el operario pidió.
- **`assist/v5`: las tres tareas de consulta libre dejan de hablar de precio y de disponibilidad**, más
  una **cuarta tarea sin cobertura**, y **una causa dura de puerta `placeholder_in_free_query`** activa
  sólo cuando no hay pieza anclada. **PRERREQUISITO**: `PitchPlaceholderResolver` retira el argumentario
  **siempre** que no hay ancla y `v3` ordena escribir los marcadores también en el modo libre —medido en
  C30b: 147 de 213 y 188 de 213—, así que sin esto el panel asistido sale **sin prosa**.
- **`uncovered` se calcula también en M1**, emitiendo `knowledge_not_covered`, cuya copia castellana ya
  existe desde C36. Hoy una consulta de conocimiento sin fragmentos ejecuta la tarea que pide apoyarse
  en fragmentos que no existen.
- **BREAKING (interno)**: se **retira el guardia** de `AiGatewayClient` que rechaza la consulta libre con
  `ArgumentException`, porque su motivo queda resuelto y no simplemente asumido.
- **Un segundo endpoint de .NET**, `POST /api/ai/search/assisted`, con **su propio interruptor, su
  propio límite de peticiones, su propio presupuesto y su propio circuito**: las cuatro propiedades ya
  difieren (30/min contra 10/min, 2.500 ms contra 10.000 ms) y el límite de peticiones es un atributo de
  endpoint.
- **Toggle** entre la ruta semántica y la asistida sobre la misma consulta, con el coste dicho **antes**
  de pulsarse, y el **castellano de los dos rechazos corteses**, que son dos textos distintos.
- **La tabla de los dieciséis estados** escrita antes de una línea de código, y la **latencia p50/p95
  extremo a extremo por .NET** medida sobre las 42 consultas del conjunto etiquetado.

**Tramo 3 — la abstención.**

- **La decisión de abstenerse lee una sonda vectorial sin filtro**, ejecutada sólo cuando el operario ha
  filtrado y reutilizando el embedding ya calculado. Hoy con un filtro estrecho la abstención **no puede
  dispararse** (`diadema` da 7 candidatos contra un mínimo de 15), así que se devolverían siete piezas
  mediocres **y M1 escribiría un párrafo hablando bien de ellas**.
- **`filters_too_narrow`** como código nuevo del vocabulario cerrado, emitido también en la ruta
  semántica porque la sonda vive en `retrieval/`.
- **`route=none` se parte en dos estados** que sólo `intent` separa, con copia distinta: al del
  clasificador degradado **no se le pide al operario que reformule**. Y **la coerción a `both`** cuando
  el clasificador admite la consulta y no nombra índice (5 de 42 · 11,9 %), con la contradicción
  observable como `router_index_absent` en el registro.
- **La repregunta del enrutador**, que en M1 sí llega y devuelve el foco a la caja de consulta.

**Tramo 4 — «todos los puntos de venta».**

- **BREAKING (invariante con test)**: una **tercera clase de ámbito** de llamada, explícita, y un
  **tercer perfil de claims** en las rutas de recuperación y de assist. Abierta a **operarios y
  administradores**. Toda operación que exija punto de venta debe **rechazarla con test**.
- **La etiqueta de existencias nombra la tienda**; sin tienda dice «Selecciona tienda para ver stock» y
  el botón de ficha **se deshabilita**.

**Tramo 5** — la fila **enseña su grupo**: «también en XS, S, M, L y 4 tallas más», con degradación al
SKU y nada escrito con un solo miembro. El agrupado ya ahorra el 19,2 % de las filas y hoy ese dato se
tira al pintar.

**Tramo 6** — el **embudo de observabilidad del administrador**: `ai_ms` frente a `total_ms`, modelo,
tokens, motivo de degradación y contadores. **Nunca euros**, y nada del contenido.

**Fuera de alcance, declarado:** la telemetría de uso y su panel de administrador (cuarta zona, con
migración de EF Core — sale como change propio); la ruta del agente; el *streaming* del argumentario;
el `v5` que arregla `dangling_citation` en la ruta `both`; y los avisos por pieza emitidos por el
servicio.

## Capabilities

### New Capabilities

- `ai-free-query-search`: la ruta .NET de la consulta libre —`POST /api/ai/search/assisted`— con su
  interruptor por punto de venta, su límite de peticiones, su presupuesto y su circuito propios; la
  ruta de disponibilidad sin IA que alimenta el badge; el ámbito «todos los puntos de venta» y quién
  puede usarlo; la respuesta agrupada por familia con argumentario, citas, intención, abstención y
  motivo de degradación; y el origen de telemetría propio que hace medible la comparación de las dos
  rutas.

### Modified Capabilities

- `assisted-search-panel`: el panel gana el toggle con su coste dicho antes de pulsarse, el badge de
  cuatro estados leído antes de buscar, los dieciséis estados de M1 distinguidos, la partición de avisos
  por sujeto, la fila que enseña su grupo, la etiqueta de existencias que nombra la tienda y el embudo
  ampliado sin euros.
- `ai-assisted-search`: los filtros de material y tipo de pieza se aplican **también en la ruta
  degradada**, y una imposibilidad de aplicarlos se declara en la respuesta en vez de callarse.
- `assist-generation`: la petición acepta filtros de catálogo; el modo libre no habla de precio ni de
  disponibilidad y una causa dura lo garantiza; nace la cuarta tarea de consulta libre sin cobertura y
  `uncovered` se calcula también ahí; y un veredicto servido sin índice se encamina a los dos índices en
  vez de no ejecutar ninguna tarea.
- `retrieval-abstention`: la decisión se toma sobre el perfil de distancias **sin filtrar**, y ese perfil
  se persiste para que la calibración siga pudiendo re-puntuar una pasada filtrada.
- `vector-retrieval`: la sonda sin filtro como segunda sentencia, secuencial y emitida sólo cuando la
  petición trae filtros; el prefiltrado de los candidatos se conserva intacto.
- `ai-service-api-contracts`: `AssistRequest` gana `filters` y el snapshot se regenera como adición pura.
- `ai-sales-assist`: la respuesta de la ficha reenvía el motivo de degradación con sus seis valores.
- `ai-search-telemetry`: un cuarto origen de búsqueda distingue la ruta generativa de la semántica, sin
  migración.
- `ai-gateway-client`: se retira el rechazo de la consulta libre; nace una tercera clase de ámbito,
  refusada por toda operación que exija punto de venta.
- `ai-service-auth`: un tercer perfil de claims para las rutas que pueden operar sin ámbito de punto de
  venta.

## Impact

**Tres capas y una frontera de autorización**, más el contrato congelado.

- **`ai-service/`**: `prompts/assist/v5.md` (nuevo), `api/schemas/assist.py`, `assist/prompt.py`,
  `assist/modes.py`, `assist/orchestrator.py`, `assist/routing.py`, `assist/constants.py`,
  `assist/verification.py`, `retrieval/orchestrator.py`, `api/auth.py`, `api/deps.py`,
  `stubs/responses.py` y **`openapi.json` regenerado**.
- **`backend/`**: `IAssistedSearchRepository` y su implementación, `SearchOrigin`, `AiCallScope`,
  `AiAssistSaleRequest`, `SalesAssistDtos`, `AiGatewayClient`, `AssistedSearchService`,
  `SalesAssistService`, `AiSearchController`, y dos piezas nuevas —el servicio de la consulta libre y su
  sección de configuración—. **Sin migración de EF Core y sin tabla nueva.**
- **`frontend/`**: `pages/sales/assisted.tsx` en profundidad,
  `components/sales/assisted-search-result-row.tsx`, componentes nuevos de la consulta libre,
  `services/ai-search.service.ts`, `types/ai-search.types.ts` y `lib/assist-copy.ts`.
- **Contratos**: `ai-service/openapi.json` se mueve por **adición pura**, verificada hoja a hoja; un
  consumidor que no envíe `filters` recibe el comportamiento de hoy. `SalesAssistResponse` gana un campo
  aditivo. `SearchLexicalAsync` cambia de firma —interfaz interna, sin consumidores externos—.
- **Seguridad**: la tercera clase de ámbito relaja una invariante fijada con test, y lo hace **añadiendo
  una clase y no relajando las dos existentes**: una claim ausente hace que el prefiltro no se aplique,
  no que case con todo, y falla cerrado en cualquier ruta que la exija.
- **Sin tocar**: `terraform/`, `.github/workflows/`, el carrito y la confirmación de venta, el escaneo y
  el reconocimiento de imágenes.
- **Orden obligado**: **C40 antes de C38**, porque sube el prompt a `assist/v5` y mueve la fase de la
  abstención; unas cifras de C38 tomadas antes describirían un prompt sustituido. **No se solapa** con
  C16 ni C36 (misma página y servicio del frontend) ni con C21, C22 o C25 (pipeline de ranking).
