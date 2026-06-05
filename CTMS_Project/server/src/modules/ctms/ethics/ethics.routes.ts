import { Router } from 'express';
import { ethicsController } from './ethics.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

router.get('/', ethicsController.list as any);
router.get('/expiring-soon', ethicsController.expiringSoon as any);
router.get('/stats', ethicsController.getStats as any);
router.get('/timeline/:projectId', ethicsController.getTimeline as any);
router.post('/', requirePermission('ethics:manage') as any, ethicsController.create as any);
router.get('/:id', ethicsController.getById as any);
router.put('/:id', requirePermission('ethics:manage') as any, ethicsController.update as any);
router.post('/:id/transition', requirePermission('ethics:manage') as any, ethicsController.transitionStatus as any);

export default router;
