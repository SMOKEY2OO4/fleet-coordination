
from enum import Enum

from pydantic import BaseModel, Field


class RobotStatus(str, Enum):
    IDLE = "IDLE"
    ASSIGNED = "ASSIGNED"
    MOVING = "MOVING"
    WAITING = "WAITING"
    CHARGING = "CHARGING"
    UNAVAILABLE = "UNAVAILABLE"
    FAULT = "FAULT"


class RobotType(str, Enum):
    SIMULATED = "SIMULATED"
    PHYSICAL = "PHYSICAL"


class RobotCreate(BaseModel):
    robot_id: str = Field(min_length=1)
    robot_type: RobotType = RobotType.SIMULATED
    current_node: str = "A"


class Robot(BaseModel):
    robot_id: str
    robot_type: RobotType
    current_node: str
    status: RobotStatus = RobotStatus.IDLE
    current_task_id: str | None = None
    battery_percent: float = Field(default=100.0, ge=0, le=100)
