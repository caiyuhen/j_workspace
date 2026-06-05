import { PrismaClient, User, Role, Permission } from '@prisma/client';
import { hashPassword } from '../src/shared/utils/hash';
import logger from '../src/shared/utils/logger';

const prisma = new PrismaClient();

async function main(): Promise<void> {
  console.log('🌱 Starting seed...');

  // ========== 1. 创建9大核心角色 ==========
  const roles = [
    { roleCode: 'SPONSOR', roleName: '申办方' },
    { roleCode: 'PI', roleName: '主要研究者' },
    { roleCode: 'SUB_I', roleName: '次要研究者' },
    { roleCode: 'PM', roleName: '项目经理' },
    { roleCode: 'CRA', roleName: '临床监查员' },
    { roleCode: 'CRC', roleName: '临床协调员' },
    { roleCode: 'MM', roleName: '医学监查员' },
    { roleCode: 'DM', roleName: '数据管理员' },
    { roleCode: 'SUPER_ADMIN', roleName: '超级管理员' },
  ];

  const roleMap = new Map<string, Role>();
  for (const r of roles) {
    const existing = await prisma.role.findUnique({ where: { roleCode: r.roleCode } });
    if (existing) {
      roleMap.set(r.roleCode, existing);
      console.log(`   ✓ Role exists: ${r.roleCode}`);
    } else {
      const created = await prisma.role.create({
        data: { roleCode: r.roleCode, roleName: r.roleName, isSystemRole: true },
      });
      roleMap.set(r.roleCode, created);
      console.log(`   ✓ Created role: ${r.roleCode}`);
    }
  }

  // ========== 2. 创建权限项 ==========
  // 2a. 原始大写权限（保持向后兼容）
  const permissions = [
    // 系统级权限
    { code: 'SYS_USER_VIEW', name: '查看用户', type: 'system', action: 'view' },
    { code: 'SYS_USER_MANAGE', name: '管理用户', type: 'system', action: 'manage' },
    { code: 'SYS_ROLE_MANAGE', name: '管理角色', type: 'system', action: 'manage' },
    { code: 'SYS_AUDIT_VIEW', name: '查看审计日志', type: 'system', action: 'view' },
    { code: 'SYS_CONFIG', name: '系统配置', type: 'system', action: 'manage' },
    // 项目级权限
    { code: 'PRJ_VIEW', name: '查看项目', type: 'project', action: 'view' },
    { code: 'PRJ_EDIT', name: '编辑项目', type: 'project', action: 'edit' },
    { code: 'PRJ_CREATE', name: '创建项目', type: 'project', action: 'create' },
    { code: 'PRJ_DELETE', name: '删除项目', type: 'project', action: 'delete' },
    { code: 'PRJ_MILESTONE_MANAGE', name: '管理里程碑', type: 'project', action: 'edit' },
    { code: 'PRJ_BUDGET_VIEW', name: '查看预算', type: 'project', action: 'view' },
    { code: 'PRJ_BUDGET_MANAGE', name: '管理预算', type: 'project', action: 'edit' },
    { code: 'PRJ_FINANCIAL_VIEW', name: '查看财务', type: 'project', action: 'view' },
    { code: 'PRJ_FINANCIAL_MANAGE', name: '管理财务', type: 'project', action: 'edit' },
    // 中心级权限
    { code: 'SITE_VIEW', name: '查看中心', type: 'site', action: 'view' },
    { code: 'SITE_EDIT', name: '编辑中心', type: 'site', action: 'edit' },
    { code: 'SITE_SUBJECT_VIEW', name: '查看受试者', type: 'site', action: 'view' },
    { code: 'SITE_SUBJECT_EDIT', name: '编辑受试者', type: 'site', action: 'edit' },
    { code: 'SITE_VISIT_VIEW', name: '查看访视', type: 'site', action: 'view' },
    { code: 'SITE_VISIT_EDIT', name: '编辑访视', type: 'site', action: 'edit' },
    // 数据级权限
    { code: 'DATA_VIEW_OWN', name: '查看本人数据', type: 'data', action: 'view' },
    { code: 'DATA_VIEW_SITE', name: '查看本中心数据', type: 'data', action: 'view' },
    { code: 'DATA_VIEW_PROJECT', name: '查看本项目数据', type: 'data', action: 'view' },
    { code: 'DATA_VIEW_ALL', name: '查看全部数据', type: 'data', action: 'view' },
    { code: 'DATA_EDIT_OWN', name: '编辑本人数据', type: 'data', action: 'edit' },
    { code: 'DATA_EDIT_SITE', name: '编辑本中心数据', type: 'data', action: 'edit' },
    { code: 'DATA_EDIT_ALL', name: '编辑全部数据', type: 'data', action: 'edit' },
    { code: 'DATA_DELETE', name: '删除数据', type: 'data', action: 'delete' },
    { code: 'DATA_EXPORT', name: '导出数据', type: 'data', action: 'export' },
    { code: 'DATA_LOCK', name: '锁定数据', type: 'data', action: 'lock' },
    { code: 'DATA_ESIG', name: '电子签名', type: 'data', action: 'esig' },
  ];

  // 2b. 路由使用的冒号风格权限代码（与requirePermission中间件对应）
  const routePermissions = [
    // 项目管理
    { code: 'project:create', name: '创建项目', type: 'project', action: 'create' },
    { code: 'project:update', name: '更新项目', type: 'project', action: 'update' },
    { code: 'project:delete', name: '删除项目', type: 'project', action: 'delete' },
    { code: 'project:milestone:manage', name: '管理里程碑', type: 'project', action: 'edit' },
    // 中心管理
    { code: 'site:create', name: '创建中心', type: 'site', action: 'create' },
    { code: 'site:update', name: '更新中心', type: 'site', action: 'update' },
    { code: 'site:delete', name: '删除中心', type: 'site', action: 'delete' },
    { code: 'site:staff:manage', name: '管理人员', type: 'site', action: 'manage' },
    // 工时管理
    { code: 'timesheet:create', name: '创建工时', type: 'timesheet', action: 'create' },
    { code: 'timesheet:submit', name: '提交工时', type: 'timesheet', action: 'submit' },
    { code: 'timesheet:approve', name: '审批工时', type: 'timesheet', action: 'approve' },
    // 财务管理
    { code: 'finance:income:create', name: '创建收入', type: 'finance', action: 'create' },
    { code: 'finance:income:update', name: '更新收入', type: 'finance', action: 'update' },
    { code: 'finance:income:delete', name: '删除收入', type: 'finance', action: 'delete' },
    { code: 'finance:expense:create', name: '创建支出', type: 'finance', action: 'create' },
    { code: 'finance:expense:update', name: '更新支出', type: 'finance', action: 'update' },
    { code: 'finance:expense:delete', name: '删除支出', type: 'finance', action: 'delete' },
    { code: 'finance:view', name: '查看财务', type: 'finance', action: 'view' },
    // 药物管理
    { code: 'ctms:drug:create', name: '创建药物', type: 'drug', action: 'create' },
    { code: 'ctms:drug:update', name: '更新药物', type: 'drug', action: 'update' },
    { code: 'ctms:drug:supply', name: '供应计划', type: 'drug', action: 'supply' },
    { code: 'ctms:drug:ship', name: '发运管理', type: 'drug', action: 'ship' },
    { code: 'ctms:drug:receive', name: '接收药物', type: 'drug', action: 'receive' },
    { code: 'ctms:drug:inventory', name: '库存管理', type: 'drug', action: 'inventory' },
    { code: 'ctms:drug:destruction', name: '销毁管理', type: 'drug', action: 'destruction' },
    // 文档管理
    { code: 'ctms:document:create', name: '创建文档', type: 'document', action: 'create' },
    { code: 'ctms:document:update', name: '更新文档', type: 'document', action: 'update' },
    { code: 'ctms:document:delete', name: '删除文档', type: 'document', action: 'delete' },
    { code: 'ctms:document:upload', name: '上传版本', type: 'document', action: 'upload' },
    { code: 'ctms:document:approve', name: '审批文档', type: 'document', action: 'approve' },
    // 供应商管理
    { code: 'vendor:manage', name: '供应商管理', type: 'vendor', action: 'manage' },
    // 合同管理
    { code: 'contract:manage', name: '合同管理', type: 'contract', action: 'manage' },
    // 伦理审批
    { code: 'ethics:manage', name: '伦理审批', type: 'ethics', action: 'manage' },
    // 工作流
    { code: 'workflow:definition:create', name: '创建流程定义', type: 'workflow', action: 'create' },
    { code: 'workflow:definition:update', name: '更新流程定义', type: 'workflow', action: 'update' },
    { code: 'workflow:instance:start', name: '启动流程', type: 'workflow', action: 'start' },
    { code: 'workflow:task:process', name: '处理任务', type: 'workflow', action: 'process' },
    { code: 'workflow:instance:cancel', name: '取消流程', type: 'workflow', action: 'cancel' },
    { code: 'workflow:admin', name: '工作流管理', type: 'workflow', action: 'admin' },
    // EDC 模板
    { code: 'edc:template:create', name: '创建模板', type: 'edc', action: 'create' },
    { code: 'edc:template:update', name: '更新模板', type: 'edc', action: 'update' },
    { code: 'edc:template:publish', name: '发布模板', type: 'edc', action: 'publish' },
    // EDC 表单
    { code: 'edc:form:create', name: '创建表单', type: 'edc', action: 'create' },
    { code: 'edc:form:update', name: '更新表单', type: 'edc', action: 'update' },
    { code: 'edc:form:delete', name: '删除表单', type: 'edc', action: 'delete' },
    { code: 'edc:form:design', name: '设计表单', type: 'edc', action: 'design' },
    { code: 'edc:form:publish', name: '发布表单', type: 'edc', action: 'publish' },
    // EDC 受试者
    { code: 'edc:subject:create', name: '登记受试者', type: 'edc', action: 'create' },
    { code: 'edc:subject:update', name: '更新受试者', type: 'edc', action: 'update' },
    { code: 'edc:visit:create', name: '创建访视', type: 'edc', action: 'create' },
    // EDC 质疑
    { code: 'edc:query:create', name: '创建质疑', type: 'edc', action: 'create' },
    { code: 'edc:query:reply', name: '回复质疑', type: 'edc', action: 'reply' },
    { code: 'edc:query:reassign', name: '重新分配质疑', type: 'edc', action: 'reassign' },
    // EDC AE/SAE
    { code: 'edc:ae:create', name: '创建AE', type: 'edc', action: 'create' },
    { code: 'edc:ae:update', name: '更新AE', type: 'edc', action: 'update' },
    { code: 'edc:ae:close', name: '关闭AE', type: 'edc', action: 'close' },
    { code: 'edc:ae:sae_report', name: 'SAE报告', type: 'edc', action: 'report' },
    { code: 'edc:ae:sae_review', name: 'SAE审核', type: 'edc', action: 'review' },
    { code: 'edc:ae:sae_submit', name: 'SAE提交', type: 'edc', action: 'submit' },
    // EDC SDV
    { code: 'edc:sdv:create', name: '创建SDV', type: 'edc', action: 'create' },
    { code: 'edc:sdv:update', name: '更新SDV', type: 'edc', action: 'update' },
    { code: 'edc:sdv:execute', name: '执行SDV', type: 'edc', action: 'execute' },
    { code: 'edc:sdv:complete', name: '完成SDV', type: 'edc', action: 'complete' },
    // EDC 知情同意
    { code: 'edc:consent:manage', name: '知情同意管理', type: 'edc', action: 'manage' },
    // EDC 逻辑核查
    { code: 'edc:edit_check:execute', name: '执行逻辑核查', type: 'edc', action: 'execute' },
    // 组织机构
    { code: 'org:manage', name: '组织机构管理', type: 'organization', action: 'manage' },
    // 报告
    { code: 'report:generate', name: '生成报告', type: 'report', action: 'generate' },
    { code: 'report:manage', name: '报告管理', type: 'report', action: 'manage' },
    // 导出
    { code: 'data:export', name: '数据导出', type: 'data', action: 'export' },
    // 同步
    { code: 'sync:manage', name: '数据同步', type: 'sync', action: 'manage' },
    // 脱敏
    { code: 'sys:config', name: '系统配置', type: 'system', action: 'config' },
    // AI
    { code: 'ai:chat', name: 'AI对话', type: 'ai', action: 'chat' },
    { code: 'ai:batch', name: 'AI批量处理', type: 'ai', action: 'batch' },
    { code: 'ai:analyze', name: 'AI数据分析', type: 'ai', action: 'analyze' },
  ];

  const allPermissions = [...permissions, ...routePermissions];

  const permMap = new Map<string, Permission>();
  for (const p of allPermissions) {
    const existing = await prisma.permission.findUnique({ where: { permissionCode: p.code } });
    if (existing) {
      permMap.set(p.code, existing);
    } else {
      const created = await prisma.permission.create({
        data: {
          permissionCode: p.code,
          permissionName: p.name,
          permissionType: p.type,
          resourceType: '*',
          actionType: p.action,
          isSystemPermission: true,
        },
      });
      permMap.set(p.code, created);
      console.log(`   ✓ Created permission: ${p.code}`);
    }
  }

  // ========== 3. 分配权限给角色 ==========
  // SUPER_ADMIN 拥有所有权限
  const superAdmin = roleMap.get('SUPER_ADMIN')!;
  for (const p of permMap.values()) {
    await prisma.rolePermission.createMany({
      data: [{ roleId: superAdmin.id, permissionId: p.id, resourceScope: 'all' }],
      skipDuplicates: true,
    });
  }
  console.log('   ✓ Assigned all permissions to SUPER_ADMIN');

  // PM 拥有项目/中心管理权限
  const pm = roleMap.get('PM')!;
  const pmPerms = ['PRJ_VIEW', 'PRJ_EDIT', 'PRJ_CREATE', 'PRJ_DELETE', 'SITE_VIEW', 'SYS_USER_VIEW'];
  for (const code of pmPerms) {
    const p = permMap.get(code)!;
    await prisma.rolePermission.createMany({
      data: [{ roleId: pm.id, permissionId: p.id, resourceScope: 'project' }],
      skipDuplicates: true,
    });
  }
  console.log('   ✓ Assigned permissions to PM');

  // 创建管理员用户
  const passwordHash = await hashPassword('root@123');
  let admin: User;

  const existingAdmin = await prisma.user.findUnique({ where: { username: 'admin' } });
  if (existingAdmin) {
    admin = await prisma.user.update({
      where: { username: 'admin' },
      data: { passwordHash },
    });
    console.log('   ✓ Admin user already exists, password updated');
  } else {
    admin = await prisma.user.create({
      data: {
        username: 'admin',
        email: 'admin@ctms-edc.com',
        passwordHash,
        displayName: '系统管理员',
        title: '系统管理员',
        department: 'IT部',
        organization: 'CTMS+EDC系统',
        status: 'active',
      },
    });
    console.log('   ✓ Created admin user (admin/root@123)');
  }

  // 分配 SUPER_ADMIN 角色给管理员
  await prisma.userRole.createMany({
    data: [{ userId: admin.id, roleId: superAdmin.id }],
    skipDuplicates: true,
  });
  console.log('   ✓ Assigned SUPER_ADMIN role to admin');

  // 创建演示项目
  const existingProject = await prisma.project.findFirst();
  if (!existingProject) {
    const project = await prisma.project.create({
      data: {
        projectCode: 'PRJ-2026-001',
        projectName: '高血压药物临床试验',
        description: '一项评估新型降压药疗效的多中心随机对照试验',
        studyType: 'RCT',
        therapeuticArea: 'Cardiology',
        indication: '原发性高血压',
        blindType: 'double',
        sampleSize: 500,
        startDate: new Date('2026-06-01'),
        endDate: new Date('2028-12-31'),
        totalBudget: 5000000,
        currency: 'CNY',
        status: 'active',
        createdBy: admin.id,
      },
    });
    console.log(`   ✓ Created demo project: ${project.projectName}`);
  }

  console.log('✅ Seed completed successfully!');
  console.log('   Login: admin / password: root@123');
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
