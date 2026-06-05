临床试验 SaaS 平台产品设计方案
================================

版本：v1.0
创建日期：2026 年
创建人：蔡宇恒
文档位置：d:\workspace\doc\clinical-trial-platform-product-design.md

=================================
目录
=================================

1. 项目概述
2. 产品定位与目标用户
3. 系统总体架构
4. 四大核心系统功能设计
   4.1 CTMS（临床试验管理系统）
   4.2 EDC（电子数据采集系统）
   4.3 IWRS（交互式随机化与药物供应系统）
   4.4 医生个人患者病历夹（ePMR）
5. CDISC 标准实现方案
6. 数据库设计
7. SaaS 多租户架构设计
8. AI 自动化测试方案
9. 技术栈选型
10. 实施计划

=================================
1. 项目概述
=================================

1.1 项目背景

随着中国医疗行业数字化转型加速，临床试验管理需求日益增长。本项目旨在构建一个符合国际标准的临床试验 SaaS 平台，服务于中国药企、CRO 公司和医疗机构，实现临床试验全流程数字化管理。

1.2 核心价值主张

- 符合国际标准（CDISC、FDA 21 CFR Part 11、GCP、NMPA）
- 一体化平台（CTMS+EDC+IWRS+ 病历夹）
- 拖拽式表单设计（零编码）
- 微服务 SaaS 架构（多租户、可扩展）
- AI 驱动的自动化测试与质量管理

1.3 产品特点

✓ 统一数据库架构，数据互通
✓ CDASH/SDTM/ADaM标准全自动映射
✓ eTMF 在线编辑与审批
✓ 工时管理系统
✓ 医生个人化患者病历夹
✓ 支持中国本土化需求

=================================
2. 产品定位与目标用户
=================================

2.1 目标用户群体

┌─────────────────────────────────────────────────────┐
│ 1. 制药企业                                          │
│    - 新药研发部门                                    │
│    - 临床试验管理部门                                │
│    - 医学部                                          │
│                                                      │
│ 2. CRO 公司                                          │
│    - 项目经理                                        │
│    - 临床监查员 (CRA)                                │
│    - 数据管理员 (DM)                                 │
│    - 统计师                                          │
│                                                      │
│ 3. 医院研究中心                                     │
│    - 主要研究者 (PI)                                 │
│    - 研究护士                                        │
│    - 研究者                                          │
│                                                      │
│ 4. 医生个人                                          │
│    - 专科医生                                        │
│    - 研究者                                          │
│    - 患者数据管理需求                                │
└─────────────────────────────────────────────────────┘

2.2 商业模式

- SaaS 订阅模式（按租户、按功能模块）
- 基础版：EDC 核心功能
- 专业版：CTMS+EDC+IWRS
- 企业版：全功能 + 医生病历夹 + 定制开发
- 按用户数/试验数量计费

=================================
3. 系统总体架构
=================================

3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Web 端   │  │  移动端   │  │  平板端   │  │  API 接口  │        │
│  │ React    │  │  React   │  │  React   │  │  RESTful  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                       API 网关层                                │
│  Kong/Nginx + JWT 认证 + 限流 + 日志 + 路由                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                     服务注册/配置中心                            │
│                      Nacos (服务发现 + 配置管理)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                       微服务层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ CTMS 服务  │  │  EDC 服务  │  │  IWRS 服务 │  │病历夹服务 │        │
│  │          │  │          │  │          │  │          │        │
│  │试验管理   │  │表单设计   │  │随机化    │  │患者管理  │        │
│  │中心管理   │  │数据录入   │  │药物管理  │  │诊疗记录  │        │
│  │eTMF       │  │数据验证   │  │入组流程  │  │自定义表单│        │
│  │工时管理   │  │审计追踪   │  │          │  │          │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│           │             │             │             │            │
│           └─────────────┴───────┬─────┴─────────────┘            │
└─────────────────────────────────┼─────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────┐
│                      服务治理层                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  熔断    │  │  限流    │  │  追踪    │  │  消息队列 │         │
│  │Sentinel  │  │Sentinel  │  │SkyWalking│  │RabbitMQ  │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────┼─────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────┐
│                      数据访问层                                  │
│      MyBatis-Plus + 多租户隔离 + 连接池 (HikariCP)                 │
└─────────────────────────────────┼─────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────┐
│                    数据存储层                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │PostgreSQL│  │  Redis   │  │  MinIO   │  │ Elasticsearch│       │
│  │  业务数据 │  │  缓存    │  │  文件存储 │  │  日志搜索  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

3.2 技术栈选型

后端技术栈：
- 开发语言：Java 17
- 微服务框架：Spring Boot 3.x + Spring Cloud Alibaba
- 服务注册/配置：Nacos
- API 网关：Spring Cloud Gateway
- 服务调用：OpenFeign
- 熔断降级：Sentinel
- 日志追踪：SkyWalking
- ORM 框架：MyBatis-Plus
- 数据库：PostgreSQL 15+
- 缓存：Redis 7.x
- 消息队列：RabbitMQ / Kafka
- 文件存储：MinIO

前端技术栈：
- 框架：React 18 + TypeScript
- UI 库：Ant Design 5
- 状态管理：Zustand
- HTTP 客户端：Axios
- 表单库：React Hook Form
- 数据可视化：ECharts
- 拖拽库：React DnD
- 富文本编辑器：Quill / Monaco Editor

DevOps 工具：
- 容器化：Docker + Kubernetes
- CI/CD：Jenkins / GitLab CI
- 监控：Prometheus + Grafana
- 日志：ELK Stack
- 代码质量：SonarQube
- 测试：Jest + Cypress + Allure

=================================
4. 四大核心系统功能设计
=================================

4.1 CTMS（临床试验管理系统）
=================================

4.1.1 试验项目管理

核心功能：
- 试验创建与规划
  * 试验基本信息：名称、方案编号、申办方、研究类型（I-IV 期）
  * 试验阶段管理：启动期、入组期、治疗期、随访期、结束期
  * 时间线规划：关键里程碑设置与追踪
  * 预算规划：各阶段预算分配与控制
  * 资源分配：人员、设备、场地分配

- 项目看板
  * 可视化项目进度仪表板
  * 关键指标监控：入组率、数据完成率、问题数
  * 风险预警机制
  * 甘特图展示（里程碑、任务依赖）

- 文档管理（eTMF 集成）
  * 核心文档库：方案、知情同意书、investigator brochure
  * 文档版本控制
  * 文档审批工作流
  * 文档模板管理

4.1.2 研究中心（Site）管理

核心功能：
- 中心信息管理
  * 研究中心基本信息：名称、地址、联系方式
  * 中心资质信息：GCP 资质、伦理委员会批准
  * 研究者信息：主要研究者（PI）、亚研究者（Sub-I）
  * 中心联系人管理

