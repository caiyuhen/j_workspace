import { z } from 'zod';

export const createSignatureSchema = z.object({
  userId: z.string().uuid(),
  projectId: z.string().uuid().optional(),
  signatureMeaning: z.string().min(1, '签名含义不能为空').max(200),
  signatureReason: z.string().min(1, '签名原因不能为空').max(500),
  tableName: z.string().max(100).optional(),
  recordId: z.string().uuid().optional(),
  previousHash: z.string().max(64).optional(),
});
export type CreateSignatureInput = z.infer<typeof createSignatureSchema>;

export const verifySignatureSchema = z.object({
  signatureId: z.string().uuid(),
  expectedHash: z.string().max(64).optional(),
});
export type VerifySignatureInput = z.infer<typeof verifySignatureSchema>;
