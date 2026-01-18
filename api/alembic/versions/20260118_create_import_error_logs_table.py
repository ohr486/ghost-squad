"""create import_error_logs table

Revision ID: 7a1b2c3d4e5f
Revises: 466d2e3e35f8
Create Date: 2026-01-18 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a1b2c3d4e5f"
down_revision: Union[str, None] = "466d2e3e35f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create import_error_logs table with all columns and indexes."""
    # Create import_error_logs table
    op.create_table(
        "import_error_logs",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column(
            "error_code",
            sa.String(length=10),
            nullable=False,
            comment="エラーコード（GS-301〜GS-399）",
        ),
        sa.Column(
            "plugin_type",
            sa.String(length=50),
            nullable=False,
            comment="データソースプラグイン種別（email, sentry等）",
        ),
        sa.Column(
            "source_id",
            sa.String(length=255),
            nullable=True,
            comment="外部システムのID（Message-ID等）",
        ),
        sa.Column(
            "error_message",
            sa.String(length=1000),
            nullable=False,
            comment="エラーメッセージ",
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="エラー発生日時",
        ),
        sa.Column(
            "resolved",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="解決済みフラグ（リトライ成功時にTrue）",
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

    # Create indexes for efficient querying
    op.create_index(
        "ix_import_error_logs_code_occurred",
        "import_error_logs",
        ["error_code", "occurred_at"],
    )
    op.create_index(
        "ix_import_error_logs_plugin",
        "import_error_logs",
        ["plugin_type"],
    )
    op.create_index(
        "ix_import_error_logs_resolved",
        "import_error_logs",
        ["resolved"],
    )


def downgrade() -> None:
    """Drop import_error_logs table and indexes."""
    # Drop indexes first
    op.drop_index("ix_import_error_logs_resolved", table_name="import_error_logs")
    op.drop_index("ix_import_error_logs_plugin", table_name="import_error_logs")
    op.drop_index("ix_import_error_logs_code_occurred", table_name="import_error_logs")

    # Drop table
    op.drop_table("import_error_logs")
