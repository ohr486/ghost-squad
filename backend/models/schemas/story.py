"""
Story Pydantic schemas (renamed from Task to avoid confusion with Kanban tasks)
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..enums import Priority, StoryCategory, StoryStatus


class StoryMetadata(BaseModel):
    original_inquiry: str
    generation_log: List[str]
    applied_template: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)  # 0-1
    review_notes: Optional[List[str]] = None


class Story(BaseModel):
    id: str
    inquiry_id: str
    title: str
    description: str
    category: StoryCategory
    priority: Priority
    estimated_effort: float  # 時間単位
    deadline: Optional[datetime] = None
    status: StoryStatus
    assignee: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)  # 他のストーリーID
    metadata: StoryMetadata
    created_at: datetime
    updated_at: datetime
