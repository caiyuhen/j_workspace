import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Input, Button, Card, List, Avatar, Typography, Space, Spin, Empty, Select, message, Tag, Tooltip, Upload, Alert, Collapse, Progress, Steps, Divider, Modal } from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  PlusOutlined,
  ClearOutlined,
  BulbOutlined,
  AudioOutlined,
  LoadingOutlined,
  PaperClipOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  FileDoneOutlined
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { conversationApi, Agent, fileApi, FileUploadResponse, ReferenceItem, LLMModel, Artifact, ChatResponse, artifactApi, TaskProgress, skillApi, SkillCandidate } from '../services/api'
import { useChatStore } from '../stores/authStore'
import { agentApi } from '../services/api'

const { TextArea } = Input
const { Text, Title } = Typography

export default function Chat() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const shouldPollTask = (status?: string) => status === 'pending' || status === 'running'

  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [agents, setAgents] = useState<Agent[]>([])
  const [llmModels, setLlmModels] = useState<LLMModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [executionMode, setExecutionMode] = useState<'chat' | 'task'>('chat')
  const [deliverableFormat, setDeliverableFormat] = useState<'md' | 'docx' | 'xlsx' | 'pptx'>('docx')
  const [messageArtifacts, setMessageArtifacts] = useState<Record<string, Artifact[]>>({})
  const [messageTaskProgress, setMessageTaskProgress] = useState<Record<string, TaskProgress>>({})
  const [pollingTasks, setPollingTasks] = useState<Record<string, string>>({})
  const [taskElapsed, setTaskElapsed] = useState<Record<string, number>>({})
  const [taskStartTime, setTaskStartTime] = useState<Record<string, number>>({})
  const [lastActiveStep, setLastActiveStep] = useState<Record<string, number>>({})

  const [uploadedFile, setUploadedFile] = useState<FileUploadResponse | null>(null)
  const [uploading, setUploading] = useState(false)
  const { messages, addMessage, setMessages, clearMessages } = useChatStore()
  
  // 优化提示词状态
  const [optimizing, setOptimizing] = useState(false)
  // 语音识别状态
  const [isListening, setIsListening] = useState(false)
  
  useEffect(() => {
    loadAgents()
    loadLLMModels()
    if (conversationId) {
      loadConversation(conversationId)
    }
  }, [conversationId])
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const entries = Object.entries(pollingTasks)
    if (!entries.length) return

    const poll = window.setInterval(async () => {
      for (const [messageId, taskId] of entries) {
        try {
          const res = await conversationApi.getTaskProgress(taskId)
          setMessageTaskProgress(prev => ({ ...prev, [messageId]: res.data }))
          if (!shouldPollTask(res.data.status)) {
            setPollingTasks(prev => {
              const next = { ...prev }
              delete next[messageId]
              return next
            })
            setTaskElapsed(prev => {
              const next = { ...prev }
              delete next[messageId]
              return next
            })
            setTaskStartTime(prev => {
              const next = { ...prev }
              delete next[messageId]
              return next
            })
            setLastActiveStep(prev => {
              const next = { ...prev }
              delete next[messageId]
              return next
            })
            return
          }
          const runningIdx = res.data.subtasks?.findIndex(s => s.status === 'running') ?? -1
          const completedCount = res.data.summary?.completed ?? 0
          setLastActiveStep(prev => ({
            ...prev,
            [messageId]: runningIdx >= 0 ? runningIdx : completedCount
          }))
        } catch (error) {
          setPollingTasks(prev => {
            const next = { ...prev }
            delete next[messageId]
            return next
          })
        }
      }
    }, 1500)

    const tick = window.setInterval(() => {
      setTaskElapsed(prev => {
        const next = { ...prev }
        for (const [mid, start] of Object.entries(taskStartTime)) {
          if (pollingTasks[mid]) {
            next[mid] = Date.now() - start
          }
        }
        return next
      })
    }, 1000)

    return () => {
      window.clearInterval(poll)
      window.clearInterval(tick)
    }
  }, [pollingTasks, taskStartTime])

  
  const loadAgents = async () => {
    try {
      const res = await agentApi.list()
      setAgents(res.data)
    } catch (error) {
      console.error('加载代理失败:', error)
    }
  }

  const loadLLMModels = async () => {
    try {
      const res = await conversationApi.listLLMModels()
      setLlmModels(res.data)
      if (!selectedModel && res.data.length > 0) {
        const defaultModel = res.data.find(m => m.default) || res.data[0]
        setSelectedModel(defaultModel.name)
      }
    } catch (error) {
      console.error('加载LLM模型失败:', error)
    }
  }
  
  const loadConversation = async (id: string) => {
    try {
      const res = await conversationApi.getMessages(id)
      setMessages(res.data.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        references: m.references
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
  
  const handleUploadFile = async (file: File) => {
    setUploading(true)
    try {
      const res = await fileApi.upload(file)
      setUploadedFile(res.data)
      message.success(`附件已上传并解析：${res.data.filename}`)
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      message.error(err.response?.data?.detail || '附件上传失败')
    } finally {
      setUploading(false)
    }
    return false
  }

  const rememberTaskResult = (messageId: string, response: ChatResponse) => {
    if (response.artifacts?.length) {
      setMessageArtifacts(prev => ({ ...prev, [messageId]: response.artifacts || [] }))
    }
    if (response.task_id) {
      const subtasks = response.subtasks || []
      const completed = subtasks.filter(item => item.status === 'completed').length
      const running = subtasks.filter(item => item.status === 'running').length
      const failed = subtasks.filter(item => item.status === 'failed').length
      const pending = subtasks.filter(item => item.status === 'pending').length
      const skipped = subtasks.filter(item => item.status === 'skipped').length
      const total = subtasks.length
      setMessageTaskProgress(prev => ({
        ...prev,
        [messageId]: {
          task_id: response.task_id || '',
          conversation_id: response.conversation_id,
          task_type: 'chat_task',
          status: response.task_status || 'completed',
          progress_percent: total ? Math.round((completed / total) * 100) : (response.async_execution ? 0 : 100),
          summary: { total, completed, running, failed, pending, skipped },
          subtasks,
          artifacts: response.artifacts || [],
          waiting_for_skill: response.waiting_for_skill,
          skill_resolution: response.skill_resolution
        }
      }))
    }
  }

  const installSkillAndResume = async (candidate: SkillCandidate, progress: TaskProgress) => {
    Modal.confirm({
      title: '确认安装 Skill',
      content: `将安装「${candidate.display_name || candidate.name}」，安装后继续执行当前任务。`,
      okText: '确认安装并继续',
      cancelText: '取消',
      async onOk() {
        try {
          await skillApi.installCandidate(candidate.id)
          const resumed = await conversationApi.resumeTask(progress.task_id)
          setMessageTaskProgress(prev => {
            const next = { ...prev }
            Object.keys(next).forEach(messageId => {
              if (next[messageId].task_id === progress.task_id) {
                next[messageId] = resumed.data
              }
            })
            return next
          })
          message.success('Skill 已安装，任务已继续执行')
        } catch (error: unknown) {
          const err = error as { response?: { data?: { detail?: string } } }
          message.error(err.response?.data?.detail || '安装 Skill 或继续任务失败')
        }
      }
    })
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
      const doSend = (overrideConversationId?: string): Promise<{ data: ChatResponse }> => {
        if (uploadedFile) {
          return fileApi.ask(uploadedFile.file_id, userMessage).then(res => ({
            data: {
              conversation_id: overrideConversationId || conversationId || '',
              agent_used: 'file-reader',
              message: {
                id: Date.now().toString(),
                role: 'assistant' as const,
                content: res.data.answer,
                tokens: 0,
                references: [],
                created_at: new Date().toISOString()
              }
            }
          }))
        }
        return conversationApi.sendMessage({
          message: userMessage,
          conversation_id: overrideConversationId,
          model: selectedModel || undefined,
          execution_mode: executionMode,
          deliverable_format: deliverableFormat
        })
      }

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
        lastMessage.id = res.data.message.id
        lastMessage.content = res.data.message.content
        lastMessage.references = res.data.message.references
        lastMessage.loading = false
        setMessages(newMessages)
      }
      rememberTaskResult(res.data.message.id, res.data)
      if (res.data.async_execution && res.data.task_id) {
        setPollingTasks(prev => ({ ...prev, [res.data.message.id]: res.data.task_id || '' }))
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
            model: selectedModel || undefined,
            execution_mode: executionMode,
            deliverable_format: deliverableFormat
          })
          // 更新助手消息
          const currentMessages = useChatStore.getState().messages
          const newMessages = [...currentMessages]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage && lastMessage.id === assistantMessageId) {
            lastMessage.id = res.data.message.id
            lastMessage.content = res.data.message.content
            lastMessage.references = res.data.message.references
            lastMessage.loading = false
            setMessages(newMessages)
          }
          rememberTaskResult(res.data.message.id, res.data)
      if (res.data.async_execution && res.data.task_id) {
        setPollingTasks(prev => ({ ...prev, [res.data.message.id]: res.data.task_id || '' }))
        const now = Date.now()
        setTaskStartTime(prev => ({ ...prev, [res.data.message.id]: now }))
        setTaskElapsed(prev => ({ ...prev, [res.data.message.id]: 0 }))
        setLastActiveStep(prev => ({ ...prev, [res.data.message.id]: -1 }))
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
  
  const handleDownloadArtifact = async (artifact: Artifact) => {
    try {
      const res = await artifactApi.download(artifact.artifact_id)
      const contentType = res.headers['content-type']
      const blob = new Blob([res.data], { type: typeof contentType === 'string' ? contentType : 'text/markdown;charset=utf-8' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = artifact.filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载交付物失败')
    }
  }

  const handleNewChat = () => {
    clearMessages()
    setUploadedFile(null)
    setMessageArtifacts({})
    setMessageTaskProgress({})
    setPollingTasks({})
    navigate('/chat')
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  const getReferenceColor = (sourceType?: string) => {
    const colors: Record<string, string> = {
      Milvus: 'purple',
      PubMed: 'blue',
      Ensembl: 'cyan',
      ChEMBL: 'magenta',
      FDA: 'volcano',
      ClinicalTrials: 'green'
    }
    return colors[sourceType || ''] || 'default'
  }

  const formatElapsed = (ms: number) => {
    const totalSec = Math.floor(ms / 1000)
    const min = Math.floor(totalSec / 60)
    const sec = totalSec % 60
    return min > 0 ? `${min}分${sec}秒` : `${sec}秒`
  }

  const getTaskStatusColor = (status?: string) => {

    if (status === 'completed') return 'success'
    if (status === 'failed') return 'exception'
    if (status === 'running') return 'active'
    return 'normal'
  }

  const renderStatusBadge = (status?: string) => {
    if (status === 'running') {
      return (
        <span className="task-status-badge task-status-running">
          <LoadingOutlined spin />
          运行中
        </span>
      )
    }
    if (status === 'completed') {
      return <span className="task-status-badge task-status-completed"><CheckCircleOutlined />已完成</span>
    }
    if (status === 'failed') {
      return <span className="task-status-badge task-status-failed"><CloseCircleOutlined />失败</span>
    }
    if (status === 'waiting_for_skill') {
      return <span className="task-status-badge task-status-waiting"><ClockCircleOutlined />等待 Skill</span>
    }
    return <span className="task-status-badge task-status-pending"><ClockCircleOutlined />{status || '等待中'}</span>
  }

  const getStepStatus = (status?: string): 'wait' | 'process' | 'finish' | 'error' => {
    if (status === 'completed') return 'finish'
    if (status === 'failed') return 'error'
    if (status === 'running') return 'process'
    return 'wait'
  }

  const getSubtaskIcon = (status?: string) => {
    if (status === 'completed') return <CheckCircleOutlined />
    if (status === 'failed') return <CloseCircleOutlined />
    if (status === 'running') return <LoadingOutlined />
    return <ClockCircleOutlined />
  }

  const formatReferenceScore = (score?: number | string) => {
    if (score === undefined || score === null || score === '') return null
    if (typeof score === 'number') return Number.isInteger(score) ? String(score) : score.toFixed(3)
    return String(score)
  }

  const renderReferenceContent = (ref: ReferenceItem) => {
    const metadata = ref.metadata || {}
    const identifiers = [
      metadata.pmid && `PMID: ${metadata.pmid}`,
      metadata.pubmed_id && `PMID: ${metadata.pubmed_id}`,
      metadata.nct_id && `NCT: ${metadata.nct_id}`,
      metadata.nctId && `NCT: ${metadata.nctId}`,
      metadata.chembl_id && `ChEMBL: ${metadata.chembl_id}`,
      metadata.ensembl_id && `Ensembl: ${metadata.ensembl_id}`,
      metadata.gene_id && `Gene: ${metadata.gene_id}`,
      metadata.application_number && `FDA Application: ${metadata.application_number}`
    ].filter(Boolean)

    return (
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        <Space wrap size={4}>
          <Tag color={getReferenceColor(ref.source_type)}>{ref.source_type || 'Unknown'}</Tag>
          {formatReferenceScore(ref.score) && <Tag>score: {formatReferenceScore(ref.score)}</Tag>}
          {identifiers.map((id) => <Tag key={String(id)}>{String(id)}</Tag>)}
        </Space>
        {ref.title && <Text strong>{ref.title}</Text>}
        {ref.content && (
          <Text type="secondary" style={{ whiteSpace: 'pre-wrap' }}>
            {ref.content.length > 600 ? `${ref.content.slice(0, 600)}...` : ref.content}
          </Text>
        )}
        {ref.url && (
          <a href={ref.url} target="_blank" rel="noreferrer">
            查看原始来源
          </a>
        )}
      </Space>
    )
  }

  const renderTaskProgress = (progress?: TaskProgress) => {
    if (!progress) return null
    const missingSkills = progress.skill_resolution?.missing_skills || []
    return (
      <Card
        size="small"
        style={{ marginTop: 10, borderRadius: 12, border: '1px solid #e6f4ff', background: 'linear-gradient(135deg, #fbfdff 0%, #f6fbff 100%)' }}
        bodyStyle={{ padding: 12 }}
      >
        <Space direction="vertical" size={10} style={{ width: '100%' }}>
          <Space style={{ width: '100%', justifyContent: 'space-between' }} align="center">
            <Space size={8}>
              <FileDoneOutlined style={{ color: '#1677ff' }} />
              <Text strong>任务执行进度</Text>
              {renderStatusBadge(progress.status)}
              {shouldPollTask(progress.status) && <span className="task-polling-pill">实时刷新中</span>}
            </Space>
            <Text type="secondary">{progress.summary.completed}/{progress.summary.total} 已完成</Text>
          </Space>
          <Progress percent={progress.progress_percent} size="small" status={getTaskStatusColor(progress.status)} />
          <Space wrap size={6}>
            <Tag color="green">完成 {progress.summary.completed}</Tag>
            <Tag color="blue">运行 {progress.summary.running}</Tag>
            <Tag>等待 {progress.summary.pending}</Tag>
            {progress.summary.failed > 0 && <Tag color="red">失败 {progress.summary.failed}</Tag>}
          </Space>
          {progress.error_message && <Alert type="error" showIcon message={progress.error_message} />}
          {progress.waiting_for_skill && missingSkills.length > 0 && (
            <Alert
              type="warning"
              showIcon
              message="任务需要安装或启用 Skill 后继续执行"
              description={(
                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                  {missingSkills.map(missing => (
                    <Card key={missing.required_skill_id} size="small" bodyStyle={{ padding: 8 }}>
                      <Space direction="vertical" size={6} style={{ width: '100%' }}>
                        <Text strong>{missing.query || missing.required_skill_id}</Text>
                        {missing.message && <Text type="secondary">{missing.message}</Text>}
                        <Space wrap>
                          {missing.candidates.map(candidate => (
                            <Button key={candidate.id} size="small" type="primary" onClick={() => installSkillAndResume(candidate, progress)}>
                              安装并继续：{candidate.display_name || candidate.name}
                            </Button>
                          ))}
                        </Space>
                      </Space>
                    </Card>
                  ))}
                </Space>
              )}
            />
          )}
          {shouldPollTask(progress.status) && (
            <Alert
              type="info"
              showIcon
              message={(
                <Space size={8}>
                  <span>任务正在后台执行</span>
                  <span className="task-elapsed-badge">已耗时 {formatElapsed(taskElapsed[Object.keys(pollingTasks).find(k => pollingTasks[k] === progress.task_id) || ''] || 0)}</span>
                </Space>
              )}
              description={(
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  <Text type="secondary">
                    {progress.subtasks?.length
                      ? `正在执行第 ${(lastActiveStep[Object.keys(pollingTasks).find(k => pollingTasks[k] === progress.task_id) || ''] || 0) + 1} / ${progress.subtasks.length} 步`
                      : '后台任务已启动，正在准备子任务'}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    每 1.5 秒自动刷新进度
                  </Text>
                </Space>
              )}
            />
          )}
          <Steps

            direction="vertical"
            size="small"
            current={Math.max(progress.summary.completed - 1, 0)}
            items={progress.subtasks.map((subtask, index) => ({
              title: `${index + 1}. ${subtask.name}`,
              description: (
                <Space direction="vertical" size={2}>
                  {subtask.description && <Text type="secondary">{subtask.description}</Text>}
                  <Space size={4} wrap>
                    {(subtask.input_data as any)?.step_type === 'tool' && (
                      <Tag color="purple">Skill</Tag>
                    )}
                    {(() => {
                      const fb = (subtask.output_data as any)?.fallback
                      if (fb === 'llm_after_skill_error') return <Tag color="cyan">已重试为 LLM</Tag>
                      if (fb === 'llm_fallback_empty' || fb === 'llm_fallback_also_failed') return <Tag color="red">兜底也失败</Tag>
                      return null
                    })()}
                    {(() => {
                      const rstatus = (subtask.input_data as any)?.resolver_status || (subtask.output_data as any)?.resolver_status
                      if (rstatus === 'auto_installed') return <Tag color="gold">已自动安装</Tag>
                      if (rstatus === 'local') return <Tag color="green">本地匹配</Tag>
                      if (rstatus === 'not_available') return <Tag color="orange">已降级</Tag>
                      return null
                    })()}
                    {(() => {
                      const skillId = (subtask.output_data as any)?.skill_id || (subtask.input_data as any)?.skill_id
                      return skillId ? <Tag color="geekblue">{skillId}</Tag> : null
                    })()}
                    {renderStatusBadge(subtask.status)}
                    {typeof (subtask.output_data as any)?.duration_seconds === 'number' && (
                      <Tag color="default">{((subtask.output_data as any).duration_seconds as number).toFixed(2)}s</Tag>
                    )}
                  </Space>
                  {(subtask.input_data as any)?.step_type === 'tool' && (subtask.input_data as any)?.input && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      输入：{JSON.stringify((subtask.input_data as any).input).slice(0, 120)}
                    </Text>
                  )}
                  {(subtask.output_data as any)?.result !== undefined && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      输出：{(() => {
                        const r = (subtask.output_data as any).result
                        const s = typeof r === 'string' ? r : JSON.stringify(r)
                        return s.length > 160 ? `${s.slice(0, 160)}…` : s
                      })()}
                    </Text>
                  )}
                  {subtask.error_message && <Text type="danger">{subtask.error_message}</Text>}
                </Space>
              ),
              status: getStepStatus(subtask.status),
              icon: getSubtaskIcon(subtask.status)
            }))}
          />
          {progress.artifacts?.length > 0 && (
            <>
              <Divider style={{ margin: '4px 0' }} />
              <Space direction="vertical" size={4}>
                <Text strong>交付物</Text>
                {progress.artifacts.map(artifact => (
                  <Button key={artifact.artifact_id} size="small" icon={<FileDoneOutlined />} onClick={() => handleDownloadArtifact(artifact)}>
                    {artifact.filename}
                  </Button>
                ))}
              </Space>
            </>
          )}
        </Space>
      </Card>
    )
  }

  const renderReferences = (references?: ReferenceItem[]) => {
    if (!references || references.length === 0) return null
    return (
      <Collapse
        size="small"
        style={{ marginTop: 8, background: '#fafafa' }}
        items={[
          {
            key: 'references',
            label: `引用内容（${references.length}）`,
            children: (
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                {references.map((ref, index) => (
                  <Card key={`${ref.source_type || 'ref'}-${ref.id || index}`} size="small" bodyStyle={{ padding: 8 }}>
                    {renderReferenceContent(ref)}
                  </Card>
                ))}
              </Space>
            )
          }
        ]}
      />
    )
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
            value={executionMode}
            onChange={setExecutionMode}
            style={{ width: 150 }}
            options={[
              { label: '普通对话', value: 'chat' },
              { label: '任务执行', value: 'task' }
            ]}
          />
          {executionMode === 'task' && (
            <Select
              value={deliverableFormat}
              onChange={setDeliverableFormat}
              style={{ width: 150 }}
              options={[
                { label: 'Word', value: 'docx' },
                { label: 'Excel', value: 'xlsx' },
                { label: 'PPT', value: 'pptx' },
                { label: 'Markdown', value: 'md' }
              ]}
            />
          )}
          <Select
            placeholder="选择LLM模型"
            style={{ width: 180 }}
            value={selectedModel || undefined}
            onChange={setSelectedModel}
            options={llmModels.map(m => ({ label: m.display_name || m.name, value: m.name }))}
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
        bodyStyle={{ 
          flex: 1, 
          overflow: 'auto', 
          padding: 16 
        }}
      >
        {messages.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical">
                <Text>开始新的对话</Text>
                <Text type="secondary">
                  您可以选择普通对话，或选择任务执行来自动生成可下载交付物
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
                      backgroundColor: item.role === 'user' ? '#1890ff' : '#1890ff'
                    }}
                    icon={item.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                  />
                  <div>
                    <div className={`chat-message ${item.role}`}>
                      {item.loading ? (
                        <Spin size="small" />
                      ) : (
                        <ReactMarkdown className="markdown-content" remarkPlugins={[remarkGfm]}>
                          {item.content}
                        </ReactMarkdown>
                      )}
                    </div>
                    {item.role === 'assistant' && !item.loading && renderTaskProgress(messageTaskProgress[item.id])}
                    {item.role === 'assistant' && !item.loading && !messageTaskProgress[item.id] && messageArtifacts[item.id]?.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <Space direction="vertical" size={4}>
                          {messageArtifacts[item.id].map(artifact => (
                            <Button
                              key={artifact.artifact_id}
                              size="small"
                              type="link"
                              onClick={() => handleDownloadArtifact(artifact)}
                            >
                              下载交付物：{artifact.filename}
                            </Button>
                          ))}
                        </Space>
                      </div>
                    )}
                    {item.role === 'assistant' && !item.loading && renderReferences(item.references)}
                  </div>
                </div>
              </div>
            )}
          />
        )}
        <div ref={messagesEndRef} />
      </Card>
      
      <div style={{ marginTop: 16 }}>
        {uploadedFile && (
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 8 }}
            message={
              <Space>
                <Text>已上传附件：{uploadedFile.filename}（{uploadedFile.char_count} 字）</Text>
                <Button size="small" icon={<DeleteOutlined />} onClick={() => setUploadedFile(null)}>
                  移除
                </Button>
              </Space>
            }
            description="发送问题时，系统会优先基于该附件内容回答；LLM 服务仍使用现有内置 RAG 能力，不在本系统重复建设 RAG。"
          />
        )}
        <Space.Compact style={{ width: '100%' }}>
          <Upload
            accept=".txt,.md,.pdf,.docx"
            showUploadList={false}
            beforeUpload={handleUploadFile}
            disabled={uploading || loading}
          >
            <Tooltip title="上传附件">
              <Button icon={<PaperClipOutlined />} loading={uploading} style={{ height: 'auto', borderRadius: '8px 0 0 8px' }} />
            </Tooltip>
          </Upload>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的问题... (Shift+Enter换行，Enter发送)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ borderRadius: 0 }}
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
