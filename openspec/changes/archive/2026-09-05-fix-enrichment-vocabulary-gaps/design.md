# Design — fix-enrichment-vocabulary-gaps (FIX1)

## Context

C09 fixed `piece_type` as a **closed** vocabulary of eight hypernyms in `enrichment/vocabularies.yaml`. That list is replicated in four other places: the prompt duplicates it as plain text, the frontend mirrors it in `materials-vocabulary.ts`, and two live specs state it normatively. A fifth consumer, C20's query dictionary, does **not** replicate it — `_base_layer()` derives its equivalence classes from the same YAML, so a term added there grows a query class on its own.

C18a found eleven products the vocabulary could not name and booked the fix as a change. Everything below was measured on **2026-09-05** against the local PostgreSQL (15.19), read-only, over the 1.168 live rows of `ai.product_document`, the 1.200 rows of `ProductAiProfiles` and the `ai.pos_projection` rows C22 left. No provider calls. Full record in [`fix1-exploration-measurements.md`](../../../../Documentos/Proyecto%20Final%20AIEng/informes/fix1-exploration-measurements.md).

Six measurements govern this design. **Two of them contradict the ficha.**

| # | Measurement | Consequence |
|---|---|---|
| 1 | 22 products carry a gap term in their name: **11 null, 9 wrongly typed, 2 correct false friends** | The population is twice what the ficha counts. Decides D1 |
| 2 | The wrong labels concentrate in `broche`: **6 of its 85 documents** are 3 tiaras, 2 cufflinks and a keyring; `collar` carries 2 tiaras of 140, `colgante` 1 of 161 | A wrong label is worse than a null, because the category filter is hard. Decides D1 |
| 3 | Lexical reach today: `diadema` **11**, `gemelos` 4, `cinturon` 3, `llavero` 3, `tiara` **0** | The ficha's end-to-end criterion already passes. Decides D2 and rules `tiara` out of the overlay |
| 4 | Assortment reach: `diadema` and `gemelos` in **11 of 11** points of sale, `cinturon` 10, `llavero` 6 — against `cadena`, shipped in the dropdown since C16 with 6 of 11 | Every new term clears the bar already accepted. Decides D5 |
| 5 | `PROMPT_VERSION` (`constants.py:5`) and `_PROMPT_RELATIVE` (`pipeline.py:51`) are declared independently | A half-done bump stamps a version that did not produce the profile. Decides D4 |
| 6 | Four pinned tests break, not two — and one of them uses `diadema` as its example of an unknown canonical | The blast radius includes C20's overlay and a second live spec. Decides D6 and D7 |

## Goals / Non-Goals

**Goals:**

- Give a canonical name to the four kinds of piece the closed vocabulary cannot express, and make the category facet **true** rather than merely present.
- Remove the nine impostors polluting `broche`, `collar` and `colgante`.
- Close the brief gap in the extraction prompt: the catalogue may hold things that are not finished jewellery.
- Make the four replicas of the vocabulary move together, deliberately, with every pinned test firing as designed.
- Leave the corpus moved by exactly one path, for exactly one enumerated cohort, before C24 labels its baseline.

**Non-Goals:**

- Re-enriching the 1.200. ~1.200 calls, diffuse reclassification nobody asked for, and no human review covers that many rows.
- `filigrana`. It is a `style_tags` gap on a different axis, it reaches its 66 documents unexpanded, and one change carries one idea.
- A new classification axis (`product_category`: jewellery / accessory / service / consumable). It would be schema, DTO, feed, index column and migration for four terms. Null keeps meaning "not a piece" or "cannot name it", and after this change the residue is **one** product.
- Moving `source-text/v1`, `embedding_version` or `indexing/embeddings.py`.
- Re-running C18a's family suggestion, though this change leaves `Llavero Cape Nao` Grande/pequeño able to form a family for the first time.
- The endpoint aggregating piece types actually present in a point of sale's assortment. It is the better answer to the replication problem, it is noted since C16, and it is **not in C28's scope** — C28's ficha is the profile review screen and its metrics.
- Any migration, any new HTTP route, any `openapi.json` regeneration, any change to `backend/src/`.

## Decisions

### D1 — The cohort is 22 SKUs, with the two Orion rows as a control group

**Decision.** Re-enrich an **enumerated** list of 22 SKUs: the 11 nulls, the 9 wrongly typed, and the 2 correctly typed false friends. Nineteen must change, one (SKU845) must stay null, and **two must not move**.

The enumeration lives here, not in a runtime query, so the run is reproducible and the report has a fixed subject.

