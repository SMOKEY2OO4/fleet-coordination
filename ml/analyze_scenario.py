
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. FILE CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[1]

FILE_PATH = (
    ROOT_DIR
    / "data"
    / "raw"
    / "simulation_data_v2.csv"
)

SCENARIO_ID = 264


# --------------------------------------------------
# 2. LOAD DATASET
# --------------------------------------------------

if not FILE_PATH.exists():
    raise FileNotFoundError(
        f"Simulation dataset not found: {FILE_PATH}"
    )

df = pd.read_csv(FILE_PATH)

print("\nAVAILABLE CSV COLUMNS:")
print(df.columns.tolist())

scenario = df[
    df["scenario_id"] == SCENARIO_ID
].sort_values("time_step")


# --------------------------------------------------
# 3. SCENARIO ANALYSIS
# --------------------------------------------------

print(
    f"\n========== SCENARIO {SCENARIO_ID} ANALYSIS =========="
)

print("Dataset:", FILE_PATH)
print("Total movement records:", len(scenario))

if scenario.empty:
    print("No records found for this scenario.")
    raise SystemExit


# --------------------------------------------------
# 4. ROBOT-WISE ANALYSIS
# --------------------------------------------------

failed_robot_ids = ["AMR-02", "AMR-03", "AMR-04", "AMR-05"]

print("\nAnalyzing failed robots only...")

for robot_id in failed_robot_ids:

    robot = scenario[
        scenario["robot_id"] == robot_id
    ].sort_values("time_step")

    if robot.empty:
        print(f"\nNo records found for {robot_id}")
        continue

    print(f"\n========== {robot_id} ==========")

    columns = [
        "time_step",
        "current_node",
        "next_node",
        "occupied_nodes",
        "competing_requests",
        "waiting_steps",
        "movement_delay",
        "is_congested",
        "move_successful"
    ]

    print("\nFIRST 15 RECORDS:")

    print(
        robot[columns]
        .head(15)
        .to_string(index=False)
    )

    print("\nLAST 10 RECORDS:")

    print(
        robot[columns]
        .tail(10)
        .to_string(index=False)
    )

    successful_moves = robot["move_successful"].sum()

    blocked_attempts = (
        robot["move_successful"] == 0
    ).sum()

    print("\nSuccessful moves:", successful_moves)
    print("Blocked attempts:", blocked_attempts)

    print(
        "Total waiting steps:",
        robot["waiting_steps"].sum()
    )

    print(
        "Congested records:",
        robot["is_congested"].sum()
    )

# --------------------------------------------------
# 5. TIME-STEP CONGESTION ANALYSIS
# --------------------------------------------------

print("\n========== TIME-STEP CONGESTION ANALYSIS ==========")

for t in range(15):

    step_data = scenario[
        scenario["time_step"] == t
    ].sort_values("robot_id")

    print(f"\nTIME STEP {t}")

    print(
        step_data[
            [
                "robot_id",
                "current_node",
                "next_node",
                "competing_requests",
                "move_successful"
            ]
        ].to_string(index=False)
    )


# --------------------------------------------------
# 5. SCENARIO SUMMARY
# --------------------------------------------------

print("\n========== SCENARIO SUMMARY ==========")

print(
    "Total robots:",
    scenario["robot_id"].nunique()
)

print(
    "Robots analyzed:",
    len(failed_robot_ids)
)

print(
    "Total successful moves:",
    scenario["move_successful"].sum()
)

print(
    "Total blocked attempts:",
    (scenario["move_successful"] == 0).sum()
)

print("\nAnalysis completed.")
