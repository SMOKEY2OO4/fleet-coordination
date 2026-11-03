
import json
from pathlib import Path
from datetime import datetime, timezone
from time import monotonic
from threading import RLock
from typing import Optional


# Persistent storage location
DATA_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "raw"
    / "movement_events.json"
)

DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

movement_events: list[dict] = []
waiting_started: dict[str, float] = {}
metrics_lock = RLock()


def load_events():
    """Load previously recorded events from disk."""
    global movement_events

    with metrics_lock:
        if DATA_FILE.exists():
            try:
                with DATA_FILE.open("r", encoding="utf-8") as file:
                    movement_events = json.load(file)
            except (json.JSONDecodeError, OSError):
                movement_events = []
        else:
            movement_events = []


def save_events():
    """Save movement events to disk."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(movement_events, file, indent=4)


def record_event(
    robot_id: str,
    event_type: str,
    current_node: str,
    task_id: Optional[str] = None,
    next_node: Optional[str] = None,
    planned_path: Optional[list[str]] = None,
    details: Optional[dict] = None,
):
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "robot_id": robot_id,
        "task_id": task_id,
        "event_type": event_type,
        "current_node": current_node,
        "next_node": next_node,
        "planned_path": planned_path,
        "details": details or {},
    }

    with metrics_lock:
        movement_events.append(event)
        save_events()


def start_waiting(robot_id: str):
    with metrics_lock:
        if robot_id not in waiting_started:
            waiting_started[robot_id] = monotonic()


def end_waiting(robot_id: str) -> Optional[float]:
    with metrics_lock:
        started = waiting_started.pop(robot_id, None)

        if started is None:
            return None

        return round(monotonic() - started, 3)


def get_movement_metrics() -> list[dict]:
    with metrics_lock:
        return movement_events.copy()


def clear_movement_metrics():
    with metrics_lock:
        movement_events.clear()
        waiting_started.clear()
        save_events()


# Restore events whenever the backend loads this module.
load_events()
