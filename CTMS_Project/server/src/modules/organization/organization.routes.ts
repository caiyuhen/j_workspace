import { Router } from 'express';
import { organizationController } from './organization.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

// 组织列表（所有认证用户可查看）
router.get('/', organizationController.list as any);
// 组织树形结构
router.get('/tree', organizationController.tree as any);
// 创建组织
router.post('/', requirePermission('org:manage') as any, organizationController.create as any);
// 组织详情
router.get('/:id', organizationController.getById as any);
// 更新组织
router.put('/:id', requirePermission('org:manage') as any, organizationController.update as any);
// 停用组织
router.delete('/:id', requirePermission('org:manage') as any, organizationController.remove as any);

export default router;
