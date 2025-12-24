"""
Inquiry Pydantic schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..enums import InquiryStatus


class Inquiry(BaseModel):
    id: str
    user_id: str
    content: str
    language: str = Field(default="ja", pattern="^(ja|en)$")
    timestamp: datetime
    status: InquiryStatus
    metadata: Dict[str, Any]


class InquiryResult(BaseModel):
    inquiry_id: str
    status: str = Field(
        ..., pattern="^(processing|needs_clarification|task_working|completed)$"
    )
    generated_stories: Optional[List["Story"]] = None  # Forward reference
    clarification_questions: Optional[List[str]] = None


# Import Story here to resolve forward reference
from .story import Story

InquiryResult.model_rebuild()
