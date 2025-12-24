"""
Export and Kanban integration models
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    type: str = Field(..., pattern="^(api_key|oauth|basic)$")
    credentials: Dict[str, str]


class FieldMapping(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[str] = None
    assignee: Optional[str] = None


class KanbanSystem(BaseModel):
    name: str
    api_endpoint: str
    auth_config: AuthConfig
    field_mapping: FieldMapping


class ExportResult(BaseModel):
    success: bool
    exported_stories: List[str]  # Story IDs
    errors: Optional[List[str]] = None
    external_task_ids: Optional[Dict[str, str]] = None  # storyId -> externalTaskId mapping


class SyncStatus(BaseModel):
    story_id: str
    external_task_id: Optional[str] = None  # Kanban task ID
    status: str = Field(..., pattern="^(pending|synced|failed)$")
    last_sync_at: Optional[datetime] = None
    error: Optional[str] = None


class NotificationSettings(BaseModel):
    email: bool
    in_app: bool
    webhook: Optional[str] = None
    deadline_reminder: int = Field(default=1, ge=0)  # days before deadline