- 中心筛选与评估
  * 中心筛选标准配置
  * 中心评估打分
  * 中心实地考察记录
  * 中心启动状态管理

- 中心绩效监控
  * 入组速度监控
  * 数据质量评估
  * 研究中心排名
  * 绩效报告生成

4.1.3 eTMF（电子试验主文档）

核心功能：
- 文档在线编辑
  * 支持 Word、Excel、PDF 在线编辑
  * 文档版本对比
  * 修订痕迹追踪
  * 多人协作编辑

- 文档审批流程
  * 多级审批配置
  * 审批通知与提醒
  * 审批意见记录
  * 审批状态追踪

- 合规性检查
  * eTMF 标准检查（FDA 要求）
  * 文档完整性验证
  * 缺失文档预警
  * 合规性报告生成

- 文档分类与索引
  * ISTAF 标准分类
  * 全文搜索
  * 标签管理
  * 文档关联

4.1.4 工时管理系统

核心功能：
- 工时填报
  * 按项目/任务填报工时
  * 工时类型：开发、测试、会议、培训等
  * 日报/周报/月报
  * 工时附件上传

- 工时审核
  * 多级审核流程
  * 审核意见记录
  * 审核状态追踪
  * 异常工时预警

- 资源管理
  * 项目人员配置
  * 人员技能标签
  * 资源利用率分析
  * 人员负荷监控

- 工时统计与分析
  * 项目工时汇总
  * 部门工时统计
  * 成本核算
  * 效率分析报告

4.2 EDC（电子数据采集系统）
=================================

4.2.1 eCRF 表单设计器（拖拽式）

设计器界面布局：

```
┌────────────────────────────────────────────────────────────────┐
│  工具栏：[文件] [编辑] [视图] [帮助] | 表单名称：v1.0 | [保存][预览][发布] │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌─────────────────────────────┐  ┌────────┐ │
│  │  组件库      │  │         画布区域             │  │ 属性面板│ │
│  │              │  │                              │  │        │ │
│  │ 基础字段     │  │  ┌───────────────────────┐  │  │ 基础属性 │ │
│  │  - 文本框    │  │  │      表单标题          │  │  │        │ │
│  │  - 数字框    │  │  ├───────────────────────┤  │  │ 字段编码│ │
│  │  - 日期选择  │  │  │      表单内容          │  │  │ 字段名称│ │
│  │  - 下拉框    │  │  │   [拖拽放置区域]       │  │  │ 字段类型│ │
│  │  - 单选/多选 │  │  │                        │  │  │ 必填/可选││
│  │              │  │  └───────────────────────┘  │  │ 验证规则│ │
│  │ 高级字段     │  │                              │  │ CDASH 映射││
│  │  - 文本域    │  │                              │  │ 显示设置│ │
│  │  - 图片上传  │  │                              │  │ 布局配置│ │
│  │  - 签名      │  │                              │  │        │ │
│  │  - 表格      │  │                              │  │        │ │
│  │              │  │                              │  │        │ │
│  │ 医学字段     │  │                              │  │        │ │
│  │  - 实验室检查│  │                              │  │        │ │
│  │  - 生命体征  │  │                              │  │        │ │
│  │  - 不良事件  │  │                              │  │        │ │
│  └──────────────┘  └─────────────────────────────┘  └────────┘ │
│                                                                 │
│  底部状态栏：已保存 | 15 个字段 | 3 个验证规则 | 100% 显示比例        │
└────────────────────────────────────────────────────────────────┘
```

核心功能：
- 可视化表单画布
  * 表单元素拖拽放置
  * 实时预览功能
  * 多表单支持（问卷式、步骤式）

- 字段类型库
  * 文本字段：单行、多行
  * 数值字段：整数、浮点数
  * 日期时间字段：日期、时间、日期时间
  * 选择字段：下拉选择、单选按钮、多选框
  * 医学字段：体检项目、实验室结果、不良事件
  * 图片字段：图片上传、签名
  * 逻辑字段：计算字段、条件显示

- CDASH 标准映射
  * 字段英文名自动验证
  * 字段中文名支持
  * CDASH 标准字段库
  * 字段属性配置（必填、只读、可选）
  * 数据域映射（Visit、Param、Timing 等）

- 逻辑验证规则
  * 必填字段校验
  * 数据范围校验
  * 逻辑一致性校验
  * 交叉验证（不同页面/表单间）
  * 自定义规则配置（公式、脚本）

- 表单版本管理
  * 表单版本历史
  * 版本差异对比
  * 版本回滚
  * 已录入数据迁移

4.2.2 数据录入界面

核心功能：
- 患者数据录入
  * 患者选择/创建
  * 访视管理（Screening、Baseline、Visit1、Visit2...）
  * 表单填写引导
  * 自动填充（基于历史数据）
  * 草稿保存

- 数据录入工作流
  * 数据录入员分配
  * 数据审核流程（双人录入、单录入双审核）
  * 数据锁定机制
  * 数据解锁审批

- 疑问（Query）管理
  * 疑问创建与分配
  * 疑问状态追踪（Open、Resolved、Closed）
  * 疑问与数据行关联
  * 疑问沟通记录
  * 批量疑问处理

- 数据审核
  * 审核检查点配置
  * 数据质量规则
  * 审核意见记录
  * 审核报告生成

4.2.3 数据管理功能

核心功能：
- 数据导入/导出
  * 支持 Excel、CSV 导入
  * CDISC SDTM 格式导出
  * ADaM 格式导出
  * Define.xml 导出
  * 数据验证预览

- 数据验证引擎
  * 内置验证规则库
  * 自定义验证规则
  * 批量数据验证
  * 验证报告生成
  * 异常数据标记

- 数据质量监控
  * 数据完整性检查
  * 数据一致性检查
  * 异常值检测
  * 趋势分析报告
  * 数据质量仪表板

- 审计追踪（Audit Trail）
  * 所有数据操作记录
  * 操作人、时间、IP 记录
  * 修改前后值对比
  * 不可篡改存储
  * 符合 21 CFR Part 11

4.2.4 SDTM 数据库设计

核心功能：
- 标准域表设计
  * DM（受试者信息）
  * SD（筛选登记）
  * CE（接触史）
  * EX（暴露）
  * GS（基因亚组）
  * LB（实验室检查）
  * AE（不良事件）
  * DS（生存期）
  * ST（生存时间）
  * MH（病史）
  * CM（合并用药）
  * VS（生命体征）

- 标准变量命名
  * 遵循 SDTM 命名规范
  * 变量类型定义
  * 值集管理

- SDTM 验证工具
  * CDISCCheck 集成
  * 标准合规性检查
  * 错误报告生成

4.3 IWRS（交互式随机化与药物供应系统）
=================================

4.3.1 随机化设计

