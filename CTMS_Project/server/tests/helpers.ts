/**
 * CTMS+EDC v4.0 测试设置与辅助工具
 */

import { generateAccessToken } from '../src/shared/utils/jwt';

// 测试用管理员 Token
export const ADMIN_USER = {
  userId: 'admin-test-id-001',
  username: 'admin',
  roles: ['admin'],
  permissions: ['*'],
};

export const TEST_USER = {
  userId: 'test-user-id-002',
  username: 'crc_user',
  roles: ['crc'],
  permissions: ['data:entry', 'query:create', 'ae:report'],
};

export function getAdminAuth(): Record<string, string> {
  return { Authorization: `Bearer ${generateAccessToken(ADMIN_USER)}` };
}

export function getUserAuth(): Record<string, string> {
  return { Authorization: `Bearer ${generateAccessToken(TEST_USER)}` };
}

export const BASE = '/api';
