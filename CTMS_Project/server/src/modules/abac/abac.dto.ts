import { z } from 'zod';

export const createAbacPolicySchema = z.object({
  policyCode: z.string().min(1).max(100),
  policyName: z.string().min(1).max(200),
  resources: z.record(z.any()),
  conditions: z.record(z.any()),
  effect: z.enum(['permit', 'deny']).optional().default('permit'),
  denyOtherwise: z.boolean().optional().default(false),
  priority: z.number().int().min(0).optional().default(0),
  isActive: z.boolean().optional().default(true),
  description: z.string().optional(),
});
export type CreateAbacPolicyInput = z.infer<typeof createAbacPolicySchema>;

export const updateAbacPolicySchema = createAbacPolicySchema.partial().omit({ policyCode: true });
export type UpdateAbacPolicyInput = z.infer<typeof updateAbacPolicySchema>;

export const evaluateAccessSchema = z.object({
  userId: z.string().uuid(),
  resource: z.string().min(1),
  action: z.string().min(1),
  context: z.record(z.any()).optional(),
});
export type EvaluateAccessInput = z.infer<typeof evaluateAccessSchema>;
