import { Router } from 'express';
import { aiController } from './ai.controller';
import { requirePermission } from '../../shared/middleware/rbac';

const router = Router();

// Agent 能力查询
router.get('/agents', aiController.getAgentList as any);

// AI 对话
router.post('/chat', requirePermission('ai:chat') as any, aiController.chat as any);

// 批量处理
router.post('/batch', requirePermission('ai:batch') as any, aiController.batchProcess as any);

// 数据分析
router.post('/analyze', requirePermission('ai:analyze') as any, aiController.analyze as any);

// Agent 日志
router.get('/logs', aiController.getLogs as any);

export default router;
