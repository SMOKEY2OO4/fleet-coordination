import React from 'react';
import clsx from 'clsx';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'cyan' | 'blue' | 'green' | 'amber' | 'red' | 'purple';
  trend?: {
    value: string;
    isPositive?: boolean;
  };
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'cyan',
  trend,
}) => {
  const iconColor = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    green: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    red: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  }[variant];

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/70 p-5 backdrop-blur-md shadow-lg transition-all duration-200 hover:border-slate-700 hover:bg-slate-900/90">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
        <div className={clsx('rounded-lg border p-2.5', iconColor)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <p className="text-2xl font-bold tracking-tight text-white">{value}</p>
        {trend && (
          <span
            className={clsx(
              'text-xs font-medium',
              trend.isPositive ? 'text-emerald-400' : 'text-amber-400'
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
      <div className="absolute -bottom-6 -right-6 h-16 w-16 rounded-full bg-slate-800/20 blur-xl pointer-events-none" />
    </div>
  );
};

