# T-AIENG-018b: Family review UI, persisted review verdicts and orphan alert (C18b)

> Ticket técnico del change OpenSpec `add-family-review-ui-and-orphan-alert`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-018b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-018b.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C18b, §0, §12), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§7.5, §7.8, §11.5, §16), sesión de exploración del 2026-08-31 con medición sobre el Postgres vivo, y código real de `ai-service/src/`, `backend/src/`, `frontend/src/` y `openspec/specs/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el precedente de `add-ai-service-contracts-and-auth/ticket.md`.

---

## Título

**T-AIENG-018b / C18b** — Auditoría de familias persistidas sobre `POST /v1/families/audit` (décima ruta del contrato congelado), entidad `FamilyReviewVerdict` con la séptima migración del plan, listado y borrado de familias en .NET, y carcasa de revisión en frontend que C28 reutilizará

---

## Contexto y Problema

C18a entregó el motor determinista, la ruta `POST /v1/families/suggest`, los dos endpoints de administración y **ejecutó el lote**: 156 familias, 486 miembros, cero conflictos, reconciliación en una sola sincronización incremental (`upserted 486, deleted 32, failed 0`).

Y con ello **dejó sin objeto la ficha de C18b**, que se escribió antes de conocer ese resultado.

**Primero: los tres números que la ficha promete pintar están caducados, y el mecanismo ya no los produce.** La ficha dice *«pintar la cola de revisión que C18a ya calcula: 15 miembros marcados, 4 grupos rechazados y 37 productos excluidos»*. Medido el 2026-08-31 contra `jpv-pv-postgres`: los 15 marcados **no son recalculables** —los 486 miembros ya pertenecen a una familia y `build_candidate_groups` los excluye en su paso 1 por convergencia, y las marcas vivían sólo en la respuesta de `suggest` porque C18a decidió no persistir propuestas—; los grupos rechazados son **2** y no 4, porque `Encargos` y `Presión` salieron del índice con `ProfileReviewStatus = Rejected` en el mismo lote; y los excluidos por la puerta son **11** y no 37, porque 26 estaban entre los 32 retirados. Y `suggest` devuelve hoy **lista vacía**: las 156 propuestas se aplicaron. Construir la pantalla literalmente entregaría **una pantalla vacía**, cuarta aparición de la firma que este proyecto persigue desde C17 tras A1 en C04, B5 en C16 y el índice en C17.

**Segundo: el trabajo real existe, y es otro.** 156 familias que nadie ha mirado —las 156 llevan `Origin = AiApproved` con aprobador e instante de un lote que se disparó de una vez— y **682 productos activos sin familia**, de los cuales **671 tienen `piece_type`** y por tanto pueden competir por una pertenencia.

**Tercero: marcados y huérfanos son el mismo predicado.** Un miembro marcado es un producto **dentro** de una familia al que un extraño le gana a su peor hermano; un huérfano candidato es un producto **fuera** al que le pasa lo mismo respecto de una familia. Mismo cálculo, mismo objeto de revisión —el par `(producto, familia)`—, mismo veredicto humano. Eso permite un endpoint, una consulta y una tabla, y reutiliza `apply_relative_veto` cambiando el universo de familias propuestas por familias persistidas.

**Cuarto: la medición desmintió la hipótesis de partida sobre el criterio del huérfano.** Se entró suponiendo que el umbral relativo se dispararía en cientos y que la pureza de vecindad sería más segura por estar acotada. Es al revés:

| | huérfanos | **A** · margen relativo > 0,02 | **B** · pureza ≥ 3 de 5 | A ∧ B |
|---|---|---|---|---|
| `real` | 216 | **21** | 19 | 6 |
| `synthetic` | 434 | **1** | **55** | 0 |
| **total** | **650** | **22** | **74** | **6** |

B camina directo a la trampa que el `design.md` de C18a documentó (*«fracasa en el sintético, donde `v2`/`v3`/`v4`/`v5` son casi-duplicados deliberados»*): nomina `Anillo Llama Eterna v3` → `Anillo llama eterna v2`, `Collar Vía Láctea v2` → `Collar via lactea`, `Anillo Orión v3` → `Anillo orion v2`. Son familias distintas por construcción de C06b. Curva del margen: `θ = 0 → 40` · `0,02 → 22` · `0,05 → 5` · `0,08 → 3`.

**Quinto: la alerta diagnostica el agrupador, no sólo el catálogo.** Los primeros por margen tienen causa nombrable: `Pendientes botón erizo de mar S dorado` (0,109), `Colgante Lapa Mini Dorado` (0,096) y `Pendientes botón estrella de mar dorado` (0,056) quedaron fuera porque **`dorado` no figura en `materials`** de `enrichment/vocabularies.yaml`, que sí tiene `baño de oro` con los sinónimos `chapado en oro` y `gold plated`. Y como el agrupador lee `name` y no `materials[]`, el sinónimo recupera familias **sin reenriquecer y sin salto de prompt**.

**Sexto: una familia contaminada es un imán.** `Colgante estrella de mar` tiene peor hermano **0,778** —se comió un sintético, hallazgo (d) del informe de C18a— frente a una media de 0,85–0,95, y por eso atrae 4 de los 25 primeros por margen, incluido `Colgante Ancla` con similitud 0,797. Se corrige con orden: auditar miembros antes que huérfanos.

**Séptimo: la contención por el turno de migración ha caducado.** El `design.md` de C18a rechazó persistir descartes porque *«el turno de migración de EF Core es único y lo esperan C19, C27 y C29»*. Tras la anulación de la rama de C19 el 2026-08-31, el §12 del plan dice: *«la única viva es la de C27, y lleva corte pre-autorizado»*.

### Estado actual del código (verificado 2026-08-31 en repo y en el Postgres local)

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-family-review-ui-and-orphan-alert` | **Scaffold** (`.openspec.yaml`, schema `spec-driven`, 0/4 artefactos); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| Rama de trabajo | `c18b-add-family-review-ui-and-orphan-alert`, creada desde `ai-eng` en `6ffd390` |
| `jbg_ai.families` | ✅ C18a — `grouping.py`, `naming.py`, `veto.py`, `vocabulary.py`, `repository.py`, `orchestrator.py`, `errors.py`. `apply_relative_veto` y `load_member_similarities` **reutilizables** cambiando el universo |
| `POST /v1/families/suggest` | ✅ C18a. Novena ruta. Excluye por convergencia los productos ya asignados → **hoy devuelve lista vacía** |
| `ai-service/openapi.json` | ✅ **9 rutas** congeladas: `assist/sale`, `enrich/products`, `evals/runs`, `families/suggest`, `index/status`, `index/sync`, `inventory/propose`, `retrieval/products`, `retrieval/substitutes` |
| `IAiGatewayClient` | ✅ 4 métodos: `SearchAsync`, `EnrichAsync`, `HealthAsync`, `SuggestFamiliesAsync`. **Sin** método de auditoría |
| `AiCatalogController` (`api/ai/catalog`) | ✅ `[Authorize(Roles = "Administrator")]`; `POST enrich-batch`, `POST family-suggestions`, `POST family-suggestions/apply` |
| `ProductFamiliesController` (`api/product-families`) | ✅ `GET {id}`, `POST`, `PUT {id}`, `PUT {id}/members`. **No hay listado ni `DELETE`** |
| `ProductFamilyService` | ✅ C07. `ReplaceMembers` idempotente, `StampUpdatedAtAsync`, 409 con detalle por producto (`SqlState 23505`) |
| **Datos de familia** | **`ProductFamilies` = 156** (todas `Origin = AiApproved`, **0 `Manual`**) · **`ProductFamilyMembers` = 486** |
| **Índice** | `ai.product_document` = **1.168** · con `family_id` = **486** · activos sin familia = **682** (671 con `piece_type`, 11 sin) |
| Perfiles | `Approved` = 1.168 · `Rejected` = 32 (retirados del índice por C18a, **todos con `IsActive = true`**) |
| Migraciones EF Core | 15 en `backend/src/JoiabagurPV.Infrastructure/Data/Migrations`, la última `20260816210303_AddProductFamily` (C07). **Ninguna entidad de veredicto** |
| `.NET` ↔ esquema `ai` | ❌ **.NET no mapea `ai`** — cero referencias en `Infrastructure/`. Los vectores son de Python |
| `enrichment/vocabularies.yaml` | `materials.terms`: `plata, oro, baño de oro, hilo, latón, acero, resina, cuero, perla`. `synonyms` incluye `chapado en oro` y `gold plated` → `baño de oro`. **`dorado` ausente** |
| Frontend | `pages/admin/` contiene **sólo** `ai-model.tsx`. `AdminRoute` + `Layout8` en `routing/app-routing-setup.tsx`. No hay servicio ni tipos de familia |
| Stack frontend disponible | `@tanstack/react-table` 8.21, `react-hook-form` 7.54, `zod` 3.24, Vitest 4, MSW 2.12 |

