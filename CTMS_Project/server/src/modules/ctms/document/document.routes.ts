import { Router } from 'express';
import { documentController } from './document.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 文档 CRUD
router.get('/', documentController.list as any);
router.post('/', requirePermission('ctms:document:create') as any, documentController.create as any);
router.get('/stats', documentController.getCompletionStats as any);
router.get('/:id', documentController.getById as any);
router.put('/:id', requirePermission('ctms:document:update') as any, documentController.update as any);
router.delete('/:id', requirePermission('ctms:document:delete') as any, documentController.remove as any);

// 版本管理
router.get('/:id/versions', documentController.getVersions as any);
router.post('/:id/versions', requirePermission('ctms:document:upload') as any, documentController.uploadVersion as any);
router.get('/:id/versions/:version', documentController.getVersionDetail as any);

// 状态审批
router.put('/:id/status', requirePermission('ctms:document:approve') as any, documentController.updateStatus as any);
router.post('/bulk-status', requirePermission('ctms:document:approve') as any, documentController.bulkUpdateStatus as any);

export default router;
