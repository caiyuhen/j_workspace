import { useEffect, useState } from 'react'
import { Card, List, Typography, Tag, Empty, Pagination, Popconfirm, message, Space, Button } from 'antd'
import {
  MessageOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { conversationApi, Conversation } from '../services/api'

const { Title, Text } = Typography

export default function History() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const navigate = useNavigate()
  
  useEffect(() => {
    loadConversations()
  }, [page])
  
  const loadConversations = async () => {
    setLoading(true)
    try {
      const res = await conversationApi.list(page, 10)
      setConversations(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch (error) {
      console.error('加载对话历史失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleDelete = async (id: string) => {
    try {
      await conversationApi.delete(id)
      message.success('删除成功')
      loadConversations()
    } catch (error) {
      message.error('删除失败')
    }
  }
  
  const handleView = (id: string) => {
    navigate(`/chat/${id}`)
  }
  
  const getStatusTag = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      archived: 'orange',
      deleted: 'red'
    }
    return <Tag color={colors[status] || 'default'}>{status}</Tag>
  }
  
  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>历史记录</Title>
      
      <Card loading={loading}>
        {conversations.length === 0 ? (
          <Empty description="暂无对话记录" />
        ) : (
          <>
            <List
              dataSource={conversations}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      type="text"
                      icon={<EyeOutlined />}
                      onClick={() => handleView(item.id)}
                    >
                      查看
                    </Button>,
                    <Popconfirm
                      title="确定要删除这个对话吗？"
                      onConfirm={() => handleDelete(item.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button type="text" danger icon={<DeleteOutlined />}>
                        删除
                      </Button>
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <div style={{
                        width: 48,
                        height: 48,
                        borderRadius: 12,
                        background: '#1890ff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <MessageOutlined style={{ fontSize: 24, color: 'white' }} />
                      </div>
                    }
                    title={
                      <Space>
                        <Text strong>{item.title || '新对话'}</Text>
                        {getStatusTag(item.status)}
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">
                          <ClockCircleOutlined style={{ marginRight: 4 }} />
                          创建: {new Date(item.created_at).toLocaleString('zh-CN')}
                        </Text>
                        <Text type="secondary">
                          <ClockCircleOutlined style={{ marginRight: 4 }} />
                          更新: {new Date(item.updated_at).toLocaleString('zh-CN')}
                        </Text>
                      </Space>
                    }
                  />
                  <div style={{ textAlign: 'right' }}>
                    <Text type="secondary">消息数: {item.message_count}</Text>
                  </div>
                </List.Item>
              )}
            />
            
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <Pagination
                current={page}
                total={total}
                pageSize={10}
                onChange={setPage}
                showSizeChanger={false}
                showTotal={(total) => `共 ${total} 条记录`}
              />
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
