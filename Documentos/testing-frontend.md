# Testing Frontend - Guía Completa

## Visión General

Stack de testing seleccionado para el frontend React 19 + TypeScript + Vite del sistema de gestión de puntos de venta.

| Componente | Tecnología | Versión |
|------------|------------|---------|
| **Test Runner** | Vitest | 2.x |
| **Testing de Componentes** | React Testing Library | 16.x |
| **Simulación de Usuario** | @testing-library/user-event | 14.x |
| **Matchers DOM** | @testing-library/jest-dom | 6.x |
| **Mocking de API** | MSW (Mock Service Worker) | 2.x |
| **Tests E2E** | Playwright | 1.x |
| **Entorno DOM** | jsdom | 25.x |

---

## 📚 Índice de Documentación

### Configuración Inicial
| Documento | Descripción |
|-----------|-------------|
| [01 - Configuración](Testing/Frontend/01-configuracion.md) | Stack tecnológico, instalación, estructura de proyecto y convenciones |

### Tests Unitarios y de Componentes
| Documento | Descripción |
|-----------|-------------|
| [02 - Tests Unitarios](Testing/Frontend/02-tests-unitarios.md) | Tests de hooks, utilities, helpers y funciones puras |
| [03 - Tests de Componentes](Testing/Frontend/03-tests-componentes.md) | React Testing Library, queries, user events, formularios (React Hook Form + Zod) y accesibilidad |
| [04 - Mocking de API](Testing/Frontend/04-mocking-api.md) | MSW handlers, escenarios de error, interceptores y estados de carga |

### Tests End-to-End
| Documento | Descripción |
|-----------|-------------|
| [05 - Tests E2E](Testing/Frontend/05-tests-e2e.md) | Playwright, navegación, formularios, autenticación y multi-navegador |

### CI/CD y Calidad
| Documento | Descripción |
|-----------|-------------|
| [06 - GitHub Actions](Testing/Frontend/06-github-actions.md) | Workflows, caché de dependencias, artifacts y reportes |
| [07 - Cobertura de Código](Testing/Frontend/07-cobertura-codigo.md) | Configuración de coverage, umbrales mínimos y reportes HTML |

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
cd frontend

# Vitest y Testing Library
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# MSW para mocking de API
npm install -D msw

# Playwright para E2E
npm install -D @playwright/test
npx playwright install
```

### 2. Configurar Vitest

**vite.config.ts**
```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['node_modules/', 'src/test/'],
    },
  },
})
```

**src/test/setup.ts**
```typescript
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Limpieza automática después de cada test
afterEach(() => {
  cleanup()
})
```

### 3. Ejecutar Tests

```bash
# Tests unitarios y de componentes
npm run test

# Tests en modo watch
npm run test:watch

# Tests con cobertura
npm run test:coverage

# Tests E2E con Playwright
npm run test:e2e

# Tests E2E con UI de Playwright
npm run test:e2e:ui
```

### 4. Scripts en package.json

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:headed": "playwright test --headed"
  }
}
```

---

