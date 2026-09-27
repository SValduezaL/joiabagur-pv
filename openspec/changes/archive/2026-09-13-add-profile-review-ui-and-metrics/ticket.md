# T-AIENG-028: Stratified human review of AI product profiles, with per-field correction rate and review timing (C28)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-026](../../archive/2026-09-12-add-substitutes-retrieval/ticket.md) y el resto de los
> tickets del Proyecto Final.

**HU origen:** [HU-AIENG-028](../../../../Documentos/Historias/AI-Eng/HU-AIENG-028.md)
**Change:** `add-profile-review-ui-and-metrics` (C28) · **Épica:** EP13
**Rama:** `c28-add-profile-review-ui-and-metrics` · **Mediciones:** [c28-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c28-exploration-measurements.md)

---

## Título

Implementar la revisión humana de perfiles de IA sobre una **cola de origen y no de estado**, con
**muestra estratificada y determinista** de 180 productos, corrección registrada **con dirección**,
cronómetro **persistido por ítem** y endpoint de métricas que reporta **por campo, por estrato y por
dirección** — sin migración, sin tocar `ai-service/` y sin mover el contrato congelado.

---

## Contexto y Problema

El §7.8 del diseño promete una revisión híbrida, el §11.5 dos métricas y el §16 las pide como casilla
de entrega. **Las tres son afirmaciones sin respaldo:** los 1.200 perfiles están en `ReviewOrigin =
AutoBulk`, con **cero revisores y cero tiempos**.

Y la ficha del plan se apoya en una premisa que el árbol desmiente. **El enrutado híbrido no acota la
cola:**

```
  size_label  →  "rule"      539 de 1200   ← el ÚNICO campo que el extractor marca como regla
  piece_type  →  "inferred" 1173 de 1200
  materials   →  "inferred" 1200 de 1200
  stone_type  →  "inferred"  629 de 1200

  → el 100 % de los productos entra en la cola con 2-3 campos sensibles inferidos
  → la política del §7.8 filtra correctamente y no descarta a nadie
```

**Y la confianza es un escalón de evidencia, no una probabilidad** — `1,00` regla / `0,85` la frase
está en el texto / `0,45` el modelo la afirmó sin evidencia / `0,20` ausente. De ahí sale el hallazgo
que gobierna el diseño del muestreo:

```
  La heurística de span solo caza FALSOS POSITIVOS.
  Es ciega, por construcción, a las OMISIONES.

  Materiales nombrados en el texto y no extraídos:
     hilo 60  ·  perla 35  ·  plata 3   →  94 productos distintos
                                           81 de ellos (86 %) en el estrato de MÁXIMA confianza

  → una cola ordenada por confianza ascendente no vería 81 de los 94 errores
```

Por eso el lote es **estratificado** y no ordenado, y por eso la corrección se registra **con
dirección**: las retiradas deben concentrarse en el estrato B y las adiciones en el C. Es una
predicción falsable, y confirmarla o refutarla es el resultado del change.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado hoy | Qué hace C28 |
|---|---|---|
| [`Domain/Entities/ProductAiProfile.cs`](../../../../backend/src/JoiabagurPV.Domain/Entities/ProductAiProfile.cs) | `ProposedProfileJson`, `FieldConfidenceJson`, `FieldSourceJson`, `ReviewStatus`, `ReviewOrigin`, `ReviewedByUserId`, `ReviewedAt`, `ReviewDurationMs` — **todas presentes** | **Sin cambios y sin migración.** C08 reservó el almacenamiento por escrito y cumplió |
| [`Application/Interfaces/IProductAiProfileService.cs`](../../../../backend/src/JoiabagurPV.Application/Interfaces/IProductAiProfileService.cs) | **Una sola operación**: `EnrichBatchAsync`. Su docstring dice que leer, aprobar y medir *«are the review capability's job»* | **Se respeta:** el trabajo va en un servicio nuevo, no aquí |
| [`API/Controllers/AiCatalogController.cs`](../../../../backend/src/JoiabagurPV.API/Controllers/AiCatalogController.cs) | `[Route("api/ai/catalog")]`, `[Authorize(Roles = "Administrator")]`. Ya sirve `family-audit`, `family-verdicts` y `family-review-metrics` | **Tres rutas nuevas** bajo el mismo prefijo y el mismo rol |
| [`Application/Services/FamilyAuditService.cs`](../../../../backend/src/JoiabagurPV.Application/Services/FamilyAuditService.cs) `GetMetricsAsync` | Reporta **dos poblaciones aparte**, `AverageReviewSeconds` **nulo y nunca cero** cuando no hay tiempos | **Es el patrón a replicar**, no a reinventar |
| [`Infrastructure/Data/Repositories/IndexFeedRepository.cs`](../../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/IndexFeedRepository.cs) | La marca de agua incluye `profile.UpdatedAt`; `IsActive` y `ReviewStatus` viajan en la fila | **Sin cambios.** Una corrección se reindexa sola y una baja se propaga |
| [`API/Controllers/ProductFamiliesController.cs`](../../../../backend/src/JoiabagurPV.API/Controllers/ProductFamiliesController.cs) | `POST` (línea 110) y `PUT {id}/members` (166) ya existen, ambos solo administrador | **Sin cambios.** Crear familia desde la revisión es **frontend puro** |
| [`frontend/src/pages/admin/family-review.tsx`](../../../../frontend/src/pages/admin/family-review.tsx) | **920 líneas**, monolítica, `shadcn/Table`, cronómetro por ítem ya corregido, **cero manejadores de teclado** | Cede **tres piezas** a un hook/componente compartido y **recibe los atajos** |
| [`frontend/src/services/family-review.service.ts`](../../../../frontend/src/services/family-review.service.ts) | Rutas relativas (`VITE_API_BASE_URL` ya trae `/api`), resultado discriminado para distinguir «vacío» de «no se pudo» | **Es el patrón** del servicio nuevo |
| [`frontend/src/routing/routes.tsx`](../../../../frontend/src/routing/routes.tsx) | `FAMILY_REVIEW: '/admin/family-review'` | **Una entrada nueva**: `PROFILE_REVIEW: '/admin/profile-review'` |
| `ai-service/` | — | **No se toca.** Ni `openapi.json`, ni `confidence.py`, ni `vocabularies.yaml`, ni los prompts |

