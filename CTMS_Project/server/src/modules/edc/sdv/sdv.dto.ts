import { z } from 'zod';

// ========== SDV 源数据核查 DTO ==========

export const createSdvRecordSchema = z.object({
  projectId: z.string().uuid(),
  siteId: z.string().uuid(),
  subjectId: z.string().uuid(),
  visitId: z.string().uuid().optional(),
  formId: z.string().uuid().optional(),
  monitoringVisitId: z.string().uuid().optional(),
  sdvDate: z.string().datetime(),
  notes: z.string().optional(),
});
export type CreateSdvRecordInput = z.infer<typeof createSdvRecordSchema>;

export const createSdvItemSchema = z.object({
  crfDataId: z.string().uuid(),
  fieldCode: z.string().min(1).max(100),
  crfValue: z.string().optional(),
  sourceValue: z.string().optional(),
  isVerified: z.boolean().optional().default(false),
  isMatch: z.boolean().optional(),
  discrepancyType: z.enum(['value_mismatch', 'missing_data', 'date_discrepancy', 'calculation_error', 'unit_error', 'other']).optional(),
  comment: z.string().optional(),
});
export type CreateSdvItemInput = z.infer<typeof createSdvItemSchema>;

export const updateSdvItemSchema = createSdvItemSchema.partial().omit({ crfDataId: true, fieldCode: true });
export type UpdateSdvItemInput = z.infer<typeof updateSdvItemSchema>;

export const completeSdvSchema = z.object({
  notes: z.string().optional(),
});
export type CompleteSdvInput = z.infer<typeof completeSdvSchema>;

export const updateSdvRecordSchema = z.object({
  notes: z.string().optional(),
  monitoringVisitId: z.string().uuid().optional(),
});
export type UpdateSdvRecordInput = z.infer<typeof updateSdvRecordSchema>;
