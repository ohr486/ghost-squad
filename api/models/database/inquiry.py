"""問い合わせモデル."""
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, CheckConstraint, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.database.base import BaseModel
from models.enums.inquiry_status import InquiryStatus


class InquiryModel(BaseModel):
    """問い合わせエンティティ.

    報告者からの自然言語による問い合わせを表現する。
    """

    __tablename__ = "inquiries"

    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[InquiryStatus] = mapped_column(
        Enum(InquiryStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=InquiryStatus.RECEIVED,
        server_default=InquiryStatus.RECEIVED.value,
        index=True,
    )
    inquiry_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=False,
        default=lambda: {},
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(content)) > 0",
            name="chk_inquiries_content_not_empty",
        ),
    )

    def __repr__(self) -> str:
        """文字列表現."""
        return (
            f"<InquiryModel(id={self.id}, user_id='{self.user_id}', "
            f"status='{self.status.value}')>"
        )
