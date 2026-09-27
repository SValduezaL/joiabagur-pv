# C40 — decisiones de exploración: el panel de búsqueda se convierte en M1

**Change previsto:** `add-frontend-free-query-panel` (C40) · **Fecha:** 2026-09-24
**Origen:** sesión de exploración durante la comprobación en demo de C36 (tarea 8.5)
**Entorno de medición:** local — `jpv-pv-postgres` con el mundo de C10 y el índice de C13,
`jbg-ai` en contenedor con `STUB_MODE=false` y credencial real, prompt `assist/v3`,
modelo `openai/gpt-4o-mini`, clasificador `openai/gpt-4o`

Este informe recoge lo que se **midió contra el servicio real** durante una sesión que empezó
siendo la verificación manual de C36 y acabó destapando que el panel de búsqueda asistida llevaba
todo el proyecto corriendo en su ruta degradada. Los §1 a §9 contienen **siete hallazgos medidos**,
**diez decisiones de diseño**, **una regla transversal de completitud** y **cuatro preguntas
cerradas**, y proponen **qué se cierra en C36, qué abre C40 y qué sale como change propio**.

> **El §10 es una segunda pasada del mismo día, contra el código y no contra el servicio.** Añade
> **cuatro hallazgos** —uno de ellos bloquea el tramo 2—, **siete decisiones más (D11 a D17)**,
> **corrige la Q3** y resuelve **dos contradicciones internas de los §1 a §9**. La línea de corte
> del §4 queda **sustituida por la del §10.10**, y la tabla de estados de la pantalla vive aparte,
> en [c40-m1-panel-states.md](c40-m1-panel-states.md).

**Tres limitaciones declaradas del §15 del diseño se cierran con C40**, una de ellas —que una pieza
no indexada no se distingue de una caída— con un solo campo que .NET ya calcula y descarta. La
única que no cierra es el consumidor del agente.

**Premisa dada por el desarrollador:** el contrato `openapi.json` se va a mover. Eso cambia lo que
es discutible: ya no hay que justificar *si* se toca, sino acotar *cuánto*.

---

## 1 · Cómo empezó: tres funcionalidades apagadas que la pantalla daba por encendidas

La sesión iba a verificar la ficha de venta de C36 en un entorno real. Lo primero que apareció no
fue un defecto de C36:

| Interruptor | Estado | Síntoma en pantalla |
|---|---|---|
| `AiSalesAssist:EnabledByDefault` | `false`, **ausente de todo `appsettings`** | «El asistente no está disponible» |
| `AiSearch:EnabledByDefault` | `false`, **ausente de todo `appsettings`** | «Búsqueda asistida no disponible» |
| Filtros en la ruta degradada | **se descartan en silencio** | *ninguno* — los chips siguen pulsados |

Los dos primeros son configuración y se resuelven con una variable de entorno. **El tercero es un
defecto**, y es el que abrió la sesión entera.

> **Lección transversal, y es la que gobierna las decisiones de abajo.** Los tres problemas son el
> mismo: una capacidad apagada que la interfaz presenta como encendida. Dos de ellos avisan; el de
> los filtros **no avisa de nada**, que es el peor de los tres.

---

## 2 · Los siete hallazgos

### H1 · La ruta degradada tira los filtros, y no hay ninguna razón escrita para ello

```csharp
return await _repository.SearchLexicalAsync(
    terms, request.PointOfSaleId, take, cancellationToken);
//  los filtros no viajan. BuildFilters() sólo alimenta la ruta asistida.
```

La firma de `SearchLexicalAsync` **no tiene parámetro de filtros**. El docstring razona con cuidado
por qué los términos se combinan con *«cualquiera»* y no con *«todos»*, y sobre materiales y tipo
de pieza guarda silencio. En este repositorio una decisión deliberada va razonada al lado; ésta no
lo está, así que se lee como omisión.

**Medido.** Consulta `plata` con `category: pendientes` sobre la ruta degradada devuelve
*Anillo Bruma grapas granate*, *Colgante mejillón doppio*, *Presión plata*. **El filtro no se
aplica en absoluto.**

**Y sí se puede aplicar.** La duda era si el catálogo transaccional tenía esos datos, porque
`piece_type` y `materials` viven en el índice. Los tiene:

| Campo | Cobertura |
|---|---|
| `ProductAiProfiles.PieceType` | **1.172 de 1.200 · 97,7 %** (276 son `pendientes`) |
| `ProductAiProfiles.MaterialsJson` | 1.098 de 1.200 · 91,5 % |

Es un `JOIN` y dos `AND`. Con una cautela que el propio servicio de IA documenta: el filtro de
materiales aplicado duro borra las piezas sin materiales extraídos —aquí el **8,5 %**—, así que el
de tipo puede ser duro y el de materiales merece una decisión propia.

### H2 · En la ruta asistida los filtros sí funcionan, y son un pre-filtro

Entran como `AND` dentro del SQL de recuperación, **antes de puntuar**, no como post-filtrado del
top-k:

```sql
AND d.materials && CAST(:materials AS text[])
AND d.piece_type = :category
```

La regla que lo gobierna está escrita y es buena: **«lo que un humano pulsa filtra; lo que una
regla infiere del texto degrada»**. Verificado en vivo contra `/v1/retrieval/products`:
`category=pendientes` devuelve sólo pendientes (Aros 01, Aros 02, Pendientes hilo cuadrado),
`category=anillo` sólo anillos, `category=diadema` sólo diademas.

### H3 · M1 no es una tercera recuperación: es la misma, con menos control y más salida

```python
# /v1/retrieval/products  (el panel de hoy)
retrieve_products(RetrievalRequest(query, top_k, FILTERS), ...)

# /v1/assist/sale en modo libre  (M1)
retrieve_products(RetrievalRequest(query=question, top_k=payload.top_k), ...)
#                                  ^ filters se queda en su valor por defecto
```

`RetrievalRequest` **tiene** campo `filters`. M1 no lo rellena, porque `AssistRequest` —el cuerpo
de la ruta de assist— **no tiene dónde llevarlos**. Así que hoy M1 sabe *menos* de lo que el
operario pidió, y encima devuelve *más*: enrutador, corpus y prosa.

| | Semántico (`/v1/retrieval/products`) | Asistido (`/v1/assist/sale`, M1) |
|---|---|---|
| Forma | `results` — **lista plana** | `groups` — **agrupado por familia** |
| Filtros | **sí** | **no** ← lo que C40 arregla |
| Argumentario | — | uno, sobre el conjunto |
| Citas | — | según la ruta (H5) |
| Rechazo del enrutador | — | `query_out_of_domain`, `query_not_in_catalogue` |
| Vacío | `low_confidence` | `abstained` |
| Coste | 1 embedding | embedding + clasificador + corpus + generación |
| Latencia medida | ~1-2 s | **p50 2,7 s · máx 5,8 s** |

### H4 · El agrupado por familia hace trabajo real, y hoy se tira

Deduplicación conservando el rango: *«a group takes the position of its best member — so grouping
never reorders what the ranking decided»*. Medido sobre 8 consultas, `top_k=10`:

| Consulta | Piezas | Filas | Familia mayor |
|---|---|---|---|
| colgante estrella de mar | 30 | **18** | **8** |
| algo azul para una boda | 30 | 22 | 3 |
| collar de perlas clásico | 30 | 23 | 4 |
| anillo de talla grande | 30 | 23 | 4 |
| pulsera de plata sencilla | 30 | 23 | 4 |
| un anillo de plata para regalar | 30 | 27 | 4 |
| aros dorados | 30 | 28 | 3 |
| pendientes pequeños para el día a día | 30 | 30 | 1 |
| **Total** | **240** | **194** | **−19,2 %** |

Sin agrupar, *«colgante estrella de mar»* gastaría **8 de sus 30 filas** en el mismo colgante. El
agrupado colapsó algo en **7 de 8** consultas.

**Pero la información se descarta:** si la fila sólo pinta al mejor miembro, saber que el grupo
tenía ocho no sirve de nada. Es dato que la lista plana de hoy **no puede** tener y que el panel
asistido tendría gratis.

### H5 · Las citas dependen de la ruta, y en la de catálogo son cero por diseño

| Consulta | Ruta | Piezas | Citas |
|---|---|---|---|
| un anillo de plata para regalar | `catalog` | 15 | **0** |
| collar de perlas clásico | `catalog` | 15 | **0** |
| ¿cómo limpio una joya en casa? | `knowledge` | 0 | **5** |
| ¿la plata se puede mojar? | `knowledge` | 0 | **0** ⚠ |
| un anillo que se pueda mojar en la piscina | `both` | 15 | **0** ⚠ |
| pendientes para piel sensible al níquel | `both` | 15 | **1** |

En `catalog` el prompt lo ordena explícitamente: *«En esta tarea la lista `corpus` de los datos
viene vacía… Devuelve la lista de citas usadas vacía»*. El corpus **ni se consulta**.

Las que sí llegan vienen completas: `citation_id`, `document_title`, `section_title`, `doc_type`,
`claim_scope` y `snippet` — incluida una de `claim_scope: establecimiento`, que es justo la que la
ficha de C36 ya sabe distinguir.

### H6 · Una respuesta puede llegar fundamentada y sin atribuir, y la causa no es la que parecía

**La medición que más cambió el diagnóstico.** «¿La plata se puede mojar?» devolvió un
argumentario correcto —*«la plata tolera bien el agua, pero lo que no tolera es quedarse
húmeda»*, que es la redacción del corpus— con `citations: []`.

Las dos hipótesis razonables eran: el corpus no se recuperó, o el modelo no citó. **Las dos son
falsas.** El registro del servicio lo dice:

```
stage=knowledge  abstained=0  citations=5  distance_min=0.3873  (umbral 0.51)
stage=assist     route=knowledge  citations=none
                 violations=claim_not_in_pitch,claim_not_in_pitch
                 withdrawn=material-plata#cuidados-y-limpieza-en-casa,
                           material-plata#que-lo-estropea
```

El corpus **se recuperó** —cinco fragmentos, holgadamente bajo el umbral— y el modelo **sí citó
dos**. Fue la **puerta de integridad de C30b** la que las retiró: cada cita debe declarar el tramo
que sostiene, *«copiado literalmente, carácter por carácter, del argumentario»*, y el tramo
declarado no aparecía literal en su propio texto.

**La puerta hace su trabajo, y hace exactamente lo que se diseñó que hiciera.** El vocabulario de
violaciones tiene **siete causas**, y seis de ellas son «duras»: retiran el argumentario entero.
`claim_not_in_pitch` **no lo es, y está escrito por qué**:

