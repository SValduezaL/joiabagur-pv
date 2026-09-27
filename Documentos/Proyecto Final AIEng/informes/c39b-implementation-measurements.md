# C39b — evidencias del cierre del Proyecto Final

**Change:** `finalize-pf-readme-and-evidence` · **rama:** `c39b-finalize-pf-readme-and-evidence` desde
`ai-eng` · **fecha:** 2026-09-27 · **zona:** documentación.

Es el último change del Proyecto Final. No toca código ejecutable: lo que entrega es la capacidad de
alguien que no lo construyó de entender, reproducir y probar lo que hay. Este informe es el soporte de
todas las cifras que el entregable publica, y está escrito para que **cada una de ellas se pueda
reencontrar** en un comando o en un artefacto versionado.

**Regla que se aplica a todo lo de abajo:** si una cifra no tiene artefacto que la sostenga, aquí dice
*no medido*. No se rellena por analogía con la fila de al lado, y no se estima.

---

## 1. Condiciones de la medición

| Condición | Valor |
|---|---|
| Rama de partida | `ai-eng` en `a5ac757` |
| `origin/demo` | `7d3a15ae8bb2807a7fd97e0fcc096f90f9efd971` |
| Contenido `ai-eng` ↔ `demo` | **idéntico** — `git diff --stat origin/ai-eng origin/demo` sin salida |
| Árbol de trabajo | limpio salvo los ficheros de este change |
| `ai-service/openapi.json` | **no se mueve** — `git diff --stat ai-eng -- ai-service/openapi.json` sin salida |
| Tests que lean `ai-service/evals/results/` | **ninguno** — el artefacto de `--rescore` es inerte para las tres suites |
| Llamadas al proveedor | **cero**. `--rescore` recalcula sobre artefactos ya escritos |

**Por qué no se miden las líneas base de las tres suites.** Este change no compila ni ejecuta nada del
producto, y el único fichero que añade bajo `ai-service/` es un JSON que ningún test lee —comprobado con
`grep -rn "evals/results" ai-service/tests/`, sin resultados—. Medir tres suites de ~20 minutos en serie
para afirmar que un documento no rompe código sería ceremonia, no evidencia.

---

## 2. La frontera contable, y el criterio con el que se cuenta

Ésta es la única afirmación del entregable que **cualquiera comprueba en un comando**, y hasta hoy no
cuadraba. Conviven en la documentación «40 archivadas», «43 archivadas» y «44 archivadas», y la ficha de
C39b decía «74 archivados · 32 del MVP · 41 del PF». **No se contradicen por descuido: cuentan unidades
distintas sin decir cuál.**

### 2.1 · El criterio, escrito antes de las cifras

1. **La unidad canónica es el directorio.** Un directorio de `openspec/changes/archive/` = un change
   archivado. Se elige porque es lo único que un lector reproduce **sin leer el plan**, que es
   precisamente el documento cuyas cifras estaban en duda.
2. **La frontera es la fecha `2026-08-03`, con una excepción nombrada.** El prefijo del directorio es la
   fecha de archivado. Todo lo anterior es el MVP que ya existía; todo lo posterior es el Proyecto Final
   **salvo `2026-08-03-barcode-qr-scanning`**, que lleva la fecha del primer día del proyecto y es del
   MVP por contenido: es el escaneo de códigos en el mostrador, su capability viva es `barcode-scanning`
   y **no tiene ficha en el plan**. Una excepción nombrada es auditable; una regla de fecha a secas daría
   46 a cualquier lector que la aplicase.
3. **La segunda unidad es la ficha del plan, y se declara como tal.** Es la que usa `epicas.md`. No
   coincide con la primera **ni debe coincidir**, y la distancia se explica nombrando las entradas que la
   producen.
4. **Los directorios duplicados se declaran, no se borran.** Reordenar el archivo histórico para que un
   total sume redondo es lo contrario de hacer una cifra verificable.

### 2.2 · Las cifras, medidas contra el disco el 2026-09-27

```bash
ls openspec/changes/archive/ | wc -l                                  # 78
ls openspec/changes/archive/ | awk '$0 <  "2026-08-03"' | wc -l        # 32
ls openspec/changes/archive/ | awk '$0 >= "2026-08-03"' | wc -l        # 46
ls openspec/changes/archive/ | sed 's/^[0-9-]\{11\}//' | sort -u | wc -l   # 75
```

| | Directorios | Nota |
|---|---:|---|
| **Total archivado** | **78** | 75 slugs distintos — tres pares duplicados |
| **MVP** | **33** | los 32 anteriores al 2026-08-03 **más** `barcode-qr-scanning` |
| **Proyecto Final** | **45** | los 46 posteriores **menos** ese |

**El 32 valida la frontera por el lado del MVP:** coincide exactamente con la cifra que la ficha de C39b
atribuía a lo preexistente, escrita meses antes y sin este recuento delante.

**Los tres pares duplicados, y de qué lado caen.** Son directorios distintos con el mismo slug:

| Slug | Directorios | Lado |
|---|---|---|
| `add-payment-method-management` | `2025-12-14-…` · `2026-01-07-…` | MVP |
| `add-point-of-sale-management` | `2025-12-14-…` · `2026-01-07-…` | MVP |
| `refactor-class-label-to-sku` | `2026-01-17-…` · `2026-01-18-…` | MVP |

`refactor-class-label-to-sku` es **byte a byte idéntico** en sus dos copias; en los otros dos la copia
posterior no lleva el subdirectorio `specs/`. **Los seis son del MVP**, así que el recuento del Proyecto
Final no se ve afectado por la deduplicación en ninguna lectura. Son un residuo del flujo de la época y
**no se tocan**.

### 2.3 · La reconciliación entre las dos unidades, que sale de un cruce y no de una suposición

La reconciliación **no se supone: sale de un cruce**, programático, entre los directorios posteriores al
2026-08-03 y las filas con slug de la tabla maestra del §2 del plan.

**Y el cruce encontró primero un defecto del plan, que es la mitad del enredo.** Con la tabla tal como
estaba, **tres directorios no tenían fila**:

| Directorio sin fila | Qué es | Cuenta como |
|---|---|---|
| `2026-08-03-barcode-qr-scanning` | escaneo de códigos, capability `barcode-scanning` | **MVP** (excepción del criterio) |
| `2026-09-26-c40-fix-all-shops-scope-unreachable` | **`C40_FIX`**, change del PF **fuera de la numeración C** | **PF** — y **le faltaba la fila** |
| `2026-09-27-fix-boot-drain-retries-both-drains` | **seguimiento de C43**, sin ficha propia | **PF** — y no la va a tener |

**`C40_FIX` aparecía una sola vez en el plan, en prosa, y ninguna en la tabla maestra.** Eso obligaba a
que cualquier recuento hecho contra la tabla se quedara corto en uno y se corrigiera después «sumándole
`C40_FIX`» — que es literalmente lo que la nota de recuento de `epicas.md` tuvo que escribir para que sus
cifras cuadrasen. **Este change le añade su fila**, así que el plan pasa de 44 a **45 filas con slug** y
el recuento deja de necesitar una corrección de memoria.

Con la fila añadida, el cruce vuelto a correr deja **exactamente dos** directorios sin fila —la excepción
del MVP y el seguimiento de C43— y **una** fila sin directorio, que es **C39b**, este change. La
aritmética queda cerrada:

```text
46 directorios posteriores al 2026-08-03
−1 barcode-qr-scanning (MVP por contenido)
= 45 directorios del Proyecto Final
      44  filas de la tabla maestra ya archivadas  (45 filas − C39b)
    +  1  fix-boot-drain-retries-both-drains, seguimiento de C43 sin ficha propia
= 45
Las «44 archivadas» de epicas.md son, exactamente, esas 44 filas.
Al archivar C39b: 46 directorios del PF · 45 fichas.
```

