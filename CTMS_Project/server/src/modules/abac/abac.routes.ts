import { Router } from 'express';
import { abacController } from './abac.controller';

const router = Router();

// 策略 CRUD
router.post('/', abacController.create as any);
router.get('/', abacController.list as any);
router.get('/:id', abacController.getById as any);
router.put('/:id', abacController.update as any);
router.delete('/:id', abacController.remove as any);

// 权限评估
router.post('/evaluate', abacController.evaluate as any);
router.post('/evaluate/batch', abacController.batchEvaluate as any);

// 适用策略查询
router.get('/effective/:resource', abacController.getEffectivePolicies as any);

export default router;
