# Demo environment — runbook

Everything needed to stand the isolated demonstration environment up from a
brand-new AWS account, populate it with the corpus, and hand out a public URL.

> **This environment is not production and cannot reach it.** It lives in a
> different AWS account, with its own Terraform state, its own image
> repositories, its own parameter prefix and its own deployment workflow. The
> shop's account is not referenced anywhere in it. See
> [`openspec/changes/add-ai-service-deployment/design.md`](../../openspec/changes/archive/2026-08-30-add-ai-service-deployment/design.md).

| Piece | Where |
|---|---|
| Infrastructure | [`terraform/demo/`](../../terraform/demo/) |
| Composition, four services | [`compose.demo.yaml`](../../compose.demo.yaml) |
| Reverse proxy | [`Caddyfile`](./Caddyfile) |
| Deployment script, runs on the host | [`deploy.sh`](./deploy.sh) |
| Workflow | [`.github/workflows/deploy-demo.yml`](../../.github/workflows/deploy-demo.yml) |
| Images | `backend/src/JoiabagurPV.API/Dockerfile.demo`, `ai-service/Dockerfile` |

---

## Two warnings, before anything else

**Never run `docker compose down -v` on this host.** The `-v` destroys named
volumes, and two of them matter:

- `jbg-demo-caddy-data` holds the **issued TLS certificate**. Let's Encrypt
  rate-limits *duplicate* certificates to **five per week** for the same set of
  names. Two careless redeployments in one week leave the demo without valid
  TLS until the limit resets — with no way to hurry it.
- `jbg-demo-pgdata` holds the **catalog and the vector index**. Recoverable
  from the dump, but that is an hour you did not plan for.

`deploy.sh` uses `up -d`, which recreates containers in place and leaves volumes
alone. Keep it that way.

**A deployed environment with an empty index passes every test.** It answers
200s, it serves a valid certificate, and assisted search finds nothing. That is
why the data path (§5 below) is part of the deployment and not an afterthought,
and why post-deployment verification fails on a document count of zero.

---

## 1. Account and prerequisites

> Account identifiers, the Identity Center portal URL and the state bucket name
> are **not written here**: this repository is public. Keep them in your own
> notes; `terraform output` reprints everything the workflow needs.

### 1.1 A dedicated member account

The demo runs in its **own AWS account**, created under AWS Organizations from
your management account. The specification only requires an account distinct
from the shop's, which a personal account already satisfies — so this is a
judgement call, made for three reasons:

- The demo publishes **a web server on the open Internet**, with a database
  holding real catalog prices and a GitHub-federated role that can create and
  destroy compute. In a dedicated account, an incident stays inside it.
- **Cost attribution is exact** with no tagging discipline: one filter by
  account in Cost Explorer. §12 of the design commits to reporting what this
  costs.
- The **OIDC provider is a singleton per account** (see [`iam.tf`](../../terraform/demo/iam.tf)).
  A virgin account is the case the module is written for.

The account itself is free; the ~20-25 USD/month is instance, disk and address.

```bash
aws organizations create-account \
  --email "<unique-root-email>" --account-name "<name>" \
  --iam-user-access-to-billing ALLOW

aws organizations list-create-account-status \
  --query 'CreateAccountStatuses[].[AccountName,State,AccountId,FailureReason]' \
  --output table
```

Asynchronous; poll until `SUCCEEDED` and keep the account id. **Closing an AWS
account takes 90 days**, so do not create one to try it out.

### 1.2 Access, without long-lived keys

Use **IAM Identity Center**, not IAM users: the credentials expire on their own,
and nothing lands on disk — the same principle the deployment follows for
secrets.

> **The trap that costs an hour.** An organization may already show an Identity
> Center instance that is an **account instance** — the kind an AWS managed
> application creates for itself. It looks identical in `list-instances` and is
> useless here. The tell is unambiguous:
>
> ```bash
> aws sso-admin list-permission-sets --instance-arn "$INSTANCE" --region <region>
> # ValidationException: Permission Sets are not enabled for this instance
> ```
>
> Permission sets are exactly what account instances lack. If it has no users
> and no applications, delete it with `aws sso-admin delete-instance` and enable
> an organization instance from the console.

In the management account, in the region you want:

1. **IAM Identity Center → Enable.** Choose **single-region**. Multi-region
   replicates your identity data to a second region and requires a
   customer-managed KMS key billed monthly — resilience nobody here needs. The
   primary region **cannot** be changed later; additional regions can be added.
2. **Users → Add user.** MFA is registered on first sign-in.
3. **Permission sets → Predefined → `AdministratorAccess`**, session duration
   **8 hours** — one hour turns a long `terraform apply` into a login loop.
   Total administrator is proportionate precisely because the account is
   dedicated and disposable.
4. **Assign the user to BOTH accounts** — the demo account to work in, and the
   management account so that organization tasks never need the root user again.

### 1.3 Local profiles

```ini
[sso-session jbg]
sso_start_url = https://<portal>.awsapps.com/start
sso_region = <identity-center-region>
sso_registration_scopes = sso:account:access

[profile jbg-demo]
sso_session = jbg
sso_account_id = <demo-account-id>
sso_role_name = <permission-set-name>
region = eu-west-1
output = json
ca_bundle = C:\Users\<you>\.aws\ca-bundle-norton.pem
```

`sso_region` and `region` are **independent**: the first is where Identity
Center lives, the second where the resources run. A portal in one region
managing workloads in another is ordinary.

