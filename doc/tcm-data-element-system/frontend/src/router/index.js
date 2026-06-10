import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'governance',
        name: 'Governance',
        redirect: '/governance/metadata',
        meta: { title: '数据治理', icon: 'DataLine' },
        children: [
          {
            path: 'metadata',
            name: 'MetaData',
            component: () => import('@/views/governance/metadata.vue'),
            meta: { title: '元数据管理' }
          },
          {
            path: 'quality',
            name: 'Quality',
            component: () => import('@/views/governance/quality.vue'),
            meta: { title: '数据质量' }
          },
          {
            path: 'standard',
            name: 'Standard',
            component: () => import('@/views/governance/standard.vue'),
            meta: { title: '数据标准' }
          }
        ]
      },
      {
        path: 'asset',
        name: 'Asset',
        redirect: '/asset/catalog',
        meta: { title: '数据资产', icon: 'Coin' },
        children: [
          {
            path: 'catalog',
            name: 'AssetCatalog',
            component: () => import('@/views/asset/catalog.vue'),
            meta: { title: '资产目录' }
          },
          {
            path: 'management',
            name: 'AssetManagement',
            component: () => import('@/views/asset/management.vue'),
            meta: { title: '资产管理' }
          }
        ]
      },
      {
        path: 'ai',
        name: 'AI',
        redirect: '/ai/kg',
        meta: { title: 'AI应用', icon: 'Cpu' },
        children: [
          {
            path: 'kg',
            name: 'KnowledgeGraph',
            component: () => import('@/views/ai/knowledge-graph.vue'),
            meta: { title: '知识图谱' }
          },
          {
            path: 'diagnosis',
            name: 'Diagnosis',
            component: () => import('@/views/ai/diagnosis.vue'),
            meta: { title: '智能诊断' }
          }
        ]
      },
      {
        path: 'system',
        name: 'System',
        redirect: '/system/user',
        meta: { title: '系统管理', icon: 'Setting' },
        children: [
          {
            path: 'user',
            name: 'User',
            component: () => import('@/views/system/user.vue'),
            meta: { title: '用户管理' }
          },
          {
            path: 'role',
            name: 'Role',
            component: () => import('@/views/system/role.vue'),
            meta: { title: '角色管理' }
          },
          {
            path: 'architecture',
            name: 'Architecture',
            component: () => import('@/views/system/architecture.vue'),
            meta: { title: '系统架构' }
          }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title + ' - 中医数据要素系统'
  }
  next()
})

export default router
