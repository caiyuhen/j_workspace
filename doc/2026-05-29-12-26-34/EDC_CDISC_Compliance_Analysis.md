# EDC系统CDISC标准合规分析报告

基于对CTMS/EDC系统EDC模块的代码分析，本报告总结了系统对CDISC标准的实现和集成情况，重点关注CRF表单设计、字段定义以及CDISC/SDTM导出功能。

## 1. 系统整体架构

### 1.1 EDC模块核心组件
在EDC模块中，系统通过对CRF表单、字段、数据和编辑核查规则的管理来实现数据收集流程。主要组件包括：

- **EdcTemplate**：标准化的模板管理
- **CrfForm**：CRF表单管理（支持CDISC标准）
- **CrfFormField**：CRF字段定义（支持CDISC属性映射）
- **CrfData**：实际数据录入记录
- **CrfEditCheckRule**：编辑核查规则定义

### 1.2 CDISC标准集成设计
系统在设计时已预置CTMS/EDC模块对CDISC标准的集成，具体包括字段级别的元数据标记（cdiscDomain, cdashVariable, sdtmVariable等），其主要代码实现在CrfFormField和CrfForm模型中。

## 2. CDISC标准字段映射机制

### 2.1 CDISC字段关键属性
在`CrfFormField`模型中，定义了与CDISC标准直接相关的字段：
- `cdiscDomain` - CDISC域标识符
- `cdashDataset` - CDASH数据集标识
- `cdashVariable` - CDASH变量标识
- `cdashDataType` - CDASH数据类型
- `sdtmVariable` - SDTM变量标识
- `codeListOid` - 代码表OID标识
- `standardMetadata` - 标准元数据存储

### 2.2 字段映射设计
字段级CDISC属性的映射遵循如下设计原则：
1. **类型化映射**：每个字段支持CDISC/CDASH/SDTM等标准标识
2. **元数据扩展**：通过`standardMetadata`字段支持任意CDISC特定参数
3. **关联代码表**：通过`codeListOid`属性与CDISC代码表关联

## 3. 表单设计与CDISC集成

### 3.1 表单级别CDISC属性
在`CrfForm`模型中包含的关键标准字段：
- `cdiscDomain`：表单所属的CDISC域
- `standardName`：标准名称（默认为CDASH）
- `standardVersion`：标准版本（默认为2.1）
- `sdtmDatasetName`：SDTM数据集名
- `cdashModel`：CDASH模型名

### 3.2 表单设计逻辑
```typescript
// 从实体中可以看出，CRF表单的CRF_Field设计师直接集成了CDISC标准
export const createFieldSchema = z.object({
  // ...
  cdiscDomain: z.string().min(2).max(10).optional(),
  cdashDataset: z.string().max(50).optional(),
  cdashVariable: z.string().max(40).optional(),
  cdashDataType: z.string().max(20).optional(),
  sdtmVariable: z.string().max(40).optional(),
  codeListOid: z.string().max(100).optional(),
  // ...
})
```

通过这些属性，系统可以支持：
- 标准字段与CDISC域的真实对应关系
- 支持CDASH/CDISC/SDTM本身的映射关系
- 实现基于域的字段分组与场景过滤（例如特定CDISC域的数据录入）

## 4. CDISC代码表支持

### 4.1 CdiscCodeList模型
系统通过`CdiscCodeList`模型支持CDISC代码表：
- `codeListOid`：代码表全局唯一标识
- `codeListName`：代码表名称
- `domain`：所属CDISC域
- `dataType`：码表中数据类型
- `items`：码表项集合

### 4.2 代码表集成
系统在CRF表单字段创建时进行代码表验证：
```typescript
async function validateCodeListOid(codeListOid?: string) {
  if (!codeListOid) return null;
  
  const codeList = await prisma.cdiscCodeList.findUnique({
    where: { codeListOid },
    select: { codeListOid: true, domain: true, dataType: true },
  });
  
  if (!codeList) {
    throw new BadRequestError(`CDISC 代码表不存在: ${codeListOid}`);
  }
  
  return codeList;
}
```

## 5. SDTM导出潜在可集成点

根据数据库Schema，SDTM导出相关的实体和配置已经预留：
- `SdtmExportConfig`表用于记录SDTM导出映射规则
- `cdiscDomain`字段允许数据按域过滤和映射
- `sdtmVariable`字段直接支持SDTM变量映射

## 6. 潜在改进点与优化建议

### 6.1 实现待完善之处
1. **CDISC到SDTM导出的实现程度**：目前仅实现基础映射结构，如`SdtmExportConfig`表，但没有具体的导出逻辑实现代码。
2. **数据分析能力有限**：缺乏与导入CDISC/SDTM数据相关的分析与检查机制。
3. **标准转换完整度**：对于CDASH、CDISC、SDTM之间的转换逻辑较弱，尤其是字段映射关系和一致性校验。
4. **标准版本管理集成度**：目前只定义了标准名称和版本字段，但缺少版本兼容性处理机制。

### 6.2 建议后续实现方向
1. **开发CDISC/SDTM转换引擎**：增加转换工具模块用于标准间映射处理
2. **创建ETL导入脚本**：支持线上和离线的CDISC/SDTM数据导入
3. **构建标准化字段检查模块**：用于完整性校验和符合性检查
4. **完善SDTM导出工具**：包括字段映射、验证系统、自动生成等

系统已具备基本的CDISC标准支持能力，但更深层的导出功能实现和标准化转换仍属待做工作。输入文档系统目前已支持从CRF表单字段到CDISC字段核心实体到属性转换，具备后续构建自动化流程的基础。