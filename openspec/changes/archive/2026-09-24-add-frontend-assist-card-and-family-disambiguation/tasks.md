## 1. Puerta de entrada

- [x] 1.1 Medir la **línea base de la suite de frontend por nombres de test**: `git stash push -u`, `npm run test` en `frontend/`, `git stash pop`, y guardar el **conjunto de nombres** que fallan. Viene roja de fábrica; el número no sirve de nada
- [x] 1.2 Comprobar que `npm run build` está en verde antes de tocar nada
- [x] 1.3 Anotar el `sha256` de `ai-service/openapi.json` para comprobar al final que no se ha movido
- [x] 1.4 `openspec validate --all --strict` en verde antes de empezar

## 2. Contrato y servicio

- [x] 2.1 Crear `frontend/src/types/sales-assist.types.ts` fiel a `SalesAssistDtos.cs`: `SalesAssistResponse`, `SalesAssistGroup`, `SalesAssistMember`, `SalesAssistCitation`, `SubstitutesResponse`, `SubstituteResult`, y los dos enumerados **en snake_case** tal como .NET los serializa
- [x] 2.2 Crear `frontend/src/services/sales-assist.service.ts` con las dos llamadas y desenlaces tipados que **nunca lanzan**, siguiendo `ai-search.service.ts`, con miembros propios para 429 y para 404
- [x] 2.3 Tests del servicio: cada código de estado del backend cae en su miembro, y ninguna llamada propaga una excepción

## 3. Tabla de copia

- [x] 3.1 Crear `frontend/src/lib/assist-copy.ts` con funciones exportadas: los **cinco** códigos de aviso alcanzables, la **etiqueta neutra**, los **cinco mensajes** de los seis estados del argumentario y los **cuatro** desenlaces de sustitutos
- [x] 3.2 Añadir las **cinco preguntas sugeridas** del corpus: mojar la pieza, piel sensible, limpieza en casa, regalo sin saber la talla, playa o piscina
- [x] 3.3 Tests directos del módulo, incluido `should label a router refusal code with the neutral fallback` para los dos códigos inalcanzables

## 4. Componentes de la ficha

- [x] 4.1 Cabecera de la pieza: foto, nombre, SKU, precio en es-ES/EUR, unidades en esa tienda, y **«Sin talla declarada» como atributo junto al SKU**, nunca como alerta
- [x] 4.2 Bloque de avisos con los cuatro códigos restantes y la etiqueta neutra para cualquier otro
- [x] 4.3 Bloque de argumentario: los seis estados pintados como cinco mensajes, con los tres retenidos terminando en una acción, y `ai_unavailable` separado de `not_generated`
- [x] 4.4 Citas plegadas por defecto con documento, sección y fragmento; `claimScope` distinguido con insignia y frase propias; **ocultas cuando el argumentario no se entrega**
- [x] 4.5 Bloque de familia: una fila y un botón por miembro, **sin preselección**, con etiqueta de variante destacada, precio, unidades, marca de agotado, marca del ancla, y degradación al SKU cuando falta la etiqueta
- [x] 4.6 Caja de pregunta con las cinco sugeridas que rellenan y envían en un solo acto, y el límite de **500 caracteres** comprobado antes de enviar
- [x] 4.7 Bloque de sustitutos con los cuatro desenlaces, el orden recibido y la **página corta declarada y no rellenada**

## 5. Página y ruta

- [x] 5.1 Añadir `SALES.ASSIST(productId)` a `routes.tsx` y registrar la ruta con **carga perezosa** en `app-routing.tsx`
- [x] 5.2 Crear `frontend/src/pages/sales/assist.tsx`: punto de venta por estado de navegación, **selector de respaldo por rol** cuando se abre en frío y **ninguna petición hasta elegir uno**
- [x] 5.3 Implementar el **episodio por visita** (referencia inicializada de forma perezosa) y la **guarda de respuestas fuera de orden**, copiados de `assisted.tsx`
- [x] 5.4 Disparar **una** petición de asistencia al entrar, **sin reintento automático**, con estado de carga desde el primer instante y un botón de reintento explícito
- [x] 5.5 La pregunta como **segunda** petición explícita, sin conservarse entre visitas y sin aparecer en la dirección de la página ni en el estado del enrutador
- [x] 5.6 Pedir sustitutos **sólo** si el miembro anclado no tiene existencias **y** la IA estaba disponible; si el card degradó, explicar por qué no se ofrecen

