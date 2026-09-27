"""Injectable `ai.pos_shop` persistence. SQLAlchemy Core; no mapped class. C43.

Two rules govern this module, and both are the opposite of the ones next door in
`pos_projection.py` — which is the whole reason it is a separate table and a separate drain.

**The reading is complete, so the write is a replacement.** `ai.pos_projection` is fed by an
incremental keyset feed where absence means "nothing changed"; here absence means **the shop
is gone from the business**. So a drain inserts or updates what the reading states and
*deletes* what it does not, and the two halves are one transaction. A committed delete without
its insert would leave the table empty, and an empty table is a state post-deployment
verification is specified to fail on: emptiness must only ever mean *nobody has drained yet*,
never *a drain was half applied*.

**There is no checkpoint and there is nothing to resume.** No cursor, no watermark, no row in
`ai.sync_checkpoint`. A drain either states the whole world or it changes nothing, so there is
no partial progress a later run would need to pick up — which is what makes this drain cheap
enough to run in full on every tick.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import text

from jbg_ai.config.settings import Settings
from jbg_ai.db.engine import session_scope
from jbg_ai.indexing.feed import PosShopItem


@dataclass(frozen=True)
class PosShopRow:
    """One stored point of sale: its identifier, its activity, and when it was written."""

    pos_id: UUID
    is_active: bool
    refreshed_at: datetime


class PosShopRepo(Protocol):
    """Implementations must not read or write schema `public`."""

    async def replace_all(
        self, items: list[PosShopItem], *, refreshed_at: datetime
    ) -> tuple[int, int]:
        """Replace the table with this reading, atomically. Returns `(written, removed)`."""
        ...

    async def get(self, pos_id: UUID) -> PosShopRow | None: ...

    async def count(self) -> int: ...


_UPSERT_SQL = text(
    """
    INSERT INTO ai.pos_shop (pos_id, is_active, refreshed_at)
    VALUES (:pos_id, :is_active, :refreshed_at)
    ON CONFLICT (pos_id) DO UPDATE SET
        is_active = EXCLUDED.is_active,
        refreshed_at = EXCLUDED.refreshed_at
    """
)

#: The other half of the replacement. Bound to the identifiers the reading stated rather than
#: to `refreshed_at < :now`, because a timestamp comparison would depend on the clock of the
#: writer agreeing with the clock of the rows — and a shop whose row happened to be written in
#: the same microsecond would survive a removal it deserved.
_DELETE_MISSING_SQL = text(
    "DELETE FROM ai.pos_shop WHERE NOT (pos_id = ANY(:keep))"
)

_DELETE_ALL_SQL = text("DELETE FROM ai.pos_shop")

_SELECT_ONE_SQL = text(
    "SELECT pos_id, is_active, refreshed_at FROM ai.pos_shop WHERE pos_id = :pos_id"
)


class SqlAlchemyPosShopRepo:
    """Core implementation over the existing engine (pool 5, max_overflow=0)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def replace_all(
        self, items: list[PosShopItem], *, refreshed_at: datetime
    ) -> tuple[int, int]:
        """One transaction: write the reading and retire everything absent from it.

        **An empty reading empties the table, deliberately.** It is tempting to guard against
        it — a feed answering with no shops looks like a bug — but a business with no point of
        sale is not an environment anybody should be shown, and post-deployment verification
        is specified to fail on exactly that. Silently keeping the previous reading would turn
        a loud, correct failure into a stale table nobody questions.
        """
        rows = [
            {
                "pos_id": item.pos_id,
                "is_active": item.is_active,
                "refreshed_at": refreshed_at,
            }
            for item in items
        ]
        keep = [item.pos_id for item in items]

        async with session_scope(self._settings) as session:
            if rows:
                await session.execute(_UPSERT_SQL, rows)
                removed = (
                    await session.execute(_DELETE_MISSING_SQL, {"keep": keep})
                ).rowcount
            else:
                removed = (await session.execute(_DELETE_ALL_SQL)).rowcount

        return len(rows), int(removed or 0)

    async def get(self, pos_id: UUID) -> PosShopRow | None:
        async with session_scope(self._settings) as session:
            row = (
                await session.execute(_SELECT_ONE_SQL, {"pos_id": pos_id})
            ).mappings().first()
        if row is None:
            return None
        return PosShopRow(
            pos_id=row["pos_id"],
            is_active=bool(row["is_active"]),
            refreshed_at=row["refreshed_at"],
        )

    async def count(self) -> int:
        async with session_scope(self._settings) as session:
            value = (
                await session.execute(text("SELECT count(*) FROM ai.pos_shop"))
            ).scalar()
        return int(value or 0)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)