## 📁 Estructura de Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx
│   │   │   └── button.test.tsx          # Test junto al componente
│   │   └── layouts/
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   └── use-auth.test.ts             # Test junto al hook
│   ├── services/
│   │   ├── api.service.ts
│   │   └── api.service.test.ts
│   ├── lib/
│   │   ├── utils.ts
│   │   └── utils.test.ts
│   └── test/
│       ├── setup.ts                      # Setup global de Vitest
│       ├── mocks/
│       │   ├── handlers.ts               # MSW handlers
│       │   └── server.ts                 # MSW server
│       ├── utils/
│       │   ├── render.tsx                # Custom render con providers
│       │   └── test-data.ts              # Factories de datos de test
│       └── __fixtures__/
│           └── products.json             # Datos de prueba
├── e2e/
│   ├── auth.spec.ts                      # Tests E2E de autenticación
│   ├── products.spec.ts                  # Tests E2E de productos
│   ├── sales.spec.ts                     # Tests E2E de ventas
│   └── fixtures/
│       └── test-user.json
├── playwright.config.ts
├── vite.config.ts
└── package.json
```

---

## 📋 Checklist de Implementación

### Fase 1: Setup Inicial
- [ ] Instalar dependencias de testing
- [ ] Configurar Vitest en `vite.config.ts`
- [ ] Crear archivo `src/test/setup.ts`
- [ ] Configurar scripts en `package.json`
- [ ] Crear estructura de carpetas de test

### Fase 2: Tests Unitarios
- [ ] Crear custom render con providers
- [ ] Tests de hooks personalizados (`use-auth`, `use-menu`, etc.)
- [ ] Tests de utilities (`lib/utils.ts`, `lib/helpers.ts`)
- [ ] Tests de servicios de API

### Fase 3: Tests de Componentes
- [ ] Configurar MSW handlers base
- [ ] Tests de componentes UI básicos (Button, Input, Select)
- [ ] Tests de componentes de formulario
- [ ] Tests de componentes con estado
- [ ] Tests de accesibilidad (a11y)

### Fase 4: Tests E2E
- [ ] Configurar Playwright (`playwright.config.ts`)
- [ ] Tests de flujo de autenticación
- [ ] Tests de CRUD de productos
- [ ] Tests de registro de ventas
- [ ] Tests responsive (móvil/desktop)

### Fase 5: CI/CD
- [ ] Crear workflow de GitHub Actions
- [ ] Configurar caché de dependencias
- [ ] Configurar reporte de tests
- [ ] Configurar cobertura de código
- [ ] Verificar ejecución en PR

### Fase 6: Mantenimiento
- [ ] Añadir badge de tests en README
- [ ] Documentar cómo ejecutar tests localmente
- [ ] Establecer cobertura mínima requerida (70%)
- [ ] Revisar y actualizar tests regularmente

---

## 📖 Convenciones

### Nomenclatura de Tests

```
describe('NombreComponente/Hook/Función', () => {
  it('should [comportamiento esperado] when [condición]', () => {})
})
```

**Ejemplos:**
- `should render product name when product is provided`
- `should call onSubmit when form is valid`
- `should show error message when API returns 401`
- `should disable button when loading is true`

### Estructura de Test

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('ProductCard', () => {
  it('should render product information correctly', async () => {
    // Arrange - Preparar datos y renderizar
    const product = { id: '1', name: 'Anillo Oro', sku: 'ANI-001' }
    render(<ProductCard product={product} />)

    // Act - Ejecutar acciones (si las hay)
    // En este caso no hay acciones

    // Assert - Verificar resultados
    expect(screen.getByText('Anillo Oro')).toBeInTheDocument()
    expect(screen.getByText('ANI-001')).toBeInTheDocument()
  })

  it('should call onClick when card is clicked', async () => {
    // Arrange
    const user = userEvent.setup()
    const handleClick = vi.fn()
    const product = { id: '1', name: 'Anillo Oro', sku: 'ANI-001' }
    render(<ProductCard product={product} onClick={handleClick} />)

    // Act
    await user.click(screen.getByRole('article'))

    // Assert
    expect(handleClick).toHaveBeenCalledWith(product)
  })
})
```

### Queries de Testing Library (Orden de Prioridad)

| Prioridad | Query | Uso |
|-----------|-------|-----|
| 1️⃣ | `getByRole` | Elementos accesibles (botones, links, etc.) |
| 2️⃣ | `getByLabelText` | Inputs de formulario |
| 3️⃣ | `getByPlaceholderText` | Inputs sin label visible |
| 4️⃣ | `getByText` | Texto visible |
| 5️⃣ | `getByDisplayValue` | Valor actual de inputs |
| 6️⃣ | `getByAltText` | Imágenes |
| 7️⃣ | `getByTitle` | Elementos con title |
| 8️⃣ | `getByTestId` | Último recurso (data-testid) |

---

## ⚠️ Estado de la suite: fallos conocidos

