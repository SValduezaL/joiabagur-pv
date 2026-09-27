"""Constants and filesystem anchors of the knowledge corpus. Delivered by C23."""

from __future__ import annotations

import uuid
from pathlib import Path

#: `ai-service/src/jbg_ai/knowledge/constants.py` → ai-service/
#:
#: **Correct for a developer checkout and wrong once the package is installed**, which is why
#: it is no longer what `CORPUS_DIR` is built from. Kept because the first candidate below is
#: exactly this, and naming it makes that candidate readable.
AI_SERVICE_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = AI_SERVICE_ROOT.parent

#: Where the corpus is looked for, in order. **Same three candidates and same reason as
#: `assist/prompt.load_prompt_file`**, whose docstring says it: one search, so that a container
#: layout cannot diverge from a developer checkout.
#:
#: The defect this replaces was measured on 2026-09-27 inside the running demo container. With
#: `uv sync --no-editable` the package is installed into the virtual environment, so
#: `Path(__file__)` is `/app/.venv/lib/python3.11/site-packages/jbg_ai/knowledge/constants.py`,
#: `parents[3]` climbs to `/app/.venv/lib/python3.11` and the corpus was therefore looked for at
#: **`/app/.venv/lib/data/knowledge`** — a path inside the dependency tree that nothing puts
#: anything into. `PROMPTS_DIR` has the identical flaw and gets away with it precisely because
#: `load_prompt_file` does not use it: it searches. The corpus had no search, so C34 had to copy
#: the files onto that absurd path by hand on the host, uncommitted, and it survived five weeks
#: only because the indexed fragments live in the database volume.
_CORPUS_RELATIVE = Path("data") / "knowledge"
_CORPUS_CANDIDATES = (
    REPO_ROOT / _CORPUS_RELATIVE,  # developer checkout: …/ai-service/../data/knowledge
    Path.cwd() / _CORPUS_RELATIVE,
    Path("/app") / _CORPUS_RELATIVE,  # the container's WORKDIR
)


def _resolve_corpus_dir() -> Path:
    """The first candidate that is a directory, or the checkout one so the path is always named.

    **Deliberately does not raise.** This runs at import, and a corpus that is missing must not
    take the whole service down with it: `/health` would stop answering and a corpus problem would
    present as a total outage. `discover_documents` already raises with the directory named, which
    is where the failure belongs and where it is actionable.
    """
    for candidate in _CORPUS_CANDIDATES:
        if candidate.is_dir():
            return candidate
    return _CORPUS_CANDIDATES[0]


#: The corpus itself, versioned in git. That it lives in the repository is what makes a
#: citation *locate*: `material-plata#cuidados-y-limpieza-en-casa` opens a file and a heading.
CORPUS_DIR = _resolve_corpus_dir()

#: Machine-readable record of how the corpus was produced, in the pattern of
#: `data/catalog/*/generated/*.meta.json`.
SIDECAR_PATH = CORPUS_DIR / "_corpus.meta.json"

#: Questions whose correct answer is **no citation at all**. Versioned beside the corpus
#: because they are part of what the corpus claims about itself.
OUT_OF_DOMAIN_PATH = CORPUS_DIR / "_eval" / "out-of-domain.yaml"

PROMPT_VERSION = "knowledge/v1"
GENERATOR_VERSION = "c23-knowledge/v1"

#: Value written to `ai.knowledge_chunk.embedding_version`, alongside the model and the
#: dimension. **Never `SOURCE_TEXT_VERSION`**: that one versions the product text renderer.
#: Sharing it would mean a change to the product text marks the whole knowledge corpus
#: stale — waste, but visible — and, far worse, that a change to *these* chunking rules
#: would NOT invalidate anything, leaving vectors that declare themselves current while
#: describing a text that no longer exists.
KNOWLEDGE_PREPROCESSING_VERSION = "knowledge/v1"

#: Namespace of the deterministic identifiers. Fixed forever: regenerating it would
#: repoint every citation in the database at once.
KNOWLEDGE_NAMESPACE = uuid.UUID("6d3f0d9a-8f1f-5f4a-9d2b-7c0a1e6b4f21")

#: The five values `ck_knowledge_document_doc_type` admits, of which this corpus uses four.
SCHEMA_DOC_TYPES = frozenset({"material", "talla", "guion_venta", "politica", "faq"})

#: `guion_venta` is **excluded by design, not by scope**: an imperative fragment retrieved
#: into a prompt is indistinguishable from an instruction, which would make the corpus
#: itself an injection surface. See `design.md` D13.
FORBIDDEN_DOC_TYPE = "guion_venta"
ALLOWED_DOC_TYPES = frozenset(SCHEMA_DOC_TYPES - {FORBIDDEN_DOC_TYPE})

#: Two values because they are two behaviours. A label that does not change behaviour is
#: decoration; `establecimiento` is never read to a customer without confirming it.
CLAIM_SCOPE_GENERAL = "general"
CLAIM_SCOPE_ESTABLISHMENT = "establecimiento"
CLAIM_SCOPES = frozenset({CLAIM_SCOPE_GENERAL, CLAIM_SCOPE_ESTABLISHMENT})

#: Hard ceiling on one section, in characters. Above it ingestion **fails**; the code
#: never splits a section by itself, because an automatic split produces a fragment with
#: no heading of its own — that is, a citation that resolves and does not locate.
MAX_SECTION_CHARS = 1200

#: Files under `CORPUS_DIR` that are not documents.
NON_DOCUMENT_STEMS = frozenset({"README"})

#: Rings that can be resized, and the three materials that cannot. Stated here because
#: three separate documents must agree on it and a test compares them.
RESIZABLE_MATERIALS = ("plata", "oro")
NON_RESIZABLE_MATERIALS = ("baño de oro", "latón", "acero")
NON_RESIZABLE_PHRASE = "no se ajusta de talla"

#: Letters of `size_label` that the catalogue does not stock. They are in the equivalence
#: table anyway, marked as available to order: the convention explains them instead of
#: pretending they do not exist.
TO_ORDER_SIZE_LETTERS = ("XXS", "XXL")

#: Words that describe the scale of a motif. They are `size_label` terms too, and they are
#: **never** a ring fit label.
MOTIF_SCALE_WORDS = ("mini", "extramini", "pequeño", "mediano", "grande")

#: `circunferencia (mm) = talla española + 40`, the ordinary Spanish relation. Verifiable
#: outside the jewellery, which is why the section stating it is scoped `general` while the
#: section assigning letters to ranges is scoped `establecimiento`.
SPANISH_SIZE_TO_CIRCUMFERENCE_OFFSET = 40
