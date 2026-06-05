// 快速插入测试用户
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function seedUser() {
  const hash = await bcrypt.hash('Admin123', 10);
  
  await prisma.user.upsert({
    where: { username: 'admin' },
    update: { passwordHash: hash },
    create: {
      username: 'admin',
      passwordHash: hash,
      displayName: '系统管理员',
      email: 'admin@ctms.com',
      status: 'active',
      userRoles: {
        create: {
          role: {
            create: {
              roleCode: 'admin',
              roleName: '系统管理员',
              rolePermissions: {
                create: {
                  permission: {
                    create: {
                      permissionCode: '*',
                      permissionName: '所有权限'
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  });

  console.log('✅ 测试用户 admin 已创建');
  await prisma.$disconnect();
}

seedUser();
