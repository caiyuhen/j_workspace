import { z } from 'zod';

export const createContractSchema = z.object({
  contractCode: z.string().min(1, '合同编码不能为空').max(100),
  contractName: z.string().min(1, '合同名称不能为空').max(300),
  contractType: z.enum(['master', 'amendment', 'sow', 'nda', 'other']),
  vendorId: z.string().uuid().optional(),
  projectId: z.string().uuid().optional(),
  amount: z.number().nonnegative().optional(),
  currency: z.string().max(10).optional().default('CNY'),
  startDate: z.string().date().optional(),
  endDate: z.string().date().optional(),
  attachmentUrl: z.string().max(500).optional(),
  description: z.string().optional(),
});
export type CreateContractInput = z.infer<typeof createContractSchema>;

export const updateContractSchema = createContractSchema.partial().extend({
  signStatus: z.enum(['draft', 'pending_sign', 'signed', 'expired', 'terminated']).optional(),
  version: z.string().max(20).optional(),
});
export type UpdateContractInput = z.infer<typeof updateContractSchema>;
