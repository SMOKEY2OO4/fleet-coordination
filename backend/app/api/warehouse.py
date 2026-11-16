from fastapi import APIRouter
from backend.app.planning.warehouse_graph import create_warehouse_graph, WAREHOUSE_COORDINATES
from backend.app.core.state import robots, tasks

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse"])


@router.get("/graph")
def get_warehouse_graph():
    """Return warehouse graph topology with coordinates."""
    graph = create_warehouse_graph()
    nodes = []
    for node_id, coords in WAREHOUSE_COORDINATES.items():
        nodes.append({
            "id": node_id,
            "x": coords[0],
            "y": coords[1],
        })
    
    edges = []
    seen = set()
    for node, neighbors in graph.items():
        for neighbor, weight in neighbors:
            edge_key = tuple(sorted([node, neighbor]))
            if edge_key not in seen:
                seen.add(edge_key)
                edges.append({
                    "from": edge_key[0],
                    "to": edge_key[1],
                    "weight": weight,
                })
    
    return {"nodes": nodes, "edges": edges}


@router.get("/status")
def get_warehouse_status():
    """Return overall warehouse status summary."""
    robot_list = list(robots.values())
    task_list = list(tasks.values())
    
    active_robots = sum(1 for r in robot_list if r.status.value in ("MOVING", "ASSIGNED", "WAITING"))
    idle_robots = sum(1 for r in robot_list if r.status.value == "IDLE")
    
    completed_tasks = sum(1 for t in task_list if t.status.value == "COMPLETED")
    pending_tasks = sum(1 for t in task_list if t.status.value in ("QUEUED", "ASSIGNED"))
    in_progress_tasks = sum(1 for t in task_list if t.status.value == "IN_PROGRESS")
    
    occupied_nodes = [r.current_node for r in robot_list]
    congested_nodes = [node for node in set(occupied_nodes) if occupied_nodes.count(node) > 1]
    
    return {
        "total_robots": len(robot_list),
        "active_robots": active_robots,
        "idle_robots": idle_robots,
        "total_tasks": len(task_list),
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "congested_nodes": congested_nodes,
        "occupied_nodes": list(set(occupied_nodes)),
        "system_health": "healthy",
    }
