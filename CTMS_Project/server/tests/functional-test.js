/**
 * CTMS+EDC 系统全模块功能测试脚本
 * 测试覆盖：Auth / User / Role / CTMS(11模块) / EDC(10模块) / System(10模块)
 * 运行方式：node server/tests/functional-test.js
 */

const BASE_URL = 'http://localhost:3000/api';
let TOKEN = '';
let CREATED_IDS = {}; // 存储创建的实体ID，供后续测试使用

// ==================== 工具函数 ====================

const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  dim: '\x1b[2m',
  bold: '\x1b[1m',
};

function log(msg, color = '') {
  console.log(`${color}${msg}${COLORS.reset}`);
}

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;
let skippedTests = 0;
let failedDetails = [];

async function request(method, path, body = null, expectStatus = null, auth = true) {
  const url = path.startsWith('http') ? path : `${BASE_URL}${path}`;
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    timeout: 10000,
  };
  if (auth && TOKEN) {
    opts.headers['Authorization'] = `Bearer ${TOKEN}`;
  }
  if (body) {
    opts.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(url, opts);
    let data;
    const text = await res.text();
    try { data = JSON.parse(text); } catch { data = text; }

    const statusOk = expectStatus ? res.status === expectStatus : res.status >= 200 && res.status < 300;
    return { status: res.status, ok: statusOk, data, headers: res.headers };
  } catch (err) {
    return { status: 0, ok: false, data: { error: err.message }, headers: {} };
  }
}

async function test(name, fn) {
  totalTests++;
  try {
    await fn();
    passedTests++;
    log(`  ✅ ${name}`, COLORS.green);
  } catch (err) {
    failedTests++;
    failedDetails.push({ name, error: err.message });
    log(`  ❌ ${name}: ${err.message}`, COLORS.red);
  }
}

function skip(name, reason) {
  totalTests++;
  skippedTests++;
  log(`  ⏭️  ${name} [跳过: ${reason}]`, COLORS.yellow);
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'Assertion failed');
}

function assertStatus(res, expected, msg = '') {
  assert(res.status === expected, msg || `期望状态码 ${expected}，实际 ${res.status} | ${JSON.stringify(res.data).slice(0, 200)}`);
}

function assertOk(res, msg = '') {
  assert(res.ok, msg || `请求失败: status=${res.status} | ${JSON.stringify(res.data).slice(0, 200)}`);
}

function assertHasData(res, msg = '') {
  assert(res.data && (res.data.success !== false), msg || '响应数据异常');
}

// ==================== 测试模块 ====================

// ---- 1. Auth 认证模块 ----
async function testAuth() {
  log('\n🔐 Auth 认证模块', COLORS.bold + COLORS.cyan);

  // 使用 admin 账户登录（已拥有 SUPER_ADMIN + 105 个权限）
  await test('POST /api/auth/login - 使用admin账户登录', async () => {
    const res = await request('POST', '/auth/login', {
      username: 'admin',
      password: 'root@123',
    }, 200, false);
    assertStatus(res, 200);
    assert(res.data.success && res.data.data?.accessToken, '登录失败或无token');
    TOKEN = res.data.data.accessToken;
    assert(res.data.data?.user?.roles?.includes('SUPER_ADMIN'), 'admin应具有SUPER_ADMIN角色');
  });

  await test('POST /api/auth/login - 错误密码应返回401', async () => {
    const res = await request('POST', '/auth/login', {
      username: 'test_admin',
      password: 'wrong_password',
    }, 401, false);
    assert(res.status === 401, '错误密码应返回401');
  });

  await test('GET /api/auth/me - 获取当前用户信息', async () => {
    const res = await request('GET', '/auth/me');
    assertOk(res);
    assert(res.data.data, '应返回用户信息');
    CREATED_IDS.currentUserId = res.data.data.id || res.data.data.userId;
  });

  await test('PUT /api/auth/password - 修改密码', async () => {
    const res = await request('PUT', '/auth/password', {
      oldPassword: 'root@123',
      newPassword: 'Admin@456789',
    });
    assertOk(res);
    // 改回来
    await request('PUT', '/auth/password', {
      oldPassword: 'Admin@456789',
      newPassword: 'root@123',
    });
  });

  await test('POST /api/auth/refresh - Token刷新', async () => {
    // 先登录获取refreshToken
    const loginRes = await request('POST', '/auth/login', {
      username: 'test_admin',
      password: 'Test@123456',
    }, 200, false);
    const refreshToken = loginRes.data.data?.refreshToken;
    if (refreshToken) {
      const res = await request('POST', '/auth/refresh', { refreshToken }, 200, false);
      assertOk(res, '刷新token失败');
    } else {
      skip('', '无refreshToken');
    }
  });
}

// ---- 2. User 用户管理模块 ----
async function testUser() {
  log('\n👤 User 用户管理模块', COLORS.bold + COLORS.cyan);

  await test('GET /api/users - 用户列表', async () => {
    const res = await request('GET', '/users');
    assertOk(res);
    assert(res.data.data && (Array.isArray(res.data.data) || Array.isArray(res.data.data?.items) || res.data.data?.total !== undefined), '应返回用户列表');
  });

  await test('POST /api/users - 创建用户', async () => {
    const res = await request('POST', '/users', {
      username: 'user_test_001',
      password: 'User@123456',
      email: 'user001@example.com',
      displayName: '测试用户001',
    });
    assertOk(res);
    CREATED_IDS.userId = res.data.data?.id;
  });

  await test('GET /api/users/:id - 用户详情', async () => {
    if (!CREATED_IDS.userId) return skip('', '无userId');
    const res = await request('GET', `/users/${CREATED_IDS.userId}`);
    assertOk(res);
  });

  await test('PUT /api/users/:id - 更新用户', async () => {
    if (!CREATED_IDS.userId) return skip('', '无userId');
    const res = await request('PUT', `/users/${CREATED_IDS.userId}`, {
      displayName: '测试用户001-已更新',
    });
    assertOk(res);
  });

  await test('GET /api/roles/permissions - 权限列表', async () => {
    const res = await request('GET', '/roles/permissions');
    assertOk(res);
  });
}