> *«Correspondence is **deliberately absent** — the fragment exists and was in the context, and what
> failed is the model's own account of using it, so the proportionate answer is withdrawing that
> citation and publishing the prose.»*

El fragmento existe y estaba en el contexto; lo que falló es el relato que el modelo hace de cómo
lo usó. Retirar la cita y publicar la prosa es la respuesta proporcionada.

**Y esto no es un hallazgo de esta sesión: es el régimen normal, ya medido y publicado.** La pasada
de C30b —120 generaciones, modos anclados, prompt `v3`— lo dice en su propio fichero de
resultados:

| | |
|---|---|
| Argumentarios publicados | **120 de 120** |
| Citas ofrecidas al modelo | 420 |
| Citas publicadas | 189 |
| **Citas retiradas** | **83 · el 30,5 % de las que el modelo declaró** |
| Generaciones que perdieron **alguna** cita | **46 de 120 · 38,3 %** |
| Generaciones publicadas **sin ninguna** cita | **14 de 120 · 11,7 %** |
| Causa | **`claim_not_in_pitch` en el 100 %**. Cero inventadas, cero por cifras |

La reparación recupera parte: de 121 violaciones en el primer intento quedan 83 tras el reintento.

**Lo que sí es nuevo de esta sesión** es que **nadie lo ha llevado nunca a la pantalla**. La ficha
de C36 enseña las citas que sobreviven sin decir que casi una de cada tres declaradas se quedó por
el camino, y en el 11,7 % de los casos **entrega una afirmación sin ninguna fuente y con el mismo
aspecto que si nunca hubiera habido corpus**.

#### Y el mismo reparto, medido ahora para M1

Pasada de **42 consultas del conjunto etiquetado del propio proyecto** — las 32 `eval_question`
del corpus, una por documento y escrita por su autor dentro de él, más las 10 consultas `both` del
conjunto de enrutado de C31. Ninguna la escribí yo. Prompt `assist/v3`, mismo servicio y mismo
índice:

| | **M1** (42 consultas) | M2 / M3 (C30b, 120 generaciones) |
|---|---|---|
| Citas declaradas por el modelo | 72 | 272 |
| Citas publicadas | 53 | 189 |
| **Citas retiradas** | **19 · 26,4 %** | **83 · 30,5 %** |
| Respuestas que pierden **alguna** | 14 de 37 · **37,8 %** | 46 de 120 · **38,3 %** |
| Respuestas **sin ninguna** cita | **9 de 37 · 24,3 %** | 14 de 120 · **11,7 %** |
| Causas | `claim_not_in_pitch` 19 · **`dangling_citation` 2** | `claim_not_in_pitch` 121 · **0 duras** |

**Tres lecturas, y las tres importan:**

1. **La tasa de retirada es comparable** — 26,4 % contra 30,5 %. M1 no es peor en esto, así que el
   fenómeno no es del modo libre: es de la puerta.
2. **Pero la tasa de respuestas sin ninguna fuente se duplica**: **24,3 % contra 11,7 %**. Es el
   número que le importa a la pantalla — **una de cada cuatro** respuestas de conocimiento en M1
   llega con una afirmación y sin una sola fuente. La causa es aritmética: en los modos anclados
   el modelo declara más citas por respuesta, así que perder una no la deja a cero.
3. **Reaparece `dangling_citation`, que en los modos anclados era cero.** Una consulta de 42 —
   *«una pulsera dorada para alguien a quien le sale verde la muñeca»*— declaró dos citas
   inventadas. Al ser causa **dura**, el argumentario se retiró entero (`pitch_chars=0`), que es lo
   correcto. Pero es exactamente el fallo que `v2` tenía y que `v3` vino a corregir, **vivo todavía
   en el modo libre a razón de 1 de 42**.

El punto 3 es el que merece quedarse: v3 arregló las citas inventadas en la ruta `catalog`
diciéndole al modelo que devolviera la lista vacía. En `both` —catálogo *y* corpus a la vez— el
modelo vuelve a componer identificadores. **La puerta lo caza**, así que no llega a pantalla, y el
coste es un argumentario perdido.

### H7 · El enrutador acierta, pero puede admitir una consulta y no darle ruta

19 llamadas en modo libre:

| `intent` | `route` | n |
|---|---|---|
| `in_domain` | `catalog` | 8 |
| `in_domain` | `knowledge` | 5 |
| `in_domain` | `both` | 2 |
| `in_domain` | **`none`** | **2** ⚠ |
| `out_of_domain` | `none` | 1 |
| `not_in_catalogue` | `none` | 1 |

**En todo lo que pude juzgar, acertó**: catálogo para consultas de piezas, conocimiento para
preguntas de oficio, `both` para mixtas, y los dos rechazos cayeron donde debían — incluidos
`query_out_of_domain` («¿qué tiempo hará mañana?») y `query_not_in_catalogue` («¿vendéis relojes
automáticos?»), que son **los dos códigos que C36 no podía alcanzar**.

Pero **2 de 19 volvieron `in_domain` sin ruta**, con `router_degraded=False`: el clasificador
funcionó y decidió no decidir.

**Y la pasada de 42 consultas del H6 lo confirma y corrige lo que yo había escrito.** `route=none`
salió **5 veces de 42 — el 11,9 %**, y **no es silencio**:

| consulta | piezas | citas | argumentario |
|---|---|---|---|
| ¿La M de un colgante significa lo mismo que la M de un anillo? | 0 | 0 | **ninguno** |
| pendientes de perla que se puedan limpiar en casa | **15** | **5** | **ninguno** |
| qué cadena le doy para que el colgante caiga sobre el escote | **15** | **5** | **ninguno** |
| un regalo de plata para quien no se quita nunca la joya | **15** | **5** | **ninguno** |
| un anillo de lapislázuli, ¿se puede meter en el ultrasonidos? | **15** | **1** | **ninguno** |

La explicación está en el orquestador: con `route=None` las dos ramas corren —
`if route in (None, "catalog", "both")` para la recuperación y `if … route in (None, "knowledge",
"both")` para el corpus—, pero `task=none` significa que **no hay sección de tarea que ejecutar**,
así que no se genera nada.

**El resultado es peor que el silencio: citas colgando de un texto que no existe.** Cuatro de las
cinco entregan quince piezas y hasta cinco fragmentos del corpus, y ni una línea de prosa que los
use. En mi primera redacción dije *«cero grupos, cero citas, cero texto»*, y era cierto sólo de las
dos consultas que había probado, que casualmente no recuperaron nada.

---

## 3 · Las diez decisiones

Tomadas con el desarrollador durante la sesión. Las marcadas **(cerrada)** no se reabren.

### D1 · El panel de búsqueda asistida **se convierte en M1** (cerrada)

No se construye una pantalla nueva. El panel ya hace la mitad —misma recuperación, mismo selector
de tienda, misma hidratación, mismo episodio por visita— y M1 es ese panel más el enrutador, el
corpus y la prosa. Una pestaña aparte duplicaría el buscador para no reutilizar nada.

### D2 · `AssistRequest` gana `filters`, y el contrato se mueve (cerrada)

Es la premisa dada. Sin ella M1 sabe menos que el panel al que sustituye (H3), y un operario que
pulsa *pendientes* y recibe anillos no vuelve a pulsar nada.

Es **adición pura** —ningún campo se retira ni cambia de tipo— y se verifica hoja a hoja, como ya
hizo C31. Toca cuatro sitios: `AssistRequest` (Python), `openapi.json`,
`AiAssistSaleRequest` (.NET) y el doble de `assist_sale_stub`, que si no mentirá en los tests.

### D3 · Un toggle entre recuperación semántica y asistida (cerrada)

Dos rutas visibles y elegibles sobre la misma consulta. **Y una razón de más que la usabilidad:**
la rúbrica del PF pide comparar configuraciones, y hoy eso sólo se demuestra en el arnés. El
toggle **es la ablación, en pantalla**.

Con un matiz que la interfaz debe decir: no son dos sabores del mismo coste. Semántico es un
embedding; asistido es embedding + clasificador + corpus + generación, 2,7 a 5,8 s medidos, contra
un presupuesto de diez por minuto.

### D4 · Badge permanente de disponibilidad de la IA (cerrada)

Encendido o apagado, visible **antes** de buscar y con independencia de que luego salga el aviso.
Es la respuesta directa a la lección del §1: los tres tropiezos de la sesión fueron capacidades
apagadas que la pantalla presentaba como encendidas.

### D5 · Los filtros también en la ruta degradada (cerrada)

Es lo que el operario ve y lo que el operario espera. Con `PieceType` al 97,7 % es un `JOIN` y dos
`AND` (H1). Y si por lo que sea no se aplicaran, **la pantalla tiene que decirlo**: un chip pulsado
que no filtra es la única de las tres averías de esta sesión que engañaba en silencio.

### D6 · «Todos los puntos de venta», y el ámbito se abre (cerrada)

Un operario podrá buscar sin acotar tienda, para asistir una venta de otra. **No abre una puerta
nueva: cierra una incoherencia.** Medido: `GET /api/inventory/product/{id}` ya devuelve a un
operario de Ciutadella el desglose de las tres tiendas (24 + 16 + 48), mientras la búsqueda y la
ficha refusan una tienda no asignada. La casa ya era inconsistente; esto la hace consistente en la
dirección permisiva, y va escrito como decisión.

Tres consecuencias que se aceptan a propósito:

1. **Es otro ranking.** Sin ámbito, `qty_bucket` y `sales_30d` quedan a `NULL`. El primero sólo
   restaba; el segundo **no ordena nada** desde que C25 lo refutó, así que la pérdida real es
   pequeña — y medida: agregar `qty_bucket` de todas las tiendas cambiaría **6 productos de
   1.194 (0,5 %)**, porque sólo 6 están agotados en todas. No merece mecanismo propio.
2. **Cambia el significado de los vacíos.** Sin tienda no hay contra qué hidratar, así que
   *«nada de esto está en tu tienda»* deja de poder decirse.
3. **La ficha exige tienda**, así que con ámbito «Todos» **el botón «Ver ficha de venta» se
   deshabilita**. Cerrar la ambigüedad en la puerta es mejor que arrastrarla a la ficha.

### D7 · La etiqueta de existencias nombra la tienda (cerrada)

- Con tienda: **«8 en Ciutadella Centre»**, no «8 en esta tienda». Con varias tiendas en juego,
  *«esta tienda»* es ambiguo, y la ambigüedad en una cifra de stock es lo que cuesta una venta.
- Sin tienda: **«Selecciona tienda para ver stock»**, que es la versión honesta de lo que si no
  sería un cero — una afirmación falsa.
- La tienda se elige en **el filtro de arriba**, no con un desplegable por fila: cambiarla sólo
  refresca la cifra y **no llama a ningún modelo**.

