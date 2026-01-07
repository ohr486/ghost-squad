"""Database models package."""
from models.database.base import Base, BaseModel
from models.database.inquiry import InquiryModel
from models.database.story import StoryModel

__all__ = ["Base", "BaseModel", "InquiryModel", "StoryModel"]
