
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.app.models.task import Task, TaskCreate, TaskStatus
from backend.app.planning.warehouse_graph import create_warehouse_graph
from backend.app.core.state import tasks
from backend.app.services.task_allocator import assign_task
router = APIRouter(prefix="/tasks", tags=["Task Management"])

# Temporary in-memory storage. Tasks reset when the server restarts.


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

    return result