# T-AIENG-032a: Sales-assistant tool registry — six read-only tools, and the one that had no service behind it (C32a)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-031](../../archive/2026-09-16-add-guardrails-and-intent-router/ticket.md),
> [T-AIENG-030b](../../archive/2026-09-14-add-assist-pitch-generation/ticket.md) y
> [T-AIENG-030a](../../archive/2026-09-13-add-assist-structure-and-rule-warnings/ticket.md).

**HU origen:** [HU-AIENG-032a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032a.md)
**Change:** `add-sales-assistant-tool-registry` (C32a) · **Épica:** EP15
**Rama:** `c32a-add-sales-assistant-tool-registry` · **Siguiente:** C32b, el bucle

---

## Título

Añadir el **registro de herramientas del asistente de venta** sobre la capa que dejaron C30b y C31:
**seis tools** con su esquema de *function calling*, validación de argumentos, **errores devueltos
como observaciones**, el **invariante de solo-lectura comprobado por introspección** y la
**etiqueta cualitativa de disponibilidad** servida desde la proyección. **No entrega el bucle, no
añade ruta y no mueve `openapi.json`.**

---

## Contexto y Problema

C32 se partió el 2026-09-20 por la regla 5 del §1 del plan de changes, con el corte que ya funcionó
en C30: la mitad sin llamadas a un proveedor va primero. Este ticket es esa mitad.

### El problema que la ficha del plan no resolvía

La ficha enumeraba **seis** tools e invocaba, en el mismo párrafo, la regla que retiró a
`perfil_punto_venta` y a `buscar_complementarios`:

> *«una tool que devuelve error es peor que una tool ausente — el bucle la reintenta y quema
> presupuesto»*

Aplicada a `consultar_disponibilidad`, que no tiene implementación, esa regla la retira y deja el
registro en cinco. Pero la misma ficha exige `test_out_of_stock_query_triggers_substitutes_tool`,
que **sin señal de disponibilidad no tiene disparador**. Las dos frases no pueden ser ciertas a la
vez.

Lo que las reconcilia está en el diseño y no en la ficha: el §6.1 declara que el esquema de la
llamada de vuelta Python → .NET *«queda como **decisión abierta del change del agente de venta**»*.
Este ticket la resuelve **difiriéndola con motivo**.

### Estado actual del código, verificado en el repositorio

| Pieza | Fichero | Estado |
|---|---|---|
| `retrieve_products()` | `retrieval/orchestrator.py` | ✅ existe — C14/C21/C25 |
| `retrieve_substitutes()` | `retrieval/substitutes.py` | ✅ existe — C26 |
| `ProductSearchPort.family_roster(family_id, cap)` | `retrieval/ports.py` | ✅ existe — C30a |
| `ProductSearchPort.source_document(product_id)` | `retrieval/ports.py` | ✅ existe — C26 |
| `ProductSearchPort.scope_buckets(pos_id)` | `retrieval/ports.py`, `retrieval/search.py` | ⚠️ existe, declarado *«Read by the evaluation only»*, y devuelve **el surtido entero** |
| `search_knowledge()` + `piece_scoped_exclusions()` | `knowledge/search.py`, `assist/knowledge_scope.py` | ✅ existe — C23 + C30a |
| `clarification_for()` / `clarification_axes()` / `CLARIFICATION_TEMPLATES` | `assist/routing.py` | ✅ existe — C31, cuatro ejes |
| `ProjectionFreshness.reported_age` | `retrieval/projection.py` | ✅ existe — C22 |
| `QTY_BUCKETS = {"0", "1-2", "3+"}` | `indexing/feed.py` | ✅ existe — **son dígitos** |
| Lectura por SKU | — | ❌ **cero** |
| Descriptor de tool, registro, esquemas de *function calling* | — | ❌ **cero** |
| Consulta puntual de disponibilidad en .NET | `Controllers/AiIndexFeedController.cs` | ❌ **cero** — sólo un feed paginado de 200 filas con keyset, `[IndexFeedKey]`, **sin `[Authorize]`** y sin `pos_id` |

