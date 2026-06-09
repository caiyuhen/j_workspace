import { useEffect, useState } from 'react'
import { Card, Row, Col, List, Tag, Typography, Badge, Descriptions, Empty, Button, Space, Modal, Form, Input, Select, message, Divider, Spin } from 'antd'
import {
  RobotOutlined,
  ThunderboltOutlined,
  CloudDownloadOutlined,
  UploadOutlined,
  PlayCircleOutlined
} from '@ant-design/icons'
import { agentApi, Agent } from '../services/api'

const { Title, Text } = Typography

const agentDescriptions: Record<string, { desc: string; color: string }> = {
  orchestrator: { desc: '任务编排代理，负责分解和协调复杂任务', color: '#722ed1' },
  diagnosis: { desc: '临床诊断代理，提供疾病诊断和鉴别诊断支持', color: '#1890ff' },
  research: { desc: '医学研究代理，检索和分析医学文献', color: '#52c41a' },
  consultation: { desc: '健康咨询代理，提供健康建议和疾病预防指导', color: '#fa8c16' },
  knowledge: { desc: '知识查询代理，检索医学知识库和临床指南', color: '#13c2c2' },
  tool: { desc: '工具集成代理，调用外部工具和Skill服务', color: '#eb2f96' },
  quality: { desc: '质量控制代理，验证输出质量和一致性', color: '#faad14' },
  learning: { desc: '学习优化代理，持续学习和优化系统性能', color: '#2f54eb' }
}

