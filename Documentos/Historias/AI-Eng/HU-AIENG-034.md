# HU-AIENG-034: Venta asistida y sustitutos en .NET — el card hidratado, los marcadores resueltos contra la pieza y ninguna caída por culpa de la IA

## Formato estándar

**Como** desarrollador del proyecto,
**quiero** dos rutas .NET ancladas a una pieza —el argumentario o la respuesta a una pregunta sobre
ella, y sus sustitutos con stock— que pidan a `jbg-ai` lo que sólo él sabe calcular, lo hidraten con
el precio, el stock y los permisos reales del punto de venta, resuelvan `{{price}}` y `{{stock}}`
contra la pieza anclada y degraden sin romperse cuando la IA no responde,
**para** que el card de venta de C36 pueda enseñar al operario, en el mostrador, una respuesta en la
que ninguna cifra la haya escrito un modelo y en la que un fallo de la IA nunca deje la pantalla
vacía.

---

## Descripción

Change OpenSpec `add-dotnet-assist-and-recommendation-endpoints` / **C34**, épica **EP15 — Venta
Asistida, Sustitutos y Agentes**. Marcado 🔴 en la ruta crítica y en la lista de *nunca se recorta*
del §6 del plan. Prerrequisitos: **C15** (el patrón de hidratación), **C26** (sustitutos) y
**C30a** (la forma de la respuesta), todos archivados.

Es **el primer consumidor .NET** de `POST /v1/assist/sale` y de `POST /v1/retrieval/substitutes`.
Cuatro changes han movido el contrato desde que se escribió la ficha —C30a, C30b, C31 y C32b—, y el
lado Python está entero: tres modos, agrupado por familia, avisos estructurales, citas con
`claim_scope`, argumentario con puerta numérica y enrutador de intención. **En .NET no hay nada**
salvo un presupuesto de 5 s reservado y sin usar, y un comentario que reserva el sitio del cliente.

