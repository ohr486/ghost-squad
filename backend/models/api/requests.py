"""
API request models
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..enums import Priority, StoryCategory


class InquiryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    language: str = Field(default="ja", pattern="^(ja|en)$")
    user_id: str = Field(..., min_length=1)


class StoryUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[StoryCategory] = None
    priority: Optional[Priority] = None
    estimated_effort: Optional[float] = Field(None, gt=0)
    deadline: Optional[datetime] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class RejectRequest(BaseModel):
    reason: Optional[str] = None