---

## Componentes Afectados

- **`backend/src/JoiabagurPV.Application`** — servicio de revisión, DTOs, validación, cálculo de
  estrato y de métricas.
- **`backend/src/JoiabagurPV.API`** — rutas nuevas en `AiCatalogController`.
- **`backend/src/JoiabagurPV.Tests`** — unitarios del cálculo, integración de rutas y permisos.
- **`frontend/src`** — `pages/admin/profile-review.tsx`, `pages/admin/family-review.tsx`,
  `services/profile-review.service.ts`, `types/`, `hooks/`, `components/`, `routing/`.
- **`openspec/changes/add-profile-review-ui-and-metrics/`** — proposal, design, specs delta y tasks.
- **`Documentos/`** — épicas, plan de changes, informe de implementación y §15 limitación 2.

**No tocados a propósito:** `backend/src/JoiabagurPV.Domain`, `.Infrastructure`, `ai-service/`,
`terraform/`, `.github/workflows/`.

---

## Especificaciones Técnicas

### Backend

**Rutas nuevas** — todas bajo `api/ai/catalog`, todas `[Authorize(Roles = "Administrator")]`:

| Método | Ruta | Propósito |
|---|---|---|
| `GET` | `api/ai/catalog/profile-review-queue` | Lote estratificado y determinista. Parámetros: estrato, página, tamaño (**máx. 50**) |
| `POST` | `api/ai/catalog/profile-reviews` | Registra **una** revisión con sus valores corregidos y su duración |
| `POST` | `api/ai/catalog/profile-reviews/bulk` | Aprobación masiva **de un campo dentro de un estrato** |
| `GET` | `api/ai/catalog/profile-review-metrics` | Tasa por campo, estrato y dirección; dos poblaciones de tiempo |

**`IProfileReviewService`** en `Application/Interfaces/`, con implementación en
`Application/Services/`. Servicio nuevo y no una ampliación de `IProductAiProfileService`, porque su
propio docstring ya adjudica este trabajo a la capacidad de revisión.

**Definición de estrato — en un único sitio.** Función compartida por la cola y por las métricas:

```text
peor = MIN( conf(piece_type) ?? 0,20 ,
            conf(materials)  ?? 0,20 ,
            conf(stone_type) ?? 1,00 )     ← ausente no penaliza: la mayoría de joyas no lleva piedra

  peor ≤ 0,20  →  A · ausencia          122 productos   cuota 60
  peor ≤ 0,45  →  B · sin evidencia     285 productos   cuota 60
  peor = 0,85  →  C · con evidencia     761 productos   cuota 60
```

**Universo de la cola:** `ReviewOrigin = AutoBulk` **y** `ReviewStatus = Approved`. Los 32
`Rejected` se sirven por un filtro aparte y **no consumen cuota**.

**Muestreo determinista:** orden por `hash(ProductId + semilla)` dentro de cada estrato, con la
semilla en configuración. El lote es reproducible **sin persistirlo**, que es lo que evita la
séptima migración.

**Dirección de la corrección**, calculada diferenciando `ProposedProfileJson` de los valores en vigor:

