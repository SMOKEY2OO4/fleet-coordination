
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.app.models.task import Task, TaskCreate, TaskStatus
from backend.app.models.robot import RobotStatus
from backend.app.planning.warehouse_graph import create_warehouse_graph
from backend.app.core.state import tasks, robots
from backend.app.services.task_allocator import assign_task
from backend.app.services.simulation_service import simulation_service

router = APIRouter(prefix="/tasks", tags=["Task Management"])


@router.post("/", response_model=Task, status_code=201)
def create_task(request: TaskCreate):
    graph = create_warehouse_graph()

    if request.start_node not in graph:
        raise HTTPException(status_code=400, detail="Invalid start node.")

    if request.destination_node not in graph:
        raise HTTPException(status_code=400, detail="Invalid destination node.")

    task = Task(
        task_id=str(uuid4()),
        start_node=request.start_node,
        destination_node=request.destination_node,
        status=TaskStatus.QUEUED,
        priority=request.priority,
    )

    tasks[task.task_id] = task
    return task


@router.get("/", response_model=list[Task])
def list_tasks():
    return list(tasks.values())


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = tasks.get(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task


@router.post("/{task_id}/assign")
def assign_task_endpoint(task_id: str):
    result = assign_task(task_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    try:
        simulation_service.load_assigned_task(task_id)
    except ValueError as exc:
        # Roll back assignment so the task remains available for correction/retry.
        task = tasks.get(task_id)
        if task:
            task.status = TaskStatus.QUEUED
            task.assigned_robot_id = None
        robot_id = result.get("robot_id")
        if robot_id in robots:
            robots[robot_id].status = RobotStatus.IDLE
            robots[robot_id].current_task_id = None
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=f"Task already {task.status.value.lower()}.",
        )

    task.status = TaskStatus.CANCELLED

    # If assigned to a robot, release the robot
    if task.assigned_robot_id and task.assigned_robot_id in robots:
        robot = robots[task.assigned_robot_id]
        if robot.current_task_id == task_id:
            robot.current_task_id = None
            robot.status = RobotStatus.IDLE

    return {"success": True, "message": f"Task {task_id} cancelled.", "task": task}


@router.delete("/{task_id}")
def delete_task(task_id: str):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task.assigned_robot_id and task.assigned_robot_id in robots:
        robot = robots[task.assigned_robot_id]
        if robot.current_task_id == task_id:
            robot.current_task_id = None
            robot.status = RobotStatus.IDLE

    del tasks[task_id]
    return {"success": True, "message": f"Task {task_id} deleted."}
