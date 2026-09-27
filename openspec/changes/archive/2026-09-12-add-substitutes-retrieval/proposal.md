## Why

El sistema sabe buscar y **no sabe qué ofrecer cuando la respuesta correcta no está disponible**,
que es el momento exacto en el que el mostrador pierde la venta.

`POST /v1/retrieval/substitutes` existe en el contrato congelado desde C02 y hoy responde **501**.
No es un hueco tácito: `vector-retrieval` lo **obliga por escrito** —*«`POST /v1/retrieval/substitutes`
MUST keep returning 501 when stubs are off»*, con su propio escenario *«Substitutes stay
unimplemented»*—, así que la ruta no puede implementarse sin mover esa spec. Es además el último 501
cerrable del servicio: `/v1/inventory/propose` también responde 501, pero su rama se anuló el
2026-08-31 y eso ya está declarado como limitación.

Cerrarlo es lo que hace real la tool `buscar_sustitutos` del agente de venta de C32, y el diseño ya
escribió la regla que lo exige: *«una tool que devuelve error es peor que una tool ausente»*.

**Esto no es «otra búsqueda».** Es la misma búsqueda con el filtro que sólo se puede escribir cuando
ya se sabe qué pieza ha fallado: con el ancla en texto hay que *adivinar* que el cliente quería una
talla M de plata; con el ancla en `product_id` se **sabe**. Y como el embedding de origen ya está
almacenado, la capacidad se entrega **sin una sola llamada al proveedor**.

