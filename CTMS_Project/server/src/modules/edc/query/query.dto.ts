import { z } from 'zod';

// ========== 数据质疑 DTO ==========

export const createQuerySchema = z.object({
  projectId: z.string().uuid(),
  subjectId: z.string().uuid().optional(),
  formId: z.string().uuid().optional(),
  fieldId: z.string().uuid().optional(),
  queryType: z.enum(['data_discrepancy', 'missing_data', 'protocol_deviation', 'query clarification', 'other']),
  priority: z.enum(['low', 'medium', 'high', 'critical']).optional().default('medium'),
  title: z.string().min(1, '质疑标题不能为空').max(200),
  description: z.string().min(1, '质疑描述不能为空'),
  assignedTo: z.string().uuid().optional(),
});
export type CreateQueryInput = z.infer<typeof createQuerySchema>;

export const replyQuerySchema = z.object({
  content: z.string().min(1, '回复内容不能为空'),
  action: z.enum(['reply', 'close', 'escalate']).optional().default('reply'),
});
export type ReplyQueryInput = z.infer<typeof replyQuerySchema>;
