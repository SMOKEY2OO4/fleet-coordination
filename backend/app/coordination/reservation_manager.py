from threading import RLock

from backend.app.core.state import robots


# Temporary reservations for movements currently being processed.
node_reservations: dict[str, str] = {}
edge_reservations: dict[tuple[str, str], str] = {}

reservation_lock = RLock()


def reserve_move(
    robot_id: str,
    current_node: str,
    next_node: str,
) -> bool:
    """
    Reserve the next node and connecting edge
    before allowing a robot to move.
    """

    with reservation_lock:

        # Check whether another robot occupies the destination.
        for other_id, robot in robots.items():
            if other_id != robot_id and robot.current_node == next_node:
                return False

        # Check whether another robot reserved the destination.
        if next_node in node_reservations:
            if node_reservations[next_node] != robot_id:
                return False

        # Prevent opposite-direction edge conflicts.
        edge = (current_node, next_node)
        reverse_edge = (next_node, current_node)

        if edge in edge_reservations:
            if edge_reservations[edge] != robot_id:
                return False

        if reverse_edge in edge_reservations:
            if edge_reservations[reverse_edge] != robot_id:
                return False

        # Reserve the destination and edge.
        node_reservations[next_node] = robot_id
        edge_reservations[edge] = robot_id

        return True


def release_move(
    robot_id: str,
    current_node: str,
    next_node: str,
) -> None:
    """Release temporary movement reservations."""

    with reservation_lock:

        if node_reservations.get(next_node) == robot_id:
            del node_reservations[next_node]

        edge = (current_node, next_node)

        if edge_reservations.get(edge) == robot_id:
            del edge_reservations[edge]
