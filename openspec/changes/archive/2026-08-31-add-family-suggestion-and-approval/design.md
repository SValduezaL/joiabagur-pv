## Context

La tubería de familias está construida entera y vacía. C07 entregó `ProductFamily` / `ProductFamilyMember` con pertenencia excluyente por índice único, orden y etiqueta de variante idempotentes, y cinco endpoints de administración; además **reservó** `Origin`, `ApprovedByUserId` y `ApprovedAt` precisamente para este change, porque C18 no tiene turno de migración. C12 emite `familyId` / `familyName` / `variantLabel` en el feed. C13 los mapea a `ai.product_document`. C02 congeló los campos de familia en el contrato de recuperación. C16 pinta la talla **sólo cuando `variantLabel` existe**.

Y el estado real, verificado el 2026-08-30 contra el Postgres local: **1.200 productos, 1.200 documentos con embedding, 0 familias, 0 documentos con `family_id`**. El `qa.md` de C07 lo dejó anotado: *«La reserva para C18 no está ejercida»*.

Este change no construye tubería. Construye las filas, y decide **cómo** se deciden.

**Restricciones que gobiernan el diseño:**

- **Python es dueño del esquema `ai` y no escribe `public` por SQL** desde el runtime. Los embeddings viven en `ai.product_document`; la verdad del catálogo vive en .NET.
- **La dirección de confianza es asimétrica**: .NET→Python va con JWT interno HS256 (`AiServiceTokenFactory` + `AiGatewayClient`, desde C03); Python→.NET sólo tiene `X-Index-Feed-Key`, de **solo lectura**.
- **`ai-service/openapi.json` está congelado** en ocho rutas, con un test que falla ante cualquier diferencia.
- **El turno de migración de EF Core es único** y lo esperan C19, C27 y C29.
- **Corpus**: 436 reales + 764 sintéticos, con vocabularios de variante muy distintos entre ambos.

## Goals / Non-Goals

**Goals:**

- Que existan ~155 familias con sus ~450 miembros, escritas de forma que el índice las vea.
- Que el algoritmo sea **determinista, reproducible y sin LLM**, y que sus parámetros se puedan barrer sin tocar código.
- Que el corpus se mueva **una sola vez**, antes de cualquier change que mida.
- Que la parte que el algoritmo no resuelve quede **contada y listada**, no escondida.
- Ejercer por primera vez la reserva de aprobación humana de C07.

**Non-Goals:**

- La pantalla de revisión por lotes y el sello de aprobación por ítem — **C18b**.
- La alerta de huérfanos — **C18b**: necesita familias existentes, es una segunda pasada por construcción.
- Persistir propuestas o rechazos.
- Cualquier migración de EF Core o de Alembic.
- Cambiar `source-text/v1`, `embedding_version` o `indexing/embeddings.py`.
- Corregir las entradas de catálogo que no son productos (`Encargos`, `Arreglos`, `Presión`): se listan, no se tocan.

## Decisions

### 1 · .NET conduce y Python calcula

El administrador llama a .NET; .NET llama a `jbg-ai` con su JWT; .NET persiste con su propio servicio.