| SKU | Name | `piece_type` before | Expected after |
|---|---|---|---|
| SKU498 | Diadema Calor del Volcán | `NULL` | `diadema` |
| SKU862 | Diadema Ola de Coral | `NULL` | `diadema` |
| SKU933 | Diadema Reflejo de Coral | `NULL` | `diadema` |
| SKU1082 | Diadema de Hilo de Plata y Oro | `NULL` | `diadema` |
| SKU1090 | Diadema Sueños de Plata | `NULL` | `diadema` |
| SKU617 | Diadema Luz de Luna | `broche` | `diadema` |
| SKU821 | Diadema Lira | `broche` | `diadema` |
| SKU1105 | Diadema Hilos de Encaje | `broche` | `diadema` |
| SKU658 | Diadema Resplandor Volcánico | `colgante` | `diadema` |
| SKU720 | Diadema Encanto de Hielo | `collar` | `diadema` |
| SKU843 | Diadema Virgo | `collar` | `diadema` |
| SKU844 | Gemelos Hércules | `NULL` | `gemelos` |
| SKU859 | Gemelos de Coral | `NULL` | `gemelos` |
| SKU500 | Gemelos Ardor Metálico | `broche` | `gemelos` |
| SKU667 | Gemelos Brasa Elegante | `broche` | `gemelos` |
| SKU415 | Llavero Cala Galdana | `NULL` | `llavero` |
| SKU417 | Llavero Cape Nao pequeño | `NULL` | `llavero` |
| SKU416 | Llavero Cape Nao Grande | `broche` | `llavero` |
| SKU936 | Cinturón Ola Dorada | `NULL` | `cinturon` |
| SKU845 | Joya del Zodiaco | `NULL` | **`NULL`** (correct: no term names it) |
| SKU822 | Broche **Cinturón de Orión** | `broche` | **`broche`** (control) |
| SKU882 | Anillo **Cinturón de Orión** | `anillo` | **`anillo`** (control) |

**Why not the eleven nulls the ficha asks for.** The facet would ship at 45 % for `diadema`, 50 % for `gemelos`, 67 % for `llavero`, and the nine impostors would stay. A dropdown offering "Diadema" and returning five of eleven is the failure `materials-vocabulary.test.ts` calls intolerable — *«"nothing of this in your shop", a sentence that would be false»* — in its worse form: it does not say zero, it says five. Cost of avoiding it: nine model calls.

**Why not the 1.200.** The ficha's reason stands and is respected. Diffuse reclassification, ~1.200 calls, and no review that covers them.

**Why the two Orion rows are re-enriched instead of excluded.** They are the only way to turn the largest risk of `v2` — that `cinturon` in the list drags a proper noun — from an assumption into a measurement. Excluding them to be safe would convert the change's most valuable check into a hope. If they move, the prompt is overfitted and we learn it **inside** the change.

### D2 — Acceptance is structural, not lexical

**Decision.** The ficha's *«buscar "diadema" pasa de cero a resultados»* is **not** used as an acceptance criterion. `diadema` already reaches 11 documents through C21's lexical branch, so that check passes before the change and a verifier would sign it green for the wrong reason — the C17 lesson in its subtlest form.

Acceptance is the table of before/after counts: nulls 11 → 1, `piece_type = 'diadema'` 0 → 11, impostors in `broche` 6 → 0, dropdown 8 → 12 options.

**Alternative considered:** keep the lexical criterion as a secondary smoke check. Rejected — a criterion that cannot fail teaches the reader that it was verified when nothing was.

### D3 — Canonical forms: `gemelos` plural, `cinturon` unaccented

**Decision.** `gemelos` (plural, like `pendientes`), `cinturon` (unaccented, like `pequeno`), `diadema`, `llavero`.

Plural reduction in `singular_candidates` strips `s`/`es`, so `diademas`, `llaveros` and `cinturones` resolve to their canonical on their own. It runs **singular←plural only**, so a typed `gemelo` cannot reach the plural canonical: that is the one case needing an overlay surface form (D6).

`cinturon` unaccented is not cosmetic. The panel value travels to `AND d.piece_type = :category`, compared by **exact equality**, so the `value` must be byte-for-byte the YAML canonical; the accent lives only in the human-readable label. The YAML is already inconsistent here (`latón` accented, `pequeno` not) and the accent-free precedent is the one that matters for a value used as a key.

**Alternative considered:** `gemelo` singular. Rejected — cufflinks are a pair, as earrings are, and `pendientes` set the house precedent.

### D4 — The prompt path derives from the version, and `v1.md` is preserved

**Decision.** `PROMPT_VERSION = "enrichment/v2"` and `_PROMPT_RELATIVE = Path("prompts") / f"{PROMPT_VERSION}.md"`. A new test asserts the loaded file's first line is `# ` + `PROMPT_VERSION`.

The failure this closes is not cosmetic. If the constant moves and the path does not, twenty-two profiles are stamped `enrichment/v2` while produced by `v1`, and the property that makes mixing prompt versions safe — *the problematic profile is the one that does not say which prompt produced it* — becomes false while looking true. Undetectable afterwards.

