import { z } from 'zod';

export const createConsentSchema = z.object({
  projectId: z.string().uuid(),
  siteId: z.string().uuid(),
  subjectId: z.string().uuid(),
  consentVersion: z.string().min(1).max(20),
  consentDate: z.string().datetime({ offset: true }),
  signeeType: z.enum(['subject', 'lar', 'parent_guardian', 'pi']),
  signeeName: z.string().min(1).max(200),
  reconsentReason: z.string().optional(),
  documentUrl: z.string().max(500).optional(),
  signatureId: z.string().uuid().optional(),
});
export type CreateConsentInput = z.infer<typeof createConsentSchema>;

export const updateConsentSchema = createConsentSchema.partial().extend({
  status: z.enum(['active', 'withdrawn', 'expired', 'reconsented']).optional(),
});
export type UpdateConsentInput = z.infer<typeof updateConsentSchema>;
