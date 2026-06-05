import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import LoginPage from './pages/LoginPage';
import useAuthStore from './store/authStore';
import './App.css';

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f0f2f5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px' }}>加载中...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// 临时首页组件
const HomePage: React.FC = () => {
  const { user, logout } = useAuthStore();

  return (
    <div style={{ padding: '24px', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto',
        backgroundColor: '#fff',
        padding: '24px',
        borderRadius: '8px'
      }}>
        <h1 style={{ marginBottom: '16px' }}>欢迎使用 CTMS + EDC 平台</h1>
        <p>当前用户：<strong>{user?.username}</strong></p>
        <p>角色：{user?.role}</p>
        <p>邮箱：{user?.email}</p>
        <button 
          onClick={logout}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#ff4d4f',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          登出
        </button>
      </div>
    </div>
  );
};

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          {/* 登录页面 - 始终可访问 */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* 受保护的路由 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          
          {/* 未来添加更多路由 */}
          {/* <Route path="/ecrf-designer" element={<ECRFDesigner />} /> */}
          {/* <Route path="/data-entry" element={<DataEntry />} /> */}
          
          {/* 404 - 重定向到首页 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
