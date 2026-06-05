import { Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { AppError, NotFoundError, ValidationError, UnauthorizedError, ForbiddenError, ConflictError, BadRequestError, TooManyRequestsError } from '../errors/AppError';
import logger from '../utils/logger';

/**
 * 全局错误处理中间件
 * 21 CFR Part 11 合规：不向客户端泄露内部错误信息
 */
export function errorHandler(
  err: any,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // 结构化日志记录
  const logContext = {
    method: req.method,
    path: req.path,
    userId: (req as any).user?.userId || 'anonymous',
    ip: req.ip || req.socket.remoteAddress,
    requestId: (req as any).requestId,
  };

  if (err instanceof z.ZodError) {
    logger.warn(`Validation error: ${err.message}`, {
      ...logContext,
      code: 'VALIDATION_ERROR',
      statusCode: 400,
    });

    res.status(400).json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: '数据校验失败',
        details: err.errors,
        requestId: (req as any).requestId,
      },
    });
    return;
  }

  if (err instanceof AppError && err.isOperational) {
    // 可预期的操作错误 → 结构化响应
    logger.warn(`Operational error: ${err.message}`, {
      ...logContext,
      code: err.code,
      statusCode: err.statusCode,
      details: err.details,
    });

    res.status(err.statusCode).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        ...(err.details ? { details: err.details } : {}),
        requestId: (req as any).requestId,
      },
    });
    return;
  }

  // 未捕获的编程错误 → 记录完整堆栈，返回通用错误
  logger.error('Unexpected error', {
    ...logContext,
    message: err.message,
    stack: err.stack,
  });

  // DEBUG: Log actual error for troubleshooting
  console.error('=== ACTUAL ERROR ===');
  console.error(err);
  console.error('===================');

  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred. Please try again later.',
      requestId: (req as any).requestId,
    },
  });
}

/**
 * 404 处理中间件
 */
export function notFoundHandler(req: Request, res: Response, next: NextFunction): void {
  next(new NotFoundError(`Route ${req.method} ${req.path}`));
}