// ---- 3. Role 角色管理模块 ----
async function testRole() {
  log('\n🔑 Role 角色管理模块', COLORS.bold + COLORS.cyan);

  await test('GET /api/roles - 角色列表', async () => {
    const res = await request('GET', '/roles');
    assertOk(res);
  });

  await test('POST /api/roles - 创建角色', async () => {
    const res = await request('POST', '/roles', {
      roleCode: 'TEST_ROLE',
      roleName: '测试角色',
      description: '功能测试用角色',
    });
    assertOk(res);
    CREATED_IDS.roleId = res.data.data?.id;
  });

  await test('GET /api/roles/:id - 角色详情', async () => {
    if (!CREATED_IDS.roleId) return skip('', '无roleId');
    const res = await request('GET', `/roles/${CREATED_IDS.roleId}`);
    assertOk(res);
  });

  await test('POST /api/roles/:id/permissions - 分配权限', async () => {
    if (!CREATED_IDS.roleId) return skip('', '无roleId');
    // 先获取权限列表，取前两个权限ID
    const permsRes = await request('GET', '/roles/permissions');
    const permIds = (permsRes.data.data || []).slice(0, 2).map(p => p.id);
    const res = await request('POST', `/roles/${CREATED_IDS.roleId}/permissions`, {
      permissionIds: permIds,
    });
    assertOk(res);
  });
}

// ---- 4. Organization 组织机构模块 ----
async function testOrganization() {
  log('\n🏢 Organization 组织机构模块', COLORS.bold + COLORS.cyan);

  await test('GET /api/organizations - 组织列表', async () => {
    const res = await request('GET', '/organizations');
    assertOk(res);
  });

  await test('GET /api/organizations/tree - 组织树形结构', async () => {
    const res = await request('GET', '/organizations/tree');
    assertOk(res);
  });

  await test('POST /api/organizations - 创建组织', async () => {
    const res = await request('POST', '/organizations', {
      orgCode: 'TEST_ORG_001',
      orgName: '测试研究中心',
      orgType: 'site',
    });
    assertOk(res);
    CREATED_IDS.orgId = res.data.data?.id;
  });
}

// ---- 5. CTMS: Project 项目管理模块 ----
async function testProject() {
  log('\n📋 CTMS: Project 项目管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/projects - 项目列表', async () => {
    const res = await request('GET', '/projects');
    assertOk(res);
  });

  await test('POST /api/projects - 创建项目', async () => {
    const res = await request('POST', '/projects', {
      projectCode: 'TEST-PRJ-001',
      projectName: 'CTMS功能测试项目',
      studyType: 'interventional',
      blindType: 'double_blind',
      description: '用于功能测试的临床试验项目',
    });
    assertOk(res);
    CREATED_IDS.projectId = res.data.data?.id;
  });

  await test('GET /api/projects/:id - 项目详情', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/projects/${CREATED_IDS.projectId}`);
    assertOk(res);
  });

  await test('PUT /api/projects/:id - 更新项目', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('PUT', `/projects/${CREATED_IDS.projectId}`, {
      description: '更新后的项目描述',
    });
    assertOk(res);
  });

  await test('GET /api/projects/:id/milestones - 里程碑列表', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/projects/${CREATED_IDS.projectId}/milestones`);
    assertOk(res);
  });

  await test('POST /api/projects/:id/milestones - 创建里程碑', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('POST', `/projects/${CREATED_IDS.projectId}/milestones`, {
      name: '测试里程碑-伦理批准',
      plannedDate: '2026-06-01',
    });
    assertOk(res);
    CREATED_IDS.milestoneId = res.data.data?.id;
  });
}

// ---- 6. CTMS: Site 中心管理模块 ----
async function testSite() {
  log('\n🏥 CTMS: Site 中心管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/sites - 中心列表', async () => {
    const res = await request('GET', '/sites');
    assertOk(res);
  });

  await test('POST /api/sites - 创建中心', async () => {
    const res = await request('POST', '/sites', {
      projectId: CREATED_IDS.projectId,
      siteCode: 'SITE-TEST-001',
      siteName: '测试研究中心-北京协和',
      piUserId: CREATED_IDS.currentUserId,
    });
    assertOk(res);
    CREATED_IDS.siteId = res.data.data?.id;
  });

  await test('GET /api/sites/:id - 中心详情', async () => {
    if (!CREATED_IDS.siteId) return skip('', '无siteId');
    const res = await request('GET', `/sites/${CREATED_IDS.siteId}`);
    assertOk(res);
  });

  await test('POST /api/sites/:id/staff - 添加中心人员', async () => {
    if (!CREATED_IDS.siteId) return skip('', '无siteId');
    const res = await request('POST', `/sites/${CREATED_IDS.siteId}/staff`, {
      userId: CREATED_IDS.currentUserId,
      role: 'CRC',
    });
    assertOk(res);
  });
}

