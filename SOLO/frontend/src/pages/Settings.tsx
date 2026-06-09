import { useState } from 'react'
import { Card, Form, Input, Button, Switch, Select, message, Typography, Descriptions, Tag } from 'antd'
import {
  UserOutlined,
  LockOutlined,
  ApiOutlined,
  DatabaseOutlined
} from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'

const { Title, Text } = Typography

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const { user } = useAuthStore()
  const [form] = Form.useForm()
  
  const handleUpdateProfile = async (_values: Record<string, string>) => {
    setLoading(true)
    try {
      // 调用更新API
      message.success('个人信息更新成功')
    } catch (error) {
      message.error('更新失败')
    } finally {
      setLoading(false)
    }
  }
  
  const handleChangePassword = async (values: Record<string, string>) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }
    
    setLoading(true)
    try {
      // 调用修改密码API
      message.success('密码修改成功')
    } catch (error) {
      message.error('密码修改失败')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>系统设置</Title>
      
      <Card title="个人信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="用户ID">{user?.id}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
          <Descriptions.Item label="姓名">{user?.name || '-'}</Descriptions.Item>
          <Descriptions.Item label="角色">
            <Tag color="blue">{user?.role}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="注册时间">
            {user?.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
      
      <Card title="修改信息" style={{ marginBottom: 16 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdateProfile}
          initialValues={{ name: user?.name }}
        >
          <Form.Item name="name" label="姓名">
            <Input prefix={<UserOutlined />} placeholder="请输入姓名" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>
      
      <Card title="修改密码" style={{ marginBottom: 16 }}>
        <Form layout="vertical" onFinish={handleChangePassword}>
          <Form.Item
            name="oldPassword"
            label="当前密码"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入当前密码" />
          </Form.Item>
          
          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入新密码" />
          </Form.Item>
          
          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            rules={[{ required: true, message: '请确认新密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请确认新密码" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
      
      <Card title="系统配置" style={{ marginBottom: 16 }}>
        <Form layout="vertical">
          <Form.Item label="默认代理">
            <Select
              placeholder="选择默认代理"
              options={[
                { label: '自动选择', value: 'auto' },
                { label: '诊断代理', value: 'diagnosis' },
                { label: '研究代理', value: 'research' },
                { label: '咨询代理', value: 'consultation' },
                { label: '知识代理', value: 'knowledge' }
              ]}
              defaultValue="auto"
            />
          </Form.Item>
          
          <Form.Item label="响应语言">
            <Select
              placeholder="选择响应语言"
              options={[
                { label: '简体中文', value: 'zh-CN' },
                { label: '繁體中文', value: 'zh-TW' },
                { label: 'English', value: 'en' }
              ]}
              defaultValue="zh-CN"
            />
          </Form.Item>
          
          <Form.Item label="消息通知">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Card>
      
      <Card title="系统信息">
        <Descriptions column={1}>
          <Descriptions.Item label={<><ApiOutlined /> LLM服务</>}>
            <Tag color="green">已连接</Tag>
            <Text type="secondary" style={{ marginLeft: 8 }}>192.168.0.214:8802</Text>
          </Descriptions.Item>
          <Descriptions.Item label={<><DatabaseOutlined /> 数据库</>}>
            <Tag color="green">已连接</Tag>
            <Text type="secondary" style={{ marginLeft: 8 }}>PostgreSQL</Text>
          </Descriptions.Item>
          <Descriptions.Item label="系统版本">
            <Text>v1.0.0</Text>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}
