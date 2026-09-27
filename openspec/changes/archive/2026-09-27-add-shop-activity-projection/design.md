## Context

`build_projection_section` publica `shops_without_scope` como la diferencia de dos recuentos tomados sobre una sola tabla:

```sql
SELECT count(DISTINCT pos_id) AS points_of_sale,
       count(DISTINCT pos_id) FILTER (WHERE is_assigned_hint) AS scoped
FROM ai.pos_projection
```

**No hay ninguna noción de si la tienda está activa**, así que una tienda legítimamente cerrada es indistinguible de una tienda rota. `deploy/demo/verify.sh` falla el despliegue si esa diferencia es mayor que cero, y el 2026-09-27 lo hizo sobre un entorno sano.

Tres restricciones gobiernan el diseño, y ninguna es negociable:

1. **El rol `jbg_ai` no puede leer `public."PointOfSales"`.** Medido, no supuesto: `InsufficientPrivilege: permission denied for table PointOfSales`. La decisión D9 / Q-5 de C41 está **impuesta por los permisos**, y `pos-projection` la fija además como requisito vivo: «*counted within schema `ai` and never by reading schema `public` by SQL*».
2. **El *feed* de disponibilidad es incremental por *keyset* sobre el *watermark* de la fila de inventario.** `IndexFeedRepository.GetPosPageAsync` calcula `let watermark = inventory.LastUpdatedAt > inventory.UpdatedAt ? … : …`. Un cambio de estado de una tienda **no toca ninguna fila de `Inventories`**, así que el *watermark* no se mueve y el incremental no reemite nada. El `aggregateHash` tampoco lo vería: se calcula sobre pares `(PointOfSaleId, ProductId)`.
3. **`alembic upgrade head` corre a mitad del despliegue.** `deploy/demo/deploy.sh:208`, **después** de `docker compose up -d` y **antes** de `verify.sh`. Cualquier tabla nueva nace **vacía con el contenedor de IA ya arrancado**, y la ventana entre esos dos instantes es exactamente donde la verificación sondea.

El consumidor del informe ya es tolerante por el lado bueno: `raw.get("isAssignedHint", True)` en `feed.py:238` es un `dict.get`, `AiHealthProjection` declara **todos** sus recuentos como `int?`, y `ai-health.types.ts:75` los declara `number | null`. Añadir campos no rompe a nadie, y un `null` viaja limpio hasta el panel, donde `(shopsWithoutScope ?? 0) > 0` lo trata como «no pintes nada».

## Goals / Non-Goals

**Goals:**

- Que el recuento de tiendas sin surtido hable de tiendas **activas**, en el informe de salud y por tanto en las tres superficies que lo leen: `verify.sh`, `GET /api/ai/health` y la tarjeta del panel.
- Que la actividad de la tienda cruce la frontera de esquemas **por el *feed***, que es el único camino que C17 dejó abierto, y no aflojando un permiso.
- Que el nuevo recuento detecte además **una tienda activa ausente por completo de la proyección**, caso hoy invisible.
- Que la quinta condición **falle con la tabla de tiendas vacía**, en lugar de pasar en vacío.
- Que el despliegue deje de registrar una rancidez ya curada al imprimirse.

**Non-Goals:**

- **No se toca el *feed* `pos-availability`**: ni su cursor, ni su `aggregateHash`, ni su tamaño de página, ni su contrato. Es el camino que funciona.
- **No se toca el frontend.** La línea roja desaparece porque el número pasa a ser correcto.
- **No se toca la capa .NET del informe de salud.** El *endpoint* nuevo es lo único que .NET gana.
- **No hay migración de EF Core**: `PointOfSales.IsActive` ya existe.
- **No hay ruta bajo `/v1`** ni regeneración de `ai-service/openapi.json`.
- **No entra la alerta `CRITICAL` de reconocimiento de imagen.** Es funcionalidad del MVP, el catálogo sintético tiene 0 fotos de 1.200 productos, y la vía elegida es declararlo en el guion de la demo en C39b.
- **No entra la verificación de extremo a extremo.** Es el despliegue, y ocurre después de archivar.

