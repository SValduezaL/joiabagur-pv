# T-AIENG-018a: Assisted product family suggestion and batch approval (C18a)

> Ticket técnico del change OpenSpec `add-family-suggestion-and-approval`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-018a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-018a.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C18), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§2.2, §7.5, §7.8, §8.3, §11.1), sesión de exploración 2026-08-30/31 con medición sobre los 1.200 vectores reales, y código real de `ai-service/src/`, `backend/src/` y `openspec/specs/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-018a / C18a** — Motor determinista de agrupación de familias (raíz L2 + fusión por material, veto relativo por embedding), ruta `POST /v1/families/suggest` en `jbg-ai`, endpoints de administración en .NET que proponen sin escribir y aplican el subconjunto aceptado, escritura vía `ProductFamilyService` con `Origin = AiApproved`, y reconciliación del índice por sincronización incremental

---

## Contexto y Problema

C07 entregó la entidad `ProductFamily`, C12 la emisión de `familyId` en el feed y C13 el mapeo al índice. **La tubería está completa y vacía**: 1.200 productos, 1.200 documentos con embedding, **0 familias y 0 documentos con `family_id`**. C06b lo dejó escrito a propósito (*«el catálogo híbrido nace sin filas de miembro»*) y el `qa.md` de C07 lo anotó igual (*«La reserva para C18 no está ejercida»*).

Al diseñar sobre el código y los datos reales aparecen cinco hechos que la ficha del plan no podía conocer.

**Primero: escribir desde Python por SQL rompería el índice en silencio.** [`ProductFamilyService.cs:201`](../../../../backend/src/JoiabagurPV.Application/Services/ProductFamilyService.cs#L201) estampa `Product.UpdatedAt` de los productos que entran y salen de una familia, con este comentario en el propio código: *«The feed's catalog cursor is `Product.UpdatedAt` (plus profile and family). Deleting a [membership row] would be skipped on an incremental pull.»* Un `INSERT` directo —el precedente de `world/ingest.py`— no estampa nada, el feed incremental nunca emite esos productos, y `family_id` sigue nulo para siempre salvo que alguien ejecute un `sync --full`. Sin un solo error. Además, la única credencial Python→.NET es `X-Index-Feed-Key`, de solo lectura.

**Segundo: el umbral absoluto del §7.5 no existe en estos datos.** Medido sobre los 1.200 vectores: la población de «peor hermano» (real 0,847–0,920) y la de «mejor extraño» (real 0,867–**0,936**) se solapan. `Anillo Bruma bata`, que no es de la familia, puntúa **0,926** contra `Anillo Bruma grapas`, por encima del peor hermano de esa familia. Y `Aurora Boreal` frente a `Aurora Boreal v2` —familias distintas por construcción— llegan a **0,9445** contra un mínimo intra-familia de 0,9497: **cinco milésimas**. En cambio, en relativo el vecino más próximo es hermano en **96,2 %** (real) y **99,7 %** (sintético), y sólo **6 de 358 productos (1,7 %)** tienen un extraño más cerca que su peor hermano.

**Tercero: el stripping global de material degenera raíces legítimas.** Quitar talla y material a la vez convierte `Anillo plata S/M/L/XL` en la raíz `anillo`, que absorbería cualquier otro «Anillo ‹material›». Quitar sólo la talla la deja en `anillo plata`, correcta. Por eso el material **fusiona** grupos ya formados en lugar de eliminarse de la raíz. La misma guarda revela que hay **servicios en el catálogo**: `Encargos plata/Oro`, `Arreglos plata/oro` y `Presión Oro/plata` no son piezas.

**Cuarto: C18a mueve el 30 % del corpus y `embedding_version` no lo distinguirá.** `build_source_text` emite `Familia:` y `Variante:`, hoy ausentes en 1.200/1.200. Llenarlas en ~358 cambia `doc_text`, `source_hash` y el vector. Pero `embedding_version` es `modelo:dims:preprocessing_id` = `openai/text-embedding-3-small:1536:source-text/v1`, y C18a cambia **contenido**, no preprocesado: el corpus anterior y el posterior llevarán la misma cadena. Es la deriva silenciosa de S11 trasladada a la evaluación, y obliga a que C18a vaya **antes de C20, C21 y C24** y a que escriba **todas** las familias de una vez.

**Quinto: cuatro changes tienen su test de familia vacuo mientras no existan filas** — C25, C26, y los irrecortables **C30** (`test_variants_grouped_by_family_id`) y **C36** (`should require variant confirmation when family has multiple members`). El plan declara irrecortables a los consumidores y recortable al productor.

### Estado actual del código (verificado 2026-08-30/31 en repo)

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-family-suggestion-and-approval` | **Scaffold** (`.openspec.yaml`, schema `spec-driven`, 0/4 artefactos); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| Rama de trabajo | `c18a-add-family-suggestion-and-approval`, creada desde `ai-eng` en `f5212a7` |
| `ProductFamily` / `ProductFamilyMember` | ✅ C07. Índice único de pertenencia excluyente, `Position` y `VariantLabel` únicos por familia, `Origin` (`Manual`/`AiApproved`), `ApprovedByUserId`, `ApprovedAt` — los tres **reservados y sin ejercer** |
| `ProductFamilyService` | ✅ 389 líneas. `ReplaceMembers` idempotente con cortocircuito de lista idéntica, `StampUpdatedAtAsync` por `ExecuteUpdate`, 409 con detalle por producto leyendo `DbException.SqlState == "23505"` |
| `ProductFamiliesController` | ✅ `api/product-families`: `GET {id}`, `POST`, `PUT {id}`, `PUT {id}/members`. Escritura sólo administradores |
| **Datos de familia** | ❌ **`ProductFamilies` = 0 · `ProductFamilyMembers` = 0 · `ai.product_document.family_id IS NOT NULL` = 0** |
| `ai.product_document` | ✅ 1.200 filas, 1.200 con embedding. Columnas `family_id`, `family_name`, `variant_label`, `embedding_model`, `embedding_version`, `piece_type`, `data_origin` (436 `real` / 764 `synthetic`) |
| `build_source_text` | ✅ [`source_text.py:78`](../../../../ai-service/src/jbg_ai/indexing/source_text.py#L78). Emite `Familia:` y `Variante:` cuando existen — **ausentes en 1.200/1.200** |
| `ai-service/openapi.json` | **8 rutas congeladas**; `/v1/families/*` **no está**. `test_openapi_snapshot_is_stable` falla ante cualquier diferencia |
| `ai-service/src/jbg_ai/` | Paquetes `api/`, `config/`, `data/`, `db/`, `enrichment/`, `indexing/`, `retrieval/`, `stubs/`. **No existe `families/`** |
| `ai-service/tests/` | `api/`, `config/`, `data/`, `db/`, `enrichment/`, `indexing/`, `migrations/`, `retrieval/`, `support/`. **No existe `families/`** |
| `IAiGatewayClient` | ✅ **3 operaciones**: `SearchAsync` (C15), `EnrichAsync` (C09), `HealthAsync` (C17). Doctrina escrita: *«every other contracted endpoint is added by the change that first calls it»* |
| `AiCatalogController` | ✅ `api/ai/catalog`, `[Authorize(Roles = "Administrator")]`, `POST enrich-batch`. **Plantilla exacta** del patrón «Python propone, .NET persiste» |
| Tests .NET de familia | `IntegrationTests/ProductFamiliesControllerTests.cs` y `ProductFamilySchemaTests.cs`. **Sin tests unitarios de servicio** |
| Frontend | ❌ **No existe** `product-family.service.ts` ni página de familias. C16 ya pinta la talla **sólo cuando `variantLabel` existe** — hueco reservado desde el 2026-08-29 |
| Turno de migración EF Core | **Libre.** C18a **no lo ocupa**; queda para C19 |

---

## Componentes Afectados

- **`ai-service/`** — nuevo paquete `src/jbg_ai/families/` (librería determinista + puerto de lectura del índice), nuevo router `api/routers/families.py`, nuevos esquemas `api/schemas/families.py`, entrada en `stubs/`, snapshot `openapi.json`, tests en `tests/families/`.
- **`backend/`** — `JoiabagurPV.Application`: `IAiGatewayClient.SuggestFamiliesAsync`, DTOs en `DTOs/Ai/`, validadores; `JoiabagurPV.Infrastructure`: implementación en `AiGatewayClient`; `JoiabagurPV.API`: dos acciones nuevas en `AiCatalogController`; `JoiabagurPV.Tests`: unitarios e integración.
- **`openspec/`** — change `add-family-suggestion-and-approval` con specs delta sobre `product-family`, `ai-service-api-contracts` y `ai-gateway-client`.
- **`Documentos/`** — HU-AIENG-018a, `epicas.md` (EP13), plan de changes (§0, §2, §4, §5, §6), informe del lote bajo `Proyecto Final AIEng/informes/`.
- **No se toca:** `frontend/`, `terraform/`, `.github/workflows/`, ninguna migración de EF Core ni de Alembic, `source-text/v1`, `indexing/embeddings.py`.

---

## Especificaciones Técnicas

### Algoritmo de agrupación (`jbg_ai.families`)

Determinista, sin LLM y sin llamadas de red. Cuatro etapas y tres guardas:

| Etapa | Qué hace |
|---|---|
| **1. Normalización de raíz** | *casefold*, `NFD` sin diacríticos, puntuación y paréntesis a espacio, espacios colapsados |
| **2. Agrupación L2** | agrupa por raíz tras retirar el **token de talla, esté donde esté en el nombre**: latino (`XS`, `S`, `M`, `L`, `XL`, insensible a caja — el catálogo real contiene `Xs`) y en palabra (`mini`, `pequeño/a`, `mediano/a`, `grande`). Un término de varias palabras (`extra mini`) se empareja entero |
| **3. Fusión por material** | fusiona dos grupos cuyas raíces difieran en **exactamente un material** (`plata`, `oro`, `latón`, `bronce`, `acero`), contando `baño de oro` como uno solo |
| **4. Veto relativo** | se marca —nunca se elimina— al miembro que tiene un producto de **otra familia propuesta** más cerca que su propio **peor hermano**, por más de un **margen** leído de `pydantic-settings` y no incrustado en el código |

> **Revisada el 2026-08-31, al implementar.** La etapa 4 salió del ticket como `mediana − k·MAD` contra el centroide del propio grupo, con `k = 2` sobre los 5 vecinos más próximos. Esa es una prueba **dentro** del grupo, mientras que la medición que la justificaba era **entre** grupos: marcaba al miembro menos típico de cada clúster —que todo clúster tiene por definición— y disparaba al 16,9 %. La sustituye la prueba comparativa de arriba, que es la que se midió, y con ella desaparecen la `k` y el número de vecinos: queda **un** parámetro, el margen, calibrado en 0,05 → 15 miembros de 486 en 5 familias. El detalle está en la decisión 4 del [`design.md`](./design.md).

**Guardas** (las tres bloquean la propuesta, no la corrigen):

1. **Raíz degenerada** — no se propone familia si la raíz resultante coincide con el tipo de pieza pelado o baja de dos tokens. Es la que evita que `Anillo plata S/M/L/XL` colapse a `anillo`, y la que revela `Encargos`, `Arreglos` y `Presión`.
2. **Puerta de `piece_type`** — nunca se agrupa a través de tipos de pieza, y **un `piece_type` nulo no agrupa con ninguno**: el nulo es valor propio de la puerta, no comodín. La tasa de nulos se mide al abrir el apply para confirmar el parámetro y dimensionar su efecto, no para decidirlo.
3. **Exclusión de ya asignados** — los productos que ya pertenecen a una familia no entran en el pool, de modo que repetir `suggest` converge.

**Vocabularios: se reutilizan, no se declaran** *(D12 revisada el 2026-08-31 al implementar)*. [`enrichment/vocabularies.yaml`](../../../../ai-service/src/jbg_ai/enrichment/vocabularies.yaml) (C09) ya declara `materials.terms`, `piece_type.terms` y `size_label.terms` **con las dos escalas** —`XXS…XXL` y `mini/pequeno/mediano/grande`— y sus sinónimos (`pequeña`, `pequeñas`, `mediana`, `grandes`). `enrichment.vocab.fold` ya hace la normalización que este paquete necesita. `frontend/src/lib/materials-vocabulary.ts` es el **espejo** de ese fichero, no su origen, como declara su propia cabecera.

Lo único nuevo es el **rango canónico de tallas**, que el vocabulario no puede aportar: su lista está agrupada por escala y no ordenada por magnitud, y el orden es lo que `ProductFamilyMember.Position` necesita. Un token de talla que el rango no nombre ordena al final y **no lanza**: una talla desconocida es un ítem de revisión, nunca una caída.

**`variant_label` guarda la subcadena tal como aparece en el nombre**, no la forma canónica. `ClosedVocab.resolve()` mapea `pequeña` → `pequeno`, lo que contradiría el escenario que exige persistir `pequeña`: se **detecta** con el vocabulario, que reconoce el sinónimo, y se **guarda** lo que el catálogo escribió.

**`variant_label`** = el fragmento retirado, **verbatim normalizado**. `mini` no se traduce a `XS`. En las 3 rejillas de dos ejes la etiqueta es compuesta (`mini oro`) y sigue siendo única dentro de su familia, que es lo que el índice de C07 exige.

**`position`** = orden por **rango canónico interno** de tallas (`mini < XS < pequeño < S < M < mediano < L < grande < XL`), nunca persistido como etiqueta. Alimenta el `Position` que C07 ya indexa.

### `POST /v1/families/suggest` (`jbg-ai`) — **novena ruta del contrato**

- Lee `ai.product_document` (esquema propio de Python). **No** consulta `public` por SQL.
- Cuerpo de petición con acotación opcional (`piece_type`, límite) y `STUB_MODE` con respuesta determinista.
- Respuesta: lista de propuestas, cada una con raíz, `piece_type`, miembros (`product_id`, `sku`, `name`, `variant_label`, `position`), el eje detectado, y las marcas de revisión con su distancia.
- Autenticación por el JWT interno HS256 ya establecido en C02; el token manda sobre el cuerpo.
- **Impacto en el snapshot:** `ai-service/openapi.json` se regenera y `test_openapi_snapshot_is_stable` se actualiza en el mismo change. Es un movimiento deliberado de la frontera.

### Endpoints .NET (`AiCatalogController`, `api/ai/catalog`)

| Ruta | Método | Rol | Comportamiento |
|---|---|---|---|
| `family-suggestions` | `POST` | Administrator | Llama a `SuggestFamiliesAsync` y devuelve las propuestas. **No escribe nada**: ni familia, ni miembro, ni `Product.UpdatedAt` |
| `family-suggestions/apply` | `POST` | Administrator | Recibe el subconjunto aceptado y lo persiste vía `ProductFamilyService`. Devuelve recuentos y los conflictos por producto |

- Validación explícita con FluentValidation (este proyecto registra validadores sin *pipeline* automático).
- `AiNotImplementedException` → **503** con mensaje que nombra la causa; `AiUnavailableException` → **503**. Patrón ya escrito en `enrich-batch`.
- Paginación: no aplica — la respuesta es el lote completo de propuestas, acotado por el tamaño del catálogo. El cap de 50 ítems de `PaginationConstants` **no** se usa aquí, igual que en el feed de indexación.

### Persistencia

- `Origin = AiApproved`, `ApprovedByUserId` = administrador que invoca `apply`, `ApprovedAt` = instante de la aprobación. **Primera escritura de las tres columnas que C07 reservó.**
- Creación vía `ProductFamilyService.CreateAsync` + `ReplaceMembersAsync`, **nunca por SQL**. El estampado de `Product.UpdatedAt` y el 409 con detalle por producto se heredan intactos.
- **Sin tabla de propuestas**, sin migración de EF Core y sin migración de Alembic.

### Reconciliación del índice

`POST /v1/index/sync` **sin** `full`. El feed debe emitir exactamente los productos estampados. Un `--full` taparía un fallo de estampado en lugar de exponerlo, y por eso está prohibido en el criterio de aceptación.

---

## Arquitectura

**Dirección de confianza, que decide el diseño:**

```
  .NET ──── JWT interno HS256 (AiServiceTokenFactory + AiGatewayClient) ───▶ Python
  Python ── X-Index-Feed-Key (feed de solo lectura) ──────────────────────▶ .NET
```

No existe credencial de escritura Python→.NET, y crearla significaría un admin JWT con poder total sobre el catálogo para una tarea de lote. Por eso **.NET conduce y Python calcula**, replicando el flujo que C09 ya estableció con `enrich-batch`.

**Decisiones previas aplicables:**

- [`2026-08-17-add-product-family-entity/design.md`](../../archive/2026-08-17-add-product-family-entity/design.md) §6 (la posición se reescribe por completo, no se inserta), §7 (reserva de `Origin`/`ApprovedByUserId`/`ApprovedAt` *«para que C18 no abra una séptima migración»*), y el aviso explícito *«Aviso para C18, C19 y C29: con claves asignadas en cliente, "añadir a la colección" no significa "insertar"»*.
- [`2026-08-16-add-product-ai-profile-entity/design.md`](../../archive/2026-08-16-add-product-ai-profile-entity/design.md): *«La pertenencia a familia queda fuera de los campos sensibles […] su propuesta es de C18. Sostener aquí una segunda autoridad sobre lo mismo crearía dos verdades.»*
- Patrones en uso: Repository, Service Layer, Dependency Injection. Sin patrones nuevos.

**Breaking changes:**

- **`ai-service/openapi.json`**: sí, deliberado. Novena ruta. Se regenera con la orden del README y se acuerda en el mismo change; al trabajar en solitario, el acuerdo que pide `CLAUDE.md` es una nota, no un bloqueo.
- **Contratos REST del backend**: ninguno. Dos rutas nuevas bajo un controlador existente; nada cambia de forma.
- **Modelo de datos**: ninguno. Sin columnas nuevas, sin migración.
- **Corpus**: ~358 documentos cambian `doc_text`, `source_hash` y embedding. `embedding_version` **no** cambia, y ése es precisamente el riesgo que obliga al orden.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec completos (`proposal`, **`design.md`**, specs delta, `tasks`) y `openspec validate --all --strict` en `0 failed`
- [ ] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] **`ai-service`**: `uv run pytest` en verde, sin llamadas reales a LLM, embeddings ni RDS; fixtures en `tests/families/`; tests de **propiedades** sobre el agrupador (invariantes, no valores concretos), nomenclatura `test_<unidad>_<escenario>_<esperado>`
- [ ] **Test de fijación que guarda la reutilización** de `enrichment/vocabularies.yaml` (D12 revisada): falla si alguien vuelve a declarar una lista de materiales o de tallas dentro de `families/`
- [ ] **`k` y el número de vecinos del veto leídos de configuración** (D10), verificado por un test que falla si alguno está incrustado en el código
- [ ] **`openapi.json` regenerado** y `test_openapi_snapshot_is_stable` en verde contra el árbol de trabajo
- [ ] **Backend**: xUnit + Moq + FluentAssertions + Bogus, integración con Testcontainers, nomenclatura `Método_Escenario_ResultadoEsperado`, cobertura ≥70 % sobre lo nuevo
- [ ] **Baseline de la suite medido antes de tocar nada** (`git stash push -u` → suite → `git stash pop`) y comparación por **nombres de test**, no por recuento — la suite de backend arrastra ~53 fallos preexistentes y la de frontend ~118
- [ ] **Sin migración de EF Core** y sin migración de Alembic — verificado explícitamente
- [ ] El lote ejecutado sobre el corpus, con recuento, cola de revisión y **tasa de nulos de `piece_type`** en [`informes/c18a-family-suggestion-report.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/) (D14)
- [ ] **Sincronización incremental verificada**: `family_id` deja de ser nulo sin recurrir a `--full`
- [ ] Plan de changes reestructurado a **C18a → C19 → C18b** (§0, §2, §4, §5, §6), divergencia de `Product.CollectionId` anotada, y **decisión sobre el doble etiquetado del golden set de C24 planteada** para resolver antes de abrir C24 (D13)
- [ ] HU enlazada en `Documentos/epicas.md` (EP13)
- [ ] Documentación actualizada según la tabla *Post-Implementation Documentation Update* de `openspec/project.md`
- [ ] Sin `TODO`/`FIXME` sin tarea de seguimiento asociada
- [ ] No aplica interfaz de usuario: C18a no toca `frontend/`

---

## Requisitos No Funcionales

- **Seguridad**: ambos endpoints .NET restringidos a `Administrator` por `[Authorize(Roles = "Administrator")]`, heredado del controlador. El JWT interno hacia `jbg-ai` sigue el patrón HS256 de C02 con `trace_id` propagado. **No se introduce ninguna credencial nueva**: es una de las razones de D1. Ningún secreto al repositorio.
- **Rendimiento**: el agrupamiento opera sobre 1.200 documentos; el veto por embedding se resuelve con el índice coseno ya existente y sin llamadas al proveedor —los vectores están persistidos—. `suggest` **no debe** invocar el cliente de embeddings. El pool de conexiones sigue acotado a 5.
- **Observabilidad**: logging estructurado con Serilog en .NET y `trace_id` propagado a `jbg-ai`; el lote registra recuentos de familias, miembros, marcados y conflictos.
- **Integridad de datos**: la pertenencia excluyente la garantiza el índice único de C07, no una comprobación de aplicación; el 409 con detalle por producto se propaga sin envolver; `apply` no deja familias a medias.
- **Idempotencia**: repetir `suggest` sobre un catálogo sin cambios devuelve el mismo resultado; repetir `apply` con la misma lista no reescribe filas, por el cortocircuito de lista idéntica de C07.

---

## Preguntas Abiertas

**Ninguna bloqueante.** Las seis que este ticket abrió el 2026-08-31 se cerraron el mismo día aplicando su opción por defecto, y quedan registradas abajo con su motivo. Se conservan en lugar de borrarse porque la alternativa descartada es parte del razonamiento, igual que en los `design.md` de C07 y C08.

### Decisiones cerradas el 2026-08-31

| # | Pregunta original | Decisión aplicada | Motivo |
|---|---|---|---|
| 1 | Tasa de nulos de `piece_type` en `ai.product_document`, no medida en la exploración porque el contenedor de Postgres se detuvo | **El nulo es valor propio de la puerta**: un producto sin tipo de pieza no agrupa con ninguno. Se mide al abrir el apply para **confirmar** y dimensionar, no para decidir | Es el lado seguro: un nulo tratado como comodín agruparía a través de tipos de pieza, que es justo lo que la puerta existe para impedir. Fijarlo ahora desbloquea el apply sin esperar a la medición |
| 2 | `k` del veto relativo (`mediana − k·MAD`) y número de vecinos | **Margen de 0,05 entre grupos**, en `pydantic-settings` — *decisión revisada el 2026-08-31 al implementar* | La forma original era una prueba **dentro** del grupo, y la medición que la justificaba era **entre** grupos: el MAD marcaba al miembro menos típico de cada clúster —algo que todo clúster tiene— y disparaba al 16,9 %. La prueba correcta marca al miembro que tiene un producto de otra familia propuesta más cerca que su propio peor hermano. Curva medida sobre 486 miembros: 0,02→33 en 18 familias · **0,05→15 en 5** · 0,08→9 en 2. Sigue en configuración porque C24 lo barrerá |
| 3 | `Alianzas Plata` / `Alianzas oro`: ¿familia legítima o raíz degenerada? | **A la cola de revisión.** La guarda la bloquea por longitud de raíz; la persona decide en C18b | Si es familia, lo dice un humano; si no lo es, la guarda ya acertó. En ningún caso debe resolverlo el algoritmo, y menos con una excepción codificada por nombre |
| 4 | ¿Reutilizar `materials-vocabulary.ts` de C16 o declarar vocabulario propio en Python? | **Ninguna de las dos.** Se reutiliza [`enrichment/vocabularies.yaml`](../../../../ai-service/src/jbg_ai/enrichment/vocabularies.yaml) — *decisión revisada el 2026-08-31 al implementar* | La pregunta partía de una premisa falsa: daba por hecho que en Python no había vocabulario. **Python es el original** (`materials.terms`, `piece_type.terms` y `size_label.terms` con las dos escalas y sus sinónimos) y el fichero del frontend es su espejo declarado. Declarar una lista dentro de `families/` habría creado exactamente la duplicación que la decisión quería evitar. El test de fijación se conserva y ahora guarda la reutilización |
| 4b | *(nueva, derivada de la anterior)* ¿`variant_label` guarda la forma canónica o la del catálogo? | **La subcadena tal como aparece en el nombre** (`pequeña`, no `pequeno`) | `ClosedVocab.resolve()` canonicaliza, lo que contradiría el escenario de la spec que exige persistir `pequeña`. Se detecta con el vocabulario —que reconoce el sinónimo— y se guarda lo que la tienda escribió, que es lo que el operador lee en la etiqueta |
| 5 | Doble etiquetado del golden set de C24 trabajando en solitario, que la ficha da por hecho entre dos y el §6 declara irrenunciable | **Fuera del alcance de C18a**; se deja planteado en la reestructuración del plan para resolver **antes** de abrir C24 | Es una decisión sobre C24, no sobre C18a. Meterla aquí la escondería en el change equivocado; dejarla sin plantear la haría aparecer con C24 ya abierto |
| 6 | ¿Se versiona el informe del lote? | **Sí**, en `Documentos/Proyecto Final AIEng/informes/c18a-family-suggestion-report.md` | Precedente de C06a, C06b, C10 y C12. Es donde vive la evidencia del recuento y de la cola de revisión que el README va a citar |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta**, pese al 🟢 del plan. No está en la ruta crítica dibujada, pero **gatea la medición**: mueve el 30 % del corpus y `embedding_version` no distinguirá el antes del después, así que debe ir por delante de C20, C21 y C24. Además desbloquea la mitad de familia de C30 y C36, ambos irrecortables.
- **Estimación:** _Pendiente_. Complejidad 3/5 — algoritmo determinista y ya medido, tres capas, sin migración ni interfaz. Candidato a partirse otra vez sólo si el veto por embedding se complica.
- **Tags:** `ai-service`, `backend`, `product-family`, `openspec`, `contract-change`, `no-migration`, `C18a`, `EP13`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-018a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-018a.md)
- **Change:** [`add-family-suggestion-and-approval`](./) · rama `c18a-add-family-suggestion-and-approval` desde `ai-eng` en `f5212a7`
- **Épica:** [EP13 — Familias de Producto y Desambiguación de Variantes](../../../../Documentos/epicas.md)
- **Specs vivas:** [`product-family`](../../../specs/product-family/spec.md) · [`index-feed`](../../../specs/index-feed/spec.md) · [`product-document-indexer`](../../../specs/product-document-indexer/spec.md) · [`ai-service-api-contracts`](../../../specs/ai-service-api-contracts/spec.md) · [`ai-gateway-client`](../../../specs/ai-gateway-client/spec.md) · [`ai-vector-schema`](../../../specs/ai-vector-schema/spec.md)
- **Decisiones previas:** [C07 `design.md`](../../archive/2026-08-17-add-product-family-entity/design.md) · [C08 `design.md`](../../archive/2026-08-16-add-product-ai-profile-entity/design.md) · [C09](../../archive/2026-08-23-add-catalog-enrichment-pipeline/) (patrón «Python propone, .NET persiste»)
- **Procedimientos:** [`Procedimiento-UserStories.md`](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [`Procedimiento-TicketsTrabajo.md`](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)
- **Testing:** [`testing-backend.md`](../../../../Documentos/testing-backend.md) *(Estado de la suite: fallos conocidos)* · [`testing-frontend.md`](../../../../Documentos/testing-frontend.md)
- **Apuntes del máster:** `S11_RAG_avanzado/Reindexacion y Versionado Embeddings.md` (deriva de contenido y versionado del índice), `S08_BBDD_Vectoriales/`, `S10_Tecnicas_Recuperacion/`

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-31 | Sergio Valdueza | Creación del ticket a partir de la sesión de exploración del 2026-08-30/31, con las decisiones D1–D8 acordadas y la medición sobre los 1.200 vectores reales |
| 2026-08-31 | Sergio Valdueza | Cerradas las seis preguntas abiertas aplicando su opción por defecto (D9–D14 en la HU): `piece_type` nulo como valor propio de la puerta, `k = 2` sobre 5 vecinos en configuración, `Alianzas` a la cola de revisión, vocabulario de materiales propio con test de fijación, doble etiquetado de C24 remitido a la reestructuración del plan, e informe del lote versionado. Propagadas a las especificaciones técnicas, al DoD y a los riesgos |
| 2026-08-31 | Sergio Valdueza | **Dos de esas seis se revisaron al implementarlas, y la fila de arriba queda como lo que se decidió, no como lo que se entregó.** **D10**: el veto pasa de `mediana − k·MAD` dentro del grupo a la comparación entre grupos, y sus dos parámetros quedan en uno, el margen. **D12**: los vocabularios se **reutilizan** de `enrichment/vocabularies.yaml` en vez de declararse aquí, que era la duplicación que la decisión quería evitar. Ambas revisadas en la etapa 4 de este ticket y en las decisiones 4, 10 y *Open Questions* del `design.md` |
