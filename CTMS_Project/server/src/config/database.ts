import { PrismaClient } from '@prisma/client';
import logger from '../shared/utils/logger';

// Prisma 客户端单例
const prismaClientSingleton = () => {
  return new PrismaClient({
    log: [
      { level: 'query', emit: 'event' },
      { level: 'error', emit: 'stdout' },
      { level: 'warn', emit: 'stdout' },
    ],
  });
};

declare global {
  var prisma: undefined | ReturnType<typeof prismaClientSingleton>;
}

export const prisma = globalThis.prisma ?? prismaClientSingleton();

// 日志查询（仅开发环境）
if (process.env.NODE_ENV === 'development') {
  prisma.$on('query' as any, (e: any) => {
    logger.debug('Prisma Query', { query: e.query, duration: e.duration + 'ms' });
  });
}

if (process.env.NODE_ENV !== 'production') {
  globalThis.prisma = prisma;
}

/**
 * 优雅关闭数据库连接
 */
export async function disconnectDatabase(): Promise<void> {
  await prisma.$disconnect();
  logger.info('Database disconnected');
}

/**
 * 健康检查 — 数据库连接测试
 */
export async function checkDatabaseHealth(): Promise<{ status: string; latencyMs?: number }> {
  try {
    const start = Date.now();
    await prisma.$queryRaw`SELECT 1`;
    const latency = Date.now() - start;
    return { status: 'ok', latencyMs: latency };
  } catch (err) {
    logger.error('Database health check failed', err);
    return { status: 'error' };
  }
}

export default prisma;
