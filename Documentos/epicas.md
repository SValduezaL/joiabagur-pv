# Épicas - Sistema de Gestión de Puntos de Venta para Joyería

Este documento describe las épicas del proyecto, agrupadas en dos bloques:

- **EP1–EP10 — MVP (Fase 1):** el sistema de gestión de puntos de venta. Sus User Stories viven en `Documentos/Historias/` con el formato `HU-EP[X]-[NNN].md`.
- **EP11–EP17 — Proyecto Final de IA:** búsqueda semántica, venta asistida y agentes sobre el catálogo existente. Sus User Stories viven en `Documentos/Historias/AI-Eng/` con el formato `HU-AIENG-[NNN].md`.

Cada épica agrupa funcionalidades relacionadas y contiene referencias a las User Stories correspondientes.

---

## Bloque 1 — MVP (EP1–EP10)

---

## Épica 1: Gestión de Productos

**Descripción:**  
Permite gestionar el catálogo centralizado de productos de la joyería, incluyendo la creación, edición, importación desde Excel y asociación de fotos de referencia para el reconocimiento de imágenes.

**Alcance:**
- Importación masiva de productos desde archivos Excel con matching por SKU
- Creación y edición manual de productos (SKU, nombre, descripción, precio, colección)
- Gestión de fotos de referencia (subida, eliminación, ordenamiento, foto principal)
- Visualización del catálogo completo con fotos asociadas
- Validación de datos y manejo de errores en importaciones

**Entidades del modelo de datos relacionadas:**
- `Product` (SKU único, precio, descripción, colección)
- `ProductPhoto` (múltiples fotos por producto, ordenamiento, foto principal)
- `Collection` (agrupación opcional de productos)

**User Stories:**
- [HU-EP1-001: Importar productos desde Excel](Historias/HU-EP1-001.md)
- [HU-EP1-002: Crear producto manualmente](Historias/HU-EP1-002.md)
- [HU-EP1-003: Editar producto existente](Historias/HU-EP1-003.md)
- [HU-EP1-004: Subir fotos de referencia a producto](Historias/HU-EP1-004.md)
- [HU-EP1-005: Gestionar fotos de producto (eliminar, reordenar, marcar principal)](Historias/HU-EP1-005.md)
- [HU-EP1-006: Visualizar catálogo de productos](Historias/HU-EP1-006.md)
- [HU-EP1-007: Buscar productos por SKU o nombre](Historias/HU-EP1-007.md)

---

## Épica 2: Gestión de Inventario

**Descripción:**  
Gestiona la asignación de productos a puntos de venta y el stock de dichos productos, permitiendo asignaciones manuales, importaciones masivas, ajustes manuales y consultas del inventario actual.

**Regla de negocio clave:** La presencia de un registro en `Inventory` (independientemente de la cantidad) determina que el producto está asignado al punto de venta y es visible para los operadores asignados a dicho punto de venta.

**Alcance:**
- **Asignación manual de productos a puntos de venta** (crear registros en Inventory con cantidad inicial 0)
- **Desasignación de productos** de puntos de venta (soft delete con preservación de historial)
- Importación de stock desde Excel (suma a cantidades existentes, con asignación implícita si el producto no está en el inventario del POS)
- Visualización de stock por punto de venta
- Vista centralizada de stock total y por ubicación
- Ajustes manuales de inventario con trazabilidad
- Validación de stock no negativo

**Entidades del modelo de datos relacionadas:**
- `Inventory` (asignación de productos a POS y stock actual por producto y punto de venta)
- `InventoryMovement` (historial completo de movimientos con trazabilidad)
- `Product` (referencia al producto del catálogo global)
- `PointOfSale` (referencia al punto de venta)

**User Stories:**
- [HU-EP2-001: Importar stock desde Excel](Historias/HU-EP2-001.md)
- [HU-EP2-002: Visualizar stock por punto de venta](Historias/HU-EP2-002.md)
- [HU-EP2-003: Visualizar stock centralizado (todos los puntos de venta)](Historias/HU-EP2-003.md)
- [HU-EP2-004: Realizar ajuste manual de inventario](Historias/HU-EP2-004.md)
- [HU-EP2-005: Consultar historial de movimientos de inventario](Historias/HU-EP2-005.md)
- [HU-EP2-006: Asignar/desasignar productos a puntos de venta](Historias/HU-EP2-006.md)

---

## Épica 3: Registro de Ventas

**Descripción:**  
Permite registrar ventas en los puntos de venta, con actualización automática del inventario y trazabilidad completa de las transacciones.

**Alcance:**
- Registro de ventas con método de pago
- Actualización automática de stock al registrar venta
- Registro de foto asociada a la venta (cuando se usa reconocimiento de imagen)
- Validación de stock disponible antes de venta
- Validación de método de pago asignado al punto de venta
- Registro de usuario operador que realiza la venta
- Edición manual de precio de venta cuando el punto de venta lo permite, con trazabilidad de precios modificados
- Carrito de ventas con persistencia local y checkout masivo atómico (`POST /api/sales/bulk`)
- Agrupación de ventas creadas en checkout masivo mediante `BulkOperationId`
- Prevención de envíos duplicados mediante clave de idempotencia

**Entidades del modelo de datos relacionadas:**
- `Sale` (venta con precio snapshot, cantidad, método de pago, fecha, indicador de precio modificado, `BulkOperationId` opcional)
- `SalePhoto` (foto opcional asociada a la venta)
- `InventoryMovement` (movimiento automático generado por la venta)
- `PaymentMethod` y `PointOfSalePaymentMethod` (validación de métodos disponibles)
- `User` (operador que realiza la venta)

**User Stories:**
- [HU-EP3-001: Registrar venta con reconocimiento de imagen](Historias/HU-EP3-001.md) *(incluye validación de stock y selección de método de pago)*
- [HU-EP3-002: Registrar venta manual (sin foto)](Historias/HU-EP3-002.md) *(incluye validación de stock y selección de método de pago)*
- [HU-EP3-003: Registrar venta con precio manual modificado](Historias/HU-EP3-003.md) *(edición de precio cuando el POS lo permite, auditoría de precios modificados)*
- [HU-EP3-004: Carrito de ventas y checkout masivo](Historias/HU-EP3-004.md) *(carrito persistente, checkout atómico multi-línea, idempotencia)*

---

## Épica 4: Reconocimiento de Imágenes con IA

**Descripción:**  
Sistema de identificación de productos mediante reconocimiento de imágenes usando inteligencia artificial, generando sugerencias ordenadas por precisión.

**Alcance:**
- Captura de foto del producto vendido
- Procesamiento de imagen mediante modelo de IA
- Generación de 3-5 sugerencias de productos ordenadas por precisión/confianza
- Visualización de sugerencias con fotos de referencia
- Validación manual del operador antes de confirmar

**Entidades del modelo de datos relacionadas:**
- `ProductPhoto` (fotos de referencia para entrenamiento/comparación)
- `ProductPhotoEmbedding` (vectores de características MobileNetV2 almacenados por foto, usados para similitud coseno)
- `SalePhoto` (foto capturada en el punto de venta)
- `Product` (productos candidatos sugeridos)

**Consideraciones técnicas:**
- Procesamiento de imágenes en cliente (navegador) usando TensorFlow.js
- **Método de inferencia principal (implementado):** Similitud coseno sobre embeddings MobileNetV2 almacenados en base de datos. Más rápido y fiable que el clasificador para catálogos pequeños.
  - Los embeddings se generan automáticamente al subir/eliminar fotos
  - "Generar Embeddings" en la página de IA permite regeneración masiva (~30-60 segundos)
  - La similitud coseno se calcula en el navegador con Float32Arrays; ~366 comparaciones en <1ms
  - Umbrales: `SIMILARITY_THRESHOLD = 0.70` (mínimo para aparecer en sugerencias), `MIN_TOP_SIMILARITY = 0.50` (mínimo del top-1)
- **Método de inferencia de respaldo:** Clasificador entrenado (Dense 256 → 128 → N clases). Se usa cuando no existen embeddings generados (instalación inicial o rollback).
- Generación de 3-5 sugerencias ordenadas por similitud/confianza
- Manejo de errores cuando no hay correspondencia fiable (redirigir a venta manual)
- Almacenamiento de fotos: sistema de archivos local en desarrollo, S3/Blob Storage en producción

**User Stories:**
- [HU-EP4-001: Reconocimiento de productos mediante imagen](Historias/HU-EP4-001.md) *(consolida captura, procesamiento, visualización y selección)*

---

## Épica 5: Gestión de Devoluciones

**Descripción:**  
Permite registrar devoluciones de productos vendidos, asociándolas a una o más ventas originales, incrementando el stock automáticamente y manteniendo trazabilidad completa. Soporta devoluciones parciales, categorización obligatoria y foto opcional.

**Alcance:**
- Registro de devolución asociada a una o más ventas originales (multi-venta)
- Soporte para devoluciones parciales (devolver parte de las unidades vendidas)
- Ventana de devolución de 30 días desde la venta
- Devolución obligatoria en el mismo punto de venta de la venta
- Categoría de devolución obligatoria (Defectuoso, Tamaño incorrecto, No satisfecho, Otro)
- Motivo de texto libre opcional (máximo 500 caracteres)
- Foto opcional de devolución (ej: foto del producto defectuoso)
- Incremento automático de stock en el punto de venta
- Generación automática de movimiento de inventario (tipo "Return")
- Validación de cantidad disponible (vendida - ya devuelta)
- Operadores pueden registrar devoluciones en sus puntos de venta asignados

**Entidades del modelo de datos relacionadas:**
- `Return` (devolución con cantidad, categoría y motivo)
- `ReturnSale` (relación muchos a muchos entre devoluciones y ventas, con cantidad y precio snapshot)
- `ReturnPhoto` (foto opcional asociada a la devolución)
- `InventoryMovement` (movimiento automático de tipo "Return")
- `Sale` (ventas originales referenciadas)
- `Inventory` (stock incrementado)

**User Stories:**
- [HU-EP5-001: Registrar devolución de producto vendido](Historias/HU-EP5-001.md)
- [HU-EP5-002: Buscar ventas elegibles para asociar devolución](Historias/HU-EP5-002.md)
- [HU-EP5-003: Consultar historial de devoluciones](Historias/HU-EP5-003.md)

---

## Épica 6: Gestión de Métodos de Pago

**Descripción:**  
Configuración y gestión de métodos de pago disponibles en el sistema, con asignación específica por punto de venta.

**Alcance:**
- Lista general de métodos de pago predefinidos (Efectivo, Bizum, Transferencia, Tarjetas TPV, PayPal)
- Asignación de métodos de pago a puntos de venta específicos
- Activación/desactivación de métodos por punto de venta
- Validación de métodos disponibles al registrar ventas

**Entidades del modelo de datos relacionadas:**
- `PaymentMethod` (métodos de pago generales con código único)
- `PointOfSalePaymentMethod` (relación muchos a muchos con activación/desactivación)

**User Stories:**
- [HU-EP6-001: Configurar métodos de pago disponibles en el sistema](Historias/HU-EP6-001.md)
- [HU-EP6-002: Asignar métodos de pago a punto de venta](Historias/HU-EP6-002.md)
- [HU-EP6-003: Activar/desactivar método de pago en punto de venta](Historias/HU-EP6-003.md)

---

## Épica 7: Autenticación y Gestión de Usuarios

**Descripción:**  
Sistema de autenticación y gestión de usuarios con roles (Administrador y Operador), incluyendo asignación de operadores a puntos de venta.

**Alcance:**
- Login con usuario y contraseña
- Gestión de roles (Admin con acceso completo, Operador con acceso restringido)
- Asignación de operadores a puntos de venta específicos
- Control de acceso basado en roles y asignaciones
- Gestión de usuarios (crear, editar, desactivar)

**Entidades del modelo de datos relacionadas:**
- `User` (usuarios con roles Admin/Operator, autenticación)
- `UserPointOfSale` (asignación de operadores a puntos de venta)
- `PointOfSale` (puntos de venta asignables)

**User Stories:**
- [HU-EP7-001: Login de usuario con usuario y contraseña](Historias/HU-EP7-001.md)
- [HU-EP7-002: Crear nuevo usuario](Historias/HU-EP7-002.md)
- [HU-EP7-003: Editar usuario existente](Historias/HU-EP7-003.md)
- [HU-EP7-004: Asignar operador a punto de venta](Historias/HU-EP7-004.md)
- [HU-EP7-005: Desasignar operador de punto de venta](Historias/HU-EP7-005.md)
- [HU-EP7-006: Control de acceso según rol y asignaciones](Historias/HU-EP7-006.md)

---

## Épica 8: Gestión de Puntos de Venta

**Descripción:**  
Permite crear, editar y gestionar los puntos de venta del sistema, incluyendo asignación de operadores y métodos de pago.

**Alcance:**
- Creación y edición de puntos de venta (nombre, código, dirección, teléfono, email)
- Asignación de operadores a puntos de venta
- Asignación de métodos de pago a puntos de venta
- Activación/desactivación de puntos de venta
- Visualización de puntos de venta disponibles según rol
- Configuración de política de edición manual de precio por punto de venta

**Entidades del modelo de datos relacionadas:**
- `PointOfSale` (información del punto de venta, incluye `AllowManualPriceEdit`)
- `UserPointOfSale` (asignación de operadores)
- `PointOfSalePaymentMethod` (asignación de métodos de pago)

**User Stories:**
- [HU-EP8-001: Crear punto de venta](Historias/HU-EP8-001.md)
- [HU-EP8-002: Editar punto de venta existente](Historias/HU-EP8-002.md)
- [HU-EP8-003: Activar/desactivar punto de venta](Historias/HU-EP8-003.md)
- [HU-EP8-004: Visualizar puntos de venta disponibles](Historias/HU-EP8-004.md)
- [HU-EP8-005: Configurar edición manual de precio por punto de venta](Historias/HU-EP8-005.md)

---

## Épica 9: Consultas y Reportes

**Descripción:**  
Proporciona funcionalidades de consulta y visualización de datos históricos de ventas e inventario, con filtros y búsquedas.

**Alcance:**
- Consulta de historial de ventas con filtros (punto de venta, fecha, producto, método de pago, operador)
- Visualización de detalles de ventas (foto, SKU, precio, método de pago, fecha, operador)
- Consulta de inventario con búsqueda de productos
- Visualización de movimientos de stock históricos
- Paginación de resultados para optimización

**Entidades del modelo de datos relacionadas:**
- `Sale` (con índices optimizados para consultas por punto de venta, producto, usuario, método de pago)
- `SalePhoto` (fotos asociadas a ventas)
- `Inventory` (stock actual)
- `InventoryMovement` (historial de movimientos)

**Optimizaciones:**
- Índices compuestos en `Sale` para consultas frecuentes
- Paginación obligatoria (máx 50 items por página)
- Filtros eficientes por fecha, punto de venta, producto

**User Stories:**
- [HU-EP9-001: Consultar historial de ventas con filtros](Historias/HU-EP9-001.md)
- [HU-EP9-002: Visualizar detalles de una venta](Historias/HU-EP9-002.md)
- [HU-EP9-003: Consultar inventario con búsqueda](Historias/HU-EP9-003.md)
- [HU-EP9-004: Consultar movimientos de inventario](Historias/HU-EP9-004.md)

---

## Épica 10: Gestión de Componentes de Joyas

**Descripción:**  
Permite gestionar los componentes que constituyen las joyas (materiales, mano de obra, etc.) mediante una tabla maestra, asignarlos a productos con cantidades y precios por defecto o override, calcular costes y precios de venta sugeridos, y generar reportes de márgenes. Solo visible para administradores.

**Decisiones de diseño tomadas:**
- **Precio oficial vs sugerido:** `Product.Price` es el precio oficial de venta. El precio calculado por componentes es solo informativo/sugerencia.
- **Override obligatorio (asignación manual):** Cada asignación de componente a producto debe tener precios de coste y venta definidos (manual o desde plantilla).
- **Override opcional:** Solo en plantillas: al aplicar plantilla se cargan precios desde la tabla maestra como valores por defecto.
- **Precisión decimal:** 4 decimales para cantidad, coste y venta.
- **Orden:** Los componentes se listan en el orden especificado en la UI; se permite reordenar con drag-and-drop.
- **Integración:** Gestión de componentes integrada dentro de la sección Productos (subsección).
- **Visibilidad:** Componentes y totales calculados ocultos para todos los roles (campo solo admin).
- **Componentes desactivados:** No se pueden asignar nuevos; los ya asignados a productos mantienen su asignación.

**Alcance:**
- Tabla maestra de componentes (Descripción, CostPrice, SalePrice opcionales, activar/desactivar)
- Asignación de componentes a productos con cantidad y precios override
- Autocomplete por descripción para buscar componentes
- Cálculo de totales en tiempo real (TotalCostPrice, TotalSalePrice)
- Sincronización de precios desde maestro con confirmación
- Advertencia de desviación de precio (>10%) con acción rápida para ajustar
- Plantillas de componentes (lista de componentes + cantidades, precios desde master)
- Reporte de márgenes por producto (tabla, filtros, totales, export Excel)
- Reporte de productos sin componentes (con botón para editar)

**Entidades del modelo de datos relacionadas:**
- `ProductComponent` (tabla maestra: Descripción, CostPrice, SalePrice opcionales, IsActive)
- `ProductComponentAssignment` (ProductId, ComponentId, Quantity, CostPrice, SalePrice, DisplayOrder)
- `ComponentTemplate` (plantillas: Id, Name, Description)
- `ComponentTemplateItem` (TemplateId, ComponentId, Quantity)

**User Stories:**
- [HU-EP10-001: Gestionar tabla maestra de componentes](Historias/HU-EP10-001.md)
- [HU-EP10-002: Asignar componentes a producto en edición](Historias/HU-EP10-002.md)
- [HU-EP10-003: Asignar componentes a producto en creación](Historias/HU-EP10-003.md)
- [HU-EP10-004: Sincronizar precios desde maestro](Historias/HU-EP10-004.md)
- [HU-EP10-005: Advertencia de desviación de precio (10%)](Historias/HU-EP10-005.md)
- [HU-EP10-006: Gestionar plantillas de componentes](Historias/HU-EP10-006.md)
- [HU-EP10-007: Reporte de márgenes por producto](Historias/HU-EP10-007.md)
- [HU-EP10-008: Reporte de productos sin componentes](Historias/HU-EP10-008.md)

**Matriz de dependencias entre User Stories de EP10:**

| Historia | Depende de | Es base para |
|----------|------------|--------------|
| HU-EP10-001 | EP7 (auth, roles) | HU-EP10-002, HU-EP10-003, HU-EP10-006 |
| HU-EP10-002 | HU-EP10-001, HU-EP1-003, EP7 | HU-EP10-003, HU-EP10-004, HU-EP10-005, HU-EP10-006, HU-EP10-007 |
| HU-EP10-003 | HU-EP10-001, HU-EP10-002, HU-EP1-002, EP7 | HU-EP10-006 |
| HU-EP10-004 | HU-EP10-002 | — |
| HU-EP10-005 | HU-EP10-002 | — |
| HU-EP10-006 | HU-EP10-001, HU-EP10-002, HU-EP10-003 | — |
| HU-EP10-007 | HU-EP10-002, EP9 (Reportes), EP7 | — |
| HU-EP10-008 | HU-EP10-001, HU-EP1-003, EP9, EP7 | — |

**Orden recomendado de implementación EP10:** 001 → 002 → 003 → 004 → 005 → 006 → 007, 008 (007 y 008 pueden hacerse en paralelo tras 002).

---

## Bloque 2 — Proyecto Final de IA (EP11–EP17)

