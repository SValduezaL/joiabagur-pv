# T-AIENG-10: Synthetic world simulator — curated POS YAML, Poisson sales, local ingest (C10)

> Ticket técnico del change OpenSpec `add-synthetic-world-simulator`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, [HU-AIENG-010](../../../../Documentos/Historias/AI-Eng/HU-AIENG-010.md), [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C10), [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§6.3, §8.2, D6–D8, §10), sesión de exploración 2026-08-23 y cierre D1–D12 + censo.
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-10 / C10** — Mundo sintético: 12 POS curadas (YAML+semilla), inventario 6,5k–8k, 15k–25k ventas Poisson, CLI en `jbg_ai.data.world`, INSERT local sin tocar catálogo ni schema `ai`

---

## Contexto y Problema

C06a+C06b dejaron **1.200** productos y **38** colecciones en Docker (`public."Products"` / `"Collections"`). El RAG de inventario y el ranking con proyección POS no pueden demostrarse sobre un mundo vacío: hoy `"PointOfSales"`, `"Inventories"` y `"Sales"` están a **cero**.

La ficha v3 de C10 pedía un generador en `jbg_ai.data.generators/` (10–14 POS, 5k–9k inventario, 15k–25k ventas, co-ocurrencia) como pieza de datos, con test de determinismo. La exploración del 2026-08-23 fija que **C10 no es un servicio de Joiabagur**: es simulación D6/D7/D8 para C19/C22/C27. Aproximación **C3**: empaquetado C06b (CLI en `jbg_ai.data`, sin HTTP) + alma C06a (sin LLM, artefactos curados) + POS escritos a mano.

**Decisiones de la exploración (cerradas, D1–D12):**

| # | Ficha / tentación | Este ticket |
|---|---|---|
| D1 | C06a=`scripts/` · C06b=LLM+JSONL catálogo · seeder .NET | **C3**: módulo **nuevo** `jbg_ai.data.world`; YAML de POS; **cero LLM**; no seeder `DatabaseSeeder`; no extender `generate.py`/`ingest.py` de catálogo |
| D2 | Escribir `ai.co_occurrence` | JSONL efímero derivado; ingest `ai` = **C22/C27**. Verdad = `Sales.BulkOperationId` |
| D3 | POS con `IsSupplySource` | Marca en YAML. Columna SQL = **C19**. Este change **no** es 🗄️ |
| D4 | ¿Un `Sale.UserId` por POS? | **No.** FK NOT NULL, no unique por POS. RAG **no** agrega por operador. 3 operadores de demo |
| D5 | Métodos de pago | **Sí** `PointOfSalePaymentMethods` (6 métodos × 11 POS activas) |
| D6 | UserId de las ventas | Operador solo en sus 3 POS; resto **`admin`**; `Import`/`Adjustment` → admin |
| D7 | ¿Generate contra BD? ¿UUIDs en YAML? | Generate: `SKU`/`Code`, sin Postgres. Ingest: resuelve UUID, unmatched → `ROLLBACK`. No `POST /api/sales` |
| D8 | Partir POS+stock / ventas | **No.** Un change |
| D9 | Returns, fotos, componentes, familias, perfiles IA, search events | **Fuera** |
| D10 | Mundo limpio | `HT-ARTRUTX` inactivo + % `Inventory.IsActive=false` |
| D11 | Fechas / phone | `Phone=600123456`; `Code`≤20; `SaleDate=MovementDate` en el pasado; `CreatedAt` alineado. Test pareja venta↔movimiento |
| D12 | RDS | **No.** Solo Docker `:5433` / `joiabagur_pv` |
| Artefactos | JSONL 20k commiteado + test determinismo | **YAML+semilla en git.** JSONL y `pg_dump` **gitignored**. Se retira `test_simulation_is_deterministic_for_same_seed` |

**Estado actual del código y de la BD (verificado 2026-08-23):**

