## Context

C18a dejó el catálogo con **156 familias y 486 miembros**, escritos en un solo lote a través de `ProductFamilyService`, y reconciliados con una única sincronización incremental (`upserted 486, deleted 32, failed 0`). Estado medido el 2026-08-31 contra el Postgres local:

| | |
|---|---|
| `ai.product_document` | **1.168** · con `family_id` **486** · activos sin familia **682** (671 con `piece_type`) |
| `ProductFamilies` / `ProductFamilyMembers` | **156 / 486** — las 156 con `Origin = AiApproved`, **0 `Manual`** |
| Perfiles | 1.168 `Approved` · 32 `Rejected`, todos con `IsActive = true` |

Y con ello **dejó sin objeto la ficha de este change**, escrita antes de conocer ese resultado. Los tres números que manda pintar están caducados y el mecanismo que los produciría ya no los produce: los 15 miembros marcados vivían **sólo en la respuesta de `suggest`** —la decisión 3 de C18a fue no persistir propuestas— y los productos que nombran ya pertenecen a una familia, así que `build_candidate_groups` los excluye en su paso 1. Los grupos rechazados son 2 y no 4; los excluidos por la puerta, 11 y no 37; y `suggest` devuelve hoy **lista vacía**.

**Restricciones que gobiernan el diseño:**

- **`.NET` no mapea el esquema `ai`** — verificado: cero referencias en `Infrastructure/`. Los vectores son de Python, y la verdad del catálogo es de .NET.
- **La dirección de confianza es asimétrica.** .NET→Python va con JWT interno HS256; Python→.NET sólo tiene `X-Index-Feed-Key`, de **solo lectura**.
- **`ai-service/openapi.json` está congelado** en nueve rutas, con un test que falla ante cualquier diferencia.
- **El pool de conexiones está limitado a cinco** para todo el servicio: las similitudes se calculan en PostgreSQL con `<=>`, en el menor número de sentencias posible, y **los vectores nunca se cargan en Python**.
- **El watermark del feed** es `greatest(Product.UpdatedAt, perfil.UpdatedAt, familia.UpdatedAt cuando el producto es miembro actual)`. Sacar a un producto de una familia **exige el estampado**, o el feed incremental no lo emitiría nunca.
- **El turno de migración de EF Core ya no está en disputa**: anuladas las ramas de C19 y C29, el plan sólo contaba la de C27.

## Goals / Non-Goals

**Goals:**

- Que las 156 familias pasen por un juicio humano **por ítem**, y que ese juicio quede escrito.
- Que un producto que el agrupador se dejó fuera tenga **alguna forma de volver a ser visto**, cosa que hoy no existe: `suggest` converge excluyéndolo para siempre.
- Que un descarte se recuerde, de modo que la señal de calidad sirva más de una vez.
- Que el proyecto pueda declarar con un número **cuánto acierta el agrupador y cuánto cuesta revisarlo**.
- Que el criterio de la alerta se elija **midiendo**, no argumentando — la disciplina que salvó a C18a de su propio veto.

**Non-Goals:**

- La pantalla de revisión de perfiles de enriquecimiento y su endpoint de métricas — **C28**, segundo inquilino de la misma carcasa.
- Ampliar `piece_type.terms` y saltar a `enrichment/v2` — es `fix-enrichment-vocabulary-gaps`, sin número asignado.
- Reenriquecer producto alguno; cambiar `source-text/v1`, `embedding_version` o `indexing/embeddings.py`.
- Tocar la fusión por material, la guarda de raíz degenerada o el rango canónico de tallas de C18a.
- Persistir propuestas de `suggest`: lo que se persiste es el **veredicto sobre un par**, no una propuesta.
- Bifurcar `/health` o reabrir `aiAvailable: false`: distinguir servicio caído de lista vacía es **de esta pantalla y de su cliente** (decisión 9), no del contrato de salud, que C16 y C17 cerraron.

## Decisions

### 1 · Se audita lo que existe, no se pintan propuestas que ya no hay

