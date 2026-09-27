# C39a-bis · Verificación del entorno de demostración redesplegado

**Change:** `verify-demo-redeployment` · **Rama:** `c39abis-verify-demo-redeployment` · **Medido:**
2026-09-27, entre las 13:30 y las 14:15 UTC · **Entorno:** cuenta `666823181744`, `eu-west-1`,
instancia `i-095f0ba16e2bb8278`, URL `https://52-49-209-14.sslip.io`

Este informe registra **lo que se midió**, no lo que se esperaba. Cada afirmación lleva su medición al
lado o se declara explícitamente como no medida. Donde una predicción de C39a se ha cumplido se dice; y
donde una premisa de los propios artefactos de este change resultó **falsa**, se dice también y se
explica qué se hizo.

**Resumen en cuatro líneas.** El despliegue ocurrió de verdad y el entorno está sano. La ejecución
figura en **rojo** por una sola condición de verificación que **juzga mal un entorno correcto**, y ése
es el hallazgo principal. La predicción de C39a sobre la proyección se **confirma**, con dos matices
que conviene no tapar. Y la premisa sobre las cuentas de demostración era **falsa**: no existían.

---

## 1 · El despliegue ocurrió, no sólo el *push*

### 1.1 La ejecución existe, publicó las dos imágenes, y falló después *(tarea 1.1)*

| | |
|---|---|
| Ejecución | **36322635852**, `Deploy demo environment` |
| Disparo | `push` sobre `demo`, «Merge pull request #47 from skydr4g0n-it/ai-eng» |
| Commit | `2b357a1e1f459904a4e02e43defeefe0596a24cb` |
| Reloj | `2026-09-27T13:30:31Z` → `13:33:15Z` (2 m 44 s) |
| Conclusión | **`failure`** |

**Y el `failure` no significa que no se desplegara**, que es exactamente la distinción que esta tarea
existe para hacer. De los trece pasos, **los doce primeros pasaron** y sólo el decimotercero falló:

```text
 6. Build and push the API image          — success
 7. Build and push the AI service image   — success
 8. Record the deployed tag               — success
 9. Discover the demo host                — success
10. Verify the host is registered with SSM — success
11. Deploy                                — success
12. Wait for the deployment               — success
13. Verify the deployment from inside the host — FAILURE
```

Las dos imágenes se construyeron y se publicaron, el tag se registró, el despliegue corrió y se esperó
a que terminara. **Lo único que falló fue el juicio posterior sobre el resultado**, y el §2.2 muestra
que ese juicio es incorrecto.

### 1.2 El `IMAGE_TAG` cambió, y el historial lo prueba *(tarea 1.2)*

Ésta es la comprobación que no se puede simular, y aquí no hay que conformarse con dos lecturas: el
parámetro guarda su historial completo.

```text
versión 8   sha-d6a740fa5e0b678eef32893f92c9a3a36bec7f8d   2026-09-22T19:53:34+02:00
versión 9   sha-2b357a1e1f459904a4e02e43defeefe0596a24cb   2026-09-27T15:32:21+02:00
```

Y el otro lado:

```text
git rev-parse origin/demo  ->  2b357a1e1f459904a4e02e43defeefe0596a24cb
```

**Coincidencia exacta.** La versión 8 es la que C39a registró; la 9 se escribió a las **13:32:21 UTC**,
un minuto antes de que el paso de verificación corriera. El tag se movió, luego se desplegó.

### 1.3 Las tres credenciales de generación son propias *(tarea 1.3)*

Del arranque de `jbg-demo-ai`, literal, sin ningún valor de clave:

```text
13:32:59,485 INFO jbg_ai.api.routers.assist stage=agent_client  model=openai/gpt-4o      timeout_s=8.0 credential=agent
13:32:59,485 INFO jbg_ai.api.routers.assist stage=router_client model=openai/gpt-4o      timeout_s=2.0 credential=router
13:32:59,485 INFO jbg_ai.api.routers.assist stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist
```

**Las tres con credencial propia y ninguna con `assist_fallback`**, que es lo que el despliegue de C34
registró y el motivo por el que C39a creó los dos parámetros. Los parámetros existen y sus fechas lo
confirman: `AGENT_LLM_API_KEY` y `ROUTER_LLM_API_KEY` escritos el 2026-09-27 a las 11:05 UTC — durante
C39a—, y `ASSIST_LLM_API_KEY` del 22 de septiembre.

### 1.4 Los contenedores llevan el tag nuevo y la base no se recreó *(tarea 1.4)*

```text
jbg-demo-api      .../jbg-demo-api:sha-2b357a1e…    Up 19 minutes (healthy)   8080/tcp
jbg-demo-ai       .../jbg-demo-ai:sha-2b357a1e…     Up 19 minutes (healthy)   8000/tcp
jbg-demo-proxy    caddy:2.10.0-alpine               Up 19 minutes             0.0.0.0:80->80, 0.0.0.0:443->443
jbg-demo-postgres pgvector/pgvector:pg15            Up 4 weeks (healthy)      5432/tcp
```

