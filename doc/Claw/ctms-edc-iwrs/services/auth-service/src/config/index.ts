// 环境配置

import dotenv from 'dotenv';

dotenv.config();

export const config = {
  // 服务器配置
  port: parseInt(process.env.PORT || '3001', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  
  // 数据库配置
  databaseUrl: process.env.DATABASE_URL || 'postgresql://ctms:ctms123456@localhost:5432/ctms_edc_iwrs_auth',
  
  // Redis 配置
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  
  // JWT 配置
  jwtSecret: process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production',
  jwtExpiration: process.env.JWT_EXPIRATION || '7d',
  jwtRefreshSecret: process.env.JWT_REFRESH_SECRET || 'your-refresh-secret-key',
  jwtRefreshExpiration: process.env.JWT_REFRESH_EXPIRATION || '30d',
  
  // 密码策略
  minPasswordLength: parseInt(process.env.MIN_PASSWORD_LENGTH || '12', 10),
  passwordResetExpiry: parseInt(process.env.PASSWORD_RESET_EXPIRY || '15', 10), // 分钟
  
  // 会话配置
  sessionMaxAge: parseInt(process.env.SESSION_MAX_AGE || '604800000', 10), // 7 天毫秒
  
  // 安全配置
  bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '12', 10),
  maxLoginAttempts: parseInt(process.env.MAX_LOGIN_ATTEMPTS || '5', 10),
  lockoutDuration: parseInt(process.env.LOCKOUT_DURATION || '900000', 10), // 15 分钟毫秒
  
  // 日志配置
  logLevel: process.env.LOG_LEVEL || 'info',
  
  // CORS 配置
  corsOrigins: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:5173'],
  
  // 速率限制
  rateLimitWindowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10), // 15 分钟
  rateLimitMaxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
};

// 类型定义
export interface Config {
  port: number;
  nodeEnv: string;
  databaseUrl: string;
  redisUrl: string;
  jwtSecret: string;
  jwtExpiration: string;
  jwtRefreshSecret: string;
  jwtRefreshExpiration: string;
  minPasswordLength: number;
  passwordResetExpiry: number;
  sessionMaxAge: number;
  bcryptRounds: number;
  maxLoginAttempts: number;
  lockoutDuration: number;
  logLevel: string;
  corsOrigins: string[];
  rateLimitWindowMs: number;
  rateLimitMaxRequests: number;
}
