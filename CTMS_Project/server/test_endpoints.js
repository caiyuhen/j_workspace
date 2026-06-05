const axios = require('axios');

const { PrismaClient } = require('@prisma/client');
const jwt = require('jsonwebtoken');
const prisma = new PrismaClient();

async function login() {
  try {
    const user = await prisma.user.findFirst({ where: { username: 'admin' }, include: { userRoles: { include: { role: true } } } });
    if (!user) return null;
    const token = jwt.sign(
      { 
        userId: user.id,
        username: user.username,
        roles: user.userRoles.map(r => r.role.roleCode)
      },
      process.env.JWT_SECRET || 'ctms_edc_super_secret_key_2026',
      { expiresIn: '1h' }
    );
    return token;
  } catch(e) {
    console.error('Login failed:', e);
    return null;
  }
}

async function run() {
  console.log("Starting tests...");
  const token = await login();
  if (!token) {
    console.log("No token, exiting.");
    return;
  }
  
  const headers = { Authorization: `Bearer ${token}` };
  const endpoints = [
    '/api/projects',
    '/api/sites',
    '/api/monitoring/plans',
    '/api/drugs',
    '/api/documents',
    '/api/finance/income',
    '/api/timesheets',
    '/api/edc/templates',
    '/api/edc/subjects',
    '/api/edc/ae',
    '/api/edc/sdv',
    '/api/edc/randomization',
    '/api/workflow/my-tasks',
    '/api/audit',
    '/api/ethics',
    '/api/contracts',
    '/api/vendors',
  ];

  for (const ep of endpoints) {
    console.log(`Testing ${ep}...`);
    try {
      const res = await axios.get(`http://localhost:3000${ep}`, { headers });
      console.log(`  -> [OK] ${res.status}`);
    } catch(e) {
      console.error(`  -> [FAIL] ${e.response?.status} - ${JSON.stringify(e.response?.data)}`);
    }
  }
}

run().catch(console.error);