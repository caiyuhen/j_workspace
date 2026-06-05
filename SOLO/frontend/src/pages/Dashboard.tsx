import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, List, Tag, Typography, Progress } from 'antd'
import {
  MessageOutlined,
  RobotOutlined,
  ToolOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons'
import { agentApi, conversationApi } from '../services/api'

const { Title, Text } = Typography

interface AgentInfo {
  name: string
  type: string
  status: string
}

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalConversations: 0,
    totalMessages: 0,
    activeAgents: 0,
    totalSkills: 0
  })
  const [agents, setAgents] = useState<AgentInfo[]>([])
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
      const [agentsRes, conversationsRes] = await Promise.all([
        agentApi.list(),
        conversationApi.list(1, 5)
      ])
      
      setAgents(agentsRes.data)
      setRecentConversations(conversationsRes.data.items || [])
      
      setStats({
        totalConversations: conversationsRes.data.total || 0,
        totalMessages: 0,
        activeAgents: agentsRes.data.filter((a: AgentInfo) => a.status === 'idle').length,
        totalSkills: 6
      })
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }
  
  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; icon: React.ReactNode }> = {
      idle: { color: 'green', icon: <CheckCircleOutlined /> },
      busy: { color: 'blue', icon: <SyncOutlined spin /> },
      error: { color: 'red', icon: null }
    }
    const config = statusMap[status] || { color: 'default', icon: null }
    return <Tag color={config.color} icon={config.icon}>{status}</Tag>
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
              title="活跃代理"
              value={stats.activeAgents}
              suffix={`/ ${agents.length}`}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#722ed1' }}
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
        <Col xs={24} lg={12}>
          <Card title="代理状态" extra={<a href="/agents">查看全部</a>}>
            <List
              dataSource={agents.slice(0, 5)}
              renderItem={(agent) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<RobotOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                    title={agent.name}
                    description={agent.type}
                  />
                  {getStatusTag(agent.status)}
                </List.Item>
              )}
              locale={{ emptyText: '暂无代理' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
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