**Los dos contenedores de aplicación llevan 19 minutos; el de base de datos, cuatro semanas.** Ésa es
la firma de un redespliegue que respetó los volúmenes, y no de una reinstalación — y es también la
razón por la que el corpus de conocimiento siguió en su sitio (§2.3).

---

## 2 · Las siete condiciones sobre el entorno real

### 2.1 Seis en verde, una en rojo, y la categoría de la que falla *(tarea 2.1)*

`verify.sh` se volvió a ejecutar **tal cual está desplegado** (`/opt/jbg-demo/deploy/demo/verify.sh`),
desde dentro del anfitrión, a las ~13:58 UTC. Salió **1**. Ésta es la clasificación que la tarea pide:

| # | Condición | Veredicto | Categoría |
|---|---|---|---|
| 1 | Documentos indexados > 0 | ✅ **1200** | — |
| 2 | Modelo configurado = modelo indexado | ✅ `openai/text-embedding-3-small` en ambos | — |
| 3 | Base alcanzable | ✅ `database: ok` | — |
| 4 | Credencial de *embeddings* configurada | ✅ `provider: configured` | — |
| 5 | Ningún punto de venta sin surtido | ❌ **falla** | **(b) demasiado estricta** |
| 6 | Corpus de conocimiento no vacío | ✅ **161** fragmentos | — |
| 7 | La ruta del agente responde | ✅ respondió 200 | — |

**La quinta es la única que falla, y no falla por el estado del entorno.** Categoría **(b)**: el
entorno está sano y la condición lo juzga mal. El §2.2 lo demuestra con el experimento. **Ninguna
condición cae en la categoría (a)**, así que el entorno **sí** se puede mostrar — y el hecho de que el
despliegue figure en rojo es un defecto de la comprobación, no del entorno.

**Un detalle del formato que conviene saber:** `verify.sh` acumula los fallos y sale **antes** de
imprimir las líneas `[verify] OK`. Así que un despliegue fallido dice qué falló pero **no dice qué
pasó**: las cifras del corpus y del agente no aparecen en el registro. De ahí que las de la tabla de
arriba se hayan leído del informe de salud y de la base, y no del log del despliegue.

### 2.2 El falso positivo de la quinta condición, con su experimento *(tarea 2.6)*

**Es el hallazgo del change.** El mensaje es:

```text
[verify] FAILED:
  - 1 point(s) of sale hold no assigned row in the projection; assisted search answers 503 for each of them
```

**Los doce puntos de venta, leídos de la base desplegada, con el `IsActive` de .NET al lado:**

| `Code` | Nombre | `IsActive` | Filas | Asignadas |
|---|---|---|---|---|
| `HT-ARTRUTX` | Hotel Cap d'Artrutx | **`f`** | 144 | **0** |
| `FORNELLS` | Fornells | `t` | 264 | 241 |
| `PORT-MAO` | Estació Marítima, Maó | `t` | 432 | 404 |
| `MAO-AIR` | Aeroport de Menorca | `t` | 456 | 416 |
| `HT-ALCUDIA` | Hotel Alcúdia | `t` | 456 | 422 |
| `HT-SONBOU` | Hotel Son Bou | `t` | 480 | 434 |
| `EIV-MARINA` | Eivissa Marina | `t` | 480 | 441 |
| `BINIBECA` | Boutique Binibeca | `t` | 504 | 457 |
| `HT-GALDANA` | Hotel Cala Galdana | `t` | 504 | 469 |
| `PALMA-JAIME3` | Palma Jaume III | `t` | 888 | 813 |
| `CIU-CENTRE` | Ciutadella Centre | `t` | 936 | 871 |
| `MAO-TALLER` | Taller Joia Bagur, Maó | `t` | 1176 | 1082 |

**Los once activos tienen surtido, de 241 a 1.082 filas asignadas.** El único sin surtido es
`cd9bfd1f-f1b2-4795-9d14-867a75c18f90` = `HT-ARTRUTX`, y es **el único inactivo de los doce**.

**No es un accidente: está declarado así desde C10.** En `data/world/pos-profiles.yaml`:

```yaml
  - code: HT-ARTRUTX
    name: Hotel Cap d'Artrutx
    is_active: false
    operator: null
    closed_after: 2025-09-30
```

**Y un matiz que refina el enunciado del propio hallazgo:** no es que `HT-ARTRUTX` *no tenga* filas.
Tiene **144**, y **todas con la asignación retirada** (`is_assigned_hint = false`), que es exactamente
lo que debe pasarle al surtido de una tienda que cerró. El *feed* hizo su trabajo bien.

**El mecanismo.** `ai-service/src/jbg_ai/api/health_report.py` publica

```sql
SELECT count(DISTINCT pos_id) AS points_of_sale,
       count(DISTINCT pos_id) FILTER (WHERE is_assigned_hint) AS scoped
FROM ai.pos_projection
```

y `shops_without_scope` es la diferencia. **No hay ninguna noción de actividad de la tienda**, así que
una tienda cerrada a propósito es indistinguible de una tienda rota.

**El experimento, contra la base desplegada:**

