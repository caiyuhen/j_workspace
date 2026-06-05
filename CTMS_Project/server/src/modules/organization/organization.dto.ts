import { z } from 'zod';

// ========== 组织机构 DTO ==========

export const createOrgSchema = z.object({
  orgCode: z.string().min(1, '组织编码不能为空').max(100),
  orgName: z.string().min(1, '组织名称不能为空').max(200),
  orgType: z.enum(['sponsor', 'cro', 'site', 'institution', 'irb', 'vendor', 'other']),
  shortName: z.string().max(100).optional().nullable().or(z.literal('')),
  address: z.string().max(200).optional().nullable().or(z.literal('')),
  city: z.string().max(100).optional().nullable().or(z.literal('')),
  province: z.string().max(100).optional().nullable().or(z.literal('')),
  country: z.string().max(50).optional().nullable().or(z.literal('')),
  contactPerson: z.string().max(50).optional().nullable().or(z.literal('')),
  contactPhone: z.string().max(50).optional().nullable().or(z.literal('')),
  contactEmail: z.string().max(200).optional().nullable().or(z.literal('')),
  parentId: z.string().uuid().optional().nullable().or(z.literal('')),
  sortOrder: z.number().int().min(0).optional(),
  description: z.string().optional().nullable().or(z.literal('')),
  
  // 中心专属字段
  gcpContactName: z.string().max(50).optional().nullable().or(z.literal('')),
  gcpContactPhone: z.string().max(50).optional().nullable().or(z.literal('')),
  researchContactName: z.string().max(50).optional().nullable().or(z.literal('')),
  researchContactPhone: z.string().max(50).optional().nullable().or(z.literal('')),
  investigatorName: z.string().optional().nullable().or(z.literal('')),
});
export type CreateOrgInput = z.infer<typeof createOrgSchema>;

export const updateOrgSchema = createOrgSchema.partial().extend({
  status: z.enum(['active', 'inactive']).optional(),
}).refine(data => {
  if (data.orgType === 'site') {
    return true;
  }
  return true;
});
export type UpdateOrgInput = z.infer<typeof updateOrgSchema>;