*Medido el 2026-08-29 sobre `c16-add-frontend-assisted-search-panel`, con el árbol de trabajo idéntico a `HEAD` para aislar la línea base. Node + Vitest 4 + jsdom.*

**482 tests, 118 fallos, en 17 de los 40 ficheros.** Duración: 252 s.

> **Re-medido el 2026-09-22, al implementar C36: la línea base da 597 tests, 114 fallos, en 15 de
> 48 ficheros, y al cierre **729** tests, 113 fallos, en 14 de 54.** Los **132** tests de más son de
> C36 y están los 132 en verde. La comparación por nombres salió **subconjunto estricto**: **cero
> nombres nuevos** y **uno que dejó de fallar**.
>
> **Y ese uno obliga a matizar el párrafo siguiente.** Es
> `pages/admin/__tests__/family-review.test.tsx :: should create a family with its members from the
> review screen`: falló en la línea base y pasó al cierre **sin que nadie tocara ni ese fichero ni su
> código de producción**. Explica por qué la línea base daba 114 y 15 ficheros donde el 13 de
> septiembre daba 113 y 14 — no es rojo acumulado, es que la suite creció seis ficheros y eso desplazó
> el orden de ejecución.
>
> Así que **la afirmación de que aquí el conjunto de fallos es estable entre ejecuciones era demasiado
> fuerte**: hay al menos un test dependiente del orden en el frontend, igual que en el backend, sólo
> que uno y no un puñado. **El método no cambia** —comparar por nombres sigue dando una respuesta
> binaria y útil—, pero conviene esperar que el recuento oscile entre **113 y 114** sin que nadie haya
> roto nada.
>
> **Y la verificación de C36 (2026-09-24) lo volvió a medir sobre el mismo commit de línea base**
> —regenerado en un worktree sobre `2b49685`— **y dio 113 fallos en 14 ficheros, no 114 en 15**: el
> test de `family-review` pasó también allí. Mismo commit, mismo código, dos respuestas. Refuerza la
> conclusión en vez de contradecirla, y es la razón por la que el recuento no sirve ni como línea base.
> Lo que se mantuvo idéntico en las dos mediciones: **cero nombres nuevos**. Detalle en
> `Documentos/Proyecto Final AIEng/informes/c36-implementation-measurements.md` §2.1.

> **Actualización del 2026-09-24, sobre `c40-add-frontend-free-query-panel`.** La suite tiene ahora
> **833 tests** —834 tras los arreglos de su verificación—: C40 añade **104**. La línea base dio
> **113 fallos de 729 en 14 de 54 ficheros**; al cierre, **113 de 833 en 14 de 57**, con el conjunto
> de nombres **idéntico** y el diff vacío. Los 104 tests nuevos están los 104 en verde.
>
> **Y no es un test dependiente del orden, son al menos tres ficheros.** La entrada anterior cerraba
> con `family-review.test.tsx` como el único caso conocido. C40 midió dos pasadas del **mismo
> commit** minutos aparte, a **113 y 114**, y el nombre discrepante fue un tercer fichero:
> `pages/sales/__tests__/scan.test.tsx :: ScanningPage should show manual SKU input fallback after
> initialization`, que **no había fallado en ninguna de las siete pasadas anteriores del change** y
> **pasa cuando el fichero se corre solo**. No toca nada de C40 —cero referencias a `ai-search`,
> `assisted` o `warnings`—. Su vecino del mismo fichero, `should render loading state initially`, es
> rojo en la línea base y **sigue rojo**, así que el fichero aporta un fallo fijo y uno oscilante.
>
> **El conjunto rotatorio conocido es, por tanto, `family-review.test.tsx`, `assist.test.tsx` y
> `scan.test.tsx`** — la tabla de inventario de más abajo los lista, pero como fallos sin más; lo que
> esta entrada añade es que **oscilan**. Y con ello el criterio útil deja de ser el del frontend y pasa
> a ser el del backend, que es el mismo en los dos árboles: **si el nombre discrepante cae en un
> fichero que ya estaba rojo y tu propia área está limpia, no es tuyo.** Un nombre nuevo en un fichero
> que tú tocas es una regresión; uno más en `scan.test.tsx` es martes.
>
> **La verificación de C40 lo reprodujo dos veces más** (2026-09-25), antes y después de sus arreglos:
> **113 de 833** y **113 de 834**, los mismos 14 ficheros las dos veces, y los **nueve** ficheros de
> test que C40 añade o toca en verde. Detalle en
> `Documentos/Proyecto Final AIEng/informes/c40-implementation-measurements.md` §10 y §14.3.