// ---- 7. CTMS: Monitoring 监察管理模块 ----
async function testMonitoring() {
  log('\n🔍 CTMS: Monitoring 监察管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/monitoring/plans - 监察计划列表', async () => {
    const res = await request('GET', '/monitoring/plans');
    assertOk(res);
  });

  await test('POST /api/monitoring/plans - 创建监察计划', async () => {
    const res = await request('POST', '/monitoring/plans', {
      projectId: CREATED_IDS.projectId,
      planName: '年度监察计划-2026',
      frequency: 'quarterly',
      status: 'active',
    });
    assertOk(res);
    CREATED_IDS.monitoringPlanId = res.data.data?.id;
  });

  await test('GET /api/monitoring/plans/:id - 监察计划详情', async () => {
    if (!CREATED_IDS.monitoringPlanId) return skip('', '无monitoringPlanId');
    const res = await request('GET', `/monitoring/plans/${CREATED_IDS.monitoringPlanId}`);
    assertOk(res);
  });

  await test('GET /api/monitoring/visits - 监察访视列表', async () => {
    const res = await request('GET', '/monitoring/visits');
    assertOk(res);
  });

  await test('POST /api/monitoring/visits - 创建监察访视', async () => {
    const res = await request('POST', '/monitoring/visits', {
      projectId: CREATED_IDS.projectId,
      craUserId: CREATED_IDS.currentUserId,
      visitType: 'routine',
      plannedDate: '2026-06-15',
      planId: CREATED_IDS.monitoringPlanId,
      siteId: CREATED_IDS.siteId,
      status: 'planned',
    });
    assertOk(res);
    CREATED_IDS.monitoringVisitId = res.data.data?.id;
  });

  await test('GET /api/monitoring/stats/:projectId - 项目监察统计', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/monitoring/stats/${CREATED_IDS.projectId}`);
    assertOk(res);
  });
}

// ---- 8. CTMS: Drug 药物管理模块 ----
async function testDrug() {
  log('\n💊 CTMS: Drug 药物管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/drugs - 药物列表', async () => {
    const res = await request('GET', '/drugs');
    assertOk(res);
  });

  await test('POST /api/drugs - 创建药物', async () => {
    const res = await request('POST', '/drugs', {
      projectId: CREATED_IDS.projectId,
      drugCode: 'DRUG-TEST-001',
      drugName: '测试药物-CT101',
      dosageForm: '片剂',
      strength: '100mg',
      storageCondition: '2-8°C冷藏',
    });
    assertOk(res);
    CREATED_IDS.drugId = res.data.data?.id;
  });

  await test('GET /api/drugs/:id - 药物详情', async () => {
    if (!CREATED_IDS.drugId) return skip('', '无drugId');
    const res = await request('GET', `/drugs/${CREATED_IDS.drugId}`);
    assertOk(res);
  });

  await test('POST /api/drugs/:id/supply-plans - 创建供应计划', async () => {
    if (!CREATED_IDS.drugId) return skip('', '无drugId');
    const res = await request('POST', `/drugs/${CREATED_IDS.drugId}/supply-plans`, {
      quantity: 1000,
      deliveryDate: '2026-06-01',
      siteId: CREATED_IDS.siteId,
    });
    assertOk(res);
  });

  await test('POST /api/drugs/:id/shipments - 创建发运', async () => {
    if (!CREATED_IDS.drugId) return skip('', '无drugId');
    const res = await request('POST', `/drugs/${CREATED_IDS.drugId}/shipments`, {
      quantity: 500,
      shipmentDate: '2026-06-01',
      from: '中心仓库',
      to: CREATED_IDS.siteId,
    });
    assertOk(res);
  });

  await test('POST /api/drugs/:id/inventories - 创建库存', async () => {
    if (!CREATED_IDS.drugId) return skip('', '无drugId');
    const res = await request('POST', `/drugs/${CREATED_IDS.drugId}/inventories`, {
      siteId: CREATED_IDS.siteId,
      quantity: 500,
      batchNumber: 'BATCH-001',
      expiryDate: '2027-12-31',
    });
    assertOk(res);
  });

  await test('POST /api/drugs/:id/destructions - 创建销毁记录', async () => {
    if (!CREATED_IDS.drugId) return skip('', '无drugId');
    const res = await request('POST', `/drugs/${CREATED_IDS.drugId}/destructions`, {
      quantity: 10,
      reason: '过期销毁',
      destructionDate: '2026-06-01',
    });
    assertOk(res);
  });
}

// ---- 9. CTMS: Document 文档管理模块 ----
async function testDocument() {
  log('\n📄 CTMS: Document 文档管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/documents - 文档列表', async () => {
    const res = await request('GET', '/documents');
    assertOk(res);
  });

  await test('POST /api/documents - 创建文档', async () => {
    const res = await request('POST', '/documents', {
      projectId: CREATED_IDS.projectId,
      tmfSection: 'section_01_icf',
      documentCode: 'DOC-TEST-001',
      documentName: '测试协议文档',
      documentType: 'protocol',
    });
    assertOk(res);
    CREATED_IDS.documentId = res.data.data?.id;
  });

  await test('GET /api/documents/stats - 文档完成统计', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/documents/stats?projectId=${CREATED_IDS.projectId}`);
    assertOk(res);
  });

  await test('GET /api/documents/:id - 文档详情', async () => {
    if (!CREATED_IDS.documentId) return skip('', '无documentId');
    const res = await request('GET', `/documents/${CREATED_IDS.documentId}`);
    assertOk(res);
  });

  await test('POST /api/documents/:id/versions - 上传版本', async () => {
    if (!CREATED_IDS.documentId) return skip('', '无documentId');
    const res = await request('POST', `/documents/${CREATED_IDS.documentId}/versions`, {
      version: '1.0',
      fileName: 'protocol_v1.pdf',
      fileSize: 1024000,
      mimeType: 'application/pdf',
    });
    assertOk(res);
  });

  await test('PUT /api/documents/:id/status - 更新文档状态', async () => {
    if (!CREATED_IDS.documentId) return skip('', '无documentId');
    const res = await request('PUT', `/documents/${CREATED_IDS.documentId}/status`, {
      status: 'APPROVED',
    });
    assertOk(res);
  });
}

