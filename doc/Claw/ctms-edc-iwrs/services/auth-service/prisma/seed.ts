import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seed...');

  // 1. Create default tenant
  console.log('🏢 Creating default tenant...');
  const tenant = await prisma.tenant.upsert({
    where: { code: 'default' },
    update: {},
    create: {
      code: 'default',
      name: 'Default Organization',
      status: 'ACTIVE',
      settings: {
        locale: 'zh-CN',
        timezone: 'Asia/Shanghai',
        dateFormat: 'YYYY-MM-DD',
        timeFormat: 'HH:mm:ss',
      },
    },
  });
  console.log(`✅ Tenant created: ${tenant.name} (${tenant.id})`);

  // 2. Create default roles
  console.log('🎭 Creating default roles...');

  // Super Admin role
  const superAdminRole = await prisma.role.upsert({
    where: { tenantId_name: { tenantId: tenant.id, name: 'super_admin' } },
    update: {},
    create: {
      tenantId: tenant.id,
      name: 'super_admin',
      displayName: '超级管理员',
      description: '拥有系统全部权限的超级管理员',
      permissions: [
        'user:create',
        'user:read',
        'user:update',
        'user:delete',
        'role:create',
        'role:read',
        'role:update',
        'role:delete',
        'tenant:read',
        'tenant:update',
        'audit:read',
        'system:admin',
      ],
      status: 'ACTIVE',
    },
  });
  console.log(`✅ Role created: ${superAdminRole.displayName}`);

  // Admin role
  const adminRole = await prisma.role.upsert({
    where: { tenantId_name: { tenantId: tenant.id, name: 'admin' } },
    update: {},
    create: {
      tenantId: tenant.id,
      name: 'admin',
      displayName: '管理员',
      description: '拥有大部分系统管理权限',
      permissions: [
        'user:read',
        'user:update',
        'role:read',
        'role:update',
        'audit:read',
        'project:create',
        'project:read',
        'project:update',
        'project:delete',
        'study:create',
        'study:read',
        'study:update',
        'study:delete',
      ],
      status: 'ACTIVE',
    },
  });
  console.log(`✅ Role created: ${adminRole.displayName}`);

  // Researcher role
  const researcherRole = await prisma.role.upsert({
    where: { tenantId_name: { tenantId: tenant.id, name: 'researcher' } },
    update: {},
    create: {
      tenantId: tenant.id,
      name: 'researcher',
      displayName: '研究员',
      description: '临床试验研究员，负责数据录入和管理',
      permissions: [
        'user:read',
        'study:read',
        'study:update',
        'subject:read',
        'subject:update',
        'visit:create',
        'visit:read',
        'visit:update',
        'data:read',
        'data:update',
        'query:create',
        'query:update',
        'audit:read',
      ],
      status: 'ACTIVE',
    },
  });
  console.log(`✅ Role created: ${researcherRole.displayName}`);

  // Monitor role
  const monitorRole = await prisma.role.upsert({
    where: { tenantId_name: { tenantId: tenant.id, name: 'monitor' } },
    update: {},
    create: {
      tenantId: tenant.id,
      name: 'monitor',
      displayName: '监查员',
      description: 'CRA 监查员，负责数据核查和质量管理',
      permissions: [
        'user:read',
        'study:read',
        'subject:read',
        'visit:read',
        'data:read',
        'data:update',
        'query:create',
        'query:update',
        'audit:read',
        'discrepancy:create',
        'discrepancy:read',
        'discrepancy:update',
      ],
      status: 'ACTIVE',
    },
  });
  console.log(`✅ Role created: ${monitorRole.displayName}`);

  // Viewer role
  const viewerRole = await prisma.role.upsert({
    where: { tenantId_name: { tenantId: tenant.id, name: 'viewer' } },
    update: {},
    create: {
      tenantId: tenant.id,
      name: 'viewer',
      displayName: '观察员',
      description: '只读权限，用于查看数据和报表',
      permissions: [
        'user:read',
        'study:read',
        'subject:read',
        'visit:read',
        'data:read',
        'audit:read',
        'report:read',
      ],
      status: 'ACTIVE',
    },
  });
  console.log(`✅ Role created: ${viewerRole.displayName}`);

  // 3. Create default admin user
  console.log('👤 Creating default admin user...');
  const hashedPassword = await bcrypt.hash('Admin@123456', 12);

  const adminUser = await prisma.user.upsert({
    where: { tenantId_username: { tenantId: tenant.id, username: 'admin' } },
    update: {},
    create: {
      tenantId: tenant.id,
      username: 'admin',
      email: 'admin@ctms-platform.com',
      passwordHash: hashedPassword,
      firstName: '系统',
      lastName: '管理员',
      status: 'ACTIVE',
      lastLoginAt: new Date(),
    },
  });
  console.log(`✅ User created: ${adminUser.username} (${adminUser.email})`);

  // 4. Assign super_admin role to admin user
  console.log('🔗 Assigning roles...');
  await prisma.userRole.upsert({
    where: {
      userId_roleId: {
        userId: adminUser.id,
        roleId: superAdminRole.id,
      },
    },
    update: {},
    create: {
      userId: adminUser.id,
      roleId: superAdminRole.id,
    },
  });
  console.log(`✅ Role assigned: super_admin → ${adminUser.username}`);

  // 5. Create sample audit log entry
  console.log('📝 Creating sample audit log...');
  await prisma.auditLog.create({
    data: {
      tenantId: tenant.id,
      userId: adminUser.id,
      action: 'SYSTEM_INIT',
      entity: 'database',
      entityId: tenant.id,
      changes: {
        from: null,
        to: 'seeded',
      },
      ipAddress: '127.0.0.1',
      userAgent: 'Prisma Seed Script',
      details: 'Database initialized with default tenant, roles, and admin user',
    },
  });
  console.log('✅ Sample audit log created');

  console.log('\n✨ Database seed completed successfully!');
  console.log('\n📊 Summary:');
  console.log(`  - 1 Tenant: ${tenant.name}`);
  console.log(`  - 5 Roles: super_admin, admin, researcher, monitor, viewer`);
  console.log(`  - 1 User: admin (password: Admin@123456)`);
  console.log('\n⚠️  Please change the default password after first login!\n');
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
