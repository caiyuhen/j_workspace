# 临床试验管理系统 (CTMS) 演示版

本项目是一个基于 React 和 TypeScript 的临床试验管理系统 (CTMS) 演示应用。旨在展示临床试验全流程中，不同角色（如项目经理、CRA、数据管理员等）的关键任务与协作流程，并结合 GCP (Good Clinical Practice) 合规要求进行功能演示。

## 🚀 项目简介

临床试验是一个复杂且受到严格监管的过程。本 CTMS 演示系统通过可视化的方式，帮助用户理解：

*   **多角色协作**：涵盖项目经理 (PM)、临床监查员 (CRA)、数据管理员 (DM)、统计师 (Stat)、药物警戒 (PV)、质量保证 (QA)、研究中心 (Site) 及伦理委员会 (IRB) 等关键角色。
*   **全流程管理**：从项目启动、中心筛选、受试者入组与治疗、数据管理与统计，直至项目关闭的全生命周期管理。
*   **GCP 合规性**：在每个关键步骤中嵌入 GCP 引用和 CTMS 功能支撑点，强调合规操作的重要性。

## ✨ 核心功能

### 1. 角色视图 (Role View)
针对临床试验中的不同角色，展示其特定的职责和任务清单。
*   **项目经理 (PM)**：统筹全局，负责项目立项、中心筛选、进度监控、预算管理等。
*   **临床监查员 (CRA)**：执行现场监查 (SMV)，进行源数据核查 (SDV)，管理偏差与 AE。
*   **数据管理员 (DM)**：负责数据核查、清理、疑问解答 (Query) 及数据库锁定。
*   **其他角色**：包括统计师的分析计划、PV 的安全性报告、QA 的审计以及 Site/IRB 的日常操作。

### 2. 流程视图 (Process View)
按照时间轴展示临床试验的各个阶段：
1.  **项目启动 (Project Initiation)**：方案设计、伦理递交、立项审批。
2.  **筛选与启动 (Site Selection & Activation)**：中心资质评估、合同签署、SIV。
3.  **受试者入组与治疗 (Recruitment & Treatment)**：受试者筛选、知情同意、随访。
4.  **数据管理与统计 (Data Management & Statistics)**：数据采集、核查、锁定与分析。
5.  **药物警戒 (Pharmacovigilance)**：AE/SAE 收集、评估与上报。
6.  **项目关闭 (Project Closeout)**：中心关闭、文件归档、总结报告。

## 🛠️ 技术栈

*   **前端框架**：[React](https://react.dev/)
*   **开发语言**：[TypeScript](https://www.typescriptlang.org/)
*   **构建工具**：[Vite](https://vitejs.dev/)
*   **UI 组件库**：[Ant Design (v6)](https://ant.design/)
*   **路由管理**：[React Router](https://reactrouter.com/)

## 📦 快速开始

### 前置要求
确保您的本地环境已安装 [Node.js](https://nodejs.org/) (推荐 v16+)。

### 安装与运行

1.  **克隆项目**
    ```bash
    git clone <repository-url>
    cd CTMS_Demo
    ```

2.  **安装依赖**
    ```bash
    npm install
    ```

3.  **启动开发服务器**
    ```bash
    npm run dev
    ```
    启动后，访问控制台输出的本地地址 (通常为 `http://localhost:5173`) 即可预览。

4.  **构建生产版本**
    ```bash
    npm run build
    ```
    构建产物将输出至 `dist` 目录。

## 📂 目录结构

```
src/
├── components/     # 公共组件 (如 MainLayout)
├── pages/          # 页面组件 (Dashboard, RoleDetail, StageDetail)
├── data/           # 模拟数据与常量定义
├── App.tsx         # 应用入口与路由配置
└── main.tsx        # 渲染入口
```

## 📝 贡献指南

欢迎提交 Issue 或 Pull Request 来改进本项目。建议在提交代码前确保通过类型检查和构建测试。

## 📄 许可证

MIT License
