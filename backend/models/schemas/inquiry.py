"""
Inquiry Pydantic schemas
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..enums import InquiryStatus

if TYPE_CHECKING:
    from .story import Story


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
    generated_stories: Optional[List["Story"]] = None
    clarification_questions: Optional[List[str]] = None
