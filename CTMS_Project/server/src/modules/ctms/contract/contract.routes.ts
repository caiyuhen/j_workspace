import { Router } from 'express';
import { contractController } from './contract.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

router.get('/', contractController.list as any);
router.get('/expiring-soon', contractController.expiringSoon as any);
router.get('/stats', contractController.getStats as any);
router.post('/', requirePermission('contract:manage') as any, contractController.create as any);
router.get('/:id', contractController.getById as any);
router.put('/:id', requirePermission('contract:manage') as any, contractController.update as any);
router.delete('/:id', requirePermission('contract:manage') as any, contractController.remove as any);
router.post('/:id/transition', requirePermission('contract:manage') as any, contractController.transitionStatus as any);

export default router;
