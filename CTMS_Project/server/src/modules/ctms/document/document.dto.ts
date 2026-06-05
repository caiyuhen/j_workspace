import { z } from 'zod';

// ========== TMF 文档管理 DTO ==========

export const createDocumentSchema = z.object({
  projectId: z.string().uuid(),
  tmfSection: z.enum([
    'section_00_general', 'section_01_icf', 'section_02_regulatory',
    'section_03_irb_iec', 'section_04_investigator', 'section_05_pharmacy',
    'section_06_lab', 'section_07_safety', 'section_08_statistics',
    'section_09_financial', 'section_10_site', 'section_11_misc',
  ]),
  documentCode: z.string().min(1, '文档编码不能为空').max(100),
  documentName: z.string().min(1, '文档名称不能为空').max(300),
  documentType: z.enum(['protocol', 'icf', 'regulatory_submission', 'irb_approval', 'cv', 'license', 'report', 'correspondence', 'lab_certificate', 'safety_report', 'training_record', 'financial', 'other']),
  description: z.string().optional(),
  isRequired: z.boolean().optional().default(false),
  expectedDate: z.string().datetime().optional(),
  expiryDate: z.string().datetime().optional(),
  tags: z.array(z.string()).optional().default([]),
  metadata: z.record(z.any()).optional(),
  parentDocumentId: z.string().uuid().optional(),
  zonalType: z.enum(['global', 'country', 'site']).optional(),
  country: z.string().max(50).optional(),
  siteId: z.string().uuid().optional(),
});
export type CreateDocumentInput = z.infer<typeof createDocumentSchema>;

export const updateDocumentSchema = createDocumentSchema.partial().omit({ projectId: true, documentCode: true });
export type UpdateDocumentInput = z.infer<typeof updateDocumentSchema>;

export const uploadDocumentVersionSchema = z.object({
  changeLog: z.string().optional(),
  fileUrl: z.string().min(1, '文件URL不能为空').max(500),
  fileSize: z.number().int().positive().optional(),
  mimeType: z.string().max(100).optional(),
});
export type UploadDocumentVersionInput = z.infer<typeof uploadDocumentVersionSchema>;

export const updateDocumentStatusSchema = z.object({
  status: z.enum(['draft', 'pending_review', 'approved', 'rejected', 'archived', 'superseded']),
  reviewComment: z.string().optional(),
});
export type UpdateDocumentStatusInput = z.infer<typeof updateDocumentStatusSchema>;

export const bulkUpdateStatusSchema = z.object({
  documentIds: z.array(z.string().uuid()).min(1),
  status: z.enum(['draft', 'pending_review', 'approved', 'rejected', 'archived', 'superseded']),
  reviewComment: z.string().optional(),
});
export type BulkUpdateStatusInput = z.infer<typeof bulkUpdateStatusSchema>;