> **`ca_bundle` is mandatory on the development machine used for C17.** Norton
> intercepts TLS with its own root CA, which sits in the Windows store but not
> in the CLI's bundled `certifi`. Without that line even `aws sso login` fails
> with `CERTIFICATE_VERIFY_FAILED`. It is the same cause that makes `uv` need
> `--system-certs` (see `CLAUDE.md`). Go-based tools — Terraform, Docker — read
> the Windows store and are unaffected. This is why `aws configure sso` is the
> wrong way to create these profiles: it does not write `ca_bundle`.
>
> **AND THE BUNDLE EXPIRES, which cost the first half hour of C39a.** Norton rotates its
> interception root, and when it does, a bundle exported months earlier no longer contains it:
> every call dies with the same `CERTIFICATE_VERIFY_FAILED` **even with `--ca-bundle` pointing
> explicitly at the file**, which reads like a profile problem and is not. The bundle in use was
> from 2026-08-11 with 131 certificates; regenerating it produced 253 and everything worked
> again. Regenerate with:
>
> ```python
> import ssl, certifi, pathlib
> parts = [pathlib.Path(certifi.where()).read_text(encoding="utf-8")]
> for store in ("ROOT", "CA"):
>     parts += [ssl.DER_cert_to_PEM_cert(der) for der, _, _ in ssl.enum_certificates(store)]
> pathlib.Path(r"C:\Users\<you>\.aws\ca-bundle-norton.pem").write_text("\n".join(parts), encoding="utf-8")
> ```
>
> **Do not filter by the trust flag.** Norton's root does not carry it, so filtering produces a
> bundle that looks complete and is not — the same warning `CLAUDE.md` gives for the Python side.

Then `aws sso login --profile jbg-demo`, and confirm with
`aws sts get-caller-identity --profile jbg-demo`.

### 1.4 State bucket

In the **demo** account, before `terraform init`:

```bash
aws s3api create-bucket --bucket <state-bucket> --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1 --profile jbg-demo
aws s3api put-bucket-versioning --bucket <state-bucket> \
  --versioning-configuration Status=Enabled --profile jbg-demo
aws s3api put-public-access-block --bucket <state-bucket> --profile jbg-demo \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

Bucket names are **globally unique**; if the one in
[`backend.tf`](../../terraform/demo/backend.tf) is taken, suffix it with the
account id and update that file.

### 1.5 Local tooling

AWS CLI v2, Terraform ≥ 1.5, Docker, and `psql`/`pg_dump` from PostgreSQL 15
client tools.

## 2. Infrastructure

```bash
cd terraform/demo
cp terraform.tfvars.example terraform.tfvars   # fill in github_repo
terraform init
terraform plan
```

**Verify the plan explicitly**: every resource it lists must belong to this
module. No production instance, security group, role, repository, parameter or
database may appear — and it cannot, because this state has never read theirs.
Read the plan anyway; the check is cheap and the failure it prevents is not.

```bash
terraform apply
terraform output          # role ARN, instance id, elastic IP, demo URL
```

> Reusing this module in an account that **already** deploys from GitHub
> Actions: the OpenID Connect provider registration is a singleton per account
> and issuer. Convert `aws_iam_openid_connect_provider.github` into a data
> source first, or the apply fails with `EntityAlreadyExists`. The comment in
> [`iam.tf`](../../terraform/demo/iam.tf) spells out the change.

Then confirm the host has registered with Systems Manager — until it does, every
deployment times out on a command nobody can collect:

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$(terraform output -raw instance_id)" \
  --query 'InstanceInformationList[0].PingStatus' --output text     # Online
```

## 3. Parameters

Terraform creates the **four** non-secret parameters: `DEMO_HOSTNAME`,
`ECR_REGISTRY`, `IMAGE_TAG` and `DEPLOYMENT_BUNDLE_URL`. *(This sentence said
"three" and omitted the last one until C39a audited the account against
`ssm.tf`, which declares four.)* **The secrets are created here, by hand, on
purpose**: a value passed to Terraform is written to its state file in clear,
which would move them out of the encrypted store and into a file.

```bash
REGION=eu-west-1
put() { aws ssm put-parameter --region "$REGION" --name "/jbg-demo/$1" \
          --type SecureString --value "$2" --overwrite; }

put POSTGRES_PASSWORD        "$(openssl rand -base64 24 | tr -d '/+=')"
put AI_DB_PASSWORD           "$(openssl rand -base64 24 | tr -d '/+=')"
put JWT_SIGNING_KEY          "$(openssl rand -base64 48 | tr -d '/+=')"
put AI_SERVICE_SHARED_SECRET "$(openssl rand -base64 48 | tr -d '/+=')"
put INDEX_FEED_SHARED_KEY    "$(openssl rand -base64 32 | tr -d '/+=')"
put EMBEDDING_API_KEY        "sk-..."      # the provider key, pasted

# OPTIONAL — one per generation stage, three in total (C39a). Each one absent is a
# declared state with a rollback of its own; see below.
put ASSIST_LLM_API_KEY       "sk-..."      # the sale argument
put ROUTER_LLM_API_KEY       "sk-..."      # the intent classifier (C31)
put AGENT_LLM_API_KEY        "sk-..."      # the sale assistant loop (C32b, surfaced by C42)
```

