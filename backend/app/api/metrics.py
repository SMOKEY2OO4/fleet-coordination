import csv
import io
import json

from fastapi.responses import StreamingResponse
from fastapi import APIRouter

from backend.app.core.metrics import (
    get_movement_metrics,
    clear_movement_metrics,
)

router = APIRouter(
    prefix="/metrics",
    tags=["Movement Metrics"],
)


@router.get("/")
def get_metrics():
    events = get_movement_metrics()

    return {
        "total_events": len(events),
        "events": events,
    }


@router.delete("/")
def delete_metrics():
    clear_movement_metrics()

    return {
        "success": True,
        "message": "Movement metrics cleared.",
    }

@router.get("/export")
def export_metrics_csv():
    events = get_movement_metrics()

    output = io.StringIO()

    fieldnames = [
        "timestamp",
        "robot_id",
        "task_id",
        "event_type",
        "current_node",
        "next_node",
        "planned_path",
        "details",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for event in events:
        row = event.copy()

        row["planned_path"] = json.dumps(
            row["planned_path"]
        )

        row["details"] = json.dumps(
            row["details"]
        )

        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=movement_metrics.csv"
        },
    )