### Los tres hallazgos que gobiernan el diseño

1. **El vocabulario de buckets son dígitos.** `{"0", "1-2", "3+"}`. Pasarlo crudo al modelo es pasarle
   una cifra de stock, que es lo que el §6.2 y el §15.10 prohíben y lo que el propio puerto declara
   al decir que *«a bucket on the wire would be the beginning of one»*.
2. **`scope_buckets` no sirve tal cual.** Devuelve el surtido completo del punto de venta —del orden
   de mil filas— para responder por una pieza. Es un volcado, y el apunte de S12 avisa de que un
   resultado inflado desperdicia contexto y confunde al modelo.
3. **La repregunta tiene un requisito vivo que la protege.** `assist-generation` declara que *«The
   clarification question is resolved in code from a closed catalogue of templates»*, y el contrato
   tipa el campo como prosa que **ninguna puerta numérica inspecciona**.

---

## Componentes Afectados

- **`ai-service/src/jbg_ai/assist/`** — `tools.py` (nuevo), `constants.py` (ampliado con los dos
  vocabularios cerrados).
- **`ai-service/src/jbg_ai/retrieval/`** — `ports.py` y `search.py`: **dos lecturas nuevas**, ninguna
  modificación de las existentes.
- **`ai-service/tests/assist/`** — `test_tools.py` (nuevo); reutiliza la costura de `conftest.py` y
  de `tests/support/`.
- **`openspec/`** — change `add-sales-assistant-tool-registry` y su delta de spec.
- **`Documentos/`** — `epicas.md`, plan de changes, `ai-service/README.md`, `tests/README.md`.

**No se tocan:** `backend/`, `frontend/`, `terraform/`, `.github/workflows/`,
`ai-service/openapi.json`, `alembic/`. **Sin migración de EF Core.**

---

## Especificaciones Técnicas

### ai-service — el descriptor y el registro

```text
jbg_ai/assist/tools.py          (NO es jbg_ai/api/schemas: nada de esto viaja al cable)

  ToolSpec        nombre · descripción es-ES · esquema de parámetros · ejecutor
  ToolObservation ok | fallida · contenido acotado · causa de vocabulario cerrado
  build_registry(...)  recibe los puertos YA construidos; nunca los construye

  TOOL_NAMES  conjunto CONGELADO de seis, expuesto como constante y comprobado por test
```

Los puertos llegan **inyectados**, como en todo `assist/`: es lo que hace que ningún test abra un
socket y lo que permite a C32b y a C38 montar el registro con fakes.

### ai-service — las seis tools

| Tool | Argumentos | Sirve | Observación |
|---|---|---|---|
| `buscar_catalogo` | `consulta`, `top_k` acotado | `retrieve_products()` | Candidatos por SKU, sin *scores* crudos ni identificadores internos |
| `buscar_sustitutos` | `sku` | `retrieve_substitutes()` | Alternativas por SKU, con su motivo |
| `listar_familia` | `sku` | lectura por SKU → `family_roster()` | Miembros de la familia con su `variant_label` |
| `consultar_conocimiento` | `pregunta`, `sku` opcional | `search_knowledge()` + `piece_scoped_exclusions()` | Fragmentos con su `citation_id` y su `claim_scope` |
| `consultar_disponibilidad` | `sku` | proyección por punto de venta | **Etiqueta cualitativa** + frescura |
| `pedir_aclaracion` | `eje` del enum cerrado | `clarification_for()` | El texto es-ES de la plantilla |

**Direccionamiento por `sku` y nunca por UUID**, por el precedente literal de C30b y C31: los
identificadores internos de producto se excluyen del *payload* por ser *«dígitos arbitrarios, nunca
se dicen en mostrador»*.

### ai-service — la disponibilidad

```text
QTY_BUCKETS del feed          →  etiqueta cualitativa (vocabulario cerrado, SIN dígitos)
    "0"                       →  sin_existencias
    "1-2"                     →  ultimas_unidades
    "3+"                      →  disponible
    fila ausente / sin pos_id →  sin_ambito        ← NO es "agotado"

la observación declara además la antigüedad de la proyección,
reutilizando la frescura de retrieval/projection.py
```

