<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { doctorPatientFolderRoutes } from './routes/doctor-patient-folder.routes';
import { edcExportRoutes } from './routes/edc-export.routes';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/doctor-folder/patients" replace />} />
        
        {/* 其他路由 */}
        {doctorPatientFolderRoutes.map((route) => {
          const Component = route.component;
          return (
            <Route
              key={route.path}
              path={route.path}
              element={<Component />}
            />
          );
        })}
        {edcExportRoutes.map((route) => {
          const Component = route.component;
          return (
            <Route
              key={route.path}
              path={route.path}
              element={<Component />}
            />
          );
        })}
      </Routes>
    </Router>
  );
};

export default App;
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import MainLayout from '@/layouts/MainLayout';
import LoginPage from '@/pages/Login';
import DashboardPage from '@/pages/Dashboard';

// CTMS 核心页面
import ProjectsPage from '@/pages/Projects';
import SitesPage from '@/pages/Sites';
import MonitoringPage from '@/pages/Monitoring';
import DrugsPage from '@/pages/Drugs';
import DocumentsPage from '@/pages/Documents';
import FinancePage from '@/pages/Finance';
import TimesheetPage from '@/pages/Timesheet';

// EDC 数据采集
import TemplatesPage from '@/pages/Templates';
import SubjectsPage from '@/pages/Subjects';
import DataEntryPage from '@/pages/DataEntry';
import QueriesPage from '@/pages/Queries';
import AePage from '@/pages/Ae';
import SdvPage from '@/pages/Sdv';
import RandomizationPage from '@/pages/Randomization';

// 工作流与系统
import WorkflowPage from '@/pages/Workflow';
import AuditPage from '@/pages/Audit';
import AiPage from '@/pages/Ai';
import SettingsPage from '@/pages/Settings';
import createPlaceholderPage from '@/pages/Placeholder';

import EthicsPage from '@/pages/Ethics';
import ContractPage from '@/pages/Contracts';
import VendorPage from '@/pages/Vendors';
const ConsentPage = createPlaceholderPage('知情同意管理', '管理受试者eConsent签署及知情版本');
const EditCheckPage = createPlaceholderPage('逻辑核查', '配置和运行数据逻辑核查规则(Edit Checks)');
const LockPage = createPlaceholderPage('数据库锁定', '管理数据库锁定申请、审批及执行流程');
const ReportPage = createPlaceholderPage('报告中心', '各类业务报表、数据大屏及自定义报告');
const ExportPage = createPlaceholderPage('数据导出', '按CDISC标准导出临床数据及相关日志');
const DataMaskingPage = createPlaceholderPage('数据脱敏', '配置敏感数据脱敏规则及脱敏审计');

import { useAuthStore } from '@/stores/auth';
import { authApi } from '@/api/auth';

// 需要认证的路由守卫
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const loading = useAuthStore((s) => s.loading);
  const setUser = useAuthStore((s) => s.setUser);

  useEffect(() => {
    if (isAuthenticated) {
      authApi
        .me()
        .then((res) => setUser(res.data))
        .catch(() => {
          useAuthStore.getState().logout();
        });
    }
  }, [isAuthenticated, setUser]);

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  return <>{children}</>;
};

const App: React.FC = () => (
  <BrowserRouter>
    <Routes>
      {/* 公开路由 */}
      <Route path="/login" element={<LoginPage />} />

      {/* 受保护路由 */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        
        {/* CTMS 核心管理 */}
        <Route path="/ctms/projects" element={<ProjectsPage />} />
        <Route path="/ctms/sites" element={<SitesPage />} />
        <Route path="/ctms/ethics" element={<EthicsPage />} />
        <Route path="/ctms/monitoring" element={<MonitoringPage />} />
        <Route path="/ctms/drugs" element={<DrugsPage />} />
        <Route path="/ctms/documents" element={<DocumentsPage />} />
        <Route path="/ctms/contracts" element={<ContractPage />} />
        <Route path="/ctms/finance" element={<FinancePage />} />
        <Route path="/ctms/vendors" element={<VendorPage />} />
        <Route path="/ctms/timesheet" element={<TimesheetPage />} />

        {/* EDC 数据采集 */}
        <Route path="/edc/templates" element={<TemplatesPage />} />
        <Route path="/edc/subjects" element={<SubjectsPage />} />
        <Route path="/edc/consent" element={<ConsentPage />} />
        <Route path="/edc/data-entry" element={<DataEntryPage />} />
        <Route path="/edc/edit-check" element={<EditCheckPage />} />
        <Route path="/edc/queries" element={<QueriesPage />} />
        <Route path="/edc/ae" element={<AePage />} />
        <Route path="/edc/sdv" element={<SdvPage />} />
        <Route path="/edc/randomization" element={<RandomizationPage />} />
        <Route path="/edc/lock" element={<LockPage />} />

        {/* 工作流与系统 */}
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="/reports" element={<ReportPage />} />
        <Route path="/export" element={<ExportPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/ai" element={<AiPage />} />
        <Route path="/data-masking" element={<DataMaskingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* 兜底 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </BrowserRouter>
);

export default App;
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