---

## Componentes Afectados

- **`ai-service/`** — `src/jbg_ai/families/` (extensión al caso persistido), `src/jbg_ai/api/routers/families.py`, `src/jbg_ai/api/schemas/families.py`, `src/jbg_ai/stubs.py`, `src/jbg_ai/config/settings.py`, `src/jbg_ai/enrichment/vocabularies.yaml`, `openapi.json` y sus tests.
- **`backend/`** — `JoiabagurPV.Domain/Entities` (entidad nueva), `JoiabagurPV.Infrastructure/Data` (configuración EF + migración), `JoiabagurPV.Application` (DTOs, interfaz y servicio, validadores), `JoiabagurPV.API/Controllers` (`AiCatalogController`, `ProductFamiliesController`), `JoiabagurPV.Tests`.
- **`frontend/`** — `src/pages/admin/`, `src/components/admin/`, `src/services/`, `src/types/`, `src/routing/`, `src/lib/materials-vocabulary.ts`, y sus tests.
- **`openspec/`** — specs delta de `family-suggestion`, `product-family`, `ai-service-api-contracts` y `ai-gateway-client`; artefactos del change.
- **`Documentos/`** — HU, `epicas.md` (EP13), `modelo-de-datos.md`, ficha C18b del plan e informe del lote.
- **No se toca** — `terraform/`, `.github/workflows/`, `indexing/embeddings.py`, `source-text/v1`, `piece_type.terms`, y el esquema `public` por SQL desde Python.

