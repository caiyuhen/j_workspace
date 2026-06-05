const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3006;

// 安全中间件
app.use(helmet());
app.use(cors());

// 解析JSON请求体
app.use(express.json());

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 健康检查端点
app.get('/health', async (req, res) => {
  try {
    // 检查数据库连接
    await pool.query('SELECT 1');
    
    res.status(200).json({ 
      status: 'OK', 
      service: 'monitoring-service',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'ERROR', 
      service: 'monitoring-service',
      error: 'Database connection failed',
      timestamp: new Date().toISOString()
    });
  }
});

// 系统指标端点
app.get('/metrics', async (req, res) => {
  try {
    // 获取数据库统计信息
    const dbStats = await pool.query(`
      SELECT 
        COUNT(*) as total_patients,
        COUNT(DISTINCT tenant_id) as total_tenants,
        COUNT(DISTINCT created_by) as total_users
      FROM patients
    `);
    
    // 获取服务状态信息（模拟）
    const serviceStatus = {
      auth_service: 'running',
      ctms_service: 'running', 
      edc_service: 'running',
      iwrs_service: 'running',
      patient_folder_service: 'running',
      api_gateway: 'running'
    };
    
    res.json({
      metrics: {
        database: {
          patients: dbStats.rows[0].total_patients,
          tenants: dbStats.rows[0].total_tenants,
          users: dbStats.rows[0].total_users
        },
        services: serviceStatus,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('获取系统指标错误:', error);
    res.status(500).json({
      error: 'Failed to retrieve metrics',
      timestamp: new Date().toISOString()
    });
  }
});

// 错误处理中间件
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal server error',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`监控服务运行在端口 ${PORT}`);
});

module.exports = app;