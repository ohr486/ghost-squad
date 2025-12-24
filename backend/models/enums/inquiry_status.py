"""
Inquiry status enumeration
"""
from enum import Enum


class InquiryStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    NEEDS_CLARIFICATION = "needs_clarification"
    TASK_WORKING = "task_working"
    COMPLETED = "completed"
    FAILED = "failed"