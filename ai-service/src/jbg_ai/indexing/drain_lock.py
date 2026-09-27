"""Mutual exclusion for the POS availability drain. Delivered by C41.

**Why a lock exists at all, and why it is not optional.** `ai.sync_checkpoint` holds *one row
per feed* (`PRIMARY KEY (feed)`) carrying `watermark` and `since_id`. Two drains writing at the
same time interleave that keyset, and an interleaved keyset **does not fail: it skips rows in
silence**, which is strictly worse than the staleness this capability set out to fix — a stale
projection widens the candidate window and says so, while a skipped row is a product the
projection simply never learns about.

**Why an advisory lock and not something cheaper.** Three candidates were considered:

* An in-process mutex protects a second scheduler tick and nothing else. It cannot see
  `python -m jbg_ai.indexing sync-pos` run by hand, in another process — and running it by hand
  is how every recorded incident of a stale projection was repaired. Insufficient by the only
  criterion that matters.
* `SELECT … FOR UPDATE` on the checkpoint row is attractive because the lock object *is* the
  thing protected, but the drain is 34 transactions rather than one: holding a transaction open
  across all of them would retain a pooled connection for minutes, out of a pool capped at five.
* `pg_try_advisory_lock` is session-scoped, crosses processes and containers because it lives in
  the database, and is released when the connection goes away even if the process is killed.

**Why NON-blocking.** A tick that waits for a slower drain builds a queue that grows without
bound; under a feed that has become slow, every interval would add another waiter and the pool
would be exhausted by drains queueing to do work that is already being done. Declining is the
correct answer, and the declined attempt is recorded rather than retried on the spot: the next
interval is soon enough.

**Why a fixed constant and not `hashtext(feed)`.** `hashtext` is an internal function whose
output is not contracted to be stable across PostgreSQL versions. A silently changed key would
not raise: it would simply take a *different* lock, so two drains would each believe they held
it. That is the exact failure this module exists to prevent, arriving through the module itself.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Protocol

from sqlalchemy import text

from jbg_ai.config.settings import Settings
from jbg_ai.db.engine import get_engine

logger = logging.getLogger(__name__)

#: `(classid, objid)` of the advisory lock, as a documented constant.
#:
#: `41` is this project's namespace for drain locks — the change that introduced them — and the
#: second component names the feed, so a future catalog drain lock takes `(41, 2)` without any
#: risk of colliding with this one. The pair form is used rather than a single `bigint` because
#: `pg_locks` shows the two components separately, which makes a held lock legible in a
#: diagnostic query instead of being an opaque 64-bit number.
POS_DRAIN_LOCK_KEY: tuple[int, int] = (41, 1)

_TRY_ACQUIRE_SQL = text("SELECT pg_try_advisory_lock(:classid, :objid)")
_RELEASE_SQL = text("SELECT pg_advisory_unlock(:classid, :objid)")


class DrainLock(Protocol):
    """A lock a drain takes before writing anything.

    `acquired()` yields `True` when this caller holds it and `False` when somebody else does.
    It never raises on contention: declining is an outcome, not an error.
    """

    @asynccontextmanager
    def acquired(self) -> AsyncIterator[bool]:  # pragma: no cover - protocol
        ...


class PostgresAdvisoryLock:
    """The real lock: `pg_try_advisory_lock` on a connection held for the whole drain.

    **Cost, declared rather than hidden.** This holds one pooled connection from the moment the
    lock is taken until the drain ends — a pool capped at five, so a running drain leaves four,
    one of which the drain itself uses for its page writes. An incremental drain holds it for
    seconds; a full one, for minutes, and a full one happens once per fresh environment.

    The same connection must both take and release the lock, because an advisory lock belongs to
    the *session* that took it. Releasing from a different pooled connection would silently do
    nothing and return false, leaving the lock held until that first connection was recycled.
    """

    def __init__(
        self, settings: Settings, *, key: tuple[int, int] = POS_DRAIN_LOCK_KEY
    ) -> None:
        self._settings = settings
        self._key = key

    @asynccontextmanager
    async def acquired(self) -> AsyncIterator[bool]:
        classid, objid = self._key
        params = {"classid": classid, "objid": objid}
        engine = get_engine(self._settings)

        async with engine.connect() as connection:
            granted = bool(
                (await connection.execute(_TRY_ACQUIRE_SQL, params)).scalar()
            )
            try:
                yield granted
            finally:
                if granted:
                    # Released explicitly rather than left to the connection returning to the
                    # pool. A pooled connection is *reused*, not closed, so the session that
                    # holds the lock would survive this block and keep holding it.
                    await connection.execute(_RELEASE_SQL, params)


class AlwaysAvailableLock:
    """A lock that is always granted. **Not a production object.**

    It exists so that the unit tests of the page loop — which own no database and are testing
    cursor arithmetic, tombstones and failed pages rather than mutual exclusion — do not have to
    carry a parameter they have nothing to say about.

    Every production entry point constructs `PostgresAdvisoryLock` instead, and that is asserted
    by a test on the entry point rather than left to reviewers to notice.
    """

    @asynccontextmanager
    async def acquired(self) -> AsyncIterator[bool]:
        yield True


def log_declined(feed: str, trace_id: str) -> None:
    """One line, in the drain's own stage vocabulary, when the lock was held elsewhere."""
    logger.info(
        "stage=pos_sync trace_id=%s lock_held feed=%s skipped=1",
        trace_id,
        feed,
        extra={"trace_id": trace_id},
    )
