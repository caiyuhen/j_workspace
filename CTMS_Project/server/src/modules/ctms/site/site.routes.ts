import { Router } from 'express';
import { siteController } from './site.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 中心列表
router.get('/', siteController.list as any);
// 创建中心
router.post('/', requirePermission('site:create') as any, siteController.create as any);
// 中心详情
router.get('/:id', siteController.getById as any);
// 更新中心
router.put('/:id', requirePermission('site:update') as any, siteController.update as any);
// 关闭中心
router.delete('/:id', requirePermission('site:delete') as any, siteController.remove as any);

// 中心人员管理
router.post('/:id/staff', requirePermission('site:staff:manage') as any, siteController.addStaff as any);
router.put('/:id/staff/:staffId', requirePermission('site:staff:manage') as any, siteController.updateStaff as any);
router.delete('/:id/staff/:staffId', requirePermission('site:staff:manage') as any, siteController.removeStaff as any);

export default router;
