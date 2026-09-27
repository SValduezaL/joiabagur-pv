# T-AIENG-031: Intent router and guardrails — two gates, two published figures, and the system's right to say "I don't know" (C31)

> **Idioma.** Título e identificadores técnicos en inglés, cuerpo en español — la regla que ya
> siguen [T-AIENG-030b](../../archive/2026-09-14-add-assist-pitch-generation/ticket.md),
> [T-AIENG-030a](../../archive/2026-09-13-add-assist-structure-and-rule-warnings/ticket.md) y
> [T-AIENG-026](../../archive/2026-09-12-add-substitutes-retrieval/ticket.md).

**HU origen:** [HU-AIENG-031](../../../../Documentos/Historias/AI-Eng/HU-AIENG-031.md)
**Change:** `add-guardrails-and-intent-router` (C31) · **Épica:** EP15
**Rama:** `c31-add-guardrails-and-intent-router` · **Conjunto de enrutado:** [`evals/routing/cases.yaml`](../../../../ai-service/evals/routing/cases.yaml)

---

## Título

Añadir el **enrutador de intención y los guardarraíles de entrada** sobre la capa de generación que
dejó C30b: clasificación de la consulta libre **antes de recuperar nada**, con **dos puertas
distintas** —dominio y cobertura de catálogo—, **rechazo cortés** como *safe-completion*,
**repregunta determinista** ante consultas ambiguas, **guardarraíl gratuito** en el modo anclado con
pregunta, y el **argumentario de la consulta libre** que C30b difirió. **No mueve la forma del
contrato**: `intent` es `str` plano y `clarification_question` ya existe, así que el movimiento es de
**descripción**.

---

## Contexto y Problema

La spec viva declara hoy, con estas palabras, el hueco que este change llena:

```
# openspec/specs/assist-generation/spec.md:398
### Requirement: The provider is not called when there is nothing to write about
The service SHALL NOT call the language model provider when the abstention rule has decided
that the catalogue cannot answer the query, and MUST NOT call it in the free-query mode.
[…] The free-query mode does not generate because classifying a query is a later
capability's work […]. The clarification question likewise belongs to that later capability
and MUST remain absent here.
```

```
# openspec/specs/assist-generation/spec.md:39
### Requirement: The detected intent is derived from the request shape and never guessed from words
[…] In every other mode the intent MUST be reported as unclassified, because classifying a
query is not this capability's work.
```

Este change **retira el primero e invierte el segundo**. Es el mismo movimiento que C30b hizo con el
requisito de C30a *«esta capability no genera prosa y no llama a ningún proveedor»*: un requisito que
se retira a los pocos días no es una corrección, es el corte funcionando como estaba diseñado.

### El problema que la ficha del plan no ve: «fuera de dominio» son dos conjuntos

La ficha de C31 se justifica con *«sin puerta, C30 contestaría «¿qué tiempo hace mañana?» […] medido,
**18 de 20** consultas fuera de dominio llegan hoy con candidatos»*. **Las dos mitades no hablan del
mismo conjunto.** Comprobado leyendo las veinte:

| Conjunto | Qué es | Ejemplos | ¿Clasificable sin recuperar? | n en el repo |
|---|---|---|---|---|
| **A · dominio** | No es una pregunta de joyería | `¿Cuál es la capital de Australia?` · `¿A qué hora abrís los domingos?` | **Sí** | **5** (`data/knowledge/_eval/out-of-domain.yaml`) |
| **B · cobertura** | Es joyería y **este** catálogo no la tiene | `un salero de plata` · `un lingote de oro` · `una correa de reloj marron` | **No por intención** — es cobertura | **20** (categoría mayor del golden set) |

`criterion.md` lo dice explícitamente de las veinte: *«son plausibles **dentro de la joyería** y el
catálogo no las puede satisfacer»*. Un clasificador de intención puro **contestaría que sí a las
veinte** y no movería el 18 de 20 con el que la ficha se justifica. Este change cubre **las dos
puertas** y publica **dos cifras que nunca se suman**.

