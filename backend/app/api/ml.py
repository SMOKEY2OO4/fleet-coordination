import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.ml_coordination import MLCongestionAdvisor, ALL_EDGES
from ml.train_congestion_model import NODE_DEGREES

router = APIRouter(prefix="/api/ml", tags=["Machine Learning Intelligence"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
advisor = MLCongestionAdvisor()

# In-memory prediction history
prediction_history: List[Dict[str, Any]] = []


class CongestionPredictionRequest(BaseModel):
    current_node: str = Field(default="A", min_length=1, max_length=1)
    next_node: str = Field(default="B", min_length=1, max_length=1)
    robot_count: int = Field(default=4, ge=1, le=10)
    occupied_nodes: int = Field(default=3, ge=1, le=9)
    competing_requests: int = Field(default=1, ge=1, le=5)
    waiting_steps: int = Field(default=0, ge=0, le=20)
    time_step: int = Field(default=0, ge=0)


@router.get("/model-info")
def get_model_info():
    metrics_path = PROJECT_ROOT / "data" / "experiments" / "ml_evaluation_metrics.json"
    metrics_data = {}
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            metrics_data = json.load(f)

    return {
        "model_loaded": advisor.is_available,
        "model_type": "Decision Tree Classifier (Pipeline)",
        "model_file": "best_congestion_model.joblib",
        "training_dataset": "simulation_data_v2.csv",
        "features_count": 14,
        "supported_edges_count": len(ALL_EDGES),
        "evaluation_summary": metrics_data.get("models", {}).get("Decision Tree", {
            "accuracy": 0.898,
            "precision": 0.947,
            "recall": 0.872,
            "f1_score": 0.908,
            "roc_auc": 0.947,
        }),
        "all_models_metrics": metrics_data.get("models", {}),
    }


@router.post("/predict-congestion")
def predict_congestion(req: CongestionPredictionRequest):
    edge = (req.current_node.upper(), req.next_node.upper())
    if edge not in ALL_EDGES:
        raise HTTPException(
            status_code=400,
            detail=f"Edge {req.current_node} -> {req.next_node} is not a valid warehouse path in the 9-node graph."
        )

    prob = advisor.predict_move_congestion_risk(
        current_node=edge[0],
        next_node=edge[1],
        robot_count=req.robot_count,
        occupied_nodes=req.occupied_nodes,
        competing_requests=req.competing_requests,
        prior_waiting_steps=req.waiting_steps,
        time_step=req.time_step,
    )
    prob = round(float(prob), 4)

    if prob >= 0.65:
        risk_level = "HIGH"
        recommendation = "High congestion risk: alternative detour route recommended."
    elif prob >= 0.35:
        risk_level = "MODERATE"
        recommendation = "Moderate congestion risk: proceed with coordinated reservation."
    else:
        risk_level = "LOW"
        recommendation = "Low congestion risk: optimal free transit corridor."

    result = {
        "candidate_edge": f"{edge[0]} -> {edge[1]}",
        "current_node": edge[0],
        "next_node": edge[1],
        "congestion_probability": prob,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "features": {
            "robot_count": req.robot_count,
            "occupied_nodes": req.occupied_nodes,
            "competing_requests": req.competing_requests,
            "waiting_steps": req.waiting_steps,
            "current_node_degree": NODE_DEGREES.get(edge[0], 2),
            "next_node_degree": NODE_DEGREES.get(edge[1], 2),
            "is_center_destination": 1 if edge[1] == "E" else 0,
        },
        "timestamp": time.strftime("%H:%M:%S"),
    }

    prediction_history.insert(0, result)
    if len(prediction_history) > 50:
        prediction_history.pop()

    return result


@router.get("/prediction-history")
def get_prediction_history():
    return prediction_history