Regla del §15.10, intacta: **degrada y nunca elimina**. La autoridad sobre el stock sigue siendo
.NET, y la consulta puntual queda **identificada, acotada y no hecha**, con la tool diseñada para
que el puerto se sustituya sin tocar la tool.

### ai-service — los errores

Vocabulario cerrado de causas, con el mismo patrón que los `warnings[]` de C30a: **códigos, nunca
prosa**. Una observación fallida dice *qué* falló para que el consumidor pueda reformular; nunca
escapa una excepción, porque una excepción mataría el bucle de C32b en vez de gastarle una vuelta.

### ai-service — el invariante de solo-lectura

Tres comprobaciones por introspección del registro construido:

1. El conjunto de nombres es **exactamente** el congelado.
2. Ningún puerto capturado por una tool expone método alguno del vocabulario de escritura
   (`insert|update|delete|write|save|upsert|persist|sync|apply`).
3. Ningún cliente HTTP registrado emite otro verbo que `GET`.

**No** se usa una bandera `writes: bool` en el descriptor: una bandera declarativa no demuestra nada
y el §15.8 es una de las tres declaraciones que el README entrega.

### ai-service — contrato y configuración

- **`ai-service/openapi.json` no se mueve**: byte a byte igual. `test_openapi_snapshot_is_stable`
  debe seguir en verde **sin regenerar nada**.
- **Ningún ajuste nuevo de `pydantic-settings`**, ninguna variable de entorno nueva y ninguna
  credencial: esta mitad no llama a ningún proveedor de chat.
- El comportamiento de `POST /v1/assist/sale` es **idéntico** al que dejó C31.

---

## Arquitectura

- **Frontera intacta.** *Python calcula parecidos y redacta; .NET calcula números y decide.* La
  etiqueta cualitativa **no es un número**: es una banda, del mismo tipo que la que el §7.6 ya usa
  para ponderar el ranking. La cifra sigue siendo de .NET.
- **Puertos inyectados**, el patrón de `assist/` desde C30a: el registro recibe
  `ProductSearchPort`, `KnowledgeSearchIndex` y `EmbeddingClient`; no construye ninguno.
- **Se replica, no se reutiliza**, donde reutilizar daría un objeto al que se le puede pedir lo
  equivocado — el criterio con el que C31 replicó la costura del cliente en vez de reutilizar
  `LiteLlmAssistClient`.
- **Breaking changes:** ninguno. No hay ruta nueva, no hay campo nuevo en ningún contrato REST y el
  *snapshot* OpenAPI no se toca. Las dos lecturas nuevas del puerto son **adiciones** a un
  `Protocol`; cualquier implementación existente que no las tenga deja de satisfacerlo, así que hay
  que actualizar también los fakes de la suite (tarea contemplada).

---

## Definición de Hecho (DoD)

- [x] Código implementado según las capas de `Documentos/modelo-c4.md` y las convenciones de `openspec/project.md`
- [x] `ai-service`: `uv run pytest` en verde **sin llamadas reales a LLM, embeddings ni RDS**; comparado **por nombres de test** contra la línea base, nunca por recuento
- [x] `ai-service/openapi.json` **sin cambios**, verificado y no supuesto
- [x] Nomenclatura `test_<unidad>_<escenario>_<esperado>`; fakes inyectados, ningún socket abierto
- [x] Los nueve escenarios de [HU-AIENG-032a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032a.md) trazados a test nombrado
- [x] Spec de la capability actualizada en `openspec/changes/add-sales-assistant-tool-registry/specs/` y **`openspec validate --all --strict` en verde**, no la forma de un solo change
- [x] Documentación actualizada según la tabla *Post-Implementation Documentation Update* de `openspec/project.md`
- [x] Informe de implementación con lo que la implementación refute de este ticket
- [x] Sin TODO/FIXME sin tarea de seguimiento asociada
- [x] Sin migración de EF Core (no aplica), sin cambios en `backend/`, `frontend/` ni `terraform/`

---

## Requisitos No Funcionales

