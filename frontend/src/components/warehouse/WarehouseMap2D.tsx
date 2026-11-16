import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, AlertTriangle, CheckCircle2, Navigation, Zap } from 'lucide-react';
import { Robot, SimulationState } from '../../types';

interface WarehouseMap2DProps {
  simulationState?: SimulationState | null;
  selectedRobotId?: string | null;
  onSelectRobot?: (robot: Robot | null) => void;
  onSelectNode?: (nodeId: string) => void;
}

// 9-Node coordinates mapped to SVG coordinate space
// A, B, C (Row 1)
// D, E, F (Row 2)
// G, H, I (Row 3)
const NODE_COORDINATES: Record<string, { x: number; y: number; label: string; zone: string }> = {
  A: { x: 140, y: 120, label: 'Node A', zone: 'Inbound Dock 1' },
  B: { x: 380, y: 120, label: 'Node B', zone: 'Staging Alpha' },
  C: { x: 620, y: 120, label: 'Node C', zone: 'Inbound Dock 2' },
  D: { x: 140, y: 320, label: 'Node D', zone: 'Aisle Corridor West' },
  E: { x: 380, y: 320, label: 'Node E', zone: 'Central Intersection Hub' },
  F: { x: 620, y: 320, label: 'Node F', zone: 'Aisle Corridor East' },
  G: { x: 140, y: 520, label: 'Node G', zone: 'Outbound Sorting 1' },
  H: { x: 380, y: 520, label: 'Node H', zone: 'Staging Beta' },
  I: { x: 620, y: 520, label: 'Node I', zone: 'Outbound Sorting 2' },
};

// 12 connecting edges in the 3x3 grid
const EDGES = [
  ['A', 'B'], ['B', 'C'],
  ['D', 'E'], ['E', 'F'],
  ['G', 'H'], ['H', 'I'],
  ['A', 'D'], ['D', 'G'],
  ['B', 'E'], ['E', 'H'],
  ['C', 'F'], ['F', 'I'],
];

