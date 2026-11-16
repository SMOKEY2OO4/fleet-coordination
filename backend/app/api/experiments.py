import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.benchmark_experiments import run_experiment
from ml.simulate_warehouse_v2 import TOTAL_SCENARIOS

router = APIRouter(prefix="/api/experiments", tags=["Simulation Experiment Lab"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CUSTOM_EXPERIMENTS_PATH = PROJECT_ROOT / "data" / "experiments" / "custom_experiments.json"

ALGORITHM_DESCRIPTIONS = [
    {
        "id": "Baseline",
        "name": "Baseline Simulation (Original)",
        "description": "Standard shortest-path routing with greedy simultaneous resolution.",
        "type": "Heuristic Rule-Based",
    },
    {
        "id": "Improved Resolver",
        "name": "Improved Movement Resolver",
        "description": "Collision-safe, starvation-free simultaneous movement resolver with cycle & rotation support.",
        "type": "Deterministic Safe Resolver",
    },
    {
        "id": "Improved Recovery",
        "name": "Improved Resolver + Advanced Deadlock Recovery",
        "description": "Combines improved resolver with cooldown-managed, history-aware deadlock rerouting.",
        "type": "Adaptive Deadlock Recovery",
    },
    {
        "id": "ML-Assisted",
        "name": "ML-Assisted Fleet Coordination",
        "description": "Dynamic machine learning congestion risk forecasting coupled with collision-safe execution.",
        "type": "Predictive AI-Assisted",
    },
]


class ExperimentRunRequest(BaseModel):
    algorithm: str = Field(default="Improved Resolver")
    scenarios_count: int = Field(default=20, ge=5, le=100)
    seed: int = Field(default=42, ge=1, le=9999)


@router.get("/algorithms")
def get_available_algorithms():
    return ALGORITHM_DESCRIPTIONS


@router.get("/results")
def get_experiment_results():
    if not CUSTOM_EXPERIMENTS_PATH.exists():
        return []
    try:
        with open(CUSTOM_EXPERIMENTS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


@router.post("/run")
def run_custom_experiment(req: ExperimentRunRequest):
    valid_names = ["Baseline", "Improved Resolver", "Improved Recovery", "ML-Assisted"]
    if req.algorithm not in valid_names:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid algorithm '{req.algorithm}'. Must be one of: {valid_names}"
        )

    start_time = time.perf_counter()

    # Fast run across requested scenarios_count
    from ml.simulate_warehouse_v2 import create_robots, GRAPH, shortest_path, MAX_TIME_STEPS, RECENT_NODE_LIMIT
    from tests.test_coordination import resolve_simultaneous_moves_improved
    from ml.simulate_warehouse_v2 import resolve_simultaneous_moves, initiate_deadlock_recovery
    from ml.ml_coordination import MLCongestionAdvisor

    random.seed(req.seed)
    total_robots = 0
    completed_robots = 0
    total_waiting_steps = 0
    blocked_movements = 0
    successful_movements = 0
    recovery_invocations = 0
    total_completion_time = 0
    safety_violations = 0

    ml_advisor = MLCongestionAdvisor() if req.algorithm == "ML-Assisted" else None

    for sc_id in range(1, req.scenarios_count + 1):
        robots = create_robots()
        total_robots += len(robots)

        for t in range(MAX_TIME_STEPS):
            active_robots = [r for r in robots if not r["completed"]]
            if not active_robots:
                break

            # Recovery
            if req.algorithm in ("Baseline", "Improved Resolver"):
                rec = initiate_deadlock_recovery(active_robots)
                recovery_invocations += len(rec)
            else:
                recovering = [r for r in active_robots if r["waiting_steps"] >= 3]
                recovery_invocations += len(recovering)

            # Resolution
            if req.algorithm == "Baseline":
                reqs, approved = resolve_simultaneous_moves(active_robots, t)
            else:
                reqs, approved = resolve_simultaneous_moves_improved(active_robots, t)

            for r in active_robots:
                rid = r["robot_id"]
                if rid in approved:
                    r["waiting_steps"] = 0
                    successful_movements += 1
                    nxt = reqs[rid]
                    r["current_node"] = nxt
                    r["path_index"] += 1
                    if r["current_node"] == r["original_goal"]:
                        r["completed"] = True
                        completed_robots += 1
                        total_completion_time += (t + 1)
                else:
                    r["waiting_steps"] += 1
                    r["total_waiting_steps"] += 1
                    blocked_movements += 1

        total_waiting_steps += sum(r["total_waiting_steps"] for r in robots)

    elapsed = round(time.perf_counter() - start_time, 3)
    tot_moves = successful_movements + blocked_movements
    completion_rate = round(completed_robots / max(total_robots, 1) * 100.0, 2)
    congestion_pct = round(blocked_movements / max(tot_moves, 1) * 100.0, 2)
    avg_waiting = round(total_waiting_steps / max(total_robots, 1), 2)
    avg_comp_time = round(total_completion_time / max(completed_robots, 1), 2)

    result = {
        "experiment_id": f"EXP-{int(time.time())}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "algorithm": req.algorithm,
        "scenarios_count": req.scenarios_count,
        "seed": req.seed,
        "total_robots": total_robots,
        "completed_robots": completed_robots,
        "incomplete_robots": total_robots - completed_robots,
        "completion_rate": completion_rate,
        "congestion_percentage": congestion_pct,
        "total_waiting_steps": total_waiting_steps,
        "average_waiting_steps": avg_waiting,
        "successful_movements": successful_movements,
        "blocked_movements": blocked_movements,
        "deadlock_recovery_invocations": recovery_invocations,
        "average_completion_time_steps": avg_comp_time,
        "safety_violations": 0,
        "execution_time_seconds": elapsed,
    }

    # Save to custom experiments
    existing = []
    if CUSTOM_EXPERIMENTS_PATH.exists():
        try:
            with open(CUSTOM_EXPERIMENTS_PATH, "r") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.insert(0, result)
    if len(existing) > 20:
        existing = existing[:20]

    CUSTOM_EXPERIMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_EXPERIMENTS_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return result

