import { z } from 'zod';

// ========== 患者 DTO ==========

export const createPatientSchema = z.object({
  patientName: z.string().min(1).max(255),
  gender: z.enum(['male', 'female', 'other']),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  contactInfo: z.string().max(1000).optional(),
  diagnosis: z.string().max(1000).optional(),
  treatmentHistory: z.array(z.string()).optional(),
  patientTags: z.array(z.string()).optional(),
});

export type CreatePatientInput = z.infer<typeof createPatientSchema>;

export const updatePatientSchema = z.object({
  patientName: z.string().min(1).max(255).optional(),
  gender: z.enum(['male', 'female', 'other']).optional(),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  contactInfo: z.string().max(1000).optional(),
  diagnosis: z.string().max(1000).optional(),
  treatmentHistory: z.array(z.string()).optional(),
  patientTags: z.array(z.string()).optional(),
});

export type UpdatePatientInput = z.infer<typeof updatePatientSchema>;