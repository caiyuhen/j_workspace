import { z } from 'zod';

export const createMaskingRuleSchema = z.object({
  ruleName: z.string().min(1).max(200),
  tableName: z.string().min(1).max(100),
  fieldName: z.string().min(1).max(100),
  maskType: z.enum(['full', 'partial', 'hash', 'replace', 'email', 'phone', 'id_card']),
  maskPattern: z.string().max(200).optional(),
  allowedRoles: z.array(z.string()).optional(),
  description: z.string().optional(),
});
export type CreateMaskingRuleInput = z.infer<typeof createMaskingRuleSchema>;

export const updateMaskingRuleSchema = createMaskingRuleSchema.partial();
export type UpdateMaskingRuleInput = z.infer<typeof updateMaskingRuleSchema>;

export const previewMaskSchema = z.object({
  tableName: z.string(),
  fieldName: z.string(),
  value: z.string(),
});
export type PreviewMaskInput = z.infer<typeof previewMaskSchema>;