```text
sin filtro de actividad   points_of_sale=12  scoped=11  shops_without_scope=1   -> FALLA
con filtro de actividad   points_of_sale=11  scoped=11  shops_without_scope=0   -> PASA
```

**Y dónde puede vivir el arreglo, comprobado y no supuesto.** Esto es lo que el change aporta sobre lo
que ya se sabía:

```text
current_user = jbg_ai
NOT READABLE | public.PointOfSales | InsufficientPrivilege: permission denied for table PointOfSales
```

El rol del servicio de IA **no puede leer la tabla de puntos de venta de .NET**. Así que la decisión
D9 / Q-5 de C41 —contar contra lo que aparece en la proyección porque Python no lee `public`— **está
impuesta por los permisos y no era sólo una preferencia de diseño**, y ni `health_report.py` ni el
bloque de `verify.sh` que corre dentro de `jbg-demo-ai` pueden arreglarlo por sí solos.

**No se arregla aquí** — es código. Queda en `openspec/DEFERRED_TASKS.md` con las tres vías y su coste;
la barata es hacer la comprobación desde el anfitrión contra el contenedor de base de datos como
superusuario, que es donde `verify.sh` ya corre y no exige reconstruir ninguna imagen.

**Y una nota sobre C41, porque le toca de lleno.** El `qa.md` de C41 ya había visto
`shops_without_scope: 1` sobre este mismo punto de venta y escribió que **«fallaría el despliegue, que
es lo correcto»**. Esa valoración es la que este change refuta: el número era correcto y el juicio no.

### 2.3 El corpus de conocimiento *(tarea 2.3)*

```text
knowledge_chunk = 161
```

**Exactamente los 161 que C39a midió.** Ni menos —que habría sido hallazgo— ni más. Sobrevivió porque
vive en `jbg-demo-pgdata` y el redespliegue no toca volúmenes, lo que la línea «Up 4 weeks» del §1.4
confirma por otro camino. Y el corpus **no está sólo presente sino en uso**: la ficha de venta del §3.2
llegó citando `material-laton#cuidados-y-limpieza-en-casa`.

### 2.4 La predicción de la proyección: CONFIRMADA, con dos matices *(tarea 2.4)*

C39a predijo que el drenaje de C41 curaría la rancidez al arrancar. **Se cumple.**

| Momento | `status` | `synced_at` | `age_seconds` | `stale` |
|---|---|---|---|---|
| 13:33:11 *(la del despliegue)* | `stale` | 2026-09-22T18:22:29 | **414 629,4** | `true` |
| 13:52:40 | `ok` | 2026-09-27T13:43:05 | 570,6 | `false` |
| 13:58 *(re-ejecución de `verify.sh`)* | `ok` | 2026-09-27T13:53:06 | 274,3 | `false` |

414 629 s contra un techo de 3 600 s son **~115 veces** el techo —C39a lo estimó en ~120, y la cifra
exacta es ésta—, con **cero páginas fallidas** en la proyección. Hoy está curada y el planificador
drena cada 600 s: `13:33:05`, `13:43:05`, `13:53:06`.

**Matiz primero: la cura es del drenaje incremental, no del completo.**
`last_full_sync_at` para `pos-availability` **sigue** en `2026-09-22T18:22:29`. La predicción hablaba
del drenaje «en su forma completa cuando no hay *checkpoint*»; había *checkpoint*, así que corrió el
incremental. El resultado es el mismo y el mecanismo no.

**Matiz segundo: la lectura que el despliegue registró ya era falsa al imprimirse.** El drenaje
comprometió el *checkpoint* a las `13:33:05.85` y `verify.sh` leyó a las `13:33:11` — **seis segundos
después** — y aun así vio la marca del 22 de septiembre. La causa son dos cosas sumadas:
`cached_health_report` reutiliza el informe **10 s** (`HEALTH_CACHE_TTL_SECONDS = 10`), y el drenaje de
arranque necesitó **dos intentos**:

```text
13:32:55,164  stage=pos_sync_scheduler started interval_seconds=600 ceiling_seconds=3600
13:32:55,164  boot_drain attempt=1
13:32:55,867  WARNING feed_not_configured error=POS feed is unavailable
13:33:04,709  boot_drain attempt=2
13:33:05,850  stage=pos_sync done pages=1 upserted=1 soft_deleted=0 failed_pages=0
```

El primer intento salió cuando el lado .NET todavía no servía el *feed*. **No hizo fallar nada** —la
rancidez no es ninguna de las siete condiciones— pero deja en el registro permanente del despliegue una
cifra de 115 veces el techo que era falsa. Anotado como tarea diferida.

### 2.5 Desde internet: TLS y puertos *(tarea 2.5)*

```text
https://52-49-209-14.sslip.io/api/health   http=200  tls_verify=0  time=0.19s
https://52-49-209-14.sslip.io/            http=200  tls_verify=0
http://52-49-209-14.sslip.io/             http=308 -> https://52-49-209-14.sslip.io/
```

