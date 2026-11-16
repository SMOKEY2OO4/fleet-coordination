# FLEETIQ — Intelligent Warehouse Fleet Management Platform

An industrial-grade Autonomous Mobile Robot (AMR) multi-agent coordination, collision resolution, and machine learning congestion intelligence platform designed for high-density warehouse fulfillment environments.

Developed as a Final Year Engineering / Computer Science Capstone Project.

---

## 1. System Architecture

```
fleet-coordination/
│
├── frontend/                            # Industrial FleetIQ React 19 + TypeScript + Tailwind Web App
│   ├── src/
│   │   ├── components/                  # Reusable UI & Warehouse Visualization Elements
│   │   │   ├── layout/                  # Sidebar, TopNavbar, Main Layout Shell
│   │   │   ├── ui/                      # StatCard, Badge, Modal, Loading Skeleton
│   │   │   └── warehouse/               # 2D Interactive Map, Live Event Feed, Controls, Drawer
│   │   ├── pages/                       # 9 Complete Industrial Fleet Management Pages
│   │   │   ├── DashboardPage.tsx        # Page 1: Executive Overview Dashboard
│   │   │   ├── WarehouseControlPage.tsx # Page 2: Live Warehouse Control Centre (2D Canvas)
│   │   │   ├── FleetManagementPage.tsx  # Page 3: Robot Fleet Management
│   │   │   ├── TaskManagementPage.tsx   # Page 4: Logistics Task Allocation & Tracking
│   │   │   ├── CoordinationMonitorPage  # Page 5: Intelligent Coordination & Conflict Monitor
│   │   │   ├── MLIntelligencePage.tsx   # Page 6: Machine Learning Congestion Intelligence
│   │   │   ├── PerformanceAnalyticsPage # Page 7: Performance Analytics & Benchmarks
│   │   │   ├── ExperimentLabPage.tsx    # Page 8: Simulation Experiment Lab
│   │   │   └── SystemSettingsPage.tsx   # Page 9: System Architecture & Infrastructure
│   │   ├── services/                    # Centralized Axios API & WebSocket Telemetry Client
│   │   └── types/                       # Shared Domain TypeScript Interfaces
│   └── package.json                     # Vite + Tailwind + Recharts + Framer Motion toolchain
│
├── backend/                             # Real-Time Fleet REST API & WebSocket Server
│   ├── app/
│   │   ├── api/                         # FastAPI Endpoints (robots, routes, tasks, warehouse, simulation, ml, experiments)
│   │   ├── coordination/                # Mutex-Locked Node/Edge Reservation Manager
│   │   ├── core/                        # In-Memory State & Metric Logging
│   │   ├── models/                      # Pydantic Domain Schemas (Robot, Task, Simulation)
│   │   ├── planning/                    # Manhattan A* & Warehouse Graph (A-I 9-Node Topology)
│   │   ├── services/                    # Movement Dispatch & Real-Time Simulation Engine
│   │   └── main.py                      # FastAPI Application Entrypoint & Static SPA Mount
│   └── tests/                           # Backend Unit Tests (Planning, Movement, API Extensions)
│
├── data/
│   ├── baseline/                        # Preserved Baseline Datasets (Immutable Reference)
│   ├── raw/                             # Simulation Data (v1, v2, robot reports, event logs)
│   └── experiments/                     # Benchmark Summaries, ML Metrics JSON & Custom Experiments
│
├── ml/                                  # Machine Learning & Simulation
│   ├── models/                          # Serialized ML Pipelines (.joblib) & Feature Importances
│   ├── simulate_warehouse_v2.py         # Advanced Multi-Robot Baseline Simulator
│   ├── train_congestion_model.py        # Leak-Free ML Training Pipeline (4 Classifiers)
│   ├── ml_coordination.py               # ML-Assisted Congestion-Aware Routing Engine
│   ├── benchmark_experiments.py         # Controlled 4-Algorithm Comparative Benchmark
│   └── generate_visualizations.py       # Publication-Grade Chart Generator (10 Charts)
│
├── simulator/                           # Visual Simulation Utilities
│   └── warehouse_visualizer.py          # Animated Simulation Matplotlib & Frame Renderer
│
├── launch_platform.py                   # Unified Single-Command Development Platform Launcher
├── run_project.py                       # Automated End-to-End Pipeline & Test Runner (37 Tests)
└── pytest.ini                           # Test Configuration
```

---

## 2. Warehouse Grid Topology

The warehouse is modeled as a standardized 9-node bidirectional topological graph on a 3×3 grid:

```
[A] (0, 0) ===== [B] (1, 0) ===== [C] (2, 0)   (Inbound Receiving Docks)
     ||               ||               ||
[D] (0, 1) ===== [E] (1, 1) ===== [F] (2, 1)   (Central Transit Arteries & Hub E)
     ||               ||               ||
[G] (0, 2) ===== [H] (1, 2) ===== [I] (2, 2)   (Outbound Sorting Depots)
```

- **Vertices ($V=9$)**: Nodes A through I with specified logistics roles.
- **Edges ($E=24$ directed, 12 bidirectional)**: High-throughput aisles between adjacent coordinates.
- **Central Intersection Hub (Node `E`)**: Degree 4 crossway exhibiting peak contention and bottleneck risk.

