"""
Interactive Real-Time Warehouse AMR Fleet Simulation Engine.

Provides live state management, step-by-step execution, real-time animation streaming,
multi-algorithm conflict resolution, ML congestion risk estimation, and WebSocket broadcasts.
"""

import asyncio
import random
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from backend.app.planning.warehouse_graph import create_warehouse_graph, WAREHOUSE_COORDINATES
from ml.simulate_warehouse_v2 import (
    GRAPH,
    shortest_path,
    alternative_path,
    find_route_with_alternative_first_move,
    initiate_deadlock_recovery,
    resolve_simultaneous_moves,
    TOTAL_SCENARIOS,
    MAX_TIME_STEPS,
    RECENT_NODE_LIMIT,
)
from tests.test_coordination import resolve_simultaneous_moves_improved
from tests.test_coordination_helpers import check_movement_safety
from ml.ml_coordination import MLCongestionAdvisor, ml_congestion_aware_path

ROBOT_COLORS = {
    "AMR-01": "#38bdf8",  # Sky blue
    "AMR-02": "#fbbf24",  # Amber
    "AMR-03": "#34d399",  # Emerald
    "AMR-04": "#f87171",  # Rose
    "AMR-05": "#a78bfa",  # Violet
}


class SimulationService:
    def __init__(self):
        self.is_running: bool = False
        self.speed_ms: int = 1000
        self.time_step: int = 0
        self.algorithm: str = "Improved Resolver"
        self.scenario_id: int = 1
        self.fleet_size: int = 4
        self.robots: List[Dict[str, Any]] = []
        self.events_history: List[Dict[str, Any]] = []
        self.successful_movements: int = 0
        self.blocked_movements: int = 0
        self.total_waiting_steps: int = 0
        self.deadlock_recovery_invocations: int = 0
        self.safety_violations: int = 0
        self.ml_advisor = MLCongestionAdvisor()
        self._loop_task: Optional[asyncio.Task] = None
        self._ws_listeners: Set[Any] = set()

        # Initialize default simulation
        self.reset(fleet_size=4, algorithm="Improved Resolver", scenario_id=1)

    def register_listener(self, ws):
        self._ws_listeners.add(ws)

    def unregister_listener(self, ws):
        self._ws_listeners.discard(ws)

    async def broadcast(self, payload: Dict[str, Any]):
        to_remove = set()
        for ws in self._ws_listeners:
            try:
                await ws.send_json(payload)
            except Exception:
                to_remove.add(ws)
        self._ws_listeners -= to_remove

    def _create_initial_robots(self, fleet_size: int, scenario_id: int) -> List[Dict[str, Any]]:
        rnd = random.Random(scenario_id * 101 + fleet_size)
        nodes = list(GRAPH.keys())
        starts = rnd.sample(nodes, fleet_size)
        robots = []

        for i in range(fleet_size):
            rid = f"AMR-0{i + 1}"
            start = starts[i]
            available_goals = [n for n in nodes if n != start]
            goal = rnd.choice(available_goals)

            if self.algorithm == "ML-Assisted" and self.ml_advisor.is_available:
                path = ml_congestion_aware_path(
                    GRAPH, start, goal, set(), self.ml_advisor,
                    robot_count=fleet_size, occupied_count=fleet_size, time_step=0
                )
                if not path:
                    path = shortest_path(start, goal)
            else:
                path = shortest_path(start, goal)

            robots.append({
                "robot_id": rid,
                "current_node": start,
                "original_goal": goal,
                "path": path,
                "path_index": 0,
                "waiting_steps": 0,
                "total_waiting_steps": 0,
                "completed": False,
                "color": ROBOT_COLORS.get(rid, "#38bdf8"),
                "battery_percent": round(rnd.uniform(85.0, 99.0), 1),
                "recent_nodes": [start],
                "recovery_history": [],
                "recovery_cooldown": 0,
            })
        return robots

    def reset(self, fleet_size: int = 4, algorithm: str = "Improved Resolver", scenario_id: int = 1):
        self.is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            self._loop_task = None

        self.fleet_size = max(2, min(5, fleet_size))
        self.algorithm = algorithm
        self.scenario_id = scenario_id
        self.time_step = 0
        self.successful_movements = 0
        self.blocked_movements = 0
        self.total_waiting_steps = 0
        self.deadlock_recovery_invocations = 0
        self.safety_violations = 0
        self.events_history = []

        self.robots = self._create_initial_robots(self.fleet_size, self.scenario_id)
        self.events_history.append({
            "time_step": 0,
            "event_type": "simulation_reset",
            "message": f"Simulation reset with {self.fleet_size} robots using '{self.algorithm}' (Scenario {self.scenario_id}).",
            "timestamp": "T0"
        })
        return self.get_state()

    def set_speed(self, speed_ms: int):
        self.speed_ms = max(100, min(5000, speed_ms))
        return {"speed_ms": self.speed_ms}

    def start(self):
        if not self.is_running:
            self.is_running = True
            if self._loop_task is None or self._loop_task.done():
                self._loop_task = asyncio.create_task(self._simulation_loop())
        return self.get_state()

    def pause(self):
        self.is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            self._loop_task = None
        return self.get_state()

    def resume(self):
        return self.start()

    async def _simulation_loop(self):
        try:
            while self.is_running:
                active = [r for r in self.robots if not r["completed"]]
                if not active:
                    self.is_running = False
                    self.events_history.insert(0, {
                        "time_step": self.time_step,
                        "event_type": "all_tasks_completed",
                        "message": "All robots have successfully completed their delivery tasks!",
                        "timestamp": f"T{self.time_step}"
                    })
                    await self.broadcast({"type": "state_update", "data": self.get_state()})
                    break

                self.step()
                await self.broadcast({"type": "state_update", "data": self.get_state()})
                await asyncio.sleep(self.speed_ms / 1000.0)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.is_running = False
            self.events_history.insert(0, {
                "time_step": self.time_step,
                "event_type": "simulation_error",
                "message": f"Simulation loop stopped unexpectedly: {str(e)}",
                "timestamp": f"T{self.time_step}"
            })
            await self.broadcast({"type": "state_update", "data": self.get_state()})

    def step(self) -> Dict[str, Any]:
        """Execute exactly one simulation step."""
        active_robots = [r for r in self.robots if not r["completed"]]
        if not active_robots:
            return self.get_state()

        self.time_step += 1
        t = self.time_step
        occupied_nodes = {r["current_node"] for r in active_robots}

        # 1. Deadlock Recovery Handling
        rec_ids = []
        if self.algorithm in ("Baseline", "Improved Resolver"):
            rec = initiate_deadlock_recovery(active_robots)
            rec_ids = [r["robot_id"] if isinstance(r, dict) else str(r) for r in rec]
            for rid in rec_ids:
                self.events_history.insert(0, {
                    "time_step": t,
                    "event_type": "deadlock_recovery",
                    "robot_id": rid,
                    "message": f"{rid} recovered from deadlock using alternate routing",
                    "timestamp": f"T{t}"
                })
        elif self.algorithm in ("Improved Recovery", "ML-Assisted"):
            recovering = sorted(
                [r for r in active_robots if r["waiting_steps"] >= 3],
                key=lambda r: (-r["waiting_steps"], r["robot_id"])
            )
            reserved_first_moves = set()
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

                new_p = find_route_with_alternative_first_move(
                    curr, goal, blocked, forbidden, robot["recent_nodes"], robot["recovery_history"]
                )
                if not new_p:
                    new_p = find_route_with_alternative_first_move(
                        curr, goal, blocked, forbidden, [], []
                    )

                if new_p and len(new_p) >= 2:
                    rec_move = (curr, new_p[1])
                    rev_move = (new_p[1], curr)
                    if rec_move not in reserved_first_moves and rev_move not in reserved_first_moves:
                        reserved_first_moves.add(rec_move)
                        reserved_first_moves.add(rev_move)
                        robot["recovery_history"].append(rec_move)
                        if len(robot["recovery_history"]) > 8:
                            robot["recovery_history"].pop(0)
                        robot["path"] = new_p
                        robot["path_index"] = 0
                        robot["waiting_steps"] = 0
                        robot["recovery_cooldown"] = 2
                        rec_ids.append(robot["robot_id"])
                        self.events_history.insert(0, {
                            "time_step": t,
                            "event_type": "deadlock_recovery",
                            "robot_id": robot["robot_id"],
                            "message": f"{robot['robot_id']} recovered from deadlock: rerouted to {new_p}",
                            "timestamp": f"T{t}"
                        })

        self.deadlock_recovery_invocations += len(rec_ids)

        # 2. Movement Resolution
        if self.algorithm == "Baseline":
            reqs, approved = resolve_simultaneous_moves(active_robots, t)
        else:
            reqs, approved = resolve_simultaneous_moves_improved(active_robots, t)

        # 3. Safety Verification
        try:
            check_movement_safety(active_robots, approved, reqs)
        except AssertionError as e:
            self.safety_violations += 1
            self.events_history.insert(0, {
                "time_step": t,
                "event_type": "safety_alert",
                "message": f"Safety invariant violation prevented: {e}",
                "timestamp": f"T{t}"
            })

        # 4. State Updates
        pending_updates = []
        for r in active_robots:
            rid = r["robot_id"]
            if rid not in reqs:
                continue

            dest = reqs[rid]
            if rid in approved:
                r["waiting_steps"] = 0
                self.successful_movements += 1
                pending_updates.append((r, dest))
                self.events_history.insert(0, {
                    "time_step": t,
                    "event_type": "movement",
                    "robot_id": rid,
                    "from_node": r["current_node"],
                    "to_node": dest,
                    "message": f"{rid} moved from {r['current_node']} to {dest}",
                    "timestamp": f"T{t}"
                })
            else:
                r["waiting_steps"] += 1
                r["total_waiting_steps"] += 1
                self.blocked_movements += 1
                self.total_waiting_steps += 1
                self.events_history.insert(0, {
                    "time_step": t,
                    "event_type": "blocked",
                    "robot_id": rid,
                    "node": r["current_node"],
                    "requested_node": dest,
                    "message": f"{rid} waiting at {r['current_node']} (conflict on {dest})",
                    "timestamp": f"T{t}"
                })

        for r, nxt in pending_updates:
            r["current_node"] = nxt
            r["path_index"] += 1
            r["recent_nodes"].append(nxt)
            if len(r["recent_nodes"]) > RECENT_NODE_LIMIT:
                r["recent_nodes"].pop(0)

            if r["current_node"] == r["original_goal"]:
                r["completed"] = True
                self.events_history.insert(0, {
                    "time_step": t,
                    "event_type": "goal_reached",
                    "robot_id": r["robot_id"],
                    "node": nxt,
                    "message": f"{r['robot_id']} arrived at destination node {nxt}! Delivery complete.",
                    "timestamp": f"T{t}"
                })

        # Keep latest 60 events in memory
        self.events_history = self.events_history[:60]
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """Compute full snapshot of simulation state."""
        active = [r for r in self.robots if not r["completed"]]
        completed = [r for r in self.robots if r["completed"]]

        occupied = {}
        for r in active:
            occupied[r["current_node"]] = r["robot_id"]

        # Predict candidate requests
        next_requests = {}
        for r in active:
            idx = r.get("path_index", 0)
            path = r.get("path", [])
            if idx + 1 < len(path):
                next_requests[r["robot_id"]] = path[idx + 1]

        # Robot representations
        robots_view = []
        for r in self.robots:
            rid = r["robot_id"]
            robots_view.append({
                "robot_id": rid,
                "current_node": r["current_node"],
                "goal": r["original_goal"],
                "path": r["path"],
                "path_index": r["path_index"],
                "next_node": next_requests.get(rid),
                "waiting_steps": r["waiting_steps"],
                "total_waiting_steps": r["total_waiting_steps"],
                "completed": r["completed"],
                "color": r["color"],
                "battery_percent": r["battery_percent"],
                "status": "COMPLETED" if r["completed"] else ("WAITING" if r["waiting_steps"] > 0 else "MOVING"),
            })

        total_moves = self.successful_movements + self.blocked_movements
        congestion_pct = round((self.blocked_movements / total_moves * 100.0), 1) if total_moves > 0 else 0.0
        avg_waiting = round(self.total_waiting_steps / max(len(self.robots), 1), 2)

        return {
            "is_running": self.is_running,
            "speed_ms": self.speed_ms,
            "time_step": self.time_step,
            "algorithm": self.algorithm,
            "scenario_id": self.scenario_id,
            "fleet_size": self.fleet_size,
            "robots": robots_view,
            "active_robots_count": len(active),
            "completed_robots_count": len(completed),
            "occupied_nodes": occupied,
            "requested_moves": next_requests,
            "metrics": {
                "successful_movements": self.successful_movements,
                "blocked_movements": self.blocked_movements,
                "total_waiting_steps": self.total_waiting_steps,
                "deadlock_recovery_invocations": self.deadlock_recovery_invocations,
                "safety_violations": self.safety_violations,
                "congestion_percentage": congestion_pct,
                "average_waiting_steps": avg_waiting,
                "completion_rate": round(len(completed) / max(len(self.robots), 1) * 100.0, 1),
            },
            "recent_events": self.events_history,
        }


# Singleton service instance
simulation_service = SimulationService()