### D8 · Los avisos no se pintan en el listado

`warnings` describe **una sola pieza** —la primera del primer grupo—, no el conjunto:

```python
focus_source = await _focus_of(groups, search=search)      # la primera
warnings = _warnings(size_label=focus_source.size_label, roster_size=len(roster), ...)
```

Medido: sobre 15 piezas, `["family_has_variants", "size_label_missing"]` describiendo a `SKU143`,
cuyo grupo visible tiene **un solo miembro**. Pintar eso como banda superior sería mentir.

**Y no se pierde nada**, que es lo que cierra la decisión: al pulsar «Ver ficha de venta» la ficha
emite **su propia** petición anclada a esa pieza (M2), así que sus avisos se calculan para ella, sea
la primera del listado o la catorceava. Un aviso es propiedad de una pieza, y la ficha es el único
sitio donde hay exactamente una.

**Queda anotado como diferido**: que el servicio emita los avisos **por pieza** es lo correcto de
verdad, y es cambio de contrato aparte.

### D10 · La fila de M1 **enseña su grupo**, no sólo a su mejor miembro (cerrada)

Cuando un producto del listado pertenece a un grupo, la fila **dice qué otras tallas o
características lleva la familia**, en vez de descartar ese dato como hace hoy.

```
  Colgante estrella de mar                                        210,00 €
  SKU610 · plata                                        8 en Ciutadella Centre
  también en XS, S, M, L y 4 tallas más
                                  [Seleccionar para venta]  [Ver ficha de venta]
```

**Por qué es una decisión y no un adorno.** El agrupado ya ocurre —es lo que evita que una familia
inunde el listado, y ahorra el 19,2 % de las filas (H4)— pero la información que lo justifica **se
tira al pintar**. Un operario ve una fila y no sabe que detrás hay ocho piezas; para enterarse
tiene que abrir la ficha.

Y es información que el modo semántico **no puede dar**: su lista es plana y no sabe que las otras
siete existen. Así que es, además, una de las diferencias que justifican el toggle de D3.

**Lo que la fila enseña** sale de los miembros que el grupo trae: `variant_label` de cada uno, con
degradación al SKU cuando falta —la misma regla que C36 ya aplica en el bloque de familia de la
ficha—. Si el grupo trae un solo miembro, no se escribe nada.

**Y engancha con la ficha sin duplicarla**: la fila *anuncia* que hay familia; la ficha, al abrirse
anclada a una pieza, la despliega con precio, unidades y botón por variante. La fila no repite ese
trabajo ni intenta vender desde el listado.

### D9 · La abstención se mide **antes** de filtrar

Hoy es al revés: `_vector_branch(..., filters=filters, ...)` filtra en el SQL y `should_abstain`
recibe las distancias ya filtradas. Tres razones para moverlo, **las tres escritas en el propio
repositorio**:

1. *«A decision about the **QUERY**, applied to the whole response»* — la consulta no cambia al
   filtrar.
2. *«An abstention produced by filtering would be indistinguishable from a retrieval that simply
   found little, and the two call for different things from the operator»* — el código hace hoy lo
   que su propia documentación desaconseja.
3. `min_candidates: 15` está *«fijado contra 20 consultas fuera de dominio y 43 contestables»*, y
   esas consultas se calibraron **sin filtros**. Correrlo sobre el conjunto filtrado lo pone en un
   régimen para el que nunca se calibró: **moverlo antes restaura la calibración, no la invalida.**

Y el coste no estorba, porque el módulo de filtros ya lo midió: *«At 1.168 rows a hard filter saves
no time»*.

**Medido, el problema que esto resuelve:** con filtro estrecho la abstención **no puede
dispararse**, porque nunca habrá 15 candidatos.

| Filtro | Candidatos |
|---|---|
| sin filtro | 30 |
| tipo=pendientes | 30 |
| **tipo=diadema** | **7** |
| **tipo=pendientes + oro** | **10** |

Con 7 candidatos, `candidatos_en_banda ≥ 15` es imposible. El sistema devolvería siete piezas
mediocres **y escribiría un párrafo hablando bien de ellas**.

**Lo que se gana:** dos mensajes que hoy no se distinguen.

| Situación | Qué debe decir |
|---|---|
| Consulta incontestable, perfil plano | «No tengo nada que encaje con lo que describes» |
| Consulta buena, filtro estrecho | «Hay piezas que encajan, pero ninguna es una diadema de oro» |

**Punto débil aceptado:** se podrá abstener en una consulta que el filtro habría rescatado
(*«algo bonito»* + *diadema*). Se acepta: la abstención juzga si **la descripción** encontró algo, y
un filtro es una restricción, no una descripción.

**Aviso de alcance:** esto toca `retrieval-abstention`, **capability viva con spec propia**, y
afecta también al panel actual. No es un cambio interno.

---

## 4 · Qué se cierra en C36 y qué abre C40

C36 está **implementado, empujado y con 49 de 50 tareas**. Su spec dice que la ficha está anclada a
una pieza y se alcanza desde tres sitios: eso está entregado y es cierto. Meter aquí el panel sería
reabrir un change terminado para cambiarle el alcance.

### Se queda en C36 — sólo lo que es suyo

| Qué | Por qué |
|---|---|
| **La cabecera de la ficha dice «en esta tienda» en vez del nombre** | **Es un defecto de C36.** La cabecera ya pinta `pointOfSaleName`, pero `assist.tsx` sólo carga la lista de tiendas cuando se abre en frío (`if (navigatedPointOfSaleId) return;`), así que con la tienda llegando por estado de navegación el nombre nunca se pide. Se arregla con `getPointOfSale(id)`: una llamada barata, sin IA |
| **Tarea 8.5**, la comprobación en demo | Ya verificada en local durante esta sesión: `pitchStatus: generated`, `promptVersion: assist/v3`, sin marcadores, familia de 4 sin preselección, citas con `claim_scope` |
| **Anotar los dos interruptores** en la documentación de puesta en marcha | Le costó la sesión entera a quien lo probó |

**Nada más.** El resto es alcance nuevo en tres capas.

### Abre C40 — `add-frontend-free-query-panel`

**Zona:** `ai-service/src/jbg_ai/`, `backend/src/`, `frontend/src/`. **Tres capas, y el contrato se
mueve**, que es lo que lo separa de C36 sin discusión.

**Línea de corte**, por si la sesión desborda — en este orden, y el criterio de ordenación es
*cuánto engaña hoy la pantalla*, no cuánto cuesta:

1. **Lo que hoy miente en silencio, y no toca el contrato.** Los filtros en la ruta degradada (D5),
   el **badge** (D4), y **subir `degraded_reason`** al DTO de .NET — que cierra la limitación 3 de
   C34 con un campo. Sólo .NET y frontend. **Es archivable solo**, y arregla las tres averías que
   esta sesión encontró por accidente.
2. **`filters` en `AssistRequest`** (D2) y el **toggle** (D3): el panel pasa a ser M1 con los
   filtros que el operario pulsó. Aquí se mueve `openapi.json`. **Y aquí entra el castellano de los
   dos rechazos** (§15.13), porque desde este tramo ya pueden llegar.
3. **La abstención antes de filtrar** (D9) y sus vacíos: el del filtro estrecho y el de la consulta
   sin ruta (Q3). Toca `retrieval-abstention`, spec viva.
4. **«Todos los puntos de venta»** (D6) con la etiqueta de D7 y la ficha deshabilitada sin tienda.
5. **La fila que usa el grupo** (H4): *«también en XS, S, M, L y 4 más»*.
6. **El embudo de observabilidad** para administrador (§4): latencia partida, modelo, tokens,
   contadores. Va el último porque es el único que **no arregla nada que hoy engañe** — enseña algo
   que hoy simplemente no está. Es también el más fácil de sacar si la sesión aprieta.

Los tramos que no entren **se declaran aplazados con su motivo**, no se callan.

**Lo que no está en la línea de corte porque no es de C40:** la telemetría de uso (§4.2), que es
una migración y una zona más.

### Qué limitaciones cierra C40, y cuál no

Cuatro limitaciones estaban en juego. **Tres se cierran**, y una de las tres es una que ni siquiera
habíamos puesto en la lista.

#### ✅ §15.12 — la pregunta libre sin pieza no tiene pantalla · **cierra**

Con M1 en el panel, los **tres** modos llegan al operario. La limitación se escribió en C30a
diciendo que *«el tercero existe en el servicio y su consumidor es el bucle del agente y el arnés
de evaluación, no una caja de texto»*. Desde C40 es una caja de texto.

#### ✅ §15.13 — el rechazo cortés no tiene pantalla · **cierra**

Ésta es la que sorprende, y la cierra **una medición**, no un argumento. Los dos códigos que C36
dejó deliberadamente sin castellano —`query_out_of_domain` y `query_not_in_catalogue`— **sí llegan
en M1** (H7): «¿qué tiempo hará mañana?» devolvió `intent=out_of_domain`, y «¿vendéis relojes
automáticos?» devolvió `intent=not_in_catalogue`.

Así que C40 **tiene que escribir esa copia**, que es exactamente la que C36 se negó a escribir. Y
las dos decisiones son correctas: desde la ficha eran caminos imposibles, desde el panel son
caminos reales. Lo que cambia no es el criterio, es la superficie.

Con eso, la distinción que el §15.13 declaraba indemostrable —*«el catálogo no puede contestar
esto»* frente a *«esto no es una pregunta de joyería»*— pasa a verse en pantalla: la primera es una
abstención, la segunda un rechazo, y con D9 además se les suma una tercera, el filtro estrecho.

#### ✅ Limitación 3 de C34 / D12 de C36 — no se distingue una pieza no indexada de una caída · **cierra, y es casi gratis**

**Esto no estaba en la lista y debería haber estado.** C36 declaró, en su D12 y en su Q-8, que la
ficha no puede distinguir una pieza que el servicio no puede procesar de una caída del servicio,
*«porque los dos dan la misma bandera y el mismo estado, y sólo el registro del backend los
separa»*.

La frase es literalmente cierta, y esconde la solución. **El registro del backend los separa porque
.NET lo sabe.** `SalesAssistService` calcula un `degradedReason` con **seis** valores:

```
switched_off · credential_rejected · not_implemented
product_not_indexed · ai_unavailable · unclassified
```

Lo escribe en su línea de registro `stage=sales_assist` y **lo descarta al construir la
respuesta**. `SalesAssistResponse` sólo reenvía `PromptVersion` y `TraceId`.

Subirlo es **añadir un campo a un DTO de .NET**. No toca `openapi.json`, porque ése es el contrato
entre .NET y Python, y esto es el contrato entre .NET y el navegador. La ficha de C36 ya sabe
pintar estados distinguidos: sólo le faltaba el dato.

