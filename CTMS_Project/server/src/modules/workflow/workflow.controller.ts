import { Request, Response, NextFunction } from 'express';
import { workflowService } from './workflow.service';
import { createDefinitionSchema, updateDefinitionSchema, startInstanceSchema, processTaskSchema } from './workflow.dto';

// ========== 流程定义 ==========

async function createDefinition(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createDefinitionSchema.parse(req.body);
    const result = await workflowService.createDefinition(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function listDefinitions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.getDefinitionList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getDefinition(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.getDefinitionById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateDefinition(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateDefinitionSchema.parse(req.body);
    const result = await workflowService.updateDefinition(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// ========== 流程实例 ==========

async function startInstance(req: Request, res: Response, next: NextFunction) {
  try {
    const input = startInstanceSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await workflowService.startInstance(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function listInstances(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.getInstanceList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getInstance(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.getInstanceById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function processTask(req: Request, res: Response, next: NextFunction) {
  try {
    const input = processTaskSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await workflowService.processTask(req.params.taskId, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function cancelInstance(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.userId;
    const reason = req.body.reason || '用户主动撤销';
    const result = await workflowService.cancelInstance(req.params.id, userId, reason);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// ========== 待办与超时 ==========

async function getMyPendingTasks(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.userId;
    const result = await workflowService.getMyPendingTasks(userId, req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getTimeoutTasks(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.getTimeoutTasks(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function processTimeoutTasks(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.processTimeoutTasks();
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// ========== 统计 ==========

async function getWorkflowStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await workflowService.getWorkflowStats(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const workflowController = {
  createDefinition, listDefinitions, getDefinition, updateDefinition,
  startInstance, listInstances, getInstance, processTask, cancelInstance,
  getMyPendingTasks, getTimeoutTasks, processTimeoutTasks, getWorkflowStats,
};