## Decisions

### D1 · La actividad viaja en una tabla propia de esquema `ai`, no en una columna de la proyección

**`ai.pos_shop`: una fila por tienda, con `pos_id`, `is_active` y `refreshed_at`.** Revisión de Alembic aditiva sobre la cabeza actual `d7c4e91b25a0`.

| Alternativa | Por qué no |
|---|---|
| Columna `is_shop_active` en `ai.pos_projection` | **Se quedaría rancia para siempre.** Restricción 2: un cambio de estado de tienda no mueve ningún *watermark* de inventario, así que el incremental no reemite la fila y la columna conserva el valor del día en que se escribió. Medido: los drenajes dan `pages=1 upserted=1` por pasada |
| `GRANT SELECT ON public."PointOfSales" TO jbg_ai` | Viola el requisito vivo de `pos-projection` y convierte en excepción la frontera que C17 dibujó adrede. Barato de escribir y caro de tener |
| Comprobar desde el anfitrión con el superusuario de la base | **No arregla la tarjeta del panel.** `verify.sh` pasaría y `GET /api/ai/health` seguiría diciendo `shopsWithoutScope: 1`. Arregla el síntoma que se mira y deja el que se enseña |

La cardinalidad decide el coste: **doce filas**. Una tabla de doce filas redrenada entera cada tick es más barata que cualquier protocolo incremental que se pudiera escribir para ella.

### D2 · Un *endpoint* nuevo, sin cursor y sin paginación

`GET /api/ai/index-feed/pos-shops`, autenticado con `X-Index-Feed-Key` como los otros dos, devolviendo **todas** las tiendas con su `pointOfSaleId`, su `isActive` y un `computedAsOf` de la lectura.

**Por qué no ensanchar `pos-availability`:** son dos cardinalidades y dos ritmos distintos. El *feed* de disponibilidad pagina de 200 en 200 sobre miles de filas de inventario y su cursor es el *watermark* de esas filas; la actividad de tienda son doce filas que cambian cuando alguien abre o cierra una tienda. Meterlas en el mismo cuerpo obligaría a decidir en qué página viajan y a que el `aggregateHash` —hoy un digesto de pares `(PointOfSaleId, ProductId)`— dejara de describir lo que describe.

**Por qué sin cursor:** un *feed* completo es la única forma de que el consumidor pueda **retirar** una tienda. Con cursor, una tienda borrada del negocio no genera ningún ítem y quedaría en `ai.pos_shop` para siempre — el mismo defecto que D1 rechaza, una tabla más allá.

**El `join` a `PointOfSales` existe aquí y no en el otro *feed***, que es la razón técnica de que el dato no estuviera disponible: `GetPosPageAsync` proyecta desde `Inventories` y nunca toca la tabla de tiendas.

### D3 · El drenaje es siempre completo y se aplica en una sola transacción

El cuerpo del *feed* es un **retrato completo**, así que el drenaje reemplaza el contenido de `ai.pos_shop` por él: inserta o actualiza lo que viene y **borra lo que no viene**.

Las dos partes van en **una transacción**. No es formalismo: un borrado comprometido sin su inserción dejaría la tabla vacía, y con la condición (a) de §D7 eso **falla el despliegue**. Una escritura parcial no puede ser un estado observable.

**Qué pasa si el *feed* devuelve cero tiendas.** La tabla queda vacía y la verificación falla, que es lo correcto: un negocio sin ninguna tienda activa no es un entorno listo para enseñarse. El fallo es honesto, no un efecto colateral.

### D4 · `NOT EXISTS` con las tiendas a la izquierda, nunca un `FILTER` sobre la proyección

