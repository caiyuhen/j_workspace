import { z } from 'zod';

// ========== 工作流定义 DTO ==========

export const stageSchema = z.object({
  id: z.string(),
  name: z.string(),
  approverRole: z.string(),
  nodeType: z.enum(['submit', 'review', 'approve', 'authorize', 'inform', 'complete']).optional().default('review'),
  esigRequired: z.boolean().optional().default(false),
  esigDualSign: z.boolean().optional().default(false),
  timeoutDays: z.number().optional(),
  timeoutHours: z.number().optional(),
  // 会签配置
  isCountersign: z.boolean().optional().default(false),
  countersignApprovers: z.array(z.string().uuid()).optional().default([]),
  countersignPassMode: z.enum(['all', 'majority', 'one']).optional().default('all'),
  // 退回配置
  allowReturn: z.boolean().optional().default(true),
  returnToStageIds: z.array(z.string()).optional().default([]),
});

export const createDefinitionSchema = z.object({
  workflowCode: z.string().min(1, '流程编码不能为空').max(50),
  workflowName: z.string().min(1, '流程名称不能为空').max(100),
  workflowType: z.enum(['project_approval', 'site_activation', 'budget_review', 'protocol_amendment', 'safety_report', 'data_lock', 'contract_approval', 'other']),
  stages: z.array(stageSchema).min(1, '至少需要一个审批阶段'),
  description: z.string().optional(),
  allowDelegate: z.boolean().optional().default(true),
  notificationEnabled: z.boolean().optional().default(true),
});
export type CreateDefinitionInput = z.infer<typeof createDefinitionSchema>;

export const updateDefinitionSchema = createDefinitionSchema.partial();
export type UpdateDefinitionInput = z.infer<typeof updateDefinitionSchema>;

// ========== 工作流实例 DTO ==========

export const startInstanceSchema = z.object({
  definitionId: z.string().uuid(),
  workflowType: z.string().optional(),
  projectId: z.string().uuid().optional(),
  businessData: z.record(z.any()).optional(),
  initiatorComment: z.string().optional(),
});
export type StartInstanceInput = z.infer<typeof startInstanceSchema>;

// ========== 任务处理 DTO ==========

export const processTaskSchema = z.object({
  action: z.enum(['approve', 'reject', 'delegate', 'return', 'countersign']),
  comment: z.string().optional(),
  delegateTo: z.string().uuid().optional(),
  // 退回到指定阶段
  returnToStageId: z.string().optional(),
  // 电子签名数据
  esigData: z.object({
    signatureMeaning: z.string(),
    signatureReason: z.string(),
  }).optional(),
  // 双签名（核准节点需要两个签名）
  esigDataSecondary: z.object({
    signatureMeaning: z.string(),
    signatureReason: z.string(),
  }).optional(),
});
export type ProcessTaskInput = z.infer<typeof processTaskSchema>;

// ========== 超时查询 DTO ==========

export const getTimeoutTasksSchema = z.object({
  overdueOnly: z.boolean().optional().default(true),
});
