# C42 — guion de la comprobación manual (tarea 12.1)

> **Por qué existe este documento y no basta con los tests.** La definición de hecho de C42 llama a
> esta comprobación *«la única puerta capaz de cazar la clase de defecto que C40 dejó pasar con 136
> escenarios en verde»*. Aquel defecto fue un ámbito construido entero —tercera clase de scope,
> tercer perfil de claims, autorización abierta a los dos roles, cantidades anulables— **al que no
> había forma de llegar desde la pantalla**: cada pieza estaba probada y el camino no existía. Ningún
> test de unidad ni de integración lo ve, porque cada uno entra por donde el camino sí existe.
>
> Y este change nace de exactamente eso: dar superficie a algo que nadie había visto funcionar.
>
> **Escrito para:** quien recorra la comprobación a mano, con el entorno ya levantado.

---

## 0 · El entorno, y cómo comprobar que está de verdad listo

| Pieza | Dónde | Cómo se comprueba |
|---|---|---|
| Frontend | <http://localhost:3001> | Carga la pantalla de login |
| API .NET | <http://localhost:5056> | `curl -s -o /dev/null -w "%{http_code}" http://localhost:5056/api/ai/search/availability` → **401** |
| `jbg-ai` | <http://localhost:8001/health> | `projection.status` = `"ok"` y `projection.stale` = `false` |

**Arrancado con los cuatro interruptores de IA encendidos por defecto**, que es lo que hace visible
la tarjeta del agente:

```bash
# desde backend/src/JoiabagurPV.API
ASPNETCORE_ENVIRONMENT=Development ASPNETCORE_URLS=http://localhost:5056 \
  AiAgentAssist__EnabledByDefault=true \
  AiFreeQuerySearch__EnabledByDefault=true \
  AiSalesAssist__EnabledByDefault=true \
  AiSearch__EnabledByDefault=true \
  dotnet run --no-launch-profile
```

> **`AiAgentAssist:EnabledByDefault` es `false` en el código, y es deliberado.** El agente cuesta
> varias veces la ruta determinista y retira su argumentario seis veces más, así que encender una
> tienda es un acto explícito. Para esta comprobación se enciende por defecto; **en un despliegue se
> enciende tienda por tienda con `AiAgentAssist:EnabledPointOfSaleIds`.**

### La precondición que el arnés necesita y la pantalla también

El drenaje programado de C41 vive en el ciclo de vida de `jbg-ai` y **necesita la API .NET sirviendo
el *index feed* en `:5056`**. Sin ella el arranque registra `feed_not_configured` y la proyección
queda rancia, con lo que el prefiltro de disponibilidad **deja de aplicarse** y el pivote a
sustitutos no se puede observar. Comprobado antes de empezar:

```bash
curl -s http://localhost:8001/health | python -m json.tool | grep -A6 projection
docker logs jpv-pv-jbg-ai 2>&1 | grep pos_sync | tail -3   # debe decir «drained pages=...»
```

---

## 1 · Los dos usuarios

| Usuario | Rol | Tienda | Contraseña | Para qué |
|---|---|---|---|---|
| `op-aeroport` | Operator | Aeroport de Menorca | *(la que le pusiste)* | El recorrido normal. **Es la tienda con surtido y proyección**, la misma que mide el arnés |
| `admin` | Administrator | *(ninguna)* | `Admin123!` **verificada** | El ámbito «todas las tiendas», que **sólo se le ofrece a él** |

> **La del administrador está comprobada contra la API levantada** (`login: 200`) y es la que siembra
> `DatabaseSeeder`. **La de los operarios no la sé**: `op-aeroport`, `op-ciutadella` y `op-fornells` los
> creaste en sesiones anteriores, no los siembra el *seeder*, y `Test123!` —que es la del molde de
> tests— **da 401** contra este entorno. Si no la recuerdas, lo más rápido es crear un operario nuevo
> desde el panel de usuarios con el `admin` y asignarlo a *Aeroport de Menorca*.

### La sonda, ya comprobada extremo a extremo

Antes de que empieces, el cable que la tarjeta lee está verificado con la API real y **sin gastar
cuota ni llamar al proveedor**:

