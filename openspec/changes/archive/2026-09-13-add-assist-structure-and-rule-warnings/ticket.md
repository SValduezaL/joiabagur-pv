# T-AIENG-030a: Structured sale-assist layer — three modes, rule-derived warnings and verifiable citations with no provider call (C30a)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-028](../../archive/2026-09-13-add-profile-review-ui-and-metrics/ticket.md) y
> [T-AIENG-026](../../archive/2026-09-12-add-substitutes-retrieval/ticket.md).

**HU origen:** [HU-AIENG-030a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-030a.md)
**Change:** `add-assist-structure-and-rule-warnings` (C30a) · **Épica:** EP15
**Rama:** `c30a-add-assist-structure-and-rule-warnings` · **Decisiones:** [c30-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30-exploration-decisions.md)

---

## Título

Sustituir el fixture de `POST /v1/assist/sale` por la **capa estructurada real**: tres modos con
validación de «al menos uno», agrupación por `family_id` **nulable**, `family_roster` nuevo en el
puerto de búsqueda, `warnings[]` como **vocabulario cerrado de códigos**, citas **verificables sin
LLM** —lookup determinista en M2, filtro de slug asimétrico en M1/M3— y puerta de abstención
declarada en `abstained`. **Mueve el `openapi.json` congelado, en un solo bloque**, y **no realiza
ninguna llamada a un proveedor**.

---

## Contexto y Problema

La ruta está en el contrato desde C02 y sirve un fixture. El módulo lo dice de sí mismo:

```python
# ai-service/src/jbg_ai/api/routers/assist.py
DELIVERED_BY = "C30 (add-assist-generation-with-rule-warnings)"
...
require_stub_mode(settings, DELIVERED_BY)     # 501 cuando STUB_MODE=false
return assist_sale_stub(payload, principal)
```

C30 se partió el 13 de septiembre y **esta es la mitad que desbloquea el grafo**: C34 y C36
dependen de **la forma** de la respuesta, no de la prosa. El corte deja además una ablación que el
§11.2 pide y que ninguna otra fila de esa tabla aporta — misma ruta, mismos candidatos, mismas
citas, con argumentario y sin él.

**Y cinco supuestos de la ficha del plan resultaron falsos contra el árbol.** Los dos que gobiernan
el diseño:

```
  AssistGroup REQUIRED: ["family_id","members"]
    family_id: {"type":"string"}        ← obligatorio y NO nullable

  C18b: 156 familias · 486 miembros  sobre ~1.168 filas indexadas
  → ~58 % DEL CATALOGO NO TIENE FAMILIA, y el contrato no puede representarlo
```

```
  C34 expone  GET /api/ai/products/{id}/sales-assist
              GET /api/ai/products/{id}/substitutes
              ← las dos ancladas a PIEZA

  AssistRequest.query: str = Field(..., min_length=1)   ← obligatoria
  AssistRequest  no tiene product_id
  → el único consumidor previsto no puede llamar a la ruta tal como está
```

