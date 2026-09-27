# Arquitectura del Sistema - Monolítica Simple con Contenedores

## Visión General

Arquitectura monolítica simple con backend y frontend separados, desplegados en contenedores Docker sobre servicios gestionados de cloud en free-tier.

---

## Stack Tecnológico

### Backend
- **Framework**: .NET 10 (ASP.NET Core Web API)
- **Lenguaje**: C#
- **ORM**: Entity Framework Core
- **Base de datos**: PostgreSQL 15+
- **Autenticación**: JWT (usuarios) y API Key `X-Index-Feed-Key` (feeds de indexación C12)
- **Contenedorización**: Docker
- **Logging**: Serilog

### Frontend
- **Framework**: React/Vue/Angular (SPA)
- **Lenguaje**: TypeScript
- **Estado**: Redux/Vuex/NgRx (según framework elegido)
- **HTTP Client**: Axios/Fetch
- **UI Components**: Material-UI / Vuetify / Angular Material
- **ML Framework**: TensorFlow.js / ONNX.js (para reconocimiento de imágenes en cliente)
- **Build Tool**: Vite / Webpack

### Servicio de IA (`jbg-ai`)

Microservicio añadido en el Proyecto Final de IA (changes `init-ai-service-skeleton` / C01, `add-ai-service-contracts-and-auth` / C02 y `add-pgvector-schema-foundation` / C05). Vive en `ai-service/` y es un contenedor independiente del backend .NET.

- **Lenguaje**: Python 3.11
- **Framework**: FastAPI (fábrica `create_app`, `docs_url` deshabilitado)
- **Gestor de dependencias**: `uv` (`pyproject.toml` + `uv.lock`)
- **Configuración**: pydantic-settings con *fail-fast* de variables obligatorias
- **Servidor**: Uvicorn
- **Base de datos**: la misma PostgreSQL, en el esquema `ai` con extensión **pgvector**, ambos creados en C05. Acceso con SQLAlchemy 2 sobre psycopg 3 y **pool acotado a 5 conexiones sin desbordamiento**; migraciones con Alembic, independientes de EF Core y con su tabla de versiones dentro de `ai`. La cadena de conexión es **opcional**: el servicio arranca sin base de datos y el motor se construye en el primer uso
- **Contenedorización**: Docker (`python:3.11-slim-bookworm`)
- **Observabilidad**: logging estructurado con `trace_id` propagado por middleware
- **Autenticación entre servicios**: JWT interno HS256 con `PyJWT`. `user_id`, `role` y `trace_id` son obligatorios en **todas** las rutas `/v1` (C02). `pos_id` se exige **solo en las rutas con alcance de punto de venta** —recuperación, venta asistida e inventario— y **no** en las de catálogo, que operan sobre todo el catálogo y no pertenecen a ningún punto de venta (C08). Son dos dependencias distintas, declaradas en cada ruta, para que relajar una no relaje la otra
- **Aislamiento entre puntos de venta**: desde C22 el `pos_id` del token es el **único filtro duro** del recuperador, así que no existe ningún valor comodín. El scope de catálogo se cierra por **dos vías independientes**: el cliente .NET rechaza un scope de catálogo en recuperación antes de emitir la petición, y `jbg-ai` sigue exigiendo `pos_id` en esas rutas (C08). C34 extiende la primera vía a las dos operaciones que añade —venta asistida y sustitutos—, que además **nunca** envían `pos_id` en el cuerpo
- **Contrato**: 11 endpoints `/v1` congelados en `ai-service/openapi.json`, con test de snapshot. Fueron ocho hasta C18a, que añadió `POST /v1/families/suggest`, nueve hasta C18b, que añadió `POST /v1/families/audit`, y diez hasta C32b, que añadió `POST /v1/assist/agent` por adición pura verificada hoja a hoja — cada uno regenerando el snapshot en su propio change. La frontera se ha movido **en cada change que lo necesitó** desde C02 —`git log -- ai-service/openapi.json` los enumera, de C08 a C32b— y siempre a propósito. Cuatro de esos movimientos definieron su forma, y la tercera es **C30a**, que a diferencia de las dos anteriores **no añadió ninguna ruta** — movió cinco esquemas de assist y dejó las diez rutas intactas, porque el esquema congelado no podía servir a su consumidor (`family_id` obligatorio contra un catálogo donde el 58 % de los productos no tiene familia) y en ese momento la ruta tenía **cero consumidores**. La cuarta es **C30b**, y es el movimiento más pequeño que cabe: **una descripción**. `prompt_version` pasa a significar «la capa de generación corrió» en vez de «hay argumentario», porque un argumentario vacío por sí solo no distingue un despliegue que no genera de una generación que fue rechazada. Verificado aplanando los dos documentos a hojas y comparándolas — **1102 antes y 1102 después**, cero campos añadidos, cero retirados, ninguno con el tipo cambiado —, así que toda la verificación de atribución cuesta **cero** movimiento de forma: el tramo de apoyo que el modelo declara por cada cita no viaja al cable. Después vinieron **C31**, que sólo movió descripciones —las de `intent`, `warnings` y `clarification_question`, para nombrar los vocabularios nuevos de intención y de rechazo—, y **C32b**, que abrió la undécima ruta —`POST /v1/assist/agent`— sin tocar ninguna de las anteriores: verificado contra el contrato de C32a, **cero hojas retiradas y cero cambiadas**, y todas las añadidas dentro de la ruta nueva y sus seis modelos. Con `STUB_MODE=true` (default local) todas las rutas `/v1` sirven fixtures C02. Con `STUB_MODE=false`, enrich (C09), index (C13), `POST /v1/retrieval/products` (C14), `POST /v1/families/suggest` (C18a), `POST /v1/families/audit` (C18b), `POST /v1/evals/runs` (C24), `POST /v1/retrieval/substitutes` (C26), `POST /v1/assist/sale` (C30a, **y redactando el argumentario desde C30b**) y `POST /v1/assist/agent` (C32b) son reales. Queda **una** en 501, y no por falta de turno: `POST /v1/inventory/propose` pertenece a una rama **anulada el 2026-08-31** y declarada como limitación, no como trabajo pendiente. C30a cerró por tanto el **último 501 cerrable** del contrato. El de enriquecimiento se renegoció en C08 para que cada valor propuesto declare su **procedencia** (`rule` \| `inferred`) además de su confianza: sin ese dato la revisión híbrida por campo no es implementable