| dirección | escalar | lista |
|---|---|---|
| `confirmación` | igual | conjuntos iguales |
| `adición` | nulo → valor | crecen los elementos |
| `retirada` | valor → nulo | decrecen los elementos |
| `sustitución` | valor → otro valor | mismo tamaño, distinto contenido |

**DTOs y validación (FluentValidation):** la petición masiva se **rechaza** si los productos
seleccionados cruzan más de un estrato o más de un campo; la individual exige `ReviewDurationMs` no
nulo. `ProposedProfileJson` **nunca** se reescribe.

### Frontend

- **Página** `src/pages/admin/profile-review.tsx`, registrada en `app-routing-setup.tsx` como `lazy`
  bajo `AdminRoute`, y en `routes.tsx` como `PROFILE_REVIEW: '/admin/profile-review'`.
- **Componentes Metronic/shadcn reutilizados**, los mismos que `family-review.tsx` ya usa: `Table`,
  `Card`, `Badge`, `Alert`, `Tabs`, `Button`, `Input`, `Skeleton`, `sonner`. **No se introduce
  TanStack Table**: solo 9 de 85 pantallas lo usan y todas son listados planos — el registro de C18b
  ya corrigió una tarea que lo afirmaba en falso.
- **Extracción estrecha**, solo lo que tiene **dos consumidores reales**:
  `useItemStopwatch()` · `<ThreeStateList>` · `useReviewKeyboard()`. Tabla, barra de acción masiva y
  tarjeta de métricas **se copian**.
- **Servicio** `profile-review.service.ts` con resultado discriminado para distinguir «vino vacío» de
  «no se pudo calcular», replicando `family-review.service.ts`.
- **Tipos** en `src/types/profile-review.types.ts`, espejo de los DTOs.
- **Atajos** enganchados también en `family-review.tsx`, inertes cuando el foco está dentro de un
  campo de texto.

### Datos

**Ninguna migración.** Ningún campo nuevo, ningún índice nuevo, ninguna entidad nueva.
`Documentos/modelo-de-datos.md` **no cambia**.

### ai-service

**Sin cambios.** El contrato congelado no se mueve y `test_openapi_snapshot_is_stable` no debe verse
afectado.

---

## Arquitectura

- **Capas** (`Documentos/modelo-c4.md`): el trabajo entra por `Application/` → `API/` → `frontend/`.
  `Domain/` e `Infrastructure/` quedan intactos, lo que es coherente con un change **sin 🗄️**.
- **Decisión estructural:** la cola es de **origen** y no de **estado**, apoyándose en un requisito
  ya vivo de [`product-ai-profile`](../../../specs/product-ai-profile/spec.md) — *«Review status and
  review origin are independent»*. El estado gobierna el índice, el origen gobierna la métrica.
  **Abrir el lote a `Pending` sacaría 180 documentos del índice a mitad de sesión**, porque el feed
  selecciona `Approved`.
- **Frontera .NET / Python** (§6.2 del diseño): la revisión humana y sus métricas son **negocio**, y
  viven en .NET. Python no interviene.
- **Patrones en uso:** Service Layer, Repository vía `ApplicationDbContext`, Dependency Injection,
  paginación obligatoria.
- **Breaking changes:** ninguno. Rutas nuevas, contrato de `jbg-ai` intacto, sin cambio de esquema.

---

## Definición de Hecho (DoD)

- [ ] Código en las capas de `Documentos/modelo-c4.md` y según las convenciones de `openspec/project.md`
- [ ] Backend: xUnit + Moq + FluentAssertions + Bogus, nomenclatura `Método_Escenario_ResultadoEsperado`, cobertura ≥ 70 %
- [ ] `Metrics_CorrectionRate_ComputedPerField` y `Metrics_ExcludesAutoBulkProfiles` en verde (tests nombrados por la ficha del plan)
- [ ] Tests añadidos: determinismo del muestreo, cuotas por estrato, dirección de la corrección, nulo-frente-a-cero en tiempos, rechazo de la masiva que cruza estrato o campo, y permisos 401/403
- [ ] Frontend: Vitest + RTL + MSW, nomenclatura `should [comportamiento] when [condición]`, queries accesibles, cobertura ≥ 70 %
- [ ] `should highlight inferred sensitive fields pending review` y `should record correction when material list is edited` en verde
- [ ] **Baseline de la suite tomado antes de tocar nada**, y comparación por **nombres** de test fallidos, nunca por recuento — backend y frontend vienen rojos de base (frontend: 118 de 482)
- [ ] `npm run build` en verde (el gate real del frontend; `tsc --noEmit` arrastra errores previos de Metronic)
- [ ] **Sin migración de EF Core** — verificado, no asumido
- [ ] Specs delta de `product-ai-profile` y `family-review` en `openspec/changes/<change>/specs/`
- [ ] `openspec validate --all --strict` con **0 failed**
- [ ] `ai-service/` sin diff; `openapi.json` sin diff
- [ ] **La sesión de revisión ejecutada**: 180 ítems cronometrados + los 32 rechazados, con su informe
- [ ] Documentación actualizada: `Documentos/epicas.md`, plan de changes, informe de implementación y §15 limitación 2 con el porcentaje real
- [ ] Sin TODO/FIXME sin tarea asociada
- [ ] UI en español (es-ES); moneda EUR (€) donde aplique

