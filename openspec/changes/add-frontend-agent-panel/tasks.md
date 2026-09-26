## 1. Puerta de entrada

- [x] 1.1 **Medir la línea base de las tres suites antes de tocar nada**, sobre el commit de partida, y guardar los **nombres** de los fallos: `dotnet test` (~50 rojos preexistentes), `npm run test` en `frontend/` (~113-114 de 729 en 14 ficheros) y `uv run pytest` en `ai-service/` (verde). **Leer la línea de resumen y no el código de salida**: `vitest` sale 0 al pipearlo, y un `JoiabagurPV.API.exe` vivo hace que `dotnet test` salga 0 con cero tests ejecutados. Validación: la lista de nombres queda escrita y `git status` está limpio
- [x] 1.2 Confirmar sobre el árbol las **cinco afirmaciones que dimensionan el change**, porque si alguna ha cambiado el plan cambia: `IAiGatewayClient` tiene siete métodos y ninguno es el del agente; `assist/v5.md` **no** contiene la tarea del agente; `origin` está en `payload_groups` y no en `response_groups`; la ruta del agente usa `get_service_principal`; y `agent_sweep.py` no tiene contador de marcadores ni registro de antigüedad de proyección. Validación: las cinco comprobadas, o el desvío anotado en el informe de implementación

## 2. Tramo 0 · Instrumentos del arnés — antes de cualquier tarea funcional

- [x] 2.1 Contador de marcadores por fila en `agent_sweep.py`: `{{price}}` y `{{stock}}` sobre el **primer** intento, con el patrón ya escrito en `evals/free_query_gate.py`. Validación: una fila del artefacto lleva los dos recuentos
- [x] 2.2 Agregados de marcadores en el resumen de la pasada: totales y número de generaciones con al menos uno de cada. Validación: el resumen los publica
- [x] 2.3 Antigüedad de la proyección **en la procedencia** de la pasada, leída del punto de control de sincronía y **nunca** de la columna de refresco de la proyección. Validación: la procedencia la lleva
- [x] 2.4 Antigüedad de la proyección **por fila**, con su veredicto de rancidez contra el techo configurado, para que una fila servida sin prefiltro sea identificable después. Validación: las filas la llevan y el veredicto cambia al superar el techo
- [x] 2.5 Tests del arnés: `test_agent_sweep_counts_placeholders` y `test_agent_sweep_records_projection_age`, offline y sin proveedor. Validación: `uv run pytest` en verde
- [x] 2.6 **Precondición de runbook escrita y comprobada**: contenedor `jbg-ai` levantado con el drenaje programado encendido, intervalo por debajo de un cuarto del techo de rancidez, verificado en `GET /health` antes de arrancar la pasada. Validación: la sección `projection` del informe de salud responde y declara la proyección fresca — **escrita, y comprobada en dos mitades porque la precondición tiene dos.** La mitad del planificador queda verificada aquí: la imagen que estaba corriendo era anterior a la sección `projection` y su `/health` no la traía en absoluto, así que se reconstruyó desde HEAD y ahora responde, con `interval_seconds=600` contra `ceiling_seconds=3600` en el log de arranque (600 < 900 = techo/4 ✓). La mitad de la frescura **exige la API .NET sirviendo el *index feed* en `:5056`**, que el drenaje necesita y que no existe hasta el tramo 2: sin ella el drenaje de arranque registra `feed_not_configured` y la proyección sigue rancia. Verificada en **10.1**, que es donde la tarea ya pedía comprobarla otra vez

## 3. Tramo 1 · `ai-service` — el contrato y el prompt

