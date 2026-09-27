"""Enriched `GET /health`: database, index, provider and model contrast (C17).

No database, no embedding provider, no network. The probe is injected on
`app.state`, the same idiom the retrieval and index routers already use.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from jbg_ai.api.main import create_app
from jbg_ai.indexing.constants import DEFAULT_EMBEDDING_MODEL
from support.fake_health_probe import FakeHealthProbe
from support.settings import build_settings

OTHER_MODEL = "openai/text-embedding-3-large"


def _app(probe: FakeHealthProbe, **settings_overrides):
    app = create_app(build_settings(**settings_overrides))
    app.state.health_probe = probe
    return app


def test_health_reports_database_index_and_provider() -> None:
    probe = FakeHealthProbe(documents=1200, models=(DEFAULT_EMBEDDING_MODEL,))
    app = _app(probe, jpv_embedding_api_key="an-embedding-key")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OK"
    assert body["database"] == "ok"
    assert body["index"]["documents"] == 1200
    assert body["index"]["model"] == DEFAULT_EMBEDDING_MODEL
    assert body["index"]["status"] == "ok"
    assert body["provider"] == "configured"


def test_health_reports_missing_provider_credential_without_failing() -> None:
    probe = FakeHealthProbe(documents=10, models=(DEFAULT_EMBEDDING_MODEL,))
    app = _app(probe, jpv_embedding_api_key=None)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["provider"] == "missing"


def test_health_reports_model_mismatch_when_index_disagrees() -> None:
    """The quietest failure of the whole deployment, made loud.

    Querying with a model other than the one that produced the indexed vectors
    compares two vector spaces: results are noise, the status code is 200, and
    nothing is logged anywhere.
    """
    probe = FakeHealthProbe(documents=1200, models=(OTHER_MODEL,))
    app = _app(
        probe,
        jpv_embedding_api_key="an-embedding-key",
        jpv_embedding_model=DEFAULT_EMBEDDING_MODEL,
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["index"]["status"] == "model_mismatch"
    # Both models are named: "mismatch" alone leaves the reader guessing which
    # of the two is the wrong one, and that decides whether the fix is a
    # configuration change or a reindex.
    assert body["index"]["model"] == OTHER_MODEL
    assert body["index"]["configured_model"] == DEFAULT_EMBEDDING_MODEL
    assert body["status"] == "degraded"


@pytest.fixture
def populated_client() -> Iterator[TestClient]:
    """A client over an index that is populated and a credential that is set.

    A fixture rather than four lines in the test body, so that it is built
    BEFORE `forbid_network` patches the socket module — the same ordering the
    other stub tests rely on. Reversed, the patch would catch the event loop's
    own self-pipe on Windows rather than anything the endpoint did.
    """
    probe = FakeHealthProbe(documents=1200, models=(DEFAULT_EMBEDDING_MODEL,))
    with TestClient(_app(probe, jpv_embedding_api_key="an-embedding-key")) as client:
        yield client


def test_health_never_calls_the_embedding_provider(
    populated_client: TestClient, forbid_network: None
) -> None:
    """`forbid_network` turns any socket connection into a failure.

    The credential is configured and the index is populated — the state in which
    a naive implementation would be most tempted to "check the provider is
    working". The field reports configuration presence only, so a provider
    outage can never fail this endpoint.
    """
    response = populated_client.get("/health")

    assert response.status_code == 200
    assert response.json()["provider"] == "configured"


def test_health_result_is_cached_between_probes() -> None:
    """The pool is capped at five for the whole system, shared with the .NET API.

    A probe that opened a connection per call could be what exhausts it during
    an incident — the probe causing the outage it reports.
    """
    probe = FakeHealthProbe(documents=7, models=(DEFAULT_EMBEDDING_MODEL,))
    app = _app(probe, jpv_embedding_api_key="an-embedding-key")

    with TestClient(app) as client:
        first = client.get("/health")
        second = client.get("/health")

    assert first.json() == second.json()
    assert probe.calls == 1


def test_health_degrades_when_database_is_unreachable() -> None:
    probe = FakeHealthProbe(database_reachable=False)
    app = _app(probe, jpv_embedding_api_key="an-embedding-key")

    with TestClient(app) as client:
        response = client.get("/health")

    # Still answers. Reporting the outage is the job; raising would make the
    # endpoint part of it.
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "unavailable"
    assert body["status"] == "degraded"
    assert body["index"]["status"] == "unavailable"


def test_health_reports_an_empty_index_as_zero_not_as_a_mismatch() -> None:
    """A brand-new environment is empty, not broken.

    Emptiness is caught by post-deployment verification, which requires a count
    above zero. Reporting it as a model mismatch here would make every first
    deployment look like a misconfiguration.
    """
    probe = FakeHealthProbe(documents=0, models=())
    app = _app(probe, jpv_embedding_api_key="an-embedding-key")

    with TestClient(app) as client:
        response = client.get("/health")

    body = response.json()
    assert body["index"]["documents"] == 0
    assert body["index"]["status"] != "model_mismatch"
    assert body["index"]["status"] == "ok"
    assert body["index"]["model"] is None


def test_health_without_a_configured_database_is_not_a_degradation() -> None:
    """The service is required to boot and answer without a database.

    That is what `ai-service-dev-compose` guarantees and what stub mode relies
    on, so an absent DATABASE_URL is a documented configuration rather than an
    outage. Reporting it as degraded would paint every local run red.
    """
    probe = FakeHealthProbe(database_reachable=False, database_configured=False)
    app = _app(probe)

    with TestClient(app) as client:
        body = client.get("/health").json()

    assert body["status"] == "OK"
    assert body["database"] == "not_configured"


@pytest.mark.parametrize("field", ["status", "version"])
def test_health_keeps_the_fields_earlier_changes_promised(field: str) -> None:
    """The enrichment adds fields; it does not take any away."""
    probe = FakeHealthProbe(documents=1, models=(DEFAULT_EMBEDDING_MODEL,))
    settings_app = _app(probe)

    with TestClient(settings_app) as client:
        body = client.get("/health").json()

    assert field in body


# ----------------------------------------------------- the projection section (C41)


def test_health_reports_projection_freshness_from_the_checkpoint() -> None:
    """The age is the drain's, taken from the checkpoint and never from the rows.

    The feed is incremental by keyset, so `ai.pos_projection.refreshed_at` records when an
    assignment last changed, not when the projection was last looked at. The probe supplies
    only the checkpoint instant, which is what makes the wrong source unreachable from here.
    """
    synced = datetime.now(tz=UTC) - timedelta(minutes=4)
    probe = FakeHealthProbe(
        documents=1,
        models=(DEFAULT_EMBEDDING_MODEL,),
        projection_synced_at=synced,
        projection_full_synced_at=synced,
        projection_points_of_sale=11,
        projection_scoped_points_of_sale=11,
    )
    app = _app(probe)

    with TestClient(app) as client:
        body = client.get("/health").json()

    projection = body["projection"]
    assert projection["status"] == "ok"
    assert projection["stale"] is False
    assert 0 <= projection["age_seconds"] < 3600
    assert projection["synced_at"] == synced.isoformat()
    assert projection["ceiling_seconds"] == 3600
    assert projection["shops_without_scope"] == 0


def test_health_reports_a_stale_projection_without_degrading_the_service() -> None:
    """Staleness widens the candidate window; it does not break the service.

    Letting it move the top-level status would couple the container health check to a cron,
    and would paint an environment serving correct results as broken.
    """
    probe = FakeHealthProbe(
        documents=1,
        models=(DEFAULT_EMBEDDING_MODEL,),
        projection_synced_at=datetime.now(tz=UTC) - timedelta(days=20),
        projection_points_of_sale=11,
        projection_scoped_points_of_sale=11,
    )
    app = _app(probe)

    with TestClient(app) as client:
        response = client.get("/health")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "OK"
    assert body["projection"]["status"] == "stale"
    assert body["projection"]["stale"] is True
    assert body["projection"]["age_seconds"] > 3600


def test_health_reports_a_point_of_sale_left_without_any_assortment() -> None:
    """The failure C34 hit: 503 on every scoped retrieval while the deployment looks healthy."""
    probe = FakeHealthProbe(
        documents=1,
        models=(DEFAULT_EMBEDDING_MODEL,),
        projection_synced_at=datetime.now(tz=UTC),
        projection_points_of_sale=12,
        projection_scoped_points_of_sale=11,
    )
    app = _app(probe)

    with TestClient(app) as client:
        body = client.get("/health").json()

    assert body["projection"]["points_of_sale"] == 12
    assert body["projection"]["shops_without_scope"] == 1


def test_health_distinguishes_a_projection_never_drained_from_a_stale_one() -> None:
    """Different causes, different fixes, and only this section can tell them apart."""
    probe = FakeHealthProbe(documents=1, models=(DEFAULT_EMBEDDING_MODEL,))
    app = _app(probe)

    with TestClient(app) as client:
        response = client.get("/health")

    body = response.json()
    assert response.status_code == 200
    assert body["projection"]["status"] == "never_drained"
    assert body["projection"]["age_seconds"] is None
    assert body["projection"]["synced_at"] is None


def test_health_reports_failed_pages_rather_than_swallowing_them() -> None:
    """Nothing else reads `ai.sync_failure`, so a page that failed is otherwise invisible."""
    probe = FakeHealthProbe(
        documents=1,
        models=(DEFAULT_EMBEDDING_MODEL,),
        projection_synced_at=datetime.now(tz=UTC),
        projection_failed_pages=3,
    )
    app = _app(probe)

    with TestClient(app) as client:
        body = client.get("/health").json()

    assert body["projection"]["failed_pages"] == 3


def test_health_still_carries_the_projection_when_the_database_is_unreachable() -> None:
    """Absent and unknown are different, and the consumer must not have to guess.

    An omitted section is indistinguishable from an older service that predates it.
    """
    probe = FakeHealthProbe(database_reachable=False)
    app = _app(probe)

    with TestClient(app) as client:
        body = client.get("/health").json()

    assert body["projection"]["status"] == "unavailable"
    assert body["projection"]["stale"] is None
    assert body["projection"]["shops_without_scope"] is None
