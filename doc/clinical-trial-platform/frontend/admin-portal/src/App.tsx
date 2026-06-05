import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  TeamOutlined,
  DatabaseOutlined,
  SettingOutlined,
} from '@ant-design/icons';

import Dashboard from './pages/Dashboard';
import TrialList from './pages/TrialList';
import StudySites from './pages/StudySites';
import CrfManager from './pages/CrfManager';
import DataEntry from './pages/DataEntry';
import Users from './pages/Users';
import Settings from './pages/Settings';

const { Header, Sider, Content } = Layout;

const App: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/trials',
      icon: <FileTextOutlined />,
      label: '试验管理',
    },
    {
      key: '/sites',
      icon: <TeamOutlined />,
      label: '研究中心',
    },
    {
      key: '/crf',
      icon: <DatabaseOutlined />,
      label: 'EDC 表单',
    },
    {
      key: '/data',
      icon: <DatabaseOutlined />,
      label: '数据录入',
    },
    {
      key: '/users',
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
          <div style={{
            height: 64,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: collapsed ? 12 : 16,
            fontWeight: 'bold'
          }}>
            {collapsed ? 'CTP' : '临床试验平台'}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={['/dashboard']}
            items={menuItems}
          />
        </Sider>
        <Layout>
          <Header style={{
            background: '#fff',
            padding: '0 24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ fontSize: 18, fontWeight: 'bold' }}>
              临床试验管理平台
            </div>
            <div>
              欢迎，管理员
            </div>
          </Header>
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/trials" element={<TrialList />} />
              <Route path="/sites" element={<StudySites />} />
              <Route path="/crf" element={<CrfManager />} />
              <Route path="/data" element={<DataEntry />} />
              <Route path="/users" element={<Users />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
};

export default App;
