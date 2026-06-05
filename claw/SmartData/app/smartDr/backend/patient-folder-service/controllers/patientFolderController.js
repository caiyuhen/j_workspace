const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 获取患者列表
const getPatients = async (req, res) => {
  try {
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT p.id, p.patient_id, p.first_name, p.last_name, p.date_of_birth, p.gender,
             p.created_at, p.updated_at
      FROM patients p
      WHERE p.tenant_id = $1
      ORDER BY p.created_at DESC
    `, [tenantId]);
    
    res.json({
      success: true,
      patients: result.rows
    });
  } catch (error) {
    console.error('获取患者列表错误:', error);
    res.status(500).json({
      success: false,
      message: '获取患者列表失败'
    });
  }
};

// 创建患者
const createPatient = async (req, res) => {
  try {
    const { patientId, firstName, lastName, dateOfBirth, gender, contactInfo } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!patientId || !firstName || !lastName) {
      return res.status(400).json({
        success: false,
        message: '患者ID、姓名是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO patients 
       (tenant_id, patient_id, first_name, last_name, date_of_birth, gender, contact_info, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
       RETURNING id, patient_id, first_name, last_name, date_of_birth, gender, contact_info`,
      [tenantId, patientId, firstName, lastName, dateOfBirth, gender, contactInfo, userId]
    );
    
    res.status(201).json({
      success: true,
      patient: result.rows[0]
    });
  } catch (error) {
    console.error('创建患者错误:', error);
    res.status(500).json({
      success: false,
      message: '创建患者失败'
    });
  }
};

// 获取特定患者详情
const getPatientDetails = async (req, res) => {
  try {
    const { id } = req.params;
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT p.id, p.patient_id, p.first_name, p.last_name, p.date_of_birth, p.gender,
             p.contact_info, p.created_at, p.updated_at
      FROM patients p
      WHERE p.id = $1 AND p.tenant_id = $2
    `, [id, tenantId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '患者不存在'
      });
    }
    
    res.json({
      success: true,
      patient: result.rows[0]
    });
  } catch (error) {
    console.error('获取患者详情错误:', error);
    res.status(500).json({
      success: false,
      message: '获取患者详情失败'
    });
  }
};

// 更新患者信息
const updatePatient = async (req, res) => {
  try {
    const { id } = req.params;
    const { patientId, firstName, lastName, dateOfBirth, gender, contactInfo } = req.body;
    const { tenantId } = req.query;
    
    const result = await pool.query(
      `UPDATE patients 
       SET patient_id = $1, first_name = $2, last_name = $3, 
           date_of_birth = $4, gender = $5, contact_info = $6, updated_at = NOW()
       WHERE id = $7 AND tenant_id = $8
       RETURNING id, patient_id, first_name, last_name, date_of_birth, gender, contact_info`,
      [patientId, firstName, lastName, dateOfBirth, gender, contactInfo, id, tenantId]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '患者不存在或权限不足'
      });
    }
    
    res.json({
      success: true,
      patient: result.rows[0]
    });
  } catch (error) {
    console.error('更新患者错误:', error);
    res.status(500).json({
      success: false,
      message: '更新患者失败'
    });
  }
};

// 创建病历夹
const createPatientFolder = async (req, res) => {
  try {
    const { patientId, name, description } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!patientId || !name) {
      return res.status(400).json({
        success: false,
        message: '患者ID和病历夹名称是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO patient_folders 
       (tenant_id, patient_id, name, description, created_by) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id, patient_id, name, description, created_at`,
      [tenantId, patientId, name, description, userId]
    );
    
    res.status(201).json({
      success: true,
      folder: result.rows[0]
    });
  } catch (error) {
    console.error('创建病历夹错误:', error);
    res.status(500).json({
      success: false,
      message: '创建病历夹失败'
    });
  }
};

