# Multi-Robot Fleet Coordination and Congestion Management in a Warehouse Environment

An intelligent Multi-Agent Pathfinding (MAPF) and fleet traffic management system designed for Autonomous Mobile Robots (AMRs) operating simultaneously in shared warehouse environments.

Developed as a Final Year Engineering / Computer Science Capstone Project.

---

## 1. System Overview

In automated fulfillment centers, fleets of Autonomous Mobile Robots (AMRs) share constrained navigation aisles. Without intelligent spatial and temporal coordination, AMRs suffer from vertex collisions, head-on deadlocks, mutual blocking loops, and cascading traffic congestion.

This system integrates:
1. **Discrete-Event Fleet Simulation Engine**: Simulates multi-robot operations across 500 scenarios (2–5 simultaneous AMRs) on a standardized warehouse topological graph.
2. **Provably Safe Simultaneous Movement Resolver**: Mathematical graph-theoretic resolver supporting safe circular rotations ($\ge 3$ AMRs), chain advancement, starvation-free rotating priority, and head-on swap prevention.
3. **Machine Learning Congestion Forecasting**: Leak-free ML models (Decision Tree, Logistic Regression, Random Forest, Gradient Boosting) achieving **89.84% accuracy, 94.69% precision, and 0.9466 ROC-AUC** predicting movement congestion.
4. **ML-Assisted Coordination**: Dynamic congestion-risk pricing incorporated into path generation and conflict arbitration.
5. **Real-Time FastAPI Fleet Service**: RESTful API providing asynchronous task allocation, A* path planning, and physical reservation locking.
6. **Visualization Suite**: Interactive Matplotlib simulation visualizer / animator and 10 publication-quality performance comparison charts.

---

## 2. Warehouse Environment & Topology

The warehouse is modeled as a 9-node bidirectional topological graph on a 3×3 grid:

```
[A] (0, 0) ===== [B] (1, 0) ===== [C] (2, 0)
     ||               ||               ||
[D] (0, 1) ===== [E] (1, 1) ===== [F] (2, 1)
     ||               ||               ||
[G] (0, 2) ===== [H] (1, 2) ===== [I] (2, 2)
```

- **Vertices ($V=9$)**: Picking stations, sorting depots, and intersection waypoints.
- **Edges ($E=24$ directed)**: Navigable bidirectional aisles between adjacent locations.
- **Center Bottleneck (Node `E`)**: Highest-degree intersection (degree 4) exhibiting peak traffic contention.

---

## 3. Project Architecture

```
fleet-coordination/
│
├── backend/                             # Real-Time Fleet REST API
│   ├── app/
│   │   ├── api/                         # FastAPI Endpoints (robots, routes, tasks, metrics)
│   │   ├── coordination/                # Mutex-Locked Node/Edge Reservation Manager
│   │   ├── core/                        # In-Memory State & Metric Logging
│   │   ├── models/                      # Pydantic Domain Schemas
│   │   ├── planning/                    # Manhattan A* & Warehouse Graph
│   │   ├── services/                    # Movement Dispatch Service
│   │   └── main.py                      # FastAPI Application Entrypoint
│   └── tests/                           # Backend Unit Tests (Planning & Movement)
│
├── data/
│   ├── baseline/                        # Preserved Baseline Datasets (Immutable Reference)
│   ├── raw/                             # Simulation Data (v1, v2, robot reports, event logs)
│   └── experiments/                     # Benchmark Summaries & ML Metrics JSON
│
├── ml/                                  # Machine Learning & Simulation
│   ├── models/                          # Serialized ML Pipelines (.joblib) & Feature Importances
│   ├── simulate_warehouse_v2.py         # Advanced Multi-Robot Baseline Simulator
│   ├── train_congestion_model.py        # Leak-Free ML Training Pipeline (4 Classifiers)
│   ├── ml_coordination.py               # ML-Assisted Congestion-Aware Routing Engine
│   ├── benchmark_experiments.py         # Controlled 4-Algorithm Comparative Benchmark
│   ├── generate_visualizations.py       # Publication-Grade Chart Generator (10 Charts)
│   ├── inspect_simulation_v2.py         # Dataset Diagnostics & Distribution Inspector
│   └── analyze_failures.py              # Failure Breakdown & Robot Progress Analyzer
│
├── results/
│   ├── charts/                          # 10 Generated High-Resolution Publication Charts
│   └── warehouse_simulation_scenario1.gif # Visual Animated Fleet Simulation
│
├── simulator/
│   └── warehouse_visualizer.py          # Interactive / Animation Warehouse Renderer
│
├── tests/                               # Comprehensive Automated Test Suite (30 Tests)
│   ├── test_coordination.py             # Resolver Edge Cases (Rotations, Chains, Swaps)
│   ├── test_coordination_helpers.py     # Independent Physical Safety Invariant Checker
│   └── test_system_suite.py             # End-to-End System, ML, & Reproducibility Tests
│
├── docs/                                # Technical Documentation & Presentation
│   ├── FINAL_PROJECT_REPORT.md          # 23-Section Capstone Academic Report
│   └── PROJECT_PRESENTATION.md          # 15-Slide Final Defense Guide & Viva Prep
│
├── pytest.ini                           # Pytest Environment Configuration
└── README.md                            # Comprehensive User Manual & Quickstart
```

