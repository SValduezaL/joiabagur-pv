## Context

El servicio implementa **tres modos** de venta asistida y hasta hoy **dos llegan al operario**: el
argumentario de una pieza y la pregunta sobre una pieza, los dos en la ficha de C36. El tercero —la
pregunta libre sin pieza, **M1**— existe desde C30b, gana enrutador con C31 y sus consumidores son el
bucle del agente y el arnés de evaluación. Es la limitación **§15.12** del diseño, y con ella la
**§15.13**: `classify_query` corre **sólo en M1**, así que los dos rechazos corteses y la repregunta
del enrutador **no pueden emitirse** por ningún camino que tenga pantalla.

La exploración de este change ocurrió en **dos pasadas el 2026-09-24**: la primera contra el servicio
real (siete hallazgos, diez decisiones, cuatro preguntas cerradas), la segunda contra el código de las
tres capas (cuatro hallazgos, siete decisiones, dos contradicciones internas resueltas). La tabla de
estados de la pantalla vive aparte porque es un entregable y no un párrafo.

**El estado de partida no es el que la pantalla presentaba.** La comprobación en demo de C36 encontró
tres cosas, y las tres son el mismo problema —una capacidad apagada que la interfaz da por encendida—:

| Interruptor | Estado | Síntoma |
|---|---|---|
| `AiSalesAssist:EnabledByDefault` | `false`, ausente de todo `appsettings` | «El asistente no está disponible» |
| `AiSearch:EnabledByDefault` | `false`, ausente de todo `appsettings` | «Búsqueda asistida no disponible» |
| Filtros en la ruta degradada | **se descartan en silencio** | **ninguno** — los chips siguen pulsados |

**Restricciones que gobiernan el diseño:**

- El **contrato `openapi.json` está congelado** y, desde C34, `/v1/assist/sale` **tiene un consumidor
  .NET**: la ventana barata de C30a y C31 está cerrada, así que cualquier movimiento se paga en los dos
  lados.
- El **presupuesto de la ruta generativa está en su techo**: `AssistTimeoutMs = 10.000` con suelo
  validado de 8.000. C34 midió **p95 7,1 s** extremo a extremo **sin enrutador**, y M1 le suma ~2 s.
- **`AiCallScope` tiene «exactly two construction paths and no third»**, con un test que fija que no hay
  constructor público, y `ForCatalog` es **refusado** por toda operación de punto de venta.
- La **abstención de C25 está calibrada sin filtros**: sus dos parámetros se fijaron contra 20 consultas
  fuera de dominio y 43 contestables, ninguna de ellas filtrada.
- **Las dos suites vienen rojas de fábrica**, y la del frontend además **oscila entre 113 y 114** por un
  test dependiente del orden.

## Goals / Non-Goals

**Goals:**

- Que **los tres modos lleguen al operario**, cerrando §15.12 y §15.13 sin construir pantalla nueva.
- Que **ninguna capacidad apagada se presente como encendida**: ni un chip que no filtra, ni un
  asistente que no está, ni una pieza sin indexar que se ve como una caída.
- Que **los dieciséis estados que M1 puede devolver se distingan sin mentir**, y que ninguno se pinte
  con una frase que el sistema no pueda defender.
- Que la **comparación de las dos rutas sea medible en la base de datos**, no sólo demostrable en
  pantalla.
- Que el **contrato se mueva una sola vez y por adición pura**, verificada hoja a hoja.

**Non-Goals:**

- **Telemetría de uso** y su panel de administrador: cuarta zona con migración de EF Core, sale como
  change propio. Sin ella la condición de reactivación de `generate=false` sigue sin ser observable.
- **La ruta del agente**: sigue sin consumidor .NET y arrastra dos tareas diferidas de C32b.
- ***Streaming*** del argumentario: la puerta de integridad necesita el texto completo.
- **Euros** en ninguna parte de la interfaz: se enseñan las entradas de un coste, nunca el producto.
- **`dangling_citation` en la ruta `both`** (1 de 42) y la tasa de `claim_not_in_pitch` (~30 %): trabajo
  de prompt, no de pantalla.