---

## Especificaciones Técnicas

### Auditoría en `jbg-ai` (`jbg_ai.families`)

Extensión del paquete de C18a, **sin declarar vocabulario nuevo** (misma regla que D12 de C18a) y **sin llamar al proveedor de embeddings** — los vectores están persistidos.

- **Carga de pertenencias reales**: lectura de `ai.product_document` con `family_id IS NOT NULL`, agrupada por familia. Sólo lectura, sólo el esquema que Python posee.
- **Peor hermano por familia**: mínimo coseno intra-familia, con `<=>` resuelto en PostgreSQL y no en Python, siguiendo el criterio de `load_member_similarities` (*«one statement rather than one per member: the connection pool is capped at five»*).
- **Miembros marcados**: `apply_relative_veto` sobre familias persistidas. Un miembro se marca cuando un producto de **otra** familia lo bate a su peor hermano por más de `JPV_FAMILY_VETO_MARGIN`.
- **Huérfanos candidatos**: para cada producto activo con `family_id IS NULL` y `piece_type` no nulo, y **sólo contra familias de su mismo tipo de pieza**, se calcula `max_sim(h, F) − peor_hermano(F)`; se nomina si supera `JPV_FAMILY_ORPHAN_MARGIN`. La **pureza de vecindad** (de los 5 vecinos más próximos del mismo tipo de pieza, cuántos son de una misma familia) se calcula y se devuelve como **señal de ordenación**, nunca como criterio de nominación.
- **Exclusión de pares ya juzgados**: la petición trae los pares `(product_id, family_id)` con veredicto, y la respuesta no los repite. Es el mismo patrón que `apply` de C18a —el llamante trae el estado, el servicio no lo almacena— y evita que Python tenga que leer `public`.
- **`data_origin` en cada candidato**, para poder contar las dos poblaciones por separado.
- **Determinismo**: mismas entradas y misma configuración ⇒ misma respuesta. Sin LLM.