El objeto de la pantalla son las **156 familias persistidas**, sus miembros no respaldados por el vector, y los **671 huérfanos activos con tipo de pieza**. El camino `suggest`/`apply` queda como vía residual para catálogo que entre después.

Construir la ficha literalmente entregaría **una pantalla vacía**: sería la cuarta aparición de la firma que este proyecto persigue desde C17, tras A1 en C04, B5 en C16 y el índice en C17 —donde el entregable *«compila, pasa, valida, y llega vacío»*—.

**Alternativas consideradas.** *(a) Literal a la ficha*: pantalla sobre `suggest`/`apply` más la alerta, asumiendo que se llenará cuando entren productos nuevos. Se descarta porque el change entregaría hoy una superficie sin contenido y las 156 familias seguirían sin revisar. *(b) Auditoría más rehacer el lote*: deshacer las 156 y reaprobarlas una a una por la pantalla. Se descarta porque movería el corpus dos veces más para obtener el mismo juicio humano que la auditoría produce sin tocar una sola fila de pertenencia.

### 2 · Marcados y huérfanos son el mismo predicado, y por eso van en una sola ruta

```
                    ai.product_document  (embeddings ya calculados, C13)
                                  │
            ┌─────────────────────┴─────────────────────┐
      family_id IS NOT NULL                     family_id IS NULL
        486 miembros                              671 huérfanos
            │                                           │
            ▼                                           ▼
  ¿un extraño está más cerca              ¿está más cerca de una familia F
  que su peor hermano?                     que el peor hermano de F?
            │                                           │
      MIEMBRO MARCADO                          HUÉRFANO CANDIDATO A F
            │                                           │
            └──────── mismo par (producto, familia) ────┘
                      mismo veredicto humano
```

Una consulta, un endpoint, un objeto de revisión. `apply_relative_veto` se reutiliza cambiando el universo de «familias propuestas» por «familias persistidas»; `load_member_similarities` cambia el conjunto de SKU y nada más.

### 3 · Python calcula, .NET conduce, y el contrato congelado se mueve a la décima ruta

`POST /v1/families/audit`. `openapi.json` se regenera y `test_openapi_snapshot_is_stable` se actualiza aquí mismo.

Lo decide una restricción dura: **.NET no mapea `ai`**, y los vectores viven ahí. Lo autoriza la doctrina que `IAiGatewayClient` lleva escrita —*«every other contracted endpoint is added by the change that first calls it»*— que C18a ya ejerció para la novena.

**Alternativas consideradas.** *(a) Extender la respuesta de `/v1/families/suggest`*: «no mueve el contrato» es falso, porque el snapshot compara el JSON entero y rompe igual; y mezclaría dos poblaciones **disjuntas** —agrupados y no agrupados— con cadencias distintas: `suggest` converge a vacío, la auditoría es señal permanente. *(b) Dos rutas separadas*, `/orphans` y `/review-queue`: duplica el join más caro para una pantalla que muestra ambas listas, y son once rutas. *(c) Computar en .NET*: exigiría que .NET leyera `embedding` de `ai`, rompiendo la frontera sobre la que descansa todo el proyecto. *(d) Reutilizar `/v1/retrieval/products`* con el texto del producto como consulta: semántica equivocada —es búsqueda híbrida, no distancia a pertenencias— y es la ruta de C14.

### 4 · El margen relativo nomina; la pureza de vecindad ordena

Se entró en el diseño con la hipótesis contraria: que el umbral relativo se dispararía en cientos sobre 671 huérfanos, y que la **pureza de vecindad** —de los *k* vecinos más próximos, cuántos son de una misma familia— sería más segura por estar acotada por construcción. **Medido sobre el corpus real, es al revés:**

| `data_origin` | huérfanos | **A** · margen relativo > 0,02 | **B** · pureza ≥ 3 de 5 | A ∧ B |
|---|---|---|---|---|
| `real` | 216 | **21** | 19 | 6 |
| `synthetic` | 434 | **1** | **55** | 0 |

