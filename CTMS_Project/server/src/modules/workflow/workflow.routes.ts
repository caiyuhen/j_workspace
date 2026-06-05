import { Router } from 'express';
import { workflowController } from './workflow.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

// 流程定义
router.get('/definitions', workflowController.listDefinitions as any);
router.post('/definitions', requirePermission('workflow:definition:create') as any, workflowController.createDefinition as any);
router.get('/definitions/:id', workflowController.getDefinition as any);
router.put('/definitions/:id', requirePermission('workflow:definition:update') as any, workflowController.updateDefinition as any);

// 流程实例
router.get('/instances', workflowController.listInstances as any);
router.post('/instances/start', requirePermission('workflow:instance:start') as any, workflowController.startInstance as any);
router.get('/instances/:id', workflowController.getInstance as any);
router.post('/instances/:taskId/process', requirePermission('workflow:task:process') as any, workflowController.processTask as any);
router.post('/instances/:id/cancel', requirePermission('workflow:instance:cancel') as any, workflowController.cancelInstance as any);

// 我的待办
router.get('/my-tasks', workflowController.getMyPendingTasks as any);

// 超时管理（管理员/系统调用）
router.get('/timeout-tasks', requirePermission('workflow:admin') as any, workflowController.getTimeoutTasks as any);
router.post('/timeout-tasks/process', requirePermission('workflow:admin') as any, workflowController.processTimeoutTasks as any);

// 统计
router.get('/stats', workflowController.getWorkflowStats as any);

export default router;
