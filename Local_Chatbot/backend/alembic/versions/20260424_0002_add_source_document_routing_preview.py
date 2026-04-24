"""Add per-document routing previews for KB routing summaries."""

from alembic import op
import sqlalchemy as sa


revision = "20260424_0002"
down_revision = "20260424_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("source_documents", sa.Column("routing_preview", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("source_documents", "routing_preview")
