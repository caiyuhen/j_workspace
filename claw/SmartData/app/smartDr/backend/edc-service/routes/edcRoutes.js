const express = require('express');
const router = express.Router();
const {
  getFormTemplates,
  createFormTemplate,
  getFormTemplateDetails,
  updateFormTemplate,
  deleteFormTemplate,
  submitFormData,
  getFormData,
  getCdashFields
} = require('../controllers/edcController');

// 表单模板相关路由
router.get('/templates', getFormTemplates);
router.post('/templates', createFormTemplate);
router.get('/templates/:id', getFormTemplateDetails);
router.put('/templates/:id', updateFormTemplate);
router.delete('/templates/:id', deleteFormTemplate);

// 表单数据相关路由
router.post('/form-data', submitFormData);
router.get('/form-data', getFormData);

// CDASH字段相关路由
router.get('/cdash-fields', getCdashFields);

module.exports = router;