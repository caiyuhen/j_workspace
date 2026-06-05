# MEMORY.md - 蔡宇恒个人项目记忆库

## 一、个人基本信息

### 身份信息
- **姓名**: 蔡宇恒 (Cai Yuheng)
- **邮箱**: caiyuheng81@outlook.com
- **所在地**: 中国 Windows 10 环境
- **工作领域**: 医疗健康 AI 行业

### 技术环境
- **操作系统**: Windows 10
- **Shell**: Git Bash / MSYS (使用 POSIX 语法)
- **路径格式**: 
  - 支持 `/c/Users/Administrator/...` 格式
  - 支持 `C:\Users\Administrator\...` 格式
- **用户目录**: `C:\Users\Administrator`
- **工作目录**: `C:\Users\Administrator\.hermes\hermes-agent`

### 文件存储
- **主要工作目录**: `d:\workspace\doc\`
- **语言偏好**: 中文
- **输出偏好**: 所有项目输出文件默认保存到该目录

---

## 二、核心项目：临床试验 SaaS 平台

### 项目名称
**医疗临床试验管理平台** (Clinical Trial Management Platform)

### 产品定位
面向中国医疗市场的临床试验全流程 SaaS 系统，包含：
1. CTMS (临床试验管理系统)
2. EDC (电子数据采集系统)
3. IWRS (交互式随机应答系统)
4. 医生个人患者病历夹

### 技术架构要求

#### 数据库
- **类型**: PostgreSQL (多租户架构)
- **标准**: 
  - CDISC 标准 (CDASH 数据采集、SDTM 数据模型、ADaM 分析数据)
  - 符合 FDA/EMA 21 CFR Part 11 合规要求

#### 系统架构
- **架构模式**: 微服务架构
- **部署方式**: SaaS 多租户
- **统一数据库**: 所有系统共享数据库，通过租户 ID 隔离

### 核心功能模块

#### 1. CTMS (临床试验管理系统)
- **试验项目管理**
  - 试验创建、阶段管理、时间线规划
  - 预算管理和成本控制
  - 文档管理 (eTMF)
  
- **中心管理 (Site Management)**
  - 研究中心信息维护
  - 研究者信息管理
  - 中心资质审核
  
- **eTMF (电子试验主文档)**
  - 文档在线编辑、版本控制
  - 审批流程管理
  - 合规性检查
  
- **工时管理系统**
  - 项目工时填报
  - 工时审核流程
  - 资源分配与利用率分析

#### 2. EDC (电子数据采集系统)
- **eCRF 表单设计器**
  - 拖拽式表单设计界面
  - 字段类型：文本、数字、日期、下拉选择、单选、多选等
  - 逻辑验证规则配置
  - 自动校验：中英文命名、数据类型、必填项
  - CDASH 标准字段映射
  
- **数据录入界面**
  - 患者数据在线录入
  - 数据编辑历史追踪
  - 疑问 (Query) 管理流程
  - 数据审核工作流
  
- **数据管理**
  - 数据导出：CDISC SDTM 格式
  - 数据验证规则引擎
  - 数据质量监控报告
  
- **数据库设计**
  - 符合 SDTM 标准的数据模型
  - 支持 ADaM 分析数据导出
  - 审计追踪 (Audit Trail)

#### 3. IWRS (交互式随机应答系统)
- **随机化设计**
  - 简单随机、分层随机、动态随机
  - 区组随机化 (Block Randomization)
  - 动态自适应随机化
  
- **药物管理**
  - 药物库存管理
  - 药物分配与追踪
  - 药物回收管理
  
- **入组流程**
  - 受试者入组/排除标准检查
  - 实时随机化分配
  - 药物配送管理

#### 4. 医生个人患者病历夹
- **患者数据管理**
  - 患者档案建立
  - 诊疗记录管理
  - 检查结果整合
  
- **自定义表单设计**
  - 拖拽式表单设计器
  - 引用 EDC 已有表单模板
  - 个人化数据采集字段
  
- **数据隐私**
  - 患者数据脱敏
  - 访问权限控制
  - 数据加密存储

### 技术实现细节

#### PostgreSQL 多租户设计
```sql
-- 租户表
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY,
    tenant_name VARCHAR(100) NOT NULL,
    subscription_tier VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 所有业务表包含 tenant_id