`v1.md` is neither edited nor deleted: 1.178 profiles keep declaring they came from it.

**Alternatives considered for the prompt's duplicated vocabulary block:**

| Option | Verdict |
|---|---|
| Keep the duplication, add a consistency test between the loaded prompt's list and the YAML | **Chosen.** Cheapest thing that turns silent drift into a red test, and the prompt stays a frozen artefact that `prompt_version` identifies |
| Render the block from the YAML at load time | **Rejected.** `prompt_version` would stop naming a fixed text: the same `v2` would send different content as the YAML changes, destroying the traceability the field exists for |
| Generate the file at build time, commit it, test that regeneration is a no-op | **Better, deferred.** One source and a frozen artefact — but generation infrastructure for four terms is out of proportion today |

### D5 — All four terms enter the frontend dropdown

**Decision.** `PIECE_TYPE_OPTIONS` grows to twelve, with `value` = canonical and `label` = human-readable («Cinturón» with its accent).

The deciding comparison is not against `broche` (85 documents) but against **`cadena`**: 7 products, carried in 6 of 11 points of sale, 2,8 per point of sale, shipped in that dropdown since C16 without anyone questioning it. `diadema` (11/11, 6,8), `gemelos` (11/11, 3,1) and `cinturon` (10/11) are comfortably above it; `llavero` (6/11, 1,5) ties it. **None of the four is a worse case than the one already accepted**, so excluding any would require explaining why `cadena` stays.

Marginal cost is zero: the mirror file must be touched anyway for its pinned test, and `assisted.tsx` maps over the constant.

Consequence to state, not hide: in the 5 points of sale without a keyring, the "Llavero" facet returns an empty list. That is correct behaviour and already true for `cadena`.

**Alternative considered:** ship only `diadema` and `gemelos`, defer the two small ones. Rejected — it introduces an unwritten population threshold that `cadena` already violates.

### D6 — The C20 overlay is in scope; `filigrana` is not

**Decision.** Remove the four terms from `exclusions`; rewrite `filigrana`'s reason so it no longer defers to this change; add class `piece_type / gemelos` with surface form `gemelo`. Do **not** add `tiara`.

The ficha lists the overlay as out of scope, but its four exclusions say *«pertenece a `fix-enrichment-vocabulary-gaps`»*. Once the gaps close, keeping them makes the file self-contradictory: a section whose purpose is to warn against what must not enter would be listing four base canonicals.

They are **deleted** rather than rewritten as "closed". The section's job is to show the rule where someone is tempted to break it; history lives in git and in the report.

`tiara` reaches **0 documents**. The overlay's own rule is that an entry without a number behind it does not go in, and `zarcillos` (also 0) was admitted as a cheap regional variant — a judgement call that does not extend to a term the corpus never uses.

`filigrana` stays out of the change: `style_tags` is a different axis with its own coverage gates in the auditor, and it reaches its 66 documents unexpanded.

### D7 — Four pinned tests fire; the guard test changes its example and is not deleted

**Decision.**

| Test | Action |
|---|---|
| `test_base_vocabulary_terms_are_pinned` | Extend the tuple to twelve terms |
| `materials-vocabulary.test.ts` | Extend the array and its description |
| `test_vocabulary_gaps_are_recorded_as_exclusions_not_smuggled_in` | Reduce the required set to the exclusions still alive: `piel`, `filigrana` |
| `test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` | **Swap `diadema` for `filigrana`** as the unknown canonical. **Do not delete** |

The fourth is the dangerous one: it fails with `DID NOT RAISE`, the opposite direction to the expected, so the reflex is to remove it. It is the guard that keeps a vocabulary gap from being smuggled in as a synonym — the mechanism that made this change visible in the first place. `filigrana` is the right replacement precisely because it is a real, still-open gap: the test goes on pointing at a live one instead of a closed one.

**Note on `synonyms.py`:** it is not modified. `_base_layer()` derives classes from the YAML, so `diadema`, `gemelos`, `cinturon` and `llavero` become query classes on their own. The error message in `_require_known_class` hardcodes this change's name; it stays, because it still names the sanctioned route for a future gap.

### D8 — The run happens inside the change, and `Force` is what makes it possible

**Decision.** The re-enrichment is executed as part of this change, not as a follow-up operation like C12's AutoBulk.

C12's run was 1.200 profiles and genuinely belonged outside a merge. This is 22 calls in one batch, and without executing it there is no report, no verdict on the control group, and no way to know whether the prompt overfitted. The change would ship a vocabulary nobody had exercised.

