const express = require('express');
const router = express.Router();
const {
  getPatients,
  createPatient,
  getPatientDetails,
  updatePatient,
  createPatientFolder,
  getPatientFolders,
  addFolderData,
  getFolderData,
  importEdcTemplate
} = require('../controllers/patientFolderController');

// 患者管理相关路由
router.get('/patients', getPatients);
router.post('/patients', createPatient);
router.get('/patients/:id', getPatientDetails);
router.put('/patients/:id', updatePatient);

// 病历夹相关路由
router.post('/folders', createPatientFolder);
router.get('/folders', getPatientFolders);

// 病历夹数据相关路由
router.post('/folder-data', addFolderData);
router.get('/folder-data', getFolderData);

// 模板导入相关路由
router.post('/import-template', importEdcTemplate);

module.exports = router;