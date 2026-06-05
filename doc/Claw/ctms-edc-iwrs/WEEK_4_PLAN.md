# 第 4 周：核心模块原型开发

**时间**: 2024-05-29 ~ 2024-06-04  
**目标**: 实现三个核心功能原型，打通前后端交互

---

## 🎯 本周任务

### 任务 1: 用户登录页面（React + 认证服务集成）

**优先级**: 🔥🔥🔥 高  
**预计时间**: 4 小时

#### 功能需求
- ✅ 用户登录表单（用户名/密码）
- ✅ 表单验证（前端 + 后端）
- ✅ 调用 Auth Service API
- ✅ JWT Token 存储（localStorage/cookie）
- ✅ 登录成功后跳转
- ✅ 错误提示（账户锁定、密码错误）
- ✅ "记住我"功能
- ✅ 忘记密码链接

#### 技术实现
```typescript
// 前端组件
- src/pages/LoginPage.tsx
- src/components/LoginForm.tsx
- src/hooks/useAuth.ts
- src/store/authStore.ts (Zustand)
- src/api/authApi.ts

// 验证规则
- src/validators/authValidator.ts

// 样式
- src/styles/Login.module.css
```

#### API 集成
```
POST /api/v1/auth/login
- Request: { username, password, rememberMe }
- Response: { accessToken, refreshToken, user }
```

#### 验收标准
- [ ] 能够使用默认账户登录 (admin/Admin@123456)
- [ ] 表单验证正常工作
- [ ] Token 正确存储
- [ ] 登录成功后跳转到首页
- [ ] 错误信息友好提示

---

### 任务 2: eCRF 表单设计器原型

**优先级**: 🔥🔥🔥 高  
**预计时间**: 8 小时

#### 功能需求
- ✅ 拖拽式表单设计器
- ✅ 字段类型支持：
  - 单行文本（String）
  - 多行文本（Text）
  - 数字（Number）
  - 日期（Date）
  - 下拉选择（Select）
  - 单选框（Radio）
  - 复选框（Checkbox）
  - 小数（Decimal）
- ✅ 字段属性配置（标签、必填、默认值、验证规则）
- ✅ 字段排序（上下移动）
- ✅ 字段删除
- ✅ 表单保存（创建 eCRF 模板）
- ✅ 表单列表管理
- ✅ 表单预览

#### 技术实现
```typescript
// 前端组件
- src/pages/FormDesigner.tsx
- src/components/FormFieldPalette.tsx
- src/components/FormCanvas.tsx
- src/components/FieldPropertyPanel.tsx
- src/components/FormFieldRenderer.tsx

// 状态管理
- src/store/formDesignerStore.ts

// API
- src/api/formApi.ts
- src/api/templateApi.ts

// 类型定义
- src/types/form.ts
- src/types/ecrf.ts
```

#### 数据结构（Prisma Schema）
```prisma
model EdcTemplate {
  id          String   @id @default(uuid())
  studyId     String
  name        String
  code        String
  version     String   @default("1.0")
  sections    Json     // 表单 section 配置
  fields      Json     // 字段配置
  validation  Json?    // 验证规则
  status      TemplateStatus
  createdBy   String
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  @@unique([studyId, code])
}

model CrfForm {
  id          String   @id @default(uuid())
  templateId  String
  subjectId   String
  data        Json     // 表单数据
  status      FormStatus
  completedAt DateTime?
  createdAt   DateTime @default(now())
  
  template    EdcTemplate @relation(fields: [templateId], references: [id])
}

model CrfFormField {
  id          String   @id @default(uuid())
  formId      String
  fieldKey    String
  fieldValue  String?
  fieldType   String
  updatedAt   DateTime @updatedAt
  
  form        CrfForm @relation(fields: [formId], references: [id])
  
  @@unique([formId, fieldKey])
}
```

#### 验收标准
- [ ] 能够拖拽字段到画布
- [ ] 能够配置字段属性
- [ ] 能够保存表单模板
- [ ] 能够预览表单
- [ ] 能够管理表单列表

