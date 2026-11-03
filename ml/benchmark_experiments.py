"""
Reproducible Benchmark and Performance Evaluation Framework.

Executes a controlled comparative benchmark across 4 system configurations
under IDENTICAL workloads, seeds, and warehouse topologies:
1. Baseline Simulation (Original v2)
2. Improved Movement Resolver (Cycle-safe, starvation-free)
3. Improved Resolver + Advanced Deadlock Recovery
4. ML-Assisted Fleet Coordination (ML risk-aware routing + improved resolver)

Records all 11 required evaluation metrics and generates comparison tables.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import time
import json
from collections import deque
import pandas as pd
import numpy as np

from ml.simulate_warehouse_v2 import (
    GRAPH,
    shortest_path,
    alternative_path,
    find_route_with_alternative_first_move,
    initiate_deadlock_recovery,
    resolve_simultaneous_moves,
    create_robots,
    TOTAL_SCENARIOS,
    MAX_TIME_STEPS,
    RECENT_NODE_LIMIT
)
from tests.test_coordination import resolve_simultaneous_moves_improved
from tests.test_coordination_helpers import check_movement_safety
from ml.ml_coordination import MLCongestionAdvisor, ml_congestion_aware_path

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "experiments"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_experiment(algorithm_name: str, seed: int = 42) -> dict:
    import random
    random.seed(seed)
    np.random.seed(seed)

    print(f"\nRunning Benchmark: [{algorithm_name}] across {TOTAL_SCENARIOS} scenarios...")
    start_time = time.perf_counter()

    ml_advisor = MLCongestionAdvisor() if "ML-Assisted" in algorithm_name else None

    total_robots = 0
    completed_robots = 0
    total_waiting_steps = 0
    blocked_movements = 0
    successful_movements = 0
    recovery_invocations = 0
    total_completion_time = 0
    total_route_length = 0
    safety_violations = 0

    scenario_records = []
    robot_records = []

    for scenario_id in range(1, TOTAL_SCENARIOS + 1):
        robots = create_robots()
        sc_robots = len(robots)
        total_robots += sc_robots

        for r in robots:
            total_route_length += len(r["path"])

        for t in range(MAX_TIME_STEPS):
            active_robots = [r for r in robots if not r["completed"]]
            if not active_robots:
                break

            occupied_nodes = {r["current_node"] for r in active_robots}

            # -------------------------------------------------------------
            # Deadlock Recovery Selection
            # -------------------------------------------------------------
            if algorithm_name == "Baseline":
                rec = initiate_deadlock_recovery(active_robots)
                recovery_invocations += len(rec)
            elif algorithm_name == "Improved Resolver":
                rec = initiate_deadlock_recovery(active_robots)
                recovery_invocations += len(rec)
            elif algorithm_name in ("Improved Recovery", "ML-Assisted"):
                # Advanced Deadlock Recovery:
                recovering = sorted(
                    [r for r in active_robots if r["waiting_steps"] >= 3],
                    key=lambda r: (-r["waiting_steps"], r["robot_id"])
                )
                reserved_first_moves = set()
                rec = []
                for robot in recovering:
                    if robot["recovery_cooldown"] > 0:
                        robot["recovery_cooldown"] -= 1
                        continue

                    curr = robot["current_node"]
                    goal = robot["original_goal"]
                    curr_path = robot["path"]
                    idx = robot["path_index"]
                    rem = curr_path[idx:]
                    forbidden = rem[1] if len(rem) > 1 else None

                    blocked = set(occupied_nodes) - {curr, goal}

                    # ML-guided alternative path scoring
                    if algorithm_name == "ML-Assisted" and ml_advisor and ml_advisor.is_available:
                        candidate_paths = []
                        strict_blocked = blocked | set(robot["recent_nodes"]) - {curr, goal}
                        for nbr in GRAPH[curr]:
                            if nbr == forbidden or nbr in blocked:
                                continue
                            if (curr, nbr) in reserved_first_moves:
                                continue
                            rem_p = alternative_path(nbr, goal, strict_blocked)
                            if not rem_p:
                                rem_p = alternative_path(nbr, goal, blocked)
                            if rem_p:
                                p = [curr] + rem_p
                                risk = ml_advisor.predict_move_congestion_risk(
                                    curr, nbr, sc_robots, len(occupied_nodes), 1, robot["waiting_steps"], t
                                )
                                # Use ML predicted risk as an intelligent tie-breaker among equal-length alternative routes
                                score = len(p) + 0.1 * risk
                                candidate_paths.append((score, len(p), p))
                        if candidate_paths:
                            candidate_paths.sort(key=lambda item: (item[0], item[1]))
                            new_p = candidate_paths[0][2]
                        else:
                            new_p = find_route_with_alternative_first_move(
                                curr, goal, blocked, forbidden, [], []
                            )
                    else:
                        new_p = find_route_with_alternative_first_move(
                            curr, goal, blocked, forbidden, robot["recent_nodes"], robot["recovery_history"]
                        )
                        if not new_p:
                            new_p = find_route_with_alternative_first_move(
                                curr, goal, blocked, forbidden, [], []
                            )

                    if not new_p or len(new_p) < 2:
                        robot["recovery_cooldown"] = 1
                        continue

                    rec_move = (curr, new_p[1])
                    rev_move = (new_p[1], curr)
                    if rec_move in reserved_first_moves or rev_move in reserved_first_moves:
                        robot["recovery_cooldown"] = 1
                        continue

                    reserved_first_moves.add(rec_move)
                    reserved_first_moves.add(rev_move)
                    robot["recovery_history"].append(rec_move)
                    if len(robot["recovery_history"]) > 8:
                        robot["recovery_history"].pop(0)

                    robot["path"] = new_p
                    robot["path_index"] = 0
                    robot["waiting_steps"] = 0
                    robot["recovery_cooldown"] = 2
                    rec.append(robot["robot_id"])
                recovery_invocations += len(rec)

            # -------------------------------------------------------------
            # Movement Resolution
            # -------------------------------------------------------------
            if algorithm_name == "Baseline":
                reqs, approved = resolve_simultaneous_moves(active_robots, t)
            else:
                reqs, approved = resolve_simultaneous_moves_improved(active_robots, t)

            # Independent Safety Verification
            try:
                check_movement_safety(active_robots, approved, reqs)
            except AssertionError:
                safety_violations += 1

            # Update state & metrics
            pending_updates = []
            for r in active_robots:
                rid = r["robot_id"]
                if rid not in reqs:
                    continue
                if rid in approved:
                    r["waiting_steps"] = 0
                    successful_movements += 1
                    pending_updates.append(r)
                else:
                    r["waiting_steps"] += 1
                    r["total_waiting_steps"] += 1
                    blocked_movements += 1

            for r in pending_updates:
                nxt = reqs[r["robot_id"]]
                r["current_node"] = nxt
                r["path_index"] += 1
                r["recent_nodes"].append(nxt)
                if len(r["recent_nodes"]) > RECENT_NODE_LIMIT:
                    r["recent_nodes"].pop(0)

                if r["current_node"] == r["original_goal"]:
                    r["completed"] = True
                    completed_robots += 1
                    total_completion_time += (t + 1)

        # Sum total waiting steps accumulated across all robots in this scenario
        total_waiting_steps += sum(r["total_waiting_steps"] for r in robots)

    elapsed_time = time.perf_counter() - start_time
    total_moves = blocked_movements + successful_movements
    congestion_pct = (blocked_movements / total_moves * 100) if total_moves else 0.0
    completion_rate = (completed_robots / total_robots * 100) if total_robots else 0.0
    avg_waiting_steps = (total_waiting_steps / total_robots) if total_robots else 0.0
    avg_completion_time = (total_completion_time / completed_robots) if completed_robots else 0.0
    avg_route_length = (total_route_length / total_robots) if total_robots else 0.0

    summary = {
        "algorithm": algorithm_name,
        "total_scenarios": TOTAL_SCENARIOS,
        "total_robots": total_robots,
        "completed_robots": completed_robots,
        "incomplete_robots": total_robots - completed_robots,
        "task_completion_rate": round(completion_rate, 2),
        "total_waiting_steps": total_waiting_steps,
        "average_waiting_steps": round(avg_waiting_steps, 2),
        "blocked_movements": blocked_movements,
        "successful_movements": successful_movements,
        "congestion_percentage": round(congestion_pct, 2),
        "average_completion_time_steps": round(avg_completion_time, 2),
        "deadlock_recovery_invocations": recovery_invocations,
        "average_route_length": round(avg_route_length, 2),
        "safety_violations": safety_violations,
        "simulation_time_seconds": round(elapsed_time, 3)
    }

    return summary


def run_all_benchmarks():
    experiments = [
        "Baseline",
        "Improved Resolver",
        "Improved Recovery",
        "ML-Assisted"
    ]

    all_summaries = []
    for exp in experiments:
        res = run_experiment(exp, seed=42)
        all_summaries.append(res)
        print(f"[{exp}] -> Completion: {res['task_completion_rate']}% | Incomplete: {res['incomplete_robots']} | Congestion: {res['congestion_percentage']}% | Wait: {res['total_waiting_steps']} | Time: {res['simulation_time_seconds']}s")

    df_summary = pd.DataFrame(all_summaries)
    csv_path = OUTPUT_DIR / "benchmark_comparison_summary.csv"
    df_summary.to_csv(csv_path, index=False)

    json_path = OUTPUT_DIR / "benchmark_comparison_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=4)

    print("\n" + "=" * 80)
    print("BENCHMARK COMPARISON SUMMARY TABLE")
    print("=" * 80)
    print(df_summary.to_string(index=False))
    print("=" * 80)
    print(f"Results saved to:\n  {csv_path}\n  {json_path}")


if __name__ == "__main__":
    run_all_benchmarks()
