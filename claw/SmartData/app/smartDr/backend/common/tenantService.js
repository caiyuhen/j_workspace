const { Pool } = require('pg');
require('dotenv').config();

// 数据库连接池
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// 获取所有租户
const getTenants = async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT t.id, t.name, t.description, t.is_active, t.created_at, t.updated_at
      FROM tenants t
      ORDER BY t.created_at DESC
    `);
    
    res.json({
      success: true,
      tenants: result.rows
    });
  } catch (error) {
    console.error('获取租户列表错误:', error);
    res.status(500).json({
      success: false,
      message: '获取租户列表失败'
    });
  }
};

// 创建租户
const createTenant = async (req, res) => {
  try {
    const { name, description } = req.body;
    const { userId } = req.user;
    
    // 验证输入
    if (!name) {
      return res.status(400).json({
        success: false,
        message: '租户名称是必填项'
      });
    }
    
    const result = await pool.query(
      `INSERT INTO tenants (name, description, created_by) 
       VALUES ($1, $2, $3) 
       RETURNING id, name, description, created_at`,
      [name, description, userId]
    );
    
    res.status(201).json({
      success: true,
      tenant: result.rows[0]
    });
  } catch (error) {
    console.error('创建租户错误:', error);
    res.status(500).json({
      success: false,
      message: '创建租户失败'
    });
  }
};

// 获取特定租户详情
const getTenantDetails = async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await pool.query(`
      SELECT t.id, t.name, t.description, t.is_active, t.created_at, t.updated_at
      FROM tenants t
      WHERE t.id = $1
    `, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '租户不存在'
      });
    }
    
    res.json({
      success: true,
      tenant: result.rows[0]
    });
  } catch (error) {
    console.error('获取租户详情错误:', error);
    res.status(500).json({
      success: false,
      message: '获取租户详情失败'
    });
  }
};

// 更新租户信息
const updateTenant = async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description, isActive } = req.body;
    
    const result = await pool.query(
      `UPDATE tenants 
       SET name = $1, description = $2, is_active = $3, updated_at = NOW()
       WHERE id = $4
       RETURNING id, name, description, is_active, updated_at`,
      [name, description, isActive, id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '租户不存在'
      });
    }
    
    res.json({
      success: true,
      tenant: result.rows[0]
    });
  } catch (error) {
    console.error('更新租户信息错误:', error);
    res.status(500).json({
      success: false,
      message: '更新租户信息失败'
    });
  }
};

// 删除租户
const deleteTenant = async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await pool.query(
      'DELETE FROM tenants WHERE id = $1 RETURNING id',
      [id]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '租户不存在'
      });
    }
    
    res.json({
      success: true,
      message: '租户删除成功'
    });
  } catch (error) {
    console.error('删除租户错误:', error);
    res.status(500).json({
      success: false,
      message: '删除租户失败'
    });
  }
};

// 获取租户用户
const getTenantUsers = async (req, res) => {
  try {
    const { tenantId } = req.params;
    
    const result = await pool.query(`
      SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.created_at,
             r.name as role_name
      FROM tenant_users tu
      JOIN users u ON tu.user_id = u.id
      LEFT JOIN user_roles ur ON u.id = ur.user_id
      LEFT JOIN roles r ON ur.role_id = r.id
      WHERE tu.tenant_id = $1
    `, [tenantId]);
    
    res.json({
      success: true,
      users: result.rows
    });
  } catch (error) {
    console.error('获取租户用户错误:', error);
    res.status(500).json({
      success: false,
      message: '获取租户用户失败'
    });
  }
};

// 添加用户到租户
const addTenantUser = async (req, res) => {
  try {
    const { tenantId, userId } = req.body;
    
    // 验证输入
    if (!tenantId || !userId) {
      return res.status(400).json({
        success: false,
        message: '租户ID和用户ID是必填项'
      });
    }
    
    const result = await pool.query(
      'INSERT INTO tenant_users (tenant_id, user_id) VALUES ($1, $2) RETURNING tenant_id, user_id',
      [tenantId, userId]
    );
    
    res.status(201).json({
      success: true,
      user: result.rows[0]
    });
  } catch (error) {
    console.error('添加租户用户错误:', error);
    res.status(500).json({
      success: false,
      message: '添加租户用户失败'
    });
  }
};

// 从租户删除用户
const removeTenantUser = async (req, res) => {
  try {
    const { tenantId, userId } = req.params;
    
    const result = await pool.query(
      'DELETE FROM tenant_users WHERE tenant_id = $1 AND user_id = $2 RETURNING tenant_id, user_id',
      [tenantId, userId]
    );
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: '用户不在该租户中'
      });
    }
    
    res.json({
      success: true,
      message: '用户已从租户中移除'
    });
  } catch (error) {
    console.error('移除租户用户错误:', error);
    res.status(500).json({
      success: false,
      message: '移除租户用户失败'
    });
  }
};

// 获取当前用户所属的租户
const getUserTenants = async (req, res) => {
  try {
    const { userId } = req.user;
    
    const result = await pool.query(`
      SELECT t.id, t.name, t.description, t.is_active
      FROM tenant_users tu
      JOIN tenants t ON tu.tenant_id = t.id
      WHERE tu.user_id = $1 AND t.is_active = true
    `, [userId]);
    
    res.json({
      success: true,
      tenants: result.rows
    });
  } catch (error) {
    console.error('获取用户租户错误:', error);
    res.status(500).json({
      success: false,
      message: '获取用户租户失败'
    });
  }
};

module.exports = {
  getTenants,
  createTenant,
  getTenantDetails,
  updateTenant,
  deleteTenant,
  getTenantUsers,
  addTenantUser,
  removeTenantUser,
  getUserTenants
};