#!/usr/bin/env bash
# ============================================================================
# deploy.sh — deploys the isolated demo environment (C17)
#
# Runs ON THE HOST, invoked through the systems management service by
# `.github/workflows/deploy-demo.yml`, or by the host's own provisioning on
# first boot. It is idempotent: running it twice recreates the containers and
# leaves the data alone.
#
# WHY THERE IS NO `set -x` ANYWHERE NEAR THE SECRETS
# --------------------------------------------------
# The standard output and standard error of a command sent through the systems
# management service are ARCHIVED in the command history, readable by anyone
# who can read that history, and retained long after the deployment. Execution
# tracing would print every expansion — including the value of every parameter
# read below — straight into that archive. If you need to debug this script,
# add echo statements naming the variables, never their values, and never turn
# on tracing above the point where the last secret is used.
#
# WHY NO ENVIRONMENT FILE IS WRITTEN
# ----------------------------------
# Secrets are read into the environment of THIS process and interpolated by
# Compose from there. Nothing lands on the host's disk. Be honest about the
# limit of that: a container's environment is readable with `docker inspect` by
# anyone who is root on this host. It is proportionate for a demonstration
# environment, and it is not a vault.
# ============================================================================

set -euo pipefail

# ─── Constants ──────────────────────────────────────────────────────────────

#: Where the host's provisioning placed the deployment bundle. The composition
#: file references `./deploy/demo/Caddyfile` relative to itself, so the
#: repository layout is preserved here rather than flattened.
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/jbg-demo}"
COMPOSE_FILE="${DEPLOY_ROOT}/compose.demo.yaml"

#: Every parameter of this environment lives under one prefix, and the demo
#: instance's role can read that prefix and nothing else.
SSM_PREFIX="${SSM_PREFIX:-/jbg-demo}"

#: Service name, fixed by the composition file.
AI_SERVICE="jbg-demo-ai"

log() { printf '[deploy] %s\n' "$*"; }

# ─── 0. Region ──────────────────────────────────────────────────────────────
#
# Resolved before anything talks to an AWS service. The instance metadata
# service requires a session token (IMDSv2 is enforced on the images this
# module uses), so the region is fetched with one, and falls back to the
# module's region if metadata is unavailable for any reason.
if [ -z "${AWS_REGION:-}" ]; then
  IMDS_TOKEN="$(curl -fsS -m 5 -X PUT http://169.254.169.254/latest/api/token \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null || true)"
  AWS_REGION="$(curl -fsS -m 5 -H "X-aws-ec2-metadata-token: ${IMDS_TOKEN}" \
    http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || echo eu-west-1)"
fi
export AWS_REGION
export AWS_DEFAULT_REGION="${AWS_REGION}"

# ─── 1. Parameters: store → this process's environment, never a file ────────

read_parameter() {
  # `--with-decryption` is harmless on a plain String parameter and required on
  # a SecureString one, so one function serves both classes.
  aws ssm get-parameter \
    --name "${SSM_PREFIX}/$1" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text
}

log "Reading parameters from ${SSM_PREFIX}/ ..."

# ── Class B · environment settings ─────────────────────────────────────────
export DEMO_HOSTNAME="$(read_parameter DEMO_HOSTNAME)"
export ECR_REGISTRY="$(read_parameter ECR_REGISTRY)"

# The tag deployed. An argument wins over the stored value so an operator can
# roll back to a previous image without editing the parameter first; with no
# argument — the host's own first boot, or a reboot — the stored value is what
# gets deployed, which is the last tag the pipeline published.
if [ "$#" -ge 1 ] && [ -n "${1:-}" ]; then
  export IMAGE_TAG="$1"
  log "Image tag from argument: ${IMAGE_TAG}"
else
  export IMAGE_TAG="$(read_parameter IMAGE_TAG)"
  log "Image tag from parameter store: ${IMAGE_TAG}"
fi

# ── Class A · secrets ──────────────────────────────────────────────────────
export POSTGRES_PASSWORD="$(read_parameter POSTGRES_PASSWORD)"
export AI_DB_PASSWORD="$(read_parameter AI_DB_PASSWORD)"
export JWT_SIGNING_KEY="$(read_parameter JWT_SIGNING_KEY)"
export EMBEDDING_API_KEY="$(read_parameter EMBEDDING_API_KEY)"

