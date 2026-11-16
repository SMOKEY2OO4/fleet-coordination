import axios from 'axios';
import {
  WarehouseNode,
  WarehouseEdge,
  WarehouseStatus,
  Robot,
  Task,
  SimulationState,
  BenchmarkSummary,
  MLMetricsResponse,
  FeatureImportance,
  PredictionResult,
  ExperimentResult,
  AlgorithmInfo,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// System & Health
export const checkBackendHealth = async (): Promise<{ status: string }> => {
  const res = await api.get('/health');
  return res.data;
};

// Warehouse Topology & Status
export const fetchWarehouseGraph = async (): Promise<{ nodes: WarehouseNode[]; edges: WarehouseEdge[] }> => {
  const res = await api.get('/api/warehouse/graph');
  return res.data;
};

export const fetchWarehouseStatus = async (): Promise<WarehouseStatus> => {
  const res = await api.get('/api/warehouse/status');
  return res.data;
};

// Robots
export const fetchRobots = async (): Promise<Robot[]> => {
  const res = await api.get('/robots/');
  return res.data;
};

export const fetchRobot = async (robotId: string): Promise<Robot> => {
  const res = await api.get(`/robots/${robotId}`);
  return res.data;
};

export const registerRobot = async (data: { robot_id: string; robot_type?: string; current_node: string }): Promise<Robot> => {
  const res = await api.post('/robots/', data);
  return res.data;
};

export const moveRobot = async (robotId: string): Promise<any> => {
  const res = await api.post(`/robots/${robotId}/move`);
  return res.data;
};

export const deleteRobot = async (robotId: string): Promise<{ success: boolean; message: string }> => {
  const res = await api.delete(`/robots/${robotId}`);
  return res.data;
};

// Tasks
export const fetchTasks = async (): Promise<Task[]> => {
  const res = await api.get('/tasks/');
  return res.data;
};

export const createTask = async (data: { start_node: string; destination_node: string; priority?: 'LOW' | 'MEDIUM' | 'HIGH' }): Promise<Task> => {
  const res = await api.post('/tasks/', data);
  return res.data;
};

export const assignTask = async (taskId: string): Promise<any> => {
  const res = await api.post(`/tasks/${taskId}/assign`);
  return res.data;
};

export const cancelTask = async (taskId: string): Promise<{ success: boolean; message: string; task: Task }> => {
  const res = await api.post(`/tasks/${taskId}/cancel`);
  return res.data;
};

export const deleteTask = async (taskId: string): Promise<{ success: boolean; message: string }> => {
  const res = await api.delete(`/tasks/${taskId}`);
  return res.data;
};

// Path Planning
export const planRoute = async (start: string, goal: string, blockedEdges: [string, string][] = []): Promise<{ path: string[]; total_cost: number }> => {
  const res = await api.post('/routes/plan', { start, goal, blocked_edges: blockedEdges });
  return res.data;
};

// Movement Metrics
export const fetchMovementMetrics = async (): Promise<{ total_events: number; events: any[] }> => {
  const res = await api.get('/metrics/');
  return res.data;
};

export const clearMovementMetrics = async (): Promise<any> => {
  const res = await api.delete('/metrics/');
  return res.data;
};

export const exportMetricsCsvUrl = (): string => `${API_BASE}/metrics/export`;

// Analytics & Benchmarks
export const fetchBenchmarks = async (): Promise<BenchmarkSummary[]> => {
  const res = await api.get('/api/analytics/benchmarks');
  return res.data;
};

export const fetchMLMetrics = async (): Promise<MLMetricsResponse> => {
  const res = await api.get('/api/analytics/ml-metrics');
  return res.data;
};

export const fetchFeatureImportances = async (): Promise<FeatureImportance[]> => {
  const res = await api.get('/api/analytics/feature-importances');
  return res.data.map((item: any) => ({
    feature: item.feature,
    importance: parseFloat(item.importance) || 0,
  }));
};

export const fetchCoordinationEvents = async (): Promise<any[]> => {
  const res = await api.get('/api/analytics/coordination-events');
  return res.data;
};

// Simulation Controls
export const fetchSimulationState = async (): Promise<SimulationState> => {
  const res = await api.get('/api/simulation/state');
  return res.data;
};

export const startSimulation = async (): Promise<SimulationState> => {
  const res = await api.post('/api/simulation/start');
  return res.data;
};

export const pauseSimulation = async (): Promise<SimulationState> => {
  const res = await api.post('/api/simulation/pause');
  return res.data;
};

export const resumeSimulation = async (): Promise<SimulationState> => {
  const res = await api.post('/api/simulation/resume');
  return res.data;
};

export const stepSimulation = async (): Promise<SimulationState> => {
  const res = await api.post('/api/simulation/step');
  return res.data;
};

export const resetSimulation = async (fleetSize = 4, algorithm = 'Improved Resolver', scenarioId = 1): Promise<SimulationState> => {
  const res = await api.post('/api/simulation/reset', {
    fleet_size: fleetSize,
    algorithm,
    scenario_id: scenarioId,
  });
  return res.data;
};

export const setSimulationSpeed = async (speedMs: number): Promise<{ speed_ms: number }> => {
  const res = await api.post('/api/simulation/speed', { speed_ms: speedMs });
  return res.data;
};

// Machine Learning Intelligence
export const fetchMLModelInfo = async (): Promise<any> => {
  const res = await api.get('/api/ml/model-info');
  return res.data;
};

export const predictCongestion = async (data: {
  current_node: string;
  next_node: string;
  robot_count: number;
  occupied_nodes: number;
  competing_requests?: number;
  waiting_steps?: number;
  time_step?: number;
}): Promise<PredictionResult> => {
  const res = await api.post('/api/ml/predict-congestion', data);
  return res.data;
};

export const fetchPredictionHistory = async (): Promise<PredictionResult[]> => {
  const res = await api.get('/api/ml/prediction-history');
  return res.data;
};

// Simulation Experiment Lab
export const fetchAvailableAlgorithms = async (): Promise<AlgorithmInfo[]> => {
  const res = await api.get('/api/experiments/algorithms');
  return res.data;
};

export const fetchExperimentResults = async (): Promise<ExperimentResult[]> => {
  const res = await api.get('/api/experiments/results');
  return res.data;
};

export const runExperiment = async (data: {
  algorithm: string;
  scenarios_count: number;
  seed: number;
}): Promise<ExperimentResult> => {
  const res = await api.post('/api/experiments/run', data);
  return res.data;
};

export default api;

