#!/usr/bin/env bash
# ============================================================================
# verify.sh — post-deployment verification for the demo environment (C17)
#
# RUNS INSIDE THE HOST, invoked through the systems management service by
# `.github/workflows/deploy-demo.yml`.
#
# It runs here and not on the pipeline runner because the AI service is PRIVATE
# BY DESIGN: it publishes no port, and the security group opens only the two the
# reverse proxy serves. A runner outside the environment cannot reach it, and
# making it reachable so that it could be checked would destroy precisely the
# property the check exists to protect (C17 D21).
#
# It fails the deployment on any of SEVEN conditions, and the first one is the
# reason this script exists at all:
#
#   1. Zero indexed documents. A deployment with an empty index answers 200s,
#      serves a valid certificate, and finds nothing. It looks like success.
#   2. The configured embedding model disagrees with the one recorded on the
#      index rows: queries and documents would live in two different vector
#      spaces, producing noise with no error anywhere.
#   3. The database is unreachable.
#   4. The embedding provider credential is not configured.
#   5. The point-of-sale availability projection holds no assigned row for some
#      point of sale (C41). Same shape as the first, one table along: every
#      scoped retrieval answers 503, the API degrades correctly to its lexical
#      path with a 200, and the environment looks healthy from outside. It had
#      already reached this environment once, in C34.
#   6. The knowledge corpus holds no fragment (C39a). The THIRD table of that
#      same series. With `ai.knowledge_chunk` empty the piece-anchored argument
#      is withheld for want of material to anchor it to, and the piece-anchored
#      question answers `knowledge_not_covered` with no citations — both of which
#      read on screen as a defect of the sale card and not of the deployment.
#      `/health` cannot report it: it has no knowledge section, so this is read
#      from the database. Measured on 2026-09-27 the live environment held 161
#      fragments, so this guards the NEXT clean environment rather than fixing a
#      present fault — the corpus lives in `jbg-demo-pgdata` and survives a
#      redeployment, which is why the gap stayed invisible for five weeks.
#   7. The agent route does not answer (C39a). Its failure is silent in the same
#      way: the screens render, the certificate is valid, and the fourth card of
#      the hub simply is not there.
#
# Note what it does NOT do, and condition 7 sharpens the rule rather than
# breaking it: it never asks whether the provider is answering. `/health` does
# not call it either, and a third-party outage is not a failed deployment. So a
# 200 carrying a stop reason of `sin_cliente` or `fallo_proveedor` is reported and
# does NOT fail: the agent credential is DECLARED OPTIONAL and deleting it is the
# documented rollback of the loop, so failing on its absence would make the
# rollback break the deployment. What fails is the route not answering at all.
#
# COST, stated because it is not free: condition 7 runs one real loop per
# deployment when the credential is present. That is the same cost model the
# embedding warm-up in `deploy.sh` already accepts, and it is the only way to
# learn end to end that the route works.
# ============================================================================

set -euo pipefail

# Plain `docker exec` on the container name, NOT `docker compose exec`. Compose
# would parse the composition file to resolve the service, and parsing it means
# interpolating every `${VAR}` in it — none of which are exported when this runs
# on its own. The result is a screen of "variable is not set" warnings on a
# verification that is working perfectly, which is exactly the kind of noise that
# teaches people to ignore output. The name is fixed by `container_name:`.
AI_CONTAINER="jbg-demo-ai"

echo "[verify] Probing the AI service health report from inside the host ..."

docker exec -i "${AI_CONTAINER}" python - <<'PYTHON'
import json
import os
import sys
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=10) as response:
    body = json.load(response)

print(json.dumps(body, indent=2, sort_keys=True))

index = body.get("index") or {}
failures = []

if body.get("database") != "ok":
    failures.append(f"database is {body.get('database')!r}, expected 'ok'")

documents = index.get("documents")
if not isinstance(documents, int) or documents <= 0:
    failures.append(
        f"indexed documents is {documents!r}; an environment with an empty index "
        "answers every request successfully and finds nothing"
    )

if index.get("status") != "ok":
    failures.append(
        f"index status is {index.get('status')!r} (configured model "
        f"{index.get('configured_model')!r} vs indexed {index.get('model')!r})"
    )

if body.get("provider") != "configured":
    failures.append(f"provider credential is {body.get('provider')!r}, expected 'configured'")

# Fifth condition (C41), and the same shape as the first one table along. An environment whose
# index is full but whose point-of-sale projection is empty PASSED this check until now: every
# scoped retrieval answers 503, the .NET side degrades correctly to its lexical path and answers
# 200, a valid certificate is served and the screens render — so the deployment looks like a
# success and quietly finds nothing that the assortment should have narrowed. It reached a
# deployed environment once already, and the deferred task recording it is closed by this block.
#
# Tolerant of an older AI image that does not report the section: absent is not a failure, it is
# a version skew, and failing a deployment for it would be a false alarm about the wrong thing.
projection = body.get("projection")
if isinstance(projection, dict):
    points_of_sale = projection.get("points_of_sale")
    without_scope = projection.get("shops_without_scope")

    if projection.get("status") == "never_drained":
        failures.append(
            "the point-of-sale projection has never been drained; every scoped retrieval "
            "will answer 503 while this deployment looks healthy from outside"
        )
    elif isinstance(points_of_sale, int) and points_of_sale == 0:
        failures.append(
            "the point-of-sale projection holds no rows at all; assisted search cannot be "
            "scoped to any shop"
        )
    elif isinstance(without_scope, int) and without_scope > 0:
        failures.append(
            f"{without_scope} point(s) of sale hold no assigned row in the projection; "
            "assisted search answers 503 for each of them"
        )