#### ❌ El agente sigue sin consumidor · **no cierra**

`POST /v1/assist/agent` no tiene ruta .NET ni método en `IAiGatewayClient`. Es una cuarta capa
sobre las tres de C40, y arrastra dos tareas diferidas de C32b que son prerrequisito: la política
de *timeout* y circuito, y el desglose de uso por etapa —sin el cual cualquier cifra de coste del
agente es falsa, porque `AgentUsage.model` nombra sólo la última de hasta tres etapas—.

Queda fuera, y con motivo.

---

### La telemetría: tres cosas distintas que estaba mezclando

Cuando escribí *«la telemetría de la ficha sigue sin existir»* me refería a **una sola** de las
tres, y era la más cara. Separadas:

| | Qué es | ¿Existe hoy? | Coste de entregarlo |
|---|---|---|---|
| **1 · Observabilidad por petición** | Latencia, modelo, tokens, motivo de degradación, embudo | **Se mide y se tira** | Campos en un DTO de .NET |
| **2 · Telemetría de uso** | Quién abrió qué ficha, quién preguntó, qué variante eligió | **No existe** | Tabla + migración de EF Core |
| **3 · Coste** | Tokens × tarifa, agregado | No existe | Depende de la 2 |

#### 1 · Observabilidad: está toda medida y no llega a ninguna parte

`SalesAssistService` ya escribe esta línea por cada petición de ficha:

```
stage=sales_assist  trace_id=  pos_id=  product_id=  mode=  ai_available=
                    degraded_reason=  pitch_status=  pitch_len=  citation_ids=  warnings=
                    members_returned=  members_carried=
                    ai_ms=  total_ms=  prompt_version=  model=  prompt_tokens=  completion_tokens=
```

Está **todo** lo que hace falta: la latencia partida en dos —lo que tardó la IA y lo que tardó el
total—, el modelo, los tokens de entrada y salida, el motivo de la degradación y los contadores del
embudo. Y del otro lado, `AssistResponse` de Python trae `usage` con `model`, `prompt_tokens`,
`completion_tokens` y `total_tokens`, más `abstained`, que .NET tampoco reenvía.

**No es un problema de medición. Es que el dato muere en la frontera del DTO.**

**Y el patrón para enseñarlo ya existe**: el embudo de administrador que C16 puso en el panel —
`data-testid="assisted-search-funnel"`, plegado por defecto, sólo para administradores, con los
contadores en insignias—. C40 lo extiende a la ficha y lo amplía en el panel.

**Tratamiento propuesto:**

- **Visible sólo para administrador y plegado por defecto**, como el de C16. Un operario con un
  cliente delante no necesita saber cuántos tokens costó la frase que está leyendo; un
  administrador que decide si esto sale caro, sí.
- **Se enseñan las entradas de un coste, no un coste.** Tokens y modelo, nunca euros. Las tarifas
  cambian y una tarifa escrita en el frontend está mal el día que el proveedor la mueve. Además,
  la documentación del contrato ya avisa de que `usage.model` **no es una clave de precio** en la
  ruta del agente, donde suma hasta tres etapas con tres modelos; en `/v1/assist/sale` hay un solo
  modelo y la multiplicación sí sería válida, pero enseñar el producto invitaría a copiarlo a la
  otra ruta, donde es falso.
- **La latencia sí, y partida**: `ai_ms` frente a `total_ms` es lo que separa «la IA tarda» de «la
  red o la hidratación tardan», y es la primera pregunta que se hace quien ve la pantalla lenta.
- **Nada del contenido.** Ni el argumentario ni la pregunta del cliente entran aquí, por la regla
  que el §7.7 del diseño y la spec de C36 ya imponen.

**Lo que esto habilita**, y no es menor: la tabla de ablación del §11.2 del diseño se demuestra hoy
sólo en el arnés. Con el toggle de D3 más este bloque, un evaluador puede poner las dos rutas una
al lado de la otra sobre la misma consulta **y ver lo que cuestan**. Eso es materia de rúbrica.

#### 2 · Telemetría de uso: sigue siendo una tabla, y sigue fuera

Ésta es la que C36 declaró y la que **no** se cierra barata. Registrar que se abrió una ficha, que
se preguntó algo o que se eligió una variante necesita una tabla y una migración de EF Core — una
**cuarta zona** sobre las tres que C40 ya toca.

Y tiene una consecuencia concreta que conviene no perder: **sin ella, la condición de reactivación
de la tarea diferida de `generate=false` no es observable**. Esa tarea propone servir la parte
estructural de la ficha sin pagar una generación, y su criterio era *«que el uso real muestre
aperturas que no leen el argumentario»*. Sin telemetría de uso, eso no se puede comprobar.

Si entra, hay una línea que no se cruza: **se registra que hubo pregunta, nunca su texto.**
`ProductSearchEvent.SearchText` sí guarda el texto de la búsqueda, con su limitación de retención
declarada en el §15.11, pero la pregunta de la ficha es de otra naturaleza — es lo que un cliente
dijo en voz alta sobre sí mismo— y tanto C34 como C36 la mantienen fuera de la URL, del historial y
de la consola por ese motivo.

#### 3 · Coste agregado: no se construye, se deriva

Con la observabilidad del punto 1 en los registros —que ya está— y la telemetría del punto 2, el
coste sale de sumar. Construir un contador de euros en el frontend sería poner una tarifa en el
sitio donde peor envejece.

---

## 5 · La regla de completitud: lo que la respuesta trae, la pantalla lo enseña

**Decisión transversal, y conviene que encabece la lista porque gobierna a las demás.** Todo lo que
una respuesta entrega tiene que llegar al frontal, **donde le corresponda**. Un campo que el
backend calcula, paga y devuelve, y que la pantalla descarta, es trabajo tirado y —peor— una
pantalla que sabe menos de lo que el sistema sabe.

La sesión encontró **tres infracciones** de esta regla, y ninguna era intencionada:

| Dato | Lo calcula | Llega al frontal | Dónde corresponde |
|---|---|---|---|
| `degraded_reason` (6 valores) | .NET | **no** | Ficha y panel: distingue pieza no indexada de caída |
| `usage`, `ai_ms`, `total_ms`, `model` | Python y .NET | **no** | Embudo de administrador |
| `abstained` | Python | **no** | El vacío del panel |

**Por modo**, lo que debe subir:

| | M1 (consulta libre) | M2 (pieza) | M3 (pieza y pregunta) |
|---|---|---|---|
| **Argumentario** | **sí** | sí *(ya)* | sí *(ya)* |
| **Citas** | **sí**, con su `claim_scope` | sí *(ya)* | sí *(ya)* |
| **Avisos** | **no** — son de una pieza y aquí hay quince (D8) | sí *(ya)* | sí *(ya)* |
| **Grupos** | **sí**, y la fila los usa (H4) | sí *(ya)* | sí *(ya)* |
| **`intent` / rechazos** | **sí** — sólo aquí llegan | no aplica | no aplica |
| **`abstained`** | **sí** | no aplica | no aplica |
| **Observabilidad** | **sí**, para administrador | **sí** | **sí** |

En M2 y M3 **aplica todo**, y la ficha de C36 ya lo pinta salvo la observabilidad y el motivo de
degradación. En M1 la única exclusión es la de los avisos, y está razonada y medida en D8.

**Verificación exigible en el *apply*:** recorrer campo a campo `SalesAssistResponse` y
`AssistedSearchResponse` y, por cada uno, o señalar dónde se pinta o declarar por qué no. Es la
misma disciplina que C36 aplicó a los siete códigos de aviso, y es la que habría cazado estas tres.

---

## 6 · Preguntas resueltas

Las cuatro se cerraron con el desarrollador en la sesión.

### Q1 · ¿El argumentario en cada búsqueda, o a petición? — **en cada búsqueda asistida** (cerrada)

Se genera **cada vez que el operario pulsa Buscar con el toggle en asistida**. M2 y M3 siguen como
están desde C34: una petición por visita a la ficha, más una por pregunta.

**Lo que resuelve esta decisión**, y era la tensión que la dejaba abierta: el enrutador corre en la
misma llamada, así que **el rechazo cortés llega a tiempo**. Si el argumentario fuese un segundo
acto, una consulta fuera de dominio se listaría como si fuera de catálogo y sólo al pedir el texto
se sabría que no lo era — que es exactamente el defecto que C40 viene a corregir.

**El coste queda acotado por el toggle**, que es quien lo hace explícito: la ruta semántica sigue
costando un embedding, y quien quiera buscar barato la tiene a un clic. La regla de C16 —*«una
búsqueda sólo cuando el operario la pide»*— se conserva íntegra: no hay búsqueda al teclear, ni al
cambiar un filtro, ni al cambiar de tienda.

### Q2 · ¿Y una cita retirada por la puerta de integridad? — **decirlo** (cerrada)

Se pinta **«sin fuente verificable»** en lugar de callar. Es la salida intermedia de las tres: no
retira el argumentario —que sería coherente con `withheld_unresolved` pero tira una respuesta
correcta— y no finge una atribución que no hay.

**Y la frecuencia ya está medida**, cosa que en la primera versión de este informe di por pendiente
sin haber mirado. Los datos de C30b (H6) la dan para los modos anclados: **30,5 %** de las citas
declaradas se retiran, **38,3 %** de las generaciones pierden alguna, y **11,7 %** acaban sin
ninguna. Siempre por `claim_not_in_pitch`, nunca por una cita inventada.

Eso convierte la etiqueta en algo **frecuente, no excepcional**, y por tanto en una decisión de
interfaz con peso: aparecerá en aproximadamente una de cada nueve respuestas del modo anclado. Dos
consecuencias de diseño:

- **La etiqueta no puede alarmar.** No es una alucinación cazada: es una cita que existía y cuyo
  tramo de apoyo no se pudo verificar palabra por palabra. Decir *«sin fuente verificable»* es
  exacto; decir *«posible invención»* sería falso.
- **Vale la pena distinguir «no había corpus» de «lo había y no se pudo verificar»**, porque hoy
  las dos se ven igual: sin citas. La primera es la ruta de catálogo, donde es correcto; la segunda
  es esto.

**Lo que sigue sin medir** es el mismo reparto **para M1**, que es el modo que C40 pone en pantalla.
La sonda de esta sesión dio 2 de 4, que no es una tasa. Y el arnés ya guarda lo necesario —
`pitch_violations` e `initial_violations` con su causa—, así que es una pasada, no un desarrollo.

### Q3 · ¿Y una consulta `in_domain` sin ruta? — **pedir que se reformule** (cerrada, y matizada por la medición)