### `POST /v1/families/audit` (`jbg-ai`) — **décima ruta del contrato**

| | |
|---|---|
| Autenticación | JWT interno HS256; el token manda sobre el body |
| Rol | Sólo `Administrator`, propagado desde .NET |
| Request | `veto_margin` y `orphan_margin` opcionales (por defecto, configuración), `max_orphans`, y `judged_pairs[]` |
| Response | `flagged_members[]`, `orphan_candidates[]`, `rejected_groups[]`, `excluded_products[]`, `families_reviewed_count`, `trace_id` |
| `STUB_MODE` | Respuesta determinista, como el resto de rutas |
| Contrato | `openapi.json` se regenera y `test_openapi_snapshot_is_stable` se actualiza **en este change** |

### Endpoints .NET

| Ruta | Método | Rol | Notas |
|---|---|---|---|
| `api/ai/catalog/family-audit` | `POST` | Administrator | Llama a `jbg-ai` con el JWT interno; adjunta los pares ya juzgados leídos de `FamilyReviewVerdict`. Manejo de `AiNotImplementedException` → 503 y `AiUnavailableException` establecido por C09 |
| `api/ai/catalog/family-verdicts` | `POST` | Administrator | Registra veredictos en bloque sobre pares `(ProductId, FamilyId)`. Idempotente: repetir el mismo veredicto no duplica fila |
| `api/product-families` | `GET` | Administrator | **Nuevo.** Paginado, máximo 50 por página; filtros por `origin`, `pieceType` y `hasFlaggedMembers` |
| `api/product-families/{id}` | `DELETE` | Administrator | **Nuevo.** Disuelve la familia; los miembros cascadean por la regla de C07 y los productos quedan libres. Estampa `Product.UpdatedAt` de los que salen |

Validación con FluentValidation, siguiendo `FamilySuggestionValidators.cs`. Cota de lote en el registro de veredictos, espejada como constante igual que `MaxProposalsLimit`.

### Persistencia

Entidad `FamilyReviewVerdict` en `public`, junto a `Origin` / `ApprovedByUserId` / `ApprovedAt`, que ya viven ahí.

| Campo | Tipo | Notas |
|---|---|---|
| `Id` | `Guid` | `BaseEntity` |
| `ProductId` | `Guid` | FK a `Products`, obligatoria |
| `FamilyId` | `Guid` | FK a `ProductFamilies`, obligatoria, **borrado en cascada** |
| `Verdict` | `enum` | `Confirmed` \| `Rejected` |
| `ReviewedByUserId` | `Guid` | FK a `Users` |
| `ReviewedAt` | `timestamptz` | |
| `MarginAtReview` | `double?` | Margen en el instante de revisar; nulo cuando no venía de la alerta |
| `Note` | `string?` | Máx. 500 |

Índice **único** sobre `(ProductId, FamilyId)`: el par es la identidad del juicio, y un segundo veredicto es una corrección, no una fila nueva. Índice de apoyo sobre `FamilyId` para el listado.

**Séptima migración del plan del Proyecto Final** (decimosexta del repositorio). Test de desfase modelo↔migración con el arnés construido en C04 y heredado por C07 y C08, más aserciones sobre `information_schema` y `pg_indexes`.

### Vocabulario

