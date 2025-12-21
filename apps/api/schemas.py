from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TaskUpdate(BaseModel):
    status: str


class TaskSchema(BaseModel):
    id: str
    title: str
    status: str
    assignee: Optional[str] = None
    energy: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class MissionRequest(BaseModel):
    instruction: str


class MissionResponse(BaseModel):
    mission_id: str
    status: str
    logs: List[str]
    energy_used: float = 0.0
    tasks: List[TaskSchema] = []  # Use TaskSchema here

    model_config = ConfigDict(from_attributes=True)


class MissionSchema(BaseModel):
    id: str
    instruction: str
    status: str
    logs: List[str] = []
    created_at: Optional[datetime] = None
    tasks: List[TaskSchema] = []

    model_config = ConfigDict(from_attributes=True)


class PlanSchema(BaseModel):  # Moved from graph.py
    tasks: List[TaskSchema]
