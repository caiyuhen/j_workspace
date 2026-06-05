const jwt = require('jsonwebtoken');
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

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
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

// 权限检查中间件
const checkPermission = (requiredPermission) => {
  return async (req, res, next) => {
    try {
      // 这里应该实现具体的权限检查逻辑
      // 检查用户是否具有所需的权限
      next();
    } catch (error) {
      return res.status(403).json({
        success: false,
        message: '权限不足'
      });
    }
  };
};

// 角色检查中间件
const checkRole = (requiredRoles) => {
  return async (req, res, next) => {
    try {
      const { userId } = req.user;
      
      // 获取用户的所有角色
      const userRolesResult = await pool.query(`
        SELECT r.name 
        FROM user_roles ur 
        JOIN roles r ON ur.role_id = r.id 
        WHERE ur.user_id = $1
      `, [userId]);
      
      const userRoles = userRolesResult.rows.map(row => row.name);
      
      // 检查用户是否具有所需角色
      const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
      
      if (!hasRequiredRole) {
        return res.status(403).json({
          success: false,
          message: '角色权限不足'
        });
      }
      
      next();
    } catch (error) {
      console.error('权限检查错误:', error);
      return res.status(403).json({
        success: false,
        message: '权限检查失败'
      });
    }
  };
};

module.exports = {
  authenticateToken,
  checkPermission,
  checkRole
};