- **Avisos por pieza** emitidos por el servicio: cambio de contrato aparte.

## Decisions

### D1 · El panel de C16 se convierte en M1; no hay pantalla nueva

El panel ya hace la mitad —misma recuperación, mismo selector de tienda, misma hidratación, mismo
episodio por visita— y M1 es ese panel más el enrutador, el corpus y la prosa.

**Alternativa descartada:** una pestaña o ruta aparte. Duplicaría el buscador, los filtros y el
selector de tienda para no reutilizar nada, y partiría en dos la telemetría de búsqueda.

**Encaje conceptual:** el panel no es un chat, es **«chat con parámetros»** —consulta, chips y selector
de modo—, el cuadrante donde la información sobre qué pedir está horneada en la interfaz. El prompt vive
versionado en el backend, que es lo que permite `v5` sin reentrenar a nadie.

### D2 · El argumentario de M1 no habla de precio ni de disponibilidad, y una puerta lo garantiza

**Es el prerrequisito que gobierna la línea de corte.** La cadena, verificada:

```
prompts/assist/v3.md:47  «El precio y la disponibilidad son SIEMPRE marcadores:
                          escribe {{price}} … {{stock}}»   ← las SEIS tareas, libres incluidas
        │
        │  medido en C30b, modos anclados:  {{price}} 147/213 · {{stock}} 188/213
        ▼
PitchPlaceholderResolver.Resolve(text, anchor=null) → Withheld, SIEMPRE
        │   «No anchor, no resolution … Called without an anchor, this withholds, always»
        ▼
AiGatewayClient.cs:671  throw ArgumentException  ← rechaza M1 antes de intentarlo
```

**Decisión: dos piezas, y las dos hacen falta.** `assist/v5` prohíbe hablar de precio y de existencias
en las tres tareas de consulta libre —el lenguaje comparativo sigue cabiendo, «el más asequible de los
tres», porque no lleva cifra—, y **una causa dura `placeholder_in_free_query`** en la puerta de
integridad, activa sólo cuando no hay pieza anclada, lo convierte en garantía. El prompt es la petición;
la puerta es la garantía: **un guardarraíl es código, no una frase en el prompt**. Y hace la frecuencia
**medible partida por causa**, que es como este repositorio lee su puerta desde C30b.

> **Medido en el grupo 4.7, y matiza esta decisión sin anularla.** El diagrama de arriba extrapola el
> 147/213 y el 188/213 de los modos **anclados** al modo libre. Sobre 90 consultas contra el proveedor
> real, `v3` escribió `{{price}}` **2 veces** y `{{stock}}` **1** — 2 de 90 generaciones, no la mayoría.
> El eslabón que de verdad impedía la prosa era el **tercero**, el guardia de la pasarela, que rechazaba
> M1 al 100 %. Las dos piezas siguen haciendo falta —la tasa de rechazo del modo libre cae de **8,9 % a
> 0 %** y la causa propia hace observable lo que antes era una caída sin explicación—, pero la magnitud
> del riesgo que evitan era **treinta veces menor** que la predicha.

| Alternativa | Por qué no |
|---|---|
| Sólo el prompt, sin puerta | Si el modelo escribe el marcador de todas formas, .NET retira el argumentario y **nadie ve por qué**: no hay causa que partir en el barrido |
| .NET neutraliza el marcador | «disponible por {{price}}» → «disponible por» es castellano roto, y rellenarlo es .NET escribiendo prosa. Es el *«would be guessing what the model meant»* que el resolutor ya rechaza |
| Resolver contra un miembro representativo | Es el fallo que el docstring del resolutor nombra: *«would put the price of one piece next to the description of another»*. Y D9 **ya rechazó el movimiento análogo para los avisos**; aceptarlo para precios sería incoherente, y una cifra de precio equivocada en el mostrador es peor que un aviso equivocado |
| No generar en la ruta `catalog` de M1 | **La mejor descartada, y queda como corte pre-autorizado.** Ahorra ~40 % de las generaciones de M1 y elimina el riesgo donde aparecen los precios, pero quita lo que el toggle compra sobre una consulta de piezas y adelgaza la ablación. **Si la latencia medida no cabe, éste es el corte** |

