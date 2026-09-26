# CLAUDE.md

Guidance for Claude Code in this repository. Full project context lives in
[openspec/project.md](openspec/project.md); functional and architectural docs in
[Documentos/](Documentos/).

## OpenSpec validation

`openspec validate` needs a target. Three forms, and only one of them is the project gate:

| Command | Scope |
|---|---|
| `openspec validate --all --strict` | **The project gate.** Every spec and every active change. Must report `0 failed` |
| `openspec validate <change-name> --strict` | One change, while it is in progress |
| `openspec validate` / `openspec validate --strict` | **Validates nothing.** Prints the alternatives and exits 1 — never read this as a pass |

Run `--all --strict` before archiving a change, not just the single-change form: a
change can be green while the live specs it syncs into are broken. That is exactly how
three malformed specs survived unnoticed until 2026-08-06.

### El validador lee sólo la PRIMERA LÍNEA FÍSICA de la descripción de un requisito

Esto cuesta una sesión la primera vez. En una delta, la descripción que sigue a
`### Requirement: …` se valida **leyendo únicamente su primera línea física**. Si editas una
spec y el `SHALL` cae en la segunda línea por un ajuste de ancho, falla con
*«must contain SHALL or MUST»* **aunque lo contenga**, y el mensaje no da ninguna pista de que
el problema es tipográfico.

Las deltas se escriben con la descripción en **una sola línea larga**, sin ajustar a 90
columnas, exactamente como están las archivadas. Los párrafos siguientes sí pueden ajustarse:
la regla sólo afecta al primero.

## Live specs vs delta specs

Delta syntax belongs **only** to a change, never to a live spec:

- `openspec/changes/<name>/specs/<capability>/spec.md` — uses `## ADDED Requirements`,
  `## MODIFIED Requirements`, `## REMOVED Requirements`, `## RENAMED Requirements`
- `openspec/specs/<capability>/spec.md` — must start with `# <capability> Specification`,
  then `## Purpose`, then `## Requirements`, then the `### Requirement:` blocks

A live spec containing `## ADDED Requirements` is a broken sync, not a style choice: it
means delta files were copied verbatim into `openspec/specs/` instead of being merged.
`--all --strict` catches it via the missing `## Purpose` section.

## Las tres suites no se pueden medir en paralelo, y el fallo no se parece a lo que es

**Medido el 2026-09-26 al abrir C42.** Lanzar `dotnet test`, `npm run test` y `uv run pytest` a la vez
sobre el mismo commit da **490 rojos de 1.347 en el backend** donde en serie da **53**. No es
regresión, no es orden, y no lo tapa ninguna de las reglas de abajo:

```text
System.TimeoutException : The operation has timed out.
   at System.IO.Pipes.NamedPipeClientStream.ConnectInternal(...)
   at Docker.DotNet.DockerClient...
```

`vitest` con 14 *workers* satura la máquina y **testcontainers deja de alcanzar el demonio de Docker
por su tubería con nombre**, así que **todos** los `IntegrationTests` mueren al arrancar. En la misma
pasada `pytest` da 2 rojos —sus dos tests de reloj del agente— que **solos pasan**.

**Es peor que el `dotnet test` desde la raíz y que el `.exe` vivo, porque sí ejecuta tests y sí
imprime una línea de resumen**: la línea dice 490 y es verdad, sólo que no está midiendo tu código.
Leer el resumen no basta aquí.

| | |
|---|---|
| Una pasada de las tres suites | **serial**, ~20 min en total |
| Si el backend da cientos de rojos en `IntegrationTests` | mira si había algo más corriendo antes de mirar tu diff |

## Backend test suite: a red count is not a regression signal

`dotnet test` on this repository comes back with **dozens of failures that were already
there**. They are not yours. Never conclude you broke something from the count alone, and
never spend a session "fixing" them without being asked — but never wave them away either:

| Step | Command |
|---|---|
| Measure the baseline first | `git stash push -u`, run the suite, `git stash pop` (on a clean tree, measure HEAD directly) |
| Compare | your change is clean if the failing **test names** fall in the same set, not if the number matches |

The number alone is unreliable: a handful of these failures are genuinely order-dependent, so
two runs of identical code disagree. Compare names — **but do not expect the name set to be
identical either.** Measured on 2026-09-24 over `93115cf`, two full runs of the *same commit*
without recompiling gave 50 and 51 failures and **fifteen differing names** — 8 appearing, 7
vanishing, 43 stable. Earlier measurements put it at thirteen, and a rerun of the rotating classes
over the *same binary* with `--no-build` at ten. The churn is always confined to the same classes —
`InventoryIntegrationTests`, `PaymentMethodsControllerTests`, `ReturnsControllerTests`; on that
2026-09-24 run all fifteen were in the first two — so the test that actually means something is:
**do the differing names fall inside those known-unstable classes, and is your change's own area
clean?** A new red name in a class you touched is a regression; a new red name in
`InventoryIntegrationTests` is Tuesday.