### Estado actual del código, verificado en el repositorio

| Pieza | Estado verificado | Qué implica |
|---|---|---|
| [`assist/modes.py`](../../../../ai-service/src/jbg_ai/assist/modes.py) | Resuelve M1/M2/M3 **por anclas y nunca por palabras**; `intent` ∈ {`product_pitch`, `unclassified`} | El hueco está marcado, no improvisado. Su docstring promete: *«ese router reemplazará a `unclassified`, nunca a `product_pitch`»* |
| [`assist/orchestrator.py`](../../../../ai-service/src/jbg_ai/assist/orchestrator.py) | Genera en M2 y M3; en M1 **no llama al proveedor**; `clarification_question=None` con comentario *«Declarado de C31»* | El cableado tiene **un punto de entrada exacto**, antes de `retrieve_products` |
| [`assist/llm.py`](../../../../ai-service/src/jbg_ai/assist/llm.py) | Costura con temperatura 0, `num_retries: 0`, `response_format`, `complete` inyectable, *timeout* propio | **La costura se replica**; la clase no se reutiliza |
| [`assist/prompt.py`](../../../../ai-service/src/jbg_ai/assist/prompt.py) | `QUERY_OPEN`/`QUERY_CLOSE`; lista blanca numérica desde `as_data()` y **nunca desde el prompt renderizado**; `PitchPayload` es **de una pieza** | La mitigación de inyección **ya está y no se rehace**. El *payload* de M1 **no existe** |
| [`assist/constants.py`](../../../../ai-service/src/jbg_ai/assist/constants.py) | `DEFAULT_ASSIST_MODEL`, `PITCH_TIMEOUT_SECONDS`, `MAX_PITCH_PROVIDER_CALLS = 2`, vocabularios cerrados | El patrón de constante-con-medición-al-lado, que este change extiende |
| [`knowledge/search.py`](../../../../ai-service/src/jbg_ai/knowledge/search.py) | `distance_threshold` **por parámetro**; defecto `0,51` | El guardarraíl de M3, **gratis y ya medido** |
| [`api/schemas/assist.py`](../../../../ai-service/src/jbg_ai/api/schemas/assist.py) | `intent: str` **plano**, `clarification_question: str \| None`, `warnings: list[str]` | **Cero movimiento de forma** en `openapi.json` |
| [`evals/routing/cases.yaml`](../../../../ai-service/evals/routing/cases.yaml) | Escrito el 2026-09-14; 5 clases por referencia + 10 casos `both` | El conjunto de evaluación **ya existe** |
| `IAiGatewayClient` (.NET) | Cinco métodos, **ninguno de assist** | `/v1/assist/sale` sigue con **cero consumidores**: la ventana barata para mover contrato |

### Los tres hallazgos que gobiernan el diseño

**1 · El presupuesto de latencia ya está justo, y este change no puede empeorarlo.**

```
AssistTimeoutMs (.NET, appsettings.json:55) ················ 5.000 ms
recuperación híbrida completa ······························   129 ms
una llamada de generación, p50 / p95 (175 llamadas, C30b) ·· 2.216 / 2.863 ms
peticiones que gastan la reparación ························    55 %
  ⇒ una petición reparada, del orden de ···················· ~4.400 ms
```

De ahí sale la decisión central: **el enrutador cuesta una llamada y sólo en M1**, que es el modo
**sin ruta .NET** (§15.12 del diseño). M2 no tiene consulta que clasificar; M3 es `both` por
construcción —la pieza es el lado de catálogo y la pregunta el de conocimiento— y su guardarraíl sale
gratis del umbral que ya corre.

