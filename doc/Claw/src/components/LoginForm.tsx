import React, { useState } from 'react';
import { Form, Input, Button, message, Typography } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';
import styles from './LoginForm.module.css';

const { Title } = Typography;

interface LoginValues {
  username: string;
  password: string;
  remember: boolean;
}

const LoginForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const [form] = Form.useForm<LoginValues>();

  const onFinish = async (values: LoginValues) => {
    try {
      setLoading(true);
      await login(values.username, values.password);
      message.success('登录成功！');
    } catch (error) {
      console.error('登录失败:', error);
      message.error('用户名或密码错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const onFinishFailed = (errorInfo: any) => {
    console.log('验证失败:', errorInfo);
  };

  return (
    <div className={styles.formContainer}>
      <Title level={3} className={styles.formTitle}>
        用户登录
      </Title>
      
      <Form
        form={form}
        name="loginForm"
        layout="vertical"
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        autoComplete="off"
        className={styles.loginForm}
        size="large"
      >
        <Form.Item
          name="username"
          label="用户名"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少 3 个字符' }
          ]}
        >
          <Input
            prefix={<UserOutlined className={styles.prefixIcon} />}
            placeholder="请输入用户名"
            allowClear
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="密码"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少 6 个字符' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined className={styles.prefixIcon} />}
            placeholder="请输入密码"
            onPressEnter={() => form.submit()}
          />
        </Form.Item>

        <Form.Item>
          <div className={styles.formActions}>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <span className={styles.remember}>记住我</span>
            </Form.Item>
            <a className={styles.forgot}>忘记密码？</a>
          </div>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<LoginOutlined />}
            className={styles.submitButton}
            block
          >
            {loading ? '登录中...' : '登 录'}
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default LoginForm;
