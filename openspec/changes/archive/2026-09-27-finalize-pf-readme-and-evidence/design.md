## Context

El Proyecto Final está construido y desplegado. Lo que falta es el entregable, y el entregable tiene
una particularidad que gobierna casi todas las decisiones de abajo: **`README.md` no es un README
técnico, es el documento de entrega del máster**, y su estructura la fija una plantilla ajena. Unas
secciones se pueden editar y otras **no**, así que el trabajo se parte en dos: lo que se escribe y lo
que se **reporta con su texto propuesto** para que lo decida quien responde de la entrega.

**Estado de partida, verificado el 2026-09-27.** Despliegue `36344846739` en verde, los diecisiete
pasos, incluida la verificación desde dentro del anfitrión; `IMAGE_TAG = sha-7d3a15ae…`; cuatro
contenedores sanos; `shops_without_scope: 0`. `ai-eng` y `demo` en sincronía de contenido, `demo` en
`7d3a15a`. Cuatro changes archivados el mismo día en la cadena que llega hasta aquí: C39a, C39a-bis,
C43 y el seguimiento del drenaje de arranque.

**Y el problema concreto que este change resuelve, que no es de prosa.** Hoy conviven en la
documentación «40 archivadas», «43 archivadas» y «44 archivadas», y la ficha de C39b dice «74
archivados · 32 del MVP · 41 del PF». Ninguna de las cuatro cifras es la de hoy, y **no se contradicen
por descuido**: cuentan **unidades distintas** —directorios del árbol de archivo unas, fichas del plan
otras— sin decir cuál. Medido contra el disco el 2026-09-27:

```text
directorios en openspec/changes/archive/     78
  con fecha >= 2026-08-03                    46
  anteriores                                 32
slugs distintos (78 dirs, 3 pares duplicados) 75
```

El 32 coincide exactamente con la cifra que la ficha atribuye al MVP, así que **la frontera por fecha
queda validada por ese lado**. Lo que no está escrito es el criterio.

## Goals / Non-Goals

**Goals:**

- Que un evaluador externo pueda **entender, reproducir y probar** el sistema desde el README y el
  paquete de evidencias, sin conocimiento previo del repositorio.
- Que **cada cifra del entregable sea verificable**: el recuento contra `openspec/changes/archive/` en
  un comando, y cada fila de la taxonomía de métodos contra un artefacto con su procedencia.
- Que las **secciones congeladas se respeten**, y que lo que debería cambiar en ellas quede propuesto
  con su texto exacto en lugar de perderse.
- Cerrar las **tres tareas que sobreviven a C38** sin gastar cuota del proveedor.
- Dejar **declaradas con su vía de cierre** las limitaciones que un evaluador va a ver de todos modos.

**Non-Goals:**

- **No se arregla nada de lo que se declara.** Ni `ModelHealthService`, ni la séptima herramienta o el
  campo de nombre en `buscar_catalogo`, ni el comparador de deriva de rama, ni el validador .NET.
- **No se graba el vídeo** —una sesión no puede— ni se da por vista ninguna validación que exija
  navegador.
- **No se crea ni se empuja el *tag***.
- **No se ejecuta ninguna pasada nueva contra el proveedor.** `--rescore` recalcula sobre artefactos
  ya escritos.
- **No se reescribe el registro histórico**: `Documentos/prompts.md`,
  `Documentos/Sesiones Master AIEng/**` y `Documentos/Propuestas/**` no se tocan, y las bitácoras de
  `epicas.md` y del plan **se amplían, no se corrigen hacia atrás**.
- No se toca código ejecutable, ni el contrato `ai-service/openapi.json`, ni Terraform.

## Decisions

### D1 · La unidad de recuento es el directorio, y se declaran **dos** unidades, no una

**Decisión.** El recuento canónico es **un directorio de `openspec/changes/archive/` = un change
archivado**, porque es lo único que cualquiera reproduce en un comando y sin leer el plan. Y como la
documentación existente cuenta además **fichas del plan**, se declaran las dos con su cifra y se dice
explícitamente que no coinciden ni deben coincidir.

| Unidad | Cifra al abrir C39b | Cómo se comprueba |
|---|---:|---|
| Directorios archivados, total | **78** | `ls openspec/changes/archive/ \| wc -l` |
| …del MVP | **33** | los 32 con fecha `< 2026-08-03` más `2026-08-03-barcode-qr-scanning` |
| …del Proyecto Final | **45** | los 46 con fecha `>= 2026-08-03` menos ese |
| Fichas del plan archivadas | **44** | la tabla maestra del §2 del plan |

**La diferencia entre las dos unidades tiene nombre y propios, y decirlo es lo que convierte el criterio
en algo usable.** Cruzados los 46 directorios posteriores al 2026-08-03 contra las 44 filas con slug de
la tabla maestra, **tres directorios no tienen fila**:

| Directorio sin fila en la tabla maestra | Qué es | De qué lado cuenta |
|---|---|---|
| `2026-08-03-barcode-qr-scanning` | escaneo de códigos en el mostrador, capability `barcode-scanning` | **MVP** — D2 |
| `2026-09-26-c40-fix-all-shops-scope-unreachable` | `C40_FIX`, change del PF **fuera de la numeración C** | **PF** — y le falta la fila, que este change añade |
| `2026-09-27-fix-boot-drain-retries-both-drains` | **seguimiento de C43**, sin ficha propia | **PF** — es la diferencia entre 45 y 44 |

Y en el sentido contrario, la única fila de la tabla maestra sin directorio es **C39b**, que es este
change.

**`C40_FIX` no tenía fila en la tabla maestra, y ésa es la mitad del enredo.** Aparecía una sola vez en
el plan, en prosa, lo que obligaba a que todo recuento hecho contra la tabla se quedara corto en uno y se
corrigiera después «sumándole `C40_FIX`». **Añadir su fila entra en este change**, porque poner el plan al
día es exactamente lo que se le pide; lo que **no** se toca son las bitácoras, que son registro fechado.

Con la fila añadida —45 filas con slug— la aritmética queda cerrada y con **un solo nombre** en la
distancia entre las dos unidades: `46 − 1 = 45` directorios del PF, de los que **44** son filas ya
archivadas y **1** es el seguimiento de C43, que no tiene ficha. Los **44** de `epicas.md` son,
exactamente, esas 44 filas. Al archivar C39b: **46 directorios · 45 fichas**.

*Alternativas descartadas.* **(a) Contar sólo fichas**: es la unidad que usa `epicas.md`, pero no se
verifica sin leer el plan, que es precisamente el documento cuya cifra se pone en duda. **(b) Contar
sólo directorios**: dejaría los recuentos de `epicas.md` sin traducción y volvería a divergir en la
siguiente sesión. **(c) Deduplicar los directorios**: los 78 son **75 slugs distintos** —tres pares
duplicados, `add-payment-method-management`, `add-point-of-sale-management` y
`refactor-class-label-to-sku`, **los tres del MVP**— y deduplicar cambiaría la cifra del MVP que ya
está publicada y validada. Se **declaran** los duplicados y no se toca el árbol: reordenar el archivo
histórico para que sume redondo es exactamente lo contrario de lo que este change persigue.

### D2 · `barcode-qr-scanning` se clasifica por **contenido**, no por fecha, y el criterio lo dice

**Decisión.** `2026-08-03-barcode-qr-scanning` cae del lado del **MVP** aunque su fecha sea la del
primer día del Proyecto Final: es el escaneo de códigos en el mostrador, su capability viva es
`barcode-scanning` y **no tiene ficha en el plan del PF**. El criterio publicado es por tanto
**fecha, con una excepción nombrada**, y no fecha a secas.

*Por qué así.* No es una decisión nueva: el plan ya lo escribió —*«las 41 posteriores al 2026-08-03
menos `barcode-qr-scanning`, que es del MVP»*— y `epicas.md` también. Lo que faltaba era elevarlo de
nota al pie a criterio. **Una excepción nombrada es auditable; una regla de fecha que un lector
aplicaría y le daría 46 no lo es.**

*Alternativa descartada.* Fecha pura: daría 32 · 46, contradiría dos documentos y obligaría a explicar
la discrepancia cada vez. Peor por el mismo motivo por el que se elige la otra.

### D3 · La taxonomía de métodos se publica bajo **una sola procedencia**, y es la tabla final de C25

**Decisión.** Las filas de recuperación toman sus cifras de la **tabla final de C25** bajo golden set
`1:198c4af44506` —seis filas, una sola procedencia, `ai-service/evals/results/c25-baselines-2026-09-11.md`—
y la tabla declara esa procedencia en su cabecera. Las cifras de C24 (0,082 · 0,454 · 0,603) se citan
**aparte y como históricas**, con su golden set anterior nombrado.

*Por qué.* La regla de `retrieval-evaluation` es que dos corridas con procedencia distinta se reportan
como no comparables en vez de compararse. Una tabla de ablations que mezcle los dos conjuntos dorados
viola la única regla que hace que la tabla signifique algo.

**Y esto destapa una inconsistencia en una sección congelada, que se reporta y no se arregla.** El
`### 1.2` del README dice que el acierto *«sube de 0,603 a 0,740»*: el 0,603 es `v2-hibrido` bajo el
golden set de **C24** y el 0,740 es `v2b-fusion` bajo el de **C25**, donde `v2-hibrido` mide **0,673**.
El salto real y comparable es **0,673 → 0,740**, y el que C25 publica como decisión es **+0,083** sobre
`v2` en el subconjunto que decide. Va al anexo de secciones congeladas con su texto propuesto.

