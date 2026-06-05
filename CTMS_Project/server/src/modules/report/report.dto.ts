import { z } from 'zod';

export const createReportTemplateSchema = z.object({
  templateCode: z.string().min(1).max(100),
  templateName: z.string().min(1).max(200),
  reportType: z.enum(['timesheet_detail', 'timesheet_summary', 'timesheet_anomaly', 'financial_pl', 'financial_cashflow', 'financial_cost', 'sae_summary', 'enrollment', 'data_quality', 'audit_compliance', 'other']),
  description: z.string().optional(),
  queryConfig: z.record(z.any()),
  columnConfig: z.array(z.object({ key: z.string(), label: z.string(), width: z.number().optional() })).optional(),
  format: z.enum(['json', 'csv', 'xlsx']).optional().default('json'),
});
export type CreateReportTemplateInput = z.infer<typeof createReportTemplateSchema>;

export const updateReportTemplateSchema = createReportTemplateSchema.partial();
export type UpdateReportTemplateInput = z.infer<typeof updateReportTemplateSchema>;

export const generateReportSchema = z.object({
  templateId: z.string().uuid(),
  projectId: z.string().uuid().optional(),
  reportName: z.string().max(300).optional(),
  parameters: z.record(z.any()).optional(),
  format: z.enum(['json', 'csv', 'xlsx']).optional().default('json'),
});
export type GenerateReportInput = z.infer<typeof generateReportSchema>;
