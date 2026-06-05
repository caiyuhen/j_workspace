# CDASH 标准资源使用指南

适用项目：Clinical Trial Platform (CTMS/EDC/IWRS + Physician EMR)
负责人：Cai Yuheng (蔡宇衡)
日期：2026-05-27

文档使用顺序

第一步：快速了解 (1 小时)
阅读：CDASH 标准资源总索引.md
- 了解 CDASH 整体框架
- 查看 16 个核心数据域
- 理解标准关系 (CDASH 到 SDTM 到 ADaM)
目标：快速建立 CDASH 概念框架

第二步：下载资源 (2 小时)
阅读：CDASH 标准下载指南.md
- 按步骤注册 CDISC 账户
- 下载免费文档 (Overview, User Guide)
- 克隆 GitHub 示例代码
目标：获取完整的标准文档和示例

第三步：深入学习 (1-2 天)
阅读顺序:
1. CDASH 标准资源索引.md - 详细理解每个数据域
2. CDASH 数据验证规则参考.md - 掌握验证规则
3. CDASH 到 SDTM 字段映射表.md - 熟悉字段映射
目标：深入理解 CDASH 标准和实现细节

第四步：实际应用 (持续)
使用场景:
1. eCRF 设计器开发
   - 参考 字段映射表 配置组件库
   - 使用 验证规则参考 实现前端验证
   
2. EDC 数据录入
   - 应用 验证规则 进行数据检查
   - 使用 字段映射 进行 SDTM 转换
   
3. SDTM 转换引擎
   - 基于 字段映射表 开发转换逻辑
   - 使用 验证规则 验证输出数据

文档内容速查

CDASH 字段命名规则
参考：CDASH 到 SDTM 字段映射表.md - 第 4 节
规则:
- 2-3 字母前缀 + 语义名称
- 大写，无下划线
- 最大长度 64 字符
示例:
- DOB (Date of Birth)
- AETERM (Adverse Event Term)
- LBTESTCD (Laboratory Test Code)

核心数据域 (16 个)
参考：CDASH 标准资源索引.md - 第 1 节
主要数据域:
1. DM - Demographics (人口统计学)
2. AE - Adverse Events (不良事件)
3. LB - Laboratory Tests (实验室检测)
4. VS - Vital Signs (生命体征)
5. EX - Exposure (暴露/用药)
6. CM - Current Medications (当前用药)
7. MH - Medical History (病史)
8. IC - Informed Consent (知情同意)
9. PRO - Patient Reported Outcomes (患者报告结果)
10. PG - Pregnancy (妊娠)
完整列表：参考 CDASH 标准资源总索引.md

验证规则示例
参考：CDASH 数据验证规则参考.md - 第 3 节
常用验证规则:

年龄验证
function validateAge(dob, refDate) {
    const birthDate = new Date(dob);
    const refDt = new Date(refDate);
    let age = (refDt - birthDate) / (365.25 * 24 * 60 * 60 * 1000);
    
    if (age < 0 || age > 120) {
        return '年龄 ' + age.toFixed(1) + ' 超出合理范围 (0-120)';
    }
    return 'Valid';
}

不良事件日期验证
function validateAEDates(aeData) {
    if (aeData.aeEndDTC && aeData.aeStartDTC) {
        const end = new Date(aeData.aeEndDTC);
        const start = new Date(aeData.aeStartDTC);
        
        if (end < start) {
            return '结束日期不能早于开始日期';
        }
    }
    return 'Valid';
}

技术实现建议

1. eCRF 设计器配置
字段组件配置 JSON:
{
  component: {
    name: Demographics,
    label: 人口统计学信息，
    fields: [
      {
        cdashName: DOB,
        cdashLabel: 出生日期，
        sdtmField: DOB,
        dataType: DT,
        required: true,
        validation: {
          type: date,
          min: 1900-01-01,
          max: 2026-01-01,
          message: 出生日期必须在合理范围内
        }
      },
      {
        cdashName: SEX,
        cdashLabel: 性别，
        sdtmField: SEX,
        dataType: CA,
        required: true,
        validation: {
          type: enum,
          values: [M, F, U],
          message: 性别必须是 M/F/U 之一
        }
      }
    ]
  }
}

2. 字段验证器实现
JavaScript 验证器类:
class CDASHValidator {
  constructor() {
    this.rules = this._loadRules();
  }
  
