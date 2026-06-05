import { Router } from 'express';
import { subjectController } from './subject.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 受试者列表
router.get('/', subjectController.list as any);
// 登记受试者
router.post('/', requirePermission('edc:subject:create') as any, subjectController.create as any);
// 受试者详情
router.get('/:id', subjectController.getById as any);
// 更新受试者
router.put('/:id', requirePermission('edc:subject:update') as any, subjectController.update as any);

// 访视管理
router.get('/:id/visits', subjectController.getVisits as any);
router.post('/:id/visits', requirePermission('edc:visit:create') as any, subjectController.createVisit as any);

export default router;