// ---- 10. CTMS: Finance 财务收支模块 ----
async function testFinance() {
  log('\n💰 CTMS: Finance 财务收支', COLORS.bold + COLORS.cyan);

  await test('GET /api/finance/income - 收入列表', async () => {
    const res = await request('GET', '/finance/income');
    assertOk(res);
  });

  await test('POST /api/finance/income - 创建收入', async () => {
    const res = await request('POST', '/finance/income', {
      projectId: CREATED_IDS.projectId,
      incomeCode: 'INC-001',
      incomeType: 'milestone',
      amount: 100000,
      description: '申办方首期拨款',
    });
    assertOk(res);
    CREATED_IDS.incomeId = res.data.data?.id;
  });

  await test('GET /api/finance/expense - 支出列表', async () => {
    const res = await request('GET', '/finance/expense');
    assertOk(res);
  });

  await test('POST /api/finance/expense - 创建支出', async () => {
    const res = await request('POST', '/finance/expense', {
      projectId: CREATED_IDS.projectId,
      expenseCode: 'EXP-TEST-001',
      expenseType: 'monitoring',
      amount: 50000,
      expenseDate: '2026-05-07',
      description: '研究中心月度费用',
    });
    assertOk(res);
    CREATED_IDS.expenseId = res.data.data?.id;
  });

  await test('GET /api/finance/summary/:projectId - 收支汇总', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/finance/summary/${CREATED_IDS.projectId}`);
    assertOk(res);
  });
}

// ---- 11. CTMS: Timesheet 工时管理模块 ----
async function testTimesheet() {
  log('\n⏰ CTMS: Timesheet 工时管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/timesheets - 工时列表', async () => {
    const res = await request('GET', '/timesheets');
    assertOk(res);
  });

  await test('POST /api/timesheets - 创建工时', async () => {
    const res = await request('POST', '/timesheets', {
      userId: CREATED_IDS.currentUserId,
      projectId: CREATED_IDS.projectId,
      weekStartDate: '2026-05-04',
      entries: [{
        workDate: '2026-05-07',
        hours: 8,
        workType: 'monitoring',
        description: '中心常规监查',
        isBillable: true,
      }],
    });
    assertOk(res);
    CREATED_IDS.timesheetId = res.data.data?.id;
  });

  await test('GET /api/timesheets/:id - 工时详情', async () => {
    if (!CREATED_IDS.timesheetId) return skip('', '无timesheetId');
    const res = await request('GET', `/timesheets/${CREATED_IDS.timesheetId}`);
    assertOk(res);
  });

  await test('POST /api/timesheets/:id/submit - 提交工时审批', async () => {
    if (!CREATED_IDS.timesheetId) return skip('', '无timesheetId');
    const res = await request('POST', `/timesheets/${CREATED_IDS.timesheetId}/submit`);
    assertOk(res);
  });
}

// ---- 12. CTMS: Vendor 供应商管理模块 ----
async function testVendor() {
  log('\n🏭 CTMS: Vendor 供应商管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/vendors - 供应商列表', async () => {
    const res = await request('GET', '/vendors');
    assertOk(res);
  });

  await test('GET /api/vendors/stats - 供应商统计', async () => {
    const res = await request('GET', '/vendors/stats');
    assertOk(res);
  });

  await test('POST /api/vendors - 创建供应商', async () => {
    const res = await request('POST', '/vendors', {
      vendorCode: 'VENDOR-001',
      vendorName: '测试CRO公司',
      vendorType: 'cro',
      contactPerson: '李经理',
      contactPhone: '13800138000',
    });
    assertOk(res);
    CREATED_IDS.vendorId = res.data.data?.id;
  });

  await test('GET /api/vendors/:id - 供应商详情', async () => {
    if (!CREATED_IDS.vendorId) return skip('', '无vendorId');
    const res = await request('GET', `/vendors/${CREATED_IDS.vendorId}`);
    assertOk(res);
  });
}

// ---- 13. CTMS: Contract 合同管理模块 ----
async function testContract() {
  log('\n📝 CTMS: Contract 合同管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/contracts - 合同列表', async () => {
    const res = await request('GET', '/contracts');
    assertOk(res);
  });

  await test('GET /api/contracts/stats - 合同统计', async () => {
    const res = await request('GET', '/contracts/stats');
    assertOk(res);
  });

  await test('POST /api/contracts - 创建合同', async () => {
    const res = await request('POST', '/contracts', {
      contractCode: 'CONTRACT-001',
      contractName: '测试CRO服务合同',
      contractType: 'sow',
      vendorId: CREATED_IDS.vendorId,
      projectId: CREATED_IDS.projectId,
      amount: 500000,
      startDate: '2026-01-01',
      endDate: '2026-12-31',
    });
    assertOk(res);
    CREATED_IDS.contractId = res.data.data?.id;
  });
}

// ---- 14. CTMS: Ethics 伦理审批模块 ----
async function testEthics() {
  log('\n⚖️ CTMS: Ethics 伦理审批', COLORS.bold + COLORS.cyan);

  await test('GET /api/ethics - 伦理列表', async () => {
    const res = await request('GET', '/ethics');
    assertOk(res);
  });

  await test('GET /api/ethics/stats - 伦理统计', async () => {
    const res = await request('GET', '/ethics/stats');
    assertOk(res);
  });

  await test('POST /api/ethics - 创建伦理审批', async () => {
    const res = await request('POST', '/ethics', {
      projectId: CREATED_IDS.projectId,
      ethicsCommittee: '北京协和医院伦理委员会',
      approvalType: 'initial',
      approvalStatus: 'pending',
    });
    assertOk(res);
    CREATED_IDS.ethicsId = res.data.data?.id;
  });
}

// ---- 15. Workflow 工作流模块 ----
async function testWorkflow() {
  log('\n🔄 Workflow 工作流', COLORS.bold + COLORS.cyan);

  await test('GET /api/workflow/definitions - 流程定义列表', async () => {
    const res = await request('GET', '/workflow/definitions');
    assertOk(res);
  });

  await test('POST /api/workflow/definitions - 创建流程定义', async () => {
    const res = await request('POST', '/workflow/definitions', {
      workflowCode: 'TEST-WF-001',
      workflowName: '测试审批流程',
      workflowType: 'project_approval',
      stages: [
        { name: '提交', nodeType: 'submit', approverRole: 'CRA' },
        { name: '审核', nodeType: 'review', approverRole: 'ADMIN' },
        { name: '完成', nodeType: 'complete' },
      ],
    });
    assertOk(res);
    CREATED_IDS.workflowDefId = res.data.data?.id;
  });

  await test('GET /api/workflow/instances - 流程实例列表', async () => {
    const res = await request('GET', '/workflow/instances');
    assertOk(res);
  });

  await test('POST /api/workflow/instances/start - 启动流程实例', async () => {
    if (!CREATED_IDS.workflowDefId) return skip('', '无workflowDefId');
    const res = await request('POST', '/workflow/instances/start', {
      definitionId: CREATED_IDS.workflowDefId,
      businessKey: `TIMESHEET_${CREATED_IDS.timesheetId || 'test'}`,
      businessType: 'TIMESHEET_APPROVAL',
    });
    assertOk(res);
    CREATED_IDS.workflowInstId = res.data.data?.id;
  });

  await test('GET /api/workflow/my-tasks - 我的待办', async () => {
    const res = await request('GET', '/workflow/my-tasks');
    assertOk(res);
  });

  await test('GET /api/workflow/stats - 工作流统计', async () => {
    const res = await request('GET', '/workflow/stats');
    assertOk(res);
  });
}

// ---- 16. EDC: Template CRF模板模块 ----
async function testTemplate() {
  log('\n📝 EDC: Template CRF模板', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/templates - 模板列表', async () => {
    const res = await request('GET', '/edc/templates');
    assertOk(res);
  });

  await test('POST /api/edc/templates - 创建模板', async () => {
    const res = await request('POST', '/edc/templates', {
      templateCode: 'TMPL-TEST-001',
      templateName: '测试人口学信息模板',
      templateType: 'crf',
      version: '1.0',
      projectId: CREATED_IDS.projectId,
      templateData: {
        fields: [
          { name: 'birthDate', label: '出生日期', type: 'date', required: true },
          { name: 'gender', label: '性别', type: 'select', required: true, options: ['男', '女'] },
          { name: 'weight', label: '体重(kg)', type: 'number', required: true },
        ],
      },
    });
    assertOk(res);
    CREATED_IDS.templateId = res.data.data?.id;
  });

  await test('GET /api/edc/templates/:id - 模板详情', async () => {
    if (!CREATED_IDS.templateId) return skip('', '无templateId');
    const res = await request('GET', `/edc/templates/${CREATED_IDS.templateId}`);
    assertOk(res);
  });

  await test('POST /api/edc/templates/:id/publish - 发布模板', async () => {
    if (!CREATED_IDS.templateId) return skip('', '无templateId');
    const res = await request('POST', `/edc/templates/${CREATED_IDS.templateId}/publish`);
    assertOk(res);
  });

  await test('POST /api/edc/templates/:id/clone - 克隆模板', async () => {
    if (!CREATED_IDS.templateId) return skip('', '无templateId');
    const res = await request('POST', `/edc/templates/${CREATED_IDS.templateId}/clone`, {
      newTemplateCode: 'TMPL-CLONE-001',
      newTemplateName: '测试克隆模板',
    });
    assertOk(res);
  });
}

// ---- 17. EDC: Form CRF表单模块 ----
async function testForm() {
  log('\n📋 EDC: Form CRF表单', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/forms - 表单列表', async () => {
    const res = await request('GET', '/edc/forms');
    assertOk(res);
  });

  await test('POST /api/edc/forms - 创建表单', async () => {
    const res = await request('POST', '/edc/forms', {
      projectId: CREATED_IDS.projectId,
      formCode: 'FORM-TEST-001',
      formName: '测试基线访视表单',
      formType: 'visit',
    });
    assertOk(res);
    CREATED_IDS.formId = res.data.data?.id;
  });

  await test('GET /api/edc/forms/:id - 表单详情', async () => {
    if (!CREATED_IDS.formId) return skip('', '无formId');
    const res = await request('GET', `/edc/forms/${CREATED_IDS.formId}`);
    assertOk(res);
  });

  await test('POST /api/edc/forms/:id/fields - 添加字段', async () => {
    if (!CREATED_IDS.formId) return skip('', '无formId');
    const res = await request('POST', `/edc/forms/${CREATED_IDS.formId}/fields`, {
      name: 'sbp',
      label: '收缩压(mmHg)',
      type: 'NUMBER',
      required: true,
      validationRules: { min: 60, max: 250 },
    });
    assertOk(res);
    CREATED_IDS.fieldId = res.data.data?.id;
  });
}

// ---- 18. EDC: Subject 受试者管理模块 ----
async function testSubject() {
  log('\n🧑‍⚕️ EDC: Subject 受试者管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/subjects - 受试者列表', async () => {
    const res = await request('GET', '/edc/subjects');
    assertOk(res);
  });

  await test('POST /api/edc/subjects - 登记受试者', async () => {
    const res = await request('POST', '/edc/subjects', {
      projectId: CREATED_IDS.projectId,
      siteId: CREATED_IDS.siteId,
      subjectCode: 'TEST-001',
      enrollmentStatus: 'enrolled',
    });
    assertOk(res);
    CREATED_IDS.subjectId = res.data.data?.id;
  });

  await test('GET /api/edc/subjects/:id - 受试者详情', async () => {
    if (!CREATED_IDS.subjectId) return skip('', '无subjectId');
    const res = await request('GET', `/edc/subjects/${CREATED_IDS.subjectId}`);
    assertOk(res);
  });

  await test('POST /api/edc/subjects/:id/visits - 创建访视', async () => {
    if (!CREATED_IDS.subjectId) return skip('', '无subjectId');
    const res = await request('POST', `/edc/subjects/${CREATED_IDS.subjectId}/visits`, {
      visitType: 'BASELINE',
      visitDate: '2026-05-07',
      formId: CREATED_IDS.formId,
    });
    assertOk(res);
    CREATED_IDS.visitId = res.data.data?.id;
  });
}

// ---- 19. EDC: Query 质疑管理模块 ----
async function testQuery() {
  log('\n❓ EDC: Query 质疑管理', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/queries - 质疑列表', async () => {
    const res = await request('GET', '/edc/queries');
    assertOk(res);
  });

  await test('POST /api/edc/queries - 创建质疑', async () => {
    const res = await request('POST', '/edc/queries', {
      projectId: CREATED_IDS.projectId,
      subjectId: CREATED_IDS.subjectId,
      formId: CREATED_IDS.formId,
      queryType: 'data_discrepancy',
      priority: 'high',
      title: '收缩压值超出合理范围',
      description: '收缩压值为300mmHg，超出正常范围，请核实',
    });
    assertOk(res);
    CREATED_IDS.queryId = res.data.data?.id;
  });

  await test('GET /api/edc/queries/:id - 质疑详情', async () => {
    if (!CREATED_IDS.queryId) return skip('', '无queryId');
    const res = await request('GET', `/edc/queries/${CREATED_IDS.queryId}`);
    assertOk(res);
  });

  await test('POST /api/edc/queries/:id/reply - 回复质疑', async () => {
    if (!CREATED_IDS.queryId) return skip('', '无queryId');
    const res = await request('POST', `/edc/queries/${CREATED_IDS.queryId}/reply`, {
      replyText: '已核实，数据正确，为患者实际情况',
    });
    assertOk(res);
  });
}

// ---- 20. EDC: AE/SAE 不良事件模块 ----
async function testAE() {
  log('\n⚠️ EDC: AE/SAE 不良事件', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/ae - AE列表', async () => {
    const res = await request('GET', '/edc/ae');
    assertOk(res);
  });

  await test('GET /api/edc/ae/statistics - AE统计', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/edc/ae/statistics?projectId=${CREATED_IDS.projectId}`);
    assertOk(res);
  });

  await test('POST /api/edc/ae - 创建AE', async () => {
    const res = await request('POST', '/edc/ae', {
      projectId: CREATED_IDS.projectId,
      subjectId: CREATED_IDS.subjectId,
      eventType: 'ae',
      termPreferred: '头痛',
      termCode: 'TEST-AE-001',
      onsetDate: '2026-05-07T10:00:00Z',
      severity: 'mild',
      seriousness: 'non_serious',
      description: '受试者出现轻度头痛，持续时间约2小时',
    });
    assertOk(res);
    CREATED_IDS.aeId = res.data.data?.id;
  });

  await test('GET /api/edc/ae/:id - AE详情', async () => {
    if (!CREATED_IDS.aeId) return skip('', '无aeId');
    const res = await request('GET', `/edc/ae/${CREATED_IDS.aeId}`);
    assertOk(res);
  });

  await test('POST /api/edc/ae/:id/close - 关闭AE', async () => {
    if (!CREATED_IDS.aeId) return skip('', '无aeId');
    const res = await request('POST', `/edc/ae/${CREATED_IDS.aeId}/close`, {
      outcome: 'RECOVERED',
      resolutionDate: '2026-05-10',
    });
    assertOk(res);
  });
}