**El coste de mover el contrato está en su mínimo histórico.** `IAiGatewayClient` expone cinco
métodos y **ninguno de assist**; C34 y C36 no existen. Hoy la ruta tiene **cero consumidores** y a
partir de C34 los tendrá. El README de `ai-service` fija la doctrina —*«Regenerating is a contract
negotiation, not a chore»*— y el precedente es propio: **C18a y C18b regeneraron el snapshot en el
mismo change en que movieron la frontera**.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado hoy | Qué hace C30a |
|---|---|---|
| [`api/routers/assist.py`](../../../../ai-service/src/jbg_ai/api/routers/assist.py) | Stub + `require_stub_mode`, **501** con stubs apagados | **Implementación real** cuando `STUB_MODE=false`; el fixture se conserva cuando está activo |
| [`api/schemas/assist.py`](../../../../ai-service/src/jbg_ai/api/schemas/assist.py) | `query` obligatoria, sin `product_id`; `AssistGroup.family_id: str`; `AssistGroupMember` sin razones; `Citation` de 3 campos; sin `abstained` ni `prompt_version` | **El bloque de contrato entero** |
| [`api/schemas/common.py`](../../../../ai-service/src/jbg_ai/api/schemas/common.py) | `PRICE_PLACEHOLDER`, `STOCK_PLACEHOLDER`, `Usage`, `ScopedResponse` | **Sin cambios**; `Usage` se emite a cero |
| [`stubs/responses.py`](../../../../ai-service/src/jbg_ai/stubs/responses.py) | `assist_sale_stub` fabrica un `family_id` para **cada** grupo | **Se ajusta al contrato nuevo**, incluyendo un grupo sin familia para que ningún cliente pueda ignorar el caso |
| [`retrieval/orchestrator.py`](../../../../ai-service/src/jbg_ai/retrieval/orchestrator.py) | `retrieve_products()`; `_Candidate` lleva `size_label`, `qty_bucket`, `family_id`, `variant_label`; `_to_result` **no emite** `size_label` ni `qty_bucket` | **Se consume, no se modifica.** `size_label` se lee del candidato interno para el aviso; `qty_bucket` **no se lee ni se emite** |
| [`retrieval/ports.py`](../../../../ai-service/src/jbg_ai/retrieval/ports.py) | `ProductSearchPort` con `search`, `search_lexical`, `source_document`, `count_*`, `scope_buckets`, `projection_synced_at`. **No hay `family_roster`** | **Método nuevo** `family_roster(family_id, …)`, leyendo **sólo `ai.product_document`** |
| [`retrieval/abstention.py`](../../../../ai-service/src/jbg_ai/retrieval/abstention.py) | `AbstentionRule`, `should_abstain`, `log_decision`. **Activa por defecto** | **Se consume.** La decisión se **propaga y se declara**; no se enciende nada |
| [`config/settings.py`](../../../../ai-service/src/jbg_ai/config/settings.py) | `jpv_abstention_enabled=True`, `α=0,03`, `N=15`; `jpv_knowledge_distance_threshold=0,51` | **Sin campos nuevos.** El valor efectivo viaja **por parámetro**, como en C20/C23/C25 |
| [`knowledge/search.py`](../../../../ai-service/src/jbg_ai/knowledge/search.py) | `search_knowledge()` es un callable; `compile_vector_sql` / `compile_lexical_sql` sólo aceptan `doc_type`, con `_DOC_TYPE_CLAUSE` inyectado condicionalmente | **Parámetro nuevo de exclusión por documento**, con la misma forma de cláusula condicional, en las dos sentencias y en el protocolo `KnowledgeSearchIndex` |
| [`knowledge/indexer.py`](../../../../ai-service/src/jbg_ai/knowledge/indexer.py) | `document_id(slug)` y `chunk_id(doc_slug, sec_slug)` = `uuid5(KNOWLEDGE_NAMESPACE, …)` | **Se reutilizan.** La exclusión va sobre la **clave primaria**; el lookup de M2 también |
| [`knowledge/corpus.py`](../../../../ai-service/src/jbg_ai/knowledge/corpus.py) | `material_sheet_slug(canonical)`, `missing_material_sheets()` | **Se reutilizan** para enumerar las nueve fichas canónicas |
| [`enrichment/vocabularies.yaml`](../../../../ai-service/src/jbg_ai/enrichment/vocabularies.yaml) | `materials.terms` = **9** términos | **Se lee, no se toca.** Tocarlo fuerza bump de prompt y re-enriquecimiento |
| `ai-service/openapi.json` | Contrato congelado; `test_openapi_snapshot_is_stable` lo vigila | **Se regenera** con el perfil canónico, y el test se actualiza con él |
| [`tests/api/test_assist_stub.py`](../../../../ai-service/tests/api/test_assist_stub.py) | Cubre el fixture actual | **Se amplía**; el árbol espejo gana `tests/assist/` |
| `ai-service/src/jbg_ai/assist/` | **No existe** | La zona de este change |
| `backend/` · `frontend/` | `IAiGatewayClient` sin método de assist; ninguna pantalla de tarjeta | **No se tocan.** Son C34 y C36 |

---

## Componentes Afectados

- **`ai-service/src/jbg_ai/assist/`** — paquete nuevo: resolución de modo, agrupación, reglas de
  aviso, direccionamiento de citas y puerta de abstención.
- **`ai-service/src/jbg_ai/api/`** — `schemas/assist.py`, `routers/assist.py`, `stubs/responses.py`.
- **`ai-service/src/jbg_ai/retrieval/`** — `ports.py` (método nuevo del protocolo) y su
  implementación SQL.
