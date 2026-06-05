import { z } from 'zod';

// ========== 药物管理 DTO ==========

export const createDrugSchema = z.object({
  projectId: z.string().uuid(),
  drugCode: z.string().min(1, '药物编码不能为空').max(100),
  drugName: z.string().min(1, '药物名称不能为空').max(200),
  genericName: z.string().max(200).optional(),
  dosageForm: z.string().max(100).optional(),
  strength: z.string().max(100).optional(),
  manufacturer: z.string().max(200).optional(),
  storageCondition: z.string().max(500).optional(),
  temperatureMin: z.number().optional(),
  temperatureMax: z.number().optional(),
  shelfLife: z.number().int().positive().optional(),
  shelfLifeUnit: z.enum(['days', 'weeks', 'months', 'years']).optional(),
  isBlinded: z.boolean().optional().default(false),
  description: z.string().optional(),
});
export type CreateDrugInput = z.infer<typeof createDrugSchema>;

export const updateDrugSchema = createDrugSchema.partial().omit({ projectId: true, drugCode: true });
export type UpdateDrugInput = z.infer<typeof updateDrugSchema>;

export const createSupplyPlanSchema = z.object({
  planName: z.string().min(1).max(200),
  plannedDate: z.string().datetime(),
  quantity: z.number().int().positive(),
  batchNumber: z.string().max(100).optional(),
  expiryDate: z.string().datetime().optional(),
  notes: z.string().optional(),
});
export type CreateSupplyPlanInput = z.infer<typeof createSupplyPlanSchema>;

export const createShipmentSchema = z.object({
  shipmentCode: z.string().min(1).max(100),
  fromLocation: z.string().min(1).max(200),
  toSiteId: z.string().uuid().optional(),
  toLocation: z.string().max(200).optional(),
  quantity: z.number().int().positive(),
  batchNumber: z.string().min(1).max(100),
  expiryDate: z.string().datetime(),
  shippedDate: z.string().datetime(),
  courier: z.string().max(200).optional(),
  trackingNumber: z.string().max(100).optional(),
  notes: z.string().optional(),
});
export type CreateShipmentInput = z.infer<typeof createShipmentSchema>;

export const receiveShipmentSchema = z.object({
  receivedDate: z.string().datetime().optional(),
  temperatureOk: z.boolean().optional(),
  temperatureLog: z.record(z.any()).optional(),
  notes: z.string().optional(),
});
export type ReceiveShipmentInput = z.infer<typeof receiveShipmentSchema>;

export const createInventorySchema = z.object({
  location: z.string().min(1).max(200),
  batchNumber: z.string().min(1).max(100),
  expiryDate: z.string().datetime(),
  quantityOnHand: z.number().int().min(0),
  siteId: z.string().uuid().optional(),
  notes: z.string().optional(),
});
export type CreateInventoryInput = z.infer<typeof createInventorySchema>;

export const adjustInventorySchema = z.object({
  adjustQuantity: z.number().int(),
  reason: z.string().min(1, '调整原因不能为空'),
});
export type AdjustInventoryInput = z.infer<typeof adjustInventorySchema>;

export const createDestructionSchema = z.object({
  batchNumber: z.string().min(1).max(100),
  quantity: z.number().int().positive(),
  destructionDate: z.string().datetime(),
  destructionMethod: z.string().min(1).max(200),
  reason: z.string().min(1, '销毁原因不能为空'),
  witnessIds: z.array(z.string()).optional().default([]),
  siteId: z.string().uuid().optional(),
  certificateUrl: z.string().max(500).optional(),
});
export type CreateDestructionInput = z.infer<typeof createDestructionSchema>;
