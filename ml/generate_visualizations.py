"""
Publication-Quality Data Visualization Suite for Multi-Robot Fleet Coordination.

Generates 10 comprehensive scientific charts saved to results/charts/:
1. Task Completion Rate Comparison
2. Successful vs. Blocked Movements
3. Average and Total Waiting Steps by Algorithm
4. Congestion Rate by Fleet Size (Robot Count)
5. Scenario-Level Incomplete Robot Distribution
6. ML Confusion Matrix (Test Set)
7. ML Feature Importance
8. Deadlock Recovery Invocations Comparison
9. Execution Time and Throughput Comparison
10. ML Model Performance Comparison (Accuracy, Precision, Recall, F1, ROC-AUC)
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure matplotlib uses a non-interactive backend
matplotlib.use("Agg")
sns.set_theme(style="whitegrid", palette="deep")

OUTPUT_CHARTS_DIR = ROOT_DIR / "results" / "charts"
OUTPUT_CHARTS_DIR.mkdir(parents=True, exist_ok=True)

BENCHMARK_CSV = ROOT_DIR / "data" / "experiments" / "benchmark_comparison_summary.csv"
ML_METRICS_JSON = ROOT_DIR / "data" / "experiments" / "ml_evaluation_metrics.json"
FEATURE_IMP_CSV = ROOT_DIR / "ml" / "models" / "feature_importances.csv"
DATASET_V2_CSV = ROOT_DIR / "data" / "raw" / "simulation_data_v2.csv"
ROBOT_REPORT_CSV = ROOT_DIR / "data" / "raw" / "scenario_robot_report.csv"


def plot_completion_rate_comparison(df_bench: pd.DataFrame):
    plt.figure(figsize=(8, 5))
    bars = plt.bar(
        df_bench["algorithm"],
        df_bench["task_completion_rate"],
        color=["#2b5c8f", "#3c8dbc", "#46a546", "#f39c12"],
        width=0.55,
        edgecolor="black",
        linewidth=0.8
    )
    plt.title("Fleet Task Completion Rate Across Coordination Strategies", fontsize=13, fontweight="bold", pad=12)
    plt.ylabel("Task Completion Rate (%)", fontsize=11)
    plt.xlabel("Coordination Algorithm", fontsize=11)
    plt.ylim(90, 101)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h + 0.3, f"{h:.2f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "1_completion_rate_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_movements_breakdown(df_bench: pd.DataFrame):
    plt.figure(figsize=(8, 5))
    x = np.arange(len(df_bench))
    width = 0.35

    plt.bar(x - width/2, df_bench["successful_movements"], width, label="Successful Movements", color="#2ca02c", edgecolor="black")
    plt.bar(x + width/2, df_bench["blocked_movements"], width, label="Blocked / Congested Movements", color="#d62728", edgecolor="black")

    plt.title("Movement Outcomes: Successful vs. Blocked Attempts", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Coordination Algorithm", fontsize=11)
    plt.ylabel("Movement Event Count", fontsize=11)
    plt.xticks(x, df_bench["algorithm"])
    plt.legend(frameon=True)
    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "2_movements_breakdown.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_waiting_time_comparison(df_bench: pd.DataFrame):
    fig, ax1 = plt.subplots(figsize=(8, 5))
    color1 = "#1f77b4"
    color2 = "#ff7f0e"

    x = np.arange(len(df_bench))
    width = 0.35

    b1 = ax1.bar(x - width/2, df_bench["total_waiting_steps"], width, color=color1, label="Total Waiting Steps", edgecolor="black")
    ax1.set_ylabel("Total Fleet Waiting Steps", color=color1, fontsize=11, fontweight="bold")
    ax1.set_xlabel("Coordination Algorithm", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_bench["algorithm"])

    ax2 = ax1.twinx()
    b2 = ax2.bar(x + width/2, df_bench["average_waiting_steps"], width, color=color2, label="Avg Waiting Steps / AMR", edgecolor="black")
    ax2.set_ylabel("Average Waiting Steps per AMR", color=color2, fontsize=11, fontweight="bold")
    ax2.grid(False)

    plt.title("Fleet Waiting Overhead by Algorithm", fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    out = OUTPUT_CHARTS_DIR / "3_waiting_time_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_congestion_by_fleet_size(df_v2: pd.DataFrame):
    plt.figure(figsize=(7, 5))
    grouped = df_v2.groupby("robot_count")["is_congested"].agg(["count", "mean"]).reset_index()
    grouped["congestion_pct"] = grouped["mean"] * 100

    bars = plt.bar(grouped["robot_count"], grouped["congestion_pct"], color="#9467bd", width=0.5, edgecolor="black")
    plt.title("Congestion Probability vs. Fleet Size (AMR Count)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Simultaneous Active Robots in Warehouse", fontsize=11)
    plt.ylabel("Congestion Probability (%)", fontsize=11)
    plt.xticks(grouped["robot_count"])
    plt.ylim(0, 100)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "4_congestion_by_fleet_size.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_scenario_failure_distribution(df_rep: pd.DataFrame):
    plt.figure(figsize=(7, 5))
    failed = df_rep[df_rep["completed"] == 0]
    sc_counts = failed.groupby("scenario_id").size().value_counts().sort_index()

    bars = plt.bar(sc_counts.index.astype(str), sc_counts.values, color="#e377c2", width=0.45, edgecolor="black")
    plt.title("Failure Concentration: Incomplete AMRs per Failing Scenario", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of Incomplete Robots in Scenario", fontsize=11)
    plt.ylabel("Number of Scenarios", fontsize=11)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h + 0.1, str(int(h)), ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "5_scenario_failure_distribution.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_ml_confusion_matrix(metrics_data: dict):
    plt.figure(figsize=(6, 5))
    best_model = metrics_data["best_model"]
    cm = np.array(metrics_data["models"][best_model]["confusion_matrix"])

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Clear (0)", "Congested (1)"],
        yticklabels=["Clear (0)", "Congested (1)"]
    )
    plt.title(f"Test Set Confusion Matrix ({best_model})", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Predicted Label", fontsize=11)
    plt.ylabel("True Label", fontsize=11)
    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "6_ml_confusion_matrix.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_ml_feature_importance(df_imp: pd.DataFrame):
    plt.figure(figsize=(8, 5))
    top_df = df_imp.head(10).iloc[::-1]

    plt.barh(top_df["feature"], top_df["importance"], color="#17becf", edgecolor="black")
    plt.title("Top 10 Feature Importances in Congestion Risk Model", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Gini / Mean Decrease Impurity", fontsize=11)
    plt.ylabel("Feature", fontsize=11)
    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "7_ml_feature_importance.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_recovery_invocations(df_bench: pd.DataFrame):
    plt.figure(figsize=(7, 5))
    bars = plt.bar(
        df_bench["algorithm"],
        df_bench["deadlock_recovery_invocations"],
        color="#bcbd22",
        width=0.5,
        edgecolor="black"
    )
    plt.title("Deadlock Recovery Trigger Frequency Across Algorithms", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Coordination Algorithm", fontsize=11)
    plt.ylabel("Recovery Passes Executed", fontsize=11)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h + 15, str(int(h)), ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "8_recovery_invocations_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_execution_time(df_bench: pd.DataFrame):
    plt.figure(figsize=(7, 5))
    bars = plt.bar(
        df_bench["algorithm"],
        df_bench["simulation_time_seconds"],
        color="#8c564b",
        width=0.5,
        edgecolor="black"
    )
    plt.title("Simulation Runtime Efficiency (500 Scenarios Batch)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Coordination Algorithm", fontsize=11)
    plt.ylabel("Wall-Clock Execution Time (Seconds)", fontsize=11)

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, h + 0.03, f"{h:.2f}s", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "9_execution_efficiency.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def plot_ml_models_comparison(metrics_data: dict):
    plt.figure(figsize=(9, 5))
    models = [m for m in metrics_data["models"].keys() if isinstance(metrics_data["models"][m], dict)]
    metrics = ["accuracy", "precision", "recall", "f1_score"]

    x = np.arange(len(models))
    width = 0.18

    for i, metric in enumerate(metrics):
        values = [metrics_data["models"][m][metric] * 100 for m in models]
        plt.bar(x + (i - 1.5) * width, values, width, label=metric.replace("_", " ").title(), edgecolor="black")

    plt.title("Machine Learning Models Comparative Evaluation (Test Set)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Machine Learning Algorithm", fontsize=11)
    plt.ylabel("Score (%)", fontsize=11)
    plt.xticks(x, models)
    plt.ylim(70, 105)
    plt.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    out = OUTPUT_CHARTS_DIR / "10_ml_models_comparison.png"
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"Saved: {out.name}")


def generate_all_visualizations():
    print("=" * 60)
    print("GENERATING SCIENTIFIC PERFORMANCE CHARTS")
    print("=" * 60)

    if BENCHMARK_CSV.exists():
        df_bench = pd.read_csv(BENCHMARK_CSV)
        plot_completion_rate_comparison(df_bench)
        plot_movements_breakdown(df_bench)
        plot_waiting_time_comparison(df_bench)
        plot_recovery_invocations(df_bench)
        plot_execution_time(df_bench)

    if DATASET_V2_CSV.exists():
        df_v2 = pd.read_csv(DATASET_V2_CSV)
        plot_congestion_by_fleet_size(df_v2)

    if ROBOT_REPORT_CSV.exists():
        df_rep = pd.read_csv(ROBOT_REPORT_CSV)
        plot_scenario_failure_distribution(df_rep)

    if ML_METRICS_JSON.exists():
        with open(ML_METRICS_JSON, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
        plot_ml_confusion_matrix(metrics_data)
        plot_ml_models_comparison(metrics_data)

    if FEATURE_IMP_CSV.exists():
        df_imp = pd.read_csv(FEATURE_IMP_CSV)
        plot_ml_feature_importance(df_imp)

    print("=" * 60)
    print(f"All 10 charts generated successfully in {OUTPUT_CHARTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_visualizations()