**Verificación exigible:** recuento de los dos marcadores sobre el texto generado de las 42 consultas,
**antes y después de `v5`**. Es la cifra que hoy no existe y la que decide si M1 tiene prosa.

### D3 · M1 vive en un segundo endpoint de .NET, no en un campo `mode`

Cuatro propiedades operativas **ya difieren y ya están modeladas por feature**:

| | semántica | asistida |
|---|---|---|
| Interruptor | `AiSearch` | `AiFreeQuerySearch` *(nuevo, sección propia)* |
| Límite | 30/min | 10/min |
| Presupuesto | 2.500 ms | 10.000 ms, suelo 8.000 |
| Cliente y circuito | `ai-retrieval` | `ai-assist` |
| Forma de la respuesta | `results` — lista plana | `groups` — agrupado |

**Alternativa descartada: un campo `mode` en `POST /api/ai/search`.** Más limpio de contar y honesto como
representación de «dos configuraciones de una búsqueda». Se descarta por una razón mecánica y no
estética: **el límite de peticiones es un atributo de endpoint**, así que habría que elegir un único
valor —30/min deja quemar treinta generaciones, 10/min estrangula la ruta barata— y el presupuesto tiene
el mismo problema. El precedente está escrito en `AiSalesAssistOptions`: *«the card is a different
feature … and its generative route has a cost profile search does not»*.

**Y el límite del endpoint nuevo es propio y no el de la ficha**: la ficha se abre una vez por pieza, el
panel se usa en ráfaga, y compartir el cupo dejaría a una de las dos sin poder trabajar.

### D4 · El badge tiene cuatro estados y necesita una ruta de lectura nueva

| `AiSearch` | asistida | Qué puede hacer el operario |
|---|---|---|
| on | on | las dos rutas del toggle |
| on | **off** | semántica sí; **la opción asistida se deshabilita con su motivo**, no cae en silencio |
| **off** | on | la semántica degrada a léxica; la asistida funciona |
| off | off | todo léxico |

`aiAvailable` llega **dentro** de la respuesta, o sea después, y `AiHealthResponse` es de administrador y
describe infraestructura. Así que hace falta **un `GET` barato, sin IA**, que reporte los dos
interruptores de un punto de venta.

**Y hay un tercer eje que ningún interruptor puede ver: el enrutador.** El estado «la IA respondió y el
clasificador no corrió» no lo anuncia ningún interruptor; sólo `intent=unclassified` en la respuesta.
**Son dos avisos —uno antes, uno durante—, no uno.**

### D5 · `route=none` son dos estados, y uno se arregla en el enrutado

La máquina, exacta. `is_sufficient` **es** `missing_axis is None`, e `index` es **nullable** en una
decisión servida y suficiente:

```
classify_query()
├─ decision is None ────────────────▶ intent=unclassified, route=None
│   (sin credencial · timeout 2 s ·   FAIL-OPEN: se consultan LAS DOS ramas
│    respuesta que no parsea)         task=None → SIN PROSA, con resultados y citas
└─ decision is not None
    ├─ served ≠ in_domain ──────────▶ rechazo, SIN recuperar, código propio
    ├─ missing_axis ≠ None ─────────▶ repregunta de plantilla, SIN recuperar
    └─ in_domain + suficiente
        ├─ index = null ────────────▶ route=None, LAS DOS ramas, task=None → SIN PROSA
        └─ index = catalog|knowledge|both ─▶ la ruta y su tarea
```

**El estado de «índice nulo» es una respuesta internamente contradictoria del clasificador.** El esquema
dice de `index`: *«Null cuando **no se atiende**»*, y un veredicto `in_domain` **es** atender. Dispara en
**5 de 42 · 11,9 %**, y hoy el servicio **ya paga las dos ramas** —quince piezas y hasta cinco
fragmentos— y después no genera porque no hay sección de tarea. Es trabajo tirado dentro del servicio.

**Decisión: coerción a `both`**, con la contradicción **observable** como causa propia en el registro
(`router_index_absent`). Es más fiel a la propia regla de desempate del prompt del enrutador —*«Ante la
duda, `in_domain`»*—: si se admite la consulta, se atiende.