---

## Requisitos No Funcionales

- **Seguridad:** todas las rutas `[Authorize(Roles = "Administrator")]`. Un operador no revisa
  perfiles: la revisión reescribe lo que el catálogo afirma de una pieza. El revisor se toma de
  `ICurrentUserService`, **nunca del cuerpo de la petición**.
- **Rendimiento:** paginación obligatoria, máximo 50 ítems por página. El cálculo de estrato opera
  sobre 1.200 filas y no requiere índice nuevo. El cronómetro viaja en la petición que ya se hace: no
  añade viajes.
- **Observabilidad:** logging estructurado con Serilog en las escrituras de revisión, registrando
  quién, qué campo y qué dirección — sin volcar el perfil entero.
- **Integridad de datos:** `ProposedProfileJson` es **inmutable**; la tasa de corrección es la
  diferencia entre esa columna y los valores en vigor, y reescribirla destruiría la métrica de forma
  irrecuperable y silenciosa. `ReviewedAt` lo estampa el servidor; `ReviewDurationMs` lo mide el
  navegador y **queda nulo en masa**, nunca cero.
- **Accesibilidad:** los atajos no capturan teclas mientras el foco está en un campo de edición.

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del apply |
|---|---|---|
| 1 | ¿Las tres rutas van en `AiCatalogController` o en un `AiProfileReviewController` nuevo? | **En `AiCatalogController`**, por coherencia con `family-review-metrics` y porque comparte prefijo y rol. Si el fichero crece de más, se parte en el apply y se anota |
| 2 | ¿Qué teclas concretas para aprobar / rechazar / siguiente? | `A` aprobar, `R` rechazar, `J`/`K` o flechas para navegar, `Enter` guardar. A confirmar en la primera sesión real, que es la prueba que la ficha pide |
| 3 | ¿La semilla del muestreo se fija en configuración o se pasa por parámetro? | **Configuración**, con posibilidad de sobrescribir por parámetro para pruebas. Se declara en el informe |
| 4 | ¿El A/B de teclado se hace con bloques alternos o con los primeros ~40 a ratón? | **Primeros ~40 a ratón**, resto con teclado, alternando estratos. El efecto aprendizaje se declara en vez de controlarse |
| 5 | ¿`Presión Oro` (rechazado, `piece_type: anillo`, `["oro"]`) es realmente una sortija vendible? | Se resuelve **en la pasada sobre los 32 rechazados**, que existe precisamente para esto |
| 6 | Si la revisión confirma que `hilo` y `perla` faltan sistemáticamente, ¿se amplía el vocabulario? | **No en este change.** Se anota como hallazgo, igual que C18a hizo con `FIX1` |

---

## Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Alta** — el §13.4 la marca como *«nunca se recorta»*; el §16 la convierte en casilla marcada o vacía |
| **Estimación** | _Pendiente_ — a fijar en refinamiento. Referencia: sin migración ni contrato, pero con 1,5-2 h de revisión humana **dentro** del alcance |
| **Tags** | `backend` `frontend` `ai-eng` `EP13` `C28` `human-review` `metrics` `no-migration` |

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-028](../../../../Documentos/Historias/AI-Eng/HU-AIENG-028.md)
- **Mediciones:** [c28-exploration-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c28-exploration-measurements.md)
- **Diseño:** §7.8, §11.5, §15 limitación 2, §16 de [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Capabilities:** [`product-ai-profile`](../../../specs/product-ai-profile/spec.md) · [`family-review`](../../../specs/family-review/spec.md) · [`index-feed`](../../../specs/index-feed/spec.md)
- **Herencias de C18b:** [c18b-family-review-report.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c18b-family-review-report.md) §8.3 y § *«El tiempo medio no está»*
- **Procedimientos:** [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md) · [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md)
- **Testing:** [testing-backend.md](../../../../Documentos/testing-backend.md) · [testing-frontend.md](../../../../Documentos/testing-frontend.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-12 | Creación del ticket a partir de HU-AIENG-028 y de las siete mediciones de exploración. Tres puntos de la ficha del plan quedan refutados: el enrutado híbrido no acota la cola, no había criterio de muestreo escrito, y la aprobación masiva vacía la métrica de tiempo si no se acota. Se añaden a la zona `API/Controllers/` y `Tests/`, y una segunda pantalla de frontend |
