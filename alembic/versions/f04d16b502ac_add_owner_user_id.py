"""add owner_user_id

Revision ID: f04d16b502ac
Revises: 50a21eb72e60
Create Date: 2026-07-17 05:56:29.363161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as postgresql


# revision identifiers, used by Alembic.
revision: str = 'f04d16b502ac'
down_revision: Union[str, Sequence[str], None] = '50a21eb72e60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "retail_points",
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_retail_points_owner_user_id",
        "retail_points",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_retail_points_owner_user_id",
        "retail_points",
        ["owner_user_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