核心功能：
- 随机化方法
  * 简单随机化
  * 分层随机化（按中心、疾病严重程度等分层）
  * 区组随机化 (Block Randomization)
  * 动态自适应随机化
  * 最小化法 (Minimization)

- 随机化方案配置
  * 治疗组配置（对照组、试验组 A、试验组 B...）
  * 分配比例配置（1:1, 2:1, 3:1 等）
  * 区组大小设置
  * 分层因素设置
  * 随机种子管理

- 随机化表管理
  * 随机化表生成
  * 随机化表查看（仅限授权人员）
  * 随机化表冻结
  * 随机化表变更审批

4.3.2 药物管理

核心功能：
- 药物库存管理
  * 药物编码管理
  * 药物批次管理
  * 药物库存数量管理
  * 药物有效期管理
  * 药物预警（库存不足、即将过期）

- 药物分配
  * 基于随机化结果分配药物
  * 药物配送管理
  * 药物接收确认
  * 药物使用记录

- 药物回收与销毁
  * 剩余药物回收
  * 药物销毁记录
  * 回收数量核对
  * 销毁审批流程

4.3.3 入组流程

核心功能：
- 受试者管理
  * 受试者筛选
  * 入组/排除标准检查
  * 知情同意书签署确认
  * 受试者编号分配（符合 ICH GCP）

- 随机化分配
  * 实时随机化请求
  * 随机化结果返回
  * 分配结果记录
  * 随机化不可逆保证

- 入组状态跟踪
  * 入组进度监控
  * 入组率统计
  * 入组预测分析
  * 入组瓶颈识别

- 入组流程自动化
  * 自动检查入组标准
  * 自动分配随机号
  * 自动通知相关人员
  * 自动更新入组状态

4.3.4 药物供应管理

核心功能：
- 药物供应预测
  * 基于入组预测的药物需求
  * 中心级别药物需求预测
  * 时间维度需求预测
  * 预警机制

- 药物供应计划
  * 药物采购计划
  * 药物调拨计划
  * 物流跟踪
  * 到货确认

- 药物使用记录
  * 每次用药记录
  * 用药依从性计算
  * 药物消耗统计
  * 药物使用偏差分析

4.3.5 接口集成

核心功能：
- 与 EDC 集成
  * 受试者信息同步
  * 入组状态同步
  * 数据一致性保证
  * 双向数据流

- 与 CTMS 集成
  * 中心信息同步
  * 项目进度同步
  * 资源分配同步

- 外部系统接口
  * 短信平台接口
  * 邮件服务器接口
  * 医院 HIS 系统接口（可选）

4.4 医生个人患者病历夹（ePMR）
=================================

4.4.1 患者数据管理

核心功能：
- 患者档案管理
  * 患者基本信息录入
  * 患者照片管理
  * 患者关联试验/项目
  * 患者生命周期管理

- 诊疗记录
  * 病史采集
  * 体格检查记录
  * 诊断记录
  * 治疗方案记录
  * 随访记录

- 检查结果整合
  * 实验室检查（血液、尿液等）
  * 影像学检查（CT、MRI、X 光等）
  * 病理检查报告
  * 基因检测结果
  * 检查结果趋势图

- 药物处方管理
  * 处方开具
  * 用药记录
  * 用药依从性追踪
  * 药物相互作用检查

4.4.2 自定义表单设计

核心功能：
- 拖拽式表单设计器
  * 与 EDC 表单设计器相同界面
  * 个人化表单创建
  * 表单模板库
  * 表单版本管理

- 引用 EDC 模板
  * 直接从 EDC 导入表单模板
  * 模板自定义修改
  * 模板版本同步
  * 模板共享管理

- 个人化字段
  * 医生自定义字段
  * 患者自定义字段
  * 自由文本字段
  * 多媒体字段（照片、视频）

- 表单逻辑
  * 条件显示
  * 必填校验
  * 数据计算
  * 数据关联

4.4.3 数据隐私与安全

核心功能：
- 患者数据脱敏
  * 自动脱敏规则
  * 手动脱敏操作
  * 脱敏级别设置
  * 脱敏审计

- 访问权限控制
  * 医生权限（只能看自己的患者）
  * 患者授权管理
  * 访问日志记录
  * 异常访问预警

- 数据加密
  * 传输加密（HTTPS/TLS）
  * 存储加密（AES-256）
  * 密钥管理
  * 加密审计

- 数据备份与恢复
  * 自动备份
  * 手动备份
  * 恢复测试
  * 备份策略配置

4.4.4 医生工作台

核心功能：
- 患者列表
  * 患者列表筛选（按试验、入组时间、状态等）
  * 患者状态标记
  * 快速导航
  * 批量操作

- 待办事项
  * 待录入数据提醒
  * 待审核事项
  * 待处理疑问
  * 随访提醒

- 数据概览
  * 患者关键数据汇总
  * 数据完整性统计
  * 异常数据提醒
  * 趋势分析

- 快捷操作
  * 快速录入
  * 快速搜索
  * 快捷报告
  * 常用模板

4.4.5 高级功能

核心功能：
- 数据可视化
  * 患者时间线
  * 关键指标趋势图
  * 实验室结果趋势
  * 用药记录时间轴

- 智能提醒
  * 随访时间提醒
  * 数据录入提醒
  * 异常数据提醒
  * 重要日期提醒

- 数据导出
  * 患者报告导出（PDF）
  * 数据导出（Excel、CSV）
  * 统计报告导出
  * 自定义导出模板

- 多端支持
  * Web 端（医生工作台）
  * 移动端（医生 APP）
  * 平板适配
  * PDA 支持（可选）

=================================
5. CDISC 标准实现方案
=================================

5.1 CDISC 标准概述

CDISC (Clinical Data Interchange Standards Consortium) 是临床数据交换标准协会，制定临床试验数据标准。

核心标准：
- CDASH (Clinical Data Acquisition Standards Harmonization): 数据采集标准
- SDTM (Study Data Tabulation Model): 研究数据表模型
- ADaM (Analysis Data Model): 分析数据模型
- Define.xml: 元数据描述标准

5.2 标准层级关系

```
┌─────────────────────────────────────────────────────────────┐
│                    Define.xml (元数据)                       │
├─────────────────────────────────────────────────────────────┤
│                    ADaM (分析数据)                           │
├─────────────────────────────────────────────────────────────┤
│                    SDTM (提交数据)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  DM 域   │ │  AE 域   │ │  LB 域   │ │  EX 域   │ ...      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    CDASH (采集数据)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ eCRF 表单 │ │ eCRF 表单 │ │ eCRF 表单 │ │ eCRF 表单 │          │
│  │  设计   │ │  采集   │ │  录入   │ │  验证   │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
```

5.3 CDASH 数据采集标准

5.3.1 命名规范

原则：
1. 使用英文大写字母
2. 使用语义清晰的缩写
3. 避免使用特殊字符
4. 长度限制：4-30 个字符
5. 遵循 SDTM 变量命名规范

