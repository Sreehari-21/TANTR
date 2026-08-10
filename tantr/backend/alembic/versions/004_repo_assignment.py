"""Add per-repo assignment brief and rubric weights.

Revision ID: 004_repo_assignment
Revises: 003_custom_vcs
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_repo_assignment"
down_revision: Union[str, None] = "003_custom_vcs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("repositories")}
    if "assignment_title" not in cols:
        op.add_column("repositories", sa.Column("assignment_title", sa.String(length=255), nullable=True))
    if "assignment_brief" not in cols:
        op.add_column("repositories", sa.Column("assignment_brief", sa.Text(), nullable=True))
    if "rubric_weights" not in cols:
        op.add_column("repositories", sa.Column("rubric_weights", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("repositories")}
    if "rubric_weights" in cols:
        op.drop_column("repositories", "rubric_weights")
    if "assignment_brief" in cols:
        op.drop_column("repositories", "assignment_brief")
    if "assignment_title" in cols:
        op.drop_column("repositories", "assignment_title")
