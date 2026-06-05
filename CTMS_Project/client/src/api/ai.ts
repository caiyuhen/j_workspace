import api from './index';
import type { ApiResponse } from '@/types';
import type {
  AiAgent,
  ChatRequest,
  ChatResponse,
  AnalyzeRequest,
  AnalyzeResponse,
  BatchProcessRequest,
  AiLogEntry,
} from '@/types';

export const aiApi = {
  // Agent 能力查询
  getAgentList: () =>
    api.get<ApiResponse<AiAgent[]>>('/ai/agents').then((r) => r.data.data),

  // AI 对话
  chat: (data: ChatRequest) =>
    api.post<ApiResponse<ChatResponse>>('/ai/chat', data).then((r) => r.data.data),

  // 数据分析
  analyze: (data: AnalyzeRequest) =>
    api.post<ApiResponse<AnalyzeResponse>>('/ai/analyze', data).then((r) => r.data.data),

  // 批量处理
  batchProcess: (data: BatchProcessRequest) =>
    api.post<ApiResponse<{ results: any[] }>>('/ai/batch', data).then((r) => r.data.data),

  // Agent 日志
  getLogs: (params?: Record<string, any>) =>
    api.get<ApiResponse<AiLogEntry[]>>('/ai/logs', { params }).then((r) => r.data.data),
};
