<template>
  <div class="user-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </div>
      </template>

      <el-table :data="userList" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="realName" label="真实姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="orgId" label="所属机构" width="150" />
        <el-table-column prop="title" label="职称" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastLoginTime" label="最后登录" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handleResetPwd(row)">重置密码</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)

const userList = ref([
  { username: 'admin', realName: '系统管理员', phone: '13800138000', email: 'admin@tcm-data.com', orgId: '总部', title: '高级工程师', status: 1, lastLoginTime: '2024-12-10 14:30:00' },
  { username: 'zhangsan', realName: '张三', phone: '13800138001', email: 'zhangsan@tcm-data.com', orgId: '北京中医院', title: '主任医师', status: 1, lastLoginTime: '2024-12-10 10:15:00' },
  { username: 'lisi', realName: '李四', phone: '13800138002', email: 'lisi@tcm-data.com', orgId: '上海中医院', title: '副主任医师', status: 1, lastLoginTime: '2024-12-09 16:45:00' },
])

const handleAdd = () => {
  ElMessage.info('新增用户')
}

const handleEdit = (row) => {
  ElMessage.info('编辑用户: ' + row.realName)
}

const handleResetPwd = (row) => {
  ElMessageBox.confirm('确认重置该用户密码?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('密码重置成功')
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确认删除该用户?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('删除成功')
  })
}
</script>

<style scoped>
.user-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
