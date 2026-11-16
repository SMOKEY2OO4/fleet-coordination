import json
import csv
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# Project root is 4 levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@router.get("/benchmarks")
def get_benchmarks():
    """Serve benchmark comparison data."""
    path = PROJECT_ROOT / "data" / "experiments" / "benchmark_comparison_summary.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Benchmark data not found.")
    with open(path, "r") as f:
        return json.load(f)


@router.get("/ml-metrics")
def get_ml_metrics():
    """Serve ML evaluation metrics."""
    path = PROJECT_ROOT / "data" / "experiments" / "ml_evaluation_metrics.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="ML metrics not found.")
    with open(path, "r") as f:
        return json.load(f)


@router.get("/feature-importances")
def get_feature_importances():
    """Serve feature importances from CSV as JSON."""
    path = PROJECT_ROOT / "ml" / "models" / "feature_importances.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Feature importances not found.")
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


@router.get("/coordination-events")
def get_coordination_events():
    """Serve movement events data."""
    path = PROJECT_ROOT / "data" / "raw" / "movement_events.json"
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)
