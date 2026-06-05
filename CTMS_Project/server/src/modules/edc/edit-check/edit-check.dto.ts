import { z } from 'zod';

export const testRuleSchema = z.object({
  ruleId: z.string().uuid(),
  fieldValues: z.record(z.any()),
  projectId: z.string().uuid(),
  subjectId: z.string().uuid().optional(),
  visitId: z.string().uuid().optional(),
  formId: z.string().uuid().optional(),
});
export type TestRuleInput = z.infer<typeof testRuleSchema>;

export const executeFormChecksSchema = z.object({
  formId: z.string().uuid(),
  projectId: z.string().uuid(),
  subjectId: z.string().uuid(),
  visitId: z.string().uuid().optional(),
  fieldValues: z.record(z.any()),
});
export type ExecuteFormChecksInput = z.infer<typeof executeFormChecksSchema>;
