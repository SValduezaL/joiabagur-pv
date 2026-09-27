"""In-memory `ai.pos_shop` repository. No sockets, no RDS. Delivered by C43.

It applies the same *replacement* the SQL port applies — write what the reading states, remove
what it does not — so a test that would fail against PostgreSQL fails here too. A fake that
merely accumulated rows would be worse than none: it would make the one property this table
exists for, that a shop leaving the business leaves the table, untestable without a database.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from jbg_ai.indexing.feed import PosShopItem
from jbg_ai.indexing.pos_shop import PosShopRow


class FakePosShopRepo:
    def __init__(self, *, fail_on_replace: bool = False) -> None:
        self.rows: dict[UUID, PosShopRow] = {}
        self.replacements = 0
        #: When set, the write blows up — for the drain tests that assert a failure is
        #: swallowed by the scheduler rather than escaping it.
        self.fail_on_replace = fail_on_replace

    async def replace_all(
        self, items: list[PosShopItem], *, refreshed_at: datetime
    ) -> tuple[int, int]:
        self.replacements += 1
        if self.fail_on_replace:
            raise RuntimeError("pos_shop write failed")

        keep = {item.pos_id for item in items}
        removed = [pos_id for pos_id in self.rows if pos_id not in keep]
        for pos_id in removed:
            del self.rows[pos_id]

        for item in items:
            self.rows[item.pos_id] = PosShopRow(
                pos_id=item.pos_id,
                is_active=item.is_active,
                refreshed_at=refreshed_at,
            )

        return len(items), len(removed)

    async def get(self, pos_id: UUID) -> PosShopRow | None:
        return self.rows.get(pos_id)

    async def count(self) -> int:
        return len(self.rows)
