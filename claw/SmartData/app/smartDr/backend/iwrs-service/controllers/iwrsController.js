const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 随机化配置管理
const getRandomizationConfig = async (req, res) => {
  try {
    const { trialId, tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT rc.id, rc.algorithm, rc.treatment_arms, rc.block_sizes, 
             rc.stratification_factors, rc.allocation_ratio, rc.created_at
      FROM randomization_configs rc
      WHERE rc.trial_id = $1 AND rc.tenant_id = $2
    `, [trialId, tenantId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '未找到随机化配置'
      });
    }
    
    res.json({
      success: true,
      config: result.rows[0]
    });
  } catch (error) {
    console.error('获取随机化配置错误:', error);
    res.status(500).json({
      success: false,
      message: '获取随机化配置失败'
    });
  }
};

// 创建随机化配置
const createRandomizationConfig = async (req, res) => {
  try {
    const { trialId, algorithm, treatmentArms, blockSizes, 
            stratificationFactors, allocationRatio } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!trialId || !algorithm || !treatmentArms) {
      return res.status(400).json({
        success: false,
        message: '试验ID、算法和治疗组是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO randomization_configs 
       (tenant_id, trial_id, algorithm, treatment_arms, block_sizes, 
        stratification_factors, allocation_ratio, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
       RETURNING id, algorithm, treatment_arms, block_sizes, 
                 stratification_factors, allocation_ratio, created_at`,
      [tenantId, trialId, algorithm, treatmentArms, blockSizes, 
       stratificationFactors, allocationRatio, userId]
    );
    
    res.status(201).json({
      success: true,
      config: result.rows[0]
    });
  } catch (error) {
    console.error('创建随机化配置错误:', error);
    res.status(500).json({
      success: false,
      message: '创建随机化配置失败'
    });
  }
};

// 获取患者的随机化结果
const getPatientRandomization = async (req, res) => {
  try {
    const { patientId, trialId, tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT pr.id, pr.patient_id, pr.trial_id, pr.treatment_group, 
             pr.randomization_date, pr.created_at
      FROM patient_randomizations pr
      WHERE pr.patient_id = $1 AND pr.trial_id = $2 AND pr.tenant_id = $3
    `, [patientId, trialId, tenantId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '未找到患者随机化记录'
      });
    }
    
    res.json({
      success: true,
      randomization: result.rows[0]
    });
  } catch (error) {
    console.error('获取患者随机化错误:', error);
    res.status(500).json({
      success: false,
      message: '获取患者随机化失败'
    });
  }
};

// 为患者执行随机化
const randomizePatient = async (req, res) => {
  try {
    const { patientId, trialId, treatmentGroup } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!patientId || !trialId) {
      return res.status(400).json({
        success: false,
        message: '患者ID和试验ID是必填项'
      });
    }
    
    // 检查是否已存在随机化记录
    const existingResult = await pool.query(
      'SELECT id FROM patient_randomizations WHERE patient_id = $1 AND trial_id = $2 AND tenant_id = $3',
      [patientId, trialId, tenantId]
    );
    
    if (existingResult.rows.length > 0) {
      return res.status(400).json({
        success: false,
        message: '该患者已在该试验中有随机化记录'
      });
    }
    
    // 执行随机化（简化版本）
    // 实际项目中需要更复杂的算法
    let group = treatmentGroup;
    if (!group) {
      // 简单的随机分配逻辑，实际应该使用配置的算法
      const random = Math.random();
      group = random < 0.5 ? 'ARM_A' : 'ARM_B';
    }
    
    const result = await pool.query(
      `INSERT INTO patient_randomizations 
       (tenant_id, patient_id, trial_id, treatment_group, randomization_date, created_by) 
       VALUES ($1, $2, $3, $4, NOW(), $5) 
       RETURNING id, patient_id, trial_id, treatment_group, randomization_date`,
      [tenantId, patientId, trialId, group, userId]
    );
    
    res.status(201).json({
      success: true,
      randomization: result.rows[0]
    });
  } catch (error) {
    console.error('患者随机化错误:', error);
    res.status(500).json({
      success: false,
      message: '患者随机化失败'
    });
  }
};

// 药物库存管理
const getDrugInventory = async (req, res) => {
  try {
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT di.id, di.drug_name, di.specification, di.batch_number, 
             di.quantity, di.expiry_date, di.location, di.created_at
      FROM drug_inventory di
      WHERE di.tenant_id = $1
      ORDER BY di.created_at DESC
    `, [tenantId]);
    
    res.json({
      success: true,
      inventory: result.rows
    });
  } catch (error) {
    console.error('获取药物库存错误:', error);
    res.status(500).json({
      success: false,
      message: '获取药物库存失败'
    });
  }
};

// 添加药物库存
const addDrugInventory = async (req, res) => {
  try {
    const { drugName, specification, batchNumber, quantity, expiryDate, location } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!drugName || !quantity) {
      return res.status(400).json({
        success: false,
        message: '药物名称和数量是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO drug_inventory 
       (tenant_id, drug_name, specification, batch_number, quantity, 
        expiry_date, location, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
       RETURNING id, drug_name, specification, batch_number, 
                 quantity, expiry_date, location, created_at`,
      [tenantId, drugName, specification, batchNumber, quantity, 
       expiryDate, location, userId]
    );
    
    res.status(201).json({
      success: true,
      inventory: result.rows[0]
    });
  } catch (error) {
    console.error('添加药物库存错误:', error);
    res.status(500).json({
      success: false,
      message: '添加药物库存失败'
    });
  }
};

// 获取破盲申请
const getBlindingRequests = async (req, res) => {
  try {
    const { tenantId, status } = req.query;
    
    let query = 'SELECT br.id, br.patient_id, br.trial_id, br.reason, br.status, br.created_at FROM blinding_requests br WHERE br.tenant_id = $1';
    const params = [tenantId];
    
    if (status) {
      query += ' AND br.status = $2';
      params.push(status);
    }
    
    query += ' ORDER BY br.created_at DESC';
    
    const result = await pool.query(query, params);
    
    res.json({
      success: true,
      requests: result.rows
    });
  } catch (error) {
    console.error('获取破盲申请错误:', error);
    res.status(500).json({
      success: false,
      message: '获取破盲申请失败'
    });
  }
};

// 创建破盲申请
const createBlindingRequest = async (req, res) => {
  try {
    const { patientId, trialId, reason } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!patientId || !trialId || !reason) {
      return res.status(400).json({
        success: false,
        message: '患者ID、试验ID和破盲理由是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO blinding_requests 
       (tenant_id, patient_id, trial_id, reason, status, created_by) 
       VALUES ($1, $2, $3, $4, 'PENDING', $5) 
       RETURNING id, patient_id, trial_id, reason, status, created_at`,
      [tenantId, patientId, trialId, reason, userId]
    );
    
    res.status(201).json({
      success: true,
      request: result.rows[0]
    });
  } catch (error) {
    console.error('创建破盲申请错误:', error);
    res.status(500).json({
      success: false,
      message: '创建破盲申请失败'
    });
  }
};

module.exports = {
  getRandomizationConfig,
  createRandomizationConfig,
  getPatientRandomization,
  randomizePatient,
  getDrugInventory,
  addDrugInventory,
  getBlindingRequests,
  createBlindingRequest
};