**Y el emisor se leyó desde el anfitrión, porque desde esta máquina la respuesta es falsa.** Medido en
local, el certificado aparece emitido por `Norton Web/Mail Shield Root`: el MITM que `CLAUDE.md`
documenta, que sustituye la cadena, de modo que un `ssl_verify_result=0` **acredita la raíz de Norton y
no la del emisor real**. Desde dentro del anfitrión, sin Norton en el camino:

```text
subject = CN=52-49-209-14.sslip.io
issuer  = C=US, O=Let's Encrypt, CN=YE1
notBefore = Aug 30 11:12:23 2026 GMT     notAfter = Nov 28 11:12:22 2026 GMT
```

**Certificado real de Let's Encrypt, válido hasta el 2026-11-28.** Margen sobrado para la entrega.

**Sólo el proxy publica puertos**, y el grupo de seguridad lo refuerza:

```text
jbg-demo-proxy      0.0.0.0:80->80, 0.0.0.0:443->443
jbg-demo-api        8080/tcp     (sin publicar)
jbg-demo-ai         8000/tcp     (sin publicar)
jbg-demo-postgres   5432/tcp     (sin publicar)

sg-05a5cbf44a44ccefb  ingress: tcp/80 0.0.0.0/0 · tcp/443 0.0.0.0/0   — y nada más
```

`sshd` escucha en `0.0.0.0:22` dentro del anfitrión, pero **no es alcanzable**: el grupo de seguridad
no lo abre y una conexión desde fuera queda filtrada. El acceso es por SSM, como C17 diseñó.

---

## 3 · El recorrido del evaluador

> **Limitación de método, declarada y no disimulada.** Esta sesión **no tiene navegador**, así que **no
> hay capturas de pantalla**. El recorrido ejercita por HTTPS público los mismos *endpoints* que llaman
> las pantallas, lo que acredita el camino de extremo a extremo —enrutador, recuperación, generación,
> citas, relojes— pero **no** que la pantalla los pinte. **La comprobación visual queda pendiente**, y
> las cuatro tarjetas del centro de IA no se han visto.

### 3.1 La cuenta administradora, y lo que el §5.3 hizo con ella *(tarea 3.1)*

**`admin` / `Admin123!` responde `401`, y es lo correcto.** La cuenta **no fue eliminada**:

```text
Id 77cef302-e097-4a21-a5d8-9edea0483485 · admin · Administrator · IsActive = f
```

El §5.3 del *runbook* la deja **desactivada a propósito**, porque el sembrador de la aplicación la
recrea en cada arranque con una contraseña que es una constante de un repositorio público, y
`LoginAsync` rechaza a un usuario desactivado aun con la contraseña correcta. **Un `401` aquí es el
sistema funcionando**, no un defecto, y responde exactamente lo que la tarea preguntaba.

**La tarjeta de salud de la IA queda SIN EJERCITAR.** `AiHealthController` es
`[Authorize(Roles = "Administrator")]`, comprobado: con un token de operario devuelve **`403`**. La
contraseña de `demo.admin` no está en el repositorio —correctamente, se generó fuera del anfitrión y
sólo viajó el hash— y este change no crea cuentas administradoras. Lo que **sí** está verificado es que
el interruptor que la cuarta tarjeta necesita está puesto:

```text
AiAgentAssist__EnabledByDefault=true      AiSalesAssist__EnabledByDefault=true
AiFreeQuerySearch__EnabledByDefault=true  AiSearch__EnabledByDefault=true
```

### 3.2 `op-ciutadella` — CIU-CENTRE, surtido máximo *(tarea 3.2)*

**Búsqueda asistida**, consulta «un anillo de plata para regalo», ámbito `CIU-CENTRE`:

```json
"pitchStatus": "generated",  "intent": "in_domain",  "abstained": false,
"aiAvailable": true,  "degradedReason": null,
"candidatesReturned": 15,  "survivedHydration": 5,
"traceId": "067a935d5486d58240289be1ed586b66"
```

Cinco grupos con **existencias resueltas en el punto de venta** —25, 29, 24, 32 unidades—, `hasStock:
true`, precios reales, colecciones (`Colección Suspiro`, `Filigrana`, `Colección Azzurro`) y
`matchReasons: ["vector","lexical"]`, o sea **recuperación híbrida funcionando**. El argumentario llegó
**generado**.

**Ficha de venta** de `SKU983` «Anillo Apotecario Secreto S»:

```json
"quantityAtPointOfSale": 7,  "hasStock": true,  "pitchStatus": "generated",
"citations": [{"citationId": "material-laton#cuidados-y-limpieza-en-casa", …}]
```

**Precio y existencias resueltos, y el argumentario anclado a la pieza con su cita del corpus.** Esto
es además la prueba de que los 161 fragmentos no sólo están, sino que se usan.

### 3.3 `op-fornells` — FORNELLS, surtido mínimo: los tres estados, alcanzados *(tarea 3.3)*

El surtido de hoy: **241 filas asignadas**, repartidas en `3+` 200 · `0` **29** · `1-2` 12. Esos 29
agotados son lo que hace alcanzable el tercer estado.

