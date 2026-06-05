import { Router } from 'express';
import { exportController } from './export.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

router.get('/history', requirePermission('data:export') as any, exportController.history as any);
router.post('/', requirePermission('data:export') as any, exportController.exportData as any);

export default router;
