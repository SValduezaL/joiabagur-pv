# Modelo C4 - Sistema de Gestión de Puntos de Venta para Joyería

Este documento describe la arquitectura del sistema utilizando el modelo C4, proporcionando diferentes niveles de abstracción desde el contexto general hasta los componentes internos.

---

## Tabla de Contenidos

1. [Nivel 1: Contexto del Sistema](#nivel-1-contexto-del-sistema)
2. [Nivel 2: Contenedores](#nivel-2-contenedores)
3. [Nivel 3: Componentes](#nivel-3-componentes)
   - [3.1 Componentes del Backend](#31-componentes-del-backend)
   - [3.2 Componentes del Frontend](#32-componentes-del-frontend)
   - [3.3 Componentes del Servicio de IA](#33-componentes-del-servicio-de-ia)
4. [Notas sobre Desarrollo vs Producción](#notas-sobre-desarrollo-vs-producción)

---

## Nivel 1: Contexto del Sistema

El **Sistema de Gestión de Puntos de Venta para Joyería** permite gestionar inventario, registrar ventas y facilitar la identificación de productos mediante reconocimiento de imágenes con inteligencia artificial en múltiples puntos de venta (propios y de terceros).

### Actores

- **Administrador**: Usuario con acceso completo al sistema. Puede gestionar productos, inventario, usuarios, puntos de venta, métodos de pago y consultar reportes de todos los puntos de venta.

- **Operador**: Usuario con acceso restringido a puntos de venta asignados. Puede registrar ventas, consultar inventario y gestionar devoluciones en sus puntos de venta asignados.

### Diagrama de Contexto

```mermaid
C4Context
    title Contexto del Sistema - Sistema de Gestión de Puntos de Venta

    Person(admin, "Administrador", "Gestiona productos, inventario, usuarios y puntos de venta")
    Person(operador, "Operador", "Registra ventas en puntos de venta asignados")

    System(sistema, "Sistema de Gestión de Puntos de Venta", "Gestiona inventario, ventas y reconocimiento de productos mediante IA")

    Rel(admin, sistema, "Gestiona el sistema completo")
    Rel(operador, sistema, "Registra ventas y consulta inventario")
```

### Descripción

El sistema permite a los administradores gestionar el catálogo de productos, inventario por punto de venta, usuarios y configuración del sistema. Los operadores utilizan el sistema principalmente desde dispositivos móviles para registrar ventas mediante reconocimiento de imágenes o manualmente, reduciendo errores en la clasificación de productos.

**Características principales:**
- Gestión centralizada de productos e inventario
- Registro de ventas con reconocimiento de imágenes mediante IA
- Gestión de múltiples puntos de venta
- Trazabilidad completa de ventas e inventario
- Optimizado para uso móvil en puntos de venta

---

## Nivel 2: Contenedores

El sistema está compuesto por cinco contenedores principales: una aplicación web frontend, una API backend, un servicio de IA, una base de datos PostgreSQL y un servicio de almacenamiento de objetos.

### Contenedores

#### Frontend Web Application
- **Tecnología**: React/Vue/Angular (SPA), TypeScript
- **Responsabilidades**:
  - Interfaz de usuario para administradores y operadores
  - Reconocimiento de imágenes con IA en cliente (TensorFlow.js/ONNX.js)
  - Gestión de sesión y autenticación
  - Comunicación con API backend mediante HTTP/REST
- **Despliegue**: En AWS producción actual, assets del SPA van **embebidos** en la imagen Docker servida tras nginx en EC2; en desarrollo, servidor local (Vite). CDN sigue siendo patrón válido en Azure u otras cuentas.

#### Backend API
- **Tecnología**: ASP.NET Core Web API (.NET 10), C#
- **Responsabilidades**:
  - Lógica de negocio y reglas de dominio
  - Autenticación y autorización (JWT)
  - Procesamiento de importaciones Excel
  - Validaciones de stock y métodos de pago
  - Gestión de archivos y almacenamiento
- **Despliegue**: Contenedor Docker en **EC2** (pila actual, imagen bundlada) u otros hosts (App Service en Azure, ECS/App Runner en variantes legado)

#### AI Service (`jbg-ai`)
- **Tecnología**: Python 3.11, FastAPI, uvicorn, `uv`, pydantic-settings, SQLAlchemy 2 + psycopg 3 + Alembic
- **Responsabilidades**:
  - Recuperación vectorial e híbrida sobre el índice del catálogo (pgvector)
  - Generación con LLM, atribución con citas y guardrails
  - Enriquecimiento del catálogo, agrupación asistida en familias e indexación (`/v1/enrich`, `/v1/families`, `/v1/index`)
  - Bucles agénticos de asistencia a la venta y de inventario
  - Evaluación offline (golden set, métricas de recuperación y generación)
  - **Mantenimiento de la proyección de disponibilidad por punto de venta (C41)**: drena el feed `pos-availability` **al arrancar el proceso** —completo si no hay *checkpoint*— y después cada `JPV_POS_SYNC_INTERVAL_SECONDS`, tomando un *advisory lock* **no bloqueante dentro del propio drenaje**, de modo que un disparo programado y un `sync-pos` corrido a mano declinan en vez de entrelazar el keyset de fila única de `ai.sync_checkpoint`. No arranca bajo `STUB_MODE` ni sin feed configurado, y **nunca bloquea el arranque**: la tarea se crea y no se espera, porque la sonda de salud del contenedor tiene tres segundos de tope
- **Lo que NO hace**: no calcula precio, stock ni permisos; no escribe ni lee el esquema `public` por SQL; no atiende al navegador
- **Despliegue**: contenedor Docker en la misma EC2, en red interna; **el puerto no se publica en nginx**. En desarrollo, servicio `jbg-ai` del Compose (`8001` → 8000)
- **Estado actual**: contrato congelado (C02) — **11** endpoints `/v1` con modelos Pydantic completos, JWT interno HS256 y `openapi.json` versionado (ocho en C02, más `POST /v1/families/suggest` en C18a, `POST /v1/families/audit` en C18b y `POST /v1/assist/agent` en C32b). *(Corregido el 2026-09-26: decía **10** y el recuento no se movió al añadir la ruta del agente. Verificado contra `ai-service/openapi.json`, que publica once rutas bajo `/v1` más `/health`.)* Las respuestas son stubs deterministas bajo `STUB_MODE`; con `STUB_MODE=false` son reales enriquecimiento (C09), índice de catálogo (C13), recuperación de productos (C14), las dos de familias (C18a, C18b), evals (C24), sustitutos (C26) y **venta asistida (C30a)**. Queda **una** ruta en 501, `POST /v1/inventory/propose` (C35), y no por falta de turno sino por una rama anulada el 2026-08-31

> **Regla de frontera (diseño §6.2):** *Python calcula parecidos y redacta; .NET calcula números y decide.* El backend .NET actúa de **hidratador** y es la autoridad final: descarta cualquier candidato que ya no cumpla las reglas de negocio.

#### PostgreSQL Database
- **Tecnología**: PostgreSQL 15+ con extensión **pgvector**
- **Responsabilidades**:
  - Almacenamiento persistente de todos los datos del sistema
  - Gestión de productos, inventario, ventas, usuarios, puntos de venta (esquema `public`, propiedad de .NET)
  - Índice vectorial y documentos del corpus (esquema `ai`, propiedad de `jbg-ai`)
  - Índices optimizados para consultas frecuentes
- **Despliegue**: RDS PostgreSQL (AWS) en producción, contenedor `pgvector/pgvector:pg15` en desarrollo

#### Object Storage
- **Tecnología**: AWS S3 / Azure Blob Storage
- **Responsabilidades**:
  - Almacenamiento de fotos de productos (ProductPhoto)
  - Almacenamiento de fotos de ventas (SalePhoto)
  - Almacenamiento de archivos Excel importados (temporal)
- **Despliegue**: S3 bucket (AWS) o Blob Storage container (Azure) en producción, sistema de archivos local en desarrollo

### Diagrama de Contenedores

```mermaid
C4Container
    title Contenedores del Sistema

    Person(admin, "Administrador")
    Person(operador, "Operador")

    System_Boundary(sistema, "Sistema de Gestión de Puntos de Venta") {
        Container(frontend, "Frontend Web Application", "React 19 + TypeScript (SPA)", "Interfaz de usuario y reconocimiento de imágenes en cliente")
        Container(api, "Backend API", "ASP.NET Core Web API (.NET 10)", "Lógica de negocio, autenticación, hidratación y gestión de datos")
        Container(ai, "AI Service (jbg-ai)", "Python 3.11 + FastAPI", "Recuperación vectorial, generación con LLM, enriquecimiento e indexación")
        ContainerDb(db, "PostgreSQL Database", "PostgreSQL 15+ con pgvector", "Esquema public (negocio) y esquema ai (vectores)")
        Container(storage, "Object Storage", "AWS S3", "Almacenamiento de fotos y archivos")
    }

    System_Ext(llm, "Proveedor LLM", "Modelos de lenguaje y embeddings")

    Rel(admin, frontend, "Usa", "HTTPS")
    Rel(operador, frontend, "Usa", "HTTPS")
    Rel(frontend, api, "Realiza peticiones HTTP/REST", "HTTPS")
    Rel(api, db, "Lee y escribe", "PostgreSQL Protocol")
    Rel(api, storage, "Lee y escribe", "S3 API")
    Rel(api, ai, "Consulta con JWT interno de servicio", "HTTP, red Docker interna")
    Rel(ai, db, "Lee y escribe solo el esquema ai", "PostgreSQL Protocol")
    Rel(ai, api, "Sincroniza el índice vía feed paginado", "HTTP")
    Rel(ai, llm, "Genera texto y embeddings", "HTTPS")
```

> El frontend **nunca** se comunica con `jbg-ai`. Si el servicio de IA no responde, el backend degrada al buscador léxico existente y marca `ai_available: false`: el sistema no se cae por culpa de la IA.

### Flujos Principales

#### Flujo de Autenticación
1. Usuario ingresa credenciales en Frontend
2. Frontend envía petición a Backend API (`POST /api/auth/login`)
3. Backend API valida credenciales contra PostgreSQL Database
4. Backend API genera token JWT y lo retorna al Frontend
5. Frontend almacena token y redirige según rol

#### Flujo de Reconocimiento de Imágenes y Venta
1. Operador captura foto del producto en Frontend
2. Frontend procesa imagen localmente con TensorFlow.js/ONNX.js
3. Frontend muestra 3 sugerencias ordenadas por confianza
4. Operador selecciona producto correcto
5. Frontend envía venta a Backend API (`POST /api/sales`)
6. Backend API valida stock y método de pago
7. Backend API crea registro en PostgreSQL Database
8. Backend API sube foto a Object Storage
9. Backend API actualiza inventario en PostgreSQL Database

#### Flujo de Importación de Productos
1. Administrador sube archivo Excel en Frontend
2. Frontend envía archivo a Backend API (`POST /api/products/import`)
3. Backend API procesa Excel y hace matching por SKU
4. Backend API actualiza/crea productos en PostgreSQL Database
5. Backend API retorna resumen de importación al Frontend

---

## Nivel 3: Componentes

### 3.1 Componentes del Backend

El Backend API está organizado en servicios de dominio, controladores REST, repositorios y servicios compartidos.

#### Servicios de Dominio

- **Authentication Service**: Gestiona autenticación de usuarios, generación de tokens JWT, validación de credenciales y control de sesión.

- **User Service**: Gestión de usuarios (crear, editar, desactivar), asignación de operadores a puntos de venta, validación de permisos según roles.

- **Product Service**: Gestión del catálogo de productos (crear, editar, buscar), importación desde Excel con matching por SKU, validación de datos.

- **Inventory Service**: Gestión de stock por punto de venta, importación de stock desde Excel, ajustes manuales, validación de stock disponible, generación de movimientos de inventario.

- **Sale Service**: Registro de ventas, validación de stock y métodos de pago, resolución de precio (oficial o manual según política del POS), persistencia de campos de auditoría de precio (`PriceWasOverridden`, `OriginalProductPrice`), actualización automática de inventario, generación de movimientos de inventario.

- **Return Service**: Gestión de devoluciones, asociación con venta original, incremento automático de stock, generación de movimientos de inventario.

- **Payment Method Service**: Gestión de métodos de pago disponibles, asignación de métodos a puntos de venta, validación de métodos asignados.

- **Point of Sale Service**: Gestión de puntos de venta (crear, editar, activar/desactivar), configuración de política de edición manual de precio (`AllowManualPriceEdit`), validación de asignaciones de operadores.

- **Report Service**: Consultas de historial de ventas con filtros, consultas de inventario, consultas de movimientos de stock, generación de reportes.

#### Servicios del Proyecto Final de IA

Viven en la misma capa de aplicación que los anteriores; se listan aparte porque su ciclo de vida lo marcan los changes C01–C39 y no las épicas del MVP.

- **Product Search Event Service** (C04): registro de la telemetría de búsqueda asistida en dos pasos —el servidor escribe la mitad de búsqueda mientras la sirve, el navegador reporta solo la selección— y derivación del rango a partir de la lista realmente devuelta. **Nunca lanza**: un fallo de telemetría no puede convertir una búsqueda correcta en un error.

- **Product AI Profile Service** (C08): enriquecimiento por lotes del catálogo contra `jbg-ai`, aplicación de la política híbrida de revisión por campo y persistencia del perfil con su procedencia. Idempotente sobre el hash de las entradas del producto, de modo que repetir un lote no vuelve a pagar el modelo ni sobrescribe una ficha ya revisada.

- **Profile Review Policy** (C08): decide, campo a campo, qué necesita mirar una persona. Clase **pura** —sin base de datos, sin HTTP, sin reloj— con sus umbrales en configuración validada al arranque, porque están pensados para recalibrarse contra el golden set de evaluación.

- **Profile Review Service** (C28): la revisión humana de esos perfiles y las métricas que produce. Servicio aparte del que enriquece, porque el contrato de aquél ya adjudicaba aquí leer, aprobar y medir. Dibuja la cola por **origen** (`AutoBulk`) sobre estado aprobado y nunca por estado —el feed del índice selecciona aprobados, así que abrir el lote a `Pending` sacaría los documentos del índice a mitad de sesión—, estratifica por evidencia con una función compartida por la cola y las métricas, y ordena cada estrato por `SHA-256(ProductId + semilla)`: el lote es reproducible **sin persistirse**, que es lo que evita una séptima migración. Registra la corrección **con su dirección** por diferencia de conjuntos, sin reescribir jamás `ProposedProfileJson` —la tasa *es* la diferencia entre esa columna y los valores en vigor—, exige la duración medida en la misma petición que registra el juicio, y acota la aprobación masiva a un campo dentro de un estrato. Se apoya en dos clases **puras**: `ProfileEvidenceStratum` y `ProfileReviewSampling`.

- **Product Family Service** (C07): gestión de las familias de producto y de su pertenencia. La lista de miembros se **declara entera** y el orden sale de la posición en ella, de modo que huecos y órdenes duplicados no se pueden expresar; declarar la lista que la familia ya tiene no escribe nada. La exclusión —un producto en una familia como máximo— la garantiza un índice único de la base, no una comprobación del servicio. Es la **única vía de escritura** de familias, también para la aprobación asistida de C18a: es lo único que mantiene coherente el watermark del feed de indexación, por el `UpdatedAt` de la propia familia al crearla y por el estampado de los productos que entran y salen al reemplazar.

- **Family Suggestion Service** (C18a): orquesta la agrupación asistida. `jbg-ai` propone y este lado persiste, con el mismo patrón que el enriquecimiento por lotes de C09. **Proponer no escribe absolutamente nada** —ni familia, ni pertenencia, ni watermark—; aplicar recorre el lote familia a familia y registra `Origin = AiApproved` con el administrador y el instante. Un producto en disputa **no tumba el lote**: esa familia se salta entera y se nombra en la respuesta, y las demás se crean.

- **AI Gateway Client** (C03, C08): cliente tipado hacia `jbg-ai`, con una familia de ruta por tipo de llamada y **cortacircuitos aislados entre ellas**, de modo que un enriquecimiento lento no pueda empujar la búsqueda del operador a su vía léxica degradada. **C34 añade la tercera familia, la generativa** (`ai-assist`, para `POST /v1/assist/sale`): presupuesto de 10 s con **suelo de 8 s comprobado al arrancar** —el peor caso que Python declara, 2 × 4 s—, circuito propio y **ningún reintento salvo una conexión que no llegó a abrirse**, porque cualquier otro fallo pudo ocurrir con la generación ya en marcha y repetir paga dos veces al proveedor. Los sustitutos (`POST /v1/retrieval/substitutes`) van por la familia de recuperación: no llaman a ningún modelo. En esas dos operaciones, y sólo en ellas, un **422** es un rechazo de la pieza y no «IA no disponible». **C42 añade la cuarta familia, la del agente** (`ai-agent`, para `POST /v1/assist/agent`): presupuesto de 18 s con **suelo de 15 s comprobado al arrancar**, que es el techo de reloj que el propio servicio declara (`AGENT_DEADLINE_SECONDS`) —el máximo medido fue 11.917 ms, y apretar el presupuesto hasta ahí tiene un modo de fallo caro: cortar una petición que Python ya pagó entera—, circuito propio, y `AssistTimeoutMs` **sin tocar**, porque el agente lleva opción propia. Su cortafuegos **no cuenta la degradación en banda** y ésa es una decisión escrita, no un descuido: Polly recibe un resultado de transporte y **no ve el cuerpo**, así que un 200 con `stop_reason=fallo_proveedor` o `sin_cliente` es un éxito en esa capa; se instrumenta como métrica, y las dos alternativas —un handler que leyera el cuerpo y un circuito de dominio— están descartadas en el design con su motivo.

- **Sales Assist Service** (C34): el card de venta de una pieza tras `POST /api/ai/products/{id}/sales-assist`. Autoriza el punto de venta y **comprueba que la tienda lleva la pieza antes de llamar a la IA** —ninguna llamada de pago para una petición que va a rechazar—, hidrata el grupo que devuelve `jbg-ai` en una sola consulta conservando su orden, **recalcula aquí** los dos avisos de stock y el de variantes, y resuelve `{{price}}`/`{{stock}}` **contra la pieza anclada**; si queda cualquier `{{…}}`, retira el argumentario y sirve el resto. Con la IA caída sirve el card desde el catálogo: la pieza, su familia de `ProductFamily` y los avisos.

- **Substitutes Service** (C34): los sustitutos de una pieza tras `GET /api/ai/products/{id}/substitutes`. Una sola llamada con la ventana máxima, una hidratación, y **sólo lo que la tienda puede vender hoy**: la exclusión por stock que C26 dejó fuera de Python a propósito vive aquí, junto al stock. Cuatro resultados vacíos distinguibles y ninguno es un error del servidor.

- **Assisted Search Service** (C15): orquesta la búsqueda del operador tras `POST /api/ai/search`. Pide a `jbg-ai` la **ventana máxima que el contrato puede producir en una sola llamada** y no repite: el recuperador aplica su umbral antes del límite de filas, así que volver a pedir devolvería lo mismo cobrando un segundo embedding. Después hidrata, trunca a la página pedida conservando el orden de relevancia, y registra la telemetría. **Ningún fallo del servicio de IA rompe la búsqueda**: todos degradan al buscador léxico propio y se reportan al llamante.

- **Free Query Search Service** (C40): la segunda ruta del panel, tras `POST /api/ai/search/assisted`. No es un campo `mode` de la anterior sino un servicio aparte, y la razón es de coste: tiene **interruptor, cupo, presupuesto y circuito propios**, porque la ruta generativa cuesta una llamada de pago y la semántica no — y hay test que fija que agotar el circuito generativo **no abre el de recuperación**. El punto de venta es **opcional**: omitirlo es el ámbito «todas las tiendas», y entonces no hay existencias que reportar, así que la cantidad y el indicador de stock viajan **nulos** en vez de cero. La hidratación no se duplica: se extrajo a **Assisted Search Result Projector**, que es lo único de esa proyección fácil de equivocar e imposible de notar —precio, stock, SKU, nombre y foto del catálogo; puntuación, materiales, razones de coincidencia, familia y variante del índice—. `usage` se construye **sólo para administradores**, así que el campo nace con su frontera de autorización puesta. Una búsqueda de ámbito global **no queda registrada** y es una carencia declarada, no un descuido: la columna de telemetría exige punto de venta y registrarla pediría una migración de EF Core.

- **Agent Assist Service** (C42): el turno del agente de venta, tras `POST /api/ai/search/agent`. Es el camino que **no existía**: `POST /v1/assist/agent` estaba entregado y medido desde C32b y `IAiGatewayClient` tenía siete métodos, ninguno el del agente. Como la consulta libre, tiene **interruptor, cupo, presupuesto y circuito propios** —el cupo son 4 por minuto, y no es una cifra de gusto: ~13.000 tokens por petición contra 25.000 TPM es **una petición por minuto**—, y su interruptor es suyo y no se deriva del asistido. Orquesta **un** turno: valida los tres topes del transcript antes de gastar nada, llama a la pasarela, **hidrata todos los miembros de todos los grupos, sustitutos incluidos**, y registra la telemetría con `Origin = SearchOrigin.AssistedAgent`. **El transcript no se registra nunca** —ni en el log ni en la telemetría—: lo que el operario teclea en una conversación es la pregunta de un cliente, y una línea de log que la lleve la convierte en dato retenido sin que nadie lo haya decidido. El punto de venta es **opcional**, como en la consulta libre: sin tienda no hay existencias que reportar, así que la cantidad y el indicador viajan **nulos**, y la ruta de Python pasó a `get_unscoped_principal` para admitir ese ámbito. La degradación en banda —un 200 que trae `fallo_proveedor` o `sin_cliente`— se registra como aviso y **no** como caída: el servicio contestó, y contarlo como fallo abriría el circuito por un resultado que el diseño prevé.

- **Availability endpoint** (C40, en `AiSearchController`): `GET /api/ai/search/availability` devuelve los **tres** interruptores —búsqueda asistida, respuesta asistida y, desde C42, el agente— **sin llamar a la IA y sin consumir cuota**. **El del agente no se deriva del veredicto asistido**: se lee de su propia opción (`AiAgentAssistOptions.IsEnabledForScope`), porque son funciones con coste distinto y derivar una de otra haría que apagar una apagara la otra en pantalla sin que nadie lo hubiera pedido; viaja en un campo opcional, así que un despliegue anterior que no lo envíe se lee como «no se pudo confirmar» y no como «apagado». Es la única lectura previa que existe, y lleva `[DisableRateLimiting]` **a propósito**: heredar la política del controlador haría que comprobar si puedes buscar te costara una búsqueda. Antes de C40, `aiAvailable` viajaba **dentro** de una respuesta de búsqueda, así que la única forma de saber que una vía estaba apagada era usarla. **Desde C40_FIX responde de un *ámbito* y no de un punto de venta**: omitir `pointOfSaleId` es el ámbito «todas las tiendas» y el identificador vuelve **nulo**, con el veredicto del valor por defecto del despliegue — la lectura estrecha, la misma que la ruta de consulta libre aplica, por un predicado compartido (`AiScopeSwitchExtensions`) para que sonda y ruta no puedan derivar. Un valor **inservible** —en blanco, con espacios, ilegible o un GUID truncado— es **400**: la ausencia es que la clave no esté, y cualquier otra cosa es un valor que tiene que ser usable. **Con una salvedad medida:** la bandera generativa que esta ruta reporta exige los interruptores de la consulta libre **y** de la ficha de venta, mientras `FreeQuerySearchService` sólo aplica el primero, así que con el segundo apagado la sonda dice `switched_off` de un ámbito que la ruta sirve. Decisión pendiente en [`openspec/DEFERRED_TASKS.md`](../openspec/DEFERRED_TASKS.md).

- **Assisted Search Repository** (C15): las dos lecturas que sostienen lo anterior, ambas en una sola consulta. La **hidratación autoritativa** parte de `Inventory` y no de `Product`, de modo que la regla de visibilidad —hay inventario activo en ese punto de venta— es la forma de la consulta y no una condición que alguien pueda olvidar; la cantidad cero se conserva y se marca. Y el **buscador degradado**, con texto completo en español calculado en consulta —sin índice ni cambio de esquema—, que casa cualquier término y ordena por relevancia léxica.

- **Atribución de la venta a la búsqueda** (C16, en `Sales Service`): el ciclo que abre `POST /api/ai/search` se cierra en la caja. `POST /api/sales` y **cada línea** de `POST /api/sales/bulk` aceptan un `searchEventId` opcional, que sólo se persiste tras comprobar que el evento existe **y pertenece a quien vende** —la misma regla de propiedad, sin excepción de administrador, que aplica el registro de la selección—. Lo que no cuadra degrada a atribución nula: nunca un error de validación, nunca una venta fallida, y nada más de la venta cambia. La comprobación es explícita y no se delega en la clave foránea, cuyo comportamiento de borrado gobierna la eliminación del evento y, ante una inserción con un identificador inexistente, abortaría la transacción entera en lugar de degradar.

#### Servicios Compartidos

- **File Storage Service**: Abstracción para almacenamiento de archivos (local en desarrollo, S3/Blob Storage en producción), gestión de fotos de productos y ventas.

- **Stock Validation Service**: Validación de stock disponible antes de ventas, usado por Sale Service y Return Service.

- **Payment Method Validation Service**: Validación de métodos de pago asignados a puntos de venta, usado por Sale Service.

- **Excel Import Service**: Procesamiento de archivos Excel para importación de productos e inventario, validación de formato y datos.

#### Infraestructura

- **Controllers**: Endpoints REST API organizados por dominio (AuthController, ProductController, SaleController, etc.), validación de entrada, manejo de errores.

- **Repositories**: Acceso a datos mediante Entity Framework Core, abstracción de persistencia, implementación de patrones de repositorio.

- **DbContext**: Configuración de Entity Framework Core, definición de entidades y relaciones, migraciones de base de datos.

- **Middleware**: Autenticación JWT, manejo de errores global, logging, CORS, rate limiting.

#### Diagrama de Componentes del Backend

```mermaid
C4Component
    title Componentes del Backend API

    Container_Boundary(api, "Backend API") {
        Component(authService, "Authentication Service", "C#", "Autenticación y generación de tokens JWT")
        Component(userService, "User Service", "C#", "Gestión de usuarios y asignaciones")
        Component(productService, "Product Service", "C#", "Gestión de catálogo de productos")
        Component(inventoryService, "Inventory Service", "C#", "Gestión de stock e inventario")
        Component(saleService, "Sale Service", "C#", "Registro y gestión de ventas")
        Component(returnService, "Return Service", "C#", "Gestión de devoluciones")
        Component(paymentService, "Payment Method Service", "C#", "Gestión de métodos de pago")
        Component(posService, "Point of Sale Service", "C#", "Gestión de puntos de venta")
        Component(reportService, "Report Service", "C#", "Consultas y reportes")
        Component(searchEventService, "Product Search Event Service", "C#", "Telemetría de búsqueda asistida (C04) · nunca lanza")
        Component(aiProfileService, "Product AI Profile Service", "C#", "Enriquecimiento por lotes y perfil IA revisable (C08)")
        Component(reviewPolicy, "Profile Review Policy", "C#", "Revisión híbrida por campo (C08) · clase pura")
        Component(profileReviewService, "Profile Review Service", "C#", "Revisión humana de perfiles y sus métricas (C28) · cola por origen, muestra estratificada y determinista, sin persistir el lote")
        Component(familyService, "Product Family Service", "C#", "Familias de producto y pertenencia declarativa (C07) · única vía de escritura, también para la aprobación asistida (C18a)")
        Component(familySuggestionService, "Family Suggestion Service", "C#", "Agrupación asistida (C18a) · jbg-ai propone, este lado persiste; proponer no escribe nada")
        Component(aiGatewayClient, "AI Gateway Client", "C#", "Cliente tipado hacia jbg-ai (C03, C08, C34, C42) · breakers aislados por familia de ruta: recuperación, enriquecimiento, generativa y agente")
        Component(assistedSearchService, "Assisted Search Service", "C#", "Búsqueda asistida (C15) · ventana máxima en una llamada, hidratación autoritativa, degradación acotada")
        Component(assistedSearchRepo, "Assisted Search Repository", "C#", "Hidratación conjunta por POS y buscador léxico español en consulta (C15)")
        Component(salesAssistService, "Sales Assist Service", "C#", "Card de venta (C34) · pieza comprobada antes de llamar, grupo hidratado, marcadores contra la pieza anclada, degradación desde el catálogo")
        Component(substitutesService, "Substitutes Service", "C#", "Sustitutos (C34) · ventana máxima en una llamada, sólo lo vendible hoy en la tienda, cuatro resultados")
        Component(freeQuerySearchService, "Free Query Search Service", "C#", "Consulta libre (C40) · interruptor, cupo, presupuesto y circuito propios; punto de venta opcional; usage sólo para administrador")
        Component(agentAssistService, "Agent Assist Service", "C#", "Turno del agente (C42) · el camino que no existía; interruptor, cupo, presupuesto y circuito propios; todos los grupos hidratados, sustitutos incluidos; el transcript nunca se registra")
        Component(assistedSearchProjector, "Assisted Search Result Projector", "C#", "De dónde viene cada campo (C40) · compartido por las dos rutas para que la proyección no derive")
        
        Component(fileStorageService, "File Storage Service", "C#", "Abstracción de almacenamiento de archivos")
        Component(stockValidationService, "Stock Validation Service", "C#", "Validación de stock disponible")
        Component(paymentValidationService, "Payment Method Validation Service", "C#", "Validación de métodos de pago")
        Component(excelService, "Excel Import Service", "C#", "Procesamiento de archivos Excel")
        
        Component(controllers, "Controllers", "ASP.NET Core", "Endpoints REST API")
        Component(repositories, "Repositories", "Entity Framework Core", "Acceso a datos")
        Component(dbContext, "DbContext", "Entity Framework Core", "Configuración de EF Core")
        Component(middleware, "Middleware", "ASP.NET Core", "JWT, CORS, logging, rate limiting")
    }

    ContainerDb(db, "PostgreSQL Database")
    Container(storage, "Object Storage")
    Container(jbgAi, "jbg-ai", "Python · FastAPI", "Recuperación vectorial y generación")

    Rel(controllers, authService, "Usa")
    Rel(controllers, userService, "Usa")
    Rel(controllers, productService, "Usa")
    Rel(controllers, inventoryService, "Usa")
    Rel(controllers, saleService, "Usa")
    Rel(controllers, returnService, "Usa")
    Rel(controllers, paymentService, "Usa")
    Rel(controllers, posService, "Usa")
    Rel(controllers, reportService, "Usa")
    Rel(controllers, searchEventService, "Usa")
    Rel(controllers, aiProfileService, "Usa")
    
    Rel(aiProfileService, reviewPolicy, "Usa")
    Rel(aiProfileService, aiGatewayClient, "Usa")
    Rel(controllers, salesAssistService, "Usa")
    Rel(controllers, substitutesService, "Usa")
    Rel(salesAssistService, aiGatewayClient, "POST /v1/assist/sale · ai-assist")
    Rel(substitutesService, aiGatewayClient, "POST /v1/retrieval/substitutes · ai-retrieval")
    Rel(salesAssistService, assistedSearchRepo, "Hidrata")
    Rel(substitutesService, assistedSearchRepo, "Hidrata")
    Rel(salesAssistService, repositories, "Familia (degradado)")
    Rel(controllers, agentAssistService, "Usa")
    Rel(agentAssistService, aiGatewayClient, "POST /v1/assist/agent · ai-agent")
    Rel(agentAssistService, assistedSearchRepo, "Hidrata todos los grupos")
    
    Rel(saleService, stockValidationService, "Usa")
    Rel(saleService, paymentValidationService, "Usa")
    Rel(productService, excelService, "Usa")
    Rel(inventoryService, excelService, "Usa")
    Rel(productService, fileStorageService, "Usa")
    Rel(saleService, fileStorageService, "Usa")
    
    Rel(authService, repositories, "Usa")
    Rel(userService, repositories, "Usa")
    Rel(productService, repositories, "Usa")
    Rel(inventoryService, repositories, "Usa")
    Rel(saleService, repositories, "Usa")
    Rel(returnService, repositories, "Usa")
    Rel(paymentService, repositories, "Usa")
    Rel(posService, repositories, "Usa")
    Rel(reportService, repositories, "Usa")
    Rel(searchEventService, repositories, "Usa")
    Rel(aiProfileService, repositories, "Usa")
    
    Rel(repositories, dbContext, "Usa")
    Rel(dbContext, db, "Lee y escribe")
    Rel(fileStorageService, storage, "Lee y escribe")
    Rel(aiGatewayClient, jbgAi, "JWT interno HS256 · red Docker interna")
    Rel(middleware, controllers, "Intercepta")
```

### 3.2 Componentes del Frontend

El Frontend está organizado en módulos funcionales, servicios y componentes compartidos.

#### Módulos Funcionales

- **Auth Module**: Componentes de login, gestión de sesión, almacenamiento de tokens, redirección según rol, interceptor HTTP para incluir tokens.

- **Product Module**: Componentes para gestión de productos (listado, creación, edición), importación desde Excel, gestión de fotos de productos, búsqueda por SKU o nombre.

- **Inventory Module**: Visualización de stock por punto de venta, vista centralizada de inventario, ajustes manuales de inventario, historial de movimientos.

- **Sale Module**: Componentes para registro de ventas (manual y con reconocimiento), selección de método de pago, validación de stock, edición manual de precio cuando el POS lo permite, indicador de precio modificado en historial/detalle, confirmación de venta.

- **Image Recognition Module**: Captura de fotos desde cámara móvil, integración con TensorFlow.js/ONNX.js, procesamiento de imágenes, visualización de sugerencias, manejo de errores de reconocimiento.

- **Assisted Search Module** (C16): Panel «Buscar con ayuda» en `/sales/new/assisted`, tercera vía de entrada a una venta junto al escaneo y el registro manual. Consulta en lenguaje natural con **envío explícito** —nunca al teclear, porque cada búsqueda no cacheada cuesta un embedding facturado—, consultas de ejemplo, filtros rápidos de material y tipo de pieza sobre el vocabulario cerrado del enriquecimiento, punto de venta resuelto por rol, y resultados **en el orden que dio el backend** con su precio y su stock. Distingue en pantalla los cuatro modos de no encontrar nada —abstención, sin surtido en esa tienda, asistencia no disponible y cuota agotada— y declara la página corta. Embudo de recuperación reservado a administradores. Entrega el producto elegido al flujo de venta manual por estado de navegación, arrastrando el identificador de la búsqueda hasta la caja.

- **Sales Assist Card Module** (C36): Ficha de venta en `/sales/new/assist/:productId`, con carga perezosa y **tres entradas** —la fila del panel de búsqueda asistida, el producto elegido en la venta manual y la pieza resuelta tras escanear—, porque la situación que la ficha nombra, *«el cliente tiene la pieza en la mano»*, no llega por el panel. Es **la única pantalla del proyecto que pone la capa RAG delante de una persona**. Emite **una petición de asistencia por visita y sin reintento automático** —la ruta cuesta una llamada de pago, el límite es de diez por minuto y usuario y la respuesta no se puede cachear—; el reintento lo pide el operario. La pregunta del cliente es una **segunda petición explícita**, acotada a 500 caracteres en el cliente y **siempre en el cuerpo**, nunca en la dirección de la página ni en el estado del enrutador que acaba en el historial, con **cinco preguntas sugeridas horneadas** del propio corpus. Desambigua por familia con **una acción de venta por miembro y ninguna preselección** —el clic es la confirmación—, degradando al SKU el miembro sin etiqueta de variante, y traspasa el miembro elegido a la venta manual por estado de navegación. Pinta los **seis `pitchStatus` como cinco mensajes** sin fundir «la IA no está disponible» con «el argumentario no se generó», porque en el primero la familia, los materiales y las razones de coincidencia salen del catálogo transaccional y no hay citas. Las citas llevan su `claimScope` distinguido —un compromiso de la casa dice que se confirme en tienda— y **se ocultan cuando el argumentario no se entrega**. `size_label_missing` se pinta **como atributo junto al SKU y nunca como aviso**, para no canibalizar a los dos de stock. Los sustitutos se piden cuando la pieza anclada no tiene existencias —**por su stock y no por el estado del argumentario**— y nunca con la IA caída, con los cuatro desenlaces distinguibles y la página corta declarada. El punto de venta llega por estado de navegación y, abierta en frío, ofrece el selector por rol y **no pide nada hasta que haya uno elegido**.

- **Agent Panel Module** (C42): Panel del agente de venta en `/sales/new/agent`, con carga perezosa y **cuarta tarjeta del hub de venta**, que nace con su estado de puerta en tres valores —encendido, apagado con su nota, y **«no se pudo confirmar»** cuando la sonda no trae el campo, que no es lo mismo que apagado—. **Cada turno es dueño de su bloque de respuesta**, y ésa es la decisión alrededor de la que está construido: un área de resultados única refrescada por turno deja al operario leyendo el argumentario de un turno sobre las filas del siguiente, y cuando el bucle pivota a sustitutos la pieza que estaba mirando desaparece sin explicación. El orden de lo que hay dentro del bloque sale de **frecuencias medidas y no de un mockup**: primero el caso sin filas —una respuesta de cada cinco no trae ninguna pieza, y de esas la mayoría son repregunta o rechazo, así que **nunca se redacta como «sin resultados»**—, luego el argumentario reutilizando el bloque de C36 **sin tocarlo**, los avisos y las citas que **no pintan nada** cuando vienen vacías (lo están en el 96,1 % y el 92,2 %), las filas bajo su rótulo de procedencia con las coincidencias antes que los sustitutos, la traza de llamadas colapsada, y la última la cinta de respuesta incompleta, que sirve al 2,0 % y **no lleva color de alarma** porque lo reunido antes del corte sigue sirviendo para vender. La tira de estado dice **una de dos cosas** según si el servicio contestó: con respuesta, el motivo de parada traducido más las vueltas y las consultas; sin ella, sólo el motivo de la degradación — afirmar una parada que no hubo culpaba a la pantalla de un servicio que simplemente no respondió. Los **tres topes del transcript se cuentan en el navegador** antes de enviar, y suman **los turnos del asistente**, no sólo lo que el operario teclea: con el argumentario reenviado, el tope de 12 turnos muerde a los 6 intercambios, así que un contador que contara la mitad llegaría a la mitad de su cuenta con el 422 ya disparado. Cambiar de tienda en medio de una conversación **avisa antes de borrarla**.

- **Family Review Module** (C18b): Pantalla `/admin/family-review`, solo administrador. Audita las familias persistidas —miembros que el vector no respalda y productos sueltos nominados por margen relativo—, registra el veredicto por par `(producto, familia)` con su cronómetro, hace visible la distancia entre un juicio registrado y la pertenencia que lo honraría, y permite corregir la etiqueta de variante de un miembro. Desde C28 **crea familias a mano** con sus miembros y etiquetas en una sola declaración —la vía que alcanza los tipos de pieza sin familia, que la auditoría por margen no puede nominar porque no hay contra qué comparar— y **opera con teclado**.

- **Profile Review Module** (C28): Pantalla `/admin/profile-review`, solo administrador. Revisa perfiles de IA sobre un lote **estratificado por evidencia** y determinista por semilla, con el **texto de origen del producto al lado de los valores** porque el criterio es la fidelidad a ese texto y no la verdad de la pieza —no hay ni una foto en el sistema—, y la ausencia de descripción **se declara** en vez de dejar un hueco. La pregunta cambia con el estrato: *«¿falta algo?»* donde toda la evidencia está en el texto, *«¿es correcto?»* en los demás. Los seis campos de vocabulario cerrado se editan por **selección** y no por texto libre, porque un valor fuera de vocabulario sería inencontrable por el filtro de recuperación y contaminaría la tasa; lo que el texto nombra y la lista no tiene se anota aparte como **hueco de vocabulario**, que es un hallazgo y no una corrección. La talla queda en texto libre: la produce una regex y su espacio de valores no es cerrado. Cronómetro por ítem que viaja en la petición de guardado, barra de aprobación masiva acotada a un campo dentro de un estrato, vista de rechazados con la pregunta invertida, y tarjeta de métricas con las dos poblaciones de tiempo separadas.

- **Return Module**: Registro de devoluciones, búsqueda de venta original, asociación con venta, registro de motivo.

- **Payment Method Module**: Gestión de métodos de pago disponibles (solo admin), asignación de métodos a puntos de venta, activación/desactivación.

- **Point of Sale Module**: Gestión de puntos de venta (solo admin), creación, edición, activación/desactivación, configuración de edición manual de precio, asignación de operadores.

- **User Module**: Gestión de usuarios (solo admin), creación, edición, asignación a puntos de venta, control de roles.

- **Report Module**: Consultas de historial de ventas con filtros, visualización de detalles de ventas, consultas de inventario, consultas de movimientos.

#### Servicios y Componentes Compartidos

- **API Client**: Cliente HTTP (Axios/Fetch) para comunicación con backend, configuración de base URL, manejo de errores HTTP, transformación de respuestas.

- **ML Model Handler**: Gestión del modelo TensorFlow.js/ONNX.js, descarga del modelo, carga en memoria, ejecución de inferencia, gestión de versiones del modelo.

- **State Management**: Gestión de estado global (Redux/Vuex/NgRx según framework), store de autenticación, store de productos, store de inventario.

- **Routing**: Configuración de rutas, protección de rutas según roles, navegación programática.

- **UI Components**: Componentes reutilizables (botones, formularios, tablas, modales), diseño responsive, optimizado para móvil.

#### Diagrama de Componentes del Frontend

```mermaid
C4Component
    title Componentes del Frontend Web Application

    Container_Boundary(frontend, "Frontend Web Application") {
        Component(authModule, "Auth Module", "React/Vue/Angular", "Login y gestión de sesión")
        Component(productModule, "Product Module", "React/Vue/Angular", "Gestión de productos")
        Component(inventoryModule, "Inventory Module", "React/Vue/Angular", "Visualización de inventario")
        Component(saleModule, "Sale Module", "React/Vue/Angular", "Registro de ventas")
        Component(imageRecognitionModule, "Image Recognition Module", "React/Vue/Angular", "Reconocimiento de imágenes con IA")
        Component(returnModule, "Return Module", "React/Vue/Angular", "Gestión de devoluciones")
        Component(paymentModule, "Payment Method Module", "React/Vue/Angular", "Gestión de métodos de pago")
        Component(posModule, "Point of Sale Module", "React/Vue/Angular", "Gestión de puntos de venta")
        Component(userModule, "User Module", "React/Vue/Angular", "Gestión de usuarios")
        Component(reportModule, "Report Module", "React/Vue/Angular", "Consultas y reportes")
        Component(assistedSearchModule, "Assisted Search Module", "React 19 + TypeScript", "Panel de búsqueda asistida (C16)")
        Component(agentPanelModule, "Agent Panel Module", "React 19 + TypeScript", "Panel del agente de venta (C42) · cada turno dueño de su bloque, grupos rotulados por procedencia, traza visible, topes contados antes de enviar")
        Component(salesAssistCardModule, "Sales Assist Card Module", "React 19 + TypeScript", "Ficha de venta con desambiguación por familia (C36)")
        Component(familyReviewModule, "Family Review Module", "React 19 + TypeScript", "Revisión de familias, solo administrador (C18b)")
        Component(profileReviewModule, "Profile Review Module", "React 19 + TypeScript", "Revisión de perfiles de IA, solo administrador (C28)")
        
        Component(apiClient, "API Client", "Axios/Fetch", "Cliente HTTP para comunicación con backend")
        Component(mlModelHandler, "ML Model Handler", "TensorFlow.js/ONNX.js", "Gestión y ejecución del modelo de IA")
        Component(stateManagement, "State Management", "Redux/Vuex/NgRx", "Gestión de estado global")
        Component(routing, "Routing", "React Router/Vue Router", "Navegación y protección de rutas")
        Component(uiComponents, "UI Components", "Material-UI/Vuetify", "Componentes reutilizables")
    }

    Container(api, "Backend API")

    Rel(authModule, apiClient, "Usa")
    Rel(productModule, apiClient, "Usa")
    Rel(inventoryModule, apiClient, "Usa")
    Rel(saleModule, apiClient, "Usa")
    Rel(saleModule, imageRecognitionModule, "Usa")
    Rel(returnModule, apiClient, "Usa")
    Rel(paymentModule, apiClient, "Usa")
    Rel(posModule, apiClient, "Usa")
    Rel(userModule, apiClient, "Usa")
    Rel(reportModule, apiClient, "Usa")
    Rel(assistedSearchModule, apiClient, "Usa")
    Rel(agentPanelModule, apiClient, "Usa")
    Rel(salesAssistCardModule, apiClient, "Usa")
    Rel(familyReviewModule, apiClient, "Usa")
    Rel(profileReviewModule, apiClient, "Usa")
    Rel(assistedSearchModule, salesAssistCardModule, "Accion secundaria de la fila")
    Rel(salesAssistCardModule, saleModule, "Traspasa el miembro elegido")
    
    Rel(imageRecognitionModule, mlModelHandler, "Usa")
    Rel(imageRecognitionModule, apiClient, "Usa", "Obtiene fotos de referencia")
    
    Rel(authModule, stateManagement, "Usa")
    Rel(productModule, stateManagement, "Usa")
    Rel(inventoryModule, stateManagement, "Usa")
    Rel(saleModule, stateManagement, "Usa")
    
    Rel(authModule, routing, "Usa")
    Rel(routing, authModule, "Protege rutas")
    
    Rel(productModule, uiComponents, "Usa")
    Rel(inventoryModule, uiComponents, "Usa")
    Rel(saleModule, uiComponents, "Usa")
    Rel(imageRecognitionModule, uiComponents, "Usa")
    Rel(returnModule, uiComponents, "Usa")
    Rel(paymentModule, uiComponents, "Usa")
    Rel(posModule, uiComponents, "Usa")
    Rel(userModule, uiComponents, "Usa")
    Rel(reportModule, uiComponents, "Usa")
    
    Rel(apiClient, api, "Realiza peticiones HTTP/REST")
```

### 3.3 Componentes del Servicio de IA

El servicio `jbg-ai` se organiza en routers de dominio, capa de recuperación y generación, y servicios transversales. **Estado actual (C31):** existen la fábrica de aplicación, el health, el middleware de trazas, los **siete** routers de dominio con sus esquemas congelados, la capa de stubs deterministas, la dependencia de autenticación de servicio, la **capa de persistencia** (esquema `ai` con pgvector, migraciones Alembic y motor con pool acotado), el **extractor de enriquecimiento (C09)**, el **indexador de `product_document` (C13)**, el **retriever híbrido de `POST /v1/retrieval/products` (C14 + C21)** — umbral 0,65, y desde C21 fusión RRF ponderada de tres listas ordenadas — el **agrupador de familias (C18a)** y la **auditoría de familias persistidas (C18b)** — que reutiliza el veto relativo de C18a con otro universo, nomina huérfanos por margen relativo frente a la cohesión de la familia destino, y **no escribe nada**—, los **sustitutos sobre el embedding almacenado (C26)** y la **capa estructurada de venta asistida (C30a)** — tres modos anclados por pieza, por consulta o por ambas, agrupación por `family_id` nulable, avisos derivados de reglas en un vocabulario cerrado de dos códigos y citas que resuelven a fichero y encabezado — y la **capa de generación del argumentario (C30b)**, que redacta esa prosa en los dos modos anclados a una pieza y la somete a tres comprobaciones deterministas antes de publicarla, degradando a la respuesta de C30a en lugar de fallar cuando alguna no pasa. Inventory sigue planificado; **evals existe desde C24** — arnés de evaluación con golden set versionado en `ai-service/evals/golden/`, líneas base v0→v2 medidas sobre relevancia graduada y persistencia opcional en `ai.eval_run` / `ai.eval_case` / `ai.eval_result`.

#### Routers de Dominio (`/v1/*`)

- **Retrieval Router**: búsqueda de productos y sustitutos sobre el índice vectorial, con sobre-recuperación y abstención por umbral. **Products existe y es híbrido (C14 + C21); substitutes existe desde C26**, sobre el embedding ya almacenado en la fila origen y sin llamada a proveedor.
- **Assist Router**: generación de respuesta estructurada agrupada por familia, con avisos calculados por reglas y citas verificables.
- **Inventory Router**: propuestas de reposición, traslado y rotación generadas por el agente de inventario.
- **Enrich Router**: extracción estructurada de perfiles de producto con confianza por campo.
- **Families Router**: agrupación de productos en familias de variantes. **Existe, con dos rutas**: `POST /v1/families/suggest` **(C18a)**, que propone familias nuevas, y `POST /v1/families/audit` **(C18b)**, que audita las que ya existen — miembros que los vectores no sostienen y huérfanos candidatos, que son la misma comparación leída desde los dos lados de la pertenencia. Fueron la novena y la décima ruta del contrato congelado. Ninguna de las dos escribe: aprobar y registrar el veredicto son de .NET.
- **Index Router**: sincronización del índice mediante cursor `since` y consulta de deriva.
- **Evals Router**: resultados del harness de evaluación (solo perfil de desarrollo).

#### Capa de Recuperación y Generación

- **Hybrid Retriever**: fusiona búsqueda vectorial (HNSW sobre pgvector) y léxica (`ts_rank` en español sobre `tsv`, con expansión de sinónimos) mediante **RRF ponderado sobre tres listas** —la tecleada, la expandida y la vectorial— truncadas a una profundidad común. **Entregado en C21**, con la rama vectorial a menor peso y filtros estructurales que degradan sin excluir.
- **Query Analyzer**: extrae por reglas las restricciones estructurales de la consulta (banda de precio, tipo de pieza, talla, materiales).
- **Embedding Client**: genera embeddings solo cuando cambia el `source_hash`, con versionado por modelo.
- **Family Grouper** (`jbg_ai.families`): agrupa por raíz de nombre dentro de un tipo de pieza, fusiona por material y guarda contra raíces degeneradas. **Existe (C18a).** Determinista y sin red: **no llama a ningún LLM ni al proveedor de embeddings**, porque los vectores ya están en el índice. El embedding **veta, no agrupa**, y lo hace en relativo —contra las otras familias propuestas, nunca contra un umbral absoluto— marcando al miembro para revisión en lugar de eliminarlo.
- **Intent Router** (`jbg_ai.assist`, módulos `routing`, `router_llm`): clasifica la consulta libre **antes de que corra ninguna recuperación**, sobre tres ejes —si se atiende, con qué índice y si la consulta basta para buscar—. **Existe (C31).** Una sola llamada al proveedor, **sin reintento y sin reparación**: la etiqueta se valida contra un conjunto cerrado en el parseo, así que un valor inventado es un fallo de parseo y nunca un valor que se propague. Rechaza con **dos códigos distintos** —fuera de dominio y fuera de catálogo— y repregunta desde un catálogo cerrado de plantillas elegido **en código**, porque el contrato tipa ese campo como prosa y el frontend no puede resolverlo. Sin credencial no se construye, y entonces el servicio se comporta exactamente como lo dejó C30b: ése es el *fail-open*, y es a la vez la ablación y el rollback. Corre **sólo** en el modo de consulta libre: el modo con pieza no tiene consulta que clasificar, y el de pieza con pregunta es `both` por construcción.
- **Generation Service** (`jbg_ai.assist`, módulos `prompt`, `llm`, `verification`, `pitch`): redacta el argumentario a partir de metadatos aprobados y chunks del corpus, emitiendo `{{price}}` y `{{stock}}` como placeholders que resuelve .NET. **Existe (C30b), y desde C31 en los tres modos**: la consulta libre redacta sobre la **ruta que el enrutador decidió**, con una segunda forma de *payload* de la que se excluyen los identificadores internos y los scores. Lo que sigue cortando **antes** de cualquier llamada es la abstención, el rechazo del enrutador y la repregunta. El prompt está versionado en fichero (`prompts/assist/v1.md`) y fijado a su constante por un test. La salida pasa por **tres comprobaciones deterministas y ningún juez** — resolución del identificador, correspondencia del tramo que el modelo declara haber apoyado con cada cita, y puerta numérica por pertenencia al **objeto de payload** más adyacencia a marca de moneda o de existencias, que rechaza aunque la cifra esté admitida. Una sola reparación, **techo literal de dos llamadas** y degradación a la respuesta de C30a en vez de error. El texto no se persiste ni se escribe en ningún log: la traza lleva versión, modelo, uso, latencia, citas y un **hash**.
- **Guardrails / Intent Router**: clasifica la intención, detecta consultas fuera de dominio y aplica la política de abstención.
- **Agent Loop** (`jbg_ai.assist`, módulos `agent`, `agent_llm`, `transcript`, sobre el registro `tools` de C32a): bucles agénticos con *tools* de solo lectura y puntos de intervención humana. **Existe para el agente de venta (C32b)**, en ruta propia —`POST /v1/assist/agent`— con seis presupuestos, `partial: true` y un motivo de parada de vocabulario cerrado; `POST /v1/assist/sale` no cambia. El puerto del modelo no tiene campo de prosa: el argumentario lo sigue escribiendo el Generation Service sobre la evidencia que el bucle reúne.

#### Servicios Transversales

- **Settings**: configuración por entorno con pydantic-settings y *fail-fast* de variables obligatorias. **Existe (C01).**
- **TraceId Middleware**: propaga `trace_id` desde la cabecera o el claim del JWT hacia los logs estructurados. **Existe (C01).**
- **Service Auth Dependency**: valida el JWT interno HS256 y construye el `ServicePrincipal`; el scope del token prevalece sobre el body. **Existe (C02).**
- **Stub Layer**: respuestas deterministas bajo `STUB_MODE`; con el flag desactivado, la ruta sin implementación real responde 501. **Existe (C02).** Excepciones reales: enrich (C09), index (C13), `POST /v1/retrieval/products` (C14), `POST /v1/families/suggest` (C18a), `POST /v1/families/audit` (C18b), `GET /v1/evals/runs` (C24, que sirve desde `ai.eval_run` y sólo bajo perfil de desarrollo), `POST /v1/retrieval/substitutes` (C26), `POST /v1/assist/sale` (C30a) y `POST /v1/assist/agent` (C32b, que bajo `STUB_MODE=true` sirve su fixture sin correr el bucle). Con C30a **sólo `POST /v1/inventory/propose` sigue respondiendo 501**, y el fixture de assist sobrevive bajo `STUB_MODE=true`.
- **Service Auth Dependency**: valida el JWT interno HS256 y construye el `ServicePrincipal`; el scope del token prevalece sobre el body.
- **Stub Layer**: respuestas deterministas bajo `STUB_MODE` para que .NET integre sin LLM ni base de datos.
- **Eval Harness**: golden set, métricas de recuperación y validador anti-alucinación (ejecución offline).

#### Diagrama de Componentes del Servicio de IA

```mermaid
C4Component
    title Componentes del AI Service (jbg-ai)

    Container_Boundary(ai, "AI Service (jbg-ai)") {
        Component(retrievalRouter, "Retrieval Router", "FastAPI", "Productos y sustitutos")
        Component(assistRouter, "Assist Router", "FastAPI", "Venta asistida con citas")
        Component(inventoryRouter, "Inventory Router", "FastAPI", "Propuestas de inventario")
        Component(enrichRouter, "Enrich Router", "FastAPI", "Enriquecimiento de catálogo")
        Component(familiesRouter, "Families Router", "FastAPI", "Propuestas de familia (C18a) · no escribe")
        Component(indexRouter, "Index Router", "FastAPI", "Sincronización del índice")
        Component(evalsRouter, "Evals Router", "FastAPI", "Resultados de evaluación (dev)")

        Component(auth, "Service Auth Dependency", "PyJWT", "Valida el JWT interno y fija el scope")
        Component(stubs, "Stub Layer", "Python", "Respuestas deterministas bajo STUB_MODE")
        Component(retriever, "Hybrid Retriever", "pgvector + tsvector", "Vectorial + léxico fusionados con RRF")
        Component(analyzer, "Query Analyzer", "Python", "Restricciones estructurales por reglas")
        Component(embeddings, "Embedding Client", "Proveedor LLM", "Embeddings con versionado")
        Component(generation, "Generation Service", "LLM", "Argumentario con citas y placeholders")
        Component(guardrails, "Guardrails / Intent Router", "Python", "Intención, abstención y seguridad")
        Component(agent, "Agent Loop", "Python", "Bucles agénticos con tools de solo lectura")
        Component(persistence, "Persistence", "SQLAlchemy 2 + Alembic", "Esquema ai: pool acotado y perezoso, migraciones, índices HNSW/GIN")
        Component(settings, "Settings", "pydantic-settings", "Configuración con fail-fast")
        Component(trace, "TraceId Middleware", "Starlette", "Propagación de trace_id")
    }

    Container(api, "Backend API (.NET)")
    ContainerDb(db, "PostgreSQL · esquema ai")
    System_Ext(llm, "Proveedor LLM")

    Rel(api, auth, "Bearer JWT interno")
    Rel(auth, retrievalRouter, "Inyecta ServicePrincipal")
    Rel(auth, assistRouter, "Inyecta ServicePrincipal")
    Rel(auth, inventoryRouter, "Inyecta ServicePrincipal")
    Rel(auth, enrichRouter, "Inyecta ServicePrincipal")
    Rel(auth, indexRouter, "Inyecta ServicePrincipal")
    Rel(auth, evalsRouter, "Inyecta ServicePrincipal")

    Rel(retrievalRouter, stubs, "Usa si STUB_MODE")
    Rel(retrievalRouter, analyzer, "Usa")
    Rel(retrievalRouter, retriever, "Usa")
    Rel(assistRouter, retriever, "Usa")
    Rel(assistRouter, generation, "Usa")
    Rel(assistRouter, guardrails, "Usa")
    Rel(inventoryRouter, agent, "Usa")
    Rel(enrichRouter, generation, "Usa")
    Rel(indexRouter, embeddings, "Usa")

    Rel(retriever, persistence, "Obtiene sesión")
    Rel(persistence, db, "Pool acotado a 5 conexiones")
    Rel(retriever, db, "Consulta vectorial y léxica")
    Rel(embeddings, db, "Escribe documentos y vectores")
    Rel(indexRouter, api, "Feed paginado since-cursor")
    Rel(generation, llm, "Genera texto")
    Rel(embeddings, llm, "Genera embeddings")
    Rel(trace, settings, "Usa")
```

---

### Relaciones entre Componentes Backend y Frontend

#### Flujo de Autenticación
1. **Auth Module** (Frontend) → **API Client** → **Backend API** → **Authentication Service** → **Repositories** → **PostgreSQL Database**
2. Token JWT retornado y almacenado en **State Management**
3. **API Client** incluye token en todas las peticiones mediante interceptor

#### Flujo de Reconocimiento de Imágenes y Venta
1. **Image Recognition Module** (Frontend) captura foto
2. **ML Model Handler** procesa imagen localmente
3. **Image Recognition Module** muestra sugerencias
4. **Sale Module** recibe producto seleccionado
5. **Sale Module** → **API Client** → **Backend API** → **Sale Service**
6. **Sale Service** usa **Stock Validation Service** y **Payment Method Validation Service**
7. **Sale Service** → **Repositories** → **PostgreSQL Database**
8. **Sale Service** → **File Storage Service** → **Object Storage**

#### Flujo de Importación de Productos
1. **Product Module** (Frontend) sube archivo Excel
2. **Product Module** → **API Client** → **Backend API** → **Product Service**
3. **Product Service** usa **Excel Import Service** para procesar archivo
4. **Product Service** → **Repositories** → **PostgreSQL Database**

#### Flujo de Búsqueda Asistida por IA
1. El operador escribe una consulta en lenguaje natural en el **Assisted Search Panel** (Frontend)
2. **API Client** → **Backend API** (JWT de usuario) → **AI Gateway Client**
3. **AI Gateway Client** firma un **JWT interno de servicio** con `user_id`, `role`, `pos_id` y `trace_id`, y llama a **Retrieval Router** de `jbg-ai`
4. **Query Analyzer** extrae restricciones estructurales; **Hybrid Retriever** consulta el esquema `ai` y devuelve candidatos sobre-recuperados con sus razones
5. El **hidratador** del Backend API resuelve precio, stock y permisos reales contra el esquema `public`, descarta lo inválido y trunca al `top_k` pedido
6. Si se pide asistencia, **Assist Router** genera el argumentario con citas y placeholders, que el Backend API sustituye antes de responder
7. Si `jbg-ai` no responde dentro del timeout, el **circuit breaker** degrada al buscador léxico y marca `ai_available: false`

#### Flujo del card de venta (C34)
1. Con una pieza delante, el card (C36) pide en paralelo `POST /api/ai/products/{id}/sales-assist` —`{pointOfSaleId, question?}`, la pregunta **siempre en el cuerpo**— y `GET /api/ai/products/{id}/substitutes`
2. **Sales Assist Service** y **Substitutes Service** autorizan el punto de venta y comprueban con una hidratación que la tienda lleva la pieza: **400 / 403 / 404 sin llamar a la IA**
3. **AI Gateway Client** llama a `POST /v1/assist/sale` por el cliente generativo (10 s, circuito propio) o a `POST /v1/retrieval/substitutes` por el de recuperación, con el `pos_id` en el JWT interno y nunca en el cuerpo
4. El Backend API hidrata el grupo o la ventana contra `public` en una consulta: miembros que la tienda no lleva fuera, orden de la IA intacto; en sustitutos, sólo `quantity > 0`
5. Calcula `stock_critical` y `family_members_out_of_stock`, ajusta `family_has_variants` a lo que sobrevive, y sustituye `{{price}}` («39,90 €») y `{{stock}}` (el entero) **con los valores de la pieza anclada**; un marcador sin resolver retira el argumentario y no la respuesta
6. Con la IA caída o el interruptor apagado, el card sale igual —`aiAvailable: false`— con la pieza y su familia leída de `ProductFamily`, y los sustitutos con `outcome: ai_unavailable`

---

## Notas sobre Desarrollo vs Producción

### Almacenamiento de Archivos

**Desarrollo:**
- **File Storage Service** utiliza sistema de archivos local (`./uploads/`)
- Configuración mediante variable de entorno `Storage__Type=Local`
- Sin necesidad de credenciales de cloud

**Producción:**
- **File Storage Service** utiliza AWS S3 o Azure Blob Storage
- Configuración mediante variable de entorno `Storage__Type=Cloud`
- Credenciales gestionadas mediante AWS Secrets Manager / Azure Key Vault
- Políticas de acceso restringidas y pre-signed URLs para acceso temporal

### Base de Datos

**Desarrollo:**
- PostgreSQL ejecutándose en contenedor Docker local
- Puerto 5432 expuesto localmente
- Datos de prueba y seeders para desarrollo
- Sin replicación ni backups automáticos

**Producción:**
- PostgreSQL gestionado (RDS en AWS o Azure Database for PostgreSQL)
- Conexión mediante connection string desde secrets
- Backups automáticos configurados
- Connection pooling optimizado (5-10 conexiones máx para free-tier)

### Frontend

**Desarrollo:**
- Servidor de desarrollo local (Vite/Webpack dev server)
- Hot Module Replacement (HMR) activo
- Source maps para debugging
- Sin optimizaciones de producción

**Producción:**
- Build optimizado y minificado
- En AWS actual: mismo origen que la API (nginx + Docker); en otras variantes, CDN (CloudFront/Azure CDN)
- Cache de assets: cabeceras HTTP / CDN según despliegue
- Code splitting y lazy loading activados

### Seguridad

**Desarrollo:**
- HTTP sin HTTPS (localhost)
- CORS permisivo para localhost
- Logging detallado en consola
- Stack traces completos en errores

**Producción:**
- HTTPS obligatorio (SSL/TLS)
- CORS restrictivo (solo dominios permitidos)
- Logging estructurado a CloudWatch/Application Insights
- Mensajes de error genéricos (sin detalles internos)
- Rate limiting activo

### Monitoreo

**Desarrollo:**
- Logging manual en consola
- Sin métricas automáticas
- Health checks básicos

**Producción:**
- CloudWatch Logs (AWS) o Application Insights (Azure)
- Métricas automáticas (request rate, response time, error rate)
- Health checks en `/health` endpoint
- Alertas configuradas para errores críticos

### Modelo de IA

**Desarrollo:**
- Modelo descargado desde servidor de desarrollo o local
- Sin optimizaciones de tamaño
- Debugging activo

**Producción:**
- Modelo distribuido mediante CDN
- Modelo optimizado y comprimido
- Versionado del modelo para actualizaciones sin interrupciones

### Servicio de IA (`jbg-ai`)

**Desarrollo:**
- Servicio `jbg-ai` del Compose, puerto `8001` publicado solo en local
- PostgreSQL con imagen `pgvector/pgvector:pg15` en el puerto `5433`
- `STUB_MODE` activo: respuestas deterministas sin LLM ni base de datos
- Secreto del JWT interno definido en el Compose, nunca reutilizable en producción

**Producción:**
- Contenedor en la misma EC2, en red Docker interna; **el puerto no se publica en nginx**
- Índice vectorial en el esquema `ai` de la RDS compartida
- Secretos (JWT interno, claves del proveedor LLM) en SSM Parameter Store
- Timeouts, reintento único y circuit breaker aplicados desde el backend .NET
- Degradación explícita: si el circuito se abre, el sistema responde con el buscador léxico

---

## Resumen de Componentes por Épica

### EP1: Gestión de Productos
- **Backend**: Product Service, Excel Import Service, File Storage Service
- **Frontend**: Product Module, API Client

### EP2: Gestión de Inventario
- **Backend**: Inventory Service, Excel Import Service
- **Frontend**: Inventory Module, API Client

### EP3: Registro de Ventas
- **Backend**: Sale Service, Stock Validation Service, Payment Method Validation Service, File Storage Service
- **Frontend**: Sale Module, Image Recognition Module, API Client

### EP4: Reconocimiento de Imágenes con IA
- **Backend**: File Storage Service (para fotos de referencia)
- **Frontend**: Image Recognition Module, ML Model Handler

### EP5: Gestión de Devoluciones
- **Backend**: Return Service, Stock Validation Service
- **Frontend**: Return Module, API Client

### EP6: Gestión de Métodos de Pago
- **Backend**: Payment Method Service, Payment Method Validation Service
- **Frontend**: Payment Method Module, API Client

### EP7: Autenticación y Gestión de Usuarios
- **Backend**: Authentication Service, User Service
- **Frontend**: Auth Module, User Module, API Client

### EP8: Gestión de Puntos de Venta
- **Backend**: Point of Sale Service (incluye configuración de `AllowManualPriceEdit`)
- **Frontend**: Point of Sale Module (incluye switch de edición manual de precio), API Client

### EP9: Consultas y Reportes
- **Backend**: Report Service
- **Frontend**: Report Module, API Client

### EP10: Gestión de Componentes de Joyas
- **Backend**: Component Service, Component Assignment Service, Component Template Service
- **Frontend**: Product Module (subsección de componentes, reportes de márgenes), API Client

### EP11: Plataforma del Servicio de IA
- **AI Service**: Settings, TraceId Middleware, Service Auth Dependency, Stub Layer
- **Backend**: AI Gateway Client (cliente tipado con Polly, emisión del JWT interno)
- **Base de datos**: esquema `ai` con pgvector

### EP12: Corpus y Enriquecimiento del Catálogo
- **AI Service**: Enrich Router, Generation Service, Embedding Client
- **Backend**: ProductAiProfile (entidad y ciclo de revisión), endpoints de feed de indexación

### EP13: Familias de Producto y Desambiguación
- **AI Service**: Hybrid Retriever (propuesta de familias por similitud)
- **Backend**: ProductFamily y ProductFamilyMember (entidades), Product Family Service (pertenencia declarativa), Product Families Controller (`POST`/`GET`/`PUT /api/product-families`, `PUT /api/product-families/{id}/members`, `GET /api/products/{id}/family`)
- **Frontend**: pantalla de revisión y aprobación por lotes

### EP14: Búsqueda Semántica Híbrida
- **AI Service**: Retrieval Router, Query Analyzer, Hybrid Retriever, Index Router
- **Backend**: AI Search Endpoint, hidratador, circuit breaker y fallback léxico
- **Frontend**: Assisted Search Panel

### EP15: Venta Asistida, Sustitutos y Agentes
- **AI Service**: Assist Router, Generation Service, Guardrails / Intent Router, Agent Loop
- **Backend**: Sales Assist Service y Substitutes Service tras `AiSalesAssistController` (C34: `POST /api/ai/products/{id}/sales-assist`, `GET /api/ai/products/{id}/substitutes`), con la familia generativa `ai-assist` del AI Gateway Client, y **Agent Assist Service tras `AiSearchController`** (C42: `POST /api/ai/search/agent`), con la cuarta familia `ai-agent` y su propio interruptor, cupo, presupuesto y circuito. *(Los complementarios salieron con C27.)*
- **Frontend**: Sales Assist Card Module (C36) — ficha de venta en `/sales/new/assist/:productId` con carga perezosa y tres entradas, una petición por visita sin reintento automático, desambiguación por familia **sin preselección** con un botón de venta por miembro, seis `pitchStatus` en cinco mensajes, citas con su alcance y los cuatro desenlaces de sustitutos — y **Agent Panel Module (C42)**, panel del agente en `/sales/new/agent` con cuarta tarjeta en el hub, un bloque de respuesta por turno, grupos rotulados por procedencia, traza de llamadas colapsada, los diez motivos de parada en castellano y los tres topes del transcript contados antes de enviar

### EP16: Inventario Asistido y Señales de Demanda
- **AI Service**: Inventory Router, Agent Loop
- **Backend**: Demand Signal Service, InventoryRecommendation, perfil comercial por POS
- **Frontend**: revisión de recomendaciones y vista imprimible

### EP17: Evaluación y Observabilidad de IA
- **AI Service**: Eval Harness, Evals Router
- **Backend**: ProductSearchEvent (telemetría consulta → selección), Product Search Event Service (registro en dos escrituras: la búsqueda la escribe el servidor, la selección la reporta el cliente), AI Search Events Controller (`POST /api/ai/search-events/{id}/selection`)

---

## Consideraciones de Arquitectura

### Patrones Utilizados

- **Repository Pattern**: Abstracción de acceso a datos en el backend
- **Service Layer**: Separación de lógica de negocio de controladores
- **Dependency Injection**: Inyección de dependencias en ASP.NET Core
- **Strategy Pattern**: File Storage Service permite cambiar entre almacenamiento local y cloud
- **Factory Pattern**: Creación de servicios según configuración

### Optimizaciones para Free-tier

- **Connection Pooling**: Máximo 5-10 conexiones simultáneas a PostgreSQL
- **Paginación**: Todas las listas paginadas (máx 50 items/página)
- **Caching**: Cache en memoria para productos y métodos de pago frecuentes
- **Índices Selectivos**: Solo índices necesarios para consultas frecuentes
- **Compresión**: Respuestas comprimidas (gzip) para reducir ancho de banda

### Escalabilidad Futura

El modelo está preparado para escalar:
- **Read Replicas**: Para reportes pesados
- **Caching Distribuido**: Redis para cache compartido entre instancias
- **Microservicios**: Separación de servicios si es necesario en el futuro
- **CDN Ampliado**: Más puntos de presencia para mejor rendimiento global

### Entorno de Demostración (C17): un tercer despliegue

Las notas anteriores contrastan dos entornos. Desde C17 hay **tres**, y el nuevo cambia dos de los contenedores del Nivel 2 sin cambiar ninguno de los componentes del Nivel 3 — la misma aplicación, otra topología.

| Contenedor del Nivel 2 | Producción | Demostración |
|---|---|---|
| Proxy inverso | nginx en el anfitrión, con cliente de certificados y tarea programada | **Caddy como contenedor**, con emisión y renovación de certificado integradas |
| Base de datos | **RDS** PostgreSQL gestionada, fuera de la instancia | **PostgreSQL con pgvector en contenedor**, con volumen persistente |
| Servicio de IA | alcanzable solo desde el backend en la red de contenedores | igual, y además **sin puertos publicados** en tres capas independientes |
| Cuenta AWS | la de la tienda | **una cuenta distinta**, con estado de Terraform propio |

La consecuencia para este modelo es una sola, y afecta al Nivel 3: como el navegador no puede alcanzar el servicio de IA, la tarjeta de estado del panel de administración **no es un componente de frontend que hable con Python**, sino uno que consume un endpoint .NET (`AiHealthController`) que hace de intermediario, con su propio cliente HTTP y sin el cortacircuitos del camino principal.

Detalle en [Arquitectura del Sistema](arquitectura.md#entorno-de-demostración-c17) y procedimiento en [`deploy/demo/README.md`](../deploy/demo/README.md).

---

## Referencias

- [Arquitectura del Sistema](arquitectura.md)
- [Modelo de Datos](modelo-de-datos.md)
- [Épicas del MVP y del Proyecto Final de IA](epicas.md)
- [README del Proyecto](../README.md)
- [Diseño del sistema de IA](Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md) — frontera de responsabilidad (§6) y diseño RAG (§7)
- [Plan de changes OpenSpec del PF](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) — C01–C39

