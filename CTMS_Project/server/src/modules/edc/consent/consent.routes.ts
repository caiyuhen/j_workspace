import { Router } from 'express';
import { consentController } from './consent.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

router.get('/', consentController.list as any);
router.get('/stats', consentController.getStats as any);
router.get('/subject-history', consentController.subjectHistory as any);
router.get('/versions/:projectId', consentController.getVersions as any);
router.post('/', requirePermission('edc:consent:manage') as any, consentController.create as any);
router.get('/:id', consentController.getById as any);
router.put('/:id', requirePermission('edc:consent:manage') as any, consentController.update as any);
router.post('/:id/withdraw', requirePermission('edc:consent:manage') as any, consentController.withdraw as any);

export default router;
