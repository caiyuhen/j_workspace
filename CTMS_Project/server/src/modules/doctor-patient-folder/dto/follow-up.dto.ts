import { z } from 'zod';

// ========== 随访数据 DTO ==========

export const createFollowUpSchema = z.object({
  patientRecordId: z.string().uuid(),
  visitDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  visitType: z.string().min(1).max(100),
  formTemplateId: z.string().uuid().optional(),
  formTemplateName: z.string().max(255).optional(),
  data: z.record(z.any()),
});

export type CreateFollowUpInput = z.infer<typeof createFollowUpSchema>;

export const updateFollowUpSchema = z.object({
  visitDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  visitType: z.string().min(1).max(100).optional(),
  formTemplateId: z.string().uuid().optional(),
  formTemplateName: z.string().max(255).optional(),
  data: z.record(z.any()).optional(),
});

export type UpdateFollowUpInput = z.infer<typeof updateFollowUpSchema>;