---

### 任务 3: 数据录入页面原型

**优先级**: 🔥🔥 中  
**预计时间**: 6 小时

#### 功能需求
- ✅ 动态渲染 eCRF 表单
- ✅ 支持所有字段类型
- ✅ 表单验证
- ✅ 数据保存（草稿 + 提交）
- ✅ 数据编辑
- ✅ 表单导航（上一页/下一页）
- ✅ 进度提示
- ✅ 数据回显

#### 技术实现
```typescript
// 前端组件
- src/pages/DataEntryPage.tsx
- src/components/DynamicForm.tsx
- src/components/FormSections.tsx
- src/components/FieldComponents/
  - TextField.tsx
  - NumberField.tsx
  - DateField.tsx
  - SelectField.tsx
  - RadioField.tsx
  - CheckboxField.tsx

// 状态管理
- src/store/dataEntryStore.ts

// API
- src/api/dataEntryApi.ts

// 工具函数
- src/utils/formValidator.ts
- src/utils/formRenderer.ts
```

#### API 设计
```
GET  /api/v1/templates/:templateId      # 获取表单模板
GET  /api/v1/forms/:formId              # 获取表单数据
POST /api/v1/forms                      # 创建表单
PUT  /api/v1/forms/:formId              # 更新表单
POST /api/v1/forms/:formId/save-draft   # 保存草稿
POST /api/v1/forms/:formId/submit       # 提交表单
```

#### 验收标准
- [ ] 能够加载 eCRF 模板并渲染
- [ ] 能够录入数据
- [ ] 能够保存草稿
- [ ] 能够提交表单
- [ ] 能够编辑已有数据
- [ ] 表单验证正常工作

---

## 📋 开发顺序

```
Day 1-2: 任务 1 - 用户登录
  ├─ 搭建前端基础架构
  ├─ 实现登录组件
  ├─ 集成 Auth Service
  └─ 测试登录功能

Day 3-4: 任务 2 - eCRF 表单设计器
  ├─ 设计拖拽组件
  ├─ 实现字段配置
  ├─ 创建后端 API
  └─ 测试表单保存

Day 5-6: 任务 3 - 数据录入页面
  ├─ 实现动态表单渲染
  ├─ 集成数据保存
  ├─ 添加表单验证
  └─ 端到端测试
```

---

## 🛠️ 技术栈

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Ant Design
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **表单验证**: Zod
- **路由**: React Router v6
- **图标**: @ant-design/icons

### 后端（EDC Service）
- **框架**: Express.js + TypeScript
- **ORM**: Prisma
- **数据库**: PostgreSQL
- **验证**: Zod
- **JWT 认证**: 复用 Auth Service

---

## 📦 需要安装的依赖

### 前端
```bash
npm install antd @ant-design/icons axios zustand react-router-dom zod @dnd-kit/core @dnd-kit/sortable
```

### 后端
```bash
# 在 edc-service 目录
npm install @prisma/client express zod jsonwebtoken
```

---

## 🎨 设计参考

### 登录页面
- 简洁的居中卡片设计
- CTMS 品牌色（蓝色）
- 响应式布局

### 表单设计器
- 左侧：字段工具栏
- 中间：表单画布
- 右侧：属性面板
- 顶部：工具栏（保存、预览、取消）

### 数据录入
- 顶部：患者信息
- 主体：分 section 的表单
- 底部：导航按钮（上一页、保存、提交）

---

## ✅ 完成标准

本周结束时，应该能够：
1. ✅ 使用浏览器登录系统
2. ✅ 创建一个新的 eCRF 表单模板
3. ✅ 使用创建的模板录入数据
4. ✅ 保存和提交数据

---

## 📝 备注

- 优先保证功能可用，UI 可以后续优化
- 使用 mock 数据测试，逐步替换为真实 API
- 保持代码简洁，便于后续重构
- 及时提交 Git 版本

---

*创建时间：2024-05-29*  
*版本：1.0.0*