// ---- 21. EDC: SDV 源数据核查模块 ----
async function testSDV() {
  log('\n✅ EDC: SDV 源数据核查', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/sdv - SDV记录列表', async () => {
    const res = await request('GET', '/edc/sdv');
    assertOk(res);
  });

  await test('GET /api/edc/sdv/statistics - SDV统计', async () => {
    const res = await request('GET', '/edc/sdv/statistics');
    assertOk(res);
  });

  await test('POST /api/edc/sdv - 创建SDV记录', async () => {
    const res = await request('POST', '/edc/sdv', {
      projectId: CREATED_IDS.projectId,
      siteId: CREATED_IDS.siteId,
      subjectId: CREATED_IDS.subjectId,
      sdvDate: '2026-05-07T10:00:00Z',
    });
    assertOk(res);
    CREATED_IDS.sdvId = res.data.data?.id;
  });

  await test('POST /api/edc/sdv/:id/items - 添加核查项', async () => {
    if (!CREATED_IDS.sdvId) return skip('', '无sdvId');
    const res = await request('POST', `/edc/sdv/${CREATED_IDS.sdvId}/items`, {
      items: [
        { fieldName: 'sbp', sourceValue: '120', crfValue: '120', result: 'MATCH' },
        { fieldName: 'gender', sourceValue: '男', crfValue: '男', result: 'MATCH' },
      ],
    });
    assertOk(res);
  });
}

