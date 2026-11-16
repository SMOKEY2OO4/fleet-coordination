import React from 'react';
import {
  Bot,
  Battery,
  MapPin,
  Flag,
  Navigation,
  Clock,
  CheckCircle2,
  AlertTriangle,
  X,
  Play,
} from 'lucide-react';
import { Robot } from '../../types';
import { Badge } from '../ui/Badge';

interface RobotDetailDrawerProps {
  robot: Robot | null;
  onClose: () => void;
  onMoveRobot?: (robotId: string) => void;
}

export const RobotDetailDrawer: React.FC<RobotDetailDrawerProps> = ({
  robot,
  onClose,
  onMoveRobot,
}) => {
  if (!robot) return null;

  const isCompleted = robot.completed;
  const isWaiting = !isCompleted && (robot.waiting_steps ?? 0) > 0;

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-sm flex-col border-l border-slate-800 bg-slate-950/95 p-6 shadow-2xl backdrop-blur-2xl animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/20 text-white font-bold"
            style={{ backgroundColor: robot.color || '#0284c7' }}
          >
            <Bot className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white font-mono">{robot.robot_id}</h3>
            <span className="text-xs text-slate-400 font-mono">
              TYPE: {robot.robot_type || 'AUTONOMOUS AMR'}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Body Information */}
      <div className="flex-1 space-y-5 overflow-y-auto py-5 text-xs">
        {/* Status Badge */}
        <div className="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <span className="font-semibold text-slate-400 uppercase tracking-wider text-[11px]">
            Operational State
          </span>
          <Badge
            variant={isCompleted ? 'green' : isWaiting ? 'amber' : 'cyan'}
            size="md"
            pulse={!isCompleted}
          >
            {isCompleted ? 'DELIVERY COMPLETE' : isWaiting ? 'WAITING / RESOLVING' : 'IN TRANSIT'}
          </Badge>
        </div>

        {/* Telemetry Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <MapPin className="h-3.5 w-3.5 text-cyan-400" />
              <span>Current Position</span>
            </div>
            <p className="text-lg font-bold text-white font-mono">Node {robot.current_node}</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Flag className="h-3.5 w-3.5 text-emerald-400" />
              <span>Target Delivery</span>
            </div>
            <p className="text-lg font-bold text-white font-mono">
              {robot.goal ? `Node ${robot.goal}` : 'Unassigned'}
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Battery className="h-3.5 w-3.5 text-emerald-400" />
              <span>Battery Level</span>
            </div>
            <p className="text-lg font-bold text-white font-mono">{robot.battery_percent ?? 98}%</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              <span>Waiting Steps</span>
            </div>
            <p className="text-lg font-bold text-white font-mono">{robot.waiting_steps ?? 0}</p>
          </div>
        </div>

        {/* Planned Route Stepper */}
        {robot.path && robot.path.length > 0 && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <span className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] block mb-3">
              Allocated Route Sequence
            </span>
            <div className="flex items-center gap-2 flex-wrap">
              {robot.path.map((node, index) => {
                const isPassed = (robot.path_index ?? 0) > index;
                const isCurrent = robot.current_node === node;

                return (
                  <div key={index} className="flex items-center gap-1.5">
                    <div
                      className={`flex h-7 w-7 items-center justify-center rounded-lg font-mono text-xs font-bold border transition-colors ${
                        isCurrent
                          ? 'border-cyan-400 bg-cyan-500/20 text-cyan-300 shadow-md shadow-cyan-500/20'
                          : isPassed
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                          : 'border-slate-700 bg-slate-800 text-slate-400'
                      }`}
                    >
                      {node}
                    </div>
                    {index < robot.path.length - 1 && (
                      <span className="text-slate-600 font-bold">→</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Conflict & Resolution Notice */}
        {isWaiting && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-amber-300">
            <div className="flex items-center gap-2 font-semibold mb-1">
              <AlertTriangle className="h-4 w-4" />
              <span>Contention Arbitration Active</span>
            </div>
            <p className="text-[11px] text-amber-400/90 leading-relaxed">
              Robot requested Node {robot.next_node || 'destination'} which is currently occupied or
              claimed by higher-priority traffic. Coordinated resolver will dispatch clearance.
            </p>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="border-t border-slate-800 pt-4 flex gap-2">
        {onMoveRobot && (
          <button
            onClick={() => onMoveRobot(robot.robot_id)}
            className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-cyan-600 px-4 py-2.5 font-semibold text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-600/20"
          >
            <Play className="h-4 w-4" />
            <span>Manual Step</span>
          </button>
        )}
        <button
          onClick={onClose}
          className="rounded-xl border border-slate-800 px-4 py-2.5 font-semibold text-slate-300 hover:bg-slate-800"
        >
          Close
        </button>
      </div>
    </div>
  );
};

