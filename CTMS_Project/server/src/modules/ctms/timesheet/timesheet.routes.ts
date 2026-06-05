import { Router } from 'express';
import { timesheetController } from './timesheet.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 工时列表
router.get('/', timesheetController.list as any);
// 创建工时
router.post('/', requirePermission('timesheet:create') as any, timesheetController.create as any);
// 工时详情
router.get('/:id', timesheetController.getById as any);
// 提交审批
router.post('/:id/submit', requirePermission('timesheet:submit') as any, timesheetController.submit as any);
// 审批工时
router.post('/:id/approve', requirePermission('timesheet:approve') as any, timesheetController.approve as any);

export default router;
