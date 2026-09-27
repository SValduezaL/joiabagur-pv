# T-AIENG-06b: Synthetic catalog augmentation with LLM CLI and local ingest (C06b)

> Ticket técnico del change OpenSpec `add-synthetic-catalog-augmentation`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-006b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006b.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C06b, §0 22 ago), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§7.5, §8.1.1, §8.2, D1/D4, §8.4, §15), sesión de exploración 2026-08-22 y cierre de preguntas abiertas.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-06b / C06b** — Corpus JSONL sintético (~1.200 totales), colecciones de diseño (8–12), CLI OpenAI en `jbg_ai.data`, INSERT local sin tocar SKUs reales ni familias

---

## Contexto y Problema

C06a archivó un corpus de **436** productos reales (`data_origin: real`) en [`data/catalog/real/generated/catalog-real-enriched.jsonl`](../../../../data/catalog/real/generated/catalog-real-enriched.jsonl), con texto asistido e ingesta `UPDATE` de `Description`. Eso desbloquea C09. C11 y C24 necesitan **volumen en `.NET`**: el índice nace del feed C12, no del JSONL.

La ficha v3 de C06b pedía un generador determinista que calibrara precio, SKU y ~350 familias S/M/L al real, con 15 % de huérfanos. La exploración del 2026-08-22 lo sustituye: el real ya tiene 354 grupos internos; prellenar `ProductFamily` chivaría C18; el copy y el precio los razona **OpenAI**; las colecciones son altas nuevas **con nombre de diseño**, no de canal de venta.

**Decisiones de la exploración (cerradas):**

| Ficha 17 ago | Este ticket |
|---|---|
| Generador determinista en `jbg_ai.data.generators/` como pieza de servicio | **CLI** en `jbg_ai.data`; `api.main` **no** lo importa; ni FastAPI ni API .NET |
| Calibrar precio, SKU, materiales, tamaño de familia | Código reserva SKU con el **esquema del real**; OpenAI razona nombre, descripción y precio; ~35 % multi-material **en la prosa** |
| ~350 familias y 15 % huérfanos | **No** se escribe `ProductFamily`. Todos huérfanos. Tallas en el `Name`; el tier se sortea por ese stem |
| 900–1.200 calibrados | Presupuesto **~1.200 totales** (holgura) |
| Colecciones genéricas / de canal | 8–12 nombres de **pieza** («El Jaleo», «Fuego»…). Hotel/aeropuerto/turista/atelier = brief de POS, no `Collection.Name` |
| Solo JSONL | JSONL commiteado **+ INSERT** colecciones y productos en Docker |

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-synthetic-catalog-augmentation` | **Scaffold** (`.openspec.yaml` + ticket + HU); proposal/design/specs/tasks **pendientes** |
| `ai-service/src/jbg_ai/data/` | **Ausente** |
| Cliente LLM / `prompts/` / settings `LLM_*` | **Ausentes.** `Settings` exige `APP_ENV` / `SERVICE_VERSION` / `JWT_SECRET`; `database_url` es opcional |
| `ai-service/pyproject.toml` | FastAPI, SQLAlchemy, psycopg, Alembic, PyJWT — **sin** SDK OpenAI aún |
| `ai-service/openapi.json` | **No debe cambiar** |
| `scripts/catalog/` | Pipeline C06a (`catalog-assist/v2`, plantillas). **No reutilizar `assist.py`** |
| JSONL real | 436 líneas; SKUs `SKU01`… (2/3 dígitos); claves sin `product_id` |
| `public."Products"` | `SKU` unique varchar(50), `Name` 200, `Description` 1000, `Price` decimal(18,2), `CollectionId` nullable, `IsActive`. **Sin** familia ni procedencia. `Id` UUID generado por la BD |
| `Collection.Name` | Unique varchar(100) |
| `ProductFamily` / miembros | Existen (C07). C06a no escribió filas. C06b **tampoco** |
| Postgres Docker | `jpv-pv-postgres`, host **5433**, BD `joiabagur_pv` |
| `.gitignore` | Exceptúa `data/catalog/real/generated/`; **no** `synthetic/generated/` |
| HU-AIENG-006b | **Creada** y alineada con este ticket |

**Impacto en producto:** el catálogo local gana colecciones y productos sintéticos visibles en .NET. No hay endpoint nuevo ni pantalla. El rol de BD de runtime de `jbg-ai` **no** gana `INSERT` sobre `public` (frontera §6.3); el CLI usa `JPV_PG*` como C06a.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/data/` | **Nuevo** — orquestador, reservador de SKU, cliente OpenAI, validación, CLI |
| `ai-service/prompts/` (`catalog-synth/v3` vigente; `v1` y `v2` se conservan) | **Nuevo** — prompt versionado. Distingue brief de público vs nombre de colección. Declara el `text_quality_tier` del lote. No es router |
| `ai-service/src/jbg_ai/config/settings.py` | Clave OpenAI / `LLM_*` **opcionales**; fail-fast del CLI, no de `/health` |
| `ai-service/pyproject.toml` | Cliente OpenAI (u HTTP equivalente); no tocar OpenAPI |
| `data/catalog/synthetic/generated/` | **Nuevo** — JSONL + sidecar commiteados |
| `.gitignore` | Excepción simétrica a `real/generated/` |
| `Documentos/Proyecto Final AIEng/informes/` | Informe `c06b-synthetic-catalog-report.md` |
| PostgreSQL local | **INSERT** `"Collections"` + `"Products"`; **cero** `"ProductFamily*"` |
| `openspec/changes/add-synthetic-catalog-augmentation/` | proposal, design, specs, tasks (posteriores) |
| `backend/` API, `frontend/`, `ai-service/openapi.json`, `ai-service/migrations/` | **Sin cambios** |

