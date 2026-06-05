import { Router } from 'express';
import { aeController } from './ae.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 不良事件 CRUD
router.get('/', aeController.list as any);
router.get('/statistics', aeController.getStatistics as any);
router.post('/', requirePermission('edc:ae:create') as any, aeController.create as any);
router.get('/:id', aeController.getById as any);
router.put('/:id', requirePermission('edc:ae:update') as any, aeController.update as any);
router.post('/:id/close', requirePermission('edc:ae:close') as any, aeController.close as any);

// SAE 报告管理
router.get('/:id/reports', aeController.getSaeReports as any);
router.post('/:id/reports', requirePermission('edc:ae:sae_report') as any, aeController.createSaeReport as any);
router.put('/:id/reports/:reportId', requirePermission('edc:ae:sae_report') as any, aeController.updateSaeReport as any);
router.post('/:id/reports/:reportId/review', requirePermission('edc:ae:sae_review') as any, aeController.reviewSaeReport as any);
router.post('/:id/reports/:reportId/submit', requirePermission('edc:ae:sae_submit') as any, aeController.submitSaeReport as any);

export default router;
