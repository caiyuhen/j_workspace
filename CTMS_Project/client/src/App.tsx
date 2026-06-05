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