```bash
curl -s -b "$COOKIES" http://localhost:5056/api/ai/search/availability
# {"pointOfSaleId":null,"semanticSearchAvailable":true,"assistedAnswerAvailable":true,
#  "assistedAnswerUnavailableReason":null,"agentAvailable":true,"agentUnavailableReason":null}
```

`agentAvailable` y `agentUnavailableReason` llegan como valores propios, así que el estado 1 de la
puerta está confirmado antes de abrir el navegador. Lo que queda por ver a mano son los estados 2 y 3
y los otros cuatro recorridos.

---

## 2 · Los cinco recorridos

### 2.1 · La puerta, con sus tres estados

**Ruta:** *Ventas* (`/sales`) · **Usuario:** `op-aeroport`

1. **Disponible.** Con los interruptores como arriba, la cuarta tarjeta —«Preguntar al Agente»—
   está **activa** y su botón habilitado. Pulsarla lleva a `/sales/new/agent`.
2. **No disponible.** Reinicia la API con `AiAgentAssist__EnabledByDefault=false`. La tarjeta sale
   **deshabilitada y con el motivo escrito encima** («El agente está desactivado en esta tienda»), y
   **la tarjeta entera deja de ser un enlace** — no hay forma de navegar a la ruta desde ahí.
   - **⚠ Lo que hay que mirar con cuidado:** que el motivo sea **del agente** y no el de la
     respuesta asistida. Con la asistida encendida y el agente apagado, la tarjeta del agente dice
     lo suyo y la de «Buscar con Ayuda» sigue activa. Ése es el estado que la sonda existe para
     poder reportar, porque el agente tiene cadena de credencial propia.
3. **La sonda no contesta.** Para la API mientras la pantalla de ventas está abierta y recárgala, o
   corta la red del navegador. La tarjeta se queda **activa, con el aviso** «No se pudo confirmar si
   el agente está disponible». **Fallar la sonda no cierra una puerta que quizá funciona.**

### 2.2 · Una conversación con pivote

**Ruta:** `/sales/new/agent` · **Usuario:** `op-aeroport`

1. Ámbito por defecto: **su tienda**, nunca «todas».
2. Pregunta algo que exista en catálogo: *«busco un anillo de plata para un regalo»*.
3. Espera. La cinta dice **«~5 s típico, hasta 12 s»**, que es lo medido (p50 5,3 s, p95 9,0 s, máx
   11,9 s). Mientras está en vuelo el compositor queda deshabilitado.
4. Con la respuesta:
   - La **tira de estado** dice por qué paró, cuántas vueltas y cuántas consultas.
   - **«Cómo lo ha averiguado»** se abre y enseña la escalera de pasos con los nombres de las
     herramientas, si cada una fue bien, y tokens y milisegundos por vuelta. **No debe aparecer
     ningún argumento de herramienta ni contenido de observación.**
5. **El pivote, que es lo que hay que provocar.** Pregunta por algo que la tienda no tenga —una
   pieza agotada, o insiste con *«¿y si no queda?»*. Cuando el bucle llame a `buscar_sustitutos`, el
   bloque tiene que traer **dos grupos rotulados**: «Coincidencias» primero y «Alternativas» después.
   - **⚠ Lo que hay que mirar con cuidado:** que un sustituto **nunca** salga bajo «Coincidencias».
     Ofrecer un segundo mejor haciéndolo pasar por lo que se pedía es lo que un cliente nota.
6. **El hilo.** Manda un segundo turno. El bloque anterior **colapsa a una línea con chips** («N
   piezas», «N vueltas») y el nuevo queda abierto. Pulsa la línea colapsada: se reabre, y se cierra
   el otro. **Sólo uno abierto a la vez.**
7. Si una pieza sale en dos turnos, **sale las dos veces**. No se deduplica: la evidencia de cada
   turno es la suya.

### 2.3 · Una respuesta sin piezas

**Ruta:** `/sales/new/agent` · **Usuario:** `op-aeroport`

Una de cada cinco respuestas no trae ninguna pieza (19,6 % medido), y **no son búsquedas vacías**.
Provoca las tres:

