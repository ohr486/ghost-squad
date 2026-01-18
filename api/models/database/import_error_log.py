"""インポートエラーログモデル."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import BaseModel


class ImportErrorLogModel(BaseModel):
    """インポートエラーログモデル.

    Importer機能で発生したエラーを記録するためのモデル。
    エラー種別ごとの統計情報や、リトライ対象の特定に使用する。
    """

    __tablename__ = "import_error_logs"

    error_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="エラーコード（GS-301〜GS-399）",
    )
    plugin_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="データソースプラグイン種別（email, sentry等）",
    )
    source_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="外部システムのID（Message-ID等）",
    )
    error_message: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="エラーメッセージ",
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="エラー発生日時",
    )
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="解決済みフラグ（リトライ成功時にTrue）",
    )

    __table_args__ = (
        Index("ix_import_error_logs_code_occurred", "error_code", "occurred_at"),
        Index("ix_import_error_logs_plugin", "plugin_type"),
        Index("ix_import_error_logs_resolved", "resolved"),
    )

    def __repr__(self) -> str:
        """文字列表現を返す."""
        return (
            f"<ImportErrorLogModel("
            f"id={self.id}, "
            f"error_code='{self.error_code}', "
            f"plugin_type='{self.plugin_type}', "
            f"resolved={self.resolved})>"
        )
