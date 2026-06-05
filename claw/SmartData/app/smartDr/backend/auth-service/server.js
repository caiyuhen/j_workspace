const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
require('dotenv').config();

const authRoutes = require('./routes/authRoutes');
const { authenticateToken } = require('./middleware/authMiddleware');

const app = express();
const PORT = process.env.PORT || 3001;

// 安全中间件
app.use(helmet());
app.use(cors());

// 速率限制
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100 // 限制每个IP 100个请求
});
app.use(limiter);

// 解析JSON请求体
app.use(express.json());

// 健康检查端点
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', service: 'auth-service' });
});

// 认证相关路由
app.use('/api/auth', authRoutes);

// 受保护的路由示例
app.get('/api/protected', authenticateToken, (req, res) => {
  res.json({ 
    message: '这是一个受保护的端点',
    user: req.user
  });
});

// 增加用户信息获取endpoint
app.get('/api/user/profile', authenticateToken, async (req, res) => {
  try {
    const { Pool } = require('pg');
    const pool = new Pool({
      connectionString: process.env.DATABASE_URL
    });

    const userResult = await pool.query(
      'SELECT id, username, email, first_name, last_name FROM users WHERE id = $1',
      [req.user.userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '用户不存在'
      });
    }

    res.json({
      success: true,
      user: userResult.rows[0]
    });
  } catch (error) {
    console.error('获取用户信息错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器内部错误'
    });
  }
});

app.listen(PORT, () => {
  console.log(`认证服务运行在端口 ${PORT}`);
});

module.exports = app;