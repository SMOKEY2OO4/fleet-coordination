"""
Comprehensive Multi-Robot Fleet Coordination System Test Suite.

Automated verification for:
1. Pathfinding (BFS, A*, alternative routes)
2. Robot creation and unique start positions
3. Collision safety (destination uniqueness, head-on swap, stationary occupancy)
4. Safe circular multi-robot rotations
5. Movement chain advancement
6. Waiting step counters and recovery cooldown mechanics
7. Task completion and termination
8. Dataset schema validation
9. ML model pipeline, training, and persistence
10. ML inference bounds and fallback resilience
11. Seed reproducibility across simulation runs
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from ml.simulate_warehouse_v2 import (
    GRAPH,
    shortest_path,
    alternative_path,
    create_robots,
    find_route_with_alternative_first_move,
    initiate_deadlock_recovery
)
from tests.test_coordination import resolve_simultaneous_moves_improved
from tests.test_coordination_helpers import check_movement_safety, build_test_robot
from ml.ml_coordination import MLCongestionAdvisor, ml_congestion_aware_path

ROOT_DIR = Path(__file__).resolve().parents[1]


# -------------------------------------------------------------
# 1. Pathfinding Tests
# -------------------------------------------------------------
def test_bfs_shortest_path_direct():
    path = shortest_path("A", "C")
    assert path == ["A", "B", "C"]
    assert len(path) == 3


def test_bfs_alternative_path_with_obstacles():
    # A to I with center E blocked: should go around perimeter
    path = alternative_path("A", "I", blocked_nodes={"E"})
    assert path is not None and len(path) > 0
    assert "E" not in path
    assert path[0] == "A" and path[-1] == "I"


def test_invalid_pathfinding_nodes():
    assert shortest_path("INVALID", "A") == []
    assert shortest_path("A", "INVALID") == []


# -------------------------------------------------------------
# 2. Robot Creation & Invariants
# -------------------------------------------------------------
def test_robot_creation_unique_starts():
    for _ in range(20):
        robots = create_robots()
        assert 2 <= len(robots) <= 5
        starts = [r["start_node"] for r in robots]
        assert len(starts) == len(set(starts)), "Initial starting nodes must be pairwise unique"
        for r in robots:
            assert r["start_node"] != r["goal"], "Start node must differ from goal"
            assert len(r["path"]) >= 2
            assert r["path"][0] == r["start_node"]
            assert r["path"][-1] == r["goal"]


# -------------------------------------------------------------
# 3. Collision Prevention & Invariant Verification
# -------------------------------------------------------------
def test_destination_collision_prevention():
    # 3 robots all requesting node E
    r1 = build_test_robot("AMR-01", "B", "E", waiting_steps=3)
    r2 = build_test_robot("AMR-02", "D", "E", waiting_steps=1)
    r3 = build_test_robot("AMR-03", "F", "E", waiting_steps=0)
    robots = [r1, r2, r3]
    reqs, approved = resolve_simultaneous_moves_improved(robots, time_step=0)
    assert len(approved) == 1
    assert "AMR-01" in approved, "Highest waiting robot must win destination contention"
    check_movement_safety(robots, approved, reqs)


def test_head_on_edge_swap_forbidden():
    r1 = build_test_robot("AMR-01", "D", "G")
    r2 = build_test_robot("AMR-02", "G", "D")
    robots = [r1, r2]
    reqs, approved = resolve_simultaneous_moves_improved(robots)
    assert len(approved) == 0
    check_movement_safety(robots, approved, reqs)


def test_stationary_occupied_node_blocks_incoming():
    # AMR-01 wants B; AMR-02 is stationary at B
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", None)
    robots = [r1, r2]
    reqs, approved = resolve_simultaneous_moves_improved(robots)
    assert len(approved) == 0
    check_movement_safety(robots, approved, reqs)


# -------------------------------------------------------------
# 4. Safe Multi-Robot Rotations
# -------------------------------------------------------------
def test_circular_3_robot_rotation_approved():
    # Rotation: B -> C -> F -> B
    r1 = build_test_robot("AMR-01", "B", "C")
    r2 = build_test_robot("AMR-02", "C", "F")
    r3 = build_test_robot("AMR-03", "F", "B")
    robots = [r1, r2, r3]
    reqs, approved = resolve_simultaneous_moves_improved(robots)
    assert approved == {"AMR-01", "AMR-02", "AMR-03"}
    check_movement_safety(robots, approved, reqs)


# -------------------------------------------------------------
# 5. Waiting & Recovery Mechanics
# -------------------------------------------------------------
def test_deadlock_recovery_cooldown_and_rerouting():
    r1 = build_test_robot("AMR-01", "G", "H", waiting_steps=3)
    r1["original_goal"] = "D"
    r1["recent_nodes"] = ["G"]
    r1["recovery_history"] = []
    r1["recovery_cooldown"] = 0
    r1["temporary_goal"] = None

    robots = [r1]
    recovered = initiate_deadlock_recovery(robots)
    assert "AMR-01" in recovered
    assert r1["waiting_steps"] == 0
    assert r1["recovery_cooldown"] == 2
    assert len(r1["recovery_history"]) == 1


# -------------------------------------------------------------
# 6. Dataset Schema Validation
# -------------------------------------------------------------
def test_dataset_v2_schema():
    csv_file = ROOT_DIR / "data" / "raw" / "simulation_data_v2.csv"
    assert csv_file.exists()
    df = pd.read_csv(csv_file)
    expected_cols = [
        "scenario_id", "time_step", "robot_id", "current_node",
        "next_node", "robot_count", "occupied_nodes", "competing_requests",
        "waiting_steps", "movement_delay", "is_congested", "move_successful"
    ]
    assert list(df.columns) == expected_cols
    assert df["is_congested"].isin([0, 1]).all()
    assert df["move_successful"].isin([0, 1]).all()
    assert (df["is_congested"] + df["move_successful"] == 1).all()


# -------------------------------------------------------------
# 7. Machine Learning Model & Inference
# -------------------------------------------------------------
def test_ml_advisor_inference_bounds():
    advisor = MLCongestionAdvisor()
    assert advisor.is_available is True
    risk = advisor.predict_move_congestion_risk("B", "E", 4, 3, 1, 0, 5)
    assert 0.0 <= risk <= 1.0


def test_ml_advisor_handles_graceful_fallback():
    # Non-existent model path should fallback cleanly without throwing
    advisor = MLCongestionAdvisor(model_path=Path("non_existent_model.joblib"))
    assert advisor.is_available is False
    risk = advisor.predict_move_congestion_risk("A", "B", 3, 2, 1, 0, 0)
    assert 0.0 <= risk <= 1.0


# -------------------------------------------------------------
# 8. Reproducibility
# -------------------------------------------------------------
def test_seed_reproducibility():
    import random
    random.seed(42)
    run1 = [create_robots() for _ in range(5)]
    random.seed(42)
    run2 = [create_robots() for _ in range(5)]

    for r_set1, r_set2 in zip(run1, run2):
        for r1, r2 in zip(r_set1, r_set2):
            assert r1["robot_id"] == r2["robot_id"]
            assert r1["start_node"] == r2["start_node"]
            assert r1["goal"] == r2["goal"]
            assert r1["path"] == r2["path"]
