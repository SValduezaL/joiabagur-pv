"""CLI: `python -m jbg_ai.indexing sync|sync-pos [--full]`.

`sync` is the catalog drain, the same one `POST /v1/index/sync` runs. `sync-pos` is the
POS availability drain, which has **no** route: `ai-service-api-contracts` enumerates the
`/v1` surface in a MUST, and a synchronisation nobody calls over HTTP does not need one.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Coroutine
from collections.abc import Sequence
from typing import Any, TypeVar

import httpx

from jbg_ai.config.settings import Settings, get_settings
from jbg_ai.indexing.constants import DEFAULT_EMBEDDING_MODEL
from jbg_ai.indexing.drain_lock import DrainLock
from jbg_ai.indexing.embeddings import EmbeddingClient, LiteLlmEmbeddingClient
from jbg_ai.indexing.feed import FEED_TIMEOUT_SECONDS, HttpxIndexFeedClient, IndexFeedClient
from jbg_ai.indexing.orchestrator import CatalogSyncRequest, CatalogSyncResult, sync_catalog
from jbg_ai.indexing.pos_drain import run_pos_drain
from jbg_ai.indexing.pos_orchestrator import PosSyncResult, describe
from jbg_ai.indexing.pos_projection import PosProjectionRepo
from jbg_ai.indexing.provenance import ProvenanceEntry, load_provenance_map
from jbg_ai.indexing.repository import ProductDocumentRepo, SqlAlchemyProductDocumentRepo
from jbg_ai.indexing.sync_errors import IndexFeedConfigError, ProvenanceMapError
from jbg_ai.knowledge.corpus import validate_corpus
from jbg_ai.knowledge.errors import KnowledgeError
from jbg_ai.knowledge.indexer import (
    KnowledgeRepo,
    KnowledgeSyncResult,
    SqlAlchemyKnowledgeRepo,
    describe as describe_knowledge,
    sync_knowledge,
)

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run the drain on a loop psycopg can use.

    Python installs the `ProactorEventLoop` on Windows and psycopg's async driver refuses
    it outright, so `asyncio.run` fails every query on a development machine with an error
    that names neither the database nor the query. The README already records this trap for
    running the service under uvicorn; a command whose whole job is to write to PostgreSQL
    should not make each operator rediscover it. No effect on Linux, where the selector loop
    is already the default, and none in the container.
    """
    if sys.platform == "win32":
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            return runner.run(coro)
    return asyncio.run(coro)


async def run_cli_sync(
    *,
    full: bool = False,
    settings: Settings | None = None,
    feed: IndexFeedClient | None = None,
    embed: EmbeddingClient | None = None,
    repo: ProductDocumentRepo | None = None,
    provenance_map: dict[str, ProvenanceEntry] | None = None,
) -> CatalogSyncResult:
    resolved = settings or get_settings()
    mapping = provenance_map if provenance_map is not None else load_provenance_map()
    if feed is not None and embed is not None and repo is not None:
        return await sync_catalog(
            CatalogSyncRequest(full=full),
            feed=feed,
            embed=embed,
            repo=repo,
            provenance_map=mapping,
            time_budget_seconds=resolved.jpv_index_sync_time_budget_seconds,
        )
    if not resolved.jpv_index_feed_base_url:
        raise IndexFeedConfigError("JPV_INDEX_FEED_BASE_URL")
    if not resolved.jpv_index_feed_api_key:
        raise IndexFeedConfigError("JPV_INDEX_FEED_API_KEY")
    if not resolved.jpv_embedding_api_key:
        raise IndexFeedConfigError("JPV_EMBEDDING_API_KEY")
    async with httpx.AsyncClient(
        base_url=resolved.jpv_index_feed_base_url.rstrip("/"),
        timeout=FEED_TIMEOUT_SECONDS,
    ) as client:
        live_feed = feed or HttpxIndexFeedClient(client, resolved.jpv_index_feed_api_key)
        live_embed = embed or LiteLlmEmbeddingClient(
            api_key=resolved.jpv_embedding_api_key,
            model=resolved.jpv_embedding_model or DEFAULT_EMBEDDING_MODEL,
            base_url=resolved.jpv_embedding_base_url,
            batch_size=resolved.jpv_embedding_batch_size,
        )
        live_repo = repo or SqlAlchemyProductDocumentRepo(resolved)
        return await sync_catalog(
            CatalogSyncRequest(full=full),
            feed=live_feed,
            embed=live_embed,
            repo=live_repo,
            provenance_map=mapping,
            time_budget_seconds=resolved.jpv_index_sync_time_budget_seconds,
        )


async def run_cli_sync_pos(
    *,
    full: bool = False,
    settings: Settings | None = None,
    feed: IndexFeedClient | None = None,
    repo: PosProjectionRepo | None = None,
    lock: DrainLock | None = None,
) -> PosSyncResult:
    """Drain the POS availability feed. Needs no embedding key: it embeds nothing.

    A thin delegation to `pos_drain.run_pos_drain`, which is where the construction lives so
    that the scheduler can reach it **without importing this module**. Importing `cli` from the
    FastAPI application factory would drag `LiteLlmEmbeddingClient` — and through it the provider
    SDK — into the app's import graph, which `test_main_does_not_import_indexing` forbids.

    Kept as a name of its own rather than replaced, because it is what the command line and the
    existing tests call, and renaming it would be churn with no property gained.
    """
    return await run_pos_drain(
        full=full, settings=settings, feed=feed, repo=repo, lock=lock
    )


