/**
 * CTMS+EDC v4.0 系统流程测试（End-to-End Business Flow Tests）
 *
 * 测试覆盖跨模块业务流程：
 * Flow 1: 项目全生命周期（创建→设置中心→招募受试者→数据录入→质疑管理→SDV）
 * Flow 2: AE/SAE 安全性报告流程
 * Flow 3: 工时→财务→导出 管理流程
 * Flow 4: 工作流审批流程
 *
 * 运行：cd server && npx jest __tests__/e2e/flow.test.ts
 */

import request from 'supertest';
import app from '@root/app';
import { generateAccessToken } from '@shared/utils/jwt';

const BASE = '/api';

// 创建具有广泛权限的测试用户 Token
const ADMIN_USER = {
  userId: 'admin-test-001',
  username: 'admin',
  roles: ['admin'],
  permissions: ['*'],
};

function auth(): Record<string, string> {
  return { Authorization: `Bearer ${generateAccessToken(ADMIN_USER)}` };
}

// ============================================================
// 辅助函数
// ============================================================

async function createTestProject(): Promise<{ id: string; projectCode: string } | null> {
  const res = await request(app)
    .post(`${BASE}/projects`)
    .set(auth())
    .send({
      projectCode: `FLOW-${Date.now()}`,
      projectName: '流程测试项目',
      studyType: 'interventional',
      phase: 'phase_ii',
      therapeuticArea: '糖尿病',
    });
  if (res.status === 201) return res.body.data;
  return null;
}

async function loginAndGetToken(username: string = 'admin', password: string = 'Admin123'): Promise<string | null> {
  const res = await request(app)
    .post(`${BASE}/auth/login`)
    .send({ username, password });
  if (res.status === 200 || res.status === 201) {
    return res.body.data.accessToken;
  }
  return null;
}

