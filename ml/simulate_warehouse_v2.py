
import csv
import random
from pathlib import Path
from collections import deque

random.seed(42)

# --------------------------------------------------
# 1. WAREHOUSE CONFIGURATION
# --------------------------------------------------

GRAPH = {
    "A": ["B", "D"],
    "B": ["A", "C", "E"],
    "C": ["B", "F"],
    "D": ["A", "E", "G"],
    "E": ["B", "D", "F", "H"],
    "F": ["C", "E", "I"],
    "G": ["D", "H"],
    "H": ["G", "E", "I"],
    "I": ["F", "H"],
}

OUTPUT_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "simulation_data_v2.csv"
)

TOTAL_SCENARIOS = 500
MAX_TIME_STEPS = 100
RECOVERY_WAIT_THRESHOLD = 3
RECENT_NODE_LIMIT = 4


# --------------------------------------------------
# 2. PATHFINDING
# --------------------------------------------------

def shortest_path(start, goal):
    """Find the shortest route using BFS."""

    if start not in GRAPH or goal not in GRAPH:
        return []

    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == goal:
            return path

        for neighbor in GRAPH[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return []


def alternative_path(start, goal, blocked_nodes):
    """Find a route while avoiding occupied nodes."""

    blocked_nodes = set(blocked_nodes)
    blocked_nodes.discard(start)
    blocked_nodes.discard(goal)

    if start not in GRAPH or goal not in GRAPH:
        return []

    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == goal:
            return path

        for neighbor in GRAPH[current]:
            if neighbor not in visited and neighbor not in blocked_nodes:
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return []



def find_route_with_alternative_first_move(
    start,
    goal,
    blocked_nodes,
    forbidden_next_node,
    recent_nodes,
    recovery_history
):
    """
    Find an alternative route while avoiding:
    1. The currently blocked first movement.
    2. Occupied nodes.
    3. Previously failed recovery movements.
    4. Recently visited nodes, where possible.
    """

    blocked_nodes = set(blocked_nodes)
    blocked_nodes.discard(start)
    blocked_nodes.discard(goal)

    recent_nodes = set(recent_nodes)
    recent_nodes.discard(start)
    recent_nodes.discard(goal)

    recovery_history = set(
        tuple(move) for move in recovery_history
    )

    candidates = []

    for neighbor in GRAPH[start]:

        # Avoid the currently blocked movement.
        if neighbor == forbidden_next_node:
            continue

        # Avoid occupied nodes.
        if neighbor in blocked_nodes:
            continue

        # Avoid previously attempted recovery movements.
        if (start, neighbor) in recovery_history:
            continue

        # First prefer routes avoiding recently visited nodes.
        strict_blocked = blocked_nodes | recent_nodes

        remaining_path = alternative_path(
            neighbor,
            goal,
            strict_blocked
        )

        # If no route exists, relax the recent-node restriction.
        if not remaining_path:
            remaining_path = alternative_path(
                neighbor,
                goal,
                blocked_nodes
            )

        if remaining_path:
            candidates.append([start] + remaining_path)

    if not candidates:
        return []

    candidates.sort(
        key=lambda path: (len(path), path[1])
    )

    return candidates[0]


# --------------------------------------------------
# 3. DEADLOCK RECOVERY
# --------------------------------------------------



def initiate_deadlock_recovery(robots):
    """
    Recover blocked robots using alternative routes.

    Improvements:
    1. Does not permanently abandon recovery after one failed attempt.
    2. Uses a controlled fallback when recent-node restrictions fail.
    3. Prevents two recovering robots from selecting the same first move.
    4. Preserves occupied-node safety.
    """

    recovered_robots = []

    occupied_nodes = {
        robot["current_node"]
        for robot in robots
        if not robot["completed"]
    }

    # Track first moves already selected during this recovery pass.
    reserved_first_moves = set()

    # Prioritize robots that have waited the longest.
    recovery_candidates = sorted(
        [
            robot for robot in robots
            if (
                not robot["completed"]
                and robot["waiting_steps"] >= RECOVERY_WAIT_THRESHOLD
            )
        ],
        key=lambda robot: (
            -robot["waiting_steps"],
            robot["robot_id"]
        )
    )

    for robot in recovery_candidates:

        # Cooldown prevents excessive route switching.
        if robot["recovery_cooldown"] > 0:
            robot["recovery_cooldown"] -= 1
            continue

        current_node = robot["current_node"]
        original_goal = robot["original_goal"]

        current_path = robot["path"]
        path_index = robot["path_index"]

        remaining_path = current_path[path_index:]

        forbidden_next_node = (
            remaining_path[1]
            if len(remaining_path) > 1
            else None
        )

        blocked_nodes = set(occupied_nodes)
        blocked_nodes.discard(current_node)
        blocked_nodes.discard(original_goal)

        # First attempt: normal recovery restrictions.
        new_path = find_route_with_alternative_first_move(
            current_node,
            original_goal,
            blocked_nodes,
            forbidden_next_node,
            robot["recent_nodes"],
            robot["recovery_history"]
        )

        # Second attempt: relax recovery history restrictions.
        if not new_path:
            new_path = find_route_with_alternative_first_move(
                current_node,
                original_goal,
                blocked_nodes,
                forbidden_next_node,
                [],
                []
            )

        # No safe alternative is currently available.
        if not new_path or len(new_path) < 2:
            robot["recovery_cooldown"] = 1
            continue

        recovery_move = (current_node, new_path[1])

        # Do not let multiple recovering robots select the same edge.
        if recovery_move in reserved_first_moves:
            robot["recovery_cooldown"] = 1
            continue

        reserved_first_moves.add(recovery_move)

        robot["recovery_history"].append(recovery_move)

        if len(robot["recovery_history"]) > 8:
            robot["recovery_history"].pop(0)

        robot["path"] = new_path
        robot["path_index"] = 0
        robot["waiting_steps"] = 0
        robot["recovery_cooldown"] = 2
        robot["temporary_goal"] = None

        recovered_robots.append(robot["robot_id"])

    return recovered_robots


# --------------------------------------------------
# 4. SIMULTANEOUS MOVEMENT RESOLUTION
# --------------------------------------------------

def resolve_simultaneous_moves(robots, time_step):
    """
    Prevent two robots from occupying the same node.
    Also prevents head-on edge swaps and cyclic dependencies.
    """

    active_robots = [
        robot for robot in robots
        if not robot["completed"]
    ]

    occupancy = {
        robot["current_node"]: robot["robot_id"]
        for robot in active_robots
    }

    requests = {}

    for robot in active_robots:

        index = robot["path_index"]
        path = robot["path"]

        if index + 1 < len(path):
            requests[robot["robot_id"]] = path[index + 1]

    # Group requests by destination.
    destination_groups = {}

    for robot_id, destination in requests.items():
        destination_groups.setdefault(destination, []).append(robot_id)

    robot_order = {
        robot["robot_id"]: index
        for index, robot in enumerate(active_robots)
    }

    total_robots = max(len(active_robots), 1)
    selected_moves = {}

    # Select one robot per destination using rotating priority.
    for destination, robot_ids in destination_groups.items():

        winner = min(
            robot_ids,
            key=lambda robot_id: (
                robot_order[robot_id] - time_step
            ) % total_robots
        )

        selected_moves[winner] = destination

    # Check whether a robot can move safely.
    def can_move(robot_id, visiting=None):

        if visiting is None:
            visiting = set()

        if robot_id in visiting:
            return False

        if robot_id not in selected_moves:
            return False

        destination = selected_moves[robot_id]
        occupying_robot = occupancy.get(destination)

        # Destination is empty.
        if occupying_robot is None:
            return True

        # Occupant is not moving.
        if occupying_robot not in selected_moves:
            return False

        return can_move(
            occupying_robot,
            visiting | {robot_id}
        )

    approved_moves = {
        robot_id
        for robot_id in selected_moves
        if can_move(robot_id)
    }

    return requests, approved_moves


# --------------------------------------------------
# 5. ROBOT CREATION
# --------------------------------------------------

def create_robots():

    nodes = list(GRAPH.keys())

    robot_count = random.randint(2, 5)
    start_nodes = random.sample(nodes, robot_count)

    robots = []

    for index in range(robot_count):

        start = start_nodes[index]

        possible_goals = [
            node for node in nodes
            if node != start
        ]

        goal = random.choice(possible_goals)

        robots.append({
            "robot_id": f"AMR-{index + 1:02d}",
            "start_node": start,
            "current_node": start,
            "goal": goal,
            "original_goal": goal,
            "temporary_goal": None,
            "path": shortest_path(start, goal),
            "path_index": 0,
            "waiting_steps": 0,
            "total_waiting_steps": 0,
            "recent_nodes": [start],
            "recovery_history": [],
"recovery_cooldown": 0,
            "completed": False,
        })

    return robots


# --------------------------------------------------
# 6. SCENARIO SIMULATION
# --------------------------------------------------

def simulate_scenario(scenario_id):

    robots = create_robots()
    records = []

    for time_step in range(MAX_TIME_STEPS):

        active_robots = [
            robot for robot in robots
            if not robot["completed"]
        ]

        if not active_robots:
            break

        occupied_nodes = {
            robot["current_node"]
            for robot in active_robots
        }

        # Recover robots that have been waiting repeatedly.
        initiate_deadlock_recovery(active_robots)

        requests, successful_moves = resolve_simultaneous_moves(
            active_robots,
            time_step
        )

        request_counts = {}

        for next_node in requests.values():
            request_counts[next_node] = (
                request_counts.get(next_node, 0) + 1
            )

        pending_updates = []

        # Record movement attempts.
        for robot in active_robots:

            robot_id = robot["robot_id"]

            if robot_id not in requests:
                continue

            current_node = robot["current_node"]
            next_node = requests[robot_id]

            conflict = robot_id not in successful_moves

            if conflict:
                robot["waiting_steps"] += 1
                robot["total_waiting_steps"] += 1

            else:
                robot["waiting_steps"] = 0
                pending_updates.append(robot)

            records.append({
                "scenario_id": scenario_id,
                "time_step": time_step,
                "robot_id": robot_id,
                "current_node": current_node,
                "next_node": next_node,
                "robot_count": len(robots),
                "occupied_nodes": len(occupied_nodes),
                "competing_requests": request_counts[next_node],
                "waiting_steps": robot["waiting_steps"],
                "movement_delay": int(conflict),
                "is_congested": int(conflict),
                "move_successful": int(not conflict),
            })

        # Apply all approved movements together.
        for robot in pending_updates:

            robot_id = robot["robot_id"]
            new_node = requests[robot_id]

            robot["current_node"] = new_node
            robot["path_index"] += 1

            # Maintain recent movement history.
            robot["recent_nodes"].append(new_node)

            if len(robot["recent_nodes"]) > RECENT_NODE_LIMIT:
                robot["recent_nodes"].pop(0)

        # Check task completion.
        for robot in robots:

            if robot["completed"]:
                continue

            if robot["current_node"] == robot["original_goal"]:

                robot["completed"] = True
                robot["goal"] = robot["original_goal"]
                robot["temporary_goal"] = None

    # --------------------------------------------------
    # 7. SCENARIO RESULTS
    # --------------------------------------------------

    completed_robots = sum(
        1 for robot in robots
        if robot["completed"]
    )

    robot_results = []

    for robot in robots:

        robot_results.append({
            "scenario_id": scenario_id,
            "robot_id": robot["robot_id"],
            "start_node": robot["start_node"],
            "goal_node": robot["original_goal"],
            "final_node": robot["current_node"],
            "completed": int(robot["completed"]),
            "waiting_steps": robot["waiting_steps"],
            "total_waiting_steps": robot["total_waiting_steps"],
            "path_index": robot["path_index"],
            "path_length": len(robot["path"]),
            "temporary_goal": robot["temporary_goal"] or "",
        })

    scenario_summary = {
        "total_robots": len(robots),
        "completed_robots": completed_robots,
        "incomplete_robots": len(robots) - completed_robots,
    }

    return records, scenario_summary, robot_results


# --------------------------------------------------
# 8. MAIN SIMULATION
# --------------------------------------------------

def main():

    all_records = []
    all_robot_results = []

    completion_stats = {
        "completed_robots": 0,
        "incomplete_robots": 0,
        "total_robots": 0,
    }

    for scenario_id in range(1, TOTAL_SCENARIOS + 1):

        scenario_records, scenario_summary, robot_results = (
            simulate_scenario(scenario_id)
        )

        all_records.extend(scenario_records)
        all_robot_results.extend(robot_results)

        completion_stats["total_robots"] += (
            scenario_summary["total_robots"]
        )

        completion_stats["completed_robots"] += (
            scenario_summary["completed_robots"]
        )

        completion_stats["incomplete_robots"] += (
            scenario_summary["incomplete_robots"]
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save movement dataset.
    fieldnames = [
        "scenario_id",
        "time_step",
        "robot_id",
        "current_node",
        "next_node",
        "robot_count",
        "occupied_nodes",
        "competing_requests",
        "waiting_steps",
        "movement_delay",
        "is_congested",
        "move_successful",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(all_records)

    # Save robot-level analysis report.
    report_file = (
        OUTPUT_FILE.parent / "scenario_robot_report.csv"
    )

    report_fields = [
        "scenario_id",
        "robot_id",
        "start_node",
        "goal_node",
        "final_node",
        "completed",
        "waiting_steps",
        "total_waiting_steps",
        "path_index",
        "path_length",
        "temporary_goal",
    ]

    with report_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as report:

        report_writer = csv.DictWriter(
            report,
            fieldnames=report_fields
        )

        report_writer.writeheader()
        report_writer.writerows(all_robot_results)

    # --------------------------------------------------
    # 9. FINAL REPORT
    # --------------------------------------------------

    print("Robot analysis report:", report_file)

    print("\n========== SIMULATION V2 COMPLETED ==========")
    print("Scenarios:", TOTAL_SCENARIOS)
    print("Movement records:", len(all_records))
    print("Output:", OUTPUT_FILE)

    print("\n========== TASK COMPLETION REPORT ==========")

    print("Total robots:", completion_stats["total_robots"])
    print("Completed robots:", completion_stats["completed_robots"])
    print("Incomplete robots:", completion_stats["incomplete_robots"])

    total = completion_stats["total_robots"]
    completed = completion_stats["completed_robots"]

    completion_rate = (
        completed / total * 100
        if total else 0
    )

    print(f"Task completion rate: {completion_rate:.2f}%")


if __name__ == "__main__":
    main()