| Estado | Cómo se provocó | Resultado |
|---|---|---|
| **Abstención** | «un reloj sumergible de buceo con correa de titanio» | `intent: "not_in_catalogue"`, `candidatesReturned: 0`, `survivedHydration: 0`, `pitchStatus: "not_generated"` |
| **Sustitutos** | `GET /substitutes` de `SKU1164`, agotado en FORNELLS | `outcome: "ok"` con candidatos y **existencias suyas** — `SKU605` 11 uds., `SKU1085` 6 uds. |
| **Aviso de agotado** | ficha de venta de ese mismo `SKU1164` | `quantityAtPointOfSale: 0`, `hasStock: false`, **`pitchStatus: "withheld_out_of_stock"`** |

**Los tres alcanzados, ninguno dado por visto.** Un matiz de precisión: la abstención se manifiesta
como `intent: "not_in_catalogue"` con cero candidatos y argumentario no generado — **no** levantando la
bandera `abstained`, que corresponde a otro estado (abstenerse *teniendo* candidatos). Y el argumentario
de una pieza agotada no se «abstiene» sino que se **retiene**, con un motivo propio y nombrado.

### 3.4 `op-aeroport` — MAO-AIR: el pivote, y la limitación medida en lugar de citada *(tarea 3.4)*

La misma pregunta, planteada de las dos maneras, sobre `SKU1127` «Pendientes Luz de Faro», **agotado**
en MAO-AIR. Ésta es la traza del bucle **por referencia**:

```text
iteración 1   consultar_disponibilidad  ok      984,9 ms   1 957 tokens
iteración 2   buscar_sustitutos         ok      746,2 ms   2 033 tokens   <-- EL PIVOTE
iteración 3   consultar_disponibilidad  ok  ×2 1 303,3 ms   2 882 tokens
iteración 4   (ninguna herramienta)            1 081,5 ms   3 038 tokens
```

```json
"stopReason": "sin_mas_herramientas",  "iterations": 4,  "toolCallsUsed": 4,
"pitchStatus": "generated",  "partial": false,  "abstained": false,  "intent": "in_domain"
```

**El pivote ocurre y se ve:** comprueba la disponibilidad, la encuentra agotada, **busca sustitutos**,
comprueba la disponibilidad de dos candidatos y compone. 9 910 tokens, 4 115,9 ms de reloj interno.

**Y por nombre no ocurre, exactamente como C42 midió:**

```text
iteración 1   buscar_catalogo           ok    2 394,8 ms   1 958 tokens
iteración 2   consultar_disponibilidad  ok      617,2 ms   2 615 tokens
iteración 3   (ninguna herramienta)             663,6 ms   2 694 tokens
```

| | por **referencia** | por **nombre** |
|---|---|---|
| Iteraciones | 4 | 3 |
| Llamadas a herramienta | 4 | 2 |
| `buscar_sustitutos` | **sí** | **no** |
| `stopReason` | `sin_mas_herramientas` | `sin_mas_herramientas` |

**La limitación queda medida y no sólo citada.** El bucle busca en el catálogo, recibe candidatos
identificados **sólo por SKU**, no puede saber cuál era la pieza que el cliente nombró, consulta la
disponibilidad de uno de ellos y **correctamente no pivota**. Es limitación declarada con su arreglo
costado en `DEFERRED_TASKS.md`, no defecto de este entorno.

### 3.5 Panel de consulta libre (M1): los tres estados *(tarea 3.5)*

| Estado | Consulta | Resultado |
|---|---|---|
| **Contestada sin pieza concreta** | «collares con motivos marinos», ámbito global | `pitchStatus: "generated"`, `intent: "in_domain"` |
| **Rechazo cortés del enrutador** | «qué tiempo hará mañana en Ciutadella» | `intent: "out_of_domain"`, `candidatesReturned: 0`, `pitchStatus: "not_generated"` |
| **Ámbito global** | `PointOfSaleId` **omitido** | responde, y **`quantityAtPointOfSale: null` en todos los miembros** |

**El ámbito global es alcanzable** —lo que C40_FIX arregló— y se comporta como su contrato promete:
la ausencia de tienda **no** es un comodín y **no** informa cantidades. Devolver `0` habría afirmado
algo falso sobre todo el catálogo; devuelve `null`.

### 3.6 Latencias y los tres relojes del agente *(tarea 3.6)*

Diez llamadas, todas por HTTPS público con el proxy delante:

| Superficie | Llamada | `http` | Reloj |
|---|---|---|---:|
| Tarjeta de salud, como operario | `GET /api/ai/health` | 403 | **0,18 s** |
| Búsqueda asistida, con ámbito | `POST /search/assisted` | 200 | **6,09 s** |
| Ficha de venta, generada | `POST /{id}/sales-assist` | 200 | **3,45 s** |
| Sustitutos | `GET /{id}/substitutes` | 200 | **0,32 s** |
| Ficha de venta, agotada (retenida) | `POST /{id}/sales-assist` | 200 | **5,61 s** |
| Abstención | `POST /search/assisted` | 200 | **0,79 s** |
| Agente, por referencia (pivota) | `POST /search/agent` | 200 | **6,39 s** |
| Agente, por nombre (no pivota) | `POST /search/agent` | 200 | **5,90 s** |
| Consulta libre, ámbito global | `POST /search/assisted` | 200 | **2,48 s** |
| Rechazo del enrutador | `POST /search/assisted` | 200 | **0,80 s** |

