import { Router } from 'express';
import { queryController } from './query.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 质疑列表
router.get('/', queryController.list as any);
// 创建质疑
router.post('/', requirePermission('edc:query:create') as any, queryController.create as any);
// 质疑详情
router.get('/:id', queryController.getById as any);
// 回复/关闭/升级质疑
router.post('/:id/reply', requirePermission('edc:query:reply') as any, queryController.reply as any);
// 重新分配质疑
router.post('/:id/reassign', requirePermission('edc:query:reassign') as any, queryController.reassign as any);

export default router;
