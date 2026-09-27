"""Point-of-sale scope resolution and projection freshness. Delivered by C22.

Freshness is read from `ai.sync_checkpoint.last_incremental_sync_at`, and the reason is the
whole reason this module exists rather than a one-line `max()` in the orchestrator. The POS
availability feed is **incremental by keyset**: an assignment that does not change is never
re-emitted, so `ai.pos_projection.refreshed_at` records when that assignment last changed,
not when the projection was last looked at. Reading the age from the rows would report months
of staleness on a projection synchronised thirty seconds ago, and the guard below would then
disable the scope on a perfectly current projection, permanently.

The read is cached for ten seconds — the same window and the same reason as the health
report: the pool is capped at five connections with no overflow, and one extra round trip per
retrieval to answer a question whose answer changes at cron cadence is a connection spent on
nothing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable
from uuid import UUID

from jbg_ai.retrieval.errors import InvalidPosIdError, RetrievalDependencyError
from jbg_ai.retrieval.ports import ProductSearchPort

#: Matching C17's health report, and for the same reason.
FRESHNESS_CACHE_SECONDS = 10.0

EMPTY_PROJECTION_DETAIL = (
    "the point-of-sale projection holds no assigned product for this token; "
    "refusing to abstain over an empty projection"
)


def parse_pos_id(raw: str | None) -> UUID | None:
    """The token claim as a UUID, `None` when it was omitted, or a rejection.

    A claim that does not parse is a mis-issued token, never a request for a global search.
    The auth module wrote the rule before this scope existed: a wildcard point of sale is
    exactly what must not exist, because this claim is the retriever's only hard filter.
    Widening to the whole catalogue on a malformed value would turn a broken token into a
    silent leak of every other shop's assortment.

    **C40 separates the omission from the malformation, and only the first is admitted.** A
    token issued for a search spread over every shop carries no `pos_id` at all, and there is
    nothing broken about that; a token carrying an unusable value is still broken, and an empty
    string is a value. The two used to share a branch because only one of them could happen.
    """
    if raw is None:
        return None
    if not raw.strip():
        raise InvalidPosIdError("pos_id claim is present but empty")
    try:
        return UUID(raw.strip())
    except ValueError as exc:
        raise InvalidPosIdError(f"pos_id claim is not a UUID: {raw!r}") from exc


@dataclass(frozen=True)
class ProjectionScope:
    """What one request decided about the point-of-sale scope, and why."""

    #: The scope to apply in SQL, or `None` when this request runs unscoped.
    pos_id: UUID | None
    #: Seconds since the last drain, or `None` when nothing has ever synchronised.
    age_seconds: float | None
    #: Assigned rows this point of sale carries, `-1` when the count was not taken.
    size: int
    applied: bool
    stale: bool

    @property
    def reported_age(self) -> float | None:
        """What the response carries. Absent when the prefilter did not run at all."""
        return self.age_seconds if (self.applied or self.stale) else None


class ProjectionFreshness:
    """Short-lived cache over the checkpoint read. Safe to share across requests."""

    def __init__(
        self,
        *,
        ttl_seconds: float = FRESHNESS_CACHE_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock or time.monotonic
        self._value: datetime | None = None
        self._read_at: float | None = None

    def invalidate(self) -> None:
        self._value = None
        self._read_at = None

    async def synced_at(self, search: ProductSearchPort) -> datetime | None:
        now = self._clock()
        if self._read_at is not None and now - self._read_at < self._ttl:
            return self._value
        self._value = await search.projection_synced_at()
        self._read_at = now
        return self._value


#: Process-wide by default, like the retrieval embedding client. Tests inject their own.
default_freshness = ProjectionFreshness()


def age_seconds(synced_at: datetime | None, *, now: datetime | None = None) -> float | None:
    """Seconds since the last drain. `None` when the drain has never run."""
    if synced_at is None:
        return None
    reference = now or datetime.now(tz=UTC)
    if synced_at.tzinfo is None:
        synced_at = synced_at.replace(tzinfo=UTC)
    return max((reference - synced_at).total_seconds(), 0.0)


async def resolve_scope(
    pos_id: UUID | None,
    *,
    search: ProductSearchPort,
    enabled: bool,
    max_age_seconds: int,
    freshness: ProjectionFreshness,
    now: datetime | None = None,
) -> ProjectionScope:
    """Decide whether this request is scoped, degraded, or refused.

    Three outcomes, in the order the design fixes them:

    **Empty** — the projection holds no assigned row for this point of sale. That is a
    dependency failure and it fails loudly, because a 200 with an empty list is
    indistinguishable from a legitimate abstention, and the operator's panel paints the same
    "we found nothing" screen over both.

    **Stale** — older than the ceiling. The scope is dropped for this request and the age is
    reported. The page may come back short; no valid product is hidden from the authority
    that hydrates it, which is the promise staleness has to keep.

    **Fresh** — the scope is applied.
    """
    # **No point of sale named, so there is no scope to resolve.** Not a degradation and not a
    # failure: the caller asked about every shop, and the prefilter simply does not apply. It is
    # reported as not applied, exactly like the switch being off, because for the reader of the
    # stage line those are the same fact — no restriction ran.
    if not enabled or pos_id is None:
        return ProjectionScope(
            pos_id=None, age_seconds=None, size=-1, applied=False, stale=False
        )

    size = await search.count_scope(pos_id)
    if size == 0:
        raise RetrievalDependencyError(EMPTY_PROJECTION_DETAIL)

    age = age_seconds(await freshness.synced_at(search), now=now)
    stale = age is None or age > max_age_seconds
    return ProjectionScope(
        pos_id=None if stale else pos_id,
        age_seconds=age,
        size=size,
        applied=not stale,
        stale=stale,
    )
