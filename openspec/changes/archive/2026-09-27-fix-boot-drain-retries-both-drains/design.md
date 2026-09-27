## Context

`_boot_drain` reintentaba mientras `drain_pass(...)` devolviera `None`, y `drain_pass` devuelve el resultado del **drenaje de disponibilidad**. El de tiendas se ejecuta antes y su resultado se descartaba, así que su fallo era invisible para el bucle.

## Goals / Non-Goals

**Goals:** que «el proceso ha arrancado» implique «las dos tablas están al día», que es el invariante para el que existe el drenaje de arranque.

**Non-Goals:** no se toca el *feed*, ni el repositorio, ni el informe de salud, ni `verify.sh`. Tampoco el bucle del intervalo: ahí `drain_pass` es correcto, porque el siguiente tic llega solo y no hay ventana que cerrar.

## Decisions

### D1 · El reintento es por drenaje, y el estado vive en el bucle

Dos banderas locales en `_boot_drain`. Se reintenta sólo el drenaje que falta, así que el que ya salió bien no se repite — que importa en el de disponibilidad, donde una pasada cuesta páginas.

**Alternativa descartada: que `drain_pass` devuelva un agregado y el bucle mire «ambos no nulos».** Funciona, pero repetiría el drenaje que ya salió bien en cada reintento, y el de disponibilidad no es barato.

**Alternativa descartada: darle al drenaje de tiendas su propio bucle de arranque.** Duplicaría la política de reintentos en dos sitios y rompería el orden —tiendas antes que disponibilidad— que el requisito fija.

### D2 · El aviso de agotamiento nombra a cada drenaje

«Se agotaron los intentos» sin decir de cuál es la mitad de la información, y es justo la mitad que habría hecho evidente este defecto al leer el registro del despliegue.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| El arranque tarda más cuando un *feed* está caído | Acotado por el mismo calendario de siempre —0, 5, 15 y 45 s— y el drenaje no bloquea el arranque: la tarea no se espera y `/health` responde durante todo el proceso |
| Un test de C41 cambia de comportamiento | No es daño colateral sino un aislamiento que faltaba: dejaba el drenaje de tiendas sin sustituir y por tanto alcanzaba el real |