**Y así la distancia entre las dos unidades tiene un solo nombre**: `fix-boot-drain-retries-both-drains`.
Un directorio de archivo sin ficha, porque es el seguimiento de C43 y no un change de la descomposición.
Antes de añadir la fila de `C40_FIX` la distancia tenía dos nombres y uno de ellos era un error del plan,
que es por lo que ningún recuento cuadraba a la primera.

### 2.4 · El barrido: dónde estaban las cifras desfasadas y qué se ha tocado

Barrido el repositorio entero buscando recuentos, excluyendo el **registro histórico intocable**
—`Documentos/prompts.md`, `Documentos/Sesiones Master AIEng/**` y `Documentos/Propuestas/**`—:

| Fichero | Qué decía | Qué se ha hecho |
|---|---|---|
| plan, ficha de C39b (§3) | «74 archivados · 32 del MVP · 41 del PF» | **párrafo conservado como registro** y anotado debajo con la medición de hoy y el criterio |
| plan, fila de C39b (§2) | la misma cifra, y 🔴 | fila reescrita: archivada, con el criterio y el resultado |
| plan, tabla maestra (§2) | **`C40_FIX` sin fila** | **fila añadida** |
| plan, recuento del §2 | «Archivados 40 · Pendientes 3» | **entrada nueva encima**, con las dos unidades y sus cifras |
| plan, bitácora (§0) | — | **entrada nueva** de C39b, la primera del documento |
| `epicas.md`, fila `TOTAL PF` | «48 fichas · 42 vivas — 40 archivadas, 3 pendientes» | **52 fichas · 45 vivas — 45 archivadas, 0 pendientes**, con la aritmética escrita |
| `epicas.md`, fila `EP17` | «C04, C24, C38, C39» y 🔴 parcial | C38 tachada como retirada, C39 partido en tres, épica **completa** |
| `epicas.md`, notas de recuento | «40», «43», «44 archivadas» en notas fechadas distintas | **no se reescriben** — son registro; se añade la entrada que fija el criterio |
| `modelo-de-datos.md` | **`ai.pos_shop` ausente**, aunque C43 la creó | **fila añadida** a la tabla del esquema `ai` |
| `openspec/project.md` | no lleva recuentos | nada que tocar |

**El único cambio de fondo en un documento ajeno a este change es la fila de `ai.pos_shop`**, y no es un
recuento: C43 creó la tabla y la puesta al día de documentación no la llevó a
`Documentos/modelo-de-datos.md`. Se encontró al comprobar que el `## 3` del README cuadrase con ese
documento, que es literalmente lo que la regla de esa sección pide.

### 2.5 · Lo que **no** es un change archivado y no debe sumarse como tal

| Ficha | Estado | Fecha |
|---|---|---|
| **C38** `add-generation-and-agent-evals` | **retirada entera** | 2026-09-27 |
| **C19, C29, C33, C35, C37** | **anulados** — la rama del agente de inventario | 2026-08-31 |
| **C27** complementarios | **cortado**, con medición y no por juicio de plazo | 2026-09-12 |

Siete fichas que no tienen directorio en el archivo y **no lo tendrán**. `C25bis` es el caso simétrico y
también conviene decirlo: está **implementado y archivado** —`2026-09-12-clean-plain-fusion`—, así que sí
cuenta.

---

## 3. El resumen de fases, y los seis changes que no salieron de ninguna ola

### 3.1 · Las fases

| Épica | Qué entrega | Changes |
|---|---|---|
| **EP11** Plataforma del servicio de IA | esqueleto, contratos congelados, cliente .NET, esquema `ai` con pgvector, despliegue de la demo | C01, C02, C03, C05, C17 |
| **EP12** Corpus y enriquecimiento | catálogo real y sintético, mundo sintético, enriquecimiento con LLM, texto fuente y *embeddings*, corpus de conocimiento | C06a, C06b, C08, C09, C10, C11, C23, `FIX1` |
| **EP13** Familias y desambiguación | entidad de familia, agrupador determinista, pantalla de revisión, métricas de revisión humana | C07, C18a, C18b, C28 |
| **EP14** Búsqueda semántica híbrida | *feeds* de índice, indexador, recuperación vectorial, endpoint .NET, panel, sinónimos, fusión RRF, prefiltro por tienda, recalibración, drenaje programado, actividad de tienda | C12, C13, C14, C15, C16, C20, C21, C22, C25, `C25bis`, C41, C43 |
| **EP15** Venta asistida, sustitutos y agentes | sustitutos, estructura y prosa del argumentario, enrutador de intención, registro de herramientas, bucle agéntico, endpoints .NET, ficha de venta, panel de consulta libre, panel del agente | C26, C30a, C30b, C31, C32a, C32b, C34, C36, C40, `C40_FIX`, C42 |
| **EP16** Inventario asistido | — | **anulada** el 2026-08-31 (C19, C29, C33, C35, C37) |
| **EP17** Evaluación y observabilidad | telemetría de búsqueda, arnés de evaluación con golden set y líneas base | C04, C24 · **C38 retirado**, **C39** partido en C39a, C39a-bis y **C39b** |

### 3.2 · Los seis changes nacidos de una comprobación manual, y no de ninguna ola

Eran cuatro cuando se escribió la ficha de C39b. **Hoy son seis**, y es un argumento del propio proyecto
sobre el valor del recorrido manual frente a las suites verdes: **ninguno de los seis lo vio ningún
test**.

| # | Change | Qué destapó, que las tres suites verdes no veían |
|---|---|---|
| 1 | **C40** `add-frontend-free-query-panel` | el panel de búsqueda asistida llevaba **todo el proyecto** sirviendo por su ruta degradada, con los filtros **descartándose en silencio** |
| 2 | **`C40_FIX`** `c40-fix-all-shops-scope-unreachable` | el ámbito «todas las tiendas» era **inalcanzable** — y lo que fallaba era una **spec viva que mentía**, no la implementación |
| 3 | **C41** `add-pos-projection-scheduled-drain` | la copia del surtido que usa el buscador llevaba **veinte días** desfasada sin que ninguna pantalla lo dijera |
| 4 | **C42** `add-frontend-agent-panel` | el agente estaba entregado y medido y **nadie lo llamaba**; y el **pivote es inalcanzable si la pieza se nombra por su nombre** |
| 5 | **C43** `add-shop-activity-projection` | la quinta condición de `verify.sh` contaba puntos de venta sin surtido **sin preguntar si la tienda está activa**, y marcaba en rojo un despliegue sano |
| 6 | **seguimiento de C43** `fix-boot-drain-retries-both-drains` | el reintento del drenaje de arranque **cubría a uno de los dos drenajes**, así que la tabla nueva se quedaba vacía tres cuartos de hora |

### 3.3 · El episodio que mejor argumenta todo lo anterior: una condición de verificación ganándose el sueldo

**C43 arregló un falso positivo y, al hacerlo, introdujo un fallo verdadero. El despliegue lo encontró el
mismo día, y lo encontró porque C43 se había obligado a fallar con la tabla vacía en vez de pasar en
vacío.**

1. El despliegue **`36322635852`** falló **con el entorno sano**: la quinta condición contaba
   `HT-ARTRUTX` —cerrada a propósito desde el mundo sintético de C10, la única de las doce— como una
   tienda rota.
2. C43 lo arregló contando **sólo tiendas activas**, y añadió a propósito una condición **(a)**: fallar si
   el servicio no conoce **ninguna** tienda activa, porque un recuento sobre una tabla vacía devuelve cero
   y *«pasar en vacío»* es el defecto que toda esta serie existe para cerrar —el índice vacío, la
   proyección vacía y el corpus vacío parecieron éxito antes de que se les obligara a fallar—.
3. El despliegue **`36343020047`** falló **por esa condición (a)**, y esta vez con razón: `_boot_drain`
   reintentaba mientras `drain_pass(...)` devolviera `None`, y ése es el resultado del drenaje **de
   disponibilidad**. Uno de los dos bastó para terminar el bucle de los dos. `ai.pos_shop` se quedó vacía
   hasta el tic de 600 s.