**2 · El guardarraíl de M3 existe, está medido y nadie lo lee como tal.** C23 fijó `0,51` sobre un
**hueco limpio de 8 milésimas**: las 32 preguntas que el corpus responde por debajo, las 5 de fuera
por encima — **100 % y 0 %**. Hoy M3 genera igual cuando llegan cero citas, y el consumidor no puede
distinguir «el corpus no lo cubre» de «no había nada que citar».

**3 · El conjunto de evaluación llevaba tres días escrito, esperando.** Las cuatro consultas
`ambigua` del golden set están declaradas **sin juicios de relevancia** con esta nota, anterior a que
ningún change reclamase `clarification_question`:

> *«Declarada sin juicios: **la respuesta correcta es una repregunta**, y eso es una decisión del
> agente.»* — `q53 · algo bonito`

---

## Componentes Afectados

- **`ai-service/src/jbg_ai/assist/`** — módulos nuevos: cliente del clasificador, esquema de salida
  del enrutador, catálogo de plantillas de repregunta y el *payload* de la consulta libre. Cableado
  en `orchestrator.py`, constantes nuevas en `constants.py`.
- **`ai-service/prompts/assist/`** — `v2.md` nuevo con las secciones de tarea de la consulta libre;
  **`v1.md` se conserva** y no se toca.
- **`ai-service/src/jbg_ai/api/schemas/assist.py`** — sólo **descripciones**: el vocabulario de
  `intent`, el de `warnings[]` y el de `clarification_question`.
- **`ai-service/src/jbg_ai/config/settings.py`** — tres ajustes nuevos con su cadena de repliegue.
- **`ai-service/openapi.json`** — regeneración con el perfil canónico, **sólo descripciones** de
  diferencia. Verificación **campo a campo** aplanando los dos documentos a hojas, como hizo C30b.
- **`ai-service/evals/routing/`** — carga del manifiesto y runner de la matriz de confusión;
  artefactos en `evals/results/`.
- **`ai-service/tests/`** — `assist/`, `api/`, `evals/`, en árbol espejo.
- **`openspec/changes/add-guardrails-and-intent-router/`** — proposal, design, specs y tasks.
- **`openspec/DEFERRED_TASKS.md`** — los cuatro pasos de despliegue de las variables nuevas.
- **`Documentos/`** — épicas, plan de changes e informe de implementación.

**No tocados a propósito:** `backend/`, `frontend/`, `terraform/`, `.github/workflows/`,
`ai-service/migrations/`, `retrieval/` y `enrichment/`. **`knowledge/` sólo se lee**: el guardarraíl
de M3 se construye sobre el resultado de `search_knowledge`, no dentro de él.

---

## Especificaciones Técnicas

### ai-service — el esquema de salida del enrutador, interno y no publicado

```python
# jbg_ai/assist/routing.py  (NO es jbg_ai/api/schemas: no viaja al cable)
class RouteDecision(BaseModel):
    served: Literal["in_domain", "out_of_domain", "not_in_catalogue"]
    index:  Literal["catalog", "knowledge", "both"] | None   # None cuando no se atiende
    missing_axis: Literal["piece_type", "material", "occasion", "price"] | None

# proyección a la respuesta:
#   served       → AssistResponse.intent              (vocabulario cerrado, validado EN CÓDIGO)
#   served       → AssistResponse.warnings[]          (código de motivo del rechazo)
#   missing_axis → AssistResponse.clarification_question  (plantilla es-ES elegida por código)
#   index        → NO viaja al cable: decide qué se ejecuta y qué sección de tarea se usa
```

**La etiqueta que devuelve el modelo se valida contra el conjunto cerrado antes de usarse.** Un
`Literal` de Pydantic lo hace en el parseo, y una etiqueta fuera del conjunto es un fallo de parseo
—o sea, *fail-open*— y nunca un valor que se propague.

### ai-service — comportamiento por modo

