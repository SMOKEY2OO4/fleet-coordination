import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.api.routes import router as routes_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.robots import router as robots_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.warehouse import router as warehouse_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.ml import router as ml_router
from backend.app.api.experiments import router as experiments_router

from backend.app.services.simulation_service import simulation_service

app = FastAPI(
    title="FleetIQ — AMR Fleet Coordination & Intelligence API",
    description="Industrial Multi-Robot Coordination and Congestion Management Platform Backend.",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(routes_router)
app.include_router(tasks_router)
app.include_router(robots_router)
app.include_router(metrics_router)
app.include_router(warehouse_router)
app.include_router(analytics_router)
app.include_router(simulation_router)
app.include_router(ml_router)
app.include_router(experiments_router)


@app.get("/")
def root():
    return {
        "message": "FleetIQ Intelligent Fleet Coordination API is running",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Mount static production frontend build if available
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/app/{full_path:path}")
    @app.get("/app")
    def serve_spa(full_path: str = ""):
        index_file = FRONTEND_DIST / "index.html"
        return FileResponse(index_file)


@app.websocket("/ws/warehouse")
@app.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket):
    await websocket.accept()
    simulation_service.register_listener(websocket)
    try:
        # Send initial state on connection
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to FleetIQ Live Warehouse Stream",
            "data": simulation_service.get_state()
        })
        while True:
            # Handle incoming client commands over WS if any
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                action = cmd.get("action")
                if action == "step":
                    state = simulation_service.step()
                    await websocket.send_json({"type": "state_update", "data": state})
                elif action == "start":
                    state = simulation_service.start()
                    await websocket.send_json({"type": "state_update", "data": state})
                elif action == "pause":
                    state = simulation_service.pause()
                    await websocket.send_json({"type": "state_update", "data": state})
                elif action == "reset":
                    state = simulation_service.reset(
                        fleet_size=cmd.get("fleet_size", 4),
                        algorithm=cmd.get("algorithm", "Improved Resolver"),
                        scenario_id=cmd.get("scenario_id", 1),
                    )
                    await websocket.send_json({"type": "state_update", "data": state})
                elif action == "get_state":
                    await websocket.send_json({"type": "state_update", "data": simulation_service.get_state()})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        simulation_service.unregister_listener(websocket)
    except Exception:
        simulation_service.unregister_listener(websocket)
