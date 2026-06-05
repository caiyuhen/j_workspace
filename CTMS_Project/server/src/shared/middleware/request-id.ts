import { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';
import logger from '../utils/logger';

/**
 * 请求ID中间件
 * 为每个请求生成唯一ID，贯穿整个请求生命周期
 * 21 CFR Part 11 合规：请求追踪
 */
export function requestIdMiddleware() {
  return (req: Request, res: Response, next: NextFunction): void => {
    const requestId = (req.headers['x-request-id'] as string) || crypto.randomUUID();
    
    // 附加到请求和响应对象
    (req as any).requestId = requestId;
    res.setHeader('X-Request-ID', requestId);
    
    // 记录请求开始
    const startTime = Date.now();
    logger.info('Request started', {
      requestId,
      method: req.method,
      path: req.path,
      ip: req.ip || req.socket.remoteAddress,
      userAgent: req.get('User-Agent'),
    });
    
    // 响应完成时记录
    res.on('finish', () => {
      const duration = Date.now() - startTime;
      logger.info('Request completed', {
        requestId,
        method: req.method,
        path: req.path,
        statusCode: res.statusCode,
        durationMs: duration,
      });
    });
    
    next();
  };
}
