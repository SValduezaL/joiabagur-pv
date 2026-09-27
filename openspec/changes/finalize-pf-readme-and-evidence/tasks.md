## 0. Precondiciones, antes de escribir una línea del entregable

- [x] 0.1 **Medir la frontera contable contra el disco, no contra ningún documento.** `ls openspec/changes/archive/ | wc -l`, el reparto por la fecha `2026-08-03` y los slugs distintos. *Validación: las cuatro cifras —78 directorios, 32 anteriores, 46 posteriores, 75 slugs distintos— escritas en el informe con el comando que las produce.*
- [x] 0.2 **Enumerar los pares de directorios duplicados y a qué lado de la frontera caen.** *Validación: `ls openspec/changes/archive/ | sed 's/^[0-9-]\{11\}//' | sort | uniq -d` da tres slugs y los tres son del MVP; escrito en el informe.*
- [x] 0.3 **Cruzar los 46 directorios posteriores al 2026-08-03 contra las fichas de la tabla maestra del plan**, para que la excepción de `barcode-qr-scanning` y el directorio sin ficha del seguimiento de C43 salgan de una comparación y no de una suposición. *Validación: la lista de las dos discrepancias, nombradas una a una, en el informe.*
- [x] 0.4 Confirmar que el árbol está limpio y que `ai-service/openapi.json` no se ha movido, para poder afirmarlo al cierre. *Validación: `git status --short` vacío salvo los ficheros de este change, y `git diff --stat ai-eng -- ai-service/openapi.json` sin salida.*
- [x] 0.5 Comprobar que **ningún test lee `ai-service/evals/results/`**, de modo que el artefacto de `--rescore` sea inerte para las tres suites y no haga falta medir sus líneas base. *Validación: `grep -rn "evals/results" ai-service/tests/` sin resultados, escrito en el informe. Si diera alguno, medir `uv run pytest` en serie antes y después.*

## 1. La frontera contable, fijada una vez y aplicada a todas las cifras

- [x] 1.1 Escribir el **criterio** en el informe de evidencias: la unidad canónica es el directorio, la segunda unidad es la ficha del plan, la excepción por contenido es `barcode-qr-scanning`, y los **tres directorios sin fila** que el cruce de 0.3 encontró —esa excepción, `C40_FIX` y el seguimiento de C43— explican una a una la distancia entre las dos unidades. *Validación: un lector con el repositorio delante reproduce las cuatro cifras y la reconciliación `46 − 1 = 45 = 43 + C40_FIX + seguimiento` sin leer el plan.*
- [x] 1.1b **Añadir la fila que falta de `C40_FIX` a la tabla maestra del plan.** Es un change del PF archivado, fuera de la numeración C, que hoy aparece una sola vez y en prosa — y es la mitad del enredo de recuentos. *Validación: la fila existe, el cruce de 0.3 vuelve a correrse y deja sólo dos directorios sin fila.*
- [x] 1.2 Aplicarlo en **`Documentos/epicas.md`**: la fila `TOTAL PF` y la nota de recuento vigente pasan a decir su unidad. **Las bitácoras anteriores no se reescriben** —son registro fechado—: se añade la entrada nueva encima. *Validación: `grep -n "archivad" Documentos/epicas.md` y ninguna cifra vigente sin unidad declarada.*
- [x] 1.3 Aplicarlo en **el plan de changes**: la ficha de C39b —que hoy dice «74 archivados · 32 · 41»— y el recuento vigente del §2. Entrada nueva en la bitácora del §0 con la fecha y el criterio. *Validación: la ficha ya no contiene una cifra desfasada y el §2 declara su unidad.*
- [x] 1.4 **Barrer el repositorio buscando cifras de recuento que hayan quedado atrás** en documentos vigentes —no en el registro histórico— y corregirlas o fecharlas. *Validación: la lista de ficheros tocados, con la cifra antigua y la nueva, en el informe.*
- [ ] 1.5 Cerrar el recuento **al archivar**, no antes: con C39b archivado son **46 directorios del PF y 45 fichas**. *Validación: recontado después del `openspec archive` y escrito en la entrada de cierre.*

## 2. Las tres tareas que sobreviven a C38

