import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';
import { wsClient } from '../../services/websocket';
import {
  fetchSimulationState,
  startSimulation,
  pauseSimulation,
  stepSimulation,
  resetSimulation,
  setSimulationSpeed,
} from '../../services/api';
import { SimulationState } from '../../types';

export const Layout: React.FC = () => {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);

  useEffect(() => {
    // Initial fetch of simulation state
    fetchSimulationState()
      .then((state) => setSimulationState(state))
      .catch((err) => console.error('Error fetching initial simulation state:', err));

    // Connect WebSocket
    const unsubscribe = wsClient.subscribe((msg) => {
      setIsConnected(true);
      if (msg.type === 'state_update' && msg.data) {
        setSimulationState(msg.data);
      } else if (msg.type === 'connected' && msg.data) {
        setSimulationState(msg.data);
      }
    });

    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, []);

  // Backup poll while simulation is running to guarantee synchronization if WebSocket disconnects
  useEffect(() => {
    if (!simulationState?.is_running) return;

    const interval = setInterval(async () => {
      try {
        const state = await fetchSimulationState();
        setSimulationState(state);
      } catch (e) {
        console.error('Simulation state poll error:', e);
      }
    }, simulationState.speed_ms || 1000);

    return () => clearInterval(interval);
  }, [simulationState?.is_running, simulationState?.speed_ms]);

  const handleStart = async () => {
    try {
      const state = await startSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error(e);
    }
  };

  const handlePause = async () => {
    try {
      const state = await pauseSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStep = async () => {
    try {
      const state = await stepSimulation();
      setSimulationState(state);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = async () => {
    try {
      const state = await resetSimulation(
        simulationState?.fleet_size || 4,
        simulationState?.algorithm || 'Improved Resolver',
        simulationState?.scenario_id || 1
      );
      setSimulationState(state);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSpeedChange = async (speed: number) => {
    try {
      await setSimulationSpeed(speed);
      if (simulationState) {
        setSimulationState({ ...simulationState, speed_ms: speed });
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
      {/* Collapsible Sidebar */}
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        isConnected={isConnected}
      />

      {/* Main Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNavbar
          simulationState={simulationState}
          onStart={handleStart}
          onPause={handlePause}
          onStep={handleStep}
          onReset={handleReset}
          onSpeedChange={handleSpeedChange}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900/60 via-slate-950 to-slate-950">
          <Outlet context={{ simulationState, setSimulationState }} />
        </main>
      </div>
    </div>
  );
};

