import { Router } from 'express';
import { sdvController } from './sdv.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// SDV 记录
router.get('/', sdvController.list as any);
router.get('/statistics', sdvController.getStatistics as any);
router.post('/', requirePermission('edc:sdv:create') as any, sdvController.create as any);
router.get('/:id', sdvController.getById as any);
router.put('/:id', requirePermission('edc:sdv:update') as any, sdvController.updateRecord as any);

// SDV 核查项
router.post('/:id/items', requirePermission('edc:sdv:execute') as any, sdvController.addItems as any);
router.put('/:id/items/:itemId', requirePermission('edc:sdv:execute') as any, sdvController.updateItem as any);
router.post('/:id/items/batch', requirePermission('edc:sdv:execute') as any, sdvController.batchUpdateItems as any);

// 完成 SDV
router.post('/:id/complete', requirePermission('edc:sdv:complete') as any, sdvController.complete as any);

export default router;