**Los tres relojes del agente, contrastados y NO recalibrados:**

| Reloj | Presupuesto | Medido | Margen |
|---|---|---|---|
| Por vuelta del bucle | 8 s | **2 394,8 ms** (la peor iteración) | sobrado |
| Reloj del servicio | 15 s | **4 115,9 ms** (suma interna) | sobrado |
| Presupuesto en .NET | 18 s | **6 387 ms** extremo a extremo | sobrado |

**Pero en frío no hay margen, y eso sí se midió.** La sonda que `verify.sh` lanzó durante el despliegue,
sobre contenedores recién arrancados, registró:

```text
13:33:04,764 WARNING stage=router verdict=none degraded=true cause=timeout router_ms=5278.5 prompt_version=router/v3
13:33:06,496 INFO    stage=agent stop=presupuesto_reloj partial=True iterations=1 tool_calls=0 elapsed_ms=7010.5
```

El enrutador **reventó su reloj de 2 s tardando 5 278 ms**, y el bucle terminó por
`presupuesto_reloj` con `partial=True` y cero herramientas. La ruta respondió —que es todo lo que la
séptima condición pide, y por eso pasó— pero **el arranque en frío es donde los relojes aprietan**, no
el régimen estacionario. El comentario de `verify.sh` predecía `stop_reason='aclaracion'` para esta
sonda; lo que salió fue `presupuesto_reloj`. Dato para quien vaya a recalibrar algún día; **aquí no se
recalibra nada**.

---

## 4 · La CI, que se ejecutó por primera vez en la historia del repositorio

### 4.1 No fueron dos ejecuciones, sino cuatro *(tarea 4.1)*

| Id | Flujo | Evento | Rama | Paso en que murió | Conclusión |
|---|---|---|---|---|---|
| **36319378725** | Backend Tests | `pull_request` | `c39a-redeploy-…` | `Run tests with coverage` | `failure` |
| **36319378727** | Frontend Tests | `pull_request` | `c39a-redeploy-…` | **`Run linting`** | `failure` |
| **36319840972** | Backend Tests | `push` | `ai-eng` | `Run tests with coverage` | `failure` |
| **36319840968** | Frontend Tests | `push` | `ai-eng` | **`Run linting`** | `failure` |

**Esa duplicación es el dato que motivó retirar el disparo por `push`**: el `pull_request` ya se evalúa
sobre la fusión con la base, así que el `push` posterior mide casi el mismo árbol y repite el trabajo.
Hoy los dos flujos llevan sólo `pull_request` sobre `[ai-eng, master]` más `workflow_dispatch`.

**Y en las dos de frontend el paso de tests quedó en `skipped`.** Ésa es la razón por la que **la suite
de frontend no se había medido nunca en CI**: `npm run lint` no podía funcionar porque
`frontend/eslint.config.js` no existía, el paso fallaba, y el de tests no llegaba a correr.

### 4.2 Los rojos, comparados por nombre *(tarea 4.2)*

**Backend.** Línea base de C39a en local: **50 de 1.408**.

| Ejecución | Resumen | Nombres distintos |
|---|---|---|
| 36319378725 (`pull_request`) | `Total tests: 1408 · Failed: 49` | 49 |
| 36319840972 (`push`) | `Total tests: 1408 · Failed: 48` | 48 |

**Trece nombres difieren entre las dos** —7 aparecen, 6 desaparecen, 42 estables— y **los trece caen
dentro de las clases que `CLAUDE.md` declara inestables**: once en `InventoryIntegrationTests` y dos en
`ReturnsControllerTests`. **Cero nombres nuevos fuera de ellas.** Contra la distribución por clase que
C39a guardó, las únicas diferencias son `InventoryIntegrationTests` 9→5 y `ReturnsControllerTests` 4→6;
`ImageCompressionServiceTests` 5, `ProductsControllerTests` 5, `SalesControllerTests` 4,
`RepositoryTests` 4, `PointOfSalesControllerTests` 3 y `EmbeddingEndpointsTests` 3 salen **idénticas**.

**Y esto añade algo que no se sabía:** la rotación **no es un artefacto de la máquina de desarrollo**.
Se reproduce en un *runner* limpio de CI, confinada a las mismas clases. `C39a` no toca código de
backend, así que ninguno de esos nombres le es atribuible.

**Frontend, la primera medición que existe.** Hubo que provocarla a mano:

```bash
gh workflow run test-frontend.yml --ref ai-eng     # -> ejecución 36324085893
```

```text
Test Files  14 failed | 49 passed (63)
     Tests  113 failed | 846 passed (959)
  Duration  153.23s
```