**Frontera de responsabilidad:** Python solo hace cálculo vectorial y generación con LLM; .NET conserva toda la regla de negocio y es la autoridad final sobre precio, stock y permisos. Python **nunca** lee ni escribe el esquema `public` por SQL, y el navegador nunca habla con Python: la SPA llama al backend .NET y este llama a `jbg-ai` con un JWT interno de servicio. C13 tira (`pull`) de `GET /api/ai/index-feed/catalog` con `X-Index-Feed-Key` desde `POST /v1/index/sync`; no hay push HTTP .NET → Python ni dreno del feed POS. **Desde C34, `POST /v1/assist/sale` y `POST /v1/retrieval/substitutes` tienen consumidor .NET** —las dos rutas del card de venta, `POST /api/ai/products/{id}/sales-assist` y `GET /api/ai/products/{id}/substitutes`—, y la frontera se aplica donde más se nota: .NET decide qué miembros de la familia hay en la tienda, cuántas unidades, si el stock es crítico, qué sustitutos se pueden vender hoy y **con qué precio se escribe el argumentario**, sustituyendo `{{price}}`/`{{stock}}` contra la pieza anclada. Con eso se cierra la ventana en la que mover la forma de `/v1/assist/sale` era gratis: C34 la consume sin moverla, `openapi.json` idéntico byte a byte. **Y desde C40 esa misma ruta tiene un segundo consumidor .NET, éste sin ancla de pieza**: `POST /api/ai/search/assisted` la llama en modo de consulta libre, con la consulta del operario y sus filtros, lo que retira el guardia que rechazaba ese modo en la pasarela. Con ello **el contrato congelado dejó de estar inmóvil, y se movió dos veces por adición pura**: `AssistRequest.filters` —una referencia a `RetrievalFilters`, que ya estaba publicado, no un esquema nuevo— y `RetrievalResponse.warnings`, una lista de códigos cerrados con defecto vacío, que viaja en la respuesta de **recuperación** y no sólo en la de asistencia porque la decisión que hay detrás de `filters_too_narrow` es de recuperación y toda ruta que acepte filtros de catálogo puede alcanzarla. Los dos movimientos se verificaron **hoja a hoja** contra el snapshot de la línea base, con **0 hojas retiradas y 0 cambiadas de tipo**; las dos que cambian de valor son `description` y están nombradas una a una en el guardián, para que una tercera siga fallando. La frontera no se mueve: `pos_id` sigue siendo el único filtro duro del recuperador, y el ámbito «todas las tiendas» se expresa por **ausencia** de la reclamación y nunca por un comodín — un `pos_id` presente y en blanco se rechaza, que es el agujero que ese mismo cambio abrió y cerró. **Y desde C42 la tercera ruta de assist tiene por fin consumidor .NET**: `POST /v1/assist/agent` estaba entregado y medido desde C32b y **nadie lo llamaba** —`IAiGatewayClient` tenía siete métodos y ninguno era el suyo—, así que la frontera pasa de dos caminos a tres. Lo hace con un cliente propio, `ai-agent`, cuarta familia de ruta, y con la frontera aplicada igual que en los otros dos: Python decide qué consultar y redacta, .NET **hidrata todos los grupos, sustitutos incluidos**, y sigue siendo la autoridad sobre precio, existencias y permisos. Con ello **el contrato congelado se movió una tercera vez, otra vez por adición pura**: `origin` (`catalogo` | `sustitutos`) en `AgentAssistGroup`, que es una **subclase** del grupo compartido — `AssistGroup` **no se ensancha**, por el precedente de `AgentUsage`, de modo que ninguna de las otras dos rutas ve un campo nuevo—, verificado contra el snapshot de la línea base guardado como `openapi-c42-baseline.json`. La ruta del agente, además, **pasa a aceptar un token sin `pos_id`**: admite el ámbito «todas las tiendas» por la misma vía que C40 abrió para la consulta libre, la ausencia de la reclamación y nunca un comodín — sin tienda no hay existencias que reportar y la cantidad viaja nula, que es exactamente lo que la comprobación manual confirmó con ámbito global (precios sí, existencias no).

### Infraestructura
- **Contenedores**: Docker
- **Orquestación**: Docker Compose (desarrollo) / Cloud Services (producción)
- **CI/CD**: GitHub Actions
- **Repositorio**: GitHub

---

## Arquitectura Detallada

### Diagrama de Componentes