Una frase que diga que no se ha entendido bien la pregunta y que invite a formularla de otra
manera. Es el tratamiento honesto de un estado en el que el clasificador admitió la consulta y no
supo encaminarla: no es un fallo, no es una abstención del catálogo y no es un rechazo. Encaja con
el patrón de C36: los estados sin respuesta **terminan en una acción**, no en un punto.

**Con un matiz que la pasada de 42 obligó a añadir** (H7): en 4 de los 5 casos medidos la respuesta
**sí trae resultados** —quince piezas y hasta cinco citas— y lo único que falta es la prosa. Así
que el mensaje no puede sustituir a la pantalla: **los resultados se enseñan igual**, y la frase
ocupa el hueco del argumentario, no el de la lista.

Dicho de otro modo, este estado se parece mucho más a `not_generated` —*«los datos son los del
índice; el argumentario no se ha generado»*, que C36 ya sabe pintar— que a un vacío. La diferencia
es la acción: allí se invita a volver a pedir la ficha, aquí a reformular la consulta.

**Y las citas que llegan sin prosa no se pintan**, por la misma regla que C36 ya aplica: una cita es
la fuente de una afirmación, y sin afirmación no atribuye nada.

### Q4 · ¿El filtro de materiales, duro o blando? — **duro, porque lo pulsó una persona** (cerrada)

Si el operario pulsa el chip, está decidiendo, y el filtro excluye. Si no pulsa ninguno, no hay
filtro y entra el catálogo entero.

Es exactamente la regla que el módulo de filtros ya tiene escrita —*«lo que un humano pulsa filtra;
lo que una regla infiere del texto degrada»*— aplicada también a la ruta degradada, que hoy no la
aplica en absoluto.

**El riesgo se acepta y se declara**: el 8,5 % del catálogo sin materiales extraídos desaparece
cuando se filtra por material. La diferencia con el caso que el módulo rechaza es quién lo decidió:
allí era una inferencia del texto, aquí es un clic. Con tipo de pieza el riesgo es menor, porque la
cobertura es del 97,7 %.

---

## 7 · El change que sale de aquí: telemetría de uso y panel de administrador

**Decidido: va en un change propio** (cerrada). No cabe en C40 y no debe: es una **cuarta zona**
—migración de EF Core— sobre las tres que C40 ya toca, y su valor no depende de que C40 exista.

### Qué registra

Las tres cosas que hoy no dejan rastro, más lo que ya se mide y se tira:

| Acto | Qué se guarda |
|---|---|
| Abrir una ficha de venta | usuario, punto de venta, producto anclado, momento |
| Preguntar algo del cliente | **que hubo pregunta**, nunca su texto |
| Elegir una variante | el miembro elegido y si era o no el anclado |
| Buscar (M1 o semántico) | ruta usada, filtros, `intent`, número de resultados |
| De cada petición a la IA | `ai_ms`, `total_ms`, `model`, tokens de entrada y salida, `degraded_reason`, `pitch_status`, citas publicadas y retiradas con su causa |

**El molde ya existe y no hay que inventarlo**: `ProductSearchEvent` guarda desde C04
`UserId`, `PointOfSaleId`, `SearchSessionId`, `SearchText`, `FiltersJson`, `ResultsJson`,
`ResultsCount`, `SearchOrigin`, `TraceId`, `RetrievalMs`, `TotalMs`, `SelectedProductId`,
`SelectedFromRank` y `SelectedAt`. Es exactamente la forma que hace falta, incluida la parte
difícil: **atar la selección a la consulta que la originó y a su posición en el ranking**.

**Con una diferencia deliberada:** `ProductSearchEvent.SearchText` guarda el texto de la búsqueda,
con su limitación de retención declarada en el §15.11 del diseño. **La pregunta de la ficha no se
guarda.** Es de otra naturaleza —es lo que un cliente dijo en voz alta sobre sí mismo— y tanto C34
como C36 la mantienen fuera de la URL, del historial del navegador y de la consola por ese motivo.
Se registra que hubo pregunta; su contenido, no.

### La pantalla: un panel de administrador sobre todas las consultas

Acceso a **todas las consultas realizadas, las propias y las de otros usuarios**, con:

- **El listado**, filtrable por usuario, punto de venta, fecha, ruta y desenlace.
- **Por consulta**: qué se preguntó, qué ruta decidió el enrutador, cuántos resultados salieron,
  qué se eligió y desde qué posición, cuánto tardó y cuántos tokens costó.
- **Agregados**: coste por periodo y por usuario, latencia p50 y p95, tasa de degradación por causa,
  tasa de abstención, y **la tasa de citas retiradas por causa** — la medición que hoy sólo existe
  en un fichero de resultados del arnés.

**Y lo que esto desbloquea**, que es la razón de fondo para hacerlo: la condición de reactivación
de la tarea diferida de `generate=false` es *«que el uso real muestre aperturas que no leen el
argumentario»*. **Sin esta tabla no es observable**, y esa tarea propone ahorrar una generación de
p50 4,4 s en las fichas que sólo se abren para mirar precio y existencias.

### Por qué es un change y no un tramo

- **Zona distinta**: migración de EF Core, tabla, rutas de lectura y una pantalla de administrador.
- **Riesgo de privacidad propio**: guarda quién hizo qué, así que hereda el problema de retención
  que el §15.11 ya declara para la telemetría de búsqueda, y necesita decidirlo, no heredarlo.
- **No bloquea a C40 ni C40 a él.** La observabilidad *por petición* de C40 —el embudo del §4.1—
  no necesita ninguna tabla: son campos que .NET ya calcula y descarta.

---

## 8 · Lo que queda cerrado, y lo que se hereda

**No queda ninguna pregunta abierta de la exploración.** Las tres que lo estaban se cerraron con
medición:

> **Matizado por el §10** *(mismo día, contra el código)*: no quedan preguntas **de diseño**, y sí
> quedan **cinco cifras por publicar** — las B1 a B5 del §10.12. La primera, los marcadores en el
> argumentario de M1, decide si M1 tiene prosa.

| # | Pregunta | Estado |
|---|---|---|
| ~~A1~~ | ~~¿Cuántas citas se retiran en M1, y por qué causa?~~ | **Resuelta con la pasada de 42** (H6): 26,4 % de las declaradas, **24,3 % de las respuestas sin ninguna fuente** —el doble que en los modos anclados— y la reaparición de `dangling_citation`, que allí era cero |
| ~~A2~~ | ~~¿Con qué frecuencia se retiran citas y por qué causa?~~ | **Resuelta con datos que ya existían.** Ver H6: estaban en `c30b-assist-sweep-*.json` sin partir por causa |
| ~~A3~~ | ~~¿El servicio debería emitir los avisos por pieza?~~ | **Resuelta.** Los avisos van **sólo en la ficha de venta**, donde hay exactamente una pieza. En el listado de M1 no se pintan, porque el servicio los calcula sólo para la primera (D8), y la ficha los trae por su cuenta al abrirse |

### Lo que la última medición añade al alcance de C40

Dos cosas que no estaban antes de medir, y ninguna cambia las decisiones ya tomadas:

- **`route=none` necesita copia propia y no es un vacío** (Q3 matizada, H7). Dispara en el **11,9 %**
  de las consultas libres, y en cuatro de cada cinco **trae resultados sin prosa**. Va al tramo 3
  de la línea de corte, con los otros vacíos.
- **La etiqueta «sin fuente verificable» aparecerá en una de cada cuatro respuestas de conocimiento
  en M1**, no en una de cada nueve como en los modos anclados. Sigue siendo la decisión correcta de
  Q2, pero a esa frecuencia **conviene que sea discreta**: una línea junto al argumentario, no una
  alerta.

### Lo que queda anotado para quien venga después, y no es de C40

- **`dangling_citation` vive en la ruta `both`**, a 1 de 42. `v3` lo eliminó en `catalog` diciéndole
  al modelo que devolviera la lista vacía; en `both`, donde hay catálogo *y* corpus, vuelve a
  componer identificadores. La puerta lo caza y el coste es un argumentario perdido, así que **no
  es urgente**, pero es trabajo de prompt —un `v5`— y no de pantalla.
- **La tasa de `claim_not_in_pitch` es del orden del 30 % en los dos modos.** Bajarla es trabajo de
  prompt sobre la instrucción del tramo de apoyo, y mejoraría la atribución de todas las pantallas
  a la vez. También fuera de C40.

---

## 9 · Reproducir las mediciones de este informe

Con `jbg-ai` levantado en `STUB_MODE=false` y credencial real:

```sh
# H1 — los filtros de la ruta degradada (vía .NET, con AiSearch apagado)
curl -s -X POST localhost:5056/api/ai/search -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"plata","pointOfSaleId":"<pos>","pageSize":6,"category":"pendientes"}'
#   → devuelve anillos y colgantes

# H2 — los filtros de la ruta asistida (directo al servicio, salta el interruptor)
curl -s -X POST localhost:8001/v1/retrieval/products -H "Authorization: Bearer $JWT" \
  -d '{"query":"plata","top_k":10,"filters":{"category":"pendientes"}}'
#   → sólo pendientes

# H5, H6, H7 — el modo libre y lo que el servicio registra
curl -s -X POST localhost:8001/v1/assist/sale -H "Authorization: Bearer $JWT" \
  -d '{"product_id":null,"query":"¿la plata se puede mojar?","top_k":5}'
docker logs jpv-pv-jbg-ai 2>&1 | grep -E "stage=(knowledge|assist) "
#   → stage=knowledge citations=5 · stage=assist citations=none withdrawn=...

# H1 — cobertura de los campos que el filtro degradado necesitaría
psql -c 'select count("PieceType"), count(*) from "ProductAiProfiles"'
#   → 1172 / 1200
```

El JWT se firma HS256 con `JWT_SECRET` y las cuatro claims congeladas —`user_id`, `role`,
`pos_id`, `trace_id`—, como documenta `ai-service/README.md`.

---

# 10 · Segunda pasada: la exploración contra el código de las tres capas

**Fecha:** 2026-09-24, el mismo día · **Método:** verificación de las diez decisiones contra
`ai-service/src/jbg_ai/`, `backend/src/` y `frontend/src/`, más los apuntes de las sesiones S4, S9,
S11 y S16 del máster

Todo lo de arriba se midió contra el servicio en marcha. Lo que sigue se ha verificado **contra el
código**, que es una pregunta distinta: no *«qué devuelve el sistema»* sino *«qué deja hacer el
sistema»*. **Ocho de las diez decisiones se sostienen tal cual.** Dos chocan con invariantes fijadas
y con test detrás, y aparecen **cuatro huecos** que cambian la línea de corte.

La tabla de estados completa vive aparte, en
[c40-m1-panel-states.md](c40-m1-panel-states.md), porque es un entregable y no un párrafo.

