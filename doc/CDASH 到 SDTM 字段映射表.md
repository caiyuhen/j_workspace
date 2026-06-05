# CDASH 到 SDTM 字段映射参考表

## 1. Demographics (DM 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| StudyID | 研究编号 | STUDYID | ST | Y | 唯一标识研究 |
| SubjectID | 受试者编号 | USUBJID | ST | Y | 唯一标识受试者 |
| SubjectName | 受试者姓名 | SUBJNM | NM | N | 可选，注意隐私 |
| DateOfBirth | 出生日期 | DOB | DT | Y | 格式：YYYY-MM-DD |
| Sex | 性别 | SEX | CA | Y | M/F/U |
| Race | 种族 | RACE | CA | C | 条件必填 |
| Country | 国家 | CTRY | CA | Y | 研究启动国家 |
| SiteID | 中心编号 | SITEID | ST | Y | 研究中心标识 |
| VisitDate | 访视日期 | VISITDT | DT | Y | 筛查日期 |
| EnrollmentDate | 入组日期 | ENRLDT | DT | Y | 随机化日期 |

## 2. Informed Consent (IC 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| ConsentType | 同意书类型 | ICSCOD | CA | Y | 如：Informed Consent |
| ConsentDate | 同意日期 | ICSSTDTC | DT | Y | 格式：YYYY-MM-DD |
| ConsentMode | 同意方式 | ICSMODE | CA | N | 纸质/电子 |
| ConsentVersion | 同意书版本 | ICSVER | ST | N | 版本号 |

## 3. Medical History (MH 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| MHTerm | 病史术语 | MHTERM | LM | Y | 诊断名称 |
| MHDTC | 诊断日期 | MHSTDTC | DT | N | |
| MHEPDTC | 结束日期 | MHENDTC | DT | N | |
| MHSOC | 系统器官分类 | MHSOC | LM | N | MedDRA SOC |
| MHLT | 低层次术语 | MHLT | LM | N | MedDRA LT |

## 4. Current Medications (CM 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| CMTRT | 药物名称 | CMTRT | NM | Y | 药物通用名 |
| CMTRTP | 药物类别 | CMTRTP | NM | N | 药物类别 |
| CMAPHR | 给药途径 | CMROUTE | ST | N | 给药途径 |
| CMDOSFRQ | 给药频率 | CMDOSFRQ | ST | N | 如：qd, bid |
| CMSTDTC | 开始日期 | CMSTDTC | DT | N | |
| CMENDTC | 结束日期 | CMENDTC | DT | N | |

## 5. Interventions (EX 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| ACTN | 治疗名称 | ACTN | ST | Y | 随机分组名称 |
| EXSTDTC | 开始日期 | EXSTDTC | DT | Y | |
| EXENDTC | 结束日期 | EXENDTC | DT | N | |
| EXDOSE | 剂量 | EXDOSE | NM | N | |
| EXDOSU | 剂量单位 | EXDOSU | ST | N | 如：mg |
| EXROUTE | 给药途径 | EXROUTE | ST | N | |
| EXDOSFRQ | 给药频率 | EXDOSFRQ | ST | N | |
| EXSTRES | 研究用药 | EXSTRES | ST | N | 是/否 |

## 6. Vital Signs (VS 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| VSSTRESCD | 体征代码 | VSTESTCD | CD | Y | 预定义代码 |
| VSSTRES | 体征结果 | VSSTRES | NM | Y | 数值结果 |
| VSSTRESU | 单位 | VSSTRESU | ST | N | 如：mmHg, kg |
| VSSORCAT | 系统器官分类 | VSSORCAT | CA | N | |
| VSLOINC | LOINC 代码 | VSLOINC | ST | N | LOINC 编码 |

### 生命体征标准字段

| VS 类型 | VSSTRESCD | 中文名称 | VSSTRESU |
|--------|----------|---------|---------|
| 收缩压 | SYSDIFF | 收缩压 | mmHg |
| 舒张压 | DIADIFF | 舒张压 | mmHg |
| 脉搏 | HEART | 脉搏 | bpm |
| 体温 | TEMPER | 体温 | °C |
| 呼吸频率 | RESPIR | 呼吸频率 | breaths/min |

## 7. Adverse Events (AE 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| AETERM | 不良事件术语 | AETERM | LM | Y | 用 MedDRA 编码 |
| AESEQ | 事件序号 | AESEQ | NM | Y | 受试者内唯一 |
| AESOC | 系统器官分类 | AESOC | LM | N | MedDRA SOC |
| AELT | 低层次术语 | AELT | LM | N | MedDRA LT |
| AEDECOD | 解码术语 | AEDECOD | LM | N | MedDRA 首选词 |
| AEOUT | 结局 | AEOUT | CA | N | 痊愈/未愈/死亡等 |
| AETERM | 严重程度 | AESTDTC | CA | N | mild/moderate/severe |
| AEREL | 与药物关系 | AEREL | CA | N | 相关/不相关 |
| AESTDTC | 开始日期 | AESTDTC | DT | Y | |
| AEENDTC | 结束日期 | AEENDTC | DT | N | |
| AE Serious | 是否严重 | AESER | CA | Y | Y/N/U |

