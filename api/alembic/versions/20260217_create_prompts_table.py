"""create prompts table

Revision ID: 8b2c3d4e5f6a
Revises: 7a1b2c3d4e5f
Create Date: 2026-02-17 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b2c3d4e5f6a"
down_revision: Union[str, None] = "7a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create prompts table with all columns and indexes."""
    # Create promptcategory enum type
    promptcategory_enum = sa.Enum(
        "story_generation", "import_analysis", "general",
        name="promptcategory",
    )

    # Create prompts table
    op.create_table(
        "prompts",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column(
            "key",
            sa.String(length=100),
            nullable=False,
            comment="プロンプト一意識別子キー",
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
            comment="プロンプト表示名",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="プロンプト説明",
        ),
        sa.Column(
            "category",
            promptcategory_enum,
            nullable=False,
            comment="プロンプトカテゴリ",
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="現在のプロンプト本文",
        ),
        sa.Column(
            "default_content",
            sa.Text(),
            nullable=False,
            comment="デフォルトプロンプト本文",
        ),
        sa.Column(
            "variables",
            sa.JSON(),
            nullable=False,
            server_default="[]",
            comment="プレースホルダー変数リスト（JSON配列）",
        ),
        sa.Column(
            "is_modified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="デフォルトから変更されているか",
        ),
        sa.Column(
            "editing_by",
            sa.String(length=100),
            nullable=True,
            comment="編集中ユーザーID",
        ),
        sa.Column(
            "editing_since",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="編集開始日時",
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
    )

    # Create indexes
    op.create_index(
        "ix_prompts_key",
        "prompts",
        ["key"],
        unique=True,
    )
    op.create_index(
        "ix_prompts_category",
        "prompts",
        ["category"],
    )


def downgrade() -> None:
    """Drop prompts table and indexes."""
    # Drop indexes first
    op.drop_index("ix_prompts_category", table_name="prompts")
    op.drop_index("ix_prompts_key", table_name="prompts")

    # Drop table
    op.drop_table("prompts")

    # Drop enum type
    sa.Enum(name="promptcategory").drop(op.get_bind(), checkfirst=True)
