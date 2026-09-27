## Context

`POST /v1/assist/sale` se congeló en C02 con los otros nueve `/v1` y **nunca se implementó**:
[`routers/assist.py`](../../../../ai-service/src/jbg_ai/api/routers/assist.py) llama a
`require_stub_mode` y responde `501` con stubs apagados. El fixture de
[`stubs/responses.py`](../../../../ai-service/src/jbg_ai/stubs/responses.py) fabrica familias
sintéticas y una frase con placeholders.

Lo que sí está construido, y este change **consume sin modificar**:

```
C21/C25/C25bis                C22                    C23                     C26
retrieve_products()      resolve_scope()        search_knowledge()     retrieve_substitutes()
fusión en dos etapas     qty_bucket (interno)   KnowledgeCitation × 10          │
match_reasons reales     nunca al cable         umbral 0,51 calibrado          │
      │                        │                      │                        │
      └────────────┬───────────┴──────────┬───────────┘                        │
                   ▼                      ▼                                    │
        ╔═════════════════════════════════════════════════════════╗            │
        ║  assist/  ← NO EXISTE. Es la zona de este change         ║            │
        ╚══════════════════════════╤══════════════════════════════╝            │
                                   ▼                                           │
                    POST /v1/assist/sale   ── hoy 501 / fixture                │
                                   │                                           │
        ╔══════════════════════════▼══════════════════════════════╗            │
        ║  C34 (.NET) ← NO EXISTE · IAiGatewayClient sin assist    ║◀───────────┘
        ╚═════════════════════════════════════════════════════════╝
```

**La restricción que gobierna el diseño no es técnica, es de oportunidad.** El contrato congelado
no puede servir a su consumidor —`family_id` obligatorio contra un catálogo donde el ~58 % no tiene
familia, y `query` obligatoria contra un consumidor anclado a pieza— y hoy la ruta tiene **cero
consumidores**. Renegociarlo ahora cuesta cero y a partir de C34 no.

