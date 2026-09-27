"""Application lifespan: what starts with the process and what stops with it. C41.

**Why this is not in `main.py`.** The application factory is forbidden from naming
`jbg_ai.indexing`, and the rule is not cosmetic: `indexing/cli.py` imports the embedding client
and through it the provider SDK, so an import there would put provider machinery in the import
graph of a process whose job is to answer HTTP. `test_main_does_not_import_indexing` and
`test_unit_suite_makes_no_provider_calls` guard that, and they caught this change trying to
break it.

The scheduler reaches the drain through `indexing/pos_drain.py`, which touches no embeddings at
all — the POS drain needs no embedding key because it embeds nothing — so the property the rule
protects is preserved rather than circumvented. That both this module and `main.py` stay clear
of the provider modules is asserted by those same tests, extended to cover this file.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from fastapi import FastAPI

from jbg_ai.config.settings import Settings
from jbg_ai.indexing.scheduler import run_scheduler, scheduler_should_run

logger = logging.getLogger(__name__)


def build_lifespan(resolved: Settings) -> Callable[[FastAPI], AsyncIterator[None]]:
    """Start the POS drain scheduler, and never make start-up wait for it.

    **The task is created and deliberately not awaited.** The container health check probes
    `GET /health` on a three-second timeout and the composition chains service start-up on it,
    so awaiting a drain — tens of pages against a budget of three minutes on a fresh
    environment — would mark the container unhealthy and fail the deployment *because of the
    improvement*. Yielding immediately is what keeps `/health` answering 200 throughout.

    On shutdown the task is cancelled and awaited, so an orderly stop does not wait out an
    interval and does not leave the event loop reporting a task nobody collected.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        task: asyncio.Task[None] | None = None
        if scheduler_should_run(resolved):
            task = asyncio.create_task(
                run_scheduler(resolved), name="pos-projection-drain"
            )
            app.state.pos_sync_task = task
        else:
            logger.info(
                "stage=pos_sync_scheduler not_started enabled=%s stub_mode=%s feed=%s",
                resolved.jpv_pos_sync_scheduler_enabled,
                resolved.stub_mode,
                bool(resolved.jpv_index_feed_base_url),
            )
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    return lifespan