`materials.synonyms` += `dorado: baño de oro` en [`enrichment/vocabularies.yaml`](../../../../ai-service/src/jbg_ai/enrichment/vocabularies.yaml), espejado en `frontend/src/lib/materials-vocabulary.ts` con su test de fijación. **No se toca `piece_type.terms`** ni el prompt: eso es `fix-enrichment-vocabulary-gaps`, change propuesto en el §0 del plan y **sin número asignado** — no confundir con **C20 `add-synonym-dictionary`**, que es un diccionario de sinónimos **de consulta**, vive en `retrieval/` y no tiene relación con este trabajo.

### Frontend

- Ruta de administrador nueva bajo `AdminRoute` + `Layout8`, con constante en `routing/routes.tsx` y carga diferida como el resto.
- `services/family-review.service.ts` con rutas relativas (`VITE_API_BASE_URL` ya lleva `/api`), siguiendo el patrón de `ai-health.service.ts`.
- `types/family-review.types.ts` espejando los DTOs.
- Tabla con **TanStack Table** (ya en dependencias), navegación por teclado, confirmación en bloque y cronómetro por ítem.
- Componentes de [`analisis-metronic-frontend.md`](../../../../Documentos/Propuestas/analisis-metronic-frontend.md) **antes** de crear ninguno nuevo.
- **Tres estados distinguibles por lista** (D20): *calculada y vacía*, *no disponible porque el servicio no contestó*, y *calculada con contenido*. El segundo nunca se pinta como el primero. Las listas que dependen de vectores —marcados y huérfanos— pueden estar no disponibles mientras la revisión de familias, que no los necesita, sigue operativa: son estados por lista, no de página.
- UI en es-ES, moneda EUR (€).
- Lo que C28 reutilizará se extrae **sólo** donde su ficha lo pide por escrito —tabla editable, atajos de teclado, aprobación masiva, registro de quién revisó y qué cambió—, no por conjetura.

### Datos

`Documentos/modelo-de-datos.md` incorpora `FamilyReviewVerdict`, sus relaciones y su índice único.

---

## Arquitectura

- **Python calcula, .NET conduce y persiste.** Decisión 1 de C18a, vigente y reforzada: `.NET` no mapea `ai` y Python sólo tiene `X-Index-Feed-Key` de lectura hacia .NET. La auditoría es lectura pura del esquema que Python posee; toda escritura es de .NET.
- **Se escribe siempre por `ProductFamilyService`**, nunca por SQL. El watermark del feed es `greatest(Product, perfil, familia cuando es miembro actual)`, así que sacar a un producto de una familia **exige el estampado** o el feed incremental no lo emitiría nunca — el matiz que C18a corrigió al escribir su test.
- **Dos caminos de escritura, declarados**: producto **sin** familia → `family-suggestions/apply` (C18a); producto **con** familia → `PUT /api/product-families/{id}/members` (C07).
- **Trampa heredada de C07**: el reemplazo declarativo falla si las altas se declaran añadiéndolas a la colección de navegación —`BaseEntity` asigna el `Guid` en el constructor y EF emite un `UPDATE` contra nada—, y *«sólo se manifiesta cuando una misma petición borra e inserta a la vez»*. **Mover un producto de una familia a otra es exactamente ese caso.**
- **Sincronización incremental, nunca `--full`.** Decisión 8 de C18a: un `--full` taparía un fallo de estampado en lugar de exponerlo.
- **Breaking changes:** `openapi.json` pasa de 9 a 10 rutas y `test_openapi_snapshot_is_stable` falla deliberadamente; se regenera aquí. Los contratos REST existentes de .NET **no cambian**: los cuatro endpoints son adiciones.
- **Orden respecto de C24:** el change cambia pertenencias, y `preprocessing_id` sigue siendo `source-text/v1`, que no delataría el movimiento. Va **antes de la línea base de C24**. El volumen es pequeño, porque confirmar sin cambiar no mueve el corpus.

---

## Definición de Hecho (DoD)

