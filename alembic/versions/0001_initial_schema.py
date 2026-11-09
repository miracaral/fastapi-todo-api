"""initial schema: users and todos

Revision ID: 0001_initial
Revises:
Create Date: 2025-03-07 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), unique=True),
        sa.Column("username", sa.String(), unique=True),
        sa.Column("first_name", sa.String()),
        sa.Column("last_name", sa.String()),
        sa.Column("hashed_password", sa.String()),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("role", sa.String()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String()),
        sa.Column("description", sa.String()),
        sa.Column("priority", sa.Integer()),
        sa.Column("completed", sa.Boolean(), default=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_index("ix_todos_id", "todos", ["id"])


def downgrade() -> None:
    op.drop_index("ix_todos_id", table_name="todos")
    op.drop_table("todos")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