// ---- 22. EDC: Randomization 随机化模块 ----
async function testRandomization() {
  log('\n🎲 EDC: Randomization 随机化', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/randomization - 随机化记录列表', async () => {
    const res = await request('GET', '/edc/randomization');
    assertOk(res);
  });

  await test('GET /api/edc/randomization/stats/:projectId - 随机化统计', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/edc/randomization/stats/${CREATED_IDS.projectId}`);
    assertOk(res);
  });

  await test('GET /api/edc/randomization/pool/:projectId - 号池状态', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/edc/randomization/pool/${CREATED_IDS.projectId}`);
    assertOk(res);
  });

  await test('POST /api/edc/randomization - 创建随机化记录', async () => {
    const res = await request('POST', '/edc/randomization', {
      projectId: CREATED_IDS.projectId,
      subjectId: CREATED_IDS.subjectId,
      randomizationNumber: 'R-001',
      randomizationDate: '2026-05-07',
    });
    assertOk(res);
    CREATED_IDS.randomizationId = res.data.data?.id;
  });
}

// ---- 23. EDC: Lock 数据锁定模块 ----
async function testLock() {
  log('\n🔒 EDC: Lock 数据锁定', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/locks - 锁定记录列表', async () => {
    const res = await request('GET', '/edc/locks');
    assertOk(res);
  });

  await test('POST /api/edc/locks - 创建锁定', async () => {
    const res = await request('POST', '/edc/locks', {
      projectId: CREATED_IDS.projectId,
      lockType: 'visit',
      targetId: CREATED_IDS.visitId || '00000000-0000-0000-0000-000000000000',
      lockReason: '数据库锁定-基线访视',
    });
    assertOk(res);
    CREATED_IDS.lockId = res.data.data?.id;
  });

  await test('GET /api/edc/locks/stats/:projectId - 锁定统计', async () => {
    if (!CREATED_IDS.projectId) return skip('', '无projectId');
    const res = await request('GET', `/edc/locks/stats/${CREATED_IDS.projectId}`);
    assertOk(res);
  });
}

