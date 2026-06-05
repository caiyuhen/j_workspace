import React from 'react';
import {  Form, Input, Button, Card, Typography, Row, Col , App } from 'antd';
import { UserOutlined, LockOutlined, ExperimentOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '@/api/auth';
import { useAuthStore } from '@/stores/auth';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const res = await authApi.login(values);
      login(res.data.accessToken, {
        id: res.data.user.id,
        username: res.data.user.username,
        email: res.data.user.email,
        displayName: res.data.user.displayName,
        role: res.data.user.role });
      message.success('登录成功');
      navigate('/');
    } catch (err: any) {
      message.error(err.response?.data?.error?.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Row justify="center" align="middle" style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Col xs={22} sm={16} md={12} lg={8} xl={6}>
        <Card
          style={{ borderRadius: 12, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}
        >
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <ExperimentOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <Title level={3} style={{ marginTop: 12, marginBottom: 4 }}>
              CTMS+EDC 临床试验管理系统
            </Title>
            <Text type="secondary">v4.0 — ICH GCP / 21 CFR Part 11 合规</Text>
          </div>

          <Form form={form} name="login" onFinish={onFinish} size="large" autoComplete="off">
            <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input prefix={<UserOutlined />} placeholder="用户名" />
            </Form.Item>
            <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                登录
              </Button>
            </Form.Item>
            <div style={{ textAlign: 'center' }}>
              <Link to="/register">注册新账号</Link>
            </div>
          </Form>
        </Card>
      </Col>
    </Row>
  );
};

export default LoginPage;
