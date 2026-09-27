"""Real POST /v1/retrieval/products: fused branches, 503 vs abstention. C14 + C21."""

from __future__ import annotations

import logging
from collections.abc import Callable
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from jbg_ai.api.main import create_app
from jbg_ai.api.schemas.retrieval import RetrievalResponse
from jbg_ai.indexing.errors import EmbeddingError
from support.fake_embedding_client import FakeEmbeddingClient
from support.fake_product_search import FakeIndexedRow, FakeProductSearch
from support.settings import OTHER_POS_ID, TOKEN_POS_ID, build_settings

A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FAMILY = UUID("11111111-1111-1111-1111-111111111111")


def _row(**kwargs) -> FakeIndexedRow:
    values = {
        "product_id": kwargs.pop("product_id", A),
        "sku": kwargs.pop("sku", "JBG-0001"),
        "distance": kwargs.pop("distance", 0.2),
        "materials": kwargs.pop("materials", ["plata"]),
        "family_id": kwargs.pop("family_id", FAMILY),
        "piece_type": kwargs.pop("piece_type", "anillo"),
        "doc_text": kwargs.pop("doc_text", "Tipo: anillo. Materiales: plata."),
    }
    values.update(kwargs)
    return FakeIndexedRow(**values)


def _real_app(
    *,
    search: FakeProductSearch | None = None,
    embed: FakeEmbeddingClient | None = None,
    **settings_overrides,
):
    settings = build_settings(stub_mode=False, **settings_overrides)
    app = create_app(settings)
    app.state.retrieval_embed = embed if embed is not None else FakeEmbeddingClient()
    app.state.retrieval_search = search if search is not None else FakeProductSearch([_row()])
    return app


def test_stub_mode_still_returns_fixtures(issue_token: Callable[..., str]) -> None:
    embed = FakeEmbeddingClient()
    search = FakeProductSearch([_row()])
    app = create_app(build_settings(stub_mode=True))
    app.state.retrieval_embed = embed
    app.state.retrieval_search = search
    token = issue_token()
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo de plata", "top_k": 2},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    parsed = RetrievalResponse.model_validate(body)
    assert parsed.candidates_returned == 6
    assert parsed.results[0].product_id.startswith("P-")
    assert embed.call_count == 0
    assert search.search_calls == []
    assert search.count_calls == []


def test_missing_embedding_key_is_503(issue_token: Callable[..., str]) -> None:
    settings = build_settings(
        stub_mode=False,
        jpv_embedding_api_key=None,
        database_url="postgresql+psycopg://u:p@db:5432/jpv",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )
        health = client.get("/health")

    assert response.status_code == 503
    assert "JPV_EMBEDDING_API_KEY" in response.json()["detail"]
    assert health.status_code == 200
    assert "low_confidence" not in response.json()


def test_missing_database_url_is_503(issue_token: Callable[..., str]) -> None:
    settings = build_settings(
        stub_mode=False,
        jpv_embedding_api_key="sk-test",
        database_url=None,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )
        health = client.get("/health")

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
    assert health.status_code == 200
    assert "low_confidence" not in response.json()


def test_empty_compatible_index_is_503_not_abstention(
    issue_token: Callable[..., str],
) -> None:
    app = _real_app(search=FakeProductSearch(compatible_count=0))
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 503
    assert response.json().get("low_confidence") is None


def test_real_mode_is_not_501(issue_token: Callable[..., str]) -> None:
    app = _real_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo de plata", "top_k": 5},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 200
    parsed = RetrievalResponse.model_validate(response.json())
    assert parsed.results
    assert sorted(parsed.results[0].match_reasons) == ["lexical", "vector"]
    assert parsed.results[0].score == 1.0
    assert parsed.low_confidence is False
    assert parsed.effective_pos_id == TOKEN_POS_ID


def test_token_without_pos_id_is_served_without_the_prefilter(
    issue_token: Callable[..., str],
) -> None:
    """C40 reverses the 401 this test used to assert, and the reversal is the point.

    It was right when written: with `pos_id` the retriever's only hard filter, a token without
    one had no business here. What C40 adds is a search deliberately spread over every shop,
    which has no shop to name — and the guarantee that keeps it safe is the one asserted below:
    the absent claim makes the prefilter **not apply**, and the response echoes the absence
    instead of substituting a value for it.
    """
    app = _real_app()
    token = issue_token(pos_id=None)
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["effective_pos_id"] == "", (
        "the absence is echoed, never a substituted value"
    )