  _loadRules() {
    return {
      ST: { maxLength: 256 },
      NM: { min: null, max: null },
      DT: { format: YYYY-MM-DD },
      CA: { enum: [] }
    };
  }
  
  validate(field, value) {
    const type = field.dataType;
    const rule = this.rules[type];
    
    switch (type) {
      case ST:
        return this.validateString(field, value, rule);
      case NM:
        return this.validateNumber(field, value, rule);
      case DT:
        return this.validateDate(field, value, rule);
      case CA:
        return this.validateEnum(field, value, rule);
      default:
        return 'Valid';
    }
  }
  
  validateString(field, value, rule) {
    if (!value) {
      return field.required ? '此字段为必填项' : 'Valid';
    }
    if (value.length > rule.maxLength) {
      return '长度不能超过 ' + rule.maxLength + ' 字符';
    }
    return 'Valid';
  }
  
  validateDate(field, value, rule) {
    const pattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!pattern.test(value)) {
      return '日期格式必须是 YYYY-MM-DD';
    }
    return 'Valid';
  }
  
  validateEnum(field, value, rule) {
    if (field.validation && field.validation.values) {
      if (!field.validation.values.includes(value)) {
        return '必须是 ' + field.validation.values.join(', ') + ' 之一';
      }
    }
    return 'Valid';
  }
}

3. SDTM 转换引擎
Python 转换器示例:
class CDASHtoSDTMConverter:
  def __init__(self):
    self.mappings = self._load_mappings()
  
  def _load_mappings(self):
    加载字段映射表
    return {
      DM: {
        STUDYID: STUDYID,
        USUBJID: USUBJID,
        DOB: DOB,
        SEX: SEX,
        SITEID: SITEID
      },
      AE: {
        USUBJID: USUBJID,
        AETERM: AETERM,
        AESEQ: AESEQ,
        AESOC: AESOC,
        AESTDTC: AESTDTC
      }
    }
  
  def convert_demographics(self, cdash_data):
    转换 Demographics 数据
    mapping = self.mappings['DM']
    sdtm_record = {}
    
    for cdash_field, sdtm_field in mapping.items():
      if cdash_field in cdash_data:
        sdtm_record[sdtm_field] = cdash_data[cdash_field]
    
    return sdtm_record
  
  def convert_adverse_events(self, cdash_data):
    转换 Adverse Events 数据
    mapping = self.mappings['AE']
    sdtm_record = {}
    
    for cdash_field, sdtm_field in mapping.items():
      if cdash_field in cdash_data:
        sdtm_record[sdtm_field] = cdash_data[cdash_field]
    
    return sdtm_record

实施检查清单

设计阶段
[ ] 阅读 CDASH Overview，了解标准框架
[ ] 下载并研究 CDASH User Guide
[ ] 查看 ODM-XML 示例代码
[ ] 整理 16 个核心数据域的字段列表
[ ] 确定必须支持的数据域

开发阶段
[ ] 创建 eCRF 设计器组件库
[ ] 实现字段命名验证器
[ ] 实现数据类型验证器
[ ] 实现逻辑验证规则
[ ] 创建字段到 SDTM 的映射表
[ ] 实现 SDTM 转换引擎

测试阶段
[ ] 编写字段验证单元测试
[ ] 编写逻辑验证集成测试
[ ] 测试 SDTM 转换准确性
[ ] 验证数据完整性

问题排查

Q: 字段命名不符合 CDASH 规范？
A: 检查命名规则 (2-3 字母前缀 + 语义)，参考 字段映射表 的命名规范

Q: 验证规则不生效？
A: 
1. 检查验证规则 JSON 配置
2. 确认验证器类正确加载规则
3. 查看前端控制台错误日志

Q: SDTM 转换失败？
A: 
1. 检查字段映射表是否正确
2. 验证 CDASH 数据完整性
3. 检查 SDTM 必填字段是否填充

文档更新记录
日期：2026-05-27 | 内容：初始版本 | 负责人：Cai Yuheng

推荐阅读顺序

入门 (1 小时)
- CDASH 标准资源总索引.md
- CDASH 标准下载指南.md

进阶 (2-3 小时)
- CDASH 到 SDTM 字段映射表.md
- CDASH 数据验证规则参考.md

深入 (1-2 天)
- CDASH Official Overview PDF
- CDASH User Guide PDF
- GitHub ODM-XML 示例代码

文档维护：Cai Yuheng (caiyuheng81@outlook.com)
最后更新：2026-05-27
适用项目：Clinical Trial Platform
