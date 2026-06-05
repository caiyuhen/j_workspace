import { z } from 'zod';

// ========== 审计日志查询 DTO ==========

export const queryAuditLogSchema = z.object({
  page: z.string().optional(),
  pageSize: z.string().optional(),
  userId: z.string().uuid().optional(),
  eventType: z.string().optional(),
  tableName: z.string().optional(),
  recordId: z.string().optional(),
  action: z.string().optional(),
  startTime: z.string().datetime({ offset: true }).optional().or(z.string().date().optional()),
  endTime: z.string().datetime({ offset: true }).optional().or(z.string().date().optional()),
  keyword: z.string().optional(),
  sortField: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
});
export type QueryAuditLogInput = z.infer<typeof queryAuditLogSchema>;