## 6. Las tres entradas y la salida

- [x] 6.1 Extender `assisted-search-result-row.tsx` con la acción secundaria hacia la ficha, **sin tocar la firma de `onSelect`** y **sin reportar selección de telemetría**
- [x] 6.2 Añadir el botón hacia la ficha en `new.tsx`, junto al producto seleccionado, y comprobar que esa página acepta un `productId` distinto al que ya tenía
- [x] 6.3 Añadir el salto a la ficha en `scan.tsx`, tras resolver el código
- [x] 6.4 Implementar el traspaso a la venta por estado de navegación con el **miembro elegido**, nunca con el ancla cuando se eligió otro

## 7. Tests

- [x] 7.1 Montar el entorno de test del card envolviendo `AuthProvider` —y `CartProvider` donde toque—, con los servicios sustituidos por `vi.mock`, sobre la plantilla de `pages/sales/__tests__/cart.test.tsx`
- [x] 7.2 `should issue exactly one assist request per visit` y `should not retry a failed assist request`
- [x] 7.3 `should require variant confirmation when family has multiple members`, `should preselect no member when the group has several` y `should carry the chosen member to the manual sale page`
- [x] 7.4 `should degrade a member row with no variant label to its sku`
- [x] 7.5 `should render citations when pitch has sources`, `should mark an establishment claim differently from a general one` y `should hide citations when the argument was withheld`
- [x] 7.6 `should fall back to a neutral label for an unknown warning code` y `should render size label missing as a piece attribute and not as a warning`
- [x] 7.7 `should tell a degraded card from one whose argument was not generated` y `should say what to do next when the argument is withheld`
- [x] 7.8 `should show substitutes block when selected product is out of stock`, `should not request substitutes when the card is degraded`, `should tell the four substitute outcomes apart` y `should declare a short substitutes page instead of padding it`
- [x] 7.9 `should fill and send in one act from a suggested question`, `should reject a question over five hundred characters before sending` y `should never put the question in the url`
- [x] 7.10 `should distinguish a rate limited response from an unavailable service` y el 404 como «esta tienda no lleva la pieza»
- [x] 7.11 `should reach the card from the result row, the sale page and the scan page`, y que el panel de C16 conserva su selección para venta intacta
- [x] 7.12 **Mutaciones de control**: romper a mano la preselección, la etiqueta neutra y el disparador de sustitutos, comprobar que fallan exactamente los tests que deben, y revertir

## 8. Cierre

- [x] 8.1 Comparar la suite contra la línea base **por nombres**, no por número
- [x] 8.2 `npm run build` en verde; la salida de `tsc --noEmit` filtrada a los ficheros propios
- [x] 8.3 Comprobar el `sha256` de `ai-service/openapi.json` y que `git status` no muestra cambios en `backend/` ni en `ai-service/`
- [x] 8.4 `openspec validate --all --strict` → **0 failed**
- [x] 8.5 Comprobación con datos reales: una ficha real con argumentario resuelto, una pregunta con citas y un grupo de familia con varias variantes — **ejecutada el 2026-09-24 en el entorno local**, no en el demo de ECR: mismo código, misma base con el mundo de C10 y el índice de C13, y el mismo `jbg-ai` con credencial real y `STUB_MODE=false`. Los tres criterios y sus cifras, en el §7 del informe de implementación
- [x] 8.6 Escribir el informe de implementación en `Documentos/Proyecto Final AIEng/informes/c36-implementation-measurements.md`

## 9. Documentación

- [x] 9.1 `Documentos/epicas.md`: EP15 al cierre de C36 y el recuento movido al archivarlo
- [x] 9.2 Plan de changes: ficha C36 corregida en el sitio con lo que la exploración refutó
- [x] 9.3 Diseño RAG: **§15.12 reescrita** (dos de los tres modos llegan al operario), **§15.13 ampliada** (el rechazo cortés sigue sin pantalla) y **limitación nueva** de telemetría de la ficha
- [x] 9.4 `frontend/README.md`: la ruta nueva, sus tres entradas y el módulo de copia
- [x] 9.5 `openspec/DEFERRED_TASKS.md`: abrir las dos entradas nuevas —servir la ficha estructural sin generar, y telemetría de la ficha— y anotar que la del corpus que no viaja en la imagen ahora pesa más
