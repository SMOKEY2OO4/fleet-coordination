import React, { useState } from 'react';
import {
  Activity,
  ArrowRight,
  AlertTriangle,
  ShieldCheck,
  RotateCw,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { SimulationEvent } from '../../types';

interface LiveEventFeedProps {
  events: SimulationEvent[];
}

export const LiveEventFeed: React.FC<LiveEventFeedProps> = ({ events }) => {
  const [filterType, setFilterType] = useState<string>('ALL');

  const filteredEvents = events.filter((ev) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'MOVEMENTS') return ev.event_type === 'movement';
    if (filterType === 'CONFLICTS') return ev.event_type === 'blocked' || ev.event_type === 'safety_alert';
    if (filterType === 'DEADLOCKS') return ev.event_type === 'deadlock_recovery';
    return true;
  });

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'movement':
        return <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />;
      case 'blocked':
        return <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />;
      case 'deadlock_recovery':
        return <RotateCw className="h-3.5 w-3.5 text-purple-400" />;
      case 'goal_reached':
      case 'all_tasks_completed':
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
      case 'safety_alert':
        return <ShieldCheck className="h-3.5 w-3.5 text-rose-400" />;
      default:
        return <Activity className="h-3.5 w-3.5 text-slate-400" />;
    }
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'movement':
        return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20';
      case 'blocked':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'deadlock_recovery':
        return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
      case 'goal_reached':
      case 'all_tasks_completed':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-800/90 bg-slate-900/70 backdrop-blur-xl shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 bg-slate-950/60">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Real-Time Coordination Feed
          </h3>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
            {events.length}
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 text-[10px]">
          {['ALL', 'MOVEMENTS', 'CONFLICTS', 'DEADLOCKS'].map((f) => (
            <button
              key={f}
              onClick={() => setFilterType(f)}
              className={`rounded-md px-2 py-1 font-semibold transition-colors ${
                filterType === f
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-[500px]">
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center text-slate-500">
            <Activity className="h-8 w-8 mb-2 opacity-30" />
            <p className="text-xs">No coordination events recorded yet</p>
            <p className="text-[11px] text-slate-600">Events will stream here automatically during simulation</p>
          </div>
        ) : (
          filteredEvents.map((ev, index) => (
            <div
              key={index}
              className="flex items-start gap-2.5 rounded-xl border border-slate-800/60 bg-slate-950/40 p-2.5 transition-all hover:bg-slate-950/80 hover:border-slate-700 text-xs"
            >
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-slate-800 bg-slate-900">
                {getEventIcon(ev.event_type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1 mb-0.5">
                  <span
                    className={`inline-flex items-center rounded px-1.5 py-0.2 text-[9px] font-bold uppercase tracking-wider border ${getEventBadge(
                      ev.event_type
                    )}`}
                  >
                    {ev.event_type.replace('_', ' ')}
                  </span>
                  <span className="font-mono text-[10px] text-slate-500">{ev.timestamp}</span>
                </div>
                <p className="text-slate-300 text-xs leading-relaxed font-normal">{ev.message}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

