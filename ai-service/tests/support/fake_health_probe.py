"""Health probe double: answers from memory and counts how often it was asked.

The count is the point of the double, not a convenience. Two of the properties
`/health` promises — that it never opens a second connection inside the cache
window, and that it never reaches the embedding provider — are only observable
by counting what it did.
"""

from __future__ import annotations

from datetime import datetime

from jbg_ai.api.health_report import IndexSnapshot
from jbg_ai.indexing.pos_projection import POS_FEED


class FakeHealthProbe:
    def __init__(
        self,
        *,
        database_reachable: bool = True,
        documents: int = 0,
        models: tuple[str, ...] = (),
        database_configured: bool = True,
        projection_synced_at: datetime | None = None,
        projection_full_synced_at: datetime | None = None,
        projection_points_of_sale: int = 0,
        projection_active_points_of_sale: int = 0,
        projection_active_without_scope: int | None = None,
        projection_failures_by_feed: dict[str, int] | None = None,
        projection_failed_pages: int | None = None,
    ) -> None:
        # `projection_failed_pages` is kept as a convenience for the many tests that only
        # care about the POS feed's count: it is folded into the per-feed mapping the
        # snapshot now carries, so neither those tests nor this double had to learn the
        # breakdown in order to keep asserting what they always asserted.
        failures = dict(projection_failures_by_feed or {})
        if projection_failed_pages is not None:
            failures.setdefault(POS_FEED, projection_failed_pages)

        self._snapshot = IndexSnapshot(
            database_reachable=database_reachable,
            documents=documents,
            models=models,
            database_configured=database_configured,
            projection_synced_at=projection_synced_at,
            projection_full_synced_at=projection_full_synced_at,
            projection_points_of_sale=projection_points_of_sale,
            projection_active_points_of_sale=projection_active_points_of_sale,
            projection_active_without_scope=projection_active_without_scope,
            projection_failures_by_feed=failures,
        )
        self.calls = 0

    async def snapshot(self) -> IndexSnapshot:
        self.calls += 1
        return self._snapshot