**A dispara 95 % sobre catálogo real. B dispara 74 % sobre sintético**, que es exactamente la trampa que el `design.md` de C18a ya tenía documentada: *«clustering puro por embedding sin raíz fracasa en el sintético, donde `v2`/`v3`/`v4`/`v5` son casi-duplicados deliberados»*. La lista de B lo confirma línea a línea — `Anillo Llama Eterna v3` → `Anillo llama eterna v2`, `Collar Vía Láctea v2` → `Collar via lactea`, `Anillo Orión v3` → `Anillo orion v2`. Son familias distintas por construcción de C06b.

Curva del margen: `θ = 0 → 40` · `0,02 → 22` · `0,05 → 5` · `0,08 → 3`. Los **6 de la intersección A ∧ B** son el núcleo de alta confianza y encabezan la lista.

**Alternativas consideradas.** *(a) Pureza como nominador*: medida y descartada arriba. *(b) Umbral absoluto de similitud*: descartado ya en C18a, y por la misma razón — las poblaciones de peor hermano y mejor extraño se solapan. *(c) Comparar el **peor** parecido del huérfano con los miembros en vez del mejor* (`min_sim(h,F) − peor_hermano(F)`): medido, dispara 3 de 650. Es tan conservador que no encuentra ni los casos que se sabe que existen.

### 5 · Primero los miembros, después los huérfanos: una familia contaminada es un imán

De los 25 primeros por margen, **cuatro apuntan a la misma familia**: `Colgante estrella de mar`, con peor hermano **0,778** frente a una media de 0,85–0,95, porque se comió un sintético — el hallazgo (d) del informe de C18a. Como el criterio compara contra el peor hermano, **cuanto peor es una familia más huérfanos atrae**: `Colgante Ancla` entra con similitud 0,797 sólo porque el listón está por los suelos.

Se resuelve con orden y no con lógica. Limpiar la familia sube su peor hermano y esos falsos positivos desaparecen solos. Y de ahí se sigue la decisión 6: **θ no se fija hasta después de la auditoría de miembros**, porque fijarlo antes sería calibrarlo contra un defecto que el propio change arregla.

**Alternativa considerada.** *Sustituir el mínimo por un cuantil robusto* (p25 de las similitudes intra-familia). Añade un parámetro y una explicación por un efecto que el orden de ejecución ya elimina. Se anota por si tras la limpieza siguieran apareciendo imanes.

> **Revisión del 2026-09-01, al cerrar: la premisa no se cumplió, y la decisión queda sin comprobar.**
>
> Esta decisión da por hecho que `SKU610` es un intruso y que sacarlo subirá el peor hermano de `Colgante estrella de mar`. **La persona que revisó lo confirmó como miembro legítimo**, y es difícil llevarle la contraria: es un colgante de estrella de mar y la familia agrupa eso. La etiqueta `synthetic` marca la procedencia del dato, no un error semántico; C18a leyó *«un sintético dentro de una familia real»* como contaminación porque cruzó una frontera de origen, y el revisor leyó la única que le importa al catálogo.
>
> De modo que **no hubo limpieza, el listón no subió, y θ se fijó en 0 sobre los números de antes** — exactamente lo que esta decisión quería evitar, aunque por un motivo que no había previsto: no que se calibrara pronto, sino que no hubiera defecto que arreglar. La predicción **no queda refutada: queda sin comprobar**, porque el experimento no llegó a hacerse.
>
> Y la dispersión de esa familia resulta ser **real y no contaminación**: va de XS a L en dos acabados, y ese recorrido es el que hunde el peor hermano a 0,778. Eso reabre la alternativa que este apartado anotaba — un cuantil robusto discriminaría entre una familia amplia y una rota, cosa que el mínimo no hace —, y con una cola ya revisada por una persona hay por fin contra qué calibrarla. Medición completa en el §7.3 del informe del lote.

### 6 · El veredicto se persiste en .NET, y es a la vez descarte y sello por ítem

`FamilyReviewVerdict` sobre el par `(ProductId, FamilyId)`, con veredicto, revisor, instante, `MarginAtReview` y nota. Índice **único** sobre el par: un segundo juicio es una corrección, no una fila nueva. Borrado **en cascada** desde la familia.