**Three parameters and not one read three times**, which is the opposite of the rule
the two shared credentials follow, and the distinction matters. There the risk is
**drift** between two halves that must agree literally, so one parameter is safer.
Here the risk is **confusing three costs**: the three stages run different models —
the classifier `gpt-4o`, the argument `gpt-4o-mini`, the loop `gpt-4o` — and a
classification of a few output tokens and a paragraph are not the same call. **They
may hold the same provider key**, exactly as `EMBEDDING_API_KEY` may.

| Parameter | Injected as | Into |
|---|---|---|
| `POSTGRES_PASSWORD` | `POSTGRES_PASSWORD`, and the API connection string | database, API |
| `AI_DB_PASSWORD` | `DATABASE_URL` of the AI service | AI service |
| `JWT_SIGNING_KEY` | `Jwt__SecretKey` | API |
| **`AI_SERVICE_SHARED_SECRET`** | `JWT_SECRET` **and** `AiGateway__JwtSecret` | **both** |
| **`INDEX_FEED_SHARED_KEY`** | `JPV_INDEX_FEED_API_KEY` **and** `IndexFeed__ApiKey` | **both** |
| `EMBEDDING_API_KEY` | `JPV_EMBEDDING_API_KEY` | AI service |
| `ASSIST_LLM_API_KEY` *(optional)* | `JPV_ASSIST_LLM_API_KEY` | AI service |
| `ROUTER_LLM_API_KEY` *(optional, C39a)* | `JPV_ROUTER_LLM_API_KEY` | AI service |
| `AGENT_LLM_API_KEY` *(optional, C39a)* | `JPV_AGENT_LLM_API_KEY` | AI service |

The two rows in bold are **one parameter read twice**, never two parameters. Two
would be free to drift, and a drifted pair produces a 401 whose cause the AI
service is specified not to disclose — a failure with no message pointing at it.

**The three provider credentials of the generation stages are the secrets whose absence is a
valid state**, and `deploy.sh` reads all three with `|| true` and validates none of them as
non-empty. Each one degrades to something declared, and **deleting the parameter and
redeploying is that stage's rollback**:

| Parameter absent | What the environment does instead |
|---|---|
| `ASSIST_LLM_API_KEY` (C30b, switched on by C34) | no generation client is built: the sale assistance route still answers 200 with the group, the warnings and the citations, but no argument — `prompt_version: null`, which the card reports as `pitchStatus: not_generated` |
| `ROUTER_LLM_API_KEY` (C31, added by C39a) | the classifier is not constructed, `intent` comes back `unclassified`, and the route serves exactly what it served before C31. **Beware the quiet case**: with the argument's key present the router falls back to it and works, logging `stage=router_client … credential=assist_fallback` — which is what this environment did until C39a. It works and it is not what is declared |
| `AGENT_LLM_API_KEY` (C32b, surfaced by C42, added by C39a) | the loop is not constructed and `POST /v1/assist/agent` answers 200 without running it. Same quiet fallback applies |

Each stage logs whether its credential was picked up, never what it is:
`stage=assist_client`, `stage=router_client`, `stage=agent_client`, with `credential=` naming
which link of the fallback won. **A deployment meant to demonstrate the system should show
`credential=assist`, `credential=router` and `credential=agent`** — anything ending in
`_fallback` means one stage is running on another's key.

**Terraform is not touched** for any of them: the instance role already reads the whole
`/jbg-demo/` prefix.

What is **not** here, and must not be added: the embedding model, the retrieval
distance threshold, and stub mode. Those are versioned literals in
`compose.demo.yaml`. Changing what the system computes belongs in a commit, not
in a parameter anyone can edit.

## 4. First deployment

Create the `demo` branch and the GitHub Environment of the same name, and set
the environment's secrets from `terraform output`:

| Secret | Value |
|---|---|
| `DEMO_DEPLOY_ROLE_ARN` | `terraform output -raw deploy_role_arn` |
| `DEMO_INSTANCE_ID` | `terraform output -raw instance_id` |

Run the workflow **manually first** (`workflow_dispatch`), before pushing
anything to `demo`. A first run on a push is a first run you cannot repeat
cheaply.

```bash
gh workflow run deploy-demo.yml
gh run watch
```

**The first run will fail, and it fails earlier than you would guess.** Not at
verification for an empty index — it never gets that far. It fails at
`alembic upgrade head`, with:

```
FATAL: password authentication failed for user "jbg_ai"
```

The `jbg_ai` role and the `ai` schema do not exist until `bootstrap.sql` runs,
and `bootstrap.sql` needs the Postgres container that this very deployment is
what creates. The chicken and egg is inherent, not a mistake: **deploy first,
provision second, redeploy third.**

Everything before that step does succeed, and two of those things matter: the
containers come up, and **Caddy obtains the TLS certificate** — so the failed
run does not cost you a certificate issuance when you re-run it.

### One-off schema provisioning

Before the AI service can migrate, the database needs the extension, the `ai`
schema and the `jbg_ai` role — a privileged, once-per-environment step that
migrations deliberately do not perform:

```bash
INSTANCE=$(cd terraform/demo && terraform output -raw instance_id)
AI_PWD=$(aws ssm get-parameter --name /jbg-demo/AI_DB_PASSWORD \
           --with-decryption --query Parameter.Value --output text)

aws ssm start-session --target "$INSTANCE"
# on the host:
sudo docker exec -i jbg-demo-postgres psql -U postgres -d joiabagur_pv \
  -v ai_password="$AI_PWD" < /opt/jbg-demo/ai-service/migrations/bootstrap.sql
```

