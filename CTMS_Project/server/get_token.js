const { PrismaClient } = require('@prisma/client');
const jwt = require('jsonwebtoken');

const prisma = new PrismaClient();

async function run() {
  const user = await prisma.user.findUnique({ where: { username: 'admin' }, include: { roles: { include: { role: true } } } });
  const token = jwt.sign(
    { 
      userId: user.id,
      username: user.username,
      roles: user.roles.map(r => r.role.roleCode)
    },
    process.env.JWT_SECRET || 'ctms_edc_super_secret_key_2026',
    { expiresIn: '1h' }
  );
  console.log(token);
}
run().finally(() => process.exit(0));