"""
ML-Assisted Fleet Coordination Engine.

Integrates trained Machine Learning models into multi-robot fleet pathfinding
and conflict arbitration:
1. Feature extraction for real-time candidate robot movement requests.
2. Congestion risk probability inference via trained ML pipeline.
3. Congestion-aware route cost evaluation:
   Cost(u, v) = Base_Cost + alpha * P(congestion | u -> v)
4. Fallback-safe: If ML model is missing or fails, falls back seamlessly to rule-based routing.
5. Strict safety guarantee: ML guidance feeds into the collision-safe movement resolver;
   ML NEVER overrides physical collision prevention.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from collections import deque
import heapq
import numpy as np
import pandas as pd
import joblib

from ml.train_congestion_model import NODE_DEGREES, engineer_features

MODEL_PATH = Path(__file__).resolve().parent / "models" / "best_congestion_model.joblib"


ALL_EDGES = [
    ("A", "B"), ("A", "D"),
    ("B", "A"), ("B", "C"), ("B", "E"),
    ("C", "B"), ("C", "F"),
    ("D", "A"), ("D", "E"), ("D", "G"),
    ("E", "B"), ("E", "D"), ("E", "F"), ("E", "H"),
    ("F", "C"), ("F", "E"), ("F", "I"),
    ("G", "D"), ("G", "H"),
    ("H", "G"), ("H", "E"), ("H", "I"),
    ("I", "F"), ("I", "H")
]


class MLCongestionAdvisor:
    """Provides machine-learning powered congestion risk estimation and decision support."""

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.is_available = False
        self._edge_risk_cache = {}
        self._load_model()

    def _load_model(self):
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.is_available = True
        except Exception as e:
            print(f"Notice: ML model could not be loaded ({e}). Operating in rule-based fallback mode.")
            self.model = None
            self.is_available = False

    def get_all_edge_risks(
        self,
        robot_count: int,
        occupied_nodes: int,
        time_step: int
    ) -> dict:
        """
        Compute or retrieve cached congestion risk for all 24 warehouse edges in a single vector operation.
        Returns dict: {(u, v): risk_probability}.
        """
        # Bucket time step to allow effective cache reuse
        time_bucket = time_step // 5
        cache_key = (robot_count, occupied_nodes, time_bucket)

        if cache_key in self._edge_risk_cache:
            return self._edge_risk_cache[cache_key]

        if not self.is_available or self.model is None:
            risks = {}
            for u, v in ALL_EDGES:
                base = 0.1
                if v == "E":
                    base += 0.35
                elif v in ("B", "D", "F", "H"):
                    base += 0.20
                risks[(u, v)] = min(1.0, base)
            self._edge_risk_cache[cache_key] = risks
            return risks

        records = [{
            "time_step": time_bucket * 5,
            "robot_count": robot_count,
            "occupied_nodes": occupied_nodes,
            "competing_requests": 1,
            "waiting_steps": 0,
            "is_congested": 0,
            "current_node": u,
            "next_node": v
        } for u, v in ALL_EDGES]

        df = engineer_features(pd.DataFrame(records))
        feature_cols_num = [
            "time_step",
            "robot_count",
            "occupied_nodes",
            "competing_requests",
            "prior_waiting_steps",
            "current_node_degree",
            "next_node_degree",
            "is_center_destination",
            "is_corner_destination",
            "occupancy_density",
            "competing_ratio"
        ]
        feature_cols_cat = ["current_node", "next_node", "directed_edge"]
        X = df[feature_cols_num + feature_cols_cat]

        try:
            probas = self.model.predict_proba(X)[:, 1]
            risks = {ALL_EDGES[i]: float(probas[i]) for i in range(len(ALL_EDGES))}
        except Exception:
            risks = {edge: 0.5 for edge in ALL_EDGES}

        self._edge_risk_cache[cache_key] = risks
        return risks

    def predict_move_congestion_risk(
        self,
        current_node: str,
        next_node: str,
        robot_count: int,
        occupied_nodes: int,
        competing_requests: int = 1,
        prior_waiting_steps: int = 0,
        time_step: int = 0
    ) -> float:
        """
        Estimate P(is_congested = 1) for an individual edge with optional contention adjustment.
        """
        edge_risks = self.get_all_edge_risks(robot_count, occupied_nodes, time_step)
        base_risk = edge_risks.get((current_node, next_node), 0.2)
        
        # Contention boost if multiple robots compete for this destination
        if competing_requests > 1:
            base_risk = min(1.0, base_risk + 0.15 * (competing_requests - 1))
        if prior_waiting_steps > 0:
            base_risk = min(1.0, base_risk + 0.10 * min(prior_waiting_steps, 3))
            
        return base_risk


def ml_congestion_aware_path(
    graph: dict,
    start: str,
    goal: str,
    blocked_nodes: set,
    ml_advisor: MLCongestionAdvisor,
    robot_count: int,
    occupied_count: int,
    time_step: int,
    alpha: float = 3.0
) -> list:
    """
    Find minimum-cost path from start to goal where edge weights incorporate ML congestion risk:
    Cost(u, v) = 1.0 + alpha * ML_Risk(u -> v)
    """
    if start not in graph or goal not in graph:
        return []

    blocked = set(blocked_nodes)
    blocked.discard(start)
    blocked.discard(goal)

    frontier = [(0.0, start, [start])]
    visited_cost = {start: 0.0}

    while frontier:
        current_cost, current_node, path = heapq.heappop(frontier)

        if current_node == goal:
            return path

        if current_cost > visited_cost.get(current_node, float("inf")):
            continue

        for neighbor in graph[current_node]:
            if neighbor in blocked and neighbor != goal:
                continue

            # Query ML model for congestion risk on this candidate edge
            risk = ml_advisor.predict_move_congestion_risk(
                current_node=current_node,
                next_node=neighbor,
                robot_count=robot_count,
                occupied_nodes=occupied_count,
                competing_requests=1,
                prior_waiting_steps=0,
                time_step=time_step
            )

            edge_cost = 1.0 + alpha * risk
            total_cost = current_cost + edge_cost

            if total_cost < visited_cost.get(neighbor, float("inf")):
                visited_cost[neighbor] = total_cost
                heapq.heappush(frontier, (total_cost, neighbor, path + [neighbor]))

    return []
