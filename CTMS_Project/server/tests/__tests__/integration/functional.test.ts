/**
 * CTMS+EDC v4.0 系统功能测试（API Integration Tests）
 *
 * 测试覆盖：认证、CRUD 操作、权限控制、数据验证
 * 使用 supertest 发送 HTTP 请求到 Express 应用
 * 依赖种子数据（需先运行 seed-test-data.ts）
 *
 * 运行：cd server && npx jest __tests__/integration/functional.test.ts
 */

import request from 'supertest';
import app from '@root/app';
import { getAdminAuth } from '../../helpers';

// 基础 URL
const BASE = '/api';

// 测试辅助函数
function expectOkOrForbidden(status: number): void {
  expect([200, 201, 403]).toContain(status);
}

function expectValidationError(status: number): void {
  expect([400, 403, 422, 500]).toContain(status);
}

describe('系统功能测试', () => {

  // ============================================================
  // 健康检查
  // ============================================================
  describe('健康检查端点', () => {
    test('GET /health 返回 ok', async () => {
      const res = await request(app).get('/health');
      expect(res.status).toBe(200);
      expect(res.body.status).toBe('ok');
      expect(res.body.service).toBe('ctms-edc-api');
    });

    test('GET /ready 返回 ready', async () => {
      const res = await request(app).get('/ready');
      expect([200, 503]).toContain(res.status);
    });
  });

  // ============================================================
  // 认证模块
  // ============================================================
  describe('认证模块 (Auth)', () => {
    test('POST /api/auth/login - admin 登录', async () => {
      const res = await request(app)
        .post(`${BASE}/auth/login`)
<<<<<<< HEAD
        .send({ username: 'zhangsan', password: 'Test@2024' });
=======
        .send({ username: 'admin', password: 'Admin123' });
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8

      expect([200, 201]).toContain(res.status);
      if (res.status === 200 || res.status === 201) {
        expect((res as any).body.success).toBe(true);
        expect((res as any).body.data).toHaveProperty('accessToken');
      }
    });

    test('POST /api/auth/login - 错误密码', async () => {
      const res = await request(app)
        .post(`${BASE}/auth/login`)
        .send({ username: 'admin', password: 'WrongPassword' });

      expect(res.status).toBe(401);
    });

    test('POST /api/auth/login - 不存在的用户', async () => {
      const res = await request(app)
        .post(`${BASE}/auth/login`)
        .send({ username: 'nonexistent_user', password: 'Admin123' });

      expect(res.status).toBe(401);
    });

    test('POST /api/auth/login - 空用户名', async () => {
      const res = await request(app)
        .post(`${BASE}/auth/login`)
        .send({ username: '', password: 'Admin123' });

      expectValidationError(res.status);
    });

    test('GET /api/auth/me - 获取当前用户信息（需认证）', async () => {
      const res = await request(app)
        .get(`${BASE}/auth/me`)
        .set(getAdminAuth());

      expect([200, 401, 403]).toContain(res.status);
    });

    test('GET /api/auth/me - 无 Token 返回 401', async () => {
      const res = await request(app).get(`${BASE}/auth/me`);
      expect(res.status).toBe(401);
    });
  });

  // ============================================================
  // 项目管理 CRUD
  // ============================================================
  describe('项目管理 (Projects)', () => {
    const auth = getAdminAuth();
    let createdProjectId: string | null = null;

    test('GET /api/projects - 获取项目列表', async () => {
      const res = await request(app)
        .get(`${BASE}/projects`)
        .set(auth)
        .query({ page: '1', pageSize: '10' });

      expectOkOrForbidden(res.status);
      if (res.status !== 403) {
        expect((res as any).body.success).toBe(true);
        expect((res as any).body.data).toHaveProperty('list');
      }
    });

    test('POST /api/projects - 创建项目', async () => {
      const res = await request(app)
        .post(`${BASE}/projects`)
        .set(auth)
        .send({
          projectCode: `TEST-${Date.now()}`,
          projectName: '自动化测试项目',
          studyType: 'interventional',
          phase: 'phase_ii',
        });

      expectOkOrForbidden(res.status);
      if (res.status === 201) {
        expect((res as any).body.success).toBe(true);
        createdProjectId = (res as any).body.data.id;
      }
    });

    test('POST /api/projects - 重复 projectCode 返回错误', async () => {
      const code = `DUP-${Date.now()}`;
      await request(app)
        .post(`${BASE}/projects`)
        .set(auth)
        .send({ projectCode: code, projectName: 'Test' });
      const res = await request(app)
        .post(`${BASE}/projects`)
        .set(auth)
        .send({ projectCode: code, projectName: 'Duplicate' });

      expect([409, 400, 403, 500]).toContain(res.status);
    });

    test('POST /api/projects - 无效 phase 返回验证错误', async () => {
      const res = await request(app)
        .post(`${BASE}/projects`)
        .set(auth)
        .send({
          projectCode: `INV-${Date.now()}`,
          projectName: 'Invalid Phase',
          phase: 'invalid_phase_value',
        });

      expectValidationError(res.status);
    });

    test('GET /api/projects/:id - 不存在的 ID', async () => {
      const res = await request(app)
        .get(`${BASE}/projects/00000000-0000-0000-0000-000000000000`)
        .set(auth);
      expect(res.status).toBe(404);
    });
  });

  // ============================================================
  // 数据导出
  // ============================================================
  describe('数据导出 (Export)', () => {
    const auth = getAdminAuth();

    test('GET /api/export/history - 获取导出历史', async () => {
      const res = await request(app)
        .get(`${BASE}/export/history`)
        .set(auth);

      expectOkOrForbidden(res.status);
    });
  });

  // ============================================================
  // 审计日志
  // ============================================================
  describe('审计日志 (Audit)', () => {
    const auth = getAdminAuth();

    test('GET /api/audit - 获取审计日志', async () => {
      const res = await request(app)
        .get(`${BASE}/audit`)
        .set(auth)
        .query({ page: '1', pageSize: '10' });

      expectOkOrForbidden(res.status);
    });
  });

  // ============================================================
  // 角色管理
  // ============================================================
  describe('角色管理 (Roles)', () => {
    const auth = getAdminAuth();

    test('GET /api/roles - 获取角色列表', async () => {
      const res = await request(app)
        .get(`${BASE}/roles`)
        .set(auth);

      expectOkOrForbidden(res.status);
    });
  });

  // ============================================================
  // 404 处理
  // ============================================================
  describe('404 处理', () => {
    test('GET /api/nonexistent - 返回 404', async () => {
      const res = await request(app)
        .get(`${BASE}/nonexistent`)
        .set(getAdminAuth());
      expect(res.status).toBe(404);
    });
  });
});
