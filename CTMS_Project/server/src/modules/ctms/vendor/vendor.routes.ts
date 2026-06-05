import { Router } from 'express';
import { vendorController } from './vendor.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

router.get('/', vendorController.list as any);
router.get('/stats', vendorController.getStats as any);
router.post('/', requirePermission('vendor:manage') as any, vendorController.create as any);
router.get('/:id', vendorController.getById as any);
router.get('/:id/contracts', vendorController.getContractStats as any);
router.put('/:id', requirePermission('vendor:manage') as any, vendorController.update as any);
router.delete('/:id', requirePermission('vendor:manage') as any, vendorController.remove as any);
router.post('/:id/rating', requirePermission('vendor:manage') as any, vendorController.updateRating as any);
router.post('/:id/blacklist', requirePermission('vendor:manage') as any, vendorController.toggleBlacklist as any);

export default router;
