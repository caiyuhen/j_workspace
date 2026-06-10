<template>
  <div class="role-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增角色
          </el-button>
        </div>
      </template>

      <el-table :data="roleList" v-loading="loading">
        <el-table-column prop="roleCode" label="角色编码" width="150" />
        <el-table-column prop="roleName" label="角色名称" width="150" />
        <el-table-column prop="roleType" label="角色类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.roleType === 'SYSTEM' ? 'danger' : 'info'">
              {{ row.roleType === 'SYSTEM' ? '系统预设' : '自定义' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handlePermission(row)">权限</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 权限配置弹窗 -->
    <el-dialog v-model="permissionVisible" title="权限配置" width="600px">
      <el-tree
        :data="permissionTree"
        show-checkbox
        default-expand-all
        node-key="id"
        :props="{ label: 'permName' }"
      />
      <template #footer>
        <el-button @click="permissionVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSavePermission">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const permissionVisible = ref(false)

const roleList = ref([
  { roleCode: 'SUPER_ADMIN', roleName: '超级管理员', roleType: 'SYSTEM', description: '系统最高权限', status: 1 },
  { roleCode: 'ORG_ADMIN', roleName: '机构管理员', roleType: 'SYSTEM', description: '机构级别管理员', status: 1 },
  { roleCode: 'DATA_ADMIN', roleName: '数据管理员', roleType: 'SYSTEM', description: '数据治理管理员', status: 1 },
  { roleCode: 'DATA_ANALYST', roleName: '数据分析师', roleType: 'SYSTEM', description: '数据分析人员', status: 1 },
  { roleCode: 'DOCTOR', roleName: '医师', roleType: 'SYSTEM', description: '中医医师', status: 1 },
  { roleCode: 'RESEARCHER', roleName: '科研人员', roleType: 'SYSTEM', description: '科研人员', status: 1 },
])

const permissionTree = ref([
  {
    id: 1,
    permName: '数据治理',
    children: [
      { id: 11, permName: '元数据管理' },
      { id: 12, permName: '数据质量' },
      { id: 13, permName: '数据标准' }
    ]
  },
  {
    id: 2,
    permName: '数据资产',
    children: [
      { id: 21, permName: '资产目录' },
      { id: 22, permName: '资产管理' }
    ]
  },
  {
    id: 3,
    permName: 'AI应用',
    children: [
      { id: 31, permName: '知识图谱' },
      { id: 32, permName: '智能诊断' }
    ]
  }
])

const handleAdd = () => {
  ElMessage.info('新增角色')
}

const handleEdit = (row) => {
  ElMessage.info('编辑角色: ' + row.roleName)
}

const handlePermission = (row) => {
  permissionVisible.value = true
  ElMessage.info('配置角色权限: ' + row.roleName)
}

const handleSavePermission = () => {
  permissionVisible.value = false
  ElMessage.success('权限配置保存成功')
}

const handleDelete = (row) => {
  if (row.roleType === 'SYSTEM') {
    ElMessage.warning('系统预设角色不能删除')
    return
  }
  ElMessageBox.confirm('确认删除该角色?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('删除成功')
  })
}
</script>

<style scoped>
.role-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