```sql
SELECT count(*) FILTER (WHERE s.is_active)                       AS active_points_of_sale,
       count(*) FILTER (WHERE s.is_active AND NOT EXISTS (
           SELECT 1 FROM ai.pos_projection j
           WHERE j.pos_id = s.pos_id AND j.is_assigned_hint))    AS active_without_scope
FROM ai.pos_shop s
```

**La dirección de la lectura es la decisión, no un detalle de escritura.** Un `FILTER` sobre `ai.pos_projection` sólo puede hablar de las tiendas que ya aparecen en ella, así que **una tienda activa sin ninguna fila es invisible** — y es el peor caso de los dos, porque responde 503 a toda recuperación igual que la otra y además nadie la ha contado nunca. Poniendo las tiendas a la izquierda, ausencia y desasignación caen en el mismo número.

Se lee en la **misma sesión** que el resto del informe, como C41 estableció: el informe entero sigue costando **una conexión** de un *pool* capado a cinco.

### D5 · Con `ai.pos_shop` vacía el recuento es `null`, no `0`

Un cero afirmaría «ninguna tienda activa carece de surtido», que es falso cuando lo que pasa es que no se sabe de ninguna tienda. `null` dice «no lo sé», y es lo que el informe ya usa cuando la base no está disponible.

**Y viaja limpio sin tocar nada más**, que es lo que hace barata esta elección: `int?` en `AiHealthProjection`, `number | null` en `ai-health.types.ts`, y `(shopsWithoutScope ?? 0) > 0` en `AdminDashboard.tsx` — el panel no pinta la línea roja ante un `null` y no hace falta editar ni la plantilla ni el DTO.

`active_points_of_sale` se publica **junto** al recuento, porque es lo que permite a un consumidor distinguir los dos ceros: `active_points_of_sale = 0` es «no sé de ninguna tienda», y `active_points_of_sale = 11` con `shops_without_scope = 0` es «las once están servidas».

### D6 · `active_points_of_sale` se publica en el informe de Python y **no** se añade al DTO de .NET

Quien necesita distinguir los dos ceros es `verify.sh`, que sondea `http://127.0.0.1:8000/health` **dentro del contenedor** y no pasa por .NET. La tarjeta del panel no lo necesita: le basta con que el número deje de ser 1.

Añadirlo a `AiHealthResponse` sería un campo que nadie lee — y la lectura tolerante de .NET ya ignora los campos que no conoce, así que publicarlo en Python no rompe nada por ese lado. Si algún día la tarjeta quiere decir «aún no sé de ninguna tienda», el campo estará esperando en el cuerpo.

### D7 · La quinta condición cambia de sujeto y gana un fallo que hoy no tiene

```text
(a)  active_points_of_sale ausente o 0   -> FALLA   «el servicio no conoce ninguna tienda activa»
(b)  shops_without_scope > 0             -> FALLA   «N tienda(s) ACTIVA(S) sin surtido»
```

La condición (a) es la que impide que este change introduzca **la cuarta instancia de la familia de defectos que viene a cerrar** —C34, C41 y C39a son las tres anteriores—, todas con la misma forma: una tabla vacía que hace pasar una comprobación en lugar de fallarla. Por la restricción 3, la tabla nueva **nace vacía a mitad del despliegue**, así que el caso no es teórico: es el estado por el que el entorno pasa en cada redespliegue.

Se conserva la tolerancia que la condición ya tiene con una imagen anterior que no reporte la sección: **ausente no es fallo, es desfase de versión**. Pero `active_points_of_sale` ausente **en una imagen que sí reporta la sección** sí lo es, y distinguir los dos casos es precisamente lo que la condición (a) hace.

### D8 · `verify.sh` espera al drenaje sondeando, no pidiendo un informe sin caché

El informe se cachea 10 s (`HEALTH_CACHE_TTL_SECONDS`) y el drenaje de arranque necesitó **dos intentos** el 2026-09-27, porque el primero salió antes de que el lado .NET sirviera el *feed*. La verificación sondeó en medio y registró una rancidez que ya era falsa.