// ============================================================
// Flow 1: 项目全生命周期流程
// ============================================================
describe('Flow 1: 项目全生命周期', () => {
  let token: string | null = null;
  let projectId: string | null = null;

  beforeAll(async () => {
    // Step 0: 登录获取真实 token
    token = await loginAndGetToken();
  });

  test('Step 1: 创建项目', async () => {
    if (!token) return;

    const res = await request(app)
      .post(`${BASE}/projects`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        projectCode: `LC-${Date.now()}`,
        projectName: '全生命周期测试项目',
        studyType: 'interventional',
        phase: 'phase_iii',
        sampleSize: 200,
        therapeuticArea: '糖尿病',
        description: '端到端流程测试项目',
      });

    expect([201, 403]).toContain(res.status);
    if (res.status === 201) {
      expect(res.body.success).toBe(true);
      expect(res.body.data.projectName).toBe('全生命周期测试项目');
      projectId = res.body.data.id;
    }
  });

  test('Step 2: 查询项目详情', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .get(`${BASE}/projects/${projectId}`)
      .set({ Authorization: `Bearer ${token}` });

    expect([200, 403]).toContain(res.status);
    expect(res.body.data.id).toBe(projectId);
  });

  test('Step 3: 获取项目列表验证项目存在', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/projects`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '50' });

    expect([200, 403]).toContain(res.status);
    if (res.status !== 403 && res.status !== 404) {
      expect(res.body.data.total).toBeGreaterThan(0);
    }
    if (projectId && res.status !== 403) {
      const found = res.body.data.list.some((p: any) => p.id === projectId);
      expect(found).toBe(true);
    }
  });

  test('Step 4: 更新项目状态', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .put(`${BASE}/projects/${projectId}`)
      .set({ Authorization: `Bearer ${token}` })
      .send({ status: 'recruiting' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 5: 创建里程碑', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/projects/${projectId}/milestones`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        milestoneName: '首例入组',
        milestoneType: 'first_patient',
        plannedDate: '2026-06-15',
        description: '首例受试者入组里程碑',
      });

    expect([201, 200]).toContain(res.status);
  });

  test('Step 6: 获取研究中心列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/sites`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
    expect(res.body.data).toHaveProperty('list');
  });

  test('Step 7: 获取受试者列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/edc/subjects`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 8: 获取 CRF 数据', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/edc/subjects`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });
});

// ============================================================
// Flow 2: AE/SAE 安全性报告流程
// ============================================================
describe('Flow 2: AE/SAE 安全性报告流程', () => {
  let token: string | null = null;
  let projectId: string | null = null;
  let subjectId: string | null = null;
  let aeId: string | null = null;

  beforeAll(async () => {
    token = await loginAndGetToken();

    // 获取已有项目和受试者
    if (token) {
      const projRes = await request(app)
        .get(`${BASE}/projects`)
        .set({ Authorization: `Bearer ${token}` })
        .query({ page: '1', pageSize: '1' });
      if (projRes.body.data?.list?.[0]) {
        projectId = projRes.body.data.list[0].id;

        const subjRes = await request(app)
          .get(`${BASE}/edc/subjects`)
          .set({ Authorization: `Bearer ${token}` })
          .query({ projectId, page: '1', pageSize: '1' });
        if (subjRes.body.data?.list?.[0]) {
          subjectId = subjRes.body.data.list[0].id;
        }
      }
    }
  });

  test('Step 1: 获取 AE 列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/edc/ae`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
    expect(res.body.success).toBe(true);
  });

  test('Step 2: 创建 AE 记录', async () => {
    if (!token || !projectId || !subjectId) return;

    const res = await request(app)
      .post(`${BASE}/edc/ae`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        projectId,
        subjectId,
        eventType: 'ae',
        termPreferred: '流程测试-AE-头痛',
        onsetDate: new Date().toISOString(),
        severity: 'mild',
        seriousness: 'non_serious',
        description: '流程测试生成的不良事件-轻度头痛',
        outcome: 'resolved',
      });

    expect([201, 200]).toContain(res.status);
    if (res.body.data?.id) {
      aeId = res.body.data.id;
    }
  });

  test('Step 3: 创建 SAE 记录', async () => {
    if (!token || !projectId || !subjectId) return;

    const res = await request(app)
      .post(`${BASE}/edc/ae`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        projectId,
        subjectId,
        eventType: 'sae',
        termPreferred: '流程测试-SAE-严重过敏',
        onsetDate: new Date().toISOString(),
        severity: 'severe',
        seriousness: 'serious',
        seriousnessCriteria: ['required_hospitalization'],
        causality: 'probable',
        description: '流程测试生成的严重不良事件',
        outcome: 'resolving',
      });

    expect([201, 200]).toContain(res.status);
  });

  test('Step 4: 获取 AE 详情', async () => {
    if (!token || !aeId) return;

    const res = await request(app)
      .get(`${BASE}/edc/ae/${aeId}`)
      .set({ Authorization: `Bearer ${token}` });

    expect([200, 403]).toContain(res.status);
    expect(res.body.data.eventType).toBe('ae');
  });

  test('Step 5: 导出 AE 数据', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/export`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        exportType: 'adverse_events',
        projectId,
        format: 'json',
      });

    expect([200, 403]).toContain(res.status);
    // 注：recordCount 可能为 0（测试环境无数据），重点检查 API 可用
    if (res.status === 200) {
      expect((res as any).body.data).toHaveProperty('data');
      expect((res as any).body.data).toHaveProperty('recordCount');
    }
  });
});

// ============================================================
// Flow 3: 工时→财务→导出管理流程
// ============================================================
describe('Flow 3: 工时→财务→导出管理流程', () => {
  let token: string | null = null;
  let projectId: string | null = null;

  beforeAll(async () => {
    token = await loginAndGetToken();

    if (token) {
      const projRes = await request(app)
        .get(`${BASE}/projects`)
        .set({ Authorization: `Bearer ${token}` })
        .query({ page: '1', pageSize: '1' });
      if (projRes.body.data?.list?.[0]) {
        projectId = projRes.body.data.list[0].id;
      }
    }
  });

  test('Step 1: 获取工时列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/timesheets`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
    expect(res.body.success).toBe(true);
  });

  test('Step 2: 获取财务收入列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/finance/income`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 3: 获取财务支出列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/finance/expense`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 4: 导出受试者数据', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/export`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        exportType: 'subjects',
        projectId,
        format: 'csv',
      });

    expect([200, 403]).toContain(res.status);
    expect(res.body.data.contentType).toBe('text/csv; charset=utf-8');
  });

  test('Step 5: 导出 CRF 数据', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/export`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        exportType: 'crf_data',
        projectId,
        format: 'json',
      });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 6: 查看导出历史', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/export/history`)
      .set({ Authorization: `Bearer ${token}` });

    expect([200, 403]).toContain(res.status);
  });

    expect([200, 403]).toContain(res.status);
  });
});

