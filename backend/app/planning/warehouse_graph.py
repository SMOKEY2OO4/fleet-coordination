
from typing import Dict, List, Tuple

WarehouseGraph = Dict[str, List[Tuple[str, float]]]

# Grid coordinates: (x, y)
WAREHOUSE_COORDINATES = {
    "A": (0, 0),
    "B": (1, 0),
    "C": (2, 0),
    "D": (0, 1),
    "E": (1, 1),
    "F": (2, 1),
    "G": (0, 2),
    "H": (1, 2),
    "I": (2, 2),
}


def create_warehouse_graph() -> WarehouseGraph:
    """Create the initial weighted warehouse graph."""
    return {
        "A": [("B", 1.0), ("D", 1.0)],
        "B": [("A", 1.0), ("C", 1.0), ("E", 1.0)],
        "C": [("B", 1.0), ("F", 1.0)],
        "D": [("A", 1.0), ("E", 1.0), ("G", 1.0)],
        "E": [("B", 1.0), ("D", 1.0), ("F", 1.0), ("H", 1.0)],
        "F": [("C", 1.0), ("E", 1.0), ("I", 1.0)],
        "G": [("D", 1.0), ("H", 1.0)],
        "H": [("G", 1.0), ("E", 1.0), ("I", 1.0)],
        "I": [("F", 1.0), ("H", 1.0)],
    }