4. El seguimiento hizo que el reintento fuera **por drenaje y no por pasada**, y el despliegue
   **`36344846739`** cerró en verde.

**Es la misma familia de defectos, un nivel más arriba:** *parte del trabajo salió bien* leído como *el
trabajo salió bien*. Y la condición que lo cazó no estaba ahí por casualidad: la escribió el change
anterior **precisamente para que una tabla vacía no hiciera pasar una comprobación**, cuatro horas antes
de que la tabla se quedara vacía por otra causa.

---

## 4. La taxonomía de métodos de búsqueda

**Once métodos, una fila cada uno, y la procedencia en la fila.** Las cifras de recuperación salen de
**una sola procedencia** —la tabla final de C25, golden set `1:198c4af44506`,
[`c25-baselines-2026-09-11.md`](../../../ai-service/evals/results/c25-baselines-2026-09-11.md)—, porque la
regla de `retrieval-evaluation` es que dos corridas con procedencia distinta se reportan como no
comparables en vez de compararse. Una tabla que mezclase dos conjuntos dorados no significaría nada.

### 4.1 · La tabla

| Método | Dónde vive | Cifra medida | Procedencia |
|---|---|---|---|
| **Léxico por nombre** — el buscador que la joyería tenía (subcadena sobre el nombre + SKU exacto) | .NET, previo al proyecto | nDCG@5 **0,092** · Recall@5 0,079 · abstención 1,000 | C25 `v0-nombre` |
| **Léxico en español** — FTS de PostgreSQL sobre el mismo texto que indexa .NET | `retrieval/search.py`, rama léxica | nDCG@5 **0,507** · Recall@5 0,558 | C25 `v0-fts` |
| **CAG** — el catálogo entero en el contexto, sin recuperación | `evals/`, configuración de línea base | Recall@5 **0,133** sobre las 12 consultas sin anclaje · **$0,002673**/consulta · 17.583 tokens para 1.168 productos · `NINGUNO` en **10 de 12** · techo en **6.643** productos | C24 §6 + C25 `v0-cag` — **fechada y no reproducible bit a bit** |
| **Vectorial** — pgvector HNSW, coseno, umbral de distancia y sobre-recuperación | `retrieval/search.py` (C14) | nDCG@5 **0,612** · Recall@5 0,637 | C25 `v1-vectorial` |
| **Fusión RRF plana** — las tres listas fusionadas de una vez | C21, **retirada por `C25bis`** | nDCG@5 **0,673** | C25 `v2-hibrido` — **fila histórica y NO re-ejecutable** |
| **Fusión RRF en dos etapas por rama** — las dos listas léxicas entre sí, y su resultado con la vectorial | C25, **la que se sirve** | nDCG@5 **0,740** · Recall@5 0,758 · P@3 0,713 · MRR 0,834 · abstención 0,150 · **+0,083** sobre `v2` en el subconjunto que decide | C25 `v2b-fusion` |
| **Señales de negocio** — disponibilidad en el último bloque de la clave lexicográfica | C25, **no adoptada como configuración por defecto** | nDCG@5 **0,729** puro · **0,732** operativo · **+0,030**, por debajo del margen de 0,05 que la regla exigía | C25 `v3-senales` |
| **M1 · consulta libre** — pregunta sin pieza delante, con enrutador de intención | C30b + C31 + C40 | marcadores en el argumentario: **0 de 90** con `assist/v5` (con `v3` eran 2 de 90 y 1 de 90) · el enrutador **no silencia ninguna** de las 48 consultas contestables · falso positivo **0,00 %** sobre 119 casos de enrutado con `gpt-4o` | C40 §1 y C31 |
| **M2 · argumentario anclado a pieza** | C30a + C30b + C34 | **118 de 120** generaciones no escriben un solo dígito · latencia extremo a extremo p95 **7,1 s**, máx 7,9 s | C30b + C34 |
| **M3 · pregunta sobre la pieza, contra el corpus** | C23 + C30a | corpus de **32 documentos ≈ 161 fragmentos** · umbral de distancia **0,51**, fijado sobre un hueco limpio de **8 milésimas** entre las 32 preguntas que el corpus responde y las 5 de fuera | C23 |
| **Agéntico** — bucle de *function calling* sobre seis herramientas de sólo lectura | C32a + C32b + C42 | **17 de 20** escenarios de calibración cumplen su expectativa · ruido entre pasadas **2 de 20** · coste **$0,022958**/petición · **0 de 102** respuestas parciales en la pasada de C42 | §5 de este informe |

**Nada en esta tabla queda sin medición**, así que no hay ninguna fila declarada *no medido*. Sí hay
**dos filas con una advertencia que no se puede quitar**:

- **CAG llama a un modelo de lenguaje.** Ni a temperatura 0 devuelve lo mismo dos veces. Es una fila
  fechada con su modelo (`openai/gpt-4o-mini`, 2026-09-11), no una configuración que se re-ejecute.
- **`v2-hibrido` es histórica y no re-ejecutable.** `C25bis` retiró del código la composición de una sola
  etapa bajo la que se midió. Se puede **citar** —tabla, detalle por consulta y configuración retirada,
  los tres versionados—, no repetir. Las otras cinco filas sí se reprodujeron, con las 315 líneas por
  consulta idénticas.

### 4.2 · Las cifras de C24, aparte y como históricas

Bajo el golden set **anterior**, `1:1474bfc3aa3a`
([`c24-baselines-2026-09-07.md`](../../../ai-service/evals/results/c24-baselines-2026-09-07.md)):

| configuración | nDCG@5 |
|---|---:|
| `v0-nombre` | 0,082 |
| `v0-fts` | 0,454 |
| `v1-vectorial` | 0,548 |
| `v2-hibrido` | 0,603 |

**No se resta ninguna de estas cifras a ninguna de la tabla de 4.1.** Se publican porque son la lectura
con la que se tomaron las decisiones de C24 y porque el README las cita; el conjunto dorado se profundizó
después y C25 re-corrió **todas** las filas bajo el nuevo, que es lo que su propia spec exige.

**Y de aquí sale un hallazgo sobre una sección congelada del README**, que va al anexo A: el `### 1.2`
dice que el acierto *«sube de 0,603 a 0,740»*, y eso **mezcla los dos conjuntos dorados**. El salto
comparable es **0,673 → 0,740**.

### 4.3 · El reranking descartado, con su protocolo y su número

El diseño lo descarta y lo declara como limitación. Lo que C24 dejó es que el **«no» sea una división y
no un argumento**:

| Configuración | consultas con un grado 2 en el top-20 pero fuera del top-5 |
|---|---:|
| `v0-fts` | 4 de 48 (8,3 %) |
| `v1-vectorial` | 1 de 48 (2,1 %) |
| **`v2-hibrido`** (configuración viva) | **1 de 48 (2,1 %)** |

Un reranker sobre la configuración viva podría arreglar **como máximo una consulta de cuarenta y ocho**. A
~250 ms de *cross-encoder* sobre un presupuesto de 2.500 ms, eso es el 10-15 % del presupuesto para un
techo del 2 % de las consultas. **El protocolo queda ejecutable** —añadir un reranker es un
`configs/v2-rerank.yaml` más una corrida—, y el número que lo haría decidible, medido.

### 4.4 · La progresión de prompts, con su impacto medido

`enrichment/v1 → v2`, de `FIX1`: amplía `piece_type` de **ocho a doce** términos. Medido sobre
`ai.product_document` (1.168 filas) después de sincronizar:

| Comprobación | Antes | Después |
|---|---:|---:|
| `piece_type = 'diadema'` | 0 | **11** |
| `piece_type = 'gemelos'` | 0 | **4** |
| `piece_type = 'llavero'` | 0 | **3** |
| `piece_type = 'cinturon'` | 0 | **1** |
| `piece_type IS NULL` | 11 | **1** |
| impostores dentro de `broche` | 6 | **0** |
| perfiles en `enrichment/v2` | 0 | **22** |

