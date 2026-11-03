
from backend.app.planning.astar import astar
from backend.app.planning.warehouse_graph import create_warehouse_graph


def test_route_exists():
    graph = create_warehouse_graph()
    path = astar(graph, "A", "I")

    assert path[0] == "A"
    assert path[-1] == "I"


def test_blocked_edge_is_avoided():
    graph = create_warehouse_graph()
    path = astar(graph, "A", "I", {("E", "F")})

    assert path
    assert all(
        (a, b) != ("E", "F") and (a, b) != ("F", "E")
        for a, b in zip(path, path[1:])
    )


def test_same_start_and_goal():
    graph = create_warehouse_graph()
    assert astar(graph, "A", "A") == ["A"]


def test_blocked_node_is_avoided():
    graph = create_warehouse_graph()

    path = astar(
        graph,
        "B",
        "I",
        blocked_nodes={"C"}
    )

    assert path
    assert "C" not in path
    assert path[0] == "B"
    assert path[-1] == "I"
