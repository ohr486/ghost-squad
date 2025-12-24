"""
Template Pydantic schemas
"""
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ..enums import StoryPattern


class TemplateField(BaseModel):
    name: str
    type: str = Field(..., pattern="^(text|number|date|select)$")
    required: bool
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None  # select型の場合


class StoryTemplate(BaseModel):
    id: int
    name: str
    pattern: StoryPattern
    fields: List[TemplateField]
    checklist: List[str]
    default_estimate: float
    is_custom: bool
    user_id: Optional[str] = None