```mermaid
flowchart TB
    subgraph Cliente["CLIENTE"]
        Browser["Navegador Web<br/>(Chrome/Firefox/Safari)"]
        SPA["React/Vue/Angular SPA"]
        ML["Modelo ML<br/>(TensorFlow.js/ONNX.js)"]
        PWA["Service Workers (PWA)"]
        
        Browser --> SPA
        SPA --> ML
        SPA --> PWA
    end
    
    NginxTLS["nginx en EC2<br/>- TLS (Let’s Encrypt)<br/>- Reverse proxy"]
    
    Gateway["Proxy a contenedor Docker<br/>- SPA estática + API /api<br/>- Cabeceras X-Forwarded-*"]
    
    subgraph Backend["BACKEND API (.NET 10)"]
        subgraph Container["Contenedor Docker"]
            API["ASP.NET Core Web API<br/>- Controllers<br/>- Middleware (Auth, CORS, Logging)<br/>- Services Layer<br/>- Repository Pattern"]
            EF["Entity Framework Core<br/>- DbContext<br/>- Migrations"]
        end
    end
    
    subgraph AI["SERVICIO DE IA (Python)"]
        subgraph AIContainer["Contenedor Docker jbg-ai"]
            FastAPI["FastAPI · uvicorn<br/>- /health público<br/>- /v1/* con JWT interno<br/>- Recuperación vectorial y generación"]
        end
    end
    
    DB["PostgreSQL Database<br/>- Esquema public: Products, Sales, Inventory, Users…<br/>- Esquema ai: vectores (pgvector)<br/>- Índices optimizados · Connection pooling"]
    
    Storage["Object Storage<br/>- Fotos de productos<br/>- Fotos de ventas<br/>- Archivos Excel importados"]
    
    LLM["Proveedor LLM + embeddings"]
    
    Cliente -->|HTTPS| NginxTLS
    NginxTLS --> Gateway
    Gateway -->|HTTP local| Backend
    Backend -->|PostgreSQL Protocol| DB
    Backend -->|S3 API / Blob Storage API| Storage
    Backend -->|JWT interno HS256 · red Docker interna| AI
    AI -->|solo esquema ai| DB
    AI --> LLM
    AI -.->|feed paginado since-cursor| Backend
```

> El navegador **nunca** habla con `jbg-ai`: el puerto de Python no se publica en nginx. Toda llamada pasa por el backend .NET, que además actúa de *hidratador* — resuelve precio, stock y permisos reales y descarta los candidatos que ya no cumplan las reglas.

---

## Entorno de Desarrollo

### Arquitectura Local

```mermaid
flowchart TB
    subgraph Dev["DESARROLLADOR LOCAL"]
        Frontend["Frontend (React/Vue/Angular)<br/>- npm/yarn dev server (localhost:3000)<br/>- Hot Module Replacement<br/>- Source maps"]
        
        Backend["Backend API (.NET 10)<br/>- dotnet run (localhost:5000)<br/>- Desarrollo con hot reload<br/>- Logging detallado en consola<br/>- CORS habilitado para localhost:3000"]
        
        Postgres["PostgreSQL con pgvector (Docker)<br/>- Imagen: pgvector/pgvector:pg15<br/>- Puerto: 5433 → 5432<br/>- Volumen persistente local"]
        
        JbgAi["jbg-ai (Docker)<br/>- FastAPI + uvicorn<br/>- Puerto: 8001 → 8000<br/>- STUB_MODE en local"]
        
        LocalStorage["Storage Local<br/>- Carpeta ./uploads/<br/>- Fotos de productos y ventas"]
        
        Frontend -->|"HTTP (sin HTTPS)"| Backend
        Backend -->|PostgreSQL| Postgres
        Backend -->|Local File System| LocalStorage
        Backend -->|"JWT interno (red jpv-network)"| JbgAi
        JbgAi -->|"esquema ai (desde C05)"| Postgres
    end
```

### Configuración de Desarrollo

#### Docker Compose (`backend/docker-compose.yml`)

El fichero real levanta la base de datos, pgAdmin y el servicio de IA. El backend .NET y el frontend se ejecutan fuera del Compose (`dotnet run` y `npm run dev`).

| Servicio | Imagen / origen | Puerto local | Notas |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg15` | `5433` → 5432 | Imagen con **pgvector**. El esquema `ai`, la extensión y el rol dedicado los crea `ai-service/migrations/bootstrap.sql`, **una vez y con privilegios de administrador**; levantar Compose no los crea |
| `pgadmin` | `dpage/pgadmin4` | `8080` → 80 | Administración de la BD |
| `jbg-ai` | build de `../ai-service` | `8001` → 8000 | Variables: `APP_ENV`, `SERVICE_VERSION`, `LOG_LEVEL`, `JWT_SECRET` (placeholder local; en producción desde SSM en C17), `STUB_MODE`, `DATABASE_URL` (apunta a `postgres:5432` por nombre de red, no al puerto publicado) y `JPV_INDEX_FEED_*` / tope 180 s (C13; URL `http://host.docker.internal:5056`, key distinta de `JWT_SECRET`). Sin `depends_on`: el motor es perezoso y el contenedor arranca aunque la base no esté aprovisionada |

Todos comparten la red `jpv-network`, que es la que permitirá a `jbg-ai` alcanzar Postgres sin exponer puertos adicionales.