And measure the summary line, not the exit code: if something holds `bin/Debug` locked — a
`JoiabagurPV.API.exe` you left running will — the build fails, **zero tests run, and `dotnet test`
still exits 0**. Same trap as `vitest` piped, opposite cause.

Two of those failures are traps you will fall into yourself the first time you write a test
here, because they look like application bugs and are not:

- **"Expected 401 but found 200/403/201".** The shared `HttpClient` a test class uses to log in
  keeps the cookies of every login it performed, so it is not anonymous. Ask the factory for a
  fresh client to assert an unauthenticated call.
- **`22001: value too long for type character varying(20)`.** The object mothers generate data
  with Bogus, and a generated phone number does not always fit `PointOfSale.Phone`. Pin the
  field explicitly (`.WithPhone("600123456")`) instead of leaving it to chance.

The full inventory — root causes, and why a tree of 270 tests went unrun for weeks — is under
*Estado de la suite: fallos conocidos* in [Documentos/testing-backend.md](Documentos/testing-backend.md).

## Frontend test suite: same story, and it catches people out harder

`npm run test` in `frontend/` **also comes back red before you touch anything**: measured on
2026-09-24 at the head of C40, **113 failures of 729 tests, across 14 of the 54 files** (113 or 114
of 597 across 14 or 15 of 48 on 2026-09-22, which is the figure this file used to quote — it was
C36's *opening* baseline and the tree has since moved to C36's close; 113 of 595 on 2026-09-13;
118 of 482 on 2026-08-29 — the suite grew and the red did not). The method is identical to the
backend's — baseline first, then compare the failing **test names**, never the count.

**Expect the count to sit at 113 or 114 without anybody having broken anything.** The frontend was
documented as having a set of names stable between runs, and C36 refuted that: `family-review.test.tsx
:: should create a family with its members from the review screen` **failed at baseline and passed at
close** with nothing touching it or its production code. Verifying C36 re-ran that same baseline
commit and the test **passed there too**, giving 113 in 14 files where the apply had seen 114 in 15:
same commit, same code, two answers.

**It is not one test.** C40 measured two full runs of the *same* commit, minutes apart, at 113 and
114 — and the differing name was a third file again: `scan.test.tsx :: ScanningPage should show
manual SKU input fallback after initialization`, which had never failed in any of the seven earlier
passes of that change and **passes when the file is run on its own**. Its neighbour in the same
file, `should render loading state initially`, is red at baseline and stays red. So the rotating set
is at least `family-review.test.tsx`, `assist.test.tsx` and `scan.test.tsx`, and the useful question
is the backend's: **does the differing name sit in a file that was already red, and is your own area
clean?** A new red name in a file you touched is a regression; one more red name in `scan.test.tsx`
is noise. The one thing that holds either way: **zero new names in your own area**.

It catches people out harder than the backend one for two reasons. Nobody expects a frontend
suite to be red, and `vitest` exits **0** when you pipe it (`npm run test | tail` reports the
exit code of `tail`), so a green shell prompt says nothing at all. Read the summary line.

Three traps, all of which look like your bug and are not:

- **`useCart must be used within a CartProvider`** (and `useAuth` / `AuthProvider`). Rendering a
  page component drags in whatever context it consumes. This alone accounts for roughly a third
  of the red: `pages/sales/__tests__/new.test.tsx` fails **11 of 11** and
  `pages/products/edit.test.tsx` **27 of 27**, for nothing but this. Wrap in the provider, or
  mock the hook — `pages/sales/__tests__/cart.test.tsx` is the file to copy.
- **MSW does not fail an unhandled request.** `src/test/setup.ts` starts the server with
  `onUnhandledRequest: 'warn'`, so a call with no handler prints a warning and returns nothing.
  A test can pass having asserted nothing at all. Declare handlers explicitly, or mock the
  service module with `vi.mock` — which is what the service tests here already do.
- **`tsc --noEmit` is not a gate — and `npm run build` is not enough on its own.** `tsc` reports
  dozens of pre-existing errors in the Metronic template files (`lucide-react` missing exports,
  absent modules, `chart.tsx`), so filter its output to your own files. But do run it: **Vite
  transpiles with esbuild, which strips types without checking them**, so `npm run build` is green
  over a type error and `vitest` never sees one either. C40 shipped a whole commit with a DTO
  nullable on the .NET side and still `number` in `ai-search.types.ts`: tests green, build green,
  and the filtered `tsc --noEmit` was the only thing that found it. Green on `npm run build` means
  "it compiles", not "the types match" — so for any change that moves a type, run both.

