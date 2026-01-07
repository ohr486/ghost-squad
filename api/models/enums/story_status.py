"""ストーリーステータス列挙型."""
from enum import Enum


class StoryStatus(str, Enum):
    """ストーリーステータス."""

    WAITING_REVIEW = "waiting_review"  # レビュー待ち
    APPROVED = "approved"  # 承認済み
    REJECTED = "rejected"  # 却下