**Configuración que el backend .NET necesita para hablar con `jbg-ai` (C03).** Como el backend se ejecuta fuera del Compose, no ve los nombres de contenedor: alcanza el servicio por el puerto publicado. La sección `AiGateway` de `appsettings.json` lo refleja y se valida **en el arranque**, de modo que la API no levanta si falta algo:

| Clave | Desarrollo | Producción |
|---|---|---|
| `AiGateway:BaseUrl` | `http://localhost:8001` (puerto publicado) | `http://jbg-ai:8000`, previsto para C17 |
| `AiGateway:JwtSecret` | Placeholder local, **idéntico** al `JWT_SECRET` del contenedor | Desde SSM en C17 |
| `AiGateway:AssistTimeoutMs` | `10000`; **el arranque rechaza < 8000**, el peor caso que `jbg-ai` declara (2 × 4 s) | `10000` (C34; la demo lo fija en `compose.demo.yaml`) |
| `AiGateway:AgentTimeoutMs` | `18000`; **el arranque rechaza < 15000**, que es el techo de reloj del propio servicio (`AGENT_DEADLINE_SECONDS`) más el margen de red. Va **por encima** de ese techo a propósito: el máximo medido en la pasada de C32b fue 11.917 ms, y apretarlo hasta ahí cortaría peticiones que Python **ya pagó enteras**. `AssistTimeoutMs` no se toca: el agente lleva opción propia | `18000` (C42) |
| `IndexFeed:ApiKey` | Placeholder local ≥ 32 caracteres, **distinto** de `Jwt:SecretKey` y de `AiGateway:JwtSecret` | SSM `/jpv/prod/IndexFeed:ApiKey` en C17 |

> El valor de producción presupone una **red Docker definida por el usuario**, que hoy no existe: el despliegue arranca los contenedores en la red *bridge* por defecto, donde Docker no resuelve nombres de contenedor. Crearla, unir ambos contenedores y dejar el puerto de `jbg-ai` sin publicar es prerrequisito de C17, junto con los parámetros `/jpv/prod/AiGateway__BaseUrl` y `/jpv/prod/AiGateway__JwtSecret`.

> **Aviso al actualizar desde una versión anterior:** el cambio de `postgres:15` a `pgvector/pgvector:pg15` puede exigir recrear el volumen local con `docker compose down -v`, lo que **destruye los datos de desarrollo**.

#### Variables de Entorno - Desarrollo

**Backend (.env.dev)**
```env
ASPNETCORE_ENVIRONMENT=Development
ASPNETCORE_URLS=http://localhost:5000

# Database
ConnectionStrings__DefaultConnection=Host=localhost;Port=5432;Database=joyeria_dev;Username=dev_user;Password=dev_password

# JWT
JWT__SecretKey=dev-secret-key-minimum-32-characters-long
JWT__Issuer=JoyeriaAPI-Dev
JWT__Audience=JoyeriaClient-Dev
JWT__ExpirationMinutes=1440

# Storage
Storage__Type=Local
Storage__LocalPath=./uploads

# CORS
CORS__AllowedOrigins=http://localhost:3000,http://localhost:5173

# Logging
Logging__LogLevel__Default=Debug
Logging__LogLevel__Microsoft=Information
Logging__LogLevel__Microsoft.AspNetCore=Warning
```

**Frontend (.env.development)**
```env
VITE_API_BASE_URL=http://localhost:5000/api
VITE_ENVIRONMENT=development
VITE_ENABLE_DEV_TOOLS=true
```

### Características de Desarrollo

- **Hot Reload**: Cambios en código se reflejan automáticamente
- **Source Maps**: Debugging completo en navegador
- **Logging Detallado**: Logs completos en consola
- **Datos de Prueba**: Seeders para datos iniciales
- **Sin HTTPS**: Desarrollo local sin certificados SSL
- **CORS Permisivo**: Permite requests desde localhost
- **Errores Detallados**: Stack traces completos en respuestas

---

## Entorno de Producción

### Arquitectura en Cloud (Free-tier)

#### Opción AWS

```mermaid
flowchart TB
    subgraph AWS["AWS Cloud (producción actual)"]
        EC2["EC2 + nginx<br/>- TLS en :443<br/>- Proxy a :8080"]
        
        subgraph Docker["Contenedor Docker"]
            BackendContainer["API .NET 10 + SPA React<br/>(imagen bundlada ECR)"]
        end
        
        RDS["RDS PostgreSQL<br/>db.t3.micro<br/>20GB"]
        
        S3["S3 prod-jpv-files<br/>Fotos / modelos ML"]
        
        SSM["SSM Parameter Store<br/>/jpv/prod/*"]
        
        CloudWatch["CloudWatch Logs"]
        
        EC2 -->|local| Docker
        Docker --> RDS
        Docker --> S3
        Docker -.->|lectura| SSM
        Docker --> CloudWatch
    end
```

#### Opción Azure

```mermaid
flowchart TB
    subgraph Azure["Azure Cloud"]
        AzureCDN["Azure CDN<br/>- Distribución del frontend<br/>- Cache de assets estáticos<br/>- SSL/TLS automático"]
        
        subgraph AppService["Azure App Service"]
            BackendContainerAzure["Backend Container (.NET 10)<br/>- F1 Free Tier (1GB RAM)<br/>- Linux Container<br/>- Auto-scaling básico"]
        end
        
        AzureDB["Azure Database PostgreSQL<br/>B1ms<br/>2GB RAM"]
        
        BlobStorage["Blob Storage<br/>(Fotos)<br/>5GB"]
        
        AppInsights["Application Insights<br/>(Logs)"]
        
        AzureCDN -->|HTTPS| AppService
        AppService --> AzureDB
        AppService --> BlobStorage
        AppService --> AppInsights
    end
```