// 代理类型中文名称映射
const agentTypeNames: Record<string, string> = {
  orchestrator: '编排代理',
  diagnosis: '诊断代理',
  research: '研究代理',
  consultation: '咨询代理',
  knowledge: '知识代理',
  tool: '工具代理',
  quality: '质控代理',
  learning: '学习代理'
}

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [installModalVisible, setInstallModalVisible] = useState(false)
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [onlineAgents, setOnlineAgents] = useState<any[]>([])
  const [onlineLoading, setOnlineLoading] = useState(false)
  const [agentForm] = Form.useForm()
  
  useEffect(() => {
    loadAgents()
  }, [])
  
  const loadAgents = async () => {
    try {
      const res = await agentApi.list()
      setAgents(res.data)
    } catch (error) {
      console.error('加载代理失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  // 从在线仓库获取代理列表
  const loadOnlineAgents = async () => {
    setOnlineLoading(true)
    try {
      // 模拟从在线仓库获取代理列表
      const mockAgents = [
        {
          id: 'agent_medical_imaging',
          name: '影像诊断代理',
          type: 'imaging',
          description: '专业医学影像分析代理，支持X光、CT、MRI影像解读',
          author: 'ClawHub',
          downloads: 1200,
          rating: 4.7
        },
        {
          id: 'agent_mental_health',
          name: '心理健康代理',
          type: 'consultation',
          description: '心理健康评估和咨询代理，提供心理状态分析',
          author: 'ClawHub',
          downloads: 890,
          rating: 4.5
        },
        {
          id: 'agent_emergency',
          name: '急诊分诊代理',
          type: 'diagnosis',
          description: '急诊分诊辅助代理，快速评估病情紧急程度',
          author: 'ClawHub',
          downloads: 2100,
          rating: 4.8
        }
      ]
      setOnlineAgents(mockAgents)
    } catch (error) {
      message.error('获取在线代理失败')
    } finally {
      setOnlineLoading(false)
    }
  }
  
  const handleInstallFromOnline = async (agent: any) => {
    try {
      // 调用后端 API 注册代理
      await agentApi.register({
        name: agent.name,
        type: agent.type,
        description: agent.description,
        config: {
          endpoint: `https://api.clawhub.ai/agents/${agent.id}`,
          author: agent.author
        }
      })
      message.success(`代理 "${agent.name}" 安装成功`)
      setInstallModalVisible(false)
      loadAgents()
    } catch (error) {
      message.error('安装失败，请检查网络连接')
    }
  }
  
  const handleImportLocal = async (_values: any) => {
    try {
      // 这里应该调用后端 API 创建代理
      message.success('导入成功')
      setImportModalVisible(false)
      agentForm.resetFields()
      loadAgents()
    } catch (error) {
      message.error('导入失败')
    }
  }
  
  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { status: 'success' | 'processing' | 'error'; text: string }> = {
      idle: { status: 'success', text: '空闲' },
      busy: { status: 'processing', text: '忙碌' },
      error: { status: 'error', text: '异常' }
    }
    const config = statusConfig[status] || { status: 'error', text: '未知' }
    return <Badge status={config.status} text={config.text} />
  }
  
  const getAgentIcon = (type: string) => {
    const colors: Record<string, string> = {
      orchestrator: '#722ed1',
      diagnosis: '#1890ff',
      research: '#52c41a',
      consultation: '#fa8c16',
      knowledge: '#13c2c2',
      tool: '#eb2f96',
      quality: '#faad14',
      learning: '#2f54eb',
      imaging: '#2f54eb',
      emergency: '#f5222d'
    }
    return (
      <div style={{
        width: 48,
        height: 48,
        borderRadius: 12,
        background: colors[type] || '#1890ff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <RobotOutlined style={{ fontSize: 24, color: 'white' }} />
      </div>
    )
  }
  
  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>代理管理</Title>
      
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Text type="secondary">
            共 {agents.length} 个代理
          </Text>
          <div style={{ flex: 1 }} />
          <Button
            type="primary"
            icon={<CloudDownloadOutlined />}
            onClick={() => {
              setInstallModalVisible(true)
              loadOnlineAgents()
            }}
          >
            在线安装
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={() => setImportModalVisible(true)}
          >
            导入本地
          </Button>
        </Space>
      </Card>
      
      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="已注册代理" loading={loading}>
            {agents.length === 0 ? (
              <Empty description="暂无代理" />
            ) : (
              <List
                dataSource={agents}
                renderItem={(agent) => (
                  <List.Item
                    onClick={() => setSelectedAgent(agent)}
                    style={{
                      cursor: 'pointer',
                      background: selectedAgent?.name === agent.name ? '#f5f5f5' : 'transparent',
                      borderRadius: 8,
                      padding: '12px 16px'
                    }}
                  >
                    <List.Item.Meta
                      avatar={getAgentIcon(agent.type)}
                      title={
                        <Space>
                          <Text strong>{agent.name}</Text>
                          <Tag color={agentDescriptions[agent.type]?.color || '#1890ff'}>
                            {agentTypeNames[agent.type] || agent.type}
                          </Tag>
                        </Space>
                      }
                      description={agent.description || agentDescriptions[agent.type]?.desc}
                    />
                    {getStatusBadge(agent.status)}
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="代理详情">
            {selectedAgent ? (
              <div>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  {getAgentIcon(selectedAgent.type)}
                  <Title level={4} style={{ marginTop: 16 }}>{selectedAgent.name}</Title>
                  {getStatusBadge(selectedAgent.status)}
                </div>
                
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="类型">{agentTypeNames[selectedAgent.type] || selectedAgent.type}</Descriptions.Item>
                  <Descriptions.Item label="状态">{getStatusBadge(selectedAgent.status)}</Descriptions.Item>
                  <Descriptions.Item label="描述">
                    {selectedAgent.description || agentDescriptions[selectedAgent.type]?.desc}
                  </Descriptions.Item>
                  <Descriptions.Item label="能力">
                    <div>
                      {selectedAgent.capabilities?.map((cap, idx) => (
                        <Tag key={idx} style={{ marginBottom: 4 }}>
                          <ThunderboltOutlined style={{ marginRight: 4 }} />
                          {cap}
                        </Tag>
                      ))}
                    </div>
                  </Descriptions.Item>
                </Descriptions>
                
                <Divider />
                
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    block
                    onClick={() => message.info('功能开发中')}
                  >
                    测试代理
                  </Button>
                </Space>
              </div>
            ) : (
              <Empty description="请选择一个代理查看详情" />
            )}
          </Card>
        </Col>
      </Row>
      
      {/* 在线安装弹窗 */}
      <Modal
        title="从在线仓库安装代理"
        open={installModalVisible}
        onCancel={() => setInstallModalVisible(false)}
        footer={null}
        width={700}
      >
        <Tabs
          items={[
            {
              key: 'online',
              label: '在线代理库',
              icon: <CloudDownloadOutlined />,
              children: (
                <Spin spinning={onlineLoading}>
                  <List
                    dataSource={onlineAgents}
                    renderItem={(agent) => (
                      <List.Item
                        actions={[
                          <Button
                            type="primary"
                            size="small"
                            icon={<CloudDownloadOutlined />}
                            onClick={() => handleInstallFromOnline(agent)}
                          >
                            安装
                          </Button>
                        ]}
                      >
                        <List.Item.Meta
                          avatar={getAgentIcon(agent.type)}
                          title={
                            <Space>
                              <Text strong>{agent.name}</Text>
                              <Tag color="blue">{agent.author}</Tag>
                            </Space>
                          }
                          description={
                            <Space direction="vertical" size={0}>
                              <Text type="secondary">{agent.description}</Text>
                              <Space size="small">
                                <Text type="secondary">下载: {agent.downloads}</Text>
                                <Text type="secondary">评分: {agent.rating}</Text>
                              </Space>
                            </Space>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </Spin>
              )
            },
            {
              key: 'url',
              label: '通过 URL 安装',
              icon: <RobotOutlined />,
              children: (
                <Form layout="vertical" onFinish={() => {
                  message.success('安装成功')
                  setInstallModalVisible(false)
                }}>
                  <Form.Item
                    name="url"
                    label="代理配置 URL"
                    rules={[{ required: true, message: '请输入 URL' }]}
                  >
                    <Input placeholder="https://clawhub.ai/agents/xxx" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" block>
                      安装
                    </Button>
                  </Form.Item>
                </Form>
              )
            }
          ]}
        />
      </Modal>
      
      {/* 导入本地代理弹窗 */}
      <Modal
        title="导入本地代理"
        open={importModalVisible}
        onCancel={() => {
          setImportModalVisible(false)
          agentForm.resetFields()
        }}
        onOk={() => agentForm.submit()}
        width={600}
      >
        <Form form={agentForm} layout="vertical" onFinish={handleImportLocal}>
          <Form.Item
            name="name"
            label="代理名称"
            rules={[{ required: true, message: '请输入代理名称' }]}
          >
            <Input placeholder="例如: 自定义诊断代理" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="代理类型"
            rules={[{ required: true, message: '请输入代理类型' }]}
          >
            <Input placeholder="例如: custom_diagnosis" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={2} placeholder="代理功能描述..." />
          </Form.Item>
          
          <Form.Item
            name="capabilities"
            label="能力列表（每行一个）"
          >
            <Input.TextArea rows={4} placeholder="capability_1&#10;capability_2&#10;capability_3" />
          </Form.Item>
          
          <Form.Item
            name="model"
            label="使用的模型"
          >
            <Select placeholder="选择模型" allowClear>
              <Select.Option value="default">默认模型</Select.Option>
              <Select.Option value="gpt4">GPT-4</Select.Option>
              <Select.Option value="claude">Claude</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="system_prompt"
            label="系统提示词"
          >
            <Input.TextArea rows={4} placeholder="你是一个专业的医学代理..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// 添加必要的导入
import { Tabs } from 'antd'
