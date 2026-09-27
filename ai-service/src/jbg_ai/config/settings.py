"""Application settings loaded from environment via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Imported rather than restated, so the library default and the environment default cannot
# drift: `assist/constants.py` carries the value together with the measurement that set it.
from jbg_ai.assist.constants import (
    AGENT_TIMEOUT_SECONDS as DEFAULT_AGENT_TIMEOUT_SECONDS,
    DEFAULT_AGENT_MODEL,
    DEFAULT_ASSIST_MODEL,
    DEFAULT_ROUTER_MODEL,
    PITCH_TIMEOUT_SECONDS as DEFAULT_ASSIST_PITCH_TIMEOUT_SECONDS,
    ROUTER_TIMEOUT_SECONDS as DEFAULT_ROUTER_TIMEOUT_SECONDS,
)

PRODUCTION_ENV_NAMES = frozenset({"prod", "production"})

CANONICAL_OPENAPI_SERVICE_VERSION = "0.1.0"

#: C21 fusion defaults, in one place so the field default, the blank-string fallback and
#: the canonical OpenAPI profile cannot drift apart. Every value is measured, and the
#: measured figures live in the C21 report rather than in the field descriptions below: a
#: figure copied into a description is a snapshot that nothing re-measures, so it starts
#: lying the first time the corpus or the index moves. The reasoning is in
#: `retrieval/fusion.py`.
FUSION_DEFAULTS: dict[str, Any] = {
    "jpv_rrf_k": 60,
    "jpv_branch_depth": 60,
    # --- C25: the fusion is composed in two stages, and the per-BRANCH weights are the pair
    # the sweep explores. Only their RATIO changes the order (scaling both preserves it, which
    # was measured), so the grid is one-dimensional and is expressed as rho = w_vec / w_lex.
    "jpv_branch_weight_lexical": 0.5,
    "jpv_branch_weight_vector": 0.5,
}

# --- C25bis retired four knobs from this block, and the reasons were not the same for all four.
#
# `JPV_FUSION_MODE` selected between the two-stage composition and C21's single fusion over
# every list. The second was kept selectable only so the published baseline row could be
# re-measured; once that table was published and frozen it became a dead path whose arithmetic
# the project had measured as defective, and a dead path that can be switched on by accident is
# how a corrected defect returns.
#
# `JPV_RRF_WEIGHT_TYPED` and `JPV_RRF_WEIGHT_EXPANDED` were NOT dead — they were the internal
# split of the lexical branch, on the live path. They went because the specification requires
# the two to be equal and forbids sweeping them, so a setting could only ever be moved into
# violation with nothing to detect it. A knob the rules forbid touching is worse than a dead
# one: it looks like a decision. They now live as `LEXICAL_INTERNAL_WEIGHT` in the orchestrator,
# and the move could not change a result because only stage one's ORDER reaches stage two.
#
# `JPV_RRF_WEIGHT_VECTOR` was the only one genuinely without a reader outside the retired path.
#
# A deployment that still exports any of the four has NO effect: they no longer exist, and the
# service composes the one way it can. Nothing is added to make the boot fail over them —
# what a run actually composed is recorded in the provenance of an evaluation run, which is
# where a reader can act on it, rather than inferred from the environment somebody intended.

#: C25 business-signal weights. Two weights, and they are NOT the same kind of number.
#:
#: `availability` is **calibrated**: it is swept against the golden set under the operational
#: metric of D3, with pure relevance as the guardrail. That sweep is possible because the
#: rubric's own scale supplies the hook — grade 1 is already defined as "a plausible
#: substitute the operator would offer second", and a piece that cannot be put on the cloth is
#: exactly that, so an exhausted grade 2 can be read as a grade 1 without inventing a constant.
#:
#: ONE weight, and it was two. The rotation term was **withdrawn, refuted by measurement**:
#: as the strict tiebreak its requirement described it decided 0 pairs in the top five across
#: all 48 queries, and as a component of the ordering key it was no tiebreak at all — it
#: inverted 11.067 pairs, 71,2 % of them more than ten positions apart, and cost relevance
#: where it acted. The figures are in the C25 implementation report.
#:
#: `availability` is read against the `computed_as_of` recorded on each projection row and
#: never against the wall clock: with a wall clock the figures go to zero, because the world
#: of C10 ends on 2026-08-23, and the ranking would be irreproducible by design.
BUSINESS_DEFAULTS: dict[str, Any] = {
    "jpv_business_weight_availability": 1.0,
}

#: C26 substitutes. ONE weight, and it is NOT the same kind of number as the availability
#: one above even though both ride in the same tail.
#:
#: `availability` there is binary against a key that was otherwise lexicographic, so its
#: value could not change the order — only its sign could, and the C25 sweep measured exactly
#: that. **That conclusion does not travel here.** In this ordering a binary size term is
#: mixed with a CONTINUOUS cosine similarity, so the weight fixes a real exchange rate — how
#: much similarity a wrong size is worth — and three values produce three different orders.
#: It is therefore swept, and the sweep is what fixes it; the figure of the last one is in
#: the C26 implementation report rather than here, where nothing would re-measure it.
#:
#: Zero is the rollback and reproduces exactly the ordering the remaining terms produce
#: alone. The term is inert whenever either side declares no size, because an absent size is
#: not a mismatch — 54 % of the rings carry none, so without that guard half the population
#: of the most affected piece type would be ordered by a mismatch that does not exist.
SUBSTITUTE_DEFAULTS: dict[str, Any] = {
    "jpv_substitute_weight_size": 0.05,
}

#: C25 abstention. The FORM was selected by a measurement under a criterion written before it
#: — the two populations of best-hit distance overlap completely, so a scalar bound cannot
#: separate them — and the relative rule reads the SHAPE of the distance profile instead: an
#: out-of-domain query is flat, because nothing in the catalogue stands out for it.
#:
#: **Fixed against the category once it grew to 20**, never against the five it had: two
#: parameters fitted to five points are fitted to five points, which is what this change
#: refused to do everywhere else. Measured over 20 out-of-domain and 43 answerable queries,
#: this point abstains on **2 of the 20 and on none of the 43** — the only operating points
#: that silence no answerable query are this one and two that catch less.
#:
#: The rate it buys is **10 %**, far from the 0,80 the ticket asked for, and the gap is
#: declared rather than closed: reaching 0,80 costs silencing **21 of the 43** answerable
#: queries, half the set. The asymmetry decides the point — silencing a query the shop CAN
#: answer is a visible failure at the counter, while failing to abstain on an impossible one
#: merely shows five pieces that do not fit and the operator can see that.
#:
#: It is on because the alternative signal does not do this job: `low_confidence` fires on 1
#: of the 20 out-of-domain queries and on 10 of the 43 answerable ones, which is
#: anti-correlated with what abstention needs.
ABSTENTION_DEFAULTS: dict[str, Any] = {
    "jpv_abstention_enabled": True,
    "jpv_abstention_band_alpha": 0.03,
    "jpv_abstention_band_min_candidates": 15,
}


#: C23 knowledge defaults, in one place for the same reason as FUSION_DEFAULTS: the field
#: default, the blank-string fallback and the canonical OpenAPI profile are three copies of
#: one value, and three copies drift. The threshold is the output of a calibration RULE and
#: not a preference; the rule, and the sweep that last applied it, are recorded in the C23
#: implementation report rather than here, where nothing would ever re-measure them.
#:
#: The threshold is the one the rule yields **against the production embedder on the live
#: index**, which is not the one the offline sweep yields: the stand-in scores lexical
#: overlap, so its distances live on another scale entirely and its optimum admits questions
#: the corpus does not cover. The offline sweep still calibrates the rule — it is what runs
#: without a provider — but the number has to come from the real index, and the tests keep
#: the two apart on purpose.
KNOWLEDGE_DEFAULTS: dict[str, Any] = {
    "jpv_knowledge_distance_threshold": 0.51,
    "jpv_knowledge_hybrid_enabled": True,
}


class Settings(BaseSettings):
    """C02 settings: fail fast on missing APP_ENV / SERVICE_VERSION / JWT_SECRET."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(..., min_length=1, description="Deployment environment name")
    service_version: str = Field(..., min_length=1, description="Service version string")
    log_level: str = Field(default="INFO", description="Logging level")
    jwt_secret: str = Field(
        ...,
        min_length=1,
        description="HS256 secret shared with the .NET API for the internal service token",
    )
    jwt_ttl_seconds: int = Field(
        default=300,
        gt=0,
        description="Documented TTL for internal tokens; the .NET API is the issuer",
    )
    stub_mode: bool = Field(
        default=True,
        description="Serve deterministic fixtures instead of real retrieval/enrichment logic",
    )
    enable_dev_endpoints: bool = Field(
        default=True,
        description="Mount development-only routes such as GET /v1/evals/runs",
    )
    database_url: str | None = Field(
        default=None,
        description=(
            "PostgreSQL connection string for schema `ai`, e.g. "
            "postgresql+psycopg://user:password@host:5432/db. Optional on purpose: "
            "the service must boot without a database, so the engine is built on "
            "first use and its absence only surfaces when a session is requested"
        ),
    )
    db_pool_size: int = Field(
        default=5,
        gt=0,
        description=(
            "Hard ceiling on simultaneous connections, with no overflow. Sized against "
            "the project-wide connection budget, which is shared with the .NET API"
        ),
    )
    jpv_catalog_llm_api_key: str | None = Field(
        default=None,
        description=(
            "C06b generate only (JPV_CATALOG_LLM_API_KEY). Distinct from "
            "JPV_RAG_LLM_API_KEY (C09 runtime). Not required to boot /health."
        ),
    )
    jpv_catalog_llm_model: str | None = Field(
        default=None,
        description="Optional model id for the catalog CLI. Absence does not block /health.",
    )
    jpv_catalog_llm_base_url: str | None = Field(
        default=None,
        description="Optional OpenAI-compatible base URL for the catalog CLI.",
    )
    jpv_rag_llm_api_key: str | None = Field(
        default=None,
        description=(
            "C09 runtime enrichment (JPV_RAG_LLM_API_KEY). Distinct from "
            "JPV_CATALOG_LLM_API_KEY. Not required to boot /health."
        ),
    )
    jpv_rag_llm_model: str | None = Field(
        default=None,
        description="Optional provider-prefixed model id (e.g. openai/gpt-4o).",
    )
    jpv_rag_llm_base_url: str | None = Field(
        default=None,
        description="Optional LiteLLM api_base (proxy / Azure / local).",
    )
    jpv_rag_llm_concurrency: int = Field(
        default=8,
        gt=0,
        description="In-flight enrichment calls per batch.",
    )
    jpv_embedding_api_key: str | None = Field(
        default=None,
        description=(
            "C11 embeddings (JPV_EMBEDDING_API_KEY). Distinct from "
            "JPV_RAG_LLM_API_KEY and JPV_CATALOG_LLM_API_KEY. Not required "
            "to boot /health; required when embedding."
        ),
    )
    jpv_embedding_model: str | None = Field(
        default=None,
        description=(
            "Optional provider-prefixed embedding model "
            "(e.g. openai/text-embedding-3-small)."
        ),
    )
    jpv_embedding_base_url: str | None = Field(
        default=None,
        description="Optional LiteLLM api_base for embeddings (proxy / Azure).",
    )
    jpv_embedding_batch_size: int = Field(
        default=64,
        gt=0,
        description="Texts per provider embedding call.",
    )
    jpv_index_feed_base_url: str | None = Field(
        default=None,
        description=(
            "C13 catalog index feed (JPV_INDEX_FEED_BASE_URL). .NET API origin "
            "for GET /api/ai/index-feed/catalog. Distinct from JWT_SECRET. "
            "Not required to boot /health; required for a real catalog sync."
        ),
    )
    jpv_index_feed_api_key: str | None = Field(
        default=None,
        description=(
            "C13 catalog index feed (JPV_INDEX_FEED_API_KEY). Sent as "
            "X-Index-Feed-Key. Distinct from JWT_SECRET and JPV_EMBEDDING_*. "
            "Not required to boot /health; required for a real catalog sync. "
            "Must not fall back to JWT_SECRET."
        ),
    )
    jpv_index_sync_time_budget_seconds: int = Field(
        default=180,
        gt=0,
        description=(
            "Wall-clock budget for one catalog drain (HTTP or CLI). Checked after "
            "each item; exhaustion persists a resume cursor."
        ),
    )
    jpv_assist_llm_api_key: str | None = Field(
        default=None,
        description=(
            "C30b credential for the sale argument (JPV_ASSIST_LLM_API_KEY). **Optional, and "
            "it falls back to JPV_RAG_LLM_API_KEY**: making it required would stop an existing "
            "deployment generating the day this field appeared, and it would do it silently — "
            "the route degrades to 200 without prose rather than failing. Set it to bill, "
            "rate-limit and rotate counter-side generation apart from C09 enrichment; the "
            "resolved choice is logged when the client is built. Not required to boot /health."
        ),
    )
    jpv_assist_llm_model: str = Field(
        default=DEFAULT_ASSIST_MODEL,
        min_length=1,
        description=(
            "C30b model that writes the sale argument (JPV_ASSIST_LLM_MODEL). Deliberately its "
            "OWN variable and never JPV_RAG_LLM_MODEL: that one is C09's enrichment model, and "
            "inheriting it would let a change to enrichment move a counter-side model whose "
            "cost, latency and rejection rate were measured on another. The default is the "
            "model every C30b figure was measured on. It must support structured output; one "
            "that does not degrades to the structured response and records the cause."
        ),
    )
    jpv_assist_pitch_timeout_seconds: float = Field(
        default=DEFAULT_ASSIST_PITCH_TIMEOUT_SECONDS,
        gt=0,
        le=60,
        description=(
            "C30b seconds one generation call of POST /v1/assist/sale may take "
            "(JPV_ASSIST_PITCH_TIMEOUT_SECONDS). Per call and not per request: the ceiling "
            "is two calls. Supplies only the DEFAULT — the effective value travels as a "
            "parameter of the client, so an evaluation can sweep it in one process. "
            "Exceeding it degrades to the structured response with 200, never an error. "
            "Not required to boot /health."
        ),
    )
    jpv_router_llm_api_key: str | None = Field(
        default=None,
        description=(
            "C31 credential for the intent classifier (JPV_ROUTER_LLM_API_KEY). **Optional, and "
            "it falls back in a chain: router, then JPV_ASSIST_LLM_API_KEY, then "
            "JPV_RAG_LLM_API_KEY.** C30b opened the last two links; this prepends one. With "
            "none of the three the classifier is not constructed at all, which is a declared "
            "deployment state and not a failure: the route behaves exactly as it did before it "
            "routed anything, and that is also the ablation and the rollback. The resolved "
            "choice is logged when the client is built, so which credential is in force is "
            "something a deployment can check instead of assume. Not required to boot /health."
        ),
    )
    jpv_router_llm_model: str = Field(
        default=DEFAULT_ROUTER_MODEL,
        min_length=1,
        description=(
            "C31 model that classifies the query (JPV_ROUTER_LLM_MODEL). Deliberately its OWN "
            "variable and never JPV_ASSIST_LLM_MODEL nor JPV_RAG_LLM_MODEL: these are calls of "
            "very different shape — around thirty output tokens against a paragraph — so "
            "sharing a variable would make any cost comparison between them false. It must "
            "support structured output; one that does not degrades to an unclassified intent "
            "and records the cause."
        ),
    )
    jpv_router_timeout_seconds: float = Field(
        default=DEFAULT_ROUTER_TIMEOUT_SECONDS,
        gt=0,
        le=60,
        description=(
            "C31 seconds the single classifier call of POST /v1/assist/sale may take "
            "(JPV_ROUTER_TIMEOUT_SECONDS). **The default is declared NOT calibrated**: it is a "
            "product judgement taken on a developer machine through a TLS interceptor, and it "
            "is an upper bound rather than a budget. Supplies only the DEFAULT — the effective "
            "value travels as a parameter of the client, so an evaluation can sweep it in one "
            "process. Exceeding it is a fail-open: the request proceeds unclassified and is "
            "served exactly as it was before routing existed. Not required to boot /health."
        ),
    )

    jpv_agent_llm_api_key: str | None = Field(
        default=None,
        description=(
            "C32b credential for the agent loop (JPV_AGENT_LLM_API_KEY). **Optional, and it "
            "falls back in a chain: agent, then JPV_ASSIST_LLM_API_KEY, then "
            "JPV_RAG_LLM_API_KEY.** With none of the three the loop is not constructed at all: "
            "POST /v1/assist/agent answers without running it rather than failing, which is a "
            "declared deployment state and is the rollback and the ablation at once — removing "
            "the credential is how a deployment returns to the behaviour that preceded the "
            "loop. The resolved link is logged once per process, so which credential is in "
            "force is something a deployment can check instead of assume. Not required to boot "
            "/health, and POST /v1/assist/sale never reads it."
        ),
    )
    jpv_agent_llm_model: str = Field(
        default=DEFAULT_AGENT_MODEL,
        min_length=1,
        description=(
            "C32b model that runs the agent loop (JPV_AGENT_LLM_MODEL). Deliberately its OWN "
            "variable and never JPV_ASSIST_LLM_MODEL nor JPV_ROUTER_LLM_MODEL: choosing which "
            "TOOL to call is a harder task than choosing which label, and sharing a variable "
            "would make any comparison of cost between the three false. It must support "
            "function calling. **It is also the cheapest lever this capability has**: the model "
            "multiplier of the agent's overhead against the deterministic pipeline is this one "
            "setting, so pointing it at a cheaper model reverts that multiplier with no code "
            "change. Not required to boot /health."
        ),
    )
    jpv_agent_timeout_seconds: float = Field(
        default=DEFAULT_AGENT_TIMEOUT_SECONDS,
        gt=0,
        le=60,
        description=(
            "C32b seconds ONE turn of the loop may take (JPV_AGENT_TIMEOUT_SECONDS). Per call "
            "and never per request: a request makes up to five of them, and measuring the "
            "total against a one-call limit is how a small cut reads as a large one. **The "
            "default is declared NOT calibrated** — it is the wall-clock budget divided by the "
            "iteration ceiling, an upper bound rather than a budget. Supplies only the DEFAULT: "
            "the effective value travels as a parameter of the client, so an evaluation can "
            "sweep it in one process. A turn that exceeds it costs the turn and not the "
            "request, and the evidence already gathered is served. Not required to boot /health."
        ),
    )

    jpv_retrieval_distance_threshold: float = Field(
        default=0.65,
        gt=0,
        le=2,
        description=(
            "C14 cosine-distance cutoff for POST /v1/retrieval/products "
            "(JPV_RETRIEVAL_DISTANCE_THRESHOLD). Optional at boot. "
            "Domain is pgvector cosine distance (0, 2]. Distinct from "
            "JWT_SECRET, JPV_EMBEDDING_*, JPV_RAG_LLM_*, JPV_INDEX_FEED_* "
            "and JPV_CATALOG_LLM_*. Not required to boot /health."
        ),
    )

    jpv_query_expansion_enabled: bool = Field(
        default=True,
        description=(
            "C20 query-side synonym expansion for the lexical branch "
            "(JPV_QUERY_EXPANSION_ENABLED). Optional at boot; default true. This "
            "supplies only the DEFAULT: the effective value travels as a parameter of "
            "the retrieval orchestration call, because C24 sweeps configurations in one "
            "process and an environment-only switch would force a restart per config, "
            "while a request field would move the frozen openapi.json. Default is on "
            "because, measured on the live index, the lexical branch answers NOTHING AT "
            "ALL without it for ordinary surface-form variants of catalogue vocabulary; "
            "the flag exists so C24 can ablate, not because the finding is in doubt. Turning "
            "it off is also the rollback for C20. Distinct from JWT_SECRET, "
            "JPV_EMBEDDING_*, JPV_RAG_LLM_*, JPV_INDEX_FEED_*, JPV_CATALOG_LLM_* and "
            "JPV_RETRIEVAL_DISTANCE_THRESHOLD. Not required to boot /health, which never "
            "loads the dictionary."
        ),
    )

    jpv_rrf_k: int = Field(
        default=FUSION_DEFAULTS["jpv_rrf_k"],
        gt=0,
        description=(
            "C21 smoothing constant of the reciprocal rank fusion (JPV_RRF_K). Optional at "
            "boot; a blank export means unset and falls back to the default. It is not "
            "independent of JPV_BRANCH_DEPTH: k governs how slowly a document's vote decays "
            "as its rank grows, so a deeper branch keeps more of its tail voting and the two "
            "must be swept together, never one at a time. Distinct from JWT_SECRET, JPV_EMBEDDING_*, "
            "JPV_RAG_LLM_*, JPV_INDEX_FEED_*, JPV_CATALOG_LLM_*, "
            "JPV_RETRIEVAL_DISTANCE_THRESHOLD and JPV_QUERY_EXPANSION_ENABLED. Not required "
            "to boot /health."
        ),
    )

    jpv_branch_weight_lexical: float = Field(
        default=FUSION_DEFAULTS["jpv_branch_weight_lexical"],
        ge=0,
        description=(
            "C25 weight of the whole LEXICAL BRANCH in the inter-branch fusion "
            "(JPV_BRANCH_WEIGHT_LEXICAL), used only in 'branch' mode. Optional at boot; blank "
            "means unset. It is the branch's TOTAL vote, whatever number of lists it is "
            "composed of and however many of them matched — which is the property the flat "
            "mode lacks, where the crossover threshold is 0.469 or 0.938 depending on whether "
            "the typed list happened to match. Supplies only the DEFAULT: the effective value "
            "travels as a parameter of the orchestration call. Not required to boot /health."
        ),
    )

    jpv_branch_weight_vector: float = Field(
        default=FUSION_DEFAULTS["jpv_branch_weight_vector"],
        ge=0,
        description=(
            "C25 weight of the VECTOR BRANCH in the inter-branch fusion "
            "(JPV_BRANCH_WEIGHT_VECTOR), used only in 'branch' mode. Optional at boot; blank "
            "means unset. Equal to the lexical branch weight by default, and that is a value "
            "of PRINCIPLE rather than a fitted one: each branch holds one vote, the best hit "
            "of each takes one of the first two places, and what both branches point at goes "
            "first. Only the RATIO to JPV_BRANCH_WEIGHT_LEXICAL changes the order, so the "
            "sweep over the two is one-dimensional. Not required to boot /health."
        ),
    )

    jpv_branch_depth: int = Field(
        default=FUSION_DEFAULTS["jpv_branch_depth"],
        gt=0,
        description=(
            "C21 depth at which EVERY fused list is truncated before fusing "
            "(JPV_BRANCH_DEPTH). Optional at boot; a blank export means unset and falls back "
            "to the default. One value shared by all three lists, because cutting the lexical "
            "branches deeper than the vector one was measured to cost accuracy rather than "
            "buy it. Conceptually distinct from the over-retrieval window the endpoint "
            "returns, which follows `top_k`, even where the two happen to share a default — "
            "reusing the existing OVER_RETRIEVAL_CAP is one fewer arbitrary constant, not the "
            "same parameter. Not "
            "required to boot /health."
        ),
    )

    jpv_business_weight_availability: float = Field(
        default=BUSINESS_DEFAULTS["jpv_business_weight_availability"],
        ge=0,
        description=(
            "C25 weight of the availability signal, and the ONLY business weight "
            "(JPV_BUSINESS_WEIGHT_AVAILABILITY). Optional at boot; a blank export means unset "
            "and falls back to the default. Its SIGN is what the calibration decided, not its "
            "value: with a single binary term the score takes two values, so every positive "
            "weight produces the same ranking — the sweep measured exactly that, and 1.0 is a "
            "declared unit rather than a fitted figure. Zero restores exactly the ordering the "
            "fusion and the typed-constraint blocks produce on their own, which makes it the "
            "rollback for the business signals. Supplies only the DEFAULT: the effective value "
            "travels as a parameter of the orchestration call. Not required to boot /health."
        ),
    )

    jpv_substitute_weight_size: float = Field(
        default=SUBSTITUTE_DEFAULTS["jpv_substitute_weight_size"],
        ge=0,
        description=(
            "C26 weight of the size-mismatch term in the substitutes ordering "
            "(JPV_SUBSTITUTE_WEIGHT_SIZE). Optional at boot; a blank export means unset and "
            "falls back to the default. Unlike JPV_BUSINESS_WEIGHT_AVAILABILITY its VALUE is "
            "what the calibration decided and not merely its sign: this key mixes a binary "
            "size term with a continuous cosine similarity, so the weight fixes an exchange "
            "rate — how much similarity a wrong size is worth — and different values produce "
            "different orders. It is a CONTINUOUS term and never an integer block, because a "
            "block would send every candidate of another size behind every candidate of the "
            "right one instead of breaking a tie. The term is inert unless both the source "
            "product and the candidate declare a size, since an absent size is not a "
            "mismatch. Zero is the rollback and reproduces exactly the ordering the "
            "remaining terms produce alone. Supplies only the DEFAULT: the effective value "
            "travels as a parameter of the call, so a sweep needs no restart. Not required "
            "to boot /health."
        ),
    )

    jpv_abstention_enabled: bool = Field(
        default=ABSTENTION_DEFAULTS["jpv_abstention_enabled"],
        description=(
            "C25 relative abstention rule (JPV_ABSTENTION_ENABLED). Optional at boot; blank "
            "means unset. Default TRUE, fixed against 20 out-of-domain and 43 answerable "
            "queries: at the configured band it abstains on 2 of the 20 and on NONE of the "
            "43. Setting it false is the rollback and restores the behaviour of answering "
            "every query. Not required to boot /health."
        ),
    )

    jpv_abstention_band_alpha: float = Field(
        default=ABSTENTION_DEFAULTS["jpv_abstention_band_alpha"],
        ge=0,
        description=(
            "C25 half-width of the band around the best retrieval distance, as a fraction of "
            "it (JPV_ABSTENTION_BAND_ALPHA). With JPV_ABSTENTION_BAND_MIN_CANDIDATES it says "
            "when a distance profile is FLAT — nothing stands out — which is the shape an "
            "out-of-domain query has. A starting point measured on five queries, not a fixed "
            "figure. Not required to boot /health."
        ),
    )

    jpv_abstention_band_min_candidates: int = Field(
        default=ABSTENTION_DEFAULTS["jpv_abstention_band_min_candidates"],
        gt=0,
        description=(
            "C25 how many candidates must fall inside the band before the profile counts as "
            "flat (JPV_ABSTENTION_BAND_MIN_CANDIDATES). See JPV_ABSTENTION_BAND_ALPHA. Not "
            "required to boot /health."
        ),
    )

    jpv_pos_prefilter_enabled: bool = Field(
        default=True,
        description=(
            "C22 point-of-sale prefilter for POST /v1/retrieval/products "
            "(JPV_POS_PREFILTER_ENABLED). Optional at boot; default true; blank -> true. "
            "Supplies only the DEFAULT: the effective value travels as a parameter of the "
            "retrieval orchestration call, in the same pattern as "
            "JPV_QUERY_EXPANSION_ENABLED, because C24 sweeps configurations in one process "
            "and putting it on the request would move the frozen openapi.json. With it off, "
            "retrieval behaves exactly as it did before the projection existed, which makes "
            "it the rollback for this change: no deploy, no migration to undo, and "
            "ai.pos_projection can stay populated because nothing else reads it. Default on "
            "because, probed against the live index, MOST points of sale were left with a "
            "very short result page on a large share of ordinary searches once the .NET side "
            "had dropped what they do not carry — worst case a single surviving product, and "
            "one query with none. The figures are in the C22 report. Not required to boot /health."
        ),
    )

    jpv_pos_projection_max_age_seconds: int = Field(
        default=3600,
        gt=0,
        description=(
            "C22 staleness ceiling of ai.pos_projection "
            "(JPV_POS_PROJECTION_MAX_AGE_SECONDS). Optional at boot; a blank export means "
            "unset and falls back to the default. Above it the point-of-sale scope is NOT "
            "applied for that request, the "
            "degradation is logged, and the response still reports the age: a stale "
            "projection may leave the page short, but it must never hide a valid product "
            "from the .NET authority. Deliberately generous next to the refresh cadence, which "
            "is a cron: the ceiling must degrade only under sustained failure and not under "
            "ordinary lateness. Degrading eagerly would surrender the "
            "whole benefit of the change on any transient. Measured against "
            "ai.sync_checkpoint.last_incremental_sync_at, never against "
            "ai.pos_projection.refreshed_at, which records when an assignment last changed "
            "and would report months on a projection synchronised seconds ago. Not required "
            "to boot /health."
        ),
    )

    jpv_pos_sync_scheduler_enabled: bool = Field(
        default=True,
        description=(
            "C41 scheduled drain of ai.pos_projection "
            "(JPV_POS_SYNC_SCHEDULER_ENABLED). Optional at boot; default true; blank -> true. "
            "Drains the pos-availability feed ONCE AT START-UP and then on an interval, "
            "reusing the same drain the CLI invokes rather than reimplementing the keyset "
            "protocol. Default ON, and that is deliberate: off by default would reproduce the "
            "exact defect this change closes -- something somebody has to remember to switch "
            "on. C22 shipped a documented cron instead and it was never installed, because "
            "the recipe began by changing into a host directory while this service ships as "
            "a container; the projection then ran twenty days stale across three separate "
            "sessions. Switching it OFF restores exactly the behaviour that preceded this "
            "setting -- the CLI as the only drain -- which makes it both the ablation and the "
            "rollback: no deploy to undo and no migration. Not required to boot /health, and "
            "the scheduler is not started at all under STUB_MODE or without a configured feed."
        ),
    )

    jpv_pos_sync_interval_seconds: int = Field(
        default=600,
        gt=0,
        description=(
            "C41 interval between scheduled POS drains "
            "(JPV_POS_SYNC_INTERVAL_SECONDS). Optional at boot; a blank export means unset "
            "and falls back to the default. DERIVED FROM THE CEILING, NOT CHOSEN: what "
            "matters is not the cadence but how many consecutive failed drains can elapse "
            "before JPV_POS_PROJECTION_MAX_AGE_SECONDS degrades the scope. At the 3600 s "
            "default ceiling, 1800 s tolerates one failure, 900 s three and 600 s five, so "
            "the rule is ceiling / interval >= 4 and the default sits comfortably inside it. "
            "600 s also matches the cron cadence C22 documented and the 5-10 min the design "
            "declares, which costs nothing to agree with. Raising this above a quarter of the "
            "ceiling means a single missed drain can degrade the scope. Not required to boot "
            "/health."
        ),
    )

    jpv_knowledge_distance_threshold: float = Field(
        default=KNOWLEDGE_DEFAULTS["jpv_knowledge_distance_threshold"],
        gt=0,
        le=2,
        description=(
            "C23 cosine-distance cutoff of the knowledge corpus "
            "(JPV_KNOWLEDGE_DISTANCE_THRESHOLD). Optional at boot; a blank export means unset "
            "and falls back to the default. Deliberately SEPARATE from "
            "JPV_RETRIEVAL_DISTANCE_THRESHOLD, which was calibrated over much shorter "
            "product documents: knowledge chunks are longer prose and their distance "
            "distribution is another one. Below it the "
            "search returns NOTHING — for a question the corpus does not cover the correct "
            "answer is no citation, and C30 depends on that to have nothing with which to "
            "invent an attribution. Calibrated and not chosen, by a rule that outlives any one "
            "measurement: zero out-of-domain citations is a CONSTRAINT and not a term to "
            "trade against recall; inside that band Recall@3 is maximised; and among the "
            "values that tie the STRICTEST wins, which is the word the rule itself uses. "
            "Re-run the sweep with `python -m jbg_ai.knowledge calibrate`; the figures of "
            "the last one are in the C23 implementation report. That sweep uses the OFFLINE "
            "stand-in embedder the spec requires, so what it calibrates is the RULE. "
            "This DEFAULT is the value the same rule yields against the PRODUCTION embedder "
            "on the live index, which is a different number and not a rounding of it: the "
            "stand-in scores lexical overlap and its distances live on another scale, so its "
            "own optimum lets through questions the corpus does not cover. Re-derive it "
            "whenever the corpus, the chunking rules or the embedding model change, and do "
            "it against a populated index. Supplies only the DEFAULT: the effective value "
            "travels as a parameter of the call. Not required to boot /health."
        ),
    )

    jpv_knowledge_hybrid_enabled: bool = Field(
        default=KNOWLEDGE_DEFAULTS["jpv_knowledge_hybrid_enabled"],
        description=(
            "C23 lexical branch of the knowledge search (JPV_KNOWLEDGE_HYBRID_ENABLED). "
            "Optional at boot; a blank export means unset and falls back to the default. "
            "Default on because it was measured and not assumed: over the fixture the fused "
            "configuration beats vector-only on BOTH Recall@3 and MRR at no cost in "
            "abstention, and `python -m jbg_ai.knowledge measure --compare` reprints that "
            "comparison on demand. "
            "The branch exists for a reason specific to this corpus — nine material sheets "
            "are structurally identical and the only thing telling them apart is the "
            "material's name, a short lexical token drowned in shared prose — and the flag "
            "is what let that prediction be refuted or confirmed with a number, in the same "
            "pattern as JPV_QUERY_EXPANSION_ENABLED. Turning it off degrades knowledge "
            "search to pure vector retrieval and is the rollback for the hybrid half of "
            "C23. Supplies only the DEFAULT: the effective value travels as a parameter of "
            "the call. Not required to boot /health."
        ),
    )

    jpv_family_veto_margin: float = Field(
        default=0.05,
        ge=0,
        le=1,
        description=(
            "C18a relative-veto margin for POST /v1/families/suggest "
            "(JPV_FAMILY_VETO_MARGIN). A member is flagged for review, never "
            "removed, when a product of ANOTHER proposed family is closer to it "
            "than its own worst sibling by more than this much. Never an absolute "
            "similarity cutoff: on this corpus the worst-sibling and "
            "nearest-stranger populations overlap, so no constant separates them. "
            "Calibrated on the size of the review queue it produces — tightening it "
            "floods the queue, loosening it empties it — with the swept figures in "
            "the C18a report. Lives here because C24 will revisit it "
            "with the golden set, and an inlined threshold cannot be swept. "
            "Not required to boot /health."
        ),
    )

    jpv_family_orphan_margin: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description=(
            "C18b orphan-nomination margin for POST /v1/families/audit "
            "(JPV_FAMILY_ORPHAN_MARGIN). A product belonging to no family is "
            "nominated as a candidate for family F when its similarity to F's "
            "members beats F's own worst-sibling similarity by more than this much. "
            "Deliberately NOT neighbourhood purity, which was measured and rejected: "
            "purity nominates mostly SYNTHETIC products, because the synthetic corpus "
            "was built with deliberate vN near-duplicate families it cannot tell from "
            "a missing member, whereas this margin nominates mostly real ones. Purity "
            "travels as a ranking signal only. The swept figures are in the C18b "
            "report. Starts at 0 on purpose: with verdicts persisted a "
            "dismissal is paid once, while a candidate the margin excluded is never "
            "seen at all. Not required to boot /health."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def derive_dev_endpoints(cls, data: Any) -> Any:
        """Default `enable_dev_endpoints` from `app_env`: off under a production profile."""
        if not isinstance(data, dict) or data.get("enable_dev_endpoints") is not None:
            return data
        app_env = str(data.get("app_env") or "").strip().lower()
        return {**data, "enable_dev_endpoints": app_env not in PRODUCTION_ENV_NAMES}

    @field_validator("app_env", "service_version", "jwt_secret", mode="before")
    @classmethod
    def reject_blank(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            raise ValueError("must not be empty")
        return value

    @field_validator(
        "database_url",
        "jpv_catalog_llm_api_key",
        "jpv_catalog_llm_model",
        "jpv_catalog_llm_base_url",
        "jpv_rag_llm_api_key",
        "jpv_rag_llm_model",
        "jpv_rag_llm_base_url",
        "jpv_embedding_api_key",
        "jpv_embedding_model",
        "jpv_embedding_base_url",
        "jpv_index_feed_base_url",
        "jpv_index_feed_api_key",
        mode="before",
    )
    @classmethod
    def blank_optional_str_is_absent(cls, value: object) -> object:
        """Treat empty optional strings as unset (DATABASE_URL, LLM_* keys).

        Compose and shell profiles export empty strings easily; failing later
        with an unparseable URL or a blank key would be a worse error than
        behaving as if the variable had not been provided at all.
        """
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jpv_rag_llm_concurrency", mode="before")
    @classmethod
    def blank_concurrency_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return 8
        return value

    @field_validator("jpv_embedding_batch_size", mode="before")
    @classmethod
    def blank_embedding_batch_size_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return 64
        return value

    @field_validator("jpv_index_sync_time_budget_seconds", mode="before")
    @classmethod
    def blank_index_sync_time_budget_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return 180
        return value

    @field_validator("jpv_assist_llm_api_key", mode="before")
    @classmethod
    def blank_assist_llm_key_is_unset(cls, value: object) -> object:
        """A blank export means "unset", so it falls back rather than configuring an empty key."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jpv_assist_llm_model", mode="before")
    @classmethod
    def blank_assist_llm_model_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return DEFAULT_ASSIST_MODEL
        return value

    @field_validator("jpv_assist_pitch_timeout_seconds", mode="before")
    @classmethod
    def blank_pitch_timeout_is_default(cls, value: object) -> object:
        """A blank export means "unset", the same rule every other optional value follows."""
        if isinstance(value, str) and not value.strip():
            return DEFAULT_ASSIST_PITCH_TIMEOUT_SECONDS
        return value

    @field_validator("jpv_router_llm_api_key", mode="before")
    @classmethod
    def blank_router_llm_key_is_unset(cls, value: object) -> object:
        """A blank export means "unset", so it falls back rather than configuring an empty key."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jpv_router_llm_model", mode="before")
    @classmethod
    def blank_router_llm_model_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return DEFAULT_ROUTER_MODEL
        return value

    @field_validator("jpv_router_timeout_seconds", mode="before")
    @classmethod
    def blank_router_timeout_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return DEFAULT_ROUTER_TIMEOUT_SECONDS
        return value

    @field_validator("jpv_agent_llm_api_key", mode="before")
    @classmethod
    def blank_agent_llm_key_is_unset(cls, value: object) -> object:
        """A blank export means "unset", so it falls back rather than configuring an empty key."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jpv_agent_llm_model", mode="before")
    @classmethod
    def blank_agent_llm_model_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return DEFAULT_AGENT_MODEL
        return value

    @field_validator("jpv_agent_timeout_seconds", mode="before")
    @classmethod
    def blank_agent_timeout_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return DEFAULT_AGENT_TIMEOUT_SECONDS
        return value

    @field_validator("jpv_retrieval_distance_threshold", mode="before")
    @classmethod
    def blank_retrieval_threshold_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return 0.65
        return value

    @field_validator("jpv_query_expansion_enabled", mode="before")
    @classmethod
    def blank_query_expansion_flag_is_default(cls, value: object) -> object:
        """A blank export means "unset", not "false" — same rule as the other options."""
        if isinstance(value, str) and not value.strip():
            return True
        return value

    @field_validator("jpv_pos_prefilter_enabled", mode="before")
    @classmethod
    def blank_pos_prefilter_flag_is_default(cls, value: object) -> object:
        """A blank export means "unset". Read as false it would silently unscope every search."""
        if isinstance(value, str) and not value.strip():
            return True
        return value

    @field_validator("jpv_pos_projection_max_age_seconds", mode="before")
    @classmethod
    def blank_projection_max_age_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return 3600
        return value

    @field_validator("jpv_pos_sync_scheduler_enabled", mode="before")
    @classmethod
    def blank_pos_sync_flag_is_default(cls, value: object) -> object:
        """A blank export means "unset". Read as false it would silently stop draining."""
        if isinstance(value, str) and not value.strip():
            return True
        return value

    @field_validator("jpv_pos_sync_interval_seconds", mode="before")
    @classmethod
    def blank_pos_sync_interval_is_default(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return 600
        return value

    @field_validator(
        "jpv_knowledge_distance_threshold",
        "jpv_knowledge_hybrid_enabled",
        mode="before",
    )
    @classmethod
    def blank_knowledge_setting_is_default(
        cls, value: object, info: ValidationInfo
    ) -> object:
        """A blank export means "unset". Read as false it would silently drop the branch."""
        if isinstance(value, str) and not value.strip():
            return KNOWLEDGE_DEFAULTS[str(info.field_name)]
        return value

    @field_validator(
        "jpv_rrf_k",
        "jpv_branch_depth",
        "jpv_branch_weight_lexical",
        "jpv_branch_weight_vector",
        mode="before",
    )
    @classmethod
    def blank_fusion_setting_is_default(cls, value: object, info: ValidationInfo) -> object:
        """A blank export means "unset". A blank weight read as 0 would silence a branch."""
        if isinstance(value, str) and not value.strip():
            return FUSION_DEFAULTS[str(info.field_name)]
        return value

    @field_validator(
        "jpv_abstention_enabled",
        "jpv_abstention_band_alpha",
        "jpv_abstention_band_min_candidates",
        mode="before",
    )
    @classmethod
    def blank_abstention_setting_is_default(cls, value: object, info: ValidationInfo) -> object:
        """A blank export means "unset". Read as false it would silently disable the rule."""
        if isinstance(value, str) and not value.strip():
            return ABSTENTION_DEFAULTS[str(info.field_name)]
        return value

    @field_validator("jpv_business_weight_availability", mode="before")
    @classmethod
    def blank_business_setting_is_default(cls, value: object, info: ValidationInfo) -> object:
        """A blank export means "unset". Read as 0 it would silently drop a signal."""
        if isinstance(value, str) and not value.strip():
            return BUSINESS_DEFAULTS[str(info.field_name)]
        return value

    @field_validator("jpv_substitute_weight_size", mode="before")
    @classmethod
    def blank_substitute_setting_is_default(
        cls, value: object, info: ValidationInfo
    ) -> object:
        """A blank export means "unset". Read as 0 it would silently take the term out."""
        if isinstance(value, str) and not value.strip():
            return SUBSTITUTE_DEFAULTS[str(info.field_name)]
        return value


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings; raises ValidationError if required env is missing."""
    return Settings()  # type: ignore[call-arg]


def canonical_openapi_settings() -> Settings:
    """Canonical development profile the versioned `openapi.json` is generated with.

    Pinned here so the snapshot test and the manual regeneration documented in the
    README can never build the app with different profiles. Values are fixed on
    purpose: environment must not leak into the committed contract.
    """
    return Settings(
        app_env="local",
        service_version=CANONICAL_OPENAPI_SERVICE_VERSION,
        log_level="WARNING",
        jwt_secret="openapi-snapshot-secret-0123456789ab",
        jwt_ttl_seconds=300,
        stub_mode=True,
        enable_dev_endpoints=True,
        # Pinned like the rest: pydantic-settings would otherwise read these
        # from the environment, and the canonical profile exists precisely so
        # that no environment leaks into the committed contract.
        database_url=None,
        db_pool_size=5,
        jpv_catalog_llm_api_key=None,
        jpv_catalog_llm_model=None,
        jpv_catalog_llm_base_url=None,
        jpv_rag_llm_api_key=None,
        jpv_rag_llm_model=None,
        jpv_rag_llm_base_url=None,
        jpv_rag_llm_concurrency=8,
        jpv_embedding_api_key=None,
        jpv_embedding_model=None,
        jpv_embedding_base_url=None,
        jpv_embedding_batch_size=64,
        jpv_index_feed_base_url=None,
        jpv_index_feed_api_key=None,
        jpv_index_sync_time_budget_seconds=180,
        jpv_retrieval_distance_threshold=0.65,
        # Pinned like the rest: a value exported in the process environment must not
        # reach the committed snapshot, even through a field no route publishes today.
        jpv_assist_pitch_timeout_seconds=DEFAULT_ASSIST_PITCH_TIMEOUT_SECONDS,
        jpv_assist_llm_api_key=None,
        jpv_assist_llm_model=DEFAULT_ASSIST_MODEL,
        # C31, pinned for the same reason as every line above: an exported
        # JPV_ROUTER_LLM_MODEL must not reach the committed contract.
        jpv_router_llm_api_key=None,
        jpv_router_llm_model=DEFAULT_ROUTER_MODEL,
        jpv_router_timeout_seconds=DEFAULT_ROUTER_TIMEOUT_SECONDS,
        # C32b, pinned for the same reason as every line above: an exported
        # JPV_AGENT_LLM_MODEL must not reach the committed contract.
        jpv_agent_llm_api_key=None,
        jpv_agent_llm_model=DEFAULT_AGENT_MODEL,
        jpv_agent_timeout_seconds=DEFAULT_AGENT_TIMEOUT_SECONDS,
        jpv_query_expansion_enabled=True,
        jpv_pos_prefilter_enabled=True,
        jpv_pos_projection_max_age_seconds=3600,
        # Pinned like the rest, so a process environment value cannot leak into the
        # committed OpenAPI snapshot through a fusion weight.
        **FUSION_DEFAULTS,
        # Pinned like the rest even though neither value can reach the contract today:
        # knowledge search is a callable and has no route, by design. But "it cannot reach
        # the contract" is a claim about the routes that exist right now, not an invariant
        # of these settings, and it stops holding the day a route reads one of them. This
        # profile is worth having precisely because nobody should have to re-derive that
        # claim per setting every time the surface grows.
        **KNOWLEDGE_DEFAULTS,
    )
