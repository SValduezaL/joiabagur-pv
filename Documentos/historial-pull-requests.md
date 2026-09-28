# Historial de pull requests

Este proyecto se desarrolló en [`skydr4g0n-it/joiabagur-pv`](https://github.com/skydr4g0n-it/joiabagur-pv),
donde se revisó e integró cada cambio mediante pull requests. Al trasladar el repositorio a
[`SValduezaL/joiabagur-pv`](https://github.com/SValduezaL/joiabagur-pv) el historial de commits viaja
completo, pero las páginas de las PR no se pueden copiar. Este documento conserva su contenido:
número, título, autor, ramas, fechas, descripción y comentarios, con el enlace a la PR original.

**Total:** 54 pull requests.

| # | Título | Estado | Ramas | Integrada |
|---|---|---|---|---|
| [#1](#pr-1) | Entrega 1: Documentación del proyecto y estructura inicial del frontend | MERGED | `feature-entrega1-MO` → `master` | 2026-01-17 |
| [#2](#pr-2) | Feature-entrega3-MO | MERGED | `feature-entrega3-MO` → `master` | 2026-02-04 |
| [#3](#pr-3) | Feature entrega3 mo | MERGED | `feature-entrega3-MO` → `master` | 2026-02-05 |
| [#4](#pr-4) | docs: diseño del sistema de IA (RAG) para el Proyecto Final — v3, consenso tras revisión | MERGED | `docs/proyecto-final-ia` → `master` | 2026-08-03 |
| [#5](#pr-5) | C01: init ai-service skeleton (jbg-ai) | MERGED | `c01-init-ai-service-skeleton` → `ai-eng` | 2026-08-03 |
| [#6](#pr-6) | feat(ai-service): congelar contratos /v1 y auth interna de jbg-ai | MERGED | `c02-add-ai-service-contracts-and-auth` → `ai-eng` | 2026-08-06 |
| [#7](#pr-7) | feat(backend): añade cliente tipado hacia jbg-ai con resiliencia (C03) | MERGED | `c03-add-dotnet-ai-gateway-client` → `ai-eng` | 2026-08-09 |
| [#8](#pr-8) | feat(telemetry): registrar el ciclo consulta→selección (C04) | MERGED | `c04-add-product-search-event-tracking` → `ai-eng` | 2026-08-11 |
| [#9](#pr-9) | feat(ai-service): esquema ai con pgvector, migraciones Alembic y pool acotado (C05) | MERGED | `c05-add-pgvector-schema-foundation` → `ai-eng` | 2026-08-15 |
| [#10](#pr-10) | feat(ai): perfil IA revisable del catálogo con revisión híbrida por campo (C08) | MERGED | `c08-add-product-ai-profile-entity` → `ai-eng` | 2026-08-16 |
| [#11](#pr-11) | feat(backend): familias de producto como entidad de negocio editable (C07) | MERGED | `c07-add-product-family-entity` → `ai-eng` | 2026-08-16 |
| [#12](#pr-12) | feat(catalog): corpus real enriquecido y pipeline offline C06a | MERGED | `feature/add-real-catalog-ingestion-and-text-assist` → `ai-eng` | 2026-08-22 |
| [#13](#pr-13) | feat(ai-service): añadir CLI y corpus sintético C06b | MERGED | `feature/add-synthetic-catalog-augmentation` → `ai-eng` | 2026-08-23 |
| [#14](#pr-14) | feat(ai-service): extraer perfiles reales en POST /v1/enrich/products | MERGED | `c09-add-catalog-enrichment-pipeline` → `ai-eng` | 2026-08-23 |
| [#15](#pr-15) | feat(ai-service): añadir CLI world simulate/ingest (C10) | MERGED | `c10-add-synthetic-world-simulator` → `ai-eng` | 2026-08-23 |
| [#16](#pr-16) | feat(ai-service): añadir source-text/v1 y cliente de embeddings 1536d | MERGED | `c11-add-source-text-and-embedding-client` → `ai-eng` | 2026-08-25 |
| [#17](#pr-17) | feat(api): añadir feeds HTTP de indexación con cursor y API Key | MERGED | `c12-add-dotnet-index-feed-endpoints` → `ai-eng` | 2026-08-25 |
| [#18](#pr-18) | feat(ai-service): drenar el feed de catálogo hacia ai.product_document | MERGED | `c13-add-product-document-indexer` → `ai-eng` | 2026-08-26 |
| [#19](#pr-19) | feat(ai-service): implementar retriever vectorial de products | MERGED | `c14-add-vector-retrieval-endpoint` → `ai-eng` | 2026-08-27 |
| [#20](#pr-20) | feat(backend): POST /api/ai/search con hidratación autoritativa y degradación (C15) | MERGED | `c15-add-dotnet-ai-search-endpoint` → `ai-eng` | 2026-08-28 |
| [#21](#pr-21) | feat(frontend): panel de búsqueda asistida y atribución de la venta (C16) | MERGED | `c16-add-frontend-assisted-search-panel` → `ai-eng` | 2026-08-29 |
| [#22](#pr-22) | feat(infra): entorno de demostración aislado para el servicio de IA | MERGED | `c17-add-ai-service-deployment` → `ai-eng` | 2026-08-30 |
| [#23](#pr-23) | feat(ai-service): agrupacion asistida de familias de producto y su aprobacion por lote | MERGED | `c18a-add-family-suggestion-and-approval` → `ai-eng` | 2026-08-31 |
| [#24](#pr-24) | feat(ai): revisión humana de familias y alerta de huérfanos — décima ruta del contrato (C18b) | MERGED | `c18b-add-family-review-ui-and-orphan-alert` → `ai-eng` | 2026-09-01 |
| [#25](#pr-25) | feat(ai-service): expansión de consulta con diccionario de sinónimos (C20) | MERGED | `c20-add-synonym-dictionary` → `ai-eng` | 2026-09-01 |
| [#26](#pr-26) | feat(ai-service): fusionar rama léxica y vectorial con RRF ponderado | MERGED | `c21-add-hybrid-search-rrf` → `ai-eng` | 2026-09-02 |
| [#27](#pr-27) | C22: sincroniza ai.pos_projection y acota la recuperación al surtido del punto de venta | MERGED | `c22-add-pos-projection-soft-prefilter` → `ai-eng` | 2026-09-05 |
| [#28](#pr-28) | fix(ai-service): cerrar las lagunas de piece_type con enrichment/v2 | MERGED | `fix1-enrichment-vocabulary-gaps` → `ai-eng` | 2026-09-05 |
| [#29](#pr-29) | feat(ai-service): añadir el corpus de conocimiento y su índice de citas | MERGED | `c23-knowledge-corpus-and-indexer` → `ai-eng` | 2026-09-06 |
| [#30](#pr-30) | feat(ai-service): añadir arnés de evaluación, golden set y líneas base | MERGED | `c24-eval-harness-golden-set-and-baselines` → `ai-eng` | 2026-09-11 |
| [#31](#pr-31) | C25: la fusion hibrida se compone en dos etapas, y el buscador aprende a callar | MERGED | `c25-recalibrate-ranking-and-abstention` → `ai-eng` | 2026-09-12 |
| [#32](#pr-32) | Retira la fusión plana y los pesos por lista: 315 filas idénticas (C25bis) | MERGED | `c25bis-clean-plain-fusion` → `ai-eng` | 2026-09-12 |
| [#33](#pr-33) | feat(ai-service): implementar sustitutos sobre el embedding almacenado | MERGED | `c26-add-substitutes-retrieval` → `ai-eng` | 2026-09-12 |
| [#34](#pr-34) | feat(profile-review): revisión humana de perfiles y sus métricas | MERGED | `c28-add-profile-review-ui-and-metrics` → `ai-eng` | 2026-09-13 |
| [#35](#pr-35) | feat(ai-service): servir la capa estructurada de venta asistida (C30a) | MERGED | `c30a-add-assist-structure-and-rule-warnings` → `ai-eng` | 2026-09-13 |
| [#36](#pr-36) | feat(ai-service): generar el argumentario de venta con tres puertas (C30b) | MERGED | `c30b-add-assist-pitch-generation` → `ai-eng` | 2026-09-14 |
| [#37](#pr-37) | feat(ai-service)!: clasificar la consulta antes de recuperar nada (C31) | MERGED | `c31-add-guardrails-and-intent-router` → `ai-eng` | 2026-09-16 |
| [#38](#pr-38) | feat(ai-service): registrar seis tools de solo lectura del agente (C32a) | MERGED | `c32a-add-sales-assistant-tool-registry` → `ai-eng` | 2026-09-20 |
| [#39](#pr-39) | feat(ai-service): añadir el bucle agéntico del asistente de venta | MERGED | `c32b-add-sales-assistant-agent-loop` → `ai-eng` | 2026-09-21 |
| [#40](#pr-40) | feat(backend): rutas .NET del card de venta con hidratación y marcadores | MERGED | `c34-add-dotnet-assist-and-recommendation-endpoints` → `ai-eng` | 2026-09-22 |
| [#41](#pr-41) | feat(frontend): añadir la ficha de venta con desambiguación por familia | MERGED | `c36-add-frontend-assist-card-and-family-disambiguation` → `ai-eng` | 2026-09-24 |
| [#42](#pr-42) | feat(ai-search): dar pantalla y ruta propia a la consulta libre | MERGED | `c40-add-frontend-free-query-panel` → `ai-eng` | 2026-09-25 |
| [#43](#pr-43) | fix(sales): hacer alcanzable el ambito de todas las tiendas | MERGED | `c40-fix-all-shops-scope-unreachable` → `ai-eng` | 2026-09-26 |
| [#44](#pr-44) | C41: la proyeccion de disponibilidad se drena sola al arrancar y cada 600 s | MERGED | `c41-add-pos-projection-scheduled-drain` → `ai-eng` | 2026-09-26 |
| [#45](#pr-45) | feat(sales): dar pantalla al agente de venta y su consumidor .NET | MERGED | `c42-add-frontend-agent-panel` → `ai-eng` | 2026-09-26 |
| [#46](#pr-46) | feat(demo): preparar el redespliegue del entorno de demostración y auditar su configuración | MERGED | `c39a-redeploy-and-audit-demo-environment` → `ai-eng` | 2026-09-27 |
| [#47](#pr-47) | release(demo): desplegar C36, C40, C40_FIX, C41, C42 y C39a — las cuatro superficies de IA al entorno de demostración | MERGED | `ai-eng` → `demo` | 2026-09-27 |
| [#48](#pr-48) | docs(demo): verificar el entorno desplegado y declarar sus cuentas | MERGED | `c39abis-verify-demo-redeployment` → `ai-eng` | 2026-09-27 |
| [#49](#pr-49) | C43 · La verificación del despliegue deja de juzgar mal un entorno correcto | MERGED | `c43-add-shop-activity-projection` → `ai-eng` | 2026-09-27 |
| [#50](#pr-50) | Pone la demo al día: C39a-bis y C43 — el despliegue deja de fallar por un entorno sano | MERGED | `ai-eng` → `demo` | 2026-09-27 |
| [#51](#pr-51) | Arregla el drenaje de arranque: reintenta por drenaje, no por pasada | MERGED | `c43-fix-boot-drain-retries-both-drains` → `ai-eng` | 2026-09-27 |
| [#52](#pr-52) | Arregla el drenaje de arranque que dejó ai.pos_shop vacía en el despliegue anterior | MERGED | `ai-eng` → `demo` | 2026-09-27 |
| [#53](#pr-53) | Cierra el Proyecto Final: entregable, criterio de recuento y evidencias (C39b) | MERGED | `c39b-finalize-pf-readme-and-evidence` → `ai-eng` | 2026-09-27 |
| [#54](#pr-54) | Pone demo al día con ai-eng: cierre del Proyecto Final (C39b) | MERGED | `ai-eng` → `demo` | 2026-09-27 |

---

<a id="pr-1"></a>
## #1 — Entrega 1: Documentación del proyecto y estructura inicial del frontend

| | |
|---|---|
| Autor | `marcello-clearcust` |
| Estado | MERGED |
| Ramas | `feature-entrega1-MO` → `master` |
| Creada | 2025-12-07 |
| Integrada | 2026-01-17 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/1 |

### Descripción

## Resumen

Esta PR incluye la documentación completa del proyecto y la estructura inicial del frontend basada en Metronic template.

## Cambios principales

### Documentación
- ✅ README.md con descripción general del proyecto e índice de documentación
- ✅ Arquitectura del sistema (arquitectura.md)
- ✅ Modelo de datos completo (modelo-de-datos.md)
- ✅ Modelo C4 del sistema (modelo-c4.md)
- ✅ Épicas del MVP con historias de usuario (epicas.md)
- ✅ 40+ historias de usuario detalladas (HU-EP1-001 a HU-EP9-004)
- ✅ Procedimientos de trabajo (User Stories y Tickets)
- ✅ Propuestas técnicas (análisis Metronic, arquitecturas, aclaraciones técnicas)
- ✅ Prompts para desarrollo asistido (prompts.md)

### Frontend
- ✅ Estructura inicial del frontend con Metronic
- ✅ Layout principal (layout-1) con componentes base
- ✅ Componentes compartidos (dialogs, dropdowns, mega-menu, navbar, topbar)
- ✅ Configuración de App.tsx

### Configuración
- ✅ .gitignore actualizado

## Próximos pasos
- Creación de tickets de trabajo
- Implementación de backend/frontend según arquitectura definida
- Desarrollo de funcionalidades según tickets de trabajo
- Integración frontend-backend

<!-- CURSOR_SUMMARY -->
---

> [!NOTE]
> Bootstraps a full Metronic-based frontend: adds multiple layouts (7–39), a comprehensive UI component library, routing, hooks/utils, configs, styles, and example pages.
> 
> - **Frontend scaffold**
>   - Adds app entry (`main.tsx`), global styles, helpers (`lib/*`), hooks (`hooks/*`), and screen loader.
> - **Layouts (new)**
>   - Implements layouts `layout-7` to `layout-39` with headers, toolbars, sidebars, mega-menus, and shared elements.
> - **UI Library (new)**
>   - Introduces comprehensive UI primitives (accordion, alert, avatar, badge, button, calendar, card, carousel, chart, checkbox, dialog, drawer, dropdown, form, input, select, table, tabs, tooltip, etc.).
> - **Configuration**
>   - Adds menu/config files for layouts (`config/layout-*.config.tsx`) and shared `types.ts`.
> - **Pages & Routing**
>   - Creates example pages for each layout (`pages/layout-*/page.tsx`).
>   - Wires routes in `routing/app-routing-setup.tsx` and loader in `routing/app-routing.tsx`.
> - **Styles**
>   - Adds component/demo styles (apexcharts, rating, scrollable, leaflet, image-input) and theme variables.
> 
> <sup>Written by [Cursor Bugbot](https://cursor.com/dashboard?tab=bugbot) for commit 593755cd5994da2411a26046751cd8b4fc145d84. This will update automatically on new commits. Configure [here](https://cursor.com/dashboard?tab=bugbot).</sup>
<!-- /CURSOR_SUMMARY -->

### Comentarios y revisiones

**cursor** · revisión COMMENTED · 2025-12-08

### This PR is being reviewed by Cursor Bugbot

<details>
<summary>Details</summary>

Your team is on the Bugbot Free tier. On this plan, Bugbot will review limited PRs each billing cycle for each member of your team.

To receive Bugbot reviews on all of your PRs, visit the [Cursor dashboard](https://www.cursor.com/dashboard?tab=bugbot) to activate Pro and start your 14-day free trial.
</details>




---

<a id="pr-2"></a>
## #2 — Feature-entrega3-MO

| | |
|---|---|
| Autor | `marcello-clearcust` |
| Estado | MERGED |
| Ramas | `feature-entrega3-MO` → `master` |
| Creada | 2026-02-04 |
| Integrada | 2026-02-04 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/2 |

### Descripción

## **User description**

<!-- CURSOR_SUMMARY -->
---

> [!NOTE]
> **High Risk**
> Introduces new persisted entities/migrations and transaction-backed stock/movement updates for returns, so bugs could impact inventory correctness and reporting. Adds new authorization and file-handling paths (photo upload/streaming) that need careful validation and access control.
> 
> **Overview**
> Adds full **returns management** backend support, including `POST /api/returns` to register a return linked to one or more original sales (partial/multi-sale), with mandatory `ReturnCategory`, optional reason, optional photo compression/storage, and automatic stock increment via an `InventoryMovement` of type `Return`.
> 
> Introduces `GET /api/returns/eligible-sales` (last-30-days window + remaining returnable quantity), `GET /api/returns` history with filtering/pagination and operator POS scoping, `GET /api/returns/{id}` details (including associated sale breakdown + total value), and `GET /api/returns/{id}/photo/file` for streaming the attached photo with access checks.
> 
> Extends inventory with admin-only `GET /api/inventory/search` and adds `IInventoryService.SearchInventoryAsync` plus `CreateReturnMovementAsync`. Adds new domain model (`Return`, `ReturnSale`, `ReturnPhoto`, `ReturnCategory`), EF Core DbSets/configurations/migration, service/validator wiring, API test REST client file `returns.http`, and updates docs/user stories to reflect the new multi-sale return rules (30-day limit, POS match, quantity constraints, operator restrictions).
> 
> <sup>Written by [Cursor Bugbot](https://cursor.com/dashboard?tab=bugbot) for commit a41e2214ea5f3fa45b183773957fe915cfed7572. This will update automatically on new commits. Configure [here](https://cursor.com/dashboard?tab=bugbot).</sup>
<!-- /CURSOR_SUMMARY -->


___

## **CodeAnt-AI Description**
Add returns management UI and backend: register returns, view history, and inventory search

### What Changed
- New "Nueva Devolución" flow: form to select point of sale, search product, pick eligible sale(s) from last 30 days (with available quantity), attach photo, choose return category/reason, and register the return which updates stock and shows the new stock quantity.
- New "Historial de Devoluciones" page: paginated list with date and POS filters, per-return details including associated sales and a dialog to view attached photos.
- Routing and menu updated so returns appear in the app navigation with dedicated routes for listing, creating, and history.
- Inventory adjustment UI now supports POS-scoped autocomplete search (debounced) and prevents adjustments that would produce negative stock; selected inventory is updated in-place after adjustment.
- Point-of-sale form: added editable "active" toggle in edit mode and made the POS code immutable after creation.
- Backend additions: database migration and service/controller interfaces and implementations to persist returns, return-items, photos, and inventory movements; endpoints for creating returns, fetching eligible sales, history, and streaming return photos.
- Tests and test helpers updated to use shared test data generators and include unit/integration coverage for the new returns functionality.

### Impact
`✅ Shorter return registration`
`✅ Clearer return history with photos and sale associations`
`✅ Fewer manual inventory lookups due to POS-scoped autocomplete`
<details>
<summary><strong>💡 Usage Guide</strong></summary>

### Checking Your Pull Request
Every time you make a pull request, our system automatically looks through it. We check for security issues, mistakes in how you're setting up your infrastructure, and common code problems. We do this to make sure your changes are solid and won't cause any trouble later.

### Talking to CodeAnt AI
Got a question or need a hand with something in your pull request? You can easily get in touch with CodeAnt AI right here. Just type the following in a comment on your pull request, and replace "Your question here" with whatever you want to ask:
<pre>
<code>@codeant-ai ask: Your question here</code>
</pre>
This lets you have a chat with CodeAnt AI about your pull request, making it easier to understand and improve your code.

#### Example
<pre>
<code>@codeant-ai ask: Can you suggest a safer alternative to storing this secret?</code>
</pre>

### Preserve Org Learnings with CodeAnt
You can record team preferences so CodeAnt AI applies them in future reviews. Reply directly to the specific CodeAnt AI suggestion (in the same thread) and replace "Your feedback here" with your input:
<pre>
<code>@codeant-ai: Your feedback here</code>
</pre>
This helps CodeAnt AI learn and adapt to your team's coding style and standards.

#### Example
<pre>
<code>@codeant-ai: Do not flag unused imports.</code>
</pre>

### Retrigger review
Ask CodeAnt AI to review the PR again, by typing:
<pre>
<code>@codeant-ai: review</code>
</pre>

### Check Your Repository Health
To analyze the health of your code repository, visit our dashboard at [https://app.codeant.ai](https://app.codeant.ai). This tool helps you identify potential issues and areas for improvement in your codebase, ensuring your repository maintains high standards of code health.

</details>


### Comentarios y revisiones

**codeant-ai** · 2026-02-04

CodeAnt AI is reviewing your PR.

---

### Thanks for using CodeAnt! 🎉

We're free for open-source projects. if you're enjoying it, help us grow by sharing.

[Share on X](https://twitter.com/intent/tweet?text=Just%20tried%20%40CodeAntAI%20for%20automated%20code%20review%20and%20I%27m%20impressed%21%20Free%20for%20open%20source%20with%20a%20free%20trial%20for%20private%20repos.%20Worth%20checking%20out%3A&url=https%3A//codeant.ai) ·
[Reddit](https://www.reddit.com/submit?title=Check%20out%20CodeAnt%20for%20automated%20code%20review&text=Just%20tried%20CodeAnt%20for%20automated%20code%20review%20and%20I%27m%20impressed%21%20Free%20for%20open%20source%20with%20a%20free%20trial%20for%20private%20repos.%20Worth%20checking%20out%3A%20https%3A//codeant.ai) ·
[LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fcodeant.ai&mini=true&title=Check%20out%20CodeAnt%20for%20automated%20code%20review&summary=Just%20tried%20CodeAnt%20for%20automated%20code%20review%20and%20I%27m%20impressed%21%20Free%20for%20open%20source%20with%20a%20free%20trial%20for%20private%20repos)


**codeant-ai** · 2026-02-04

## Nitpicks 🔍

<table>
<tr><td>🔒&nbsp;<strong>No security issues identified</strong></td></tr>
<tr><td>⚡&nbsp;<strong>Recommended areas for review</strong><br><br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-db56a491c95926833c5110eb28d52af56ef7f61cb4ff798d17bb04f37e90c680R94-R96'><strong>Authorization boundary relies on service</strong></a><br>Several endpoints (CreateReturn, GetEligibleSales, GetReturnsHistory) rely on the called service to enforce POS/role scoping (the controller forwards _currentUserService.IsAdmin). Ensure the service enforces POS ownership checks and that the controller doesn't inadvertently allow operators to affect/see other POS data.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-dd2b29d1636022c0217d6cf56c0bc370f70fb0d9b872a5d25b4c4c3d91e0b269R16-R29'><strong>Authorization model surface</strong></a><br>The API surface relies on a boolean `isAdmin` and explicit `userId` for authorization decisions. Ensure the implementation consistently validates POS-scoped access for operators and that passing `isAdmin` cannot be spoofed by higher layers. Consider using a claims/principal abstraction in service implementations or centralizing permission checks.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-db56a491c95926833c5110eb28d52af56ef7f61cb4ff798d17bb04f37e90c680R65-R92'><strong>Large image payload / DoS risk</strong></a><br>The controller decodes and processes Base64 image payloads directly in-memory (Convert.FromBase64String + CompressImageAsync). An attacker can send very large Base64 strings causing high memory usage, long GC pauses or OOM. Request size should be validated (before decoding) and limits enforced.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-d09eefc178c1f45d90a973b13c4e683b63aa825d35421215fce3a48735735380R47-R52'><strong>Photo size/format risk</strong></a><br>`PhotoBase64` accepts arbitrary base64 content. Without size or format checks this can be used to send very large payloads, causing memory/DoS risks when decoding or storing. `PhotoFileName` may also need sanitization before filesystem/storage use.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-32bc50c25fae8bb2f453c7aa2e34163de2a40d3a15df733112ddec01ebe15560R36-R45'><strong>Large payloads / upload flow</strong></a><br>`CreateReturnRequest` allows `photoBase64` (base64-encoded image) and `photoFileName`, which can produce very large request bodies and cause performance or DoS problems. Prefer a multipart/form-data upload or a separate upload endpoint that returns an asset id to reference in the create request.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-14984031986a22ebca3748ec69fc9612ea0ceaa1eb311c17486ce5aaf1c67645R105-R109'><strong>Unique index risk</strong></a><br>A unique index is created on InventoryMovements.ReturnId. If existing non-null InventoryMovements rows contain duplicate ReturnId values this migration will fail. Verify existing data or change index strategy (non-unique or filtered) to avoid runtime migration errors.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-ec1b5661807194c5a455a9d2d808a91f5b50d864b954dcad50adf01298794ad6R612-R700'><strong>Concurrency / data integrity</strong></a><br>CreateReturnMovementAsync updates inventory.Quantity without any optimistic concurrency checks (row version) or explicit locking. Concurrent sales/returns could cause lost updates and incorrect stock. Consider optimistic concurrency or database-level increment to ensure correctness.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-a10a5305078c8730f6aa1dc1404424b6727d4cb5679f84e92ae6acefe5e6eb5fR260-R275'><strong>Transactional Consistency</strong></a><br>The inventory movement created by _inventoryService.CreateReturnMovementAsync is executed after DB changes are saved but may not participate in the same unit-of-work/DB transaction. If the inventory service updates external systems or its own DB context separately, failures or partial successes could leave database state and inventory out of sync.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-794f3c91b5f634a30fce49274d3731e1f4016024de7cc7b9d5b3e77a6854f599R159-R167'><strong>Unique index on InventoryMovement</strong></a><br>The migration creates unique indexes on `InventoryMovements.ReturnId` and `InventoryMovements.SaleId`. If your domain allows multiple inventory movements related to the same sale or return (for partial refunds, corrections, or additional adjustments), the uniqueness constraint will prevent that and can cause runtime exceptions or data loss. Verify the intended cardinality and adjust the index/constraints accordingly.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-80c76d5d55b78cb7d2fc8e9dd41dd969bc9b856ec5e9739fd921f29d34016082R160-R161'><strong>Unique FK constraint</strong></a><br>An index marking InventoryMovement.ReturnId as unique (one-to-one) was added. Confirm the business rule: do you intend each Return to map to at most one InventoryMovement? If multiple inventory movements per return are ever needed (e.g., multi-step adjustments), this uniqueness will block them.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-533f9cb52892fe173105f97286e5d43e24b07ecd2392fa8136223293332f1039R35-R35'><strong>Test Database Reset</strong></a><br>The explicit call that previously ensured product tables were cleared was removed and replaced by a comment claiming Respawn handles cleanup. Confirm that _factory.ResetDatabaseAsync() resets all product-related tables (Products, Collections, ProductPhotos, imports, etc.). If Respawn isn't configured for those tables, tests may become flaky or leak state between runs.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-533f9cb52892fe173105f97286e5d43e24b07ecd2392fa8136223293332f1039R38-R39'><strong>Unchecked user creation</strong></a><br>The setup creates an operator user via a POST but does not verify the response. If user creation fails (validation, duplicate, seed issues), subsequent authentication and many tests will fail and produce confusing errors. Ensure the creation response is validated and the setup aborts on failure.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-4e878a9f96e411085976bf479c45746085cc9c6677fbaa8080656756add0706cR110-R119'><strong>Fragile cookie parsing</strong></a><br>`CreateAuthenticatedClientAsync` directly reads "Set-Cookie" headers, splits and looks for a cookie named exactly "access_token" and adds a separate `Cookie` header per found cookie. This parsing is brittle (assumes header present, exact cookie name/casing, no URL encoding) and may produce multiple Cookie headers instead of a single combined header or properly using a CookieContainer. Failures here will cause all subsequent authenticated requests to fail.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-ebceb858c61ac287da1e4a9f8ebcdc32a62ccc0835640ac15f9ffe30be5e8554R113-R132'><strong>Cookie handling</strong></a><br>CreateAuthenticatedClientAsync reads Set-Cookie values and adds a separate "Cookie" header per cookie. Multiple Cookie headers may be non-standard; cookies should be combined into a single Cookie header string. Also the code assumes Set-Cookie is always present and will throw if the header is missing.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-e55c3bbbd558f43024361ea2112d8e2a05b102e0f58a394c5cc04a67bcbd207cR131-R150'><strong>Fragile auth cookie handling</strong></a><br>The test login flow parses Set-Cookie headers manually and adds multiple "Cookie" request headers on a per-cookie basis. This is brittle (missing headers will throw, cookies should be combined or managed by a CookieContainer), may produce invalid cookie headers, and can break if the authentication cookie format changes. Replace manual parsing with a robust cookie container / handler approach or at least validate header presence and combine cookies into a single header.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-28530045b639c622f9a36372a911a2060eadd838c3a2ec256d39cc3d325a12fbR17-R18'><strong>Credentials in repo</strong></a><br>The script contains a hard-coded admin username/password which exposes sensitive credentials and makes tests brittle. Replace with environment variables or secret management and avoid committing real credentials.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-a04af61f1af96df5afd5b06fc37886e7b64362145d8789b30a3d050c50d48bbcR56-R132'><strong>Missing success/transaction test</strong></a><br>There are only negative/validation unit tests for CreateReturnAsync. The critical transactional path (successful return creation) that should assert repository saves, inventory movement invocation and unit-of-work commit is not covered. This is important because the new feature increments inventory and persists multiple entities in a single transaction.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-a04af61f1af96df5afd5b06fc37886e7b64362145d8789b30a3d050c50d48bbcR27-R54'><strong>Interaction assertions absent</strong></a><br>The tests do not verify that the service interacts with collaborators: e.g., _inventoryService to create the return movement, _returnRepository/_returnSaleRepository to persist entities, or _unitOfWork to commit. Without these verifies, regressions where side effects are not executed may go unnoticed.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-95b8dd7d8193585ba1b40138dbbea7c07e0037884a2cb11c5cff1f1fd2047f2cR1-R279'><strong>Bundled dependency committed</strong></a><br>A large, compiled vendor file (React DOM development build) was added to the repository. Committing build artifacts inside source control bloats the repo, causes merge friction, and can lead to stale/incorrect artifacts being used in CI or deployments.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-95b8dd7d8193585ba1b40138dbbea7c07e0037884a2cb11c5cff1f1fd2047f2cR1-R279'><strong>Development build shipped</strong></a><br>The file contains the React DOM development build (notice lots of console errors/warnings and unminified code). Development builds should not be used in production — they are larger and include extra runtime checks and console messages.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-70a435593851148cd8073c864c7f1ed2ec5cba65dd5204da9e4c5122537464acR998-R1014'><strong>Duplicate React risk</strong></a><br>Exporting an embedded `require_react` and bundling React here can lead to multiple React copies if other bundles or node_modules supply React, causing hooks/runtime errors (invalid hook calls) or inconsistent behavior. Validate that the app uses a single React instance across bundles.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-70a435593851148cd8073c864c7f1ed2ec5cba65dd5204da9e4c5122537464acR1015-R1028'><strong>Source map / license exposure</strong></a><br>A sourceMappingURL and full development comments/licenses are present. If this file is served in production it may expose source map contents (and internal code paths). Confirm source maps are disabled or protected in production environments.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-70a435593851148cd8073c864c7f1ed2ec5cba65dd5204da9e4c5122537464acR960-R994'><strong>Dev build included</strong></a><br>This file contains the React development build (lots of runtime warnings, unminified code and developer-only checks). Shipping the dev build in production will hurt performance and flood logs. Ensure production builds use the production React bundle and minification.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/2/files#diff-70a435593851148cd8073c864c7f1ed2ec5cba65dd5204da9e4c5122537464acR1-R1028'><strong>Committed build artifact</strong></a><br>A full, large bundled dependency (React development build + loader helpers) was added to the repo under .vite/deps. Committing build outputs increases repo size, creates merge noise, and makes dependency updates error-prone. Prefer keeping generated bundles out of source control and generating them in CI or locally.<br>

</td></tr>
</table>


**codeant-ai** · 2026-02-04

CodeAnt AI finished reviewing your PR.
**cursor** · revisión COMMENTED · 2026-02-04

Cursor Bugbot has reviewed your changes and found 6 potential issues.

<sup>Bugbot Autofix is OFF. To automatically fix reported issues with Cloud Agents, enable Autofix in the [Cursor dashboard](https://www.cursor.com/dashboard?tab=bugbot).</sup>

### This PR is being reviewed by Cursor Bugbot

<details>
<summary>Details</summary>

Your team is on the Bugbot Free tier. On this plan, Bugbot will review limited PRs each billing cycle for each member of your team.

To receive Bugbot reviews on all of your PRs, visit the [Cursor dashboard](https://www.cursor.com/dashboard?tab=bugbot) to activate Pro and start your 14-day free trial.
</details>




---

<a id="pr-3"></a>
## #3 — Feature entrega3 mo

| | |
|---|---|
| Autor | `marcello-clearcust` |
| Estado | MERGED |
| Ramas | `feature-entrega3-MO` → `master` |
| Creada | 2026-02-05 |
| Integrada | 2026-02-05 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/3 |

### Descripción

## **User description**
<!-- CURSOR_SUMMARY -->
> [!NOTE]
> **Medium Risk**
> Touches inventory fetching UX, manual sales product lookup flow, and TensorFlow.js training pipeline; main risk is regressions in pagination/search behavior and new training memory-management code affecting model training reliability on different browsers/GPUs.
> 
> **Overview**
> Adds **client-side pagination** to the Inventory Stock page, fetching stock via `inventoryService.getStock(posId, page, pageSize)` and providing next/prev controls with range display.
> 
> Updates manual sale creation to use **API-backed debounced product search** (min 2 chars) instead of preloading/filtering the full product list, and simplifies image-recognition preselection to fetch the product directly by ID.
> 
> Hardens browser-side TFJS model training with **more aggressive memory management**: smaller training/feature batch sizes, WebGL backend setup with CPU fallback, batched load+feature-extraction to avoid holding all images in memory, periodic GPU memory monitoring, explicit cleanup via `tf.tidy()`/`tf.nextFrame()`, and clearer error handling for WebGL context/memory failures.
> 
> <sup>Written by [Cursor Bugbot](https://cursor.com/dashboard?tab=bugbot) for commit 91662c5e1ecad51609cdbe7f4aba5fe7799db482. This will update automatically on new commits. Configure [here](https://cursor.com/dashboard?tab=bugbot).</sup>
<!-- /CURSOR_SUMMARY -->


___

## **CodeAnt-AI Description**
Use API-backed product search, add inventory pagination, and make client-side model training more memory-resilient

### What Changed
- Manual sales product lookup now queries the backend with a 300ms debounce and requires at least 2 characters; preselected products from image recognition are fetched directly from the API if not already loaded.
- Inventory stock page adds client-side pagination (50 items per page) with previous/next controls, page display, and resets to page 1 when the selected point of sale changes.
- Client-side image-recognition training now processes images in small batches, reduces training/feature batch sizes, monitors GPU memory, recovers/falls back from WebGL errors, disposes tensors more aggressively, and provides clearer warnings when GPU memory is low or WebGL fails.

### Impact
`✅ Faster product lookup in manual sales`
`✅ Clearer inventory navigation with page controls`
`✅ Fewer browser training crashes from GPU memory exhaustion`
<details>
<summary><strong>💡 Usage Guide</strong></summary>

### Checking Your Pull Request
Every time you make a pull request, our system automatically looks through it. We check for security issues, mistakes in how you're setting up your infrastructure, and common code problems. We do this to make sure your changes are solid and won't cause any trouble later.

### Talking to CodeAnt AI
Got a question or need a hand with something in your pull request? You can easily get in touch with CodeAnt AI right here. Just type the following in a comment on your pull request, and replace "Your question here" with whatever you want to ask:
<pre>
<code>@codeant-ai ask: Your question here</code>
</pre>
This lets you have a chat with CodeAnt AI about your pull request, making it easier to understand and improve your code.

#### Example
<pre>
<code>@codeant-ai ask: Can you suggest a safer alternative to storing this secret?</code>
</pre>

### Preserve Org Learnings with CodeAnt
You can record team preferences so CodeAnt AI applies them in future reviews. Reply directly to the specific CodeAnt AI suggestion (in the same thread) and replace "Your feedback here" with your input:
<pre>
<code>@codeant-ai: Your feedback here</code>
</pre>
This helps CodeAnt AI learn and adapt to your team's coding style and standards.

#### Example
<pre>
<code>@codeant-ai: Do not flag unused imports.</code>
</pre>

### Retrigger review
Ask CodeAnt AI to review the PR again, by typing:
<pre>
<code>@codeant-ai: review</code>
</pre>

### Check Your Repository Health
To analyze the health of your code repository, visit our dashboard at [https://app.codeant.ai](https://app.codeant.ai). This tool helps you identify potential issues and areas for improvement in your codebase, ensuring your repository maintains high standards of code health.

</details>


### Comentarios y revisiones

**codeant-ai** · 2026-02-05

CodeAnt AI is reviewing your PR.

---

### Thanks for using CodeAnt! 🎉

We're free for open-source projects. if you're enjoying it, help us grow by sharing.

[Share on X](https://twitter.com/intent/tweet?text=Just%20tried%20%40CodeAntAI%20for%20automated%20code%20review%20and%20I%27m%20impressed%21%20Free%20for%20open%20source%20with%20a%20free%20trial%20for%20private%20repos.%20Worth%20checking%20out%3A&url=https%3A//codeant.ai) ·
[Reddit](https://www.reddit.com/submit?title=Check%20out%20CodeAnt%20for%20automated%20code%20review&text=Just%20tried%20CodeAnt%20for%20automated%20code%20review%20and%20I%27m%20impressed%21%20Free%20for%20open%20source%20with%20a%20free%20trial%20for%20private%20repos.%20Worth%20checking%20out%3A%20https%3A//codeant.ai) ·
[LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fcodeant.ai&mini=true&title=Check%20out%20CodeAnt%20for%20automated%20code%20review&summary=Just%20tried%20CodeAnt%20for%20automated%20code%20review%20and%20I%27m%20impressed%21%20Free%20for%20open%20source%20with%20a%20free%20trial%20for%20private%20repos)


**codeant-ai** · 2026-02-05

## Nitpicks 🔍

<table>
<tr><td>🔒&nbsp;<strong>No security issues identified</strong></td></tr>
<tr><td>⚡&nbsp;<strong>Recommended areas for review</strong><br><br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/3/files#diff-d821f429bf7de37c8782c464d9b83c706ef1501d8bb25aa3a9b268c35586e4beR192-R216'><strong>Search race condition</strong></a><br>The new debounced product search schedules an async fetch with setTimeout but does not cancel in-flight requests or ignore out-of-order responses. This can cause stale results to overwrite newer ones and the UI loading state to become inconsistent when responses arrive out-of-order or when cleanup runs while a fetch is in-flight.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/3/files#diff-6703ba986894c1308d053b2da3b058ee49400d6d88d23ec85396cb192782219aR70-R79'><strong>WebGL context detection</strong></a><br>The code registers WebGL context loss/restored handlers on a newly created canvas, but TensorFlow.js uses its own internal WebGL context/canvas. Attaching listeners to a created canvas will not catch TFJS's context events, so context-loss recovery may be ineffective. Verify and attach handlers to the actual WebGL canvas used by the TFJS backend, or query the backend for its GL context.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/3/files#diff-0ca526cd5d504957e6d0da6da8fc376db55153fc49d32989c7ac4a9719856524R75-R76'><strong>API contract assumption</strong></a><br>The new call `inventoryService.getStock(selectedPosId, currentPage, pageSize)` assumes the backend accepts (posId, page, pageSize) and that `page` indexing matches this client (likely 1-based). Verify backend pagination index (0 vs 1) and whether `totalCount` and `items.length` semantics match the UI logic.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/3/files#diff-6703ba986894c1308d053b2da3b058ee49400d6d88d23ec85396cb192782219aR90-R96'><strong>Backend internals mutation</strong></a><br>The code writes to an internal backend property (`numMBBeforeWarning`) on the TFJS WebGL backend. Mutating internal implementation details is fragile across TFJS versions and environments. Prefer using tf.memory() sampling and configurable thresholds rather than changing backend internals.<br>

- [ ] <a href='https://github.com/marcello-clearcust/joiabagur-pv/pull/3/files#diff-0ca526cd5d504957e6d0da6da8fc376db55153fc49d32989c7ac4a9719856524R70-R83'><strong>Race condition</strong></a><br>When `selectedPosId` changes the code both resets `currentPage` (useEffect) and triggers `loadStock()` (via the loadStock useCallback dependency). Because both are effects that run after render the page reset and the fetch can happen in either order, meaning the new POS may be loaded with the previous page instead of page 1. This can cause surprising pagination results and extra/incorrect API calls.<br>

</td></tr>
</table>


**codeant-ai** · 2026-02-05

CodeAnt AI finished reviewing your PR.
**cursor** · revisión COMMENTED · 2026-02-05

Cursor Bugbot has reviewed your changes and found 2 potential issues.

<sup>Bugbot Autofix is OFF. To automatically fix reported issues with Cloud Agents, enable Autofix in the [Cursor dashboard](https://www.cursor.com/dashboard?tab=bugbot).</sup>

### This is the final PR Bugbot will review for you during this billing cycle

Your free Bugbot reviews will reset on February 7

<details>
<summary>Details</summary>

Your team is on the Bugbot Free tier. On this plan, Bugbot will review limited PRs each billing cycle for each member of your team.

To receive Bugbot reviews on all of your PRs, visit the [Cursor dashboard](https://www.cursor.com/dashboard?tab=bugbot) to activate Pro and start your 14-day free trial.
</details>




---

<a id="pr-4"></a>
## #4 — docs: diseño del sistema de IA (RAG) para el Proyecto Final — v3, consenso tras revisión

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `docs/proyecto-final-ia` → `master` |
| Creada | 2026-08-01 |
| Integrada | 2026-08-03 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/4 |

### Descripción

## Qué aporta esta PR

Solo documentación. **No toca código, ni el modelo de datos, ni la infraestructura.** Contiene el diseño del sistema de IA que se propone construir sobre Joiabagur PV como Proyecto Final del Máster, más el material de referencia del máster.

> **Actualizada a v3** tras la revisión funcional. La respuesta punto por punto a las 12 decisiones está en el comentario de abajo y, en detalle, en la §3 del documento de diseño.

## Documentos

### `Documentos/Proyecto Final AIEng/` — los entregables

| Documento | Qué es |
|---|---|
| **`proyecto-final-diseno-rag-joiabagur.md`** | 📌 **Documento principal, v3.** Diseño conceptual: análisis crítico de las specs v2, respuesta a las 12 decisiones de la revisión, arquitectura y frontera .NET/Python, estrategia de datos, capa agéntica, inventario asistido, evaluación y plan hasta el 3 de septiembre. |
| **`proyecto-final-plan-changes-openspec.md`** | 📌 **Vigente, v3.** Descomposición en **39 changes OpenSpec** de 2-3 h, en orden cronológico, con prerequisitos, ruta crítica, tests por change y orden de corte fijado de antemano. |
| `joiabagur-ia-especificaciones-funcionales-v2.md` | Especificaciones funcionales vigentes. **Se adoptan como referencia.** |
| `joiabagur-ia-especificaciones-funcionales-v1.md` | Versión anterior, conservada para trazabilidad. |
| `*-3devs.md` | Variantes archivadas para un equipo de 3 personas. **No vigentes y desactualizadas** desde la v3. |

### `Documentos/Sesiones Master AIEng/` — material de referencia

Apuntes de las sesiones S1-S15 del máster (CAG, wrappers, datos, embeddings, BBDD vectoriales, RAG, técnicas de recuperación, agentes, orquestación, multiagente, producción). Base técnica citada por el diseño.

## Alcance comprometido

**Fase 1 completa + Fase 3 parcial** de las specs v2:

- Enriquecimiento de catálogo con `materials[]`, vocabulario cerrado y revisión humana híbrida
- `ProductFamily` + `ProductFamilyMember`, con propuesta asistida por IA y aprobación humana
- Búsqueda semántica híbrida por POS, con desambiguación por familia
- Venta asistida con avisos calculados por reglas y citas verificables
- Agente de venta y agente de inventario, ambos de solo lectura
- Sustitutos, complementarios y perfil comercial por POS
- Inventario: reposición, traslados y rotación, con aprobación manual
- Evaluación con golden set, ablations y validador anti-alucinación

**Fuera, declarado explícitamente:** packing list con máquina de estados, liquidación con descuentos, upsell/downsell, políticas de inventario configurables, reranking implementado.

## Principios de arquitectura

- **`.NET` es la fuente de verdad y conserva toda la regla de negocio**, incluido el motor de recomendaciones de inventario. Python solo hace espacio vectorial y LLM.
- **La IA nunca es fuente de verdad de stock ni de precio.** Se emiten placeholders y el backend los sustituye al hidratar; si alguno queda sin resolver, la respuesta se rechaza. Verificado por un validador determinista con umbral de cero fallos.
- **La proyección de disponibilidad nunca excluye**: pondera el ranking, se sobre-recupera y .NET decide.
- **Degradación garantizada:** si el servicio de IA no responde, el backend cae al buscador léxico actual y la UI sigue funcionando.
- **Sin cambios destructivos:** entidades nuevas y un esquema `ai` propio del servicio Python. No se toca el reconocimiento visual existente.

## Cómo revisar

1. §0 y §3 del documento de diseño: resumen y respuesta a las 12 decisiones.
2. §7.6 (prefiltro blando) y §6.3 (contrato de sincronización): las dos correcciones técnicas que salen de la revisión.
3. §13.4: orden de corte, por si el ritmo de 39 changes no se sostiene.

**Quedan dos puntos marcados ⏳ pendientes de acuerdo** (diccionario de sinónimos y packing list). Ver comentario.

### Comentarios y revisiones

**skydr4g0n-it** · 2026-08-02

## Revisión funcional de la propuesta RAG

La propuesta está bien orientada como MVP técnico y académico centrado en RAG, búsqueda híbrida y asistencia a operadores. Sin embargo, **no cubre completamente las especificaciones funcionales vigentes** y requiere varias decisiones antes de aprobar el diseño.

### Cobertura del alcance

#### Enriquecimiento del catálogo

Cobertura parcial-alta.

Puntos positivos:

* Pipeline de extracción automática de metadatos.
* Uso de confianza, validación y revisión.
* Generación de embeddings.
* Indexación para búsqueda semántica.
* Evaluación mediante golden set y métricas.

Diferencias respecto a la especificación vigente:

* `material` debe ser `materials[]`, ya que un producto puede contener varios materiales.
* Se reintroduce `variant_group_key`, aunque se había sustituido por un modelo explícito `ProductFamily` + `ProductFamilyMember`.
* Se reintroducen conceptos previamente eliminados:

  * `search_aliases`
  * instrucciones de cuidado
  * pitch o guion comercial persistido

La búsqueda puede generar explicaciones comerciales dinámicamente, pero estos datos no deberían almacenarse como atributos del producto salvo que se tome una nueva decisión funcional.

---

#### Búsqueda semántica y venta asistida

Cobertura alta.

La propuesta contempla correctamente:

* búsqueda híbrida léxica y vectorial;
* filtros por POS;
* disponibilidad;
* productos similares;
* desambiguación;
* abstención cuando no existe suficiente confianza;
* resultados estructurados para integrarlos en la venta;
* validación del stock real desde .NET.

Puntos pendientes:

* No queda suficientemente definido el tratamiento de productos complementarios y cross-selling.
* La gestión de variantes debe basarse en `ProductFamily`, no en una clave textual generada.
* Debe aclararse cómo se evita excluir productos válidos cuando la proyección de inventario del servicio Python esté desactualizada.

---

#### Recomendaciones de inventario

Cobertura insuficiente.

La propuesta incluye:

* motor de sustitutos;
* sugerencia de productos similares;
* argumentario por POS en forma de documentos o contexto RAG.

Pero deja fuera:

* recomendaciones de reposición;
* traslados entre POS;
* packing lists;
* detección de stock parado;
* recomendaciones de liquidación o rotación;
* priorización basada en velocidad de venta;
* generación de propuestas de inventario para aprobación.

Por tanto, la propuesta actual no implementa la funcionalidad completa de “Recomendaciones de inventario”. Implementa principalmente búsqueda de sustitutos.

---

## Decisiones críticas necesarias

### 1. Alcance de la entrega

Hay que decidir si esta propuesta representa:

* la implementación completa de las especificaciones funcionales; o
* una primera fase centrada exclusivamente en RAG, búsqueda y sustitutos.

La propuesta actual solo encaja claramente como **Fase 1**.

---

### 2. Modelo definitivo de variantes

Elegir entre:

* `ProductFamily` + `ProductFamilyMember`; o
* `VariantGroupKey`.

Recomendación: mantener `ProductFamily`, porque las tallas y variantes son relaciones de negocio explícitas y no deberían depender de una cadena generada o inferida.

---

### 3. Modelo de materiales

Debe cambiarse:

```text
material
```

por:

```text
materials[]
```

También debe decidirse:

* si se almacena como `text[]`, `jsonb` o relación normalizada;
* si existe vocabulario controlado;
* cómo se normalizan sinónimos;
* cómo se filtran productos que contienen varios materiales.

---

### 4. Campos eliminados que reaparecen

Hay que confirmar si deben eliminarse nuevamente:

* `SearchAliases`
* `CareInstructions`
* `SalesPitch` o equivalente
* `VariantGroupKey`

Recomendación: no persistirlos como atributos IA del producto.

El argumentario comercial puede generarse en tiempo de consulta a partir de los metadatos aprobados.

---

### 5. Estrategia de revisión humana

La propuesta plantea autoaprobación por confianza y revisión por excepción.

Debe decidirse si:

* todos los perfiles requieren aprobación;
* se autoaprueba todo lo que supere un umbral;
* se aplica un modelo híbrido.

Recomendación: modelo híbrido.

Los campos sensibles para búsqueda y selección deberían revisarse cuando sean inferidos:

* materiales;
* piedra;
* talla;
* tipo de pieza;
* familia o variante.

Los tags comerciales podrían autoaprobarse con alta confianza.

---

### 6. Alcance mínimo de inventario

Debe decidirse qué entra en esta fase:

* solo sustitutos;
* sustitutos + reposición;
* sustitutos + reposición + packing list;
* inventario completo.

Recomendación mínima para considerar cubierta la funcionalidad:

* recomendaciones de reposición;
* sustitutos cuando no haya disponibilidad;
* packing list;
* stock parado y rotación;
* aprobación manual de recomendaciones.

---

### 7. Argumentario por hotel

La propuesta debe aclarar si el argumentario por POS será:

* un documento estático;
* un perfil generado periódicamente;
* una respuesta dinámica en cada consulta.

Recomendación: calcular un perfil periódico por POS a partir de ventas e inventario y almacenarlo como contexto estructurado.

Ejemplos:

* rangos de precio más vendidos;
* tipos de pieza con mayor rotación;
* materiales preferidos;
* productos con stock prioritario;
* productos que interesa liquidar.

---

### 8. Productos complementarios

La propuesta cubre bien productos similares y sustitutos, pero no define claramente productos complementarios.

Debe decidirse si la venta asistida incluye:

* solo localizar el producto;
* proponer sustitutos;
* recomendar complementos;
* upselling y cross-selling.

Recomendación: incluir complementarios inicialmente mediante reglas simples o configuración manual.

---

### 9. Arquitectura Python frente a .NET

El microservicio Python es razonable para el proyecto de IA, pero añade:

* otro despliegue;
* otro pipeline;
* nuevas migraciones;
* sincronización entre servicios;
* autenticación interna;
* circuit breaker;
* duplicación parcial de datos;
* nuevos puntos de fallo.

Debe decidirse si:

* es una arquitectura temporal para el proyecto académico;
* será una arquitectura permanente de producción;
* algunas funcionalidades deberían permanecer en .NET.

---

### 10. Propiedad y sincronización de datos

Hay que definir con precisión:

* qué servicio es propietario de cada dato;
* quién inicia la sincronización;
* cómo se manejan actualizaciones;
* cómo se procesan borrados y desactivaciones;
* cómo se detecta divergencia;
* cómo se reintentan errores;
* cómo se versionan embeddings y documentos.

La base transaccional .NET debe seguir siendo la fuente de verdad para:

* productos;
* precios;
* POS;
* permisos;
* inventario;
* ventas.

---

### 11. Frescura del inventario

La propuesta usa una proyección de disponibilidad en Python con posible retraso.

Existe riesgo de que un producto válido sea eliminado antes de que .NET pueda validar su stock real.

Recomendación:

* usar la proyección para ranking y prefiltrado no destructivo;
* validar stock y asignación definitivamente en .NET;
* no usar datos potencialmente desactualizados como único filtro excluyente.

---

### 12. Datos de evaluación

La evaluación sintética es válida para demostrar la arquitectura, pero no permite validar el problema real del hotel con mayor volumen.

Recomendación:

* usar catálogo real;
* usar histórico real anonimizado de 2026;
* construir consultas reales o representativas;
* medir errores de selección;
* comparar búsqueda actual frente a búsqueda semántica;
* validar sustitutos con revisión de negocio.

---

## Recomendación final

La propuesta puede aprobarse como **Fase 1 centrada en enriquecimiento, RAG, búsqueda semántica, venta asistida y sustitutos**, siempre que se corrijan antes estos puntos:

1. Cambiar `material` por `materials[]`.
2. Sustituir `VariantGroupKey` por `ProductFamily`.
3. Eliminar los campos que ya se habían descartado.
4. Definir claramente la revisión humana.
5. Aclarar la sincronización y propiedad de datos.
6. Evitar que una proyección desactualizada excluya productos válidos.
7. Declarar explícitamente que reposición, packing list y rotación quedan para una fase posterior.

Si la PR pretende cubrir las especificaciones funcionales completas, debe ampliarse para incluir las funcionalidades de inventario pendientes.



---

<a id="pr-5"></a>
## #5 — C01: init ai-service skeleton (jbg-ai)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c01-init-ai-service-skeleton` → `ai-eng` |
| Creada | 2026-08-03 |
| Integrada | 2026-08-03 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/5 |

### Descripción

## Summary
- Skeleton FastAPI `ai-service` / `jbg_ai`: settings fail-fast, `GET /health`, middleware `X-Trace-Id`
- Dockerfile + servicio Compose `jbg-ai` en `jpv-network` (`8001:8000`); Postgres local a `pgvector/pgvector:pg15`
- OpenSpec C01 archivado; specs `ai-service-runtime` y `ai-service-dev-compose` en main; incluye archive/sync de barcode-qr-scanning

## Test plan
- [ ] `cd ai-service && uv sync --system-certs && uv run pytest`
- [ ] `cd backend && docker compose up --build -d jbg-ai`
- [ ] `curl http://127.0.0.1:8001/health` → OK + version
- [ ] Confirmar que no se crea schema `ai` ni `CREATE EXTENSION` en este change


---

<a id="pr-6"></a>
## #6 — feat(ai-service): congelar contratos /v1 y auth interna de jbg-ai

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c02-add-ai-service-contracts-and-auth` → `ai-eng` |
| Creada | 2026-08-06 |
| Integrada | 2026-08-06 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/6 |

### Descripción

## 📋 Descripción

Congela la superficie HTTP `/v1` del microservicio Python `jbg-ai` y añade su autenticación de servicio interna. Se publican ocho endpoints (`retrieval/products`, `retrieval/substitutes`, `assist/sale`, `inventory/propose`, `enrich/products`, `index/sync`, `index/status` y `evals/runs`) con modelos Pydantic explícitos de petición y respuesta, servidos por stubs deterministas mientras la lógica real llega en changes posteriores (C09, C13, C14, C24, C26, C30, C35). El contrato queda versionado en `ai-service/openapi.json` y un test de igualdad estricta convierte cualquier deriva en un fallo de build.

Cada ruta `/v1` exige un token HS256 emitido por la API .NET (`ai-service/src/jbg_ai/api/auth.py:decode_service_token`), con cuatro claims obligatorios congelados en `snake_case`: `user_id`, `role`, `pos_id` y `trace_id`. El `pos_id` y el `role` salen siempre del token: el body puede traer `pos_id` por compatibilidad de cliente, pero se ignora y la respuesta devuelve el ámbito realmente aplicado en `effective_pos_id`. Cualquier fallo de validación responde un 401 opaco que no revela qué comprobación falló. `GET /health` sigue público y con el mismo contrato de C01.

La PR incluye además la sincronización documental del change (README de `ai-service`, `backend` y `terraform`, `Documentos/` y `openspec/`), el arreglo de tres specs vivas malformadas y una skill `update-docs` replicada en los cinco harnesses del repo. De las 14 565 líneas añadidas, 8 252 son esas cinco copias byte a byte idénticas de la skill.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [x] 💥 breaking change — rompe compatibilidad (solo de configuración: ver *Deployment notes*)

---

## 🎯 Motivación y contexto

C01 dejó `jbg-ai` como un esqueleto ejecutable (settings, `/health`, logging con `trace_id`, contenedor y Compose). C03 tiene que construir el cliente tipado .NET contra un contrato que todavía no existía. Congelar ahora la frontera —con stubs deterministas en vez de esperar a la lógica real— permite que el lado .NET escriba sus tests de mapeo contra respuestas estables y que cada change posterior sustituya un handler sin renegociar el contrato.

- **Change OpenSpec**: `openspec/changes/archive/2026-08-06-add-ai-service-contracts-and-auth/` (proposal, design con 12 decisiones, tasks, ticket `T-AIENG-002` y `qa.md`), ya archivado en este mismo diff.
- **Historia de usuario**: `Documentos/Historias/AI-Eng/HU-AIENG-002.md` (13 escenarios de aceptación).
- **Regla de frontera** que motiva la forma de los contratos: Python calcula similitud y escribe prosa; .NET calcula números y decide. Ningún modelo de `ai-service/src/jbg_ai/api/schemas/` transporta un precio o un stock.

No hay issues referenciados en los commits de la rama.

---

## 🔄 Cambios realizados

### `ai-contracts` — contratos congelados (+2 432)

- `api/schemas/` nuevo, un módulo por dominio: `retrieval.py`, `assist.py`, `inventory.py`, `enrich.py`, `index.py`, `evals.py` y `common.py`. `common.py` fija `PRICE_PLACEHOLDER = "{{price}}"` y `STOCK_PLACEHOLDER = "{{stock}}"`, y define `TracedResponse` (`trace_id`) y `ScopedResponse` (`effective_pos_id`), de los que heredan las respuestas con ámbito de punto de venta.
- `retrieval.py`: `top_k` es el tamaño de página **tras** hidratar en .NET (`ge=1, le=50`); `family_id` y `variant_label` son nullables por contrato; `SubstituteResult` extiende `RetrievalResult` con `SimilaritySignals` (sin señal de precio, por diseño).
- `api/auth.py`: `ServicePrincipal` (`user_id`, `role`, `pos_id`, `trace_id`), `InvalidServiceToken` y `decode_service_token()`, que valida firma, caducidad y presencia no vacía de los cuatro claims.
- `api/deps.py`: `get_service_principal()` (dependencia `HTTPBearer` con `auto_error=False`), `require_stub_mode()` para el 501, `_unauthorized()` con un único mensaje opaco y `V1_RESPONSES` documentando 401 y 501 en todas las rutas. Tras validar el token, sobrescribe `request.state.trace_id` con el claim.
- `ai-service/openapi.json` — snapshot nuevo de 1 867 líneas (49 946 bytes). El chunk 14 del diff llega truncado a cabeceras de hunk, así que lo que sigue está leído directamente del fichero en la rama, no inferido del test de snapshot:
  - OpenAPI **3.1.0**, `info.title = jbg-ai`, `info.version = 0.1.0`, sin bloque `servers`: el contrato no fija host.
  - **9 operaciones**: `GET /health` sin `security`, y las ocho rutas `/v1` con `security: [{"HTTPBearer": []}]`. Único esquema de seguridad declarado: `HTTPBearer` (`type: http`, `scheme: bearer`, descripción «Internal HS256 service token»).
  - **Respuestas por ruta `/v1`**: `200`, `401` («Invalid or missing internal service token»), `501` («Not implemented yet; delivered in a later change») y, en las seis que llevan body, `422`.
  - **35 schemas** en `components.schemas`: los 33 modelos de dominio más `HTTPValidationError` y `ValidationError`.
  - Las restricciones viajan en el contrato, no solo en el código: `RetrievalRequest.top_k` (default 10, rango 1–50), `EnrichRequest.products` (1–50 elementos), `RetrievalMode` como enum `hybrid|vector|lexical`, `family_id` y `variant_label` como `anyOf [string, null]` con la descripción «Null when the family/variant is unknown», y `pos_id` documentado como «Accepted for client compatibility and ignored; scope comes from the token».
  - Las respuestas con ámbito declaran `trace_id` y `effective_pos_id` entre sus campos **obligatorios** (`RetrievalResponse.required = [trace_id, effective_pos_id, results, candidates_returned]`), y `AssistResponse.pitch` documenta en su `description` los placeholders sin resolver.

### `ai-service` — routers, settings y stubs (+684 / −11)

- `api/routers/` nuevo, uno por dominio, todos con `Depends(get_service_principal)` y una constante `DELIVERED_BY` que nombra el change que traerá la implementación real. `routers/__init__.py:DOMAIN_ROUTERS` agrupa los cinco que se montan siempre.
- `api/main.py:create_app()` monta `DOMAIN_ROUTERS` y añade `evals.router` **solo** si `enable_dev_endpoints`: bajo perfil de producción la ruta no existe, en lugar de responder un 404 documentado y engañoso.
- `config/settings.py`: `jwt_secret` obligatorio (`min_length=1`, con `reject_blank`), `jwt_ttl_seconds` (300), `stub_mode` (`true`) y `enable_dev_endpoints`, derivado de `app_env` por `derive_dev_endpoints()` — `false` para `prod`/`production`. Se añade `canonical_openapi_settings()`, el perfil fijo con el que se genera el snapshot para que test y regeneración manual no puedan divergir.
- `api/middleware.py:TraceIdMiddleware.dispatch()` relee `request.state.trace_id` después del handler, de modo que el claim del token gane sobre la cabecera `X-Trace-Id` tanto en la respuesta como en los logs.
- `stubs/responses.py`: constructores puros, sin reloj ni aleatoriedad ni E/S. Implementan la regla de sobre-recuperación `over_retrieval_count() = min(top_k × 3, 60)`, el `pitch` con placeholders sin resolver y fechas fijas (`_LAST_FULL_SYNC_AT`, `_NEXT_CURSOR`) para no romper el determinismo.

### `tests` — suite de contrato (+878 / −52)

- Nuevos: `tests/api/` (`test_auth.py`, `test_contracts.py`, `test_retrieval_stub.py`, `test_assist_stub.py`, `test_stub_mode.py`, `test_evals_gating.py`, `test_openapi_snapshot.py`) y `tests/config/test_settings.py`.
- `tests/support/` nuevo con helpers importables: `settings.py:build_settings()`, `sample_requests.py:V1_REQUESTS`/`RESPONSE_MODELS` y `paths.py:OPENAPI_SNAPSHOT`, que ancla la ruta del snapshot una sola vez en lugar de contar `parents[N]` desde cada test.
- `tests/conftest.py` añade las fixtures `client`, `issue_token`, `auth_headers` y `forbid_network`, esta última convierte cualquier conexión de socket en fallo.
- Reubicaciones: `tests/test_settings.py` eliminado y reescrito como `tests/config/test_settings.py`; `tests/test_health.py` renombrado a `tests/api/test_health.py` con un test nuevo, `test_health_is_public`.

### `deps` (+21 / −1)

- `pyproject.toml`: dependencia nueva `pyjwt>=2.9.0` (resuelta a 2.13.0 en `uv.lock`); `pythonpath = ["src", "tests"]`, `addopts = "--import-mode=importlib"` y los marcadores `db` y `slow`.

### `infra` (+114)

- `backend/docker-compose.yml`: el servicio `jbg-ai` recibe `JWT_SECRET` (placeholder de desarrollo) y `STUB_MODE: "true"`, para que el contenedor arranque en local sin configuración adicional.
- `terraform/README.md` nuevo: documenta el stack de producción existente (EC2, RDS, S3, ECR, IAM/OIDC, SSM `/jpv/prod/*`), variables, outputs y avisos operativos. Es documentación: **no cambia ningún `.tf`**.

### `openspec` (+1 264 / −16)

- Change archivado en `changes/archive/2026-08-06-add-ai-service-contracts-and-auth/` con sus artefactos completos.
- Specs vivas nuevas: `specs/ai-service-api-contracts/spec.md` y `specs/ai-service-auth/spec.md`. Modificadas: `ai-service-runtime` (fail-fast de `JWT_SECRET`, precedencia del `trace_id` del claim) y `ai-service-dev-compose` (credenciales de servicio en Compose).
- **Fix**: `specs/dashboard-analytics/spec.md`, `specs/inventory-movement-report/spec.md` y `specs/sales-reports/spec.md` empezaban por `## ADDED Requirements` —sintaxis de delta copiada tal cual en una spec viva— y no tenían `## Purpose`. Ahora siguen el formato `# <capability> Specification` / `## Purpose` / `## Requirements`.
- `openspec/project.md` y `openspec/config.yaml` incorporan el stack de `jbg-ai`, sus convenciones de test, la rama de integración `ai-eng`, las épicas EP11–EP17 y una sección de validación que fija `openspec validate --all --strict` como puerta del proyecto.

### `docs` (+906 / −163)

- `ai-service/README.md`: variables de entorno, tabla de los ocho endpoints congelados, reglas del token interno, stubs y 501, y el procedimiento de regeneración del snapshot (bash y PowerShell) con la advertencia de que regenerar es una negociación de contrato, no una tarea rutinaria.
- `ai-service/tests/README.md` nuevo: el árbol de tests refleja `src/jbg_ai/`, con la tabla de qué change aterriza en cada carpeta y las reglas de `support/` vs `fixtures/`.
- `Documentos/arquitectura.md`, `modelo-c4.md` y `epicas.md` incorporan `jbg-ai` como contenedor, sus componentes y las épicas EP11–EP17. `backend/README.md` corrige el arranque local (tres servicios de Compose, puerto 5433) y sustituye Swagger UI por Scalar (`/scalar/v1`, `/openapi/v1.json`).
- `Documentos/modelo-de-datos.md`: el `erDiagram` se limpia de los pseudo-atributos `indexed(...)` y `unique(...)`, que Mermaid no interpreta, y las claves compuestas pasan a marcarse `FK,UK`. Para que no se pierda nada por el camino, se añade una nota bajo el diagrama que explica la notación y remite a «Índices y Optimizaciones» como referencia completa, y esa sección recupera los dos únicos índices que no estaban representados en ningún otro sitio: `IX_Sale_BulkOperation (BulkOperationId)` y `IX_Inventory_PointOfSale_Product_IsActive (PointOfSaleId, ProductId, IsActive)`, ambos verificados contra `SaleConfiguration.cs:57` e `InventoryConfiguration.cs:52`.

### `ai-tooling` (+8 252) y `misc` (+3)

- Skill `update-docs` (SKILL.md, `config/doc-impact.json`, cuatro `references/`, `scripts/docs-context.ps1`, plantilla de informe) replicada en `.agent/`, `.claude/`, `.codex/`, `.cursor/` y `.opencode/`, más los comandos/workflow que la invocan. Se ha comprobado que las cinco copias son idénticas.
- `CLAUDE.md`, hasta ahora vacío, documenta las tres formas de `openspec validate`, la diferencia entre spec viva y spec delta, y las dos particularidades de `ai-service` (`--system-certs` y el snapshot congelado). En consecuencia, el Paso 0 de `update-docs/SKILL.md` ya no dice que `CLAUDE.md` esté vacío: ahora describe qué contiene y lo deja fuera del alcance de escritura de la skill.
- `.gitignore` añade `.docs-update/`, el scratch de la nueva skill.

---

## 🧪 Testing

`ai-service`: 47 funciones de test en 9 ficheros (`pytest`), varias parametrizadas sobre los ocho endpoints de `support/sample_requests.py:V1_REQUESTS`.

| Fichero | Tests | Qué fija |
|---|---|---|
| `tests/api/test_auth.py` | 11 | 401 sin token, siete variantes de token inválido, cabecera mal formada, `alg=none`, precedencia de `pos_id` y `trace_id` del token, `role` del body inerte, `trace_id` en logs |
| `tests/config/test_settings.py` | 7 | Fail-fast de `APP_ENV` / `SERVICE_VERSION` / `JWT_SECRET` (ausente y en blanco), defaults y derivación de `ENABLE_DEV_ENDPOINTS` |
| `tests/api/test_retrieval_stub.py` | 6 | Schema, sobre-recuperación en seis puntos del rango, determinismo, `similarity_signals`, 422 con `top_k` fuera de rango |
| `tests/api/test_contracts.py` | 5 | Los ocho endpoints validan contra su modelo declarado; eco de `effective_pos_id` |
| `tests/api/test_openapi_snapshot.py` | 4 | Igualdad con el fichero committeado, detección de deriva, superficie congelada, `docs_url`/`redoc_url` deshabilitados |
| `tests/api/test_health.py` | 4 | Health público con versión y correlación (C01 + `test_health_is_public`) |
| `tests/api/test_assist_stub.py` | 4 | Agrupación por familia, placeholders sin resolver, ausencia de cifras, determinismo |
| `tests/api/test_stub_mode.py` | 3 | 501 con `STUB_MODE=false`, mensaje que nombra el change entregador, auth antes que el guard |
| `tests/api/test_evals_gating.py` | 3 | Evals en perfil dev, ausente en perfil prod, resto de `/v1` intacto en prod |

La fixture `forbid_network` bloquea `socket.connect` y `socket.create_connection` en los tests de stub: ningún test llama a un proveedor LLM, a una API de embeddings ni a RDS.

`openspec/changes/archive/.../qa.md`, incluido en este diff, registra la ejecución hecha sobre el commit de implementación `6ba8094`: **77 tests recogidos, 77 en verde, ~1,3 s**, con Python 3.11.15 y `uv run --system-certs pytest`. Ese registro nombra las rutas planas (`tests/test_auth.py`…) porque es anterior al commit `deb5520`, que reorganizó el árbol de tests; los ficheros son los mismos.

Sin tests de backend .NET ni de frontend en esta PR: no hay código de esos componentes en el diff.

---

## ✅ Checklist pre-merge

- [ ] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — cobertura no medida en este diff; el umbral aplica a backend y frontend, que no cambian aquí
- [x] Migración de EF Core incluida si cambia el modelo de datos — no aplica: sin cambios en entidades ni en el esquema
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` — cuatro capabilities sincronizadas; `openspec validate --all --strict` no se ejecuta desde el diff
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`) — el único secreto es el placeholder de Compose, marcado como local
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

**Variables de entorno nuevas de `jbg-ai`:**

| Variable | Obligatoria | Default | Dónde darla de alta |
|---|---|---|---|
| `JWT_SECRET` | **sí** | — | Compose local (ya en el diff); producción, SSM `/jpv/prod/*` en C17 |
| `JWT_TTL_SECONDS` | no | `300` | — |
| `STUB_MODE` | no | `true` | Compose local la fija explícitamente |
| `ENABLE_DEV_ENDPOINTS` | no | derivada de `APP_ENV` (`false` en `prod`/`production`) | — |

- **Arranque fail-fast**: sin `JWT_SECRET`, o con el valor en blanco, `Settings` lanza `ValidationError` y el proceso no sirve nada. Cualquier instancia de `jbg-ai` anterior a C02 que no aporte esa variable deja de arrancar. Compose la incluye en este mismo diff; producción todavía no despliega `jbg-ai` (es C17).
- **Dependencia nueva**: `pyjwt` — hay que rehacer el entorno con `uv sync --system-certs` desde `ai-service/`.
- **Secreto compartido**: el valor de `JWT_SECRET` debe ser el mismo que firme la API .NET en C03. El placeholder de Compose es solo de desarrollo y no debe reutilizarse.
- **Orden de despliegue**: `jbg-ai` es un contenedor aparte y aquí es el proveedor del contrato, así que va antes que su consumidor .NET (C03). Esta PR no toca la imagen de producción (API + SPA) ni ningún `.tf`.
- **Sin migraciones ni acceso a base de datos**: C02 no abre conexión a PostgreSQL.
- **Rollback**: revertir el merge basta; no hay migración de datos ni estado persistido. Si se revierte, hay que quitar también `JWT_SECRET`/`STUB_MODE` del Compose local para evitar confusión.

---

## 📝 Notas adicionales

- **Breaking de configuración, no de contrato.** Los ocho endpoints son nuevos y no tienen consumidor todavía, así que no rompen a nadie; lo que sí rompe es el arranque de un `jbg-ai` existente sin `JWT_SECRET`. Se marca la casilla por eso y solo por eso.
- **El snapshot publica `/v1/evals/runs`.** `canonical_openapi_settings()` fija el perfil de desarrollo, así que la ruta de evaluación forma parte del `openapi.json` committeado aunque un despliegue de producción no la sirva. La asimetría es deliberada y está documentada en `ai-service/README.md`; conviene que quien consuma el snapshot desde .NET lo sepa.
- **Acoplamiento con .NET (C03)**: los claims van en `snake_case` en el cable (`user_id`, `role`, `pos_id`, `trace_id`) y los cuatro son obligatorios. Un token que mande `posId` recibe 401. El lado .NET no está en este diff: queda pendiente de alinear.
- **Sobre el chunk truncado**: `ai-service/openapi.json` (1 867 líneas) supera el umbral del troceador y su diff solo trae cabeceras de hunk. Las afirmaciones sobre el contrato en «Cambios realizados» se han verificado leyendo el fichero committeado en la rama, no el diff ni el test.
- **`Documentos/modelo-de-datos.md`**: la limpieza de la notación Mermaid no pierde información, salvo dos índices que ya no aparecían en ningún otro punto del documento y que esta PR añade a «Índices y Optimizaciones» (`Sale.BulkOperationId` e `Inventory (PointOfSaleId, ProductId, IsActive)`). El resto de índices compuestos y de restricciones únicas ya estaban documentados ahí con más detalle del que cabía en el diagrama; una nota bajo el `erDiagram` lo deja explícito.
- **Volumen del diff**: 118 ficheros y 14 565 inserciones, de las cuales 8 252 son las cinco copias idénticas de la skill `update-docs` y ~2 800 son documentación y specs. El código de producción de `jbg-ai` son ~1 100 líneas.
- **Fuera de alcance, para otra PR**: `generate-pr/SKILL.md` (también replicada en los cinco harnesses) arrastra la misma frase corregida aquí — «`CLAUDE.md` y `AGENTS.md` están vacíos en este repo» —. No se toca porque esa skill no forma parte de este change.



---

<a id="pr-7"></a>
## #7 — feat(backend): añade cliente tipado hacia jbg-ai con resiliencia (C03)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c03-add-dotnet-ai-gateway-client` → `ai-eng` |
| Creada | 2026-08-09 |
| Integrada | 2026-08-09 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/7 |

### Descripción

## 📋 Descripción

Añade el **primer cliente HTTP saliente del backend .NET**: `IAiGatewayClient`, que consume el contrato congelado del microservicio `jbg-ai`. Expone **un único método**, `SearchAsync`, contra `POST /v1/retrieval/products`. Es C03 del Proyecto Final de IA (épica EP11), y su valor no es funcionalidad visible —el operador no ve nada— sino desbloquear C15, y con él C16, C17 y C34.

Como es el primero de su especie, lo que se decide aquí lo heredan los tres changes siguientes: dónde vive el cliente, cómo se firma el token de servicio, qué se reintenta y qué no, y cómo se traza la llamada. Por eso el diff pesa más en decisiones que en superficie: `Application` gana un cliente, un emisor de token, un ámbito de llamada, cuatro excepciones tipadas y un registro con pipeline de resiliencia explícito.

El resto del diff son las consecuencias de eso: nueve modelos de transporte espejo del contrato, el acceso a la traza en la capa API, los dos perfiles de logging por entorno, cuarenta tests con tres helpers reutilizables, y el change de OpenSpec archivado con sus dos specs sincronizadas y la documentación de contexto puesta al día.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

C02 congeló ocho rutas `/v1` en `jbg-ai` con stubs deterministas y autenticación HS256, y **nadie las llamaba**. Del lado .NET no existía ninguna pieza de integración: ni un cliente HTTP saliente, ni resiliencia, ni correlación de trazas entre servicios.

Hay un segundo motivo, menos obvio. La capability `ai-service-auth` obliga a `jbg-ai` a rechazar todo token dudoso con un **401 que no revela la causa**: correcto como decisión de seguridad, hostil como experiencia de diagnóstico. Un secreto mal copiado, una audiencia de más en el token y un desfase de reloj producen exactamente el mismo síntoma mudo. Varias decisiones de este PR existen para eliminar esas causas antes de que ocurran, y para anclarlas con tests.

- **Change:** `openspec/changes/archive/2026-08-09-add-dotnet-ai-gateway-client/` (proposal, design, specs, tasks, ticket y qa)
- **Historia:** [HU-AIENG-003](Documentos/Historias/AI-Eng/HU-AIENG-003.md) · ticket T-AIENG-003
- **Plan:** ficha C03 en `Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md`

---

## 🔄 Cambios realizados

### `backend-application` — el cliente y su tubería

- `Services/AiGatewayClient.cs`: `SearchAsync` firma el token, añade la cabecera de correlación, hace el POST y **no trunca** la lista de candidatos —el servicio sobre-recupera a propósito y truncar es trabajo de C15—. Traduce cada modo de fallo del contrato a una excepción distinguible.
- `Services/AiServiceTokenFactory.cs`: HS256 con secreto propio. Ensambla el `JwtPayload` a mano en lugar de usar `SecurityTokenDescriptor` para controlar exactamente qué claims salen.
- `Extensions/AiGatewayServiceCollectionExtensions.cs`: named client `ai-retrieval` y pipeline de resiliencia explícito (timeout, reintento, cortacircuitos), más `Validate(...).ValidateOnStart()`.
- `Services/AiGatewayAttemptTracker.cs`: contador ambiente de intentos, porque el reintento vive dentro del pipeline y no es observable desde el punto de llamada.
- `Configuration/AiGatewayOptions.cs` y `Exceptions/` (base `AiGatewayException` + tres derivadas).
- Interfaces: `IAiGatewayClient`, `IAiServiceTokenFactory`, `ITraceContextAccessor`.

### `backend-api` — modelos de transporte y correlación

- `DTOs/Ai/`: nueve tipos espejo del contrato congelado, con `AiGatewaySerialization` centralizando la política `snake_case` en un único `JsonSerializerOptions` en lugar de un atributo por propiedad.
- `DTOs/Ai/AiCallScope.cs`: clase sellada con **única** fábrica `ForPointOfSale`.
- `Services/TraceContextAccessor.cs` (capa API, patrón de `CurrentUserService`) y su registro en `Extensions/ServiceCollectionExtensions.cs`.
- `Program.cs`: `AddAiGateway(builder.Configuration)` como línea propia, sin tocar la firma de `AddApplication()`.

### `config` — configuración y perfiles de logging

- `appsettings.json`: sección `AiGateway` nueva; el sink de consola pasa a forma con clave y **sin `Args`**.
- `appsettings.Development.json` y `appsettings.Production.json` (nuevos): cada entorno aporta los argumentos de su sink.

### `deps`

- `Microsoft.Extensions.Http` y `Microsoft.Extensions.Http.Resilience` 10.8.0 en `Application`; `Serilog.Formatting.Compact` 3.0.0 en `API`; `Microsoft.Extensions.TimeProvider.Testing` en `Tests`.
- La familia `Microsoft.Extensions.*` sube de 10.0.0 a 10.0.10 **como conjunto**: el paquete de resiliencia depende de esa línea y dejar el resto en 10.0.0 es una degradación de paquete (NU1605), no una preferencia.

### `misc` — política de configuración frente a secretos

- `.gitignore`: `appsettings.Development.json` y `appsettings.Production.json` salen de la sección de secretos; entran `appsettings.Local.json` y `appsettings.*.Local.json`.

### `tests`

- Helpers reutilizables en `TestHelpers/`: `FakeHttpMessageHandler` (respuestas programadas y **contador de peticiones emitidas**), `RecordingLoggerProvider` (eventos con plantilla, propiedades y scopes), `RepositoryRoot`, y `AiGatewayTestHost`, que monta el gateway como en producción y sustituye solo el socket.
- Cinco suites: cliente, emisor de token, ámbito de llamada, registro y validación de arranque, contrato, y perfiles de Serilog.

### `openspec`

- Change archivado en `changes/archive/2026-08-09-add-dotnet-ai-gateway-client/`.
- `specs/ai-gateway-client/spec.md`: capability nueva, 10 requisitos y 27 escenarios.
- `specs/backend/spec.md`: `Structured Logging` amplía render por entorno y correlación de llamadas **salientes**, conservando sus dos escenarios originales.
- `project.md`: stack de HTTP saliente con resiliencia.

### `docs`

- `epicas.md`: HU-AIENG-003 marcada como hecha.
- `backend/README.md`: la instrucción de arranque decía «Create `appsettings.Development.json`», fichero que ahora está versionado y lleva el perfil de logging — seguirla lo sobrescribía. Añade las dos variables `AiGateway` sin las que la API no arranca, la política de configuración frente a secretos, y corrige «Production Deployment».
- `README.md` (§1.2 y §1.4), `arquitectura.md` (configuración local + prerrequisito de red para C17), `testing-backend.md` (helpers compartidos).

---

## 🧪 Testing

**40 tests nuevos, todos en verde. Cero regresión**, verificada contra baseline con `git stash`: 265 aprobados sin este trabajo y 305 con él, con la **misma** lista de 10 fallos preexistentes (imágenes, PDF, Excel y transacciones — ninguna zona que este PR toque).

| Suite | Qué cubre |
|---|---|
| `AiGatewayClientTests` (13) | Mapeo completo, nulos del contrato, ausencia de truncado, cabeceras, timeout, circuito abierto, y los tres modos de reintento |
| `AiServiceTokenFactoryTests` (6) | Claims, nombres `snake_case`, ausencia de `aud`/`iss`/`nbf`/`iat`, vencimiento y algoritmo |
| `AiCallScopeTests` (5) | Validaciones de la fábrica y ausencia de constructor público |
| `AiGatewayRegistrationTests` (5) | Fallo de arranque por secreto ausente, secreto corto y dirección no absoluta |
| `AiContractSnapshotTests` (6) | Cada propiedad de los modelos frente a `ai-service/openapi.json` |
| `SerilogEnvironmentProfileTests` (4) | Render por entorno y ausencia de restos del fichero base |

Tres detalles de diseño de los tests que conviene mirar en review:

- Los tests de **501, 401 y 503 afirman el número de peticiones HTTP emitidas**, no solo el tipo de excepción. Un predicado que reintenta todo lanza igualmente la excepción correcta, solo que después de gastar el presupuesto: el contador es lo único que discrimina.
- El test del cortacircuitos configura umbrales bajos explícitos. Con los valores por defecto de Polly v8 —ventana de muestreo y mínimo de llamadas— dos fallos no abren nada y el test pasaría sin probar nada.
- Los tests corren contra el **pipeline de resiliencia real**, con un `HttpMessageHandler` falso debajo. Sin red, sin contenedor.

Verificación adicional recogida en `qa.md`: humo extremo a extremo contra un `jbg-ai` levantado (`/health` 200; `top_k = 5` devolvió 15 candidatos sin truncar; el `trace_id` volvió) y comprobación manual de que la guarda de contrato muerde, insertando una propiedad ausente del esquema y confirmando el test en rojo.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — hay 40 tests nuevos, pero **la cobertura no se ha medido**
- [x] Migración de EF Core incluida si cambia el modelo de datos — no cambia: no hay entidades ni migraciones en el diff
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — no cambia: `ai-service/` no tiene ni un fichero en el diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: 30 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`) — las cadenas con forma de credencial en `appsettings.json` son marcadores de desarrollo, del mismo tipo que los que ya existían; producción las sobrescribe desde SSM
- [x] Revisado el impacto en otros componentes del monorepo — `ai-service/`, `frontend/` y `terraform/` suman **0 ficheros** en el diff

---

## 🚀 Deployment notes

**Este PR no despliega nada.** El despliegue del servicio y sus secretos son C17.

Dos variables nuevas, ambas obligatorias, con validación **en el arranque**: si faltan o están mal formadas, la API no levanta y el error nombra la clave.

| Variable | Desarrollo | Producción |
|---|---|---|
| `AiGateway__BaseUrl` | `http://localhost:8001` | `http://jbg-ai:8000` |
| `AiGateway__JwtSecret` | Marcador local, idéntico al `JWT_SECRET` del contenedor | `/jpv/prod/AiGateway__JwtSecret` |

> ⚠️ **Prerrequisito para C17, no un hecho de hoy.** La dirección de producción presupone una **red Docker definida por el usuario**, que no existe: el despliegue arranca los contenedores con `docker run` sobre la red *bridge* por defecto, donde Docker **no resuelve nombres de contenedor**. C17 debe crear la red, unir ambos contenedores, dejar el puerto de `jbg-ai` sin publicar y crear los dos parámetros SSM. Sin eso, la integración funciona en desarrollo y falla en producción con conexión rechazada.

**Rollback:** revertir el merge. No hay migración que deshacer, ni consumidor del cliente todavía —`AiController` no existe: llega en C15—, así que el único efecto observable de un despliegue es que la API exige la sección `AiGateway` para arrancar.

---

## 📝 Notas adicionales

**Sin breaking changes.** No se modifica ningún contrato REST existente ni el snapshot de `jbg-ai`.

Cinco decisiones que no son obvias leyendo el diff:

1. **El cliente vive en `Application`, no en `Infrastructure`.** El instinto dice lo contrario —es E/S externa, y el precedente cercano es `S3FileStorageService`—, pero `JoiabagurPV.Infrastructure.csproj` referencia **solo** a `Domain`: implementarlo allí obligaría a subir `IAiGatewayClient` y sus modelos al dominio de joyería. Un `AiSearchResult` con `match_reasons` y `variant_label` no es dominio de joyería.
2. **`AiCallScope` es clase sellada y no `record struct`.** Todo struct tiene un `default` implícito, es decir un ámbito con punto de venta vacío: justo el estado que la fábrica existe para impedir. Desde C22, `pos_id` será el **único filtro duro** del recuperador, así que un valor centinela llegando ahí sería una fuga entre puntos de venta disfrazada de parámetro de conveniencia.
3. **El token no emite `aud`, `iss` ni `nbf`.** `jbg-ai` decodifica sin audiencia esperada, y PyJWT rechaza un token que **declara** una audiencia cuando el validador no espera ninguna; además valida `iat` y `nbf` sin margen de reloj. Cualquiera de las tres cosas rompe todas las llamadas con el 401 que la spec obliga a no explicar.
4. **El predicado de reintento es lista blanca.** Excluye 401 —configuración, no fallo transitorio— y 501, que C02 eligió en lugar de 503 precisamente para que un cliente resiliente no insistiera en una ruta sin implementación.
5. **Cliente con nombre separado para recuperación.** Además del presupuesto de tiempo distinto, el motivo de fondo es que un cortacircuitos compartido haría que un modelo de lenguaje lento abriese el circuito de la búsqueda, y C15 caería a su buscador léxico por un problema que no era suyo.

Tres hallazgos aparecidos al implementar, todos con test detrás:

- `Uri.TryCreate("localhost:8001", UriKind.Absolute, out _)` **devuelve true**: lee `localhost` como esquema. Es la errata típica en configuración de producción, así que la validación exige esquema `http` o `https`.
- La configuración de .NET fusiona **por clave hoja**, no solo los arrays por índice. El sink de consola acababa recibiendo `outputTemplate` **y** `formatter`, sin sobrecarga que acepte ambos: producción habría escrito texto pareciendo correctamente configurada. Por eso el fichero base declara el sink sin argumentos y cada entorno aporta los suyos.
- Los dos ficheros de perfil estaban en `.gitignore` bajo «Secrets and sensitive files», de modo que el perfil de producción **nunca habría llegado a la imagen** y su test pasaba solo en la máquina que los creó. Se corrigió la regla en lugar de exceptuar los ficheros: `appsettings*.json` son configuración y se versionan; los overrides personales van a `appsettings*.Local.json` y los secretos reales a user-secrets o SSM.

**Deuda señalada, no resuelta aquí:** `backend/docker-compose.prod.yml` no lo invoca ningún workflow, terraform ni script, construye el `Dockerfile` equivocado y declara su propio Postgres donde producción usa RDS — pero `backend/README.md` lo documentaba como el despliegue de producción. El README queda corregido y el fichero marcado para eliminar en C17.

**Punto de atención para review:** los ficheros que más merecen mirada son `AiServiceTokenFactory.cs` (por el motivo 3) y `AiGatewayServiceCollectionExtensions.cs` (por el 4 y el 5). El resto es mapeo y andamiaje de test.



---

<a id="pr-8"></a>
## #8 — feat(telemetry): registrar el ciclo consulta→selección (C04)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c04-add-product-search-event-tracking` → `ai-eng` |
| Creada | 2026-08-11 |
| Integrada | 2026-08-11 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/8 |

### Descripción

## 📋 Descripción

Añade la capability `ai-search-telemetry`: el registro del ciclo **consulta → selección** de la búsqueda asistida. Entra la entidad `ProductSearchEvent` (17 columnas), la columna `Sale.SearchEventId`, una migración de EF Core, un servicio de aplicación con dos caminos de escritura y **un único endpoint HTTP**.

La decisión estructural es **quién escribe cada dato**. El backend registra la mitad de búsqueda mientras la sirve, porque el origen de los resultados, el `trace_id`, la latencia real de recuperación y la lista efectivamente devuelta no existen en ningún otro sitio; el navegador reporta solo el producto elegido, y el servidor deriva el rank desde la lista guardada. El cuerpo que envía el cliente acaba teniendo **un campo**.

No hay ninguna ruta de lectura: ni `GET`, ni listado, ni agregación. El análisis de estos eventos se hace con SQL directo. El change está archivado y sus 12 requisitos ya sincronizados a `openspec/specs/ai-search-telemetry/spec.md`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Seis de los KPIs de las especificaciones funcionales v2 §5.11 no tenían soporte de datos: tiempo búsqueda→selección, ventas iniciadas desde búsqueda asistida, consultas sin resultado, selección en rank 1/3, ticket medio asistido frente a no asistido, y ventas con sustituto sugerido. Sin tabla, la única alternativa era un cruce difuso por usuario, POS, producto y ventana temporal, que falla justo en el caso más frecuente del negocio: vender dos veces el mismo artículo.

Se hace antes que el frontend que lo usará por dos motivos. Es 🟢 y no bloquea a nadie, mientras que C16 es 🔴 y cae en la ola más congestionada: adelantarlo **descarga la ruta crítica**. Y es la primera migración de EF Core de las seis previstas, así que paga un coste fijo de utillaje —no existía ni un test de migración en el repo— que conviene pagar donde no espera nadie.

- **Change OpenSpec:** `openspec/changes/archive/2026-08-11-add-product-search-event-tracking/` (39/39 tareas, capability `ai-search-telemetry`)
- **Historia de usuario:** [HU-AIENG-004](Documentos/Historias/AI-Eng/HU-AIENG-004.md) — EP17, Evaluación y Observabilidad de IA
- **Ticket técnico:** `T-AIENG-004`, dentro del change archivado

---

## 🔄 Cambios realizados

### `backend-domain`

- `Domain/Enums/SearchOrigin.cs`: enum nuevo con valores explícitos (`Assisted = 1`, `LexicalFallback = 2`). Distingue la ruta asistida de la degradada al buscador léxico. **No reutiliza `AiRetrievalMode`** de C03: aquel describe la estrategia interna de `jbg-ai`, este si el servicio llegó a responder.

### `backend-data`

- `Domain/Entities/ProductSearchEvent.cs`: entidad nueva, **sin propiedades de navegación**.
- `Domain/Entities/Sale.cs`: propiedad `SearchEventId` (`Guid?`). Solo adiciones — ninguna línea eliminada.
- `Infrastructure/Data/Configurations/ProductSearchEventConfiguration.cs`: `FiltersJson` y `ResultsJson` como `jsonb` declarado a mano, `SearchText` a `varchar(500)` —longitud tomada de `query.maxLength` en `ai-service/openapi.json`—, índice compuesto `(PointOfSaleId, CreatedAt)` en ese orden y las tres reglas de borrado salientes como `Restrict`.
- `Infrastructure/Data/Configurations/SaleConfiguration.cs`: relación hacia el evento con **`OnDelete: SetNull`**.
- `Infrastructure/Data/Migrations/20260811061759_AddProductSearchEventTracking.cs`: `CreateTable` + `AddColumn` nullable sobre `Sales`. Reversible: el `Down` elimina ambos.
- `ApplicationDbContext.cs`: `DbSet<ProductSearchEvent>`.

### `backend-application`

- `Interfaces/IProductSearchEventService.cs` + `Services/ProductSearchEventService.cs`: dos caminos de escritura. `RecordSearchAsync` devuelve `Guid?` y **nunca lanza** —absorbe cualquier fallo de persistencia y lo registra a nivel de error—; el registro de selección deriva el rank buscando el producto en la lista guardada, sella el instante y aplica «última escritura gana».
- Proyección a JSON en `camelCase` con truncado **por número de entradas** (`MaxStoredResults = 50`), nunca por bytes.
- `DTOs/Ai/RecordSearchRequest.cs`: construido sobre `AiCallScope`, `AiSearchFilters` y `AiSearchResult`, tipos ya congelados por C03.
- `Validators/RecordSearchSelectionRequestValidator.cs` + registro en `Extensions/ServiceCollectionExtensions.cs`.

### `backend-api`

- `Controllers/AiSearchEventsController.cs`: `POST /api/ai/search-events/{id}/selection`, `[Authorize]`, cuerpo `{ productId }`, respuestas `204` / `400` / `401` / `403` / `404`. **Sin versión en la ruta** y **sin heredar de `BaseController`**, cuyo helper de creación apunta a un `GetById` que aquí no existe.
- `DTOs/Ai/SelectionOutcome.cs`: resultado explícito (`Recorded`, `EventNotFound`, `NotOwner`) en vez de excepciones, porque hay dos rechazos distintos que mapean a códigos distintos.

### `tests`

- `TestHelpers/SchemaAssert.cs`: ayudante compartido que lee del catálogo de PostgreSQL el tipo y la nulabilidad de una columna, su longitud máxima, las columnas de un índice **en orden**, y la regla de borrado de una clave foránea.
- `UnitTests/Persistence/MigrationModelDriftTests.cs`: compara el modelo con el snapshot de migraciones **sin base de datos**.
- `IntegrationTests/ProductSearchEventSchemaTests.cs`, `IntegrationTests/AiSearchEventsControllerTests.cs`, `UnitTests/Application/ProductSearchEventServiceTests.cs`.
- `backend/api-tests/ai-search-events.http` y su entrada en el README de esa carpeta.

### `openspec`

- Change archivado con sus seis artefactos, incluido `qa.md`.
- `openspec/specs/ai-search-telemetry/spec.md`: capability viva nueva, 12 requisitos y 24 escenarios, con `## Purpose` redactado.
- `openspec/project.md`: `ProductSearchEvent` y el campo nuevo de `Sale` en §Key Entities. Se añade también `ProductPhotoEmbedding`, que faltaba desde marzo.

### `docs`

- Tres correcciones a `joiabagur-ia-especificaciones-funcionales-v2.md` §5.8-5.9, con fecha y motivo: el endpoint, el lado del enlace venta↔búsqueda y el desdoble del campo de duración.
- `proyecto-final-plan-changes-openspec.md`: sección de revisiones nueva, ficha C04 reescrita y **obligaciones heredadas** añadidas a las fichas de C15 y C16.
- `proyecto-final-diseno-rag-joiabagur.md`: §11.2 gana la comparación online v0-léxico frente a producción; §15 una limitación sobre retención.
- `modelo-de-datos.md`, `modelo-c4.md`, `epicas.md`, `README.md`, `backend/README.md` y `testing-backend.md`.

### `ai-tooling`

- `CLAUDE.md`: sección nueva sobre cómo leer una suite en rojo (ver *Notas adicionales*).

---

## 🧪 Testing

**35 métodos de test nuevos → 48 casos ejecutados** (los `[Theory]` con `InlineData` expanden). Todos en verde.

| Fichero | Métodos | Qué cubre |
|---|---|---|
| `ProductSearchEventServiceTests` | 17 | Proyección y rank 1-based, truncado y contador real, origen degradado, episodio, reformulación frente a abandono, derivación de rank, producto ausente, última escritura, propiedad, no propagación de fallos, confidencialidad del texto de consulta |
| `ProductSearchEventSchemaTests` | 7 (20 casos) | Tipos `jsonb`, longitud del texto, orden del índice compuesto, nulabilidad de doce columnas, las cuatro reglas de borrado |
| `AiSearchEventsControllerTests` | 10 | `204` con rank derivado, `400` con identificador vacío, `403` ajeno, `403` administrador, `404`, `401`, atribución de venta, ausencia de rutas de lectura, `SET NULL` real, ciclo completo |
| `MigrationModelDriftTests` | 1 | Desfase modelo↔migración, sin contenedor |

Nomenclatura `Método_Escenario_ResultadoEsperado`. Integración con Testcontainers sobre PostgreSQL 15.

Dos comprobaciones fuera de la suite, registradas en `qa.md`:

- **El arnés probado contra sí mismo**: un test desechable que afirmaba lo contrario en tres puntos —tipo de columna, orden del índice y regla de borrado— falló en los tres, confirmando que `SchemaAssert` lee el catálogo real y no repite la expectativa. Se borró después.
- **Línea base medida, no supuesta**: suite completa sobre la rama guardada con `git stash push -u`.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *hay 35 tests nuevos, pero **el porcentaje de cobertura no se ha medido** en esta rama*
- [x] Migración de EF Core incluida si cambia el modelo de datos
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *el contrato no cambia; solo se lee para derivar la longitud del texto de consulta*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — *`--all --strict`: 31 passed, 0 failed*
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff — *ningún `appsettings*.json` ni `.env` aparece en el diff*
- [x] Revisado el impacto en otros componentes del monorepo — *`frontend/`, `ai-service/` y `terraform/` no tienen ni un fichero en el diff*

---

## 🚀 Deployment notes

**Requiere aplicar la migración** `20260811061759_AddProductSearchEventTracking`.

| Aspecto | Detalle |
|---|---|
| Naturaleza | Aditiva: crea `ProductSearchEvents` y añade una columna **nullable** a `Sales`. Sin backfill |
| Reversibilidad | El `Down` elimina la clave foránea, la tabla, el índice y la columna |
| Variables de entorno | **Ninguna nueva**. No hay cambios en `appsettings*.json` ni parámetros SSM |
| Dependencias | **Ninguna nueva**. Ningún `.csproj` cambia en el diff |
| Orden de despliegue | Sin acoplamiento: no hay frontend ni `ai-service` implicados |
| Datos tras el deploy | La tabla queda **vacía** hasta que C15 invoque el servicio (ver *Notas adicionales*) |

---

## 📝 Notas adicionales

### Breaking changes: ninguno

Verificado contra el diff: no se elimina ni renombra ningún endpoint —se añade uno—, ninguna propiedad de DTO existente cambia de nombre o tipo —todos los DTO son nuevos—, `Sale.cs` solo tiene adiciones, la migración es aditiva y reversible, y no se toca `ai-service/openapi.json` ni ninguna clave de configuración.

### Riesgo: alto por rúbrica, contenido en la práctica

Por la tabla de riesgo del repo el conjunto es **alto**: toca entidades de dominio, `ApplicationDbContext` y una migración de EF Core. Lo que lo contiene: todo es aditivo, la columna de `Sales` es nullable y no requiere backfill, nadie la escribe todavía, y las cuatro reglas de borrado están declaradas a mano y afirmadas contra el catálogo real por los tests de esquema.

### Puntos de atención para reviewers

1. **El endpoint no comprueba el punto de venta, y es deliberado.** La garantía la aporta la firma del servicio: `RecordSearchAsync` recibe un `AiCallScope`, cuya única fábrica exige un POS ya validado, así que la fila no puede existir para un POS ajeno porque la búsqueda tampoco pudo. El endpoint comprueba **propiedad del evento**, que es otro eje. Merece escrutinio: es la pieza de la que depende el aislamiento.
2. **El administrador no hace bypass**, contra el patrón uniforme del resto del repo. Un evento de telemetría no se gestiona: es el registro de lo que hizo una persona concreta. Documentado en `backend/README.md` y fijado por `RecordSelection_WhenCallerIsAdminButNotOwner_Returns403`.
3. **Obligación crítica sobre C15.** Si el endpoint de búsqueda no invoca `RecordSearchAsync`, esta capability queda especificada, implementada, probada y **vacía** — compila, los tests pasan y la tabla llega vacía a la entrega. Recogida en el proposal y en la ficha de C15 del plan de changes.
4. **`jsonb` normaliza el documento**: reordena claves y reescribe separadores. Las aserciones sobre esas columnas parsean el JSON en vez de comparar texto, que estaría comprobando el formateo de PostgreSQL.
5. **Cerrojo de migración liberado.** C04 era el primer 🗄️; al archivarse, C07, C08, C19, C27 y C29 pueden abrirse.

### Suite en rojo: no lo introduce esta rama

La suite completa devuelve **633 tests con 51 fallos**, frente a **585 con 52** en la base, medido con la rama guardada. Los 35 tests nuevos pasan y **ninguna clase de esta rama aparece entre los fallos**, comprobado por nombre y no por aritmética.

Al diagnosticarlos apareció algo que no se sabía: los 10 fallos unitarios son **exactamente los que registró el QA de C03**, nombre por nombre, y los ~42 restantes están todos en el árbol de integración, que **nunca se había medido** — necesita Docker, y `test-backend.yml` solo se dispara en `main` y `develop`, mientras todo el Proyecto Final se construye en `ai-eng`. Un árbol de 270 tests lleva semanas sin ejecutarse ni en local ni en CI.

Queda documentado en `CLAUDE.md` (la regla: comparar **nombres** contra una línea base, nunca el recuento) y en `Documentos/testing-backend.md` (inventario con causas raíz). **No se ha arreglado nada**: no pertenece a esta rama y merece un change propio, empezando por el disparador de CI, que es lo que impide que siga creciendo sin que nadie lo vea.

### Nota sobre el diff

El chunk `07-backend-data` viene **truncado** (1635 líneas): es `...Designer.cs`, el snapshot generado por EF Core. Su contenido está espejado en `ApplicationDbContextModelSnapshot.cs`, que sí se revisó completo.



---

<a id="pr-9"></a>
## #9 — feat(ai-service): esquema ai con pgvector, migraciones Alembic y pool acotado (C05)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c05-add-pgvector-schema-foundation` → `ai-eng` |
| Creada | 2026-08-15 |
| Integrada | 2026-08-15 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/9 |

### Descripción

## 📋 Descripción

Añade la capa de persistencia vectorial de `jbg-ai`: extensión `vector`, esquema `ai`, rol de base de datos dedicado, migraciones Alembic y seis tablas vacías con sus índices, más un motor asíncrono con el pool acotado. Hasta ahora `ai-service/` no tenía ni una línea de código de base de datos: `pyproject.toml` no declaraba ningún driver, `config/settings.py` no tenía cadena de conexión y todas las rutas `/v1` respondían desde fixtures bajo `STUB_MODE`.

La particularidad de este change es que **casi ninguno de sus errores produce un error**. Un índice HNSW creado con la *operator class* equivocada existe, no da aviso y simplemente nunca se usa; la tabla de versiones de Alembic nace en `public` sin que nada proteste; un tipo enumerado sobrevive al `downgrade` y rompe el `upgrade` siguiente semanas después. Por eso los tests no son cobertura genérica: cada uno apunta a un fallo mudo concreto, y en `qa.md` queda registrado que los cuatro principales se verificaron **rompiendo a propósito** lo que vigilan.

No cambia ningún comportamiento observable del servicio: las seis tablas nacen vacías, no hay ninguna consulta de similitud en `src/`, `GET /health` responde igual y `ai-service/openapi.json` no se toca.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

**Change de OpenSpec:** `openspec/changes/archive/2026-08-15-add-pgvector-schema-foundation/` (C05, archivado en esta misma rama, 34/34 tareas).
**Historia de usuario:** [HU-AIENG-005](Documentos/Historias/AI-Eng/HU-AIENG-005.md) — épica EP11, ruta crítica 🔴.
**Ticket técnico:** `ticket.md` (T-AIENG-005) dentro del change archivado.

C05 es el cuello de botella de la Ola 1. La cadena que sostiene el hito del 19 de agosto —C11 texto canónico → C13 indexador → C14 recuperación → C15 endpoint → C16 panel— arranca en C11, y C11 no puede escribir un `source_hash` en ninguna parte mientras `ai.product_document` no exista.

C01 dejó la pista preparada a propósito: `backend/docker-compose.yml` ya usaba `pgvector/pgvector:pg15` con el comentario *«that is C05»*, el marcador `db` de pytest ya estaba declarado y `ai-service/tests/README.md` ya reservaba la carpeta `tests/migrations/` por nombre. Esta PR consume esa preparación.

---

## 🔄 Cambios realizados

### `ai-service` — migraciones y motor

- **`migrations/env.py`**: entorno de Alembic con `version_table_schema="ai"`. El valor por defecto crearía `public.alembic_version` y rompería la frontera del diseño §6.3 (*«Python nunca escribe en `public`»*) en la primera migración del lado Python. `_provision()` crea esquema y extensión **antes** de que Alembic materialice su tabla de versiones, porque un `CREATE SCHEMA` dentro de `upgrade()` llegaría tarde.
- **`migrations/versions/f46c55c056e2_ai_schema_foundation.py`**: revisión única, escrita a mano. Crea `ai.product_document`, `ai.knowledge_document`, `ai.knowledge_chunk`, `ai.pos_projection`, `ai.co_occurrence` y `ai.sync_failure`, con catorce índices declarados. `downgrade()` borra las seis tablas y **conserva** esquema y extensión.
- **`migrations/bootstrap.sql`**: aprovisionamiento puntual con privilegios de administrador — extensión, esquema, rol `jbg_ai` y sus permisos. Fuera de Alembic porque los roles son objetos de clúster: crearlos desde una migración exigiría privilegio de creación de roles y haría fallar la reversión.
- **`src/jbg_ai/db/engine.py`**: motor asíncrono con `pool_size` configurable, `max_overflow=0`, `pool_timeout=2.0` y `pool_pre_ping=True`. Construcción perezosa vía `get_engine()`; `DatabaseNotConfiguredError` se lanza al pedir sesión, no al arrancar.
- **`src/jbg_ai/config/settings.py`**: `database_url` (opcional, sin defecto) y `db_pool_size` (defecto 5). El validador `blank_database_url_is_absent` trata la cadena vacía como ausente. `canonical_openapi_settings()` los fija para que el entorno no se filtre al contrato.
- **`alembic.ini`**: sin `sqlalchemy.url` — la cadena se lee del entorno. `path_separator = os` para que las rutas de Windows no se troceen por el separador heredado.

### `deps` — dependencias

`ai-service/pyproject.toml`: `alembic>=1.14`, `pgvector>=0.3.6`, `psycopg[binary,pool]>=3.2` y `sqlalchemy[asyncio]>=2.0.36` en runtime; `testcontainers[postgres]>=4.9` en `dev`. Alembic va en runtime, no en dev, para que C17 pueda migrar desde el contenedor.

> El diff de `uv.lock` viene **resumido** por el troceador (chunk `04-deps`, `truncated: true`): su análisis se apoya en las cabeceras de hunk y en el `pyproject.toml`, que sí está completo.

### `infra` — contenedor y Compose

- **`ai-service/Dockerfile`**: `COPY alembic.ini ./` y `COPY migrations ./migrations`, después de `uv sync` para no invalidar la capa de dependencias. Sin esto la imagen no contiene las migraciones y **C17 no podría migrar en producción**.
- **`backend/docker-compose.yml`**: `DATABASE_URL` en el servicio `jbg-ai`, resolviendo `postgres` por nombre de red en el puerto interno 5432 (no el 5433 publicado). Sin `depends_on`: el motor es perezoso. El comentario del servicio `postgres` deja de decir *«that is C05»* y nombra `bootstrap.sql`.

### `tests` — 50 tests nuevos

- **`tests/migrations/conftest.py`**: contenedor `pgvector/pgvector:pg15` de ámbito de sesión y **una base de datos nueva por test**; `pytest.skip` con motivo cuando Docker no responde. El fixture `run_bootstrap` ejecuta `bootstrap.sql` con psql dentro del contenedor, porque el script usa meta-comandos (`\gset`, `\if`) que ningún driver interpreta.
- **`tests/migrations/test_ai_schema_migration.py`** (18): los cuatro detectores de la ficha más las aserciones de catálogo — *operator class*, GIN, B-tree, columnas generadas, ausencia de FK hacia `public`, reversibilidad de tres piernas.
- **`tests/migrations/test_ai_schema_invariants.py`** (9): vocabularios cerrados, orientación y unicidad del par de co-ocurrencia, cascada de conocimiento, frescura de la proyección.
- **`tests/migrations/test_bootstrap_and_privileges.py`** (7): `bootstrap.sql` ejecutado de verdad, su idempotencia, el rol migrando sin privilegio de extensión y las dos negativas sobre `public`.
- **`tests/db/test_engine.py`** (9) y **`tests/db/test_boots_without_database.py`** (3): tope del pool, construcción perezosa, y arranque sin base de datos.
- **`tests/config/test_settings.py`**: cuatro casos para los ajustes nuevos.
- **`tests/support/paths.py`** y **`settings.py`**: rutas de Alembic ancladas una vez, y `database_url` fijado a `None` en `build_settings()` para que la variable de entorno de un desarrollador no altere los tests.

### `openspec` — specs y archivado

- **Nueva capability `openspec/specs/ai-vector-schema/spec.md`** con 15 requisitos.
- **`ai-service-runtime`**: modificado el requisito de configuración para incluir los dos ajustes opcionales.
- **`ai-service-dev-compose`**: modificados dos requisitos, reescritos además en términos atemporales — decían *«this change»* y *«until a later change»*, autorreferencias que en una spec viva ya no tienen antecedente.
- Change movido a `openspec/changes/archive/2026-08-15-add-pgvector-schema-foundation/`, con `qa.md` y `ticket.md`.

### `docs`

`Documentos/arquitectura.md` (servicio de IA y tabla de Compose), `modelo-c4.md` (nivel 2, nivel 3 y el diagrama Mermaid, con el componente `Persistence`), `modelo-de-datos.md` (sección nueva del esquema `ai` y sus índices), `epicas.md` (EP11), `openspec/project.md` y `openspec/config.yaml` (stack y contexto condensado), `README.md` §1.2, `ai-service/README.md` y `ai-service/tests/README.md`. En `proyecto-final-plan-changes-openspec.md` §0 se registran **dos lagunas del propio plan**: `ai.query_log` no la reclama ninguna ficha, y no existe integración continua para Python.

---

## 🧪 Testing

`uv run --system-certs pytest` desde `ai-service/`:

| Ejecución | Resultado |
|---|---|
| Con Docker | **127 passed** |
| Sin Docker (`DOCKER_HOST` inalcanzable) | **93 passed, 34 skipped** |
| Línea base (antes de este change) | 77 passed |

Los 34 tests marcados `db` levantan un contenedor efímero y **se omiten, no fallan**, cuando Docker no responde: no hay flujo de CI que ejecute la suite de Python, y unos rojos permanentes en local enseñarían a ignorar el rojo. La contrapartida está dicha en `ai-service/README.md`: una ejecución verde no prueba por sí sola que la migración se haya ejercitado.

`qa.md` §4 registra las cinco roturas deliberadas con las que se verificó que los detectores no son vacuos — sustituir `vector_cosine_ops` por `vector_l2_ops` pone en rojo dos tests con el mensaje que explica por qué el índice quedaría inservible, y `CREATE INDEX` no emite ningún aviso.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — 50 tests nuevos en `ai-service`; los umbrales citados son de backend/frontend, que esta PR no toca
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: `backend/` no cambia salvo `docker-compose.yml`; la migración es Alembic
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**: el contrato no cambia y el snapshot no está en el diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: 32 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`) — ver nota abajo sobre el placeholder de Compose
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

**Esta PR no despliega nada.** El aprovisionamiento contra RDS y el despliegue del contenedor son alcance de **C17**, y no se ha ejecutado nada contra producción.

Cuando llegue ese momento, el orden es:

1. **Una vez, con el usuario maestro de RDS**: `ai-service/migrations/bootstrap.sql`, con la contraseña desde SSM `/jpv/prod/*`. Crea extensión, esquema, rol y permisos.
2. **Con el rol `jbg_ai`**: `alembic upgrade head` desde el contenedor. Funciona sin privilegio para instalar extensiones porque el aprovisionamiento **comprueba antes de crear** en lugar de fiarse de `IF NOT EXISTS`.

Variables nuevas, ambas **opcionales**: `DATABASE_URL` y `DB_POOL_SIZE` (defecto 5). Su ausencia no impide arrancar — es un requisito de la spec `ai-service-dev-compose`, no un descuido.

**En local**, tras esta PR: `docker compose up -d postgres` desde `backend/`, ejecutar `bootstrap.sql` una vez y `uv run alembic upgrade head`. El procedimiento está en `ai-service/README.md`.

**Rollback**: `alembic downgrade base` borra las seis tablas y conserva esquema y extensión. Es inocuo mientras las tablas estén vacías; deja de serlo en cuanto C13 empiece a poblarlas.

---

## 📝 Notas adicionales

**Sin breaking changes.** No cambia ningún contrato REST, ni el snapshot OpenAPI, ni el comportamiento observable del servicio. La variable de Compose es aditiva y opcional. `ai-service/openapi.json` no aparece en el diff, y `test_openapi_snapshot_is_stable` sigue en verde.

**Sobre el checklist de credenciales.** El diff añade `DATABASE_URL: postgresql+psycopg://jbg_ai:local-dev-ai-password@postgres:5432/joiabagur_pv` en `backend/docker-compose.yml`. Es un **placeholder de desarrollo**, misma convención que el `JWT_SECRET: local-dev-jwt-secret-...` que ya vivía en ese fichero desde C01, y apunta a un contenedor local. La credencial de producción sale de SSM en C17. Se señala explícitamente para que el reviewer lo vea como decisión, no como descuido.

**Un defecto de diseño corregido durante la implementación**, registrado con fecha en `design.md` §4. La decisión afirmaba que `IF NOT EXISTS` bastaba para que el aprovisionamiento fuera un no-op inocuo para un rol sin privilegios. Es falso: PostgreSQL evalúa el privilegio **antes** del cortocircuito, así que `CREATE SCHEMA IF NOT EXISTS ai` falla con *permission denied* aunque el esquema ya exista — rompiendo justo el camino de RDS que la decisión pretendía habilitar. Apareció al migrar por primera vez como `jbg_ai` en lugar de como superusuario. La decisión sigue en pie; cambió su mecanismo, y los requisitos de la spec no se tocaron porque describían el resultado, no el mecanismo.

**Hallazgo de plataforma sin corrección de código.** psycopg asíncrono no funciona con el `ProactorEventLoop`, el event loop por defecto de Python en Windows. No afecta a producción (contenedor Linux) ni a los tests (Alembic es síncrono), solo a levantar uvicorn directamente en Windows cuando una ruta llegue a tocar la base de datos — situación que no existe hasta C13/C14. Documentado en `ai-service/README.md`; cambiar el event loop global desde un módulo de librería sería peor que el problema.

**Decisiones que un reviewer querrá cuestionar**, todas con su motivo en `design.md`:

| Decisión | Por qué |
|---|---|
| Extensión en `public`, no en `ai` | Instalarla en `ai` obligaría a cualificar el tipo como `ai.vector(1536)` y a manipular `search_path` en cada conexión, para siempre. La regla de propiedad habla de datos, no de instalación de extensiones |
| `text` + `CHECK` en vez de `ENUM` | Un tipo enumerado sobrevive al borrado de su tabla y rompe el `upgrade` siguiente. Además los vocabularios se deciden en C09 y C23 |
| Migración a mano, sin modelos ORM | `autogenerate` no expresa *operator classes* de HNSW, GIN sobre arrays ni columnas generadas |
| `m=16`, `ef_construction=128` explícitos | El defecto de pgvector es 64; 128 es el valor que fijan los apuntes S8 para 1536 dimensiones |
| Sin FK hacia `public` | Acoplaría el esquema `ai` al ciclo de vida de las tablas de EF Core |

**Limitaciones declaradas.** No se aplica `halfvec` (que S8 recomienda «desde el día uno» para producción real), ni `hnsw.iterative_scan`, ni `CREATE INDEX CONCURRENTLY`, ni el ciclo `VACUUM`/`REINDEX`. A ~1.500 vectores ninguno cambia una cifra medible; se declaran para el README de C39 como decisiones, no como olvidos.

**Dos lagunas del plan quedan abiertas** y registradas en `proyecto-final-plan-changes-openspec.md` §0: `ai.query_log` aparece en el diseño §7.2 y **ninguna ficha la reclama** (C05 la deja sin crear a propósito), y **no existe `test-ai-service.yml`** — nada ejecuta `uv run pytest` en CI, que es lo que condiciona la decisión de omitir los tests de base de datos en lugar de fallar.



---

<a id="pr-10"></a>
## #10 — feat(ai): perfil IA revisable del catálogo con revisión híbrida por campo (C08)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c08-add-product-ai-profile-entity` → `ai-eng` |
| Creada | 2026-08-16 |
| Integrada | 2026-08-16 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/10 |

### Descripción

## 📋 Descripción

Entrega C08 (`add-product-ai-profile-entity`): el perfil IA revisable del catálogo, con la confianza y la **procedencia de cada campo**, y la política híbrida de revisión que se apoya en ellas.

El catálogo no tenía ningún atributo estructurado con el que buscar por semántica — `Product` guarda SKU, nombre, descripción, precio y colección, y nada más. Todo `PieceType`, `MaterialsJson`, `StoneType` y `SizeLabel` nace aquí, y con ellos la pregunta de quién responde de cada uno: un atributo inferido por un modelo y aprobado por nadie llega a una operadora que lo repite delante de un cliente.

La respuesta es la revisión híbrida por campo: un atributo sensible que **infirió** un modelo necesita a una persona; el mismo atributo producido por una **regla determinista**, no; y las etiquetas comerciales se auto-aprueban por encima de un umbral configurable. Esa regla es la que obligó a renegociar el contrato de enriquecimiento, que no transportaba la procedencia y por tanto la hacía inimplementable.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [x] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change OpenSpec**: `openspec/changes/archive/2026-08-16-add-product-ai-profile-entity/` (39/39 tareas, 4/4 artefactos, archivado)
- **Historia de usuario**: [HU-AIENG-008](Documentos/Historias/AI-Eng/HU-AIENG-008.md) · **Ticket**: `T-AIENG-008`
- **Épica**: EP12 — Corpus y Enriquecimiento del Catálogo · **Ola 1** del Proyecto Final

**Quién estaba esperando esto.** C12 (feeds de indexación, en la ruta crítica) tiene C08 como prerrequisito y filtra su feed por el estado de aprobación del perfil. C28 promete al README la tasa de corrección del extractor y el tiempo medio de revisión, y **no tiene turno de migración**: si C08 no le reservaba dónde guardarlo, esas métricas no se podrían calcular nunca.

Este PR ocupa además el **turno único de migración de EF Core** que comparte con C07, C19, C27 y C29.

---

## 🔄 Cambios realizados

### `backend-domain` · `backend-data` — entidad y persistencia

- `Domain/Entities/ProductAiProfile.cs`: valores vigentes, confianza y procedencia por campo, propuesta cruda inmutable, hash de entradas y bloque de revisión. **Sin propiedad de navegación desde `Product`**.
- `Domain/Enums/ProfileReviewStatus.cs` (`Pending`/`Approved`/`Rejected`) y `ProfileReviewOrigin.cs` (`AutoBulk`/`Human`) — **columnas ortogonales**: el feed de indexación selecciona por estado, las métricas de revisión humana por origen, y un único valor combinado haría que una de las dos consultas mintiera.
- `Infrastructure/Data/Configurations/ProductAiProfileConfiguration.cs`: siete columnas `jsonb`, **índice único** sobre `ProductId`, índices `(ReviewStatus)` y `(ReviewStatus, ReviewOrigin)`, y `RESTRICT` en las dos claves foráneas. Todo declarado a mano porque **equivocarse en cualquiera de ellas no produce ningún error**.
- Migración `20260816113455_AddProductAiProfile`.

### `ai-contracts` — contrato de enriquecimiento renegociado 💥

- `ai-service/src/jbg_ai/api/schemas/enrich.py`: `ProposedValue` con `source` (`rule` \| `inferred`), campos `piece_type`, `stone_type` y `size_label`, desglose de `tags` en `color_tags`/`style_tags`/`occasion_tags`, y `prompt_version` en la respuesta.
- `ai-service/src/jbg_ai/api/auth.py`: `pos_id` pasa a `str | None`; `decode_service_token` recibe qué claims exigir. `BASE_CLAIMS` / `CATALOG_CLAIMS`.
- `ai-service/src/jbg_ai/api/deps.py`: `get_catalog_principal` nuevo. **`get_service_principal` no cambia.**
- `ai-service/openapi.json` regenerado con el perfil canónico.

### `ai-service` — stub y enrutado

- `routers/enrich.py` pasa a `get_catalog_principal`. Recuperación, asistencia e inventario se quedan igual.
- `stubs/responses.py`: fixtures que **ejercitan ambas procedencias** y etiquetas a ambos lados de un umbral plausible. Sin esa variedad, una política que no exime nada pasaría sus propios tests.

### `backend-api` — scope de catálogo y superficie HTTP

- `DTOs/Ai/AiCallScope.cs` 💥: `PointOfSaleId` pasa a `Guid?` y aparece `ForCatalog(userId, role)`. Exactamente **dos** caminos de construcción, ningún centinela.
- `DTOs/Ai/AiCallScopeKind.cs`, `AiProposedValue.cs`, `AiEnrichRequest.cs`, `AiEnrichResponse.cs`, `EnrichBatchDtos.cs`.
- `API/Controllers/AiCatalogController.cs`: `POST /api/ai/catalog/enrich-batch`, **solo Administrador**, validador invocado explícitamente (el proyecto no cablea pipeline automático) y traducción del 501 a **503 nombrando C09**.

### `backend-application` — cliente, política y caso de uso

- `Services/AiGatewayClient.cs`: `EnrichAsync`, más la guarda que **rechaza un scope de catálogo en recuperación antes de emitir la petición**.
- `Extensions/AiGatewayServiceCollectionExtensions.cs`: cliente con nombre `ai-enrich`, **cortacircuitos aislado** y **sin reintento** — un reintento sobre una extracción duplica coste de modelo sin razón para esperar otro resultado.
- `Services/ProfileReviewPolicy.cs` + `Interfaces/IProfileReviewPolicy.cs`: clase **pura**, sin base de datos ni HTTP. Umbrales en `Configuration/ProfileReviewOptions.cs`, validados al arranque.
- `Services/ProductAiProfileService.cs`: descarte por hash **antes** de llamar al gateway, modos `Routed`/`AutoBulk`, y traducción de la carrera de unicidad.
- `Services/ProductEnrichmentSourceHash.cs`: SHA-256 de las **entradas**.
- `Services/AiServiceTokenFactory.cs`: emite `pos_id` **solo** cuando el scope lo tiene.
- `Services/ProductSearchEventService.cs`: guarda por el paso de `PointOfSaleId` a nullable (ver Notas).

### `backend-misc`

- `API/Program.cs`: registro de `AddProfileReview(builder.Configuration)`.

### `openspec` · `docs`

- Capability nueva `product-ai-profile` (10 requisitos / 31 escenarios) y tres specs vivas modificadas.
- `Documentos/arquitectura.md`: corregida una **afirmación falsa** — decía que `pos_id` es claim obligatorio siempre.
- `Documentos/modelo-c4.md`: bloque de servicios del Proyecto Final de IA, incluido el `ProductSearchEventService` que C04 nunca añadió, y diagrama Mermaid en coherencia.
- `Documentos/modelo-de-datos.md`, `Documentos/testing-backend.md`, `Documentos/epicas.md`, `README.md`, `backend/README.md`, `ai-service/README.md`, `ai-service/tests/README.md`, `openspec/project.md`.

---

## 🧪 Testing

**+96 tests** (la suite de .NET pasa de 633 a 729; la de Python de 127 a 139).

**Ficheros nuevos (.NET)** — `ProductAiProfileSchemaTests` (29, Testcontainers), `AiCatalogControllerTests` (9, Testcontainers), `ProfileReviewPolicyTests` (11, puros), `ProductAiProfileServiceTests` (10, mock estricto), `ProductEnrichmentSourceHashTests` (7), `AiGatewayEnrichTests` (7).

**Ampliados** — `AiContractSnapshotTests` (+9), `AiCallScopeTests` (+5), `AiGatewayRegistrationTests` y `ProfileReviewRegistrationTests` (+7), `AiServiceTokenFactoryTests` (+1), `AiGatewayClientTests` (+1).

**Python** — `test_contracts.py` (+6) y `test_auth.py` (+6).

**Tres cosas que conviene saber al revisar los tests:**

1. **Los detectores de esquema se verificaron fallando.** Se rompió a propósito lo que cada uno vigila —`jsonb`→`text`, quitar la unicidad, `RESTRICT`→`CASCADE`— y fallaron **exactamente los tres correspondientes y ninguno más**. Detalle en `qa.md` §4.
2. **La comparación con la línea base es por nombres, no por recuento.** `CLAUDE.md` lo advierte y esta rama lo confirmó: dos ejecuciones sobre el mismo commit dieron **48 y 51** fallos. Aparecieron tres nombres de `InventoryIntegrationTests` que **no** eran regresión — pasan en aislamiento y la siguiente pasada trae otros distintos sobre código idéntico. Ninguno de los 96 tests nuevos falla en ninguna de las cuatro pasadas.
3. **La prueba extremo a extremo se hizo contra el contenedor real**, no contra un *fake*: token de catálogo sin `pos_id` → 200 en enriquecimiento; **el mismo token → 401 en recuperación**; token con punto de venta → 200. Es lo único que ninguna prueba en proceso podía demostrar.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate --all --strict` con **`0 failed`**
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

**Orden de despliegue: `jbg-ai` y el backend .NET van juntos.** Un `jbg-ai` con el contrato antiguo devolvería perfiles sin `source`, y el enrutado los trataría como inferidos — mandando el catálogo entero a una cola de revisión. En desarrollo no se nota porque ambos suben con `docker compose`.

**Migración**: puramente aditiva (una tabla nueva, ninguna columna en tablas existentes), así que puede aplicarse antes que el código. El `Down` borra una sola tabla y no deja objetos huérfanos — no hay tipos `ENUM`.

**Configuración nueva**, toda opcional y con valores por defecto documentados:

| Clave | Defecto | Qué gobierna |
|---|---|---|
| `AiGateway:EnrichTimeoutMs` | `120000` | Presupuesto de un lote de enriquecimiento |
| `ProfileReview:TagAutoApproveThreshold` | `0.80` | Umbral de auto-aprobación de etiquetas |
| `ProfileReview:MinimumFieldConfidence` | `0.50` | Suelo de confianza |

Los dos de `ProfileReview` se validan al arranque: un valor fuera de `[0,1]` **detiene el host** nombrando la clave. Están pensados para recalibrarse contra el golden set de C24, que es la razón de que no sean constantes.

**Rollback**: la migración revierte borrando una tabla; el contrato, restaurando el snapshot anterior. Ningún dato de negocio se pierde — el perfil es derivado y se regenera reejecutando el lote.

---

## 📝 Notas adicionales

### Breaking changes (tres, todos deliberados)

1. **`ai-service/openapi.json` cambia.** La ruta `/v1/enrich/products` **no tenía ningún otro consumidor**: romperla no invalidó una sola línea. Diferirlo a C09 habría obligado a construir la entidad sobre una forma ya sabida insuficiente. El precio fue un snapshot regenerado y dos suites en verde — que es exactamente el mecanismo que C02 montó para este momento.
2. **`AiCallScope.PointOfSaleId` pasa a `Guid?`.** Hoy solo lo leen `AiServiceTokenFactory` y `AiGatewayClient`.
3. **`ServicePrincipal.pos_id` pasa a opcional.** Recuperación, asistencia e inventario **no cambian de comportamiento**: siguen exigiéndolo.

### Puntos de atención para quien revise

**El aislamiento entre puntos de venta tiene dos cierres independientes.** Desde C22 el `pos_id` del token será el único filtro duro del recuperador, así que un scope de catálogo llegando ahí sería una fuga. Lo impiden el cliente .NET (rechaza antes de emitir) **y** `jbg-ai` (sigue exigiendo el claim en esas rutas). Que uno se relaje por descuido no abre la puerta — es el punto que más merece una segunda mirada.

**`SourceHash` no es el `source_hash` de C11.** Este cubre las **entradas** del enriquecimiento; el de Python cubrirá el `doc_text` canónico para decidir si recalcula embedding. Nombres casi idénticos, propósitos distintos.

**El modo `AutoBulk` es un atajo declarado, no una trampa.** Aprueba todo para que el corpus se pueda indexar, **pero `FieldConfidenceJson` y `FieldSourceJson` siguen registrando lo que el enrutado habría decidido**, así que después se puede responder con un número qué porcentaje del corpus no miró nadie.

**Una carrera de unicidad se traduce, no revienta el lote.** El servicio hacía leer-luego-escribir sin capturar `DbUpdateException`, y la ventana **es la llamada al modelo**, de segundos: dos administradores con lotes solapados producían un 500. Ahora se sueltan las filas perdedoras y se reportan en `skippedConcurrent`, separado de `failed` porque el producto **sí acabó enriquecido**, solo que por otro. Detección por `SQLSTATE 23505` vía `DbException.SqlState` (BCL), sin acoplar la capa de aplicación a Npgsql.

**Efecto colateral en C04.** `PointOfSaleId` nullable rompió `ProductSearchEventService`. Se resolvió con una guarda **dentro** del `try` existente: se traga y se registra como cualquier otro fallo. La garantía de C04 —la telemetría nunca rompe una búsqueda— pesa más que sacar a la luz un error que el compilador ya no puede cazar. **Es discutible y está documentada como tal** en `tasks.md` 5.4.

### Limitaciones declaradas

- **Enriquecimiento síncrono, lotes de 50.** El catálogo completo son ~20 llamadas encadenadas. Sin cola, sin reanudación, sin progreso observable. Aceptable a esta escala; no lo sería a escala real.
- **Sin medición de carga**: `EnrichTimeoutMs = 120 s` es una estimación razonada, no un dato — no se ha enriquecido un lote de 50 contra un modelo real.
- **`ReviewDurationMs` y `ReviewOrigin = Human` no tienen camino de escritura**: los abre C28. Las columnas existen y su semántica está probada, pero nadie las llena todavía.
- **Obligación heredada por C09**: el contrato ya declara `source`; el pipeline debe **producirlo de verdad**. Si devolviera todo como `inferred`, la revisión híbrida seguiría compilando y mandaría el catálogo entero a una cola que nadie tiene tiempo de vaciar. Registrado en el §0 del plan de changes.

### Nota de revisión

`chunks/10-backend-data.diff` viene **truncado** en el análisis: es el `Designer.cs` de la migración, generado por EF Core.

Los deltas `MODIFIED` de las tres specs vivas ya están sincronizados en `openspec/specs/`, así que **sustituyen literalmente** lo que había. Merecen lectura: relajan garantías que C02 y C03 habían escrito en absoluto, de forma intencionada y razonada en `design.md`.



---

<a id="pr-11"></a>
## #11 — feat(backend): familias de producto como entidad de negocio editable (C07)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c07-add-product-family-entity` → `ai-eng` |
| Creada | 2026-08-16 |
| Integrada | 2026-08-16 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/11 |

### Descripción

## 📋 Descripción

Añade `ProductFamily` y `ProductFamilyMember` al dominio .NET: los productos que son **la misma pieza en varias variantes** —el mismo anillo en tallas S, M y L— agrupados como entidad de negocio editable. Sustituye a `VariantGroupKey`, la clave textual que las especificaciones v2 guardaban dentro del perfil de IA y que la decisión 2 de la revisión rechazó por tres motivos que son tres requisitos: se rompía por un guion y dejaba de agrupar justo donde el aviso importaba, no la podía corregir un administrador —y si la corregía, el siguiente enriquecimiento la machacaba—, y sin identidad propia no había contra qué comparar para detectar productos huérfanos.

La pertenencia se **declara como lista completa**: lo que no aparece en la petición deja de ser miembro y el orden sale de la posición en el array, de modo que huecos y posiciones duplicadas no se pueden expresar. Que un producto pertenezca **a una familia como máximo** lo garantiza un índice único de la base de datos y no una comprobación del servicio: una comprobación deja abierta la carrera entre dos administradores y, peor, un segundo miembro no produce ningún error — se manifestaría aguas abajo como dos `family_id` emitidos para un mismo producto.

`Product` **no cambia**: ni una columna ni una propiedad de navegación. El contrato de `jbg-ai` tampoco: `family_id` y `variant_label` ya viajaban en él desde C02 y `ai.product_document` ya los reservaba desde C05. Este change solo produce el dato del lado .NET.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

El caso de negocio es el crítico del proyecto: tres anillos con la misma foto y tallas distintas producen tres resultados indistinguibles en cualquier buscador, y el error de venta no se detecta hasta que el cliente vuelve. La recuperación semántica no lo arregla —los tres son legítimamente parecidos y devolverlos los tres es lo correcto—; lo que falta es que el sistema **sepa que son variantes** y pueda exigir que se confirme cuál.

- **Change OpenSpec**: `openspec/changes/archive/2026-08-17-add-product-family-entity/` (C07, esquema `spec-driven`, 35/35 tareas, archivado en esta rama)
- **HU**: `Documentos/Historias/AI-Eng/HU-AIENG-007.md` · **Ticket**: `T-AIENG-007`, en el `ticket.md` del change
- **Épica**: EP13 — Familias de Producto y Desambiguación de Variantes
- **Desbloquea**: C12 (feed de indexación) 🔴, C18 (propuesta asistida y pantalla) y C30 (venta asistida) 🔴
- **Turno de migración de EF Core**: este change lo ocupaba y lo **libera** al mergearse

---

## 🔄 Cambios realizados

### `backend-domain` (2 archivos, +88)

- `Domain/Entities/ProductFamily.cs` — nombre, descripción, colección de miembros y las tres columnas de aprobación (`Origin`, `ApprovedByUserId`, `ApprovedAt`) **reservadas y sin uso en este change**.
- `Domain/Entities/ProductFamilyMember.cs` — `ProductFamilyId`, `ProductId`, `VariantLabel` (nulable) y `SortOrder`. Sin navegación hacia `Product`.
- `Domain/Enums/FamilyOrigin.cs` — `Manual = 1` | `AiApproved = 2`.
- `Domain/Interfaces/Repositories/IProductFamilyRepository.cs` — `GetWithMembersAsync`, `GetByProductIdAsync`, `GetMembershipsInOtherFamiliesAsync`, `AddMembersAsync`, `RemoveMembersAsync`.

Las cotas de longitud (`ProductFamily.NameMaxLength`, `ProductFamilyMember.VariantLabelMaxLength`) viven en las **entidades** y no en las configuraciones de EF: los validadores las necesitan y `JoiabagurPV.Application` no referencia `JoiabagurPV.Infrastructure`.

### `backend-data` (9 archivos, +2473)

- `Configurations/ProductFamilyConfiguration.cs` y `ProductFamilyMemberConfiguration.cs` — **tres índices únicos** (`ProductId` global, `(ProductFamilyId, SortOrder)`, `(ProductFamilyId, VariantLabel)`), índice sobre `Name`, índices sobre `UpdatedAt` de ambas tablas para el cursor `since` de C12, `HasConversion<int>()` en `Origin`, `Cascade` de familia a miembros y `Restrict` hacia `Product` y `User`.
- `Migrations/20260816210303_AddProductFamily.cs` (+ `.Designer.cs` y `ApplicationDbContextModelSnapshot.cs`) — **una única migración**.
- `Data/ApplicationDbContext.cs` — dos `DbSet`.
- `Data/Repositories/ProductFamilyRepository.cs` — ordena en el `Include` (`Include(f => f.Members.OrderBy(m => m.SortOrder))`).

> El chunk `05-backend-data.diff` viene **resumido** por tamaño: corresponde al `.Designer.cs` y al snapshot del modelo, ambos generados por `dotnet ef`.

### `backend-application` (5 archivos, +551)

- `Services/ProductFamilyService.cs` — crear, leer, editar metadatos, declarar miembros y consultar por producto. Reemplazo de miembros con **cortocircuito de no-operación** cuando la lista declarada coincide con la vigente, y traducción de la violación de unicidad concurrente leyendo `DbException.SqlState == "23505"` (biblioteca base, no `PostgresException`, para que `Application` no referencie el driver).
- `Interfaces/IProductFamilyService.cs`, `DTOs/Products/ProductFamilyDtos.cs`, `Validators/ProductFamilyValidators.cs`, `Exceptions/ProductFamilyConflictException.cs` — la excepción transporta los productos en conflicto y la familia que los tiene, para que el 409 sea accionable.
- `Extensions/ServiceCollectionExtensions.cs` — registro del servicio.

### `backend-api` (3 archivos, +284)

`Controllers/ProductFamiliesController.cs`, con `[Route("api/product-families")]` y `[Authorize]` a nivel de clase:

| Método | Ruta | Autorización |
|---|---|---|
| `POST` | `/api/product-families` | `Administrator` |
| `GET` | `/api/product-families/{id:guid}` | autenticado |
| `PUT` | `/api/product-families/{id:guid}` | `Administrator` |
| `PUT` | `/api/product-families/{id:guid}/members` | `Administrator` |
| `GET` | `/api/products/{productId:guid}/family` | autenticado |

La última se añade a `Controllers/ProductsController.cs` y distingue **404** (el producto no existe), **204** (existe y no tiene familia) y **200**. La lectura **no se filtra por punto de venta**: la pertenencia a familia es un hecho del catálogo, no del inventario. Validación de FluentValidation invocada **explícitamente** en el controlador, porque el proyecto registra validadores sin pipeline automático.

### `backend-infrastructure` (1 archivo, +3)

`Extensions/ServiceCollectionExtensions.cs` — registro de `IProductFamilyRepository`.

### `tests` (3 archivos, +923)

`ProductFamilySchemaTests.cs` (17), `ProductFamiliesControllerTests.cs` (25) y la retirada de `ProductFamilyMother` de `TestHelpers/Mothers/TestDataMother.cs`, sustituida por un comentario que explica por qué no está.

### `openspec` (9 archivos, +1244)

Change archivado en `openspec/changes/archive/2026-08-17-add-product-family-entity/` con sus seis artefactos (`proposal`, `design`, `specs`, `tasks`, `ticket`, `qa`), capability **nueva** `openspec/specs/product-family/spec.md` (8 requisitos, 28 escenarios) y `openspec/project.md` con las dos entidades en *Key Entities* y una regla de negocio nueva.

### `docs` (8 archivos, +375/-7)

`HU-AIENG-007.md` (nueva), `modelo-de-datos.md` (las dos entidades con la tabla comparativa frente a `Collection`), `modelo-c4.md` (componente y mapeo EP13), `epicas.md` (EP13), `backend/README.md` (endpoints y matriz), `README.md` (§3.2), `testing-backend.md` (tercera medición de la suite) y el §0 del plan de changes con las desviaciones de la ficha.

---

## 🧪 Testing

**42 tests nuevos, todos en verde**, con nomenclatura `Método_Escenario_ResultadoEsperado`.

- **17 detectores de esquema** (`ProductFamilySchemaTests`) contra el catálogo real de PostgreSQL vía Testcontainers: las tres unicidades, el orden de columnas del índice compuesto, las dos reglas de borrado, nulabilidad y que `Origin` sea `integer` y no un tipo enumerado nativo. **Cada uno verificado rompiendo a propósito lo que vigila**: tres roturas aplicadas a la vez produjeron exactamente tres fallos y ninguno más.
- **25 de integración** (`ProductFamiliesControllerTests`): los cuatro que pedía la ficha del plan, más reordenado, intercambio de etiquetas, ámbito de la etiqueta por familia, cortocircuito de no-operación, huérfano frente a inexistente, la matriz de autorización completa y la carrera perdida.

**Suite completa**: 771 tests / 44 fallos, frente a una línea base de 729 / 49 medida en esta misma rama antes de escribir código. Comparado **por nombres**, no por recuento: un solo nombre nuevo, verde al ejecutarlo en aislamiento y disjunto del ruido de la pasada anterior. Cero fallos en los 42 tests de este change.

> Los 44 rojos restantes son preexistentes y están documentados en `Documentos/testing-backend.md`.

> El chunk `09-tests.diff` viene **resumido** por tamaño; el inventario de tests procede del `manifest.json` y de la ejecución registrada en el `qa.md` del change.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — 42 tests nuevos, **pero la cobertura no se ha medido con herramienta**
- [x] Migración de EF Core incluida si cambia el modelo de datos
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no cambia**: no hay ningún fichero de `ai-service/` en el diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: 34 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo — ninguno: el diff no toca `frontend/`, `ai-service/`, `terraform/` ni `.github/workflows/`

---

## 🚀 Deployment notes

**Requiere aplicar una migración de EF Core**: `20260816210303_AddProductFamily`, que crea `ProductFamilies` y `ProductFamilyMembers`. Solo crea tablas nuevas — no altera ni una columna existente—, así que es compatible hacia atrás y una versión anterior del backend convive con el esquema nuevo.

Sin variables de entorno nuevas, sin dependencias nuevas y sin cambios de infraestructura. **Rollback**: el `Down` de la migración borra las dos tablas; al no haber ninguna clave foránea entrante, no arrastra nada.

Este change ocupaba el **turno único de migración de EF Core** que el plan comparte con C19, C27 y C29; conviene mergear antes de que otro abra el suyo.

---

## 📝 Notas adicionales

**Sin breaking changes.** Los cinco endpoints son nuevos, `Product` no gana ninguna columna ni navegación, ninguna spec viva se modifica —solo se añade una— y `ai-service/openapi.json` no se regenera.

**El fallo que los tests destaparon y el diseño no anticipaba.** `BaseEntity` asigna el `Guid` en el constructor, así que un miembro nuevo **añadido a la colección de navegación** llega al change tracker con clave no vacía, se toma por una fila existente y la escritura sale como `UPDATE` contra nada. Solo se manifiesta cuando una misma petición **borra e inserta a la vez** —reordenar variantes, intercambiar dos etiquetas—; añadir o quitar por separado funciona. Corregido declarando altas y bajas explícitamente por el repositorio. **Es un aviso para C18, C19 y C29**, que van a mover colecciones hijas por el mismo camino, y queda registrado en el §0 del plan de changes y en el `design.md` del change.

**Dos deudas adjudicadas a C12 por escrito**, ambas consecuencia de que la pertenencia se declare como lista completa: un producto que **sale** de una familia pierde su fila y el cursor `since` no puede verlo, y **renombrar** una familia no toca ninguna fila de miembro pese a que el índice denormaliza el nombre. Ninguna se resuelve aquí: el §6.3 del diseño ya tiene el mecanismo —la invalidación que .NET empuja cuando cambia una familia— y ese mecanismo es de C12. Este change deja los índices sobre `UpdatedAt` preparados para que el feed pueda unir por familia.

**Limitaciones declaradas** (detalle en el `qa.md` del change, §7): cobertura sin medir, sin prueba extremo a extremo contra un despliegue, sin datos a escala —las ~350 familias son de C06 y aún no existen— y la reserva para C18 sin ejercer, porque `Origin` se escribe siempre como `Manual`.

**Para quien revise**, tres decisiones que conviene mirar con calma: que el reemplazo de miembros sea declarativo y no incremental; que la etiqueta de variante sea opcional pero única dentro de la familia, apoyándose en que PostgreSQL trata los nulos como distintos; y que el nombre de familia **no** sea único, para no obligar a C18 a inventar sufijos desambiguadores al aprobar ~350 familias por lotes — que es exactamente el problema de la clave generada que este change vino a eliminar.



---

<a id="pr-12"></a>
## #12 — feat(catalog): corpus real enriquecido y pipeline offline C06a

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `feature/add-real-catalog-ingestion-and-text-assist` → `ai-eng` |
| Creada | 2026-08-22 |
| Integrada | 2026-08-22 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/12 |

### Descripción

## 📋 Descripción

C06a entrega el corpus de **436 SKUs reales** y el pipeline offline que lo genera, valida e ingiere. El export xlsx sigue gitignored; el derivado versionado es `data/catalog/real/generated/catalog-real-enriched.jsonl` (`generator_version` `c06a-assist/v2`, semilla `20260822`).

La implementación no vive en `jbg-ai`. El paquete `catalog-pipeline` está en `scripts/catalog/`: lectura del xlsx, agrupación interna para el sorteo de calidad, redacción `catalog-assist/v2` solo en `rich`/`sparse`, copia literal del xlsx en `original`, y `UPDATE` de `Description` por SKU en Postgres local. No hay cliente LLM, no hay migración Alembic de `text_provenance`, no hay cambio de `openapi.json` ni de API .NET.

El change OpenSpec queda archivado y la capability viva es `openspec/specs/real-catalog-corpus/spec.md`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

El catálogo real importado (436 filas) no da texto suficiente para que C09 demuestre sus puertas de cobertura de tags. C06a desbloquea C09 y C10 con un JSONL `data_origin: real` y dos ejes de procedencia (`text_provenance` / `text_quality_tier`) **sin** falsear SKU, nombre, precio ni colección.

Change: `openspec/changes/archive/2026-08-22-add-real-catalog-ingestion-and-text-assist/` (HU-AIENG-006a). La ficha original del plan situaba generadores en `jbg_ai.data` y una columna Alembic; el `design.md` del change documenta la desviación a `scripts/catalog/` y deja la columna para C13.

Sin issue GitHub en los commits.

---

## 🔄 Cambios realizados

### Pipeline y corpus (`misc`)

- Paquete `catalog_pipeline` con CLI `catalog-pipeline` (`cli.py:main`): subcomandos `generate`, `validate`, `spike`, `ingest`.
- `reader.py` lee xlsx/csv (`SKU`, `Name`, `Description`, `Price`, `Collection`).
- `grouping.py:group_products` agrupa por stem + talla (el material solo entra en la etiqueta si hay talla). Esa agrupación **no** se serializa.
- `quality.py:assign_quality` sortea `rich` / `sparse` / `original` por familia, semilla fija.
- `assist.py:draft_description`: `original` copia `SourceRow.description`; `rich`/`sparse` ensamblan prosa de vendedor; `assert_no_meta_copy` / `assert_no_unevidenced_claims` rechazan mención a foto/ficha y claims no evidentes.
- `models.py:EnrichedRecord.to_json_dict` emite `sku`, `name`, `description`, `price`, `collection_name`, `data_origin`, `text_provenance`, `text_quality_tier` (y `product_id` solo si existe). `validate.py:assert_payload_omits_family_fields` prohíbe `variant_group_key` / `variant_label` / `family_seed` en el JSONL.
- `ingest.py:run_ingest` + `PostgresCatalogStore.update_description`: `UPDATE public."Products" SET "Description" = %s, "UpdatedAt" = NOW() WHERE "SKU" = %s`. Transacción; rollback si cambia identidad o el `COUNT(*)` de filas. SKUs sin match se listan, no se insertan. Conexión vía `JPV_PGHOST` / `JPV_PGPORT` / `JPV_PGDATABASE` / `JPV_PGUSER` / `JPV_PGPASSWORD`.
- `.gitignore`: excepción `!data/catalog/real/generated/**`. El xlsx sigue ignorado.
- Corpus commiteado: 436 líneas; sidecar `catalog-real-enriched.meta.json` con `product_count: 436`, tiers 293/94/49 (`rich`/`sparse`/`original` → 67.20 / 21.56 / 11.24 %), `model: null`, agrupación 354 grupos (44 multi, 310 unarios).

### Tests (`tests`)

- pytest en `scripts/catalog/tests/`: grouping, identity, ingest (`FakeCatalogStore`), quality (determinismo de semilla y familia compartida), reader, schema (`test_jsonl_omits_family_seed_fields`), validate (`test_original_tier_keeps_source_description`, tope 1000 caracteres, copy sin foto/ficha).
- Marker `db` en `pyproject.toml` para Postgres real; los tests del diff usan store falso.

### Dependencias (`deps`)

- `scripts/catalog/pyproject.toml`: Python ≥ 3.11, `openpyxl>=3.1`, `psycopg[binary]>=3.2`, pytest en grupo `dev`. `uv.lock` del paquete editable.

### OpenSpec (`openspec`)

- Change archivado en `openspec/changes/archive/2026-08-22-add-real-catalog-ingestion-and-text-assist/` (proposal, design, tasks, ticket, delta spec).
- Spec viva `openspec/specs/real-catalog-corpus/spec.md`.
- `openspec/project.md`: referencia al JSONL/informe/README del pipeline y fila post-impl de `scripts/catalog/README.md`.

### Docs (`docs`)

- HU-AIENG-006a, informe `c06a-catalog-enrichment-report.md`, ficha C06a del plan (🟢 🗄️, Alcance/Tests alineados al entregable), EP12 con C06a hecho.
- `README.md` §2.3: `scripts/catalog/` y `data/catalog/real/generated/`.
- `ai-service/README.md`: C06a **fuera** de este servicio.
- `scripts/catalog/README.md`: comandos y `JPV_PG*`.

### Tooling (`ai-tooling`)

- Área `catalog-pipeline` en las cinco copias de `doc-impact.json` (`scripts/catalog/**`, `data/catalog/real/generated/**`).

---

## 🧪 Testing

- [x] Tests unitarios añadidos en `scripts/catalog/tests/` (pytest; `FakeCatalogStore` para ingest)
- [ ] Tests de integración backend (Testcontainers) — no aplica: el diff no toca `backend/`
- [ ] Tests frontend (Vitest / RTL) — no aplica
- [ ] Tests E2E (Playwright) — no aplica
- [x] `ai-service`: el diff no añade pytest de `jbg-ai` ni toca `openapi.json`
- [ ] Suite ejecutada en CI / local (resultado) — UNKNOWN en el diff
- [ ] QA manual (flujos de usuario)

Para correr el pipeline: `cd scripts/catalog` → `uv sync --system-certs` → `uv run pytest`. Marker `db` si hay Postgres alcanzable.

---

## ✅ Checklist pre-merge

- [ ] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` (el pipeline es un script offline, no un contenedor C4)
- [x] Hay tests para el código nuevo (cobertura % UNKNOWN; no hay umbral de `jbg-ai`/xUnit aquí)
- [x] Migración de EF Core: no aplica (el diff no cambia el modelo .NET)
- [x] `ai-service/openapi.json` no forma parte del diff
- [x] Spec viva `real-catalog-corpus` y change archivado en `openspec/`
- [x] Documentación de `Documentos/` y README actualizada
- [x] Sin secrets ni credenciales en el diff (`JPV_PG*` se leen del entorno; `.env` está en `scripts/catalog/.gitignore`)
- [x] Revisado el impacto en otros componentes: no hay cambios en `backend/src/`, `frontend/` ni `ai-service/src/`

---

## 🚀 Deployment notes

Sin impacto de despliegue en producción (no hay Terraform, Compose, workflows ni imagen de `jbg-ai`).

Ingesta **local** opcional: variables `JPV_PGHOST`, `JPV_PGPORT`, `JPV_PGDATABASE`, `JPV_PGUSER`, `JPV_PGPASSWORD`. El README del pipeline documenta host `localhost:5433` / BD `joiabagur_pv` como convención local, no como recurso nuevo de AWS.

Rollback de código: revertir la rama. El JSONL es el artefacto; un `UPDATE` local de `Description` no se deshace con el merge.

---

## 📝 Notas adicionales

- **No breaking** para consumidores HTTP: no hay contrato `/v1` ni DTO .NET nuevos.
- C18 no debe leer agrupación de este JSONL; C13 materializa `text_provenance` en `ai.product_document`.
- Ratios del sidecar (67.20 / 21.56 / 11.24) quedan dentro de ~70/20/10 ±3 pp del diseño.
- El verify previo a archivar señaló copy de `original` pegado al texto asistido en algunos SKU (`assist.py:_original_missing_from_text`); no es un fallo de identidad y no está “corregido” en este diff.



---

<a id="pr-13"></a>
## #13 — feat(ai-service): añadir CLI y corpus sintético C06b

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `feature/add-synthetic-catalog-augmentation` → `ai-eng` |
| Creada | 2026-08-23 |
| Integrada | 2026-08-23 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/13 |

### Descripción

## 📋 Descripción

C06b inaugura el CLI `python -m jbg_ai.data` (`generate` / `ingest`) en `jbg_ai.data`. El modelo propone `name`, `description` y `price`; el código reserva SKUs con el esquema del real (desde 437, primer libre `SKU440`), sella `data_origin` / `text_provenance` = `synthetic` y asigna `text_quality_tier` por stem de `Name` antes del draft. `jbg_ai.api.main` no importa el paquete. `GET /health` arranca sin `JPV_CATALOG_LLM_*`.

El JSONL versionado (`data/catalog/synthetic/generated/catalog-synthetic.jsonl`, 764 líneas; sidecar `c06b-synth/v3` / `catalog-synth/v3`) acerca el híbrido a 1.200 con los 436 reales. La ingesta es un `INSERT` transaccional local (`JPV_PG*`, `:5433` / `joiabagur_pv`): no hace `UPDATE` de SKUs C06a ni escribe `ProductFamily*`. El change OpenSpec queda archivado y la spec viva `synthetic-catalog-corpus` entra en `openspec/specs/`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

C06a dejó 436 productos reales con texto usable y desbloqueó C09. C11 y C24 necesitan volumen ya ingerido en `.NET`: el índice nace del feed C12, no del JSONL. Un corpus sintético sin `INSERT` no llega al índice.

Change archivado: `openspec/changes/archive/2026-08-23-add-synthetic-catalog-augmentation/`. HU: `Documentos/Historias/AI-Eng/HU-AIENG-006b.md`. Épica EP12. Desviación respecto a la ficha v3 (2026-08-22): no hay generador determinista que calibre precio/familias al real; no se preasignan `ProductFamily`; las colecciones son nombres de diseño, no de canal.

---

## 🔄 Cambios realizados

### ai-service

- Paquete nuevo `ai-service/src/jbg_ai/data/`: `cli.py:cmd_generate` / `cmd_ingest`, `generate.py:generate_corpus` (no pisa JSONL sin `--regenerate-text`), `sku.py:allocate_skus`, `quality.py:fit_description_to_tier`, `families.py:plan_slots` / `expand_base`, `validate.py:validate_records`, `ingest.py:run_ingest` + `PostgresCatalogStore` / `FakeCatalogStore`.
- Prompts `ai-service/prompts/catalog-synth/v1|v2|v3` (markdown + JSON schema). Vigente `catalog-synth/v3`. Puerto `llm.py:CatalogLlm` / `OpenAICatalogLlm`.
- `settings.py`: `jpv_catalog_llm_api_key|model|base_url` opcionales; `canonical_openapi_settings` los fija a `None`. No aparece `openapi.json` en el diff.

### tests

- `ai-service/tests/data/` con `conftest.py:_no_provider_network` (autouse + `forbid_network`).
- `support/fake_llm.py:FakeCatalogLlm`. Tests: `test_sku_follows_real_magnitude_scheme`, `test_generate_does_not_overwrite_without_flag`, `test_ingest_rolls_back_on_sku_or_collection_collision`, `test_settings_do_not_require_llm_key_to_boot`, `test_api_main_does_not_import_jbg_ai_data`, `test_unit_suite_makes_no_provider_calls`.

### misc (corpus)

- `.gitignore`: ignora `backend/.env`; exceptúa solo `data/catalog/synthetic/generated/`.
- JSONL añadido (764 líneas; **chunk 01 truncado**, no se inspeccionó el copy línea a línea). Sidecar: `product_count` 764, `hybrid_total` 1200, `slack_vs_target` 0, tiers 504/173/87, `unassigned_count` 153.

### config / infra / deps

- `backend/.env.example`: `JPV_PG*` y `JPV_CATALOG_LLM_*` (clave vacía). Comentarios de `JPV_RAG_LLM_*` para C09, no inyectados.
- `backend/docker-compose.yml`: comentario que **prohíbe** `env_file: .env` en `jbg-ai`.
- `ai-service/pyproject.toml`: `openai>=1.68.0` + `uv.lock`.

### openspec / docs

- Artefactos en `openspec/changes/archive/2026-08-23-add-synthetic-catalog-augmentation/` (proposal, design, delta spec, tasks 35/35, ticket).
- Spec viva `openspec/specs/synthetic-catalog-corpus/spec.md` (10 requirements).
- `openspec/project.md` / `config.yaml`: target ~1.200, excepción CLI sobre `public`, enlace al corpus C06b.
- Informe `Documentos/Proyecto Final AIEng/informes/c06b-synthetic-catalog-report.md`. Plan, épicas (C06b hecho), README raíz §2.3, `ai-service/README.md`, `scripts/catalog/README.md`.

---

## 🧪 Testing

- [x] `ai-service/tests/data/` — generate (fake), ingest (FakeCatalogStore), SKU, validate, quality, families, sidecar, scope
- [x] `test_settings_do_not_require_llm_key_to_boot`
- [ ] Suite `dotnet test` / frontend — no hay cambios en esos árboles
- [ ] Ingesta Docker y GET familia 204 — manual; el informe lo anota, no hay test HTTP .NET en este diff

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (pytest en `tests/data/`; no aplica umbral .NET/SPA)
- [ ] Migración de EF Core incluida si cambia el modelo de datos
- [ ] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` (`synthetic-catalog-corpus`)
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets de producción en el diff (`backend/.env` gitignored; `.env.example` trae la password local ya documentada del compose)
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

Sin impacto en producción / RDS / SSM. C06b no apunta a RDS.

**Local (host, no el contenedor `jbg-ai`):**

- Copiar `backend/.env.example` → `backend/.env` y rellenar `JPV_CATALOG_LLM_API_KEY` solo para `generate`.
- `uv sync --system-certs` en `ai-service/` (nueva dep `openai`).
- `ingest` usa `JPV_PG*` contra `localhost:5433` / `joiabagur_pv`. Snapshot previo de `"Products"` / `"Collections"` (gitignored).
- No añadir `env_file: .env` al servicio `jbg-ai` del compose.

**Rollback local:** restaurar el snapshot de Postgres. El JSONL se queda: es el corpus, no el estado de la BD.

---

## 📝 Notas adicionales

- **No breaking.** Campos LLM opcionales; `openapi.json` no está en el diff; no hay ruta HTTP nueva.
- Riesgo **medio**: el CLI de host hace `INSERT` en `public` (misma excepción que C06a). El runtime `jbg-ai` no gana ese privilegio.
- El JSONL no lleva `product_id`, `materials`, `family_seed`, `variant_group_key` ni `variant_label`. Familias léxicas S/M/L/XL son solo sufijo de `Name` + precio; C18 sigue siendo quien escribe `ProductFamily*`.
- Chunk 01: el JSONL está resumido (770 líneas > umbral 600). Recuentos y ratios salen del sidecar, no de un muestreo del JSONL en este análisis.
- `HU-AIENG-006b.md` aún cita la ruta activa `openspec/changes/add-synthetic-catalog-augmentation/`; el change vive en `archive/2026-08-23-…`.
- Regenerar texto exige `--regenerate-text` (`generate.py:generate_corpus`). Temperatura > 0: el artefacto en git es la fuente.



---

<a id="pr-14"></a>
## #14 — feat(ai-service): extraer perfiles reales en POST /v1/enrich/products

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c09-add-catalog-enrichment-pipeline` → `ai-eng` |
| Creada | 2026-08-23 |
| Integrada | 2026-08-23 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/14 |

### Descripción

## 📋 Descripción

Sustituye el stub de `POST /v1/enrich/products` cuando `STUB_MODE=false` por el pipeline de `jbg_ai.enrichment`: vocabularios YAML, talla por regex sobre `Name` luego `Description`, LiteLLM a temperatura 0 y confianza por span. Con `STUB_MODE=true` el handler sigue siendo `enrich_products_stub`. El contrato `ai-service/openapi.json` no entra en el diff.

El change OpenSpec `add-catalog-enrichment-pipeline` (C09 / HU-AIENG-009) queda archivado en `openspec/changes/archive/2026-08-23-add-catalog-enrichment-pipeline/` y sincronizado a las specs vivas `catalog-enrichment-pipeline` y `ai-service-runtime`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

C08 ya persiste `ProductAiProfile` y llama a `POST /v1/enrich/products`. En la base, esa ruta usa `require_stub_mode` y `enrich_products_stub`; con stub off responde 501 nombrando C09. El stub marca talla `rule` por índice de lote y la atribuye al SKU; en este catálogo la talla está en el nombre.

Sin extractor real, C08 enruta perfiles del ciclo determinista y C11 no puede construir un `SourceText` honesto. Esta PR entrega el pipeline en Python y no toca `backend/src/` ni el frontend.

- Change: `openspec/changes/archive/2026-08-23-add-catalog-enrichment-pipeline/`
- HU: `Documentos/Historias/AI-Eng/HU-AIENG-009.md`

---

## 🔄 Cambios realizados

### ai-service

- `ai-service/src/jbg_ai/api/routers/enrich.py:enrich_products` pasa a `async def`. Si `stub_mode`, sigue `enrich_products_stub`. Si no hay `JPV_RAG_LLM_API_KEY` ni fake inyectado en `app.state.enrich_llm`, responde **503** (detalle nombra la clave); no 501. Si hay clave, `LiteLlmEnrichClient` + `pipeline.enrich_products`.
- Paquete nuevo `ai-service/src/jbg_ai/enrichment/`: `vocab.py` + `vocabularies.yaml`, `size.py:extract_size` (Name > Description, sin SKU), `confidence.py` (0.85 / 0.45 / 0.20; listas = min), `llm.py:LiteLlmEnrichClient` (temp 0, retry de parse 1 vez), `pipeline.py:assemble_profile` (`title` / `description` / `family_id` / `variant_label` nulos), `audit.py:audit_batch` (unicidad de SKU, vocabulario, cobertura por estrato; no se llama desde el POST).
- Prompt `ai-service/prompts/enrichment/v1.md` (`prompt_version = enrichment/v1`).
- `settings.py`: `jpv_rag_llm_api_key` / `model` / `base_url` opcionales; `jpv_rag_llm_concurrency` default 8; strings en blanco = unset; `canonical_openapi_settings` las pinna a `None`.

### tests

- `tests/enrichment/` con `FakeEnrichLlm` (`tests/support/fake_enrich_llm.py`).
- Auditor: `test_batch_fails_when_sku_is_duplicated`, cobertura por estrato, HTTP 200 con tags vacías.
- `test_stub_mode.py` excluye `/v1/enrich/products` del 501 (`STUB_ONLY_REQUESTS`).
- Settings/health: boot sin `JPV_RAG_LLM_*`.

### deps / infra / config

- `pyproject.toml`: `litellm==1.98.0`, `pyyaml==6.0.3`. `uv.lock` actualizado (chunk resumido a cabeceras de hunk).
- `ai-service/Dockerfile`: `COPY prompts ./prompts`.
- `backend/.env.example`: documenta `JPV_RAG_LLM_MODEL=openai/gpt-4o`, `BASE_URL`, `CONCURRENCY=8` (comentadas; no se inyectan en compose hasta haber clave).

### openspec / docs

- Spec viva nueva `openspec/specs/catalog-enrichment-pipeline/spec.md`.
- `openspec/specs/ai-service-runtime/spec.md`: requisito *RAG LLM settings do not block process boot*.
- Épica EP12, plan C01–C39, `openspec/project.md`, `config.yaml`, README raíz y de `ai-service` alineados.

### ai-tooling (incidental)

- `.cursor/rules/use-powershell.mdc` pasa a `alwaysApply: true` (here-strings, no HEREDOC de bash).

---

## 🧪 Testing

- [x] Suite pytest de `tests/enrichment/` (vocabulario, talla, pipeline, LLM fake, auditor) más ampliaciones en `test_settings.py`, `test_health.py` y `test_stub_mode.py`
- [ ] `dotnet test` — esta PR no toca `backend/src/`
- [ ] Vitest / Playwright — no hay cambios de frontend
- [ ] QA manual / `enrich-batch` AutoBulk sobre los 1.200 — verificación posterior; hace falta `JPV_RAG_LLM_API_KEY`

El diff no incluye salida de pytest; no se afirma un recuento de verdes.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (pytest en `ai-service/tests/enrichment/`; umbral 70 % .NET/FE no aplica)
- [x] Migración de EF Core incluida si cambia el modelo de datos (no aplica)
- [x] `ai-service/openapi.json` no se regenera; el contrato de forma no cambia
- [x] Spec de la capability actualizada en `openspec/` (`catalog-enrichment-pipeline` + delta RAG en `ai-service-runtime`)
- [x] Documentación de `Documentos/` actualizada (EP12, plan de changes, arquitectura)
- [x] Sin secrets ni credenciales en el diff (`backend/.env.example` solo placeholders comentados)
- [x] Revisado el impacto en otros componentes del monorepo (.NET no cambia; Compose local sigue en stub)

---

## 🚀 Deployment notes

- **Imagen `jbg-ai`:** reconstruir para copiar `prompts/` y resolver `litellm` / `pyyaml` del lock. `uv.lock` truncado en el contexto de PR; las pins exactas de aplicación están en `pyproject.toml`.
- **Variables:** `JPV_RAG_LLM_API_KEY` / `MODEL` / `BASE_URL` / `CONCURRENCY` opcionales al boot. Compose local y el snapshot siguen en `STUB_MODE=true` hasta haber clave. Producción: SSM `/jpv/prod/*` (C17); no reutilizar `JPV_CATALOG_LLM_API_KEY`.
- **Comportamiento:** con `STUB_MODE=false` y sin clave, `POST /v1/enrich/products` pasa de 501 a 503. C08 ya mapea 5xx de enrich a 503; no hay cambio de forma JSON.
- **Orden:** desplegar el contenedor `jbg-ai` antes de apuntar enrich-batch a modo real. Backend y frontend no se reconstruyen por este diff.
- **Rollback:** `STUB_MODE=true`. La ruta vuelve al stub. C09 no escribe filas.
- **Post-deploy:** `GET /health` sin clave RAG; enrich real solo con clave. No hay migración Alembic/EF.

---

## 📝 Notas adicionales

- **Breaking:** ninguno de contrato. `openapi.json` no está en el diff. Las settings RAG no son obligatorias. Cambio de comportamiento acotado a stub off + enrich.
- **Riesgo:** medio. Dependencia nueva LiteLLM y llamada real a proveedor en runtime; la suite inyecta fake y no abre sockets. Semáforo default 8.
- **Cruzado:** el único consumidor HTTP sigue siendo `AiGatewayClient.EnrichAsync`. `backend/src/` no cambia; el mensaje 503 de `AiCatalogController` que nombra C09 como futuro queda fuera de esta PR.
- **HU:** `HU-AIENG-009.md` describe el problema en presente («sigue en stub»); es el texto de la historia, no el estado del código.
- **Fuera de alcance:** AutoBulk sobre 1.200, Instructor, migrar C06b a LiteLLM, C11/C12/C18/C20/C28.



---

<a id="pr-15"></a>
## #15 — feat(ai-service): añadir CLI world simulate/ingest (C10)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c10-add-synthetic-world-simulator` → `ai-eng` |
| Creada | 2026-08-23 |
| Integrada | 2026-08-23 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/15 |

### Descripción

## 📋 Descripción

C10 entrega un CLI de host (`python -m jbg_ai.data world simulate|ingest`) que, a partir de un YAML de 12 POS commiteado, simula inventario sesgado y un histórico Poisson y lo inserta en Postgres Docker local. No hay ruta HTTP, no se regenera `openapi.json` y `jbg_ai.api.main` no importa `jbg_ai.data`.

`world simulate` no abre Postgres ni llama a un LLM; emite JSONL con claves `sku` / `pos_code` / `username`. `world ingest` resuelve FKs contra `"Products"` con `JPV_PG*` (host 5433, BD `joiabagur_pv`) en una transacción. El JSONL de ventas y el `pg_dump` quedan gitignored; la receta es `data/world/pos-profiles.yaml` (`generator_version` `c10-world/v1`, seed `20260823`).

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Tras C06a+C06b el catálogo local tiene ~1.200 productos, pero `"PointOfSales"`, `"Inventories"` y `"Sales"` estaban a cero. C19/C22/C27 no pueden demostrar señales ni proyección POS sobre un mundo vacío.

Change OpenSpec archivado: [`openspec/changes/archive/2026-08-23-add-synthetic-world-simulator/`](openspec/changes/archive/2026-08-23-add-synthetic-world-simulator/). Spec viva: `openspec/specs/synthetic-world-simulator/spec.md`. HU: [`Documentos/Historias/AI-Eng/HU-AIENG-010.md`](Documentos/Historias/AI-Eng/HU-AIENG-010.md).

Desviación respecto a la ficha v3 del plan (documentada en `design.md`): módulo `jbg_ai.data.world` en lugar de `generators/`; no se commitea el JSONL; se retira `test_simulation_is_deterministic_for_same_seed`; co-ocurrencia solo por `BulkOperationId`; `is_supply_source` solo en YAML (columna SQL = C19).

Sin issue GitHub en los commits.

---

## 🔄 Cambios realizados

### misc

- `.gitignore`: ignora `data/world/generated/*` y `data/world/backups/*`; exceptúa `.gitkeep`.
- `data/world/pos-profiles.yaml`: censo de 12 códigos (`MAO-TALLER` … `HT-ARTRUTX`), 3 operadores (`op-ciutadella` / `op-fornells` / `op-aeroport`), teléfono `600123456`, huecos `SKU135`/`SKU400`/`SKU418`, `HT-ARTRUTX` con `is_active: false` y `closed_after: 2025-09-30`.

### ai-service

- `cli.py`: `cmd_world_simulate` / `cmd_world_ingest`; subparser anidado `world simulate|ingest`. Flags de `generate`/`ingest` de catálogo intactos (`test_world_cli_does_not_change_catalog_generate_ingest_flags`).
- `world/catalog.py:load_catalog_skus`: lee JSONL C06a+C06b y excluye huecos.
- `world/constants.py`: `GENERATOR_VERSION = c10-world/v1`, `BCRYPT_ROUNDS = 12`, `BCRYPT_PREFIX = b"2a"`, censo y bandas.
- `world/cooccurrence.py`: pares `{product_sku_a, product_sku_b, …}` solo con el mismo `BulkOperationId`.
- `world/profiles.py:load_profiles` / `parse_profiles`: valida censo, teléfono, un solo supply, sin UUID.
- `world/simulate.py`: Poisson, stock no negativo, fechas simuladas (no `NOW()`).
- `world/ingest.py`: fichero nuevo (771 líneas). El chunk de contexto está **truncado** (umbral 600); el comportamiento observable está en los tests (`FakeWorldStore`, rollback, BCrypt).

### tests

Nuevos en `ai-service/tests/data/world/`:

- `test_world_cli_does_not_change_catalog_generate_ingest_flags`
- `test_yaml_census_has_twelve_codes`, `test_phone_is_pinned_and_code_fits_varchar20`, rechazo de YAML inválido
- `test_simulate_does_not_require_postgres`, `test_known_catalog_holes_are_not_sold`, `test_no_sale_without_stock_at_that_pos`, estacionalidad, mix aeropuerto, bulk ~15 %, no cartesiano
- `test_co_occurrence_only_counts_same_bulk_operation`
- `test_ingest_does_not_touch_products_or_collections`, `test_ingest_rolls_back_on_unmatched_sku`, operadores, Artrutx, `test_operator_password_hash_verifies_with_bcrypt`
- `test_unit_suite_makes_no_provider_calls` (fixture `forbid_network`)

No existe `test_simulation_is_deterministic_for_same_seed`.

### deps

- `ai-service/pyproject.toml`: `bcrypt>=4.2.0`; lock `bcrypt` 5.0.0. No es dependencia de boot de `/health`.

### config

- `backend/.env.example`: comentario de `JPV_PG*` incluye C10. No hay variable nueva ni cambio de default.

### docs

- README raíz §2.3: CLI C10 y `data/world/`.
- `ai-service/README.md`: bullet C10, fila `JPV_PG*`, layout `world/`.
- `ai-service/src/jbg_ai/data/README.md`: comandos `world` y one-liner `pg_dump` / restore.
- `ai-service/tests/README.md`: C10 landed en `data/world/`.
- `Documentos/epicas.md` (EP12 / HU-AIENG-010 hecho) e informe `c10-synthetic-world-report.md` (recuentos de la pasada local: 12 POS, 6720 inventario, 22961 ventas).
- Plan C10: bloque **Hecho (2026-08-23)**.

### openspec

- Change archivado en `openspec/changes/archive/2026-08-23-add-synthetic-world-simulator/` (proposal, design, tasks 24/24, ticket, qa, delta spec).
- Spec viva nueva `openspec/specs/synthetic-world-simulator/spec.md` (12 requisitos).
- `openspec/project.md`: excepción CLI host C10, `bcrypt`, enlace al informe.

---

## 🧪 Testing

Tests pytest en el diff (`ai-service/tests/data/world/`). Ejecución de la suite **no** está en el diff → resultado UNKNOWN.

Pasada real simulate/ingest contra Docker: cifras en `informes/c10-synthetic-world-report.md`, no en pytest de tamaño real.

- [x] Tests unitarios/invariantes añadidos en el árbol `tests/data/world/`
- [ ] Suite `uv run pytest` ejecutada en CI de esta PR (UNKNOWN)
- [ ] Login HTTP `op-ciutadella` / `Operator123!` contra la API .NET (fuera del diff)

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` (CLI host, schema `ai` no tocado por el proceso `jbg-ai`)
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — cobertura % no verificable en el diff; hay pytest de world
- [x] Migración de EF Core: no aplica (sin cambio de modelo; `IsSupplySource` SQL es C19)
- [x] `ai-service/openapi.json` no cambia (contrato `/v1` intacto)
- [x] Spec viva `synthetic-world-simulator` en `openspec/specs/`
- [x] Documentación de `Documentos/` y README alineada
- [x] Sin secrets de producción ni SSM; `Operator123!` es password de demo documentado (como `Admin123!`)
- [x] Impacto en otros componentes: solo comentario en `backend/.env.example`; sin frontend ni controladores .NET

---

## 🚀 Deployment notes

Sin impacto de despliegue en producción (RDS / SSM / imagen de runtime). El ingest es solo Docker local (`JPV_PG*`, `:5433`).

- **Deps host:** `uv sync --system-certs` en `ai-service/` por `bcrypt>=4.2.0`.
- **Env:** `JPV_PG*` ya existían para C06b; C10 las reutiliza. Ausencia no bloquea `/health`.
- **Post-merge local (opcional):** `python -m jbg_ai.data world simulate` y `world ingest` si el volumen está vacío; rehydrate = restore del dump, no un segundo ingest (el CLI aborta si los códigos del censo ya existen).
- **Rollback:** revertir la rama. Datos locales: restaurar `pg_dump` o recrear el volumen. El YAML se queda en git.

---

## 📝 Notas adicionales

- **Breaking changes:** ninguno. Flags C06b intactos; OpenAPI congelado; sin settings nuevas de boot.
- **Riesgo:** medio en el volumen Docker local (INSERT masivo a `public`); bajo en producción (D12: solo local).
- **`ingest.py` truncado en el contexto de la PR:** 771 líneas; revisar el fichero completo en el review, no solo el chunk.
- **Co-ocurrencia:** JSONL efímero; no hay `INSERT` a `ai.co_occurrence` (C22/C27).
- **`is_supply_source`:** solo YAML. No hay columna SQL.
- **HU-AIENG-010** describe el estado Docker *antes* del ingest (tablas mundo vacías). El informe C10 documenta el estado *después*.
- Orden de review sugerido: `cli.py` + tests CLI → `profiles.py`/`pos-profiles.yaml` → `simulate.py` → `ingest.py` + tests fake store.



---

<a id="pr-16"></a>
## #16 — feat(ai-service): añadir source-text/v1 y cliente de embeddings 1536d

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c11-add-source-text-and-embedding-client` → `ai-eng` |
| Creada | 2026-08-25 |
| Integrada | 2026-08-25 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/16 |

### Descripción

## 📋 Descripción

Entrega C11 (`add-source-text-and-embedding-client`): biblioteca `jbg_ai.indexing` con el constructor canónico `source-text/v1`, el hash SHA-256 del `doc_text` UTF-8 y un cliente LiteLLM de embeddings 1536-d (`aembedding`) con caché in-memory, batch 64 y backoff 429/5xx.

No hay superficie HTTP nueva. `jbg_ai.api.main` no importa el paquete; `POST /v1/index/sync` y `GET /v1/index/status` siguen siendo el stub de C13. `ai-service/openapi.json` no forma parte del diff. El change queda archivado y las specs vivas (`catalog-source-text`, delta de `ai-service-runtime`) quedan alineadas.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

C05 dejó `ai.product_document` con `doc_text`, `source_hash` y `embedding vector(1536)` vacía; C09 extrae perfiles. Sin un texto canónico estable y un cliente que no vuelva a pagar el modelo si el hash no cambió, C13 tendría que inventar el `SourceText` dentro del upsert y C14/C23 reimplementarían el cliente.

Change OpenSpec archivado: `openspec/changes/archive/2026-08-25-add-source-text-and-embedding-client/`. Historia: `Documentos/Historias/AI-Eng/HU-AIENG-011.md`. Ticket: `T-AIENG-011`. Épica EP12. No hay issue `#NN` en los commits.

---

## 🔄 Cambios realizados

### ai-service

Paquete nuevo `ai-service/src/jbg_ai/indexing/`:

- `source_text.py:ProductSourceText` — DTO con `extra="forbid"`; `sku` y `name` obligatorios; sin `price`, `family_id`, `source` ni proveniencia.
- `source_text.py:build_source_text` — plantilla `source-text/v1` (etiquetas en español, `\n`, listas ordenadas con `str.casefold`); omite la línea si el valor falta o la lista está vacía.
- `source_text.py:hash_source_text` — SHA-256 del `doc_text` UTF-8, hex minúsculas de 64 caracteres.
- `embeddings.py:LiteLlmEmbeddingClient` — puerto `EmbeddingClient` (`async embed`); caché `InMemoryEmbeddingCache` por `(sha256(text), model, version)`; `document_version_key = {model}:1536:source-text/v1` y `model_version_key = {model}:1536`; assert `EMBEDDING_DIM == 1536`; batch `JPV_EMBEDDING_BATCH_SIZE` (default 64); retry 429/5xx con backoff `0.25 * 2**attempt` (máx. 3); no reintenta 4xx de validación; import perezoso de `litellm.aembedding` con `num_retries=0`.
- `embeddings.py:embed` — sin `JPV_EMBEDDING_API_KEY` (o en blanco) lanza `EmbeddingConfigError` y no usa `JPV_RAG_LLM_API_KEY`.
- `errors.py` — `EmbeddingError`, `EmbeddingConfigError`, `EmbeddingDimensionError`.
- `constants.py` — `SOURCE_TEXT_VERSION = "source-text/v1"`, `DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-3-small"`, `EMBEDDING_DIM = 1536`.

Settings en `config/settings.py:Settings`: campos opcionales `jpv_embedding_api_key` / `model` / `base_url` y `jpv_embedding_batch_size` (default 64; string en blanco → 64). `canonical_openapi_settings` pinna key/model/base URL a `None` y batch a 64. No hay cambio en `pyproject.toml` (`litellm==1.98.0` ya estaba).

### tests

- `tests/indexing/test_source_text.py` — estabilidad byte a byte, orden de materiales/tags, cambio de familia, ausentes sin sentinela, precio y UUID fuera, DTO `extra=forbid`.
- `tests/indexing/test_embeddings.py` — version keys, caché, dimensión 384/3072, batch 70→64+6, 4xx sin retry, retry 429 y 5xx, clave propia vs RAG, `api.main` no importa `indexing`, stub C13 intacto.
- `tests/support/fake_embedding_client.py:FakeEmbeddingClient` — inyecta `embed_batch`; no abre sockets.
- `tests/indexing/conftest.py` — no auto-aplica `forbid_network` (mismo patrón que C09: `asyncio.run` en Windows abre `socketpair`).
- Ampliaciones: `tests/config/test_settings.py` (boot sin clave, blank → unset, pin OpenAPI) y `tests/api/test_health.py:test_health_starts_without_embedding_key`.
- `tests/support/settings.py:build_settings` — defaults de embeddings a ausentes / batch 64.

### config

`backend/.env.example`: documenta `JPV_EMBEDDING_API_KEY`, `JPV_EMBEDDING_MODEL=openai/text-embedding-3-small`, `JPV_EMBEDDING_BASE_URL` y `JPV_EMBEDDING_BATCH_SIZE=64`, todas comentadas. Distintas de `JPV_RAG_LLM_*` y `JPV_CATALOG_LLM_*`. `/health` no las exige.

### docs

- Nueva `Documentos/Historias/AI-Eng/HU-AIENG-011.md`.
- Plan de changes: C11 marcado archivado (25 ago) con párrafo de entregable.
- `Documentos/epicas.md` (EP12): HU-AIENG-011 y bloque **Entregable C11**.
- `Documentos/arquitectura.md`, `README.md`, `ai-service/README.md`, `ai-service/tests/README.md`: árbol y tabla `JPV_EMBEDDING_*`; `indexing/` deja de ser nombre reservado.

### openspec

- Change archivado en `openspec/changes/archive/2026-08-25-add-source-text-and-embedding-client/` (proposal, design, ticket, tasks `[x]`, qa, deltas).
- Spec viva nueva `openspec/specs/catalog-source-text/spec.md`.
- `openspec/specs/ai-service-runtime/spec.md`: requisito *Embedding settings do not block process boot*.
- `openspec/config.yaml` y `openspec/project.md`: LiteLLM también para C11 embeddings; fila de docs de contexto C11.

---

## 🧪 Testing

Tests añadidos o ampliados en el diff (pytest, fake inyectable, sin red al proveedor):

- `test_source_text_is_stable_for_same_profile`
- `test_material_order_does_not_change_hash`
- `test_hash_changes_when_family_changes`
- `test_absent_fields_are_omitted_not_sentinel`
- `test_price_is_not_in_source_text`
- `test_family_id_uuid_is_not_in_source_text`
- `test_dto_rejects_blank_sku_and_name` / `test_dto_forbids_price_and_provenance_fields`
- `test_embedding_not_recomputed_when_hash_unchanged`
- `test_vector_dimension_mismatch_is_rejected`
- `test_embedding_batch_is_split_by_setting`
- `test_embed_without_key_fails_without_using_rag_llm_key`
- `test_validation_4xx_is_not_retried` / `test_retry_on_429` / `test_retry_on_5xx`
- `test_main_does_not_import_indexing` / `test_index_routes_still_name_c13`
- `test_health_starts_without_embedding_key` y settings de embeddings

`qa.md` del change registra, sobre el commit de implementación, el alcance C11 en verde (`tests/indexing` + `tests/config` + `test_health.py` + `test_openapi_snapshot.py`) y `openspec validate --all --strict` con 0 failed. Esa pasada no se reejecuta en esta redacción; el checklist de cobertura ≥70% backend/frontend no aplica (no hay código .NET ni frontend en el diff).

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [ ] Migración de EF Core incluida si cambia el modelo de datos
- [ ] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [ ] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

Sin impacto de despliegue en runtime HTTP: `create_app` no importa `indexing`; Compose no necesita inyectar la clave para que `/health` siga en 200.

Variables nuevas (todas opcionales al boot; documentadas en `backend/.env.example` y `ai-service/README.md`):

| Variable | Obligatoria | Default |
|---|---|---|
| `JPV_EMBEDDING_API_KEY` | no al boot; sí al llamar `embed` | ausente |
| `JPV_EMBEDDING_MODEL` | no | en código `openai/text-embedding-3-small` |
| `JPV_EMBEDDING_BASE_URL` | no | vacío = default del proveedor |
| `JPV_EMBEDDING_BATCH_SIZE` | no | 64 |

No hay alta en SSM en este change (C17). No hay cambio de `pyproject.toml` / `uv.lock`, Docker, Terraform ni migraciones Alembic/EF Core. `ai-service/openapi.json` no se regenera.

**Rollback:** revertir el paquete `jbg_ai.indexing` y los campos de settings. No hay filas ni esquema que deshacer.

**Orden:** no aplica acoplamiento de contrato REST. El consumidor real de esta biblioteca es C13 (indexador), aún no en esta PR.

---

## 📝 Notas adicionales

**Breaking changes:** ninguno. Las `JPV_EMBEDDING_*` son opcionales; no hay cambio de DTO/ruta `/v1` ni de JWT interno.

**Riesgo:** bajo. Biblioteca no cableada al HTTP; tests con fake; assert 1536 antes de devolver vectores.

**Frontera de hashes:** `ProductAiProfile.SourceHash` (C08, entradas del extractor) no es `source_hash` de C11 (SHA-256 del `doc_text`). No se unifican.

**Fuera de alcance (no está en el diff):** feed C12, upsert C13, escritura en `ai.product_document`, Redis/tabla de caché, embeddings visuales 1280d, regeneración de OpenAPI.

**Para reviewers:** `embeddings.py` queda congelado para C23 (no reimplementar). Confirmar que `ai-service/openapi.json` sigue intacto y que `jbg_ai.api.main` no importa `jbg_ai.indexing`.



---

<a id="pr-17"></a>
## #17 — feat(api): añadir feeds HTTP de indexación con cursor y API Key

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c12-add-dotnet-index-feed-endpoints` → `ai-eng` |
| Creada | 2026-08-25 |
| Integrada | 2026-08-25 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/17 |

### Descripción

## 📋 Descripción

C12 expone `GET /api/ai/index-feed/catalog` (página fija 50) y `GET /api/ai/index-feed/pos-availability` (página fija 200) para que C13 (y C22) puedan tirar del catálogo y de la disponibilidad POS por HTTP, sin leer `public` por SQL. Autenticación **solo** con header `X-Index-Feed-Key` (`IndexFeed:ApiKey`); un JWT de usuario, una cookie `access_token` o un token C03 responden **401**.

El feed de catálogo pagina por keyset `(watermark, productId)` y emite `kind = upsert` o `tombstone` (`deactivated` / `unapproved`). El de POS es disperso: filas `Inventory` activas como upsert (`qtyBucket`, sin `quantity`) y desasignación como tombstone `unassigned`. `ReplaceMembers` sella `Product.UpdatedAt` vía `ExecuteUpdateAsync` para que altas y bajas de familia entren en el cursor. Sin migración EF, sin push a `POST /v1/index/sync`, sin cambios en `ai-service/` ni en `frontend/`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Python no tiene `SELECT` sobre `public` (C05). C11 construye `doc_text` desde `ProductSourceText`, un DTO que nadie serializaba. Sin este feed, C13 o viola el §6.3 del diseño RAG o nace con `ai.product_document` vacío.

C07 dejó dos fallos mudos: un producto que **sale** de una familia pierde la fila de miembro y el cursor no lo ve; un rename de familia no toca miembros. C08 dejó el predicado `ReviewStatus = Approved`. Reutilizar `AiGateway:JwtSecret` haría válidos los tokens C03 que Python ya posee.

- Change archivado: [`openspec/changes/archive/2026-08-26-add-dotnet-index-feed-endpoints/`](openspec/changes/archive/2026-08-26-add-dotnet-index-feed-endpoints/)
- HU: [`Documentos/Historias/AI-Eng/HU-AIENG-012.md`](Documentos/Historias/AI-Eng/HU-AIENG-012.md)
- Spec viva nueva: `openspec/specs/index-feed/spec.md`

---

## 🔄 Cambios realizados

### backend-api

- `AiIndexFeedController` (`[Route("api/ai/index-feed")]`, `[IndexFeedKey]`, **sin** `[Authorize]`): `GetCatalog` y `GetPosAvailability` con query `since` / `sinceId`.
- DTOs en `IndexFeedDtos.cs`: `IndexFeedPageDto` (`items`, `nextCursor`, `hasMore`, `pageSize`, `aggregateHash`); `CatalogUpsertItemDto` (superset de source-text + `price` / `priceBand` / `familyId`, sin provenance); tombstones `{ kind, productId, reason, at }`; POS upsert con `qtyBucket` y **sin** propiedad `Quantity`.

### backend-misc / config

- `IndexFeedKeyAttribute`: compara `X-Index-Feed-Key` con `IndexFeedKeyComparer.Matches`; 401 si falta o no coincide; el valor del header no se escribe a logs.
- `Program.cs` registra `AddIndexFeed` (fail-fast al arranque).
- Sección `IndexFeed` (`ApiKey`, `ApiKeyPrevious`) en `appsettings.json`, `appsettings.Development.json` y `appsettings.Production.json` (placeholder local `local-dev-index-feed-key-0123456789ab`). `backend/.env.example` documenta `IndexFeed__ApiKey` / `IndexFeed__ApiKeyPrevious` (comentadas). Producción: SSM `/jpv/prod/IndexFeed:ApiKey` en **C17**, no en este diff.

### backend-application

- `IndexFeedOptions` (≥ 32 caracteres, mismo mínimo que `AiGatewayOptions`); `IndexFeedPageSizes.Catalog = 50`, `PosAvailability = 200` (no usan `PaginationConstants.MaxPageSize`).
- `AddIndexFeed`: `ValidateOnStart` — key ausente, corta, o `ApiKeyPrevious` no vacía y corta, detiene el host.
- `IndexFeedService`: sync completo (sin cursor) solo indexables; pull incremental incluye no indexables para tombstones; hash agregado del conjunto **global** (`IndexFeedAggregateHash.OfProductIds` / `OfPosPairs`), no de la página; log `index_feed_page` con prefijo de 12 hex del hash.
- `PriceBand.From` (`price-band/v1`: `lt-30` / `30-80` / `80-150` / `150-300` / `gte-300`; negativo → `ArgumentOutOfRangeException`).
- `QtyBucket.From`: `0` | `1-2` | `3+`.
- `ProductFamilyService.StampCatalogWatermarkAsync`: altas/bajas (y stayers en reorder/label) via `IProductRepository.StampUpdatedAtAsync`. Rename de metadatos: `IProductFamilyRepository.StampUpdatedAtAsync` sobre la familia, no sobre los miembros.

### backend-domain / backend-data / backend-infrastructure

- `IIndexFeedRepository` + filas de proyección (`CatalogFeedRow`, `PosFeedRow`, `PosAssignmentPair`, `PosSalesAggregate`). `GetSalesAggregatesAsync` suma `Sale.Quantity` en 30/90 d **sin** restar `Return`.
- `IndexFeedRepository`: keyset catálogo con watermark `greatest(Product.UpdatedAt, Profile.UpdatedAt, Family.UpdatedAt)`; POS con `greatest(LastUpdatedAt, UpdatedAt)` sobre `Inventory`.
- `StampUpdatedAtAsync` en `ProductRepository` / `ProductFamilyRepository` con `ExecuteUpdateAsync` (porque `UpdatedAt` es `ValueGeneratedOnAddOrUpdate`).
- `ApplicationDbContext.SaveChangesAsync`: en entidades `Modified`, marca `UpdatedAt` como `IsModified = true` para que el UPDATE no omita la columna.
- Registro `IIndexFeedRepository` → `IndexFeedRepository`. Sin tablas nuevas.

### tests

- Integración: `AiIndexFeedAuthTests` (401 con cliente HTTP fresco: JWT de usuario, token C03, sin key, key incorrecta; 200 con key actual y con `ApiKeyPrevious` vía `WithWebHostBuilder`).
- `AiIndexFeedCatalogTests` / `AiIndexFeedPosTests`: cursor, tombstones, hash estable por página, mapeo upsert, familia→catálogo, bucket vs `quantity`, ventas sin netear devoluciones, tope 200.
- `ProductFamiliesControllerTests`: sello de `UpdatedAt` en enter/leave/reorder; lista idéntica no escribe Product; rename no sella miembros.
- Factory: `UseSetting("IndexFeed:ApiKey", IndexFeedTestKeys.ApiKey)`.
- Unitarios: hash, comparador constant-time, fail-fast de options, cortes de `PriceBand`.

### openspec

- Change archivado `2026-08-26-add-dotnet-index-feed-endpoints` (proposal, design, qa, tasks, ticket, deltas).
- Spec viva `openspec/specs/index-feed/spec.md`. `product-family` gana el requisito de sello de watermark.
- `openspec/project.md` / `config.yaml`: paginación de operator lists vs topes del feed; security de la API Key.

### docs

- HU-AIENG-012 y runbook `c12-catalog-autobulk-runbook.md` (procedimiento; **no** se ejecuta AutoBulk en este merge).
- Alineación de `epicas.md`, `arquitectura.md`, `modelo-de-datos.md`, `proyecto-final-plan-changes-openspec.md`, `README.md` §4 y `backend/README.md` (matriz ❌†, env vars, sello de familia).

---

## 🧪 Testing

Presentes en el diff (no se afirma un recuento de ejecución):

- [x] `Feed_WithUserJwt_Returns401` / `Feed_WithC03Token_Returns401` / `Feed_MissingApiKey_Returns401` / `Feed_WrongApiKey_Returns401` / `Feed_WithValidApiKey_Returns200` / `Feed_WithPreviousApiKey_Returns200`
- [x] `CatalogFeed_WithSinceCursor_ReturnsOnlyChangedRows` / `CatalogFeed_EmitsTombstoneWhenProductDeactivated` / `CatalogFeed_ExcludesUnapprovedProfiles` / `CatalogFeed_EmitsTombstoneWhenProfileUnapproved` / `CatalogFeed_NeverApprovedProduct_IsAbsent`
- [x] `Feed_ReturnsAggregateHashForDriftDetection` / `CatalogFeed_Upsert_MapsSourceTextAndIdentifiers`
- [x] `CatalogFeed_AfterReplaceMembers_EmitsLeavingProduct` / `CatalogFeed_AfterFamilyRename_EmitsMembersViaFamilyWatermark`
- [x] `PosAvailabilityFeed_ReturnsBucketNotExactQuantity` / `PosAvailabilityFeed_Unassigned_EmitsTombstone` / `PosAvailabilityFeed_SalesWindows_DoNotSubtractReturns` / `PosAvailabilityFeed_PageSize_Is200`
- [x] `ReplaceMembers_LeavingProduct_StampsUpdatedAt` / `ReplaceMembers_EnteringProduct_StampsUpdatedAt` / `ReplaceMembers_IdenticalList_DoesNotWriteProduct`
- [x] `AddIndexFeed_WhenApiKeyMissing_FailsOnStart` / `PriceBand_Cuts_MatchV1` / `PriceBand_NegativePrice_Throws`
- [ ] Suite global `dotnet test` (no verificable desde el diff; hay fallos preexistentes documentados en `Documentos/testing-backend.md`)
- [ ] AutoBulk de los 1.200 perfiles (fuera de alcance; runbook escrito, no ejecutado)
- [ ] Scalar / QA manual del header

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — cobertura % UNKNOWN
- [x] Migración de EF Core incluida si cambia el modelo de datos — no hay entidades/columnas nuevas ni carpeta `Migrations/` en el diff
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — no cambia; no está en el diff
- [x] Spec de la capability actualizada en `openspec/` (`index-feed` viva + delta `product-family` sincronizado)
- [x] Documentación de `Documentos/` actualizada (HU, runbook, épicas, arquitectura, modelo de datos, plan)
- [x] Sin secrets de producción en el diff — placeholders locales, mismo patrón que `AiGateway`; SSM en C17
- [x] Revisado el impacto en otros componentes del monorepo — `ai-service/` y `frontend/` no están en el diff; C13 será el primer consumidor

---

## 🚀 Deployment notes

**Variables nuevas**

| Clave | Obligatoria | Default | Dónde |
|---|---|---|---|
| `IndexFeed:ApiKey` / `IndexFeed__ApiKey` | Sí (≥ 32) | placeholder en `appsettings*.json` | local: appsettings / `.env`; prod: SSM `/jpv/prod/IndexFeed:ApiKey` (**C17**) |
| `IndexFeed:ApiKeyPrevious` | No | `""` (unset) | rotación; si no está vacía, también ≥ 32 |

Sin ella (o si es corta) **el host no arranca** (`ValidateOnStart`). Distinct de `Jwt:SecretKey` y de `AiGateway:JwtSecret`.

**Post-deploy:** ninguno en este change (sin migración, sin Compose, sin terraform). El AutoBulk de perfiles no es criterio de merge; ver el runbook.

**Rollback:** revertir el deploy de la API. Superficie nueva: no hay consumidor en producción hasta C13. El sello `ExecuteUpdate` y el `IsModified` de `UpdatedAt` en `SaveChangesAsync` sí afectan escrituras de familia (y de cualquier entidad `Modified` con `UpdatedAt`).

**Orden:** desplegar el backend .NET **antes** de que C13 tire del feed. `jbg-ai` no envía el header todavía.

---

## 📝 Notas adicionales

**Breaking changes:** ninguno de contrato REST existente ni de OpenAPI de Python. Endpoints nuevos. La clave `IndexFeed:ApiKey` es obligatoria al arranque; los `appsettings*.json` del repo ya traen placeholder.

**Riesgo: alto** — auth nueva (`Program.cs` + filtro), y `ApplicationDbContext` fuerza `UpdatedAt` en **todo** `Modified`, no solo en Product/familia.

**Puntos para reviewers**

1. `AiIndexFeedController` no lleva `[Authorize]` a propósito: un JWT humano no debe abrir el feed. Los 401 de integración usan cliente HTTP **fresco** (trampa del `HttpClient` compartido).
2. `StampUpdatedAtAsync` usa `ExecuteUpdateAsync` porque `UpdatedAt` es `ValueGeneratedOnAddOrUpdate`; un `UPDATE` del tracker omitiría la columna.
3. Hash agregado = conjunto indexable **global**, idéntico en cada página. Cursor keyset, no un ISO-8601 suelto.
4. POS no filtra por POS del operador: es credencial de servicio, no de usuario. `quantity` no sale en el JSON.
5. `HU-AIENG-012` aún enlaza `openspec/changes/add-dotnet-index-feed-endpoints/` (ruta activa, ya no existe). Corrección → `enrich-us`.
6. Python no consume el feed en esta PR. `POST /v1/index/sync` sigue siendo el stub de C13.



---

<a id="pr-18"></a>
## #18 — feat(ai-service): drenar el feed de catálogo hacia ai.product_document

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c13-add-product-document-indexer` → `ai-eng` |
| Creada | 2026-08-26 |
| Integrada | 2026-08-26 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/18 |

### Descripción

## 📋 Descripción

Sustituye el stub C02 de `POST /v1/index/sync` y `GET /v1/index/status` por el dreno real del feed de catálogo cuando `STUB_MODE=false`. Python tira de `GET /api/ai/index-feed/catalog` con `X-Index-Feed-Key`, escribe `ai.product_document` (upsert con skip-embed, tombstones, procedencia sellada) y persiste un checkpoint keyset. Con stub mode siguen los fixtures C02.

El contrato OpenAPI de índice gana `since_id` / `cursor_id` (uuid, opcionales). `batch_size` permanece en el schema y se ignora: la página es la 50 fija de C12. `httpx` pasa de grupo `dev` a dependencia de runtime.

No hay cambios de código en backend .NET, frontend ni `IAiGatewayClient`. `indexing/embeddings.py` no se toca. El feed POS existe en el cliente y el orquestador no lo llama.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

Campos OpenAPI nuevos **opcionales**; no hay consumidor .NET de estas rutas (`IAiGatewayClient` no tiene operación de índice). El cambio de comportamiento con `STUB_MODE=false` (deja de ser 501) es el entregable, no una ruptura de un cliente existente.

---

## 🎯 Motivación y contexto

C11 dejó `jbg_ai.indexing` sin importar en `api.main`. C12 dejó el feed HTTP sin consumidor Python. Con `STUB_MODE=false` las rutas de índice respondían 501. Sin este change, C14 consultaría HNSW sobre cero filas o violaría el §6.3 leyendo `public`.

- Change OpenSpec archivado: `openspec/changes/archive/2026-08-26-add-product-document-indexer/`
- HU: `Documentos/Historias/AI-Eng/HU-AIENG-013.md`
- Spec viva nueva: `openspec/specs/product-document-indexer/spec.md`

Sin issue GitHub en los commits.

---

## 🔄 Cambios realizados

### ai-service

- Alembic `b8e3c1a4d7f0` (hija de `f46c55c056e2`, a mano): `ai.product_document.text_provenance` NOT NULL + CHECK (`merchant` | `ai_assisted` | `synthetic`) + B-tree; tabla `ai.sync_checkpoint`; `ai.sync_failure` gana `cursor_since_id` y `product_id`. Sin ENUM, sin FK a `public`, sin backfill. Downgrade reversible.
- `api/routers/index.py`: `get_catalog_principal` (sin `pos_id`); stub vs real como C09; 503 nombrando setting si faltan feed URL/key, embed key o mapa. Inyección por `request.app.state` (`index_feed`, `index_embed`, `index_repo`, `index_provenance`). Importa `indexing` el router, no `api.main`.
- Settings opcionales al boot: `JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY`, `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` (default 180; blank → 180). Pin en `canonical_openapi_settings`. String vacío = unset. No caen a `JWT_SECRET`.
- Cliente `HttpxIndexFeedClient` (`indexing/feed.py`): header `X-Index-Feed-Key`, keyset `since`/`sinceId`, parseo `kind` upsert|tombstone, timeout 10 s. `fetch_pos_page` presente.
- Orquestador `sync_catalog` / `report_index_status`: precedencia `full` > body keyset > checkpoint; tope de tiempo tras cada ítem (HTTP 200 con cursor parcial); skip-embed si `source_hash` coincide y hay vector 1536, UPDATE de columnas siempre; tombstone DELETE idempotente; aislamiento por ítem → `sync_failure`; `skipped` = embed omitido. Drift: SHA-256 del conjunto de `product_id` (`set_hash.of_product_ids`, orden .NET `Guid.CompareTo`) vs un GET de la primera página (`aggregateHash`).
- Repositorio Core `SqlAlchemyProductDocumentRepo` sobre el engine existente (pool 5). UPSERT atómico fila+vector. Cero INSERT con embedding NULL desde este escritor.
- Mapa `indexing/sku_provenance.json` commiteado (archivo nuevo, ~4802 líneas; diff resumido a cabecera de hunk). Runtime: `load_provenance_map()` solo lee `src/`. Generador `python -m jbg_ai.indexing.generate_provenance_map`.
- CLI `python -m jbg_ai.indexing sync [--full]` llama a la misma `sync_catalog`.
- Stub `index_sync_stub` rellena `since_id` / `cursor_id`.

### ai-contracts

- `IndexSyncRequest` / `IndexSyncResponse`: `since_id` y `cursor_id` (uuid | null). Descripción de `batch_size` como ignorado; `skipped` = embeber omitido.
- `openapi.json` regenerado: 503 documentado en `/v1/index/sync` y `/v1/index/status`.

### deps

- `httpx>=0.28.1` pasa de `[dependency-groups] dev` a `dependencies` en `ai-service/pyproject.toml` (y `uv.lock`). Sin salto de mayor.

### tests

- Rutas: token de catálogo sin `pos_id`; 503 nombrado; stub no toca fakes; status con un GET; feed caído no escribe.
- Feed: mapeo camelCase, tombstone, query params, 5xx/transporte → `IndexFeedConfigError`, 401 no se mapea a unavailable.
- Orquestador: skip-embed + update de precio; rename de familia reembebe; tombstone repetido no-op; aislamiento; mapa ausente; vector ≠1536 no se persiste; no llama POS; tope de tiempo; `batch_size` warning.
- Mapa: invariante 1.200 claves (436 `real` / 764 `synthetic`; 387 `ai_assisted` / 49 `merchant` / 764 `synthetic`) contra los JSONL.
- Migración: CHECK NOT NULL de `text_provenance`, tabla checkpoint, columnas de `sync_failure`, downgrade a C05. Tests de esquema existentes pasan a insertar `text_provenance`.
- Fakes en `tests/support/index_fakes.py`. `test_index_routes_still_name_c13` se sustituye por `test_index_routes_use_catalog_principal`. `STUB_ONLY_REQUESTS` excluye también `/v1/index/*`.

### config

- `backend/.env.example`: placeholders comentados `JPV_INDEX_FEED_BASE_URL`, `JPV_INDEX_FEED_API_KEY`, `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS=180`. Host `127.0.0.1:5056`.

### infra

- `backend/docker-compose.yml` servicio `jbg-ai`: `JPV_INDEX_FEED_BASE_URL=http://host.docker.internal:5056`, key placeholder distinta de `JWT_SECRET`, tope 180, `extra_hosts: host.docker.internal:host-gateway`.

### openspec

- Change archivado `2026-08-26-add-product-document-indexer` (proposal, design, qa, ticket, tasks, deltas).
- Spec viva nueva `product-document-indexer`. Deltas fusionados en `ai-service-api-contracts`, `ai-service-runtime`, `ai-vector-schema`, `catalog-source-text` (el no-objetivo C11 de que `/v1/index/*` siga en stub se levanta; `api.main` sigue sin importar `indexing`).
- `openspec/project.md` y `openspec/config.yaml` registran C13.

### docs

- HU-AIENG-013 nueva. `epicas.md` (EP14), `modelo-de-datos.md` (`text_provenance`, `sync_checkpoint`, deriva), `arquitectura.md`, `modelo-c4.md`, plan de changes (C13 archivado), READMEs de raíz, `ai-service` y `ai-service/tests`.

---

## 🧪 Testing

Presentes en el diff (pytest, fakes; sin sockets a OpenAI ni `:5056`):

- `ai-service/tests/api/test_index_routes.py` — auth de catálogo, 503, stub vs real, keyset, feed caído
- `ai-service/tests/indexing/test_orchestrator.py` — skip-embed, tombstone, aislamiento, cursores, drift, tope
- `ai-service/tests/indexing/test_feed_client.py` — parseo y `MockTransport`
- `ai-service/tests/indexing/test_cli.py` — misma función que el router
- `ai-service/tests/indexing/test_provenance_map.py` — mapa = unión JSONL
- `ai-service/tests/migrations/test_c13_schema.py` — Alembic (omitir si Docker no responde; `pytest.mark.db`)
- Ajustes en `test_contracts.py`, `test_health.py`, `test_stub_mode.py`, `test_settings.py`, `test_embeddings.py`, invariantes C05

Resultado de la suite en CI: **UNKNOWN** (no ejecutada en esta redacción). Smoke local `indexed_documents = 1200` / `drift_count = 0` es verificación **posterior**, no criterio de merge.

- [x] Tests de contrato/API de `jbg-ai` añadidos o actualizados
- [ ] Tests xUnit del backend
- [ ] Tests Vitest / RTL / Playwright del frontend
- [ ] `openspec validate --all --strict` en verde (no verificado aquí)

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` (Python no lee `public`; router importa `indexing`, `api.main` no)
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — no aplica; cobertura pytest **UNKNOWN**
- [ ] Migración de EF Core incluida si cambia el modelo de datos — no aplica (Alembic en `ai`, no EF)
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` (`product-document-indexer` + deltas vivos). `openspec validate` **UNKNOWN**
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets de producción en el diff (placeholder local ya usado por C12: `local-dev-index-feed-key-0123456789ab`; SSM en C17)
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

**Orden:** aplicar Alembic `b8e3c1a4d7f0` en el esquema `ai` del Postgres de `jbg-ai` **antes** de un sync real. El contenedor `jbg-ai` es independiente de la imagen API+SPA.

**Variables nuevas** (opcionales al boot; `/health` no las exige; sync real → 503 nombrado):

| Variable | Default | Dónde |
|---|---|---|
| `JPV_INDEX_FEED_BASE_URL` | unset | Compose: `http://host.docker.internal:5056`. Host: `http://127.0.0.1:5056`. Prod: C17 |
| `JPV_INDEX_FEED_API_KEY` | unset | Mismo valor que `IndexFeed:ApiKey` del API .NET. Distinta de `JWT_SECRET` |
| `JPV_INDEX_SYNC_TIME_BUDGET_SECONDS` | `180` | Compose y `.env.example` |

**Post-deploy local:** `alembic upgrade head` en `ai-service`; API .NET en `:5056` con `IndexFeed:ApiKey`; `POST /v1/index/sync` `{full: true}` o `python -m jbg_ai.indexing sync --full`. Compose ya inyecta URL/key al servicio `jbg-ai`.

**Rollback:** `alembic downgrade f46c55c056e2` elimina `text_provenance`, `sync_checkpoint` y las columnas nuevas de `sync_failure`. Las seis tablas C05 permanecen. Revertir la imagen deja de nuevo el 501 en índice si se vuelve a un binario pre-C13. Filas ya indexadas se pierden al bajar la columna; la tabla estaba vacía al diseñar la migración.

**Terraform / SSM / nginx / CI:** sin cambios en este diff. Producción de las keys: C17.

---

## 📝 Notas adicionales

**Riesgo: alto.** Toca `openapi.json`, auth de catálogo (`get_catalog_principal`), Alembic del esquema `ai` y un secreto de feed distinto de `JWT_SECRET`. No hay breaking de consumidor: campos OpenAPI opcionales; nadie en .NET llama `/v1/index/*`.

**Acoplamiento .NET ↔ Python.** C13 consume el feed C12; no modifica el API .NET. El consumidor de un contrato se despliega después del proveedor: el feed `:5056` debe estar arriba para un sync real. Compose usa `host.docker.internal` porque el backend no es servicio Compose.

**Fuera de alcance verificado en tests:** `test_catalog_sync_does_not_call_pos_feed`; `test_main_does_not_import_indexing` se mantiene; `embeddings.py` no está en el diff.

**Reviewers:** el diff de `sku_provenance.json` está resumido (~4802 líneas). La cardinalidad se afirma en `test_provenance_map_matches_jsonl_union`, no en el hunk truncado.

**Limitación:** un pytest no exige 1.200 filas reales. El smoke `indexed_documents = 1200` / `drift_count = 0` queda fuera del merge.



---

<a id="pr-19"></a>
## #19 — feat(ai-service): implementar retriever vectorial de products

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c14-add-vector-retrieval-endpoint` → `ai-eng` |
| Creada | 2026-08-27 |
| Integrada | 2026-08-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/19 |

### Descripción

## 📋 Descripción

C14 sustituye el 501 de `POST /v1/retrieval/products` cuando `STUB_MODE=false` por un retriever vectorial sobre `ai.product_document`. Embebe la query con `LiteLlmEmbeddingClient` (`max_attempts=1`, sin editar `indexing/embeddings.py`), busca con `<=>` cosine y umbral de distancia en SQL, aplica overfetch **después** del umbral y honra los filtros del body. Con `STUB_MODE=true` siguen los fixtures C02, cero I/O.

`POST /v1/retrieval/substitutes` sigue en stub/501 (C26). El snapshot `ai-service/openapi.json` no se regenera. El change OpenSpec queda archivado y las specs vivas `vector-retrieval` y `ai-service-runtime` alineadas.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

El contrato OpenAPI y los schemas Pydantic no cambian. El único cambio de comportamiento es el intencional de C14: con `STUB_MODE=false`, `/v1/retrieval/products` deja de responder 501 y pasa a 200/422/503 reales. El default local (`STUB_MODE=true`) no se mueve.

---

## 🎯 Motivación y contexto

Tras C13, `ai.product_document` es consultable (HNSW cosine). C02 congeló el contrato y C03 ya llama `POST /v1/retrieval/products` con timeout 800 ms. Sin retriever real, C15 hidrataría el stub o se quedaría en circuito abierto.

- Change OpenSpec archivado: `openspec/changes/archive/2026-08-27-add-vector-retrieval-endpoint/`
- Historia: [HU-AIENG-014](Documentos/Historias/AI-Eng/HU-AIENG-014.md)
- Spec viva nueva: `openspec/specs/vector-retrieval/spec.md`

Sin issue de GitHub en los commits.

---

## 🔄 Cambios realizados

### ai-service

- `api/routers/retrieval.py:retrieve_products` pasa a `async def`. Quita `require_stub_mode` **solo** en `/products`. Stub si `settings.stub_mode`; si no, orquesta embed + search. Substitutes intacto (`SUBSTITUTES_DELIVERED_BY` C26).
- 503 si faltan `JPV_EMBEDDING_API_KEY` o `DATABASE_URL` (salvo fake inyectado en `app.state.retrieval_embed` / `retrieval_search`). `InvalidFamilyIdError` → 422. `DatabaseNotConfiguredError` y `RetrievalDependencyError` → 503. `payload.pos_id` sigue ignorado; `effective_pos_id` sale del token.
- Paquete nuevo `jbg_ai/retrieval/`:
  - `orchestrator.py:build_retrieval_embed_client` — `LiteLlmEmbeddingClient(..., max_attempts=1)`.
  - `orchestrator.py:retrieve_products` — `count_compatible` = 0 → `RetrievalDependencyError` (no abstención); score `clamp(1 − d, 0, 1)`; overfetch con `over_retrieval_count`; `low_confidence` si `results` vacío; logs `stage=embed|search` con `trace_id`. `mode` hybrid/lexical añade `vector_only_until_c21` en `debug.notes`.
  - `search.py:SqlAlchemyProductSearch` — SQLAlchemy Core sobre `session_scope`; `<=>` + `LIMIT :overfetch` **tras** el umbral; filtros `materials &&`, `piece_type`, `family_id`, `exclude_product_ids`. Sin `pos_id`, precio, stock ni schema `public`.
  - `ports.py:ProductSearchPort`, `errors.py:RetrievalDependencyError` / `InvalidFamilyIdError`.
- `config/settings.py:jpv_retrieval_distance_threshold` — default 0.65, dominio `(0, 2]`, blank → 0.65; pin en `canonical_openapi_settings`. No bloquea `GET /health`.

No hay diff de `indexing/embeddings.py`, `openapi.json`, Alembic, backend ni frontend.

### tests

- `tests/api/test_retrieval_real.py` — stub cero I/O, 503 de key/DB/índice vacío, real ≠ 501, 401 sin `pos_id`, body `pos_id` ignorado, 422, hybrid/lexical, provider 503, logs HTTP.
- `tests/retrieval/test_orchestrator.py` — abstención 200, overfetch 15, no relleno sobre umbral, orden por distancia, `max_attempts=1`, filtros, exclusiones malformadas, hybrid/lexical.
- `tests/retrieval/test_search_port.py` — fake count/search; SQL sin `pos_id` / `public` / precio / stock; `<=>` presente y `<->` ausente.
- `tests/support/fake_product_search.py` — puerto in-memory.
- Ajustes: `test_stub_mode.py` saca `/v1/retrieval/products` del 501 y apunta el mensaje C26 a substitutes; settings/health cubren el umbral opcional.

### openspec

- Archivo `2026-08-27-add-vector-retrieval-endpoint` (proposal, design, qa, ticket, tasks, deltas).
- Spec viva nueva `openspec/specs/vector-retrieval/spec.md`.
- `openspec/specs/ai-service-runtime/spec.md`: requisito de `JPV_RETRIEVAL_DISTANCE_THRESHOLD` opcional al boot.
- `openspec/config.yaml` y `openspec/project.md`: C14 en el contexto de runtime.

### docs

- HU-AIENG-014 nueva. C14 marcado archivado en el plan de changes, `epicas.md` (EP14), `arquitectura.md`, `modelo-c4.md`, `README.md` y `ai-service/README.md` (tabla del setting y lista de rutas reales).

---

## 🧪 Testing

Tests añadidos o ampliados en el diff (pytest, fakes, sin sockets a OpenAI/RDS):

- `tests/api/test_retrieval_real.py` (12)
- `tests/retrieval/test_orchestrator.py` (13)
- `tests/retrieval/test_search_port.py` (3)
- `tests/config/test_settings.py` (+4 umbral)
- `tests/api/test_health.py` (`test_health_starts_without_retrieval_threshold`)
- `tests/api/test_stub_mode.py` (products fuera del 501)

El `qa.md` del change archivado registra, en la fecha del apply, **144 passed** en `tests/retrieval` + `tests/api` + `tests/config` y `openspec validate --all --strict` **42 passed, 0 failed**. Esta sesión no reejecuta esas suites.

Sin xUnit, Vitest ni Playwright: C14 no cruza `backend/` ni `frontend/`.

Verificación posterior (no DoD de merge, según HU y ticket): un `POST` local con `STUB_MODE=false` contra el índice de 1.200 filas. No está en el diff de código.

- [x] Tests unitarios añadidos (pytest, fakes)
- [ ] Tests de integración (pgvector/Docker) — el change los deja opcionales y no los añade
- [ ] Tests E2E
- [ ] Verificado manualmente

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [ ] Migración de EF Core incluida si cambia el modelo de datos
- [ ] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo

`openapi.json` **no** se actualiza a propósito (contrato C02 intacto; 503 se lanza y no se declara). No hay migración EF ni Alembic. Cobertura ≥70% backend/frontend no aplica: el diff es solo `ai-service`. El ítem de `openspec validate` se marca porque `qa.md` del archivo lo registra en verde; no se ha reejecutado aquí.

---

## 🚀 Deployment notes

- Setting nueva **opcional**: `JPV_RETRIEVAL_DISTANCE_THRESHOLD` (default `0.65`). No bloquea boot ni `/health`. Distinct de `JPV_EMBEDDING_*` / `JPV_RAG_LLM_*` / `JPV_INDEX_FEED_*`.
- Camino real (`STUB_MODE=false`) exige `JPV_EMBEDDING_API_KEY` y `DATABASE_URL` (ya existentes) y un índice compatible; si faltan, 503 nombrando el fallo. Compose local sigue en stub mode.
- Producción / SSM: C17, fuera de este change. No hay recurso Terraform ni workflow en el diff.
- Rollback: `STUB_MODE=true` no cambia de comportamiento; revertir paquete `retrieval/` + router + setting. Nada que revertir en esquema ni snapshot.
- Orden: desplegar `jbg-ai` con este código **antes** de que C15 encienda real mode. C03 ya mapea 200/503/501 y no se toca.

---

## 📝 Notas adicionales

**Breaking de contrato:** ninguno (OpenAPI, JWT, EF, variables obligatorias). El 501 → 200/503 en real mode es el entregable.

**Riesgo: medio.** Nueva inferencia (embed + umbral 0,65 no calibrado; C24 calibra). Auth de retrieval no cambia (`get_service_principal` sigue exigiendo `pos_id`).

**Puntos para reviewers:**

1. **No filtrar por `pos_id`** en SQL es deliberado (C22 + hidratación C15). Hay test `test_search_sql_does_not_use_pos_id_as_a_predicate`.
2. **`mode=hybrid`/`lexical` ejecutan vector** hasta C21; `debug.notes` lleva `vector_only_until_c21`. No 501 por modo.
3. **Índice vacío ≠ abstención:** count compatible 0 → 503; umbral sin hits → 200 + `low_confidence`.
4. **Freeze C11:** `embeddings.py` no aparece en el diff. Cliente de retrieval distinto (`max_attempts=1`), no reutilizar `index_embed` (3 intentos) para no pelear con los 800 ms de C03.
5. **503 no está en el snapshot OpenAPI** (mismo corte que C09). Declararlo obligaría a regenerar.
6. `api.main` no importa `jbg_ai.retrieval`; el router importa submódulos. Inyección por `app.state` para tests.
7. Python no lee `public`. No hay `ai.query_log`.



---

<a id="pr-20"></a>
## #20 — feat(backend): POST /api/ai/search con hidratación autoritativa y degradación (C15)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c15-add-dotnet-ai-search-endpoint` → `ai-eng` |
| Creada | 2026-08-28 |
| Integrada | 2026-08-28 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/20 |

### Descripción

## 📋 Descripción

Entrega **C15**: `POST /api/ai/search`, el endpoint que faltaba entre el cliente de pasarela (C03), la telemetría de búsqueda (C04) y el recuperador vectorial (C14). La IA propone candidatos y **el backend pone la verdad**: precio, cantidad y qué tiene esa tienda salen del catálogo transaccional, nunca de la respuesta del servicio de IA.

El endpoint pide a `jbg-ai` la **ventana máxima que el contrato congelado puede producir, en una sola llamada** (`top_k = 20` → 60 candidatos) y **no vuelve a pedir** cuando la hidratación deja la página corta: el recuperador aplica su umbral de distancia antes del `LIMIT`, así que repedir devolvería las mismas filas cobrando un segundo embedding. Después hidrata con una consulta conjunta sobre `Inventory ⋈ Product`, descarta lo que ese punto de venta no tiene, conserva y marca lo que tiene a cero, y trunca a la página conservando el orden de relevancia.

Cualquier fallo del servicio de IA degrada a un buscador léxico propio, acotado al mismo punto de venta, con `to_tsvector('spanish', …)` calculado en consulta —sin índice ni cambio de esquema— y semántica OR. **La búsqueda nunca falla por culpa de la IA.** Sin migración de EF Core y sin tocar `ai-service/`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec:** `openspec/changes/archive/2026-08-28-add-dotnet-ai-search-endpoint/` (archivado en esta misma rama, 43/43 tareas).
- **Historia de usuario:** `Documentos/Historias/AI-Eng/HU-AIENG-015.md`.
- **Ticket:** `T-AIENG-015`, dentro del change.

Sin este endpoint **C04 es código muerto sin síntoma**: compila, sus tests pasan y su tabla llegaría vacía a la entrega, porque nadie invoca `RecordSearchAsync`. Desbloquea además C16 (panel del operador) y C17 (despliegue del servicio).

El diseño del change (`design.md`) documenta el hallazgo que lo gobierna: el §7.6 del diseño RAG sitúa el `pos_id` como filtro duro **dentro del recuperador**, pero C13 no indexó disponibilidad y C14 declara que su SQL no filtra por punto de venta. C15 vive en la ventana anterior a C22 y sólo puede aplicarlo al hidratar, con la pérdida de resultados que eso implica en las tiendas de baja cobertura. Se acepta, se dobla la ventana de candidatos al máximo del contrato, y **se mide** — esa medición es la línea base contra la que se comparará C22.

---

## 🔄 Cambios realizados

### `backend-api` — 3 archivos, +293

- **`AiSearchController.cs`** *(nuevo)*: `POST /api/ai/search` bajo `api/ai/*`, sin versión en la ruta, `[Authorize]` y `[EnableRateLimiting(RateLimitPolicies.AiSearch)]`. Valida el cuerpo explícitamente —el proyecto tiene `SuppressModelStateInvalidFilter` activo— y mapea el resultado: 400 sin punto de venta o con uno inactivo, 403 si el operador no está asignado, 200 en el resto.
- **`AssistedSearchDtos.cs`** *(nuevo)*: `AssistedSearchRequest`, `AssistedSearchResultDto`, `AssistedSearchResponse`, `AssistedSearchOutcome` y `AssistedSearchResult`.
- **`AiSearchRequest.cs`**: añade las constantes del contrato congelado `MaxTopK = 50`, `MaxQueryLength = 500`, `OverRetrievalCap = 60` y el helper `OverRetrievalCount(topK)`. Son constantes estáticas, invisibles para `AiContractSnapshotTests`, que inspecciona propiedades de instancia — el contrato no se mueve.

### `backend-application` — 6 archivos, +908

- **`AssistedSearchService.cs`** *(nuevo)*: orquesta el flujo completo — autorización, bandera por punto de venta, caché, llamada única al gateway, hidratación, truncado, telemetría y embudo. Captura las tres subclases concretas de `AiGatewayException` **más una cláusula final sobre el tipo abstracto**, para que una cuarta añadida por un change posterior no rompa la búsqueda.
- **`AssistedSearchCandidateCache.cs`** *(nuevo)*: instancia dedicada de `MemoryCache` con `SizeLimit`. Guarda **sólo identificadores y puntuaciones**; la hidratación se rehace en cada acierto, así que nunca se sirve precio ni stock rancios. La clave se hashea —la consulta es texto libre del operador— e **incluye el punto de venta desde el primer día**, aunque hoy la recuperación no dependa de él.
- **`AiSearchOptions.cs`** *(nuevo)* y **`AiSearchServiceCollectionExtensions.cs`** *(nuevo)*: opciones enlazadas con `IOptionsMonitor` y validadas con `ValidateOnStart`.
- **`IAssistedSearchService.cs`** *(nuevo)* y **`AssistedSearchRequestValidator.cs`** *(nuevo)*.

### `backend-domain` — 2 archivos, +87/-1

- **`SearchOrigin.cs`**: añade `Disabled = 3`. No se pliega sobre `LexicalFallback` a propósito: ese valor existe para medir cuántas veces falla la IA, y una tienda con la función apagada nunca le preguntó nada.
- **`IAssistedSearchRepository.cs`** *(nuevo)*: contrato de las dos lecturas, con los tipos de fila.

### `backend-data` — 1 archivo, +151

- **`AssistedSearchRepository.cs`** *(nuevo)*: ambas consultas parten de `Inventory` y no de `Product`, de modo que la regla de visibilidad es la forma de la consulta y no una condición que alguien pueda olvidar. El buscador degradado usa `websearch_to_tsquery` y no la conversión estricta, que lanza excepción ante un carácter reservado escrito por el operador.

### `backend-misc` — 2 archivos, +72/-3

- **`API/Extensions/ServiceCollectionExtensions.cs`**: clase `RateLimitPolicies` con los nombres de política, y `AiSearchRateLimit` particionada por `ClaimTypes.NameIdentifier`.
- **`Program.cs`**: registra `AddAssistedSearch` y **mueve `app.UseRateLimiter()` detrás de `app.UseAuthentication()`**. Ver *Notas adicionales*.

### `backend-infrastructure` — 1 archivo, +5

- Registro de `IAssistedSearchRepository`.

### `tests` — 3 archivos, +1285

- **`AssistedSearchServiceTests.cs`** *(nuevo, 35 tests)* — chunk **resumido** por el troceador; el análisis de este archivo se apoya en las cabeceras de hunk.
- **`AiSearchControllerTests.cs`** *(nuevo, 15 tests)* contra PostgreSQL real.
- **`AiSearchRateLimitTests.cs`** *(nuevo, 3 tests)*.

### `openspec` — 11 archivos, +1680/-8

Change archivado con sus seis artefactos, y specs vivas sincronizadas: `ai-assisted-search` **creada** (12 requisitos, 38 escenarios) y `ai-search-telemetry` **modificada** para el tercer origen. `openspec/project.md` gana las reglas de negocio 14 y 15.

### `docs` — 8 archivos, +320/-7

`backend/README.md` (matriz de autorización y variables `AiSearch__*`), `Documentos/modelo-de-datos.md` y `modelo-c4.md` (lista **y** diagrama), `testing-backend.md` (cuarta medición fechada), `epicas.md`, el plan de changes (entrada §0, ficha C15, §5 y obligación B6 heredada por C16), `README.md` §1.2 y §4, y la HU.

### `misc` — 1 archivo, +3

`.gitignore`: `TestResults/`.

---

## 🧪 Testing

**53 tests nuevos, todos en verde.** Ninguno llama al servicio de IA ni a un proveedor de embeddings: el gateway es un doble en los unitarios y, en integración, simplemente no está configurado.

| Suite | Nº | Cubre |
|---|---|---|
| `AssistedSearchServiceTests` | 35 | Hidratación autoritativa y deriva de SKU · ventana máxima en una llamada · página corta sin segunda llamada · orden de recuperación · abstención vs página vacía tras hidratar · stock cero conservado · una sola consulta de hidratación · degradación por los cuatro caminos de excepción · términos OR · bandera y origen `Disabled` · telemetría con la lista mostrada y `RetrievalMs` en todos los orígenes · caché con POS en la clave, cota y consulta no en claro · embudo · consulta fuera de logs de producción · permisos |
| `AiSearchControllerTests` | 15 | Contra PostgreSQL real: degradación efectiva, coincidencia por término, **tolerancia a caracteres reservados**, búsqueda por SKU, precio y stock del catálogo, stock cero, descarte de lo no asignado o inactivo, cantidad del POS y no la suma, evento registrado, 400/403/401 |
| `AiSearchRateLimitTests` | 3 | Límite excedido, **partición por usuario y no por dirección de red**, y que el rechazo no se reporta como caída de la IA |

Suite completa: **882 tests**, 49 fallos frente a los 54 de la línea base. Comparación **por nombres** —la única válida en este repositorio— da **cero regresiones**: el delta cae íntegramente en `InventoryIntegrationTests`, cuya inestabilidad por orden se verificó ejecutándola en aislamiento y obteniendo un cuarto conjunto de fallos distinto. El detalle está en `qa.md` §1.1 del change archivado.

Verificación adicional contra el mundo sembrado, fuera del DoD de merge (`qa.md` §9): búsqueda real desde `op-ciutadella` y `op-fornells` con `jbg-ai` en modo real y el índice local poblado.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: sin cambio de esquema
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**: `git diff` vacío
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: 43 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] QA manual del reviewer

---

## 🚀 Deployment notes

**Variables de entorno nuevas** (ninguna es secreta; no van a SSM):

| Variable | Efecto | Por defecto |
|---|---|---|
| `AiSearch__EnabledPointOfSaleIds__0`, `__1`, … | Puntos de venta con búsqueda asistida. Recargable sin redesplegar | vacío |
| `AiSearch__EnabledByDefault` | Si los ausentes de esa lista usan la vía asistida | `false` |
| `AiSearch__CandidateWindow` | Ventana pedida a `jbg-ai` | `20` |
| `AiSearch__RateLimitPermitLimit` / `__RateLimitWindowSeconds` | Peticiones por usuario y ventana | `30` / `60` |

**Despliegue aditivo y reversible por configuración.** El valor por defecto deja la asistencia **apagada** salvo en los puntos de venta que se listen, así que activar es un cambio de configuración y revertir también, sin redespliegue. Sin migración: la ampliación de `SearchOrigin` se persiste sobre una columna entera existente y los valores anteriores conservan su significado.

**Requiere `jbg-ai` con `STUB_MODE=false`** y el índice poblado para que la vía asistida responda; sin él, todo degrada al buscador léxico y se reporta con `aiAvailable: false`.

⚠️ **Para C17**: la primera llamada tras arrancar el contenedor midió **799 ms**, agotando justo el presupuesto de 800 ms de C03 y degradando esa búsqueda; las siguientes, 265–275 ms. El coste es el establecimiento de la conexión con el proveedor. Un calentamiento al arrancar lo evitaría. No es un defecto de esta PR —la degradación actuó como debe—, pero el primer operador tras un despliegue puede recibir resultados degradados.

---

## 📝 Notas adicionales

**Cambio de orden en un middleware compartido.** `app.UseRateLimiter()` pasa de la línea 108 a después de `UseAuthentication()`/`UseAuthorization()`. Es una corrección, no una preferencia: una política que particiona por usuario necesita `HttpContext.User`, y ejecutándose antes leía un principal vacío y caía a la dirección de red — detrás del proxy inverso toda una tienda comparte una, así que un operador podía agotar el cupo de sus compañeros. Fallaba en silencio: sin error, sin log, sin test en rojo. `LoginRateLimit` no se ve afectada, porque particiona por dirección y ésa está disponible en cualquier punto del pipeline. **`AiSearchRateLimitTests.Search_RateLimitIsPartitionedByUser_NotByNetworkOrigin` falla si el orden se revierte**, y se comprobó reintroduciéndolo.

**Limitación conocida y medida: pérdida de resultados en tiendas de baja cobertura.** El filtro más selectivo del canal se aplica al final, a un salto de red del ranking. Medido contra el mundo sembrado: CIU-CENTRE (72,6 % del catálogo) llena la página siempre; FORNELLS (20,1 %) devuelve páginas de 5 y de 8, con un **37,5 %** de páginas sin llenar frente al **0 %** de la primera. Y el descarte **correlaciona con el ranking**: una consulta alineada con una colección que esa tienda apenas tiene deja 5 supervivientes de 60, menos de la mitad de su media. Se corrige en **C22**; esta PR deja la línea base para medirlo, computable desde `ProductSearchEvents` sin columnas nuevas.

**Deudas anotadas, no pagadas aquí.** `ai-service/src/jbg_ai/api/routers/retrieval.py` construye un cliente de embeddings **por petición**, así que su caché en memoria no acierta nunca en producción; corresponde a C21/C22, que ya trabajan en esa zona, y C15 no cruza a Python. Un índice invertido sobre el catálogo transaccional sólo tendrá sentido si el catálogo crece un orden de magnitud.

**Obligación heredada por C16** *(registrada en la ficha del plan como B6)*: los tres «sin resultados» —abstención, sin surtido en este punto de venta, y degradado— deben decir cosas distintas en pantalla. El backend los expone con `aiAvailable`, `lowConfidence` y los contadores del embudo; renderizarlos como una única lista vacía haría que el panel mintiera en dos de los tres casos.

**Puntos de atención para reviewers:**

1. `AssistedSearchService.RetrieveAsync` — la ausencia de una segunda llamada es deliberada y está demostrada aritméticamente en `design.md` D1.
2. `AssistedSearchRepository.SearchLexicalAsync` — la expresión del documento está escrita dos veces a propósito: una llamada a método dentro de un árbol de expresión no es traducible y EF rechazaría la consulta.
3. `AssistedSearchCandidateCache` — la instancia dedicada no es capricho: `SizeLimit` es propiedad de la caché, no de la entrada, y ponerlo en la compartida obligaría al dashboard a declarar tamaño en entradas que nunca lo tuvieron.



---

<a id="pr-21"></a>
## #21 — feat(frontend): panel de búsqueda asistida y atribución de la venta (C16)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c16-add-frontend-assisted-search-panel` → `ai-eng` |
| Creada | 2026-08-29 |
| Integrada | 2026-08-29 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/21 |

### Descripción

## 📋 Descripción

Entrega el panel **«Buscar con ayuda»** (`/sales/new/assisted`): el operador describe una pieza con sus palabras y recibe lo que su tienda realmente tiene, al precio y con el stock que el catálogo transaccional dice ahora. Es la primera pantalla del sistema RAG y el consumidor que le faltaba a `POST /api/ai/search`, entregado en C15 sin nadie que lo llamara.

Al implementarlo apareció una laguna que sólo se ve desde aquí: la spec viva `ai-search-telemetry` declara —archivada como cumplida— que una venta lleva la búsqueda que la originó, y la columna `Sale.SearchEventId` existe con índice y clave foránea desde C04, pero **ningún objeto de transferencia de venta aceptaba el campo**. El único sitio del repositorio que la escribía era un test tocando la entidad a mano. Esta PR lo cierra: `CreateSaleRequest` y `BulkSaleLineRequest` aceptan un `searchEventId` opcional que se persiste tras comprobar existencia **y propiedad**.

Incluye además un ajuste temporal del presupuesto de recuperación (800 → 2500 ms) sin el cual la vía asistida degradaba en **todas** las búsquedas, y la documentación del baseline rojo de la suite de frontend, que no estaba escrito en ninguna parte.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Change de OpenSpec: **`add-frontend-assisted-search-panel`** (C16), archivado en `openspec/changes/archive/2026-08-29-add-frontend-assisted-search-panel/` con 70/70 tareas. Historia: [HU-AIENG-016](Documentos/Historias/AI-Eng/HU-AIENG-016.md). Ticket: `T-AIENG-016`. Épica **EP14 — Búsqueda Semántica Híbrida**, ruta crítica.

Antes de esta PR, el operador sólo encontraba un producto escaneando su código o tecleando el SKU exacto: `ProductService.SearchProductsAsync` casa la cadena completa contra el nombre, así que cualquier frase en lenguaje natural devuelve lista vacía.

Tres hechos del código, verificados al diseñar, gobiernan las decisiones de esta PR:

1. **La clave de la caché de candidatos de C15 incluye la consulta completa**, así que ningún prefijo puede acertar. Un disparo con `debounce` de 400 ms factura entre tres y seis embeddings por consulta —de los que se lee uno— y agota en cinco o seis consultas el límite de 30 peticiones/minuto/usuario. De ahí el **envío explícito**.
2. **`match_reasons` es la constante `["vector"]`** en `ai-service/src/jbg_ai/retrieval/orchestrator.py` hasta que llegue la rama léxica (C21), y **`variantLabel` lo puebla C18**. Ninguno de los dos se simula en pantalla.
3. **El requisito de atribución de venta no tenía camino por el que cumplirse**, descrito arriba.

---

## 🔄 Cambios realizados

### `frontend-pages` · `frontend` · `frontend-services`

- **`pages/sales/assisted.tsx`** (nuevo). Panel completo: episodio de búsqueda generado al montar (`useRef` con inicialización perezosa), envío explícito por Enter o botón, consultas de ejemplo que rellenan y buscan en un acto, filtros de material (multi-selección) y tipo de pieza que **no disparan búsqueda**, selector de punto de venta oculto con una única asignación y limitado a activos, guardia de petición vigente para descartar respuestas obsoletas, y bloque de embudo plegable sólo para administradores.
- **`components/sales/assisted-search-result-row.tsx`** (nuevo). Fila aislada desde el día uno para que C36 la amplíe en vez de reescribir la página. Foto, SKU, nombre, precio en EUR con formato es-ES, cantidad del punto de venta, marca de agotado **por texto además de por color**, insignia de origen desde un mapa ampliable y chips de materiales. `variantLabel` sólo cuando existe.
- **`services/ai-search.service.ts`** (nuevo). `search()` y `reportSelection()` sobre rutas **relativas** (`VITE_API_BASE_URL` ya trae `/api`). Mapea `429`, `403` y `400` a un resultado tipado; normaliza las dos formas reales de `ApiError.errors` (array plano en los endpoints de IA, diccionario por campo en el resto). `search()` nunca lanza; `reportSelection()` resuelve en vez de rechazar, porque el llamante no la espera.
- **`types/ai-search.types.ts`** (nuevo) y **`types/sales.types.ts`**: `searchEventId?` en `CartLine`, `CreateSaleRequest` y `BulkSaleLineRequest`.
- **`lib/materials-vocabulary.ts`** (nuevo). Vocabulario cerrado replicado de `ai-service/src/jbg_ai/enrichment/vocabularies.yaml`, con las consultas de ejemplo.
- **`routing/routes.tsx`** y **`routing/app-routing-setup.tsx`**: `SALES.NEW_ASSISTED` y ruta perezosa bajo `ProtectedRoute` + `Layout8`.
- **`pages/sales/index.tsx`**: tercera tarjeta, sin desplazar «Escanear Código» de la posición primaria.
- **`pages/sales/new.tsx`**: lee `searchEventId` del estado de navegación y lo envía en `createSale` y `addLine`. La atribución **caduca si el operador cambia de producto** (`attributedSearchEventId` compara con `locationState.productId`), para no inflar la conversión con ventas que el panel no produjo.
- **`pages/sales/cart.tsx`**: lo envía **por línea** en `createBulkSales`.

### `backend-api`

- **`DTOs/Sales/CreateSaleRequest.cs`** y **`DTOs/Sales/CreateBulkSalesRequest.cs`**: `Guid? SearchEventId`, opcional, por línea en el masivo.
- **`DTOs/Ai/AssistedSearchDtos.cs`**: `List<string> Materials` en `AssistedSearchResultDto`, documentado como **no hidratado y no autoritativo**.

### `backend-application`

- **`Services/SalesService.cs`**: `ResolveAttributionAsync(Guid?, Guid)` comprueba con `AnyAsync(e => e.Id == … && e.UserId == …)` que el evento exista **y sea del usuario que vende** —sin excepción de administrador, por coherencia con `RecordSelectionAsync`— y asigna en el camino individual y **línea a línea** en el masivo. La comprobación es explícita y no se delega en la clave foránea, cuyo comportamiento de borrado gobierna la eliminación del evento y abortaría la transacción ante una inserción con identificador inexistente.
- **`Services/AssistedSearchService.cs`**: `Materials = candidate?.Materials ?? []` en la construcción del resultado.
- **`Configuration/AiGatewayOptions.cs`**: `RetrievalTimeoutMs` por defecto 800 → **2500**.

### `config`

- **`appsettings.json`**: `AiGateway:RetrievalTimeoutMs` 800 → 2500, con las mediciones y el `TODO(C21/C22)` en el comentario. Ver *Deployment notes*.

### `openspec`

Capacidad nueva **`assisted-search-panel`** (13 requisitos, 37 escenarios). Deltas sobre `sales-management` (`ADDED` de la atribución + `MODIFIED` de los métodos de entrada, de dos a tres) y `ai-assisted-search` (`ADDED` de los materiales). Las tres sincronizadas en `openspec/specs/` al archivar. `openspec/project.md` gana las reglas de negocio 16 y 17. `openspec/DEFERRED_TASKS.md` registra la reversión del presupuesto.

### `docs` · `ai-tooling`

`README.md` (§4 y las secciones 1.2 y 1.3, congeladas, corregidas con aprobación explícita), `backend/README.md`, `Documentos/modelo-c4.md`, `Documentos/epicas.md`, `Documentos/testing-backend.md`, `Documentos/testing-frontend.md`, el plan de changes del PF (fichas **C15 y C16** cerradas) y `CLAUDE.md`.

---

## 🧪 Testing

**51 tests nuevos**, todos en verde.

| Fichero | Tests | Cubre |
|---|---|---|
| `pages/sales/__tests__/assisted.test.tsx` | 29 | Coste del disparo, filtros, orden recibido, los cuatro «sin resultados», página corta, los tres escenarios del episodio, selección, punto de venta y rol, embudo, respuesta obsoleta |
| `services/ai-search.service.test.ts` | 9 | Rutas relativas y mapeo de `429` / `403` / `400` (array y diccionario) / genérico |
| `pages/sales/__tests__/sales-index.test.tsx` | +2 | La tercera tarjeta con su `href` y que «Escanear Código» sigue primera |
| `lib/materials-vocabulary.test.ts` | 4 | Fijación de los nueve términos canónicos y los ocho tipos de pieza |
| `pages/sales/__tests__/new-attribution.test.tsx` | 3 | El arrastre hasta la línea del carrito y que no se atribuye si el producto cambió |
| `IntegrationTests/SaleAttributionTests.cs` | 6 | Los cuatro casos de atribución, el masivo por línea y que una atribución inservible no altera precio, cantidad ni movimiento de inventario |
| `UnitTests/Application/AssistedSearchServiceTests.cs` | +2 | `materials` viene del candidato; vacío-pero-presente en el camino degradado |

> El chunk `06-tests.diff` viene **resumido** por tamaño (613 líneas > umbral 600): el recuento de `assisted.test.tsx` se ha tomado del fichero completo, no de las cabeceras de hunk.

**Comparación contra la línea base** (el recuento no vale; se comparan nombres):

| Suite | Base | Después | Regresiones |
|---|---|---|---|
| .NET | 882 · 834 verdes · 48 rojos | 890 · 841 · 49 | **0** — los siete que entran y los seis que salen viven en las mismas tres clases dependientes del orden |
| Frontend | 482 · 364 · 118 | 529 · 416 · 113 | **0** — los cinco que dejan de fallar están en ficheros que esta PR no toca |

`dotnet build`, `npm run build` (1 m 29 s) y `openspec validate --all --strict` (44 passed, 0 failed) en verde.

**Verificación manual con el mundo sembrado y recuperación real** (`STUB_MODE=false`, 1.200 documentos con embedding), registrada en el `qa.md` del change:

| Punto de venta | Cobertura | Candidatos | Supervivientes | Mostrados |
|---|---|---|---|---|
| CIU-CENTRE | 0,78 | 60 | 32 | 10 — página llena |
| FORNELLS | 0,22 | 60 | 8 | **8 — página corta** |

Los cuatro casos de atribución —evento propio, desconocido, de otro usuario y sin referencia— dieron `201` con precio, cantidad y movimiento de inventario idénticos, y sólo el primero quedó atribuido.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: la columna, su índice y su clave foránea son de C04; `git status` de `Migrations/` vacío
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**: `ai-service/` sin diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] QA manual del panel en navegador — **pendiente de revisor**: el comportamiento está cubierto por 29 tests de componente y por la verificación contra datos reales, pero nadie ha mirado la pantalla renderizada

---

## 🚀 Deployment notes

**Compatible hacia atrás. Sin migración.** Los dos campos nuevos son opcionales y anulables sobre peticiones existentes; `materials` es aditivo en una respuesta. Un cliente que no envíe la atribución crea ventas idénticas a las de hoy.

**Variable de entorno con valor prestado — leer antes de desplegar:**

`AiGateway__RetrievalTimeoutMs` pasa de **800 a 2500 ms**. No es una preferencia: medido contra el mundo sembrado con recuperación real, a 800 ms la vía asistida degradaba en **todas** las búsquedas (`ai_gateway_call_failed timeout 1956 2` → `LexicalFallback`), y a 2500 ms sirvió en 0,86 s y 0,31 s. Sin este ajuste la funcionalidad llegaría a producción **pareciendo sana** —HTTP 200, resultados en pantalla— respondiendo siempre desde el buscador léxico.

La causa está en el otro servicio y **no se arregla aquí**: `ai-service/src/jbg_ai/api/routers/retrieval.py` construye un `LiteLlmEmbeddingClient` por petición, así que la caché en memoria que C11 congeló nace vacía y cada búsqueda paga un viaje completo al proveedor de embeddings. Deuda anotada al diseñar C15 y asignada a **C21/C22**. Registrado en `openspec/DEFERRED_TASKS.md` con los pasos para revertir y el motivo de no dejarlo así: con el reintento único de C03, el peor caso pasa a ser unos cinco segundos de un operador esperando en el mostrador.

El valor está en `appsettings.json` **y** en el defecto de `AiGatewayOptions` para que no queden dos verdades. En producción se puede sobrescribir desde SSM sin redesplegar.

**Activación.** La búsqueda asistida sigue **apagada por defecto** (`AiSearch:EnabledByDefault = false`): encenderla en una tienda es añadir su identificador a `AiSearch__EnabledPointOfSaleIds__N`, y se recarga sin redespliegue.

**Rollback:** retirar la tarjeta y la ruta. Los dos campos opcionales quedarían sin emisor y ninguna venta existente cambia de significado.

---

## 📝 Notas adicionales

**Acoplamiento backend ↔ frontend, resuelto en la misma PR.** El contrato cambia en `backend-api` y los tipos TypeScript acompañan en `frontend-services` (`types/ai-search.types.ts`, `types/sales.types.ts`). Sin desajuste pendiente.

**Frontera con `jbg-ai` intacta.** Ni `ai-service/`, ni `ai-service/openapi.json`, ni `IAiGatewayClient` tienen diff. Los claims del JWT interno no cambian.

**Limitaciones conocidas, declaradas y no disimuladas:**

- La **talla** no se pinta porque `variantLabel` es nulo hasta C18. Se renderiza condicionalmente, así que aparecerá sola cuando ese change entre.
- El **motivo** real no existe: `matchReasons` es la constante `["vector"]` hasta C21. Se sustituye por insignia de origen más chips de materiales, con un mapa preparado para aceptar valores nuevos sin tocar el panel.
- El panel **no puede distinguir** «asistencia desactivada en este punto de venta» de «la IA se cayó»: la respuesta trae `aiAvailable: false` en ambos casos. La telemetría sí los separa (`Disabled` vs `LexicalFallback`); la API no. Decisión consciente, no descuido.
- La **página corta es frecuente** en los puntos de venta de baja cobertura, y dos de los tres operadores de demostración están en 0,38 o por debajo. Se declara en pantalla en vez de disimularse; es la línea base «antes» de la ablation de C22.

**Un fallo preexistente sigue rojo**, a propósito: `sales-index.test.tsx > should show "Escanear Código" tile` falla por `Found multiple elements` —la tarjeta repite su nombre en el título y en el botón— y ya fallaba en la línea base. Arreglarlo enturbiaría la comparación nombre a nombre sobre la que se apoya todo el registro de verificación. El test añadido dos líneas más abajo enseña el patrón correcto.

**`/opsx:verify` encontró un requisito insatisfacible** y está corregido en esta rama: la spec del panel pedía «the correlation identifier» en el bloque del embudo, y `AssistedSearchResponse` no lo lleva —C15 lo dejó fuera del contrato a propósito—. Se corrigió la spec, no el código; el identificador del evento, que es lo que sí viaja, es además la clave que une la pantalla con la fila persistida.

**Para el revisor de C36:** la fila de resultado es un componente propio para que la amplíes en vez de reescribirla, y al añadir selección múltiple habrá que impedir arrastrar al carrito una fila con `hasStock: false` — la verificación manual tropezó con un `400 · Stock insuficiente` por exactamente eso.

**No paralelizar** con C36: misma página y mismo servicio del frontend.



---

<a id="pr-22"></a>
## #22 — feat(infra): entorno de demostración aislado para el servicio de IA

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c17-add-ai-service-deployment` → `ai-eng` |
| Creada | 2026-08-30 |
| Integrada | 2026-08-30 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/22 |

### Descripción

## 📋 Descripción

Levanta un **entorno de demostración aislado** para el servicio de IA, en una cuenta AWS distinta de la de la tienda, y lo puebla con el corpus real. Hasta ahora todo lo construido desde C01 —corpus, enriquecimiento, índice vectorial, recuperación, hidratación autoritativa y panel del operador— funcionaba **sólo contra el Docker de un portátil**, y el criterio de entrega del Proyecto Final pide una URL pública con usuario de demostración.

La ficha original daba por hecho un despliegue a producción. No hay acceso a esa cuenta, y su base de datos contiene el catálogo real del negocio: inyectar allí 764 productos sintéticos y 12 puntos de venta simulados sería un daño, no una decisión técnica. El change levanta en su lugar un entorno autocontenido en otra cuenta, con estado de Terraform propio, sin una sola arista hacia la de la tienda.

Además entrega dos piezas de producto que el entorno necesita para poder diagnosticarse: el **`/health` enriquecido** del servicio de IA —base de datos, estado del índice, presencia de la credencial del proveedor y contraste del modelo de embeddings configurado contra el indexado, sin llamar nunca al proveedor— y la **tarjeta de estado** en el panel de administración, servida por un endpoint .NET porque el navegador no puede consultar un servicio que es privado por diseño.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-08-30-add-ai-service-deployment/` (archivado, 86/86 tareas), con `proposal.md`, `design.md` (21 decisiones), `tasks.md`, `ticket.md` y `qa.md`.
- **Historia**: `Documentos/Historias/AI-Eng/HU-AIENG-017.md`, épica EP11.
- **Capacidades**: crea `demo-deployment` y amplía `ai-service-runtime` y `dashboard-analytics`.

El riesgo que gobierna el change es el dato, no el despliegue: un entorno impecable con el índice vacío pasa todas las pruebas y entrega una URL donde la búsqueda asistida no encuentra nada. Por eso el camino del dato entra en el change y la verificación posterior exige un recuento de documentos mayor que cero.

**Producción no se toca.** Las únicas ediciones de su lado son cabeceras de deprecado sobre ficheros en desuso (`backend/src/JoiabagurPV.API/Dockerfile`, `Dockerfile.prod`, `backend/docker-compose.prod.yml`) y la corrección de `backend/README.md`, que presentaba un camino de despliegue obsoleto como vigente — deuda que el ticket de C03 ya había asignado aquí.

---

## 🔄 Cambios realizados

### `infra` — 20 archivos

- **`terraform/demo/`** — módulo nuevo con **estado propio** (`backend.tf`, bucket y clave separados). Proveedor OIDC de GitHub, rol de despliegue con confianza acotada a `repo:<org>/<repo>:environment:demo`, rol e instance profile del anfitrión, dos repositorios ECR **cada uno con su política de ciclo de vida**, grupo de seguridad con entrada sólo en 80/443, instancia, IP elástica y parámetros no secretos. La AMI se resuelve por `data "aws_ssm_parameter"` del alias público de AL2023, sin variable manual.
- **`terraform/demo/templates/user_data.sh`** — aprovisionamiento en **cuatro pasos y sin nada específico de la aplicación**: motor de contenedores y plugin de Compose con versión fijada, servicios del sistema, paquete de despliegue y ejecución.
- **`deploy/demo/deploy.sh`** — lee los parámetros del almacén **al entorno del proceso, nunca a disco**, valida cada variable con `: "${VAR:?}"`, y usa `up -d` — **jamás `down -v`**, que destruiría el volumen del certificado contra un límite de cinco duplicados semanales. Sin trazado de intérprete en el tramo que lee secretos, porque la salida del comando remoto se archiva.
- **`Dockerfile.demo`** (nuevo) con `VITE_API_BASE_URL=/api` por defecto: la imagen queda agnóstica del nombre de dominio. La de producción, `Dockerfile.bundled`, **no se toca**.
- **`ai-service/Dockerfile`** endurecido: construcción multietapa, usuario sin privilegios, instalador `uv` **con versión fijada** en lugar de `:latest`, y `HEALTHCHECK` con el intérprete ya presente.
- **`.dockerignore`** en la raíz y en `ai-service/`, inexistentes hasta ahora.

### `misc` — `compose.demo.yaml`, `deploy/demo/Caddyfile`

Composición de cuatro servicios donde **sólo el proxy declara puertos publicados**. El servicio de IA, que custodia la clave del proveedor, no publica ninguno y lleva `mem_limit` explícito —no `deploy.resources`, que se ignora fuera de swarm—. Los ajustes que cambian *lo que el sistema calcula* van como **literales versionados**: modelo de embeddings, umbral de distancia, `STUB_MODE=false` y `AiSearch__EnabledByDefault`.

### `ci` — `.github/workflows/deploy-demo.yml`

Flujo sobre la rama `demo` con OIDC contra el rol de la demo. Descubre el anfitrión **por etiqueta**, no por secreto. Despliegue y verificación se ejecutan **dentro del anfitrión** por `aws ssm send-command`, porque el servicio de IA no es alcanzable desde un ejecutor externo. Filtro de rutas como **lista negra**: una lista blanca falla hacia no desplegar, y además dejaría fuera todo el paquete de despliegue.

### `ai-service` — 3 archivos

- **`api/health_report.py`** (nuevo) — sondas de base de datos, índice y credencial, con caché de ventana corta para no agotar un pool limitado a cinco conexiones. **Nunca llama al proveedor.** Estado `model_mismatch` cuando el modelo configurado difiere del que consta en el índice, nombrando ambos.
- **`api/main.py`** — `/health` pasa a `async` y compone el informe. Conserva el retorno `dict[str, Any]` y no añade ruta, así que **`openapi.json` no cambia**.
- **`indexing/set_hash.py`** — **corrección de un defecto de C13**: `_dotnet_guid_sort_key` ordenaba como el `Guid.CompareTo` del .NET Framework (con signo) cuando .NET Core compara sin signo, equivalente al orden de bytes. Los dos lados nunca coincidían y `drift_count` no podía dar cero con un índice real.

### `backend-api` y `backend-application` — 6 archivos

`AiHealthController` en `api/ai/health`, `[Authorize(Roles = "Administrator")]`, y `AiHealthResponse`. En el cliente del gateway, `HealthAsync` sobre un **cliente HTTP con nombre propio y sin pipeline de resiliencia** (`HealthClientName`): sin disyuntor a propósito, porque su trabajo es diagnosticar precisamente cuando el camino principal falla. `HealthTimeoutMs` se valida al arranque junto al resto de presupuestos.

### `frontend-pages` y `frontend-services` — 3 archivos

Tarjeta de estado en `AdminDashboard.tsx` con componentes Metronic existentes (`card`, `badge`, `alert`, `skeleton`, `separator`), sin componentes nuevos. La discrepancia de modelo se presenta **como error y en texto**, no sólo por color, y el servicio inalcanzable se reporta sin tumbar el resto del panel: se carga fuera del `Promise.all` que gobierna el estado de carga.

### `openspec` y `docs` — 28 archivos

Change archivado con sus cinco artefactos, tres capacidades sincronizadas en las specs vivas, y catorce documentos de contexto puestos al día — cada uno porque el código lo contradecía. Detalle en la sección de notas.

---

## 🧪 Testing

**21 tests nuevos, todos en verde.**

| Suite | Nuevos | Cobertura |
|---|---|---|
| `ai-service` (pytest) | 10 en `tests/api/test_health_report.py` + 1 en `tests/indexing/test_orchestrator.py` | Base/índice/proveedor, discrepancia de modelo, **no llamar al proveedor** (con `forbid_network`), caché entre sondas, degradación con base caída, índice vacío que no es discrepancia, y un vector de hash que **sí distingue** los dos órdenes |
| Backend (xUnit) | 3 en `AiHealthControllerTests` + 4 en `AiGatewayHealthTests` | `AiHealth_ReturnsUnauthorized_ForAnonymousRequest` (con cliente nuevo de la factoría), `_ReturnsForbidden_ForOperatorRole`, `_DoesNotLeakConnectionStringOrApiKey` (sobre el cuerpo **crudo**), `AiHealth_BypassesCircuitBreaker_WhenGatewayCircuitIsOpen` |
| Frontend (Vitest + RTL) | 4 en `ai-service-status.test.tsx` | Tarjeta visible para administrador y ausente para operador, discrepancia como error, servicio inalcanzable sin tumbar el panel. Servicios mockeados con `vi.mock`, no dejados al simulador de red |

`ai-service/openapi.json` **sin cambios**, y su prueba de deriva en verde.

Comparación de suites **por nombres de test**, no por recuento: frontend, subconjunto estricto sin fallos nuevos; backend, el vaivén observado está en clases que este change no toca, y se comprobó ejecutándolas en aislamiento.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica: sin cambios de modelo**
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica: el contrato no se mueve, verificado con diff vacío**
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: 45 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

**Sobre producción: sin impacto.** Este PR no cambia el flujo de despliegue de la tienda, ni su módulo de Terraform, ni su imagen. Los tres ficheros de producción tocados reciben sólo cabeceras de deprecado.

**Sobre el entorno de demostración**, que ya está desplegado y verificado:

1. **Seis secretos** en el almacén de parámetros bajo `/jbg-demo/`, creados a mano y fuera del estado de Terraform. Dos de ellos —el token interno y la credencial del feed— son **un parámetro leído dos veces**, no dos parámetros: dos podrían derivar, y una derivación produce un 401 cuya causa el servicio tiene prohibido revelar.
2. **`bootstrap.sql` es un paso previo obligatorio** y de una sola vez: crea la extensión, el esquema `ai` y el rol `jbg_ai`. Sin él, `alembic upgrade head` falla con `password authentication failed for user "jbg_ai"`.
3. **Nunca `docker compose down -v`** en ese anfitrión: destruye el volumen del certificado, y la autoridad limita a cinco duplicados por semana.
4. El **nombre de dominio es un parámetro**: migrar al dominio propio no reconstruye ninguna imagen.
5. Requiere el **GitHub Environment `demo`** con el secreto `DEMO_DEPLOY_ROLE_ARN`, ya creado.

Runbook completo en `deploy/demo/README.md`.

### Acoplamientos entre componentes

| Frontera | Estado en este diff |
|---|---|
| **Backend ↔ Frontend** | El DTO `AiHealthResponse` y sus tipos TypeScript `ai-health.types.ts` **viajan juntos**. Sin desajuste pendiente |
| **Backend ↔ `jbg-ai`** | **Los claims del token interno no cambian.** `HealthAsync` no envía cabecera de autorización: `GET /health` es público en el lado de Python, y la restricción vive en el endpoint .NET, limitado a administradores |
| **`openapi.json`** | **Sin tocar**, verificado con diff vacío contra el commit previo al apply. La salud enriquecida conserva su retorno abierto precisamente para no mover el contrato congelado ni romper su prueba de deriva |
| **Migraciones EF Core** | Ninguna. El modelo de datos no cambia |
| **Código ↔ especificación** | Ambos lados en el diff: las tres capacidades sincronizadas en `openspec/specs/` y el change archivado |

**Orden de despliegue:** `jbg-ai` provee `/health` y el backend lo consume, así que el proveedor va antes o a la vez. En `compose.demo.yaml` ambas imágenes están fijadas al **mismo `IMAGE_TAG`** y se despliegan en la misma operación, de modo que «el entorno corre el commit X» sigue siendo un solo hecho.

---

## 📝 Notas adicionales

### Sin breaking changes

No se modifica ningún contrato REST existente, ni el contrato congelado de `jbg-ai`, ni el fichero de composición de desarrollo, ni la imagen de producción, ni el modelo de datos. **No hay migración**, ni de EF Core ni de Alembic.

### Siete defectos que sólo aparecieron desplegando de verdad

Cuatro de ellos son silenciosos — responden 200 y aparentan funcionar. Están documentados con su evidencia en el §9.bis del `qa.md` archivado:

1. **`drift_count` no podía dar cero nunca** (defecto de C13, corregido aquí). La prueba que lo guardaba usaba dos UUID de la misma mitad del rango, donde ambos órdenes coinciden, así que pasaba con la implementación correcta y con la incorrecta.
2. **La búsqueda servía el camino léxico degradado**, con 200 y resultados plausibles: C16 dejó una puerta de despliegue progresivo que `compose.demo.yaml` no abría. Es el hueco que la verificación de extremo a extremo existe para cazar.
3. **La API resembraba `admin`/`Admin123!`** —constante de un repositorio público— tras el truncado de la tabla de usuarios, en un anfitrión abierto a Internet. Cerrado con un `admin` desactivado que satisface la guarda del sembrador.
4. Dos trampas al fabricar hashes BCrypt fuera de .NET, y dos defectos propios de este change (`--unlink-first` sobre directorios no vacíos, y deriva perpetua del proveedor OIDC).

### Límites de la verificación, declarados

De 52 escenarios entre las tres specs, **49 verificados**. Los tres restantes están anotados en el §11 del `qa.md` con su razón: el reinicio por política tras una terminación no pedida (Docker excluye el `kill` manual por diseño, y el núcleo descarta la señal cuando viene del propio espacio de nombres), el cambio de nombre de anfitrión (necesita un dominio que no existe) y el fallo por índice vacío (leído, no ejercitado).

### Deuda anotada, no resuelta

En `openspec/DEFERRED_TASKS.md`: la bifurcación de `/health` en vida y disponibilidad con sus tres disparadores; el presupuesto de recuperación **medido** en la demo (170–1707 ms) y deliberadamente **no revertido**; el dimensionado medido; y que **los workflows de test nunca se han ejecutado** porque disparan sobre ramas que no existen — causa que `Documentos/testing-backend.md` ya documentaba y que este change confirma empíricamente.

### Para quien revise

El diff es grande (73 archivos), pero **28 son documentación y artefactos de OpenSpec**. El código de producción son 15 archivos: 3 en `ai-service`, 6 en backend y 3 en frontend, más los 3 de infraestructura ejecutable (`deploy.sh`, `verify.sh`, `compose.demo.yaml`). Los puntos que más merecen mirada son `set_hash.py` —cambia un hash que compara dos sistemas— y `AiGatewayServiceCollectionExtensions.cs`, donde el cliente nuevo se registra **sin** pipeline de resiliencia a propósito.



---

<a id="pr-23"></a>
## #23 — feat(ai-service): agrupacion asistida de familias de producto y su aprobacion por lote

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c18a-add-family-suggestion-and-approval` → `ai-eng` |
| Creada | 2026-08-31 |
| Integrada | 2026-08-31 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/23 |

### Descripción

## 📋 Descripción

C18a llena la tubería de familias de producto, que C07, C12 y C13 dejaron construida entera y vacía: la entidad, sus cinco endpoints de administración, la emisión de `familyId` en el feed y la columna `family_id` en `ai.product_document` existían, y no había una sola fila. Esta PR añade el motor que las propone y el camino que las escribe.

El agrupador vive en `ai-service/src/jbg_ai/families/` y es **determinista y sin red**: no llama a ningún LLM ni al proveedor de embeddings, y no toca el esquema `public` por SQL. Agrupa por raíz de nombre normalizada dentro de un mismo `piece_type`, fusiona grupos que difieren en exactamente un material, y guarda contra raíces degeneradas. El embedding **no agrupa: veta**, y lo hace en relativo —contra las otras familias propuestas, nunca contra un umbral absoluto— marcando al miembro para revisión en lugar de eliminarlo (`families/veto.py:apply_relative_veto`).

El reparto de responsabilidades es el mismo patrón que `AiCatalogController.EnrichBatch` de C09: `jbg-ai` propone y .NET persiste. `POST /api/ai/catalog/family-suggestions` devuelve propuestas **sin escribir nada**; `POST /api/ai/catalog/family-suggestions/apply` persiste el subconjunto que el administrador devuelve, siempre a través de `ProductFamilyService`. No hay tabla de propuestas ni estado intermedio, y por tanto **no hay migración de EF Core ni de Alembic** en el diff.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

> Sobre el último: el `proposal.md` del change etiqueta la novena ruta como **BREAKING** porque mueve un contrato declarado congelado. Con el criterio de `breaking-and-risk.md` **no lo es**: añadir un endpoint no rompe a ningún consumidor, y `ai-service/openapi.json` se regenera en este mismo diff, así que el test de snapshot queda en verde. Se deja sin marcar y se explica en *Notas adicionales*.

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-08-31-add-family-suggestion-and-approval/` (archivado en esta rama, 64/64 tareas).
- **Historia de usuario**: `Documentos/Historias/AI-Eng/HU-AIENG-018a.md`.
- **Informe del lote**: `Documentos/Proyecto Final AIEng/informes/c18a-family-suggestion-report.md`.

El `design.md` del change documenta por qué se hace **ahora** y no más tarde: llenar `Familia:` y `Variante:` en el documento canónico cambia `doc_text`, `source_hash` y el vector de ~30 % del corpus, y `embedding_version` no lo distingue —es `modelo:dims:preprocessing_id`, y esto altera contenido, no preprocesado—. Cualquier medición tomada antes describiría un corpus que este change sustituye por debajo sin que nada lo señale.

También cierra la **decisión abierta 4** de `Documentos/Proyecto Final AIEng/joiabagur-ia-especificaciones-funcionales-v2.md` §10 —si `ProductFamily` se crea manualmente, por IA o mediante flujo mixto—, que quedó sin resolver desde las especificaciones v2.

---

## 🔄 Cambios realizados

### `ai-service` — motor de agrupación

Paquete nuevo `src/jbg_ai/families/`:

- `vocabulary.py`: **no declara ningún término**. Reutiliza los vocabularios cerrados de `enrichment/vocabularies.yaml` (C09) y su `fold()`. Lo único nuevo es el **rango canónico de tallas**, que el vocabulario no puede aportar porque agrupa por escala y no ordena por magnitud. `FamilyVocabulary.size_at()` / `material_at()` emparejan **frases**, más largas primero, acotadas por el término más largo del propio vocabulario (`_span`).
- `naming.py:parse_name()`: normaliza sobre `enrichment.vocab.fold` y retira **un** token de talla **de cualquier posición**, no solo del sufijo. `_surface_form()` recupera la grafía original, de modo que la etiqueta conserva su acento.
- `grouping.py:build_candidate_groups()`: excluye lo ya asignado (regla de convergencia), aplica la puerta de `piece_type` —el nulo es valor propio, no comodín—, agrupa por raíz, fusiona por material en `_fuse_on_material()` **sin retirar material de la raíz**, y rechaza raíces degeneradas y grupos con etiquetas duplicadas devolviendo el motivo.
- `veto.py:apply_relative_veto()`: marca al miembro que tiene un producto de otra familia propuesta más cerca que su propio peor hermano, por más de un margen de configuración. **Marca, nunca elimina.**
- `repository.py`: lectura SQLAlchemy Core de solo lectura sobre `ai.product_document`. Las similitudes se calculan en PostgreSQL con `<=>`; no se cargan vectores en Python.
- `orchestrator.py:suggest_families()` y `errors.py`.

Ajuste nuevo `jpv_family_veto_margin` en `config/settings.py` (`JPV_FAMILY_VETO_MARGIN`, default `0.05`, rango `[0, 1]`).

### `ai-contracts` — la novena ruta

- `api/routers/families.py`: `POST /v1/families/suggest` con `get_catalog_principal` (sin `pos_id`, como las rutas de índice de C13). Responde `503` nombrando `DATABASE_URL` cuando falta, y `422` ante un `piece_type` desconocido en vez de una respuesta vacía plausible.
- `api/schemas/families.py`: seis modelos Pydantic; la respuesta lleva **tres** listas —propuestas, grupos rechazados y productos excluidos— más el recuento de los ya asignados.
- `stubs/responses.py:families_suggest_stub()`: fixture determinista para `STUB_MODE`.
- `ai-service/openapi.json` regenerado (+295 líneas): nueve rutas `/v1`.

### `backend-application`

- `IAiGatewayClient.SuggestFamiliesAsync()` y su implementación en `AiGatewayClient`: cuarta operación del cliente. Usa el cliente HTTP de enriquecimiento —comparte su presupuesto y su cortacircuitos, no los de recuperación— y exige `AiCallScopeKind.Catalog`.
- `FamilySuggestionService`: `SuggestAsync()` registra propuestas, rechazos y exclusiones juntos; `ApplyAsync()` recorre el lote familia a familia y captura `ProductFamilyConflictException` **por familia**.
- `ProductFamilyService.CreateFromSuggestionAsync()`: escribe `Origin = FamilyOrigin.AiApproved`, `ApprovedByUserId` y `ApprovedAt` — **primera escritura de las tres columnas** que C07 reservó en la primera migración y dejó sin ejercer.
- `Validators/FamilySuggestionValidators.cs`: FluentValidation del cuerpo de `apply`, incluida la detección de un producto declarado en dos familias del mismo lote.
- DTOs en `DTOs/Ai/AiFamilySuggestionDtos.cs` y `DTOs/Ai/FamilySuggestionBatchDtos.cs`; registro en `ServiceCollectionExtensions`.

### `backend-api`

Dos acciones en `AiCatalogController`, ambas solo para administradores:

- `SuggestFamilies()` → `200` con las propuestas; `503` tanto para `AiNotImplementedException` como para `AiUnavailableException`. **Sin fallback degradado**: a diferencia de la búsqueda, no hay respuesta parcial honesta.
- `ApplyFamilySuggestions()` → valida explícitamente (el proyecto registra validadores sin pipeline automático) y devuelve `200` con los recuentos y la lista de conflictos.

### `openspec`

- Capacidad viva nueva `openspec/specs/family-suggestion/spec.md` (9 requisitos, 32 escenarios).
- `ai-service-api-contracts`: la superficie congelada pasa de ocho rutas a nueve, con la regla de regenerar el snapshot en el mismo change.
- `ai-gateway-client`: dos requisitos nuevos (la operación y sus fallos tipados).
- `product-family`: el camino de escritura de la aprobación asistida.
- `openspec/project.md`: `Origin`, `ApprovedByUserId` y `ApprovedAt` dejan de describirse como «unused here and reserved».
- El change queda archivado en `openspec/changes/archive/2026-08-31-add-family-suggestion-and-approval/`.

### `docs`

`ai-service/README.md` (ruta, variable, changelog y el no-goal que **negaba** la existencia de la ruta), `ai-service/tests/README.md` (carpeta `families/`), `backend/README.md` (matriz de autorización y sección *Assisted grouping*), `README.md` raíz, `Documentos/arquitectura.md` (8 → 9 endpoints), `Documentos/modelo-c4.md` (Families Router, Family Grouper, Family Suggestion Service, **y los dos diagramas Mermaid**), `Documentos/testing-backend.md`, `Documentos/epicas.md` y el plan de changes.

---

## 🧪 Testing

**`ai-service` (pytest)** — `tests/families/` nuevo con `test_grouping.py`, `test_veto.py`, `test_vocabulary.py` y `test_invariants.py` (tests de propiedades sobre pertenencia única, orden sin huecos y unicidad de etiqueta), más `tests/api/test_families_route.py`.

Dos guardas se verificaron **fallando** antes de darlas por buenas, según registra el `qa.md` del change: `test_no_term_list_is_declared_inside_the_families_package` falla si alguien vuelve a declarar una lista de materiales dentro de `families/`, y `test_openapi_snapshot_is_stable` se comprobó en rojo *antes* de regenerar el snapshot.

**`backend` (xUnit)** — `FamilySuggestionControllerTests` (13 tests de integración) y `AiGatewayFamilySuggestionTests` (11 unitarios). El que separa esta implementación de una que falla en silencio es `ApplyFamilySuggestions_MakesMembersVisibleToAnIncrementalPull`: afirma **sobre el feed**, no sobre `Product.UpdatedAt`, porque crear una familia mueve el watermark por el `UpdatedAt` de la propia familia y el timestamp era el detalle de implementación.

Resultados medidos en esta rama:

- `uv run pytest`: **2 failed / 442 passed** — los dos son los del baseline, comparados por nombre (`tests/retrieval/test_orchestrator.py`).
- `FamilySuggestionControllerTests` en aislamiento: **12 de 12**.
- `dotnet test` completo: **920 descubiertos**, y **51 y 50 fallos en dos ejecuciones seguidas del mismo árbol** sin recompilar. Los 50 se reparten por 17 clases y **ninguno pertenece a una clase que esta PR toque**. Es la dependencia de orden preexistente que documenta `Documentos/testing-backend.md`, ampliada en esta PR con una nota fechada.
- `dotnet build JoiabagurPV.sln`: 0 errores.
- `openspec validate --all --strict`: **0 failed**.

- [x] Tests nuevos en el diff, en los dos componentes
- [ ] QA manual de la pantalla de revisión — **no aplica**: la pantalla es C18b

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: el diff no contiene ninguna migración, y es deliberado (las tres columnas ya existían desde C07)
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] Revisión humana del orden de despliegue (ver *Deployment notes*)

---

## 🚀 Deployment notes

**Orden de despliegue: `jbg-ai` primero, .NET después.** El backend llama a una ruta que solo existe tras desplegar el servicio de IA. Mientras no exista, ambas excepciones tipadas (`AiNotImplementedException` y `AiUnavailableException`) se traducen a `503` en `AiCatalogController.SuggestFamilies()` y **no se escribe nada**: es el modo de fallo diseñado, no una caída.

**Variable de entorno nueva**: `JPV_FAMILY_VETO_MARGIN`, **opcional**, default `0.05`. No hace falta provisionarla para arrancar ni para `/health`. Vive en configuración justamente para poder barrerse en C24 sin tocar código.

**Migración de datos, no de esquema.** El `qa.md` del change registra la ejecución sobre el corpus local: 156 familias y 486 miembros creados con `Origin = AiApproved`, 32 entradas que no son joyería terminada retiradas del índice poniendo `ProfileReviewStatus.Rejected` en su `ProductAiProfile` —**nunca `IsActive = false`**, que las sacaría también del TPV y `Encargos` es una línea de caja real—, y **una sola** sincronización incremental (`upserted 486 · deleted 32 · failed 0`). En cualquier otro entorno esos tres pasos son operación posterior al despliegue, no automáticos.

**Rollback**: borrar las familias con `Origin = AiApproved` y volver a sincronizar. El borrado cascadea a los miembros por la regla de C07 y los documentos pierden `Familia:` y `Variante:`, recuperando su hash anterior. No hay esquema que revertir.

---

## 📝 Notas adicionales

**Sobre la etiqueta BREAKING del `proposal.md`.** El change la usa en el sentido de «mueve un contrato declarado congelado», que es una decisión deliberada y documentada: la doctrina de `IAiGatewayClient` dice que cada endpoint contratado lo añade *el change que primero lo llama*. Operativamente no rompe nada —ruta nueva, `openapi.json` regenerado en el mismo diff, snapshot en verde— y por eso la casilla queda sin marcar. Si el criterio del equipo es marcarla igualmente por el hecho de mover la frontera, es cambiar una casilla.

**Riesgo: alto**, por el criterio de la referencia, y conviene decir de dónde sale. Lo dispara tocar `ai-service/openapi.json` más la migración de datos ya ejecutada. **No** hay cambios en autenticación, ni en `Program.cs`, ni en entidades de dominio, ni migraciones de EF Core, y `frontend/`, `terraform/` y `.github/` no aparecen en el diff.

**Dos correcciones de método que quedaron por escrito**, porque el error es más instructivo que el resultado:

1. El veto se implementó primero como `mediana − k·MAD` contra el centroide del grupo. Es una prueba *dentro* del grupo, mientras que la medición que la justificaba era *entre* grupos: marcaba al miembro menos típico de cada clúster —que todo clúster tiene por definición— y disparaba al 16,9 %. La prueba comparativa que quedó marca **15 de 486 miembros (3,1 %) en 5 familias**. El `design.md` conserva ambas versiones con su fecha.
2. La primera versión del test del watermark afirmaba sobre `Product.UpdatedAt` y falló, con razón: el requisito es que el feed vea a los miembros nuevos, y el timestamp era el mecanismo, no el requisito.

**Cola de revisión sin pantalla hasta C18b.** Los 15 miembros marcados, los grupos rechazados y los productos excluidos solo se leen hoy en el informe versionado. Es coste aceptado: la pantalla de revisión y la alerta de huérfanos son C18b, y un rechazo no se recuerda entre llamadas porque no se persisten propuestas.

**Hallazgos de calidad de catálogo que esta PR no resuelve** y quedan anotados en el informe y en el §0 del plan de changes: C09 forzó un `piece_type` a seis servicios de taller porque su vocabulario cerrado no admite «no es una pieza»; nueve joyas sintéticas legítimas tienen `piece_type` nulo porque `piece_type.terms` solo nombra ocho tipos; y `Cadena Barbara oro 40/42/45 cm` es una familia real que el agrupador no ve, porque su eje de variante son centímetros. Los tres se proponen como change propio (`fix-enrichment-vocabulary-gaps`), no incluido aquí.



---

<a id="pr-24"></a>
## #24 — feat(ai): revisión humana de familias y alerta de huérfanos — décima ruta del contrato (C18b)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c18b-add-family-review-ui-and-orphan-alert` → `ai-eng` |
| Creada | 2026-09-01 |
| Integrada | 2026-09-01 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/24 |

### Descripción

## 📋 Descripción

C18b añade la **revisión humana de las familias de producto** y la **alerta de huérfanos**, sobre la agrupación asistida que dejó C18a. El objeto de la pantalla no son propuestas nuevas: son las **156 familias que nadie había mirado** —todas con `Origin = AiApproved`, aprobador e instante de un lote que se disparó de una vez, y cero familias `Manual`— y los **682 productos activos sin familia** que el agrupador no puede volver a ver, porque converge excluyendo a los que ya pertenecen a alguna.

El núcleo es `POST /v1/families/audit`, **décima ruta** del contrato congelado, que en una sola llamada devuelve los **miembros que los vectores no sostienen** —un producto de otra familia queda más cerca que su peor hermano— y los **huérfanos candidatos**. Son la misma comparación leída desde los dos lados de la línea de pertenencia, y por eso van en una ruta y no en dos. La nominación de huérfanos usa **margen relativo a la cohesión de la familia destino, nunca un umbral absoluto**; la pureza de vecindad se reporta pero **no nomina**.

En .NET entra la entidad `FamilyReviewVerdict` sobre el par `(producto, familia)`, que hace tres trabajos con una fila: lista de descartes, memoria de la auditoría, y el **sello de aprobación por ítem** que la aprobación por lotes de C18a no podía dar. La pantalla de administración distingue **tres estados por lista** —calculada con contenido, calculada y vacía, y no disponible— puestos en el tipo y no en el render, porque sobre una pantalla de calidad de catálogo *«no hay nada que revisar»* se lee como *«el catálogo está limpio»*, que es justo la conclusión que este change existe para sostener con evidencia.

La revisión **se ejecutó de verdad** antes de cerrar: 58 juicios humanos, 7 decisiones aplicadas al catálogo e índice reconciliado.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [x] 💥 breaking change — el contrato congelado de `jbg-ai` pasa de 9 a 10 rutas `/v1`

---

## 🎯 Motivación y contexto

**Change de OpenSpec:** `openspec/changes/archive/2026-09-01-add-family-review-ui-and-orphan-alert/` (archivado en esta misma rama, 68/68 tareas).
**Historia:** [`HU-AIENG-018b`](Documentos/Historias/AI-Eng/HU-AIENG-018b.md) · **Informe del lote:** [`c18b-family-review-report.md`](Documentos/Proyecto%20Final%20AIEng/informes/c18b-family-review-report.md)

Dos problemas concretos:

1. **No había evidencia de revisión humana.** El checklist de entrega pide tasa de corrección y tiempo medio de revisión, y las 156 familias registraban al administrador que lanzó un lote, no un juicio sobre ninguna familia en particular.
2. **La cola de revisión que este change iba a pintar ya no existía.** Los 15 miembros marcados de C18a vivían en una respuesta de `suggest` que nunca se persistió, y sus productos pertenecen hoy a familias, así que quedan excluidos de toda ejecución posterior. Pintar aquella cola no es posible; **recomputarla sobre las familias que existen sí**, y es la misma comparación.

---

## 🔄 Cambios realizados

### `ai-service` — el motor de auditoría

- **`families/audit.py`** (nuevo): orquestador que **reutiliza `apply_relative_veto` de C18a con otro universo** (familias persistidas en vez de propuestas), no lo reimplementa. Nomina huérfanos por margen relativo y omite los pares ya juzgados que le llegan en la petición.
- **`families/repository.py`**: `PersistedMember`, `OrphanCandidate`, `load_family_memberships` y `load_orphan_candidates` — una consulta con CTE de peor hermano, puerta de `piece_type` dentro del join y LATERAL de pureza. **Lee sólo `ai.product_document`**, nunca el esquema `public`.
- **`api/routers/families.py`**: la ruta `POST /v1/families/audit`.
- **`config/settings.py`**: `jpv_family_orphan_margin` (default `0.0`).
- **`enrichment/vocabularies.yaml`**: **una línea** — `dorado: baño de oro` en `materials.synonyms`. Recupera familias sin reenriquecer, porque el agrupador lee `name` y no `materials[]`.
- **`migrations/env.py`**: `fileConfig(..., disable_existing_loggers=False)` — ver *Notas adicionales*.

### `ai-contracts` — el contrato congelado se mueve

- **`openapi.json`** regenerado: entra `/v1/families/audit`. Es la segunda vez que la frontera se mueve desde C02, y como C18a, se regenera en el mismo change.
- **`api/schemas/families.py`**: `JudgedPair`, `FamilyAuditRequest` (`piece_type`, `veto_margin`, `orphan_margin`, `max_orphans`, `judged_pairs`), `FlaggedMemberModel` y el resto del modelo de respuesta.

### `backend-domain` / `backend-data` — la entidad y sus tres migraciones

- **`FamilyReviewVerdict`** con el **par como identidad**: se registra pertenezca o no el producto a esa familia hoy, porque un huérfano no tiene fila de pertenencia que lo lleve.
- **`FamilyReviewVerdictConfiguration`**: índice **único** sobre `(ProductId, ProductFamilyId)`; `Outcome` como `integer` y **nunca `ENUM` de PostgreSQL**; **`CASCADE`** desde la familia y **`RESTRICT`** hacia `Product` y `User`.
- **Tres migraciones**, todas sobre la tabla nueva:
  - `20260831191040_AddFamilyReviewVerdict` — la tabla, sus tres claves ajenas y sus índices.
  - `20260831221511_AddFamilyReviewSeconds` — `ReviewSeconds double precision NULL`.
  - `20260831222840_AddVerdictSubjectPopulation` — `SubjectWasMember boolean NOT NULL DEFAULT false`.
- `FamilyReviewVerdictRepository`, `ProductFamilySummary` (en `Domain`, para no invertir la estratificación) y `FamilyReviewOutcome`.

### `backend-api` / `backend-application`

- **`AiCatalogController`**: `POST family-audit`, `POST family-verdicts`, `GET family-verdicts`, `GET family-review-metrics`.
- **`ProductFamiliesController`**: `GET /api/product-families` (paginado, tope 50, `400` ante un origen no reconocido) y `DELETE /api/product-families/{id}`. Ninguno de los dos existía.
- **`FamilyAuditService`**: `AuditAsync`, `RecordVerdictsAsync` (dedup último-gana, `SubjectWasMember` escrito **por el servidor**), `ListVerdictsAsync` con la acción pendiente calculada, y `GetMetricsAsync`.
- **`AiGatewayClient.AuditFamiliesAsync`**: exige ámbito de catálogo, valida `max_orphans` **antes de enviar**, y traduce un cuerpo vacío a fallo — nunca a resultado vacío.

### `frontend-services` / `frontend-pages`

- **`family-review.types.ts`**: `AuditOutcome` como unión discriminada — un llamante **no puede alcanzar las listas sin pasar por el estado**.
- **`family-review.service.ts`**: `getAudit` traduce cualquier fallo a `{ state: 'unavailable' }`, mientras `listFamilies` **propaga** el error. La asimetría es deliberada: una auditoría no disponible es un estado de la revisión; un listado que falla es un error corriente.
- **`pages/admin/family-review.tsx`**: cinco pestañas (Familias, Marcados, Huérfanos, Aplicar, Incidencias), cronómetro por ítem enviado con cada juicio, y edición de etiqueta sobre miembros ya existentes.
- Ruta `/admin/family-review` y entrada de menú bajo *Configuración*.

### `openspec` — archivado y specs vivas

Change archivado con sus siete artefactos. **Nace la capacidad `family-review`** (10 requisitos); `ai-service-api-contracts` 13 → 14, `ai-gateway-client` 14 → 16, `product-family` 10 → 12. Ninguna spec viva contiene sintaxis delta, verificado a mano.

### `docs`

`epicas.md` (EP13), `modelo-de-datos.md` (la entidad y el porqué de cada regla de borrado), `arquitectura.md` (9 → 10 endpoints), `modelo-c4.md`, la ficha del plan, los README de raíz, backend y `ai-service`, y las dos guías de testing con su entrada fechada.

---

## 🧪 Testing

**Suites completas, comparadas contra las líneas base versionadas en `baseline/` por nombre de test, nunca por recuento.**

| Suite | Línea base | Al cierre | Veredicto |
|---|---|---|---|
| `ai-service` (pytest) | 0 fallos / 356 | **0 fallos / 472** | +116 tests, cero rojo |
| Frontend (vitest) | 113 fallos / 533 | **113 fallos / 552** | **los mismos 113 nombres**, cero nuevos, cero arreglados |
| Backend (xUnit) | 47 fallos / 920 | 49 y 52 fallos / **973** en dos pasadas | ver abajo |

Las **siete clases** de la superficie tocada corren **133/133 en verde**: `FamilyReviewControllerTests`, `FamilyReviewVerdictSchemaTests`, `ProductFamiliesControllerTests`, `ProductFamilySchemaTests`, `AiCatalogControllerTests`, `FamilySuggestionControllerTests` y `AiGatewayFamilyAuditTests`.

Tests nuevos destacados:

- **ai-service** — `test_audit_flags_member_when_stranger_beats_worst_sibling`, `test_purity_does_not_nominate`, `test_orphan_nomination_never_crosses_piece_type`, `test_orphan_without_piece_type_is_never_nominated`, `test_audit_writes_nothing`, `test_audit_calls_no_provider`, `test_audit_is_deterministic`, `test_judged_pairs_match_regardless_of_guid_case`.
- **backend** — `Verdict_DismissedPair_ExcludedFromNextAudit`, `Verdict_SamePairTwice_CorrectsInsteadOfDuplicating`, `Verdict_FailedAudit_ChangesNothing`, `Metrics_RejectedMemberRemovedFromItsFamily_IsStillCountedAsAMember`, `DeleteFamily_CascadesVerdictsAndFreesProducts`, `DeleteFamily_StampsDepartingProducts`, `MoveProductBetweenFamilies_ReordersAndSwapsLabels_WithoutPhantomUpdate`, y nueve `Migration_*` de esquema.
- **frontend** — `should show the audit as unavailable when the ai service does not answer`, `should show an empty audit as computed and empty, not as unavailable`, `should keep family review usable when the audit is unavailable`, `should say when nothing was timed rather than showing a zero average`.

**Cuatro guardas verificadas fallando**, no sólo pasando: el snapshot del contrato antes de regenerarlo; un `UPDATE` inyectado en el repositorio de familias; la puerta `piece_type IS NOT NULL` retirada del SQL de huérfanos; y un `import` del cliente de embeddings en `audit.py`. Las cuatro muerden, y se restauraron.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo

`openspec validate --all --strict`: **47 passed, 0 failed**.

---

## 🚀 Deployment notes

**Orden de despliegue.** `jbg-ai` **antes** que el backend: la ruta `POST /v1/families/audit` debe existir cuando el cliente tipado la llame. Un backend nuevo contra un `jbg-ai` viejo recibe `501` y la pantalla lo pinta como *no disponible* — degrada, no rompe.

**Migraciones.** Tres, en serie y en este orden. `AddVerdictSubjectPopulation` añade una columna `NOT NULL DEFAULT false`, así que **las filas anteriores quedan en `false`**: si el entorno ya tiene veredictos registrados, necesitan backfill. El de este repo ya se aplicó con [`backfill-subject-population.sql`](backfill-subject-population.sql).

**Variable de entorno nueva.** `JPV_FAMILY_ORPHAN_MARGIN`, opcional, default `0.0`. Su ausencia no bloquea `/health`.

**Sin claves nuevas.** La auditoría **no llama al proveedor de embeddings**: lee los vectores que el índice ya tiene y calcula la similitud en la base con `<=>`. Requiere `DATABASE_URL` y responde **503** nombrándola si falta.

**Rollback.** Revertir las migraciones en orden inverso y el `openapi.json`. Los cambios de pertenencia se deshacen por los mismos endpoints que los hicieron. Respaldo `pre-c18b.dump` (39,9 MB) tomado antes de escribir la primera fila.

---

## 📝 Notas adicionales

### Breaking change acotado

El contrato congelado de `jbg-ai` pasa de **9 a 10 rutas `/v1`**, y el snapshot se regenera en este change como hizo C18a con la novena. `test_openapi_snapshot_is_stable` se verificó **fallando** antes de regenerarlo. Ningún consumidor existente cambia: sólo se añade superficie.

### Tres decisiones que se tomaron midiendo, no argumentando

- **El criterio de nominación salió al revés de la hipótesis.** Se esperaba que el margen relativo disparase de más y la pureza fuese más segura. Medido sobre el corpus, **la pureza dispara sobre 55 sintéticos frente a 19 reales** —los casi-duplicados sintéticos fueron construidos para ser familias distintas— y el margen relativo lo hace casi en exclusiva sobre huecos reales. La pureza quedó como señal de orden.
- **La precisión de la señal es baja y está medida:** 1 de 18 en miembros marcados (**6 %**) y 6 de 40 en huérfanos (**15 %**). No invalida la señal —18 juicios por un hallazgo real es una compra razonable— pero sí cualquier lectura automática: **nada se mueve sin que una persona lo diga**.
- **La precisión hereda la cohesión de la familia destino.** La misma familia que se llevó 7 de las 18 marcas atrajo 8 candidatos y no acertó ninguno; una familia estrecha nominó 2 y acertó 2. Ponderar por cohesión queda anotado para C28.

### Un fallo de Alembic que rompía la suite de Python, y no era de este change

`migrations/env.py` llamaba a `fileConfig(...)` sin `disable_existing_loggers=False`, y ese valor por defecto es `True`. Bajo el CLI es inocuo porque el proceso termina justo después; **en proceso es destructivo**, y los tests de migración corren Alembic en el mismo intérprete, dejando muertos los loggers de `jbg_ai` para todo lo posterior. Se arregla con **tres tests de regresión**, uno de los cuales fija que el valor por defecto *habría sido* destructivo.

### Lo que queda fuera, y dónde está escrito

- **Los atajos de teclado de la pantalla se descopan a C28**, con nota fechada en `design.md` y en las dos fichas del plan. La tarea que los daba por hechos estaba mal marcada.
- **La carcasa compartida no se extrajo.** Abstraer con un solo inquilino a la vista produce la abstracción equivocada; tres de las cuatro cosas que C28 pide por escrito ya existen en la pantalla.
- **Dos familias manuales** —`Cadena` y `Alianzas`, 9 SKU— heredadas a C28: la auditoría no puede verlas porque `cadena` no tiene ni una familia de su tipo contra la que calcular margen.

### Puntos de atención para quien revise

1. **`backfill-subject-population.sql` está en la raíz del repo.** Es el registro de una operación puntual ya ejecutada. Decidir si se conserva como traza o se mueve/elimina.
2. **El estampado del watermark no está verificado.** El segundo pase de sincronización salió con `since: null` y barrió los 1.168 documentos; el estado final es correcto y está comprobado, pero un barrido completo **tapa exactamente el fallo** que esa comprobación buscaba.
3. **`DashboardServiceTests` aparece en rojo y no es de este change.** `GetGlobalStatsAsync_WithSalesToday_ShouldReturnCorrectKPIs` construye ventas restando días a `UtcNow` y afirma un total **mensual**: falla los primeros cinco días de cada mes. Documentado en `Documentos/testing-backend.md`.
4. **Un 4xx que emite el servicio no se distingue por tipo de una indisponibilidad.** `TranslateStatus` es compartido por todas las rutas del cliente; el requisito de la spec se corrigió para **nombrar el límite en vez de taparlo**, y estrecharlo no es de este change.



---

<a id="pr-25"></a>
## #25 — feat(ai-service): expansión de consulta con diccionario de sinónimos (C20)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c20-add-synonym-dictionary` → `ai-eng` |
| Creada | 2026-09-01 |
| Integrada | 2026-09-01 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/25 |

### Descripción

## 📋 Descripción

C20 añade la **expansión de consulta con diccionario de sinónimos** que consumirá la rama léxica de C21. `ai.product_document.tsv` —columna generada `to_tsvector('spanish', doc_text)` con índice GIN— está poblada en las 1.168 filas vivas desde C05 y **no la consulta nadie**. C21 la encenderá, y medido contra ese índice contestaría **cero documentos** a frases ordinarias del oficio: `gargantilla dorada` 0, `collares de plata` 0, `criollas de oro` 1 de 102 posibles.

El diccionario es de **dos capas**. `enrichment/vocabularies.yaml` aporta las clases de equivalencia base y **no se modifica** —tocarlo obligaría a `enrichment/v2` y a reenriquecer el corpus, que es otro change—; `retrieval/query_synonyms.yaml` añade lo que no debe entrar en el contrato de extracción. `expand_query` es una **función pura** que devuelve **grupos de equivalencia más los términos resueltos**, nunca una cadena reescrita: medido, una sola `tsquery` ensanchada saca del top-10 los tres productos llamados literalmente «Sortija», y fusionando por RRF la lista original con la expandida vuelven a las posiciones 1, 2 y 3 conservando los 144 candidatos.

**La entrega es observe-only y se declara como tal.** La expansión se calcula en cada recuperación real y se registra como `stage=expand` con `consumed=False`, pero **no se consume** hasta C21: la respuesta de `POST /v1/retrieval/products` es idéntica antes y después de esta PR. No cabía otra forma —`openapi.json` está congelado con el lado .NET, así que ningún endpoint podía exponerla, y el harness que la juzgará (C24) está dos changes aguas abajo— y la alternativa era una biblioteca que no se ejecuta ni una vez.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-09-01-add-synonym-dictionary/` (archivado en esta misma rama, 4/4 artefactos, 27/27 tareas).
- **Historia de usuario**: [HU-AIENG-020](Documentos/Historias/AI-Eng/HU-AIENG-020.md) · ticket técnico `T-AIENG-020` en el change.
- **Épica**: EP14 — Búsqueda Semántica Híbrida.

La decisión 4 de la revisión del diseño sacó `SearchAliases` del perfil de producto por ser texto generado por IA y persistido por producto, con deriva. Su sustituto acordado (§7.4 del diseño RAG) es un diccionario del dominio aplicado **en consulta, nunca en indexación**. Esto es ese diccionario.

C20 está pintado 🟢 en el plan pero **es el tapón del grafo**: era el único prerrequisito que le faltaba a C21, y C21 bloquea a la vez a C24 (harness de evaluación) y a C30 (generación).

---

## 🔄 Cambios realizados

### `ai-service` — 8 archivos

- **`retrieval/synonyms.py`** *(nuevo)*: cargador de dos capas y `expand_query`. Emparejamiento sobre texto plegado (`fold()` / `ClosedVocab.resolve()` de `enrichment/vocab.py`, reutilizados y no reimplementados) y **emisión sobre formas de superficie con diacríticos**. Reducción de plural en ambos lados, aplicada sólo cuando la forma reducida ya está en el diccionario. Emparejamiento por frase más larga primero. `lru_cache`, como `load_vocabularies()`. Errores de carga vía `SynonymDictionaryError`.
- **`retrieval/query_synonyms.yaml`** *(nuevo)*: overlay de consulta con `classes`, `bridges` y `exclusions`, cada entrada con la medición que la justifica.
- **`retrieval/measure.py`** y **`retrieval/__main__.py`** *(nuevos)*: `python -m jbg_ai.retrieval measure`. Sólo lectura, `connection.read_only = True`, y **salta limpiamente con código 0** cuando no hay base alcanzable. Compone la `tsquery` con `plainto_tsquery` por forma, `||` dentro del grupo y `&&` entre grupos: los términos viajan como parámetros y no se concatena sintaxis.
- **`retrieval/orchestrator.py`**: llamada a `expand_query`, etapa de log `stage=expand` junto a `stage=embed` y `stage=search`, y parámetro `expand_synonyms` en `retrieve_products`. Comentario explícito en la llamada al embed: se embebe **la consulta original**, nunca una forma expandida.
- **`config/settings.py`**: `jpv_query_expansion_enabled` (default `true`), su validador de cadena en blanco y el pin en `canonical_openapi_settings`.
- **`indexing/cli.py`** y **`indexing/__main__.py`**: `run_module` carga `backend/.env` mediante `jbg_ai.data.envload.load_local_env()`, como ya hacía `python -m jbg_ai.data` desde C06b. Va en `run_module` y **no** en `main` porque los tests llaman a `main`.

### `deps` — 2 archivos

- **`pyproject.toml`** / **`uv.lock`**: se declara `python-dotenv>=1.0`. `data/envload.py` la importa desde C06b y funcionaba sólo porque `pydantic-settings` y `litellm` la arrastran. El lock no mueve versiones: sólo registra la arista directa.

### `tests` — 8 archivos, +551 líneas

- **`tests/retrieval/test_synonyms.py`** *(nuevo)*: 22 tests — capas, precedencia, artefactos del stemmer, plurales, frase más larga, término desconocido, flag apagado, pureza, exclusiones y direccionalidad de los puentes.
- **`tests/retrieval/test_measure.py`** *(nuevo)*: composición segura de la `tsquery` y salto limpio sin base de datos.
- **`tests/retrieval/test_orchestrator.py`**: `stage=expand` con `trace_id`, barrido de dos configuraciones en un proceso, respuesta invariable con el flag encendido y apagado, y que el vector embebe el texto original.
- **`tests/api/test_health.py`** y **`tests/api/test_contracts.py`**: `/health` no carga el diccionario, y `RetrievalRequest` no tiene campo de expansión.
- **`tests/config/test_settings.py`**, **`tests/support/settings.py`**, **`tests/indexing/test_cli.py`**: default y pin del flag, y las dos guardas del cargador de entorno.

### `openspec` — 12 archivos

- Change archivado en `openspec/changes/archive/2026-09-01-add-synonym-dictionary/`.
- **`openspec/specs/query-expansion/spec.md`** *(nuevo)*: capability viva, 12 requisitos y 26 escenarios, en formato de spec viva —`# … Specification`, `## Purpose`, `## Requirements`— y no volcando el delta.
- **`openspec/specs/ai-service-runtime/spec.md`**: de 9 a 10 requisitos con el flag de expansión, junto al del umbral de distancia.
- **`openspec/project.md`** y **`openspec/config.yaml`**: las dos listas normativas de settings opcionales de `jbg-ai` incluyen ya `JPV_QUERY_EXPANSION_ENABLED`.

### `docs` — 8 archivos

`README.md` (§1.2 y §2), `ai-service/README.md`, `ai-service/tests/README.md`, `Documentos/arquitectura.md`, `Documentos/epicas.md`, el plan de changes del Proyecto Final, la HU nueva y el informe `ai-service/evals/results/c20-query-expansion-reach.md`.

De paso se cierran **dos huecos que no son de C20**: `families/` faltaba en el `## Layout` de `ai-service/README.md` desde C18a, y `retrieval/` nunca estuvo en la lista de carpetas del README raíz pese a existir desde C14.

---

## 🧪 Testing

`ai-service`: **510 tests en verde** (474 en la base). Los 36 nuevos son pytest offline: la expansión es una función pura y `test_expansion_makes_no_database_or_provider_call` lo fija reutilizando la fixture `forbid_network`. Ningún test abre socket a proveedor de embeddings, LLM ni RDS, y ninguno exige que el índice tenga un número concreto de filas.

`openspec validate --all --strict`: **48 passed, 0 failed**.

**Medición reproducida** con `python -m jbg_ai.retrieval measure` contra el índice local de 1.168 filas, informe versionado en `ai-service/evals/results/c20-query-expansion-reach.md`:

| consulta | sin expansión | con expansión |
|---|---:|---:|
| `gargantilla dorada` | 0 | 64 |
| `collares de plata` | 0 | 66 |
| `criollas de oro` | 1 | 102 |
| `sortija de plata` | 3 | 144 |
| `aros de plata` | 22 | 205 |

`brazalete de cuero` se queda en 0 → 0, que es honesto y no un fallo: `cuero` tiene un solo producto en todo el catálogo.

**No verificable desde CI**: este repositorio no tiene CI activa — `test-backend.yml` y `test-frontend.yml` disparan sobre `main`/`develop`, ramas que no existen (documentado en `openspec/DEFERRED_TASKS.md`). Los recuentos de arriba son de ejecución local.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *no aplica a backend/frontend: esta PR no los toca. `ai-service` añade 36 tests para el código nuevo*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: sin cambios en el modelo de datos*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *no aplica: el contrato no se mueve y el snapshot no se regenera*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *diff vacío en `backend/`, `frontend/` y `terraform/`*

---

## 🚀 Deployment notes

**Sin impacto de despliegue obligatorio.** Ni migración de Alembic, ni de EF Core, ni extensión de PostgreSQL, ni configuración de búsqueda de texto, ni reindexado: `doc_text`, `tsv` y `source_hash` son idénticos antes y después.

- **Variable de entorno nueva y opcional**: `JPV_QUERY_EXPANSION_ENABLED` (booleano, default `true`). Su ausencia no bloquea el arranque ni `GET /health`, que nunca carga el diccionario. No hay que añadirla a Compose ni a SSM para que el servicio funcione.
- **Dependencia declarada**: `python-dotenv>=1.0`, ya presente de forma transitiva y ya resuelta en `uv.lock` a la misma versión. `uv sync` no descarga nada nuevo.
- **Comprobado que el paquete se construye completo**: `query_synonyms.yaml` viaja dentro del wheel (`jbg_ai/retrieval/query_synonyms.yaml`), junto a `vocabularies.yaml` y `sku_provenance.json`. Con instalación editable el fichero se resuelve desde el árbol de fuentes, lo que habría escondido un contenedor que revienta en el primer `expand_query`.
- **Rollback**: `JPV_QUERY_EXPANSION_ENABLED=false`. Y como nada consume los grupos hasta C21, incluso eso es redundante.

---

## 📝 Notas adicionales

**Sin breaking changes.** El comportamiento observable de `POST /v1/retrieval/products` es idéntico: sólo aparece una línea de log más. Es deliberado y es lo que hace seguro archivar C20 antes de que exista su consumidor.

**Tres decisiones que conviene mirar en la revisión, todas con su medición en `qa.md`:**

1. **Los puentes entre vocabularios son direccionales.** La primera medición dio `bano de oro` 0 → 436, cifra que el diseño no predecía: la unión simétrica hacía que una consulta por el baño —420 € de media— arrastrase las **282 piezas de oro macizo de 587 € de media**. La dirección contraria sí hace falta (los 64 de `gargantilla dorada` vienen enteros de incluir `oro`). Con puentes por dirección queda en 154. Las donaciones se toman de un snapshot previo a todos los puentes, porque si no la dirección se cuela transitivamente por un segundo puente.

2. **La deduplicación es por mayúsculas y nunca por plegado.** La primera versión plegaba con `fold()`, y así la forma tecleada `bano de oro` **suprimía** la acentuada `baño de oro`, dejando el grupo sin la única forma que alcanza esos 38 documentos. El stemmer español pliega tildes agudas pero **no la `ñ`**.

3. **`piel` → `cuero` está excluido con motivo medido**, y la exclusión está escrita en el propio YAML: los 7 documentos que casan dicen «sobre la piel», piel humana en prosa comercial, y `cuero` tiene un producto. Es el ejemplo de por qué el diccionario se cura y no se genera.

**Limitación declarada**: el diccionario se cura **contra el corpus, no contra demanda observada**. `public."ProductSearchEvents"` tiene 31 filas y 12 textos distintos, todos escritos por el desarrollador y en vocabulario canónico. Está dicho en `ai-service/README.md` y lo re-mide C24 con relevancia graduada.

**Deuda que esta PR no paga** y sigue asignada a C21/C22 en `openspec/DEFERRED_TASKS.md`: el cliente de embeddings se construye por petición y `AiGateway:RetrievalTimeoutMs` sigue en los 2500 ms temporales de C16. C20 no añade ni una llamada al proveedor, así que ni la empeora ni la arregla.

**Para quien abra C21**: hereda `matched` (`término tecleado → campo → canónico`) para su extracción de filtros por reglas, la composición de `tsquery` verificada arriba, y el hecho —comprobado contra este índice— de que PostgreSQL absorbe un grupo de sólo stopwords a cualquier lado de `&&`, así que no hay que filtrarlos. Comparte zona `retrieval/`, por eso C20 se archiva antes.



---

<a id="pr-26"></a>
## #26 — feat(ai-service): fusionar rama léxica y vectorial con RRF ponderado

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c21-add-hybrid-search-rrf` → `ai-eng` |
| Creada | 2026-09-02 |
| Integrada | 2026-09-02 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/26 |

### Descripción

## 📋 Descripción

Conecta los dos cables que C05 y C20 dejaron pelados. `ai.product_document.tsv` —columna generada `to_tsvector('spanish', doc_text)` con índice GIN— estaba poblada desde C05 y **ninguna consulta la leía**; la expansión de sinónimos de C20 se calculaba, se registraba como `stage=expand` y no la consumía nadie. `POST /v1/retrieval/products` pasa a fundir **tres listas ordenadas** —la tecleada (`websearch_to_tsquery`), la expandida (`plainto_tsquery` por forma emitida) y la vectorial— mediante RRF ponderado a profundidad simétrica.

Tres módulos nuevos en `ai-service/src/jbg_ai/retrieval/`, separados porque cada uno tiene un consumidor distinto ya previsto: `fusion.py` es puro y sin dominio para que C23, C25 y C26 lo importen sin pasar por este endpoint; `filters.py` es la costura que C25 sustituirá por pesos calibrados; `lexical.py` compone la `tsquery`. Se suma `cache.py`, la caché acotada que hace viable el singleton del cliente de embeddings.

**El contrato no se mueve**: `ai-service/openapi.json` no aparece en el diff y `backend/` no se toca en absoluto. Lo que sí cambia es el comportamiento observable del endpoint — ver *Notas adicionales*.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

> No se marca *breaking change*: los esquemas de petición y respuesta no se mueven y .NET no necesita cambio alguno. Sí hay **cambios de comportamiento declarados**, listados al final.

---

## 🎯 Motivación y contexto

Change de OpenSpec: [`openspec/changes/archive/2026-09-02-add-hybrid-search-rrf/`](openspec/changes/archive/2026-09-02-add-hybrid-search-rrf/) (C21, 38/38 tareas, archivado en esta misma rama). Historia: [`Documentos/Historias/AI-Eng/HU-AIENG-021.md`](Documentos/Historias/AI-Eng/HU-AIENG-021.md). Mediciones de la exploración: [`Documentos/Proyecto Final AIEng/informes/c21-hybrid-exploration-measurements.md`](Documentos/Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md).

El problema está medido, no supuesto: sirviendo solo desde la rama vectorial, el recuperador acertaba **67 de 120** en el top-10 sobre doce consultas de operador, con `dije de plata` en **0/10**, y fallaba **sin abstenerse** porque el umbral de 0,65 deja pasar 1.168 de 1.168 documentos.

La medición contra el índice real **refutó cuatro puntos escritos antes**, y el `design.md` del change los recoge uno a uno:

| Lo que decía la ficha | Lo medido |
|---|---|
| Conjunción estricta entre grupos | Deja **7 de las 10** consultas reales en cero documentos |
| `@>` para consultas multi-material | Alcanza **60** documentos frente a **913** de `&&`; 126 documentos no tienen materiales extraídos |
| Realce de SKU y nombre exacto | No compra nada: un nombre exacto ya encabeza ambas listas léxicas, y ante un SKU la rama vectorial devuelve **cero** candidatos |
| Paridad de peso entre ramas | Es la **peor** de las fusiones: 96/120 frente a 105/120 con peso vectorial 0,33 |

---

## 🔄 Cambios realizados

### `ai-service` (11 archivos, +1578/−137)

- **`retrieval/lexical.py`** (nuevo): composición segura de la `tsquery`. Un `plainto_tsquery` por forma emitida, formas OR-adas dentro del grupo y **grupos OR-ados entre sí**, con todo término como parámetro ligado. `SPARSE_VOCABULARY_FIELDS` es constante de módulo —con su cobertura medida en el comentario— y excluye de la coordinación los campos cuya ausencia no es evidencia (`occasion_tags` 13 %, `style_tags` 11 %, `color_tags` 19 %, `size_label` 45 %).
- **`retrieval/fusion.py`** (nuevo): `fuse()` implementa `Σ wᵢ/(k + rankᵢ)` sobre N listas, devolviendo orden fusionado y procedencia por candidato. Sin sesión, sin proveedor, sin dominio. `k` y `depth` son argumentos **obligatorios**: no hay valor por defecto en el módulo.
- **`retrieval/filters.py`** (nuevo): extrae techo de precio, talla y materiales del texto y los aplica como **orden por bloques estable**, nunca como exclusión.
- **`retrieval/cache.py`** (nuevo): `BoundedEmbeddingCache`, LRU con tope, inyectada por la costura de constructor que ya existía en `LiteLlmEmbeddingClient`. `indexing/embeddings.py` **no aparece en el diff**.
- **`retrieval/orchestrator.py`**: reescrito. `retrieve_products()` gana los parámetros `rrf_k`, `weight_typed`, `weight_expanded`, `weight_vector` y `branch_depth`; la rama léxica corre en `asyncio.gather` contra el **embedding**, no contra la búsqueda vectorial, y sus dos consultas van secuenciales para retener una sola conexión del pool. Desaparece `VECTOR_UNTIL_C21_NOTE`.
- **`retrieval/ports.py`** y **`retrieval/search.py`**: nuevo `LexicalHit` y `search_lexical()` en el puerto; SQL léxica sobre `ai.product_document` con `ORDER BY coordination DESC, ts_rank DESC`. `overfetch` se renombra a `depth`. Ambas ramas seleccionan `price` y `size_label` para poder degradar con ellos, sin ningún predicado sobre precio ni stock.
- **`config/settings.py`**: `FUSION_DEFAULTS` con los cinco ajustes nuevos, fijados también en `canonical_openapi_settings()`.
- **`api/main.py`** y **`api/routers/retrieval.py`**: el cliente de embeddings se construye una vez en `create_app()`; el router lo **resuelve** desde `app.state` en vez de construirlo por petición.
- **`retrieval/measure.py`**: subcomando `compare` que compara vector-only / lexical-only / fusión y escribe informe versionado.

### `frontend` (3 archivos, +92/−18)

- **`components/sales/assisted-search-result-row.tsx`**: la insignia de origen se deriva por resultado con `resultOrigin(matchReasons)` en lugar de la decisión única `aiAvailable`; se elimina esa prop. Se añade `searchOrigin(results, aiAvailable)`, que distingue `assisted` / `service-lexical` / `legacy-lexical` / `unknown`.
- **`pages/sales/assisted.tsx`**: nuevo aviso «Coincidencia semántica no disponible» cuando `searchOrigin` devuelve `service-lexical` — el caso en que el servicio responde 200 con resultados y `aiAvailable: true` habiendo servido solo la rama léxica, que hasta ahora era invisible en pantalla.
- **`types/ai-search.types.ts`**: solo documentación de `matchReasons` y `lowConfidence`; sin cambio de tipos.

### `tests` (14 archivos, +1923/−274)

Cuatro ficheros nuevos —`test_lexical.py`, `test_fusion.py`, `test_filters.py`, `test_cache.py`— más las extensiones de `test_orchestrator.py`, `test_search_port.py`, `test_measure.py`, `test_settings.py`, `test_retrieval_real.py` y `test_health.py`. En frontend, `__tests__/assisted-search-result-row.test.tsx` (nuevo) y dos casos en `__tests__/assisted.test.tsx`.

> El chunk `06-tests.diff` viene **resumido** (883 líneas > umbral 600): el análisis de `test_orchestrator.py` se apoya en las cabeceras de hunk, no en el diff completo.

### `openspec` (19 archivos, +2417/−55)

Change archivado con sus artefactos (`proposal`, `design`, `tasks`, `ticket`, `qa`) y sync de las specs vivas: **`hybrid-fusion` nace como capacidad nueva** con nueve requisitos; `vector-retrieval` baja de nueve a ocho al perder *Hybrid and lexical modes run the vector branch until C21*; `query-expansion` sustituye dos requisitos por otros dos; `assisted-search-panel` sube a catorce y `ai-service-runtime` a once. `DEFERRED_TASKS.md` registra el singleton como pagado con las cifras de latencia medidas.

### `docs` (11 archivos, +744/−18)

`modelo-c4.md` (tres afirmaciones que declaraban la fusión pendiente), `README.md` §1.2, `arquitectura.md` (árbol de módulos), `epicas.md`, el plan de changes (C21 a verde, recuento y párrafo *Hecho*), `ai-service/README.md` (párrafo C21, cinco filas de entorno y los dos cambios de comportamiento declarados), `tests/README.md`, y una nota de estado en §5.5 de las especificaciones funcionales. Se añade el informe `evals/results/c21-fusion-configuration-comparison.md`.

### `ai-tooling` (10 archivos, +60/−15)

`openspec/DEFERRED_TASKS.md` se registra en la matriz de impacto de la skill `update-docs`, con política `report-only`. Replicado a los cinco harnesses.

---

## 🧪 Testing

`ai-service` (pytest): **598 tests en verde**, sobre una línea base de 510 medida ejecutando la suite en el commit anterior a la implementación. Ninguno abre socket a proveedor, LLM ni RDS: el fake `FakeProductSearch` gana `search_lexical` y un campo `doc_text` que permite ejercitar la rama léxica sin configuración de texto en español.

Tests que fijan las decisiones medidas, por si se deshacen sin querer:

| Test | Qué impide |
|---|---|
| `test_groups_are_ored_with_each_other_and_never_conjoined` | Volver a la conjunción entre grupos |
| `test_vector_branch_weight_defaults_below_lexical` | Subir el peso vectorial «por simetría» |
| `test_surface_forms_use_plainto_not_phraseto` | Adjacencia posicional en formas multi-palabra |
| `test_multi_material_query_uses_contains_all` | Reintroducir `@>` (invertido: fija su exclusión) |
| `test_embeddings_module_is_unchanged` | Editar el módulo congelado en C11 (hash SHA-256) |
| `test_fusion_weights_and_k_load_from_settings_not_hardcoded` | Cablear pesos, `k` o profundidad en `fusion.py` |
| `test_only_one_lexical_query_is_in_flight_at_a_time` | Paralelizar las dos consultas léxicas y retener dos conexiones del pool |

Frontend (Vitest / RTL): 16 tests nuevos. La suite arranca en rojo en este repo, así que se comparó **por nombres de test fallido** contra la línea base: 113 fallos antes y 113 después, **cero nuevos**.

Medición contra el índice local (1.168 documentos) y el proveedor real, en `evals/results/c21-fusion-configuration-comparison.md`: sobre 24 consultas, vector-only **157/240**, lexical-only **219/240**, fusión por defecto **224/240**.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *el porcentaje no se mide en esta PR: `backend/` no se toca y el frontend añade tests sin retirar ninguno*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: no hay cambio de modelo de datos ni migración, ni de EF Core ni de Alembic*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *no aplica: el contrato no cambia y el fichero no está en el diff*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

**Cinco variables de entorno nuevas, todas opcionales y con valor por defecto**, así que un despliegue sin tocarlas se comporta con la configuración medida:

| Variable | Default |
|---|---|
| `JPV_RRF_K` | `60` |
| `JPV_RRF_WEIGHT_TYPED` | `0.5` |
| `JPV_RRF_WEIGHT_EXPANDED` | `0.5` |
| `JPV_RRF_WEIGHT_VECTOR` | `0.33` |
| `JPV_BRANCH_DEPTH` | `60` |

**Sin migración ni reindexado.** `doc_text`, `tsv` y `source_hash` no cambian: se verificó contra el índice local que las 1.168 filas activas siguen embebidas y compatibles con el `document_version_key` vivo, con cero filas desfasadas.

**Orden de despliegue:** `jbg-ai` es un contenedor aparte y es el proveedor del contrato; el frontend es consumidor indirecto a través de .NET. El cambio del panel es **inerte** hasta que el servicio devuelva un `match_reasons` distinto de `["vector"]`, así que las dos mitades no dependen del orden.

**Rollback sin desplegar código**: `JPV_RRF_WEIGHT_VECTOR=0` deja un recuperador solo léxico; poner los dos pesos léxicos a 0 restaura el comportamiento de C14 ordenado por RRF sobre una lista; `JPV_QUERY_EXPANSION_ENABLED=false` degrada a una sola lista léxica.

`AiGateway:RetrievalTimeoutMs` **sigue en 2500 ms**. El singleton baja la latencia en caliente a 76 ms, pero la primera llamada de cada texto distinto midió hasta 1328 ms, así que revertir a 800 ms sigue siendo un change aparte, anotado en `DEFERRED_TASKS.md` con las cifras nuevas.

---

## 📝 Notas adicionales

### Cambios de comportamiento declarados

Los esquemas no se mueven y ningún llamante necesita cambio, pero el endpoint responde distinto:

1. **`score` cambia de escala.** Deja de ser `clamp(1 − cosine_distance)` y pasa a ser el score RRF normalizado al primer resultado. Sigue en `[0, 1]` y sigue siendo monótono con el orden, que es lo que promete el contrato congelado. Como C04 lo persiste en telemetría, **las cifras de antes y después de C21 no son comparables**. La distancia mapeada se mueve a `debug.vector_score`.
2. **`match_reasons` deja de ser la constante `["vector"]`** y reporta procedencia real por resultado. La spec retirada deja su *Migration*: quien detectara una respuesta vector-only leyendo `vector_only_until_c21` en `debug.notes` debe leer `match_reasons`.
3. **Un fallo del proveedor en `mode=hybrid` ya no es siempre 503.** Si la rama léxica produjo candidatos se sirve con 200 y `match_reasons: ["lexical"]`; solo se responde 503 cuando no hay nada léxico que servir, porque un 200 con lista vacía sería indistinguible de una abstención legítima.
4. **`low_confidence` cambia de significado**: pasa a ser la ausencia de consenso entre ramas, y **solo cuando corrieron dos**. Con una sola rama ningún candidato puede aparecer dos veces, así que conserva el significado de C14 —no se devolvió nada—. Es señal, no cambia cuántos resultados se devuelven ni en qué orden.

### Limitación declarada y no arreglada

El umbral de distancia **no discrimina** entre consultas plausibles: medido, `<= 0.65` deja pasar 1.168 de 1.168 documentos en una consulta ordinaria y 0 ante texto sin sentido. Es un suelo, y lo que acota de verdad la lista vectorial es la profundidad de rama. Recalibrarlo exigiría un cuantil por consulta en vez de una constante, que es trabajo que la ficha de C25 ya reclama.

### Para quien revise

- La rúbrica de la medición **es la función objetivo de la propia rama léxica** (`doc_text` lleva líneas canónicas `Tipo:` y `Materiales:` y la expansión apunta a ellas), así que un brazo léxico puntúa bien por construcción. Las cifras fijan un punto de partida, no un veredicto: el juez es el golden set graduado de C24.
- De los dos objetivos que el ticket pedía reproducir, `sortija de plata` da **4/10 → 10/10** exacto y `criollas de oro` se queda en **5/10** frente a los 6/10 esperados. La discrepancia está declarada en `qa.md` §11.2 con su causa probable (la rúbrica de este CLI se deriva automáticamente de los términos que la expansión resuelve; la de la exploración se curó a mano).
- El `qa.md` del change registra siete incidencias de la implementación, incluidas tres premisas erróneas del propio autor donde el código tenía razón.



---

<a id="pr-27"></a>
## #27 — C22: sincroniza ai.pos_projection y acota la recuperación al surtido del punto de venta

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c22-add-pos-projection-soft-prefilter` → `ai-eng` |
| Creada | 2026-09-05 |
| Integrada | 2026-09-05 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/27 |

### Descripción

## 📋 Descripción

Conecta el tercer cable que quedaba pelado en la ruta de recuperación. C05 creó `ai.pos_projection`, C12 construyó `GET /api/ai/index-feed/pos-availability` y C13 escribió el cliente que lo lee — con prohibición explícita de consumirlo. La tabla llevaba **cero filas** desde entonces, así que el recuperador gastaba su ventana de 60 candidatos sobre el catálogo entero y `AssistedSearchRepository.Carried()` descartaba después, al hidratar, todo lo que el punto de venta no lleva.

Esta PR sincroniza la proyección desde el feed que ya existía, convierte el `pos_id` del token en el **único filtro duro** del recuperador —aplicado en SQL a las tres ramas—, y hace que el stock agotado **degrade sin eliminar**. Añade además el reloj de ventas inyectado (`IndexFeed:SalesAsOf`), que es lo que impide que `sales_30d` se vacíe a cero y que la tabla de ablations de C24 sea irreproducible.

Cruza de lenguaje: `ai-service/` (drenaje, alcance, degradación y guardias) y `backend/src/JoiabagurPV.Application` + `Infrastructure` (reloj inyectado y `computedAsOf` en la página del feed). Incluye **tres desviaciones declaradas** respecto a lo que decían los artefactos del change, detalladas en Notas adicionales.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [x] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

**Change de OpenSpec:** `openspec/changes/archive/2026-09-05-add-pos-projection-soft-prefilter/` (archivado en esta misma rama, 47/47 tareas).
**HU:** `Documentos/Historias/AI-Eng/HU-AIENG-022.md`.
**Informes:** `Documentos/Proyecto Final AIEng/informes/c22-exploration-measurements.md` (el antes) y `c22-implementation-measurements.md` (el después).

El problema es aritmético y está medido sobre el índice real: sobre 20 sondas, **ocho de los once puntos de venta** tenían al menos 6 de cada 20 búsquedas por debajo de una página de 10, con un peor caso de **un solo producto superviviente**. Para el operador eso es indistinguible de una abstención legítima: el panel de C16 pinta la misma pantalla de «no hemos encontrado nada».

En paralelo, el mundo sintético de C10 termina el **2026-08-23** y los agregados del feed se contaban contra el reloj de pared, así que `sales_30d` caía del 16,28 % de pares no nulos a **cero el 26 de septiembre**. C25 habría barrido pesos sobre una señal muerta y habría escrito en la tabla de ablations que las señales de negocio no mejoran el ranking — un artefacto del calendario registrado como hallazgo.

---

## 🔄 Cambios realizados

### `ai-service` — drenaje de la proyección

- `indexing/feed.py`: tipa los ítems del feed POS sobre el `fetch_pos_page` que ya existía — `PosUpsertItem`, `PosTombstoneItem`, `parse_pos_item`, y `QTY_BUCKETS = frozenset({"0", "1-2", "3+"})`. Un bucket fuera del vocabulario se rechaza **al parsear**, no se deja para que el `CHECK` aborte el lote. `PosFeedPage` gana `computed_as_of`.
- `indexing/pos_projection.py` (nuevo): repositorio de `ai.pos_projection`. `apply_page` escribe una página en una transacción; el tombstone es un `INSERT … ON CONFLICT DO UPDATE` con `is_assigned_hint = FALSE` y `qty_bucket = '0'` — **no hay ningún `DELETE` en el módulo**. `POS_FEED = "pos-availability"`.
- `indexing/pos_orchestrator.py` (nuevo): `sync_pos_availability` drena por cursor keyset propio, registra fallos por lote en `ai.sync_failure` sin abortar el resto, y emite `trace_id` (`new_trace_id()`) en cada línea de log. `EXHAUSTED_SINCE_ID = UUID(int=0)` es el cursor de agotamiento — el `Inventory.Id` del keyset nunca llega al cliente.
- `indexing/cli.py`: subcomando `sync-pos [--full]` y `run_async`, que en Windows usa un bucle selector porque psycopg rechaza el `ProactorEventLoop`. Sale **distinto de cero** si alguna página falló.

### `ai-service` — alcance, degradación y guardias

- `retrieval/search.py`: CTE `WITH scope AS MATERIALIZED` sobre `ai.pos_projection` (`pos_id = :pos_id AND is_assigned_hint IS TRUE`), aplicada a las tres sentencias. `ai.product_document` pasa a aliasarse como `d` porque el join hace ambiguo `product_id`. Añade `COUNT_SCOPE_SQL` y `PROJECTION_SYNCED_AT_SQL`.
- `retrieval/projection.py` (nuevo): `parse_pos_id` (claim que no parsea → `InvalidPosIdError`), `ProjectionFreshness` con caché de `FRESHNESS_CACHE_SECONDS = 10.0`, y `resolve_scope`, que decide vacía → 503, obsoleta → sin alcance, fresca → alcance.
- `retrieval/filters.py`: `demotion_rank` pasa de 3 a **4 componentes**, con `_out_of_stock` el último y binario sobre `OUT_OF_STOCK_BUCKET = "0"`.
- `retrieval/orchestrator.py`: resuelve el alcance antes de las ramas, lo pasa a `search` y `search_lexical`, y emite `stage=projection`; `stage=search` gana `scoped`, `depth` y `truncated`.
- `retrieval/ports.py`: `SearchHit` y `LexicalHit` ganan `qty_bucket`; el puerto gana `count_scope` y `projection_synced_at`.
- `config/settings.py`: `jpv_pos_prefilter_enabled` (default `true`) y `jpv_pos_projection_max_age_seconds` (default `3600`), fijados en `canonical_openapi_settings`.

### `ai-contracts` — el snapshot se mueve

- `api/schemas/retrieval.py` + `ai-service/openapi.json`: `RetrievalResponse` gana `projection_age_seconds` (`float | None`, `ge=0.0`). **13 líneas insertadas en el snapshot, ninguna borrada.**

### `backend-application` / `backend-api` / `backend-data` — el reloj inyectado

- `IndexFeedOptions`: `SalesAsOf` (`DateTime?`) y `SalesAsOfUtc`, que normaliza. Dos validaciones `ValidateOnStart` en `ServiceCollectionExtensions`: un valor con `DateTimeKind.Unspecified` —es decir, sin offset— **para el arranque**, porque el binder de configuración lo leería como hora local del host.
- `IndexFeedDtos.cs`: `IndexFeedPageDto` deja de ser `sealed` y nace `PosAvailabilityPageDto : IndexFeedPageDto` con `ComputedAsOf`. `IIndexFeedService.GetPosAvailabilityPageAsync` y el controlador devuelven el tipo derivado: `System.Text.Json` serializa por el tipo declarado, así que ensanchar la base habría añadido un campo permanentemente nulo al contrato del catálogo.
- `IndexFeedRepository.cs`: `LastSaleAt` pasa de `MAX(SaleDate)` a `MAX(CASE WHEN SaleDate <= now)`, acotado como ya lo estaban las dos ventanas.

### `openspec` y `docs`

- Change archivado en `openspec/changes/archive/2026-09-05-add-pos-projection-soft-prefilter/` y specs vivas sincronizadas: nace `openspec/specs/pos-projection/spec.md` (11 requisitos, 22 escenarios) y se reescriben tres requisitos MODIFIED en `index-feed`, `product-document-indexer` y `vector-retrieval`.
- Siete documentos de contexto puestos al día, cada uno porque el código contradecía una frase concreta (`modelo-de-datos.md`, `README.md` §1.2 y §2.3, `ai-service/tests/README.md`, `openspec/project.md`, `testing-backend.md`, `epicas.md` y el plan de changes).

---

## 🧪 Testing

**`ai-service` (pytest): 598 → 697, 0 failed.** La línea base se midió sobre el árbol limpio del commit de artefactos, no se supuso.

| Fichero | Antes → Después | Cubre |
|---|---|---|
| `tests/retrieval/test_pos_scope.py` | 0 → **34** | Claim malformado en seis formas; alcance en las tres ramas y tomado del token; fila en borrado blando fuera de alcance; degradación por stock que nunca elimina; frescura desde el checkpoint y con caché; 503 en vacío; degradación en obsoleto con log; flag que restaura el comportamiento previo; cifras de venta ilegibles desde el pipeline |
| `tests/indexing/test_pos_projection.py` | 0 → **21** | Mapeo camelCase; seis buckets fuera de vocabulario; idempotencia; borrado blando que conserva la historia; tombstone de par desconocido que inserta; el `CHECK` rechazando lo que el parser rechaza |
| `tests/indexing/test_pos_orchestrator.py` | 0 → **20** | Cursor de agotamiento; reanudación frente a `--full`; la fila `catalog` intacta; página fallida registrada sin abortar; `trace_id` en cada línea; código de salida del CLI; ausencia de ruta `/v1` y de planificador |
| `tests/migrations/test_c22_schema.py` | 0 → **5** | Columna anulable y sin default; **el resto de la tabla intacto**; reversibilidad |
| `tests/api/test_retrieval_projection.py` | 0 → **7** | 503 y no lista vacía; `/health` en 200 con proyección vacía y obsoleta; 422 por claim malformado; el contrato comprometido lleva el campo |
| `tests/retrieval/test_filters.py` | 15 → **21** | Clave de orden de 4 componentes con stock el último; bucket ausente ≠ bucket cero |

**`backend` (xUnit): 973 → 984.** `IndexFeedSalesClockTests` (5, nueva), `IndexFeedRegistrationTests` (+5), `AiIndexFeedPosTests` (+2).

Los tres nombres que exigía `tasks.md` existen: `SalesAggregates_WithConfiguredAsOf_CountWindowsAgainstIt`, `SalesAggregates_WithoutAsOf_FallBackToWallClock`, `PosAvailabilityPage_DeclaresComputedAsOf`.

**Sobre el rojo de `dotnet test`:** la línea base daba **52 fallos de 973** y el cierre **53 de 984**. Comparados por nombre aparecen 7 y desaparecen 6, todos `22001: value too long for type character varying(20)` — el teléfono de Bogus que documenta `CLAUDE.md`. Para descartar que fuera de esta rama se ejecutaron **dos veces las dos clases que rotan sobre el mismo binario con `--no-build`**: 11 y 13 fallos, con **10 nombres de diferencia**. Más rotación sin tocar una línea que la que separa las dos mediciones. **Cero fallos en las ocho clases del feed de indexación y del contrato (68 de 68).**

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica: ninguna migración de EF Core**. Sí hay una revisión de Alembic aditiva, ver Notas
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: 50 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] QA manual sobre el panel del operador — no ejecutado en esta rama

---

## 🚀 Deployment notes

**Orden, y el orden importa.** `jbg-ai` es el consumidor del feed que sirve .NET, así que el proveedor va primero:

1. **Aplicar la revisión de Alembic** `c9a71f2b6d54` (`ai.pos_projection.computed_as_of`). Aditiva, anulable, sin default: no hay backfill ni reescritura de tabla.
2. **Desplegar el backend .NET** con `IndexFeed:SalesAsOf` **ya fijado**. Un valor sin offset UTC **impide el arranque** — es deliberado.
3. **Ejecutar `python -m jbg_ai.indexing sync-pos --full`** una vez, para poblar la proyección y crear su fila de checkpoint.
4. **Desplegar `jbg-ai`.** Antes del paso 3, la guardia responde **503**, que es la respuesta correcta para una proyección sin sincronizar.

**Fijar el instante antes del primer drenaje, no después.** Una pasada incremental **no recalcula nada**: el feed sólo reemite los pares cuyo inventario se movió, así que cambiar el reloj más tarde deja los pares intactos con el reloj viejo. Recuperarse de ese orden cuesta un `--full`.

**Cron sugerido** (documentado en `ai-service/README.md`): `*/10 * * * *` sobre `sync-pos`.

**Variables nuevas:** `IndexFeed__SalesAsOf` (.NET, opcional; ausente = reloj de pared), `JPV_POS_PREFILTER_ENABLED` (default `true`), `JPV_POS_PROJECTION_MAX_AGE_SECONDS` (default `3600`).

**Rollback:** `JPV_POS_PREFILTER_ENABLED=false` devuelve la recuperación al comportamiento previo **sin desplegar nada**. `ai.pos_projection` puede quedarse poblada: no la lee nadie más.

---

## 📝 Notas adicionales

### Breaking changes

1. **`ai-service/openapi.json` se mueve por primera vez desde C13**, por un campo opcional de respuesta. **Compatible hacia atrás**: `AiContractSnapshotTests.Dtos_MatchCommittedOpenApiSchema` barre *de .NET hacia el contrato* —exige que cada propiedad .NET exista en el schema, no al revés—, así que un campo que .NET no declara no rompe nada. Sus 15 pruebas están en verde.
2. **La respuesta de `GET /api/ai/index-feed/pos-availability` gana `computedAsOf`.** El cliente Python lo trata como opcional, así que un feed anterior sigue siendo válido.
3. **`IndexFeedPageDto` deja de ser `sealed`.** El contrato JSON del feed de catálogo **no cambia**.

### Tres desviaciones respecto a los artefactos, declaradas y no disimuladas

1. **Se abre una revisión de Alembic**, contra el «sin migración de ninguna clase» que declaraban la propuesta, el diseño, un MUST de la spec, la HU y el ticket. `ai.pos_projection` no tenía columna donde persistir el instante de referencia que el propio alcance exige, y como el drenaje es incremental, sin ella la proyección puede acabar con filas contadas contra dos relojes distintos **e indistinguibles**. Diferirla no la ahorra: la traslada sobre una proyección ya contaminada. Los seis documentos quedan enmendados con el porqué.
2. **El filtro duro es `is_assigned_hint`, no la existencia de fila** — contra la lectura literal de la ficha. `Carried()` excluye exactamente eso, así que mantener un desasignado gastaría ventana para nada: el 7-9 % en los puntos de venta con operador. En consecuencia `test_unassigned_product_is_penalised_not_removed` se renombra a **`test_out_of_stock_product_is_penalised_not_removed`**, que protege el principio realmente en vigor.
3. **Dos cifras del diseño no se confirmaron al medirlas.** La exploración predijo 7,3 ms escopado frente a 10,8 ms; medido sobre la proyección poblada son **14,8-17,3 ms frente a 18,0-33,1 ms**. Y el plan real **filtra los 1.168 documentos por distancia y hace el join después**, así que la CTE **no ahorra cómputo**: lo que la justifica es la corrección —el subconjunto existe antes de ordenar, así que la profundidad de rama se respeta por construcción— no la velocidad. `design.md` queda corregido.

### Medido contra el feed real

Drenaje: 6.050 upserts + 670 borrados blandos = **6.720 filas** (exactamente las de `Inventories`), 34 páginas, 0 fallos, 10,9 s. **Deriva 0** contra el `aggregateHash`. Páginas cortas: de **8 de 11** puntos de venta a **ninguno**. `sales_30d` no nulos estable en **23,54 %** — no el 16,28 % que predijo el diseño, porque la ventana anclada cae en el pico de verano; la diferencia queda explicada en el informe, no redondeada.

### Para reviewers

- **La columna «después» de la tasa de llenado no es una medida de calidad.** El 60 es la profundidad de rama y se alcanza siempre, porque el surtido más pequeño supera la ventana. Esta PR garantiza que la página se llena, **no que se llene bien**: eso lo mide C24 con el golden set, etiquetado *sin escopar* a propósito para no mezclar calidad de recuperación con cobertura de surtido.
- **Una consecuencia operativa nueva:** HT-ARTRUTX tiene surtido cero y 144 filas en borrado blando, así que un token suyo recibe **503**. Es la respuesta correcta —no tiene nada que vender— pero conviene saberlo antes de encontrarlo en un log.
- **`sales_30d`, `sales_90d` y `last_sale_at` se escriben y no se lee ninguno.** Es deliberado: son la entrada de C25, y hay dos tests que fijan que el pipeline de recuperación **no puede** leerlos.
- **El frontend no entra en esta PR y no le hace falta**: `projection_age_seconds` es opcional y su consumidor de interfaz es territorio de C34/C36.



---

<a id="pr-28"></a>
## #28 — fix(ai-service): cerrar las lagunas de piece_type con enrichment/v2

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `fix1-enrichment-vocabulary-gaps` → `ai-eng` |
| Creada | 2026-09-05 |
| Integrada | 2026-09-05 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/28 |

### Descripción

## 📋 Descripción

`piece_type` era un vocabulario **cerrado de ocho hiperónimos**, fijado por C09 en `ai-service/src/jbg_ai/enrichment/vocabularies.yaml` y replicado en el prompt de extracción, en el espejo del frontend y en dos specs vivas. El catálogo contiene piezas que esos ocho términos no saben nombrar, y el extractor hacía ante ellas exactamente lo que se le pidió: dejar `piece_type` nulo o elegir el hiperónimo más plausible. Esta PR añade `diadema`, `gemelos`, `cinturon` y `llavero` a la lista cerrada, salta el prompt a **`enrichment/v2`** y propaga el cambio a los cinco sitios donde la lista está replicada.

El salto de prompt arrastra un segundo arreglo: `PROMPT_VERSION` (en `enrichment/constants.py`) y la ruta del fichero (en `enrichment/pipeline.py`) se declaraban **por separado**, así que mover uno sin el otro sellaría perfiles con una versión cuyo texto nunca llegó al modelo — una afirmación que parece cierta y no se puede comprobar después. `pipeline.py:_PROMPT_RELATIVE` deriva ahora la ruta de la constante, y `test_prompt_version_matches_the_loaded_prompt_file` fija la otra mitad: el encabezado del fichero cargado nombra esa misma versión.

`prompts/enrichment/v1.md` **no se edita ni se borra**: 1.178 perfiles siguen declarando venir de él y esa declaración tiene que seguir siendo verificable. El corpus queda por tanto **mezclado**, lo que se documenta en `ai-service/README.md` con su consecuencia: cualquier métrica agregada sobre atributos extraídos debe reportarse por `PromptVersion`.

### Tipo de cambio

- [ ] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Change de OpenSpec: **`fix-enrichment-vocabulary-gaps`** (FIX1), archivado en esta misma rama como `openspec/changes/archive/2026-09-05-fix-enrichment-vocabulary-gaps/`. Historia: `Documentos/Historias/AI-Eng/HU-AIENG-FIX1.md`. Nace de un hallazgo de C18a y va deliberadamente fuera de la numeración C.

**Un tipo erróneo es peor que un nulo.** El filtro de categoría es duro (`AND d.piece_type = :category`), así que una diadema etiquetada `broche` aparece cuando el operador filtra por broches. La exploración registrada en `informes/fix1-exploration-measurements.md` midió que de los 22 productos cuyo nombre lleva uno de los cuatro términos, **once no tenían tipo y nueve estaban mal tipados**: seis de los 85 documentos `broche` eran tres diademas, dos gemelos y un llavero, más dos diademas en `collar` y una en `colgante`.

Dos puntos de la ficha original quedaron refutados con medición, y ambos están recogidos en `Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md`:

1. **La población es de 22, no de 11.** Reenriquecer solo los nulos habría entregado una faceta «Diadema» que devuelve 5 de 11: no dice cero, dice cinco.
2. **Su criterio de extremo a extremo ya se cumplía antes del change.** *«Buscar "diadema" pasa de cero a resultados»* — medido, `diadema` ya alcanzaba 11 documentos por la rama léxica de C21, porque el nombre vive en `doc_text`. Los criterios se reescribieron como estructurales: nulos 11 → 1, faceta `diadema` 0 → 11, impostores en `broche` 6 → 0.

---

## 🔄 Cambios realizados

### `ai-service` (5 archivos, +38/−25)

- `enrichment/vocabularies.yaml`: `piece_type.terms` pasa de 8 a 12 con `diadema`, `gemelos`, `cinturon` y `llavero`. **Sin sinónimo de extracción** para ninguno: las variantes de consulta pertenecen al overlay de C20.
- `enrichment/constants.py`: `PROMPT_VERSION = "enrichment/v2"`.
- `enrichment/pipeline.py`: `_PROMPT_RELATIVE = Path("prompts") / f"{PROMPT_VERSION}.md"` — la ruta se deriva de la constante. Se conservan los tres candidatos de búsqueda y el mensaje de `FileNotFoundError` deja de nombrar `v1` fijo.
- `retrieval/query_synonyms.yaml`: se **eliminan** las cuatro `exclusions` de `llavero`, `diadema`, `gemelos` y `cinturon` — el motivo por el que estaban listadas dejó de ser cierto. Se añade la clase `piece_type / gemelos` con la forma de superficie `gemelo`, porque la reducción de plural corre singular←plural y el singular no puede alcanzar un canónico plural. Se reescribe el motivo de `filigrana`, que sigue abierta como hueco de `style_tags`.
- `retrieval/synonyms.py:_require_known_class()`: el error de ancla desconocida deja de apuntar a un change con nombre y apunta al vocabulario base. La frase anterior nombraba a FIX1, que es precisamente el change que esta PR archiva.

`prompts/enrichment/v2.md` es nuevo (+53). Su diff contra `v1.md` son tres bloques: el encabezado, la lista de doce términos, y la línea que advierte de que el catálogo puede contener servicios, consumibles y artículos de regalo, para los que `piece_type` es `null` — con la precedencia de la lista cerrada declarada por encima de esa advertencia.

### `frontend` (1 archivo, +8/−0)

- `src/lib/materials-vocabulary.ts`: `PIECE_TYPE_OPTIONS` pasa a doce entradas. El `value` es byte a byte el canónico del YAML porque viaja a `AND d.piece_type = :category` y se compara por igualdad exacta; **la tilde vive solo en el `label`** (`cinturon` / «Cinturón»). Ningún cambio en `pages/sales/assisted.tsx`: el `<Select>` itera sobre la constante.

### `tests` (5 archivos, +207/−12)

Detallado en la sección de Testing.

### `openspec` (11 archivos, +1278/−4)

- Specs vivas sincronizadas: `catalog-enrichment-pipeline` pasa de 8 a 9 requisitos (la lista canónica a doce, el escenario de `prompt_version` a `enrichment/v2`, y el requisito nuevo de que las filas que no son joyería terminada llevan tipo nulo) y `query-expansion` mantiene sus 12 requisitos con el de exclusiones reescrito.
- Los ocho artefactos del change se mueven a `changes/archive/2026-09-05-fix-enrichment-vocabulary-gaps/`.
- `DEFERRED_TASKS.md` registra las tres cosas que el informe deja sin ficha.

### `docs` (9 archivos, +957/−21)

- `ai-service/README.md`: sección nueva sobre versiones de prompt y la obligación de reportar por `PromptVersion`; se corrige la línea que fijaba `enrichment/v1` como versión vigente.
- `README.md` §2.3 y `ai-service/tests/README.md`: alineados con `v2` y con las carpetas de test que FIX1 tocó.
- `informes/fix1-exploration-measurements.md` e `informes/fix1-vocabulary-gaps-measurements.md`: la medición previa y el acta de la corrida.
- `epicas.md` y `proyecto-final-plan-changes-openspec.md`: FIX1 marcado como archivado, con sus dos refutaciones y los recuentos al día.

---

## 🧪 Testing

**+7 tests netos en `ai-service` (697 → 704, 0 fallos)**, según el registro de `openspec/changes/archive/2026-09-05-fix-enrichment-vocabulary-gaps/qa.md`. Un test renombrado: `test_prompt_version_is_enrichment_v1` → `test_prompt_version_matches_the_loaded_prompt_file`.

| Archivo | Tests |
|---|---|
| `tests/enrichment/test_vocabularies.py` | `test_new_piece_types_are_canonical_and_normalised` — los cuatro resuelven a sí mismos, `Cinturón` pliega a `cinturon`, y ni `tiara` ni `gemelo` son sinónimos de extracción |
| `tests/enrichment/test_llm.py` | `test_prompt_version_matches_the_loaded_prompt_file`, `test_superseded_prompt_versions_stay_in_the_repository`, `test_prompt_piece_type_list_matches_the_closed_vocabulary` (cruza la lista escrita en el prompt contra el YAML, para que la deriva falle en rojo) |
| `tests/enrichment/test_pipeline.py` | `test_a_null_piece_type_is_kept_and_not_defaulted`, `test_untypeable_jewel_stays_null`, `test_proper_name_containing_a_piece_type_does_not_beat_the_head_noun` |
| `tests/retrieval/test_synonyms.py` | `test_plural_canonical_is_reachable_from_its_singular` |
| `frontend/src/lib/materials-vocabulary.test.ts` | La lista fijada pasa a doce; test nuevo de que ningún `value` lleva tilde |

**Cuatro tests fijados saltan a propósito** y se actualizan de forma deliberada, que es para lo que se pusieron: `test_base_vocabulary_terms_are_pinned` (la tupla a doce), `materials-vocabulary.test.ts` (el espejo), `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in` (el conjunto de exclusiones se reduce a `piel` y `filigrana`) y `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap`, que usaba `diadema` como ejemplo de canónico desconocido y **falla con `DID NOT RAISE`** — la dirección contraria a la esperada, que es justo la que invita a borrarlo. **No se borró**: es el guardián que impide que una laguna entre como sinónimo, y su ejemplo pasa a `filigrana`.

`npm run build` limpio. La suite de frontend mantiene el mismo conjunto de nombres de test fallidos que la línea base (los preexistentes que documenta `Documentos/testing-frontend.md`).

---

## ✅ Checklist pre-merge

- [ ] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — 7 tests netos en `ai-service` y 1 en frontend
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: sin migración de ningún tipo, ni EF Core ni Alembic
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**: ninguna ruta, campo ni schema se mueve; el fichero no aparece en el diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `openspec validate --all --strict` reporta `0 failed`
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo — el espejo del frontend viaja en esta misma PR

---

## 🚀 Deployment notes

**Sin migración, sin variables de entorno nuevas y sin cambio de contrato.** `ai-service/openapi.json`, `source-text/v1`, `embedding_version` e `indexing/embeddings.py` quedan intactos: la plantilla del documento no cambia, solo el contenido de las filas reenriquecidas.

**Paso post-despliegue, y no es opcional.** Esta PR entrega el código, no los datos. El reenriquecimiento de la cohorte se ejecutó contra el corpus local y su acta está en `informes/fix1-vocabulary-gaps-measurements.md`; **en cualquier otro entorno los perfiles siguen en `enrichment/v1` hasta que se corra el mismo paso**:

1. `POST /api/ai/catalog/enrich-batch` con los 22 `productId` enumerados en el informe, `force: true` y `reviewMode: "AutoBulk"`, en un solo lote. Requiere el contenedor `jbg-ai` con `STUB_MODE=false` y `JPV_RAG_LLM_API_KEY`.
2. **Una** sincronización incremental del índice.
3. Comprobar el grupo de control: `SKU822` debe seguir siendo `broche` y `SKU882` `anillo`.

Sin ese paso el desplegable ofrece «Diadema» y devuelve lista vacía en ese entorno. `jbg-ai` es un contenedor aparte y provee el contrato, así que se despliega antes que su consumidor.

**Rollback**: revertir el código devuelve `PROMPT_VERSION` a `enrichment/v1`, pero **no revierte los perfiles ya reenriquecidos**, que seguirían declarando `enrichment/v2` con cuatro tipos que el vocabulario revertido no conocería. Un rollback real exige reenriquecer esos 22 productos con el prompt anterior.

---

## 📝 Notas adicionales

**La corrida encontró lo que ningún test podía encontrar.** La primera pasada de `v2` dejó **sin tipo a dos de los tres llaveros**: la línea nueva advierte de que el catálogo puede contener artículos de regalo, y un llavero *es* un artículo de regalo, así que el modelo hizo exactamente lo que se le pidió. `v2` declara ahora la precedencia de la lista cerrada sobre esa advertencia y la cohorte se volvió a correr entera. Con un `EnrichLlm` falso esto era invisible por construcción, y así se dice en el docstring de `test_a_null_piece_type_is_kept_and_not_defaulted`.

**Falso amigo medido, y grupo de control.** `Broche Cinturón de Orión` (SKU822) y `Anillo Cinturón de Orión` (SKU882) son la constelación, no la pieza. Añadir `cinturon` al vocabulario cerrado es justo lo que los pone en riesgo, y el informe registra que no se movieron campo a campo. Es el mismo patrón que la exclusión `piel → cuero` de C20.

**Lo que queda abierto**, registrado en `openspec/DEFERRED_TASKS.md`:

- `filigrana` sigue siendo una laguna, pero de **`style_tags`**, que es otro eje con sus propias puertas de cobertura. No tiene change asignado y es el ejemplo al que apunta ahora el test guardián.
- El endpoint que agregue los tipos realmente presentes en el surtido sigue sin ficha propia.
- `Llavero Cape Nao` Grande y pequeño comparten `piece_type` por primera vez y podrían formar familia; correr el agrupador de C18a quedó fuera de alcance.

**Deuda declarada, no oculta.** `Documentos/Historias/AI-Eng/HU-AIENG-009.md` sigue enumerando los ocho `piece_type` de C09: es una historia de usuario y le corresponde a `enrich-us`, no a la pasada de documentación. El informe de C18a también dice «ocho términos», y es un documento fechado que no se reescribe retroactivamente.

**Para reviewers.** El punto que más merece mirada es `retrieval/synonyms.py:_require_known_class()`: su mensaje de error nombraba a `fix-enrichment-vocabulary-gaps` como el destino de cualquier laguna futura, y ese change es el que esta PR archiva. Se generalizó para que la guía no sobreviva al change que nombraba, y la aserción del test guardián se movió con ella.



---

<a id="pr-29"></a>
## #29 — feat(ai-service): añadir el corpus de conocimiento y su índice de citas

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c23-knowledge-corpus-and-indexer` → `ai-eng` |
| Creada | 2026-09-06 |
| Integrada | 2026-09-06 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/29 |

### Descripción

## 📋 Descripción

Construye el **segundo índice** del sistema. `ai.product_document` responde a «enséñame anillos de plata» y no puede responder a «¿este anillo se puede mojar?», porque esa respuesta no vive en ningún producto. Las tablas `ai.knowledge_document` y `ai.knowledge_chunk` existían desde C05 con su forma final y **ningún código las escribía ni las leía**; esta PR aporta las dos mitades que faltaban: el contenido y el camino de ida y vuelta hasta él.

El paquete nuevo `ai-service/src/jbg_ai/knowledge/` cubre ingesta y consulta: carga y validación del corpus (`corpus.py`), troceado puro por secciones (`chunking.py`), persistencia idempotente con identidad determinista (`indexer.py`) y búsqueda híbrida con citas (`search.py`), más `sizing.py`, `offline.py` y `measure.py` para la convención de tallas y la medición. El corpus son 32 documentos Markdown versionados en `data/knowledge/`, generados contra ocho prompts versionados en `ai-service/prompts/knowledge/v1/`.

**Sin migración, sin ruta HTTP y con `ai-service/openapi.json` byte a byte idéntico.** La búsqueda se expone como `search.py:search_knowledge()`, un callable del propio servicio y no un endpoint: el único consumidor es C30, en el mismo proceso Python, y abrir una ruta obligaría a mover un contrato congelado para conectar dos módulos del mismo proceso. Todo campo que haría falta y la tabla no tiene vive en `metadata jsonb`, que ya lleva su índice GIN.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Change de OpenSpec: `openspec/changes/archive/2026-09-06-add-knowledge-corpus-and-indexer/` (archivado en esta misma PR, 58/58 tareas). Historia: [`HU-AIENG-023`](Documentos/Historias/AI-Eng/HU-AIENG-023.md). Capability viva nueva: `openspec/specs/knowledge-corpus/spec.md`.

Sin este índice, C30 no puede emitir `citations[]`: solo prosa. El riesgo que gobierna el diseño no es de código y está declarado en `design.md`: **el corpus lo redacta un asistente** —los textos comerciales que el diseño daba como «a pedir al negocio» nunca llegaron— y **la verificación de citas es estructural, no semántica**: confirma que la fuente citada existía y se recuperó, no que diga la verdad. De ahí que cada sección declare su `claim_scope` y que la limitación esté escrita en `ai-service/README.md` y sellada en `data/knowledge/_corpus.meta.json`.

---

## 🔄 Cambios realizados

### `ai-service` — paquete `knowledge/` (14 archivos, +2768 −48)

- **`corpus.py`** — descubrimiento, parseo y las siete reglas de autoría, validadas y no confiadas al autor: un `# Título` y solo secciones `##`, nada de texto antes de la primera sección, tope de 1.200 caracteres, `claim_scope` obligatorio por sección, modo descriptivo, prohibición de SKU/producto/precio y una pregunta de evaluación por documento. `missing_material_sheets()` deriva la cobertura del vocabulario cerrado de `enrichment/vocabularies.yaml`, que **lee sin modificar**: añadir `titanio` al vocabulario sin su ficha pasa a ser un defecto detectable.
- **`chunking.py`** — función pura, sin sesión ni proveedor ni socket. Una sección `##` = un chunk, sin solape; `compose_content()` mete el título del documento y el de la sección **dentro** de `content`, que es lo que los introduce a la vez en el embedding y en la `tsvector` generada por el esquema; la marca de `claim_scope` se retira antes de componer.
- **`indexer.py`** — `document_id()` y `chunk_id()` son `uuid5` sobre los slugs, **nunca `(document_id, chunk_index)`**: insertar una sección en medio desplazaría el índice de todas las posteriores y repuntaría en silencio cada cita. `knowledge_version_key()` calcula `knowledge/v1` **en este paquete** en vez de importar `document_version_key` de C11, que sella `source-text/v1`. Upsert por documento, borrado de lo que la ejecución no produce, y omisión del embedding cuando `content_hash` y `embedding_version` coinciden.
- **`search.py`** — rama vectorial k-NN con `<=>` (alineado con la clase del índice HNSW) más rama léxica sobre `knowledge_chunk.tsv`, fusionadas **importando** `retrieval/fusion.py` de C21 sin reescribir una línea. La `tsquery` se compone con `retrieval/lexical.py` desde los grupos de `retrieval/synonyms.py:expand_query()`. El conjunto de candidatos lo fija la rama vectorial: un chunk que el umbral rechazó no puede convertirse en cita por evidencia léxica.
- **`sizing.py`**, **`offline.py`**, **`measure.py`**, **`cli.py`**, **`constants.py`**, **`errors.py`** — tabla de equivalencia de talla leída del propio corpus, embebedor determinista e índice en memoria para medir sin proveedor, y Recall@3 / MRR / tasa de abstención sobre el fixture.
- **`config/settings.py`** — `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` y `JPV_KNOWLEDGE_HYBRID_ENABLED`, ambos opcionales y con default en `KNOWLEDGE_DEFAULTS`, del que beben el campo, el validador de export en blanco y el perfil canónico de OpenAPI. En el mismo archivo se retiran las cifras medidas de las descripciones de los `Field`: una cifra copiada en una descripción es una instantánea que nada re-mide.
- **`indexing/cli.py`** — subcomando `sync-knowledge [--full]`, con la misma carga de entorno que `sync` y `sync-pos`. Valida el corpus **antes** de escribir nada.

### `docs` — corpus, prompts y documentación (48 archivos, +6789 −25)

- **`data/knowledge/`** — 32 documentos y 161 secciones: 14 fichas de material —tres de ellas de piedras—, 4 de talla, 10 de FAQ y 4 de política. **Cero documentos `guion_venta`** de los cinco que el esquema admite, y no por recorte de alcance: un guion es texto imperativo y un fragmento imperativo recuperado dentro de un prompt es indistinguible de una instrucción. `data/knowledge/README.md` lleva las siete reglas de autoría.
- **`ai-service/prompts/knowledge/v1/`** — ocho prompts de bloque, uno por bloque de generación.
- **`ai-service/README.md`** — sección «The knowledge corpus and its index (C23)», los dos ajustes en la tabla de entorno, `Layout` con `knowledge/`, y la sección «What this corpus is, and what it is not».
- **`ai-service/tests/README.md`** — fila `knowledge/` en la tabla de carpetas; C23 sale de la fila `data/`, donde no dejó ningún test.
- **`Documentos/epicas.md`** y **`proyecto-final-plan-changes-openspec.md`** — C23 pasa a hecho, y se corrigen tres afirmaciones de la ficha que la implementación refutó: la zona (`data/` + `indexing/` → paquete propio `knowledge/`), el alcance (prometía guiones de venta) y `indexing/knowledge.py`, que nunca existió.

### `tests` (10 archivos, +1499 −1)

`ai-service/tests/knowledge/` con 8 archivos, espejo de `src/jbg_ai/knowledge/`, más el doble inyectable `tests/support/fake_knowledge_repo.py`.

### `openspec` (10 archivos, +1581 −1)

Change archivado y capability viva `knowledge-corpus` sincronizada (11 requisitos, 39 escenarios) en **formato de spec viva** —`# Specification`, `## Purpose`, `## Requirements`— y no copiando el delta. `project.md` completa `Key Documentation References`, que se había quedado en C13. `config.yaml` pasa de declarar un índice vectorial a declarar los dos.

### `ai-tooling` (5 archivos, +30 −0)

Área `knowledge-corpus` en `doc-impact.json`, replicada en los cinco harnesses. Va declarada **antes** del comodín `ai-service/**` porque el matcher devuelve la primera coincidencia.

---

## 🧪 Testing

`pytest` sobre `ai-service/tests/knowledge/`, íntegramente offline: sin llamadas reales a LLM, embeddings ni RDS. Los tests de base usan testcontainers con pgvector.

- **Trazabilidad e identidad**: `test_citation_id_resolves_to_a_file_and_a_heading_in_the_corpus`, `test_chunk_identity_is_stable_across_reindexing`, `test_inserting_a_section_does_not_repoint_existing_citations`.
- **Reglas de autoría**: `test_section_over_the_size_limit_fails_ingestion`, `test_document_with_text_before_first_section_is_rejected`, `test_corpus_contains_no_sku_product_or_price`, `test_corpus_contains_no_sales_script_document`, `test_corpus_does_not_depend_on_the_current_contents_of_the_catalogue`.
- **Cobertura derivada**: `test_every_canonical_material_has_exactly_one_sheet`, `test_a_new_vocabulary_term_without_its_sheet_is_a_failure`.
- **Indexación**: `test_running_twice_over_an_unchanged_corpus_leaves_the_same_rows`, `test_unchanged_section_is_not_re_embedded`, `test_reindexing_removes_chunks_no_longer_produced`, `test_reordering_sections_does_not_trip_the_unique_constraint`.
- **Búsqueda**: `test_knowledge_search_returns_chunk_with_citation_id`, `test_out_of_domain_question_returns_no_citation`, `test_hybrid_disabled_falls_back_to_vector_only`, `test_fusion_consumes_ranks_and_not_raw_scores`.
- **Guardias de congelación** (`test_frozen.py`): `test_embeddings_module_is_untouched` compara el SHA-256 de `indexing/embeddings.py`; `test_knowledge_opens_no_http_surface` comprueba que `openapi.json` no contiene la palabra `knowledge`; `test_the_knowledge_package_contains_no_ddl` prohíbe `create table`/`alter table`/`create index` en el paquete.

Resultado de la suite completa de `ai-service`: **798 passed, 0 failed**. `openspec validate --all --strict`: **51 passed, 0 failed**.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` — paquete por capacidad, como `enrichment/`, `families/` y `retrieval/`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — 8 archivos en `ai-service/tests/knowledge/`; el umbral porcentual es de backend y frontend, que esta PR no toca
- [x] Migración de EF Core incluida si cambia el modelo de datos — no aplica: cero migraciones, y el diff no toca `backend/`
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — no aplica: el contrato no se mueve y el archivo no aparece en el diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [ ] Revisado el impacto en otros componentes del monorepo — el diff no toca `backend/`, `frontend/` ni `terraform/`, pero la revisión cruzada la confirma un humano

---

## 🚀 Deployment notes

**Dos variables nuevas, ambas opcionales y con default en código.** Ninguna bloquea el arranque ni `GET /health`; un export en blanco se lee como «sin definir» y cae al default.

| Variable | Obligatoria | Default | Efecto |
|---|---|---|---|
| `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` | no | `0.81` | Corte de distancia coseno del corpus. Por debajo, la búsqueda devuelve **cero** fragmentos |
| `JPV_KNOWLEDGE_HYBRID_ENABLED` | no | `true` | Rama léxica de la búsqueda de conocimiento. En `false` degrada a vectorial puro |

Ambas aportan solo el **default**: el valor efectivo viaja como parámetro de la llamada, así que una comparación de configuraciones no necesita reiniciar el proceso.

**Sin migración**: las dos tablas existen desde C05 con su forma final. **Paso post-deploy**, opcional y manual: `python -m jbg_ai.indexing sync-knowledge`, que necesita `JPV_EMBEDDING_API_KEY` y `DATABASE_URL` y es idempotente. No necesita feed de índice: el corpus en git es toda la verdad.

**Rollback**: no indexar, o borrar las filas de las dos tablas de conocimiento. Ninguna otra parte del sistema las lee todavía, así que revertir no puede degradar producción. Para la mitad híbrida, `JPV_KNOWLEDGE_HYBRID_ENABLED=false` sin desplegar nada.

---

## 📝 Notas adicionales

**Breaking changes: ninguno.** No se elimina ni renombra ningún endpoint, DTO, entidad ni variable existente; las dos variables nuevas son opcionales con default; `openapi.json` no aparece en el diff y un test lo comprueba.

**Nivel de riesgo: bajo.** No toca autenticación, `JoiabagurPVDbContext`, entidades de dominio, migraciones de EF Core ni `terraform/`. Nada en la ruta de petición actual cambia de comportamiento: el código nuevo está **latente** hasta que C30 lo consuma, y la indexación es un comando manual. Archivos congelados verificados intactos en el diff: `indexing/embeddings.py`, `enrichment/vocabularies.yaml`, `retrieval/orchestrator.py`, `retrieval/search.py`, `retrieval/fusion.py`, `retrieval/synonyms.py` y `retrieval/lexical.py`.

**Puntos de atención para reviewers:**

1. **El corpus es sintético y la verificación de citas es estructural.** Puede pasar la comprobación al 100 % citando algo falso, con sello de verificado. Está declarado en `ai-service/README.md` y sellado en `_corpus.meta.json`, no escondido.
2. **`JPV_KNOWLEDGE_DISTANCE_THRESHOLD = 0.81` es provisional en un sentido concreto.** La especificación obliga a que la medición corra sin proveedor, así que el barrido usa el embebedor determinista de `knowledge/offline.py`, que puntúa solape léxico y no significado. Lo que queda calibrado es **la regla** —cero citas fuera de dominio es una restricción, no un término negociable contra el recall—; el **número** hay que volver a medirlo contra el embebedor de producción antes de que C30 lo ponga delante de un cliente.
3. **La tabla de tallas de anillo es un compromiso de la casa, no un estándar.** Su marca `establecimiento` ya lo señala. Confirmarla con el negocio es una verificación posterior no bloqueante: si sus tramos son otros, cambia una sección de un documento.
4. **`claim_scope` obliga a C30.** Un fragmento `establecimiento` no puede leerse a un cliente como si fuera un hecho comprobable fuera de la joyería; el consumidor está obligado a propagar la marca.

**Fuera de esta PR, con responsable:** `HU-AIENG-023` sigue redactada como trabajo por hacer y le corresponde al comando `enrich-us`.



---

<a id="pr-30"></a>
## #30 — feat(ai-service): añadir arnés de evaluación, golden set y líneas base

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c24-eval-harness-golden-set-and-baselines` → `ai-eng` |
| Creada | 2026-09-11 |
| Integrada | 2026-09-11 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/30 |

### Descripción

## 📋 Descripción

C24 construye el arnés de evaluación del recuperador y lo ejecuta. Hasta esta rama, las tres piezas de la búsqueda híbrida —expansión (C20), fusión RRF (C21) y prefiltro por punto de venta (C22)— se habían configurado contra una rúbrica que cuenta un acierto como «tipo de pieza y material correctos». Esa rúbrica es la función objetivo de la rama léxica: `doc_text` lleva líneas canónicas `Tipo:` y `Materiales:` y la expansión apunta justo ahí, de modo que premia por construcción a quien casa esas líneas. Los cuatro changes archivados que dependen de ella escribieron la misma frase, «C24 lo re-mide».

Esta PR entrega el juez que lo re-mide: un golden set de **48 consultas juzgadas y 56 escritas** (`ai-service/evals/golden/`) con relevancia graduada 0-2 y criterio de anotación escrito antes de etiquetar, un paquete `jbg_ai.evals` con carga y validación del conjunto, *pooling* de profundidad adaptativa, métricas, cinco configuraciones de línea base, runner, informe y persistencia opcional, y tres tablas nuevas en el esquema `ai` mediante una revisión de Alembic aditiva. `GET /v1/evals/runs` deja de ser un *stub* y sirve las ejecuciones persistidas **sin mover `openapi.json`**.

El resultado de la medición está en `ai-service/evals/results/c24-baselines-2026-09-07.md`: `v0-nombre` 0,082 de nDCG@5, `v0-fts` 0,454, `v1-vectorial` 0,548 y `v2-hibrido` 0,603. La rúbrica anterior queda refutada — daba a la rama vectorial 67 de 120 frente a 107 de la léxica, y contra un juez que no es parte del pleito la vectorial bate a la línea léxica. La PR incluye además **una desviación declarada que toca ruta viva**: las dos sentencias de `retrieval/search.py` ganan una clave de desempate, sin la cual `LIMIT` corta dentro de un empate y dos ejecuciones idénticas difieren.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

**Change de OpenSpec**: `openspec/changes/archive/2026-09-11-add-eval-harness-golden-set-and-baselines/` (archivado en esta misma rama, 84/84 tareas).
**Historia de usuario**: `Documentos/Historias/AI-Eng/HU-AIENG-024.md` (añadida aquí).
**Informes**: `Documentos/Proyecto Final AIEng/informes/c24-exploration-measurements.md` (exploración) y `c24-implementation-measurements.md` (implementación).

El problema técnico es de validez del juez, no de rendimiento. `proposal.md` lo resume: ninguna decisión del recuperador se tomó con una métrica de relevancia, y el riesgo dejó de ser teórico el 2026-09-06, cuando en el corpus de conocimiento de C23 un sustituto *offline* midió que la rama léxica ganaba +6,2 pp de recall y, contra el proveedor real, el veredicto se invirtió.

De ahí dos restricciones que gobiernan el diseño y se ven en el código: el golden set es un **artefacto versionado en git** y no una tabla (`evals/golden.py:load_golden_set`), porque cambiar la vara de medir debe pasar por revisión de código; y su composición la **valida el código y falla la carga** (`evals/golden.py:_validate_traceability`), porque un conjunto que no ataca los pleitos que debe arbitrar confirma por construcción a quien lo escribió.

---

## 🔄 Cambios realizados

### `ai-service` — el paquete de evaluación (33 archivos, +8.633/−12)

- **`src/jbg_ai/evals/` (19 módulos nuevos)**. `golden.py` carga `queries.jsonl` / `judgements.jsonl` y valida seis mínimos de composición —doce consultas cuyo mejor documento la rama léxica no alcanza tras la expansión, cinco que resuelven sólo a campos de baja cobertura, cuatro piedras distintas, las tres clases de entrada del diccionario, cinco fuera de dominio plausibles y cuatro literales—, más el anclaje a productos reales comprobado **por categoría** (`_validate_origin_anchoring`). `pooling.py` implementa la profundidad adaptativa (base 20, bloques de 10 mientras aparezcan relevantes, tope 60) y los juicios apendables por `(query_id, product_id)`. `metrics.py` calcula nDCG@5 graduado y su lectura binaria, más el desglose por origen del dato, `unjudged@5`, el desplazamiento sintético y la distribución de distancias por grado. `configs.py` + `baselines.py` definen las cinco configuraciones; `cag.py` / `cag_run.py` la línea base sin recuperación. `runner.py` orquesta y **no importa** `repository.py`, que es el sumidero opcional. `cli.py` expone `uv run evals`.
- **`src/jbg_ai/retrieval/search.py` (+13/−2)**. `_SEARCH_ORDER_LIMIT` y `_LEXICAL_ORDER_LIMIT` añaden `, d.product_id ASC` como **última** clave. Es un desempate, nunca una señal de ranking: sólo decide entre filas que la clave anterior ya declaró iguales.
- **`src/jbg_ai/api/routers/evals.py` (+46/−10)**. `list_eval_runs()` deja de devolver el *stub* con `STUB_MODE=false` y lee de `ai.eval_run` a través de `evals/repository.py:read_runs`, más reciente primero, con 503 si falta `DATABASE_URL`. Los modelos de request y response no se tocan.
- **`migrations/versions/d7c4e91b25a0_eval_run_case_result.py` (nuevo, 197 líneas)**. Crea `ai.eval_run`, `ai.eval_case` y `ai.eval_result`. Aditiva: ninguna tabla existente se altera y el `downgrade` las elimina sin dejar rastro, cosa que puede hacer porque los vocabularios cerrados son `CHECK` y no tipos enumerados.
- **Datos versionados**: `evals/golden/` (56 consultas, 3.926 juicios, 48 vectores congelados, `criterion.md`, `pricing.yaml` con `as_of` y fuente), `evals/configs/` (cinco YAML) y `evals/results/` (informe de líneas base, barrido, medición de CAG y detalle por consulta en `runs/<run_id>.jsonl`).

### `deps` — 1 archivo, +6/−0

`ai-service/pyproject.toml` añade `[project.scripts] evals = "jbg_ai.evals.cli:run_module"`. **No se añade ninguna dependencia**.

### `tests` — 12 archivos, +2.502/−4

Carpeta nueva `tests/evals/` (`conftest.py` más seis módulos) y dos ficheros fuera de ella: `tests/retrieval/test_tiebreak.py` y `tests/migrations/test_c24_schema.py`. Se modifican `tests/api/test_evals_gating.py` (cuatro escenarios nuevos para la ruta real), `tests/api/test_stub_mode.py` (`/v1/evals/runs` entra en `_REAL_WHEN_STUBS_OFF`) y `tests/support/fake_product_search.py`, cuyo doble pasa a ordenar por `(distance, product_id)` y `(-coordination, -ts_rank, product_id)` para espejar las sentencias.

### `openspec` — 15 archivos, +2.068/−4

Nace la capability viva **`retrieval-evaluation`** (`openspec/specs/retrieval-evaluation/spec.md`, 17 requisitos). `vector-retrieval` y `hybrid-fusion` ganan un requisito cada una —la rama trunca bajo un orden total— y `ai-service-api-contracts` sustituye el requisito de la ruta de evaluación entero: decía que devolvía «una lista determinista de ejecuciones» (un *fixture*) y pasa a servir ejecuciones persistidas, con lista vacía y 200 cuando no hay ninguna. Los diez artefactos del change se mueven a `openspec/changes/archive/2026-09-11-…/`.

### `docs` — 14 archivos, +2.099/−20

Además de la HU y los dos informes nuevos: `ai-service/README.md` documenta la CLI, las filas de entorno y **las cuatro limitaciones declaradas** (sin acuerdo entre anotadores, el anotador escribió parte del corpus, conjunto pequeño con ±0,13 sobre la porción real, y coste del prefiltro sin medir). `ai-service/tests/README.md` incorpora `evals/` a la guía de la suite. `Documentos/modelo-de-datos.md` documenta las tres tablas y sus índices; `modelo-c4.md` y `arquitectura.md` recogen el paquete y la ruta; `epicas.md` y el plan de changes marcan C24 como hecho. El párrafo de `README.md` §1.2 cierra con el veredicto medido.

---

## 🧪 Testing

**Suite `ai-service` ejecutada en local: `915 passed, 0 failed`** (`uv run pytest`, 90,5 s), con la base PostgreSQL levantada, de modo que los 15 tests marcados `@pytest.mark.db` corrieron de verdad y no se saltaron. Este repositorio no ejecuta los workflows de test en CI, así que la cifra es de ejecución local.

Lo que cubren los tests del diff:

- **`tests/evals/test_golden_validation.py`** — un test por cada requisito de la matriz de trazabilidad, cada uno con un golden set de *fixture* que lo incumple: menos de doce consultas sin anclaje, cuatro consultas sobre una sola piedra, una clase de sinónimo que el diccionario no corrobora, texto sin sentido presentado como fuera de dominio, una categoría íntegramente sintética.
- **`tests/evals/test_metrics.py`** — nDCG contra un valor **calculado a mano** sobre *fixture*, la lectura binaria como número distinto, el desglose por origen que nunca encoge el corpus, el desplazamiento sintético y los juicios con `source_hash` caducado.
- **`tests/evals/test_pooling_and_cag.py`** — el *pool* como unión sin repetición, la profundidad que se detiene cuando un bloque no aporta, el truncado determinista de un catálogo **mayor** que el presupuesto (no que «cabe»), y que ningún precio llega al contexto.
- **`tests/evals/test_reproducibility.py`** — dos ejecuciones con la misma procedencia dan métricas idénticas, y el arnés no llama al proveedor durante una corrida.
- **`tests/evals/test_provenance_and_report.py`** — la huella de índice distinta marca la comparación como no válida, el informe se escribe sin base de datos, y la regla de cambio de defaults se ejercita en sus cuatro desenlaces.
- **`tests/retrieval/test_tiebreak.py`** — compila las sentencias reales y afirma sobre el texto de su `ORDER BY` clave por clave, de modo que quitar el desempate del SQL rompe el test; y comprueba que la clave no reordena candidatos cuyas distancias o rangos difieren.
- **`tests/migrations/test_c24_schema.py`** — `@pytest.mark.db`: `upgrade`/`downgrade` reversible sin rastro, los `CHECK`, el orden que sirve la ruta y el borrado en cascada.
- **`tests/api/test_evals_gating.py`** — 200 con ejecuciones, 200 con lista vacía, ya no 501 con stubs desactivados, y ausencia de la ruta bajo perfil de producción.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [ ] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: el modelo de .NET no cambia; la migración es de Alembic, en el esquema `ai`*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *el contrato no se mueve: `openapi.json` no aparece en el diff y `test_openapi_snapshot_is_stable` pasa*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `openspec validate --all --strict`: `52 passed, 0 failed`
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *ningún archivo de `backend/`, `frontend/`, `terraform/` ni `.github/workflows/` aparece en el diff*

---

## 🚀 Deployment notes

**Requiere migración.** `alembic upgrade head` aplica la revisión `d7c4e91b25a0` (`down_revision = c9a71f2b6d54`). Es aditiva —tres tablas nuevas en el esquema `ai`, ninguna existente alterada— y su `downgrade` las elimina sin dejar rastro.

**Ninguna variable de entorno nueva en el servicio.** `config/settings.py` no aparece en el diff: el arnés no introduce ajuste propio y no mueve ningún *default*. Lo que la CLI necesita ya existe (`DATABASE_URL`, `JPV_EMBEDDING_API_KEY` sólo para `freeze-vectors`, `JPV_RAG_LLM_API_KEY` sólo para `evals cag`, `SSL_CERT_FILE` en Windows), y está documentado en `ai-service/README.md`.

**El comando `evals` es herramienta de desarrollo, no de tiempo de ejecución.** Aparece como `[project.scripts]`, así que requiere reinstalar el paquete (`uv sync`) para estar en el PATH; el servicio no lo invoca.

`GET /v1/evals/runs` sigue montándose **sólo** bajo perfil de desarrollo (`ENABLE_DEV_ENDPOINTS`), de modo que en producción la ruta no existe, igual que antes. Sin pasos post-deploy ni cambios de imagen.

**Rollback**: `alembic downgrade c9a71f2b6d54` y revertir el *merge*. Las tablas de evaluación no las lee nadie más que la propia ruta de desarrollo, así que perderlas no afecta a ninguna otra función; el informe normativo vive en git.

---

## 📝 Notas adicionales

**Breaking changes: ninguno.** `openapi.json` no está en el diff, los modelos de la ruta no cambian, no hay entidad ni DTO de .NET tocado, y ninguna variable de entorno nueva es obligatoria. El cambio de comportamiento de `/v1/evals/runs` —de 501 a 200 con stubs desactivados— era el que su propio *placeholder* anunciaba por escrito nombrando a este change.

**Riesgo: medio**, y concentrado en dos puntos que conviene mirar con calma:

1. **`retrieval/search.py` es ruta viva.** El desempate es una desviación declarada en `proposal.md`, no un descuido: sin una clave final de orden el `LIMIT` corta dentro de un empate y PostgreSQL puede devolver cualquiera de las filas, lo que convierte un arnés de regresión en un generador de ruido. La clave va **la última**, detrás de la distancia y detrás de `coordination`/`ts_rank`, y `test_tiebreak.py` afirma ese orden sobre la sentencia compilada.
2. **La revisión de Alembic.** Escrita a mano, como todas las de este repositorio (no se autogenera: C05 dejó índices HNSW/GIN y columnas generadas que `autogenerate` reescribiría).

**El cambio de *defaults* NO se hace, y ése es un resultado.** El barrido direccional (`evals/results/c24-sweep.md`) encuentra el óptimo en `wC` entre 0,75 y 1,0, con +0,057 global y +0,073 en las consultas nuevas, pero la partición de ajuste empeora 0,024 y la regla escrita **antes** de medir exige el mismo signo en las tres lecturas. Por eso `config/settings.py` sale de esta rama sin una sola línea de diff.

**Limitaciones declaradas, no mitigadas** (las cuatro están en `ai-service/README.md`): no hay acuerdo entre anotadores —el proyecto lo desarrolla una persona, y lo que sustituye a la conciliación es el criterio escrito antes de etiquetar, la agrupación por categoría y la relectura diferida—; el anotador escribió parte del corpus, que es irreducible y es la razón de que toda métrica se desglose por origen del dato; con 41 consultas en la porción real el intervalo de confianza es ±0,13; y lo que cuesta en recall el prefiltro por punto de venta no se mide, por decisión tomada en C22.

**Dos desviaciones de alcance abiertas durante la implementación**, ambas declaradas donde se usan: `Recall@5` se publica **también** con el denominador acotado a `min(5, |relevantes|)`, porque dos consultas tienen noventa documentos relevantes y la lectura clásica tiene ahí un techo estructural de 0,055 que mide el tamaño del catálogo y no el recuperador; y el conjunto juzgado es el *pool* más las respuestas que el autor declara (381 juicios de 3.926), porque cuatro de las doce consultas sin anclaje no las encontraba ninguna configuración.

**Puntos de atención para reviewers.** Vale la pena leer `evals/golden.py:_validate_traceability` —es lo que impide que el golden set confirme a C21 por construcción— y `evals/sweep.py`, donde la regla de decisión está escrita antes que la medición y `FUSION_DEFAULTS` se lee como suelo en lugar de redefinirse. Y en la migración, el `CHECK ((grade IS NULL) = unjudged)`: es lo único que impide declarar una tasa cómoda de no juzgados sobre filas que sí tienen grado.

**Deuda conocida que esta PR deja anotada, no resuelta**: la recalibración de `JPV_RETRIEVAL_DISTANCE_THRESHOLD` es alcance de C25 y la respuesta que C24 publica es negativa —las distancias de los documentos relevantes y las de los irrelevantes se solapan por completo, así que hace falta un cuantil por consulta y no un escalar—; y el campo `judged_at` de los juicios registra la sesión de etiquetado (6 de septiembre) mientras el criterio lleva la hora del reloj del fichero (00:22:40 del 7), un desfase explicado en `qa.md §2.2` y cuya corrección se aplaza a C25 para no falsear la procedencia de la única corrida.



---

<a id="pr-31"></a>
## #31 — C25: la fusion hibrida se compone en dos etapas, y el buscador aprende a callar

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c25-recalibrate-ranking-and-abstention` → `ai-eng` |
| Creada | 2026-09-12 |
| Integrada | 2026-09-12 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/31 |

### Descripción

## 📋 Descripción

C25 corrige un defecto de la fusión híbrida de C21 que el juez de C24 dejó al descubierto: **la fusión no fusiona, concatena**. Con la rama léxica sumando 1,00 votos repartidos en dos listas y la vectorial 0,33 en una, un documento léxico en el rango 60 —el peor puesto posible— puntúa 0,008333 y el mejor documento que sólo vio la rama vectorial puntúa 0,005410, de modo que los 60 documentos léxicos ganan al #1 vectorial en toda consulta. La corrección es **fusión en dos etapas con pesos por rama** (`retrieval/orchestrator.py`): las dos listas léxicas se fusionan entre sí y el resultado con la vectorial, así el voto total de una rama es exactamente su peso declarado y no depende de cuántas de sus listas dispararon.

Sobre esa base entran tres cosas más: la **ponderación adaptativa por cobertura**, que escala el peso léxico por la proporción de la consulta que casó su mejor candidato y no introduce ningún parámetro configurable; la **señal de disponibilidad separada del alcance** (`LEFT JOIN` que lee frente a `INNER JOIN` que restringe), puntuada de forma continua en el último bloque de la clave de degradación; y `retrieval/abstention.py`, una **regla de abstención relativa por consulta** en lugar de un umbral escalar.

El change se entrega **archivado** (94/94 tareas), con sus cinco delta specs sincronizadas a las specs vivas —nacen `business-signals-ranking` y `retrieval-abstention`—, con la documentación de contexto puesta al día y con `C25bis` integrado en el plan de changes. La rama incluye la propuesta de `clean-plain-fusion` (C25bis), que **no está implementada**: sólo sus artefactos, con 0/29 tareas.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change OpenSpec:** `openspec/changes/archive/2026-09-12-recalibrate-ranking-and-abstention/` (archivado, 94/94).
- **Historia:** [HU-AIENG-025](Documentos/Historias/AI-Eng/HU-AIENG-025.md) · ticket `T-AIENG-025` en el propio change.
- **Mediciones:** `Documentos/Proyecto Final AIEng/informes/c25-exploration-measurements.md` y `c25-implementation-measurements.md`; tabla en `ai-service/evals/results/c25-baselines-2026-09-11.md`.

Tres deudas que este change es el primero que puede pagar, según su `proposal.md`: la penalización de disponibilidad de C22 no se disparó ni una vez en la evaluación (el golden set corría sin punto de venta), la abstención estaba en 0,000 sobre fuera-de-dominio, y `sales_30d` llevaba persistido desde C22 con un test que prohibía leerlo.

**Tres puntos de la ficha se retiran refutados por medición**, no por argumento: la penalización de variante ambigua dentro de familia (D16), la calibración de `1-2` frente a `3+` (D17) y la rotación como criterio de orden (D10).

---

## 🔄 Cambios realizados

### `ai-service` — recuperación

- **`retrieval/orchestrator.py`**: composición en dos etapas con `fusion` como perilla (`branch` por defecto, `flat` seleccionable); lectura de `coordination` del primer hit expandido para aplicar `w_lex × cobertura`; `scope_pos_id` y `signal_pos_id` como argumentos independientes; invocación de la abstención después de la fusión, con log `stage=fuse` que nombra el modo en vigor.
- **`retrieval/abstention.py`** (nuevo): `AbstentionRule`, `candidates_in_band()`, `should_abstain()` y `log_decision()`. La regla lee la *forma* del perfil de distancias —cuántos candidatos caen en una banda alrededor del mejor— y no su nivel. Corre después de la fusión y **no altera el conjunto de candidatos**, que es lo que mantiene válidas las ventanas persistidas del barrido.
- **`retrieval/search.py`**: separa el `INNER JOIN` que restringe del `LEFT JOIN` que sólo lee; añade `sales_30d` al `SELECT` del CTE.
- **`retrieval/ports.py`**: `sales_30d` en `SearchHit` y `LexicalHit`, con `None` cuando no hay fila de proyección.
- **`retrieval/filters.py`**: clave lexicográfica de tres componentes más score continuo en la cola; `demote()` conserva el *early return* y no elimina candidatos.
- **`retrieval/lexical.py`**: denominador de cobertura con `numnode(<fragmento>) > 0`, en la misma sentencia que la coordinación.
- **`config/settings.py`**: `FUSION_DEFAULTS` reformulado a pesos por rama, `BUSINESS_DEFAULTS` con un único peso y `ABSTENTION_DEFAULTS`.

### `ai-service` — evaluación

- **`evals/sweep.py`**: barrido partido en fases `capture` y `rescore`; `FusionFingerprint` en cada ventana capturada y `check_fusion_matches()`, que **rechaza** una ventana capturada bajo otra fusión.
- **`evals/metrics.py`**: `nDCG@5 operativo` junto a la graduada y la binaria.
- **`evals/provenance.py`**: la tupla pasa de cinco a seis elementos con `fusion_mode`; `current_git_sha()` marca `+dirty` cuando el árbol de trabajo tiene cambios sin commitear.
- **`evals/report.py`**, **`runner.py`**, **`repository.py`**, **`cli.py`**, **`configs.py`**, **`golden.py`**, **`execute.py`**: columna de fusión en la tabla, subcomandos de las dos fases y validación de composición del golden set.
- **`evals/configs/`**: `v2b-fusion.yaml` y `v3-senales.yaml` nuevos y congelados; `v2-hibrido.yaml` fija explícitamente `fusion: flat` y `abstain: false` para seguir reproduciendo la línea base publicada.
- **Golden set**: `fuera-de-dominio` pasa de 5 a **20** consultas.

### `tests`

Fichero nuevo `tests/retrieval/test_abstention.py` y ampliación de `test_fusion.py`, `test_orchestrator.py`, `test_pos_scope.py`, `test_filters.py`, `test_metrics.py`, `test_sweep_phases.py`, `test_provenance_and_report.py` y `fake_product_search.py`. Se retira el guardián `test_the_retrieval_path_cannot_read_the_sales_figures` y lo sustituye el que prohíbe leer `sales_90d` y `last_sale_at`.

### `openspec`

Change archivado en `changes/archive/2026-09-12-…/`; specs vivas sincronizadas por *merge*: **nacen** `business-signals-ranking` (8 requisitos) y `retrieval-abstention` (7); `hybrid-fusion` 10 → 12, `pos-projection` 11, `retrieval-evaluation` 17 → 20 con un requisito **retirado** (el de C24 que congelaba el umbral). Se añade la propuesta `changes/clean-plain-fusion/` y se actualizan `project.md` y `config.yaml`.

### `docs` — contexto de C25

`README.md` (§1.2 y §2), `ai-service/README.md`, `ai-service/tests/README.md`, `Documentos/epicas.md`, `arquitectura.md`, el §11.2 del diseño RAG —el criterio de aceptación pasa de absoluto a relativo— y la §5.5 de las especificaciones funcionales.

### `docs` — plan de changes: C25bis y limpieza de las variantes para 3 desarrolladores

**`C25bis` (`clean-plain-fusion`) entra en el plan.** Se creó el 11 de septiembre junto con los artefactos de C25 y estaba en `openspec/changes/` y en `epicas.md`, pero no en `proyecto-final-plan-changes-openspec.md`, que es donde se decide el orden. Entra en el §2 con fila propia, en el §3 con ficha completa y en el §4 con su arista y su fila de desbloqueos, **fuera de la numeración C** por el mismo motivo que `FIX1`.

Al integrarlo aparecieron **tres incongruencias más**, todas del archivado del día anterior: la fila de C25 en la tabla maestra seguía en `rev. 2026-09-11` sin marcar archivado, la ficha del §3 conservaba el nombre anterior al renombrado (`add-business-signals-ranking`) y la cadena crítica del §4 aún arrancaba en C25. La ficha se pone al día con lo que de verdad entregó, incluida la «re-fijación del umbral» que acabó siendo lo contrario.

**Se retiran `proyecto-final-diseno-rag-joiabagur-3devs.md` y `proyecto-final-plan-changes-openspec-3devs.md`** (1.198 líneas). Ambas se declaran desactualizadas en su propia cabecera desde la v3 y describen un reparto en tres roles que dejó de existir. Sus referencias se retiran **conservando el hecho**: HU-AIENG-002 sigue documentando que el contrato de C02 se reconstruyó desde la tabla §6.8 de aquel diseño, con la anotación de que el documento se retiró y de que la fuente de verdad es `ai-service/openapi.json`. Igual en HU-AIENG-003 y en el §0 del plan.

### `ai-tooling`

`check-doc-links.ps1` nuevo y paso 6 en el `SKILL.md` de `openspec-archive-change`, replicados en los seis harnesses. Se reparan **61 enlaces relativos rotos** en 22 documentos. Los cinco `doc-impact.json` y los `documentos-funcionales.md` de `update-docs` dejan de mencionar la variante `-3devs`.

---

## 🧪 Testing

`uv run --system-certs pytest` en `ai-service/`: **994 pasan, 0 fallan**. No hay suite de backend ni de frontend afectada: el diff no toca esos componentes.

Tests destacados presentes en el diff:

- `test_flat_fusion_mode_reproduces_the_published_baseline`, `test_branch_vote_is_independent_of_how_many_of_its_lists_matched`, `test_multi_list_branch_contributes_no_more_candidates_than_a_single_list_one`, `test_vector_top_hit_reaches_the_top_five_without_lexical_consensus`.
- `test_full_coverage_leaves_the_lexical_weight_untouched`, `test_stopword_group_does_not_lower_coverage`, `test_partial_coverage_lowers_the_lexical_weight`.
- `test_signal_join_never_restricts_the_candidate_set`, `test_absent_projection_row_reports_absent_signals_not_zero`, `test_scope_join_still_restricts_when_supplied`.
- `test_rotation_does_not_order_anything`, `test_availability_is_the_only_business_weight`, `test_typed_constraint_outranks_the_business_score`.
- `test_abstention_does_not_fire_on_answerable_queries`, `test_a_dependency_failure_is_not_disguised_as_an_abstention`, `test_the_rule_does_not_alter_the_candidate_set`.
- `test_rescore_phase_reaches_no_provider_and_no_database`, `test_window_captured_under_a_different_fusion_is_refused`.
- `test_the_fusion_mode_is_recorded_in_the_provenance`, `test_a_dirty_tree_is_marked_and_never_passes_as_its_commit`.

Verificaciones de documentación, reproducibles desde la raíz:

- `pwsh .claude/skills/openspec-archive-change/scripts/check-doc-links.ps1` → **759 enlaces, 0 rotos**, salida 0.
- `openspec validate --all --strict` → **55 passed, 0 failed**.
- Recuentos del plan cuadrados: 27 archivadas + 11 pendientes = 38 vivos, con los once listados.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: el diff no contiene ninguna migración ni toca el modelo*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *no aplica: `openapi.json` no aparece en el diff*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `--all --strict`: **55 passed, 0 failed**
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *cero ficheros en `backend/`, `frontend/`, `terraform/` y `.github/workflows/`*

---

## 🚀 Deployment notes

**Variables de entorno nuevas, todas opcionales al arranque y todas con default en `config/settings.py`:**

| Variable | Default | Qué hace |
|---|---|---|
| `JPV_FUSION_MODE` | `branch` | `flat` restaura la fusión de C21 |
| `JPV_BRANCH_WEIGHT_LEXICAL` | `0.5` | Peso de la rama léxica |
| `JPV_BRANCH_WEIGHT_VECTOR` | `0.5` | Peso de la rama vectorial |
| `JPV_BUSINESS_WEIGHT_AVAILABILITY` | `1.0` | Disponibilidad; `0` es la marcha atrás |
| `JPV_ABSTENTION_ENABLED` | `true` | `false` restaura contestar siempre |
| `JPV_ABSTENTION_BAND_ALPHA` | `0.03` | Semiancho de la banda |
| `JPV_ABSTENTION_BAND_MIN_CANDIDATES` | `15` | Candidatos en banda que declaran plano el perfil |

**Sin migración** (`ai.pos_projection` ya tenía `sales_30d`, `sales_90d`, `last_sale_at` y `computed_as_of`), **sin cambio de contrato** y **sin reindexar**.

**Rollback** sin desplegar código: `JPV_FUSION_MODE=flat`, `JPV_BUSINESS_WEIGHT_AVAILABILITY=0` y `JPV_ABSTENTION_ENABLED=false` devuelven el comportamiento anterior.

---

## 📝 Notas adicionales

**Breaking change interno, no de contrato.** Cae el test guardián `test_the_retrieval_path_cannot_read_the_sales_figures`: `sales_30d` entra en la ruta de recuperación **para diagnóstico** y ninguna regla de orden lo consume. La prohibición sigue siendo estructural para `sales_90d` y `last_sale_at`.

**Tres listones no se alcanzan y se declaran en vez de cerrarse**, según `ai-service/README.md`: `Recall@5` 0,758 contra 0,85; abstención 0,150 contra 0,80 (llegar a 0,80 costaría silenciar 21 de las 43 contestables); y `v3-senales` no bate a `v2b-fusion` por el margen de 0,05 (+0,030 operativo) aunque cumple su propia regla de adopción.

**Puntos de atención para quien revise:**

1. **La columna de abstención del informe une dos señales.** Una abstención y un `low_confidence` terminan en la misma bandera de `RetrievalResponse`, así que el 0,150 es su unión y no la tasa de la regla sola —ésta caza 2 de 20 y `low_confidence` 1 de 20—. Separarlas exigiría un campo nuevo en un esquema congelado por contrato, así que se declara en el informe y en la etiqueta de la columna en vez de atribuirse mal.
2. **La tabla publicada se midió con el árbol sucio.** Su procedencia dice `29a7bc5249aa+dirty`: las cifras salen del código que aterrizó en el commit siguiente. Queda anotado en el propio informe, y `current_git_sha()` marca ahora los árboles sucios para que no se repita.
3. **`clean-plain-fusion` (C25bis) es sólo propuesta**, 0/29 tareas. Retira la fusión plana cuando la decisión esté congelada y publicada; este archivado es lo que lo desbloquea.
4. **Los 61 enlaces reparados** son en su mayoría anteriores a este change: tickets rotos al archivar C06b–C24 y FIX1, y seis HU con profundidad relativa equivocada que nunca funcionaron. El script sólo reescribe destinos que existen en disco; lo ambiguo lo reporta sin tocar.
5. **Quedan siete menciones textuales a los documentos `-3devs`**, todas en tres changes **archivados** (`2026-08-06-add-ai-service-contracts-and-auth` y `2026-08-09-add-dotnet-ai-gateway-client`). No se tocan a propósito: son registro fechado, y ninguna es un enlace sino una cita en texto, así que no dejan ningún enlace roto.



---

<a id="pr-32"></a>
## #32 — Retira la fusión plana y los pesos por lista: 315 filas idénticas (C25bis)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c25bis-clean-plain-fusion` → `ai-eng` |
| Creada | 2026-09-12 |
| Integrada | 2026-09-12 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/32 |

### Descripción

## 📋 Descripción

Retira la fusión de una sola etapa sobre todas las listas, los tres pesos por lista que la
gobernaban y el selector `JPV_FUSION_MODE`. C25 los había conservado para poder re-medir la fila
de referencia de su tabla de ablations; publicada esa tabla y congelada la configuración, lo que
quedaba era un camino que nadie ejecuta, que cualquiera puede encender por error y cuya aritmética
el propio proyecto midió como defectuosa.

**Ninguna conducta observable cambia, y está demostrado en vez de argumentado.** El listón se subió
antes de tocar código de *«cifras idénticas»* a *«líneas idénticas»*, porque seis agregados iguales
pueden esconder reordenaciones que se compensan. Dos corridas completas del arnés —una antes del
borrado y otra después, sobre el mismo golden set `1:198c4af44506` y la misma huella de índice
`051a6b06021efc3f…`— dan **las 315 filas por consulta idénticas**, listas de resultados incluidas.
El único elemento de la procedencia que difiere es la revisión del código, que es precisamente la
hipótesis bajo prueba. Suite **994 → 997 con cero fallos a los dos lados**.

El inventario de lo que se retira se comprobó sobre el árbol antes de borrar nada, y **refutó tres
afirmaciones de la ficha del change**: los pesos por lista sí tenían lector vivo, la variante
adaptativa perdedora no existía, y el fallo al arranque no era alcanzable por el mecanismo que se
suponía. Esas tres refutaciones cambian qué se retira y por qué, y están en el cuerpo de la PR.

### Tipo de cambio

- [ ] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [x] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [x] 💥 breaking change — **interno**: la configuración de evaluación `v2-hibrido` deja de poder ejecutarse. Sin ruptura externa: ni REST, ni OpenAPI, ni esquema

---

## 🎯 Motivación y contexto

**Change de OpenSpec:** [`clean-plain-fusion`](openspec/changes/archive/2026-09-12-clean-plain-fusion/) (C25bis), archivado el 2026-09-12 con 46/46 tareas.
**HU:** [`HU-AIENG-025bis`](Documentos/Historias/AI-Eng/HU-AIENG-025bis.md) · **Ticket:** `T-AIENG-025bis`.
**Informes:** [decisiones de exploración](Documentos/Proyecto%20Final%20AIEng/informes/c25bis-exploration-decisions.md) · [mediciones de implementación](Documentos/Proyecto%20Final%20AIEng/informes/c25bis-implementation-measurements.md).

El defecto que la composición retirada encarnaba está medido y publicado: con los pesos de C21, un
documento léxico en el peor puesto puntúa `1,00/120 = 0,008333` y el mejor candidato que sólo vio
la rama vectorial puntúa `0,33/61 = 0,005410`, así que los sesenta documentos léxicos ganaban al #1
vectorial **en toda consulta**, y el documento de grado 2 que la rama vectorial pone primero caía a
la **posición 33** en tres consultas del golden set. No era un peso mal calibrado: era una partición
dura disfrazada de fusión.

**Las tres refutaciones de la ficha**, comprobadas por búsqueda sobre el árbol:

| Lo que decía la ficha | Lo que dice el árbol |
|---|---|
| «los pesos por lista que sólo ella consumía» | **Falso.** `weight_typed` y `weight_expanded` eran también los `internal_weights` de la etapa 1 **viva**. Se retiran igualmente, pero por ser **trampas** —la spec exige que sean iguales y prohíbe barrerlas, así que sólo podían moverse hacia la violación sin que nada lo detectase— y no por estar muertas. Sólo `weight_vector` carecía de lector |
| «retirar la variante adaptativa que perdió el barrido» | **Pata vacía.** La forma binaria se implementó y se retiró **dentro de C25**, y hay un test que falla si vuelve |
| «que el arranque falle al nombrar una perilla retirada» | **Inalcanzable y contraproducente.** Con `extra="ignore"`, pasar a `forbid` no caza variables de entorno; un validador que barra el entorno convertiría un residuo inofensivo en un fallo de arranque. La obligación se acota a la configuración de evaluación, donde el daño es de **medición** —una fila que mide otra cosa— y allí la guarda **ya existía** |

**El principio que el change deja escrito:** *una perilla es algo que se puede poner; un registro es
algo que se escribe.* De ahí salen las tres decisiones que más forma dan al diff.

---

## 🔄 Cambios realizados

### `ai-service` — el borrado

- [`retrieval/orchestrator.py`](ai-service/src/jbg_ai/retrieval/orchestrator.py): desaparece la rama `FUSION_MODE_FLAT` de `_fuse_branches` con su `flat_weights`; desaparecen los parámetros `fusion`, `weight_typed`, `weight_expanded` y `weight_vector` de `retrieve_products` y la comprobación de modo desconocido; `_fuse_two_stage` pierde `internal_weights` y compone la etapa 1 con la constante nueva **`LEXICAL_INTERNAL_WEIGHT`**. La traza `stage=fuse` deja de emitir `mode=`: un campo que sólo puede imprimir un valor es ruido.
- [`config/settings.py`](ai-service/src/jbg_ai/config/settings.py): `FUSION_DEFAULTS` pasa de 7 a 4 claves; caen los cuatro campos `jpv_fusion_mode`, `jpv_rrf_weight_typed`, `_expanded` y `_vector`, el validador `known_fusion_mode` y las constantes `FUSION_MODE_BRANCH/FLAT/MODES`. **`extra="ignore"` no se toca.** `canonical_openapi_settings()` se corrige solo: usa `**FUSION_DEFAULTS`.
- [`evals/configs.py`](ai-service/src/jbg_ai/evals/configs.py): `EvalConfig` pierde `fusion` y los tres `weight_*`; `v2-hibrido` sale de `ABLATION_ORDER` y de `POOLED`. La guarda de claves desconocidas que ya existía pasa a ser el mecanismo del escenario de fallo ruidoso.
- [`evals/sweep.py`](ai-service/src/jbg_ai/evals/sweep.py): `FusionFingerprint` pierde `mode` y los tres `weight_*`. `evals/execute.py`, `runner.py` y `cli.py` pierden las lecturas correspondientes; `_fusion_mode_of` deja de recibir `settings`.
- [`evals/provenance.py`](ai-service/src/jbg_ai/evals/provenance.py): **`fusion_mode` se conserva** y nace `BRANCH_FUSION` junto a `NO_FUSION`. El selector muere; el registro vive, porque una corrida archivada bajo la composición retirada debe seguir declarándose no comparable con una actual.
- `evals/configs/v2-hibrido.yaml` → **`evals/configs/retired/v2-hibrido.yaml`**, con cabecera que lo declara histórico. La inercia es estructural: el cargador hace `glob("*.yaml")` **sin recursión**.
- Tres configuraciones congeladas pierden una clave inerte cada una (`v1-vectorial` los tres pesos por lista, `v2b-fusion` y `v3-senales` el `fusion: branch`), con el motivo escrito en cada fichero. Ver *Notas adicionales*.

### `openspec` — specs vivas y archivado

`hybrid-fusion` **12 → 11** requisitos, `retrieval-evaluation` **20 → 20** con dos reescritos. Ni `ADDED` ni `RENAMED`: no nace ninguna capacidad.

| Operación | Requisito | Escenarios |
|---|---|---|
| `REMOVED` | `The flat fusion remains selectable so the published baseline stays reproducible` | −3 |
| `MODIFIED` | `Weights and smoothing are configuration, and the weakest branch weighs less` | 7 → 9 |
| `MODIFIED` | `The lexical branch weighs less when its best candidate matched less of the query` | 6 → 6, una cláusula |
| `MODIFIED` | `Fusion tests run offline and pin the measured defaults` | 2 → 3 |
| `MODIFIED` | `An ablation table isolates each change it reports` | 2 → 5 |
| `MODIFIED` | `A run is comparable to another only when its provenance matches` | 2 → 4 |

El único escenario vivo que desaparece sin sustituto es `The baseline row is still reproducible`, y
desaparece a propósito: lo reemplaza la conservación declarada. También se corrigen los dos
`## Purpose`, que afirmaban que la fusión plana seguía seleccionable — un requisito correcto con un
resumen que lo contradice es medio-sync.

`openspec/project.md` y `openspec/config.yaml` dejan de enumerar las perillas retiradas.

### `tests` — 9 ficheros

**Cuatro retirados** (`test_flat_fusion_mode_reproduces_the_published_baseline`,
`test_vector_branch_weight_defaults_below_lexical`,
`test_the_two_lexical_weights_sum_to_one_lexical_list`,
`test_baseline_row_is_still_selectable_and_reproducible`) y **siete añadidos**. Uno más se renombra
(`test_low_confidence_means_the_same_under_both_fusion_modes` →
`…_means_branch_disagreement_and_not_list_disagreement`). Neto **+3**, que es exactamente 994 → 997.

El que más importa es **`test_the_flat_arithmetic_that_was_retired_buried_the_vector_leader`**: el
fósil. Demuestra el defecto sobre `fuse()` a solas —sin orquestador, sin ajustes, sin modo— con los
pesos de C21 como **literales locales del test**. Un número en un módulo de settings es una
configuración que alguien puede poner; el mismo número en un test es un registro de lo que se midió.

### `docs`

README del servicio y de la suite, cabecera de histórico sobre el informe publicado de C25, §0 y
ficha del plan, `epicas.md`, `arquitectura.md`, los dos informes nuevos y las dos corridas de
verificación versionadas.

---

## 🧪 Testing

- **`uv run pytest`: 997 passed, 0 failed.** Línea base tomada antes de tocar nada: **994 passed, 0 failed**, con la lista de nombres en rojo **vacía** — lo que hace la comparación más estricta de lo que el `CLAUDE.md` prevé para este repositorio.
- **Diff línea a línea del JSONL por consulta**, emparejando por `(config_id, query_id)` sobre `ranked` completo y todas las métricas: **315 filas idénticas** sobre las cinco configuraciones supervivientes. Ambas corridas quedan versionadas en [`evals/results/c25bis/`](ai-service/evals/results/c25bis/) para que la comprobación sea reproducible por terceros.
- Las cifras publicadas coinciden a tres decimales en las cinco filas.
- Cero llamadas a proveedor: los vectores de consulta están congelados.
- [ ] Cobertura ≥70% — no verificable desde el diff.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *siete tests nuevos; el porcentaje no se verifica desde el diff*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: sin diff en `backend/`*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *no aplica: sin diff en `openapi.json`*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — *`--all --strict`: 54 passed, 0 failed*
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *sin diff en `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`*

---

## 🚀 Deployment notes

**Sin impacto de despliegue.** Sin migración, sin cambio de contrato, sin reindexado.

Cuatro variables de entorno **dejan de existir**: `JPV_FUSION_MODE`, `JPV_RRF_WEIGHT_TYPED`,
`JPV_RRF_WEIGHT_EXPANDED` y `JPV_RRF_WEIGHT_VECTOR`. Se comprobó que **ninguna configuración de
despliegue las trae** —ni `backend/.env`, ni los `.env.example`, ni `terraform/`, ni los
`docker-compose`; `ai-service/` no tiene `.env.example` ni compose propio—, así que no hay nada que
retirar de ningún entorno.

**Un entorno que todavía las exporte no tiene efecto y el arranque no falla**, y la asimetría es
deliberada: una perilla retirada e ignorada produce el comportamiento **bueno**, así que lo que
queda es una creencia equivocada y no un resultado equivocado; rechazarla convertiría un residuo
inofensivo en una caída. Donde una perilla rancia **sí** cambiaría un resultado es en una
configuración de evaluación, y allí se rechaza nombrándola.

**Rollback:** revertir el commit. Nada en los datos ni en el esquema cambia.

---

## 📝 Notas adicionales

**Breaking change interno, declarado y no disimulado.** La configuración de evaluación `v2-hibrido`
deja de poder ejecutarse. Se conserva **citable** con tres artefactos versionados: sus cifras y
procedencia en el informe publicado, su detalle por consulta en el JSONL, y la configuración exacta
bajo la que se midió en `evals/configs/retired/`. El arnés **no** reformula el pipeline retirado
para mantener la fila viva, porque un arnés que reformula un pipeline mide la reformulación.

**Una desviación de un *non-goal* propio, declarada como D-I** en el `design.md`, siguiendo el
precedente de C22 con su revisión de Alembic. El change decía no tocar `v2b-fusion` ni
`v3-senales`, y se editaron: la guarda de claves desconocidas las habría dejado sin cargar. Las tres
claves retiradas eran **inertes** —`v1-vectorial` corre con `mode: vector`, o sea con la rama léxica
apagada, y `branch` era el valor vivo por defecto—, lo que el diff de las 315 filas confirma después
del hecho.

**Pérdida de cobertura que conviene mirar.** Dos tests perdieron su segundo brazo —servir el mismo
corpus bajo la composición retirada para atestiguar el contraste—. Verificado que **ningún escenario
de spec se queda sin cobertura**: el brazo superviviente afirma la propiedad y el contraste vive en
el fósil. Sostengo que salen reforzados, porque lo que era una comparación entre dos composiciones
pasa a estar garantizado por la forma del código, pero es la pérdida más real del change.

**Por qué el borrado era bit-idéntico por construcción y no por suerte.** En la etapa 1 ambas listas
llevan el mismo peso, RRF escala linealmente con el peso, y de esa etapa sólo se reenvía el **orden**
a la etapa 2 — la magnitud se descarta. Con pesos iguales, cualquier valor produce el mismo
resultado.

**Queda declarado y sin cerrar:**
- El brazo de control de la regla de cobertura **no tiene fila propia** en la tabla y sólo es alcanzable a mano: ninguna configuración superviviente fija `coverage_rule: none`. La próxima profundización del golden set lo necesitará.
- `coverage_rule` **no es una marcha atrás de despliegue** — no es campo de `Settings` y el router no lo pasa. La spec decía lo contrario y se corrigió en una cláusula.
- Las **tres brechas que C25 dejó abiertas** siguen abiertas: `Recall@5` 0,758 contra 0,85, abstención 0,150 contra 0,80, y `v3` sin batir a `v2b` por el margen. Este change no las toca.



---

<a id="pr-33"></a>
## #33 — feat(ai-service): implementar sustitutos sobre el embedding almacenado

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c26-add-substitutes-retrieval` → `ai-eng` |
| Creada | 2026-09-12 |
| Integrada | 2026-09-12 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/33 |

### Descripción

## 📋 Descripción

Implementa **C26 (`add-substitutes-retrieval`)**: el motor de sustitutos por falta de stock detrás de `POST /v1/retrieval/substitutes`, que hasta ahora respondía **501**. La ruta y sus modelos (`SubstitutesRequest`, `SubstituteResult`, `SimilaritySignals`, `SubstitutesResponse`) están en el contrato congelado desde C02, y `ai-service/openapi.json` **no aparece en este diff**: el contrato no se mueve.

El cambio de coste que gobierna el diseño es que sustituto es **producto → producto**. El ancla es un `product_id` cuyo embedding ya está almacenado en `ai.product_document`, así que la capacidad se entrega **sin una sola llamada al proveedor de embeddings**, sin rama léxica, sin expansión de consulta y sin fusión: una sentencia SQL y una clave de orden. Vive en un módulo nuevo, `ai-service/src/jbg_ai/retrieval/substitutes.py`, y no en `orchestrator.py`, cuyo flujo no comparte ninguna de esas etapas.

La PR arrastra además dos cosas del mismo tramo de rama: el **corte de C27** (`add-complementary-recommendations`), que sale del alcance con cinco mediciones en `informes/c27-cut-measurements.md`, y el **archivado de C26** con la sincronización de sus delta specs a `openspec/specs/`.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

El sistema sabía buscar y **no sabía qué ofrecer cuando la respuesta correcta no está disponible**, que es el momento en el que el mostrador pierde la venta. Era además el **último 501 cerrable** del servicio: `/v1/inventory/propose` también responde 501, pero su rama se anuló el 2026-08-31 y eso ya está declarado como limitación.

No se podía implementar sin mover una spec viva: `vector-retrieval` **obligaba por escrito** a que la ruta siguiera devolviendo 501, con su escenario *«Substitutes stay unimplemented»*.

- Change: `openspec/changes/archive/2026-09-12-add-substitutes-retrieval/` (proposal, design, tasks 62/62, ticket)
- Historia: `Documentos/Historias/AI-Eng/HU-AIENG-026.md`
- Mediciones: `informes/c26-exploration-measurements.md` y `informes/c26-implementation-measurements.md`

**La exploración refutó tres puntos de la ficha del plan**, y eso cambió el diseño:

1. **«Misma familia primero» está invertida.** La familia es, por construcción, el conjunto de piezas que se diferencian *justo en el atributo que descalifica* — la talla. Para `SKU13 Anillo erizo de mar M` el top-5 del vector puro no contiene un solo sustituto usable: los tres primeros son el mismo anillo en L, S y XL.
2. **Pero la familia no se puede excluir**: el mejor sustituto de `SKU159` es su hermano de *misma talla y otro material*, y es el #1. La pertenencia a familia es **ortogonal**; el discriminante es la talla.
3. **La exclusión por falta de stock no pertenece aquí.** Estaba especificada dos veces, y la versión correcta es la de .NET (C34), que es la autoridad sobre el stock.

---

## 🔄 Cambios realizados

### `ai-service` — el motor (16 archivos, +1469/−30)

- **`retrieval/substitutes.py`** *(nuevo, 409 líneas)*. `retrieve_substitutes()` resuelve alcance con `projection.resolve_scope`, lee el documento origen, pide vecinos y compone el orden. La clave es `_Scored.order_score` → `sim − w_size·[talla distinta] − w_availability·[agotado]`, con **todos los términos continuos**; `_ordering_key()` añade `material_overlap` como desempate estricto y `product_id` al final para que dos corridas idénticas no difieran.
  - `_size_differs()` devuelve `True` **solo cuando ambos lados declaran talla**: ausencia no es desajuste, y el 54 % de los anillos no tiene `size_label`.
  - `_jaccard()` calcula `material_overlap` y `style_similarity` sobre los conjuntos de etiquetas, nunca desde el embedding.
  - `_match_reasons()` transporta lo que `SimilaritySignals` no puede expresar — señaladamente la talla — y declara explícitamente cuando **no había etiquetas de estilo que comparar**. No emite ninguna cifra de precio ni de stock.
  - `VISUAL_SIMILARITY_UNAVAILABLE = None` y `SUBSTITUTES_NEVER_ABSTAIN = False`, ambos con el comentario que los justifica.
  - **No reutiliza `demotion_rank`**: su bloque entero de talla particiona en lugar de desempatar. Sí reutiliza `filters.business_score` y `OUT_OF_STOCK_BUCKET`, para que la semántica de «agotado» siga viviendo en un solo sitio.
- **`retrieval/ports.py`**: dataclasses `SourceDocument` y `NeighbourHit`, más dos métodos en `ProductSearchPort` — `source_document()` (la ausencia vuelve como `None`, no como excepción) y `neighbours_of()`. El docstring de este último documenta que **no existe** parámetro `pos_id` que restrinja: el punto de venta entra solo como `signal_pos_id`.
- **`retrieval/search.py`**: `SOURCE_DOCUMENT_SQL` y `compile_neighbours_sql()`. El k-NN corre contra el embedding de la fila origen mediante una subconsulta escalar no correlacionada (`_SOURCE_EMBEDDING`), reutiliza `_SCOPE_CTE` y **`_SIGNAL_JOIN`** (`LEFT JOIN`) y nunca `_SCOPE_JOIN`. `piece_type` usa `IS NOT DISTINCT FROM` porque un documento vivo no declara tipo. Conserva el desempate `ORDER BY … , d.product_id ASC` que introdujo C24.
- **`retrieval/errors.py`**: `UnusableSourceProductError(product_id, cause)` — tres causas, tres frases.
- **`api/routers/retrieval.py`**: `retrieve_substitutes` pasa a `async`, pierde `require_stub_mode` y conserva el stub de C02 bajo `STUB_MODE`. Traduce el error a **422** nombrando la causa, y a 503 si falta base de datos. Se retiró la constante `SUBSTITUTES_DELIVERED_BY`. La explicación va en **comentario y no en docstring**, porque FastAPI publicaría un docstring como `description` de la operación y el snapshot se movería.
- **`config/settings.py`**: `SUBSTITUTE_DEFAULTS` y el campo `jpv_substitute_weight_size` (default `0.05`, `ge=0`), con validador `blank_substitute_setting_is_default` para que un export vacío no se lea como cero.
- **`retrieval/filters.py`** y **`retrieval/fusion.py`**: solo docstrings. `fusion.py` retira su predicción *«C26 (substitutes) is the next caller»*, que resultó falsa — con una sola lista no hay nada que fusionar. `filters.py` acota a la clave de C25 la afirmación de que la magnitud del peso de disponibilidad es irrelevante.
- **Evaluación**: `evals/substitutes_slice.py` *(nuevo)* y el subcomando `substitutes` en `evals/cli.py`, que publica el recorrido del barrido y **nombra el peso adoptado** aplicando la regla por programa. `evals/golden.py` añade `GoldenQuery.source_product_id`, la constante `SUBSTITUTE` y la propiedad **`GoldenSet.retrieval_queries`**, y valida que toda consulta `sustituto` declare un UUID de origen. `runner.py`, `sweep.py` y `cag_run.py` migran de `judged_queries` a `retrieval_queries`.
- **Golden set**: `queries.jsonl` ancla `q49`–`q52` con `source_product_id` y retira su marca de no juzgadas; añade `q72`, la quinta consulta, anclada en `SKU102` — **real, huérfano y sin talla**. `judgements.jsonl` crece en 126 líneas, todas añadidas.

### `tests` — 6 archivos, +1135/−6

- **`tests/retrieval/test_substitutes.py`** *(nuevo, 23 tests)*. El fixture `SKU13_NEIGHBOURS` son las **distancias de coseno reales** del índice vivo, no números redondos.
- **`tests/api/test_substitutes_route.py`** *(nuevo, 8 tests)* y **`tests/evals/test_substitutes_slice.py`** *(nuevo, 8 tests)*.
- `tests/api/test_stub_mode.py` y `tests/evals/test_sweep_phases.py` se reapuntan; `tests/support/fake_product_search.py` gana el doble de los dos métodos nuevos del puerto.
- *(El chunk `05-tests.diff` viene **resumido** por tamaño: el recuento de tests por archivo sale de las cabeceras de hunk y de los nombres de función, no del diff completo.)*

### `openspec` — 11 archivos, +1093/−6

- Nace **`openspec/specs/substitutes-retrieval/spec.md`** con **10 requisitos**.
- **`openspec/specs/vector-retrieval/spec.md`** (4+/4−): el requisito *«Real product retrieval replaces the stub…»* pierde la obligación del 501 y su escenario *«Substitutes stay unimplemented»* pasa a *«No retrieval route is left answering 501»*. Los otros ocho requisitos quedan idénticos.
- `openspec/project.md` gana la entrada de C26 y corrige la cifra del golden set (`48 de 56` → `68 de 72`, contado sobre `queries.jsonl`). `openspec/config.yaml` añade `JPV_SUBSTITUTE_WEIGHT_SIZE` a su enumeración de knobs.
- El change queda en `openspec/changes/archive/2026-09-12-add-substitutes-retrieval/`.

### `docs` — 12 archivos, +1492/−42

- `informes/c26-exploration-measurements.md`, `c26-implementation-measurements.md` y **`c27-cut-measurements.md`** *(nuevos)*, más `evals/results/c26-substitutes-slice.md` con el barrido de once pesos.
- `ai-service/README.md` documenta la capacidad, el ajuste nuevo, que **no se llama al proveedor** y **dos limitaciones medidas**. `ai-service/tests/README.md` ubica los escenarios nuevos.
- `Documentos/arquitectura.md`: las rutas reales incluyen C26 y «el resto sigue en 501» pasa a nombrar las **dos** que quedan; el árbol sube a `C01–C26`.
- `README.md` §2.3 y §1.2, `Documentos/epicas.md` y el plan de changes: C26 archivado, recuento **29 archivadas / 8 pendientes**, y la cadena crítica arrancando en **C34**.
- `joiabagur-ia-especificaciones-funcionales-v2.md` §6.3.2: nota con los cuatro criterios que la medición refutó, **sin reescribir** la tabla de pesos recomendados.

---

## 🧪 Testing

`uv run --system-certs pytest` en `ai-service/`: **1038 passed, 0 failed** (2:18). La línea base previa al change en el mismo árbol fue 997 passed / 0 failed, así que la comparación por **nombres** que exige `CLAUDE.md` es vacía en los dos sentidos.

`openspec validate --all --strict`: **55 passed, 0 failed**.

Escenarios que el diff añade, con los dos que impiden los atajos del diseño:

- `test_different_size_sibling_stays_inside_the_visible_window` — **el test que prohíbe el bloque entero**: no basta con que la talla correcta suba; el hermano degradado tiene que seguir dentro de la ventana visible.
- `test_size_weight_of_zero_reproduces_the_ordering_without_the_term` — el rollback restaura el orden del coseno puro exactamente.
- `test_never_returns_a_different_piece_type`, con un colgante colocado **más cerca** que todos los anillos.
- `test_out_of_stock_candidate_is_demoted_and_never_removed` y `test_absent_projection_row_is_not_read_as_zero_stock`.
- `test_no_embedding_provider_call_is_made`, con un doble que levanta al ser invocado.
- `test_style_similarity_is_not_derived_from_the_embedding` y `test_match_reasons_carry_no_price_or_stock_figure`.
- `test_unknown_or_unindexed_source_product_is_an_explicit_error` y `test_stub_mode_still_serves_the_c02_substitutes_fixture`.
- `test_the_published_ablation_denominator_is_the_one_c25_measured`, que fija en 63 el denominador de la tabla publicada.
- `test_the_token_scope_wins_over_the_body`.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: el diff no contiene migraciones de EF Core ni de Alembic*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *no aplica: el contrato no se mueve y el fichero no está en el diff*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *el diff no toca `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`*
- [ ] QA manual sobre el índice real
- [ ] Revisión de seguridad

---

## 🚀 Deployment notes

**Una variable nueva, opcional:** `JPV_SUBSTITUTE_WEIGHT_SIZE`, default `0.05`, declarada en `ai-service/src/jbg_ai/config/settings.py` con `ge=0`. **No hace falta darla de alta** ni en el Compose local ni en SSM: el servicio arranca sin ella y un export vacío se lee como «sin definir» y cae al default, no a cero. **`0` es el rollback de la capacidad** y reproduce exactamente el orden que producen los términos restantes por sí solos.

El resto, sin impacto:

- **Sin dependencias nuevas**: `pyproject.toml` y `uv.lock` no están en el diff.
- **Sin migraciones** de Alembic ni de EF Core, y sin cambios en el esquema `ai`.
- **Sin infraestructura**: ni `Dockerfile`, ni `docker-compose.yml`, ni `terraform/`, ni `.github/workflows/`.
- **Sin orden de despliegue que coordinar**: `jbg-ai` es un contenedor aparte y es el único que cambia.

**Verificación post-deploy:** con `STUB_MODE=false` y `DATABASE_URL` configurada, `POST /v1/retrieval/substitutes` con un `product_id` indexado debe responder **200** y no 501. Con un `product_id` inexistente, **422** nombrando la causa. Sin `DATABASE_URL`, 503 — y en ningún caso se exige una credencial de proveedor, porque esa ruta no embebe nada.

**Rollback:** exportar `JPV_SUBSTITUTE_WEIGHT_SIZE=0` desactiva el término de talla sin desplegar nada. Revertir la capacidad entera requiere revertir el commit, y haría que la ruta volviera a 501 — lo que contradiría la spec viva `substitutes-retrieval` que esta PR sincroniza.

---

## 📝 Notas adicionales

**Breaking changes: ninguno.** El único cambio observable desde fuera es que una ruta que devolvía 501 pasa a devolver 200. Los esquemas Pydantic no cambian, `ai-service/openapi.json` no está en el diff y `test_openapi_snapshot_is_stable` está en verde. La variable nueva tiene default, así que no rompe ningún arranque. Hoy ningún consumidor .NET llama a esa ruta: la consume **C34**.

**Riesgo: medio.** Dos focos concretos para quien revise:

1. **El alcance del arnés de evaluación cambió, y afecta a una tabla publicada.** Las cinco consultas de sustituto pasan a `judged: true`, así que `judged_queries` crece. Para que el **denominador** de la tabla de ablations de C24/C25 no se moviera, se introdujo `GoldenSet.retrieval_queries` —que excluye la categoría `sustituto`— y se migraron *todos* los puntos de llamada de `runner.py`, `sweep.py` y `cag_run.py`. Si uno se hubiera quedado atrás, las cifras publicadas cambiarían sin que ninguna configuración hubiera cambiado. `test_the_published_ablation_denominator_is_the_one_c25_measured` lo fija en 63.
2. **Aislamiento por punto de venta, conservado.** `payload.pos_id` se ignora a propósito y el alcance sale del claim del token, igual que en la ruta de productos. El punto de venta entra **solo** como `signal_pos_id`, nunca como parámetro que restrinja, y `neighbours_of()` no tiene uno.

**Tres limitaciones medidas, declaradas y no cerradas:**

- **`style_similarity` es cero por construcción** sobre catálogo real: solo **1 de 404** productos tiene algún candidato del mismo tipo con el que compartir etiqueta de estilo. El contrato la exige requerida y no nulable, así que se emite el cero y la ausencia se declara en `match_reasons` para que nunca pueda leerse como «estilos distintos».
- **El término de disponibilidad particiona en la práctica.** Reutiliza `w_availability = 1.0` de C25 tal como la spec exige, y la similitud vive en `[0, 1]`, así que ese peso cubre el rango entero: los agotados quedan detrás de los disponibles, siempre. No elimina nada, que es el invariante, y la spec lo **acepta por escrito** en vez de dejarlo como hallazgo para quien mida después. El golden set está etiquetado sin alcance de punto de venta, así que ninguna rebanada puede recalibrar ese peso. Anotado en la ficha de **C34**.
- **El recall de familia es la ausencia de una regla que excluya, no una cota sobre la ventana.** Ningún filtro puede sacar a un hermano —`piece_type` lo comparten por construcción—, pero puede quedar fuera de la ventana de sobre-recuperación: con `top_k=1` la ventana son tres filas y una familia de ocho no cabe. La spec lo dice así en lugar de prometer lo que la sentencia no garantiza.

**Sobre la evaluación:** el peso de talla se barrió en **once puntos** sobre las cinco consultas ancladas, y el recorrido completo se publica, no solo el ganador. El máximo de nDCG@5 graduado está en `0,075`, pero ahí entra un documento de grado 0 en un top-5; gana el guardarraíl, y entre `0,05` y `0,06` la diferencia es de **0,0051**, por debajo del umbral que este conjunto resuelve, así que el default se queda en `0,05` y el informe lo dice. La medición aísla la calidad del sustituto **dado el producto origen correcto**: la cadena «texto del operador → producto → sustitutos» es de C32.

**C27 sale del alcance en esta misma rama**, y por medición y no por plazo: las cinco comprobaciones de `informes/c27-cut-measurements.md` salen en contra, empezando por que la co-ocurrencia se deriva del `BulkOperationId` y el simulador de C10 agrupa las cestas **maximizando la diferencia** entre líneas — es decir, el generador no tiene modelo de afinidad, tiene lo contrario. La condición de reactivación queda escrita para ser comprobable: percentil 95 de `co_sales_count` ≥ 3; hoy es **1**.



---

<a id="pr-34"></a>
## #34 — feat(profile-review): revisión humana de perfiles y sus métricas

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c28-add-profile-review-ui-and-metrics` → `ai-eng` |
| Creada | 2026-09-13 |
| Integrada | 2026-09-13 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/34 |

### Descripción

## 📋 Descripción

Implementa **C28 (`add-profile-review-ui-and-metrics`)**: la revisión humana de los perfiles de IA del catálogo y las dos cifras que el §16 del diseño pedía como casilla de entrega. Antes de esta rama los 1.200 perfiles estaban en `ReviewOrigin = AutoBulk` con **cero revisores y cero tiempos**, así que ninguna de las dos cifras existía.

El trabajo entra por `Application/` → `API/` → `frontend/`, **sin migración de EF Core** —C08 había reservado `ProposedProfileJson` y `ReviewDurationMs`— y **sin tocar `ai-service/` ni `openapi.json`**. Se añaden seis rutas a `AiCatalogController`, un servicio `IProfileReviewService` con su estratificación y muestreo, una pantalla de administrador nueva, y tres piezas compartidas extraídas de `family-review.tsx`, que además recibe los atajos de teclado y la creación de familia que C18b dejó pendientes.

El change se archivó en `openspec/changes/archive/2026-09-13-add-profile-review-ui-and-metrics/` tras ejecutar la sesión de revisión: **204 perfiles en 109 minutos, los 204 cronometrados**.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [x] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-09-13-add-profile-review-ui-and-metrics/` (proposal, design, specs delta, tasks, ticket).
- **HU**: `Documentos/Historias/AI-Eng/HU-AIENG-028.md`.
- **Mediciones**: `Documentos/Proyecto Final AIEng/informes/c28-exploration-measurements.md` (previas) y `c28-implementation-measurements.md` (resultados).

La exploración refutó la premisa operativa de la propia ficha del plan: **el enrutado híbrido no acota la cola**. `size_label` es el único campo que el extractor marca alguna vez `rule` (539 de 1.200); `piece_type`, `materials` y `stone_type` salen siempre `inferred`, así que el 100 % de los productos entra en la cola. De ahí que el criterio de muestreo se invente aquí y sea **estratificado por evidencia**, no ordenado por confianza: la heurística de span solo caza falsos positivos y es ciega por construcción a las omisiones.

---

## 🔄 Cambios realizados

### `backend-application`

- **`Services/ProfileEvidenceStratum.cs`** — clase pura que asigna el estrato desde el mínimo de las confianzas de los tres campos sensibles, con `stone_type` ausente tratado como no penalizador. **Una sola implementación**, consumida por la cola y por las métricas.
- **`Services/ProfileReviewSampling.cs`** — orden determinista por `OrderKey()` = `SHA-256(ProductId + semilla)`, con cuotas por estrato y `StratumDraw.Exhausted` cuando un estrato es menor que su cuota. No usa `Random` ni `GetHashCode()`, que no son estables entre procesos.
- **`Services/ProfileCorrection.cs`** — clasifica cada campo como `confirmation`/`addition`/`removal`/`substitution` comparando los valores en vigor contra `ProposedProfileJson`, por **diferencia de conjuntos** en los campos de lista. No escribe.
- **`Services/ProfileReviewService.cs`** — cola sobre `ReviewOrigin = AutoBulk` **y** `ReviewStatus = Approved`, revisión individual, aprobación masiva y métricas. `ApplyValues()` no toca `ProposedProfileJson`, `FieldConfidenceJson`, `FieldSourceJson` ni `SourceHash`.
- **`Interfaces/IProfileReviewService.cs`**, **`Validators/ProfileReviewValidators.cs`** — duración obligatoria en la revisión individual; la masiva exige exactamente un campo y un estrato declarado.
- **`Configuration/ProfileReviewOptions.cs`** — `SamplingSeed` y `QuotaPerStratum`, validados en `Extensions/ServiceCollectionExtensions.cs:AddProfileReview()` con `ValidateOnStart()`.

### `backend-api`

- **`Controllers/AiCatalogController.cs`** — seis rutas nuevas bajo `api/ai/catalog`, heredando `[Authorize(Roles = "Administrator")]` de la clase: `GET profile-review-queue`, `POST profile-reviews`, `POST profile-reviews/bulk`, `GET profile-reviews/rejected`, `POST profile-reviews/restore`, `GET profile-review-metrics`. El revisor se toma de `ICurrentUserService`, nunca del cuerpo.
- **`DTOs/Ai/ProfileReviewDtos.cs`** — DTOs de cola, revisión, masiva, rechazados y métricas. `BulkApproveProfilesRequest.Fields` es lista para que «más de un campo» sea expresable y por tanto rechazable.

### `frontend`

- **`hooks/use-item-stopwatch.ts`**, **`hooks/use-review-keyboard.ts`**, **`components/admin/three-state-list.tsx`** — extracción estrecha desde `family-review.tsx`. El cronómetro devuelve el tiempo con `measure()` para que viaje en la petición de guardado.
- **`components/admin/vocabulary-field.tsx`** y **`hooks/use-vocabulary-gaps.ts`** — selección sobre vocabulario cerrado y registro de términos ausentes, separado de las correcciones.
- **`lib/materials-vocabulary.ts`** — espejo ampliado a los seis vocabularios cerrados (`CLOSED_VOCABULARIES`), fijado por test.

### `frontend-pages` / `frontend-services`

- **`pages/admin/profile-review.tsx`** — pantalla nueva: tabla editable con confianza y procedencia por campo, texto de origen al lado, pregunta según estrato, barra de aprobación masiva acotada, vista de rechazados y tarjeta de métricas.
- **`pages/admin/family-review.tsx`** (+259/−54) — reconectada a las tres piezas compartidas; gana atajos de teclado y creación de familia. `Tabs` pasa a controlado para que el teclado sepa qué cola hay en pantalla.
- **`services/profile-review.service.ts`** y **`types/profile-review.types.ts`** — resultado discriminado para distinguir «vino vacío» de «no se pudo calcular».
- **`routing/routes.tsx`**, **`routing/app-routing-setup.tsx`**, **`config/menu.config.tsx`** — ruta `/admin/profile-review` bajo `AdminRoute`, con su entrada de menú solo para administrador.

### `openspec` / `docs`

- Nace la capability viva **`openspec/specs/profile-review/spec.md`** (15 requisitos); **`family-review`** pasa de 10 a 12.
- `openspec/DEFERRED_TASKS.md` recoge tres hallazgos sin ficha.
- `Documentos/`: informe de implementación, §15 limitación 2 con el 17,0 % real, épicas, plan de changes, `modelo-c4`, `testing-backend`, `testing-frontend` y la Authorization Matrix de `backend/README.md`.

---

## 🧪 Testing

**77 tests nuevos en backend**, todos en verde:

- `UnitTests/Application/ProfileEvidenceStratumTests.cs` — incluye `Stratum_StoneTypeAbsent_DoesNotLowerStratum` y `Stratum_ComputedIdenticallyForQueueAndMetrics`.
- `UnitTests/Application/ProfileReviewSamplingTests.cs` — `Sampling_SameSeed_ReturnsSameBatchInSameOrder`, `Sampling_StratumSmallerThanQuota_ReturnsAllAndReportsExhausted`.
- `UnitTests/Application/ProfileReviewServiceTests.cs` — `Sampling_QueueRequest_WritesNoRow`, `Review_AnyCorrection_LeavesProposedProfileJsonUnchanged`, `Review_IndividualWithoutDuration_IsRejected`, `BulkApprove_SelectionSpansStrata_IsRejectedAndModifiesNothing`.
- `UnitTests/Application/ProfileReviewMetricsTests.cs` — `Metrics_CorrectionRate_ComputedPerField`, `Metrics_ExcludesAutoBulkProfiles`, `Metrics_Total_WeightedByCorpusStratumSize_NotBySampleSize`, `Metrics_NoTimedReviews_AverageIsNullNotZero`.
- `IntegrationTests/ProfileReviewControllerTests.cs` — `ProfileReview_OperatorRole_Returns403` y `ProfileReview_Unauthenticated_Returns401` como teorías sobre **las seis rutas**, con cliente nuevo de la factoría para el 401.

**Frontend**: `pages/admin/__tests__/profile-review.test.tsx` (21) y ampliación de `family-review.test.tsx` (20 → 22) y `lib/materials-vocabulary.test.ts`. El servicio se mockea con `vi.mock` en vez de MSW, porque la suite arranca con `onUnhandledRequest: 'warn'` y un test sin handler pasaría sin afirmar nada.

**Comparación por nombres contra la línea base** (ambas suites vienen rojas de base):

| Suite | Línea base | Cierre | Fallos nuevos |
|---|---|---|---|
| Backend | 52 de 984 | 46 de 1.060 | **0** fuera de las clases dependientes del orden |
| Frontend | 113 de 482* | 113 de 595 | **0** — conjunto de nombres idéntico |

\* re-medida en esta rama; el documento citaba 118 de 482 del 2026-08-29.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: sin cambio de modelo, verificado contra la base
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**: `ai-service/` sin diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde (**57 passed, 0 failed**)
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] QA manual de la pantalla por un segundo par de ojos

---

## 🚀 Deployment notes

**Sin impacto de infraestructura**: no hay migración, no cambia el contrato de `jbg-ai`, no se añade variable de entorno obligatoria. `appsettings.json` gana una sección `ProfileReview` cuyos dos valores tienen **default en C#** (`ProfileReviewOptions`), así que un despliegue sin ella arranca igual.

Backend y SPA van en la misma imagen, así que se despliegan juntos y no hay orden que coordinar.

**Dos avisos operativos:**

1. **`ProfileReview:SamplingSeed` no debe cambiarse** una vez publicada una cifra: la semilla es lo que hace reconstruible el lote de 180 que produjo el resultado del informe.
2. **Rechazar un perfil lo saca del índice vectorial.** `IndexFeedRepository` selecciona `product.IsActive && profile.ReviewStatus == Approved`, así que un rechazo humano retira el documento de la búsqueda asistida. Es reversible desde la propia pantalla («Devolver a aprobado»).

**Rollback**: retirar las rutas y la ruta de frontend. Ningún dato escrito por este change es requerido por nada más, y los perfiles que queden en `ReviewOrigin = Human` siguen siendo válidos porque estado y origen son independientes por spec.

---

## 📝 Notas adicionales

**Sin breaking changes.** Las seis rutas son nuevas, los DTOs son archivos nuevos, y los tipos de TypeScript acompañan a los DTOs en el mismo diff.

**El punto de mayor riesgo para el reviewer** es `frontend/src/pages/admin/family-review.tsx` (+259/−54): es una pantalla de 920 líneas ya validada por una persona. La extracción fue estrecha —solo lo que tiene dos consumidores— y su suite pasó de 19/19 a 22/22 sin fallos nuevos.

**Resultados de la sesión de revisión**, con su lectura:

- Tasa de corrección ponderada por el catálogo: **20,9 %**, que se publica partida en **10,4 % en campos sensibles** y 42,3 % en etiquetas comerciales. Las segundas llegaban vacías y el revisor las rellenó con su criterio, sin verdad de referencia: no miden lo mismo y el §15 declara el 10,4 %.
- Tiempo medio: **32,1 s** sobre 204 revisiones, **204 cronometradas**. C18b registró 6 de 64.
- La predicción falsable del diseño sale **confirmada a medias**: las retiradas se concentran en el estrato B (8 de 9, cero en A, una en C), pero las adiciones están en A y no en C — A *es* el estrato de la ausencia, así que rellenar un campo vacío es una adición por construcción.

**Tres cosas se declaran sin medir en vez de estimarse** (§4 del informe): el A/B de teclado no se obtuvo porque los bloques no se separaron; la tesis de que el span es ciego a las omisiones no se puso a prueba, porque la muestra tocó 2 de sus 28 candidatos; y las 22 filas de `enrichment/v2` siguen sin ser una comparación de versiones de prompt.

**Hallazgos anotados en `DEFERRED_TASKS.md`, sin ficha:**

- `vidrio` falta en el vocabulario de `materials` y alcanza **67 productos (5,6 % del catálogo)**. Ninguna consulta automática podía encontrarlo: la exploración solo supo preguntar por los términos que ya estaban en la lista.
- El extractor emite `plata` cuando el texto dice `platino`, en 11 de 20 productos — cazados todos por la confianza a 0,45.
- `StoneType` es escalar y 14 productos nombran dos piedras. Cerrarlo exige migración **y** mover el contrato congelado.

**Dos artefactos del change se corrigieron durante el apply, con medición delante**: se retiró la marca «pendiente de revisión» por campo —constante en 6 de los 7 campos sobre 1.114 perfiles, enmendando la spec delta— y se precisó D7 sobre los consumidores reales de la carcasa extraída. La tarea 10.3 queda **sin marcar a propósito**, con el motivo escrito.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-35"></a>
## #35 — feat(ai-service): servir la capa estructurada de venta asistida (C30a)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c30a-add-assist-structure-and-rule-warnings` → `ai-eng` |
| Creada | 2026-09-13 |
| Integrada | 2026-09-13 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/35 |

### Descripción

## 📋 Descripción

`POST /v1/assist/sale` estaba congelado en el contrato desde C02 y respondía **501** con los stubs apagados. Esta PR lo convierte en implementación real: sirve **tres modos** seleccionados por los anclajes que trae la petición —consulta libre, pieza sola, pieza con pregunta—, agrupa los candidatos por un `family_id` **nulable**, emite **avisos derivados de reglas** en un vocabulario cerrado de dos códigos y devuelve **citas que resuelven a un fichero y un encabezado** del corpus en git.

**Sin una sola llamada a un modelo de lenguaje.** `pitch` sale vacío, `prompt_version` nulo y `usage` a cero: la prosa es C30b, y el corte es justo lo que la hace medible contra esta capa como ablación —misma ruta, mismos candidatos, mismas citas, con argumentario y sin él—. Con esto `/v1/inventory/propose` queda como la **única** ruta del contrato que responde 501, y no por trabajo pendiente sino porque su rama se canceló el 2026-08-31.

La PR incluye además el **archivado del change** (`openspec/changes/archive/2026-09-13-…`), la sincronización de las specs vivas —nace la capability `assist-generation`— y la puesta al día de la documentación de contexto que el archivado dejó obsoleta.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad *(ver «Notas adicionales»: el esquema se mueve, pero **no hay consumidor que romper** — verificado)*

---

## 🎯 Motivación y contexto

- **Change**: [`add-assist-structure-and-rule-warnings`](openspec/changes/archive/2026-09-13-add-assist-structure-and-rule-warnings/) (C30a) · 48/48 tareas · [ticket](openspec/changes/archive/2026-09-13-add-assist-structure-and-rule-warnings/ticket.md)
- **HU**: [HU-AIENG-030a](Documentos/Historias/AI-Eng/HU-AIENG-030a.md) · 19 escenarios, todos con test
- **Informes**: [`c30a-implementation-measurements.md`](Documentos/Proyecto%20Final%20AIEng/informes/c30a-implementation-measurements.md) · exploración [`c30-exploration-decisions.md`](Documentos/Proyecto%20Final%20AIEng/informes/c30-exploration-decisions.md)

**Por qué el contrato se mueve ahora.** El esquema congelado no podía servir a su propio consumidor: `family_id` era **obligatorio** contra un catálogo donde el **58 %** de los productos no tiene familia, y `query` era obligatoria contra dos rutas .NET ancladas a pieza. En este momento la ruta tiene **cero consumidores** —`IAiGatewayClient` no expone método de assist y C34 no existe—, así que la renegociación es gratis hoy y costaría coordinación después de C34. Precedente propio: C18a y C18b regeneraron el snapshot en el mismo change que movieron la frontera.

**Tres spikes decidieron antes de escribir código**, contra el índice vivo y al umbral de producción:

| Spike | Medición | Decisión |
|---|---|---|
| Umbral de conocimiento en M1 | 1 cita inequívocamente espuria de 101, sobre 72 consultas | **No** hace falta umbral propio |
| Filtro asimétrico de fichas | Retira 36,4 citas de ficha ajena por ancla; abstenciones 41 → 44,3 de 72 | No produce falsa abstención en masa |
| Cardinalidad de familia | Máximo observado **8** sobre 156 familias y 491 miembros | Tope del roster en **24** |

El spike 2 encontró un efecto que el diseño **no anticipó**: el filtro no sólo borra, **promueve**. Las 36,4 citas retiradas cuestan una caída neta de sólo 24,6, porque la cláusula filtra **antes del `LIMIT`** y unos 11,8 fragmentos correctos por ancla ascienden a los huecos liberados.

---

## 🔄 Cambios realizados

### `ai-contracts` — el bloque de contrato (2 archivos, +224/−29)

- `api/schemas/assist.py`: `AssistRequest` gana `product_id` y hace `query` opcional, con un `model_validator` de «al menos uno» que **nombra ambos campos** en el error. `AssistGroup.family_id` pasa a **nulable**; `AssistGroupMember` gana `match_reasons`. `Citation` se reforma —`citation_id`, `document_title`, `section_title`, `claim_scope`, `doc_type`, `score`— y **retira `source`**. `AssistResponse` gana `abstained` (obligatorio) y `prompt_version` (nulable).
- `openapi.json` regenerado: **5 esquemas movidos, 0 rutas**. Las otras nueve rutas quedan idénticas.

### `ai-service` — la capa (14 archivos, +1299/−36)

- **Paquete nuevo `assist/`**: `modes.py` (resolución estructural de los tres modos; el `intent` sale de la forma de la petición y **nunca** de las palabras, porque clasificar una consulta es C31), `constants.py` (vocabulario cerrado, lista blanca de secciones, topes), `errors.py`, `knowledge_scope.py` (el filtro asimétrico), `grounding.py` (direccionamiento por clave primaria) y `orchestrator.py`.
- **`retrieval/ports.py`**: `FamilyMember` y `family_roster(family_id, *, cap)` en `ProductSearchPort`. No es `search` con filtro de familia: no hay consulta, así que no hay vector, ni umbral, ni profundidad de rama que signifiquen nada.
- **`retrieval/search.py`**: `FAMILY_ROSTER_SQL`, una sentencia sobre `ai.product_document` **únicamente** —nunca el esquema `public`, nunca la proyección de punto de venta—, con `LIMIT` bajo el `ORDER BY`.
- **`retrieval/orchestrator.py`**: 14 líneas, 12 de ellas comentario. Costura `on_abstention`, aditiva y con la misma forma que el `on_fused_candidates` que ya existía. **Cero cambios de comportamiento.**
- **`knowledge/search.py`**: `exclude_documents` en ambas ramas (`compile_vector_sql` **y** `compile_lexical_sql`) sobre la clave primaria del documento, y `address_fragments` / `fetch_chunks` para obtener fragmentos por identidad sin búsqueda ni proveedor.
- **`api/routers/assist.py`**: despacho real con `STUB_MODE=false`; el fixture sobrevive con los stubs encendidos. Retirada la constante `DELIVERED_BY`. `UnusableAnchorProductError` → **422**, nunca un 200 con `abstained`.

### `tests` (15 archivos, +2572/−17) · `openspec` (15) · `docs` (10) · `ai-tooling` (1)

- Árbol `tests/assist/` nuevo, más `test_assist_real.py`, `test_assist_contract.py`, `test_family_roster.py`, `test_search_exclusion.py`, `test_addressing.py` y los *fakes* de `support/`.
- Change archivado; specs vivas sincronizadas: **`assist-generation` nace con 13 requisitos**, `knowledge-corpus` 11→14, `retrieval-abstention` 7→10, `ai-service-api-contracts` 14→15.
- Documentación: `arquitectura.md`, `modelo-c4.md`, `epicas.md`, plan de changes, `openspec/project.md`, `ai-service/README.md`, `ai-service/tests/README.md` y el README raíz.
- `CLAUDE.md` anota tres trampas de entorno encontradas: el validador de OpenSpec **lee sólo la primera línea física** de la descripción de un requisito, `--system-certs` arregla a `uv` pero no al proceso Python, y `psycopg` rechaza el `ProactorEventLoop` de Windows.

---

## 🧪 Testing

**Suite de `ai-service`: 1038 → 1195 tests, `0 failed`, `0 skipped`, 422,65 s.** Comparación **por nombres** contra la línea base, como exige `CLAUDE.md`: conjunto de fallos **vacío en las dos puntas**, ningún nombre nuevo en rojo. `skipped=0` confirma que el test `db` del roster corrió de verdad contra pgvector en vez de omitirse.

- `tests/assist/` — `test_modes.py` (los tres modos y el error sin anclaje), `test_grounding.py` (direccionamiento, alcance `general`, piezas mixtas), `test_orchestrator.py` (agrupación, avisos, abstención, los tres errores de pieza inservible).
- `tests/api/` — `test_assist_real.py` (ruta con stubs apagados; recorre la **respuesta serializada entera** buscando precio y stock, precisamente porque un `pitch` vacío haría pasar una comprobación sobre el `pitch` sin afirmar nada), `test_assist_contract.py`, `test_assist_stub.py`, `test_stub_mode.py`.
- `tests/knowledge/` — `test_search_exclusion.py` (exclusión por **ambas** ramas), `test_addressing.py`. `tests/retrieval/test_family_roster.py` con Testcontainers, que **se omite** si Docker no está accesible en vez de fallar.
- **67/67 escenarios de las specs** con test nombrado, y **19/19 escenarios de la HU**.

`openspec validate --all --strict`: **0 failed** (58 ítems con el change presente, 57 tras archivarlo).

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *N/A para .NET y frontend: el diff no los toca. `ai-service` suma 159 tests nuevos*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *ninguna migración: `alembic heads` sin revisión nueva y el diff no toca `migrations/`*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *el diff **no toca** `backend/`, `frontend/`, `terraform/`, `.github/workflows/`, `migrations/`, `enrichment/` ni `prompts/`*

---

## 🚀 Deployment notes

**Sin variables de entorno nuevas y sin migración.** `JPV_KNOWLEDGE_DISTANCE_THRESHOLD` no se toca —el spike 1 midió que no hace falta moverlo— y la banda de abstención (`jpv_abstention_enabled`, `α`, `N`) tampoco: la regla ya decidía, este change la **propaga y la declara**.

Con `STUB_MODE=false` la ruta exige `JPV_EMBEDDING_API_KEY` y `DATABASE_URL`, o responde **503**. Nótese que los exige también en el modo de pieza sin pregunta, que no embebe nada; es uniforme a nivel de ruta y está documentado en `ai-service/README.md`.

**Rollback**: el filtro de exclusión es aditivo y su rollback es **no pasar nada** —ausente y vacío se comportan igual, hasta el orden de los fragmentos—. Volver atrás en la ruta es reactivar `STUB_MODE`.

---

## 📝 Notas adicionales

### Sobre el breaking change: el esquema se mueve, pero no rompe a nadie

El cambio **tiene forma** de breaking —`Citation.source` desaparece, `Citation` gana seis campos obligatorios, `AssistResponse.abstained` es obligatorio y `AssistGroup.family_id` deja de serlo—, pero **no rompe ningún consumidor existente**, y eso está verificado y no supuesto: `IAiGatewayClient` expone `SearchAsync`, `EnrichAsync`, `HealthAsync`, `SuggestFamiliesAsync` y `AuditFamiliesAsync`, y **ninguno es assist**; el frontend no referencia la ruta. Los ficheros .NET que casan con «assist» son la **búsqueda asistida** (C15/C16), que consume `/v1/retrieval/products` y no se toca.

**Riesgo: alto por rúbrica** —el diff toca `ai-service/openapi.json`—, mitigado por la ausencia de consumidores y por el test de snapshot en verde.

### Seis supuestos de los artefactos resultaron falsos, y van corregidos

No silenciados: el ticket afirmaba que `retrieval/orchestrator.py` no se modificaba (se modifica); el diseño citaba 486 miembros y familias de 7 y 8 (son 491 y no existe ninguna de 7); la tarea 4.1 exigía `mypy` y `ruff`, que **no están en este repositorio**. Los seis están en el §4 del informe.

### Un hueco de especificación cerrado por escrito

Ni la HU ni el diseño dicen a qué pieza describen los avisos **cuando no hay pieza anclada**, y el escenario 3 exige que el aviso de variantes dispare en ese modo. Decisión tomada: los avisos describen la **pieza foco** —la anclada en M2 y M3, el candidato mejor clasificado en M1—. Aplicarlo a cualquier candidato haría que `size_label_missing` disparase en cuanto una de quince piezas no declarase talla, que es casi siempre y por tanto no informa de nada.

### Puntos de atención para reviewers

1. **`retrieval/orchestrator.py`** es el único fichero de una capa compartida que se toca. Merece lectura: 14 líneas, 12 comentario, y la afirmación de «cero cambios de comportamiento» depende de que la costura sólo **reporte**.
2. **La decisión de abstención no se expresa con `low_confidence`**, y no es preferencia de nombre: ese campo mide consenso entre ramas y está **anticorrelacionado** —dispara en 1 de 20 fuera de dominio y en 10 de 43 contestables—, así que reutilizarlo reportaría lo contrario de la verdad.
3. **`modelo-c4.md` arrastraba obsolescencia anterior a este change.** «Substitutes sigue 501» llevaba desactualizado desde C26 (12 de septiembre). Se corrige aquí porque eran las mismas frases que había que tocar, pero **no se ha auditado el resto del documento** buscando más de lo mismo.
4. El chunk `08-tests.diff` venía **resumido** por tamaño; el análisis de `test_orchestrator.py` en esa porción se apoya en cabeceras de hunk además del fichero en el árbol.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-36"></a>
## #36 — feat(ai-service): generar el argumentario de venta con tres puertas (C30b)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c30b-add-assist-pitch-generation` → `ai-eng` |
| Creada | 2026-09-14 |
| Integrada | 2026-09-14 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/36 |

### Descripción

## 📋 Descripción

C30a dejó `POST /v1/assist/sale` sirviendo **estructura sin prosa**: `pitch` vacío, `prompt_version` nulo y `usage` a cero. C30b escribe esa prosa en los **dos modos anclados a una pieza** y la somete a **tres comprobaciones deterministas en ejecución** —resolución, correspondencia y puerta numérica—, con **una sola reparación** y **dos políticas de degradación** según qué violación sobreviva.

El corte entre C30a y C30b era su propia ablación, y se ha cobrado: **el barrido midió 120 generaciones reales** en tres anchos de contexto, y la medición **refuta tres cosas que los propios artefactos del change daban por buenas**. La mayor: el riesgo declarado como número uno del diseño —«la puerta numérica se come los argumentarios buenos»— **no se materializó ni una vez**, `0 de 120`.

Incluye el **archivado del change** (`archive/2026-09-14-…`), el sync de la spec viva —`assist-generation` pasa de **13 a 25 requisitos**— y la documentación de contexto que el archivado dejó obsoleta.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug *(aislamiento entre tests en `db/engine.py`; ver notas)*
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad *(el contrato se mueve **una descripción**; ninguna forma de esquema cambia)*

---

## 🎯 Motivación y contexto

- **Change**: [`add-assist-pitch-generation`](openspec/changes/archive/2026-09-14-add-assist-pitch-generation/) (C30b) · [ticket](openspec/changes/archive/2026-09-14-add-assist-pitch-generation/ticket.md)
- **HU**: [HU-AIENG-030b](Documentos/Historias/AI-Eng/HU-AIENG-030b.md) · 19 escenarios
- **Informes**: [`c30b-implementation-measurements.md`](Documentos/Proyecto%20Final%20AIEng/informes/c30b-implementation-measurements.md) · exploración [`c30b-exploration-decisions.md`](Documentos/Proyecto%20Final%20AIEng/informes/c30b-exploration-decisions.md)
- **Artefacto del barrido**: [`c30b-assist-sweep-5a6e1b4b8621.json`](ai-service/evals/results/c30b-assist-sweep-5a6e1b4b8621.json) sobre la muestra declarada en [`sweep-sample.yaml`](ai-service/evals/assist/sweep-sample.yaml)

**El change retira un requisito que C30a había puesto el día antes.** *«This capability generates no prose and calls no provider»* deja de ser cierto por construcción, y eso no es una corrección sino el corte funcionando como se diseñó: `assist-generation` suma 13 requisitos, modifica el de las citas —que ahora exige que una cita publicada sea una que el argumento **usó**— y retira ese.

---

## 🔄 Cambios realizados

### `ai-service` — la capa de generación (15 archivos, +11503/−41)

| Módulo | Qué hace |
|---|---|
| `assist/prompt.py` | Prompt versionado **fijado al fichero del que se carga** y `PitchPayload`, el objeto que la puerta numérica lee. Un solo objeto, para que el conjunto admitido no pueda divergir de los datos entregados |
| `assist/schema.py` | La salida estructurada del modelo. **No vive en `api/schemas/`**, y por eso la verificación cuesta **cero** movimiento de contrato |
| `assist/llm.py` | Cliente propio. **Replica la costura de C09 y no reutiliza su clase**: `LiteLlmEnrichClient.extract()` descarta `response.usage`, y aquí hace falta en tres sitios a la vez |
| `assist/verification.py` | Las tres comprobaciones, en orden de coste. **Ningún modelo juzga nada** |
| `assist/pitch.py` | La reparación única y las dos políticas de degradación |
| `evals/assist_sweep.py` | El runner del barrido |

**El tramo de apoyo es la decisión de diseño que más compra.** La forma obvia —`{pitch, citation_ids[]}`— sólo verifica que un identificador resuelve: un modelo que devuelve los cinco que se le entregaron pasa esa comprobación trivialmente sin haber usado ninguno. Exigir que señale **cinco tramos del texto que acaba de escribir** hace que un tramo inventado sea subcadena de nada. Determinista, sin juez, sin llamada extra, ~30 tokens de salida.

**Dos políticas y no una.** Una cita que no resuelve, o una cifra que el contexto no trae, cuestan **el argumentario entero**. Un tramo declarado que no aparece en la prosa cuesta **esa cita y nada más**: el fragmento existe y estaba en el contexto, y lo que falló es el relato del modelo sobre haberlo usado.

### `ai-contracts` (2 archivos, +4/−2)

`openapi.json` se regenera por **una sola descripción**: `prompt_version` pasa de «*Null while there is no pitch*» a «*null when it did not run*». **Ninguna forma de esquema cambia.**

### `config` (1 archivo) · `openspec` (11) · `docs` (11) · `tests` (11, +2439/−13)

- `backend/.env.example` documenta `JPV_ASSIST_LLM_API_KEY`, `JPV_ASSIST_LLM_MODEL` y `JPV_ASSIST_PITCH_TIMEOUT_SECONDS`, las tres **opcionales**.
- Change archivado; `assist-generation` **13 → 25** requisitos.
- Documentación: `arquitectura.md`, `modelo-c4.md`, `epicas.md`, plan de changes, `openspec/config.yaml`, `openspec/project.md`, los dos README de `ai-service` y el raíz.

---

## 🧪 Testing

**Suite de `ai-service`: 1195 → 1320, `0 en rojo` en las dos puntas**, comparada **por nombres** como exige `CLAUDE.md`, con el conjunto en rojo **idéntico y vacío**. **125 tests nuevos** en `tests/assist/`, `tests/api/` y `tests/evals/`. *(Cifras del informe §6; en esta PR he verificado por mi cuenta la puerta de OpenSpec y los enlaces, no he vuelto a correr la suite.)*

`openspec validate --all --strict`: **57 passed, 0 failed** — verificado en esta rama.
`check-doc-links`: **937 enlaces, 0 rotos** — verificado.

**El barrido no es un test, y por eso vale**: 120 generaciones **reales** contra el proveedor, en tres anchos de contexto, con su artefacto y su muestra versionados. Ningún test de la suite llama al proveedor.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *N/A .NET y frontend: no se toca código de ninguno. `ai-service` suma 125 tests*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *ninguna, y por el motivo inverso al habitual: **el argumentario no se persiste**, así que no necesita tabla*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff — *`.env.example` deja `JPV_ASSIST_LLM_API_KEY=` **comentada y vacía***
- [x] Revisado el impacto en otros componentes del monorepo — *ver la nota sobre `backend/` abajo*

---

## 🚀 Deployment notes

**Tres variables nuevas, las tres opcionales, y ninguna migración.**

| Variable | Por defecto | Nota |
|---|---|---|
| `JPV_ASSIST_LLM_API_KEY` | repliega a `JPV_RAG_LLM_API_KEY` | Cuál ganó se registra **una vez por proceso**: `stage=assist_client … credential=assist\|rag_fallback` |
| `JPV_ASSIST_LLM_MODEL` | `openai/gpt-4o-mini` | **Nunca hereda `JPV_RAG_LLM_MODEL`** |
| `JPV_ASSIST_PITCH_TIMEOUT_SECONDS` | `4` | Segundos **por llamada**, con techo de dos por petición |

**El modelo no se hereda a propósito.** `JPV_RAG_LLM_MODEL` es el de enriquecimiento por lotes (C09); heredarlo movería un modelo **de cara al mostrador** cuyo coste y tasa de rechazo se midieron sobre otro.

**Rollback: no exportar ninguna de las dos claves.** La ruta sirve entonces la respuesta estructurada de C30a con **200 y sin prosa** — nunca un error. El rollback y la ablación son literalmente la misma palanca.

---

## 📝 Notas adicionales

### La implementación refuta tres cosas de sus propios artefactos

Ninguna silenciada; las tres están en el §4 del informe.

1. **La puerta numérica no rechazó nada: `0 de 120`.** El diseño la declaraba *el riesgo mayor del change* —«un falso positivo cuesta el argumentario entero»—. Las **121 violaciones del barrido son todas de correspondencia**. El riesgo grande no se materializó y el que sí dispara era el que parecía menor.
2. **El coste real es 1,9 × el estimado**: 0,00077 USD por petición contra los ~0,0004 de la ficha. Dos motivos visibles en el artefacto: el contexto real son 2.245 tokens de media y no ~1.500, y **el 55 % de las peticiones gasta la reparación**. Sigue siendo despreciable —el barrido entero costó 0,0897 USD— y ninguna decisión se tomó por coste, pero la cifra queda corregida en vez de repetida.
3. **El *timeout* de 3 s estaba puesto a 1,05 × p95 sin haber medido la distribución.** Corregido a 4 s por llamada.

Y una cuarta, del propio arnés: la primera pasada midió el *timeout* **contra la petición entera en vez de contra la llamada**, y leyó un 70 % donde había un 4,6 %.

### Puntos de atención para reviewers

1. **El diff SÍ toca `backend/`, y el informe dice que no.** Es **un solo fichero y no es código .NET**: `backend/.env.example`, que documenta las tres variables opcionales. El §1 del informe afirma que «`backend/` … no se toca», lo cual es cierto de la implementación pero no del conjunto de la rama —entró en `9645176` y `6e765f2`—. Verificado: `backend/.env.example` es el **único** fichero fuera de `ai-service/`, `openspec/` y `Documentos/`.
2. **`db/engine.py` es una excepción de zona, declarada.** No es de C30b. Apareció al comparar las suites por nombres: dos tests de `tests/evals/test_reproducibility.py` fallaban con una selección concreta y pasaban en la suite completa, intentando resolver el host `db`. **Es reproducible en un comando**, así que no es *flakiness*: el motor global ignoraba el `Settings` que recibe. Se arregla en vez de anotarse como folclore.
3. **La fidelidad semántica no se verifica, y está declarado.** Que el fragmento citado **diga** lo que la frase afirma es la *alucinación con coartada*: ningún juez-modelo corre en la ruta de servicio —doblaría latencia y coste con un cliente delante, y usar un modelo para cazar las fabricaciones de otro es circular—. Se mide con RAGAS en C38.
4. **La puerta numérica lee el objeto y nunca el prompt renderizado.** Si leyera el texto, las cifras de las propias instrucciones entrarían en la lista blanca y la puerta se abriría sola. `prompts/assist/v1.md` está escrito **sin un solo dígito** para que la regla no cueste nada, pero la regla no depende de que esa disciplina se mantenga.
5. **El chunk `04-ai-service.diff` viene resumido** (9.424 líneas): es el artefacto JSON del barrido, un fichero de resultados y no código.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-37"></a>
## #37 — feat(ai-service)!: clasificar la consulta antes de recuperar nada (C31)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c31-add-guardrails-and-intent-router` → `ai-eng` |
| Creada | 2026-09-16 |
| Integrada | 2026-09-16 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/37 |

### Descripción

## 📋 Descripción

Entrega **C31** (`add-guardrails-and-intent-router`): `POST /v1/assist/sale` **clasifica la consulta libre antes de ejecutar ninguna recuperación**, y con ello el servicio gana un camino explícito para reconocer que no sabe. La clasificación es de un modelo; **la aplicación de cada etiqueta es código**: la salida se valida contra un conjunto cerrado con `Literal` de Pydantic en el parseo, así que una etiqueta inventada es un fallo de parseo y nunca un valor que se propague.

Hay **dos puertas y no una**, porque «fuera de dominio» significaba dos cosas distintas: *«esto no es una pregunta de joyería»* (5 casos, el fixture de C23) y *«esto es joyería y **este** catálogo no la tiene»* (la categoría mayor del golden set, 20 de 72 — platería de mesa, relojería, papelería). Un clasificador de intención puro contesta **que sí** a las veinte. Los dos rechazos viajan con **códigos distintos**, y ninguno reutiliza `abstained`: la abstención de C25 lee el perfil de distancias *después* de recuperar y esto clasifica *antes*, así que colapsarlas haría indistinguibles las dos cifras que este change existe para publicar por separado.

`clarification_question` deja de ser permanentemente nula, resuelta **en código** desde un catálogo cerrado de plantillas es-ES; el modo anclado con pregunta gana un guardarraíl que no cuesta ninguna llamada —cero citas tras el umbral `0,51` de C23 ya significaba que el corpus no cubre la pregunta, y nadie lo leía así—; y el modo de consulta libre, que C30b difirió aquí, **redacta** sobre la ruta que el clasificador decidió. **La forma del contrato no se mueve**: `openapi.json` cambia en **tres descripciones**, verificado hoja a hoja.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [x] 💥 breaking change — **de comportamiento, no de forma** (ver Notas adicionales)

---

## 🎯 Motivación y contexto

- **Change:** `openspec/changes/archive/2026-09-16-add-guardrails-and-intent-router/` — **48/48 tareas**, archivado en esta rama.
- **HU:** [`HU-AIENG-031`](Documentos/Historias/AI-Eng/HU-AIENG-031.md) · **Ticket:** `T-AIENG-031`.
- **Capability:** `assist-generation`, que pasa de **25 a 41 requisitos**.

El problema técnico: la capa de generación sabía **callarse** pero no **decidir**. La regla de abstención de C25 es una red que lee la *forma* del perfil de candidatos después de recuperar — la propia spec viva la llamaba así — y medido, **18 de 20** consultas imposibles llegaban a la capa de generación con candidatos. Faltaba el clasificador.

C31 desbloquea **C32** (bucle agéntico) y, con él, C38 y C39. Entra **antes que C34** por decisión explícita: `/v1/assist/sale` sigue teniendo **cero consumidores** en `IAiGatewayClient`, que es la ventana en la que mover el contrato es gratis.

---

## 🔄 Cambios realizados

### `ai-service` — el clasificador y su costura

- **`assist/schema.py`** — `RouteDecision` con tres ejes `Literal`: `served` (`in_domain` / `out_of_domain` / `not_in_catalogue`), `index` (`catalog` / `knowledge` / `both`) y `missing_axis`. Los tres **requeridos**, los dos últimos anulables: el modelo se compromete con cada eje en vez de omitir los que no sabe. Interno, **nunca viaja al cable**.
- **`assist/router_llm.py`** *(nuevo)* — `LiteLlmRouterClient`. **Replica** la costura de `assist/llm.py` y no reutiliza la clase, porque aquella fija `response_format` a `AssistPitch`: temperatura 0, `num_retries: 0`, `complete` inyectable, *timeout* propio. **Una llamada, sin reintento y sin reparación** — no hay nada en una etiqueta que reparar.
- **`assist/routing.py`** *(nuevo)* — la proyección al contrato (`INTENT_BY_VERDICT`, `REFUSAL_CODE_BY_VERDICT`), el catálogo cerrado de plantillas `CLARIFICATION_TEMPLATES`, y `classify_query()`, cuyo `RoutingOutcome.degraded_cause` es `None` **exactamente** cuando hubo decisión: el *fail-open* es una rama con causa, no un `except` mudo.
- **`assist/errors.py`** — `RouterProviderError` con su `cause`, para que la degradación tenga **una** cosa que capturar.
- **`assist/orchestrator.py`** — el enrutador corre **sólo en el modo de consulta libre** y corta **antes** de `retrieve_products`; M2 no tiene consulta y M3 es `both` por construcción, y ninguno de los dos alcanza esa línea. `_task_of()` concentra toda la política de generación; `_usage()` acumula las **tres** llamadas.
- **`assist/prompt.py`** — `PitchTask` (seis secciones de tarea), `resolve_task()` y `FreeQueryPayload`, la **segunda forma de *payload***, de la que se excluyen los identificadores internos y los *scores* de recuperación. `PitchContext` deja a `verification.py` sin saber cuál de las dos lee.
- **`assist/constants.py`** — 3 intenciones y 3 códigos de aviso nuevos; `MAX_PROVIDER_CALLS` **derivado** (`1 + 2`) y no escrito como dígito.
- **`api/routers/assist.py`** — `_resolve_router_client()` con la cadena de credencial **router → assist → rag** y la línea `stage=router_client … credential=…`, una vez por proceso y sin ninguna clave.
- **`config/settings.py`** — `jpv_router_llm_api_key`, `jpv_router_llm_model` y `jpv_router_timeout_seconds`, los tres opcionales y fijados en `canonical_openapi_settings()`.
- **`prompts/`** — `router/v1..v3.md` y `assist/v2..v3.md`. **`assist/v1.md` no se toca** y hay un test que lo fija sección a sección.
- **`evals/routing.py`, `routing_run.py`, `free_query_gate.py`** *(nuevos)* — el manifiesto de 119 casos, la matriz de confusión y la puerta numérica de M1 medida **aparte**.

### `ai-contracts` — sólo descripciones

`api/schemas/assist.py` amplía las descripciones de `intent` y `warnings` (ambas construidas **desde las constantes**, no repetidas a mano) y `clarification_question` pasa de `str | None = None` a un `Field` con descripción: **mismo tipo, mismo defecto**. `openapi.json` se regenera con el perfil canónico.

### `tests` — 99 nuevos

`assist/test_routing.py` (33), `assist/test_guardrails.py` (30), `evals/test_routing_cases.py` (23), más los de `test_prompt.py`, `test_assist_generation.py`, `test_assist_contract.py` y `test_modes.py`. Helper nuevo: `tests/support/assist_router.py`.

### `openspec` — la capability y el archivado

Delta de `assist-generation` con **20 requisitos** (17 `ADDED`, 2 `MODIFIED`, 1 `REMOVED`) y **31 escenarios**, sincronizada a la spec viva (25 → 41) con el `## Purpose` reescrito. `DEFERRED_TASKS.md` gana los cuatro pasos de despliegue.

### `docs`

README raíz (estructura, tests y §1.2), `ai-service/README.md`, `tests/README.md`, `modelo-c4.md`, `openspec/project.md`, `epicas.md`, plan de changes, e informe de implementación con las cifras.

---

## 🧪 Testing

**`uv run --system-certs pytest`: 1418 passed / 0 failed** (línea base 1320). Comparado **por nombres de test**, no por recuento: **99 node id nuevos, 4 desaparecidos y los cuatro renombrados con sucesor** — afirmaban vocabularios cerrados «en exactamente dos» y «el modo de consulta libre no tiene bloque de tarea», propiedades que este change invierte a propósito. **Ningún test se borra.**

Ningún test llama a un proveedor real: los clientes se conducen sobre un `complete` guionizado que envuelve el **cliente real**, así que el parseo, la validación del conjunto cerrado, el *timeout* y la extracción de coste son los de producción y sólo se sustituye el socket.

Lo que cubren, por si es útil al revisar:

- **El vocabulario cerrado se aplica en el parseo** — `test_a_label_outside_the_closed_vocabulary_fails_the_parse` (5 casos) y `test_an_unknown_label_never_appears_anywhere_in_the_response`, que comprueba sobre el **volcado entero** de la respuesta.
- **El corte ocurre antes de recuperar** — los dos rechazos y la repregunta se afirman con índices que **revientan** si se los toca. Incluye `test_the_refusing_doubles_actually_refuse`, que conduce cada doble por la llamada exacta que hace producción: la primera versión de uno de ellos sobreescribía un método que `search_knowledge` nunca llama y **no podía disparar**.
- **M2 y M3 no pagan clasificador** — por introspección, con un cliente que levanta si se le llama.
- **El *fail-open*** — parseo inválido, etiqueta desconocida, `timeout`, fallo de proveedor y ausencia de credencial, cada uno con su causa y su test.
- **El techo de 3 llamadas** — una clasificación, una generación y una reparación, observable desde `usage`.
- **Determinismo de la repregunta** — 4 ejes × 2 ejecuciones, texto idéntico.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *no aplica a backend/frontend: no se tocan. 99 tests nuevos en `ai-service`*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: sin cambio de datos; `alembic heads` sigue en `d7c4e91b25a0`*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — **57 passed / 0 failed**
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo — *`backend/`, `frontend/`, `terraform/` y `.github/` sin cambios; la ruta queda anotada en las fichas de C34 y C36*

---

## 🚀 Deployment notes

**Tres variables nuevas, las tres opcionales, y ninguna hay que poner todavía.**

| Variable | Defecto | Nota |
|---|---|---|
| `JPV_ROUTER_LLM_API_KEY` | ausente | cadena **router → assist → rag**; la resuelta se registra una vez por proceso |
| `JPV_ROUTER_LLM_MODEL` | `openai/gpt-4o` | **movido por medición**, ver abajo |
| `JPV_ROUTER_TIMEOUT_SECONDS` | `2.0` | **declarado no calibrado**; deliberadamente **fuera** de los pasos de despliegue hasta medir la distribución del propio despliegue |

**Sin credencial el clasificador no se construye**, `intent` vuelve a `unclassified` y la ruta se comporta **exactamente** como la dejó C30b. Eso es el *fail-open*, la ablación y el rollback a la vez, y está entregado con test. Los cuatro pasos (parámetro SSM a mano, `deploy.sh` sin `:?`, `compose.demo.yaml`, runbook) están en `openspec/DEFERRED_TASKS.md`. **Terraform no se toca**: el rol de instancia ya lee todo el prefijo `/jbg-demo/`.

> ⚠️ **Un despliegue que apunte `JPV_ROUTER_LLM_MODEL` a `gpt-4o-mini` estaría sirviendo una configuración que el veto rechazó.**

**Rollback:** quitar la credencial.

---

## 📝 Notas adicionales

### Breaking changes — de comportamiento, no de forma

1. **Una consulta libre fuera de dominio deja de devolver grupos.** Hoy devuelve hasta cinco, y es el defecto que el change existe para cerrar.
2. **`intent` gana tres valores.** Un consumidor que compare contra `unclassified` verá `in_domain`, `out_of_domain` y `not_in_catalogue`.

Ninguno rompe a nadie hoy: `/v1/assist/sale` tiene **cero consumidores** — `IAiGatewayClient` no lo implementa y C34 no existe. Ésa es la razón de abrir C31 antes que C34.

**La forma del contrato no se mueve, y está verificado aplanando los dos `openapi.json` a hojas** (no leyendo el diff): 1102 → 1103 hojas, **0 campos añadidos, 0 retirados, 0 tipos cambiados**, 346 hojas de `type` y 125 de `required` **idénticas**. La única hoja «nueva» es una clave `description` sobre un campo que ya existía. El diff de git son **3 líneas**, que es exactamente por qué leerlo a ojo no bastaba.

### Para quien revise: el veto tumbó la primera configuración

D12 declaró **antes de medir** que una sola consulta contestable silenciada rechaza la configuración. La primera medición sobre los 119 casos:

| prompt | modelo | `catalog` | falso positivo | silenciadas | veto |
|---|---|---|---|---|---|
| `router/v1` | `gpt-4o-mini` | 47,9 % | 31,25 % | **15** | **NO PASA** |
| `router/v2` | `gpt-4o-mini` | 79,2 % | 8,33 % | 4 | **NO PASA** |
| `router/v3` | `gpt-4o-mini` | 81,3 % | 6,25 % | 3 | **NO PASA** |
| **`router/v3`** | **`gpt-4o`** | **100 %** | **0,00 %** | **0** | **PASA** |

Lo que fallaba **no era clasificar intención**, sino no saber cómo se nombra este catálogo: sus piezas se llaman `<tipo> <motivo>` —«Colgante erizo de mar», «Anillo caracola»—, así que *«el bicho con puas que se pisa en las rocas»* **es** una consulta de catálogo. Tres revisiones de prompt llevaron el falso positivo de 31,25 % a 6,25 % y **no lo cerraron**; lo cerró el **modelo**, con el mismo prompt. Eso enmienda la opción por defecto nº 4 del ticket y **vindica D9**: la variable separada del modelo es lo único que permitió moverlo sin invalidar las 120 generaciones de C30b.

**Las seis pasadas se conservan en `evals/results/`**, incluidas las que fracasaron. Una versión que fracasa y se borra es una medición que nadie puede repetir.

### El riesgo mayor declarado no se materializó

La lista blanca numérica de la consulta libre resultó ser de **~13 numerales y no de cinco** —`top_k=5` cuenta familias tras hidratar y la recuperación devuelve **15** candidatos— y la puerta numérica rechazó **0 de 89**. Lo que retiraba el argumentario era `dangling_citation`, porque la sección de tarea de `catalog` no decía que no hubiera citas y la regla invariante «puedes no citar nada» **permite sin obligar**. Corregido en `assist/v3`.

### Tres defectos que la verificación encontró, los tres míos

1. **Dos dobles de test que no podían fallar.** `_refusing_knowledge` sobreescribía `search`, que `search_knowledge` **nunca llama**. La aserción «no se ejecuta búsqueda de conocimiento» era **vacía**.
2. **El veto podía aprobar de forma vacía.** Una pasada con 89 de 119 casos muertos por límite de tasa informó «PASA». Ahora exige **cobertura completa**.
3. **La contradicción que el archivado destapó.** El requisito vivo de los avisos declaraba *«SHALL emit exactly two codes»* y C31 los lleva a **cinco**, sin que la delta lo modificara. Ni el validador ni los tests lo habrían visto. Corregido **en la delta**, no en la spec viva.

### Limitaciones declaradas, no cerradas

- **La cifra del enrutador es dentro de muestra.** Tres revisiones de prompt y un barrido de modelo se decidieron mirando resultados sobre el mismo conjunto. Se dice en vez de disimularse. Lo que **no** queda contaminado es el veto: es un criterio de rechazo declarado antes de medir.
- **Los diez casos `both` son construidos**, y **las veinte `not_in_catalogue` fueron elegidas para ser insatisfacibles**, así que el 100 % sobre ellas es una **cota superior**.
- **La fidelidad semántica no se mide**: es C38.
- **El rechazo no se ve en pantalla**: la consulta libre no tiene superficie. La ruta queda anotada en C34 y el bloque de copy en C36.
- **La primera consulta libre tras un arranque en frío degrada**, porque el `import litellm` cae dentro del *timeout* de la llamada. Cae en el *fail-open*, que es correcto, y queda anotado en `DEFERRED_TASKS.md`.

### Contraste con el umbral de C23

`0 discrepancias en 37` entre el enrutador y el umbral `0,51` sobre el eje servir/no servir: dos mecanismos que no comparten ni entrada ni método coinciden por completo, lo que es la evidencia más fuerte disponible de que aquel hueco de 8 milésimas separa algo real.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-38"></a>
## #38 — feat(ai-service): registrar seis tools de solo lectura del agente (C32a)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c32a-add-sales-assistant-tool-registry` → `ai-eng` |
| Creada | 2026-09-20 |
| Integrada | 2026-09-20 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/38 |

### Descripción

## 📋 Descripción

Entrega **C32a**, la mitad baja del agente de venta: las **seis herramientas de solo lectura** y el registro que las contiene, sin bucle y sin ruta. `assist/tools.py` (845 líneas, nuevo) define el descriptor de tool, la observación, el registro y el invariante; `assist/constants.py` gana los dos vocabularios cerrados; y `retrieval/ports.py` y `search.py` ganan **dos lecturas nuevas y ninguna modificación**.

El corte es deliberado y se nota en lo que *no* está: no hay bucle, ni iteraciones, ni presupuestos, ni `partial: true`, ni `POST /v1/assist/agent`. Todo eso es **C32b**. La consecuencia es que `ai-service/openapi.json` queda **idéntico byte a byte** (`sha256 43f70fda…68c684`) y `POST /v1/assist/sale` se comporta exactamente como lo dejó C31 — y no por cuidado al editar, sino estructuralmente: **nada en `src/` importa `assist/tools.py`**, así que el módulo no es alcanzable desde la aplicación.

Lo que esta mitad sí entrega de lo evaluable es **uno de los cuatro puntos** del agente: el invariante de solo-lectura, comprobado por **introspección del grafo de objetos** en la construcción del registro —los nombres, los métodos de cada puerto capturado y los verbos HTTP de cualquier cliente— y no con una bandera `writes: bool` que pondría quien registra la tool, que es justo quien podría equivocarse. El §15.8 del diseño declara al mundo que ningún agente escribe: o se demuestra o no se declara.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

No es *breaking*: no se retira ni se modifica ningún comportamiento publicado. Las dos lecturas nuevas son **adiciones** a un `Protocol`, que obligan a ampliar los dobles de la suite pero no a ningún consumidor del servicio.

---

## 🎯 Motivación y contexto

- **Change**: `openspec/changes/archive/2026-09-20-add-sales-assistant-tool-registry/` — archivado en esta misma rama, 44/44 tareas, 10/10 del DoD.
- **HU**: [`HU-AIENG-032a`](Documentos/Historias/AI-Eng/HU-AIENG-032a.md), nueve escenarios de aceptación, los nueve trazados a test nombrado.
- **Capability nueva**: `sales-assistant-tools` — 13 requisitos, 25 escenarios.

C32 se partió el 2026-09-20 y ésta es la mitad que **no llama a ningún proveedor de chat**, lo que la hace medible a coste cero. Había además una deuda concreta que vencía aquí: de las seis tools de la ficha, **cinco estaban servidas por código ya probado y una no tenía servicio detrás**, `consultar_disponibilidad`. El §6.1 del diseño RAG dejaba el esquema de la llamada de vuelta Python → .NET como *«decisión abierta del change del agente de venta»*, y éste es ese change.

**Se cierra difiriéndola con motivo.** La tool se sirve desde `ai.pos_projection`, un dato que Python ya tiene proyectado, en vez de inventar un esquema de autenticación de vuelta: la única arista Python → .NET que existe es `AiIndexFeedController`, autenticada con `X-Index-Feed-Key`, **sin `[Authorize]` a propósito** y **sin transportar `pos_id`**, y su ruta `pos-availability` es un feed paginado de 200 filas con keyset, no una consulta puntual. El endpoint .NET queda **identificado, acotado y no hecho** en `openspec/DEFERRED_TASKS.md`.

---

## 🔄 Cambios realizados

### `ai-service` — el registro y sus vocabularios

- **`assist/tools.py`** *(nuevo)*: `ToolSpec` (nombre, descripción es-ES, esquema de parámetros derivado de un modelo de pydantic, ejecutor), `ToolObservation` (acotada, y el fallo es una de sus formas), `ToolRegistry` con el conjunto de nombres **congelado por igualdad** —cinco tools es tan erróneo como siete—, `build_registry()` que recibe los puertos **ya construidos**, y `verify_read_only()` que corre en la construcción.
- **`ToolRegistry.invoke()` no lanza nunca.** Valida los argumentos **antes de tocar ningún puerto** y traduce cada fallo a una causa de vocabulario cerrado. El `except Exception` final es el requisito, no pereza: una excepción que escapara mataría el bucle de C32b en vez de gastarle una vuelta.
- **`assist/constants.py`**: `TOOL_NAMES` (seis, congelado) y `WITHDRAWN_TOOL_NAMES` (`perfil_punto_venta`, `buscar_complementarios`, nombradas para que su vuelta no sea un diff silencioso); las **cuatro etiquetas de disponibilidad** y el mapa desde `QTY_BUCKETS`; las **cuatro causas de fallo**; y `WRITE_METHOD_VERBS` / `WRITE_HTTP_VERBS`.
- **`retrieval/ports.py` y `search.py`**: `document_by_sku()` y `availability_bucket()` — **116 inserciones, 0 borrados**. Ninguna consulta existente se modifica; `DOCUMENT_BY_SKU_SQL` es `SOURCE_DOCUMENT_SQL` con otro `WHERE`, y `AVAILABILITY_BUCKET_SQL` es `SCOPE_BUCKETS_SQL` con un predicado más.

Decisiones que conviene que el revisor vea:

- **Disponibilidad como etiqueta cualitativa sin dígitos**, nunca el bucket. `QTY_BUCKETS` es `{"0","1-2","3+"}` — son cifras, y pasarlas al modelo es lo que la frontera del §6.2 prohíbe.
- **`sin_ambito` es un cuarto valor y no «agotado»**. Sin `pos_id` en el principal, o sin fila de proyección, la observación lo dice. Confundirlos dispararía el pivote a sustitutos sobre una pieza que la tienda sí puede vender.
- **Direccionamiento por SKU y nunca por identificador interno**, que es por lo que hacían falta las dos lecturas nuevas.
- **Sin `score` crudo en ninguna observación**: si el orden importa viaja como `posicion`. Un *score* de recuperación y uno de sustitutos no miden lo mismo.
- **`pedir_aclaracion` elige eje; el castellano lo escribe el código**, resuelto del catálogo cerrado de C31.

### `tests` — 51 pruebas nuevas, todas offline

`tests/assist/test_tools.py` *(nuevo)* y la ampliación de `tests/support/fake_product_search.py` (44 inserciones, 0 borrados). El invariante se ejerce **contra un puerto que sí escribe, registrado a propósito**, con un descriptor que afirma explícitamente lo contrario — y la construcción falla igual.

### `openspec`

Delta y spec viva de `sales-assistant-tools`, el change archivado con sus seis artefactos, la ficha del endpoint .NET diferido en `DEFERRED_TASKS.md`, el párrafo de contexto de C32a en `config.yaml` (**sin ajuste ni credencial nuevos**) y la entrada de C32a en el historial de `project.md`.

### `docs`

HU nueva; informe de implementación con las seis refutaciones; el README de `ai-service` y el de su suite; y en `proyecto-final-diseno-rag-joiabagur.md` el **cierre del §6.1**: la nota fechada, la arista `consultar_disponibilidad` del diagrama Mermaid pasada a punteada y etiquetada «NO HECHA», y la tabla de agentes corregida de `(.NET)` a `ai.pos_projection`.

### `ai-tooling`

`doc-impact.json` de la skill `update-docs`, en los **cinco harnesses**: el diseño RAG no estaba en la matriz pese a ser el documento que los diseños de C30a–C32a citan como autoridad, así que ninguna pasada de `update-docs` lo habría propuesto nunca.

---

## 🧪 Testing

| | |
|---|---|
| Suite `ai-service` | **1.469 passed / 0 failed**, 0 skipped |
| Comparación | **por nombre de test** (`comm` sobre los *node id*), no por recuento: **0 desaparecidos** |
| Línea base | 1.418 / 0, medida en un `git worktree` sobre el árbol limpio |
| Pruebas marcadas `db` en el change | **0** — `pytest -m db tests/assist/test_tools.py` → `51 deselected` |
| Llamadas a proveedor | **0, y por construcción**: `test_the_assist_package_imports_no_provider_client` recorre todos los módulos de `jbg_ai.assist` —ahora también `tools.py`— y exige que ninguno importe `litellm`, `openai`, `anthropic` ni `httpx` |
| Red | `test_the_whole_registry_runs_with_no_socket_available` ejerce las seis con `socket.connect` parcheado para fallar |

Los nueve escenarios de la HU y los 25 de la delta están trazados a test nombrado, con la tabla en el §6 del informe y el §3 del QA.

**Una pasada de verificación independiente** reprodujo cada cifra contra el árbol antes de archivar y encontró cuatro cosas, **dos de ellas defectos de código**, corregidas en `ab5c27a`:

1. La exclusión de objetos inertes del invariante estaba escrita **por categoría** —todo modelo de pydantic y toda dataclass—, lo que dejaba `InMemoryKnowledgeIndex` (el puerto que `consultar_conocimiento` captura, y que es una dataclass) **fuera de los tres ejes**, y habría dejado pasar un puerto que escribiera si estuviera escrito como cualquiera de las dos. Ahora se excluyen **dos tipos nombrados**, `Settings` y `ServicePrincipal`.
2. `document_by_sku()` resolvía con `.first()` apoyándose en un comentario que afirmaba que `sku` es único en `ai.product_document`. **No lo es** — la unicidad la impone .NET sobre su propia tabla, y el ticket archivado de `add-pgvector-schema-foundation` decidió expresamente no crear ese índice —, así que un SKU duplicado devolvía una fila arbitraria de un resultado sin `ORDER BY`. Ahora es `.one_or_none()`.
3. El campo `abstenido` no tenía ningún test que ejerciera su camino `True`: las aserciones existentes habrían pasado sobre un `False` cableado a mano.
4. El enunciado de lo que el vocabulario de escritura pierde era inexacto.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` — puertos inyectados y nunca construidos, como el resto de `assist/` desde C30a
- [x] Hay tests para el código nuevo — 51 pruebas en `tests/assist/test_tools.py`
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: `backend/` sin tocar y `alembic heads` sin mover (`d7c4e91b25a0`)
- [x] `ai-service/openapi.json` actualizado si cambia el contrato — **no cambia**: idéntico byte a byte, verificado por `sha256` y por `git diff` vacío
- [x] Spec de la capability actualizada y `openspec validate --all --strict` en verde — **58 passed, 0 failed**
- [x] Documentación de `Documentos/` actualizada
- [x] Sin secrets ni credenciales en el diff — este change no añade ninguna variable de entorno
- [x] Revisado el impacto en otros componentes del monorepo — `backend/`, `frontend/`, `terraform/` y `.github/` sin tocar

---

## 🚀 Deployment notes

**Sin impacto de despliegue.** Ninguna variable de entorno nueva, ninguna dependencia nueva (`pyproject.toml` sin tocar), ninguna migración y ningún cambio de contrato. Nada de lo que entrega este change es alcanzable desde fuera del proceso, porque no se cablea a ninguna ruta.

**Rollback**: retirar el módulo. Al no haber consumidor y al no moverse el contrato, la marcha atrás no deja rastro en ninguna superficie publicada. La única huella fuera de `assist/` son las dos lecturas añadidas al puerto, que ningún camino existente invoca.

---

## 📝 Notas adicionales

**Limitaciones declaradas, no descubiertas después:**

- **Las dos sentencias SQL nuevas no se han ejecutado nunca contra PostgreSQL.** Ninguna prueba del change está marcada `db` y el doble las simula. Se apoyan en las mismas tablas y columnas que consultas ya en producción, pero **eso es un argumento y no una medición**. La primera ejecución real ocurrirá en C32b o en el primer despliegue que las use.
- **El invariante caza lo que puede cazar**, y sus cuatro límites están escritos en el código y en el §8 del informe: no recorre atributos de un colaborador; sólo ve lo que el ejecutor **cierra**; sobre `pedir_aclaracion` pasa **vacuamente** porque esa tool no captura nada (mitigado con una prueba de anti-vacuidad); y el vocabulario de escritura **no es exhaustivo** — `put_checkpoint()` escribe y no casa, ni por token ni por subcadena. Es un suelo bajo el grafo de objetos, no una demostración de que ningún método escribe.
- **Nada protege el `Protocol` `ProductSearchPort`.** No es `runtime_checkable`, nada hace `isinstance` contra él, y el repositorio no tiene `mypy` ni workflow de CI para `ai-service`. Una implementación futura que olvide uno de los dos métodos fallará donde se use, no al construirse. Queda dicho en el §2.5 del informe; añadir `mypy` es un cambio de la puerta de calidad del repositorio y no cabe aquí.
- **Las descripciones de las tools no se han medido contra un modelo**, ni se ha comprobado si la granularidad de seis es la correcta. Es limitación estructural del corte: esta mitad no llama a ninguno, y una descripción es un *prompt* que se itera con medición. Ocurre en **C32b**.

**Para quien construya el endpoint .NET diferido**: un cliente HTTP de propósito general **no pasará** el tercer eje del invariante, porque expone `post`, `put`, `patch` y `delete`. Habrá que envolverlo en una superficie que exponga sólo la lectura — que es precisamente la restricción que se quería dejar puesta.

**Aguas abajo**: desbloquea **C32b** y, a través de él, **C38** y **C39**.



---

<a id="pr-39"></a>
## #39 — feat(ai-service): añadir el bucle agéntico del asistente de venta

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c32b-add-sales-assistant-agent-loop` → `ai-eng` |
| Creada | 2026-09-21 |
| Integrada | 2026-09-21 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/39 |

### Descripción

## 📋 Descripción

Añade a `jbg-ai` el **bucle agéntico del asistente de venta**, que es la mitad de C32 que llama al proveedor. Se sirve en una ruta propia, `POST /v1/assist/agent`, y `POST /v1/assist/sale` se queda como la fila determinista de la ablación, idéntica campo a campo.

El bucle hace *function calling* manual sobre las seis *tools* de solo lectura del registro de C32a. Lo acotan **seis presupuestos**:

- 5 vueltas;
- 8 llamadas a *tools*;
- 8 llamadas al proveedor, cifra derivada de las constantes de sus tres tramos;
- 40.000 tokens de prompt;
- 30.000 caracteres de observaciones;
- 15 s de reloj para la petición entera, con 8 s reservados al argumentario.

Si se agota cualquiera, la respuesta sale con `partial: true` y un `stop_reason` de vocabulario cerrado. La transcripción multi-turno viaja en la petición porque el servicio no guarda nada entre llamadas. El contrato se mueve **por adición pura**.

Incluye además una **pasada con proveedor real de dos brazos** (`gpt-4o` y `gpt-4o-mini`, 204 peticiones) que fija tres de los presupuestos por medición. La rama lleva también la **verificación independiente** de esa implementación con sus correcciones, el **archivado del change** con la sincronización de dos specs vivas, y la **puesta al día de la documentación**.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

Los *fix* corrigen defectos de esta misma rama, encontrados por la verificación independiente antes del merge. Nada de lo que ya está en `ai-eng` cambia de comportamiento.

---

## 🎯 Motivación y contexto

C32 se partió el 2026-09-20. **C32a** (PR #38) entregó las seis *tools* y su registro sin llamar a ningún proveedor. **C32b** entrega la capa de decisión: de las cuatro cosas que el Proyecto Final evalúa de un agente —el bucle, el presupuesto duro, el invariante de solo-lectura y el `partial: true`— faltaban tres.

La ruta es aparte porque el peor caso del bucle no cabe en los 5 s que el diseño declara para `/v1/assist`. Además, la ablación *pipeline contra agente* necesita que las dos rutas sigan ejecutables sobre el mismo conjunto.

- **Change de OpenSpec:** `openspec/changes/archive/2026-09-21-add-sales-assistant-agent-loop/`: proposal, design (D-1..D-18), specs, tasks (77/77), ticket y QA.
- **Historia:** `Documentos/Historias/AI-Eng/HU-AIENG-032b.md`.
- **Informe:** `Documentos/Proyecto Final AIEng/informes/c32b-implementation-measurements.md`.

---

## 🔄 Cambios realizados

### ai-service

- **El bucle, `assist/agent.py`.**
  - `run_agent()` recibe todos sus puertos y clientes inyectados.
  - El clasificador de C31 actúa de **guardarraíl**: una sola llamada, sobre el turno que se contesta. El rechazo cortocircuita en cualquier turno; el veredicto de insuficiencia y el de índice se ignoran.
  - Las llamadas de una vuelta se ejecutan en paralelo con un tope de 4, por debajo del pool de 5 conexiones.
  - Las que no caben en el presupuesto vuelven como observación con la causa `presupuesto_agotado`, sin tocar ningún puerto.
  - `pedir_aclaracion` es terminal: termina el bucle.
  - Proyección de la evidencia al argumentario (`_pieces`):
    - los sustitutos llegan como grupo distinguido;
    - ninguna etiqueta de disponibilidad llega al *payload*;
    - la pieza que el bucle abandonó al pivotar no llega como coincidencia;
    - el tope de piezas descarta antes coincidencias que sustitutos.
  - `AgentRun` guarda el uso de cada etapa por separado (`router_usage`, `loop_usage`, `pitch_usage`).
  - Dos trazas: la del cable no lleva argumentos; la que queda en proceso, sí.
  - `agent_response()` es el único punto de proyección al contrato.
- **El puerto, `assist/agent_llm.py`.** `AgentStep` **no declara ningún campo capaz de llevar prosa**. `LiteLlmAgentClient` usa temperatura 0, no fija `response_format`, pone `num_retries` a 0 y descarta el texto en la frontera, de modo que sólo registra su longitud y su *digest*.
- **La transcripción, `assist/transcript.py`.** Tres topes: 12 turnos, 500 caracteres por turno y 4.000 en total. Cada turno va delimitado con `QUERY_OPEN`/`QUERY_CLOSE`, y los turnos atribuidos al asistente se tratan como dato del cliente.
- **Vocabularios y límites, `assist/constants.py`.** Los seis presupuestos, `AGENT_PITCH_RESERVE_SECONDS` (derivada), los diez `STOP_*`, `GROUP_ORIGIN_*`, `TURN_ROLE_*` y la quinta causa de fallo `TOOL_CAUSE_BUDGET_EXHAUSTED`. `assist/errors.py` añade `AgentProviderError` y `TranscriptError`.
- **Registro, `assist/tools.py`.** `EvidenceLedger` guarda lo que el contrato exige y la observación excluye por regla: `product_id`, `score` y el título del documento. Es inerte al invariante de solo-lectura **por construcción**, porque no tiene métodos públicos; la PR incluye un test de que un *ledger* con `save()` se rechaza.
- **Generación.** `assist/pitch.py:generate_pitch()` recibe `prompt_version` para no sellar `assist/v4` como `assist/v3`. `assist/prompt.py` añade `AgentPitchTask` y el campo `origin` de `FreeQueryGroup`, que sólo se renderiza cuando está puesto, así que el *payload* de `/sale` no cambia. `orchestrator.py` hace pública `to_citation`. `llm.py` corrige un comentario falso sobre sumas de uso con varios modelos.
- **Ruta, `api/routers/assist.py`.** `assist_agent()` sirve `POST /v1/assist/agent`, y `_resolve_agent_client()` resuelve la credencial con la cadena `agent → assist → rag`, registrando una vez por proceso qué eslabón ganó. La reserva del argumentario sale del *timeout* configurado.
- **Ajustes, `config/settings.py`.** `jpv_agent_llm_api_key`, `jpv_agent_llm_model` (por defecto `openai/gpt-4o`) y `jpv_agent_timeout_seconds` (por defecto 8), fijados en `canonical_openapi_settings()`.
- **Stub, `stubs/responses.py`.** `assist_agent_stub()` no simula ningún bucle: cero iteraciones, `stop_reason=sin_cliente`, sin avisos.
- **Prompts.** `prompts/agent/v1.md` es el mensaje de sistema del bucle. `prompts/assist/v4.md` es `v3` más la tarea de evidencia del agente. `v3` queda intacto.
- **Instrumentos.** `evals/agent_sets.py` genera `evals/agent/load-set.yaml` (82 transcripciones sintéticas). `evals/agent/calibration.yaml` tiene 20 escenarios escritos a mano, es `calibration-only` y declara la discrepancia de C19 en su campo `declared_discrepancy`.
- **Arnés, `evals/agent_sweep.py`.**
  - Ejecuta la pasada de dos brazos y tarifa **cada etapa con su propio modelo**.
  - Calcula la tasa de pivote por brazo y puntúa las expectativas de la calibración.
  - Escribe cada fila en cuanto la produce (`.partial.jsonl`).
  - La procedencia registra los modelos de las tres etapas y el `sha256` de cada prompt.
  - `--rescore` recalcula cualquier artefacto sin proveedor ni base de datos.
- **Artefactos, `evals/results/`.** La pasada `c32b-agent-sweep-293fe5c6e470.json` (204 filas), sus cinco sondas y el `.rescore.json` con las cifras que publica el informe.

> Los *chunks* de `agent.py`, `agent_sweep.py`, `tests/assist/test_agent.py`, los artefactos JSON, `load-set.yaml`, el fixture de contrato y `qa.md` salen **truncados** en el diff por tamaño. Lo que se dice aquí de `agent.py` y `agent_sweep.py` está verificado contra el fichero del árbol, no contra el chunk.

### ai-contracts

- **Esquemas, `api/schemas/assist.py`.**
  - `AgentTurn` y `AgentAssistRequest`: los topes van declarados en el esquema, y `pos_id` se acepta y se ignora.
  - `AgentAssistResponse` es **subclase** de `AssistResponse` y añade `partial`, `stop_reason`, `iterations`, `tool_calls_used`, `trace` y `agent_prompt_version`.
  - `AgentUsage(Usage)` añade `calls` y redeclara `model` con una descripción que dice que no es clave de precio.
  - `AgentTraceTool` y `AgentTraceIteration` forman la traza del cable.
- **Contrato, `ai-service/openapi.json`.** 393 inserciones y 0 supresiones. Frente al contrato de C32a: 1.103 → 1.289 hojas, **0 retiradas y 0 cambiadas**, y todas las añadidas caen dentro de `/v1/assist/agent` y sus seis modelos. `AssistResponse` y el `Usage` compartido no cambian.

### tests

- **107 tests nuevos:**
  - `tests/assist/test_agent.py`: 49;
  - `tests/evals/test_agent_sets.py`: 19;
  - `tests/api/test_agent_route.py`: 13;
  - `tests/evals/test_agent_sweep.py`: 13, los primeros tests del arnés;
  - `tests/assist/test_transcript.py`: 12;
  - `tests/data/test_envload.py`: 1.
- `tests/support/assist_agent.py` es el doble guionizado del proveedor.
- `tests/api/fixtures/openapi-c32a-baseline.json` es el contrato de C32a, contra el que `test_the_published_contract_moved_by_addition_only` particiona hoja a hoja.
- **Tres tests preexistentes modificados**, ninguno retirado ni renombrado: `test_prompt.py` (el directorio de prompts pasa a v1–v4), `test_openapi_snapshot.py` (undécima ruta) y `test_tools.py` (el registro sigue sin declarar ruta ni presupuesto).

### config

- **`backend/.env.example`.** Documenta el bloque `JPV_AGENT_LLM_API_KEY` (comentada y vacía), `JPV_AGENT_LLM_MODEL=openai/gpt-4o` y `JPV_AGENT_TIMEOUT_SECONDS` (comentada). No hay ningún `.cs`, `.csproj` ni migración.

### openspec

- **Archivado.** El change pasa a `openspec/changes/archive/2026-09-21-add-sales-assistant-agent-loop/`.
- **Specs vivas.** Nace `openspec/specs/sales-assistant-agent/spec.md` con 22 requisitos y 46 escenarios. `openspec/specs/sales-assistant-tools/spec.md` cambia dos requisitos: el vocabulario de causas pasa de cuatro a cinco, y el requisito sobre rutas deja de llamar al bucle «a later change».
- **`openspec/DEFERRED_TASKS.md`.** Cuatro entradas nuevas:
  - la política de *timeout* y de circuito de la ruta en .NET;
  - la nota de que 15 s ya acota la petición entera;
  - once tests preexistentes que salen a la red;
  - el desglose del uso por etapa en el cable.
- **`openspec/project.md` y `config.yaml`.** Entrada de C32b y cifras corregidas.

### docs

- **Informe de implementación.** Diez secciones más un §11 con lo que cambió en la verificación.
- **HU-AIENG-032b.**
- **READMEs.** `ai-service/README.md` (variables `JPV_AGENT_*`, ruta, *non-goals*, *Layout*, sección de C32b), `ai-service/tests/README.md` y el README raíz (§2.3 y §2.6).
- **`Documentos/arquitectura.md`.** 11 endpoints `/v1` y la historia real de los movimientos del contrato.
- **`Documentos/modelo-c4.md`.** *Agent Loop* existe.
- **`Documentos/epicas.md` y plan de changes.** C32b archivado y recuento de 35 archivados / 4 pendientes.
- **Diseño RAG.** §6.4 y §9.2.

---

## 🧪 Testing

- [x] Tests unitarios y de ruta con pytest, sin proveedor, sin red y sin base de datos. El proveedor se sustituye por dobles guionizados y los puertos por *fakes*.
- [x] Un test por motivo de parada y por presupuesto. Incluye que el reloj acota la petición entera, argumentario incluido, y que la rama global de contexto llega a ejecutarse.
- [x] Invariantes de tipo y de seguridad: `AgentStep` no tiene campo de prosa; la inyección en el turno 3 de 5 no cambia el mensaje de sistema de ninguna llamada real; un turno de asistente falsificado se trata como dato.
- [x] Contrato: adición pura hoja a hoja contra el fixture de C32a, y `/v1/assist/sale` idéntico en campos y techo.
- [x] Arnés: coste por etapa, pivote por brazo, `KeyError` de `pivot_rates` cubierto, evaluador de expectativas, escritura incremental, y `--rescore` del artefacto commiteado reproduciendo las cifras del informe.
- [ ] Resultado de la suite: **no lo muestra el diff.** El QA archivado (§1 y §12) registra **1.576 passed / 0 failed**, comparado por nombres de test contra 1.469 con 0 nombres desaparecidos, y `openspec validate --all --strict` en 59 / 0.
- [ ] `dotnet test` y `npm run test`: no ejecutados, porque no se toca código .NET ni frontend.

---

## ✅ Checklist pre-merge

- [ ] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — no aplica: todo el código nuevo es de `ai-service` y lleva sus tests en el diff
- [x] Migración de EF Core incluida si cambia el modelo de datos — no aplica: no cambia el modelo de datos ni el esquema `ai`
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`) — `backend/.env.example` lleva las claves comentadas y vacías
- [ ] Revisado el impacto en otros componentes del monorepo

---

## 🚀 Deployment notes

- **Variables de entorno nuevas, todas opcionales:**
  - `JPV_AGENT_LLM_API_KEY`, con respaldo en `JPV_ASSIST_LLM_API_KEY` y luego en `JPV_RAG_LLM_API_KEY`. Sin ninguna de las tres, `POST /v1/assist/agent` responde 200 sin ejecutar el bucle (`stop_reason=sin_cliente`) y nunca 503.
  - `JPV_AGENT_LLM_MODEL`, por defecto `openai/gpt-4o`.
  - `JPV_AGENT_TIMEOUT_SECONDS`, por defecto 8, por vuelta.
  - Ninguna es necesaria para arrancar `/health`. `backend/docker-compose.yml` y `terraform/` no las pasan al contenedor, igual que ya ocurría con las de C30b y C31.
- **Sin migraciones**, ni de EF Core ni de Alembic, y **sin dependencias nuevas**: `pyproject.toml` y `uv.lock` no están en el diff.
- **Contrato:** la ruta es nueva y por ahora **no tiene consumidor .NET**. La política de *timeout* y circuito de ese lado está identificada y no hecha, en `openspec/DEFERRED_TASKS.md`.
- **Rollback**, de menor a mayor coste:
  1. Quitar la credencial del agente: la ruta deja de construir el cliente y degrada.
  2. Apuntar `JPV_AGENT_LLM_MODEL` al brazo barato. Es más barato, pero se midió que no sostiene la selección de herramienta.
  3. Revertir la ruta: como el movimiento del contrato fue adición pura, ningún consumidor existente se entera.

---

## 📝 Notas adicionales

- **Breaking changes: ninguno.** Es una ruta nueva; `AssistResponse` y el `Usage` compartido no cambian, y `/v1/assist/sale` sigue igual.
- **Riesgo: medio.** Se regenera `ai-service/openapi.json`, aunque por adición pura y verificado hoja a hoja. Hay lógica nueva de control de flujo con llamadas a un proveedor externo, cada una acotada por su *timeout* y por el reloj de la petición.
- **Cifras publicadas.** El sobrecoste del agente frente al *pipeline* es **×3,0** (`gpt-4o`) y **×1,1** (`gpt-4o-mini`), con cada etapa tarifada con su propio modelo. La pasada costó 3,82 USD. `gpt-4o-mini` se descartó por comportamiento: agota un presupuesto en el 66 % de las peticiones, frente al 1,2 % de `gpt-4o`. Todo es reproducible con `python -m jbg_ai.evals.agent_sweep --rescore`.
- **Fe de erratas.** El mensaje del commit `0f444f9` decía ×7,6, «46 respuestas» y que `dangling_citation` retiraba el 13,1 %. La verificación independiente lo corrigió:
  - ×7,6 tarifaba el clasificador con un coste sin fuente;
  - el 13,1 % es la retirada por cualquier causa, y `dangling_citation` explica 9,5 puntos;
  - el «46» no es verificable.

  Está en el §12 del QA archivado. La historia de git no se reescribe.
- **Abierto y medido, no cerrado:**
  - el agente retira el 13,1 % de los argumentarios en `gpt-4o`, frente al 2,2 % de la ruta determinista;
  - la mención de disponibilidad en el argumento se mide (`pitch_availability_terms`), pero no se impide;
  - la proyección tras un pivote cambió después de la pasada, así que su efecto en la calidad del argumento queda para el change de evaluación (C38).
- **Hallazgo preexistente, fuera de alcance:** once tests de `tests/api/test_assist_generation.py` (C30b y C31) salen a `api.openai.com` con una clave falsa. Está registrado en `openspec/DEFERRED_TASKS.md`.
- **Para reviewers.**
  - El `.rescore.json` registra `git_sha 0f444f9…+dirty` porque se generó antes de commitear; regenerarlo da las mismas cifras.
  - La latencia de 15 s síncronos queda declarada como limitación: no hay *streaming*.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-40"></a>
## #40 — feat(backend): rutas .NET del card de venta con hidratación y marcadores

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c34-add-dotnet-assist-and-recommendation-endpoints` → `ai-eng` |
| Creada | 2026-09-22 |
| Integrada | 2026-09-22 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/40 |

### Descripción

## 📋 Descripción

C34 entrega **el primer consumidor .NET** de `POST /v1/assist/sale` y `POST /v1/retrieval/substitutes`: dos rutas ancladas a una pieza que el card de venta de C36 podrá leer sin reinterpretar nada. `POST /api/ai/products/{productId}/sales-assist` devuelve el argumentario de la pieza (o la respuesta a una pregunta sobre ella) y `GET /api/ai/products/{productId}/substitutes` los sustitutos que esa tienda puede vender hoy.

El invariante que gobierna todo el change es que **ninguna cifra que lea el operario la ha escrito un modelo**. El punto de venta se valida con la regla de C15 y la pieza anclada se comprueba con una `HydrateAsync` **antes** de llamar a la IA, así que un 400, un 403 o un 404 nunca cuestan una llamada de pago; el grupo que devuelve el índice se hidrata contra el catálogo transaccional de esa tienda conservando el orden de la IA; y `{{price}}` y `{{stock}}` se resuelven contra la pieza anclada —`ToString("C2", es-ES)` y un entero invariante—. Si tras sustituir queda cualquier `{{` o `}}`, **se retira el argumentario y no la respuesta**: los grupos, los avisos y las citas se sirven igual, y la plantilla cruda no llega a ningún campo ni a ninguna línea de log.

La pasarela gana su tercera familia de ruta, la generativa. El cliente `ai-assist` tiene presupuesto de 10 s con **suelo de 8 s comprobado al arrancar**, circuito propio y **ningún reintento ante un timeout o un 5xx** —sólo ante una conexión que no llegó a abrirse—, porque cualquier otro fallo pudo ocurrir con la generación ya en marcha y repetir paga dos veces al proveedor. Un **422 deja de leerse como «IA no disponible»** en esas dos operaciones y sólo en ellas. Con la IA caída, o con el interruptor apagado, el card sale igual: **200** con la pieza y su familia leídas del catálogo.

La rama incluye además el **archivado del change**, la sincronización de sus dos capabilities a las specs vivas, una **verificación independiente adversarial** del trabajo y la puesta al día de la documentación de contexto.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/` (**C34**, archivado en esta rama con 50/50 tareas).
- **Historia**: [`HU-AIENG-034`](Documentos/Historias/AI-Eng/HU-AIENG-034.md), épica **EP15**. Ticket `T-AIENG-034` dentro del change.
- **Informes**: [`c34-exploration-decisions.md`](Documentos/Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md) (nuevo, 863 líneas) y [`c34-implementation-measurements.md`](Documentos/Proyecto%20Final%20AIEng/informes/c34-implementation-measurements.md).

`POST /v1/assist/sale` y `POST /v1/retrieval/substitutes` estaban servidos y medidos en `jbg-ai` desde C26, C30a, C30b y C31, pero **no tenían ningún consumidor .NET**: ni el argumentario, ni las citas, ni los sustitutos llegaban a un operario. En `IAiGatewayClient` no había método para ninguna de las dos, y `AssistTimeoutMs = 5000` estaba reservado y sin usar.

La exploración previa **refutó la anotación de la ficha** que daba a C34 la ruta de la consulta libre: los marcadores `{{price}}`/`{{stock}}` no dicen de qué pieza son, y en ese modo el argumentario habla de varias. Por eso el change se queda con las dos rutas del card, y M1 y la ruta del agente **quedan fuera por decisión cerrada**, con el arreglo identificado y no hecho —es de Python—.

---

## 🔄 Cambios realizados

### `backend-api` (5 archivos, +774/−1)

- **`AiSalesAssistController.cs`** (nuevo): `[Route("api/ai/products")]` con `POST {productId:guid}/sales-assist` bajo la política `AiSalesAssist` y `GET {productId:guid}/substitutes` bajo `AiSearch`. La pregunta viaja **sólo en el cuerpo** —es texto libre sobre un cliente y una URL la registran el proxy, el navegador y cualquier caché—. Validación invocada explícitamente, porque `SuppressModelStateInvalidFilter` está activo, y cuerpo nulo tratado.
- **`SalesAssistDtos.cs`** (nuevo): contrato hacia el frontend con `PitchStatus` (seis valores) y `SubstitutesOutcome` (cuatro), serializados en *snake_case* vía `JsonStringEnumMemberName`.
- **`AiAssistSaleDtos.cs`** y **`AiSubstitutesDtos.cs`** (nuevos): DTO del contrato de `jbg-ai`, **sin `pos_id` en el cuerpo** —el ámbito viaja en el token—.
- **`AiGatewayOutcome.cs`**: gana `Rejected`.

### `backend-application` (13 archivos, +1720/−7)

- **`SalesAssistService.cs`** (nuevo): autoriza, comprueba la pieza, llama, hidrata el grupo con **una** `HydrateAsync`, calcula los avisos, decide el `pitchStatus` en el orden del diseño y degrada. Nunca lanza por un fallo de la IA.
- **`SubstitutesService.cs`** (nuevo): una llamada con `top_k = 20` —la ventana de 60 que el contrato permite—, filtro `Quantity > 0`, orden intacto, `Take(pageSize)` y los cuatro `outcome`.
- **`SalesCardAccess.cs`** (nuevo): las comprobaciones que comparten las dos rutas. Replica la lógica de `AssistedSearchService.AuthoriseAsync` **en vez de extraerla**, porque es privada y moverla tocaría una ruta que este change promete dejar intacta.
- **`PitchPlaceholderResolver.cs`** (nuevo): unidad pura. Sólo los dos tokens exactos; cualquier `{{` o `}}` restante retira el argumentario; **sin pieza anclada retira siempre**.
- **`AiGatewayClient.cs`**: `AssistSaleAsync` y `SubstitutesAsync`, con guarda de ámbito de catálogo y de petición sin pieza antes de emitir nada, y `TranslateAnchoredStatus` —método aparte— para que el 422 se traduzca **sólo** en esas dos operaciones y `TranslateStatus` siga intacto para el resto.
- **`AiGatewayServiceCollectionExtensions.cs`**: cliente con nombre `ai-assist` en el hueco reservado, con su propio circuito, `HttpClient.Timeout` infinito y un predicado de reintento que sólo acepta `HttpRequestException { HttpRequestError: ConnectionError }`.
- **`AiGatewayOptions.cs`**: `AssistTimeoutMs` 5000 → **10000**, con `MinimumAssistTimeoutMs = 8000` validado al arranque.
- **`AiSalesAssistOptions.cs`** y **`AiSalesAssistServiceCollectionExtensions.cs`** (nuevos): interruptor por punto de venta, umbral de stock crítico, ventana y páginas de sustitutos y límite de peticiones, con cinco reglas de validación al arranque que **nombran la clave** al fallar.
- **`SalesAssistRequestValidator.cs`** (nuevo): `pointOfSaleId` obligatorio, `question` no vacía tras `Trim()` y ≤ 500 —**el máximo que declara el contrato congelado**, no un número elegido aquí— y `pageSize` acotado por configuración.
- **`AiRequestRejectedException.cs`** (nuevo).

### `backend-misc` y `config` (3 archivos, +41/−1)

- `ServiceCollectionExtensions.cs`: política `AiSalesAssistRateLimit`, ventana fija **particionada por usuario** —detrás del proxy toda una tienda comparte dirección—, con límite alto en test salvo que el test lo fije.
- `Program.cs`: `AddSalesAssist(builder.Configuration)`.
- `appsettings.json`: `AiGateway:AssistTimeoutMs` a 10000.

### `tests` (17 archivos, +2996/−140)

- **`ThrowingAiGatewayClient.cs`** (nuevo): clase base con todos los métodos de `IAiGatewayClient` lanzando. Los **siete dobles escritos a mano** de C03 migran a ella, así que el próximo método no vuelve a romperlos.
- **`FakeHttpMessageHandler.cs`**: gana `EnqueueConnectionFailure()` y `EnqueueHangUntilCancelled()`. El `EnqueueHang()` existente lanza `TaskCanceledException` en el acto, así que la estrategia de timeout de Polly **nunca veía expirar su presupuesto** y un test de «no reintenta el timeout» habría pasado aunque el predicado sí los reintentara.
- **`AiGatewayTestHost.cs`**: acepta el manejador del cliente nuevo y un `TimeProvider`, registrado **antes** de `AddAiGateway` para que el *pipeline* lo tome del contenedor.
- Diez clases nuevas o ampliadas: `SalesAssistServiceTests`, `SubstitutesServiceTests`, `PitchPlaceholderResolverTests`, `SalesAssistConfigurationTests`, `AiGatewayAssistTests`, `AiSalesAssistControllerTests`, `AiSalesAssistRateLimitTests`, y filas nuevas en `AiContractSnapshotTests`, `AiGatewayRegistrationTests` y `AiGatewayClientTests`.

### `infra` y `misc` (2 archivos, +40/−0)

- `deploy/demo/deploy.sh`: lee `ASSIST_LLM_API_KEY` con `|| true` y **sin `:?`** —su ausencia es un estado válido— y registra si está o no, nunca su valor.
- `compose.demo.yaml`: `JPV_ASSIST_LLM_MODEL` y `JPV_ASSIST_LLM_API_KEY` en `jbg-demo-ai`; `AiSalesAssist__EnabledByDefault` y `AiGateway__AssistTimeoutMs` en la API.

### `openspec` (13 archivos, +3119/−8)

- El change **archivado** en `changes/archive/2026-09-22-…/` con sus cinco artefactos y su registro de QA.
- **Specs vivas sincronizadas**: `ai-sales-assist` **nace** con 15 requisitos y 45 escenarios; `ai-gateway-client` pasa de 16/48 a **17/63** sin perder ningún requisito ni escenario previo.
- `DEFERRED_TASKS.md`: cierra *«C30b — la demo no genera argumentario»*, re-mide *Instance sizing* y abre dos entradas del entorno.
- `project.md`: ficha de C34 y corrección de «Still zero .NET consumers» en las de C30b y C31, que dejaron de ser ciertas con este change.

### `docs` y `ai-tooling` (17 archivos, +1966/−37)

`backend/README.md` (endpoints, matriz de autorización y variables), `arquitectura.md`, `modelo-c4.md`, `epicas.md`, el plan de changes, `deploy/demo/README.md` y el README raíz. `testing-backend.md` gana una familia nueva en el inventario de fallos conocidos. `CLAUDE.md` precisa que el MITM de Norton no alcanza a los contenedores. La matriz de impacto de `update-docs` gana los globs de la demo, en los cinco harnesses.

---

## 🧪 Testing

**181 tests nuevos**, todos en verde. La suite se comparó **por nombres** contra una línea base medida sobre el árbol previo, que es la única comparación válida en este repositorio: el recuento varía entre ejecuciones.

| Medición | Resultado |
|---|---|
| Línea base (árbol previo, *worktree* desprendido) | 1060 nombres · 49 en rojo |
| Cierre | 1241 nombres · 50 en rojo |
| Nombres de la línea base ausentes al cierre | **0** |
| Nombres **nuevos** en rojo | **0** |

Los que rotan son de `InventoryIntegrationTests` —rotación ya documentada— y `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct`, una carrera de reloj de microsegundos en un controlador **fuera del diff**, que esta rama añade al inventario de fallos conocidos.

Cobertura del código nuevo: **97,0 % de líneas y 94,9 % de ramas**. Declarado: `AiGatewayClient.SubstitutesAsync` se queda en 76,4 % porque sus ramas de timeout, transporte y cuerpo malformado no tienen test propio —las de `AssistSaleAsync`, que son el mismo código, sí—.

**Ocho mutaciones de control**, compilando cada una antes de correr: siete mueren donde deben (filtro de stock, umbral de stock crítico, regla de variantes, resolución de marcadores, ausencia de `pos_id` en el cuerpo). La octava **sobrevivió** y destapó un hueco real: el orden entre `withheld_out_of_stock` y `withheld_unresolved` no estaba cubierto. Cerrado con `SalesAssist_OutOfStockAnchor_WinsOverAnUnresolvedPlaceholder`, verde sobre el árbol y rojo él solo bajo esa mutación.

Los tests de integración **usan un doble del gateway y comprueban que se invocó**, con el interruptor encendido explícitamente: los de C15 nunca llegan al gateway y daban verde en vacío.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica: el diff no toca `JoiabagurPV.Infrastructure/`**
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica: `ai-service/` está fuera del diff y el blob del contrato es el mismo objeto git**
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — **60 passed / 0 failed**
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] QA manual sobre el entorno desplegado por quien revise

---

## 🚀 Deployment notes

**Sin migración de EF Core y sin cambio de contrato**: el diff no toca `JoiabagurPV.Infrastructure/` ni `ai-service/`, y `terraform/` queda intacto.

**Las rutas nacen apagadas.** `AiSalesAssist:EnabledByDefault` vale `false`, así que sin configuración las dos rutas responden 200 degradado sin llamar a la IA. Encenderlas es un acto explícito, por punto de venta o por defecto, y `IOptionsMonitor` lo recarga **sin redesplegar**.

Variables nuevas, todas opcionales salvo la primera:

| Variable | Valor | Dónde |
|---|---|---|
| `AiGateway__AssistTimeoutMs` | `10000` — **el arranque rechaza < 8000** | API |
| `AiSalesAssist__EnabledByDefault` / `__EnabledPointOfSaleIds__N` | `false` / vacío | API |
| `AiSalesAssist__StockCriticalThreshold`, `__Substitutes*`, `__RateLimit*` | por defecto en código | API |
| `JPV_ASSIST_LLM_MODEL` | `openai/gpt-4o-mini` | `jbg-ai` |
| `JPV_ASSIST_LLM_API_KEY` | **el único secreto opcional** | `jbg-ai` |

**`/jbg-demo/ASSIST_LLM_API_KEY` se crea a mano como `SecureString`.** Su ausencia es un estado declarado: sin ella no se construye el cliente de generación, la ruta sigue respondiendo 200 con el grupo, los avisos y las citas, y el card lo ve como `not_generated`. **Borrar el parámetro y redesplegar es el rollback de la generación.** Terraform no se toca: el rol de instancia ya lee todo el prefijo `/jbg-demo/`.

**Orden de despliegue**: `jbg-ai` es el proveedor del contrato y ya sirve ambas rutas desde changes anteriores, así que no hay dependencia de orden nueva. Apagar el interruptor devuelve el card al camino degradado sin desplegar nada.

**Dos pasos por entorno**, documentados en `deploy/demo/README.md` §5.5c y abiertos en `DEFERRED_TASKS.md`: un entorno recién desplegado deja `ai.pos_projection` vacía y **toda** la recuperación responde 503 hasta que se drena con `sync-pos --full`; y el corpus de conocimiento **no viaja en la imagen** de `jbg-ai`, así que hay que copiarlo y lanzar `sync-knowledge --full`. Ninguno de los dos es de C34 —el segundo se arregla en `ai-service/Dockerfile`, que este change declara intocable— pero ambos hacen que la IA parezca rota.

---

## 📝 Notas adicionales

**Sin breaking changes.** Las rutas son nuevas, `POST /api/ai/search` queda intacto —`AssistedSearchService.cs` y `AiSearchController.cs` están fuera del diff— y el contrato de `jbg-ai` es el mismo objeto git. `IAiGatewayClient` crece con dos métodos, lo que rompería los dobles de test escritos a mano; por eso el change extrae `ThrowingAiGatewayClient` y migra los siete.

**Componentes sin alinear**: el frontend no entra en esta PR. El card que consume estas dos rutas es **C36**, y hereda una obligación explícita — los seis `pitchStatus` y los cuatro `outcome` significan cosas distintas, y pintarlos como una misma ausencia haría mentir a la pantalla.

**Fuera de alcance, con motivo**: la consulta libre sin pieza (M1) y la ruta del agente. Sus marcadores no tienen pieza a la que referirse, el arreglo es de Python y queda identificado. La política de timeout y circuito de `/v1/assist/agent` sigue diferida.

**Limitaciones declaradas**: el 11,7 % de los argumentarios escribe `{{stock}}` donde un número no encaja gramaticalmente; cuando .NET retira el argumentario las citas son sólo las que ese argumentario usó, un subconjunto que no se puede reconstruir; una familia editada tarda en verse en el camino nominal hasta la siguiente sincronización del índice; y en el cuerpo de `/sales-assist` un 422 no se distingue de una caída —el log sí los distingue, y añadir un campo no rompería nada—.

**Puntos de atención para quien revise**:

1. `SalesAssistService.DecidePitch` implementa un **orden fijo** de seis estados; el primero que aplica gana. Es lo que C36 pinta, y el par 4↔5 sólo tiene test desde la verificación independiente.
2. El 422 se traduce en `TranslateAnchoredStatus`, deliberadamente separado de `TranslateStatus`. `SearchAsync_When422_StillThrowsUnavailable` existe para que estrecharlo al resto rompa la suite.
3. El presupuesto de 10 s **no se bajó** pese a que el máximo medido fue 7,9 s: está al 99 % del suelo de 8 s, y bajarlo dejaría sin margen justo las peticiones más lentas, que son las que reparan el argumentario.
4. La última corrida completa de la suite tarda ~8 min y **viene en rojo de fábrica**; compara nombres, no números.

**Verificación independiente**: el §14 del QA archivado registra una pasada adversarial hecha por una sesión distinta de la que implementó. Encontró una cifra falsa —el QA afirmaba «0 migraciones de EF Core» en el salto de la demo cuando había **tres**, de C28, que la API aplica sola al arrancar— y el hueco de test del punto 1. Las dos, corregidas en esta rama.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-41"></a>
## #41 — feat(frontend): añadir la ficha de venta con desambiguación por familia

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c36-add-frontend-assist-card-and-family-disambiguation` → `ai-eng` |
| Creada | 2026-09-24 |
| Integrada | 2026-09-24 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/41 |

### Descripción

## 📋 Descripción

Entrega la **ficha de venta del frontend** en `/sales/new/assist/:productId`, que consume las dos rutas .NET que C34 dejó servidas y **sin ningún consumidor**: `POST /api/ai/products/{id}/sales-assist` y `GET /api/ai/products/{id}/substitutes`. Es la única pantalla del Proyecto Final que pone la capa RAG delante de una persona, y cierra la cadena `C30a → C34 → C36`.

La zona del cambio es **`frontend/src/`**. No hay migración de EF Core, no se toca código de `backend/` ni de `ai-service/` —0 ficheros de cada uno en el diff— y `ai-service/openapi.json` sigue en `d8d48f87b279d45d22bce80a67c4fd51caef6e679363c413f5b697c99ec2b875`, idéntico byte a byte. Los únicos ficheros fuera de `frontend/` son documentación: `backend/README.md`, `CLAUDE.md`, `Documentos/`, `README.md` y `openspec/`.

La PR incluye además el **archivado del change** —`openspec/changes/archive/2026-09-24-add-frontend-assist-card-and-family-disambiguation/`— con la sincronización de sus dos delta specs, y la documentación de contexto que ese archivado deja desfasada.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

El `fix` es `piece-header.tsx`: la cabecera pintaba «24 en **esta tienda**» teniendo el identificador del punto de venta en la mano, porque `assist.tsx` sólo cargaba la lista de tiendas al abrirse en frío y el camino normal —punto de venta por estado de navegación— nunca pedía el nombre.

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-09-24-add-frontend-assist-card-and-family-disambiguation/` (C36), archivado en esta misma PR con sus 50 tareas completas.
- **Historia**: [HU-AIENG-036](Documentos/Historias/AI-Eng/HU-AIENG-036.md), 11 escenarios de aceptación.
- **Épica**: EP15 — Venta Asistida, Sustitutos y Agentes, que **queda completa** con este archivado.

Hasta aquí el argumentario, las citas, el agrupado por familia y los sustitutos existían, estaban medidos y **sólo se demostraban con `curl` y con el arnés de evaluación**. C34 se escribió para el desarrollador porque no había pantalla; esto se escribe para el operario.

La regla que gobierna la pantalla es la que la spec viva de `assisted-search-panel` ya imponía y esta capability hereda: **no se enseña nada que el sistema no haya afirmado**. El frontend no reordena, no recalcula stock ni precio, no añade avisos y no inventa la etiqueta de un código que no conoce.

---

## 🔄 Cambios realizados

### `frontend-services` — contrato y servicio

- `types/sales-assist.types.ts`: los objetos de transferencia de C34 (`SalesAssistResponse`, `SalesAssistGroup`, `SalesAssistMember`, `SalesAssistCitation`, `SubstitutesResponse`, `SubstituteResult`) con los dos enumerados **en snake_case**, tal como .NET los serializa.
- `services/sales-assist.service.ts`: las dos llamadas con **desenlaces tipados que nunca lanzan**, siguiendo el patrón de `ai-search.service.ts`. Miembros propios para `429` —exceder el presupuesto no es una caída— y para `404`, que aquí significa «esta tienda no lleva esta pieza».

### `frontend` — los seis bloques y la tabla de copia

- `components/sales/sales-assist-card/`: `piece-header.tsx`, `warnings-block.tsx`, `pitch-block.tsx`, `family-block.tsx`, `question-box.tsx`, `substitutes-block.tsx` e `index.ts`. Ningún componente de interfaz nuevo: `card`, `badge`, `alert`, `collapsible`, `skeleton`, `textarea`, `select` y `button` ya estaban en la plantilla.
  - `family-block.tsx`: una fila y **un botón por miembro, sin preselección** —el clic es la confirmación—; degrada al SKU el miembro sin `variantLabel`, marca el ancla y el agotado, y **no reordena**. Con un solo miembro vuelve la acción directa.
  - `pitch-block.tsx`: los **seis `pitchStatus` como cinco mensajes**, sin fundir `ai_unavailable` con `not_generated`, y las citas con `claimScope` distinguido —insignia y frase propias para un compromiso de la casa— **ocultas cuando el argumentario no se entrega**.
  - `piece-header.tsx`: `size_label_missing` como **atributo junto al SKU**, nunca entre los avisos.
  - `question-box.tsx`: límite de **500 caracteres** comprobado antes de enviar, y la caja deshabilitada mientras una pregunta está en vuelo.
- `lib/assist-copy.ts`: la tabla de copia en módulo propio y probada directamente — los **cinco códigos alcanzables**, la etiqueta neutra `UNKNOWN_WARNING_LABEL` para cualquier otro, los cinco mensajes de estado, los cuatro desenlaces de sustitutos y las cinco preguntas sugeridas del corpus.
- `components/sales/assisted-search-result-row.tsx`: gana `onOpenCard?` como prop **opcional**. La firma de `onSelect` **no se toca**.

### `frontend-pages` — ruta, orquestación y las tres entradas

- `routing/routes.tsx` y `routing/app-routing-setup.tsx`: `SALES.ASSIST(productId)` y la ruta con **carga perezosa** (el paquete la emite como `assist-<hash>.js`, aparte del `index`).
- `pages/sales/assist.tsx`: la orquestación — episodio por visita en una referencia inicializada de forma perezosa, **guarda de respuestas fuera de orden** (`requestSeq`), **una petición al entrar y sin reintento automático** (`askedForRef`, que guarda el punto de venta y no un booleano), y el disparador de sustitutos por `anchor.hasStock` y **nunca por `pitchStatus`**.
- `pages/sales/assisted.tsx`, `pages/sales/new.tsx`, `pages/sales/scan.tsx`: las tres entradas.

> **Cambio de comportamiento a revisar:** `scan.tsx` **ya no salta solo a la caja**. Antes, al resolver un código, navegaba de inmediato a `/sales/new`; ahora se detiene en una tarjeta con dos acciones. *«Continuar con la venta»* es la primaria y aterriza exactamente donde aterrizaba antes, con el mismo estado de navegación. El escenario 1 de la HU pide que el operario **active** la acción, y sin un instante en el que elegir no hay dónde ponerla. Es un toque más en un flujo de venta.

### `openspec` — archivado y specs vivas

- El change se mueve a `openspec/changes/archive/2026-09-24-…/` con sus cuatro artefactos y sus 50 tareas completas.
- **Nace `openspec/specs/sales-assist-card/spec.md`**: 11 requisitos, 38 escenarios.
- `openspec/specs/assisted-search-panel/spec.md`: **14 → 15** requisitos y **43 → 47** escenarios, por adición pura. La fila gana la acción secundaria, que no sustituye ni bloquea la selección para venta y **no reporta selección a la telemetría**.
- `openspec/project.md`: entrada de C36 en la lista de changes archivados.
- `openspec/DEFERRED_TASKS.md`: dos entradas nuevas —servir la parte estructural de la ficha sin pagar una generación, y la telemetría de la ficha—, encadenadas a propósito.

### `docs` — contexto de largo plazo

- `Documentos/epicas.md`: **37 archivadas y 2 pendientes**, contadas contra `openspec/changes/archive/`; **EP15 completa**.
- `Documentos/modelo-c4.md`: módulo **Sales Assist Card (C36)** en Nivel 3, resumen de EP15, y el diagrama Mermaid del frontend con **los cuatro módulos de IA** (C16, C18b, C28 y C36), que le faltaban todos.
- `Documentos/Proyecto Final AIEng/proyecto-final-diseno-rag-joiabagur.md`: §15.12 reescrita, §15.13 ampliada y **§15.14 nueva** (la ficha no tiene telemetría).
- `README.md` §1.2 y §1.3, `frontend/README.md`, `backend/README.md`, `Documentos/testing-frontend.md`, `CLAUDE.md` y los dos informes del change.
- `Documentos/Proyecto Final AIEng/informes/c40-exploration-decisions.md` **no es de este change**: es la exploración de C40, que viaja en esta rama por haberse hecho durante la implementación.

---

## 🧪 Testing

**132 tests nuevos en seis ficheros, los 132 en verde.** Todos con `vi.mock` y **sin un solo handler de MSW**, porque `src/test/setup.ts` arranca con `onUnhandledRequest: 'warn'` y un test podría pasar sin haber afirmado nada.

| Fichero | Tests |
|---|---|
| `pages/sales/__tests__/assist.test.tsx` | 62 |
| `lib/assist-copy.test.ts` | 35 |
| `services/sales-assist.service.test.ts` | 22 |
| `pages/sales/__tests__/assist-entrances.test.tsx` | 6 |
| `components/sales/__tests__/assisted-search-row-card-action.test.tsx` | 4 |
| `pages/sales/__tests__/new-assist-card-entrance.test.tsx` | 3 |

**La suite de frontend viene roja de fábrica, así que la comparación es por nombres y no por número.** Línea base regenerada en un worktree sobre el commit de artefactos y comparada con el informador JSON:

```
BASELINE : 113 failing of 597, in 14 files
HEAD     : 113 failing of 729, in 14 files
NEW failing names (must be 0): 0        ← subconjunto estricto
```

**Cobertura del código nuevo**, medida sobre los seis ficheros de test (umbral del proyecto: 70 % sentencias/líneas/funciones, 60 % ramas):

| Fichero | Sentencias | Ramas | Funciones | Líneas |
|---|---|---|---|---|
| `lib/assist-copy.ts` | 100 | 100 | 100 | 100 |
| `services/sales-assist.service.ts` | 95,65 | 70,58 | 100 | 100 |
| `pages/sales/assist.tsx` | 92,72 | 89,77 | 100 | 95,87 |
| `components/sales/sales-assist-card/` | 91,04 | 82,29 | 95,83 | 95,16 |

**Mutaciones de control.** Tres invariantes se rompieron a mano y se revirtieron; dos fueron reproducidas de forma independiente durante la verificación, con el número y los nombres exactos que el informe declara:

| Mutación | Tests que caen |
|---|---|
| `warningLabel` devuelve el código en bruto | **5** — 3 del módulo y 2 de la pantalla |
| El disparador de sustitutos pasa a `pitchStatus` | **8** — el bloque entero, incluido `should not request substitutes when the card is degraded` |
| `data-selected="true"` en la fila del ancla | **1** — `should preselect no member when the group has several` |

Otras puertas: `npm run build` verde (15,39 s, 3850 módulos) y `openspec validate --all --strict` en **61 passed, 0 failed**.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` — con una desviación declarada en Notas adicionales
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — 84–100 % en sentencias, medido
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no cambia**: 0 ficheros en `Migrations/`
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no cambia**: `sha256` idéntico y 0 ficheros de `ai-service/` en el diff
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — 61 passed, 0 failed
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`) — sólo **nombres** de variable en `backend/README.md`, ningún valor
- [x] Revisado el impacto en otros componentes del monorepo — `backend/` y `ai-service/` sin una línea de código tocada
- [ ] QA manual sobre el demo desplegado — pendiente, ver Deployment notes

---

## 🚀 Deployment notes

**Sin variables de entorno nuevas, sin dependencias nuevas, sin migración y sin orden de despliegue que coordinar**: el proveedor del contrato (C34) ya está en `ai-eng`, así que este consumidor puede ir solo. La imagen de producción empaqueta API y SPA juntas; `jbg-ai` no se toca.

**Dos interruptores que hay que conocer antes de probar la ficha**, ninguno de ellos nuevo y ninguno presente en ningún `appsettings`:

| Interruptor | Por defecto | Síntoma si está apagado |
|---|---|---|
| `AiSalesAssist:EnabledByDefault` | `false` | La ficha responde 200 con `aiAvailable: false` y «El asistente no está disponible» |
| `AiSearch:EnabledByDefault` | `false` | El panel cae a la vía léxica |

Con el de la ficha apagado, `SalesAssistService` **ni siquiera llama** al servicio de IA (`degradedReason = "switched_off"`) y la pantalla pinta correctamente su estado degradado. **Parece un defecto de esta PR y no lo es.** Quedan documentados en `backend/README.md`.

**Rollback**: la ruta es nueva y con carga perezosa, y las tres entradas son botones añadidos. Revertir el commit de la ruta deja el resto del flujo de venta intacto. La excepción es `scan.tsx`, que cambia de comportamiento (ver arriba).

**Pendiente**: la comprobación con datos reales se ejecutó el 2026-09-24 en **entorno local** y no en el demo desplegado —mismo código, misma base con el mundo de C10 y el índice de C13, mismo `jbg-ai` con credencial real y `STUB_MODE=false`—, porque `compose.demo.yaml` tira de imágenes de ECR y de secretos del almacén de parámetros. La equivalente sobre el demo es el §5.6b de `deploy/demo/README.md`. Aviso que esa guía ya documenta: **`ai.knowledge_chunk` nace vacía** en un entorno nuevo, así que las cinco preguntas sugeridas responderán todas que la documentación no las cubre hasta que se cargue el corpus.

---

## 📝 Notas adicionales

**Cinco decisiones que parecen defectos y no lo son**, cada una con su medición en el design:

1. **No hay castellano para `query_out_of_domain` ni `query_not_in_catalogue`.** El enrutador de intención corre sólo en el modo de consulta libre y las dos rutas de C34 son siempre ancladas: son **inalcanzables** desde esta pantalla. Escribir su copia daría dos pruebas verdes sobre caminos imposibles; en su lugar hay un test que comprueba que caen en la etiqueta neutra.
2. **`size_label_missing` va junto al SKU y no entre los avisos.** Salta en el **58,3 %** de las fichas y está anticorrelacionado con tener familia (4,0 % contra 92,5 %): describe el estado del enriquecimiento, no la pieza. Como alerta canibalizaría a `stock_critical`, que salta en el 3,9 % y sí puede costar una venta. **Se pinta siempre**: el frontend no suprime un código que el backend emitió.
3. **`ai_unavailable` y `not_generated` no comparten mensaje.** En el primero la familia, los materiales y las razones de coincidencia salen del catálogo transaccional y no hay citas; fundirlos haría que la ficha mintiera sobre de dónde sale lo que enseña. Los dos retenidos sí comparten texto, pero siguen distinguibles en el DOM.
4. **El disparador de sustitutos es `hasStock === false` del ancla**, no `pitchStatus`: el primero está presente en todos los estados servidos, el segundo sólo cuando no hubo pregunta.
5. **El bloque de familia no preselecciona nada.** Preseleccionar y confirmar es el patrón que se pulsa sin leer.

**Desviación de convención.** Los componentes llevan `data-testid` de forma extensa, mientras `openspec/project.md` prefiere consultas accesibles (`getByRole`, `getByLabelText`). Los cuatro atributos **de estado** (`data-pitch-status`, `data-outcome`, `data-claim-scope`, `data-anchor`) sí los exige la spec —*«MUST keep all six distinguishable in the rendered document»* cuando dos estados comparten texto, que no se puede afirmar desde el texto visible—, y en el test de los cuatro desenlaces `data-outcome` sólo sirve para esperar el render correcto: la aserción va sobre `textContent`. El `data-testid` indiscriminado es la parte discutible y está anotada como deuda.

**Limitaciones que se declaran y no se cierran.**

1. **La ficha no tiene telemetría.** Abrir, preguntar y elegir variante no dejan rastro, así que su uso **no es medible** y la condición de reactivación de la tarea diferida de `generate=false` no es observable con datos. Abrir la ficha desde la fila **deliberadamente no reporta selección**, porque ver una ficha no es elegir la pieza.
2. **Una pieza que el servicio no puede procesar se ve como «IA no disponible»** en la ruta de asistencia: el cuerpo de la respuesta no los distingue (limitación 3 de C34). En sustitutos **sí** se distinguen.
3. **La pregunta libre sin pieza sigue sin pantalla**, y el rechazo cortés del enrutador tampoco tiene superficie.
4. **La espera de 4 a 8 s no se puede partir** sin tocar el backend: estado de carga desde el primer instante.

**Verificación independiente antes de archivar.** Se pasó `/opsx:verify` sobre el change, con la línea base de la suite regenerada, la cobertura medida por primera vez y dos de las tres mutaciones reproducidas. **No encontró ningún defecto de implementación** y corrigió **dos artefactos del propio change**, los dos en la delta spec y antes de que el archivado los congelara como spec viva:

- El escenario de la entrada de escaneo afirmaba que la ficha *«se abre para el punto de venta de esa venta»*. Es **insatisfacible**: `scan.tsx` no tiene punto de venta —nunca lo ha tenido— y el test afirma exactamente eso. Ahora dice que abre con el selector por rol, y el cuerpo del requisito nombra cuáles de las tres entradas llevan uno.
- El cambio de punto de venta con la ficha servida emite otra petición y tenía test propio, pero **ningún requisito lo amparaba**: el titular decía *«exactly one … per visit»*. Respeta las tres causas que la spec prohíbe —re-renderizar, que llegue la respuesta, que algo falle—, así que no la contradecía; pero no contradecirla no es estar en ella. El requisito pasa a *«… on entry to the card … and only an explicit act issues another»*.

**Para quien revise**, los tres puntos donde mirar primero: el cambio de comportamiento de `scan.tsx`, la guarda `askedForRef` de [assist.tsx](frontend/src/pages/sales/assist.tsx) y el disparador de sustitutos del mismo fichero.



---

<a id="pr-42"></a>
## #42 — feat(ai-search): dar pantalla y ruta propia a la consulta libre

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c40-add-frontend-free-query-panel` → `ai-eng` |
| Creada | 2026-09-25 |
| Integrada | 2026-09-25 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/42 |

### Descripción

## 📋 Descripción

Da pantalla al tercer modo del asistente de venta —la **consulta libre**, sin pieza anclada—, que el servicio sabía responder desde C30b y que no llegaba a ningún operario. El panel de `/sales/new/assisted` gana una segunda ruta, `POST /api/ai/search/assisted`, servida por `FreeQuerySearchService` con interruptor, cupo, presupuesto y circuito **propios**, y un selector que elige entre ella y la búsqueda semántica de C15.

La cadena que bloqueaba ese modo tenía tres eslabones y el que mordía era el tercero: el guard de `AiGatewayClient.AssistSaleAsync()` rechazaba toda petición sin `product_id`. Se retira, y el rechazo queda sólo para una petición **sin ningún ancla** (`AssistSaleAsync_WithNeitherAnchor_ThrowsBeforeAnyRequest`). En el camino se corrigen dos averías que el panel arrastraba desde C16: la ruta degradada **descartaba en silencio** los filtros de categoría y materiales, que ahora aplica con un `JOIN` a `ProductAiProfiles` en `AssistedSearchRepository.SearchLexicalAsync()`, y `aiAvailable` viajaba **dentro** de una respuesta de búsqueda, así que la única forma de saber que una vía estaba apagada era usarla — lo cierra `GET /api/ai/search/availability`, que no llama a la IA y lleva `[DisableRateLimiting]` para que comprobar si puedes buscar no te cueste una búsqueda.

En `jbg-ai`, `assist/v5` prohíbe hablar de precio y disponibilidad en las tres tareas de modo libre y añade una **cuarta**, «sin cobertura»; `retrieval/orchestrator.py` emite una **sonda vectorial sin filtro** para que la abstención se decida sobre un perfil que ningún filtro ha estrechado, de donde sale el sexto código del vocabulario cerrado, `filters_too_narrow`; y `api/auth.py` admite un tercer perfil de claims —un token **sin** `pos_id`— sólo en recuperación y assist. El contrato congelado `ai-service/openapi.json` se mueve **dos veces, por adición pura**.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Change de OpenSpec: **C40 `add-frontend-free-query-panel`**, archivado en este mismo diff en `openspec/changes/archive/2026-09-25-add-frontend-free-query-panel/` con 67 de 67 tareas. Historia: `Documentos/Historias/AI-Eng/HU-AIENG-040.md`, ticket `T-AIENG-040`.

El problema concreto que lo abre no estaba planificado: nace de la tarea 8.5 de C36 —la comprobación en demo— y lo primero que apareció no fue un defecto de C36, sino que **el panel de búsqueda asistida llevaba todo el proyecto sirviendo por su ruta degradada**, porque `AiSearch:EnabledByDefault` no está en ningún `appsettings*.json`, y que **en esa ruta los filtros se descartaban sin decirlo**. La entrada de C36 en `openspec/project.md` cerraba declarando su propia limitación —*«the free query with no piece still has no screen»*—, que es lo que este change retira.

Capabilities afectadas: `ai-free-query-search` **nace** con nueve requisitos; `assisted-search-panel` crece 15→23, `assist-generation` 41→45, `retrieval-abstention` 10→12, `vector-retrieval` 9→11, y `ai-sales-assist`, `ai-service-auth` y `ai-service-api-contracts` una cada una. Total: **28 requisitos añadidos, 8 modificados, 0 retirados**.

---

## 🔄 Cambios realizados

### `backend-api` (9 archivos, +587/−16)

- `AiSearchController.cs`: dos rutas nuevas — `[HttpPost("assisted")]` con `[EnableRateLimiting(RateLimitPolicies.AiFreeQuerySearch)]`, y `[HttpGet("availability")]` con `[DisableRateLimiting]`.
- `FreeQuerySearchDtos.cs`: `FreeQuerySearchResponse` con 16 campos raíz —`groups`, `pitch`, `pitchStatus`, `citations`, `warnings`, `clarificationQuestion`, `intent`, `abstained`, `aiAvailable`, `degradedReason`, `usage`, `searchEventId`, `pointOfSaleId`, `candidatesReturned`, `survivedHydration`, `traceId`— y `FreeQueryUsageDto`.
- `AiSearchAvailabilityResponse.cs`: nuevo.
- `AiCallScope.cs` / `AiCallScopeKind.cs`: tercera clase de ámbito `ForAllPointsOfSale`, con constructor privado y sin centinela. `Catalog` y `AllPointsOfSale` llevan los mismos campos y son dos `Kind` distintos a propósito.
- `AssistedSearchDtos.cs`: `AssistedSearchResultDto.QuantityAtPointOfSale` y `HasStock` pasan a **anulables** (`int?`, `bool?`) — sin tienda no hay existencias que reportar y cero sería falso; `AssistedSearchResponse` gana `Warnings` y `UnappliedFilters`.
- `SalesAssistDtos.cs`: `SalesAssistResponse.DegradedReason`, reenviando el valor que `SalesAssistService` ya calculaba y tiraba.
- `AiAssistSaleDtos.cs`: `AiAssistSaleRequest.Filters`, **no anulable con defecto** (`= new()`), siguiendo el precedente de `AiSubstitutesRequest`.

### `backend-application` (11 archivos, +1013/−60)

- `FreeQuerySearchService.cs`: nuevo. Resolución de ámbito, llamada al assist con filtros, hidratación, telemetría con el origen nuevo, y `Usage` construido **sólo** para administradores. Un fallo de telemetría no rompe la búsqueda.
- `AssistedSearchResultProjector.cs`: nuevo. La regla de **de dónde viene cada campo** —precio, stock, SKU, nombre y foto del catálogo; puntuación, materiales, razones de coincidencia, familia y variante del índice—, extraída para que las dos rutas no dupliquen la proyección.
- `AiFreeQuerySearchOptions.cs` + su extensión de registro: sección `AiFreeQuerySearch`, validada al arranque. Todas las claves con defecto; `EnabledByDefault` es `false`.
- `AiGatewayClient.cs`: retirado el guard que rechazaba la consulta libre; `SearchAsync()` y `AssistSaleAsync()` aceptan `AllPointsOfSale`, `SubstitutesAsync()` sigue exigiendo `PointOfSale`.
- `AssistedSearchService.cs`: pasa los filtros a la ruta degradada y declara un filtro no aplicable.
- `SalesAssistService.cs` / `SubstitutesService.cs`: `degradedReason` al DTO y `?? throw` donde la cantidad existe por construcción, en vez de `?? 0`.

### `backend-domain` · `backend-data` (3 archivos, +191/−14)

- `SearchOrigin.cs`: `AssistedGenerative = 4`. La columna ya era `int`, así que **no hace falta migración**.
- `IAssistedSearchRepository.cs`: `SearchLexicalAsync` con filtros y punto de venta anulable, usando un tipo `AssistedSearchFilters` **propio del `Domain`** — el fragmento del ticket proponía pasar `AiSearchFilters` de `Application`, lo que invertía la dependencia de capas.
- `AssistedSearchRepository.cs`: el `JOIN` a `ProductAiProfiles` y los dos `AND`; sin tienda la consulta **agrupa por producto**, porque sin agrupar un producto que tres tiendas llevan vuelve tres veces y el `ToDictionary` del llamador revienta.

### `ai-service` · `ai-contracts` (27 archivos, +7536/−46)

- `prompts/assist/v5.md`: las tres tareas de consulta libre prohíben precio y disponibilidad, más la **cuarta** tarea «sin cobertura». `PROMPT_VERSION = "assist/v5"` en `assist/constants.py`.
- `assist/verification.py` + `constants.py`: `CAUSE_PLACEHOLDER_IN_FREE_QUERY` como **causa dura**, comprobada sólo cuando `product_id is None`.
- `assist/prompt.py`: `FREE_QUERY_UNCOVERED` como cuarta entrada de `resolve_task`.
- `assist/routing.py` · `orchestrator.py`: coerción a `both` cuando el veredicto es servido, sin eje pendiente y sin índice, con la causa `router_index_absent` en el registro de etapa.
- `retrieval/orchestrator.py` · `ports.py`: la **sonda sin filtro**, secuencial y sólo con filtros presentes; `SearchFilters.is_empty` cuenta los cuatro campos; `narrow_filters` exige `abstention.enabled`.
- `retrieval/projection.py`: `parse_pos_id` separa la **omisión** de la **malformación** — `None` devuelve `None`, una cadena vacía sigue levantando.
- `api/auth.py` · `deps.py`: `UNSCOPED_CLAIMS` como tercer perfil, aplicado sólo a recuperación y assist; un `pos_id` **presente y en blanco** se rechaza.
- `evals/sweep.py`: `CapturedWindow.probe_distances` y la regla viajando **en el fichero** de captura, no leída de `Settings()`. `CAPTURE_VERSION` **no se mueve**.
- `evals/routing.py`: `git_sha()` lee `GIT_SHA` del entorno antes del subproceso.
- `openapi.json`: dos adiciones — `AssistRequest.properties.filters` (referencia a `RetrievalFilters`, ya publicado) y `RetrievalResponse.properties.warnings`.
- `evals/results/c40-*.json`: siete artefactos de medición con `run_id`, `git_sha` y `prompt_version`.

### `frontend` · `frontend-pages` · `frontend-services` (14 archivos, +1695/−23)

- `lib/free-query-states.ts`: `resolveFreeQueryState()` resuelve los **dieciséis estados** como unión discriminada de 10 miembros y no como escalera de comprobaciones de campo, en el orden de la máquina: degradado → los dos rechazos → repregunta → abstención → filtro estrecho → sin ruta → sin prosa → respondida.
- `components/sales/search-route-toggle.tsx` · `ai-availability-badge.tsx`: el selector, con la ruta rápida por defecto y el coste dicho antes de pulsar; la insignia de cuatro estados.
- `components/sales/free-query/free-query-answer.tsx` · `free-query-funnel.tsx`: el render del argumentario, las citas, la repregunta verbatim, y el embudo de administrador con `aiMs` frente a `totalMs`.
- `lib/assist-copy.ts`: copia para los **dos rechazos como textos distintos**, `filters_too_narrow`, los dos estados sin ruta con acción opuesta (`noRouteMessage()` devuelve `action: null` para `unclassified`), y «sin fuente verificable».
- `lib/family-note.ts`: función pura que compone qué otras variantes lleva la familia, degradando a SKU y devolviendo `null` para un grupo de uno.
- `components/sales/assisted-search-result-row.tsx`: **tres** estados de stock y no dos; `hasStock === null` no es «agotado».
- `pages/sales/assisted.tsx`: las dos rutas, y `handleSelect()` atribuyendo la venta en **ambas**.
- `services/ai-search.service.ts` · `types/ai-search.types.ts`: `searchAssisted()` y `getAvailability()` con desenlaces tipados que nunca lanzan y `rate-limited` como miembro propio.

### `openspec` (29 archivos, +3219/−21)

Change archivado y las once delta specs sincronizadas a `openspec/specs/**`, con `ai-free-query-search/spec.md` creada. `openspec/project.md` gana la entrada de C40 y la convención 17 pasa a describir las dos rutas. `DEFERRED_TASKS.md`: dos entradas nuevas y la de C34 agravada.

### `docs` (19 archivos, +3661/−41) · `ai-tooling` (6 archivos, +51/−23)

`README.md` (§1.2, §2.2 y §4, de cuatro endpoints a seis), `Documentos/arquitectura.md`, `modelo-c4.md` (prosa **y** los dos `Component()` del Mermaid), `modelo-de-datos.md` (`SearchOrigin` a cuatro valores), `testing-backend.md` y `testing-frontend.md` (citas fechadas con la rotación medida), los cuatro README de componente y `ai-service/tests/README.md`. Informes: `c40-implementation-measurements.md`, `c40-m1-panel-states.md`, `c40-exploration-decisions.md` y `c40-verify-prompt.md`.

En `ai-tooling`, `CLAUDE.md` y las cinco copias de `config/doc-impact.json` de la skill `update-docs`: el área `frontend-tests` no cubría los tests **colocados** junto al código, así que `Documentos/testing-frontend.md` nunca salía como documento candidato.

---

## 🧪 Testing

**38 archivos de test en el diff (+4677/−87).** Al cierre, y medido:

| Suite | Resultado |
|---|---|
| `ai-service` | **1 625 passed, 0 failed** |
| `frontend` | **113 de 834 en 14 de 57 ficheros** — el mismo conjunto de nombres que la línea base; los 9 ficheros de test de C40, en verde |
| `backend`, área de C40 | **410 de 410**, filtrando `AiCallScope\|AiGateway\|FreeQuerySearch\|AssistedSearch\|SalesAssist\|Substitutes\|ProductSearchEvent\|AiContract` |
| `openspec validate --all --strict` | **62 passed, 0 failed** |
| `tsc --noEmit` filtrado a los ficheros de C40 | **0 errores** |

> Las suites de `backend` y `frontend` **vienen rojas de fábrica** en este repositorio: se comparan por **nombres**, nunca por número. El inventario está en `Documentos/testing-backend.md` y `testing-frontend.md`, actualizados en este diff.

Tests que conviene mirar por lo que fijan, más que por lo que cubren:

- `AiCallScopeTests.cs:120` — `AiCallScope_ExposesExactlyThreeConstructionPaths` comprueba **por reflexión** que hay exactamente tres factorías y ningún constructor público.
- `test_auth.py:316` — `test_a_blank_pos_claim_is_never_read_as_its_absence`: un `pos_id` en blanco da 401 y no «todas las tiendas».
- `test_agent_route.py:390` — `test_the_published_contract_moved_by_addition_only`, hoja a hoja, con **0 retiradas y 0 cambiadas de tipo** y las dos `description` que cambian de valor nombradas una a una.
- `ProductSearchEventSchemaTests.cs:138` — `HasPendingModelChanges().Should().BeFalse()`: el cuarto valor del enum no deja el modelo por delante del esquema.
- `free-query-states.test.ts` — 20 tests sobre la clasificación y no sobre el DOM, porque los tres estados que se pintarían mal están mal en la **resolución**.
- `free-query-funnel.test.tsx:91` — el embudo no muestra importe: comprueba `€`, `EUR`, `$`, «coste» y «precio», no un símbolo.
- `test_probe.py` — la sonda es secuencial (contador de peticiones en vuelo con máximo 1), no cuesta llamada al proveedor, y nada de lo que encuentra llega a la respuesta.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] QA manual de la pantalla con datos reales por alguien que no sea el autor

Notas sobre tres de las casillas:

- **Capas**: el tipo de filtros de `IAssistedSearchRepository` es `AssistedSearchFilters`, del `Domain`, precisamente porque pasar el de `Application` invertía la dependencia. `Documentos/modelo-c4.md` recoge los componentes nuevos.
- **Migración**: el modelo de datos cambia (`SearchOrigin` gana un valor) y **no necesita migración**, lo que fija un test. No hay ningún fichero bajo `Migrations/` en el diff.
- **Cobertura ≥70 %**: marcada por los 38 ficheros de test del diff, no por una medición de cobertura — C40 no la midió. C36 publicó 84–100 % para su código nuevo.

---

## 🚀 Deployment notes

**Sin migración de base de datos, sin dependencias nuevas, sin cambios de infraestructura.** El diff no toca `Migrations/`, `*.csproj`, `package.json`, `pyproject.toml`, `uv.lock`, `terraform/`, `Dockerfile`, `docker-compose.yml` ni `.github/workflows/`.

**Orden de despliegue.** `jbg-ai` **antes** que la API: es el proveedor del contrato y este diff lo mueve. La comprobación con datos reales de la tarea 14.2 lo pagó — la primera pasada dio 6 de 8 porque el contenedor era de antes del grupo 12 y `/v1/assist/sale` todavía exigía `pos_id`, devolviendo `credential_rejected` en 56 ms. Reconstruida la imagen, 8 de 8. Backend y SPA salen juntos en la misma imagen.

**Configuración nueva, toda opcional.** Sección `AiFreeQuerySearch`, que **no existe en ningún `appsettings*.json`** y por tanto toma sus defectos:

| Clave | Defecto |
|---|---|
| `AiFreeQuerySearch:EnabledByDefault` | `false` |
| `AiFreeQuerySearch:EnabledPointOfSaleIds` | `[]` |
| `AiFreeQuerySearch:RateLimitPermitLimit` | `10` por minuto |
| `AiFreeQuerySearch:CandidateWindow` · `DefaultPageSize` · `MaxPageSize` | `5` · `5` · `20` |

Los **tres interruptores están apagados por defecto** —`AiSearch`, `AiSalesAssist` y `AiFreeQuerySearch`— y ninguno figura en `appsettings`. Con ellos apagados la pantalla sirve en degradado; desde este change **lo dice** en vez de callarlo, salvo la ficha de venta, que sigue sin lectura previa. El arranque local está documentado en `backend/README.md` con las tres variables `AiSearch__EnabledByDefault`, `AiSalesAssist__EnabledByDefault` y `AiFreeQuerySearch__EnabledByDefault`.

**Rollback.** Apagar `AiFreeQuerySearch:EnabledByDefault` deja el panel exactamente como estaba: el selector deshabilita su opción asistida con el motivo al lado en vez de fallar al pulsarla. Un despliegue sin `JPV_ASSIST_LLM_API_KEY` es la ablación gratuita — `pitchStatus = not_generated` y el resto de la respuesta intacto. Ninguna de las dos vías necesita revertir código ni datos.

**Post-deploy.** `GET /api/ai/search/availability` con un punto de venta cualquiera: no consume cuota y devuelve los dos interruptores. Y si el corpus importa para la demo, ojo con la limitación de más abajo.

---

## 📝 Notas adicionales

**Ningún breaking change, y el punto que hay que mirar.** Cero campos retirados o renombrados. Dos cambian de tipo, los dos por **ampliación**: `AssistedSearchResultDto.QuantityAtPointOfSale` (`int` → `int?`) y `HasStock` (`bool` → `bool?`), porque en el ámbito «todas las tiendas» no hay existencias que reportar y un cero sería una afirmación que nadie hizo. El único consumidor es el frontend y viaja alineado en el mismo diff (`types/ai-search.types.ts`), con la fila resolviendo **tres** estados en vez de dos. Si algo se revisa de este diff con lupa, que sea esto.

**El contrato congelado se movió dos veces, las dos por adición pura**, y el DoD se verificó hoja a hoja: **0 retiradas, 0 cambiadas de tipo**. Las 2 hojas que cambian de valor son `description` —el vocabulario de avisos ganó su sexto código— y están nombradas una a una en el guardián para que una tercera siga fallando.

**La frontera de autorización es la parte de más riesgo del diff, y este change abrió un agujero y lo cerró.** Hacer `pos_id` opcional en dos rutas significa que el decodificador deja de exigirlo, y **descartaba en silencio un valor inservible**: un `pos_id` en blanco se habría convertido en «todas las tiendas», que es el comodín por accidente que toda la reclamación existe para impedir. La regla que lo cierra: **ausencia es que la clave no esté en el payload; cualquier otra cosa es un valor, y un valor tiene que ser usable.** La propiedad que hace seguro el ámbito global es que la **ausencia** de `pos_id` hace que el prefiltro de disponibilidad **no se aplique**, no que case con todo.

**Tres mediciones refutan lo que el diseño predijo**, y los artefactos viajan en el diff:

| Medición | Predicho | Medido |
|---|---|---|
| Marcadores en el argumentario de M1 | «la mayoría se retirarían» | **2 de 90** y **1 de 90** con `v3`; **0 y 0** con `v5` |
| Latencia p95 extremo a extremo por .NET | al borde de los 10 s | **7 160 ms**, 0 de 42 fuera de presupuesto |
| Tasa de `router_index_absent` | 11,9 % | **0 de 42**, y 0 en 144 réplicas servidas |

La primera cambia la lectura del orden del change: lo que bloqueaba M1 al **100 %** era el guard de la pasarela, no la frecuencia de marcadores. La segunda evitó disparar un corte pre-autorizado — el enrutador **se paga con el trabajo que ahorra**, y un rechazo cuesta la quinta parte que una respuesta. La tercera vacía el estado 4 de la tabla del panel: no es «el 11,9 % de las consultas», es un estado que esta versión del clasificador no produce. La coerción se mantiene porque no cuesta nada y resuelve una contradicción que el esquema admite.

**Tres limitaciones declaradas**, las dos primeras en `openspec/DEFERRED_TASKS.md`:

1. **Una consulta libre de ámbito global no queda registrada.** `ProductSearchEvent.PointOfSaleId` es no nulo, `IsRequired()` e indexado: registrarla exige una migración de EF Core, y la spec prohíbe el marcador de posición. `searchEventId` vuelve nulo y el embudo lo declara. La parte incómoda: su frecuencia **no se puede medir porque no se registran**.
2. **`ForAllPointsOfSale_IsRefusedByInventory` no tiene superficie .NET** donde afirmarse: `IAiGatewayClient` no tiene operación de inventario. La garantía vive en Python (`test_pos_scoped_route_still_rejects_it`) y del lado .NET queda un centinela que afirma que la operación no existe, para que falle el día que crezca.
3. **El corpus de conocimiento no viaja en la imagen de `jbg-ai`**, y la tarea diferida de C34 **se agrava**: `CORPUS_DIR` se deriva de `REPO_ROOT`, que dentro del contenedor resuelve a `/app/.venv/lib`, así que copiar `data/knowledge` no basta — hace falta además que la ruta deje de derivarse de la posición del paquete. Un contenedor recién creado no puede indexar nada, y en ese estado M1 responde siempre **sin citas**.

**Una nota sobre el propio proceso, por si ayuda a quien revise.** Una pasada de verificación independiente encontró una **cuarta infracción de completitud** del mismo tipo que las tres que el change vino a corregir: `FreeQuerySearchResponse.searchEventId` se persistía y no se usaba, porque `handleSelect()` resolvía el identificador con `state.kind === 'answered'` — sólo la ruta semántica—, así que una pieza encontrada por consulta libre llegaba a la caja sin evento detrás y la mitad de la ablación del selector quedaba sin medir. Corregido en los tres sitios, con dos tests. La misma pasada encontró dos afirmaciones falsas en el informe del change y restauró una garantía que el sync de specs había retirado en silencio. Está todo en el commit `44c05a1` y en el §11 del informe.

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-43"></a>
## #43 — fix(sales): hacer alcanzable el ambito de todas las tiendas

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c40-fix-all-shops-scope-unreachable` → `ai-eng` |
| Creada | 2026-09-26 |
| Integrada | 2026-09-26 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/43 |

### Descripción

## 📋 Descripción

C40 construyó el ámbito «todas las tiendas» completo —tercera clase de `AiCallScope`, tercer perfil de *claims*, autorización abierta a los dos roles, DTO anulables, hidratación agrupada por producto y una fila de resultado con tres estados— y **no dejó ningún control para entrar en él**. El selector del panel no ofrecía la opción, el efecto de carga fijaba la primera tienda activa y la búsqueda no se disparaba sin tienda, así que ese tramo de código **no se ejecutó nunca en la aplicación real**. Esta PR lo hace alcanzable y corrige las specs vivas que, mientras tanto, afirmaban lo contrario de lo que el sistema hacía.

El cambio toca tres piezas y no una. En el **backend**, `GET /api/ai/search/availability` pasa a responder de un *ámbito* en vez de un punto de venta, y el predicado del interruptor se extrae a `AiScopeSwitchExtensions` para que la sonda y la ruta de búsqueda no puedan resolver la ausencia de tienda con reglas distintas. En el **frontend**, el selector ofrece «Todas las tiendas» al administrador, el ámbito fija la ruta asistida —porque `POST /api/ai/search` sigue exigiendo punto de venta y responde 400 sin él— y cinco cadenas de copia se eligen por ámbito, porque «en esta tienda» cuando no hay tienda es una afirmación falsa. En **`openspec/specs/`**, cuatro enunciados que habían dejado de ser verdad se retiran.

La rama incluye además una **verificación independiente posterior a la implementación**, que refutó cinco afirmaciones de los propios artefactos del change y encontró un defecto de producción que la implementación había introducido. Ambas cosas están corregidas en el diff y documentadas, no sólo anotadas.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec:** `openspec/changes/archive/2026-09-26-c40-fix-all-shops-scope-unreachable/` (38/38 tareas, archivado en esta misma rama), con `proposal.md`, `design.md`, `tasks.md`, `ticket.md` y `qa.md`.
- **HU:** [`Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md`](Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md).
- **Capabilities afectadas:** `assisted-search-panel` (23 → 25 requisitos) y `ai-free-query-search` (1 requisito modificado).

El problema no era un bug de implementación sino **un estado especificado sin camino hasta él**. Los 136 escenarios de C40 salieron verdes porque los tres del panel están condicionados con *«WHEN the search is scoped to every point of sale»*: describen qué hace la pantalla **estando** en ese estado y ninguno exige que ofrezca la forma de entrar. Y la spec viva no callaba, contradecía al sistema: `assisted-search-panel` afirmaba *«The panel SHALL send a concrete point of sale on every search»*, falso desde C40, con `openspec validate --all --strict` en verde por encima porque valida estructura y no verdad.

---

## 🔄 Cambios realizados

### `backend-api` (2 archivos, +43/−6)

- **`AiSearchController.cs:Availability()`** pasa de `[FromQuery] Guid` a `[FromQuery] Guid?`. Omitir el parámetro es el ámbito global; `Guid.Empty` sigue siendo 400, con el texto de la ruta de consulta libre («El punto de venta no es válido. Omítelo para consultar todas las tiendas.»).
- **La misma guarda rechaza además un valor que no parsea.** `Guid?` se queda a `null` ante una cadena vacía, espacios, un identificador ilegible o un GUID truncado, y `null` es ahora un *significado* —«todas las tiendas»— en vez de un campo ausente; `SuppressModelStateInvalidFilter` está activado globalmente (`ServiceCollectionExtensions.cs:69`), así que nada más lo rechaza. La guarda comprueba `Request.Query.ContainsKey(nameof(pointOfSaleId))`, de modo que la clave presente sin un valor usable es 400.
- **`AiSearchAvailabilityResponse.PointOfSaleId`** pasa a `Guid?`, documentado como **nulo y nunca `Guid.Empty`**.

### `backend-application` (4 archivos, +88/−15)

- **`Configuration/AiScopeSwitchExtensions.cs` (nuevo)**: `IsEnabledForScope(this <opciones>, Guid?)` para `AiSearchOptions`, `AiFreeQuerySearchOptions` y `AiSalesAssistOptions`. Sin tienda resuelve a `EnabledByDefault` — la lectura estrecha: *un despliegue que habilita la función tienda a tienda no la ha habilitado para «todas ellas»*.
- **`AssistedSearchService.cs:GetAvailability(Guid?)`** consume el predicado extraído en los tres interruptores. `SemanticSearchAvailable` se sigue reportando con su predicado normal: la ruta rápida no acepta este ámbito, pero eso es **alcanzabilidad** y no un interruptor, y devolver `false` afirmaría que la búsqueda semántica está apagada, que es otra cosa y es falsa.
- **`FreeQuerySearchService.cs`** retira su `IsEnabled` privado y llama al extraído, para que la ruta y la sonda no puedan derivar.
- **`IAssistedSearchService.cs`** actualiza la firma a `Guid?` con su documentación.

### `frontend`, `frontend-pages`, `frontend-services` (5 archivos, +234/−27)

- **`assisted.tsx`**: centinela `ALL_POINTS_OF_SALE` local al módulo, opción «Todas las tiendas» **la primera** de la lista y sólo para `isAdmin`; `scopedPointOfSaleId` traduce el centinela a **ausencia** antes de cualquier petición; `effectiveRoute` es **derivada y no estado**, para que salir del ámbito devuelva al operario la vía que había elegido; el `payload` **omite la clave** con un *spread* condicional en vez de enviarla vacía; línea de consecuencia y aviso de callejón sin salida (`data-testid` `assisted-scope-consequence` y `assisted-scope-dead-end`).
- **`search-route-toggle.tsx`**: `semanticUnavailableReason` deshabilita la vía rápida con un **motivo de ámbito** —«La búsqueda rápida trabaja sobre una tienda concreta»— y nunca con el del interruptor.
- **`ai-availability-badge.tsx`**: tabla de copia aparte (`UNAVAILABLE_REASONS_ALL_SHOPS`) para que ningún texto diga «en esta tienda» cuando no hay tienda.
- **`ai-search.service.ts:getAvailability()`** acepta la ausencia y **omite el parámetro** en vez de enviarlo en blanco.
- **`ai-search.types.ts`**: `pointOfSaleId` opcional en `AssistedSearchRequest` y `FreeQuerySearchRequest`; `AiSearchAvailability.pointOfSaleId` admite `string | null`.

### `openspec` (12 archivos, +2142/−9)

- Change archivado en `openspec/changes/archive/2026-09-26-…/`.
- **`openspec/specs/assisted-search-panel/spec.md`**: 23 → **25** requisitos. Los dos `ADDED` van colocados por sentido —el del control junto al requisito de ámbito cuyo estado describe, el del selector de vía junto a los otros dos del mismo selector— y los tres `MODIFIED` reemplazan a su contraparte en el sitio que ocupaba.
- **`openspec/specs/ai-free-query-search/spec.md`**: el requisito de la sonda, modificado.
- **Cinco enunciados dejan de ser falsos**: los tres `SHALL` del panel, el «for one point of sale» de la sonda y —encontrado sólo al sincronizar— el `## Purpose` de `assisted-search-panel`, que resumía la capability con la misma frase que el change retira.
- **`openspec/DEFERRED_TASKS.md`**: dos entradas. La extensión de la ruta rápida al ámbito global **con la agrupación de `SearchLexicalAsync` como prerrequisito obligatorio** (su rama nula es un `ArgumentException` → 500 dormido, porque acepta `Guid?` sin agrupar por producto mientras `BuildResultsAsync` hace `rows.ToDictionary(row => row.ProductId)` incondicionalmente); y la divergencia sonda/ruta descrita más abajo.
- **`openspec/project.md`**: entrada de C40_FIX en la lista por change.

### `docs` (9 archivos, +512/−10)

- **`Documentos/testing-frontend.md`** retira una frase falsa: decía que «la puerta real es `npm run build`». Vite transpila con esbuild, que descarta los tipos sin comprobarlos — medido sobre este árbol, `npm run build` sale **0** y `tsc --noEmit` sale **2 con 176 errores**.
- **`Documentos/modelo-c4.md`** y **`README.md` §4** dejan de describir la sonda como «los dos interruptores **de un punto de venta**».
- **`Documentos/testing-backend.md`**: entrada por change, y una sección nueva porque `coverlet` **no instrumenta `JoiabagurPV.Application`** en este repositorio (el informe sale sin ese paquete, sin error y sin aviso), con causa y apaño. Avisado también en **`backend/README.md`** junto al propio comando.
- **`Documentos/epicas.md`**: recuento al día (39 archivadas, 2 pendientes) y corrección de la afirmación de que el `[Theory]` del change comparaba el veredicto de la sonda contra el de la ruta.
- **`frontend/README.md`** documenta el ámbito global y las tres reglas que no hay que romper al tocar el panel; **`Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md`** y **`Documentos/Historias/AI-Eng/HU-AIENG-040-FIX.md`** quedan al día de recuento y de enlaces al árbol de archivo.

### `misc` (1 archivo, +14)

- **`compose.demo.yaml`** declara `AiFreeQuerySearch__EnabledByDefault: "true"`, que faltaba desde C40. Sin ella, en la demo la sonda respondía `switched_off` para **todas** las tiendas y el panel generativo de C40 estaba apagado en el entorno cuyo único trabajo es enseñarlo. Es **prerrequisito y no mejora**: el ámbito global lo sirve la ruta asistida en solitario.

---

## 🧪 Testing

**33 casos nuevos** en el diff: 18 en backend y 15 en frontend.

| Archivo | Casos | Tipo |
|---|---:|---|
| `UnitTests/Application/AssistedSearchServiceTests.cs` | 8 | unitario (uno es `[Theory]` de 4 casos) |
| `UnitTests/Application/AiScopePredicateAgreementTests.cs` (nuevo) | 4 | unitario, sonda **y** ruta sobre las mismas opciones |
| `IntegrationTests/AiSearchControllerTests.cs` | 6 | integración con Testcontainers (uno es `[Theory]` de 4 casos) |
| `pages/sales/__tests__/assisted.test.tsx` | 14 | página, con `vi.mock` de los servicios |
| `services/ai-search.service.test.ts` | 1 | servicio |

**`AiScopePredicateAgreementTests` existe porque el test que la implementación escribió para su invariante central era tautológico.** `GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate` calcula el valor esperado con los mismos métodos de extensión que usa la sonda y **nunca invoca `FreeQuerySearchService`**: se comprobó con tres mutaciones compiladas y ejecutadas, y sigue en verde tanto al invertir la rama nula del predicado compartido como al reescribir la ruta con otra regla para la ausencia. La clase nueva construye las dos piezas sobre los mismos objetos de opciones, **ejecuta la ruta** y compara veredictos; caza las tres mutaciones.

**Cobertura del código nuevo** (medida, no estimada): `AiScopeSwitchExtensions` 100 %, `AssistedSearchService.GetAvailability` 100 %, `AiSearchAvailabilityResponse` 100 %, `AiSearchController.Availability` 87,5 % (las dos líneas sin cubrir son la guarda `Unauthorized`, inalcanzable tras `[Authorize]`); en frontend `assisted.tsx` 93,7 %, `ai-availability-badge.tsx` 94,1 %, `search-route-toggle.tsx` 83,3 % y `ai-search.service.ts` 100 %. Requiere el apaño de `coverlet` documentado en `Documentos/testing-backend.md`, porque el comando por defecto no instrumenta `Application`.

**Suites comparadas por nombres contra línea base propia**, que es el criterio de este repositorio: backend **51 de 1.339 → 53 de 1.347**, y los **doce nombres que difieren están los doce en `InventoryIntegrationTests`**, la clase que `CLAUDE.md` documenta como no determinista; frontend **113 de 848 en 14 ficheros** —pasada completa tomada antes de añadir el test de servicio, así que el total actual es 849—, donde la pasada de la implementación midió 114 en 15 sobre el mismo commit: rotación conocida de `family-review.test.tsx`, tercera observación independiente del mismo nombre. **Cero rojos en el área propia** en las dos suites. `openspec validate --all --strict` en **0 failed**.

**Verificado contra la aplicación levantada**, con los dos roles y proveedor real: la opción sólo la ve el administrador (comprobado también con un operario creado con **dos** tiendas, para que la ausencia de la opción no se debiera a que el selector se oculta con una sola asignación); el `POST` sale **sin la clave** `pointOfSaleId`; las filas no muestran cifras, no nombran tienda, no duplican producto y deshabilitan la ficha; cambiar de ámbito no emite búsqueda; y la ruta **sí** sirve el ámbito a un operario (200 con cantidades nulas) mientras rechaza una tienda no asignada (403).

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` — `Domain` e `Infrastructure` sin tocar, el predicado en `Application/Configuration`, el controlador en `API`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — cifras medidas en la sección de Testing
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**: ninguna entidad, columna ni índice cambia; el diff no toca `JoiabagurPV.Domain/Entities/**` ni `Migrations/**`
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**: `ai-service/` no aparece en el diff; el tercer perfil de *claims* de C40 ya acepta un token sin `pos_id`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `0 failed`
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff — lo único nuevo en `compose.demo.yaml` es un booleano
- [x] Revisado el impacto en otros componentes del monorepo — ver «Notas adicionales»

---

## 🚀 Deployment notes

**Una variable de entorno nueva, y sólo en la demo.** `compose.demo.yaml` declara `AiFreeQuerySearch__EnabledByDefault: "true"`. **No es obligatoria**: la propiedad tiene default `false` y `EnabledPointOfSaleIds` vacía, así que un entorno sin ella arranca igual — pero el ámbito global queda **seleccionable y no buscable**, con su motivo en pantalla. En producción el interruptor se gobierna como los otros dos, por SSM `/jpv/prod/*`, y esta PR no lo da de alta allí.

**Sin migración de base de datos** y **sin cambio en `ai-service/openapi.json`**, así que no hay orden de despliegue que respetar entre componentes. Backend y SPA viajan en la misma imagen y salen juntos; `jbg-ai` no cambia.

**Rollback en tres niveles, ninguno exige revertir código:**

1. Apagar `AiFreeQuerySearch__EnabledByDefault` → el ámbito global queda seleccionable y no buscable, con su motivo enunciado; el resto del panel se comporta como antes.
2. Retirar la opción del selector → estado previo a esta PR, exactamente. Ojo: el ámbito vuelve a ser inalcanzable **y las specs vuelven a mentir**, así que un rollback de código debe revertir también las deltas.
3. Contrato: `AiSearchAvailabilityResponse.PointOfSaleId` anulable es **adición de tolerancia** — un cliente que leía un valor sigue leyéndolo cuando hay tienda.

---

## 📝 Notas adicionales

**Breaking changes: ninguno.** `pointOfSaleId` pasa de obligatorio a opcional en la sonda, lo cual relaja un requisito; el DTO de respuesta se amplía a anulable y el único consumidor —el panel— viaja en el mismo diff con sus tipos actualizados. Respecto a `ai-eng`, los cinco valores inservibles del parámetro siguen respondiendo **400** igual que antes. Un detalle para quien dependa del cuerpo del error: el texto del 400 cambia de «El punto de venta es obligatorio.» a «El punto de venta no es válido. Omítelo para consultar todas las tiendas.» — ningún consumidor del repositorio compara ese literal.

**Riesgo: medio.** Lógica nueva en `Application/Services` y un predicado compartido por dos servicios. No toca autenticación, `JoiabagurPVDbContext`, entidades, `Program.cs`, migraciones ni `terraform/`.

**Control de acceso por punto de venta: intacto y comprobado.** El recorte al administrador es **de pantalla y no de autorización**, y el requisito lo dice explícitamente para que nadie endurezca el backend «por simetría»: la ruta sigue sirviendo el ámbito a operarios, y la frontera que de verdad se protege —no poder **nombrar** una tienda no asignada— se verificó contra la API viva (403). `isAdmin` en el cliente no es una frontera de seguridad y el código lo documenta como tal.

**Dos puntos para reviewers, los dos anotados en `DEFERRED_TASKS.md` y no resueltos aquí:**

1. **La sonda es más estricta que la ruta que describe.** `GetAvailability` reporta la bandera generativa como `AiFreeQuerySearch && AiSalesAssist`, mientras `FreeQuerySearchService` no lee `AiSalesAssistOptions` en ningún punto. Con la consulta libre encendida y la ficha de venta apagada, la sonda responde `switched_off` de un ámbito que la ruta sirve con prosa generada —medido por HTTP—, y en pantalla eso deshabilita **las dos** vías y escribe un motivo falso. Es comportamiento heredado de C40, no introducido aquí, pero **el requisito que esta PR escribe lo prohíbe**. Qué lado está mal es decisión de producto, con coste en las dos direcciones; la respuesta de hoy queda fijada por `Probe_AlsoReportsTheSaleCardSwitch_WhichTheRouteNeverApplies` para que quien la cambie pase por ahí.
2. **`SearchLexicalAsync` tiene un HTTP 500 dormido.** Acepta `Guid?` y suelta el filtro de tienda, pero **no agrupa por producto** como sí hace `HydrateAsync`, y `BuildResultsAsync` hace `ToDictionary(ProductId)` incondicionalmente en las dos ramas. Hoy es código muerto —su único llamante pasa siempre una tienda concreta— y se activaría al extender la ruta rápida al ámbito global, **primero en desarrollo local**, donde la ruta degradada es la que corre. El orden obligatorio está escrito: primero la agrupación y su test, después el DTO.

**Deuda declarada que esta PR no cierra:** una búsqueda de ámbito global **no se registra en telemetría** —la columna exige punto de venta y la spec prohíbe una falsa—, así que su uso no es medible; el recorte al administrador lo vuelve marginal. Y la **demo desplegada no se levantó**: el interruptor está en el compose y hace lo que dice en local, pero no se comprobó allí.

**Sin `TODO`/`FIXME`/`HACK` nuevos** en el diff.



---

<a id="pr-44"></a>
## #44 — C41: la proyeccion de disponibilidad se drena sola al arrancar y cada 600 s

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c41-add-pos-projection-scheduled-drain` → `ai-eng` |
| Creada | 2026-09-26 |
| Integrada | 2026-09-26 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/44 |

### Descripción

## 📋 Descripción

`ai.pos_projection` es la copia del surtido por punto de venta que el prefiltro de recuperación lee para acotar los candidatos a lo que esa tienda lleva. Hasta ahora se drenaba con `python -m jbg_ai.indexing sync-pos`, un comando que alguien tenía que acordarse de ejecutar. **Esta PR le da dueño**: `jbg-ai` drena el feed **al arrancar el proceso** —completo si no hay *checkpoint*, incremental si lo hay— y después **cada 600 s**, tomando un *advisory lock* no bloqueante. La edad resultante llega a `GET /health` y de ahí a la tarjeta de estado del administrador, y `deploy/demo/verify.sh` gana una quinta condición de fallo.

**No es una fuga de datos y conviene fijarlo antes de revisar**: la frontera de visibilidad es `Carried()` en .NET, que parte de `Inventories` y corre en toda respuesta. Un operario nunca ve una pieza que su tienda no lleva, pase lo que pase con la proyección. Lo que la rancidez causa es que **la página llegue corta** —el comportamiento anterior a C22—, y degradar ante una proyección rancia sigue siendo la decisión correcta: esta PR **no la toca**.

**El contrato congelado no se mueve.** `ai-service/openapi.json` no aparece en el diff: mismo `sha256` antes y después, ninguna ruta nueva bajo `/v1`, y `test_openapi_snapshot_is_stable` pasa sin regenerarlo. Tampoco hay migración de Alembic ni de EF Core.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

Change de OpenSpec **C41** `add-pos-projection-scheduled-drain`, archivado en `openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/`. Historia [HU-AIENG-041](Documentos/Historias/AI-Eng/HU-AIENG-041.md), épica **EP14**.

**Tres incidentes registrados, dos modos de fallo distintos:**

| # | Cuándo | Modo | Efecto |
|---|---|---|---|
| 1 | C34 (demo) | Proyección **vacía** | `count_scope = 0` → **503 en toda recuperación**. .NET degrada correctamente a léxico con 200, así que desde fuera el entorno parece sano |
| 2 | C40 | **Rancia**, 19,7 días | El ámbito se cae y la página llega corta |
| 3 | C41 | **Rancia**, 20 días | Ídem |

**La causa no era falta de disciplina.** El único planificador que existía vivía en `ai-service/README.md` como receta de cron, y empezaba por `cd /srv/jbg-ai` —una ruta de host— contra un servicio que se despliega en contenedor. Describía un despliegue que no existe; por eso nunca se instaló.

**Y los dos incidentes locales ocurrieron levantando el entorno para probar**, no en régimen permanente. De ahí que el disparo de arranque sea la parte que importa: un intervalo deja una ventana abierta justo cuando se mide, y un cron de host no corre en el portátil de nadie.

---

## 🔄 Cambios realizados

### `ai-service` — 9 archivos (+765/−35)

**Nuevo · `indexing/drain_lock.py`.** `PostgresAdvisoryLock` sobre `pg_try_advisory_lock`, **no bloqueante**, con clave constante documentada `POS_DRAIN_LOCK_KEY = (41, 1)` y liberación explícita en la misma conexión. Incluye `AlwaysAvailableLock` como costura de test y `log_declined()`.

**Nuevo · `indexing/pos_drain.py`.** `run_pos_drain()` construye feed, repositorio y lock. **Existe como módulo propio y no como función de `cli.py`** para que el planificador no arrastre `LiteLlmEmbeddingClient` —y con él el SDK del proveedor— al grafo de importación del *app factory*.

**Nuevo · `indexing/scheduler.py`.** `scheduler_should_run()` (conmutador, no `STUB_MODE`, feed configurado), `drain_once()` que **nunca propaga excepciones**, `_boot_drain()` con retroceso acotado `(5, 15, 45)` s, y `run_scheduler()`.

**Nuevo · `api/lifespan.py`.** `build_lifespan()` crea la tarea **sin esperarla** y la cancela al apagar.

**Modificado · `indexing/pos_orchestrator.py`.** `sync_pos_availability()` acepta `lock` y toma el bloqueo **dentro del drenaje**; el bucle de páginas se extrae a `_drain()` sin cambiar su lógica. `PosSyncResult` gana `declined: bool`, y `describe()` distingue en palabras un drenaje declinado de uno vacío.

**Modificado · `indexing/cli.py`.** `run_cli_sync_pos()` pasa a delegar en `run_pos_drain`. El código de salida gana **75** (`EX_TEMPFAIL`) para «otro drenaje tiene el lock»: declinar no es fallar, y devolver 1 haría que un envoltorio de cron alertara por un sistema sano.

**Modificado · `api/health_report.py`.** `IndexSnapshot` gana cinco campos de proyección, leídos **en la misma sesión** que los dos existentes para que el informe siga costando una conexión. `build_projection_section()` compone `status` / `synced_at` / `full_synced_at` / `age_seconds` / `ceiling_seconds` / `stale` / `failed_pages` / `points_of_sale` / `shops_without_scope`. La edad sale de `ai.sync_checkpoint.last_incremental_sync_at` y **nunca** de `ai.pos_projection.refreshed_at`.

**Modificado · `config/settings.py`.** `JPV_POS_SYNC_SCHEDULER_ENABLED` (defecto `true`) y `JPV_POS_SYNC_INTERVAL_SECONDS` (defecto `600`), con el patrón `blank_*_is_default`. Ninguno se fija en `canonical_openapi_settings()`.

**Modificado · `api/main.py`.** Dos líneas: importa `build_lifespan` y lo pasa al constructor de `FastAPI`.

### `backend-api` — 1 archivo (+71/−0)

`AiHealthResponse.cs` gana `AiHealthProjection? Projection`, **anulable**, y la clase que la describe con sus ocho propiedades también anulables. Un `jbg-ai` anterior a este change no emite la sección, y un DTO que fallara por su ausencia convertiría un desfase de versiones en un dashboard roto.

### `frontend-services` y `frontend-pages` — 2 archivos (+170/−1)

`ai-health.types.ts` añade `AiHealthProjectionStatus` y `AiHealthProjection`, con `projection?` opcional en `AiHealthReport`.

`AdminDashboard.tsx` pinta tres estados —al día, desactualizada, sin sincronizar nunca— más la línea de tiendas sin ámbito y el recuento de páginas con error, con `describeProjectionFreshness()` para la edad en lenguaje natural y el valor exacto en el `title`. **La copia avisa de completitud, no de corrección**: «pueden devolver menos resultados de los disponibles» es cierto; «no son fiables» sería falso, porque el backend sigue aplicando la verdad al hidratar. El bloque sólo se renderiza cuando el servicio reporta la sección.

### `scripts` — 1 archivo (+41/−1)

`deploy/demo/verify.sh` gana la **quinta condición de fallo**: una proyección sin ninguna fila asignada falla el despliegue. Tolerante a un `jbg-ai` antiguo que no reporte la sección.

### `openspec` — 15 archivos (+2060/−15)

Los cuatro artefactos del change más `qa.md`, movidos al archivo. Las tres deltas sincronizadas: `pos-projection` pasa de 11 a **14** requisitos —el `MODIFIED` retira la cláusula `MUST NOT start an in-process scheduler or background task` y escribe en la propia spec la refutación de las tres razones que C22 dio para ponerla—, y `ai-service-runtime` y `demo-deployment` conservan su número.

El `## Purpose` de `pos-projection` decía «No route under `/v1`, no scheduler, no EF Core migration»; sigue sin haber ruta ni migración, pero el planificador ya existe, así que se reescribió. `DEFERRED_TASKS.md` cierra la entrada de C34.

### `docs` y `ai-tooling` — 13 archivos (+1256/−26)

`ai-service/README.md` sustituye la sección «There is no route and no scheduler, on purpose» y **conserva la receta de cron marcada como inservible**, con la explicación de por qué no podía funcionar. `modelo-c4.md` añade la responsabilidad del drenaje y **corrige el recuento de endpoints de 10 a 11** —desfase que venía de C32b y que esta rama no causa—. `openspec/config.yaml`, `openspec/project.md`, `epicas.md`, la ficha del plan, `deploy/demo/README.md`, `ai-service/tests/README.md` y el §6.3 del diseño RAG quedan al día. `README.md` §1.1 gana el párrafo de C41.

`CLAUDE.md` documenta la trampa del *heredoc*: un documento de 37 KB no cabe en la línea de comandos de Windows (32.767 caracteres) y el error `ENAMETOOLONG: name too long, uv_spawn` no dice lo que pasa.

Además se anota el §8 del informe de C40 — su manipulación del entorno se aplicó a `refreshed_at` cuando el guard lee el *checkpoint*, así que **su reparto de estados describe el sistema degradado**. Ninguna de sus cifras se modifica.

---

## 🧪 Testing

**+24 tests en `ai-service`** (1.625 → **1.649 passed, 0 failed**):

- `tests/indexing/test_pos_scheduler.py` — **17 nuevos**. Seis del lock (declina sin escribir nada, se libera también cuando el drenaje lanza, un drenaje real siempre construye uno, la clave es constante y no `hashtext`) y once del planificador (las cuatro condiciones de arranque, que una excepción nunca escapa, el retroceso acotado, y que el modo completo se deriva del cursor ausente).
- `tests/api/test_health_report.py` — **6 nuevos**: la edad desde el checkpoint, que una proyección rancia **no degrada el estado global**, la tienda sin surtido, `never_drained` distinguido de `stale`, las páginas fallidas, y que la sección viaja aun con la base inalcanzable.
- `tests/indexing/test_embeddings.py` — **1 nuevo**, `test_lifespan_reaches_the_drain_without_the_provider_sdk`, que extiende al fichero nuevo el guardián que este change estuvo a punto de eludir.
- `tests/support/fake_health_probe.py` — el doble acepta los cinco campos nuevos.

**+5 tests en frontend**, en `ai-service-status.test.tsx` (**9/9 en verde**): la edad en pantalla, el aviso de completitud y **no** de fiabilidad, las tiendas sin ámbito, `never_drained`, y que la tarjeta se renderiza intacta cuando el servicio no reporta la sección.

**Backend: sin tests nuevos, y es lo correcto** — el cambio es una propiedad anulable en un DTO que ningún test referencia. `AiGatewayHealthTests` (4) y `AiHealthControllerTests` (3) siguen **7/7 en verde**.

**Suites completas** *(comparadas por nombres, no por recuento, según `CLAUDE.md`)*:

| Suite | Base | Cierre |
|---|---|---|
| `ai-service` | 1.625 · 0 fallos | **1.649 · 0 fallos** |
| `backend` | 45 de 1.329 | **48 de 1.347**, 9 nombres discrepantes y **8 en `InventoryIntegrationTests`** |
| `frontend` | 119 en 17 ficheros | 114-119 en 15-18 · **ningún fichero del área propia** |

El registro completo de QA está en `openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/qa.md`, con seis incidencias que el implementador se abrió a sí mismo.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%)
- [x] Migración de EF Core incluida si cambia el modelo de datos — **no aplica: ninguna migración**
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica: el contrato no se mueve**, mismo `sha256`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — **62 passed, 0 failed**
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] Verificación independiente del change — **pendiente**, ver notas

---

## 🚀 Deployment notes

**Dos variables nuevas, las dos opcionales y con defecto seguro:**

| Variable | Defecto | Efecto |
|---|---|---|
| `JPV_POS_SYNC_SCHEDULER_ENABLED` | `true` | A `false` restaura exactamente el comportamiento anterior: el CLI como único drenaje. Es la ablación y el *rollback* |
| `JPV_POS_SYNC_INTERVAL_SECONDS` | `600` | **Derivado, no elegido**: `techo / intervalo ≥ 4` sobre los 3.600 s de `JPV_POS_PROJECTION_MAX_AGE_SECONDS`, de modo que caben cinco drenajes fallidos seguidos antes de que el guard degrade el ámbito |

**Ninguna hace falta exportar**: no declararlas deja los defectos, que son los valores medidos.

**Sin migraciones** —ni Alembic ni EF Core—, **sin cambios en el contrato** y **sin reindexar**.

**Al desplegar, `jbg-ai` drenará solo.** En un entorno nuevo el drenaje de arranque corre **completo**, que es lo que cura una proyección vacía. `verify.sh` **fallará el despliegue** si la proyección sigue sin filas asignadas — comportamiento nuevo y deliberado: hasta ahora ese entorno pasaba la verificación.

**El orden de despliegue no importa**, pero conviene saberlo: si `jbg-ai` sube antes que la API .NET, el drenaje de arranque fallará y reintentará con retroceso acotado hasta que el feed responda. Eso es diseño, no avería.

**Rollback:** `JPV_POS_SYNC_SCHEDULER_ENABLED=false` y reiniciar el contenedor. Nada que deshacer en base de datos.

### Acoplamientos del monorepo, revisados

| Frontera | Estado |
|---|---|
| **backend ↔ frontend** | El DTO `AiHealthProjection` y los tipos TypeScript **viajan en esta misma PR**; no queda desajuste |
| **backend ↔ `jbg-ai`** (JWT interno HS256) | **Sin tocar.** Ningún *claim* cambia. El drenaje se autentica contra el feed con `X-Index-Feed-Key`, como ya hacía el CLI |
| **`ai-service/openapi.json`** | **Sin diff.** El dominio `ai-contracts` no aparece en el manifiesto, y `GET /health` declara su retorno como *mapping* abierto desde C17, que es lo que permite enriquecerlo a coste cero |
| **Migraciones EF Core** | Ninguna: el orden de despliegue no queda condicionado |
| **Código ↔ especificación** | Las tres capabilities están sincronizadas y el change archivado en la misma rama |

---

## 📝 Notas adicionales

**Sin breaking changes.** `AiHealthProjection` es anulable en .NET y opcional en TypeScript, así que un `jbg-ai` anterior a este change sigue funcionando contra esta API y contra esta tarjeta.

**Tres decisiones que se apartan de lo que el ticket pedía**, con su razón:

1. **El drenaje se queda en `jbg-ai`** y no pasa a un `BackgroundService` de .NET. Lo que el ticket pedía no es un planificador sino **una segunda implementación del protocolo del keyset**; como la spec obliga a conservar el CLI, quedarían dos drenadores sobre la misma fila de `ai.sync_checkpoint`. Además .NET tendría que escribir `ai.*`, frontera que `migrations/bootstrap.sql` hace estructural por *grants*.
2. **La edad va en `GET /health`** y no en `GET /api/ai/search/availability`, que tiene un `MUST` de spec viva prohibiéndole llamar al servicio de IA y cuyo método es síncrono.
3. **El lock va dentro del drenaje**, no en el planificador, o el CLI corrido a mano —que es como se reparó las tres veces— queda sin cubrir.

**Lo que esta PR deliberadamente no trae:** botón de refresco (ni para el operario ni para el administrador), insignia de frescura en la pantalla del operario, y cambios en `Carried()` o en la decisión de degradar.

**Puntos de atención para quien revise:**

- **Un test existente cazó el primer diseño**, que importaba `jbg_ai.indexing` desde `api/main.py` y arrastraba el SDK del proveedor al *app factory*. Se arregló por arquitectura —dos módulos nuevos— y **el guardián se extendió al fichero nuevo** en vez de dejar el hueco abierto. Merece una mirada: sacar el `lifespan` a otro fichero habría satisfecho la letra del test original y roto su propósito.
- **`openspec validate --all --strict` valida estructura, no verdad.** Daba 0 failed mientras una delta se dejaba cinco escenarios que al sincronizar habría borrado de la spec viva. Se detectó al escribir el QA y está corregido, pero la lección aplica a cualquier revisión de deltas.
- **Un hallazgo real que no es de este change:** `GET /health` reporta `shops_without_scope: 1` contra el entorno local. El punto de venta `cd9bfd1f…` tiene **0 filas asignadas sobre 144** y responde 503 a toda recuperación con ámbito desde C34. Es la primera vez que aparece reportado.

**Deuda declarada:**

- `ai.sync_failure` sigue sin lector automático. Las páginas fallidas se cuentan y se reportan en `/health`; recuperarlas sigue siendo un `--full` a mano.
- `Documentos/testing-frontend.md` mantiene cifras desfasadas (729 tests frente a 854). **No se actualizan aquí**: la causa no es este change y la medición propia perdió los nombres de la línea base, así que sustituir una cifra desfasada por otra peor documentada no sería una mejora. Anotado para quien verifique.
- **La verificación independiente del change está pendiente.** El prompt autocontenido para ejecutarla en una sesión nueva está en `Documentos/Proyecto Final AIEng/informes/c41-verify-prompt.md`.



---

<a id="pr-45"></a>
## #45 — feat(sales): dar pantalla al agente de venta y su consumidor .NET

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c42-add-frontend-agent-panel` → `ai-eng` |
| Creada | 2026-09-26 |
| Integrada | 2026-09-26 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/45 |

### Descripción

## 📋 Descripción

El agente de venta —`POST /v1/assist/agent`, entregado y medido desde C32b— **no tenía ningún consumidor**: `IAiGatewayClient` declaraba siete métodos y ninguno era el suyo, así que la ruta existía, se probaba y nadie la llamaba. Esta PR construye ese consumidor y le da pantalla: ruta propia `/sales/new/agent`, cuarta tarjeta en el hub de venta, y un hilo de conversación donde **cada turno es dueño de su bloque de respuesta**, con los grupos rotulados por procedencia, la traza de llamadas desplegable y los diez motivos de parada traducidos.

Por el camino se arregla que el argumentario del agente se retirase **por construcción**: la tarea del agente vivía en `assist/v4`, cuyo *Sistema* ordena escribir `{{price}}`/`{{stock}}` siempre, su payload viaja con `is_anchored = False`, y C40 metió `placeholder_in_free_query` en `HARD_VIOLATION_CAUSES`. Los tres eslabones son correctos por separado y juntos retiraban el argumentario. Se añade `ai-service/prompts/assist/v6.md` y sólo se mueve `AGENT_PITCH_PROMPT_VERSION`: `PROMPT_VERSION`, `v4.md` y `v5.md` quedan sin diff, porque sus cifras están publicadas.

No hay ruta nueva bajo `/v1`, ni migración de EF Core o Alembic, ni séptima herramienta. El contrato congelado se mueve en una sola hoja y `SearchOrigin` gana un quinto valor sin tocar el esquema.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

El `fix` no es incidental: es el defecto de los tres eslabones descrito arriba, más la parada inexistente que la comprobación manual encontró en `agent-answer-block.tsx` (ver *Notas adicionales*).

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-09-27-add-frontend-agent-panel/` — archivado en esta misma rama con **75/75 tareas**. 2 capabilities nacidas (`ai-agent-assist`, `sales-agent-panel`) y 5 modificadas (`sales-assistant-agent`, `assist-generation`, `ai-gateway-client`, `ai-free-query-search`, `ai-service-auth`), con 25 requisitos en 7 delta specs.
- **HU**: `Documentos/Historias/AI-Eng/HU-AIENG-042.md` (nueva, 16 escenarios de aceptación y 16 decisiones cerradas D1–D16).
- **Informes**: `c42-exploration-decisions.md` y su `-v2` (que corrige el §11 del v1), y `c42-implementation-measurements.md` con las refutaciones medidas.
- **Deuda cerrada**: la entrada de C32b en `openspec/DEFERRED_TASKS.md` se cierra **por refutación y no por ejecución**, con la aritmética escrita — ~13.000 tokens por petición contra 25.000 TPM es una petición por minuto, así que una pasada de 204 peticiones cuesta 2 h 44 min.

El orden de ejecución **no fue el del ticket**, y está anotado en `tasks.md`: el v1 de la exploración pedía medir antes de la primera tarea y eso no era ejecutable, porque el arnés no contaba marcadores ni registraba la antigüedad de la proyección. De ahí un tramo de instrumentos antes de cualquier tarea funcional.

---

## 🔄 Cambios realizados

### `ai-contracts` — el contrato congelado, en una hoja

- `ai-service/src/jbg_ai/api/schemas/assist.py`: nace `AgentAssistGroup(AssistGroup)` con `origin: Literal[GROUP_ORIGIN_CATALOGUE, GROUP_ORIGIN_SUBSTITUTES]`, y `AgentAssistResponse.groups` se retipa a `list[AgentAssistGroup]`. **Es una subclase y no un campo en `AssistGroup`**, por el precedente que sienta `AgentUsage`: el modelo compartido es lo que publica `POST /v1/assist/sale`, y ensancharlo movería el esquema de esa ruta.
- `ai-service/openapi.json`: regenerado. **El diff no es adición literal pura** y conviene que el reviewer lo sepa: retira exactamente **una** línea, el `$ref` de `AgentAssistResponse.groups.items`, que pasa de `#/components/schemas/AssistGroup` a `#/components/schemas/AgentAssistGroup`. Al ser la subclase un superconjunto de campos, ningún campo desaparece para un consumidor; el resto del diff es el esquema nuevo.

### `ai-service` — procedencia, prompt y ámbito

- `assist/agent.py`: `AgentRun.groups` y `_pieces()` retipados; `response_groups.append(AgentAssistGroup(..., origin=origin, ...))` lee **la misma clave `key[0]`** que usa el grupo del payload, en lugar de re-derivar la procedencia.
- `assist/constants.py`: `AGENT_PITCH_PROMPT_VERSION` pasa de `"assist/v4"` a `"assist/v6"`.
- `ai-service/prompts/assist/v6.md` (nuevo): `## Sistema` copiado carácter a carácter de v5, y una única `## Tarea · evidencia del agente` con la regla añadida — sin pieza anclada no hay nada contra lo que resolver un marcador, así que no se escribe ninguno, y el lenguaje comparativo sí cabe.
- `api/routers/assist.py`: la ruta del agente pasa a `Depends(get_unscoped_principal)`, uniéndose a las que C40 ensanchó. Admite el ámbito «todas las tiendas» por **ausencia** de la reclamación `pos_id`, nunca por comodín.
- `stubs/responses.py`: el stub etiqueta todos sus grupos como `GROUP_ORIGIN_CATALOGUE`, con el motivo escrito — no corre ningún bucle, así que fabricar un pivote enseñaría a los clientes de stub un contrato que el camino real no produce.
- `evals/agent_sweep.py`: dos instrumentos nuevos. `placeholders_in()` cuenta marcadores sobre el **primer intento** y no sobre el reparado, porque contar al superviviente mide la reparación y no el prompt; `projection_freshness()` lee `projection_synced_at()` de `ai.sync_checkpoint` y **nunca** `ai.pos_projection.refreshed_at`, registrado **por fila** porque una pasada dura más que el techo de 3.600 s. Las filas anteriores al instrumento llevan `None` y **no cero**.
- `evals/results/c32b-agent-sweep-17fbdd15a18c.json` (nuevo): artefacto de la pasada, con `run_id`, `git_sha`, `prompt_version` y antigüedad de proyección.

### `backend-domain`

- `Domain/Enums/SearchOrigin.cs`: `AssistedAgent = 5`, con el remark que explica por qué **no** se pliega en `AssistedGenerative` —una ruta generativa es una consulta produciendo un resultado; ésta es una conversación que paga varias vueltas del transcript acumulado— y que **no necesita migración**, porque la columna persiste el enum por conversión a entero.

### `backend-api`

- `API/Controllers/AiSearchController.cs`: `[HttpPost("agent")]` con `[EnableRateLimiting(RateLimitPolicies.AiAgentAssist)]`; `Guid.Empty` responde 400 y el validador corre antes de llamar al servicio.
- `Application/DTOs/Ai/AiAssistAgentDtos.cs` (nuevo): contrato de pasarela — `AiAssistAgentRequest`, `AiAgentTurn`, `AiAssistAgentResponse : AiAssistSaleResponse` con `new List<AiAssistAgentGroup> Groups`, `AiAssistAgentGroup : AiAssistGroup` con `Origin`, `AiAgentUsage : AiUsage` con `Calls`, `AiAgentTraceIteration`, `AiAgentTraceTool`.
- `Application/DTOs/Ai/AgentAssistDtos.cs` (nuevo): contrato de aplicación, con `AgentTranscriptCaps` (`MaxTurns=12`, `MaxTurnChars=500`, `MaxTranscriptChars=4000`) y los DTO de turno, traza, uso y desenlace.
- `Application/DTOs/Ai/AiSearchAvailabilityResponse.cs`: `AgentAvailable` (bool **opcional**) y `AgentUnavailableReason`. Opcional a propósito: un backend anterior a C42 lo deja indefinido, y ausente significa «la sonda no lo dijo», no «apagado».

### `backend-application`

- `Services/AgentAssistService.cs` (nuevo): orquesta **un** turno. Interruptor propio vía `options.IsEnabledForScope`, hidratación de **todos** los miembros de **todos** los grupos incluidos los sustitutos, `RecordAsync` con `Origin = SearchOrigin.AssistedAgent`, y `LogFunnel` con `stage=agent_assist`. **El transcript no se registra nunca**, ni en log ni en telemetría.
- `Services/AiGatewayClient.cs`: `AgentClientName = "ai-agent"`, `AssistAgentPath = "/v1/assist/agent"`, `InBandDegradations = ["fallo_proveedor", "sin_cliente"]` y `AssistAgentAsync`, que registra `ai_gateway_agent_degraded` como *warning* y `ai_gateway_agent_completed` al cerrar.
- `Extensions/AiGatewayServiceCollectionExtensions.cs`: registro del cliente `ai-agent` con su *pipeline* de Polly y validación de arranque de `AgentTimeoutMs`, cuyo mensaje **nombra `AGENT_DEADLINE_SECONDS`**. El comentario deja escritas las tres razones por las que el cortafuegos **no cuenta** la degradación en banda: Polly recibe un `Outcome<HttpResponseMessage>` y **no ve el cuerpo**, así que un 200 con `stop_reason=fallo_proveedor` es un éxito en esa capa y se instrumenta como métrica.
- `Configuration/AiAgentAssistOptions.cs` (nuevo): `SectionName = "AiAgentAssist"`, `EnabledByDefault` (false), `EnabledPointOfSaleIds`, `RateLimitPermitLimit = 4`, `CandidateWindow = 5`.
- `Configuration/AiGatewayOptions.cs`: `AgentTimeoutMs = 18_000` con `MinimumAgentTimeoutMs = 15_000`. `AssistTimeoutMs` no se toca.
- `Services/AssistedSearchService.cs`: la sonda resuelve el agente con `_agentOptions.CurrentValue.IsEnabledForScope(pointOfSaleId)`, **nunca derivado** del veredicto asistido.
- `Validators/AgentAssistRequestValidator.cs` (nuevo): los tres topes, al menos un turno de operario, mensajes es-ES.
- `Interfaces/IAgentAssistService.cs` (nuevo) e `Interfaces/IAiGatewayClient.cs`: el octavo método de la interfaz.

### `backend-misc`

- `API/Extensions/ServiceCollectionExtensions.cs`: `RateLimitPolicies.AiAgentAssist` y su política de ventana fija particionada por usuario. El comentario deja la aritmética: el límite lo fija la cuota de tokens por minuto, no el gusto.
- `API/Program.cs`: `builder.Services.AddAgentAssist(builder.Configuration)`.

### `frontend` + `frontend-pages` + `frontend-services`

- `components/sales/agent/` (7 ficheros nuevos): `agent-answer-block.tsx` (el bloque por turno, con el orden derivado de frecuencias medidas), `agent-transcript.ts` (`countTranscript(turns, hasDraft)`, que suma **los turnos del asistente**), `agent-copy.ts` (los diez motivos de parada, `UNKNOWN_STOP_REASON`, `BUDGET_STOP_REASONS`, `ORIGIN_COPY`), `agent-entry-card.tsx` (`agentGateState`, tres estados), `agent-trace.tsx`, `agent-composer.tsx`, `agent-session-cost.tsx`.
- `pages/sales/agent.tsx` (nuevo) y `pages/sales/index.tsx` (lectura de la sonda al montar + `<AgentEntryCard>`).
- `routing/routes.tsx`: `NEW_AGENT: '/sales/new/agent'`; `routing/app-routing-setup.tsx`: carga perezosa de `AgentSalesPage`.
- `services/agent-assist.service.ts` y `types/ai-agent.types.ts` (nuevos); `types/ai-search.types.ts` gana `agentAvailable?` y `agentUnavailableReason?`.

### `openspec` + `docs`

- Specs vivas sincronizadas y change archivado en `openspec/changes/archive/2026-09-27-add-frontend-agent-panel/`.
- `openspec/config.yaml`: retirada la frase «Free query and agent routes have no .NET consumer», que C40 y C42 refutan. `openspec/project.md`: `SearchOrigin` pasa de «three paths» a cinco (iba **dos** changes por detrás), la regla 17 de tres vías de entrada a cuatro, y entrada nueva de C42.
- `Documentos/`: `modelo-c4.md` (componente **Agent Assist Service**, módulo **Agent Panel Module**, cuarta familia del gateway y los dos diagramas Mermaid), `arquitectura.md` (tercer camino de la frontera .NET↔Python y fila de `AgentTimeoutMs`), `modelo-de-datos.md` (quinto `SearchOrigin`), `epicas.md`, `testing-backend.md`, `testing-frontend.md`, y el plan de changes.
- Los cinco README: el raíz (§4 con el cuarto endpoint de IA), `backend/README.md` (matriz de autorización, cuatro interruptores donde decía tres, seis variables nuevas), `frontend/README.md`, `ai-service/README.md`, `ai-service/tests/README.md`. `terraform/README.md` **sin cambios**: ningún interruptor de IA llega a SSM.
- `CLAUDE.md`: regla nueva medida en este change — **las tres suites no se pueden medir en paralelo**; en paralelo dan 490 rojos de 1.347 en el backend donde en serie dan 53, porque `vitest` satura la máquina y testcontainers pierde la tubería con nombre de Docker.

---

## 🧪 Testing

Tests presentes en el diff: **53 nuevos en xUnit, 105 en Vitest y 11 en pytest**, más la reescritura de los guardianes de contrato existentes.

| Suite | Fichero | Qué fija |
|---|---|---|
| xUnit | `UnitTests/Application/AgentAssistServiceTests.cs` (nuevo, 18) | El turno, la hidratación de sustitutos, el ámbito global y que el transcript no se registra |
| xUnit | `UnitTests/Application/AiGatewayAgentTests.cs` (nuevo, 16) | `AssistAgentAsync`, la degradación en banda como *warning* y que no abre el circuito |
| xUnit | `IntegrationTests/AiAgentAssistControllerTests.cs` (nuevo, 15) | El endpoint sobre HTTP, los 400 y el cupo |
| xUnit | `UnitTests/Application/AiGatewayRegistrationTests.cs` (+4) | El suelo de 15 s rechazado en el arranque |
| xUnit | `UnitTests/Application/AiContractSnapshotTests.cs` | Los 7 DTO del agente entran en la guarda de paridad — **y ella encontró un desajuste real**: `TopK` era `int?` contra un contrato `int` |
| Vitest | `components/sales/agent/__tests__/` (4 ficheros, 74) | El bloque por turno, los topes con `hasDraft`, la copia de los diez motivos y los tres estados de la tarjeta |
| Vitest | `pages/sales/__tests__/agent.test.tsx` (nuevo, 20) | La página, el aviso al cambiar de tienda y el coste de sesión |
| Vitest | `services/agent-assist.service.test.ts` (nuevo, 11) | El servicio |
| pytest | `tests/assist/test_agent.py` (+4) | `origin` como **diferencia de conjuntos de campos**: `"origin" not in AssistGroup.model_fields` y `set(AgentAssistGroup.model_fields) - set(AssistGroup.model_fields) == {"origin"}`, así que ensanchar el modelo compartido rompe el test aunque las respuestas sigan bien |
| pytest | `tests/api/test_agent_route.py` | Guardián de contrato reapuntado a `fixtures/openapi-c42-baseline.json` (`sha256 8d9060ac…`), con el recorrido hoja a hoja — **1295 hojas** en la línea base — y `origin` verificado propiedad a propiedad |
| pytest | `tests/api/test_auth.py` (+1) | `test_agent_route_accepts_a_token_without_pos_claim`, con las rutas de una sola tienda seguidas rechazando la omisión |
| pytest | `tests/assist/test_prompt.py` (+2) | `assist/v6` fijado a su constante y `PROMPT_VERSION` fijado a **no** moverse |
| pytest | `tests/evals/test_agent_sweep.py` (+4) | Los dos instrumentos del arnés |

Comprobación **manual** ejecutada por el usuario según `c42-manual-check-runbook.md`, con dos hallazgos que ningún test vio (ver *Notas adicionales*).

---

## ✅ Checklist pre-merge

- [ ] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` — *requiere juicio del reviewer; el diff respeta la separación (enum en `Domain`, DTO y servicios en `Application`, endpoint en `API`)*
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *hay ficheros de test para cada pieza nueva; el **porcentaje** de cobertura no es medible desde el diff y queda sin verificar*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no aplica: `SearchOrigin` se persiste por `HasConversion<int>()`, así que un miembro nuevo es un valor admisible y no un cambio de esquema*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai`
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — *`openspec validate --all --strict` → 64 passed, 0 failed, ejecutado en la rama tras archivar; son 64 y no 65 porque el change ya no cuenta como activo*
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`) — *el guion manual cita la semilla de desarrollo local (`admin` / `Admin123!`), que ya está publicada en `backend/README.md:566`; no hay credencial nueva ni de producción*
- [x] Revisado el impacto en otros componentes del monorepo — *ver Deployment notes*

---

## 🚀 Deployment notes

**Orden de despliegue: `jbg-ai` antes que el backend.** El proveedor del contrato va primero — el backend consume `origin`, que sólo existe tras desplegar el servicio. Al revés, `AgentAssistService` recibiría grupos sin `origin` y la deserialización fallaría. Backend y SPA se despliegan juntos porque la imagen de producción los empaqueta.

**Variables nuevas, todas opcionales y con valor por defecto:**

| Variable | Defecto | Nota |
|---|---|---|
| `AiAgentAssist__EnabledByDefault` | `false` | El agente **no se sirve por defecto**: encenderlo en una tienda es un acto explícito |
| `AiAgentAssist__EnabledPointOfSaleIds__N` | vacío | Recargable sin redespliegue vía `IOptionsMonitor` |
| `AiAgentAssist__RateLimitPermitLimit` / `__RateLimitWindowSeconds` | `4` / `60` | Derivado de la cuota de tokens del proveedor |
| `AiAgentAssist__CandidateWindow` | `5` | El tope que el contrato congelado impone a `top_k` |
| `AiGateway__AgentTimeoutMs` | `18000` | **El arranque rechaza < 15000**, que es `AGENT_DEADLINE_SECONDS` |

Ninguna llega a SSM: no guardan secreto. `AiGateway__AssistTimeoutMs` no cambia.

**Precondición para reproducir la pasada de medición** (no para desplegar): el contenedor `jbg-ai` levantado con `JPV_POS_SYNC_SCHEDULER_ENABLED=true`, comprobado en la sección `projection` de `GET /health`. El arnés es un CLI y **no drena nada**, así que tener C41 archivado no basta.

**Rollback**: poner `AiAgentAssist__EnabledByDefault=false` y vaciar la lista de tiendas apaga la función sin desplegar nada — la tarjeta se pinta en gris con su motivo y el endpoint no llama a la IA ni consume cuota. Sin migración, no hay nada que revertir en la base.

---

## 📝 Notas adicionales

**Ningún breaking change, y merece justificarse pieza a pieza.** El `$ref` retipado de `AgentAssistResponse.groups.items` estrecha el esquema **de esa ruta sola** hacia un superconjunto de campos, así que ningún campo desaparece; la ruta además no tenía consumidor antes de esta PR. `get_unscoped_principal` **relaja** el requisito de la reclamación `pos_id`, no lo endurece. Los dos campos de la respuesta de disponibilidad son opcionales. Las cinco variables nuevas tienen defecto. Y `SearchOrigin` sólo añade un miembro.

**Riesgo: alto por señales, sin ruptura confirmada.** Toca `Program.cs`, `ai-service/openapi.json`, un enum de dominio y el perfil de reclamaciones de una ruta — cuatro de las señales que la referencia de riesgo marca como altas. Lo que compensa: sin migración, sin breaking, y el interruptor por defecto apagado deja la superficie nueva inerte hasta que alguien la encienda.

**Un método nuevo en `IAiGatewayClient`** rompería a cualquier implementador externo; dentro del monorepo los únicos son el cliente real y los dobles de test, y ambos están en el diff (`TestHelpers/ThrowingAiGatewayClient.cs`).

**Trece refutaciones medidas, de las que cuatro conviene que el reviewer conozca:**

1. **La caída del argumentario retirado del 13,1 % al 1,2 % NO es atribuible a `assist/v6`**, y el informe nombra los confundidores. Era lo esperado: la frase que ordena escribir marcadores es idéntica palabra por palabra en `v3` y `v4`, y C40 ya había medido ahí 3 de 90. El arreglo del prompt es real y su urgencia era pequeña.
2. **Las piezas por respuesta siguen saturando en `MAX_AGENT_PIECES`**: el tope sigue mordiendo.
3. **La tabla de herramientas del informe de exploración mezcla los dos arms**: 115 de las 125 invocaciones de `buscar_sustitutos` pertenecen al arm descartado, así que la cifra que justificaba rotular la procedencia acertaba en la conclusión y no en la magnitud.
4. **Nada ejercitaba la ruta del agente sobre HTTP**: el contenedor servía código anterior al change, y eso sólo apareció al montar la comprobación manual.

**Dos hallazgos de la comprobación manual que ningún test vio:**

- `agent-answer-block.tsx` **afirmaba un motivo de parada cuando la pasarela no había contestado**, mostrando «el agente terminó por un motivo que esta pantalla no reconoce» junto a «0 vueltas · 0 consultas» de un bucle que nunca corrió. Corregido condicionando la tira a `aiAvailable`, con 6 tests.
- **Limitación conocida, declarada y fuera de alcance**: el pivote a sustitutos **es inalcanzable si el operario nombra la pieza por su nombre**, porque `buscar_catalogo` no devuelve el nombre del producto. Establecido con un experimento HTTP —por SKU pivota, por nombre no— y abierto en `openspec/DEFERRED_TASKS.md`.

**Limitación heredada, no cerrada**: una consulta de ámbito global **no queda registrada**, porque el evento de telemetría exige punto de venta. Es la misma carencia que declaró el cuarto valor de `SearchOrigin`, y cerrarla sí abre migración. Además, como el operario elige el panel, la comparación entre vías es una **ablación y no un contraste aleatorizado**.

**Cinco chunks del diff vienen truncados** por tamaño y su análisis se apoya en cabeceras de hunk: los tres informes largos de `Documentos/`, el artefacto de medición `c32b-agent-sweep-17fbdd15a18c.json`, el fixture `openapi-c42-baseline.json`, y el grupo de `openspec/` que incluye `tasks.md`, `ticket.md` y cuatro specs vivas.



---

<a id="pr-46"></a>
## #46 — feat(demo): preparar el redespliegue del entorno de demostración y auditar su configuración

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c39a-redeploy-and-audit-demo-environment` → `ai-eng` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/46 |

### Descripción

## 📋 Descripción

Prepara el entorno de demostración del Proyecto Final para volver a servir el sistema que el proyecto ha construido, y cierra los huecos de configuración que un redespliegue tal cual habría dejado abiertos. **La rama `demo` está 84 commits por detrás de `ai-eng`**, parada en el QA de C34, y el `IMAGE_TAG` desplegado —`sha-d6a740fa5e0b…`— coincide con el HEAD de esa rama: no es una deducción a partir de git, es el commit desde el que se construyó la imagen que está corriendo. Lo desplegado no contiene C36, C40, C40_FIX, C41 ni C42.

Pero un *fast-forward* no bastaba. La auditoría de `compose.demo.yaml` contra los 51 ajustes que declara `jbg_ai` y las 7 clases de opciones de `Application/Configuration/` destapó cinco huecos, y el que más pesa es que **`AiAgentAssist__EnabledByDefault` no estaba**: es un `bool` sin inicializador con lista de puntos de venta vacía, así que el panel del agente no se serviría en el entorno cuyo único trabajo es enseñarlo. **Es la tercera vez que el mismo defecto llega al mismo fichero** —C17 lo encontró para la búsqueda asistida, C40_FIX para la consulta libre—, y la forma es idéntica las tres veces.

Esta PR **no despliega nada**: `deploy-demo.yml` dispara por `push` sobre `demo`, no sobre `ai-eng`. Lo que hace es dejar el árbol en un estado en el que ese despliegue sea correcto. La verificación del entorno resultante es de **C39a-bis** (`verify-demo-redeployment`), que entra en esta misma PR con sus cuatro artefactos y sin implementar.

### Tipo de cambio

- [x] ✨ feat — funcionalidad nueva
- [x] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [x] 🧪 test — tests
- [x] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change:** `openspec/changes/archive/2026-09-27-redeploy-and-audit-demo-environment/` (archivado en esta PR, 28/28 tareas) y `openspec/changes/verify-demo-redeployment/` (abierto, 0/24).
- **HU:** `Documentos/Historias/AI-Eng/HU-AIENG-043.md`, 14 escenarios.
- **Informe:** `Documentos/Proyecto Final AIEng/informes/c39a-implementation-measurements.md`.

El §5 de la convocatoria del Proyecto Final es tajante: *«si el evaluador no puede acceder al sistema funcionando, el proyecto no puede evaluarse correctamente»*. Hoy la demo responde 200 con certificado válido y sirve la búsqueda asistida de C16 y las rutas de C34 — y nada más de lo que vino después.

**El change se partió en dos durante su propio apply**, y el motivo es de orden: sus tareas de verificación exigían un entorno desplegado, y el despliegue ocurre **al mergear el change a `demo`**. Un change que sólo se puede archivar después de archivarse no es un change.

---

## 🔄 Cambios realizados

### `misc` — `compose.demo.yaml` (+41)

- **`AiAgentAssist__EnabledByDefault: "true"`** en `jbg-demo-api`, literal versionado. Los otros tres interruptores del mismo patrón ya estaban; éste faltaba.
- **`JPV_ROUTER_LLM_API_KEY`** y **`JPV_AGENT_LLM_API_KEY`** en `jbg-demo-ai`, interpoladas con valor por defecto vacío (`${…:-}`) para que `docker compose config` resuelva sin el script de despliegue.

### `infra` — `ai-service/Dockerfile`, `deploy/demo/deploy.sh`, `backend/docker-compose.yml` (+89)

- **El corpus entra en la imagen de `jbg-ai`** por un **contexto adicional con nombre**: `COPY --from=corpus . ./data/knowledge`. El contexto primario sigue siendo `ai-service`, y eso es deliberado — `backend/docker-compose.yml` construye el mismo `Dockerfile` con `context: ../ai-service` para desarrollo local, así que mover el contexto a la raíz lo habría roto. Ese compose gana `additional_contexts: corpus: ../data/knowledge`, sin el cual dejaría de construir.
- **`deploy.sh`** lee los dos parámetros nuevos con el patrón **literal** de `ASSIST_LLM_API_KEY` —`read_parameter … || true`, sin `: "${…:?}"`— y registra *presente/ausente* por etapa, una línea por cada una, sin revelar valor.

### `scripts` — `deploy/demo/verify.sh` (+127/-4)

De **cinco condiciones de fallo a siete**:

- **Sexta**: `ai.knowledge_chunk` sin fragmentos. Leída de la base y no de `/health`, porque el informe de salud no tiene sección de corpus y añadírsela sería tocar `ai-service/src`, fuera del alcance declarado.
- **Séptima**: la ruta del agente no responde, con un token de servicio acuñado como ya hace el calentamiento de `deploy.sh`. **Distingue el no responder de una degradación en banda**: un 200 con `stop_reason` de `sin_cliente` o `fallo_proveedor` se reporta y **no** hace fallar, porque la credencial del agente es opcional por diseño y borrarla es su *rollback* documentado.

### `ai-service` — `src/jbg_ai/knowledge/constants.py` (+40/-1)

`CORPUS_DIR` pasa de **derivarse** a **buscarse**, con los mismos tres candidatos que `assist/prompt.load_prompt_file`. Antes se calculaba con `parents[3].parent`, correcto en un *checkout* y absurdo con el paquete instalado por `uv sync --no-editable`: medido dentro del contenedor desplegado, el corpus se buscaba en `/app/.venv/lib/data/knowledge`. `_resolve_corpus_dir()` **no levanta excepción al importar** — corre en tiempo de importación, y un corpus ausente no debe presentarse como el servicio entero caído; `discover_documents` sigue siendo quien falla, con el directorio nombrado.

### `tests` — `ai-service/tests/knowledge/test_corpus_location.py` (+77, nuevo)

Cinco tests: la resolución en *checkout*, que los candidatos cubren el despliegue instalado, que el orden decide, que **nunca levanta excepción** aunque no exista ninguno, y que `SIDECAR_PATH` y `OUT_OF_DOMAIN_PATH` cuelgan de la resuelta.

### `ci` — los tres workflows (+47/-4)

- **`test-backend.yml`** y **`test-frontend.yml`**: disparador de `[main, develop]` a **`[ai-eng, master]`**. **Ninguna de las dos ramas anteriores existe** en este repositorio, así que los dos workflows estaban bien escritos y eran inertes: no se habían ejecutado nunca. Los filtros `paths:` se conservan.
- **`deploy-demo.yml`**: `--build-context corpus=./data/knowledge` en el *build* de la imagen de IA.

### `openspec` — 93 ficheros (+2260/-793)

| Naturaleza | Ficheros |
|---|---|
| C39a archivado en `archive/2026-09-27-…/` | 7 |
| **C39a-bis** `verify-demo-redeployment/`, cuatro artefactos y una delta | 5 |
| Specs vivas sincronizadas: `demo-deployment`, `backend-testing` | 2 |
| `DEFERRED_TASKS.md`: cierre de la entrada del corpus de C34 | 1 |
| **Enlaces relativos reparados** | 78 |

La sincronización mueve **cinco requisitos** y lleva 15 escenarios a 28. Los 78 restantes son la reparación de **874 enlaces** que el archivado de un change rompe desde agosto y que el comprobador del repositorio excluye por diseño: dos defectos del mismo mecanismo —678 a tres niveles apuntando a la raíz, 193 a dos niveles apuntando a `openspec/specs/` o a otro change archivado— corregidos con la regla de que sólo se reescribe un enlace **cuyo destino corregido existe en disco**.

### `docs` — 10 ficheros (+1320/-47)

Nuevos: **HU-AIENG-043** (413 líneas, 14 escenarios) y el **informe de implementación** (426). Puestos al día: el plan de changes, `epicas.md`, `deploy/demo/README.md` (+108/-23: los dos parámetros nuevos, el recuento de no secretos corregido a cuatro, un §5.6c para las otras dos superficies de IA y la nota de caducidad del bundle de CA), `testing-backend.md`, `backend/README.md`, `ai-service/README.md`, `ai-service/tests/README.md` y una frase del **README raíz**.

---

## 🧪 Testing

- **`ai-service`**: **1.664 passed, 0 failed** (`uv run pytest`), incluidos los 5 nuevos de `test_corpus_location.py`. El snapshot del contrato congelado, **4 passed**, y `ai-service/openapi.json` **no aparece en el diff**.
- **Líneas base medidas antes de tocar nada, en serie**: backend **50 de 1.408** (`Con error: 50, Superado: 1358`) y frontend **113 de 959 en 14 ficheros de 63**. Las dos dentro de la banda que `CLAUDE.md` documenta. **No se volvieron a medir**: el diff no toca `backend/src` ni `frontend/src`, así que sus insumos no cambiaron — y esta PR **dispara los dos workflows por tocar sus propios ficheros**, que es la primera ejecución de esos workflows en la historia del repositorio.
- **Las dos condiciones nuevas de `verify.sh`, probadas en los dos sentidos**: el camino de paso contra el entorno desplegado actual —`161 fragment(s)`, ruta del agente respondiendo— y el de fallo **provocado**, que sale con código 1 y nombra las dos causas.
- **La imagen, construida y comprobada por dentro**: `CORPUS_DIR` = `/app/data/knowledge`, no es enlace, 33 documentos y *sidecar* presente; en la imagen anterior el directorio **no existe**. Y un *build* **sin** el contexto nombrado **falla** con código 1.
- `openspec validate --all --strict`: **65 passed, 0 failed**.

Sin tests de backend ni de frontend en el diff, porque no hay código de esos componentes en él.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md`
- [x] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — *el único código nuevo es de `ai-service` y lleva sus 5 tests; no hay código de backend ni de frontend en el diff*
- [x] Migración de EF Core incluida si cambia el modelo de datos — *no cambia: cero migraciones en el diff, y comprobado que tampoco hay ninguna entre `demo` y `ai-eng`*
- [x] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — *no cambia el contrato; el fichero no está en el diff y su test de snapshot pasa*
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [x] Sin secrets ni credenciales en el diff (van a SSM `/jpv/prod/*`)
- [x] Revisado el impacto en otros componentes del monorepo
- [ ] Recorrido manual del entorno desplegado — **es de C39a-bis y no puede hacerse desde esta PR**

---

## 🚀 Deployment notes

**Mergear esta PR a `ai-eng` no despliega nada.** `deploy-demo.yml` dispara por `push` sobre `demo`. El despliegue ocurre al llevar `demo` a `ai-eng` después.

**Dos parámetros nuevos en SSM, ya creados** como `SecureString` en la cuenta de la demo, versión 1: `/jbg-demo/ROUTER_LLM_API_KEY` y `/jbg-demo/AGENT_LLM_API_KEY`. **Los dos son opcionales** y `deploy.sh` no los valida como no vacíos: su ausencia es un estado declarado, no un fallo de despliegue.

**Sin variables de Terraform nuevas**, y es una decisión: los dos *stacks* no tienen ninguna de IA porque esa configuración vive en el compose como literal versionado y en SSM como secreto creado a mano, deliberadamente fuera del fichero de estado.

**Cuando se despliegue, esperar dos efectos medibles**: la proyección de disponibilidad está a **unas 120 veces** su techo de rancidez —último drenaje incremental el 22 de septiembre contra un techo de 3.600 s— y el drenaje de C41 corre al arrancar, así que debería curarse sola; y el corpus ya tiene **161 fragmentos** en la base, que sobreviven porque viven en el volumen `jbg-demo-pgdata`.

**Sin riesgo de certificado**: el límite de cinco duplicados por semana sólo se toca destruyendo `jbg-demo-caddy-data` con `down -v`, y `deploy.sh` hace `up -d --remove-orphans`.

**Rollback, por pieza y sin revertir código**: borrar `/jbg-demo/AGENT_LLM_API_KEY` devuelve la ruta del agente a su degradación declarada; `AiAgentAssist__EnabledByDefault: "false"` apaga el panel; y el `IMAGE_TAG` anterior está registrado en SSM, así que `deploy.sh` acepta volver a él por argumento.

---

## 📝 Notas adicionales

**La ruta de producción no se toca, y está comprobado fichero a fichero.** Ni `deploy-aws-ec2.yml`, ni `deploy-backend-aws.yml`, ni `deploy-frontend-aws.yml`, ni `terraform/`, ni `Dockerfile.bundled`. Un aviso para el revisor: **`backend/docker-compose.yml` parece de producción y no lo es** — es el compose de desarrollo local; el de producción es `docker-compose.prod.yml`, sin tocar. Y `ai-service/Dockerfile` es exclusivo de la ruta de demo: se comprobó que `deploy-aws-ec2.yml` sólo construye `Dockerfile.bundled`.

**Tres refutaciones de los propios artefactos del change**, todas registradas en el sitio en vez de corregidas en silencio:

1. **El corpus no estaba vacío**: 161 fragmentos y 32 documentos. Se indexa en la base y la base vive en un volumen que el redespliegue no toca, así que el hueco impide **reindexar** y no vacía nada. Urgencia rebajada, cierre igual.
2. **La decisión D5 del `design.md` era incorrecta**: mover el contexto de *build* a la raíz habría roto el desarrollo local. Sustituida por el contexto nombrado, que además **falla en voz alta** si se omite.
3. **El corpus no sólo faltaba en la imagen**: la ruta que el servicio lee estaba mal calculada. Esa refutación es la que amplió la zona del change a `ai-service/src`.

**Las dos ejecuciones de CI de esta PR saldrán en rojo, y no es una regresión**: 50 de 1.408 y 113 de 959 fallos preexistentes, con los nombres guardados en la línea base del informe. Entran **informativas y no como puerta**, porque una comprobación obligatoria sobre una suite roja es un bloqueo permanente. Si alguna vez se hace obligatoria, hay una trampa anotada en `DEFERRED_TASKS.md`: un workflow omitido por filtro de rutas nunca reporta estado.

**Dos limitaciones declaradas y no cerradas:**

- **Nada detecta que la demo sirva una rama vieja.** Estuvo 84 commits y cinco semanas por detrás sin que ninguna comprobación lo dijera, y las siete condiciones de `verify.sh` **siguen sin comparar lo desplegado con la rama que debería servirse**. El dato existe en los dos lados; falta quien los cruce. Vía de cierre escrita en el *proposal* de C39a-bis.
- **La rancidez de la proyección no es condición de verificación.** La quinta condición cuenta filas ausentes, nunca antigüedad, así que un entorno con 6.720 filas rancias de cinco días pasa la verificación.

**Y un desvío de la máquina de desarrollo que no estaba en el ticket**: el bundle de CA **caduca** cuando Norton rota su raíz de interceptación, y el de agosto ya no la contenía — toda llamada a AWS moría con `CERTIFICATE_VERIFY_FAILED` incluso apuntando al bundle explícitamente. Regenerado de 131 certificados a 253, y documentado en el §1.3 del *runbook*, que decía cómo crearlo y no que expira.



---

<a id="pr-47"></a>
## #47 — release(demo): desplegar C36, C40, C40_FIX, C41, C42 y C39a — las cuatro superficies de IA al entorno de demostración

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `ai-eng` → `demo` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/47 |

### Descripción

> ## ⚠️ Mergear esta PR **es** el despliegue
>
> `deploy-demo.yml` dispara por `push` sobre `demo`. No hay un paso posterior: al mergear, el workflow construye las dos imágenes, las publica en ECR, ejecuta las revisiones de esquema, calienta el cliente de *embeddings* y corre la verificación desde dentro del anfitrión. **Es la única PR de este repositorio cuyo merge tiene efecto en un entorno alcanzable desde internet.**

## 📋 Qué se despliega

El entorno de demostración lleva **cinco semanas sirviendo una versión de hace 84 commits**. Su `IMAGE_TAG` es `sha-d6a740fa5e0b…`, que es exactamente el HEAD de `demo`: no es una inferencia, es el commit desde el que se construyó la imagen que está corriendo. Esta PR lo pone al día con **89 commits** y **seis changes**.

| Change | Qué añade al entorno |
|---|---|
| **C36** `add-frontend-assist-card-and-family-disambiguation` | La **ficha de venta** en `/sales/new/assist/:productId`: argumentario, variantes de la familia con confirmación explícita antes de vender, sustitutos y caja de pregunta |
| **C40** `add-frontend-free-query-panel` | El **panel de consulta libre** (modo M1), su interruptor, los dieciséis estados de respuesta distinguidos en pantalla y el cuarto origen de telemetría |
| **C40_FIX** `c40-fix-all-shops-scope-unreachable` | El ámbito **«todas las tiendas»**, que era inalcanzable al primer clic |
| **C41** `add-pos-projection-scheduled-drain` | El **drenaje de la proyección de disponibilidad** al arrancar y cada 600 s, más la sección `projection` del informe de salud |
| **C42** `add-frontend-agent-panel` | El **panel del agente**, con la traza del bucle en pantalla — la única prueba visible de que hay un agente y no un prompt |
| **C39a** `redeploy-and-audit-demo-environment` | Los cinco huecos de configuración que habrían dejado apagado lo anterior, el corpus dentro de la imagen y dos condiciones de verificación nuevas |

**Con esto las cuatro superficies de IA quedan alcanzables**: búsqueda asistida, ficha de venta, consulta libre y panel del agente. Hoy sólo llegan las dos primeras, y la segunda a medias.

### Reparto del diff

```
387 ficheros, +74.774 / −1.141

código      backend/src        56 ficheros   +7.980 / −103
            frontend/src       57            +11.921 / −54
            ai-service/src     31            +1.635 / −91
            ai-service/tests   24            +5.735 / −72
config      compose.demo.yaml   1            +55
            deploy/             3            +363 / −20
            .github/workflows   3            +47 / −4
            terraform/          —            SIN CAMBIOS
registro    Documentos/        30            +11.912 / −76
            openspec/         159            +14.282 / −666
```

**`terraform/` no se toca**, y es una decisión y no un olvido: la configuración de IA vive en `compose.demo.yaml` como literal versionado y en SSM como secreto creado a mano, deliberadamente fuera del fichero de estado.

---

## 🎯 Por qué ahora

El §5 de la convocatoria del Proyecto Final es tajante: *«si el evaluador no puede acceder al sistema funcionando, el proyecto no puede evaluarse correctamente»*. La URL responde 200 con certificado válido desde el 30 de agosto — y sirve un sistema al que le faltan **cuatro de las cinco superficies más visibles del entregable**. Un 200 no distingue un entorno actualizado de uno viejo, y ése es exactamente el modo de fallo que dejó pasar cinco semanas.

---

## 📍 Estado ANTES del despliegue

Medido contra la cuenta el 2026-09-27, para que el «después» sea comprobable y no una impresión:

| | |
|---|---|
| Instancia | `i-095f0ba16e2bb8278`, `running`, `t3.small`, desde el 2026-08-30 |
| *Hostname* | `52-49-209-14.sslip.io` — HTTPS válido, `http=200` |
| **`IMAGE_TAG`** | **`sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d`** ← el objetivo de *rollback* |
| Parámetros en SSM | **13** — 4 no secretos y 9 secretos, incluidos los **dos nuevos** ya creados |
| `ai.product_document` | 1.200 |
| `ai.knowledge_chunk` | 161 |
| `ai.pos_projection` | 6.720 filas, último drenaje incremental el **2026-09-22** → **≈120 × el techo** de rancidez |

---

## ⚙️ Qué hará el despliegue, en orden

1. **Construye y publica dos imágenes** en ECR: `jbg-demo-api` (con la SPA horneada en su `wwwroot` y `VITE_API_BASE_URL` relativo) y `jbg-demo-ai` — ésta **con el corpus dentro**, por un contexto adicional con nombre, y un *build* sin él **falla** en vez de producir una imagen vacía.
2. **Levanta la composición** con `up -d --remove-orphans`. **No** hay `down -v`: el volumen `jbg-demo-pgdata` sobrevive con catálogo, corpus y proyección, y `jbg-demo-caddy-data` con el certificado ya emitido.
3. **Aplica las revisiones de esquema** con `alembic upgrade head`. **Sin efecto esta vez: no hay ninguna migración entre `demo` y `ai-eng`**, ni de Alembic ni de EF Core, comprobado sobre los dos árboles.
4. **Calienta el cliente de *embeddings***, deliberadamente no fatal.
5. **Verifica desde dentro del anfitrión** con **siete** condiciones, dos de ellas nuevas en esta entrega: corpus sin fragmentos y ruta del agente que no responde.

---

## ✅ Qué comprobar después

- [ ] **Que el workflow se ejecutó**, y no sólo que el *push* llegó. `deploy-demo.yml` lleva `paths-ignore`, así que un empuje que cayera entero en esas rutas no despliega y no avisa.
- [ ] **Que el `IMAGE_TAG` de SSM cambió** respecto a `sha-d6a740fa…`. **Es la única comprobación que no se puede simular**: sin cambio de tag no hubo despliegue, responda lo que responda la URL.
- [ ] **Las siete condiciones de `verify.sh` en verde**, incluidas las dos nuevas.
- [ ] **Las tres credenciales de generación, propias y no de repliegue**: el log debe decir `stage=assist_client`, `stage=router_client` y `stage=agent_client`, **ninguna con `credential=…_fallback`**. El despliegue de C34 registró `assist_fallback` para el enrutador, y es la razón de que existan los dos parámetros nuevos.
- [ ] **La cuarta tarjeta del *hub* presente**, y una conversación pintando la traza del bucle.
- [ ] **La proyección curada.** Es una **predicción, no un hecho**: el drenaje de C41 corre al arrancar y en su forma completa cuando no hay *checkpoint*. Si no se cura, el hallazgo es del drenaje y se declara.
- [ ] **Sólo el proxy publica puertos** — ni la API, ni el servicio de IA, ni la base de datos.

El recorrido completo, con los cuatro usuarios sobre las cuatro superficies, es el change **C39a-bis** (`verify-demo-redeployment`), que entra abierto con 0/24 tareas y **no toca código por diseño**: sólo ficheros que el `paths-ignore` del despliegue ignora, así que verificar no cuesta un segundo redespliegue.

---

## 🔁 Rollback

Por pieza, y **ninguno exige revertir código**:

| Qué falla | Vuelta atrás |
|---|---|
| El entorno entero | `deploy.sh` acepta un tag por argumento, y el anterior es `sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d` |
| El argumentario del agente resulta caro o ruidoso | Borrar `/jbg-demo/AGENT_LLM_API_KEY` y redesplegar: la ruta vuelve a su degradación declarada |
| Igual con el enrutador de intención | Borrar `/jbg-demo/ROUTER_LLM_API_KEY` |
| El panel del agente estorba en la demostración | `AiAgentAssist__EnabledByDefault: "false"`, un literal y un redespliegue |

---

## ⚠️ Riesgos y avisos

**Ninguna acción destructiva.** `deploy.sh` no ejecuta `down -v`, que es lo único que destruiría `jbg-demo-pgdata` —catálogo, corpus e índice vectorial— y `jbg-demo-caddy-data`. Por eso **no hay riesgo de tocar el límite de cinco certificados duplicados por semana**: no se pide certificado nuevo.

**Producción no se ve afectada, y la separación es estructural**: otra cuenta de AWS, otra región (`eu-west-3` frente a `eu-west-1`), otro *stack* de Terraform, otras imágenes, y su propio workflow disparado por `main`/`master`. Comprobado además que **producción no construye la imagen de `jbg-ai`**, así que el cambio de su `Dockerfile` no la alcanza.

**Una petición por minuto.** ~13.000 tokens contra una cuota de 25.000 por minuto. Basta para un mostrador y para un evaluador; **no para dos simultáneos**. Es una limitación declarada del entorno, no un defecto a corregir aquí.

**Dos limitaciones que este despliegue no cierra:**

- **Nada detecta que el entorno sirva una rama vieja.** Es el defecto que permitió las cinco semanas: las siete condiciones de verificación miran índice, modelo, base, credencial, proyección, corpus y ruta del agente — y **ninguna compara lo desplegado con la rama que debería servirse**. El dato existe en los dos lados: `IMAGE_TAG` en SSM y `git rev-parse origin/demo`. Falta quien los cruce, y su arreglo es código.
- **La rancidez de la proyección no es condición de verificación.** La quinta cuenta filas ausentes, nunca antigüedad, así que un entorno con 6.720 filas de cinco días pasa la verificación.

**Y una nota para quien despliegue desde esta máquina:** el bundle de CA de `~/.aws/` **caduca** cuando Norton rota su raíz de interceptación, y entonces toda llamada a AWS muere con `CERTIFICATE_VERIFY_FAILED` incluso apuntando al bundle explícitamente. El §1.3 del *runbook* documenta cómo regenerarlo.



---

<a id="pr-48"></a>
## #48 — docs(demo): verificar el entorno desplegado y declarar sus cuentas

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c39abis-verify-demo-redeployment` → `ai-eng` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/48 |

### Descripción

## 📋 Descripción

Cierra **C39a-bis** (`verify-demo-redeployment`): recorre el entorno de demostración que el merge de C39a a `demo` desplegó, y deja la evidencia escrita. **Ni una línea de código** — los 13 ficheros del diff son documentación y especificación, y todos caen dentro del `paths-ignore` de `deploy-demo.yml`, de modo que **el diff de esta PR no dispara ningún despliegue**. Eso no es una casualidad de estilo: es la propiedad que justificó partir C39a en dos, porque sus tareas de verificación exigían un entorno que sólo existe *después* de archivar el change que las contenía.

**El resultado es que el entorno está sano y la comprobación está mal.** El despliegue ocurrió de verdad —ejecución `36322635852`, `IMAGE_TAG` de `sha-d6a740fa…` (versión 8 del parámetro) a `sha-2b357a1e…` (versión 9), idéntico a `git rev-parse origin/demo`— y los doce primeros pasos del workflow pasaron, incluidas las dos imágenes publicadas. Falló sólo el decimotercero, y por **una** de las siete condiciones de `verify.sh`: la quinta cuenta puntos de venta sin surtido **sin preguntar si la tienda está activa**, y `HT-ARTRUTX` está declarada cerrada a propósito desde C10. **Seis de siete en verde**, y el rojo es del juicio, no del entorno.

Por el camino se refutó una premisa de los propios artefactos de este change: **las cuentas del recorrido no existían**. El entorno tenía dos, no cuatro, y los tres operarios sintéticos sólo vivían en el mundo local, así que la abstención, los sustitutos y el pivote del agente **no se podían demostrar**. Quedan en cuatro cuentas activas —un administrador y un operario por tienda— declaradas en el nuevo §5.8 del *runbook*, que es el requisito que la delta añade a `demo-deployment`.

### Tipo de cambio

- [ ] ✨ feat — funcionalidad nueva
- [ ] 🐛 fix — corrección de bug
- [ ] ♻️ refactor — reestructuración sin cambio de comportamiento
- [ ] ⚡ perf — mejora de rendimiento
- [x] 📝 docs — documentación
- [ ] 🧪 test — tests
- [ ] 🔧 chore / ci / build
- [ ] 💥 breaking change — rompe compatibilidad

---

## 🎯 Motivación y contexto

- **Change de OpenSpec**: `openspec/changes/archive/2026-09-27-verify-demo-redeployment/` — archivado en esta PR, con `proposal.md`, `design.md`, `tasks.md` (28/29) y una delta de `demo-deployment`.
- **Historia**: [HU-AIENG-043](Documentos/Historias/AI-Eng/HU-AIENG-043.md) — los catorce escenarios quedan cerrados con su veredicto, repartidos entre C39a y C39a-bis.
- **Informe de mediciones**: `Documentos/Proyecto Final AIEng/informes/c39a-bis-implementation-measurements.md`.

C39a dejó el árbol correcto y **no podía comprobar el resultado**, porque el despliegue se dispara al mergear a `demo` — o sea después de archivar. Un change que sólo se puede cerrar después de cerrarse no es un change, y por eso se partió durante su propio *apply*. Esta PR es la otra mitad.

---

## 🔄 Cambios realizados

### `openspec` — 8 ficheros, +319/−48

- **Archivado del change**: `openspec/changes/verify-demo-redeployment/` → `openspec/changes/archive/2026-09-27-verify-demo-redeployment/`, con su `.openspec.yaml`.
- **`openspec/specs/demo-deployment/spec.md`** — delta sincronizada: **de 13 a 14 requisitos**. Entra *«The environment declares its demonstration accounts and what each one exercises»* con **5 escenarios**, dos de los cuales separan la cuenta sembrada —desactivada a propósito— de la administradora utilizable, cuya contraseña se declara **deliberadamente ausente** del repositorio. La descripción del requisito se fusionó **sin reescribir el texto**, así que sigue en una sola línea física de 404 caracteres: el validador lee sólo la primera, y un ajuste de ancho la rompe con un mensaje que no delata que el problema sea tipográfico.
- **`openspec/DEFERRED_TASKS.md`** — cuatro entradas nuevas, cada una con su experimento y su vía de cierre: la quinta condición, el caché de 10 s del informe de salud, las 66 filas de `ai.sync_failure` del *feed* `catalog` que nada mira, y el `CRITICAL` del reconocimiento de imagen.
- **`…/archive/2026-09-27-verify-demo-redeployment/tasks.md`** — un enlace relativo reparado (`../../../` → `../../../../`), roto por el propio movimiento al archivo.

### `docs` — 5 ficheros, +991/−11 *(chunk resumido por el recolector)*

- **`deploy/demo/README.md`** — nuevo **§5.8** con la tabla de cuentas: cada una con su punto de venta y **qué conducta es la única alcanzable desde ella**, más las desactivadas con su motivo. Incluye la restricción medida del agente (por referencia pivota, por nombre no) y la nota de que `HT-ARTRUTX` cuenta siempre como una tienda sin ámbito. El **§5.3** se corrigió dos veces: decía «exactly two accounts».
- **`Documentos/Proyecto Final AIEng/informes/c39a-bis-implementation-measurements.md`** — informe nuevo: las siete condiciones una por una con su categoría, el experimento del falso positivo, el recorrido del evaluador por las cuatro superficies, las latencias contra los tres relojes del agente, las cuatro ejecuciones de CI comparadas **por nombre**, y lo que se refutó.
- **`Documentos/Historias/AI-Eng/HU-AIENG-043.md`** — cierre de los catorce escenarios, con lo que **no** se cumple dicho explícitamente.
- **`Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md`** — entrada del §0, marcador de estado a `✅ archivado` y recuento al día.
- **`Documentos/epicas.md`** — recuento a **43 archivadas / 1 pendiente** y el resultado de C39a-bis en el bloque de C39.

---

## 🧪 Testing

**No hay tests en el diff, y no aplican: la PR no lleva código.** Lo que sí lleva son mediciones, y éstas son las que un revisor puede reproducir:

| Qué | Resultado |
|---|---|
| `openspec validate --all --strict` | **64 passed, 0 failed** |
| `verify.sh` desde dentro del anfitrión | sale **1**, con una sola causa; seis condiciones en verde |
| Experimento de la quinta condición | **1** sin filtro de actividad, **0** con él |
| Backend en CI *(2 ejecuciones)* | **49 y 48 de 1.408** — 13 nombres rotando, **los 13 en las clases ya declaradas inestables** |
| Frontend en CI *(provocado a mano)* | **113 de 959 en 14 de 63** — idéntico fichero por fichero a la línea base local de C39a |
| Lint de frontend | **89 errores, 82 avisos** — declarados y no arreglados |

**Las suites no se re-midieron en local** para este change: se leyeron de la CI, que se ejecutó por primera vez en la historia del repositorio. Y la de frontend **nunca había corrido**: moría en un lint que no podía funcionar porque `frontend/eslint.config.js` no existía.

---

## ✅ Checklist pre-merge

- [x] El código sigue las convenciones de `openspec/project.md` y las capas de `Documentos/modelo-c4.md` — *no hay código; las convenciones aplicables son las de `CLAUDE.md` sobre spec viva vs delta, respetadas*
- [ ] Hay tests para el código nuevo (backend ≥70%, frontend ≥70%) — **no aplica**, sin código
- [ ] Migración de EF Core incluida si cambia el modelo de datos — **no aplica**, el modelo no se toca
- [ ] `ai-service/openapi.json` actualizado si cambia el contrato de `jbg-ai` — **no aplica**, el contrato no se mueve
- [x] Spec de la capability actualizada en `openspec/` y `openspec validate` en verde — `demo-deployment` 13 → 14, gate en `64 passed, 0 failed`, y la spec viva sin sintaxis de delta
- [x] Documentación de `Documentos/` actualizada según la tabla de `openspec/project.md`
- [ ] **Sin secrets ni credenciales en el diff** — ⚠️ **deliberadamente no marcado, leer las notas.** No hay ninguna clave de proveedor, credencial de AWS ni clave privada, pero el diff **sí documenta contraseñas de las cuentas de operario de la demo**
- [x] Revisado el impacto en otros componentes del monorepo — los cinco README verificados uno a uno, los cinco sin cambios, con veredicto escrito

---

## 🚀 Deployment notes

**El diff de esta PR no dispara ningún despliegue**, y es criterio de aceptación comprobado fichero a fichero: los 13 caen en `openspec/**`, `Documentos/**` o `**/README.md`, las tres primeras reglas del `paths-ignore` de `deploy-demo.yml`. Cero ficheros fuera.

**Pero mergear `ai-eng` a `demo` sí desplegará, y no por esta PR.** `ai-eng` ya lleva `0c9bb68` por delante de `demo`, que toca `frontend/eslint.config.js` — fuera del `paths-ignore`. La propiedad que esta PR garantiza es la de **su propio diff**; no puede garantizar lo que la rama de integración ya arrastraba. Conviene saberlo para no leer un despliegue inesperado como un fallo del filtro.

**Dos mutaciones del entorno desplegado que no aparecen en ningún diff**, y se escriben aquí porque callarlas sería esconderlas:

1. Se **crearon por SQL** las tres cuentas de operario sintéticas (`op-ciutadella`, `op-fornells`, `op-aeroport`), rol `Operator`, hash BCrypt `2a`/12 generado **fuera del anfitrión** con el ayudante del propio proyecto. `admin` y `demo.admin` no se tocaron.
2. Se **desactivó** `demo.operador`, que duplicaba el mostrador de `op-aeroport`. Desactivada y **no borrada: la referencian 3.380 ventas**.

Ninguna es código, ninguna entra en una imagen y ninguna redespliega — pero las dos cambian un entorno accesible desde internet.

**Rollback**: revertir esta PR devuelve la documentación y desarchiva el change; **no deshace** las dos mutaciones de base de datos, que se revierten con sendos `UPDATE` sobre `"Users"."IsActive"`.

---

## 📝 Notas adicionales

### Lo de las credenciales, explicado

El diff documenta `Operator123!` como contraseña de las tres cuentas de operario de la demo. Tres razones por las que es deliberado, y una por la que aun así el ítem queda sin marcar:

- **Ya era una constante pública** del mundo sintético, documentada en `ai-service/src/jbg_ai/data/README.md`. No se añade ningún secreto que no estuviera.
- Son cuentas de **rol `Operator` únicamente**, sobre un catálogo sintético.
- La contraseña de la **cuenta administradora utilizable** (`demo.admin`) **no está**, y el nuevo requisito de la spec obliga a que siga sin estar.
- Aun así, **son credenciales en un diff de un repositorio público**, así que el revisor debe verlo y decidir, no encontrárselo marcado como limpio.

`admin` / `Admin123!` también aparece, pero como **credencial muerta**: está `IsActive = false` a propósito, porque el sembrador la recrea en cada arranque y `LoginAsync` rechaza a un usuario desactivado. Un `401` ahí es el sistema funcionando.

### Dos hallazgos que esta PR **declara y no arregla**

**1 · La quinta condición marca en rojo un despliegue sano.** Y lo útil no es el defecto, sino **dónde no cabe el arreglo**: el rol `jbg_ai` recibe `permission denied for table PointOfSales`, así que ni `health_report.py` ni el bloque de `verify.sh` que corre dentro del contenedor pueden leer la actividad de la tienda. La decisión D9 de C41 —contar contra lo que aparece en la proyección— **está impuesta por los permisos y no sólo elegida**. Quedan tres vías en `DEFERRED_TASKS.md`. Y refuta el `qa.md` de C41, que vio este mismo `1` y escribió que fallar «es lo correcto».

**2 · El panel avisa en `CRITICAL` de un modelo que este entorno no puede tener.** El catálogo sintético tiene **0 fotos de 1.200 productos**, así que el reconocimiento de imagen no tiene material del que aprender. Son **dos rojos en la misma pantalla** y ninguno señala nada roto; el segundo es funcionalidad del MVP, no del Proyecto Final.

### Predicciones refutadas, que es parte del valor de la pasada

| Se creía | Se midió |
|---|---|
| Las siete condiciones en verde | **Seis**, y la séptima falla por estricta |
| Dos ejecuciones de CI | **Cuatro** — el par `pull_request` y el par `push` |
| La CI de frontend publicaría resultado | **Nunca había corrido**: moría en un lint imposible |
| Existían `admin` activo y tres operarios | **Dos** cuentas `demo.*` y `admin` desactivada |
| La sonda del agente daría `aclaracion` | `presupuesto_reloj`: en frío el enrutador revienta su reloj de 2 s tardando 5.278 ms |

La predicción sobre la proyección **sí se confirma** —de ~115 veces el techo a `stale: false`—, con dos matices: la cura es del drenaje **incremental** (`last_full_sync_at` sigue en el 22 de septiembre) y **el registro del despliegue no la vio**, porque el informe se cachea 10 s y el drenaje de arranque necesitó dos intentos.

### Limitación de método, dicha y no dada por vista

**La sesión de verificación no tenía navegador, así que no hay capturas.** El recorrido ejercitó por HTTPS público los mismos *endpoints* que llaman las pantallas —y con eso quedan medidos el argumentario generado con citas, la abstención, los sustitutos, el aviso de agotado, el pivote, el ámbito global y el rechazo del enrutador—, pero **las cuatro tarjetas del centro de IA no se han visto**. La de salud de la IA **sí** quedó ejercitada por su ruta.

### Puntos de atención para quien revise

- La tabla de ficheros del §7 del informe cita rutas `openspec/changes/verify-demo-redeployment/…`, **sin** el prefijo del archivo: documenta el diff tal como se commiteó, cuando el change aún estaba activo. Es intencionado.
- El **recuento absoluto** de changes del PF discrepa entre documentos (42 en `epicas.md`, 41 en el plan, 44 carpetas en disco tras la frontera). Aquí sólo va el delta **+1/−1**, que sí es verificable; fijar el criterio de la frontera contable es **tarea declarada de C39b**.
- `deploy/demo/README.md` **no está en la matriz** de `config/doc-impact.json` de la skill `update-docs`, así que un cambio en el *runbook* no dispara su revisión. Hueco de cobertura, no desactualización.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-49"></a>
## #49 — C43 · La verificación del despliegue deja de juzgar mal un entorno correcto

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c43-add-shop-activity-projection` → `ai-eng` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/49 |

### Descripción

## Qué arregla

**La verificación posterior al despliegue deja de juzgar mal un entorno correcto.** Dos defectos de
la misma familia, descubiertos por C39a-bis, y van juntos porque el segundo es **requisito previo**
del primero.

El despliegue `36322635852` del 2026-09-27 construyó, publicó las dos imágenes, actualizó `IMAGE_TAG`
y **falló** con una sola causa:

```text
[verify] FAILED:
  - 1 point(s) of sale hold no assigned row in the projection; assisted search answers 503 for each of them
```

**El entorno estaba sano.** Las otras seis condiciones pasaban. El punto de venta señalado es
`HT-ARTRUTX` / «Hotel Cap d'Artrutx», cerrado **a propósito** desde el mundo sintético de C10, único
de los doce, que conserva sus 144 filas con la asignación retirada — exactamente lo que debe pasarle
al surtido de una tienda que cerró. El falso positivo llegaba además en rojo a la tarjeta del
administrador, así que arreglar sólo `verify.sh` no habría bastado.

## Por qué no cabía donde parecía

Comprobado, no supuesto: el rol con el que corre el servicio de IA responde `permission denied for
table PointOfSales`. Ni `health_report.py` ni el bloque de `verify.sh` que corre **dentro** de
`jbg-demo-ai` pueden leer la actividad de la tienda, así que la decisión D9 / Q-5 de C41 estaba
**impuesta por los permisos** y no sólo elegida.

**Vía B2:** `ai.pos_shop` en el esquema `ai`, poblada por un *feed* nuevo sin cursor.

Las dos alternativas, descartadas con motivo:

- **Columna `is_shop_active` en `ai.pos_projection`** — se quedaría rancia **para siempre**. El *feed*
  es incremental por *keyset* sobre el *watermark* de la fila de inventario, y si una tienda cambia de
  estado **ninguna fila de `Inventories` se toca**: el *watermark* no se mueve y el incremental no
  reemite nada. El `aggregateHash` tampoco lo vería, porque digiere pares `(PointOfSaleId, ProductId)`.
- **`GRANT SELECT` a `jbg_ai`** — viola el requisito vivo de `pos-projection` y cruza la frontera de
  esquemas que C17 dibujó adrede.

## Qué entra

| | |
|---|---|
| `ai.pos_shop` | una fila por tienda; revisión de Alembic **aditiva** sobre `d7c4e91b25a0`. **Sin migración de EF Core** |
| `GET /api/ai/index-feed/pos-shops` | retrato **completo**, sin cursor ni paginación, con el `join` a `PointOfSales` que el *feed* de disponibilidad no tiene |
| Drenaje nuevo | siempre completo, en una transacción, **antes** del de disponibilidad en cada pasada del planificador |
| `shops_without_scope` | contado contra tiendas **activas**, con `NOT EXISTS` y las tiendas **a la izquierda** |
| Quinta condición de `verify.sh` | lee el número nuevo, **falla con `ai.pos_shop` vacía**, y espera a que los drenajes reporten antes de sondear |
| `failed_pages` | desglosado **por *feed***: las 66 filas de `catalog` dejan de ser invisibles |

**Sin cursor es la decisión, no una simplificación.** Un *feed* por *keyset* sólo puede decir lo que
cambió, así que una tienda **retirada** del negocio no emite nada y su fila sobreviviría para siempre.
Sólo un retrato completo permite retirar lo que ya no está.

**La condición falla con la tabla vacía, y esa mitad es la que se olvida.** `alembic upgrade head`
corre a mitad de `deploy.sh`, así que `ai.pos_shop` nace vacía en una ventana por la que pasa cada
redespliegue — y contar tiendas-sin-surtido sobre una tabla vacía da cero y **pasa**. Sería la cuarta
instancia de la familia que este change cierra (índice vacío en C34, proyección vacía en C41, corpus
vacío en C39a), introducida precisamente por el arreglo de la tercera.

## Qué NO se toca

`frontend/` *(la línea roja desaparece porque el número pasa a ser correcto)* · el DTO de .NET del
informe de salud · el *feed* `pos-availability` en ninguna de sus piezas · `ai-service/openapi.json`
· ninguna ruta bajo `/v1` · ninguna migración de EF Core. **Comprobado sobre el propio diff.**

El `null` con la tabla vacía viaja limpio hasta el panel sin tocar nada, porque `int?` →
`number | null` → `?? 0` ya recorren toda la cadena.

## Medido

Reproducido **contra la base desplegada**, no dado por bueno:

```text
recuento viejo   points_of_sale=12  scoped=11  shops_without_scope=1   -> FALLA
recuento nuevo   active=11          active_without_scope=0            -> PASA
la tienda        HT-ARTRUTX | Hotel Cap d'Artrutx | IsActive = f
ai.sync_failure  catalog|66
```

Y de punta a punta en local, con el API sirviendo el *feed* de verdad: 12 ítems con una sola
`isActive:false` → `written=12 removed=0 active=11` → informe real con `shops_without_scope: 0` →
**el bloque real de `verify.sh`, extraído del guión y ejecutado, no da ningún fallo**.

Trece casos de la quinta condición, incluido el de imagen anterior a C43 (tolerada como desfase de
versión) y el de tabla vacía (falla). Herramienta re-ejecutable en la ficha archivada.

**Higiene:** drenaje completo contra el entorno desplegado —`upserted=6050 soft_deleted=670 pages=34
failed_pages=0`—, que cura `last_full_sync_at` (parado desde el 22 de septiembre) y confirma
**deriva cero** por tres vías que concuerdan: el `aggregate hash` idéntico antes y después, el
recuento de filas sin moverse (6.720) y la aritmética exacta (6050 + 670 = 6720).

## Suites

| Suite | Línea base | Al cierre |
|---|---|---|
| `ai-service` | 1.664 · **0** fallidos | **1.687 · 0 fallidos** |
| Backend | **49** de 1.408 | **49** de **1.415** |
| Frontend | **113** de 959, 14 de 63 ficheros | **114** de 959, **14** de 63 |

Comparado **por nombre**, no por recuento. En el backend seis aparecen y seis desaparecen, todas en
`InventoryIntegrationTests` salvo `ProductsControllerTests.Update_WithValidData_ShouldReturnUpdatedProduct`,
que **pasa al ejecutarse sola** — dependencia de orden, no regresión, y coherente con añadir una clase
a una colección que comparte base de datos. En el frontend el nombre nuevo vive en un fichero que ya
estaba en rojo, en un árbol donde **este change no toca ni un fichero**. **Cero nombres nuevos en el
área propia:** las 30 pruebas de `AiIndexFeed*` pasan.

`openspec validate --all --strict`: **0 failed**.

## Registro

Cierra **dos** de las cuatro fichas diferidas de C39a-bis y hace la mitad barata de una tercera. Pone
un **sello fechado** en el `qa.md` archivado de C41 —que vio este mismo `shops_without_scope: 1` y
escribió que «fallaría el despliegue, que es lo correcto»— **sin reescribirlo**: la casa conserva las
fichas archivadas como registro.

## Y dónde se para

**`demo` no se toca en esta PR.** La verificación de extremo a extremo **es** el despliegue, y ocurre
al mergear `ai-eng` → `demo`, que es una decisión del responsable. La confirmación de que la ejecución
concluye `success` y de que el panel ya no pinta la línea roja **la recoge C39b**. No se abre un
C43-bis.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-50"></a>
## #50 — Pone la demo al día: C39a-bis y C43 — el despliegue deja de fallar por un entorno sano

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `ai-eng` → `demo` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/50 |

### Descripción

> **Esta PR despliega.** Al mergearla, el *push* a `demo` dispara `deploy-demo.yml`: reconstruye
> **las dos imágenes**, las publica, actualiza `IMAGE_TAG` y ejecuta `verify.sh` dentro del
> anfitrión. No es un merge de documentación.

`demo` lleva **14 commits de retraso** desde el 2026-09-22. Esta PR la pone al día con `ai-eng`, y lo
que trae son **dos changes completos** —C39a-bis y C43— más el arreglo de *lint* que los precede.

## Qué debe pasar al mergear

El despliegue anterior (`36322635852`) terminó en **`failure`**, y por una única causa que **no era
del entorno**. Esta PR la arregla. La secuencia esperada:

1. `alembic upgrade head` aplica `e2f81a6c4b93` y crea **`ai.pos_shop`** — vacía, con el contenedor
   de IA ya arrancado.
2. El drenaje de arranque la llena: **doce tiendas, once activas**.
3. `verify.sh` **espera** a que los drenajes reporten (techo 180 s, sondeo cada 5 s) y sólo entonces
   sondea.
4. La quinta condición da **0 tiendas activas sin surtido**.
5. **La ejecución concluye `success`** — la primera desde el 22 de septiembre.

## Por qué el despliegue anterior figura en rojo, y por qué el entorno estaba bien

```text
[verify] FAILED:
  - 1 point(s) of sale hold no assigned row in the projection; assisted search answers 503 for each of them
```

Ese `1` es `HT-ARTRUTX` / «Hotel Cap d'Artrutx», **cerrada a propósito** desde el mundo sintético de
C10 y única de las doce, que conserva sus 144 filas con la asignación retirada — exactamente lo que
debe pasarle al surtido de una tienda que cerró. La quinta condición contaba puntos de venta sin
surtido **sin preguntar si la tienda estaba activa**, así que leía esa corrección como una avería. El
mismo falso positivo llegaba en rojo a la tarjeta del administrador.

Medido contra la propia base desplegada:

```text
recuento viejo   points_of_sale=12  scoped=11  shops_without_scope=1   -> FALLA
recuento nuevo   active=11          active_without_scope=0            -> PASA
```

## Los dos changes que van dentro

| | |
|---|---|
| **C39a-bis** `verify-demo-redeployment` | Verificó el entorno desplegado recorrido a recorrido y **dejó el entorno con cuatro cuentas** —un administrador y un operario por tienda—. Es quien encontró los dos defectos que C43 arregla |
| **C43** `add-shop-activity-projection` | `ai.pos_shop` en el esquema `ai`, un *feed* nuevo sin cursor, el recuento contra tiendas **activas**, y la espera al drenaje en `verify.sh` |

Y `0c9bb68`, que ignora la caché de Vite en el *lint* — el fichero que, estando fuera del
`paths-ignore`, hace que este merge despliegue aunque el resto fuera documentación.

## Lo que cambia en el entorno desplegado

- **Esquema:** una tabla nueva, `ai.pos_shop`. Revisión **aditiva**, con `downgrade` que no deja
  rastro. **Ninguna migración de EF Core** — `PointOfSales.IsActive` ya existía.
- **Imagen de .NET:** una ruta nueva, `GET /api/ai/index-feed/pos-shops`, bajo la misma clave
  `X-Index-Feed-Key`. **El *feed* `pos-availability` no se toca**: ni su cursor, ni su página de 200,
  ni su `aggregateHash`.
- **Imagen de IA:** el drenaje de tiendas enganchado al planificador que ya existía, y el recuento del
  informe de salud. **Ninguna ruta bajo `/v1`** y `openapi.json` **byte a byte igual**.
- **Frontend:** **nada**. La línea roja de la tarjeta desaparece porque el número pasa a ser correcto,
  no porque se edite la plantilla.
- **Datos:** ninguna pérdida. `up -d` recrea contenedores y **no** volúmenes; el certificado y
  `jbg-demo-pgdata` sobreviven.

## Si la verificación vuelve a fallar

| Síntoma | Qué significa |
|---|---|
| `knows of no active point of sale` | `ai.pos_shop` quedó vacía: el drenaje de tiendas no llegó a correr. **Es un fallo verdadero**, no el falso positivo de antes — la condición está escrita precisamente para no pasar en vacío |
| `N ACTIVE point(s) of sale hold no assigned row` | Ahora sí son tiendas **abiertas** sin surtido. Fallo real |
| Nota `other feeds carry recorded failures` | Informativa, **no falla**: son las 66 filas de `catalog` en `ai.sync_failure`, que hasta ahora nadie podía ver |

La séptima condición gasta **una llamada real al proveedor** por despliegue, y la cuota es del orden
de una petición por minuto.

## Verificación previa

Reproducido contra la base desplegada, y medido de punta a punta en local con el API sirviendo el
*feed*: `written=12 removed=0 active=11` → informe real con `shops_without_scope: 0` → **el bloque
real de `verify.sh`, extraído del guión y ejecutado, sin ningún fallo**. Trece casos de la quinta
condición, incluido el de tabla vacía (falla) y el de imagen anterior a C43 (tolerada).

Higiene ya aplicada al entorno: drenaje completo de `pos-availability` —`upserted=6050
soft_deleted=670 pages=34 failed_pages=0`—, que curó `last_full_sync_at` (parado desde el 22 de
septiembre) y confirmó **deriva cero**.

Suites al cierre, comparadas **por nombre**: `ai-service` **1.687 · 0 fallidos**; backend **49 de
1.415** con la rotación confinada a `InventoryIntegrationTests`; frontend **114 de 959** en los mismos
14 ficheros, en un árbol que estos cambios no tocan. **Cero nombres nuevos en el área propia.**
`openspec validate --all --strict`: **0 failed**.

## Lo que esto NO cierra

La confirmación de que la ejecución concluye `success` y de que el panel ya no pinta la línea roja
**se recoge en C39b**, que es documentación y no vuelve a desplegar. **No se abre un C43-bis.**

Sigue abierta, y es deliberado: la alerta `CRITICAL` de reconocimiento de imagen. El catálogo
sintético tiene **0 fotos de 1.200 productos**, así que no puede existir modelo; es funcionalidad del
MVP y se declara en el guion de la demo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-51"></a>
## #51 — Arregla el drenaje de arranque: reintenta por drenaje, no por pasada

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c43-fix-boot-drain-retries-both-drains` → `ai-eng` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/51 |

### Descripción

> **Arregla un defecto que C43 introdujo y que su propia condición encontró el mismo día.** El
> entorno desplegado **ya está correcto**; esto impide que el **próximo** arranque lo deje a medias.

## Qué pasó

El despliegue `36343020047` construyó las dos imágenes, las publicó, actualizó `IMAGE_TAG`, desplegó
— y **falló en la verificación**:

```text
[verify] waited 180s for the start-up drains to report
"active_points_of_sale": 0,
"shops_without_scope": null,
"synced_at": "2026-09-27T19:07:08.851185+00:00"     <- la proyección SÍ se drenó
[verify] FAILED:
  - the AI service knows of no active point of sale; ai.pos_shop is empty, so the count of
    shops without assortment is vacuous and proves nothing about this environment
```

**La condición (a) hizo exactamente su trabajo.** Es la que C43 añadió para que una tabla vacía no
pasara en vacío, y lo primero que cazó fue un fallo del propio C43. Sin ella el despliegue habría
concluido `success` con la tabla vacía y nadie mirando.

## La causa

```text
19:07:07,442  boot_drain attempt=1
19:07:07,644  WARNING pos_shop_scheduler feed_not_configured error=POS shops feed is unavailable
19:07:08,857  pos_sync_scheduler drained pages=1 upserted=1 soft_deleted=0 failed_pages=0
```

El drenaje de tiendas falló **por 1,2 segundos** —el lado .NET aún no servía el *feed*—, y el de
disponibilidad salió bien un segundo después. `_boot_drain` reintentaba mientras `drain_pass(...)`
devolviera `None`, y **`drain_pass` devuelve el resultado del de disponibilidad**: uno de los dos
bastó para terminar el bucle de los dos. No hubo intento 2, y `ai.pos_shop` se quedó vacía hasta el
tic de 600 s — muy por detrás de los 180 s que la verificación espera.

**Es la misma familia de defectos que C43 cierra, un nivel más arriba:** *parte del trabajo salió
bien* leído como *el trabajo salió bien*.

## El arreglo

`_boot_drain` reintenta **por drenaje**: lleva la cuenta de cuál ha corrido y reintenta sólo el que
falta, conservando el orden —tiendas primero—, de modo que el que ya salió bien no se repite. Y el
aviso de agotamiento declara el resultado de cada uno, porque «se agotaron los intentos» sin decir de
cuál es la mitad de la información — y es la mitad que habría hecho evidente esto al leer el registro.

Con los reintentos en 0, 5, 20 y 65 s, el intento 2 habría caído a las 19:07:12, con el API ya
sirviendo desde las 19:07:08.

## Por qué no lo cazó nada antes

`test_the_boot_drain_runs_a_whole_pass` da por buenos los dos drenajes, así que nunca ejercitó el caso
mixto. Y **la spec no lo pedía**: decía que los dos drenajes corren al arrancar y en orden, pero no
que el **reintento** cubriera a los dos. Esta PR añade ese escenario, que es lo que permitió que el
defecto pasara la revisión.

Tres tests nuevos: uno reproduce literalmente la secuencia del despliegue, otro su espejo —para que el
arreglo no quede cojo de un lado— y otro comprueba que el agotamiento registra ambos resultados.

**Y se aísla un test de C41:** `test_the_boot_drain_retries_until_the_feed_answers` dejaba
`run_pos_shop_drain` sin sustituir, así que alcanzaba el drenaje real y fallaba por su cuenta; con el
arreglo eso cambiaba el número de intentos y el test dejaba de afirmar lo que su nombre dice.

## Estado del entorno

**Correcto, y se curó solo** — lo que confirma que el mecanismo de C43 está bien y que sólo fallaba el
arranque:

```text
19:17:08,912  pos_shop_scheduler drained written=12 removed=0 active=11
```

```json
{ "active_points_of_sale": 11, "shops_without_scope": 0, "points_of_sale": 12,
  "status": "ok", "stale": false, "failed_pages_by_feed": {"catalog": 66} }
```

**El falso positivo original está resuelto.** Lo que queda es que el arranque no vuelva a dejar la
tabla a medias, que es lo que arregla esta PR.

## Verificación

`ai-service`: **1.690 pasados · 0 fallidos** (línea base de C43: 1.687 · 0). `openspec validate
--all --strict`: **0 failed**. No se toca el *feed*, ni el repositorio, ni el informe de salud, ni
`verify.sh`.

**Requiere redespliegue**, porque cambia la imagen de IA. Lo que debe verse en el próximo arranque es
`boot_drain attempt=1 shops_pending=True availability_pending=True`, y si el *feed* aún no responde,
un `attempt=2` con `shops_pending=True availability_pending=False`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-52"></a>
## #52 — Arregla el drenaje de arranque que dejó ai.pos_shop vacía en el despliegue anterior

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `ai-eng` → `demo` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/52 |

### Descripción

> **Esta PR despliega.** `ai-service/src/jbg_ai/indexing/scheduler.py` queda fuera del
> `paths-ignore`, así que el *push* a `demo` reconstruye las imágenes y vuelve a ejecutar
> `verify.sh`. Son **2 commits** y tocan **sólo el planificador de `jbg-ai`**.

Arregla el defecto que el despliegue anterior (`36343020047`) destapó, y que era **de C43, no del
entorno**.

## Qué arregla

`_boot_drain` reintentaba mientras `drain_pass(...)` devolviera `None`, y `drain_pass` devuelve el
resultado del drenaje **de disponibilidad**. Así que uno de los dos bastaba para terminar el bucle de
los dos:

```text
19:07:07,442  boot_drain attempt=1
19:07:07,644  WARNING pos_shop_scheduler feed_not_configured   ← el API aún no servía
19:07:08,857  pos_sync_scheduler drained pages=1 upserted=1    ← 1,2 s después ya sí
```

El drenaje de tiendas falló **por 1,2 segundos**, no hubo intento 2, y `ai.pos_shop` se quedó vacía
hasta el tic de 600 s — muy por detrás de los 180 s que la verificación espera. Ahora el reintento es
**por drenaje**: sólo se reintenta el que falta, y el que ya salió bien no se repite.

## Aviso importante: esta vez el tick verde NO prueba el arreglo

`ai.pos_shop` **ya tiene sus 12 filas** —el tic de las 19:17 las escribió— y `up -d` recrea
contenedores pero **no destruye volúmenes**. O sea que la quinta condición pasará **aunque el arreglo
no funcionase**, simplemente porque la tabla ya está llena de antes.

**Lo que prueba el arreglo es el registro del planificador, no el resultado del despliegue.** Lo que
hay que ver en el arranque:

```text
boot_drain attempt=1 shops_pending=True availability_pending=True
```

y, **si el *feed* aún no responde**, un segundo intento que persiga sólo lo que falta:

```text
boot_drain attempt=2 shops_pending=True availability_pending=False
```

Si el *feed* responde a la primera —que es lo más probable, porque ahora el contenedor de .NET lleva
rato en marcha— no habrá `attempt=2` y el arreglo quedará sin ejercitarse en producción. **No es un
problema**: está cubierto por tres tests que reproducen la secuencia exacta, incluido su espejo. Lo
digo para que nadie lea el verde como una demostración de algo que no demuestra.

## Estado actual del entorno, para comparar después

```json
{ "active_points_of_sale": 11, "shops_without_scope": 0, "points_of_sale": 12,
  "status": "ok", "stale": false, "failed_pages_by_feed": {"catalog": 66} }
```

**El falso positivo que motivó C43 está resuelto.** Esta PR no repara un entorno roto: impide que un
arranque futuro lo deje a medias y vuelva a marcar en rojo un despliegue que por lo demás está bien.

## Qué cambia en el entorno

- **Imagen de IA:** sólo `_boot_drain`. Ningún cambio de esquema, ninguna migración nueva, ninguna
  ruta.
- **Imagen de .NET:** se reconstruye porque el *workflow* construye las dos, pero **no cambia ni un
  fichero de `backend/src`**.
- **Datos:** intactos. Ni el certificado ni `jbg-demo-pgdata` se tocan.

## Verificación previa

`ai-service`: **1.690 pasados · 0 fallidos** (línea base de C43: 1.687 · 0 — tres tests nuevos).
`openspec validate --all --strict`: **0 failed**.

Los tres tests nuevos: uno reproduce literalmente la secuencia del despliegue, otro su espejo —para
que el arreglo no quede cojo de un lado— y otro comprueba que al agotarse los intentos el registro
dice **cuál** de los dos no llegó a correr. Se aisla además un test de C41 que dejaba
`run_pos_shop_drain` sin sustituir y por tanto alcanzaba el drenaje real.

La spec de `pos-projection` gana el escenario que le faltaba — que el reintento de arranque cubra a
cada drenaje por separado — que es precisamente lo que permitió que el defecto pasara la revisión.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-53"></a>
## #53 — Cierra el Proyecto Final: entregable, criterio de recuento y evidencias (C39b)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `c39b-finalize-pf-readme-and-evidence` → `ai-eng` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/53 |

### Descripción

**C39b, el último change del Proyecto Final.** Al mergearse, la cola de changes queda vacía: `openspec/changes/` sin ningún change activo y `openspec validate --all --strict` en **65 passed, 0 failed**.

**No toca una línea de código de producto.** Ni backend, ni frontend, ni `ai-service` salvo un artefacto JSON que escribe el propio comando `--rescore`. Sin migraciones, sin mover `ai-service/openapi.json` —comprobado—, sin variables de Terraform.

---

## Lo primero que arregla es una cifra que nadie podía comprobar

Circulaban **cuatro** recuentos distintos: «40 archivadas», «43» y «44» en `Documentos/epicas.md`, y «74 archivados · 32 del MVP · 41 del PF» en la ficha del plan. **No se contradecían por descuido: contaban unidades distintas sin decir cuál.**

El criterio queda fijado y medido contra el disco, con **las dos unidades declaradas**:

| Unidad | Cifra | Cómo se comprueba |
|---|---:|---|
| Directorios en `openspec/changes/archive/` | **79** | `ls openspec/changes/archive/ \| wc -l` |
| …del MVP | **33** | los 32 con fecha `< 2026-08-03` **más** `barcode-qr-scanning`, del MVP **por contenido** |
| …del **Proyecto Final** | **46** | los 47 posteriores **menos** ése |
| Fichas de la tabla maestra, todas archivadas | **45** | las 45 filas con slug del §2 del plan |

La unidad canónica es **el directorio**, porque es lo único que un lector reproduce en un comando **sin leer el plan** — que es precisamente el documento cuyas cifras estaban en duda. La frontera es la fecha, **con una excepción nombrada**: una excepción auditable, frente a una regla de fecha a secas que daría 46 a cualquiera que la aplicase.

**Y el cruce entre las dos unidades destapó un defecto de la propia tabla maestra**: `C40_FIX` no tenía fila y aparecía una sola vez, en prosa. Eso obligaba a que **todo recuento hecho contra esa tabla se quedara corto en uno** y se corrigiera después «sumándole `C40_FIX`» — que es literalmente lo que la nota de recuento de `epicas.md` tuvo que escribir para cuadrar. **Se le añade la fila**, y con ella la distancia entre las dos unidades pasa a tener **un solo nombre**: `fix-boot-drain-retries-both-drains`, el seguimiento de C43, un directorio de archivo sin ficha propia.

Los 79 directorios son **76 slugs distintos** —tres pares duplicados, **los tres del MVP**—, y se **declaran en vez de deduplicarse**: reordenar el archivo histórico para que un total sume redondo es lo contrario de hacer una cifra verificable.

## Las tres tareas que sobrevivían a C38, cerradas sin gastar cuota

`agent_sweep --rescore` recalcula todos los agregados de una pasada ya escrita **sin llamar al proveedor ni a la base de datos**.

- **El éxito de tarea queda definido antes de mirar cifras**: expectativa de herramientas cumplida —todas las exigidas, alguna de las admitidas, ninguna de las prohibidas— y sin discrepancia declarada. Con el detalle de **qué queda fuera del veredicto y por qué**: motivo de parada, iteraciones y grupos existen en cada fila pero ningún escenario tiene expectativa escrita sobre ellos, así que admitirlos ahora sería definir el criterio a partir de los datos.
- **La tabla, por escenario**: **17 de 20**, con `C14` y `C17` nombrados y `C19` contado aparte por traer su discrepancia declarada de antes.
- **No se publica una tasa porcentual, y el motivo es medido**: puntuando la pasada de C32b y la de C42 contra el fichero de escenarios de hoy, el veredicto coincide en 17 de 20 y **los vuelcos reales son 2 de 20**. Con ese ruido, un «85 %» sería una precisión fingida.
- **El validador .NET** pasa a **limitación declarada con cifra esperada cero**, porque es un espejo de la puerta numérica que Python ya aplica al mismo texto — con los tres datos que lo sostienen y su vía de cierre, incluido el criterio de aceptación que **no** vale («atrapa algo»).

## La taxonomía, y lo que destapa en una sección congelada

Once métodos, una fila cada uno, **las de recuperación todas bajo una sola procedencia** —la tabla final de C25, golden set `1:198c4af44506`—, porque la regla de `retrieval-evaluation` es que dos corridas con procedencia distinta se reportan como no comparables en vez de compararse. Con dos advertencias que no se pueden quitar: **CAG es una fila fechada y no reproducible bit a bit**, y **`v2-hibrido` es histórica y no re-ejecutable** desde que `C25bis` retiró su composición del código.

Al aplicar esa regla aparece que el **`### 1.2` del README** dice que el acierto *«sube de 0,603 a 0,740»* **mezclando los dos conjuntos dorados**: el 0,603 es de C24, y bajo el conjunto de C25 esa misma configuración mide **0,673**. **Es una sección congelada**, así que se **reporta con su texto propuesto y no se edita**.

## Las secciones congeladas se respetan, y se comprueba

`## 0`, `### 1.1`, `### 1.2`, `### 1.3`, `## 5` y `## 6` están intactas **byte a byte** contra `ai-eng`. Lo desfasado en ellas va al **anexo A del informe** con el texto exacto propuesto: el «(en desarrollo)» del `### 1.2`, el salto de nDCG de arriba, y la **autoría de la ficha `## 0`**, que no es la del historial de git y choca con el nombre del *tag* acordado.

Editado sólo lo editable: `### 1.4` —arranque de los tres servicios con sus puertos, y las tres suites **en serie y leyendo la línea de resumen**—, `## 2` completo, `## 3.2`, `## 4` —con las tres rutas de *feed* y `GET /api/ai/health`— y `## Documentación adicional`.

## Tres limitaciones declaradas y no arregladas, cada una con su vía de cierre

- **La alerta `CRITICAL` de reconocimiento de imagen.** 0 fotos de 1.200 productos: funcionalidad **del MVP y no del Proyecto Final**, así que la alerta más visible del panel no es ni de lo que se evalúa. Se cierra por la **vía 1** —declararla en el guion—, y al escribirlo se descubre que **no es una tarjeta sino un aviso que salta al iniciar sesión como administrador**, diez segundos y una vez por sesión: entra en cámara si nadie la anticipa.
- **El pivote del agente inalcanzable por nombre**, con el experimento que lo establece y el arreglo costado.
- **La deriva de rama**, que estrena entrada en `DEFERRED_TASKS.md`. Hoy **mide cero** —`IMAGE_TAG` y `git rev-parse origin/demo` coinciden—, y eso es lo que la hace incómoda: la comprobación que faltaba cabe en una comparación de cadenas y nadie la había escrito, que es por lo que la deriva pudo durar cinco semanas.

## Y lo que NO se ha verificado se declara, nombre a nombre

El **dato** de la tarjeta de administración sí: `shops_without_scope: 0`, leído en vivo desde dentro del anfitrión por SSM contra el `/health` interno de `jbg-ai`, sin necesitar credencial de usuario. **El renderizado, no**: una sesión no tiene navegador, y «el número que pinta la línea es cero» y «la línea no está en la pantalla» **no son la misma afirmación**. Van como dos frases distintas.

Tampoco: el vídeo —se entrega el **guion**, siete tramos con su cuenta y su consulta literal—, el `docker compose up` en máquina limpia, ni el certificado remedido desde el anfitrión. Anexo B del informe.

## Especificaciones

- **`pf-delivery-package`** (nueva, 7 requisitos): el contrato del entregable. El recuento con su unidad y sus excepciones, la taxonomía con cifra medida **o declaración de no medida** por fila, las secciones congeladas que se reportan, cada limitación con su vía de cierre, el guion, la validación que se declara en vez de darse por vista, y el *tag* que se propone.
- **`retrieval-evaluation`** (+1 requisito): el éxito de tarea del agente como veredicto definido, recomputable sin proveedor y publicado con sus fallos nombrados.

El archivado deja el `## Purpose` de la capability nueva en `TBD` y lo dice: **se ha escrito**, porque una spec viva con la sección presente y vacía es la clase de sync a medias que `--all --strict` no puede ver.

## Dos cosas encontradas de paso

- **`ai.pos_shop` no estaba en `Documentos/modelo-de-datos.md`**: C43 creó la tabla y la puesta al día de documentación no la llevó allí. Se encontró al comprobar que el `## 3` del README cuadrase con ese documento, que es lo que la regla de esa sección pide. **Fila añadida.**
- **Mergear este change a `demo` sí dispara un despliegue.** El filtro de rutas del flujo ignora `openspec/**`, `Documentos/**` y `**/README.md`, pero **no** `ai-service/**`, y el artefacto de `--rescore` vive ahí porque es donde el comando lo escribe por diseño. Tres minutos y ninguna imagen con contenido nuevo; es el fallo hacia el lado seguro que ese filtro declara buscar por ser una lista negra. **Queda escrito para que la decisión se tome sabiéndolo.**

## Comprobaciones

| | |
|---|---|
| `openspec validate --all --strict` | **65 passed, 0 failed** |
| Sintaxis de delta en specs vivas | **ninguna** |
| Changes activos tras archivar | **0** |
| Secciones congeladas del README | **intactas byte a byte** contra `ai-eng` |
| Enlaces relativos del change archivado | **ninguno** — sólo rutas entre comillas invertidas, así que no hay nada que repuntar |
| Enlaces relativos de los ficheros tocados | **0 rotos** |
| `ai-service/openapi.json` | **no se mueve** |
| Tres suites de tests | **no se miden, y se dice por qué**: no se compila ni ejecuta nada del producto, y ningún test lee `ai-service/evals/results/` |
| *Tag* y rama de entrega | **propuestos, no creados** — `git tag --list "v1.0-final*"` vacío |

🤖 Generated with [Claude Code](https://claude.com/claude-code)



---

<a id="pr-54"></a>
## #54 — Pone demo al día con ai-eng: cierre del Proyecto Final (C39b)

| | |
|---|---|
| Autor | `SValduezaL` |
| Estado | MERGED |
| Ramas | `ai-eng` → `demo` |
| Creada | 2026-09-27 |
| Integrada | 2026-09-27 |
| Original | https://github.com/skydr4g0n-it/joiabagur-pv/pull/54 |

### Descripción

Pone `demo` al día con `ai-eng` tras cerrar el Proyecto Final (C39b), para que la rama no vuelva a derivar — el defecto que C39a destapó y que dejó la demo **84 commits y cinco semanas** por detrás sin que nada lo dijera.

**Sólo documentación, con una excepción que dispara el despliegue y está declarada de antemano.** El filtro de rutas del flujo ignora `openspec/**`, `Documentos/**` y `**/README.md`, pero **no** `ai-service/**`, y este merge lleva un fichero ahí: `ai-service/evals/results/c32b-agent-sweep-17fbdd15a18c.rescore.json`, el artefacto que `agent_sweep --rescore` escribe **junto a su origen por diseño**.

Así que el despliegue se dispara. **Ninguna imagen cambia de contenido** —no hay código, ni prompt, ni corpus, ni paquete de despliegue en este diff—, cuesta unos minutos, y es el fallo hacia el lado seguro que ese filtro declara buscar por ser una lista negra en vez de una blanca. Asumido a propósito.

**Deriva antes de este merge: cero.** `IMAGE_TAG` en SSM (`sha-7d3a15ae…`) coincidía exactamente con `git rev-parse origin/demo`, comprobado el 2026-09-27. Esa comparación sigue sin estar automatizada y queda como entrada abierta en `openspec/DEFERRED_TASKS.md`, con la octava condición de `verify.sh` que la cerraría.

🤖 Generated with [Claude Code](https://claude.com/claude-code)



