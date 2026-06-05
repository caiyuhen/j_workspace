import { z } from 'zod';

// ========== AI Agent DTO ==========

export const AGENT_TYPES = [
  'doc_review',      // 文档审查
  'ae_coding',       // AE 编码
  'cons_audit',      // 知情同意审核
  'sdv_assist',      // SDV 辅助
  'sae_alert',       // SAE 预警
  'prot_check',      // 方案依从性检查
  'lab_norm',        // 实验室异常值
  'data_clean',      // 数据清洗
  'qm_report',       // 质量管理报告
  'work_hour',       // 工时分析
  'chatbot',         // 智能助手
  'translate',       // 翻译
] as const;

export type AgentType = typeof AGENT_TYPES[number];

export const chatSchema = z.object({
  agentType: z.enum(AGENT_TYPES),
  message: z.string().min(1, '消息不能为空').max(10000),
  projectId: z.string().uuid().optional(),
  contextData: z.record(z.any()).optional(),
});
export type ChatInput = z.infer<typeof chatSchema>;

export const batchProcessSchema = z.object({
  agentType: z.enum(AGENT_TYPES),
  projectId: z.string().uuid(),
  items: z.array(z.record(z.any())).min(1).max(50),
  options: z.record(z.any()).optional(),
});
export type BatchProcessInput = z.infer<typeof batchProcessSchema>;

export const analyzeSchema = z.object({
  agentType: z.enum(AGENT_TYPES),
  projectId: z.string().uuid(),
  analysisType: z.string().min(1).max(100),
  parameters: z.record(z.any()).optional(),
});
export type AnalyzeInput = z.infer<typeof analyzeSchema>;
