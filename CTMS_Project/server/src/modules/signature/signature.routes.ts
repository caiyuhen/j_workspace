import { Router } from 'express';
import { signatureController } from './signature.controller';

const router = Router();

router.get('/', signatureController.list as any);
router.get('/stats', signatureController.getStats as any);
router.get('/audit-trail/:recordId', signatureController.auditTrail as any);
router.get('/audit-report/:recordId', signatureController.exportAuditReport as any);
router.post('/', signatureController.create as any);
router.post('/batch', signatureController.batchCreate as any);
router.get('/:id/verify', signatureController.verify as any);
router.post('/:id/revoke', signatureController.revoke as any);

export default router;
