import React, { useState, useEffect } from 'react';
import {
  Bot,
  Plus,
  Search,
  Filter,
  Trash2,
  Play,
  Battery,
  MapPin,
  Clock,
  ShieldAlert,
  RotateCcw,
} from 'lucide-react';
import { fetchRobots, registerRobot, deleteRobot, moveRobot } from '../services/api';
import { Robot } from '../types';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';

export const FleetManagementPage: React.FC = () => {
  const [robots, setRobots] = useState<Robot[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [newBotId, setNewBotId] = useState<string>('AMR-06');
  const [newNode, setNewNode] = useState<string>('A');
  const [newType, setNewType] = useState<string>('SIMULATED');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadRobots = async () => {
    try {
      const data = await fetchRobots();
      setRobots(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadRobots();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await registerRobot({
        robot_id: newBotId.trim().toUpperCase(),
        robot_type: newType,
        current_node: newNode,
      });
      setIsModalOpen(false);
      setNewBotId(`AMR-0${robots.length + 2}`);
      loadRobots();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to register robot');
    }
  };

  const handleDelete = async (robotId: string) => {
    if (!confirm(`Are you sure you want to deactivate and remove ${robotId}?`)) return;
    try {
      await deleteRobot(robotId);
      loadRobots();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete robot');
    }
  };

  const handleMove = async (robotId: string) => {
    try {
      await moveRobot(robotId);
      loadRobots();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Movement not possible (robot not assigned or waiting)');
    }
  };

  const filteredRobots = robots.filter((r) => {
    const matchesSearch = r.robot_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'ALL' || r.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Top Bar with Registration & Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white">Autonomous Robot Fleet Registry</h2>
          <p className="text-xs text-slate-400">
            Monitor hardware telemetry, state machines, active assignments and battery health
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>REGISTER NEW AMR</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800/80 bg-slate-900/60 p-4 backdrop-blur-xl">
        <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 w-full sm:w-72">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by Robot ID (e.g. AMR-01)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-transparent text-xs text-slate-200 outline-none placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center gap-2 text-xs">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-slate-400">Status:</span>
          {['ALL', 'IDLE', 'ASSIGNED', 'MOVING', 'WAITING'].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`rounded-lg px-2.5 py-1 font-semibold transition-colors ${
                filterStatus === s
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Robot Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredRobots.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center py-16 text-center text-slate-500 rounded-2xl border border-slate-800/80 bg-slate-900/30">
            <Bot className="h-12 w-12 mb-3 opacity-30 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-300">No matching robots registered</h3>
            <p className="text-xs text-slate-500 mt-1">
              Click &quot;Register New AMR&quot; above to commission a warehouse unit.
            </p>
          </div>
        ) : (
          filteredRobots.map((robot) => {
            const isWaiting = robot.status === 'WAITING';
            const isMoving = robot.status === 'MOVING';
            const isAssigned = robot.status === 'ASSIGNED';

            return (
              <div
                key={robot.robot_id}
                className="flex flex-col justify-between rounded-2xl border border-slate-800/80 bg-slate-900/70 p-5 shadow-xl backdrop-blur-xl transition-all hover:border-slate-700"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 font-bold text-white shadow-md shadow-cyan-600/20 font-mono">
                        <Bot className="h-6 w-6" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white font-mono">{robot.robot_id}</h3>
                        <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
                          {robot.robot_type}
                        </span>
                      </div>
                    </div>

                    <Badge
                      variant={isMoving ? 'green' : isWaiting ? 'amber' : isAssigned ? 'blue' : 'gray'}
                      size="sm"
                      pulse={isMoving || isWaiting}
                    >
                      {robot.status}
                    </Badge>
                  </div>

                  {/* Attributes Grid */}
                  <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
                    <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-2.5">
                      <span className="text-[10px] text-slate-400 block mb-0.5">CURRENT NODE</span>
                      <span className="text-sm font-bold text-cyan-300 font-mono">
                        Node {robot.current_node}
                      </span>
                    </div>

                    <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-2.5">
                      <span className="text-[10px] text-slate-400 block mb-0.5">BATTERY SOC</span>
                      <span className="text-sm font-bold text-emerald-400 font-mono">
                        {robot.battery_percent}%
                      </span>
                    </div>

                    <div className="col-span-2 rounded-xl border border-slate-800/80 bg-slate-950/40 p-2.5">
                      <span className="text-[10px] text-slate-400 block mb-0.5">ASSIGNED TASK</span>
                      <span className="text-xs font-mono text-slate-200 truncate block">
                        {robot.current_task_id || 'IDLE — Available for Task'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-4 mt-4 border-t border-slate-800/80">
                  <button
                    onClick={() => handleMove(robot.robot_id)}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800/80 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
                  >
                    <Play className="h-3.5 w-3.5 text-cyan-400" />
                    <span>Advance 1 Step</span>
                  </button>

                  <button
                    onClick={() => handleDelete(robot.robot_id)}
                    className="flex items-center justify-center rounded-xl border border-rose-500/30 bg-rose-500/10 p-2 text-rose-400 hover:bg-rose-500/20 transition-colors"
                    title="Decommission Robot"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modal: Register Robot */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Commission New Autonomous Robot">
        <form onSubmit={handleRegister} className="space-y-4 text-xs">
          {errorMsg && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-rose-300">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Robot Identifier (ID)</label>
            <input
              type="text"
              required
              value={newBotId}
              onChange={(e) => setNewBotId(e.target.value)}
              placeholder="e.g. AMR-05"
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Initial Location Node</label>
            <select
              value={newNode}
              onChange={(e) => setNewNode(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-cyan-500 font-mono"
            >
              {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'].map((n) => (
                <option key={n} value={n}>
                  Node {n}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Robot Hardware Type</label>
            <select
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-cyan-500"
            >
              <option value="SIMULATED">SIMULATED (Virtual AMR Engine)</option>
              <option value="PHYSICAL">PHYSICAL (Industrial Hardware AMR)</option>
            </select>
          </div>

          <div className="pt-3 flex gap-2">
            <button
              type="submit"
              className="flex-1 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 py-2.5 font-bold text-white hover:from-cyan-400 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/20"
            >
              Commission Robot
            </button>
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="rounded-xl border border-slate-700 px-4 py-2.5 font-semibold text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

