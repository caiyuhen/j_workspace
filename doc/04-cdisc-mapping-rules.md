# CDISC 标准映射规则详解

## 一、CDISC 标准概述

### 1.1 CDISC 简介

**CDISC (Clinical Data Interchange Standards Consortium)** 是临床数据交换标准协会，制定临床试验数据标准。

**核心标准:**
- **CDASH (Clinical Data Acquisition Standards Harmonization)**: 数据采集标准
- **SDTM (Study Data Tabulation Model)**: 研究数据表模型
- **ADaM (Analysis Data Model)**: 分析数据模型
- **Define.xml**: 元数据描述标准

### 1.2 标准层级关系

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

---

## 二、CDASH 数据采集标准

### 2.1 CDASH 原则

#### 2.1.1 命名规范

```
原则：
1. 使用英文大写字母
2. 使用语义清晰的缩写
3. 避免使用特殊字符
4. 长度限制：4-30 个字符
5. 遵循 SDTM 变量命名规范

示例：
✅ 正确：SUBJID, AGE, SEX, RANDDT, WEIGHT, HEIGHT
❌ 错误：subject_id, age (小写), PatientID, 1AGE
```

#### 2.1.2 数据类型

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
    values: ' predefined'
  }
};
```

### 2.2 CDASH 标准字段

#### 2.2.1 受试者特征 (DM 域对应)

```javascript
const CDASHDMFields = [
  {
    cdashVariable: 'SUBJID',
    cdashName: 'Subject Identifier',
    chineseName: '受试者编号',
    sdmtVariable: 'SUBJID',
    dataType: 'Character',
    maxLength: 25,
    required: true,
    description: '试验内唯一标识受试者的编号'
  },
  {
    cdashVariable: 'BIRTHDT',
    cdashName: 'Date of Birth',
    chineseName: '出生日期',
    sdmtVariable: 'BRTHDT',
    dataType: 'Date',
    format: 'YYYY-MM-DD',
    required: true,
    description: '受试者出生日期'
  },
  {
    cdashVariable: 'AGE',
    cdashName: 'Age',
    chineseName: '年龄',
    sdmtVariable: 'AGE',
    dataType: 'Numeric',
    unit: 'years',
    required: true,
    description: '试验入组时年龄（周岁）'
  },
  {
    cdashVariable: 'AGEU',
    cdashName: 'Age Unit',
    chineseName: '年龄单位',
    sdmtVariable: 'AGEU',
    dataType: 'Character',
    values: ['years', 'months', 'days'],
    defaultValue: 'years',
    required: true
  },
  {
    cdashVariable: 'SEX',
    cdashName: 'Sex',
    chineseName: '性别',
    sdmtVariable: 'SEX',
    dataType: 'Character',
    values: ['M', 'F', 'U'],
    displayValues: ['男', '女', '未知'],
    required: true,
    description: '受试者生理性别'
  },
  {
    cdashVariable: 'RACE',
    cdashName: 'Race',
    chineseName: '种族',
    sdmtVariable: 'RACE',
    dataType: 'Character',
    required: false,
    description: '受试者种族'
  },
  {
    cdashVariable: 'ETHNIC',
    cdashName: 'Ethnicity',
    chineseName: '民族',
    sdmtVariable: 'ETHNIC',
    dataType: 'Character',
    values: ['HISPANIC OR LATINO', 'NOT HISPANIC OR LATINO', 'UNKNOWN'],
    required: false
  },
  {
    cdashVariable: 'WEIGHT',
    cdashName: 'Weight',
    chineseName: '体重',
    sdmtVariable: 'WT',
    dataType: 'Numeric',
    unit: 'kg',
    required: true,
    description: '入组时体重'
  },
  {
    cdashVariable: 'HEIGHT',
    cdashName: 'Height',
    chineseName: '身高',
    sdmtVariable: 'HT',
    dataType: 'Numeric',
    unit: 'cm',
    required: true,
    description: '入组时身高'
  },
  {
    cdashVariable: 'BMI',
    cdashName: 'Body Mass Index',
    chineseName: '体重指数',
    sdmtVariable: 'BMI',
    dataType: 'Numeric',
    precision: 2,
    required: false,
    description: '体重指数（可由身高体重计算）'
  }
];
```

#### 2.2.2 实验室检查 (LB 域对应)

```javascript
const CDASHLBFields = [
  {
    cdashVariable: 'LBDTC',
    cdashName: 'Collection Date/Time',
    chineseName: '采集日期时间',
    sdmtVariable: 'LBDTC',
    dataType: 'DateTime',
    required: true
  },
  {
    cdashVariable: 'LBTESTCD',
    cdashName: 'Test Short Name',
    chineseName: '检查项目代码',
    sdmtVariable: 'LBTESTCD',
    dataType: 'Character',
    maxLength: 10,
    required: true,
    description: 'CDISC 标准检查项目代码'
  },
  {
    cdashVariable: 'LBTEST',
    cdashName: 'Test Name',
    chineseName: '检查项目名称',
    sdmtVariable: 'LBTEST',
    dataType: 'Character',
    maxLength: 200,
    required: true
  },
  {
    cdashVariable: 'LBORRES',
    cdashName: 'Original Result',
    chineseName: '原始结果',
    sdmtVariable: 'LBORRES',
    dataType: 'Character',
    maxLength: 200,
    required: true
  },
  {
    cdashVariable: 'LBORNRLO',
    cdashName: 'Reference Low',
    chineseName: '参考范围下限',
    sdmtVariable: 'LBNRLO',
    dataType: 'Numeric',
    required: false
  },
  {
    cdashVariable: 'LBORNRHI',
    cdashName: 'Reference High',
    chineseName: '参考范围上限',
    sdmtVariable: 'LBNRHI',
    dataType: 'Numeric',
    required: false
  },
  {
    cdashVariable: 'LBORRESU',
    cdashName: 'Original Result Unit',
    chineseName: '原始结果单位',
    sdmtVariable: 'LBORRESU',
    dataType: 'Character',
    maxLength: 20,
    required: true
  },
  {
    cdashVariable: 'LBNRIND',
    cdashName: 'Normalcy Indicator',
    chineseName: '正常性指标',
    sdmtVariable: 'LBNRIND',
    dataType: 'Character',
    values: ['N', 'H', 'L', 'HH', 'LL'],
    displayValues: ['正常', '偏高', '偏低', '严重偏高', '严重偏低'],
    required: false
  }
];
```

#### 2.2.3 不良事件 (AE 域对应)

```javascript
const CDASHAEFields = [
  {
    cdashVariable: 'AESTDTC',
    cdashName: 'Start Date/Time',
    chineseName: '发生日期时间',
    sdmtVariable: 'AESTDTC',
    dataType: 'DateTime',
    required: true
  },
  {
    cdashVariable: 'AEENDTC',
    cdashName: 'End Date/Time',
    chineseName: '结束日期时间',
    sdmtVariable: 'AEENDTC',
    dataType: 'DateTime',
    required: false
  },
  {
    cdashVariable: 'AETERM',
    cdashName: 'Term',
    chineseName: '不良事件术语',
    sdmtVariable: 'AETERM',
    dataType: 'Character',
    maxLength: 200,
    required: true,
    description: 'MedDRA 术语'
  },
  {
    cdashVariable: 'AESEV',
    cdashName: 'Severity',
    chineseName: '严重程度',
    sdmtVariable: 'AESEV',
    dataType: 'Character',
    values: ['MILD', 'MODERATE', 'SEVERE'],
    displayValues: ['轻度', '中度', '重度'],
    required: true
  },
  {
    cdashVariable: 'AEREL',
    cdashName: 'Relatedness',
    chineseName: '相关性',
    sdmtVariable: 'AEREL',
    dataType: 'Character',
    values: ['NOT RELATED', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY LIKELY'],
    displayValues: ['无关', '可能无关', '可能相关', '很可能相关', '很可能相关'],
    required: true
  },
  {
    cdashVariable: 'AEOUT',
    cdashName: 'Outcome',
    chineseName: '转归',
    sdmtVariable: 'AEOUT',
    dataType: 'Character',
    values: ['RECOVERED/RESOLVED', 'NOT RECOVERED/NOT RESOLVED', 'RECOVERED/RESOLVED WITH SEQUELAE', 
             'FATAL', 'NOT RECOVERED/RESOLVED WITH SEQUELAE', 'UNKNOWN'],
    required: false
  },
  {
    cdashVariable: 'AESER',
    cdashName: 'Serious Event',
    chineseName: '严重不良事件',
    sdmtVariable: 'AESER',
    dataType: 'Boolean',
    values: ['Y', 'N'],
    required: true
  }
];
```

### 2.3 CDASH 访视设计

```javascript
const CDASHVisitDesign = {
  // 标准访视
  standardVisits: [
    {
      visitCode: 'SCREENING',
      visitName: '筛选期',
      timing: {
        minDay: -30,
        maxDay: -1
      },
      allowed: true
    },
    {
      visitCode: 'BASELINE',
      visitName: '基线',
      timing: {
        minDay: -1,
        maxDay: 1
      },
      allowed: true,
      mandatory: true
    },
    {
      visitCode: 'V1',
      visitName: '访视 1',
      timing: {
        minDay: 1,
        maxDay: 7
      },
      allowed: true
    },
    {
      visitCode: 'V2',
      visitName: '访视 2',
      timing: {
        minDay: 15,
        maxDay: 21
      },
      allowed: true
    },
    {
      visitCode: 'V3',
      visitName: '访视 3',
      timing: {
        minDay: 29,
        maxDay: 35
      },
      allowed: true
    },
    {
      visitCode: 'ENDOFTRT',
      visitName: '治疗结束',
      timing: {
        minDay: null,
        maxDay: null
      },
      allowed: true,
      mandatory: true
    },
    {
      visitCode: 'FOLLOWUP',
      visitName: '随访',
      timing: {
        minDay: 36,
        maxDay: 90
      },
      allowed: true
    }
  ],
  
  // 访视窗口期设计原则
  windowRules: {
    tightWindow: {
      min: -1,
      max: 1,
      description: '紧密窗口，适用于基线评估'
    },
    standardWindow: {
      min: -7,
      max: 7,
      description: '标准窗口，适用于常规访视'
    },
    looseWindow: {
      min: -14,
      max: 14,
      description: '宽松窗口，适用于长期随访'
    }
  }
};
```

---

## 三、SDTM 数据模型

### 3.1 SDTM 域定义

#### 3.1.1 一般信息域 (General Purpose)

```javascript
const SDTMGeneralDomains = {
  DM: {
    domainName: 'Demographics',
    domainDescription: '受试者特征',
    required: true,
    variables: [
      {
        variable: 'STUDYID',
        label: 'Study Identifier',
        dataType: 'Character',
        maxLength: 200,
        required: true,
        definition: '试验编号'
      },
      {
        variable: 'USUBJID',
        label: 'Unique Subject Identifier',
        dataType: 'Character',
        maxLength: 100,
        required: true,
        definition: '受试者唯一标识符'
      },
      {
        variable: 'SUBJID',
        label: 'Subject Identifier for the Study',
        dataType: 'Character',
        maxLength: 50,
        required: true,
        definition: '研究内受试者编号'
      },
      {
        variable: 'AGE',
        label: 'Age',
        dataType: 'Numeric',
        precision: 0,
        required: true,
        definition: '入组时年龄（周岁）'
      },
      {
        variable: 'AGEU',
        label: 'Age Unit',
        dataType: 'Character',
        maxLength: 10,
        required: true,
        values: ['years', 'months', 'days'],
        definition: '年龄单位'
      },
      {
        variable: 'SEX',
        label: 'Sex',
        dataType: 'Character',
        maxLength: 10,
        required: true,
        values: ['M', 'F', 'U'],
        definition: '性别'
      },
      {
        variable: 'RACE',
        label: 'Race',
        dataType: 'Character',
        maxLength: 100,
        required: false,
        definition: '种族'
      },
      {
        variable: 'ETHNIC',
        label: 'Ethnicity',
        dataType: 'Character',
        maxLength: 10,
        required: false,
        values: ['HISPANIC OR LATINO', 'NOT HISPANIC OR LATINO', 'UNKNOWN'],
        definition: '民族'
      },
      {
        variable: 'SITEID',
        label: 'Study Site Identifier',
        dataType: 'Character',
        maxLength: 50,
        required: true,
        definition: '研究中心编号'
      },
      {
        variable: 'COUNTRY',
        label: 'Country',
        dataType: 'Character',
        maxLength: 100,
        required: true,
        definition: '研究中心所在国家'
      }
    ],
    keys: ['STUDYID', 'USUBJID'],
    perSubject: true
  },
  
  AE: {
    domainName: 'Adverse Events',
    domainDescription: '不良事件',
    required: true,
    variables: [
      {
        variable: 'STUDYID',
        label: 'Study Identifier',
        dataType: 'Character',
        maxLength: 200,
        required: true
      },
      {
        variable: 'USUBJID',
        label: 'Unique Subject Identifier',
        dataType: 'Character',
        maxLength: 100,
        required: true
      },
      {
        variable: 'AESEQ',
        label: 'Sequence Number',
        dataType: 'Numeric',
        precision: 0,
        required: true,
        definition: '不良事件序号（受试者内唯一）'
      },
      {
        variable: 'AETERM',
        label: 'Adverse Event Term',
        dataType: 'Character',
        maxLength: 200,
        required: true,
        definition: '不良事件术语（MedDRA 术语）'
      },
      {
        variable: 'AEDECOD',
        label: 'Adverse Event Preferred Term',
        dataType: 'Character',
        maxLength: 200,
        required: true,
        definition: '不良事件首选术语（MedDRA PT）'
      },
      {
        variable: 'AEBODSYS',
        label: 'Adverse Event System Organ Class',
        dataType: 'Character',
        maxLength: 200,
        required: true,
        definition: '不良事件系统器官分类（MedDRA SOC）'
      },
      {
        variable: 'AESEV',
        label: 'Severity/Intensity',
        dataType: 'Character',
        maxLength: 20,
        required: true,
        values: ['MILD', 'MODERATE', 'SEVERE'],
        definition: '严重程度'
      },
      {
        variable: 'AEREL',
        label: 'Relatedness to Study Procedure',
        dataType: 'Character',
        maxLength: 20,
        required: true,
        values: ['NOT RELATED', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY LIKELY'],
        definition: '与研究的相关性'
      },
      {
        variable: 'AESTDTC',
        label: 'Date/Time of Onset',
        dataType: 'DateTime',
        required: true,
        definition: '不良事件开始日期时间'
      },
      {
        variable: 'AEENDTC',
        label: 'Date/Time of Completion',
        dataType: 'DateTime',
        required: false,
        definition: '不良事件结束日期时间'
      },
      {
        variable: 'AEOUT',
        label: 'Outcome of Adverse Event',
        dataType: 'Character',
        maxLength: 20,
        required: false,
        values: ['RECOVERED/RESOLVED', 'NOT RECOVERED/NOT RESOLVED', 'RECOVERED/RESOLVED WITH SEQUELAE', 
                 'FATAL', 'NOT RECOVERED/RESOLVED WITH SEQUELAE', 'UNKNOWN'],
        definition: '不良事件转归'
      },
      {
        variable: 'AESER',
        label: 'Serious Adverse Event',
        dataType: 'Character',
        maxLength: 1,
        required: true,
        values: ['Y', 'N'],
        definition: '是否为严重不良事件'
      }
    ],
    keys: ['STUDYID', 'USUBJID', 'AESEQ'],
    perSubject: false
  }
};
```

#### 3.1.2 其他常用域

```javascript
const SDTMOtherDomains = {
  EX: {
    domainName: 'Exposure',
    domainDescription: '暴露',
    variables: [
      'STUDYID', 'USUBJID', 'EXSEQ', 'EXTRT', 'EXTRTP', 'EXDOSE',
      'EXDOSU', 'EXSTDTC', 'EXENDTC', 'EXRFDOSE', 'EXRFDOSU'
    ]
  },
  
  LB: {
    domainName: 'Laboratory Test Results',
    domainDescription: '实验室检查',
    variables: [
      'STUDYID', 'USUBJID', 'LBBASE', 'LBDY', 'LBDSL',
      'LBCAT', 'LBTESTCD', 'LBTEST', 'LBORRES', 'LBORRESU',
      'LBNRLO', 'LBNRHI', 'LBNRIND', 'LBDTC'
    ]
  },
  
  DS: {
    domainName: 'Disposition',
    domainDescription: '状态',
    variables: [
      'STUDYID', 'USUBJID', 'DSSEQ', 'DSCAT', 'DSDECOD',
      'DSDOM', 'DSTERM', 'DSRSLT', 'DSSTDTC', 'DSENDTC'
    ]
  },
  
  VS: {
    domainName: 'Vital Signs',
    domainDescription: '生命体征',
    variables: [
      'STUDYID', 'USUBJID', 'VSSEQ', 'VSTESTCD', 'VSTEST',
      'VSORRES', 'VSORRESU', 'VSSTRESC', 'VSSTRESN', 'VSSTRESU',
      'VSDTC', 'VSBASIS', 'VSPER'
    ]
  },
  
  CE: {
    domainName: 'Consent',
    domainDescription: '知情同意',
    variables: [
      'STUDYID', 'USUBJID', 'CETESTCD', 'CETEST', 'CEORRES',
      'CEDTC', 'CECAT', 'CEVAR'
    ]
  }
};
```

### 3.2 SDTM 变量命名规则

```javascript
const SDTMNamingRules = {
  // 命名结构
  structure: {
    prefix: '2 位字母前缀，表示域',
    base: '基础名称',
    suffix: '可选后缀，表示派生'
  },
  
  // 常见后缀
  suffixes: [
    { suffix: 'DT', type: 'Date', example: 'RANDDT' },
    { suffix: 'DTC', type: 'Date/Time Character', example: 'EXSTDTC' },
    { suffix: 'ST', type: 'Start', example: 'EXSTRT' },
    { suffix: 'EN', type: 'End', example: 'EXENDT' },
    { suffix: 'OC', type: 'Object', example: 'AEOC' },
    { suffix: 'OR', type: 'Original', example: 'LBORRES' },
    { suffix: 'RE', type: 'Result', example: 'LBORRES' },
    { suffix: 'SC', type: 'String', example: 'LBSTRESC' },
    { suffix: 'SN', type: 'Numeric', example: 'LBSTRESN' },
    { suffix: 'U', type: 'Unit', example: 'AGEU' }
  ],
  
  // 命名示例
  examples: [
    { original: 'SUBJID', explanation: 'Subject Identifier' },
    { original: 'RANDDT', explanation: 'Randomization Date' },
    { original: 'RANDDTC', explanation: 'Randomization Date/Time Character' },
    { original: 'WEIGHT', explanation: 'Weight (SDTM: WT)' },
    { original: 'HEIGHT', explanation: 'Height (SDTM: HT)' },
    { original: 'LBTESTCD', explanation: 'Laboratory Test Code' },
    { original: 'LBORRES', explanation: 'Laboratory Original Result' },
    { original: 'AESEV', explanation: 'Adverse Event Severity' }
  ]
};
```

---

## 四、CDASH → SDTM 映射规则

### 4.1 映射原理

```
eCRF 字段 (CDASH)     →     SDTM 变量
├─ 字段编码             →    变量名
├─ 字段名称             →    变量标签
├─ 数据类型             →    变量类型
├─ 验证规则             →    值集约束
├─ 访视设计             →    域分组
└─ 数据值               →    域记录
```

### 4.2 自动映射规则

```javascript
class CDASHTOSDTMMapper {
  
  /**
   * 自动映射规则库
   */
  autoMappingRules = {
    // 标准字段映射
    standardFields: {
      'SUBJID': { cdash: '受试者编号', sdtm: 'SUBJID', domain: 'DM' },
      'RANDDT': { cdash: '随机化日期', sdtm: 'RANDDT', domain: 'DM' },
      'AGE': { cdash: '年龄', sdtm: 'AGE', domain: 'DM' },
      'SEX': { cdash: '性别', sdtm: 'SEX', domain: 'DM' },
      'WEIGHT': { cdash: '体重', sdtm: 'WT', domain: 'EX' },
      'HEIGHT': { cdash: '身高', sdtm: 'HT', domain: 'EX' },
      'BMI': { cdash: '体重指数', sdtm: 'BMI', domain: 'EX' },
      'BIRTHDT': { cdash: '出生日期', sdtm: 'BRTHDT', domain: 'DM' }
    },
    
    // 命名转换规则
    namingConversion: {
      // 日期字段
      dateFields: {
        pattern: /\b(日期|date|dt|time)\b/i,
        sdtmSuffix: 'DTC',
        cdashSuffix: 'DTC'
      },
      
      // 数值字段
      numericFields: {
        pattern: /\b(数值|number|num|int)\b/i,
        sdtmSuffix: 'N',
        cdashSuffix: ''
      },
      
      // 字符串字段
      stringFields: {
        pattern: /\b(字符|text|str)\b/i,
        sdtmSuffix: 'SC',
        cdashSuffix: 'C'
      }
    }
  };
  
  /**
   * 执行映射
   */
  mapToSDTM(cdashField, domain) {
    // 1. 检查是否为标准字段
    const standardMapping = this.autoMappingRules.standardFields[cdashField.cdashVariable];
    if (standardMapping) {
      return {
        ...standardMapping,
        originalCode: cdashField.cdashVariable,
        originalName: cdashField.cdashName
      };
    }
    
    // 2. 自定义字段映射
    return this.customMapping(cdashField, domain);
  }
  
  /**
   * 自定义字段映射
   */
  customMapping(field, domain) {
    const cdashCode = field.cdashVariable;
    
    // 转换 CDASH 代码为 SDTM 代码
    const sdtmCode = this.transformToSDTMCode(cdashCode, domain);
    
    return {
      sdtmVariable: sdtmCode,
      sdtmLabel: field.cdashName,
      domain: domain,
      dataType: field.dataType,
      maxLength: field.maxLength,
      unit: field.unit,
      values: field.codelist
    };
  }
  
  /**
   * 转换代码格式
   */
  transformToSDTMCode(cdashCode, domain) {
    // 特殊规则
    const specialMappings = {
      'WEIGHT': 'WT',
      'HEIGHT': 'HT',
      'BIRTHDT': 'BRTHDT',
      'SEX': 'SEX',
      'RACE': 'RACE',
      'ETHNIC': 'ETHNIC'
    };
    
    if (specialMappings[cdashCode]) {
      return specialMappings[cdashCode];
    }
    
    // 默认转换
    return cdashCode;
  }
}
```

### 4.3 映射转换示例

```javascript
// 示例 1: 受试者基本信息
const cdashSubjectInfo = {
  fields: [
    {
      cdashVariable: 'SUBJID',
      cdashName: '受试者编号',
      dataType: 'Character',
      maxLength: 12
    },
    {
      cdashVariable: 'BIRTHDT',
      cdashName: '出生日期',
      dataType: 'Date',
      format: 'YYYY-MM-DD'
    },
    {
      cdashVariable: 'AGE',
      cdashName: '年龄',
      dataType: 'Numeric',
      unit: 'years'
    },
    {
      cdashVariable: 'SEX',
      cdashName: '性别',
      dataType: 'Character',
      values: ['M', 'F', 'U']
    }
  ]
};

// 转换为 SDTM DM 域
const sdtmDM = {
  domain: 'DM',
  variables: [
    {
      variable: 'SUBJID',
      label: 'Subject Identifier for the Study',
      dataType: 'Character',
      maxLength: 50
    },
    {
      variable: 'BRTHDT',
      label: 'Date of Birth',
      dataType: 'Date',
      format: 'YYYY-MM-DD'
    },
    {
      variable: 'AGE',
      label: 'Age',
      dataType: 'Numeric',
      precision: 0
    },
    {
      variable: 'AGEU',
      label: 'Age Unit',
      dataType: 'Character',
      values: ['years', 'months', 'days'],
      defaultValue: 'years'
    },
    {
      variable: 'SEX',
      label: 'Sex',
      dataType: 'Character',
      values: ['M', 'F', 'U']
    }
  ]
};
```

### 4.4 验证规则转换

```javascript
// CDASH 验证规则 → SDTM 值集约束
const validationRulesConversion = {
  // 必填规则
  required: {
    cdash: 'required: true',
    sdtm: { required: true, definition: 'Required in SDTM' }
  },
  
  // 范围规则
  range: {
    cdash: 'min: 18, max: 85',
    sdtm: { 
      definition: 'Valid range: 18-85 years',
      check: 'AGE >= 18 AND AGE <= 85'
    }
  },
  
  // 枚举规则
  codelist: {
    cdash: "values: ['M', 'F', 'U']",
    sdtm: {
      codelist: 'CLSEX',
      values: ['M', 'F', 'U'],
      display: ['Male', 'Female', 'Unknown']
    }
  },
  
  // 正则规则
  regex: {
    cdash: 'pattern: "^[A-Z0-9]{6,12}$"',
    sdtm: {
      definition: 'Must be 6-12 alphanumeric characters',
      check: 'SUBJID matches pattern'
    }
  }
};
```

---

## 五、Define.xml 生成

### 5.1 Define.xml 结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ODM xmlns="http://cdisc.org/ns/odm/v1.3"
     FileType="Snapshot"
     ODMVersion="1.3"
     Originator="Clinical Trial Platform">
  
  <Study OID="TRIAL001" Name="Test Study">
    
    <!-- 元数据 -->
    <MetaDataVersion OID="MV1" Name="Version 1.0">
      
      <!-- SDTM 定义 -->
      <ItemDef OID="DM.SUBJID" Name="Subject Identifier for the Study"
               DataType="text" Length="50" RequiredIndicator="Y">
        <Definition>受试者编号</Definition>
      </ItemDef>
      
      <ItemDef OID="DM.SEX" Name="Sex" DataType="text" Length="10" RequiredIndicator="Y">
        <Definition>性别</Definition>
        <CodeListRef OID="CLSEX"/>
      </ItemDef>
      
      <!-- 值集定义 -->
      <CodeList OID="CLSEX" Name="Sex" DataType="text">
        <ItemLabel Selection="Y">Male</ItemLabel>
        <ItemLabel Selection="M">Male</ItemLabel>
        <ItemLabel Selection="N">Female</ItemLabel>
        <ItemLabel Selection="U">Unknown</ItemLabel>
      </CodeList>
      
      <!-- 研究数据表 -->
      <StudyData StudyOID="TRIAL001">
        <StudySubject StudySubjectOID="S001" SubjectKey="SUBJ001">
          <StudyEventData StudyEventOID="SCREENING">
            <FormData FormDataOID="DM">
              <ItemData ItemOID="DM.SUBJID" Value="S001"/>
              <ItemData ItemOID="DM.SEX" Value="M"/>
            </FormData>
          </StudyEventData>
        </StudySubject>
      </StudyData>
      
    </MetaDataVersion>
  </Study>
</ODM>
```

### 5.2 Define.xml 生成代码

```java
@Component
public class DefineXMLGenerator {
  
  /**
   * 生成 Define.xml
   */
  public String generateDefineXML(Trial trial, List<SdtmDomain> domains) {
    StringBuilder xml = new StringBuilder();
    
    // XML 头部
    xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
    xml.append("<ODM xmlns=\"http://cdisc.org/ns/odm/v1.3\" ");
    xml.append("FileType=\"Snapshot\" ");
    xml.append("ODMVersion=\"1.3\" ");
    xml.append("Originator=\"Clinical Trial Platform\">\n\n");
    
    // 研究信息
    xml.append("  <Study OID=\"").append(trial.getTrialCode()).append("\" ");
    xml.append("Name=\"").append(trial.getTrialName()).append("\">\n");
    
    // 元数据版本
    xml.append("    <MetaDataVersion OID=\"MV1\" Name=\"Version 1.0\">\n");
    
    // SDTM 域定义
    for (SdtmDomain domain : domains) {
      xml.append("      ").append(generateDomainDefinition(domain));
    }
    
    // 值集定义
    xml.append("      ").append(generateCodelists(trial));
    
    // 数据定义
    xml.append("      ").append(generateStudyData(trial, domains));
    
    xml.append("    </MetaDataVersion>\n");
    xml.append("  </Study>\n");
    xml.append("</ODM>");
    
    return xml.toString();
  }
  
  /**
   * 生成域定义
   */
  private String generateDomainDefinition(SdtmDomain domain) {
    StringBuilder sb = new StringBuilder();
    sb.append("      <ItemGroupDef OID=\"").append(domain.getDomain()).append("\" ");
    sb.append("Name=\"").append(domain.getDomainName()).append("\" ");
    sb.append("Repeating=\"No\" Type=\"").append(domain.getDomainName()).append("\">\n");
    
    for (Item item : domain.getItems()) {
      sb.append("        ").append(generateItemDef(item));
    }
    
    sb.append("      </ItemGroupDef>\n");
    return sb.toString();
  }
}
```

---

## 六、数据验证规则

### 6.1 SDTM 验证规则

```javascript
const SDTMValidationRules = {
  // DM 域验证规则
  DM: {
    required: ['STUDYID', 'USUBJID', 'SUBJID', 'AGE', 'AGEU', 'SEX', 'SITEID', 'COUNTRY'],
    unique: ['STUDYID', 'USUBJID'],
    format: {
      'AGE': { type: 'numeric', min: 0, max: 150 },
      'AGEU': { type: 'codelist', values: ['years', 'months', 'days'] },
      'SEX': { type: 'codelist', values: ['M', 'F', 'U'] }
    },
    logic: [
      {
        rule: 'AGE >= 0',
        message: '年龄必须大于等于 0'
      },
      {
        rule: 'AGEU = "years" OR AGEU = "months" OR AGEU = "days"',
        message: '年龄单位必须是 years、months 或 days'
      }
    ]
  },
  
  // AE 域验证规则
  AE: {
    required: ['STUDYID', 'USUBJID', 'AESEQ', 'AETERM', 'AEDECOD', 'AEBODSYS',
               'AESEV', 'AEREL', 'AESTDTC', 'AESER'],
    unique: ['STUDYID', 'USUBJID', 'AESEQ'],
    format: {
      'AESEV': { type: 'codelist', values: ['MILD', 'MODERATE', 'SEVERE'] },
      'AESER': { type: 'codelist', values: ['Y', 'N'] }
    }
  },
  
  // LB 域验证规则
  LB: {
    required: ['STUDYID', 'USUBJID', 'LBDTC', 'LBTESTCD', 'LBTEST', 'LBORRES', 'LBORRESU'],
    unique: ['STUDYID', 'USUBJID', 'LBDTC', 'LBTESTCD']
  }
};
```

### 6.2 逻辑验证引擎

```java
@Component
public class LogicalValidationEngine {
  
  /**
   * 执行逻辑验证
   */
  public ValidationResult validateLogical(Trial trial, Map<String, Object> data) {
    ValidationResult result = new ValidationResult();
    
    // DM 域逻辑验证
    if (data.containsKey("DM")) {
      Map<String, Object> dm = (Map<String, Object>) data.get("DM");
      
      // 年龄逻辑验证
      validateAgeLogic(dm, result);
      
      // 随机化日期逻辑验证
      validateRandomizationLogic(dm, trial, result);
    }
    
    // AE 域逻辑验证
    if (data.containsKey("AE")) {
      List<Map<String, Object>> aeList = (List<Map<String, Object>>) data.get("AE");
      
      for (Map<String, Object> ae : aeList) {
        validateAELogic(ae, result);
      }
    }
    
    // LB 域逻辑验证
    if (data.containsKey("LB")) {
      List<Map<String, Object>> lbList = (List<Map<String, Object>>) data.get("LB");
      
      for (Map<String, Object> lb : lbList) {
        validateLBLogic(lb, result);
      }
    }
    
    return result;
  }
  
  /**
   * 年龄逻辑验证
   */
  private void validateAgeLogic(Map<String, Object> dm, ValidationResult result) {
    Object age = dm.get("AGE");
    Object birthDate = dm.get("BIRTHDT");
    Object randDate = dm.get("RANDDT");
    
    if (age != null && birthDate != null && randDate != null) {
      // 计算实际年龄
      int calculatedAge = calculateAge(birthDate, (Date) randDate);
      
      // 验证年龄一致性
      if (Math.abs(calculatedAge - (Integer) age) > 1) {
        result.addError("AGE", "计算年龄与实际年龄不一致");
      }
    }
  }
  
  /**
   * 随机化日期逻辑验证
   */
  private void validateRandomizationLogic(Map<String, Object> dm, Trial trial, 
                                          ValidationResult result) {
    Object randDate = dm.get("RANDDT");
    Object screenDate = dm.get("SCRDT");
    
    if (randDate != null && screenDate != null) {
      Date screen = (Date) screenDate;
      Date rand = (Date) randDate;
      
      // 随机化日期不能早于筛选日期
      if (rand.before(screen)) {
        result.addError("RANDDT", "随机化日期不能早于筛选日期");
      }
    }
  }
  
  /**
   * 不良事件逻辑验证
   */
  private void validateAELogic(Map<String, Object> ae, ValidationResult result) {
    Object aedtc = ae.get("AESTDTC");
    Object enddtc = ae.get("AEENDTC");
    Object ser = ae.get("AESER");
    
    if (aedtc != null && enddtc != null) {
      Date start = (Date) aedtc;
      Date end = (Date) enddtc;
      
      // 结束日期不能早于开始日期
      if (end.before(start)) {
        result.addError("AEENDTC", "不良事件结束日期不能早于开始日期");
      }
    }
    
    // 严重不良事件必须有结束日期或转归
    if ("Y".equals(ser)) {
      if (enddtc == null || ae.get("AEOUT") == null) {
        result.addError("AESER", "严重不良事件必须有结束日期或转归");
      }
    }
  }
  
  /**
   * 计算年龄
   */
  private int calculateAge(Date birthDate, Date referenceDate) {
    Calendar birth = Calendar.getInstance();
    birth.setTime(birthDate);
    
    Calendar reference = Calendar.getInstance();
    reference.setTime(referenceDate);
    
    int age = reference.get(Calendar.YEAR) - birth.get(Calendar.YEAR);
    
    // 如果还没到生日，年龄减 1
    if (reference.get(Calendar.DAY_OF_YEAR) < birth.get(Calendar.DAY_OF_YEAR)) {
      age--;
    }
    
    return age;
  }
}
```

---

## 七、数据导出与转换

### 7.1 eCRF → SDTM 转换

```java
@Component
public class DataConverter {
  
  /**
   * 将 eCRF 表单数据转换为 SDTM 格式
   */
  public List<SdtmDm> convertToSDTM(List<FormSubmission> submissions) {
    return submissions.stream()
      .map(submission -> {
        SdtmDm dm = new SdtmDm();
        
        // 基本信息转换
        dm.setSTUDYID(submission.getTrialCode());
        dm.setUSUBJID(submission.getSubjectCode());
        dm.setSUBJID(submission.getSubjectCode());
        
        // 随机化信息
        dm.setRMSTRTCD(submission.getTreatmentArm());
        dm.setACTARMCD(submission.getTreatmentArm());
        
        // 人口学信息
        dm.setSEX(submission.getGender());
        dm.setRACEF(submission.getEthnicity());
        dm.setAGE((Integer) submission.getAge());
        dm.setAGEU("years");
        
        // 中心信息
        dm.setSITEID(submission.getSiteCode());
        dm.setCOUNTRY("China");
        
        // 状态
        dm.setSPRTRTFL("Y");
        dm.setSPRTRT(submission.getTreatmentArm());
        
        return dm;
      })
      .collect(Collectors.toList());
  }
  
  /**
   * 生成 SDTM 数据集文件
   */
  public SDTMFileset generateSDTMFileset(Trial trial, 
                                         Map<String, List<?>> sdtmData) {
    SDTMFileset fileset = new SDTMFileset();
    fileset.setStudyId(trial.getTrialCode());
    
    // 生成每个域的 SDTM 数据集
    for (Map.Entry<String, List<?>> entry : sdtmData.entrySet()) {
      String domain = entry.getKey();
      List<?> data = entry.getValue();
      
      SdtmDataset dataset = new SdtmDataset();
      dataset.setDomain(domain);
      dataset.setRecords(data);
      dataset.setMetadata(generateDomainMetadata(domain));
      
      fileset.addDataset(dataset);
    }
    
    // 生成 Define.xml
    fileset.setDefineXML(generateDefineXML(trial, sdtmData));
    
    // 生成 SDTM 数据集说明文档
    fileset.setConcordanceFile(generateConcordanceFile(trial, sdtmData));
    
    return fileset;
  }
  
  /**
   * 生成域元数据
   */
  private SDTMDomainMetadata generateDomainMetadata(String domain) {
    SDTMDomainMetadata metadata = new SDTMDomainMetadata();
    metadata.setDomain(domain);
    metadata.setVariables(getDomainVariables(domain));
    return metadata;
  }
}
```

---

## 八、最佳实践

### 8.1 CDASH 设计原则

```
✅ 正确做法:
1. 使用标准 CDASH 字段名
2. 遵循 CDASH 命名规范
3. 明确访视窗口期
4. 定义清晰的验证规则
5. 保持中英文对照
6. 使用统一的值集
7. 设计可维护的表单结构

❌ 错误做法:
1. 使用任意字段名 (如：subject_name, patient_id)
2. 不遵循 CDASH 命名规范
3. 访视窗口期过宽或过窄
4. 验证规则缺失或不清晰
5. 只有中文或只有英文
6. 混用不同的值集
7. 表单结构混乱
```

### 8.2 SDTM 设计原则

```
✅ 正确做法:
1. 遵循 SDTM 域结构
2. 使用标准变量名
3. 正确设置键值
4. 定义清晰的值集
5. 生成完整的元数据
6. 包含 Define.xml
7. 执行数据验证

❌ 错误做法:
1. 自定义 SDTM 域结构
2. 使用非标准变量名
3. 键值定义不完整
4. 值集未定义或定义错误
5. 缺少元数据描述
6. 不生成 Define.xml
7. 不执行数据验证
```

---

*文档版本：v1.0*
*创建日期：2026 年*
*维护人：蔡宇恒*
