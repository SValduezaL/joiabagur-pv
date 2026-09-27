"""pos_shop: the activity of every point of sale, inside schema `ai`

One table (C43). Hand-written like every revision here; do not autogenerate — C05
left HNSW/GIN indexes and generated columns that autogen would rewrite.

Additive: one new table in schema `ai`, nothing existing altered. The downgrade drops
exactly it and leaves no trace, which it can only do because no enumerated type is
created — the same reason the foundation revision records.

**Why a table and not a column on `ai.pos_projection`.** The obvious place for "is this
shop still trading" is beside the assortment, and it is the wrong place. The POS
availability feed is incremental by keyset over the watermark of the inventory row, and
a point of sale changing its activity **touches no inventory row**: the watermark does
not move, the incremental pass re-emits nothing, and the column would keep the value it
held the day the assignment last changed — for ever. The aggregate hash cannot see it
either, being a digest of `(pointOfSaleId, productId)` pairs. A separate table fed by a
complete reading has no such failure mode, because every drain states the whole set.

**Why `pos_id` alone is the key.** One row per point of sale is the whole point: the
count this table serves asks "how many active shops hold no assortment", and a shape
that allowed two rows for one shop would let that question have two answers.

**What is deliberately absent.** No code, no name, no address. This table records
activity and nothing else: the count counts and does not name, and `public` remains the
authority on every descriptive attribute of a point of sale. Copying one here would put
a second copy of a business fact inside the AI schema, which is the coupling the schema
boundary exists to prevent — and it would go stale between drains with nobody watching.

**No foreign key on `pos_id`.** Same boundary as `ai.pos_projection` and
`ai.product_document`: the identifier is assigned by the .NET side, the two schemas are
owned by different services, and a key across that line would make a business-side
delete fail on an AI-side row.

Revision ID: e2f81a6c4b93
Revises: d7c4e91b25a0
Create Date: 2026-09-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e2f81a6c4b93"
down_revision: str | None = "d7c4e91b25a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

AI = "ai"


def upgrade() -> None:
    op.create_table(
        "pos_shop",
        # Assigned by the .NET side. No foreign key by design — see the module docstring.
        sa.Column("pos_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        # NOT NULL with no default: every row comes from a reading that stated the value,
        # and a default would let a half-written row claim a shop is open when nobody said so.
        sa.Column("is_active", sa.Boolean(), nullable=False),
        # When the drain last wrote this row. Unlike `ai.pos_projection.refreshed_at` this
        # one does mean "when the projection was last looked at", because this feed is a
        # complete reading rather than an incremental one: every drain rewrites every row.
        sa.Column(
            "refreshed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema=AI,
    )

    # The count reads active shops and nothing else, so the index carries exactly that
    # predicate. Partial rather than plain: with twelve rows it changes no plan today, and
    # it states in the schema which subset the table exists to be asked about.
    op.create_index(
        "ix_pos_shop_active",
        "pos_shop",
        ["pos_id"],
        unique=False,
        schema=AI,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index("ix_pos_shop_active", table_name="pos_shop", schema=AI)
    op.drop_table("pos_shop", schema=AI)
