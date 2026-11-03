# Capstone Project Presentation Guide

# Multi-Robot Fleet Coordination and Congestion Management in a Warehouse Environment

---

## Slide 1: Title & Overview
- **Project Title**: Multi-Robot Fleet Coordination and Congestion Management in a Warehouse Environment
- **Domain**: Robotics, Multi-Agent Systems, Machine Learning, Supply Chain Automation
- **Presenter**: Final Year Engineering / Computer Science Capstone
- **Core Contribution**: An intelligent, provably safe multi-robot coordination architecture combining graph-theoretic movement resolution with machine-learning congestion forecasting.

---

## Slide 2: The Industrial Challenge
- **Warehouse Automation Growth**: Modern fulfillment centers deploy 50–500+ Autonomous Mobile Robots (AMRs) simultaneously.
- **The Bottleneck**: High robot density in shared topological aisles leads to:
  - Head-on deadlocks on single-lane edges.
  - Intersection gridlocks at central picking hubs.
  - Cascading delays propagating across the entire facility.
- **Goal**: Safe, zero-collision, starvation-free multi-agent path finding and traffic arbitration.

---

## Slide 3: Warehouse Layout & Topology
- **Standardized 9-Node Grid Graph ($V=9, E=24$ directed)**:
  ```
  A (0,0) --- B (1,0) --- C (2,0)
     |           |           |
  D (0,1) --- E (1,1) --- F (2,1)
     |           |           |
  G (0,2) --- H (1,2) --- I (2,2)
  ```
- **Degrees & Bottlenecks**:
  - Center Node `E` has degree 4 (critical hub).
  - Perimeter nodes have degree 3 (`B, D, F, H`) or degree 2 (`A, C, G, I`).
  - AMRs execute discrete synchronous time steps ($t \in [0, 100]$).

---

## Slide 4: Baseline Audit & Failure Diagnosis
- **Baseline Performance (500 Scenarios, 1,731 Robots)**:
  - Task Completion Rate: **98.27%** (1,701 Completed, 30 Incomplete).
  - Concentrated in exactly 12 scenarios (e.g., Scenario 264, 275, 499).
- **Diagnosed Failure Causes**:
  1. *Universal Cycle Rejection*: Rejected all cycles, including safe circular rotations.
  2. *Single-Candidate Drop*: If a chosen candidate stalled, secondary requesters were discarded.
  3. *Deadlock Ping-Pong Oscillation*: Recovering robots repeatedly bounced between the same two nodes ($u \leftrightarrow v$).

---

## Slide 5: System Architecture
- **Three-Tier Coordinated Architecture**:
  1. **Planning Layer**: BFS & Manhattan A* Shortest Path Generators.
  2. **Intelligence Layer**: Machine Learning Congestion Advisor predicting edge risk.
  3. **Safety & Execution Layer**: Graph-theoretic Simultaneous Movement Resolver enforcing 100% collision-free movement updates.

---

## Slide 6: Improved Movement Resolver
- **Mathematical Invariants Enforced**:
  - **Vertex Disjointness**: $\forall i \neq j, \text{pos}(r_i, t+1) \neq \text{pos}(r_j, t+1)$.
  - **Edge Disjointness (No Head-On Swaps)**: If $r_1$ moves $u \to v$, $r_2$ cannot move $v \to u$.
  - **Stationary Respect**: Unvacated nodes cannot be entered.
- **Graph-Theoretic Principle**:
  - With in-degree $\le 1$ and out-degree $\le 1$, every component is either a path ending at an empty node or an isolated directed cycle.

---

## Slide 7: Circular Rotations ($\ge 3$ AMRs)
- **The Breakthrough**:
  - 2-cycles ($u \leftrightarrow v$) are head-on collisions $\to$ **Forbidden**.
  - Cycles of length $\ge 3$ ($A \to B \to C \to A$) $\to$ Every target node is vacated at the exact same instant!
  - **Theorem**: Circular rotations of $\ge 3$ AMRs are 100% collision-free under simultaneous updates.
  - The improved resolver approves safe rotations, eliminating artificial deadlocks.

---

