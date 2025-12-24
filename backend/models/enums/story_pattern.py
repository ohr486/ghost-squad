"""
Story pattern enumeration for template matching (renamed from TaskPattern)
"""
from enum import Enum


class StoryPattern(str, Enum):
    BUG_FIX = "bug_fix"
    FEATURE_ADDITION = "feature_addition"
    INVESTIGATION = "investigation"
    REVIEW = "review"
    MAINTENANCE = "maintenance"
