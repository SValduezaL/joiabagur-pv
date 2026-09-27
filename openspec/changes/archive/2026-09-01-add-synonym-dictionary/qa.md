# QA — add-synonym-dictionary (C20)

## 1. Gates

| Check | Result |
|---|---|
| `uv run pytest` (`ai-service`) | **510 passed**, 0 failed — baseline before the change was 474; 508 at the end of the apply, plus the two pinning tests `/opsx:verify` asked for |
| `openspec validate --all --strict` | **48 passed, 0 failed** |
| `openspec status --change add-synonym-dictionary` | 4/4 artifacts, **27/27 tasks** |
| Provider / LLM / RDS calls in the suite | none — the expansion is pure and `test_expansion_makes_no_database_or_provider_call` pins it |

## 2. The cut line held

`git diff --stat` over the ticket's "explicitly untouched" list is **empty**:

```
ai-service/src/jbg_ai/enrichment/vocabularies.yaml
ai-service/src/jbg_ai/indexing/          (embeddings.py, source_text.py included)
ai-service/openapi.json
ai-service/migrations/
backend/
frontend/
```

No Alembic revision, no EF Core migration, no PostgreSQL extension installed, no text-search
configuration created, no document re-indexed. `AiGateway:RetrievalTimeoutMs` is still 2500 ms:
the embedding-client singleton stays with C21/C22 in `openspec/DEFERRED_TASKS.md`, and C20 adds
no provider call, so it neither worsens nor fixes that budget.

## 3. Measured reach, reproduced

`python -m jbg_ai.retrieval measure` against the live index (1.168 active rows), report committed
at [`ai-service/evals/results/c20-query-expansion-reach.md`](../../../../ai-service/evals/results/c20-query-expansion-reach.md):

| query | without expansion | with expansion |
|---|---:|---:|
| `gargantilla dorada` | 0 | **64** |
| `collares de plata` | 0 | **66** |
| `criollas de oro` | 1 | **102** |
| `sortija de plata` | 3 | **144** |
| `aros de plata` | 22 | **205** |

The five figures the design predicted are reproduced exactly. `brazalete de cuero` stays 0 → 0,
which is honest rather than broken: `cuero` has one product in the whole catalogue.

## 4. Three findings the apply produced

### 4.1 The base covered more than the ficha assumed — and less in two places nobody had named

Probed before curating anything: `sortija`, `alianza`, `gargantilla`, `brazalete`, `esclava`,
`criollas`, `bano de oro`, `chapado en oro` and every regular plural already matched through the
base plus singularisation. Two did not, and both matter:

- **`pendiente` in the singular** — the base only carries the plural canonical, 275 documents, so
  an operator typing the singular of the commonest piece type matched nothing.
- **`dorada` in the feminine** — which is half of `gargantilla dorada`, the headline query.

Both went into the overlay. Roughly ten entries the ficha listed turned out not to be needed at
all, because singularisation on both sides covers them.

### 4.2 The vocabulary bridge had to become directional, and the first measurement is why

The first run reported `bano de oro` **0 → 436**, a number the design had not predicted. Cause: a
symmetric union meant a query for the plating also matched every solid-gold piece. Measured:

| group | products | average price |
|---|---:|---:|
| what was asked for (`baño de oro` / `dorado`) | 154 | 420 € |
| what the symmetric bridge added (solid `oro` only) | **282** | **587 €** |

In a jewellery shop that is the wrong direction: the operator named the cheaper finish and got the
dearer one in the candidate set. But the reverse direction earns its place — measured on
`gargantilla dorada`, `dorado` alone gives 22, `dorado | baño de oro` still 22, and the full union
64, so the whole gain comes from `oro`. A gold-**coloured** necklace is gold-coloured either way.

Bridges are now declared per direction. `bano de oro` lands at 154 and the five design figures are
unchanged. The spec gained the requirement *Bridges between vocabularies are directional*, with a
second scenario for the leak found while fixing it: donations are taken from a snapshot of the
classes as they stood **before any bridge ran**, because otherwise a first bridge widening the
colour towards `oro` lets a second bridge carry `oro` back into the plating transitively.

### 4.3 A bug of exactly the kind the design predicted

The first deduplicator collapsed group members with `fold()`. Since `fold()` strips the `ñ`, the
typed form `bano de oro` **suppressed** the accented `baño de oro` — leaving the group without the
only form that reaches those 38 documents, which is the entire purpose of the entry. The same bug
silently dropped `pequeño` from its class.

