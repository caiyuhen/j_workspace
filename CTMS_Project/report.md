# 项目状态报告：CDISC 导出功能补齐及待安全保障建议

## 一、已完成内容（模块实现）

### 1. 扩展导出功能（SDTM, ECRF, ADaM）

- **新增** `to-ecrf` API 端点（`/form/:formId/to-ecrf`）。
- **引入** `to-adam` 前置结构支持（通过 `AdamExporter` 模块）。
- **标准统一**：新增 `export.types.ts` 定义 `ExportFormat` 枚举和通用接口如 `ExportRequest`、`AuditLogEntry`，保障逻辑一致性和易扩展性。

### 2. 


- **架构升级**：`etl-process.ts` 中实现了新的转换函数 `executeEcrfExport` 和 `executeAdamExport`。
- **日志审计增强**：
    - 引入 `auditLogs` 内存缓存。
    - 函数 `addAuditLog(...)` 用于记录关键行为（例如 `exportId`）。
- **规范导出接口接入**：所有统一以 `ExportRequest` 为输入，分离数据流转路径。

### 3. 模块兼容性加强

- 所有变动兼容旧系统 `CDISCSdtmConverter`、`ConsistencyValidator`、`export.routes.ts`，未破坏任何既有流程。
- 所有模块已优化导入路径并扫描无引用缺失。

## 二、遗留问题 & 安全待强化点

### 1. 用户级权限控制（RBAC）

- **现状**：所有导出逻辑由于缺少有效的 `userId`/`role` 限制，缺少曝光层 TAM（Trust Access Model）防护。
- **建议**：
    - 在 `EtlProcess.executeXXX` 中传入 `userId`。
    - 使用 Prisma 查询时增加 `projectId`, `userId` 作为安全限定条件。
    - 拓展 `projectUserPermission` 表用于生效范围判断。

### 2. 持久化审计日志

- **现状**：目前仅存在内存缓存及其 `addAuditLog` 模拟函数。
- **建议**：
    - 在 Prisma Schema 添加 `AuditLog` 模型。
    - 更新 `EtlProcess.addAuditLog` 实现 `prisma.auditLog.create()` 同步写入。

### 3. Prisma 查询边界设定

- **现状**：存在 SQL 不安全部分，查询中大量使用硬编码 `projectId`而非绑定确认。
- **建议**：
    - 在所有数据库分级查询中加入 `where` 条件含 properties 如 `{ userId, projectId }`。
    - 在 `extractCrfData` 和 `loadSdtmData` 等关键函数中加入各类 `AND` 条件校验。

### 4. 单元测试进阶

- **现状**：规则已覆盖转换器和 ETLP 流程，未包含是否发出 DB 请求的更高精度断言。
- **建议**：
    - 编写对 `PrismaClient` 的模拟断言层。
    - 使用 `sinon` + `mock-fs` 确保模拟触发并不影响执行层调用结构。

---

## 三、项目极简结构图示意

```mermaid
graph TD
    A[EtlProcess) --> B(CDISCSdtmConverter)
    A --> C(ConsistencyValidator)
    A --> D(AdamExporter)
    A --> E(AuditLogger)
    B --> F[SDTM 应用]
    C --> G[合规检查]
    D --> H[ADaM 架构]
    E --> I[代码审计日志]
    subgraph 导出接口
        A --> J[export.routes.ts]
    end
```

---

## 四、后续建议

| 任务 | 描述 |
| :--- | :--- |
| 写入 PRISM 架构安全强化 | `crfForm.findUnique` 强绑定用户角色字段 |
| 增加 Prisma 日志持久化 | `AuditLog` 模型、实际插入、前端日志挂钩 |
| 前端 RBAC 静态认证 | JWT token 从服务打通、岗位分类接入 |
| 引入 Taleum CI 通行证 | CI 检查单元测试覆盖率强制，并自动同步 jenkins |