**Idéntica, cifra por cifra, a la línea base local de C39a** (`14 failed | 49 passed (63)` ·
`113 failed | 846 passed (959)`, 197 s). Y **los catorce ficheros son exactamente los mismos catorce**
que C39a enumeró: `payment-methods.test.tsx`, `products/__tests__/edit.test.tsx`,
`product-photo-upload.test.tsx`, `products/edit.test.tsx`, `sales/__tests__/new-image.test.tsx`,
`new.test.tsx`, `sales-index.test.tsx`, `scan.test.tsx`, `image-recognition.service.test.ts`,
`ml-edge-cases.test.ts`, `model-training.service.test.ts`, `auth.service.test.ts`,
`payment-method.service.test.ts`, `product.service.test.ts`. **Cero nombres nuevos.**

Que la suite que rota entre 113 y 114 en local diera **113 en los mismos 14 ficheros** en un *runner*
limpio es el resultado más limpio que esta línea base ha tenido.

### 4.3 El lint, declarado y no arreglado *(tarea 4.3)*

```text
✖ 171 problems (89 errors, 82 warnings)
```

**89 errores y 82 avisos**, en 104 ficheros. El paso está en `continue-on-error` **a propósito**: sin
eso volvería a dejar los tests en `skipped`, que es el defecto que acabamos de quitar. El lint informa;
no bloquea. **No se arregló nada de esto**, y no entra en este change.

### 4.4 No actúan como puerta *(tarea 4.4)*

Comprobado por los dos lados. **Estructuralmente:** ninguna de las tres ramas tiene protección
configurada — `ai-eng`, `master` y `demo` devuelven `404 Not Found` en
`/branches/<rama>/protection`, así que **no hay ninguna comprobación requerida**. **Empíricamente:**
la PR #46 se integró el 2026-09-27T12:41:40Z con sus dos flujos en rojo, y la #47 a las 13:30:29Z.

Es deliberado y está documentado: con **48-49 de 1.408** en backend y **113 de 959** en frontend
preexistentes, un flujo que bloqueara integraría cero PRs.

---

## 5 · Las cuentas de demostración: la premisa era falsa

### 5.1 Lo que había, frente a lo que los artefactos daban por supuesto *(tarea 5.1)*

**Éste es el segundo hallazgo del change, y afecta a su propia especificación.** La delta de
`demo-deployment` afirma que hay tres cuentas de operario ligadas a puntos de venta con surtidos
deliberadamente distintos. **No las había.** Lo que la base desplegada tenía:

| Username | Rol | `IsActive` | Punto de venta |
|---|---|---|---|
| `demo.admin` | Administrator | `t` | — |
| `demo.operador` | Operator | `t` | `MAO-AIR` |
| `admin` | Administrator | **`f`** | — |
| `retirado-18f39e69` | Operator | **`f`** | `CIU-CENTRE` |
| `retirado-95675ead` | Operator | **`f`** | `FORNELLS` |

El §5.3 del *runbook* —«Replace the shop's staff», obligatorio— sustituye el personal real por
**exactamente dos** cuentas. Las dos operarias sintéticas que venían en el volcado quedaron renombradas
a `retirado-<prefijo>` y **desactivadas**, lo que preserva el historial de ventas que las referencia.
`op-ciutadella`, `op-fornells` y `op-aeroport` **sólo viven en el mundo sintético local**
(`ai-service/src/jbg_ai/data/world/constants.py`), nunca en la demo.

**La consecuencia era grave para el propósito del entorno:** con una sola cuenta de operario activa,
ligada a `MAO-AIR`, **la abstención, los sustitutos y el pivote no se podían demostrar en absoluto**,
porque cada uno depende del surtido de un punto de venta **distinto**. Un evaluador habría concluido
que esas conductas no existen.

### 5.2 Lo que se hizo, y por qué se dice en voz alta

**Decidido con el responsable durante el apply**, porque no estaba previsto por los artefactos: se
aprovisionaron los tres operarios sintéticos contra la base desplegada.

```text
INSERT 0 3   -- Users:            op-ciutadella, op-fornells, op-aeroport
INSERT 0 3   -- UserPointOfSales: CIU-CENTRE,    FORNELLS,    MAO-AIR
```

- Rol **`Operator` únicamente**. `admin` y `demo.admin` **no se tocaron**.
- Hash **BCrypt `2a`/12**, generado **fuera del anfitrión** con el ayudante del propio proyecto
  (`hash_operator_password`, que usa `BCRYPT_ROUNDS = 12` y `BCRYPT_PREFIX = b"2a"`) y verificado con
  `password_matches` antes de enviarlo. Sólo viajó el hash, como el §5.3 exige.
- Contraseña `Operator123!`, que **ya era una constante pública documentada** del mundo sintético
  (`ai-service/src/jbg_ai/data/README.md`), así que **no se añade ningún secreto nuevo** al
  repositorio.
- Idempotente (`ON CONFLICT DO NOTHING` y `NOT EXISTS`), en una transacción.

**Y hay que decir qué es esto exactamente:** no es código, no entra en ninguna imagen, no aparece en el
diff y **no dispara el despliegue** — pero **sí es una mutación de un entorno accesible desde
internet**. Se registra aquí porque un cambio que no aparece en un diff es precisamente el que hay que
escribir.

