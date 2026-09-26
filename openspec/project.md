# Project Context

## Purpose

**Sistema de Gestión de Puntos de Venta para Joyería** - An integral management system for a jewelry business operating across multiple points of sale (own stores and third-party locations like hotels). The application enables inventory management, sales registration, and product identification through AI-powered image recognition.

### Key Objectives
- Centralized product catalog with photo-based product identification
- Multi-location inventory tracking with Excel import capabilities
- Sales registration with AI image recognition (3-5 suggestions ordered by confidence)
- Role-based access (Administrator full access, Operator restricted to assigned locations)
- Optimized for mobile use by operators at points of sale
- Free-tier cloud deployment (AWS/Azure)

### MVP Scope (Phase 1)
10 Epics with 47 User Stories covering:
- **EP1**: Product Management (7 stories)
- **EP2**: Inventory Management (6 stories — includes assign/unassign products to POS)
- **EP3**: Sales Registration (4 stories — includes manual price override, cart & bulk checkout)
- **EP4**: AI Image Recognition (1 story)
- **EP5**: Returns Management (3 stories — multi-sale, partial, categorized)
- **EP6**: Payment Methods Management (3 stories)
- **EP7**: Authentication & User Management (6 stories)
- **EP8**: Points of Sale Management (5 stories — includes AllowManualPriceEdit config)
- **EP9**: Queries & Reports (4 stories)
- **EP10**: Jewelry Component Management (8 stories — master table, assignment, templates, margin reports)

---

## Tech Stack

### Backend
- **Runtime**: .NET 10
- **Framework**: ASP.NET Core Web API
- **Language**: C#
- **ORM**: Entity Framework Core
- **Database**: PostgreSQL 15+
- **Authentication**: JWT (JSON Web Tokens)
- **API Documentation**: Scalar (modern alternative to Swagger)
- **Logging**: Serilog — structured events, human-readable console in development and JSON under the production profile
- **Outbound HTTP**: typed `HttpClient` with `Microsoft.Extensions.Http.Resilience` (Polly v8). The AI gateway client (`IAiGatewayClient`, capability `ai-gateway-client`) is the reference implementation: named client per route family with its own circuit breaker, explicit pipeline rather than the standard preset, whitelist retry predicate, internal HS256 service token, and options validated at start-up
- **Architecture**: Monolithic with layered separation (Domain → Infrastructure → Application → API)

### Frontend
- **Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite
- **UI Template**: Metronic React (Layout 8 - sidebar navigation)
- **UI Components**: Radix UI, Tailwind CSS, Lucide React icons
- **Forms**: React Hook Form + Zod validation
- **Tables**: TanStack Table (React Table)
- **HTTP Client**: Axios/Fetch
- **State Management**: Context API (or Zustand if needed)
- **ML Framework**: TensorFlow.js / ONNX.js (client-side image recognition)

### AI Service (`jbg-ai`)
- **Runtime**: Python 3.11+
- **Framework**: FastAPI + Uvicorn (app factory, `docs_url` disabled)
- **Package Manager**: uv (`pyproject.toml` + `uv.lock`)
- **Configuration**: pydantic-settings with fail-fast on required env
- **Service Auth**: internal HS256 JWT (PyJWT); the .NET API is the only issuer
- **Contract**: frozen `/v1` surface versioned in `ai-service/openapi.json`
- **Persistence**: SQLAlchemy 2 (async) over psycopg 3, pgvector types, Alembic migrations in `ai-service/migrations/`
- **Schema ownership**: `ai` only for the `jbg-ai` runtime process. Host CLIs (C06a `scripts/catalog/`, C06b `python -m jbg_ai.data ingest`, C10 `python -m jbg_ai.data world ingest`) are the documented exception: they use `JPV_PG*` against local Docker and do not run inside the service container.
- **Connection pool**: capped at `DB_POOL_SIZE` (default 5) with no overflow; built lazily, so the service boots with no database
- **Runtime LLM**: LiteLLM (`litellm==1.98.0`) for C09 enrichment (`acompletion`) and C11 embeddings (`aembedding`). C14 retrieval constructs a distinct embed client with `max_attempts=1` and does not edit `indexing/embeddings.py`; since C21 that client is built **once per process** with a bounded LRU cache injected through the frozen module's existing constructor seam. `JPV_RAG_LLM_*`, `JPV_EMBEDDING_*`, `JPV_RETRIEVAL_DISTANCE_THRESHOLD` (default 0.65), `JPV_QUERY_EXPANSION_ENABLED` (default true, C20), the fusion settings `JPV_RRF_K` / `JPV_BRANCH_DEPTH` / `JPV_BRANCH_WEIGHT_LEXICAL` / `JPV_BRANCH_WEIGHT_VECTOR` (C21 and C25; C25bis retired the per-list weights and the composition selector, so a deployment that still exports them has no effect) and the C22 prefilter settings `JPV_POS_PREFILTER_ENABLED` (default true) / `JPV_POS_PROJECTION_MAX_AGE_SECONDS` (default 3600) optional at boot; embed key and `DATABASE_URL` required at call time on real retrieval. Distinct from `JPV_CATALOG_LLM_*` (C06b CLI). No fallback from embedding key to RAG key.

### Infrastructure
- **Containers**: Docker, Docker Compose (development)
- **CI/CD**: GitHub Actions
- **Repository**: GitHub
- **Cloud**: AWS (EC2 + Docker bundlado + nginx, RDS PostgreSQL, S3, ECR, SSM Parameter Store; GitHub OIDC para deploy)
- **Entorno de demostración (C17)**: cuenta AWS **separada** de la de la tienda, con estado de Terraform propio (`terraform/demo/`), cuatro contenedores tras Caddy con TLS automático, PostgreSQL con pgvector en contenedor en lugar de RDS, y el servicio de IA **sin puertos publicados**. Ni infraestructura, ni permisos, ni datos en común con producción. Runbook en `deploy/demo/README.md`
- **Target**: Free-tier optimized deployment
- **Locale**: es-ES, currency EUR (€)

### Testing Stack

**Backend:**
- Test Framework: xUnit 2.9.x
- Mocking: Moq 4.20.x
- Assertions: FluentAssertions 7.x
- Test Data: Bogus 35.x
- Integration Tests: Testcontainers 4.x (PostgreSQL)

**Frontend:**
- Test Runner: Vitest 4.x
- Component Testing: React Testing Library 16.x
- User Events: @testing-library/user-event 14.x
- API Mocking: MSW (Mock Service Worker) 2.x
- E2E Testing: Playwright 1.x
- DOM Environment: jsdom 25.x

**AI Service (`jbg-ai`):**
- Test Framework: pytest 9.x
- HTTP Client: httpx (FastAPI `TestClient`)
- No real LLM, embedding or RDS calls; stub tests block socket connections
- Database tests: testcontainers with `pgvector/pgvector:pg15`, a fresh database per test; skipped (not failed) when Docker is unreachable

---

## Project Conventions

### Code Style

