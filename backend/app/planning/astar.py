
import heapq
from typing import Dict, List, Optional, Tuple, Set

from backend.app.planning.warehouse_graph import (
    WAREHOUSE_COORDINATES,
    WarehouseGraph,
)


def astar(
    graph: WarehouseGraph,
    start: str,
    goal: str,
    blocked_edges: Optional[Set[Tuple[str, str]]] = None,
    blocked_nodes: Optional[Set[str]] = None,
) -> List[str]:
    """Find a minimum-cost path using A*, avoiding blocked edges and nodes."""

    if start not in graph or goal not in graph:
        raise ValueError("Start and goal must exist in the warehouse graph.")

    if set(graph) - set(WAREHOUSE_COORDINATES):
        raise ValueError("Every graph node must have coordinates.")

    if start == goal:
        return [start]

    blocked_edges = blocked_edges or set()
    blocked_nodes = blocked_nodes or set()

    # Cannot reach a destination occupied by another robot.
    if goal in blocked_nodes:
        return []

    def is_blocked_edge(a: str, b: str) -> bool:
        return (a, b) in blocked_edges or (b, a) in blocked_edges

    def heuristic(node: str) -> float:
        x1, y1 = WAREHOUSE_COORDINATES[node]
        x2, y2 = WAREHOUSE_COORDINATES[goal]
        return abs(x1 - x2) + abs(y1 - y2)

    frontier = [(heuristic(start), 0.0, start)]
    came_from: Dict[str, Optional[str]] = {start: None}
    cost_so_far = {start: 0.0}

    while frontier:
        _, current_cost, current = heapq.heappop(frontier)

        if current_cost > cost_so_far.get(current, float("inf")):
            continue

        if current == goal:
            break

        for neighbor, edge_cost in graph[current]:

            if edge_cost < 0:
                raise ValueError("Edge costs must be non-negative.")

            if is_blocked_edge(current, neighbor):
                continue

            # Avoid nodes occupied by other robots.
            if neighbor in blocked_nodes:
                continue

            new_cost = current_cost + edge_cost

            if new_cost < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current

                priority = new_cost + heuristic(neighbor)
                heapq.heappush(
                    frontier,
                    (priority, new_cost, neighbor)
                )

    if goal not in came_from:
        return []

    path = []
    current: Optional[str] = goal

    while current is not None:
        path.append(current)
        current = came_from[current]

    return list(reversed(path))
