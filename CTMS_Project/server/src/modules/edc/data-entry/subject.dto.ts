import { z } from 'zod';

// ========== 受试者管理 DTO ==========

export const createSubjectSchema = z.object({
  projectId: z.string().uuid(),
  siteId: z.string().uuid().optional(),
  subjectCode: z.string().min(1, '受试者编号不能为空').max(50),
  screeningNumber: z.string().optional(),
  enrollmentStatus: z.enum(['screening', 'enrolled', 'randomized', 'ongoing', 'completed', 'discontinued', 'withdrawn']).optional().default('screening'),
});
export type CreateSubjectInput = z.infer<typeof createSubjectSchema>;

export const updateSubjectSchema = createSubjectSchema.partial().extend({
  enrollmentStatus: z.enum(['screening', 'enrolled', 'randomized', 'ongoing', 'completed', 'discontinued', 'withdrawn']).optional(),
  discontinuationReason: z.string().optional(),
  randomizationNumber: z.string().optional(),
});
export type UpdateSubjectInput = z.infer<typeof updateSubjectSchema>;
