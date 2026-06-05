// JWT 认证中间件

import { Request, Response, NextFunction } from 'express';
import { verifyAccessToken, JwtPayload } from '../utils/jwt';
import logger from '../utils/logger';

// 扩展 Express Request 类型
declare global {
  namespace Express {
    interface Request {
      user?: JwtPayload;
    }
  }
}

/**
 * JWT 认证中间件
 * 验证 Authorization header 中的 Bearer token
 */
export const authenticate = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      res.status(401).json({
        success: false,
        message: 'No token provided',
        error: 'UNAUTHORIZED',
      });
      return;
    }

    const token = authHeader.substring(7); // 移除"Bearer "前缀

    try {
      const payload = verifyAccessToken(token);
      req.user = payload;
      next();
    } catch (error) {
      logger.warn(`Authentication failed: ${error}`);
      res.status(401).json({
        success: false,
        message: 'Invalid or expired token',
        error: 'UNAUTHORIZED',
      });
    }
  } catch (error) {
    logger.error(`Authentication middleware error: ${error}`);
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: 'INTERNAL_ERROR',
    });
  }
};

/**
 * 可选认证中间件
 * 如果提供 token 则验证，但不强制要求
 */
export const optionalAuth = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  try {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const payload = verifyAccessToken(token);
      req.user = payload;
    }

    next();
  } catch (error) {
    // 忽略错误，继续执行
    next();
  }
};

/**
 * 租户认证中间件
 * 验证 X-Tenant-ID header
 */
export const authenticateTenant = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  try {
    const tenantId = req.headers['x-tenant-id'] as string;

    if (!tenantId) {
      res.status(400).json({
        success: false,
        message: 'Tenant ID is required',
        error: 'BAD_REQUEST',
      });
      return;
    }

    // TODO: 验证租户是否存在且活跃
    // const tenant = await prisma.tenant.findUnique({ where: { id: tenantId } });
    // if (!tenant || tenant.status !== 'ACTIVE') {
    //   res.status(404).json({
    //     success: false,
    //     message: 'Tenant not found or inactive',
    //     error: 'TENANT_NOT_FOUND',
    //   });
    //   return;
    // }

    req.tenantId = tenantId;
    next();
  } catch (error) {
    logger.error(`Tenant authentication error: ${error}`);
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: 'INTERNAL_ERROR',
    });
  }
};
