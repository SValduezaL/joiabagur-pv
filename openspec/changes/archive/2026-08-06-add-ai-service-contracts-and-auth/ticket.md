# T-AIENG-002: Freeze jbg-ai HTTP contracts and internal service auth (C02)

> Ticket técnico del change OpenSpec `add-ai-service-contracts-and-auth`, generado con `/enrich-us`.
> **Fuentes de verdad:** `openspec/project.md`, `Documentos/` (diseño RAG y plan de changes), specs de `openspec/specs/` y [HU-AIENG-002](../../../../Documentos/Historias/AI-Eng/HU-AIENG-002.md).
> **Idioma:** título e identificadores técnicos en inglés; cuerpo en español, por coherencia con la HU y con el resto de `Documentos/`.

---

## Título

**T-AIENG-002 / C02** — Congelar los contratos HTTP de `jbg-ai` (modelos Pydantic + stubs deterministas + JWT HS256 + snapshot OpenAPI)

---

## Contexto y Problema

Tras C01 ([HU-AIENG-001](../../../../Documentos/Historias/AI-Eng/HU-AIENG-001.md), change archivado `init-ai-service-skeleton`), `jbg-ai` solo expone `GET /health`. Sin contrato congelado ni autenticación de servicio, el cliente tipado .NET (C03) y el resto de la ruta crítica no pueden avanzar: las dos personas del Proyecto Final se bloquearían mutuamente durante semanas.

El plan ([proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), ficha C02) exige modelos completos "§6.8", pero el diseño v3 ([proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)) termina en **§6.4**. La tabla de contratos está en [proyecto-final-diseno-rag-joiabagur-3devs.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) §6.8; v3 aporta `materials[]`, familias con `variant_label`, sobre-recuperación (§7.6), placeholders de precio y stock (§7.7) e `inventory/propose`. Este ticket reconstruye el contrato desde ambas fuentes y lo congela.

**Estado actual del código (verificado en el repositorio):**

| Pieza | Estado |
|---|---|
| `create_app()` en `api/main.py`, `GET /health`, `docs_url=None` | Existe (C01) |
| `Settings` con `app_env`, `service_version`, `log_level` y fail-fast | Existe (C01) |
| `TraceIdMiddleware` (`X-Trace-Id`) y logging con `trace_id` | Existe (C01) |
| `tests/conftest.py`, `test_health.py`, `test_settings.py` | Existen (C01) |
| Routers `/v1/*`, schemas, stubs, auth JWT, `openapi.json` | **Ausente** |
| Specs vivas `ai-service-runtime`, `ai-service-dev-compose` | Existen (C01) |
| Artefactos OpenSpec de este change (proposal, design, specs, tasks) | **A regenerar** desde esta HU y este ticket |

**Impacto en producto:** ninguno visible para el operador. El valor es desbloquear C03 y el slice vertical (C14–C16) sin esperar a LLM ni a índice reales.

---

## Componentes Afectados

| Componente | Impacto |
|---|---|
| `ai-service/` (`jbg_ai`) | **Principal** — routers, schemas, auth, stubs, settings, tests, `openapi.json`, README |
| `backend/docker-compose.yml` | Entorno del servicio `jbg-ai`: `JWT_SECRET`, `STUB_MODE` |
| `openspec/changes/add-ai-service-contracts-and-auth/` | Artefactos del change (a regenerar) y este ticket |
| `openspec/specs/` | Nuevas capabilities `ai-service-api-contracts` y `ai-service-auth`; delta sobre `ai-service-runtime` |
| `Documentos/Historias/AI-Eng/HU-AIENG-002.md` | Historia de usuario origen |
| `Documentos/modelo-c4.md`, `Documentos/arquitectura.md`, `Documentos/epicas.md` | **Ya actualizados** (contenedor `jbg-ai`, frontera y EP11–EP17). Fuera del apply salvo delta nuevo |
| `backend/` (.NET) | **Sin código en este change** — consumidor futuro en C03 |
| `frontend/` | Sin impacto: la SPA nunca habla con Python |
| Base de datos / Alembic | Sin impacto: el acceso a datos entra en C05 |