Lo primero que hay que separar es **qué se descarta**, porque la ficha decía «lista de descartes de propuestas» y hay tres objetos distintos:

| Objeto | Clave estable | ¿Cuántos hoy? |
|---|---|---|
| Una **propuesta** de familia | **ninguna** — es raíz más conjunto de miembros | **0** |
| Un **miembro marcado** | `(ProductId, FamilyId)` | los que salgan de la auditoría |
| Un **huérfano candidato** | `(ProductId, FamilyId)` | los que salgan de la auditoría |

Los dos que existen **comparten clave**; el que la ficha nombra no tiene ninguna. Y esa misma fila **es el sello de aprobación por ítem** que la decisión 7 de C18a aplazó aquí por escrito. Una tabla responde a tres promesas.

**Por qué en .NET y no en `ai`.** Es la alternativa (a) que el `design.md` de C18a ya rechazó —*«crea un estado paralelo a .NET que nada invalida y que envejece en silencio»*— y el argumento se refuerza al concretarlo: `ai.product_document` es una **proyección** que se lapida y se reconstruye, así que una tabla a su lado no hereda su ciclo de vida; borrar una familia dejaría filas huérfanas que nada limpia; y el revisor sería un GUID opaco que la pantalla no puede resolver a un nombre. En `public`, la FK lo resuelve todo eso sin código.

**La contención que lo impedía ha caducado.** C18a rechazó la tabla porque *«el turno de migración de EF Core es único y lo esperan C19, C27 y C29»*. Anuladas las ramas de C19 y C29, el plan sólo cuenta la de C27, que además lleva corte pre-autorizado.

**Alternativas consideradas.** *(a) Tabla Alembic en `ai`*: arriba. *(b) Columnas `ReviewedAt`/`ReviewedBy` en `ProductFamilyMember`*: natural para el sello por ítem, pero **no cubre al huérfano**, que por definición no tiene fila de pertenencia, y sigue siendo migración. *(c) Sin persistir, en `localStorage`*: no se comparte, muere al cambiar de navegador, y sin memoria la alerta es inútil pasada la primera pasada.

### 7 · Auditar lee; los veredictos se escriben por otra ruta

`POST /api/ai/catalog/family-audit` no escribe **nada**. El registro va por `POST /api/ai/catalog/family-verdicts`. Es la misma separación que C18a impuso entre `suggest` y `apply`, y no es estilo: el criterio de aceptación que exige que la auditoría no toque el catálogo **sólo es verificable si el camino de escritura es otro**.

Los pares ya juzgados los envía .NET en la petición, igual que `apply` devuelve lo aceptado: el llamante trae el estado y Python no almacena ninguno, que es lo que le evita tener que leer `public`.

### 8 · Dos caminos de escritura de pertenencia, declarados

```
producto SIN familia  ──▶  POST /api/ai/catalog/family-suggestions/apply   (C18a)
producto CON familia  ──▶  PUT  /api/product-families/{id}/members         (C07)
```

Son contratos distintos con semánticas distintas, y la pantalla vive a caballo. **Siempre a través de `ProductFamilyService`, nunca por SQL**: el servicio es el único que mantiene el watermark coherente en las dos direcciones, y sacar a un producto exige el estampado o el feed incremental no lo emitiría jamás.

Y el segundo camino pisa **una mina ya documentada**. El apply de C07 dejó escrito que el reemplazo declarativo falla si las altas se declaran añadiéndolas a la colección de navegación —`BaseEntity` asigna el `Guid` en el constructor, así que EF toma al miembro nuevo por una fila existente y emite un `UPDATE` contra nada— y que *«sólo se manifiesta cuando una misma petición borra e inserta a la vez»*. **Mover un producto de una familia a otra es exactamente ese caso**, y lo cubre un test que reordena e intercambia etiquetas.

### 9 · Faltan dos endpoints de familia, y la pantalla distingue tres estados por lista

