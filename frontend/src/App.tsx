import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { WarehouseControlPage } from './pages/WarehouseControlPage';
import { FleetManagementPage } from './pages/FleetManagementPage';
import { TaskManagementPage } from './pages/TaskManagementPage';
import { CoordinationMonitorPage } from './pages/CoordinationMonitorPage';
import { MLIntelligencePage } from './pages/MLIntelligencePage';
import { PerformanceAnalyticsPage } from './pages/PerformanceAnalyticsPage';
import { ExperimentLabPage } from './pages/ExperimentLabPage';
import { SystemSettingsPage } from './pages/SystemSettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="live-control" element={<WarehouseControlPage />} />
          <Route path="fleet" element={<FleetManagementPage />} />
          <Route path="tasks" element={<TaskManagementPage />} />
          <Route path="coordination" element={<CoordinationMonitorPage />} />
          <Route path="ml-intelligence" element={<MLIntelligencePage />} />
          <Route path="analytics" element={<PerformanceAnalyticsPage />} />
          <Route path="experiment-lab" element={<ExperimentLabPage />} />
          <Route path="settings" element={<SystemSettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