**Y la nota honesta, que es la mitad del valor de esta sección:** el criterio léxico que la ficha proponía
—*«buscar "diadema" pasa de cero a resultados»*— **ya se cumplía antes del change**, porque la rama léxica
de C21 alcanzaba los 11 documentos por el nombre. Firmarlo verde no habría demostrado nada, así que **no
se usa como prueba**. `v1.md` se conserva intacto porque 1.178 perfiles declaran venir de él y esa
declaración tiene que seguir siendo verificable.

### 4.5 · Las métricas de revisión humana

De C28, sobre **204 perfiles, todos cronometrados**:

| Métrica | Valor |
|---|---|
| Tasa de corrección, ponderada por el catálogo | **20,9 %** |
| Tiempo medio por ítem | **32,1 s** |
| …de ellos, **campos sensibles** (`piece_type`, `materials`, `stone_type`, `size_label`) | 85 / 816 = **10,4 %** |
| …de ellos, **etiquetas comerciales** (`color_tags`, `style_tags`, `occasion_tags`) | 259 / 612 = **42,3 %** |

**Se publican partidas porque no miden lo mismo.** El 10,4 % son campos que deciden la respuesta y
llegaban vacíos o mal; el **42,3 % es subjetivo por declaración expresa del revisor** —etiquetas donde
«elegante» y «clásico» son ambas defendibles— y **no es comparable** con el otro. Citar sólo el 20,9 %
ponderado escondería esa diferencia; citar sólo el 42,3 % haría parecer que el extractor se equivoca en
cuatro de cada diez campos, que no es lo que pasó.

---

## 5. Las tres tareas que sobreviven a C38

C38 (`add-generation-and-agent-evals`) se **retiró entero** el 2026-09-27, por valor marginal y sobre
mediciones tomadas en su propia sesión de exploración. Sobreviven tres tareas, y caen aquí.

### 5.1 · Tarea 1 — la definición de éxito de tarea, escrita antes de mirar cifras

> **Un escenario de calibración del agente tiene éxito cuando su expectativa de herramientas se cumple:
> invocó en algún momento *todas* las que el escenario exige, *al menos una* de las que admite como
> alternativa, y *ninguna* de las que prohíbe — y el escenario no declara de antemano una discrepancia
> propia.**

Tres precisiones que la hacen usable:

- **`forbids` pesa tanto como `expects`, y no es simetría por simetría.** En el pivote el fallo caro es el
  **de más**: apartar al cliente de una pieza que la tienda sí puede vender. Un criterio que sólo mirase
  lo que debe ocurrir mediría el infra-pivote y sería ciego al sobre-pivote, que es el que cuesta dinero.
- **`expects_any` existe porque faltaba.** Dos escenarios de guardarraíl decían en su prosa «se admite
  cualquiera de las dos» y lo codificaban con una conjunción, así que contaban como fallo haciendo lo que
  su texto permitía.
- **Una discrepancia declarada se cuenta aparte**, ni como éxito ni como fallo nuevo. Declararla no cambia
  la expectativa —eso es lo que la contaminaría—, sólo dónde se suma.

**Lo que queda deliberadamente FUERA del veredicto**, y por qué: el motivo de parada, el número de
iteraciones y de llamadas a herramienta, el número de grupos y si se generó argumentario. Los cuatro
existen en cada fila, pero **ningún escenario tiene una expectativa escrita sobre ellos**, así que
admitirlos ahora sería definir el criterio a partir de los datos. Se publican **al lado** del veredicto,
como contexto.

### 5.2 · Tarea 2 — la tabla, emitida con `--rescore` y sin gastar cuota

```bash
cd ai-service
uv run python -m jbg_ai.evals.agent_sweep --rescore \
    evals/results/c32b-agent-sweep-17fbdd15a18c.json
```

**No llama al proveedor ni a la base de datos.** Recalcula todos los agregados con el código de hoy sobre
un artefacto ya escrito, y deja el resultado a su lado.

| Procedencia | Valor |
|---|---|
| Artefacto | `c32b-agent-sweep-17fbdd15a18c.json` — la pasada de **C42** |
| `sha256` (con fines de línea normalizados) | `613020762afd815ab2b4f95dde2d335842269d22a5d912cb437d5b3c33a71277` |
| `run_id` | `17fbdd15a18c` · tomada el 2026-09-26T19:02:45Z |
| Brazo | `openai/gpt-4o` · 102 peticiones (20 de calibración, 82 de carga) |
| Prompts | `agent/v1` · `assist/v6` · `router/v3` |
| Recalculado con | `a5ac757` |

**Veredicto: 17 cumplen · 2 no cumplen (`C14`, `C17`) · 1 discrepancia declarada (`C19`) · 0 no
comparables.**

| # | mide | expectativa | herramientas invocadas | parada | it. | veredicto |
|---|---|---|---|---|---:|---|
| **C01** | granularidad | exige `buscar_catalogo` · prohíbe `pedir_aclaracion`, `buscar_sustitutos` | `buscar_catalogo`, `consultar_disponibilidad` | `sin_mas_herramientas` | 3 | **✅ cumple** |
| **C02** | granularidad | exige `pedir_aclaracion` · prohíbe `buscar_catalogo`, `buscar_sustitutos`, `consultar_disponibilidad` | `pedir_aclaracion` | `aclaracion` | 1 | **✅ cumple** |
| **C03** | granularidad | exige `consultar_conocimiento` · prohíbe `buscar_catalogo` | `consultar_conocimiento` | `sin_mas_herramientas` | 2 | **✅ cumple** |
| **C04** | granularidad | exige `buscar_catalogo`, `consultar_conocimiento` · prohíbe `pedir_aclaracion` | `buscar_catalogo`, `consultar_conocimiento` ×5, `consultar_disponibilidad` | `sin_mas_herramientas` | 4 | **✅ cumple** |
| **C05** | granularidad | exige `listar_familia` | `listar_familia` | `sin_mas_herramientas` | 2 | **✅ cumple** |
| **C06** | granularidad | exige `buscar_catalogo` | `buscar_catalogo`, `consultar_disponibilidad` | `sin_mas_herramientas` | 3 | **✅ cumple** |
| **C07** | pivote | exige `consultar_disponibilidad`, `buscar_sustitutos` | `consultar_disponibilidad`, `buscar_sustitutos`, `consultar_disponibilidad` ×2 | `sin_mas_herramientas` | 4 | **✅ cumple** |
| **C08** | pivote | exige `consultar_disponibilidad` · prohíbe `buscar_sustitutos` | `consultar_disponibilidad` | `sin_mas_herramientas` | 2 | **✅ cumple** |
| **C09** | pivote | exige `consultar_disponibilidad` · prohíbe `buscar_sustitutos` | `consultar_disponibilidad` | `sin_mas_herramientas` | 2 | **✅ cumple** |
| **C10** | pivote | exige `consultar_disponibilidad` · prohíbe `buscar_sustitutos` | `consultar_disponibilidad` | `sin_mas_herramientas` | 2 | **✅ cumple** |
| **C11** | pivote | exige `consultar_disponibilidad`, `buscar_sustitutos` | `consultar_disponibilidad`, `buscar_sustitutos` | `sin_mas_herramientas` | 3 | **✅ cumple** |
| **C12** | pivote | exige `consultar_disponibilidad`, `buscar_sustitutos`, `consultar_conocimiento` | `consultar_disponibilidad`, `consultar_conocimiento`, `buscar_sustitutos` | `sin_mas_herramientas` | 3 | **✅ cumple** |
| **C13** | elíptico | exige `buscar_catalogo` · prohíbe `pedir_aclaracion` | `buscar_catalogo`, `consultar_disponibilidad` | `sin_mas_herramientas` | 3 | **✅ cumple** |
| **C14** | elíptico | exige `buscar_catalogo` · prohíbe `pedir_aclaracion` | *(ninguna)* | `sin_mas_herramientas` | 1 | ❌ **no cumple** |
| **C15** | guardarraíl | prohíbe **las seis** | *(ninguna)* | `rechazado` | 0 | **✅ cumple** |
| **C16** | guardarraíl | alguna de `buscar_catalogo`, `pedir_aclaracion` | `buscar_catalogo`, `consultar_disponibilidad` | `sin_mas_herramientas` | 3 | **✅ cumple** |
| **C17** | guardarraíl | alguna de `buscar_catalogo`, `pedir_aclaracion` | *(ninguna)* | `sin_mas_herramientas` | 1 | ❌ **no cumple** |
| **C18** | abstención | prohíbe `buscar_sustitutos` | *(ninguna)* | `rechazado` | 0 | **✅ cumple** |
| **C19** | abstención | exige `buscar_catalogo` · prohíbe `buscar_sustitutos` | *(ninguna)* | `rechazado` | 0 | ⚠️ **discrepancia declarada** |
| **C20** | granularidad | exige `consultar_conocimiento` · prohíbe `buscar_catalogo`, `consultar_disponibilidad` | `consultar_conocimiento` ×2 | `sin_mas_herramientas` | 3 | **✅ cumple** |

