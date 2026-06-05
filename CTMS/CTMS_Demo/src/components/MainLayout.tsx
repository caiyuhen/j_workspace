
import React, { useState } from 'react';
import { Layout, Menu, Breadcrumb } from 'antd';
import {
  DesktopOutlined,
  TeamOutlined,
  ProjectOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { ROLES, STAGES } from '../constants';

const { Header, Content, Footer, Sider } = Layout;

type MenuItem = Required<React.ComponentProps<typeof Menu>>['items'][number];

function getItem(
  label: React.ReactNode,
  key: React.Key,
  icon?: React.ReactNode,
  children?: MenuItem[],
): MenuItem {
  return {
    key,
    icon,
    children,
    label,
  } as MenuItem;
}

const items: MenuItem[] = [
  getItem('工作台', '/', <DesktopOutlined />),
  getItem('按角色分工', 'roles', <TeamOutlined />, 
    ROLES.map(role => getItem(role.label, `/role/${role.key}`))
  ),
  getItem('按流程管控', 'stages', <ProjectOutlined />, 
    STAGES.map(stage => getItem(stage.label, `/stage/${stage.key}`))
  ),
];

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
  };

  // Determine selected keys based on current path
  const selectedKeys = [location.pathname];
  // Determine open keys based on current path
  const openKeys = location.pathname.startsWith('/role') ? ['roles'] : 
                   location.pathname.startsWith('/stage') ? ['stages'] : [];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
        <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)', textAlign: 'center', color: 'white', lineHeight: '32px', fontWeight: 'bold' }}>
            Clinical Trial Process
        </div>
        <Menu 
            theme="dark" 
            defaultSelectedKeys={['/']} 
            selectedKeys={selectedKeys}
            defaultOpenKeys={openKeys}
            mode="inline" 
            items={items} 
            onClick={handleMenuClick}
        /> 
      </Sider>
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: 0, background: '#fff', paddingLeft: 16 }}>
            <h2>GCP 临床试验管理角色说明</h2>
        </Header>
        <Content style={{ margin: '0 16px' }}>
          <Breadcrumb 
            style={{ margin: '16px 0' }} 
            items={[
              { title: 'CTMS' },
              { title: location.pathname === '/' ? '工作台' : location.pathname.split('/')[1] === 'role' ? '角色视图' : '流程视图' }
            ]}
          />
          <div className="site-layout-background" style={{ padding: 24, minHeight: 360, background: '#fff' }}>
            <Outlet />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>CTMS Demo ©2023 Created for GCP Compliance</Footer>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
