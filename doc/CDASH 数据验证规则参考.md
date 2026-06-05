# CDASH 数据验证规则参考

## 1. 数据类型验证规则

### 1.1 字符串类型 (ST)
```
验证规则:
- 允许字符：字母、数字、空格、特殊字符 (.,'-)
- 最大长度：根据字段定义 (通常 1-256 字符)
- 必填检查：是否空值

示例字段:
- USUBJID: 1-20 字符，字母数字 + 下划线
- SITEID: 1-20 字符
- AETERM: 1-256 字符
```

### 1.2 数值类型 (NM)
```
验证规则:
- 允许字符：数字、小数点、负号
- 允许范围：根据字段定义
- 小数位数：根据字段定义

示例字段:
- AGE: 0-150 (单位：年)
- WEIGHT: 0-500 (单位：kg)
- ALT: -999 到 9999 (单位：U/L)
```

### 1.3 日期类型 (DT)
```
验证规则:
- 格式：YYYY-MM-DD (ISO 8601)
- 范围：1900-01-01 到 当前日期
- 逻辑验证：结束日期 ≥ 开始日期

示例字段:
- DOB: 1900-01-01 到 当前日期 -18 年
- AESTDTC: 研究开始日期前 2 年到 结束日期后 1 年
- CONSENTDT: ≤ 随机化日期
```

### 1.4 文本类型 (LM/CM)
```
验证规则:
- 多行文本
- 允许 HTML 标签 (可选)
- 最大长度：根据定义 (通常 1-10000 字符)

示例字段:
- AEDESCRIPTION: 自由文本描述
- CONSENTNOTE: 同意书备注
```

---

## 2. 必填字段规则 (CDASH 核心字段)

### 2.1 Demographics (DM) - 必填字段

| 字段 | 条件 | 验证规则 |
|------|------|---------|
| STUDYID | 所有记录 | 非空，符合命名规范 |
| USUBJID | 所有记录 | 唯一，1-20 字符，字母数字 + 下划线 |
| DOB | 所有记录 | 有效日期，年龄 0-120 岁 |
| SEX | 所有记录 | 枚举：M/F/U |
| SITEID | 所有记录 | 非空，与研究中心匹配 |
| CTRY | 所有记录 | ISO 国家代码 |

### 2.2 Informed Consent (IC) - 必填字段

| 字段 | 条件 | 验证规则 |
|------|------|---------|
| ICSCOD | 所有记录 | 枚举：Informed Consent |
| ICSSTDTC | 所有记录 | 有效日期，≤ ENRLDT |

### 2.3 Adverse Events (AE) - 必填字段

| 字段 | 条件 | 验证规则 |
|------|------|---------|
| AETERM | 所有记录 | 非空，1-256 字符 |
| AESTDTC | 所有记录 | 有效日期 |
| AESER | 所有记录 | 枚举：Y/N/U |
| AEOUT | 所有记录 | 枚举：痊愈/未愈/未知/死亡等 |
| AEREL | 所有记录 | 枚举：相关/不相关/未知 |

### 2.4 Interventions (EX) - 必填字段

| 字段 | 条件 | 验证规则 |
|------|------|---------|
| ACTN | 所有记录 | 非空，枚举：Treatment A/B/Placebo |
| EXSTDTC | 所有记录 | 有效日期，≥ 随机化日期 |

---

## 3. 逻辑验证规则

### 3.1 日期逻辑

```
规则 1: 出生日期 ≤ 入组日期
- DOB ≤ ENRLDT

规则 2: 入组日期 ≤ 随机化日期
- ENRLDT ≤ RNDTDTC

规则 3: 访视日期范围
- 筛选日期 ≤ 随机化日期
- 随机化日期 ≤ 结束随访日期

规则 4: 不良事件日期
- AESTDTC ≥ 筛选日期前 2 年
- AESTDTC ≤ 研究结束日期后 1 年
- AEENDTC ≥ AESTDTC

规则 5: 知情同意日期
- CONSENTDT ≤ 首次入组日期
- CONSENTDT < 首次用药日期
```

### 3.2 数值范围