**La espera se implementa reintentando la sonda** hasta que el informe declare los dos drenajes hechos, con un techo de tiempo, y sólo entonces se evalúan las condiciones.

| Alternativa | Por qué no |
|---|---|
| Un parámetro de consulta `?fresh=1` en `/health` | Mueve el contrato de una ruta que el *snapshot* de OpenAPI congela, y añade a un *endpoint* de diagnóstico una forma de saltarse la protección del *pool* |
| Bajar `HEALTH_CACHE_TTL_SECONDS` | El caché existe para que la sonda del contenedor y un humano refrescando no agoten cinco conexiones. Se pagaría en todas partes para arreglar un sitio |
| Mover `alembic upgrade head` antes de `up -d` | No puede: la revisión se aplica **desde dentro** del contenedor de IA, que tiene `alembic`, las revisiones y `DATABASE_URL` |

El reintento arregla los dos defectos con un solo mecanismo: espera a que la tabla nueva esté llena **y** deja de imprimir una rancidez caducada.

### D9 · El drenaje de tiendas va en el planificador de C41, y antes que el de disponibilidad

El mismo `lifespan`, el mismo intervalo, las mismas tres condiciones de `scheduler_should_run` —interruptor, no `STUB_MODE`, *feed* configurado— y el mismo reintento de arranque.

**El orden importa y es tiendas primero.** El recuento cruza las dos tablas; drenar la proyección antes que las tiendas deja una ventana en la que hay surtido y no hay a quién atribuírselo, que es el estado que la condición (a) lee como fallo. Al revés no hay ventana mala: tiendas conocidas y proyección aún vacía es un fallo **verdadero** mientras dure.

Este drenaje **no embebe nada** y no necesita clave de proveedor, igual que el de C41, que es la propiedad que permite alcanzarlo desde un proceso cuyo trabajo es responder HTTP.

### D10 · `failed_pages` pasa a contarse por *feed*

Es la misma línea de código —`_PROJECTION_FAILURES_SQL` filtra por `feed = :feed`— y hace visibles las **66 filas** de `ai.sync_failure` del *feed* `catalog` que hoy nadie mira. El informe dice `0` y dice la verdad, porque cuenta sólo `pos-availability`; lo que no existe es quien cuente las otras.

Se publica **desglosado y conservando el escalar actual** para el *feed* de la proyección, de modo que ni `verify.sh` ni la tarjeta cambian de lectura mientras el dato nuevo aparece al lado.

## El flujo, de punta a punta

```text
deploy.sh                    jbg-demo-api (.NET)        jbg-demo-ai (Python)        PostgreSQL
    │                               │                            │                      │
    ├─ docker compose up -d ───────▶│                            │                      │
    │                               │                       [lifespan]                  │
    ├─ alembic upgrade head ────────┼───────────────────────────▶│─ CREATE ai.pos_shop ▶│   (VACÍA)
    │                               │                            │                      │
    │                               │◀── GET /index-feed/pos-shops ─┤  (drenaje 1)       │
    │                               │──── 12 filas, sin cursor ──▶│── replace en 1 tx ──▶│
    │                               │◀── GET /index-feed/pos-availability ─┤ (drenaje 2) │
    │                               │──── página + cursor ───────▶│── upsert ───────────▶│
    │                               │                            │                      │
    ├─ verify.sh ───────────────────┼──── GET /health ──────────▶│── 1 sesión, 1 conn ─▶│
    │   reintenta hasta 'drained'   │                            │                      │
    │   (a) active_points_of_sale>0 │                            │                      │
    │   (b) shops_without_scope==0  │                            │                      │
    ▼                               │                            │                      │
 success                            │                            │                      │
```

