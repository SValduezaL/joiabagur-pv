"""Shop activity: feed typing, the drain, and `ai.pos_shop` persistence. Delivered by C43.

The offline half runs against the in-memory fake. The `db` half runs the real SQL against an
ephemeral PostgreSQL, because the property this table exists for — that a shop absent from the
reading is **removed**, atomically, and that an empty reading empties the table rather than
half-emptying it — is a property of statements, and a fake that never executed one would prove
nothing about it.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from jbg_ai.config.settings import Settings
from jbg_ai.indexing.feed import (
    POS_SHOPS_PATH,
    PosShopItem,
    PosShopsReading,
    parse_pos_shop_item,
    parse_pos_shops_reading,
)
from jbg_ai.indexing import pos_shop as pos_shop_module
from jbg_ai.indexing.pos_shop import SqlAlchemyPosShopRepo
from jbg_ai.indexing.pos_shop_drain import run_pos_shop_drain, sync_pos_shops
from support.async_db import run_db
from support.fake_pos_shop import FakePosShopRepo

SHOP_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
SHOP_B = uuid.UUID("22222222-2222-2222-2222-222222222222")
SHOP_C = uuid.UUID("33333333-3333-3333-3333-333333333333")

#: The shop the finding is about: `HT-ARTRUTX`, closed on purpose since 2025-09-30.
ARTRUTX = uuid.UUID("cd9bfd1f-f1b2-4795-9d14-867a75c18f90")

REFRESHED = datetime(2026, 9, 27, 13, 33, 5, tzinfo=UTC)


def run(coro):
    """Drive one coroutine. The suite installs no asyncio plugin, by convention."""
    return asyncio.run(coro)


def repo_for(settings: Settings, database_url: str) -> SqlAlchemyPosShopRepo:
    return SqlAlchemyPosShopRepo(
        settings.model_copy(update={"database_url": database_url})
    )


class StubShopFeed:
    """Answers one reading and records that it was asked. Opens no socket."""

    def __init__(self, reading: PosShopsReading) -> None:
        self.reading = reading
        self.calls = 0

    async def fetch_pos_shops(self) -> PosShopsReading:
        self.calls += 1
        return self.reading


def reading(*items: PosShopItem, computed_as_of: datetime | None = None) -> PosShopsReading:
    return PosShopsReading(items=list(items), computed_as_of=computed_as_of)


# --------------------------------------------------------------------------- parsing


def test_the_route_is_the_one_the_dotnet_side_serves() -> None:
    assert POS_SHOPS_PATH == "/api/ai/index-feed/pos-shops"


def test_parsing_reads_the_identifier_and_the_activity() -> None:
    item = parse_pos_shop_item({"pointOfSaleId": str(SHOP_A), "isActive": False})

    assert item.pos_id == SHOP_A
    assert item.is_active is False


def test_parsing_tolerates_fields_it_does_not_know() -> None:
    """The consumer must not break when the .NET side adds a field, as C41 established."""
    item = parse_pos_shop_item(
        {"pointOfSaleId": str(SHOP_A), "isActive": True, "code": "CIU-CENTRE", "n": 7}
    )

    assert item.pos_id == SHOP_A
    assert item.is_active is True


def test_an_unstated_activity_defaults_to_active() -> None:
    """The safe direction: it can over-report a shop as needing attention, never under-report.

    Defaulting to inactive would silently drop a genuinely broken shop out of the count, which
    is the exact failure this capability exists to stop.
    """
    assert parse_pos_shop_item({"pointOfSaleId": str(SHOP_A)}).is_active is True


def test_the_reading_carries_no_cursor_and_states_its_instant() -> None:
    parsed = parse_pos_shops_reading(
        {
            "items": [
                {"pointOfSaleId": str(SHOP_A), "isActive": True},
                {"pointOfSaleId": str(ARTRUTX), "isActive": False},
            ],
            "computedAsOf": "2026-09-27T13:33:05+00:00",
        }
    )

    assert len(parsed.items) == 2
    assert parsed.computed_as_of == datetime(2026, 9, 27, 13, 33, 5, tzinfo=UTC)
    assert not hasattr(parsed, "next_cursor")
    assert not hasattr(parsed, "has_more")


def test_a_reading_whose_items_are_not_a_list_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        parse_pos_shops_reading({"items": {"pointOfSaleId": str(SHOP_A)}})


# --------------------------------------------------------------------------- the drain


def test_the_drain_writes_the_whole_reading() -> None:
    feed = StubShopFeed(
        reading(
            PosShopItem(pos_id=SHOP_A, is_active=True),
            PosShopItem(pos_id=SHOP_B, is_active=True),
            PosShopItem(pos_id=ARTRUTX, is_active=False),
        )
    )
    repo = FakePosShopRepo()

    result = run(sync_pos_shops(feed=feed, repo=repo, refreshed_at=REFRESHED))

    assert result.written == 3
    assert result.removed == 0
    assert result.active == 2, "the closed shop is stored but not counted as active"
    assert repo.rows[ARTRUTX].is_active is False


def test_a_shop_absent_from_the_reading_is_removed() -> None:
    """The reason the feed is complete: a cursored one could never say this."""
    repo = FakePosShopRepo()
    first = StubShopFeed(
        reading(
            PosShopItem(pos_id=SHOP_A, is_active=True),
            PosShopItem(pos_id=SHOP_B, is_active=True),
        )
    )
    run(sync_pos_shops(feed=first, repo=repo, refreshed_at=REFRESHED))

    second = StubShopFeed(reading(PosShopItem(pos_id=SHOP_A, is_active=True)))
    result = run(sync_pos_shops(feed=second, repo=repo, refreshed_at=REFRESHED))

    assert result.written == 1
    assert result.removed == 1
    assert SHOP_B not in repo.rows


def test_a_shop_that_closes_is_kept_and_marked_inactive() -> None:
    """Closed and deleted need opposite treatment, so the feed must distinguish them."""
    repo = FakePosShopRepo()
    run(
        sync_pos_shops(
            feed=StubShopFeed(reading(PosShopItem(pos_id=ARTRUTX, is_active=True))),
            repo=repo,
            refreshed_at=REFRESHED,
        )
    )

    run(
        sync_pos_shops(
            feed=StubShopFeed(reading(PosShopItem(pos_id=ARTRUTX, is_active=False))),
            repo=repo,
            refreshed_at=REFRESHED,
        )
    )

    assert ARTRUTX in repo.rows, "a closed shop keeps its row"
    assert repo.rows[ARTRUTX].is_active is False


def test_the_drain_needs_no_provider_credential() -> None:
    """It embeds nothing, which is what lets it run inside the process that answers HTTP."""
    feed = StubShopFeed(reading(PosShopItem(pos_id=SHOP_A, is_active=True)))
    repo = FakePosShopRepo()

    result = run(run_pos_shop_drain(feed=feed, repo=repo))

    assert result.written == 1
    assert feed.calls == 1


# --------------------------------------------------------------------------- SQL


@pytest.mark.db
def test_the_replacement_writes_updates_and_retires_in_one_pass(
    migrated: sa.Engine, database_url: str, minimal_settings: Settings
) -> None:
    repo = repo_for(minimal_settings, database_url)

    async def scenario():
        first = await repo.replace_all(
            [
                PosShopItem(pos_id=SHOP_A, is_active=True),
                PosShopItem(pos_id=SHOP_B, is_active=True),
                PosShopItem(pos_id=ARTRUTX, is_active=False),
            ],
            refreshed_at=REFRESHED,
        )
        # SHOP_B leaves the business, ARTRUTX reopens, SHOP_C appears.
        second = await repo.replace_all(
            [
                PosShopItem(pos_id=SHOP_A, is_active=True),
                PosShopItem(pos_id=ARTRUTX, is_active=True),
                PosShopItem(pos_id=SHOP_C, is_active=False),
            ],
            refreshed_at=REFRESHED,
        )
        return (
            first,
            second,
            await repo.count(),
            await repo.get(SHOP_B),
            await repo.get(ARTRUTX),
        )

    first, second, count, gone, reopened = run_db(scenario)

    assert first == (3, 0)
    assert second == (3, 1)
    assert count == 3
    assert gone is None, "a shop absent from the reading must leave the table"
    assert reopened is not None and reopened.is_active is True


@pytest.mark.db
def test_the_replacement_is_idempotent(
    migrated: sa.Engine, database_url: str, minimal_settings: Settings
) -> None:
    repo = repo_for(minimal_settings, database_url)
    items = [PosShopItem(pos_id=SHOP_A, is_active=True)]

    async def scenario():
        await repo.replace_all(items, refreshed_at=REFRESHED)
        await repo.replace_all(items, refreshed_at=REFRESHED)
        return await repo.count(), await repo.get(SHOP_A)

    count, row = run_db(scenario)

    assert count == 1
    assert row is not None and row.is_active is True


@pytest.mark.db
def test_an_empty_reading_empties_the_table_rather_than_keeping_a_stale_one(
    migrated: sa.Engine, database_url: str, minimal_settings: Settings
) -> None:
    """Deliberate. An environment with no trading shop must fail verification loudly.

    Keeping the previous reading would turn a correct, loud failure into a stale table that
    nobody questions — which is the shape of every finding this series has cost a session.
    """
    repo = repo_for(minimal_settings, database_url)

    async def scenario():
        await repo.replace_all(
            [PosShopItem(pos_id=SHOP_A, is_active=True)], refreshed_at=REFRESHED
        )
        removed = await repo.replace_all([], refreshed_at=REFRESHED)
        return removed, await repo.count()

    removed, count = run_db(scenario)

    assert removed == (0, 1)
    assert count == 0


@pytest.mark.db
def test_a_failed_replacement_leaves_the_previous_reading_intact(
    migrated: sa.Engine,
    database_url: str,
    minimal_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One transaction, and this is the invariant that needs a database to prove.

    The dangerous half is the **delete**: committed without its insert it would leave the
    table empty, and an empty `ai.pos_shop` is a state post-deployment verification is
    specified to fail on. So the failure is forced precisely there — the upsert succeeds, the
    delete blows up — and what must survive is the *previous* reading: not the new rows, and
    above all not an empty table.

    A duplicate identifier was tried first and proved nothing: SQLAlchemy sends the reading as
    an executemany, so the second row simply updates the first and the write succeeds.
    """
    repo = repo_for(minimal_settings, database_url)

    async def scenario():
        await repo.replace_all(
            [
                PosShopItem(pos_id=SHOP_A, is_active=True),
                PosShopItem(pos_id=SHOP_B, is_active=True),
            ],
            refreshed_at=REFRESHED,
        )

        monkeypatch.setattr(
            pos_shop_module,
            "_DELETE_MISSING_SQL",
            sa.text("DELETE FROM ai.pos_shop WHERE no_such_column = :keep"),
        )
        try:
            await repo.replace_all(
                [PosShopItem(pos_id=SHOP_C, is_active=True)], refreshed_at=REFRESHED
            )
        except Exception:  # noqa: BLE001 — the point is what survives it
            pass
        monkeypatch.undo()

        return await repo.count(), await repo.get(SHOP_A), await repo.get(SHOP_C)

    count, survivor, never_written = run_db(scenario)

    assert count == 2, "the previous reading survives a failed replacement"
    assert survivor is not None, "and it is the previous reading, not an empty table"
    assert never_written is None, "the upsert rolled back with the delete"


@pytest.mark.db
def test_the_count_reads_only_schema_ai(
    migrated: sa.Engine, database_url: str, minimal_settings: Settings
) -> None:
    """The boundary this whole design exists to respect: `jbg_ai` cannot read `public`."""
    repo = repo_for(minimal_settings, database_url)

    async def scenario():
        await repo.replace_all(
            [PosShopItem(pos_id=SHOP_A, is_active=True)], refreshed_at=REFRESHED
        )
        return await repo.count()

    assert run_db(scenario) == 1

    # Every statement this module issues, read from the module itself. The role `jbg_ai` is
    # refused `SELECT` on `public."PointOfSales"`, so a statement naming it would not fail
    # here — the test database runs as the owner — it would fail in the deployed environment
    # only, which is the worst place to find out.
    statements = [
        str(sql)
        for name, sql in vars(pos_shop_module).items()
        if name.endswith("_SQL")
    ]
    assert statements, "the module is expected to declare its statements as module globals"
    for statement in statements:
        assert "public" not in statement, statement
        assert "ai." in statement, statement