// 获取患者病历夹
const getPatientFolders = async (req, res) => {
  try {
    const { patientId, tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT pf.id, pf.name, pf.description, pf.created_at, pf.updated_at,
             u.username as created_by_name
      FROM patient_folders pf
      LEFT JOIN users u ON pf.created_by = u.id
      WHERE pf.patient_id = $1 AND pf.tenant_id = $2
      ORDER BY pf.created_at DESC
    `, [patientId, tenantId]);
    
    res.json({
      success: true,
      folders: result.rows
    });
  } catch (error) {
    console.error('获取病历夹错误:', error);
    res.status(500).json({
      success: false,
      message: '获取病历夹失败'
    });
  }
};

// 添加数据到病历夹
const addFolderData = async (req, res) => {
  try {
    const { folderId, patientId, data } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!folderId || !patientId || !data) {
      return res.status(400).json({
        success: false,
        message: '病历夹ID、患者ID和数据是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO patient_folder_data 
       (tenant_id, folder_id, patient_id, data, created_by) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id, folder_id, patient_id, data, created_at`,
      [tenantId, folderId, patientId, data, userId]
    );
    
    res.status(201).json({
      success: true,
      folderData: result.rows[0]
    });
  } catch (error) {
    console.error('添加病历夹数据错误:', error);
    res.status(500).json({
      success: false,
      message: '添加病历夹数据失败'
    });
  }
};

// 获取病历夹数据
const getFolderData = async (req, res) => {
  try {
    const { folderId, patientId, tenantId } = req.query;
    
    let query = 'SELECT pfd.id, pfd.folder_id, pfd.patient_id, pfd.data, pfd.created_at FROM patient_folder_data pfd WHERE pfd.tenant_id = $1';
    const params = [tenantId];
    
    if (folderId) {
      query += ' AND pfd.folder_id = $2';
      params.push(folderId);
    }
    
    if (patientId) {
      query += ' AND pfd.patient_id = $3';
      params.push(patientId);
    }
    
    query += ' ORDER BY pfd.created_at DESC';
    
    const result = await pool.query(query, params);
    
    res.json({
      success: true,
      folderData: result.rows
    });
  } catch (error) {
    console.error('获取病历夹数据错误:', error);
    res.status(500).json({
      success: false,
      message: '获取病历夹数据失败'
    });
  }
};

// 引用EDC模板创建病历夹表单
const importEdcTemplate = async (req, res) => {
  try {
    const { templateId, folderId } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!templateId || !folderId) {
      return res.status(400).json({
        success: false,
        message: '模板ID和病历夹ID是必填项'
      });
    }
    
    // 获取EDC模板数据
    const templateResult = await pool.query(
      'SELECT template_data, cdash_fields FROM edc_templates WHERE id = $1 AND tenant_id = $2',
      [templateId, tenantId]
    );
    
    if (templateResult.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'EDC模板不存在'
      });
    }
    
    const templateData = templateResult.rows[0].template_data;
    
    // 检查是否已有这个模板的导入记录
    const existingResult = await pool.query(
      'SELECT id FROM imported_templates WHERE template_id = $1 AND folder_id = $2 AND tenant_id = $3',
      [templateId, folderId, tenantId]
    );
    
    if (existingResult.rows.length > 0) {
      return res.status(400).json({
        success: false,
        message: '该模板已导入到此病历夹'
      });
    }
    
    // 创建导入记录
    await pool.query(
      'INSERT INTO imported_templates (tenant_id, template_id, folder_id, imported_data, created_by) VALUES ($1, $2, $3, $4, $5)',
      [tenantId, templateId, folderId, templateData, userId]
    );
    
    res.json({
      success: true,
      message: 'EDC模板已成功导入到病历夹'
    });
  } catch (error) {
    console.error('导入EDC模板错误:', error);
    res.status(500).json({
      success: false,
      message: '导入EDC模板失败'
    });
  }
};

module.exports = {
  getPatients,
  createPatient,
  getPatientDetails,
  updatePatient,
  createPatientFolder,
  getPatientFolders,
  addFolderData,
  getFolderData,
  importEdcTemplate
};