**Alternativa descartada:** un validador que rechace la combinación. Haría fallar el parseo → *fail-open*
→ **el estado con la peor copia posible**. Mueve el 11,9 %, no lo arregla.

**Y la copia de los dos estados no puede ser la misma**, que es la corrección más importante a la
decisión original:

| `intent` | Qué pasó | Copia |
|---|---|---|
| `in_domain` | el clasificador corrió y se contradijo | «No he acabado de entender la consulta; prueba a formularla de otra manera» |
| `unclassified` | el clasificador **no corrió** | «El argumentario no está disponible ahora mismo» — **y no se le pide reformular** |

Pedirle al operario que reformule en el segundo caso es **echarle la culpa de una credencial ausente**.
Y no es un camino teórico: con la credencial del enrutador ausente, **todas** las consultas caen ahí.

### D6 · La abstención lee una sonda sin filtro, ejecutada sólo cuando hay filtros

Hoy los filtros entran como `AND` en el SQL —prefiltro, antes de puntuar— y `should_abstain` recibe las
distancias **ya filtradas**. Con un filtro estrecho la abstención **no puede dispararse**:

| Filtro | Candidatos | ¿Puede abstenerse con mínimo 15? |
|---|---|---|
| sin filtro | 30 | sí |
| `tipo=pendientes` | 30 | sí |
| **`tipo=diadema`** | **7** | **imposible** |
| **`tipo=pendientes + oro`** | **10** | **imposible** |

```
si filters vacíos:   UNA sentencia. Comportamiento idéntico al de hoy.
si no:               DOS, SECUENCIALES (una conexión del pool a la vez)
   1ª  sin filtros → distances_probe → should_abstain(probe, rule)
   2ª  con filtros → candidatos, orden y ventana   (prefiltrado intacto)
```

El embedding **ya está calculado**, así que no hay segunda llamada al proveedor, y el módulo de filtros
ya midió que *«at 1.168 rows a hard filter saves no time»*: el escaneo extra es de un dígito de
milisegundos y **sólo se paga cuando el operario ha filtrado**.

Lo que se gana son **dos mensajes que hoy no se distinguen**:

```
            ┌─ perfil SIN FILTRO plano ──▶ «No tengo nada que encaje con lo que describes»
sonda  ─────┤                              (el filtro es irrelevante)
            └─ perfil con pico ──┬─ filtrado poblado ──▶ resultados + argumentario
                                 └─ filtrado escaso ──▶ «Hay piezas que encajan con tu
                                                         descripción, pero ninguna es
                                                         una diadema de oro»
```

| Alternativa | Por qué no |
|---|---|
| Una sentencia sin filtro y filtrar en Python | Convierte el prefiltro en **post-filtro**. `diadema` da 7 candidatos de **todo el índice**, así que post-filtrar una ventana de 30 daría casi ninguna. Destriparía en silencio los filtros estrechos — y descartarla es lo que **hace necesaria** la segunda sentencia |
| No mover la abstención; sólo contar los que sobreviven al filtro | Mucho más barato y no toca la regla calibrada. Pero *«hay piezas que encajan, pero ninguna es una diadema de oro»* **presupone que las piezas sin filtrar encajan**: con una consulta incontestable y un filtro estrecho **escribiría una frase falsa**. Con la sonda, el perfil decide primero cuál de las dos frases se ha ganado |

**Una precisión que desactiva el riesgo que esta decisión parecía tener:** el conjunto dorado **no
contiene consultas filtradas**, así que **ninguna cifra publicada se mueve** —ni la tasa del 10 %, ni
«2 de 20 fuera de dominio y 0 de 43 contestables»—. Lo que sí obliga a escribir es un requisito nuevo:
la spec dice que la regla *«does not alter the candidate set, which is what lets the calibration
re-score persisted windows»*, y con un insumo distinto de la ventana persistida `--rescore` deja de
poder recalcular la decisión **en las pasadas filtradas**. Así que la sonda **declara que es sin filtro
y persiste sus distancias**.

