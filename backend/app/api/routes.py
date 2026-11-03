
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.planning.astar import astar
from backend.app.planning.warehouse_graph import create_warehouse_graph

router = APIRouter(prefix="/routes", tags=["Path Planning"])


class RouteRequest(BaseModel):
    start: str
    goal: str
    blocked_edges: list[tuple[str, str]] = Field(default_factory=list)


@router.post("/plan")
def plan_route(request: RouteRequest):
    graph = create_warehouse_graph()

    try:
        path = astar(
            graph=graph,
            start=request.start,
            goal=request.goal,
            blocked_edges=set(request.blocked_edges),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not path:
        raise HTTPException(
            status_code=404,
            detail="No route is available between the requested nodes.",
        )

    return {
        "start": request.start,
        "goal": request.goal,
        "path": path,
        "total_cost": float(len(path) - 1),
    }