- [x] 2.1 **Definir el éxito de tarea del agente**, por escrito y antes de mirar ninguna cifra: expectativa de herramientas cumplida —exigidas todas, alguna de las admitidas, ninguna de las prohibidas— y el escenario no declara su propia discrepancia. Decir qué campos quedan **fuera** del veredicto y por qué. *Validación: la definición cabe en un párrafo, no menciona ninguna cifra y coincide con lo que `expectation_verdict` ya computa.*
- [x] 2.2 **Emitir la tabla por escenario con `--rescore`** sobre `ai-service/evals/results/c32b-agent-sweep-17fbdd15a18c.json`, que es la pasada de C42 con `gpt-4o` y `assist/v6`. **No llama al proveedor, así que no gasta cuota.** Una fila por escenario con lo que exige, lo que invocó, el motivo de parada y el veredicto. *Validación: el comando reproduce 17 · 2 · 1 · 0 —correctos, fallos, discrepancia declarada, no comparables— con `C14` y `C17` como fallos y `C19` como declarado; el artefacto `.rescore.json` queda committed y su digest citado en el informe.*
- [x] 2.3 **Declarar el ruido entre pasadas junto a la cifra**, con su procedencia: 2 de 20 al puntuar la pasada de C32b y la de C42 contra el fichero de escenarios de hoy, de los cuales `C05` cambió porque el escenario se corrigió y está documentado en la cabecera del fichero. *Validación: la frase publicada es «17 de 20 y éstos son los tres», y en ningún sitio aparece una tasa porcentual de éxito.*
- [x] 2.4 **Escribir la limitación del validador .NET no implementado** con su vía de cierre y su cifra esperada de cero, y el dato que lo sostiene: es un espejo de la puerta numérica de Python sobre el mismo texto, sólo la ficha de venta comprueba algo en .NET, y `placeholder_in_free_query` es causa dura desde C40 con 0 marcadores de 102 medidos en C42. *Validación: la limitación dice qué no está hecho, por qué su cifra esperada es cero y qué haría falta para cerrarla; sin una línea de código.*
- [x] 2.5 Anotar en `openspec/DEFERRED_TASKS.md` la entrada del validador .NET, para que sobreviva al archivado de este change. *Validación: la entrada existe y nombra C38 como su origen y C39b como quien la declara.*

## 3. El resumen de fases del Proyecto Final

- [x] 3.1 Escribir el resumen por fases/olas contra la tabla maestra del plan, no de memoria. *Validación: cada fase nombra los changes que la componen y todos aparecen en la tabla maestra.*
- [x] 3.2 Contar aparte los **seis changes nacidos de comprobaciones manuales y no de ninguna ola** —C40, `C40_FIX`, C41, C42, C43 y el seguimiento del drenaje de arranque— y decir qué destapó cada uno. *Validación: los seis, con su hallazgo en una línea, y la cifra 6 coherente con el resto del documento.*
- [x] 3.3 Escribir el episodio de C43 como el mejor ejemplo del proyecto de una condición de verificación ganándose el sueldo: arregló un falso positivo, **introdujo un fallo verdadero**, y lo cazó el despliegue `36343020047` **porque C43 se había obligado a fallar con la tabla vacía** en vez de pasar en vacío. *Validación: el relato cita los dos identificadores de despliegue y la condición (a), y no atribuye el hallazgo a ninguna suite.*
- [x] 3.4 Declarar las **fichas que no son archivadas y no deben sumarse como tales**: retirada C38, anulados C19, C29, C33, C35 y C37, cortado C27. *Validación: los siete nombrados con su estado y su fecha.*

## 4. La taxonomía de métodos de búsqueda