Las cinco cuentas activas quedan declaradas en el nuevo **§5.8 del *runbook***, con su punto de venta y
**qué conducta es alcanzable desde cada una**, más `admin` con su estado y el motivo por el que debe
seguir desactivada. El §5.3 se corrigió: decía «exactly two accounts» y había dejado de describir el
entorno.

---

## 6 · Lo que se refutó, y lo que queda anotado sin arreglar

**Predicciones de C39a y de los artefactos de este change, con su veredicto:**

| Predicción | Veredicto |
|---|---|
| El `IMAGE_TAG` habrá cambiado | ✅ **confirmada**, con el historial del parámetro como prueba |
| El corpus seguirá en 161 o más | ✅ **confirmada**, exactamente 161 |
| La proyección se cura sola al arrancar | ✅ **confirmada**, con dos matices (§2.4) |
| Las tres credenciales serán propias | ✅ **confirmada** |
| Las siete condiciones en verde | ❌ **refutada**: seis, y la séptima falla por ser demasiado estricta |
| Dos ejecuciones de CI | ❌ **refutada**: fueron cuatro |
| La CI de frontend publicará resultado | ❌ **refutada**: moría en el lint; su suite nunca había corrido |
| Existen `admin` activo y tres operarios | ❌ **refutada**: había dos cuentas `demo.*` y `admin` desactivada |
| `stop_reason='aclaracion'` en la sonda del agente | ❌ **refutada**: `presupuesto_reloj` en frío |

**Anotado en `openspec/DEFERRED_TASKS.md`, y no arreglado:**

1. **La quinta condición marca en rojo un despliegue sano** — con los doce puntos de venta, el
   `IsActive` de `HT-ARTRUTX`, el experimento `1` / `0`, la comprobación de permisos que descarta el
   arreglo evidente, y las tres vías con su coste.
2. **La rancidez que el despliegue registra puede ser falsa** — el caché de 10 s contra el drenaje de
   arranque a dos intentos, con las dos vías de cierre.
3. **`ai.sync_failure` acumula 66 filas del *feed* `catalog` que nada mira** — hallado de paso. No es
   un fallo vivo (el índice tiene sus 1.200 documentos), pero es una acumulación silenciosa en una
   tabla cuyo nombre dice exactamente lo contrario.
4. **La deriva de rama**, que C39a dejó declarada: nada compara lo desplegado con la rama que debería
   servirse, aunque los dos datos existen.

**Y lo que queda pendiente de una sesión con navegador**, dicho para que no se dé por hecho: las cuatro
tarjetas del centro de IA **no se han visto**, y la tarjeta de salud de la IA **no se ha ejercitado**
por falta de una credencial administradora.

---

## 7 · La restricción propia de este change, sobre el diff completo *(tarea 6.5)*

Lista de ficheros modificados, uno a uno, contra el `paths-ignore` de `deploy-demo.yml`:

| Fichero | Regla que lo ignora |
|---|---|
| `openspec/changes/verify-demo-redeployment/proposal.md` | `openspec/**` |
| `openspec/changes/verify-demo-redeployment/design.md` | `openspec/**` |
| `openspec/changes/verify-demo-redeployment/tasks.md` | `openspec/**` |
| `openspec/changes/verify-demo-redeployment/specs/demo-deployment/spec.md` | `openspec/**` |
| `openspec/DEFERRED_TASKS.md` | `openspec/**` |
| `deploy/demo/README.md` | `**/README.md` |
| `Documentos/Proyecto Final AIEng/informes/c39a-bis-implementation-measurements.md` | `Documentos/**` |
| `Documentos/Proyecto Final AIEng/proyecto-final-plan-changes-openspec.md` | `Documentos/**` |
| `Documentos/Historias/AI-Eng/HU-AIENG-043.md` | `Documentos/**` |

**Cero ficheros fuera de la lista**, así que el merge a `demo` **no** dispara `deploy-demo.yml`.

**Dos precisiones que hacen la afirmación honesta.**

**Primera:** la lista de seis rutas que los artefactos citan es un **subconjunto** del `paths-ignore`
real, que ignora también `.github/workflows/test-*.yml`, `deploy-aws-ec2.yml`,
`deploy-backend-aws.yml`, `deploy-frontend-aws.yml`, `.claude/**`, `.codex/**`, `.cursor/**`,
`.agent/**`, `.opencode/**`, `.docs-update/**` y `.pr/**`. Quedarse dentro de las seis es **más
estricto** que lo necesario, no menos.

**Segunda, y hay que decirla porque el criterio se leería mal sin ella:** `ai-eng` ya lleva **un commit
por delante de `demo`** que **no** está en el `paths-ignore` — `0c9bb68`, que toca
`frontend/eslint.config.js`. Así que **el próximo merge de `ai-eng` a `demo` sí desplegará**, por ese
commit y no por este change. La propiedad que este change garantiza es la suya: **su propio diff no
dispara nada**. No garantiza que la rama a la que se incorpora no lleve ya otra cosa.
