"""
API response models
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..enums import InquiryStatus, Priority, StoryCategory, StoryStatus
from ..schemas import StoryMetadata


class InquiryResponse(BaseModel):
    id: int
    user_id: str
    content: str
    language: str
    timestamp: datetime
    status: InquiryStatus
    metadata: Dict[str, Any]


class StoryResponse(BaseModel):
    id: int
    inquiry_id: int
    title: str
    description: str
    category: StoryCategory
    priority: Priority
    estimated_effort: float
    deadline: Optional[datetime] = None
    status: StoryStatus
    assignee: Optional[str] = None
    tags: List[str]
    dependencies: List[int]
    metadata: StoryMetadata
    created_at: datetime
    updated_at: datetime


class StoryGenerationResponse(BaseModel):
    inquiry_id: int
    stories: List[StoryResponse]
    status: str = Field(..., pattern="^(success|partial|failed)$")
    message: Optional[str] = None


class GenerationStatusResponse(BaseModel):
    inquiry_id: int
    status: str = Field(..., pattern="^(processing|completed|failed)$")
    progress: int = Field(..., ge=0, le=100)
    message: Optional[str] = None
