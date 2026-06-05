const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 获取审计日志
const getAuditLogs = async (req, res) => {
  try {
    const { tenantId, userId, tableName, action, startDate, endDate } = req.query;
    
    let query = 'SELECT al.id, al.user_id, al.action, al.table_name, al.record_id, al.old_values, al.new_values, al.ip_address, al.user_agent, al.created_at, u.username as user_name FROM audit_logs al LEFT JOIN users u ON al.user_id = u.id WHERE al.tenant_id = $1';
    const params = [tenantId];
    
    if (userId) {
      query += ' AND al.user_id = $2';
      params.push(userId);
    }
    
    if (tableName) {
      query += ' AND al.table_name = $3';
      params.push(tableName);
    }
    
    if (action) {
      query += ' AND al.action = $4';
      params.push(action);
    }
    
    if (startDate) {
      query += ' AND al.created_at >= $5';
      params.push(startDate);
    }
    
    if (endDate) {
      query += ' AND al.created_at <= $6';
      params.push(endDate);
    }
    
    query += ' ORDER BY al.created_at DESC LIMIT 100';
    
    const result = await pool.query(query, params);
    
    res.json({
      success: true,
      logs: result.rows
    });
  } catch (error) {
    console.error('获取审计日志错误:', error);
    res.status(500).json({
      success: false,
      message: '获取审计日志失败'
    });
  }
};

// 记录审计日志
const logAudit = async (tenantId, userId, action, tableName, recordId, oldValues, newValues, ipAddress, userAgent) => {
  try {
    await pool.query(
      `INSERT INTO audit_logs 
       (tenant_id, user_id, action, table_name, record_id, old_values, new_values, ip_address, user_agent) 
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [tenantId, userId, action, tableName, recordId, oldValues, newValues, ipAddress, userAgent]
    );
  } catch (error) {
    console.error('记录审计日志错误:', error);
    // 记录失败不应该影响主要功能，只记录日志
  }
};

// 获取数据加密密钥
const getEncryptionKeys = async (req, res) => {
  try {
    const { tenantId } = req.query;
    
    const result = await pool.query(`
      SELECT ek.id, ek.key_name, ek.created_at
      FROM encryption_keys ek
      WHERE ek.tenant_id = $1
      ORDER BY ek.created_at DESC
    `, [tenantId]);
    
    res.json({
      success: true,
      keys: result.rows
    });
  } catch (error) {
    console.error('获取加密密钥错误:', error);
    res.status(500).json({
      success: false,
      message: '获取加密密钥失败'
    });
  }
};

// 创建加密密钥
const createEncryptionKey = async (req, res) => {
  try {
    const { keyName, keyValue } = req.body;
    const { userId, tenantId } = req.user;
    
    // 验证输入
    if (!keyName) {
      return res.status(400).json({
        success: false,
        message: '密钥名称是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO encryption_keys 
       (tenant_id, key_name, key_value, created_by) 
       VALUES ($1, $2, $3, $4) 
       RETURNING id, key_name, created_at`,
      [tenantId, keyName, keyValue, userId]
    );
    
    res.status(201).json({
      success: true,
      key: result.rows[0]
    });
  } catch (error) {
    console.error('创建加密密钥错误:', error);
    res.status(500).json({
      success: false,
      message: '创建加密密钥失败'
    });
  }
};

// 检查用户敏感数据访问
const checkSensitiveDataAccess = async (req, res) => {
  try {
    const { userId, tenantId, dataCategory } = req.query;
    
    // 简单的访问控制检查
    // 实际项目中应更复杂的逻辑检查用户权限
    const allowedCategories = ['patient', 'medical', 'trial'];
    
    if (!allowedCategories.includes(dataCategory)) {
      return res.status(403).json({
        success: false,
        message: '访问的数据类别不被允许'
      });
    }
    
    // 这里应该结合用户角色和权限进行更严格的检查
    res.json({
      success: true,
      allowed: true,
      message: '用户有访问权限'
    });
  } catch (error) {
    console.error('检查敏感数据访问错误:', error);
    res.status(500).json({
      success: false,
      message: '检查访问权限失败'
    });
  }
};

module.exports = {
  getAuditLogs,
  logAudit,
  getEncryptionKeys,
  createEncryptionKey,
  checkSensitiveDataAccess
};