**Backend (C#/.NET):**
- Follow Microsoft C# coding conventions
- Use async/await for I/O operations
- Repository pattern for data access
- Service layer for business logic
- DTOs for API contracts
- FluentValidation for input validation
- Structured logging with Serilog

**Frontend (TypeScript/React):**
- Functional components with hooks
- TypeScript strict mode enabled
- Components colocated with tests (`component.tsx` + `component.test.tsx`)
- Services organized by domain module
- Custom hooks for reusable logic
- Prefer Metronic UI components over custom implementations

### Architecture Patterns

**Backend Layers (per Modelo C4):**
1. **Domain (Core)**: Entities, Value Objects, domain interfaces
2. **Infrastructure**: EF Core repositories, DbContext, migrations, File Storage Service
3. **Application (Services)**: Product Service, Sale Service, Inventory Service, etc.
4. **API (Controllers)**: REST endpoints, DTOs, middleware (JWT, CORS, logging)

**Frontend Modules (per Metronic analysis):**
- Auth Module (login, session, token management)
- Product Module (catalog, import, photos)
- Inventory Module (stock views, adjustments)
- Sale Module (registration, payment selection)
- Image Recognition Module (capture, ML inference, suggestions)
- Return Module (registration, history)
- Payment Method Module (configuration, assignment)
- Point of Sale Module (CRUD)
- User Module (management, assignments)
- Report Module (queries, filters)

**Shared Services:**
- File Storage Service (abstraction for local/S3/Blob)
- Stock Validation Service
- Payment Method Validation Service
- Excel Import Service

### Testing Strategy

**Backend Tests:**
- Nomenclature: `Method_Scenario_ExpectedResult` (e.g., `CreateSale_WithInsufficientStock_ShouldThrowException`)
- Structure: AAA (Arrange, Act, Assert)
- Minimum coverage target: 70%
- Unit tests for services and validators
- Integration tests with Testcontainers (PostgreSQL)
- JWT authentication tests for protected endpoints

**Frontend Tests:**
- Nomenclature: `should [behavior] when [condition]` (e.g., `should show error when API returns 401`)
- Prefer accessible queries (`getByRole`, `getByLabelText` over `getByTestId`)
- MSW for API mocking
- Playwright for E2E flows (authentication, CRUD operations)
- Minimum coverage target: 70%

**AI Service (`jbg-ai`) Tests:**
- Nomenclature: `test_<unit>_<scenario>_<expected>` (e.g., `test_health_returns_ok_with_version`)
- Test tree mirrors the `src/jbg_ai/` package; see `ai-service/tests/README.md`
- Injected fakes for LLM and embedding clients — never a real provider, API or RDS
- Markers: `db` (needs PostgreSQL with pgvector), `slow` (evaluation sweeps)

### Git Workflow

- **Main branch**: `master` (production-ready)
- **Integration branch**: `ai-eng` (AI final project work)
- **Feature branches**: `feature/[epic]-[description]`
- **Commits**: Conventional commits format
- **CI/CD**: GitHub Actions for build, test, and deploy

### OpenSpec Validation

- **Project gate**: `openspec validate --all --strict` must report `0 failed`. Use this exact form in Definition-of-Done items.
- **Single change in progress**: `openspec validate <change-name> --strict`.
- The bare form (`openspec validate`, with or without `--strict`) validates nothing and exits 1 — it is not a pass.

### Documentation

- **Language**: Technical documentation in English, User Stories and user-facing guides in Spanish
- **Tickets**: Written in English for code consistency
- **UI Language**: Spanish (es-ES)
- **Location**: `Documentos/` folder for all project documentation
- **User Stories**: `Documentos/Historias/HU-EP[X]-[NNN].md`
- **Work Tickets**: `Tickets/EP[X]/HU-EP[X]-[NNN]/T-EP[X]-[NNN]-[MMM].md`

#### Post-Implementation Documentation Update

After completing an OpenSpec change implementation (e.g., via `openspec-apply`), update the project documentation to reflect the new or modified capability. Review each file below and update only those affected by the change:

| File | Update when... |
|------|---------------|
| `Documentos/epicas.md` | Epic scope, user story list, or story counts changed |
| `Documentos/Historias/HU-EP[X]-[NNN].md` | A new user story is needed for the capability |
| `Documentos/modelo-de-datos.md` | Entity fields, relationships, or indexes changed |
| `Documentos/modelo-c4.md` | New components, containers, or integration points added |
| `Documentos/arquitectura.md` | Architectural patterns, layers, or cross-cutting concerns changed |
| `Documentos/Guias/*.md` | User-facing flows, validations, or FAQ entries affected |
| `README.md` (root) | Installation steps, architecture, data model, or documented API endpoints changed — technical sections only; the deliverable sections (0, 1.1–1.3, 5, 6) are frozen |
| `backend/README.md` | Endpoints, authorization matrix, environment variables, migrations, or test setup changed |
| `frontend/README.md` | Tech stack versions, npm scripts, or test setup changed |
| `ai-service/README.md` | `jbg-ai` contract, settings, layout, non-goals, or the change marker (C01, C02…) changed |
| `ai-service/tests/README.md` | The test tree gains a folder, a marker, or a shared helper in `tests/support/` |
| `scripts/catalog/README.md` | Offline catalog pipeline commands, `JPV_PG*`, seed or `generator_version` changed |
| `terraform/README.md` | AWS resources, variables, outputs, or `/jpv/prod/*` parameters changed |
| `openspec/config.yaml` | A fact restated in the condensed `context` block changed |

Run the `update-docs` command (skill replicated in `.agent/`, `.claude/`, `.codex/`, `.cursor/` and `.opencode/skills/update-docs/`) to detect which of these are affected by the latest committed and uncommitted changes, review them against the real code, and apply the updates after confirmation.

---

## Domain Context

### Business Domain
- **Industry**: Jewelry retail
- **Operations**: Multiple points of sale (own stores + third-party locations like hotels)
- **Key Challenge**: Product identification accuracy - jewelry items can be difficult to distinguish
- **Solution**: AI-powered image recognition with manual confirmation

### Key Entities
- **Product**: SKU (unique), name, description, price, collection (optional)
- **ProductPhoto**: Multiple reference photos per product for ML training
- **ProductPhotoEmbedding**: MobileNetV2 feature vector (1280 dims) per product photo, stored as JSON `text`. Backs cosine-similarity recognition, which runs in the browser — hence no `pgvector` here
- **PointOfSale**: Store locations with assigned operators, payment methods, and manual price edit policy (`AllowManualPriceEdit`)
- **User**: Admin (full access) or Operator (restricted to assigned locations)
- **Sale**: Transaction with price snapshot (official or manual override), payment method, optional photo, override audit fields (`PriceWasOverridden`, `OriginalProductPrice`), optional `BulkOperationId` for cart checkout grouping, optional `SearchEventId` attributing the sale to the assisted search it came from (`ON DELETE SET NULL`)
- **SalePhoto**: Optional photo attached to a sale (image recognition or manual)
- **Inventory**: Stock quantity per product per location. `IsActive` flag = product assigned to POS (soft delete)
- **InventoryMovement**: Full audit trail (Sale, Return, Adjustment, Import) with `QuantityBefore`/`QuantityAfter`
- **PaymentMethod**: Efectivo, Bizum, Transferencia, Tarjeta TPV propio, Tarjeta TPV punto de venta, PayPal
- **Return**: Multi-sale returns with category (Defectuoso, TamañoIncorrecto, NoSatisfecho, Otro), optional reason & photo, 30-day window, same POS only
- **ReturnSale**: Many-to-many between Return and Sale with quantity and unit price snapshot
- **ReturnPhoto**: Optional photo for return documentation
- **RefreshToken**: JWT refresh token with revocation and rotation tracking
- **ProductComponent**: Master table of jewelry components (materials, labor) with optional cost/sale prices
- **ProductComponentAssignment**: Component assigned to product with quantity, override prices, display order
- **ComponentTemplate**: Reusable template of components for quick product setup
- **ComponentTemplateItem**: Component within a template with quantity
- **ModelMetadata**: AI model versions with accuracy metrics, only one active at a time
- **ModelTrainingJob**: Training job status tracking (Queued, InProgress, Completed, Failed) with progress
- **ProductAiProfile**: AI-proposed catalog attributes of one product — piece type, materials (a list, `[]` when there is no evidence), stone, size and commercial tags — each carrying its confidence and its provenance (`rule` when a deterministic normalization produced it, `inferred` when a model did). Provenance is what the hybrid review policy turns on: a sensitive field a model inferred needs a person, the same field from a rule does not, and commercial tags auto-approve above a configured threshold. `ReviewStatus` (where it stands) and `ReviewOrigin` (who put it there — bulk or human) are separate columns on purpose, so the indexing feed can select by status while review metrics select by origin without either lying. The raw proposal is kept immutably in `ProposedProfileJson`, which is what makes the extractor's correction rate computable. One profile per product, enforced by a unique index. `SourceHash` covers the enrichment *inputs* — not the indexer's hash of the canonical document text — so a repeated batch neither pays for a model call nor overwrites a review (capability `product-ai-profile`)
- **ProductSearchEvent**: One executed assisted search and, if it happened, the selection made on it. Written in two steps by whoever can observe each half: the backend records the search while serving it — origin, trace id, retrieval latency and the list actually returned exist nowhere else — and the browser reports only the chosen product, from which the server derives the rank. `SearchSessionId` groups the queries of one episode, so a reformulation is distinguishable from an abandonment; `SearchOrigin` separates five paths — assisted, degraded because the AI service could not answer, never consulted because assisted search is switched off for that point of sale, the generative free query of C40, and the sale agent's turn of C42; the last two are separate values rather than one «generative» bucket because the free query answers once over a payload the caller composed while the agent decides for itself what to consult, so pooling them would make the cost per answer of either unreadable — and neither needed a migration, the column having always been `int`; `jsonb` for the effective filters and the displayed results. No read surface: analysed with SQL (capability `ai-search-telemetry`)
- **ProductFamily** / **ProductFamilyMember**: the products that are one piece in several variants — the same ring in sizes S, M and L — grouped as an editable business entity, replacing a generated text key that broke on a hyphen and that no administrator could correct. **Not a `Collection`**: a collection groups by editorial criteria and a product may belong to one of many unrelated ones, whereas a product belongs to **at most one family**, enforced by a unique index on the membership rather than by a check in code — a second membership raises no error and would surface as two family identifiers emitted for one product. A member carries the `VariantLabel` that tells it from its siblings (optional while unknown, unique within the family when given) and a `SortOrder` derived from its place in the declared list. Membership is declared as a complete list and persisted by deleting every row and inserting the new set, so a member's `CreatedAt` is when the list was last written, not when the product joined. Entering and leaving products (and stayers on reorder/label change) have `Product.UpdatedAt` stamped via `ExecuteUpdateAsync` so the catalog index-feed cursor can see them; an identical list still writes nothing, including Product. `Origin`, `ApprovedByUserId` and `ApprovedAt` were reserved from the first migration for the assisted approval flow, which has no migration turn of its own, and **C18a writes them**: `POST /api/ai/catalog/family-suggestions/apply` creates a family with `Origin = AiApproved`, the approving administrator and the instant, through the same service as the manual path. Manual creation still records `Manual` with the approval fields empty, so the two remain distinguishable after the fact. No navigation property from `Product`. **C18b** makes families enumerable — a paginated, filterable admin listing that did not exist — and dissolvable outright rather than only emptied, freeing the members, taking the review verdicts with it, and stamping the departing products' catalog watermark so an incremental index pull sees them (capabilities `product-family`, `family-suggestion`, `family-review`)
- **FamilyReviewVerdict**: one person's judgement about one `(product, family)` pair, added by **C18b**. **The pair is the identity, not the membership** — a verdict is recorded whether or not the product currently belongs to that family, because the two questions a reviewer answers are the same one from opposite sides: a member the vectors do not support, and an unassigned product that looks like it belongs. Hanging it off `ProductFamilyMember` would have covered only the first, since an orphan has no membership row to carry it. One row does three jobs: it is the dismissal list, so a rejected candidate never returns; the audit's memory, so a queue worked through stays worked through; and the **per-item approval stamp** C18a deferred here, its 156 families all recording the administrator who fired one batch rather than a judgement about any particular family. It lives in the transactional schema and not beside the index, because `ai.product_document` is a projection that gets tombstoned and rebuilt — a table next to it would inherit none of that lifecycle, deleting a family would leave rows nothing cleans, and the reviewer would be an opaque identifier the screen cannot resolve to a name; here the foreign keys settle all three without code. Unique index on the pair, so judging it twice is a correction and not a second opinion. **`SubjectWasMember` is captured when the verdict is written**, never derived afterwards: once a rejected member is actually removed it is indistinguishable from a rejected candidate, so deriving the population from present state gets it wrong for precisely the judgements that were acted on. **`ReviewSeconds` is persisted per judgement** rather than accumulated in the screen, because an average that dies with the tab is not a metric — and it is nullable, since a fabricated zero would assert an instant review (capability `family-review`)

### Business Rules
1. Operators can only access assigned points of sale
2. Sales require valid payment method assigned to the point of sale
3. Stock cannot be negative (validated at application level)
4. Price in Sale is a snapshot (not reference to current product price)
5. Products need at least one photo for image recognition
6. Only one photo can be marked as primary per product
7. Manual sale price edits are only allowed when the POS has `AllowManualPriceEdit = true`; overrides are audited with `PriceWasOverridden` and `OriginalProductPrice`
8. Returns must be at the same POS as the original sale, within 30 days, with mandatory category
9. Cart checkout is atomic (all-or-nothing) with idempotency key to prevent duplicates; all lines share same POS and payment method
10. Inventory record presence (`IsActive = true`) determines product assignment to POS (visible to operators)
11. Jewelry component prices use 4-decimal precision; component management is admin-only
12. AI model trains in-browser via TensorFlow.js (MobileNetV2 transfer learning); confidence threshold 40%
13. A product belongs to at most one product family, enforced by a unique database index rather than an application check
14. Assisted search (`POST /api/ai/search`, capability `ai-assisted-search`) is scoped to one concrete point of sale, required in the body for every role: operators are checked against their assignments, administrators may pick any **active** one. The AI service proposes candidates; the backend applies the truth — price, quantity and what the shop carries come from `public`, never from the AI response. A candidate without an active inventory record at that point of sale is dropped; one with a quantity of zero is kept and marked, because availability weights a result and never removes it
15. Assisted search never fails because of the AI: every failure mode of the gateway degrades to a point-of-sale-scoped Spanish full-text searcher and is reported to the caller. It is switched on per point of sale from configuration, and disabled shops are recorded under their own `SearchOrigin` so they cannot be mistaken for AI outages
16. A sale may declare the assisted search it originated from (`searchEventId`, optional on `POST /api/sales` and on **each line** of `POST /api/sales/bulk`, capability `sales-management`). It is stored only after verifying that the event exists **and belongs to the user making the sale** — the same ownership rule as recording a selection, with no administrator exception, because a search event is the record of what one specific person did. An unknown or foreign identifier degrades the attribution to none: never a validation error, never a failed sale, and nothing else about the sale changes. Attribution is analytics; refusing a sale over it would turn a measurement into a till outage
17. The operator's entry points to a sale are four: barcode/QR scanning, manual SKU search, the assisted panel (`/sales/new/assisted`, capability `assisted-search-panel`), and — **since C42** — the sale agent's own screen (`/sales/new/agent`, capability `sales-agent-panel`), a fourth card in the sale hub and a conversation thread where each turn owns its answer block, because a single results area refreshed per turn leaves the operator reading one turn's argument over the next turn's rows, and when the loop pivots to substitutes the piece being looked at disappears with no explanation. The panel issues a search only on an explicit act and never while typing, because every uncached search charges a query embedding and the candidate cache is keyed on the whole query string, so no prefix of a query can ever hit it. **Since C40 the panel offers two routes and the operator picks**: the fast semantic search, which is the default, and the assisted answer of the free query (`POST /api/ai/search/assisted`, capability `ai-free-query-search`), which costs a paid provider call. The cost difference is stated **before** the choice — thirty searches a minute against ten, an immediate answer against a few seconds — and the choice is **not remembered between visits**, deliberately: remembering the expensive face is how spend happens without anybody deciding it. Changing the route issues no request. Whether each route is even on is readable **before** searching, from `GET /api/ai/search/availability`, which makes no AI call and carries `[DisableRateLimiting]` so that checking whether you may search does not cost a search

---

## Important Constraints

### Free-tier Optimization
- **Database connections**: Max 5-10 simultaneous (connection pooling)
- **Pagination**: Mandatory for operator lists (max 50 items/page). Indexing feeds use their own caps (catalog 50, POS 200) and do not read `PaginationConstants.MaxPageSize`.
- **Caching**: In-memory cache for frequently accessed data (products, payment methods)
- **Image compression**: Before upload to storage
- **Bundle size**: Frontend < 500KB initial load

### Performance Targets
- **Users**: 2-3 concurrent
- **Products**: ~1.200 catalog items (436 real + 764 synthetic; hybrid C06a+C06b)
- **Response time**: Optimize for mobile operators

### Security Requirements
- JWT authentication with refresh tokens
- Index-feed routes authenticate with `X-Index-Feed-Key` (`IndexFeed:ApiKey`); a user JWT does not open them
- BCrypt password hashing with salt
- HTTPS required in production
- CORS configured per environment
- Role-based access control (RBAC)
- Pre-signed URLs for storage access

### Data Storage
- **Development**: Local filesystem (`./uploads/`) + PostgreSQL in Docker
- **Production**: S3/Blob Storage + managed PostgreSQL (RDS/Azure Database)
- **Strategy Pattern**: IFileStorageService abstraction for environment switching

---

## External Dependencies

### Cloud Services (Production — AWS)
- **PostgreSQL**: RDS (db.t3.micro, 20GB)
- **Object Storage**: S3 bucket de ficheros (`prod-jpv-files` en pila Terraform)
- **Edge / TLS**: nginx en EC2 (Let’s Encrypt)
- **Container hosting**: EC2 + Docker (imagen ECR con API + SPA)
- **Config / secrets**: SSM Parameter Store (`/jpv/prod/*`)
- **Logging**: CloudWatch Logs

### Third-party Libraries

**Backend:**
- Entity Framework Core (ORM)
- Serilog (logging)
- BCrypt.Net (password hashing)
- ClosedXML (Excel processing)

**AI Service (`jbg-ai`):**
- OpenAI SDK (`openai`) — C06b catalog CLI (`generate`); not required to boot `/health`
- LiteLLM (`litellm==1.98.0`) — C09 runtime enrichment; not required to boot `/health`
- bcrypt (`bcrypt>=4.2.0`) — C10 world ingest (operator password hashes); not required to boot `/health`

**Frontend:**
- Metronic React template (UI components, layouts)
- TensorFlow.js or ONNX.js (ML inference)
- xlsx/exceljs (Excel file reading)
- React Router v7 (routing)
- Sonner (toast notifications)
- next-themes (dark mode support)

### Development Tools
- Docker & Docker Compose
- GitHub Actions
- PostgreSQL 15+
- Node.js (for frontend)
- .NET 10 SDK

---

## Key Documentation References

- **Architecture**: `Documentos/arquitectura.md`
- **C4 Model**: `Documentos/modelo-c4.md`
- **Data Model**: `Documentos/modelo-de-datos.md`
- **Epics**: `Documentos/epicas.md`
- **Testing Backend**: `Documentos/testing-backend.md` + `Documentos/Testing/Backend/`
- **Testing Frontend**: `Documentos/testing-frontend.md` + `Documentos/Testing/Frontend/`
- **Metronic Analysis**: `Documentos/Propuestas/analisis-metronic-frontend.md`
- **Technical Clarifications**: `Documentos/Propuestas/aclaraciones-tecnicas.md`
- **AWS Deploy Guide**: `Documentos/Guias/deploy-aws-production.md`
- **AI Model Admin Guide**: `Documentos/Guias/admin-modelo-ia.md`
- **Sales Registration Guide**: `Documentos/Guias/ventas-registro.md`
- **AWS vs Azure Comparison**: `Documentos/Propuestas/comparacion-aws-azure-deploy.md`
- **User Story Procedure**: `Documentos/Procedimientos/Procedimiento-UserStories.md`
- **Work Ticket Procedure**: `Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md`
- **C06a catalog corpus**: `data/catalog/real/generated/catalog-real-enriched.jsonl` + `scripts/catalog/README.md` + `Documentos/Proyecto Final AIEng/informes/c06a-catalog-enrichment-report.md`
- **C06b synthetic corpus**: `data/catalog/synthetic/generated/catalog-synthetic.jsonl` + `ai-service/src/jbg_ai/data/README.md` + `Documentos/Proyecto Final AIEng/informes/c06b-synthetic-catalog-report.md`
- **C10 synthetic world**: `data/world/pos-profiles.yaml` + `ai-service/src/jbg_ai/data/README.md` + `Documentos/Proyecto Final AIEng/informes/c10-synthetic-world-report.md`
- **C11 source text & embeddings**: `ai-service/src/jbg_ai/indexing/` (`source-text/v1`, LiteLLM 1536-d). `api.main` does not import it; the index router does (C13). Live spec `catalog-source-text`.
- **C12 index feed**: `GET /api/ai/index-feed/catalog` and `.../pos-availability`; live spec `index-feed`. Runbook `Documentos/Proyecto Final AIEng/informes/c12-catalog-autobulk-runbook.md`.
- **C13 catalog indexer**: `POST /v1/index/sync` / `GET /v1/index/status` pull the catalog feed; committed `sku_provenance.json`; live spec `product-document-indexer`.
- **C14 vector retrieval**: `POST /v1/retrieval/products`; cosine k-NN over `ai.product_document` with `JPV_RETRIEVAL_DISTANCE_THRESHOLD`. Live spec `vector-retrieval`.
- **C18a family suggestion**: `POST /v1/families/suggest`; offline grouping with a relative veto that flags for review and never removes. Live spec `family-suggestion`. Report `Documentos/Proyecto Final AIEng/informes/c18a-family-suggestion-report.md`.
- **C18b family review**: `POST /v1/families/audit`, the tenth `/v1` route; audits persisted families and nominates orphans by relative margin. Live spec `family-review`. Report `Documentos/Proyecto Final AIEng/informes/c18b-family-review-report.md`.
- **C20 query expansion**: `ai-service/src/jbg_ai/retrieval/synonyms.py` + `query_synonyms.yaml`; a pure function returning equivalence groups, never a rewritten query and never `tsquery` syntax. Live spec `query-expansion`. Reach report `ai-service/evals/results/c20-query-expansion-reach.md`.
- **C21 hybrid fusion**: three ranked lists fused by weighted RRF in `retrieval/fusion.py`; `score` became a normalised fused score, so figures recorded before and after are not comparable. Live spec `hybrid-fusion`. Reports `Documentos/Proyecto Final AIEng/informes/c21-hybrid-exploration-measurements.md` and `ai-service/evals/results/c21-fusion-configuration-comparison.md`.
- **C22 POS projection**: `ai.pos_projection` drained by `python -m jbg_ai.indexing sync-pos`; soft prefilter that degrades rather than hides, with a staleness ceiling. Live spec `pos-projection`. Reports `Documentos/Proyecto Final AIEng/informes/c22-exploration-measurements.md` and `c22-implementation-measurements.md`.
- **C41 scheduled drain**: since C41 that drain also runs **inside `jbg-ai`**, once at start-up (in full when no checkpoint exists) and then every `JPV_POS_SYNC_INTERVAL_SECONDS` (600, derived from the ceiling so several consecutive failures fit under it). It takes a **non-blocking advisory lock inside the drain**, so a scheduled tick and a manual `sync-pos` cannot interleave the single-row keyset of `ai.sync_checkpoint` — an interleaved keyset skips rows in silence. **No route under `/v1` and no change to `openapi.json`.** `GET /health` gains a `projection` section read from the checkpoint (never from `refreshed_at`) which reaches the administrator card, and `deploy/demo/verify.sh` gains a fifth failure condition for a projection with no assigned row. *(This line previously read «a cron, not a route». The cron existed only in prose and was unrunnable against a containerised service.)*
- **FIX1 enrichment vocabulary**: `piece_type` widened from eight to twelve canonicals and prompt `enrichment/v2` in force; `v1` kept intact because earlier profiles still declare it. Live specs `catalog-enrichment-pipeline` and `query-expansion`. Reports `Documentos/Proyecto Final AIEng/informes/fix1-exploration-measurements.md` and `fix1-vocabulary-gaps-measurements.md`.
- **C23 knowledge corpus**: `data/knowledge/` (Markdown, one file per document, `_corpus.meta.json` sidecar) + `ai-service/prompts/knowledge/v1/`; indexed by `python -m jbg_ai.indexing sync-knowledge` into `ai.knowledge_document` / `ai.knowledge_chunk`. Each section declares a `claim_scope` that travels with the retrieved fragment, and search is a callable rather than a route. Live spec `knowledge-corpus`. Reports `Documentos/Proyecto Final AIEng/informes/c23-exploration-measurements.md` and `c23-implementation-measurements.md`.
- **C24 eval harness**: `ai-service/src/jbg_ai/evals/` plus the golden set in `ai-service/evals/golden/` — 68 judged queries of 72 written, graded 0-2, the annotation criterion written before labelling, and a composition validated by code that **fails the load** rather than documenting an intention. `uv run evals run --config vX [--persist]` always writes the report to `ai-service/evals/results/` and writes `ai.eval_run` / `ai.eval_case` / `ai.eval_result` only on request. `GET /v1/evals/runs` stops being a stub without moving `openapi.json`, and both retrieval statements gained a `product_id` tiebreak so that a run is repeatable at all. Live spec `retrieval-evaluation`. Reports `Documentos/Proyecto Final AIEng/informes/c24-exploration-measurements.md` and `c24-implementation-measurements.md`, plus `ai-service/evals/results/c24-baselines-2026-09-07.md`.
- **C25 ranking recalibration**: the fusion is composed in **two stages** with per-branch weights (`retrieval/orchestrator.py`), because C21's flat fusion **concatenated rather than fused** — with 1.00 lexical votes against 0.33 vector, the 60 lexical documents outranked the best vector-only hit in every query, and the measured consequence was a grade-2 document falling to position 33. Adds the coverage rule that scales the lexical branch by how much of the query its best candidate matched (no configured parameter of its own), `retrieval/abstention.py` — a **relative per-query rule**, not a scalar threshold, because the out-of-domain distance range sits *inside* the answerable one — and the availability signal read by `LEFT JOIN` **without restricting** the candidate set, scored inside the last block of the ordering key. The flat fusion stays selectable so the published baseline stays reproducible; `clean-plain-fusion` retires it. Rotation was **withdrawn from the ordering by measurement** and `sales_30d` is read for diagnosis only. Live specs `business-signals-ranking` and `retrieval-abstention` are **born** here; `hybrid-fusion`, `pos-projection` and `retrieval-evaluation` are modified. Reports `Documentos/Proyecto Final AIEng/informes/c25-exploration-measurements.md` and `c25-implementation-measurements.md`, plus `ai-service/evals/results/c25-baselines-2026-09-11.md`.
- **C26 substitutes retrieval**: `POST /v1/retrieval/substitutes`, the last closeable 501 of the frozen contract, served by `retrieval/substitutes.py` over the embedding **already stored** on the source row — no provider call, no lexical branch, no expansion, no fusion, because the anchor is a `product_id` and not a typed query. `piece_type` is the only hard filter; size mismatch and unavailability are **continuous** tail terms and never an integer block, because a block partitions the result instead of breaking a tie and would send a product's own family variants to the tail by construction — which is why `demotion_rank` is deliberately not reused. The size term is inert unless both sides declare a size, since 54 % of the rings declare none. Availability **demotes and never removes**: excluding on stock is C34's, on the .NET side, which owns stock. Adds `JPV_SUBSTITUTE_WEIGHT_SIZE` (0.05, swept over eleven grid points; zero is the rollback). Live spec `substitutes-retrieval` is **born** here with ten requirements, and `vector-retrieval` is modified, losing the requirement that the route keep answering 501. Reports `Documentos/Proyecto Final AIEng/informes/c26-exploration-measurements.md` and `c26-implementation-measurements.md`, plus the slice `ai-service/evals/results/c26-substitutes-slice.md`.
- **C28 profile review**: human review of the AI product profiles and the two figures the delivery checklist asks for, **.NET and frontend only** — `ai-service/` untouched, and **no migration**, because C08 had reserved `ProposedProfileJson` and `ReviewDurationMs` in writing and delivered them. Six administrator-only routes on `AiCatalogController` (`profile-review-queue`, `profile-reviews`, `.../bulk`, `.../rejected`, `.../restore`, `profile-review-metrics`) over `IProfileReviewService`. The queue is drawn by review **origin** (`AutoBulk`) over approved **status**, never by status, because the index feed selects approved profiles and opening a batch into `Pending` would withdraw those documents from the vector index mid-session. The batch is **stratified by evidence** — the worst of the three sensitive fields' confidences, an absent stone type not penalising — and drawn deterministically by `SHA-256(ProductId + seed)` per stratum, so it is reproducible from a declared seed **without being persisted**, which is what avoids a seventh migration. Corrections carry a **direction** derived from the set difference, and `ProposedProfileJson` is never rewritten: the rate *is* the difference between that column and the values in force. Review time travels in the same request that records the judgement — the previous review capability recorded 64 judgements and 6 timings — and bulk approval is bounded to one field within one stratum. Live spec `profile-review` is **born** here with fifteen requirements; `family-review` grows from ten to twelve, gaining family creation from the screen and the keyboard shortcuts C18b recorded as delivered without delivering. **Delivered figures**: 20,9 % weighted correction rate and 32,1 s average over 204 profiles, 204 of them timed — published split into **10,4 % on the sensitive fields** and 42,3 % on the commercial tags, which arrived empty and were filled by reviewer judgement against no ground truth. Three things are declared unmeasured rather than estimated: the keyboard A/B, the exploration's blindness-to-omissions thesis, and the prompt-version comparison. Report `Documentos/Proyecto Final AIEng/informes/c28-implementation-measurements.md`, exploration `c28-exploration-measurements.md`.
- **C30a assist structure and rule warnings**: `POST /v1/assist/sale` stops being a fixture and serves the **structured** half of sale assistance — **no language-model call at all**, which is what makes C30b measurable against it as an ablation: same route, same candidates, same citations, with prose and without. Three modes selected **structurally** by the anchors the request carries (a free query, a piece, a piece with a question); the intent is never guessed from the wording, because routing a query is C31's and a keyword mini-router here would be work C31 deletes. Candidates group by a **nullable** `family_id` under the invariant *null implies exactly one member*, enforced structurally rather than asserted. Warnings are computed by rule into a **closed vocabulary of two codes** (`family_has_variants`, `size_label_missing`); the variants one reads the family **roster** the index holds — a new `family_roster` on `ProductSearchPort`, capped at 24 against a measured maximum of 8 — and not the candidates retrieved, because knowing a member exists that was never returned requires reading the roster. **No stock warning and no price anywhere in the response**, verified over the whole serialised body rather than over the empty pitch. The piece-with-no-question mode **addresses** its fragments by primary key over an allow-list of sections, admitting only `claim_scope: general`, so a commitment of the establishment never enters an argument nobody asked for; the modes with a question search the corpus with the sheets of the **undeclared** materials excluded in **both** branches — measured over the 72 golden queries, that removes a mean of 36,4 foreign-sheet citations per anchor while raising abstentions only from 41 to 44,3, and promotes ~11,8 correct fragments per anchor because the clause filters before the `LIMIT`. Abstention travels in its own `abstained` field and deliberately **not** in `low_confidence`, whose measured meaning is anticorrelated. An unusable anchor is a 422 naming which of the three cases occurred, never a 200 with `abstained`. **The frozen contract moved** — five assist schemas, **zero routes** — taken now because the route had zero consumers, the precedent being C18a/C18b. Live spec `assist-generation` is **born** here with thirteen requirements; `knowledge-corpus` grows 11→14, `retrieval-abstention` 7→10 and `ai-service-api-contracts` 14→15. With it, `/v1/inventory/propose` is the **only** route left answering 501, and not for want of a turn. No migration. Report `Documentos/Proyecto Final AIEng/informes/c30a-implementation-measurements.md`, exploration `c30-exploration-decisions.md`.
- **C30b assist pitch generation**: `POST /v1/assist/sale` **writes the sale argument** in the two piece-anchored modes, which inverts the requirement C30a declared — the live spec `assist-generation` loses *This capability generates no prose and calls no provider* and grows **13→25 requirements**. The free-query mode and an abstained request still call nothing, and those two cuts are stated separately because they are two different reasons. **Three deterministic checks and no judge**: resolution (the declared identifier was in the set handed over), correspondence (the model declares, per citation, the span of its **own** argument that citation supports, and the code verifies that span is a literal substring), and a numeric gate that whitelists by membership in the **payload object** — never the rendered prompt, whose own numerals would open the gate — **plus** adjacency to a currency or stock marker, which rejects *even when the numeral is whitelisted*: measured on the corpus, `material-oro.md` states that eighteen carats are 750 thousandths, so «750 €» walks through a pure whitelist. Semantic fidelity is **declared as not verified** and left to RAGAS in C38: a model judging another model is circular and would double the latency where a customer waits. **One repair for every violation at once**, and the ceiling of **two provider calls is literal** — `num_retries: 0` and C09's backoff deliberately not replicated, because a 2 s sleep against a 4 s budget would make «no more than two calls» false. Two policies: a hard violation costs the whole argument, a correspondence failure costs **that citation** and the prose is served. Degrading never leaves the response poorer than C30a's — same route, same candidates, same citations — which is what keeps the two halves comparable as an **ablation**, and a deployment with no provider credential is that ablation for free. The argument is **never persisted and never logged**: the log carries the version, the model, the usage, the latency, the citation identifiers, the length and a **hash**, and the text is re-derivable from a versioned prompt at temperature zero. A **120-generation sweep** over three context widths (0,0897 USD, 0 provider errors in 175 calls) refuted the design's own biggest declared risk: the numeric gate rejected **nothing**, because 118 of the 120 arguments carry no digit at all — prevention in the prompt did the work, so the figure that answers the risk is «2 numerals seen, 0 rejected» and not «0 of 120». It also raised the per-call timeout 3→4 s on a measured p95 of 2.863 ms and promoted it to `Settings`. Three new settings, all optional and all pinned in the canonical OpenAPI profile: `JPV_ASSIST_LLM_API_KEY` (falls back to `JPV_RAG_LLM_API_KEY`, and which one won is logged), `JPV_ASSIST_LLM_MODEL` (**never** inherits `JPV_RAG_LLM_MODEL`, which is C09's) and `JPV_ASSIST_PITCH_TIMEOUT_SECONDS`. **The frozen contract moved by one description** — `prompt_version` now means «the generation layer ran» and no longer «there is a pitch»: verified leaf by leaf, 1102 before and after, zero fields added or removed, because `supported_claim` never travels to the wire. **Zero .NET consumers** when this change shipped, and **C34 is that consumer**; `/v1/inventory/propose` remains the only route answering 501. No migration. Report `Documentos/Proyecto Final AIEng/informes/c30b-implementation-measurements.md`, QA record in the archived change.
- **C31 guardrails and intent router**: `POST /v1/assist/sale` **classifies the free query before any retrieval runs**, which inverts the requirement C30a wrote and C30b kept — the live spec `assist-generation` loses *The detected intent is derived from the request shape and never guessed from words* and grows **25→41 requirements**. **Two gates and two figures that are never summed**: the card motivating the change conflated *«this is not a jewellery question»* (5 cases, in C23's knowledge fixture) with *«this is jewellery and THIS catalogue does not stock it»* (the golden set's largest category, 20 of 72 — silverware, watchmaking, stationery), and a pure intent classifier answers **yes** to all twenty. Refusals carry **two distinct codes** because what an operator says at the counter differs between a trade the shop does not practise and a piece it does not carry; `abstained` is **never** reused for either, since it reads the distance profile AFTER retrieving and this classifies BEFORE. `clarification_question` stops being permanently null, resolved **in code** from a closed catalogue of es-ES templates keyed on the missing axis — the field is typed as prose, so the presentation layer cannot resolve it, and a model-written *«algo por menos de 50 €?»* would put an unchecked figure in the one field no numeric gate inspects. The anchored-question mode is `both` **by construction** and pays no classifier; its guardrail is free, reading C23's already-computed `0,51` result: **zero citations means the corpus does not cover the question**, which nothing could read as such before. `unclassified` gains a second, honest meaning — *this request was not classified* — and an unavailable classifier is a **declared fail-open**, a branch with a test and a logged cause, never a mute `except`. Ceiling of **three provider calls**, literal: one classifier call that is **never retried and never repaired** (there is nothing in a label to repair) plus C30b's two. **The veto of D12 — declared before measuring — rejected the first configuration**: `router/v1` silenced **15 of the 48** answerable queries, and what was failing was not intent classification but not knowing how this catalogue is NAMED — its pieces are `<type> <motif>` (*Colgante erizo de mar*, *Anillo caracola*), so *«el bicho con puas que se pisa en las rocas»* **is** a catalogue query. Three prompt revisions took the false positive 31,25 % → 6,25 % and **could not close it**; the MODEL closed it: with the same prompt `gpt-4o` scores **48/48** on `catalog`, silences **0** and passes, so `DEFAULT_ROUTER_MODEL` moved to `openai/gpt-4o` **by measurement** — which is D9 vindicated, because the separate model variable is the only reason the classifier could move without invalidating C30b's 120 generations. **The change's own biggest declared risk did not materialise**: the free-query numeric whitelist turned out to be ~13 numerals and not five (`top_k=5` counts families after hydration; retrieval returns **15** candidates) and the numeric gate rejected **0 of 89** — what withheld the argument was `dangling_citation`, because the `catalog` task section said nothing about citations while the invariant rule *«puedes no citar nada»* permits without obliging. Prompts are versioned and none deleted: `assist/v1` **untouched** so C30b's figures stay interpretable, `assist/v2` kept with the measurement that produced `assist/v3`, and `router/v1..v3` with theirs. **The frozen contract moved by three descriptions** — verified leaf by leaf, 1102→1103, **zero fields added, removed or retyped**, the one new leaf being a `description` key on a field that had none. Three new optional settings pinned in the canonical profile: `JPV_ROUTER_LLM_API_KEY` (chain router→assist→rag, the resolved link logged once per process), `JPV_ROUTER_LLM_MODEL` and `JPV_ROUTER_TIMEOUT_SECONDS` (**declared NOT calibrated**). Evaluation over `ai-service/evals/routing/cases.yaml`: **119 cases, six classes, five of them REFERENCED and not copied**, and a load that **fails** when a declared count stops matching the tree. **Zero .NET consumers** when this change shipped, and **C34 is that consumer**; `/v1/inventory/propose` remains the only route answering 501. No migration. Report `Documentos/Proyecto Final AIEng/informes/c31-implementation-measurements.md`, QA record in the archived change.
- **C32a sale-assistant tool registry**: the six read-only tools of the sale assistant and the registry that holds them — `buscar_catalogo`, `buscar_sustitutos`, `listar_familia`, `consultar_conocimiento`, `consultar_disponibilidad` and `pedir_aclaracion` — **wired to no route**, because the only consumer is the agent loop and that is C32b. `ai-service/openapi.json` is **identical byte for byte** (`sha256 43f70fda…68c684`), nothing in `src/` imports `assist/tools.py`, and `POST /v1/assist/sale` behaves exactly as C31 left it. Live spec `sales-assistant-tools` is **born** here with thirteen requirements; no other spec moves. **The read-only invariant is structural, not declared**: three axes over the constructed registry — the frozen set of names, the methods every collaborator a tool captures exposes, and the HTTP verbs any registered client could issue — and it runs at construction, so a future tool injected with a writing port fails the build rather than the third turn of a loop. There is deliberately no `writes: bool` on the descriptor: it is set by whoever registers the tool, which is precisely who could be wrong. **D-6's own vocabulary refuted the design**: read as a substring, `sync` flags `projection_synced_at()` and `synced_at()`, which read a checkpoint, making the invariant unsatisfiable with the very ports the registry must inject; the vocabulary was left untouched and the **comparison rule** fixed instead, token by token with exact equality. An independent verification pass then refuted the remedy twice over and both were code defects, not wording: the inert-object exclusion was written **by category** — every pydantic model and every dataclass — which silently dropped `InMemoryKnowledgeIndex`, a real port captured by `consultar_conocimiento`, out of all three axes and would have let a writing port through by the same door, so it now excludes **two named types** and a port is inspected whatever it is built from; and `document_by_sku()` resolved with `.first()` on the strength of a comment asserting `sku` is UNIQUE in `ai.product_document`, which it is not — the uniqueness is .NET's, and the migration that created the table decided expressly not to add that index — so a duplicate reference returned an arbitrary row of an unordered result through the door four of the six tools resolve by; it is `one_or_none()` now. What the write vocabulary loses is **a verb it never held and not an inflection**: `put_checkpoint()` writes and matches nothing under either reading, so the set is a floor under the object graph and not a proof that no method writes. **`consultar_disponibilidad` was the one tool with no service behind it**, and it is served from `ai.pos_projection` rather than from .NET, which **closes the open decision the RAG design's §6.1 had carried since August by deferring it with a reason**: the only Python → .NET edge that exists carries `X-Index-Feed-Key`, has no `[Authorize]` on purpose and no `pos_id`, and its `pos-availability` route is a paginated feed of 200 rows rather than a point lookup. The endpoint is identified, bounded and **not built**, recorded in `openspec/DEFERRED_TASKS.md` with the warning that a general-purpose HTTP client will not pass the third axis. Availability travels as a **qualitative label with no digit in it** and never as the stored bucket, whose members are numerals; the absence of a reading scope or of a projection row is **a fourth value of its own** and never an absence of stock, because collapsing the two would pivot to substitutes over a piece the shop can sell. Failures are **observations carrying a closed vocabulary of four causes**, never an exception that would kill the consuming loop instead of costing it one turn. Tools address pieces **by SKU and never by internal identifier**, which added two reads to `ProductSearchPort` and modified none. **No tool calls a chat provider** and the embedding calls two of them make are counted in a counter of their own, so the published `usage.calls` still means chat calls of one request. Suite **1.469 passed / 0 failed** compared by test NAME, zero disappeared; **no test is marked `db`**, so the two new SQL statements have **not been executed against PostgreSQL** and that is declared rather than argued away. No migration, `alembic heads` unmoved at `d7c4e91b25a0`, and no new setting or environment variable. Report `Documentos/Proyecto Final AIEng/informes/c32a-implementation-measurements.md`, QA record in the archived change.
- **C32b sale-assistant agent loop**: `POST /v1/assist/agent`, a route of its own so `POST /v1/assist/sale` stays the deterministic row of the ablation, identical field for field. A manual function-calling loop (`assist/agent.py`) drives C32a's registry through a port whose return type has **no field for prose** (`agent_llm.py`); the transcript travels in the request, capped and delimited turn by turn (`transcript.py`); the classifier is an entry **guardrail**, one call over the turn being answered. **Six budgets** — 5 turns, 8 tool calls, 8 chat calls (derived), 40.000 prompt tokens, 30.000 observation characters and a 15 s deadline for the whole request with 8 s reserved for the argument — end in `partial: true` with a closed-vocabulary `stop_reason`, and the tool failure vocabulary gains a fifth cause, `presupuesto_agotado`. A two-armed provider pass (`evals/agent_sweep.py`, recomputable with `--rescore`) fixed three budgets and measured the agent at **×3,0** the pipeline; `gpt-4o-mini` was discarded for exhausting a budget on 66 % of requests. Live spec `sales-assistant-agent` is born with 22 requirements and `sales-assistant-tools` is modified; the contract moved by pure addition. Report `Documentos/Proyecto Final AIEng/informes/c32b-implementation-measurements.md`, QA record in the archived change.
- **C34 .NET sale-assist and substitutes endpoints**: the **first .NET consumer** of `POST /v1/assist/sale` and `POST /v1/retrieval/substitutes`, and the change that applies the one-sentence rule of the design where it shows most — *Python computes likeness and writes; .NET computes numbers and decides*. Two routes anchored to one product, live spec `ai-sales-assist` **born** with fifteen requirements: a write-free `POST /api/ai/products/{productId}/sales-assist` carrying the point of sale and an optional question **in the body** — free text about a customer, which a URL would hand to the proxy log, the browser history and any cache — and `GET /api/ai/products/{productId}/substitutes`. **No figure the operator reads was written by a model**: the point of sale is validated with C15's rule and the anchored product checked with one `HydrateAsync` **before** the AI service is called, so a request this side is about to refuse (400 · 403 · 404) never costs a paid call; the group the index returns is hydrated against the transactional catalog of that shop, in the AI's order, with a member it does not carry dropped; and `{{price}}`/`{{stock}}` are resolved against the anchored product — `ToString("C2", es-ES)` and a bare whole number, 88,3 % of 213 C30b arguments writing the stock where a number reads naturally. **An unresolved placeholder withholds the argument and never the response**: six `pitchStatus` values decided in a fixed order, the raw template reaching no field and no log line, and the group, warnings and citations served in every state the service answered. The two stock warnings are computed here and `family_has_variants` is **only ever removed**, never added on the served path — it would be false for 19,2 % of anchored pieces with a family once hydrated. Substitutes ask **once** with `top_k = 20` (the window of 60 the frozen contract caps at), keep the order, drop what the shop cannot sell today and truncate after filtering, with **four distinguishable empty outcomes** and none of them a server error. `ai-gateway-client` grows 16→17 requirements: the generative route gets its **own named client** `ai-assist` with a **10 s budget and an 8 s floor start-up refuses to go below** — the worst case the service declares, `MAX_PITCH_PROVIDER_CALLS × PITCH_TIMEOUT_SECONDS = 2 × 4 s` — its own circuit, and **no retry on a timeout or a 5xx**, only on a connection that never opened, because every other failure may have happened after generation began and a second attempt doubles both the wait at the counter and the paid calls; substitutes ride on `ai-retrieval`, calling no provider. **HTTP 422 stops reading as «AI unavailable»** in those two operations **and only there** — it is a product absent from the index, which the next synchronisation fixes — translated in a separate `TranslateAnchoredStatus` so the shared translation stays intact for every other operation. Any gateway failure, or the per-point-of-sale switch being off, answers **200** with the card read from `ProductFamily`. Latency measured end to end with the real provider through Docker Compose, 80 requests: **p50 4,4 s, p95 7,1 s, max 7,9 s, none above 8 s**, so the budget was *not* lowered. **The free query with no product and the agent route are excluded by a closed decision**: their placeholders name no product and one argument speaks about several pieces, so there is nothing to resolve them against — the fix is Python's and is recorded, not done. The demo generates: `/jbg-demo/ASSIST_LLM_API_KEY` is **the only optional secret**, absent means `not_generated` and that is also the rollback. **`openapi.json` identical byte for byte and no migration.** Report `Documentos/Proyecto Final AIEng/informes/c34-implementation-measurements.md`, QA record — including an independent verification pass — in the archived change.
- **C36 frontend sale card and family disambiguation**: `/sales/new/assist/:productId`, the **only screen of the final project that puts the RAG layer in front of a person**, and the first consumer of the two routes C34 left served with none. Live spec `sales-assist-card` is **born** with eleven requirements; `assisted-search-panel` grows 14 to 15, the result row gaining a **secondary action** that neither replaces nor blocks selection for sale and that **reports no selection to the telemetry endpoint**, because opening a card is not choosing the piece to sell and counting it would inflate the selection rate the search event exists to measure. **Exactly one assist request on entry to each visit and no automatic retry** — the route costs a paid provider call, the budget is ten per minute per user and the response cannot be cached — with the visit identifier in a lazily initialised ref and an out-of-order guard both copied from the panel, where they were already tested. Naming a different point of sale is the one other explicit act that asks again, because leaving the previous shop’s price and units under the new shop’s name would be the screen stating something false. The customer’s question is a **second explicit request**, capped at five hundred characters client-side and always in the body — never in the address of the page nor in router state the browser records in history — with **five suggested questions baked in** from the situations the corpus covers, because 9 of 40 real counter questions fell to «not covered». **A family of several members preselects none** and offers one sale action per member, degrading an absent variant label to the SKU; the chosen member travels to the manual sale page through navigation state, never the anchored piece. The **six `pitchStatus` values render as five messages** and `ai_unavailable` is never merged with `not_generated`: in the first the group, materials and match reasons come from the transactional catalog and there are no citations, so one message would misstate where what is displayed came from. The two withheld states share a text and stay distinguishable in the DOM. Citations carry their `claimScope`, an establishment commitment saying it is to be confirmed in store, and are **hidden when the argument is not delivered**. `size_label_missing` is an **attribute beside the SKU and never a warning**: it fires on 58,3 % of cards and is anti-correlated with having a family (4,0 % against 92,5 %), so it states the enrichment status of the catalog rather than the piece, and as an alert it would crowd out `stock_critical` at 3,9 %. Substitutes are triggered by **the anchored member’s stock and never by `pitchStatus`**, and are not requested at all on a degraded card, where the outcome would be an unavailable service with certainty. Every failure of the two routes is a typed outcome that **never throws**, with 429 and 404 carrying sentences of their own. The two router refusal codes are deliberately **left untranslated** — the intent classifier runs only in the free-query mode, so they cannot reach this screen — and a test asserts they fall to the neutral label. **Frontend only**: `backend/` and `ai-service/` untouched, `openapi.json` identical byte for byte, no migration. **132 new tests, zero new failing names** against a baseline that itself oscillates between 113 and 114, and coverage of the new code measured at 84–100 % of statements. **Three limitations declared**: the card has **no telemetry**, so its use is not measurable and the reactivation condition of the deferred `generate=false` task is not observable; a product the service cannot process still reads as «AI unavailable» on the assist route, though substitutes tell it apart; and the free query with no piece still has no screen. Report `Documentos/Proyecto Final AIEng/informes/c36-implementation-measurements.md`, QA record — including an independent verification pass that found no implementation defect and corrected two of the change’s own spec artifacts — in the archived change.
- **C40 frontend free-query panel**: the free query with no piece in hand **gets a screen**, which is the limitation C36 closed its own entry declaring. The panel gains a second route, `POST /api/ai/search/assisted`, with live spec `ai-free-query-search` **born** carrying nine requirements; `assisted-search-panel` grows 15→23, `assist-generation` 41→45, `retrieval-abstention` 10→12, `vector-retrieval` 9→11, and `ai-sales-assist`, `ai-service-auth` and `ai-service-api-contracts` one each — 28 requirements added and 8 modified over eleven capabilities, 0 removed. **The chain had three links and the one that bit was the third**: the ticket reasoned that `assist/v3` would fill M1's arguments with `{{price}}`/`{{stock}}` and most would be withheld, extrapolating C30b's 69 % and 88,3 % from the anchored modes; measured over 90 free-query generations it is **2 of 90 and 1 of 90**, a factor of thirty, because the anchored task invites selling one piece while the free one asks to compare up to fifteen grouped. What blocked M1 at **100 %** was the `AiGatewayClient` guard rejecting the mode outright. `assist/v5` stays justified with another magnitude — the free-query rejection rate falls **8,9 % → 0 %** — and adds a **fourth task, «uncovered»**, with the anchored rule: do not answer from memory, do not dodge with a generality, cite nothing; plus the hard cause `placeholder_in_free_query`, checked **only** when `product_id is None`. **Sixteen panel states resolved as a discriminated union and not as a ladder of field checks**, because the states are *combinations* and a screen that branches field by field gets every branch right and the combinations wrong — which is how C16's panel ended with five empty branches, three of which would paint a correct answer as a failure. `resolveFreeQueryState` decides and the component says; the three that would be painted wrongly by default are the knowledge route with zero pieces, and the two routeless states that need **opposite copy** by `intent` — one invites a rephrase, the other must not, because there the classifier never ran and asking the operator to rephrase blames them for a missing credential. **The abstention now reads a distance profile no filter has narrowed**: `retrieve_products` issues a second, unfiltered vector statement, sequential, reusing the vector, and **only when the request carries filters** — which is the defect the group corrects, since over a filtered profile the rule can never fire when the filter is narrow and the system served a handful of mediocre pieces while praising them in prose. From it comes the sixth closed-vocabulary code, `filters_too_narrow`, emitted by **retrieval** and transported by assistance so the two routes cannot diverge. **«Every point of sale» is a third scope class and not a relaxation of the first**: `AiCallScope` exposes exactly three construction paths, asserted by reflection, with no public constructor and **no sentinel** — the property that makes it safe is that an absent `pos_id` makes the availability prefilter **not apply**, failing closed, whereas a sentinel would reach the retriever's only hard filter and match everything. Making the claim optional on two routes opened a hole the same change closed: a **blank** `pos_id` was silently dropped and would have become «every shop», so absence is now the key being absent from the payload and anything else is a value that has to be usable. What cannot be known is not invented: without a shop the quantity and stock flag travel **null**, the row has three states rather than two, the label names the shop, and the sale-card button is disabled. **Five figures, three of them refutations.** Latency end to end through .NET over the 42 labelled queries: **p50 3 404 ms, p95 7 160 ms, 0 of 42 outside the 10 s budget**, so the pre-authorised cut was not triggered — the design feared the router would add ~2 s onto C34's 7,1 s, and measured it **pays for itself with the work it saves**, a refusal costing a fifth of an answer (p50 686 ms). `router_index_absent` after the coercion: **0 of 42** against H7's predicted 11,9 %, and not once in 144 served replies, so state 4 of the panel table is one this classifier does not produce. The probe costs **p50 20,9 ms / p95 29,3 ms** and **zero** on an unfiltered search, refuting the ticket in both directions at once — the hard filter *does* save time (21,3 → 9,3 ms) and the probe costs two digits, because it is exactly the full scan the filter avoided; end to end the operator waits 5 ms more on 87. Nine of the sixteen states observed over 71 queries. **No EF Core migration** — `SearchOrigin` gains a fourth value over an `int` column, fixed by `HasPendingModelChanges().Should().BeFalse()` — and **the frozen contract moved twice by pure addition**, verified leaf by leaf with 0 removed and 0 retyped. Two deferred items with their reasons: a global-scope free query **is not recorded**, because the telemetry column requires a shop and the spec forbids a placeholder one, so its frequency cannot be measured *because* it is not recorded; and `ForAllPointsOfSale_IsRefusedByInventory` has **no .NET surface** to assert on, so the guarantee lives in Python and a sentinel asserts the operation does not exist. **The corpus does not travel in the image** and C34's deferred entry is **aggravated**: `CORPUS_DIR` derives from `REPO_ROOT`, which inside the container resolves to `/app/.venv/lib`, so copying the corpus would not be enough on its own. Report `Documentos/Proyecto Final AIEng/informes/c40-implementation-measurements.md` and the sixteen-state table `c40-m1-panel-states.md`; QA record — including an independent verification pass that found a fourth completeness infraction, two false statements in the change's own report and restored a guarantee the spec sync had silently dropped — in the archived change.
- **C40_FIX every-shop scope made reachable** (`c40-fix-all-shops-scope-unreachable`, outside the C numbering like `FIX1` and `C25bis`): C40 built the every-point-of-sale scope in full — a third `AiCallScope` class, a third claims profile, authorisation open to both roles, nullable quantities, product-grouped hydration and a result row with three states — and **added no control**, so none of it ever ran. **Nothing failed**, which is the finding that shaped the change: the three panel scenarios were all conditioned on *«WHEN the search is scoped to every point of sale»*, so they described the state and none demanded a way into it. Worse, the live spec asserted the opposite of what the system did — *«The panel SHALL send a concrete point of sale on every search»* — and `--all --strict` passes over that, because it validates structure and not truth. The panel now offers the scope, **to administrators only**: it reports no stock, so it cannot close a sale, and the narrowing is **a decision of the screen and not an authorisation boundary** — the free-query route keeps serving the scope to operators, verified against a real operator over HTTP (200 with null quantities, 403 when naming an unassigned shop). `GET /api/ai/search/availability` answers for a **scope** rather than a shop: absence is «all of them» and comes back as a null identifier, resolved by `AiScopeSwitchExtensions`, one shared predicate the probe and the route both read so the null rule cannot drift. Four live statements stopped being false, and a fifth — the capability's own `## Purpose` — was caught only when syncing. Two things are recorded rather than fixed. **The guard the change shipped for its central invariant was tautological**: `GetAvailability_WithoutPointOfSale_MatchesTheRoutePredicate` computes its expectation with the same extension methods the probe uses and never invokes `FreeQuerySearchService`, so it stays green both when the shared null branch is inverted and when the route is rewritten with a different rule — three mutations, compiled and run. It is replaced by `AiScopePredicateAgreementTests`, which builds both services over the same options, **runs the route** and compares verdicts. **And the probe is still stricter than the route it describes**: it reports `AiFreeQuerySearch && AiSalesAssist` while the free-query path never reads the second, so with the card switched off it answers `switched_off` for a scope the route serves with generated prose — measured over HTTP — which on screen disables both routes and prints a false reason. Inherited from C40, prohibited by the requirement C40_FIX writes, and left as a **product decision in `openspec/DEFERRED_TASKS.md`** rather than changed, with today's answer pinned by a test. A separate defect the change itself introduced was fixed: making the query parameter `Guid?` meant an **unparseable** `pointOfSaleId` — blank, whitespace, a typo, a truncated GUID — bound to `null` and was served as the wider scope, since `SuppressModelStateInvalidFilter` is global and the non-nullable type had been the net; all four forms answered 200 and now answer 400. No migration, `ai-service/` untouched, `openapi.json` without a diff. Live specs `assisted-search-panel` 23 → 25 and `ai-free-query-search` modified; QA record — including an independent verification pass that refuted five of the change's own claims and closed four of the five boxes its author declared unverified — in the archived change.
- **C42 frontend agent panel**: the sale agent — `POST /v1/assist/agent`, delivered and measured since C32b and which **nobody called** — gets a screen. Its own route `/sales/new/agent`, a fourth card in the sale hub, and a conversation thread where **each turn owns its answer block**, with groups labelled by provenance, the call trace visible and the ten stop reasons in Spanish. Two capabilities **born** — `ai-agent-assist` and `sales-agent-panel` — and five modified (`sales-assistant-agent`, `assist-generation`, `ai-gateway-client`, `ai-free-query-search`, `ai-service-auth`): 25 requirements over 7 delta specs, and **no new `/v1` route, no EF Core or Alembic migration and no seventh tool**. **The order of the work was not the ticket's.** The exploration's v1 asked for the measurement before the first task, and that was **not executable**: the sweep harness counted no placeholders and recorded no projection age, so instrumenting it became group 2 and ran before any functional task — which is what keeps a pass longer than the 3.600 s staleness ceiling from being read as a fresh one, the defect that already contaminated part of C32b's retrieval figures beyond repair. **The frontend order comes from measured frequencies and not from a mockup**: one answer in five carries no piece (19,6 %, identical on both arms) and of those **fourteen of twenty are a clarification or a refusal**, so only 5,9 % of requests may be worded as «I searched and found nothing» — the no-rows case is therefore first and never phrased as an empty result; citations are empty in 92,2 % and warnings in 96,1 %, so both render nothing at all; the incompleteness ribbon serves **2,0 %** on the served arm and comes last. `origin` went before the prompt because `buscar_sustitutos` was invoked **125 times** in the measured pass, so labelling provenance is what most often stops the screen lying. **Thirteen refutations, all measured**, of which four govern: the withdrawal of the argument falling **13,1 % → 1,2 % is NOT attributable to `assist/v6`** and the report names the confounders, so the prompt fix is real and its urgency was small — as predicted, since the placeholder rule is word for word identical in `v3` and `v4` and C40 had already measured 3 of 90 there; pieces per response **still saturate at `MAX_AGENT_PIECES`**; the exploration report's tool table **pools both model arms** (115 of 125 `buscar_sustitutos` calls belong to the discarded one); and the container was serving **pre-change code** while **nothing exercised the agent route over HTTP at all**. The frozen contract moved by **pure addition** — `origin` on `AgentAssistGroup`, a subclass, with the shared `AssistGroup` deliberately **not** widened, by the precedent of `AgentUsage` — and the baseline fixture became `openapi-c42-baseline.json`. `SearchOrigin` gains a **fifth** value, `AssistedAgent = 5`, with no migration. The gateway gains a fourth route family, `ai-agent`, whose breaker **does not count an in-band degradation**: Polly sees a transport outcome and not the body, so a 200 carrying `fallo_proveedor` is a success at that layer and is instrumented as a metric instead — the two alternatives, a body-reading handler and a domain circuit, were discarded in the design with their reason. C32b's deferred entry is closed **by refutation and not by execution**, with the arithmetic written: ~13.000 tokens a request against 25.000 TPM is one request a minute, so a 204-request pass costs 2 h 44 min. **The manual check found what no test did**, twice: the answer strip claimed a stop reason the screen could not recognise next to «0 vueltas · 0 consultas» when the gateway had simply not answered, now keyed on `aiAvailable`; and **the pivot is unreachable when the operator names the piece by its name**, because `buscar_catalogo` never returns the product name — established by an HTTP experiment (SKU pivots, name does not), out of this change's scope and filed in `openspec/DEFERRED_TASKS.md`. Report `Documentos/Proyecto Final AIEng/informes/c42-implementation-measurements.md` and the manual-check script `c42-manual-check-runbook.md`; 75/75 tasks.