### D4 · El **éxito de tarea** del agente se define sobre campos que el artefacto ya registra, y se publica «N de 20 con los nombres»

**Decisión.** Éxito de tarea de un escenario de calibración = **su expectativa de herramientas se
cumple** —las que exige, alguna de las que admite, ninguna de las que prohíbe— **y** el escenario no
declara de antemano su propia discrepancia. Se calcula con
`python -m jbg_ai.evals.agent_sweep --rescore`, que **no llama al proveedor ni a la base de datos**, y
se publica como **«17 de 20, y éstos son los tres que no»**, jamás como una tasa porcentual.

*Por qué no un porcentaje.* Porque el **ruido entre pasadas está medido en 2 de 20, un 10 %**: una
*«tasa de éxito del 85 %»* sería una precisión fingida. La forma con los nombres además informa más, y
es lo que ya hizo el informe de C32b.

*Por qué no una definición más ancha* —que incluyera el motivo de parada, el número de grupos o la
presencia de argumentario—. Porque esos campos existen en la fila pero **no tienen expectativa escrita
por escenario**, así que meterlos en el veredicto sería inventar el criterio después de ver los datos.
Se publican **al lado** del veredicto, como contexto, y no dentro de él.

### D5 · El validador .NET pasa a **limitación declarada con vía de cierre**, y su cifra esperada es **cero**

**Decisión.** Se escribe como limitación: la mitad .NET del validador determinista **no está
implementada**, su cifra esperada de rechazos es **cero** porque es **un espejo** de la puerta numérica
que Python ya aplica al mismo texto, y su vía de cierre es la que C38 dejó identificada. Con el dato
que lo hace defendible y no una excusa: de los tres caminos **sólo la ficha de venta comprueba algo en
.NET**, y `placeholder_in_free_query` es causa dura desde C40, con **0 marcadores de 102** medidos en
C42.

*Por qué se declara en vez de implementarse.* Porque un seguro cuya cifra esperada es cero, escrito
después de haberlo medido, es una limitación honesta; implementarlo aquí sería código en un change de
documentación, y sin una sola línea de evidencia de que atrapa algo.

### D6 · El guion del vídeo nombra las piezas **por su referencia**, y explica las dos alertas rojas antes de que aparezcan

**Decisión.** El tramo del agente usa **la referencia** (`SKU759`), nunca el nombre, y el guion dice
por qué. Y antes del tramo del panel de administración, el guion **anticipa las dos alertas rojas** —la
`CRITICAL` de reconocimiento de imagen y lo que se ve en la tarjeta de salud de la IA— para que quien
mire no las lea como averías.

*Por qué.* Está medido sobre el entorno desplegado: por referencia el bucle pivota a `buscar_sustitutos`
en 4 iteraciones; por nombre no pivota —3 iteraciones, 2 herramientas—, porque `buscar_catalogo` no
devuelve el nombre del producto. Un guion que nombrara la pieza por su nombre **enseñaría el fallo en
vez del pilar**. Formato tomado de `c42-manual-check-runbook.md`, que es el precedente del repositorio.

### D7 · Las secciones congeladas se reportan en un **anexo con el texto propuesto**, no se editan

**Decisión.** Un anexo del informe de evidencias enumera, sección por sección, qué está desfasado en
`## 0`, `### 1.1`–`### 1.3`, `## 5` y `## 6`, **con el texto exacto que se propone** y la consecuencia
de no cambiarlo. Nada de eso se aplica en este change.

Tres cosas ya identificadas para ese anexo: el `### 1.2` cierra su párrafo de IA con *«(en
desarrollo)»* y el proyecto está entregado; el mismo párrafo arrastra el salto `0,603 → 0,740` de D3; y
la ficha `## 0` declara una autoría y unas iniciales que **no son las del historial de git**, lo que
choca con el nombre del *tag* acordado en D8.

### D8 · El *tag* y la rama de entrega se **proponen**, con las iniciales del historial

**Decisión.** Se propone `v1.0-final-SVL` y `finalproject-SVL`, sobre el commit de merge de C39b en
`ai-eng`. **No se crean ni se empujan.** La discrepancia contra la ficha §0.1 del README —que nombra a
otra persona— se reporta en el anexo de D7, porque resolverla es editar una sección congelada.

### D9 · El artefacto de `--rescore` se comete donde el comando lo escribe, y su consecuencia se declara

**Decisión.** `c32b-agent-sweep-17fbdd15a18c.rescore.json` queda en
`ai-service/evals/results/`, que es donde `rescore_path()` lo escribe y donde ya vive el de otra
corrida. **Y con ello se declara que mergear este change a `demo` sí dispararía un despliegue**: el
filtro del flujo ignora `openspec/**`, `Documentos/**` y `**/README.md`, pero no `ai-service/**`.