- [x] 3.1 `AgentAssistGroup(AssistGroup)` con `origin` sobre vocabulario cerrado, y `AgentAssistResponse.groups` apuntando a la subclase. **No se toca `AssistGroup`.** Validación: compila y los tests del esquema determinista siguen verdes
- [x] 3.2 `_response_member` y la construcción de `response_groups` (`assist/agent.py`) publican el `origin` que `payload_groups` ya calcula, sin recalcularlo en un segundo sitio. Validación: `test_agent_group_declares_its_origin`
- [x] 3.3 Test de que el modelo compartido **no se ensanchó**: el esquema de la ruta determinista es idéntico campo a campo. Validación: el test falla si `AssistGroup` gana el campo
- [x] 3.4 `prompts/assist/v6.md`: cabecera con su fila en la tabla de versiones, **sección *Sistema* copiada literalmente de `v5`** y **una sola tarea**, la de evidencia del agente, con la prohibición de marcadores y el lenguaje comparativo permitido. `v4.md` y `v5.md` **no se tocan**
- [x] 3.5 `AGENT_PITCH_PROMPT_VERSION` pasa a `assist/v6`. **`PROMPT_VERSION` no se toca.** Validación: la respuesta del agente reporta `v6` y la determinista sigue reportando `v5`
- [x] 3.6 `test_v6_system_section_matches_v5` — la guarda contra la deriva entre los dos ficheros. Validación: el test falla si se edita una de las dos secciones
- [x] 3.7 `test_agent_pitch_carries_no_placeholder` sobre payload sin anclar. Validación: en verde
- [x] 3.8 La ruta del agente pasa de `get_service_principal` a `get_unscoped_principal` (`api/routers/assist.py`). Validación: `test_agent_route_accepts_a_token_without_pos_claim`
- [x] 3.9 Test de que **sustitutos e inventario siguen rechazando** la omisión del punto de venta, y de que con ámbito ausente la etiqueta de disponibilidad reporta «sin ámbito» y **nunca** «sin existencias». Validación: los dos en verde
- [x] 3.10 Regenerar `ai-service/openapi.json` con el one-liner del README y **sustituir el *fixture* del snapshot** declarando la adición permitida, como hizo el change anterior que movió el contrato. Validación: `test_openapi_snapshot_is_stable` en verde y el diff del contrato es **sólo** adición — **hecha, y la validación se cumple con una excepción medida y declarada: el diff NO es sólo adición.** Hoja a hoja con el mismo `_walk` del guardián: **1295 → 1316, 0 eliminadas, 21 añadidas y exactamente 1 cambiada**, que es `$.components.schemas.AgentAssistResponse.properties.groups.items.$ref`, de `AssistGroup` a `AgentAssistGroup`. En el cable sigue siendo adición —la subclase lleva toda propiedad de la compartida con idéntica definición, más `origin`, y el test lo comprueba propiedad por propiedad en vez de fiarse del nombre—, pero el propio guardián declaraba que *«any changed `type` or `$ref` still fails»*, así que se nombra individualmente en `allowed_changes` con su motivo y no se admite por regla: el siguiente `$ref` que se mueva vuelve a fallar. Refutación anotada en el informe

## 4. Tramo 2 · `backend` — el consumidor que no existe

- [ ] 4.1 `SearchOrigin.AssistedAgent = 5` en el dominio, con su comentario de por qué no se pliega en el valor de la ruta generativa. Validación: compila y **no se crea ninguna migración**
- [ ] 4.2 DTOs del agente en la capa de aplicación: petición con la transcripción, y respuesta = la de consulta libre **más** `Partial`, `StopReason`, `Iterations`, `ToolCallsUsed`, `Trace` y `AgentPromptVersion`, con `Origin` en el grupo. Validación: compila
- [ ] 4.3 `AgentTimeoutMs` en las opciones de la pasarela, **por encima del techo de reloj del servicio más margen de red** y con su suelo validado al arranque. Validación: un valor por debajo del suelo falla el arranque con mensaje propio
- [ ] 4.4 Método del agente en `IAiGatewayClient` y su implementación, **sin enviar punto de venta en el cuerpo**. Validación: compila y el test de mapeo cubre los cinco campos nuevos y el `origin`
- [ ] 4.5 Registro del cliente con nombre `ai-agent`: `HttpClient.Timeout` infinito, presupuesto en el *pipeline*, reintento **sólo** para conexión nunca abierta, y cortafuegos sobre condiciones de transporte. Validación: `AgentAssist_UsesItsOwnTimeoutAndNotTheAssistOne`
- [ ] 4.6 El cortafuegos **no cuenta** la degradación servida con 200, con el motivo en el comentario y la aritmética de una petición por minuto. Validación: `AgentAssist_WhenProviderFails_DoesNotOpenTheCircuitOnPartial`
- [ ] 4.7 Métrica y log de `stop_reason=fallo_proveedor`, para que su tasa quede observable sin que el circuito actúe. Validación: el test comprueba que se registra
- [ ] 4.8 `AgentAssistRequestValidator` con FluentValidation: turnos entre 1 y el tope, longitud por turno, **suma sobre todos los turnos** y al menos un turno del operario. Mensajes en es-ES. Validación: `AgentAssist_WhenTranscriptExceedsItsCaps_IsRefusedBeforeTheCall`, que además comprueba que **no se llamó al servicio**
- [ ] 4.9 Servicio de aplicación del agente: llama a la pasarela, hidrata **todos los miembros de todos los grupos** con `AssistedSearchResultDto`, y con ámbito global deja cantidad y existencias como desconocidas en vez de cero. Validación: el test de hidratación cubre un grupo de sustitutos
- [ ] 4.10 Endpoint del agente en la capa de API, autorizado **por la misma regla que la ruta de consulta libre** —los dos roles, ámbito global incluido— y rechazando una tienda no asignada. Validación: los tres tests de autorización, con **cliente fresco de la factoría** para la llamada no autenticada
- [ ] 4.11 `AgentAvailable` en la respuesta de la sonda y en `GetAvailability`, reutilizando el predicado extraído por el fix de C40 y **la cadena de credencial del agente**, sin derivarlo del interruptor de la asistida. Validación: `AgentAvailability_WithoutPointOfSale_ReportsTheAgentSwitch` y el escenario de asistida encendida con agente apagado
- [ ] 4.12 Registro del evento de selección con el quinto origen, conservando el hueco declarado de que la consulta de ámbito global no se registra. Validación: el test del origen
- [ ] 4.13 Comprobar que **no se ha creado ninguna migración** y que `dotnet build` está en 0 errores. Validación: `git status` sobre el árbol de migraciones

