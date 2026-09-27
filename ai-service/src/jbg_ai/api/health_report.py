"""Enriched health report for `GET /health`. Delivered by C17.

Four properties are deliberate, and each one prevents a failure with a name.

**The provider is never called.** The report says whether the embedding
credential is *configured*, not whether the provider is answering. A probe that
depends on a third party turns somebody else's outage into a failed deployment
and, with a container runtime watching it, into a restart loop. None of the
three consumers — the container health check, post-deployment verification, and
the administrator card on the dashboard — needs to know the provider is up. What
they need to know is whether somebody forgot to configure the credential, which
is the failure that actually happens.

**The configured embedding model is contrasted against the index.** Querying
with a model other than the one that produced the indexed vectors compares two
different vector spaces: the answer is noise, the status code is 200, and
nothing is logged. It is the most silent failure in the whole deployment, and
the index already records the model per row, so detecting it needs no new
schema.

**The result is cached for a short window.** The connection pool is capped at
five for the whole system and shared with the .NET API. A probe that opened a
connection per call could be the thing that exhausts the pool during an
incident: the probe causing the outage it reports.

**The shape stays an open mapping.** No Pydantic response model and no new
route, so the frozen OpenAPI snapshot — and the drift test that guards it —
are unaffected. Splitting this into liveness and readiness probes *would* move
the contract, and is recorded as deferred rather than done here.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import text

from jbg_ai.config.settings import Settings
from jbg_ai.db.engine import session_scope
from jbg_ai.indexing.constants import DEFAULT_EMBEDDING_MODEL
from jbg_ai.indexing.pos_projection import POS_FEED

logger = logging.getLogger(__name__)

#: How long a report is reused. Short enough that an operator refreshing the
#: dashboard sees the environment change within seconds; long enough that a
#: container health check every 30 s and a human clicking about cannot together
#: monopolise a pool of five connections.
HEALTH_CACHE_TTL_SECONDS = 10.0

STATUS_OK = "OK"
STATUS_DEGRADED = "degraded"

DATABASE_OK = "ok"
DATABASE_UNAVAILABLE = "unavailable"
#: A third state, and not a pedantic one. The service is specified to boot and
#: serve without a database — that is what `ai-service-dev-compose` guarantees
#: and what stub mode relies on — so an absent `DATABASE_URL` is a documented
#: configuration, not an outage. Collapsing it into `unavailable` would report
#: every local run and every test run as degraded. In the demo environment the
#: variable is always set, so this value never appears there, and
#: post-deployment verification requires `ok` rather than merely "not broken".
DATABASE_NOT_CONFIGURED = "not_configured"

INDEX_OK = "ok"
INDEX_MODEL_MISMATCH = "model_mismatch"
INDEX_UNAVAILABLE = "unavailable"

PROVIDER_CONFIGURED = "configured"
PROVIDER_MISSING = "missing"

PROJECTION_OK = "ok"
PROJECTION_STALE = "stale"
#: The drain has never run in this environment. Distinguished from `stale` on purpose: a
#: projection nobody has ever drained answers 503 to every scoped retrieval, while a stale
#: one serves a wider window and says so. They need different actions and this is the only
#: place that can tell them apart.
PROJECTION_NEVER_DRAINED = "never_drained"
PROJECTION_UNAVAILABLE = "unavailable"

#: Read from the checkpoint and NEVER from `max(ai.pos_projection.refreshed_at)`. The feed is
#: incremental by keyset, so an assignment that does not change is never re-emitted and that
#: column records when the assignment last moved — not when the projection was last looked at.
#: Reading it from the rows would report months of staleness on a projection synchronised
#: thirty seconds ago. This confusion has already cost two sessions: one diagnosing with the
#: wrong column and one *repairing* with it, which is why the warning is repeated here.
_PROJECTION_CHECKPOINT_SQL = text(
    "SELECT last_incremental_sync_at, last_full_sync_at "
    "FROM ai.sync_checkpoint WHERE feed = :feed"
)

#: How many points of sale the projection knows of at all. Reported unchanged, because it is
#: what the deployment check uses to tell "the projection is empty" from "a shop is missing an
#: assortment", and those stay different questions.
_PROJECTION_SHOPS_SQL = text(
    "SELECT count(DISTINCT pos_id) AS points_of_sale FROM ai.pos_projection"
)

#: **The shops go on the LEFT, and that is the decision.** C43.
#:
#: Until this change the count was `count(DISTINCT pos_id) FILTER (WHERE is_assigned_hint)`
#: subtracted from the total, taken over `ai.pos_projection` alone — which has no notion of
#: whether a shop is still trading, so a shop closed on purpose was indistinguishable from a
#: shop whose assortment never arrived. It failed a healthy deployment on 2026-09-27 and put a
#: red line on the administrator's dashboard, over one shop deliberately closed since
#: 2025-09-30 whose whole assortment was correctly retired.
#:
#: Reading from `ai.pos_shop` outwards also closes a case the old shape could not see at all: a
#: filter over the projection can only speak of shops that already appear in it, so an **active
#: shop absent from the projection entirely** — the worse of the two, refusing every scoped
#: retrieval — was never counted. With the shops on the left, absence and de-assignment land in
#: the same number.
#:
#: This reads only schema `ai`. The activity arrives over the feed, because the `jbg_ai` role
#: is refused `SELECT` on `public."PointOfSales"` and the schema boundary is deliberate.
_PROJECTION_ACTIVE_SHOPS_SQL = text(
    """
    SELECT count(*) FILTER (WHERE s.is_active) AS active_points_of_sale,
           count(*) FILTER (WHERE s.is_active AND NOT EXISTS (
               SELECT 1 FROM ai.pos_projection j
               WHERE j.pos_id = s.pos_id AND j.is_assigned_hint
           )) AS active_without_scope
    FROM ai.pos_shop s
    """
)

#: Per feed, not for the projection feed alone. C43.
#:
#: The scalar this used to be counted only `pos-availability` and told the truth — but nothing
#: counted the rest, and `ai.sync_failure` held 66 rows from the `catalog` feed that no reader
#: could reach. A table named `sync_failure` accumulating in silence is the shape of the three
#: findings C34, C41 and C39a each cost a session to discover.
_PROJECTION_FAILURES_BY_FEED_SQL = text(
    "SELECT feed, count(*) AS failures FROM ai.sync_failure GROUP BY feed"
)


def projection_age_seconds(
    synced_at: datetime | None, *, now: datetime | None = None
) -> float | None:
    """Seconds since the last drain, or `None` when it has never run."""
    if synced_at is None:
        return None
    reference = now or datetime.now(tz=UTC)
    if synced_at.tzinfo is None:
        synced_at = synced_at.replace(tzinfo=UTC)
    return max((reference - synced_at).total_seconds(), 0.0)


def build_projection_section(
    snapshot: IndexSnapshot, settings: Settings, *, now: datetime | None = None
) -> dict[str, Any]:
    """The projection block of the report.

    **The age and the verdict both travel, and that is not redundancy.** The age informs a
    reader; `status` states what the retrieval guard decided against the ceiling *this*
    deployment is configured with. Deriving the verdict on the consumer's side would put the
    threshold in two places, which is exactly the duplication the change set out to avoid — so
    `ceiling_seconds` travels too, and a screen can explain the verdict without knowing how the
    service is configured.

    **The age is the drain's, not a shop's.** The checkpoint holds one row per feed, so every
    scope reports the same number; anything named as though it were per-shop would be false.
    """
    ceiling = settings.jpv_pos_projection_max_age_seconds
    age = projection_age_seconds(snapshot.projection_synced_at, now=now)

    if age is None:
        status = PROJECTION_NEVER_DRAINED
    elif age > ceiling:
        status = PROJECTION_STALE
    else:
        status = PROJECTION_OK

    return {
        "status": status,
        "synced_at": (
            snapshot.projection_synced_at.isoformat()
            if snapshot.projection_synced_at
            else None
        ),
        "full_synced_at": (
            snapshot.projection_full_synced_at.isoformat()
            if snapshot.projection_full_synced_at
            else None
        ),
        "age_seconds": age,
        "ceiling_seconds": ceiling,
        "stale": status != PROJECTION_OK,
        "failed_pages": snapshot.projection_failed_pages,
        # Every feed's failures, beside the scalar rather than instead of it. C43 added this
        # after 66 rows from the `catalog` feed turned out to be unreachable to any reader.
        "failed_pages_by_feed": dict(snapshot.projection_failures_by_feed),
        "points_of_sale": snapshot.projection_points_of_sale,
        # **How many shops the service knows to be trading.** Zero means the shop reading has
        # not arrived, and it is what lets a consumer tell that apart from "nothing is wrong":
        # the count below is `null` in exactly that state, and `null` is not zero.
        "active_points_of_sale": snapshot.projection_active_points_of_sale,
        # The count that C34 needed and nobody reported: a point of sale with no assigned row
        # answers 503 to every scoped retrieval while the deployment looks healthy from
        # outside, because the .NET side degrades correctly to its lexical path with a 200.
        #
        # **Counted over ACTIVE shops since C43.** Counted over whatever the projection held,
        # it could not tell a shop closed on purpose from a broken one, and failed a healthy
        # deployment on 2026-09-27. The name is kept: the consumers read this key, the .NET
        # DTO already declares it nullable and the dashboard already treats `null` as nothing
        # to draw, so the correction reaches all three screens without moving any of them.
        "shops_without_scope": snapshot.projection_active_without_scope,
    }


@dataclass(frozen=True)
class IndexSnapshot:
    """What one look at the database found.

    `models` holds the DISTINCT `embedding_model` values present on the index
    rows — a tuple rather than a single value because an index half-reindexed
    with a second model is a real state, and reporting only one of the two
    models would hide it.
    """

    database_reachable: bool
    documents: int = 0
    models: tuple[str, ...] = ()
    #: False only when no `DATABASE_URL` is configured at all. See
    #: DATABASE_NOT_CONFIGURED.
    database_configured: bool = True

    # --- point-of-sale projection (C41) -------------------------------------------------
    #
    # Read in the SAME session as the two above, so the whole report still costs one
    # connection out of a pool capped at five.

    #: `ai.sync_checkpoint.last_incremental_sync_at` for the POS feed, or `None` when the
    #: drain has never run. **Never `max(ai.pos_projection.refreshed_at)`**: the feed is
    #: incremental by keyset, so that column records when an assignment last changed and
    #: would report months on a projection synchronised seconds ago.
    projection_synced_at: datetime | None = None
    projection_full_synced_at: datetime | None = None
    #: Points of sale that appear in the projection at all.
    projection_points_of_sale: int = 0

    # --- shop activity (C43) ------------------------------------------------------------
    #
    # Read from `ai.pos_shop`, in the same session as everything above.

    #: Points of sale recorded as ACTIVE in `ai.pos_shop`. Zero means the shop reading has
    #: not arrived yet — not that the business has no shops — which is why the count below
    #: is reported as unknown rather than zero in that state.
    projection_active_points_of_sale: int = 0
    #: Of the ACTIVE ones, how many hold no assigned row in the projection. `None` when
    #: `ai.pos_shop` is empty, because zero would assert that every active shop is served,
    #: and that is a claim the service cannot make before it knows of any shop at all.
    projection_active_without_scope: int | None = None
    #: Rows in `ai.sync_failure` per feed. Cumulative and persisted, not "the last run's":
    #: nothing else reads that table, so a page that failed months ago is otherwise
    #: invisible for ever.
    projection_failures_by_feed: dict[str, int] = field(default_factory=dict)

    @property
    def projection_failed_pages(self) -> int:
        """Failures recorded against the POS feed, which is what the deployment check reads."""
        return self.projection_failures_by_feed.get(POS_FEED, 0)


class HealthProbe(Protocol):
    """One database round trip, injectable so tests never need a database."""

    async def snapshot(self) -> IndexSnapshot: ...


class SqlAlchemyHealthProbe:
    """Both questions in ONE session, so the report costs one connection."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def snapshot(self) -> IndexSnapshot:
        # Asked before any connection is attempted: an absent DATABASE_URL is a
        # configuration, not a failure, and `session_scope` would raise for it.
        if not self._settings.database_url:
            return IndexSnapshot(database_reachable=False, database_configured=False)

        try:
            async with session_scope(self._settings) as session:
                documents = (
                    await session.execute(text("SELECT count(*) FROM ai.product_document"))
                ).scalar()
                models = (
                    await session.execute(
                        text(
                            "SELECT DISTINCT embedding_model FROM ai.product_document "
                            "WHERE embedding_model IS NOT NULL"
                        )
                    )
                ).scalars().all()
                # Same session as the two above: the whole report stays one connection.
                checkpoint = (
                    await session.execute(_PROJECTION_CHECKPOINT_SQL, {"feed": POS_FEED})
                ).mappings().first()
                shops = (
                    await session.execute(_PROJECTION_SHOPS_SQL)
                ).mappings().first()
                active_shops = (
                    await session.execute(_PROJECTION_ACTIVE_SHOPS_SQL)
                ).mappings().first()
                failures_by_feed = {
                    str(row["feed"]): int(row["failures"] or 0)
                    for row in (
                        await session.execute(_PROJECTION_FAILURES_BY_FEED_SQL)
                    ).mappings()
                }
        except Exception:  # noqa: BLE001 - any failure to reach the database is one answer
            # Deliberately broad, and deliberately not re-raised. This endpoint
            # exists to REPORT that the database is unreachable; raising would
            # turn the report into the outage.
            logger.warning("health_probe_database_unreachable", exc_info=True)
            return IndexSnapshot(database_reachable=False)

        active = int((active_shops or {}).get("active_points_of_sale") or 0)

        return IndexSnapshot(
            database_reachable=True,
            documents=int(documents or 0),
            models=tuple(sorted(str(model) for model in models)),
            projection_synced_at=(
                checkpoint["last_incremental_sync_at"] if checkpoint else None
            ),
            projection_full_synced_at=(
                checkpoint["last_full_sync_at"] if checkpoint else None
            ),
            projection_points_of_sale=int((shops or {}).get("points_of_sale") or 0),
            projection_active_points_of_sale=active,
            # `None` and not 0 when no shop is known: see the field's own note. Deriving it
            # here rather than in the section builder keeps the builder a pure function of
            # the snapshot, which is what lets every case be tested without a database.
            projection_active_without_scope=(
                int((active_shops or {}).get("active_without_scope") or 0)
                if active
                else None
            ),
            projection_failures_by_feed=failures_by_feed,
        )


