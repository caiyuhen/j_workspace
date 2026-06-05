import React from 'react';
import { Layout, Menu, Breadcrumb } from 'antd';
import { Route, Routes, Link } from 'react-router-dom';
import { AppstoreOutlined, UserOutlined, FileSearchOutlined } from '@ant-design/icons';

import PatientListPage from '../pages/DoctorPatientFolder/PatientListPage';
import FormDesignerPage from '../pages/DoctorPatientFolder/FormDesignerPage';
import ReportsPage from '../pages/DoctorPatientFolder/ReportsPage';

const { Header, Sider, Content } = Layout;

const DoctorPatientFolderLayout = () => {
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
              icon: <AppstoreOutlined />,
              label: <Link to="/doctor-folder/patients">患者管理</Link>,
            },
            {
              key: '2',
              icon: <UserOutlined />,
              label: <Link to="/doctor-folder/forms">表单模板</Link>,
            },
            {
              key: '3',
              icon: <FileSearchOutlined />,
              label: <Link to="/doctor-folder/reports">数据统计</Link>,
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
              { title: '医生病历夹' }
            ]}
          />
          <div className="site-layout-background" style={{ padding: 24, minHeight: 360 }}>
            <Routes>
              <Route path="patients" element={<PatientListPage />} />
              <Route path="forms" element={<FormDesignerPage />} />
              <Route path="reports" element={<ReportsPage />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default DoctorPatientFolderLayout;