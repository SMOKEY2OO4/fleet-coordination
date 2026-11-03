
from fastapi import FastAPI

from backend.app.api.routes import router as routes_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.robots import router as robots_router
from backend.app.api.metrics import router as metrics_router
app = FastAPI(
    title="AMR Fleet Coordination API",
    description="Backend for warehouse robot fleet coordination.",
    version="0.1.0",
)

# Register API routers
app.include_router(routes_router)
app.include_router(tasks_router)
app.include_router(robots_router)
app.include_router(metrics_router)

@app.get("/")
def root():
    return {
        "message": "AMR Fleet Coordination API is running",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
