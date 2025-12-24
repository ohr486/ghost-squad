"""
Inquiry database model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base
from ..enums import InquiryStatus


class InquiryModel(Base):
    __tablename__ = "inquiries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(2), nullable=False, default="ja")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default=InquiryStatus.RECEIVED.value)
    inquiry_metadata = Column(JSON, nullable=True)  # Renamed to avoid SQLAlchemy conflict
    
    # Relationships
    stories = relationship("StoryModel", back_populates="inquiry", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Inquiry(id={self.id}, user_id={self.user_id}, status={self.status})>"