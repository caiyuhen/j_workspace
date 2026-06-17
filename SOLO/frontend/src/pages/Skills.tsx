import { useEffect, useState } from 'react'
import { Card, Row, Col, List, Tag, Typography, Empty, Input, Select, Button, Space, Modal, Form, message, Tabs, Divider, Descriptions, Spin, Alert } from 'antd'
import {
  ToolOutlined,
  PlayCircleOutlined,
  ApiOutlined,
  CloudDownloadOutlined,
  UploadOutlined,
  DeleteOutlined
} from '@ant-design/icons'
import { skillApi, Skill, SkillCandidate } from '../services/api'

const { Title, Text, Paragraph } = Typography
const { Search } = Input

// 分类中文名称映射
const categoryNames: Record<string, string> = {
  diagnosis: '诊断',
  pharmacy: '药学',
  research: '研究',
  reference: '参考',
  imaging: '影像',
  consultation: '咨询'
}

export default function Skills() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [filteredSkills, setFilteredSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)
  const [searchText, setSearchText] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [executeModalVisible, setExecuteModalVisible] = useState(false)
  const [installModalVisible, setInstallModalVisible] = useState(false)
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [onlineSkills, setOnlineSkills] = useState<SkillCandidate[]>([])
  const [onlineLoading, setOnlineLoading] = useState(false)
  // 在线搜索（POST /skills/search）状态
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchLocal, setSearchLocal] = useState<Array<{ skill_id: string | null; title: string; description?: string | null; url?: string | null }>>([])
  const [searchRemote, setSearchRemote] = useState<Array<{ skill_id: string | null; title: string; description?: string | null; url?: string | null }>>([])
  const [searchRemoteStatus, setSearchRemoteStatus] = useState<'ok' | 'unavailable' | 'disabled' | ''>('')
  const [searchRemoteMessage, setSearchRemoteMessage] = useState<string>('')
  const [form] = Form.useForm()
  const [installForm] = Form.useForm()
  
  useEffect(() => {
    loadSkills()
  }, [])
  
  useEffect(() => {
    filterSkills()
  }, [skills, searchText, categoryFilter])
  
  const loadSkills = async () => {
    try {
      const res = await skillApi.list()
      setSkills(res.data)
    } catch (error) {
      console.error('加载技能失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const filterSkills = () => {
    let filtered = skills
    
    if (searchText) {
      filtered = filtered.filter(s => 
        s.name.includes(searchText) || 
        s.display_name.includes(searchText) ||
        s.description?.includes(searchText)
      )
    }
    
    if (categoryFilter) {
      filtered = filtered.filter(s => s.category === categoryFilter)
    }
    
    setFilteredSkills(filtered)
  }
  
  // 方案B：发现候选技能，但不自动安装
  const loadOnlineSkills = async () => {
    setOnlineLoading(true)
    try {
      const res = await skillApi.discover({ query: searchText || undefined })
      setOnlineSkills(res.data.candidates)
    } catch (error) {
      message.error('发现候选技能失败')
    } finally {
      setOnlineLoading(false)
    }
  }
  
  const handleInstallFromOnline = async (skill: SkillCandidate) => {
    Modal.confirm({
      title: '确认安装候选技能？',
      content: `将安装「${skill.display_name}」。系统不会自动安装技能，只有确认后才会加入可用技能列表。`,
      okText: '确认安装',
      cancelText: '取消',
      onOk: async () => {
        try {
          await skillApi.installCandidate(skill.id)
          message.success(`技能 "${skill.display_name}" 安装成功`)
          setInstallModalVisible(false)
          loadSkills()
        } catch (error) {
          message.error('安装失败')
        }
      }
    })
  }
  
  const handleImportLocal = async (values: any) => {
    try {
      await skillApi.create({
        name: values.name,
        display_name: values.display_name,
        description: values.description,
        category: values.category,
        protocol: values.protocol,
        config: values.config || {},
        input_schema: values.input_schema ? JSON.parse(values.input_schema) : {},
        output_schema: values.output_schema ? JSON.parse(values.output_schema) : {}
      })
      message.success('导入成功')
      setImportModalVisible(false)
      installForm.resetFields()
      loadSkills()
    } catch (error) {
      message.error('导入失败')
    }
  }
  
  const handleExecute = async (values: Record<string, unknown>) => {
    if (!selectedSkill) return
    
    try {
      await skillApi.execute(selectedSkill.id, values)
      message.success('技能执行成功')
      setExecuteModalVisible(false)
      form.resetFields()
    } catch (error) {
      message.error('技能执行失败')
    }
  }
  
  const handleDelete = async (skillId: string) => {
    try {
      await skillApi.delete(skillId)
      message.success('删除成功')
      setSelectedSkill(null)
      loadSkills()
    } catch (error) {
      message.error('删除失败')
    }
  }
  
  const getProtocolTag = (protocol: string) => {
    const colors: Record<string, string> = {
      builtin: 'blue',
      skillhub: 'green',
      mcp: 'purple'
    }
    const labels: Record<string, string> = {
      builtin: '内置',
      skillhub: 'SkillHub',
      mcp: 'MCP'
    }
    return <Tag color={colors[protocol] || 'default'}>{labels[protocol] || protocol.toUpperCase()}</Tag>
  }
  
  const getCategoryIcon = (category: string) => {
    const colors: Record<string, string> = {
      diagnosis: '#1890ff',
      pharmacy: '#52c41a',
      research: '#722ed1',
      reference: '#fa8c16',
      imaging: '#eb2f96',
      consultation: '#13c2c2'
    }
    return (
      <div style={{
        width: 48,
        height: 48,
        borderRadius: 12,
        background: colors[category] || '#1890ff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <ToolOutlined style={{ fontSize: 24, color: 'white' }} />
      </div>
    )
  }
  
  const categories = [...new Set(skills.map(s => s.category))]
  
  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>技能中心</Title>
      
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Search
            placeholder="搜索技能名称或描述..."
            allowClear
            style={{ width: 280 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Select
            placeholder="选择分类"
            allowClear
            style={{ width: 150 }}
            value={categoryFilter || undefined}
            onChange={setCategoryFilter}
            options={categories.map(c => ({ label: categoryNames[c] || c, value: c }))}
          />
          <Text type="secondary">
            共 {filteredSkills.length} 个技能
          </Text>
          <div style={{ flex: 1 }} />
          <Button
            type="primary"
            icon={<CloudDownloadOutlined />}
            onClick={() => {
              setInstallModalVisible(true)
              loadOnlineSkills()
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
        <Col xs={24} lg={14}>
          <Card title="可用技能" loading={loading}>
            {filteredSkills.length === 0 ? (
              <Empty description="暂无技能" />
            ) : (
              <List
                grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 2, xl: 2 }}
                dataSource={filteredSkills}
                renderItem={(skill) => (
                  <List.Item>
                    <Card
                      hoverable
                      onClick={() => setSelectedSkill(skill)}
                      style={{
                        border: selectedSkill?.id === skill.id ? '2px solid #1890ff' : undefined
                      }}
                    >
                      <Card.Meta
                        avatar={getCategoryIcon(skill.category)}
                        title={
                          <Space direction="vertical" size={0}>
                            <Text strong>{skill.display_name}</Text>
                            {getProtocolTag(skill.protocol)}
                          </Space>
                        }
                        description={
                          <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
                            {skill.description}
                          </Paragraph>
                        }
                      />
                    </Card>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        
        <Col xs={24} lg={10}>
          <Card title="技能详情">
            {selectedSkill ? (
              <div>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  {getCategoryIcon(selectedSkill.category)}
                  <Title level={4} style={{ marginTop: 16 }}>{selectedSkill.display_name}</Title>
                  <Space>
                    {getProtocolTag(selectedSkill.protocol)}
                    <Tag color={selectedSkill.is_active ? 'green' : 'red'}>
                      {selectedSkill.is_active ? '已启用' : '已禁用'}
                    </Tag>
                  </Space>
                </div>
                
                <Paragraph>{selectedSkill.description}</Paragraph>
                
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="分类">
                    <Tag>{categoryNames[selectedSkill.category] || selectedSkill.category}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="使用次数">
                    <Text strong>{selectedSkill.usage_count}</Text>
                  </Descriptions.Item>
                </Descriptions>
                
                <Divider />
                
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={() => setExecuteModalVisible(true)}
                    disabled={!selectedSkill.is_active}
                    block
                  >
                    执行技能
                  </Button>
                  {!selectedSkill.is_builtin && (
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => handleDelete(selectedSkill.id)}
                      block
                    >
                      删除技能
                    </Button>
                  )}
                </Space>
              </div>
            ) : (
              <Empty description="请选择一个技能查看详情" />
            )}
          </Card>
        </Col>
      </Row>
      
      {/* 执行技能弹窗 */}
      <Modal
        title={`执行技能: ${selectedSkill?.display_name}`}
        open={executeModalVisible}
        onCancel={() => {
          setExecuteModalVisible(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleExecute}>
          <Form.Item
            name="input"
            label="输入参数"
            rules={[{ required: true, message: '请输入参数' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入 JSON 格式的参数..." />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 在线安装弹窗 */}
      <Modal
        title="发现并确认安装候选技能"
        open={installModalVisible}
        onCancel={() => setInstallModalVisible(false)}
        footer={null}
        width={700}
      >
        <Tabs
          items={[
            {
              key: 'online',
              label: '候选技能库',
              icon: <CloudDownloadOutlined />,
              children: (
                <Spin spinning={onlineLoading}>
                  <List
                    dataSource={onlineSkills}
                    renderItem={(skill) => (
                      <List.Item
                        actions={[
                          <Button
                            type="primary"
                            size="small"
                            icon={<CloudDownloadOutlined />}
                            onClick={() => handleInstallFromOnline(skill)}
                          >
                            确认安装
                          </Button>
                        ]}
                      >
                        <List.Item.Meta
                          avatar={getCategoryIcon(skill.category)}
                          title={
                            <Space>
                              <Text strong>{skill.display_name}</Text>
                              <Tag color="blue">候选</Tag>
                            </Space>
                          }
                          description={
                            <Space direction="vertical" size={0}>
                              <Text type="secondary">{skill.description}</Text>
                              <Space size="small">
                                <Tag>{categoryNames[skill.category] || skill.category}</Tag>
                                <Tag color="green">{skill.protocol}</Tag>
                                {skill.source && <Text type="secondary">来源: {skill.source}</Text>}
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
              icon: <ApiOutlined />,
              children: (
                <Form form={installForm} layout="vertical" onFinish={async (values) => {
                  const url = (values?.url || '').trim()
                  if (!url) {
                    message.error('请输入合法的技能 URL')
                    return
                  }
                  try {
                    // 通过 URL 真实调用后端安装接口；失败时不显示成功
                    const res = await skillApi.installByUrl(url)
                    message.success(`技能 "${res.data.display_name}" 安装成功`)
                    installForm.resetFields()
                    setInstallModalVisible(false)
                    loadSkills()
                  } catch (err: any) {
                    const detail = err?.response?.data?.detail || '安装失败'
                    message.error(detail)
                  }
                }}>
                  <Form.Item
                    name="url"
                    label="技能 URL"
                    rules={[
                      { required: true, message: '请输入技能 URL' },
                      { type: 'url', message: '请输入合法的 http/https URL' }
                    ]}
                  >
                    <Input placeholder="https://clawhub.ai/skills/xxx" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" block>
                      安装
                    </Button>
                  </Form.Item>
                </Form>
              )
            },
            {
              key: 'search',
              label: '在线搜索',
              icon: <ApiOutlined />,
              children: (
                <Spin spinning={searchLoading}>
                  <Space.Compact style={{ width: '100%', marginBottom: 12 }}>
                    <Input
                      placeholder="输入技能关键词，例如：ecrf 表单、症状自查"
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      onPressEnter={async () => {
                        const q = searchKeyword.trim()
                        if (!q) {
                          message.error('请输入搜索关键词')
                          return
                        }
                        setSearchLoading(true)
                        try {
                          const res = await skillApi.search(q)
                          setSearchLocal(res.data.local || [])
                          setSearchRemote(res.data.remote || [])
                          setSearchRemoteStatus(res.data.remote_status)
                          setSearchRemoteMessage(res.data.remote_message || '')
                        } catch (err: any) {
                          message.error(err?.response?.data?.detail || '搜索失败')
                        } finally {
                          setSearchLoading(false)
                        }
                      }}
                    />
                    <Button
                      type="primary"
                      onClick={async () => {
                        const q = searchKeyword.trim()
                        if (!q) {
                          message.error('请输入搜索关键词')
                          return
                        }
                        setSearchLoading(true)
                        try {
                          const res = await skillApi.search(q)
                          setSearchLocal(res.data.local || [])
                          setSearchRemote(res.data.remote || [])
                          setSearchRemoteStatus(res.data.remote_status)
                          setSearchRemoteMessage(res.data.remote_message || '')
                        } catch (err: any) {
                          message.error(err?.response?.data?.detail || '搜索失败')
                        } finally {
                          setSearchLoading(false)
                        }
                      }}
                    >
                      搜索
                    </Button>
                  </Space.Compact>

                  {searchRemoteStatus && searchRemoteStatus !== 'ok' && (
                    <Alert
                      style={{ marginBottom: 12 }}
                      type={searchRemoteStatus === 'disabled' ? 'info' : 'warning'}
                      showIcon
                      message={searchRemoteStatus === 'disabled' ? '远程技能搜索未启用' : '远程技能仓库暂不可用'}
                      description={searchRemoteMessage || '请联系管理员配置远程技能仓库后重试。'}
                    />
                  )}

                  <Text strong>本地匹配</Text>
                  <List
                    style={{ marginBottom: 12 }}
                    locale={{ emptyText: '没有匹配的本地技能' }}
                    dataSource={searchLocal}
                    renderItem={(item) => (
                      <List.Item>
                        <List.Item.Meta
                          title={
                            <Space>
                              <Text strong>{item.title}</Text>
                              <Tag color="green">本地</Tag>
                              {item.skill_id && <Tag color="geekblue">{item.skill_id}</Tag>}
                            </Space>
                          }
                          description={item.description}
                        />
                      </List.Item>
                    )}
                  />

                  <Text strong>远程候选</Text>
                  <List
                    locale={{ emptyText: '没有远程候选（远程未启用或本次未返回结果）' }}
                    dataSource={searchRemote}
                    renderItem={(item) => (
                      <List.Item
                        actions={[
                          item.url ? (
                            <Button
                              key="install"
                              type="primary"
                              size="small"
                              onClick={async () => {
                                try {
                                  const res = await skillApi.installByUrl(item.url!)
                                  message.success(`已安装：${res.data.display_name}`)
                                  loadSkills()
                                } catch (err: any) {
                                  message.error(err?.response?.data?.detail || '安装失败')
                                }
                              }}
                            >
                              安装
                            </Button>
                          ) : null
                        ]}
                      >
                        <List.Item.Meta
                          title={
                            <Space>
                              <Text strong>{item.title}</Text>
                              <Tag color="purple">clawhub</Tag>
                            </Space>
                          }
                          description={
                            <Space direction="vertical" size={0}>
                              <Text type="secondary">{item.description}</Text>
                              {item.url && <Text type="secondary">{item.url}</Text>}
                            </Space>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </Spin>
              )
            }
          ]}
        />
      </Modal>
      
      {/* 导入本地技能弹窗 */}
      <Modal
        title="导入本地技能"
        open={importModalVisible}
        onCancel={() => {
          setImportModalVisible(false)
          installForm.resetFields()
        }}
        onOk={() => installForm.submit()}
        width={600}
      >
        <Form form={installForm} layout="vertical" onFinish={handleImportLocal}>
          <Form.Item
            name="name"
            label="技能标识"
            rules={[{ required: true, message: '请输入技能标识' }]}
          >
            <Input placeholder="例如: my_custom_skill" />
          </Form.Item>
          
          <Form.Item
            name="display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="例如: 自定义技能" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={2} placeholder="技能功能描述..." />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select placeholder="选择分类">
              <Select.Option value="diagnosis">诊断</Select.Option>
              <Select.Option value="pharmacy">药学</Select.Option>
              <Select.Option value="research">研究</Select.Option>
              <Select.Option value="reference">参考</Select.Option>
              <Select.Option value="imaging">影像</Select.Option>
              <Select.Option value="consultation">咨询</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="protocol"
            label="协议类型"
            rules={[{ required: true, message: '请选择协议类型' }]}
          >
            <Select placeholder="选择协议类型">
              <Select.Option value="builtin">内置工具</Select.Option>
              <Select.Option value="skillhub">SkillHub</Select.Option>
              <Select.Option value="mcp">MCP 协议</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="config"
            label="配置 (JSON 格式)"
          >
            <Input.TextArea rows={3} placeholder='{"endpoint": "https://..."}' />
          </Form.Item>
          
          <Form.Item
            name="input_schema"
            label="输入参数定义 (JSON Schema)"
          >
            <Input.TextArea rows={3} placeholder='{"type": "object", "properties": {...}}' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
