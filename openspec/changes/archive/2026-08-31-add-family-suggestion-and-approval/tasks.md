> **Guardarraíl.** Este change **no abre migración** de EF Core ni de Alembic, y **no toca `frontend/`**. Si alguna tarea parece pedir una columna, es señal de que se está adelantando trabajo de C18b — pararse y releer el `design.md`, decisión 3.
>
> **Orden que no es negociable:** el grupo 7 (lote + reconciliación) mueve el 30 % del corpus. Nada de C20, C21 ni C24 debe medirse antes de que ese grupo esté cerrado.

## 1. Línea base y medición previa

- [x] 1.1 Levantar el Postgres local y registrar la línea base: recuento de `ProductFamilies`, de `ProductFamilyMembers` y de `ai.product_document` con `family_id` no nulo. Verificación: los tres son 0.
- [x] 1.2 **Medir la tasa de nulos de `piece_type`** en `ai.product_document` y anotarla. Confirma D9 y dimensiona su efecto; **no** cambia la regla, que ya está fijada.
- [x] 1.3 Medir el baseline de la suite antes de tocar nada (`git stash push -u` → `dotnet test` y `uv run pytest` → `git stash pop`) y guardar los **nombres** de los tests en rojo, no el recuento. La suite de backend arrastra ~53 fallos preexistentes y la de frontend ~118.

## 2. Librería de agrupación en `ai-service`

- [x] 2.1 Crear el paquete `ai-service/src/jbg_ai/families/` y su espejo `ai-service/tests/families/`, siguiendo la convención de `ai-service/tests/README.md`.
- [x] 2.2 **Reutilizar** los vocabularios cerrados de `jbg_ai/enrichment/vocabularies.yaml` (C09) para materiales, talla y tipo de pieza. **No se declara ninguna lista nueva**: Python es el original y `frontend/src/lib/materials-vocabulary.ts` es el espejo, como su propia cabecera dice. D12 revisada el 2026-08-31.
- [x] 2.3 Declarar **únicamente el rango canónico de tallas**, que es lo que el vocabulario no puede tener: su lista está agrupada por escala, no ordenada por magnitud. Un token de talla que el rango no nombre ordena al final, nunca lanza.
- [x] 2.4 Implementar la **normalización de raíz** sobre `enrichment.vocab.fold` —que ya hace casefold, `NFD` sin diacríticos, puntuación a espacio y espacios colapsados— añadiendo sólo la retirada del token de talla. **En cualquier posición, no sólo al final**: `Anillo lapislázuli mediano oro` esconde la talla detrás de un material y `Anillo mini conchiglie` nunca llegaría a `Anillo conchiglie`. Los términos de varias palabras (`extra mini`, `baño de oro`) se emparejan enteros y con preferencia sobre cualquier palabra suelta que contengan.
- [x] 2.5 Implementar la **agrupación por raíz** con la puerta de `piece_type`, tratando el nulo como valor propio que no agrupa con nadie.
- [x] 2.6 Implementar la **fusión por material** entre grupos cuyas raíces difieran en exactamente un token, **sin** retirar material de la raíz.
- [x] 2.7 Implementar la **guarda de raíz degenerada** (raíz igual al tipo de pieza pelado, o de menos de dos tokens) y devolver los grupos rechazados **con su motivo**, no descartarlos en silencio.
- [x] 2.8 Implementar el **veto relativo por embedding** que **marca y no elimina**, con su margen leído de `pydantic-settings` (D10 revisada el 2026-08-31). La prueba es **entre grupos**: se marca al miembro que tiene un producto de **otra familia propuesta** más cerca que su propio peor hermano, por más del margen. La versión inicial usaba `mediana − k·MAD` contra el centroide, que es una prueba *dentro* del grupo y disparaba al 16,9 % marcando al miembro menos típico de cada clúster — algo que todo clúster tiene por definición.
- [x] 2.9 Implementar la **detección de `variant_label`** como el fragmento retirado verbatim normalizado, admitiendo la etiqueta nula para la pieza base y la etiqueta compuesta en las familias de dos ejes.
- [x] 2.10 Implementar el cálculo de `position` por rango canónico, **sin** persistir el rango como etiqueta.
- [x] 2.11 Implementar la **exclusión de productos ya asignados** a una familia, que es lo que hace converger la repetición.
- [x] 2.12 Puerto de lectura sobre `ai.product_document`. **No** se lee ni se escribe `public` por SQL, **no** se llama al proveedor de embeddings y **no** se modifica `indexing/embeddings.py`.

