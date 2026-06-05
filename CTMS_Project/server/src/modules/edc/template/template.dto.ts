import { z } from 'zod';

// ========== EDC 模板管理 DTO ==========

export const createTemplateSchema = z.object({
  templateCode: z.string().min(1, '模板编码不能为空').max(50),
  templateName: z.string().min(1, '模板名称不能为空').max(200),
  templateType: z.enum(['crf', 'ae_report', 'lab_result', 'visit_note', 'consent', 'other']),
  version: z.string().min(1, '版本号不能为空').regex(/^\d+\.\d+$/, '版本号格式应为 x.y'),
  templateData: z.record(z.any()).describe('模板 JSON 定义'),
  description: z.string().optional(),
  projectId: z.string().uuid().optional(),
  isSystemTemplate: z.boolean().optional().default(false),
  isShared: z.boolean().optional().default(false),
});
export type CreateTemplateInput = z.infer<typeof createTemplateSchema>;

export const updateTemplateSchema = createTemplateSchema.partial().extend({
  status: z.enum(['draft', 'published', 'deprecated', 'archived']).optional(),
});
export type UpdateTemplateInput = z.infer<typeof updateTemplateSchema>;

export const cloneTemplateSchema = z.object({
  newTemplateCode: z.string().min(1),
  newTemplateName: z.string().min(1),
  newVersion: z.string().optional(),
  projectId: z.string().uuid().optional(),
});
export type CloneTemplateInput = z.infer<typeof cloneTemplateSchema>;