> Pass the password **raw**. `psql`'s `:'var'` already renders it as a quoted
> literal; pre-quoting produces a password containing apostrophes that then
> fails to authenticate.

Re-run the workflow afterwards: `alembic upgrade head` now succeeds.

## 5. The data path

The corpus does not exist outside a laptop. It travels as a dump — **not
recomputed** — so that the published index is, row for row, the one the reported
figures describe. Recomputing would produce a *different* index and make those
figures describe a different system.

### 5.1 Measure the source

Before dumping, record what you expect to find on the other side: products,
collections, points of sale, inventory rows, approved AI profiles, indexed
documents, **and the embedding model recorded on the index**:

```bash
docker exec -i jpv-pv-postgres psql -U postgres -d joiabagur_pv <<'SQL'
SELECT 'products', count(*) FROM "Products"
UNION ALL SELECT 'collections',   count(*) FROM "Collections"
UNION ALL SELECT 'points_of_sale',count(*) FROM "PointOfSales"
UNION ALL SELECT 'inventory',     count(*) FROM "Inventories"
UNION ALL SELECT 'profiles_approved', count(*) FROM "ProductAiProfiles" WHERE "Status" = 1
UNION ALL SELECT 'documents',     count(*) FROM ai.product_document;
SELECT DISTINCT embedding_model FROM ai.product_document;
SQL
```

The distinct model **must** be `openai/text-embedding-3-small`, the literal in
`compose.demo.yaml`. If it is not, stop: the environment would answer 200s with
meaningless results, which is exactly what `/health` now reports as
`model_mismatch`.

### 5.2 Dump both schemas

```bash
docker exec jpv-pv-postgres pg_dump -U postgres -d joiabagur_pv \
  --schema=public --no-owner --no-acl > /tmp/demo-public.sql
docker exec jpv-pv-postgres pg_dump -U postgres -d joiabagur_pv \
  --schema=ai --no-owner --no-acl > /tmp/demo-ai.sql
```

### 5.3 Replace the shop's staff — mandatory

The dump carries the jewellery's real employees and their e-mail addresses. In a
publicly reachable environment they are replaced by two demonstration accounts,
one of each role, so both dashboards and the administrator-only diagnostics
block can be shown.

The catalog itself — real SKUs and real prices — **is** published: a business
decision taken explicitly.

After restoring, on the demo database:

```sql
-- Keep nothing of the real staff.
DELETE FROM "Users";
-- Then create the demonstration accounts, with BCrypt hashes at work factor 12 — the factor
-- the application itself uses — so the password check matches what it expects.
-- FOUR accounts: one administrator, and one operator per shop worth showing (see 5.8).
--   username demo.admin      e-mail demo.admin@joiabagur.example       role Administrator
--   username op-ciutadella   e-mail op-ciutadella@joiabagur.example    role Operator -> CIU-CENTRE
--   username op-fornells     e-mail op-fornells@joiabagur.example      role Operator -> FORNELLS
--   username op-aeroport     e-mail op-aeroport@joiabagur.example      role Operator -> MAO-AIR
```

> **What was actually done is not the `DELETE` above, and the difference matters later (5.9).** Sales,
> families, reviews and profiles reference `Users` with `ON DELETE RESTRICT`, so the rows were
> **renamed in place, keeping their `Id`**. Measured on 2026-09-28: the local `admin`
> (`3e03450b-…`) *is* `demo.admin` here, and the local operators survive as `demo.operador` and
> `retirado-<id-prefix>`. The `admin` row that exists now is a different one, recreated by the seeder
> (`77cef302-…`) and deactivated. Anything authored locally by `admin` therefore lands in the demo
> authored by `demo.admin`, with no remapping.

> **It used to say «exactly two accounts», and two turned out not to be enough.** C39a-bis found
> the demo holding only `demo.admin` and `demo.operador`, the latter bound to `MAO-AIR` — and with a
> single shop reachable, **abstention, substitutes and the agent's pivot cannot be demonstrated at
> all**, because each of them depends on the assortment of a *different* point of sale (5.8). The two
> synthetic operators that arrived in the dump had been renamed `retirado-<id-prefix>` and
> deactivated, which preserves the sales history their rows are referenced by; that is fine, and
> leaving it there is what made the environment undemonstrable. **The privacy rule is unchanged and
> absolute: no real employee, and no real e-mail address, may survive the restore.** The three
> operator accounts are synthetic, carry `@joiabagur.example` addresses, and hold the `Operator` role
> only.
>
> **`demo.operador` was then deactivated too**, on the same day and for a different reason: it was
> bound to `MAO-AIR`, which `op-aeroport` already covers, so it was a second credential for a counter
> that already had one. **Deactivated, never deleted — 3.380 sales reference it.** What is left is
> four accounts that sign in: one administrator, one operator per shop.
>
> **Sign-in is by `Username`, not by e-mail** (`AuthenticationService.LoginAsync` reads
> `GetByUsernameAsync`), so the usable accounts sign in as `demo.admin`, `op-ciutadella`,
> `op-fornells` and `op-aeroport`. Note that `demo.admin`
> carries a dot, which the API's own `CreateUserRequestValidator` rejects (`^[a-zA-Z0-9_]+$`) — as do the
> hyphens of the other three: all of them were
> created by SQL, and an earlier version of this section claimed otherwise. To reset one of these
> passwords later, generate the hash **off the host** and send only the hash — never the plaintext —
> then `update "Users" set "PasswordHash" = '<hash>', "UpdatedAt" = now() where "Username" = '…'`.
>
> The application's seeder recreates a `admin` / `Admin123!` account on every start **if no user named
> `admin` exists**, which the `DELETE` above guarantees. Leave that account **deactivated**
> (`IsActive = false`): `LoginAsync` refuses a deactivated user even with the right password, which is
> what keeps a default credential out of a publicly reachable environment. Verified on 2026-09-22.