示例：
✅ 正确：SUBJID, AGE, SEX, RANDDT, WEIGHT, HEIGHT
❌ 错误：subject_id, age (小写), PatientID, 1AGE

5.3.2 数据类型

```javascript
const CDASHTypes = {
  // 字符类型
  Character: {
    examples: ['SUBJID', 'SEX', 'RACE', 'ETHNIC'],
    maxLength: '根据 SDTM 定义',
    format: '字母、数字、空格、连字符'
  },
  
  // 数值类型
  Numeric: {
    examples: ['AGE', 'WEIGHT', 'HEIGHT', 'BMI'],
    precision: '根据变量定义',
    unit: '根据 SDTM 单位'
  },
  
  // 日期类型
  Date: {
    examples: ['RANDDT', 'BIRTHDT', 'DEATHDT'],
    format: 'YYYY-MM-DD',
    required: '完整日期'
  },
  
  // 日期时间
  DateTime: {
    examples: ['EXSTDTC', 'EXENDTC'],
    format: 'YYYY-MM-DDTHH:mm:ss',
    precision: '可选秒级'
  },
  
  // 布尔类型
  Boolean: {
    examples: ['ISP', 'DTHFL'],
    values: ['Y', 'N'],
    display: ['是/否', 'Yes/No']
  },
  
  // 枚举类型
  Codelist: {
    examples: ['AESEV', 'AEOUT', 'AEREL'],
    standard: 'CDISC 值集',
    values: 'predefined'
  }
};
```

5.3.3 标准字段映射

CDASH → SDTM 映射示例：

| CDASH 字段 | 中文名称 | SDTM 域名 | SDTM 变量 | 数据类型 |
|-----------|---------|----------|----------|---------|
| SUBJID | 受试者编号 | DM | SUBJID | Character |
| BIRTHDT | 出生日期 | DM | BRTHDT | Date |
| AGE | 年龄 | DM | AGE | Numeric |
| AGEU | 年龄单位 | DM | AGEU | Character |
| SEX | 性别 | DM | SEX | Character |
| RACE | 种族 | DM | RACE | Character |
| WEIGHT | 体重 | DM | WT | Numeric |
| HEIGHT | 身高 | DM | HT | Numeric |
| LBDTC | 采集日期时间 | LB | LBDTC | DateTime |
| LBTESTCD | 检查项目代码 | LB | LBTESTCD | Character |
| LBTEST | 检查项目名称 | LB | LBTEST | Character |
| LBORRES | 原始结果 | LB | LBORRES | Character |
| AESTDTC | 不良事件发生时间 | AE | AESTDTC | DateTime |
| AEDECOD | 不良事件术语 | AE | AEDECOD | Character |
| AESEV | 不良事件严重程度 | AE | AESEV | Character |

5.3.4 CDASH 标准字段库

预置标准表单模板：
- 人口学表单（DEM）
- 生命体征（VIT）
- 实验室检查（LAB）
- 不良事件（AE）
- 合并用药（ME）
- 病史（MH）
- 体格检查（PH）
- 知情同意书（ICF）

5.4 SDTM 转换引擎

转换流程：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ EDC 原始数据  │ ──► │ 数据清洗    │ ──► │ SDTM 映射    │
│ (eCRF 录入)  │     │ 与验证      │     │ 引擎        │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ SDTM 域表    │
                                       │ (DM, AE, LB) │
                                       └─────────────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ Define.xml  │
                                       │ 生成        │
                                       └─────────────┘
```

核心功能：
- eCRF 字段 → SDTM 变量映射
- 数据转换规则
- 衍生变量计算
- 映射文档自动生成
- SDTM 验证工具集成

5.5 ADaM 分析数据模型

核心功能：
- 分析数据集生成
- 衍生变量计算
- 分析前数据处理
- 分析结果报告

=================================
6. 数据库设计
=================================

6.1 多租户架构设计

6.1.1 租户隔离策略

方案 1: Schema 隔离（推荐）
```sql
-- 为每个租户创建独立 Schema
CREATE SCHEMA tenant_001;
CREATE SCHEMA tenant_002;
-- 每个租户独立 Schema，数据完全隔离
```

方案 2: 行级隔离
```sql
-- 所有租户数据在同一表，通过 tenant_id 字段隔离
CREATE TABLE patients (
    tenant_id UUID NOT NULL,
    patient_id BIGSERIAL,
    -- ... 其他字段
    PRIMARY KEY (tenant_id, patient_id)
);
```

推荐的 PostgreSQL 多租户实现：
```sql
-- 启用行级安全 (RLS)
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略
CREATE POLICY tenant_isolation ON patients
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- 设置租户上下文
SET app.current_tenant = 'uuid-here';
```

6.1.2 核心表结构

```sql
-- 租户表
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    tenant_name VARCHAR(100) NOT NULL,
    subscription_tier VARCHAR(50),
    max_users INTEGER DEFAULT 10,
    max_trials INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expired_at TIMESTAMP,
    config JSONB DEFAULT '{}'
);

-- 用户表
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    real_name VARCHAR(50),
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

-- 角色表
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

-- 用户角色关联表
CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);
```

6.1.3 CTMS 核心表

```sql
-- 试验项目表
CREATE TABLE trials (
    trial_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_code VARCHAR(50) UNIQUE NOT NULL,
    trial_name VARCHAR(200) NOT NULL,
    protocol_number VARCHAR(100),
    sponsor_name VARCHAR(200),
    phase VARCHAR(20),
    therapeutic_area VARCHAR(100),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'planning',
    budget DECIMAL(15, 2),
    manager_id UUID,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);

-- 研究中心表
CREATE TABLE study_sites (
    site_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    site_code VARCHAR(50) NOT NULL,
    site_name VARCHAR(200) NOT NULL,
    hospital_name VARCHAR(200),
    address TEXT,
    city VARCHAR(50),
    province VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    contact_person VARCHAR(50),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    gcp_certified BOOLEAN DEFAULT FALSE,
    ethical_approval_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    UNIQUE(tenant_id, trial_id, site_code)
);

-- 研究者表
CREATE TABLE investigators (
    investigator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    site_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    name VARCHAR(50) NOT NULL,
    title VARCHAR(100),
    specialty VARCHAR(100),
    qualification VARCHAR(100),
    role VARCHAR(20), -- PI, Sub-I, Coordinator
    phone VARCHAR(20),
    email VARCHAR(100),
    signature_image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);
