# EDC CDISC/SDTM 导出功能说明

## 功能概述

本模块实现了EDC系统中基于CDISC标准的数据导出功能，支持将CRF表单数据导出为SDTM、ECRF、ADaM等符合临床研究标准的数据格式。该功能截取现有EDC系统中的CDISC/SDTM导出模块，确保数据符合监管要求，可用于临床试验数据管理。

## 核心特性

1. **多格式导出支持**：
   - SDTM（Study Data Tabulation Model）
   - ECRF（Electronic Case Report Form）
   - ADaM（Analysis Data Model）

2. **数据合规性**：
   - CDISC标准字段映射
   - 数据一致性验证
   - 域完整性检查

3. **导出流程**：
   - 提取阶段：从CRF表单中提取结构化数据
   - 验证阶段：确保数据符合CDISC标准
   - 转换阶段：将数据转换为指定格式
   - 加载阶段：保存导出数据

4. **管理功能**：
   - 支持按项目、时间范围、领域筛选
   - 导出历史记录管理
   - 导出任务状态监控

## 技术架构

### 后端组件

1. **`form.types.ts`** - CRF表单和字段的基础类型定义
2. **`cdisc-sdtm-converter.ts`** - CRF到SDTM转换器
3. **`consistency-validator.ts`** - 数据一致性和合规性验证器
4. **`etl-process.ts`** - ETL处理流程
5. **`sdtm.types.ts`** - SDTM数据结构定义
6. **`export.types.ts`** - 导出相关类型定义
7. **`adam-exporter.ts`** - ADaM导出器
8. **`export.routes.ts`** - 导出功能API路由

### 前端组件

1. **`ExportConfigPage.tsx`** - 导出配置页面
2. **`ExportHistoryPage.tsx`** - 导出历史页面
3. **`ValidationPage.tsx`** - 合规性验证页面
4. **`ReportsPage.tsx`** - 导出报告页面
5. **`EdcExportLayout.tsx`** - 导出功能导航布局

## 路由配置

### API路由

- `GET /api/edc/export/config` - 获取导出配置
- `POST /api/edc/export/form/:formId/to-sdtm` - 单表单SDTM导出
- `POST /api/edc/export/form/:formId/to-ecrf` - 单表单ECRF导出
- `POST /api/edc/export/form/:formId/to-adam` - 单表单ADaM导出
- `GET /api/edc/export/validate-form/:formId` - 表单合规性验证
- `POST /api/edc/export/batch-to-sdtm` - 批量SDTM导出
- `GET /api/edc/export/history` - 获取导出历史

### 前端路由

- `/edc-export/config` - 导出配置页面
- `/edc-export/history` - 导出历史页面
- `/edc-export/validation` - 合规性验证页面
- `/edc-export/reports` - 导出报告页面

## 数据处理流程

1. **数据提取**：根据项目和筛选条件从数据库提取CRF数据
2. **数据验证**：
   - 验证CRF结构是否符合CDISC标准
   - 检查必填字段是否存在
   - 核对字段类型和域定义
3. **数据转换**：
   - 将CRF字段映射到SDTM变量
   - 根据CDISC标准进行字段转换
4. **数据加载**：将转换后的数据保存到指定位置

## 合规性要求

1. **CDISC标准遵循**：
   - 遵循CDISC SDTM标准
   - 支持标准域定义
   - 遵循ADaM数据模型

2. **21 CFR Part 11合规**：
   - 数据完整性保证
   - 审计轨迹记录
   - 访问控制和权限管理

3. **数据安全性**：
   - 敏感数据加密处理
   - 访问权限控制
   - 数据备份机制

## 使用示例

### 导出配置示例

```javascript
{
  "projectId": "clinical-trial-2023",
  "filters": {
    "startDate": "2023-01-01",
    "endDate": "2023-12-31",
    "domains": ["DM", "AE", "VS"],
    "formIds": ["form-001", "form-002"]
  },
  "format": "SDTM"
}
```

### 验证请求示例

```javascript
{
  "formId": "form-001",
  "projectId": "clinical-trial-2023"
}
```

## 性能优化

1. **数据库查询优化**：合理使用索引和分页
2. **内存管理**：批量处理大量数据
3. **缓存策略**：高频数据缓存
4. **异步处理**：长时间导出任务异步执行

## 扩展性考虑

1. **多格式扩展**：支持新增导出格式（如SEND等）
2. **自定义转换**：支持用户自定义转换规则
3. **插件化架构**：支持第三方导出插件
4. **云集成**：支持与云存储和计算服务集成