> **Actualización del 2026-09-26, sobre `c40-fix-all-shops-scope-unreachable` (C40_FIX).** La suite
> tiene **848 tests**: C40_FIX añade **14** de página y **1** de servicio, los quince en verde. La
> línea base del implementador dio **113 fallos de 834 en 14 de 57 ficheros**; su cierre, **114 de 848
> en 15**.
>
> **Y la verificación independiente midió el cierre otra vez, sobre el mismo commit `4b1d056`, y dio
> 113 en 14 ficheros.** El nombre que sobra en una pasada y falta en la otra es
> `admin/__tests__/family-review.test.tsx :: family review screen should create a family with its
> members from the review screen` — **el mismo** que C36 usó para refutar que aquí el conjunto fuera
> estable, y el mismo al que C40 apuntaba. Es la **tercera** observación independiente de ese nombre
> rotando, y esta vez en la dirección contraria: rojo para quien implementó, verde para quien
> verificó, mismo árbol. De paso se confirma el par de `scan.test.tsx` que describe la entrada
> anterior: `should render loading state initially` sigue rojo y `should show manual SKU input
> fallback after initialization` sale verde.
>
> **La consecuencia operativa, que es la que importa:** en este árbol **113 y 114 son el mismo
> resultado**, y quien mida uno u otro no está observando su propio cambio. `assisted.test.tsx` —el
> área del change— no aparece entre los rojos en ninguna de las tres pasadas.
>
> Detalle en el `qa.md` del change archivado, §1.1 y §11.9.

> **Actualización del 2026-09-26, sobre `c42-add-frontend-agent-panel` (C42).** La suite tiene ahora
> **953 tests**: C42 añade **99** —6 ficheros nuevos, los 99 en verde—. La línea base dio **113 fallos
> de 854 en 14 de 57 ficheros**; al cierre, **113 de 953 en 14**, con el conjunto de nombres
> **idéntico** y el diff vacío. Cuarta observación consecutiva de que el rojo de este árbol no crece
> con la suite.
>
> **Pero la primera comparación de C42 dio 114, y el nombre que sobraba era una regresión de verdad —
> la primera de esta serie de entradas.** `pages/sales/__tests__/sales-index.test.tsx :: should show
> "Buscar con Ayuda" tile linking to the assisted search panel`. La causa no estaba en ningún test
> nuevo: la tarjeta que C42 añade al hub llevaba la viñeta «Más lento y más caro que **buscar con
> ayuda**», con lo que el **nombre accesible de su propio enlace** pasaba a encajar también con
> `/Buscar con Ayuda/i`, y la consulta del test —`getByRole('link', { name: … })`— encontraba dos
> elementos. Reescrita la viñeta, el recuento vuelve a 113.
>
> **Y eso es lo que esta entrada aporta al método**, porque va justo contra la costumbre que las
> anteriores establecieron: aquí el nombre discrepante **no** era ruido de un fichero ya rojo. Cayó en
> un fichero que el change **tocaba** —`pages/sales/index.tsx`—, que es exactamente el criterio que las
> entradas de C40 y C40_FIX dejaron escrito: *un nombre nuevo en un fichero que tú tocas es una
> regresión; uno más en `scan.test.tsx` es martes*. El criterio funcionó a la primera.
>
> **La otra lección es sobre el paralelismo, y vale para las tres suites de este repositorio.** La
> primera medición de C42 lanzó `dotnet test`, `npm run test` y `uv run pytest` **a la vez**, y el
> backend dio **490 fallos de 1.347** en vez de 53: `vitest` con 14 *workers* satura la máquina y
> testcontainers deja de alcanzar el demonio de Docker por su tubería con nombre, así que **todos** los
> tests de integración fallan al arrancar con un `TimeoutException` de `NamedPipeClientStream`. En la
> misma pasada, `pytest` dio 2 rojos —sus dos tests de reloj del agente— que solos pasan. **Una pasada
> de las tres suites es serial**, y cuesta unos 20 minutos.
>
> Detalle en `Documentos/Proyecto Final AIEng/informes/c42-implementation-measurements.md` §1.

