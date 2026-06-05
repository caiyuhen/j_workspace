import React from 'react';
import { Layout, Menu, Breadcrumb } from 'antd';
import { Link, Route, Routes } from 'react-router-dom';
import { 
  FileSearchOutlined, 
  FileOutlined, 
  HistoryOutlined,
  ExportOutlined 
} from '@ant-design/icons';
import ExportConfigPage from '../pages/EdcExport/ExportConfigPage';
import ExportHistoryPage from '../pages/EdcExport/ExportHistoryPage';
import ValidationPage from '../pages/EdcExport/ValidationPage';
import ReportsPage from '../pages/EdcExport/ReportsPage';

const { Header, Sider, Content } = Layout;

const EdcExportLayout = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider>
        <div style={{ height: 32, margin: 16, background: 'rgba(255,255,255,.2)' }} />
        <Menu 
          theme="dark" 
          defaultSelectedKeys={['1']} 
          mode="inline" 
          items={[
            {
              key: '1',
              icon: <ExportOutlined />,
              label: <Link to="/edc-export/config">导出配置</Link>,
            },
            {
              key: '2',
              icon: <HistoryOutlined />,
              label: <Link to="/edc-export/history">导出历史</Link>,
            },
            {
              key: '3',
              icon: <FileOutlined />,
              label: <Link to="/edc-export/validation">合规性验证</Link>,
            },
            {
              key: '4',
              icon: <FileSearchOutlined />,
              label: <Link to="/edc-export/reports">导出报告</Link>,
            },
          ]}
        />
      </Sider>
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: 0 }} />
        <Content style={{ margin: '0 16px' }}>
          <Breadcrumb 
            style={{ margin: '16px 0' }} 
            items={[
              { title: 'EDC导出管理' }
            ]}
          />
          <div className="site-layout-background" style={{ padding: 24, minHeight: 360 }}>
            <Routes>
              <Route path="config" element={<ExportConfigPage />} />
              <Route path="history" element={<ExportHistoryPage />} />
              <Route path="validation" element={<ValidationPage />} />
              <Route path="reports" element={<ReportsPage />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default EdcExportLayout;