export const WarehouseMap2D: React.FC<WarehouseMap2DProps> = ({
  simulationState,
  selectedRobotId,
  onSelectRobot,
  onSelectNode,
}) => {
  const robots = simulationState?.robots || [];
  const occupiedNodes = simulationState?.occupied_nodes || {};
  const requestedMoves = simulationState?.requested_moves || {};

  // Find congested nodes (nodes with waiting robots or multiple requests)
  const waitingNodes = new Set(
    robots.filter((r) => !r.completed && (r.waiting_steps ?? 0) > 0).map((r) => r.current_node)
  );

  // Group active robots by current node for stacking offset
  const robotsByNode: Record<string, Robot[]> = {};
  robots.forEach((r) => {
    if (!r.completed) {
      if (!robotsByNode[r.current_node]) robotsByNode[r.current_node] = [];
      robotsByNode[r.current_node].push(r);
    }
  });

  return (
    <div className="relative w-full h-[580px] rounded-2xl border border-slate-800/90 bg-slate-950/90 p-4 shadow-2xl overflow-hidden backdrop-blur-xl flex flex-col items-center justify-center">
      {/* Grid Background Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* Top Map Telemetry Bar */}
      <div className="absolute top-4 left-5 right-5 flex items-center justify-between pointer-events-none z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 backdrop-blur-md">
            <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-xs font-semibold tracking-wider text-slate-300 uppercase">
              GRID TOPOLOGY: 9 NODES / 12 TRANSIT ARTERIES
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 backdrop-blur-md">
            <span className="text-xs font-mono text-cyan-400">
              ACTIVE AMRs: {robots.filter((r) => !r.completed).length} / {robots.length}
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 text-[11px] backdrop-blur-md">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 border border-cyan-300" />
            <span className="text-slate-400">Clear Transit</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400 border border-amber-300" />
            <span className="text-slate-400">Waiting/Conflict</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 border border-emerald-300" />
            <span className="text-slate-400">Delivered</span>
          </div>
        </div>
      </div>

      {/* SVG Warehouse Map Canvas */}
      <svg
        viewBox="0 0 760 640"
        className="w-full h-full max-h-[540px] select-none"
        style={{ filter: 'drop-shadow(0 4px 20px rgba(0,0,0,0.5))' }}
      >
        <defs>
          <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
          </linearGradient>
          <linearGradient id="congestedEdgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.6" />
          </linearGradient>
          <radialGradient id="centerHubGlow">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Central Hub Glow Area around Node E */}
        <circle cx={NODE_COORDINATES.E.x} cy={NODE_COORDINATES.E.y} r="120" fill="url(#centerHubGlow)" />

        {/* 1. Connecting Edges */}
        {EDGES.map(([u, v]) => {
          const p1 = NODE_COORDINATES[u];
          const p2 = NODE_COORDINATES[v];
          const isCongested = waitingNodes.has(u) && waitingNodes.has(v);

          return (
            <g key={`${u}-${v}`}>
              {/* Outer Glow Line */}
              <line
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                stroke={isCongested ? '#ef4444' : '#1e293b'}
                strokeWidth={isCongested ? '8' : '6'}
                strokeLinecap="round"
                className="transition-colors duration-300"
              />
              {/* Inner Transit Track */}
              <line
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                stroke={isCongested ? 'url(#congestedEdgeGradient)' : '#334155'}
                strokeWidth="2.5"
                strokeDasharray={isCongested ? '6 4' : 'none'}
              />
            </g>
          );
        })}

        {/* 2. Warehouse Nodes */}
        {Object.entries(NODE_COORDINATES).map(([nodeId, coords]) => {
          const isOccupied = !!occupiedNodes[nodeId];
          const isWaiting = waitingNodes.has(nodeId);
          const isCenter = nodeId === 'E';

          return (
            <g
              key={nodeId}
              className="cursor-pointer group"
              onClick={() => onSelectNode && onSelectNode(nodeId)}
            >
              {/* Node Outer Radar Ring */}
              <circle
                cx={coords.x}
                cy={coords.y}
                r={isCenter ? 36 : 30}
                fill="#0f172a"
                stroke={
                  isWaiting
                    ? '#f59e0b'
                    : isOccupied
                    ? '#0284c7'
                    : '#334155'
                }
                strokeWidth={isWaiting ? 3 : 2}
                className="transition-all duration-300 group-hover:stroke-cyan-400"
              />

              {/* Node Center Disc */}
              <circle
                cx={coords.x}
                cy={coords.y}
                r={isCenter ? 26 : 22}
                fill={
                  isWaiting
                    ? '#78350f'
                    : isOccupied
                    ? '#0c4a6e'
                    : isCenter
                    ? '#164e63'
                    : '#1e293b'
                }
                className="transition-colors duration-200"
              />

              {/* Node Identifier Text */}
              <text
                x={coords.x}
                y={coords.y + 6}
                textAnchor="middle"
                fontSize={isCenter ? '18' : '15'}
                fontWeight="bold"
                fill={isWaiting ? '#fbbf24' : isOccupied ? '#38bdf8' : '#e2e8f0'}
                className="pointer-events-none select-none tracking-tight font-mono"
              >
                {nodeId}
              </text>

              {/* Node Tag Label */}
              <text
                x={coords.x}
                y={coords.y + 48}
                textAnchor="middle"
                fontSize="11"
                fontWeight="500"
                fill="#94a3b8"
                className="pointer-events-none select-none"
              >
                {coords.zone}
              </text>
            </g>
          );
        })}

        {/* 3. Render Animated AMR Robots */}
        {robots.map((robot) => {
          const currentPos = NODE_COORDINATES[robot.current_node];
          if (!currentPos) return null;

          const isSelected = selectedRobotId === robot.robot_id;
          const isWaiting = !robot.completed && (robot.waiting_steps ?? 0) > 0;
          const isCompleted = robot.completed;

          // Offset if multiple robots share node
          const sharing = robotsByNode[robot.current_node] || [];
          const idx = sharing.findIndex((r) => r.robot_id === robot.robot_id);
          const offsetX = sharing.length > 1 ? (idx === 0 ? -16 : 16) : 0;
          const offsetY = sharing.length > 1 ? (idx === 0 ? -14 : 14) : 0;

          const targetX = currentPos.x + offsetX;
          const targetY = currentPos.y + offsetY;

          // Compute destination vector angle if moving
          let nextNodeCoords = robot.next_node ? NODE_COORDINATES[robot.next_node] : null;

          return (
            <motion.g
              key={robot.robot_id}
              initial={false}
              animate={{ x: targetX, y: targetY }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="cursor-pointer"
              onClick={(e) => {
                e.stopPropagation();
                onSelectRobot && onSelectRobot(robot);
              }}
            >
              {/* Pulsing indicator when waiting/conflict */}
              {isWaiting && (
                <circle
                  cx={0}
                  cy={0}
                  r="24"
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="2"
                  strokeDasharray="4 3"
                  className="animate-spin"
                />
              )}

              {/* Selection Halo */}
              {isSelected && (
                <circle
                  cx={0}
                  cy={0}
                  r="26"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="2.5"
                  className="animate-pulse"
                />
              )}

              {/* Robot Chassis */}
              <circle
                cx={0}
                cy={0}
                r="18"
                fill={isCompleted ? '#065f46' : isWaiting ? '#b45309' : robot.color || '#0284c7'}
                stroke={isCompleted ? '#34d399' : isWaiting ? '#fbbf24' : '#e0f2fe'}
                strokeWidth="2"
                style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.6))' }}
              />

              {/* Directional Vector Arrow */}
              {nextNodeCoords && !isCompleted && !isWaiting && (
                <line
                  x1={0}
                  y1={0}
                  x2={(nextNodeCoords.x - currentPos.x) * 0.12}
                  y2={(nextNodeCoords.y - currentPos.y) * 0.12}
                  stroke="#ffffff"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
              )}

              {/* Robot Icon / ID badge */}
              <text
                x={0}
                y={4}
                textAnchor="middle"
                fontSize="9"
                fontWeight="bold"
                fill="#ffffff"
                className="pointer-events-none select-none font-mono tracking-tighter"
              >
                {robot.robot_id.replace('AMR-', 'R')}
              </text>

              {/* Robot Float Tag */}
              <g transform="translate(0, -25)">
                <rect
                  x="-28"
                  y="-10"
                  width="56"
                  height="16"
                  rx="4"
                  fill="#090d16"
                  stroke={isWaiting ? '#f59e0b' : '#334155'}
                  strokeWidth="1"
                />
                <text
                  x="0"
                  y="2"
                  textAnchor="middle"
                  fontSize="8"
                  fontWeight="bold"
                  fill={isWaiting ? '#fbbf24' : '#38bdf8'}
                  className="pointer-events-none select-none font-mono"
                >
                  {robot.robot_id}
                </text>
              </g>
            </motion.g>
          );
        })}
      </svg>
    </div>
  );
};

