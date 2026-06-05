import jsonwebtoken from 'jsonwebtoken';
import config from '../../config/env';

export interface JwtPayload {
  userId: string;
  username: string;
  roles: string[]; // 角色代码数组
  permissions: string[]; // 权限代码数组
  siteIds?: string[];
  projectIds?: string[];
}

/**
 * 生成 Access Token（短期，15分钟）
 */
export function generateAccessToken(payload: JwtPayload): string {
  return jsonwebtoken.sign(
    payload,
    config.jwtSecret,
    { expiresIn: config.jwtAccessExpiresIn } as jsonwebtoken.SignOptions
  );
}

/**
 * 生成 Refresh Token（长期，7天）
 */
export function generateRefreshToken(userId: string): string {
  return jsonwebtoken.sign(
    { userId, type: 'refresh' },
    config.jwtSecret,
    { expiresIn: config.jwtRefreshExpiresIn } as jsonwebtoken.SignOptions
  );
}

/**
 * 验证 Token
 */
export function verifyToken(token: string): JwtPayload {
  try {
    return jsonwebtoken.verify(token, config.jwtSecret) as JwtPayload;
  } catch (err) {
    throw new Error('Invalid or expired token');
  }
}

/**
 * 验证 Refresh Token
 */
export function verifyRefreshToken(token: string): { userId: string; type: string } {
  try {
    const payload = jsonwebtoken.verify(token, config.jwtSecret) as any;
    if (payload.type !== 'refresh') {
      throw new Error('Invalid refresh token');
    }
    return { userId: payload.userId, type: payload.type };
  } catch (err) {
    throw new Error('Invalid or expired refresh token');
  }
}
