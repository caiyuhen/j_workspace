// 工时管理相关API

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