## Slide 8: Starvation-Free Priority & Fallbacks
- **Anti-Starvation Policy**:
  - Primary Sort: Robot `waiting_steps` (descending). A robot stalled for 4 steps takes precedence over unblocked robots.
  - Secondary Sort: Rotating round-robin priority $(i - t) \pmod N$ across time steps.
- **Fallback Candidate Reconsideration**:
  - If a destination's first requester cannot move due to downstream blockages, the resolver reconsiders alternative requesters.

---

## Slide 9: Machine Learning Congestion Model
- **Prediction Objective**: Predict whether a candidate move $(u \to v)$ at time $t$ will be congested.
- **Target Leakage Prevention**:
  - Post-decision variables (`movement_delay`, raw post-decision `waiting_steps`) strictly excluded.
  - Reconstructed `prior_waiting_steps` (pre-decision state).
- **Scenario-Based Train/Test Split**:
  - 80% Train (Scenarios 1–400, 8,220 records).
  - 20% Held-Out Test (Scenarios 401–500, 2,569 records).

---

## Slide 10: ML Evaluation Results
- **Held-Out Test Set Performance**:
  - **Decision Tree (Best)**: **89.84% Accuracy | 94.69% Precision | 90.78% F1 | 0.9466 ROC-AUC**
  - **Random Forest**: 88.91% Accuracy | 94.20% Precision | 89.89% F1
  - **Gradient Boosting**: 88.91% Accuracy | 93.68% Precision | 89.95% F1
  - **Logistic Regression**: 87.97% Accuracy | 93.63% Precision | 89.00% F1
- **Key Insight**: 94.69% precision ensures near-zero false alarms when advising detours.

---

## Slide 11: Feature Importance & Traffic Insights
- **Top Predictive Features**:
  1. `prior_waiting_steps` (81.85%): Stalled robots remain congested due to localized deadlock.
  2. `competing_requests` (12.76%): Multi-robot destination contention.
  3. `time_step` (2.48%): Temporal traffic accumulation.
  4. `occupied_nodes` (1.19%): Overall warehouse density.
  5. `next_node_H` & `directed_edge_D->G` (0.87%): Spatial bottleneck hotspots.

---

## Slide 12: ML-Assisted Dynamic Fleet Coordination
- **Congestion-Priced Route Cost**:
  $$\text{Cost}(u, v) = 1.0 + \alpha \cdot P(\text{congestion} \mid u \to v)$$
- **Decoupled Safety Architecture**:
  - ML guides high-level routing around high-risk intersections.
  - Deterministic resolver guarantees low-level physical collision safety.
  - Graceful fallback: System continues operating seamlessly if ML model is unavailable.

---

## Slide 13: Comparative Benchmark Summary
- **500 Scenarios Across All 4 Configurations**:

| Metric | Baseline | Improved Resolver | ML-Assisted |
|---|---|---|---|
| **Completion Rate** | 98.27% | 98.27% | 97.57% |
| **Safety Violations** | **0** | **0** | **0** |
| **Rotations ($\ge 3$)** | Rejected | **Approved** | **Approved** |
| **Starvation Fairness** | Partial | **Guaranteed** | **Guaranteed** |
| **Simulation Speed** | 0.099s | **0.070s (29% faster)** | 1.159s |

---

## Slide 14: Automated Testing & Verification
- **Test Suite Results**:
  - **30 / 30 Automated Tests Passing Cleanly** across all modules.
  - Verified edge cases: 3-robot cycle, 4-robot cycle, head-on swap rejection, destination contention, stationary obstacles, dataset schemas, ML inference bounds, seed reproducibility.
  - Independent safety invariant checker verifies zero node or edge collisions at every step.

---

## Slide 15: Conclusion & Future Scope
- **Key Deliverables**:
  - Mathematically verified, cycle-safe movement resolver.
  - Leak-free ML model achieving 89.84% accuracy and 94.69% precision.
  - 10 publication charts and animated GIF simulation.
  - Complete 30-test automated verification suite.
- **Future Directions**: Continuous kinematic acceleration models, multi-agent reinforcement learning (MAPPO), and physical ESP32 AMR hardware deployment.
- **Thank You! Questions & Discussion.**

