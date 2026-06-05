import EdcExportLayout from '../layouts/EdcExportLayout';
import ExportConfigPage from '../pages/EdcExport/ExportConfigPage';
import ExportHistoryPage from '../pages/EdcExport/ExportHistoryPage';
import ValidationPage from '../pages/EdcExport/ValidationPage';
import ReportsPage from '../pages/EdcExport/ReportsPage';

// 定义路由配置
export const edcExportRoutes = [
  {
    path: '/edc-export/*',
    component: EdcExportLayout,
    routes: [
      {
        path: '/edc-export/config',
        component: ExportConfigPage,
      },
      {
        path: '/edc-export/history',
        component: ExportHistoryPage,
      },
      {
        path: '/edc-export/validation',
        component: ValidationPage,
      },
      {
        path: '/edc-export/reports',
        component: ReportsPage,
      },
    ],
  },
];