### Configuración de Producción

#### Dockerfile de Producción (Backend)

```dockerfile
# Build stage
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy csproj and restore dependencies
COPY ["Joyeria.API/Joyeria.API.csproj", "Joyeria.API/"]
RUN dotnet restore "Joyeria.API/Joyeria.API.csproj"

# Copy everything else and build
COPY . .
WORKDIR "/src/Joyeria.API"
RUN dotnet build "Joyeria.API.csproj" -c Release -o /app/build

# Publish stage
FROM build AS publish
RUN dotnet publish "Joyeria.API.csproj" -c Release -o /app/publish

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=publish /app/publish .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

ENTRYPOINT ["dotnet", "Joyeria.API.dll"]
```

#### Variables de Entorno - Producción

**Backend (Azure App Service / AWS ECS)**
```env
ASPNETCORE_ENVIRONMENT=Production
ASPNETCORE_URLS=http://+:8080

# Database (desde Azure Key Vault / AWS Secrets Manager)
ConnectionStrings__DefaultConnection=<from-secrets>

# JWT (desde secrets)
JWT__SecretKey=<from-secrets-min-32-chars>
JWT__Issuer=JoyeriaAPI-Prod
JWT__Audience=JoyeriaClient-Prod
JWT__ExpirationMinutes=480

# Storage
Storage__Type=Cloud
Storage__Provider=AWS-S3|Azure-Blob
Storage__BucketName=joyeria-photos-prod
Storage__Region=us-east-1|westeurope

# CORS
CORS__AllowedOrigins=https://joyeria-app.com,https://www.joyeria-app.com

# Logging
Logging__LogLevel__Default=Information
Logging__LogLevel__Microsoft=Warning
Logging__LogLevel__Microsoft.AspNetCore=Warning
```

**Frontend (Build de Producción)**
```env
VITE_API_BASE_URL=https://api.joyeria-app.com/api
VITE_ENVIRONMENT=production
VITE_ENABLE_DEV_TOOLS=false
```

### Características de Producción

- **HTTPS Obligatorio**: Todas las comunicaciones cifradas
- **CORS Restrictivo**: Solo dominios permitidos
- **Logging Estructurado**: Logs a CloudWatch/Application Insights
- **Health Checks**: Endpoints para monitoreo
- **Connection Pooling**: Optimización de conexiones DB
- **Caching**: CDN para assets estáticos
- **Secrets Management**: Credenciales en servicios gestionados
- **Error Handling**: Respuestas genéricas sin detalles internos

---

## Entorno de Demostración (C17)

Hay un **tercer entorno**, y no es una variante de los dos anteriores: vive en una **cuenta AWS distinta** de la de la tienda, con estado de Terraform propio (`terraform/demo/`) y sin una sola arista hacia producción — ni infraestructura, ni permisos, ni flujos de despliegue, ni datos. Existe para poder enseñar el sistema completo funcionando, con el corpus cargado, sin tocar el catálogo real del negocio.

### Topología

Cuatro contenedores sobre una única instancia, descritos en `compose.demo.yaml`:

| Servicio | Papel | Puertos publicados |
|---|---|---|
| `jbg-demo-proxy` | Caddy: termina TLS y emite y renueva el certificado por sí mismo | **80 y 443 — los únicos** |
| `jbg-demo-api` | API .NET con la SPA embebida, servida desde su propio `wwwroot` | ninguno |
| `jbg-demo-ai` | Servicio `jbg-ai`, con límite de memoria explícito de 512 MiB | ninguno |
| `jbg-demo-postgres` | PostgreSQL 15 con pgvector, en contenedor y con volumen persistente | ninguno |

### Tres diferencias que importan frente a producción

- **Caddy en lugar de nginx.** El certificado se emite y renueva solo, sin cliente de certificados en el anfitrión ni tarea programada, y el aprovisionamiento de la máquina no sabe nada de dominios.
- **PostgreSQL en contenedor en lugar de RDS.** Vuelve irrelevante la pregunta de si el servicio gestionado admite la extensión vectorial, y da simetría exacta con el entorno local: el mismo `bootstrap.sql` y el mismo camino de migraciones funcionan sin una variación.
- **El servicio de IA no publica puertos.** Custodia la clave del proveedor de embeddings, y la frontera se cumple en **tres capas independientes**: el grupo de seguridad sólo abre 80 y 443, el proxy es el único servicio con puertos publicados, y el propio servicio no declara ninguno. Como consecuencia, el navegador no puede consultarlo: la tarjeta de estado del panel de administración la sirve un endpoint .NET que hace de intermediario.

El nombre de dominio es un **parámetro**, no una constante de construcción: el entorno arranca bajo un nombre derivado de su IP elástica y migra a un dominio propio sin reconstruir ninguna imagen. Procedimiento completo en [`deploy/demo/README.md`](../deploy/demo/README.md).

---

## Diferencias Clave: Desarrollo vs Producción

