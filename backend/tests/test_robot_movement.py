
import pytest

from backend.app.core.state import robots, tasks
from backend.app.models.robot import Robot, RobotStatus, RobotType
from backend.app.models.task import Task, TaskStatus
from backend.app.services.robot_movement import move_robot_one_step
from backend.app.coordination.reservation_manager import (
    node_reservations,
    edge_reservations,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset shared state before every test."""
    robots.clear()
    tasks.clear()
    node_reservations.clear()
    edge_reservations.clear()


def create_robot(robot_id, node):
    robot = Robot(
        robot_id=robot_id,
        robot_type=RobotType.SIMULATED,
        current_node=node,
        status=RobotStatus.MOVING,
        current_task_id="TASK-01",
        battery_percent=100,
    )
    robots[robot_id] = robot
    return robot


def create_task(destination="I"):
    task = Task(
        task_id="TASK-01",
        start_node="B",
        destination_node=destination,
        status=TaskStatus.IN_PROGRESS,
        assigned_robot_id="AMR-01",
    )
    tasks[task.task_id] = task
    return task


def test_robot_avoids_occupied_node():
    create_robot("AMR-01", "B")
    create_robot("AMR-02", "C")
    create_task()

    result = move_robot_one_step("AMR-01")

    assert result["current_node"] == "E"
    assert "C" not in result["planned_path"]
    assert result["planned_path"] == ["B", "E", "F", "I"]


def test_robot_waits_when_no_safe_route_exists():
    create_robot("AMR-01", "B")
    create_robot("AMR-02", "A")
    create_robot("AMR-03", "C")
    create_robot("AMR-04", "E")
    create_task()

    result = move_robot_one_step("AMR-01")

    assert result["current_node"] == "B"
    assert result["robot_status"] == RobotStatus.WAITING
    assert "No safe alternative route" in result["message"]


def test_robot_resumes_after_obstacles_clear():
    create_robot("AMR-01", "B")
    create_robot("AMR-02", "A")
    create_robot("AMR-03", "C")
    create_robot("AMR-04", "E")
    create_task()

    # First attempt: all immediate routes are blocked.
    first_result = move_robot_one_step("AMR-01")

    assert first_result["robot_status"] == RobotStatus.WAITING

    # Remove the blocking robots.
    robots.pop("AMR-02")
    robots.pop("AMR-03")
    robots.pop("AMR-04")

    # Second attempt: the robot should resume movement.
    second_result = move_robot_one_step("AMR-01")

    assert second_result["current_node"] == "C"
    assert second_result["robot_status"] == RobotStatus.MOVING


def test_robot_completes_task_at_destination():
    robot = create_robot("AMR-01", "I")
    task = create_task()

    result = move_robot_one_step("AMR-01")

    assert result["current_node"] == "I"
    assert result["task_status"] == TaskStatus.COMPLETED
    assert robot.status == RobotStatus.IDLE
    assert robot.current_task_id is None