| Modo | ¿Llama al clasificador? | Ruta | Guardarraíl |
|---|---|---|---|
| **M2** pieza sin pregunta | **No** — no hay consulta | — | Ninguno nuevo. `intent = product_pitch` intacto |
| **M3** pieza con pregunta | **No** — `both` por construcción | `both` | **Determinista y gratis**: cero citas tras `0,51` ⇒ código de aviso + tarea degradada |
| **M1** consulta sola | **Sí, una vez, sin reparación** | según decisión | Rechazo cortés o repregunta, **antes de recuperar** |

### ai-service — la puerta de entrada de M1, y qué corta

```
consulta libre
   │
   ├─ served = out_of_domain    → groups=[], intent=out_of_domain,  warnings=[…]
   ├─ served = not_in_catalogue → groups=[], intent=not_in_catalogue, warnings=[…]
   ├─ missing_axis != None      → groups=[], clarification_question=<plantilla>
   └─ in_domain + sufficient    → index decide qué índices se consultan
                                   │
                                   └─ abstención de C25 sigue corriendo: es la RED
```

**`abstained` NO se reutiliza para el rechazo del enrutador.** Son dos mecanismos —uno lee la forma
del perfil de distancias *después* de recuperar, el otro clasifica *antes*— y confundirlos haría
indistinguibles las dos cifras que este change existe para publicar por separado.

### ai-service — el *payload* de la consulta libre y su lista blanca numérica

`PitchPayload` es hoy **de una pieza**: `sku`, `piece_type`, `materials`, `size_label`,
`variant_label`, `variants`, `citations`. M1 devuelve **hasta cinco grupos y ninguna pieza anclada**,
así que hace falta una segunda forma.

```python
# La lista blanca sale de as_data(), como en C30b, así que CADA candidato la ensancha.
# Se excluyen explícitamente, por la misma razón que C30b excluyó product_id:
#   - identificadores internos de producto (dígitos arbitrarios, nunca se dicen en mostrador)
#   - los scores de recuperación
```

**Es el punto de mayor riesgo del change.** La puerta numérica midió **0 violaciones en 120
generaciones** con una lista blanca de una pieza; cinco candidatos aportan cinco SKU, cinco tallas y
cinco etiquetas de variante. La medición de la tasa de rechazo en M1 se publica **aparte** de la de
M2/M3, porque no miden la misma puerta.

### ai-service — el prompt versionado

`prompts/assist/v2.md`. **`v1.md` se conserva**: añadir secciones a v1 movería en silencio lo que
«v1» significa para las 120 generaciones ya medidas de C30b, y esas cifras tienen que seguir siendo
interpretables. Las **reglas invariantes del sistema no cambian** — mismo bloque, misma prohibición
de cifras, misma delimitación de la consulta como dato—; lo nuevo son las secciones de tarea de la
consulta libre, una por ruta.

> **De paso, esto entrega la progresión v1→v2 que C39 pide por escrito** (*«progresión de prompts
> v1→v2 con impacto medido»*, §11.6 del diseño). Nada más en el grafo la iba a producir.

### ai-service — el cliente del clasificador y su presupuesto

| Propiedad | Valor | Razón |
|---|---|---|
| Llamadas por petición | **1, sin reparación** | La salida es una etiqueta; no hay nada que reparar. Un fallo de parseo es *fail-open* |
| Techo del sistema | **3 llamadas** (1 enrutador + 2 argumentario) | Literal y comprobable por introspección, como el de 2 de C30b |
| Temperatura | **0** | Reproducibilidad de la evaluación, igual que C09 y C30b |
| *Backoff* de proveedor | **No** | Mismo argumento que C30b: consume el presupuesto antes de que arranque la llamada reintentada |

### ai-service — configuración