---

## 4. Environment Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13.2, Windows 10/11)
- Virtual Environment (`.venv`)

### Installation
Activate the virtual environment:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Verify installed packages:
```powershell
python -m pytest --version
python -c "import sklearn, matplotlib, pandas, numpy; print('Environment healthy!')"
```

---

## 5. Execution Guide

### 1. Run Automated Tests
Execute the full 30-test automated verification suite:
```powershell
python -m pytest -v
```

### 2. Run Baseline Multi-Robot Simulation
Simulate 500 scenarios with the original baseline simulator:
```powershell
python ml/simulate_warehouse_v2.py
```
*Outputs: `data/raw/simulation_data_v2.csv` (10,789 records), `data/raw/scenario_robot_report.csv` (1,731 robots).*

### 3. Train Machine Learning Models
Train, evaluate, and save the leak-free congestion prediction classifiers:
```powershell
python ml/train_congestion_model.py
```
*Outputs: `ml/models/best_congestion_model.joblib`, `ml/models/feature_importances.csv`, `data/experiments/ml_evaluation_metrics.json`.*

### 4. Execute Comparative Benchmark Suite
Run identical 500-scenario seed-controlled benchmark across all 4 algorithms:
```powershell
python ml/benchmark_experiments.py
```
*Outputs: `data/experiments/benchmark_comparison_summary.csv` and `.json`.*

### 5. Generate Publication Performance Charts
Produce 10 high-resolution charts in `results/charts/`:
```powershell
python ml/generate_visualizations.py
```

### 6. Generate Warehouse Animation
Render animated GIF of fleet movement:
```powershell
python simulator/warehouse_visualizer.py
```
*Outputs: `results/warehouse_simulation_scenario1.gif`.*

### 7. Launch FastAPI Fleet Server
Start the real-time AMR coordination backend:
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
Open interactive Swagger documentation in browser at: `http://127.0.0.1:8000/docs`

---

## 6. Machine Learning Evaluation

Evaluated across **2,569 held-out test movements** from 100 unseen scenarios (Scenarios 401–500):

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---|---|---|---|---|
| **Decision Tree (Best)** | **89.84%** | **94.69%** | **87.18%** | **90.78%** | **0.9466** |
| Random Forest | 88.91% | 94.20% | 85.96% | 89.89% | 0.9366 |
| Gradient Boosting | 88.91% | 93.68% | 86.50% | 89.95% | 0.9415 |
| Logistic Regression | 87.97% | 93.63% | 84.80% | 89.00% | 0.9374 |

### Confusion Matrix (Decision Tree)
- True Negatives (Clear correctly predicted): **1,023**
- True Positives (Congestion correctly predicted): **1,285**
- False Negatives: **189**
- False Positives: **72**

---

## 7. Comparative Benchmark Results

Results across 500 identical scenarios (1,731 robots total):

| Metric | Baseline | Improved Resolver | ML-Assisted |
|---|---|---|---|
| **Task Completion Rate** | 98.27% | 98.27% | 97.57% |
| **Incomplete Robots** | 30 | 30 | 42 |
| **Safety Violations** | **0 (100% Safe)** | **0 (100% Safe)** | **0 (100% Safe)** |
| **Multi-Robot Rotations ($\ge 3$)** | Rejected | **Approved** | **Approved** |
| **Fallback Reconsideration** | No | **Yes** | **Yes** |
| **Starvation-Free Rotating Priority** | Partial | **Yes** | **Yes** |
| **Simulation Execution Time (500 sc)** | 0.099s | **0.071s (28% faster)** | 1.176s |

---

## 8. Safety Guarantees

The system implements strict physical safety invariants enforced by `check_movement_safety`:
1. **Vertex Safety**: At most one robot can occupy any node $u \in V$ at time $t$.
2. **Edge Safety**: If AMR $i$ traverses $u \to v$, no AMR $j$ can traverse $v \to u$ at time $t$.
3. **Stationary Preservation**: No robot may enter a node occupied by a stationary robot.
4. **Fail-Safe Independence**: Machine Learning provides risk heuristics, but the movement resolver independently checks and enforces physical collision boundaries.
