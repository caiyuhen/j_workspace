import { Request, Response, NextFunction } from 'express';
import { verifyToken } from '../utils/jwt';
import { UnauthorizedError } from '../errors/AppError';
import logger from '../utils/logger';
import config from '../../config/env';

declare global {
  namespace Express {
    interface Request {
      user?: {
        userId: string;
        username: string;
        roles: string[];
        permissions: string[];
        siteIds?: string[];
        projectIds?: string[];
      };
    }
  }
}

/**
 * JWT 认证中间件
 * 从 Authorization header 提取并验证 token
 * 21 CFR Part 11 合规：记录会话ID和IP地址
 */
export function authMiddleware() {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const authHeader = req.headers.authorization;
      
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        throw new UnauthorizedError('Missing or invalid authorization header');
      }

      const token = authHeader.split(' ')[1];
      const payload = verifyToken(token);

      // 将用户信息附加到请求对象
      req.user = {
        userId: payload.userId,
        username: payload.username,
        roles: payload.roles || [],
        permissions: payload.permissions || [],
        siteIds: payload.siteIds,
        projectIds: payload.projectIds,
      };

      // 21 CFR Part 11 合规：记录访问日志
      logger.info('API Access', {
        userId: payload.userId,
        username: payload.username,
        method: req.method,
        path: req.path,
        ip: req.ip || req.socket.remoteAddress,
        userAgent: req.get('User-Agent'),
      });

      next();
    } catch (err) {
      next(new UnauthorizedError('Invalid or expired token'));
    }
  };
}

/**
 * 可选的认证中间件（用于公开接口）
 */
export function optionalAuthMiddleware() {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const authHeader = req.headers.authorization;
      
      if (authHeader && authHeader.startsWith('Bearer ')) {
        const token = authHeader.split(' ')[1];
        const payload = verifyToken(token);
        req.user = {
          userId: payload.userId,
          username: payload.username,
          roles: payload.roles || [],
          permissions: payload.permissions || [],
          siteIds: payload.siteIds,
          projectIds: payload.projectIds,
        };
      }
    } catch {
      // 忽略错误，继续作为未认证用户
    }
    next();
  };
}