| Variable | Defecto | Notas |
|---|---|---|
| `JPV_ROUTER_LLM_MODEL` | `openai/gpt-4o-mini`, desde `DEFAULT_ROUTER_MODEL` | **No hereda** de `JPV_ASSIST_LLM_MODEL` ni de `JPV_RAG_LLM_MODEL`: son llamadas de forma muy distinta —~30 *tokens* de salida contra un párrafo— y compartir variable haría falsa cualquier comparación de coste. Mismo argumento medido que C30b usó para no heredar de C09 |
| `JPV_ROUTER_LLM_API_KEY` | ausente ⇒ repliega | Cadena **router → assist → rag**. C30b abrió los dos últimos eslabones; éste prepende uno |
| `JPV_ROUTER_TIMEOUT_SECONDS` | **2.0** | **Declarado no calibrado**, igual que C30b abrió en 3 s «como juicio de producto sin medición detrás» y su barrido lo movió a 4. Va delante de todo, así que su corte es más duro |

```
stage=router_client model=openai/gpt-4o-mini timeout_s=2.0 credential=router
```

`credential=assist_fallback` o `rag_fallback` dirían que repliega; `stage=router_client` ausente, que
no se construyó cliente y la ruta se comporta como C30b. **Es la misma comprobación sin consola ni
claves** que C30b dejó escrita.

### ai-service — contrato

**Cero movimiento de forma.** `intent` es `str` plano, `clarification_question` ya existe y
`warnings[]` es `list[str]` con su vocabulario en la descripción. Lo que cambia son **descripciones**,
y la verificación es la misma que C30b ejecutó: aplanar los dos `openapi.json` a hojas y comprobar
que **ningún campo se añade, se retira ni cambia de tipo**.

### Seguridad y ámbito

- El **JWT interno HS256** y el ámbito por `pos_id` no cambian: el enrutador corre **dentro** de la
  ruta ya autenticada, y `payload.pos_id` se sigue ignorando en favor del token.
- La consulta del operario **es la única superficie que controla alguien fuera del código**, y sigue
  viajando como dato delimitado en el mensaje de usuario — también en la llamada del clasificador.
- **La consulta no entra en la lista blanca numérica**, ni aquí ni en C30b: es *qué contestar*, no
  *qué es cierto*.

### Datos

**Ninguno.** Sin migración, sin tabla nueva y sin persistencia: ni la decisión del enrutador ni la
repregunta se guardan. El log registra la etiqueta, el motivo, la latencia y el coste — **nunca el
texto de la consulta**, por la misma regla que C30b aplicó al argumentario.

---

## Arquitectura

Decisiones previas que aplican sin cambio:

- **La frontera del §6.2**: Python clasifica y redacta; la autoridad sobre precio y stock sigue
  siendo de .NET. El enrutador no toca ninguna de las dos.
- **Códigos en el cable, copy en el frontend** — `assisted-search-panel` lo declara literalmente para
  los `match_reasons`, y C30a lo aplicó a `warnings[]`. El rechazo y la repregunta son dos filas más
  de la tabla de copy de C36. **Excepción razonada:** `clarification_question` está **tipada como
  prosa**, así que el frontend no puede resolverla; se resuelve en Python desde un catálogo cerrado
  de plantillas, que conserva el determinismo sin romper el tipo.
- **Degradar antes que caer** — C30b: un proveedor caído sirve la respuesta estructurada con 200.
  Aquí es *fail-open*, y el peor caso es **exactamente el comportamiento de hoy**.
- **Configuración por parámetro y no leída dentro** — C20, C23, C25 y C30a: el conjunto de evaluación
  barre configuraciones **en un proceso**.

### Breaking changes

**Ninguno en la forma del contrato.** Dos cambios de comportamiento observables, los dos deseados y
con requisito que los declara:

1. **Una consulta libre de fuera de dominio deja de devolver grupos.** Hoy devuelve hasta cinco, y es
   el defecto que el change existe para cerrar.
2. **`intent` gana valores.** Un consumidor que compare contra `unclassified` verá valores nuevos —
   pero `/v1/assist/sale` tiene **cero consumidores**: `IAiGatewayClient` no lo implementa, y C34 aún
   no existe. **Ésta es la razón de abrir C31 antes que C34.**