`ProductFamiliesController` tiene `GET {id}`, `POST`, `PUT {id}` y `PUT {id}/members`. **No hay listado** —una pantalla que revisa 156 familias no puede enumerarlas— ni **borrado**: disolver una familia mala obligaría a vaciarla con `ReplaceMembers([])`, dejando una familia fantasma sin miembros. La spec viva admite ese estado como legítimo, pero como resultado de «esta familia estaba mal» es basura. Ambos se añaden, sólo administradores, y el listado paginado a 50 como el resto.

**Y una decisión que se tomó dos veces el mismo día, porque la primera estaba mal.** Se recortó el comportamiento con `jbg-ai` caído, dejando el requisito de distinguir un fallo de una auditoría sin hallazgos **sólo en `ai-gateway-client`**. Revertido: **entra en alcance, y la pantalla distingue tres estados por lista**.

```
   ┌─ MIEMBROS MARCADOS ──────┐   ┌─ HUÉRFANOS ──────────────┐   ┌─ FAMILIAS (156) ─────────┐
   │  calculada · 0 hallazgos │   │  no disponible           │   │  calculada · 156         │
   │  «nada marcado»          │   │  «el servicio no         │   │  la revisión sigue       │
   │                          │   │   contestó»              │   │  operativa: no usa       │
   │                          │   │                          │   │  vectores                │
   └──────────────────────────┘   └──────────────────────────┘   └──────────────────────────┘
        estado (1)                       estado (2)                      estado (3)
```

Son estados **por lista y no de página**: la revisión de familias no depende de vectores y debe seguir funcionando mientras la auditoría no esté disponible.

El motivo del giro es que el requisito no puede vivir sólo en el cliente. `ai-gateway-client` sí debe distinguir un fallo de un resultado vacío —y su spec lo exige— pero eso no alcanza a la superficie que la persona mira: **una lista vacía pintada sin más *es* la respuesta equivocada, la distinga o no la capa de debajo**. Y aquí el daño es peor que en C17, donde la búsqueda devolvía diez resultados plausibles por el camino léxico sin decir que la asistencia estaba apagada: sobre una pantalla de **calidad de catálogo**, «no hay nada que revisar» se lee como **«el catálogo está limpio»**, que es justo la conclusión que el change existe para poder sostener con evidencia.

**Alternativa considerada.** *Dejarlo en el cliente y confiar en el manejo de error genérico del frontend*: es el recorte original, y falla porque el estado vacío y el estado no disponible se renderizan igual salvo que alguien lo pida explícitamente. Cuesta un escenario y un test, no un rediseño — y ése fue el argumento para recortarlo, que resultó ser el argumento para no hacerlo.

### 10 · El sinónimo `dorado` entra aquí, y su efecto se comprueba

`materials.synonyms += dorado: baño de oro`. Tres de los huérfanos de mayor margen —`Pendientes botón erizo de mar S dorado` (0,109), `Colgante Lapa Mini Dorado` (0,096), `Pendientes botón estrella de mar dorado` (0,056)— quedaron fuera por eso: `materials.terms` tiene `baño de oro` con `chapado en oro` y `gold plated` como sinónimos, y **`dorado` falta**.

Va en este change y no en `fix-enrichment-vocabulary-gaps` porque **el agrupador lee `name`, no `materials[]`**: el sinónimo recupera familias **sin reenriquecer y sin salto de prompt**. La otra mitad de aquel change —ampliar `piece_type.terms`— sí exige `enrichment/v2` y se queda donde está.

**Y no es gratis del todo.** Reconocer un token de material afecta a **todos** los nombres, no sólo a los tres buscados: puede fusionar grupos que no debían fusionarse o disparar la guarda de raíz degenerada en sitios nuevos. Por eso la primera tarea del change es el **diff completo de propuestas antes y después**, y no la comprobación de los tres casos. La hipótesis del mapeo es además **falsable**: si `dorado` fuese `oro`, dos miembros recibirían la misma etiqueta y el grupo aparecería rechazado por `duplicate_variant_labels` en lugar de fusionarse.

