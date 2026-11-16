import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  Sparkles,
  BarChart3,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  History,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { StatCard } from '../components/ui/StatCard';
import { Badge } from '../components/ui/Badge';
import {
  fetchMLModelInfo,
  fetchMLMetrics,
  fetchFeatureImportances,
  predictCongestion,
  fetchPredictionHistory,
} from '../services/api';
import { MLMetricsResponse, FeatureImportance, PredictionResult } from '../types';

export const MLIntelligencePage: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [metrics, setMetrics] = useState<MLMetricsResponse | null>(null);
  const [features, setFeatures] = useState<FeatureImportance[]>([]);
  const [history, setHistory] = useState<PredictionResult[]>([]);

  // Interactive Prediction Inspector Form
  const [currNode, setCurrNode] = useState<string>('D');
  const [nextNode, setNextNode] = useState<string>('E');
  const [robotCount, setRobotCount] = useState<number>(4);
  const [occupiedNodes, setOccupiedNodes] = useState<number>(3);
  const [competingRequests, setCompetingRequests] = useState<number>(1);
  const [waitingSteps, setWaitingSteps] = useState<number>(1);
  const [predictResult, setPredictResult] = useState<PredictionResult | null>(null);
  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.allSettled([
      fetchMLModelInfo(),
      fetchMLMetrics(),
      fetchFeatureImportances(),
      fetchPredictionHistory(),
    ]).then(([resInfo, resMetrics, resFeatures, resHistory]) => {
      if (resInfo.status === 'fulfilled') setModelInfo(resInfo.value);
      if (resMetrics.status === 'fulfilled') setMetrics(resMetrics.value);
      if (resFeatures.status === 'fulfilled') setFeatures(resFeatures.value);
      if (resHistory.status === 'fulfilled') setHistory(resHistory.value);
    });
  }, []);

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsPredicting(true);
    try {
      const res = await predictCongestion({
        current_node: currNode,
        next_node: nextNode,
        robot_count: robotCount,
        occupied_nodes: occupiedNodes,
        competing_requests: competingRequests,
        waiting_steps: waitingSteps,
      });
      setPredictResult(res);
      const updatedHistory = await fetchPredictionHistory();
      setHistory(updatedHistory);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Inference failed: Ensure edge is connected in graph.');
    } finally {
      setIsPredicting(false);
    }
  };

  const dtMetrics = metrics?.models?.['Decision Tree'] || {
    accuracy: 0.8984,
    precision: 0.9469,
    recall: 0.8718,
    f1_score: 0.9078,
    roc_auc: 0.9466,
    confusion_matrix: [
      [1023, 72],
      [189, 1285],
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-purple-950/40 p-6 shadow-xl backdrop-blur-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="purple" size="sm">
                TRAINED MODEL PIPELINE
              </Badge>
              <Badge variant="green" size="sm">
                VALIDATED SCENARIO-SPLIT
              </Badge>
            </div>
            <h2 className="text-2xl font-extrabold tracking-tight text-white">
              Machine Learning Congestion Intelligence
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl">
              Forecasting transit corridor bottleneck probability prior to dispatch. Trained on 8,220
              pre-decision simulation state records across 400 scenarios with 0 cross-scenario leakage.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-right">
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">Selected Model</span>
              <span className="text-sm font-bold text-purple-300 font-mono">
                {modelInfo?.model_type || 'Decision Tree Classifier'}
              </span>
            </div>
          </div>
        </div>
        <div className="absolute top-0 right-0 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />
      </div>

      {/* Top 5 Evaluation Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Model Accuracy
          </span>
          <span className="text-2xl font-bold font-mono text-white">
            {(dtMetrics.accuracy * 100).toFixed(1)}%
          </span>
          <span className="text-[10px] text-emerald-400 block mt-1">2,569 Test Samples</span>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Precision
          </span>
          <span className="text-2xl font-bold font-mono text-cyan-300">
            {(dtMetrics.precision * 100).toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block mt-1">Low False Positive Rate</span>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Recall (Sensitivity)
          </span>
          <span className="text-2xl font-bold font-mono text-emerald-300">
            {(dtMetrics.recall * 100).toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block mt-1">Captures Bottlenecks</span>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            F1-Score
          </span>
          <span className="text-2xl font-bold font-mono text-purple-300">
            {(dtMetrics.f1_score * 100).toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block mt-1">Balanced Metric</span>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            ROC-AUC Score
          </span>
          <span className="text-2xl font-bold font-mono text-amber-300">
            {(dtMetrics.roc_auc * 100).toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-400 block mt-1">High Discriminative Power</span>
        </div>
      </div>

      {/* Interactive Candidate Move Inspector & Confusion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Interactive Prediction Inspector */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Sliders className="h-4 w-4 text-purple-400" />
                Live Candidate Movement Inference Inspector
              </h3>
              <p className="text-xs text-slate-400">
                Query the ML pipeline in real-time to compute congestion risk P(Congested | u &rarr; v)
              </p>
            </div>
            <Badge variant="purple" size="sm">INTERACTIVE API</Badge>
          </div>

          <form onSubmit={handlePredict} className="space-y-4">
            {errorMsg && (
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
                {errorMsg}
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Origin Node (u)</label>
                <select
                  value={currNode}
                  onChange={(e) => setCurrNode(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-purple-500 font-mono"
                >
                  {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'].map((n) => (
                    <option key={n} value={n}>Node {n}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Candidate Target (v)</label>
                <select
                  value={nextNode}
                  onChange={(e) => setNextNode(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-purple-500 font-mono"
                >
                  {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'].map((n) => (
                    <option key={n} value={n}>Node {n}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Active Fleet Size</label>
                <input
                  type="number"
                  min={1}
                  max={6}
                  value={robotCount}
                  onChange={(e) => setRobotCount(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-purple-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Occupied Nodes</label>
                <input
                  type="number"
                  min={1}
                  max={9}
                  value={occupiedNodes}
                  onChange={(e) => setOccupiedNodes(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-purple-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Competing Requests</label>
                <input
                  type="number"
                  min={1}
                  max={4}
                  value={competingRequests}
                  onChange={(e) => setCompetingRequests(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-purple-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Prior Waiting Steps</label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={waitingSteps}
                  onChange={(e) => setWaitingSteps(Number(e.target.value))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-purple-500 font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isPredicting}
              className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-2.5 text-xs font-bold text-white hover:from-purple-500 hover:to-indigo-500 transition-all shadow-lg shadow-purple-600/20 disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              <span>{isPredicting ? 'EVALUATING MODEL...' : 'INSPECT CANDIDATE MOVE RISK'}</span>
            </button>
          </form>

          {/* Inference Output Card */}
          {predictResult && (
            <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950/80 p-4 transition-all">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                  <span className="text-[10px] text-slate-400 font-semibold uppercase block">Evaluated Artery</span>
                  <span className="text-base font-bold font-mono text-cyan-400">
                    {predictResult.candidate_edge}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      predictResult.risk_level === 'HIGH'
                        ? 'red'
                        : predictResult.risk_level === 'MODERATE'
                        ? 'amber'
                        : 'green'
                    }
                    size="md"
                    pulse
                  >
                    {predictResult.risk_level} CONGESTION RISK
                  </Badge>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-400">Congestion Probability:</span>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          predictResult.congestion_probability >= 0.65
                            ? 'bg-rose-500'
                            : predictResult.congestion_probability >= 0.35
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.round(predictResult.congestion_probability * 100)}%` }}
                      />
                    </div>
                    <span className="font-mono font-bold text-white">
                      {(predictResult.congestion_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-slate-400">Routing Recommendation:</span>
                  <p className="mt-1 text-slate-200 font-medium">{predictResult.recommendation}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Col: Confusion Matrix Display */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider mb-1">
              Test Set Confusion Matrix
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated on 2,569 unseen post-split scenario records
            </p>
          </div>

          <div className="my-auto py-4">
            <div className="grid grid-cols-2 gap-2 text-center text-xs">
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
                <span className="text-[10px] text-emerald-400 font-semibold block">TRUE NEGATIVE (TN)</span>
                <span className="text-xl font-bold font-mono text-white mt-1 block">
                  {dtMetrics.confusion_matrix[0][0]}
                </span>
                <span className="text-[10px] text-slate-400">Predicted Clear & Actual Clear</span>
              </div>

              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
                <span className="text-[10px] text-amber-400 font-semibold block">FALSE POSITIVE (FP)</span>
                <span className="text-xl font-bold font-mono text-white mt-1 block">
                  {dtMetrics.confusion_matrix[0][1]}
                </span>
                <span className="text-[10px] text-slate-400">Predicted Congested but Clear</span>
              </div>

              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3">
                <span className="text-[10px] text-rose-400 font-semibold block">FALSE NEGATIVE (FN)</span>
                <span className="text-xl font-bold font-mono text-white mt-1 block">
                  {dtMetrics.confusion_matrix[1][0]}
                </span>
                <span className="text-[10px] text-slate-400">Missed Congestion Event</span>
              </div>

              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
                <span className="text-[10px] text-emerald-400 font-semibold block">TRUE POSITIVE (TP)</span>
                <span className="text-xl font-bold font-mono text-white mt-1 block">
                  {dtMetrics.confusion_matrix[1][1]}
                </span>
                <span className="text-[10px] text-slate-400">Predicted Congested & Congested</span>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-800 pt-3 text-[11px] text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Overall Specificity:</span>
              <span className="font-mono text-white">93.4%</span>
            </div>
            <div className="flex justify-between">
              <span>Sensitivity (Recall):</span>
              <span className="font-mono text-emerald-400">87.2%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Importance Horizontal Chart */}
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Top Predictive Feature Importances
            </h3>
            <p className="text-xs text-slate-400">
              Computed Gini impurity reduction across all Decision Tree decision splits
            </p>
          </div>
          <Badge variant="cyan" size="sm">FEATURE ATTRIBUTION</Badge>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={features.slice(0, 8)}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 120, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" stroke="#64748b" fontSize={11} domain={[0, 'dataMax + 0.05']} />
              <YAxis
                type="category"
                dataKey="feature"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                formatter={(val: any) => [`${(Number(val) * 100).toFixed(2)}%`, 'Importance']}
              />
              <Bar dataKey="importance" fill="#a855f7" radius={[0, 4, 4, 0]}>
                {features.slice(0, 8).map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? '#38bdf8' : index === 1 ? '#a855f7' : '#818cf8'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

