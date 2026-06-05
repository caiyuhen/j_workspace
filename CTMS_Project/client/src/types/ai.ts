// ==================== AI 智能助手 ====================

export interface AiAgent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'inactive';
  category: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agentId?: string;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  agentId: string;
  message: string;
  context?: Record<string, any>;
  conversationId?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  conversationId: string;
}

export interface AnalyzeRequest {
  agentId: string;
  data: Record<string, any>;
  analysisType: 'risk' | 'trend' | 'anomaly' | 'summary' | 'prediction';
}

export interface AnalyzeResponse {
  result: Record<string, any>;
  recommendations?: string[];
  confidence?: number;
}

export interface BatchProcessRequest {
  agentId: string;
  taskType: string;
  items: Record<string, any>[];
}

export interface AiLogEntry {
  id: string;
  agentId: string;
  agentName: string;
  userId: string;
  action: string;
  inputSummary?: string;
  outputSummary?: string;
  status: 'success' | 'error';
  duration: number;
  createdAt: string;
}
