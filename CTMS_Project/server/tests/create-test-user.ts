/**
 * 创建测试用户脚本
 * 为集成测试创建 admin 用户
 */

import { PrismaClient } from '@prisma/client';
<<<<<<< HEAD
import bcrypt from 'bcryptjs';
=======
import bcrypt from 'bcrypt';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8

const prisma = new PrismaClient();

async function createTestUser() {
  console.log('🔐 创建测试用户 admin...');

  const password = 'Admin123';
  const hash = await bcrypt.hash(password, 10);

  try {
    // 创建 admin 用户
    const user = await prisma.user.upsert({
      where: { username: 'admin' },
      update: { 
        passwordHash: hash,
        status: 'active'
      },
      create: {
        username: 'admin',
        passwordHash: hash,
        displayName: '系统管理员',
        email: 'admin@ctms.com',
        status: 'active',
      }
    });

    console.log(`✅ 用户 admin 已创建/更新 (ID: ${user.id})`);
    console.log(`   用户名：admin`);
    console.log(`   密码：Admin123`);

  } catch (error) {
    console.error('❌ 创建用户失败:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

createTestUser();