# Sixth condition (C39a). Read from the DATABASE and not from `/health`, because the health
# report has no knowledge section: it covers the product index, the projection, the database and
# the embedding credential, and adding a section to it would mean touching `ai-service/src`,
# which this change declares out of scope. The connection string is the container's own, so no
# password is handled here.
#
# Tolerant of the table not existing, which is a version skew and not an empty corpus: an image
# older than C23 has no `ai.knowledge_chunk` at all, and failing a deployment for that would be a
# false alarm about the wrong thing — the same tolerance the projection block above applies.
knowledge_chunks = None
try:
    import psycopg

    with psycopg.connect(
        os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    ) as connection:
        (knowledge_chunks,) = connection.execute(
            "select count(*) from ai.knowledge_chunk"
        ).fetchone()
except Exception as exc:  # noqa: BLE001 — a probe records what it could not read
    print(f"[verify] NOTE: the knowledge corpus could not be counted: {exc}")

if isinstance(knowledge_chunks, int) and knowledge_chunks == 0:
    failures.append(
        "the knowledge corpus holds no fragment; the piece-anchored argument is withheld for "
        "want of material to anchor it to and the piece-anchored question answers "
        "'knowledge_not_covered', which both read on screen as a defect of the sale card"
    )

# Seventh condition (C39a). The route is probed with ONE minimal operator turn, with a service
# token minted here exactly as the warm-up of `deploy.sh` does — the container holds `JWT_SECRET`,
# so nothing is read from outside.
#
# What fails and what does not: a transport error, a non-200 or a timeout FAILS. A 200 carrying
# `sin_cliente` or `fallo_proveedor` is REPORTED AND DOES NOT FAIL, because the agent credential
# is declared optional and deleting it is the documented rollback of the loop — failing here would
# make that rollback break the deployment. The distinction mirrors the .NET breaker, which
# deliberately does not count an in-band degradation either: it sees a transport outcome and never
# the body.
DEGRADED_STOP_REASONS = {"sin_cliente", "fallo_proveedor"}
agent_stop_reason = None
try:
    import uuid
    from datetime import UTC, datetime, timedelta

    import jwt

    minted_at = datetime.now(tz=UTC)
    agent_token = jwt.encode(
        {
            "user_id": "verify",
            "role": "Operator",
            # A RANDOM point of sale, like the warm-up uses — and unlike the warm-up, here
            # that CHANGES THE OUTCOME, which is worth saying so nobody reads it as a fault.
            # The warm-up only needs the query embedded, which happens before the scope
            # filter. The agent searches a scope, and a scope that matches no shop gives it
            # nothing to work with, so the loop legitimately ends by asking for
            # clarification. Measured on 2026-09-27 against the live environment:
            # `stop_reason='aclaracion'`. That is a route that ANSWERS, which is all this
            # condition asks. Pinning a real point of sale here would make the probe depend
            # on the assortment of one shop, which is a different and worse coupling.
            "pos_id": str(uuid.uuid4()),
            "trace_id": f"verify-{uuid.uuid4()}",
            "iat": minted_at,
            "exp": minted_at + timedelta(seconds=120),
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    agent_request = urllib.request.Request(
        "http://127.0.0.1:8000/v1/assist/agent",
        data=json.dumps(
            {"turns": [{"role": "operario", "text": "busco un anillo de plata"}]}
        ).encode(),
        headers={
            "Authorization": f"Bearer {agent_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    # Wider than the service's own 15 s wall clock, so that the deadline the loop enforces is
    # what cuts a slow turn — not this probe, which would report a healthy route as broken.
    with urllib.request.urlopen(agent_request, timeout=25) as agent_response:
        agent_body = json.load(agent_response)
    agent_stop_reason = agent_body.get("stop_reason")
except Exception as exc:  # noqa: BLE001
    failures.append(
        f"the agent route did not answer ({type(exc).__name__}: {exc}); the fourth card of the "
        "hub would simply not be there while the rest of the environment looks healthy"
    )

if failures:
    print("[verify] FAILED:", file=sys.stderr)
    for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
    sys.exit(1)

print(f"[verify] OK — {documents} documents indexed with {index.get('model')}")
if isinstance(projection, dict):
    print(
        f"[verify] OK — projection drained {projection.get('age_seconds')}s ago, "
        f"{projection.get('points_of_sale')} point(s) of sale scoped"
    )
if isinstance(knowledge_chunks, int):
    print(f"[verify] OK — knowledge corpus holds {knowledge_chunks} fragment(s)")
if agent_stop_reason in DEGRADED_STOP_REASONS:
    print(
        f"[verify] OK — the agent route answered, DEGRADED: stop_reason={agent_stop_reason!r}. "
        "That is a declared state, not an outage; the loop did not run"
    )
else:
    print(f"[verify] OK — the agent route answered, stop_reason={agent_stop_reason!r}")
PYTHON

echo "[verify] Post-deployment verification passed."