| Pieza | Estado |
|---|---|
| Change OpenSpec `add-synthetic-world-simulator` | **Scaffold** (`.openspec.yaml`); proposal/design/specs/tasks **pendientes**; este ticket + HU |
| `ai-service/src/jbg_ai/data/` | **Existe** (C06b): `generate`/`ingest` de catálogo, `briefs.py`, LLM OpenAI. `cli.py` solo esos dos subcomandos. `api.main` no importa el paquete |
| `jbg_ai.data.world` | **Ausente** |
| `ai-service/openapi.json` | **No debe cambiar** |
| Schema `ai` en Docker local | **No existe** (C05 bootstrap no corrido en este volumen) |
| `"PointOfSales"` / `"Inventories"` / `"Sales"` / `"InventoryMovements"` / `"UserPointOfSales"` / `"PointOfSalePaymentMethods"` | **0 filas** |
| `"Products"` | **1.200** (433 en rango SKU 1–436, 767 ≥437; faltan `SKU135`, `SKU400`, `SKU418`). Todos `IsActive` |
| `"Collections"` | **38** |
| `"PaymentMethods"` | **6** (seeder: `CASH`, `BIZUM`, `TRANSFER`, `CARD_OWN`, `CARD_POS`, `PAYPAL`) |
| `"Users"` | **1** `admin` / `Administrator` / `Admin123!` |
| `"ProductFamily*"` / `"ProductAiProfiles"` | 0 (no tocar) |
| `PointOfSale` | Name 100, **Code 20 unique**, Phone **20**, sin `IsSupplySource`. `AllowManualPriceEdit` bool |
| `Inventory` | Unique `(ProductId, PointOfSaleId)`. `IsActive` = asignación |
| `Sale` | `UserId` **NOT NULL**; `BulkOperationId` nullable; `SearchEventId` nullable (no rellenar); `Price` snapshot `numeric(18,2)` |
| `InventoryMovement` | `SaleId` **unique**; `MovementType` 1=Sale, 3=Adjustment, 4=Import; `UserId` NOT NULL |
| `User.Role` | Persistido como **string** EF (`Operator` / `Administrator`), no entero. `PasswordHash` varchar(128). Username unique 50 |
| Postgres Docker | `jpv-pv-postgres`, host **5433**, BD `joiabagur_pv`, `JPV_PG*` |
| `.gitignore` | Cubre `data/catalog/*`; **no** `data/world/` todavía |
| HU-AIENG-010 | **Creada** y alineada con este ticket |

**Impacto en producto:** la base local gana una red de tiendas, stock y un histórico. No hay endpoint nuevo ni pantalla. El rol de runtime de `jbg-ai` **no** gana `INSERT` sobre `public` (§6.3); el CLI usa `JPV_PG*` como C06a/C06b. Tres logins Operator permiten demo de C16 en aeropuerto / Ciutadella / Fornells.