- [ ] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus (integración con Testcontainers/PostgreSQL), nomenclatura `Método_Escenario_ResultadoEsperado`, cobertura ≥70 %
- [ ] Frontend: Vitest + React Testing Library + MSW, nomenclatura `should [comportamiento] when [condición]`, queries accesibles, cobertura ≥70 %
- [ ] `ai-service`: `uv run pytest` en verde **sin llamadas reales** a LLM, embeddings ni RDS; `openapi.json` regenerado y test de deriva actualizado
- [ ] **Tres** migraciones de EF Core creadas, aplicables y con test de desfase modelo↔migración: `AddFamilyReviewVerdict`, `AddFamilyReviewSeconds` y `AddVerdictSubjectPopulation`
- [ ] Backfill de `SubjectWasMember` sobre los veredictos anteriores a la columna, **revisado por una persona antes de ejecutarse**: escribe sobre datos de revisión y la reconstrucción es una inferencia
- [ ] **Línea base medida y anotada antes de tocar nada**: 156 familias, 486 miembros, 682 huérfanos activos, 1.168 documentos
- [ ] **Diff completo de propuestas antes y después del sinónimo `dorado`**, no sólo los tres casos buscados
- [ ] **Comprobación manual con `jbg-ai` parado** (D20): cada lista dice si está vacía o no disponible, y la revisión de familias sigue siendo posible. MSW no basta — el fallo de C17 fue precisamente que el camino degradado parecía correcto
- [ ] Reconciliación por **sincronización incremental**, verificando que se emiten exactamente los productos estampados y ninguno más
- [ ] Informe del lote versionado en `Documentos/Proyecto Final AIEng/informes/c18b-family-review-report.md`, con tasa de corrección del agrupador, tiempo medio de revisión y reparto por `data_origin`
- [ ] Specs delta actualizadas y `openspec validate --all --strict` en **`0 failed`**
- [x] **Ficha C18b del plan corregida** — hecho el 2026-08-31, antes de abrir el change: ficha reescrita y marcada 🗄️, zona corregida, entrada fechada en el §0, fila de la tabla maestra, recuento de migraciones y nota de recortabilidad del §6
- [ ] Documentación restante actualizada: `epicas.md` (EP13) y `modelo-de-datos.md` con la entidad nueva
- [ ] Compatibilidad hacia atrás verificada en los contratos REST de .NET
- [ ] Sin TODO/FIXME sin tarea de seguimiento asociada
- [ ] UI en español (es-ES) y moneda EUR (€)

---

## Requisitos No Funcionales

- **Seguridad**: los cuatro endpoints .NET sólo `Administrator`; JWT interno HS256 hacia `jbg-ai` con el rol propagado; sin secretos en el repositorio. El operador no participa en ninguna operación de este change.
- **Rendimiento**: la auditoría recorre 486 miembros y 671 huérfanos contra 156 familias. Las similitudes se resuelven **en PostgreSQL con `<=>`**, en el menor número de sentencias posible, porque el pool está limitado a cinco conexiones para todo el servicio; los vectores **nunca** se cargan en Python. Listado paginado con máximo 50 por página. Bundle inicial < 500 KB, con carga diferida de la página nueva.
- **Observabilidad**: `trace_id` propagado extremo a extremo; logging estructurado con Serilog en .NET; la respuesta de auditoría informa de los recuentos que el informe va a citar.
- **Integridad de datos**: índice único sobre `(ProductId, FamilyId)`; borrado de familia en cascada sobre sus veredictos; toda escritura de pertenencia a través de `ProductFamilyService`, con estampado de `Product.UpdatedAt` en las dos direcciones.

---

## Preguntas Abiertas

**Ninguna bloqueante.** Las seis que este ticket abrió el 2026-08-31 se cerraron el mismo día, todas confirmando su opción por defecto. Quedan registradas abajo con su motivo, y en la HU como **D14–D20**. La séptima, **D20**, se abrió y se cerró en dos pasos el mismo día: primero como recorte, después revertida al comprobar que el requisito no podía vivir sólo en el cliente.