**La exploración midió seis cosas antes de escribir esto y refutó tres puntos de la ficha del plan.**
Evidencias en
[`c26-exploration-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c26-exploration-measurements.md):

- **«Misma familia primero» está invertida.** La familia es, por construcción, el conjunto de piezas
  que se diferencian **justo en el atributo que descalifica** —la talla—. Para `SKU13 Anillo erizo de
  mar M` el top-5 del vector puro **no contiene un solo sustituto usable**: los tres primeros son el
  mismo anillo en talla L, S y XL, el cuarto es un **colgante**, y el primero utilizable es el #6.
- **Pero la familia no se puede excluir.** El mejor sustituto de `SKU159 Anillo lapislázuli mediano`
  es su hermano `mediano oro` —**misma talla, otro material**— y es el **#1**. La pertenencia a
  familia es **ortogonal**; el discriminante es la talla, y cruza su frontera en las dos direcciones.
  Lo confirma `criterion.md`, que ya clasificaba «falla la talla que la consulta nombró» como
  **grado 1 — segunda opción**, no como respuesta.
- **La exclusión por falta de stock no pertenece aquí.** Estaba especificada dos veces —en esta ficha
  y en la de C34— y la versión correcta es la de .NET, que es la autoridad sobre el stock. El
  invariante vigente es que la disponibilidad **degrada y nunca elimina**.
- **`style_similarity` no tiene dato:** sólo **1 de 404** productos reales tiene algún candidato del
  mismo tipo con el que compartir etiqueta de estilo, frente al **97,8 %** que lo tiene por material.
- **No cabe abstención:** todo producto del catálogo tiene vecino a menos de **0,255** y el rango de
  los productos sin familia **contiene** el de los que la tienen — la misma contención que impidió a
  C25 re-fijar su umbral escalar.

## What Changes

- **Se implementa el motor de sustitutos** en un módulo nuevo `retrieval/substitutes.py`, y la ruta
  deja de responder 501 cuando los stubs están apagados. El stub de C02 sigue sirviendo la ruta en
  modo stub, para que los tests de contrato committeados sigan en verde.
- **El universo de candidatos se restringe por `piece_type`**, que es el único filtro duro: un anillo
  no sustituye a un colgante. Se excluyen la propia pieza origen y los identificadores que el cuerpo
  pida excluir.
- **El orden lo componen tres términos continuos**: la similitud del coseno sobre el embedding
  almacenado, una **degradación por talla distinta** y la **degradación por disponibilidad** ya
  calibrada. Ningún término es un bloque entero, porque un bloque entero particiona en lugar de
  desempatar.
- **La talla degrada de forma suave y sólo cuando hay dato en los dos lados.** Si la pieza origen o
  el candidato no declaran talla, el término es inerte: ausencia no es desajuste.
- **La familia no ordena, pero no se pierde.** Entra en el conjunto de candidatos y se declara en las
  señales; ninguna variante viva de la familia puede quedar fuera del conjunto devuelto.
- **Cada candidato explica por qué está ahí**, con las señales del contrato congelado más una lista
  de motivos legible que transporta lo que ese contrato no puede expresar — señaladamente la talla.
- **Una señal sin dato se declara en vez de fingirse**: un solape de estilo igual a cero sobre piezas
  sin etiquetas nunca puede leerse como «estilos distintos».
- **El endpoint no abstiene**, por decisión medida y no por aplazamiento.
- **No se llama al proveedor de embeddings** en la ruta.
- **Las consultas de sustituto del golden set se anclan a un producto origen explícito** y se miden
  en una **rebanada propia**, con al menos un producto origen sin familia. La tabla de ablations
  publicada no se toca.

**Lo que explícitamente no cambia:** el contrato congelado (`ai-service/openapi.json` no se
regenera), el modelo de datos (sin migración), la exclusión por stock (queda en C34) y los pesos
calibrados por C25.

## Capabilities

### New Capabilities
- `substitutes-retrieval`: el motor de sustitutos por falta de stock — universo restringido por tipo
  de pieza, orden por similitud sobre el embedding almacenado con degradación suave por talla y por
  disponibilidad, señales y motivos por candidato, ausencia de abstención declarada, y la rebanada de
  evaluación anclada por producto origen.

### Modified Capabilities
- `vector-retrieval`: cae la obligación de que `POST /v1/retrieval/substitutes` siga devolviendo 501
  con los stubs apagados, y con ella su escenario *«Substitutes stay unimplemented»*. Se sustituye por
  la obligación simétrica —la ruta responde 200 o un error explícito, nunca 501 remitiendo a un change
  posterior— conservando intactas las tres garantías vecinas: el stub de C02 en modo stub, el
  snapshot de OpenAPI congelado y que Python no lee el esquema `public`.

## Impact

**Código afectado** — todo dentro de `ai-service/`:

| Zona | Qué pasa |
|---|---|
| `src/jbg_ai/retrieval/substitutes.py` | **Nuevo.** Orquestación, composición del orden y construcción de señales |
| `src/jbg_ai/retrieval/search.py` | Sentencia nueva: vecinos por embedding almacenado, con filtro por tipo de pieza y la proyección leída como señal |
| `src/jbg_ai/retrieval/ports.py` | Dos métodos nuevos en el puerto: leer el documento origen y buscar sus vecinos |
| `src/jbg_ai/retrieval/fusion.py` | Sólo el docstring: predice un consumidor que no existirá, porque con una sola lista no hay nada que fusionar |
| `src/jbg_ai/api/routers/retrieval.py` | Se retira la guarda de no-implementado de **esa** ruta |
| `src/jbg_ai/config/settings.py` | Un ajuste nuevo para el peso de la talla, opcional al arranque |
| `src/jbg_ai/evals/`, `evals/golden/` | Rebanada de evaluación, anclaje por producto origen y una consulta nueva sin familia |
| `tests/` | Doce escenarios nuevos más los de perímetro |

**Sin impacto**: `backend/`, `frontend/`, `terraform/`, `.github/workflows/`, `ai-service/openapi.json`,
migraciones de Alembic y de EF Core, y el modelo de datos de `Documentos/modelo-de-datos.md`.

**Contrato y compatibilidad**: ninguna ruptura. El único cambio observable desde fuera es que una ruta
que devolvía 501 pasa a devolver 200. `test_openapi_snapshot_is_stable` es la puerta que lo verifica.

**Dependencias**: C22 (proyección por punto de venta) y C25 (fusión y señales de negocio), ambos
archivados. Este change desbloquea **C34** —y con él C36— y hace real la tool `buscar_sustitutos` de
**C32**.

**Riesgo principal**: que el término de talla se implemente como bloque entero y destierre a los
hermanos de familia al final de la lista. Es el fallo que C25 midió con la rotación, y el change lo
contiene con un escenario que exige que sigan dentro de la ventana visible.