| Aspecto | Desarrollo | Producción |
|---------|-----------|------------|
| **Entorno** | Local (Docker Compose) | Cloud (AWS/Azure) |
| **HTTPS** | No (HTTP localhost) | Sí (SSL/TLS) |
| **CORS** | Permisivo (localhost) | Restrictivo (dominios específicos) |
| **Logging** | Consola (Debug) | CloudWatch/App Insights (Info/Warning) |
| **Errores** | Stack traces completos | Mensajes genéricos |
| **Base de Datos** | PostgreSQL local (Docker) | RDS/Azure Database |
| **Storage** | Sistema de archivos local | S3/Blob Storage |
| **Build** | Hot reload | Build optimizado |
| **Secrets** | Archivos .env | Key Vault/Secrets Manager |
| **Monitoreo** | Manual (consola) | Automático (CloudWatch/Insights) |
| **Escalabilidad** | 1 instancia | Auto-scaling (1-2 instancias) |

---

## Estructura del Proyecto

```
joiabagur-pv/
├── backend/
│   ├── src/
│   │   ├── JoiabagurPV.API/             # Controllers, Middleware, Extensions, Program.cs
│   │   ├── JoiabagurPV.Application/     # DTOs, Interfaces, Services, Validators
│   │   ├── JoiabagurPV.Domain/          # Entities, Enums, Exceptions, Interfaces
│   │   ├── JoiabagurPV.Infrastructure/  # Data (DbContext, Migrations), Services
│   │   └── JoiabagurPV.Tests/           # UnitTests, IntegrationTests, TestHelpers
│   ├── api-tests/
│   ├── scripts/ml-training/
│   └── docker-compose.yml               # postgres (pgvector), pgadmin, jbg-ai
├── frontend/
│   ├── src/                             # pages, components, services, hooks, providers, routing, types
│   ├── e2e/                             # Playwright
│   └── package.json
├── ai-service/                          # Microservicio de IA (C01–C26)
│   ├── src/jbg_ai/
│   │   ├── api/                         # main.py (create_app), auth.py, deps.py, middleware.py, routers/, schemas/
│   │   ├── config/                      # settings.py (pydantic-settings)
│   │   ├── db/                          # motor perezoso, pool acotado (C05)
│   │   ├── data/                        # CLI C06b; api.main no lo importa
│   │   ├── enrichment/                  # extractor C09 (vocabularios, talla, LiteLLM, auditor)
│   │   ├── indexing/                    # C11 source-text/embeddings (congelado) + C13 feed/orquestador/mapa; api.main no lo importa
│   │   ├── retrieval/                   # C14 retriever vectorial (embed max_attempts=1, <=> HNSW, filtros del body)
│   │   │                                # + C20 expansión de consulta: diccionario en dos capas y CLI de medición
│   │   │                                # + C21 rama léxica (lexical), fusión RRF (fusion), filtros que
│   │   │                                #   degradan (filters) y caché acotado del singleton (cache)
│   │   │                                # + C22 alcance por punto de venta (projection)
│   │   │                                # + C24 desempate determinista en las dos sentencias
│   │   │                                # + C25 fusión en dos etapas con pesos por rama (C25bis
│   │   │                                #   retiró la plana y los pesos por lista), ponderación por
│   │   │                                #   cobertura, señal de POS que lee sin restringir, score
│   │   │                                #   de negocio en el último bloque y abstención relativa
│   │   │                                #   por consulta (abstention)
│   │   │                                # + C26 sustitutos sobre el embedding ALMACENADO
│   │   │                                #   (substitutes): producto -> producto, sin proveedor ni
│   │   │                                #   fusión; piece_type es el único filtro duro y la talla y
│   │   │                                #   la disponibilidad degradan como términos continuos;
│   │   │                                #   origen inexistente/inactivo/sin embedding -> 422 con causa
│   │   ├── families/                    # C18a agrupador + C18b auditoría de familias persistidas; offline
│   │   ├── knowledge/                   # C23 segundo índice: corpus, troceado, indexador y búsqueda con citas
│   │   ├── evals/                       # C24 arnés de evaluación: golden set, pooling, métricas, líneas
│   │   │                                #   base, barrido, informe y sumidero opcional (CLI `uv run evals`)
│   │   │                                # + C26 rebanada de sustitutos anclada por producto origen
│   │   │                                #   (substitutes_slice), fuera de la tabla de ablations publicada
│   │   └── stubs/                       # respuestas deterministas bajo STUB_MODE
│   ├── prompts/                         # catalog-synth/v3 (C06b) + enrichment/v1 (C09)
│   ├── openapi.json                     # snapshot versionado del contrato
│   ├── tests/                           # api, config, db, migrations, data, enrichment, evals, families, indexing, knowledge, retrieval, support
│   ├── pyproject.toml · uv.lock
│   └── Dockerfile
├── terraform/                           # IaC de producción (EC2, RDS, S3, ECR, SSM, IAM)
├── openspec/                            # Contexto, specs vivas y changes
├── Documentos/                          # Documentación funcional y de arquitectura
└── .github/workflows/                   # CI/CD
```

---

## Flujos de Datos Principales

### 1. Flujo de Autenticación

```mermaid
sequenceDiagram
    participant Cliente
    participant Backend
    participant PostgreSQL
    
    Cliente->>Backend: POST /api/auth/login<br/>{ username, password }
    Backend->>PostgreSQL: Valida credenciales
    PostgreSQL-->>Backend: Credenciales válidas
    Backend->>Backend: Genera JWT token
    Backend-->>Cliente: { token, refreshToken, expiresIn }
    Cliente->>Cliente: Almacena token<br/>(httpOnly cookie o localStorage)
```

### 2. Flujo de Reconocimiento de Imagen