### 11 · Se reaprueban las 156, y revisar no mueve el corpus

Es lo que produce la evidencia del renglón *«métricas de revisión humana»* del checklist, que hoy **no tiene ninguna**: cero productos y cero familias han pasado por una revisión real.

Y sale barato en lo que más preocupa: **confirmar una familia sin cambiarla escribe una fila de veredicto y no toca `Product.UpdatedAt` ni el hash del documento**. Sólo mueve el corpus lo que la persona **cambia**, así que «revisar 156» y «mover el corpus» quedan desacoplados: probablemente se muevan una decena de documentos, no 486. Aun así el change va **antes de la línea base de C24**, por el argumento que ordenó a C18a: `preprocessing_id` sigue siendo `source-text/v1` y no delataría el cambio.

### 12 · Carcasa compartida, con C18b de primer inquilino y sólo lo que C28 pide por escrito

C18b y C28 son la misma pantalla dos veces —ambas *frontend + `Application/`*, sólo administrador, revisión por lotes de salida de IA— y EP13 ya las agrupa. C18b construye la carcasa; C28 es el segundo inquilino.

Lo que se generaliza es **exclusivamente lo que la ficha de C28 pide por escrito**: tabla editable, atajos de teclado, aprobación masiva y registro de quién revisó y qué cambió. Nada conjeturado. Diseñar para dos inquilinos con uno solo a la vista es la forma habitual de producir la abstracción equivocada; si C28 necesita más, lo extrae C28, que es cuando se sabrá qué.

> **Revisión del 2026-09-01, al cerrar: la carcasa no se extrajo, y C28 debe planificar con eso.**
>
> `/opsx:verify` lo destapó: **no se extrajo ni un componente compartido**. Todo vive en [`family-review.tsx`](../../../../frontend/src/pages/admin/family-review.tsx), 920 líneas, y los únicos ficheros nuevos de `frontend/` son esa página, su servicio, sus tipos, su test, la ruta y la entrada de menú. La frase *«C18b construye la carcasa»* sobrepromete y hay que leerla corregida: **C18b construye la primera pantalla; la carcasa, si hace falta, la extrae C28 de ella.**
>
> No se arregla extrayendo ahora, y el motivo es esta misma decisión: abstraer con un solo inquilino a la vista produce la abstracción equivocada. Con la pantalla escrita y usada de verdad, C28 tiene delante el caso concreto que aquí faltaba — y **de las cuatro cosas que la ficha de C28 pide por escrito, tres ya existen** en esta página: tabla editable *(edición de etiqueta por miembro)*, aprobación masiva *(los veredictos se acumulan y se envían en un lote)*, y registro de quién revisó y qué cambió *(`FamilyReviewVerdict`, con revisor, instante, margen y segundos)*.
>
> **La cuarta, los atajos de teclado, no se entregó y se descopa explícitamente.** La tarea 6.4 la daba por hecha y no existe: cero manejadores de teclado en la página. Entra en el alcance de C28, que es quien la pide por escrito, en vez de añadirse a última hora a una pantalla ya revisada por una persona — donde la prueba que importa es volver a recorrer una cola con ella, no un test que compruebe que el manejador está enganchado.

### 13 · Tres cosas que sólo aparecieron al revisar de verdad

*(Añadidas al alcance el 2026-09-01, después de ejecutar la revisión completa sobre el corpus.)*

Ninguna se veía leyendo el diseño. Las tres salieron de usar la pantalla para las 58 decisiones.

**Un veredicto no es una pertenencia, y la pantalla no lo decía.** Se registraron 58 juicios y el
catálogo quedó exactamente igual: 156 familias, 486 miembros, el sintético todavía dentro. Siete
decisiones se quedaron sin efecto y **nada lo señalaba**, porque la auditoría omite los pares
juzgados —que es lo que hace que un descarte se quede descartado— así que una decisión no ejecutada
desaparece de todas las listas y se lee como trabajo terminado. El arreglo es una lectura nueva que
devuelve, por cada juicio, la acción que el catálogo todavía necesita; el cálculo va en el servidor
porque sólo este lado conoce la pertenencia.

