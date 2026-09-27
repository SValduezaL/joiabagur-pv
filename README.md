# Sistema de Gestión de Puntos de Venta para Joyería

## Índice

0. [Ficha del proyecto](#0-ficha-del-proyecto)
1. [Descripción general del producto](#1-descripción-general-del-producto)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Modelo de datos](#3-modelo-de-datos)
4. [Especificación de la API](#4-especificación-de-la-api)
5. [Historias de usuario](#5-historias-de-usuario)
6. [Tickets de trabajo](#6-tickets-de-trabajo)

---

## 0. Ficha del proyecto

### 0.1. Tu nombre completo

Marcello Orrico

### 0.2. Nombre del proyecto

Sistema de Gestión de Puntos de Venta para Joyería (Joiabagur PV)

### 0.3. Descripción breve del proyecto

Sistema de gestión integral para una joyería que opera en múltiples puntos de venta (propios y de terceros). Permite gestionar inventario, registrar ventas y facilitar la identificación de productos mediante reconocimiento de imágenes con IA (inferencia y entrenamiento en el navegador con TensorFlow.js).

### 0.4. URL del proyecto

https://pv.joiabagur.com

**Entorno de demostración del Proyecto Final de IA:** https://52-49-209-14.sslip.io

Despliegue aislado en una cuenta AWS propia, con el catálogo real y sus 1.200 documentos vectorizados cargados, y **cuatro cuentas de demostración** —una de administración y **tres de operación, cada una en un punto de venta con un surtido deliberadamente distinto**— cuyas credenciales se entregan aparte. Las diferencias de surtido son parte de lo que hay que probar: la **abstención**, los **sustitutos** y el **pivote del agente** a piezas alternativas sólo son observables desde la tienda que los provoca, así que entrar con una sola cuenta de operación deja fuera comportamientos que sí existen. El nombre de dominio deriva de la IP elástica y es un parámetro del despliegue: migrar a un dominio propio no reconstruye ninguna imagen.

### 0.5. URL o archivo comprimido del repositorio

https://github.com/marcello-clearcust/joiabagur-pv

---

## 1. Descripción general del producto

### 1.1. Objetivo

El producto tiene como propósito ofrecer una solución integral de gestión para una joyería con varios puntos de venta (tiendas propias y ubicaciones de terceros como hoteles). Aporta valor al centralizar el catálogo de productos, el inventario por ubicación, el registro de ventas con método de pago y la identificación de productos mediante IA en el punto de venta, reduciendo errores y agilizando el proceso. Está dirigido a administradores (gestión completa) y operadores (registro de ventas e inventario en sus puntos asignados).

### 1.2. Características y funcionalidades principales

- **Gestión de productos e inventario:** Catálogo centralizado (SKU, precio, descripción, colección), gestión de stock por punto de venta con vista centralizada, importación y actualización desde Excel, edición manual de productos e inventario, asociación de fotos de referencia para reconocimiento de imágenes.
- **Registro de ventas:** Captura de ventas por punto de venta (manual o con IA), foto opcional por transacción, registro de método de pago, historial con trazabilidad, validación de stock en tiempo real, actualización atómica de inventario, alertas de stock bajo no bloqueantes.
- **Reconocimiento de productos con IA:** Inferencia en el cliente con TensorFlow.js, identificación mediante cámara en el punto de venta, 3–5 sugerencias ordenadas por confianza (umbral 40%), validación manual del operador, fallback a entrada manual si la confianza es baja.
- **Entrenamiento del modelo de IA:** Entrenamiento en el navegador con TensorFlow.js (sin Python), un clic desde el panel de administración, aceleración GPU vía WebGL 2.0, métricas de salud del modelo y progreso en tiempo real.
- **Gestión de métodos de pago:** Lista general (Efectivo, Bizum, Transferencia, Tarjeta TPV propio/punto de venta, PayPal), asignación por punto de venta y registro del método en cada venta.
- **Gestión de usuarios:** Roles Administrador y Operador, autenticación con usuario y contraseña, operadores asociados a puntos de venta concretos.
- **Otras funcionalidades:** Devoluciones, ajustes manuales de inventario, historial de ventas y movimientos de stock, dashboard con estadísticas y stock crítico.
- **Búsqueda semántica y venta asistida (en desarrollo):** Proyecto Final del Máster de IA. Añade búsqueda semántica sobre el catálogo, sugerencia de sustitutos y argumentario de venta asistido, mediante el microservicio `jbg-ai`. A día de hoy están congelados el contrato HTTP y la autenticación entre servicios, el backend .NET ya dispone del cliente tipado que los consume —con timeouts, reintento único y cortacircuitos— y la capa de persistencia vectorial está lista: esquema `ai` con pgvector, migraciones propias e índices HNSW por similitud coseno. La recuperación vectorial de `POST /v1/retrieval/products` (C14) y el endpoint .NET de búsqueda asistida con hidratación autoritativa (C15) están entregados: el operador puede buscar en lenguaje natural y recibir resultados con el precio y el stock reales de su tienda. **El panel del operador (C16) también está entregado**: describe la pieza con sus palabras, distingue en pantalla los cuatro modos de no encontrar nada —la IA no encontró, la tienda no lo tiene, la asistencia no está sirviendo, o se han hecho demasiadas búsquedas seguidas— y arrastra la búsqueda hasta la caja, de modo que la venta queda atribuida a la consulta que la originó. **Y desde C17 todo lo anterior es demostrable en público**: un entorno aislado en una cuenta AWS propia, con TLS válido, el catálogo real y sus 1.200 documentos vectorizados cargados, y una tarjeta en el panel de administración que informa del estado del servicio de IA — incluida la discrepancia entre el modelo de embeddings configurado y el del índice, que de otro modo devolvería resultados sin sentido sin dar ningún error. **Y el catálogo ya está agrupado (C18a)**: las variantes de una misma pieza —el mismo anillo en sus tallas, el mismo colgante en plata y en oro— dejan de ser 486 productos sueltos y son 156 familias, propuestas por un algoritmo determinista y aprobadas por una persona antes de escribirse. **Y esas familias ya se revisan (C18b)**: una pantalla de administración las enumera, permite disolver la que esté mal y señala los productos que se parecen a una familia sin pertenecer a ella, de modo que la calidad del agrupamiento deja de ser una suposición y pasa a ser una cola que alguien trabaja. **Y el buscador ya entiende cómo se habla en la tienda (C20)**: quien atiende puede escribir «gargantilla», «sortija» o «criollas» y encontrar lo que el catálogo llama «collar», «anillo» y «pendientes», con un diccionario curado a mano —sin texto inventado por la IA y corregible en un commit— que además resuelve algo que no es de vocabulario sino del idioma: quien teclea sin eñe o en plural obtenía cero resultados. **Y desde C21 el buscador es híbrido de verdad**: combina la búsqueda por significado con la búsqueda por texto y las fusiona por consenso, de modo que un resultado que las dos vías señalan sube por encima del que sólo ve una. Sobre el catálogo real pasa de 157 aciertos de 240 a 224, y cada resultado dice en pantalla qué vía lo encontró — incluido el caso en que la parte semántica no ha podido responder y contesta sólo la de texto, que antes se servía sin avisar. **Y desde C22 el buscador sabe qué tiene cada tienda**: hasta ahora ordenaba el catálogo entero y el backend descartaba después lo que ese punto de venta no lleva, así que la página llegaba corta — medido sobre el catálogo real, ocho de los once puntos de venta se quedaban por debajo de una página en al menos seis de cada veinte búsquedas, y en el peor caso sobrevivía **un solo producto**. Ahora la búsqueda se acota al surtido de la tienda desde el principio, lo que está agotado baja en la lista en lugar de desaparecer, y si el inventario que maneja la IA se queda desfasado el sistema lo declara y deja de filtrar, antes que esconder un producto que la tienda sí tiene. **Y desde C24 hay una respuesta medida a la pregunta que sostiene el proyecto** — ¿la búsqueda semántica mejora de verdad lo que la joyería tenía? Hasta aquí ninguna de las decisiones del buscador se había tomado con una métrica de relevancia. Ahora sí: sobre **48 consultas juzgadas a mano** con una escala de tres grados y un criterio escrito antes de etiquetar, el buscador que la joyería tenía acierta **0,082** de nDCG@5, el buscador por texto en español **0,454** y la búsqueda híbrida que se entrega **0,603**. Leído en dos saltos: tokenizar en español aporta **+0,372** y es gratis, y la recuperación semántica aporta **+0,149** encima. La medición también **refuta** la rúbrica con la que se habían tomado esas decisiones —daba a la parte semántica siete puntos de ciento veinte, y contra un juez que no es parte del pleito la parte semántica bate al buscador por texto— y, cuando el propio barrido encontró una configuración mejor, la regla escrita **antes** de medir bloqueó el cambio porque empeoraba en el subconjunto de control. Medir sirve para decidir, y también para no hacerlo. **Y lo primero que ese juez encontró (C25) fue un defecto en el propio buscador: la fusión no fusionaba, concatenaba.** La búsqueda por texto votaba con tanta fuerza que sus sesenta resultados ganaban **siempre** al mejor resultado de la búsqueda por significado —medido en el informe publicado, una pieza perfecta que la parte semántica ponía la primera aparecía en el puesto **33**—, y eso explicaba por qué el híbrido rendía peor que la parte semántica sola justo en las consultas descritas con palabras propias. Al componer la fusión **en dos etapas**, para que cada vía pese lo que dice pesar, el acierto sube de **0,603** a **0,740** de nDCG@5. Además el buscador aprende dos cosas que importan en el mostrador: **lo que la tienda no tiene deja de estorbar** —la señal de disponibilidad retira el **91 %** de las piezas agotadas de los cinco primeros resultados, sin esconderlas— y **sabe callar** cuando el catálogo no puede responder, con una regla que mira si todos los candidatos son igual de mediocres en vez de fiarse de un umbral fijo, y que no silencia ni una sola de las consultas que la tienda sí puede contestar. Tres objetivos numéricos **no se alcanzan y se declaran como tales** en lugar de ajustar el listón después de medir. **Y desde C26 el mostrador tiene respuesta cuando la pieza correcta no está**: pidiendo sustitutos de un producto concreto, el sistema ofrece alternativas del mismo tipo de pieza —un anillo no sustituye a un colgante— ordenadas por parecido real, poniendo delante las que sí son de la talla que se pidió sin desterrar a la cola las variantes de la misma pieza, y dejando lo agotado más abajo pero **a la vista**, porque esconder lo que la tienda quizá sí pueda vender es peor que mostrarlo último. Cada alternativa dice por qué está ahí, y cuando no hay dato para comparar estilos lo declara en vez de dar un cero que parecería un juicio. **Y desde C30a el mostrador recibe además la ficha ordenada de la pieza**: las variantes de la misma pieza agrupadas, los avisos que importan al vender —que la familia tiene otras tallas, que a esta le falta la etiqueta— y las citas del corpus comercial de la joyería, que resuelven al fichero y al apartado exactos de donde sale cada afirmación. **Y desde C30b ese material ya viene redactado**: quien atiende recibe un argumentario en prosa, escrito por un modelo de lenguaje, que **no puede inventarse una cifra ni una fuente**. Tres comprobaciones deterministas —sin ningún segundo modelo haciendo de juez— lo revisan antes de que salga: que cada fuente citada estuviera de verdad entre las que se le dieron, que el modelo señale qué frase concreta de su propio texto apoya cada cita y que esa frase exista, y que ningún número del argumentario esté fuera de los datos entregados ni pegado a un símbolo de moneda — porque el propio corpus dice que el oro de 18 quilates son 750 milésimas, así que «750 €» pasaría cualquier lista blanca. El precio y el stock viajan siempre como huecos que rellena el backend con la verdad de esa tienda. Si algo no pasa, el sistema pide **una** corrección y, si reincide, **retira el argumentario o esa cita concreta y sirve el resto** en lugar de fallar: quien atiende nunca se queda con una pantalla vacía. Medido sobre 120 generaciones reales, **118 no escriben ni un dígito** y ningún argumentario se perdió por el camino. **Y desde C31 el sistema sabe cuándo no debe contestar.** Antes de buscar nada clasifica lo que se le ha pedido, y distingue dos negativas que no son la misma: *«esto no es de una joyería»* y *«esto es de joyería y esta tienda no lo lleva»* —un salero de plata, una correa de reloj—, que ante un cliente se dicen de forma distinta y por eso viajan con códigos distintos. Si lo escrito no basta para buscar —«algo bonito»—, devuelve una repregunta que **nombra lo que falta** en vez de cinco piezas al azar, y esa frase la elige el código de un catálogo cerrado, no el modelo. Hay además una regla dura, escrita **antes** de medir: silenciar una consulta que la tienda **sí** puede atender invalida la configuración entera, por muchas imposibles que capture. La primera configuración probada **la incumplió** —silenciaba 15 de 48— y lo que fallaba no era entender la intención, sino no saber que las piezas de esta casa se llaman por su motivo: *«el bicho con púas que se pisa en las rocas»* es el erizo de mar, y hay diez piezas con ese motivo en el catálogo. La configuración que se sirve **no silencia ninguna** de las 48, y si el clasificador no está disponible el sistema se comporta exactamente como antes en lugar de rechazarlo todo. **Y desde C34 todo eso llega al mostrador con las cifras de la tienda.** Hasta aquí el argumentario existía pero no tenía quien lo pidiera: el backend .NET no llamaba aún a esa parte del servicio. Ahora sí, y lo hace poniendo la verdad delante —comprueba que la pieza esté en ese punto de venta **antes** de gastar una llamada de pago, y rellena el precio y las unidades con lo que dice el inventario de esa tienda, nunca el modelo—. Si algún hueco se queda sin rellenar, **retira el argumentario y sirve el resto** en vez de enseñar la plantilla a medio escribir; y si la pieza está agotada, en lugar del argumento de venta aparecen los sustitutos que esa tienda **sí puede vender hoy**. Con la IA caída la pantalla sale igual, con la pieza y su familia leídas del catálogo: un fallo del servicio nunca deja al joyero delante de un card vacío. **Y desde C36 todo esto es una pantalla que alguien usa.** Hasta aquí el argumentario, las citas y los sustitutos existían en el servidor y sólo se demostraban con herramientas de desarrollo: **C36 es la única pantalla del proyecto que pone esta capa delante de una persona**. Quien atiende abre la ficha de la pieza que el cliente tiene en la mano —desde la búsqueda con ayuda, desde la venta manual o justo después de escanear el código— y ve el argumentario con el precio y las unidades de su tienda, las fuentes desplegables de donde sale cada afirmación —distinguiendo un dato general de un **compromiso de la casa**, que conviene confirmar antes de trasladarlo a un cliente— y, si la pieza tiene varias tallas, **una fila y un botón por talla sin ninguna preseleccionada**, de modo que vender la talla equivocada exige elegirla a mano. Puede escribir la pregunta que le acaban de hacer —«¿se puede mojar?», «¿y si tiene la piel sensible?»— y recibe la respuesta citada; y si la pieza está agotada, alternativas que esa tienda **sí puede vender hoy**. Cuando el sistema no puede sostener un argumentario **lo dice y explica qué hacer**, en lugar de callar o de inventar: la pantalla distingue «el asistente no está disponible, esto viene del catálogo» de «el argumentario no se ha generado», porque no significan lo mismo para quien está vendiendo. **Y desde C40 se puede preguntar sin tener ninguna pieza delante.** Era el último modo del asistente que no llegaba a nadie: el servicio sabía responder a «algo para regalar a mi madre, que no sea muy llamativo» desde C30b, pero no había pantalla que lo pidiera y una guarda del backend lo rechazaba al 100 %. Ahora el mismo panel de búsqueda ofrece **dos vías y un selector**: la búsqueda rápida de siempre, y una respuesta asistida que agrupa las piezas por familia y las explica en prosa. **El coste se dice antes de pulsar** —treinta búsquedas por minuto contra diez, respuesta inmediata contra unos segundos— y la elección **no se recuerda entre visitas**, porque recordar la vía cara es como se gasta sin que nadie lo decida. El panel **dice qué vías están encendidas antes de la primera búsqueda**, en vez de dejar que se descubra usándolas: ésa era exactamente la avería que abrió este trabajo, una pantalla ofreciendo una capacidad apagada. Y responde de **dieciséis maneras distinguibles**, que es lo que separa una pantalla honesta de una que se encoge de hombros: las dos negativas se dicen con palabras distintas, una consulta ambigua recibe la repregunta literal del servicio y el foco vuelve a la caja, «no tengo fuente que lo sostenga» se dice como una línea discreta y nunca como una alarma, y —lo que el sistema no sabía decir— **«el catálogo sí tiene algo parecido, pero tus filtros lo han dejado fuera»** se distingue de «no hay nada parecido», que llevan a acciones opuestas: quitar un filtro, o describirlo de otra manera. Se puede además buscar **en todas las tiendas a la vez**, y entonces la pantalla no inventa existencias: donde no hay tienda que nombrar dice que hay que elegir una, en lugar de un cero que significaría que la pieza se ha agotado en todas partes. Cada fila cuenta **qué otras tallas lleva su familia**, porque la lista agrupa y el dedo del cliente suele ser una talla mayor. Y el panel de diagnóstico del administrador separa lo que tardó el proveedor de lo que tardamos nosotros, con el modelo y los tokens, pero **nunca un importe**: una tarifa escrita en una pantalla está mal el día que el proveedor la mueve. Tres de las cinco mediciones publicadas **refutaron lo que se había previsto** —el enrutador no encarece la respuesta porque se paga con el trabajo que ahorra, la contradicción que se esperaba en el 11,9 % de las consultas no apareció ni una vez, y los marcadores de precio que iban a arruinar «la mayoría» de los argumentarios fueron 2 de 90—, y las tres quedan escritas con su artefacto al lado. **Y desde C41 ese inventario se mantiene al día solo.** Hasta aquí alguien tenía que acordarse de refrescar la copia del surtido que usa el buscador, y en tres ocasiones distintas nadie lo hizo: una de ellas dejó **veinte días** de desfase sin que ninguna pantalla lo dijera, y otra dejó a un entorno entero sin poder buscar mientras parecía sano desde fuera. Lo que fallaba no era la disciplina: la única rutina programada que existía estaba escrita en un manual y describía un servidor que este sistema no usa. Ahora el servicio la refresca **al arrancar y cada diez minutos**, y dos drenajes simultáneos —el automático y el que alguien lance a mano— no pueden pisarse, porque saltarse filas en silencio sería peor que el desfase que se venía a arreglar. El panel de administración informa de cuándo fue la última vez y de **qué tiendas se han quedado sin surtido sincronizado**, que es la avería que hasta ahora sólo se descubría buscando y no encontrando nada. Al medirlo contra el entorno real apareció una tienda en ese estado desde hacía semanas. **Y desde C42 quien atiende puede conversar con un agente que decide por sí mismo qué consultar.** Era el último pilar del proyecto que existía entero y no llegaba a nadie: el agente estaba entregado y medido desde hacía tiempo —seis herramientas de sólo lectura, hasta ocho consultas por respuesta, y la capacidad de **cambiar de idea a mitad de camino** y ofrecer sustitutos cuando lo que se pedía no está—, pero ninguna pantalla lo llamaba y ninguna parte del backend sabía hablarle. Ahora tiene la suya, una cuarta vía de entrada a la venta junto al escaneo, el registro manual y la búsqueda con ayuda: se le pregunta con las palabras del cliente —«busco un regalo», «el cliente quiere algo para una boda pero no muy llamativo»— y él decide si mirar el catálogo, si consultar las existencias, si listar las tallas de una familia o si buscar en el corpus del oficio, y **enseña lo que ha consultado** en una traza que se despliega. **Cada pregunta conserva su respuesta**, con las piezas rotuladas según de dónde salieron —las que encajan, y las que ofrece como alternativa—, y eso no es un detalle estético: una pantalla que refrescara un único bloque dejaría al joyero leyendo el argumento de una pregunta sobre las piezas de la siguiente, y cuando el agente cambia de idea la pieza que estaba mirando desaparecería sin que nadie le dijera por qué. Cuando el agente se detiene, la pantalla **dice en castellano por qué** y ninguno de los diez motivos se pinta como una avería: pedir una aclaración, declinar cortésmente o quedarse sin presupuesto son desenlaces normales de una conversación, y lo que ya encontró antes de parar sigue sirviendo para vender. La conversación **avisa antes de que el mensaje no quepa** y avisa antes de borrarse si se cambia de tienda a mitad. Y la comprobación manual encontró dos cosas que ningún test había visto: la pantalla afirmaba un motivo de parada cuando el servicio simplemente no había contestado —culpando a la pantalla de una caída ajena—, ya corregido; y **una limitación que se declara en vez de disimularse**: si el cliente nombra la pieza por su nombre en lugar de por su referencia, el agente no llega a comprobar si la tienda la tiene, porque la herramienta con la que busca no le devuelve el nombre del producto. Está medido con un experimento, escrito, y en la cola de trabajo pendiente.

### 1.3. Diseño y experiencia de usuario

El usuario aterriza en la pantalla de login; tras autenticarse, accede al dashboard (estadísticas globales para administradores o por punto de venta para operadores). Desde la navegación puede: registrar ventas de forma manual (`/sales/new`), escaneando el código de barras o QR (`/sales/new/scan`), buscando con ayuda en lenguaje natural (`/sales/new/assisted`) o con reconocimiento por imagen (`/sales/new/image`); abrir desde cualquiera de esas vías la **ficha de venta** de una pieza (`/sales/new/assist/:productId`), que reúne su argumentario con las fuentes citadas, la caja para preguntar por ella y la elección de talla antes de pasar por caja; consultar historial de ventas con filtros y paginación, gestionar productos e inventario (catálogo, importación Excel, stock por POS, ajustes), configurar puntos de venta y métodos de pago, y (solo administradores) acceder al dashboard de modelo de IA y al listado de stock crítico con paginación. La interfaz está optimizada para uso en móvil en el punto de venta (cámara, gestos) y es responsive para administradores. La moneda es euro (EUR) con formato español.

*Se añadirá un videotutorial en esta sección.*

### 1.4. Instrucciones de instalación

**Requisitos previos**

- Backend: .NET 10 SDK, PostgreSQL 14+ (o Docker para desarrollo).
- Frontend: Node.js 20+ y npm, navegador moderno (Chrome 90+, Edge 90+, Safari 14+).

**Pasos**

1. **Backend**
   ```bash
   cd backend/src/JoiabagurPV.API
   dotnet restore
   cp Properties/launchSettings.Example.json Properties/launchSettings.json
   dotnet run
   ```
   La API queda disponible en `http://localhost:5056`. **El copiado del perfil de arranque no es opcional:** `launchSettings.json` está ignorado por git y, sin él, `ASPNETCORE_ENVIRONMENT` queda vacío, .NET asume `Production` y la cookie de sesión sale con `SameSite=None` sin `Secure` — combinación que el navegador descarta, dejando el login en un `200` engañoso y todo lo autenticado en `401`. El detalle está en [backend/README.md](backend/README.md#4-create-your-launch-profile).

   Los ficheros `appsettings*.json` ya vienen versionados con valores de desarrollo que funcionan tal cual; para ajustar algo en tu máquina, crea `appsettings.Local.json` (ignorado por git) o usa user-secrets, en lugar de editar los ficheros versionados. Las migraciones EF Core se aplican solas en cada arranque, junto con la siembra del usuario administrador; para aplicarlas a mano, `dotnet ef database update --project ../JoiabagurPV.Infrastructure`.

2. **Frontend**
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   npm run dev
   ```
   La UI queda disponible en `http://localhost:3000`. El fichero `.env.development` ya apunta a `http://localhost:5056/api`, el mismo puerto que fija el perfil de arranque del backend; solo hay que tocar `VITE_API_BASE_URL` si cambias uno de los dos.

3. **Usuario por defecto (desarrollo)**  
   Usuario: `admin`. Contraseña: `Admin123!`. Cambiar la contraseña tras el primer acceso.

4. **Tests**
   - Backend: `cd backend/src/JoiabagurPV.Tests` y `dotnet test`.
   - Frontend: `cd frontend` y `npm run test`.

Para despliegue en AWS (EC2, nginx, Docker API+SPA, RDS, S3, ECR, OIDC) y CI/CD, ver [Documentos/Guias/deploy-aws-production.md](Documentos/Guias/deploy-aws-production.md). Migración desde App Runner/CloudFront: [Documentos/Guias/deploy-aws-ec2-migration.md](Documentos/Guias/deploy-aws-ec2-migration.md).

---

## 2. Arquitectura del sistema

### 2.1. Diagrama de arquitectura

La aplicación sigue una arquitectura monolítica simple con backend y frontend separados, desplegados en contenedores y servicios cloud en régimen free-tier. Se eligió este enfoque para reducir complejidad operativa, mantener un único despliegue y optimizar costes; el sacrificio es menor escalado independiente por componente.

```mermaid
flowchart TB
    subgraph Cliente["CLIENTE"]
        Browser["Navegador Web"]
        SPA["React SPA"]
        ML["Modelo ML TensorFlow.js"]
        Browser --> SPA
        SPA --> ML
    end
    Nginx["nginx (TLS) + EC2"]
    Gateway["Reverse proxy → contenedor Docker"]
    subgraph Backend["BACKEND API .NET 10"]
        API["ASP.NET Core Web API"]
        EF["Entity Framework Core"]
        API --> EF
    end
    DB["PostgreSQL"]
    Storage["Object Storage S3/Blob"]
    AI["jbg-ai (Python/FastAPI)<br/>red interna, no expuesto en nginx"]
    Cliente -->|HTTPS| Nginx
    Nginx --> Gateway
    Gateway -->|HTTP interno| Backend
    Backend --> DB
    Backend --> Storage
    Backend -->|JWT interno HS256| AI
```

### 2.2. Descripción de componentes principales

- **Backend:** ASP.NET Core Web API (.NET 10), C#, Entity Framework Core, PostgreSQL 15+, JWT para autenticación, Serilog para logging, patrón Repository y capa de servicios. Documentación de API con Scalar.
- **Frontend:** React 19, TypeScript, Vite, Metronic React (Layout 8), Radix UI, Tailwind CSS, React Hook Form + Zod, TensorFlow.js para inferencia y entrenamiento en el navegador.
- **Base de datos:** PostgreSQL con índices para ventas, inventario y productos; connection pooling y paginación (máx. 50 ítems por página).
- **Almacenamiento:** Servicio de ficheros abstracto (local en desarrollo, S3/Blob en producción) para fotos de productos, ventas y devoluciones.
- **Servicio de IA (`jbg-ai`):** Microservicio Python 3.11 con FastAPI en contenedor propio, para recuperación vectorial y generación con LLM. El navegador nunca lo llama: solo el backend .NET, con un JWT interno HS256 sobre la red Docker. .NET conserva la autoridad sobre precio, stock y permisos.

### 2.3. Descripción de alto nivel del proyecto y estructura de ficheros

- `backend/`: Solución .NET en capas (Domain, Infrastructure, Application, API). Controllers en `JoiabagurPV.API/Controllers`, servicios y DTOs en `JoiabagurPV.Application`, entidades e interfaces de dominio en `JoiabagurPV.Domain`, repositorios y DbContext en `JoiabagurPV.Infrastructure`. Tests en `JoiabagurPV.Tests`.
- `frontend/`: SPA React; `src/pages` por módulo (dashboard, sales, products, inventory, etc.), `src/services` para llamadas API, `src/components` para UI y layouts.
- `Documentos/`: Arquitectura, modelo de datos, épicas, historias de usuario, guías de deploy y testing.
- `openspec/`: Especificaciones (specs) y cambios (changes) según metodología OpenSpec (spec-driven development).
- `ai-service/`: Microservicio Python `jbg-ai` (FastAPI) del Proyecto Final de IA. Contenedor independiente, alcanzable solo desde el backend .NET.
- `scripts/catalog/`: pipeline offline de C06a (lectura xlsx, JSONL, ingesta local de `Description`). No forma parte de `jbg-ai`.
- `ai-service/src/jbg_ai/data/`: CLI C06b (`generate|ingest` de catálogo) y C10 (`world simulate|ingest`). `api.main` no lo importa.
- `ai-service/src/jbg_ai/enrichment/`: extractor C09 de `POST /v1/enrich/products` (`STUB_MODE=false`). Prompt vigente `ai-service/prompts/enrichment/v2.md` **desde FIX1**, que amplió `piece_type` de ocho a doce términos; `v1.md` se conserva intacto porque 1.178 perfiles declaran venir de él y esa declaración tiene que seguir siendo verificable.
- `ai-service/src/jbg_ai/families/`: agrupador C18a de `POST /v1/families/suggest`. Determinista y sin red: agrupa por raíz de nombre y el embedding **veta en relativo**, sin llamar a ningún modelo.
- `ai-service/src/jbg_ai/retrieval/`: retriever de `POST /v1/retrieval/products` — vectorial en C14 (coseno `<=>`, umbral de distancia, sobre-recuperación), expansión de consulta en C20 (diccionario de sinónimos en dos capas y CLI de medición), **híbrido desde C21** y **recompuesto en C25** (la fusión se hace en **dos etapas** con pesos por rama —las dos listas léxicas se fusionan entre sí y el resultado con la vectorial, de modo que el voto de cada rama sea el declarado y no dependa de cuántas de sus listas dispararon—, más ponderación del peso léxico por cobertura, score de disponibilidad en el último bloque de la clave y `abstention.py`, la regla relativa por consulta que decide **si** contestar), y **acotado al punto de venta desde C22** (`projection.py`: el alcance sale del claim del token y se aplica en SQL, el stock agotado degrada sin eliminar, y `projection_age_seconds` gobierna el 503 por proyección vacía y la degradación por desfase). No lee nunca el esquema `public`. **Y sirve una segunda ruta desde C26**: `POST /v1/retrieval/substitutes` (`substitutes.py`), que responde a «esta pieza no se la puedo vender, ¿qué le enseño?». Al ser producto → producto, el embedding del origen **ya está almacenado**, así que no llama al proveedor de embeddings ni fusiona nada: una sola sentencia, el tipo de pieza como único filtro duro —un anillo no sustituye a un colgante— y una cola continua que degrada la talla distinta y lo agotado **sin eliminar a nadie**, porque la proyección de stock puede desfasarse minutos. Cada candidato explica por qué está ahí, y un producto origen inexistente, inactivo o sin embedding es un error explícito que nombra la causa en vez de un 200 con lista vacía.
- `ai-service/src/jbg_ai/knowledge/`: **segundo índice** del sistema, de C23. `ai.product_document` responde a «enséñame anillos de plata» y no puede responder a «¿este anillo se puede mojar?»: eso vive en `data/knowledge/`, 32 documentos Markdown troceados por sección, 161 fragmentos, cada uno citable por `<documento>#<sección>` — una cita que **resuelve, localiza y abre** el fichero y el encabezado en git. Cada sección declara su `claim_scope`, que separa un hecho del mundo de un compromiso de la casa, y la búsqueda es **una llamada de biblioteca y no una ruta HTTP**. El umbral de distancia `0,51` se fijó sobre un hueco limpio de 8 milésimas entre las 32 preguntas que el corpus responde y las 5 de fuera.
- `ai-service/src/jbg_ai/assist/`: la venta asistida de `POST /v1/assist/sale`, en tres capas que se entregaron por separado y siguen siendo separables. **C30a** puso la estructura —tres modos resueltos por los anclajes de la petición, agrupación por familia, avisos derivados por regla y citas direccionadas por clave primaria, **sin una sola llamada a un modelo**—. **C30b** puso la prosa y sus tres comprobaciones deterministas (`prompt.py`, `llm.py`, `verification.py`, `pitch.py`), que revisan el argumentario **sin ningún segundo modelo haciendo de juez**. **Y C31 puso la puerta de entrada** (`routing.py`, `router_llm.py`): clasifica la consulta libre **antes de recuperar nada**, distingue «no es de joyería» de «es joyería y este catálogo no la tiene» con dos códigos distintos, repregunta desde un catálogo cerrado de plantillas elegido **en código**, y declara que el corpus no cubre una pregunta anclada leyendo un resultado ya calculado, sin llamada extra. Sin credencial de clasificador el servicio **se comporta exactamente como antes** — el *fail-open* es la ablación y el rollback a la vez. **Y C32a añade `tools.py`**: el catálogo de seis herramientas de solo lectura que el agente de venta podrá invocar —buscar en el catálogo, proponer sustitutos, listar la familia de una pieza, consultar el corpus de conocimiento, preguntar por la disponibilidad y repreguntar al cliente— con el conjunto de nombres **congelado**, sus esquemas de *function calling*, validación de argumentos **antes de tocar ningún puerto** y los fallos devueltos como datos con causa de vocabulario cerrado, nunca como excepción. Que ninguna de las seis escriba **se comprueba por introspección del grafo de objetos** en la construcción del registro —los nombres, los métodos de cada puerto capturado y los verbos HTTP de cualquier cliente—, no con una bandera que declare el propio autor de la herramienta. El registro no declara ruta propia: **lo consume C32b** (`agent.py`, `agent_llm.py`, `transcript.py`), el bucle de *function calling* que sirve `POST /v1/assist/agent` en ruta aparte —seis presupuestos, `partial: true` con un motivo de parada de vocabulario cerrado y la transcripción multi-turno viajando en la petición, porque el servicio no guarda nada entre llamadas—, mientras `POST /v1/assist/sale` no cambia campo a campo. **Y C40 cierra el modo que las cinco capas anteriores dejaron sin llegar a nadie**: la consulta libre. `prompts/assist/v5.md` prohíbe hablar de precio y de disponibilidad en sus tres tareas de modo libre —donde hay hasta quince piezas agrupadas y lo que se pide es comparar, así que un marcador no tiene pieza contra la que resolverse— y añade una **cuarta tarea, «sin cobertura»**, con la misma regla que la anclada: no contestar de memoria, no esquivar con una generalidad, no citar nada. Un marcador que aun así aparezca es **causa dura** (`placeholder_in_free_query`) y retira el argumentario entero, comprobada **sólo** cuando no hay pieza anclada. La medición refutó la predicción que ordenaba el change: se esperaba que «la mayoría» de los argumentarios se retiraran, y salieron **2 de 90 y 1 de 90** con `v3` y **0 y 0** con `v5` — lo que bloqueaba el modo libre al 100 % era el guardia de la pasarela .NET, no la frecuencia de marcadores. C40 añade también la **sonda vectorial sin filtro** de `retrieval/orchestrator.py`, secuencial y sólo cuando la petición trae filtros, para que la abstención se decida sobre un perfil de distancias que ningún filtro ha estrechado: de ahí sale `filters_too_narrow`, que distingue «el catálogo no tiene nada parecido» de «lo tiene y tus filtros lo excluyeron».
- `ai-service/src/jbg_ai/indexing/`: biblioteca C11 (`source-text/v1` + embeddings) y **dos drenajes independientes** — el de catálogo de C13 (`POST /v1/index/sync`, CLI `python -m jbg_ai.indexing sync`) y el de disponibilidad por punto de venta de C22 (`pos_projection.py` + `pos_orchestrator.py`, CLI `sync-pos`, **sin ruta HTTP y sin planificador**), cada uno con su propia fila en `ai.sync_checkpoint`. `api.main` no lo importa; el router de índice sí.
- `data/catalog/real/generated/`: corpus JSONL versionado (`data_origin: real`). El xlsx crudo permanece gitignored.
- `data/catalog/synthetic/generated/`: corpus JSONL sintético (`data_origin: synthetic`; 764 líneas; híbrido 1.200 con el real).
- `data/world/`: receta YAML de 12 POS (`pos-profiles.yaml`, en git). JSONL de ventas y `pg_dump` gitignored.
- `terraform/`: Pila de infraestructura AWS de producción (EC2, RDS, S3, ECR, SSM, OIDC).

### 2.4. Infraestructura y despliegue

En producción (AWS): EC2 con nginx (TLS) y un contenedor Docker con API .NET + SPA React; RDS PostgreSQL; S3 (`prod-jpv-files`) para ficheros; ECR; parámetros en SSM; despliegue con GitHub Actions y OIDC. Backups RDS según Terraform (p. ej. 7 días). Detalle en [Documentos/Guias/deploy-aws-production.md](Documentos/Guias/deploy-aws-production.md).

**Entorno de demostración del Proyecto Final de IA (C17):** despliegue independiente en una **cuenta AWS distinta**, con su propio estado de Terraform ([terraform/demo/](terraform/demo/)) y su propio flujo de despliegue. Cuatro contenedores —proxy Caddy con TLS automático, API con la SPA, servicio de IA y PostgreSQL con pgvector— de los que **sólo el proxy publica puertos**: el servicio que custodia la clave del proveedor no es alcanzable desde Internet, y esa frontera se cumple en tres capas independientes (grupo de seguridad, puertos publicados y ausencia de ruta). Los secretos se leen del almacén de parámetros al entorno del proceso y **nunca a disco**. Runbook en [deploy/demo/README.md](deploy/demo/README.md).

### 2.5. Seguridad

- Autenticación JWT (stateless) y refresh tokens para renovación de sesión.
- Contraseñas con BCrypt y salt.
- Control de acceso por roles (Administrator / Operator) y por punto de venta (operadores solo acceden a sus POS asignados).
- CORS configurado por origen permitido; en producción solo dominios de la aplicación.
- HTTPS en producción; secretos de aplicación en AWS SSM Parameter Store en la pila actual.
- Uso de EF Core para evitar inyección SQL; sanitización de entradas frente a XSS.

### 2.6. Tests

- **Backend:** xUnit, Moq, FluentAssertions; tests unitarios de servicios y validadores; tests de integración con Testcontainers (PostgreSQL). Nomenclatura tipo `Method_Scenario_ExpectedResult`. Los controladores críticos (por ejemplo ventas) tienen tests de integración que cubren creación, validación de stock, método de pago y permisos.
- **Frontend:** Vitest, React Testing Library, MSW para simular API; pruebas de componentes y de flujos; E2E con Playwright (en progreso). Documentación en [Documentos/testing-backend.md](Documentos/testing-backend.md) y [Documentos/testing-frontend.md](Documentos/testing-frontend.md).
- **Servicio de IA (`jbg-ai`):** pytest con el `TestClient` de FastAPI (`uv run pytest`); cubre autenticación de servicio, conformidad de los contratos, respuestas stub, extracción de catálogo con LLM falso (`tests/enrichment/`), retriever vectorial con fakes (`tests/retrieval/`), búsqueda y direccionamiento sobre el corpus de conocimiento (`tests/knowledge/`), la venta asistida completa —estructura, citas, redacción del argumentario con sus tres comprobaciones deterministas, desde C31 el enrutador de intención con sus dos rechazos, la repregunta determinista y el *fail-open*, y desde C32a el registro de herramientas: el conjunto congelado afirmado **por nombre**, el invariante de solo-lectura ejercido contra un puerto que sí escribe registrado a propósito, y una prueba de anti-vacuidad que fija qué puerto se ve capturar a cada herramienta, porque una comprobación que no encontrara nada que inspeccionar pasaría sobre una lista vacía, y desde C32b el bucle agéntico: una prueba por motivo de parada y por presupuesto, el reloj acotando la petición entera y la inyección en un turno anterior comprobada sobre los mensajes que recibe el proveedor— (`tests/assist/`), el conjunto de enrutado de 119 casos y su criterio de veto, y los instrumentos y el arnés de la pasada del agente (`tests/evals/`) y estabilidad del snapshot OpenAPI. Los tests no llaman a proveedores LLM, APIs de embeddings ni RDS: el cliente generativo se conduce con un doble que revienta si alguien lo llama de verdad.

---

## 3. Modelo de datos

### 3.1. Diagrama del modelo de datos

El modelo está optimizado para PostgreSQL 15+ y Entity Framework Core. A continuación se muestra el diagrama de entidades principales (relaciones resumidas).

```mermaid
erDiagram
    User ||--o{ UserPointOfSale : "asignado a"
    User ||--o{ Sale : "realiza"
    PointOfSale ||--o{ UserPointOfSale : "tiene asignados"
    PointOfSale ||--o{ Sale : "registra ventas"
    PointOfSale ||--o{ Inventory : "tiene stock"
    Product ||--o{ ProductPhoto : "tiene fotos"
    Product ||--o{ Sale : "se vende"
    Product ||--o{ Inventory : "en stock"
    Product ||--o{ InventoryMovement : "movimiento"
    Sale ||--o{ SalePhoto : "tiene foto"
    Sale ||--o{ InventoryMovement : "genera movimiento"
    Inventory ||--o{ InventoryMovement : "tiene movimientos"
    PaymentMethod ||--o{ Sale : "usado en"
    Return ||--o{ InventoryMovement : "genera movimiento"
    User { uuid Id PK string Username UK string PasswordHash enum Role }
    PointOfSale { uuid Id PK string Name string Code UK bool AllowManualPriceEdit }
    Product { uuid Id PK string SKU UK decimal Price }
    Sale { uuid Id PK uuid ProductId FK uuid PointOfSaleId FK uuid PaymentMethodId FK decimal Price int Quantity }
    Inventory { uuid Id PK uuid ProductId FK uuid PointOfSaleId FK int Quantity bool IsActive }
    InventoryMovement { uuid Id PK uuid InventoryId FK enum MovementType int QuantityChange }
```

Descripción completa y resto de entidades (Return, ReturnSale, Collection, etc.) en [Documentos/modelo-de-datos.md](Documentos/modelo-de-datos.md).

### 3.2. Descripción de entidades principales

- **User:** Id (UUID), Username (único), Email (opcional), PasswordHash (BCrypt), Role (Admin/Operator), IsActive. Relación con UserPointOfSale (asignación a POS) y con Sale.
- **PointOfSale:** Id, Name, Code (único), Address/Phone/Email opcionales, IsActive, AllowManualPriceEdit. Relación con Inventory, Sale, UserPointOfSale, PointOfSalePaymentMethod.
- **Product:** Id, SKU (único, indexado), Name, Description, Price, CollectionId (opcional), IsActive. Relación con ProductPhoto, Sale, Inventory, InventoryMovement.
- **Sale:** Id, ProductId, PointOfSaleId, UserId (operador), PaymentMethodId, Price (snapshot), Quantity, Notes, PriceWasOverridden, OriginalProductPrice, BulkOperationId (opcional), SearchEventId (opcional, búsqueda asistida de la que procede la venta), SaleDate. Índices por POS, producto, usuario, fecha. Relación con SalePhoto e InventoryMovement.
- **Inventory:** Id, ProductId, PointOfSaleId, Quantity, IsActive (asignado/desasignado). Unique(ProductId, PointOfSaleId). La presencia de registro activo determina visibilidad del producto para operadores en ese POS.
- **InventoryMovement:** Id, InventoryId, SaleId/ReturnId (opcionales), UserId, MovementType (Sale, Return, Adjustment, Import), QuantityChange, QuantityBefore, QuantityAfter, Reason (ajustes), MovementDate. Trazabilidad completa de movimientos.

Otras entidades (ProductPhoto, PaymentMethod, PointOfSalePaymentMethod, Return, ReturnSale, Collection, ProductSearchEvent, ProductAiProfile, ProductFamily, ProductFamilyMember, FamilyReviewVerdict, etc.) se describen con detalle en [Documentos/modelo-de-datos.md](Documentos/modelo-de-datos.md).

---

## 4. Especificación de la API

A continuación se describen seis endpoints principales en formato OpenAPI (resumen). La API base es `/api` y requiere cabecera `Authorization: Bearer <token>` para endpoints protegidos, salvo `GET /api/ai/index-feed/*`, que autentica con `X-Index-Feed-Key`.

### POST /api/sales — Crear venta

Crea una venta validando stock, método de pago asignado al POS y que el usuario esté asignado al punto de venta (o sea administrador). Actualiza inventario en la misma transacción.

`searchEventId` es opcional y atribuye la venta a la búsqueda asistida de la que procede. Se comprueba que el evento exista **y pertenezca a quien vende**; un identificador desconocido o ajeno deja la atribución nula, sin error de validación y sin alterar nada más de la venta. `POST /api/sales/bulk` lo acepta **por línea**, porque cada línea de un carrito puede venir de una búsqueda distinta o de ninguna.

**Request (application/json)**

| Campo            | Tipo    | Requerido | Descripción                                      |
|------------------|---------|-----------|--------------------------------------------------|
| productId        | uuid    | Sí        | ID del producto                                  |
| pointOfSaleId    | uuid    | Sí        | ID del punto de venta                            |
| paymentMethodId  | uuid    | Sí        | ID del método de pago                            |
| quantity         | integer | Sí        | Cantidad (mayor que 0)                            |
| price            | number  | No        | Override de precio (solo si POS permite edición) |
| notes            | string  | No        | Notas (máx. 500 caracteres)                      |
| photoBase64      | string  | No        | Foto en Base64 (opcional)                         |
| photoFileName    | string  | No        | Nombre original del archivo de la foto           |
| searchEventId    | uuid    | No        | Búsqueda asistida que originó la venta           |

**Responses**

- **201 Created:** Cuerpo con `sale` (objeto con id, productId, pointOfSaleId, etc.), `warning` (opcional), `isLowStock` (boolean), `remainingStock` (número).
- **400 Bad Request:** Validación fallida o stock insuficiente / método de pago no disponible / producto no asignado al POS. Cuerpo con `message` o `errors`.
- **401 Unauthorized:** No autenticado.
- **403 Forbidden:** Operador no asignado al punto de venta.

**Ejemplo de petición**

```json
POST /api/sales
{
  "productId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "pointOfSaleId": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
  "paymentMethodId": "3fa85f64-5717-4562-b3fc-2c963f66afa8",
  "quantity": 1,
  "notes": "Venta con foto"
}
```

---

### GET /api/sales — Historial de ventas

Devuelve ventas paginadas. Los administradores ven todas; los operadores solo las de sus puntos de venta asignados.

**Query parameters**

| Parámetro      | Tipo   | Descripción                    |
|----------------|--------|--------------------------------|
| startDate      | date   | Fecha inicio (inclusive)       |
| endDate        | date   | Fecha fin (inclusive)          |
| pointOfSaleId  | uuid   | Filtrar por POS                |
| productId      | uuid   | Filtrar por producto           |
| userId         | uuid   | Filtrar por usuario            |
| paymentMethodId| uuid   | Filtrar por método de pago    |
| page           | int    | Página (por defecto 1)         |
| pageSize       | int    | Tamaño de página (p. ej. 20)  |

**Response 200 OK**

- `sales`: array de objetos venta (id, productId, pointOfSaleId, paymentMethodId, price, quantity, saleDate, hasPhoto, etc.).
- `totalCount`, `page`, `pageSize`, `totalPages` (según implementación en `SalesHistoryResponse`).

**401 Unauthorized** si no hay token válido.

---

### GET /api/dashboard/low-stock — Stock bajo (administradores)

Devuelve productos con stock bajo (por defecto cantidad ≤ 2) paginados. Solo rol Administrator.

**Query parameters**

| Parámetro | Tipo | Descripción                          |
|-----------|------|--------------------------------------|
| page      | int  | Página (por defecto 1)               |
| pageSize  | int  | Tamaño de página (entre 1 y 50)      |

**Response 200 OK**

- `items`: array de `{ productName, sku, pointOfSaleName, stock }`.
- `totalCount`, `page`, `pageSize`, `totalPages`.

**401 Unauthorized** / **403 Forbidden** si no autenticado o no administrador.

---

### POST /api/ai/search — Búsqueda asistida

Busca en el catálogo con lenguaje natural. El servicio de IA propone candidatos y **el backend pone la verdad**: precio, stock y qué tiene esa tienda salen de PostgreSQL, nunca de la respuesta de la IA.

**Request body**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| query | string | Consulta en lenguaje natural. Obligatoria, máximo 500 caracteres |
| pointOfSaleId | uuid | **Obligatorio para todos los roles.** El operador debe estar asignado; el administrador puede elegir cualquiera activo |
| pageSize | int | Resultados a mostrar (1–50, por defecto 10) |
| searchSessionId | uuid | Agrupa las reformulaciones de un mismo episodio. El servidor genera uno si falta |
| materials, category | — | Filtros rápidos opcionales |

**Response 200 OK**

- `results`: array de `{ productId, sku, name, price, quantityAtPointOfSale, hasStock, primaryPhotoUrl, collectionName, score, matchReasons, familyId, variantLabel }`, **en el orden de relevancia recibido**.
- `searchEventId`: identificador del evento de telemetría, para reportar después la selección.
- `aiAvailable`, `lowConfidence`: distinguen los **tres** «sin resultados» — la IA se abstuvo, la tienda no tiene ninguno de los candidatos, o la IA no atendió la búsqueda.
- `candidatesReturned`, `survivedHydration`: embudo de la recuperación.

**400 Bad Request** sin punto de venta, con consulta vacía o si el punto de venta no está activo. **403 Forbidden** si el operador no está asignado a él. **429 Too Many Requests** al superar el límite por usuario.

La búsqueda **nunca falla por culpa de la IA**: cualquier fallo del servicio degrada a un buscador léxico acotado al mismo punto de venta y se reporta con `aiAvailable: false`.

### POST /api/ai/search/assisted — Respuesta asistida a una consulta libre

La segunda ruta del mismo panel, y la que pone el RAG delante del operario **sin una pieza delante**. Acepta el mismo cuerpo que la anterior más `question`, y devuelve las piezas **agrupadas por familia** con un argumentario redactado sobre la ruta que el clasificador de intención decidió. Es un endpoint aparte y no un campo `mode` de la anterior porque tiene interruptor, cupo, presupuesto y circuito **propios**: la ruta asistida cuesta una llamada de pago al proveedor y la rápida no.

**Response 200 OK** — sobre lo de `POST /api/ai/search`, añade `groups`, `pitch` y `pitchStatus`, `citations` con su `claimScope`, `warnings`, `clarificationQuestion` (verbatim, de un catálogo cerrado resuelto en código), `intent`, `abstained`, `degradedReason` y `usage` — este último **sólo para administradores**, con dos tiempos separados, modelo y tokens, y nunca un importe.

`pointOfSaleId` es aquí **opcional**: omitirlo busca en **todas las tiendas**, que operarios y administradores pueden hacer. Sin tienda no hay existencias que reportar y **cero sería falso**, así que `quantityAtPointOfSale` y `hasStock` vuelven nulos y la fila lo dice en vez de pintar un agotado. Esa búsqueda **no queda registrada**: la columna de telemetría exige punto de venta y registrarla pediría una migración, así que `searchEventId` vuelve nulo y el embudo lo declara — está anotado en `openspec/DEFERRED_TASKS.md`.

**429 Too Many Requests** con cupo propio, independiente del de la ficha: un cupo agotado **no** se reporta como servicio caído.

### POST /api/ai/search/agent — El agente de venta, en conversación

La tercera ruta de IA del panel de venta, y la que **no tenía ningún consumidor**: el agente estaba entregado y medido desde C32b, con sus seis herramientas de sólo lectura y su bucle, y ningún método del cliente de pasarela lo llamaba. A diferencia de las dos anteriores, no recibe una consulta sino **un transcript**: la conversación entera viaja en cada petición, porque el servicio no guarda estado de sesión.

**Request** — `turns` (la conversación, cada turno con `role` `operario` \| `asistente` y su `text`), `pointOfSaleId` **opcional** y `topK`. Los tres topes del transcript son del contrato y se validan antes de gastar nada: **12 turnos, 500 caracteres por turno y 4.000 en total sumando todos los turnos, incluidos los del asistente** — con el argumentario reenviado, el tope de turnos muerde a los seis intercambios.

**Response 200 OK** — sobre lo de `POST /api/ai/search/assisted`, añade `groups` con `origin` (`catalogo` \| `sustitutos`, que es lo que permite rotular de dónde salió cada pieza en vez de mezclarlas), `partial`, `stopReason` (vocabulario **cerrado de diez** motivos), `iterations`, `toolCallsUsed`, `trace` —la escalera de pasos: qué herramienta se llamó en cada vuelta y con qué resultado—, `agentPromptVersion` y `usage.providerCalls`, porque una petición del agente resuelve varias llamadas al proveedor y una cuenta única no permitiría repartir el coste.

`pointOfSaleId` es **opcional**, como en la ruta asistida: omitirlo es el ámbito «todas las tiendas», y entonces no hay existencias que reportar, así que la cantidad y el indicador de stock viajan **nulos** — se sirven precios, no disponibilidades.

**El motivo de parada no es un error.** Ocho de los diez son desenlaces normales de una conversación —una repregunta, un rechazo cortés, un presupuesto agotado con evidencia ya reunida—, y la pantalla los traduce al castellano sin pintar ninguno como fallo: lo buscado antes del corte sigue sirviendo para vender.

**429 Too Many Requests** con cupo propio de **4 por minuto**, que no es una cifra de gusto: unos 13.000 tokens por petición contra 25.000 TPM del proveedor es, en la práctica, una petición por minuto.

### GET /api/ai/search/availability — Qué vías están encendidas, antes de gastar

Devuelve los **tres** interruptores —búsqueda rápida, respuesta asistida y, desde C42, el agente— **sin llamar a la IA y sin consumir cuota**, para que el panel pueda decir qué puede ofrecer antes de la primera búsqueda. El del agente **no se deriva** del veredicto asistido: se lee de su propia opción, porque son funciones con coste distinto y derivar una de otra apagaría en pantalla algo que nadie apagó. Viaja en un campo **opcional**, así que un despliegue que no lo envíe se lee como «no se pudo confirmar» y no como «desactivado». Lleva `[DisableRateLimiting]` a propósito: heredar la política del controlador haría que comprobar si puedes buscar **te costara una búsqueda**. Hasta C40 la única forma de saber que una vía estaba apagada era usarla, y así es como el panel acabó ofreciendo una capacidad desactivada.

**Responde de un ámbito y no de una tienda.** `pointOfSaleId` es **opcional**: con una tienda informa de ella, y **omitido** informa del ámbito «todas las tiendas» devolviendo el identificador **nulo**. Un valor que no sirve —vacío, con espacios, ilegible o un GUID truncado— es **400**, porque la ausencia es que el parámetro no esté y cualquier otra cosa es un valor que tiene que ser usable. Es la misma distinción que aplica `POST /api/ai/search/assisted`, y por el mismo motivo: sin tienda el prefiltro de disponibilidad **no se aplica**, mientras un identificador en blanco sería un comodín por accidente.

---

## 5. Historias de usuario

Se documentan tres historias principales del desarrollo.

### Historia de Usuario 1 — Registrar venta con reconocimiento de imagen

**Como** operador, **quiero** registrar una venta usando reconocimiento de imagen **para** agilizar el proceso y reducir errores en la identificación del producto.

**Descripción:** Registrar una venta capturando una foto del producto, procesándola con IA para obtener sugerencias, seleccionando el producto correcto, validando stock, eligiendo método de pago y confirmando. Incluye validación de stock y método de pago.

**Criterios de aceptación (resumidos):** Venta exitosa con foto y sugerencias de IA; rechazo si stock insuficiente; rechazo si método de pago no asignado al POS; rechazo si operador no asignado al POS; si la IA no ofrece correspondencia fiable (< 60 %), ofrecer otra foto o venta manual. Detalle completo en [Documentos/Historias/HU-EP3-001.md](Documentos/Historias/HU-EP3-001.md).

---

### Historia de Usuario 2 — Crear producto manualmente

**Como** administrador, **quiero** crear productos manualmente en el sistema **para** agregar productos individuales al catálogo sin importar desde Excel.

**Descripción:** Crear productos con SKU, nombre, descripción, precio y colección (opcional). El producto se crea activo por defecto.

**Criterios de aceptación (resumidos):** Creación correcta con SKU único y precio > 0; error si el SKU ya existe; validación de campos obligatorios. Detalle en [Documentos/Historias/HU-EP1-002.md](Documentos/Historias/HU-EP1-002.md).

---

### Historia de Usuario 3 — Reconocimiento de productos mediante imagen

**Como** operador, **quiero** identificar productos mediante reconocimiento de imágenes con IA **para** obtener sugerencias a partir de una foto capturada.

**Descripción:** Flujo de captura de foto, preprocesado en cliente, inferencia con TensorFlow.js/ONNX.js, generación de 3 sugerencias ordenadas por confianza, visualización con fotos de referencia y selección. Si la confianza es < 60 %, ofrecer otra foto o venta manual.

**Criterios de aceptación (resumidos):** Reconocimiento exitoso con sugerencias y fotos; baja confianza con redirección a manual; visualización de sugerencias con SKU, nombre y porcentaje; captura desde cámara en móvil y procesamiento local. Detalle en [Documentos/Historias/HU-EP4-001.md](Documentos/Historias/HU-EP4-001.md).

---

## 6. Tickets de trabajo

Se documentan tres tickets principales a partir de las especificaciones OpenSpec del proyecto: uno de backend, uno de frontend y uno de bases de datos/dominio.

### Ticket 1 (Backend) — Registro de ventas con doble vía de entrada

**Objetivo:** Permitir a los operadores registrar ventas mediante dos métodos (reconocimiento por imagen con foto adjunta o selección manual de producto con foto opcional), validando stock, método de pago, autorización del operador y política de precio del punto de venta.

**Requisitos clave (spec: sales-management):**

- Crear registro Sale aplicando reglas de precio efectivo (precio oficial del producto por defecto; override solo si el POS tiene AllowManualPriceEdit).
- Crear SalePhoto con foto comprimida (JPEG 80 %, ≤ 2 MB) cuando se envía foto.
- Crear InventoryMovement tipo "Sale" y actualizar Inventory.Quantity en la misma transacción.
- Validación doble de stock (previa en formulario y justo antes del commit) para seguridad ante concurrencia.
- Rechazar con 400 si stock insuficiente, producto no asignado al POS, método de pago no disponible o operador no autorizado para el POS.
- Rechazar override de precio manual si el POS no lo permite; validar cantidad > 0.
- Devolver aviso de stock bajo (no bloqueante) cuando el stock restante quede por debajo del umbral configurado.

**Tareas (derivadas de la spec):** Implementar endpoint POST /api/sales con validadores (FluentValidation); integrar IStockValidationService e IPaymentMethodValidationService; ejecutar venta + movimiento de inventario en transacción; devolver sale, warning, isLowStock y remainingStock en la respuesta; tests de integración para escenarios de éxito, stock insuficiente, método de pago inválido y operador no asignado.

**Referencia:** [openspec/specs/sales-management/spec.md](openspec/specs/sales-management/spec.md).

---

### Ticket 2 (Frontend) — Reconocimiento de imágenes con inferencia en cliente

**Objetivo:** Ejecutar la inferencia de ML en el navegador/dispositivo con TensorFlow.js y presentar 3–5 sugerencias de productos con puntuación de confianza para que el operador seleccione el producto correcto.

**Requisitos clave (spec: image-recognition):**

- Descargar el modelo desde GET /api/image-recognition/model en el primer uso; mostrar progreso; cachear en IndexedDB.
- Comprobar versión del modelo (GET /api/image-recognition/model/metadata) y actualizar caché si hay nueva versión; en offline, usar modelo en caché sin comprobación.
- Preprocesar imagen (redimensionar 224x224, normalizar), ejecutar model.predict() en cliente y devolver 3–5 productos ordenados por confianza (umbral 40 %); inferencia < 500 ms en dispositivo móvil.
- Mostrar sugerencias con foto de referencia, SKU, nombre y porcentaje de confianza; permitir seleccionar una para continuar al flujo de venta.
- Si falla la descarga del modelo, mostrar error y redirigir a entrada manual (degradación controlada).

**Tareas (derivadas de la spec):** Componente de captura de foto (cámara en móvil); integración con TensorFlow.js (carga de modelo, preprocesado, predict); componente de lista de sugerencias con fotos y confianza; umbral 40 % y máximo 5 sugerencias; notificación cuando el modelo está desactualizado (> 7 días) y botón "Actualizar modelo"; tests de componente y flujo. Referencia: [openspec/specs/image-recognition/spec.md](openspec/specs/image-recognition/spec.md).

---

### Ticket 3 (Bases de datos / dominio) — Gestión de inventario y asignación a puntos de venta

**Objetivo:** Gestionar la asignación de productos a puntos de venta (registros Inventory), la importación de stock desde Excel, la visualización de stock por POS y los movimientos de inventario con trazabilidad, garantizando reglas de negocio sobre visibilidad y cantidad.

**Requisitos clave (spec: inventory-management):**

- Asignación: el administrador asigna productos del catálogo a un POS creando registros Inventory con Quantity = 0 e IsActive = true. La existencia de un Inventory activo determina que el producto sea visible para los operadores de ese POS. Evitar asignación duplicada; no asignar productos inactivos. Reasignar reactivando registro existente (IsActive = true) preservando cantidad.
- Desasignación: soft delete (IsActive = false) solo cuando Quantity = 0; error explícito si hay stock.
- Importación Excel: columnas SKU y Quantity; punto de venta elegido en la UI. Valores positivos suman al stock existente; valores negativos restan (el stock resultante no puede ser negativo). Crear Inventory (asignación implícita) si el producto no existe en el POS (solo para cantidades positivas). Crear InventoryMovement tipo "Import". Validar SKUs en catálogo y formato antes de importar; la importación es todo o nada. Ofrecer plantilla de descarga con ejemplos positivos y negativos.
- Visualización: administradores ven stock de cualquier POS; operadores solo de sus POS asignados. Incluir productos con cantidad 0.
- Ajustes manuales: crear InventoryMovement tipo "Adjustment" con QuantityChange, Reason y usuario; actualizar Inventory.Quantity y LastUpdatedAt. No permitir stock negativo.

**Tareas (derivadas de la spec):** Modelo de datos Inventory (ProductId, PointOfSaleId, Quantity, IsActive) e InventoryMovement (MovementType, QuantityChange, QuantityBefore, QuantityAfter, Reason, UserId, SaleId/ReturnId opcionales); repositorios y servicios de asignación/desasignación; endpoint de importación Excel con validación y plantilla; endpoints de consulta de stock por POS con control de acceso; tests unitarios e integración para asignación, desasignación con stock > 0 e importación. Referencia: [openspec/specs/inventory-management/spec.md](openspec/specs/inventory-management/spec.md).

---

## Documentación adicional

- [Épicas del MVP](Documentos/epicas.md): épicas, user stories y orden de implementación.
- [Arquitectura del sistema](Documentos/arquitectura.md): stack, diagramas, entornos y seguridad.
- [Modelo de datos](Documentos/modelo-de-datos.md): diagramas ER completos y descripción de entidades.
- [Modelo C4](Documentos/modelo-c4.md): niveles de contexto y componentes.
- [Testing Backend](Documentos/testing-backend.md) y [Testing Frontend](Documentos/testing-frontend.md).
- [Guía de deploy AWS](Documentos/Guias/deploy-aws-production.md).
- [README del backend](backend/README.md), [del frontend](frontend/README.md), [del servicio de IA `jbg-ai`](ai-service/README.md) y [de la pila Terraform](terraform/README.md).
- [Plan de changes del Proyecto Final de IA](Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) y [especificaciones funcionales v2](Documentos/Proyecto%20Final%20AIEng/joiabagur-ia-especificaciones-funcionales-v2.md).
- [Procedimiento de User Stories](Documentos/Procedimientos/Procedimiento-UserStories.md) y [Procedimiento de Tickets de Trabajo](Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md).
