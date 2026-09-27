## Context

C25 dejó vivas piezas que sólo existen para que su propia medición fuese posible. La ficha del plan
las enumeraba de memoria; **este change las comprobó por búsqueda antes de escribir una línea**, y
el inventario real no es el supuesto:

| Andamio supuesto | Lo que dice el árbol | Qué se hace |
|---|---|---|
| Fusión plana de tres listas, seleccionable | Correcto: `JPV_FUSION_MODE=flat` la selecciona y la rama existe en `_fuse_branches` | Se retira |
| Pesos por lista, «que sólo consume el modo plano» | **Falso.** `weight_typed` y `weight_expanded` son también los `internal_weights` de la etapa 1 **viva**. Sólo `weight_vector` es exclusivo del modo plano | Se retiran **los tres**, pero por ser trampas y no por estar muertos |
| Dos formas de ponderación adaptativa | **No existen.** `COVERAGE_RULES == ("continuous", "none")`; la binaria con `alfa` se implementó y se retiró dentro de C25 | Nada que retirar. Se comprueba y se declara |

El defecto que la fusión plana encarna está medido y publicado: con los pesos de C21, un documento
léxico en el rango 60 puntúa `1,00/120 = 0,008333` y el mejor documento que sólo vio la rama
vectorial puntúa `0,33/61 = 0,005410`, así que **los 60 documentos léxicos ganan al #1 vectorial en
toda consulta**; y el grado 2 que la vectorial pone en el primer puesto cae a la posición 33 en tres
consultas del golden set. Dejar seleccionable un camino con esa propiedad es dejar abierta la puerta
por la que el defecto vuelve.

**Restricción que gobierna este change:** no puede abrirse antes de que C25 esté archivado y su
tabla publicada. **Cumplido el 2026-09-12.**

