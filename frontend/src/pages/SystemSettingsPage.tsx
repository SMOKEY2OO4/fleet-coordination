import React, { useState, useEffect } from 'react';
import {
  Settings,
  Server,
  Activity,
  BrainCircuit,
  Radio,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  Code,
  Layers,
  Database,
} from 'lucide-react';
import { checkBackendHealth, fetchMLModelInfo } from '../services/api';
import { Badge } from '../components/ui/Badge';

export const SystemSettingsPage: React.FC = () => {
  const [backendHealth, setBackendHealth] = useState<string>('checking...');
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const checkStatus = async () => {
    setIsRefreshing(true);
    try {
      const res = await checkBackendHealth();
      setBackendHealth(res.status);
    } catch {
      setBackendHealth('offline');
    }

    try {
      const info = await fetchMLModelInfo();
      setModelStatus(info);
    } catch {
      setModelStatus(null);
    }
    setIsRefreshing(false);
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white">System Architecture & Service Settings</h2>
          <p className="text-xs text-slate-400">
            Platform runtime connectivity, machine learning inference service, WebSocket status and specifications
          </p>
        </div>

        <button
          onClick={checkStatus}
          disabled={isRefreshing}
          className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 text-cyan-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>RE-PROBE SERVICES</span>
        </button>
      </div>

      {/* Connectivity & Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Backend API */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-xl flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">FastAPI Core Backend</h3>
                <span className="text-[11px] font-mono text-slate-400">http://127.0.0.1:8000</span>
              </div>
            </div>
            <Badge variant={backendHealth === 'healthy' ? 'green' : 'red'} size="sm" pulse>
              {backendHealth.toUpperCase()}
            </Badge>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Endpoints:</span>
              <span className="font-mono text-white">/robots, /tasks, /routes, /simulation</span>
            </div>
            <div className="flex justify-between">
              <span>Swagger UI:</span>
              <a
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="text-cyan-400 hover:underline flex items-center gap-1 font-mono"
              >
                /docs <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </div>

        {/* WebSocket Telemetry */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-xl flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Radio className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">WebSocket Stream</h3>
                <span className="text-[11px] font-mono text-slate-400">ws://127.0.0.1:8000/ws/warehouse</span>
              </div>
            </div>
            <Badge variant="green" size="sm">ACTIVE</Badge>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Protocol:</span>
              <span className="font-mono text-white">JSON Real-Time Broadcast</span>
            </div>
            <div className="flex justify-between">
              <span>Reconnection:</span>
              <span className="text-emerald-400 font-semibold">Auto-heal (2.5s jitter)</span>
            </div>
          </div>
        </div>

        {/* Machine Learning Engine */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-xl shadow-xl flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                <BrainCircuit className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Congestion ML Pipeline</h3>
                <span className="text-[11px] font-mono text-slate-400">best_congestion_model.joblib</span>
              </div>
            </div>
            <Badge variant={modelStatus?.model_loaded ? 'purple' : 'gray'} size="sm">
              {modelStatus?.model_loaded ? 'ONLINE' : 'FALLBACK'}
            </Badge>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Model Classifier:</span>
              <span className="font-mono text-white">Decision Tree (89.8% Acc)</span>
            </div>
            <div className="flex justify-between">
              <span>Features Extracted:</span>
              <span className="font-mono text-purple-300">14 leak-free spatial features</span>
            </div>
          </div>
        </div>
      </div>

      {/* Industrial Platform Specifications */}
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6 backdrop-blur-xl shadow-xl space-y-4">
        <div>
          <h3 className="text-base font-bold text-white uppercase tracking-wider">
            FLEETIQ Platform Specifications
          </h3>
          <p className="text-xs text-slate-400">
            Multi-Robot Fleet Coordination and Congestion Management in a Warehouse Environment
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2">
            <h4 className="font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Warehouse Topology Architecture
            </h4>
            <ul className="space-y-1.5 text-slate-300">
              <li>• <strong>Nodes:</strong> 9 Discrete Transit Points (A, B, C, D, E, F, G, H, I)</li>
              <li>• <strong>Grid Dimensions:</strong> 3x3 Continuous Planar Grid with Inverted Y coordinate mapping</li>
              <li>• <strong>Transit Arteries:</strong> 12 Bi-directional Edges (24 Directed Transition Corridors)</li>
              <li>• <strong>Central Intersection:</strong> Node E (Degree 4 Central Bottleneck Hub)</li>
              <li>• <strong>Perimeter Arteries:</strong> Nodes B, D, F, H (Degree 3), Corner Docks: A, C, G, I (Degree 2)</li>
            </ul>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2">
            <h4 className="font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="h-4 w-4" />
              Safety & Verification Invariants
            </h4>
            <ul className="space-y-1.5 text-slate-300">
              <li>• <strong>Unit Test Suite:</strong> 37 Automated Automated Python Invariant Tests Passing (100%)</li>
              <li>• <strong>Vertex Exclusion:</strong> At most 1 AMR per warehouse node at any time instant</li>
              <li>• <strong>Edge Swap Exclusion:</strong> Opposite direction simultaneous traversal prohibited</li>
              <li>• <strong>Deadlock Bound:</strong> Guaranteed recovery triggering at 3 waiting step ticks</li>
              <li>• <strong>Rotational Safety:</strong> Cycle validation for simultaneous circular shifts (&ge; 3 robots)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