---

## 10.1 · F1 · .NET rechaza M1 hoy, por construcción, y el motivo es el que C40 tiene que resolver

**Es el hallazgo que gobierna la línea de corte.** No es una pieza que falte: es un guardia
explícito, con su razón escrita, repetida en tres sitios.

```csharp
// AiGatewayClient.cs:668-677
// The contract also serves a free query with no product. This client refuses it: the
// placeholders of the generated argument name no product, so with several pieces on the
// table there is nothing to resolve them against.
if (string.IsNullOrWhiteSpace(request.ProductId))
    throw new ArgumentException(
        "Sale assistance requires an anchored product. Without one the price and stock "
        + "placeholders of the argument cannot be resolved.", nameof(request));
```

| Sitio | Qué dice |
|---|---|
| `AiGatewayClient.cs:671` | lanza `ArgumentException` si no hay `product_id` |
| `AiAssistSaleDtos.cs:28` | *«the client refuses to issue one»* |
| `PitchPlaceholderResolver.cs:37` | *«No anchor, no resolution … Called without an anchor, this withholds, **always**»* |

Y la cadena completa:

```
prompt assist/v3, regla invariante (línea 47):
   «El precio y la disponibilidad son SIEMPRE marcadores. Escribe {{price}} … {{stock}}»
   ← aplica a las SEIS secciones de tarea, incluidas las tres de consulta libre
                              │
   medido en C30b (modos anclados):  {{price}} en 147/213 · 69 %
                                     {{stock}} en 188/213 · 88,3 %
                              │
              M1 no tiene ancla, por definición
                              ▼
   PitchPlaceholderResolver.Resolve(pitch, null) → Withheld, siempre
                              ▼
        PitchStatus.WithheldUnresolved → la pantalla no enseña argumentario
```

**Y por qué la medición de arriba no lo vio.** Las 42 consultas del H6 se ejecutaron con `curl`
contra `localhost:8001`, o sea contra Python, **saltándose la etapa de resolución de .NET**. Cuando
el §2 dice «37 respuestas con argumentario», eso es cierto *del servicio* y **no dice nada de lo que
el operario vería**. Con la tasa de C30b, la mayoría de los argumentarios de las rutas `catalog` y
`both` morirían en la frontera.

Es, otra vez, exactamente la avería del §1: **una capacidad que la pantalla presentaría como
encendida y estaría apagada.** Sólo que esta vez la crearía C40.

**Consecuencia sobre la línea de corte: el tramo 2 tal como estaba escrito —`filters` en
`AssistRequest` más el toggle— entregaría un panel cuyo modo asistido casi nunca tiene prosa.** Hay
que cerrarlo *dentro* del tramo 2.

### D11 · El argumentario de la consulta libre no habla de precio ni de disponibilidad (cerrada)

**Dos piezas, y las dos hacen falta.**

1. **`assist/v5`**: las tres tareas de consulta libre dejan de pedir marcadores y **prohíben hablar
   de precio y de existencias**. El lenguaje comparativo sigue permitido —*«el más asequible de los
   tres es el colgante»*— porque no lleva cifra y no toca la lista negra de marcadores.
2. **Una causa dura en la puerta**, `placeholder_in_free_query`, activa **sólo** cuando
   `product_id is None`.

Y en consecuencia, el guardia de `AiGatewayClient.cs:671` **se retira**, porque su motivo queda
resuelto y no simplemente asumido.

**Por qué las dos y no sólo el prompt.** Es la doctrina del propio proyecto y la del máster:
*«un guardrail es código, no una frase en el prompt»* (S16). El prompt es la petición; la puerta es
la garantía. Con `v5` funcionando, la causa dispara casi nunca y no cuesta nada: **silenciosa
cuando el prompt se porta, ruidosa cuando no** — y, sobre todo, **medible partida por causa**, que
es como este repositorio lee su puerta desde C30b.

**Alternativas consideradas:**

| Alternativa | Por qué no |
|---|---|
| **.NET neutraliza los marcadores** («disponible por {{price}}» → «disponible por») | Castellano roto, o .NET escribiendo prosa. Es literalmente el *«normalising spellings would be guessing what the model meant»* que el resolutor ya rechaza |
| **Resolver contra un miembro representativo** (el primero del primer grupo, que es lo que `_focus_of` ya hace para los avisos) | Es el fallo que el docstring del resolutor nombra — *«would put the price of one piece next to the description of another»*. Y **D8 ya rechazó el movimiento análogo para los avisos**: aceptarlo para precios sería incoherente, y una cifra de precio equivocada en el mostrador es peor que un aviso equivocado |
| **No generar en la ruta `catalog` de M1** | **La mejor descartada, y queda nombrada como corte.** Ahorraría cerca del 40 % de las generaciones de M1 —`catalog` es la ruta más frecuente, 15 de 42— y eliminaría el riesgo donde aparecen los precios. Se descarta porque quita lo principal que el toggle compra sobre una consulta de piezas —*qué tienen en común, cuál encaja*— y adelgaza la ablación de D3. **Si la latencia del §10.5 no cabe, éste es el corte** |

**Verificación exigible:** recuento de `{{price}}` y `{{stock}}` sobre el texto generado de las 42
consultas, antes y después de `v5`. Es la cifra que hoy no existe y la que decide si M1 tiene prosa.

---

## 10.2 · F2 · M1 no tiene la salvaguarda de cobertura que M3 sí tiene

En M3, cero citas tras el umbral **significa** que el corpus no cubre la pregunta, y eso se
convierte en una sección de prompt distinta y en un código de aviso:

```python
# assist/orchestrator.py:311-318  — SÓLO en la rama anclada
uncovered = not citations          # → WARNING_KNOWLEDGE_NOT_COVERED
# → resolve_task(...) → PitchTask.PIECE_AND_QUERY_UNCOVERED
#   «no finjas haber contestado la pregunta … no la respondas de memoria»
```

En M1 no existe. `resolve_task` para `QUERY_ONLY` elige **sólo por ruta**, y `FREE_QUERY_TASKS`
tiene tres entradas sin variante «sin cobertura» (`prompt.py:139-145`). Así que una consulta de
conocimiento en M1 con cero fragmentos ejecuta la tarea que dice *«Responde a la pregunta
apoyándote en esos fragmentos»* **sin fragmentos**. Es una invitación explícita a contestar de
memoria, en el modo que C40 saca a pantalla, sin la red que M3 tiene desde C34.

**Y el caso está medido arriba, leído como otra cosa.** En el H5:

| Consulta | Ruta | Piezas | Citas |
|---|---|---|---|
| un anillo que se pueda mojar en la piscina | `both` | 15 | **0** ⚠ |

El ⚠ se interpretó como *«las citas dependen de la ruta»*. Lo que es en realidad: **la tarea
equivocada corriendo sobre un contexto vacío.**

### D12 · `uncovered` se calcula también en M1, con su cuarta tarea de consulta libre (cerrada)

Tres cosas, todas en Python:

1. `uncovered` se calcula para `route in ("knowledge", "both")` en el modo libre, igual que en M3.
2. Una cuarta entrada en `FREE_QUERY_TASKS` —consulta libre sin cobertura— con la misma regla que
   la de M3: *no finjas haber contestado.*
3. `WARNING_KNOWLEDGE_NOT_COVERED` pasa a ser emitible en M1.

**La copia castellana ya existe** —`knowledge_not_covered: 'La documentación no cubre esta pregunta'`
en `frontend/src/lib/assist-copy.ts:51`, escrita por C36—, así que el coste de pantalla es cero.

---

## 10.3 · F3 · «Todos los puntos de venta» es una frontera de autorización, no un desplegable

D6 choca de frente con una invariante fijada, razonada y con test:

```
AiCallScope.cs:13   «There are EXACTLY TWO construction paths and no third.»
                    ForPointOfSale exige un POS concreto: «a sentinel value such as "*" or
                    "system" reaching it would be a cross-POS leak wearing a
                    convenience-parameter costume»
                    ForCatalog «is REFUSED by every point-of-sale operation of the client»
AiCallScopeTests    AiCallScope_ExposesNoPublicConstructor  ← la fija
auth.py:21          REQUIRED_CLAIMS = (user_id, role, trace_id, pos_id)
                    «Retrieval, sale assistance and inventory: the caller is always somewhere»
```

**La medición que D6 usa es correcta y verificada:** `GET /api/inventory/product/{productId}` lleva
sólo `[Authorize]` de clase, **sin restricción de rol**, y devuelve el desglose de las tres tiendas
a cualquier operario autenticado (`InventoryController.cs:222`). La casa ya es inconsistente.

Lo que D6 no decía es **cuánto cuesta cerrarla**: no es un desplegable, son cinco cosas.

### D13 · Una tercera clase de ámbito, explícita, y abierta a operarios (cerrada)

- Un `AiCallScope.ForAllPointsOfSale`, token **sin** claim `pos_id`, y un **tercer perfil de
  claims** en la ruta de recuperación y de assist.
- **Amplitud: operarios y administradores**, que es lo que D6 decidió. Va con **requisito y test
  que nombren quién puede**, no como efecto colateral de un desplegable.

**Por qué esta forma y no otra.** Es el patrón que el propio código declara —*«not a relaxation of
the first: it is a different scope»*—, es greppable y testeable, y el rechazo de `Catalog` queda
intacto. **El lado Python ya lo tolera**: `auth.py:44` dice *«Which claims are required is a
property of the route, not of the token»*, así que es un perfil más y no un agujero.

**Y el argumento que hay que escribir para defenderlo**, porque el comentario de `AiCallScope`
parece prohibirlo: lo que ese comentario teme es **un valor centinela llegando al filtro duro**. Una
claim **ausente** hace que el prefiltro **no se aplique**, no que «case con todo», y **falla
cerrado** en cualquier ruta que la exija —ficha, inventario—. Mismo resultado para la recuperación,
mecanismo distinto, y un test por cada operación que debe seguir rechazando el ámbito nuevo.

**Alternativas consideradas:**

| Alternativa | Por qué no |
|---|---|
| **N búsquedas, una por tienda** | N embeddings y N generaciones. Descartada sin discusión |
| **Sólo administrador en C40** | El delta de autorización más pequeño —los administradores ya reciben una excepción explícita en `AuthoriseAsync` y no tienen asignaciones— y suficiente para la demo. Se descarta porque no sirve el caso que D6 nombra. **Queda como la variante conservadora si el tramo 4 aprieta** |

**Y una precisión honesta sobre la fuerza del caso de uso:** la incoherencia medida es sobre
*mirar un producto que ya tienes*, no sobre *descubrir a lo largo de la cadena*, que es otra forma.
Y la consecuencia 3 de D6 deshabilita la ficha sin tienda, así que el operario no puede actuar sobre
el resultado sin cambiar de tienda. El caso se sostiene; no es tan fuerte como la incoherencia
sugiere.