Las evidencias completas, con los lectores verificados de cada elemento y las cuatro
contradicciones internas encontradas, están en
[`c25bis-exploration-decisions.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25bis-exploration-decisions.md).

## Goals / Non-Goals

**Goals:**

- Que no quede seleccionable ningún camino de fusión que la medición haya descartado.
- Que no quede ninguna perilla que la norma prohíba mover — porque ésa no es una perilla muerta,
  es una trampa.
- Que la composición realmente en vigor siga **registrada** aunque ya no se pueda **elegir**.
- Que la pérdida de re-ejecución de la línea base quede **declarada**, no descubierta más tarde.
- Que el proyecto conserve, ejecutable, **por qué** se llegó hasta aquí, sin conservar el camino.

**Non-Goals:**

- Cambiar ningún valor calibrado por C25. Este change **no re-mide nada** y no mueve ningún peso:
  si al retirar código cambiase una cifra, sería un defecto del borrado y no un resultado.
- Retirar las perillas que C25 deja **calibrables a propósito** —los pesos de negocio, el umbral,
  `k`, la profundidad—: siguen teniendo lector y siguen siendo el mecanismo de decisión de C26 y
  C38.
- Retirar `coverage_rule = "none"`. Es el brazo de control y la marcha atrás declarada de la regla
  adaptativa, y dos escenarios vivos lo exigen.
- Añadir una fila de control para esa regla. El hueco se declara; no se cierra.
- Añadir una lista negra de nombres de variables retiradas validada al arranque.
- Retirar el golden set, `v2b-fusion`, `v3-senales`, o cualquier artefacto de evaluación distinto de
  la fila que deja de ser ejecutable.
- Tocar `backend/`, `frontend/`, `terraform/` o `.github/workflows/`.

## Decisions

### D-A · La línea base se conserva como artefacto citable, no como código ejecutable

Al retirar el modo plano, `v2-hibrido` deja de ser una fila. Se conservan sus cifras y su
procedencia —el informe en `ai-service/evals/results/`, el JSONL por consulta y, por D-E, su propio
YAML— y se **declara** que la fila es histórica y no re-ejecutable.

*Razón:* la garantía que importa es poder **citar** de dónde viene una comparación, y eso lo da la
procedencia archivada. Poder re-ejecutarla sería mejor, pero su precio es mantener vivo un camino
medido como roto, y ese precio es más alto.

*Y hay una razón de coherencia normativa:* la spec viva ya resolvió el caso simétrico en
`Deepening the golden set re-runs every row`, que ordena que las cifras de la versión anterior *«se
citen como históricas y no como filas comparables»* y que **toda fila de una tabla comparta una
misma tupla de procedencia**. Una fila leída de artefacto metería dos tuplas en una tabla.

*Alternativas descartadas:* **(a)** mantener el modo plano sólo para el arnés —es lo que este change
existe para evitar, y un modo que sólo usan los tests deja de estar ejercitado por la ruta viva y se
pudre sin que nadie lo note—. **(b)** Congelar la fila leyéndola del JSONL dentro del informe
—código nuevo en un change de limpieza, y procedencia mixta en una misma tabla—. **(c)**
Reimplementar el pipeline dentro del arnés —prohibido por el propio requisito modificado y por la
doctrina de C24: *«un arnés que reimplementa el pipeline mide la copia»*.

*Consecuencia normativa:* el requisito de `retrieval-evaluation` que obliga a que la configuración
de la línea base siga siendo seleccionable se sustituye por uno de conservación y declaración. **No
hace falta delta sobre `Deepening the golden set…`**: una configuración retirada deja de ser fila, y
el requisito habla de las filas que existen.

### D-B · El selector muere, el registro vive

`JPV_FUSION_MODE` desaparece como ajuste y como clave de configuración de evaluación.
`Provenance.fusion_mode` **se conserva**, poblado desde constante de módulo.

*Razón:* son dos cosas distintas que el mismo nombre confundía. El docstring de `provenance.py`
dice que el modo pasó a ser el sexto elemento *«porque C25 lo hizo uno»*, cuando la fusión plana se
volvió seleccionable; retirar el selector devuelve esa lógica al `git_sha`. Pero el registro sigue
haciendo dos trabajos que nada más hace: `differences()` marca **no comparable** una corrida
archivada bajo `flat` frente a una nueva bajo la composición viva, y la columna `fusión` del informe
distingue las filas que fusionan de las cuatro que no.

*Y cierra el único agujero que habría justificado una lista negra de perillas retiradas (D-G):* si
alguien exportase la variable retirada creyendo reproducir la línea base, la fila resultante se
imprimiría marcada con la composición **real** y no con la que quiso elegir.

*Principio que queda escrito:* **una perilla es algo que se puede poner; un registro es algo que se
escribe.** Este change retira perillas. De él salen también D-E —`POOLED` es quién *entra* al
próximo pooling, `pooled_in` es el registro de quién *entró*— y D-G.

*Consecuencia normativa:* el requisito vivo `A run is comparable to another only when its provenance
matches` enumera **cinco** elementos y no nombra el modo; su único mandato vivía dentro del requisito
que este change elimina. Conservar el registro exige añadirlo a ese requisito.

### D-C · Mueren los tres pesos por lista; la etapa 1 queda con pesos iguales no configurables

*Argumento de identidad, que es lo que permite exigir cifras idénticas:* en la etapa 1 ambas listas
llevan el mismo peso, RRF escala linealmente con el peso, y `_fuse_two_stage` sólo reenvía a la
etapa 2 el **orden** de la etapa 1 (`lexical_ids`) — la magnitud se descarta. Con pesos iguales,
cualquier valor produce el mismo orden y el mismo resultado final. El borrado es bit-idéntico **por
construcción**, no por comprobación afortunada.

*Por qué no bastaba con retirar sólo `weight_vector`, que es el único realmente muerto:* la spec viva
ya ordena que los pesos internos *«MUST be equal and MUST NOT be swept»*. Una perilla que existe y
que la norma prohíbe mover **no es una perilla muerta: es una trampa**, porque ponerla desigual viola
un requisito sin que nada lo detecte. Conservarla con un validador que la obligue a ser igual sería
una perilla de un solo valor.

*Consecuencia normativa:* `Fusion tests run offline and pin the measured defaults` exige hoy un test
que falle *«si el peso vectorial por defecto sube hasta o por encima del léxico»*. Ese peso es el de
lista y desaparece — y el requisito que lo fijaba **ya estaba declarado retirado** por
`Weights and smoothing…` desde C25, así que la spec viva se contradecía a sí misma antes de este
change. Se sustituye el pin por uno cierto.

### D-D · `none` se queda y la pata de la variante perdedora se declara cumplida

No se retira nada de la regla de cobertura. La pata *«retirar la variante adaptativa que perdió el
barrido»* se declara **cumplida por C25** y se comprueba en vez de ejecutarse.

*Evidencia de que está cumplida:* `COVERAGE_RULES == ("continuous", "none")`, `rule="binary"` levanta
`ValueError`, y el test que lo fija declara que la binaria *«was implemented and withdrawn… it lost
on cost rather than on result»*.

*Evidencia de que `none` está mandatado:* dos escenarios del propio requisito —*«switching the rule
off is available as a control and a rollback»* y *«a comparison between two forms of the scaling is
not accepted in place of that control»*—. El segundo es una guarda anti-patrón que C25 escribió
contra sí mismo, y retirarla sería exactamente el error que este change dice evitar.

*Y una cláusula que sí se corrige:* esa spec promete que apagar la regla es un *rollback*.
Comprobado: `coverage_rule` **no es campo de `Settings`** y el router no lo pasa, así que en
producción la regla está fijada por código. La marcha atrás es cierta del arnés y falsa del
servicio, y la delta lo dice.

*Alternativa descartada: retirar `none`.* Rompería dos escenarios vivos, dejaría el +0,128 sin
control con el que re-confirmarse cuando el golden set crezca, y `coverage_rule` ni siquiera es una
perilla de entorno: no pertenece a la clase de riesgo que este change existe para eliminar.

*Hueco declarado y no cerrado:* ninguna configuración superviviente fija `coverage_rule: none`, así
que el brazo de control sólo es alcanzable a mano.

### D-E · El fichero de la línea base se conserva en `evals/configs/retired/`

`ai-service/evals/configs/v2-hibrido.yaml` se mueve a `evals/configs/retired/v2-hibrido.yaml` con
cabecera que lo declara histórico. `v2-hibrido` sale de `ABLATION_ORDER` y de `POOLED`.

*Razón, y es estructural y no convencional:* `CONFIG_DIR.glob("*.yaml")` **no es recursivo**, así
que el subdirectorio es inalcanzable por el cargador **por cómo está escrito el cargador**. Y
`load_config("v2-hibrido")` falla nombrando la ruta y listando las disponibles.

*Por qué no se borra:* el informe publicado lleva etiqueta, columna de fusión, procedencia y cifras
— **no lleva los valores de las perillas**. El YAML es el único artefacto donde vive la configuración
misma, y el proyecto ya rechazó por escrito el argumento de «está en git»: *«evidencia que vive sólo
en una base de datos es evidencia que nadie diffea»*.

*Por qué no se renombra en su sitio:* dejaría un fichero muerto conviviendo con los vivos, que es la
misma forma que este change combate, y su inercia dependería del patrón `*.yaml` en vez de de la
estructura del directorio.

*Lo que no diferencia a las tres opciones, y conviene no confundir con un coste:* cualquiera de
ellas obliga a tocar `ABLATION_ORDER`, `POOLED` y los cuatro tests que lo cargan de disco, porque
`test_every_configuration_loads_and_the_table_is_in_order` exige igualdad **exacta**.

*Regalo colateral:* el artefacto archivado se convierte en la prueba ejecutable de que la retirada
está completa, usando la guarda de claves desconocidas que **ya existe** en `configs.py`.

### D-F · Se conserva la demostración del defecto, sin que sea activable

El testigo del defecto deja de ser **un camino** y pasa a ser **un fósil en un test**: aritmética
pura sobre `fuse()` y `RankedList`, sin `_fuse_branches`, sin `Settings` y sin modo, con los pesos de
C21 como **literales locales comentados como históricos**.

*Razón:* el proyecto pierde la capacidad de ejecutar el camino roto y conserva la de demostrar por
qué estaba roto. Que los pesos dejen de leerse de `FUSION_DEFAULTS` es justo lo que los convierte en
fósil en vez de en configuración.

*Qué muere con ello:* los cuatro sitios que hoy usan `fusion="flat"` como testigo diferencial, entre
ellos el que comprueba que el modo plano **entierra** el mejor acierto vectorial.

### D-G · La obligación de fallar ruidosamente se acota a la configuración de evaluación

No se añade lista negra de nombres retirados validada contra el entorno. El escenario se corrige
para que la obligación caiga donde el daño es de medición y no de creencia.

*Evidencia decisiva:* el commit `27dfe66` de C25 —*«Retira la rotacion del orden»*, 11-09— eliminó
`JPV_BUSINESS_WEIGHT_ROTATION`, que tenía campo, default, fallback de cadena en blanco **y su propio
`field_validator`**, y no añadió guarda alguna. Exigírsela ahora a `JPV_FUSION_MODE` sería una
asimetría sin fundamento, o obligaría a este change a enumerar también aquélla.

*La asimetría que decide:* una perilla **retirada** e ignorada produce el comportamiento **bueno**;
lo silencioso no es un defecto de comportamiento sino de creencia. Una clave mal escrita en un YAML
de evaluación, en cambio, **publica una fila que mide otra cosa** — y esa guarda ya está
implementada y ya tiene test.

*El mecanismo, además, no es el que la ficha suponía:* con `extra="ignore"` y `pydantic-settings`,
pasar a `extra="forbid"` **no** caza variables de entorno —ni se recogen— y sólo caza claves del
fichero `.env`, donde reventaría con cualquier clave ajena. Cumplirlo exigiría un validador que
barra `os.environ`, con tres costes: falsifica el *«retira comportamiento y no introduce ninguno»*,
convierte un residuo inofensivo en un **fallo de arranque** —peor radio de daño que el defecto que
previene—, y se pudre en cuanto alguien retire otra perilla sin ampliarlo.

*Consistencia interna, obligatoria:* la nota `Migration` del requisito eliminado y el apartado
*Rollback* de este documento decían *«el arranque debe fallar nombrándola»*. **Cambian en el mismo
commit**, o la delta se contradice a sí misma.

### D-I · Desviación declarada: tres configuraciones congeladas hubo que editarlas

**Este change cruzó uno de sus propios *non-goals***, y se declara en vez de disimularse, como C22
declaró la revisión de Alembic que su ficha decía no necesitar.

El *non-goal* dice: *«Retirar el golden set, `v2b-fusion`, `v3-senales`, o cualquier artefacto de
evaluación distinto de la fila que deja de ser ejecutable»*. No se retiró ninguno, pero **se
editaron tres**: `v1-vectorial.yaml` perdió los tres pesos por lista, y `v2b-fusion.yaml` y
`v3-senales.yaml` perdieron `fusion: branch`.

*Por qué era inevitable:* la guarda de claves desconocidas de `configs.py` —que existe desde C24 y
que este mismo change apoya como mecanismo del escenario de fallo ruidoso— **rechaza cualquier
fichero que nombre una clave retirada**. Dejar las claves habría dejado las tres configuraciones
sin poder cargarse, que es precisamente el defecto que la guarda existe para señalar.

*Por qué no mueve ninguna cifra, y está medido:* las tres claves eran **inertes**. `v1-vectorial`
corre con `mode: vector`, es decir con la rama léxica apagada, así que las listas que esos pesos
gobernaban no llegaban a existir; y `branch` era el valor vivo por defecto, de modo que fijarlo
sólo repetía lo que ya ocurría. El diff de las 315 filas por consulta lo confirma después del
hecho: idénticas.

*Qué se hizo con ello:* cada uno de los tres ficheros lleva escrito, en su cabecera, por qué la
retirada no lo mueve. Lo que ninguno pierde es una sola clave de las que deciden su orden.

### D-H · El orden es medir, borrar, verificar y sólo entonces documentar

Primero la corrida de referencia **antes de tocar nada**; después el borrado con los tests en verde;
después la re-ejecución y el diff; y sólo con las cifras idénticas delante se actualizan el README y
los documentos de contexto. Escribir antes la declaración de que la línea base es histórica sería
declararlo sin saber si el borrado fue limpio.

## Risks / Trade-offs

- **El borrado se lleva algo que estaba en la ruta viva** → Es el riesgo principal y el único que
  importa. Mitigación: **diff línea a línea** del JSONL por consulta —`ranked` completo y todas las
  métricas— entre la corrida previa y la posterior, exigiendo **cero diferencias**; y `uv run
  pytest` antes y después comparando **nombres** de tests que fallan y no su recuento, como manda el
  `CLAUDE.md`.
- **Tomar la tabla publicada como referencia** → Sería un error: el informe de C25 declara que su
  corrida se tomó `+dirty`, con código que aterrizó en el commit siguiente, así que compararse
  contra ella compararía dos árboles. Mitigación: la referencia es la corrida previa de esta rama.
- **El arnés declarará las dos corridas no comparables** → Y tiene razón: `comparable_with` incluye
  `git_sha`. Mitigación: excepción **declarada por escrito y acotada** — `git_sha` es el único
  elemento que puede diferir; si difiere cualquier otro, la verificación es **inválida**, no floja.
- **Se pierde la capacidad de re-ejecutar la línea base** → Aceptado a propósito y declarado en el
  README (D-A). Lo que se conserva es la procedencia citable y, por D-E, la configuración misma.
- **Retirar una perilla que sí tenía lector** → Ocurrió: dos de los tres pesos por lista lo tenían.
  Mitigación: el inventario se comprobó por búsqueda y no por memoria, y la retirada se justificó de
  nuevo sobre lo comprobado (D-C).
- **Las capturas de barrido anteriores dejan de cargarse** al perder `FusionFingerprint` cuatro
  campos → Aceptado: no están versionadas y la fase de captura se vuelve a ejecutar cuando haga
  falta. Se declara.
- **Tentación de «aprovechar» para ajustar algo** → Un change de limpieza que mueve una cifra deja
  de ser verificable. Mitigación: cualquier delta es un fallo, no un resultado.

## Migration Plan

1. Verificar que C25 está **archivado** y su tabla publicada. **Cumplido el 2026-09-12.**
2. Comprobar que la huella del conjunto indexado sigue siendo la de la tabla publicada. Si se ha
   movido, **parar**: sin corrida previa comparable no hay verificación posible.
3. Tomar la **corrida de referencia previa al borrado** y versionarla.
4. Retirar el modo plano, los pesos por lista y el fichero de la línea base.
5. `uv run pytest` en verde; caen los tests del comportamiento retirado y **ninguno más**.
6. Re-ejecutar y **diferenciar los dos JSONL línea a línea**: cero diferencias.
7. Actualizar README, informe de C25, plan, épicas y el informe de implementación.

**Rollback:** es un borrado sin migración ni cambio de contrato, así que revertir es revertir el
commit. Nada en los datos ni en el esquema cambia. **Ninguna configuración de despliegue depende de
las perillas retiradas** —se comprueba, y hoy no existe ninguna que las nombre—; si alguna las
trajese, no tendría efecto, y lo que la corrida compuso realmente se lee de su procedencia registrada
y no del entorno que alguien pretendió (D-G).

## Open Questions

| # | Abierta | Opción por defecto |
|---|---|---|
| 1 | Al desaparecer el modo de los ajustes, ¿dónde viven las constantes de composición que la procedencia registra? | En `evals/provenance.py`, junto a `NO_FUSION`, que ya está ahí |
| 2 | ¿Se conserva la columna `fusión` del informe de ablations? | **Sí**: sigue distinguiendo las filas que fusionan de las cuatro que no |
| 3 | ¿`_fusion_mode_of` desaparece o se simplifica? | Se **simplifica**: decide entre la composición viva y `NO_FUSION` según el tipo de configuración, que es una decisión real y no una lectura de ajuste |
| 4 | ¿Se añade una fila de control con `coverage_rule: none`? | **No.** El change no tiene autoridad sobre la tabla; el hueco se declara |
| 5 | ¿Qué pasa si la huella del índice se hubiese movido? | **Parar.** Sin verificación, este change no puede afirmar lo único que afirma |

*Las preguntas 1 y 2 de la versión anterior de este documento están **cerradas**: no hay variante
adaptativa que retirar (D-D), y el inventario de perillas se comprobó y está en el `## Context`.*
