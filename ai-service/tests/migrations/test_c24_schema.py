"""C24 schema: the three evaluation tables the foundation revision never created.

`GET /v1/evals/runs` has been published in the frozen contract since C02 and its stub named
C24 in writing as the change that would fill it. These tests pin what that route now reads
from, the invariants the database enforces on its own, and the reversibility that makes the
revision safe to open in a change whose ticket declares no migration.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.db

AI = "ai"
C22 = "c9a71f2b6d54"
C24 = "d7c4e91b25a0"

STARTED = datetime(2026, 9, 7, 9, 0, tzinfo=UTC)


def _columns(engine: sa.Engine, table: str) -> dict[str, sa.engine.Row]:
    with engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                """
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                """
            ),
            {"schema": AI, "table": table},
        ).all()
    return {row[0]: row for row in rows}


def _index_columns(engine: sa.Engine, table: str) -> set[tuple[str, ...]]:
    """Every index of the table as its ordered column tuple, primary keys included."""
    with engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                """
                SELECT i.relname,
                       array_agg(a.attname ORDER BY k.ord)
                FROM pg_index x
                JOIN pg_class t ON t.oid = x.indrelid
                JOIN pg_class i ON i.oid = x.indexrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN LATERAL unnest(x.indkey) WITH ORDINALITY AS k(attnum, ord) ON TRUE
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
                WHERE n.nspname = :schema AND t.relname = :table
                GROUP BY i.relname
                """
            ),
            {"schema": AI, "table": table},
        ).all()
    return {tuple(row[1]) for row in rows}


def _insert_run(connection: sa.Connection, **overrides: object) -> uuid.UUID:
    values: dict[str, object] = {
        "run_id": uuid.uuid4(),
        "config_id": "v2-hibrido",
        "golden_set_version": "1",
        "index_set_hash": "0" * 64,
        "embedding_model_version_key": "openai/text-embedding-3-small:1536",
        "git_sha": "a03b4ad",
        "started_at": STARTED,
        "status": "completed",
    }
    values.update(overrides)
    columns = ", ".join(values)
    params = ", ".join(f":{name}" for name in values)
    connection.execute(
        sa.text(f"INSERT INTO ai.eval_run ({columns}) VALUES ({params})"), values
    )
    return values["run_id"]  # type: ignore[return-value]


def test_the_three_tables_exist_with_the_provenance_a_run_is_compared_by(
    migrated: sa.Engine,
) -> None:
    run = _columns(migrated, "eval_run")

    assert set(run) == {
        "run_id",
        "config_id",
        "golden_set_version",
        "index_set_hash",
        "embedding_model_version_key",
        "git_sha",
        "started_at",
        "finished_at",
        "status",
        "metrics",
        "documents_omitted",
        "notes",
    }
    assert run["metrics"].data_type == "jsonb"
    assert set(_columns(migrated, "eval_case")) == {
        "run_id",
        "query_id",
        "category",
        "in_tuning_set",
        "data_origin_bucket",
        "judged_depth",
        "metrics",
    }
    assert set(_columns(migrated, "eval_result")) == {
        "run_id",
        "query_id",
        "product_id",
        "rank",
        "score",
        "grade",
        "unjudged",
    }


def test_the_indexes_the_report_and_the_route_read_through_exist(migrated: sa.Engine) -> None:
    assert {("config_id",), ("started_at",)} <= _index_columns(migrated, "eval_run")
    assert ("run_id", "query_id") in _index_columns(migrated, "eval_case")
    assert ("run_id", "query_id", "rank") in _index_columns(migrated, "eval_result")


def test_a_lexical_baseline_records_no_embedding_model_and_that_is_a_value(
    migrated: sa.Engine,
) -> None:
    """NULL means "does not depend on the embedder", never "unknown"."""
    with migrated.begin() as connection:
        run_id = _insert_run(connection, config_id="v0-fts", embedding_model_version_key=None)

    with migrated.connect() as connection:
        row = connection.execute(
            sa.text(
                "SELECT embedding_model_version_key, documents_omitted, metrics "
                "FROM ai.eval_run WHERE run_id = :run_id"
            ),
            {"run_id": run_id},
        ).one()

    assert row[0] is None
    assert row[1] == 0, "zero omitted is the recorded default, not an absent value"
    assert row[2] == {}


def test_an_unknown_status_is_refused(migrated: sa.Engine) -> None:
    with pytest.raises(IntegrityError), migrated.begin() as connection:
        _insert_run(connection, status="probablemente")


def test_a_case_cannot_be_recorded_twice_for_one_run(migrated: sa.Engine) -> None:
    with migrated.begin() as connection:
        run_id = _insert_run(connection)
        connection.execute(
            sa.text(
                "INSERT INTO ai.eval_case "
                "(run_id, query_id, category, in_tuning_set, judged_depth) "
                "VALUES (:run_id, 'q07', 'descripcion-sin-anclaje', false, 40)"
            ),
            {"run_id": run_id},
        )

    with pytest.raises(IntegrityError), migrated.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO ai.eval_case "
                "(run_id, query_id, category, in_tuning_set, judged_depth) "
                "VALUES (:run_id, 'q07', 'materiales', false, 20)"
            ),
            {"run_id": run_id},
        )


def test_out_of_domain_queries_group_under_no_origin(migrated: sa.Engine) -> None:
    """They have no relevant document, so there is no origin to take a bucket from."""
    with migrated.begin() as connection:
        run_id = _insert_run(connection)
        connection.execute(
            sa.text(
                "INSERT INTO ai.eval_case "
                "(run_id, query_id, category, in_tuning_set, judged_depth, data_origin_bucket) "
                "VALUES (:run_id, 'q45', 'fuera-de-dominio', false, 20, NULL)"
            ),
            {"run_id": run_id},
        )

    with migrated.connect() as connection:
        assert (
            connection.execute(
                sa.text("SELECT data_origin_bucket FROM ai.eval_case")
            ).scalar()
            is None
        )


def test_an_invented_origin_bucket_is_refused(migrated: sa.Engine) -> None:
    with pytest.raises(IntegrityError), migrated.begin() as connection:
        run_id = _insert_run(connection)
        connection.execute(
            sa.text(
                "INSERT INTO ai.eval_case "
                "(run_id, query_id, category, in_tuning_set, judged_depth, data_origin_bucket) "
                "VALUES (:run_id, 'q01', 'materiales', false, 20, 'inventado')"
            ),
            {"run_id": run_id},
        )


def _insert_result(connection: sa.Connection, run_id: uuid.UUID, **overrides: object) -> None:
    values: dict[str, object] = {
        "run_id": run_id,
        "query_id": "q07",
        "product_id": uuid.uuid4(),
        "rank": 1,
        "score": 0.5,
        "grade": 2,
        "unjudged": False,
    }
    values.update(overrides)
    connection.execute(
        sa.text(
            "INSERT INTO ai.eval_result "
            "(run_id, query_id, product_id, rank, score, grade, unjudged) "
            "VALUES (:run_id, :query_id, :product_id, :rank, :score, :grade, :unjudged)"
        ),
        values,
    )


def test_a_graded_result_cannot_claim_to_be_unjudged(migrated: sa.Engine) -> None:
    """"Measured irrelevant" and "not measured" are different, and the database keeps them so."""
    with pytest.raises(IntegrityError), migrated.begin() as connection:
        run_id = _insert_run(connection)
        _insert_result(connection, run_id, grade=0, unjudged=True)


def test_an_unjudged_result_cannot_carry_a_grade(migrated: sa.Engine) -> None:
    with pytest.raises(IntegrityError), migrated.begin() as connection:
        run_id = _insert_run(connection)
        _insert_result(connection, run_id, grade=None, unjudged=False)


def test_an_unjudged_result_is_accepted_without_a_grade(migrated: sa.Engine) -> None:
    with migrated.begin() as connection:
        run_id = _insert_run(connection)
        _insert_result(connection, run_id, grade=None, unjudged=True)

    with migrated.connect() as connection:
        assert connection.execute(sa.text("SELECT count(*) FROM ai.eval_result")).scalar() == 1


def test_two_documents_cannot_hold_the_same_rank_position(migrated: sa.Engine) -> None:
    with pytest.raises(IntegrityError), migrated.begin() as connection:
        run_id = _insert_run(connection)
        _insert_result(connection, run_id, rank=1)
        _insert_result(connection, run_id, rank=1)


def test_deleting_a_run_takes_its_cases_and_results_with_it(migrated: sa.Engine) -> None:
    with migrated.begin() as connection:
        run_id = _insert_run(connection)
        connection.execute(
            sa.text(
                "INSERT INTO ai.eval_case "
                "(run_id, query_id, category, in_tuning_set, judged_depth) "
                "VALUES (:run_id, 'q07', 'materiales', false, 20)"
            ),
            {"run_id": run_id},
        )
        _insert_result(connection, run_id)

    with migrated.begin() as connection:
        connection.execute(
            sa.text("DELETE FROM ai.eval_run WHERE run_id = :run_id"), {"run_id": run_id}
        )

    with migrated.connect() as connection:
        assert connection.execute(sa.text("SELECT count(*) FROM ai.eval_case")).scalar() == 0
        assert connection.execute(sa.text("SELECT count(*) FROM ai.eval_result")).scalar() == 0


def test_a_case_cannot_belong_to_a_run_that_does_not_exist(migrated: sa.Engine) -> None:
    with pytest.raises(IntegrityError), migrated.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO ai.eval_case "
                "(run_id, query_id, category, in_tuning_set, judged_depth) "
                "VALUES (:run_id, 'q07', 'materiales', false, 20)"
            ),
            {"run_id": uuid.uuid4()},
        )


def test_most_recent_first_is_the_order_the_route_serves(migrated: sa.Engine) -> None:
    with migrated.begin() as connection:
        older = _insert_run(connection, config_id="v0-nombre", started_at=STARTED)
        newer = _insert_run(
            connection, config_id="v2-hibrido", started_at=STARTED + timedelta(hours=1)
        )

    with migrated.connect() as connection:
        ordered = [
            row[0]
            for row in connection.execute(
                sa.text("SELECT run_id FROM ai.eval_run ORDER BY started_at DESC")
            )
        ]

    assert ordered == [newer, older]


def test_upgrade_downgrade_is_reversible_and_leaves_no_trace(
    alembic_config: Config, database_url: str
) -> None:
    """The revision is additive, so reverting it must return the schema exactly as it was.

    **Pinned to C24 rather than to `head`, and that is the point of the test.** Reading `head`
    made this assert something it never meant: that no revision after C24 adds a table, so the
    first one that did — C43's `ai.pos_shop` — failed here with a diff about a table this file
    has no opinion about. What C24 has to guarantee is that *its own* three tables come and go
    without trace, which is exactly what upgrading to C24 and reverting to C22 measures.
    """
    command.upgrade(alembic_config, C24)
    engine = sa.create_engine(database_url)
    try:

        def tables() -> set[str]:
            with engine.connect() as connection:
                return {
                    row[0]
                    for row in connection.execute(
                        sa.text(
                            "SELECT table_name FROM information_schema.tables "
                            "WHERE table_schema = :schema"
                        ),
                        {"schema": AI},
                    )
                }

        def types() -> set[str]:
            with engine.connect() as connection:
                return {
                    row[0]
                    for row in connection.execute(
                        sa.text(
                            "SELECT t.typname FROM pg_type t "
                            "JOIN pg_namespace n ON n.oid = t.typnamespace "
                            "WHERE n.nspname = :schema AND t.typtype = 'e'"
                        ),
                        {"schema": AI},
                    )
                }

        with_c24 = tables()
        assert {"eval_run", "eval_case", "eval_result"} <= with_c24

        command.downgrade(alembic_config, C22)
        after = tables()
        assert after == with_c24 - {"eval_run", "eval_case", "eval_result"}
        assert "product_document" in after, "the C05 tables must survive the downgrade"
        assert types() == set(), "an orphaned enumerated type would break the next upgrade"

        command.upgrade(alembic_config, C24)
        assert tables() == with_c24, "re-applying must be possible after a full revert"
    finally:
        engine.dispose()
