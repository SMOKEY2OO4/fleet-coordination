from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from backend.app.services.simulation_service import simulation_service

router = APIRouter(prefix="/api/simulation", tags=["Simulation Control"])


class ResetSimulationRequest(BaseModel):
    fleet_size: Optional[int] = Field(default=4, ge=2, le=5)
    algorithm: Optional[str] = "Improved Resolver"
    scenario_id: Optional[int] = 1


class SpeedRequest(BaseModel):
    speed_ms: int = Field(default=1000, ge=100, le=5000)


@router.get("/state")
def get_simulation_state():
    return simulation_service.get_state()


@router.post("/start")
async def start_simulation():
    return simulation_service.start()


@router.post("/pause")
async def pause_simulation():
    return simulation_service.pause()


@router.post("/resume")
async def resume_simulation():
    return simulation_service.resume()


@router.post("/step")
def step_simulation():
    return simulation_service.step()


@router.post("/reset")
def reset_simulation(req: ResetSimulationRequest):
    return simulation_service.reset(
        fleet_size=req.fleet_size or 4,
        algorithm=req.algorithm or "Improved Resolver",
        scenario_id=req.scenario_id or 1,
    )


@router.post("/speed")
def set_simulation_speed(req: SpeedRequest):
    return simulation_service.set_speed(req.speed_ms)