- [x] 4.1 Construir la tabla con **una fila por método** —léxico por nombre, léxico en español, CAG, vectorial, fusión RRF plana, fusión en dos etapas por rama, señales de negocio, M1, M2, M3 y agéntico— y una columna de procedencia. *Validación: once filas, ninguna sin columna de procedencia.*
- [x] 4.2 **Tomar las cifras de recuperación de una sola procedencia**: la tabla final de C25 bajo golden set `1:198c4af44506`, declarada en la cabecera. *Validación: cada cifra se reencuentra en `ai-service/evals/results/c25-baselines-2026-09-11.md`.*
- [x] 4.3 Publicar las cifras de C24 **aparte y como históricas**, con su golden set anterior nombrado, sin mezclarlas en ninguna comparación. *Validación: el documento no contiene ningún delta que reste una cifra de C24 a una de C25.*
- [x] 4.4 **Declarar no medida toda fila que no tenga artefacto**, en vez de rellenarla por analogía. *Validación: revisión fila a fila; cada celda con cifra tiene artefacto y cada celda sin artefacto dice «no medido».*
- [x] 4.5 Añadir la **sección del reranking descartado con su protocolo y su número**: el protocolo es ejecutable —un `configs/v2-rerank.yaml` más una corrida— y el número que lo hace decidible está medido, **1 consulta de 48** con un grado 2 en el top-20 y fuera del top-5 sobre la configuración viva. *Validación: la sección cita el informe de C24 y la división que sostiene el «no».*
- [x] 4.6 Añadir la **progresión de prompts con su impacto medido**: `enrichment/v1 → v2` de FIX1, `piece_type` de ocho a doce términos, con los recuentos sobre `ai.product_document` y la nota honesta de que el criterio léxico de la ficha **ya se cumplía antes** y por eso no se usa como prueba. *Validación: los recuentos coinciden con el informe de FIX1 y la nota está escrita.*
- [x] 4.7 Añadir las **métricas de revisión humana** de C28: tasa de corrección **20,9 %** ponderada y **32,1 s** de media por ítem sobre 204 perfiles cronometrados, publicadas **partidas** —10,4 % de campos sensibles contra 42,3 % de etiquetas comerciales— porque no miden lo mismo. *Validación: las tres cifras y la descomposición, con la advertencia de que el 42,3 % es subjetivo por declaración del revisor.*
- [x] 4.8 Añadir la fila de **CAG con su coste y su techo**: 17.583 tokens para 1.168 productos, `$0,002673` por consulta, Recall@5 **0,133** sobre las 12 consultas sin anclaje, `NINGUNO` en 10 de esas 12, y el techo en 6.643 productos. Declarada **fechada y no reproducible bit a bit**, porque llama a un modelo. *Validación: las cifras se reencuentran en el informe de C24 y en el de línea base de C25.*

## 5. El README raíz — sólo las secciones editables

- [x] 5.1 **`### 1.4. Instrucciones de instalación`**: arranque local de los tres servicios con `docker compose`, requisitos, puertos y el usuario de desarrollo. *Validación: los puertos y los nombres de fichero citados existen en el repositorio.*
- [x] 5.2 **`## 2. Arquitectura del sistema`** (2.1–2.6): el diagrama gana el servicio de IA con sus dos índices vectoriales, y 2.2–2.6 se ponen al día con la frontera .NET/Python **justificada** —.NET es la autoridad de precio, existencias y permisos; Python hace búsqueda vectorial y generación— y con los cinco pilares del PF nombrados: CAG, RAG, agentes, evaluación y despliegue. *Validación: cada componente citado existe, y `## Índice` sigue cuadrando con los encabezados.*
- [x] 5.3 **`## 3. Modelo de datos`**: las entidades del PF que faltan, cuadrando con `Documentos/modelo-de-datos.md`. *Validación: ninguna entidad citada en el README falta en ese documento, y al revés para las del esquema `ai`.*
- [x] 5.4 **`## 4. Especificación de la API`**: revisar que las cuatro rutas de IA documentadas sigan describiendo lo que sirve el código, e incluir la del *feed* de tiendas de C43 si procede. *Validación: cada ruta citada existe en un controlador, verificado por `grep`.*
- [x] 5.5 **`## Documentación adicional`**: enlazar el informe de evidencias, el guion del vídeo y el *runbook* de la demo. *Validación: los enlaces relativos resuelven desde la raíz del repositorio.*
- [x] 5.6 Si algún encabezado cambia, **actualizar el `## Índice`** de la cabecera en el mismo commit. *Validación: cada entrada del índice resuelve a un encabezado existente.*
- [x] 5.7 **No tocar** `## 0`, `### 1.1`, `### 1.2`, `### 1.3`, `## 5` ni `## 6`. *Validación: `git diff README.md` no muestra ni una línea dentro de esas secciones.*

## 6. El anexo de secciones congeladas