> Las épicas EP1–EP10 cubren el MVP del sistema de punto de venta. Las siguientes cubren el **Proyecto Final del Máster de IA**: incorporan búsqueda semántica, venta asistida y agentes sobre el catálogo existente, mediante el microservicio `jbg-ai`.
>
> **Convención de nomenclatura.** A diferencia del MVP, las historias del PF **no** se numeran por épica: siguen una serie plana `HU-AIENG-[NNN]` en `Documentos/Historias/AI-Eng/`, porque el trabajo se organiza por *change* de OpenSpec (C01–C39) y una misma historia puede atravesar varias épicas. Cada épica indica abajo qué changes agrupa.
>
> **El número de la historia es el del change, no el de creación** *(regla fijada el 2026-08-16, al redactar HU-AIENG-008)*. `HU-AIENG-[NNN]` y su ticket `T-AIENG-[NNN]` toman el número de `C[NN]`, de modo que el trío historia ↔ ticket ↔ change se lee sin tabla de equivalencias. Los changes se cogen por desbloqueo y no por orden, así que la serie tendrá huecos —`006` y `007` esperan a C06 y C07— y eso es correcto: un hueco significa «ese change aún no se ha redactado», que es exactamente lo que se quiere saber de un vistazo.
>
> **Fuentes:** [diseño del sistema de IA](Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) (§4 alcance acordado, §6 frontera, §7 diseño RAG) y [plan de changes](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (tabla maestra C01–C39).

---

## Épica 11: Plataforma del Servicio de IA

**Descripción:**
Cimientos del microservicio `jbg-ai`: esqueleto ejecutable, contratos HTTP congelados, autenticación entre servicios, esquema vectorial y despliegue. Es la épica habilitadora: sin ella ninguna de las siguientes puede empezar.

**Alcance:**
- Servicio Python con FastAPI, `uv`, configuración por entorno y `GET /health`
- Contratos `/v1/*` congelados con modelos Pydantic, stubs deterministas y snapshot OpenAPI versionado
- JWT interno HS256 entre .NET y Python, con scope por usuario, rol y punto de venta
- Cliente tipado `IAiGatewayClient` en .NET con timeouts, reintento y circuit breaker
- Esquema `ai` con pgvector, migraciones y rol de base de datos dedicado
- Despliegue del contenedor en un **entorno de demostración aislado, en una cuenta AWS propia** —no en la de la tienda, a la que no hay acceso—, secretos en el almacén de parámetros y health enriquecido con contraste del modelo de embeddings contra el índice

**Changes asociados:** C01, C02, C03, C05, C17

**User Stories:**
- [HU-AIENG-001: Esqueleto ejecutable del servicio de IA](Historias/AI-Eng/HU-AIENG-001.md) *(C01 — hecho)*
- [HU-AIENG-002: Contratos congelados y autenticación de servicio](Historias/AI-Eng/HU-AIENG-002.md) *(C02 — hecho)*
- [HU-AIENG-003: Cliente tipado .NET hacia `jbg-ai` con resiliencia y token de servicio](Historias/AI-Eng/HU-AIENG-003.md) *(C03 — hecho)*
- [HU-AIENG-005: Cimiento de persistencia vectorial — extensión `vector`, esquema `ai` y migraciones Alembic](Historias/AI-Eng/HU-AIENG-005.md) *(C05 — hecho)*
- [HU-AIENG-017: Entorno de demostración aislado — despliegue del servicio de IA, salud enriquecida y tarjeta de estado](Historias/AI-Eng/HU-AIENG-017.md) *(C17 — hecho)*

---

## Épica 12: Corpus y Enriquecimiento del Catálogo

**Descripción:**
Construcción del corpus sobre el que opera todo el sistema RAG: perfiles de producto extraídos con LLM contra vocabularios cerrados, confianza por campo y revisión humana híbrida, más el corpus de conocimiento comercial que permite responder con citas verificables.

**Alcance:**
- ✅ Corpus JSONL de 436 productos reales con procedencia dual, pipeline offline en `scripts/catalog/` e ingesta local de `Description` (C06a)
- Pipeline de enriquecimiento: normalización determinista → extracción estructurada → validación → confianza por campo
- `materials[]` como lista contra vocabulario cerrado; nunca se inventa un material por defecto
- Entidad `ProductAiProfile` en .NET con su ciclo de aprobación
- Texto canónico (`SourceText`) y `source_hash`: solo se recalcula el embedding si cambia el hash
- Corpus de conocimiento comercial **general, no por producto** (materiales, piedras, tallas, cuidados, alergias, servicio, glosario y origen de las colecciones), troceado por secciones y citable, con el **alcance de cada afirmación declarado por sección**: `general` si es comprobable fuera, `establecimiento` si es un compromiso de la joyería. Sin guiones de venta: el corpus guarda hechos para citar, el prompt guarda instrucciones para obedecer (C23)
- Generador de mundo sintético (CLI `jbg_ai.data.world`, YAML de 12 POS, Poisson, ingest local) para disponer de inventario y ventas coherentes con el catálogo
- El vocabulario cerrado se amplía **sólo por change**, con salto de versión de prompt y reenriquecimiento de una cohorte enumerada (FIX1)

**Changes asociados:** C06a (hecho), C06b (hecho), C08 (hecho), C09 (hecho), C10 (hecho), C11 (hecho), **C23** (`add-knowledge-corpus-and-indexer` — **hecho**, abierto y archivado el 2026-09-06; capability viva `knowledge-corpus`), **FIX1** (`fix-enrichment-vocabulary-gaps`, fuera de la numeración C — **hecho**, abierto, ejecutado y archivado el 2026-09-05; entró antes de que C24 etiquete)

- **C23 (hecho, abierto y archivado el 2026-09-06):** el **segundo índice** del sistema. `ai.product_document` responde a «enséñame anillos de plata» y no puede responder a «¿este anillo se puede mojar?», porque esa respuesta no vive en ningún producto. C23 construye el corpus de conocimiento general, su troceado por secciones, su indexación idempotente en `ai.knowledge_chunk` —tabla que **existe desde C05 y que ningún código escribe todavía**— y su búsqueda con citas. **La exploración corrigió la ficha y el plan en dos puntos, con medición sobre los 1.200 productos:** (1) el corte pre-autorizado del §13.4 bajaba el alcance a **15 documentos**, pero se expresó **en documentos** cuando la cifra que el diseño fija en D5 está **en chunks (150-250)**: quince dan ~80, la mitad, y con un índice tan pequeño **la abstención no se puede demostrar**. Se entregan **32 documentos ≈ 161 chunks**, que es el centro de D5; el corte no se ignora, se refuta por su propia unidad de medida. (2) `guion_venta` **sale del corpus y no por alcance**: un guion es texto imperativo, y un chunk imperativo recuperado dentro de un prompt es indistinguible de una instrucción — convertiría el propio corpus en superficie de inyección, con C31 todavía sin existir. **Y la medición del catálogo funda tres documentos que habrían sido inventados:** la letra de talla del catálogo **no es una talla de dedo sino el tamaño de la pieza** —el tipo que más etiquetas lleva es `pendientes`, que no tiene ajuste—; las colecciones llevan **nombre de calas y cabos reales de Menorca** (`Es Caló Blanc`, `Biniacolla`, `Sa Mesquida`, `Cala Pregonda`, `Cala Presili`, `Binibeca`, `Cavalleria`), lo que rescata un documento que la propia exploración había descartado; y **once de las 28 «colecciones» no son líneas de diseño** sino cajones operativos (`Varios`, `Composturas`, `Tienda`, `Cursos`…), hallazgo de calidad de catálogo que nadie buscaba. **El problema que gobierna el diseño no es de código:** el corpus lo redacta un asistente, porque los textos comerciales que el §8.1 daba como «a pedir al negocio» nunca llegaron, y la verificación de citas es **estructural, no semántica** — puede pasar al 100 % citando algo falso. De ahí `claim_scope` por sección: el origen del texto es constante y vive en el sidecar y en el README, pero el **alcance** varía dentro de un mismo documento y cambia el comportamiento. Sin migración, sin ruta HTTP, sin tocar `openapi.json` ni `indexing/embeddings.py`. Historia [HU-AIENG-023](Historias/AI-Eng/HU-AIENG-023.md), ticket [T-AIENG-023](../openspec/changes/archive/2026-09-06-add-knowledge-corpus-and-indexer/ticket.md) y mediciones en [c23-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c23-exploration-measurements.md) y [c23-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c23-implementation-measurements.md).

- **C23 — lo que la implementación midió (2026-09-06).** Corpus entregado: **32 documentos y 161 secciones**, exactamente el recuento fijado de antemano, con **25 secciones `establecimiento`** —el 15,5 %, la cifra que el README declara— y **cero `guion_venta`**. **La rama léxica se queda, por medición**, aunque su papel se aclaró en dos pasos: contra el embebedor *offline* ganaba recall (78,1 % frente a 71,9 %), y contra el real **no gana recall sino orden** —93,8 % en las dos configuraciones, con MRR 0,891 frente a 0,854—. Sigue justificada, por reordenar y no por recuperar. El umbral queda **calibrado en 0,51**, y esa cifra llegó por el camino largo: el barrido *offline* que la spec obliga a usar daba 0,81, y al indexar el corpus de verdad ese valor **citaba cuatro de las cinco preguntas fuera de dominio** — el mecanismo de abstención inoperante, no una imprecisión. Contra el embebedor real hay un hueco limpio entre 0,5062 y 0,5145, así que la regla de D8 se aplica literalmente por primera vez. **Latencia p50 60,7 ms** en caliente, que es la que hereda C30, con la rama léxica costando unos 3 ms. **Y la re-medición contra `ai.product_document` destapó lo que ningún test buscaba:** cuatro secciones habían copiado las cifras del catálogo al texto citable —«`pequeño` encabeza con 108», «el 44,6 % del surtido»—, lo que ata el corpus al surtido de hoy y hace que un producto nuevo deje una sección falsa **en silencio**, con la cita resolviendo y localizando igual. La regla 5 gana su segunda mitad y la ingesta la comprueba: **ni recuento ni proporción del surtido**, y el detector lee el vecindario para no borrar mineralogía legítima. Seis secciones reescritas, decisión **D17** en el `design.md` y tres escenarios nuevos en la spec, incluido el que enuncia la propiedad de verdad: *añadir o retirar un producto no invalida ningún documento*. Suite completa en verde —incluidos los tests de base contra pgvector— en la corrida del 2026-09-06; **cero migraciones** y `openapi.json` byte a byte idéntico.

- **FIX1 (hecho, 2026-09-05):** cierre de las lagunas del vocabulario de enriquecimiento. `piece_type.terms` pasa de ocho a doce con `diadema`, `gemelos`, `cinturon` y `llavero`; prompt **`enrichment/v2`** con la lista ampliada y la línea que advierte de que el catálogo puede contener servicios, consumibles y regalo —la salida `null` ya existía en C09: **lo que faltaba era el encargo, no la opción**—; y `load_prompt()` pasa a derivar la ruta de `PROMPT_VERSION`, que hasta ahora se declaraban por separado y podían sellar un perfil con una versión que no lo produjo. **La exploración corrigió dos cosas de la ficha, con medición contra la base viva:** (1) la población es de **22 productos y no de 11** — once sin tipo, **nueve mal tipados** y dos falsos amigos («Cinturón de Orión», la constelación) que deben quedarse como están; y el mal tipado es peor que el nulo, porque el filtro de categoría es duro y hoy **seis de los 85 `broche` son tres diademas, dos gemelos y un llavero**, más dos diademas en `collar` y una en `colgante`; (2) su criterio de extremo a extremo —*«buscar "diadema" pasa de cero a resultados»*— **ya se cumple hoy**: la rama léxica de C21 alcanza los 11 documentos porque el nombre está en `doc_text`, así que un verificador lo firmaría verde por el motivo equivocado. Los criterios se reescriben como **estructurales**: nulos 11 → 1, facet `diadema` 0 → 11, impostores en `broche` 6 → 0. Reenriquecer sólo los once nulos entregaría un desplegable que ofrece «Diadema» y devuelve **5 de 11**, que es la firma de C17 en su versión peor —no dice cero, dice cinco—, así que la cohorte son los 22 con los dos de Orión como **grupo de control que debe no moverse**. Toca además **dos specs vivas y no una** (`catalog-enrichment-pipeline` y `query-expansion`) y hace saltar **cuatro tests fijados y no dos**, uno de ellos con `DID NOT RAISE` porque usa `diadema` como ejemplo de canónico desconocido. Sin migración, sin tocar `openapi.json`, sin mover `source-text/v1` ni `embedding_version`. Historia [HU-AIENG-FIX1](Historias/AI-Eng/HU-AIENG-FIX1.md), mediciones en [fix1-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/fix1-exploration-measurements.md) y acta de la corrida en [fix1-vocabulary-gaps-measurements.md](Proyecto%20Final%20AIEng/informes/fix1-vocabulary-gaps-measurements.md). **La corrida encontró lo que ningún test podía encontrar:** la línea nueva sobre servicios, consumibles y artículos de regalo dejó sin tipo a dos de los tres llaveros —un llavero *es* un artículo de regalo—, así que `v2` declara la precedencia de la lista cerrada sobre esa advertencia y la cohorte se volvió a correr entera. Grupo de control intacto campo a campo, 19 filas reembebidas por una sola sincronización, `embedding_version` sin mover.

**User Stories:**
- [HU-AIENG-006a: Ingesta del catálogo real y corpus enriquecido versionado](Historias/AI-Eng/HU-AIENG-006a.md) *(C06a — corpus JSONL + informe)*
- [HU-AIENG-006b: Ampliación sintética del catálogo — LLM, colecciones nuevas e ingesta local](Historias/AI-Eng/HU-AIENG-006b.md) *(C06b — hecho; CLI en `jbg_ai.data`; sin familias)*
- [HU-AIENG-009: Pipeline de enriquecimiento del catálogo — extracción estructurada con vocabularios cerrados](Historias/AI-Eng/HU-AIENG-009.md) *(C09 — hecho; extractor real de `POST /v1/enrich/products`)*
- [HU-AIENG-010: Simulador de mundo sintético — POS, inventario e histórico de ventas](Historias/AI-Eng/HU-AIENG-010.md) *(C10 — hecho; CLI `world simulate` / `world ingest`; YAML en git, JSONL gitignored)*
- [HU-AIENG-011: SourceText canónico y cliente de embeddings con idempotencia por hash](Historias/AI-Eng/HU-AIENG-011.md) *(C11 — hecho; biblioteca `jbg_ai.indexing`, sin HTTP ni SQL)*
- [HU-AIENG-023: Corpus de conocimiento comercial e índice de citas verificables](Historias/AI-Eng/HU-AIENG-023.md) *(C23 — **hecho**; 32 documentos Markdown versionados en `data/knowledge/` con ~161 secciones, `claim_scope` por sección con dos valores —`general` frente a `establecimiento`— y **cero** guiones de venta; troceado por secciones sin solape, con los dos títulos dentro de `content` para que entren a la vez en el embedding y en el `tsv` generado; identidad determinista del chunk (`uuid5` de `<doc_slug>#<section_slug>`) más `citation_id` legible, de modo que la cita **resuelve, localiza y abre el fichero del repositorio** — nunca `uuid4`, nunca `chunk_index`, que repuntaría en silencio cada cita al insertar una sección; indexación idempotente con `content_hash` en `metadata` para no re-embeber lo que no cambió; búsqueda híbrida que **importa** `retrieval/fusion.py` de C21 sin reescribir una línea y compone su rama léxica desde los grupos de C20, con umbral de abstención propio porque el 0,65 se calibró para documentos de producto; paquete propio `jbg_ai/knowledge/` como desviación declarada de la ficha, que asignaba zona sólo de indexación y sin embargo pedía un test de búsqueda; mini-medición de ~32 preguntas más fuera de dominio **sin usar las tablas `ai.eval_*`**, que las crea C24; y la generación del corpus planificada en **ocho encargos, uno por bloque y cada uno en su propia ventana o subagente**, porque 161 secciones no caben en una sola y de una vez las últimas fichas dejan de parecerse a las primeras)*
- [HU-AIENG-FIX1: Cerrar las lagunas del vocabulario de enriquecimiento — cuatro tipos de pieza, `enrichment/v2` y una cohorte de veintidós](Historias/AI-Eng/HU-AIENG-FIX1.md) *(FIX1 — **hecho**; `piece_type.terms` de 8 a 12 con `diadema`, `gemelos`, `cinturon` y `llavero`; prompt `v2` con el encargo que faltaba sobre servicios y consumibles, y `v1.md` conservado intacto porque 1.178 perfiles siguen declarando venir de él; `load_prompt()` derivando la ruta de `PROMPT_VERSION`; cohorte enumerada de 22 SKU con `force` —11 sin tipo y **9 mal tipados**— y los dos «Cinturón de Orión» como grupo de control que debe no moverse; espejo del frontend a 12 opciones, con `cinturon` sin tilde como `value` y «Cinturón» como `label`, porque el filtro compara por igualdad exacta; cierre de las cuatro exclusiones del overlay de C20 y forma de superficie `gemelo`; `filigrana` fuera por ser hueco de `style_tags`; **dos deltas de specs vivas** y **cuatro tests fijados** que saltan a propósito; sin migración, sin OpenAPI y sin mover `source-text/v1` ni `embedding_version`)*

**Entregable C06a.** El corpus versionado vive en [`data/catalog/real/generated/catalog-real-enriched.jsonl`](../data/catalog/real/generated/catalog-real-enriched.jsonl) (sidecar `.meta.json` al lado; `generator_version` `c06a-assist/v2`). Cada línea lleva identidad + `data_origin` / `text_provenance` / `text_quality_tier` (`rich` / `sparse` / `original`); **no** emite `variant_group_key`, `variant_label` ni `family_seed`. La pasada de vendedor, los ratios y la limitación §15 están en [`Proyecto Final AIEng/informes/c06a-catalog-enrichment-report.md`](Proyecto%20Final%20AIEng/informes/c06a-catalog-enrichment-report.md). Los scripts son el pipeline offline [`scripts/catalog/`](../scripts/catalog/). El xlsx crudo sigue gitignored.

**Entregable C06b (JSONL).** El corpus sintético vive en [`data/catalog/synthetic/generated/catalog-synthetic.jsonl`](../data/catalog/synthetic/generated/catalog-synthetic.jsonl) (sidecar al lado; `generator_version` `c06b-synth/v3`, `prompt_version` `catalog-synth/v3`). 764 líneas, híbrido 1.200 con el real. Tiers `rich` / `sparse` / `short` (nunca `empty` ni `original`); el copy se recorta por frases enteras y se aproxima a las medias del real. CLI en [`ai-service/src/jbg_ai/data/`](../ai-service/src/jbg_ai/data/README.md). Recuentos, muestras, ingesta local y nota §15: [`Proyecto Final AIEng/informes/c06b-synthetic-catalog-report.md`](Proyecto%20Final%20AIEng/informes/c06b-synthetic-catalog-report.md). Ingesta Docker (`INSERT` en `:5433` / `joiabagur_pv`): 10 colecciones + 764 productos; GET familia sobre un sintético → 204.

**Entregable C09 (extractor).** `POST /v1/enrich/products` con `STUB_MODE=false` corre el pipeline en [`ai-service/src/jbg_ai/enrichment/`](../ai-service/src/jbg_ai/enrichment/) (vocabularios YAML, talla por regex `Name` > `Description`, LiteLLM temp 0, confianza por span). Prompt [`ai-service/prompts/enrichment/v1.md`](../ai-service/prompts/enrichment/v1.md); `prompt_version = enrichment/v1`. Las puertas de lote (unicidad de SKU, vocabulario, cobertura de tags por estrato) viven en el auditor, **fuera del HTTP**: el POST de 50 no responde 422 por esas cifras. Compose y el snapshot se quedan en `STUB_MODE=true` hasta que haya `JPV_RAG_LLM_API_KEY`.

**Entregable C10 (mundo).** Receta en [`data/world/pos-profiles.yaml`](../data/world/pos-profiles.yaml) (`generator_version` `c10-world/v1`, semilla `20260823`). CLI `python -m jbg_ai.data world simulate|ingest` en [`ai-service/src/jbg_ai/data/world/`](../ai-service/src/jbg_ai/data/README.md). Ingesta Docker (`:5433` / `joiabagur_pv`): 12 POS, 3 operadores, 6.720 inventario, 22.961 ventas; `"Products"` intacto. Informe: [`Proyecto Final AIEng/informes/c10-synthetic-world-report.md`](Proyecto%20Final%20AIEng/informes/c10-synthetic-world-report.md). JSONL y dump **gitignored**. `is_supply_source` solo en YAML (columna SQL = C19).

**Entregable C11 (biblioteca de indexación).** Paquete [`ai-service/src/jbg_ai/indexing/`](../ai-service/src/jbg_ai/indexing/) — constructor `source-text/v1` (`build_source_text` / `hash_source_text`) y cliente LiteLLM de embeddings 1536d con caché in-memory, *batch* 64 y backoff. **Renderer y embeddings sin HTTP ni SQL.** `jbg_ai.api.main` no importa `indexing`. El dreno de catálogo (`POST /v1/index/sync`) lo entrega C13 en el mismo paquete (el router de índice sí importa). `JPV_EMBEDDING_*` no bloquean `/health` y no caen a `JPV_RAG_LLM_API_KEY`. Tests en [`ai-service/tests/indexing/`](../ai-service/tests/indexing/). Change OpenSpec [`add-source-text-and-embedding-client`](../openspec/changes/archive/2026-08-25-add-source-text-and-embedding-client/).

---

## Épica 13: Familias de Producto y Desambiguación de Variantes

**Descripción:**
Resuelve el caso de negocio crítico: variantes visualmente casi idénticas que provocan errores de venta. La IA propone agrupaciones y el administrador las aprueba, edita o rechaza; la familia resultante es una entidad de negocio editable sin tocar nada de IA.

**Alcance:**
- ✅ Entidades `ProductFamily` y `ProductFamilyMember` en .NET, con pertenencia excluyente garantizada por índice único, etiqueta de variante y orden declarados de forma idempotente, y cinco endpoints de administración (C07)
- ✅ Propuesta asistida de familias y aprobación por lotes: **156 familias y 486 miembros creados** el 2026-08-31 (C18a)
- Pantalla de revisión y aprobación por ítem (segundo caso de intervención humana del PF) — C18b
- Alerta de huérfanos: productos con similitud alta a una familia a la que no pertenecen — C18b
- Pantalla de revisión de perfiles de IA con métricas de calidad — **C28 (hecho)**

**Changes asociados:** C07 (hecho), **C18a (hecho)**, **C18b (hecho, archivado 2026-09-01)**, **C28 (hecho, archivado 2026-09-13)**

**Nota de secuencia.** C07 entrega la entidad y su edición manual, no la inteligencia: agrupar ~350 familias a mano es inviable y por eso existe C18. Lo que C07 hace posible es que haya un sitio donde esas familias vivan y se corrijan, y que `Product` no gane ninguna columna en el proceso. C07 reserva además `Origin`, `ApprovedByUserId` y `ApprovedAt` para que C18 —que no tiene turno de migración de EF Core— pueda registrar la aprobación humana sin abrir uno. **C18a ejerció esa reserva el 2026-08-31**, que hasta entonces no tenía ningún camino de escritura.

**C18 se partió en dos el 2026-08-31**, según la regla 5 del plan: se entrega primero la mitad que desbloquea. **C18a** es el motor y el camino de escritura —lo que hace que `family_id` deje de ser nulo, y con ello que dejen de ser vacuos los tests de familia de C25, C26, C30 y C36—; **C18b** es la pantalla de revisión y la alerta de huérfanos, que necesitan familias ya existentes para tener algo que revisar.

**Entregable C18a.** Motor determinista en [`ai-service/src/jbg_ai/families/`](../ai-service/src/jbg_ai/families/) —raíz normalizada, fusión por material con guarda de raíz degenerada, puerta de `piece_type`, veto **relativo** por embedding que marca y no elimina—, novena ruta del contrato `POST /v1/families/suggest`, y en .NET `POST /api/ai/catalog/family-suggestions` más `/apply`, que persiste vía `ProductFamilyService` para que el feed incremental vea las altas. Reconciliación en **una sola** sincronización: `upserted 486, deleted 32, failed 0`. Informe: [`informes/c18a-family-suggestion-report.md`](Proyecto%20Final%20AIEng/informes/c18a-family-suggestion-report.md).

- [HU-AIENG-007: Entidad de familia de producto y edición manual](Historias/AI-Eng/HU-AIENG-007.md) *(C07 — hecho)*
- [HU-AIENG-018a: Propuesta asistida de familias y aprobación por lotes](Historias/AI-Eng/HU-AIENG-018a.md) *(C18a — hecho; 156 familias / 486 miembros; `Origin = AiApproved`; 32 entradas que no son joyería retiradas del índice con `ReviewStatus = Rejected`, nunca con `IsActive`; cola de revisión de 15 miembros en 5 familias)*
- [HU-AIENG-018b: Revisión humana de familias, alerta de huérfanos y veredicto persistente](Historias/AI-Eng/HU-AIENG-018b.md) *(C18b — hecho, 2026-09-01; **la cola de 15 miembros de C18a ya no existía** y el change se reformuló de «pintar una cola» a «auditar lo que hay»: aquella cola vivía en una respuesta de `suggest` que nunca se persistió, y sus productos ya pertenecen a familias. `POST /v1/families/audit` —**décima ruta** del contrato congelado— recomputa sobre las familias persistidas, reutilizando el veto relativo con otro universo, y en la misma llamada nomina huérfanos: son la misma comparación leída desde los dos lados de la pertenencia. **Nominación por margen relativo, nunca por umbral absoluto** — medido, la pureza de vecindario dispara sobre los casi-duplicados sintéticos y el margen sobre huecos reales del catálogo; la pureza queda como señal de orden. Entidad nueva `FamilyReviewVerdict` sobre el par `(producto, familia)` —**séptima migración del plan, más dos que la propia revisión obligó a añadir**— que es a la vez el registro de descarte y el sello de aprobación por ítem que la aprobación por lotes no podía dar. Listado paginado y disolución de familias en `ProductFamiliesController`. Pantalla de administración en [`/admin/family-review`](../frontend/src/pages/admin/family-review.tsx) con **tres estados por lista** puestos en el tipo (`AuditOutcome`) y no en el render: una auditoría que no se pudo calcular **nunca** se pinta como catálogo limpio. Revisión real ejecutada: **58 juicios, 17 de 18 pertenencias confirmadas y 6 de 40 candidatos aceptados**, 7 aplicados al catálogo. Sinónimo `dorado` → `baño de oro` en el vocabulario de enriquecimiento. Informe en [c18b-family-review-report.md](Proyecto%20Final%20AIEng/informes/c18b-family-review-report.md))*

---

## Épica 14: Búsqueda Semántica Híbrida

**Descripción:**
El corazón del Proyecto Final. Búsqueda que combina la rama vectorial y la léxica, filtra por punto de venta, entiende restricciones estructurales de la consulta y se abstiene cuando no hay confianza suficiente.

**Alcance:**
- Indexación del catálogo en el esquema `ai` mediante feed paginado con cursor `since` y *tombstones*
- **C12 (hecho, archivado 2026-08-26):** `GET /api/ai/index-feed/catalog` (página 50) y `GET /api/ai/index-feed/pos-availability` (página 200), autenticados **solo** con header `X-Index-Feed-Key` (`IndexFeed:ApiKey`, ≥ 32 caracteres). Un JWT de usuario o un token C03 responden **401**. **Sin migración EF** y **sin HTTP push** hacia Python. Spec viva `index-feed`. Runbook AutoBulk: [`informes/c12-catalog-autobulk-runbook.md`](Proyecto%20Final%20AIEng/informes/c12-catalog-autobulk-runbook.md).
- **C13 (hecho, archivado 2026-08-26):** `jbg-ai` tira del feed de catálogo (`POST /v1/index/sync`, CLI `python -m jbg_ai.indexing sync`). Mapa de procedencia commiteado en [`ai-service/src/jbg_ai/indexing/sku_provenance.json`](../ai-service/src/jbg_ai/indexing/sku_provenance.json). OpenAPI con keyset `since_id` / `cursor_id`. **Sin POS** y **sin editar** `indexing/embeddings.py`. Auth de catálogo (`get_catalog_principal`, sin `pos_id`). `drift_count` compara el SHA-256 del conjunto de `product_id` con **un** GET de la primera página del feed (`aggregateHash`).
- **C14 (hecho, archivado 2026-08-27):** retriever vectorial de `POST /v1/retrieval/products` cuando `STUB_MODE=false`. Paquete [`ai-service/src/jbg_ai/retrieval/`](../ai-service/src/jbg_ai/retrieval/): embebe la query con `LiteLlmEmbeddingClient` (`max_attempts=1`, **sin editar** `indexing/embeddings.py`), busca con `<=>` cosine sobre HNSW, umbral de distancia `JPV_RETRIEVAL_DISTANCE_THRESHOLD` default **0,65**, overfetch **después** del umbral. `mode=hybrid` y `lexical` ejecutan la rama vectorial hasta C21 (`debug.notes` incluye `vector_only_until_c21`). Índice vacío / sin `JPV_EMBEDDING_API_KEY` / sin `DATABASE_URL` → **503**; abstención real → 200 + `low_confidence`. **Sin** `ai.query_log`, **sin** regenerar OpenAPI, **sin** filtrar por `pos_id`. Historia [HU-AIENG-014](Historias/AI-Eng/HU-AIENG-014.md).
- **C15 (hecho, 2026-08-28):** `POST /api/ai/search` en [`AiSearchController`](../backend/src/JoiabagurPV.API/Controllers/AiSearchController.cs). Pide la **ventana máxima del contrato en una sola llamada** (`top_k = 20` → 60 candidatos) y **no repide**: el retriever aplica su umbral antes del `LIMIT`, así que repedir devolvería las mismas filas cobrando un segundo embedding. **Hidratación autoritativa** en una consulta conjunta: descarta lo que no tiene inventario activo en ese POS o cuyo producto está inactivo, **conserva la cantidad cero** marcándola, y devuelve la cantidad **de ese POS**. Buscador degradado propio con `to_tsvector('spanish', …)` calculado en consulta —**sin índice y sin migración**—, semántica OR y orden por `ts_rank`. Flag por POS en configuración (`AiSearch:EnabledPointOfSaleIds`, `IOptionsMonitor`) y **`SearchOrigin.Disabled = 3`**. Caché de candidatos con el POS en la clave y rate limit por usuario. Punto de venta **obligatorio**; el admin puede elegir cualquiera **activo**. Historia [HU-AIENG-015](Historias/AI-Eng/HU-AIENG-015.md).
- **C16 (hecho, 2026-08-29):** panel «Buscar con ayuda» en [`/sales/new/assisted`](../frontend/src/pages/sales/assisted.tsx), tercera tarjeta del hub de ventas y entrega al flujo manual por estado de navegación (patrón de `scan.tsx`). **Envío explícito** de la consulta con consultas de ejemplo — nunca `debounce`: la clave de la caché de candidatos incluye la cadena completa, así que ningún prefijo acierta y cada pulsación intermedia facturaría un embedding contra el límite de 30 peticiones por minuto y usuario. Filtros de material (multi-selección) y tipo de pieza sobre el vocabulario cerrado replicado en [`materials-vocabulary.ts`](../frontend/src/lib/materials-vocabulary.ts) con test de fijación; **no disparan búsqueda por sí solos**. Resultados **en el orden recibido**, con insignia de origen y chips de materiales en lugar del `matchReasons` crudo (que es la constante `["vector"]` hasta C21), y talla sólo cuando `variantLabel` exista (lo puebla C18). **Cuatro estados sin resultados** —abstención, sin surtido, degradado o desactivado, y cuota agotada (`429`, que la spec de C15 exige no confundir con indisponibilidad)— más el aviso de **página corta**. Embudo colapsado sólo para administradores. **Tramo .NET sin migración:** `SearchEventId` opcional en `CreateSaleRequest` y `BulkSaleLineRequest`, asignado tras comprobar **existencia y propiedad** del evento; un identificador desconocido o ajeno degrada la atribución a nula y **nunca hace fallar la venta**. Cierra el requisito de atribución de `ai-search-telemetry`, que estaba archivado como cumplido y no tenía camino por el que cumplirse. Historia [HU-AIENG-016](Historias/AI-Eng/HU-AIENG-016.md).
  - **Anotado el 2026-09-24, al explorar C40:** este panel **es el fichero que C40 amplía**, y la comprobación en demo de C36 destapó que llevaba **todo el proyecto sirviendo por su ruta degradada** —`AiSearch:EnabledByDefault` ausente de todos los `appsettings`— y que **en esa ruta los filtros de material y tipo de pieza se descartaban en silencio**, porque `SearchLexicalAsync` no tiene parámetro de filtros y `BuildFilters()` sólo alimenta la ruta asistida. Los chips seguían pulsados. C40 los aplica también ahí —`PieceType` al 97,7 %, un `JOIN` y dos `AND`— y añade un **badge de disponibilidad de cuatro estados visible antes de buscar**, porque `aiAvailable` sólo llega *dentro* de la respuesta. Las cuatro reglas que este panel fijó —envío explícito, orden recibido, vacíos distinguibles y etiqueta neutra para un valor desconocido— **se conservan enteras** y gobiernan los dieciséis estados de M1. C40 es de **EP15**, aunque modifique la capability `assisted-search-panel` de esta épica.
- **C20 (hecho, archivado 2026-09-01):** diccionario de sinónimos **de consulta** para la rama léxica de C21. Dos capas: [`enrichment/vocabularies.yaml`](../ai-service/src/jbg_ai/enrichment/vocabularies.yaml) aporta las clases base y **no se modifica** —tocarlo obliga a `enrichment/v2` y a reenriquecer—, y [`retrieval/query_synonyms.yaml`](../ai-service/src/jbg_ai/retrieval/query_synonyms.yaml) añade lo que no debe entrar en el contrato de extracción: **artefactos del stemmer español** (`collar`/`collares` da 140 documentos frente a 1; `baño`/`bano` da 38 frente a 0, porque pliega tildes agudas pero no la `ñ`), variantes del oficio que la base no tiene, y un puente **direccional** entre vocabularios. `expand_query` es **función pura** y devuelve **grupos de equivalencia más los términos resueltos**, nunca una cadena reescrita: medido, una sola `tsquery` ensanchada saca del top-10 los tres productos llamados literalmente «Sortija». Flag `JPV_QUERY_EXPANSION_ENABLED` con default en `Settings` y **valor por parámetro** del orquestador, para que C24 barra configuraciones sin reiniciar. **Observe-only**: log `stage=expand` y la expansión **no se consume** hasta C21, lo que se declara en vez de disimularse. Sin migración, sin tocar `openapi.json`, sin reindexar. Historia [HU-AIENG-020](Historias/AI-Eng/HU-AIENG-020.md).
- **C21 (hecho, archivado 2026-09-02):** búsqueda híbrida — enciende por fin la columna `tsv` que C05 dejó generada, indexada y **sin consumidor**, y consume los grupos de equivalencia que C20 dejaba calculados y sin leer. **Fusión RRF de tres listas**: la tecleada, la expandida y la vectorial. La exploración midió contra los 1.168 documentos vivos y el proveedor real, y **refutó cuatro cosas escritas antes**: (1) la conjunción estricta entre grupos deja **7 de las 10 consultas reales** del operador en cero documentos, y el *zero-drop* rescata sólo una — se adopta **OR entre grupos con ordenación por coordinación**, que contiene al AND y lo pone en cabeza; (2) `@>` sobre materiales alcanza **60 documentos frente a 913** de `&&`, y 126 documentos no tienen materiales extraídos, así que los filtros deducidos del texto **degradan y nunca excluyen** —*lo que un humano pulsó, filtra; lo que una regla dedujo, degrada*—; (3) la paridad de peso entre ramas es la **peor** de las fusiones (96/120 frente a 105/120 con peso vectorial 0,33), porque la rama vectorial **no abstiene** y bajo RRF vota siempre; (4) el realce de SKU y nombre exacto **no compra nada** — un nombre exacto ya encabeza las dos listas léxicas y ante un SKU la rama vectorial devuelve cero candidatos; (5) dar **profundidades desiguales** a las listas (200 léxica frente a 60 vectorial) cuesta **6-8 puntos de 120**, porque con `k=60` el documento de la posición 200 conserva el 38 % del voto del primero y esa cola larga desplaza al consenso — regla adoptada, **`profundidad ≈ k`, simétrica en 60**; (6) los campos **subjetivos están cubiertos al 11-19 %** (`Ocasiones:` 150 de 1.168, `boda` casa **5** documentos), así que la coordinación los convertía en dictadores: cinco piezas etiquetadas adelantaban a 1.163 igual de válidas — **la coordinación pasa a contar sólo los campos cuya ausencia es evidencia**, con la consecuencia elegante de que una consulta subjetiva queda en manos de la rama vectorial **sin un segundo peso que calibrar**. Y un supuesto de C14 que cae: el **umbral de 0,65 no filtra nada** —deja pasar 1.168 de 1.168 en consultas ordinarias y sólo abstiene ante texto sin sentido—, así que el corte real de la rama vectorial es el `LIMIT` y su recalibración por cuantil queda anotada para C25. Además: `match_reasons` deja de ser la constante `["vector"]`, `mode` deja de mentir, si cae el proveedor de embeddings se sirve la rama léxica **y se dice en pantalla**, `low_confidence` pasa a significar desacuerdo entre ramas **sólo cuando corrieron dos** —con una sola rama ningún candidato puede aparecer dos veces, así que la regla marcaría todas las respuestas y el campo no informaría de nada, y allí conserva el significado de C14: no se devolvió nada—, y se paga la deuda del **singleton del cliente de embeddings** con caché **acotado** —el `dict` sin cota de C11 es inofensivo por petición y una fuga de por vida como singleton—. Sin migración, sin tocar `openapi.json`, sin tocar `backend/`. Historia [HU-AIENG-021](Historias/AI-Eng/HU-AIENG-021.md), mediciones en [c21-hybrid-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c21-hybrid-exploration-measurements.md).
- **C22 (hecho, archivado 2026-09-05):** prefiltro blando por punto de venta. Enciende `ai.pos_projection`, que C05 creó y nadie escribió nunca, tirando del feed `GET /api/ai/index-feed/pos-availability` que C12 dejó servido y C13 tenía prohibido consumir — CLI `python -m jbg_ai.indexing sync-pos`, checkpoint propio (`feed = 'pos-availability'`) y **una revisión de Alembic aditiva** (`ai.pos_projection.computed_as_of`) que el change abrió **contra su propia ficha**: el instante de referencia que su alcance exige no tenía dónde persistirse y, con drenaje incremental, la proyección acabaría con filas contadas contra dos relojes distintos e indistinguibles. La exploración midió y **reencuadró cuatro puntos de la ficha**: (1) el problema de la página corta no era de FORNELLS sino de **ocho de los once puntos de venta** —al menos 6 de cada 20 búsquedas por debajo de una página de 10, peor caso **un solo producto**, y una consulta de MAO-AIR con **cero** supervivientes—; (2) el filtro duro correcto es **`is_assigned_hint`** replicando `Carried()` de .NET, porque excluir lo que la autoridad ya excluye no cuesta nada y los desasignados son el **7-9 %** en los POS con operador — lo que de verdad se degrada sin eliminar es el **stock**, y ahí la señal es gruesa (**MAO-AIR tiene el 34,4 % de su surtido a cero**); (3) el **índice HNSW no se ha usado nunca** en la ruta viva —el planificador elige escaneo exacto desde C14: 8-11 ms frente a **113,7 ms** forzándolo, que además devuelve **40 de las 60 filas pedidas** por `ef_search = 40`—, así que escopar con CTE más distancia exacta no cambia de motor y encima acelera (7,3 ms); (4) el tombstone `unassigned` se aplica como **borrado suave**, porque `IsAssignedHint` viaja hoy hardcodeado a `true` y sin ello el campo sería inalcanzable y C26 no podría distinguir «nunca lo llevaste» de «lo dejaste de llevar». `projection_age_seconds` **gobierna comportamiento** —proyección vacía → 503, vieja → se desactiva el filtro duro y se declara— y sale del checkpoint y **nunca** de `max(refreshed_at)`, porque con un feed incremental ese campo mide cuándo cambió la asignación y no cuándo se miró. Incluye además el **reloj inyectado** (`IndexFeed:SalesAsOf = 2026-08-23T23:59:59Z`): el mundo de C10 termina el 2026-08-23 y, contra el reloj de pared, `sales_30d` cae del **16,28 %** de pares no nulos a **cero el 26 de septiembre** — C25 calibraría sobre una señal muerta y concluiría que la rotación no aporta. Y no es un parche: C24 exige `test_run_is_reproducible_for_same_config_and_seed` y el §16 pide ablations reproducibles, así que un ranking que lee `now()` ya era irreproducible por diseño. Historia [HU-AIENG-022](Historias/AI-Eng/HU-AIENG-022.md), mediciones en [c22-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c22-exploration-measurements.md) y [c22-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c22-implementation-measurements.md). Al archivarse **nace la capacidad viva `pos-projection`**.
- Recuperación vectorial sobre HNSW y léxica con `ts_rank` en español, fusionadas con RRF
- Diccionario de sinónimos del dominio aplicado en expansión de consulta, nunca en indexación
- Prefiltro blando: el surtido del punto de venta acota, y la disponibilidad penaliza el score pero **nunca excluye** un candidato (**C22**)
- Frescura de esa proyección **con dueño ejecutable**: drenaje al arrancar el servicio y cada 600 s, con lock, y su edad dicha en la tarjeta de estado del administrador (**C41**)
- Sobre-recuperación (`top_k × 3`, tope 60) para que .NET tenga margen tras hidratar
- Abstención por umbral: devolver cero resultados es información válida
- Endpoint de búsqueda en .NET con hidratación, circuit breaker y fallback léxico
- Panel de búsqueda asistida en el frontend

**Changes asociados:** C12 (hecho), C13 (hecho), C14 (hecho), C15 (hecho), C16 (hecho), C20 (hecho), C21 (hecho), **C22 (hecho)**, **C25** (`recalibrate-ranking-and-abstention` — **hecho**, abierto el 2026-09-11 y archivado el 2026-09-12; renombrado desde `add-business-signals-ranking`), **C25bis** (`clean-plain-fusion` — **implementado el 2026-09-12**, 45/45, pendiente de archivar), **C41** (`add-pos-projection-scheduled-drain` — **archivado el 26 sep**, no previsto en ninguna ola: nace de las pruebas manuales posteriores al cierre de C40)

> **Ampliado el 2026-09-26 — C41, y la épica se reabre.** **C41**
> (`add-pos-projection-scheduled-drain`) se enriquece con historia
> ([HU-AIENG-041](Historias/AI-Eng/HU-AIENG-041.md)) y ticket
> ([T-AIENG-041](../openspec/changes/archive/2026-09-26-add-pos-projection-scheduled-drain/ticket.md)). **Entra en EP14 y
> no en EP15**, que es lo que su ticket declaraba: la capability que modifica es `pos-projection`,
> nacida en C22, y el criterio del repositorio ya se aplicó al revés con C40 —*«C40 es de EP15, aunque
> modifique la capability `assisted-search-panel` de esta épica»*—. La épica la fija **de qué trata el
> change**, no qué capability toca.
>
> **El problema: la frescura de `ai.pos_projection` no tiene dueño ejecutable.** El *checkpoint* del
> feed `pos-availability` venía del **5 de septiembre** contra un techo de 3.600 s, y hubo que drenarlo
> a mano. **Y es la tercera vez, con dos modos de fallo distintos**: C34 encontró la proyección
> **vacía** en la demo —`count_scope = 0`, **503 en toda recuperación**, con .NET degradando a léxico
> con 200, *«así que desde fuera el entorno parece sano»*—, y C40 y C41 la encontraron **rancia** a 19,7
> y 20 días. **No es una fuga**: la frontera es `Carried()` en .NET y ningún operario ve una pieza que
> su tienda no lleva. Lo que causa es que **la página llegue corta**, que es la avería que C22 midió —
> ocho de once tiendas por debajo de una página en seis de cada veinte búsquedas, peor caso **un solo
> producto**.
>
> **La exploración del 26 sep reencuadra el ticket seis veces, y dos de ellas cambian el alcance.**
> **(1) El planificador ya existe y vive en prosa:** `ai-service/README.md:330` lleva desde C22 una
> receta de cron cada diez minutos que **es inejecutable en la topología que desplegamos**, porque
> empieza por `cd /srv/jbg-ai` y `jbg-ai` es un contenedor. Por eso nadie la instaló. **(2) El drenaje
> se queda en `jbg-ai` y no pasa a un `BackgroundService` de .NET:** lo que el ticket pedía no es un
> planificador sino **una segunda implementación del protocolo del keyset**, y como la spec obliga a
> conservar el CLI quedarían **dos drenadores escribiendo la misma fila de checkpoint** — la corrupción
> de la que el propio ticket avisa. Además .NET tendría que escribir `ai.*`, frontera que
> `bootstrap.sql` hace **estructural por *grants***. **(3) El disparo que importa es el de arranque**,
> no el del intervalo: los tres incidentes ocurrieron *levantando un entorno para probar*, y un cron de
> host no corre en el portátil de nadie. **(4) La edad se dice en `GET /health` y no en
> `GET /api/ai/search/availability`**, porque esa ruta tiene un `MUST` de spec viva que le prohíbe
> llamar al servicio de IA y su método es síncrono, mientras el informe de salud es *mapping* abierto en
> los dos lados y llega a la tarjeta de administrador que C17 ya construyó: **coste de contrato cero**.
> **(5) El lock va dentro del drenaje y no en el planificador**, o el CLI corrido a mano —que es como
> se arregló las tres veces— queda fuera. **(6) La edad es del drenaje y es global**, no de la tienda:
> el checkpoint es una fila por feed.
>
> **Y un hallazgo que obliga a anotar un informe publicado.** La manipulación declarada en el §8 de C40
> —*«se actualizaron `refreshed_at` y `computed_as_of` en 1.176 filas»*— **se aplicó a la columna
> equivocada**: el guard lee `ai.sync_checkpoint.last_incremental_sync_at`. Cuatro pruebas lo cierran:
> los dos campos del checkpoint son **idénticos** (2026-09-25 20:49:24 UTC), luego el único drenaje fue
> el de C41; el artefacto del grupo 8 está fechado **15 h 07 min antes**; quedan **94 filas** con la
> huella del `UPDATE` (`computed_as_of = 2026-09-25 05:32:04`, diez minutos antes de medir); y «1.176»
> es el **total exacto de filas del POS `0388f003…`**. **El reparto de los dieciséis estados describe el
> sistema degradado**; la latencia (p50 3.404 / p95 7.160) **se sostiene**, porque sin ámbito el SQL es
> 2-3 ms más lento contra un p95 dominado por dos llamadas a proveedor y .NET **no repide** cuando la
> página llega corta. **Se anota, no se rehace** (el arnés del grupo 8 nunca se commiteó). Y el remate:
> `degraded_reason` es **`null` las 42 veces** del artefacto, porque .NET no tiene campo para la
> degradación de la proyección — *un dato que el sistema conoce, paga y descarta en la frontera*.
>
> **Alcance acordado:** drenaje al arrancar (completo sin checkpoint, incremental con él) y cada
> **600 s** —derivado de `techo / intervalo ≥ 4`, que tolera cinco fallos seguidos—, con
> `pg_try_advisory_lock` no bloqueante; sección `projection` en `GET /health` → tarjeta de
> administrador; y un **quinto motivo de fallo en `verify.sh`** que caza la proyección vacía y cierra la
> deuda de C34 en `DEFERRED_TASKS.md`. **Se corta el botón manual, también el del administrador**: el
> argumento que mata el del operario —*«con el tramo 1 hecho, no tiene caso de uso»*— vale igual para
> él. **Sin ruta nueva bajo `/v1`, sin regenerar `openapi.json`, sin migración y sin tocar `Carried()`.**

> **Actualizado el 2026-09-12, al implementar C25bis.** El borrado **no movió nada, y está demostrado**: dos corridas del arnés sobre el mismo golden set y la misma huella de índice dan **315 filas por consulta idénticas** en las cinco configuraciones supervivientes, listas de resultados incluidas, y el único elemento de la procedencia que difiere es la revisión del código. Suite **994 → 997 con cero fallos** a los dos lados. **Tres puntos de su ficha se refutaron por comprobación**: los pesos por lista sí tenían lector vivo —se retiran por ser trampas que la spec prohíbe mover, no por estar muertos—, la variante adaptativa perdedora no existía porque C25 ya la había retirado, y el fallo al arranque no era alcanzable con `extra="ignore"` y tenía más radio de daño que el defecto que prevenía, así que la obligación se acotó a la configuración de evaluación, donde ya estaba implementada: **cero código nuevo**. El principio que queda escrito es *una perilla es algo que se puede poner; un registro es algo que se escribe* — por eso `Provenance.fusion_mode` sobrevive al selector y `judgements.jsonl` conserva `v2-hibrido` en `pooled_in` mientras `POOLED` lo pierde. La fila de referencia queda **histórica y citable** con tres artefactos —informe, JSONL y su propia configuración, movida a `evals/configs/retired/`— y **por qué se retiró sigue demostrable sin ser activable**, como aritmética pura sobre `fuse()`.

- **C25bis (implementado el 2026-09-12, creado el 11):** limpieza del andamio de C25, y **fuera de la numeración C principal** por el mismo motivo que `FIX1`: no sale de la descomposición original del proyecto sino de una consecuencia de C25. Aquél **conserva la fusión plana como modo seleccionable** porque sin ella la fila `v2-hibrido` de la tabla de ablations deja de ser reproducible y el change pierde la referencia contra la que se leen todas las demás filas. Publicada la tabla y congelada la configuración, ese modo pasa a ser lo contrario de lo que era: **un camino muerto, activable por error, cuya aritmética el proyecto midió como defectuosa** — los 60 documentos léxicos ganando al mejor candidato vectorial en toda consulta, y el grado 2 cayendo a la posición 33. Retira además la variante de ponderación adaptativa que pierda el barrido de C25 y las perillas que queden sin lector, con un **inventario comprobado por búsqueda y no por memoria**, porque este subsistema ya sorprendió cuatro veces con cables calculados y sin consumidor (`tsv`, la expansión, `qty_bucket` y `coordination`) y aquí el riesgo es el simétrico: retirar algo que sí tenía lector. **Acepta un coste y lo declara:** la fila de la línea base deja de poder re-medirse y pasa a ser **histórica y citable** —su informe y su JSONL por consulta quedan versionados—, porque la alternativa era mantener vivo un camino medido como roto, y un camino muerto que se puede activar por error es cómo un defecto corregido regresa. **No re-mide nada y no tiene autoridad para mover una cifra:** su criterio de verificación es que las filas supervivientes den cifras **idénticas** tras el borrado, y cualquier diferencia es un fallo del change que se revierte, no un resultado que discutir. Sin migración, sin contrato y sin diff fuera de `ai-service/`. Change [`clean-plain-fusion`](../openspec/changes/archive/2026-09-12-clean-plain-fusion/).

- **C25 (hecho, abierto el 2026-09-11 y archivado el 2026-09-12):** recalibración del ranking y de la abstención. La exploración encontró un **defecto que vale más que todo el alcance original de la ficha: la fusión vigente no fusiona, concatena.** Con `w_typed 0,50 + w_expanded 0,50 = 1,00` votos frente a `w_vector = 0,33`, un documento léxico en el **rango 60** —el peor puesto posible— puntúa 0,008333 y el mejor documento que sólo vio la rama vectorial puntúa 0,005410: **los 60 documentos léxicos ganan al #1 vectorial, en toda consulta, siempre.** Verificado en el run publicado de C24: el grado 2 que la vectorial pone en el #1 cae en la **posición 33** en tres consultas distintas, los 32 anteriores son **sólo léxicos** y la cola conserva **exactamente** el orden vectorial. Y hay un segundo sesgo que nadie había visto: `typed` y `expanded` se truncan por separado, así que la rama léxica puede meter **120 documentos** frente a los 60 de la vectorial — **el doble de huecos y el triple de voto**. La corrección es **fusión en dos etapas con pesos por rama**: las dos listas léxicas se fusionan entre sí y el resultado se fusiona con la vectorial, de modo que el voto total de la rama es exactamente `w_lex` **sin depender de cuántas de sus listas dispararon** (hoy el umbral de cruce es 0,469 o 0,938 según si el AND de `websearch` casó, una propiedad de la consulta que nadie declaró). Medido con `fuse()` real: **sólo importa el cociente `ρ = w_vec / w_lex`**, así que el barrido es de una dimensión, y la **banda útil es `ρ ∈ [0,9 ; 1,1]`** —a 0,95 el #1 vectorial entra en el top-5, a 0,90 cae al 8— donde la rejilla de C24 tenía **un solo punto**: por eso su óptimo parecía un filo de cuchillo. Más una **regla adaptativa `w_lex × cobertura` con cero parámetros**, que consume el `coordination` que hoy se calcula, viaja en el *hit* y **el orquestador no lee nunca** —cuarto cable pelado, tras `tsv`, la expansión y `qty_bucket`—; su punto crítico es el denominador, porque las palabras vacías **cuentan como grupo** (`['de']`, `['una']`, `['y']`) con `tsquery` vacía, y con el denominador ingenuo la regla **recortaría un tercio del peso léxico en `sortija de plata`, que puntúa nDCG 1,000**, destruyendo justo las categorías que existe para no tocar. **Y el juez de C24 es ciego a lo que este change añade:** `criterion.md` no menciona stock ni rotación, así que un barrido que maximice nDCG@5 converge a **peso 0** en todas las señales — se resuelve con una **métrica derivada sin re-etiquetar** (`g_efectivo = máx(grado−1, 0)` si `qty_bucket = '0'`, que no inventa una constante sino que **reutiliza la escala**: el grado 1 ya es *«sustituto plausible que el operador ofrecería como segunda opción»*) y la relevancia pura como **guardarraíl**. Además: la señal de POS se separa del alcance (`LEFT JOIN` que lee frente a `INNER JOIN` que restringe), porque hoy el golden set corre sin POS y **la penalización de disponibilidad de C22 no se disparó ni una vez** en las 192 filas del run; la rotación entra como **desempate declarado y no calibrado**, porque no hay instrumento que la pueda aprobar —la rúbrica no premia rotar, la vía online tiene **31 filas**, y la señal es no nula en el 23,54 % de los pares—; y la abstención se diseña **después** de medir `min(distancia)` **por consulta**, que es la cantidad que decide y que **no existe en ningún artefacto** (C24 midió el solape **por documento**, que es otra pregunta). **Dos puntos de la ficha quedan refutados por medición:** la penalización de variante ambigua —sólo 2 de 156 familias pueden llenar cinco huecos, el panel ya pinta `Talla {variantLabel}`, `variante-talla` ya es la mejor categoría y diversificar **baja** el nDCG@5, así que la agrupación es presentación y pertenece a C30/C36— y la calibración de `1-2` frente a `3+`, que **no tiene función objetivo posible** porque ninguno de los dos pierde grado. Y la **regla de decisión heredada se reformula con argumento y fecha antes de re-medir**: **6 de 8** consultas de ajuste están en el techo del nDCG@5 y **las 8** en el de Recall@5, P@3 y MRR, y **7 de 8 salen de la lista curada de C20/C21** — la condición *«mismo signo en las tres lecturas»* veta subir el peso vectorial con las consultas elegidas para que la léxica ganase, y una partición que C24 declaró **contaminada** (0,942 en ajuste contra 0,535 en nuevas) es evidencia de sobreajuste del titular, **no un grupo de control**. **Al aplicar, la medición confirmó lo grande y refutó tres cosas más.** La fusión por rama vale **+0,083** sobre la línea base en la lectura que decide, y el modelo reprodujo la **posición 33** exacta en las tres consultas. La regla adaptativa por cobertura aporta **+0,128** en `descripcion-sin-anclaje` y **cero exacto** en las otras siete categorías —la predicción falsable de su diseño, confirmada contra el índice vivo— y hace algo que ninguna cifra agregada deja ver: convierte la elección del cociente de rama de **acantilado en meseta**, con el recorrido del barrido cayendo de **0,070 a 0,007**; sin ella, elegir mal `ρ` cuesta siete centésimas. La señal de disponibilidad retira el **91 %** de las piezas agotadas del top-5 y es quirúrgica: sólo mueve 13 de las 48 consultas. **Y se retiran tres puntos, no dos.** La **rotación sale del orden**, refutada durante el apply: como el desempate estricto que su propio requisito describía decidía **cero** pares del top-5, y como clave de ordenación no desempataba sino que **particionaba** —11.067 pares invertidos, sólo el 3,4 % adyacentes y el 71,2 % a más de diez puestos— con coste medido en las dos lecturas; `sales_30d` se sigue leyendo para diagnóstico y **no ordena nada**, con la prohibición devuelta a estructural. Se retira también la **variante binaria** de la regla adaptativa, indistinguible de la continua en los 16 puntos del barrido, y con ella el último número que parecía ajustado: **C25 no deja ni un peso calibrado** — `ρ = 1,0` es de principio y ahora además medido como robusto, y el de disponibilidad decide su **signo y no su valor**, porque con un término binario el orden es invariante a la magnitud. **La abstención resultó no caber en un escalar:** el mejor acierto de las contestables llega a 0,7118 y el de las imposibles arranca en 0,4469, o sea **contención total** y no solape parcial, confirmada después sobre **20** consultas y no cinco; la regla adoptada es **relativa por consulta** y lee la **forma** del perfil —una consulta imposible es *plana*— subiendo la abstención de 0,050 a **0,150 sin silenciar ni una contestable**. **Tres listones no se alcanzan y se declaran en vez de cerrarse:** `Recall@5` **0,758** contra 0,85, abstención **0,150** contra 0,80, y `v3` no bate a `v2b` por el margen —**+0,030** operativo— aunque cumple su propia regla de adopción, porque el golden set es **estructuralmente ciego** a la disponibilidad y lo que falta es resolución y no evidencia. La categoría `fuera-de-dominio` pasa de **5 a 20** consultas, con el equilibrio de material **medido y declarado**: nombrar «de plata» acerca la consulta 0,12 al catálogo y la hace parecer contestable, así que un conjunto construido todo de una forma mediría el metal y no la ausencia. Sin migración, sin tocar `openapi.json`, sin reindexar y sin diff en `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`, verificado contra el punto de nacimiento de la rama. Historia [HU-AIENG-025](Historias/AI-Eng/HU-AIENG-025.md), ticket [T-AIENG-025](../openspec/changes/archive/2026-09-12-recalibrate-ranking-and-abstention/ticket.md), decisiones en [c25-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c25-exploration-measurements.md) y [c25-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c25-implementation-measurements.md), tabla en [c25-baselines-2026-09-11.md](../ai-service/evals/results/c25-baselines-2026-09-11.md).

**User Stories:**
- [HU-AIENG-012: Feeds HTTP de indexación con cursor, tombstones y autenticación de servicio](Historias/AI-Eng/HU-AIENG-012.md) *(C12 — `GET /api/ai/index-feed/catalog` y `.../pos-availability`; API Key `X-Index-Feed-Key`; sin migración / sin push)*
- [HU-AIENG-013: Indexador de `ai.product_document` desde el feed de catálogo](Historias/AI-Eng/HU-AIENG-013.md) *(C13 — pull del feed de catálogo; mapa SKU en `src/jbg_ai/indexing/sku_provenance.json`; OpenAPI keyset; sin POS / sin `embeddings.py`)*
- [HU-AIENG-014: Recuperación vectorial real en `POST /v1/retrieval/products`](Historias/AI-Eng/HU-AIENG-014.md) *(C14 — retriever vectorial; umbral 0,65; hybrid=vector hasta C21; sin `query_log` / sin OpenAPI / sin `embeddings.py`)*
- [HU-AIENG-015: Endpoint de búsqueda asistida en .NET con hidratación autoritativa](Historias/AI-Eng/HU-AIENG-015.md) *(C15 — `POST /api/ai/search`; ventana máxima en una llamada sin repetición; hidratación por POS que conserva el stock cero; buscador degradado con full-text español sin índice; flag en configuración con `SearchOrigin.Disabled`; caché de candidatos y rate limit; sin migración)*
- [HU-AIENG-016: Panel «Buscar con ayuda» del operador, con atribución de la venta a la búsqueda](Historias/AI-Eng/HU-AIENG-016.md) *(C16 — panel en `/sales/new/assisted`; envío explícito sin `debounce`; filtros sobre vocabulario cerrado; cuatro estados sin resultados incluida la cuota agotada; página corta declarada; embudo sólo para admin; atribución de la venta a la búsqueda, sin migración)*
- [HU-AIENG-020: Diccionario de sinónimos de consulta para la rama léxica](Historias/AI-Eng/HU-AIENG-020.md) *(C20 — base `vocabularies.yaml` sin modificar más overlay de consulta; artefactos del stemmer como contenido de primera clase; grupos de equivalencia en vez de cadena reescrita; puente direccional; flag en la firma del orquestador; observe-only con informe de alcance medido; sin migración y sin OpenAPI)*
- [HU-AIENG-021: Búsqueda híbrida — rama léxica, fusión RRF de tres listas y filtros estructurales que degradan](Historias/AI-Eng/HU-AIENG-021.md) *(C21 — **implementado**; OR con ordenación por coordinación en vez de conjunción estricta; fusión RRF de lista tecleada, expandida y vectorial con pesos configurables y rama vectorial a menor peso; filtros deducidos del texto que degradan y nunca excluyen; `@>` y realce de exacto descartados con medición; degradación honesta a léxico cuando cae el proveedor; `low_confidence` como desacuerdo entre ramas; singleton del cliente de embeddings con caché acotado; sin migración, sin OpenAPI y sin tocar `backend/`)*
- [HU-AIENG-022: Prefiltro blando por punto de venta — la proyección pondera, el surtido acota y el reloj deja de derivar](Historias/AI-Eng/HU-AIENG-022.md) *(C22 — **hecho**, archivado 2026-09-05; sincronización de `ai.pos_projection` desde el feed de disponibilidad con CLI y checkpoint propio; tombstone `unassigned` como borrado suave; filtro duro sobre `is_assigned_hint` replicando `Carried()`; CTE de alcance más KNN exacto en las tres ramas, porque HNSW nunca se usó y forzarlo trunca a 40 de 60; `qty_bucket = '0'` degrada y nunca elimina; `projection_age_seconds` desde el checkpoint —nunca desde `refreshed_at`— gobernando 503 sobre proyección vacía y degradación declarada sobre proyección vieja; reloj inyectado `IndexFeed:SalesAsOf`; flag de ablación para C24; **una revisión de Alembic aditiva** (`computed_as_of`) abierta contra su propia ficha, `openapi.json` regenerado y **tres deltas MODIFIED** sobre specs vivas, más la capacidad nueva `pos-projection`)*
- [HU-AIENG-025: Recalibrar el ranking y la abstención — que la fusión fusione, que el stock pese y que el buscador sepa callar](Historias/AI-Eng/HU-AIENG-025.md) *(C25 — **hecho**, archivado el 2026-09-12; fusión en **dos etapas** con pesos por rama, que corrige el defecto por el que los 60 documentos léxicos ganaban al #1 vectorial **siempre** y lo dejaban en la posición 33; el barrido pasa a **una dimensión** porque sólo importa el cociente `ρ = w_vec / w_lex`, con banda útil `[0,9 ; 1,1]` que la rejilla de C24 sólo tocaba en un punto; regla adaptativa `w_lex × cobertura` **sin parámetros**, consumiendo el `coordination` que se calculaba y se tiraba, con el denominador corregido para excluir los grupos de `tsquery` vacía; **métrica `nDCG@5 operativo`** derivada de los juicios existentes **sin re-etiquetar**, con la relevancia pura como guardarraíl, porque la rúbrica de C24 no menciona stock y un barrido sobre ella converge a peso 0; señal de POS por `LEFT JOIN` **separada** del alcance por `INNER JOIN`, para medir la reordenación sin pagar el coste de recall del prefiltro; rotación como **desempate declarado y no calibrado**; abstención diseñada **después** de medir `min(distancia)` por consulta y con `fuera-de-dominio` ampliada de 5 a 15-20; barrido en fases `capture`/`rescore` que hace el de señales **exacto y sin proveedor**; tabla de **seis filas** con `v2b-fusion` aislando la fusión de las señales y la fusión plana **conservada** como modo para que `v2-hibrido` siga reproduciendo la línea base; **dos puntos de la ficha refutados por medición** —penalización de variante ambigua y calibración de `1-2`/`3+`—; dos capacidades nuevas (`business-signals-ranking`, `retrieval-abstention`) y tres deltas `MODIFIED`; **sin migración, sin OpenAPI y sin tocar `backend/`, `frontend/` ni `terraform/`**)*
- [HU-AIENG-041: La frescura de `ai.pos_projection` deja de ser un acto manual — drenaje al arrancar y por horario, con lock, y la edad dicha en la tarjeta del administrador](Historias/AI-Eng/HU-AIENG-041.md) *(C41 — **archivado el 26 sep**, abierto el 25 y enriquecido el 26; tarea de `lifespan` en `jbg-ai` que reutiliza `sync_pos_availability` **sin reescribirlo**, con drenaje de arranque —completo sin checkpoint, incremental con él— e intervalo de **600 s** derivado de `techo / intervalo ≥ 4`; `pg_try_advisory_lock` **no bloqueante y dentro del drenaje**, para que cubra también al CLI corrido a mano; la tarea **no bloquea el arranque**, porque el `HEALTHCHECK` sondea `/health` con 3 s y `depends_on: service_healthy` tumbaría el despliegue; sección `projection` en `GET /health` —edad desde el **checkpoint** y nunca desde `refreshed_at`, `stale` contra el techo, páginas fallidas y puntos de venta sin ámbito— transportada por `AiHealthResponse` hasta la tarjeta de C17; quinto motivo de fallo en `verify.sh` que caza la proyección vacía y cierra la deuda de C34; **quince decisiones cerradas y las seis preguntas del ticket respondidas**; **sin insignia de operario, sin botón manual —tampoco para el administrador—, sin ruta bajo `/v1`, sin regenerar `openapi.json`, sin migración y sin tocar `Carried()`**; deroga con refutación numérica el `MUST NOT start an in-process scheduler` de `pos-projection`)*

---

## Épica 15: Venta Asistida, Sustitutos y Agentes

**Descripción:**
Capa de generación y agéntica. Convierte un conjunto de candidatos en una respuesta útil para el operador: agrupada por familia, con avisos calculados por reglas, argumentario con citas y sugerencias de sustitutos o complementarios.

**Alcance:**
- Respuesta estructurada con `groups[]` por familia y `variant_label` destacado. **Tres modos** *(13 sep)*: argumentario de una pieza, pregunta sobre una pieza, y pregunta libre sin pieza — de los tres, los dos primeros llegan a pantalla con C36 y el tercero servía al bucle del agente y al arnés. **Los tres llegan al operario con C40** *(24 sep)*, que convierte el panel de búsqueda de C16 en la superficie del tercero en vez de construir una pantalla nueva: el panel ya hacía la mitad —misma recuperación, mismo selector de tienda, misma hidratación, mismo episodio por visita— y M1 es ese panel más el enrutador, el corpus y la prosa. **`family_id` es nulable**, porque el ~58 % del catálogo no pertenece a ninguna familia
- Avisos calculados por reglas, nunca generados libremente, y **como códigos de vocabulario cerrado** cuyo castellano escribe el frontend. **Repartidos por autoridad sobre el dato** *(13 sep)*: los estructurales —existen variantes, falta talla— los calcula el servicio de IA desde el índice; los de **stock** —stock crítico, miembros sin stock— los calcula **.NET tras hidratar**, porque en Python sólo hay un *bucket* de disponibilidad que nunca sale al cable y puede desfasarse minutos
- Argumentario generado en tiempo de consulta con `citations[]`, no persistido —y **no persistido incluye no logueado**, con la única excepción del arnés de evaluación *(13 sep)*. **Lo que se cita lo construye C23 en EP12**: sin corpus de conocimiento indexado no hay `citations[]`, sólo prosa. C30 lo consume en proceso como la tool `consultar_conocimiento` del agente de venta, sin ruta HTTP de por medio, y **debe propagar el `claim_scope` de cada fragmento**: un compromiso de la joyería no se presenta como un hecho comprobable. **Y `citations[]` son las que el argumentario usó, no las que devolvió el recuperador** *(13 sep)*: emitir todo lo recuperado no es atribuir, es decorar, y hace imposible comprobar que ninguna cita apunta al vacío. **Matizado el 14 sep, al explorar C30b:** comprobar que el identificador **resuelve** no basta para sostener esa regla — un modelo que devuelva los cinco identificadores entregados la pasa de forma perfecta y trivial sin haber usado ninguno. Lo que la sostiene es que el modelo declare, por cita, **el tramo de su propio argumentario** que esa cita respalda, y que el código verifique que ese tramo está literalmente en el texto que escribió
- **Toda cifra de precio o stock se emite como placeholder** que resuelve .NET; si alguno queda sin resolver, ~~la respuesta se rechaza~~ **se retira el argumentario y no la respuesta** *(precisado el 21 sep, al explorar C34: es la misma política que ya aplican las puertas de C30b, y los grupos, avisos y citas siguen siendo correctos)*. **Y el placeholder se resuelve contra la pieza anclada**, porque no dice de qué pieza habla: por eso sólo los dos modos anclados llegan a pantalla. **Y el flanco simétrico también se cierra** *(13 sep)*: un argumentario que escriba «39,90 €» literal no deja placeholder alguno y pasaría ese rechazo, así que el servicio de IA admite **sólo cifras presentes en el material que se le entregó** —tallas, milímetros, `925`, dígitos de SKU—, en ejecución y no sólo en evaluación
- Guardrails, enrutado de intención y pregunta de aclaración ante consultas ambiguas. Hasta que llegue el enrutador, la capa de generación **no redacta cuando el catálogo no puede contestar** — es una red, no un clasificador, y la diferencia se declara. **Precisado el 14 sep, al explorar C31: son DOS puertas y no una**, porque «fuera de dominio» significa dos cosas distintas — *«esto no es una pregunta de joyería»*, clasificable sin recuperar, y *«esto es joyería y **este** catálogo no lo tiene»*, que es cobertura y no intención. Las 20 consultas de la categoría `fuera-de-dominio` del golden set son todas de la segunda clase, así que se cubren las dos y se publican **dos cifras que nunca se suman**: la abstención del retriever de C25, que no se mueve, y el rechazo del enrutador
- Agente asistente de venta con *tools* de solo lectura e intervención humana. **Partido el 20 sep** en dos mitades: **C32a** entrega las seis tools y el registro, con el invariante de solo-lectura comprobado **por introspección** y no por una bandera que cualquiera puede poner a falso; **C32b**, el bucle, **seis presupuestos duros** —iteraciones, llamadas a tool, llamadas al proveedor, tokens, contexto en caracteres y **reloj de pared**—, `partial: true`, la traza y la ruta propia `POST /v1/assist/agent`, con la transcripción multi-turno viajando en la petición y el servicio **sin guardar nada**. De las seis tools, **cuatro son envoltorios de código ya probado** —recuperación, sustitutos, roster de familia y corpus—, y la única que no tenía servicio detrás es `consultar_disponibilidad`
- **El agente llega al operario** *(26 sep, C42)*: ruta propia `/sales/new/agent`, cuarta tarjeta en el hub y un **hilo de conversación donde cada turno es dueño de su bloque de respuesta**, con los grupos rotulados por procedencia —lo que se pedía frente a lo que se ofrece en su lugar—, la **traza de llamadas visible** y los diez motivos de parada traducidos. Hasta C42, `POST /v1/assist/agent` estaba entregado y medido desde C32b y **no lo llamaba nadie**: de los cinco pilares del PF, el de agentes era el único sin superficie. **El agente no se sirve por defecto** —ruta propia y demostración de ablación— porque su única cifra comparativa dice ×3,0 de coste y 13,1 % de retirada del argumentario contra el 2,2 % de la ruta determinista
- Sustitutos por falta de stock. ~~Complementarios por reglas y co-ocurrencia~~ — **cortado el 2026-09-12 con medición** (ver abajo)
- Tarjeta de asistencia y desambiguación por familia en el frontend, **con caja de pregunta sobre la pieza elegida** *(13 sep)* — es la superficie por la que el corpus de EP12 llega por fin al joyero

**Changes asociados:** **C26** (`add-substitutes-retrieval` — **archivado el 2026-09-12**, 62/62), ~~C27~~ (**cortado**), **C30a**, **C30b**, **C31** *(archivado el 16 sep)*, **C32a** *(archivado el 20 sep)*, **C32b** *(archivado el 21 sep)* *(partidos el 20 sep)*, **C34** *(archivado el 22 sep)*, **C36** *(archivado el 24 sep)*, **C40** (`add-frontend-free-query-panel` — **archivado el 25 sep**, no previsto en ninguna ola: nace al comprobar C36 en demo), **C40_FIX** (`c40-fix-all-shops-scope-unreachable` — **archivado el 26 sep**, fuera de la numeración C: corrige a C40), **C42** (`add-frontend-agent-panel` — **abierto el 26 sep**, no previsto en ninguna ola: nace al valorar la cola pendiente del PF)

> **Ampliado el 2026-09-26 — C42, y el motivo es que un pilar no se puede enseñar.** **C42** (`add-frontend-agent-panel`) se abre con historia ([HU-AIENG-042](Historias/AI-Eng/HU-AIENG-042.md)), ticket ([T-AIENG-042](../openspec/changes/archive/2026-09-27-add-frontend-agent-panel/ticket.md)) y **dos informes de exploración del mismo día** ([v1, contra el código](Proyecto%20Final%20AIEng/informes/c42-exploration-decisions.md) · [v2, contra los artefactos ya escritos](Proyecto%20Final%20AIEng/informes/c42-exploration-decisions-v2.md)), en la rama `c42-add-frontend-agent-panel`. **No estaba en el plan**: sale de una sesión abierta para decidir entre implementar C38 entero o dar superficie al agente, y gana el segundo por lo que el §5 de la convocatoria escribe —*«el sistema debe poder probarse»*—. Recuento: **40 archivadas** —entra C41— y **3 pendientes**: **C42**, C38 y C39, en ese orden. **Va antes de C38** por la misma cadena de prompts que puso a C40 antes que a C38: aquí la tarea del agente sube de versión, así que unas cifras de generación tomadas antes describirían un prompt sustituido.

> **Actualizado el 2026-09-27 — C42 archivado, C38 retirado entero, y C39 partido en tres.** Tres
> movimientos en un día y ninguno estaba previsto en ninguna ola.
>
> **C38 se retira** (`add-generation-and-agent-evals`) y no se recorta: se cae del todo, por valor
> marginal y sobre mediciones tomadas en su propia sesión de exploración. Sus datos ya existían —los 20
> escenarios del agente están corridos **dos veces contra el proveedor real** y sus filas traen
> veredicto, con **17 de 20** cumpliendo su expectativa y **2 de 20** de ruido entre pasadas—, su
> validador resultó ser **un espejo** de la regla que la puerta numérica de Python ya aplica al mismo
> texto, y sólo los adversarios arrancaban de verdad en cero. Es la primera vez que cae un elemento de
> la lista de *«nunca se recortan»* del plan, y queda escrito allí con su motivo.
>
> **C39 se parte**, primero en **C39a** (`redeploy-and-audit-demo-environment`) y **C39b**
> (`finalize-pf-readme-and-evidence`), y al implementar el primero en **C39a** y **C39a-bis**
> (`verify-demo-redeployment`). La segunda partición es de orden y no de tamaño: las tareas de
> verificación de C39a exigían un entorno desplegado, y **el despliegue ocurre al mergear el change a la
> rama `demo`** — un change que sólo se puede archivar después de archivarse no es un change. C39a-bis
> toca sólo ficheros que el `paths-ignore` del despliegue ignora, así que **verificar no cuesta un
> redespliegue**.
>
> **C39a se archiva el mismo día**, con historia ([HU-AIENG-043](Historias/AI-Eng/HU-AIENG-043.md)),
> ticket ([T-AIENG-043](../openspec/changes/archive/2026-09-27-redeploy-and-audit-demo-environment/ticket.md))
> e [informe](Proyecto%20Final%20AIEng/informes/c39a-implementation-measurements.md). Su hallazgo de
> partida: **la rama `demo` llevaba cinco semanas 84 commits por detrás**, parada en el QA de C34, con el
> `IMAGE_TAG` desplegado igual al HEAD de esa rama — así que la demo no tenía C36, C40, C40_FIX, C41 ni
> C42, o sea cuatro de las cinco superficies más visibles del entregable.
>
> **C39a-bis se archiva el mismo día**, con su
> [informe](Proyecto%20Final%20AIEng/informes/c39a-bis-implementation-measurements.md). Confirma que el
> despliegue ocurrió de verdad —`IMAGE_TAG` de `sha-d6a740fa…` a `sha-2b357a1e…`, idéntico al HEAD de
> `demo`— y que el entorno está sano, y **su hallazgo es que la ejecución figura en rojo por un falso
> positivo**: la quinta condición de `verify.sh` cuenta puntos de venta sin surtido **sin preguntar si la
> tienda está activa**, y `HT-ARTRUTX` está cerrada a propósito desde C10. El arreglo no cabe donde
> parecía —el rol del servicio de IA no puede leer la tabla de puntos de venta de .NET—, así que queda
> diferido con sus tres vías.
>
> Y de paso destapa que **las cuentas del recorrido no existían**: el entorno tenía dos, no cuatro, y los
> tres operarios sintéticos sólo vivían en el mundo local, de modo que la abstención, los sustitutos y el
> pivote **no se podían demostrar**. Quedan en cuatro cuentas —un administrador y un operario por tienda—
> declaradas en el §5.8 del *runbook*, que es el requisito que la delta añade a `demo-deployment`.
>
> Recuento: **43 archivadas** —entran C42, C39a y C39a-bis—, **1 retirada** (C38) y **1 pendiente**:
> **C39b**.
>
> **Actualizado el 2026-09-27 — entra C43, y nace de lo que C39a-bis encontró al mirar.** **C43**
> (`add-shop-activity-projection`) no estaba en el plan: sale del hallazgo principal de C39a-bis,
> que el despliegue `36322635852` **falló con el entorno sano** y por una sola causa. La quinta
> condición de `verify.sh` contaba puntos de venta sin surtido **sin preguntar si la tienda está
> activa**, así que `HT-ARTRUTX` —cerrada a propósito desde el mundo sintético de C10, y la única
> de las doce— se leía como una tienda rota. El falso positivo no se quedaba en el registro:
> llegaba en rojo a la tarjeta del administrador.
>
> **Y el arreglo no cabía donde parecía**, que es lo que lo convierte en un change y no en un
> parche: el rol `jbg_ai` recibe `permission denied for table PointOfSales`, de modo que la
> decisión D9 / Q-5 de C41 —contar contra lo que aparece en la proyección— **estaba impuesta por
> los permisos**. C43 lleva la actividad al esquema `ai` por un *feed* propio,
> `GET /api/ai/index-feed/pos-shops`, retrato completo sin cursor drenado a `ai.pos_shop`; una
> columna en `ai.pos_projection` habría nacido rancia para siempre, porque el *feed* de
> disponibilidad es incremental por *keyset* sobre el *watermark* de inventario y un cambio de
> estado de tienda no mueve ninguna fila. Entra en **EP14** por lo mismo que C41: modifica
> `pos-projection`.
>
> Cierra **dos** de las cuatro fichas diferidas de C39a-bis —el falso positivo y la rancidez que el
> despliegue registraba ya curada— y deja abiertas las otras dos a propósito: la purga de
> `ai.sync_failure`, cuya mitad barata sí hace (el informe ya publica los fallos **por *feed***, y
> las 66 filas de `catalog` dejan de ser inalcanzables), y la alerta `CRITICAL` de reconocimiento
> de imagen, que es del MVP y se declara en el guion de la demo en C39b.
>
> Recuento: **44 archivadas** —entra C43—, **1 retirada** (C38) y **1 pendiente**: **C39b**.
>
> **Actualizado el 2026-09-27 — entra C39b y la cola queda vacía; el Proyecto Final está cerrado.** **C39b**
> (`finalize-pf-readme-and-evidence`) es el último change, y **no toca una línea de código de producto**:
> entrega el README del máster en sus secciones editables, el **informe de cierre**
> ([c39b-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c39b-implementation-measurements.md))
> y la **guía del revisor** ([guia-del-revisor.md](Proyecto%20Final%20AIEng/guia-del-revisor.md)), que sustituye al guion del vídeo.
> Entra en **EP17**, que con él pasa a **completa**.
>
> **Lo primero que arregla es una cifra que nadie podía comprobar**, y es la razón por la que la nota de
> recuento de esta misma página tenía que decir «sumándole `C40_FIX`» para cuadrar: **ese change no tenía
> fila en la tabla maestra del plan** y aparecía sólo en prosa. C39b **le añade la fila** y publica el
> criterio de recuento con sus **dos unidades declaradas** —directorios de archivo y fichas del plan—,
> medido contra el disco. La distancia entre las dos queda con **un solo nombre**:
> `fix-boot-drain-retries-both-drains`, el seguimiento de C43, un directorio sin ficha.
>
> **Y cuenta seis changes nacidos de comprobaciones manuales y de ninguna ola**, no cuatro: entran **C43** y
> el **seguimiento del drenaje de arranque**. El episodio de C43 es el mejor ejemplo del proyecto de una
> condición de verificación ganándose el sueldo — arregló un falso positivo, **introdujo un fallo verdadero**
> y lo cazó el despliegue siguiente **porque se había obligado a fallar con la tabla vacía** en vez de pasar
> en vacío.
>
> **Cierra las tres tareas que sobrevivían a C38** sin gastar cuota del proveedor: el éxito de tarea del
> agente **definido antes de mirar cifras** y publicado con `--rescore` como **17 de 20 con los tres fallos
> nombrados** —y nunca como tasa porcentual, porque el ruido entre pasadas se reprodujo en **2 de 20**—, y
> el **validador .NET** como limitación declarada con **cifra esperada cero**. **Declara y no arregla** la
> alerta `CRITICAL` de reconocimiento de imagen —funcionalidad del MVP, 0 fotos de 1.200 productos—, el
> pivote del agente inalcanzable por nombre, y la **deriva de rama**, que estrena entrada diferida y hoy
> mide cero. **Ninguna sección congelada del README se edita**: lo desfasado va al anexo A del informe con
> su texto propuesto, incluido un salto de nDCG del `### 1.2` que **mezcla dos conjuntos dorados**.
>
> **Ocho hallazgos y dieciséis decisiones, y la segunda pasada refuta a la primera con cifras del propio repositorio.** El v1 encontró una **regresión latente que C40 introdujo sin tocar el agente** —la tarea del agente vive en `assist/v4`, cuyo *Sistema* ordena escribir `{{price}}` y `{{stock}}` **siempre**; su payload es un `FreeQueryPayload` con `is_anchored = False`; y C40 metió `placeholder_in_free_query` en `HARD_VIOLATION_CAUSES`— y concluyó que sin arreglarlo C42 entregaría *«un panel de agente sin prosa»*. **El v2 lo desmiente**: la frase que ordena marcadores es **idéntica palabra por palabra** en `v3.md:47` y `v4.md:59`, así que **C40 ya midió este caso** sobre 90 consultas libres con payload sin anclar — **3 de 90 generaciones con marcador y 0 retiradas tras la reparación única**, que además *«no es una por comprobación»* sino una sola con la lista entera de violaciones. La referencia que el v1 usó —C30b, `{{price}}` en 147 de 213— es de los modos **anclados**, y la cabecera de `assist/v5.md` ya había escrito por qué no se traslada: *«anclado hay una pieza y se la vende; en libre hay hasta quince agrupadas y lo que se pide es comparar»*. **El arreglo entra igual pero no gobierna la línea de corte: la gobierna el consumidor .NET, que no existe** —`IAiGatewayClient` tiene siete métodos y ninguno es el del agente, que es el 100 % y no el 3 %—. Y **la causa que de verdad retira el argumentario del agente ya estaba medida y no es el marcador**: `dangling_citation`, 85 en el primer intento y 72 supervivientes, con el **92,2 % de las respuestas trayendo cero citas**.
>
> **Cuatro decisiones nuevas, cerradas antes de los artefactos.** **`assist/v6` sólo para el agente, conservando `v5` intacto** —`v5` no contiene la tarea del agente y su cabecera declara que cada versión tiene cifras medidas contra ella, así que editarlo haría mentir su fila justo cuando C38 va a medirlo; el riesgo de la opción, la deriva entre los dos *Sistema*, se cierra con un test de identidad—. **`fallo_proveedor` como métrica y no como entrada del circuito**, cerrando **por refutación** la entrada que `DEFERRED_TASKS.md` arrastraba desde C32b: con ~13.000 tokens por petición contra un techo de 25.000 TPM el sistema admite **una petición por minuto**, y un cortafuegos con `MinimumThroughput` no se abre nunca a ese ritmo porque la ventana de muestreo expira antes de acumular la muestra — quien avisa a la pantalla es la sonda, y el *pipeline* de `ai-assist` ya declaraba que un 200 degradado *«is not a failure»*. **El turno del asistente lleva el argumentario íntegro**, con línea sintética cuando se retiró, y eso fija la profundidad real de la conversación en **6 intercambios y no 12**, porque `_within_the_total_cap` suma **todos** los turnos y el argumentario mide p50 386 caracteres: un contador que sólo contase lo que el operario escribió llegaría a «turno 9/12» con el 422 ya disparado. **Y una sola pasada de medición**, con la línea base prestada de C40 y declarada.
>
> **El hallazgo de C41 tiene una segunda vida en el arnés del agente, y ahí es peor.** Donde en C40 hubo una columna equivocada, aquí **no hay ninguna comprobación y los dos caminos leen cosas distintas**: `scope_buckets` es un `SELECT` crudo declarado *«read by the evaluation only»* y el camino de servicio usa `projection_synced_at()`, así que **el arnés resuelve fixtures perfectos por rancia que esté la proyección mientras el camino que mide sirve sin ámbito**. La pasada de C32b duró **2 h 44 min** contra un techo de **1 h**, sin drenaje automático disponible entonces —es de C41, cinco días posterior—, así que **a lo sumo las primeras ~74 de 204 filas corrieron con el prefiltro aplicado**, y no se puede limpiar a posteriori porque la procedencia no registra antigüedad. **El pivote sobrevive** —`consultar_disponibilidad` lee `availability_bucket` directamente, sin pasar por el guard, con la regla *«degrade, never remove»*—, y con él la justificación de que el ámbito por defecto sea la tienda del operario. De ahí nace un **tramo 0 de instrumentos** que va antes de cualquier tarea funcional: contador de marcadores, antigüedad de la proyección por fila, y la precondición de tener el contenedor arriba con el drenaje de C41 encendido. **C41 deja de ser un arreglo previo y pasa a ser prerrequisito habilitante.**
>
> **Lo que la pantalla tiene que pintar, ordenado por frecuencia medida y no por la maqueta:** **una de cada cinco respuestas no tiene ni una fila** (19,6 %, idéntico en los dos arms, y de las 20 por arm **14 son repregunta o rechazo** — sólo 6 de 102 son «busqué y no encontré nada»), las **citas están vacías en el 92,2 %** y los **avisos en el 96,1 %**, y la cinta de `partial` sirve al **2,0 %** en el arm servido — frente al 58,8 % de `gpt-4o-mini`, que quema el presupuesto de herramientas **56 veces contra 2** y queda confirmado como inservible para esta ruta. El **pivote es rutina y no anécdota**: `buscar_sustitutos` se invocó **125 veces**, y eso es lo que pone el `origin` de los grupos por delante del arreglo del prompt dentro del tramo 1. **Fuera de alcance declarado:** *streaming*/SSE, preguntar por el stock de una tienda concreta —ninguna tool acepta punto de venta y habilitarlo es un cambio de modelo de autorización, no una tool más—, el desglose de `usage` por etapa, la telemetría de la ficha, el registro de la consulta de ámbito global, los escenarios puntuados del agente (son de C38) y recalibrar el presupuesto de herramientas, aunque se mida que **el efectivo es 6 y no 8** porque con 4 llamadas concurrentes el bucle para cuando la siguiente tanda cruzaría el tope.
>
> **Ampliado el 2026-09-26 — C40_FIX, y lo que corrige no es un defecto de implementación sino una spec viva que miente.** **C40_FIX** (`c40-fix-all-shops-scope-unreachable` — **archivado el 26 sep**, 38/38) se abre con historia ([HU-AIENG-040-FIX](Historias/AI-Eng/HU-AIENG-040-FIX.md)) y ticket ([T-AIENG-040-FIX](../openspec/changes/archive/2026-09-26-c40-fix-all-shops-scope-unreachable/ticket.md)), en la rama `c40-fix-all-shops-scope-unreachable`. Va **fuera de la numeración C** por el mismo motivo que `FIX1` y `C25bis`: no sale de la descomposición original, sino de una consecuencia de otro change. Recuento: **39 archivadas** —entran C40 y C40_FIX— y **2 pendientes**: C38 y C39.
>
> **El defecto: C40 construyó el ámbito «todas las tiendas» entero y nadie puede alcanzarlo.** Tercera clase de `AiCallScope` sin centinela, tercer perfil de *claims* en `deps.py`, autorización abierta a operarios y administradores con sus dos tests, DTO anulables, hidratación agrupada por producto y fila con sus tres estados — **y el selector del panel no ofrece la opción**, el efecto de carga fija la primera tienda activa, la búsqueda no se dispara sin tienda y el botón *Buscar* está deshabilitado. El grupo 12 de C40 **no se ejecuta en la aplicación real ni una vez**.
>
> **Y no falló nada, que es el hallazgo de verdad.** Los 136 escenarios de C40 salieron verdes y su verificación independiente pasó por encima, porque los tres escenarios del panel están condicionados con *«WHEN the search is scoped to every point of sale»*: describen qué hace la pantalla **estando** en ese estado y **ninguno exige que ofrezca la forma de entrar en él**. Peor: `assisted-search-panel/spec.md:88` afirma hoy *«The panel SHALL send a concrete point of sale on every search»*, que **dejó de ser cierto con C40**. La spec viva no calla — **contradice lo que el sistema hace**, y `openspec validate --all --strict` seguiría en verde sobre ella porque valida **estructura y no verdad**. Es la versión peor de las tres specs malformadas de agosto: aquéllas rompían el formato y el validador las cazó; ésta está bien formada y miente. **Y es la tercera aparición del mismo modo de fallo** en esta familia: el barrido de completitud de C40 emparejaba por nombre y se le escapó un campo sin lector; su verificación arregló aquello y cometió la variante —auditar **el estado** sin comprobar su **alcanzabilidad**—. Los tres son lo mismo: *verificar la pieza en aislamiento en vez del camino hasta ella*.
>
> **La exploración del 26 sep refuta el ticket dos veces, y la segunda dimensiona el change.** El ticket declaraba *«no toca el backend»*, se corrigió a *«dos piezas»* — y son **tres**: **la ruta rápida rechaza el ámbito global**. El panel tiene dos rutas, `route` arranca en `'semantic'` porque *«el valor por defecto es la barata»*, y el ámbito global sólo se construyó para la generativa: `AssistedSearchRequest.PointOfSaleId` es `Guid` y su validador lleva `.NotEmpty()`, mientras `FreeQuerySearchRequest.PointOfSaleId` es `Guid?`. Añadir sólo el `SelectItem` haría que el primer *Buscar* pintara **«La búsqueda asistida requiere un punto de venta»** debajo del control que lo acaba de ofrecer. **Tres hallazgos más:** `GetAvailability` **no vive en `FreeQuerySearchService`** sino en `AssistedSearchService`, y consulta **tres** interruptores, así que no son «tres líneas en el controlador»; **`AiFreeQuerySearch__EnabledByDefault` no está puesto en ningún sitio del repositorio** —`compose.demo.yaml` pone los otros dos y no el tercero, así que en la demo el toggle asistido está apagado en todas partes, exactamente el fallo que el comentario de ese fichero describe tres líneas más arriba—; y **`SearchLexicalAsync` tiene una mina dormida**: acepta `Guid?` pero **no agrupa por producto** como sí hace `HydrateAsync`, y `BuildResultsAsync` hace `ToDictionary(ProductId)` incondicionalmente, así que la rama nula es un **HTTP 500** esperando un llamante. Y un **tercer `SHALL` falso** en la misma spec: la línea 41 dice que cambiar de tienda limpia resultados y la 596 que refresca las existencias; el código limpia, y el test de C40 sólo comprobó la segunda cláusula del escenario.
>
> **La decisión que ordena el change: el control es sólo del administrador, y por una razón de producto, no de coste.** El ámbito global **no informa existencias** —cantidad nula, sin tienda que nombrar, ficha deshabilitada, sin telemetría—, así que responde *«esta pieza existe en el catálogo»* y **no** *«está en la tienda del Puerto»*. El dependiente que pregunta «¿lo tenemos en otra tienda?» no obtiene respuesta a esa pregunta ni con el ámbito abierto a él: obtiene un callejón sin salida. Limitarlo al administrador no declina servir un caso de uso — **declina ofrecer una herramienta que no responde la pregunta que su nombre sugiere**, y deja el change que sí la responde —desagregar existencias por tienda— nombrado en vez de prometido con la copia. Consecuencias: el selector **ya se renderiza siempre** para ese rol, así que el requisito *«A single assignment needs no choice»* no se toca y **cero tests existentes se invierten**; **la ruta del backend se queda abierta a operarios** y el requisito lo dice explícitamente, para que nadie la endurezca por simetría; y el ámbito global **fija la ruta generativa**, con la rápida deshabilitada **con motivo de ámbito** —«trabaja sobre una tienda concreta»— y nunca con el del interruptor, que sería falso. Eso deja `AssistedSearchService` intacto y la mina de la rama léxica dormida, anotada como tarea diferida con su motivo.
>
> **Dos reglas que el change no puede violar.** **El centinela del `Select` no sale al cable:** se traduce a **ausencia** antes de la petición, porque la propiedad que hace seguro este ámbito es que la ausencia hace que el prefiltro **no se aplique**, no que case con todo — un `Guid.Empty` viajando sería el comodín por accidente al que C40 dedicó un grupo entero. Y **la sonda tiene que calcular el mismo predicado que la ruta aplica**, o se recrea la avería original de C40: por eso el predicado se **extrae** en vez de escribirse tres veces, y por eso sin tienda resuelve a `EnabledByDefault` —la lectura estrecha, ya razonada en el código: *«un despliegue que habilita la función tienda a tienda no la ha habilitado para “todas ellas”»*. La sonda describe **interruptores**; el panel describe **alcanzabilidad**, y el callejón sin salida **se enuncia al llegar** en vez de pre-deshabilitar la opción, que exigiría leer la sonda dos veces.
>
> **Un requisito meta de alcanzabilidad se considera y se descarta.** *«Todo estado especificado DEBE ser alcanzable»* **no produce ningún escenario que un runner pueda fallar** — sería un requisito que valida en verde y no cambia nada, el mismo modo de fallo un nivel más arriba. En su lugar, **tres escenarios fallables** en el requisito concreto: que el administrador tenga el control, que el operario no, y que el ámbito global deshabilite la ruta rápida con su motivo. La lección va a la documentación de verificación, donde vive la definición del barrido de completitud que ya falló dos veces.
>
> **Implementado el 2026-09-26 — 38 de 38 tareas de código, y la puerta que de verdad importa queda pendiente a propósito.** C40_FIX cierra con las dos suites comparadas **por nombres** contra su propia línea base, `dotnet build` en 0 errores, `tsc --noEmit` filtrado limpio y `openspec validate --all --strict` en **63 passed, 0 failed**. Queda pendiente al cerrar la implementación la **comprobación manual en el entorno levantado**, que exige una persona delante de la pantalla — y es la única puerta capaz de cazar esta clase de defecto, porque las tres specs que este change corrige estaban **bien formadas y eran falsas** y el validador pasó sobre ellas en el archivado de C40 sin inmutarse. Un change que nace de una prueba manual no se cierra sin otra. **El desarrollador la ejecutó ese mismo día** con los dos roles, declarando una salvedad —los tres operarios sembrados tienen una sola tienda, así que el selector se oculta por una regla previa y el camino del operario con varias no se ejercitó—, y **la verificación independiente cerró los dos caminos que faltaban** conduciendo el navegador: un operario creado con dos tiendas ve el selector con sus dos tiendas y **sin** la opción global, y con la API arrancada sin el interruptor de la consulta libre se lee el aviso del callejón sin salida en vez de dos opciones muertas.
>
> | Medición | Línea base | Al cierre |
> |---|---|---|
> | Frontend | 113 fallos · 834 tests · 14 de 57 ficheros | 114 · **848** · 15 de 57 |
> | Backend | 45 con error · 1.329 tests | 52 · **1.339** |
> | `assisted.test.tsx` (el área propia) | **verde entero** | **71/71**, con los 14 nuevos |
> | Clases .NET del área propia | 0 fallos | **122/122**, con los 11 nuevos |
>
> **Los 25 tests nuevos son los +10 y los +14 del total**, y el desglose cuadra fila a fila: 8 unitarios .NET —uno es un `[Theory]` de cuatro casos—, 2 de integración y 14 de página.
>
> **El juicio se toma por nombres, y aquí hay una medición que endurece lo que `CLAUDE.md` documenta.** En frontend **un solo nombre** difiere: `family-review.test.tsx :: should create a family with its members from the review screen`, que es **literalmente** el que C36 usó para refutar que aquí el conjunto fuera estable entre corridas; comprobado, **pasa 22/22 al correr su fichero solo** y no tiene ni una importación en común con lo tocado. En backend difieren **once** —nueve aparecen, dos desaparecen—, **diez de ellos en `InventoryIntegrationTests`** y el undécimo en `ProductsControllerTests`, que ya venía con cinco. El salto de recuento (45 → 52) es mayor que el ±1 documentado, así que no se dio por bueno citando el documento: se midió. **Dos pasadas aisladas del mismo binario con `--no-build` dieron 9 y 9 fallos con siete de los nueve nombres distintos**, y los tres que en la primera pasada «seguían rojos en aislamiento» —incluidos dos de autorización de operario— **pasaron en la segunda**. La clase no es «a veces inestable»: es no determinista de una pasada a la siguiente sobre el mismo binario. Y no hay camino causal: **cero referencias** desde cualquier fichero de inventario o productos a los seis que el change modifica.
>
> **Lo que quedó en el código, y las dos decisiones que se tomaron al escribirlo.** El predicado del interruptor se **extrae a un sitio único** (`AiScopeSwitchExtensions`) que consumen la sonda **y** la ruta, de modo que **la regla del nulo** no pueda divergir — divergir es la avería original de C40—, con un `[Theory]` de cuatro combinaciones que pretende comparar el veredicto de una contra el de la otra. *(Corregido el 2026-09-26 por la verificación independiente: **ese `[Theory]` no compara nada**. Calcula el valor esperado con los mismos métodos de extensión que la sonda y **nunca invoca `FreeQuerySearchService`**, así que sobrevive en verde a invertir la rama nula del predicado compartido **y** a reescribir la ruta con otra regla para la ausencia — dos mutaciones, compiladas y ejecutadas. Lo único que fija es la sonda contra `AiScopeSwitchExtensions`, que es un lado. Sustituido por `AiScopePredicateAgreementTests`, que construye las dos piezas sobre las mismas opciones, **ejecuta la ruta** y compara veredictos. **Y el riesgo sigue vivo en una dirección:** la sonda devuelve `freeQuery && salesAssist` y la ruta aplica `freeQuery` a secas, así que con el segundo interruptor apagado la sonda dice `switched_off` de un ámbito que la ruta sirve con prosa —medido por HTTP—, lo que en pantalla deshabilita las dos vías. Es herencia de C40, no de C40_FIX, pero el requisito que C40_FIX escribe lo prohíbe; decisión pendiente en `openspec/DEFERRED_TASKS.md`. **Es la lección de D6 una vuelta más arriba: auditar el test en aislamiento no es auditar lo que el test demuestra.**)* Y la ruta efectiva del panel es **derivada y no estado**: fijarla en el estado dejaría al administrador que sale del ámbito global en la ruta cara sin haberlo pedido, que es justo lo que el requisito del toggle prohíbe. En la capa de copia aparecieron **cinco** cadenas que afirmaban cosas falsas en el ámbito global y no las dos que el ticket preveía —el subtítulo, el título y el cuerpo del vacío de surtido, el vacío de la ruta degradada y la página corta—, todas escritas cuando una tienda era el único ámbito posible.
>
> **Y la delta de spec creció respecto al `proposal.md`**, que enumeraba dos requisitos modificados: al escribirla salieron **dos nuevos y tres corregidos**. El `proposal.md` se puso al día en el mismo acto, porque dejar que los artefactos del change se contradigan entre sí es la misma deriva que el change persigue en las specs vivas. Se descartó `RENAMED` para corregir el título del requisito de ámbito: **no hay un solo precedente en los 71 changes archivados**, y estrenar una vía del validador en la puerta del proyecto es el riesgo que este repositorio ya ha pagado.
>
> **Dos tareas diferidas quedan anotadas como una sola**, con orden obligatorio: extender la ruta rápida al ámbito global **exige antes** agrupar por producto en `SearchLexicalAsync`, cuya rama nula es un **HTTP 500** dormido —`BuildResultsAsync` hace `ToDictionary(ProductId)` incondicionalmente— que se activaría primero en desarrollo local, donde la ruta degradada es la que corre siempre.
>
> **Ampliado el 2026-09-24 — la épica se reabre el mismo día en que se cerró, y no por un cambio de opinión.** **C40** (`add-frontend-free-query-panel`) se abre con historia ([HU-AIENG-040](Historias/AI-Eng/HU-AIENG-040.md)), ticket ([T-AIENG-040](../openspec/changes/archive/2026-09-25-add-frontend-free-query-panel/ticket.md)) y **dos informes de exploración del mismo día** ([decisiones](Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md) · [tabla de estados](Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md)), en la rama `c40-add-frontend-free-query-panel`. **No estaba en ninguna ola**: nace en la tarea 8.5 de C36 —la comprobación en demo— y lo primero que apareció no fue un defecto de C36, sino que **el panel de búsqueda asistida llevaba todo el proyecto sirviendo por su ruta degradada** (`AiSearch:EnabledByDefault` ausente de todos los `appsettings`) y que **en esa ruta los filtros se descartan en silencio**. Los recuentos de archivadas **no se mueven** —siguen 37— y el de pendientes pasa a **3**.
>
> **La lección que ordena el change entero:** los tres tropiezos de aquella sesión son el mismo problema, **una capacidad apagada que la interfaz presenta como encendida**, y dos de los tres avisan mientras el de los filtros no avisa de nada. Por eso los seis tramos de C40 se ordenan por *cuánto engaña hoy la pantalla* y no por cuánto cuestan, y por eso el embudo de observabilidad —lo único que no arregla nada que hoy engañe— va el último.
>
> **Once hallazgos medidos, y el que gobierna la línea de corte sólo aparece leyendo el código.** **.NET rechaza M1 hoy por construcción**: `AiGatewayClient` lanza `ArgumentException` sin `product_id` porque `PitchPlaceholderResolver` retira el argumentario **siempre** que no hay ancla, y `assist/v3` ordena escribir los marcadores de precio y stock **también en las tres tareas de consulta libre** —medido en C30b: `{{price}}` en **147 de 213** y `{{stock}}` en **188 de 213**—. Las 42 consultas del informe se midieron con `curl` **contra Python**, saltándose esa etapa, así que su «37 respuestas con argumentario» no describe lo que el operario vería: **sin el tramo 2 completo, C40 entregaría un panel asistido sin prosa**, que es la misma avería que vino a corregir. De ahí que `assist/v5` —las tareas libres dejan de hablar de precio y disponibilidad— y la causa dura `placeholder_in_free_query` sean **prerrequisitos declarados** y no mejoras. **Tres hallazgos más de esa segunda pasada:** M1 **no tiene la salvaguarda de cobertura que M3 sí tiene**, así que una consulta de conocimiento sin fragmentos ejecuta la tarea que pide apoyarse en fragmentos que no existen —y el caso está medido en el propio informe y leído como otra cosa—; **«todos los puntos de venta» choca con una invariante fijada y con test** (*«exactly two construction paths and no third»*), así que es una **frontera de autorización** y no un desplegable; y hay **dos interruptores independientes** con sus dos límites (30/min contra 10/min) y sus dos presupuestos (2.500 ms contra 10.000 ms), de modo que el badge tiene **cuatro estados** y necesita una ruta de lectura que hoy no existe, porque `aiAvailable` llega *dentro* de la respuesta.
>
> **Y dos contradicciones internas del primer informe, resueltas en el segundo.** **`route=none` no es un estado, son dos** y sólo `intent` los separa: con `in_domain` el clasificador corrió y se contradijo —devolvió veredicto servido con `index` nulo, **5 de 42 · 11,9 %**— y se arregla **coercionando a `both`**, porque el *fail-open* ya recupera las dos ramas y después tira la prosa; con `unclassified` el clasificador **no corrió**, y ahí pedirle al operario que reformule es echarle la culpa de una credencial ausente. Y **D8 estaba demasiado ancho**: los códigos de rechazo se apilan en el mismo `warnings[]` que los avisos de pieza, así que la partición correcta es **por sujeto del aviso** —los de pieza no se pintan en M1, los de consulta sí—, porque aplicada al pie de la letra se comería justo los dos códigos para los que la §15.13 obliga a escribir castellano.
>
> **Tres limitaciones se cierran** —la **§15.12** (la pregunta libre ya es una caja de texto), la **§15.13** (los dos rechazos corteses sí llegan desde M1, y son dos textos distintos) y la **limitación 3 de C34** (una pieza no indexada deja de verse igual que una caída, con `degradedReason`, seis valores que .NET ya calculaba y descartaba)— y **tres se declaran y no se cierran**: el agente sigue sin consumidor, la **telemetría de uso** sale como **change propio** por ser una cuarta zona con migración de EF Core —y sin ella la condición de reactivación de `generate=false` sigue sin ser observable—, y el presupuesto de la ruta asistida **ya está en su techo** de 10 s con suelo validado de 8, contra un p95 de C34 de 7,1 s que no incluía el enrutador.
>
> **Dos cosas que C40 hace y no son de pantalla.** La **abstención pasa a leer una sonda sin filtro**, ejecutada sólo cuando el operario ha filtrado y reutilizando el embedding ya calculado: con filtro estrecho la abstención **no puede dispararse hoy** —`diadema` da 7 candidatos de todo el índice contra un mínimo de 15—, así que el sistema devolvería siete piezas mediocres **y con M1 escribiría un párrafo hablando bien de ellas**. Es M1 quien convierte ese defecto en peligro, y por eso la sonda es de C40 aunque toque `retrieval-abstention`, spec viva con tres consumidores. Y **`SearchOrigin` gana un cuarto valor** sin abrir migración, porque se persiste con `HasConversion<int>()`: con él la comparación de las dos rutas del toggle deja de ser una demostración y pasa a ser **una consulta SQL** sobre la telemetría que existe desde C04 — que es lo que hace medible la ablación del §11.2, porque **un toggle elegido por el usuario no es un A/B test**.
>
> **Implementado el 2026-09-25 — los catorce grupos entran, ninguno se corta, y lo que más valor deja son las refutaciones.** C40 cierra con **67 de 67 tareas** y **cinco cifras medidas**, tres de las cuales contradicen lo que la exploración predijo:
>
> | Medición | Predicho | Medido |
> |---|---|---|
> | Marcadores en el argumentario de M1 | «la mayoría se retirarían», por 147/213 y 188/213 en C30b | **2 de 90** y **1 de 90** en `v3`; **0 y 0** en `v5` — un factor de treinta |
> | Latencia p95 extremo a extremo por .NET | ~2 s por encima de los 7,1 s de C34, al borde del presupuesto | **7 160 ms**, prácticamente igual: **0 de 42** fuera del presupuesto de 10 s |
> | Tasa de `router_index_absent` | **5 de 42 · 11,9 %** (H7) | **0 de 42**, y 0 en 144 réplicas servidas de toda la sesión |
> | Coste de la sonda sin filtro | «un dígito de milisegundos», porque un filtro duro no ahorra tiempo | **20,9 ms** de mediana — y el filtro **sí** ahorra: 21,3 → 9,3 ms |
> | Reparto de los dieciséis estados | — | **9 observados** sobre 71 consultas reales |
>
> **La predicción que gobernaba la línea de corte era falsa, y el corte era correcto igual.** El tramo 2 se declaró prerrequisito porque `assist/v3` llenaba de marcadores el argumentario de M1; medido, casi no lo hacía. Lo que sí bloqueaba M1 al **100 %** era el guard del *gateway*, el tercero de los tres eslabones — así que `assist/v5` sigue siendo necesario y la razón escrita en el ticket no lo era. Corregidos el ticket, el diseño y el propio `v5.md`.
>
> **Tres defectos que sólo aparecieron al implementar**, ninguno previsto: hacer opcional la reclamación `pos_id` habría convertido un valor **en blanco** en «todas las tiendas» —un token de una tienda ampliado calladamente a todas—; el `--rescore` del barrido calculaba la decisión de abstención y la **tiraba**, porque `aggregate` no promedia ese campo; y la copia del argumentario ausente, escrita para la ficha, nombraba «la ficha» y «esta pieza» en un panel que no tiene ninguna de las dos. El tercero lo encontró la **comprobación con datos reales**, no un test.
>
> **Y un fallo de puerta que merece quedar escrito:** `npm run build` estuvo **verde sobre un error de tipos durante un commit entero**, porque Vite transpila con esbuild y esbuild descarta los tipos sin mirarlos. Lo encontró `tsc --noEmit` filtrado, que el `CLAUDE.md` describe como «no es la puerta». Anotado allí: verde en `npm run build` significa «compila», no «los tipos casan».
>
> **Dos huecos declarados en vez de disimulados.** Una consulta libre de **ámbito global no se registra**, porque `ProductSearchEvent.PointOfSaleId` es obligatorio y darle un valor falso está prohibido por la spec: entre una migración de EF Core —lo único que el encargo excluía— y una mentira, se eligió no registrar y escribirlo, con la parte incómoda de que la frecuencia de esas búsquedas no se puede medir *porque* no se registran. Y el test `ForAllPointsOfSale_IsRefusedByInventory` **no tiene dónde afirmarse**: `IAiGatewayClient` no tiene operación de inventario, así que la garantía vive del lado de Python y del lado .NET queda un test que afirma que la superficie no existe, para que falle el día que crezca.
>
> **La tarea diferida de C34 sobre el corpus sigue abierta, y la comprobación la agrava.** Dentro del contenedor hay ocho Markdown en `/app/prompts/knowledge/v1` que **parecen** el corpus y son los encargos de producción; el corpus son **33 documentos** en `data/knowledge/`, que el `Dockerfile` no copia. Y hay algo peor que una línea que falta: `CORPUS_DIR` es `REPO_ROOT / "data" / "knowledge"` y dentro del contenedor `REPO_ROOT` resuelve a `/app/.venv/lib`, porque el paquete vive en `site-packages` — así que **copiar el corpus a `/app/data/knowledge` tampoco lo encontraría**. Que esta máquina tenga 161 fragmentos con vector no lo contradice: se indexó **desde el host**. La comprobación con datos reales y proveedor real da **8 de 8 casos correctos y 0 marcadores**.
>
> **Ampliado el 2026-09-22 — C36 pasa a en curso, y su exploración retira tres filas de copy que la ficha daba por necesarias.** **C36** (`add-frontend-assist-card-and-family-disambiguation`) se abre con historia ([HU-AIENG-036](Historias/AI-Eng/HU-AIENG-036.md)), ticket ([T-AIENG-036](../openspec/changes/archive/2026-09-24-add-frontend-assist-card-and-family-disambiguation/ticket.md)) y decisiones ([c36-exploration-decisions.md](Proyecto%20Final%20AIEng/informes/c36-exploration-decisions.md)), en la rama `c36-add-frontend-assist-card-and-family-disambiguation`. Es **el único change del Proyecto Final que pone la capa RAG delante de una persona**: hasta hoy el argumentario, las citas, el agrupado por familia y los sustitutos sólo se demuestran con `curl` y con el arnés. Los recuentos **no se mueven** —siguen **36 archivadas y 3 pendientes**— porque abrir no es archivar. **Lo que la exploración refuta de la ficha:** el enrutador de intención de C31 corre **sólo en M1** y las dos rutas de C34 son siempre ancladas, así que `clarification_question` es constante `null` y los dos códigos de rechazo (`query_out_of_domain`, `query_not_in_catalogue`) **no pueden llegar al card**; no se les escribe castellano y en su lugar **un test comprueba que caen en la etiqueta neutra**, que es la regla de tolerancia que la ficha sí exigía. El vocabulario visible queda en **cinco códigos**. **Y una decisión que sale de una medición:** `size_label_missing` salta en el **58,3 %** de las fichas y está anticorrelacionado con tener familia —**4,0 %** con ella contra **92,5 %** sin ella—, así que informa del estado del enriquecimiento y no de la pieza: se degrada a **atributo junto al SKU** en vez de competir con los dos avisos de stock, que saltan en el 3,9 % y el 4,3 % y sí pueden costar una venta. El **bloque de familia**, en cambio, sale reforzado: dispara en el **31,2 %** de las fichas y el **98,3 %** de sus 544 grupos trae las etiquetas de variante presentes y distintas, con el **99,6 %** cabiendo en dos a cuatro filas — la sospecha de que enseñara filas indistinguibles **queda refutada**. El card vive en **ruta propia** con tres entradas —fila de búsqueda asistida, página de venta y escaneo—, porque la situación que la ficha nombra, *«el cliente tiene la pieza en la mano»*, no llega por el panel; emite **una petición por visita y sin reintento**, contra un límite de 10 por minuto y usuario y con la caché prohibida; y **no preselecciona ninguna variante**, de modo que el clic es la confirmación. **Dos limitaciones se declaran y no se cierran**: el card no tendrá telemetría, y sus datos baratos —familia, avisos, stock— sólo se obtienen pagando una generación de p95 7,1 s, porque llegan soldados en la misma respuesta.
>
> **Actualizado el 2026-09-22 — C34 verificado y archivado.** Las dos rutas del card existen: **`POST /api/ai/products/{id}/sales-assist`** con la pregunta en el cuerpo y **`GET /api/ai/products/{id}/substitutes`**, las dos con el punto de venta obligatorio, la **pieza comprobada en esa tienda antes de gastar una llamada** (400 · 403 · 404 sin tocar la IA) y **ninguna cifra que el operario lea escrita por un modelo**: precio, cantidad y los dos avisos de stock salen de la hidratación, y `{{price}}`/`{{stock}}` se resuelven contra la pieza anclada —«39,90 €» y el entero—. Un marcador sin resolver **retira el argumentario y no la respuesta**, con **seis estados** de `pitchStatus` que C36 tiene que pintar distintos; los sustitutos salen con la ventana máxima en una sola llamada, **sólo lo vendible hoy en esa tienda**, y **cuatro `outcome` distinguibles**. La pasarela gana el cliente generativo **`ai-assist`**: 10 s con **suelo de 8 s comprobado al arrancar**, circuito propio y **sin reintento en timeout**; y un **422 que deja de leerse como «IA no disponible»** sólo en esas dos operaciones. Con la IA caída el card sale igual, desde el catálogo. **Sin migración y con `openapi.json` idéntico byte a byte.** La demo queda configurada para generar; la **demo quedó desplegada y verificada el 22 de septiembre**: una asistencia real devuelve el argumentario con «**250,00 €**» y «**5**» resueltos en el texto, los sustitutos salen con tres tramos de su embudo —60 candidatos, 28 en la tienda, página de 5— y `jbg-demo-ai` se queda en **269,9 MiB de 512**, sin moverse al generar. La latencia de extremo a extremo se midió con proveedor real sobre 80 peticiones: **p95 7,1 s y máximo 7,9 s**, así que el presupuesto se queda en 10 s. **La cuota de tokens por minuto no es la restricción**: corta antes el límite propio de 10 peticiones por minuto y usuario. Y el despliegue dejó **dos hallazgos ajenos a C34**, los dos en `DEFERRED_TASKS.md`: un entorno nuevo nace con `ai.pos_projection` vacía y **toda** la recuperación responde 503, y el corpus de conocimiento **no viaja en la imagen** de `jbg-ai`. Los recuentos **sí se mueven al archivarla**: **36 archivadas y 3 pendientes** —C36, C38 y C39—. Detalle en [c34-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c34-implementation-measurements.md).
>
> **Ampliado el 2026-09-21 — C34 pasa a en curso, y su exploración refuta la anotación que le daba la consulta libre.** **C34** (`add-dotnet-assist-and-recommendation-endpoints`) se abre con historia ([HU-AIENG-034](Historias/AI-Eng/HU-AIENG-034.md)), ticket ([T-AIENG-034](../openspec/changes/archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/ticket.md)) y decisiones ([c34-exploration-decisions.md](Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md)), en la rama `c34-add-dotnet-assist-and-recommendation-endpoints`. Es el **primer consumidor .NET** de `POST /v1/assist/sale` y de `POST /v1/retrieval/substitutes`, y el change que **desbloquea a C36**: con C32b archivado, **es el único nodo libre del grafo**. Los recuentos no se mueven —siguen **35 archivadas y 4 pendientes**— porque abrir no es archivar.
>
> **La anotación del 14 de septiembre que daba a C34 la ruta de la consulta libre es falsa en su premisa.** Decía *«ninguna hidratación nueva»*, pero `{{price}}` y `{{stock}}` **no dicen de qué pieza son**: en M2 y M3 da igual, porque hay una sola; en M1 y en el agente el argumentario habla de varias piezas con los mismos dos tokens, y .NET no puede asignarlos sin adivinar. **C34 se queda con las dos rutas del card** —el argumentario o la pregunta sobre una pieza, y sus sustitutos— y **el §15.12 del diseño sigue siendo cierto**. El arreglo es de Python y es pequeño —prohibir los marcadores en las tareas sin pieza anclada, porque las filas ya enseñan el precio hidratado—, y queda identificado y no hecho.
>
> **Cinco mediciones reproducibles decidieron el resto**, con su SQL o su script en el informe. **Uno · el presupuesto de 5 s del §6.4 está por debajo del peor caso de Python**: en el ancho que se sirve, el **7,5 %** de las peticiones pasa de 5 s sólo en llamadas al proveedor y el peor caso por construcción es 2 × 4 s. Pasa a **10 s**, con **suelo validado al arranque** y **sin reintento en timeout**, porque reintentar son 20 s y dos llamadas de pago. **Dos · `{{stock}}` se escribe como número en el 88,3 %** de 213 argumentarios («tenemos {{stock}} en tienda»), así que se sustituye por el entero y no por una etiqueta. **Tres · hidratar cambia lo que Python afirma**: quitar los miembros que la tienda no lleva dejaría `family_has_variants` falso en el **19,2 %** de las piezas ancladas con familia, y .NET lo recalcula. **Cuatro · la ventana de sustitutos la decide .NET**: con `top_k = 5`, en Fornells el **71,1 %** de las piezas no llena una página; con `top_k = 20`, el **7,1 %**. **Cinco · .NET tiene dos definiciones incompatibles de stock bajo**, y `stock_critical` se fija en **1 o 2 unidades** —el *bucket* `ultimas_unidades` de C32a—, que salta en el **4,2 %** de las filas.
>
> **Cuatro decisiones se cerraron con el desarrollador:** sólo el card; **`POST` con `question` en el cuerpo**, porque en una URL la pregunta del cliente acaba en el log de nginx; con la pieza anclada **sin stock**, el argumentario se retira si no hay pregunta y se conserva si la hay —147 de 213 escriben *«disponible por {{price}}»* antes de saber el stock—; y **encender la generación en la demo es la última tarea**, así que la zona gana `deploy/demo/` y `compose.demo.yaml` y se cierra la tarea diferida de C30b. **Un cambio de política respecto a la ficha:** un marcador sin resolver retira el argumentario y no la respuesta. Y **un 422 de Python deja de leerse como «IA no disponible»**: hoy lo es, y una pieza dada de alta antes de la sincronización aparecería como una caída.

> **Actualizado el 2026-09-21 — C32b implementado, y la pasada refuta el número central del diseño.** **El sobrecoste de la autonomía no es ×19: es ×3,0** (0,0274 USD/petición contra ~0,0092 del pipeline determinista, **cada etapa tarifada con su propio modelo**), medido en la pasada `293fe5c6e470` de **204 peticiones y dos brazos** y **3,82 USD**. *(Corregido por la verificación independiente: la primera versión publicaba ×7,6 sobre un coste del clasificador de 0,00205 USD atribuido a C31 que C31 nunca publicó; el artefacto lo mide a 0,0084. Las cifras salen hoy de `agent_sweep --rescore`, sin proveedor.)* Y **la descomposición «×5 estructural de tokens × ×4 reversible de modelo» no se sostiene**: el brazo barato baja a ×1,1 —mejor de lo que el ×4 predecía— **a cambio de no servir**, porque topa un presupuesto en **54 de 82 peticiones (66 %)** contra **1 de 82** del caro. No es que elija peor: **no sabe parar**. Q-7 queda respondida en no, con el mismo desenlace que C31 midió para el clasificador y por un síntoma distinto. **Tres de los seis presupuestos se fijan por medición y dejan de ser marcadores**: tokens 120.000 → **40.000** (p95 16.244 de clasificador + bucle, que es lo que el presupuesto compara), contexto 40.000 → **30.000** caracteres (p95 4.709) y reloj 20 s → **15,0 s** (p95 9,0 s) **para la petición entera, argumentario incluido** —el bucle corre contra 15 s menos 8 s de reserva, y en `gpt-4o` ninguna de las 102 peticiones habría cortado—; el techo de herramientas sube de 6 a **8** tras medir p95 5 con un 3,9 % de peticiones truncadas. **La curva de crecimiento cierra O-5:** de 1.974 a 3.470 tokens entre la vuelta 1 y la 5, casi lineal — **no hace falta compactar**, y la decisión se toma con el dato delante en vez de por precaución. **Las dos preguntas que C32a dejó abiertas quedan respondidas:** ninguna herramienta muerta, **cero nombres de herramienta inventados** —que era «el dato más informativo que la pasada podía producir» y sale vacío— y cero llamadas consecutivas idénticas; y la etiqueta cualitativa **es compatible con gobernar el pivote**: `gpt-4o` pivota en 3 de 3 escenarios sin existencias y en ninguno de las tres etiquetas donde sería caro, sobre **un escenario por etiqueta**, y el único infra-pivote es del brazo barato. **Lo que la implementación refuta de sus propios artefactos:** el ticket **no lista `assist/tools.py`** y hubo que tocarlo, porque la observación de C32a excluye por regla `product_id`, la puntuación y el título del documento y el contrato congelado los exige — se resuelve con un registro de evidencia que es la segunda banda lateral del registro, inerte al invariante de solo-lectura **estructuralmente** y no por exención; y **un fallo de proveedor reportaba `sin_mas_herramientas` con `partial: false`**, defecto que sólo apareció cuando un límite de tasa dejó respuestas indistinguibles de una completa —cuántas no se sabe: la pasada no dejó artefacto—, y que añade `fallo_proveedor` al vocabulario cerrado **hasta el contrato publicado**. Cierre: **1.576 passed / 0 failed** comparados **por nombres** contra 1.469 —**0 nombres desaparecidos**, 107 añadidos (89 de la implementación y 18 de la verificación independiente), tres tests preexistentes modificados y ninguno retirado ni renombrado—, `openspec validate --all --strict` en **59 · 0**, y `openapi.json` movido de `43f70fda…` a **`d8d48f87…`** con **0 hojas retiradas y 0 cambiadas** verificadas contra la línea base de C32a, que ahora un test compara desde un fixture. **El golden set no se ha tocado**, con dos tests que lo comprueban en las dos direcciones. Queda **abierto y medido**: el **13,1 %** de los argumentarios de `gpt-4o` se retira —9,5 puntos por `dangling_citation`— contra el 2,2 % de la ruta determinista. Informe: [c32b-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c32b-implementation-measurements.md).

> **Ampliado el 2026-09-20 — C32b pasa a en curso, y con él arranca lo único que taponea el cierre del proyecto.** **C32b** (`add-sales-assistant-agent-loop`) se abre con historia ([HU-AIENG-032b](Historias/AI-Eng/HU-AIENG-032b.md)) y ticket ([T-AIENG-032b](../openspec/changes/archive/2026-09-21-add-sales-assistant-agent-loop/ticket.md)). De las **cuatro cosas que el PF evalúa de la capa agéntica** —el bucle, el presupuesto duro, el invariante de solo-lectura y el `partial: true`— C32a entregó **una**; C32b entrega **las tres restantes**, y con ellas la fila de ablación del §11.4 que justifica el sobrecoste de la autonomía. Esa fila **desaparecería si el bucle sustituyera al pipeline** en vez de convivir con él, que es por lo que la ruta es nueva y `POST /v1/assist/sale` no se toca campo a campo ni techo a techo.
>
> **Las decisiones de arquitectura quedan cerradas en la exploración, y tres cambian la ficha.** **Uno · el clasificador cambia de papel:** en esta ruta es **guardarraíl y no enrutador** — una clasificación por petición sobre el turno que se contesta, el rechazo cortocircuitando en cualquier turno con los dos códigos de C31 y sin gastar tools, la repregunta movida al bucle vía `pedir_aclaracion` (que pasa a ser **terminal**) y el `index` descartado. La matriz de confusión publicada **queda intacta**, porque lo que entra al clasificador sigue siendo una consulta suelta. **Dos · el puerto del agente no tiene campo de texto:** *«el contenido textual de las vueltas se descarta»* deja de ser disciplina y pasa a ser **verdad del tipo**, el mismo criterio con el que C32a comprobó el invariante de solo-lectura por introspección en vez de con un `writes: bool` — un campo que alguien no debe leer es un campo que alguien leerá. Coste declarado: se pierde el razonamiento del modelo para depurar, y el adaptador registra longitud y digest, nunca el texto. **Tres · ninguna etiqueta de disponibilidad llega al argumentario:** gobierna la decisión del bucle y no la prosa, porque la autoridad sobre el stock es de .NET, la proyección se desfasa minutos, `{{stock}}` es la única expresión de existencias que el contrato admite, y `disponible` es **literalmente miembro de `STOCK_MARKERS`** en la puerta numérica.
>
> **Dos consecuencias que el change arrastra y conviene no perder.** **`ai-service/openapi.json` se regenera** —primera vez desde C30a—, con movimiento de **adición pura** verificado hoja a hoja: ningún campo se retira ni cambia de tipo, y la forma de `AssistResponse` queda pinchada como conjunto. Y **la capability viva `sales-assistant-tools` se modifica**: `TOOL_FAILURE_CAUSES` gana un quinto valor, `presupuesto_agotado`, para las tool calls que el modelo pide y no caben en el presupuesto — se ejecutan las que caben **por orden de emisión** y el resto vuelve como observación fallida, porque un error es dato y no excepción. No es, por tanto, un change de sólo `## ADDED`.
>
> **Actualizado el 2026-09-20 — C32a implementado, y la implementación refuta seis cosas, empezando por el propio invariante.** **El vocabulario de escritura de D-6, leído al pie de la letra, es insatisfacible con los puertos que el diseño obliga a inyectar**: `sync` aparece dentro de `ProductSearchPort.projection_synced_at()` y de `ProjectionFreshness.synced_at()`, que son **lecturas** de un checkpoint, y la primera está en el puerto que `consultar_disponibilidad` tiene que capturar. El vocabulario **no se toca** —es una decisión tomada y está en dos artefactos— y lo que se fija es la **regla de comparación**: token a token con igualdad exacta, que sigue cazando `save_profile`, `bulk_insert`, `upsert_projection`, `delete_row` y `sync_now`, con los dos falsos positivos pinchados como casos negativos. **`Settings` tropieza con lo mismo** —el shim deprecado `update_forward_refs` de pydantic— y se resuelve excluyendo la configuración **por tipo** y no por una bandera que la tool ponga: una tool no puede sacar sus dependencias de la comprobación. **Y el hallazgo que no estaba en ningún artefacto:** `low_confidence` **no es la abstención** y emitirlo habría dicho lo contrario de la verdad sobre el conjunto juzgado —el propio `retrieval/orchestrator.py` lo avisa en un comentario, 1 de 20 fuera de dominio contra 10 de 43 respondibles—, así que `buscar_catalogo` usa la costura `on_abstention` de C30a y emite `abstenido`. **La trampa que los artefactos anunciaban como la más cara no costó nada:** ampliar `ProductSearchPort` **no** rompe los dobles, porque es un `Protocol` sin `@runtime_checkable`, nadie hace `isinstance` contra él y el repositorio no tiene `mypy` ni CI para `ai-service`; ampliar el doble sigue siendo necesario, pero porque la suite **llama** a los dos métodos nuevos, no porque un tipo la rechace. Cierre: **1.468 passed / 0 failed** comparados **por nombres** contra una línea base de 1.418 —**ningún test retirado ni renombrado**, y la suite de `ai-service` está verde de fábrica, al revés que backend y frontend—, `openspec validate --all --strict` en **58 · 0**, **1.021 enlaces y 0 rotos**, y `openapi.json` **idéntico byte a byte** verificado contra su `sha256` y no supuesto. **Archivado el 2026-09-20 con 1.469 passed / 0 failed**, tras una pasada de verificación independiente que reprodujo cada cifra contra el árbol y encontró cuatro cosas, **dos de ellas defectos de código**: la exclusión de objetos inertes del invariante estaba escrita **por categoría** —todo modelo de pydantic y toda dataclass—, lo que dejaba el puerto de conocimiento fuera de los tres ejes y habría dejado pasar un puerto que escribiera si estuviera escrito como cualquiera de las dos; y `document_by_sku()` usaba `.first()` sobre la premisa falsa de que `sku` es único en el esquema `ai`. Capability viva `sales-assistant-tools` nacida con **13 requisitos y 25 escenarios**. Informe: [c32a-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c32a-implementation-measurements.md).
>
> **Ampliado el 2026-09-20 — C32a pasa a en curso, y su exploración resuelve una decisión que el diseño llevaba abierta desde agosto.** **C32a** (`add-sales-assistant-tool-registry`) se abre con historia ([HU-AIENG-032a](Historias/AI-Eng/HU-AIENG-032a.md)) y ticket ([T-AIENG-032a](../openspec/changes/archive/2026-09-20-add-sales-assistant-tool-registry/ticket.md)). Los recuentos **no se mueven** —siguen 33 archivadas y 6 pendientes— porque **abrir no es archivar**. Es la mitad **sin llamadas a un proveedor**: entrega las seis tools, el registro y los invariantes, y deja el bucle a C32b.
>
> **La sexta tool no tenía servicio detrás, y la ficha se contradecía a sí misma.** Enumeraba seis e invocaba dos veces la regla que retiró a `perfil_punto_venta` y a `buscar_complementarios` —*«una tool que devuelve error es peor que una tool ausente»*—, que aplicada a `consultar_disponibilidad` la deja en cinco; pero nombraba también `test_out_of_stock_query_triggers_substitutes_tool`, que **sin señal de disponibilidad no tiene disparador**, y el pivote a sustitutos es el escenario de venta más característico del dominio. Lo que las reconcilia estaba en el diseño y no en la ficha: el §6.1 declara que el esquema de la llamada de vuelta Python → .NET *«queda como decisión abierta del change del agente de venta»*. Se resuelve **difiriéndola con motivo**: la tool se sirve desde `ai.pos_projection` y el endpoint .NET queda **identificado, acotado y no hecho**. La única arista de vuelta que existe hoy lleva `X-Index-Feed-Key`, **no lleva `[Authorize]` a propósito**, no transporta `pos_id`, y es un feed paginado de 200 filas con keyset — no una consulta puntual por producto.
>
> **Y el bucket no puede viajar crudo, porque son dígitos.** `QTY_BUCKETS` es `{"0", "1-2", "3+"}`: pasárselo al modelo es pasarle una cifra de stock, que es lo que el §6.2 y el §15.10 prohíben y lo que el propio puerto declara al decir que *«a bucket on the wire would be the beginning of one»*. La observación viaja como **etiqueta cualitativa sin dígitos** —vocabulario cerrado, igual que los `warnings[]`—, declara la antigüedad de la proyección, y distingue **«sin ámbito»** de **«agotado»**: ausencia de fila no es cero, y confundirlas dispararía el pivote a sustitutos sobre una pieza que la tienda sí puede vender. La puerta numérica de C30b sigue siendo la red, pero deja de tener que salvarnos.
>
> **La repregunta como tool no escribe la pregunta.** Recibe un eje del enum cerrado que C31 ya publica y el castellano lo sigue escribiendo `clarification_for()`: el campo está tipado como prosa, **ninguna puerta numérica lo inspecciona**, y dejarlo al modelo retiraría un requisito vivo de `assist-generation`. **Y el invariante de solo-lectura se comprueba por introspección del registro** —nombres congelados, ningún puerto con método de escritura, ningún cliente que emita otro verbo que `GET`— y no con una bandera que cualquiera puede poner a falso: el §15.8 es una de las tres declaraciones que el README entrega, así que o se demuestra o no se declara. **Cero movimiento de `openapi.json`**: el registro no se cablea a ninguna ruta porque su único consumidor es el bucle de C32b.
>
> **Ampliado el 2026-09-14 — C31 pasa a en curso, y su exploración refuta la justificación de su propia ficha.** **C31** (`add-guardrails-and-intent-router`) abre con historia ([HU-AIENG-031](Historias/AI-Eng/HU-AIENG-031.md)), ticket ([T-AIENG-031](../openspec/changes/archive/2026-09-16-add-guardrails-and-intent-router/ticket.md)) y conjunto de enrutado ([`evals/routing/cases.yaml`](../ai-service/evals/routing/cases.yaml)), sobre la rama `c31-add-guardrails-and-intent-router`. Los recuentos de la tabla **no se mueven** —siguen **32 archivadas y 6 pendientes**— porque abrir no es archivar. Es el **duodécimo change consecutivo cuya exploración refuta lo escrito antes** — tras C21, C22, FIX1, C23, C24, C25, C25bis, C26, C28, C30a y C30b — y lo que refuta es **el argumento con el que la ficha se justifica**.
>
> **«Fuera de dominio» significa dos cosas y la ficha las mezcla.** Se justifica diciendo que *«sin puerta, C30 contestaría «¿qué tiempo hace mañana?» con cinco familias»* y apoyándolo en que **18 de 20** consultas fuera de dominio llegan hoy con candidatos. **Las dos mitades no hablan del mismo conjunto.** Las 20 de la categoría `fuera-de-dominio` del golden set son `un salero de plata`, `un lingote de oro`, `una correa de reloj marron`, `un joyero de viaje para los anillos`: **relojería, platería de mesa, papelería y numismática**, o sea los oficios vecinos, y el propio `criterion.md` lo dice — *«son plausibles **dentro de la joyería** y el catálogo no las puede satisfacer»*. Un clasificador de intención que se pregunte *«¿es esto una pregunta de joyería?»* **contestará que sí a las veinte, y con razón**, así que la ficha tal como está entregaría un guardarraíl para un conjunto de **cinco casos** en todo el repositorio y **no movería la cifra que usa para justificarse**. Son **dos puertas**: dominio, clasificable sin recuperar, y **cobertura de catálogo**, que es lo que mide el 18 de 20. Se cubren las dos y se publican **dos cifras separadas**, porque la diferencia **es el hallazgo**: el retriever no puede distinguirlas —está medido, el rango entero de las imposibles vive *dentro* del de las contestables— y el enrutador sí.
>
> **La distinción no es opaca: está escrita en los datos y es contra un vocabulario cerrado.** Los `note` del golden set la redactan caso por caso — `un joyero de viaje para los anillos` → *«lo que guarda las joyas, **no una joya**»* —, y eso es una pregunta sobre el objeto pedido contra los **doce tipos de pieza** de `vocabularies.yaml`. **Una regla léxica muere ahí a propósito:** `pulsera` y `anillos` aparecen literalmente en dos de las veinte, puestas para matarla; y la trampa simétrica también existe, porque las **12** consultas de `descripcion-sin-anclaje` no nombran ningún tipo de pieza y son justo las que la rama vectorial existe para servir. De ahí el **criterio de veto declarado antes de medir**: una sola de esas doce silenciada tumba la configuración, aunque capture las veinte.
>
> **Dos decisiones más que salen de medir, no de opinar.** **Una · el enrutador cuesta una llamada y sólo en M1.** Medido: `AssistTimeoutMs` son **5.000 ms**, una llamada de generación va a **2.216 ms de p50** y el **55 %** de las peticiones gasta la reparación, así que una petición reparada ya está del orden de **4.400 ms** — el margen para meter algo en serie delante es de centenares de milisegundos. M2 no tiene consulta que clasificar; **M3 es `both` por construcción** y su guardarraíl sale **gratis** del umbral `0,51` que C23 fijó sobre un **hueco limpio de 8 milésimas** (32 preguntas del corpus por debajo, 5 de fuera por encima): *cero citas tras el umbral* ya significa «el corpus no cubre esto», y hoy **nadie lo lee como tal**. **Dos · el conjunto de evaluación ya existía repartido y nadie lo había conectado**: 48 `catalog`, 20 `not_in_catalogue` y 4 `ambiguous` del golden set, 32 `knowledge` de las marcas del corpus y 5 `out_of_domain` del fixture de C23 — **109 casos con coste de etiquetado cero**, más **10 casos `both`** nuevos, que es la única clase que no existía. Y el detalle que cierra el círculo: las cuatro `ambigua` se declararon **sin juicios** el 2026-09-11 con la nota *«la respuesta correcta es una repregunta, y eso es una decisión del agente»* — su conjunto de evaluación llevaba tres días esperando a que alguien reclamase `clarification_question`, que es lo que C30b propuso el día antes.
>
> **Y lo que la exploración deja anotado fuera de C31:** la **consulta libre gana ruta**, porque C31 pone argumentario en M1 y ese modo **no tiene pantalla** (§15.12). La ruta .NET queda anotada en la ficha de **C34** y el bloque de pantalla es de **C36** —dos filas más en la tabla de copy que esa ficha ya va a escribir—, con la distinción que no se puede perder: `abstained` y el rechazo del enrutador son **dos negativas de mecanismos distintos** y pintarlas igual borra justamente lo que las dos cifras existen para sostener.

> **Actualizado el 2026-09-15 — C31 implementado, y la medición refuta siete cosas, empezando
> por su propia primera configuración.** El **veto de D12 —declarado antes de medir— tumbó la
> primera pasada**: `router/v1` silenciaba **15 de las 48** consultas contestables, diez de ellas
> `descripcion-sin-anclaje`, con un falso positivo del **31,25 %**. Y lo que fallaba **no era
> clasificar intención**, sino no saber **cómo se nombra este catálogo**: las piezas se llaman
> `<tipo> <motivo>` —«Colgante erizo de mar», «Anillo caracola»—, así que *«el bicho con púas que
> se pisa en las rocas»* **es** una consulta de catálogo, y el clasificador la leía como una
> pregunta ajena a la joyería. La distinción fina que la ficha no veía no es *intención contra
> cobertura* sino **artículo de otro oficio contra motivo de éste**, y la regla que la corta es
> negativa: nadie entra en una joyería a comprar una bicicleta. **Tres revisiones de prompt
> bajaron el falso positivo a 6,25 % y no lo cerraron; el que lo cerró fue el modelo.** Con el
> mismo prompt, `gpt-4o` acierta **48 de 48** en `catalog`, silencia **0** y **pasa el veto**,
> mientras `gpt-4o-mini` seguía silenciando tres consultas **nombradas literalmente en el prompt**
> como ejemplos de lo que no hay que rechazar. Eso **refuta la opción por defecto nº 4 del
> ticket** —«mismo `gpt-4o-mini` de partida»— y **vindica D10/D9 con una medición**: la variable
> separada del modelo es lo único que permitió mover el del clasificador sin invalidar las 120
> generaciones de C30b. **Y el riesgo mayor declarado no se materializó:** la lista blanca
> numérica de la consulta libre resultó ser de **~13 numerales y no de cinco** —la recuperación
> devuelve 15 candidatos, no 5— y aun así la puerta numérica rechazó **cero**; lo que sí tumbaba
> el argumentario de M1 era `dangling_citation`, porque la sección de tarea de `catalog` no decía
> que no hubiera citas que usar. **El contraste con el umbral `0,51` de C23 da 0 discrepancias en
> 37**, que es la evidencia más fuerte disponible de que aquel hueco de 8 milésimas separa algo
> real. Informe: [c31-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c31-implementation-measurements.md).

> **Actualizado el 2026-09-13 — C30 se parte en C30a y C30b, y con él se cierra un hueco que no era suyo.** El corte lo decide **la dependencia de sus consumidores**, no el tamaño: C34 y C36 necesitan **la forma** de la respuesta y no la prosa. **C30a** (`add-assist-structure-and-rule-warnings`) entrega el movimiento del contrato congelado, los tres modos, la agrupación por familia, el listado de miembros, los avisos por reglas, el filtro de ficha de material y la puerta de abstención — **sin una sola llamada a un proveedor**, y aun así con **citas verificables**, porque el corpus está indexado y el direccionamiento por ficha de material es determinista. **C30b** (`add-assist-pitch-generation`) añade el argumentario, la integridad referencial de las citas y la puerta numérica. El corte deja de regalo la **ablación de la capa de generación**: misma ruta, mismos candidatos, mismas citas, con prosa y sin ella.
>
> **El hueco que la exploración descubre y que no era de C30:** el corpus de conocimiento de C23 —**32 documentos y 161 fragmentos**, indexado y calibrado desde el 6 de septiembre— **no tenía ninguna ruta hasta la pantalla del joyero**. C34 exponía sólo rutas por pieza y C36 sólo una tarjeta; diez de esos 32 documentos son conversación de mostrador puro —la piscina, la piel sensible, los niños, viajar, regalar sin saber la talla, la cosmética— y ninguno era alcanzable. Se cierra por el camino más barato que existe: **un parámetro de pregunta en la ruta que C34 ya va a escribir y una caja en la tarjeta que C36 ya va a construir**. El tercer modo —pregunta libre **sin** pieza delante— se implementa en el servicio pero **no recibe pantalla en esta ronda**, y eso queda declarado como limitación: su consumidor es el bucle del agente y el arnés.
>
> **Ampliado el 2026-09-13 — C30a pasa a en curso.** Con C26 archivado, **C30a es el único change libre que desbloquea algo**, y desbloquea la cadena entera. Tiene historia ([HU-AIENG-030a](Historias/AI-Eng/HU-AIENG-030a.md)) y ticket ([T-AIENG-030a](../openspec/changes/archive/2026-09-13-add-assist-structure-and-rule-warnings/ticket.md)), y es el **décimo change consecutivo cuya exploración refuta lo escrito antes** — tras C21, C22, FIX1, C23, C24, C25, C25bis, C26 y C28. Su rama es `c30a-add-assist-structure-and-rule-warnings`.
>
> **Las seis preguntas abiertas del ticket se cerraron el mismo día** tomando su opción por defecto, antes de generar el resto de los artefactos. La que más pesa: la capability nueva se llama **`assist-generation`**, porque C30b añade requisitos sobre ella en vez de crear otra y porque `sale-assist` nombraba el caso de uso y no la capacidad, con `assisted-search-panel` y `ai-assisted-search` ya ocupando ese registro. Las otras cinco fijan las dos secciones de la lista blanca, el tope de dos materiales, los tres spikes dentro del change, un grupo sin familia en el fixture y `abstained` emitido siempre. Los valores de las dos primeras son **punto de partida de un barrido**, no calibración.
>
> **Y cinco supuestos de la ficha de C30 resultaron falsos contra el árbol**, comprobados antes de escribir código: el contrato exigía `family_id` **obligatorio** cuando el ~58 % del catálogo no tiene familia; el único consumidor previsto está **anclado a pieza** mientras la petición sólo aceptaba texto; dos de los cuatro avisos necesitan stock real y por tanto **son de .NET**; la citación perdía en la frontera el identificador resoluble y la marca de alcance —**25 de 161 fragmentos** son compromisos de la casa—; y la abstención está al **10 %** —activa por defecto, pero el camino de venta asistida no la miraba—, con **18 de 20** consultas fuera de dominio llegando con candidatos sobre un conjunto de evaluación cuya categoría mayor son esas **20 de 72**. Detalle en [c30-exploration-decisions.md](Proyecto%20Final%20AIEng/informes/c30-exploration-decisions.md).

> **Ampliado el 2026-09-14 — C30b pasa a en curso, y su exploración refuta las dos garantías que la ficha prometía.** Con C30a archivado, **C30b** (`add-assist-pitch-generation`) abre con historia ([HU-AIENG-030b](Historias/AI-Eng/HU-AIENG-030b.md)), ticket ([T-AIENG-030b](../openspec/changes/archive/2026-09-14-add-assist-pitch-generation/ticket.md)) y decisiones ([c30b-exploration-decisions.md](Proyecto%20Final%20AIEng/informes/c30b-exploration-decisions.md)), sobre la rama `c30b-add-assist-pitch-generation`. Es el **undécimo change consecutivo cuya exploración refuta lo escrito antes** — tras C21, C22, FIX1, C23, C24, C25, C25bis, C26, C28 y C30a — y lo que refuta son **sus dos garantías centrales**, las dos por medición estática sobre el árbol. **Uno · la lista blanca numérica se abre sola, y la abre el propio corpus**: `material-oro.md` dice «18 quilates son 750 milésimas, 14 quilates son 585» y `material-plata.md` habla de «925 milésimas», así que con la ficha del oro en contexto un argumentario que escriba **«750 €» pasa** una lista blanca pura — exactamente el agujero que la puerta existía para cerrar. De ahí sale la única lista negra del diseño: **adyacencia a un marcador de moneda o de existencias rechaza siempre**, esté o no el número en la lista blanca, y es correcta porque ese conjunto sí es cerrado y no ambiguo, al contrario que «números en joyería». **Dos · `{pitch, citation_ids[]}` no prohíbe la decoración que D-D existía para prohibir**: un modelo que devuelva los cinco `citation_id` entregados pasa la integridad referencial de forma **perfecta y trivial** sin haber usado ninguno, con lo que la afirmación *«son las que el argumentario usó»* queda en palabra del modelo. Se corrige con un **tramo de apoyo**: el modelo declara, por cita, el fragmento de su propio texto que esa cita sostiene, y el código comprueba que es subcadena literal de lo que escribió. Determinista, sin juez, sin llamada extra, y **no viaja al cable** — la respuesta conserva `pitch: str` y `citations[]` con sus diez campos.
>
> **Y un hueco que ningún artefacto tenía anotado:** el golden set de C24/C26 son **72 consultas y ninguna ancla una pieza** —`source_product_id` sólo aparece en las **5** de categoría `sustituto`, y ancla una búsqueda de sustitutos—, o sea **100 % del modo de consulta libre**, que es justo el que C30b difiere a C31. **El golden set no puede evaluar el argumentario.** El barrido de C30b necesita muestra propia, estratificada por número de materiales, y **C38 hereda el mismo hueco** para sus escenarios de generación y su RAGAS. Las otras siete decisiones —una sola reparación con las violaciones acumuladas, las citas que no se vacían al degradar, `prompt_version` pasando a significar *«la capa de generación corrió»*, el cliente propio porque la costura de C09 **descarta `response.usage`**, la degradación en vez del 5xx y el corte antes de llamar cuando hay abstención, y la consulta como dato delimitado— están en el informe con sus alternativas descartadas.
>
> **Ampliado el 2026-09-14, al implementar C30b — y la medición refuta el riesgo que el propio
> change declaraba como el mayor.** `POST /v1/assist/sale` **escribe el argumentario** en los dos
> modos anclados a pieza: prosa corrida de 3 a 5 frases, `prompt_version` y `usage` reales, y
> tres comprobaciones deterministas sobre lo generado. El modo de consulta libre y la abstención
> **cortan antes de llamar**, y un proveedor caído o un *timeout* devuelven la respuesta de C30a
> con **200**. La suite de `ai-service` pasa de **1195 a 1320 tests, 0 en rojo antes y después**;
> `openapi.json` se regenera por **una sola descripción** —verificada aplanando los dos
> documentos a hojas: **1102 antes y 1102 después, una hoja cambiada**, ningún campo añadido,
> retirado ni con el tipo cambiado— y **no hay migración**, porque el argumentario no se
> persiste.
>
> **El barrido, 120 generaciones reales sobre muestra propia declarada de antemano** —40 piezas
> estratificadas a partes iguales entre 1 material y ≥2, en 3 anchos de contexto—, dice tres
> cosas que sus artefactos no decían. **Uno · la puerta numérica no rechazó nada: 0 de 120.** El
> diseño declaraba como riesgo mayor que *«la puerta se coma los argumentarios buenos»*, y no
> ocurrió ni una vez; las 121 violaciones del barrido son **todas** de correspondencia, y ninguna
> costó un argumentario porque su política es proporcionada —se retira esa cita y la prosa se
> publica—. La lectura no es que la puerta sobre, sino que **la prevención funcionó y la
> detección no tuvo que actuar**: prosa corrida impuesta en el prompt, placeholders obligatorios
> y un fichero de prompt **sin un solo dígito**. **Dos · la decoración que D-D y D9 existían para
> prohibir, por fin con cifra**: en el ancho que se sirve se ofrecen **140 citas y sólo 60
> sobreviven a la verificación** —42,9 %—, así que emitir todo lo recuperado habría publicado más
> del doble de citas que el argumentario puede sostener. **Tres · el coste real es 1,9 × el
> estimado** —0,00077 USD por petición contra los ~0,0004 de la ficha—, porque el contexto es
> mayor y el 55 % de las peticiones gasta la reparación.
>
> **Y dos umbrales decididos con la cifra delante, que es como se decide aquí.** El **plegado de
> signos NO se añade**: sólo el **2,5 %** de los fallos de correspondencia son de puntuación,
> contra el umbral del 10 % declarado antes de medir — el fallo es de paráfrasis, no de signos.
> El ***timeout* de 3 s sí cortaba**: medido **por llamada**, que es como se aplica, el p95 es
> **2.863 ms**, así que 3 s estaba a **1,05 × p95** y cortaba *jitter* en 8 de 175 llamadas. Sube
> a **4 s** y pasa a ser ajustable (`JPV_ASSIST_PITCH_TIMEOUT_SECONDS`), que es literalmente lo
> que el diseño decía hacer *«sólo si el barrido mide que corta generaciones buenas»*. Subir un
> *timeout* no ralentiza ninguna llamada rápida: la espera típica sigue en ~2,2 s y lo único que
> cambia es la cola, que antes se servía sin argumentario.
>
> **Una cuarta refutación, del propio arnés y propia.** La primera pasada medía el *timeout*
> contra el **tiempo total de la petición**, que incluye dos llamadas cuando hay reparación:
> leía **70 % de cortes donde había 4,6 %**, y esa lectura habría justificado mover el umbral
> tres veces más de lo que la medición sostiene. Se corrigió instrumentando la latencia por
> llamada, se repitió el barrido entero y el error quedó fijado con un test
> (`test_the_timeout_is_measured_per_call_and_never_per_request`). **Y un defecto real que la comparación por nombres
> destapó, corregido:** dos tests de `tests/evals/test_reproducibility.py` fallaban con una
> selección parcial de directorios y pasaban en la suite completa. No era *flakiness*, era
> reproducible en un comando: `jbg_ai/db/engine.py` cachea un motor **global de proceso** y
> `get_engine` **ignoraba el `Settings` que recibe** si ya había uno, así que el test que
> configura a propósito un host inalcanzable —`@db:5432`, para demostrar el 503— construía el
> motor global y envenenaba a todo consumidor posterior del proceso; en la suite completa no se
> veía porque un test intermedio llamaba a `dispose_engine()` por casualidad. El motor pasa a
> recordar **la URL con la que se construyó** y a reconstruirse cuando cambia, `get_sessionmaker`
> pregunta por él **primero** para no cortocircuitar la decisión, y **cuatro tests de regresión**
> lo fijan. Es exactamente por qué la regla es comparar **nombres** y no recuentos: un recuento
> habría dicho «igual de verde» y el fallo seguiría ahí.
> Cifras y artefacto en [c30b-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c30b-implementation-measurements.md).

> **Ampliado el 2026-09-13, al implementar C30a.** **`POST /v1/assist/sale` deja de responder 501** y sirve la capa estructurada real. Con ello **`/v1/inventory/propose` queda como la única ruta del contrato que responde 501**, y no por trabajo pendiente sino porque su rama se canceló el 31 de agosto. La suite de `ai-service` pasa de **1038 a 1195 tests, 0 en rojo antes y después**, `openapi.json` se regenera moviendo **sólo los cinco esquemas de assist** —ninguna ruta, ningún esquema añadido o retirado, las otras nueve rutas idénticas— y **no hay migración**. **Archivado el 2026-09-13**, sincronizando **20 requisitos nuevos y 2 modificados** y haciendo nacer la capability viva **`assist-generation`** con 13 requisitos.
>
> **Los tres spikes se corrieron antes de escribir código, y sus cifras decidieron.** *(1)* Las 72 consultas del golden set por `search_knowledge` **contra el índice vivo y al umbral de producción `0,51`**, en dos brazos: el filtro asimétrico retira una media de **36,4 citas de ficha ajena** por material anclado y sólo sube las abstenciones de **41 a 44,3 de 72** — no produce falsa abstención en masa, que era el riesgo que el diseño temía. Y **el modo de consulta libre no necesita umbral propio**: de 101 citas **una sola** es inequívocamente espuria. *(2)* El vector de consulta **sí es reutilizable** entre recuperación y conocimiento — misma `model_version_key` carácter por carácter — y la costura ya existía: es la caché acotada del cliente, con la condición medida de pasar el **mismo texto recortado** a los dos. *(3)* El roster: **156 familias, 491 miembros, máximo 8**; tope fijado en **24**.
>
> **Y la implementación refutó seis cosas más**, recogidas en [c30a-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c30a-implementation-measurements.md). Las dos que importan: el ticket afirmaba que `retrieval/orchestrator.py` **no se modificaba**, y hubo que añadirle una **costura aditiva de observabilidad** (`on_abstention`) porque la decisión de abstención no es recuperable desde `RetrievalResponse` sin reutilizar `low_confidence`, que es justamente lo que D9 prohíbe; y **ni la HU ni el diseño decían a qué pieza describen los avisos cuando no hay pieza anclada**, hueco que se cierra declarándolo: describen la **pieza foco** — la anclada, o el candidato mejor clasificado cuando no la hay.

> **Ampliado el 2026-09-12, al implementar C26.** **`POST /v1/retrieval/substitutes` deja de responder 501** y pasa a servir candidatos reales, con lo que cae el **último 501 cerrable** del contrato congelado —`/v1/inventory/propose` también responde 501, pero su rama se anuló el 31 de agosto y eso ya está declarado como limitación—. Sin migración, sin mover `openapi.json` y **sin una sola llamada al proveedor**: sustituto es producto→producto y el embedding de origen ya está almacenado, así que la capacidad entera es una sentencia SQL. Suite de `ai-service` de **997 a 1038 passed, 0 failed**; `openspec validate --all --strict` en **55/0**.
>
> **Tres cosas que la implementación añadió a lo que la exploración ya había refutado.** (1) **`w_size = 0,05` lo fija el barrido, no el diseño**: once puntos de rejilla, y el término resulta hacer algo —de `0` a `0,05`, **+0,1039 de nDCG@5**—, lo que confirma que la conclusión de C25 *«el valor del peso no cambia el orden, sólo su signo»* **no se traslada** aquí. Las dos lecturas del criterio **discrepan** y eso se publica como hallazgo, porque `criterion.md` lo manda: el nDCG graduado premia `0,075`, pero desde `0,07` la lectura binaria cae y entra en un top-5 un anillo liso de la talla correcta y nada más —el grado 0 explícito de la rúbrica—, así que gana el guardarraíl y, dentro de él, `0,06` y `0,05` empatan por debajo del ruido. (2) **El bloque entero se midió antes de descartarlo**: con la clave de bloque, el hermano de familia más cercano de `SKU13` cae del puesto 1 al **4**, detrás de un anillo que está al doble de distancia, y el más lejano sale de la ventana visible. (3) **La tarea de verificar que la tabla de ablations no se movía acabó siendo una corrección**: los ficheros publicados no cambian, pero el *runner* iteraba todas las consultas juzgadas, que pasaron de **63 a 68** al etiquetar las cinco de sustituto, así que una re-ejecución habría absorbido consultas que dos de sus configuraciones **no pueden ejecutar**. La separación quedó en código (`GoldenSet.retrieval_queries`) y no en una convención: antes de C26 los dos conjuntos coincidían y el alcance era correcto **por accidente**.
>
> **Dos limitaciones medidas, declaradas y no cerradas.** `style_similarity` es cero por construcción para **403 de 404** productos reales —el contrato la exige requerida y no nulable, así que se emite el cero y **la ausencia se declara en `match_reasons`**, y no se deriva del embedding porque sería una copia de `score`—; y la rebanada aísla la calidad del sustituto **dado el producto origen correcto**, ya que la cadena «texto → producto → sustitutos» es de C32. A ellas se suma el sesgo declarado de que el etiquetado de las 126 parejas lo hizo quien diseñó el orden, acotado —no eliminado— por que la rúbrica es anterior al change y por que se etiquetó sobre atributos y nunca sobre posiciones. Historia [HU-AIENG-026](Historias/AI-Eng/HU-AIENG-026.md), mediciones en [c26-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c26-implementation-measurements.md) y rebanada en [c26-substitutes-slice.md](../ai-service/evals/results/c26-substitutes-slice.md).

> **Ampliado el 2026-09-12, al abrir C26.** **C26 (`add-substitutes-retrieval`) pasa a en curso**, con historia ([HU-AIENG-026](Historias/AI-Eng/HU-AIENG-026.md)), ticket ([T-AIENG-026](../openspec/changes/archive/2026-09-12-add-substitutes-retrieval/ticket.md)) y mediciones ([c26-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c26-exploration-measurements.md)). Es el **séptimo change consecutivo cuya exploración refuta lo escrito antes**, tras C21, C22, FIX1, C23, C24 y C25 — y esta vez lo que invierte es el **orden** que la ficha pedía. Cierra el último **501 cerrable** del contrato congelado y ocupa el único eslabón vivo de la cadena crítica `C26 → C34 → C36`.
>
> **Lo que la medición refuta: «misma familia primero» lidera con los candidatos invendibles.** La familia es, por construcción, el conjunto de piezas que se diferencian **justo en el atributo que descalifica** — la talla. Vecinos por coseno de `SKU13 Anillo erizo de mar M`: los tres primeros son el mismo anillo en talla **L, S y XL**, el cuarto es un **colgante** (otro tipo de pieza) y **el primer sustituto usable es el #6**. Pero la familia tampoco se puede excluir: el mejor sustituto de `SKU159 Anillo lapislázuli mediano` es su hermano `mediano oro` —**misma talla, otro material**— y es el **#1**. **La pertenencia a familia es ortogonal; el discriminante es la talla**, y cruza la frontera de la familia en las dos direcciones. Lo confirma el criterio de etiquetado que el proyecto ya tenía escrito: `criterion.md` clasifica «falla la talla que la consulta nombró» como **grado 1 — segunda opción**, no como respuesta.
>
> **El diseño que sale de ahí:** filtro **duro** por `piece_type` —el vector lo viola en 2 de 4 casos—, familia **en el conjunto pero sin prioridad**, y **degradación suave por talla como término continuo en la cola** (`w ≈ 0,05`, barrido; con 0,02 no mueve nada y con 0,08 el hermano cae al puesto 8), **inerte cuando alguna de las dos piezas no declara talla** — porque el **54 % de los anillos** no tiene `size_label` y penalizar por una ausencia es tratarla como valor, que es lo que `ports.py` ya prohíbe. **No reutiliza `demotion_rank`**: su bloque entero de talla particiona, que es exactamente el fallo que C25 midió con la rotación.
>
> **Tres decisiones más, todas medidas.** La **exclusión por stock sale de Python**: estaba especificada dos veces y la versión correcta es la de C34, que respeta la frontera del §6.2 y el invariante del §15.10 —la proyección degrada y nunca elimina—. **`style_similarity` no tiene dato**: sólo **1 de 404** productos reales tiene con quién compartir etiqueta de estilo, frente al **97,8 %** que lo tiene por material, así que se emite el Jaccard y **la ausencia se declara en `match_reasons`** en vez de derivarlo del embedding, que lo convertiría en una copia de `score`. Y **no abstiene**: todo producto del catálogo tiene vecino a menos de **0,255** y el rango de los productos sin familia contiene el de los que la tienen — la misma contención que impidió a C25 re-fijar su umbral escalar. **Cero llamadas al proveedor**: sustituto es producto→producto y el embedding de origen ya está almacenado.
>
> **Cómo se mide:** las cuatro consultas que C24 dejó declaradas sin juicios a nombre de C26 (`q49`–`q52`) se anclan con **`source_product_id` explícito** y se evalúan en **rebanada separada**, porque el endpoint recibe `product_id` y no texto y añadir filas movería el denominador de la tabla publicada. **Entra una quinta consulta sin familia** (`SKU102`), porque las cuatro reservadas tienen familia y el camino sin ella es el **58 %** del catálogo.

> **Actualizado el 2026-09-12 — C27 cortado con medición, no por plazo.** **C27 (`add-complementary-recommendations`) sale del alcance.** Era el corte nº 1 pre-autorizado desde el 31 de agosto, con el disparador *«si el núcleo peligra»*; con prórroga abierta ese disparador no decide nada, así que se sustituyó por uno de evidencia. **Sus dos señales están vacías.** La co-ocurrencia se deriva del `BulkOperationId` y **todas las ventas las escribe el simulador de C10**, cuyo `_pack_operations` baraja las líneas del día y luego escoge deliberadamente el artículo **de lexema o colección distinta**: la matriz está sesgada **en contra** de lo que se le pide medir. Y aunque no lo estuviera, de **4.078 pares** el **98,6 % se ha visto una sola vez**, ninguno tres o más en dieciséis meses, y **463 de 1.168 productos (39,6 %) no tienen ni un socio**. La otra mitad de la regla —solape de `color_tags`/`style_tags`— está indefinida para el **74,7 %** del catálogo y para **403 de 404 productos reales**. Lo que quedaría en pie es `WHERE piece_type <> :tipo AND price_band IN (…) AND stock > 0`, sin una llamada a un LLM: el criterio exacto con el que se anularon cinco changes el 31 de agosto. **Y nunca hubo intención de medirlo:** ni la tabla del §11.1 del diseño ni el golden set reservan categoría a complementarios —las 8 consultas sin juzgar son 4 de C26 y 4 de C31—, así que el change **no puede añadir una fila a la evaluación** a cambio de la última migración EF Core viva. **No hay cestas reales ni las habrá:** el export del 17 de agosto fue catálogo y nada más. Se conservan la ficha, la tabla `ai.co_occurrence` vacía y `cooccurrence.py` con su test; se retiran la tool `buscar_complementarios` de C32, la ruta `.../recommendations` de C34 y el bloque «También puede encajar» de C36. **Condición de reactivación, comprobable:** un export con histórico real a nivel de ticket cuyo percentil 95 de `co_sales_count` sea **≥ 3** — hoy es **1**. Detalle en [c27-cut-measurements.md](Proyecto%20Final%20AIEng/informes/c27-cut-measurements.md).

---

## Épica 16: Inventario Asistido y Señales de Demanda — ⛔ ANULADA (2026-08-31)

> **Toda la rama del agente de inventario está anulada**: C19, C29, C33, C35 y C37. El motivo y sus consecuencias están en el §0 del [plan de changes](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (entrada del 2026-08-31) y en el §10 del [diseño RAG](Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md), donde el diseño se conserva como registro. En corto: **cuatro de los ocho cortes pre-acordados vivían dentro de esta rama**, y lo que quedaba en pie tras dispararlos era una migración, un motor de reglas .NET y una pantalla de aprobación — todo el esfuerzo fuera de lo que el Proyecto Final evalúa. Los agregados de venta que el ranking necesita (`sales30d`, `sales90d`, `lastSaleAt`, `qtyBucket`) **ya están implementados** en el feed de indexación de C12 y son normativos desde la spec viva `index-feed`: C19 habría construido una segunda copia de la misma agregación, con el riesgo de que las dos definiciones divergieran.
>
> El alcance de abajo se conserva **como registro de lo que se decidió no hacer**, no como trabajo pendiente. Las fichas de los cinco changes siguen en el plan con su sello ⛔.

**Descripción:**
Segundo agente del proyecto. Propone reposiciones, traslados entre puntos de venta y acciones sobre stock parado, siempre con aprobación humana. Las señales numéricas se calculan en SQL en .NET; el LLM solo redacta y prioriza.

**Alcance *(anulado — registro histórico)*:**
- Señales de demanda calculadas en SQL: ventas a 7/30/60 días, cobertura, días sin venta, stock en otros puntos de venta
- Perfil comercial por punto de venta, calculado periódicamente
- Entidad `InventoryRecommendation` con ciclo de aprobación y auditoría
- Agente de inventario con propuestas priorizadas y justificadas
- Pantalla de revisión de recomendaciones y vista imprimible por punto de venta

**Changes asociados:** ~~C19~~, ~~C29~~, ~~C33~~, ~~C35~~, ~~C37~~ — **los cinco anulados el 2026-08-31**. C33 (`add-pos-sales-profile`) queda anotado en el plan como *rescatable suelto* si alguna vez hiciera falta el perfil comercial por punto de venta para el ranking.

---

## Épica 17: Evaluación y Observabilidad de IA

**Descripción:**
Sin medición no hay proyecto de IA defendible. Cubre la telemetría de uso real, el conjunto de evaluación etiquetado a mano, las métricas de recuperación y generación, y los escenarios adversarios.

**Alcance:**
- Telemetría consulta → selección (`ProductSearchEvent`) desde el primer día
- Golden set de consultas etiquetadas y línea base de métricas de recuperación
- Ablations para medir el efecto de cada componente (sinónimos, híbrido, señales de negocio)
- Validador anti-alucinación y escenarios de agente
- Casos adversarios: fuera de dominio, inyección, stock cero, consulta imposible, PII
- Documentación final del proyecto con evidencias y limitaciones declaradas

**Changes asociados:** C04 (hecho), **C24** (`add-eval-harness-golden-set-and-baselines` — **hecho**, abierto el 2026-09-06 y archivado el 2026-09-11), C38, C39

- **C24 (hecho, abierto el 2026-09-06 y archivado el 2026-09-11):** el **juez imparcial** del recuperador. El sistema tiene una búsqueda híbrida completa —expansión (C20), fusión RRF de tres listas (C21), prefiltro por punto de venta (C22)— y **ninguna de sus decisiones se tomó con una métrica de relevancia**: se tomaron con una rúbrica que los propios informes declararon insuficiente, y los cuatro escribieron *«C24 lo re-mide»*. Esa rúbrica cuenta aciertos como «tipo de pieza correcto y material correcto», y el informe de C21 la recusa él mismo — *«`doc_text` lleva líneas canónicas `Tipo:` y `Materiales:`, y la expansión apunta justo ahí»*—; bajo ella la rama vectorial saca **67 de 120** frente a **107** de la léxica sola, es decir siete puntos de ciento veinte para justificar el proveedor externo y el índice HNSW. **Y el riesgo dejó de ser teórico el mismo 2026-09-06:** en el corpus de conocimiento, el sustituto *offline* de C23 había medido que la rama léxica ganaba +6,2 pp de recall, y contra el embebedor real el veredicto **se invirtió** —93,8 % en las dos configuraciones, sólo mejora el orden—, además de dejar un umbral que citaba cuatro de las cinco preguntas fuera de dominio. De ahí la primera regla del change: **se mide contra el proveedor real y el índice real, nunca contra un sustituto**. **La exploración cerró trece decisiones y reencuadró la ficha en cuatro puntos:** (1) `v0-lexico` son **dos filas y no una** —`v0-nombre`, el `Name.Contains` que la joyería tenía y que responde la decisión 12, y `v0-fts`, el degradado en español que construyó el propio trabajo de IA— porque juntas informan de qué parte de la mejora es tokenizar en español, gratis y sin IA, y qué parte es recuperación semántica; (2) el golden set baja de 60-70 a **48 juzgadas y 56 escritas**, derivadas **desde los pleitos** y no desde la ficha, con una **matriz de trazabilidad comprobada por código** que falla la carga si el conjunto no contiene, por ejemplo, doce consultas cuya respuesta perfecta no comparte ni un término con la consulta — la contención del riesgo de que el golden set confirme a C21 por construcción; (3) `v0-cag` deja de ser una fila de calidad y pasa a ser **la prueba medida de por qué existe RAG**, porque CAG no tiene una sola línea en el sistema y el PF exige describirlo como componente: entrega tokens, coste y **curva de escala** hasta el punto en que deja de caber, con contexto compactado y **sin precio**, porque la autoridad sobre el precio es .NET; (4) **dos desviaciones que tocan fuera de su zona** — el desempate determinista en las dos sentencias de `retrieval/search.py`, sin el cual dos ejecuciones idénticas difieren y el arnés deja de detectar regresiones, y el cambio de defaults en `Settings` bajo una regla escrita **antes** de medir. Historia [HU-AIENG-024](Historias/AI-Eng/HU-AIENG-024.md), ticket [T-AIENG-024](../openspec/changes/archive/2026-09-11-add-eval-harness-golden-set-and-baselines/ticket.md) decisiones en [c24-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c24-exploration-measurements.md) y **mediciones de la implementación** en [c24-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c24-implementation-measurements.md). **El veredicto, medido el 2026-09-07 sobre las 48 consultas juzgadas:** el buscador que la joyería tenía saca **nDCG@5 0,082**, el degradado en español **0,454**, la rama vectorial sola **0,548** y el híbrido vivo **0,603** — es decir, tokenizar en español aporta +0,372 y es gratis, y la recuperación semántica aporta +0,149 encima. **La rúbrica de C21 queda refutada**: contra un juez que no es parte, la rama vectorial no aporta siete puntos de ciento veinte, sino que **bate a la línea léxica**, y en las doce consultas sin anclaje léxico saca 0,431 frente a 0,035. Tres hallazgos que nadie buscaba: la fusión vigente **pierde más de la mitad** de la ventaja de su rama vectorial justo en esas consultas (0,172 el híbrido frente a 0,431 la vectorial sola); las distancias de los documentos relevantes y las de los irrelevantes **se solapan por completo**, de modo que queda demostrado que C25 necesita un cuantil por consulta y no un escalar; y la regla de defaults, escrita antes de medir, **bloquea** el cambio de `wC` a 1,0 pese a mejorar +0,057 global y +0,073 en las consultas nuevas, porque empeora en la partición de ajuste — que es el caso incómodo para el que la regla se escribió.

**User Stories:**
- [HU-AIENG-004: Telemetría de búsqueda asistida — evento consulta→selección](Historias/AI-Eng/HU-AIENG-004.md) *(C04 — hecho)*
- [HU-AIENG-024: Arnés de evaluación, golden set y líneas base](Historias/AI-Eng/HU-AIENG-024.md) *(C24 — **hecho**, archivado el 2026-09-11; golden set de 48 consultas juzgadas y 56 escritas en `ai-service/evals/golden/`, versionado en git para que cambiar la vara de medir pase por revisión de código, con relevancia graduada 0-2 de anclas mecánicas y publicando **también** la lectura binaria derivada, que es lo que contesta con datos la objeción del apunte de S10 en vez de con argumento; cinco líneas base —`v0-nombre`, `v0-fts`, `v0-cag` acotado, `v1-vectorial`, `v2-hibrido`— y **una** revisión de Alembic con `ai.eval_run/case/result`, que la migración fundacional nunca creó; reproducibilidad por **vectores de consulta congelados** más una tupla de procedencia `(golden_set_version, config_id, index_set_hash, embedding_model_version_key, git_sha)` que sustituye a la semilla aleatoria que la ficha pedía y que no existe en un pipeline determinista; ***pooling* de profundidad adaptativa** —base 20, +10 mientras el tramo siga dando relevantes, tope 60— con juicios **apendables** por `(query_id, product_id)` y `unjudged@5` reportado, de modo que `v3-señales` de C25 pueda profundizar sin re-etiquetar y sepa cuándo su fila no es comparable; desglose por `data_origin` **agrupando por consulta y contando por juicio**, con la recuperación siempre sobre los 1.168 documentos porque restringir el corpus a la porción real daría 436 y **inflaría** el número del titular; y `GET /v1/evals/runs`, publicado en el `openapi.json` congelado desde C02 y con un stub que nombra a C24 por escrito, dejando por fin de ser stub **sin mover el contrato**)*

---

## Resumen de Épicas

| Épica | Descripción Breve | User Stories Estimadas |
|-------|-------------------|------------------------|
| **EP1** | Gestión de Productos | 7 |
| **EP2** | Gestión de Inventario | 6 |
| **EP3** | Registro de Ventas | 4 |
| **EP4** | Reconocimiento de Imágenes con IA | 1 |
| **EP5** | Gestión de Devoluciones | 3 |
| **EP6** | Gestión de Métodos de Pago | 3 |
| **EP7** | Autenticación y Gestión de Usuarios | 6 |
| **EP8** | Gestión de Puntos de Venta | 5 |
| **EP9** | Consultas y Reportes | 4 |
| **EP10** | Gestión de Componentes de Joyas | 8 |
| **TOTAL MVP** | | **47** |

### Épicas del Proyecto Final de IA

Se miden por *changes* de OpenSpec, no por número de historias: la serie `HU-AIENG-[NNN]` es plana y se genera a demanda por change.

| Épica | Descripción Breve | Changes | Ruta crítica |
|-------|-------------------|---------|--------------|
| **EP11** | Plataforma del Servicio de IA | C01, C02, C03, C05, C17 | 🔴 completa |
| **EP12** | Corpus y Enriquecimiento del Catálogo | C06a (hecho), C06b (hecho), C08 (hecho), C09 (hecho), C10 (hecho), C11 (hecho), **C23 (hecho)**, **FIX1 (hecho)** | 🔴 parcial |
| **EP13** | Familias de Producto y Desambiguación | C07 (hecho), C18a (hecho), C18b (hecho), **C28 (hecho)** | 🟢 completa |
| **EP14** | Búsqueda Semántica Híbrida | C12, C13, C14, C15, C16, C20, C21, **C22**, **C25** (hechos), **C41 (archivado 26 sep)** *(no previsto)*, **C43 (27 sep)** *(no previsto: corrige el recuento de C41, que marcaba en rojo un despliegue sano)* | 🟠 **parcial — reabierta** |
| **EP15** | Venta Asistida, Sustitutos y Agentes | **C26 (archivado)**, ~~C27~~ *(cortado 12 sep)*, **C30a (archivado 13 sep)**, **C30b (archivado 14 sep)** *(partidos el 13 sep)*, **C31 (archivado 16 sep)**, **C32a (archivado 20 sep)**, **C32b (archivado 21 sep)** *(partidos el 20 sep)*, **C34 (archivado 22 sep)**, **C36 (archivado 24 sep)**, **C40 (archivado 25 sep)** *(no previsto)*, **C40_FIX (archivado 26 sep)** *(fuera de la numeración C: corrige a C40)*, **C42** *(archivado el 27 sep, 75/75 — no previsto; da superficie al único pilar del PF que no la tenía)* | 🟠 **parcial — reabierta** |
| **EP16** | ~~Inventario Asistido y Señales de Demanda~~ | ~~C19, C29, C33, C35, C37~~ | ⛔ **anulada 31 ago** |
| **EP17** | Evaluación y Observabilidad de IA | C04 (hecho), **C24 (hecho)**, ~~C38~~ *(retirado 27 sep)*, **C39a**, **C39a-bis** y **C39b** *(partidos el 27 sep; los tres archivados)* · *(C25 amplía el arnés y el golden set desde EP14)* | 🟢 **completa** |
| **TOTAL PF** | | **52 fichas · 45 vivas** (5 anuladas, 1 cortada, 1 retirada) — **45 archivadas, 0 pendientes** | |

> **Cerrado el 2026-09-27, al archivar C39b — y desde aquí cada cifra dice su unidad, que es lo que
> faltaba.** **La cola del Proyecto Final queda vacía.** Las notas de abajo se conservan como registro
> fechado y **no se reescriben**; lo que esta entrada añade es el **criterio**, porque las cifras que
> circulaban —«40», «43» y «44 archivadas» en este documento, «74 · 32 · 41» en la ficha del plan— no se
> contradecían por descuido: **contaban unidades distintas sin decir cuál**.
>
> | Unidad | Cifra | Cómo se comprueba |
> |---|---:|---|
> | **Fichas** del plan del Proyecto Final | **52 · 45 vivas** (5 anuladas, 1 cortada, 1 retirada) — **45 archivadas, 0 pendientes** | las 45 filas de la tabla maestra del §2 del plan, más las 7 conservadas como registro |
> | **Directorios** en `openspec/changes/archive/`, total | **79** | `ls openspec/changes/archive/ \| wc -l` |
> | …del MVP | **33** | los 32 con fecha `< 2026-08-03` **más** `barcode-qr-scanning`, del MVP **por contenido** |
> | …del **Proyecto Final** | **46** | los 47 con fecha `>= 2026-08-03` **menos** ese |
>
> **Las dos unidades no coinciden ni deben coincidir**, y la distancia tiene **un solo nombre**:
> `fix-boot-drain-retries-both-drains`, el seguimiento de C43, que es un directorio de archivo **sin ficha
> propia**. Éste es el documento que cuenta **fichas**; el plan publica las dos.
>
> **De dónde salen las 52 y por qué no son las 48 de la fila anterior**, dicho para que la aritmética no
> haya que reconstruirla: **48 + 2** por partirse C39 en C39a, C39a-bis y C39b, **+1** por C43, y **+1**
> por `C40_FIX`, que **no tenía fila en la tabla maestra** y aparecía sólo en prosa — el defecto que
> obligaba a que todo recuento hecho contra esa tabla se quedara corto en uno y se corrigiera después
> «sumándole `C40_FIX`», exactamente como hace la nota de más abajo. **C39b le añadió su fila.** Y las
> vivas: **42 + 2 + 1 = 45**, que es el número exacto de filas de la tabla — C38 sale de las vivas al
> retirarse y pasa a contarse con las anuladas y la cortada.
>
> Criterio completo y su derivación en el
> [informe de cierre](Proyecto%20Final%20AIEng/informes/c39b-implementation-measurements.md), §2.
>
> **Actualizado el 2026-09-27, al archivar C42 — y el recuento sigue cuadrando por dentro.**
> **41 archivadas y 2 pendientes** —C38 y C39, en ese orden—, y **48 fichas · 42 vivas**: **C42 pasa de
> pendiente a archivada** (`add-frontend-agent-panel`, EP15, no previsto en ninguna ola, **75/75 tareas**).
> La aritmética, que conviene dejar escrita: 48 fichas menos 5 anuladas y 1 cortada dan **42 vivas**; de
> ésas, 2 están pendientes y **40 archivadas**; y las **41** de la fila salen de sumarle **C40_FIX**, que
> está archivado y **fuera de la numeración C**, igual que `FIX1` y `C25bis` están dentro de ella. Ésa es
> exactamente la unidad que faltaba para que «41 vivas» y «40 + 2» no sumaran lo mismo.
>
> **El orden de las dos pendientes no es preferencia, es la cadena de prompts.** C40 subió a `assist/v5`
> y movió la fase de la abstención; **C42 subió la tarea del agente a `assist/v6`** —y con un hallazgo
> que conviene llevarse a C38: medido antes y después, la caída del argumentario retirado del **13,1 %
> al 1,2 % NO es atribuible a v6**, y el informe de C42 nombra los confundidores—; y sólo con los dos
> hechos las cifras de generación de C38 describen los prompts que se sirven. De ahí que C42 ganara a
> C38 de prerrequisito, anotado ya en la ficha de C38 del
> [plan de changes](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), que **manda sobre
> este resumen**.
>
> **Actualizado el 2026-09-26, al explorar C40_FIX — y de paso se corrige el recuento, que el archivado
> de C40 dejó sin mover.** **39 archivadas y 2 pendientes** —C38 y C39, en ese orden—
> contadas contra `openspec/changes/archive/`. **C40 se archivó el 25 de septiembre y este documento
> seguía contándolo como pendiente**: el commit del archivado repuntó sus enlaces al árbol de archivo y
> no tocó ni la tabla ni las cifras, así que la fila de EP15 lo daba por «abierto el 24 sep» un día
> después de cerrarse. Es la misma clase de desfase que el change que ahora se abre viene a corregir en
> las specs — documentación bien formada y falsa—, sólo que aquí la cazó una relectura y no una prueba
> manual.
>
> **Corregido el 2026-09-26, al enriquecer C41: eran 3 pendientes y no 2.** La fila decía **2** y
> **C41 no aparecía en ninguna parte de este documento**, ni en la tabla ni en EP14, pese a estar
> abierto desde el 25 de septiembre — el mismo desfase que la nota de arriba acababa de corregir para
> C40, repetido una ficha después. Las pendientes son **C38, C39 y C41**, contadas contra el
> [plan de changes](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md), que ya las daba
> así y **manda sobre este resumen**. Las 41 vivas no se mueven: C41 ya estaba dentro de ellas en el
> plan. **Y C41 entra en EP14, no en EP15** como declaraba su ticket: modifica `pos-projection`, que
> nació en C22.
>
> **C40_FIX (`c40-fix-all-shops-scope-unreachable`) es lo que sale de las pruebas manuales sobre el
> entorno levantado tras cerrar C40**, con historia ([HU-AIENG-040-FIX](Historias/AI-Eng/HU-AIENG-040-FIX.md))
> y ticket ([T-AIENG-040-FIX](../openspec/changes/archive/2026-09-26-c40-fix-all-shops-scope-unreachable/ticket.md)). Va
> **fuera de la numeración C**, como `FIX1` y `C25bis`: no sale de la descomposición original sino de una
> consecuencia de otro change. **No entra en la ruta crítica** —la cadena que queda es `C38 → C39`— pero
> **arrastra urgencia propia**: una spec viva afirma ahora mismo algo que el sistema no hace, y cada
> change que se archive encima consolida esa afirmación. Y **comparte zona con C38**, así que los dos no
> se abren en paralelo.
>
> **Lo que corrige no es un defecto de implementación: es que el ámbito «todas las tiendas» que C40
> construyó entero no se puede alcanzar desde la pantalla, y que la spec afirma lo contrario de lo que el
> sistema hace.** El detalle está en EP15; lo que conviene retener aquí son las dos lecciones de método.
> **Una:** `openspec validate --all --strict` **no puede cazar este defecto** — las tres specs
> implicadas están bien formadas y lo que falla es su contenido, así que la puerta de verdad es la
> comprobación manual por la interfaz. **Dos:** un requisito transversal del tipo *«todo estado
> especificado debe ser alcanzable»* se consideró y **se descartó**, porque no produce ningún escenario
> que un runner pueda fallar; la lección va a la documentación de verificación y a la spec van escenarios
> fallables.
>
> **Actualizado el 2026-09-24, al explorar C40 — y EP15 se reabre el mismo día en que se cerró.**
> **37 archivadas y 3 pendientes** —**C40**, C38 y C39, en ese orden—, contadas contra
> `openspec/changes/archive/`: abrir no mueve el recuento de archivadas y sí el de pendientes. **EP15
> pasa de 🟢 completa a 🟠 parcial** unas horas después de haberse cerrado, y el motivo no es un cambio
> de opinión: **la tarea 8.5 de C36 —la comprobación en demo— destapó que el panel de búsqueda asistida
> llevaba todo el proyecto sirviendo por su ruta degradada**, porque `AiSearch:EnabledByDefault` está
> ausente de todos los `appsettings`, y que **en esa ruta los filtros se descartan en silencio**. Los
> tres tropiezos de aquella sesión son el mismo problema —**una capacidad apagada que la interfaz
> presenta como encendida**— y dos de los tres avisan; el de los filtros no avisa de nada.
>
> **C40 (`add-frontend-free-query-panel`) es lo que sale de ahí**, con historia
> ([HU-AIENG-040](Historias/AI-Eng/HU-AIENG-040.md)), ticket
> ([T-AIENG-040](../openspec/changes/archive/2026-09-25-add-frontend-free-query-panel/ticket.md)) y **dos informes de
> exploración del mismo día**: uno contra el servicio real —**siete hallazgos, diez decisiones, cuatro
> preguntas cerradas**— y otro contra el código de las tres capas —**cuatro hallazgos más, siete
> decisiones, dos contradicciones internas resueltas**—, con la tabla de estados de la pantalla aparte
> ([c40-exploration-decisions.md](Proyecto%20Final%20AIEng/informes/c40-exploration-decisions.md) ·
> [c40-m1-panel-states.md](Proyecto%20Final%20AIEng/informes/c40-m1-panel-states.md)). **Convierte el
> panel de C16 en M1** —la pregunta libre sin pieza— en vez de construir pantalla nueva, y con ello
> **los tres modos de la venta asistida llegan por fin al operario**. **Cierra tres limitaciones
> declaradas**: la §15.12, la §15.13 y la limitación 3 de C34, ésta con un campo que .NET ya calcula y
> descarta.
>
> **El hallazgo que gobierna su línea de corte, y que sólo aparece leyendo el código:** **.NET rechaza
> M1 hoy por construcción.** `AiGatewayClient` lanza `ArgumentException` sin `product_id` porque
> `PitchPlaceholderResolver` retira el argumentario **siempre** que no hay ancla, y el prompt `assist/v3`
> ordena escribir los marcadores de precio y stock **también en las tres tareas de consulta libre**
> —medido en C30b: **147 de 213** y **188 de 213**—. Las 42 consultas del informe se midieron con `curl`
> **contra Python**, saltándose esa etapa, así que su «37 respuestas con argumentario» no dice nada de lo
> que el operario vería. **Sin su tramo 2 completo, C40 entregaría un panel asistido sin prosa**: la
> misma avería que vino a corregir. De ahí que `assist/v5` y la causa dura de puerta sean prerrequisitos
> declarados y no mejoras.
>
> **Y C40 va antes de C38**, que es orden obligado y no disciplina de rama: sube el prompt a `assist/v5`
> y **mueve la fase de la abstención**, así que unas cifras de C38 tomadas antes describirían un prompt
> sustituido y una fase movida. La cadena que queda es **`C40 → C38 → C39`**.
>
> **Actualizado el 2026-09-24, al archivar C36.** **37 archivadas y 2 pendientes** —C38 y C39—, contadas contra `openspec/changes/archive/`: archivar mueve el recuento y abrir no, que es la distinción que las notas de abajo llevan escrita cinco veces. **EP15 queda 🟢 completa**: con C36 archivado no le queda ningún change, y los dos pendientes son de EP17. Al archivarse **nace la capability viva `sales-assist-card`** con 11 requisitos y 38 escenarios, y **`assisted-search-panel` crece de 14 a 15**: la fila de resultados gana la acción secundaria hacia la ficha, que no sustituye ni bloquea la selección para venta y **no reporta selección a la telemetría**, porque ver una ficha no es elegir la pieza. **La verificación previa al archivado no encontró ningún defecto de implementación y corrigió dos artefactos del propio change**: el escenario de la entrada de escaneo afirmaba que la ficha *«se abre para el punto de venta de esa venta»* cuando `scan.tsx` no tiene ninguno —insatisfacible, y a punto de congelarse como spec viva—, y el cambio de punto de venta con la ficha servida emitía otra petición con test propio y sin requisito que lo amparara. También midió **la cobertura, que el apply no había medido**: del **84 % al 100 % en sentencias** sobre el código nuevo, con la tabla de copia al 100 %. Detalle en [c36-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c36-implementation-measurements.md).
>
> **Ampliado el 2026-09-22, al implementar C36.** Los recuentos **no se mueven** —**36 archivadas y 3 pendientes**: C36, C38 y C39— porque implementar no es archivar; el recuento se mueve al archivar C36. EP15 sigue 🟠 parcial hasta entonces. C36 entrega **la única pantalla del Proyecto Final que pone la capa RAG delante de una persona** y cierra la cadena `C30a → C34 → C36`: ruta propia `/sales/new/assist/:productId` con carga perezosa y tres entradas, una petición por visita sin reintento automático, desambiguación por familia **sin preselección** con un botón de venta por miembro, seis `pitchStatus` pintados como cinco mensajes sin fundir `ai_unavailable` con `not_generated`, citas con `claimScope` distinguido y ocultas cuando el argumentario se retira, caja de pregunta acotada a 500 caracteres y siempre en el cuerpo, y los cuatro desenlaces de sustitutos distinguibles. **132 tests nuevos, cero nombres nuevos en rojo** contra la línea base. **Es el undécimo change consecutivo cuya implementación refuta algo escrito antes**, y esta vez lo refutado es la propia guía de pruebas: la línea base del frontend **oscila entre 113 y 114** porque `family-review.test.tsx` tiene un test dependiente del orden, así que la afirmación de que aquí el conjunto de fallos es estable entre ejecuciones era demasiado fuerte. Detalle en [c36-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c36-implementation-measurements.md). **Deja una limitación nueva declarada**: la ficha **no tiene telemetría**, así que su uso no es medible.
>
> **Ampliado el 2026-09-21, al abrir C34.** Los recuentos **no se mueven** —**35 archivadas y 4 pendientes**: C34, C36, C38 y C39— porque abrir no es archivar. **La fila TOTAL sí se corrige**: seguía diciendo 34 · 5 desde el archivo de C32b, aunque la nota de debajo ya daba 35 · 4. Con C32b archivado, **C34 es el único nodo libre del grafo**: desbloquea C36 y es el último prerrequisito que le falta a C38, que queda libre en cuanto C34 se archive. La cadena que falta es **`C34 → C36`** y **`C34 → C38 → C39`**.
>
> **Actualizado el 2026-09-21, al archivar C32b.** **35 archivadas y 4 pendientes** — C34, C36, C38 y C39 —, contadas contra `openspec/changes/archive/`: archivar mueve el recuento y abrir no. EP15 sigue 🟠 parcial, porque le quedan C34 y C36. C32b se archivó tras una verificación independiente que corrigió su cifra central —el sobrecoste es ×3,0 y no ×7,6— y sincronizó dos specs: nace `sales-assistant-agent` y se modifica `sales-assistant-tools`.
>
> **Actualizado el 2026-09-20, al archivar C32a y abrir C32b.** **34 archivadas y 5 pendientes** — C32b, C34, C36, C38 y C39 —, contadas **contra `openspec/changes/archive/`** y no contra la nota anterior: el directorio tiene 35 entradas del Proyecto Final menos `barcode-qr-scanning`, que es del MVP. **Archivar sí mueve el recuento y abrir no**, que es la distinción que las notas de abajo ya dejaron escrita dos veces. La cadena crítica queda en **`C32b → C38 → C39`** por un lado y **`C34 → C36`** por el otro, con **C32b como el único nodo que taponea el cierre del proyecto**.
>
> **Ampliado el 2026-09-20, al abrir C32b — su exploración cierra seis decisiones y refuta cinco supuestos de la ficha.** **C32b** (`add-sales-assistant-agent-loop`) se abre con historia ([HU-AIENG-032b](Historias/AI-Eng/HU-AIENG-032b.md)) y ticket ([T-AIENG-032b](../openspec/changes/archive/2026-09-21-add-sales-assistant-agent-loop/ticket.md)), en la rama `c32b-add-sales-assistant-agent-loop`. **Lo que la exploración refuta, por orden de consecuencia:** **(1)** la propuesta de *«clasificar todos los turnos»* cuesta **O(N²)** con contrato sin estado —N clasificaciones en la petición N, 15 llamadas en una conversación de cinco turnos en vez de 5— y **rompe desde el turno 8 el techo de ocho llamadas que la propia ficha declara**; se sustituye por **una clasificación sobre el turno que se contesta**, con el rechazo cortocircuitando en cualquier turno, la repregunta movida al bucle vía `pedir_aclaracion` y el `index` descartado, porque **el agente elige su propia tool**: eso es tener un bucle. **(2)** El turno de seguimiento es **elíptico** —`«¿y en dorado?»` clasifica como insuficiente— y la matriz de confusión de C31 se midió sobre consultas sueltas, así que la repregunta tenía que salir del clasificador o el sistema preguntaría por un eje que la conversación acaba de responder. **(3)** **No existe puerto de *function calling***: `AssistLlm` está fijado a `response_format=AssistPitch`, de modo que el change añade un **tercer puerto, tercera credencial y tercera variable de modelo**, y no «sólo el bucle». **(4)** El **5×** que predicen los apuntes de S12 es el multiplicador de **tokens** y se cumple; el coste en dinero sale **~19×** porque se le suma un **×4 de modelo** que es **elección separable y reversible** — de ahí que la pasada corra **los dos brazos**, `gpt-4o` y `gpt-4o-mini`, sobre el mismo conjunto. **(5)** La ficha escribía cuatro presupuestos y **faltaba el de reloj de pared**, que es el único que un mostrador siente; pasan a ser **seis**, con el de contexto en caracteres evaluado antes de llamar y el de tokens **post-hoc**, porque hacerlo cumplir antes exigiría un tokenizador como dependencia nueva.
>
> **Y una decisión que no estaba en ninguna ficha y que es el riesgo mayor del change: el muro de contaminación.** El §11.4 pide la ablación sobre el **mismo golden set**; iterar el prompt del agente contra él —o contra escenarios multi-turno, que son los 20-25 de C38— haría nacer inservible la cifra que el PF puntúa. Se levantan **dos instrumentos y ninguno es de evaluación**: un **set de carga** de ~60-100 transcripciones **sintéticas generadas**, que mide p50/p95 de tokens y de reloj, curva de crecimiento del contexto y coste por brazo sin juzgar calidad; y un **set de calibración** de ~15-20 escritas a mano **con herramienta esperada por turno**, declarado *calibration-only*, que responde las dos preguntas que C32a dejó abiertas —si la **granularidad de seis** es la correcta y si la **etiqueta cualitativa se queda corta** para decidir el pivote a sustitutos—. **El golden set de C24 no se toca.** Los dos tamaños difieren por una razón que no es presupuestaria: a temperatura cero repetir un escenario devuelve casi lo mismo, así que **las repeticiones no compran resolución de p95** y el p95 necesita variedad, mientras que la verdad de terreno necesita lo contrario. Hay datos reales para ejercer el pivote: C25 midió **411 candidatos agotados de 3.774** y en **MAO-AIR 13 de 48** consultas enseñaban una pieza agotada en el top-5.
>
> **Actualizado el 2026-09-20, al explorar C32: se parte en C32a y C32b.** Las archivadas **no se mueven** —siguen **33**—, pero los pendientes pasan de **5 a 6**: C32a, C32b, C34, C36, C38 y C39. **Partir sí mueve el recuento de fichas**, al revés que abrir: **45 fichas y 39 vivas**. El corte es el mismo que funcionó en C30 —**la mitad que no llama a ningún proveedor va primero**—: **C32a** entrega las seis tools, el registro, los esquemas de *function calling* y el invariante de solo-lectura comprobado por introspección; **C32b**, el bucle, los tres presupuestos, `partial: true`, la traza y la ruta **`POST /v1/assist/agent`**. Y vuelve a dejar una ablación gratis: *pipeline determinista contra agente*, mismo golden set y mismas tools, que es la fila que el §11.4 del diseño pide y la que desaparecería si el bucle sustituyera al pipeline en vez de convivir con él. **Tres supuestos de la ficha se caen contra el árbol**: `consultar_disponibilidad` era la única de las seis **sin servicio detrás** —no hay ruta puntual en .NET y la única arista de vuelta es el feed paginado con `X-Index-Feed-Key`—, el **techo de 3 llamadas de C31 no se hereda como cifra** sino como patrón (pasa a 8 por petición, y ni el de tokens ni el de embeddings los escribía nadie), y `QTY_BUCKETS` son **dígitos**, así que el bucket crudo en el contexto del modelo es una cifra de stock. Detalle y las cuatro decisiones de arquitectura, en el §0 del [plan de changes](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md). **C32a se abre el mismo día**, con historia y ticket, y eso **no mueve los recuentos**: abrir no es archivar.
>
> **Ampliado el 2026-09-14, al abrir C31.** Los recuentos **no se mueven** —siguen **32 archivadas y 6 pendientes**, con C31 entre los pendientes— porque **abrir no es archivar**, que es exactamente la lección que las dos correcciones de abajo dejaron escrita el mismo día. C31 entra **antes que C34** por decisión explícita: `/v1/assist/sale` sigue teniendo **cero consumidores** —`IAiGatewayClient` no lo implementa— y ésa es la ventana en la que cualquier movimiento de contrato es gratis, la misma razón que C30a usó para regenerar `openapi.json` sin coste.
>
> **Recuento actualizado el 2026-09-16, al archivar C31.** **33 archivadas y 5 pendientes** — C32, C34, C36, C38 y C39. **Archivar sí mueve el recuento**, al revés que abrir, que es la distinción que las dos notas de abajo dejaron escrita.
>
> **Recuento corregido el 2026-09-14.** **32 archivadas y 6 pendientes** — C31, C32, C34, C36, C38 y C39. La fila decía 30 · 8 e incluía a **C30a** entre los pendientes: quedó desfasada por unas horas, porque la nota se escribió cuando C30a estaba implementado y sin archivar, y se archivó ese mismo día. **Y volvió a pasar con C30b, en el mismo día y por el mismo motivo**: la nota decía 31 · 7 con C30b entre los pendientes, escrita mientras estaba implementado y sin archivar. El patrón es el que es: una cifra de archivadas escrita el mismo día en que un change se archiva nace con horas de vida, y lo que la corrige no es escribirla con más cuidado sino contarla **después** del archivado. Coincide ahora con el §2 del plan de changes.
>
> **Recuento actualizado el 2026-09-13.** Las **44** salen de **42 numeradas** —C01–C39, con C06, C18 y ahora **C30** partidas en dos— más **`FIX1`** y **`C25bis`**, las dos deliberadamente fuera de la numeración C. El desglose 30 archivadas + 8 pendientes son las **38 vivas**; los 8 pendientes son **C30a**, **C30b**, C31, C32, C34, C36, C38 y C39. *(La fila anterior decía 43 · 37 · 29 archivadas: le faltaba C28, archivado el 13 de septiembre, y es previa al desdoble de C30.)*
>
> **Recuento actualizado el 2026-09-05.** Las 42 fichas son 41 numeradas —C01–C39 con C06 y C18 partidas en dos— más **`FIX1` (`fix-enrichment-vocabulary-gaps`)**, que hasta ahora no aparecía en esta tabla: nació de un hallazgo de C18a, va deliberadamente **fuera de la numeración C** y pertenece a EP12 por zona (`enrichment/`, prompts y espejo del frontend). Está **detrás de C22 y antes de que C24 etiquete**, porque `preprocessing_id` sigue siendo `source-text/v1` y no delataría el cambio de vocabulario.
>
> **Ampliado el 2026-09-05, al explorarlo.** FIX1 abrió el mismo día con historia ([HU-AIENG-FIX1](Historias/AI-Eng/HU-AIENG-FIX1.md)), ticket y mediciones ([fix1-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/fix1-exploration-measurements.md)). La exploración **corrigió su ficha en dos puntos**: la población es de **22 productos y no de 11** —nueve de ellos están mal tipados, que es peor que estar sin tipar porque el filtro de categoría es duro— y su criterio de extremo a extremo **ya se cumplía antes del change**, porque la rama léxica de C21 alcanza las once diademas por el nombre. Es el tercer change consecutivo cuya exploración refuta lo escrito antes, tras C21 y C22.
>
> **Ampliado el 2026-09-06, al abrir C24.** **C23 se archivó** ese mismo día y **C24 (`add-eval-harness-golden-set-and-baselines`) pasa a en curso**, con historia ([HU-AIENG-024](Historias/AI-Eng/HU-AIENG-024.md)), ticket y decisiones ([c24-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c24-exploration-measurements.md)). Recuento: **25 archivadas, 12 pendientes**. Se elige por la regla 2 del §5 del plan llevada a su extremo: es **el único change pendiente que bloquea a dos** —C25 y C38— y el siguiente eslabón de la cadena crítica `C21 → C24 → C25 → C26 → C34 → C36`. Es el **quinto change consecutivo cuya exploración refuta lo escrito antes**, tras C21, C22, FIX1 y C23, y lo hace en cuatro puntos: el golden set baja de 60-70 a 48 juzgadas **derivadas desde los pleitos y no desde la ficha**, `v0-lexico` se parte en dos filas porque el repositorio contiene dos buscadores léxicos y sólo uno es anterior al trabajo de IA, `v0-cag` deja de ser una fila de calidad para ser la prueba medida de por qué existe RAG, y el change abre **dos desviaciones fuera de su zona** —el desempate determinista en `retrieval/search.py` y el posible cambio de defaults en `Settings`—. **Y su primera regla la escribió C23 unas horas antes:** el sustituto *offline* con el que aquel change calibró su umbral resultó dejar el mecanismo de abstención inoperante e **invirtió su propio veredicto sobre la rama léxica** al re-medirse contra el proveedor real, así que C24 mide contra el proveedor y el índice reales, nunca contra un sustituto.
>
> **Ampliado el 2026-09-06, al abrir C23.** **C23 (`add-knowledge-corpus-and-indexer`) pasa a en curso**, con historia ([HU-AIENG-023](Historias/AI-Eng/HU-AIENG-023.md)), ticket y mediciones ([c23-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c23-exploration-measurements.md)). Los recuentos de la tabla no se mueven —sigue habiendo 24 archivadas y 13 pendientes— porque abrir no es archivar. Es el **cuarto change consecutivo cuya exploración refuta lo escrito antes**, tras C21, C22 y FIX1, y el primero que refuta **al plan y no a su propia ficha**: el corte pre-autorizado del §13.4 fijaba el alcance en 15 documentos, pero lo expresó en documentos cuando el objetivo del diseño está en chunks. Se elige por desbloqueo y no por calendario, como manda la regla 2 del §5 del plan: **no está en la cadena crítica** `C21 → C24 → C25 → C26 → C34 → C36`, pero es prerrequisito **único** de C30 y con él de toda la rama de generación `C30 → C31 → C32 → C38 → C39`, así que entra por el lado sin taponar a nadie.
>
> **Ampliado el 2026-09-11, al abrir C25.** **C25 pasa a en curso** y se **renombra** de `add-business-signals-ranking` a **`recalibrate-ranking-and-abstention`**, porque el nombre anterior describía un tercio de su alcance; el número se conserva, ya que renumerar rompería las referencias de C26 (`prereq C22, C25`) y C27 (`C10, C25`) a cambio de nada. Los recuentos no se mueven —siguen **26 archivadas y 11 pendientes**— porque abrir no es archivar. Es el **sexto change consecutivo cuya exploración refuta lo escrito antes**, tras C21, C22, FIX1, C23 y C24, y el primero que refuta **dos puntos de su propia ficha con una medición** en lugar de reencuadrarlos: la penalización de variante ambigua —el reparto real de familias de C18a acota la inundación a **2 de 156**, el panel ya pinta `Talla {variantLabel}`, `variante-talla` ya es la mejor categoría con 0,830 y diversificar **baja** el nDCG@5 cuando las hermanas son grado 2— y la calibración de `1-2` frente a `3+`, que **no tiene función objetivo posible** porque con la ganancia efectiva ninguno de los dos pierde grado. **Y encontró un defecto que vale más que todo su alcance original:** la fusión de C21 **no fusiona, concatena** — los 60 documentos léxicos ganan al #1 vectorial **siempre**, medido en el run publicado como la posición 33 en tres consultas distintas, con los 32 anteriores **sólo léxicos** y la cola conservando **exactamente** el orden vectorial. El óptimo que el barrido de C24 encontró (`wC` 0,75-1,0) no era un peso mejor: era **el intervalo de los umbrales de cruce de la fórmula**. Y la regla de decisión que bloqueó aquel cambio se reformula con argumento y fecha **antes** de re-medir, porque su partición de ajuste tiene **6 de 8** consultas en el techo del nDCG@5, **las 8** en el de Recall@5, P@3 y MRR, y **7 de 8** salidas de la lista con la que se calibró la rama léxica: una partición que C24 declaró contaminada (0,942 contra 0,535) es evidencia de sobreajuste del titular, **no un grupo de control**. Historia [HU-AIENG-025](Historias/AI-Eng/HU-AIENG-025.md), ticket [T-AIENG-025](../openspec/changes/archive/2026-09-12-recalibrate-ranking-and-abstention/ticket.md), mediciones en [c25-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c25-exploration-measurements.md).
>
> **Actualizado el 2026-09-11, al archivar C24.** **C24 (`add-eval-harness-golden-set-and-baselines`) pasa a hecho** y con él la cadena crítica arranca en **C25**. Recuento: **26 archivadas, 11 pendientes**. El change entrega el juez imparcial que cuatro changes archivados prometieron por escrito: 48 consultas juzgadas a mano con relevancia graduada, y un veredicto que **refuta la rúbrica de C21** — aquélla daba 67 de 120 a la rama vectorial contra 107 de la léxica, y contra un juez que no es parte la vectorial (nDCG@5 **0,548**) bate a la línea léxica (**0,454**), con el híbrido vivo en **0,603** y el buscador que la joyería tenía en **0,082**. La regla de cambio de defaults, escrita antes de medir, **bloquea** mover `wC` a 1,0 pese a un +0,057 global: empeora en la partición de ajuste, que es el caso incómodo para el que la regla se escribió. Informe en [c24-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c24-implementation-measurements.md).
>
> **Actualizado el 2026-09-12, al archivar C25.** **C25 (`recalibrate-ranking-and-abstention`) pasa a hecho** y con él la cadena crítica arranca en **C26**. Recuento: **27 archivadas, 10 pendientes**. Al archivarse **nacen dos capacidades vivas** — `business-signals-ranking` (la disponibilidad como reordenación blanda calibrada contra el golden set) y `retrieval-abstention` (la regla que decide **si** contestar) — y se modifican `hybrid-fusion`, `pos-projection` y `retrieval-evaluation`. El change entrega lo que su exploración encontró y no lo que su ficha pedía: **la fusión de C21 no fusionaba, concatenaba**, y componerla en **dos etapas con pesos por rama** vale **+0,083** sobre la línea base en la lectura que decide (nDCG@5 de 0,673 a **0,740**). La ponderación por cobertura aporta **+0,128** en `descripcion-sin-anclaje` y **cero exacto** en las otras siete categorías — la predicción falsable de su diseño, confirmada — y convierte la elección del cociente de rama de acantilado en meseta (recorrido del barrido de 0,070 a 0,007). La señal de disponibilidad retira el **91 %** de las piezas agotadas del top-5. **Se retiran tres cosas por medición y no por argumento:** la rotación sale del orden (como desempate estricto decidía **0 pares**; como clave particionaba, invirtiendo 11.067), la variante ambigua (es presentación, pasa a C30/C36) y la variante binaria de la regla adaptativa (indistinguible de la continua). **C25 no deja ni un peso calibrado:** `rho = 1,0` es de principio y medido como robusto, y el de disponibilidad decide su **signo y no su valor**. La abstención resultó **no caber en un escalar** — el rango de las imposibles cae **dentro** del de las contestables — así que la regla adoptada es **relativa por consulta** y lee la *forma* del perfil. **Tres listones no se alcanzan y se declaran en vez de cerrarse:** `Recall@5` **0,758** contra 0,85, abstención **0,150** contra 0,80, y `v3` no bate a `v2b` por el margen (**+0,030** operativo) aunque cumple su propia regla de adopción. Queda **C25bis** (`clean-plain-fusion`) desbloqueado, que es quien cierra EP14.
>
> **Actualizado el 2026-09-12, al cortar C27 y abrir C26.** **C27 sale del alcance con cinco mediciones** (detalle en EP15 y en [c27-cut-measurements.md](Proyecto%20Final%20AIEng/informes/c27-cut-measurements.md)) y **C26 pasa a en curso**. Recuento: **27 archivadas, 10 pendientes** — C25bis, C26, C28, C30, C31, C32, C34, C36, C38 y C39.
>
> **Y el hueco que el corte deja a la vista, que gobierna el orden de lo que queda:** `ai-service/src/jbg_ai/assist/` **no existe**. C30 (generación con citas), C31 (guardrails y router de intención) y C32 (bucle agéntico) están a cero, y son lo que el rubro del PF nombra por su nombre — *«escala desde un prototipo CAG hasta un sistema RAG **con agentes**»*. Ésa, y no complementarios, es la deuda grande de EP15.
>
> **Actualizado el 2026-09-12, al archivar C26.** **C26 (`add-substitutes-retrieval`) pasa a hecho** y con él la cadena crítica deja de arrancar en C26 y arranca en **C34**. Recuento: **29 archivadas, 8 pendientes** (C28, C30, C31, C32, C34, C36, C38 y C39) — suben dos de golpe porque `C25bis` se archivó el mismo día. Con C26 cae el **último 501 cerrable** del contrato congelado: `/v1/inventory/propose` sigue respondiendo 501, pero por una rama anulada el 2026-08-31 y ya declarada como limitación, no por falta de turno. Nace la capability viva `substitutes-retrieval` con diez requisitos, y `vector-retrieval` pierde por escrito la obligación de que la ruta siguiera devolviendo 501. **Lo que C26 no se lleva** y queda anotado en la ficha de **C34**: la exclusión por falta de stock, porque la autoridad sobre el stock es de .NET y en Python la disponibilidad degrada y nunca elimina.
>
> **Ampliado el 2026-09-12, al abrir C28.** **C28 (`add-profile-review-ui-and-metrics`) pasa a en curso**, con historia ([HU-AIENG-028](Historias/AI-Eng/HU-AIENG-028.md)), ticket ([T-AIENG-028](../openspec/changes/archive/2026-09-13-add-profile-review-ui-and-metrics/ticket.md)) y mediciones ([c28-exploration-measurements.md](Proyecto%20Final%20AIEng/informes/c28-exploration-measurements.md)). Los recuentos no se mueven —siguen **29 archivadas y 8 pendientes**— porque abrir no es archivar; sí se corrige la fila **TOTAL PF**, que había quedado en 27/10 al archivarse C26 y `C25bis` el mismo día. Se elige **sin estar en la cadena crítica y sin desbloquear a nadie**: C28 es hoja del grafo, y entra porque el §13.4 la marca como *«nunca se recorta»* y el §16 la convierte en una casilla marcada o vacía, no en un grado — el checklist pide literalmente *«métricas de revisión humana del enriquecimiento»* y el §11.5 advierte de que esos números *«no existen sin la vía revisada»*. Es el **octavo change consecutivo cuya exploración refuta lo escrito antes**, tras C21, C22, FIX1, C23, C24, C25 y C26, y lo hace en el punto que sostenía su propia ficha: **el enrutado híbrido de la decisión 5 no acota la cola**. Medido sobre los 1.200 perfiles, `size_label` es el **único** campo que el extractor marca alguna vez `rule` (539 de 1.200); `piece_type`, `materials` y `stone_type` salen **siempre** como `inferred`, así que el 100 % de los productos entra en la cola con dos o tres campos sensibles cada uno y la política del §7.8 filtra correctamente sin descartar a nadie. **Y la exploración destapó un error que ninguna métrica del proyecto puede ver hoy:** la confianza no es una probabilidad sino un escalón de evidencia —`0,85` significa que la frase del vocabulario está literalmente en el texto—, de modo que la heurística **solo caza falsos positivos y es ciega por construcción a las omisiones**. Medidos **94 productos** cuyo texto nombra un material que el extractor no extrajo (`hilo` 60, `perla` 35, `plata` 3), y **81 de ellos —el 86 %— están en el estrato de máxima confianza**: una cola ordenada por confianza ascendente, que es el orden que cualquiera escribiría, no vería ninguno. De ahí que el lote sea **estratificado A/B/C con cuotas 60/60/60 sobre los 1.168 aprobados**, determinista por semilla y **sin migración** —C08 reservó `ProposedProfileJson` y `ReviewDurationMs` y cumplió—, y que la corrección se registre **con dirección** (adición / retirada / sustitución / confirmación), que es lo que separa la omisión de la alucinación. La cola es de **origen** (`AutoBulk`) y no de **estado**, porque abrirla a `Pending` sacaría 180 documentos del índice a mitad de sesión. C28 hereda además de C18b **los atajos de teclado** —que la tarea 6.4 de aquel change dio por hechos sin entregarlos— y **los nueve SKU sin familia** de las dos raíces degeneradas, que entran como requisito separado de `family-review` porque el `POST` de creación ya existe desde C07 y el coste es de frontend. **Y una trampa heredada que el change tiene que evitar por escrito:** C18b registró 64 juicios y **solo 6 tiempos**, porque el cronómetro vivía en el estado del componente y moría con la pestaña; con la aprobación masiva que esta ficha pide, C28 va camino de repetirlo, así que el cronómetro se persiste en cada guardado y las dos poblaciones —cronometrada y masiva— se reportan aparte.

> **Actualizado el 2026-09-13, al archivar C28.** **C28 (`add-profile-review-ui-and-metrics`) pasa a hecho** y con él **EP13 queda completa**. Recuento: **30 archivadas, 7 pendientes** (C30, C31, C32, C34, C36, C38 y C39). Entrega las dos cifras que el §16 pedía y que no existían: **tasa de corrección ponderada del 20,9 %** y **tiempo medio de 32,1 s**, sobre **204 perfiles revisados en 109 minutos y 204 cronometrados — el 100 %**, frente a los 6 de 64 que C18b pudo registrar. Pero el titular se publica partido, porque las dos mitades no miden lo mismo: **10,4 % en los campos sensibles** —los que el §7.8 define como aquellos cuyo error llega a un cliente— y **42,3 % en las etiquetas comerciales**, que llegaban vacías y que el revisor rellenó con su criterio, sin verdad de referencia contra la que contrastar una opinión de estilo u ocasión. La cifra que el §15 declara es el **10,4 %**. **La predicción falsable del diseño sale confirmada a medias**: las retiradas se concentran en el estrato B como estaba previsto —8 de 9, cero en A, una en C— pero las adiciones están en A y no en C, y visto después es obvio, porque A *es* el estrato de la ausencia y rellenar un campo vacío es una adición por construcción. **El hallazgo más rentable es el que no buscaba nadie:** `vidrio` falta en el vocabulario de `materials` y alcanza **67 productos, el 5,6 % del catálogo**; la exploración no podía verlo porque solo supo preguntar por los términos que ya estaban en la lista, y hacía falta una persona leyendo. Con `naturaleza` en `style_tags` (38, junto al `filigrana` que dejó FIX1), `platino` (20) y `cobre` (15), la ruta de ampliación queda dimensionada y anotada en `DEFERRED_TASKS.md`, con su orden obligatorio: publicar la tasa **antes** de ampliar, porque `confidence.py` calcula el span contra el vocabulario y añadir esos términos movería 21 de los 122 productos del estrato A. **Tres cosas se declaran sin medir en vez de estimarlas:** el A/B de teclado no se obtuvo —los atajos se usaron pero los bloques no se separaron, y el revisor no percibió ventaja—, la tesis de que el span es ciego a las omisiones no se puso a prueba porque la muestra tocó 2 de sus 28 candidatos, y las 22 filas de `enrichment/v2` siguen sin ser una comparación de versiones de prompt. Nace la capability viva **`profile-review`** con quince requisitos, y `family-review` pasa de diez a doce al recibir la creación de familia y los atajos que la tarea 6.4 de C18b dio por entregados sin entregarlos. **Sin migración** —C08 había reservado el almacenamiento y cumplió— y **sin tocar `ai-service/`**. Detalle en [c28-implementation-measurements.md](Proyecto%20Final%20AIEng/informes/c28-implementation-measurements.md).

---

## Orden de Implementación

Este orden de implementación ha sido definido considerando las dependencias entre épicas y la necesidad de construir primero las bases del sistema antes de implementar funcionalidades más complejas. Este orden es **fundamental para generar los tickets de trabajo en el orden correcto de desarrollo**.

**Orden de implementación confirmado:**

1. **EP7**: Autenticación y Gestión de Usuarios (base del sistema)
   - Sin autenticación no se puede acceder al sistema
   - Los roles y permisos son necesarios para todas las demás funcionalidades
   - Base para control de acceso en el resto del sistema

2. **EP8**: Gestión de Puntos de Venta (necesario para el resto)
   - Los puntos de venta son necesarios para inventario, ventas y asignaciones
   - Debe estar disponible antes de asignar operadores o métodos de pago

3. **EP6**: Gestión de Métodos de Pago (necesario para ventas)
   - Los métodos de pago deben estar configurados antes de registrar ventas
   - Necesario para asignar métodos a puntos de venta

4. **EP1**: Gestión de Productos (necesario para ventas e inventario)
   - El catálogo de productos es base para inventario y ventas
   - Las fotos de productos son necesarias para reconocimiento de imágenes

5. **EP2**: Gestión de Inventario (necesario para ventas)
   - El stock debe estar gestionado antes de poder registrar ventas
   - Las validaciones de stock requieren inventario configurado

6. **EP3**: Registro de Ventas (funcionalidad principal)
   - Requiere: productos, inventario, métodos de pago y puntos de venta
   - Funcionalidad core del sistema

7. **EP4**: Reconocimiento de Imágenes con IA (mejora de ventas)
   - Mejora la experiencia de registro de ventas
   - Requiere productos con fotos de referencia (EP1)
   - Puede desarrollarse en paralelo con EP3 pero se integra después

8. **EP5**: Gestión de Devoluciones (complemento)
   - Requiere ventas registradas (EP3)
   - Funcionalidad complementaria que mejora la gestión completa

9. **EP9**: Consultas y Reportes (análisis)
   - Requiere datos existentes (ventas, inventario, devoluciones)
   - Funcionalidad de análisis que se beneficia de tener datos históricos

10. **EP10**: Gestión de Componentes de Joyas (costes de producción)
   - Requiere: EP1 (productos), EP7 (admin), EP9 (reportes para sección Reportes)
   - Extiende la gestión de productos con componentes, costes y reportes de márgenes
   - Orden interno de EP10: HU-EP10-001 → HU-EP10-002 → HU-EP10-003 → HU-EP10-004 → HU-EP10-005 → HU-EP10-006 → HU-EP10-007 → HU-EP10-008

> **Nota importante:** Este orden debe respetarse al generar los tickets de trabajo para asegurar que las dependencias estén resueltas antes de implementar funcionalidades que las requieren.

### Orden de Implementación del Proyecto Final (EP11–EP17)

Las épicas del PF **presuponen el MVP terminado**: operan sobre el catálogo, el inventario y los puntos de venta que ya existen. Su orden no es estrictamente secuencial por épica, sino por olas de trabajo con dependencias cruzadas entre changes:

1. **EP11** (cimientos) — sin el esqueleto, los contratos y el esquema vectorial no arranca nada.
2. **EP12** en paralelo con el resto de EP11 — el corpus es el insumo de la búsqueda.
3. **EP14** — requiere corpus indexado (EP12) y contratos (EP11). Es la ruta crítica principal. *(Actualizado el 26 sep: la épica **se reabre con C41**, que no venía de ninguna ola sino de las pruebas manuales posteriores al cierre de C40. **C41 no tapona a nadie** —es una hoja: no toca prompt, ni fase de abstención, ni el contrato congelado, así que no compite con C38 ni con C39 y puede ir antes, después o en paralelo—, **pero va antes de cualquier remedición**: el entorno está hoy a **14,4 veces** el techo de rancidez, así que una pasada tomada ahora volvería a describir un sistema desconfigurado, que es exactamente lo que le pasó al grupo 8 de C40. Su zona principal es **`ai-service/`** —la ficha del plan dice *«backend/ y frontend/ — no toca ai-service/»* y **está mal**, porque el drenaje se queda en `jbg-ai`—, más `deploy/demo/` y un retoque en el DTO de salud y en la tarjeta. **No se abre a la vez que ningún change que toque `retrieval/` o `indexing/`.**)* *(Actualizado el 26 sep: **C41 archivado**, y lo que dejó es más que un arreglo. El drenaje corre **al arrancar y cada 600 s** contra un techo de 3.600, con la regla `techo / intervalo ≥ 4` que tolera cinco drenajes fallidos seguidos, así que la ventana de rancidez deja de abrirse sola. **Eso convierte a C41 en prerrequisito habilitante de C42**: una pasada de medición del agente dura 2 h 44 min y el arreglo manual caducaba en una hora, de modo que antes de C41 **ninguna pasada larga podía medir el sistema configurado**. Con una salvedad que va al runbook y no al grafo: `run_scheduler` vive **sólo en el lifespan de FastAPI**, y los arneses son CLI que no drenan nada — así que la pasada exige el contenedor `jbg-ai` levantado, no sólo el change archivado.)*
4. **EP13** — puede avanzar en paralelo desde que existe el índice; su aprobación humana alimenta la desambiguación de EP15.
5. **EP15** — requiere recuperación funcionando (EP14) y familias (EP13). **Y es donde arranca lo que queda** *(13 sep)*: con C26 archivado, **C30a es el único change libre que desbloquea algo**, y desbloquea la cadena entera —`C30a → C34 → C36` y `C30a → C30b → C31 → C32 → C38`—. *(Al día 22 sep: la cadena `C30a → C34 → C36` está **en su último eslabón**, con C36 en curso; por el otro lado sólo queda **C38**, que depende de C34 y no de la pantalla de C36, así que los dos pueden avanzar en paralelo.)*. Sus cuatro changes de servicio comparten zona y son **estrictamente secuenciales**: no se abren dos a la vez. *(Actualizado el 14 sep: archivado C30a, los nodos libres pasan a ser **dos** —**C30b** y **C34**—, uno por cada rama de la bifurcación. Se abre **C30b** primero por la regla 2 del §1 del plan, desbloqueo antes que calendario: abre C31 y C38, mientras C34 es el arranque de la otra rama y no tapona a nadie que no esté ya esperando. La secuencialidad estricta sigue aplicando dentro de `assist/`: **C30b ‖ C31 ‖ C32 no se solapan**.)* *(Actualizado el 14 sep: archivado C30b, los nodos libres vuelven a ser **dos** —**C31** y **C34**— y se abre **C31**. No es por desbloqueo, que ahí empatan: es por la **ventana de contrato**. `/v1/assist/sale` sigue con **cero consumidores**, así que C31 puede mover descripciones y vocabulario sin que nadie pague; en cuanto C34 escriba el cliente .NET, esa ventana se cierra y cualquier ajuste del enrutador lo paga el otro lado. Y C34 nace entonces conociendo ya el vocabulario del enrutador y su presupuesto de latencia, que es justo lo que la anotación del 14 sep le deja escrito en su ficha.)* *(Actualizado el 20 sep: archivados C31 y **C32a**, se abre **C32b**. La ventana de contrato **sigue abierta y se gasta ahora**: `/v1/assist/sale` continúa con cero consumidores .NET, así que la ruta nueva `POST /v1/assist/agent` se añade al momento más barato que queda —el mismo argumento con el que C30a y C31 movieron el contrato sin coste—, y a partir de C34 ya no lo sería. Los nodos libres son **dos**, **C32b** y **C34**, y se abre C32b porque **es el único que tapona el cierre**: `C32b → C38 → C39`, mientras C34 sólo abre C36. La secuencialidad estricta dentro de `assist/` se mantiene: **C30a ‖ C30b ‖ C31 ‖ C32a ‖ C32b nunca simultáneos**.)* *(Actualizado el 21 sep: archivado C32b, **C34 es el único nodo libre** y se abre. Con él la ventana de contrato de `/v1/assist/sale` **se cierra**: a partir de aquí la ruta tiene un consumidor .NET, y cualquier cambio en su forma se paga en los dos lados. C34 no la mueve —`openapi.json` queda idéntico byte a byte—, y deja fuera la consulta libre y el agente porque sus marcadores no dicen de qué pieza son.)* *(Actualizado el 24 sep: archivado C36, la épica quedó cerrada y **se reabre el mismo día con C40**, que no venía de ninguna ola sino de comprobar C36 en demo. **C40 es el único nodo libre y el arranque de lo que queda**, `C40 → C38 → C39`, y su orden respecto a C38 es **obligado y no disciplina de rama**: sube el prompt a `assist/v5` y mueve la fase de la abstención, así que unas cifras de C38 tomadas antes describirían un prompt sustituido y una fase movida. **La ventana de contrato de `/v1/assist/sale` está cerrada desde C34**, así que C40 paga lo que C31 y C32b no pagaron: `filters` en `AssistRequest` es **adición pura** y se verifica hoja a hoja, pero ya cuesta un lado más. Y **la secuencialidad estricta dentro de `assist/` sigue aplicando**, a la que se suma ahora `retrieval/`: C40 mueve la fase de la abstención, así que tampoco se solapa con C21, C22 ni C25.)* *(Actualizado el 26 sep: archivado C40, el nodo libre es **C40_FIX** y la cadena que queda es `C38 → C39`. **C40_FIX no tapona a nadie** —es una hoja, fuera de la numeración C, y C38 no depende de él— pero **va primero de todos modos, y no por disciplina de rama**: corrige un `SHALL` de `assisted-search-panel` que afirma lo contrario de lo que el sistema hace, y cada change archivado encima consolida esa afirmación. **Comparte zona con C38** —el panel y sus specs—, así que los dos no se abren en paralelo. **No mueve el contrato con `jbg-ai`**: `openapi.json` queda sin diff, porque el tercer perfil de *claims* de C40 ya acepta un token sin `pos_id` en recuperación y assist. Y **no toca `assist/` ni `retrieval/`**, así que la secuencialidad estricta de esas dos zonas no le aplica.)* *(Actualizado el 26 sep: archivado C40_FIX, **la épica se reabre por tercera vez en tres días con C42**, que tampoco venía de ninguna ola. **C42 es el único nodo libre y el arranque de lo que queda**, `C42 → C38 → C39`, y su orden respecto a C38 es **obligado y por el mismo motivo que lo fue el de C40**: sube la tarea del agente a `assist/v6`, así que unas cifras de generación del agente tomadas antes describirían un prompt sustituido. **Mueve el contrato**, y ya cuesta los dos lados: `origin` en el grupo de la respuesta del agente es adición pura y se verifica hoja a hoja, pero obliga a sustituir el *fixture* del snapshot con sus adiciones declaradas —C40 fue el change anterior que lo hizo, y el propio test escribe que *«the next change that moves the contract replaces this fixture… deliberately»*—. **La secuencialidad estricta de `assist/` le aplica de lleno**: toca `assist/agent.py`, `assist/constants.py` y los prompts, así que no se solapa con C38 ni con ningún change de esa zona. **Y arrastra una dependencia que no es de grafo sino de entorno**: su pasada de medición dura **2 h 44 min** contra un techo de rancidez de **1 h**, así que **exige el drenaje programado de C41 encendido** — sin él mediría el sistema degradado, que es el error que C41 anotó sobre el §8 de C40 y que en el arnés del agente reaparece peor, porque allí **no hay comprobación de frescura ninguna**.)*
6. ~~**EP16**~~ — **anulada el 2026-08-31** junto con sus cinco changes. Ya no ocupa lugar en el orden.
7. **EP17** — la telemetría (C04) se implanta desde el primer día. La evaluación se parte en dos y **no espera a la generación**: **C24** sólo necesita recuperación (EP14) y **se archivó el 2026-09-11**, mientras que C38 —validador anti-alucinación, RAGAS y escenarios de agente— sí requiere EP15 y se integra en el runner que C24 entrega. ~~**C24 es el único change pendiente que bloquea a dos**~~ *(cumplido)*. La cadena crítica ya no es `C21 → C24 → C25 → C26 → C34 → C36`: los cinco primeros eslabones están archivados y **arranca ahora en `C30a → C34 → C36`** *(actualizado el 2026-09-13)*. Y C38 hereda dos cosas de C30b: el validador anti-alucinación **mide** un invariante que el servicio ya sostiene en ejecución, y la excepción que permite al arnés guardar el texto generado viene ya declarada en la especificación de C30b — sin ella, la primera sesión de C38 rompería el invariante o quedaría bloqueada por él. **Y hereda dos más, descubiertas al explorar C30b** *(14 sep)*: que el arnés debe guardar **el objeto de generación completo** —argumentario más las citas usadas con su tramo de apoyo— y no sólo el texto, porque con los tramos los pares afirmación↔cita llegan ya alineados y *faithfulness* se puede medir por afirmación en vez de sobre la respuesta entera; y que **el golden set no le sirve para esto**, porque sus 72 consultas no anclan ninguna pieza y el argumentario se genera en los modos anclados. C38 necesita casos propios, y la muestra estratificada que declare C30b es de donde deben salir.

> El orden fino, con olas fechadas, dependencias exactas y pares que no deben ejecutarse en paralelo, está en el [plan de changes](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) (§4 grafo de dependencias y §5 calendario). Ese documento manda sobre este resumen.

---

## Notas

- Las User Stories se crearán siguiendo el formato definido en `Documentos/Procedimientos/Procedimiento-UserStories.md`
- Las historias de EP10 incluyen requisitos funcionales (RF), no funcionales (RNF), criterios de aceptación Given/When/Then y matriz de dependencias explícita
- Cada User Story tendrá su propio archivo en `Documentos/Historias/` con el formato `HU-EP[X]-[NNN].md`
- Las épicas están diseñadas para cubrir todos los casos de uso del MVP definidos en el README
- El modelo de datos está optimizado para soportar todas estas épicas de manera eficiente
- Las funcionalidades de Fase 2 (alertas, reportes avanzados, dashboard, etc.) no están incluidas en este MVP
- **Nota:** Algunas historias han sido consolidadas para evitar duplicación. Ver `Documentos/aclaraciones-tecnicas.md` para detalles.