**Los tres que no cumplen, dichos por su nombre.** `C14` es elíptico —tres elipsis encadenadas— y el
bucle no llamó a `buscar_catalogo`: paró en la primera vuelta sin usar el contexto acumulado. `C17` es de
guardarraíl y admitía cualquiera de dos herramientas; no invocó ninguna. `C19` es de abstención y **su
discrepancia ya venía declarada en el propio conjunto**, de antes de esta pasada.

**El contexto, que se publica al lado y no dentro:**

| | calibración (20) | carga (82) |
|---|---|---|
| Motivos de parada | `sin_mas_herramientas` 16 · `rechazado` 3 · `aclaracion` 1 | `sin_mas_herramientas` 72 · `aclaracion` 9 · `rechazado` 1 |
| Respuestas parciales | **0** | **0** |
| Argumentario generado / retirado | 11 / **0** | 72 / **1** (1,2 %) |
| Coste por petición | **$0,022958** — enrutador 0,008423 · bucle 0,014205 · argumentario 0,000330 | $0,028259 |
| Pivote en `sin_existencias` | **3 de 3** (`C07`, `C11`, `C12`) · sobre-pivotes **0** | — |

### 5.3 · El ruido entre pasadas, declarado junto a la cifra

Las **mismas 20 transcripciones**, dos pasadas distintas, **un solo criterio** —el fichero de escenarios
tal como está hoy—:

| # | C32b `293fe5c6e470` (21 sep, `assist/v4`) | C42 `17fbdd15a18c` (26 sep, `assist/v6`) | ¿coincide? |
|---|---|---|---|
| C01–C04, C06–C13, C15, C16, C18, C20 | cumple | cumple | sí |
| **C05** | **no comparable** | cumple | **no** |
| **C14** | cumple | **no cumple** | **no** |
| **C17** | cumple | **no cumple** | **no** |
| C19 | discrepancia declarada | discrepancia declarada | sí |

**El veredicto coincide en 17 de 20.** De los tres que discrepan, **`C05` no es un vuelco**: su
transcripción **se corrigió** después de la primera pasada y está documentado en la cabecera del propio
fichero, así que el arnés lo marca *no comparable* en vez de puntuarlo. **Los vuelcos reales son `C14` y
`C17`: 2 de 20, un 10 %.**

**Y de ahí sale la forma de publicación, que es una decisión y no un estilo.** Con un 10 % de ruido, una
*«tasa de éxito del 85 %»* sería una precisión fingida: el intervalo de la cifra cubre al menos dos
escenarios. Lo publicable es **«17 de 20, y éstos son los tres que fallan y por qué»** — que además es
más informativo, y es lo que ya hizo el informe de C32b.

**Cómo se reproduce, y por qué no queda un artefacto nuevo de esta comparación.** Basta con
`--rescore` sobre los **dos** artefactos de pasada, que están committed, y leer su bloque
`expectations.current`:

```bash
cd ai-service
uv run python -m jbg_ai.evals.agent_sweep --rescore evals/results/c32b-agent-sweep-293fe5c6e470.json
uv run python -m jbg_ai.evals.agent_sweep --rescore evals/results/c32b-agent-sweep-17fbdd15a18c.json
```

La primera orden **sobrescribe** `c32b-agent-sweep-293fe5c6e470.rescore.json`, que ya estaba en el
repositorio desde C32b. **Ese fichero se ha devuelto a su estado original a propósito**: es evidencia
derivada de otro change, y cambiar su `taken_at` por el de hoy sólo enturbiaría su procedencia. Su
recálculo con el código de hoy da los mismos veredictos —**18 · 0 · 1 declarado · 1 no comparable** para
el brazo `gpt-4o` bajo el fichero de escenarios actual— y añade dos campos a `null`
(`pitch_placeholders`, `projection_freshness`), que son instrumentos que **no existían** cuando esa pasada
se corrió. Sólo se comete el artefacto nuevo, el de la pasada de C42.

**Una limitación de esta comparación, dicha aquí y no en una nota al pie.** Las filas de la pasada de
C32b **no llevan `turns_sha256`**, porque ese campo se añadió después; su comparabilidad se decide con la
comprobación **más débil** que el propio `--rescore` declara —el `fixture`—. Es suficiente para detectar
que `C05` cambió, y **no** garantiza que las otras 19 transcripciones fueran idénticas palabra por
palabra. El 2 de 20 es por tanto un **suelo** del ruido, no una medición fina de él.

### 5.4 · Tarea 3 — el validador .NET no implementado, declarado con su vía de cierre

**Qué no está hecho.** La mitad .NET del validador determinista de C38: una comprobación, en la pasarela,
de que ningún número del argumentario generado aparezca pegado a una marca de moneda o de existencias.

**Su cifra esperada es cero, y eso es lo que la convierte en una limitación y no en una deuda.** Es **un
espejo**: la regla que aplicaría es **la misma** que la puerta numérica de Python ya aplica **al mismo
texto**, así que todo lo que .NET rechazaría Python lo rechazó antes. Tres datos lo sostienen:

- De los tres caminos de generación, **sólo la ficha de venta comprueba algo en .NET**.
  `FreeQuerySearchService` y `AgentAssistService` hacen `Pitch = ai.Pitch`, y `grep "{{\|Resolve"` sobre
  los dos devuelve **cero líneas**.
- `placeholder_in_free_query` es **causa dura** desde C40: un marcador en modo libre retira el
  argumentario entero, en Python, antes de que .NET lo vea.
- C42 midió **0 marcadores de 102** peticiones, y C40 antes de él **2 de 90** y **1 de 90** con el prompt
  anterior, **0 y 0** con el vigente.

**Sigue siendo un seguro defendible** —una regla que hoy no dispara puede disparar el día que alguien
cambie el prompt o añada un cuarto camino—, pero es **un seguro y no un arreglo**, y escribirlo después de
haberlo medido a cero es la forma honesta de declararlo.

**Vía de cierre**, identificada y no ejecutada: la comprobación vive en la pasarela, junto a
`PitchPlaceholderResolver`, que es el único punto por el que pasan los tres caminos; rechaza con el mismo
vocabulario cerrado de causas que Python; y su criterio de aceptación **no puede ser «atrapa algo»**, sino
un test que le dé un texto con una cifra pegada a un símbolo de moneda y compruebe que lo retira. Queda
anotada en [`DEFERRED_TASKS.md`](../../../openspec/DEFERRED_TASKS.md).

---

## 6. Las limitaciones que se declaran, y no se arreglan

### 6.1 · El panel avisa en `CRITICAL` de un modelo que este entorno no puede tener

`GET /api/image-recognition/model/health` devuelve, sobre el entorno desplegado:

```json
{ "currentVersion": null, "lastTrainedAt": null, "alertLevel": "CRITICAL",
  "alertMessage": "No AI model exists. Please train an initial model.",
  "catalogMetrics": { "totalProducts": 1200, "productsWithPhotos": 0,
                      "productsWithoutPhotos": 1200 },
  "photoMetrics": { "totalPhotos": 0 }, "precisionMetrics": null }
```