- **`ai-service/src/jbg_ai/knowledge/`** — `search.py` (parámetro y cláusula de exclusión).
- **`ai-service/openapi.json`** — regeneración con el perfil canónico.
- **`ai-service/tests/`** — `assist/`, `api/`, `knowledge/`, `retrieval/`, en árbol espejo.
- **`openspec/changes/add-assist-structure-and-rule-warnings/`** — proposal, design, specs y tasks.
- **`Documentos/`** — épicas, plan de changes e informe de implementación.

**No tocados a propósito:** `backend/`, `frontend/`, `terraform/`, `.github/workflows/`,
`ai-service/migrations/`, `enrichment/` y `prompts/`.

---

## Especificaciones Técnicas

### ai-service — el bloque de contrato

```python
# ── AssistRequest ─────────────────────────────────────────────
  query:      str | None        # era obligatoria (min_length=1)
+ product_id: str | None        # NUEVO
+ model_validator: AL MENOS UNO de los dos

# ── AssistGroup ───────────────────────────────────────────────
  family_id: str | None         # era obligatoria y NO nullable
+ invariante: family_id is None  ⇒  len(members) == 1

# ── AssistGroupMember ─────────────────────────────────────────
+ match_reasons: list[str]      # mismo vocabulario que RetrievalResult

# ── Citation ─────────────────────────────────────── reforma ──
+ citation_id · document_title · section_title · claim_scope · doc_type · score
  snippet · product_id          # se mantienen
− source                        # RETIRADO: lo sustituye citation_id

# ── AssistResponse ────────────────────────────────────────────
+ abstained:      bool          # NO reutilizar low_confidence
+ prompt_version: str | None    # null en C30a
  warnings: list[str]           # MISMO TIPO, vocabulario CERRADO
  intent: str                   # product_pitch (M2) | unclassified (M1, M3)
```

### ai-service — comportamiento por modo

| | `product_id` | `query` | `intent` | citas | abstención |
|---|---|---|---|---|---|
| **M1** | — | ✓ | `unclassified` | `search_knowledge(query)`, sin filtro de material | aplicable |
| **M2** | ✓ | — | `product_pitch` | lookup determinista por `chunk_id`, lista blanca, sólo `general` | no aplica |
| **M3** | ✓ | ✓ | `unclassified` | `search_knowledge(query)` **con filtro de slug** | parte de conocimiento: cero citas |

### ai-service — vocabulario cerrado de `warnings`

| código | condición | fuente del dato |
|---|---|---|
| `family_has_variants` | el roster de la familia declara más de un miembro | `ai.product_document` vía `family_roster` |
| `size_label_missing` | el producto no declara `size_label` | `ai.product_document` |

`stock_critical` y `family_members_out_of_stock` **no se emiten aquí**: necesitan stock real y son
de C34, tras hidratar.

### ai-service — el filtro de slug, sobre la clave primaria

```python
excluded = [document_id(material_sheet_slug(t))
            for t in MATERIALS_TERMS if t not in piece.materials]
#  → cláusula condicional `AND d.id <> ALL(:excluded)` en compile_vector_sql
#    y compile_lexical_sql, con la misma forma que _DOC_TYPE_CLAUSE
#  → sin migración, sin columna nueva y sin tocar jsonb
```

Pasan **siempre**: `faq` (10), `politica` (4), `talla` (4), `piedras-*` (3),
`material-piezas-mixtas` y `material-marcajes-y-punzones` — los dos últimos llevan
`doc_type = material` pero **no son salidas de `material_sheet_slug`**.

### Seguridad y ámbito

`pos_id` sale **del token y nunca del cuerpo**, como en el resto de `/v1`; `effective_pos_id` lo
devuelve. Un `pos_id` que no parsea es un token mal emitido y se rechaza — `projection.py` ya fija
que un punto de venta comodín *«is exactly what must not exist»*.

### Datos

**Ninguna migración.** El roster lee `ai.product_document`; la exclusión de documentos opera sobre
la clave primaria de `ai.knowledge_document`, derivada con `document_id(slug)`. No hay entidad ni
columna nueva, así que `Documentos/modelo-de-datos.md` no cambia.

---

## Arquitectura

- **Frontera respetada**: Python calcula similitud y estructura; **.NET conserva precio, stock y
  permisos**. Los dos avisos de stock cruzan a C34 por esa razón, no por comodidad.
