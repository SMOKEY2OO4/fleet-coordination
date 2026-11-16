
from fastapi import APIRouter, HTTPException
from backend.app.services.robot_movement import move_robot_one_step
from backend.app.models.robot import (
    Robot,
    RobotCreate,
    RobotStatus,
)
from backend.app.models.task import TaskStatus
from backend.app.planning.warehouse_graph import create_warehouse_graph
from backend.app.core.state import robots, tasks
from backend.app.coordination.reservation_manager import reservation_lock, node_reservations, edge_reservations

router = APIRouter(prefix="/robots", tags=["Robot Management"])


@router.post("/", response_model=Robot, status_code=201)
def register_robot(request: RobotCreate):
    if request.robot_id in robots:
        raise HTTPException(
            status_code=409,
            detail="Robot ID already registered.",
        )

    graph = create_warehouse_graph()

    if request.current_node not in graph:
        raise HTTPException(
            status_code=400,
            detail="Invalid warehouse node.",
        )

    robot = Robot(
        robot_id=request.robot_id,
        robot_type=request.robot_type,
        current_node=request.current_node,
        status=RobotStatus.IDLE,
        battery_percent=100.0,
    )

    robots[robot.robot_id] = robot
    return robot


@router.get("/", response_model=list[Robot])
def list_robots():
    return list(robots.values())


@router.get("/{robot_id}", response_model=Robot)
def get_robot(robot_id: str):
    robot = robots.get(robot_id)

    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found.")

    return robot


@router.post("/{robot_id}/move")
def move_robot(robot_id: str):
    return move_robot_one_step(robot_id)


@router.delete("/{robot_id}")
def delete_robot(robot_id: str):
    robot = robots.get(robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found.")

    # Clean up any assigned task
    if robot.current_task_id and robot.current_task_id in tasks:
        t = tasks[robot.current_task_id]
        if t.status in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
            t.status = TaskStatus.QUEUED
            t.assigned_robot_id = None

    # Clean up reservations
    with reservation_lock:
        nodes_to_del = [n for n, rid in node_reservations.items() if rid == robot_id]
        for n in nodes_to_del:
            del node_reservations[n]
        edges_to_del = [e for e, rid in edge_reservations.items() if rid == robot_id]
        for e in edges_to_del:
            del edge_reservations[e]

    del robots[robot_id]
    return {"success": True, "message": f"Robot {robot_id} removed."}