---

## Especificaciones Técnicas

### Contrato JSONL (línea por producto sintético)

```json
{
  "sku": "SKU437",
  "name": "...",
  "description": "...",
  "price": "89.00",
  "collection_name": "El Jaleo",
  "data_origin": "synthetic",
  "text_provenance": "synthetic",
  "text_quality_tier": "rich"
}
```

Prohibidos: `variant_group_key`, `variant_label`, `family_seed`, `materials`, `materials[]`, **`product_id`**.

- `sku`: lo asigna el **código**, mismo esquema que C06a: literal `SKU` + 2 dígitos si n &lt; 100 (`SKU01`…`SKU99`), 3 si n &lt; 1000, 4 a partir de 1000. Continúa en **437**. Unique vs JSONL C06a y vs `"Products"."SKU"`. El LLM no inventa SKUs.
- `collection_name`: nombre de **diseño**, no de canal. Unique vs las 28 reales.
- `price`: string decimal como C06a; el LLM lo propone; validador: `> 0`, precisión 18,2, **`price < 50000`**.
- `text_quality_tier`: ~70 `rich` / ~20 `sparse` / ~10 corto o vacío. El código asigna el bucket **antes** del draft (stem de `Name`; hermanos de talla no mezclan tier). La longitud del copy tiene que coincidir: `rich` ≥150, `sparse` ~115 (techo de frase entera 140), `short` ≤32 o vacío (~20 % de los `short` vacíos, stem entero). Nunca se recorta a mitad de frase. `text_provenance` es **siempre** `synthetic`.

Sidecar: `generator_version` (`c06b-synth/v3`), `seed`, `model` (OpenAI + id de modelo), `prompt_version` (`catalog-synth/v3`), `generated_at`, `product_count`, ratios por tier, `empty_short_count`. Opcional: mapa colección → público/POS **pensado** (metadato de generación; no es columna .NET).

### Nombres de colección vs brief de POS

Dos capas que el prompt debe separar:

| Capa | Qué es | Ejemplo | ¿Va a `"Collections"."Name"`? |
|---|---|---|---|
| Nombre editorial | Identidad de la línea, inspirada en las piezas | «El Jaleo», «Fuego», «Cielo estrellado», «La Pomada» | **Sí** |
| Público / POS pensado | Para quién o en qué vitrina se imagina | hotel, aeropuerto, turista, atelier clásico | **No** — brief e informe |

8–12 colecciones nuevas. Un par pueden ser de diseño menorquín/marino; el resto divergen. Prohibido llamarlas Hotel, Aeropuerto, Turista, Atelier o sinónimos de canal.

### Orquestación LLM (OpenAI)