- **Seguridad.** El ámbito de lectura lo fija **el token** y nunca el cuerpo, como en todo `/v1`: si
  el principal no trae `pos_id`, la disponibilidad responde «sin ámbito» y **no inventa ausencia**.
  Ninguna tool escribe, y eso se comprueba estructuralmente.
- **Privacidad.** Nada se persiste: ni observaciones ni argumentos de tool. La consulta del operario
  **no se escribe en ningún log**, por la regla que C30b y C31 dejaron con test. El arnés de
  evaluación sigue siendo la excepción declarada.
- **Rendimiento y free-tier.** Pool de conexiones limitado a 5: la disponibilidad se lee **por pieza**
  y no volcando el surtido. Observaciones acotadas, porque lo que esta mitad decida se reenvía en
  cada vuelta del bucle de C32b y el contexto acumulado es el factor dominante del coste.
- **Observabilidad.** `trace_id` propagado a cada ejecución de tool; la línea de log lleva nombre de
  tool, resultado, causa y latencia, **nunca los argumentos**.
- **Integridad de datos.** La proyección **degrada y nunca elimina** (§15.10). Ausencia de fila no es
  cero.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto |
|---|---|---|
| **Q-1** | ¿Delta de `assist-generation` o capability propia? | **Capability propia** `sales-assistant-tools`. `assist-generation` tiene ya 41 requisitos y describe una ruta HTTP; esto es una biblioteca sin ruta |
| **Q-2** | ¿Tres etiquetas de disponibilidad o cuatro? | **Cuatro**, con «sin ámbito» aparte, porque no puede ser confundible con agotado |
| **Q-3** | ¿`buscar_catalogo` expone `top_k`? | **Sí, acotado** en el esquema con mínimo y máximo |
| **Q-4** | ¿*Snapshot* congelado de los esquemas de *function calling*? | **No.** Se fija con test de forma; `openapi.json` se congela por ser frontera con .NET, y esto no cruza ninguna |
| **Q-5** | ¿La lectura por SKU va en `ProductSearchPort` o en un puerto nuevo? | **En `ProductSearchPort`**, junto a `source_document()` y `family_roster()` |
| **Q-6** | ¿Las observaciones llevan `score`? | **No crudo.** Si hace falta señal de orden, viaja como posición y no como número comparable entre tools |

---

## Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Alta** — taponea a C32b y con él a C38 y C39. El §6 del plan marca C32a y C32b como «nunca se recortan» |
| **Estimación** | _Pendiente_ — complejidad **2/5**: cuatro de las seis tools son envoltorios de código probado, sin proveedor, sin migración, sin contrato que mover |
| **Tags** | `ai-service` · `python` · `assist` · `agent-tools` · `read-only-invariant` · `no-contract-change` · `C32a` · `EP15` |

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-032a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032a.md)
- **Ficha del plan:** [§3 · C32a](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) y la nota del **§0 del 2026-09-20**
- **Diseño RAG:** [§6.1, §6.2, §9.1, §9.2, §15.8, §15.10](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Capability viva:** [`assist-generation`](../../../specs/assist-generation/spec.md)
- **Capabilities consumidas:** [`vector-retrieval`](../../../specs/vector-retrieval/spec.md) · [`substitutes-retrieval`](../../../specs/substitutes-retrieval/spec.md) · [`knowledge-corpus`](../../../specs/knowledge-corpus/spec.md) · [`pos-projection`](../../../specs/pos-projection/spec.md)
- **Tickets precedentes:** [T-AIENG-031](../../archive/2026-09-16-add-guardrails-and-intent-router/ticket.md) · [T-AIENG-030b](../../archive/2026-09-14-add-assist-pitch-generation/ticket.md)
- **Procedimientos:** [Tickets de trabajo](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [User Stories](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)
- **Épica:** [EP15](../../../../Documentos/epicas.md)

---

## Historial de Cambios

| Fecha | Cambio | Autor |
|---|---|---|
| 2026-09-20 | Creación del ticket a partir de la exploración de C32 y de su desdoblamiento en C32a y C32b | Sergio Valdueza Lozano |
