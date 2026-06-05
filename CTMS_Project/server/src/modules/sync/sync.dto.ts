import { z } from 'zod';

export const createSyncLogSchema = z.object({
  syncType: z.enum(['project_info', 'subject_data', 'subject_enrollment', 'visit_data', 'ae_sae', 'adverse_events', 'timesheet', 'finance']),
  direction: z.enum(['ctms_to_edc', 'edc_to_ctms', 'bidirectional']),
  projectId: z.string().uuid().optional(),
  sourceSystem: z.enum(['CTMS', 'EDC']),
  targetSystem: z.enum(['CTMS', 'EDC']),
  recordId: z.string().uuid().optional(),
  recordType: z.string().max(50).optional(),
  payload: z.record(z.any()).optional(),
});
export type CreateSyncLogInput = z.infer<typeof createSyncLogSchema>;

export const triggerSyncSchema = z.object({
  syncType: z.enum(['project_info', 'subject_data', 'subject_enrollment', 'visit_data', 'ae_sae', 'adverse_events', 'timesheet', 'finance']),
  projectId: z.string().uuid().optional(),
  direction: z.enum(['ctms_to_edc', 'edc_to_ctms', 'bidirectional']).optional(),
  parameters: z.record(z.any()).optional(),
});
export type TriggerSyncInput = z.infer<typeof triggerSyncSchema>;