```

6.1.4 EDC 核心表

```sql
-- 表单设计表
CREATE TABLE crf_designs (
    design_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    form_name VARCHAR(200) NOT NULL,
    form_code VARCHAR(50) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    description TEXT,
    layout_json JSONB, -- 表单布局配置
    fields_json JSONB, -- 字段配置
    validation_rules_json JSONB, -- 验证规则
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- 患者表
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    site_id UUID NOT NULL,
    subject_id VARCHAR(50) NOT NULL, -- 受试者编号
    patient_name_encrypted TEXT, -- 加密存储
    date_of_birth DATE,
    gender VARCHAR(10),
    phone_encrypted TEXT, -- 加密存储
    email VARCHAR(100),
    status VARCHAR(20) DEFAULT 'screening',
    consent_date DATE,
    randomization_number VARCHAR(50),
    treatment_arm VARCHAR(50),
    screening_date DATE,
    enrollment_date DATE,
    last_visit_date DATE,
    withdrawal_date DATE,
    withdrawal_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE,
    UNIQUE(tenant_id, subject_id)
);

-- 访视表
CREATE TABLE visits (
    visit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    visit_name VARCHAR(100) NOT NULL, -- Screening, Baseline, Visit1...
    visit_code VARCHAR(50),
    planned_date DATE,
    actual_date DATE,
    visit_number INTEGER,
    status VARCHAR(20) DEFAULT 'planned',
    duration INTEGER, -- 分钟
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- 表单数据表
CREATE TABLE form_data (
    data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    visit_id UUID NOT NULL,
    design_id UUID NOT NULL,
    form_data JSONB, -- 表单数据
    status VARCHAR(20) DEFAULT 'draft',
    submitted_by UUID,
    submitted_at TIMESTAMP,
    locked_by UUID,
    locked_at TIMESTAMP,
    locked_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id) ON DELETE CASCADE,
    FOREIGN KEY (design_id) REFERENCES crf_designs(design_id) ON DELETE CASCADE
);

-- 疑问表
CREATE TABLE queries (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    visit_id UUID NOT NULL,
    form_data_id UUID NOT NULL,
    field_name VARCHAR(100),
    question TEXT NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    severity VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_by UUID,
    resolved_at TIMESTAMP,
    closed_by UUID,
    closed_at TIMESTAMP,
    response TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id) ON DELETE CASCADE,
    FOREIGN KEY (form_data_id) REFERENCES form_data(data_id) ON DELETE CASCADE
);
```

6.1.5 IWRS 核心表

```sql
-- 随机化方案表
CREATE TABLE randomization_schemes (
    scheme_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    scheme_name VARCHAR(100) NOT NULL,
    randomization_type VARCHAR(50), -- simple, block, stratified, minimization
    treatment_arms_json JSONB, -- 治疗组配置
    allocation_ratio VARCHAR(20), -- 1:1, 2:1, 3:1
    block_sizes JSONB, -- 区组大小
    stratification_factors JSONB, -- 分层因素
    random_seed BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE
);

-- 药物库存表
CREATE TABLE drug_inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID NOT NULL,
    site_id UUID NOT NULL,
    drug_code VARCHAR(50) NOT NULL,
    drug_name VARCHAR(200) NOT NULL,
    batch_number VARCHAR(100),
    quantity INTEGER NOT NULL,
    unit VARCHAR(20),
    expiry_date DATE,
    storage_condition VARCHAR(100),
    location VARCHAR(100),
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (site_id) REFERENCES study_sites(site_id) ON DELETE CASCADE
);

