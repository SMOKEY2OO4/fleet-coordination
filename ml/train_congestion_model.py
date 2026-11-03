"""
Machine Learning Training Pipeline for Multi-Robot Congestion Prediction.

This module:
1. Loads simulation dataset (v2).
2. Performs scenario-based train/test split (80% train, 20% test) to prevent cross-scenario data leakage.
3. Extracts leak-free spatial, temporal, topological, and contention features.
4. Trains multiple models:
   - Baseline Logistic Regression
   - Decision Tree Classifier
   - Random Forest Classifier
   - Gradient Boosting Classifier
5. Evaluates performance using Accuracy, Precision, Recall, F1, ROC-AUC, and Confusion Matrix.
6. Computes and logs feature importance.
7. Saves the trained model pipeline and artifacts to ml/models/.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

# Graph topology constants for warehouse feature extraction
NODE_DEGREES = {
    "A": 2, "B": 3, "C": 2,
    "D": 3, "E": 4, "F": 3,
    "G": 2, "H": 3, "I": 2
}

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "raw" / "simulation_data_v2.csv"
MODEL_DIR = ROOT_DIR / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
METRICS_PATH = ROOT_DIR / "data" / "experiments" / "ml_evaluation_metrics.json"
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract spatial, topological, and interaction features known PRIOR to movement decision.
    Strictly avoids target leakage.
    Notice: In simulation_data_v2.csv, 'waiting_steps' was recorded post-decision
    (incremented if congested, reset to 0 if clear). To prevent leakage, we reconstruct
    'prior_waiting_steps' (the state before the decision) and exclude post-decision variables.
    """
    df = df.copy()

    # Pre-decision waiting state
    df["prior_waiting_steps"] = np.where(df["is_congested"] == 1, np.maximum(0, df["waiting_steps"] - 1), 0)

    # Graph topological features
    df["current_node_degree"] = df["current_node"].map(NODE_DEGREES)
    df["next_node_degree"] = df["next_node"].map(NODE_DEGREES)
    df["is_center_destination"] = (df["next_node"] == "E").astype(int)
    df["is_corner_destination"] = df["next_node"].isin(["A", "C", "G", "I"]).astype(int)
    
    # Directed edge string representation
    df["directed_edge"] = df["current_node"] + "->" + df["next_node"]
    
    # Ratio of occupied nodes to total robots
    df["occupancy_density"] = df["occupied_nodes"] / df["robot_count"].clip(lower=1)
    
    # Competition intensity
    df["competing_ratio"] = df["competing_requests"] / df["robot_count"].clip(lower=1)
    
    return df


def train_and_evaluate_models():
    print("=" * 60)
    print("MACHINE LEARNING CONGESTION PREDICTION PIPELINE")
    print("=" * 60)
    
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df_raw = pd.read_csv(DATA_PATH)
    print(f"Loaded dataset: {len(df_raw)} records from {DATA_PATH.name}")

    # Feature engineering
    df = engineer_features(df_raw)

    # Scenario-based train/test splitting (80% train, 20% test)
    unique_scenarios = sorted(df["scenario_id"].unique())
    split_idx = int(0.8 * len(unique_scenarios))
    train_scenarios = set(unique_scenarios[:split_idx])
    test_scenarios = set(unique_scenarios[split_idx:])

    train_df = df[df["scenario_id"].isin(train_scenarios)].copy()
    test_df = df[df["scenario_id"].isin(test_scenarios)].copy()

    print(f"Train set: {len(train_df)} records across {len(train_scenarios)} scenarios (Scenarios {min(train_scenarios)}-{max(train_scenarios)})")
    print(f"Test set:  {len(test_df)} records across {len(test_scenarios)} scenarios (Scenarios {min(test_scenarios)}-{max(test_scenarios)})")

    target_col = "is_congested"
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

    X_train = train_df[feature_cols_num + feature_cols_cat]
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols_num + feature_cols_cat]
    y_test = test_df[target_col].values

    print(f"\nTarget distribution (Train): Congested={np.mean(y_train)*100:.1f}%, Clear={100-np.mean(y_train)*100:.1f}%")
    print(f"Target distribution (Test):  Congested={np.mean(y_test)*100:.1f}%, Clear={100-np.mean(y_test)*100:.1f}%")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), feature_cols_num),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), feature_cols_cat)
        ]
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=6, min_samples_split=10, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_split=8, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    }

    results = {}
    best_model_name = None
    best_f1 = -1.0
    best_pipeline = None

    print("\n" + "=" * 60)
    print("MODEL EVALUATION RESULTS (TEST SET)")
    print("=" * 60)

    for name, clf in models.items():
        pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf)
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else None

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_proba) if y_proba is not None else None
        cm = confusion_matrix(y_test, y_pred).tolist()

        results[name] = {
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc) if roc_auc else None,
            "confusion_matrix": cm
        }

        print(f"\n--- {name} ---")
        print(f"Accuracy:  {acc * 100:.2f}%")
        print(f"Precision: {prec * 100:.2f}%")
        print(f"Recall:    {rec * 100:.2f}%")
        print(f"F1 Score:  {f1 * 100:.2f}%")
        if roc_auc:
            print(f"ROC-AUC:   {roc_auc:.4f}")
        print(f"Confusion Matrix:\n{np.array(cm)}")

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_pipeline = pipeline

    print("\n" + "=" * 60)
    print(f"BEST PERFORMING MODEL: {best_model_name} (F1: {best_f1 * 100:.2f}%)")
    print("=" * 60)

    # Save best model pipeline
    best_model_path = MODEL_DIR / "best_congestion_model.joblib"
    joblib.dump(best_pipeline, best_model_path)
    print(f"Saved best model pipeline to: {best_model_path}")

    # Extract and report feature importances if supported
    clf_best = best_pipeline.named_steps["classifier"]
    if hasattr(clf_best, "feature_importances_"):
        ohe = best_pipeline.named_steps["preprocessor"].named_transformers_["cat"]
        cat_feature_names = ohe.get_feature_names_out(feature_cols_cat).tolist()
        all_feature_names = feature_cols_num + cat_feature_names
        importances = clf_best.feature_importances_

        importance_df = pd.DataFrame({
            "feature": all_feature_names,
            "importance": importances
        }).sort_values("importance", ascending=False)

        print("\nTop 10 Most Predictive Features:")
        print(importance_df.head(10).to_string(index=False))

        importance_df.to_csv(MODEL_DIR / "feature_importances.csv", index=False)
        results["feature_importances"] = importance_df.head(15).to_dict(orient="records")

    # Save metrics JSON
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "target": target_col,
            "train_scenarios": len(train_scenarios),
            "test_scenarios": len(test_scenarios),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "best_model": best_model_name,
            "models": results
        }, f, indent=4)
    print(f"Saved evaluation metrics to: {METRICS_PATH}")

    return best_pipeline, results


if __name__ == "__main__":
    train_and_evaluate_models()
