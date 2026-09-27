# T-AIENG-06a: Real catalog ingestion and assisted text corpus (C06a)

> Ticket técnico del change OpenSpec `add-real-catalog-ingestion-and-text-assist`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-006a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006a.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C06a), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§8.1.1, §8.4, §8.5, §15), sesión de exploración 2026-08-22.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-06a / C06a** — Ingesta del catálogo real (436), corpus JSONL con texto asistido y metadatos de variantes, ingesta local en `public."Products"` por SKU

---

## Contexto y Problema

C05 dejó el esqueleto vectorial (`ai.product_document` con `data_origin`) y C08 abrió la vía de perfiles IA en .NET, pero **el catálogo real sigue siendo textualmente casi vacío**: 436 productos con ~37,7 caracteres de media entre nombre y descripción, 51 sin descripción. C09 no puede demostrar puertas de calidad sobre tags ni C10 simular ventas con semántica creíble mientras el único input sea ese export.

La ficha **C06a** del plan resuelve esto: ingestar los 436 reales, aplicar reparto de calidad dirigido (§8.4), asistir la redacción sin tocar identidad de producto, y emitir JSONL versionado que desbloquee **C09 y C10** sin esperar a C06b.

**Desviación acordada (exploración 2026-08-22).** La ficha original incluye generador Python con cliente LLM y migración Alembic de `text_provenance`. Este ticket adopta:

