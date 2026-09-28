# Historial de pull requests

Este proyecto se desarrolló en [`skydr4g0n-it/joiabagur-pv`](https://github.com/skydr4g0n-it/joiabagur-pv),
donde se revisó e integró cada cambio mediante pull requests. Al trasladar el repositorio a
[`SValduezaL/joiabagur-pv`](https://github.com/SValduezaL/joiabagur-pv) el historial de commits viaja
completo, pero las páginas de las PR no se pueden copiar. Esta carpeta conserva su contenido, una página por PR:
número, título, autor, ramas, fechas, descripción y comentarios, con el enlace a la PR original.

**Total:** 54 pull requests.

| # | Título | Estado | Ramas | Integrada |
|---|---|---|---|---|
| [#1](pr-01.md) | Entrega 1: Documentación del proyecto y estructura inicial del frontend | MERGED | `feature-entrega1-MO` → `master` | 2026-01-17 |
| [#2](pr-02.md) | Feature-entrega3-MO | MERGED | `feature-entrega3-MO` → `master` | 2026-02-04 |
| [#3](pr-03.md) | Feature entrega3 mo | MERGED | `feature-entrega3-MO` → `master` | 2026-02-05 |
| [#4](pr-04.md) | docs: diseño del sistema de IA (RAG) para el Proyecto Final — v3, consenso tras revisión | MERGED | `docs/proyecto-final-ia` → `master` | 2026-08-03 |
| [#5](pr-05.md) | C01: init ai-service skeleton (jbg-ai) | MERGED | `c01-init-ai-service-skeleton` → `ai-eng` | 2026-08-03 |
| [#6](pr-06.md) | feat(ai-service): congelar contratos /v1 y auth interna de jbg-ai | MERGED | `c02-add-ai-service-contracts-and-auth` → `ai-eng` | 2026-08-06 |
| [#7](pr-07.md) | feat(backend): añade cliente tipado hacia jbg-ai con resiliencia (C03) | MERGED | `c03-add-dotnet-ai-gateway-client` → `ai-eng` | 2026-08-09 |
| [#8](pr-08.md) | feat(telemetry): registrar el ciclo consulta→selección (C04) | MERGED | `c04-add-product-search-event-tracking` → `ai-eng` | 2026-08-11 |
| [#9](pr-09.md) | feat(ai-service): esquema ai con pgvector, migraciones Alembic y pool acotado (C05) | MERGED | `c05-add-pgvector-schema-foundation` → `ai-eng` | 2026-08-15 |
| [#10](pr-10.md) | feat(ai): perfil IA revisable del catálogo con revisión híbrida por campo (C08) | MERGED | `c08-add-product-ai-profile-entity` → `ai-eng` | 2026-08-16 |
| [#11](pr-11.md) | feat(backend): familias de producto como entidad de negocio editable (C07) | MERGED | `c07-add-product-family-entity` → `ai-eng` | 2026-08-16 |
| [#12](pr-12.md) | feat(catalog): corpus real enriquecido y pipeline offline C06a | MERGED | `feature/add-real-catalog-ingestion-and-text-assist` → `ai-eng` | 2026-08-22 |
| [#13](pr-13.md) | feat(ai-service): añadir CLI y corpus sintético C06b | MERGED | `feature/add-synthetic-catalog-augmentation` → `ai-eng` | 2026-08-23 |
| [#14](pr-14.md) | feat(ai-service): extraer perfiles reales en POST /v1/enrich/products | MERGED | `c09-add-catalog-enrichment-pipeline` → `ai-eng` | 2026-08-23 |
| [#15](pr-15.md) | feat(ai-service): añadir CLI world simulate/ingest (C10) | MERGED | `c10-add-synthetic-world-simulator` → `ai-eng` | 2026-08-23 |
| [#16](pr-16.md) | feat(ai-service): añadir source-text/v1 y cliente de embeddings 1536d | MERGED | `c11-add-source-text-and-embedding-client` → `ai-eng` | 2026-08-25 |
| [#17](pr-17.md) | feat(api): añadir feeds HTTP de indexación con cursor y API Key | MERGED | `c12-add-dotnet-index-feed-endpoints` → `ai-eng` | 2026-08-25 |
| [#18](pr-18.md) | feat(ai-service): drenar el feed de catálogo hacia ai.product_document | MERGED | `c13-add-product-document-indexer` → `ai-eng` | 2026-08-26 |
| [#19](pr-19.md) | feat(ai-service): implementar retriever vectorial de products | MERGED | `c14-add-vector-retrieval-endpoint` → `ai-eng` | 2026-08-27 |
| [#20](pr-20.md) | feat(backend): POST /api/ai/search con hidratación autoritativa y degradación (C15) | MERGED | `c15-add-dotnet-ai-search-endpoint` → `ai-eng` | 2026-08-28 |
| [#21](pr-21.md) | feat(frontend): panel de búsqueda asistida y atribución de la venta (C16) | MERGED | `c16-add-frontend-assisted-search-panel` → `ai-eng` | 2026-08-29 |
| [#22](pr-22.md) | feat(infra): entorno de demostración aislado para el servicio de IA | MERGED | `c17-add-ai-service-deployment` → `ai-eng` | 2026-08-30 |
| [#23](pr-23.md) | feat(ai-service): agrupacion asistida de familias de producto y su aprobacion por lote | MERGED | `c18a-add-family-suggestion-and-approval` → `ai-eng` | 2026-08-31 |
| [#24](pr-24.md) | feat(ai): revisión humana de familias y alerta de huérfanos — décima ruta del contrato (C18b) | MERGED | `c18b-add-family-review-ui-and-orphan-alert` → `ai-eng` | 2026-09-01 |
| [#25](pr-25.md) | feat(ai-service): expansión de consulta con diccionario de sinónimos (C20) | MERGED | `c20-add-synonym-dictionary` → `ai-eng` | 2026-09-01 |
| [#26](pr-26.md) | feat(ai-service): fusionar rama léxica y vectorial con RRF ponderado | MERGED | `c21-add-hybrid-search-rrf` → `ai-eng` | 2026-09-02 |
| [#27](pr-27.md) | C22: sincroniza ai.pos_projection y acota la recuperación al surtido del punto de venta | MERGED | `c22-add-pos-projection-soft-prefilter` → `ai-eng` | 2026-09-05 |
| [#28](pr-28.md) | fix(ai-service): cerrar las lagunas de piece_type con enrichment/v2 | MERGED | `fix1-enrichment-vocabulary-gaps` → `ai-eng` | 2026-09-05 |
| [#29](pr-29.md) | feat(ai-service): añadir el corpus de conocimiento y su índice de citas | MERGED | `c23-knowledge-corpus-and-indexer` → `ai-eng` | 2026-09-06 |
| [#30](pr-30.md) | feat(ai-service): añadir arnés de evaluación, golden set y líneas base | MERGED | `c24-eval-harness-golden-set-and-baselines` → `ai-eng` | 2026-09-11 |
| [#31](pr-31.md) | C25: la fusion hibrida se compone en dos etapas, y el buscador aprende a callar | MERGED | `c25-recalibrate-ranking-and-abstention` → `ai-eng` | 2026-09-12 |
| [#32](pr-32.md) | Retira la fusión plana y los pesos por lista: 315 filas idénticas (C25bis) | MERGED | `c25bis-clean-plain-fusion` → `ai-eng` | 2026-09-12 |
| [#33](pr-33.md) | feat(ai-service): implementar sustitutos sobre el embedding almacenado | MERGED | `c26-add-substitutes-retrieval` → `ai-eng` | 2026-09-12 |
| [#34](pr-34.md) | feat(profile-review): revisión humana de perfiles y sus métricas | MERGED | `c28-add-profile-review-ui-and-metrics` → `ai-eng` | 2026-09-13 |
| [#35](pr-35.md) | feat(ai-service): servir la capa estructurada de venta asistida (C30a) | MERGED | `c30a-add-assist-structure-and-rule-warnings` → `ai-eng` | 2026-09-13 |
| [#36](pr-36.md) | feat(ai-service): generar el argumentario de venta con tres puertas (C30b) | MERGED | `c30b-add-assist-pitch-generation` → `ai-eng` | 2026-09-14 |
| [#37](pr-37.md) | feat(ai-service)!: clasificar la consulta antes de recuperar nada (C31) | MERGED | `c31-add-guardrails-and-intent-router` → `ai-eng` | 2026-09-16 |
| [#38](pr-38.md) | feat(ai-service): registrar seis tools de solo lectura del agente (C32a) | MERGED | `c32a-add-sales-assistant-tool-registry` → `ai-eng` | 2026-09-20 |
| [#39](pr-39.md) | feat(ai-service): añadir el bucle agéntico del asistente de venta | MERGED | `c32b-add-sales-assistant-agent-loop` → `ai-eng` | 2026-09-21 |
| [#40](pr-40.md) | feat(backend): rutas .NET del card de venta con hidratación y marcadores | MERGED | `c34-add-dotnet-assist-and-recommendation-endpoints` → `ai-eng` | 2026-09-22 |
| [#41](pr-41.md) | feat(frontend): añadir la ficha de venta con desambiguación por familia | MERGED | `c36-add-frontend-assist-card-and-family-disambiguation` → `ai-eng` | 2026-09-24 |
| [#42](pr-42.md) | feat(ai-search): dar pantalla y ruta propia a la consulta libre | MERGED | `c40-add-frontend-free-query-panel` → `ai-eng` | 2026-09-25 |
| [#43](pr-43.md) | fix(sales): hacer alcanzable el ambito de todas las tiendas | MERGED | `c40-fix-all-shops-scope-unreachable` → `ai-eng` | 2026-09-26 |
| [#44](pr-44.md) | C41: la proyeccion de disponibilidad se drena sola al arrancar y cada 600 s | MERGED | `c41-add-pos-projection-scheduled-drain` → `ai-eng` | 2026-09-26 |
| [#45](pr-45.md) | feat(sales): dar pantalla al agente de venta y su consumidor .NET | MERGED | `c42-add-frontend-agent-panel` → `ai-eng` | 2026-09-26 |
| [#46](pr-46.md) | feat(demo): preparar el redespliegue del entorno de demostración y auditar su configuración | MERGED | `c39a-redeploy-and-audit-demo-environment` → `ai-eng` | 2026-09-27 |
| [#47](pr-47.md) | release(demo): desplegar C36, C40, C40_FIX, C41, C42 y C39a — las cuatro superficies de IA al entorno de demostración | MERGED | `ai-eng` → `demo` | 2026-09-27 |
| [#48](pr-48.md) | docs(demo): verificar el entorno desplegado y declarar sus cuentas | MERGED | `c39abis-verify-demo-redeployment` → `ai-eng` | 2026-09-27 |
| [#49](pr-49.md) | C43 · La verificación del despliegue deja de juzgar mal un entorno correcto | MERGED | `c43-add-shop-activity-projection` → `ai-eng` | 2026-09-27 |
| [#50](pr-50.md) | Pone la demo al día: C39a-bis y C43 — el despliegue deja de fallar por un entorno sano | MERGED | `ai-eng` → `demo` | 2026-09-27 |
| [#51](pr-51.md) | Arregla el drenaje de arranque: reintenta por drenaje, no por pasada | MERGED | `c43-fix-boot-drain-retries-both-drains` → `ai-eng` | 2026-09-27 |
| [#52](pr-52.md) | Arregla el drenaje de arranque que dejó ai.pos_shop vacía en el despliegue anterior | MERGED | `ai-eng` → `demo` | 2026-09-27 |
| [#53](pr-53.md) | Cierra el Proyecto Final: entregable, criterio de recuento y evidencias (C39b) | MERGED | `c39b-finalize-pf-readme-and-evidence` → `ai-eng` | 2026-09-27 |
| [#54](pr-54.md) | Pone demo al día con ai-eng: cierre del Proyecto Final (C39b) | MERGED | `ai-eng` → `demo` | 2026-09-27 |


