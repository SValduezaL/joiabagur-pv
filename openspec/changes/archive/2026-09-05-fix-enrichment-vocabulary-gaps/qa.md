# QA — FIX1 `fix-enrichment-vocabulary-gaps`

> Registro de las comprobaciones **realmente ejecutadas** sobre la implementación del change, con sus resultados.
> **Fecha:** 2026-09-05 · **Rama:** `fix1-enrichment-vocabulary-gaps` · **Commit de artefactos:** `90e1d04` · **Implementación:** en árbol de trabajo, sin commitear
> **Idioma:** cuerpo en español, identificadores técnicos en inglés, por coherencia con [ticket.md](ticket.md) y con la HU.
> **Alcance:** **53/53 tareas**. Las de §9 y §10 (corrida real y verificación de extremo a extremo) se ejecutaron contra proveedor real con `STUB_MODE=false`; ver §8.
> **Desviación de artefactos:** ninguna en alcance. Dos hallazgos no previstos por `tasks.md` obligaron a tocar dos ficheros de más —un quinto test fijado y una corrección del encargo de `v2`—; ambos en §9.
> **Acta de la corrida:** [`fix1-vocabulary-gaps-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/fix1-vocabulary-gaps-measurements.md)

---

## Entorno de verificación

| Pieza | Valor |
|---|---|
| Python | 3.11 · `uv` — **con `--system-certs` en todas las llamadas `uv run`**, según `CLAUDE.md` |
| PostgreSQL | 15 con `vector` (`jpv-pv-postgres`, puerto 5433), base local `joiabagur_pv` con 1.168 documentos y 1.200 perfiles |
| `jbg-ai` | contenedor `jpv-pv-jbg-ai` en `:8001`, **imagen reconstruida** con `docker compose build jbg-ai` |
| API .NET | 10.0.303, `dotnet run --launch-profile http` en `:5056` |
| Proveedor | **Real.** `STUB_MODE=false`, `openai/gpt-4o-mini`, `JPV_RAG_LLM_CONCURRENCY=2` (override del runbook de C12), y `JPV_EMBEDDING_API_KEY` para la sincronización |
| Contrato | `ai-service/openapi.json` **no se regenera**. `git diff` vacío, comprobado antes y después |
| Prompt anterior | `git diff -- ai-service/prompts/enrichment/v1.md` **vacío**, y fijado por test |
| `backend/src/` | **sin una línea de cambio**. Sólo se *ejecuta* un endpoint que ya existía |
| Frontend | Node · `vitest` 4.0.15 · `npm run build` como puerta real, `tsc --noEmit` **no** |

**Nota sobre las claves:** ni `JPV_RAG_LLM_API_KEY` ni `JPV_EMBEDDING_API_KEY` se imprimieron nunca. Se
verificaron por longitud (`printenv … | wc -c` → 165) y por el `provider: "configured"` de `/health`.

---

## 1. Suites automáticas

La línea base de Python se midió **de verdad**, sobre el árbol limpio, antes de tocar una línea.

| Ejecución | Resultado |
|---|---|
| **Línea base** `ai-service` (árbol limpio en `90e1d04`) | **697 passed**, 0 failed, 126,9 s |
| `ai-service` al cerrar los grupos 2–8 | **703 passed**, 0 failed, 40,6 s |
| `ai-service` tras corregir el encargo de `v2` (§9.1) | **703 passed**, 0 failed, 39,0 s |
| `ai-service` tras cubrir el escenario que faltaba (§3.1) | **704 passed**, 0 failed, 54,4 s |
| **Línea base** `frontend` (`npm run test`) | **113 failed / 455 passed** de 568, 14 ficheros rojos de 47 |
| `frontend` tras la implementación | **113 failed / 456 passed** de 569 — ver §2 |
| `npm run build` | **limpio, salida 0** |
| `openspec validate fix-enrichment-vocabulary-gaps --strict` | *valid* |
| `openspec validate --all --strict` | **51 passed, 0 failed** |

**+7 tests** de Python sobre la línea base (697 → 704) y **+1** en el frontend (568 → 569).

> El recuento **sí es fiable** en `ai-service`: parte de **cero** fallos y no llama a proveedores ni a RDS.
> En `frontend/` **no lo es** —arranca en rojo y `vitest` sale 0 al canalizarlo— y la comparación se hace
> por nombres en §2.

### Desglose de tests nuevos o ampliados

| Fichero | Antes → Después | Qué cubre |
|---|---|---|
| `tests/enrichment/test_vocabularies.py` | 4 → **5** | `test_new_piece_types_are_canonical_and_normalised`: los cuatro términos resuelven a sí mismos, `Cinturón`/`cinturón` pliegan al canónico sin tilde, `LLAVERO` a `llavero`; y **`tiara` y `gemelo` siguen siendo desconocidos para el base**, que es lo que prueba que no se coló ningún sinónimo de extracción |
| `tests/enrichment/test_llm.py` | 11 → **13** (+1 renombrado) | `test_prompt_version_matches_the_loaded_prompt_file` (renombra a `test_prompt_version_is_enrichment_v1`, §9.2): la ruta sale de la constante y **el encabezado del fichero cargado la nombra**. `test_superseded_prompt_versions_stay_in_the_repository`: `v1.md` sigue ahí y sigue diciendo `# enrichment/v1`. `test_prompt_piece_type_list_matches_the_closed_vocabulary`: la lista escrita en el prompt **es** la del YAML, así que la deriva entre las dos réplicas falla en rojo en vez de en silencio |
| `tests/enrichment/test_pipeline.py` | 10 → **13** | `test_a_null_piece_type_is_kept_and_not_defaulted` (el nombre honesto de §9.2 del ticket); `test_untypeable_jewel_stays_null`, que además comprueba que **no hay warning** —un nulo correcto no es una extracción rechazada—; y `test_proper_name_containing_a_piece_type_does_not_beat_the_head_noun`, con los dos «Cinturón de Orión» y la comprobación de que el vocabulario **no resuelve el nombre propio por su cuenta** |
| `tests/retrieval/test_synonyms.py` | 22 → **23** (+3 fijados actualizados) | `test_plural_canonical_is_reachable_from_its_singular` (§3.1). Los tres fijados que saltan: la tupla a doce términos, el conjunto de exclusiones reducido a `piel` y `filigrana` **más la aserción de que los cuatro cerrados ya no están**, y el guardián con `filigrana` en lugar de `diadema` |
| `frontend/src/lib/materials-vocabulary.test.ts` | 4 → **5** | El array fijado a doce y su descripción; y un test nuevo que exige que **ningún `value` lleve tilde** y que «Cinturón» viva sólo en el `label`, porque el valor se compara por igualdad exacta contra el índice |

---

## 2. Suite del frontend, comparada por nombres

`CLAUDE.md` avisa de que el recuento no vale y de que `vitest` sale 0 al canalizarlo. No me limité a
citarlo: capturé la salida **completa** de las dos pasadas y las comparé por nombre de test.

```bash
sed -E 's/\x1b\[[0-9;]*m//g' frontend-baseline-full.txt | grep -E "^ +× " | sort  > baseline.txt
sed -E 's/\x1b\[[0-9;]*m//g' frontend-after.txt         | grep -E "^ +× " | sort  > after.txt
diff baseline.txt after.txt   # → sin salida
```

| Medición | Resultado |
|---|---|
| Línea base | 113 nombres fallando de 568 |
| Tras la implementación | 113 nombres fallando de 569 |
| **Diferencia por nombres** | **cero: conjunto idéntico** |

Los 14 ficheros rojos son los preexistentes que documenta [testing-frontend.md](../../../../Documentos/testing-frontend.md)
—`payment-methods`, los dos `products/edit`, `product-photo-upload`, los cuatro de `sales/`, y cinco de
`services/`—. **`materials-vocabulary.test.ts` no está entre ellos**, ni antes ni después: el fichero que
este change toca estaba verde y sigue verde.

> La primera pasada de la línea base se canalizó con `| tail -60` y **perdió los nombres**. Se repitió
> entera, redirigiendo a fichero, **antes de tocar un solo fichero del frontend**. Es exactamente la
> trampa que `CLAUDE.md` describe, y caí en ella una vez.

---

## 3. Escenarios de las specs, uno a uno

**17 escenarios `#### Scenario:`** en los dos deltas: `catalog-enrichment-pipeline` 13, `query-expansion` 4.
Todos tienen test nombrado. El decimoséptimo no lo tenía y se le puso (§3.1).

### `catalog-enrichment-pipeline` (13)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Enriquecimiento real · Stub mode keeps the C08 fixture cycle | `test_enrich_stub_is_deterministic` · `test_enrich_reports_prompt_version` · `test_enrich_stub_exercises_both_provenances` | ✅ |
| Enriquecimiento real · Real mode produces extracted profiles | `test_real_mode_does_not_use_stub_cycle` — afirma `prompt_version == PROMPT_VERSION`, que **ahora es `enrichment/v2`** | ✅ |
| Enriquecimiento real · **The prompt version cannot disagree with the prompt that was sent** | `test_prompt_version_matches_the_loaded_prompt_file` · `test_superseded_prompt_versions_stay_in_the_repository` | ✅ |
| Enriquecimiento real · Real mode without a key fails explicitly | `test_real_mode_without_key_fails_explicitly` | ✅ |
| Enriquecimiento real · OpenAPI snapshot stays frozen | `test_openapi_snapshot_is_stable` + `git diff` vacío (§5) | ✅ |
| Vocabularios cerrados · Several materials become a canonical list | `test_extracts_multiple_materials_from_description` | ✅ |
| Vocabularios cerrados · A material synonym is normalized and an invented value is rejected | `test_material_synonym_normalized_to_canonical_term` · `test_rejects_value_outside_closed_vocabulary` (×2, vocab y pipeline) | ✅ |
| Vocabularios cerrados · No material evidence yields an empty list | `test_empty_materials_flags_review_not_default_value` | ✅ |
| Vocabularios cerrados · Piece type stores the hypernym | `test_piece_type_stores_hypernym_not_hyponym` (×2, vocab y pipeline) | ✅ |
| Vocabularios cerrados · **The widened vocabulary names the pieces the eight hypernyms could not** | `test_new_piece_types_are_canonical_and_normalised` · `test_base_vocabulary_terms_are_pinned` · **y la corrida real**: SKU617 → `diadema`, SKU844 → `gemelos`, SKU415 → `llavero`, SKU936 → `cinturon` (§8) | ✅ |
| Vocabularios cerrados · **A proper name containing a piece type does not beat the head noun** | `test_proper_name_containing_a_piece_type_does_not_beat_the_head_noun` · **y el grupo de control de la corrida**: SKU822 sigue `broche` y SKU882 sigue `anillo`, sin mover un solo campo (§8.3) | ✅ |
| Filas que no son joyería · A service is not given a piece type | `test_a_null_piece_type_is_kept_and_not_defaulted` | ✅ |
| Filas que no son joyería · A jewel the vocabulary cannot name keeps a null type | `test_untypeable_jewel_stays_null` · **y SKU845 en la corrida**, que sigue nulo y es el único nulo del índice | ✅ |

### `query-expansion` (4)

| Requisito · escenario | Test | Resultado |
|---|---|---|
| Entradas y exclusiones justificadas · A measured false friend is absent from the dictionary | `test_excluded_false_friend_is_absent` | ✅ |
| … · Vocabulary gaps are not smuggled in as synonyms | `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` (ahora con `filigrana`) · `test_shipped_overlay_anchors_all_exist_in_the_base_vocabulary` | ✅ |
| … · **A closed gap stops being recorded as an exclusion** | `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in`, que **exige `piel` y `filigrana` y prohíbe los cuatro cerrados** | ✅ |
| … · **A plural canonical is reachable from its singular** | `test_plural_canonical_is_reachable_from_its_singular` — **añadido en esta pasada**, §3.1 | ✅ |

### 3.1. Un escenario que no tenía test, y se le puso

El escenario *«A plural canonical is reachable from its singular»* es normativo en el delta de
`query-expansion` y **ninguna tarea de `tasks.md` pedía un test para él**. La tarea 5.3 pedía la entrada
del overlay; nadie pedía comprobar que funciona.

`test_plural_canonical_is_reachable_from_its_singular` cierra las dos mitades del argumento:

- `singular_candidates("gemelo") == ()` — la reducción de plurales va **singular←plural** y nunca al
  revés, así que el singular no puede alcanzar al canónico plural por su cuenta;
- `gemelo` está declarado en las formas del overlay y `"gemelos" in _forms("gemelo")`;
- y `diademas`, `llaveros` y `cinturones` **no** están declarados y aun así alcanzan su canónico, que es
  por lo que no se les añadió entrada. Una entrada de más también habría sido un defecto.

---

## 4. Nombres exigidos por `tasks.md`

| Tarea | Nombre exigido | Existe |
|---|---|---|
| 2.3 | `test_new_piece_types_are_canonical_and_normalised` | ✅ |
| 3.6 | `test_prompt_version_matches_the_loaded_prompt_file` | ✅ |
| 4.1 | *renombrar* `test_service_and_consumable_rows_get_null_piece_type` | ✅ como `test_a_null_piece_type_is_kept_and_not_defaulted` — ver abajo |
| 4.2 | `test_untypeable_jewel_stays_null` | ✅ |
| 4.3 | `test_proper_name_containing_a_piece_type_does_not_beat_the_head_noun` | ✅ |
| 6.1 | `test_base_vocabulary_terms_are_pinned` (ampliar a doce) | ✅ |
| 6.2 | `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in` (reducir a las vivas) | ✅ |
| 6.3 | `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` (**sustituir ejemplo, no borrar**) | ✅ |

**Sobre la 4.1.** El test que manda renombrar **no existía**: era un nombre propuesto en el §3 del plan
de changes, que ni la exploración ni el ticket llegaron a crear. La tarea se cumplió en su intención —que
el nombre diga lo que la prueba comprueba— escribiéndolo directamente como
`test_a_null_piece_type_is_kept_and_not_defaulted`, con la advertencia del ticket en el docstring: con un
`EnrichLlm` falso esto no dice nada del **enunciado**, y la evaluación del prompt es la corrida.

---

## 5. Alcance negativo

```bash
git status --short -- frontend/src/pages terraform/ .github/ backend/src/ \
  ai-service/openapi.json ai-service/prompts/enrichment/v1.md \
  ai-service/src/jbg_ai/retrieval/synonyms.py ai-service/src/jbg_ai/indexing/
```

Salida **vacía**.

| Guardarraíl | Comprobación | Resultado |
|---|---|---|
| `prompts/enrichment/v1.md` | `git diff` vacío **y** `test_superseded_prompt_versions_stay_in_the_repository` | ✅ |
| `ai-service/openapi.json` | `git diff` vacío **y** `test_openapi_snapshot_is_stable` en verde | ✅ |
| `retrieval/synonyms.py` | `git diff` vacío. `_base_layer()` deriva las cuatro clases del YAML sin tocarse; verificado leyendo el bucle sobre `vocabs.field(field).canonical` | ✅ |
| `indexing/embeddings.py` · `source_text.py` | `git diff` vacío. La plantilla del documento no cambia: cambia el contenido de 19 filas | ✅ |
| `backend/src/` | **ni una línea**. `Force`, `MaxBatchSize = 50` y `AutoBulk → Approved` ya existían | ✅ |
| `frontend/src/pages/` | `git diff` vacío: `assisted.tsx:335` itera sobre la constante y se rellena solo | ✅ |
| `terraform/` · `.github/workflows/` | `git diff` vacío | ✅ |
| **Migración** | ninguna, ni de Alembic ni de EF Core. Ninguna tabla, columna ni índice cambia | ✅ |
| Ruta HTTP nueva | ninguna. El único tráfico es un `POST` a un endpoint existente | ✅ |
| `embedding_version` · `text_provenance` | **sin mover en las 1.168 filas**, comprobado por diff de la columna antes y después de la sincronización (§8.4) | ✅ |
| Defaults del servicio | `test_defaults_remain_gpt4o_and_concurrency_8` sigue en verde: `gpt-4o-mini` y concurrencia 2 fueron **override del contenedor**, no del código | ✅ |
| `tiara` en el overlay | ausente. Alcanza 0 documentos y la regla del fichero es que una entrada sin número detrás no entra | ✅ |
| Sinónimos de extracción nuevos | ninguno: `normalize_value("gemelo", piece_type) is None` y `("tiara")` también | ✅ |

---

## 6. Los cinco alambres que debían saltar

La HU contaba dos, la exploración corrigió a cuatro, y la implementación encontró un quinto (§9.2).
**Los cinco saltaron, y ninguno se borró.**

| # | Alambre | Cómo falló | Qué se hizo |
|---|---|---|---|
| 1 | `test_base_vocabulary_terms_are_pinned` | tupla de 8 ≠ 12 | Ampliado a doce y **docstring reescrito**: ya no anuncia este change, cuenta que lo movió a propósito |
| 2 | `materials-vocabulary.test.ts` | array de 8 ≠ 12 | Ampliado, descripción «eight» → «twelve», y **un test nuevo** sobre la tilde del `value` |
| 3 | `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in` | exigía los cuatro términos en `exclusions` | Reducido a `piel` y `filigrana`, **más una aserción en negativo** de que los cuatro cerrados ya no están |
| 4 | `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` | **`DID NOT RAISE`** — la dirección contraria a la esperada | Ejemplo cambiado de `diadema` a `filigrana`. **No se borró.** Es el guardián que hizo visible este change |
| 5 | `test_prompt_version_is_enrichment_v1` | `assert PROMPT_VERSION == "enrichment/v1"` | Reescrito como `test_prompt_version_matches_the_loaded_prompt_file`, que ya no fija una versión concreta sino **la coherencia entre constante, ruta y encabezado**. Ver §9.2 |

El cuarto es el peligroso y se comprobó a mano que sigue guardando: se ejecutó aislado y **lanza**
`SynonymDictionaryError` nombrando `filigrana` y `fix-enrichment-vocabulary-gaps`.

---

## 7. Decisiones de diseño, verificadas en código

| Decisión | Evidencia |
|---|---|
| D1 · Cohorte de 22 con dos de control | Lista enumerada en `design.md`, no consulta en tiempo de ejecución. La consulta previa devolvió **exactamente esos 22 SKU** con los `piece_type` que la tabla predecía |
| D2 · Aceptación estructural, no léxica | El criterio *«buscar diadema pasa de cero a resultados»* **no se usó**. La aceptación es la tabla de recuentos de §8.5 |
| D3 · `gemelos` plural, `cinturon` sin tilde | `test_new_piece_types_are_canonical_and_normalised` + el test nuevo del frontend que prohíbe tildes en cualquier `value` |
| D4 · Ruta derivada de la versión, `v1.md` conservado | `_PROMPT_RELATIVE = Path("prompts") / f"{PROMPT_VERSION}.md"`; el `FileNotFoundError` ya no nombra `v1`; dos tests |
| D5 · Los cuatro términos entran en el desplegable | `PIECE_TYPE_OPTIONS` a doce; `npm run build` limpio; y la consecuencia declarada se comprobó: en los PdV sin llavero el facet devuelve lista vacía (§8.6) |
| D6 · El overlay entra; `filigrana` no | Cuatro exclusiones **borradas**, motivo de `filigrana` reescrito sin remitir a este change, clase `gemelos` con su medición. `tiara` ausente |
| D7 · Cuatro alambres, con el guardián cambiando de ejemplo | §6 |
| D8 · La corrida ocurre dentro del change | §8. Y fue la corrida —no un test— la que encontró el defecto del encargo (§9.1), que es el argumento de D8 demostrado |
| D9 · La spec fija `enrichment/v2` literalmente | El escenario dice `enrichment/v2`; `test_real_mode_does_not_use_stub_cycle` lo comprueba a través de la constante |

---

## 8. La corrida real

Condiciones completas y tabla de las 22 filas en el
[acta](../../../../Documentos/Proyecto%20Final%20AIEng/informes/fix1-vocabulary-gaps-measurements.md).

### 8.1. Comprobación previa (tareas 1.3 y 1.4)

```
 docs | null_type | broche | collar | colgante
 1168 |        11 |     85 |    140 |      161
```

Y `PromptVersion` → `enrichment/v1: 1200`. **Coincide dígito a dígito con lo que midió la exploración.**
De los 22 perfiles de la cohorte, **ninguno** tenía `ReviewedByUserId` ni `ReviewedAt`: no había revisión
humana que perder, y no se registró ningún `enrich_profile_review_reset`.

### 8.2. El lote (tarea 9.3)

```json
{"requested":22,"enriched":22,"skippedUnchanged":0,"skippedConcurrent":0,"failed":0}
```

Un solo lote, `force: true`, `reviewMode: "AutoBulk"`, 14,1 s. Los 22 quedan `ReviewStatus = 2`
(*Approved*) y `ReviewOrigin = 1` (*AutoBulk*), por tanto indexables.

### 8.3. Grupo de control (tarea 9.5) — el veredicto

**SKU822 `Broche Cinturón de Orión` y SKU882 `Anillo Cinturón de Orión` no se movieron en ningún campo.**
No sólo el tipo: materiales, piedra, talla, los tres arrays de etiquetas y **hasta la confianza** son
idénticos (0,458 → 0,458 y 0,460 → 0,460). Añadir `cinturon` al vocabulario cerrado no arrastró el nombre
propio. Era el riesgo mayor de `v2` y queda **medido**, no supuesto.

`SKU845 Joya del Zodiaco` se comporta igual: fila idéntica, nulo conservado, y es el único nulo que queda.

### 8.4. Sincronización (tareas 9.8 y 9.9)

```
upserted=19 skipped=1149 deleted=0 failed=0
```

**19 = 22 − 3.** Las tres excluidas son justo aquellas cuyo perfil no cambió, así que su `doc_text` y su
`source_hash` tampoco. Comprobado comparando el hash de las **1.168** filas antes y después: cambian
exactamente 19, y son las 19 esperadas por SKU. El indexador no tocó una fila de más.

`embedding_version` y `text_provenance` **sin una sola diferencia** en las 1.168 filas.

### 8.5. Recuentos (tareas 10.1 y 10.2)

| Comprobación | Antes | Después | Esperado |
|---|---:|---:|---:|
| `diadema` / `gemelos` / `llavero` / `cinturon` | 0 / 0 / 0 / 0 | **11 / 4 / 3 / 1** | 11 / 4 / 3 / 1 ✅ |
| `piece_type IS NULL` | 11 | **1** | 1 ✅ |
| `broche` | 85 | **79** | 79 ✅ |
| Impostores dentro de `broche` | 6 | **0** | 0 ✅ |
| `collar` / `colgante` | 140 / 161 | **138 / 160** | −2 / −1 ✅ |
| Perfiles `v2` / `v1` | 0 / 1.200 | **22 / 1.178** | 22 / 1.178 ✅ |

La consulta de impostores es explícita, no un conteo de cabecera:
`WHERE piece_type='broche' AND (name ILIKE '%diadema%' OR '%gemelos%' OR '%llavero%' OR '%tiara%')`
→ **0 filas**.

### 8.6. Por la interfaz (tarea 10.3)

Sesión real de administrador contra `POST /api/ai/search`, que es la llamada que emite el panel.

| Filtro | Candidatos | En surtido | Contenido |
|---|---:|---:|---|
| «Diadema» | **11** | 6 | las once diademas; **todas** son diademas |
| «Broche» | 60 (tope de sobre-recuperación) | 29 | **ningún impostor** |
| «Gemelos» | 4 | 2 | los cuatro |
| «Cinturón» | 1 | 1 | `Cinturón Ola Dorada` |
| «Llavero» | 1 | 1 en Taller Joia Bagur | `Llavero Cala Galdana` |

**Tarea 10.4 respetada:** en ningún momento se usó «buscar `diadema` devuelve resultados» como prueba.
Ya se cumplía antes del change.

---

## 9. Incidencias de esta pasada

### 9.1. El encargo nuevo se comió un canónico nuevo

**La incidencia más importante, y sólo la corrida podía encontrarla.** La primera ejecución de `v2` dejó
**dos de los tres llaveros sin tipo** (SKU415 y SKU417), sin `warnings`: el modelo devolvió nulo, no
propuso nada que el pipeline rechazara. Los tres textos son casi idénticos entre sí, así que no era falta
de evidencia.

La línea nueva del encargo —la que la HU pedía— advierte de que el catálogo puede contener *servicios,
consumibles y **artículos de regalo***, y que para ellos `piece_type` es nulo. **Un llavero es literalmente
un artículo de regalo.** El modelo hizo exactamente lo que se le pidió.

Se corrigió `v2.md` en dos frases, sin tocar el vocabulario: se declara que **la lista cerrada manda sobre
esa advertencia**, y se acota la regla del nombre propio para que no niegue el sustantivo núcleo —que en
estos productos era la única evidencia que había—. **La cohorte entera se volvió a correr**, no sólo las
dos filas fallidas: si no, veintidós perfiles sellados `enrichment/v2` habrían venido de dos textos
distintos, que es exactamente la propiedad que D4 existe para proteger.

Segunda corrida: 22/22, los tres llaveros tipados, y el grupo de control **sigue sin moverse**.

### 9.2. Un quinto test fijado que ningún artefacto contaba

`test_prompt_version_is_enrichment_v1` ([test_llm.py](../../../../ai-service/tests/enrichment/test_llm.py))
afirmaba `PROMPT_VERSION == "enrichment/v1"` y abría `prompts/enrichment/v1.md` por ruta literal. Ni la
HU, ni el ticket, ni `design.md` lo inventarían: los tres cuentan cuatro alambres.

Se convirtió en el test que la tarea 3.6 pedía, en vez de añadir uno al lado: ya no fija una versión
concreta —lo que obligaría a editarlo en cada salto— sino **la coherencia entre la constante, la ruta
derivada y el encabezado del fichero cargado**. La mitad que se perdía al reescribirlo (que `v1.md` sigue
existiendo) se recuperó en un test propio.

### 9.3. La imagen del contenedor estaba obsoleta, y habría producido un informe falso

`backend-jbg-ai:latest` existía de antes y **no contenía `v2.md`**. Correr el lote contra ella habría
sellado 22 perfiles como `enrichment/v2` habiéndolos producido `v1` —el fallo exacto que D4 describe,
llegando por la puerta de al lado—. Se reconstruyó con `docker compose build jbg-ai` y se verificó
**dentro del contenedor** antes de lanzar nada:

```
$ docker exec jpv-pv-jbg-ai sh -c 'ls /app/prompts/enrichment/ && head -1 /app/prompts/enrichment/v2.md'
v1.md
v2.md
# enrichment/v2
```

Tras la corrección de §9.1 se reconstruyó y reverificó otra vez (`grep -c "manda sobre esta advertencia"` → 1).

### 9.4. La ruta asistida está apagada en local, y la primera verificación por interfaz fue un falso negativo

Las cinco primeras consultas por categoría devolvieron **la misma lista para las cinco**, ignorando el
filtro. No es un fallo del change: `AiSearch:EnabledByDefault` es `false` y ningún punto de venta está en
la lista de permitidos, así que `/api/ai/search` degrada a un listado de catálogo. El log lo dice sin
ambigüedad —`Origin=Disabled`, `aiAvailable:false`, `candidatesReturned:0`— y jbg-ai **no registró ni una
petición de recuperación**, que fue la prueba decisiva.

La verificación se repitió con `AiSearch__EnabledByDefault=true` **como variable de entorno**, sin tocar
ningún fichero del repositorio. `git status` lo confirma.

Merece constar porque es un falso negativo con la firma de C17: resultados en pantalla, HTTP 200, ningún
error, y una conclusión equivocada esperando a quien lea sólo la primera línea.

### 9.5. `python` no está en el PATH de este entorno

Las ediciones precisas de ficheros con acentos se hicieron con `uv run --system-certs python`, no con
`sed`, para no arriesgar la codificación. `v2.md` se verificó como **UTF-8 con CRLF**, igual que `v1.md`.

---

## 10. Verificado a mano

- **Los 22 SKU de la cohorte se consultaron antes de correr nada** y coinciden uno a uno con la tabla de
  `design.md` D1, incluidos los `piece_type` erróneos que predecía.
- **El diff completo de las 22 filas se leyó campo a campo**, no sólo `piece_type`. De ahí salen los
  movimientos colaterales que el acta publica: tres `stone_type` que degradan al residual y dos que
  desaparecen. Son variación del extractor, no efecto del vocabulario —las filas afectadas no comparten
  el tipo nuevo—, y se escriben en vez de omitirse.
- **El árbol `tests/enrichment/` se ejecutó con los sockets no-loopback bloqueados** por un plugin de
  pytest ad hoc: **41 passed**. Se descartó primero una versión que bloqueaba también loopback, que hacía
  fallar 8 tests por el bucle de asyncio y el `TestClient` — el `conftest.py` del árbol ya lo advertía.
- `docker exec … printenv STUB_MODE JPV_RAG_LLM_MODEL JPV_RAG_LLM_CONCURRENCY` → `false`,
  `openai/gpt-4o-mini`, `2`. La clave **nunca se imprimió**: sólo su longitud.
- **El modelo de la corrida coincide con el de los 1.178 perfiles no reenriquecidos** (`openai/gpt-4o-mini`),
  comprobado en `GeneratedByModel` del estado previo. Las dos poblaciones se distinguen por
  `PromptVersion` y no por modelo, que es lo que hace comparable la tabla del acta.
- El `ProposedProfileJson` de los tres llaveros se leyó entero para descartar que el pipeline hubiese
  rechazado un valor: `warnings: []` en los tres. El nulo venía del modelo.
- `git status --porcelain` revisado al cerrar: 12 modificados y 2 nuevos, todos esperados.

---

## 11. Documentación de contexto

| Documento | Qué se alineó |
|---|---|
| `ai-service/README.md` | Sección nueva **«Enrichment prompt versions»**: la ruta deriva de la constante, los ficheros superados se conservan, el corpus queda mezclado en 22/1.178, y **toda métrica agregada sobre atributos extraídos debe reportarse por `PromptVersion`** —la misma disciplina que C24 aplica a `data_origin`—, con la distinción frente a mezclar `embedding_version` |
| `Documentos/epicas.md` | FIX1 pasa de «en curso» a **hecho** en las cuatro apariciones (bloque de EP12, resumen, índice de historias y tabla de épicas), y se enlaza el acta con el resumen del defecto del encargo |
| Informe nuevo | [`fix1-vocabulary-gaps-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/fix1-vocabulary-gaps-measurements.md): condiciones, la corrida fallida y su causa, el diff completo de las 22 filas, el veredicto del control, los recuentos, la sincronización y las suites |

---

## 12. Fuera de esta pasada

- **Los 1.178 perfiles restantes.** Siguen en `enrichment/v1` a propósito. El acta y el README dejan
  escrito que cualquier agregado sobre atributos hay que partirlo por versión de prompt.
- **`filigrana`.** Única laguna viva, en el eje `style_tags`, con su motivo actualizado en las exclusiones
  y convertida en el ejemplo del test guardián.
- **La regresión de `stone_type`** en cinco filas de la cohorte. Medida, publicada y **no corregida**:
  perseguirla sería reenriquecer buscando un resultado, que es lo contrario de lo que el change hace.
- **El endpoint de facets agregados desde el surtido.** Este change no lo abre: le sube el precio a no
  cruzarlo —cinco ficheros, cuatro alambres, dos lenguajes y dos specs vivas por cuatro términos— y le
  entrega la primera medición.
- **Reejecutar la sugerencia de familias de C18a**, aunque `Llavero Cape Nao` Grande y pequeño compartan
  tipo por primera vez.
- **El rojo preexistente del frontend.** 113 nombres en línea base, con cinco causas documentadas. No se
  tocó ninguno: no es de este change.
- **`dotnet test`.** El change no cambia una línea de `backend/src/`, así que la suite de .NET no está en
  su radio. No se ejecutó, y se dice en vez de insinuar que salió verde.

---

## Veredicto

**Sin problemas abiertos.** `uv run --system-certs pytest` **704 passed, 0 failed** sobre una línea base
medida de **697**, sin abrir un socket a proveedor en el árbol de enriquecimiento —comprobado bloqueándolos—.
El frontend mantiene el **conjunto de nombres de test fallidos idéntico** al de la línea base, con `npm run
build` limpio. `openspec validate --all --strict` **51 passed, 0 failed**. **17/17 escenarios** con test
nombrado —uno de ellos añadido en esta pasada—, **8/8 nombres** exigidos por `tasks.md`, **53/53 tareas**, y
**los cinco alambres fijados saltaron sin que se borrase ninguno**.

**La corrida real hizo su trabajo, que era encontrar lo que ningún test podía.** La línea nueva del encargo
dejaba sin tipo a dos de los tres llaveros porque un llavero *es* un artículo de regalo; se corrigió la
precedencia y se reenrichó la cohorte entera para que los 22 perfiles vengan de un solo texto. Es
literalmente el argumento de D8 —*«si el prompt se sobreajusta, lo aprendemos dentro del change»*—
ocurriendo, sólo que en la dirección contraria a la vigilada.

**El grupo de control no se movió en un solo campo**, confianza incluida: `cinturon` en el vocabulario
cerrado no se come «Cinturón de Orión». Los recuentos caen en su sitio —nulos 11 → 1, `diadema` 0 → 11,
impostores en `broche` 6 → 0— y la sincronización reembebió **19 filas, exactamente las 19 cuyo
`source_hash` cambió**, sin mover `embedding_version` ni `source-text/v1`.

**Listo para archivar.**