**No se arregla entrenando nada, porque la causa es estructural:** el catálogo sintético de C10 no tiene
**ni una fotografía** —1.200 productos, 0 con foto—, así que el reconocimiento de imagen no tiene material
del que aprender y **nunca** podrá tener modelo en este entorno. Lo corrobora la búsqueda asistida por
otro camino: todos sus resultados llegan con `"primaryPhotoUrl": null`.

**Y el agravante:** el reconocimiento de imagen es funcionalidad **del MVP y no del Proyecto Final**, así
que la alerta más visible del panel **no es ni de lo que se evalúa**.

| | |
|---|---|
| **Vía elegida para C39b** | **la 1 — declararlo en el guion de la demo**, para que quien evalúe sepa de antemano que esa tarjeta no aplica. Es documentación y no toca código |
| Vía 2, el arreglo correcto | distinguir «no alimentado» de «sin entrenar» en `ModelHealthService`: con `productsWithPhotos == 0` el nivel debe ser informativo y el mensaje decir que la funcionalidad no tiene material. **No es de este change** |
| Vía 3 | ocultar la tarjeta. Más barata y peor: esconde el estado en vez de nombrarlo |

`CRITICAL` está mal elegido, y ésa es la parte que **sí** es un defecto: ese nivel describe algo que se ha
roto, y aquí hay una funcionalidad **no alimentada**.

### 6.2 · El pivote del agente es inalcanzable si la pieza se nombra por su nombre

**Medido sobre el entorno desplegado, contra el proveedor real, por HTTP.** Una pieza agotada de verdad
—`SKU759`, *Anillo Luna Creciente S*, `qty_bucket = '0'` en `ai.pos_projection` para `CIU-CENTRE`—
preguntada de las dos maneras:

| Cómo la nombra el operario | Herramientas que el bucle eligió | ¿Pivota? |
|---|---|---|
| **Por su referencia**, `SKU759` | `consultar_disponibilidad` → **`buscar_sustitutos`** | ✅ **Sí.** 4 iteraciones · 6 grupos, todos `sustitutos` |
| **Por su nombre**, «Anillo Luna Creciente S» | `consultar_disponibilidad` ❗`referencia_desconocida` → `buscar_catalogo` → `consultar_disponibilidad` | ❌ **No.** 3 iteraciones · 2 herramientas · 8 grupos, todos `catalogo` |

**El mecanismo es estructural y no una torpeza del modelo: `buscar_catalogo` no devuelve el nombre de la
pieza.** Su observación lleva `posicion`, `sku`, `materiales`, `variante` y `motivos`. El modelo pasa el
nombre a `consultar_disponibilidad`, que quiere un SKU y responde `referencia_desconocida`; recupera con
`buscar_catalogo`, que devuelve ocho candidatos identificados **sólo por SKU, material y variante**; y
**no tiene con qué saber cuál de los ocho es la pieza que el cliente nombró**, así que consulta la
disponibilidad de otra —que sí tiene stock— y, correctamente, no pivota. **El bucle hace lo correcto en
cada paso.**

**Por qué el arnés no lo vio:** `scenario_turns` resuelve el marcador `{pieza}` a un **SKU** y lo escribe
en el turno, así que en las 204 peticiones de C32b y en las 102 de C42 el modelo **siempre recibió la
referencia servida**. Un operario teclea un nombre.

**Vía de cierre, costada:** que la observación de `buscar_catalogo` lleve el nombre del producto — un
campo, en la observación que ve el modelo y no en el payload de generación. El argumento de C30b contra
ensanchar el payload **no se le aplica tal cual**, porque esa regla es sobre **numerales** y un nombre no
lleva cifras; pero sigue siendo **una de las seis herramientas congeladas**, así que lo decide quien las
posea. **Mientras no se haga, el pivote se demuestra nombrando la referencia**, y el guion del vídeo lo
hace así.

### 6.3 · La deriva de rama sigue abierta — y hoy, medida, no hay deriva

**Nada compara lo desplegado con la rama que debería servirse**, aunque los dos datos existen. Comprobado
a mano el 2026-09-27:

| Dato | Valor |
|---|---|
| `IMAGE_TAG` en SSM (`/jbg-demo/IMAGE_TAG`) | `sha-7d3a15ae8bb2807a7fd97e0fcc096f90f9efd971` |
| `git rev-parse origin/demo` | `7d3a15ae8bb2807a7fd97e0fcc096f90f9efd971` |
| Veredicto | **coinciden — no hay deriva hoy** |

**Y eso es exactamente lo que hace la limitación incómoda:** la comprobación que faltaba cabe en una
línea, y nadie la ha escrito. Su sitio natural es `verify.sh`, junto a las siete condiciones que ya
tiene. No entra aquí porque **este change no toca el paquete de despliegue**, y porque una condición nueva
en `verify.sh` se prueba disparando un despliegue.

**Por qué importa:** es el defecto que C39a destapó. `origin/demo` estuvo **84 commits y cinco semanas**
por detrás de `ai-eng` —su último commit en el QA de C34— sin que nada lo dijera, y lo desplegado no
contenía C36, C40, `C40_FIX`, C41 ni C42: **cuatro de las cinco superficies más visibles del proyecto**.

### 6.4 · Las 66 filas de `ai.sync_failure` del *feed* de catálogo

Abierta, con su mitad barata ya hecha por C43: el informe de salud las publica **por *feed***, así que
dejan de ser invisibles. Leído en vivo hoy: `"failed_pages_by_feed": {"catalog": 66}`. Lo que falta es la
purga y el criterio de caducidad.

### 6.5 · Lo que queda para fase posterior

Declarado explícitamente y no por omisión: **packing list** completa (con su máquina de seis estados y su
auditoría), **liquidación con descuentos**, **upsell / downsell**, **políticas de inventario
configurables** y —desde el 2026-08-31— el **agente de inventario completo**, cuyo diseño está íntegro en
el §10 del documento hermano y sólo espera implementación.

**Próximos pasos, en orden de madurez del diseño:** agente de inventario completo; perfil comercial por
punto de venta, que es la mitad barata de lo anterior y devuelve al agente de venta una séptima
herramienta; packing list completa; liquidación y políticas de inventario; prioridad comercial por margen
—los datos ya existen en `ProductComponentAssignment`—; reranking medido; reranking aprendido con
`ProductSearchEvent` reales; fusión de señal visual y textual; evaluación en línea con A/B por punto de
venta.

### 6.6 · Las tres declaraciones que son puntos a favor si están escritas y huecos si faltan

1. **Un solo agente.** El proyecto entrega el agente **de venta** y ninguno más. El de inventario está
   diseñado —§10 del documento hermano, íntegro— y **no implementado**: su rama se anuló el 2026-08-31 con
   cinco changes (C19, C29, C33, C35, C37). Va como próximo paso, no como capacidad.
2. **El golden set no tiene acuerdo entre anotadores.** Lo etiquetó **una sola persona**, así que no hay
   kappa que publicar. Se declara como limitación del conjunto en lugar de reclamar una mitigación que no
   se aplicó. Lo que sí tiene: escala de tres grados, criterio escrito **antes** de etiquetar, *pooling*
   con profundidad registrada por consulta, y el `no juzgado@5` publicado por configuración para que una
   fila con buena parte de su top-5 sin juzgar se vea **no comparable** en vez de puntuarse en silencio.
3. **El proyecto es individual, no en pareja.** Toda la autoría, las decisiones y las mediciones son de
   una sola persona.

### 6.7 · Repaso de `DEFERRED_TASKS.md`: qué queda abierto, y qué de eso puede encontrarse un evaluador

Recorridas todas las entradas del fichero. **Dos quedan cerradas por C43** el día anterior a este change
—el falso positivo de la quinta condición y la rancidez que el despliegue registraba ya curada—, y
**una por C39a** —el corpus que no viajaba en la imagen—. De las abiertas, éstas son las que alguien que
evalúe puede tocar:

| Entrada | ¿La ve un evaluador? | Estado tras C39b |
|---|---|---|
| **El panel avisa en `CRITICAL`** de un modelo que el mundo sintético no puede alimentar | **Sí, y es lo primero que ve** al entrar como administrador | **vía 1 ejecutada** — declarada en el guion §0.1. Vías 2 y 3 abiertas |
| **El pivote inalcanzable por nombre** | **Sí**, si teclea el nombre en vez de la referencia | declarada con su arreglo costado; el guion usa la referencia |
| **La deriva de rama** | No directamente, pero es lo que haría que **todo lo demás fuera falso** | **entrada nueva**, con los dos datos y la octava condición que la cerraría |
| Las **66 filas** de `ai.sync_failure` del *feed* de catálogo | En el informe de salud, como `failed_pages_by_feed` | abierta; su mitad barata la hizo C43 |
| **El validador .NET** no implementado | No: no hay superficie | **entrada nueva** — limitación con cifra esperada cero |
| **Este repositorio no tiene CI efectiva** | Sí, si mira las pestañas de Actions | abierta y **declarada en el README §2.4**, como informativa y no como puerta |
| El resto (C16, C17, C28, C30b, C31, C32a, C32b, C36, C40, `C40_FIX`, FIX1) | No | abiertas, cada una con su vía de cierre ya escrita en su entrada |

**Ninguna entrada abierta se cierra en este change**, y eso es deliberado: C39b declara, no arregla. Lo
que sí cambia es que **las dos que un evaluador va a ver están explicadas antes de que las vea**, que es
la única mitigación que un change de documentación puede ofrecer.
---

## 7. La confirmación de extremo a extremo que este change absorbe

Se decidió explícitamente **no abrir un C43-bis**: la quinta condición de `verify.sh` sólo da su veredicto
real en un despliegue, y ése ocurre al mergear a `demo` **después** de archivar C43. Esa confirmación se
recoge aquí.

### 7.1 · El despliegue en verde

**Ejecución `36344846739`, 2026-09-27: los diecisiete pasos en verde**, incluida «Verify the deployment
from inside the host». **Es la primera ejecución correcta desde el 22 de septiembre.** `IMAGE_TAG =
sha-7d3a15ae…`, cuatro contenedores sanos.

```text
[verify] OK — 1200 documents indexed with openai/text-embedding-3-small
[verify] OK — projection drained 596s ago, 11 active point(s) of sale, all with an assortment
                                          (12 present in the projection, closed shops included)
[verify] NOTE: other feeds carry recorded failures: {'catalog': 66}
[verify] OK — knowledge corpus holds 161 fragment(s)
[verify] OK — the agent route answered, stop_reason='presupuesto_reloj'
[verify] Post-deployment verification passed.
```

### 7.2 · El dato de la tarjeta de administración, comprobado hoy y sin credencial

La línea roja de «1 tienda sin surtido sincronizado» venía de `shops_without_scope`. **Leído en vivo el
2026-09-27**, desde dentro del anfitrión por SSM contra el `/health` interno de `jbg-ai` —que no exige
credencial de usuario, porque el servicio es privado por diseño—:

```json
"projection": {
  "status": "ok", "stale": false,
  "age_seconds": 95.058925, "ceiling_seconds": 3600,
  "points_of_sale": 12, "active_points_of_sale": 11,
  "shops_without_scope": 0,
  "failed_pages": 0, "failed_pages_by_feed": { "catalog": 66 },
  "full_synced_at": "2026-09-27T18:21:48.491723+00:00",
  "synced_at":      "2026-09-27T20:17:12.390775+00:00"
}
```

Y el resto del informe, en la misma lectura:

```json
{ "status": "OK", "database": "ok", "provider": "configured", "version": "0.1.0",
  "index": { "status": "ok", "documents": 1200,
             "model": "openai/text-embedding-3-small",
             "configured_model": "openai/text-embedding-3-small" } }
```

| Afirmación | Estado |
|---|---|
| `shops_without_scope` es **0**, así que **el dato que pintaba la línea roja ya no existe** | ✅ **verificado** por lectura directa, 2026-09-27 |
| Las **doce** tiendas están en la proyección y **once** son activas — la cerrada cuenta y no se exige que tenga surtido | ✅ **verificado** |
| La proyección **no está rancia**: 95 s de edad contra un techo de 3.600 s, y el drenaje programado corriendo | ✅ **verificado** |
| 1.200 documentos indexados y el modelo configurado **coincide** con el del índice | ✅ **verificado** |
| Cuatro contenedores sanos: `api`, `ai`, `proxy`, `postgres` | ✅ **verificado** |

### 7.3 · El renderizado de la tarjeta, declarado y **no** dado por visto

**Lo que este change NO ha visto: la tarjeta pintada en el navegador.** Una sesión de Claude Code no tiene
navegador, y la vía .NET —`GET /api/ai/health`, sólo para administradores— exige la contraseña de
`demo.admin`, que **no está en el repositorio**: se generó fuera del anfitrión y sólo viajó el hash.

Por eso son **dos afirmaciones distintas y así se publican**:

- **El dato es cero** — verificado en 7.2, por lectura directa del informe que alimenta la tarjeta.
- **La tarjeta no pinta la línea roja** — **declarado**, pendiente de observación del responsable con su
  fecha. **No consta como comprobado.**

«El número que pinta la línea es cero» y «la línea no está en la pantalla» no son la misma afirmación, y
mezclarlas es exactamente la clase de suposición que este proyecto ha pagado seis veces.

---

## 8. El *tag* y la rama de entrega — **propuesta**, no ejecución

| | Propuesta |
|---|---|
| *Tag* | **`v1.0-final-SVL`** |
| Rama de entrega | **`finalproject-SVL`** |
| Commit | el merge de `c39b-finalize-pf-readme-and-evidence` en `ai-eng` |

**Ni el *tag* ni la rama se crean ni se empujan en este change.** `git tag --list "v1.0-final*"` está
vacío, y así queda hasta que lo confirme quien responde de la entrega.

**Las iniciales discrepan de la ficha §0.1 del README**, que nombra a otra persona. `SVL` son las del
autor del historial de git. La discrepancia **se reporta y no se resuelve aquí**, porque resolverla es
editar una sección congelada: va al anexo A.3.

---

## 9. El cierre, recontado **después** de archivar

El recuento se cierra al archivar y no antes, porque archivar es lo que mueve la cifra. Medido tras
`openspec archive`:

```text
directorios en openspec/changes/archive/    79      (78 + este change)
  < 2026-08-03                              32
  >= 2026-08-03                             47
slugs distintos                             76
changes activos en openspec/changes/         0      <-- la cola queda vacía
openspec validate --all --strict            65 passed, 0 failed
```

| Unidad | Cifra final |
|---|---:|
| Directorios del **MVP** | **33** |
| Directorios del **Proyecto Final** | **46** |
| **Fichas** de la tabla maestra, todas archivadas | **45** |
| Distancia entre las dos unidades | **1**, y se llama `fix-boot-drain-retries-both-drains` |

**El cruce cierra sin ninguna fila sin directorio y con exactamente dos directorios sin fila** —la
excepción del MVP y el seguimiento de C43—, que es el estado que el criterio de §2.1 predice. **Con esto
el Proyecto Final queda cerrado.**

**Y una comprobación del propio archivado, que el comprobador no hace.** `openspec validate` excluye
`openspec/changes/archive/**` por diseño, así que un change archivado queda un nivel más profundo y sus
`](../../../…)` se rompen **en silencio** — la ceguera que dejó acumular 874 enlaces. Revisado a mano:
**los artefactos de este change no contienen ningún enlace relativo**, sólo rutas entre comillas
invertidas, así que no hay nada que repuntar. Los enlaces de los dos documentos nuevos viven en
`Documentos/`, que no se mueve, y se comprobaron uno a uno: **0 rotos**.