| Qué preguntar | Qué debe salir |
|---|---|
| *«¿cómo se limpia la plata?»* | Prosa y, si hay corpus, sus **Fuentes**. **Ninguna frase de vacío** |
| *«busco un regalo»* (sin eje) | Sólo **la repregunta**, y el **foco vuelve al compositor** |
| Algo de joyería que el catálogo no tenga | «El agente buscó en el catálogo y no encontró ninguna pieza que encaje», **distinguible de las dos de arriba** |

- **⚠ Lo que hay que mirar con cuidado:** que ninguna de las dos primeras diga «sin resultados» ni
  nada que suene a que el catálogo falló. La conversación está funcionando.

### 2.4 · El tope del compositor

**Ruta:** `/sales/new/agent` · **Usuario:** `op-aeroport`

1. Mira los contadores **antes de escribir nada**: `turnos 0/12 · 0/4.000 car.`
2. Manda un turno y vuelve a mirar: **`turnos 2/12`, no 1**. El argumentario del asistente viaja de
   vuelta y es la mayor parte del gasto.
3. Sigue hasta **seis intercambios**. Al llegar, el compositor **se cierra con su motivo** —«La
   conversación ha llegado a su tope de turnos»— y **la caja de texto se deshabilita con él**.
   - **⚠ Lo que hay que mirar con cuidado:** que **no se envíe ninguna petición** al llegar al tope.
     El punto entero del contador es no estrellarse contra un 422 después de haber pagado la llamada.
   - Y que el tope de caracteres, cuando salte, **mencione las respuestas del agente**: si no, el
     operario ve 4.000 habiendo escrito 200 y lee un error.

### 2.5 · El ámbito global, y lo que se pierde con él

**Ruta:** `/sales/new/agent` · **Usuario:** `admin`

1. El selector ofrece **«Todas las tiendas»**. Con `op-aeroport` **no debe aparecer**.
2. Al seleccionarlo aparece la línea: *«Con todas las tiendas el agente no puede saber si algo está
   agotado, así que **no ofrecerá alternativas** y tampoco dirá existencias.»*
   - No es estética: sin punto de venta la etiqueta de disponibilidad sólo puede decir «sin ámbito»,
     así que **el pivote no se dispara nunca**. Es una capacidad que se pierde.
3. Pregunta algo. Las filas salen **con precio y sin existencias**, diciendo «Selecciona una tienda
   para ver existencias», y **«Ver ficha de venta» queda deshabilitado**. «Seleccionar para venta»
   **sigue activo**, y es correcto: el ámbito global existe para saber *dónde* está una pieza, y el
   flujo de venta manual exige tienda propia y valida existencias allí.
4. **Cambia de ámbito con una conversación abierta.** Debe **avisar antes** y, al aceptar, **vaciar
   el hilo** y reiniciar el contador de coste. Si se declina, el hilo se queda como estaba.

---

## 3 · Lo demás que conviene mirar de paso

- **El coste de la sesión**, en la barra fija: no aparece antes de la primera pregunta, y después
  **acumula** en vez de sustituir. Sólo lo ve el administrador, porque `usage` viaja sólo para él.
- **El enlace «Panel directo»**, arriba a la derecha: lleva a `/sales/new/assisted`. La misma
  pregunta en los dos paneles es la ablación, legible a simple vista.
- **Vender desde el bloque abierto** lleva al flujo de venta de siempre con la pieza puesta, y
  registra el quinto origen. Comprobable en base:

  ```sql
  SELECT "SearchOrigin", count(*) FROM ai."ProductSearchEvents" GROUP BY 1 ORDER BY 1;
  -- 5 = AssistedAgent
  ```

- **Una conversación de ámbito global no se registra**, y es una limitación heredada y declarada:
  la columna de punto de venta del evento es obligatoria y cerrarlo abriría migración. La respuesta
  vuelve sin `searchEventId` y no se atribuye ninguna selección.

---

## 4 · Qué anotar

Para cada uno de los cinco recorridos: **pasa / no pasa**, y si no pasa, qué se vio. Lo que esta
comprobación busca no es un test que falle —esos ya están verdes— sino **un camino que no exista, un
rótulo que mienta o un estado que la pantalla no sepa decir**, que es la clase de defecto que sólo
se ve usándolo.
