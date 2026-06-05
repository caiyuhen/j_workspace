import { Router } from 'express';
import { drugController } from './drug.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 药物信息 CRUD
router.get('/', drugController.listDrugs as any);
router.post('/', requirePermission('ctms:drug:create') as any, drugController.createDrug as any);
router.get('/:id', drugController.getDrugById as any);
router.put('/:id', requirePermission('ctms:drug:update') as any, drugController.updateDrug as any);

// 供应计划
router.get('/:id/supply-plans', drugController.getSupplyPlans as any);
router.post('/:id/supply-plans', requirePermission('ctms:drug:supply') as any, drugController.createSupplyPlan as any);

// 发运跟踪
router.get('/:id/shipments', drugController.getShipments as any);
router.post('/:id/shipments', requirePermission('ctms:drug:ship') as any, drugController.createShipment as any);
router.post('/shipments/:shipmentId/receive', requirePermission('ctms:drug:receive') as any, drugController.receiveShipment as any);

// 库存管理
router.get('/:id/inventories', drugController.getInventories as any);
router.post('/:id/inventories', requirePermission('ctms:drug:inventory') as any, drugController.createInventory as any);
router.put('/:id/inventories/:inventoryId', requirePermission('ctms:drug:inventory') as any, drugController.adjustInventory as any);

// 回收销毁
router.get('/:id/destructions', drugController.getDestructions as any);
router.post('/:id/destructions', requirePermission('ctms:drug:destruction') as any, drugController.createDestruction as any);

export default router;
