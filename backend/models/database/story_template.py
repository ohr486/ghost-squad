"""
Story template database model (renamed from TaskTemplateModel)
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String

from .base import Base
from .types import BigIntegerID


class StoryTemplateModel(Base):
    __tablename__ = "story_templates"

    id = Column(BigIntegerID(), primary_key=True, autoincrement=True)  # type: ignore
    name = Column(String(255), nullable=False)
    pattern = Column(String(50), nullable=False)
    fields = Column(
        JSON, nullable=False, default=list, server_default="[]"
    )  # List[TemplateField]
    checklist = Column(
        JSON, nullable=False, default=list, server_default="[]"
    )  # List[str]
    default_estimate = Column(Float, nullable=False)
    is_custom = Column(Boolean, nullable=False, default=False)
    user_id = Column(String(255), nullable=True)  # カスタムテンプレートの場合
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return (
            f"<StoryTemplate(id={self.id}, name={self.name}, pattern={self.pattern})>"
        )
