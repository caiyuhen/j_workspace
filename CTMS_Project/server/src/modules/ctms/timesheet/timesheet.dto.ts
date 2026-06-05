import { z } from 'zod';

// ========== 工时管理 DTO ==========

export const createTimesheetSchema = z.object({
  userId: z.string().uuid(),
  projectId: z.string().uuid().optional(),
  weekStartDate: z.string().datetime({ offset: true }).or(z.string().date()),
  entries: z.array(z.object({
    workDate: z.string().datetime({ offset: true }).or(z.string().date()),
    hours: z.number().min(0).max(24),
    workType: z.enum(['monitoring', 'site_management', 'project_management', 'data_review', 'training', 'meeting', 'travel', 'other']),
    projectId: z.string().uuid().optional(),
    siteId: z.string().uuid().optional(),
    description: z.string().optional(),
    isBillable: z.boolean().optional().default(true),
  })).min(1, '至少包含一条工时记录'),
});
export type CreateTimesheetInput = z.infer<typeof createTimesheetSchema>;

export const submitTimesheetSchema = z.object({
  comment: z.string().optional(),
});
export type SubmitTimesheetInput = z.infer<typeof submitTimesheetSchema>;

export const approveTimesheetSchema = z.object({
  action: z.enum(['approve', 'reject']),
  comment: z.string().optional(),
});
export type ApproveTimesheetInput = z.infer<typeof approveTimesheetSchema>;
