
import pandas as pd
from pathlib import Path

INPUT_FILE = (
    Path(__file__).resolve().parents[1]
    / "data" / "raw" / "simulation_data_v2.csv"
)

df = pd.read_csv(INPUT_FILE)

print("\n========== DATASET OVERVIEW ==========")
print("Total records:", len(df))
print("Unique scenarios:", df["scenario_id"].nunique())
print("Unique robots:", df["robot_id"].nunique())

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== CONGESTION DISTRIBUTION ==========")
print(df["is_congested"].value_counts())
print(df["is_congested"].value_counts(normalize=True) * 100)

print("\n========== MOVEMENT SUCCESS ==========")
print(df["move_successful"].value_counts())

print("\n========== WAITING STATISTICS ==========")
print(df["waiting_steps"].describe())

print("\n========== COMPETING REQUESTS ==========")
print(df["competing_requests"].value_counts().sort_index())

print("\n========== RECORDS PER SCENARIO ==========")
print(df.groupby("scenario_id").size().describe())

print("\n========== FIRST 10 RECORDS ==========")
print(df.head(10).to_string(index=False))

print("\nInspection completed.")