async def run_cli_sync_knowledge(
    *,
    full: bool = False,
    settings: Settings | None = None,
    embed: EmbeddingClient | None = None,
    repo: KnowledgeRepo | None = None,
) -> KnowledgeSyncResult:
    """Index `data/knowledge/` into the two C05 knowledge tables.

    Needs no index feed: the corpus is versioned in git and is the whole truth, so there is
    no cursor to resume and `--full` means *re-embed everything* rather than *ignore a
    checkpoint*. It does need an embedding key, unlike `sync-pos`, because it embeds.

    The corpus is validated **before** anything is written: an invalid document must fail
    the command, not land half-indexed.
    """
    resolved = settings or get_settings()
    corpus = validate_corpus()
    if embed is not None and repo is not None:
        return await sync_knowledge(corpus, embed=embed, repo=repo, full=full)
    if not resolved.jpv_embedding_api_key:
        raise IndexFeedConfigError("JPV_EMBEDDING_API_KEY")
    live_embed = embed or LiteLlmEmbeddingClient(
        api_key=resolved.jpv_embedding_api_key,
        model=resolved.jpv_embedding_model or DEFAULT_EMBEDDING_MODEL,
        base_url=resolved.jpv_embedding_base_url,
        batch_size=resolved.jpv_embedding_batch_size,
    )
    live_repo = repo or SqlAlchemyKnowledgeRepo(resolved)
    return await sync_knowledge(corpus, embed=live_embed, repo=live_repo, full=full)


def run_module(argv: Sequence[str] | None = None) -> int:
    """Process entry point for `python -m jbg_ai.indexing`.

    Loads `backend/.env` — the same file Compose interpolates, and the single place
    the local credentials live — before any setting is read. Until this existed the
    command silently depended on the variables already being exported by hand, while
    `python -m jbg_ai.data` had been loading them since C06b.

    It lives here and not inside `main` on purpose: tests call `main` directly, and
    `support.settings.build_settings` pins the optional fields to `None` precisely so
    that a developer's exported credentials cannot make an "absent configuration" case
    stop failing as it should. Loading the file from a code path a test can reach would
    undo that guarantee.
    """
    from jbg_ai.data.envload import load_local_env

    load_local_env()
    return main(argv)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m jbg_ai.indexing")
    sub = parser.add_subparsers(dest="command", required=True)
    sync_parser = sub.add_parser("sync", help="Drain the catalog index feed")
    sync_parser.add_argument(
        "--full",
        action="store_true",
        help="Ignore checkpoint and body cursor; start without query params",
    )
    pos_parser = sub.add_parser(
        "sync-pos", help="Drain the POS availability feed into ai.pos_projection"
    )
    pos_parser.add_argument(
        "--full",
        action="store_true",
        help="Ignore the pos-availability checkpoint; start without query params",
    )
    knowledge_parser = sub.add_parser(
        "sync-knowledge",
        help="Index data/knowledge/ into ai.knowledge_document and ai.knowledge_chunk",
    )
    knowledge_parser.add_argument(
        "--full",
        action="store_true",
        help="Re-embed every chunk, even the ones whose content and version are unchanged",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command not in {"sync", "sync-pos", "sync-knowledge"}:
        parser.error("unknown command")

    if args.command == "sync-knowledge":
        try:
            knowledge_result = run_async(run_cli_sync_knowledge(full=args.full))
        except (IndexFeedConfigError, KnowledgeError) as exc:
            sys.stderr.write(f"{exc}\n")
            return 1
        sys.stdout.write(describe_knowledge(knowledge_result) + "\n")
        return 0

    if args.command == "sync-pos":
        try:
            pos_result = run_async(run_cli_sync_pos(full=args.full))
        except IndexFeedConfigError as exc:
            sys.stderr.write(f"{exc}\n")
            return 1
        sys.stdout.write(describe(pos_result) + "\n")
        # **Declining is not failing, and gets its own code.** Another drain held the lock, so
        # the work is being done right now by the process that holds it; exiting 1 would put a
        # scheduled drain overlapping a manual one on the same footing as a page nobody drained,
        # and a cron wrapper that alerts on non-zero would page somebody for a healthy system.
        # Exiting 0 would be worse in the other direction: a script that runs this and then
        # measures would believe it had just refreshed the projection.
        if pos_result.declined:
            return 75  # EX_TEMPFAIL: try again, nothing is wrong.
        # A page that failed is a page nobody drained. Reporting success would let a
        # partially synchronised projection look like a complete one, which is the shape
        # of lie the freshness guard exists to prevent one layer up.
        return 1 if pos_result.failed_pages else 0

    try:
        result = run_async(run_cli_sync(full=args.full))
    except (IndexFeedConfigError, ProvenanceMapError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    sys.stdout.write(
        f"upserted={result.upserted} skipped={result.skipped} "
        f"deleted={result.deleted} failed={result.failed}\n"
    )
    return 0