## 5. Tramo 3 · `frontend` — tipos y servicio

- [ ] 5.1 Tipos TypeScript del agente: la transcripción, la respuesta con sus cinco campos, el grupo con `origin` y la traza por iteración. Validación: `tsc --noEmit` **filtrado a los ficheros propios**, sin errores nuevos
- [ ] 5.2 `agentAssistService` con el envío de la transcripción y la lectura de la sonda. Validación: test del servicio con `vi.mock`, sin depender de un handler de MSW que no falla si no existe
- [ ] 5.3 Tabla de copy de los **diez** motivos de parada y de los avisos del agente, con **etiqueta neutra** para un valor no reconocido. Validación: el test que recorre los diez valores y el del valor desconocido

## 6. Tramo 3 · `frontend` — la puerta y la ruta

- [ ] 6.1 Ruta `/sales/new/agent` en el enrutado, **cargada de forma diferida** como sus hermanas. Validación: la ruta resuelve y el bundle inicial no crece
- [ ] 6.2 Cuarta tarjeta en la página de entrada de venta, leyendo la sonda **al montar**. Validación: no se gasta cupo ni llamada al proveedor
- [ ] 6.3 Los tres estados de la tarjeta. Validación: `should close the agent card when the probe says the agent is off` y `should open the agent card when the probe cannot answer`
- [ ] 6.4 El motivo mostrado es **el del agente** y no el de la asistida. Validación: el test del escenario asistida-encendida / agente-apagado
- [ ] 6.5 Enlace al panel determinista desde el panel del agente, para que la misma pregunta se pueda comparar. Validación: a ojo en la pantalla

## 7. Tramo 3 · `frontend` — el hilo y el compositor

- [ ] 7.1 El hilo como eje: un bloque de respuesta por turno, anclado, **sólo el último abierto**, los anteriores colapsados a una línea con chips y reabribles. Validación: `should keep each turn's answer anchored to its own turn`
- [ ] 7.2 El turno del asistente que viaja en la petición lleva **el argumentario íntegro**; con argumentario retirado o repregunta, una **línea sintética con los SKU**. Validación: `should send a synthetic assistant turn when the pitch was withheld`
- [ ] 7.3 Contadores del compositor sobre **la transcripción que se va a enviar**, turnos del asistente incluidos. Validación: `should count the assistant turns towards the transcript caps`
- [ ] 7.4 El compositor **se cierra con su motivo** al alcanzar cualquiera de los tres topes, sin enviar la petición. Validación: `should stop the composer with a reason when a cap is reached`
- [ ] 7.5 El ámbito es fijo durante la conversación; cambiarlo **avisa y reinicia el hilo**. Validación: el escenario del reinicio
- [ ] 7.6 La opción de ámbito global se ofrece **con la misma regla que el panel hermano**, y al seleccionarla una línea dice que **el agente deja de ofrecer alternativas**. Validación: `should warn that the every-shop scope stops the agent offering alternatives`
- [ ] 7.7 Estado de espera del envío, con el aviso de duración típica. Validación: a ojo, y el test de que el compositor queda deshabilitado mientras la petición está en vuelo

## 8. Tramo 3 · `frontend` — el bloque de respuesta

- [ ] 8.1 **El bloque sin filas primero**: prosa y citas con cero piezas, sin ninguna de las frases de vacío. Validación: `should render an answer with prose and no pieces`
- [ ] 8.2 La repregunta pinta sólo la pregunta y **devuelve el foco al compositor**. Validación: el test del foco
- [ ] 8.3 «Busqué y no encontré nada» se distingue de las dos anteriores. Validación: el test que separa las tres
- [ ] 8.4 Tira de estado del bloque: motivo de parada traducido, vueltas y herramientas usadas. Validación: el test de los diez motivos a nivel de bloque
- [ ] 8.5 Prosa y citas con `pitch-block` de C36, **sin modificarlo**. Validación: `git status` sobre ese fichero, sin diff
- [ ] 8.6 Filas con `assisted-search-result-row` de C40, **sin modificarlo**, bajo los dos rótulos de procedencia y con las coincidencias primero. Validación: `should label a substitutes group as alternatives` y `git status` sin diff sobre la fila
- [ ] 8.7 Las piezas repetidas entre turnos **no se deduplican**. Validación: el test de la pieza repetida
- [ ] 8.8 La traza, colapsada, como escalera de pasos, **sin argumentos ni contenido de observaciones**. Validación: el test que comprueba que no aparecen
- [ ] 8.9 Cinta de respuesta incompleta que **nombra el presupuesto agotado** y no usa color de alarma. Validación: `should tell a budget-cut answer from a complete one`
- [ ] 8.10 Vender desde el bloque abierto reutiliza el camino de venta existente y registra el quinto origen. Validación: el test de la selección