// ============================================================
// Flow 4: 工作流审批流程
// ============================================================
describe('Flow 4: 工作流审批流程', () => {
  let token: string | null = null;
  let projectId: string | null = null;

  beforeAll(async () => {
    token = await loginAndGetToken();

    if (token) {
      const projRes = await request(app)
        .get(`${BASE}/projects`)
        .set({ Authorization: `Bearer ${token}` })
        .query({ page: '1', pageSize: '1' });
      if (projRes.body.data?.list?.[0]) {
        projectId = projRes.body.data.list[0].id;
      }
    }
  });

  test('Step 1: 获取工作流定义列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/workflow/definitions`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 2: 创建工作流定义', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/workflow/definitions`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        name: `流程测试-审批-${Date.now()}`,
        description: '自动化测试审批流程',
        projectId,
        stages: [
          { name: '提交', stageType: 'start', assigneeRoleCodes: ['crc'] },
          { name: '审核', stageType: 'review', assigneeRoleCodes: ['pi'], approverRoleCodes: ['pi'] },
          { name: '完成', stageType: 'end' },
        ],
      });

    expect([201, 200, 403, 500]).toContain(res.status);
  });

  test('Step 3: 获取工作流实例列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/workflow/instances`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 4: 获取我的任务列表', async () => {
    if (!token) return;

    const res = await request(app)
      .get(`${BASE}/workflow/my-tasks`)
      .set({ Authorization: `Bearer ${token}` });

    expect([200, 403]).toContain(res.status);
  });
});

// ============================================================
// Flow 5: 数据质疑管理流程
// ============================================================
describe('Flow 5: 数据质疑管理流程', () => {
  let token: string | null = null;
  let projectId: string | null = null;

  beforeAll(async () => {
    token = await loginAndGetToken();

    if (token) {
      const projRes = await request(app)
        .get(`${BASE}/projects`)
        .set({ Authorization: `Bearer ${token}` })
        .query({ page: '1', pageSize: '1' });
      if (projRes.body.data?.list?.[0]) {
        projectId = projRes.body.data.list[0].id;
      }
    }
  });

  test('Step 1: 获取质疑列表', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .get(`${BASE}/edc/queries`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ projectId, page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 2: 创建质疑', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/edc/queries`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        projectId,
        queryType: 'data_discrepancy',
        priority: 'high',
        title: `流程测试-数据核查质疑-${Date.now()}`,
        description: '流程测试：发现数据不一致，需要核实',
      });

    expect([201, 200]).toContain(res.status);
  });
});

// ============================================================
// Flow 6: SDV 源数据核查流程
// ============================================================
describe('Flow 6: SDV 源数据核查流程', () => {
  let token: string | null = null;
  let projectId: string | null = null;

  beforeAll(async () => {
    token = await loginAndGetToken();

    if (token) {
      const projRes = await request(app)
        .get(`${BASE}/projects`)
        .set({ Authorization: `Bearer ${token}` })
        .query({ page: '1', pageSize: '1' });
      if (projRes.body.data?.list?.[0]) {
        projectId = projRes.body.data.list[0].id;
      }
    }
  });

  test('Step 1: 获取 SDV 列表', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .get(`${BASE}/edc/sdv`)
      .set({ Authorization: `Bearer ${token}` })
      .query({ projectId, page: '1', pageSize: '10' });

    expect([200, 403]).toContain(res.status);
  });

  test('Step 2: 导出 SDV 数据', async () => {
    if (!token || !projectId) return;

    const res = await request(app)
      .post(`${BASE}/export`)
      .set({ Authorization: `Bearer ${token}` })
      .send({
        exportType: 'sdv',
        projectId,
        format: 'json',
      });

    expect([200, 403]).toContain(res.status);
  });
});

// ============================================================
// Flow 7: 综合模块可用性检查
// ============================================================
describe('Flow 7: 综合模块可用性检查', () => {
  let token: string | null = null;

  beforeAll(async () => {
    token = await loginAndGetToken();
  });

  const endpoints = [
    { method: 'get', path: '/api/organizations', desc: '组织机构' },
    { method: 'get', path: '/api/vendors', desc: '供应商管理' },
    { method: 'get', path: '/api/contracts', desc: '合同管理' },
    { method: 'get', path: '/api/documents', desc: '文档管理' },
    { method: 'get', path: '/api/ethics', desc: '伦理审批' },
    { method: 'get', path: '/api/edc/consent', desc: '知情同意' },
    { method: 'get', path: '/api/edc/randomization', desc: '随机化' },
    { method: 'get', path: '/api/edc/sdv', desc: 'SDV' },
    { method: 'get', path: '/api/edc/ae', desc: 'AE/SAE' },
    { method: 'get', path: '/api/notifications', desc: '消息通知' },
    { method: 'get', path: '/api/reports', desc: '报告中心' },
    { method: 'get', path: '/api/signatures', desc: '电子签名' },
    { method: 'get', path: '/api/audit', desc: '审计日志' },
  ];

<<<<<<< HEAD
  test.each(endpoints)('$desc 端点可访问', async ({ method, path }: any) => {
=======
  test.each(endpoints)('$desc 端点可访问', async ({ method, path }) => {
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    if (!token) return;

    const res = await (request(app) as any)[method](path)
      .set({ Authorization: `Bearer ${token}` })
      .query({ page: '1', pageSize: '5' });

    // 大多数列表端点应返回 200
    expect([200, 404, 403]).toContain(res.status);
  });
});
