import { Router } from 'express';
import { userController } from './user.controller';
import { requireRole } from '../../shared/middleware/rbac';

const router = Router();

// 用户列表（所有认证用户可访问）
router.get('/', userController.list as any);
// 用户详情
router.get('/:id', userController.getById as any);
// 创建用户（仅管理员）
router.post('/', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, userController.create as any);
// 更新用户
router.put('/:id', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, userController.update as any);
// 删除用户
router.delete('/:id', requireRole('SUPER_ADMIN') as any, userController.remove as any);
// 分配角色
router.post('/:id/roles', requireRole('SUPER_ADMIN', 'SPONSOR_ADMIN') as any, userController.assignRoles as any);
// 重置密码（仅超管）
router.post('/:id/reset-password', requireRole('SUPER_ADMIN') as any, userController.resetPassword as any);

export default router;