---

## Definición de Hecho (DoD)

- [x] Enrutador cableado **sólo en M1**, con corte **antes** de `retrieve_products`
- [x] M2 y M3 **no** invocan al clasificador, comprobado por test y no por lectura
- [x] Guardarraíl determinista de M3 sobre cero citas, **sin llamada adicional**
- [x] `clarification_question` resuelta desde catálogo cerrado, con test de determinismo
- [x] Argumentario de M1 con su *payload* propio y su política de lista blanca
- [x] `prompts/assist/v2.md` con test fichero↔constante; **`v1.md` intacto** — *y `v3.md`,
      porque la medición de M1 refutó una sección de tarea de v2; las tres se conservan*
- [x] *Fail-open* como rama con test, nunca un `except` mudo
- [x] Techo de **3** llamadas al proveedor comprobado por introspección
- [x] `ai-service`: `uv run pytest` en verde **sin llamadas reales** a LLM, embeddings ni RDS
- [x] Línea base de la suite comparada **por nombres de test** y no por recuento
- [x] `openapi.json` regenerado y verificado **hoja a hoja**: ningún campo añadido, retirado ni con el tipo cambiado
- [x] Matriz de confusión publicada con las **dos cifras separadas** y el falso positivo sobre `catalog` como cifra propia
- [x] **Cero** consultas `descripcion-sin-anclaje` silenciadas — criterio de veto · *lo cumple
      `gpt-4o` con `router/v3` (48/48 en `catalog`, falso positivo 0,00 %); **`gpt-4o-mini` NO lo
      cumple** y por eso `DEFAULT_ROUTER_MODEL` se movió*
- [x] Deltas de `assist-generation` con `openspec validate --all --strict` en **0 failed**
- [x] Entrada en `DEFERRED_TASKS.md` con los cuatro pasos de despliegue
- [x] Documentación actualizada: épicas, plan de changes, `ai-service/README.md`, `openspec/config.yaml`
- [x] Sin migración de EF Core — este change **no toca datos**
- [x] Sin TODO/FIXME sin tarea de seguimiento

---

## Requisitos No Funcionales

- **Rendimiento.** El enrutador sólo entra en M1, que **no tiene ruta .NET** y por tanto no compite
  por los 5.000 ms de `AssistTimeoutMs`. M2 y M3 **no cambian su latencia en absoluto**: el
  guardarraíl de M3 lee un resultado que ya se calcula. Una consulta rechazada es **más barata** que
  hoy: no recupera, no busca conocimiento y no genera.
- **Coste.** Una llamada de ~30 *tokens* de salida contra los 0,00077 USD/petición que mide C30b. Se
  publica **por separado** para que la comparación siga siendo interpretable.
- **Observabilidad.** `trace_id` propagado; una línea de `stage=router` con etiqueta, motivo,
  latencia, coste y credencial en vigor. **Nunca el texto de la consulta.**
- **Seguridad.** Guardarraíl de entrada + guardarraíl de salida, los dos **deterministas en su
  acción** aunque la clasificación la haga un modelo: la etiqueta se valida contra un conjunto
  cerrado y la acción por etiqueta es código. Es la distinción que el apunte de S16 hace —*«un
  guardrail es código, no una frase en el prompt»*— aplicada donde corresponde.
- **Disponibilidad.** *Fail-open* declarado: sin clasificador, el sistema degrada al comportamiento
  de hoy y no a una caída ni a un rechazo universal.

---

## Preguntas Abiertas

Cinco, todas con **opción por defecto declarada** que se aplicará si no hay respuesta antes del apply.

