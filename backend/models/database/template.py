"""
Story template database model (renamed from TaskTemplateModel)
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class StoryTemplateModel(Base):
    __tablename__ = "story_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    pattern = Column(String(50), nullable=False)
    fields = Column(JSON, nullable=False)  # List[TemplateField]
    checklist = Column(JSON, nullable=False, default=list)  # List[str]
    default_estimate = Column(Float, nullable=False)
    is_custom = Column(Boolean, nullable=False, default=False)
    user_id = Column(String(255), nullable=True)  # カスタムテンプレートの場合
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<StoryTemplate(id={self.id}, name={self.name}, pattern={self.pattern})>"