**Y el argumento de encaje:** la gravedad de esto **la crea M1**. Antes, un filtro estrecho enseñaba
siete piezas mediocres; con M1 enseña siete piezas mediocres **y escribe un párrafo hablando bien de
ellas**. Por eso es trabajo de este change aunque toque una spec viva con tres consumidores —el panel,
los sustitutos y la tool `buscar_catalogo` del agente—.

### D7 · «Todos los puntos de venta» es una tercera clase de ámbito, no una relajación

```
AiCallScope.cs:13   «There are EXACTLY TWO construction paths and no third»
                    ForPointOfSale exige un POS concreto: «a sentinel value such as "*" or
                    "system" reaching it would be a cross-POS leak wearing a
                    convenience-parameter costume»
AiCallScopeTests    AiCallScope_ExposesNoPublicConstructor  ← lo fija
auth.py:21          REQUIRED_CLAIMS = (user_id, role, trace_id, pos_id)
```

**Decisión: una tercera clase explícita**, con un tercer perfil de claims en las rutas de recuperación y
de assist, **abierta a operarios y administradores**.

**El argumento que hay que escribir, porque el comentario parece prohibirlo:** lo que ese comentario teme
es **un valor centinela llegando al filtro duro**. Una claim **ausente** hace que el prefiltro **no se
aplique** —no que «case con todo»— y **falla cerrado** en cualquier ruta que la exija. Es el patrón que
el propio código declara para `ForCatalog`: *«not a relaxation of the first: it is a different scope»*.
Con un test por cada operación que debe seguir rechazándolo.

**Por qué se abre a operarios y no sólo a administradores:** no abre una puerta nueva, **cierra una
incoherencia**. `GET /api/inventory/product/{productId}` lleva sólo `[Authorize]` de clase, **sin
restricción de rol**, y devuelve el desglose de las tres tiendas a cualquier operario autenticado. La
variante conservadora —sólo administrador— queda como el corte del tramo 4.

**Tres consecuencias que se aceptan a propósito:** es **otro ranking**, porque sin ámbito `qty_bucket` y
`sales_30d` quedan a nulo —agregar el *bucket* de todas las tiendas cambiaría **6 productos de 1.194 ·
0,5 %**, así que no merece mecanismo propio—; **cambia el significado de los vacíos**, porque sin tienda
no hay contra qué hidratar y *«nada de esto está en tu tienda»* deja de poder decirse; y **la ficha exige
tienda**, así que sin ella su botón **se deshabilita** — cerrar la ambigüedad en la puerta es mejor que
arrastrarla a la ficha.

### D8 · Los avisos se pintan o no **por sujeto**, no por lista

`warnings` describe **la primera pieza del primer grupo**, no el conjunto: medido, sobre 15 piezas
`["family_has_variants", "size_label_missing"]` describiendo a un SKU cuyo grupo visible tiene **un solo
miembro**. Pintarlo como banda superior sería mentir. **Pero `routing.refusal_codes` se apila en esa
misma lista**, así que la regla leída al pie de la letra **se comería los dos códigos de rechazo** para
los que §15.13 obliga a escribir castellano.

| Sujeto | Códigos | En M1 |
|---|---|---|
| **una pieza** | `family_has_variants`, `size_label_missing`, y los dos de stock de .NET | **no se pintan** |
| **la consulta** | `query_out_of_domain`, `query_not_in_catalogue`, `knowledge_not_covered`, `filters_too_narrow` | **sí se pintan** |

**Y no se pierde nada**: al abrir la ficha, ésta emite **su propia** petición anclada a esa pieza, así
que sus avisos se calculan para ella.

### D9 · El toggle demuestra la ablación; lo que la mide es un valor de enum

`SearchOrigin` se persiste con `HasConversion<int>()`, así que **un cuarto valor no abre migración**. Con
él, la comparación de las dos rutas deja de ser una demostración y pasa a ser **una consulta** sobre
`ProductSearchEvent`, que ya lleva `FiltersJson`, `RetrievalMs`, `TotalMs` y `SelectedFromRank`. El
comentario del propio enum ya dice que su tercer valor existe para ser *«el brazo de control»*.