The full inventory — the five root causes and which files each one accounts for — is under
*Estado de la suite: fallos conocidos* in [Documentos/testing-frontend.md](Documentos/testing-frontend.md).

## ai-service (jbg-ai)

- `uv sync` and `uv run` need `--system-certs` on this machine, otherwise PyPI fails with
  `invalid peer certificate: UnknownIssuer`.
- **`--system-certs` arregla a `uv`, no al proceso Python.** En tiempo de ejecución `litellm`
  sale por `aiohttp`/`httpx`, que usan el bundle de `certifi` y **no** el almacén de Windows, y
  esta máquina tiene un MITM de **Norton Web/Mail Shield** cuya raíz vive sólo en ese almacén.
  Cualquier llamada real al proveedor —un spike, una pasada de `evals`, un `sync` de índice—
  muere con `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`. La salida:
  exportar el almacén a un PEM y apuntar `SSL_CERT_FILE` (y `REQUESTS_CA_BUNDLE`) a él.
  `ssl.enum_certificates('ROOT'|'CA')` concatenado al `certifi.where()` basta. **Filtrar por la
  bandera de confianza no basta**: la raíz de Norton no la lleva y el bundle sale incompleto.
  **No afecta a ningún test** — ninguno llama al proveedor. **Tampoco afecta a los contenedores**:
  desde Docker el TLS del proveedor y de PyPI se verifica con el bundle del sistema y lo firma la CA
  real (comprobado en C34, §2.8 de su informe), así que medir con `jbg-ai` en Compose no necesita PEM.
- **Windows: `psycopg` rechaza el `ProactorEventLoop`**, que es el que Python instala por
  defecto. Cualquier script suelto que abra el motor asíncrono necesita
  `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())`. En los tests eso ya
  lo resuelve `support/async_db.run_db`, que además dispone el motor a ambos lados: el motor es
  de proceso y sus conexiones pertenecen al bucle que las abrió, así que **dos `asyncio.run` en
  un mismo test fallan con `InterfaceError`**. Un escenario, un bucle.
- `ai-service/openapi.json` is a frozen contract with the .NET side. If
  `test_openapi_snapshot_is_stable` fails, the boundary moved — agree the change with
  whoever owns the .NET client before regenerating it with the README one-liner.

## Escribir ficheros largos: el heredoc no sirve, y el error miente

Este repositorio escribe documentos largos constantemente —historias de 400 líneas, tickets de 550,
fichas del plan— y **el heredoc de Bash no puede con ellos**. Escribir

```bash
cat > Documentos/Historias/AI-Eng/HU-AIENG-041.md <<'EOF'
...37 KB de markdown...
EOF
```

falla con:

```text
ENAMETOOLONG: name too long, uv_spawn
```

**El mensaje es engañoso y es la mitad de la trampa.** Habla de un *nombre* demasiado largo y nombra
`uv_spawn`, así que se lee como un problema de ruta —que en Windows tiene un límite real de 260
caracteres— o como algo del entorno de `uv`. No es ninguna de las dos cosas: **el cuerpo entero del
heredoc viaja en la línea de comandos del proceso que se lanza**, y Windows la corta en **32 767
caracteres** (`CreateProcess`). El documento que disparó esto medía **37,5 KB**; el ticket de al lado,
**38,2 KB**. El límite no es del fichero ni de la ruta: es de cuánto texto cabe en la invocación.

| Qué escribir | Con qué |
|---|---|
| Un documento entero (historia, ticket, informe, spec) | **La herramienta de escritura de ficheros.** Siempre, sin estimar el tamaño primero |
| Un retoque dentro de un documento existente | La herramienta de edición, contra una cadena única |
| Un fragmento corto: `.env`, un YAML de pocas líneas, un script de usar y tirar | Heredoc, sin problema |

**La regla práctica: si el contenido no cabe cómodamente en pantalla, no cabe en un heredoc.** No
merece la pena calcular bytes — el modo de fallo es un error que no dice lo que pasa, y el intento
fallido se paga entero porque hay que reescribir el documento completo en la segunda llamada.

**Y no se arregla troceándolo.** Encadenar `cat >>` en varias llamadas funciona, pero deja el fichero
a medias si una falla, mezcla el contenido con el escapado del shell (`` ` ``, `$`, `\`) y hace que
cualquier revisión posterior tenga que reconstruir mentalmente el documento a partir de N comandos.
Una sola escritura, con la herramienta que existe para eso.
