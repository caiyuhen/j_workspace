# CDASH 标准资源总索引

> **版本**: 1.0  
> **创建时间**: 2026-05-27  
> **创建人**: Cai Yuheng (蔡宇衡)  
> **项目**: Clinical Trial Platform (CTMS/EDC/IWRS + Physician EMR)

---

## 文档目录

1. [CDASH 标准资源索引](#cdash 标准资源索引)
2. [CDASH 到 SDTM 字段映射表](#cdash 到 sdtm 字段映射表)
3. [CDASH 数据验证规则参考](#cdash 数据验证规则参考)
4. [官方资源下载](#官方资源下载)
5. [实施指南](#实施指南)

---

## 相关文档

### 1. CDASH 标准资源索引.md
**路径**: `d:/workspace/doc/CDASH 标准资源索引.md`

**内容**:
- CDASH 标准概述和版本历史
- 16 个核心数据域介绍
- CDASH v1.1, SAE Supplement, User Guide 等官方资源
- 标准关系图 (CDASH 到 SDTM 到 ADaM)
- 下载方式和实施建议

**用途**: 了解 CDASH 标准整体框架和获取官方资源

---

### 2. CDASH 到 SDTM 字段映射表.md
**路径**: `d:/workspace/doc/CDASH 到 SDTM 字段映射表.md`

**内容**:
- 10 个核心数据域的详细字段映射 (DM, IC, MH, CM, EX, VS, AE, LB, PRO, PG)
- 字段对照表 (CDASH 名 到 SDTM 名 到 数据类型 到 必填规则)
- 生命体征和实验室检测标准代码表
- CDASH 字段命名规则
- 实施建议

**用途**: 
- eCRF 设计器字段配置
- 字段命名自动验证
- SDTM 转换引擎开发

---

### 3. CDASH 数据验证规则参考.md
**路径**: `d:/workspace/doc/CDASH 数据验证规则参考.md`

**内容**:
- 数据类型验证规则 (ST, NM, DT, LM)
- 必填字段规则 (所有核心域)
- 逻辑验证规则 (日期逻辑、数值范围、枚举)
- 字段特定验证规则 (USUBJID, AGE, AE, LB 等)
- 数据完整性规则 (审计追踪)
- eCRF 设计器验证配置示例 (JSON 格式)
- JavaScript 验证规则库代码
- 测试建议

**用途**: 
- EDC 系统前端/后端验证实现
- eCRF 设计器配置
- 数据录入验证
- 自动化测试用例

---

## 官方资源链接

### CDISC 官方网站
- **CDASH 标准页**: https://www.cdisc.org/standards/foundational/cdash
- **SDTM 标准页**: https://www.cdisc.org/standards/foundational/sdtm
- **ADaM 标准页**: https://www.cdisc.org/standards/foundational/adam
- **社区论坛**: https://community.cdisc.org/
- **GitHub**: https://github.com/cdisc-org

### 免费资源
1. **CDASH v1.1 Overview** - 标准概览文档
2. **CDASH User Guide v1.0** - 实施指南
3. **CDASH ODM-XML** - 示例 XML 文件
4. **CDASH CRF Examples** - 示例 CRF 表单

### 付费资源 (需要订阅)
1. **CDASH v1.1 完整标准文档** - PDF 格式
2. **CDASH SAE Supplement** - 严重不良事件补充
3. **CDASHIG v2.0** - 新版本实施指南 (开发中)

---

## 实施建议

### 第一阶段：标准学习和资源获取

1. **下载 CDASH 官方文档**
   - 注册 CDISC 账户
   - 下载 CDASH v1.1 标准文档
   - 下载 CDASH User Guide
   - 下载 CDASH ODM-XML 示例

2. **研究标准文档**
   - 理解 16 个核心数据域
   - 熟悉字段命名规则
   - 掌握数据类型定义
   - 学习验证规则

3. **创建内部参考库**
   - 整理 CDASH 标准字段库
   - 创建字段映射表
   - 开发验证规则库

---

### 第二阶段：eCRF 设计器开发

1. **字段组件库**
   ```
   预置组件 (拖拽到画布):
   - Demographics 域组件 (DOB, SEX, RACE 等)
   - Adverse Events 域组件 (AETERM, AESER 等)
   - Vital Signs 域组件 (SYSBP, DIA, HR 等)
   - Lab Tests 域组件 (WBC, HGB, ALT 等)
   - Custom 域组件 (用户自定义)
   ```

2. **字段属性面板**
   ```
   配置项:
   - 英文名 (CDASH 标准)
   - 中文名
   - 数据类型 (ST, NM, DT, LM, CA)
   - 必填性 (Yes/No/Conditional)
   - 验证规则 (长度、范围、枚举)
   - SDTM 字段映射
   - 显示顺序
   - 条件显示规则
   ```

3. **实时验证**
   ```
   字段输入时:
   - 英文名自动检查 (是否符合 CDASH 规范)
   - 必填字段提示
   - 数据类型匹配
   - 枚举值提示
   ```

---

### 第三阶段：EDC 数据录入

1. **表单渲染引擎**
   ```
   输入时验证:
   - 必填字段检查
   - 数据类型验证
   - 数值范围检查
   - 日期逻辑验证
   - 枚举值验证
   ```

2. **提交前验证**
   ```
   完整验证流程:
   1. 检查所有必填字段
   2. 验证数据格式
   3. 逻辑关系检查
   4. 审计追踪记录
   5. 生成验证报告
   ```

3. **疑问管理**
   ```
   验证失败时:
   - 高亮显示错误字段
   - 显示错误信息
   - 创建数据疑问 (Query)
   - 通知数据管理员
   ```

---

### 第四阶段：SDTM 转换

1. **转换引擎设计**
   ```
   数据转换流程:
   CDASH 数据 到 字段映射 到 SDTM 格式 到 XPT 文件
   ```

2. **标准域生成**
   ```
   预定义转换:
   - DM 域 (Demographics)
   - AE 域 (Adverse Events)
   - LB 域 (Laboratory)
   - EX 域 (Exposure)
   - VS 域 (Vital Signs)
   - CM 域 (Current Medications)
   - MH 域 (Medical History)
   ```

3. **输出验证**
   ```
   SDTM 验证:
   - 检查必填字段
   - 验证数据格式
   - 检查唯一键
   - 验证逻辑关系
   ```

---

## 技术实现建议

### 1. 字段命名规范 (JavaScript)

```javascript
// CDASH 字段验证器
class CDASHFieldValidator {
  static validateFieldName(name) {
    // 命名规则：2-3 字母前缀 + 语义名称
    const pattern = /^[A-Z]{2,3}[A-Z]+$/;
    return pattern.test(name);
  }
  
  static validateFieldNameLength(name) {
    return name.length <= 64;
  }
  
  static isStandardCDASH(name) {
    const standardFields = [
      // Demographics
      'STUDYID', 'USUBJID', 'DOB', 'SEX', 'RACE', 'SITEID',
      // Adverse Events
      'AETERM', 'AESEQ', 'AESOC', 'AESTDTC', 'AEENDTC', 'AESER',
      // Lab
      'LBTESTCD', 'LBTEST', 'LBORRES', 'LBORRESU',
      // Vital Signs
      'VSTESTCD', 'VSTEST', 'VSSTRES', 'VSSTRESU'
    ];
    return standardFields.includes(name);
  }
}
```

### 2. 验证规则配置 (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CDASH Field Definition",
  "type": "object",
  "properties": {
    "cdashName": {
      "type": "string",
      "pattern": "^[A-Z]{2,3}[A-Z]+$",
      "maxLength": 64,
      "description": "CDASH 标准字段名"
    },
    "cdashLabel": {
      "type": "string",
      "maxLength": 256,
      "description": "字段标签"
    },
    "sdtmField": {
      "type": "string",
      "description": "对应的 SDTM 字段名"
    },
    "dataType": {
      "type": "string",
      "enum": ["ST", "NM", "DT", "TM", "LM", "CA"],
      "description": "数据类型"
    },
    "required": {
      "type": "boolean",
      "description": "是否必填"
    },
    "maxLength": {
      "type": "integer",
      "minimum": 1,
      "description": "最大长度"
    },
    "enumValues": {
      "type": "array",
      "items": { "type": "string" },
      "description": "枚举值列表"
    }
  },
  "required": ["cdashName", "cdashLabel", "dataType", "required"]
}
```

### 3. 验证规则引擎 (Python)

```python
from datetime import datetime
from typing import List, Dict, Any

class CDASHValidator:
    def __init__(self):
        self.rules = self._load_validation_rules()
    
    def _load_validation_rules(self):
        return {
            'age_range': {'min': 0, 'max': 120},
            'weight_range': {'min': 30, 'max': 250},
            'height_range': {'min': 100, 'max': 250},
            'sysbp_range': {'min': 40, 'max': 300},
            'dia_range': {'min': 20, 'max': 200}
        }
    
    def validate_age(self, dob, ref_date):
        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        ref_dt = datetime.strptime(ref_date, '%Y-%m-%d')
        
        age = (ref_dt - birth_date).days / 365.25
        
        if not (self.rules['age_range']['min'] <= age <= self.rules['age_range']['max']):
            return '年龄 {:.1f} 超出合理范围'.format(age)
        
        return 'Valid'
    
    def validate_lab_value(self, test, value):
        if test in self.rules:
            rule = self.rules[test]
            if value < rule['min'] or value > rule['max']:
                return '{} 值超出合理范围 ({}-{})'.format(test, rule['min'], rule['max'])
        
        return 'Valid'
    
    def validate_date_logic(self, date1, date2, comparison='lte'):
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        
        if comparison == 'lte' and not (d1 <= d2):
            return '{} 不应晚于 {}'.format(date1, date2)
        if comparison == 'gte' and not (d1 >= d2):
            return '{} 不应早于 {}'.format(date1, date2)
        
        return 'Valid'
```

---

## 实施时间表

| 阶段 | 时间 | 任务 |
|------|------|------|
| 第 1 周 | 第 1-7 天 | 学习 CDASH 标准，下载官方文档 |
| 第 2 周 | 第 8-14 天 | 创建字段库和验证规则 |
| 第 3-4 周 | 第 15-28 天 | eCRF 设计器原型开发 |
| 第 5-8 周 | 第 29-56 天 | EDC 数据录入模块开发 |
| 第 9-12 周 | 第 57-84 天 | SDTM 转换引擎开发 |
| 第 13-16 周 | 第 85-112 天 | 测试和优化 |

---

## 常见问题

### Q1: 如何获取完整的 CDASH v1.1 标准文档？
**A**: 访问 CDISC 官网注册账户，部分文档免费，完整标准需要订阅。

### Q2: CDASH 和 SDTM 有什么区别？
**A**: 
- CDASH: 数据采集标准 (用于 eCRF 设计和数据录入)
- SDTM: 数据交换标准 (用于向监管机构提交数据)
- CDASH 到 SDTM: 需要转换引擎

### Q3: 如何确保字段命名符合 CDASH 规范？
**A**: 
1. 使用标准字段 (从 CDASH 标准库选择)
2. 自定义字段遵循命名规则 (2-3 字母前缀 + 语义)
3. 实现字段名验证器

### Q4: 如何处理非标准字段？
**A**: 
- 尽量使用标准字段
- 自定义字段保持语义清晰
- 记录自定义字段与 SDTM 的映射关系
- 在转换文档中说明

---

## 联系方式

**项目**: Clinical Trial Platform  
**负责人**: Cai Yuheng (caiyuheng81@outlook.com)  
**文档维护**: Cai Yuheng  
**最后更新**: 2026-05-27

---

## 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-05-27 | 初始版本，包含 3 个核心文档 |

---

**注意**: CDASH 标准不断更新，建议定期查看 CDISC 官网获取最新版本。
