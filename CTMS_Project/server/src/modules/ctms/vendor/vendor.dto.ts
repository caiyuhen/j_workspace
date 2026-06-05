import { z } from 'zod';

export const createVendorSchema = z.object({
  vendorCode: z.string().min(1, '供应商编码不能为空').max(100),
  vendorName: z.string().min(1, '供应商名称不能为空').max(200),
  vendorType: z.enum(['lab', 'cro', 'logistics', 'it', 'consulting', 'other']),
  contactPerson: z.string().max(200).optional(),
  contactPhone: z.string().max(50).optional(),
  contactEmail: z.string().email().max(200).optional(),
  address: z.string().max(500).optional(),
  qualification: z.record(z.any()).optional(),
  rating: z.number().min(0).max(5).optional(),
  description: z.string().optional(),
});
export type CreateVendorInput = z.infer<typeof createVendorSchema>;

export const updateVendorSchema = createVendorSchema.partial().extend({
  status: z.enum(['active', 'inactive', 'blacklisted']).optional(),
});
export type UpdateVendorInput = z.infer<typeof updateVendorSchema>;
