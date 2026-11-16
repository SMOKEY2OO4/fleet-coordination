import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { WarehouseMap2D } from '../components/warehouse/WarehouseMap2D';
import { LiveEventFeed } from '../components/warehouse/LiveEventFeed';
import { SimulationControls } from '../components/warehouse/SimulationControls';
import { RobotDetailDrawer } from '../components/warehouse/RobotDetailDrawer';
import { Modal } from '../components/ui/Modal';
import {
  startSimulation,
  pauseSimulation,
  stepSimulation,
  resetSimulation,
  setSimulationSpeed,
  moveRobot,
} from '../services/api';
import { Robot, SimulationState } from '../types';

export const WarehouseControlPage: React.FC = () => {
  const { simulationState, setSimulationState } = useOutletContext<{
    simulationState: SimulationState | null;
    setSimulationState: React.Dispatch<React.SetStateAction<SimulationState | null>>;
  }>();

  const [selectedRobot, setSelectedRobot] = useState<Robot | null>(null);
  const [inspectedNode, setInspectedNode] = useState<string | null>(null);

  const handleStart = async () => {
    try {
      const state = await startSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error('[FleetIQ] Start simulation error:', e);
    }
  };

  const handlePause = async () => {
    try {
      const state = await pauseSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error('[FleetIQ] Pause simulation error:', e);
    }
  };

  const handleStep = async () => {
    try {
      const state = await stepSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error('[FleetIQ] Step simulation error:', e);
    }
  };

  const handleReset = async (fleetSize: number, algorithm: string, scenarioId: number) => {
    try {
      const state = await resetSimulation(fleetSize, algorithm, scenarioId);
      setSimulationState(state);
      setSelectedRobot(null);
    } catch (e) {
      console.error('[FleetIQ] Reset simulation error:', e);
    }
  };

  const handleSpeedChange = async (speed: number) => {
    try {
      await setSimulationSpeed(speed);
      if (simulationState) {
        setSimulationState({ ...simulationState, speed_ms: speed });
      }
    } catch (e) {
      console.error('[FleetIQ] Speed change error:', e);
    }
  };

  const handleManualMove = async (robotId: string) => {
    try {
      await moveRobot(robotId);
      const state = await stepSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error('[FleetIQ] Manual move error:', e);
    }
  };

  return (
    <div className="space-y-5">
      {/* Simulation Controls Toolbar */}
      <SimulationControls
        simulationState={simulationState}
        onStart={handleStart}
        onPause={handlePause}
        onStep={handleStep}
        onReset={handleReset}
        onSpeedChange={handleSpeedChange}
      />

      {/* Main Workspace: 2D Map + Live Feed Panel */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Left 2 Cols: 2D Interactive Warehouse Canvas */}
        <div className="xl:col-span-2 space-y-4">
          <WarehouseMap2D
            simulationState={simulationState}
            selectedRobotId={selectedRobot?.robot_id}
            onSelectRobot={(robot) => setSelectedRobot(robot)}
            onSelectNode={(nodeId) => setInspectedNode(nodeId)}
          />

          {/* Quick Fleet Position Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(simulationState?.robots || []).map((r) => (
              <div
                key={r.robot_id}
                onClick={() => setSelectedRobot(r)}
                className={`cursor-pointer rounded-xl border p-3 transition-all ${
                  selectedRobot?.robot_id === r.robot_id
                    ? 'border-cyan-400 bg-cyan-950/40 shadow-lg shadow-cyan-950/40'
                    : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-bold text-xs text-white">{r.robot_id}</span>
                  <span
                    className={`h-2 w-2 rounded-full ${
                      r.completed
                        ? 'bg-emerald-400'
                        : (r.waiting_steps ?? 0) > 0
                        ? 'bg-amber-400 animate-pulse'
                        : 'bg-cyan-400'
                    }`}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Pos: <strong className="text-slate-200">{r.current_node}</strong></span>
                  <span>Goal: <strong className="text-cyan-400">{r.goal || '—'}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Live Event Feed */}
        <div className="h-[650px]">
          <LiveEventFeed events={simulationState?.recent_events || []} />
        </div>
      </div>

      {/* Robot Detail Drawer (opened on click) */}
      <RobotDetailDrawer
        robot={selectedRobot}
        onClose={() => setSelectedRobot(null)}
        onMoveRobot={handleManualMove}
      />

      {/* Node Inspection Modal */}
      <Modal
        isOpen={!!inspectedNode}
        onClose={() => setInspectedNode(null)}
        title={`Warehouse Locus Inspection — Node ${inspectedNode}`}
      >
        {inspectedNode && (
          <div className="space-y-4 text-xs">
            <p className="text-slate-300">
              Detailed topological node attributes and connected transit edges for Node{' '}
              <strong className="text-cyan-400 font-mono">{inspectedNode}</strong>:
            </p>
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Topological Degree:</span>
                <span className="font-mono font-bold text-white">
                  {inspectedNode === 'E' ? 4 : ['B', 'D', 'F', 'H'].includes(inspectedNode) ? 3 : 2}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Zone Role:</span>
                <span className="font-semibold text-cyan-300">
                  {inspectedNode === 'E'
                    ? 'Central Crossway Hub (High Traffic)'
                    : ['A', 'C'].includes(inspectedNode)
                    ? 'Inbound Receiving Dock'
                    : ['G', 'I'].includes(inspectedNode)
                    ? 'Outbound Packaging Station'
                    : 'Intermediate Logistics Transit Corridor'}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Current Occupant:</span>
                <span className="font-mono font-bold text-slate-200">
                  {simulationState?.occupied_nodes[inspectedNode] || 'VACANT'}
                </span>
              </div>
            </div>
            <button
              onClick={() => setInspectedNode(null)}
              className="w-full rounded-xl bg-cyan-600 py-2.5 font-semibold text-white hover:bg-cyan-500 transition-colors"
            >
              Close Inspector
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
};
