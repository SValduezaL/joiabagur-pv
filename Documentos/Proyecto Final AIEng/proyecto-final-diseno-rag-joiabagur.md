# Proyecto Final de Máster — Diseño del sistema de IA para Joiabagur PV

**Versión:** 3 — consenso tras la revisión de la [PR #4](https://github.com/skydr4g0n-it/joiabagur-pv/pull/4) y las [especificaciones funcionales v2](joiabagur-ia-especificaciones-funcionales-v2.md)
**Documento:** diseño conceptual + estrategia de datos + plan de ejecución
**Dominio:** Joiabagur PV (gestión de puntos de venta de joyería)
**Fecha de entrega del PF:** **prórroga abierta desde el 2026-08-31** — sin fecha; el objetivo es entregar cuanto antes
**Rama de entrega:** `finalproject-[INICIALES]` *(placeholder)*
**Equipo:** **1 desarrollador**, trabajando en Python, .NET y frontend
**Descomposición ejecutable:** [proyecto-final-plan-changes-openspec.md](proyecto-final-plan-changes-openspec.md)

> **Tres supuestos de la versión 3 dejaron de valer el 2026-08-31**, y el documento se lee con eso puesto: la entrega tenía fecha y ahora tiene **prórroga abierta**; el equipo eran **dos personas y ahora es una**; y el **agente de inventario se anula** junto con toda su rama de implementación (C19, C29, C33, C35, C37). El razonamiento completo está en el §0 del documento hermano. Aquí las secciones afectadas —§4, §9, §10, §11, §13, §14, §15 y §16— llevan la corrección en el sitio, y **el §10 se conserva íntegro a propósito**: es el diseño que el README adjunta como próximo paso.

---

## 0. Resumen ejecutivo

Construimos un **buscador semántico de catálogo con venta asistida** para operadores de joyería, servido por un microservicio RAG en Python sobre pgvector e integrado en el backend .NET existente, con un **agente asistente de venta** de tools de solo lectura y humano en el bucle.

El **agente de inventario** —reposiciones y traslados con aprobación humana— estaba en el alcance acordado y **se anula el 2026-08-31**: no aportaba nada al sistema RAG (la señal de demanda que pondera el ranking ya llega por el feed de indexación) y costaba cinco changes de los que tres no tenían LLM. Su diseño se conserva completo en el §10 y se entrega como próximo paso documentado.

### Qué cambia respecto a la versión anterior

La revisión del compañero es acertada en casi todo y **se acepta en bloque** la parte de modelo de datos y disciplina. Los cambios estructurales:

| Cambio | Origen |
|---|---|
| `material` → **`materials[]`** en todo el pipeline (extracción, filtros, `SourceText`, evaluación) | Revisión, decisión 3 |
| `variant_group_key` → **`ProductFamily` + `ProductFamilyMember`** como entidad explícita y editable | Revisión, decisión 2 |
| **No se persiste texto comercial generado por IA** en el perfil del producto: fuera `SalesPitchShort`, `OperatorHint`, `CareInstructions`, `SearchAliases` | Revisión, decisión 4 |
| **Revisión humana híbrida**: campos sensibles siempre revisados si son inferidos; tags comerciales auto-aprobables | Revisión, decisión 5 |
| **La proyección de inventario nunca excluye**: prefiltro blando + sobre-recuperación; .NET decide | Revisión, decisión 11 |
| **Toda regla de negocio vive en .NET.** Python solo hace lo que necesita el espacio vectorial y el LLM | Revisión, decisión 9 |
| **Entra inventario**: reposición, traslados, rotación/stock parado, sustitutos y aprobación manual | Revisión, decisión 6 |
| **Entra argumentario por POS** como perfil calculado periódicamente y almacenado estructurado | Revisión, decisión 7 |
| **Entran complementarios** por reglas + co-ocurrencia de ventas | Revisión, decisión 8 |

### Las tres decisiones que no acepto tal cual

Las dos primeras están **⏳ pendientes de acuerdo** y se cierran en conversación, no en este documento. Ambas van planteadas de forma que la discusión sea sobre el intercambio, no sobre el gusto.

1. **⏳ `SearchAliases` fuera, sí — pero hace falta un sustituto.** Sin alias, la rama léxica no encuentra "sortija" cuando el producto se llama "anillo". La solución no es persistir alias por producto (tiene razón: es texto IA por producto, con deriva), sino un **diccionario de sinónimos del dominio, único, curado a mano** (~40-60 entradas), aplicado en expansión de consulta. Cumple su principio y resuelve mejor el problema (§7.4).
   **Si no hay acuerdo:** se implementa igual **tras un flag**, se mide con la categoría de sinónimos del golden set y se decide con el número, no con el argumento. Coste de discrepancia: cero.
2. **⏳ Packing list fuera del PF.** Es el único punto de su "mínimo" que no acepto: es la única pieza del bloque de inventario con **cero contenido de IA**, tiene una máquina de 6 estados con auditoría y está *aguas abajo* de las recomendaciones aprobadas, así que aplazarla no bloquea nada. En su lugar entra una **vista imprimible de recomendaciones aprobadas agrupadas por POS**.
   **Si no hay acuerdo:** entra, cuesta **+1,5-2 changes en la ola 4**, que ya es la más cargada, y arrastra el corte de **complementarios y rotación** (puntos 1 y 2 de §13.4). El intercambio es ese, y es una decisión de producto legítima: packing list a cambio de complementarios y detección de stock parado.
3. **Upselling y downselling fuera.** El margen es calculable (`ProductComponentAssignment.CostPrice`/`SalePrice` existen), así que es viable técnicamente, pero es estrategia de precio sin datos que la validen antes del 3 de septiembre. Este no está en discusión.

### Restricciones que gobiernan el documento

**Tiempo:** *(reescrito el 2026-08-31)* **prórroga abierta, sin fecha de entrega.** El objetivo es entregar cuanto antes, y en consecuencia lo que ordena el trabajo no es el calendario sino el **desbloqueo del grafo de dependencias** (§4 del documento hermano). **Equipo: una persona.** De las 41 fichas planificadas quedan **36 vivas**: 19 archivadas y 17 pendientes. El orden de corte del §13.4 sigue fijado de antemano, y ahora tiene cuatro posiciones en vez de ocho.

> **Alcance de la entrega (respuesta a la decisión 1):** esto es **Fase 1 completa + Fase 3 parcial** de las especificaciones v2. Packing list (Fase 4), liquidación con descuentos, upsell/downsell, políticas de inventario configurables y —**desde el 2026-08-31**— el **agente de inventario completo** quedan **explícitamente fuera** y documentados como fase posterior.

---

## 1. Punto de partida verificado en el repositorio

| Área | Estado real | Implicación |
|---|---|---|
| Backend | .NET 10, capas Domain/Infrastructure/Application/API, EF Core, PostgreSQL, JWT, Serilog, 18 controllers | El servicio de IA se acopla por HTTP, no por código |
| Modelo de dominio | `Product`, `Collection`, `Inventory` (Product×POS), `InventoryMovement`, `Sale` (precio congelado), `PointOfSale`, `User`/`UserPointOfSale`, `Return`, `ProductPhoto` | Todas las señales del RAG y del inventario ya existen |
| **Margen por producto** | `ProductComponent` + `ProductComponentAssignment` (`CostPrice`, `SalePrice`, `Quantity`) y `ComponentReportService` | El margen **es calculable**. Habilita "prioridad comercial" como señal futura; fuera de este alcance por tiempo, no por imposibilidad |
| Búsqueda actual | `GET /api/products/search` → SKU exacto + nombre parcial, máx. 50, filtrado por POS asignados ([ProductsController.cs:92](../../backend/src/JoiabagurPV.API/Controllers/ProductsController.cs#L92)) | Es el **baseline v0-lexico** y el **fallback** |
| **Tienda central** | **No existe** como concepto: `PointOfSale` solo tiene Name, Code, Address, Phone, Email, IsActive, AllowManualPriceEdit | **Bloquea las reglas de reposición y traslado.** Ver pregunta abierta en §14 |
| IA existente | Reconocimiento **visual**: `ProductPhotoEmbedding` (MobileNetV2 1280d en JSON), TF.js en navegador | No se toca. Otro problema, otro espacio vectorial |
| pgvector | **No instalado** | Trabajo nuevo: extensión en RDS + esquema propio |
| Datos versionados | Solo admin y métodos de pago en el seeder. **Sin catálogo, inventario ni ventas** | Sin export real, el corpus es sintético. Ver §8 |
| Despliegue | EC2 + nginx + Docker + RDS + S3 + ECR + GitHub Actions OIDC. Producción viva en `pv.joiabagur.com` | Añadimos un contenedor |
| Metodología | OpenSpec en uso | El trabajo se entrega como *changes* |
| Frontend | React 19 + Vite + TS + Metronic, `src/pages/sales/` con flujo manual y `scan.tsx` | Punto de inserción del panel de búsqueda |

---

## 2. Análisis crítico de las especificaciones funcionales v2

La v2 corrige la mayoría de lo que criticaba la versión anterior de este documento: `Materials[]`, familias explícitas, sin textos comerciales persistidos, avisos por reglas. Lo que sigue es lo que **queda por resolver**.

### 2.1. Lo que la v2 resuelve bien y se adopta sin cambios

`Materials[]` como array · `ProductFamily`/`ProductFamilyMember` editable · avisos calculados por reglas y no persistidos · principio 2 (IA no es fuente de verdad de stock/precio) · principio 5 (control por POS) · `SourceHash` e idempotencia · versionado de embeddings · separación embeddings visuales/semánticos · matriz §7.3 de cuándo usar generativa, embeddings o reglas · `InventoryRecommendation` con estados y aprobación humana.

### 2.2. Lo que sigue sin resolverse en la v2

| Punto | Problema | Resolución adoptada |
|---|---|---|
| **Arquitectura §7.1** sigue colocando todo en .NET (`Application/AiCatalog`, `AiSalesAssist`, `AiInventory`) | Incompatible con el requisito del PF de implementar RAG en Python, y con el instrumental del máster (pgvector desde Python, RAGAS) | Frontera precisa en §6: **.NET conserva toda la regla de negocio** (incluido el motor de inventario), Python solo espacio vectorial y LLM |
| **Sin capa de evaluación.** La v2 tiene KPIs de negocio pero ninguna métrica de sistema | El PF exige evals objetivas; es criterio explícito de "destaca" | §11 como componente de primera clase |
| **Sin agentes.** La v2 los excluye ("agentes que modifiquen stock sin aprobación humana") | El PF los exige. La tensión es aparente: lo prohibido es **escribir** sin aprobación | Agentes con tools de **solo lectura** + HITL en toda escritura (§9) |
| **Eliminar `SearchAliases` sin sustituto** deja ciega la rama léxica ante sinónimos | "sortija", "aro", "gargantilla" no aparecen en el catálogo | Diccionario de sinónimos del dominio, curado, en expansión de consulta (§7.4) |
| **`ProductFamily` sin definir quién la crea** (decisión abierta 4 de la v2) | Crear ~350 familias a mano es inviable | **Flujo mixto**: la IA propone familias por similitud, el admin aprueba o edita (§7.5) |
| **Ranking §5.5 con 8 términos** | No hay datos para calibrar 8 pesos en 4 semanas | 4 señales calibradas contra el golden set; el resto documentado (§7.6) |
| **`ProductRecommendation` precomputada** para Similar/Complementary/Substitute | Precomputar similitud es caché prematura: el retriever la calcula en milisegundos | La tabla existe **solo para curación manual** (complementarios configurados por el admin). Similar y sustituto se calculan en línea |
| **Sin concepto de tienda central** pese a que las reglas de reposición lo asumen | `PointOfSale` no distingue tipos | Pregunta abierta §14. Mitigación provisional: campo `IsSupplySource` en POS |
| **KPIs de negocio no medibles** antes del 3 de septiembre | Requieren tráfico real y A/B | Se **instrumentan**, no se prometen números |

### 2.3. Veredicto

> **Adoptar la v2 como especificación funcional de referencia**, con la frontera arquitectónica de §6, la capa de evaluación de §11 y los agentes de §9 como adiciones exigidas por el Proyecto Final. El alcance entregable es Fase 1 completa + Fase 3 parcial.

---

## 3. Respuesta punto por punto a la revisión de la PR

| # | Decisión pedida | Postura | Justificación | Coste |
|---|---|---|---|---|
| 1 | Alcance de la entrega | **Fase 1 + Fase 3 parcial**, declarado explícitamente | Con 2 personas y 4,4 semanas, comprometer las 5 fases sería mentir | — |
| 2 | Modelo de variantes | **`ProductFamily` + `ProductFamilyMember`**. Acepto | Tiene razón: una clave textual generada por IA se rompe ("anillo-erizo-mar" vs "anillo-erizo-de-mar"), no la puede corregir un admin y falla justo en el caso que queremos evitar. Además la entidad hace implementable la alerta de "productos parecidos sin familia" | +2 changes |
| 3 | `materials[]` | Acepto. `text[]` en el índice, `MaterialsJson` en .NET, **vocabulario cerrado**, filtro por solape (`&&`) con índice GIN | Un producto es "plata con baño de oro". Con un solo valor, el filtro por material da falsos negativos | +0 (dentro del enriquecimiento) |
| 4 | Campos reaparecidos | Acepto eliminar los cuatro del perfil. **⏳ Contrapropuesta pendiente de acuerdo para los alias** (§7.4) y una precisión sobre cuidados (§7.7) | Persistir texto IA por producto genera deriva y datos no revisables. Pero el problema que resolvían los alias sigue existiendo | +1 change |
| 5 | Revisión humana | **Híbrido, como propone**: `piece_type`, `materials`, `stone_type`, `size_label` y familia siempre revisados **si son inferidos**; tags comerciales auto-aprobados con confianza alta | Es su propuesta y es mejor que la mía. Ver §7.8 para cómo se demuestra sin dejar el corpus vacío | +0 |
| 6 | Alcance mínimo de inventario | **Reposición + sustitutos + traslados + stock parado/rotación + aprobación manual. ⏳ Packing list fuera, pendiente de acuerdo** | Todo lo que acepto tiene contenido de IA o HITL demostrable. La packing list es CRUD con máquina de 6 estados y auditoría, cero IA, y está aguas abajo: aplazarla no bloquea nada. En su lugar, vista imprimible de recomendaciones aprobadas por POS. Si entra, sale complementarios y rotación | +6 changes (+2 si entra packing list) |
| 7 | Argumentario por hotel | **Perfil periódico calculado y almacenado estructurado**, como propone | Es la opción correcta: barata, verificable contra métricas y reutilizable por ranking, sustitutos y reposición | +1,5 changes |
| 8 | Complementarios | **Reglas + co-ocurrencia de ventas + tabla de curación manual.** Upsell/downsell fuera | Complementario ≠ similar: distinto `piece_type`, colores y estilos compatibles, banda de precio, y co-venta histórica. El margen existe pero validar upselling requiere datos de negocio que no tendremos | +1 change |
| 9 | Python vs .NET | **Permanente, con frontera estrecha**: Python solo embeddings, índice vectorial, recuperación, generación y bucle agéntico. **Toda regla de negocio, cálculo y persistencia de negocio en .NET** | Reduce a la mitad los riesgos que señala (duplicación, sincronización, migraciones). Si algún día se consolida en .NET, solo se mueve la capa de recuperación | — |
| 10 | Propiedad y sincronización | Contrato explícito en §6.3: propietario por dato, quién inicia, altas/bajas/desactivaciones con **tombstones**, detección de divergencia, reintentos, versionado | Faltaba en mi versión anterior. Tiene razón | +0 (va en los feeds) |
| 11 | Frescura del inventario | **Acepto, y es su mejor aportación técnica.** La proyección pasa a ser prior de ranking; se sobre-recupera y **.NET decide** | Mi versión podía descartar un producto válido antes de que .NET lo viera, sin posibilidad de recuperarlo. Ver §7.6 | +0 |
| 12 | Datos de evaluación | **Aceptado y resuelto: corpus híbrido.** Habrá export real, de tamaño probablemente insuficiente, ampliado con sintético. Cada documento lleva `data_origin: real \| synthetic` y **toda métrica se reporta desglosada** | Es la respuesta correcta a su objeción: el golden set se ancla en lo real, lo sintético solo aporta volumen y estrés. Sin el desglose, los productos sintéticos —más limpios— inflarían los números. Medir errores de selección reales exige usuarios: fuera de plazo | +0,5 change |

---

## 4. Alcance acordado

| # | Capacidad | Estado | Justificación |
|---|---|---|---|
| 1 | Enriquecimiento de catálogo (`materials[]`, vocabulario cerrado, confianza por campo, revisión híbrida) | **Núcleo** | Es la construcción del corpus |
| 2 | `ProductFamily` + `ProductFamilyMember`, con propuesta asistida y aprobación humana | **Núcleo** | Desambiguación de variantes: el caso de negocio crítico |
| 3 | Búsqueda semántica híbrida por POS (dos índices, sinónimos, prefiltro blando, abstención) | **Núcleo** | Corazón del PF |
| 4 | Venta asistida (agrupación por familia, avisos por reglas, citas) | **Núcleo** | Capa de generación con atribución verificable |
| 5 | Agente asistente de venta (tools de solo lectura, guardrails, HITL) | **Núcleo** | Requisito del PF |
| 6 | Sustitutos por falta de stock | **Núcleo** | Reutiliza el retriever |
| 7 | Complementarios por reglas + co-ocurrencia | **Acordado (con corte pre-autorizado)** | Decisión 8 de la revisión. Es el corte nº 1 del §13.4 |
| 8 | Perfil comercial por POS, calculado periódicamente | **Fuera — fase posterior** *(31 ago)* | Decisión 7. Cae con la rama del agente de inventario, aunque **no dependía de ella**: es el único de los cinco rescatable por separado, y el §13.4 explica cómo |
| 9 | Agente de inventario: reposición, traslados, rotación/stock parado, con aprobación | **Fuera — fase posterior** *(31 ago)* | Decisión 6. **Anulado:** cero aporte al sistema RAG a cambio de cinco changes, tres de ellos sin LLM. Diseño íntegro conservado en el §10 |
| 10 | Evaluación (golden set, ablations, validador anti-alucinación, escenarios de agente) | **Núcleo** | Requisito del PF. Sin los 8-10 escenarios de inventario ni el test de fidelidad del perfil por POS |
| 11 | Vista imprimible de recomendaciones aprobadas por POS | **Fuera — fase posterior** *(31 ago)* | Sin recomendaciones que aprobar, no hay nada que imprimir |
| 12 | Packing list con máquina de 6 estados y auditoría | **Fuera — fase posterior** | Cero IA, aguas abajo, no bloquea nada |
| 13 | Liquidación con descuentos, `InventoryPolicy` configurable | **Fuera** | Toca precios; requiere decisión de negocio y auditoría propia |
| 14 | Upsell / downsell / prioridad comercial por margen | **Fuera** | Viable (el margen existe) pero sin datos para validarlo antes del 3/9 |
| 15 | Reranking cross-encoder | **No implementado, protocolizado** | Con ~1.500 vectores la hipótesis es que no compensa. Se documenta cómo se mediría |
| 16 | Reconocimiento visual, try-on, fine-tuning | **Fuera** | Ya existe (visual) o no aporta |

---

## 5. El problema de recuperación, bien planteado

- **No hay documentos largos que trocear.** Un producto es una entidad con ~15 atributos y 40-120 palabras. **Chunking = ninguno** en el índice de catálogo.
- **La consulta es corta, coloquial y de jerga mixta**, y mezcla intención semántica, restricciones duras (precio, talla, materiales, POS) y términos literales (SKU). **Búsqueda híbrida obligatoria**: lo semántico diluiría "ERIZO-M".
- **Con `SearchAliases` fuera, la rama léxica necesita ayuda externa**: un diccionario de sinónimos del dominio en expansión de consulta (§7.4).
- **El resultado no es prosa: es un conjunto ordenado de entidades** agrupadas por familia, más una explicación. La generación es la capa fina.
- **Sí hay un segundo corpus con forma de documento**: conocimiento comercial general (materiales y alergias, equivalencias de talla, guiones de venta, política de devoluciones) — **general, no por producto**, que es exactamente lo que la revisión pide evitar. Ese sí se trocea y es lo que permite citas verificables.

---

## 6. Arquitectura y frontera de responsabilidad

### 6.1. Vista general

```mermaid
flowchart TB
    subgraph cliente["Cliente"]
        SPA["React SPA · Buscar con ayuda · Card de venta asistida · Revisión de perfiles"]
    end

    subgraph ec2["EC2 · nginx TLS"]
        subgraph net["Backend .NET 10 — toda la regla de negocio"]
            API["ASP.NET Core API"]
            BIZ["Familias · Perfiles IA · Agregados de venta del feed"]
            HYD["Hidratador: stock, precio, permisos POS — AUTORIDAD FINAL"]
            CB["Circuit breaker + fallback léxico"]
        end
        subgraph py["jbg-ai (Python · FastAPI) — solo vectorial y LLM"]
            R1["/v1/retrieval · híbrido, sinónimos, sustitutos, complementarios"]
            R2["/v1/assist · generación con citas + agente de venta"]
            R4["/v1/index · /v1/enrich"]
            EV["Harness de evals (offline)"]
        end
    end

    DB[("RDS PostgreSQL · public (negocio, fuente de verdad) + ai (vectores)")]
    LLM["Proveedor LLM + embeddings"]

    SPA -->|JWT usuario| API
    API --> CB
    CB -->|JWT interno| R1
    CB -->|JWT interno| R2
    R4 -->|feed paginado since-cursor| API
    R2 -.->|tool: consultar_disponibilidad<br/>NO HECHA — C32a lee ai.pos_projection| API
    API --> BIZ
    BIZ --> DB
    API --> HYD
    HYD --> DB
    R1 --> DB
    R2 --> R1
    R2 --> LLM
    R4 --> LLM
```

> **Corregido el 2026-08-31.** El diagrama de la v3 dibujaba un tercer servicio Python, `/v1/inventory/propose`, y una arista de vuelta `Python → .NET` etiquetada *«tools: señales de demanda»*. Ambos desaparecen con la anulación del agente de inventario.
>
> La llamada de vuelta **no desaparece**: `consultar_disponibilidad` es tool del agente de venta y también va de Python a .NET. Lo que cambia es su superficie, y para bien. **El §6.4 solo especifica el sentido .NET → Python** (JWT interno de servicio HS256 con `pos_id` y `trace_id`); el de vuelta seguía sin esquema definido, y ahora tiene que resolverse **una sola vez, para un dato que el hidratador ya es autoridad de expresar**, en lugar de dos veces y transportando además cifras de demanda por producto. Queda como decisión abierta del change del agente de venta.
>
> **Cerrada el 2026-09-20 por C32a, y cerrada difiriéndola con motivo.** C32a es ese change, y su decisión D-1 es que `consultar_disponibilidad` **no llama a .NET**: se sirve desde `ai.pos_projection`, que es un dato que Python ya tiene proyectado. La arista de vuelta del diagrama de arriba, por tanto, **no existe todavía**. El motivo no es de plazo: la única arista Python → .NET que hay hoy es `AiIndexFeedController`, autenticada con `X-Index-Feed-Key`, **sin `[Authorize]` a propósito** y **sin transportar `pos_id`**, y su ruta `pos-availability` es un feed paginado de 200 filas con keyset, pensado para un drenaje batch y no para preguntar por una pieza. Construirlo habría significado ruta .NET nueva, filtro de autenticación con ámbito de punto de venta y tests de integración: zona .NET dentro de un change de zona Python. **El endpoint queda identificado, acotado y no hecho**, con su ficha y lo que hará falta en [`openspec/DEFERRED_TASKS.md`](../../openspec/DEFERRED_TASKS.md) — incluida la advertencia de que un cliente HTTP de propósito general **no pasará** el invariante de solo-lectura del registro, porque expone `post`, `put`, `patch` y `delete`, y habrá que envolverlo en una superficie que exponga sólo la lectura. Lo que C32a sí fija de forma definitiva, venga el dato de donde venga, es que **al modelo no le llega un número**: la observación es una etiqueta cualitativa sin dígitos.

### 6.2. Qué vive dónde (respuesta a la decisión 9)

| Responsabilidad | Servicio | Motivo |
|---|---|---|
| Catálogo, precios, POS, permisos, inventario, ventas | **.NET** | Fuente de verdad transaccional |
| `ProductAiProfile`, `ProductFamily`, `ProductFamilyMember`, `ProductRecommendation` (curación manual) | **.NET** | Datos de negocio revisables por humanos |
| **Agregados de venta por (producto, POS)** — `sales30d`, `sales90d`, `lastSaleAt`, `qtyBucket` | **.NET, en SQL** | Cálculos deterministas sobre datos transaccionales. Un LLM aquí solo introduce error. **Ya implementados** en el feed de indexación; son la señal de negocio que pondera el ranking |
| ~~Señales de demanda de inventario~~ (`sales_7/60d`, días a rotura, stock en otros POS) | — | **Fuera desde el 31 ago.** Nunca alimentaron el ranking: eso lo hace la fila de arriba. Diseño en el §10.1 |
| ~~Motor de recomendaciones · `InventoryRecommendation` · perfil por POS~~ | — | **Fuera desde el 31 ago.** Diseño en §10.2, §10.3 y §10.4 |
| Embeddings, índice vectorial, recuperación híbrida, sustitutos, complementarios | **Python** | Es el espacio vectorial |
| Generación con citas, guardrails, bucles agénticos | **Python** | Es la capa LLM |
| Evaluación offline | **Python** | Instrumental del máster (RAGAS, harness) |

**Regla de una frase:** *Python calcula parecidos y redacta; .NET calcula números y decide.*

### 6.3. Contrato de sincronización (respuesta a la decisión 10)

| Aspecto | Regla |
|---|---|
| **Propiedad** | `public.*` y las tablas IA de negocio son de .NET. `ai.*` es de Python. Python **nunca** escribe en `public` ni lo lee por SQL |
| **Quién inicia** | Python **tira** (`pull`) de feeds HTTP paginados con cursor `since`. .NET **empuja** una invalidación cuando se aprueba un perfil o cambia una familia |
| **Altas y cambios** | Upsert idempotente por `product_id`, guiado por `source_hash`. Sin cambio de hash no se recalcula embedding |
| **Bajas y desactivaciones** | El feed emite **tombstones** (`{product_id, deleted_at \| deactivated_at}`). Un producto desactivado sale del índice en la siguiente sincronización, y además el hidratador lo descarta al instante |
| **Detección de divergencia** | `GET /v1/index/status` compara conteo y hash agregado del índice contra el del feed; expone `drift_count` y `last_full_sync_at`. Sincronización completa nocturna que reconcilia |
| **Reintentos** | Backoff exponencial con tope; un lote fallido no bloquea el resto; los fallos quedan en `ai.sync_failure` para reintento manual |
| **Versionado** | `embedding_model` + `embedding_version` por fila. Cambiar de modelo se hace en **columna nueva**, nunca sobrescribiendo |
| **Frescura de inventario** | La proyección se refresca cada 5-10 min y **nunca excluye** (§7.6) *(cumplido el 2026-09-26 con **C41**, y con dos precisiones que el diseño no tenía. La horquilla pasa a ser **600 s**, **derivados** de `techo / intervalo ≥ 4` sobre el techo de 3.600 s: lo que importa no es la cadencia sino cuántos drenajes fallidos seguidos caben antes de que el guard degrade el ámbito. Y el drenaje corre **también al arrancar el proceso** —completo si no hay checkpoint—, porque los tres incidentes registrados se encontraron **levantando un entorno para probarlo**, no en régimen permanente: un intervalo deja una ventana abierta justo en el momento en que se mide. Entre C22 y C41 esta fila describió una intención: el planificador existía sólo como receta de cron en un README, y apuntaba a una ruta de host contra un servicio que se despliega en contenedor.)* |

### 6.4. Seguridad y degradación

- El frontend nunca habla con Python. .NET → Python con **JWT interno de servicio** (HS256, TTL corto, secreto en SSM) que transporta `user_id`, `role`, `pos_id`, `trace_id`. Python valida y aplica ese scope; no confía en el body. Red interna Docker, puerto no publicado en nginx.
- Timeouts (0,8 s retrieval / 5 s assist; **15 s el agente de venta, en ruta propia —`POST /v1/assist/agent`—** *(añadido el 2026-09-21: su peor caso no cabía en los 5 s, así que C32b le dio ruta aparte y `/v1/assist/sale` conserva los suyos. Los 15 s son el* deadline *del lado Python, que acota la petición entera; la política de* timeout *y circuito de .NET para esa ruta está identificada y no hecha, en `openspec/DEFERRED_TASKS.md`)*), reintento único, circuit breaker con Polly. Si el circuito abre, .NET responde con el **buscador léxico existente** y `ai_available: false`. **El sistema nunca se cae por culpa de la IA.** Feature flag por POS.

---

## 7. Diseño del sistema RAG

### 7.1. Pipeline de enriquecimiento

```text
Producto (SKU, nombre, descripción, precio, colección)
  → normalización determinista (limpieza, unidades, tallas por regex)
  → extracción estructurada con LLM (JSON schema estricto, temperatura 0)
  → validación: esquema + vocabularios cerrados + coherencia
  → confianza POR CAMPO → enrutado híbrido de revisión (§7.8)
  → ProductAiProfile (.NET) + SourceText canónico + SourceHash
  → embedding solo si cambia SourceHash → ai.product_document
```

`materials` se extrae como **lista** contra vocabulario cerrado (plata, acero, baño de oro, oro, latón, resina, cuero, perla cultivada…). El extractor devuelve `[]` si no hay evidencia, nunca inventa un material por defecto — y `[]` con confianza baja enruta a revisión.

### 7.2. Esquema del índice (`ai`, pgvector)

```text
ai.product_document              -- 1 fila por producto, sin chunking
  product_id (uuid, PK)
  sku, name, collection_name, price, price_band
  piece_type, materials text[], stone_type, size_label
  family_id uuid nullable, family_name, variant_label
  color_tags[], style_tags[], occasion_tags[]
  doc_text text                  -- SourceText canónico
  source_hash char(64)
  embedding vector(1536)
  tsv tsvector                   -- to_tsvector('spanish', ...)
  is_active bool
  embedding_model, embedding_version, indexed_at

ai.knowledge_document / ai.knowledge_chunk   -- conocimiento GENERAL, no por producto
  doc_type: material | talla | guion_venta | politica | faq
  content, chunk_index, metadata jsonb, embedding vector(1536), tsv

ai.pos_projection                -- prior de ranking, NUNCA filtro excluyente
  pos_id, product_id, is_assigned_hint, qty_bucket (0 | 1-2 | 3+)
  sales_30d, sales_90d, last_sale_at, refreshed_at

ai.co_occurrence                 -- señal de complementarios
  product_a, product_b, co_sales_count, last_seen_at

ai.sync_failure, ai.query_log, ai.eval_run, ai.eval_case, ai.eval_result
```

Índices: **HNSW `vector_cosine_ops`** sobre ambos `embedding` (alineado con el operador `<=>`; desalinearlo desactiva el índice en silencio), **GIN** sobre `tsv`, sobre `metadata` y **sobre `materials`** (filtro por solape), B-tree sobre `family_id`, `piece_type`, `price_band`.

**`qty_bucket`, no cantidad exacta.** La proyección puede estar desfasada; guardar el número exacto invitaría a mostrarlo. Con un *bucket* solo puede usarse como señal de ranking. La cantidad real la pone .NET.

### 7.3. Filtro por materiales

Con `materials[]`, el filtro deja de ser igualdad y pasa a ser **solape**: "algo de plata" recupera productos cuyo array contiene `plata`, aunque también tengan `baño de oro`. Dos semánticas, elegidas por consulta:

- **Contiene alguno** (`materials && ARRAY['plata']`) — comportamiento por defecto, el que espera un operador.
- **Contiene todos** (`materials @> ARRAY['plata','baño de oro']`) — cuando la consulta nombra varios.

La normalización de sinónimos de material ("plata de ley", "925", "sterling" → `plata`) se hace en el **vocabulario cerrado** durante la extracción, no en consulta.

### 7.4. Diccionario de sinónimos (sustituto de `SearchAliases`)

**Problema:** sin alias por producto, la rama léxica no encuentra "sortija" para un producto llamado "anillo", ni "gargantilla" para "collar".

**Propuesta:** un fichero **único y curado a mano** en el repositorio, ~40-60 entradas, versionado y revisable:

```yaml
anillo:    [sortija, aro de dedo, alianza]
pendiente: [aro, arete, pendientes, criolla]
collar:    [gargantilla, cadena, colgante]
pulsera:   [brazalete, esclava]
dorado:    [oro, color oro, baño de oro, gold]
```

Se aplica en **expansión de consulta** ("sortija plata" busca también "anillo plata"), nunca en indexación, para no contaminar los documentos. Ventajas frente a alias por producto: una sola lista, cero generación por IA, cero deriva, corregible en un commit y aplicable a productos futuros sin reindexar. **Su efecto se mide**: el golden set tiene una categoría de consultas con sinónimos y se compara con y sin diccionario.

### 7.5. Familias: flujo mixto (respuesta a la decisión abierta 4 de la v2)

Crear ~350 familias a mano es inviable, y dejarlas a la IA es lo que la revisión rechaza con razón. El flujo acordado *(C06b, 2026-08-22, no adelanta este trabajo: el catálogo híbrido nace sin filas de miembro)*:

1. **La IA propone**: agrupa candidatos por similitud de embedding (umbral alto) + mismo `piece_type` + raíz común de nombre, y genera propuestas con miembros y etiquetas de variante detectadas.
2. **El admin aprueba, edita o rechaza** en una pantalla de revisión por lotes. Al aprobar se crean `ProductFamily` y `ProductFamilyMember` reales, en .NET.
3. **La familia es editable después** sin tocar nada de IA: es una entidad de negocio.
4. **Alerta de huérfanos**: productos con similitud alta a una familia existente pero sin pertenecer a ella se listan como incidencia de calidad.

Esto convierte la exigencia del compañero en un uso legítimo del índice que ya construimos, y es un segundo caso de HITL demostrable para el PF.

### 7.6. Recuperación: prefiltro blando y sobre-recuperación (respuesta a la decisión 11)

El orden importa, y cambia respecto a la versión anterior:

1. **Filtros duros — solo los que no pueden estar obsoletos.** El `pos_id` del solicitante viene del token, no de la proyección: eso sí es duro. Nada más se excluye en Python.
2. **Filtros estructurales de la consulta**: banda de precio, tipo de pieza, talla, materiales (solape). Extraídos **por reglas** (`menos de 80`, `talla M`, nombres del vocabulario de materiales) con *fallback* a consulta cruda.
3. **Búsqueda híbrida**: vectorial (`<=>` sobre HNSW) + léxica (`ts_rank` español + expansión de sinónimos + *boost* de SKU/nombre exacto), fusionadas con **RRF**.
4. **Prior de disponibilidad, no filtro**: `qty_bucket = 0` o `is_assigned_hint = false` **penalizan** el score; nunca eliminan al candidato.
5. **Sobre-recuperación**: Python devuelve `top_k × 3` candidatos (tope 60) para que .NET tenga margen tras descartar.
6. **.NET decide**: el hidratador aplica la verdad — producto activo, `Inventory.IsActive` real, stock, precio, permisos — descarta lo inválido y **trunca a `top_k`**. Si tras hidratar quedan menos de los pedidos, .NET puede repedir con `top_k` mayor.
7. **Threshold y abstención**: por debajo del umbral no se devuelve nada y se marca `low_confidence: true`. Devolver cero es información válida.
8. **Reranking cross-encoder**: no se implementa; se documenta la hipótesis y el protocolo (§11.2).

Con esto, un producto válido **no puede** desaparecer por una proyección desfasada: como mucho baja de posición, y .NET siempre lo ve.

### 7.7. Generación, avisos y citas

La respuesta es **estructurada**, no prosa libre:

- `groups[]`: candidatos agrupados por **`family_id`**, con `variant_label` destacado.
- `reason` por candidato: qué señales coincidieron, construido desde datos (tipo, materiales, color, disponibilidad), no inventado.
- `warnings[]`: **calculados por reglas**, no persistidos ni generados libremente — existen variantes en la familia, falta `size_label`, stock crítico, familia con miembros sin stock.
- `pitch`: argumentario **generado en tiempo de consulta** desde metadatos aprobados y, si aplica, chunks del corpus de conocimiento con `citations[]`. **No se persiste.**
- `clarification_question` si la consulta es ambigua.

**Sobre los cuidados**: se elimina `CareInstructions` como atributo del producto, de acuerdo. Pero el conocimiento sobre cuidados **sí existe** en el corpus general (`doc_type: material`), donde es una ficha por material y no por producto — cumple el principio de la revisión y permite responder "¿este anillo se puede mojar?" con cita verificable.

**Toda cifra de precio o stock se emite como placeholder** (`{{price}}`, `{{stock}}`) que el modelo no puede rellenar; .NET los sustituye al hidratar y **rechaza la respuesta** si alguno queda sin resolver.

**Los avisos viajan como códigos y el castellano lo escribe la capa de presentación** *(precisado el 2026-09-22, al implementar C36)*. `warnings[]` no contiene nunca una frase: contiene valores de un vocabulario **cerrado pero versionado**, y su traducción vive en `frontend/src/lib/assist-copy.ts`, exportada y probada directamente. Es la misma regla que la spec viva del panel de búsqueda impone para las razones de coincidencia del recuperador, incluida su cláusula de tolerancia: **un código que la pantalla no conoce se pinta con una etiqueta neutra y nunca en bruto**, porque eso es lo único que impide que una versión nueva del servicio rompa una fila.

**Y dos de los siete códigos del vocabulario no tienen consumidor.** `query_out_of_domain` y `query_not_in_catalogue` los emite sólo `classify_query`, que corre únicamente en el modo de consulta libre; las dos rutas que la ficha consume son siempre ancladas, así que **no pueden llegar a ninguna pantalla**. No se les escribe castellano —sería copia muerta— y caen en la etiqueta neutra, con un test que lo comprueba. Por lo mismo, `clarification_question` es **constante `null`** en esas dos rutas: se lee del contrato y se pintaría si llegara, pero no tiene bloque ni copia propios, porque es un campo del objeto de transferencia y no una funcionalidad.

**El séptimo, `size_label_missing`, se pinta pero no como aviso.** Salta en el **58,3 %** de las fichas y está anticorrelacionado con pertenecer a una familia —4,0 % con ella contra 92,5 % sin ella—, de modo que informa del estado del enriquecimiento del catálogo y no de la pieza que el cliente tiene delante. La ficha lo muestra como **atributo junto al SKU**, nunca entre las alertas, y **nunca lo suprime**: el frontend no retira un código que el backend emitió. Como alerta canibalizaría a `stock_critical`, que salta en el 3,9 % y sí puede costar una venta.

> **Revisado el 2026-09-13, al explorar C30 y partirlo en C30a y C30b.** Lo de arriba se conserva
> porque sigue siendo la forma de la respuesta; lo que cambia es **quién calcula cada cosa y en qué
> orden se entrega**. Cinco correcciones, todas comprobadas contra el árbol; las once decisiones
> con sus alternativas están en
> [`informes/c30-exploration-decisions.md`](informes/c30-exploration-decisions.md).
>
> **1 · La respuesta tiene tres modos, no uno.** El `groups[]` de arriba describe el modo anclado a
> una consulta, pero el flujo por consulta **ya lo sirve** `POST /api/ai/search` (C15) con su panel
> (C16), y el único consumidor previsto de `/v1/assist/sale` —C34— expone rutas **por pieza**. Así
> que el contrato acepta `product_id` y `query` con validación de «al menos uno»: **M1** pregunta
> libre, **M2** argumentario de la pieza elegida, **M3** pregunta sobre la pieza elegida. M3 es el
> que hace realizable el *«¿este anillo se puede mojar?»* de esta misma sección, y hasta ahora no
> tenía ruta: se abre con `?question=` en `/sales-assist` y una caja en el card.
>
> **2 · `family_id` puede ser nulo, y el agrupado tiene que admitirlo.** **~58 % del catálogo no
> pertenece a ninguna familia** (C18b: 156 familias y 486 miembros sobre ~1.168 filas indexadas),
> mientras el esquema congelado exigía `family_id` obligatorio y no nulable. Pasa a nulable con el
> invariante *sin familia ⇒ exactamente un miembro*. Y el `reason` por candidato de arriba **no
> tenía campo**: se sirve reusando `match_reasons`, que desde C21 ya lleva procedencia real.
>
> **3 · Dos de los cuatro avisos son de .NET.** «Stock crítico» y «familia con miembros sin stock»
> necesitan el stock **real**, y en Python sólo existe `qty_bucket`, que el §6.2 mantiene fuera del
> cable y el §15.10 permite desfasado. Los calcula **C34 tras hidratar** y los apila sobre los dos
> estructurales, que sí son del índice. Los `warnings[]` viajan como **códigos de vocabulario
> cerrado** y el castellano lo escribe el frontend — lo que además hace del *«nunca generados
> libremente»* de arriba algo verificable, porque el modelo no ve el vocabulario.
>
> **4 · La citación tiene que llevar `claim_scope`, o el mecanismo del §7.8 se muere en la
> frontera.** El `Citation` congelado llevaba tres campos y `KnowledgeCitation` tiene diez: se
> perdían el `citation_id` —el que resuelve, **localiza** y abre el fichero y el encabezado en
> git— y la marca de alcance, que son **25 de los 161** fragmentos. Se reforma. Y `citations[]`
> pasa a ser **lo que el pitch usó**, no lo que el retriever devolvió, con la integridad
> referencial comprobada **en código después de generar**: citar todo lo recuperado no es
> atribuir, es decorar.
>
> **5 · El placeholder protege un flanco y deja el otro abierto.** .NET rechaza un placeholder sin
> resolver, pero un pitch que escriba «39,90 €» **literal** no deja placeholder alguno y pasa. El
> validador determinista del §11.3 lo caza en evaluación, no en ejecución. Así que C30b añade una
> puerta **en ejecución**: el pitch sólo puede contener cifras **presentes en el payload que se le
> entregó** —tallas, mm, `925`, dígitos de SKU— más los dos tokens. Lista blanca y no lista negra,
> porque este dominio está lleno de números legítimos.
>
> **Y una precisión sobre el «no se persiste» de arriba: incluye no loguearlo.** Una línea de log
> es almacenamiento durable fuera de la base y **sin el `effective_pos_id` que la respuesta sí
> lleva**, así que el texto no se escribe en ningún log — sólo su longitud, su hash y los
> `citation_id` usados. Es viable porque a temperatura 0 y con prompt versionado el texto es
> re-derivable. La **excepción declarada** es el arnés del §11.3–11.4, que sí guarda las
> generaciones atadas a `run_id`, `git_sha` y `prompt_version`, fuera del camino de servicio.

### 7.8. Revisión humana híbrida (respuesta a la decisión 5)

| Campo | Política |
|---|---|
| `piece_type`, `materials`, `stone_type`, `size_label`, pertenencia a familia | **Revisión obligatoria si el valor es inferido.** Si viene de un dato estructurado existente o de una regla determinista (regex de talla), se marca `source: rule` y no requiere revisión |
| `color_tags`, `style_tags`, `occasion_tags` | **Auto-aprobación** si la confianza supera el umbral; a revisión si no |
| Cualquier campo con confianza bajo umbral | Revisión |

**El problema operativo, dicho abiertamente:** con ~1.000 productos, "revisar todos los campos sensibles inferidos" son horas de trabajo humano que no hay, y si solo se indexan perfiles aprobados el corpus queda vacío y no hay demo.

> **Matiz del 2026-08-31.** La restricción original era de calendario —*«que no tenemos antes del 3 de septiembre»*— y con **prórroga abierta** ya no lo es. Sigue siendo real, pero por otra razón: es **una sola persona** revisando, y el cuello de botella es de atención, no de fecha. La consecuencia práctica sí cambia y conviene aprovecharla: el lote revisado **puede crecer por encima de los 120-150** sin romper nada, y hacerlo mejora directamente los dos números que el checklist del §16 exige —tasa de corrección por campo y tiempo medio de revisión—, que son mejores cuanto mayor es la muestra. El porcentaje revisado que acabe declarando la limitación 2 del §15 se fija con lo que se revise de verdad, no con este párrafo.

**Cómo se resuelve sin hacer trampa:** dos vías declaradas y distinguibles en los datos.

- **Vía revisada**: un lote de 120-150 productos pasa por la pantalla de revisión de verdad, cronometrado. De ahí sale un dato que va al README: **tiempo medio de revisión por producto y tasa de corrección real del extractor**. Es la evidencia de que el mecanismo funciona y de cuánto cuesta.
- **Vía masiva**: el resto se marca `review_state = auto_bulk`, se indexa y se distingue en toda métrica. El README dice explícitamente qué porcentaje del corpus está revisado por humanos.

Ningún número de evaluación mezcla ambas vías sin decirlo.

---

## 8. Datos

### 8.1. Datos reales y su dependencia

| Fuente | Disponibilidad | Uso |
|---|---|---|
| Modelo de datos y semántica de negocio | **Real y verificado** | Define esquemas, filtros, permisos, reglas |
| **Catálogo real e histórico de ventas 2026 anonimizado** | **Recibido el 2026-08-17: 436 productos, 28 colecciones** | Núcleo del corpus y **ancla del golden set**. Se amplía con sintético hasta alcanzar volumen. **El tamaño resultó suficiente y la calidad textual no**: 38,5 caracteres de media entre nombre y descripción, 51 productos sin descripción. Ver §8.1.1 |
| Textos comerciales de la joyería (materiales, garantía, tallas) | A pedir al negocio | Semilla del corpus de conocimiento |
| Fotos de producto | **No llegaron: 0 fotos y 0 embeddings visuales en el sistema** | No se usan (el índice visual ya existe y es otro problema). **Consecuencia añadida el 2026-08-17:** la asistencia de redacción de C06a simula un reconocimiento multimodal que no existe, así que no puede verificar piedras ni acabados — solo expandir lo que ya consta y acotar por banda de precio lo que no. Declarado en §15 |

### 8.1.1. Corpus híbrido: cómo se combinan real y sintético

El export real llegó el 2026-08-17 con 436 productos: cubre la mitad del volumen objetivo y hay que ampliarlo. La combinación no es "mezclar y olvidar": tiene tres reglas que protegen la validez de la evaluación.

1. **Todo documento lleva dos ejes de procedencia**, tanto en `ai.product_document` como en el golden set. Son columnas, no comentarios:
   - **`data_origin: real | synthetic`** — ¿el producto existe? SKU, precio y colección de un producto `real` son reales, y .NET sigue siendo su autoridad.
   - **`text_provenance: merchant | ai_assisted | synthetic`** — ¿de dónde sale su texto?

   *Revisado el 2026-08-17.* Originalmente había un solo eje. El export real llegó con 38,5 caracteres de texto por producto y hubo que asistir su redacción; al hacerlo se vio que la columna respondía a **dos preguntas independientes** y se rompía. Un producto real puede tener texto del comerciante o texto asistido sin dejar de ser real.
2. **El generador sintético no clona el estilo del real por accidente, y ya no «calibra» lo que el problema necesita declarado.** Del corpus C06a se toman los SKUs y los nombres de colección **a no reutilizar**. No se heredan distribución de precios, convenciones de SKU ni tamaño medio de familia: con 354 grupos internos ya en el real, copiar esa media (~1,23) evaporaría el caso de variantes, y copiar precios (mediana 72 €, cola a 4.175 €) ancla un LLM que debe razonar pieza a pieza.

   **Excepción, añadida el 2026-08-17: la longitud de descripción no se calibra, se declara.** Heredarla del real daría 100 % de descripciones pobres y no el ~30 % de §8.4, así que las dos reglas se contradecían en cuanto el export resultó ser este. El reparto de calidad —~70 % rico, ~20 % escueto, ~10 % sin descripción— se fija explícitamente. En C06a el sorteo es por familia de variantes *interna* (no serializada). En C06b no hay `ProductFamily`: si se declara el mismo reparto, el agrupamiento interno por stem de nombre (tallas en el copy) no se escribe en .NET.

   *Revisado el 2026-08-22, al diseñar C06b.* D1 lo genera un **LLM vía CLI** en `jbg_ai.data` (nombres, descripciones, precios razonados, colecciones nuevas). El código reserva SKUs, sella procedencia y valida tope de 1000 caracteres. No hay ruta HTTP. Las colecciones sintéticas son **altas nuevas** (brief de vitrina de hotel, aeropuerto/turista o tienda clásica), no un campo de canal en `Product`. El ~35 % multi-material vive en la **prosa** para que C09 lo extraiga; el JSONL no lleva `materials[]`.

   *Revisado el 2026-08-22, al generar el JSONL v3.* El 70/20/10 **sigue declarándose** (no se hereda la pobreza textual del export). Dentro de cada bucket, la longitud del copy **sí** se aproxima a las medias del JSONL real enriquecido (`rich` ~289 / `sparse` ~115 / `original` ~14). El recorte es por frases enteras; ~20 % de los `short` quedan vacíos.
3. **Toda métrica se reporta desglosada por los dos ejes, y también global.** Es la regla que evita el autoengaño. Los productos sintéticos son más limpios y regulares; si el Recall@5 global sale bien pero el de la porción real sale mal, el sistema no sirve y hay que verlo.

   **El número que va al README como resultado principal es el de `data_origin: real`, declarando junto a él qué `text_provenance` lo compone.** Mientras esa porción llevaba texto del comerciante, era además el grupo de control honesto del experimento. Desde que su texto está asistido ya no lo es, y el README debe decirlo: la afirmación del proyecto es «funciona sobre un catálogo **realista**», no «sobre un catálogo real». Las métricas de enriquecimiento (§11.5) no se ven afectadas —miden al extractor, no a la verdad del dato—; las de recuperación sí dejan de hablar del negocio tal cual es.

Y una regla sobre el golden set: **se etiqueta primero sobre productos reales** y solo se completa con sintéticos si no hay material suficiente para cubrir las 9 categorías. Si el export trae, por ejemplo, 200 productos, esos 200 sostienen la mayor parte de las 60-70 consultas.

**Postura:** el sistema funciona con cualquiera de los dos extremos; el diseño no depende del tamaño del export, solo la fuerza de la evidencia.

### 8.2. Estrategia: mundo determinista, texto con IA

- **LLM → lo textual y semántico**: nombres, descripciones, **catálogo sintético D1 (C06b, CLI en `jbg_ai.data`, no un endpoint)**, corpus de conocimiento, consultas de operador.
- **Código determinista con semilla → lo numérico y relacional**: reserva de SKU y validación del corpus; red de POS, propensión producto×POS, simulación de ventas (Poisson con estacionalidad y perfil por hotel), inventario, movimientos, co-ocurrencia (**C10, mismo paquete, también CLI** — ni la API .NET ni FastAPI).

El histórico así generado es **coherente por construcción** con catálogo y stock, que es lo que necesitan rotación, sustitutos, complementarios, perfil por POS y reposición.

### 8.3. Datasets

| # | Dataset | Volumen | Novedades v3 | Alimenta |
|---|---|---|---|---|
| D0 | **Catálogo real anonimizado** | **436** (recibido) | **Ancla del corpus y del golden set**. C06a: `data_origin: real`, texto `ai_assisted`/`merchant`. C06b no reutiliza sus SKUs ni sus 28 colecciones | Índice, evaluación |
| D1 | Catálogo sintético | Hasta completar **~1.200** con D0 (holgura) | LLM+CLI; colecciones **nuevas** (hotel / aeropuerto / clásico); precio razonado; `data_origin`/`text_provenance: synthetic`; ~35 % multi-material **en el texto**. **Sin familias** | Índice |
| D2 | Perfiles IA | = D0+D1 | `materials[]`, confianza por campo, `source: rule\|inferred` | Filtros, revisión |
| D3 | `SourceText` + embeddings | = D0+D1 | Incluye familia y variante **cuando C18 las haya aprobado** | Búsqueda vectorial |
| D4 | Familias | las que C18 apruebe | **`ProductFamily` + miembros**, propuestos por C18. C06b **no** preasigna miembros: el catálogo híbrido nace huérfano | Desambiguación, alerta de calidad |
| D5 | Corpus de conocimiento | 30-45 docs → 150-250 chunks | Fichas **por material**, no por producto | Citas, faithfulness |
| D6 | Red de POS | 10-14 | **Marca de origen de suministro** (§14) | Filtros, perfil, reposición |
| D7 | Inventario por POS | 5.000-9.000 filas | — | Prior de ranking, sustitutos |
| D8 | Histórico de ventas | 15.000-25.000 / 14-18 meses | **Co-ocurrencia por operación de venta** | Rotación, perfil POS, complementarios, reposición |
| D9 | Diccionario de sinónimos | 40-60 entradas | **Nuevo**, curado a mano | Rama léxica |
| D10 | Consultas de operador | 300-400 | Categorías de sinónimos y multi-material | Calibración |
| D11 | **Golden set** | 60-70 etiquetadas a mano por ambos | + categorías sinónimo y materiales múltiples; **prioridad a productos reales**, con `data_origin` por caso | Métricas de recuperación |
| D12 | Casos adversarios | 20-25 | — | Guardrails |
| D13 | Escenarios de agente | 20-25 (venta) + 8-10 (inventario) | **Nuevo**: escenarios de inventario | Eval de agentes |

**Índice vectorial total: ~1.200-1.500 vectores.** Pequeño, y conviene decirlo: pgvector con HNSW es holgado aquí; la decisión se justifica por operación (una sola base de datos, filtros SQL nativos, cero infraestructura nueva), no por escala.

### 8.4. Realismo dirigido

Familias confundibles (3-5 variantes con diferencia solo de talla **en el nombre**, para que C18 tenga qué agrupar) · **~20 % de descripciones escuetas y ~10 % sin descripción** · SKUs sintéticos en un espacio que no colisiona con el real · **~35 % de productos multi-material en la prosa** · colisiones semánticas verificadas (ningún par > 0,97 coseno) · consultas con faltas, abreviaturas y sinónimos · estacionalidad por hotel.

**Revisado el 2026-08-17.** Donde antes decía «~30 % de descripciones pobres» ahora hay dos tramos, porque «pobre» agrupaba dos casos que el recuperador no trata igual: un texto escueto aporta algo de señal léxica y uno vacío no aporta ninguna. Y **el reparto se sortea por familia de variantes, nunca por producto suelto**: todos los miembros de una familia comparten nivel. Sin esa regla, la riqueza del texto se convierte en un discriminador artificial dentro de la familia y contamina la desambiguación de variantes, que son 10 de las 60-70 consultas del golden set y el caso que este documento llama crítico. La unidad es la familia de variantes y no el tipo de pieza: sobre el catálogo real hay 354 grupos internos (C06a) frente a tipos de pieza concentrados.

**Revisado el 2026-08-22.** El «15 % de huérfanos deliberados» era ruido **inyectado por el generador** (85 % ya miembros de `ProductFamily`). Eso **chivaba C18**. C06b no escribe pertenencia: reales y sintéticos nacen huérfanos; la alerta de calidad de §7.5 opera sobre lo que C18 no asigne. El ~350 de D4 deja de ser cupo de C06b.

### 8.5. Calidad, privacidad y trazabilidad

- **Puertas de calidad** antes de indexar: unicidad de SKU, vocabulario cerrado respetado, `materials` no vacío salvo justificación, **cobertura de tags ≥ 70 % global y ≥ 90 % sobre el estrato `text_provenance: ai_assisted`**, sin colisiones, sin obligatorios vacíos. Falla la puerta → falla el pipeline.

  *Revisado el 2026-08-17.* El umbral era del 90 % global, cifra fijada suponiendo descripciones de longitud normal. Con el reparto de §8.4 el techo alcanzable es ≈ 77 %, así que el 90 % global bloquearía el pipeline siempre. Peor aún, un umbral solo global **mide en parte la propia política de ruido**: cambiar el reparto haría saltar la puerta sin que el extractor se hubiera tocado, y una puerta que salta por decisiones nuestras deja de detectar regresiones. El desglose por estrato conserva la exigencia donde hay evidencia textual y deja de castigar el 10 % que se vació a propósito. Es también lo que permite cumplir la puerta **sin violar** la regla de §7.1 —«devuelve `[]` si no hay evidencia, nunca inventa»—, con la que el 90 % global era incompatible sobre este catálogo.
- **PII**: el modelo **no almacena datos de cliente final** (`Sale` no tiene cliente). Los únicos datos personales son de operadores: ficticios en sintético, anonimizados antes de salir de producción si hay export. Ningún dato personal entra en el índice ni en un prompt.
- **Trazabilidad**: cada dataset lleva `generator_version`, `seed`, `model`, `generated_at`; el corpus se regenera con un comando.

---

## 9. Capa agéntica

### 9.1. Un agente, y no escribe

Eran dos hasta el 2026-08-31; el de inventario se anuló con toda su rama de implementación.

| Agente | Qué decide | Tools (todas de lectura) | Salida |
|---|---|---|---|
| **Asistente de venta** (síncrono) | Si buscar, si pedir aclaración, si pivotar a sustitutos o variantes, si consultar conocimiento | `buscar_catalogo`, `consultar_disponibilidad` (~~.NET~~ → **`ai.pos_projection`**, *corregido el 2026-09-20*), `listar_familia`, `buscar_sustitutos`, ~~`buscar_complementarios`~~, `consultar_conocimiento`, `pedir_aclaracion` — **seis** *(corregido el 2026-09-13)* | Resultados estructurados + borrador de venta que confirma el operador |
| ~~**Agente de inventario** (batch)~~ | ~~Qué priorizar, qué sustituto proponer, cómo redactar el motivo~~ | ~~`senales_demanda`, `stock_por_pos`, `buscar_sustitutos`, `perfil_punto_venta`~~ | **Fuera desde el 31 ago** |

~~**Siete tools, no ocho.**~~ → **Seis** *(corregido el 2026-09-13; el documento hermano ya lo había bajado a seis el 12 de septiembre y esta sección no se sincronizó).* `perfil_punto_venta` sale del registro con el perfil por POS: registrar una tool cuyo servicio no existe le da al modelo una herramienta que falla siempre, y una tool que devuelve error es peor que una tool ausente — el bucle la reintenta y quema presupuesto. Si el perfil por POS se rescata, vuelve. Y `buscar_complementarios` **salió el 12 de septiembre**, al dispararse el corte nº 1 del §13.4 sobre complementarios: la condición era exactamente ésta y se cumplió. **El recuento no es lo que el PF evalúa del agente**: lo son el bucle, el presupuesto duro, el invariante de solo-lectura y el `partial: true`.

> **Dos de las seis llegan medio construidas** *(anotado el 2026-09-13, al partir C30)*.
> `listar_familia` la sirve el `family_roster(family_id)` que C30a añade al puerto de búsqueda para
> su aviso de variantes, y `consultar_conocimiento` la sirve el `search_knowledge` que C23 dejó
> **con forma de tool a propósito**, al que C30a añade el filtro por ficha de material. Cuando el
> bucle las invoque sobre una pieza concreta, la segunda ya no podrá citar la ficha de un material
> que la pieza no declara. Lo nuevo del change del agente es el bucle, no las herramientas.

**Los números nunca los calcula el LLM.** Sigue siendo el principio rector, y sigue siendo verificable con lo que queda: precio y stock viajan como **placeholders** que el modelo no puede rellenar (§7.7), el hidratador .NET los resuelve, y el validador determinista del §11.3 rechaza la respuesta si sobrevive alguna cifra sin contrastar. Es exactamente la matriz §7.3 de las especificaciones v2.

### 9.2. Control del bucle y HITL

- Presupuesto duro: 5 iteraciones y ~~6~~ → **8** llamadas a tools por consulta *(corregido el 2026-09-21: el techo lo movió la medición de C32b, que en 6 truncaba el 3,9 % de las peticiones con un p95 de 5 y no dejaba sitio al pivote)*, más los cuatro que C32b añadió —llamadas al proveedor (8, derivado de sus tres tramos), tokens (40.000), contexto en caracteres (30.000) y **reloj de pared** (15 s para la petición entera, argumentario incluido)—; superado cualquiera, responde con lo que tenga, marca `partial: true` y nombra el presupuesto en un motivo de parada de vocabulario cerrado.
- **Ninguna tool escribe.** La única acción con efecto en venta es "seleccionar para venta", que devuelve un borrador confirmado por el operador en el flujo existente. En inventario, toda recomendación nace `Proposed` y requiere aprobación explícita del admin.
- Orquestación: bucle manual con function calling. No se adopta LangGraph: no hay ramificación con estado ni reanudación que lo justifique. El punto de migración queda identificado.

---

## 10. Inventario asistido — FUERA DEL ALCANCE, diseño conservado

> **⛔ Anulado el 2026-08-31, con toda su rama de implementación** (C19, C29, C33, C35, C37 del documento hermano). **Esta sección se conserva íntegra a propósito:** es lo que el README adjunta como próximo paso, y una limitación identificada con su solución ya diseñada puntúa en la evaluación del PF donde un hueco no puntúa nada.
>
> **Por qué se anula.** No aporta nada al sistema RAG. La afirmación del §10.1 de que las señales son *«reutilizadas por el ranking de búsqueda»* es cierta del concepto y **falsa del cableado**: el ranking usa `sales_30d` y `qty_bucket` desde `ai.pos_projection`, que se sincroniza del feed de indexación, y ni ese feed ni el ranking dependen de este bloque. Lo que compraba era el segundo agente, a cambio de cinco changes de los que tres no tienen ni una llamada a un LLM.
>
> **Dos cosas que hay que saber antes de retomarlo:**
>
> 1. **El perfil por POS (§10.3) no depende de las señales de demanda (§10.1)**, aunque el plan lo encadenaba así. Sus siete métricas son agregados a nivel POS sobre ventas y perfiles IA, y lo único per-producto que usan —`sales_30d` y `lastSaleAt`— ya lo calcula el feed. Es la pieza rescatable por separado, y la que devuelve al agente de venta su octava tool.
> 2. **La ventana de 7 días hay que replantearla, y está medido.** El mundo sintético termina el 2026-08-23; contra el reloj de pared el 2026-08-31, `sales_7d` es distinto de cero en **3 de 6.050** pares (producto, POS) activos — 0,05 %. Anclada al final de los datos serían 443. Toda señal con ventana necesita un instante de referencia inyectado y **declarado en la respuesta**, igual que `projection_age_seconds` declara la frescura de la proyección en el §7.6.

### 10.1. Señales de demanda — .NET, en SQL

Por producto y POS: `sales_7d`, `sales_30d`, `sales_60d`, `current_stock`, `stock_in_other_pos`, `days_since_last_sale`, `avg_daily_sales_30d`, `estimated_days_to_stockout`, `is_top_seller_in_pos`. Deterministas y testeables sin LLM.

### 10.2. Reglas iniciales

| Tipo | Regla | Salida |
|---|---|---|
| `Replenish` | `current_stock = 0` y `sales_30d > 0` → prioridad alta; `estimated_days_to_stockout < 14` y `sales_30d ≥ 2` → media/alta | Producto, POS destino, cantidad, origen sugerido |
| `Transfer` | Destino con stock 0 y `sales_30d ≥ 2`; origen con stock ≥ 3 y `sales_60d = 0` | Origen, destino, cantidad |
| `Substitute` | Reposición no satisfacible por falta de stock global | Sustitutos del retriever con señales de similitud |
| `Rotate` | `stock > 0` y `days_since_last_sale > 90` → stock parado; si otro POS vende, sugerir traslado | POS destino sugerido |
| `Review` | Sin ventas y perfil IA incompleto | Revisar catálogo antes de decidir |

`Liquidate` **no se implementa**: toca precios y exige decisión de negocio y auditoría propias.

### 10.3. Perfil comercial por POS (decisión 7)

Calculado periódicamente en .NET desde ventas e inventario: `top_piece_types`, `top_materials`, `top_price_ranges`, `top_collections`, `average_ticket`, `best_selling`, `slow_moving`. Se almacena estructurado y el LLM **solo redacta el resumen a partir de esas métricas**, con un test que verifica que no menciona nada ausente del payload. Se consume en tres sitios: prior de ranking en búsqueda, priorización de sustitutos y ajuste de cantidades en reposición.

### 10.4. Aprobación y salida física

Pantalla de revisión con aprobar/rechazar por recomendación, señales visibles y motivo. Desde las aprobadas, **vista imprimible agrupada por POS destino** con SKU, nombre, foto, cantidad, origen y motivo — el 80 % del valor operativo de una packing list sin su máquina de estados. La packing list completa (Draft→Approved→Prepared→Delivered→Applied→Cancelled con auditoría) queda para fase posterior.

---

## 11. Evaluación

### 11.1. Golden set

**60-70 consultas** etiquetadas a mano, con relevancia graduada (0/1/2) sobre un *pool* generado por la unión de todas las configuraciones (*pooling*).

> **Corregido el 2026-08-31.** La v3 decía *«por las dos personas por separado, con conciliación de discrepancias»*. Con un solo anotador eso no existe, y el sustituto no es fingirlo: **se etiqueta una vez**, se conserva el *pooling* —que es la mitad del rigor y no depende del número de personas—, se añade **relectura diferida** de las consultas etiquetadas con dudas, y el README **declara la ausencia de acuerdo entre anotadores** como limitación del golden set en lugar de reclamar una mitigación que no se aplicó.

| Categoría | Nº | Qué mide |
|---|---:|---|
| Descripción natural | 20 | Recuperación semántica pura |
| Variante / talla (familia) | 10 | Desambiguación: el caso crítico |
| **Materiales (incl. multi-material)** | 8 | Filtro por solape sobre `materials[]` |
| **Sinónimos** | 6 | Diccionario de expansión |
| Precio / ocasión / regalo | 8 | Filtros estructurales |
| Sustituto / sin stock | 6 | Retriever invertido |
| Léxico exacto (SKU, nombre) | 5 | Rama léxica |
| Ambigua → requiere aclaración | 5 | Decisión del agente |
| Fuera de dominio / imposible | 5 | Abstención y guardrails |

### 11.2. Ablations

| Config | Descripción |
|---|---|
| **v0-lexico** | Buscador actual del repo — **es la comparación "búsqueda actual vs semántica" que pide la decisión 12** |
| **v0-cag** | Catálogo del POS entero en contexto, sin retrieval |
| **v1-vectorial** | Solo pgvector + threshold |
| **v2-hibrido** | Vectorial + léxico (RRF) + **sinónimos** + filtros estructurales |
| **v2b-fusion** | la fusión **por rama** con ponderación adaptativa por cobertura, **sin** señales de negocio |
| **v3-señales** | v2b + disponibilidad |

> **Revisado el 2026-09-11, al aplicar C25.** La tabla pasa de cinco filas a **seis** y el
> criterio de aceptación, de absoluto a **relativo**.
>
> **`v3-señales` se parte en dos.** Sin una fila que aísle la fusión, una mejora en `v3` sería
> **inatribuible**: no se sabría si el mérito es de la composición o de las señales. Y hubo que
> aislarla porque la fusión de C21 resultó no fusionar sino **concatenar** — con sus pesos, los
> sesenta documentos léxicos ganaban al mejor acierto vectorial en toda consulta, de modo que un
> grado 2 que la vectorial ponía primero caía a la **posición 33**.
>
> **La fila pierde dos de sus tres señales.** *Rotación*: como desempate estricto decidía **cero**
> pares del top-5 en las 48 consultas, y como clave de ordenación no desempataba sino que
> particionaba —11.067 pares invertidos, el 71,2 % a más de diez puestos— con coste en relevancia.
> `sales_30d` se lee para diagnóstico y **no ordena**. *Perfil de POS*: anulado con C19 el
> 2026-08-31. Queda la disponibilidad, y su peso decide su **signo y no su valor**: con un único
> término binario el orden es invariante a la magnitud, así que `1,0` es unidad declarada.
>
> **Los tres umbrales absolutos no se alcanzan, y se declaran en vez de cerrarse.** `Recall@5`
> real llega a **0,758** contra 0,85; la abstención correcta a **0,150** contra 0,80. Los dos se
> fijaron **antes de que existiera el golden set** que los mediría, y ninguna palanca de C25 puede
> cerrarlos: el recall a cinco depende de **qué** entra en la ventana y las señales sólo reordenan
> lo que ya entró. `nDCG@5 ≥ 0,75` sí se alcanza en global (0,740 en `v2b`, 0,729 en `v3`) pero no
> sobre la porción real. **El `p95` sí se cumple con holgura: 128,6 ms contra 500.**
>
> **El criterio pasa a ser relativo:** cada configuración bate a aquella sobre la que se construye,
> en la lectura que decide y por encima de un margen de 0,05. `v2b` lo cumple con **+0,083**;
> `v3` **no** lo alcanza —+0,030 en la métrica operativa— y se adopta igualmente porque cumple su
> propia regla de adopción y porque el golden set es **estructuralmente ciego** a la
> disponibilidad: `criterion.md` no menciona stock ni rotación, así que lo que falta es resolución
> del instrumento y no evidencia. Esa brecha queda declarada, no cerrada.
>
> **Y aparece una tercera lectura de la misma anotación**, la *operativa*, con una función de
> ganancia declarada antes de medir: un grado 2 agotado cuenta como grado 1, porque la rúbrica ya
> define el grado 1 como *«sustituto plausible que el operador ofrecería como segunda opción»* y
> una pieza que no se puede poner sobre el paño es exactamente eso. No inventa constante y no toca
> `judgements.jsonl`. La relevancia pura queda como **guardarraíl**.

Métricas: Recall@5, nDCG@5 —en sus tres lecturas: graduada, binaria y **operativa**—, MRR, P@3, abstención correcta, % sin resultado, p50/p95 y coste por consulta. Aceptación **relativa** (revisada el 2026-09-11): cada fila bate a aquella sobre la que se construye por encima de 0,05 en la lectura que decide, sin que ninguna categoría medida caiga más de 0,05; el `p95` de retrieval sigue por debajo de 500 ms. La distancia a los umbrales absolutos originales —`Recall@5 ≥ 0,85` y abstención ≥ 0,80— se declara como limitación con sus cifras medidas.

**Las lecturas de relevancia se promedian sobre las consultas contestables**, no sobre todas. Una consulta de fuera de dominio tiene el conjunto relevante vacío, así que puntúa 0 para **toda** configuración por construcción: promediarla no informa del orden y **comprime toda diferencia**. Medido al ampliar esa categoría de 5 a 20, la mejora de la fusión por rama leía +0,053 con ellas dentro y +0,084 fuera — con un margen de 0,05, una mejora real se quedó a tres milésimas de ser vetada por la composición del conjunto en vez de por su mérito. Esas consultas se informan por la métrica que sí las mide, que es la tasa de abstención.

**Cada métrica se reporta tres veces: sobre la porción real, sobre la sintética y global** (§8.1.1). El umbral de aceptación se aplica a **la porción real**; si el global cumple y el real no, la conclusión es que el corpus sintético es demasiado fácil, no que el sistema funcione.

> **Añadido el 2026-08-10, al diseñar C04.** Esta tabla es offline, sobre el golden set. Al decidir que `ProductSearchEvent` registre también las búsquedas **degradadas** —las que responde el buscador léxico existente cuando el circuito abre, §6.4— aparece de regalo una comparación **online** entre `v0-lexico` y la configuración en producción: mismo operador, mismas consultas reales, dos rutas distinguidas por la columna `SearchOrigin`. No sustituye a la tabla —no hay relevancia etiquetada— pero sí aporta lo que ninguna ablación offline puede: qué elige de verdad una persona con un cliente delante. El `p95` de recuperación queda además medido en producción y no solo en el harness, gracias a `RetrievalMs`. Sin esa columna, además, un periodo con el cortacircuitos abriéndose se leería como una degradación del ranking cuando la IA sencillamente no corrió.

**Reranking:** no se implementa. El README documenta la hipótesis (con ~1.500 entidades el cuello de botella es el corpus y el filtrado, no el orden dentro del top-20), el protocolo con el que se mediría (dos filas más en esta tabla, delta de nDCG@5 contra delta de p95) y el criterio de decisión.

### 11.3. Generación

- **Validador anti-alucinación determinista** (sin LLM juez): extrae toda cifra de precio/stock de la respuesta final y la contrasta con el hidratador. **Umbral: 0 fallos.** Es la pieza de evaluación con mejor retorno y convierte el principio 2 en garantía verificable.

  > **Revisado el 2026-09-13.** Este validador **mide** en evaluación una garantía que ahora se
  > sostiene también **en ejecución**: C30b lleva una puerta por **lista blanca** —el argumentario
  > sólo puede contener cifras presentes en el payload que se le entregó, más los dos tokens de
  > placeholder— porque un pitch que escriba «39,90 €» literal no deja ningún placeholder sin
  > resolver y por tanto **pasa el rechazo de .NET** del §7.7. Lo que cambia aquí es que este
  > validador deja de ser la primera línea y pasa a ser la que comprueba que la primera funciona,
  > que es un test más fuerte. Y la **excepción de persistencia** que el §7.7 declara vive
  > precisamente aquí: el arnés sí guarda las generaciones, atadas a `run_id`, `git_sha` y
  > `prompt_version`.
- **RAGAS** (faithfulness, answer relevancy, context precision, context recall) sobre el subconjunto con citas.
- **Verificación de citas**: toda afirmación del corpus apunta a un `chunk_id` existente y realmente recuperado.
- ~~**Test de fidelidad del perfil por POS**~~: fuera desde el 31 ago — evaluaba el perfil por POS, anulado. Vuelve si el perfil se rescata.

### 11.4. Agentes

20-25 escenarios multi-turno de venta, con éxito definido. Métricas: *task success rate*, tools invocadas vs esperadas, pasos, coste medio, tasa de escalado. Más 20-25 casos adversarios con criterio de bloqueo por categoría.

Los **8-10 escenarios de agente de inventario** salen el 2026-08-31 con el agente. Lo que la evaluación conserva es lo que el PF puntúa: validador anti-alucinación con umbral cero, escenarios de venta, adversarios y RAGAS.

### 11.5. Métricas del enriquecimiento

Del lote revisado a mano (§7.8): **tasa de corrección por campo** (cuántos `materials`, `piece_type`, `size_label` inferidos corrigió el humano) y **tiempo medio de revisión**. Son los números que dicen si el extractor sirve, y no existen sin la vía revisada.

### 11.6. Iteración de prompts

Prompts versionados en `ai-service/prompts/`; cada versión guarda su ejecución del harness. El README muestra qué se cambió y qué métrica se movió.

---

## 12. Despliegue

Se hace en la **ola 2**, no al final: con dos personas, descubrir un problema de infraestructura el 30 de agosto es fatal.

1. `docker-compose` gana el servicio `jbg-ai` en red interna de la EC2, **no publicado en nginx**.
2. RDS: `CREATE EXTENSION vector`, esquema `ai`, usuario propio. Alembic, independiente de EF Core. **Verificar que RDS lo admite en la ola 0.**
3. Secretos en SSM Parameter Store.
4. Workflow `deploy-ai-service.yml` con el patrón OIDC + ECR existente.
5. `/health` con conectividad a BD, proveedor y estado del índice; tarjeta en el dashboard de admin.
6. **Evidencia**: URL pública con usuario demo, vídeo de 2-3 min y `docker compose up` reproducible con corpus incluido.

**Coste estimado**: decenas de euros con modelo de embeddings pequeño y generación económica; instrumentado y reportado.

---

## 13. Plan de trabajo (3 agosto → 3 septiembre 2026)

### 13.1. Modelo de trabajo

**Un desarrollador, sin roles** *(desde el 2026-08-31; eran dos)*, que trabaja indistintamente en Python, .NET y frontend y **toma el siguiente change desbloqueado**. El detalle, con prerequisitos y grafo de changes vivos, está en [proyecto-final-plan-changes-openspec.md](proyecto-final-plan-changes-openspec.md).

Tres reglas de orden:

1. **Prioridad al desbloqueo, no al calendario.** Entre los changes libres se coge el que más aristas abre en el grafo, no el marcado de ruta crítica: el caso vivo es el diccionario de sinónimos, fuera de ruta crítica y sin embargo único prerrequisito pendiente de la búsqueda híbrida, que a su vez bloquea el harness de evaluación **y** la capa de generación.
2. **Una sola migración EF Core activa a la vez.** Con un solo desarrollador deja de ser coordinación y pasa a ser disciplina de rama: dos migraciones abiertas colisionan en el orden igual aunque las escriba la misma mano.
3. **Contratos congelados el día 2** con test de *snapshot* de OpenAPI: cambiar el contrato rompe el build y obliga a decidirlo, en vez de filtrarse.

### 13.2. Olas

> **Registro, no plan** *(desde el 2026-08-31)*. Con prórroga abierta no hay fechas que cumplir: las olas describen cómo se ejecutó O0–O2 y en qué orden estaba previsto lo demás. **Lo que decide qué se abre a continuación es el grafo de dependencias del documento hermano.** La O4 tal como está descrita ya no existe: pierde señales de demanda, motor de recomendaciones, agente de inventario y pantallas de revisión de inventario, y se queda en generación, guardrails, agente de venta y evals.

| Ola | Fechas | Objetivo | Hito verificable |
|---|---|---|---|
| **O0** | 3-5 ago | Cimientos y **contratos congelados**. Esqueleto del servicio, cliente .NET con circuit breaker, verificación de pgvector en RDS | `GET /health` responde; nadie espera a nadie |
| **O1** | 6-12 ago | **Datos y modelo.** Generador de catálogo con `materials[]`, familias, enriquecimiento, esquema `ai`, entidades .NET (`ProductAiProfile`, `ProductFamily`), feeds con tombstones | ~1.000 perfiles generados y validados; familias propuestas |
| **O2** | 13-19 ago | **Slice vertical desplegado.** Indexador, recuperación, endpoint .NET con hidratación autoritativa, panel en la SPA, **servicio en producción** | Un operador busca en lenguaje natural desde `pv.joiabagur.com` con stock real |
| **O3** | 20-26 ago | **Calidad y medición.** Híbrido + sinónimos, prior de disponibilidad, corpus de conocimiento, **golden set (ambos)**, baselines, señales de negocio, sustitutos y complementarios | **Tabla de ablations v0→v3 con números reales** |
| **O4** | 27-31 ago | **Agentes e inventario.** Generación con citas y avisos por reglas, guardrails, agente de venta, señales de demanda, motor de recomendaciones, agente de inventario, pantallas de revisión, evals finales | Flujo completo en producción; validador anti-alucinación en verde; recomendaciones aprobables |
| **O5** | 1-3 sep | **Congelación.** README, diagramas, limitaciones, vídeo, tag, entrega | Entrega el 3 de septiembre |

### 13.3. Trabajo restante

*(Reescrito el 2026-08-31.)* De **41 fichas** planificadas quedan **36 vivas**: **19 archivadas** y **17 pendientes**. No se planifica por semanas ni por carga: se toma el siguiente change que más desbloquee.

### 13.4. Orden de corte, fijado de antemano

**Reescrito el 2026-08-31.** La lista tenía ocho posiciones y **cuatro vivían dentro del bloque de inventario** —rotación, traslados, vista imprimible y el agente entero—, que es lo que delató que el bloque sobraba: un plan que se compromete de antemano a destripar una funcionalidad está diciendo que no la necesita. Anulado el bloque, el disparador deja de ser una fecha y pasa a ser el juicio de que el núcleo peligra:

1. **Complementarios** → fase posterior; los sustitutos ya cubren el caso de venta. Ahorra además la última migración EF Core viva
2. **Corpus de conocimiento** 30-45 → **15 documentos**, manteniendo las citas verificables
3. **RAGAS** → se conservan validador anti-alucinación, escenarios de venta y adversarios
4. **Golden set** 70 → 45 consultas

Los cortes **1 y 2 están confirmados de antemano** y se aplican desde el principio del change, no a mitad.

**Nunca se recorta:** corpus e índice, familias, **diccionario de sinónimos** (tapona el grafo), retriever híbrido con prefiltro blando, hidratación autoritativa en .NET, **guardrails**, agente de venta, harness con ablations, validador anti-alucinación, **métricas de revisión humana del enriquecimiento** (las pide el checklist del §16 y el §11.5 advierte de que no existen sin la vía revisada), despliegue y README.

### 13.5. Riesgos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| **Equipo de uno** *(desde el 31 ago)*: cualquier interrupción para el proyecto entero | Alta | Medio | **Mitigado por la prórroga abierta**: sin fecha, una pausa retrasa pero no recorta. Sigue valiendo el slice vertical ya desplegado y el orden de corte fijado |
| ~~**El alcance de inventario desborda la ola 4**~~ | — | — | **Se materializó, y la respuesta fue anular el bloque entero** el 31 de agosto, no degradarlo. La degradación prevista —recomendaciones por reglas puras sin capa agéntica— habría dejado en pie una migración, un motor de reglas .NET y una pantalla, es decir todo el coste fuera de lo que el PF evalúa |
| **El export real llega tarde o es muy pequeño** | Media | Medio | El generador se calibra con lo que haya; si el export llega después de C24, el golden set se re-ancla sobre productos reales en una sesión adicional. Nunca se bloquea el desarrollo esperándolo |
| La revisión humana de 120-150 perfiles se alarga | Media | Medio | Pantalla de revisión por lotes con atajos; tope de 3 h por persona; el resto va a `auto_bulk` declarado |
| Datos sintéticos demasiado fáciles → métricas infladas | Alta | Alto | Ruido dirigido (§8.4); métricas **reportadas por `data_origin`** y umbral aplicado a la porción real. **La mitigación de «etiqueta quien no generó el corpus» ya no es posible** con un solo desarrollador: se declara en el §15 |
| Disponibilidad irregular | Alta | Bajo *(era Alto)* | **Degradado por la prórroga abierta**: sin fecha, la irregularidad retrasa y no recorta. Contratos congelados y trabajo desacoplado siguen valiendo |
| Fricción con pgvector en RDS | Baja | Alto | **Verificar en O0**; alternativa: contenedor Postgres+pgvector en la misma EC2 |

---

## 14. Preguntas abiertas que bloquean trabajo

| # | Pregunta | Estado | Resolución |
|---|---|---|---|
| 1 | **¿Existe una "tienda central" u origen de suministro?** | ⛔ **Sin objeto** *(31 ago)* | Se resolvió que sí, y la columna `IsSupplySource` iba a añadirse en C19. **Anulado con la rama.** La marca sigue existiendo solo en el YAML de perfiles de POS del mundo sintético (`MAO-TALLER`), nunca llega a SQL, y el `insert_pos` del ingest tampoco la escribía |
| 2 | **¿Habrá export anonimizado de catálogo e histórico 2026?** | ✅ **Resuelto** | Sí, de tamaño desconocido y probablemente insuficiente. **Corpus híbrido** con `data_origin` y métricas desglosadas (§8.1.1). El golden set se ancla en lo real |
| 3 | **¿Diccionario de sinónimos en lugar de `SearchAliases`?** | ⏳ **Pendiente de acuerdo** | Se implementa tras flag y se decide con la categoría de sinónimos del golden set. Coste de discrepancia: cero |
| 4 | **¿Packing list fuera del PF?** | ⛔ **Sin objeto** *(31 ago)* | Fuera, y ahora también lo está la vista imprimible que iba a sustituirla: sin recomendaciones que aprobar no hay nada que imprimir |
| 5 | **Umbrales iniciales de reposición** (días de cobertura, mínimo por POS) | ⛔ **Sin objeto** *(31 ago)* | Los valores por defecto propuestos —cobertura < 14 días, `sales_30d ≥ 2`— quedan anotados en el §10.2 para quien retome el bloque |
| 6 | **¿Se captura feedback del admin sobre sustitutos?** | ⛔ **Sin objeto** *(31 ago)* | Se registraba en la recomendación, que ya no existe. Los sustitutos (§6.3.2) siguen vivos, pero se consumen en venta asistida y ahí el feedback es la propia venta |
| 7 | **¿Qué tamaño tiene el export real?** | 🔸 **A verificar antes del 10 de agosto** | Determina cuántas de las 60-70 consultas del golden set se pueden anclar en productos reales y cuánto sintético hay que generar. No cambia el diseño, sí la fuerza de la evidencia |

---

## 15. Limitaciones que el README debe declarar

1. **El corpus es híbrido**: una porción real anonimizada (436 productos), ampliada con sintéticos hasta ~1.200 totales. El README declara el porcentaje exacto de cada origen y **reporta las métricas desglosadas**, con la porción real como resultado principal. Los sintéticos (C06b) los escribe un LLM, con SKUs y colecciones que no reutilizan el ancla real; no son un clon estadístico del export.

   **Y el texto de esa porción real no lo escribió el comerciante** *(añadido el 2026-08-17)*. El export llegó con 38,5 caracteres de media entre nombre y descripción —51 productos sin descripción ninguna— y **sin una sola etiqueta de estilo, color u ocasión**, que son campos que el enriquecimiento necesita extraer. Su texto se ha redactado con un LLM que **simula un reconocimiento multimodal de fotografías que no está implementado**: no hay ni una foto en el sistema. La redacción expande la evidencia que sí constaba —el 88 % de los productos ya declaraba tipo de pieza y material— y acota por banda de precio lo que no constaba, pero **los atributos no derivables de esa evidencia son plausibles, no verificados**: un anillo puede figurar con diamantes sin que nadie haya comprobado que los lleva. `SKU`, precio y colección no se tocan en ningún caso y siguen siendo reales.

   Tres consecuencias que el lector debe tener presentes: la afirmación defendible es **«funciona sobre un catálogo realista»**, no «sobre un catálogo real»; las métricas de **enriquecimiento** (§11.5) no se ven afectadas, porque miden al extractor y no la verdad del dato; las de **recuperación** dejan de describir el negocio tal como está hoy. El catálogo original queda archivado y **el delta entre ambos sigue siendo medible** con un segundo `eval_run` (§11.2).
2. **Solo el 17,0 % de los perfiles está revisado por humanos** *(medido el 2026-09-13, al ejecutar C28)*; el resto es `auto_bulk` y está marcado como tal en todas las métricas. Son **204 perfiles de 1.200**, en una sesión de 109 minutos, repartidos por muestreo estratificado sobre los 1.168 aprobados: **70 del estrato de ausencia de evidencia (57 % de ese estrato), 69 del de valores afirmados sin frase en el texto (24 %) y 65 del de valores con frase (8,5 %)**. La muestra no es uniforme a propósito, así que la tasa de corrección publicada va **ponderada por el tamaño real de cada estrato en el catálogo**.

   Y el porcentaje no es lo único que hay que declarar: **las dos cifras que el §16 pide no son comparables entre sí**. La tasa ponderada global es del **20,9 %**, pero se descompone en **10,4 % sobre los campos sensibles** —los que el §7.8 define como aquellos cuyo error llega a un cliente— y **42,3 % sobre las etiquetas comerciales**, que normalmente llegaban vacías y que el revisor rellenó con su criterio. Esa segunda cifra no mide al extractor contra una verdad de referencia: mide una opinión de estilo y ocasión donde el criterio declarado de la revisión —fidelidad al texto de origen— apenas restringe la respuesta. **La cifra que este documento defiende es el 10,4 %**, y el 20,9 % nunca se cita sin su descomposición al lado. Detalle completo en [c28-implementation-measurements.md](informes/c28-implementation-measurements.md).
3. **No hay validación con usuarios reales.** Los KPIs de negocio están instrumentados, no medidos.
4. **El golden set es pequeño (60-70), lo etiquetó quien construyó el sistema, y no hay acuerdo entre anotadores** *(corregido el 2026-08-31)*. La v3 prometía doble etiquetado con conciliación entre dos personas; el proyecto lo desarrolla una sola, así que esa mitigación **no se aplicó** y el README lo dice en lugar de reclamarla. Lo que sí se conserva es el *pooling* sobre la unión de todas las configuraciones —que evita el sesgo de evaluar solo lo que la configuración favorita recupera— y la relectura diferida de las consultas etiquetadas con dudas. La consecuencia honesta: los valores absolutos de nDCG y Recall llevan el sesgo de un único juicio, y **lo comparable entre configuraciones sigue siendo válido**, porque el sesgo es el mismo en todas las filas de la tabla de ablations.
5. **El reranking no se ha medido**, solo argumentado y protocolizado.
6. **Packing list, liquidación con descuentos, upsell/downsell y políticas de inventario configurables no están implementados** y se declaran como fase posterior.
7. **Dos espacios vectoriales conviven** (visual MobileNetV2 y textual): no se fusionan.
8. **Ningún agente escribe.** Toda acción con efecto pasa por el operador o el admin.
9. **El sistema entrega un solo agente, el asistente de venta** *(añadido el 2026-08-31)*. El agente de inventario —reposiciones, traslados y detección de stock parado con aprobación humana— estaba en el alcance acordado y **se anuló junto con toda su rama de implementación**, cinco changes de los que tres no contenían LLM. El motivo no fue de plazo: no aportaba nada al sistema RAG, porque la señal de demanda que pondera el ranking ya llega por el feed de indexación y no por él. **Su diseño está completo en el §10** de este documento —señales, reglas, perfil por POS y ciclo de aprobación— y se entrega como próximo paso, con dos avisos medidos: el perfil comercial por POS no depende de las señales de demanda y es rescatable por separado, y la ventana de 7 días necesita un instante de referencia inyectado antes de significar nada.
10. **La proyección de disponibilidad puede desfasarse minutos**; por eso solo pondera el ranking y nunca excluye.
11. **La telemetría de búsqueda no tiene política de retención** *(añadido el 2026-08-10, al diseñar C04)*. `ProductSearchEvent.SearchText` es texto libre escrito por un operador y se conserva indefinidamente; en un punto de venta de hotel puede recoger incidentalmente una referencia a un huésped. Las medidas adoptadas son proporcionadas al riesgo real —tope de 500 caracteres, el texto confinado a nivel `Debug` en los logs, y **ninguna ruta de lectura por API**: solo se consulta con SQL—, y no se aplica anonimización porque este texto nunca entra en el espacio vectorial ni se recupera semánticamente. La supresión por usuario queda operable: el enlace `Sale.SearchEventId` es `ON DELETE SET NULL`, así que borrar eventos no destruye ni bloquea ventas.

12. **La pregunta libre sin pieza elegida no tiene pantalla** *(añadido el 2026-09-13, al partir C30; **reescrito el 2026-09-22, al implementar C36**)*. De los tres modos de la venta asistida, el servicio implementa los tres y **dos llegan ya al operario**: el **argumentario de una pieza** y la **pregunta sobre una pieza**, los dos en la ficha de venta que C36 entrega en `/sales/new/assist/:productId`. Eso es lo que cambia: hasta C36 la afirmación era *«sólo dos llegan»* en futuro, y ahora es un hecho con pantalla, con tres entradas —la fila de búsqueda asistida, el producto elegido en la página de venta y la pieza resuelta tras escanear— y con una caja de pregunta que lleva **cinco sugerencias horneadas** del propio corpus.

    **El tercero sigue sin pantalla, y la limitación no se cierra.** La **pregunta libre, sin pieza delante**, existe en el servicio y sus consumidores son el bucle del agente y el arnés de evaluación, no una caja de texto. La consecuencia concreta es que el *«no lo sé»* del sistema ante una consulta fuera de dominio **se demuestra con escenarios y no en pantalla**. Lo que sí deja de ser cierto es la segunda mitad de la frase original: las diez fichas de mostrador del corpus —playa y piscina, piel sensible, niños, viajar, regalar sin saber la talla, cosmética— **ya tienen ruta hasta el joyero**, aunque sigan requiriendo una pieza anclada. Exponer el tercer modo son una ruta nueva en .NET y un bloque de respuesta en el panel de búsqueda; está identificado, acotado y **no hecho**.

13. **La abstención del catálogo está al 10 %, y en el camino de venta asistida se aplica sin clasificar la intención** *(añadido el 2026-09-13; **ampliado el 2026-09-22, al implementar C36**)*. La brecha de la tasa ya se declara en el §11.2 desde C25 —llegar a 0,80 costaba silenciar 21 de 43 consultas contestables—, pero conviene decir lo que eso significa aguas abajo: la capa de generación **no redacta** cuando el perfil de candidatos es plano, y eso es una red, no un clasificador. Distinguir *«el catálogo no puede contestar esto»* de *«esto no es una pregunta de joyería»* es trabajo del enrutador de intención, que llega después. Hasta entonces, una consulta fuera de dominio recibe una abstención honesta y no un rechazo cortés, que son dos cosas distintas y la segunda es la buena.

    **Y C31 no cambia esto, aunque exista, porque su enrutador no llega a ninguna pantalla** *(2026-09-22)*. `classify_query` corre **sólo en el modo de consulta libre**, y las dos rutas que la ficha de C36 consume son **siempre ancladas**: `query_out_of_domain` y `query_not_in_catalogue` **no pueden emitirse** por el camino que tiene interfaz. La ficha, por tanto, **no escribe castellano para ellos** —sería copia muerta sobre caminos imposibles— y los trata como cualquier código desconocido, con la etiqueta neutra y **un test que lo comprueba**: `should label a router refusal code with the neutral fallback`. Por la misma razón, `clarification_question` es constante `null` en estas rutas y no tiene bloque propio. El rechazo cortés existe en el servicio, está medido en el arnés de C31 y **sigue sin superficie de operario**; la distinción se demuestra ahí y sólo ahí.

14. **La ficha de venta no tiene telemetría, así que su uso no es medible** *(añadido el 2026-09-22, al implementar C36)*. A diferencia de la búsqueda asistida, que persiste `ProductSearchEvent` desde C04 y con él sostiene la tasa de selección del §11, **ninguna de las tres cosas que la ficha decide deja rastro**: abrirla, preguntar, y elegir una variante. No hay tabla equivalente y C36 no la crea —crearla era una migración, y la zona del change es `frontend/src/`—. Se declara como limitación y no como medición pendiente, porque tiene una consecuencia concreta y desagradable: **la condición de reactivación de la tarea diferida de `generate=false` no se puede comprobar con datos**. Esa tarea propone servir la parte estructural de la ficha —grupo, avisos y existencias, que no cuestan ni un token— sin pagar una generación de p50 4,4 s, y su criterio de reactivación era *«que el uso real muestre aperturas que no leen el argumentario»*. Sin telemetría, ese criterio no es observable, así que la decisión tendrá que tomarse por argumento o abriendo antes la telemetría. **La selección sí se reporta cuando se vende desde la ficha**, por la vía existente de la página de venta; lo que no se cuenta es la apertura, y **abrir la ficha desde la fila de resultados deliberadamente no reporta selección**, porque ver una ficha no es elegir la pieza y contarlo inflaría la métrica que el evento de búsqueda existe para medir.

**Próximos pasos**, en orden de madurez del diseño: **agente de inventario completo** —señales de demanda, motor de reglas, perfil comercial por POS, ciclo de aprobación y vista imprimible—, cuyo diseño está íntegro en el §10 y solo espera implementación; **perfil comercial por POS** por separado, que es la mitad barata de lo anterior y devuelve al agente de venta una octava tool; packing list completa; liquidación y políticas de inventario; prioridad comercial por margen (los datos existen en `ProductComponentAssignment`); reranking medido; reranking aprendido con `ProductSearchEvent` reales; fusión de señal visual y textual; evaluación online con A/B por POS.

---

## 16. Checklist de entrega

- [ ] Rama `finalproject-[INICIALES]` con README y código funcional
- [ ] README con dominio, arquitectura y decisiones justificadas, CAG/RAG/agente/evaluación/despliegue, arranque local, autoría **individual**, limitaciones y próximos pasos
- [ ] URL pública con usuario demo **y** vídeo de 2-3 min
- [ ] Tabla de ablations v0→v3 reproducible con un comando
- [ ] Métricas de revisión humana del enriquecimiento (tasa de corrección y tiempo medio)
- [ ] Prompts versionados con evidencia de iteración
- [ ] `docker compose up` reproducible con corpus sintético
- [ ] Tag `v1.0-final-[INICIALES]`
- [ ] Acceso al TA si el repositorio es privado
- [ ] **Tres declaraciones que el README debe llevar explícitas** *(añadido el 2026-08-31)*: **un solo agente**, con el §10 adjunto como diseño del que falta; **golden set sin acuerdo entre anotadores**, por etiquetador único; y **proyecto individual**, no en pareja
- [x] ~~**Dos declaraciones más**~~ *(añadido el 2026-09-13, al partir C30; matizado el 2026-09-22 con C36; **cerradas el 2026-09-25 al implementar C40**)*: la **pregunta libre sin pieza no tiene pantalla** (§15.12) y la **abstención se aplica sin clasificar intención** (§15.13). **Las dos las cierra C40**, y conviene decir cómo, porque no es sólo «ya hay pantalla»: el modo M1 tiene su propia ruta (`POST /api/ai/search/assisted`), un toggle que lo hace alcanzable, y las **dieciséis** condiciones en que su respuesta puede llegar se distinguen en pantalla en vez de colapsarse en «sin resultados» — que era el riesgo real, porque el panel de C16 tenía cinco ramas de vacío y tres de los estados nuevos se pintaban mal por defecto. El rechazo cortés del enrutador **tiene ya superficie**, con dos textos distintos para «no es una pregunta de joyería» y «no trabajamos ese tipo de pieza», y la repregunta llega literal desde el catálogo cerrado del servicio. La abstención sigue corriendo, y además **lee ahora un perfil sin filtro**: era la avería que quedaba, porque sobre un perfil filtrado la regla no puede dispararse cuando el filtro es estrecho, y el sistema servía piezas mediocres con prosa elogiándolas
- [ ] **Una declaración más** *(añadido el 2026-09-22, al implementar C36; **matizada el 2026-09-25 con C40**)*: **la ficha de venta no tiene telemetría** (§15.14). Abrirla, preguntar y elegir variante no dejan rastro, así que su uso no es medible y la condición de reactivación de la tarea diferida de `generate=false` no es observable con datos. **C40 no la cierra y sí la estrecha**: la consulta libre **sí** deja rastro, con un cuarto origen propio (`SearchOrigin.AssistedGenerative`) que convierte la comparación de las dos rutas del panel en una consulta sobre la telemetría en vez de una demostración en pantalla. La ficha sigue sin él, y aparece un hueco nuevo y declarado: **una consulta libre de ámbito global no se registra**, porque la tabla exige un punto de venta y darle uno falso está prohibido — ver `openspec/DEFERRED_TASKS.md`
- [ ] **Ablación de la capa de generación** *(añadido el 2026-09-13)*: misma ruta, mismos candidatos y mismas citas, **con argumentario y sin él**. Sale gratis del corte de C30 en dos mitades —la estructurada no llama a ningún proveedor— y es la única fila de la tabla del §11.2 que aísla lo que aporta el LLM frente a lo que ya aportaba la recuperación
- [ ] **El argumentario no tiene copia durable en ninguna parte** *(añadido el 2026-09-13)*: ni en base de datos ni en logs, con la excepción declarada del arnés de evaluación (§7.7, §11.3). Es una propiedad comprobable, así que o se declara cierta o no se declara
- [ ] ~~Entrega antes del 3 de septiembre de 2026~~ → **prórroga abierta desde el 2026-08-31**; el objetivo es entregar cuanto antes, sin fecha comprometida
