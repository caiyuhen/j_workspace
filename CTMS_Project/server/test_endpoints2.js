const axios = require('axios');
const fs = require('fs');

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
    fs.appendFileSync('test_out.txt', 'Login failed: ' + e + '\n');
    return null;
  }
}

async function run() {
  fs.writeFileSync('test_out.txt', "Starting tests...\n");
  const token = await login();
  if (!token) {
    fs.appendFileSync('test_out.txt', "No token, exiting.\n");
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
  ];

  for (const ep of endpoints) {
    fs.appendFileSync('test_out.txt', `Testing ${ep}...\n`);
    try {
      const res = await axios.get(`http://localhost:3000${ep}`, { headers });
      fs.appendFileSync('test_out.txt', `  -> [OK] ${res.status}\n`);
    } catch(e) {
      fs.appendFileSync('test_out.txt', `  -> [FAIL] ${e.response?.status} - ${JSON.stringify(e.response?.data)}\n`);
    }
  }
}

run().catch(e => fs.appendFileSync('test_out.txt', 'Error: ' + e + '\n'));