> **Re-medido el 2026-09-13, al cerrar C28: 595 tests, 113 fallos, en 14 de 48 ficheros.** La suite
> ha crecido 113 tests en dos semanas y el rojo **no ha crecido con ella**: cae de 118 a 113 y de 17
> ficheros a 14. La proporción pasa del 24 % al 19 %. El conjunto de nombres fallidos de C28 fue
> **idéntico entre línea base y cierre** —ni uno nuevo, ni uno resuelto— sobre 113 nombres, lo que
> dice algo que el backend no puede decir: **aquí el conjunto de fallos sí es estable entre
> ejecuciones**. La rotación que obliga a comparar por nombres en el backend no tiene equivalente en
> el frontend; lo que sí se mantiene es la razón para comparar por nombres, porque el **recuento**
> cambia en cuanto alguien añade tests. Detalle en
> `Documentos/Proyecto Final AIEng/informes/c28-implementation-measurements.md`. Ninguno tiene que ver con el código de producción: son defectos de los propios tests, mocks incompletos y aserciones que se quedaron atrás cuando la interfaz cambió. Se documentan aquí por la misma razón que los del backend — sin este registro, cada persona que ejecuta la suite pierde una hora concluyendo que ha roto algo — y por una razón más, que el backend no tiene.

> **`vitest` sale con código 0 si canalizas su salida.** `npm run test | tail` devuelve el código de `tail`, no el de la suite. Un prompt verde no significa nada: hay que leer la línea de resumen.

> **Actualización del 2026-08-30, sobre `c17-add-ai-service-deployment`.** La suite tiene ahora **529 tests, 116 fallos, en 15 de los 44 ficheros** en la línea base, y **533, 113 y 14 de 45** al cierre del change. Los cuatro tests de más son los de `pages/dashboard/ai-service-status.test.tsx`, los cuatro verdes.

> **Actualización del 2026-09-01, sobre `c18b-add-family-review-ui-and-orphan-alert`.** La suite
> tiene ahora **552 tests, 113 fallos, en 14 de los 46 ficheros**. La línea base de ese change dio
> **533 y 113**, y el cierre es el **caso más limpio que este documento registra**: los 113 nombres
> en rojo son **exactamente los mismos 113**, cero nuevos y cero arreglados.
>
> Los 19 tests de más son los de `pages/admin/__tests__/family-review.test.tsx`, los diecinueve
> verdes. Tres de ellos cubren el punto que da sentido a la pantalla —que una auditoría que **no se
> pudo calcular** nunca se pinte igual que una que vino vacía—, y para eso los tres estados viven en
> el tipo (`AuditOutcome`) y no en el render: un llamante no puede alcanzar las listas sin pasar por
> el estado.
>
> Conviene subrayar por qué esa comparación salió exacta donde la del backend no: **aquí el nombre
> del test sí es una unidad estable**. La inestabilidad por orden que documenta la guía del backend
> no se da en esta suite, así que comparar por nombres da una respuesta binaria y no una
> interpretación.
>
> El detalle está en
> `openspec/changes/archive/2026-09-01-add-family-review-ui-and-orphan-alert/qa.md` §2.
>
> La comparación por nombres salió **subconjunto estricto**: ni un fallo nuevo, y **tres que dejaron de fallar** sin que nadie tocara sus ficheros — los tres de `pages/sales/__tests__/assisted.test.tsx`, conocidos por ser dependientes del orden. Es la segunda vez que se observa el mismo fenómeno tras el de C16, y refuerza la regla de esta misma sección: el número no sirve, el conjunto de nombres sí.

