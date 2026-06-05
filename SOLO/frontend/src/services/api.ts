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

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_type?: string
  tokens: number
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
  usage_count: number
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  agent_type?: string
}

export interface ChatResponse {
  conversation_id: string
  message: Message
  agent_used: string
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
    api.get<Agent>(`/agents/${name}`),
  
  getStatus: () => 
    api.get<Record<string, string>>('/agents/status'),
  
  register: (data: { name: string; type: string; description?: string; config?: Record<string, unknown>; capabilities?: string[] }) =>
    api.post<Agent>('/agents/register', data),
  
  listCustom: () =>
    api.get<{ total: number; agents: Agent[] }>('/agents/custom'),
  
  deleteCustom: (agentId: string) =>
    api.delete(`/agents/custom/${agentId}`)
}

// 技能相关
export const skillApi = {
  list: () => 
    api.get<Skill[]>('/skills'),
  
  get: (id: string) => 
    api.get<Skill>(`/skills/${id}`),
  
  execute: (id: string, params: Record<string, unknown>) => 
    api.post(`/skills/${id}/execute`, params),
  
  create: (data: { name: string; display_name: string; description?: string; category?: string; protocol?: string; config?: Record<string, unknown>; input_schema?: Record<string, unknown>; output_schema?: Record<string, unknown> }) =>
    api.post<Skill>('/skills', data),
  
  delete: (id: string) =>
    api.delete(`/skills/${id}`)
}