CREATE TABLE patients (
    patient_id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    patient_code VARCHAR(50) NOT NULL,
    -- ... 其他字段
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);
```

#### CDISC 标准实现
- **CDASH**: 数据采集表单字段命名规范
- **SDTM**: 研究数据表结构标准
- **ADaM**: 分析数据集定义
- **Define.xml**: 元数据描述

#### API 设计
- RESTful API
- OpenAPI 3.0 规范
- JWT 身份验证
- 租户隔离 API 网关

### 开发计划

#### 第一阶段 (1-6 个月)
- EDC 核心功能
- eCRF 表单设计器
- 基础数据录入
- PostgreSQL 多租户架构

#### 第二阶段 (7-12 个月)
- CTMS 模块
- eTMF 文档管理
- 工时管理系统
- 基础 IWRS 功能

#### 第三阶段 (13-18 个月)
- 完整 IWRS 功能
- 医生个人病历夹
- 高级数据分析
- CDISC 标准导出

### 预算估算
- **总预算**: 1000-1500 万人民币
- **人力成本**: 800-1200 万 (60-80 人团队，18 个月)
- **基础设施**: 100-200 万 (服务器、云服务)
- **合规认证**: 100-200 万 (FDA 21 CFR Part 11、GCP 认证)
- **其他**: 100-200 万 (培训、市场推广)

### 合规认证要求
- **FDA 21 CFR Part 11**: 电子记录/电子签名
- **GDPR**: 欧洲数据保护法规
- **中国 NMPA**: 医疗器械软件认证
- **GCP**: 药物临床试验质量管理规范
- **HIPAA**: 患者隐私保护 (如拓展国际市场)

---

## 三、医疗 AI 产品矩阵

### 产品列表
1. **EDC 系统** - 临床试验数据采集
2. **患者健康管理平台** - 慢性病管理、随访
3. **数字孪生患者** - 患者虚拟模型、病情预测
4. **数字孪生医生** - 医生工作流程优化
5. **RL 增强医疗 LLM** - 基于强化学习的医疗对话系统
   - 基础模型：Qwen 系列
   - 应用场景：医疗咨询、病历生成、诊疗建议

### 中国市场战略
- **目标客户**: 药企、CRO 公司、医院、研究者
- **合作伙伴**: 中国移动 (基础设施、算力支持)
- **盈利模式**: 
  - SaaS 订阅费
  - 按试验项目收费
  - 增值服务 (数据分析、定制开发)

### 快速变现策略
1. 优先开发 EDC 和 CTMS 核心功能
2. 聚焦中小型 CRO 公司市场
3. 提供中国本地化服务
4. 与医院合作试点项目
5. 申请医疗器械认证提升竞争力

---

## 四、工作习惯与偏好

### 沟通偏好
- **语言**: 中文优先
- **回复风格**: 简洁、直接、事实导向
- **技术细节**: 需要提供具体命令、代码示例

### 文档管理
- **所有输出文件**: 保存到 `d:\workspace\doc\`
- **文件命名**: 使用中文标题，便于理解
- **版本控制**: 重要文档需包含版本号

### 项目要求
- **完整性**: 文档需包含完整功能、技术设计、实施细节
- **标准化**: 遵循行业规范 (CDISC、GCP 等)
- **实用性**: 可直接指导开发和实施

### 工具使用
- **数据库**: PostgreSQL
- **微服务**: 容器化部署
- **API**: RESTful + OpenAPI
- **前端**: 现代化 UI 框架
- **后端**: 可扩展的微服务架构

---

## 五、重要参考信息

### 服务器信息
- **IP**: 36.213.1.249
- **SSH**: `ssh -i d:/v100_ed caiyuheng@36.213.1.249`
- **配置**:
  - CPU: Intel Xeon Gold 6248R (48 核 96 线程)
  - 内存：754 GB
  - GPU: 8x NVIDIA A100 (40GB)
  - 存储：多 NVMe SSD

### 行业标准
- **CDISC**: Clinical Data Interchange Standards Consortium
- **CDASH**: Clinical Data Acquisition Standards Harmonization
- **SDTM**: Study Data Tabulation Model
- **ADaM**: Analysis Data Model
- **GCP**: Good Clinical Practice
- **21 CFR Part 11**: FDA 电子记录规范

### 关键联系人
- **技术团队**: 需要组建 60-80 人开发团队
- **医疗专家**: 需要临床试验专家顾问
- **合规专家**: FDA/NMPA 认证咨询

---

## 六、待办事项与进度追踪

### 已完成
- [x] 产品设计文档创建
- [x] 技术架构规划
- [x] 预算估算

### 进行中
- [ ] 详细技术设计文档
- [ ] 数据库 ER 图设计
- [ ] API 接口文档

### 待开始
- [ ] 原型开发
- [ ] 团队组建
- [ ] 服务器环境配置

### 需要关注的风险
- CDISC 标准合规性
- 数据安全与隐私保护
- 中国本地化适配
- 竞争市场分析

---

*最后更新：2026 年*  
*维护人：蔡宇恒*