**Y conviene no decir de más:** **un toggle elegido por el usuario no es un A/B test.** Sus dos
poblaciones están sesgadas por quién elige qué, así que el toggle **demuestra** la ablación del §11.2 y
lo que la **mide** es este valor más la telemetría de C04. El README del PF debe decirlo así.

### D10 · La fila enseña su grupo

El agrupado por familia deduplica conservando el rango —*«a group takes the position of its best member
— so grouping never reorders what the ranking decided»*— y medido sobre 8 consultas con `top_k=10`
ahorra **194 filas de 240 · −19,2 %**, colapsando algo en **7 de 8**. Sin agrupar, *«colgante estrella de
mar»* gastaría **8 de sus 30 filas** en el mismo colgante.

**Pero la información que lo justifica se tira al pintar.** La fila dice qué otras tallas o
características lleva la familia, con `variant_label` de cada miembro y degradación al SKU cuando falta
—la misma regla que C36 aplica en el bloque de familia—, y **nada escrito** con un solo miembro. Es,
además, información que el modo semántico **no puede dar**: su lista es plana.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| **El argumentario de M1 no llega si `v5` no entra**, y la pantalla lo presentaría como disponible | `v5` y la causa dura son **prerrequisitos declarados del tramo 2**, que no admite corte, con la cifra de verificación —recuento de marcadores antes y después— como criterio de hecho |
| **El p95 puede sentarse en el techo.** C34 midió p95 7,1 s **sin enrutador**; M1 le suma ~2 s contra un presupuesto de 10 s que **no se puede subir** | Se **mide y se publica** extremo a extremo por .NET sobre las 42 consultas. El toggle es la mitigación de producto —la ruta barata a un clic, con su coste dicho antes—, y el corte pre-autorizado es **no generar en la ruta `catalog`** de M1 (≈40 % de sus generaciones) |
| **Siete segundos de espera indiferenciada con un cliente delante** es donde esta función se abandona | Esqueleto y una línea de expectativa desde el primer instante, nunca una pantalla en blanco. El *streaming* queda **explícitamente fuera**: es una capa arquitectónica entera |
| **D7 relaja una invariante fijada con test** | Se **añade una clase** y no se relajan las dos existentes; una claim ausente falla cerrado; y hay un test de rechazo por cada operación que debe seguir exigiendo punto de venta |
| **Once capabilities en el delta** (una nueva y diez vivas) | La línea de corte **agrupa los tramos por subconjunto de specs**, así que un tramo aplazado no deja ninguna spec a medias |
| **La sonda añade una ida y vuelta al pool, capado en 5** | Secuencial y no concurrente, respetando la propiedad de «una conexión a la vez»; y **no se emite cuando no hay filtros**, que es la mayoría de las búsquedas |
| **`--rescore` deja de poder recalcular la abstención en pasadas filtradas** | Las distancias de la sonda **se persisten**, y en las pasadas sin filtrar —todo el conjunto dorado— nada cambia. Se declara en la spec en vez de descubrirse |
| **El contrato congelado se mueve con un consumidor ya escrito** | **Adición pura**, verificada **hoja a hoja**: 0 hojas retiradas y 0 cambiadas de tipo. Un cliente que no envíe `filters` recibe el comportamiento de hoy |
| **Dieciséis estados y cinco ramas de vacío en el panel actual**: tres se pintarían mal por defecto | La **tabla de estados es el primer entregable**, antes de una línea de código, con un test por cada distinción que la pantalla tiene que sostener |
| **Las dos suites vienen rojas de fábrica**, y la del frontend oscila entre 113 y 114 | Línea base **por nombres de test**, nunca por número, medida antes de tocar nada. Los servicios se mockean con `vi.mock`, porque MSW con `onUnhandledRequest: 'warn'` deja pasar un test que no ha afirmado nada |
| **El corpus no viaja en la imagen de `jbg-ai`** (tarea diferida de C34) | **Pesa más aquí que en C36**: sin corpus, M1 responde siempre sin citas y la ruta de conocimiento parece vacía. Se comprueba en la verificación con datos reales y se declara si no está resuelto |
| **La consulta de M1 se persiste en `SearchText`** y hereda el problema de retención del §15.11 | Se **declara** en vez de heredarse en silencio. La **pregunta de la ficha sigue sin guardarse**, porque es de otra naturaleza: es lo que un cliente dijo en voz alta sobre sí mismo |

