const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 用户登录
const login = async (req, res) => {
  try {
    const { username, password } = req.body;
    
    // 验证输入
    if (!username || !password) {
      return res.status(400).json({
        success: false,
        message: '用户名和密码是必填项'
      });
    }

    // 从数据库查询用户
    const userResult = await pool.query(
      'SELECT id, username, email, password_hash, first_name, last_name FROM users WHERE username = $1 OR email = $1',
      [username]
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({
        success: false,
        message: '用户名或密码错误'
      });
    }

    const user = userResult.rows[0];

    // 验证密码
    const isPasswordValid = await bcrypt.compare(password, user.password_hash);
    
    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        message: '用户名或密码错误'
      });
    }

    // 生成JWT令牌
    const token = jwt.sign(
      { 
        userId: user.id, 
        username: user.username,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name
      },
      process.env.JWT_SECRET,
      { expiresIn: '24h' }
    );

    // 响应成功
    res.json({
      success: true,
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name
      }
    });

  } catch (error) {
    console.error('登录错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器内部错误'
    });
  }
};

// 用户注册
const register = async (req, res) => {
  try {
    const { username, email, password, firstName, lastName } = req.body;

    // 验证输入
    if (!username || !email || !password) {
      return res.status(400).json({
        success: false,
        message: '用户名、邮箱和密码是必填项'
      });
    }

    // 检查用户是否已存在
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE username = $1 OR email = $1',
      [username]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({
        success: false,
        message: '用户名或邮箱已存在'
      });
    }

    // 密码加密
    const saltRounds = 10;
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // 创建新用户
    const newUser = await pool.query(
      'INSERT INTO users (username, email, password_hash, first_name, last_name) VALUES ($1, $2, $3, $4, $5) RETURNING id, username, email, first_name, last_name',
      [username, email, hashedPassword, firstName, lastName]
    );

    // 为新用户分配默认角色（例如：patient）
    const defaultRole = 'patient';
    const roleResult = await pool.query(
      'SELECT id FROM roles WHERE name = $1',
      [defaultRole]
    );

    if (roleResult.rows.length > 0) {
      await pool.query(
        'INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)',
        [newUser.rows[0].id, roleResult.rows[0].id]
      );
    }

    // 生成JWT令牌
    const token = jwt.sign(
      { 
        userId: newUser.rows[0].id, 
        username: newUser.rows[0].username,
        email: newUser.rows[0].email,
        firstName: newUser.rows[0].first_name,
        lastName: newUser.rows[0].last_name
      },
      process.env.JWT_SECRET,
      { expiresIn: '24h' }
    );

    // 响应成功
    res.status(201).json({
      success: true,
      token,
      user: {
        id: newUser.rows[0].id,
        username: newUser.rows[0].username,
        email: newUser.rows[0].email,
        firstName: newUser.rows[0].first_name,
        lastName: newUser.rows[0].last_name
      }
    });

  } catch (error) {
    console.error('注册错误:', error);
    res.status(500).json({
      success: false,
      message: '服务器内部错误'
    });
  }
};

// 验证令牌
const validateToken = async (req, res) => {
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
    
    // 验证用户是否存在
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

    res.json({
      success: true,
      user: {
        id: userResult.rows[0].id,
        username: userResult.rows[0].username,
        email: userResult.rows[0].email
      }
    });

  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(403).json({
        success: false,
        message: '令牌已过期'
      });
    }
    
    return res.status(403).json({
      success: false,
      message: '令牌无效或已过期'
    });
  }
};

module.exports = {
  login,
  register,
  validateToken
};