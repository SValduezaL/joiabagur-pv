## Why

C25 corrige la fusión híbrida y, para poder demostrar que la corrige, **conserva la fusión plana
como modo seleccionable**: sin ella la fila `v2-hibrido` de la tabla de ablations deja de ser
reproducible y el change pierde la referencia contra la que se leen todas las demás filas. Es una
decisión de medición, no de producto, y su propio `design.md` la declara temporal.

Una vez la tabla está publicada y la configuración ganadora congelada, ese modo pasa a ser lo
contrario de lo que era: **un camino muerto que nadie ejecuta y que cualquiera puede activar por
error**, con una aritmética que el propio proyecto midió como defectuosa —los 60 documentos
léxicos ganando al mejor candidato vectorial en toda consulta, y el grado 2 cayendo a la posición
33—. Mantener vivo un camino que se demostró roto es la forma más callada de que vuelva.

**El inventario de lo que hay que retirar se comprobó sobre el árbol antes de escribir esto, y
refutó tres afirmaciones de la ficha del plan.** Las decisiones y sus evidencias están en
[`c25bis-exploration-decisions.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/c25bis-exploration-decisions.md):

- Los pesos por lista **no** los consume sólo el modo plano: `weight_typed` y `weight_expanded`
  alimentan también la etapa 1 de la fusión viva. Se retiran igualmente, pero por ser **trampas**
  —la spec ya prohíbe moverlos— y no por estar muertos.
- «La variante de ponderación adaptativa que perdió el barrido» **no existe**: la forma binaria se
  implementó y se retiró dentro de C25, y hay un test que falla si vuelve. La pata se declara
  cumplida y se comprueba, no se ejecuta.
- «Que el arranque falle al nombrar una perilla retirada» **no es alcanzable por el mecanismo que
  la ficha suponía**, y el remedio sería peor que el mal.

## What Changes

- **Se retira la fusión plana de tres listas.** Deja de ser seleccionable y su código desaparece,
  junto con el ajuste `JPV_FUSION_MODE` y la clave `fusion` de las configuraciones de evaluación.
- **Se retiran los tres pesos por lista** (`JPV_RRF_WEIGHT_TYPED`, `_EXPANDED`, `_VECTOR`). La
  etapa 1 de la fusión pasa a componerse con **pesos iguales declarados en el módulo**, que es lo
  que la spec viva ya ordenaba. El resultado es bit-idéntico por construcción: de la etapa 1 sólo
  se reenvía el orden, y con pesos iguales el valor concreto no puede alterarlo.
- **Se conserva el registro de la composición** en la procedencia de cada corrida, poblado desde
  constante de módulo y nunca desde el entorno. *Una perilla es algo que se puede poner; un
  registro es algo que se escribe* — este change retira perillas.
- **Se conserva la demostración del defecto** como test de aritmética pura sobre la primitiva de
  fusión, que ninguna configuración puede seleccionar.
- **BREAKING (interno):** la configuración de evaluación `v2-hibrido` deja de poder ejecutarse. Su
  fichero se conserva en `evals/configs/retired/`, sus cifras y su JSONL por consulta siguen
  versionados, y la fila pasa a ser **histórica y no re-ejecutable**, lo que se declara en lugar de
  disimularse.
- **Se sustituye el requisito de reproducibilidad de la línea base por uno de conservación**: lo
  que el proyecto garantiza a partir de aquí es que las cifras de la línea base están archivadas y
  citables, no que su código siga ejecutable.
- **Se acota a la configuración de evaluación** la obligación de fallar nombrando una perilla
  retirada, porque es ahí donde el daño es de medición —una fila que mide otra cosa— y no de
  creencia. Esa guarda **ya existe** y no se escribe código nuevo para ella.

**No se retira `coverage_rule = "none"`**: es el brazo de control con el que se midió la regla
adaptativa y su marcha atrás declarada, y dos escenarios vivos lo exigen por escrito.

## Capabilities

### New Capabilities

Ninguna. Es un change de limpieza: retira comportamiento y no introduce ninguno. La única pieza de
código que se **escribe** son tests.

### Modified Capabilities

- `hybrid-fusion`:
  - se elimina el requisito que obliga a mantener seleccionable la fusión de una sola etapa;
  - el requisito de pesos y suavizado pasa a prohibir la fusión plana **en el código** y a declarar
    que los pesos internos de la rama léxica no son configuración;
  - el requisito de ponderación por cobertura se corrige en **una cláusula**: apagar la regla es un
    brazo de control de la evaluación, no un ajuste de despliegue, porque `coverage_rule` no es
    campo de `Settings` y el router no lo pasa;
  - el requisito de tests offline sustituye el pin del peso de lista —ya declarado retirado por
    C25— por uno que siga siendo cierto.
- `retrieval-evaluation`:
  - el requisito de que la configuración de la línea base siga siendo seleccionable se sustituye
    por el de que sus cifras y su procedencia queden archivadas y citables, con la pérdida de
    re-ejecución declarada;
  - el requisito de comparabilidad incorpora la composición de las ramas como sexto elemento de la
    procedencia, cuyo único mandato vivía dentro del requisito que se elimina.

## Impact

- **`ai-service/` es el único componente con cambio de código**, y sólo por borrado:
  - `src/jbg_ai/retrieval/orchestrator.py` — desaparece la rama del modo plano, sus parámetros y la
    ramificación de la traza
  - `src/jbg_ai/config/settings.py` — desaparecen el modo de fusión, los tres pesos por lista, su
    validador y sus entradas en el fallback de blancos y en el perfil canónico
  - `src/jbg_ai/evals/{configs,sweep,runner,execute,cli}.py` — desaparecen los campos retirados
  - `src/jbg_ai/evals/provenance.py` — **conserva** el campo y reescribe su justificación
  - `evals/configs/v2-hibrido.yaml` → `evals/configs/retired/v2-hibrido.yaml`
  - `tests/{retrieval,evals,config,api}/` — caen los tests del comportamiento retirado y entran
    cuatro que fijan el borrado
- **Sin migración, sin cambio de contrato, sin reindexar.** `openapi.json` no se mueve.
- **Sin diff en `backend/`, `frontend/`, `terraform/` ni `.github/workflows/`.**
- **Aguas arriba:** depende por completo de C25, **archivado el 2026-09-12**. Prerrequisito duro
  cumplido.
- **Riesgo que el change acepta a propósito:** se pierde la capacidad de re-ejecutar la línea base.
  Es el precio de no dejar vivo un camino medido como defectuoso, y se declara en el README.
- **Riesgo principal, y el único que importa:** que el borrado se lleve algo que estaba en la ruta
  viva. No se mitiga revisando sino midiendo: un diff **línea a línea** del JSONL por consulta
  entre una corrida tomada antes del borrado y otra tomada después, exigiendo **cero diferencias**.
