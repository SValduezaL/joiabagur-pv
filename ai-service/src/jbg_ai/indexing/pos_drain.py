"""Construction of a real POS drain: feed client, repository and lock. Delivered by C41.

**Why this is a module of its own rather than a function in `cli.py`.** The scheduler needs the
same construction the command line performs, and importing it from `cli.py` would drag
`LiteLlmEmbeddingClient` — and through it the provider SDK — into the import graph of the
FastAPI application factory. `test_main_does_not_import_indexing` and
`test_unit_suite_makes_no_provider_calls` exist to prevent exactly that, and they caught it.

Nothing here touches embeddings, and nothing here should ever start to: **this drain embeds
nothing**. It needs no embedding key, which is the property that lets it be reached from a
process whose job is to answer HTTP.
"""

from __future__ import annotations

import httpx

from jbg_ai.config.settings import Settings, get_settings
from jbg_ai.indexing.drain_lock import DrainLock, PostgresAdvisoryLock
from jbg_ai.indexing.feed import (
    FEED_TIMEOUT_SECONDS,
    HttpxIndexFeedClient,
    IndexFeedClient,
)
from jbg_ai.indexing.pos_orchestrator import (
    PosSyncRequest,
    PosSyncResult,
    sync_pos_availability,
)
from jbg_ai.indexing.pos_projection import PosProjectionRepo, SqlAlchemyPosProjectionRepo
from jbg_ai.indexing.sync_errors import IndexFeedConfigError


async def run_pos_drain(
    *,
    full: bool = False,
    settings: Settings | None = None,
    feed: IndexFeedClient | None = None,
    repo: PosProjectionRepo | None = None,
    lock: DrainLock | None = None,
) -> PosSyncResult:
    """Drain the POS availability feed. The one entry point every caller goes through.

    **The command line and the scheduler both arrive here**, and that is what makes the advisory
    lock cover all three ways a drain can start — a scheduled tick, a second scheduled tick, and
    somebody running the command by hand. Giving the scheduler a construction path of its own
    would have left the command line unprotected, and the command line run by hand is how every
    recorded incident of a stale projection was repaired: it is the overlap most likely to
    actually happen, not the least.

    When `feed` and `repo` are both injected the caller is a test supplying its own doubles, and
    whether it passes a lock is its business. Otherwise a real `PostgresAdvisoryLock` is built
    here and is never defaulted away.
    """
    resolved = settings or get_settings()

    if feed is not None and repo is not None:
        return await sync_pos_availability(
            PosSyncRequest(full=full),
            feed=feed,
            repo=repo,
            time_budget_seconds=resolved.jpv_index_sync_time_budget_seconds,
            lock=lock,
        )

    if not resolved.jpv_index_feed_base_url:
        raise IndexFeedConfigError("JPV_INDEX_FEED_BASE_URL")
    if not resolved.jpv_index_feed_api_key:
        raise IndexFeedConfigError("JPV_INDEX_FEED_API_KEY")

    async with httpx.AsyncClient(
        base_url=resolved.jpv_index_feed_base_url.rstrip("/"),
        timeout=FEED_TIMEOUT_SECONDS,
    ) as client:
        live_feed = feed or HttpxIndexFeedClient(client, resolved.jpv_index_feed_api_key)
        live_repo = repo or SqlAlchemyPosProjectionRepo(resolved)
        live_lock = lock or PostgresAdvisoryLock(resolved)
        return await sync_pos_availability(
            PosSyncRequest(full=full),
            feed=live_feed,
            repo=live_repo,
            time_budget_seconds=resolved.jpv_index_sync_time_budget_seconds,
            lock=live_lock,
        )