*Por qué no moverlo a `Documentos/`.* Porque el comando lo escribe junto a su origen por diseño —el
nombre deriva del artefacto leído— y separarlos rompería la trazabilidad por el nombre. El coste del
disparo son tres minutos y ninguna imagen cambia de contenido; el filtro es una **lista negra**
precisamente para fallar hacia desplegar de más.

### D10 · La comprobación de la tarjeta de administración se parte en **dos afirmaciones distintas**

**Decisión.** El **dato** que alimenta la tarjeta se afirma comprobado por HTTP desde el anfitrión
—`GET /api/ai/health` con credencial de administrador, más el `shops_without_scope: 0` que `verify.sh`
ya imprimió—. El **renderizado** se declara como observación aportada por el responsable, con su fecha,
y **no se da por visto**: una sesión de Claude Code no tiene navegador.

*Por qué no una sola frase.* Porque «la tarjeta ya no pinta la línea roja» y «el número que la pinta
es cero» no son la misma afirmación, y mezclarlas es exactamente la clase de suposición que este
proyecto ha pagado cuatro veces.

## Risks / Trade-offs

**[El archivado rompe enlaces relativos que el comprobador no ve]** → El comprobador excluye
`openspec/changes/archive/**` por diseño, y un change archivado queda un nivel más profundo: sus
`](../../../…)` pasan a `](../../../../…)`. Es la ceguera que dejó acumular 874 enlaces. **Mitigación:**
revisión manual de los enlaces relativos del change **después** del movimiento, como paso explícito de
la tarea de archivado.

**[El validador de OpenSpec lee sólo la primera línea física de la descripción de un requisito]** → Si
el `SHALL` cae en la segunda línea por un ajuste de ancho, falla con *«must contain SHALL or MUST»*
aunque lo contenga. **Mitigación:** las descripciones de las deltas se escriben en **una sola línea
larga**, sin ajustar a 90 columnas.

**[`openspec validate` a secas no valida nada y sale 1]** → Leer ese 1 como un fallo, o su ausencia
como un pase, cuesta una sesión. **Mitigación:** la única puerta es
`openspec validate --all --strict` con **`0 failed`**, corrida **antes** de archivar, porque un change
puede estar verde mientras las specs vivas en las que sincroniza están rotas.

**[El recuento vuelve a divergir en la siguiente sesión]** → Es lo que ya pasó cuatro veces.
**Mitigación:** el criterio no se escribe sólo en prosa: entra como **requisito de
`pf-delivery-package`**, de modo que la siguiente cifra tenga una regla contra la que medirse en vez de
un precedente que interpretar.

**[Una fila de la taxonomía sin medición se rellena por analogía]** → Sería la forma más fácil de
arruinar la única propiedad que hace útil a esa tabla. **Mitigación:** el requisito la obliga a
declararse **no medida**, y la revisión de la tarea lo comprueba fila a fila contra su artefacto.

**[Mergear a `demo` dispara un despliegue por el artefacto de `--rescore`]** → D9. **Mitigación:**
declarado antes de decidir; el merge a `demo` es opcional y la decisión es de quien responde del
entorno. Si no se quiere el disparo, la salida es no mergear a `demo` o mergear sólo la documentación.

**[Escribir documentos largos con un heredoc]** → Este change escribe varios de cientos de líneas. El
cuerpo del heredoc viaja en la línea de comandos, Windows la corta en 32.767 caracteres y falla con
`ENAMETOOLONG: name too long, uv_spawn`, que suena a problema de ruta y no lo es; y el intento fallido
se paga entero. **Mitigación:** herramienta de escritura de ficheros siempre, heredoc nunca.

## Migration Plan

No hay migración: ni esquema, ni contrato, ni despliegue. La marcha atrás de todo el change es
`git revert` de sus commits, y no deja estado que limpiar.

**Orden de ejecución**, que no es indiferente en un punto: la **frontera contable va primero**, porque
el resumen de fases, la taxonomía y el README citan sus cifras, y medirlas dos veces con criterios
distintos es exactamente el defecto que este change existe para cerrar.

## Open Questions

- **La contraseña de `demo.admin`** no está en el repositorio —se generó fuera del anfitrión y sólo
  viajó el hash—. Sin ella, D10 se resuelve por su mitad declarada. Pedida al responsable.
- **La aprobación del anexo de secciones congeladas** (D7) es de quien responde de la entrega, y puede
  llegar después de archivar este change sin invalidar nada: el anexo es el entregable, no la edición.
- **Si `ai-eng` se merge a `demo`** al cerrar, con la consecuencia de D9 ya declarada. Conviene para que
  la rama no vuelva a derivar —el defecto que C39a destapó, 84 commits y cinco semanas— y es opcional.
