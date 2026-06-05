import app from './app';
import config from './config/env';
import logger from './shared/utils/logger';
import prisma from './config/database';

const PORT = config.port;

/**
 * 启动服务器
 */
async function startServer(): Promise<void> {
  try {
    // 测试数据库连接
    await prisma.$connect();
    logger.info('Database connected successfully');
    
    // 启动HTTP服务器
    const server = app.listen(PORT, () => {
      logger.info(`CTMS+EDC Server v4.0 started`, {
        port: PORT,
        host: config.host,
        env: config.nodeEnv,
        apiUrl: `http://localhost:${PORT}`,
        healthUrl: `http://localhost:${PORT}/health`,
      });
      
      // 优雅关闭处理
      setupGracefulShutdown(server);
    });
    
  } catch (err) {
    logger.error('Failed to start server', err);
    process.exit(1);
  }
}

/**
 * 优雅关闭处理（21 CFR Part 11 合规）
 */
function setupGracefulShutdown(server: any): void {
  const shutdown = async (signal: string) => {
    logger.info(`Received ${signal}, starting graceful shutdown...`);
    
    // 停止接受新连接
    server.close(() => {
      logger.info('HTTP server closed');
    });
    
    try {
      // 关闭数据库连接
      await prisma.$disconnect();
      logger.info('Database disconnected');
      
      process.exit(0);
    } catch (err) {
      logger.error('Error during shutdown', err);
      process.exit(1);
    }
  };
  
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

// 未捕获异常处理
process.on('uncaughtException', (err) => {
  logger.error('Uncaught Exception', { message: err.message, stack: err.stack });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', { reason, promise });
});

// 启动服务器
startServer();