# C30b · C34. UNLIKE every other secret here, this parameter may NOT exist:
# without it the generation layer does not run, and the sale assistance route
# serves its structured response with a 200 — a declared, valid state and the
# rollback of the generation. Hence `|| true`: `set -e` plus the store's own
# error would otherwise abort the whole deployment over a credential whose
# absence is legitimate. And for the same reason there is NO `:?` line for it in
# the validation block below: empty here means "we do not generate", not "broken".
export ASSIST_LLM_API_KEY="$(read_parameter ASSIST_LLM_API_KEY || true)"
# Whether it is there, never what it is: the output of this script is archived.
if [ -n "${ASSIST_LLM_API_KEY}" ]; then
  log "Generation credential: present (the sale argument will be generated)"
else
  log "Generation credential: absent (the sale card serves no argument; see deploy/demo/README.md)"
fi

# C31 · C32b · C39a. The other TWO optional credentials, one per remaining
# generation stage, and the same rule as the one above for the same reason: each
# one absent is a declared state with a rollback of its own, so `|| true` here and
# NO `:?` line in the validation block below.
#
# They are three separate parameters and never one read three times, which is the
# OPPOSITE of the rule the two shared credentials below follow. The distinction is
# the point: there the risk is DRIFT between two halves that must agree literally,
# so one parameter is safer. Here the risk is CONFUSING THREE COSTS — the three
# stages run different models, and the router in particular was measured on
# `gpt-4o` after `gpt-4o-mini` was vetoed for silencing answerable queries — so
# three parameters is what keeps the bill readable. They may hold the same value.
#
# Until C39a neither existed, and both stages fell back to the argument's key:
# the C34 deployment logged `stage=router_client ... credential=assist_fallback`
# and the agent had no consumer at all.
export ROUTER_LLM_API_KEY="$(read_parameter ROUTER_LLM_API_KEY || true)"
export AGENT_LLM_API_KEY="$(read_parameter AGENT_LLM_API_KEY || true)"

# Whether each is there, never what it is. One line per stage, because a single
# line for the three would not say WHICH one is missing, and the three degrade to
# three different things.
if [ -n "${ROUTER_LLM_API_KEY}" ]; then
  log "Router credential: present (intent is classified with the router's own model)"
else
  log "Router credential: absent (the classifier falls back to the generation key, or to none: intent is 'unclassified')"
fi
if [ -n "${AGENT_LLM_API_KEY}" ]; then
  log "Agent credential: present (the sale assistant loop will run)"
else
  log "Agent credential: absent (POST /v1/assist/agent answers without running the loop)"
fi

# The two shared credentials. Each is ONE parameter, read ONCE here, and
# interpolated by the composition file into the TWO services that must agree on
# it literally:
#
#   AI_SERVICE_SHARED_SECRET → JWT_SECRET (ai) and AiGateway__JwtSecret (api)
#   INDEX_FEED_SHARED_KEY    → JPV_INDEX_FEED_API_KEY (ai) and IndexFeed__ApiKey (api)
#
# Storing them as two independently editable parameters each would let the two
# halves drift, and drift produces a 401 whose cause the AI service is required
# not to disclose — a failure with no message and no log line pointing at it.
export AI_SERVICE_SHARED_SECRET="$(read_parameter AI_SERVICE_SHARED_SECRET)"
export INDEX_FEED_SHARED_KEY="$(read_parameter INDEX_FEED_SHARED_KEY)"

