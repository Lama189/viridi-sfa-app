"""add photo_id to products

Revision ID: a8d29b37e411
Revises: 13f32943b9f2
Create Date: 2026-08-27 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8d29b37e411'
down_revision: Union[str, Sequence[str], None] = '13f32943b9f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('photo_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_products_photo_id_media_objects',
        'products',
        'media_objects',
        ['photo_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_products_photo_id_media_objects',
        'products',
        type_='foreignkey',
    )
    op.drop_column('products', 'photo_id')
