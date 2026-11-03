
import pandas as pd
from pathlib import Path

INPUT_FILE = (
    Path(__file__).resolve().parents[1]
    / "data" / "raw" / "simulation_data.csv"
)

df = pd.read_csv(INPUT_FILE)

print("\n========== DATASET OVERVIEW ==========")
print("Total records:", len(df))
print("Total scenarios:", df["scenario_id"].nunique())
print("Unique robots:", df["robot_id"].nunique())

print("\n========== FIRST 10 RECORDS ==========")
print(df.head(10).to_string(index=False))

print("\n========== DATA TYPES ==========")
print(df.dtypes)

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== CONGESTION DISTRIBUTION ==========")
print(df["is_congested"].value_counts())
print("\nCongestion percentage:")
print(df["is_congested"].value_counts(normalize=True) * 100)

print("\n========== MOVEMENT DELAY SUMMARY ==========")
print(df["movement_delay"].describe())

print("\n========== ROBOT COUNT DISTRIBUTION ==========")
print(df["robot_count"].value_counts().sort_index())

print("\nDataset inspection completed.")