```
规则 1: 年龄验证
- 计算年龄 = (随机化日期 - DOB) 的天数 / 365.25
- 0 ≤ 年龄 ≤ 120

规则 2: 体重验证
- 30 ≤ WEIGHT ≤ 250 (单位：kg)
- 排除极端值

规则 3: 身高验证
- 100 ≤ HEIGHT ≤ 250 (单位：cm)
- 排除极端值

规则 4: 生命体征合理性
- 收缩压：40-300 (mmHg)
- 舒张压：20-200 (mmHg)
- 脉搏：30-220 (bpm)
- 体温：30-45 (°C)
- 呼吸频率：5-60 (breaths/min)
```

### 3.3 枚举值验证

```
SEX: M, F, U (未知)
RACE: Asian, Black or African American, White, American Indian, Alaska Native, Native Hawaiian, Other Pacific Islander
AESER: Y, N, U (未知)
AEOUT: Recovered, Recovering, Not Recovered, Fatal, Unknown
AEREL: Not Related, Possibly Related, Probably Related, Probably Unrelated, Unrelated, Unknown
```

---

## 4. 字段特定验证规则

### 4.1 受试者编号 (USUBJID)

```javascript
// 验证规则
function validateUSUBJID(value, study) {
    // 格式：中心号 - 受试者号
    const pattern = /^[A-Z]{2,3}\d{3}-\d{1,5}$/;
    
    if (!pattern.test(value)) {
        return "USUBJID 格式错误，应为：CC001-0001";
    }
    
    // 唯一性检查
    if (isDuplicate(value)) {
        return "USUBJID 已存在";
    }
    
    return "Valid";
}
```

### 4.2 年龄 (AGE)

```javascript
function validateAge(dob, enrldt) {
    const birthDate = new Date(dob);
    const enrollDate = new Date(enrldt);
    
    // 计算年龄
    let age = enrollDate.getFullYear() - birthDate.getFullYear();
    const monthDiff = enrollDate.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && enrollDate.getDate() < birthDate.getDate())) {
        age--;
    }
    
    if (age < 0 || age > 120) {
        return `年龄 ${age} 超出合理范围 (0-120)`;
    }
    
    return "Valid";
}
```

### 4.3 不良事件严重性 (AESTDTC)

```javascript
function validateSeverity(severity) {
    const validSeverities = ['Mild', 'Moderate', 'Severe'];
    
    if (!validSeverities.includes(severity)) {
        return `严重程度必须是：${validSeverities.join(', ')}`;
    }
    
    return "Valid";
}

// SAE 验证规则
function validateSAE(aeData) {
    if (aeData.SERIOUS === 'Y') {
        if (!aeData.SAE_REASON) {
            return "严重不良事件必须填写原因";
        }
        if (!aeData.SAE_OUTCOME) {
            return "严重不良事件必须填写结局";
        }
        if (!aeData.REPORTING_DOCTOR) {
            return "严重不良事件必须填写报告医师";
        }
    }
    return "Valid";
}
```

### 4.4 实验室检测值 (LB)

```javascript
function validateLabValue(lbData) {
    const { test, value, unit } = lbData;
    
    // 特殊处理缺失值
    if (value === null || value === '') {
        return "Missing";
    }
    
    // 根据检测类型验证
    switch (test) {
        case 'WBC':
            if (value < 0.1 || value > 100) {
                return '白细胞计数超出合理范围 (0.1-100 x10^9/L)';
            }
            break;
        case 'HGB':
            if (value < 40 || value > 250) {
                return '血红蛋白超出合理范围 (40-250 g/L)';
            }
            break;
        case 'ALT':
            if (value < 0 || value > 2000) {
                return 'ALT 超出合理范围 (0-2000 U/L)';
            }
            break;
    }
    
    return "Valid";
}
```

---

## 5. 数据完整性规则

### 5.1 必填字段完整性

```
对于每个 eCRF 表单:
1. 标记必填字段 (*)
2. 提交前检查所有必填字段
3. 显示错误列表和定位到对应字段

规则:
- 所有带 * 的字段必须填写
- 逻辑必填 (conditional required) 字段根据其他字段值决定
```

### 5.2 数据一致性

```
检查:
1. 同一受试者不同表单间的数据一致性
   - 性别在所有表单中必须一致
   - DOB 在所有表单中必须一致
   
2. 访视间数据逻辑
   - 基线值 ≤ 后续访视值 (某些检测)
   - 体重变化合理 (±50% 每月)
```

### 5.3 审计追踪

