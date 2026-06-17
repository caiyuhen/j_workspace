import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User, Token, ReferenceItem } from '../services/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  
  // Actions
  setAuth: (user: User, token: Token) => void
  setToken: (token: Token) => void
  setUser: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      setAuth: (user, token) => set({
        user,
        token: token.access_token,
        isAuthenticated: true
      }),
      
      setToken: (token) => set({
        token: token.access_token
      }),
      
      setUser: (user) => set({ user }),
      
      logout: () => set({
        user: null,
        token: null,
        isAuthenticated: false
      })
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

// 对话状态
interface ConversationState {
  currentConversationId: string | null
  conversations: Array<{
    id: string
    title: string | null
    updated_at: string
  }>
  
  setCurrentConversation: (id: string | null) => void
  setConversations: (conversations: ConversationState['conversations']) => void
  addConversation: (conversation: { id: string; title: string | null; updated_at: string }) => void
}

export const useConversationStore = create<ConversationState>((set) => ({
  currentConversationId: null,
  conversations: [],
  
  setCurrentConversation: (id) => set({ currentConversationId: id }),
  
  setConversations: (conversations) => set({ conversations }),
  
  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations]
  }))
}))

// 聊天状态
interface ChatState {
  messages: Array<{
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    references?: ReferenceItem[]
    loading?: boolean
  }>
  isLoading: boolean
  
  addMessage: (message: ChatState['messages'][0]) => void
  updateLastMessage: (content: string) => void
  setMessages: (messages: ChatState['messages']) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  updateLastMessage: (content) => set((state) => {
    const messages = [...state.messages]
    if (messages.length > 0) {
      messages[messages.length - 1] = {
        ...messages[messages.length - 1],
        content,
        loading: false
      }
    }
    return { messages }
  }),
  
  setMessages: (messages) => set({ messages }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  clearMessages: () => set({ messages: [] })
}))
