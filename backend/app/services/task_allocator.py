
from backend.app.core.state import robots, tasks
from backend.app.models.robot import RobotStatus
from backend.app.models.task import TaskStatus
from backend.app.planning.astar import astar
from backend.app.planning.warehouse_graph import create_warehouse_graph


def assign_task(task_id: str) -> dict:
    task = tasks.get(task_id)

    if task is None:
        return {"success": False, "message": "Task not found."}

    if task.status != TaskStatus.QUEUED:
        return {
            "success": False,
            "message": "Only queued tasks can be assigned.",
        }

    graph = create_warehouse_graph()
    candidates = []

    for robot in robots.values():
        if robot.status != RobotStatus.IDLE:
            continue

        path = astar(graph, robot.current_node, task.start_node)

        if path:
            candidates.append((len(path) - 1, robot.robot_id, path))

    if not candidates:
        return {
            "success": False,
            "message": "No available robot can reach the task.",
        }

    distance, robot_id, path = min(candidates)

    robot = robots[robot_id]
    robot.status = RobotStatus.ASSIGNED
    robot.current_task_id = task.task_id

    task.assigned_robot_id = robot_id
    task.status = TaskStatus.ASSIGNED

    return {
        "success": True,
        "task_id": task.task_id,
        "robot_id": robot_id,
        "distance_to_pickup": distance,
        "pickup_path": path,
    }
