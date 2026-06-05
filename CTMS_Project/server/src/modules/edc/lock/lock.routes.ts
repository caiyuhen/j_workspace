// lock.routes.ts - 数据锁定路由

import { Router } from 'express';
import { requireRole } from '../../../shared/middleware/rbac';
import * as lockController from './lock.controller';

const router = Router();

// GET /api/edc/locks - 锁定记录列表
router.get('/', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, lockController.listLocks as any);

// POST /api/edc/locks - 创建锁定
router.post('/', requireRole('SUPER_ADMIN', 'ADMIN', 'PI') as any, lockController.createLock as any);

// GET /api/edc/locks/stats/:projectId - 项目锁定统计
router.get('/stats/:projectId', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA') as any, lockController.getLockStats as any);

// GET /api/edc/locks/check/:lockType/:targetId - 查询某对象锁定状态
router.get('/check/:lockType/:targetId', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, lockController.checkLockStatus as any);

// GET /api/edc/locks/:id - 锁定记录详情
router.get('/:id', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, lockController.getLockById as any);

// PATCH /api/edc/locks/:id/unlock - 解锁（需要高权限）
router.patch('/:id/unlock', requireRole('SUPER_ADMIN', 'ADMIN') as any, lockController.unlockRecord as any);

export default router;
