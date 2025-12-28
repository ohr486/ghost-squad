"""Database models package."""
from models.database.base import Base, BaseModel
from models.database.inquiry import InquiryModel

__all__ = ["Base", "BaseModel", "InquiryModel"]
