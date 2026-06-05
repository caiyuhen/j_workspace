import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Trials from './pages/Trials';
import Subjects from './pages/Subjects';
import Sites from './pages/Sites';
import Documents from './pages/Documents';
import Safety from './pages/Safety';
import Monitoring from './pages/Monitoring';
import Users from './pages/Users';
import Drugs from './pages/Drugs';
import Specimens from './pages/Specimens';
import AuditTrail from './pages/AuditTrail';
import Layout from './components/Layout';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <div>加载中...</div>;
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
              <Route index element={<Dashboard />} />
              <Route path="trials" element={<Trials />} />
              <Route path="subjects" element={<Subjects />} />
              <Route path="sites" element={<Sites />} />
              <Route path="safety" element={<Safety />} />
              <Route path="monitoring" element={<Monitoring />} />
              <Route path="documents" element={<Documents />} />
              <Route path="users" element={<Users />} />
              <Route path="drugs" element={<Drugs />} />
              <Route path="specimens" element={<Specimens />} />
              <Route path="audit-trail" element={<AuditTrail />} />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
