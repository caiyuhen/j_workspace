import { z } from 'zod';

// ========== AE/SAE 安全性管理 DTO ==========

export const createAdverseEventSchema = z.object({
  projectId: z.string().uuid(),
  subjectId: z.string().uuid(),
  eventType: z.enum(['ae', 'sae']),
  termPreferred: z.string().min(1, '不良事件术语不能为空').max(500),
  termCode: z.string().max(50).optional(),
  meddraCode: z.string().max(50).optional(),
  onsetDate: z.string().datetime(),
  endDate: z.string().datetime().optional(),
  isOngoing: z.boolean().optional().default(true),
  severity: z.enum(['mild', 'moderate', 'severe']),
  seriousness: z.enum(['non_serious', 'serious']),
  seriousnessCriteria: z.array(z.string()).optional().default([]),
  causality: z.enum(['not_related', 'unlikely', 'possible', 'probable', 'definite']).optional(),
  causalityMethod: z.enum(['who_umc', 'naranjo', 'investigator_judgment']).optional(),
  relationship: z.enum(['unrelated', 'unlikely_related', 'possibly_related', 'probably_related', 'definitely_related']).optional(),
  description: z.string().min(1, '事件描述不能为空'),
  actionTaken: z.array(z.string()).optional().default([]),
  outcome: z.enum(['resolved', 'resolving', 'not_resolved', 'fatal', 'unknown']).optional(),
  siteId: z.string().uuid().optional(),
});
export type CreateAdverseEventInput = z.infer<typeof createAdverseEventSchema>;

export const updateAdverseEventSchema = createAdverseEventSchema.partial().omit({ projectId: true, subjectId: true, eventType: true });
export type UpdateAdverseEventInput = z.infer<typeof updateAdverseEventSchema>;

export const createSaeReportSchema = z.object({
  reportType: z.enum(['initial', 'follow_up', 'final', 'death', 'expedited', 'annual']),
  reportVersion: z.string().max(20).optional(),
  regulatoryBody: z.string().max(200).optional(),
  reportDate: z.string().datetime(),
  reportContent: z.record(z.any()).optional().default({}),
});
export type CreateSaeReportInput = z.infer<typeof createSaeReportSchema>;

export const submitSaeReportSchema = z.object({
  submittedTo: z.string().min(1).max(200),
  submissionRef: z.string().max(200).optional(),
});
export type SubmitSaeReportInput = z.infer<typeof submitSaeReportSchema>;

export const reviewSaeReportSchema = z.object({
  reviewStatus: z.enum(['approved', 'rejected', 'revision_required']),
  reviewComments: z.string().optional(),
});
export type ReviewSaeReportInput = z.infer<typeof reviewSaeReportSchema>;