Verify afterwards that **no** real address can authenticate:

```sql
SELECT "Email" FROM "Users";     -- exactly the two demonstration addresses
```

### 5.4 Restore and check the counts

```bash
aws ssm start-session --target "$INSTANCE"
# on the host, after bootstrap.sql and `alembic upgrade head`:
sudo docker exec -i jbg-demo-postgres psql -U postgres -d joiabagur_pv < demo-public.sql
sudo docker exec -i jbg-demo-postgres psql -U postgres -d joiabagur_pv < demo-ai.sql
```

Re-run the count query of §5.1 against the demo database and compare, number by
number, against what you recorded.

### 5.5 One reconciliation sync

The dump proves the data arrived. It does **not** prove the path that keeps it
up to date is wired. One synchronisation does:

```bash
# from the host, with an internal token signed by AI_SERVICE_SHARED_SECRET
sudo docker exec jbg-demo-ai python - <<'PY'
# POST /v1/index/sync, then GET /v1/index/status
PY
```

Expected: `drift_count = 0`. Anything else means the feed and the index disagree
about the catalog, and the environment must not be shown until it does not.

### 5.5b Three traps a wipe-and-restore sets, all found the hard way in C17

**The API reseeds `admin` / `Admin123!` on every start.** Its seeder's only guard
is "does any user named `admin` exist?", and after a truncate none does — so a
restart creates an administrator whose password is a constant in a **public**
repository, on a host open to the Internet. Deleting the row does not help: the
next restart recreates it. Leave one **disabled** row named `admin` with an
unusable hash: the seeder finds it and skips, and login rejects it on `IsActive`
before it ever checks the password.

**Password hashes minted outside .NET must use the `$2a$` prefix.** Python's
`bcrypt` emits `$2b$` by default, and the BCrypt.Net version here answers
`SaltParseException: Invalid salt version` — which escapes uncaught and turns a
login into a **500, not a 401**. Use `bcrypt.gensalt(12, prefix=b"2a")`. Do this
for the disabled accounts too: their hash never has to verify, but it does have
to *parse*.

**Do not read a hash file with `source`.** A line like `H=$2a$12$...` is an
unquoted assignment, and the shell eats `$2a` and `$12` as positional
parameters. The value arrives mangled and produces exactly the same
`SaltParseException`, which sends you hunting for the wrong bug. Read it with
command substitution instead: `H=$(grep '^H=' file | cut -d= -f2-)`.

### 5.5c Two drains the restore does not do, and without which the AI looks broken

Both are **once per environment** and survive restarts, because they write to the database. Both were
missing on this environment until C34 tripped over them on 2026-09-22.

**The point-of-sale availability projection — no longer a manual step since C41.** `ai.pos_projection`
is populated by draining the feed the API serves, and **retrieval refuses to work without it**:
`resolve_scope` raises rather than abstain over an empty projection, and the service answers **503**
to `/v1/retrieval/products` **and** `/v1/retrieval/substitutes`. The .NET side degrades correctly —
the search falls back to its lexical path and substitutes report `ai_unavailable`, both with a 200 —
so from outside the environment looks healthy while the assisted path is dead.

**C41 makes this self-healing**: `jbg-ai` drains the feed **when it starts**, in full when no
checkpoint exists, which is exactly the state a freshly deployed environment is in. Then every ten
minutes. So the container coming up is what populates the projection, and `verify.sh` **fails the
deployment** if it did not — that is its fifth condition, and it is why this step is now a safety net
rather than a requirement.

Run it by hand only to force a **full reconciliation** — after `IndexFeed:SalesAsOf` changes, or when
`GET /health` reports failed pages. A drain that overlaps the scheduled one declines and exits `75`,
writing nothing:

```bash
docker exec -i jbg-demo-ai python -m jbg_ai.indexing sync-pos --full
docker exec -i jbg-demo-postgres psql -U postgres -d joiabagur_pv -At -c 'select count(*), count(distinct pos_id) from ai.pos_projection'
```

To read the state instead of changing it, ask the health report — which is also what the
administrator dashboard card shows, and what `verify.sh` checks:

```bash
docker exec -i jbg-demo-ai python -c "import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8000/health'))['projection'], indent=2))"
```

**The knowledge corpus. ~~Does not ship in the AI image~~ — CLOSED BY C39a, and the step below is
kept only as the record of what used to be needed.** The corpus now travels inside the image, and
the path the service reads it from was fixed rather than worked around:

```bash
# Read-only check. Should print a real directory with the documents in it.
docker exec -i jbg-demo-ai python -c "from jbg_ai.knowledge.constants import CORPUS_DIR; import pathlib; p=pathlib.Path(CORPUS_DIR); print(p, p.is_dir(), len(list(p.glob('*.md'))))"
docker exec -i jbg-demo-postgres psql -U postgres -d joiabagur_pv -At -c 'select count(*) from ai.knowledge_chunk'
```