## 3. Tests de la librería

- [x] 3.1 `test_groups_products_differing_only_in_size_suffix` y `test_inconsistent_capitalisation_does_not_split_family` (el caso real `Anillo erizo de mar` / `Anillo Erizo de mar XL`).
- [x] 3.2 `test_does_not_group_across_piece_types` y `test_null_piece_type_groups_with_nobody`.
- [x] 3.3 `test_merges_groups_differing_in_one_material_token` y `test_material_in_root_is_not_stripped` (el caso `Anillo plata S/M/L/XL`, que debe seguir siendo familia).
- [x] 3.4 `test_degenerate_root_is_rejected_and_reported` (los casos `Encargos` y `Arreglos`).
- [x] 3.5 `test_veto_flags_member_without_removing_it` y `test_no_global_threshold_decides_membership`.
- [x] 3.6 `test_veto_parameters_come_from_configuration` — falla si `k` o el número de vecinos están incrustados en el código.
- [x] 3.6b `test_family_vocabulary_reuses_enrichment_terms` — falla si alguien vuelve a declarar una lista de materiales o de tallas dentro de `families/`, que es la regresión que D12 revisada existe para impedir.
- [x] 3.7 `test_variant_label_is_verbatim_not_translated` (`mini` no se convierte en `XS`) y `test_base_member_has_null_variant_label`.
- [x] 3.8 `test_members_ordered_by_canonical_rank_not_alphabetically` y `test_two_axis_family_labels_stay_unique`.
- [x] 3.9 `test_suggestion_is_deterministic_for_same_catalog_and_config` y `test_suggestion_calls_no_provider`.
- [x] 3.10 Tests de **propiedades** sobre los invariantes del agrupador —pertenencia única, orden sin huecos, etiquetas únicas por familia— y no sobre valores concretos.

## 4. Ruta HTTP en `jbg-ai`

- [x] 4.1 Esquemas Pydantic en `api/schemas/families.py`: cuerpo de acotación opcional, propuestas con miembros ordenados y etiquetas anulables, marcas de revisión con su distancia, y grupos rechazados con su motivo.
- [x] 4.2 Router `api/routers/families.py` con `POST /v1/families/suggest`, exigiendo el token de servicio como el resto de `/v1`.
- [x] 4.3 Fixture determinista en `stubs/` para `STUB_MODE`, que valide contra el modelo declarado y **no** abra conexión a base de datos.
- [x] 4.4 `503` nombrado cuando falten los ajustes necesarios con `STUB_MODE=false`, siguiendo el patrón de `retrieval.py`.
- [x] 4.5 Tests de la ruta en `tests/api/`: modelo declarado, token exigido, stub sin base de datos, y `503` por configuración ausente.

## 5. Contrato congelado

- [x] 5.1 **Regenerar `ai-service/openapi.json`** con la orden del README del `ai-service`. Verificación: el fichero contiene **nueve** rutas `/v1`.
- [x] 5.2 Actualizar `test_openapi_snapshot_is_stable` y dejarlo en verde contra el árbol de trabajo. Registrar en el `proposal` que el movimiento de frontera es deliberado.

## 6. Camino .NET