- **El puerto no lee `public`**: `family_roster` se implementa sobre el esquema `ai`, como el resto
  de `ProductSearchPort`.
- **Los valores efectivos viajan por parámetro** (abstención, umbral de conocimiento, lista blanca
  de secciones), con `Settings` aportando sólo el valor por defecto — el patrón que C20, C23 y C25
  establecieron para que el arnés barra configuraciones en un proceso.
- **Se reutiliza el patrón de error de C26**: `source_document` devuelve `None` y el router convierte
  los tres casos inservibles —desconocido, inactivo, sin indexar— en tres respuestas distintas. Una
  pieza ausente **no** es una abstención.

### Breaking changes

**Sí, y declarado:** el esquema de `POST /v1/assist/sale` cambia en peticiones y respuestas, y
`openapi.json` se regenera. **Sin consumidores hoy** (`IAiGatewayClient` no tiene método de assist),
así que el impacto real es cero y la ventana para hacerlo es ésta.

---

## Definición de Hecho (DoD)

- [ ] Código en las capas de `Documentos/modelo-c4.md` y con las convenciones de `openspec/project.md`
- [ ] `uv run pytest` en verde, **sin una sola llamada real** a LLM, *embeddings* ni RDS; fakes inyectados y fixtures en `ai-service/tests/`
- [ ] Nomenclatura `test_<unidad>_<escenario>_<esperado>`; árbol de tests espejo de `src/jbg_ai`
- [ ] Tests de base de datos con Testcontainers + pgvector, que se omiten si Docker no está accesible
- [ ] `openapi.json` regenerado con el perfil canónico y `test_openapi_snapshot_is_stable` en verde
- [ ] **Ninguna migración** de Alembic ni de EF Core
- [ ] Capability nueva **`assist-generation`** y deltas de `ai-service-api-contracts`, `knowledge-corpus` y `retrieval-abstention` en `openspec/changes/<change>/specs/`, con **`openspec validate --all --strict` en `0 failed`**
- [ ] Línea base de las suites comparada **por nombres de test** y no por recuento, antes y después
- [ ] Documentación actualizada: `Documentos/epicas.md`, plan de changes, `ai-service/README.md`
- [ ] Informe de implementación con las cifras de los tres spikes y con lo que la implementación refute de la HU
- [ ] Sin `TODO`/`FIXME` sin tarea de seguimiento
- [ ] Ningún campo de la respuesta contiene precio ni cantidad de stock, comprobado sobre la respuesta completa

---

## Requisitos No Funcionales

- **Seguridad**: JWT interno HS256; `pos_id` del token y nunca del cuerpo; claim que no parsea →
  rechazo, jamás búsqueda global. Sin secretos nuevos.
- **Rendimiento**: **cero llamadas a proveedor**. M2 no toca el índice vectorial. El filtro de slug
  opera sobre 161 fragmentos, donde C23 midió la rama léxica en **~3 ms**. Pool capado a 5
  conexiones sin *overflow*: el roster es **una** sentencia y no una por miembro.
- **Observabilidad**: `trace_id` propagado; log estructurado del modo resuelto, del número de grupos,
  de los códigos de aviso, de los `citation_id` devueltos y de la decisión de abstención.
- **Integridad**: `warnings` restringido a su vocabulario cerrado; el invariante *sin familia ⇒ un
  miembro* y el de *sólo `claim_scope: general` en M2* verificados por test, no por convención.
- **Degradación**: un fallo del proveedor de *embeddings* en M1/M3 degrada la parte de conocimiento
  a **cero citas** —que es el comportamiento que C23 ya define— y nunca convierte la respuesta en un
  error.

---

## Preguntas Abiertas

**Ninguna. Las seis se cerraron el 2026-09-13 tomando la opción por defecto declarada**, antes de
generar el resto de los artefactos del change. Quedan aquí como registro de la decisión y de su
motivo, porque cuatro de ellas son ajustables durante la implementación y conviene saber contra qué
se comparó.

