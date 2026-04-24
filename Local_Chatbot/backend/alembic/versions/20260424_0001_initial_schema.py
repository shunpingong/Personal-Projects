"""Initial relational schema for Local_Chatbot."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260424_0001"
down_revision = None
branch_labels = None
depends_on = None


message_role_enum = postgresql.ENUM(
    "user",
    "assistant",
    "system",
    name="message_role_enum",
    create_type=False,
)
document_status_enum = postgresql.ENUM(
    "processing",
    "ready",
    "failed",
    name="document_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    message_role_enum.create(bind, checkfirst=True)
    document_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "knowledge_bases",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_bases_slug"), "knowledge_bases", ["slug"], unique=True)

    op.create_table(
        "source_documents",
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=260), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=400), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("status", document_status_enum, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_documents_checksum"), "source_documents", ["checksum"], unique=False)
    op.create_index(op.f("ix_source_documents_knowledge_base_id"), "source_documents", ["knowledge_base_id"], unique=False)

    op.create_table(
        "chat_threads",
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["knowledge_bases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_threads_knowledge_base_id"), "chat_threads", ["knowledge_base_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", message_role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_thread_id"), "chat_messages", ["thread_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_messages_thread_id"), table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index(op.f("ix_chat_threads_knowledge_base_id"), table_name="chat_threads")
    op.drop_table("chat_threads")

    op.drop_index(op.f("ix_source_documents_knowledge_base_id"), table_name="source_documents")
    op.drop_index(op.f("ix_source_documents_checksum"), table_name="source_documents")
    op.drop_table("source_documents")

    op.drop_index(op.f("ix_knowledge_bases_slug"), table_name="knowledge_bases")
    op.drop_table("knowledge_bases")

    bind = op.get_bind()
    document_status_enum.drop(bind, checkfirst=True)
    message_role_enum.drop(bind, checkfirst=True)