`SourceHash` is computed from the **product's own source text**, not from the profile, so it does not change on re-enrichment and the batch would be skipped: `request.Force` is mandatory, not optional. `reviewMode: AutoBulk` keeps the profiles `Approved` and therefore indexable. `MaxBatchSize = 50` fits all 22 in one call.

**Pre-flight check, to verify and not assume:** that no profile in the cohort has `ReviewedByUserId` or `ReviewedAt` set. `Upsert` clears them and logs `enrich_profile_review_reset`; all 1.200 were approved in bulk mode, so there should be none.

### D9 — The spec fixes `enrichment/v2` literally

**Decision.** The modified scenario reads `enrichment/v2`, not "the currently shipped prompt version".

It means every prompt bump requires a change. That is the intended discipline, and it is the reason this work is a change rather than a commit.

## Risks / Trade-offs

- **Two live specs are left false if their deltas are not emitted, and `--all --strict` stays green over both** → Emit both deltas as part of the change, and run the full gate — not the single-change form — before archiving. Worse than August's three malformed specs: those broke the format and the validator caught them; these would be well-formed and lying.
- **`test_overlay_anchor_absent_from_the_base_is_a_vocabulary_gap` fails in the opposite direction to the expected, inviting deletion** → D7 names the replacement example explicitly and the tasks say "swap, do not delete".
- **Re-enrichment with `v2` may move other fields of the 22** — materials, stone, tags — not just the type → The report publishes the **full diff**, not just `piece_type`. Twenty-two rows are reviewable by hand; that is a reason the cohort is small, not a reason to skip the review.
- **The control group may move** → That is the point of including it. If SKU822 or SKU882 changes, the prompt is overfitted, and the change stops to fix the brief rather than shipping a `cinturon` term that eats proper nouns.
- **Editing `v1.md` instead of creating `v2.md`** → Leaves 1.178 profiles declaring a provenance that can no longer be verified. Stated in D4 and enforced by a task that checks `v1.md` has no diff.
- **Bumping `PROMPT_VERSION` without deriving the path** → Silently stamps the wrong provenance. Closed structurally by D4 plus its test.
- **Running with `STUB_MODE=true`** → The batch returns the C08 stub cycle and the report would describe a fiction. The run requires `STUB_MODE=false` and `JPV_RAG_LLM_API_KEY`, with the container recreated per C12's runbook.
- **`ts_rank` shifts slightly** because 19 documents gain a `Tipo:` line → 1,6 % of the corpus, expected to be noise, but C21 was calibrated against a still corpus and this is stated rather than assumed.
- **Zone shared with C23** (`enrichment/`) **and C25** (`retrieval/`, through the overlay) → Not opened in parallel, even by the same person, per the plan's §1 rule.
- **Deadline** → Must land before C24 labels its baseline. `source-text/v1` would not betray the change, so a golden set labelled earlier would describe a corpus that no longer exists.

## Migration Plan

No schema migration, of either kind. The data movement is:

1. **Baselines first.** Record failing **test names** (not counts) for `uv run pytest` and for the frontend suite; both are red before this change is touched.
2. **Code and specs** land together: vocabulary, `v2.md`, version derivation, overlay, mirror, four pinned tests, four new tests, two spec deltas.
3. **Pre-flight:** confirm no cohort profile carries a human review; confirm `STUB_MODE=false` and the LLM key are live per C12's runbook.
4. **One batch** of 22 `productId` with `force: true`, `reviewMode: "AutoBulk"`.
5. **One incremental index sync.** Verify the number of re-embedded rows equals the number of profiles whose `doc_text` changed.
6. **Verify** the before/after table, including the control group, and the facet counts through the UI.
7. **Report** `fix1-vocabulary-gaps-measurements.md` with the full 22-row diff.

**Rollback.** The corpus movement is reversible without a backup: restore `v1.md` as the loaded prompt (revert `PROMPT_VERSION`), re-run the same 22 SKUs with `force: true`, and re-sync. The profiles return to `enrichment/v1` and `doc_text` to its previous content. Nothing else was written. Reverting the code alone, without re-running, leaves 22 profiles stamped `v2` in a repository whose `v2.md` no longer exists — so the re-run is part of the rollback, not optional.

## Open Questions

All resolved on 2026-09-05; recorded here because each had a real alternative.

| # | Question | Resolution |
|---|---|---|
| 1 | Which term replaces `diadema` as the unknown-canonical example in the guard test? | **`filigrana`** — the gap still open and documented as such in the overlay, so the test keeps pointing at a real one |
| 2 | What happens to the four terms removed from `exclusions`? | **Deleted from the file.** Their stated reason — "belongs to FIX1" — stops being true, and the section exists to warn, not to archive |
| 3 | Does the re-enrichment run inside the change or as a follow-up? | **Inside.** See D8: 22 calls, and without it there is no report and no verdict on the control group |