| # | Decisión | Valor fijado | Motivo, y qué se descartó |
|---|---|---|---|
| 1 | **Nombre de la capability nueva** | **`assist-generation`** | C30b añadirá requisitos **sobre esta misma capability** en vez de crear otra, y el nombre cubre el par. Se descarta `sale-assist` porque nombra el caso de uso y no la capacidad, y porque `assisted-search-panel` y `ai-assisted-search` ya ocupan el registro semántico de «venta asistida» en el lado .NET y de frontend |
| 2 | **Secciones de la lista blanca en M2** | `cuidados-y-limpieza-en-casa` y `piel-sensible-y-alergias` | Son las dos presentes y `general` en **las nueve** fichas canónicas. Viajan **por parámetro**, no como constante, para que C30b barra 1/2/3 secciones y publique el efecto sobre la tasa de rechazo de su puerta numérica |
| 3 | **Tope de materiales por pieza en M2** | **2**, en el orden en que la pieza los declara | Más la sección `material-piezas-mixtas#limpiar-una-pieza-mixta-sin-estropear-nada` cuando declara dos o más. También **por parámetro**. El tope acota el riesgo de atribución cruzada entre materiales que la pieza sí declara, que es el único que el filtro no puede resolver |
| 4 | **Los tres spikes** | **Dentro del change**, como tarea 2 | Sus cifras acaban en el informe de implementación en vez de en una nota suelta, y el spike 1 —los dos brazos con y sin filtro de slug— es la primera fila de C30a que puede entrar en la tabla de ablaciones del §11.2 |
| 5 | **El fixture gana un grupo sin familia** | **Sí** | Mismo motivo por el que `families_suggest_stub` y `families_audit_stub` pueblan **todas** sus listas: un fixture donde toda respuesta tiene familia deja pasar un cliente que nunca maneja el caso nulo, y ese caso es el **58 %** del catálogo |
| 6 | **`abstained` en M2** | **Sí, siempre `false`** | Un campo obligatorio ausente según el modo obliga al cliente a ramificar sobre la forma de la respuesta. En M2 no hay recuperación que pueda abstenerse, así que el valor es constante y honesto |

> **Lo que sigue sin decidirse aquí, y a propósito:** los valores de las decisiones 2 y 3 son el
> **punto de partida** de un barrido, no una calibración. El change los fija para poder medirlos;
> quien los mueva después lo hará con una cifra delante, que es la regla que este proyecto aplica
> desde C21.

---

## Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Crítica** — nodo de arranque de la cadena crítica `C30a → C34 → C36`, y en la lista de «nunca se recortan» del §6 del plan |
| **Estimación** | _Pendiente_ — a fijar en refinamiento. El esqueleto de tareas de la HU tiene 12 entradas y el change está dimensionado para **una sesión** tras el desdoble |
| **Tags** | `ai-service` · `python` · `fastapi` · `pydantic` · `contract-change` · `openapi-snapshot` · `rag` · `citations` · `abstention` · `no-migration` · `no-provider-call` · `C30a` · `EP15` |

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-030a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-030a.md)
- **Decisiones de exploración:** [c30-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30-exploration-decisions.md)
- **Diseño:** §7.7 con su bloque revisado del 13 sep, §9.1, §11.2–11.3, §15 limitaciones 12 y 13 — [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Plan de changes:** ficha de C30a en el §3 y entrada del §0 del 13 sep — [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Capabilities consumidas:** [`ai-service-api-contracts`](../../../specs/ai-service-api-contracts/spec.md) · [`knowledge-corpus`](../../../specs/knowledge-corpus/spec.md) · [`retrieval-abstention`](../../../specs/retrieval-abstention/spec.md) · [`hybrid-fusion`](../../../specs/hybrid-fusion/spec.md) · [`product-family`](../../../specs/product-family/spec.md)
- **Precedentes de movimiento de contrato:** C18a y C18b, en [`archive/2026-08-31-add-family-suggestion-and-approval/`](../../archive/2026-08-31-add-family-suggestion-and-approval/) y [`archive/2026-09-01-add-family-review-ui-and-orphan-alert/`](../../archive/2026-09-01-add-family-review-ui-and-orphan-alert/)
- **Procedimientos:** [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-13 | Creación del ticket a partir de HU-AIENG-030a y del informe de decisiones de exploración de C30. Recoge el desdoble de C30 en C30a/C30b y las once decisiones. **Corrige de entrada un dato**: `jpv_abstention_enabled` está **activa** por defecto (`α=0,03`, `N=15`); la primera redacción del informe la daba por desactivada tomándolo de un estado intermedio del apply de C25. La decisión no cambia —lo que la sostiene es el 18 de 20— pero el trabajo sí: se **propaga y declara** una regla que ya decide, en vez de encenderla |