```
código (semilla, presupuesto ~1200 − 436)
  → reserva SKU437, SKU438, …
  → 8–12 briefs: (nombre-de-diseño propuesto o pedido al modelo, público/POS pensado)
  → OpenAI (JSON schema, temperatura > 0): name, description, price; el lote ya trae el tier
  → código: recorte por frases enteras, ~20 % de short vacíos, valida longitud vs tier
  → JSONL + sidecar → git  (sin product_id)
  → INSERT transaccional  (la BD asigna Id)
```

Tests unitarios: LLM **fake**. La pasada real se hace una vez (o con `--regenerate-text`). El artefacto commiteado es la fuente.

### Por qué no hay `product_id` en el JSONL

En C06a el campo era un lookup opcional: el xlsx no trae UUID y alguien podría querer el Guid de .NET en el artefacto. Aquí el producto **no existía**; el `INSERT` crea `Products.Id`. C09 extrae del texto (no necesita Guid). C12/C13 leen el Guid **desde .NET** en el feed. Reescribir el JSONL tras ingerir solo ensucia el diff y no tiene consumidor. **Se omite.**

### Ingesta local PostgreSQL

```text
Host: localhost:5433
Database: joiabagur_pv
Schema: public
1. INSERT "Collections" (Name unique vs existentes; nombre de diseño)
2. INSERT "Products" (SKU, Name, Description, Price, CollectionId, IsActive=true)
   Id = DEFAULT (uuid generado por la BD / BaseEntity)
NEVER: UPDATE de filas cuyo SKU está en el JSONL C06a
NEVER: "ProductFamilies", "ProductFamilyMembers"
NEVER: reescribir el JSONL con product_id
NEVER: RDS
```

Transacción única. Si un SKU sintético ya existe o un nombre de colección colisiona → `ROLLBACK`. Snapshot previo recomendado (no se commitea).

Variables `JPV_PGHOST` / `JPV_PGPORT` / `JPV_PGDATABASE` / `JPV_PGUSER` / `JPV_PGPASSWORD`. Nunca en el repo.

### `text_provenance` — dónde vive

| Capa | Cuándo |
|---|---|
| JSONL / `.meta.json` / informe | **C06b** |
| `public."Products"` | **Nunca** |
| `ai.product_document` | **C13** |

---

## Arquitectura

**Proceso vs paquete.** C06b no arranca Uvicorn. El código vive en el paquete `jbg-ai` para compartir (más adelante) cliente OpenAI con C09 y carpeta `data/` con C10. `create_app` no registra routers nuevos.

**Frontera §6.3.** El servicio `jbg-ai` solo posee el esquema `ai`. El INSERT a `public` es un CLI de desarrollador, no el rol de runtime. Misma excepción documentada que C06a.

**Relación con C09.** Extrae sobre texto. Por eso no viaja `materials[]` ni un prefijo de SKU que grite «synthetic». El prompt **sí** pide mix de materiales en un ~35 % de piezas.

**Relación con C18 / EP13.** C07 ya tiene entidades. C18 propone agrupaciones por embedding + `piece_type` + raíz de nombre. C06b no adelanta miembros. El 70/20/10 usa esa misma raíz **solo** para el tier.

**Relación con C11.** Cierta solo si hay ingesta. Sin filas, el feed no ve el sintético.

**Breaking changes.** Ninguno en API ni OpenAPI.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec del change completos y `openspec validate --all --strict` → **0 failed**
- [ ] CLI documentado; `jbg_ai.api.main` no importa `jbg_ai.data`
- [ ] JSONL sintético commiteado; sidecar con modelo OpenAI y `prompt_version`; **sin** familia, `materials[]` ni `product_id`
- [ ] SKUs `SKU437`… con 2/3/4 dígitos; únicos vs C06a y vs `"Products"`; ~1.200 totales en sidecar (holgura)
- [ ] 8–12 colecciones nuevas de **diseño**; ninguna nombrada como canal/POS; productos sintéticos no reutilizan colecciones reales
- [ ] Tiers 70/20/10; ningún stem de `Name` mezcla tier
- [ ] Ingesta INSERT ejecutada en Docker: reales intactos; sintéticos `IsActive`; cero filas `ProductFamily*`; JSONL no reescrito con UUIDs
- [ ] Informe con muestras, nombres de colección vs público pensado (separados) y recuentos
- [ ] `GET /health` arranca sin clave OpenAI; pytest sin red a proveedores
- [ ] `ai-service/openapi.json` **sin cambios**; backend/frontend API sin cambios; sin migración Alembic
- [ ] `.gitignore` permite `data/catalog/synthetic/generated/`
- [ ] HU-AIENG-006b coherente con el entregable; change listo para archive tras verify

