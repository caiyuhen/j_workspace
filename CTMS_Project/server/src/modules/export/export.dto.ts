import { z } from 'zod';

export const exportDataSchema = z.object({
  exportType: z.enum(['subjects', 'crf_data', 'adverse_events', 'queries', 'sdv', 'randomization']),
  projectId: z.string().uuid(),
  siteId: z.string().uuid().optional(),
  format: z.enum(['json', 'csv']).optional().default('json'),
  filters: z.record(z.any()).optional(),
});
export type ExportDataInput = z.infer<typeof exportDataSchema>;
