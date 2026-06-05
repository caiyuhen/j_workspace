import { Router } from 'express';
import { syncController } from './sync.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

router.get('/logs', syncController.listLogs as any);
router.get('/stats', syncController.stats as any);
router.post('/trigger', requirePermission('sync:manage') as any, syncController.trigger as any);

export default router;
