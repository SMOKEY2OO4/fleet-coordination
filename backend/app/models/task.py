
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskCreate(BaseModel):
    start_node: str = Field(min_length=1)
    destination_node: str = Field(min_length=1)


class Task(BaseModel):
    task_id: str
    start_node: str
    destination_node: str
    status: TaskStatus = TaskStatus.QUEUED
    assigned_robot_id: str | None = None
