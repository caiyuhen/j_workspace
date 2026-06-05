import { z } from 'zod';

// ========== 模板 DTO ==========

export const createTemplateSchema = z.object({
  templateName: z.string().min(1).max(255),
  templateType: z.enum(['crf', 'informed_consent', 'screening', 'visit', 'other']),
  fields: z.record(z.any()),
});

export type CreateTemplateInput = z.infer<typeof createTemplateSchema>;

export const updateTemplateSchema = z.object({
  templateName: z.string().min(1).max(255).optional(),
  templateType: z.enum(['crf', 'informed_consent', 'screening', 'visit', 'other']).optional(),
  fields: z.record(z.any()).optional(),
});

export type UpdateTemplateInput = z.infer<typeof updateTemplateSchema>;