- [x] 6.1 DTOs de petición y respuesta en `JoiabagurPV.Application/DTOs/Ai/`, con nombres `snake_case` en el cable y `variant_label` anulable.
- [x] 6.2 `IAiGatewayClient.SuggestFamiliesAsync` y su implementación en `AiGatewayClient`, **sin truncar ni reordenar** ninguna de las dos listas.
- [x] 6.3 Traducción de fallos a los errores tipados ya existentes: `501` → no implementado, timeout/circuito/5xx → indisponible, credenciales → configuración. **Sin fallback degradado.**
- [x] 6.4 Validadores FluentValidation del cuerpo de `apply`, invocados **explícitamente** en la acción: este proyecto registra validadores sin pipeline automático.
- [x] 6.5 `POST /api/ai/catalog/family-suggestions` en `AiCatalogController` — sólo administradores, **sin escribir nada**.
- [x] 6.6 `POST /api/ai/catalog/family-suggestions/apply` — persiste el subconjunto recibido **a través de `ProductFamilyService`**, con `Origin = AiApproved`, aprobador e instante.
- [x] 6.7 Propagación del conflicto **por familia**, con el detalle de qué familia retiene cada producto en disputa y sin dejar ninguna a medias. **200 y no 409**: el lote es de ~156 familias y un producto en disputa no puede costarle al administrador las otras 155. La familia contestada se salta entera y se nombra en la respuesta; el 409 sigue siendo la respuesta de los endpoints manuales de C07, que crean una familia y sólo una.

## 7. Tests .NET

- [x] 7.1 `SuggestFamilies_ReturnsProposals_WithoutWritingAnything` — ni familia, ni miembro, ni `Product.UpdatedAt`. Exige **sustituir el gateway por un doble** que devuelva propuestas sobre los productos del fixture: contra el gateway real la llamada acaba en 503 y las afirmaciones no prueban nada, porque una petición que no devolvió propuesta tampoco pudo persistirla.
- [x] 7.2 `ApplyFamilySuggestions_RecordsAiApprovedOriginWithApprover` y `CreateFamily_StillRecordsManualOrigin`.
- [x] 7.3 `ApplyFamilySuggestions_MakesMembersVisibleToAnIncrementalPull` — se afirma **sobre el feed**, no sobre `Product.UpdatedAt`. Crear una familia mueve el watermark por `Family.UpdatedAt`, así que el timestamp del producto era el detalle de implementación y el feed es el requisito. El primer intento afirmaba el timestamp y falló, con razón.
- [x] 7.4 `ApplyFamilySuggestions_ReportsConflict_WithoutPartialFamily`.
- [x] 7.5 `ApplyFamilySuggestions_AppliedTwice_WritesNothingTheSecondTime` — no reescribe filas ni toca `UpdatedAt`. **No es el cortocircuito de lista idéntica de C07**, que era el nombre con el que salió esta tarea: la segunda aprobación toma el camino del conflicto, porque los productos ya pertenecen a la familia que creó la primera. No se escribe nada igualmente, y reportarlo es mejor que absorberlo — aprobar dos veces el mismo lote es un error que conviene ver.
- [x] 7.6 `SuggestFamilies_ReturnsForbidden_ForOperator` y `SuggestFamilies_ReturnsUnauthorized_ForAnonymous`. **Pedir un cliente nuevo a la factoría**: el `HttpClient` compartido conserva las cookies de cada login y no es anónimo.
- [x] 7.7 `SuggestFamilies_ReturnsServiceUnavailable_WhenGatewayNotImplemented` y el equivalente para indisponibilidad.
- [x] 7.8 Al fijar datos con los *object mothers*, anclar `PointOfSale.Phone` explícitamente: Bogus genera teléfonos que no caben en `varchar(20)`.

## 8. Ejecución del lote y reconciliación