### La comparación válida es por nombres, igual que en el backend

```powershell
# Línea base, antes de tocar nada
npm run test

# Después
npm run test
```

Tu cambio está limpio si el **conjunto de nombres** que falla es el mismo, no si coincide el número. Y el número tampoco es estable aquí: añadir ficheros de test desplaza el orden de ejecución, y con él un puñado de fallos dependientes del orden. En la pasada de C16, con 43 tests nuevos añadidos, **cinco tests que fallaban dejaron de fallar** sin que nadie tocara sus ficheros.

### Los 17 ficheros en rojo

| Fichero | Fallos | Causa dominante |
|---|---|---|
| `pages/products/edit.test.tsx` | **27 / 27** | A · `useAuth must be used within an AuthProvider` |
| `services/__tests__/ml-edge-cases.test.ts` | 23 / 27 | B · mock de TensorFlow.js incompleto |
| `services/__tests__/image-recognition.service.test.ts` | 15 / 40 | B + C |
| `pages/products/components/product-photo-upload.test.tsx` | 12 / 35 | E · aserciones desactualizadas |
| `pages/sales/__tests__/new.test.tsx` | **11 / 11** | A · `useCart must be used within a CartProvider` |
| `pages/sales/__tests__/new-image.test.tsx` | 8 / 17 | A · `useCart` |
| `pages/payment-methods/payment-methods.test.tsx` | 4 / 13 | E |
| `services/__tests__/model-training.service.test.ts` | 4 / 10 | C + `canvas.addEventListener is not a function` |
| `pages/products/__tests__/edit.test.tsx` | 4 / 4 | D · `vi.mock` sin factoría |
| `pages/products/create.test.tsx` | 2 / 25 | C · timeout |
| `services/product.service.test.ts` | 2 / 10 | D |
| `pages/points-of-sale/points-of-sale.test.tsx` | 1 / 17 | C |
| `pages/sales/__tests__/sales-index.test.tsx` | 1 / 3 | E · `Found multiple elements` |
| `pages/sales/__tests__/scan.test.tsx` | 1 / 2 | E |
| `pages/users/users.test.tsx` | 1 / 12 | C |
| `services/auth.service.test.ts` | 1 / 8 | E |
| `services/payment-method.service.test.ts` | 1 / 11 | E |

### Las cinco causas raíz

**A · La página se renderiza sin su proveedor de contexto.** La más numerosa: alrededor de un tercio del rojo. Renderizar un componente de página arrastra todos los contextos que consume, y si falta uno el hook lanza. `new.test.tsx` falla **entero** por `useCart`, y `products/edit.test.tsx` **entero** por `useAuth`. No es un fallo de la aplicación: es que el test monta el componente desnudo.

*Cómo se escribe bien:* envolver en el proveedor real, o mockear el hook. [`pages/sales/__tests__/cart.test.tsx`](../frontend/src/pages/sales/__tests__/cart.test.tsx) —que está en verde— es el fichero a copiar: mockea `@/providers/cart-provider` con un objeto de estado que el test controla.

**B · El mock global de TensorFlow.js se quedó corto.** `src/test/setup.ts` mockea `@tensorflow/tfjs` con `createTensorFlowMock()`, y ese doble no exporta todo lo que el código bajo prueba usa: `No "memory" export is defined on the "@tensorflow/tfjs" mock`. Afecta a los dos ficheros de aprendizaje automático.

**C · Timeouts de 10 s.** 27 ocurrencias, y en su mayoría **consecuencia** de A y B: cuando el render lanza, el `waitFor` que lo sigue espera algo que nunca va a aparecer y agota el reloj. Perseguir el timeout suele ser perseguir el síntoma.

