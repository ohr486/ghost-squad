"""
Story status enumeration (renamed from TaskStatus to avoid confusion with Kanban tasks)
"""
from enum import Enum


class StoryStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    EXPORTED = "exported"
    REJECTED = "rejected"