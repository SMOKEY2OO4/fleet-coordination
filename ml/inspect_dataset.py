
import pandas as pd
import os

# Input dataset
INPUT_FILE = "data/raw/movement_metrics.csv"

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

# Load dataset
df = pd.read_csv(INPUT_FILE)

print("\n========== DATASET OVERVIEW ==========")

print("\nTotal records:", len(df))
print("\nColumns:")
print(df.columns.tolist())

print("\n========== FIRST 5 RECORDS ==========")
print(df.head())

print("\n========== DATA TYPES ==========")
print(df.dtypes)

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== EVENT DISTRIBUTION ==========")
print(df["event_type"].value_counts())

print("\n========== ROBOT ACTIVITY ==========")
print(df["robot_id"].value_counts())

print("\n========== DATASET SUMMARY ==========")
print(df.describe(include="all"))

print("\nDataset inspection completed.")

