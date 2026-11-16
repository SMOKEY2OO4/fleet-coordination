import pytest

from backend.app.core.state import robots, tasks
from backend.app.models.robot import Robot, RobotStatus, RobotType, RobotCreate
from backend.app.models.task import Task, TaskStatus, TaskCreate, TaskPriority
from backend.app.api.robots import register_robot, list_robots, get_robot, delete_robot
from backend.app.api.tasks import create_task, list_tasks, get_task, cancel_task, delete_task
from backend.app.api.warehouse import get_warehouse_graph, get_warehouse_status
from backend.app.api.analytics import get_benchmarks, get_ml_metrics, get_feature_importances
from backend.app.api.simulation import get_simulation_state, reset_simulation, step_simulation, set_simulation_speed, ResetSimulationRequest, SpeedRequest
from backend.app.api.ml import get_model_info, predict_congestion, get_prediction_history, CongestionPredictionRequest
from backend.app.api.experiments import get_available_algorithms, run_custom_experiment, ExperimentRunRequest
from backend.app.services.simulation_service import simulation_service


@pytest.fixture(autouse=True)
def clean_state():
    robots.clear()
    tasks.clear()
    yield
    robots.clear()
    tasks.clear()


def test_robot_api_lifecycle():
    # Register robot
    create_req = RobotCreate(robot_id="TEST-BOT-1", robot_type=RobotType.SIMULATED, current_node="A")
    bot = register_robot(create_req)
    assert bot.robot_id == "TEST-BOT-1"
    assert bot.current_node == "A"
    assert bot.battery_percent == 100.0

    # List robots
    all_bots = list_robots()
    assert len(all_bots) == 1
    assert all_bots[0].robot_id == "TEST-BOT-1"

    # Get robot
    fetched = get_robot("TEST-BOT-1")
    assert fetched.robot_id == "TEST-BOT-1"

    # Delete robot
    del_res = delete_robot("TEST-BOT-1")
    assert del_res["success"] is True
    assert len(list_robots()) == 0


def test_task_api_lifecycle():
    # Create task
    task_req = TaskCreate(start_node="A", destination_node="C", priority=TaskPriority.HIGH)
    task = create_task(task_req)
    assert task.start_node == "A"
    assert task.destination_node == "C"
    assert task.priority == TaskPriority.HIGH
    task_id = task.task_id

    # List tasks
    all_tasks = list_tasks()
    assert len(all_tasks) == 1

    # Cancel task
    cancel_res = cancel_task(task_id)
    assert cancel_res["success"] is True
    assert cancel_res["task"].status == TaskStatus.CANCELLED

    # Delete task
    del_res = delete_task(task_id)
    assert del_res["success"] is True
    assert len(list_tasks()) == 0


def test_warehouse_api():
    graph = get_warehouse_graph()
    assert len(graph["nodes"]) == 9
    assert len(graph["edges"]) == 12

    status = get_warehouse_status()
    assert "total_robots" in status
    assert "total_tasks" in status
    assert status["system_health"] == "healthy"


def test_analytics_api():
    benchmarks = get_benchmarks()
    assert isinstance(benchmarks, list)
    assert len(benchmarks) >= 4

    metrics = get_ml_metrics()
    assert "models" in metrics
    assert "Decision Tree" in metrics["models"]

    features = get_feature_importances()
    assert isinstance(features, list)
    assert len(features) > 0


def test_simulation_service_and_api():
    # Reset
    reset_req = ResetSimulationRequest(fleet_size=3, algorithm="Improved Resolver", scenario_id=1)
    state = reset_simulation(reset_req)
    assert len(state["robots"]) == 3
    assert state["time_step"] == 0
    assert state["algorithm"] == "Improved Resolver"

    # Step
    step_state = step_simulation()
    assert step_state["time_step"] == 1
    assert "metrics" in step_state

    # Speed
    speed_req = SpeedRequest(speed_ms=500)
    speed_res = set_simulation_speed(speed_req)
    assert speed_res["speed_ms"] == 500

    # Get state
    cur_state = get_simulation_state()
    assert cur_state["speed_ms"] == 500


def test_ml_prediction_api():
    info = get_model_info()
    assert info["model_type"] == "Decision Tree Classifier (Pipeline)"
    assert info["supported_edges_count"] == 24

    # Valid candidate move
    pred_req = CongestionPredictionRequest(
        current_node="A",
        next_node="B",
        robot_count=4,
        occupied_nodes=3,
        competing_requests=1,
        waiting_steps=0,
        time_step=2
    )
    pred = predict_congestion(pred_req)
    assert 0.0 <= pred["congestion_probability"] <= 1.0
    assert pred["risk_level"] in ("LOW", "MODERATE", "HIGH")

    # Invalid edge rejection
    with pytest.raises(Exception):
        inv_req = CongestionPredictionRequest(current_node="A", next_node="I")
        predict_congestion(inv_req)

    # History
    hist = get_prediction_history()
    assert len(hist) >= 1


def test_experiment_lab_api():
    algos = get_available_algorithms()
    assert len(algos) == 4

    run_req = ExperimentRunRequest(algorithm="Improved Resolver", scenarios_count=5, seed=42)
    res = run_custom_experiment(run_req)
    assert res["scenarios_count"] == 5
    assert "completion_rate" in res
    assert "congestion_percentage" in res
    assert res["safety_violations"] == 0