| # | Pregunta | Opción por defecto | Motivo |
|---|---|---|---|
| 1 | **¿El motivo del rechazo viaja en `warnings[]` o en un campo nuevo?** | **En `warnings[]`**, con códigos nuevos del vocabulario cerrado | Cuesta **cero** movimiento de forma en `openapi.json` y reutiliza la tabla de copy que C36 ya va a escribir. Un campo `refusal_reason` propio sería más explícito pero regeneraría el contrato por una forma, no por una descripción |
| 2 | **¿Se mide la clase `both` o se declara servida-y-no-medida?** | **Se mide**, con los diez casos construidos y **declarando que lo son** | Listarla en la spec sin decir cuál de las dos es lo único insostenible. Sus diez casos llevan **ocho pares de control** contra consultas ya juzgadas, que es más evidencia de la que tendría un conjunto libre del mismo tamaño |
| 3 | **¿El argumentario de M1 entra en este change?** | **Sí**, y es la **línea de corte declarada** si la sesión se desborda | El enrutador y el rechazo son irrenunciables por ficha; M1 no. Si se corta, M1 sigue devolviendo `pitch` vacío —comportamiento actual, con test— y el corte se declara |
| 4 | **¿El clasificador comparte modelo con el argumentario?** | **Mismo `gpt-4o-mini` de partida, variable propia** | Empezar con dos constantes sin medición sería lo que el propio argumento de C30b critica. La variable separada permite barrer el modelo después **sin mover** el del argumentario, cuyo coste y tasa de rechazo están medidos sobre otro |
| 5 | **¿Se persiste la decisión del enrutador para análisis posterior?** | **No**, sólo log | Misma regla que el argumentario de C30b. La excepción declarada sigue siendo el arnés, que guarda sus resultados en `evals/results/` atados a `run_id`, `git_sha` y versión del prompt |

> **Lo que no se decide aquí, a propósito:** los **casos adversarios y de inyección sistemáticos**,
> que son de **C38** (20-25 casos). La mitigación estructural ya está entregada por C30b y **no se
> rehace**; lo que falta es clasificar y rechazar, que es otra cosa. Y la **fidelidad semántica**
> sigue declarada como limitación de la capability, sin juez en el camino del mostrador.

---

## Prioridad / Estimación / Tags

| Atributo | Valor |
|---|---|
| **Prioridad** | **Crítica** — en la lista de «nunca se recortan» del §6 del plan, con motivo propio: *«sin guardrails el agente de C32 no es defendible como sistema en producción»*. Desbloquea **C32**, y con él **C38** y **C39** |
| **Estimación** | _Pendiente_ — a fijar en refinamiento. El esqueleto de la HU tiene 16 entradas; la línea de corte declarada, si se desborda, es el argumentario de M1 |
| **Tags** | `ai-service` · `python` · `fastapi` · `litellm` · `rag` · `guardrails` · `intent-routing` · `safe-completion` · `abstention` · `prompt-versioning` · `structured-output` · `fail-open` · `no-persistence` · `no-migration` · `openapi-descriptions-only` · `C31` · `EP15` |

---

## Enlaces o Referencias