def test_body_pos_id_is_ignored(issue_token: Callable[..., str]) -> None:
    app = _real_app()
    token = issue_token(pos_id=TOKEN_POS_ID)
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1, "pos_id": OTHER_POS_ID},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["effective_pos_id"] == TOKEN_POS_ID


def test_invalid_family_id_is_422(issue_token: Callable[..., str]) -> None:
    app = _real_app()
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={
                "query": "anillo",
                "top_k": 1,
                "filters": {"family_id": "not-a-uuid"},
            },
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 422


def test_every_mode_answers_and_the_c21_placeholder_note_is_gone(
    issue_token: Callable[..., str],
) -> None:
    token = issue_token()
    for body in (
        {"query": "anillo", "top_k": 1},
        {"query": "anillo", "top_k": 1, "mode": "hybrid"},
        {"query": "anillo", "top_k": 1, "mode": "lexical"},
        {"query": "anillo", "top_k": 1, "mode": "vector"},
    ):
        with TestClient(_real_app()) as client:
            response = client.post(
                "/v1/retrieval/products",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200, response.text
        for item in response.json()["results"]:
            assert "vector_only_until_c21" not in item["debug"]["notes"]


def test_lexical_mode_makes_no_provider_call(issue_token: Callable[..., str]) -> None:
    embed = FakeEmbeddingClient()
    app = _real_app(embed=embed)
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1, "mode": "lexical"},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 200
    assert embed.provider_calls == []
    assert response.json()["results"][0]["match_reasons"] == ["lexical"]


def test_provider_failure_degrades_to_the_lexical_branch(
    issue_token: Callable[..., str],
) -> None:
    class _Boom(FakeEmbeddingClient):
        async def embed(self, texts: list[str]):
            raise EmbeddingError("provider down")

    app = _real_app(embed=_Boom())
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert all("vector" not in item["match_reasons"] for item in results)


def test_provider_failure_with_nothing_lexical_to_serve_is_503(
    issue_token: Callable[..., str],
) -> None:
    """A 200 with an empty list would be indistinguishable from a legitimate abstention."""

    class _Boom(FakeEmbeddingClient):
        async def embed(self, texts: list[str]):
            raise EmbeddingError("provider down")

    app = _real_app(
        search=FakeProductSearch([_row(doc_text="Tipo: broche. Materiales: laton.")]),
        embed=_Boom(),
    )
    with TestClient(app) as client:
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": f"Bearer {issue_token()}"},
        )

    assert response.status_code == 503
    assert "low_confidence" not in response.json()


def test_retrieval_embed_client_is_a_process_singleton() -> None:
    """C21 pays half the debt of `openspec/DEFERRED_TASKS.md`: one client, bounded cache."""
    from jbg_ai.api.main import create_app
    from jbg_ai.retrieval.cache import BoundedEmbeddingCache

    app = create_app(
        build_settings(
            stub_mode=False,
            jpv_embedding_api_key="sk-test",
            database_url="postgresql+psycopg://u:p@db:5432/jpv",
        )
    )
    first = app.state.retrieval_embed
    second = create_app(
        build_settings(
            stub_mode=False,
            jpv_embedding_api_key="sk-test",
            database_url="postgresql+psycopg://u:p@db:5432/jpv",
        )
    ).state.retrieval_embed

    assert first is not None
    assert first is app.state.retrieval_embed, "resolved per request, built once per process"
    assert isinstance(first.cache, BoundedEmbeddingCache)
    assert first.cache.max_entries > 0
    assert first is not second, "one app, one client"


def test_trace_id_appears_in_stage_logs(
    issue_token: Callable[..., str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = _real_app()
    logging.getLogger().addHandler(caplog.handler)
    token = issue_token(trace_id="trace-c14")
    with caplog.at_level(logging.INFO, logger="jbg_ai.retrieval.orchestrator"):
        with TestClient(app) as client:
            response = client.post(
                "/v1/retrieval/products",
                json={"query": "anillo", "top_k": 1},
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    messages = [record.getMessage() for record in caplog.records]
    for stage in ("embed", "search", "lexical", "filters", "fuse"):
        assert any(f"stage={stage} " in msg and "trace-c14" in msg for msg in messages), stage