`verify.sh` fails the deployment when that count is zero, which it did not do before C39a, and
that was how this stayed invisible: with the fragments already indexed, an image with no corpus
answers everything correctly until somebody needs to re-index.

> **What it used to require, and why it kept working anyway.** `CORPUS_DIR` was derived by counting
> parent directories from the module file, which is right in a checkout and lands inside the
> virtual environment once the package is installed — measured here as
> `/app/.venv/lib/data/knowledge`. So the corpus had to be copied onto that path by hand after
> every new image:
>
> ```bash
> # HISTORICAL. Not needed since C39a; kept because it explains five weeks of silence.
> DEST=$(docker exec -i jbg-demo-ai python -c "from jbg_ai.knowledge.constants import CORPUS_DIR; print(CORPUS_DIR)")
> docker exec -u root -i jbg-demo-ai mkdir -p "$(dirname "$DEST")"
> docker cp /opt/jbg-demo/data/knowledge "jbg-demo-ai:$(dirname "$DEST")/"
> docker exec -i jbg-demo-ai python -m jbg_ai.indexing sync-knowledge --full
> ```
>
> **It survived five weeks unnoticed** because the indexed fragments live in `jbg-demo-pgdata` and a
> redeployment does not touch that volume: the environment served 161 fragments from the database
> while its image could not have produced a single one.

### 5.6 End-to-end check

Sign in as the **operator** account, run a natural-language search from
«Buscar con Ayuda», and confirm the badge reports the **assisted** origin — not
the degraded lexical path. A degraded badge with results still looks like it
works, which is precisely why it has to be read rather than assumed.

### 5.6b The sale card generates (C34)

The card has two routes, `POST /api/ai/products/{productId}/sales-assist` and
`GET /api/ai/products/{productId}/substitutes`, both switched on in this environment by
`AiSalesAssist__EnabledByDefault: "true"` and with the generative budget pinned by
`AiGateway__AssistTimeoutMs: "10000"` (start-up refuses anything below 8000). Three checks,
none of which needs the console or a key:

1. **The credential was picked up.** In `docker logs jbg-demo-ai`, after the first sale
   assistance request (the client is built lazily, once per process):

   ```text
   stage=assist_client model=openai/gpt-4o-mini timeout_s=4.0 credential=assist
   ```

   `credential=rag_fallback` would mean it fell back to the enrichment key; no
   `stage=assist_client` line at all means no client was built — the parameter is absent or
   empty, and `deploy.sh` said so (`Generation credential: absent`). A line
   `stage=router_client … credential=assist_fallback` is **expected** alongside it: the C31
   router falls back to this key, and it runs only for a free query with no product, which
   this environment never sends.
2. **An argument arrives, resolved.** As the operator, a sale assistance request for a piece
   the shop carries returns `aiAvailable: true`, `pitchStatus: "generated"`, a `promptVersion`
   and a `pitch` carrying the piece's catalog price as «39,90 €» and its units as a bare
   number — never `{{price}}` or `{{stock}}`. For a piece the shop has run out of, the same
   request with no question returns `withheld_out_of_stock`: that is the rule, not a fault.
3. **The container still fits.** `docker stats --no-stream jbg-demo-ai` against its 512 MiB
   limit (232.5 MiB before generation was switched on), and a handful of requests in a row
   to see whether the organisation's tokens-per-minute quota is what gives first.

### 5.6c The other two AI surfaces (C40, C42) — added by C39a

The environment served only the two surfaces above until C39a brought the branch up to date.
The other two have switches of their own, and **a missing switch is the failure this file has
now recorded three times** — C17 for search, C40_FIX for the free query, C39a for the agent:

| Surface | Switch | How to read it |
|---|---|---|
| **Free-query panel (M1)**, C40 | `AiFreeQuerySearch__EnabledByDefault: "true"` | the toggle in «Buscar con Ayuda» is reachable, a query with no piece is answered, and a query that is not about jewellery gets a **polite refusal** rather than an empty result |
| **Agent panel**, C42 | `AiAgentAssist__EnabledByDefault: "true"` | the **fourth card** of the hub is present, and a conversation paints the **loop trace**: tools per turn, iterations, stop reason |

Two things about the agent that are declared behaviour and not faults:

1. **Name the piece by its REFERENCE, not by its product name.** `buscar_catalogo` returns
   position, SKU, materials, variant and reasons — never the product name — so a name reaches
   `consultar_disponibilidad` as an unknown reference, the loop recovers by searching, and it
   cannot tell which of the candidates the customer meant. It then checks another piece and
   **correctly does not pivot**. Measured in C42's manual check; three fix options are recorded
   in `openspec/DEFERRED_TASKS.md`. Naming the reference is realistic at a counter, where the
   piece has its label in front of you.
2. **`stop_reason` is part of the answer.** `aclaracion` is the loop asking a question,
   `rechazado` the router refusing, and `sin_cliente` or `fallo_proveedor` a declared
   degradation — none of them is an error, and `verify.sh` is written not to fail on the last
   two.

## 5.7 Two ways to leave the demo quietly broken

Both were found by verifying C17 against the live environment, and both share the shape this
whole change is built to defend against: **the site keeps answering 200 with plausible
results**, so nobody notices.

### Stopping the AI container by hand does not undo itself

