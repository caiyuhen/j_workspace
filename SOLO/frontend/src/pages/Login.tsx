import { useState } from 'react'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { UserOutlined, LockOutlined, RobotOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { authApi } from '../services/api'

const { Title, Text } = Typography

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  
  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const tokenRes = await authApi.login(values)
      
      // 先保存 token 到 store，这样后续请求才能带上 Authorization header
      useAuthStore.getState().setToken(tokenRes.data)
      
      // 然后再获取用户信息
      const userRes = await authApi.getMe()
      
      setAuth(userRes.data, tokenRes.data)
      message.success('登录成功')
      navigate('/dashboard')
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      message.error(err.response?.data?.detail || '登录失败，请检查邮箱和密码')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <RobotOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          <Title level={2} style={{ marginTop: 16, marginBottom: 0 }}>
            医学智能体系统
          </Title>
          <Text type="secondary">多代理协同智能医疗平台</Text>
        </div>
        
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="邮箱地址" 
            />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="密码" 
            />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
          
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">
              还没有账号？ <Link to="/register">立即注册</Link>
            </Text>
          </div>
        </Form>
        
        <div style={{ 
          marginTop: 24, 
          padding: 16, 
          background: '#f5f5f5', 
          borderRadius: 8 
        }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            测试账号：<br />
            admin@medical.ai / admin123<br />
            doctor@medical.ai / doctor123
          </Text>
        </div>
      </Card>
    </div>
  )
}