---

## 10.4 · F4 · Dos interruptores, y un tercer eje que ningún interruptor ve

Cuatro propiedades operativas **ya difieren** y **ya están modeladas por feature**:

| | semántica (panel de hoy) | asistida (M1) |
|---|---|---|
| Interruptor | `AiSearch:EnabledByDefault` | `AiSalesAssist:EnabledByDefault` |
| Límite de tasa | **30/min** | **10/min** |
| Presupuesto .NET | **2.500 ms** | **10.000 ms** (mínimo 8.000) |
| Cliente HTTP y circuito | `ai-retrieval` | `ai-assist` |
| Método de gateway | `SearchAsync` | `AssistSaleAsync` |
| Forma de la respuesta | `results` — lista plana | `groups` — agrupado |

### D14 · M1 vive en un segundo endpoint de .NET, no en un campo `mode` (cerrada)

`POST /api/ai/search/assisted`, reutilizando hidratación y telemetría por composición.

- **Pros.** Cada ruta conserva su interruptor, su límite, su presupuesto y su circuito — los cuatro
  ya distintos. Los DTO se quedan honestos, sin un tipo unión `results ∪ groups`. Y **el precedente
  está escrito en el propio código**: `AiSalesAssistOptions` existe como sección propia y no como
  «más claves bajo `AiSearchOptions`» por este mismo motivo, razonado en su docstring — *«the card
  is a different feature … and its generative route has a cost profile search does not»*.
- **Contras.** Dos endpoints y fontanería compartida. Mitigable extrayendo hidratación más
  telemetría a un colaborador, que es casi lo que `AssistedSearchService` ya es.

**Alternativa considerada: un campo `mode` en `POST /api/ai/search`.** Más limpio de contar y
honesto como representación de «dos configuraciones de una búsqueda». Se descarta por una razón
mecánica y no estética: **el límite de tasa es un atributo de endpoint en ASP.NET**, así que
habría que elegir un único valor —30/min deja quemar treinta generaciones, 10/min estrangula la
ruta barata sin motivo— y el presupuesto de tiempo tiene el mismo problema: o la ruta de 0,9 s
espera diez segundos antes de fallar, o la de 7 s se corta.

### D15 · `SearchOrigin` gana un cuarto valor, y la ablación pasa a ser una consulta SQL (cerrada)

`SearchOrigin` se persiste con `HasConversion<int>()`
(`ProductSearchEventConfiguration.cs:57`), así que **un cuarto valor no abre migración**. Con
`AssistedGenerative = 4`, la ablación de D3 deja de ser una demo y pasa a ser **una consulta**:
misma consulta, dos rutas, dos poblaciones, con `RetrievalMs` y `TotalMs` ya en la tabla y
`FiltersJson` también.

El comentario del propio enum ya dice que su tercer valor existe para ser *«el brazo de control»*.
Coste: un valor de enum y su documentación. Es materia de rúbrica por lo que abajo se matiza.

### D16 · El badge tiene cuatro estados y necesita una ruta de lectura que no existe (cerrada)

Con dos interruptores independientes hay cuatro combinaciones, y la que importa es la segunda:
**búsqueda encendida y assist apagado ⇒ la opción asistida del toggle se deshabilita con su motivo,
no cae en silencio.**

**Y D4 pide el badge *antes* de buscar, cuando hoy no hay de dónde leerlo:** `aiAvailable` viaja
**dentro** de la respuesta, o sea después. `AiHealthResponse` existe pero es de administrador y
describe infraestructura, no los interruptores por punto de venta. **C40 necesita una ruta de
lectura nueva, barata y sin IA**, que reporte los dos interruptores para un POS. No estaba en la
línea de corte.

**Y hay un tercer eje que ningún interruptor puede ver: el enrutador.** El estado 5 de la tabla de
estados —la IA respondió y el clasificador no corrió— no lo anuncia ningún interruptor; sólo
`intent=unclassified`. Así que el badge cubre la disponibilidad *antes* y ese estado cubre la
degradación *durante*: **son dos avisos, no uno.**

---

## 10.5 · Latencia: el número que decide si esto se usa

```
M1, ruta `both`, extremo a extremo:
  enrutador gpt-4o        ~2.000 ms   (timeout_s=2.0, DEFERRED_TASKS)
+ embedding + vector + léxico
+ recuperación de corpus
+ generación gpt-4o-mini   p50 2.277 · p95 2.739 · máx 10.082 ms   (C30b)
+ ¿pasada de reparación?    una segunda llamada  (MAX_PROVIDER_CALLS = 3)
+ hidratación .NET
──────────────────────────────────────────────────────────────────
  presupuesto:  AssistTimeoutMs = 10.000, MinimumAssistTimeoutMs = 8.000
                                          ↑ ya está en su techo documentado
```

**El dato que hay que poner al lado de los 2,7 s de p50 del §2:** C34 midió **p95 7,1 s · máx
7,9 s** extremo a extremo por .NET **para los modos anclados, que no llaman al enrutador**. M1 le
suma ~2 s. El p95 de M1 se sienta plausiblemente en **~9 s contra un presupuesto de 10**, y el
presupuesto no se puede subir: diez segundos es el máximo declarado y ocho el mínimo validado al
arranque.

Los 2,7 s del §2 son de Python directo y con muestra pequeña. **No son el número del mostrador.**

Tres consecuencias:

1. **El toggle es la mitigación, y ahora tiene cifras.** D3 dice «un matiz que la interfaz debe
   decir»; el matiz es **2.500 ms contra 10.000 ms** de presupuesto y **30/min contra 10/min** de
   cupo. Un 4× de reloj y un 3× de cupo.
2. **Un spinner indiferenciado de siete segundos con un cliente delante es donde esta función se
   abandona.** Recomendación: la versión barata —esqueleto más una línea de expectativa— y
   **dejar el *streaming* / SSE explícitamente fuera de C40**, porque es una capa arquitectónica
   entera y no un detalle de presentación.
3. **Medirlo es tarea de C40, no de C38:** p50 y p95 extremo a extremo por .NET sobre las mismas 42
   consultas, como hizo C34. Es una pasada, no un desarrollo.

---

## 10.6 · D9 confirmada, con el mecanismo elegido y un requisito que faltaba

**Primero, una corrección que desactiva el riesgo que D9 se atribuía.** El conjunto dorado **no
contiene consultas filtradas**. Así que **ninguna cifra publicada se mueve** con ninguna de las
variantes: ni la tasa del 10 %, ni «2 de 20 fuera de dominio y 0 de 43 contestables». La diferencia
aparece sólo en consultas filtradas, que la calibración nunca vio. El argumento de D9 —*«moverlo
restaura la calibración»*— es cierto y, a la vez, **no observable sobre el conjunto dorado**. Eso
baja mucho el riesgo de tocarlo, en las dos direcciones.

### D17 · La abstención lee una sonda sin filtro, ejecutada sólo cuando hay filtros (cerrada)

Una segunda sentencia vectorial sin filtros, **reutilizando el embedding ya calculado** — no hay
segunda llamada al proveedor. Secuencial y no concurrente, para respetar la propiedad *«one pool
connection held at any moment (D10)»*. **Sin filtros las dos sentencias son idénticas, así que la
segunda se salta**: el coste se paga sólo cuando el operario ha filtrado, que es la minoría.

```
            ┌─ perfil SIN FILTRO plano ──▶ «No tengo nada que encaje con lo que describes»
sonda sin   │                              (el filtro es irrelevante)
filtro  ────┤
            └─ perfil con pico ──┬─ conjunto filtrado poblado ──▶ resultados + argumentario
                                 └─ conjunto filtrado escaso ──▶ «Hay piezas que encajan con tu
                                                                  descripción, pero ninguna es
                                                                  una diadema de oro»
```

**El coste no estorba** y el módulo de filtros ya lo midió: *«At 1.168 rows a hard filter saves no
time»*, o sea que el escaneo extra es de un dígito de milisegundos sobre las mismas 1.168 filas.

**Alternativas consideradas:**

| Alternativa | Por qué no |
|---|---|
| **Una sola sentencia sin filtro y filtrar en Python** | Convierte el prefiltro en **post-filtro**, que es lo que el H2 alaba y lo que los apuntes de S9 advierten en seco: *«El riesgo de post-filtering es perder recall cuando el filtro es muy selectivo»*. Medido aquí: `tipo=diadema` da **7 candidatos sobre el índice entero**, así que post-filtrar una ventana sin filtro de 30 daría casi ninguna diadema. Destriparía en silencio los filtros estrechos. **Descartarla es lo que hace necesaria la segunda sentencia** |
| **No mover la abstención; añadir sólo una señal de «filtro estrecho»** | Mucho más barato —un contador y una rama— y **no toca la regla calibrada**. Se descarta por una razón concreta: el mensaje *«hay piezas que encajan, pero ninguna es una diadema de oro»* **presupone que las piezas sin filtrar encajan**, y sin la sonda no se puede afirmar. Con una consulta incontestable y un filtro estrecho, **escribiría una frase falsa.** Con la sonda, el perfil sin filtro decide primero cuál de las dos frases se ha ganado |

**Y un requisito que nadie había escrito y que esta forma obliga a escribir.** La spec de
`retrieval-abstention` dice que la regla *«runs after the fusion and does not alter the candidate
set, which is what lets the calibration re-score persisted windows»*. Si el insumo de la regla pasa
a ser una lista de distancias **distinta** de la ventana persistida, `--rescore` deja de poder
recalcular la decisión **en las pasadas filtradas**. En las sin filtrar —todo el conjunto dorado—
nada cambia. Así que la spec tiene que decir dos cosas: **que la sonda es sin filtro y por qué**, y
**que sus distancias se persisten** si alguna vez va a re-puntuarse una pasada filtrada.

**Y el argumento de encaje que D9 no usaba y es el mejor que tiene:** la gravedad de esto **la crea
M1**. Antes de M1, un filtro estrecho enseñaba siete piezas mediocres. Con M1, enseña siete piezas
mediocres **y escribe un párrafo hablando bien de ellas**. Eso convierte a D9 en trabajo de C40 y no
en un change aparte, aunque toque una spec viva con tres consumidores — el panel, los sustitutos y
la tool `buscar_catalogo` del agente.

---

## 10.7 · Q3 se corrige: `route=none` son dos estados, y uno se arregla en el enrutado

El detalle está en [c40-m1-panel-states.md](c40-m1-panel-states.md) §1 y §4. El resumen:

**`route=none` no es un estado, son dos**, y sólo `intent` los separa:

| `intent` | Qué pasó | Copia correcta |
|---|---|---|
| `in_domain` | el clasificador corrió y **se contradijo**: devolvió `in_domain` con `index` nulo | «No he acabado de entender la consulta; prueba a formularla de otra manera» |
| `unclassified` | el clasificador **no corrió** — sin credencial, *timeout* de 2 s sin reintento, o respuesta no parseable | «El argumentario no está disponible ahora mismo» — **y no se le pide reformular** |

**Pedirle al operario que reformule en el segundo caso es echarle la culpa de una credencial
ausente**, que es la avería del §1 con otro disfraz. Las cinco consultas medidas en el H7 eran todas
del primer tipo (`router_degraded=False`), así que la copia de Q3 es correcta **para lo que midió**;
el otro camino existe y es el que dispara en un despliegue sin la credencial del enrutador.

**Y el primero admite un arreglo mejor que la copia: coerción a `both`** cuando el veredicto es
`in_domain`, `missing_axis` es nulo e `index` es nulo.

- El esquema dice de `index`: *«Null cuando **no se atiende**»*. Un veredicto `in_domain` **es**
  atender, así que la respuesta es internamente contradictoria y el código no puede saber a cuál de
  las dos mitades creer.
- **Los datos que la tarea necesita ya se están recuperando**: con `route=None` el *fail-open*
  consulta las dos ramas, recupera quince piezas y hasta cinco fragmentos, **y después tira la
  capacidad de escribir sobre ellos**. Es el trabajo tirado que la regla del §5 condena, dentro del
  servicio.
- Elimina el **11,9 %** de un estado degenerado en lugar de documentarlo, y es más fiel a la propia
  regla de desempate del prompt del enrutador: *«Ante la duda, `in_domain`»*.
- **La contradicción sigue siendo observable**: una causa propia en el registro
  (`router_index_absent`) y su recuento, sin tocar la respuesta.

**Alternativa descartada: un `model_validator` que rechace la combinación.** Haría fallar el parseo
→ *fail-open* → **el estado con la peor copia posible**. Mueve el 11,9 %, no lo arregla.

---

## 10.8 · Dos contradicciones internas de este informe, resueltas

1. **D8 se come los dos códigos de rechazo.** D8 dice *«los avisos no se pintan en el listado»*
   porque `warnings` describe una sola pieza. Pero `routing.refusal_codes` **se apila en esa misma
   lista** (`orchestrator.py:387`), así que D8 aplicado literalmente suprimiría
   `query_out_of_domain` y `query_not_in_catalogue`, que son justo los dos para los que §15.13
   obliga a escribir castellano. **La partición correcta es por sujeto del aviso:**

   | Sujeto | Códigos | En M1 |
   |---|---|---|
   | **una pieza** | `family_has_variants`, `size_label_missing`, y los dos de stock que apila .NET | **no se pintan** — D8, y sigue siendo correcto |
   | **la consulta** | `query_out_of_domain`, `query_not_in_catalogue`, `knowledge_not_covered`, y el nuevo `filters_too_narrow` | **sí se pintan** |

2. **El toggle no es un A/B test, y conviene no decir que lo es.** D3 dice que el toggle *«es la
   ablación, en pantalla»*. Lo elige el usuario y no un reparto de tráfico, así que sus dos
   poblaciones están sesgadas por quién elige qué: es una **demostración** de la ablación, no una
   medición. Lo que la convierte en medición es el cuarto valor de `SearchOrigin` (D15) más la
   telemetría de búsqueda que ya existe desde C04. **C39 debe decirlo así y no de más**, que es
   exactamente lo que S16 separa entre optimizar y demostrar que no has roto nada.

---

## 10.9 · Encaje con los apuntes del máster

| Nota | Qué respalda, y qué matiza |
|---|---|
| **S4 · De interfaz conversacional a interfaz de producto** | El respaldo más fuerte a D1 y D3. El panel no es un chat: es **«chat con parámetros»** —consulta, chips, selector de modo—, el mismo cuadrante que Perplexity con su selector *Search / Academic*. *«La información sobre qué pedir se puede hornear en la interfaz»* es literalmente D4, las consultas de ejemplo y los chips. Y *«¿dónde vive el prompt?»* ya está bien resuelto aquí: vive versionado en el backend, no en el textarea — que es precisamente lo que permite el `v5` de D11 |
| **S9 · Retrieval que no es sólo cosine** | Es el que **descarta el post-filtrado** de D17, con su propia frase. Y da el marco que faltaba: aquí los filtros van de baja selectividad (`pendientes`: 30 de 30) a alta (`diadema`: 7 de todo el índice). **Ni pre ni post sirven para todos**, de ahí la sonda separada |
| **S16 · Un sistema debe saber decir «No lo sé»** | Los tres caminos —responder, **abstenerse con honestidad** (*safe-completion*: «no puedo, y esto es lo que haría falta»), escalar a un humano— son la tabla de estados. El estado del filtro estrecho y el `route=none` son *safe-completion* de libro: **dicen qué haría falta** (quita el filtro, reformula). Y su tesis central —*«un guardrail es código, no una frase en el prompt»*— es la segunda mitad de D11 |
| **S11 · Citación y atribución verificable** | Respalda Q2 y el H6 |
| **S16 · Coste, latencia y A/B testing** | **Matiza D3**, y está en el §10.8 |

---

## 10.10 · La línea de corte, revisada

Sustituye a la del §4. El criterio de ordenación no cambia —*cuánto engaña hoy la pantalla*— y lo
que cambia es qué cae en cada tramo.

```
┌─ TRAMO 1 ─ lo que hoy miente en silencio · sólo .NET + frontend · archivable solo ────┐
│ D5   filtros en la ruta degradada  (JOIN + 2 AND — PieceType 97,7 %)                  │
│ D4   badge — CUATRO estados, no dos                                    ← D16          │
│      └── ruta de lectura nueva de los dos interruptores por POS. Sin IA ← NUEVO       │
│ L3   degraded_reason (6 valores) al DTO → cierra la limitación 3 de C34               │
│ D15  SearchOrigin = 4 → la ablación pasa a ser SQL. Sin migración       ← NUEVO       │
├─ TRAMO 2 ─ el contrato se mueve · y con tres prerrequisitos que no estaban ───────────┤
│ D2   filters en AssistRequest + openapi.json + AiAssistSaleRequest + stub              │
│ D11  assist/v5 · las tareas libres no hablan de precio ni disponibilidad ← PRERREQ.   │
│      + causa dura placeholder_in_free_query (product_id null)           ← PRERREQ.    │
│      + retirar el guard de AiGatewayClient:671, con su motivo resuelto   ← PRERREQ.    │
│ D12  uncovered en M1 + cuarta tarea «consulta libre sin cobertura»       ← NUEVO       │
│ D14  segundo endpoint .NET, con su interruptor, límite, presupuesto y circuito         │
│ D3   el toggle · §15.13 castellano de los dos rechazos                                 │
│ ★    LA TABLA DE ESTADOS, antes de una línea de código                  ← NUEVO       │
│ ★    medición de latencia p50/p95 extremo a extremo por .NET, 42 consultas ← NUEVO     │
├─ TRAMO 3 ─ toca retrieval-abstention, spec viva con tres consumidores ────────────────┤
│ D17  sonda sin filtro, sólo cuando hay filtros · los dos mensajes                      │
│      + requisito de persistencia para --rescore                         ← NUEVO       │
│      + filters_too_narrow como código del vocabulario cerrado           ← NUEVO       │
│ Q3′  route=none son dos estados · coerción a both · router_index_absent  ← CORREGIDO   │
│      + clarification_question, que en M1 SÍ llega                       ← NUEVO       │
├─ TRAMO 4 ─ D6 «todos los POS» — frontera de autorización ─────────────────────────────┤
│ D13  tercera clase de ámbito + tercer perfil de claims + tests de rechazo              │
│ D7   la etiqueta nombra la tienda · ficha deshabilitada sin tienda                     │
├─ TRAMO 5 ─ D10 la fila enseña su grupo ──────────────────────────────────────────────┤
├─ TRAMO 6 ─ embudo de observabilidad para administrador ──────────────────────────────┘
```

**Los dos movimientos que importan:**

1. **El tramo 2 crece con tres prerrequisitos.** Sin ellos no entrega un panel asistido: entrega un
   panel asistido sin prosa.
2. **D6 sube de «decisión de producto» a «frontera de autorización»**, lo que lo convierte en el
   mejor candidato a salir si la sesión aprieta — **por delante del embudo**, porque el embudo no
   arriesga nada y esto sí. La variante conservadora, si sale a medias, es sólo administrador.

Los tramos que no entren **se declaran aplazados con su motivo**, no se callan.

---

## 10.11 · Dos cosas de planificación

1. **C40 nace en el plan maestro con esta pasada.** Hasta hoy el plan llegaba a C39 y C40 sólo
   existía en este informe.
2. **El orden C38 ↔ C40 importa, y nadie lo había decidido.** C40 sube el prompt a `assist/v5` y
   mueve la fase de la abstención. Si C38 corriera primero, **sus cifras del modo libre describirían
   un prompt que C40 sustituye** y una fase de abstención que C40 mueve. **C40 va antes de C38**, y
   C38 mide `v5`. Queda anotado en las dos fichas.

---

## 10.12 · Lo que sigue sin medir después de esta pasada

No son preguntas abiertas de diseño: son cifras que la implementación tiene que publicar.

| # | Qué | Por qué importa |
|---|---|---|
| **B1** | **Marcadores en el argumentario de M1**, antes y después de `v5` | Decide si M1 tiene prosa. Es la cifra que F1 deja al descubierto y que no existe |
| **B2** | Reparto de los 16 estados sobre las 42 consultas | Es la única forma de saber cuál de las copias nuevas se va a ver y cuál casi nunca |
| **B3** | Latencia p50/p95 de M1 **extremo a extremo por .NET** | Los 2,7 s del §2 son de Python directo. El presupuesto está en su techo |
| **B4** | Tasa de `router_index_absent` tras la coerción a `both` | Convierte un estado degenerado del 11,9 % en una cifra de calidad del clasificador |
| **B5** | Efecto de la sonda sin filtro sobre la latencia de una búsqueda filtrada | El módulo de filtros predice un dígito de milisegundos. Conviene confirmarlo y no citarlo |

Y una nota de higiene: **la pasada de 42 consultas del H6 no quedó persistida** en
`ai-service/evals/results/` — no hay ningún `c40-*.json`. Sus cifras son reproducibles pero no
re-puntuables. La pasada de verificación de C40 sí debe persistirse con `run_id`, `git_sha` y
`prompt_version`, como hicieron C30b, C31 y C32b.
