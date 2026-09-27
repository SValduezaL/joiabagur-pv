"""Construction and execution of the shop activity drain. Delivered by C43.

**Why a module of its own rather than a branch inside `pos_drain.py`.** The same reason that
one exists apart from `cli.py`: the scheduler reaches this from a process whose job is to
answer HTTP, and `cli.py` imports the embedding client and through it the provider SDK.
`test_main_does_not_import_indexing` and `test_unit_suite_makes_no_provider_calls` guard that
boundary and have caught a change crossing it before.

**This drain embeds nothing and needs no provider credential**, exactly like the availability
drain. It also takes **no advisory lock**, and that is a decision rather than an omission: the
lock next door exists because two interleaved drains would corrupt the single-row keyset of
`ai.sync_checkpoint`, skipping rows in silence. This drain keeps no cursor at all. Two
concurrent runs each write the same complete reading, so the worst case is one redundant
replacement — whereas taking a lock would make a scheduled tick decline and leave the table
older than it needed to be, for no protection anybody needs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

from jbg_ai.config.settings import Settings, get_settings
from jbg_ai.indexing.feed import (
    FEED_TIMEOUT_SECONDS,
    HttpxIndexFeedClient,
    IndexFeedClient,
)
from jbg_ai.indexing.pos_shop import PosShopRepo, SqlAlchemyPosShopRepo, now_utc
from jbg_ai.indexing.sync_errors import IndexFeedConfigError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PosShopSyncResult:
    """What one drain wrote. No cursor and no `declined`: there is neither to report."""

    written: int = 0
    removed: int = 0
    active: int = 0
    computed_as_of: datetime | None = None


async def sync_pos_shops(
    *,
    feed: IndexFeedClient,
    repo: PosShopRepo,
    refreshed_at: datetime | None = None,
) -> PosShopSyncResult:
    """Read the whole set and replace the table with it."""
    reading = await feed.fetch_pos_shops()
    written, removed = await repo.replace_all(
        reading.items, refreshed_at=refreshed_at or now_utc()
    )
    active = sum(1 for item in reading.items if item.is_active)

    logger.info(
        "stage=pos_shop_sync done written=%s removed=%s active=%s",
        written,
        removed,
        active,
    )
    return PosShopSyncResult(
        written=written,
        removed=removed,
        active=active,
        computed_as_of=reading.computed_as_of,
    )


async def run_pos_shop_drain(
    *,
    settings: Settings | None = None,
    feed: IndexFeedClient | None = None,
    repo: PosShopRepo | None = None,
) -> PosShopSyncResult:
    """Drain the shop feed. The one entry point every caller goes through.

    When `feed` and `repo` are both injected the caller is a test supplying its own doubles.
    Otherwise the real client and repository are built here, and the feed configuration is
    required rather than defaulted away.

    **Settings are resolved only when something needs them**, after the injected path has been
    taken. `get_settings()` validates the whole environment and raises without one, so
    resolving first would make a drain that touches neither the network nor the database
    depend on configuration it never reads.
    """
    if feed is not None and repo is not None:
        return await sync_pos_shops(feed=feed, repo=repo)

    resolved = settings or get_settings()

    if not resolved.jpv_index_feed_base_url:
        raise IndexFeedConfigError("JPV_INDEX_FEED_BASE_URL")
    if not resolved.jpv_index_feed_api_key:
        raise IndexFeedConfigError("JPV_INDEX_FEED_API_KEY")

    async with httpx.AsyncClient(
        base_url=resolved.jpv_index_feed_base_url.rstrip("/"),
        timeout=FEED_TIMEOUT_SECONDS,
    ) as client:
        live_feed = feed or HttpxIndexFeedClient(client, resolved.jpv_index_feed_api_key)
        live_repo = repo or SqlAlchemyPosShopRepo(resolved)
        return await sync_pos_shops(feed=live_feed, repo=live_repo)
