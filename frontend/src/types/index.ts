export interface WarehouseNode {
  id: string;
  x: number;
  y: number;
}

export interface WarehouseEdge {
  from: string;
  to: string;
  weight: number;
}

export interface Robot {
  robot_id: string;
  robot_type: string;
  current_node: string;
  status: 'IDLE' | 'ASSIGNED' | 'MOVING' | 'WAITING' | 'CHARGING' | 'FAULT' | 'COMPLETED';
  current_task_id?: string | null;
  battery_percent: number;
  goal?: string;
  next_node?: string;
  path?: string[];
  path_index?: number;
  waiting_steps?: number;
  total_waiting_steps?: number;
  completed?: boolean;
  color?: string;
}

export interface Task {
  task_id: string;
  start_node: string;
  destination_node: string;
  status: 'QUEUED' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'FAILED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  assigned_robot_id?: string | null;
}

export interface WarehouseStatus {
  total_robots: number;
  active_robots: number;
  idle_robots: number;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  congested_nodes: string[];
  occupied_nodes: string[];
  system_health: string;
}

export interface SimulationEvent {
  time_step: number;
  event_type: string;
  robot_id?: string;
  message: string;
  timestamp: string;
  from_node?: string;
  to_node?: string;
  node?: string;
  requested_node?: string;
}

export interface SimulationState {
  is_running: boolean;
  speed_ms: number;
  time_step: number;
  algorithm: string;
  scenario_id: number;
  fleet_size: number;
  robots: Robot[];
  active_robots_count: number;
  completed_robots_count: number;
  occupied_nodes: Record<string, string>;
  requested_moves: Record<string, string>;
  metrics: {
    successful_movements: number;
    blocked_movements: number;
    total_waiting_steps: number;
    deadlock_recovery_invocations: number;
    safety_violations: number;
    congestion_percentage: number;
    average_waiting_steps: number;
    completion_rate: number;
  };
  recent_events: SimulationEvent[];
}

export interface BenchmarkSummary {
  algorithm: string;
  total_scenarios: number;
  total_robots: number;
  completed_robots: number;
  incomplete_robots: number;
  task_completion_rate: number;
  total_waiting_steps: number;
  average_waiting_steps: number;
  blocked_movements: number;
  successful_movements: number;
  congestion_percentage: number;
  average_completion_time_steps: number;
  deadlock_recovery_invocations: number;
  average_route_length: number;
  safety_violations: number;
  simulation_time_seconds: number;
}

export interface MLModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  confusion_matrix: number[][];
}

export interface MLMetricsResponse {
  target: string;
  train_scenarios: number;
  test_scenarios: number;
  train_samples: number;
  test_samples: number;
  best_model: string;
  models: Record<string, MLModelMetrics>;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface PredictionResult {
  candidate_edge: string;
  current_node: string;
  next_node: string;
  congestion_probability: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH';
  recommendation: string;
  features: {
    robot_count: number;
    occupied_nodes: number;
    competing_requests: number;
    waiting_steps: number;
    current_node_degree: number;
    next_node_degree: number;
    is_center_destination: number;
  };
  timestamp: string;
}

export interface ExperimentResult {
  experiment_id: string;
  timestamp: string;
  algorithm: string;
  scenarios_count: number;
  seed: number;
  total_robots: number;
  completed_robots: number;
  incomplete_robots: number;
  completion_rate: number;
  congestion_percentage: number;
  total_waiting_steps: number;
  average_waiting_steps: number;
  successful_movements: number;
  blocked_movements: number;
  deadlock_recovery_invocations: number;
  average_completion_time_steps: number;
  safety_violations: number;
  execution_time_seconds: number;
}

export interface AlgorithmInfo {
  id: string;
  name: string;
  description: string;
  type: string;
}

