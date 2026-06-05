// monitoring.routes.ts - 监察管理路由

import { Router } from 'express';
import { requireRole } from '../../../shared/middleware/rbac';
import * as monitoringController from './monitoring.controller';

const router = Router();

// ==================== 监察计划路由 ====================

// GET /api/monitoring/plans - 列表
router.get('/plans', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, monitoringController.listPlans as any);

// POST /api/monitoring/plans - 创建
router.post('/plans', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA') as any, monitoringController.createPlan as any);

// GET /api/monitoring/plans/:id - 详情
router.get('/plans/:id', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, monitoringController.getPlanById as any);

// PUT /api/monitoring/plans/:id - 更新
router.put('/plans/:id', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA') as any, monitoringController.updatePlan as any);

// DELETE /api/monitoring/plans/:id - 删除
router.delete('/plans/:id', requireRole('SUPER_ADMIN', 'ADMIN') as any, monitoringController.deletePlan as any);

// ==================== 监察访视路由 ====================

// GET /api/monitoring/visits - 列表
router.get('/visits', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, monitoringController.listVisits as any);

// POST /api/monitoring/visits - 创建
router.post('/visits', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA') as any, monitoringController.createVisit as any);

// GET /api/monitoring/visits/:id - 详情
router.get('/visits/:id', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC', 'PI') as any, monitoringController.getVisitById as any);

// PUT /api/monitoring/visits/:id - 更新
router.put('/visits/:id', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA') as any, monitoringController.updateVisit as any);

// DELETE /api/monitoring/visits/:id - 删除
router.delete('/visits/:id', requireRole('SUPER_ADMIN', 'ADMIN') as any, monitoringController.deleteVisit as any);

// ==================== 统计 ====================

// GET /api/monitoring/stats/:projectId - 项目监察统计
router.get('/stats/:projectId', requireRole('SUPER_ADMIN', 'ADMIN', 'CRA', 'CRC') as any, monitoringController.getMonitoringStats as any);

export default router;
