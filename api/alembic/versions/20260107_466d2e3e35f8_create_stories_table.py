"""create stories table

Revision ID: 466d2e3e35f8
Revises: 09ab3b97
Create Date: 2026-01-07 17:16:57.183334

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "466d2e3e35f8"
down_revision: Union[str, None] = "09ab3b97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create stories table with all columns, constraints, and indexes."""
    # Create enum types for Priority and StoryStatus
    priority_enum = sa.Enum(
        "low",
        "medium",
        "high",
        "urgent",
        name="priority",
    )

    story_status_enum = sa.Enum(
        "waiting_review",
        "approved",
        "rejected",
        name="storystatus",
    )

    # Create stories table
    op.create_table(
        "stories",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("inquiry_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            priority_enum,
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            story_status_enum,
            nullable=False,
            server_default="waiting_review",
        ),
        sa.Column("estimated_effort", sa.Float(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assignee", sa.String(length=50), nullable=True),
        sa.Column(
            "story_metadata",
            sa.JSON(),
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
        sa.ForeignKeyConstraint(
            ["inquiry_id"],
            ["inquiries.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "length(trim(title)) > 0 AND length(title) <= 500",
            name="chk_stories_title",
        ),
        sa.CheckConstraint(
            "length(trim(description)) > 0",
            name="chk_stories_description",
        ),
    )

    # Create indexes
    op.create_index("ix_stories_inquiry_id", "stories", ["inquiry_id"])
    op.create_index("ix_stories_status", "stories", ["status"])
    op.create_index("ix_stories_priority", "stories", ["priority"])
    op.create_index("ix_stories_created_at", "stories", ["created_at"])


def downgrade() -> None:
    """Drop stories table, indexes, and enum types."""
    # Drop indexes first
    op.drop_index("ix_stories_created_at", table_name="stories")
    op.drop_index("ix_stories_priority", table_name="stories")
    op.drop_index("ix_stories_status", table_name="stories")
    op.drop_index("ix_stories_inquiry_id", table_name="stories")

    # Drop table
    op.drop_table("stories")

    # Explicitly drop enum types to ensure cleanup
    sa.Enum(name="storystatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="priority").drop(op.get_bind(), checkfirst=True)