- **HU origen:** [HU-AIENG-031](../../../../Documentos/Historias/AI-Eng/HU-AIENG-031.md)
- **Conjunto de enrutado:** [`ai-service/evals/routing/cases.yaml`](../../../../ai-service/evals/routing/cases.yaml) — 109 casos existentes por referencia + 10 `both` con 8 pares de control
- **Golden set y su criterio:** [`queries.jsonl`](../../../../ai-service/evals/golden/queries.jsonl) · [`criterion.md`](../../../../ai-service/evals/golden/criterion.md)
- **Fixture de fuera de dominio de C23:** [`out-of-domain.yaml`](../../../../data/knowledge/_eval/out-of-domain.yaml)
- **Change predecesor:** [`archive/2026-09-14-add-assist-pitch-generation/`](../../archive/2026-09-14-add-assist-pitch-generation/)
- **Decisiones heredadas:** [c30b-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30b-exploration-decisions.md) (D2 y D8 en particular) · [c30-exploration-decisions.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30-exploration-decisions.md) (D-G)
- **Mediciones que este change consume:** [c30b-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c30b-implementation-measurements.md) (latencia por llamada, tasa de reparación) · [c23-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c23-implementation-measurements.md) (el hueco de 8 milésimas)
- **Diseño:** §11.2, §15.12 y §15.13 — [proyecto-final-diseno-rag-joiabagur.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-diseno-rag-joiabagur.md)
- **Plan de changes:** ficha de C31 en el §3, y la anotación de C34 del 14 sep — [proyecto-final-plan-changes-openspec.md](../../../../Documentos/Proyecto%20Final%20AIEng/proyecto-final-plan-changes-openspec.md)
- **Capability que se modifica:** [`assist-generation`](../../../specs/assist-generation/spec.md)
- **Capabilities consumidas:** [`knowledge-corpus`](../../../specs/knowledge-corpus/spec.md) · [`retrieval-abstention`](../../../specs/retrieval-abstention/spec.md) · [`vector-retrieval`](../../../specs/vector-retrieval/spec.md) · [`ai-service-api-contracts`](../../../specs/ai-service-api-contracts/spec.md)
- **Apunte del máster:** *Un sistema debe saber decir «No lo sé»* — [S16](../../../../Documentos/Sesiones%20Master%20AIEng/S16_Produccion_II/)
- **Procedimientos:** [Procedimiento-TicketsTrabajo.md](../../../../Documentos/Procedimientos/Procedimiento-TicketsTrabajo.md) · [Procedimiento-UserStories.md](../../../../Documentos/Procedimientos/Procedimiento-UserStories.md)

---

## Historial de Cambios

| Fecha | Cambio |
|---|---|
| 2026-09-15 | **Implementado.** La medición **enmienda la opción por defecto nº 4 de este ticket**: «mismo `gpt-4o-mini` de partida» no sobrevive al veto. Sobre los 119 casos, mismo prompt y temperatura 0, `gpt-4o-mini` silencia **3** consultas contestables —falso positivo 6,25 %— y **falla el veto de D12**, mientras `gpt-4o` silencia **0**, acierta **48/48** en `catalog` y pasa. Tres revisiones de prompt llevaron la cifra de quince silenciadas a tres y **no lograron cerrarla**; el modelo la cerró sin tocar una palabra del prompt. Es **D9 vindicado**: la variable separada es lo único que permitió mover el modelo del clasificador sin invalidar las 120 generaciones de C30b. Y **el riesgo mayor de este ticket no se materializó**: la lista blanca numérica de M1 resultó de **~13 numerales y no de cinco** —la recuperación devuelve 15 candidatos, no 5— y la puerta numérica rechazó **cero**; lo que tumbaba el argumentario de M1 era `dangling_citation`, porque la sección de tarea de `catalog` no decía que no hubiera citas. Cifras completas en [c31-implementation-measurements.md](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c31-implementation-measurements.md) |
| 2026-09-14 | Creación del ticket a partir de HU-AIENG-031 y de la exploración de C31. Recoge el hallazgo que reencuadra el change —**«fuera de dominio» son dos conjuntos y la ficha del plan los mezcla**: las 20 consultas de la categoría son oficios vecinos y no preguntas ajenas a la joyería, así que un clasificador de intención puro no movería el 18 de 20 con el que la ficha se justifica—, y las tres decisiones que salen de medir: **el enrutador cuesta una llamada y sólo en M1**, porque una petición reparada ya está en ~4.400 ms de los 5.000 de `AssistTimeoutMs`; **el guardarraíl de M3 es gratis**, porque el umbral `0,51` de C23 ya separa con un hueco de 8 milésimas; y **el conjunto de evaluación ya existía repartido**, con las cuatro consultas `ambigua` declaradas sin juicios desde el 2026-09-11 porque *«la respuesta correcta es una repregunta»* |
