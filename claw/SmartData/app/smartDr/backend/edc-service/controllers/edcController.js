const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 获取表单模板列表
const getFormTemplates = async (req, res) => {
  try {
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT ft.id, ft.name, ft.description, ft.created_at,
             u.username as created_by_name
      FROM form_templates ft
      LEFT JOIN users u ON ft.created_by = u.id
      WHERE ft.tenant_id = $1
      ORDER BY ft.created_at DESC
    `, [tenantId]);
    
    res.json({
      success: true,
      templates: result.rows
    });
  } catch (error) {
    console.error('获取表单模板错误:', error);
    res.status(500).json({
      success: false,
      message: '获取表单模板失败'
    });
  }
};

// 创建表单模板
const createFormTemplate = async (req, res) => {
  try {
    const { name, description, templateData } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!name) {
      return res.status(400).json({
        success: false,
        message: '模板名称是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO form_templates 
       (tenant_id, name, description, template_data, created_by) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id, name, description, template_data`,
      [tenantId, name, description, templateData, userId]
    );
    
    res.status(201).json({
      success: true,
      template: result.rows[0]
    });
  } catch (error) {
    console.error('创建表单模板错误:', error);
    res.status(500).json({
      success: false,
      message: '创建表单模板失败'
    });
  }
};

// 获取特定表单模板详情
const getFormTemplateDetails = async (req, res) => {
  try {
    const { id } = req.params;
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT ft.id, ft.name, ft.description, ft.template_data, ft.created_at,
             u.username as created_by_name
      FROM form_templates ft
      LEFT JOIN users u ON ft.created_by = u.id
      WHERE ft.id = $1 AND ft.tenant_id = $2
    `, [id, tenantId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '表单模板不存在'
      });
    }
    
    res.json({
      success: true,
      template: result.rows[0]
    });
  } catch (error) {
    console.error('获取表单模板详情错误:', error);
    res.status(500).json({
      success: false,
      message: '获取表单模板详情失败'
    });
  }
};

// 更新表单模板
const updateFormTemplate = async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description, templateData } = req.body;
    const { tenantId } = req.query;
    
    const result = await pool.query(
      `UPDATE form_templates 
       SET name = $1, description = $2, template_data = $3, updated_at = NOW()
       WHERE id = $4 AND tenant_id = $5
       RETURNING id, name, description, template_data`,
      [name, description, templateData, id, tenantId]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '表单模板不存在或权限不足'
      });
    }
    
    res.json({
      success: true,
      template: result.rows[0]
    });
  } catch (error) {
    console.error('更新表单模板错误:', error);
    res.status(500).json({
      success: false,
      message: '更新表单模板失败'
    });
  }
};

// 删除表单模板
const deleteFormTemplate = async (req, res) => {
  try {
    const { id } = req.params;
    const { tenantId } = req.query;
    
    const result = await pool.query(
      'DELETE FROM form_templates WHERE id = $1 AND tenant_id = $2 RETURNING id',
      [id, tenantId]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '表单模板不存在或权限不足'
      });
    }
    
    res.json({
      success: true,
      message: '表单模板删除成功'
    });
  } catch (error) {
    console.error('删除表单模板错误:', error);
    res.status(500).json({
      success: false,
      message: '删除表单模板失败'
    });
  }
};

// 提交表单数据
const submitFormData = async (req, res) => {
  try {
    const { trialId, patientId, templateId, data } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!trialId || !patientId || !templateId || !data) {
      return res.status(400).json({
        success: false,
        message: '试验ID、患者ID、模板ID和数据是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO edc_data 
       (tenant_id, trial_id, patient_id, form_template_id, data, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6) 
       RETURNING id, trial_id, patient_id, form_template_id, data, created_at`,
      [tenantId, trialId, patientId, templateId, data, userId]
    );
    
    res.status(201).json({
      success: true,
      formData: result.rows[0]
    });
  } catch (error) {
    console.error('提交表单数据错误:', error);
    res.status(500).json({
      success: false,
      message: '提交表单数据失败'
    });
  }
};

// 获取表单数据
const getFormData = async (req, res) => {
  try {
    const { patientId, templateId, tenantId } = req.query;
    
    let query = 'SELECT ed.id, ed.trial_id, ed.patient_id, ed.form_template_id, ed.data, ed.created_at FROM edc_data ed WHERE ed.tenant_id = $1';
    const params = [tenantId];
    
    if (patientId) {
      query += ' AND ed.patient_id = $2';
      params.push(patientId);
    }
    
    if (templateId) {
      query += ' AND ed.form_template_id = $3';
      params.push(templateId);
    }
    
    query += ' ORDER BY ed.created_at DESC';
    
    const result = await pool.query(query, params);
    
    res.json({
      success: true,
      formData: result.rows
    });
  } catch (error) {
    console.error('获取表单数据错误:', error);
    res.status(500).json({
      success: false,
      message: '获取表单数据失败'
    });
  }
};

// 获取CDASH字段库
const getCdashFields = async (req, res) => {
  try {
    // 这里应该是从数据库或配置文件获取CDASH字段库
    const cdashFields = [
      {
        variableName: "AESEV",
        displayLabel: "不良事件严重程度",
        domain: "AE",
        fieldType: "ENUM",
        allowedValues: ["MILD", "MODERATE", "SEVERE"],
        sdtmMapping: {
          domain: "AE",
          variable: "ASEV"
        }
      },
      {
        variableName: "LBTEST",
        displayLabel: "实验室测试名称",
        domain: "LB",
        fieldType: "STRING",
        sdtmMapping: {
          domain: "LB",
          variable: "LBTEST"
        }
      },
      {
        variableName: "DMETH",
        displayLabel: "研究药物",
        domain: "DM",
        fieldType: "ENUM",
        allowedValues: ["Drug A", "Drug B", "Placebo"],
        sdtmMapping: {
          domain: "DM",
          variable: "DMETH"
        }
      }
    ];
    
    res.json({
      success: true,
      cdashFields: cdashFields
    });
  } catch (error) {
    console.error('获取CDASH字段库错误:', error);
    res.status(500).json({
      success: false,
      message: '获取CDASH字段库失败'
    });
  }
};

module.exports = {
  getFormTemplates,
  createFormTemplate,
  getFormTemplateDetails,
  updateFormTemplate,
  deleteFormTemplate,
  submitFormData,
  getFormData,
  getCdashFields
};