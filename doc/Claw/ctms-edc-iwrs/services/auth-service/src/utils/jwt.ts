// JWT 工具函数

import jwt from 'jsonwebtoken';
import { config } from '../config';
import { v4 as uuidv4 } from 'uuid';

export interface JwtPayload {
  userId: string;
  tenantId: string;
  username: string;
  email: string;
  roles: string[];
  iat?: number;
  exp?: number;
}

/**
 * 生成访问令牌（Access Token）
 */
export const generateAccessToken = (payload: Omit<JwtPayload, 'iat' | 'exp'>): string => {
  return jwt.sign(payload, config.jwtSecret, {
    expiresIn: config.jwtExpiration,
    issuer: 'ctms-auth-service',
    audience: 'ctms-platform',
  });
};

/**
 * 生成刷新令牌（Refresh Token）
 */
export const generateRefreshToken = (userId: string, tenantId: string): string => {
  const payload = {
    userId,
    tenantId,
    jti: uuidv4(), // JWT ID（防止重放攻击）
  };
  
  return jwt.sign(payload, config.jwtRefreshSecret, {
    expiresIn: config.jwtRefreshExpiration,
    issuer: 'ctms-auth-service',
    audience: 'ctms-refresh',
  });
};

/**
 * 验证并解析访问令牌
 */
export const verifyAccessToken = (token: string): JwtPayload => {
  try {
    const decoded = jwt.verify(token, config.jwtSecret, {
      issuer: 'ctms-auth-service',
      audience: 'ctms-platform',
    }) as JwtPayload;
    
    return decoded;
  } catch (error) {
    throw new Error('Invalid or expired access token');
  }
};

/**
 * 验证并解析刷新令牌
 */
export const verifyRefreshToken = (token: string): { userId: string; tenantId: string; jti: string } => {
  try {
    const decoded = jwt.verify(token, config.jwtRefreshSecret, {
      issuer: 'ctms-auth-service',
      audience: 'ctms-refresh',
    }) as { userId: string; tenantId: string; jti: string };
    
    return decoded;
  } catch (error) {
    throw new Error('Invalid or expired refresh token');
  }
};

/**
 * 解码令牌（不验证）
 */
export const decodeToken = (token: string): JwtPayload | null => {
  try {
    return jwt.decode(token) as JwtPayload;
  } catch (error) {
    return null;
  }
};