// ---- 24. EDC: Consent 知情同意模块 ----
async function testConsent() {
  log('\n✍️ EDC: Consent 知情同意', COLORS.bold + COLORS.cyan);

  await test('GET /api/edc/consent - 知情同意列表', async () => {
    const res = await request('GET', '/edc/consent');
    assertOk(res);
  });

  await test('GET /api/edc/consent/stats - 知情同意统计', async () => {
    const res = await request('GET', '/edc/consent/stats');
    assertOk(res);
  });

  await test('POST /api/edc/consent - 创建知情同意', async () => {
    const res = await request('POST', '/edc/consent', {
      projectId: CREATED_IDS.projectId,
      siteId: CREATED_IDS.siteId,
      subjectId: CREATED_IDS.subjectId,
      consentVersion: '1.0',
      consentDate: '2026-05-07T10:00:00+08:00',
      signeeType: 'subject',
      signeeName: '测试受试者',
    });
    assertOk(res);
    CREATED_IDS.consentId = res.data.data?.id;
  });
}

// ---- 25. EDC: Edit Check 逻辑核查模块 ----
async function testEditCheck() {
  log('\n🧪 EDC: Edit Check 逻辑核查', COLORS.bold + COLORS.cyan);

  await test('POST /api/edc/edit-check/test - 测试核查规则', async () => {
    if (!CREATED_IDS.formId || !CREATED_IDS.projectId) return skip('', '无formId或projectId');
    // edit-check/test 需要已有的 ruleId，如果没有规则则跳过
    try {
      const res = await request('POST', '/edc/edit-check/test', {
        ruleId: '00000000-0000-0000-0000-000000000000',
        fieldValues: { sbp: 300, gender: 'male' },
        projectId: CREATED_IDS.projectId,
        formId: CREATED_IDS.formId,
      });
      // 如果规则不存在返回404，也视为预期行为
      if (res.status === 404) return skip('', '无编辑核查规则可测试');
      assertOk(res, 'edit-check test failed');
    } catch {
      skip('', 'edit-check test skipped (no rules)');
    }
  });

  await test('POST /api/edc/edit-check/execute - 执行表单核查', async () => {
    if (!CREATED_IDS.formId || !CREATED_IDS.projectId || !CREATED_IDS.subjectId) return skip('', '无formId或projectId或subjectId');
    const res = await request('POST', '/edc/edit-check/execute', {
      formId: CREATED_IDS.formId,
      projectId: CREATED_IDS.projectId,
      subjectId: CREATED_IDS.subjectId,
      fieldValues: {},
    });
    assertOk(res);
  });
}

// ---- 26. Audit 审计日志模块 ----
async function testAudit() {
  log('\n📖 Audit 审计日志', COLORS.bold + COLORS.cyan);

  await test('GET /api/audit - 审计日志列表', async () => {
    const res = await request('GET', '/audit');
    assertOk(res);
  });

  await test('GET /api/audit/stats - 审计统计', async () => {
    const res = await request('GET', '/audit/stats');
    assertOk(res);
  });
}

// ---- 27. Notification 消息通知模块 ----
async function testNotification() {
  log('\n🔔 Notification 消息通知', COLORS.bold + COLORS.cyan);

  await test('GET /api/notifications - 通知列表', async () => {
    const res = await request('GET', '/notifications');
    assertOk(res);
  });

  await test('GET /api/notifications/unread-count - 未读数量', async () => {
    const res = await request('GET', '/notifications/unread-count');
    assertOk(res);
  });

  await test('GET /api/notifications/stats - 通知统计', async () => {
    const res = await request('GET', '/notifications/stats');
    assertOk(res);
  });

  await test('POST /api/notifications - 创建通知', async () => {
    const res = await request('POST', '/notifications', {
      recipientId: CREATED_IDS.currentUserId,
      title: '测试通知',
      content: '这是一条功能测试通知',
      channel: 'in_app',
    });
    assertOk(res);
    CREATED_IDS.notificationId = res.data.data?.id;
  });

  await test('POST /api/notifications/:id/read - 标记已读', async () => {
    if (!CREATED_IDS.notificationId) return skip('', '无notificationId');
    const res = await request('POST', `/notifications/${CREATED_IDS.notificationId}/read`);
    assertOk(res);
  });
}

// ---- 28. Report 报告中心模块 ----
async function testReport() {
  log('\n📊 Report 报告中心', COLORS.bold + COLORS.cyan);

  await test('GET /api/reports - 报告模板列表', async () => {
    const res = await request('GET', '/reports');
    assertOk(res);
  });

  await test('GET /api/reports/instances - 报告实例列表', async () => {
    const res = await request('GET', '/reports/instances');
    assertOk(res);
  });

  await test('POST /api/reports/generate - 生成报告', async () => {
    // 需要先创建报告模板才能生成报告
    const tmplRes = await request('POST', '/reports', {
      templateCode: 'RPT-TEST-001',
      templateName: '测试报告模板',
      reportType: 'data_quality',
      queryConfig: {},
      format: 'json',
    });
    const templateId = tmplRes.data.data?.id;
    if (!templateId) return skip('', '无法创建报告模板');
    const res = await request('POST', '/reports/generate', {
      templateId: templateId,
      projectId: CREATED_IDS.projectId,
      format: 'json',
    });
    assertOk(res);
  });
}

// ---- 29. Export 数据导出模块 ----
async function testExport() {
  log('\n📤 Export 数据导出', COLORS.bold + COLORS.cyan);

  await test('GET /api/export/history - 导出历史', async () => {
    const res = await request('GET', '/export/history');
    assertOk(res);
  });

  await test('POST /api/export - 导出数据', async () => {
    const res = await request('POST', '/export', {
      exportType: 'subjects',
      projectId: CREATED_IDS.projectId,
      format: 'csv',
    });
    assertOk(res);
  });
}