---

## 3. Platform Capabilities & Complete Pages

1. **Executive Overview Dashboard (`/`)**:
   - Fleet KPIs: Total, active, idle robots, and utilization rate.
   - Task metrics: Total, completed, queued, and delivery completion rate.
   - Congestion level and average waiting steps.
   - Hourly movement volume area chart and AMR status distribution pie chart.
   - 4-algorithm benchmark quick-summary comparison.

2. **Live Warehouse Control Centre (`/live-control`)**:
   - High-fidelity interactive 2D SVG canvas rendering nodes A–I and all connecting arteries.
   - Real-time animated AMR movement transitions with direction vectors.
   - Controllable via Start, Pause, Resume, Reset, Speed selector (0.5x, 1x, 2x, 4x), and Single-step execution.
   - Live event feed categorized by movements, conflicts, and deadlock recovery events.
   - Interactive robot drawer showing position, destination, battery SOC, and active route.

3. **Robot Fleet Management (`/fleet`)**:
   - Commission new simulated or physical AMRs at any valid warehouse node.
   - Real-time search by AMR ID and status filtering (IDLE, ASSIGNED, MOVING, WAITING).
   - Advance robot movement by single step and decommission/delete robots cleanly.

4. **Logistics Task Allocation (`/tasks`)**:
   - Create delivery missions specifying origin node, destination node, and priority (HIGH, MEDIUM, LOW).
   - Dispatch available idle AMRs automatically using the task allocator.
   - Track progress from QUEUED to ASSIGNED, IN_PROGRESS, and COMPLETED.
   - Cancel pending tasks safely and release associated AMR resources.

5. **Intelligent Coordination Monitor (`/coordination`)**:
   - Vertex and edge conflict prevention invariants explained and verified.
   - Contention arbitration metrics: Approved moves, blocked moves, and deadlock recovery triggers.
   - Starvation-free priority order and rotational cycle detection.
   - In-memory movement metrics log audit table with CSV export.

6. **Machine Learning Intelligence (`/ml-intelligence`)**:
   - Trained Decision Tree classifier pipeline achieving **89.84% accuracy, 94.69% precision, and 0.9466 ROC-AUC**.
   - Test set confusion matrix display ($1,023$ TN, $72$ FP, $189$ FN, $1,285$ TP).
   - Top predictive feature importances chart (occupancy density, prior waiting steps, center destination, etc.).
   - Interactive candidate movement prediction inspector calculating $P(\text{Congestion} \mid u \to v)$ in real-time.

7. **Performance Analytics & Benchmarks (`/analytics`)**:
   - Controlled 4-algorithm benchmark results comparing Baseline, Improved Resolver, Improved Recovery, and ML-Assisted.
   - Scientific bar charts for completion rate, movement breakdown, and deadlock recovery invocations.
   - Algorithm matrix highlighting optimal empirical results across all 11 scientific metrics.

8. **Simulation Experiment Lab (`/experiment-lab`)**:
   - Empirical experiment interface allowing custom runs with selected algorithms, scenario counts (5–50), and seeds.
   - Live execution metrics and safety invariant verification.
   - Isolated results storage (`data/experiments/custom_experiments.json`) preserving baseline benchmark purity.

9. **System Architecture & Settings (`/settings`)**:
   - Real-time service connectivity check for FastAPI, WebSocket stream, and ML pipeline.
   - Swagger API documentation link (`/docs`).
   - Platform specifications and safety invariants audit.

---

## 4. Quick Launch Instructions

### Option A: Unified Launcher (Starts Frontend + Backend)

To launch the complete application with a single command:

```powershell
.venv\Scripts\python launch_platform.py
```

This simultaneously starts:
- **FastAPI Backend**: `http://127.0.0.1:8000`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Frontend Dashboard (Dev)**: `http://localhost:5173`
- **Integrated Production SPA**: `http://127.0.0.1:8000/app`

### Option B: Independent Service Startup

**Terminal 1 — Backend API:**
```powershell
.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend App:**
```powershell
cd frontend
npm run dev
```

### Option C: Build Production Frontend Assets

```powershell
cd frontend
npm run build
```
The compiled assets will be built into `frontend/dist/` and automatically served by FastAPI at `http://127.0.0.1:8000/app`.

---

## 5. Verification & Automated Tests

Run the full end-to-end demonstration and test suite:

```powershell
.venv\Scripts\python run_project.py
```

Or run pytest directly:

```powershell
.venv\Scripts\pytest -v
```

### Current Test Suite Status:
- **Total Tests Collected**: 37 automated tests
- **Tests Passing**: 37 passed (100%)
- **Safety Invariant Violations**: 0
- **Categories Covered**:
  - Manhattan A* routing and obstacle avoidance
  - Collision prevention (vertex exclusion, head-on swap prevention)
  - Circular rotational shifts ($\ge 3$ AMRs)
  - Stationary obstacle blocking and movement chains
  - Deadlock recovery and cooldown-managed rerouting
  - ML advisor inference bounds and fallback resilience
  - REST API lifecycle (robots, tasks, warehouse, simulation, ML predictions, experiments)