## 8. Laboratory Tests (LB 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| LBTESTCD | 检测代码 | LBTESTCD | CD | Y | 预定义代码 |
| LBTEST | 检测名称 | LBTEST | LM | Y | |
| LBORRES | 原始结果 | LBORRES | NM | N | 原始测量值 |
| LBORRESU | 原始单位 | LBORRESU | ST | N | |
| LBSTRESN | 标准化结果 | LBSTRESN | NM | Y | 标准化数值 |
| LBSTRESU | 标准化单位 | LBSTRESU | ST | N | |
| LBLOL | 低值上限 | LBLOL | NM | N | 正常范围下限 |
| LBHILO | 高值上限 | LBHILO | NM | N | 正常范围上限 |
| LBLOINC | LOINC 代码 | LBLOINC | ST | N | |
| LBSPEC | 标本来源 | LBSPEC | LM | N | 如：血液、尿液 |

### 常用实验室检测代码

| LBTESTCD | 检测名称 | LBORRESU |
|----------|---------|---------|
| WBC | 白细胞计数 | 10^9/L |
| RBC | 红细胞计数 | 10^12/L |
| HGB | 血红蛋白 | g/L |
| PLT | 血小板计数 | 10^9/L |
| ALT | 丙氨酸氨基转移酶 | U/L |
| AST | 天冬氨酸氨基转移酶 | U/L |
| BUN | 血尿素氮 | mg/dL |
| CREA | 肌酐 | mg/dL |
| GLUC | 血糖 | mg/dL |

## 9. Questionnaires (PRO 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| PROCAT | 领域分类 | PROCAT | CA | N | 如：生活质量 |
| PROAREA | 区域 | PROAREA | ST | N | |
| PROITEM | 项目 | PROITEM | ST | N | |
| PRORCAT | 结果分类 | PRORCAT | CA | N | |
| PROSCALE | 量表名称 | PROSCALE | ST | N | 如：SF-36, EQ-5D |

## 10. Pregnancy (PG 域)

| CDASH 字段名 | 中文名称 | SDTM 字段 | 数据类型 | 必填 | 备注 |
|------------|---------|---------|---------|------|------|
| PGPRGNC | 妊娠状态 | PGPRGNC | CA | N | 是/否 |
| PGTRTIDT | 末次月经日期 | PGTRTIDT | DT | N | |
| PGOUTCOME | 妊娠结局 | PGOUTCOME | CA | N | 如：自然流产、足月产 |

---

## CDASH 字段命名规则

### 通用规则
1. **前缀**: 使用域缩写 (DM, AE, LB 等)
2. **语义**: 清晰表达字段含义
3. **长度**: 不超过 64 个字符
4. **字符**: 只使用字母、数字、下划线

### 常见后缀
- TERM: 术语 (如 AETERM)
- DT: 日期 (如 DOB, AESTDTC)
- TC: 时间 (如 AESTDTC)
- CAT: 分类 (如 AESOC)
- CD: 代码 (如 VSTESTCD)
- RES: 结果 (如 LBORRES)
- U: 单位 (如 VSSTRESU)

### 必填字段标记
- **Y**: 必填 (Required)
- **N**: 非必填 (Not Required)
- **C**: 条件必填 (Conditional)

---

## 实施建议

### 1. eCRF 设计器实现
```
当用户拖拽字段到画布时:
- 自动验证字段英文名是否符合 CDASH 命名规范
- 提供 CDASH 标准字段库供快速选择
- 自动关联 SDTM 字段映射
```

### 2. 数据验证规则
```
CDASH 定义的验证规则包括:
- 数据类型验证 (数值、日期、文本)
- 必填字段检查
- 范围检查 (如年龄 0-120 岁)
- 逻辑验证 (如结束日期>开始日期)
- 枚举值验证 (如 SEX 只能是 M/F/U)
```

### 3. SDTM 转换引擎
```
转换流程:
1. 从 eCRF 提取 CDASH 格式数据
2. 应用字段映射表
3. 验证 SDTM 格式要求
4. 生成 SDTM 数据集 (DM, AE, LB 等)
5. 输出标准 XPT 文件
```

---

## 参考资源

1. **CDASH 官方网站**: https://www.cdisc.org/standards/foundational/cdash
2. **SDTM 标准**: https://www.cdisc.org/standards/foundational/sdtm
3. **LOINC 数据库**: https://loinc.org/
4. **MedDRA 字典**: https://www.meddra.org/
5. **CDISC 示例数据**: https://github.com/cdisc-org

---

**创建时间**: 2026-05-27
**文档版本**: 1.0
**适用标准**: CDASH v1.1, SDTM v3.5
