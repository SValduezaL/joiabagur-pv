## Why

C07, C12 y C13 dejaron el camino de familias completo de punta a punta —entidad con pertenencia excluyente, cinco endpoints de administración, emisión de `familyId` en el feed, mapeo en el indexador, columna `family_id` indexada en `ai.product_document`, y los campos de familia en el contrato de recuperación desde C02— **y no hay una sola fila**: 1.200 productos, 1.200 documentos con embedding, **0 familias y 0 documentos con `family_id`**. Agrupar a mano las ~155 familias del catálogo es inviable, que es exactamente el motivo por el que la decisión abierta 4 de las especificaciones v2 quedó sin resolver y el §7.5 del diseño propuso un flujo mixto.

Se hace ahora, y no más tarde, por una razón de orden que no es de conveniencia: llenar `Familia:` y `Variante:` en el documento canónico cambia `doc_text`, `source_hash` y el vector de **~358 documentos, el 30 % del corpus**, y `embedding_version` **no lo distinguirá** —es `modelo:dims:preprocessing_id`, y este change altera contenido, no preprocesado—. Cualquier medición tomada antes (C20, C21, C24) describiría un corpus que este change sustituye por debajo, sin que nada lo señale.

## What Changes

- **Motor de agrupación determinista** en `ai-service/src/jbg_ai/families/`, sin LLM y sin red: normalización de raíz, agrupación por raíz tras retirar el token de talla —esté donde esté en el nombre—, **fusión** de grupos que difieren en un material, puerta de `piece_type`, guarda de raíz degenerada, y **veto relativo por embedding** —nunca por umbral absoluto— que marca para revisión en lugar de eliminar.
- **BREAKING** — **`POST /v1/families/suggest`**: novena ruta de la superficie `/v1`, hasta ahora congelada en ocho. `ai-service/openapi.json` regenerado con la orden canónica del README, y `test_snapshot_covers_the_frozen_surface` actualizado con la ruta nueva. **Hecho el 2026-08-31**: el test de deriva se comprobó en rojo *antes* de regenerar, que es la señal de que la frontera se movió de verdad, y en verde después. Es una ruta **de catálogo**, no de punto de venta: usa `get_catalog_principal` y responde `TracedResponse` sin `effective_pos_id`, como las rutas de índice de C13.
- **`IAiGatewayClient.SuggestFamiliesAsync`**: cuarta operación del cliente .NET, junto a `SearchAsync`, `EnrichAsync` y `HealthAsync`.
- **`POST /api/ai/catalog/family-suggestions`** y **`/apply`** en `AiCatalogController`, sólo administradores: el primero devuelve propuestas **sin escribir nada**, el segundo persiste el subconjunto que el llamante acepta. **Sin persistencia de propuestas**: no hay tabla nueva ni estado intermedio.
- **Escritura vía `ProductFamilyService`**, nunca por SQL directo, con `Origin = AiApproved`, `ApprovedByUserId` y `ApprovedAt` — **primera escritura de las tres columnas que C07 reservó y dejó sin ejercer**.
- **Reconciliación del índice por sincronización incremental**, nunca `--full`.
- **Sin migración de EF Core ni de Alembic.** El turno único de migración queda libre para C19.

## Capabilities

### New Capabilities

- `family-suggestion`: agrupación asistida de productos en familias de variantes y su aprobación por lotes — el algoritmo determinista y sus guardas, la ruta de propuesta en `jbg-ai`, los endpoints de administración en .NET que separan proponer de aplicar, y la regla de que la propuesta no escribe y el aplicar es la única vía de escritura.

### Modified Capabilities

- `ai-service-api-contracts`: la superficie `/v1` congelada pasa de ocho rutas a nueve; el snapshot de OpenAPI se regenera y su test de deriva vuelve a verde contra el nuevo contrato.
- `ai-gateway-client`: el cliente gana la operación de sugerencia de familias, con su traducción de `501` y de indisponibilidad a los errores tipados que el controlador ya distingue.
- `product-family`: se añade el camino de escritura de aprobación asistida. La spec viva de C07 especifica el **almacenamiento** del origen y sus scenarios sólo cubren la creación manual; nada describe todavía cómo se registra una familia aprobada desde una sugerencia.

## Impact

- **`ai-service/`** — paquete nuevo `src/jbg_ai/families/`, router `api/routers/families.py`, esquemas `api/schemas/families.py`, entrada en `stubs/`, un ajuste de `pydantic-settings` (el margen del veto), snapshot `openapi.json`, árbol de tests `tests/families/`.
- **`backend/`** — `Application`: operación e interfaces del gateway, DTOs y validadores; `Infrastructure`: implementación en `AiGatewayClient`; `API`: dos acciones en `AiCatalogController`; `Tests`: unitarios de servicio e integración de los dos endpoints.
- **Datos** — se crean ~155 `ProductFamily` y ~450 `ProductFamilyMember`. **Ninguna columna nueva.** El estampado de `Product.UpdatedAt` que hace `ProductFamilyService` es lo que permite al feed incremental ver el cambio; escribir por SQL lo rompería en silencio.
- **Corpus** — ~358 documentos cambian `doc_text`, `source_hash`, `tsv` y embedding. `source-text/v1` y `embedding_version` **no** cambian, y esa es precisamente la razón por la que este change debe preceder a C20, C21 y C24.
- **Sistemas aguas abajo** — dejan de ser vacuos `test_ambiguous_variant_penalty_applies_only_within_family` (C25), `test_same_family_variant_ranks_first_when_available` (C26), `test_variants_grouped_by_family_id` (C30) y `should require variant confirmation when family has multiple members` (C36). Los dos últimos pertenecen a changes que el §6 del plan declara irrecortables.
- **No se toca** — `frontend/` (la pantalla de revisión y la alerta de huérfanos son C18b), `terraform/`, `.github/workflows/`, `indexing/embeddings.py`, `source-text/v1`, y el esquema `public` por SQL desde Python.
- **Documentación** — [HU-AIENG-018a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-018a.md) y [ticket](./ticket.md) ya escritos; quedan `Documentos/epicas.md` (EP13), la reestructuración del plan de changes al orden **C18a → C19 → C18b**, y el informe del lote.