Deduplication is now by case and never by folding, with the reason written where the temptation is.
This is design decision D4 biting in practice within an hour of being written down.

## 5. Two spec corrections the code forced

| Was | Is | Why |
|---|---|---|
| Stemmer-split terms "MUST be declared in the overlay" | The group MUST contain both surface forms; overlay entry or plural reduction is an implementation detail | `collares` needs no entry: singularisation plus emitting the typed form already yields `['collares', 'collar']`. The requirement was specifying the mechanism instead of the outcome |
| "The overlay MAY create new classes" | Every overlay anchor MUST name a canonical the base defines, and loading MUST fail otherwise | A canonical the base does not know is a **vocabulary gap**, not a synonym. The loader now rejects it at startup naming `fix-enrichment-vocabulary-gaps`, which makes structural a rule that was only a test |

## 6. Verified by hand

- `python -m jbg_ai.retrieval measure` with `JPV_PG*` unset → `skipping measurement: Missing
  environment variables: …`, **exit 0**. A development aid must not fail on a laptop with no Docker.
- `plainto_tsquery('spanish','de') && plainto_tsquery('spanish','plata')` → `'plat'`. PostgreSQL
  absorbs a stop-word-only group on either side of `&&`, so the composition needs no filtering —
  useful for C21.
- The retrieval response is identical with the flag on and off, asserted in
  `test_response_is_unchanged_while_expansion_has_no_consumer`. Until C21 reads the groups, C20
  changes nothing an API client can observe except one log line.

## 6bis. Latency and load, measured after implementing

Measured with `/opsx:verify` on 2026-09-01, after the code existed rather than before:

| Case | Per call |
|---|---:|
| `gargantilla dorada` | 0,022 ms |
| `sortija de plata` | 0,036 ms |
| `un anillo de plata para regalar` | 0,073 ms |
| `pendientes de oro con piedra azul` | 0,088 ms |
| 500 characters — the contract maximum | **1,76 ms** |

The ticket's original target of "< 1 ms" holds for operator traffic with three orders of magnitude
to spare, and **does not hold at the 500-character maximum** — a query nobody types, and still
noise beside the 170–1707 ms the embedding costs. The ticket now states the measured figures
instead of the estimate.

**Loading the dictionary costs 28,3 ms, once per process, and the first search pays it — not boot.**
That is deliberate: pre-loading would make `GET /health` pay for a dictionary it never reads, and
the heartbeat must stay cheap (S16: *"no confundáis el latido con la vigilancia"*). Against a cold
embedding round trip of 1707 ms it is invisible.
`test_health_does_not_load_the_synonym_dictionary` pins it, and the guard is not vacuous: calling
the loader moves `cache_info().currsize` from 0 to 1, which is what the assertion reads.

## 6ter. The two scenarios that were only verified by hand now have tests

`/opsx:verify` reported both as structurally true but unpinned. Closed:

| Scenario | Test |
|---|---|
| `Health starts without the expansion flag` — "no synonym dictionary is loaded" | `tests/api/test_health.py::test_health_does_not_load_the_synonym_dictionary` |
| `The flag is not part of the request contract` — "no expansion field" | `tests/api/test_contracts.py::test_query_expansion_is_not_part_of_the_request_contract` |

The second pins the whole field set of `RetrievalRequest`, not just the absence of an expansion
name, so any future addition to the frozen request has to be a deliberate act.

**Also verified, and not in any task:** `query_synonyms.yaml` travels inside the built wheel
(`jbg_ai/retrieval/query_synonyms.yaml`, beside `vocabularies.yaml` and `sku_provenance.json`).
Checked by building the package, because an editable install resolves the file from the source
tree and would have hidden a container that crashes on the first `expand_query`.

## 7. What C20 deliberately did not do

The expansion **is not consumed**. It is computed on every real retrieval, logged as
`stage=expand` with `consumed=False`, and discarded. That is the honest shape given `openapi.json`
is frozen (no endpoint could expose it) and C24 sits two changes downstream. The alternative was a
library that never executes once — the signature this project has chased since C17.

Rollback is `JPV_QUERY_EXPANSION_ENABLED=false`, and since nothing consumes the groups yet, even
that is belt-and-braces.
