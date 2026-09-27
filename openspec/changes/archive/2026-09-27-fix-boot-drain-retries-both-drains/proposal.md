## Why

**C43 arregló el falso positivo y, al hacerlo, introdujo un fallo verdadero en el drenaje de arranque. El despliegue lo encontró el mismo día.**

El despliegue `36343020047` del 2026-09-27 construyó las dos imágenes, las publicó, actualizó `IMAGE_TAG`, desplegó — y **falló en la verificación**, esta vez con razón:

```text
[verify] waited 180s for the start-up drains to report
[verify] FAILED:
  - the AI service knows of no active point of sale; ai.pos_shop is empty, so the count of
    shops without assortment is vacuous and proves nothing about this environment
```

**La condición hizo exactamente su trabajo.** Es la condición (a) que C43 añadió precisamente para que una tabla vacía no pasara en vacío, y lo que destapó es un defecto del propio C43.

El registro del contenedor no deja dudas:

```text
19:07:07,442  boot_drain attempt=1
19:07:07,644  WARNING pos_shop_scheduler feed_not_configured error=POS shops feed is unavailable
19:07:08,857  pos_sync_scheduler drained pages=1 upserted=1 soft_deleted=0 failed_pages=0
```

**El drenaje de tiendas falló por 1,2 segundos**, porque el lado .NET todavía no servía el *feed*. El de disponibilidad, un segundo después, sí. Y ahí está el fallo: `_boot_drain` reintentaba mientras `drain_pass(...)` devolviera `None`, y **`drain_pass` devuelve el resultado del drenaje de disponibilidad**. Uno de los dos bastó para terminar el bucle de los dos. No hubo intento 2. `ai.pos_shop` se quedó vacía hasta el tic de 600 s — muy por detrás de los 180 s que la verificación espera.

**Es la misma familia de defectos que C43 vino a cerrar, un nivel más arriba:** *parte del trabajo salió bien* se leyó como *el trabajo salió bien*. Exactamente la forma de «una tabla vacía hace pasar una comprobación» que la condición (a) existe para impedir, sólo que esta vez en el bucle que llena la tabla.

**Y el mecanismo de C43 está bien**: cuando el tic de 600 s corrió, a las 19:17:08, escribió `written=12 removed=0 active=11` y el informe pasó a `active_points_of_sale: 11`, `shops_without_scope: 0`. El entorno quedó correcto **solo**. Lo que falla es únicamente el camino de arranque.

**Por qué el test de C43 no lo cazó:** `test_the_boot_drain_runs_a_whole_pass` da por buenos los dos drenajes, así que nunca ejercitó el caso en que uno falla y el otro no. Y la spec no lo pedía: dice que los dos drenajes corren al arrancar y en orden, pero **no dice que el reintento de arranque cubra a los dos**.

## What Changes

- **`_boot_drain` reintenta por drenaje, no por pasada.** Lleva la cuenta de cuál ha corrido ya y reintenta **sólo el que falta**, de modo que el que ya salió bien no se repite.
- **El aviso de agotamiento dice cuál no llegó a correr** — `shops_drained=False availability_drained=True` —, porque «se agotaron los intentos» sin decir de qué es la mitad de la información.
- **La spec gana el escenario que faltaba**, que es lo que permitió que el defecto pasara la revisión: el reintento de arranque debe cubrir a cada drenaje por separado.
- **Tres tests nuevos**, uno de ellos reproduciendo literalmente la secuencia del despliegue —tiendas falla en el intento 1, disponibilidad sale bien en el intento 1— y su espejo, para que el arreglo no quede cojo de un lado.
- **Un test de C41 se aísla:** `test_the_boot_drain_retries_until_the_feed_answers` dejaba `run_pos_shop_drain` sin sustituir, así que alcanzaba el drenaje real y fallaba por su cuenta. Con el arreglo eso cambia el número de intentos y el test dejaba de afirmar lo que su nombre dice.

**No se toca nada más.** Ni el *feed*, ni el repositorio, ni el informe de salud, ni `verify.sh` — cuya condición (a) **funcionó** y es la razón por la que esto se supo el mismo día en lugar de en la demostración.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `pos-projection`: **una modificación**. El requisito del drenaje planificado dice que los dos drenajes corren al arrancar y en orden, y que el fallo de uno no impide intentar el otro. Le falta la mitad que este defecto destapó: que el **reintento de arranque** se aplique a cada drenaje por separado, porque el arranque es el único momento en que la ventana importa — el tic siguiente está a diez minutos y la verificación espera tres.

## Impact

- `ai-service/src/jbg_ai/indexing/scheduler.py` — `_boot_drain`
- `ai-service/tests/indexing/test_pos_scheduler.py` — tres tests nuevos y uno aislado
- `openspec/specs/pos-projection/spec.md` al sincronizar

**Requiere redespliegue**, porque cambia la imagen de IA. El entorno desplegado **ya está correcto** —el tic de 600 s llenó la tabla—, así que esto no repara un entorno roto: impide que el **próximo** arranque vuelva a dejarlo a medias y marque en rojo un despliegue que por lo demás está bien.
