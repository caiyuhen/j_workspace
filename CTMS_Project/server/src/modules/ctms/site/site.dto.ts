import { z } from 'zod';

// ========== 中心管理 DTO ==========

export const createSiteSchema = z.object({
  projectId: z.string().uuid().optional(),
  siteCode: z.string().min(1, '中心编码不能为空').max(50),
  siteName: z.string().min(1, '中心名称不能为空').max(200),
  piUserId: z.string().uuid().optional(),
  address: z.string().optional().nullable().or(z.literal('')),
  contactPhone: z.string().optional().nullable().or(z.literal('')),
  ethicsStatus: z.enum(['pending', 'approved', 'rejected', 'not_required']).optional().default('pending'),
  contractStatus: z.enum(['pending', 'signed', 'terminated']).optional().default('pending'),
  gcpContactName: z.string().optional().nullable().or(z.literal('')),
  gcpContactPhone: z.string().optional().nullable().or(z.literal('')),
  researchContactName: z.string().optional().nullable().or(z.literal('')),
  researchContactPhone: z.string().optional().nullable().or(z.literal('')),
});
export type CreateSiteInput = z.infer<typeof createSiteSchema>;

export const updateSiteSchema = createSiteSchema.partial().extend({
  status: z.enum(['active', 'inactive', 'suspended', 'closed']).optional(),
});
export type UpdateSiteInput = z.infer<typeof updateSiteSchema>;

export const addSiteStaffSchema = z.object({
  userId: z.string().uuid(),
  roleAtSite: z.enum(['PI', 'SUB_I', 'CRC', 'CRA', 'PHARMACIST', 'NURSE', 'OTHER']),
  joinedAt: z.string().datetime({ offset: true }).optional().or(z.string().date().optional()),
});
export type AddSiteStaffInput = z.infer<typeof addSiteStaffSchema>;

export const updateSiteStaffSchema = addSiteStaffSchema.partial().extend({
  roleAtSite: z.enum(['PI', 'SUB_I', 'CRC', 'CRA', 'PHARMACIST', 'NURSE', 'OTHER']).optional(),
  leftAt: z.string().datetime({ offset: true }).optional().or(z.string().date().optional()),
  status: z.enum(['active', 'inactive']).optional(),
});
export type UpdateSiteStaffInput = z.infer<typeof updateSiteStaffSchema>;