- [x] 8.1 Ejecutar `family-suggestions` sobre el corpus y revisar propuestas, grupos rechazados y productos excluidos antes de aplicar.
- [x] 8.2 Ejecutar `apply` con el lote completo. Verificación: **156 familias y 486 miembros** creados, todos con `Origin = AiApproved`.
- [x] 8.2b **Sacar del índice las 32 entradas que no son joyería terminada**, poniendo `ReviewStatus = Rejected` en su `ProductAiProfile`. **Nunca `IsActive = false`**: la tienda las vende —`Encargos` es una línea de caja de 10 €— y desactivarlas rompería el TPV para arreglar la búsqueda. La lista, validada el 2026-08-31: los 6 con tipo forzado (`Arreglos oro`, `Encargos Oro`, `Encargos plata`, `Presión Oro`, `Presión plata`, `Presión plata (x2)`) más los 26 nulos reales que son servicios, experiencias, velas y regalo, envío y merchandising `Neus`. **Se quedan dentro** `Llavero Cala Galdana` (28 €) y `Llavero Cape Nao pequeño` (85 €): son pieza artesanal propia, no reventa.
- [x] 8.3 Ejecutar **un solo** `POST /v1/index/sync` **sin `full`** que reconcilie a la vez las altas de familia y las bajas de 8.2b — el corpus se mueve una vez, y eso incluye las bajas. Verificación: los emitidos son **exactamente** los productos estampados más los 32 tombstones, y `family_id` deja de ser nulo sólo en los miembros.
- [x] 8.4 Comprobar que `doc_text` de esos documentos incluye `Familia:` y `Variante:`, que su `source_hash` cambió y que el embedding se recalculó.
- [x] 8.5 Comprobar que `source-text/v1` y `embedding_version` **no** han cambiado — es lo que obliga al orden, y conviene verificarlo en vez de suponerlo.
- [x] 8.6 Escribir [`Documentos/Proyecto Final AIEng/informes/c18a-family-suggestion-report.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/) con recuentos, cola de revisión, tasa de nulos de `piece_type` y los parámetros del veto usados (D14). Debe recoger además los cuatro hallazgos de calidad de catálogo: **(a)** las 32 entradas retiradas del índice y por qué; **(b)** que C09 **forzó** un tipo de pieza a seis servicios (`Arreglos oro`→collar, `Encargos`→collar, `Presión`→anillo) porque su vocabulario cerrado no admite «no es una pieza»; **(c)** que **9 joyas sintéticas legítimas** de 160 a 1.300 € —5 diademas, 2 gemelos, 1 cinturón, 1 «Joya del Zodiaco»— tienen `piece_type` nulo porque `piece_type.terms` sólo nombra ocho tipos y no incluye los suyos, incoherencia entre lo que C06b generó y lo que C09 puede expresar; **(d)** que `Cadena Barbara oro 40/42/45 cm` es una familia real que el agrupador **no ve**, porque su eje de variante son centímetros y el vocabulario de talla no tiene escala métrica.

## 9. Documentación y cierre

- [x] 9.1 Enlazar HU-AIENG-018a en `Documentos/epicas.md` (EP13) y marcar C18a como hecho en su lista de changes.
- [x] 9.2 **Reestructurar el plan de changes** al orden **C18a → C19 → C18b**: tabla maestra (§2), grafo de dependencias (§4) —hoy no dibuja C18→C25, C18→C26, C18→C30 ni C18→C36—, calendario (§5) y lista de *nunca se recorta* (§6), donde C30 y C36 son irrecortables mientras C18 no lo es. Renombrar la ficha y anunciar C18b como `add-family-review-ui-and-orphan-alert`.
- [x] 9.3 Añadir al §0 del plan la **revisión fechada con la medición del coseno** que corrige el enunciado del §7.5 del diseño.
- [x] 9.4 Dejar planteada en el §0 la decisión sobre el **doble etiquetado del golden set de C24** trabajando en solitario, para resolver antes de abrir C24 (D13).
- [x] 9.4b Anotar como **candidatos a change propio** los tres arreglos de raíz que C18a destapa y no resuelve: ampliar `piece_type.terms` con `diadema`, `gemelos` y `cinturon` —lo que obliga a reenriquecer esos 9 productos y **volverá a mover el corpus**, así que necesita su propia decisión de cuándo—; dar a C09 una salida explícita «no es una pieza» en vez de forzar un tipo; y llevar los cierres `Presión` a `ProductComponents` (EP10), que es donde conceptualmente viven.
- [x] 9.5 Anotar la **divergencia spec/código de `Product.CollectionId`**: la spec viva `product-family` apela a una cardinalidad 1..N que el código no tiene (`Guid? CollectionId`, FK única y anulable). Los discriminadores reales son el tipo de pieza y el tamaño.
- [x] 9.6 Actualizar la documentación afectada según la tabla *Post-Implementation Documentation Update* de `openspec/project.md`.
- [x] 9.7 Comparar la suite contra la línea base de 1.3 **por nombres de test**, no por recuento, y dejar constancia en `qa.md`.
- [x] 9.8 `openspec validate --all --strict` en verde (`0 failed`) antes de archivar — el gate completo, no sólo la forma de un change.
