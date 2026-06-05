import { Router } from 'express';
import { auditController } from './audit.controller';
import { requireRole } from '../../shared/middleware/rbac';

const router = Router();

// 审计日志查询（仅管理员和审计员）
router.get('/', requireRole('SUPER_ADMIN', 'AUDITOR') as any, auditController.queryLogs as any);
// 审计统计
router.get('/stats', requireRole('SUPER_ADMIN', 'AUDITOR') as any, auditController.getStats as any);
// 审计日志详情
router.get('/:id', requireRole('SUPER_ADMIN', 'AUDITOR') as any, auditController.getById as any);
// 记录变更历史
router.get('/record/:tableName/:recordId', requireRole('SUPER_ADMIN', 'AUDITOR') as any, auditController.getRecordHistory as any);

export default router;