`restart: unless-stopped` deliberately does **not** restart a container that an operator
stopped — that is the difference between `unless-stopped` and `always`, and it is the right
default. So after a `docker stop jbg-demo-ai` or `docker kill jbg-demo-ai`, the container stays
down until someone starts it.

The environment survives that, which is the point of D18: the proxy, the API and the database
keep serving, and assisted search degrades to the lexical path. It also means the demo looks
fine. Verified: with the AI container down, a search returned **HTTP 200 with ten results** and
`aiAvailable: false`.

> If you stop it to debug, **start it again yourself**. And read `aiAvailable`, not the result
> count, when checking whether the assisted path is alive.

### Restarting outside `deploy.sh` skips the warm-up

`docker start jbg-demo-ai` brings the container back but does not run the warm-up call that
`deploy.sh` makes. The AI service builds its embedding client per request, so the first searches
pay a full cold round trip — measured after a bare restart at **5124 ms across two attempts**,
past the 2500 ms gateway budget, and therefore degraded.

It heals on its own: four consecutive queries went 0,84 → 0,42 s and reported
`aiAvailable: true` throughout. But it degrades **exactly when someone opens the demo for the
first time after a restart**, which is the worst possible moment.

> After restarting the AI container by hand, run one throwaway search before showing anything —
> or redeploy through `deploy.sh`, which warms it for you.

## 5.8 The demonstration accounts, and what each one reaches

**Added by C39a-bis, because an account list on its own is not enough.** The three operator accounts
are bound to points of sale with deliberately different assortments, and **which AI behaviours are
reachable at all depends on which account is used**. An evaluator handed a URL and one credential can
correctly conclude that abstention does not exist when it is merely out of reach.

**The environment holds exactly four accounts that can sign in: one administrator and one operator per
shop.** Everything else in the table below is a deactivated row kept for referential integrity, and
each says why. Four is the number on purpose — one credential per thing there is to see, and no
second credential pointing at a counter another one already covers.

Every password below is a public constant of the demonstration: the operators' come from the
synthetic world (`ai-service/src/jbg_ai/data/README.md`), and the administrator's has been published
in the project README since 2026-09-28 so an evaluator can sign in. None of them is held in the
parameter store, and none is a real employee's. **Rotate `demo.admin` once the evaluation is over**
(hash generated off the host, as the note in 5.3 describes).

| Username | Password | Role | Point of sale | What it is the account able to reach |
|---|---|---|---|---|
| `demo.admin` | `DemoAdmin123!` | Administrator | — | **The AI health card**, which is `[Authorize(Roles = "Administrator")]` and therefore reachable from no operator account, plus the family and profile review screens. Its hash was generated off the host; the plaintext is published for the evaluation and must be rotated afterwards. **This is the only administrator that can sign in** |
| `demo.operador` | **unusable by design** | Operator | `MAO-AIR` | **Deactivated on 2026-09-27**, and the row is kept rather than deleted because **3.380 sales reference it**. It duplicated `op-aeroport` — same shop, same reachable behaviour — and a second credential for the same counter only makes an evaluator wonder which one to use |
| `op-ciutadella` | `Operator123!` | Operator | `CIU-CENTRE` | **The happy path.** The largest assortment — 871 assigned rows — so assisted search returns stock everywhere and the sale card's argument is *generated* rather than withheld. Start here |
| `op-fornells` | `Operator123!` | Operator | `FORNELLS` | **Abstention, substitutes and the out-of-stock notice.** The smallest assortment — 241 assigned rows, of which **29 sit in the `0` bucket** — which is what makes a withheld argument and a substitute list reachable at all |
| `op-aeroport` | `Operator123!` | Operator | `MAO-AIR` | **The agent's pivot to substitutes.** The shop with the most stock-outs, so the loop can find a piece unavailable and go looking for an alternative. This is where the fourth card of the hub is worth opening |
| `admin` | **unusable by design** | Administrator | — | **Deactivated on purpose (`IsActive = false`), and it must stay that way.** The application's seeder recreates it on every start with a password that is a constant in a public repository; `LoginAsync` refuses a deactivated user even with the right password, and that is the only thing keeping a default credential out of an Internet-facing host. A `401` here is the system working |

### The one restriction that governs the agent, and it is declared rather than broken

**Name the piece by its reference, not by its product name.** `buscar_catalogo` returns position, SKU,
materials, variant and match reasons — **never the product's name** — so a loop asked about
«los Pendientes Luz de Faro» receives candidates identified only by SKU, cannot tell which of them was
the piece the customer meant, and **correctly declines to pivot**. Measured on the deployed
environment on 2026-09-27, the same question two ways:

| Asked as | Iterations | Tool calls | `buscar_sustitutos` | Outcome |
|---|---|---|---|---|
| `SKU1127` — **by reference** | 4 | 4 | **yes** | Availability checked, out of stock, **pivots**, then checks two alternatives |
| «Pendientes Luz de Faro» — by name | 3 | 2 | **no** | Searches the catalogue, checks one candidate, answers without pivoting |

This is a **declared limitation with its fix costed** in `openspec/DEFERRED_TASKS.md`, not a fault of
the environment — and it is realistic at a counter, where the piece has its label in front of the
operator.

### A `503` from a scoped search is one specific thing

If assisted search answers `503` for a shop, its row in `ai.pos_projection` is missing, not its
catalogue. Check `shops_without_scope` in the health card.

