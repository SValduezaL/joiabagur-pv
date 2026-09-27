"""Health probe double: answers from memory and counts how often it was asked.

The count is the point of the double, not a convenience. Two of the properties
`/health` promises — that it never opens a second connection inside the cache
window, and that it never reaches the embedding provider — are only observable
by counting what it did.
"""

from __future__ import annotations

from datetime import datetime

from jbg_ai.api.health_report import IndexSnapshot


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
        projection_scoped_points_of_sale: int = 0,
        projection_failed_pages: int = 0,
    ) -> None:
        self._snapshot = IndexSnapshot(
            database_reachable=database_reachable,
            documents=documents,
            models=models,
            database_configured=database_configured,
            projection_synced_at=projection_synced_at,
            projection_full_synced_at=projection_full_synced_at,
            projection_points_of_sale=projection_points_of_sale,
            projection_scoped_points_of_sale=projection_scoped_points_of_sale,
            projection_failed_pages=projection_failed_pages,
        )
        self.calls = 0

    async def snapshot(self) -> IndexSnapshot:
        self.calls += 1
        return self._snapshot