```mermaid
sequenceDiagram
    participant Usuario
    participant Cliente
    participant ML["Modelo ML"]
    participant Backend
    participant Storage["S3/Blob Storage"]
    participant PostgreSQL
    
    Usuario->>Cliente: Toma foto con cámara
    Cliente->>ML: Ejecuta inferencia localmente
    ML-->>Cliente: 3-5 productos sugeridos con scores
    Cliente->>Usuario: Muestra sugerencias
    Usuario->>Cliente: Selecciona producto correcto
    Cliente->>Backend: POST /api/sales<br/>{ productId, pointOfSaleId, paymentMethodId, photo }
    Backend->>Backend: Valida datos y usuario
    Backend->>Storage: Sube foto
    Storage-->>Backend: Foto subida
    Backend->>PostgreSQL: Crea registro de venta
    Backend->>PostgreSQL: Actualiza stock
    PostgreSQL-->>Backend: Operación exitosa
    Backend-->>Cliente: { saleId, success: true }
```

### 3. Flujo de Importación de Productos

```mermaid
sequenceDiagram
    participant Usuario
    participant Cliente
    participant Backend
    participant PostgreSQL
    
    Usuario->>Cliente: Sube archivo Excel
    Cliente->>Backend: POST /api/products/import<br/>FormData { file: Excel }
    Backend->>Backend: Valida archivo Excel
    Backend->>Backend: Procesa filas (match por SKU)
    Backend->>PostgreSQL: Inserta/Actualiza productos
    PostgreSQL-->>Backend: Operación completada
    Backend->>Backend: Genera resumen de importación
    Backend-->>Cliente: { imported: 50, updated: 10, errors: [] }
```

---

## Seguridad

### Autenticación y Autorización

- **JWT Tokens**: Stateless authentication
- **Refresh Tokens**: Renovación automática de sesión
- **Password Hashing**: BCrypt con salt
- **Role-Based Access Control**: Admin vs Operador
- **CORS**: Configurado por origen permitido

### Protección de Datos

- **HTTPS**: Todas las comunicaciones cifradas
- **Secrets Management**: Credenciales en servicios gestionados
- **SQL Injection**: Prevención mediante Entity Framework Core
- **XSS**: Sanitización de inputs
- **CSRF**: Tokens CSRF en formularios

### Almacenamiento Seguro

- **S3/Blob Storage**: Políticas de acceso restringidas
- **Pre-signed URLs**: Para acceso temporal a imágenes
- **Encriptación**: Datos en reposo encriptados

---

## Optimizaciones para Free-tier

### Backend

- **Connection Pooling**: Máximo 5-10 conexiones simultáneas
- **Caching**: Cache en memoria para datos frecuentes (productos)
- **Lazy Loading**: Carga diferida de relaciones
- **Paginación**: Todas las listas paginadas (máx 50 items/página)
- **Compresión**: Respuestas comprimidas (gzip)

### Base de Datos

- **Índices Optimizados**: 
  - SKU (único)
  - PointOfSaleId + ProductId (ventas)
  - CreatedAt (búsquedas por fecha)
- **VACUUM Regular**: Limpieza automática de PostgreSQL
- **Queries Optimizadas**: Evitar N+1 queries

### Frontend

- **Code Splitting**: Carga diferida de módulos
- **Lazy Loading**: Componentes cargados bajo demanda
- **Image Optimization**: Compresión y formatos modernos (WebP)
- **Bundle Size**: Minimizar tamaño del bundle (< 500KB inicial)
- **Service Workers**: Cache de assets estáticos

### Storage

- **Image Compression**: Reducir tamaño antes de subir
- **Lifecycle Policies**: Eliminar imágenes antiguas automáticamente
- **CDN**: Cache agresivo de imágenes

---

## Monitoreo y Logging

### Logging

- **Serilog**: Backend logging estructurado
- **Niveles**: Debug (dev), Information/Warning (prod)
- **Destinos**: 
  - Desarrollo: Consola
  - Producción: CloudWatch Logs / Application Insights

### Health Checks

- **Endpoint**: `/health`
- **Checks**:
  - Database connectivity
  - Storage connectivity
  - Memory usage

### Métricas Clave

- **Request Rate**: Requests por minuto
- **Response Time**: Tiempo promedio de respuesta
- **Error Rate**: Porcentaje de errores
- **Database Connections**: Conexiones activas
- **Storage Usage**: Espacio utilizado

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main, develop ]

