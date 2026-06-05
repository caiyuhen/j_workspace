import { Router } from 'express';
import { editCheckController } from './edit-check.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

router.post('/test', requirePermission('edc:edit_check:execute') as any, editCheckController.testRule as any);
router.post('/execute', requirePermission('edc:edit_check:execute') as any, editCheckController.executeFormChecks as any);

export default router;
