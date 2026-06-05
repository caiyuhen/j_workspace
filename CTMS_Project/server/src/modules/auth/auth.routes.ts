import { Router } from 'express';
import { authController } from './auth.controller';
import { authMiddleware } from '../../shared/middleware/auth';

const router = Router();

// 公开路由（不需要认证）
router.post('/login', authController.login as any);
router.post('/register', authController.register as any);
router.post('/refresh', authController.refresh as any);

// 需要认证的路由
router.get('/me', authMiddleware() as any, authController.getMe as any);
router.put('/password', authMiddleware() as any, authController.changePassword as any);

export default router;
