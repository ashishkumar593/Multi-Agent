"""Initial PostgreSQL schema for research jobs and ingested documents.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Research jobs table
    op.create_table(
        "research_jobs",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("topic", sa.String(length=512), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False, server_default="comprehensive"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("current_agent", sa.String(length=32), nullable=False, server_default="planner"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("report_title", sa.String(length=512), nullable=True),
        sa.Column("report_markdown", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_research_jobs_id", "research_jobs", ["id"])
    op.create_index("ix_research_jobs_status", "research_jobs", ["status"])

    # 2. Ingested documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("filename", sa.String(length=256), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("chunks_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_documents_id", "documents", ["id"])
    op.create_index("ix_documents_file_hash", "documents", ["file_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_documents_file_hash", table_name="documents")
    op.drop_index("ix_documents_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_research_jobs_status", table_name="research_jobs")
    op.drop_index("ix_research_jobs_id", table_name="research_jobs")
    op.drop_table("research_jobs")
