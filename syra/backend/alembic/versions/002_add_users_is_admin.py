"""Add users.is_admin for dev DBs created before Alembic.

Revision ID: 002_is_admin
Revises: 001_initial
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_is_admin"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "is_admin" not in cols:
        op.add_column(
            "users",
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "is_admin" in cols:
        op.drop_column("users", "is_admin")