---

## Especificaciones Técnicas

### Servicio Python (`ai-service`)

**Endpoints** (todos internos, nunca expuestos por nginx; JWT salvo health):

| Método | Ruta | Auth | Notas |
|---|---|---|---|
| `POST` | `/v1/retrieval/products` | Bearer JWT | Stub: `min(top_k × 3, 60)` resultados y `candidates_returned` |
| `POST` | `/v1/retrieval/substitutes` | Bearer JWT | Mismo shape de resultado más `similarity_signals` |
| `POST` | `/v1/assist/sale` | Bearer JWT | `groups[]` por `family_id` con `variant_label`; `pitch` con `{{price}}` / `{{stock}}` |
| `POST` | `/v1/inventory/propose` | Bearer JWT | Lista priorizada mínima (delta v3) |
| `POST` | `/v1/enrich/products` | Bearer JWT | Perfiles por lote con confianza por campo y `materials[]` |
| `POST` | `/v1/index/sync` | Bearer JWT | Cursor `since`; contadores de upsert |
| `GET` | `/v1/index/status` | Bearer JWT | `drift_count`, `last_full_sync_at` |
| `GET` | `/v1/evals/runs` | Bearer JWT | **Solo perfil de desarrollo**; lista determinista de ejecuciones |
| `GET` | `/health` | **Público** | Sin cambios de contrato respecto a C01 |

**Modelos Pydantic (mínimo exigible):**

- *Retrieval request*: `query`, `top_k`, `filters` (incluye `materials: list[str]`), `mode`; `pos_id` opcional y **ignorado**.
- *Retrieval result*: `product_id`, `sku`, `score`, `match_reasons`, `materials`, `family_id`, `variant_label`, `debug?`.
- *Retrieval response*: `results[]`, `candidates_returned`, `low_confidence`, `trace_id`.
- *Assist response*: `intent`, `groups[]`, `pitch`, `citations[]`, `warnings[]`, `clarification_question?`, `usage`.
- *Enrich response*: lote de perfiles propuestos con confianza por campo.
- *Index*: contadores de upsert y estado de deriva. *Inventory*: propuestas priorizadas. *Evals*: ejecuciones con métricas.

Los campos opcionales (`debug`, `usage`, `match_reasons`, `similarity_signals`) se incluyen aunque el stub los rellene de forma mínima: reducen la probabilidad de reabrir el contrato en la Ola 4.

**Autenticación:**

- `PyJWT`, algoritmo HS256, secreto en `JWT_SECRET`.
- Claims obligatorios: `user_id`, `role`, `pos_id`, `trace_id`.
- Dependencia FastAPI → `ServicePrincipal`; 401 si el token falta, está mal firmado, ha caducado o le faltan claims.
- **Regla: el token manda.** El body nunca sobrescribe `pos_id` ni `role`.
- `trace_id`: se prefiere el claim; si no viene, se mantiene el `TraceIdMiddleware` de C01.

**Settings nuevas** (sobre las de C01):

| Variable | Obligatoria | Default | Notas |
|---|---|---|---|
| `JWT_SECRET` | sí | — | Fail-fast si falta o está vacío |
| `JWT_TTL_SECONDS` | no | `300` | Documentado; en producción vía SSM (C17) |
| `STUB_MODE` | no | `true` | `true` en local y test |
| `ENABLE_DEV_ENDPOINTS` | no | `true` salvo perfil de producción | Controla el montaje de `/v1/evals/runs` |

**Stubs:**

- `STUB_MODE=true` → fixtures deterministas, sin ninguna E/S externa.
- `STUB_MODE=false` y sin implementación real → HTTP 501 con mensaje que indica el change que la aportará.

