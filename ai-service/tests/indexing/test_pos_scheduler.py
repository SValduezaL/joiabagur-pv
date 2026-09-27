"""Scheduled POS drain: the lock, the start-up drain, the interval. C41.

Offline throughout. The lock is a double, the feed is a double, and the projection is the
in-memory one — the same discipline C22's drain tests follow, and for the same reason: the
property under test is mutual exclusion and scheduling, not PostgreSQL.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest

from jbg_ai.config.settings import Settings
from jbg_ai.indexing import pos_drain, scheduler
from jbg_ai.indexing.drain_lock import (
    POS_DRAIN_LOCK_KEY,
    AlwaysAvailableLock,
    PostgresAdvisoryLock,
)
from jbg_ai.indexing.feed import PosFeedPage, parse_pos_item
from jbg_ai.indexing.pos_orchestrator import PosSyncRequest, describe, sync_pos_availability
from jbg_ai.indexing.pos_projection import POS_FEED
from jbg_ai.indexing.sync_errors import IndexFeedConfigError
from support.fake_pos_projection import FakePosProjectionRepo

POS_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
PRODUCT_A = uuid.UUID("22222222-2222-2222-2222-222222222222")
AS_OF = datetime(2026, 8, 23, 23, 59, 59, tzinfo=UTC)
WATERMARK = datetime(2026, 8, 22, 10, 0, 0, tzinfo=UTC)


def run(coro):
    return asyncio.run(coro)


def upsert(product_id: uuid.UUID, watermark: datetime):
    return parse_pos_item(
        {
            "kind": "upsert",
            "pointOfSaleId": str(POS_A),
            "productId": str(product_id),
            "qtyBucket": "1-2",
            "isAssignedHint": True,
            "sales30d": 1,
            "sales90d": 2,
            "lastSaleAt": None,
            "watermark": watermark.isoformat(),
        }
    )


def page(items):
    return PosFeedPage(
        items=list(items),
        next_cursor=None,
        has_more=False,
        page_size=200,
        aggregate_hash="a" * 64,
        computed_as_of=AS_OF,
    )


class FakePosFeed:
    def __init__(self, pages: list[PosFeedPage]) -> None:
        self.pages = pages
        self.requests: list[tuple[datetime | None, uuid.UUID | None]] = []

    async def fetch_catalog_page(self, since, since_id):  # pragma: no cover
        raise AssertionError("the POS drain must not touch the catalog feed")

    async def fetch_pos_page(self, since, since_id) -> PosFeedPage:
        self.requests.append((since, since_id))
        return self.pages[min(len(self.requests) - 1, len(self.pages) - 1)]


class HeldLock:
    """A lock somebody else is holding. Declines every time, and records the attempts."""

    def __init__(self) -> None:
        self.attempts = 0

    @asynccontextmanager
    async def acquired(self):
        self.attempts += 1
        yield False


class CountingLock:
    """Grants, and records that it was both taken and released."""

    def __init__(self) -> None:
        self.taken = 0
        self.released = 0

    @asynccontextmanager
    async def acquired(self):
        self.taken += 1
        try:
            yield True
        finally:
            self.released += 1


def settings(**overrides) -> Settings:
    base = dict(
        app_env="local",
        service_version="test",
        log_level="WARNING",
        jwt_secret="scheduler-test-secret-0123456789ab",
        stub_mode=False,
        jpv_index_feed_base_url="http://feed.invalid",
        jpv_index_feed_api_key="k" * 32,
    )
    base.update(overrides)
    return Settings(**base)


# --------------------------------------------------------------------------- the lock


def test_a_drain_that_cannot_take_the_lock_declines_and_writes_nothing() -> None:
    repo = FakePosProjectionRepo()
    feed = FakePosFeed([page([upsert(PRODUCT_A, WATERMARK)])])
    lock = HeldLock()

    result = run(
        sync_pos_availability(
            PosSyncRequest(), feed=feed, repo=repo, lock=lock, trace_id="t-declined"
        )
    )

    assert result.declined is True
    assert result.pages == 0
    assert result.upserted == 0
    # The point of the lock: not one request was issued and not one row was written, so the
    # keyset of the drain that DOES hold it cannot be interleaved by this one.
    assert feed.requests == []
    assert repo.checkpoints == {}


def test_a_declined_drain_is_not_reported_as_an_empty_success() -> None:
    repo = FakePosProjectionRepo()
    feed = FakePosFeed([page([])])

    declined = run(
        sync_pos_availability(PosSyncRequest(), feed=feed, repo=repo, lock=HeldLock())
    )
    empty = run(
        sync_pos_availability(
            PosSyncRequest(), feed=FakePosFeed([page([])]), repo=FakePosProjectionRepo()
        )
    )

    # Both drains wrote no rows, and they mean opposite things. The counters alone cannot
    # tell them apart, which is exactly why `describe` says one of them in words.
    assert declined.upserted == empty.upserted == 0
    assert "declined" in describe(declined)
    assert "declined" not in describe(empty)


def test_the_lock_is_released_so_the_next_drain_proceeds() -> None:
    lock = CountingLock()
    repo = FakePosProjectionRepo()

    for _ in range(2):
        run(
            sync_pos_availability(
                PosSyncRequest(),
                feed=FakePosFeed([page([upsert(PRODUCT_A, WATERMARK)])]),
                repo=repo,
                lock=lock,
            )
        )

    assert lock.taken == 2
    assert lock.released == 2


def test_the_lock_is_released_even_when_the_drain_raises() -> None:
    lock = CountingLock()

    class ExplodingFeed(FakePosFeed):
        async def fetch_pos_page(self, since, since_id):
            raise RuntimeError("feed exploded mid-drain")

    with pytest.raises(RuntimeError):
        run(
            sync_pos_availability(
                PosSyncRequest(),
                feed=ExplodingFeed([]),
                repo=FakePosProjectionRepo(),
                lock=lock,
            )
        )

    # A lock left held by a crashed drain would block every later one until the connection
    # was recycled, which is a worse failure than the one that caused it.
    assert lock.taken == 1
    assert lock.released == 1


def test_a_real_drain_always_constructs_a_lock() -> None:
    """The structural guarantee, asserted where it can actually be forgotten.

    The page-loop unit tests pass no lock because they are testing cursor arithmetic. That is
    only safe if every PRODUCTION path builds one, and this is the assertion that says so.
    """
    seen: dict[str, object] = {}

    async def _capture(request, *, feed, repo, time_budget_seconds, lock=None, **kwargs):
        seen["lock"] = lock
        from jbg_ai.indexing.pos_orchestrator import PosSyncResult

        return PosSyncResult()

    original = pos_drain.sync_pos_availability
    pos_drain.sync_pos_availability = _capture  # type: ignore[assignment]
    try:
        run(pos_drain.run_pos_drain(settings=settings()))
    finally:
        pos_drain.sync_pos_availability = original  # type: ignore[assignment]

    assert isinstance(seen["lock"], PostgresAdvisoryLock)


def test_the_lock_key_is_a_documented_constant() -> None:
    """`hashtext` is not contracted to be stable across database versions.

    A silently changed key would not raise: it would take a DIFFERENT lock, so two drains
    would each believe they held it — the exact failure the lock exists to prevent. Asserted
    against the statement that is actually executed rather than against the source text, so
    the module stays free to explain the reasoning in its own docstring.
    """
    from jbg_ai.indexing import drain_lock

    assert POS_DRAIN_LOCK_KEY == (41, 1)

    for statement in (drain_lock._TRY_ACQUIRE_SQL, drain_lock._RELEASE_SQL):
        sql = str(statement)
        assert ":classid" in sql and ":objid" in sql
        assert "hashtext" not in sql


# --------------------------------------------------------------------------- the scheduler


def test_the_scheduler_does_not_run_under_stub_mode() -> None:
    """A stubbed service answers from fixtures and has no real feed to drain."""
    assert scheduler.scheduler_should_run(settings(stub_mode=True)) is False


def test_the_scheduler_does_not_run_when_switched_off() -> None:
    assert (
        scheduler.scheduler_should_run(settings(jpv_pos_sync_scheduler_enabled=False))
        is False
    )


def test_the_scheduler_does_not_run_without_a_configured_feed() -> None:
    assert (
        scheduler.scheduler_should_run(settings(jpv_index_feed_base_url=None)) is False
    )
    assert (
        scheduler.scheduler_should_run(settings(jpv_index_feed_api_key=None)) is False
    )


def test_the_scheduler_runs_by_default() -> None:
    """Off by default would reproduce the defect this change closes."""
    assert scheduler.scheduler_should_run(settings()) is True


def test_a_drain_that_raises_never_escapes_the_scheduler(monkeypatch) -> None:
    """It runs in a task nobody awaits, so an escaping exception would stop the loop silently."""

    async def _boom(**kwargs):
        raise RuntimeError("database went away")

    monkeypatch.setattr(scheduler, "run_pos_drain", _boom)
    assert run(scheduler.drain_once(settings(), trace_id="t-boom")) is None


def test_an_unconfigured_feed_is_reported_and_not_raised(monkeypatch) -> None:
    async def _unconfigured(**kwargs):
        raise IndexFeedConfigError("JPV_INDEX_FEED_BASE_URL")

    monkeypatch.setattr(scheduler, "run_pos_drain", _unconfigured)
    assert run(scheduler.drain_once(settings(), trace_id="t-unconfigured")) is None


def test_the_boot_drain_retries_until_the_feed_answers(monkeypatch) -> None:
    """The local-development case: jbg-ai is up and the .NET API is not, yet."""
    attempts = {"n": 0}

    async def _flaky(**kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("connection refused")
        from jbg_ai.indexing.pos_orchestrator import PosSyncResult

        return PosSyncResult(pages=1, upserted=7)

    slept: list[float] = []

    async def _sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(scheduler, "run_pos_drain", _flaky)
    monkeypatch.setattr(scheduler.asyncio, "sleep", _sleep)

    run(scheduler._boot_drain(settings()))

    assert attempts["n"] == 3
    # Bounded and increasing, and it gave up to the interval rather than retrying for ever.
    assert slept == [5.0, 15.0]


def test_the_boot_drain_gives_up_to_the_interval(monkeypatch) -> None:
    attempts = {"n": 0}

    async def _always_down(**kwargs):
        attempts["n"] += 1
        raise RuntimeError("connection refused")

    async def _sleep(delay: float) -> None:
        return None

    monkeypatch.setattr(scheduler, "run_pos_drain", _always_down)
    monkeypatch.setattr(scheduler.asyncio, "sleep", _sleep)

    run(scheduler._boot_drain(settings()))

    assert attempts["n"] == len(scheduler.BOOT_RETRY_DELAYS_SECONDS) + 1


def test_the_boot_drain_does_not_force_a_full_run(monkeypatch) -> None:
    """A fresh environment drains in full on its own, from the absent checkpoint.

    Deciding it here would be a second read of the same fact, and a second chance to
    disagree with the orchestrator about what "no cursor" means.
    """
    seen: dict[str, object] = {}

    async def _capture(**kwargs):
        seen.update(kwargs)
        from jbg_ai.indexing.pos_orchestrator import PosSyncResult

        return PosSyncResult()

    monkeypatch.setattr(scheduler, "run_pos_drain", _capture)
    run(scheduler.drain_once(settings(), trace_id="t-boot"))

    assert "full" not in seen


def test_the_interval_default_leaves_room_for_several_failures() -> None:
    """The interval is derived from the ceiling, not chosen. `ceiling / interval >= 4`."""
    resolved = settings()
    assert resolved.jpv_pos_sync_interval_seconds == 600
    assert (
        resolved.jpv_pos_projection_max_age_seconds
        / resolved.jpv_pos_sync_interval_seconds
        >= 4
    )


def test_a_blank_export_of_either_setting_is_the_default() -> None:
    resolved = settings(
        jpv_pos_sync_scheduler_enabled="", jpv_pos_sync_interval_seconds=""
    )
    assert resolved.jpv_pos_sync_scheduler_enabled is True
    assert resolved.jpv_pos_sync_interval_seconds == 600