La ventana peligrosa es la franja entre `alembic upgrade head` y el final del drenaje 1: ahí `ai.pos_shop` está vacía y el proceso de IA ya está atendiendo. La condición (a) la convierte en un fallo declarado y el reintento de D8 la deja pasar sin ruido cuando el drenaje sencillamente aún no ha terminado.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| **La tabla nace vacía a mitad del despliegue** (restricción 3) y la verificación sondea en esa ventana | D7 condición (a) la declara fallo en lugar de dejarla pasar; D8 reintenta hasta que el drenaje reporte hecho, con techo de tiempo |
| **Un *feed* que devuelve cero tiendas vacía la tabla** | D3: retrato completo en **una transacción**, así que no hay estado intermedio observable. Y el resultado —verificación en rojo— es el juicio correcto sobre un negocio sin tiendas activas |
| **El recuento cruza dos tablas que dos drenajes distintos llenan**, así que pueden desincronizarse | D9 fija el orden —tiendas antes que disponibilidad—, que es el que sólo produce falsos **negativos** transitorios (fallo verdadero mientras dura) y nunca un falso positivo silencioso |
| **Una tienda que se cierre entre dos ticks queda contada como activa hasta 600 s** | Es rancidez acotada por el mismo intervalo que la proyección ya tolera, y en la dirección segura: una tienda recién cerrada se cuenta como activa y sin surtido, lo que **avisa de más**, nunca de menos |
| **El *endpoint* nuevo añade superficie a una API autenticada sólo por clave de *feed*** | Misma clave, mismo filtro `[IndexFeedKey]`, mismo controlador. No expone cantidades ni nada que los otros dos no expongan ya: `pointOfSaleId` e `isActive`, que la capa .NET ya sirve a operarios autenticados |
| **La suite de .NET tiene ~48-50 rojos preexistentes** y la del frontend 113 de 959 | Se compara **por nombre** y no por recuento, con la línea base medida antes. La rotación conocida vive en `InventoryIntegrationTests`, `ReturnsControllerTests` y `PaymentMethodsControllerTests`. Criterio: **cero nombres nuevos en el área propia** |
| **`verify.sh` sólo se prueba contra el compose local** dentro de este change | Declarado, no escondido: la verificación de extremo a extremo **es** el despliegue y ocurre después de archivar. La recoge C39b |

## Migration Plan

1. **Revisión de Alembic aditiva** sobre `d7c4e91b25a0`. Crea `ai.pos_shop` y nada más; el `downgrade` la elimina y no deja rastro, que es posible porque no crea ningún tipo enumerado.
2. **Se aplica sola en el despliegue**: `deploy.sh` ya corre `alembic upgrade head` desde dentro del contenedor de IA. No hay paso manual.
3. **Redrenaje completo de `pos-availability`** con `python -m jbg_ai.indexing sync-pos --full`, confirmando `drift_count = 0`. `last_full_sync_at` sigue en `2026-09-22T18:22:29` mientras el incremental avanza cada 600 s, y **nadie ha comprobado nunca la deriva contra este entorno**.
4. **Rollback**: el `downgrade` de la revisión, y una imagen anterior. Una imagen anterior contra una base con la tabla nueva funciona —nadie la lee— y la imagen nueva contra una base sin ella cae en la condición (a), que falla el despliegue diciendo exactamente lo que pasa en lugar de pasar en silencio.

## Open Questions

Ninguna bloqueante. Dos decisiones quedan tomadas por defecto y se pueden revisar al aplicar:

- **Si `ai.pos_shop` debe guardar también el código de la tienda** (`HT-ARTRUTX`) además del identificador. Hoy no: el informe cuenta y no nombra, y un nombre en el esquema `ai` es una copia más de un dato del que `public` es la autoridad. Si un día la tarjeta quiere **decir cuál** es la tienda rota, entra entonces y con ese motivo.
- **Si el desglose de `failed_pages` por *feed* (D10) entra en este change o en el suyo.** Entra aquí porque es la misma línea de código y su entrada diferida ya existe; si al aplicar resulta que arrastra decisiones sobre purgar `ai.sync_failure`, se deja anotado y se saca.