| Ficha original | Decisión acordada |
|---|---|
| Cliente LLM en `ai-service` | Texto en **pasada asistida** (agente + reglas §15); scripts deterministas en `scripts/catalog/` |
| Migración `text_provenance` en `ai.product_document` | **C13** — no C06a |
| Tests de generador con LLM fake | Tests de scripts deterministas + validación de JSONL; sin llamadas LLM en pytest |
| Solo JSONL | JSONL **commiteado en git** + **informe** + **ingesta local** en `public."Products"` |

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-real-catalog-ingestion-and-text-assist` | **Scaffold creado** (`.openspec.yaml`); proposal/design/specs/tasks **pendientes** |
| `ai-service/src/jbg_ai/data/` | **Ausente** |
| `scripts/catalog/` | **Ausente** |
| `data/catalog/real/product-JoiaBagur.xlsx` | **Presente en local** (gitignored): 436 productos |
| `data/catalog/real/backup-2026-08-17-catalogo-corregido.sql` | **Solo esquema**, sin datos COPY |
| `ai.product_document.data_origin` | **Existe** (C05); **`text_provenance` no** (columna en **C13**) |
| `public."Products"` (.NET) | Sin columna de procedencia de texto; campos: `SKU`, `Name`, `Description`, `Price`, `CollectionId` |
| Postgres Docker | `jpv-pv-postgres`, host **5433**, BD `joiabagur_pv` |
| `ai-service/openapi.json` | **No debe cambiar** en este change |
| HU-AIENG-006a | **Creada** |

**Impacto en producto:** las descripciones visibles en catálogo .NET pasan de escuetas a enriquecidas en entorno local; el JSONL alimenta C09/C10. No hay endpoint nuevo ni pantalla.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `data/catalog/real/generated/` | **Nuevo** — JSONL + `.meta.json` (**commiteados**; derivado anonimizado) |
| `Documentos/Proyecto Final AIEng/informes/` | **Nuevo** — informe `c06a-catalog-enrichment-report.md` |
| `scripts/catalog/` | **Nuevo** — lectura xlsx, agrupación, reparto, ingesta SQL |
| `openspec/changes/add-real-catalog-ingestion-and-text-assist/` | proposal, design, specs, tasks (posteriores a este ticket) |
| `Documentos/Historias/AI-Eng/HU-AIENG-006a.md` | **Nuevo** |
| PostgreSQL local `public."Products"` | **UPDATE** por SKU (**solo `Description`**; invariantes SKU/Price/CollectionId/Name) |
| `ai-service/migrations/` | **Sin cambio en C06a** — migración `text_provenance` en **C13** |
| `backend/`, `frontend/`, `ai-service/openapi.json` | **Sin cambios** |

---

## Especificaciones Técnicas

### Fuente de datos

| Campo xlsx | Uso |
|---|---|
| `SKU` | Clave de match ingesta .NET e identificador en JSONL |
| `Name` | **Inmutable** — no se actualiza en ingesta |
| `Description` | Texto original; reemplazado según tier en ingesta |
| `Price` | **Inmutable** |
| `Collection` | **Inmutable** (`CollectionId` en BD no se toca) |

### Agrupación de variantes

- Referencia orientativa de exploración: ~403 grupos, ~23 con >1 miembro (~56 productos).
- **Hay tolerancia:** no es requisito alcanzar esas cifras exactas; el informe documenta los conteos reales.
- Unidad: **familia de variantes**, no `piece_type` (§8.4).
- Uso **interno** para el sorteo de calidad (misma familia → mismo tier). **No se serializa** en el JSONL (`variant_group_key`, `variant_label`, `family_seed` contaminan C09/C10).
- Algoritmo: documentar en `design.md`; enfoque base: normalización de nombre + sufijos de talla.

### Reparto de calidad (semilla fija, determinista)

| Tier | ~% familias | `text_quality_tier` | `text_provenance` | Descripción |
|---|---|---|---|---|
| Rico | 70 | `rich` | `ai_assisted` | 3–5 frases, más inventiva de vendedor |
| Escueto | 20 | `sparse` | `ai_assisted` | 1–2 frases, más contenido |
| Original | 10 | `original` | `merchant` | `Description` del xlsx **sin cambiar** (vacía o no) |

**Regla crítica:** todos los miembros de una familia interna comparten tier. Esa clave **no** sale en el JSONL. `original` **no** significa «campo vacío»: vaciar un texto que sí estaba en el catálogo es un error.

### Redacción asistida (`catalog-assist/v2`)

- Escribir como un vendedor con la pieza delante: descripción natural de producto, sin mencionar fotos, fichas ni lagunas.
- Conservar todo lo que está en `Name` y `Description` originales.
- No inventar piedras ni accesorios que no consten.
- `rich` se esmera más; `sparse` es 1–2 frases. El tier `original` **no redacta**: deja la `Description` del xlsx exactamente como está.

### Contrato JSONL (línea por producto)

Campos mínimos:

```json
{
  "sku": "SKU01",
  "name": "...",
  "description": "...",
  "price": "48.00",
  "collection_name": "...",
  "data_origin": "real",
  "text_provenance": "ai_assisted",
  "text_quality_tier": "rich",
  "product_id": "uuid-opcional-post-query"
}
```

Prohibidos en cada línea: `variant_group_key`, `variant_label`, `family_seed`.

- `product_id`: **opcional** en JSONL; se obtiene por lookup de SKU contra `public."Products"` durante ingesta o enriquecimiento posterior del artefacto.
- Sidecar `.meta.json`: `generator_version`, `seed`, `generated_at`, ratios, conteos de agrupación.

### Ingesta local PostgreSQL

```text
Host: localhost:5433
Database: joiabagur_pv
Schema: public
Table: "Products"
Match: "SKU" = jsonl.sku
UPDATE: "Description" = jsonl.description, "UpdatedAt" = now()
INVARIANT: "Price", "CollectionId", "SKU", "Id", "Name" unchanged
Script location: scripts/catalog/
```

- Transacción única; rollback si falla invariante.
- SKUs sin fila → lista *unmatched* en informe.
- Snapshot previo recomendado: CSV `SKU, Name, Description` o `pg_dump` parcial.

### `text_provenance` — dónde vive

| Capa | Cuándo |
|---|---|
| JSONL / `.meta.json` | **C06a** |
| Informe | **C06a** (ratios por estrato) |
| `public."Products"` | **Nunca** |
| `ai.product_document` | **C13** (migración Alembic + columna al indexar) |

---

## Arquitectura

**Frontera §6.3.** Metadatos de corpus (`data_origin`, `text_provenance`) viven en **artefactos de generación** (JSONL) en C06a y en `ai.product_document` desde C13. El texto operativo que ve .NET es `Product.Description`. No se emite semilla de familias en el JSONL.

**Sin contrato HTTP.** Este change no toca `jbg-ai` routers ni `openapi.json`. Es trabajo offline + scripts en `scripts/catalog/`.

**Relación con C09.** C09 consume el JSONL (o fixtures derivados) como input de extracción; **no** es parte de C06a.

**Relación con C13.** C13 añade la migración `text_provenance` y puebla `ai.product_document` con ambos ejes de procedencia.

**Breaking changes.** Ninguno en API ni OpenAPI.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec del change completos y `openspec validate --all --strict` → **0 failed**
- [ ] JSONL con **436** líneas commiteado; `.meta.json` con seed y ratios; **sin** campos de familia por línea
- [ ] Informe publicado con estadísticas, muestras de vendedor antes/después y limitación **solo en el informe**
- [ ] Invariante SKU/precio/colección/nombre verificado (JSONL vs xlsx)
- [ ] Ninguna familia interna mezcla tiers; el JSONL no serializa la agrupación
- [ ] Ingesta local ejecutada: UPDATE **solo `Description`** por SKU; `Price`, `CollectionId` y `Name` verificados
- [ ] SKUs unmatched documentados en informe
- [ ] Scripts en `scripts/catalog/` documentados y ejecutables
- [ ] `ai-service/openapi.json` **sin cambios**; backend/frontend sin cambios de API
- [ ] Sin cliente LLM añadido a `pyproject.toml` por este change (salvo que design revierta)
- [ ] Sin migración Alembic en C06a (`text_provenance` queda para C13)
- [ ] Documentación: desviaciones respecto a ficha C06a en `design.md`; HU-AIENG-006a coherente con entregable
- [ ] Change archivado tras verify

---

## Requisitos No Funcionales

- **Seguridad:** xlsx crudo permanece gitignored; JSONL commiteado es derivado anonimizado. Credenciales Postgres local no en repo. Sin RDS producción.
- **Determinismo:** misma `seed` + misma `generator_version` → mismos tiers y agrupación; descripciones reproducibles bajo mismas reglas de redacción.
- **Integridad:** ingesta con transacción; abortar si `Price`, `CollectionId` o `Name` difieren post-update.
- **Testing:** scripts en `scripts/catalog/` testeables sin LLM; pytest sin llamadas a proveedores externos (regla transversal plan §1).

---

## Decisiones cerradas (antes preguntas abiertas)

| # | Tema | Decisión |
|---|---|---|
| 1 | Agrupación ~403/~23 | **Referencia orientativa con tolerancia** — no exige cifra exacta; informe documenta conteos reales |
| 2 | JSONL en git | **Sí** — commitear derivado anonimizado; xlsx crudo sigue gitignored |
| 3 | Migración `text_provenance` | **C13** — fuera de alcance de C06a |
| 4 | Columnas en ingesta | **Solo `Description`** — `Name` inmutable |
| 5 | Ubicación scripts | **`scripts/catalog/`** |
| 6 | `product_id` sin UUID en xlsx | **Lookup por SKU** en ingesta; campo `product_id` opcional en JSONL tras post-query a .NET |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** — 🔴 ruta crítica; desbloquea C09 y C10.
- **Estimación:** **5 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C01 (archivado). No compite por migración EF Core. No requiere C08/C07 para el corpus textual.
- **Tags:** `HU-AIENG-006a`, `T-AIENG-06a`, `C06a`, `EP12`, `python`, `catalog`, `corpus`, `data`, `critical-path`, `offline`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-006a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006a.md)
- **Change OpenSpec:** `openspec/changes/add-real-catalog-ingestion-and-text-assist/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C06a, §0) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Precedentes:** [HU-AIENG-005](../../../../Documentos/Historias/AI-Eng/HU-AIENG-005.md) · [ticket C05](../../archive/2026-08-15-add-pgvector-schema-foundation/ticket.md)
- **Import xlsx:** [`ExcelImportService`](../../../../backend/src/JoiabagurPV.Application/Services/ExcelImportService.cs)
- **Compose Postgres:** [`backend/docker-compose.yml`](../../../../backend/docker-compose.yml)
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-22 | `/enrich-us` | Creación del ticket y HU a partir de exploración C06a |
| 2026-08-22 | Revisión | Renombrado a HU-AIENG-006a / T-AIENG-06a; decisiones cerradas (tolerancia agrupación, JSONL en git, migración en C13, solo Description, scripts/catalog/, product_id por SKU) |
| 2026-08-22 | Revisión v2 | Voz de vendedor (`catalog-assist/v2`); JSONL sin campos de familia; tercer tier `original` (conserva Description del xlsx; no se llama `empty` ni se vacía) |
