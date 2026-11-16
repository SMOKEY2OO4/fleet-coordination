import React from 'react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import {
  LayoutDashboard,
  Compass,
  Bot,
  ListTodo,
  GitFork,
  BrainCircuit,
  BarChart3,
  FlaskConical,
  Settings,
  Radio,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  isConnected: boolean;
}

const navItems = [
  { name: 'Executive Overview', path: '/', icon: LayoutDashboard },
  { name: 'Live Warehouse Control', path: '/live-control', icon: Compass, badge: 'LIVE' },
  { name: 'Robot Fleet', path: '/fleet', icon: Bot },
  { name: 'Task Management', path: '/tasks', icon: ListTodo },
  { name: 'Coordination Monitor', path: '/coordination', icon: GitFork },
  { name: 'ML Intelligence', path: '/ml-intelligence', icon: BrainCircuit },
  { name: 'Performance Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Simulation Lab', path: '/experiment-lab', icon: FlaskConical },
  { name: 'System Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  isConnected,
}) => {
  return (
    <aside
      className={clsx(
        'relative flex flex-col border-r border-slate-800/80 bg-slate-950/95 backdrop-blur-xl transition-all duration-300 z-30 select-none',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Branding */}
      <div className="flex h-16 items-center px-4 border-b border-slate-800/80 justify-between">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20">
            <Bot className="h-6 w-6 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="text-base font-extrabold tracking-wider text-white">
                FLEET<span className="text-cyan-400">IQ</span>
              </span>
              <span className="text-[10px] font-medium text-slate-400 truncate tracking-tight">
                AMR Warehouse Intelligence
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800/80 hover:text-white transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1.5 overflow-y-auto px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-300 shadow-sm border border-cyan-500/30 font-semibold'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                )
              }
              title={collapsed ? item.name : undefined}
            >
              <Icon className="h-5 w-5 shrink-0 transition-transform duration-200 group-hover:scale-110" />
              {!collapsed && (
                <div className="flex flex-1 items-center justify-between truncate">
                  <span className="truncate">{item.name}</span>
                  {item.badge && (
                    <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-semibold text-cyan-400 border border-cyan-500/30">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Connection Status Pill */}
      <div className="border-t border-slate-800/80 p-3">
        <div
          className={clsx(
            'flex items-center gap-2.5 rounded-xl border p-2.5 text-xs transition-colors',
            isConnected
              ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
              : 'border-rose-500/20 bg-rose-500/10 text-rose-400'
          )}
        >
          <Radio className={clsx('h-4 w-4 shrink-0', isConnected && 'animate-pulse')} />
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-semibold">{isConnected ? 'LIVE TELEMETRY' : 'DISCONNECTED'}</span>
              <span className="text-[10px] opacity-80 truncate">
                {isConnected ? 'WebSocket Sync 100%' : 'Attempting Reconnect'}
              </span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