**Since C43 that number counts only ACTIVE shops, so it should read `0` here.** It used to count
`HT-ARTRUTX` — deliberately closed since 2025-09-30, keeping its 144 rows with every assignment
correctly retired — and therefore always read `1`, which failed the deployment of 2026-09-27 over
a healthy environment and painted a red line on the administrator's dashboard. The activity now
reaches the AI service through `ai.pos_shop`, filled by `GET /api/ai/index-feed/pos-shops`,
because the `jbg_ai` role is refused `SELECT` on `public."PointOfSales"`.

So the reading changed, and so did what a non-zero value means:

| What the health card says | What it means |
|---|---|
| `shopsWithoutScope: 0` | every trading shop has an assortment — the expected state |
| `shopsWithoutScope: null` | `ai.pos_shop` has not been drained yet; the service knows of no shop **and says so** rather than reporting a reassuring zero |
| `shopsWithoutScope: N > 0` | **N shops that are open have no assortment.** A real fault now, not a closed shop |

`verify.sh` fails the deployment on the last two. It also waits, up to 180 s, for the start-up
drains to report before judging — the health report is cached for 10 s and the boot drain can
need a second attempt, which on 2026-09-27 made the deployment log record a staleness the drain
had already cured six seconds earlier.

## 5.9 Bringing post-deployment local work into the demo

The demo database was restored from a dump taken on **2026-08-30**. Family suggestion and review,
the vocabulary re-enrichment and the human profile review all happened afterwards, **in the local
database only**, so until 2026-09-28 the demo showed 0 families, 0 human reviews and 1.200 indexed
documents. This is how that work was brought across, and how to do it again.

**A targeted copy, not a full restore.** A full restore would erase the four demonstration accounts
(the `demo.admin` hash exists only here), force 5.3 again and drag local checkpoints along. Only the
tables the local work changed are copied; `Users`, `UserPointOfSales`, sales, inventory, search
events, migration history, `ai.pos_projection`, `ai.pos_shop`, `ai.sync_*` and `ai.knowledge_*` are
left alone.

| Copied (local → demo) | Rows on 2026-09-28 |
|---|---|
| `public."ProductFamilies"` / `"ProductFamilyMembers"` / `"FamilyReviewVerdicts"` | 156 / 492 / 64 |
| `public."ProductAiProfiles"` | 1.200 — 204 reviewed by a person, all timed |
| `ai.product_document` | 1.168 on arrival, 1.167 after the reconciliation sync |
| `ai.eval_run` / `ai.eval_case` / `ai.eval_result` | 4 / 192 / 6.970 |
| `public."Products"."UpdatedAt"` | 16 rows, the products whose family changed |

**Preconditions, all read-only, both sides — stop if any differs:** the same `ai.alembic_version`
and last `__EFMigrationsHistory` entry; the same
`md5(string_agg("Id"::text||"SKU", ',' ORDER BY "Id"))` over `"Products"`; the local reviewer's
`Id` present in the demo (see the note in 5.3); and no demo row of those tables touched by hand
(`"UpdatedAt" > '2026-08-30 12:30'` returns 0).

**Steps as run on 2026-09-28:**

1. Back up the demo on the host before writing anything:
   `docker exec jbg-demo-postgres pg_dump -U postgres -d joiabagur_pv -Fc -f /tmp/pre-sync-demo.dump`,
   then `docker cp` it to `/root/`, plus a data-only dump of `Users` and `UserPointOfSales`.
2. Locally, `pg_dump --data-only --no-owner --no-acl -t …` of the tables above, wrapped in one
   script: `\set ON_ERROR_STOP on`, `BEGIN`, `DELETE` in foreign-key order (verdicts → members →
   families, profiles, `product_document`, `eval_result` → `eval_case` → `eval_run`), the dump, the
   `UPDATE`s of `"Products"."UpdatedAt"`, counts, `COMMIT`. **Dry-run it locally with `ROLLBACK`
   first.**
3. Move it through S3 with a presigned URL — the host role has no S3 permission and does not need
   one: `aws s3 cp` to `s3://jbg-demo-terraform-state/transfer/`, `aws s3 presign --expires-in 900`,
   `curl` + `sha256sum -c` on the host, `docker cp` into the container, `psql -f`. Delete the object
   afterwards.
4. Reconcile: `docker exec jbg-demo-ai python -m jbg_ai.indexing sync --full`. On 2026-09-28 it
   reported `upserted=173 skipped=994 deleted=1`: the upserts are products whose profile was corrected
   after the last *local* indexing, and the delete is the one profile rejected by hand.
5. `verify.sh`, which passed: 1.167 documents, projection fresh, 161 knowledge fragments, agent route
   answering.

**Rollback:** `pg_restore --clean -d joiabagur_pv` from `/root/pre-sync-demo.dump`, then `sync --full`.

## 6. Moving to a purchased domain

Nothing is rebuilt. The hostname is configuration end to end:

1. Point an `A` record at the elastic IP (`terraform output -raw public_ip`).
2. Set `demo_hostname` in `terraform.tfvars`, `terraform apply` — this updates
   `/jbg-demo/DEMO_HOSTNAME`.
3. Re-run the workflow. The proxy requests a certificate for the new name on the
   first request and keeps serving the old one until it has it.

Do **not** delete `jbg-demo-caddy-data` in the process. See the warning at the
top.

## 7. Tearing it down

```bash
cd terraform/demo && terraform destroy
```

The cost stops, and by construction the shop's account cannot be affected: no
shared state, no shared account, no shared resource.
