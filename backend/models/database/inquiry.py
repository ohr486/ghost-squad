"""
Inquiry database model
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..enums import InquiryStatus
from .base import Base


class InquiryModel(Base):
    __tablename__ = "inquiries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(2), nullable=False, default="ja")
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), nullable=False, default=InquiryStatus.RECEIVED.value)
    inquiry_metadata = Column(
        JSON, nullable=True
    )  # Renamed to avoid SQLAlchemy conflict

    # Relationships
    stories = relationship(
        "StoryModel", back_populates="inquiry", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Inquiry(id={self.id}, user_id={self.user_id}, status={self.status})>"