```
记录所有数据变更:
- 字段名
- 原始值
- 新值
- 修改时间
- 修改人
- 修改原因 (可选)

实现:
CREATE TABLE audit_trail (
    audit_id SERIAL PRIMARY KEY,
    study_id VARCHAR(20),
    subject_id VARCHAR(20),
    form_name VARCHAR(50),
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(50),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT
);
```

---

## 6. eCRF 设计器验证配置

### 6.1 字段属性配置

```json
{
  "field": {
    "cdash_name": "AETERM",
    "cdash_label": "Adverse Event Term",
    "sdtm_field": "AETERM",
    "data_type": "ST",
    "required": true,
    "max_length": 256,
    "min_length": 1,
    "pattern": "",
    "enum_values": [],
    "conditional_required": {
      "rule": "",
      "trigger_field": "",
      "trigger_value": ""
    },
    "validation_rules": [
      {
        "type": "required",
        "message": "不良事件术语为必填项"
      },
      {
        "type": "length",
        "min": 1,
        "max": 256,
        "message": "长度必须在 1-256 字符之间"
      }
    ]
  }
}
```

### 6.2 验证规则库

```javascript
// 预定义验证规则库
const validationRules = {
  // 数据类型验证
  'is_string': (value) => typeof value === 'string',
  'is_number': (value) => !isNaN(value),
  'is_date': (value) => /^\d{4}-\d{2}-\d{2}$/.test(value),
  'is_email': (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
  
  // 范围验证
  'min_length': (value, min) => value.length >= min,
  'max_length': (value, max) => value.length <= max,
  'min_value': (value, min) => value >= min,
  'max_value': (value, max) => value <= max,
  
  // 枚举验证
  'in_enum': (value, enumValues) => enumValues.includes(value),
  
  // 逻辑验证
  'date_gte': (date1, date2) => new Date(date1) >= new Date(date2),
  'date_lte': (date1, date2) => new Date(date1) <= new Date(date2),
  'age_valid': (dob, refDate) => {
    const age = (refDate - dob) / (365.25 * 24 * 60 * 60 * 1000);
    return age >= 0 && age <= 120;
  }
};
```

---

## 7. 实施建议

### 7.1 前端验证 (eCRF 设计器)

```
1. 实时验证：用户输入时立即检查
2. 提交验证：表单提交前完整验证
3. 错误提示：清晰展示错误位置和原因
4. 自动修正：部分错误可自动修复 (如日期格式)
```

### 7.2 后端验证 (EDC 系统)

```
1. 二次验证：后端必须重新验证所有数据
2. 完整性检查：检查所有必填字段
3. 逻辑验证：跨表、跨记录验证
4. 审计追踪：记录所有数据变更

Node.js 示例:
app.post('/api/edc/data', async (req, res) => {
  const validationErrors = validateCDASH(req.body);
  
  if (validationErrors.length > 0) {
    return res.status(400).json({ errors: validationErrors });
  }
  
  // 保存数据并记录审计日志
  await saveWithAudit(req.user, req.body);
});
```

### 7.3 SDTM 转换前验证

```
转换前检查:
1. 所有必填字段已填充
2. 数据类型符合 SDTM 要求
3. 枚举值在 SDTM 允许范围内
4. 逻辑关系正确 (如日期顺序)
5. 受试者编号唯一性
```

---

## 8. 测试建议

### 8.1 单元测试

```python
# 验证规则测试
def test_age_validation():
    dob = datetime(1990, 1, 1)
    enrldt = datetime(2020, 1, 1)
    assert validate_age(dob, enrldt) == "Valid"  # 年龄 30 岁
    
def test_sae_validation():
    ae_data = {
        'serious': 'Y',
        'reason': 'Hospitalization',
        'outcome': 'Recovered',
        'doctor': 'Dr. Smith'
    }
    assert validate_sae(ae_data) == "Valid"
    
def test_date_logic():
    assert validate_date_logic(dob='1990-01-01', enrldt='2020-01-01') == True
```

### 8.2 集成测试

```
1. 创建测试用例覆盖所有验证规则
2. 测试边界值 (最小、最大、空值)
3. 测试异常输入 (特殊字符、超长文本)
4. 测试逻辑冲突 (日期倒置、数值超范围)
```

---

**创建时间**: 2026-05-27
**文档版本**: 1.0
**适用标准**: CDASH v1.1
**用途**: EDC 系统验证规则实现参考
