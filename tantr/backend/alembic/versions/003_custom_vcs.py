"""Custom VCS tables + widen commit sha / add HEAD.

Revision ID: 003_custom_vcs
Revises: 002_is_admin
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_custom_vcs"
down_revision: Union[str, None] = "002_is_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if "vcs_objects" not in insp.get_table_names():
        op.create_table(
            "vcs_objects",
            sa.Column("sha", sa.String(length=64), nullable=False),
            sa.Column("kind", sa.String(length=16), nullable=False),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("sha"),
        )
        op.create_index("ix_vcs_objects_kind", "vcs_objects", ["kind"])
        op.create_index("ix_vcs_objects_kind_sha", "vcs_objects", ["kind", "sha"])

    repo_cols = {c["name"] for c in insp.get_columns("repositories")}
    if "head_sha" not in repo_cols:
        op.add_column("repositories", sa.Column("head_sha", sa.String(length=64), nullable=True))
        op.create_index("ix_repositories_head_sha", "repositories", ["head_sha"])

    commit_cols = {c["name"]: c for c in insp.get_columns("commits")}
    if "tree_sha" not in commit_cols:
        op.add_column("commits", sa.Column("tree_sha", sa.String(length=64), nullable=True))
    if "parent_sha" not in commit_cols:
        op.add_column("commits", sa.Column("parent_sha", sa.String(length=64), nullable=True))

    # Widen sha if needed (SQLite may ignore ALTER type; best-effort)
    dialect = bind.dialect.name
    if dialect != "sqlite" and "sha" in commit_cols:
        op.alter_column("commits", "sha", existing_type=sa.String(40), type_=sa.String(64), existing_nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    commit_cols = {c["name"] for c in insp.get_columns("commits")}
    if "parent_sha" in commit_cols:
        op.drop_column("commits", "parent_sha")
    if "tree_sha" in commit_cols:
        op.drop_column("commits", "tree_sha")
    repo_cols = {c["name"] for c in insp.get_columns("repositories")}
    if "head_sha" in repo_cols:
        op.drop_index("ix_repositories_head_sha", table_name="repositories")
        op.drop_column("repositories", "head_sha")
    if "vcs_objects" in insp.get_table_names():
        op.drop_index("ix_vcs_objects_kind_sha", table_name="vcs_objects")
        op.drop_index("ix_vcs_objects_kind", table_name="vcs_objects")
        op.drop_table("vcs_objects")
