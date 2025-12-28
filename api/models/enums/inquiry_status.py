"""問い合わせステータス列挙型."""
from enum import Enum


class InquiryStatus(str, Enum):
    """問い合わせステータス."""

    RECEIVED = "received"  # 受付済み
    PROCESSING = "processing"  # 処理中
    NEEDS_CLARIFICATION = "needs_clarification"  # 明確化要求
    TASK_WORKING = "task_working"  # タスク作業中
    COMPLETED = "completed"  # 完了
    REJECTED = "rejected"  # 却下済み
    FAILED = "failed"  # 失敗
