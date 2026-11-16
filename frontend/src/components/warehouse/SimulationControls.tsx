import React, { useState } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Sliders,
  Layers,
  Sparkles,
  Bot,
} from 'lucide-react';
import { SimulationState } from '../../types';

interface SimulationControlsProps {
  simulationState?: SimulationState | null;
  onStart: () => void;
  onPause: () => void;
  onStep: () => void;
  onReset: (fleetSize: number, algorithm: string, scenarioId: number) => void;
  onSpeedChange: (speed: number) => void;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  simulationState,
  onStart,
  onPause,
  onStep,
  onReset,
  onSpeedChange,
}) => {
  const isRunning = simulationState?.is_running ?? false;
  const currentAlgorithm = simulationState?.algorithm ?? 'Improved Resolver';
  const currentFleetSize = simulationState?.fleet_size ?? 4;
  const currentScenarioId = simulationState?.scenario_id ?? 1;

  const [selectedAlgo, setSelectedAlgo] = useState<string>(currentAlgorithm);
  const [selectedFleet, setSelectedFleet] = useState<number>(currentFleetSize);
  const [selectedScenario, setSelectedScenario] = useState<number>(currentScenarioId);

  const handleApplyReset = () => {
    onReset(selectedFleet, selectedAlgo, selectedScenario);
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800/90 bg-slate-900/80 p-4 backdrop-blur-xl shadow-xl">
      {/* Left: Execution Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={isRunning ? onPause : onStart}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all shadow-lg ${
            isRunning
              ? 'bg-amber-500 text-slate-950 hover:bg-amber-400 shadow-amber-500/20'
              : 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-400 hover:to-blue-500 shadow-cyan-500/20'
          }`}
        >
          {isRunning ? (
            <>
              <Pause className="h-4 w-4 fill-current" />
              <span>PAUSE SIMULATION</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-current" />
              <span>START SIMULATION</span>
            </>
          )}
        </button>

        <button
          onClick={onStep}
          disabled={isRunning}
          className="flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 disabled:opacity-40 transition-colors"
        >
          <SkipForward className="h-4 w-4 text-cyan-400" />
          <span>STEP (1 TICK)</span>
        </button>

        <button
          onClick={handleApplyReset}
          className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-800/40 px-3 py-2.5 text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          title="Reset with current parameters"
        >
          <RotateCcw className="h-4 w-4" />
          <span>RESET</span>
        </button>
      </div>

      {/* Right: Parameter Selectors */}
      <div className="flex flex-wrap items-center gap-3 text-xs">
        {/* Algorithm Select */}
        <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-1.5">
          <Layers className="h-3.5 w-3.5 text-cyan-400" />
          <span className="text-slate-400 font-medium">Algorithm:</span>
          <select
            value={selectedAlgo}
            onChange={(e) => {
              setSelectedAlgo(e.target.value);
              onReset(selectedFleet, e.target.value, selectedScenario);
            }}
            className="bg-transparent font-semibold text-cyan-300 outline-none cursor-pointer"
          >
            <option value="Improved Resolver" className="bg-slate-900 text-slate-200">
              Improved Resolver (Safe)
            </option>
            <option value="Improved Recovery" className="bg-slate-900 text-slate-200">
              Improved Recovery (Adaptive)
            </option>
            <option value="ML-Assisted" className="bg-slate-900 text-slate-200">
              ML-Assisted (Predictive)
            </option>
            <option value="Baseline" className="bg-slate-900 text-slate-200">
              Baseline (Original)
            </option>
          </select>
        </div>

        {/* Fleet Size */}
        <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-1.5">
          <Bot className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-slate-400 font-medium">Fleet:</span>
          <select
            value={selectedFleet}
            onChange={(e) => {
              const count = Number(e.target.value);
              setSelectedFleet(count);
              onReset(count, selectedAlgo, selectedScenario);
            }}
            className="bg-transparent font-semibold text-emerald-300 outline-none cursor-pointer"
          >
            <option value={2} className="bg-slate-900 text-slate-200">2 Robots</option>
            <option value={3} className="bg-slate-900 text-slate-200">3 Robots</option>
            <option value={4} className="bg-slate-900 text-slate-200">4 Robots</option>
            <option value={5} className="bg-slate-900 text-slate-200">5 Robots (Dense)</option>
          </select>
        </div>

        {/* Scenario ID */}
        <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-1.5">
          <span className="text-slate-400 font-medium">Scenario:</span>
          <select
            value={selectedScenario}
            onChange={(e) => {
              const sc = Number(e.target.value);
              setSelectedScenario(sc);
              onReset(selectedFleet, selectedAlgo, sc);
            }}
            className="bg-transparent font-semibold text-slate-200 outline-none cursor-pointer"
          >
            {[1, 2, 5, 10, 25, 50, 100].map((num) => (
              <option key={num} value={num} className="bg-slate-900 text-slate-200">
                #{num}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

