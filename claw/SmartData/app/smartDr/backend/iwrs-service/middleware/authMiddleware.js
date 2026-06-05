const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// JWT认证中间件
const authenticateToken = async (req, res, next) => {
  try {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
      return res.status(401).json({
        success: false,
        message: '访问令牌缺失'
      });
    }

    const jwt = require('jsonwebtoken');
    const secret = process.env.JWT_SECRET || 'default-secret-key';
    
    const decoded = jwt.verify(token, secret);
    
    // 验证用户是否存在且激活
    const userResult = await pool.query(
      'SELECT id, username, email FROM users WHERE id = $1 AND is_active = true',
      [decoded.userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({
        success: false,
        message: '用户不存在或已被禁用'
      });
    }

    req.user = decoded;
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(403).json({
        success: false,
        message: '令牌已过期'
      });
    }
    
    return res.status(403).json({
      success: false,
      message: '令牌无效'
    });
  }
};

module.exports = {
  authenticateToken
};