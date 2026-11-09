"""phone number added

Revision ID: d899796fe1a5
Revises: 0001_initial
Create Date: 2025-03-07 13:11:46.387506
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d899796fe1a5"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("phone_number")