**D · `vi.mock` sin factoría deja los miembros en `undefined`.** `vi.mock('@/services/product.service')` sin segundo argumento produce un módulo cuyos miembros son `undefined`, y el test revienta con `Cannot read properties of undefined (reading 'getProduct')`. Hay que pasar la factoría, o usar `vi.mocked(...)` sobre un mock automático que sí exista.

**E · Aserciones que la interfaz dejó atrás.** `Unable to find an element with the text …`, `Found multiple elements …`, `toBeDisabled()` sobre un elemento que ya no lo está. Son textos y roles que cambiaron sin que nadie actualizara el test.

### La trampa que no da error: MSW en modo aviso

[`src/test/setup.ts`](../frontend/src/test/setup.ts) arranca el servidor así:

```ts
server.listen({ onUnhandledRequest: 'warn' });
```

Una petición sin manejador **no rompe el test**: imprime un aviso y devuelve nada. Un test puede pasar entero sin haber probado absolutamente nada, y el aviso se pierde entre las 118 líneas de rojo preexistente. El comentario del propio fichero explica por qué está así —`'error'` rompería los tests unitarios que no hacen llamadas—, pero la consecuencia hay que conocerla.

*Cómo se escribe bien:* declarar los manejadores explícitamente para las rutas que el componente llama, o —lo que hace la mayoría de los tests de servicio de este repositorio— mockear el módulo del servicio con `vi.mock` y afirmar sobre `toHaveBeenCalledWith`, que es una comprobación que no puede pasar por accidente.

### `tsc --noEmit` no es una puerta

Devuelve decenas de errores preexistentes en los ficheros de plantilla de Metronic: `lucide-react` sin exportar `ShieldUser`, `VectorSquare` o `PanelTopBottomDashed`, módulos ausentes (`@/components/image-input`, `embla-carousel-react`), y tipos rotos en `chart.tsx` y `data-grid-table.tsx`. Filtra su salida a tus propios ficheros antes de sacar conclusiones.

**Pero no lo sustituyas por `npm run build`, porque `npm run build` no comprueba tipos.** *(Corregido el 2026-09-26, al verificar C40_FIX: este párrafo decía que la puerta real era `npm run build`, y es falso.)* Vite transpila con **esbuild**, que descarta las anotaciones de tipo **sin mirarlas**, así que el build sale verde sobre un error de tipos y `vitest` tampoco lo ve. Medido sobre el mismo árbol: `npm run build` **sale 0** en 27,7 s mientras `tsc --noEmit` **sale 2** con 176 errores. C40 se comió un commit entero por esto —un DTO anulable en .NET y todavía `number` en `ai-search.types.ts`, con tests y build en verde— y **el `tsc --noEmit` filtrado fue lo único que lo encontró**.

La lectura correcta es que **ninguno de los dos es una puerta por sí solo** y miden cosas distintas: `npm run build` dice «compila y empaqueta», `tsc --noEmit` filtrado a tus ficheros dice «los tipos cuadran». Para cualquier cambio que mueva un tipo —un DTO, una firma de servicio, un campo anulable— hay que correr los dos.

---

## 🔗 Recursos Externos

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library Cheatsheet](https://testing-library.com/docs/react-testing-library/cheatsheet/)
- [MSW Documentation](https://mswjs.io/docs/)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Testing Library - Which Query](https://testing-library.com/docs/queries/about#priority)
- [Kent C. Dodds - Testing JavaScript](https://testingjavascript.com/)

---

## 🎯 Conclusión

Esta combinación de herramientas ofrece:

- ✅ **Velocidad**: Vitest aprovecha Vite para tests ultra-rápidos
- ✅ **Confiabilidad**: Tests basados en comportamiento del usuario real
- ✅ **Multi-navegador**: Playwright testea en Chromium, Firefox y WebKit
- ✅ **Integración**: Compatible con GitHub Actions y free-tier
- ✅ **DX**: Excelente experiencia de desarrollo con hot reload y UI interactiva
- ✅ **Accesibilidad**: Testing Library promueve queries accesibles por defecto
