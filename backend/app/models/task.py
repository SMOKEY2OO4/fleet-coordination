
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskCreate(BaseModel):
    start_node: str = Field(min_length=1)
    destination_node: str = Field(min_length=1)
    priority: TaskPriority = TaskPriority.MEDIUM


class Task(BaseModel):
    task_id: str
    start_node: str
    destination_node: str
    status: TaskStatus = TaskStatus.QUEUED
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_robot_id: str | None = None
