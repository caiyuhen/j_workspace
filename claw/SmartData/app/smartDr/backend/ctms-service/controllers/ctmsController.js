const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 获取临床试验列表
const getTrials = async (req, res) => {
  try {
    const { tenantId } = req.query;
    
    // 获取当前用户可访问的试验列表
    let query = `
      SELECT ct.id, ct.name, ct.description, ct.start_date, ct.end_date, ct.status, 
             u.username as created_by_name
      FROM clinical_trials ct
      LEFT JOIN users u ON ct.created_by = u.id
      WHERE ct.tenant_id = $1
      ORDER BY ct.created_at DESC
    `;
    
    const result = await pool.query(query, [tenantId]);
    
    res.json({
      success: true,
      trials: result.rows
    });
  } catch (error) {
    console.error('获取试验列表错误:', error);
    res.status(500).json({
      success: false,
      message: '获取试验列表失败'
    });
  }
};

// 创建临床试验
const createTrial = async (req, res) => {
  try {
    const { name, description, startDate, endDate, status } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!name) {
      return res.status(400).json({
        success: false,
        message: '试验名称是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO clinical_trials 
       (tenant_id, name, description, start_date, end_date, status, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6, $7) 
       RETURNING id, name, description, start_date, end_date, status`,
      [tenantId, name, description, startDate, endDate, status, userId]
    );
    
    res.status(201).json({
      success: true,
      trial: result.rows[0]
    });
  } catch (error) {
    console.error('创建试验错误:', error);
    res.status(500).json({
      success: false,
      message: '创建试验失败'
    });
  }
};

// 获取特定试验详情
const getTrialDetails = async (req, res) => {
  try {
    const { id } = req.params;
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT ct.id, ct.name, ct.description, ct.start_date, ct.end_date, ct.status,
             u.username as created_by_name, ct.created_at
      FROM clinical_trials ct
      LEFT JOIN users u ON ct.created_by = u.id
      WHERE ct.id = $1 AND ct.tenant_id = $2
    `, [id, tenantId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '试验不存在'
      });
    }
    
    res.json({
      success: true,
      trial: result.rows[0]
    });
  } catch (error) {
    console.error('获取试验详情错误:', error);
    res.status(500).json({
      success: false,
      message: '获取试验详情失败'
    });
  }
};

// 更新试验信息
const updateTrial = async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description, startDate, endDate, status } = req.body;
    const { tenantId } = req.query;
    
    const result = await pool.query(
      `UPDATE clinical_trials 
       SET name = $1, description = $2, start_date = $3, end_date = $4, status = $5, updated_at = NOW()
       WHERE id = $6 AND tenant_id = $7
       RETURNING id, name, description, start_date, end_date, status`,
      [name, description, startDate, endDate, status, id, tenantId]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '试验不存在或权限不足'
      });
    }
    
    res.json({
      success: true,
      trial: result.rows[0]
    });
  } catch (error) {
    console.error('更新试验错误:', error);
    res.status(500).json({
      success: false,
      message: '更新试验失败'
    });
  }
};

// 删除试验
const deleteTrial = async (req, res) => {
  try {
    const { id } = req.params;
    const { tenantId } = req.query;
    
    const result = await pool.query(
      'DELETE FROM clinical_trials WHERE id = $1 AND tenant_id = $2 RETURNING id',
      [id, tenantId]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '试验不存在或权限不足'
      });
    }
    
    res.json({
      success: true,
      message: '试验删除成功'
    });
  } catch (error) {
    console.error('删除试验错误:', error);
    res.status(500).json({
      success: false,
      message: '删除试验失败'
    });
  }
};

