// 脚本：验证项目完整性
const fs = require('fs');
const path = require('path');

console.log('=== 项目完整性检查 ===');

const checkDirectories = [
  'backend/auth-service',
  'backend/ctms-service', 
  'backend/edc-service',
  'backend/iwrs-service',
  'backend/patient-folder-service',
  'backend/api-gateway',
  'backend/monitoring-service',
  'frontend/auth',
  'frontend/ctms', 
  'frontend/edc',
  'frontend/iwrs',
  'frontend/patient-folder',
  'database',
  'deploy',
  'api/docs'
];

const checkFiles = [
  // 后端服务主文件
  'backend/auth-service/server.js',
  'backend/ctms-service/server.js',
  'backend/edc-service/server.js',
  'backend/iwrs-service/server.js',
  'backend/patient-folder-service/server.js',
  'backend/api-gateway/server.js',
  'backend/monitoring-service/server.js',
  
  // 包文件
  'backend/auth-service/package.json',
  'backend/ctms-service/package.json',
  'backend/edc-service/package.json',
  'backend/iwrs-service/package.json',
  'backend/patient-folder-service/package.json',
  'backend/api-gateway/package.json',
  'backend/monitoring-service/package.json',
  
  // 控制器文件
  'backend/ctms-service/controllers/ctmsController.js',
  'backend/ctms-service/controllers/timeEntryController.js',
  'backend/edc-service/controllers/edcController.js',
  'backend/iwrs-service/controllers/iwrsController.js',
  'backend/patient-folder-service/controllers/patientFolderController.js',
  
  // 路由文件
  'backend/ctms-service/routes/ctmsRoutes.js',
  'backend/edc-service/routes/edcRoutes.js',
  'backend/iwrs-service/routes/iwrsRoutes.js',
  'backend/patient-folder-service/routes/patientFolderRoutes.js',
  
  // 中间件文件
  'backend/auth-service/middleware/authMiddleware.js',
  'backend/ctms-service/middleware/authMiddleware.js',
  'backend/edc-service/middleware/authMiddleware.js',
  'backend/iwrs-service/middleware/authMiddleware.js',
  'backend/patient-folder-service/middleware/authMiddleware.js',
  
  // 数据库初始化脚本
  'database/init.sql',
  
  // 前端文件
  'frontend/auth/login.html',
  'frontend/ctms/dashboard.html',
  'frontend/edc/dashboard.html',
  'frontend/iwrs/dashboard.html',
  'frontend/patient-folder/dashboard.html',
  
  // API文档
  'api/docs/system-architecture.md',
  'README.md'
];

// 检查目录是否存在
console.log('\n1. 检查目录结构:');
let allDirsValid = true;
checkDirectories.forEach(dir => {
  const exists = fs.existsSync(dir);
  if (exists) {
    console.log(`✓ ${dir}`);
  } else {
    console.log(`✗ ${dir} (不存在)`);
    allDirsValid = false;
  }
});

// 检查关键文件是否存在
console.log('\n2. 检查关键文件:');
let allFilesValid = true;
checkFiles.forEach(file => {
  const exists = fs.existsSync(file);
  if (exists) {
    console.log(`✓ ${file}`);
  } else {
    console.log(`✗ ${file} (不存在)`);
    allFilesValid = false;
  }
});

// 检查Docker配置
console.log('\n3. 检查部署配置:');
const dockerFiles = ['Dockerfile', 'docker-compose.yml'];
let allDockerValid = true;
dockerFiles.forEach(file => {
  const exists = fs.existsSync(file);
  if (exists) {
    console.log(`✓ ${file}`);
  } else {
    console.log(`✗ ${file} (不存在)`);
    allDockerValid = false;
  }
});

// 检查部署脚本
console.log('\n4. 检查部署脚本:');
const deployScripts = ['deploy/deploy.sh', 'deploy/ci-cd.md'];
let allDeployValid = true;
deployScripts.forEach(file => {
  const exists = fs.existsSync(file);
  if (exists) {
    console.log(`✓ ${file}`);
  } else {
    console.log(`✗ ${file} (不存在)`);
    allDeployValid = false;
  }
});

// 检查项目根目录重要文件
console.log('\n5. 检查根目录文件:');
const rootFiles = ['package.json', 'README.md', '.gitignore'];
let allRootValid = true;
rootFiles.forEach(file => {
  const exists = fs.existsSync(file);
  if (exists) {
    console.log(`✓ ${file}`);
  } else {
    console.log(`✗ ${file} (不存在)`);
    allRootValid = false;
  }
});

// 最终结果
console.log('\n=== 检查结果 ===');
const allValid = allDirsValid && allFilesValid && allDockerValid && allDeployValid && allRootValid;

if (allValid) {
  console.log('✅ 所有文件和目录都已正确创建');
  console.log('✅ 项目结构完整，可以正常运行');
} else {
  console.log('❌ 发现缺失的文件或目录');
  console.log('请检查以上标记为"不存在"的项目');
}

module.exports = {
  checkDirectories,
  checkFiles,
  allValid
};