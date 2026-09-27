## Why

**Es el último change del Proyecto Final, y lo que entrega no es código sino la capacidad de un
evaluador externo de entender, reproducir y probar lo que hay.** Todo lo que se va a evaluar está
construido, desplegado y verificado —el despliegue `36344846739` cerró en verde sus diecisiete
pasos el 2026-09-27, la primera ejecución correcta desde el 22 de septiembre—, y nada de eso está
contado en el entregable: el README raíz sigue describiendo la capa de IA como *«en desarrollo»*, la
frontera entre lo que ya existía y lo que es del Proyecto Final **no está escrita con un criterio**, y
las cifras de cuántos changes se han archivado **se contradicen entre documentos** —«40», «43» y «44»
conviven hoy en `epicas.md` y en el plan—.

**La contradicción no es cosmética: es la única afirmación del entregable que cualquiera puede
comprobar en un comando**, y hoy no cuadra porque los documentos mezclan dos unidades de recuento sin
decir cuál usan. Fijar el criterio, aplicarlo una vez y dejar todas las cifras coherentes vale más que
cualquier párrafo de prosa nueva.

Y hereda tres tareas que **sobreviven a la retirada entera de C38** el 2026-09-27: el éxito de tarea del
agente, su tabla emitida con `--rescore` —que recalcula sin llamar al proveedor, así que no gasta
cuota— y la limitación del validador .NET no implementado con su vía de cierre. Sus datos ya están
medidos y committed; lo que falta es una definición y unos párrafos.

## What Changes

- **La frontera contable queda fijada con su criterio y verificada contra el disco.** Dos unidades
  distintas, declaradas como tales: **78 directorios** en `openspec/changes/archive/` —**33 del MVP**
  (los 32 anteriores al 2026-08-03 más `barcode-qr-scanning`, que es del MVP por contenido) y **45 del
  Proyecto Final**— y **44 fichas del plan**, porque `fix-boot-drain-retries-both-drains` es el
  seguimiento de C43 y no tiene ficha propia. Se declara además que los 78 directorios son **75 slugs
  distintos**: tres pares duplicados, los tres del MVP.
- **Las cifras contradictorias de `epicas.md` y del plan se dejan coherentes**, cada una diciendo qué
  unidad cuenta. No se reescribe el registro histórico de sus bitácoras: se añade la entrada que fija
  el criterio y se corrigen las filas de recuento vigentes.
- **Resumen de fases del Proyecto Final**, con los **seis** changes nacidos de comprobaciones manuales
  y no de ninguna ola —C40, `C40_FIX`, C41, C42, **C43** y el seguimiento del drenaje de arranque—, y
  con el episodio que mejor argumenta el recorrido manual: C43 arregló un falso positivo e **introdujo
  un fallo verdadero**, que el despliegue `36343020047` cazó porque C43 se había obligado a fallar con
  la tabla vacía en vez de pasar en vacío.
- **Taxonomía explícita de métodos de búsqueda**, una fila por método y **cada una con su cifra medida y
  su procedencia** —léxico por nombre, léxico en español, CAG, vectorial, fusión RRF plana, fusión en
  dos etapas por rama, señales de negocio, M1/M2/M3 y agéntico—. Una fila sin medición se declara **no
  medida**, nunca se rellena por analogía.
- **Las tres tareas que sobreviven a C38**: definición escrita del **éxito de tarea** del agente; la
  **tabla por escenario emitida con `agent_sweep --rescore`** sobre el artefacto de C42, con su digest y
  su procedencia; y la **limitación del validador .NET no implementado** con su vía de cierre y su cifra
  esperada de cero.
- **Guion del vídeo de entrega**, con la cuenta de cada tramo, la consulta exacta que se teclea en cada
  superficie y **las dos alertas rojas explicadas de antemano** para que no descoloquen a quien mire.
- **Dos limitaciones declaradas y no arregladas**, cada una con su vía de cierre: la alerta `CRITICAL`
  de reconocimiento de imagen sobre un catálogo con **0 fotos de 1.200 productos** —funcionalidad del
  MVP, no del Proyecto Final— y el **pivote del agente inalcanzable si la pieza se nombra por su
  nombre**, medido sobre el entorno desplegado. Más la **deriva de rama**, que sigue abierta.
- **El README raíz se edita sólo en sus secciones editables.** `## 0`, `### 1.1`–`### 1.3`, `## 5` y
  `## 6` están **CONGELADAS**: lo que debería cambiar en ellas se **reporta con el texto propuesto** y
  espera aprobación, no se edita.
- **Se propone el nombre del *tag* y su commit, y no se crea ni se empuja.** `v1.0-final-SVL` y la rama
  de entrega `finalproject-SVL`, con la discrepancia contra la ficha §0.1 del README reportada.
- **Se absorbe la confirmación de extremo a extremo de C43 y de C39a-bis**, porque se decidió
  explícitamente no abrir un C43-bis: el despliegue en verde con su identificador y la salida de
  `verify.sh`, y el estado de la tarjeta de administración.

**No se toca código de producción.** Ni backend, ni frontend, ni `ai-service` salvo el artefacto de
`--rescore` que el propio comando escribe junto al que lee. Sin migraciones, sin mover
`ai-service/openapi.json`, sin variables de Terraform.

## Capabilities

### New Capabilities

- `pf-delivery-package`: el contrato del entregable del Proyecto Final — qué tiene que poder
  comprobar quien evalúe y con qué criterio: el recuento verificable contra el árbol de archivo, la
  taxonomía de métodos con una cifra medida o la declaración de no medida por fila, las secciones
  congeladas que se reportan en vez de editarse, cada limitación con su vía de cierre, y el guion de
  la demostración con las alertas que no aplican explicadas antes de aparecer.

### Modified Capabilities

- `retrieval-evaluation`: el **éxito de tarea** de los escenarios del agente pasa a ser un veredicto
  definido y publicable — con su forma de publicación fijada («N de 20 y éstos son los que fallan»,
  nunca una tasa porcentual), su recomputación sin proveedor y el ruido entre pasadas declarado junto
  a la cifra.

## Impact

- **README.md raíz** — secciones `### 1.4`, `## 2`, `## 3`, `## 4` y `## Documentación adicional`.
- **`Documentos/Proyecto Final AIEng/`** — el plan de changes (bitácora, tabla de estado y ficha de
  C39b) y un informe nuevo de evidencias del cierre, más el guion del vídeo.
- **`Documentos/epicas.md`** — las filas de recuento y la entrada que fija el criterio.
- **`openspec/DEFERRED_TASKS.md`** — la entrada de la alerta `CRITICAL` pasa a declarada por la vía 1;
  la del pivote por nombre y la de la deriva de rama quedan declaradas con su vía de cierre.
- **`openspec/specs/`** — una capability nueva y una modificada al sincronizar.
- **`ai-service/evals/results/`** — el artefacto de `--rescore`, escrito por el propio comando.
- **Sin impacto en código ejecutable, API, base de datos ni despliegue.**
- **Y un efecto del filtro de rutas que conviene decir antes de que sorprenda:** el flujo de la demo
  ignora `openspec/**`, `Documentos/**` y `**/README.md`, así que un merge de sólo documentación a
  `demo` **no dispara nada** — pero el artefacto de `--rescore` vive bajo `ai-service/`, que **no está
  en la lista negra**, de modo que mergear este change a `demo` **sí redesplegaría**. Es el fallo hacia
  el lado seguro que el propio flujo declara buscar, cuesta tres minutos y no cambia ninguna imagen;
  queda escrito para que la decisión de mergear o no a `demo` se tome sabiéndolo.
