import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Input, Button, Card, List, Avatar, Typography, Space, Spin, Empty, Select, message, Tag, Tooltip } from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  PlusOutlined,
  ClearOutlined,
  BulbOutlined,
  AudioOutlined,
  LoadingOutlined
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { conversationApi, Agent } from '../services/api'
import { useChatStore } from '../stores/authStore'
import { agentApi } from '../services/api'

const { TextArea } = Input
const { Text, Title } = Typography

export default function Chat() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const { messages, addMessage, setMessages, clearMessages } = useChatStore()
  
  // 优化提示词状态
  const [optimizing, setOptimizing] = useState(false)
  // 语音识别状态
  const [isListening, setIsListening] = useState(false)
  
  useEffect(() => {
    loadAgents()
    if (conversationId) {
      loadConversation(conversationId)
    }
  }, [conversationId])
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  const loadAgents = async () => {
    try {
      const res = await agentApi.list()
      setAgents(res.data)
    } catch (error) {
      console.error('加载代理失败:', error)
    }
  }
  
  const loadConversation = async (id: string) => {
    try {
      const res = await conversationApi.getMessages(id)
      setMessages(res.data.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        agent_type: m.agent_type
      })))
    } catch (error) {
      // 后端当前使用内存存储，对话在服务重启后会丢失；此时需要回退到新对话
      const status = (error as any)?.response?.status
      if (status === 404) {
        message.warning('该对话已失效（服务重启后会丢失），已为你回到新对话')
        clearMessages()
        navigate('/chat', { replace: true })
        return
      }
      console.error('加载对话失败:', error)
    }
  }
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  // 优化提示词功能
  const handleOptimizePrompt = () => {
    if (!inputValue.trim()) {
      message.warning('请先输入提示词')
      return
    }
    setOptimizing(true)
    setTimeout(() => {
      const optimized = inputValue + '\n\n请提供：\n1. 问题分析\n2. 可能原因\n3. 建议措施\n4. 注意事项'
      setInputValue(optimized)
      setOptimizing(false)
      message.success('提示词已优化')
    }, 500)
  }
  
  // 语音输入功能
  const handleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      message.error('您的浏览器不支持语音识别')
      return
    }
    if (isListening) {
      setIsListening(false)
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.onresult = (e: any) => {
      setInputValue(prev => prev + e.results[0][0].transcript)
      setIsListening(false)
    }
    recognition.onerror = () => {
      setIsListening(false)
      message.error('语音识别失败')
    }
    recognition.start()
    setIsListening(true)
    message.info('开始语音识别...')
  }
  
  const handleSend = async () => {
    if (!inputValue.trim() || loading) return
    
    const userMessage = inputValue.trim()
    setInputValue('')
    
    // 添加用户消息
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: userMessage
    })
    
    setLoading(true)
    
    // 添加助手消息占位
    const assistantMessageId = (Date.now() + 1).toString()
    addMessage({
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      loading: true
    })
    
    let retried = false
    try {
      const doSend = (overrideConversationId?: string) =>
        conversationApi.sendMessage({
          message: userMessage,
          conversation_id: overrideConversationId,
          agent_type: selectedAgent || undefined
        })

      let res = await doSend(conversationId)
      // 如果当前对话在后端不存在（常见于后端重启导致内存丢失），自动重试创建新对话
      if ((res as any)?.response?.status === 404) {
        throw res
      }
      
      // 更新助手消息
      const currentMessages = useChatStore.getState().messages
      const newMessages = [...currentMessages]
      const lastMessage = newMessages[newMessages.length - 1]
      if (lastMessage && lastMessage.id === assistantMessageId) {
        lastMessage.content = res.data.message.content
        lastMessage.agent_type = res.data.agent_used
        lastMessage.loading = false
        setMessages(newMessages)
      }
      
      // 如果是新对话，更新URL
      if (!conversationId && res.data.conversation_id) {
        navigate(`/chat/${res.data.conversation_id}`, { replace: true })
      }
    } catch (error) {
      const status = (error as any)?.response?.status
      if (status === 404 && conversationId && !retried) {
        retried = true
        message.warning('当前对话已失效（服务重启后会丢失），已为你创建新对话并重试')
        try {
          const res = await conversationApi.sendMessage({
            message: userMessage,
            agent_type: selectedAgent || undefined
          })
          // 更新助手消息
          const currentMessages = useChatStore.getState().messages
          const newMessages = [...currentMessages]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.id === assistantMessageId) {
            lastMessage.content = res.data.message.content
            lastMessage.agent_type = res.data.agent_used
            lastMessage.loading = false
            setMessages(newMessages)
          }
          if (res.data.conversation_id) {
            navigate(`/chat/${res.data.conversation_id}`, { replace: true })
          }
          return
        } catch (_e2) {
          // fallthrough
        }
      }

      message.error('发送消息失败')
      // 移除加载中的消息
      const currentMessages = useChatStore.getState().messages
      const newMessages = currentMessages.filter(m => m.id !== assistantMessageId)
      setMessages(newMessages)
    } finally {
      setLoading(false)
    }
  }
  
  const handleNewChat = () => {
    clearMessages()
    navigate('/chat')
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  const getAgentIcon = (agentType?: string) => {
    if (!agentType) return <RobotOutlined />
    return <RobotOutlined />
  }
  
  const getAgentColor = (agentType?: string) => {
    const colors: Record<string, string> = {
      orchestrator: '#722ed1',
      diagnosis: '#1890ff',
      research: '#52c41a',
      consultation: '#fa8c16',
      knowledge: '#13c2c2',
      tool: '#eb2f96',
      quality: '#faad14',
      learning: '#2f54eb'
    }
    return colors[agentType || ''] || '#1890ff'
  }
  
  return (
    <div style={{ height: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 16 
      }}>
        <Title level={4} style={{ margin: 0 }}>
          智能对话
          {conversationId && <Text type="secondary" style={{ fontSize: 14, marginLeft: 8 }}>ID: {conversationId.slice(0, 8)}...</Text>}
        </Title>
        <Space>
          <Select
            placeholder="选择代理"
            allowClear
            style={{ width: 150 }}
            value={selectedAgent || undefined}
            onChange={setSelectedAgent}
            options={agents.map(a => ({ label: a.name, value: a.type }))}
          />
          <Button icon={<ClearOutlined />} onClick={handleNewChat}>
            清空
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleNewChat}>
            新对话
          </Button>
        </Space>
      </div>
      
      <Card 
        style={{ 
          flex: 1, 
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
        styles={{ 
          body: { 
            flex: 1, 
            overflow: 'auto', 
            padding: 16 
          }
        }}
      >
        {messages.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical">
                <Text>开始新的对话</Text>
                <Text type="secondary">
                  您可以询问医学相关问题，系统将智能分配专业代理为您解答
                </Text>
              </Space>
            }
            style={{ marginTop: '20%' }}
          />
        ) : (
          <List
            dataSource={messages}
            renderItem={(item) => (
              <div style={{
                display: 'flex',
                justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: 16
              }}>
                <div style={{
                  maxWidth: '70%',
                  display: 'flex',
                  gap: 8,
                  flexDirection: item.role === 'user' ? 'row-reverse' : 'row'
                }}>
                  <Avatar 
                    style={{ 
                      backgroundColor: item.role === 'user' ? '#1890ff' : getAgentColor(item.agent_type)
                    }}
                    icon={item.role === 'user' ? <UserOutlined /> : getAgentIcon(item.agent_type)}
                  />
                  <div>
                    {item.agent_type && (
                      <Tag color={getAgentColor(item.agent_type)} style={{ marginBottom: 4 }}>
                        {item.agent_type}
                      </Tag>
                    )}
                    <div className={`chat-message ${item.role}`}>
                      {item.loading ? (
                        <Spin size="small" />
                      ) : (
                        <ReactMarkdown className="markdown-content">
                          {item.content}
                        </ReactMarkdown>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          />
        )}
        <div ref={messagesEndRef} />
      </Card>
      
      <div style={{ marginTop: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的问题... (Shift+Enter换行，Enter发送)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ borderRadius: '8px 0 0 0' }}
          />
          <Tooltip title="语音输入">
            <Button 
              icon={isListening ? <LoadingOutlined /> : <AudioOutlined />}
              onClick={handleVoiceInput}
              type={isListening ? 'primary' : 'default'}
              danger={isListening}
              style={{ height: 'auto' }}
            />
          </Tooltip>
          <Tooltip title="优化提示词">
            <Button 
              icon={<BulbOutlined />}
              onClick={handleOptimizePrompt}
              loading={optimizing}
              style={{ height: 'auto' }}
            />
          </Tooltip>
          <Button 
            type="primary" 
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            style={{ height: 'auto', borderRadius: '0 8px 8px 0' }}
          >
            发送
          </Button>
        </Space.Compact>
      </div>
    </div>
  )
}
