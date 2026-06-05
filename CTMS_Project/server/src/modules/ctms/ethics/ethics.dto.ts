import { z } from 'zod';

export const createEthicsSchema = z.object({
  projectId: z.string().uuid(),
  siteId: z.string().uuid().optional(),
  ethicsCommittee: z.string().min(1, '伦理委员会名称不能为空').max(200),
  approvalType: z.enum(['initial', 'amendment', 'follow_up', 'annual_review', 'safety_report']),
  approvalNumber: z.string().max(100).optional(),
  submissionDate: z.string().date().optional(),
  approvalDate: z.string().date().optional(),
  expiryDate: z.string().date().optional(),
  approvalStatus: z.enum(['pending', 'under_review', 'approved', 'conditionally_approved', 'rejected', 'withdrawn']).optional(),
  documentUrl: z.string().max(500).optional(),
  notes: z.string().optional(),
});
export type CreateEthicsInput = z.infer<typeof createEthicsSchema>;

export const updateEthicsSchema = createEthicsSchema.partial();
export type UpdateEthicsInput = z.infer<typeof updateEthicsSchema>;
