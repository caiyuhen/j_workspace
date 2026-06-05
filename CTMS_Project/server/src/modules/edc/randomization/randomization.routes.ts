// randomization.routes.ts - 随机化管理路由

import { Router } from 'express';
import { requireRole } from '../../../shared/middleware/rbac';
import * as randomizationController from './randomization.controller';

const router = Router();

// 列表
router.get('/', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, randomizationController.listRecords as any);

// 统计
router.get('/stats/:projectId', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, randomizationController.getRandomizationStats as any);

// 号池状态
router.get('/pool/:projectId', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, randomizationController.getNumberPoolStatus as any);

// 导出清单
router.get('/export/:projectId', requireRole('SUPER_ADMIN', 'ADMIN') as any, randomizationController.exportRandomizationList as any);

// 创建随机化记录
router.post('/', requireRole('SUPER_ADMIN', 'ADMIN', 'CRC', 'PI') as any, randomizationController.createRecord as any);

// 紧急揭盲
router.post('/emergency-unblind/:subjectId', requireRole('SUPER_ADMIN', 'ADMIN', 'PI') as any, randomizationController.emergencyUnblind as any);

// 按受试者查询
router.get('/subject/:subjectId', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, randomizationController.getRecordBySubject as any);

// 详情
router.get('/:id', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, randomizationController.getRecordById as any);

export default router;
