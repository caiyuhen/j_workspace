import DoctorPatientFolderLayout from '../layouts/DoctorPatientFolderLayout';
import PatientListPage from '../pages/DoctorPatientFolder/PatientListPage';
import PatientDetailPage from '../pages/DoctorPatientFolder/PatientDetailPage';
import FormDesignerPage from '../pages/DoctorPatientFolder/FormDesignerPage';
import ReportsPage from '../pages/DoctorPatientFolder/ReportsPage';

// 定义路由配置
export const doctorPatientFolderRoutes = [
  {
    path: '/doctor-folder/*',
    component: DoctorPatientFolderLayout,
    routes: [
      {
        path: '/doctor-folder/patients',
        component: PatientListPage,
      },
      {
        path: '/doctor-folder/patient/:id',
        component: PatientDetailPage,
      },
      {
        path: '/doctor-folder/forms',
        component: FormDesignerPage,
      },
      {
        path: '/doctor-folder/reports',
        component: ReportsPage,
      },
    ],
  },
];