## 9. Tramo 4 · el coste

- [ ] 9.1 Contador de coste acumulado de la sesión en la barra fija: peticiones, tokens y euros, acumulando el consumo que cada respuesta reporta. Validación: el test de que acumula en vez de sustituir

## 10. Medición — una sola pasada, después del cambio

- [ ] 10.1 Comprobar la precondición de 2.6 **inmediatamente antes** de arrancar, y anotar la antigüedad de partida. Validación: queda escrita en el informe
- [ ] 10.2 Pasada del arnés con el modelo servido, con el PEM del almacén de Windows en `SSL_CERT_FILE`, y artefacto persistido con `run_id`, `git_sha`, `prompt_version` y antigüedad de proyección. Validación: el artefacto existe y su procedencia está completa
- [ ] 10.3 Publicar **`dangling_citation` sobre el agente con `v6`**, incidencia y supervivencia, que es la causa que de verdad retira el argumentario. Validación: la cifra queda en el informe
- [ ] 10.4 Publicar **marcadores con `v6`**, con la línea base **prestada de C40 y declarada como prestada**. Validación: la cifra y la declaración quedan escritas
- [ ] 10.5 Publicar la **tasa de retirada partida por causa**. Validación: en el informe
- [ ] 10.6 Publicar **piezas por respuesta y reparto coincidencias/sustitutos**, esta vez con ámbito aplicado y auditable. Validación: en el informe
- [ ] 10.7 Publicar la **latencia p50/p95 extremo a extremo medida por .NET**. Validación: en el informe
- [ ] 10.8 Publicar el **reparto de los motivos de parada** de la pasada nueva, y contrastarlo con el ya publicado en el informe de exploración v2. Validación: en el informe

## 11. Specs, validación y anotaciones

- [ ] 11.1 Revisar las seis deltas contra lo implementado y corregir cualquier desvío. **Las descripciones de requisito van en una sola línea física**, porque el validador lee sólo la primera. Validación: `openspec validate add-frontend-agent-panel --strict` en verde
- [ ] 11.2 `openspec validate --all --strict` con **`0 failed`**, que es la puerta del proyecto y no la forma de un solo change. Validación: la línea de totales
- [ ] 11.3 Cerrar la entrada de `DEFERRED_TASKS.md` de C32b **por refutación**, escribiendo la aritmética de una petición por minuto y marcándola como cerrada-refutada y no como hecha. Validación: la entrada lo dice
- [ ] 11.4 Anotar `c32b-implementation-measurements.md`: la pasada duró más del doble del techo de rancidez sin drenaje disponible entonces, sus cifras de recuperación quedan como no medidas, y **el pivote se anota explícitamente como superviviente** porque parecería caer con el resto. Validación: la anotación está fechada y firmada como posterior
- [ ] 11.5 Anotar la ficha C42 del plan de changes: el hallazgo del prompt **no gobierna** la línea de corte, y la referencia comparable es la del análogo de C40 y no la de los modos anclados. Validación: las dos frases corregidas

## 12. Cierre

- [ ] 12.1 **Comprobación manual en el entorno levantado**, con los dos roles, recorriendo los tres estados de la puerta, una conversación con pivote, una respuesta sin piezas y el tope del compositor. Es la puerta que cazó el defecto de C40 y que ningún test habría encontrado
- [ ] 12.2 Comparar las tres suites **por nombres** contra la línea base de 1.1, y comprobar que **el área propia está limpia**: cero nombres rojos nuevos en los ficheros que este change toca
- [ ] 12.3 `tsc --noEmit` filtrado a los ficheros propios y `npm run build` en verde — **los dos**, porque el build es verde sobre un error de tipos
- [ ] 12.4 Escribir `Documentos/Proyecto Final AIEng/informes/c42-implementation-measurements.md` con las siete cifras, los desvíos respecto al ticket y lo que se haya refutado
- [ ] 12.5 Actualizar la documentación de contexto que este change deje desfasada, según la tabla de actualización posterior a la implementación