- [x] 6.1 Enumerar, sección por sección, qué está desfasado en las congeladas, **con el texto exacto propuesto** y la consecuencia de dejarlo como está. *Validación: cada entrada trae un bloque de texto listo para pegar.*
- [x] 6.2 Incluir las tres ya identificadas: el `### 1.2` cierra su párrafo de IA con «(en desarrollo)» y el proyecto está entregado; ese mismo párrafo arrastra el salto **0,603 → 0,740**, que mezcla dos conjuntos dorados y cuyo salto comparable es **0,673 → 0,740**; y la ficha `## 0` declara una autoría cuyas iniciales **no son las del historial de git**, lo que choca con el nombre del *tag* propuesto. *Validación: las tres, con su texto propuesto y su medición al lado.*
- [x] 6.3 Dejar constancia de lo que **ya es correcto y no hay que rehacer**: la línea 35 describe correctamente las cuatro cuentas de demostración —describía un mundo que no existía hasta que C39a-bis lo aprovisionó—, y los `admin` / `Admin123!` de la línea 95 y de `backend/README.md` son del apartado de **desarrollo local**, donde siguen siendo verdad. *Validación: comprobado contra el fichero y contra el sembrador, y escrito para que nadie lo «arregle».*

## 7. El guion del vídeo de entrega

- [x] 7.1 Escribir el guion de 2-3 minutos con **un tramo por pilar**, y por tramo: la cuenta con la que se entra, la consulta exacta que se teclea y qué debe salir. Formato tomado de `c42-manual-check-runbook.md`. *Validación: ningún tramo sin cuenta, sin consulta literal y sin criterio de éxito.*
- [x] 7.2 Repartir los tramos por las cuentas cuyo surtido los hace observables: `op-ciutadella` el camino feliz, `op-fornells` abstención y sustitutos, `op-aeroport` el pivote del agente, `demo.admin` la tarjeta de salud. *Validación: cada comportamiento cae en la cuenta que puede alcanzarlo, comprobado contra el §5.8 del *runbook*.*
- [x] 7.3 **Nombrar la pieza por su referencia** en el tramo del agente, y decir por qué: por referencia pivota —4 iteraciones con `buscar_sustitutos`—, por nombre no —3 iteraciones, 2 herramientas, ningún pivote—. *Validación: el guion no contiene ninguna consulta que nombre una pieza por su nombre en ese tramo.*
- [x] 7.4 **Explicar las dos alertas rojas antes del tramo que las muestra.** *Validación: las dos explicaciones aparecen en el guion antes del tramo del panel de administración.*
- [x] 7.5 Declarar en el guion que la **grabación no es parte de este change** y qué queda por hacer para producirla. *Validación: escrito, y sin ninguna afirmación que dé el vídeo por grabado.*

## 8. Las limitaciones declaradas, que se declaran y no se arreglan

- [x] 8.1 **La alerta `CRITICAL` de reconocimiento de imagen**: 0 fotos de 1.200 productos, funcionalidad **del MVP y no del Proyecto Final**, y por tanto una tarjeta que no aplica. Se cierra por la **vía 1** de su entrada diferida —declararlo en el guion de la demo—, y el arreglo de fondo (distinguir «no alimentado» de «sin entrenar» en `ModelHealthService`) **no es de este change**. *Validación: la entrada de `DEFERRED_TASKS.md` marca la vía 1 como ejecutada por C39b y las vías 2 y 3 como abiertas; el guion lo explica.*
- [x] 8.2 **El pivote inalcanzable por nombre**, con su medición sobre el entorno desplegado y su arreglo costado. *Validación: la limitación cita las dos columnas del experimento y nombra `buscar_catalogo` como la causa estructural.*
- [x] 8.3 **La deriva de rama**, que sigue abierta: nada compara lo desplegado con la rama que debería servirse, aunque los dos datos existen —`IMAGE_TAG` en SSM y `git rev-parse origin/demo`—. *Validación: declarada con los dos datos nombrados y con lo que costaría cerrarla.*
- [x] 8.4 Recorrer `openspec/DEFERRED_TASKS.md` y dejar **cada entrada abierta que un evaluador pueda encontrarse** con su vía de cierre escrita. *Validación: la lista de entradas revisadas, con las que quedan abiertas y por qué, en el informe.*
- [x] 8.5 Escribir la **declaración de lo que queda para fase posterior** —packing list, liquidación con descuentos, upsell/downsell, políticas de inventario configurables y el agente de inventario completo, cuyo diseño está íntegro en el §10 del documento hermano— y los **próximos pasos** en orden de madurez. *Validación: coincide con el §785 y el §802 del documento de diseño, sin añadir nada que allí no esté.*
- [x] 8.6 Escribir las **tres declaraciones** que son puntos a favor si están y huecos si faltan: **un solo agente**, con el diseño del de inventario adjunto como próximo paso; **golden set sin acuerdo entre anotadores**, por etiquetador único; y **proyecto individual**, no en pareja. *Validación: las tres, escritas como limitación y no como omisión.*

