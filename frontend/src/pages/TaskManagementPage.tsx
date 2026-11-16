import React, { useState, useEffect } from 'react';
import {
  ListTodo,
  Plus,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Filter,
  Trash2,
  Bot,
  AlertCircle,
} from 'lucide-react';
import { fetchTasks, createTask, assignTask, cancelTask, deleteTask } from '../services/api';
import { Task } from '../types';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';

export const TaskManagementPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [startNode, setStartNode] = useState<string>('A');
  const [destNode, setDestNode] = useState<string>('I');
  const [priority, setPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('HIGH');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadTasks = async () => {
    try {
      const data = await fetchTasks();
      setTasks(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (startNode === destNode) {
      setErrorMsg('Start node and destination node must be distinct.');
      return;
    }

    try {
      await createTask({
        start_node: startNode,
        destination_node: destNode,
        priority,
      });
      setIsModalOpen(false);
      loadTasks();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleAssign = async (taskId: string) => {
    try {
      await assignTask(taskId);
      loadTasks();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'No available idle robots to assign');
    }
  };

  const handleCancel = async (taskId: string) => {
    try {
      await cancelTask(taskId);
      loadTasks();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Could not cancel task');
    }
  };

  const handleDelete = async (taskId: string) => {
    try {
      await deleteTask(taskId);
      loadTasks();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Could not delete task');
    }
  };

  const filteredTasks = tasks.filter((t) => {
    if (filterStatus === 'ALL') return true;
    return t.status === filterStatus;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-white">Logistics Task Dispatch & Tracking</h2>
          <p className="text-xs text-slate-400">
            Dispatch point-to-point delivery orders, inspect automated robot assignment and track lifecycles
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>CREATE NEW MISSION</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {['ALL', 'QUEUED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'].map((s) => (
          <button
            key={s}
            onClick={() => setFilterStatus(s)}
            className={`rounded-xl px-3.5 py-1.5 font-semibold transition-colors border ${
              filterStatus === s
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm'
                : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:bg-slate-800'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Tasks Table / Cards */}
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800 bg-slate-950/80 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="py-3.5 px-4">Mission ID</th>
                <th className="py-3.5 px-4">Transit Route</th>
                <th className="py-3.5 px-4">Priority</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Assigned AMR</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredTasks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <ListTodo className="h-8 w-8 mx-auto mb-2 opacity-30" />
                    <p className="text-xs">No tasks found matching filter &quot;{filterStatus}&quot;</p>
                  </td>
                </tr>
              ) : (
                filteredTasks.map((t) => {
                  const isQueued = t.status === 'QUEUED';
                  const isAssigned = t.status === 'ASSIGNED';
                  const isInProgress = t.status === 'IN_PROGRESS';
                  const isCompleted = t.status === 'COMPLETED';
                  const isCancelled = t.status === 'CANCELLED';

                  return (
                    <tr key={t.task_id} className="hover:bg-slate-950/40 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-white truncate max-w-[140px]">
                        {t.task_id.substring(0, 8)}...
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-slate-800 px-2 py-0.5 font-bold text-cyan-300">
                            Node {t.start_node}
                          </span>
                          <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
                          <span className="rounded bg-slate-800 px-2 py-0.5 font-bold text-emerald-300">
                            Node {t.destination_node}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`font-semibold text-[10px] uppercase rounded px-2 py-0.5 border ${
                            t.priority === 'HIGH'
                              ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                              : t.priority === 'MEDIUM'
                              ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}
                        >
                          {t.priority}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge
                          variant={
                            isCompleted
                              ? 'green'
                              : isInProgress
                              ? 'cyan'
                              : isAssigned
                              ? 'blue'
                              : isCancelled
                              ? 'red'
                              : 'amber'
                          }
                          size="sm"
                          pulse={isInProgress}
                        >
                          {t.status}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        {t.assigned_robot_id ? (
                          <span className="text-cyan-400 font-bold">{t.assigned_robot_id}</span>
                        ) : (
                          <span className="text-slate-500 italic">Unassigned</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isQueued && (
                            <button
                              onClick={() => handleAssign(t.task_id)}
                              className="rounded-lg bg-cyan-600/20 border border-cyan-500/30 px-2.5 py-1 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-600/30 transition-colors"
                            >
                              Dispatch AMR
                            </button>
                          )}
                          {!isCompleted && !isCancelled && (
                            <button
                              onClick={() => handleCancel(t.task_id)}
                              className="rounded-lg border border-slate-800 px-2 py-1 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition-colors"
                              title="Cancel Mission"
                            >
                              Cancel
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(t.task_id)}
                            className="rounded-lg p-1 text-slate-500 hover:text-rose-400 transition-colors"
                            title="Delete Task"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Create Task */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Dispatch New Logistics Mission">
        <form onSubmit={handleCreate} className="space-y-4 text-xs">
          {errorMsg && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-rose-300">
              {errorMsg}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Pickup Node (Origin)</label>
              <select
                value={startNode}
                onChange={(e) => setStartNode(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-cyan-500 font-mono"
              >
                {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'].map((n) => (
                  <option key={n} value={n}>Node {n}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">Delivery Node (Target)</label>
              <select
                value={destNode}
                onChange={(e) => setDestNode(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-cyan-500 font-mono"
              >
                {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'].map((n) => (
                  <option key={n} value={n}>Node {n}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Dispatch Priority Level</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as any)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-200 outline-none focus:border-cyan-500"
            >
              <option value="HIGH">HIGH (Urgent Dispatch, Priority Corridor)</option>
              <option value="MEDIUM">MEDIUM (Standard Fulfillment Flow)</option>
              <option value="LOW">LOW (Deferred Transit Capacity)</option>
            </select>
          </div>

          <div className="pt-3 flex gap-2">
            <button
              type="submit"
              className="flex-1 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 py-2.5 font-bold text-white hover:from-cyan-400 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/20"
            >
              Queue Delivery Task
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

