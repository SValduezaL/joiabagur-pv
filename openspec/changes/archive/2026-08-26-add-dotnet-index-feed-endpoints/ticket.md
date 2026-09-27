# T-AIENG-012: .NET index-feed endpoints with keyset cursor, tombstones and service API key (C12)

> Ticket técnico del change OpenSpec `add-dotnet-index-feed-endpoints`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-012](../../../../Documentos/Historias/AI-Eng/HU-AIENG-012.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C12, §0 C07, §6.3), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.2, §6.3, §7.2, D10, D11), sesión de exploración 2026-08-25, código real de `backend/src/` y `ai-service/src/`.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-012 / C12** — `GET /api/ai/index-feed/catalog` y `.../pos-availability`: cursor keyset, tombstones, hash agregado, API Key de servicio, `price-band/v1`, invalidación por `UpdatedAt` (sin migración)

---

## Contexto y Problema

Python no puede leer `public` por SQL: C05 materializó la frontera (el rol `jbg_ai` no tiene `SELECT` sobre negocio). C11 construye `doc_text` a partir de un DTO que **aún nadie serializa**. C13 tiene que tirar de un feed HTTP. Sin C12, el indexador o bien viola §6.3 o bien nace vacío.

C07 adjudicó a este change, por escrito, dos fallos mudos: un producto que **sale** de una familia pierde el miembro y el cursor no lo ve; un rename de familia no toca miembros. C08 dejó el predicado de indexación (`ReviewStatus = Approved`) y advirtió que su `SourceHash` no es el del índice. El §6.3 habla de *pull* y de *push*; el *push* HTTP hacia el stub C13 es teatro. La invalidación es ensuciar `UpdatedAt`.

Auth: reutilizar `AiGateway:JwtSecret` haría válidos los tokens C03 que Python ya posee. S9, en este camino (un consumidor, cero identidad), pide API Key.