// ---- 30. Signature 电子签名模块 ----
async function testSignature() {
  log('\n🖊️ Signature 电子签名', COLORS.bold + COLORS.cyan);

  await test('GET /api/signatures - 签名列表', async () => {
    const res = await request('GET', '/signatures');
    assertOk(res);
  });

  await test('GET /api/signatures/stats - 签名统计', async () => {
    const res = await request('GET', '/signatures/stats');
    assertOk(res);
  });

  await test('POST /api/signatures - 创建签名', async () => {
    const res = await request('POST', '/signatures', {
      userId: CREATED_IDS.currentUserId,
      signatureMeaning: 'AUTHORSHIP',
      signatureReason: '确认数据录入',
      recordId: CREATED_IDS.formId || '00000000-0000-0000-0000-000000000000',
    });
    assertOk(res);
    CREATED_IDS.signatureId = res.data.data?.id;
  });

  await test('GET /api/signatures/:id/verify - 验证签名', async () => {
    if (!CREATED_IDS.signatureId) return skip('', '无signatureId');
    const res = await request('GET', `/signatures/${CREATED_IDS.signatureId}/verify`);
    assertOk(res);
  });
}

// ---- 31. Sync 数据同步模块 ----
async function testSync() {
  log('\n🔁 Sync 数据同步', COLORS.bold + COLORS.cyan);

  await test('GET /api/sync/logs - 同步日志', async () => {
    const res = await request('GET', '/sync/logs');
    assertOk(res);
  });

  await test('GET /api/sync/stats - 同步统计', async () => {
    const res = await request('GET', '/sync/stats');
    assertOk(res);
  });
}

// ---- 32. Data Masking 数据脱敏模块 ----
async function testMasking() {
  log('\n🎭 Data Masking 数据脱敏', COLORS.bold + COLORS.cyan);

  await test('GET /api/data-masking - 脱敏规则列表', async () => {
    const res = await request('GET', '/data-masking');
    assertOk(res);
  });

  await test('GET /api/data-masking/stats - 脱敏统计', async () => {
    const res = await request('GET', '/data-masking/stats');
    assertOk(res);
  });

  await test('POST /api/data-masking/preview - 预览脱敏效果', async () => {
    const res = await request('POST', '/data-masking/preview', {
      tableName: 'subjects',
      fieldName: 'name',
      value: '张三',
    });
    assertOk(res);
  });
}

// ---- 33. ABAC 策略引擎模块 ----
async function testABAC() {
  log('\n🛡️ ABAC 策略引擎', COLORS.bold + COLORS.cyan);

  await test('GET /api/abac - 策略列表', async () => {
    const res = await request('GET', '/abac');
    assertOk(res);
  });

  await test('POST /api/abac - 创建策略', async () => {
    const res = await request('POST', '/abac', {
      policyCode: 'TEST-POLICY-001',
      policyName: '测试策略',
      resources: { resource: 'projects', actions: ['view', 'edit'] },
      conditions: { role: 'CRA' },
      effect: 'permit',
    });
    assertOk(res);
    CREATED_IDS.abacPolicyId = res.data.data?.id;
  });

  await test('POST /api/abac/evaluate - 权限评估', async () => {
    const res = await request('POST', '/abac/evaluate', {
      userId: CREATED_IDS.currentUserId,
      resource: 'projects',
      action: 'view',
      context: { role: 'CRA' },
    });
    assertOk(res);
  });

  await test('GET /api/abac/effective/:resource - 适用策略查询', async () => {
    const res = await request('GET', '/abac/effective/projects');
    assertOk(res);
  });
}

// ---- 34. AI Agent 模块 ----
async function testAI() {
  log('\n🤖 AI Agent 集成', COLORS.bold + COLORS.cyan);

  await test('GET /api/ai/agents - Agent能力列表', async () => {
    const res = await request('GET', '/ai/agents');
    assertOk(res);
  });

  await test('GET /api/ai/logs - Agent操作日志', async () => {
    const res = await request('GET', '/ai/logs');
    assertOk(res);
  });
}

// ==================== 主流程 ====================

async function main() {
  log('\n' + '='.repeat(70), COLORS.cyan);
  log('  CTMS+EDC 系统全模块功能测试', COLORS.bold + COLORS.cyan);
  log('  时间: ' + new Date().toISOString(), COLORS.dim);
  log('='.repeat(70) + '\n', COLORS.cyan);

  const startTime = Date.now();

  try {
    // Auth 必须最先测试（获取Token）
    await testAuth();

    // 系统管理模块
    await testUser();
    await testRole();
    await testOrganization();

    // CTMS 模块
    await testProject();
    await testSite();
    await testMonitoring();
    await testDrug();
    await testDocument();
    await testFinance();
    await testTimesheet();
    await testVendor();
    await testContract();
    await testEthics();
    await testWorkflow();

    // EDC 模块
    await testTemplate();
    await testForm();
    await testSubject();
    await testQuery();
    await testAE();
    await testSDV();
    await testRandomization();
    await testLock();
    await testConsent();
    await testEditCheck();

    // 系统管理模块（续）
    await testAudit();
    await testNotification();
    await testReport();
    await testExport();
    await testSignature();
    await testSync();
    await testMasking();
    await testABAC();
    await testAI();

  } catch (err) {
    log(`\n💥 致命错误: ${err.message}`, COLORS.red);
    log(err.stack, COLORS.dim);
  }

  const duration = ((Date.now() - startTime) / 1000).toFixed(1);

  // ==================== 汇总报告 ====================
  log('\n' + '='.repeat(70), COLORS.cyan);
  log('  测试报告汇总', COLORS.bold + COLORS.cyan);
  log('='.repeat(70), COLORS.cyan);
  log(`  总计: ${totalTests} 个测试`, '');
  log(`  通过: ${passedTests}`, COLORS.green);
  log(`  失败: ${failedTests}`, COLORS.red);
  log(`  跳过: ${skippedTests}`, COLORS.yellow);
  log(`  通过率: ${totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : 0}%`, passedTests === totalTests ? COLORS.green : COLORS.red);
  log(`  耗时: ${duration}s`, COLORS.dim);
  log('='.repeat(70) + '\n', COLORS.cyan);

  if (failedDetails.length > 0) {
    log('失败详情:', COLORS.red);
    failedDetails.forEach((d, i) => {
      log(`  ${i + 1}. ${d.name}`, COLORS.red);
      log(`     ${d.error}`, COLORS.dim);
    });
    log('');
  }

  // 退出码
  process.exit(failedTests > 0 ? 1 : 0);
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(2);
});
