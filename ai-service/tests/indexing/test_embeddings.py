"""Embedding port, cache, dimension, LiteLLM adapter. Delivered by C11."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from jbg_ai.indexing.constants import DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIM, SOURCE_TEXT_VERSION
from jbg_ai.indexing.embeddings import LiteLlmEmbeddingClient, document_version_key, model_version_key
from jbg_ai.indexing.errors import EmbeddingConfigError, EmbeddingDimensionError
from support.fake_embedding_client import FakeEmbeddingClient
from support.paths import AI_SERVICE_ROOT


def test_embedding_client_exposes_distinct_version_keys() -> None:
    fake = FakeEmbeddingClient()

    assert fake.model_id == DEFAULT_EMBEDDING_MODEL
    assert fake.document_version_key == f"{DEFAULT_EMBEDDING_MODEL}:{EMBEDDING_DIM}:{SOURCE_TEXT_VERSION}"
    assert fake.model_version_key == f"{DEFAULT_EMBEDDING_MODEL}:{EMBEDDING_DIM}"
    assert fake.document_version_key == document_version_key(DEFAULT_EMBEDDING_MODEL)
    assert fake.model_version_key == model_version_key(DEFAULT_EMBEDDING_MODEL)

    result = asyncio.run(fake.embed(["anillo de plata"]))
    assert result.embedding_model == DEFAULT_EMBEDDING_MODEL
    assert result.embedding_version == fake.document_version_key
    assert result.embedding_version != fake.model_version_key
    assert len(result.vectors) == 1
    assert len(result.vectors[0]) == EMBEDDING_DIM


def test_embedding_not_recomputed_when_hash_unchanged() -> None:
    fake = FakeEmbeddingClient()
    text = "SKU: SKU01\nNombre: Anillo"

    first = asyncio.run(fake.embed([text]))
    second = asyncio.run(fake.embed([text]))

    assert fake.call_count == 1
    assert first.cache_hits == 0
    assert second.cache_hits == 1
    assert first.vectors == second.vectors


def test_vector_dimension_mismatch_is_rejected() -> None:
    fake = FakeEmbeddingClient(dimension=384)

    with pytest.raises(EmbeddingDimensionError, match="384"):
        asyncio.run(fake.embed(["anillo"]))

    fake_3072 = FakeEmbeddingClient(dimension=3072)
    with pytest.raises(EmbeddingDimensionError, match="3072"):
        asyncio.run(fake_3072.embed(["anillo"]))


def test_embedding_batch_is_split_by_setting() -> None:
    fake = FakeEmbeddingClient(batch_size=64)
    texts = [f"text-{index}" for index in range(70)]

    result = asyncio.run(fake.embed(texts))

    assert len(result.vectors) == 70
    assert fake.call_count == 2
    assert all(len(batch) <= 64 for batch in fake.provider_calls)
    assert len(fake.provider_calls[0]) == 64
    assert len(fake.provider_calls[1]) == 6


def test_adapter_does_not_import_data_or_enrich_llm() -> None:
    source_path = AI_SERVICE_ROOT / "src" / "jbg_ai" / "indexing" / "embeddings.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert "from litellm import" in source or any(
        name == "litellm" or name.startswith("litellm") for name in imported
    )
    assert "jbg_ai.data" not in imported and "jbg_ai.data" not in source
    assert "jbg_ai.enrichment.llm" not in imported and "jbg_ai.enrichment.llm" not in source
    assert "OpenAICatalogLlm" not in source
    assert "LiteLlmEnrichClient" not in source


def test_embed_without_key_fails_without_using_rag_llm_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JPV_RAG_LLM_API_KEY", "sk-rag-must-not-be-used")
    calls: list[list[str]] = []

    async def _batch(texts: list[str]) -> list[list[float]]:
        calls.append(list(texts))
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    client = LiteLlmEmbeddingClient(api_key=None, embed_batch=_batch)
    with pytest.raises(EmbeddingConfigError, match="JPV_EMBEDDING_API_KEY"):
        asyncio.run(client.embed(["anillo"]))

    client_blank = LiteLlmEmbeddingClient(api_key="   ", embed_batch=_batch)
    with pytest.raises(EmbeddingConfigError, match="JPV_EMBEDDING_API_KEY"):
        asyncio.run(client_blank.embed(["anillo"]))

    assert calls == []


def test_validation_4xx_is_not_retried() -> None:
    calls = {"n": 0}

    async def _batch(texts: list[str]) -> list[list[float]]:
        _ = texts
        calls["n"] += 1
        error = RuntimeError("bad request")
        error.status_code = 400  # type: ignore[attr-defined]
        raise error

    sleeps: list[float] = []

    async def _sleep(delay: float) -> None:
        sleeps.append(delay)

    client = LiteLlmEmbeddingClient(api_key="sk-test", embed_batch=_batch, sleep=_sleep)
    with pytest.raises(RuntimeError, match="bad request"):
        asyncio.run(client.embed(["anillo"]))

    assert calls["n"] == 1
    assert sleeps == []


def test_retry_on_429() -> None:
    calls = {"n": 0}

    async def _batch(texts: list[str]) -> list[list[float]]:
        calls["n"] += 1
        if calls["n"] == 1:
            error = RuntimeError("rate limited")
            error.status_code = 429  # type: ignore[attr-defined]
            raise error
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    sleeps: list[float] = []

    async def _sleep(delay: float) -> None:
        sleeps.append(delay)

    client = LiteLlmEmbeddingClient(api_key="sk-test", embed_batch=_batch, sleep=_sleep)
    result = asyncio.run(client.embed(["anillo"]))

    assert calls["n"] == 2
    assert sleeps == [0.25]
    assert len(result.vectors[0]) == EMBEDDING_DIM


def test_retry_on_5xx() -> None:
    calls = {"n": 0}

    async def _batch(texts: list[str]) -> list[list[float]]:
        calls["n"] += 1
        if calls["n"] == 1:
            error = RuntimeError("provider unavailable")
            error.status_code = 500  # type: ignore[attr-defined]
            raise error
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    sleeps: list[float] = []

    async def _sleep(delay: float) -> None:
        sleeps.append(delay)

    client = LiteLlmEmbeddingClient(api_key="sk-test", embed_batch=_batch, sleep=_sleep)
    result = asyncio.run(client.embed(["anillo"]))

    assert calls["n"] == 2
    assert sleeps == [0.25]
    assert len(result.vectors[0]) == EMBEDDING_DIM


def test_main_does_not_import_indexing() -> None:
    source = Path(
        __import__("jbg_ai.api.main", fromlist=["main"]).__file__
    ).read_text(encoding="utf-8")
    assert "jbg_ai.indexing" not in source


def test_lifespan_reaches_the_drain_without_the_provider_sdk() -> None:
    """C41 moved the lifespan out of `main.py`; the guard follows it rather than losing it.

    The application must be able to start a POS drain, and the drain lives in `jbg_ai.indexing`,
    so `main.py` alone could no longer carry the whole rule. The property being protected was
    never "main.py mentions no string": it is that **no provider SDK enters the import graph of
    a process whose job is to answer HTTP**. The POS drain embeds nothing and needs no embedding
    key, so it can be reached without `indexing.embeddings` — and this asserts that it is.
    """
    from jbg_ai.api import lifespan as api_lifespan

    source = Path(api_lifespan.__file__).read_text(encoding="utf-8")
    assert "jbg_ai.indexing.embeddings" not in source
    assert "jbg_ai.indexing.cli" not in source
    assert "jbg_ai.data" not in source

    # The reachable path, checked one hop further: the scheduler must not pull the CLI in
    # either, because the CLI is what imports the embedding client.
    from jbg_ai.indexing import scheduler

    scheduler_source = Path(scheduler.__file__).read_text(encoding="utf-8")
    assert "jbg_ai.indexing.cli" not in scheduler_source
    assert "jbg_ai.indexing.embeddings" not in scheduler_source


def test_index_routes_use_catalog_principal() -> None:
    source = (
        AI_SERVICE_ROOT / "src" / "jbg_ai" / "api" / "routers" / "index.py"
    ).read_text(encoding="utf-8")
    assert "get_catalog_principal" in source
    assert "require_stub_mode" not in source
    assert "jbg_ai.indexing" in source


def test_unit_suite_makes_no_provider_calls(forbid_network: None) -> None:
    _ = forbid_network
    from jbg_ai.api import main as api_main

    source = Path(api_main.__file__).read_text(encoding="utf-8")
    assert "jbg_ai.indexing" not in source
    assert "jbg_ai.data" not in source
