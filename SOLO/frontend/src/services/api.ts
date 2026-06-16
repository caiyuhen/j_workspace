import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000,  // 增加到300秒，LLM服务响应可能较慢
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// ============== 类型定义 ==============

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name?: string
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  email: string
  name: string | null
  role: string
  created_at: string
}

export interface Conversation {
  id: string
  title: string | null
  status: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ReferenceItem {
  id?: string
  source_type?: string
  title?: string
  content?: string
  url?: string
  score?: number | string
  metadata?: Record<string, unknown>
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_type?: string
  tokens: number
  references?: ReferenceItem[]
  created_at: string
}

export interface Agent {
  name: string
  type: string
  description: string
  capabilities: string[]
  status: 'idle' | 'busy' | 'error'
}

export interface Skill {
  id: string
  name: string
  display_name: string
  description: string
  category: string
  protocol: string
  is_active: boolean
  is_builtin?: boolean
  usage_count: number
}

export interface SkillCandidate {
  id: string
  target_skill_id: string
  name: string
  display_name: string
  description?: string
  category: string
  protocol: string
  source?: string
  install_requires_confirmation: boolean
  input_schema?: Record<string, unknown>
}

export interface SkillDiscoveryResponse {
  installed: boolean
  required_skill_id?: string
  query?: string
  candidates: SkillCandidate[]
  message: string
}

export interface MissingSkillInfo {
  required_skill_id: string
  query?: string
  category?: string
  candidates: SkillCandidate[]
  message?: string
}

export interface SkillResolution {
  ready: boolean
  required_skills: Record<string, unknown>[]
  installed_skills: Skill[]
  missing_skills: MissingSkillInfo[]
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  agent_type?: string
  model?: string
  execution_mode?: 'chat' | 'task'
  deliverable_format?: 'md' | 'docx' | 'xlsx' | 'pptx'
}

export interface LLMModel {
  name: string
  display_name: string
  type: string
  default: boolean
}

export interface FileUploadResponse {
  file_id: string
  filename: string
  content_type?: string
  char_count: number
  text_preview: string
  created_at: string
}

export interface FileAskResponse {
  file_id: string
  filename: string
  question: string
  answer: string
}

export interface Artifact {
  artifact_id: string
  task_id: string
  filename: string
  format: string
  download_url: string
  created_at: string
}

export interface SubTaskProgress {
  id: string
  name: string
  description?: string
  agent_type?: string
  status: string
  input_data?: Record<string, unknown>
  output_data?: Record<string, unknown>
  error_message?: string
  started_at?: string
  completed_at?: string
  created_at?: string
  updated_at?: string
}

export interface TaskProgress {
  task_id: string
  conversation_id?: string
  title?: string
  description?: string
  task_type: string
  status: string
  progress_percent: number
  summary: {
    total: number
    completed: number
    running: number
    failed: number
    pending: number
    skipped: number
  }
  subtasks: SubTaskProgress[]
  artifacts: Artifact[]
  error_message?: string
  duration_seconds?: number
  waiting_for_skill?: boolean
  skill_resolution?: SkillResolution
}

export interface ChatResponse {
  conversation_id: string
  message: Message
  agent_used: string
  task_id?: string
  task_status?: string
  async_execution?: boolean
  waiting_for_skill?: boolean
  skill_resolution?: SkillResolution
  subtasks?: SubTaskProgress[]
  artifacts?: Artifact[]
}

// ============== API 函数 ==============

// 认证相关
export const authApi = {
  login: (data: LoginRequest) => 
    api.post<Token>('/auth/login', data),
  
  register: (data: RegisterRequest) => 
    api.post<User>('/auth/register', data),
  
  getMe: () => 
    api.get<User>('/auth/me'),
  
  logout: () => 
    api.post('/auth/logout'),
  
  refreshToken: () => 
    api.post<Token>('/auth/refresh')
}

// 对话相关
export const artifactApi = {
  download: (artifactId: string) =>
    api.get(`/artifacts/${artifactId}/download`, { responseType: 'blob' })
}

export const conversationApi = {
  list: (page = 1, pageSize = 20) => 
    api.get<{ items: Conversation[], total: number }>('/conversations', {
      params: { page, page_size: pageSize }
    }),
  
  get: (id: string) => 
    api.get<Conversation>(`/conversations/${id}`),
  
  create: (title?: string) => 
    api.post<Conversation>('/conversations', { title }),
  
  delete: (id: string) => 
    api.delete(`/conversations/${id}`),
  
  getMessages: (id: string) => 
    api.get<Message[]>(`/conversations/${id}/messages`),
  
  listLLMModels: () =>
    api.get<LLMModel[]>('/conversations/llm-models'),

  getTaskProgress: (taskId: string) =>
    api.get<TaskProgress>(`/conversations/tasks/${taskId}/progress`),

  resumeTask: (taskId: string) =>
    api.post<TaskProgress>(`/conversations/tasks/${taskId}/resume`),
  
  sendMessage: (data: ChatRequest) => 
    api.post<ChatResponse>('/conversations/chat', data),
  
  sendMessageStream: async (data: ChatRequest, onMessage: (text: string) => void) => {
    const response = await fetch('/api/v1/conversations/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore.getState().token}`
      },
      body: JSON.stringify(data)
    })
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        onMessage(text)
      }
    }
  }
}

// 代理相关
export const agentApi = {
  list: () => 
    api.get<Agent[]>('/agents'),
  
  get: (name: string) => 
    api.get<Agent>(`/agents/${encodeURIComponent(name)}`),
  
  getStatus: () => 
    api.get<Record<string, string>>('/agents/status'),
  
  register: (data: { name: string; type: string; description?: string; config?: Record<string, unknown>; capabilities?: string[] }) =>
    api.post<Agent>('/agents/register', data),
  
  listCustom: () =>
    api.get<{ total: number; agents: Agent[] }>('/agents/custom'),
  
  deleteCustom: (agentId: string) =>
    api.delete(`/agents/custom/${agentId}`)
}

// 附件相关
export const fileApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<FileUploadResponse>('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  ask: (fileId: string, question: string) =>
    api.post<FileAskResponse>(`/files/${encodeURIComponent(fileId)}/ask`, { question }),

  get: (fileId: string) =>
    api.get<FileUploadResponse>(`/files/${encodeURIComponent(fileId)}`)
}

// 技能相关
export const skillApi = {
  list: () => 
    api.get<Skill[]>('/skills'),
  
  get: (id: string) => 
    api.get<Skill>(`/skills/${encodeURIComponent(id)}`),

  discover: (params?: { query?: string; required_skill_id?: string; category?: string }) =>
    api.get<SkillDiscoveryResponse>('/skills/discover', { params }),

  installCandidate: (candidateId: string) =>
    api.post<Skill>('/skills/install-candidate', { candidate_id: candidateId }),
  
  execute: (id: string, input: Record<string, unknown>, config?: Record<string, unknown>) => 
    api.post(`/skills/${id}/execute`, { input, config }),
  
  create: (data: { name: string; display_name: string; description?: string; category?: string; protocol?: string; config?: Record<string, unknown>; input_schema?: Record<string, unknown>; output_schema?: Record<string, unknown> }) =>
    api.post<Skill>('/skills', data),
  
  delete: (id: string) =>
    api.delete(`/skills/${id}`)
}