## 9. La confirmación de extremo a extremo que este change absorbe

- [x] 9.1 Recoger el **despliegue en verde** `36344846739` con su `IMAGE_TAG`, sus diecisiete pasos y la salida literal de `verify.sh`. *Validación: la salida pegada incluye las cinco líneas `OK`, la `NOTE` de `{'catalog': 66}` y el `Post-deployment verification passed.`.*
- [x] 9.2 **El dato de la tarjeta de administración**, comprobado por HTTP desde el anfitrión con credencial de administrador. **Requiere la contraseña de `demo.admin`, que no está en el repositorio.** *Validación: el `shops_without_scope` leído, con la fecha y el medio; y si la credencial no llega, la tarea se cierra declarando la mitad que sí está verificada.*
- [x] 9.3 **El renderizado de la tarjeta declarado, no dado por visto**: observación aportada por el responsable, con su fecha, y separada del dato de 9.2. *Validación: las dos afirmaciones son dos frases distintas y ninguna dice «comprobado» de lo que no se vio.*
- [x] 9.4 Anotar que la confirmación de C43 se recoge aquí **porque se decidió no abrir un C43-bis**. *Validación: escrito, con la referencia a la entrada del plan que lo decide.*

## 10. El *tag* y la rama de entrega

- [x] 10.1 **Proponer** `v1.0-final-SVL` y `finalproject-SVL`, con el commit al que apuntarían —el merge de C39b en `ai-eng`— y **preguntar antes de crear o empujar nada**. *Validación: el informe contiene la propuesta y el repositorio **no** contiene el tag: `git tag --list "v1.0-final*"` vacío.*
- [x] 10.2 Reportar la discrepancia de iniciales contra la ficha §0.1 sin editarla. *Validación: está en el anexo de 6.2 y `git diff README.md` no toca la sección `## 0`.*

## 11. El informe de evidencias

- [x] 11.1 Escribir `Documentos/Proyecto Final AIEng/informes/c39b-implementation-measurements.md` con todo lo anterior: la frontera y su criterio, el resumen de fases, la taxonomía, las tres tareas de C38, las limitaciones, la confirmación del despliegue y el anexo de secciones congeladas. **Con la herramienta de escritura de ficheros, nunca con un heredoc.** *Validación: el fichero existe, sus enlaces relativos resuelven y ninguna cifra carece de procedencia.*
- [x] 11.2 Escribir el guion del vídeo como documento aparte en la misma carpeta. *Validación: el fichero existe y el README lo enlaza.*
- [x] 11.3 Declarar en el informe **todo lo que este change NO ha verificado**, nombre a nombre. *Validación: una sección explícita, y ninguna afirmación del resto del informe la contradice.*

## 12. Cierre

- [ ] 12.1 `openspec validate --all --strict`, que es **la única puerta que valida algo**, y debe reportar **`0 failed`**. `openspec validate` a secas no valida nada y sale 1. *Validación: la línea de resumen, pegada en el informe.*
- [ ] 12.2 Sincronizar las deltas en las specs vivas: `pf-delivery-package` nace como capability nueva —con su `# … Specification`, su `## Purpose` y su `## Requirements`— y `retrieval-evaluation` gana su requisito. **Sintaxis de delta en una spec viva es un sync roto.** *Validación: `--all --strict` verde después del sync y ninguna spec viva contiene `## ADDED Requirements`.*
- [ ] 12.3 Archivar el change y **revisar a mano los enlaces relativos** del árbol archivado, que quedan un nivel más profundo y que el comprobador **no ve** porque excluye `openspec/changes/archive/**`. *Validación: cada `](../…)` del change archivado resuelve.*
- [ ] 12.4 Poner al día `epicas.md` y el plan con el cierre: **la cola del Proyecto Final queda vacía**. *Validación: los dos documentos lo dicen con la unidad declarada, y el recuento de 1.5 aplicado.*
- [ ] 12.5 Preguntar si se merge `ai-eng` a `demo`, **declarando antes que este change sí dispararía un despliegue** por el artefacto de `--rescore` bajo `ai-service/`. *Validación: la pregunta hecha y la consecuencia escrita; nada empujado sin respuesta.*
