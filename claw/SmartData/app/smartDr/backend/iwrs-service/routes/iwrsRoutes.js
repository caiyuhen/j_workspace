const express = require('express');
const router = express.Router();
const {
  getRandomizationConfig,
  createRandomizationConfig,
  getPatientRandomization,
  randomizePatient,
  getDrugInventory,
  addDrugInventory,
  getBlindingRequests,
  createBlindingRequest
} = require('../controllers/iwrsController');

// 随机化配置相关路由
router.get('/randomization-config', getRandomizationConfig);
router.post('/randomization-config', createRandomizationConfig);

// 患者随机化相关路由
router.get('/patient-randomization', getPatientRandomization);
router.post('/patient-randomization', randomizePatient);

// 药物库存相关路由
router.get('/drug-inventory', getDrugInventory);
router.post('/drug-inventory', addDrugInventory);

// 破盲申请相关路由
router.get('/blinding-requests', getBlindingRequests);
router.post('/blinding-requests', createBlindingRequest);

module.exports = router;