## Migration Plan

**Sin migración de EF Core y sin tabla nueva.** El cuarto `SearchOrigin` cabe en la columna `int` que ya
existe.

**Orden de despliegue**, y el orden importa en un sitio:

1. **`ai-service` primero**: `v5`, la causa dura, `uncovered` en M1, la coerción, la sonda, el tercer
   perfil de claims y `filters` en `AssistRequest`. Todo es **aditivo hacia atrás**: un .NET que no
   envíe `filters` y no use el ámbito nuevo recibe el comportamiento de hoy.
2. **`backend` después**: los filtros de la ruta degradada, `degradedReason`, el cuarto origen, la
   tercera clase de ámbito, el endpoint nuevo y su sección de configuración.
3. **`frontend` al final**: el toggle, el badge, los estados, la fila y el embudo.
4. **Encender los interruptores**, que es lo que la sesión de C36 descubrió que nadie había hecho:
   `AiSearch:EnabledByDefault` y el del endpoint nuevo, **anotados en la documentación de puesta en
   marcha**.

**Rollback**, en tres escalones y sin desplegar nada:

- **Apagar el interruptor del endpoint nuevo** → el toggle deshabilita su opción con su motivo y el panel
  se comporta como el de C16.
- **Retirar la credencial del enrutador** → el *fail-open* de C31 sirve lo que servía antes de que M1
  enrutara, y el badge lo dice.
- **`JPV_ABSTENTION_ENABLED=false`** → la sonda deja de decidir nada, y sin filtros ni se emite.

## Open Questions

Las diecisiete decisiones de diseño y las cuatro preguntas de producto están cerradas. Las once del
ticket **se resuelven aquí por su opción por defecto**, y quedan registradas para que el *apply* no las
vuelva a abrir:

| # | Pregunta | Resuelta como |
|---|---|---|
| 1 | Capability para el endpoint nuevo | **Nueva**, `ai-free-query-search`, por el precedente de `ai-sales-assist`. El panel se queda en `assisted-search-panel` modificada |
| 2 | Ruta del endpoint | **`POST /api/ai/search/assisted`** |
| 3 | El toggle recuerda la última ruta | **No**, y por defecto **la semántica** |
| 4 | Cupo compartido con la ficha | **No**: sección de configuración propia |
| 5 | Quién puede usar «todos los puntos de venta» | **Operarios y administradores**, con requisito y test |
| 6 | La consulta de M1 en `SearchText` | **Sí**, con la limitación del §15.11 declarada. La pregunta de la ficha **sigue sin guardarse** |
| 7 | `usage.model` como clave de precio | **No**: modelo y tokens, nunca el producto |
| 8 | La coerción a `both` como requisito | **Sí**, propio, en `assist-generation`. La causa de registro es interna |
| 9 | Persistir el artefacto de verificación | **Sí**, con `run_id`, `git_sha` y `prompt_version` |
| 10 | Generar también en la ruta `catalog` | **Sí**, salvo que la latencia medida no quepa; entonces se corta y **se declara** |
| 11 | `filters_too_narrow` en la ruta semántica | **Sí**: la sonda vive en `retrieval/`, así que el panel semántico gana la distinción sin coste añadido |

**Lo que sigue sin medir, y es trabajo del *apply*, no una duda de diseño:** el recuento de marcadores
antes y después de `v5`; el reparto de los dieciséis estados sobre las 42 consultas; la latencia p50/p95
por .NET; la tasa de `router_index_absent` tras la coerción; y el efecto de la sonda sobre la latencia de
una búsqueda filtrada.

**Regla por defecto si el *apply* descubre un detalle menor no listado:** la opción más estrecha que
**no** añada migración, **no** cambie el comportamiento de la ficha más allá de `degradedReason`, **no**
retire ni cambie de tipo ningún campo del contrato, y **no** suprima ningún dato que el backend haya
emitido.
