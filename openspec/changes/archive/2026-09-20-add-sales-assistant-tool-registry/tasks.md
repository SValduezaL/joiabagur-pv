## 1. Puerta de entrada

- [x] 1.1 Medir la línea base de la suite de `ai-service` **por nombres de test** y no por recuento: `git stash push -u`, `uv run pytest`, `git stash pop`, y guardar la lista de nombres para comparar al cierre
- [x] 1.2 Comprobar `openspec validate --all --strict` en verde **antes** de tocar nada, y anotar la cifra de partida
- [x] 1.3 Guardar el hash del `ai-service/openapi.json` actual, para poder demostrar al cierre que no se ha movido

## 2. Vocabularios cerrados

- [x] 2.1 Añadir a `assist/constants.py` el vocabulario de **etiquetas de disponibilidad**: `sin_existencias`, `ultimas_unidades`, `disponible` y `sin_ambito`
- [x] 2.2 Añadir el **mapa desde `QTY_BUCKETS`** a esas etiquetas, con `sin_ambito` reservado para la ausencia de ámbito o de fila y **nunca** derivado de un bucket
- [x] 2.3 Test: **ninguna etiqueta contiene un dígito**, y el mapa cubre el vocabulario completo que el feed puede almacenar
- [x] 2.4 Añadir el vocabulario cerrado de **causas de fallo** de tool, con el mismo patrón que los códigos de aviso de C30a
- [x] 2.5 Añadir la constante congelada con los **seis nombres** de tool

## 3. Lecturas nuevas del puerto de búsqueda

- [x] 3.1 Añadir a `ProductSearchPort` la lectura de **una pieza por SKU**, junto a `source_document()` y `family_roster()`, devolviendo la fila ausente **como valor** y nunca como excepción
- [x] 3.2 Añadir a `ProductSearchPort` la lectura de **disponibilidad de una pieza** en un punto de venta, distinguiendo «no hay fila» de «bucket cero»
- [x] 3.3 Implementar las dos en `retrieval/search.py`, leyendo sólo el esquema `ai` y **sin modificar** ninguna consulta existente
- [x] 3.4 Reutilizar la frescura ya cableada en `retrieval/projection.py` en lugar de recalcularla
- [x] 3.5 **Ampliar los dobles de `ProductSearchPort`** de la suite para que vuelvan a satisfacer el `Protocol`, sin cambiar el comportamiento que ya afirman

## 4. Descriptor y registro

- [x] 4.1 Crear `assist/tools.py` con el **descriptor de tool**: nombre, descripción es-ES, esquema de parámetros y ejecutor
- [x] 4.2 Definir la **observación**: resultado correcto o fallido, contenido acotado y causa de vocabulario cerrado
- [x] 4.3 Construir el **registro** recibiendo los puertos **ya construidos**, sin construir ninguno, como en el resto de `assist/`
- [x] 4.4 Implementar la **validación de argumentos antes de ejecutar**, de modo que un argumento inválido no toque ningún puerto
- [x] 4.5 Exportar el **esquema de *function calling*** de cada tool

## 5. Las seis herramientas

- [x] 5.1 `buscar_catalogo` sobre `retrieve_products()`, con `top_k` **acotado** por mínimo y máximo en el esquema
- [x] 5.2 `buscar_sustitutos` sobre `retrieve_substitutes()`, anclada por SKU
- [x] 5.3 `listar_familia` resolviendo el SKU y llamando a `family_roster()` con su tope
- [x] 5.4 `consultar_conocimiento` sobre `search_knowledge()`, con el filtro de slug de C30a cuando la invocación va anclada a pieza
- [x] 5.5 `consultar_disponibilidad` sobre la lectura de proyección, devolviendo **etiqueta cualitativa + frescura** y `sin_ambito` cuando no hay ámbito o no hay fila
- [x] 5.6 `pedir_aclaracion` recibiendo **eje del enum cerrado** y devolviendo la plantilla que `clarification_for()` resuelve
- [x] 5.7 Acotar la observación de cada tool: **sin *scores* crudos** y **sin identificadores internos**, con la posición como única señal de orden

## 6. Los invariantes, comprobados

- [x] 6.1 Test de **conjunto congelado**: el registro tiene exactamente seis nombres y no aparecen `perfil_punto_venta` ni `buscar_complementarios`
- [x] 6.2 Test de **solo-lectura por introspección**, con sus tres comprobaciones: nombres, métodos de los puertos capturados y verbo de cualquier cliente HTTP
- [x] 6.3 Test de que el invariante **falla al registrar** una tool que capture un puerto con método de escritura, aunque su descriptor declare lo contrario
- [x] 6.4 Test de que **ninguna tool llama a un proveedor de chat**, ejecutando el registro entero sin credencial configurada
- [x] 6.5 Test de que **ningún esquema admite un identificador interno** de producto como parámetro
- [x] 6.6 Test de forma de los **esquemas de *function calling***, sin fichero *snapshot* versionado

## 7. Trazabilidad de los escenarios

- [x] 7.1 Test de **fallo de dependencia como observación**, no como excepción
- [x] 7.2 Test de **SKU desconocido** como observación fallida con su causa
- [x] 7.3 Test de **disponibilidad sin cifras** y con frescura declarada
- [x] 7.4 Test de **«sin ámbito» distinto de «agotado»**, en los dos casos: principal sin punto de venta y pieza sin fila de proyección
- [x] 7.5 Test de **determinismo de la repregunta** y de rechazo del eje fuera del enum
- [x] 7.6 Comprobar que los **nueve escenarios** de [HU-AIENG-032a](../../../../Documentos/Historias/AI-Eng/HU-AIENG-032a.md) tienen test nombrado, y dejar la tabla de trazabilidad en el informe

## 8. Cierre

- [x] 8.1 Comprobar que `ai-service/openapi.json` sigue **byte a byte igual** contra el hash de la tarea 1.3, y que `test_openapi_snapshot_is_stable` está en verde **sin regenerar nada**
- [x] 8.2 Comparar la suite **por nombres** contra la línea base de la tarea 1.1: ningún test desaparece sin sucesor nombrado
- [x] 8.3 `openspec validate --all --strict` en verde, no sólo la forma de un solo change
- [x] 8.4 Ejecutar el comprobador de enlaces de documentación y dejarlo en cero rotos
- [x] 8.5 Escribir el **informe de implementación** en `Documentos/Proyecto Final AIEng/informes/`, con lo que la implementación **refute** de la historia y del ticket
- [x] 8.6 Actualizar la documentación afectada: `Documentos/epicas.md`, plan de changes, `ai-service/README.md`, `ai-service/tests/README.md` y `openspec/config.yaml`
- [x] 8.7 Anotar en la ficha de **C32b** lo que este change le deje escrito, y en `openspec/DEFERRED_TASKS.md` el endpoint .NET de disponibilidad puntual con su motivo