**OpenAPI:**

- Fichero versionado `ai-service/openapi.json`, generado desde `create_app(...).openapi()`.
- Test de igualdad estricta contra el fichero committeado.
- Se genera con el **perfil canónico documentado en el README** (endpoints de desarrollo incluidos) para que el snapshot sea determinista.
- `docs_url` sigue en `None`: el artefacto es el snapshot, no una Swagger UI pública.

**Layout propuesto:**

```text
ai-service/src/jbg_ai/
  api/auth.py, deps.py
  api/routers/{retrieval,assist,inventory,index,enrich,evals}.py
  api/schemas/...
  stubs/responses.py
  config/settings.py
ai-service/openapi.json
ai-service/tests/test_auth.py, test_retrieval_stub.py, test_openapi_snapshot.py, test_stub_mode.py
```

### Fuera de este ticket

- Emisión y firma del JWT e `IAiGatewayClient` con Polly (.NET) → C03.
- Lógica real de retrieval, enrich e index → C09 y posteriores.
- `complementary` y `families/suggest` → changes posteriores, con negociación del OpenAPI.
- Esquema `ai`, extensión `vector` y Alembic → C05. Despliegue y SSM → C17.

---

## Arquitectura

- **Frontera:** SPA → JWT de usuario → API .NET → JWT interno → `jbg-ai` (diseño v3 §6.1 y §6.4). Regla de una frase: *Python calcula parecidos y redacta; .NET calcula números y decide*.
- **Patrones:** routers FastAPI con `Depends` de autenticación; `pydantic-settings`; stubs inyectables; `TestClient` en proceso (patrón heredado de C01).
- **Capabilities OpenSpec:** nuevas `ai-service-api-contracts` y `ai-service-auth`; delta sobre `ai-service-runtime` (settings de JWT y stubs).
- **Breaking changes:** ninguno para consumidores externos, porque todavía no los hay. El Compose local sí necesita las variables nuevas.
- **ADRs:** este repositorio no tiene `memory-bank/`; las decisiones equivalentes viven en `openspec/changes/archive/*/design.md` y en la tabla de decisiones de `Documentos/arquitectura.md`.

```text
.NET (futuro C03) --Bearer JWT--> jbg-ai /v1/*
                                   ├─ valida HS256 → ServicePrincipal
                                   ├─ principal.pos_id (body ignorado)
                                   └─ STUB_MODE ? fixture determinista : 501
GET /health --------------------------> público (C01)
GET /v1/evals/runs -------------------> solo perfil de desarrollo
```

---

## Criterios de Aceptación

Condiciones verificables para dar el ticket por hecho:

1. Los ocho endpoints `/v1/*` responden con cuerpos que validan contra sus modelos Pydantic, y `/health` sigue público.
2. Toda petición a `/v1/*` sin token válido responde 401, sin filtrar detalle del secreto ni de la causa.
3. El scope efectivo procede siempre del token; un `pos_id` distinto en el body no altera el comportamiento ni provoca error.
4. Con `STUB_MODE=true` no se produce ninguna llamada a LLM, embeddings o base de datos.
5. Con `STUB_MODE=false` y sin implementación real, la respuesta es 501.
6. `ai-service/openapi.json` está committeado y coincide con el esquema vivo.
7. Arrancar sin `JWT_SECRET` falla de inmediato con un error que identifica la variable.

**Pruebas de validación** (`uv run pytest` desde `ai-service/`):

