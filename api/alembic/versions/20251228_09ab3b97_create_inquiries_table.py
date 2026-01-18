"""create inquiries table

Revision ID: 09ab3b97
Revises:
Create Date: 2025-12-28 14:14:18.990627

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "09ab3b97"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create inquiries table with all columns and constraints."""
    # Create enum type for InquiryStatus
    # Note: SQLAlchemy automatically creates the enum type when creating the table
    # So we define it here but don't explicitly create it
    inquiry_status_enum = sa.Enum(
        "received",
        "processing",
        "needs_clarification",
        "task_working",
        "completed",
        "rejected",
        "failed",
        name="inquirystatus",
    )

    # Create inquiries table
    op.create_table(
        "inquiries",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            inquiry_status_enum,
            nullable=False,
            server_default="received",
        ),
        sa.Column(
            "inquiry_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "length(trim(content)) > 0",
            name="chk_inquiries_content_not_empty",
        ),
    )

    # Create indexes
    op.create_index("ix_inquiries_user_id", "inquiries", ["user_id"])
    op.create_index("ix_inquiries_status", "inquiries", ["status"])
    op.create_index("ix_inquiries_created_at", "inquiries", ["created_at"])

    # Create GIN index for importer duplicate check optimization
    # This index speeds up queries like:
    # SELECT id FROM inquiries
    # WHERE inquiry_metadata->'importer'->>'source_type' = 'email'
    #   AND inquiry_metadata->'importer'->>'source_id' = 'message-id-xxx';
    op.create_index(
        "ix_inquiries_importer_source",
        "inquiries",
        [sa.text("(inquiry_metadata->'importer')")],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Drop inquiries table and enum type."""
    # Drop indexes first (in reverse order of creation)
    op.drop_index("ix_inquiries_importer_source", table_name="inquiries")
    op.drop_index("ix_inquiries_created_at", table_name="inquiries")
    op.drop_index("ix_inquiries_status", table_name="inquiries")
    op.drop_index("ix_inquiries_user_id", table_name="inquiries")

    # Drop table (SQLAlchemy will automatically drop the enum type)
    op.drop_table("inquiries")

    # Explicitly drop enum type to ensure cleanup
    sa.Enum(name="inquirystatus").drop(op.get_bind(), checkfirst=True)
