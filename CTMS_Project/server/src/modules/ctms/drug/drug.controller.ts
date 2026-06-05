import { Request, Response, NextFunction } from 'express';
import { drugService } from './drug.service';
import {
  createDrugSchema, updateDrugSchema,
  createSupplyPlanSchema, createShipmentSchema, receiveShipmentSchema,
  createInventorySchema, adjustInventorySchema, createDestructionSchema,
} from './drug.dto';

async function createDrug(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createDrugSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.createDrug(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function listDrugs(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await drugService.getDrugList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getDrugById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await drugService.getDrugById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateDrug(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateDrugSchema.parse(req.body);
    const result = await drugService.updateDrug(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 供应计划
async function createSupplyPlan(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createSupplyPlanSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.createSupplyPlan(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getSupplyPlans(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await drugService.getSupplyPlans(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 发运跟踪
async function createShipment(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createShipmentSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.createShipment(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getShipments(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await drugService.getShipments(req.params.id, req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function receiveShipment(req: Request, res: Response, next: NextFunction) {
  try {
    const input = receiveShipmentSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.receiveShipment(req.params.shipmentId, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 库存管理
async function createInventory(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createInventorySchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.createInventory(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getInventories(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await drugService.getInventories(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function adjustInventory(req: Request, res: Response, next: NextFunction) {
  try {
    const input = adjustInventorySchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.adjustInventory(req.params.inventoryId, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 回收销毁
async function createDestruction(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createDestructionSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await drugService.createDestruction(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getDestructions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await drugService.getDestructions(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const drugController = {
  createDrug, listDrugs, getDrugById, updateDrug,
  createSupplyPlan, getSupplyPlans,
  createShipment, getShipments, receiveShipment,
  createInventory, getInventories, adjustInventory,
  createDestruction, getDestructions,
};