**Estado actual del código y de la BD (verificado 2026-08-25):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-dotnet-index-feed-endpoints` | **Scaffold** (`.openspec.yaml`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `GET /api/ai/index-feed/*` | **Ausente** |
| Auth API | Un solo `AddJwtBearer` con `Jwt:SecretKey`; cookie `access_token` en `OnMessageReceived`. `AiGateway:JwtSecret` solo **firma** hacia Python |
| `IAiGatewayClient` | Retrieval + enrich. **No** hay operación de feed (Python es el cliente, en C13) |
| `Product` | `SKU`, `Name`, `Description`, `Price`, `CollectionId`, `IsActive`. **Sin** `DataOrigin` |
| `ProductAiProfile` | Un perfil por producto; `ReviewStatus` / `ReviewOrigin` ortogonales; `MaterialsJson` y tags en `jsonb` |
| `ProductFamily` / `ProductFamilyMember` | Índices `UpdatedAt` listos. `ReplaceMembersAsync` borra e inserta; **no** toca `Product.UpdatedAt` |
| `SaveChangesAsync` | Sella `UpdatedAt` en entidades `Modified`. Un delete de miembro no modifica `Product` |
| `Inventory` | `Quantity`, `IsActive`, `LastUpdatedAt` (+ `UpdatedAt` de `BaseEntity`) |
| `Sale.Quantity` / `SaleDate` | Histórico C10 ingerido (22.961 ventas). `Return` existe y **no** se resta en este feed |
| `PaginationConstants.MaxPageSize` | **1000**. Listados de productos: default 50, max 100. **No** usar esa constante en el feed |
| `AiEnrichRequest.MaxBatchSize` | **50** — tope de `enrich-batch`, no del feed POS |
| `"Products"` Docker (`:5433` / `joiabagur_pv`) | **1.200** |
| `"ProductAiProfiles"` / `"ProductFamilies"` | **0** / **0** |
| Esquema `ai` en ese volumen | **Ausente** (bootstrap C05 no corrido) |
| `STUB_MODE` Compose | `"true"` — AutoBulk real exige `false` + `JPV_RAG_LLM_API_KEY` |
| `POST /v1/index/sync` | Stub C13. **No se toca** |
| `ai-service/openapi.json` | **No debe cambiar** |
| `ProductSourceText` (C11) | Contrato de campos de prosa/perfil/familia-nombre que el feed debe poder mapear |
| HU-AIENG-012 | **Creada** y alineada con este ticket |

**Impacto en producto:** ninguno visible. El valor es habilitador: C13 deja de tener que elegir entre SQL ilegal y un índice vacío.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `JoiabagurPV.API/Controllers/` | **Nuevo** `AiIndexFeedController` — ruta literal `api/ai/index-feed` |
| `JoiabagurPV.API/Extensions/ServiceCollectionExtensions.cs` | Options `IndexFeed`, filtro/middleware de API Key. **No** un segundo `JwtBearer` |
| `JoiabagurPV.Application/Configuration/` | `IndexFeedOptions` (`ApiKey`, `ApiKeyPrevious`), validación al arranque (≥ 32 bytes) |
| `JoiabagurPV.Application/DTOs/Ai/` | DTOs de catálogo y POS (`kind`, cursor, `aggregateHash`) |
| `JoiabagurPV.Application/Services/` | `IndexFeedService` (o equivalente) + `PriceBand.From(decimal)` `price-band/v1` |
| `JoiabagurPV.Application/Services/ProductFamilyService.cs` | Tras `ReplaceMembers`, sellar `Product.UpdatedAt` de altas y bajas vía `ExecuteUpdateAsync` |
| `JoiabagurPV.Infrastructure/Data/Repositories/` | Consultas keyset (catálogo y POS). Sin migración |
| `backend/.env.example` · `appsettings*.json` | `IndexFeed:ApiKey` (placeholder local). Producción: SSM en **C17**, no aquí |
| `JoiabagurPV.Tests/` | Unitarios de banda y hash; integración de feeds y 401 (cliente fresco) |
| `openspec/changes/add-dotnet-index-feed-endpoints/` | proposal, **design.md**, specs (`index-feed` nueva; delta `product-family`), tasks |
| `Documentos/epicas.md` (EP14) | Enlazar HU-AIENG-012 |
| `Documentos/Proyecto Final AIEng/informes/c12-catalog-autobulk-runbook.md` | **Nuevo** — *runbook*, no acta de ejecución |
| `Documentos/modelo-de-datos.md` | Mencionar el feed como lector; **no** nueva entidad |
| `ai-service/`, `frontend/`, `openapi.json`, migraciones EF/Alembic | **Sin cambios** |

---

## Especificaciones Técnicas

### Auth: API Key, no JWT de servicio

Header `X-Index-Feed-Key`. Comparación `CryptographicOperations.FixedTimeEquals` (equivalente a `secrets.compare_digest` de S9). Aceptar `ApiKey` o, si está configurada y no vacía, `ApiKeyPrevious`.

El controlador **no** lleva `[Authorize(Roles = ...)]`. Un Bearer de usuario, una cookie `access_token` o un JWT C03 **no** cuentan. Sin key / key mala → **401**.

Fail-fast al arranque si `ApiKey` falta o mide menos de 32 caracteres (mismo umbral que `AiGatewayOptions.MinimumSecretLength`).

Python **no** envía nada en este change. C13 añadirá el header. Los tests .NET lo mandan a mano.

### Catálogo — `GET /api/ai/index-feed/catalog`

Query: `since` (ISO-8601, opcional), `sinceId` (guid, opcional). Ausentes = primera página (sync completo). `pageSize` **no** se acepta del cliente: fijo 50.

`watermark = greatest(Product.UpdatedAt, Profile.UpdatedAt, Family.UpdatedAt)` del producto (familia solo si hay miembro actual).

```
indexable  = Product.IsActive AND Profile.ReviewStatus = Approved
kind       = upsert si indexable; tombstone si el watermark cambió y ya no es indexable
```

Un producto **nunca** aprobado no aparece (ni tombstone). C13 no tiene documento que borrar.

Cuerpo de `upsert` (camelCase): los campos de `ProductSourceText` + `productId`, `familyId` (uuid o null), `price`, `priceBand`, `isActive`, `watermark`. Materiales y tags como arrays JSON, no como el `*Json` persistido. `collectionName` desde `Collection.Name`.

Tombstone: `{ kind, productId, reason: deactivated|unapproved, at }`.

Respuesta de página: `items`, `nextCursor: { since, sinceId } | null`, `hasMore`, `pageSize`, `aggregateHash`.

### POS — `GET /api/ai/index-feed/pos-availability`

Página fija **200**. Feed **disperso**: filas `Inventory` activas como upsert; `IsActive = false` cuyo `LastUpdatedAt`/`UpdatedAt` entra en el cursor → tombstone `{ pointOfSaleId, productId, reason: unassigned, at }`.

`qtyBucket`: `0` si `Quantity <= 0`; `1-2` si 1 o 2; `3+` si ≥ 3. **Prohibido** serializar `quantity`.

`sales30d` / `sales90d`: `SUM(Sale.Quantity)` por `(ProductId, PointOfSaleId)` con `SaleDate` en [now-30d, now] y [now-90d, now]. **Sin** restar devoluciones. `lastSaleAt`: `MAX(SaleDate)` o null.

### `price-band/v1`

Clase pura, sin HTTP ni EF. Cortes cerrados en la HU. Precio &lt; 0 no debería existir (`Product.IsPriceValid`); si llega, fallar ruidoso en tests y tratarlo como `lt-30` o lanzar — default: **lanzar `ArgumentOutOfRangeException`**. Versionar el nombre de la función en un comentario/constante `PriceBandVersion = "price-band/v1"`. Cambiar cortes = v2 = re-sync C13 **sin** reembeber.

### Invalidación de familia

En `ReplaceMembersAsync`, **después** de calcular altas y bajas y **antes** o junto al `SaveChanges` de miembros:

1. Productos que salen: sellar `Product.UpdatedAt`.
2. Productos que entran: igual, por si su `UpdatedAt` de catálogo es antiguo.
3. Cortocircuito idéntico: **cero** escrituras, incluido Product.

El sello es `ExecuteUpdateAsync` (`StampUpdatedAtAsync`): `UpdatedAt` es `ValueGeneratedOnAddOrUpdate`, así que un `UPDATE` del tracker omite la columna. Rename de metadatos: sellar `Family.UpdatedAt`; el feed une por ahí. No amplificar miembros.

### Hash agregado

SHA-256 UTF-8 de los `productId` indexables ordenados, hex minúsculas 64 chars. Calcularlo **una vez por request** sobre el conjunto global (1.200 uuids es barato). POS: analogía sobre pares `(posId, productId)` de filas asignadas activas.

### Informe AutoBulk (entregable de este ticket; la corrida no)

Crear [`Documentos/Proyecto Final AIEng/informes/c12-catalog-autobulk-runbook.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c12-catalog-autobulk-runbook.md) al **final** del apply, cuando los feeds existan y el *runbook* pueda incluir un `GET` de verificación. Es un procedimiento, no un acta: **no** se ejecuta el lote en C12.

El fichero debe contener, como mínimo:

1. **Para qué.** Puerta de C13: sin 1.200 `Approved`, el primer sync deja `ai.product_document` a 0 (fallo mudo de S11).
2. **Fuera de C12.** Quién lo corre: una persona, en local (y más adelante en demo), **después de archivar C12 y antes de aplicar C13**.
3. **Condiciones** (todas obligatorias) y comandos para comprobarlas — PowerShell:

```powershell
# API .NET en http://localhost:5056 ; Postgres publicado en :5433
# 1) Productos ingeridos
docker exec jpv-pv-postgres psql -U postgres -d joiabagur_pv -c "SELECT COUNT(*) FROM public.""Products"";"
# esperar 1200

# 2) Perfiles (antes deben ser 0; después Approved = 1200)
docker exec jpv-pv-postgres psql -U postgres -d joiabagur_pv -c "SELECT ""ReviewStatus"", COUNT(*) FROM public.""ProductAiProfiles"" GROUP BY 1;"

# 3) jbg-ai NO está en stub
docker exec jpv-pv-jbg-ai printenv STUB_MODE
# debe ser false — Compose lo fija a true; recrear el servicio con
# STUB_MODE=false y JPV_RAG_LLM_API_KEY (y JPV_RAG_LLM_MODEL, default openai/gpt-4o)

# 4) Salud
curl -s http://localhost:8001/health
curl -s http://localhost:5056/health   # o el /health que exponga la API
```

4. **Ejecución** (lote 50 = `AiEnrichRequest.MaxBatchSize`; 24 llamadas). Login admin (`admin` / `Admin123!` según `backend/api-tests/README.md`); cookie `access_token`. IDs desde SQL, no desde `GET /api/products` (max 100/página).

```powershell
curl -s -c cookies.txt -X POST http://localhost:5056/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"Admin123!"}'

# $ids = lista de Guid desde psql COPY o un script.
# Trocear de 50 en 50:
curl -s -b cookies.txt -X POST http://localhost:5056/api/ai/catalog/enrich-batch `
  -H "Content-Type: application/json" `
  -d '{"productIds":["..."],"reviewMode":"AutoBulk","force":false}'
```

`force: false` — reejecutar es barato (C08 salta por `SourceHash`). No mezclar con `Routed` (eso es C28).

5. **Verificación posterior al lote** (sigue sin ser C13):

```powershell
docker exec jpv-pv-postgres psql -U postgres -d joiabagur_pv -c "SELECT COUNT(*) FROM public.""ProductAiProfiles"" WHERE ""ReviewStatus"" = 2;"
# ProfileReviewStatus.Approved = 2 (Pending = 1, Rejected = 3). HasConversion<int>().
# Smoke del feed C12 (key de .env.example):
curl -s -H "X-Index-Feed-Key: <IndexFeed:ApiKey>" `
  "http://localhost:5056/api/ai/index-feed/catalog"
```

6. **Tiempo estimado.** C09 extrae **un producto por llamada LLM**, concurrencia 8 (`JPV_RAG_LLM_CONCURRENCY`). 50 productos/lote ≈ 7 oleadas. A ~1–3 s/oleada → ~10–20 s/lote; 24 lotes **secuenciales** (un HTTP .NET espera al batch) → **15–40 min** de reloj. Techo: `EnrichTimeoutMs = 120_000` por lote; si el proveedor se ahoga, acercarse a 24×2 min.

7. **Coste estimado.** Default `openai/gpt-4o`. Prompt `enrichment/v1` + vocabularios ~1,5–2,5 k tokens in; salida JSON ~150–250 out; hasta 1 reintento de parseo. Orden de magnitud **1.200–1.500 completions** → **≈ 6–12 USD** (tarifas gpt-4o ~2,50 USD/1M in y ~10 USD/1M out, agosto 2026; recalcular si el modelo configurado es `gpt-4o-mini`, entonces &lt; 1 USD). Instrumentar coste real en el *runbook* como “estimación a priori”; no hace falta pegar factura.

8. **Qué no hacer.** No correrlo con `STUB_MODE=true` si el objetivo es C14/C24. No marcarlo `ReviewOrigin = Human`. No es un criterio de merge de C12.

---

## Arquitectura

```
SPA ──Jwt:SecretKey──► .NET ──AiGateway:JwtSecret──► jbg-ai   (C03, identidad)
                         ▲
                         │  X-Index-Feed-Key
                         └── feed pull ──────────────────────  (C13 será el cliente)
```

- **§6.3:** pull. Invalidación = watermark. Sync nocturno completo = cinturón de C13, no de este ticket.
- **§6.2:** `price` y `price_band` los calcula .NET. Python no inventa bandas.
- **S9:** API Key en este sentido; JWT donde hay claims de persona/POS.
- **C05:** `data_origin` NOT NULL en `ai.product_document` lo rellena C13, no este JSON.
- **C11:** el feed es **superset** de `ProductSourceText`; C13 mapea y hashea.
- **Breaking:** ninguno sobre contratos ya congelados. Superficie **nueva**. `openapi.json` de Python intacto.

`design.md` es **obligatorio**: auth, cursor, tombstones, tope 200, UpdatedAt vs outbox.

---

## Definición de Hecho (DoD)

- [ ] `GET /api/ai/index-feed/catalog` y `.../pos-availability` autenticados por `X-Index-Feed-Key`
- [ ] Cursor keyset; catálogo ≤ 50; POS ≤ 200; buckets sin cantidad exacta
- [ ] Tombstones `deactivated` / `unapproved` / `unassigned`; hash agregado estable por conjunto
- [ ] `price-band/v1` cubierto por tests unitarios
- [ ] `ReplaceMembers` actualiza `Product.UpdatedAt` de altas y bajas; lista idéntica no escribe
- [ ] JWT de usuario / token C03 / sin key → 401 (cliente fresco)
- [ ] Sin migración EF Core; `Model_HasNoPendingMigrationDifferences` verde
- [ ] Tests nuevos verdes; no “arreglar” rojos preexistentes; comparar **nombres** de fallos
- [ ] *Runbook* AutoBulk escrito en `informes/c12-catalog-autobulk-runbook.md`
- [ ] `Documentos/epicas.md` (EP14) enlaza HU-AIENG-012
- [ ] Specs del change + **`openspec validate --all --strict` con `0 failed`**
- [ ] `design.md` presente
- [ ] `ai-service/openapi.json` intacto; `/v1/index/sync` sigue C13
- [ ] AutoBulk de los 1.200 **no** ejecutado
- [ ] UI: **no aplica**

---

## Requisitos No Funcionales

- **Seguridad:** la API Key no se loguea. Distinta de `Jwt:SecretKey` y de `AiGateway:JwtSecret`. Comparación constant-time. Producción: SSM `/jpv/prod/*` (C17). El feed no se publica como página de operador; nginx ya no expone Python, pero esta ruta **sí** vive en la API pública — la key es la defensa.
- **Rendimiento:** 1.200 productos / 6.720 inventarios. Hash global por request es aceptable. POS 200 reduce round-trips frente a 50 (~34 páginas vs ~135).
- **Observabilidad:** log estructurado de página (`item_count`, `has_more`, `aggregate_hash` truncado, `trace_id` si llega). No dump de descripciones a Information.
- **Integridad:** no emitir stock exacto; no indexar `Pending`; no netear devoluciones aquí (C19 es la autoridad de demanda).

---

## Preguntas Abiertas

Ninguna pendiente de diseño. Cerradas en exploración (2026-08-25), incluida **B — API Key**.

| # | Pregunta | Decisión |
|---|---|---|
| 1 | ¿C12 abre migración? | **No** |
| 2 | ¿HTTP push a Python? | **No** |
| 3 | ¿`data_origin` en el JSON? | **No** |
| 4 | ¿Quién define `price_band`? | **C12**, `price-band/v1`, cortes de la HU |
| 5 | ¿Tope POS? | **200**, no copiable a UI |
| 6 | ¿Auth? | **API Key** `X-Index-Feed-Key` |
| 7 | ¿Ventas netean devoluciones? | **No** |
| 8 | ¿Actor HU? | Desarrollador; AutoBulk fuera, *runbook* dentro |
| 9 | ¿Partir catálogo / POS? | **No**; ambos en este change |
| 10 | ¿`text_provenance`? | **No** |
| 11 | ¿401 o 403 con JWT de usuario? | **401** (desviación explícita de la ficha) |

Default si el apply descubre un detalle menor no listado: la opción más estrecha que no abra migración ni toque Python.

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Alta** (🔴). Nunca se recorta. Desbloquea C13 y C22.
- **Estimación:** **8 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C07 y C08 archivados; C11 archivado (DTO). **Bloquea** C13 (catálogo) y C22 (POS). AutoBulk (ops) bloquea un C13 *útil*, no este código.
- **Línea de corte:** el usuario pidió **no partir**. Si aun así desborda: catálogo + auth primero (desbloquea C13); POS después (C22).
- **Tags:** `HU-AIENG-012`, `C12`, `EP14`, `backend`, `dotnet`, `index-feed`, `api-key`, `tombstone`, `pagination`, `product-family`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-012](../../../../Documentos/Historias/AI-Eng/HU-AIENG-012.md)
- **Change OpenSpec:** `openspec/changes/add-dotnet-index-feed-endpoints/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C12, §0 C07) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.3, §7.2)
- **Apuntes del Máster (guía):** [S9 capa de datos / API Key vs JWT](../../../../Documentos/Sesiones%20Master%20AIEng/S9_Fundamentos_RAG/La%20capa%20de%20datos%20como%20servicio%20-%20Aislar%20y%20Securizar%20el%20Retriever.md) · [S11 reindexación](../../../../Documentos/Sesiones%20Master%20AIEng/S11_RAG_avanzado/Reindexacion%20y%20Versionado%20Embeddings.md)
- **Specs vivas:** `product-family` · `product-ai-profile` · `catalog-source-text` · `ai-vector-schema` · `ai-service-auth` (no se modifica el JWT hacia Python)
- **Precedentes:** `AiCatalogController` · `AiServiceTokenFactory` (solo emisor .NET→Python) · `ProductFamilyService.ReplaceMembersAsync` · `ApplicationDbContext.SaveChangesAsync` (`UpdatedAt`)
- **Contrato Python:** `ai-service/openapi.json` — **no se modifica**
- **Runbook (a crear en apply):** `Documentos/Proyecto Final AIEng/informes/c12-catalog-autobulk-runbook.md`
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-25 | `/enrich-us` | Creación a partir de HU-AIENG-012 y de la exploración. Recoge: pull sin push, sin migración, API Key, `price-band/v1`, POS 200, tombstones por `kind`/`reason`, UpdatedAt de altas/bajas, `data_origin`/`text_provenance` fuera, *runbook* AutoBulk como entregable y la corrida fuera |
| 2026-08-25 | `/opsx:verify` follow-up | Sello de familia documentado como `ExecuteUpdateAsync` (`UpdatedAt` es `ValueGeneratedOnAddOrUpdate`; el tracker omite la columna) |