jobs:
  build-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t joyeria-backend ./backend
      - name: Run tests
        run: docker run joyeria-backend dotnet test
      
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build
      
  deploy:
    needs: [build-backend, build-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to AWS/Azure
        # Configurar deployment según proveedor
```

---

## Consideraciones de Escalabilidad Futura

### Si el Proyecto Crece

1. **Escalar Verticalmente**: Aumentar recursos de instancia (RAM, CPU)
2. **Escalar Horizontalmente**: Múltiples instancias con load balancer
3. **Read Replicas**: Réplicas de lectura para PostgreSQL
4. **Caching Layer**: Redis para cache distribuido
5. **CDN Ampliado**: Más puntos de presencia
6. **Migración a Microservicios**: Solo si realmente necesario

### Límites de Free-tier

- **AWS**: 
  - RDS: 750 horas/mes (db.t3.micro)
  - ECS: 750 horas/mes
  - S3: 5GB storage, 20,000 GET requests
- **Azure**:
  - App Service: F1 Free (1GB RAM, limitado)
  - Database: B1ms (limitado)
  - Blob Storage: 5GB

**Recomendación**: Monitorear uso y planificar upgrade antes de alcanzar límites.

---

## Checklist de Despliegue

### Pre-despliegue

- [ ] Variables de entorno configuradas
- [ ] Secrets en Key Vault/Secrets Manager
- [ ] Base de datos creada y migraciones aplicadas
- [ ] Storage buckets/containers creados
- [ ] Certificados SSL configurados
- [ ] Dominios DNS configurados
- [ ] Health checks funcionando

### Post-despliegue

- [ ] Verificar conectividad base de datos
- [ ] Verificar acceso a storage
- [ ] Probar autenticación
- [ ] Probar reconocimiento de imágenes
- [ ] Verificar logs en CloudWatch/Insights
- [ ] Probar health checks
- [ ] Verificar CORS
- [ ] Probar en dispositivos móviles

---

## Conclusión

Esta arquitectura monolítica simple con contenedores es ideal para el MVP del sistema de gestión de puntos de venta, proporcionando:

- ✅ Desarrollo rápido y mantenible
- ✅ Costos mínimos en free-tier
- ✅ Escalabilidad futura cuando sea necesario
- ✅ Separación clara entre desarrollo y producción
- ✅ Seguridad adecuada para datos sensibles
- ✅ Optimizaciones específicas para free-tier

La arquitectura puede evolucionar fácilmente a microservicios o serverless si el proyecto crece significativamente en el futuro.

---

## Documentación Relacionada

### Deploy en Producción

Para instrucciones detalladas sobre el deploy en AWS, consultar:

- **[Guía de Deploy AWS](Guias/deploy-aws-production.md)**: Producción en EC2, Terraform, RDS, S3, ECR, OIDC y GitHub Actions.
- **[Migración EC2](Guias/deploy-aws-ec2-migration.md)** y **[Legado App Runner](Guias/deploy-aws-app-runner-legacy.md)**.

- **[Comparación AWS vs Azure](Propuestas/comparacion-aws-azure-deploy.md)**: Análisis detallado de pros y contras de ambas plataformas, costos estimados, y justificación de la elección de AWS.

- **[OpenSpec Proposal](../openspec/changes/archive/2026-01-18-add-aws-production-deployment/proposal.md)**: Propuesta técnica formal para la implementación del deploy en AWS (change archivado).

### Servicio de IA (Proyecto Final AIEng)

- **[Diseño del sistema de IA](Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)**: arquitectura RAG, frontera de responsabilidad Python ↔ .NET (§6), diseño del sistema de recuperación (§7) y despliegue (§12).
- **[Plan de changes OpenSpec](Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)**: descomposición en 39 changes (C01–C39), olas y grafo de dependencias.
- **[Especificaciones funcionales v2](Proyecto%20Final%20AIEng/joiabagur-ia-especificaciones-funcionales-v2.md)**: funcionalidades priorizadas y criterios de aceptación de negocio.
- **Épicas asociadas**: EP11–EP17 en [epicas.md](epicas.md).

### Decisiones de Arquitectura

| Decisión | Opción Elegida | Justificación |
|----------|----------------|---------------|
| **Cloud Provider** | AWS | Experiencia del equipo, free-tier generoso |
| **Backend + frontend** | EC2 + Docker (imagen bundlada) + nginx | Un solo dominio, TLS en instancia, Terraform |
| **Database** | RDS PostgreSQL | Managed service, backups automáticos (p. ej. 7 días) |
| **File Storage** | S3 `prod-jpv-files` | Fotos y modelos ML; bucket distinto del legado `jpv-files-prod` |
| **Frontend estático** | Incluido en imagen (`wwwroot`) | Sin CloudFront dedicado en la pila nueva |
| **Secrets / config** | SSM Parameter Store | Parámetros leídos por la API en producción |
| **CI/CD** | GitHub Actions | Ya en uso, free-tier generoso, actions oficiales AWS |
| **Servicio de IA** | Microservicio Python separado (`jbg-ai`) | Aísla el ecosistema vectorial/LLM sin contaminar el monolito .NET; se despliega y evoluciona por separado |
| **Base vectorial** | pgvector sobre la misma RDS, esquema `ai` | Una sola base de datos, filtros SQL nativos y cero infraestructura nueva. La decisión no se justifica por escala (~1.500 vectores) sino por operación |
| **Frontera Python ↔ .NET** | JWT interno HS256 sobre red Docker interna; C13 tira del feed C12 (`X-Index-Feed-Key`) | Python nunca lee ni escribe `public`; el navegador nunca habla con Python; .NET es la autoridad final sobre precio, stock y permisos |
| **Moneda** | Euro (EUR, €) | Mercado objetivo español/europeo |
| **Locale** | es-ES | Formato español para números y fechas |

### Localización y Formato de Moneda

El sistema está configurado para el mercado español/europeo:

| Configuración | Valor | Descripción |
|---------------|-------|-------------|
| **Moneda** | EUR (€) | Euro como moneda principal |
| **Locale** | es-ES | Español de España |
| **Formato de Precios** | €X.XX | Símbolo € antes del valor, 2 decimales |
| **Intl.NumberFormat** | `es-ES`, `EUR` | Para formateo automático de moneda |

**Implementación Frontend:**
```typescript
// Formato simple
€{price.toFixed(2)}

// Formato con Intl.NumberFormat
new Intl.NumberFormat('es-ES', {
  style: 'currency',
  currency: 'EUR',
}).format(amount);
```

