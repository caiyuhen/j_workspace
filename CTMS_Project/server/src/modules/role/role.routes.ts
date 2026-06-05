import { Router } from 'express';
import { roleController } from './role.controller';
import { requireRole } from '../../shared/middleware/rbac';

const router = Router();

// 权限列表（所有认证用户可查看，前端角色分配时需要）
router.get('/permissions', roleController.listPermissions as any);
// 角色列表
router.get('/', roleController.list as any);
// 创建角色（仅管理员）
router.post('/', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, roleController.create as any);
// 角色详情
router.get('/:id', roleController.getById as any);
// 更新角色
router.put('/:id', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, roleController.update as any);
// 删除角色
router.delete('/:id', requireRole('SUPER_ADMIN') as any, roleController.remove as any);
// 分配权限
router.post('/:id/permissions', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, roleController.assignPermissions as any);
// 角色下的用户列表
router.get('/:id/users', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, roleController.getRoleUsers as any);

export default router;
