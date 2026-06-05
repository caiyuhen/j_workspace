import winston from 'winston';
import path from 'path';
import config from '../../config/env';

const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'ISO' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
    return `${timestamp} [${level}] ${message} ${metaStr}`;
  })
);

const logger = winston.createLogger({
  level: config.logLevel,
  format: logFormat,
  defaultMeta: { service: 'ctms-edc-server' },
  transports: [
    new winston.transports.File({
      filename: path.join(__dirname, '../../logs/error.log'),
      level: 'error',
      maxsize: 10485760, // 10MB
      maxFiles: 5,
    }),
    new winston.transports.File({
      filename: path.join(__dirname, '../../logs/combined.log'),
      maxsize: 10485760,
      maxFiles: 5,
    }),
  ],
});

// 开发环境增加控制台输出
if (config.nodeEnv === 'development') {
  logger.add(
    new winston.transports.Console({
      format: consoleFormat,
    })
  );
}

export default logger;

// 结构化日志辅助函数（21 CFR Part 11 合规）
export function auditLog(params: {
  userId?: string;
  sessionId?: string;
  ipAddress?: string;
  eventType: string;
  tableName?: string;
  recordId?: string;
  action: string;
  oldValues?: any;
  newValues?: any;
  message: string;
}) {
  logger.info('AUDIT', {
    audit: true,
    ...params,
    timestamp: new Date().toISOString(),
  });
}