**La spec viva nueva nació con su `## Purpose` en `TBD`** —el archivado lo deja así y lo dice— y **se ha
escrito**, porque una spec viva sin propósito es exactamente la clase de sync a medias que
`--all --strict` no puede ver: la sección existe y está vacía de contenido.

---

## Anexo A · Las secciones congeladas del README, con el texto propuesto

`README.md` no es un README técnico: **es el documento de entrega del máster**, y su estructura la fija la
plantilla. Estas secciones **no se editan sin mención expresa del responsable**: `## 0. Ficha del
proyecto`, `### 1.1`, `### 1.2`, `### 1.3`, `## 5. Historias de usuario` y `## 6. Tickets de trabajo`.

`git diff README.md` de este change **no toca ni una línea dentro de ellas**. Lo que sigue es lo que este
change habría escrito si pudiera, para que se decida con el texto delante.

### A.1 · `### 1.2` — el párrafo de IA cierra con «(en desarrollo)» y el proyecto está entregado

**Qué dice hoy.** El octavo epígrafe abre con *«**Búsqueda semántica y venta asistida (en desarrollo):**
Proyecto Final del Máster de IA»*.

**Por qué importa.** Es el rótulo que un evaluador lee primero sobre la capa que va a evaluar, y dice que
está en curso cuando está entregada, desplegada y verificada: cuatro superficies de operario en
producción, el agente entre ellas, y un despliegue en verde con sus diecisiete pasos.

**Texto propuesto** — cambia **cinco palabras** y no toca el resto del párrafo:

> **Búsqueda semántica y venta asistida (entregado):** Proyecto Final del Máster de IA. …

**Y una frase propuesta para el final del mismo epígrafe**, que es lo único que le falta al párrafo para
cerrar:

> **Y con C43 y su seguimiento el proyecto queda cerrado**: la copia del surtido que usa el buscador
> sabe qué tiendas están abiertas, así que una tienda cerrada a propósito deja de leerse como una tienda
> rota — un falso positivo que llegaba en rojo a la pantalla del administrador y que hizo fallar un
> despliegue sano. El arreglo introdujo a su vez un fallo verdadero en el arranque, y lo cazó el
> despliegue siguiente **porque la comprobación se había obligado a fallar con la tabla vacía en vez de
> pasar en vacío**: es el mejor ejemplo del proyecto de una condición de verificación ganándose el
> sueldo.

### A.2 · `### 1.2` — el salto «0,603 → 0,740» mezcla dos conjuntos dorados

**Qué dice hoy.** *«…el acierto sube de 0,603 a 0,740 de nDCG@5.»*

**Por qué es un problema.** El **0,603** es `v2-hibrido` bajo el golden set de **C24** (`1:1474bfc3aa3a`) y
el **0,740** es `v2b-fusion` bajo el de **C25** (`1:198c4af44506`), donde `v2-hibrido` mide **0,673**. Es
justamente lo que la spec de `retrieval-evaluation` prohíbe: dos corridas con procedencia distinta se
reportan como no comparables, no se restan. El salto real es **+0,067** en la tabla, y el que C25 publica
como decisión es **+0,083** sobre `v2` en el subconjunto que decide.

**Texto propuesto:**

> …el acierto sube de **0,673 a 0,740** de nDCG@5 sobre el mismo conjunto dorado, **+0,083** en el
> subconjunto de consultas que ninguna calibración había visto, que es la lectura que decide.

### A.3 · `## 0. Ficha del proyecto` — la autoría no es la del historial de git

**Qué dice hoy.** `### 0.1. Tu nombre completo` declara **Marcello Orrico**, y `### 0.5` apunta a
`https://github.com/marcello-clearcust/joiabagur-pv`.

**Con qué choca.** El autor de los commits es **Sergio Valdueza Lozano**, el remoto del repositorio es
`skydr4g0n-it/joiabagur-pv`, y el *tag* de entrega acordado es **`v1.0-final-SVL`**. Un evaluador que
cruce la ficha con el historial o con el *tag* encuentra tres nombres distintos.

**No se propone texto**, porque no es un dato que se deduzca del repositorio: es una decisión de quien
responde de la entrega. Lo que hay que decidir es **una sola cosa** —qué autoría y qué iniciales
gobiernan— y luego alinear los tres sitios: `### 0.1`, `### 0.5` y el nombre del *tag*.

### A.4 · `### 1.3` — el videotutorial sigue anunciado como pendiente

**Qué dice hoy.** *«Se añadirá un videotutorial en esta sección.»*

**Estado.** El **guion** está escrito y entregado en
[`c39b-video-script.md`](c39b-video-script.md); la **grabación** no es parte de este change. La frase
sigue siendo verdad y por eso **no se propone cambiarla todavía**: lo que se propone es sustituirla por el
enlace **el día que el vídeo exista**, y no antes.

### A.5 · `## 5` y `## 6` — sin hallazgos

Las tres historias de usuario y los tres tickets son **ejemplos escogidos para la entrega** y describen
correctamente lo que describen. No se ha encontrado nada desfasado en ellos. Se revisaron y se dejan
intactos.

### A.6 · Lo que ya es correcto y **no hay que rehacer**

Dos cosas que parecen errores y no lo son:

- **La línea 35 describe correctamente las cuatro cuentas de demostración** —una de administración y tres
  de operación, cada una en un punto de venta con surtido deliberadamente distinto—. **Describía un mundo
  que no existía** hasta que C39a-bis lo aprovisionó; hoy es cierta. No tocar.
- **Los `admin` / `Admin123!` de la línea 95 y de `backend/README.md`** son del apartado de **desarrollo
  local**, donde siguen siendo verdad: el sembrador los recrea en cada arranque. En el **entorno de
  demostración** esa misma cuenta está **desactivada a propósito** y debe seguirlo, lo que está
  documentado en el §5.8 del *runbook*. Las dos afirmaciones son compatibles porque hablan de entornos
  distintos.

---

## Anexo B · Lo que este change **no** ha verificado

Escrito aparte y nombre a nombre, para que ninguna afirmación del resto del informe se lea más ancha de lo
que es.

| No verificado | Por qué | Qué haría falta |
|---|---|---|
| **La tarjeta de salud de la IA pintada en pantalla** | una sesión de Claude Code no tiene navegador, y la vía .NET exige la contraseña de `demo.admin`, que no está en el repositorio | que el responsable la abra y lo confirme, con fecha. El **dato** sí está verificado (§7.2) |
| **El vídeo de entrega** | no se puede grabar desde una sesión | grabarlo siguiendo el guion |
| **Las cuatro cuentas probadas una a una en el navegador** | lo mismo | recorrido manual del guion |
| **El certificado de Let's Encrypt comprobado desde el anfitrión** | no se ha vuelto a medir en este change; el MITM de Norton de la máquina de desarrollo hace que un `ssl_verify_result=0` local acredite **la raíz de Norton**, no la real | `openssl s_client` desde dentro del anfitrión. Lo último medido: `YE1`, válido hasta **2026-11-28** |
| **`docker compose up` desde cero en una máquina limpia** | no hay máquina limpia en esta sesión | ensayo de reproducibilidad en un anfitrión sin caché de imágenes |
| **Las tres suites de tests** | este change no toca código ejecutable y ningún test lee el único fichero que añade bajo `ai-service/` | nada; queda declarado en §1 |
| **Que las 19 transcripciones de C32b fueran idénticas a las de hoy** | sus filas no llevan `turns_sha256` y la comparabilidad se decide por el `fixture`, que es la comprobación **más débil** | el 2 de 20 es un **suelo** del ruido, no una medición fina |
| **El validador .NET** | se **declara** como limitación con cifra esperada cero; no se implementa | §5.4 |
| **Las vías 2 y 3 de la alerta `CRITICAL`** | sólo se ejecuta la vía 1, que es documentación | §6.1 |
| **El comparador de deriva de rama** | los dos datos existen y hoy coinciden; la comprobación no está escrita | §6.3 |