**Influencia posterior de `Sale.UserId` (honesta):** casi **cero** para C19–C35 (agregan producto×POS). Útil para historial de la app (HU-EP9-001), movimientos de auditoría, y para entrar como Operator. El JWT `user_id` de búsqueda es el usuario *logueado ahora*, no este campo.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/src/jbg_ai/data/world/` | **Nuevo** — perfiles, Poisson, movimientos, CLI `world simulate\|ingest` |
| `ai-service/src/jbg_ai/data/cli.py` | Subcomandos `world` **sin** alterar el contrato de `generate`/`ingest` de catálogo |
| `ai-service/src/jbg_ai/api/main.py` | **Sin import** nuevo |
| `data/world/` | YAML + semilla **commiteados**; `generated/` JSONL y `backups/*.sql` **gitignored** |
| `.gitignore` | Ignorar JSONL de mundo y dumps; exceptuar el YAML de perfiles |
| `Documentos/Proyecto Final AIEng/informes/` | Informe `c10-synthetic-world-report.md` |
| PostgreSQL local | `INSERT` POS, Users (3), UserPointOfSales, PointOfSalePaymentMethods, Inventories, Sales, InventoryMovements. **Cero** Products/Collections/Families/ai.* |
| `openspec/changes/add-synthetic-world-simulator/` | proposal, design, specs, tasks (posteriores) |
| `backend/` API, `frontend/`, `openapi.json`, migraciones EF/Alembic | **Sin cambios** |

---

## Especificaciones Técnicas

### Artefactos (qué va a git)

```
data/world/pos-profiles.yaml          # 12 POS + seed + generator_version   COMMIT
data/world/.gitkeep
data/world/generated/*.jsonl          # ventas, inventario, co-occurrence   GITIGNORE
data/world/backups/*.sql              # pg_dump post-ingest                 GITIGNORE
```

El JSONL efímero usa claves naturales (`sku`, `pos_code`, `username`), **nunca** UUID de producto/POS. Sidecar local (también gitignored o solo en el informe): recuentos, seed usada, `generated_at`.

Comandos (nombres orientativos; el proposal puede ajustar el parser):

```powershell
cd ai-service
uv run --system-certs python -m jbg_ai.data world simulate --profiles ../data/world/pos-profiles.yaml --out ../data/world/generated
uv run --system-certs python -m jbg_ai.data world ingest --dir ../data/world/generated
```

Credenciales: `JPV_PG*` de `backend/.env`. **No** `JPV_CATALOG_LLM_*`. Simulate **no** habla con Postgres. Ingest **sí**.

Backup (documentar en README del módulo; no commitear):

```powershell
docker exec jpv-pv-postgres pg_dump -U postgres joiabagur_pv > data/world/backups/c10-world.sql
```

### Censo YAML (12 POS)

Ver tabla completa en la HU. Códigos obligatorios: `MAO-TALLER`, `CIU-CENTRE`, `MAO-AIR`, `FORNELLS`, `BINIBECA`, `HT-GALDANA`, `HT-SONBOU`, `PORT-MAO`, `PALMA-JAIME3`, `EIV-MARINA`, `HT-ALCUDIA`, `HT-ARTRUTX`.

- `MAO-TALLER`: único `is_supply_source: true`; λ retail ~0; `AllowManualPriceEdit=false`.
- `HT-ARTRUTX`: `is_active: false`; ventas solo en su ventana viva (verano 2025) y corte; inventario residual `IsActive=false`; sin pagos activos; sin operador. Sustituye al pop-up de Navidad descartado.
- Precio manual `true`: `MAO-AIR`, `HT-GALDANA`, `HT-SONBOU`, `EIV-MARINA`, `HT-ALCUDIA`.
- Teléfono de todos: `600123456`.

Estacionalidad y matriz intención≠evolución: HU (no repetir aquí salvo que el YAML deba llevar pesos de colección por POS — sí, para que simulate no copie briefs C06b a ciegas).

### Operadores

| Username | FirstName / LastName (propuesta) | POS | Password |
|---|---|---|---|
| `op-ciutadella` | Catalina Pons | `CIU-CENTRE` | `Operator123!` |
| `op-fornells` | Joan Marí | `FORNELLS` | `Operator123!` |
| `op-aeroport` | Marta Soler | `MAO-AIR` | `Operator123!` |

- `Role` literal `"Operator"` (conversión string de EF).
- Hash BCrypt **work factor 12**, igual que [`DatabaseSeeder`](../../../../backend/src/JoiabagurPV.Infrastructure/Data/DatabaseSeeder.cs).
- Email nullable (no hace falta; el índice unique filtra `IS NOT NULL`).
- `UserPointOfSales.IsActive=true` solo en esa POS.
- Ventas de esas 3 POS → ese `UserId`. Resto → `admin`. Movimientos `Sale` copian el `UserId` de la venta; `Import`/`Adjustment` (stock inicial) → admin.

### Simulación

- Horizonte **16 meses** por defecto (banda 14–18), extremo reciente = «hoy» del apply, extremo lejano = hoy−16 meses. `HT-ARTRUTX` corta al cierre.
- Poisson por POS×día (o semana) con λ del perfil × estacionalidad × propensión SKU.
- Inventario: **no** materializar 1.200×12. Objetivo **6.500–8.000** filas. Taller casi cubre catálogo; hoteles/aeropuerto sesgados; Fornells poco surtido + idle; % `IsActive=false` en POS vivas (D10).
- Ventas **15.000–25.000**. Qty típica 1; alguna línea >1. Un % de checkouts con `BulkOperationId` y **2+ líneas de distinto stem / pieza** (C27 necesita distinto `piece_type` más adelante; aquí no hay `piece_type` en `Product` — sesgar por colección/nombre es suficiente para que existan pares).
- `Sale.Price` = precio de `"Products"` al ingest (snapshot). `PriceWasOverridden=false`. `SearchEventId=null`. `Notes` null.
- `MovementType.Sale=1`, `Import=4` para el alta inicial de stock. No generar `Return=2`.
- Stock nunca negativo. Invariante: no hay venta sin fila activa con qty suficiente.

### Ingesta (transacción única)

```
1. INSERT PointOfSales          (Id DEFAULT; Code unique)
2. INSERT Users ×3              (BCrypt)
3. INSERT UserPointOfSales ×3
4. INSERT PointOfSalePaymentMethods  (11 POS × 6 métodos; no Artrutx)
5. SELECT Id, SKU, Price FROM Products → mapa
6. unmatched SKUs → ROLLBACK + lista
7. INSERT Inventories
8. INSERT Sales                 (UserId resuelto; Price del mapa)
9. INSERT InventoryMovements    (SaleId 1:1 para tipo Sale)
NEVER: UPDATE/INSERT Products, Collections, ProductFamily*, ai.*
NEVER: columna IsSupplySource
NEVER: RDS
```

`SaleDate` / `MovementDate` / `CreatedAt` / `UpdatedAt` / `LastUpdatedAt` se **escriben** con la fecha simulada (timestamptz UTC). Si se deja el `DEFAULT NOW()`, las ventanas 7/30/60d que usen `CreatedAt` mienten (D11). C19 usará `SaleDate`; igual hay que alinear.

### Co-ocurrencia

Derivada **después** de asignar `BulkOperationId`. JSONL efímero `{product_sku_a, product_sku_b, co_sales_count, last_seen_at}` con `sku_a < sku_b`. **No** ingest a `ai.co_occurrence`. C27 podrá recomputar desde `Sales`.

### Tests (pytest, nomenclatura `test_<unidad>_<escenario>_<esperado>`)

**Sí:**

- `test_no_sale_without_stock_at_that_pos`
- `test_seasonality_peaks_match_pos_profile` (incluye Artrutx sin ventas post-cierre; taller ~0)
- `test_inventory_movements_reconcile_with_final_stock`
- `test_co_occurrence_only_counts_same_bulk_operation`
- `test_sale_and_movement_share_date_and_user` (D11)
- `test_ingest_rolls_back_on_unmatched_sku`
- `test_ingest_does_not_touch_products_or_collections`
- `test_artrutx_is_inactive_without_active_payments`
- `test_operator_sales_only_on_assigned_pos`
- `test_api_main_does_not_import_data_package` (ya existe espíritu C06b; no romperlo)
- `test_phone_is_pinned_and_code_fits_varchar20`

**No:** `test_simulation_is_deterministic_for_same_seed` (retirado a propósito).

Cero llamadas LLM. Docker solo en tests de ingest (o Testcontainers); el simulate puro es unitario en memoria.

### Relación con changes posteriores

| Change | Qué necesita de C10 | Qué no debe hacer C10 |
|---|---|---|
| C19 | Filas Sales+Inventory+POS. Marca supply en YAML | Migración `IsSupplySource` |
| C22 | Inventario sesgado, POS, qty 0 vs no asignado | `ai.pos_projection` |
| C27 | `BulkOperationId` + JSONL derivado | `ai.co_occurrence` INSERT |
| C12 | POS e inventario para el feed (cuando exista) | Endpoints |
| C16/C36 | 3 operadores para demo | Frontend |

---

## Arquitectura

```
pos-profiles.yaml (git)          public."Products" (solo lectura)
        \                                /
         v                              v
   world simulate (sin PG)         world ingest (JPV_PG*)
         \                                /
          v                              v
   JSONL gitignored          INSERT public (transacción)
                                      |
                                      v
                              pg_dump gitignored
```

**Proceso vs paquete.** Igual que C06b: no arranca Uvicorn. El código vive junto al CLI de catálogo para compartir `envload` / `JPV_PG*`. `create_app` no registra routers.

**Frontera §6.3.** Runtime `jbg-ai` solo posee `ai`. El INSERT a `public` es CLI de desarrollador.

**Por qué no la API de ventas.** `POST /api/sales` valida operador asignado, actualiza stock en vivo y sella `SaleDate≈now`. El histórico de 16 meses y 20k filas no cabe ahí.

**Breaking changes.** Ninguno en API ni OpenAPI.

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec del change completos y `openspec validate --all --strict` → **0 failed**
- [ ] YAML de 12 POS + seed commiteado; JSONL de ventas y dumps **no** en git
- [ ] CLI `world simulate|ingest` documentado; `jbg_ai.api.main` no importa `jbg_ai.data`
- [ ] Ingest Docker: 12 POS, 3 operadores, 3 asignaciones, pagos en 11 activas, inventario 6,5k–8k, ventas 15k–25k, movimientos que cuadran; `"Products"` intacto
- [ ] `HT-ARTRUTX.IsActive=false`; `MAO-TALLER` supply solo en YAML; sin columna SQL nueva
- [ ] `Sale.UserId` según D6; pareja venta↔movimiento en fecha y usuario
- [ ] Co-ocurrencia solo por `BulkOperationId`; cero escrituras a `ai`
- [ ] Informe C10; README con `pg_dump` / restore
- [ ] Tests de invariantes verdes; **sin** test de bit-identidad; cero LLM
- [ ] `openapi.json` sin cambios; backend/frontend API sin cambios; sin migración EF/Alembic
- [ ] HU-AIENG-010 coherente; change listo para archive tras verify

---

## Requisitos No Funcionales

- **Seguridad:** Postgres solo por `JPV_PG*`. Passwords de operadores locales, documentados en el informe (mismo criterio que `Admin123!`). Sin RDS. Sin PII de cliente.
- **Reproducibilidad:** seed en YAML = intención. Fuente operativa del mundo = volumen Docker + dump local. Invariantes en pytest.
- **Integridad:** transacción de ingest; abortar si SKU unmatched o `Code` duplicado; stock no negativo.
- **Testing:** plan §1 — ninguna llamada real a LLM. Nomenclatura `test_<unidad>_<escenario>_<esperado>`. `uv run` con `--system-certs` en esta máquina.
- **Boot:** no exigir nada nuevo en `Settings` de `/health`.
- **Rendimiento:** ingest masivo en una transacción; `COPY`/executemany aceptable; no 20k roundtrips. Irrelevante en runtime del servicio.
- **Constraints reales:** `Phone` 20, `Code` 20, `Username` 50, `PasswordHash` 128, `Sale.Notes` 500 (dejar null).

---

## Preguntas Abiertas

Ninguna bloquea el apply. Defectos si no se reabre el debate:

| # | Tema | Defecto |
|---|---|---|
| Q1 | Librería BCrypt en Python | Usar `bcrypt` work factor 12 (compatible con BCrypt.Net). Si no se quiere dependencia: hash precomputado constante de `Operator123!` en el YAML/código de ingest |
| Q2 | % exacto de `Inventory.IsActive=false` en POS vivas | **~8 %** de las filas de inventario activas-de-asignación, además del 100 % de Artrutx |
| Q3 | Meses exactos | **16** |
| Q4 | % de checkouts con `BulkOperationId` multi-línea | **~15 %** de las operaciones (no de las líneas), 2–3 líneas |
| Q5 | ¿Simulate lee JSONL de catálogo o un dump de SKU? | Lee **ambos JSONL de catálogo** para sesgar mix por `collection_name`; ingest **autoriza** contra `"Products"`. SKUs del JSONL ausentes en BD no se venden (no están en el mapa) |
| Q6 | Nombres de pila de operadores | Los de la tabla de este ticket, salvo que se pidan otros |

---

## Prioridad / Estimación / Tags

- **Prioridad:** **Media** — 🟢; desbloquea C19/C22/C27, no la ruta C11–C16.
- **Estimación:** **5 SP** *(pendiente de refinamiento)*.
- **Dependencias:** C06a+C06b ingeridos (1.200 SKUs en Docker). No compite por migración EF Core. C05 schema `ai` **no** es prerrequisito (no se escribe `ai`).
- **Tags:** `HU-AIENG-010`, `T-AIENG-10`, `C10`, `EP12`, `python`, `cli`, `synthetic-world`, `pos`, `inventory`, `sales`, `offline`

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-010](../../../../Documentos/Historias/AI-Eng/HU-AIENG-010.md)
- **Change OpenSpec:** `openspec/changes/add-synthetic-world-simulator/`
- **Plan y diseño:** [plan de changes](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (ficha C10) · [diseño RAG](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) §6.3, §8.2, D6–D8, §10
- **Precedentes CLI:** [HU-AIENG-006a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006a.md) · [HU-AIENG-006b](../../../../Documentos/Historias/AI-Eng/HU-AIENG-006b.md) · [ticket C06b](../../archive/2026-08-23-add-synthetic-catalog-augmentation/ticket.md)
- **Entidades:** [`PointOfSale.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/PointOfSale.cs) · [`Inventory.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/Inventory.cs) · [`Sale.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/Sale.cs) · [`InventoryMovement.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/InventoryMovement.cs) · [`User.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/User.cs) · [`SalesService.cs`](../../../../backend/src/JoiabagurPV.Application/Services/SalesService.cs) (chequeo operador: solo API)
- **Compose Postgres:** [`backend/docker-compose.yml`](../../../../backend/docker-compose.yml) · [`.env.example`](../../../../backend/.env.example)
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Autor | Cambio |
|---|---|---|
| 2026-08-23 | `/enrich-us` | Creación del ticket y HU a partir de la exploración C10 (C3, D1–D12, censo 12 POS, hotel Artrutx cerrado, YAML+dump sin JSONL en git, sin test de determinismo) |