Cifras del árbol, medidas y citadas en
[`c30-exploration-decisions.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30-exploration-decisions.md):

| Dato | Valor | Fuente |
|---|---|---|
| Productos con familia | 486 de ~1.168 (**~42 %**) | C18b: 156 familias / 486 miembros |
| Corpus de conocimiento | **32 documentos, 161 fragmentos** | C23 |
| Fragmentos de alcance `establecimiento` | **25 de 161** (15,5 %) | C23 |
| Fichas de material canónicas | **9**, esqueleto idéntico | `materials.terms` + invariante 1:1 de C23 |
| Umbral de conocimiento | **0,51**, calibrado contra el embebedor de producción | C23 |
| Abstención, en la banda configurada | **2 de 20** fuera de dominio, **0 de 43** contestables | `settings.py`, descriptor del campo |
| Consultas fuera de dominio en el golden set | **20 de 72**, su categoría mayor | `evals/golden/queries.jsonl` |

## Goals / Non-Goals

**Goals:**

- Servir `POST /v1/assist/sale` de verdad con `STUB_MODE=false`, en **tres modos**, sobre los
  candidatos que la recuperación ya produce.
- Mover el contrato congelado **una sola vez y en bloque**, mientras el coste es cero.
- Entregar **citas resolubles con su marca de alcance** sin invocar ningún modelo, para que C30b
  sea una capa medible **contra** esta.
- Dejar el listado de miembros de familia y el filtro de conocimiento en forma de **herramienta**,
  porque C32 los necesita como tools y C34 como datos.
- Que los avisos sean **verificables como derivados de reglas**, no creíbles por convención.

**Non-Goals:**

- **El argumentario en prosa** y todo lo que arrastra: prompt versionado, cliente generativo,
  integridad referencial de lo que el modelo diga y puerta numérica. Es C30b.
- **Clasificar la intención.** Es C31 entero. Aquí la intención se **deriva de la forma de la
  petición** o se declara sin clasificar.
- **El bucle agéntico.** Es C32.
- **Los avisos de stock.** Son de C34, por autoridad sobre el dato.
- **La superficie de operario.** El parámetro de pregunta en la API .NET y la caja en la tarjeta son
  C34 y C36.
- **Recalibrar nada.** El umbral 0,51, la banda de abstención y los pesos de fusión se **consumen**.
- **Cualquier migración**, y cualquier cambio en `backend/`, `frontend/`, `enrichment/` o `prompts/`.

## Decisions

### D1 · El contrato se renegocia ahora, en un solo bloque

**Decisión.** Un único movimiento de `openapi.json`, en este change, con el perfil canónico.

```
AssistRequest    + product_id (opcional) · query pasa a opcional · validador «al menos uno»
AssistGroup        family_id → nulable · invariante: nulo ⇒ exactamente un miembro
AssistGroupMember + match_reasons
Citation           reforma: + citation_id · document_title · section_title
                            + claim_scope · doc_type · score   ·   − source
AssistResponse   + abstained · prompt_version
warnings           mismo tipo (lista de cadenas), vocabulario CERRADO de códigos
```

**Por qué.** El README de `ai-service` fija la doctrina —*«Regenerating is a contract negotiation,
not a chore»*— y el precedente es propio: **C18a y C18b regeneraron el snapshot en el mismo change
en que movieron la frontera**. La contraparte de la negociación es la misma persona, y hoy no hay
código que romper.

**Alternativas descartadas.** *(a) `family_id` sintético* (`solo:<uuid>` o el propio identificador
de producto): es una mentira en el cable, obliga a .NET y al frontend a reconocer un prefijo que
ningún esquema declara, y nada en el tipo impediría que el aviso de variantes dispare sobre un
grupo de uno — con lo que el test de C36 `should require variant confirmation when family has
multiple members` pasaría en vacío, que es la firma que este proyecto persigue desde C17.
*(b) Mover sólo el mínimo* y declarar el resto como limitación: deja la marca de alcance fuera del
cable, que es el fallo que el mecanismo entero de C23 existe para evitar, y obliga a una segunda
negociación cuando C34 ya exista. *(c) Descartar los productos sin familia*: pierde el 58 % del
catálogo.

### D2 · Tres modos con «al menos uno», y no «exactamente uno»

**Decisión.** `product_id` y `query` son ambos opcionales y se exige **al menos uno**.

| modo | `product_id` | `query` | `intent` | consumidor |
|---|---|---|---|---|
| **M1** | — | ✓ | `unclassified` | bucle de C32 · escenarios de C38 |
| **M2** | ✓ | — | `product_pitch` | C34 → tarjeta de C36 |
| **M3** | ✓ | ✓ | `unclassified` | C34 con parámetro de pregunta → caja en la tarjeta |

**Por qué.** El flujo por consulta **ya está servido** por `POST /api/ai/search` (C15) y su panel
(C16); el consumidor previsto de esta ruta expone **dos rutas ancladas a pieza**. M3 es el modo de
mejor relación valor/coste y el que hace realizable el ejemplo que el §7.7 del diseño usa por su
nombre. El precedente de «dos formas en una petición, validadas» es propio: `IndexSyncRequest` con
`full` frente a `since`.

**Alternativas descartadas.** *Exactamente uno* excluye M3. *Una ruta nueva* rompe el MUST de diez
rutas y C23 argumentó contra añadir rutas por comodidad. *Que C34 sintetice la consulta* deja el
argumentario hablando de piezas parecidas, permite que la pieza elegida no salga primera, y paga un
segundo *embedding* por un producto ya conocido.

### D3 · La intención se deriva de la forma, no de palabras clave

**Decisión.** `product_pitch` cuando hay pieza y no hay pregunta; `unclassified` en los otros dos
modos.

**Por qué.** Es estructural y por tanto no puede equivocarse, y el valor de M2 **sigue siendo
correcto después de C31**: el enrutador sustituirá `unclassified`, no `product_pitch`. Un
clasificador por palabras clave sería trabajo que C31 borra, y el repo ya pagó una vez por retirar
andamio con C25bis.

### D4 · Agrupar y avisar de variantes son dos consultas distintas

**Decisión.** La agrupación opera sobre los candidatos recuperados. El aviso `family_has_variants`
se calcula con un **método nuevo del puerto de búsqueda**, `family_roster(family_id)`, que lee
únicamente `ai.product_document`.

**Por qué.** Un producto puede pertenecer a una familia de cuatro y la recuperación devolver dos:
agrupar no puede saber de los miembros que no vinieron. Y el método sirve **dos consumidores
reales** — este aviso y la tool `listar_familia` de C32 — que es el umbral que este proyecto exige
para extraer una pieza compartida.

**Alternativa descartada.** Reusar `search`/`search_lexical` con el filtro de familia: exige un
vector de consulta y un umbral, que es semánticamente falso para «enumérame los miembros de esta
familia», y pagaría un *embedding* por un listado.

**Coste asumido y declarado.** El roster es la foto del índice **a fecha del último sync**, así que
el aviso puede quedar desfasado esa ventana. Es degradación y nunca eliminación, coherente con el
invariante del §15.10. La alternativa —pedirlo a .NET, que tiene la verdad— cruzaría la frontera en
sentido contrario para un dato de estructura de catálogo, que es del índice.

### D5 · Los avisos son códigos cerrados, y los de stock no son de aquí

**Decisión.** `warnings` conserva su tipo y pasa a llevar **vocabulario cerrado**:
`family_has_variants` y `size_label_missing`. El castellano lo escribe el frontend.
`stock_critical` y `family_members_out_of_stock` **se retiran del alcance** y pasan a C34.

**Por qué.** En Python sólo existe `qty_bucket`, y `ports.py` lo declara sin ambigüedad: *«Carried
for the availability demotion and never emitted: a bucket on the wire would be the beginning of
one»*. Además puede desfasarse minutos. Un aviso «stock crítico» con doce unidades en el cajón no
es un matiz de precisión: es la credibilidad del asistente en el mostrador. **Es el segundo caso de
la misma forma** — la exclusión por falta de stock ya migró de C26 a C34 el 12 de septiembre por
idéntico motivo.

Y los códigos hacen el invariante **verificable**: el vocabulario es cerrado y el modelo nunca lo
ve, así que `test_warnings_are_rule_derived_not_model_generated` deja de ser una afirmación de
confianza. El precedente de «códigos en el cable, copy en la capa de presentación» es literal en la
spec viva del panel: *«MUST NOT render the retriever's raw match reason values, which are
engineering vocabulary»*, con su regla de tolerar un valor desconocido con etiqueta neutra.

**Alternativas descartadas.** *Prosa castellana en Python*: produce una lista de procedencia
mezclada cuando C34 apila los suyos, indistinguible para el frontend. *Cambiar el tipo a objetos
`{code, params}`*: movimiento de esquema mayor sin necesidad.

### D6 · La citación lleva identificador resoluble y marca de alcance, y sólo cita el corpus

**Decisión.** `Citation` se reforma. Y **`citations[]` son fragmentos del corpus de conocimiento y
sólo eso**: el anclaje al catálogo se expresa con `match_reasons`.

**Por qué.** `claim_scope` no es decorativo — su docstring dice que *«travels with the fragment and
is not optional: a commitment of the establishment read aloud as if it were a fact of the world is
the failure mode the whole marking mechanism exists to prevent»*, y son 25 de 161 fragmentos. Y
`citation_id` es lo que hace la cita **resoluble y localizadora**: *«resolves, locates and opens the
file and the heading in git»*, que son las tres propiedades que la sesión de citación verificable
exige. Citar el catálogo, en cambio, no verifica nada: los metadatos del producto ya viajan en la
respuesta, así que la cita sería decoración.

**Alternativa descartada.** Meter `citation_id` en el campo libre `source`: funciona mecánicamente
y pierde título de documento y de sección, dejando al frontend pintando un slug.

### D7 · En M2 no se busca: se direcciona por clave primaria

**Decisión.** El contexto de una pieza sin pregunta se obtiene con
`chunk_id(document_slug, section_slug)` sobre una **lista blanca de secciones**, para los materiales
que la pieza declara, con tope de **2** materiales y **sólo `claim_scope: general`**.

```
para cada material declarado (tope 2, en el orden que la pieza los declara):
    material-<slug>#cuidados-y-limpieza-en-casa
    material-<slug>#piel-sensible-y-alergias
si la pieza declara ≥2 materiales:
    material-piezas-mixtas#limpiar-una-pieza-mixta-sin-estropear-nada
```

**Por qué.** `chunk_id()` y `material_sheet_slug()` **ya existen**, y las dos secciones están
presentes y son de alcance general en **las nueve** fichas canónicas. Es exacto, cuesta una
sentencia por clave primaria y **no puede devolver una cita espuria**.

**El invariante de alcance no es celo, es una medición.** `material-bano-de-oro` tiene una **séptima
sección**, `Nuestra garantía sobre el baño`, de alcance `establecimiento`, cuyo último párrafo dice
literalmente *«Como todo compromiso de la casa, estas condiciones se confirman en tienda antes de
trasladarlas a un cliente»*. Una regla del tipo «mete las secciones de la ficha» metería una
garantía de taller en un argumentario que nadie pidió, y **sólo** para las piezas bañadas. El riesgo
no crece linealmente con el número de secciones: **es un escalón, y está en secciones concretas**.

**Y el coste no decide nada aquí.** A ~200 tokens por sección y con el modelo y las tarifas
verificadas en `pricing.yaml`, la diferencia entre dos y seis secciones por material es de décimas
de céntimo por llamada. Lo que decide es la atención —el corpus describe las nueve fichas como
*«structurally identical»* y advierte que *«cosine collapses by homogeneity»*, así que el riesgo no
es que un fragmento se ignore sino que **un hecho de un material se atribuya a otro**— y la fatiga
de citación.

**El riesgo que sobrevive en M2, y no lo arregla ningún filtro.** Una pieza de plata con baño de oro
lleva dos fichas, las **dos correctas**, y *«la plata tolera bien el agua»* pertenece a una parte y
no a la otra. Mitigación: el tope de 2, **etiquetar cada fragmento con su material dentro del
contexto** —que el consumidor lo lea, no que lo infiera— y la sección que el corpus ya escribió
para esto, `material-piezas-mixtas#plata-con-bano-la-parte-fragil-manda`.

**Los valores son punto de partida de un barrido, no calibración.** La lista de secciones y el tope
viajan **por parámetro**, como en C20, C23 y C25, para que C30b compare 1/2/3 secciones en un
proceso.

### D8 · En M1 y M3 el filtro de conocimiento es asimétrico

**Decisión.** `search_knowledge` gana un parámetro de **exclusión por documento**. Con pieza
presente, excluye las fichas de las **nueve** materiales canónicas que la pieza **no** declara, y
**no filtra nada más**.

```
EXCLUIR        material-<slug>  de cada canónica que la pieza NO declara   (~8 señuelos)
PASAR SIEMPRE  faq (10) · politica (4) · talla (4) · piedras-* (3)
               material-piezas-mixtas · material-marcajes-y-punzones

excluded = [document_id(material_sheet_slug(t)) for t in MATERIALS_TERMS
            if t not in piece.materials]
→ cláusula condicional sobre la CLAVE PRIMARIA, con la misma forma que el
  _DOC_TYPE_CLAUSE que ya existe, en compile_vector_sql y compile_lexical_sql
→ sin migración, sin columna nueva y sin tocar jsonb
```

**Por qué es seguro dentro de las nueve**, y sólo dentro: son **mutuamente excluyentes por
construcción** —el invariante 1:1 contra `materials.terms`— y **confundibles por construcción**, que
es la razón por la que C23 tuvo que añadir la rama léxica. Fuera de ese conjunto los documentos son
temáticos y no específicos de material.

**Por qué NO un filtro general por material.** Cortaría **23 de los 32 documentos** y con ellos casi
toda pregunta real de mostrador —la piscina, el arreglo, la talla, el regalo sin talla—: falsa
abstención en masa. Y el proyecto ya zanjó esa asimetría con medición en C25: *«silenciar una
consulta que la tienda SÍ puede contestar es un fallo visible en el mostrador, mientras que no
abstenerse en una imposible muestra cinco piezas que no encajan y el operario lo ve»*.

**Detalle que el filtro debe respetar.** `marcajes-y-punzones` y `piezas-mixtas` llevan
`doc_type = material` pero **no son salidas de `material_sheet_slug()`**, así que pasan. Es lo
correcto: *«¿qué significa el 925?»* es contestable sobre una pieza de acero.

**Efecto secundario a favor.** El filtro **refuerza** la abstención del conocimiento: quitar ocho
señuelos casi idénticos deja un conjunto admitido más pequeño y más discriminativo, y el umbral
gobierna la admisión — *«a branch that returns few candidates has already earned the right to be
believed»*. Si el único fragmento sobre umbral era la ficha del material equivocado, filtrarlo
produce abstención, **y es la correcta**.

**En M1 no hay filtro posible**, porque no hay pieza ni materiales declarados. El riesgo de
atribución cruzada es máximo justo donde no se puede acotar, y de ahí sale el spike 1.

### D9 · La abstención se honra y se declara; no se enciende

**Decisión.** La capa **no genera** cuando la regla relativa de C25 ha saltado, y lo declara en
**`abstained: bool`**. El valor efectivo viaja **por parámetro**.

**Por qué.** La regla **ya está activa** (`α = 0,03`, `N = 15`) y en esa banda abstiene en 2 de 20
fuera de dominio y en 0 de 43 contestables: **18 de 20 llegan con candidatos**, sobre un golden set
cuya categoría mayor son esas 20 de 72. Sin puerta, esta capa contestaría *«¿qué tiempo hace
mañana?»* con cinco familias **durante toda una vuelta de manivela**, porque el arreglo es C31 y
C31 lleva C30 de prerrequisito. Se comprobó si el orden se puede invertir: **no limpiamente**,
porque C31 lleva *«rechazo cortés sin llamar al retriever»* y *«validación de salida contra JSON
schema»*, y las dos necesitan que la ruta y el generador existan.

**Por qué el nombre importa.** `low_confidence` ya tiene aquí un significado medido —consenso entre
ramas— que está **anticorrelacionado** con lo que hace falta: dispara en 1 de 20 fuera de dominio y
en **10 de 43** contestables. Reutilizarlo importaría el sentido equivocado y nadie lo notaría hasta
medir.

**Alcance por modo.** `abstained` se emite **siempre**, y en M2 vale constantemente `false`: no hay
recuperación de la que abstenerse, y un campo ausente según el modo obliga al cliente a ramificar
sobre la forma de la respuesta.

### D10 · Una pieza inservible es un error, no una abstención

**Decisión.** Se reutiliza el patrón de C26: el puerto devuelve ausencia como **resultado** y el
router convierte los tres casos —desconocido, inactivo, sin indexar— en **tres respuestas
distintas**.

**Por qué.** Responder `200` con `abstained: true` afirmaría que el catálogo no puede contestar
cuando el problema es la pieza. Y el docstring de `source_document` ya fija la doctrina: *«the three
unusable cases are three different sentences at the boundary, and which sentence a caller writes is
not a decision the SQL layer gets to make»*.

### D11 · El fixture sobrevive, y gana un grupo sin familia

**Decisión.** El modo de stubs sigue sirviendo una respuesta determinista, ajustada al contrato
nuevo, **incluyendo un grupo con familia ausente**.

**Por qué.** Es el mismo razonamiento que `families_suggest_stub` y `families_audit_stub` escribieron
en su propio código: poblar todas las listas porque *«a stub that only returned proposals would let
a client ship without ever handling the two kinds of refusal»*. Un fixture donde toda respuesta
tiene familia deja pasar un cliente que nunca maneja el caso nulo — **y ese caso es el 58 % del
catálogo**.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| **El umbral de conocimiento devuelve citas espurias sobre consultas de producto en M1**, donde no hay filtro posible. El 0,51 se calibró con preguntas de conocimiento frente a fuera de dominio, **nunca con consultas de producto** | **Spike 1, en dos brazos**: las 72 consultas del golden set por `search_knowledge`, con y sin el filtro de D8, contando citas espurias y abstenciones. Si la tasa es alta, se endurece el umbral **para el camino de producto** y nunca se mete un router por palabras clave. Acotado además porque **M2 no usa vectores** y **M3 sí filtra** |
| **La lista blanca de secciones se relaja en implementación** y entra una afirmación de alcance `establecimiento` en un argumentario que nadie pidió | Invariante en la capability, no convención: **sólo `general` en M2**, con test propio. La lista es **blanca y explícita**, nunca «todas las secciones de la ficha» |
| **El filtro de slug se aplica de más** y corta los 23 documentos temáticos, produciendo falsa abstención en masa | Requisito y test de que `faq`, `politica`, `talla`, `piedras-*`, `piezas-mixtas` y `marcajes-y-punzones` **pasan siempre**. El filtro se construye **enumerando las nueve canónicas a excluir**, no enumerando lo que pasa |
| **Atribución cruzada entre los materiales que la pieza sí declara.** Ningún filtro lo resuelve: las dos fichas son correctas | Tope de 2 materiales, **etiquetado por material dentro del contexto**, y la sección de piezas mixtas cuando declara dos o más. Queda **declarado** como límite del modo |
| **El roster se da por pequeño y una familia de ocho miembros desborda** el contexto o el presupuesto de la consulta | **Spike 3**: cardinalidad máxima medida. C18b da una media de ~3,1 pero existen familias de 7 y 8. Tope **declarado**, no confianza en la media |
| **La regeneración del `openapi.json` arrastra cambios no intencionados** del perfil canónico | Regenerar **con `canonical_openapi_settings()`** y revisar el diff del snapshot campo a campo antes de comprometerlo. El test de estabilidad es la red |
| **El alcance se desborda hacia el argumentario**, que es exactamente lo que el desdoble existe para evitar | `pitch` vacío, `prompt_version` nulo y `usage` a cero **como requisito**, con test. Y un test de que el paquete no importa ningún cliente de proveedor |
| **El aviso de variantes queda desfasado** la ventana del último sync del índice | Aceptado y **declarado**: degrada y nunca elimina, como el §15.10 exige de la proyección. Pedirlo a .NET cruzaría la frontera en sentido contrario para un dato que es del índice |
| **La suite de `ai-service` está en verde y este change la mueve mucho** | Línea base **por nombres de test** y no por recuento, antes de tocar nada, y comparación final por nombres |

## Migration Plan

**Sin migración de base de datos**, ni de Alembic ni de EF Core: el roster lee una tabla existente y
la exclusión de documentos opera sobre una clave primaria ya derivable con `document_id(slug)`.

**Lo que sí es un despliegue con orden:**

1. El contrato se mueve y `openapi.json` se regenera **en el mismo change**, como C18a y C18b.
2. **`STUB_MODE` sigue siendo el interruptor.** Con stubs activos, la ruta sirve el fixture nuevo;
   con stubs apagados, la implementación real. No hay bandera propia y no hace falta: el snapshot
   canónico se genera con stubs activos, tal como está documentado.
3. **Marcha atrás**: volver a `STUB_MODE=true` devuelve la ruta al fixture sin tocar código. El
   filtro de conocimiento y el roster son aditivos —un parámetro opcional y un método nuevo—, así
   que no alteran el comportamiento de `POST /v1/retrieval/products` ni de la búsqueda de
   conocimiento cuando no se les pasa nada.
4. **Ningún consumidor que coordinar**: `IAiGatewayClient` no llama a esta ruta. C34 nacerá contra el
   contrato nuevo.

## Open Questions

**Ninguna bloqueante.** Las seis del ticket se cerraron el 2026-09-13 tomando su opción por defecto,
y quedan registradas allí con su motivo: el nombre de la capability (`assist-generation`), las dos
secciones de la lista blanca, el tope de dos materiales, los tres spikes dentro del change, el grupo
sin familia en el fixture y `abstained` emitido siempre.

Lo que queda abierto es **deliberadamente empírico y se resuelve dentro del change**:

- **¿Necesita M1 un umbral de conocimiento propio?** Lo decide el spike 1. Por defecto, **no**: se
  consume el 0,51 y se declara lo que se mida.
- **¿Se puede reutilizar el vector de consulta** entre la recuperación de producto y la búsqueda de
  conocimiento? Lo decide el spike 2. Si es viable, el coste marginal de consultar el conocimiento
  baja a una sentencia sobre 161 filas; si no, M3 paga un *embedding* y se declara.
- **¿Cuál es el tope del roster?** Lo decide el spike 3.

Las tres son mediciones, no decisiones de arquitectura, y por eso van como tarea y no como pregunta
al usuario.