**Corregir una etiqueta era imposible desde la pantalla.** Un miembro ya dentro de una familia no
tenía ninguna forma de edición, y las cuatro correcciones de la primera revisión —una variante
olvidada en blanco, un material escrito de forma no canónica— hubo que aplicarlas por API a mano.
Es un hueco obvio en retrospectiva y no lo era antes de revisar: la pantalla sabía crear una
pertenencia y no enmendarla.

**El cronómetro moría con la pestaña.** La media vivía en estado de componente, la sesión se cerró
y con ella se perdió la mitad de lo que pide el §16. Ahora el tiempo se persiste **por juicio** y la
media se calcula desde lo guardado; cuando nada se cronometró se informa la ausencia y nunca un
cero, porque un cero afirma una revisión instantánea y la verdad es que no se midió.

Y una cuarta que salió al escribir el test de la métrica: **la población hay que capturarla al
registrar, no deducirla después.** Un miembro rechazado que se saca de su familia queda
indistinguible de un candidato rechazado —ninguno es miembro, ambos rechazados— así que derivarla
del estado actual falla exactamente en los juicios que sí se ejecutaron. `SubjectWasMember` lo
escribe el servidor en el momento del registro.

**Coste.** Dos migraciones más sobre la misma tabla nueva. Se aceptan porque el change ya tiene el
turno y ambas son columnas de su propia tabla; la alternativa —dejar la métrica mal o no tenerla—
falla el renglón del checklist que este change existe para cumplir.

## Risks / Trade-offs

- **Construir la ficha literalmente entrega una pantalla vacía** → Decisión 1, y es verificable: el criterio de aceptación exige que la auditoría devuelva sus listas sobre 156 familias y 671 huérfanos reales, no sobre propuestas.
- **La alerta puede degenerar en vertedero**, como el veto `mediana − k·MAD` de C18a que disparaba al 16,9 % → Decisión 4: el criterio se elige midiendo, y θ vive en configuración para poder barrerlo.
- **Una familia contaminada atrae falsos positivos** → Decisión 5: se resuelve con orden de ejecución, no con lógica ni con un parámetro más.
- **Mover un producto entre familias pisa la trampa de C07** → Decisión 8: miembros declarados por identificador, nunca añadidos a la colección de navegación, con test que reordena e intercambia etiquetas.
- **El sinónimo `dorado` puede fusionar de más** → Decisión 10: diff completo de propuestas antes de aceptarlo, y la hipótesis del mapeo es falsable por la guarda de etiquetas duplicadas.
- **Mover el contrato congelado a diez rutas** rompe `test_openapi_snapshot_is_stable` → Deliberado y regenerado aquí, como hizo C18a con la novena. Trabajando en solitario, el acuerdo con «quien posee el cliente .NET» que pide `CLAUDE.md` es una nota, no un bloqueo.
- **Un veredicto no se invalida cuando la evidencia cambia** → Se guarda `MarginAtReview` y se muestra junto al actual (*«revisado el T con margen 0,16; hoy 0,31»*), en lugar de una lógica de reaparición automática que nadie mantendría.
- **Revisar 156 familias puede degenerar en dar al botón**, que es el fallo que el mecanismo existe para evitar → El cronómetro por ítem hace visible el problema en la propia métrica de entrega.
- **La séptima migración** es la primera desde C08 → El arnés de desfase modelo↔migración existe desde C04 y lo heredaron C07 y C08. Y no compite por turno: la única otra viva es la de C27, con la que no se abre a la vez.
- **Los 21 huérfanos cuyo tipo de pieza no tiene ninguna familia** quedan fuera de la alerta por construcción → No es defecto: no hay familia a la que pertenecer. Se cuenta en el informe.
- **Una decisión registrada y no ejecutada es invisible** → Decisión 13: la lista de pendientes es una lectura propia, porque la auditoría omite los pares juzgados por diseño.
- **La métrica de tiempo se pierde si vive en la pantalla** → Decisión 13: se persiste por juicio. Ya ocurrió una vez, y el informe lo declara en lugar de rellenarlo.
- **Con `jbg-ai` caído, una lista vacía se leería como «el catálogo está limpio»** → Decisión 9: tres estados por lista, con escenario de aceptación y test. Es el riesgo de C17 trasladado a esta pantalla, y aquí la conclusión errónea es exactamente la que el change existe para sostener con evidencia.