// 获取研究中心列表
const getStudySites = async (req, res) => {
  try {
    const { trialId, tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT ss.id, ss.name, ss.status, ss.contact_person, ss.contact_email, ss.contact_phone,
             u.username as created_by_name
      FROM study_sites ss
      LEFT JOIN users u ON ss.created_by = u.id
      WHERE ss.trial_id = $1 AND ss.tenant_id = $2
      ORDER BY ss.created_at DESC
    `, [trialId, tenantId]);
    
    res.json({
      success: true,
      sites: result.rows
    });
  } catch (error) {
    console.error('获取研究中心错误:', error);
    res.status(500).json({
      success: false,
      message: '获取研究中心失败'
    });
  }
};

// 创建研究中心
const createStudySite = async (req, res) => {
  try {
    const { trialId, name, status, contactPerson, contactEmail, contactPhone } = req.body;
    const { userId, tenantId } = req.user;
    
    const result = await pool.query(
      `INSERT INTO study_sites 
       (tenant_id, trial_id, name, status, contact_person, contact_email, contact_phone, created_by) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
       RETURNING id, name, status, contact_person, contact_email, contact_phone`,
      [tenantId, trialId, name, status, contactPerson, contactEmail, contactPhone, userId]
    );
    
    res.status(201).json({
      success: true,
      site: result.rows[0]
    });
  } catch (error) {
    console.error('创建研究中心错误:', error);
    res.status(500).json({
      success: false,
      message: '创建研究中心失败'
    });
  }
};

// 获取工时记录
const getTimeEntries = async (req, res) => {
  try {
    const { tenantId, userId } = req.query;

    // 根据查询条件获取对应工时记录
    let query = `SELECT te.id, te.date, te.hours, te.description, te.task_type,
                       u.username as reported_by_name
                FROM time_entries te
                LEFT JOIN users u ON te.reported_by = u.id
                WHERE te.tenant_id = $1`;
    const params = [tenantId];

    if (userId) {
      query += ' AND te.reported_by = $2';
      params.push(userId);
    }

    query += ' ORDER BY te.date DESC';

    const result = await pool.query(query, params);

    res.json({
      success: true,
      timeEntries: result.rows
    });
  } catch (error) {
    console.error('获取工时记录错误:', error);
    res.status(500).json({
      success: false,
      message: '获取工时记录失败'
    });
  }
};

// 创建工时记录
const createTimeEntry = async (req, res) => {
  try {
    const { date, hours, description, taskType } = req.body;
    const { userId, tenantId } = req.user;

    // 验证输入
    if (!date || !hours || !taskType) {
      return res.status(400).json({
        success: false,
        message: '日期、工时和任务类型是必填项'
      });
    }

    const result = await pool.query(
      `INSERT INTO time_entries
       (tenant_id, reported_by, date, hours, description, task_type)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, date, hours, description, task_type`,
      [tenantId, userId, date, hours, description, taskType]
    );

    res.status(201).json({
      success: true,
      timeEntry: result.rows[0]
    });
  } catch (error) {
    console.error('创建工时记录错误:', error);
    res.status(500).json({
      success: false,
      message: '创建工时记录失败'
    });
  }
};

// 更新工时记录
const updateTimeEntry = async (req, res) => {
  try {
    const { id } = req.params;
    const { date, hours, description, taskType } = req.body;
    const { tenantId } = req.query;

    const result = await pool.query(
      `UPDATE time_entries
       SET date = $1, hours = $2, description = $3, task_type = $4, updated_at = NOW()
       WHERE id = $5 AND tenant_id = $6
       RETURNING id, date, hours, description, task_type`,
      [date, hours, description, taskType, id, tenantId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '工时记录不存在或权限不足'
      });
    }

    res.json({
      success: true,
      timeEntry: result.rows[0]
    });
  } catch (error) {
    console.error('更新工时记录错误:', error);
    res.status(500).json({
      success: false,
      message: '更新工时记录失败'
    });
  }
};

// 删除工时记录
const deleteTimeEntry = async (req, res) => {
  try {
    const { id } = req.params;
    const { tenantId } = req.query;

    const result = await pool.query(
      'DELETE FROM time_entries WHERE id = $1 AND tenant_id = $2 RETURNING id',
      [id, tenantId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '工时记录不存在或权限不足'
      });
    }

    res.json({
      success: true,
      message: '工时记录删除成功'
    });
  } catch (error) {
    console.error('删除工时记录错误:', error);
    res.status(500).json({
      success: false,
      message: '删除工时记录失败'
    });
  }
};

// 获取工时统计报告
const getTimeEntryReport = async (req, res) => {
  try {
    const { tenantId, startDate, endDate, userId } = req.query;

    let query = `
      SELECT
        u.username,
        SUM(te.hours) as total_hours,
        COUNT(te.id) as entry_count,
        MIN(te.date) as first_date,
        MAX(te.date) as last_date
      FROM time_entries te
      JOIN users u ON te.reported_by = u.id
      WHERE te.tenant_id = $1
    `;
    const params = [tenantId];

    if (startDate) {
      query += ' AND te.date >= $2';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND te.date <= $3';
      params.push(endDate);
    }

    if (userId) {
      query += ' AND te.reported_by = $4';
      params.push(userId);
    }

    query += ' GROUP BY u.username ORDER BY total_hours DESC';

    const result = await pool.query(query, params);

    res.json({
      success: true,
      report: result.rows
    });
  } catch (error) {
    console.error('获取工时报告错误:', error);
    res.status(500).json({
      success: false,
      message: '获取工时报告失败'
    });
  }
};

module.exports = {
  getTrials,
  createTrial,
  getTrialDetails,
  updateTrial,
  deleteTrial,
  getStudySites,
  createStudySite,
  getTimeEntries,
  createTimeEntry,
  updateTimeEntry,
  deleteTimeEntry,
  getTimeEntryReport
};