
from fastapi import HTTPException

from backend.app.core.state import robots, tasks
from backend.app.core.metrics import (
    record_event,
    start_waiting,
    end_waiting,
)

from backend.app.models.robot import RobotStatus
from backend.app.models.task import TaskStatus
from backend.app.planning.astar import astar
from backend.app.planning.warehouse_graph import create_warehouse_graph

from backend.app.coordination.reservation_manager import (
    reserve_move,
    release_move,
    reservation_lock,
)


def move_robot_one_step(robot_id: str) -> dict:
    robot = robots.get(robot_id)

    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found.")

    if robot.status not in (
        RobotStatus.ASSIGNED,
        RobotStatus.MOVING,
        RobotStatus.WAITING,
    ):
        raise HTTPException(
            status_code=400,
            detail="Robot is not assigned to an active task.",
        )

    task = tasks.get(robot.current_task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Assigned task not found.")

    if task.status not in (
        TaskStatus.ASSIGNED,
        TaskStatus.IN_PROGRESS,
    ):
        raise HTTPException(
            status_code=400,
            detail="Task is not ready for movement.",
        )

    graph = create_warehouse_graph()

    with reservation_lock:

        target = (
            task.start_node
            if task.status == TaskStatus.ASSIGNED
            else task.destination_node
        )

        current_node = robot.current_node

        # Identify nodes occupied by other robots.
        occupied_nodes = {
            other_robot.current_node
            for other_id, other_robot in robots.items()
            if other_id != robot_id
        }

        # Calculate the original shortest route.
        original_path = astar(
            graph,
            current_node,
            target,
        )

        # Calculate a safe route avoiding occupied nodes.
        path = astar(
            graph,
            current_node,
            target,
            blocked_nodes=occupied_nodes,
        )

        # No safe route is available.
        if not path:
            robot.status = RobotStatus.WAITING
            start_waiting(robot_id)

            record_event(
                robot_id=robot_id,
                task_id=task.task_id,
                event_type="blocked",
                current_node=current_node,
                details={
                    "occupied_nodes": sorted(occupied_nodes),
                    "reason": "No safe alternative route available",
                },
            )

            return {
                "robot_id": robot.robot_id,
                "current_node": current_node,
                "robot_status": robot.status,
                "task_id": task.task_id,
                "task_status": task.status,
                "message": "No safe alternative route available. Robot is waiting.",
            }

        # Record when the robot successfully recovers from waiting.
        waiting_duration = end_waiting(robot_id)

        if waiting_duration is not None:
            record_event(
                robot_id=robot_id,
                task_id=task.task_id,
                event_type="waiting_completed",
                current_node=current_node,
                details={
                    "waiting_duration_seconds": waiting_duration,
                },
            )

        # Record when an alternative route is selected.
        if path != original_path:
            record_event(
                robot_id=robot_id,
                task_id=task.task_id,
                event_type="reroute",
                current_node=current_node,
                next_node=path[1] if len(path) > 1 else None,
                planned_path=path,
                details={
                    "original_path": original_path,
                    "occupied_nodes": sorted(occupied_nodes),
                },
            )

        # Handle pickup or delivery completion.
        if len(path) == 1:

            if task.status == TaskStatus.ASSIGNED:
                task.status = TaskStatus.IN_PROGRESS
                robot.status = RobotStatus.MOVING

                record_event(
                    robot_id=robot_id,
                    task_id=task.task_id,
                    event_type="pickup_reached",
                    current_node=current_node,
                )

            elif task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.COMPLETED
                robot.status = RobotStatus.IDLE
                robot.current_task_id = None

                record_event(
                    robot_id=robot_id,
                    task_id=task.task_id,
                    event_type="task_completed",
                    current_node=current_node,
                )

            return {
                "robot_id": robot.robot_id,
                "current_node": current_node,
                "robot_status": robot.status,
                "task_id": task.task_id,
                "task_status": task.status,
                "target_node": target,
                "message": "Target reached.",
            }

        next_node = path[1]

        # Reserve the next node before movement.
        if not reserve_move(robot_id, current_node, next_node):
            robot.status = RobotStatus.WAITING
            start_waiting(robot_id)

            record_event(
                robot_id=robot_id,
                task_id=task.task_id,
                event_type="blocked",
                current_node=current_node,
                next_node=next_node,
                planned_path=path,
                details={
                    "reason": "Movement reservation denied",
                },
            )

            return {
                "robot_id": robot.robot_id,
                "current_node": current_node,
                "robot_status": robot.status,
                "task_id": task.task_id,
                "task_status": task.status,
                "message": "Movement blocked. Robot is waiting.",
            }

        try:
            # Execute one movement step.
            robot.status = RobotStatus.MOVING
            robot.current_node = next_node

            record_event(
                robot_id=robot_id,
                task_id=task.task_id,
                event_type="movement",
                current_node=current_node,
                next_node=next_node,
                planned_path=path,
            )

            # Reached pickup location.
            if (
                task.status == TaskStatus.ASSIGNED
                and robot.current_node == task.start_node
            ):
                task.status = TaskStatus.IN_PROGRESS

                record_event(
                    robot_id=robot_id,
                    task_id=task.task_id,
                    event_type="pickup_reached",
                    current_node=robot.current_node,
                )

            # Reached delivery location.
            if (
                task.status == TaskStatus.IN_PROGRESS
                and robot.current_node == task.destination_node
            ):
                task.status = TaskStatus.COMPLETED
                robot.status = RobotStatus.IDLE
                robot.current_task_id = None

                record_event(
                    robot_id=robot_id,
                    task_id=task.task_id,
                    event_type="task_completed",
                    current_node=robot.current_node,
                )

        finally:
            release_move(robot_id, current_node, next_node)

        return {
            "robot_id": robot.robot_id,
            "current_node": robot.current_node,
            "robot_status": robot.status,
            "task_id": task.task_id,
            "task_status": task.status,
            "target_node": target,
            "planned_path": path,
            "message": (
                "Alternative route selected."
                if path != original_path
                else "Movement successful."
            ),
        }
