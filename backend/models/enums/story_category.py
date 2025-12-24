"""
Story category enumeration.

Renamed from TaskCategory to avoid confusion with Kanban tasks.
"""
from enum import Enum


class StoryCategory(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"
