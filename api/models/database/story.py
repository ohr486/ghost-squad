"""ストーリーモデル."""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (JSON, CheckConstraint, DateTime, Enum, Float,
                        ForeignKey, Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import BaseModel
from models.enums.priority import Priority
from models.enums.story_status import StoryStatus


class StoryModel(BaseModel):
    """ストーリーエンティティ.

    問い合わせからAIを活用して構造化されたユーザーストーリーを表現する。
    """

    __tablename__ = "stories"

    # 外部キー（必須、すべてのストーリーは問い合わせと関連付けられる）
    inquiry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inquiries.id"), nullable=False, index=True
    )

    # 必須フィールド
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Priority.MEDIUM,
        server_default=Priority.MEDIUM.value,
        index=True,
    )
    status: Mapped[StoryStatus] = mapped_column(
        Enum(StoryStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=StoryStatus.WAITING_REVIEW,
        server_default=StoryStatus.WAITING_REVIEW.value,
        index=True,
    )

    # オプショナルフィールド
    estimated_effort: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assignee: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # JSON拡張フィールド
    story_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=lambda: {}
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) > 0 AND length(title) <= 500",
            name="chk_stories_title",
        ),
        CheckConstraint(
            "length(trim(description)) > 0",
            name="chk_stories_description",
        ),
    )

    def __repr__(self) -> str:
        """文字列表現."""
        return (
            f"<StoryModel(id={self.id}, inquiry_id={self.inquiry_id}, "
            f"status='{self.status.value}')>"
        )
