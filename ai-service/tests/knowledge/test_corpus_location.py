"""Where the corpus is looked for, and why one search and not two. C39a.

**This file exists because the resolution was wrong for five weeks and nothing said so.**
`CORPUS_DIR` was built from `Path(__file__).resolve().parents[3].parent`, which is correct for a
developer checkout and lands inside the dependency tree once the package is installed with
`uv sync --no-editable`: measured in the deployed container on 2026-09-27, the corpus was looked
for at `/app/.venv/lib/data/knowledge`. The demo kept working only because the indexed fragments
live in the database volume and C34 had copied the files onto that path by hand, uncommitted.

The fix is the search `assist/prompt.load_prompt_file` already performs, and these tests pin the
two halves that matter: that an installed layout is covered, and that the resolution never raises
at import.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jbg_ai.knowledge import constants
from jbg_ai.knowledge.constants import CORPUS_DIR


def test_the_corpus_resolves_to_a_real_directory_in_this_checkout() -> None:
    """The first candidate wins in a developer checkout, which is what the suite runs in."""
    assert CORPUS_DIR.is_dir()
    assert (CORPUS_DIR / "material-plata.md").is_file()


def test_the_candidates_cover_the_installed_container_layout() -> None:
    """`/app/data/knowledge` is among them, which is the whole point of the change.

    Without this candidate an installed package looks inside its own virtual environment, and
    the failure is silent: the indexer simply finds nothing to index.
    """
    assert Path("/app") / "data" / "knowledge" in constants._CORPUS_CANDIDATES
    assert constants.REPO_ROOT / "data" / "knowledge" in constants._CORPUS_CANDIDATES


def test_resolution_prefers_the_first_candidate_that_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Order decides, so a checkout is never served a stale copy from somewhere else."""
    second = tmp_path / "second" / "data" / "knowledge"
    second.mkdir(parents=True)
    third = tmp_path / "third" / "data" / "knowledge"
    third.mkdir(parents=True)

    monkeypatch.setattr(
        constants,
        "_CORPUS_CANDIDATES",
        (tmp_path / "missing" / "data" / "knowledge", second, third),
    )

    assert constants._resolve_corpus_dir() == second


def test_resolution_never_raises_when_no_candidate_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing corpus must not take the service down at import.

    This runs while the module is imported, so raising here would stop `/health` answering and
    present a corpus problem as a total outage. `discover_documents` raises instead, with the
    directory named, which is where the failure is actionable.
    """
    absent = tmp_path / "nowhere" / "data" / "knowledge"
    monkeypatch.setattr(constants, "_CORPUS_CANDIDATES", (absent,))

    assert constants._resolve_corpus_dir() == absent


def test_the_derived_paths_hang_off_the_resolved_directory() -> None:
    """The sidecar and the out-of-domain fixture follow the corpus and are not resolved apart."""
    assert constants.SIDECAR_PATH.parent == CORPUS_DIR
    assert constants.OUT_OF_DOMAIN_PATH.parent.parent == CORPUS_DIR
