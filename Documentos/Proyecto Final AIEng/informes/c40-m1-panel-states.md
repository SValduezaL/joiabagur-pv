# C40 — la tabla de estados de M1 en el panel

**Change:** `add-frontend-free-query-panel` (C40) · **Fecha:** 2026-09-24
**Origen:** segunda pasada de la exploración de C40, esta vez contra el código de las tres capas
**Complementa:** [c40-exploration-decisions.md](c40-exploration-decisions.md), del que hereda las diez
decisiones y las cuatro preguntas cerradas

Este documento existe por una razón: **el panel de hoy tiene cinco ramas de vacío y M1 tiene
dieciséis estados**. El informe de exploración nombra cuatro de los nuevos; los demás salen de leer
las combinaciones de campos que el servicio puede devolver, y tres de ellos se pintarían mal por
defecto.

Es la misma disciplina que C36 aplicó a sus siete códigos de aviso, con una diferencia que importa:
**la unidad no es el campo, es el estado**, porque son combinaciones de campos y la pantalla se
equivoca en las combinaciones, no en los campos. La verificación campo a campo del §5 del informe
—necesaria— no habría encontrado ninguno de los tres.

---

## 1 · La máquina del enrutador, exacta

Lo primero que hay que fijar, porque el informe lo describe con una frase que es cierta y no es
suficiente. `route = none` **no es un estado**: son dos, y sólo `intent` los separa.

```
        AssistRequest(product_id=null, query="…", filters={…})
                              │
                              ▼
                    classify_query()  ← una llamada, sin reintento, sin reparación
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
   decision is None                          decision is not None
   (sin credencial · timeout 2 s ·                 │
    respuesta que no parsea)                       │
         │                                         │
    intent=unclassified              ┌─────────────┼─────────────┬──────────────┐
    route=None                       │             │             │              │
    FAIL-OPEN: se consultan     served=            served=   in_domain      in_domain
    LAS DOS ramas               out_of_domain  not_in_        +              + suficiente
         │                                     catalogue   missing_axis          │
    task=None → SIN PROSA            │             │        ≠ None          ┌────┴────┐
    resultados + citas          SIN recuperar  SIN recup.       │      index=null  index=
         ▼                      código propio  código propio  SIN recup.     │    catalog|
    ESTADO 5                         ▼             ▼        la repregunta    │    knowledge|
                                ESTADO 1      ESTADO 2         ▼             │    both
                                                          ESTADO 3      route=None     │
                                                                        se consultan   │
                                                                        LAS DOS ramas  │
                                                                        task=None      │
                                                                        SIN PROSA      ▼
                                                                            ▼     ESTADOS
                                                                        ESTADO 4   6 a 16
```

Las tres propiedades que hacen esto exacto, y que no están en el informe:

| Propiedad | Dónde | Consecuencia |
|---|---|---|
| `is_sufficient` **es** `missing_axis is None` | [schema.py:74](../../../ai-service/src/jbg_ai/assist/schema.py#L74) | `route=None` con veredicto servido ⟺ hay repregunta **o** `index` es nulo. No hay tercera vía |
| `index` es **nullable** en una decisión servida y suficiente | [schema.py:54](../../../ai-service/src/jbg_ai/assist/schema.py#L54) | es el mecanismo real del `route=none` que H7 midió al 11,9 % |
| `refusal_codes` devuelve `()` cuando `decision is None` | [routing.py:222](../../../ai-service/src/jbg_ai/assist/routing.py#L222) | el enrutador degradado **no emite ningún código**. Sólo `intent` lo delata |

### El estado 4 es una respuesta internamente contradictoria del clasificador

Y esto cambia qué hay que hacer con él. El esquema dice de `index`: *«Null cuando **no se
atiende**»*, y de `missing_axis`: *«null siempre que **no se atienda**»*. Un veredicto `in_domain`
**es** atender. Así que el modelo devuelve a la vez *«esta consulta es de esta joyería»* y *«no se
atiende»*, y el código, que no puede saber a cuál de las dos creer, no ejecuta ninguna tarea.

Dispara en **5 de 42 · 11,9 %** (H7). No es «el clasificador decidió no decidir»: es **el
clasificador contradiciéndose**, y eso admite un arreglo que no es copia de pantalla.

**Y hoy el servicio ya paga las dos ramas y luego tira la capacidad de escribir sobre ellas.** Con
`route=None` el orquestador consulta catálogo *y* corpus —`if route in (None, "catalog", "both")` y
`if … route in (None, "knowledge", "both")`—, recupera quince piezas y hasta cinco fragmentos, y
después no genera porque no hay sección de tarea. Es exactamente el trabajo tirado que la regla de
completitud del §5 del informe condena, sólo que dentro del servicio.

**Propuesta: coerción a `both`, con la contradicción observable.** Ver el §4.

---

## 2 · Los dieciséis estados

Ordenados por **qué capa decide**, que es también el orden en que se cortan. Leyenda: `pv` =
`prompt_version`.

### El enrutador decide, antes de recuperar nada

| # | Estado | `intent` | grupos | citas | `pitch` | `pv` | `abstained` | Otro |
|---|---|---|---|---|---|---|---|---|
| **1** | rechazo · fuera de dominio | `out_of_domain` | 0 | 0 | `""` | `null` | `false` | `warnings=[query_out_of_domain]` |
| **2** | rechazo · no en catálogo | `not_in_catalogue` | 0 | 0 | `""` | `null` | `false` | `warnings=[query_not_in_catalogue]` |
| **3** | **repregunta** | `in_domain` | 0 | 0 | `""` | `null` | `false` | `clarification_question` ≠ null |
| **4** | admitida sin índice | `in_domain` | ≤15 | ≤5 | `""` | `null` | `false` | nada la delata salvo la forma |
| **5** | **enrutador degradado** | `unclassified` | ≤15 | ≤5 | `""` | `null` | `false` | nada la delata salvo `intent` |

**Qué pinta la pantalla**

| # | Copia | Resultados | Citas | Acción que ofrece |
|---|---|---|---|---|
| 1 | «Esto no es una pregunta de joyería» — §15.13, **la escribe C40** | — | — | volver a la caja de consulta |
| 2 | «No trabajamos ese tipo de pieza» — §15.13, **la escribe C40**, y **es un texto distinto del 1** | — | — | ídem |
| 3 | **la pregunta del servicio, tal cual** (catálogo cerrado de cuatro, en castellano, en [routing.py:100](../../../ai-service/src/jbg_ai/assist/routing.py#L100)) | — | — | **el foco vuelve a la caja**, que es la acción que la pregunta pide |
| 4 | «No he acabado de entender la consulta; prueba a formularla de otra manera» | **sí** | **no** | reformular |
| 5 | «El argumentario no está disponible ahora mismo» | **sí** | **no** | *ninguna del operario* — **no se le pide reformular** |

> **La distinción 4 / 5 es la corrección más importante de este documento a la Q3 del informe.**
> Q3 cierra `route=none` con *«pedir que se reformule»*. Correcto para el 4 —el enrutador corrió y
> se contradijo— y **falso para el 5**: ahí el clasificador nunca corrió (sin credencial, *timeout*
> de 2 s sin reintento, o respuesta no parseable), y pedirle al operario que reformule es **echarle
> la culpa de una credencial ausente**. Es, literalmente, la avería del §1 del informe: una
> capacidad apagada presentada como algo que el usuario hace mal.
>
> Y no es un camino teórico. Con la credencial del enrutador ausente —estado que
> `DEFERRED_TASKS.md` describe para la demo, aunque C31 repliega a la clave de *assist*— **todas**
> las consultas de M1 caen en el 5. Un panel que pidiera reformular en todas sería la peor demo
> posible del proyecto.

### La recuperación decide

| # | Estado | `intent` | grupos | citas | `pitch` | `pv` | `abstained` |
|---|---|---|---|---|---|---|---|
| **6** | abstención · perfil plano | `in_domain` | 0 | 0 | `""` | `null` | **`true`** |
| **7** | **filtro estrecho** (D9, nuevo) | `in_domain` | pocos | ≤5 | ¿? | ¿? | `false` |

**El 6 ya se pinta** — es la rama `lowConfidence` del panel actual. Nota de forma: con `abstained`
el corpus **no se consulta** (`if not abstained and route in (…)`), así que las citas son cero por
construcción y no por ausencia de cobertura.

**El 7 es nuevo y necesita dos decisiones que C40 tiene que tomar:**

1. **¿Cómo lo aprende la pantalla?** Recomendación: **un código nuevo del vocabulario cerrado**,
   `filters_too_narrow`, no una derivación en el frontend a partir de `candidatesReturned` más «hay
   filtros puestos». El vocabulario es cerrado y versionado, la pantalla ya tiene la regla de
   etiqueta neutra para un código desconocido, y una derivación en el cliente es una regla que
   nadie mantiene.
2. **¿Se genera argumentario?** Recomendación: **sí**, si hay piezas. Las pocas que sobrevivieron al
   filtro **sí encajan con la descripción** —eso es precisamente lo que la sonda sin filtro acaba de
   establecer—, así que hablar bien de ellas no es el fallo que la abstención previene. Lo que hay
   que decir al lado es que el filtro dejó fuera lo demás.

> **Y aquí hay una contradicción dentro del informe que hay que resolver antes de implementar.** D8
> dice *«los avisos no se pintan en el listado»* porque `warnings` describe una sola pieza. Pero
> `routing.refusal_codes` se **apila en esa misma lista** —[orchestrator.py:387](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L387)—,
> así que D8 aplicado literalmente **se comería los dos códigos de rechazo** para los que §15.13
> obliga a escribir castellano. La partición correcta no es por lista, es por **sujeto**:
>
> | Sujeto del aviso | Códigos | En M1 |
> |---|---|---|
> | **una pieza** | `family_has_variants`, `size_label_missing`, y los dos de stock que apila .NET | **no se pintan** — D8, y sigue siendo correcto |
> | **la consulta** | `query_out_of_domain`, `query_not_in_catalogue`, `knowledge_not_covered`, `filters_too_narrow` | **sí se pintan** |

### La generación decide

| # | Estado | grupos | citas | `pitch` | `pv` |
|---|---|---|---|---|---|
| **8** | ruta `catalog` con prosa | ≤15 | **0 por diseño** | sí | sí |
| **9** | ruta `knowledge` con prosa | **0** | ≤5 | sí | sí |
| **10** | ruta `both` con prosa | ≤15 | ≤5 | sí | sí |
| **11** | la puerta retiró **alguna** cita | ≤15 | reducidas | sí | sí |
| **12** | la puerta retiró **el argumentario** (causa dura) | ≤15 | **se mantienen** | `""` | **sí** |
| **13** | `knowledge`/`both` **sin corpus** | según ruta | **0** | sí | sí |
| **14** | **sin credencial de generación** | ≤15 | ≤5 | `""` | **`null`** |
| **15** | **marcador en el argumentario de M1** | ≤15 | ≤5 | `""` | sí |

**El 9 es el que se pinta mal por defecto.** Cero piezas y una respuesta correcta. Las cinco ramas
de vacío del panel actual —[assisted.tsx:424-460](../../../frontend/src/pages/sales/assisted.tsx#L424)—
escribirían *«Sin resultados»* encima de una buena respuesta de conocimiento. **Requisito: con
`route=knowledge` la ausencia de piezas no es un vacío y no se anuncia como tal.**

**El 11 es Q2** y su frecuencia está medida: **26,4 %** de las citas declaradas se retiran en M1 y
**24,3 % de las respuestas de conocimiento se quedan sin ninguna fuente** —el doble que en los
modos anclados—. Por eso la etiqueta «sin fuente verificable» va **discreta, una línea junto al
argumentario**, no como alerta.

**El 12 y el 14 se distinguen sólo por `prompt_version`**, y son cosas opuestas: en el 12 el modelo
escribió y la puerta lo retiró; en el 14 **no hubo generación**. C36 ya sabe pintar esa distinción
(`withheld_by_ai` frente a `not_generated`) y su test lo fija. **Se reutiliza tal cual.**

> **Y una tensión deliberada que conviene no «arreglar».** En el 12 el servicio **conserva las
> citas** a propósito: *«a degraded response must never be poorer than the one the structured layer
> produces on its own, which is what keeps the ablation comparable»*
> ([orchestrator.py:402](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L402)). La pantalla,
> por la regla de Q3, **no las pinta**: una cita sin afirmación no atribuye nada. Las dos
> decisiones son correctas y apuntan en direcciones distintas porque sirven a consumidores
> distintos — el arnés y el operario. Quien lea una de las dos sin la otra va a intentar
> unificarlas.

**El 13 no tiene hoy salvaguarda, y es el segundo hueco del informe.** `uncovered` se calcula
**sólo en la rama anclada** ([orchestrator.py:311](../../../ai-service/src/jbg_ai/assist/orchestrator.py#L311)),
y `FREE_QUERY_TASKS` tiene tres entradas sin variante «sin cobertura»
([prompt.py:139](../../../ai-service/src/jbg_ai/assist/prompt.py#L139)). Así que una consulta de
conocimiento en M1 con cero fragmentos ejecuta la tarea que dice *«Responde a la pregunta
apoyándote en esos fragmentos»* **sin fragmentos**: una invitación explícita a contestar de memoria,
en el modo que C40 saca a pantalla, sin la red que M3 tiene desde C34.

El caso está **medido en el propio informe y leído como otra cosa**: en su H5, *«un anillo que se
pueda mojar en la piscina»* → ruta `both`, 15 piezas, **0 citas** ⚠. El ⚠ se interpretó como «las
citas dependen de la ruta». Lo que es: **la tarea equivocada corriendo sobre un contexto vacío.**

La copia castellana **ya existe**: `knowledge_not_covered: 'La documentación no cubre esta pregunta'`
en [assist-copy.ts:51](../../../frontend/src/lib/assist-copy.ts#L51). Falta el lado Python.

**El 15 es el hallazgo que bloquea el tramo 2** y está razonado en el §2 del informe ampliado. Con
`assist/v5` más la causa dura `placeholder_in_free_query`, debe caer a cero; el barrido de
verificación es el que lo tiene que decir.

### .NET decide

| # | Estado | `aiAvailable` | Qué enseña |
|---|---|---|---|
| **16** | interruptor apagado · circuito abierto · credencial rechazada · 422 no indexado · 501 · sin clasificar | `false` | resultados léxicos, **con los filtros aplicados** (D5) |

`degradedReason` tiene **seis** valores que `SalesAssistService` calcula, escribe en su línea de
registro y **descarta al construir la respuesta**. Subirlo al DTO es lo que cierra la limitación 3
de C34 y separa `product_not_indexed` de `ai_unavailable`, que hoy se ven igual.

---

## 3 · Lo que esto obliga a decidir sobre el badge

El informe pide un badge de disponibilidad de la IA, *«encendido o apagado»*. Son **cuatro
estados**, porque hay **dos interruptores independientes**, cada uno con su límite de tasa, su
presupuesto de tiempo y su circuito:

| `AiSearch` | `AiSalesAssist` | Qué puede hacer el operario |
|---|---|---|
| on | on | las dos rutas del toggle |
| on | **off** | semántica sí; **la opción asistida se deshabilita con su motivo**, no cae en silencio |
| **off** | on | la semántica degrada a léxica; la asistida funciona *(raro y posible)* |
| off | off | todo léxico |

Y tres consecuencias:

1. **D4 pide el badge *antes* de buscar, y hoy no hay de dónde leerlo.** `aiAvailable` llega
   **dentro** de la respuesta, es decir después. `AiHealthResponse` existe pero es de administrador
   y describe infraestructura, no los interruptores por punto de venta. **C40 necesita una ruta de
   lectura nueva, barata y sin IA**, que reporte los dos interruptores para un POS. No está en la
   línea de corte del informe.
2. **Hay un tercer eje que el badge no puede ver: el enrutador.** El estado 5 es «la IA respondió y
   el clasificador no corrió». Ningún interruptor lo anuncia; sólo `intent=unclassified` en la
   respuesta. Así que el badge cubre la disponibilidad *antes*, y el estado 5 cubre la degradación
   *durante*. **Son dos avisos, no uno.**
3. **El toggle debe decir el coste antes de pulsarse, y ahora hay cifras:** presupuesto de
   **2.500 ms** para la semántica contra **10.000 ms** para la asistida, y un límite de **30/min**
   contra **10/min**. Un 4× de reloj y un 3× de cupo.

---

## 4 · Las tres cosas que este documento propone y el informe no tenía

### P1 · El estado 4 se arregla en el enrutado, no en la pantalla

**Coerción a `both`** cuando el veredicto es `in_domain`, `missing_axis` es nulo e `index` es nulo.

- **Pros.** Elimina el 11,9 % de un estado degenerado en vez de documentarlo. **Los datos que la
  tarea necesita ya se están recuperando**: el *fail-open* de `route=None` consulta las dos ramas,
  así que hoy se paga el catálogo y el corpus y después se tira la prosa. Y es más fiel a la propia
  regla de desempate del prompt del enrutador —*«Ante la duda, `in_domain`»*—: si se admite la
  consulta, se atiende.
- **Contras.** Hace invisible la contradicción del clasificador. **Se resuelve sin renunciar a
  nada**: una causa propia en el registro (`router_index_absent`) y su recuento, sin tocar la
  respuesta. Es el patrón que este repositorio ya usa para leer su puerta — partir por causa.
- **Riesgo aceptado.** Generar sobre `both` cuando el modelo dudaba puede dar un argumentario peor.
  Pero el *fail-open* **ya decidió** que consultar los dos índices es la respuesta correcta a una
  clasificación ausente; escribir sobre lo que se ha consultado es la continuación coherente de esa
  decisión, no una nueva.
- **Lo que no arregla, y hay que decirlo:** el estado 5 sigue sin tarea. La copia de Q3 sobrevive,
  pero para el estado correcto y a una frecuencia mucho menor —sólo cuando el enrutador falla de
  verdad—.

**Alternativa considerada y descartada: un `model_validator` que rechace la combinación.** Haría
fallar el parseo → `RouterProviderError(cause="parse")` → *fail-open* → **estado 5**. O sea: mueve
el 11,9 % del estado 4 al 5, que es el estado con la peor copia posible. Cambia una etiqueta, no un
comportamiento.

### P2 · `filters_too_narrow` como código, y la partición de D8 por sujeto

Ver el §2, estado 7. Lo que hay que escribir en la spec es la **partición por sujeto del aviso**,
porque D8 tal como está redactado se come los dos códigos de rechazo.

### P3 · La ausencia de piezas en `route=knowledge` no es un vacío

Requisito explícito, con test. Es el estado 9 y es el que el panel de hoy pinta mal sin que nadie
haya cambiado nada.

---

## 5 · Cómo se verifica esta tabla

**Un barrido, no un desarrollo.** El arnés ya guarda lo necesario y las 42 consultas del conjunto
etiquetado ya existen —las 32 `eval_question` del corpus más las 10 consultas `both` de C31—.

| Qué hay que publicar | De dónde sale |
|---|---|
| Reparto de los 16 estados sobre las 42 consultas | `stage=assist` ya registra `intent`, `route`, `router_degraded`, `task`, `groups`, `citations`, `abstained`, `pitch_chars`, `violations`, `withdrawn` |
| **Marcadores en el argumentario de M1**, antes y después de `v5` | recuento de `{{price}}` y `{{stock}}` sobre el texto generado. **Es la cifra que hoy no existe y que decide si M1 tiene prosa** |
| `route=none` partido en 4 y 5 | `intent` más `router_degraded` |
| Tasa de `router_index_absent` | la causa nueva de P1 |
| Latencia p50/p95 **extremo a extremo por .NET** | como midió C34 para los modos anclados. Las 42 del informe se midieron contra Python directo |

**Y una nota sobre los artefactos:** la pasada de 42 consultas del H6 **no quedó persistida** en
`ai-service/evals/results/` — no hay ningún `c40-*.json`. Las cifras del informe son reproducibles
pero no re-puntuables. La pasada de verificación de C40 sí debe persistirse, con `run_id`, `git_sha`
y `prompt_version`, como hicieron C30b, C31 y C32b.
