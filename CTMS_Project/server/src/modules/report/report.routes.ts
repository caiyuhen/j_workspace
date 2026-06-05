import { Router } from 'express';
import { reportController } from './report.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

router.get('/instances', reportController.listInstances as any);
router.get('/', reportController.listTemplates as any);
router.post('/generate', requirePermission('report:generate') as any, reportController.generate as any);
router.post('/', requirePermission('report:manage') as any, reportController.createTemplate as any);
router.get('/:id', reportController.getTemplateById as any);
router.put('/:id', requirePermission('report:manage') as any, reportController.updateTemplate as any);

export default router;