-- 药物分配记录表
CREATE TABLE drug_allocation (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    allocation_date TIMESTAMP NOT NULL,
    randomization_number VARCHAR(50) NOT NULL,
    treatment_arm VARCHAR(50) NOT NULL,
    drug_code VARCHAR(50) NOT NULL,
    batch_number VARCHAR(100),
    quantity_allocated INTEGER,
    quantity_returned INTEGER DEFAULT 0,
    quantity_destroyed INTEGER DEFAULT 0,
    allocated_by UUID,
    received_by UUID,
    received_date TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
```

6.1.6 医生病历夹核心表

```sql
-- 医生个人病历夹配置表
CREATE TABLE doctor_pmrs (
    pmr_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    pmr_name VARCHAR(100) NOT NULL,
    description TEXT,
    template_id UUID, -- 引用 EDC 模板
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES crf_designs(design_id) ON DELETE SET NULL
);

-- 患者个人病历表
CREATE TABLE patient_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    pmr_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    patient_name VARCHAR(100),
    patient_id_encrypted TEXT, -- 加密存储
    gender VARCHAR(10),
    date_of_birth DATE,
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    medical_history JSONB, -- 病史
    diagnosis TEXT,
    treatment_plan JSONB, -- 治疗方案
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (pmr_id) REFERENCES doctor_pmrs(pmr_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 随访记录表
CREATE TABLE follow_up_records (
    follow_up_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    record_id UUID NOT NULL,
    follow_up_date DATE NOT NULL,
    visit_type VARCHAR(50), -- 初次、复查、随访
    symptoms TEXT,
    examination_results JSONB,
    lab_results JSONB,
    treatment_changes TEXT,
    next_follow_up_date DATE,
    recorded_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (record_id) REFERENCES patient_records(record_id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(user_id) ON DELETE SET NULL
);
```

6.1.7 eTMF 核心表

```sql
-- eTMF 文档分类表
CREATE TABLE etmf_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID,
    parent_id UUID,
    category_code VARCHAR(50) NOT NULL,
    category_name VARCHAR(200) NOT NULL,
    istaf_code VARCHAR(50), -- ISTAF 标准代码
    level INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES etmf_categories(category_id) ON DELETE SET NULL
);

-- 电子文档表
CREATE TABLE electronic_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    trial_id UUID,
    category_id UUID NOT NULL,
    document_name VARCHAR(300) NOT NULL,
    document_code VARCHAR(100),
    document_type VARCHAR(50), -- PDF, DOCX, XLSX
    version VARCHAR(20) DEFAULT '1.0',
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(100), -- 文件哈希值
    uploader_id UUID,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'draft',
    review_status VARCHAR(20) DEFAULT 'pending',
    approved_by UUID,
    approved_at TIMESTAMP,
    expiration_date DATE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES etmf_categories(category_id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 文档审批工作流表
CREATE TABLE document_workflows (
    workflow_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    document_id UUID NOT NULL,
    workflow_type VARCHAR(50), -- review, approval, publication
    current_stage INTEGER DEFAULT 1,
    total_stages INTEGER,
    status VARCHAR(20) DEFAULT 'in_progress',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    workflow_config JSONB,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES electronic_documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 审批记录表
CREATE TABLE approval_records (
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL,
    stage_number INTEGER NOT NULL,
    approver_id UUID NOT NULL,
    action VARCHAR(20), -- approve, reject, request_change
    comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES document_workflows(workflow_id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(user_id) ON DELETE CASCADE
);
```

6.1.8 工时管理核心表

```sql
-- 工时类型表
CREATE TABLE time_entry_types (
    type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type_code VARCHAR(50) NOT NULL,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

-- 工时填报表
CREATE TABLE time_entries (
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    trial_id UUID,
    project_task_id UUID,
    entry_date DATE NOT NULL,
    hours DECIMAL(4,2) NOT NULL,
    type_id UUID NOT NULL,
    description TEXT,
    attachments JSONB, -- 附件列表
    status VARCHAR(20) DEFAULT 'submitted',
    submitted_at TIMESTAMP,
    reviewer_id UUID,
    reviewed_at TIMESTAMP,
    review_status VARCHAR(20),
    review_comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (trial_id) REFERENCES trials(trial_id) ON DELETE SET NULL,
    FOREIGN KEY (type_id) REFERENCES time_entry_types(type_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id) ON DELETE SET NULL
);
```

=================================
7. SaaS 多租户架构设计
=================================

7.1 多租户架构策略

7.1.1 隔离级别选择

┌─────────────────────────────────────────────────────────────┐
│ 隔离级别对比                                               │
├─────────────────────────────────────────────────────────────┤
│ 1. 数据库级隔离                                              │
│    - 优点：完全隔离，安全性高                               │
│    - 缺点：成本高，维护复杂                                 │
│    - 适用：大型企业客户                                    │
│                                                              │
│ 2. Schema 级隔离（推荐）                                     │
│    - 优点：平衡安全与成本，易于维护                         │
│    - 缺点：需要 Schema 管理                                 │
│    - 适用：大多数 SaaS 客户                                 │
│                                                              │
│ 3. 行级隔离                                                │
│    - 优点：成本最低，简单                                   │
│    - 缺点：安全性相对较低                                 │
│    - 适用：中小客户，低风险场景                             │
└─────────────────────────────────────────────────────────────┘

7.1.2 推荐的 PostgreSQL Schema 隔离实现

```sql
-- 创建租户 Schema
CREATE SCHEMA tenant_001;
ALTER SCHEMA tenant_001 OWNER TO saas_user;

-- 在 Schema 中创建表
CREATE TABLE tenant_001.trials (
    trial_id UUID PRIMARY KEY,
    trial_name VARCHAR(200),
    -- ... 其他字段
    tenant_id UUID NOT NULL DEFAULT 'tenant_001-uuid'
);

-- 设置默认 Schema 搜索路径
SET search_path TO tenant_001, public;
```

7.2 SaaS 核心功能

7.2.1 订阅管理

```sql
-- 订阅计划表
CREATE TABLE subscription_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_code VARCHAR(50) UNIQUE NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    features JSONB, -- 功能特性
    max_trials INTEGER,
    max_users INTEGER,
    max_sites INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 租户订阅表
CREATE TABLE tenant_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    plan_id UUID NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    billing_cycle VARCHAR(20), -- monthly, yearly
    status VARCHAR(20) DEFAULT 'active',
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_method VARCHAR(50),
    next_billing_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(plan_id) ON DELETE CASCADE
);
```

7.2.2 租户配额管理

```sql
-- 租户配额表
CREATE TABLE tenant_quotas (
    quota_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    max_trials INTEGER DEFAULT 5,
    max_users INTEGER DEFAULT 10,
    max_sites INTEGER DEFAULT 20,
    max_storage_gb INTEGER DEFAULT 100,
    max_api_calls_per_day INTEGER DEFAULT 10000,
    current_trials INTEGER DEFAULT 0,
    current_users INTEGER DEFAULT 0,
    current_storage_gb INTEGER DEFAULT 0,
    current_api_calls INTEGER DEFAULT 0,
    last_reset_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);
```

7.3 API 网关设计

7.3.1 路由配置

```yaml
# Gateway 路由配置示例
routes:
  - id: ctms_service
    uri: lb://ctms-service
    predicates:
      - Path=/api/ctms/**
    filters:
      - JwtAuthentication
      - RateLimiter=1000
      - CircuitBreaker=ctms-cb
      
  - id: edc_service
    uri: lb://edc-service
    predicates:
      - Path=/api/edc/**
    filters:
      - JwtAuthentication
      - RateLimiter=2000
      - CircuitBreaker=edc-cb
      
  - id: iwrs_service
    uri: lb://iwrs-service
    predicates:
      - Path=/api/iwrs/**
    filters:
      - JwtAuthentication
      - RateLimiter=500
      - CircuitBreaker=iwrs-cb
      
  - id: pmr_service
    uri: lb://pmr-service
    predicates:
      - Path=/api/pmr/**
    filters:
      - JwtAuthentication
      - RateLimiter=1500
      - CircuitBreaker=pmr-cb
```

=================================
8. AI 自动化测试方案
=================================

8.1 测试架构

```
┌─────────────────────────────────────────────────────────────┐
│                    测试管理层                                 │
│  测试计划 | 测试用例 | 测试执行 | 测试报告 | 缺陷管理        │
├─────────────────────────────────────────────────────────────┤
│                      AI 测试引擎                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  用例生成   │  │  用例执行   │  │  结果分析   │          │
│  │  AI Model   │  │  Agent      │  │  AI Model   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                    自动化测试框架                            │
│  Cypress / Playwright + Jest + Allure                       │
├─────────────────────────────────────────────────────────────┤
│                    测试数据管理                              │
│  测试数据生成 | 数据脱敏 | 数据恢复                          │
└─────────────────────────────────────────────────────────────┘
```

8.2 AI 测试用例生成

8.2.1 基于需求文档生成测试用例

```python
# AI 测试用例生成示例
from hermes_tools import write_file

test_cases = """
# EDC 系统测试用例

## 1. eCRF 表单设计器测试

### TC-EDC-001: 拖拽字段功能测试
**前置条件**: 用户已登录，已创建试验项目
**测试步骤**:
1. 进入 eCRF 表单设计器
2. 从组件库拖拽"文本框"到画布
3. 拖拽"日期选择"到画布
4. 拖拽"下拉框"到画布
**预期结果**:
- 所有组件成功放置在画布上
- 组件可被选中并编辑属性
- 组件显示正确样式

### TC-EDC-002: CDASH 字段验证测试
**前置条件**: 用户已创建表单
**测试步骤**:
1. 添加字段名为"subject_id"（小写，不符合 CDASH）
2. 系统应提示字段名不符合 CDASH 规范
3. 自动建议改为"SUBJID"
4. 接受建议
**预期结果**:
- 系统正确识别 CDASH 违规
- 提供自动修正建议
- 修正后字段名符合规范

### TC-EDC-003: 表单验证规则测试
**前置条件**: 表单已创建
**测试步骤**:
1. 为年龄字段添加验证规则：0 <= age <= 150
2. 保存表单
3. 进入预览模式，输入年龄 200
**预期结果**:
- 系统提示"年龄超出合理范围"
- 字段变红显示错误
"""

write_file(
    path="d:/workspace/doc/ai-test-cases.md",
    content=test_cases
)
```

8.2.2 测试用例生成策略

| 测试类型 | AI 生成策略 | 覆盖要点 |
|---------|-----------|---------|
| 功能测试 | 基于需求文档 + 用户故事 | 主流程、异常流程、边界条件 |
| UI 测试 | 基于界面截图 + 组件树 | 布局、样式、交互 |
| 接口测试 | 基于 API 文档 | 请求/响应、状态码、数据验证 |
| 性能测试 | 基于系统负载预测 | 并发数、响应时间、吞吐量 |
| 安全测试 | 基于 OWASP Top 10 | 注入、XSS、CSRF、认证绕过 |

8.3 AI 测试执行

8.3.1 智能测试 Agent

```python
# AI 测试执行 Agent 伪代码
class TestAgent:
    def __init__(self):
        self.browser = Browser()
        self.vision = Vision()
        self.llm = LLM()
        
    async def execute_test_case(self, test_case):
        """执行测试用例"""
        # 1. 分析测试用例
        steps = self.llm.parse_test_steps(test_case)
        
        # 2. 逐步骤执行
        for step in steps:
            result = await self.execute_step(step)
            if not result.success:
                # 3. AI 智能诊断
                screenshot = await self.browser.screenshot()
                error_analysis = self.vision.analyze_error(screenshot, step)
                self.llm.generate_error_report(error_analysis)
                return result
                
        # 4. 生成测试报告
        return self.generate_test_report()
    
    async def execute_step(self, step):
        """执行单步操作"""
        # 智能元素定位
        element = await self.browser.smart_find(step.target)
        
        # 执行操作
        if step.action == "click":
            await element.click()
        elif step.action == "type":
            await element.type(step.text)
        elif step.action == "drag":
            await element.drag(step.target)
            
        # 验证结果
        success = await self.verify_step_result(step)
        
        return TestResult(
            success=success,
            step=step,
            timestamp=datetime.now()
        )
```

8.3.2 视觉验证

```python
# 视觉回归测试
class VisualRegressionTest:
    def __init__(self):
        self.reference_store = ReferenceStore()
        self.vision_model = VisionModel()
        
    async def compare_screenshots(self, current_screenshot, test_case_id):
        """对比当前截图与基准截图"""
        # 1. 获取基准截图
        reference = await self.reference_store.get(test_case_id)
        
        # 2. AI 视觉对比
        differences = await self.vision_model.compare(
            current_screenshot, 
            reference
        )
        
        # 3. 智能判断是否为真实问题
        is_significant = await self.vision_model.is_significant(
            differences
        )
        
        if is_significant:
            return VisualRegressionResult(
                passed=False,
                differences=differences,
                severity=self.assess_severity(differences)
            )
            
        return VisualRegressionResult(passed=True)
```

8.4 自动化测试框架集成

8.4.1 Cypress + AI 测试

```typescript
// Cypress 测试示例 + AI 增强
describe('EDC 表单设计器测试', () => {
  beforeEach(() => {
    cy.login('test-user', 'test-password');
    cy.visit('/trials/new');
  });

  it('TC-EDC-001: 拖拽字段功能', () => {
    // 使用 AI 智能元素定位
    cy.aiFind('组件库').contains('文本框').dragTo('画布区域');
    
    // 验证组件创建
    cy.aiFind('画布区域').contains('文本框').should('be.visible');
    
    // AI 视觉验证
    cy.aiScreenshot('表单设计器 - 文本框已添加');
  });

  it('TC-EDC-002: CDASH 字段验证', () => {
    cy.aiFind('字段名称').type('subject_id');
    
    // AI 智能验证错误提示
    cy.aiVerifyErrorMessage('字段名不符合 CDASH 规范');
    
    // 验证自动修正
    cy.aiFind('修正建议').click();
    cy.aiFind('字段名称').should('have.value', 'SUBJID');
  });
});
```

8.5 测试数据管理

8.5.1 AI 测试数据生成

```python
# AI 生成测试数据
class TestDataGenerator:
    def __init__(self):
        self.llm = LLM()
        
    def generate_patient_data(self, trial_config):
        """根据试验配置生成患者数据"""
        prompt = f"""
        生成临床试验患者测试数据
        
        试验配置：
        {trial_config}
        
        要求：
        1. 符合 CDASH 标准
        2. 包含正常数据和异常数据
        3. 包含边界值数据
        4. 符合入组/排除标准
        
        输出格式：JSON
        """
        
        data = self.llm.generate(prompt, response_format='json')
        return data
    
    def generate_edge_cases(self, form_schema):
        """生成边界值和异常场景数据"""
        prompt = f"""
        为表单生成边界测试数据
        
        表单结构：
        {form_schema}
        
        需要覆盖的边界：
        1. 最小值/最大值
        2. 空值/NULL
        3. 特殊字符
        4. 超长字符串
        5. 格式错误数据
        """
        
        edge_cases = self.llm.generate(prompt)
        return self.parse_edge_cases(edge_cases)
```

8.6 测试报告与缺陷管理

8.6.1 AI 测试报告生成

```python
class AITestReport:
    def __init__(self):
        self.llm = LLM()
        
    async def generate_report(self, test_results):
        """生成智能测试报告"""
        # 1. 统计分析
        summary = self.analyze_results(test_results)
        
        # 2. AI 智能分析
        insights = await self.llm.analyze(
            f"""
            分析测试结果：
            {json.dumps(summary, indent=2)}
            
            请提供：
            1. 测试覆盖度分析
            2. 缺陷分布分析
            3. 质量风险评估
            4. 改进建议
            """
        )
        
        # 3. 生成报告
        report = {
            'summary': summary,
            'insights': insights,
            'recommendations': self.generate_recommendations(insights),
            'risk_level': self.assess_risk(summary, insights)
        }
        
        return report
```

8.7 测试策略

| 测试层级 | AI 自动化程度 | 工具 |
|---------|------------|------|
| 单元测试 | 100% | Jest + AI 生成测试用例 |
| 集成测试 | 90% | Cypress + AI 智能定位 |
| E2E 测试 | 85% | Playwright + AI 视觉验证 |
| 性能测试 | 80% | JMeter + AI 负载预测 |
| 安全测试 | 75% | OWASP ZAP + AI 漏洞分析 |

=================================
9. 技术栈选型（详细）
=================================

9.1 后端详细技术栈

```yaml
# 后端技术栈
language: Java 17
framework: 
  - Spring Boot 3.x
  - Spring Cloud Alibaba
  - Spring Cloud Gateway

service_registration: Nacos 2.x
circuit_breaker: 
  - Sentinel 1.8
  - Resilience4j

orm:
  - MyBatis-Plus 3.5
  - Liquibase (数据库版本管理)

cache: Redis 7.x
  - 分布式锁
  - 会话管理
  - 数据缓存

message_queue:
  - RabbitMQ 3.11 (异步任务、事件驱动)
  - Kafka 3.3 (日志、事件流)

monitoring:
  - SkyWalking 9.x (链路追踪)
  - Prometheus 2.40 (指标采集)
  - Grafana 9.x (可视化)

logging:
  - SLF4J + Logback
  - ELK Stack (Elasticsearch, Logstash, Kibana)

file_storage: MinIO (兼容 S3 协议)
```

9.2 前端详细技术栈

```yaml
# 前端技术栈
framework: React 18
type_system: TypeScript 5
ui_library: 
  - Ant Design 5
  - Tailwind CSS (样式工具)

state_management: 
  - Zustand (全局状态)
  - React Query (服务端状态)

forms:
  - React Hook Form
  - Zod (表单验证)

http_client: Axios 1.x
routing: React Router 6

visualization:
  - ECharts 5
  - AntV G2

drag_and_drop: 
  - React DnD
  - dnd-kit

rich_text_editor:
  - Quill (富文本)
  - Monaco Editor (代码编辑)

pdf_generation: 
  - React-PDF
  - pdfmake

i18n: react-i18next
```

9.3 DevOps 详细技术栈

```yaml
# DevOps 工具链
containerization:
  - Docker 24.x
  - Kubernetes 1.28

ci_cd:
  - Jenkins 2.x
  - GitLab CI
  - GitHub Actions

infrastructure_as_code:
  - Terraform 1.x
  - Ansible 7.x

monitoring:
  - Prometheus
  - Grafana
  - AlertManager
  - PagerDuty

log_management:
  - ELK Stack
  - Loki + Grafana

code_quality:
  - SonarQube 10.x
  - ESLint
  - Prettier

security:
  - Snyk (依赖漏洞扫描)
  - OWASP ZAP (安全测试)
  - Vault (密钥管理)
```

=================================
10. 实施计划
=================================

10.1 项目阶段划分

```
Phase 1: 基础架构搭建（1-2 个月）
├── 技术选型与架构设计
├── 开发环境搭建
├── 微服务框架搭建
├── 数据库设计与建表
├── CI/CD流水线配置
└── 基础组件开发

Phase 2: CTMS 核心功能（2-3 个月）
├── 试验项目管理
├── 研究中心管理
├── eTMF 文档管理
├── 工时管理系统
└── 用户权限管理

Phase 3: EDC 核心功能（3-4 个月）
├── eCRF 表单设计器
├── 数据录入界面
├── 数据验证引擎
├── CDASH/SDTM映射
└── 审计追踪

Phase 4: IWRS 核心功能（2-3 个月）
├── 随机化方案设计
├── 药物库存管理
├── 入组流程
├── 药物分配
└── 紧急揭盲

Phase 5: 医生病历夹（2-3 个月）
├── 患者档案管理
├── 自定义表单
├── 诊疗记录
├── 数据隐私安全
└── 医生工作台

Phase 6: SaaS 功能（2 个月）
├── 多租户架构
├── 订阅管理
├── 配额控制
├── API 网关
└── 监控告警

Phase 7: AI 自动化测试（2 个月）
├── 测试用例生成
├── 自动化测试框架
├── 视觉回归测试
├── 测试数据分析
└── 缺陷管理集成

Phase 8: 系统集成测试（1-2 个月）
├── 接口集成测试
├── 性能测试
├── 安全测试
├── 用户验收测试
└── 生产环境部署

Phase 9: 优化与迭代（持续）
├── 性能优化
├── 功能优化
├── 用户体验改进
└── 新技术引入
```

10.2 里程碑

| 里程碑 | 时间点 | 交付物 |
|-------|-------|--------|
| M1: 架构完成 | 第 2 个月 | 基础框架、开发环境、CI/CD |
| M2: CTMS 完成 | 第 4 个月 | CTMS 系统 MVP |
| M3: EDC 完成 | 第 7 个月 | EDC 系统 MVP、表单设计器 |
| M4: IWRS 完成 | 第 9 个月 | IWRS 系统 |
| M5: 医生病历夹 | 第 12 个月 | 完整系统 MVP |
| M6: SaaS 功能 | 第 14 个月 | 多租户、订阅管理 |
| M7: 测试自动化 | 第 16 个月 | AI 测试框架 |
| M8: 正式发布 | 第 18 个月 | 生产环境上线 |

10.3 团队配置

```
核心团队成员（15-20 人）：
├── 产品经理 (2 人)
├── UI/UX设计师(2 人)
├── 架构师 (1 人)
├── 后端开发 (6 人)
├── 前端开发 (5 人)
├── 测试工程师 (3 人)
├── DevOps 工程师 (1 人)
└── AI 工程师 (2 人)
```

=================================
11. 风险管理
=================================

11.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| CDISC 标准变更 | 高 | 中 | 保持标准映射层抽象化，易于调整 |
| 性能问题 | 高 | 中 | 压测、优化、缓存策略 |
| 数据安全问题 | 高 | 低 | 加密、审计、合规认证 |
| 微服务复杂度 | 中 | 高 | 标准化、文档化、监控 |

11.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| 市场需求变化 | 高 | 中 | 敏捷开发、快速迭代 |
| 竞争加剧 | 中 | 高 | 差异化功能、本地化 |
| 法规变更 | 高 | 中 | 合规团队、标准跟踪 |

=================================
12. 成功指标
=================================

12.1 技术指标

- 系统可用性：99.9%
- API 响应时间：< 200ms (P95)
- 页面加载时间：< 3s
- 并发用户支持：≥ 1000
- 数据迁移时间：< 1 小时（100 万条记录）

12.2 业务指标

- 客户满意度：≥ 90%
- 系统上线时间：≤ 18 个月
- 缺陷密度：< 1 个/千行代码
- 自动化测试覆盖率：≥ 80%
- 客户续约率：≥ 85%

=================================
13. 总结
=================================

本产品设计文档详细描述了一个完整的临床试验 SaaS 平台，包含：

✓ 四大核心系统：CTMS、EDC、IWRS、医生病历夹
✓ 符合国际标准：CDISC、FDA 21 CFR Part 11、GCP
✓ 微服务 SaaS 架构：多租户、可扩展
✓ AI 自动化测试：智能测试生成与执行
✓ 完整实施计划：18 个月上线

核心价值：
- 一体化平台，数据互通
- 零编码表单设计
- 标准自动映射
- 合规保障
- 中国本土化适配

后续工作：
1. 详细设计文档细化
2. 技术 PoC 验证
3. 原型开发
4. 客户反馈收集
5. 迭代优化

---

文档版本历史：
- v1.0 (2026 年) - 初始版本

维护人：蔡宇恒
联系方式：caiyuheng81@outlook.com
文档位置：d:\workspace\doc\clinical-trial-platform-product-design.md
