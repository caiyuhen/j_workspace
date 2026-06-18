import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, List, Typography, Progress } from 'antd'
import {
  MessageOutlined,
  ToolOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import { conversationApi } from '../services/api'

const { Title, Text } = Typography

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalConversations: 0,
    totalMessages: 0,
    totalSkills: 0
  })
  const [recentConversations, setRecentConversations] = useState<Array<{
    id: string
    title: string | null
    updated_at: string
  }>>([])
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    try {
      const conversationsRes = await conversationApi.list(1, 5)
      
      setRecentConversations(conversationsRes.data.items || [])
      
      setStats({
        totalConversations: conversationsRes.data.total || 0,
        totalMessages: 0,
        totalSkills: 6
      })
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }
  
  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>仪表盘</Title>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="对话总数"
              value={stats.totalConversations}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="消息总数"
              value={stats.totalMessages}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="可用技能"
              value={stats.totalSkills}
              prefix={<ToolOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>
      
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="最近对话" extra={<a href="/history">查看全部</a>}>
            <List
              dataSource={recentConversations}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<MessageOutlined style={{ fontSize: 20, color: '#52c41a' }} />}
                    title={item.title || '新对话'}
                    description={
                      <Text type="secondary">
                        <ClockCircleOutlined style={{ marginRight: 4 }} />
                        {new Date(item.updated_at).toLocaleString('zh-CN')}
                      </Text>
                    }
                  />
                </List.Item>
              )}
              locale={{ emptyText: '暂无对话记录' }}
            />
          </Card>
        </Col>
      </Row>
      
      <Card title="系统资源" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Text>LLM服务连接</Text>
            <Progress percent={100} status="active" strokeColor="#52c41a" />
          </Col>
          <Col span={8}>
            <Text>数据库连接</Text>
            <Progress percent={100} status="active" strokeColor="#1890ff" />
          </Col>
          <Col span={8}>
            <Text>缓存服务</Text>
            <Progress percent={100} status="active" strokeColor="#722ed1" />
          </Col>
        </Row>
      </Card>
    </div>
  )
}
