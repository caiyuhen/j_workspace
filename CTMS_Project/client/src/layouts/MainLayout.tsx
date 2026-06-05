import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Typography, theme } from 'antd';
import {
  DashboardOutlined,
  ProjectOutlined,
  BankOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  SafetyOutlined,
  AuditOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ApartmentOutlined,
  DatabaseOutlined,
  FormOutlined,
  RobotOutlined,
  SolutionOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
  LockOutlined,
  BarChartOutlined,
  ExportOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/auth';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '工作台' },
  {
    key: 'ctms',
    icon: <ProjectOutlined />,
    label: 'CTMS 试验管理',
    children: [
      { key: '/ctms/projects', icon: <ProjectOutlined />, label: '项目管理' },
      { key: '/ctms/sites', icon: <BankOutlined />, label: '中心管理' },
      { key: '/ctms/ethics', icon: <SafetyCertificateOutlined />, label: '伦理审批' },
      { key: '/ctms/monitoring', icon: <AuditOutlined />, label: '监察管理' },
      { key: '/ctms/drugs', icon: <MedicineBoxOutlined />, label: '药物管理' },
      { key: '/ctms/documents', icon: <FileTextOutlined />, label: '文档管理' },
      { key: '/ctms/contracts', icon: <SolutionOutlined />, label: '合同管理' },
      { key: '/ctms/finance', icon: <DatabaseOutlined />, label: '财务收支' },
      { key: '/ctms/vendors', icon: <TeamOutlined />, label: '供应商管理' },
      { key: '/ctms/timesheet', icon: <FormOutlined />, label: '工时管理' },
    ],
  },
  {
    key: 'edc',
    icon: <ExperimentOutlined />,
    label: 'EDC 数据采集',
    children: [
      { key: '/edc/templates', icon: <FormOutlined />, label: '模板库' },
      { key: '/edc/subjects', icon: <UserOutlined />, label: '受试者管理' },
      { key: '/edc/consent', icon: <SafetyOutlined />, label: '知情同意' },
      { key: '/edc/data-entry', icon: <FormOutlined />, label: '数据录入' },
      { key: '/edc/edit-check', icon: <AuditOutlined />, label: '逻辑核查' },
      { key: '/edc/queries', icon: <BellOutlined />, label: '质疑管理' },
      { key: '/edc/ae', icon: <SafetyOutlined />, label: 'AE/SAE' },
      { key: '/edc/sdv', icon: <AuditOutlined />, label: 'SDV 核查' },
      { key: '/edc/randomization', icon: <ExperimentOutlined />, label: '随机化' },
      { key: '/edc/lock', icon: <LockOutlined />, label: '数据库锁定' },
    ],
  },
  { key: '/workflow', icon: <ApartmentOutlined />, label: '工作流' },
  { key: '/reports', icon: <BarChartOutlined />, label: '报告中心' },
  { key: '/export', icon: <ExportOutlined />, label: '数据导出' },
  { key: '/audit', icon: <AuditOutlined />, label: '审计日志' },
  { key: '/ai', icon: <RobotOutlined />, label: 'AI 助手' },
  { key: '/data-masking', icon: <EyeInvisibleOutlined />, label: '数据脱敏' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心' },
    { key: 'settings', icon: <SettingOutlined />, label: '账号设置' },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ];

  const onMenuClick = (info: { key: string }) => {
    navigate(info.key);
  };

  const onUserMenuClick = (info: { key: string }) => {
    if (info.key === 'logout') {
      logout();
      navigate('/login');
    }
  };

  // 展开当前路径对应的父级菜单
  const defaultOpenKeys = menuItems
    .filter((item) => 'children' in item && item.children?.some((c: any) => c.key === location.pathname))
    .map((item) => item.key);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={240}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 10,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <ExperimentOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          {!collapsed && (
            <Text strong style={{ color: '#fff', marginLeft: 10, fontSize: 16, whiteSpace: 'nowrap' }}>
              CTMS+EDC v4.0
            </Text>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={defaultOpenKeys}
          items={menuItems}
          onClick={onMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 240, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 9,
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
              style: { fontSize: 18, cursor: 'pointer' },
              onClick: () => setCollapsed(!collapsed),
            })}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
            <Dropdown menu={{ items: userMenuItems, onClick: onUserMenuClick }} placement="bottomRight">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <Text>{user?.displayName || user?.username || '用户'}</Text>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ margin: 24 }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