| Test | Cubre |
|---|---|
| `test_retrieval_stub_matches_response_schema` | Criterios 1 y 4 |
| `test_over_retrieval_returns_capped_candidates` | `top_k = 5 → 15`; `top_k = 30 → 60` |
| `test_assist_sale_groups_by_family` | `groups[]`, `variant_label`, placeholders sin resolver |
| `test_request_without_token_is_rejected` | Criterio 2 |
| `test_invalid_token_is_rejected` | Criterio 2 (firma, caducidad, claims ausentes) |
| `test_pos_id_from_token_overrides_body_value` | Criterio 3 |
| `test_health_is_public` | Criterio 1 |
| `test_unimplemented_route_returns_501_when_stub_mode_off` | Criterio 5 |
| `test_openapi_snapshot_is_stable` | Criterio 6 |
| `test_settings_fail_fast_when_jwt_secret_missing` | Criterio 7 |
| `test_dev_only_evals_route_absent_in_prod_profile` | Montaje condicional de evals |

---

## Definición de Hecho (DoD)

- [ ] Artefactos OpenSpec del change regenerados y coherentes con HU-AIENG-002 y este ticket
- [ ] Código implementado según el layout y las decisiones de este ticket
- [ ] Los once tests de la tabla anterior en verde con `uv run pytest`
- [ ] Sin llamadas reales a LLM, embeddings ni RDS en la suite de tests
- [ ] `ai-service/openapi.json` committeado y alineado con el esquema vivo
- [ ] `ai-service/README.md` y `backend/docker-compose.yml` actualizados con `JWT_SECRET` y `STUB_MODE`
- [ ] Documentación de arquitectura (`modelo-c4.md`, `arquitectura.md`, `epicas.md`) ya incorpora `jbg-ai` — no requiere trabajo en este change salvo delta nuevo del apply
- [ ] Sin `TODO` ni `FIXME` sin tarea de seguimiento asociada
- [ ] `openspec validate` y el verify del change en verde antes de archivar

---

## Requisitos No Funcionales

- **Seguridad:** solo JWT de servicio en `/v1/*`; el secreto nunca se committea (local en Compose, producción en SSM `/jpv/prod/*` en C17); health público de forma deliberada; el puerto de Python no se publica en nginx. Los errores de autenticación no revelan la causa exacta.
- **Rendimiento:** los stubs son O(1) y no hacen E/S. Los objetivos reales de latencia (retrieval p95 < 500 ms, assist p95 < 3,5 s) y los timeouts de 0,8 s / 5 s pertenecen a C03 y a los changes de implementación.
- **Observabilidad:** `trace_id` desde el claim del JWT o desde el middleware de C01; logging estructurado ya existente.
- **Determinismo:** mismo input, misma respuesta. C03 construirá sus tests de mapeo contra estos stubs.
- **Contrato:** cualquier cambio de schema rompe el snapshot y obliga a una negociación explícita entre los dos desarrolladores.
- **Integridad de la frontera:** Python no lee ni escribe `public` por SQL, y no emite cifras de precio ni de stock: las deja como placeholders para que .NET las resuelva.

---

## Preguntas Abiertas → Decisiones (cerradas antes de artefactos OpenSpec)

1. **TTL local por defecto del JWT → `300` s (confirmado).**  
   Corto para un JWT de servicio hop-to-hop (no es sesión de usuario), alineado con “TTL corto” del diseño. Suficiente para una llamada + reintentos de Polly; en producción el valor real llega por SSM en C17. `JWT_TTL_SECONDS=300` queda como default documentado en settings y README.

