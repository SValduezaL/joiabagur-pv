"""Internal service token tests (no LLM / embeddings / RDS)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from jbg_ai.api.auth import decode_service_token
from support.sample_requests import V1_REQUESTS
from support.settings import OTHER_POS_ID, TEST_JWT_SECRET, TOKEN_POS_ID


def _call(
    client: TestClient,
    method: str,
    path: str,
    body: dict[str, Any] | None,
    headers: dict[str, str] | None = None,
) -> Any:
    if method == "GET":
        return client.get(path, headers=headers)
    return client.post(path, json=body, headers=headers)


@pytest.mark.parametrize(("method", "path", "body"), V1_REQUESTS)
def test_request_without_token_is_rejected(
    client: TestClient, method: str, path: str, body: dict[str, Any] | None
) -> None:
    response = _call(client, method, path, body)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "token_kwargs",
    [
        pytest.param({"secret": "wrong-secret-0123456789abcdefghijkl"}, id="bad-signature"),
        pytest.param({"expires_in": -60}, id="expired"),
        pytest.param({"user_id": None}, id="missing-user-id"),
        pytest.param({"role": None}, id="missing-role"),
        pytest.param({"trace_id": None}, id="missing-trace-id"),
        # Present and empty, which is a VALUE and not an absence. C40 made the omission
        # admissible on this route and this case must not follow it: dropping a blank claim
        # would promote a shop-scoped token to «every shop» without anybody asking.
        pytest.param({"pos_id": "   "}, id="blank-pos-id"),
    ],
)
def test_invalid_token_is_rejected(
    client: TestClient, issue_token: Callable[..., str], token_kwargs: dict[str, Any]
) -> None:
    token = issue_token(**token_kwargs)

    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "test-jwt-secret-0123456789abcdefghij" not in response.text
    assert "signature" not in response.text.lower()
    assert "expired" not in response.text.lower()


def test_malformed_authorization_header_is_rejected(client: TestClient) -> None:
    for header in ("Bearer not-a-jwt", "Basic dXNlcjpwYXNz", "token-without-scheme"):
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={"Authorization": header},
        )

        assert response.status_code == 401, header


def test_token_signed_with_unexpected_algorithm_is_rejected(client: TestClient) -> None:
    import jwt

    unsigned = jwt.encode(
        {"user_id": "u-1", "role": "Admin", "pos_id": TOKEN_POS_ID, "trace_id": "t-1"},
        key="",
        algorithm="none",
    )

    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1},
        headers={"Authorization": f"Bearer {unsigned}"},
    )

    assert response.status_code == 401


def test_valid_token_is_accepted(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1},
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_decode_service_token_exposes_every_claim(issue_token: Callable[..., str]) -> None:
    """The principal is the seam: user_id and role reach it even if no route reads them yet."""
    token = issue_token(user_id="u-42", role="Admin", pos_id=OTHER_POS_ID, trace_id="t-9")

    principal = decode_service_token(token, TEST_JWT_SECRET)

    assert principal.user_id == "u-42"
    assert principal.role == "Admin"
    assert principal.pos_id == OTHER_POS_ID
    assert principal.trace_id == "t-9"


def test_pos_id_from_token_overrides_body_value(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    token = issue_token(pos_id=TOKEN_POS_ID)

    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1, "pos_id": OTHER_POS_ID},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["effective_pos_id"] == TOKEN_POS_ID


def test_role_in_body_is_inert(client: TestClient, auth_headers: dict[str, str]) -> None:
    """A body role cannot escalate anything: the response is byte-identical without it."""
    payload = {"query": "anillo", "top_k": 1}

    baseline = client.post("/v1/retrieval/products", json=payload, headers=auth_headers)
    with_role = client.post(
        "/v1/retrieval/products", json={**payload, "role": "Admin"}, headers=auth_headers
    )

    assert with_role.status_code == 200
    assert with_role.content == baseline.content


def test_token_trace_id_wins_over_header(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    token = issue_token(trace_id="trace-from-token")

    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1},
        headers={
            "Authorization": f"Bearer {token}",
            "X-Trace-Id": "trace-from-header",
        },
    )

    assert response.status_code == 200
    assert response.json()["trace_id"] == "trace-from-token"
    assert response.headers["X-Trace-Id"] == "trace-from-token"


def test_token_trace_id_reaches_structured_logs(
    client: TestClient,
    issue_token: Callable[..., str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = issue_token(trace_id="trace-in-logs")

    with caplog.at_level(logging.INFO, logger="jbg_ai"):
        response = client.post(
            "/v1/retrieval/products",
            json={"query": "anillo", "top_k": 1},
            headers={
                "Authorization": f"Bearer {token}",
                "X-Trace-Id": "trace-from-header",
            },
        )

    assert response.status_code == 200
    logged = [getattr(record, "trace_id", None) for record in caplog.records]
    assert "trace-in-logs" in logged


def test_rejected_request_still_carries_a_trace_id(client: TestClient) -> None:
    response = client.post("/v1/retrieval/products", json={"query": "anillo"})

    assert response.status_code == 401
    assert response.headers.get("X-Trace-Id")


ENRICH_BODY = {"products": [{"product_id": "P-1", "sku": "JBG-1"}]}


def test_catalog_token_without_pos_is_accepted_on_enrich(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    """Enriching the catalog belongs to no point of sale.

    Requiring `pos_id` here would force the caller to invent one, and the only
    values available to invent are wildcards — which is precisely what must never
    exist, since that claim is the retriever's only hard filter.
    """
    token = issue_token(pos_id=None)

    response = client.post(
        "/v1/enrich/products", json=ENRICH_BODY, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, response.text


def test_retrieval_accepts_a_token_without_pos_claim(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    """C40 reverses this, and the test it replaces was right when it was written.

    Until now the service refused a token with no `pos_id` on retrieval, and the argument was
    sound: that claim is the retriever's only hard filter between points of sale, and the
    .NET client refused to send a catalog scope here for the same reason. Two independent
    closures on one boundary.

    What changed is not the reasoning but the case. A search deliberately spread over every
    shop has no shop to name, and inventing one is exactly what must never happen. So the
    **omission** is admitted on this route and on sale assistance, and nowhere else — and
    what it buys is that the availability prefilter does not apply, rather than matching
    everything. The old closure survives in the two tests below it: a blank claim is still
    refused, and every point-of-sale route still refuses the omission.
    """
    token = issue_token(pos_id=None)

    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code != 401, response.text


def test_sale_assistance_accepts_a_token_without_pos_claim(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    """The second of exactly three routes that admit it. The list is closed on purpose."""
    token = issue_token(pos_id=None)

    response = client.post(
        "/v1/assist/sale",
        json={"query": "un anillo de plata"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code != 401, response.text


def test_agent_route_accepts_a_token_without_pos_claim(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    """C42 adds the third, and the test it replaces was right while the route had no consumer.

    The agent route used to refuse the omission, and the reasoning below it read «the agent acts
    on the shop's behalf, so it has nothing to answer without one». That was never quite the
    claim: the agent's loop answers perfectly well without a shop — it just cannot pivot to
    substitutes, because with no scope the availability tool reports that no scope applies rather
    than that the shop is out of stock. What made the refusal harmless was that **nothing called
    the route**. C42 gives it a panel, and that panel offers the every-shop scope under the same
    rule its sibling applies — so leaving this route stricter than the route beside it would
    break the pair with no test failing anywhere.

    What the omission buys here is what it buys on the other two: the availability prefilter does
    not apply. Never a wildcard, which remains impossible.
    """
    token = issue_token(pos_id=None)

    response = client.post(
        "/v1/assist/agent",
        json={"turns": [{"role": "operario", "text": "busco un anillo de plata"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code != 401, response.text


@pytest.mark.parametrize(
    ("path", "body"),
    [
        pytest.param(
            "/v1/retrieval/substitutes",
            {"product_id": "b0000000-0000-4000-8000-000000000001", "top_k": 1},
            id="substitutes",
        ),
        pytest.param(
            "/v1/inventory/propose",
            {"top_k": 1},
            id="inventory",
        ),
    ],
)
def test_pos_scoped_route_still_rejects_it(
    client: TestClient,
    issue_token: Callable[..., str],
    path: str,
    body: dict[str, Any],
) -> None:
    """The omission fails closed everywhere it matters, which is what makes it safe.

    **These two work inside one shop, and the agent no longer belongs here.** Substitutes rank by
    what that shop can hand over and inventory proposes for that shop's stock: neither has
    anything to answer without one. The agent's case is different in kind — it can answer, it
    just cannot pivot — and it moved to the test above when C42 gave it a consumer. Widening it
    did not widen these: the list is closed and this is what keeps it closed.
    """
    token = issue_token(pos_id=None)

    response = client.post(path, json=body, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401, path


def test_rejection_does_not_reveal_the_missing_claim(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    """A 401 that names the claim tells an attacker what to forge next."""
    token = issue_token(pos_id=None)

    response = client.post(
        "/v1/inventory/propose",
        json={"top_k": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "pos_id" not in response.text
    assert "claim" not in response.text.lower()


def test_a_blank_pos_claim_is_never_read_as_its_absence(
    client: TestClient, issue_token: Callable[..., str]
) -> None:
    """The hole C40 opened and closed in the same change, and it is worth a test of its own.

    Making the claim optional on two routes meant the decoder stopped requiring it — and it
    used to drop an unusable value silently, because until now a blank one could never get
    past the required-claims loop. Dropped here, a blank `pos_id` would have become «every
    shop»: a token issued for one shop, quietly widened to all of them, with nobody asking.

    Absence is the key not being in the payload. Anything else is a value, and a value has to
    be usable.
    """
    response = client.post(
        "/v1/retrieval/products",
        json={"query": "anillo", "top_k": 1},
        headers={"Authorization": f"Bearer {issue_token(pos_id='   ')}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("claim", ["user_id", "role", "trace_id"])
def test_catalog_route_still_rejects_a_token_missing_the_other_claims(
    client: TestClient, issue_token: Callable[..., str], claim: str
) -> None:
    token = issue_token(pos_id=None, **{claim: None})

    response = client.post(
        "/v1/enrich/products", json=ENRICH_BODY, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_catalog_route_still_reports_pos_scope_when_the_token_carries_one(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """A point-of-sale token is not rejected on a catalog route — it is just not required."""
    response = client.post("/v1/enrich/products", json=ENRICH_BODY, headers=auth_headers)

    assert response.status_code == 200
