## 1. El arreglo

- [x] 1.1 `_boot_drain` reintenta **por drenaje**: lleva la cuenta de cuál ha corrido y reintenta sólo el que falta, conservando el orden —tiendas primero—. *Validación: test que reproduce la secuencia del despliegue (tiendas falla en el intento 1, disponibilidad sale bien) y comprueba que hay intento 2 de tiendas y **uno solo** de disponibilidad.*
- [x] 1.2 El aviso de agotamiento declara el resultado de cada drenaje. *Validación: test que lo lee del registro.*
- [x] 1.3 Aislar `test_the_boot_drain_retries_until_the_feed_answers`, que dejaba `run_pos_shop_drain` sin sustituir y por tanto alcanzaba el drenaje real. *Validación: el test vuelve a afirmar lo que su nombre dice, y los 25 del fichero pasan.*

## 2. Puerta de salida

- [x] 2.1 Suite de `ai-service` entera, comparada contra la línea base de C43 (**1.687 · 0 fallidos**). *Validación: la línea de resumen.*
- [x] 2.2 `openspec validate --all --strict` con **`0 failed`**, antes de archivar. *Validación: la línea de resumen.*
- [ ] 2.3 Confirmar en el **próximo despliegue** que el arranque llena las dos tablas y que la verificación concluye `success`. *Validación: el registro del despliegue y el log del planificador.*
