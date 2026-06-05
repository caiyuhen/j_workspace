import prisma from '../../../config/database';
import {
  CreateDrugInput, UpdateDrugInput,
  CreateSupplyPlanInput, CreateShipmentInput, ReceiveShipmentInput,
  CreateInventoryInput, AdjustInventoryInput, CreateDestructionInput,
} from './drug.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const DRUG_SORT_FIELDS = ['drugName', 'drugCode', 'status', 'createdAt', 'updatedAt'];

// ========== 药物信息管理 ==========

async function createDrug(input: CreateDrugInput, userId: string) {
  const project = await prisma.project.findUnique({ where: { id: input.projectId } });
  if (!project) throw new NotFoundError('Project', input.projectId);

  const existing = await prisma.drug.findUnique({
    where: { projectId_drugCode: { projectId: input.projectId, drugCode: input.drugCode } },
  });
  if (existing) throw new ConflictError('药物编码已存在');

  const drug = await prisma.drug.create({ data: input });

  logger.info('Drug created', {
    audit: true, eventType: 'DRUG_CREATE', projectId: input.projectId,
    message: `创建药物: ${input.drugName}`,
  });

  return drug;
}

async function getDrugList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, DRUG_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.status) where.status = query.status;
  if (query.isBlinded !== undefined) where.isBlinded = query.isBlinded === 'true';
  if (query.keyword) {
    where.OR = [
      { drugName: { contains: query.keyword, mode: 'insensitive' } },
      { drugCode: { contains: query.keyword, mode: 'insensitive' } },
      { genericName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [drugs, total] = await Promise.all([
    prisma.drug.findMany({
      where, ...prismaPagination(pagination),
      include: {
        _count: { select: { shipments: true, inventories: true, supplyPlans: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.drug.count({ where }),
  ]);

  return buildPaginatedResult(drugs, total, pagination);
}

async function getDrugById(id: string) {
  const drug = await prisma.drug.findUnique({
    where: { id },
    include: {
      shipments: { orderBy: { shippedDate: 'desc' }, take: 20 },
      inventories: { orderBy: { createdAt: 'desc' } },
      supplyPlans: { orderBy: { plannedDate: 'asc' } },
    },
  });
  if (!drug) throw new NotFoundError('Drug', id);
  return drug;
}

async function updateDrug(id: string, input: UpdateDrugInput) {
  const drug = await prisma.drug.findUnique({ where: { id } });
  if (!drug) throw new NotFoundError('Drug', id);

  const updated = await prisma.drug.update({ where: { id }, data: input });

  logger.info('Drug updated', {
    audit: true, eventType: 'DRUG_UPDATE', projectId: drug.projectId,
    message: `更新药物: ${drug.drugName}`,
  });

  return updated;
}

// ========== 供应计划 ==========

async function createSupplyPlan(drugId: string, input: CreateSupplyPlanInput, userId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  const plan = await prisma.drugSupplyPlan.create({
    data: {
      drugId,
      ...input,
      plannedDate: new Date(input.plannedDate),
      expiryDate: input.expiryDate ? new Date(input.expiryDate) : undefined,
      createdBy: userId,
    },
  });

  logger.info('Drug supply plan created', {
    audit: true, eventType: 'DRUG_SUPPLY_PLAN_CREATE', projectId: drug.projectId,
    message: `创建供应计划: ${input.planName}`,
  });

  return plan;
}

async function getSupplyPlans(drugId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  return prisma.drugSupplyPlan.findMany({
    where: { drugId },
    orderBy: { plannedDate: 'asc' },
  });
}

// ========== 发运跟踪 ==========

async function createShipment(drugId: string, input: CreateShipmentInput, userId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  const existing = await prisma.drugShipment.findUnique({ where: { shipmentCode: input.shipmentCode } });
  if (existing) throw new ConflictError('发运编码已存在');

  const shipment = await prisma.drugShipment.create({
    data: {
      drugId,
      ...input,
      shippedDate: new Date(input.shippedDate),
      expiryDate: new Date(input.expiryDate),
      status: 'shipped',
    },
  });

  logger.info('Drug shipment created', {
    audit: true, eventType: 'DRUG_SHIPMENT_CREATE', projectId: drug.projectId,
    message: `创建发运: ${input.shipmentCode}`,
  });

  return shipment;
}

async function getShipments(drugId: string, query: Record<string, any>) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  const where: any = { drugId };
  if (query.status) where.status = query.status;
  if (query.toSiteId) where.toSiteId = query.toSiteId;

  return prisma.drugShipment.findMany({
    where,
    orderBy: { shippedDate: 'desc' },
  });
}

async function receiveShipment(shipmentId: string, input: ReceiveShipmentInput, userId: string) {
  const shipment = await prisma.drugShipment.findUnique({ where: { id: shipmentId } });
  if (!shipment) throw new NotFoundError('DrugShipment', shipmentId);
  if (shipment.status === 'received') throw new BadRequestError('该发运已接收');

  const updated = await prisma.drugShipment.update({
    where: { id: shipmentId },
    data: {
      status: 'received',
      receivedDate: input.receivedDate ? new Date(input.receivedDate) : new Date(),
      receivedBy: userId,
      temperatureOk: input.temperatureOk,
      temperatureLog: input.temperatureLog,
    },
  });

  // 自动创建库存记录
  await prisma.drugInventory.create({
    data: {
      drugId: shipment.drugId,
      siteId: shipment.toSiteId,
      location: shipment.toLocation || '默认仓库',
      batchNumber: shipment.batchNumber,
      expiryDate: shipment.expiryDate,
      quantityOnHand: shipment.quantity,
    },
  });

  logger.info('Drug shipment received', {
    audit: true, eventType: 'DRUG_SHIPMENT_RECEIVE',
    message: `接收发运: ${shipment.shipmentCode}`,
  });

  return updated;
}

// ========== 库存管理 ==========

async function createInventory(drugId: string, input: CreateInventoryInput, userId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  const inventory = await prisma.drugInventory.create({
    data: {
      drugId,
      ...input,
      expiryDate: new Date(input.expiryDate),
    },
  });

  logger.info('Drug inventory created', {
    audit: true, eventType: 'DRUG_INVENTORY_CREATE', projectId: drug.projectId,
    message: `创建库存记录: ${input.batchNumber}`,
  });

  return inventory;
}

async function getInventories(drugId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  return prisma.drugInventory.findMany({
    where: { drugId },
    orderBy: { createdAt: 'desc' },
  });
}

async function adjustInventory(inventoryId: string, input: AdjustInventoryInput, userId: string) {
  const inventory = await prisma.drugInventory.findUnique({ where: { id: inventoryId } });
  if (!inventory) throw new NotFoundError('DrugInventory', inventoryId);

  const newQuantity = inventory.quantityOnHand + input.adjustQuantity;
  if (newQuantity < 0) throw new BadRequestError('调整后库存不能为负数');

  const updated = await prisma.drugInventory.update({
    where: { id: inventoryId },
    data: {
      quantityOnHand: newQuantity,
      lastCountDate: new Date(),
    },
  });

  logger.info('Drug inventory adjusted', {
    audit: true, eventType: 'DRUG_INVENTORY_ADJUST',
    message: `库存调整: ${inventory.batchNumber}, 数量 ${inventory.quantityOnHand} → ${newQuantity}`,
  });

  return updated;
}

// ========== 药物回收销毁 ==========

async function createDestruction(drugId: string, input: CreateDestructionInput, userId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  const destruction = await prisma.drugDestruction.create({
    data: {
      drugId,
      ...input,
      destructionDate: new Date(input.destructionDate),
      performedBy: userId,
      witnessIds: input.witnessIds || [],
    },
  });

  logger.info('Drug destruction created', {
    audit: true, eventType: 'DRUG_DESTRUCTION_CREATE', projectId: drug.projectId,
    message: `药物销毁: ${input.batchNumber}, 数量 ${input.quantity}`,
  });

  return destruction;
}

async function getDestructions(drugId: string) {
  const drug = await prisma.drug.findUnique({ where: { id: drugId } });
  if (!drug) throw new NotFoundError('Drug', drugId);

  return prisma.drugDestruction.findMany({
    where: { drugId },
    orderBy: { destructionDate: 'desc' },
  });
}

export const drugService = {
  createDrug, getDrugList, getDrugById, updateDrug,
  createSupplyPlan, getSupplyPlans,
  createShipment, getShipments, receiveShipment,
  createInventory, getInventories, adjustInventory,
  createDestruction, getDestructions,
};