Lo decide una restricción dura, no el estilo. [`ProductFamilyService.cs:201`](../../../../backend/src/JoiabagurPV.Application/Services/ProductFamilyService.cs#L201) estampa `Product.UpdatedAt` de los productos que entran y salen, con este comentario en el código: *«The feed's catalog cursor is `Product.UpdatedAt` (plus profile and family). Deleting a [membership row] would be skipped on an incremental pull.»* Un `INSERT` directo desde Python no estampa nada, **el feed incremental nunca emite esos productos, y `family_id` sigue nulo para siempre** salvo que alguien ejecute un `sync --full`. Sin un solo error.

> **Matiz medido el 2026-08-31, al escribir el test.** El estampado de `Product.UpdatedAt` es **la mitad** del mecanismo, no todo. El watermark del feed es `greatest(Product.UpdatedAt, perfil.UpdatedAt, familia.UpdatedAt cuando el producto es miembro actual)`, así que **crear** una familia mueve el watermark por el `UpdatedAt` de la propia familia, sin tocar `Product` — y por eso `CreateAsync` nunca estampó. El estampado hace falta en el **reemplazo**: un producto que **sale** deja de unirse a la fila de familia y desaparecería del cursor si nadie lo tocara.
>
> La conclusión de esta decisión no cambia —se escribe por el servicio, siempre— pero el argumento correcto es *«el servicio es el único que mantiene el watermark coherente en las dos direcciones»*, no *«el único que estampa `Product`»*. El primer test que escribí afirmaba el timestamp y falló, con razón: el timestamp era el detalle de implementación y el feed era el requisito.

**Alternativas consideradas.** *(a) CLI de Python que escribe `public` por SQL*, siguiendo el precedente de `world/ingest.py` (C10), que sí escribe `PointOfSales`, `Users` y `Sales`. Se descarta: aquel precedente escribe tablas **sin watermark de indexación**; la familia y su pertenencia sí lo tienen, y además se saltaría el 409 con detalle por producto y la validación de etiqueta duplicada que C07 construyó. *(b) CLI de Python que llama a la API .NET*: conserva las invariantes, pero exige un admin JWT en `Settings` —un secreto con poder total sobre el catálogo para una tarea de lote— y C18b pagaría igualmente el movimiento del contrato.

El patrón existe y está probado: `AiCatalogController.EnrichBatch` (C09) es exactamente «Python propone, .NET persiste», con el manejo de `AiNotImplementedException` → 503 y `AiUnavailableException` ya escrito.

### 2 · Se mueve el contrato congelado, en este change

`POST /v1/families/suggest` es la novena ruta. `openapi.json` se regenera y `test_openapi_snapshot_is_stable` se actualiza aquí mismo.

Lo autoriza la doctrina que `IAiGatewayClient` lleva escrita: *«every other contracted endpoint is added by **the change that first calls it**: adding a method here is a small diff, whereas the wire contract it consumes is frozen and expensive to renegotiate.»* Y C17 fijó el criterio al aplazar la bifurcación de `/health`: romper el test de deriva **es el resultado correcto**, porque la frontera se ha movido de verdad; el test existe para hacerlo visible en lugar de silencioso.

**Alternativa considerada.** *CLI sin ruta HTTP*, dejando el contrato quieto. Se descarta porque C18b necesita la ruta para pintar la pantalla, de modo que el movimiento sólo se aplaza; y porque sin ruta hay que resolver el problema de credencial de (1).

### 3 · Sin persistencia de propuestas: `apply` recibe de vuelta lo aceptado

`suggest` devuelve propuestas; el llamante envía a `apply` el subconjunto que acepta. No hay tabla de propuestas ni estado intermedio.

Evita una tabla en `ai` y, sobre todo, **la séptima migración de EF Core** que el `design.md` de C07 se gastó tres columnas nulables en evitar, y que su tabla de riesgos nombra literalmente (*«C18 descubre que necesita una columna y abre una séptima migración en la Ola 3»*). `suggest` es determinista y **converge**, porque excluye del pool los productos que ya pertenecen a una familia.

**Coste aceptado.** Un rechazo no se recuerda: al repetir `suggest`, una propuesta descartada reaparece. Es tolerable mientras la aprobación sea por lotes; la lista de descartes es de C18b, que es donde existe la pantalla que la necesita.

**Alternativas consideradas.** *(a) Tabla `ai.family_suggestion`*: da rechazos persistentes y Python sería su dueño, pero crea un estado paralelo a .NET que nada invalida y que envejece en silencio. *(b) Entidad .NET*: auditoría completa, al precio de la migración que este change existe para no abrir.

### 4 · La raíz del nombre agrupa; el embedding veta, y en relativo

El §7.5 del diseño dice *«agrupa candidatos por similitud de embedding (**umbral alto**) + mismo `piece_type` + raíz común de nombre»*. **Medido sobre los 1.200 vectores reales, ese enunciado no funciona:**

| | peor hermano *(hay que incluirlo)* | mejor extraño *(hay que excluirlo)* |
|---|---|---|
| real | 0,847 – 0,920 | 0,867 – **0,936** |
| sintético | 0,896 – 0,948 | 0,845 – **0,945** |

Las dos poblaciones se solapan, así que **no existe corte absoluto**. Dos casos:

- `Anillo Bruma grapas {amatista, citrino, granate, peridoto, topacio}` tiene coseno interno 0,895–0,946, y el vecino **no perteneciente** `Anillo Bruma bata plata y oro + piedra` puntúa **0,926** — por encima del peor hermano.
- `Anillo Aurora Boreal S/M/L/XL` frente a `Anillo Aurora Boreal v2 S/M/L/XL`, familias distintas por construcción, llegan a **0,9445** contra un mínimo intra-familia de 0,9497: **cinco milésimas**.

Pero **en relativo el embedding es excelente**: el vecino más próximo es hermano en **96,2 %** (50/52) de los miembros reales y **99,7 %** (305/306) de los sintéticos, y sólo **6 de 358 productos (1,7 %)** tienen un extraño más cerca que su peor hermano.

De ahí la inversión: **la raíz agrupa y el embedding veta**, comparando cada miembro contra el centroide de **su propio grupo** (`mediana − k·MAD`), nunca contra una constante global. Y el veto **marca para revisión, no elimina**: un miembro que comparte raíz y tipo de pieza pero que el vector no respalda es justamente lo que una persona debe mirar.

> **Corrección del 2026-08-31, al implementar.** Ese 1,7 % se midió sobre **familias formadas sólo por sufijo de talla** —373 productos, 24 familias reales— y **no es comparable** con el algoritmo que este change entrega. Se citó aquí como si fuera universal y no lo era.
>
> Dos consecuencias. La primera: la cifra sube porque **el algoritmo mejoró**. Con L2 más fusión hay 68 familias reales en vez de 24, y una familia que agrupa `pequeño` con `pequeño oro` tiene vectores genuinamente más dispersos. Más riqueza, más dispersión interna, más marcas. El 1,7 % era el precio de dejar fuera 44 familias reales.
>
> La segunda: el veto se implementó primero como `mediana − k·MAD` contra el centroide, que es una prueba **dentro** del grupo, mientras que la medición que lo justificaba era **entre** grupos. Son cosas distintas y se confundieron. El MAD marcaba al miembro menos típico de cada clúster —que todo clúster tiene— y disparaba al **16,9 %**.
>
> **La prueba correcta es la que se midió**: se marca al miembro que tiene un producto de **otra familia propuesta** más cerca que su propio peor hermano. Con margen 0,05, la cifra honesta es **15 de 486 miembros (3,1 %) en 5 familias**, y la mayor de las cinco es aquélla donde un producto sintético se coló en una real. Ésa es la cifra que el README debe citar.

Ese residuo irreducible es lo que justifica la revisión humana con un número en lugar de con una afirmación.

**Alternativas consideradas.** *(a) Umbral absoluto del §7.5*: medido y descartado arriba. *(b) Clustering puro por embedding sin raíz*: fracasa en el sintético, donde `v2`/`v3`/`v4`/`v5` son casi-duplicados deliberados. *(c) Embedding sólo del nombre en vez del documento*: separaría mejor, pero exige 1.200 llamadas nuevas al proveedor y una columna más — coste desproporcionado para un veto.

### 5 · L2 más fusión por material, nunca stripping global

Retirar talla **y** material de todos los nombres a la vez convierte `Anillo plata S/M/L/XL` en la raíz `anillo`, que absorbería cualquier otro «Anillo ‹material›». Retirar sólo la talla la deja en `anillo plata`, correcta.

Por eso el material **no se elimina de la raíz**: se usa para **fusionar** grupos ya formados que difieren en exactamente un token de material. Misma cobertura (~68 familias reales frente a 24 con sólo talla), sin degenerar.

La guarda que lo hace posible —no fusionar si la raíz resultante queda en el tipo de pieza pelado o baja de dos tokens— resulta además tener valor de negocio: de las seis raíces que bloquea, **tres no son productos**. `Encargos plata/Oro` y `Arreglos plata/oro` son servicios del taller, y `Presión Oro/plata` es un componente. Se listan como incidencia de catálogo.

### 6 · `variant_label` verbatim y `Position` por rango canónico; los ejes no se separan

Descomponiendo las familias por **qué eje las separa**:

| | REAL (~68) | SINTÉTICO (87) |
|---|---|---|
| solo eje talla | 33 (49 %) | 87 (100 %) |
| solo eje material | 28 (41 %) | 0 |
| **rejilla talla × material** | **3 (4 %)** | 0 |
| sin eje detectado *(pieza base sin token)* | 4 (6 %) | 0 |

**El 90 % tiene un solo eje**, y por tanto etiqueta limpia. Sólo tres familias necesitan etiqueta compuesta (`mini oro`), que sigue cumpliendo el índice `UNIQUE(family_id, variant_label)` de C07 y que su spec admite explícitamente: *«the size, colour **or finish** that tells one variant from another»*, texto libre y opcional.

Las 4 «sin eje» no son un defecto sino un artefacto del detector: `Anillo mini conchiglie` / `Anillo conchiglie` sí varían en talla — **la ausencia de token es un valor de variante**, la pieza base, y C07 ya contempla `variant_label` nulo como estado legítimo.

Sobre las **dos escalas de talla** (`XS/S/M/L/XL` y `mini/pequeño/mediano/grande`) se separan dos necesidades que se confundían: **la etiqueta se guarda literal** —`mini` no es `XS`; es la palabra del taller y la que el dependiente dice al cliente— y **el orden se calcula con un rango canónico interno** (`mini < XS < pequeño < S < M < mediano < L < grande < XL`) que alimenta el `Position` que C07 ya persiste e indexa. Sólo 2 familias mezclan escalas, y van a la cola de revisión en lugar de a una regla.

**Alternativa considerada.** *Separar `variant_label` en `SizeLabel` + `MaterialLabel`*: representación limpia, al precio de una migración de EF Core **más** un cambio en la plantilla `source-text/v1` que elevaría `preprocessing_id` a `v2` y forzaría reindexar **los 1.200** en vez de 358. Ganancia: **3 familias de 155**. Relación coste/beneficio mala; descartada.

### 7 · Todas las familias en un lote, con `Origin = AiApproved`

`apply` escribe con `Origin = AiApproved`, `ApprovedByUserId` = el administrador que invoca, `ApprovedAt` = el instante. Es honesto a nivel de lote: un administrador dispara conscientemente la aprobación; **C18b lo refina a nivel de ítem**. Una familia creada por los endpoints de C07 sigue registrando `Manual`.

Se escriben **todas** de una vez porque el corpus debe moverse una sola vez. Escribir un subconjunto ahora y el resto en C18b lo movería dos veces, y la segunda caería después de la línea base de C24 — que es el riesgo que el §2 de este documento existe para evitar.

### 8 · Reconciliación incremental, nunca `--full`

`POST /v1/index/sync` sin `full`. Un `--full` reindexaría todo y **taparía** un fallo de estampado en lugar de exponerlo. El incremental es la única prueba real de que la decisión 1 se implementó bien, y por eso el criterio de aceptación exige contar que los emitidos sean exactamente los estampados.

### 9 · Lo que la puerta excluye se nombra, y lo que no es joyería sale del índice en este mismo lote

*(Decisión añadida el 2026-08-31, a partir de un hallazgo de la implementación.)*

La guarda de raíz degenerada encontró que **el catálogo contiene cosas que no son joyas terminadas**, y que están indexadas y por tanto en la búsqueda asistida: servicios de taller (`Arreglos`, `Cambiar hilo`, `Comprobar pureza del oro`), experiencias (`Joyero por un día`), velas y regalo, envío, merchandising, y cierres de pendiente. En seis de ellas **C09 forzó un tipo de pieza** —`Arreglos oro`→`collar`, `Encargos`→`collar`, `Presión`→`anillo`— porque su vocabulario cerrado no admite «no es una pieza» y el extractor tuvo que elegir algo.

**La palanca correcta ya existía y nadie la había usado:** `ProfileReviewStatus`. El predicado de indexabilidad es `Product.IsActive AND profile.ReviewStatus == Approved`, y C08 separó estado de origen precisamente *«so the indexing feed selects by status alone»*. Poner `Rejected` las saca del índice y **las deja vendibles**. Las 1.200 estaban en `Approved`.

**`IsActive = false` sería un error**, y conviene dejarlo escrito para que nadie lo intente: también las sacaría del TPV, y `Encargos` es una línea de caja real de 10 €. Se arreglaría la búsqueda rompiendo la venta.

**Va en este lote, no después**, porque el principio de la decisión 7 —el corpus se mueve una sola vez— **aplica igual a las bajas que a las altas**: 32 documentos que desaparecen son un movimiento del corpus, y hacerlo tras la línea base de C24 invalidaría la tabla de ablations exactamente igual que hacerlo con las altas. Una sola sincronización incremental reconcilia ambas cosas.

**Y la puerta deja de ser muda.** Un `piece_type` nulo excluye al producto de las familias *y de la cola de revisión*, de modo que nada volvería a mencionarlo: `Arreglos plata` desapareció así. La respuesta de `suggest` gana una tercera lista con los productos excluidos y su motivo. Los que ya pertenecen a una familia se cuentan en vez de enumerarse: tras el primer lote son cientos y su exclusión es la regla de convergencia funcionando, no un hallazgo.

**Lo que esta decisión NO resuelve**, y queda anotado como change propio: **9 joyas sintéticas legítimas** de 160 a 1.300 € —5 diademas, 2 gemelos, un cinturón— tienen `piece_type` nulo porque `piece_type.terms` sólo nombra ocho tipos y no incluye los suyos. Ahí el nulo **no** significa «no es una pieza» sino «mi vocabulario no la sabe nombrar», y el arreglo es el contrario: ampliar el vocabulario y reenriquecer. Eso mueve el corpus una tercera vez, así que necesita su propia decisión de cuándo, y no se toma aquí.

### 10 · El parámetro del veto vive en configuración

**Un solo ajuste**, `JPV_FAMILY_VETO_MARGIN`, leído de `pydantic-settings` y calibrado en **0,05**. Es la distancia por la que el mejor extraño tiene que ganarle al peor hermano para que el miembro se marque: por debajo, un empate es ruido. Medido sobre el corpus, 0,05 → 15 miembros de 486 en 5 familias; 0,02 → 33 en 18; 0,08 → 9 en 2. C24 lo revisará con el golden set, y un umbral incrustado en el código no se puede barrer.

> **Revisada el 2026-08-31, al implementar.** Esta decisión decía «`k = 2` sobre los 5 vecinos más próximos», que eran los parámetros de la prueba `mediana − k·MAD` **dentro** del grupo. Esa prueba se sustituyó por la comparación **entre** grupos de la decisión 4 —el motivo está allí— y con ella desaparecieron tanto la `k` como el número de vecinos: la prueba comparativa no elige vecinos, los mira todos. Queda un parámetro donde se anunciaban dos, y es el margen.

## Risks / Trade-offs

- **Escribir por SQL directo rompería el índice en silencio** → Decisión 1: se escribe siempre por `ProductFamilyService`, y el escenario de aceptación lo verifica con sincronización **incremental**, que es la que falla si el estampado falta.
- **El corpus se mueve y `embedding_version` no lo distingue** → Se mueve **una sola vez** (decisión 7) y este change precede a C20, C21 y C24. Queda anotado en el informe del lote y en la reestructuración del plan.
- **Sobre-agrupamiento por la fusión de material** → Guarda de raíz degenerada, puerta de `piece_type` y veto relativo. Las excepciones van a la cola de revisión, no a una regla; ninguna se resuelve con una excepción codificada por nombre.
- **El veto puede quedar mal calibrado** (el margen 0,05 sale de una muestra corta) → Decisión 10: vive en configuración y se barre con C24 sin tocar código.
- **La cola de revisión no tiene pantalla hasta C18b** → Aceptado. En C18a la aprobación es por lotes y las ~11 excepciones se listan en el informe versionado.
- **`piece_type` sin medir** (el contenedor de Postgres se detuvo durante la exploración) → El nulo se trata como valor propio de la puerta: no agrupa con nadie, que es el lado seguro. La medición del apply confirma y dimensiona, no decide.
- **Mover el contrato congelado** rompe `test_openapi_snapshot_is_stable` → Deliberado y regenerado en el mismo change. Trabajando en solitario, el acuerdo con «quien posee el cliente .NET» que pide `CLAUDE.md` es una nota, no un bloqueo.
- **Un rechazo no se recuerda** → Coste aceptado de la decisión 3; la lista de descartes es de C18b.

## Migration Plan

**No hay migración de esquema** — ni EF Core ni Alembic. Sí hay **migración de datos**, en cuatro pasos y con vuelta atrás en cada uno:

1. **Medir la línea base**: recuento de familias (0), de documentos con `family_id` (0) y tasa de nulos de `piece_type`. Se anota en el informe.
2. **Proponer** con `POST /api/ai/catalog/family-suggestions`. No escribe nada: repetible sin consecuencias.
3. **Aplicar** con `/apply`. Reversible: borrar las familias creadas cascadea sus miembros por la regla de C07, y los productos vuelven a no pertenecer a ninguna. El `Origin = AiApproved` identifica exactamente qué borrar frente a lo creado a mano.
4. **Reconciliar** con `POST /v1/index/sync` incremental y verificar que `family_id` deja de ser nulo en los productos estampados y sólo en ésos.

**Vuelta atrás completa:** borrar las familias con `Origin = AiApproved` y volver a sincronizar. Los documentos pierden `Familia:` y `Variante:`, su hash vuelve al anterior y se reembeben. El corpus queda como estaba.

## Open Questions

**Ninguna bloqueante.** Las seis que el ticket abrió el 2026-08-31 se cerraron el mismo día aplicando su opción por defecto, y quedan registradas con su motivo en [`ticket.md`](./ticket.md) § *Decisiones cerradas* y en la HU como D9–D14: `piece_type` nulo como valor propio de la puerta, los parámetros del veto en configuración —que al implementar quedaron en **uno**, el margen; ver la revisión de la decisión 10—, `Alianzas Plata/oro` a la cola de revisión, vocabularios **reutilizados** de `enrichment/vocabularies.yaml`, doble etiquetado del golden set de C24 remitido a la reestructuración del plan, e informe del lote versionado.

> **D12, revisada el 2026-08-31 al implementar.** La decisión original decía «declarar el vocabulario de materiales en Python y aceptar la duplicación como deuda». Es al revés: [`enrichment/vocabularies.yaml`](../../../../ai-service/src/jbg_ai/enrichment/vocabularies.yaml) (C09) ya declara materiales, tipo de pieza y `size_label` **con las dos escalas** y sus sinónimos, y `enrichment.vocab.fold` ya hace la normalización que la decisión 5 describe. El fichero del frontend es el espejo de ése, no su origen. Declarar una lista dentro de `families/` habría creado la duplicación que D12 quería evitar, un borde más adentro. **Lo único nuevo es el rango canónico de tallas** —el vocabulario agrupa por escala, no ordena por magnitud, y el orden es lo que `Position` necesita— y la regla de que `variant_label` guarda la subcadena del nombre y no la forma canónica que `resolve()` devolvería.

Dos cuestiones siguen vivas, ambas fuera del alcance de este change y anotadas para que no se pierdan:

- **El doble etiquetado del golden set de C24**, que su ficha da por hecho entre dos personas y el §6 del plan declara irrenunciable, no existe trabajando en solitario. Debe resolverse **antes** de abrir C24.
- **La divergencia entre la spec viva `product-family` y el código**: aquélla justifica la distinción con las colecciones diciendo que un producto puede pertenecer *«to one of many unrelated collections»*, pero [`Product.cs:31`](../../../../backend/src/JoiabagurPV.Domain/Entities/Product.cs#L31) declara `Guid? CollectionId`, una FK única y anulable. Ambas cardinalidades son 0..1. Los discriminadores reales, medidos: una colección abarca 1–154 productos (mediana 15) y **13–16 tipos de pieza**; una familia, 2–4 productos de **un solo tipo**.