---

## Requisitos No Funcionales

- **Seguridad:** clave OpenAI y Postgres solo por entorno. Sin RDS. JSONL sintético no es PII.
- **Determinismo:** misma `seed` → mismos SKUs y mismos tiers por stem de `Name`. El texto de OpenAI **no** es determinista; el JSONL commiteado sí es la fuente.
- **Integridad:** transacción de ingesta; abortar si colisión de SKU o de `Collection.Name`.
- **Testing:** regla transversal del plan §1 — ninguna llamada real a LLM en tests unitarios. Nomenclatura `test_<unidad>_<escenario>_<esperado>`.
- **Boot:** no convertir la API key de OpenAI en `Field(...)` requerido de `Settings` (rompería C17).
- **Rendimiento / free-tier:** irrelevante en runtime; la pasada generate es offline y de una vez.

---

## Decisiones cerradas (antes preguntas abiertas)

| # | Tema | Decisión |
|---|---|---|
| 1 | Forma del SKU | Mismo esquema que el real: `SKU` + 2/3/4 dígitos según magnitud, desde **437**. Sin `SYN-` (no dar pista a C09) |
| 2 | Proveedor LLM | **OpenAI**. Tests con fake. Dependencia en `pyproject.toml`. Clave solo exigida por el CLI |
| 3 | `text_quality_tier` | **Sí**, ~70/20/10. Misma regla C06a: stem del `Name` comparte tier. `text_provenance` siempre `synthetic` |
| 4 | Colecciones | **8–12** nuevas. Nombre de **diseño**, no de canal. Brief hotel/aeropuerto/turista/atelier aparte |
| 5 | `product_id` en JSONL | **No.** El `Id` lo genera la BD; C12/C13 lo leen de .NET. Reescribir el artefacto no tiene consumidor |
| 6 | Techo de precio | Rechazar `price >= 50000` antes de ingerir. Sin bandas de canal |

Ninguna pregunta abierta bloqueante.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Media** — 🟢; desbloquea volumen de C11/C24, no la ruta C09.
- **Estimación:** **5 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C06a archivado. No compite por migración EF Core. No requiere C07 para el corpus (C07 ya está; este change no lo usa). C18 posterior.
- **Tags:** `HU-AIENG-006b`, `T-AIENG-06b`, `C06b`, `EP12`, `python`, `catalog`, `corpus`, `synthetic`, `openai`, `offline`, `cli`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-006b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006b.md)
- **Change OpenSpec:** `openspec/changes/add-synthetic-catalog-augmentation/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C06b, §0 22 ago) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Precedente:** [HU-AIENG-006a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006a.md) · [ticket C06a](../../archive/2026-08-22-add-real-catalog-ingestion-and-text-assist/ticket.md)
- **Spec viva que no se modifica:** [`real-catalog-corpus`](../../../specs/real-catalog-corpus/spec.md) — C06b introduce capability nueva en el proposal
- **Entidades:** [`Product.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/Product.cs) · [`Collection.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/Collection.cs) · [`ProductFamilyMember.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/ProductFamilyMember.cs)
- **Compose Postgres:** [`backend/docker-compose.yml`](../../../../backend/docker-compose.yml)
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-22 | `/enrich-us` | Creación del ticket y HU a partir de la exploración C06b (LLM+CLI, INSERT, colecciones nuevas, familias en C18) |
| 2026-08-22 | Cierre Q | SKU esquema real desde 437; OpenAI; tiers 70/20/10 por stem de `Name`; colecciones de diseño 8–12; sin `product_id`; techo 50.000 €; canal ≠ nombre de colección |
| 2026-08-22 | Apply v3 | Prompt `catalog-synth/v3`; el tier se declara al LLM; recorte solo por frases enteras; bandas alineadas al real (`rich` ≥150 / `sparse` ~115 / `short` ≤32, ~20 % vacíos); JSONL regenerado |
