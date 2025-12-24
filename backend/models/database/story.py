"""
Story database model (renamed from TaskModel to avoid confusion with Kanban tasks)
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..enums import StoryStatus
from .base import Base


class StoryModel(Base):
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inquiry_id = Column(UUID(as_uuid=True), ForeignKey("inquiries.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    estimated_effort = Column(Float, nullable=False)  # 時間単位
    deadline = Column(DateTime, nullable=True)
    status = Column(
        String(50), nullable=False, default=StoryStatus.PENDING_REVIEW.value
    )
    assignee = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True, default=list)  # List[str]
    dependencies = Column(JSON, nullable=True, default=list)  # List[str] - 他のストーリーID
    story_metadata = Column(
        JSON, nullable=False
    )  # Renamed to avoid SQLAlchemy conflict
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    inquiry = relationship("InquiryModel", back_populates="stories")
    
    # Test field for migration
    # comments = Column(Text, nullable=True)  # Uncomment to test migrations

    def __repr__(self):
        return f"<Story(id={self.id}, title={self.title}, status={self.status})>"
