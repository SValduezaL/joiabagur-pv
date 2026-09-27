"""Scheduled drain of `ai.pos_projection`. Delivered by C41.

**Why this module exists, when C22 argued it should not.** C22 shipped the drain as a command
with a documented cron and wrote down three reasons for refusing an in-process scheduler: a
background task inside a 512 MiB container competing for a pool of five connections; a frozen
contract that enumerates the `/v1` surface in a MUST; and the position that honesty about
staleness comes from the reported projection age rather than from a hidden cron.

The second never applied to a scheduler, only to a route, and this module adds none. The first
is answered by what a drain actually costs: an incremental run fetches nought or one page of at
most two hundred rows and holds a connection for seconds, once every ten minutes, keeping no
state between ticks. The third is answered by what happened — the age was reported faithfully
for twenty days and **reached no screen**, across three sessions and two distinct failure modes,
and two of those sessions published measurements taken over a scope that had silently degraded.
Reporting honestly was necessary and it was not sufficient. The cron also stops being hidden:
`GET /health` now states when the drain last ran.

**And the cron C22 documented was never installed, for a reason that is not forgetfulness.** The
recipe began by changing into a host directory, while this service ships as a container. It
described a deployment that does not exist.

**Why the start-up drain is the part that matters.** Every recorded incident was found by
somebody bringing an environment up in order to test it — not in steady state. An interval alone
leaves a window open at exactly the moment the system is being measured, and a host-level cron
does not run on a developer machine at all. Draining at start-up makes *the environment is up*
imply *the projection is fresh*, which is the invariant that was missing.
"""

from __future__ import annotations

import asyncio
import logging

from jbg_ai.config.settings import Settings
from jbg_ai.indexing.pos_drain import run_pos_drain
from jbg_ai.indexing.pos_orchestrator import PosSyncResult, new_trace_id
from jbg_ai.indexing.sync_errors import IndexFeedConfigError

logger = logging.getLogger(__name__)

#: Backoff for a start-up drain that cannot reach the feed, in seconds.
#:
#: Bounded and short, and it gives up to the ordinary interval rather than retrying for ever.
#: The case this exists for is local development, where `jbg-ai` comes up in Compose while the
#: .NET API is still being started by hand: the drain fails, retries, and succeeds the moment the
#: feed appears — which is the moment somebody is about to start testing. Past that, a feed that
#: is still down is not a start-up problem any more and the interval handles it.
BOOT_RETRY_DELAYS_SECONDS: tuple[float, ...] = (5.0, 15.0, 45.0)


def scheduler_should_run(settings: Settings) -> bool:
    """Whether this process drains on a schedule at all.

    Three conditions, and each removes a way of being wrong rather than being a preference:

    * The switch, which is the ablation and the rollback.
    * Not `STUB_MODE`: a stubbed service answers from fixtures and has no real feed to drain, so
      a scheduler there would log failures for ever about a dependency nobody intended to have.
    * A configured feed, for the same reason the retrieval embedding client is only built when
      its credential is present — building a client that cannot work and discovering it at the
      first tick is strictly worse than not building it.
    """
    return bool(
        settings.jpv_pos_sync_scheduler_enabled
        and not settings.stub_mode
        and settings.jpv_index_feed_base_url
        and settings.jpv_index_feed_api_key
    )


async def drain_once(settings: Settings, *, trace_id: str) -> PosSyncResult | None:
    """One drain. Returns `None` when it could not run; never raises.

    **Never raises, and that is the requirement rather than defensiveness.** This runs inside a
    task nobody awaits, so an exception escaping here would become an unretrieved task
    exception — logged by the event loop at an arbitrary later moment, with no correlation to the
    drain that caused it, and with the loop having silently stopped draining.

    **`full` is not passed and does not need to be.** `resolve_start_cursor` already returns an
    empty keyset when no checkpoint exists, and the orchestrator computes `is_full` from exactly
    that, so a fresh environment drains in full on its own. Asking the checkpoint here in order
    to decide would be a second read of the same fact and a second chance to disagree with it.
    """
    try:
        result = await run_pos_drain(settings=settings)
    except IndexFeedConfigError as exc:
        logger.warning(
            "stage=pos_sync_scheduler trace_id=%s feed_not_configured error=%s",
            trace_id,
            exc,
            extra={"trace_id": trace_id},
        )
        return None
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - see the docstring
        logger.warning(
            "stage=pos_sync_scheduler trace_id=%s drain_failed error=%s",
            trace_id,
            exc,
            extra={"trace_id": trace_id},
        )
        return None

    if result.declined:
        return result

    logger.info(
        "stage=pos_sync_scheduler trace_id=%s drained pages=%s upserted=%s "
        "soft_deleted=%s failed_pages=%s",
        trace_id,
        result.pages,
        result.upserted,
        result.soft_deleted,
        result.failed_pages,
        extra={"trace_id": trace_id},
    )
    return result


async def _boot_drain(settings: Settings) -> None:
    """Drain once at start-up, retrying a bounded number of times."""
    for attempt, delay in enumerate((0.0,) + BOOT_RETRY_DELAYS_SECONDS):
        if delay:
            await asyncio.sleep(delay)
        trace = new_trace_id()
        logger.info(
            "stage=pos_sync_scheduler trace_id=%s boot_drain attempt=%s",
            trace,
            attempt + 1,
            extra={"trace_id": trace},
        )
        if await drain_once(settings, trace_id=trace) is not None:
            return

    logger.warning(
        "stage=pos_sync_scheduler boot_drain_exhausted attempts=%s "
        "handing over to the interval",
        len(BOOT_RETRY_DELAYS_SECONDS) + 1,
    )


async def run_scheduler(settings: Settings) -> None:
    """Drain at start-up and then every interval, until cancelled.

    Cancellation is the normal way this ends: the application lifespan cancels the task on
    shutdown and the `CancelledError` propagates, which is what lets an orderly shutdown be
    orderly instead of waiting out an interval.
    """
    interval = settings.jpv_pos_sync_interval_seconds
    logger.info(
        "stage=pos_sync_scheduler started interval_seconds=%s ceiling_seconds=%s",
        interval,
        settings.jpv_pos_projection_max_age_seconds,
    )

    await _boot_drain(settings)

    while True:
        await asyncio.sleep(interval)
        await drain_once(settings, trace_id=new_trace_id())