## Migration Plan

**Hay migración de esquema** —`FamilyReviewVerdict`, la séptima del plan— y migración de datos. Cinco pasos, con vuelta atrás en cada uno:

1. **Medir la línea base y respaldar**: 156 familias, 486 miembros, 682 huérfanos activos, 1.168 documentos, distribución de márgenes. Volcado previo de `public` y `ai`, como hizo C18a con `pre-c18a.dump`.
2. **Aplicar la migración**. Reversible: la tabla nace vacía y `Down` la elimina sin tocar nada más.
3. **Añadir el sinónimo y diffear las propuestas** completas antes y después. Si degrada alguna raíz existente, se revierte el sinónimo y el caso se documenta — es un cambio de un fichero YAML, sin efecto persistido hasta que alguien aplique.
4. **Auditar miembros, fijar θ sobre números recalculados, auditar huérfanos**, y revisar las 156. Reversible por partes: un veredicto se corrige sobrescribiendo el par; un cambio de pertenencia se deshace por los mismos endpoints que lo hicieron.
5. **Reconciliar con `POST /v1/index/sync` incremental**, nunca `--full`, verificando que se emiten exactamente los productos estampados y ninguno más. Un `--full` **taparía** un fallo de estampado en lugar de exponerlo — decisión 8 de C18a, vigente.

**Vuelta atrás completa:** deshacer los cambios de pertenencia por los endpoints, vaciar `FamilyReviewVerdict`, revertir el sinónimo, y resincronizar. El respaldo del paso 1 cubre el caso de que algo salga peor de lo previsto.

## Open Questions

**Ninguna bloqueante.** Las seis que el ticket abrió el 2026-08-31 se cerraron el mismo día confirmando su opción por defecto, y quedan registradas con su motivo en [`ticket.md`](./ticket.md) § *Decisiones cerradas* y en la HU como **D14–D20**: `dorado` es sinónimo de `baño de oro` y no de `oro`; se acepta la etiqueta canónica aunque el taller diga `dorado`; un veredicto no se invalida solo; θ se fija tras la auditoría de miembros arrancando en `0`; el registro de veredictos es endpoint propio; y de la carcasa se extrae sólo lo que C28 pide por escrito. La séptima, el comportamiento con `jbg-ai` caído, se cerró dos veces el mismo día: primero como recorte y después revertida, al comprobar que dejar el requisito sólo en el cliente no alcanza a la pantalla (decisión 9).

Dos cuestiones siguen vivas, ambas **fuera del alcance de este change** y anotadas para que no se pierdan:

- **`fix-enrichment-vocabulary-gaps` no tiene número ni ficha en la tabla maestra.** Ampliar `piece_type.terms` con `diadema`, `gemelos`, `cinturon` y `llavero` y saltar a `enrichment/v2` mueve el corpus, así que debe ordenarse **antes de la línea base de C24** por el mismo argumento que ordena a éste. C18b no lo resuelve ni lo bloquea, pero deja 11 productos invisibles al filtro y a la puerta mientras no entre.
- **La divergencia entre la spec viva `product-family` y el código sigue sin corregirse.** Aquélla justifica la distinción con las colecciones diciendo que un producto puede pertenecer *«to one of many unrelated collections»*, pero [`Product.cs:31`](../../../../backend/src/JoiabagurPV.Domain/Entities/Product.cs#L31) declara `Guid? CollectionId`, una FK única y anulable: ambas cardinalidades son 0..1. Los discriminadores reales, medidos: una colección abarca 1–154 productos (mediana 15) y 13–16 tipos de pieza; una familia, 2–4 de un solo tipo. Heredada de C18a, que también la dejó anotada.
