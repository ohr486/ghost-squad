"""
Service interface protocols
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from ..api import StoryUpdateRequest
from ..enums import StoryCategory, StoryPattern
from ..export import (ExportResult, KanbanSystem, NotificationSettings,
                      SyncStatus)
from ..schemas import Inquiry, InquiryResult, Story


class InquiryServiceProtocol(Protocol):
    async def submit_inquiry(self, inquiry: str, user_id: str) -> InquiryResult:
        ...

    async def get_inquiry_history(self, user_id: str) -> List[Inquiry]:
        ...

    async def request_clarification(
        self, inquiry_id: str, questions: List[str]
    ) -> None:
        ...

    async def update_inquiry_status(self, inquiry_id: str) -> None:
        ...

    async def check_story_completion(self, inquiry_id: str) -> bool:
        ...


class StoryConverterProtocol(Protocol):
    async def convert_to_stories(self, inquiry: Inquiry) -> List[Story]:
        ...

    async def extract_deadlines(self, inquiry: str) -> Optional[datetime]:
        ...

    async def categorize_story(self, story_description: str) -> StoryCategory:
        ...

    async def estimate_effort(self, story_description: str) -> float:
        ...


class PatternRecognizerProtocol(Protocol):
    async def identify_pattern(self, story_description: str) -> StoryPattern:
        ...

    async def apply_template(self, pattern: StoryPattern, story: Story) -> Story:
        ...

    async def learn_from_history(self, stories: List[Story]) -> None:
        ...


class StoryServiceProtocol(Protocol):
    async def get_pending_stories(self, user_id: str) -> List[Story]:
        ...

    async def update_story(self, story_id: str, updates: StoryUpdateRequest) -> Story:
        ...

    async def approve_story(self, story_id: str) -> None:
        ...

    async def reject_story(self, story_id: str, reason: Optional[str] = None) -> None:
        ...

    async def batch_approve(self, story_ids: List[str]) -> None:
        ...

    async def get_story_history(
        self, story_id: str
    ) -> List[Dict[str, Any]]:  # StoryVersion
        ...


class ExportServiceProtocol(Protocol):
    async def export_to_kanban(
        self, stories: List[Story], target_system: KanbanSystem
    ) -> ExportResult:
        ...

    def get_supported_systems(self) -> List[KanbanSystem]:
        ...

    async def track_sync_status(self, story_id: str) -> SyncStatus:
        ...


class NotificationServiceProtocol(Protocol):
    async def send_story_completion_notification(
        self, user_id: str, stories: List[Story]
    ) -> None:
        ...

    async def send_error_alert(self, user_id: str, error: Exception) -> None:
        ...

    async def send_deadline_reminder(self, user_id: str, stories: List[Story]) -> None:
        ...

    async def configure_notification_settings(
        self, user_id: str, settings: NotificationSettings
    ) -> None:
        ...
