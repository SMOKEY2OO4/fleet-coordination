import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Activity,
  Gauge,
  Clock,
  ShieldCheck,
  User,
} from 'lucide-react';
import { Badge } from '../ui/Badge';
import { SimulationState } from '../../types';

interface TopNavbarProps {
  simulationState?: SimulationState | null;
  onStart: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
}

const titles: Record<string, { title: string; category: string }> = {
  '/': { title: 'Executive Overview Dashboard', category: 'Executive Telemetry' },
  '/live-control': { title: 'Live Warehouse Control Centre', category: 'Mission Control' },
  '/fleet': { title: 'Robot Fleet Management', category: 'Fleet Operations' },
  '/tasks': { title: 'Task Allocation & Tracking', category: 'Logistics Queue' },
  '/coordination': { title: 'Intelligent Coordination Monitor', category: 'Conflict Resolution' },
  '/ml-intelligence': { title: 'Machine Learning Intelligence', category: 'Predictive Analytics' },
  '/analytics': { title: 'Performance Analytics & Benchmarks', category: 'Scientific Evaluation' },
  '/experiment-lab': { title: 'Simulation Experiment Lab', category: 'Empirical Research' },
  '/settings': { title: 'System Architecture & Settings', category: 'Infrastructure' },
};

export const TopNavbar: React.FC<TopNavbarProps> = ({
  simulationState,
  onStart,
  onPause,
  onStep,
  onReset,
  onSpeedChange,
}) => {
  const location = useLocation();
  const current = titles[location.pathname] || { title: 'FleetIQ Platform', category: 'Overview' };
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const isRunning = simulationState?.is_running ?? false;
  const currentSpeed = simulationState?.speed_ms ?? 1000;

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-6 backdrop-blur-md">
      {/* Breadcrumb & Title */}
      <div className="flex flex-col">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <span>FleetIQ</span>
          <span>/</span>
          <span className="text-cyan-400">{current.category}</span>
        </div>
        <h1 className="text-base font-bold text-slate-100 truncate">{current.title}</h1>
      </div>

      {/* Center: Global Simulation Fast Controller */}
      <div className="hidden lg:flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/80 p-1.5 shadow-inner">
        <button
          onClick={isRunning ? onPause : onStart}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
            isRunning
              ? 'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30'
              : 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30'
          }`}
          title={isRunning ? 'Pause Simulation' : 'Run Simulation'}
        >
          {isRunning ? <Pause className="h-3.5 w-3.5 fill-current" /> : <Play className="h-3.5 w-3.5 fill-current" />}
          <span>{isRunning ? 'PAUSE' : 'RUN'}</span>
        </button>

        <button
          onClick={onStep}
          disabled={isRunning}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 disabled:opacity-40 transition-colors"
          title="Execute Single Step"
        >
          <SkipForward className="h-3.5 w-3.5" />
          <span>STEP</span>
        </button>

        <button
          onClick={onReset}
          className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          title="Reset Simulation"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>RESET</span>
        </button>

        <div className="h-4 w-[1px] bg-slate-800" />

        <div className="flex items-center gap-1.5 px-2 text-xs text-slate-400">
          <Gauge className="h-3.5 w-3.5 text-slate-500" />
          <select
            value={currentSpeed}
            onChange={(e) => onSpeedChange(Number(e.target.value))}
            className="bg-transparent text-xs text-slate-200 outline-none cursor-pointer"
          >
            <option value={2000} className="bg-slate-900 text-slate-200">0.5x (2.0s)</option>
            <option value={1000} className="bg-slate-900 text-slate-200">1.0x (1.0s)</option>
            <option value={500} className="bg-slate-900 text-slate-200">2.0x (0.5s)</option>
            <option value={250} className="bg-slate-900 text-slate-200">4.0x (0.25s)</option>
          </select>
        </div>

        <div className="h-4 w-[1px] bg-slate-800" />

        <div className="flex items-center gap-1.5 px-2 text-xs font-mono font-medium text-cyan-400">
          <span>STEP T{simulationState?.time_step ?? 0}</span>
        </div>
      </div>

      {/* Right: Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        <Badge variant="green" size="sm" pulse>
          <ShieldCheck className="h-3.5 w-3.5" />
          SYSTEM OPTIMAL
        </Badge>

        <div className="hidden sm:flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/60 px-2.5 py-1 text-xs font-mono text-slate-300">
          <Clock className="h-3.5 w-3.5 text-slate-400" />
          <span>{time}</span>
        </div>

        <div className="flex items-center gap-2 border-l border-slate-800 pl-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 font-semibold text-white shadow-sm">
            <User className="h-4 w-4" />
          </div>
          <div className="hidden xl:flex flex-col text-left">
            <span className="text-xs font-semibold text-slate-200 leading-tight">AMR Supervisor</span>
            <span className="text-[10px] text-slate-500 leading-tight">Industrial Level 4</span>
          </div>
        </div>
      </div>
    </header>
  );
};

