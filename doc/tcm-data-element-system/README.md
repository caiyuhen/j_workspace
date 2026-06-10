# 中医数据要素系统 (TCM Data Element System)

## 项目简介

中医数据要素系统是一个面向中医药行业的数据要素治理与AI应用平台，旨在实现中医药数据的标准化治理、资产化管理、安全流通和AI智能化应用，支撑"数智中医药"战略落地。

## 核心功能

### 1. 数据治理中心
- **元数据管理**：自动采集、血缘追踪、影响分析
- **主数据管理**：患者、医师、药材、方剂、病证等核心主数据
- **数据质量管理**：规则引擎、质量评分、问题闭环
- **数据标准规范**：中医药专属标准库、标准对标分析

### 2. 数据分类分级
- **自动分类分级**：基于内容识别+规则引擎
- **分级管控策略**：访问控制、存储策略、流通管控
- **合规审计**：等保、密评、个人信息保护

### 3. 数据资产管理
- **资产目录**：分层分域的数据资产全景图
- **资产估值**：成本法、收益法、市场法
- **资产入表**：三权分置、成本归集、审计追踪

### 4. AI智能应用
- **知识图谱**：疾病、证型、方剂、中药等实体关系
- **智能辨证**：四诊信息采集、AI辨证推理
- **方剂推荐**：经典方剂推荐、用药禁忌提醒
- **体质辨识**：智能问卷、多模态辨识

## 技术架构

### 后端技术栈
- **框架**：Spring Boot 3.2 + Spring Cloud Alibaba
- **数据库**：MySQL 8.0 + Redis + Neo4j
- **搜索引擎**：Elasticsearch
- **大数据**：Spark + Flink + Doris
- **AI平台**：PyTorch + 大模型推理引擎

### 前端技术栈
- **框架**：Vue 3 + TypeScript
- **UI组件**：Element Plus
- **可视化**：ECharts
- **状态管理**：Pinia
- **路由**：Vue Router

## 快速开始

### 环境要求
- JDK 17+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+
- Neo4j 5.x

### 后端部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd tcm-data-element-system/backend

# 2. 配置数据库
# 修改 application.yml 中的数据库连接信息

# 3. 编译打包
mvn clean package -DskipTests

# 4. 运行
java -jar target/tcm-data-element-system-1.0.0.jar
```

### 前端部署

```bash
# 1. 进入前端目录
cd tcm-data-element-system/frontend

# 2. 安装依赖
npm install

# 3. 开发模式运行
npm run dev

# 4. 生产构建
npm run build
```

### Docker部署

```bash
# 使用Docker Compose一键部署
docker-compose up -d
```

## 项目结构

```
tcm-data-element-system/
├── backend/                    # 后端项目
│   ├── src/main/java/
│   │   └── com/tcm/data/
│   │       ├── controller/     # 控制器层
│   │       ├── service/        # 业务逻辑层
│   │       ├── repository/     # 数据访问层
│   │       ├── entity/         # 实体类
│   │       ├── dto/            # 数据传输对象
│   │       ├── config/         # 配置类
│   │       └── common/         # 公共组件
│   └── src/main/resources/
│       └── db/migration/       # 数据库迁移脚本
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── views/              # 页面视图
│   │   ├── components/         # 公共组件
│   │   ├── api/                # API接口
│   │   ├── stores/             # 状态管理
│   │   └── router/             # 路由配置
│   └── package.json
└── docker-compose.yml          # Docker编排文件
```

## 开发计划

### 第一阶段：基础平台建设（6-8个月）
- [x] 项目基础架构搭建
- [x] 数据库设计与初始化
- [x] 用户权限管理
- [x] 数据治理中心（元数据、主数据、质量）
- [x] 数据标准规范管理
- [x] 数据分类分级管理

### 第二阶段：数据资产与流通平台（4-6个月）
- [ ] 数据资产管理模块
- [ ] 数据目录与智能检索
- [ ] 数据交易与流通管理
- [ ] 隐私计算平台对接
- [ ] 统计分析与大屏

### 第三阶段：AI智能应用（6-8个月）
- [x] 知识图谱构建
- [x] 智能辨证系统
- [ ] 体质辨识系统
- [ ] 名老中医经验传承
- [ ] 中药饮片追溯

### 第四阶段：运营优化（持续）
- [ ] 系统性能优化
- [ ] 数据运营服务
- [ ] 生态合作对接

## 核心团队

- **产品经理**：2人
- **后端开发**：6人
- **前端开发**：3人
- **数据工程师**：4人
- **算法工程师**：6人
- **测试工程师**：2人

## 许可证

Apache License 2.0

## 联系方式

- 邮箱：admin@tcm-data.com
- 官网：https://www.tcm-data.com
