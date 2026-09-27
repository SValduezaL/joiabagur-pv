## Why

`POST /v1/assist/sale` y `POST /v1/retrieval/substitutes` están servidos y medidos en `jbg-ai` desde
C26, C30a, C30b y C31, pero **no tienen ningún consumidor .NET**: ni el argumentario, ni las citas, ni
los sustitutos llegan a un operario, y el card de venta de C36 no tiene a quién llamar. Este change
entrega ese consumidor y, con él, la **regla de una frase del §6.2** del diseño en el punto donde más
se nota: *Python calcula parecidos y redacta; .NET calcula números y decide*. Aquí .NET decide qué
miembros de la familia existen en la tienda, cuántas unidades hay, qué sustitutos se pueden vender hoy
y con qué precio se escribe el argumentario — y garantiza que un fallo de la IA nunca deja el card
vacío.

La exploración del 2026-09-21 ([informe](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md))
refutó la anotación de la ficha que daba a este change la ruta de la consulta libre —los marcadores
`{{price}}`/`{{stock}}` no dicen de qué pieza son, y en ese modo hay varias— y midió cuatro cifras que
fijan el diseño: el presupuesto de 5 s corta el 7,5 % de las peticiones, `{{stock}}` se escribe como
número en el 88,3 % de los argumentarios, `family_has_variants` saldría falso en el 19,2 % tras
hidratar, y una ventana de sustitutos de 15 deja sin página al 71,1 % de las piezas de Fornells.

## What Changes

- **Nuevo `POST /api/ai/products/{productId}/sales-assist`** con cuerpo `{pointOfSaleId, question?}`:
  el argumentario de la pieza (M2) o la respuesta a una pregunta sobre ella (M3). La pregunta viaja en
  el cuerpo y nunca en la URL, porque es texto libre del cliente.
- **Nuevo `GET /api/ai/products/{productId}/substitutes?pointOfSaleId=&pageSize=`**.
- **Autorización y comprobación de la pieza antes de gastar una llamada**: punto de venta obligatorio
  con la regla de C15, 403 para un operario sin asignación y **404 si la pieza anclada no está en esa
  tienda**, las dos sin llamar a la IA.
- **Hidratación autoritativa del grupo**: sólo los miembros que la tienda lleva, en el orden de la IA,
  con precio, cantidad y foto del catálogo transaccional.
- **Resolución de `{{price}}` y `{{stock}}` contra la pieza anclada** —«39,90 €» y el entero—, y
  **retirada del argumentario, no de la respuesta**, cuando queda cualquier marcador sin resolver.
  Seis estados explícitos del argumentario para el frontend.
- **Pieza anclada agotada**: sin pregunta se retira el argumentario; con pregunta se sustituye el 0.
- **Los dos avisos de stock** (`stock_critical`, `family_members_out_of_stock`) calculados aquí, y
  **`family_has_variants` recalculado** sobre los miembros que sobreviven a la hidratación.
- **Sustitutos** con la ventana máxima en una sola llamada, exclusión de lo que no tiene stock en la
  tienda, orden intacto, paginado y **cuatro resultados vacíos distinguibles**.
- **Degradación**: con la IA caída, el card sale con la pieza, su familia leída del catálogo y los
  avisos de stock, sin argumentario ni citas.
- **Cliente del gateway**: dos operaciones tipadas; cliente propio para la ruta generativa a **10 s**,
  **sin reintento en timeout**, con circuito propio y un **suelo de 8 s validado al arranque**; y un
  **422 que deja de leerse como «IA no disponible»** en esas dos operaciones.
- **Operación**: interruptor por punto de venta, límite de peticiones propio para la ruta generativa y
  una política de logs en la que **el argumentario resuelto no aparece nunca**.
- **La generación encendida en la demo**, como última tarea.

Sin cambios de ruptura: rutas nuevas, `POST /api/ai/search` intacto, contrato de `jbg-ai` **idéntico
byte a byte** y sin migración. `IAiGatewayClient` crece con dos métodos.

## Capabilities

### New Capabilities
- `ai-sales-assist`: las dos rutas del card de venta del backend — ámbito de punto de venta y
  comprobación de la pieza anclada antes de llamar a la IA, hidratación autoritativa del grupo,
  avisos de stock y ajuste del aviso de variantes a la tienda, resolución de marcadores contra la
  pieza con retirada del argumentario y sus estados explícitos, sustitutos con ventana máxima,
  exclusión por stock y resultados vacíos distinguibles, degradación con la familia del catálogo,
  activación por punto de venta, límite de peticiones y política de registro.

### Modified Capabilities
- `ai-gateway-client`: gana las operaciones de asistencia de venta y de sustitutos. La política de
  reintento deja de reintentar los timeouts **en la ruta generativa**, donde repetir cuesta el doble
  de latencia y dos llamadas de pago; la degradación gana un cliente y un circuito propios para esa
  ruta; el 422 de esas dos operaciones pasa a ser un rechazo distinguible de la indisponibilidad; la
  configuración valida al arranque que el presupuesto generativo no quede por debajo del peor caso
  declarado del servicio de IA; y la guarda de deriva de contrato cubre los modelos nuevos.

## Impact

- **Backend `.NET`** — controlador nuevo bajo `api/ai/*`; servicios de asistencia y de sustitutos;
  dos operaciones y un cliente con nombre nuevos en la pasarela, con su excepción de rechazo; objetos
  de transferencia del contrato de `jbg-ai` y de las dos rutas; opciones validadas al arranque; una
  política de limitación de peticiones; una clase base de test para los siete dobles escritos a mano
  de la pasarela; pruebas unitarias e integración con contenedores y pasarela falsa.
- **Demo** — `compose.demo.yaml`, `deploy/demo/deploy.sh` y `deploy/demo/README.md`, más un
  parámetro del almacén de secretos creado a mano. **Terraform no se toca.**
- **Sin cambios** en `ai-service/` (el contrato no se mueve), en el frontend, en `POST /api/ai/search`
  ni en el esquema de base de datos: **no se abre migración**.
- **Desbloquea C36** —el card que lee estas dos rutas— y deja a C38 sin prerrequisitos pendientes
  cuando se archive.
- **Cierra** la tarea diferida *«C30b — la demo no genera argumentario»*. **Deja abiertas**, con motivo,
  la consulta libre sin pieza (§15.12 del diseño) y la ruta del agente: las dos necesitan que los
  marcadores digan de qué pieza hablan, y ese arreglo es de Python.
- **Obligación heredada por C36**: los seis estados del argumentario y los cuatro resultados de
  sustitutos dicen cosas distintas; pintarlos como una misma ausencia haría mentir a la pantalla.
