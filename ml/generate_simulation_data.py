
import csv
import random
from pathlib import Path

# Reproducible simulation
random.seed(42)

# Existing 9-node warehouse graph
GRAPH = {
    "A": ["B", "D"],
    "B": ["A", "C", "E"],
    "C": ["B", "F"],
    "D": ["A", "E", "G"],
    "E": ["B", "D", "F", "H"],
    "F": ["C", "E", "I"],
    "G": ["D", "H"],
    "H": ["G", "E", "I"],
    "I": ["F", "H"]
}

OUTPUT_FILE = (
    Path(__file__).resolve().parents[1]
    / "data" / "raw" / "simulation_data.csv"
)


def shortest_path(start, goal, blocked_nodes=None):
    blocked_nodes = blocked_nodes or set()

    if start in blocked_nodes or goal in blocked_nodes:
        return []

    queue = [[start]]
    visited = {start}

    while queue:
        path = queue.pop(0)
        current = path[-1]

        if current == goal:
            return path

        for neighbor in GRAPH[current]:
            if neighbor not in visited and neighbor not in blocked_nodes:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return []


def generate_scenario(scenario_id):
    # Vary the number of robots in each scenario
    robot_count = random.randint(2, 5)

    nodes = list(GRAPH.keys())
    robots = []

    for robot_number in range(robot_count):
        start = random.choice(nodes)
        goal = random.choice([n for n in nodes if n != start])

        robots.append({
            "robot_id": f"AMR-{robot_number + 1:02d}",
            "start": start,
            "goal": goal
        })

    # Randomly introduce warehouse congestion
    blocked_nodes = set()

    if random.random() < 0.4:
        blocked_nodes.add(random.choice(nodes))

    records = []

    for robot in robots:
        path = shortest_path(
            robot["start"],
            robot["goal"],
            blocked_nodes
        )

        if not path:
            continue

        for index in range(len(path) - 1):
            current_node = path[index]
            next_node = path[index + 1]

            # Simulated traffic around the next node
            nearby_traffic = random.randint(0, robot_count - 1)

            # Simulated movement delay
            movement_delay = random.randint(1, 5) + nearby_traffic * 2

            records.append({
                "scenario_id": scenario_id,
                "robot_id": robot["robot_id"],
                "start_node": robot["start"],
                "goal_node": robot["goal"],
                "current_node": current_node,
                "next_node": next_node,
                "robot_count": robot_count,
                "occupied_nodes": len(blocked_nodes),
                "nearby_traffic": nearby_traffic,
                "movement_delay": movement_delay,
                "is_congested": int(movement_delay >= 7)
            })

    return records


def main():
    all_records = []

    total_scenarios = 500

    for scenario_id in range(1, total_scenarios + 1):
        all_records.extend(generate_scenario(scenario_id))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "scenario_id",
        "robot_id",
        "start_node",
        "goal_node",
        "current_node",
        "next_node",
        "robot_count",
        "occupied_nodes",
        "nearby_traffic",
        "movement_delay",
        "is_congested"
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print("========== SIMULATION DATA GENERATED ==========")
    print(f"Scenarios generated: {total_scenarios}")
    print(f"Total movement records: {len(all_records)}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
