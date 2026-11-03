import pandas as pd
from pathlib import Path

# Locate the project directory
ROOT_DIR = Path(__file__).resolve().parents[1]

FILE_PATH = (
    ROOT_DIR
    / "data"
    / "raw"
    / "scenario_robot_report.csv"
)

# Load report
df = pd.read_csv(FILE_PATH)

# Separate completed and incomplete robots
failed = df[df["completed"] == 0]
completed = df[df["completed"] == 1]

print("\n========== FAILURE ANALYSIS ==========")

print("Total robots:", len(df))
print("Completed robots:", len(completed))
print("Incomplete robots:", len(failed))

print("\n========== FAILURE RATE ==========")

failure_rate = len(failed) / len(df) * 100
print(f"Failure rate: {failure_rate:.2f}%")

print("\n========== INCOMPLETE ROBOT DETAILS ==========")

columns = [
    "scenario_id",
    "robot_id",
    "start_node",
    "goal_node",
    "final_node",
    "waiting_steps",
    "total_waiting_steps",
    "path_index",
    "path_length",
    "temporary_goal"
]

print(failed[columns].to_string(index=False))

print("\n========== TOTAL WAITING STATISTICS ==========")

if not failed.empty:
    print(failed["total_waiting_steps"].describe())

print("\n========== FAILURE BY WAITING TIME ==========")

if not failed.empty:
    print(
        failed["total_waiting_steps"]
        .value_counts()
        .sort_index()
    )

print("\n========== SCENARIOS WITH MOST FAILURES ==========")

print(
    failed.groupby("scenario_id")
    .size()
    .sort_values(ascending=False)
    .head(10)
)

print("\n========== ROUTE PROGRESS ANALYSIS ==========")

if not failed.empty:
    failed["route_progress"] = (
        failed["path_index"] /
        failed["path_length"].clip(lower=1)
    ) * 100

    print(
        failed[
            [
                "scenario_id",
                "robot_id",
                "route_progress",
                "total_waiting_steps"
            ]
        ].to_string(index=False)
    )