Una sola cuestión sigue viva, y es **de otro change**: `fix-enrichment-vocabulary-gaps` —ampliar `piece_type.terms` con `diadema`, `gemelos`, `cinturon` y `llavero`, y saltar a `enrichment/v2`— no tiene número asignado ni ficha en la tabla maestra, y **debe ordenarse antes de la línea base de C24** por el mismo argumento que ordena a éste. C18b no lo resuelve ni lo bloquea.

### Decisiones cerradas el 2026-08-31

| # | Decisión | Motivo |
|---|---|---|
| **D14** | **`dorado` es sinónimo de `baño de oro`**, no de `oro` | El catálogo vende `Colgante Erizo S oro` y `Colgante dorado erizo de mar S` por separado, luego la tienda los distingue; y si el mapeo fuese a `oro`, la guarda de etiquetas duplicadas lo rechazaría. La hipótesis es **falsable** y el diff de propuestas la comprueba: si el mapeo estuviera mal, el grupo aparecería rechazado por `duplicate_variant_labels` en lugar de fusionarse |
| **D15** | **Se acepta que la etiqueta de variante sea `baño de oro`** aunque el dependiente diga `dorado` | La spec viva obliga a la forma canónica en el eje de material, y su motivo sigue vigente: dos grafías de un material darían dos etiquetas para la misma cosa, un par que **pasa la guarda de unicidad —que compara etiquetas, no significados— y llega a la tienda como una familia cuyas dos variantes son indistinguibles en la vitrina**. Se anota como limitación en el informe del lote |
| **D16** | **Un veredicto no se invalida automáticamente** cuando el producto se reenriquece o se reembebe | Se guarda `MarginAtReview` y se muestra junto al margen actual —*«revisado el T con margen 0,16; hoy 0,31»*— en lugar de una lógica de reaparición que nadie mantendría. Honesto y barato: el dato que hace falta para juzgar si el veredicto envejeció está delante de quien lo revisa |
| **D17** | **`JPV_FAMILY_ORPHAN_MARGIN` se fija después de la auditoría de miembros**, sobre números recalculados, arrancando en `0` | Fijarlo antes sería calibrarlo contra el imán que el propio change arregla: `Colgante estrella de mar`, con peor hermano 0,778, se lleva 4 de los 25 primeros. Y con los veredictos persistidos, **un descarte se paga una vez**, mientras que un huérfano que el margen dejó fuera no aparece jamás: la asimetría favorece arrancar generoso |
| **D18** | **El registro de veredictos es endpoint propio** (`family-verdicts`), no un modo de `family-audit` | Auditar es lectura y no debe escribir nunca. Es la misma separación que C18a impuso entre `suggest` y `apply`, y el escenario de aceptación que exige que la auditoría no toque nada sólo es verificable si el camino de escritura es otro |
| **D19** | **De la carcasa se extrae sólo lo que la ficha de C28 pide por escrito**: tabla editable, atajos de teclado, aprobación masiva y registro de quién revisó y qué cambió | Diseñar para dos inquilinos con uno solo a la vista produce abstracciones equivocadas. Lo que está especificado se comparte; lo conjeturado, no. Si C28 necesita más, lo extrae C28, que es cuando se sabrá qué |
| **D21** | **Aplicar el veredicto, corregir la etiqueta y persistir el tiempo entran en el alcance** *(2026-09-01)*, en lugar de quedar como deuda para C28 | Los tres salieron de revisar de verdad y ninguno se veía en el diseño. Siete decisiones quedaron sin efecto sin que nada lo dijera; cuatro etiquetas hubo que corregirlas por API; y los tiempos de la primera sesión se perdieron al cerrar la pestaña, que es media métrica del §16. Dejarlos fuera habría entregado una pantalla que registra juicios sin consecuencia y una cifra que no se puede recuperar |
| **D22** | **La población de un juicio se captura al registrarlo** (`SubjectWasMember`), no se deduce del estado actual | Una vez que un miembro rechazado sale de su familia queda indistinguible de un candidato rechazado: ninguno es miembro, ambos rechazados. Derivarla del presente falla exactamente en los juicios que sí se ejecutaron, e infla una cola vaciando la otra. Lo escribe el servidor, que es quien conoce la pertenencia |
| **D20** | ~~El comportamiento con `jbg-ai` caído sale de alcance~~ → **revisada el mismo 2026-08-31: entra en alcance.** La pantalla distingue tres estados por lista —*calculada y vacía*, *no disponible*, *con contenido*— con escenario de aceptación y test | El recorte dejaba el requisito en `ai-gateway-client`, que sí debe distinguir un fallo de una auditoría sin hallazgos, pero **no en la superficie que la persona mira**, y ahí el cliente no basta: una lista vacía pintada sin más **es** la respuesta equivocada, la distinga o no la capa de debajo. Es la forma exacta en que se materializó el riesgo de C17 —resultados plausibles por el camino léxico sin decir que la asistencia estaba apagada— y sobre una pantalla de calidad de catálogo el daño es peor, porque «nada que revisar» se lee como **«el catálogo está limpio»** |