2. **Nombre exacto de los claims frente a .NET → `snake_case` en el wire (`user_id`, `role`, `pos_id`, `trace_id`).**  
   **Decisión:** Python congela esos nombres literales en el payload JWT. C03 es el único responsable de emitir el token con esas claves (aunque el dominio .NET use `PointOfSaleId` en C#).  
   **Por qué:** el diseño v3/3devs ya escribe `pos_id` en la frontera; OpenAPI y PyJWT leen JSON keys, no propiedades C#. Duplicar aliases (`pos_id` *y* `pointOfSaleId`) complica validación y tests sin beneficio mientras solo haya un emisor (.NET). Si en C03 aparece fricción con librerías JWT de ASP.NET, se resuelve allí con un mapper al firmar, no reabriendo el contrato Python.

3. **Regeneración del OpenAPI → comparación en test + regeneración manual documentada (sin script en C02).**  
   **Decisión:** el test `test_openapi_snapshot_is_stable` falla si el esquema vivo ≠ `openapi.json`; el README documenta el comando one-liner para regenerar (p. ej. `uv run python -c "..."` o equivalente mínimo). **No** se añade `jbg_ai.tools.export_openapi` en este change.  
   **Balance:** un módulo/script dedicado ahorra poco (la regeneración ocurre pocas veces, solo al negociar contrato) y añade superficie a mantener, entrypoint, y riesgo de que el script y el test usen perfiles distintos. El beneficio real del snapshot es el **fail en CI**, no el DX de regenerar. Si en Ola 4 la regeneración se vuelve frecuente, se puede extraer el one-liner a un script sin tocar el contrato.

4. **Gating de `/v1/evals/runs` → montar solo si `ENABLE_DEV_ENDPOINTS` (derivado de `APP_ENV`); snapshot con perfil de desarrollo.**  
   **Decisión confirmada.** Implicaciones:
   - En **producción** la ruta **no existe** en el router: FastAPI responde 404 genérico de “ruta no encontrada”, no un 404 de negocio documentado. El path no aparece en un OpenAPI generado con perfil prod.
   - El **`openapi.json` versionado** se genera con el **perfil canónico de desarrollo** (evals incluido), documentado en el README. Así el snapshot es determinista y C03/.NET ven el contrato completo de lo que pueden llamar en local.
   - **Trade-off aceptado:** el snapshot de repo **no** es idéntico al esquema que expondría un despliegue prod (faltaría evals allí). Eso es deliberado: evals es herramienta de desarrollo, no API de producto. Alternativa “montar siempre y 404 en prod” contaminaría el contrato publicado con una ruta que en prod no debe usarse y obligaría a documentar un 404 semántico engañoso.
   - Tests obligatorios: ruta presente + 200 en perfil dev; ruta ausente en perfil prod.

---

## Prioridad / Estimación / Tags

- **Prioridad:** Alta — Ola 0, ruta crítica 🔴; bloquea C03 y todo el trabajo en paralelo.
- **Estimación:** **8 SP** (propuesta del PO, a validar en refinamiento). Amplitud alta y capa de autenticación nueva, sin lógica real ni base de datos.
- **Tags:** `HU-AIENG-002`, `C02`, `jbg-ai`, `ai-service`, `contracts`, `jwt`, `openapi`, `stubs`, `feature`, `python`, `tests`
- **Asignación:** cualquiera de los dos desarrolladores del PF (regla del plan: coger el 🔴 libre).

---

## Enlaces o Referencias

- **User Story:** [HU-AIENG-002.md](../../../../Documentos/Historias/AI-Eng/HU-AIENG-002.md)
- **HU prerrequisito:** [HU-AIENG-001.md](../../../../Documentos/Historias/AI-Eng/HU-AIENG-001.md) (change archivado `init-ai-service-skeleton`)
- **Change:** `openspec/changes/add-ai-service-contracts-and-auth/`
- **Plan:** ficha C02 en [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Diseño:** v3 §6.1–6.4, §7.6–7.7 · 3devs §6.8
- **Contexto de proyecto:** `openspec/project.md`
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-08-05 | Creación del ticket enriquecido al abrir el change C02 |
| 2026-08-05 | Reescritura con `/enrich-us` adaptado: se añade `GET /v1/evals/runs`, criterios de aceptación con pruebas de validación, cuatro tests nuevos, settings de evals y estimación propuesta |
| 2026-08-06 | Componentes afectados: docs de arquitectura ya actualizados. Preguntas abiertas cerradas (TTL 300s, claims `snake_case`, OpenAPI manual sin script, gating evals con `ENABLE_DEV_ENDPOINTS`) |