def configured_embedding_model(settings: Settings) -> str:
    """The model retrieval would embed a query with, resolved the same way it is."""
    return settings.jpv_embedding_model or DEFAULT_EMBEDDING_MODEL


async def build_health_report(settings: Settings, probe: HealthProbe) -> dict[str, Any]:
    """Compose the report. Never raises, never calls the embedding provider."""
    configured_model = configured_embedding_model(settings)
    provider = PROVIDER_CONFIGURED if settings.jpv_embedding_api_key else PROVIDER_MISSING

    snapshot = await probe.snapshot()

    if not snapshot.database_reachable:
        index: dict[str, Any] = {
            "documents": 0,
            "model": None,
            "configured_model": configured_model,
            "status": INDEX_UNAVAILABLE,
        }
        return {
            # A database that was never configured is not a degradation: the
            # service is required to boot and answer without one.
            "status": STATUS_OK if not snapshot.database_configured else STATUS_DEGRADED,
            "version": settings.service_version,
            "database": (
                DATABASE_NOT_CONFIGURED
                if not snapshot.database_configured
                else DATABASE_UNAVAILABLE
            ),
            "index": index,
            "provider": provider,
            # Present even here, and saying it does not know. An absent section would be
            # indistinguishable from an old service that predates it, which is precisely the
            # ambiguity the consumer's tolerant reading would then have to guess at.
            "projection": {
                "status": PROJECTION_UNAVAILABLE,
                "synced_at": None,
                "full_synced_at": None,
                "age_seconds": None,
                "ceiling_seconds": settings.jpv_pos_projection_max_age_seconds,
                "stale": None,
                "failed_pages": None,
                "failed_pages_by_feed": None,
                "points_of_sale": None,
                "active_points_of_sale": None,
                "shops_without_scope": None,
            },
        }

    # An empty index is NOT a mismatch. There is no indexed model to disagree
    # with, and reporting one would make a brand-new environment — which is
    # exactly the state the deployment starts in — look broken rather than
    # empty. Emptiness is caught by post-deployment verification, which requires
    # a document count above zero, and that is the right place for it.
    if not snapshot.models:
        indexed_model: str | None = None
        index_status = INDEX_OK
    elif set(snapshot.models) == {configured_model}:
        indexed_model = snapshot.models[0]
        index_status = INDEX_OK
    else:
        # Both models are named in the body on purpose: "mismatch" alone leaves
        # the reader to guess which of the two is wrong, and the answer decides
        # whether the fix is a configuration change or a reindex.
        indexed_model = ", ".join(snapshot.models)
        index_status = INDEX_MODEL_MISMATCH

    projection = build_projection_section(snapshot, settings)

    return {
        # **The projection does NOT move the top-level status, and that is deliberate.** A
        # stale projection is a degradation of the candidate window, not of the service: the
        # .NET side still puts the truth, no valid product is hidden, and `GET /health` is what
        # the container health check probes. Letting staleness mark the service degraded would
        # make an environment that is serving correct results look broken, and — worse — would
        # couple the liveness of the container to a cron. The projection reports its own state
        # in its own section, which is what the administrator card reads.
        "status": STATUS_OK if index_status == INDEX_OK else STATUS_DEGRADED,
        "version": settings.service_version,
        "database": DATABASE_OK,
        "index": {
            "documents": snapshot.documents,
            "model": indexed_model,
            "configured_model": configured_model,
            "status": index_status,
        },
        "provider": provider,
        "projection": projection,
    }


async def cached_health_report(
    state: Any,
    settings: Settings,
    probe: HealthProbe,
    *,
    ttl_seconds: float = HEALTH_CACHE_TTL_SECONDS,
) -> dict[str, Any]:
    """Reuse the last report for `ttl_seconds`.

    The cache lives on the application state rather than in a module global, so
    two applications in one process — which is every test file here — cannot
    serve each other's answers.
    """
    cached = getattr(state, "health_cache", None)
    now = time.monotonic()

    if cached is not None and now < cached[0]:
        return cached[1]  # type: ignore[no-any-return]

    report = await build_health_report(settings, probe)
    state.health_cache = (now + ttl_seconds, report)
    return report
