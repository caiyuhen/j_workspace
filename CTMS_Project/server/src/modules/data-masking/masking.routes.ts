import { Router } from 'express';
import { maskingController } from './masking.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

router.get('/', maskingController.list as any);
router.get('/stats', maskingController.getStats as any);
router.get('/suggestions', maskingController.getSuggestions as any);
router.post('/preview', maskingController.preview as any);
router.post('/batch', maskingController.batchMask as any);
router.post('/', requirePermission('sys:config') as any, maskingController.create as any);
router.get('/:id', maskingController.getById as any);
router.put('/:id', requirePermission('sys:config') as any, maskingController.update as any);
router.delete('/:id', requirePermission('sys:config') as any, maskingController.remove as any);

export default router;