---

## Prioridad / Estimación / Tags

- **Prioridad:** Media-alta. Hoja del grafo —no tapona a nadie— pero es el único change que puede producir la evidencia del renglón *«métricas de revisión humana»* del §16, que hoy no tiene ninguna, y **debe ir antes de la línea base de C24** porque cambia pertenencias.
- **Estimación:** _Pendiente_ · **Complejidad:** 4 — cuatro superficies (Python, contrato HTTP, .NET con migración, frontend), primera migración desde C08 y primera pantalla de administración pensada para dos inquilinos.
- **Tags:** `ai-service`, `backend`, `frontend`, `database-migration`, `openapi-contract`, `human-review`, `catalog-quality`, `EP13`, `C18b`

---

## Enlaces o Referencias

- HU origen: [HU-AIENG-018b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-018b.md) · Anterior: [HU-AIENG-018a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-018a.md)
- Change: [`add-family-review-ui-and-orphan-alert`](./) · Anterior: [`2026-08-31-add-family-suggestion-and-approval`](../../archive/2026-08-31-add-family-suggestion-and-approval/)
- Informe de C18a: [`c18a-family-suggestion-report.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c18a-family-suggestion-report.md)
- Plan: [`proyecto-final-plan-changes-openspec.md`](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) — ficha C18b, §0 (partición de C18, anulación de la rama de C19, propuesta `fix-enrichment-vocabulary-gaps`), §12 (turno de migración)
- Diseño: [`proyecto-final-diseno-rag-joiabagur.md`](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) §7.5, §7.8, §11.5, §16
- Specs vivas: [`family-suggestion`](../../../specs/family-suggestion/spec.md), [`product-family`](../../../specs/product-family/spec.md), [`ai-service-api-contracts`](../../../specs/ai-service-api-contracts/spec.md), [`ai-gateway-client`](../../../specs/ai-gateway-client/spec.md), [`index-feed`](../../../specs/index-feed/spec.md), [`ai-vector-schema`](../../../specs/ai-vector-schema/spec.md)
- Procedimientos: [`Procedimiento-UserStories.md`](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md), [`Procedimiento-TicketsTrabajo.md`](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)
- Testing: [`testing-backend.md`](../../../../Documentos/testing-backend.md), [`testing-frontend.md`](../../../../Documentos/testing-frontend.md) — **ambas suites vienen rojas de base**; comparar **nombres** de test, nunca recuentos
- Frontend: [`analisis-metronic-frontend.md`](../../../../Documentos/Propuestas/analisis-metronic-frontend.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-08-31 | Creación del ticket con `/enrich-us`, tras la sesión de exploración que midió el estado del corpus, comparó los dos criterios de nominación de huérfanos sobre datos reales y cerró las trece decisiones de diseño de la HU |
