"""
Interactive / Animated Warehouse Fleet Visualizer.

Renders the 9-node warehouse grid (A-I), connections, AMRs, paths,
real-time movements, congestion highlights, waiting status, and goal completions.
Can export animated GIF or step snapshot frames.
"""

import sys
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.planning.warehouse_graph import WAREHOUSE_COORDINATES
from ml.simulate_warehouse_v2 import GRAPH, create_robots
from tests.test_coordination import resolve_simultaneous_moves_improved

matplotlib.use("Agg")

NODE_POS = {
    # Inverted y for visual clarity: row 0 at top, row 2 at bottom
    "A": (0, 2), "B": (1, 2), "C": (2, 2),
    "D": (0, 1), "E": (1, 1), "F": (2, 1),
    "G": (0, 0), "H": (1, 0), "I": (2, 0)
}

ROBOT_COLORS = {
    "AMR-01": "#1f77b4",  # Blue
    "AMR-02": "#ff7f0e",  # Orange
    "AMR-03": "#2ca02c",  # Green
    "AMR-04": "#d62728",  # Red
    "AMR-05": "#9467bd",  # Purple
}


def simulate_scenario_for_replay(scenario_id: int, seed: int = 42, max_steps: int = 25):
    """Run a scenario and record step-by-step fleet states for visual playback."""
    import random
    random.seed(seed)
    robots = create_robots()

    history = []

    for t in range(max_steps):
        active = [r for r in robots if not r["completed"]]
        if not active:
            break

        reqs, approved = resolve_simultaneous_moves_improved(active, t)

        # Snapshot before movement
        step_state = {
            "time_step": t,
            "robots": [
                {
                    "robot_id": r["robot_id"],
                    "current_node": r["current_node"],
                    "goal": r["original_goal"],
                    "next_node": reqs.get(r["robot_id"]),
                    "is_approved": r["robot_id"] in approved,
                    "waiting_steps": r["waiting_steps"],
                    "completed": r["completed"]
                }
                for r in robots
            ]
        }
        history.append(step_state)

        # Execute
        for r in active:
            rid = r["robot_id"]
            if rid in approved:
                r["current_node"] = reqs[rid]
                r["path_index"] += 1
                r["waiting_steps"] = 0
                if r["current_node"] == r["original_goal"]:
                    r["completed"] = True
            else:
                r["waiting_steps"] += 1

    return history


def render_scenario_animation(scenario_id: int = 1, output_path: Path = None, max_steps: int = 20):
    if output_path is None:
        output_path = ROOT_DIR / "results" / f"warehouse_simulation_scenario{scenario_id}.gif"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    history = simulate_scenario_for_replay(scenario_id, seed=42, max_steps=max_steps)
    if not history:
        print("No simulation frames generated.")
        return

    fig, ax = plt.subplots(figsize=(8, 8))

    def update(frame_idx):
        ax.clear()
        state = history[frame_idx]
        t = state["time_step"]

        ax.set_title(
            f"Warehouse AMR Fleet Simulation — Scenario {scenario_id} [Time Step: {t}]",
            fontsize=13, fontweight="bold", pad=12
        )
        ax.set_xlim(-0.6, 2.6)
        ax.set_ylim(-0.6, 2.6)
        ax.set_aspect("equal")
        ax.axis("off")

        # Draw grid edges
        drawn_edges = set()
        for u in GRAPH:
            for v in GRAPH[u]:
                edge = tuple(sorted((u, v)))
                if edge not in drawn_edges:
                    drawn_edges.add(edge)
                    x1, y1 = NODE_POS[u]
                    x2, y2 = NODE_POS[v]
                    ax.plot([x1, x2], [y1, y2], color="#cccccc", linewidth=3, zorder=1)

        # Draw warehouse nodes
        for node, (x, y) in NODE_POS.items():
            circle = plt.Circle((x, y), 0.18, color="#e8ecf1", ec="#4a6984", lw=2, zorder=2)
            ax.add_patch(circle)
            ax.text(x, y, node, ha="center", va="center", fontsize=12, fontweight="bold", color="#1c2d42", zorder=3)

        # Draw robots
        occupied_nodes = {}
        for r in state["robots"]:
            if r["completed"]:
                continue
            occupied_nodes.setdefault(r["current_node"], []).append(r)

        for node, robs in occupied_nodes.items():
            x_base, y_base = NODE_POS[node]
            offset = 0.08 if len(robs) > 1 else 0.0

            for i, r in enumerate(robs):
                rid = r["robot_id"]
                col = ROBOT_COLORS.get(rid, "#333333")
                rx = x_base + (i * 0.16 - offset)
                ry = y_base + (i * 0.16 - offset)

                # Draw robot marker
                robot_circle = plt.Circle((rx, ry), 0.12, color=col, ec="black", lw=1.5, zorder=4)
                ax.add_patch(robot_circle)
                ax.text(rx, ry, rid.replace("AMR-", "R"), ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=5)

                # Movement intent arrow
                if r["next_node"] and not r["completed"]:
                    nx, ny = NODE_POS[r["next_node"]]
                    dx = (nx - rx) * 0.55
                    dy = (ny - ry) * 0.55
                    arrow_col = "#2ca02c" if r["is_approved"] else "#d62728"
                    ax.arrow(rx, ry, dx, dy, head_width=0.06, head_length=0.06, fc=arrow_col, ec=arrow_col, lw=2, zorder=6)

        # Legend / Status Panel
        active_count = sum(1 for r in state["robots"] if not r["completed"])
        comp_count = sum(1 for r in state["robots"] if r["completed"])
        ax.text(-0.5, -0.45, f"Active AMRs: {active_count} | Completed: {comp_count} | Green Arrow = Moving | Red Arrow = Blocked", fontsize=10, style="italic")

    anim = animation.FuncAnimation(fig, update, frames=len(history), interval=600, repeat=True)
    anim.save(output_path, writer="pillow", fps=1.5)
    plt.close()
    print(f"Warehouse simulation animation saved to: {output_path}")


if __name__ == "__main__":
    render_scenario_animation(scenario_id=1)
