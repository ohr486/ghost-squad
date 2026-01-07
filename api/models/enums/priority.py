"""優先度列挙型."""
from enum import Enum


class Priority(str, Enum):
    """ストーリー優先度."""

    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    URGENT = "urgent"  # 緊急