Aplica la **regla de una frase del §6.2** del diseño en el punto donde más se nota: *Python calcula
parecidos y redacta; .NET calcula números y decide*. Aquí .NET decide qué miembros de la familia
existen en esa tienda, cuántas unidades hay, si hay stock crítico, qué sustitutos se pueden vender
hoy y con qué precio se escribe el argumentario.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado | Evidencia |
|---|---|---|
| `POST /v1/assist/sale` con M2 (pieza) y M3 (pieza y pregunta) | ✅ real desde C30a, genera desde C30b con `assist/v3` | [`api/routers/assist.py`](../../../ai-service/src/jbg_ai/api/routers/assist.py) |
| `POST /v1/retrieval/substitutes` | ✅ real desde C26; devuelve **la ventana entera**, `min(3·top_k, 60)` | [`retrieval/substitutes.py`](../../../ai-service/src/jbg_ai/retrieval/substitutes.py) |
| `AssistedSearchService` (C15): autorizar, llamar, hidratar, truncar, degradar | ✅ el patrón a copiar | [`AssistedSearchService.cs`](../../../backend/src/JoiabagurPV.Application/Services/AssistedSearchService.cs) |
| `IAssistedSearchRepository.HydrateAsync(ids, posId)` | ✅ una consulta; conserva cantidad 0 | [`AssistedSearchRepository.cs`](../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/AssistedSearchRepository.cs) |
| `IProductFamilyRepository.GetByProductIdAsync` | ✅ la familia de .NET, ordenada por `SortOrder` | [`ProductFamilyRepository.cs`](../../../backend/src/JoiabagurPV.Infrastructure/Data/Repositories/ProductFamilyRepository.cs) |
| Métodos de assist y de sustitutos en `IAiGatewayClient` | ❌ **cero** | [`IAiGatewayClient.cs`](../../../backend/src/JoiabagurPV.Application/Interfaces/IAiGatewayClient.cs) |
| Cliente con nombre para la ruta generativa | ❌ **cero**; `AssistTimeoutMs = 5000` reservado y sin usar | [`AiGatewayOptions.cs`](../../../backend/src/JoiabagurPV.Application/Configuration/AiGatewayOptions.cs) |
| Un 422 de Python distinguible de «IA caída» | ❌ `TranslateStatus` lo convierte en `AiUnavailableException` | [`AiGatewayClient.cs`](../../../backend/src/JoiabagurPV.Application/Services/AiGatewayClient.cs) |
| Definición de «stock bajo» | ⚠️ **dos incompatibles**: `max(10 %, 5)` en ventas, `≤ 2` en el dashboard | [`StockValidationService.cs`](../../../backend/src/JoiabagurPV.Application/Services/StockValidationService.cs), [`DashboardService.cs`](../../../backend/src/JoiabagurPV.Application/Services/DashboardService.cs) |
| Generación en la demo | ❌ sin credencial en `compose.demo.yaml`: sirve `pitch: ""` | [`DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md) |

### Lo que la exploración refutó de la ficha

La exploración del 2026-09-21 dejó **nueve hallazgos, catorce decisiones y cinco mediciones
reproducibles** en [`c34-exploration-decisions.md`](../../Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md).
Los cuatro que más pesan en esta historia:

1. **Los marcadores no dicen de qué pieza son.** En M2 y M3 da igual, porque hay una sola pieza. En la
   consulta libre y en el agente, el argumentario habla de varias con los mismos dos tokens. La
   anotación del 14 de septiembre que daba a C34 la ruta de la consulta libre (*«ninguna hidratación
   nueva»*) es **falsa**, y por eso esa ruta **no entra aquí**.
2. **Con 5 s de timeout, .NET tiraría respuestas que Python iba a entregar**: el 7,5 % de las
   peticiones pasa de 5 s sólo en llamadas al proveedor, y el peor caso por construcción es 2 × 4 s.
3. **`family_has_variants` sería falso en el 19,2 % de las piezas ancladas con familia** una vez
   quitados los miembros que la tienda no lleva.
4. **Con `top_k = 5`, en Fornells el 71,1 % de las piezas no llena una página de sustitutos**; con
   `top_k = 20`, el 7,1 %.

---

### Alcance de esta historia (sí)

1. **`POST /api/ai/products/{productId}/sales-assist`** con cuerpo `{pointOfSaleId, question?}`: M2
   sin pregunta, M3 con ella.
2. **`GET /api/ai/products/{productId}/substitutes?pointOfSaleId=&pageSize=`**.
3. **Autorización y comprobación previa**: 403 para un operario sin asignación al punto de venta, y
   404 si la pieza anclada no está en ese punto de venta. En los dos casos, **antes** de llamar a la IA.
4. **Hidratación del grupo**: miembros que la tienda lleva, en el orden de Python, con precio, cantidad
   y foto de .NET.
5. **Resolución de marcadores** contra la pieza anclada, con **retirada del argumentario —no de la
   respuesta—** si queda cualquier `{{…}}`.
6. **Los dos avisos de stock** (`stock_critical`, `family_members_out_of_stock`) y el **recálculo de
   `family_has_variants`**.
7. **Sustitutos**: ventana máxima en una llamada, exclusión de lo que no tiene stock en el punto de
   venta, paginado sin reordenar y **cuatro resultados vacíos distinguibles**.
8. **Degradación**: con la IA caída, el card sale con la pieza, su familia leída de .NET y los avisos
   de stock, sin argumentario.
9. **Cliente del gateway**: dos métodos tipados, cliente `ai-assist` a 10 s sin reintento en timeout y
   con circuito propio, y un 422 que deja de leerse como «IA no disponible».
10. **Operación**: límite de peticiones propio, interruptor por punto de venta, política de logs.
11. **Última tarea: la generación encendida en la demo**, con los cuatro pasos de `DEFERRED_TASKS.md`
    más la configuración .NET de la demo y una nueva medición de memoria.

### Fuera de alcance (no)

1. **La consulta libre sin pieza (M1)**: sus marcadores no tienen pieza a la que referirse. El §15.12
   del diseño sigue siendo cierto. El arreglo, que es de Python, queda identificado y no hecho.
2. **La ruta del agente, `POST /v1/assist/agent`**: el mismo problema, y sin pantalla de conversación
   que la consuma. Su política de timeout y circuito sigue diferida.
3. **Ninguna pantalla**: el card, la caja de pregunta y la tabla de copy de los códigos son de **C36**.
4. **Ningún cambio en `ai-service/`**: `openapi.json` queda **idéntico byte a byte**.
5. **Complementarios**: la ruta `.../recommendations` salió con C27 el 12 de septiembre.
6. **Sin migración de EF Core** y sin tabla nueva: familias, inventario y precios ya existen.
7. **El validador .NET de cifras no verificadas** (`Response_WithUnverifiedNumber_IsRejected`) es de
   C38.
8. **Sin caché** de respuestas de la IA.
9. **Ni `terraform/` ni `.github/workflows/`**: la activación de la demo es de `deploy/demo/` y
   `compose.demo.yaml`.

---

### Decisiones de diseño ya acordadas

Las cuatro marcadas **«cerrada»** se tomaron con el desarrollador en la sesión de exploración; el resto
son la recomendación de la exploración, aceptada por defecto. Las alternativas descartadas de cada una
están en el [informe](../../Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md).

| # | Decisión | Razón |
|---|---|---|
| **D-A** *(cerrada)* | **Sólo las dos rutas del card**; ni M1 ni el agente | Por H1: en esos dos modos el argumentario habla de varias piezas y los marcadores no tienen pieza a la que referirse |
| **D-B** *(cerrada)* | **`POST` con `question` en el cuerpo** para el argumentario, `GET` para los sustitutos, y `pointOfSaleId` **obligatorio** en las dos | Texto libre del cliente en una URL acaba en el log de nginx (§15.11 del diseño y D-I de C30). Un `GET` se puede precargar y cada precarga es una llamada de pago. Precedente de C15 |
| **D-C** | Los marcadores se refieren a **la pieza anclada**: `{{price}}` como «39,90 €» y `{{stock}}` como **entero** | El 88,3 % de 213 argumentarios de C30b escribe `{{stock}}` como número («tenemos {{stock}} en tienda»). «N unidades» rompe 4 más; una etiqueta rompe el 88 % |
| **D-D** | **Un marcador sin resolver retira el argumentario, no la respuesta**; el argumentario resuelto **nunca se loguea** | Es la política que ya aplican las puertas de C30b, y la S4 del máster pide declarar la política. El texto resuelto lleva el precio real |
| **D-E** *(cerrada)* | **Pieza anclada con stock 0**: en M2 se retira el argumentario; en M3 se sustituye el 0 | 147 de 213 escriben «disponible por {{price}}» antes de saber el stock. En M3 la respuesta de conocimiento vale igual para una pieza agotada. Pasa en el **6,5 %** de las piezas ancladas |
| **D-F** | Cliente **`ai-assist` a 10 s**, **sin reintento en timeout** y con circuito propio; sustitutos en **`ai-retrieval`**; **`AiRequestRejectedException`** para el 422 | El presupuesto de fuera ≥ el peor caso de dentro (2 × 4 s): con 5 s se corta el 7,5 %. Reintentar un timeout son 20 s y dos llamadas de pago |
| **D-G** | El grupo es **el de Python, hidratado**; se quitan los miembros que la tienda no lleva, se **conserva el orden** y se **recalcula `family_has_variants`** | El 19,2 % saldría falso sin el recálculo. Es el patrón de C15 y el contrato que C30a construyó para C34 |
| **D-H** | **`stock_critical` = 1 o 2 unidades**, configurable; **el 0 es un estado**, no un aviso | Coincide con el *bucket* `1-2` / `ultimas_unidades` de C32a y con el panel del dashboard. Salta en el 4,2 %, frente al 14,4 % de `≤ 5` |
| **D-I** | Sustitutos con **`top_k = 20`** en una sola llamada, filtro «en la tienda ∧ qty > 0», orden intacto y **cuatro `outcome`** | Ventana 15: el 71,1 % de Fornells no llena página. Ventana 60: el 7,1 %. Precedente de *«the three empty outcomes are distinguishable»* de C15 |
| **D-J** | **Degradación**: pieza anclada + familia de .NET + avisos de stock, sin argumentario ni citas | La confirmación de variante es lógica de negocio, no de IA, y las familias son de .NET (§6.2) |
| **D-K** | Contrato hacia el frontend con **`pitchStatus` enumerado** | La codificación de dos campos de C30b era el precio de no mover un contrato congelado. Éste no lo está |
| **D-L** | Se **extiende `IAiGatewayClient`** y se extrae una **clase base de test** para los siete dobles; integración con **gateway falso e interruptor encendido** | Los tests de integración de C15 no llegan nunca al gateway (H8) |
| **D-M** | Límite de peticiones propio (~10/min/usuario), interruptor por POS propio, **sin caché**, la pregunta sólo a nivel `Debug` | Coste de LLM y cuota de tokens por minuto medida en C32b |
| **D-N** *(cerrada)* | **Encender la generación en la demo es la última tarea**; la zona gana `deploy/demo/` y `compose.demo.yaml` | Sin ella la sustitución de marcadores no se puede enseñar, y `pitchStatus` sería siempre `not_generated` |

### Referencias

- Change de OpenSpec: `openspec/changes/add-dotnet-assist-and-recommendation-endpoints/` (C34), rama
  `c34-add-dotnet-assist-and-recommendation-endpoints`
- Ticket: [T-AIENG-034](../../../openspec/changes/archive/2026-09-22-add-dotnet-assist-and-recommendation-endpoints/ticket.md)
- Informe de exploración: [`c34-exploration-decisions.md`](../../Proyecto%20Final%20AIEng/informes/c34-exploration-decisions.md)
- Ficha del plan: [§3 · C34](../../Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md) y la
  nota del **§0 del 2026-09-21**
- Diseño RAG: [§6.2, §6.4, §7.6, §7.7, §15.10, §15.12](../../Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- Capabilities consumidas: [`assist-generation`](../../../openspec/specs/assist-generation/spec.md),
  [`substitutes-retrieval`](../../../openspec/specs/substitutes-retrieval/spec.md)
- Capability que se modifica: [`ai-gateway-client`](../../../openspec/specs/ai-gateway-client/spec.md)
- Precedente directo: [`ai-assisted-search`](../../../openspec/specs/ai-assisted-search/spec.md) y
  [HU-AIENG-015](HU-AIENG-015.md)
- Reglas de acceso: [`access-control`](../../../openspec/specs/access-control/spec.md)
- Historias anteriores de la cadena: [HU-AIENG-026](HU-AIENG-026.md) · [HU-AIENG-030a](HU-AIENG-030a.md)
  · [HU-AIENG-030b](HU-AIENG-030b.md) · [HU-AIENG-031](HU-AIENG-031.md)
- Épica: [EP15 — Venta Asistida, Sustitutos y Agentes](../../epicas.md)

---

## Criterios de Aceptación

### Escenario 1: El argumentario de una pieza llega con su precio y su stock reales

- **Dado que** un operario asignado a un punto de venta pide el argumentario de una pieza que esa
  tienda lleva, con 3 unidades,
- **Cuando** la IA devuelve un argumentario con los dos marcadores,
- **Entonces** el argumentario llega con el precio de catálogo de la pieza en formato «39,90 €» y con
  un «3» en el lugar del stock,
- **Y** ningún marcador queda en el texto,
- **Y** el estado del argumentario es «generado»,
- **Y** el precio y la cantidad de cada miembro del grupo vienen del catálogo y del inventario de esa
  tienda, nunca de la respuesta de la IA.

### Escenario 2: Una pregunta sobre la pieza devuelve citas que distinguen su alcance

- **Dado que** el operario escribe una pregunta sobre la pieza que tiene delante,
- **Cuando** pide la asistencia con esa pregunta,
- **Entonces** la pregunta viaja en el cuerpo de la petición y nunca en la URL,
- **Y** la respuesta trae las citas que el argumentario usó, cada una con su alcance —hecho general o
  compromiso de la casa—, su documento y su sección,
- **Y** si el corpus no cubre la pregunta, la respuesta lo declara con el código que lo dice en vez de
  aparentar que la ha contestado.

### Escenario 3: Un marcador que no se puede resolver retira el argumentario y no la respuesta

- **Dado que** la IA devuelve un argumentario con un marcador que no es ninguno de los dos conocidos,
- **Cuando** se compone la respuesta,
- **Entonces** el argumentario **no** se entrega y su estado dice que se retiró por un marcador sin
  resolver,
- **Y** los grupos, los avisos y las citas **sí** se entregan,
- **Y** la plantilla cruda no aparece en ningún campo de la respuesta ni en ninguna línea de log.

### Escenario 4: Una pieza agotada no recibe un argumento de venta, pero sí la respuesta a su pregunta

- **Dado que** la pieza anclada tiene 0 unidades en el punto de venta,
- **Cuando** se pide su argumentario **sin pregunta**,
- **Entonces** el argumentario se retira con el estado que dice que la pieza está agotada,
- **Y** el miembro anclado viene marcado como sin stock, que es lo que dispara el bloque de sustitutos
  del card,
- **Y cuando** se pide **con pregunta**, el argumentario se entrega con un «0» en el lugar del stock.

### Escenario 5: Los avisos de stock los calcula .NET, y el de variantes se ajusta a la tienda

- **Dado que** la pieza anclada tiene 2 unidades, otro miembro de su familia está en la tienda con 0 y
  un tercero no está en esa tienda,
- **Cuando** se sirve la asistencia,
- **Entonces** la respuesta trae el aviso de stock crítico y el de miembros de la familia sin stock,
- **Y** ninguno de los dos procede de la respuesta de la IA,
- **Y** el miembro que la tienda no lleva **no** aparece en el grupo,
- **Y** si tras quitarlo queda un solo miembro, el aviso de que la familia tiene variantes **no**
  aparece.

### Escenario 6: Los permisos se comprueban antes de gastar una llamada de pago

- **Dado que** un operario pide la asistencia para un punto de venta que no tiene asignado,
- **Cuando** llega la petición,
- **Entonces** se responde 403,
- **Y** no se hace ninguna llamada a la IA,
- **Y cuando** el punto de venta es suyo pero la pieza no está en esa tienda, se responde 404, también
  sin llamar a la IA,
- **Y** una petición sin punto de venta, o con uno inactivo, se rechaza como inválida.

### Escenario 7: Los sustitutos que se ofrecen se pueden vender hoy en esa tienda

- **Dado que** la IA devuelve una ventana de candidatos en la que algunos no tienen stock en el punto
  de venta y otros no están en esa tienda,
- **Cuando** se piden los sustitutos de una pieza,
- **Entonces** sólo aparecen candidatos con stock en esa tienda,
- **Y** conservan el orden en que la IA los devolvió,
- **Y** no se devuelven más que los de la página pedida,
- **Y** la IA recibió **una sola** petición, con la ventana máxima.

### Escenario 8: Los cuatro vacíos de los sustitutos se distinguen

- **Dado que** se piden sustitutos de una pieza,
- **Cuando** la IA contesta y ningún candidato tiene stock en la tienda,
- **Entonces** el resultado dice «ninguno con stock»,
- **Y cuando** la IA responde que la pieza no está en su índice, el resultado dice «pieza no indexada» y
  **no** «IA no disponible»,
- **Y cuando** la IA no responde, el resultado dice «IA no disponible»,
- **Y** en ninguno de los tres casos la respuesta es un error del servidor.

### Escenario 9: Con la IA caída el card sale igual, sin argumentario

- **Dado que** el circuito de la IA está abierto, o la llamada supera su presupuesto de tiempo,
- **Cuando** se pide la asistencia de una pieza que pertenece a una familia,
- **Entonces** la respuesta es correcta y declara que la IA no está disponible,
- **Y** trae la pieza y los miembros de su familia que la tienda lleva, leídos del catálogo, con sus
  precios, cantidades y el aviso de variantes si procede,
- **Y** trae los avisos de stock,
- **Y** no trae argumentario ni citas.

### Escenario 10: Un timeout no se reintenta, y el presupuesto cubre el peor caso de la IA

- **Dado que** la llamada de asistencia supera su presupuesto de tiempo,
- **Cuando** el cliente la gestiona,
- **Entonces** se hizo **una sola** petición HTTP,
- **Y** el presupuesto configurado nunca es menor que el peor caso declarado de las llamadas al
  proveedor del servicio de IA, cosa que se comprueba al arrancar,
- **Y** un circuito abierto en la asistencia no impide que la búsqueda asistida siga funcionando.

### Escenario 11: Nada de lo que el cliente pregunta ni de lo que se le responde queda en un log

- **Dado que** se ha servido una asistencia con pregunta y con argumentario generado,
- **Cuando** se revisan los logs del backend,
- **Entonces** el argumentario ya resuelto no aparece en ninguna línea, a ningún nivel,
- **Y** la pregunta sólo aparece a nivel de depuración,
- **Y** sí aparecen el identificador de traza, el estado del argumentario, su longitud, los
  identificadores de las citas, los códigos de aviso y los contadores del embudo de sustitutos.

### Escenario 12: La demo enseña el argumentario

- **Dado que** la demo se ha desplegado con la credencial de generación y la configuración de C34,
- **Cuando** un operario de demo pide el argumentario de una pieza,
- **Entonces** el argumentario llega generado, con el precio y el stock reales,
- **Y** el log del servicio de IA declara qué credencial está en vigor sin mostrarla,
- **Y** la memoria del contenedor de IA se ha vuelto a medir y queda dentro de su tope.

### Escenario 13: Fuera de alcance explícito — ni consulta libre, ni agente, ni contrato de Python

- **Dado que** este change sólo expone las dos rutas del card,
- **Cuando** se revisa lo entregado,
- **Entonces** no existe ninguna ruta .NET para la consulta libre ni para el agente,
- **Y** el contrato de `jbg-ai` es **idéntico byte a byte** al de antes del change,
- **Y** no hay migración de EF Core,
- **Y** la búsqueda asistida de C15 se comporta exactamente igual que antes.

---

## Notas adicionales

**Actor.** Desarrollador del proyecto, igual que en C15. El operario es el beneficiario final, pero la
pantalla llega con **C36**: esta historia deja listo lo que ese card lee. La aceptación se comprueba con
tests de integración y con la demo, no con una pantalla.

**Encaje con los apuntes del máster.** Los números fuera del modelo coinciden con S11 (*«agregar antes
de generar»*) y S14 (*«la divergencia se calcula, no se opina»*); el proyecto va más lejos, porque la
cifra **no llega nunca** al modelo, y eso se declara como decisión. La política de fallo por partes es la
de S4 (*«cada guardrail debe declarar su política»*) y de S11 (`gate_line`). El post-filtrado
instrumentado es el aviso de S9 (*«sin instrumentación, no te enteras»*). **Dos desviaciones
conscientes**: no se reintenta en timeout (S9 reintenta con 30 s de presupuesto, y un mostrador no los
tiene) y no se loguea la respuesta literal (S3 lo recomienda; D-I de C30 lo prohíbe).

**Limitaciones conocidas que se declaran y no se cierran.**

1. **El 11,7 % de los argumentarios escribe `{{stock}}` donde no encaja un número** («y en
   {{stock}}»). Arreglarlo exige que el modelo sepa qué tipo de sustitución recibirá, y eso es un cambio
   de prompt con su pasada de medición.
2. **Cuando .NET retira un argumentario, las citas son sólo las que ese argumentario usó**, un
   subconjunto de las que fundamentaron la respuesta. Cuando lo retira Python, vuelven todas. .NET no
   puede reconstruir la diferencia.
3. **Una familia editada tarda en verse** hasta la siguiente sincronización del índice, porque el grupo
   nominal lo construye Python. El card degradado lee la familia de .NET y no tiene ese desfase.
4. **La cuota de tokens por minuto** de la organización, y no el dinero, limita cuántos operarios de la
   demo pueden generar a la vez.
5. **El presupuesto de 10 s** sale de las constantes de Python y de una medición tomada a través de un
   interceptor TLS. La latencia real de extremo a extremo se mide durante la implementación.

**Change de OpenSpec por el que se implementa.**
`openspec/changes/add-dotnet-assist-and-recommendation-endpoints/`, rama
`c34-add-dotnet-assist-and-recommendation-endpoints`.

---

## Tareas

1. **Puerta de entrada**: línea base de la suite de backend **por nombres de test** (`git stash push
   -u`, correr, `git stash pop`), `openspec validate --all --strict` en verde y `sha256` de
   `ai-service/openapi.json` anotado para comprobar al final que no se ha movido.
2. **DTO del contrato de Python** para assist y sustitutos, sin `pos_id` en el cuerpo, y sus filas en la
   tabla de deriva de contrato.
3. **Cliente del gateway**: `AssistSaleAsync` y `SubstitutesAsync`, cliente con nombre `ai-assist` con su
   presupuesto, su circuito y sin reintento en timeout, la excepción del 422 y la validación al arranque
   del suelo de presupuesto.
4. **Clase base de test** para los siete dobles de `IAiGatewayClient`.
5. **Opciones** del card: interruptor por punto de venta, umbral de stock crítico, ventana y página de
   sustitutos, límite de peticiones.
6. **Servicio de asistencia**: autorizar, comprobar la pieza, llamar, hidratar el grupo, calcular avisos,
   resolver marcadores, retirar lo que toque, degradar.
7. **Servicio de sustitutos**: autorizar, comprobar la pieza, ventana máxima, filtrar, paginar, los
   cuatro resultados y el embudo en el log.
8. **Controlador** con las dos rutas, validación explícita y política de límite de peticiones.
9. **Tests**: unitarios de los dos servicios y del cliente, e integración con Testcontainers y gateway
   falso.
10. **Specs**: capability nueva del card y `## MODIFIED` de `ai-gateway-client`, con
    `openspec validate --all --strict` en verde.
11. **Medición de latencia de extremo a extremo** de M2 y M3 en Docker Compose, para confirmar o bajar
    los 10 s sin romper el suelo.
12. **Demo**: los cuatro pasos de `DEFERRED_TASKS.md`, la configuración .NET de la demo, la
    comprobación del log de credencial y la nueva medición de memoria.
13. **Documentación**: `Documentos/epicas.md`, plan de changes, `backend/README.md` (endpoints y
    matriz de autorización), `Documentos/arquitectura.md` y `modelo-c4.md` si cambian las integraciones,
    `deploy/demo/README.md`, `openspec/DEFERRED_TASKS.md` y la tarea de C30b que se cierra.

---

## Estimaciones y atributos de priorización

| Atributo | Valor |
|---|---|
| Puntos de historia | _Pendiente_ — a fijar en refinamiento |
| Impacto en usuario / valor de negocio | **5/5** — es el primer punto en el que la capa de generación llega al mostrador con cifras de verdad. Sin él, C30a, C30b y C31 sólo se demuestran en el arnés |
| Urgencia | **5/5** — **bloquea a C36** y aparece en los prerrequisitos de **C38**. El §6 del plan lo marca como *nunca se recorta* |
| Complejidad / esfuerzo | **4/5** — dos rutas, un cliente nuevo con su política, hidratación y degradación, pero **sobre un patrón que C15 ya dejó probado** y sin migración ni cambio de contrato de Python |
| Riesgos | **El presupuesto de 10 s queda largo o corto** en el despliegue real (mitigado por la tarea 11 y por el suelo validado al arranque). **La demo agota la cuota de tokens por minuto** con varios operarios a la vez (se comprueba y se declara). **Un test de integración que no llega al gateway** da verde en vacío, como pasó en C15 (mitigado por D-L y por un test que falla si el doble no se invoca). **La memoria del `t3.small`** con la ruta generativa encendida (se mide en la tarea 12) |
| Dependencias | **C15**, **C26** y **C30a** archivados; consume también lo que dejaron **C30b** y **C31**. **Bloquea a C36** y aparece en los prerrequisitos de **C38**. **No se abre a la vez que C15**: comparten el servicio de búsqueda |

---

## Preguntas Abiertas

| # | Pregunta | Opción por defecto si no hay respuesta antes del *apply* |
|---|---|---|
| **Q-1** | ¿Una capability nueva para las dos rutas, o dos? | **Una**, `ai-sales-assist`: las dos rutas son el mismo card, comparten autorización, comprobación de pieza e interruptor |
| **Q-2** | ¿El interruptor por punto de venta apaga las dos rutas o sólo el argumentario? | **Las dos**: el card es uno. Con el interruptor apagado, la asistencia responde degradada y los sustitutos con «IA no disponible», y el log dice que fue el interruptor |
| **Q-3** | ¿Los sustitutos comparten el límite de peticiones de la búsqueda? | **Sí**: no llaman al LLM. El argumentario tiene el suyo propio |
| **Q-4** | ¿Qué suelo exacto valida el arranque para `AssistTimeoutMs`? | **8.000 ms**, que es `MAX_PITCH_PROVIDER_CALLS × PITCH_TIMEOUT_SECONDS` con los valores por defecto de Python, citados en el mensaje de error |
| **Q-5** | ¿Un fallo de transporte en `ai-assist` se reintenta? | **Sólo si la conexión no llegó a abrirse** (`HttpRequestError.ConnectionError`): ahí no se gastó ninguna llamada al proveedor. Cualquier otro fallo, no |
| **Q-6** | ¿La pieza anclada va primera en el grupo? | **No se reordena**: se conserva el orden de Python y la pieza lleva una marca propia |
| **Q-7** | ¿Se expone el uso de tokens de la IA al frontend? | **No.** Se loguea con el modelo, para el coste; la pantalla no lo necesita |