# ─── 2. Validation: an empty value must fail here, loudly ───────────────────
#
# A missing parameter already fails, because `set -e` plus the store's own error
# stops the script. An EMPTY one does not: it would start a service that answers
# every request with a credential rejection whose cause is deliberately not
# disclosed, and a database whose password is the empty string. `:?` turns each
# of those into a named failure before a single container is created.
: "${DEMO_HOSTNAME:?/jbg-demo/DEMO_HOSTNAME is empty; the proxy would request a certificate for no name}"
: "${ECR_REGISTRY:?/jbg-demo/ECR_REGISTRY is empty; no image reference can be resolved}"
: "${IMAGE_TAG:?/jbg-demo/IMAGE_TAG is empty; refusing to deploy an unnamed image}"
: "${POSTGRES_PASSWORD:?/jbg-demo/POSTGRES_PASSWORD is empty}"
: "${AI_DB_PASSWORD:?/jbg-demo/AI_DB_PASSWORD is empty}"
: "${JWT_SIGNING_KEY:?/jbg-demo/JWT_SIGNING_KEY is empty; user tokens would be signed with nothing}"
: "${EMBEDDING_API_KEY:?/jbg-demo/EMBEDDING_API_KEY is empty; retrieval would answer 503}"
: "${AI_SERVICE_SHARED_SECRET:?/jbg-demo/AI_SERVICE_SHARED_SECRET is empty; every internal call would be rejected}"
: "${INDEX_FEED_SHARED_KEY:?/jbg-demo/INDEX_FEED_SHARED_KEY is empty; the catalog feed would reject every sync}"

log "All required parameters are present."

# ─── 3. Registry login and image pull ───────────────────────────────────────

log "Authenticating against the image registry ..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

log "Pulling ${IMAGE_TAG} ..."
docker compose -f "${COMPOSE_FILE}" pull jbg-demo-api jbg-demo-ai

# ─── 4. Start ───────────────────────────────────────────────────────────────
#
# `up -d` recreates in place: containers are replaced, VOLUMES ARE NOT.
#
# NEVER `docker compose down -v` here, or anywhere in a deployment path. It
# destroys `jbg-demo-caddy-data`, which holds the issued certificate, and the
# certificate authority rate-limits DUPLICATE certificates to FIVE PER WEEK for
# the same set of names. Two careless redeployments in a week leave the demo
# serving no valid TLS until the limit resets — and it also destroys
# `jbg-demo-pgdata`, which holds the catalog and the vector index.
log "Starting the environment ..."
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

# ─── 5. Schema revisions ────────────────────────────────────────────────────
#
# From inside the AI container, which already has alembic, the revisions and
# DATABASE_URL. The one-off `bootstrap.sql` — extension, schema `ai` and the
# `jbg_ai` role — is NOT run here: it needs administrator privileges and is a
# per-environment step documented in this directory's README.
log "Applying schema revisions ..."
docker compose -f "${COMPOSE_FILE}" exec -T "${AI_SERVICE}" alembic upgrade head

# ─── 6. Warm-up ─────────────────────────────────────────────────────────────
#
# The AI service builds its embedding client per request, so the first search
# after a deployment pays a full cold round trip to the provider — measured at
# roughly two seconds during C16, which is beyond the gateway's budget and
# would degrade that first search to the lexical path. Absorbing it here means
# the person opening the demo is not the one who pays for it.
#
# Deliberately non-fatal: a slow provider on one call is not a reason to fail a
# deployment. Whether the environment is actually correct is decided by the
# post-deployment verification, which is not best-effort.
log "Warming the embedding client ..."
docker compose -f "${COMPOSE_FILE}" exec -T "${AI_SERVICE}" python - <<'PYTHON' || log "WARNING: warm-up did not complete; the first search may be slow."
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta

import jwt

now = datetime.now(tz=UTC)
token = jwt.encode(
    {
        "user_id": "warmup",
        "role": "Operator",
        # Any point of sale identifier warms the same path: the query is
        # embedded before the scope filter is applied.
        "pos_id": str(uuid.uuid4()),
        "trace_id": f"warmup-{uuid.uuid4()}",
        "iat": now,
        "exp": now + timedelta(seconds=120),
    },
    os.environ["JWT_SECRET"],
    algorithm="HS256",
)

request = urllib.request.Request(
    "http://127.0.0.1:8000/v1/retrieval/products",
    data=json.dumps({"query": "anillo de plata", "top_k": 1}).encode(),
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as response:
    print(f"warm-up status {response.status}")
PYTHON

# ─── 7. Done ────────────────────────────────────────────────────────────────

log "Deployed ${IMAGE_TAG}. Public entry point: https://${DEMO_HOSTNAME}"
docker compose -f "${COMPOSE_FILE}" ps
